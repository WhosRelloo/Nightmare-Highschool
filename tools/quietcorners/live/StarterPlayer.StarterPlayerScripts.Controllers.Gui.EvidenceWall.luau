--[[
	EvidenceWall (client). Controllers.Gui.EvidenceWall  (2.38, Quiet Corners QC5)
	Spec: docs/superpowers/specs/2026-11-21-quiet-corners-ui-design.md §7 (and §9, the fit rules). Plan: Task R9.
	Rules: ReplicatedStorage.Functions.QuietCorners (QC.Wall / Pin / Unpin / Miss / ShowHint). Art: Config.EvidenceArt
	(cards, sheets, plate, tacks, thread, lens, stamp, wall quadrants), Config.QuietCornersArt.PromptCap (key caps) and the
	Bell Tower Seal (Config.BellTowerArt.Seal, tinted crimson = "Answered", plan ruling 11). Never Theme.Images.Seal.
	Every piece with no uploaded id falls back to kit art (Decorate / Panel / Plate / SlotBg / Knob / BarFill / OrbRing).

	The Evidence Wall replaces the Journal's Case Files tab: a full-screen cork board (menu state, NHMenuOpen) that
	always shows the case's big question on the plate, splits it into small question sheets, and lets you drop each
	clue card on the question it answers.
	  - Pick up a found clue (click / A / tap): every slot that can take it glows (gold UIStroke; no pulse under
	    NHReducedFlash). Drop it in a slot: QC.Pin; once both slots hold different clues the pair goes to the server as
	    Packets.QuestAction { Action = "Link"; Case; A; B; Question }.
	  - LinkHit: re-render, the thread draws in (instant under NHReducedMotion) and the insight types out.
	  - LinkMiss: QC.Miss + QC.Unpin, both cards shake (NHReducedMotion: a 0.2 s red outline); after two misses the
	    question's hint shows.
	  - When every non-bonus question is answered: "Your answer", one AnswerCard per deduction option (sends Deduce).
	  - Solved: the chosen card centres and the StampInk "SOLVED" stamp lands (a fade under NHReducedMotion).
	  - Inspect (X / right click; on phones tap a held card again): the Lens shows the clue's full text at 22 px.
	  - Missing clues show as chalk outlines ("Not found yet"); "X Mark it" only when Local.MarkTarget finds the
	    clue's world object (a TODO hook: it returns nil for now, so the cap stays hidden).
	Phones (Kit.Phone): the plate stays on top, the clues sit in a horizontal tray at the bottom, the questions scroll
	in between; tap a clue, then a slot. Consoles: GuiService.SelectedObject moves over cards / slots / answers, and
	ContextActionService binds A (pick / pin), X (inspect / mark), B (put back, close the lens, close) while open.
	Esc closes. Re-renders on StateController.ProfileUpdated (SetQuests).
	Fit (qc_fit.lua): every text >= 20 design px, measured to fit, inside its art's QcBox, with QcBg on art that has
	a measured paper colour; texts in a scroller that are not fully in view are hidden so nothing overlaps.
	API: Open(CaseId?), Close(), IsOpen(), OnStart().
	Studio probe (HudState.Probe): Wall(CaseId?), WallClose(), WallPin(Q, Slot, Clue), WallInfo().
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Lighting = game:GetService("Lighting")
local GuiService = game:GetService("GuiService")
local ContextActionService = game:GetService("ContextActionService")
local TweenService = game:GetService("TweenService")
local TextService = game:GetService("TextService")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Kit = require(ReplicatedStorage:WaitForChild("UI"):WaitForChild("Components"))
local Theme = Kit.Theme
local QC = require(ReplicatedStorage:WaitForChild("Functions"):WaitForChild("QuietCorners"))
local ConfigFolder = ReplicatedStorage:WaitForChild("Config")
local Art = require(ConfigFolder:WaitForChild("EvidenceArt"))
local QcArt = require(ConfigFolder:WaitForChild("QuietCornersArt"))
local Cases = require(ConfigFolder:WaitForChild("Cases"))
local Packets = require(ReplicatedStorage:WaitForChild("Remotes"):WaitForChild("Packets"))
local StateController = require(script.Parent.Parent:WaitForChild("StateController"))
local Fx = require(script.Parent.Parent:WaitForChild("Fx"))

local BellArt = nil
do
	local Mod = ConfigFolder:FindFirstChild("BellTowerArt")
	if Mod then
		local Ok, R = pcall(require, Mod)
		if Ok then BellArt = R end
	end
end

local Player = Players.LocalPlayer
local Local = {}
local Shared = {}

---| Palette (plan ruling 13: the ink fixed for contrast) |---

local rgb = Color3.fromRGB
local COL = {
	Ink = rgb(40, 22, 16); InkDim = rgb(48, 30, 22); InkRed = rgb(70, 6, 11); PlateInk = rgb(24, 14, 8); -- (S4) InkRed was 96,10,16: 3.9 contrast on the Object card, 4.6+ on every card now
	Gold = rgb(230, 190, 108); Bone = rgb(236, 226, 206); Dim = rgb(200, 188, 168); Chalk = rgb(226, 222, 210);
	Crimson = rgb(220, 52, 62); Thread = rgb(170, 28, 44); StampRed = rgb(176, 20, 30); Slate = rgb(40, 36, 46);
}
local BG = { -- measured QcBg values (plan ruling 13)
	Paper = rgb(170, 156, 134); Record = rgb(160, 137, 106); Object = rgb(163, 132, 88); Plate = rgb(133, 93, 36); Cap = rgb(46, 41, 40);
}
local CARD_BG = { CardNote = BG.Paper; CardPhoto = BG.Paper; CardRecord = BG.Record; CardObject = BG.Object }

local Faces = Theme.FontFaces
local FACE = {
	Body = Faces.Body;
	Bold = Faces.BodyBold;
	Italic = Font.new(Faces.Body.Family, Enum.FontWeight.Regular, Enum.FontStyle.Italic);
	Title = Font.new(Faces.Title.Family, Enum.FontWeight.Bold);
}

local CARD_W, CARD_H = 220, 300
local SHEET_W, SHEET_H, SHEET_STEP = 720, 252, 264
local COMPACT_H, COMPACT_STEP = 160, 170
local SLOT_W, SLOT_H = 120, 164
local SHEET_BOX = "0.0306,0.0159,0.9694,0.9524"
local COMPACT_BOX = "0.0306,0.0125,0.9694,0.95"
local CAP_BOX = "0.12,0.15,0.88,0.85"
local ANSWER_BOX = "0.12,0.2,0.88,0.8"

---| State |---

local Ui = nil :: any
local IsOpen = false
local CaseId = nil :: string?
local Model = nil :: any
local PinsBy = {} :: { [string]: any }    -- [CaseId] = QC pins (client-only)
local MissBy = {} :: { [string]: any }    -- [CaseId] = QC misses
local Pending = {} :: { [string]: number } -- ["Case|Q"] = os.clock() of the Link sent
local Fresh = {} :: { [string]: boolean }  -- ["Case|Q"]: the thread draws in on the next render
local Typed = {} :: { [string]: boolean }  -- ["Case|Q"]: the insight types out on the next render
local Held = nil :: string?
local LensId = nil :: string?
local Stamping = false
local LastOption = {} :: { [string]: number }
local LastPadA = 0
local RenderGen = 0

local function key(C: string?, Q: string): string return tostring(C) .. "|" .. Q end

---| Small helpers |---

function Local.New(Class: string, Props: { [string]: any }, Parent: Instance?): any
	local I = Instance.new(Class)
	for K, V in Props do (I :: any)[K] = V end
	if Parent then I.Parent = Parent end
	return I
end

function Local.Race(): string return QC.Race(Player:GetAttribute("Race")) end
function Local.Art(Piece: string): string? return QC.Image(Art, Piece, Local.Race()) end
function Local.Reduced(): boolean return Kit.ReducedMotion and Kit.ReducedMotion() or (Fx.Reduced and Fx.Reduced()) or false end
function Local.NoFlash(): boolean return Kit.ReducedFlash and Kit.ReducedFlash() or false end
function Local.Sound(Name: string, Vol: number?, Speed: number?) pcall(Kit.PlaySound, Name, Vol, Speed) end

function Local.BoxString(B: { number }?): string
	if not B then return "0,0,1,1" end
	return ("%.4f,%.4f,%.4f,%.4f"):format(B[1], B[2], B[3], B[4])
end

function Local.Tag(Obj: Instance, Box: string, Bg: Color3?)
	Obj:SetAttribute("QcBox", Box)
	if Bg then Obj:SetAttribute("QcBg", Bg) end
end

-- the kit fallback for a piece with no uploaded art (a slate surface with the slot frame)
function Local.Skin(Obj: GuiObject, FrameColor: Color3?, BgColor: Color3?)
	pcall(Kit.Decorate, Obj, { ornament = "slot"; shadow = false; frameColor = FrameColor; bgColor = BgColor })
end

-- an art surface: the uploaded piece, else a kit-decorated one. Returns the object and whether the real art is up.
function Local.Surface(Class: string, Parent: Instance, Name: string, Piece: string?, Pos: UDim2, Size: UDim2, Props: { [string]: any }?): (any, boolean)
	local Img = if Piece then Local.Art(Piece) else nil
	local O = Local.New(Class, { Name = Name; BackgroundTransparency = 1; BorderSizePixel = 0; Position = Pos; Size = Size; Image = Img or ""; ZIndex = 2 }, nil)
	if Class == "ImageButton" then O.AutoButtonColor = false; O.Selectable = true end
	if Props then for K, V in Props do O[K] = V end end
	O.Parent = Parent
	if not Img then Local.Skin(O, COL.Gold:Lerp(COL.Bone, 0.5), COL.Slate) end
	return O, Img ~= nil
end

---| Text: measured to fit (spec §9) |---

local function measure(Text: string, Size: number, Kind: string, W: number): Vector2
	local F = if Kind == "Title" then Enum.Font.Fantasy else Enum.Font.Garamond
	local Fac = if Kind == "Bold" or Kind == "Title" then 1.12 else 1.06 -- bold / italic run wider than the enum font
	local Ok, V = pcall(TextService.GetTextSize, TextService, Text, Size, F, Vector2.new(math.max(8, W / Fac), 100000))
	return if Ok then V else Vector2.new(W, Size * 1.3)
end

function Local.LineH(Size: number, Kind: string): number return math.ceil(measure("Ag", Size, Kind, 1000).Y) + 4 end

-- shorten at a word until it fits W x MaxH; returns the text and the label height
function Local.Fit(Text: string, Size: number, Kind: string, W: number, MaxH: number): (string, number)
	local function ok(T: string): boolean return measure(T, Size, Kind, W).Y + 2 <= MaxH end
	local T = QC.Ellipsize(Text, ok)
	return T, math.min(MaxH, math.ceil(measure(T, Size, Kind, W).Y) + 4)
end

-- the safety net: if the engine still says it doesn't fit, drop words until it does
function Local.Settle(L: TextLabel)
	task.spawn(function()
		for _ = 1, 24 do
			RunService.Heartbeat:Wait()
			if not L.Parent or not Ui or not Ui.Gui.Enabled then return end
			if not L.Visible or L.AbsoluteSize.X <= 0 then continue end
			if L.TextFits then return end
			local Base = string.gsub(L.Text, "…$", "")
			local Words = string.split(Base, " ")
			if #Words <= 1 then return end
			table.remove(Words)
			L.Text = table.concat(Words, " ") .. "…"
		end
	end)
end

-- O = { X, Y, W, Text, Size, Kind?, Color, MaxH?, AlignX?, Name?, CenterY? }
function Local.Label(Parent: Instance, O: any): (TextLabel, number)
	local Kind = O.Kind or "Body"
	local Size = math.max(QC.MIN_TEXT, O.Size or 20)
	local MaxH = O.MaxH or Local.LineH(Size, Kind)
	local T, H = Local.Fit(tostring(O.Text or ""), Size, Kind, O.W, MaxH)
	local Y = if O.CenterY then O.CenterY - H / 2 else O.Y
	local L = Local.New("TextLabel", {
		Name = O.Name or "Text"; BackgroundTransparency = 1; BorderSizePixel = 0;
		Position = UDim2.fromOffset(O.X, Y); Size = UDim2.fromOffset(O.W, H);
		Text = T; TextSize = Size; FontFace = FACE[Kind] or FACE.Body; TextColor3 = O.Color or COL.Ink;
		TextWrapped = true; RichText = false; TextXAlignment = O.AlignX or Enum.TextXAlignment.Left;
		TextYAlignment = if O.CenterY then Enum.TextYAlignment.Center else Enum.TextYAlignment.Top; ZIndex = 4;
	}, Parent) :: TextLabel
	Local.Settle(L)
	return L, H
end

function Local.TypeOut(L: TextLabel)
	if Local.Reduced() then return end
	local N = utf8.len(L.Text) or #L.Text
	L.MaxVisibleGraphemes = 0
	TweenService:Create(L, TweenInfo.new(math.clamp(N * 0.025, 0.4, 2.2), Enum.EasingStyle.Linear), { MaxVisibleGraphemes = N + 2 }):Play()
end

---| Data |---

function Local.CaseIds(): { string }
	local Ids = {}
	for Id in Cases do table.insert(Ids, Id) end
	table.sort(Ids, function(A, B)
		local NA, NB = Cases[A].Number or 99, Cases[B].Number or 99
		if NA ~= NB then return NA < NB end
		return A < B
	end)
	return Ids
end

function Local.Saved(Id: string?): any
	local P = StateController.GetProfile(false)
	local Q = P and P.Quests
	local C = typeof(Q) == "table" and Q.Cases
	return typeof(C) == "table" and Id and C[Id] or nil
end

function Local.DefaultCase(): string?
	local Ids = Local.CaseIds()
	for _, Id in Ids do
		local S = Local.Saved(Id)
		if S and typeof(S.Clues) == "table" and next(S.Clues) ~= nil then return Id end
	end
	return Ids[1]
end

function Local.Number(Id: string): number
	local Def = Cases[Id]
	if Def and typeof(Def.Number) == "number" then return Def.Number end
	return table.find(Local.CaseIds(), Id) or 1
end

function Local.Build(): any
	if not CaseId or not Cases[CaseId] then return nil end
	return QC.Wall(Cases[CaseId], Local.Saved(CaseId), PinsBy[CaseId])
end

function Local.Clue(M: any, Id: string?): any
	if not M or not Id then return nil end
	for _, C in M.Clues do if C.Id == Id then return C end end
	return nil
end

function Local.Question(M: any, Q: string): any
	if not M then return nil end
	for _, R in M.Questions do if R.Id == Q then return R end end
	return nil
end

function Local.Ask(): string
	local Def = CaseId and Cases[CaseId]
	if not Def then return "" end
	return if Def.Deduction and Def.Deduction.Question then Def.Deduction.Question else (Def.Name or "")
end

function Local.HintFor(Q: any): string?
	if Q.State == "Answered" then return nil end
	if QC.ShowHint(MissBy[CaseId or ""], Q.Id) and Q.Hint then return Q.Hint end
	return nil
end

-- TODO (Quiet Corners follow-up): find the clue's quest object in the world (Config.Quests.Objects[..].Clue) so
-- "X Mark it" can pin it on the compass. Until then it returns nil and the Mark it cap stays hidden.
function Local.MarkTarget(_ClueId: string): Instance?
	return nil
end

function Local.Mark(ClueId: string)
	local Target = Local.MarkTarget(ClueId)
	if not Target then return end
	Local.Sound("Tick", 0.7)
	-- TODO: hand Target to the compass marker once MarkTarget finds objects
end

---| Build (static) |---

function Local.MakeGui(): any
	local Phone = Kit.Phone and Kit.Phone() or false
	local Gui = Local.New("ScreenGui", {
		Name = "NHEvidenceWall"; ResetOnSpawn = false; DisplayOrder = 30; IgnoreGuiInset = true; Enabled = false;
		ZIndexBehavior = Enum.ZIndexBehavior.Sibling;
	}, Player:WaitForChild("PlayerGui"))
	if Phone then
		Kit.AutoScale(Gui) -- on phones AutoScale runs Kit.ClampPanels: the board is clamped to the screen
	else
		Kit.AutoScale(Gui, { fitWidth = 1920; fitHeight = 1080; fitMargin = 0 })
	end

	-- the scrim: the kit's soft shadow, not a plain frame (an ImageButton so clicks don't reach the world)
	Local.New("ImageButton", {
		Name = "Scrim"; Image = Theme.Images.Shadow; ImageColor3 = rgb(0, 0, 0); ImageTransparency = 0.42;
		ScaleType = Enum.ScaleType.Slice; SliceCenter = Rect.new(40, 40, 88, 88); AutoButtonColor = false; Selectable = false;
		BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5);
		Size = UDim2.fromScale(3, 3); ZIndex = 0;
	}, Gui)

	local Board = Local.New("Frame", {
		Name = "Board"; BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5);
		Size = UDim2.fromOffset(1920, 1080); ZIndex = 1;
	}, Gui)

	-- the wall: four quadrants edge to edge (plan ruling 4), else the kit's ornate panel
	local Quads = { "WallTL", "WallTR", "WallBL", "WallBR" }
	local All = true
	for _, Q in Quads do if not QC.Image(Art, Q) then All = false end end
	if All then
		for I, Q in Quads do
			Local.New("ImageLabel", {
				Name = Q; Image = QC.Image(Art, Q) :: string; BackgroundTransparency = 1; ZIndex = 1;
				Position = UDim2.fromScale(((I - 1) % 2) * 0.5, ((I - 1) // 2) * 0.5); Size = UDim2.fromScale(0.5, 0.5);
			}, Board)
		end
	else
		local Ok = pcall(Kit.Panel, {
			Name = "WallPanel"; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5);
			Size = UDim2.new(1, -120, 1, -120); Parent = Board;
		})
		if not Ok then Local.Skin(Board) end
	end

	local U = { Gui = Gui; Board = Board; Phone = Phone; Dyn = nil; Answers = 0 }
	Board:GetPropertyChangedSignal("Size"):Connect(function()
		if IsOpen and Ui == U then task.defer(Local.Render) end
	end)
	return U
end

function Local.Rebuild()
	local Was = IsOpen
	if Ui then Ui.Gui:Destroy() end
	Ui = Local.MakeGui()
	if Was then Ui.Gui.Enabled = true Local.Render() end
end

---| Render |---

function Local.Render()
	if not Ui or not IsOpen or not CaseId then return end
	RenderGen += 1
	local Gen = RenderGen
	local M = Local.Build()
	if not M then return end
	Model = M
	if Held and not (Local.Clue(M, Held) and Local.Clue(M, Held).Found) then Held = nil end

	local Sel = GuiService.SelectedObject
	local SelName = if Sel and Sel:IsDescendantOf(Ui.Gui) then Sel.Name else nil
	if Ui.Dyn then Ui.Dyn:Destroy() end
	local Board = Ui.Board
	local W, H = Board.Size.X.Offset, Board.Size.Y.Offset
	local Dyn = Local.New("Frame", { Name = "Dyn"; BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1); ZIndex = 2 }, Board)
	Ui.Dyn = Dyn

	Local.Plate(Dyn, M, W)
	Local.Header(Dyn, M, W)
	if Ui.Phone then Local.Tray(Dyn, M, W, H) else Local.Cards(Dyn, M) end
	Local.Sheets(Dyn, M, W, H)
	if not Ui.Phone then Local.Foot(Dyn, H) end
	if LensId then Local.Lens(Dyn, LensId) end
	Local.Bind()

	task.spawn(function()
		RunService.Heartbeat:Wait()
		RunService.Heartbeat:Wait()
		if Gen ~= RenderGen or not Ui or Ui.Dyn ~= Dyn then return end
		Local.Cull()
		Local.Threads(true)
		Local.Select(SelName)
	end)
end

-- the plate: the case's big question, engraved (CasePlate<Race>, else the kit plate)
function Local.Plate(Dyn: Instance, _M: any, W: number)
	local PW = if Ui.Phone then math.clamp(W - 520, 480, 800) else 800
	local PH = 100
	local X = if Ui.Phone then (W - PW) / 2 else 560
	local Y = if Ui.Phone then 8 else 70
	local Img = Local.Art("CasePlate")
	local Plate
	if Img then
		Plate = Local.New("ImageLabel", { Name = "Plate"; Image = Img; BackgroundTransparency = 1; Position = UDim2.fromOffset(X, Y); Size = UDim2.fromOffset(PW, PH); ZIndex = 3 }, Dyn)
	else
		local Ok, R = pcall(Kit.Plate, { Name = "Plate"; Position = UDim2.fromOffset(X, Y); Size = UDim2.fromOffset(PW, PH); Parent = Dyn })
		Plate = if Ok then R else Local.Surface("ImageLabel", Dyn, "Plate", nil, UDim2.fromOffset(X, Y), UDim2.fromOffset(PW, PH))
	end
	local B = Art.Boxes.CasePlate
	Local.Tag(Plate, Local.BoxString(B), if Img then BG.Plate else nil)
	local BX0, BY0, BX1, BY1 = B[1] * PW, B[2] * PH, B[3] * PW, B[4] * PH
	Local.Label(Plate, {
		Name = "Ask"; X = BX0 + 4; W = BX1 - BX0 - 8; CenterY = (BY0 + BY1) / 2; MaxH = BY1 - BY0 - 2;
		Text = Local.Ask(); Size = 28; Kind = "Bold"; Color = if Img then COL.PlateInk else COL.Gold; AlignX = Enum.TextXAlignment.Center;
	})
end

-- the header: case number and name top-left, progress top-right (both on the wall's dark frame)
function Local.Header(Dyn: Instance, M: any, W: number)
	local Def = Cases[CaseId :: string]
	local Num = ("CASE %02d"):format(Local.Number(CaseId :: string))
	local Clues = ("Clues %d of %d"):format(M.Found, M.Total)
	local Answered = ("Answered %d of %d"):format(M.Answered, M.Needed)
	local Touch = Kit.TouchOnly and Kit.TouchOnly() or false
	if Ui.Phone then
		local PW = math.clamp(W - 520, 480, 800)
		local CW = math.max(140, (W - PW) / 2 - 28)
		Local.Label(Dyn, { Name = "CaseNo"; X = 16; Y = 12; W = CW; Text = Num; Size = 22; Kind = "Bold"; Color = COL.Gold })
		Local.Label(Dyn, { Name = "CaseName"; X = 16; Y = 46; W = CW; Text = Def.Name or ""; Size = 20; Color = COL.Bone; MaxH = 56 })
		Local.CloseButton(Dyn, W - 16 - 120, 8)
		Local.Label(Dyn, { Name = "Clues"; X = W - 16 - CW; Y = 56; W = CW; Text = Clues; Size = 20; Kind = "Bold"; Color = COL.Bone; AlignX = Enum.TextXAlignment.Right })
		Local.Label(Dyn, { Name = "Answered"; X = W - 16 - CW; Y = 84; W = CW; Text = Answered; Size = 20; Color = COL.Dim; AlignX = Enum.TextXAlignment.Right })
		return
	end
	Local.Label(Dyn, { Name = "CaseNo"; X = 92; CenterY = 104; W = 440; Text = Num; Size = 22; Kind = "Bold"; Color = COL.Gold })
	Local.Label(Dyn, { Name = "CaseName"; X = 92; CenterY = 134; W = 440; Text = Def.Name or ""; Size = 20; Color = COL.Bone })
	Local.Label(Dyn, { Name = "Clues"; X = 1388; CenterY = 104; W = 442; Text = Clues; Size = 22; Kind = "Bold"; Color = COL.Bone; AlignX = Enum.TextXAlignment.Right })
	Local.Label(Dyn, { Name = "Answered"; X = 1388; CenterY = 134; W = 442; Text = Answered; Size = 20; Color = COL.Dim; AlignX = Enum.TextXAlignment.Right })
	if Touch then Local.CloseButton(Dyn, 1830 - 120, 24) end
end

function Local.CloseButton(Dyn: Instance, X: number, Y: number)
	pcall(Kit.Button, {
		text = "Close"; style = "default"; onClick = function() Shared.Close() end;
		Name = "Close"; Position = UDim2.fromOffset(X, Y); Size = UDim2.fromOffset(120, 44); Parent = Dyn;
	})
end

---| Cards |---

function Local.CardPiece(C: any): string return "Card" .. (if C.Kind == "Photo" then "Photo" else C.Kind) end

function Local.Cards(Dyn: Instance, M: any)
	local Rows = math.max(1, math.ceil(#M.Clues / 3))
	local Scroll = Local.New("ScrollingFrame", {
		Name = "Cards"; BackgroundTransparency = 1; BorderSizePixel = 0; Position = UDim2.fromOffset(90, 210); Size = UDim2.fromOffset(980, 790);
		CanvasSize = UDim2.fromOffset(0, 20 + Rows * 360); ScrollingDirection = Enum.ScrollingDirection.Y; ScrollBarThickness = 6;
		ScrollBarImageColor3 = COL.Gold; Selectable = false; ZIndex = 3;
	}, Dyn)
	for I, C in M.Clues do
		local X, Y = 10 + ((I - 1) % 3) * 270, 20 + ((I - 1) // 3) * 360
		if C.Found then Local.Card(Scroll, C, X, Y) else Local.Missing(Scroll, C, X, Y) end
	end
	Scroll:GetPropertyChangedSignal("CanvasPosition"):Connect(function() Local.Cull() Local.Threads(false) end)
end

function Local.Card(Parent: Instance, C: any, X: number, Y: number)
	local Piece = Local.CardPiece(C)
	local Def = Cases[CaseId :: string].Clues[C.Id] or {}
	if C.Kind == "Photo" and typeof(C.Photo) == "number" then -- the photo sits behind the card's window
		Local.New("ImageLabel", { Name = "Photo_" .. C.Id; Image = "rbxassetid://" .. C.Photo; BackgroundTransparency = 1;
			Position = UDim2.fromOffset(X + 15, Y + 15); Size = UDim2.fromOffset(190, 175); ZIndex = 1 }, Parent)
	end
	local Card, Real = Local.Surface("ImageButton", Parent, "Card_" .. C.Id, Piece, UDim2.fromOffset(X, Y), UDim2.fromOffset(CARD_W, CARD_H))
	Card:SetAttribute("QcItem", true)
	local B = Art.Boxes[Piece] or Art.Boxes.CardNote
	Local.Tag(Card, Local.BoxString(B), if Real then CARD_BG[Piece] else nil)
	local Ink = if Real then COL.Ink else COL.Bone
	local Dim = if Real then COL.InkDim else COL.Dim
	local Red = if Real then COL.InkRed else COL.Gold
	local BX0, BY0, BX1, BY1 = B[1] * CARD_W, B[2] * CARD_H, B[3] * CARD_W, B[4] * CARD_H
	local TX = BX0 + 4
	local TW = BX1 - TX - 4
	if C.Kind == "Photo" then
		local _, H1 = Local.Label(Card, { Name = "Kind"; X = TX; Y = BY0 + 2; W = TW; Text = "PHOTO"; Size = 20; Kind = "Bold"; Color = Red })
		local _, H2 = Local.Label(Card, { Name = "Name"; X = TX; Y = BY0 + 2 + H1; W = TW; Text = C.Name or C.Id; Size = 22; Kind = "Bold"; Color = Ink })
		Local.Label(Card, { Name = "Where"; X = TX; Y = BY0 + 2 + H1 + H2; W = TW; Text = C.Where or ""; Size = 20; Color = Dim; MaxH = math.max(20, BY1 - (BY0 + 2 + H1 + H2) - 2) })
	else
		local Yc = BY0 + 8
		local _, H1 = Local.Label(Card, { Name = "Kind"; X = TX; Y = Yc; W = TW; Text = string.upper(C.Kind); Size = 20; Kind = "Bold"; Color = Red })
		Yc += H1 + 2
		local _, H2 = Local.Label(Card, { Name = "Name"; X = TX; Y = Yc; W = TW; Text = C.Name or C.Id; Size = 22; Kind = "Bold"; Color = Ink; MaxH = 3 * Local.LineH(22, "Bold") })
		Yc += H2 + 2
		local _, H3 = Local.Label(Card, { Name = "Where"; X = TX; Y = Yc; W = TW; Text = C.Where or ""; Size = 20; Color = Dim; MaxH = 2 * Local.LineH(20, "Body") })
		Yc += H3 + 10
		local Quote = Def.Quote or C.Text
		local Avail = BY1 - 6 - Yc
		if Quote and Avail >= Local.LineH(20, "Italic") then
			Local.Label(Card, { Name = "Quote"; X = TX; Y = Yc; W = TW; Text = Quote; Size = 20; Kind = "Italic"; Color = Ink; MaxH = Avail })
		end
	end
	Local.Tack(Card, CARD_W / 2 - 15, -12)
	if Held == C.Id then Local.Stroke(Card, "QcHeld", COL.Gold, 3, false) end
	Card.Activated:Connect(function(Input) if Local.PadDup(Input) then return end Local.Pick(C.Id) end)
	Card.MouseButton2Click:Connect(function() Local.Inspect(C.Id) end)
end

function Local.Missing(Parent: Instance, C: any, X: number, Y: number)
	local Img = Local.Art("CardMissing")
	local Card = Local.New("ImageButton", { Name = "Card_" .. C.Id; Image = Img or ""; ImageColor3 = COL.Chalk; BackgroundTransparency = 1; AutoButtonColor = false;
		Selectable = true; Position = UDim2.fromOffset(X, Y); Size = UDim2.fromOffset(CARD_W, CARD_H); ZIndex = 2 }, Parent)
	if not Img then Local.Skin(Card, COL.Chalk, COL.Slate) end
	Card:SetAttribute("QcItem", true)
	local B = Art.Boxes.CardMissing
	Local.Tag(Card, Local.BoxString(B), nil)
	local BX0, BY1 = B[1] * CARD_W, B[4] * CARD_H
	Local.Label(Card, { Name = "NotFound"; X = BX0; W = CARD_W - 2 * BX0; CenterY = 56; Text = "Not found yet"; Size = 22; Kind = "Bold"; Color = COL.Chalk; AlignX = Enum.TextXAlignment.Center })
	local Yc = 82
	local _, H1 = Local.Label(Card, { Name = "Name"; X = 26; Y = Yc; W = CARD_W - 52; Text = C.Name or C.Id; Size = 20; Color = COL.Chalk; MaxH = 2 * Local.LineH(20, "Body") })
	Yc += H1 + 10
	local Where = string.gsub(tostring(C.Where or "the school"), "^The ", "the ")
	local Target = Local.MarkTarget(C.Id)
	local Floor = if Target then 220 else BY1 - 4
	if Floor - Yc >= Local.LineH(20, "Italic") then
		Local.Label(Card, { Name = "Where"; X = 26; Y = Yc; W = CARD_W - 52; Text = "Somewhere in " .. Where .. "."; Size = 20; Kind = "Italic"; Color = COL.Dim; MaxH = Floor - Yc })
	end
	if Target then
		local CapW = Local.Cap(Card, 26, 226, "X", 40)
		Local.Label(Card, { Name = "MarkIt"; X = 26 + CapW + 8; CenterY = 246; W = CARD_W - 52 - CapW - 8; Text = "Mark it"; Size = 20; Kind = "Bold"; Color = COL.Chalk })
		Card.Activated:Connect(function(Input) if Local.PadDup(Input) then return end Local.Mark(C.Id) end)
	end
end

function Local.Tack(Parent: Instance, X: number, Y: number)
	local Img = Local.Art("Tack")
	Local.New("ImageLabel", { Name = "Tack"; Image = Img or Theme.Images.Knob; ImageColor3 = if Img then rgb(255, 255, 255) else COL.Gold;
		BackgroundTransparency = 1; Position = UDim2.fromOffset(X, Y); Size = UDim2.fromOffset(30, 30); ZIndex = 6 }, Parent)
end

-- a key cap (PromptCap art, else a kit-framed cap); returns its width
function Local.Cap(Parent: Instance, X: number, Y: number, Key: string, Size: number): number
	local TW = measure(Key, 20, "Bold", 400).X
	local CW = math.max(Size, math.ceil((TW + 8) / 0.76))
	local Img = QC.Image(QcArt, "PromptCap", Local.Race())
	local Cap = Local.New("ImageLabel", { Name = "Cap"; Image = Img or ""; BackgroundTransparency = 1; Position = UDim2.fromOffset(X, Y);
		Size = UDim2.fromOffset(CW, Size); ZIndex = 4 }, Parent)
	if not Img then Local.Skin(Cap, COL.Gold, COL.Slate) end
	Local.Tag(Cap, CAP_BOX, if Img then BG.Cap else nil)
	Local.New("TextLabel", { Name = "Key"; BackgroundTransparency = 1; Position = UDim2.fromScale(0.12, 0.15); Size = UDim2.fromScale(0.76, 0.7);
		Text = Key; TextSize = 20; FontFace = FACE.Bold; TextColor3 = COL.Bone; TextXAlignment = Enum.TextXAlignment.Center;
		TextYAlignment = Enum.TextYAlignment.Center; ZIndex = 5 }, Cap)
	return CW
end

function Local.Stroke(Obj: Instance, Name: string, Color: Color3, Thick: number, Pulse: boolean): UIStroke
	local S = Local.New("UIStroke", { Name = Name; Color = Color; Thickness = Thick; ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, Obj) :: UIStroke
	if Pulse and not Local.NoFlash() then
		TweenService:Create(S, TweenInfo.new(0.6, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true), { Transparency = 0.6 }):Play()
	end
	return S
end

---| The phone tray |---

function Local.Tray(Dyn: Instance, M: any, W: number, H: number)
	local Tray = Local.New("ScrollingFrame", {
		Name = "Cards"; BackgroundTransparency = 1; BorderSizePixel = 0; Position = UDim2.fromOffset(16, H - 236); Size = UDim2.fromOffset(W - 32, 232);
		CanvasSize = UDim2.fromOffset(16 + #M.Clues * 134, 0); ScrollingDirection = Enum.ScrollingDirection.X; ScrollBarThickness = 6;
		ScrollBarImageColor3 = COL.Gold; Selectable = false; ZIndex = 3;
	}, Dyn)
	for I, C in M.Clues do
		local Item = Local.New("Frame", { Name = "Item_" .. C.Id; BackgroundTransparency = 1; Position = UDim2.fromOffset(8 + (I - 1) * 134, 8);
			Size = UDim2.fromOffset(SLOT_W, 220); ZIndex = 2 }, Tray)
		Item:SetAttribute("QcItem", true)
		local Piece = if C.Found then Local.CardPiece(C) else "CardMissing"
		local Img = Local.Art(Piece)
		local Mini = Local.New("ImageButton", { Name = "Card_" .. C.Id; Image = Img or ""; ImageColor3 = if C.Found then rgb(255, 255, 255) else COL.Chalk;
			BackgroundTransparency = 1; AutoButtonColor = false; Selectable = true; Size = UDim2.fromOffset(SLOT_W, SLOT_H); ZIndex = 2 }, Item)
		if not Img then Local.Skin(Mini, if C.Found then COL.Gold:Lerp(COL.Bone, 0.5) else COL.Chalk, COL.Slate) end
		if Held == C.Id then Local.Stroke(Mini, "QcHeld", COL.Gold, 3, false) end
		Local.Label(Item, { Name = "Name"; X = 0; Y = SLOT_H + 4; W = SLOT_W; Text = if C.Found then (C.Name or C.Id) else "Not found yet";
			Size = 20; Kind = "Bold"; Color = if C.Found then COL.Bone else COL.Chalk; AlignX = Enum.TextXAlignment.Center; MaxH = 2 * Local.LineH(20, "Bold") })
		if C.Found then
			Mini.Activated:Connect(function(Input) if Local.PadDup(Input) then return end Local.Pick(C.Id) end)
		end
	end
	Tray:GetPropertyChangedSignal("CanvasPosition"):Connect(function() Local.Cull() Local.Threads(false) end)
end

---| Question sheets, answers, the solve |---

function Local.Sheets(Dyn: Instance, M: any, W: number, H: number)
	local X, Y, SW, SH
	if Ui.Phone then
		SW = SHEET_W + 40
		X, Y = (W - SW) / 2, 116
		SH = math.max(200, H - 116 - 244)
	else
		X, Y, SW, SH = 1100, 180, 760, 830
	end
	local Scroll = Local.New("ScrollingFrame", {
		Name = "Sheets"; BackgroundTransparency = 1; BorderSizePixel = 0; Position = UDim2.fromOffset(X, Y); Size = UDim2.fromOffset(SW, SH);
		CanvasSize = UDim2.fromOffset(0, 0); ScrollingDirection = Enum.ScrollingDirection.Y; ScrollBarThickness = 6;
		ScrollBarImageColor3 = COL.Gold; Selectable = false; ZIndex = 3;
	}, Dyn)
	local Yc = 10
	Ui.Answers = 0
	if M.Solved or M.Ready then
		for _, Q in M.Questions do
			if Q.State == "Answered" then Local.Sheet(Scroll, Q, 10, Yc, true) Yc += COMPACT_STEP end
		end
		if M.Solved then Yc = Local.SolvedBlock(Scroll, M, Yc) else Yc = Local.AnswerBlock(Scroll, Yc) end
	else
		for _, Q in M.Questions do Local.Sheet(Scroll, Q, 10, Yc, false) Yc += SHEET_STEP end
	end
	Scroll.CanvasSize = UDim2.fromOffset(0, Yc + 10)
	Scroll:GetPropertyChangedSignal("CanvasPosition"):Connect(function() Local.Cull() Local.Threads(false) end)
end

function Local.Sheet(Parent: Instance, Q: any, X: number, Y: number, Compact: boolean)
	local H = if Compact then COMPACT_H else SHEET_H
	local Sheet, Real = Local.Surface("ImageLabel", Parent, "Sheet_" .. Q.Id, "QuestionSheet", UDim2.fromOffset(X, Y), UDim2.fromOffset(SHEET_W, H))
	Sheet:SetAttribute("QcItem", true)
	Local.Tag(Sheet, if Compact then COMPACT_BOX else SHEET_BOX, if Real then BG.Paper else nil)
	local Ink = if Real then COL.Ink else COL.Bone
	local Dim = if Real then COL.InkDim else COL.Dim
	local Red = if Real then COL.InkRed else COL.Crimson
	local Ask = Q.Ask .. (if Q.Bonus then " (bonus)" else "")
	local AskH = if Compact then 34 else math.floor(0.195 * H) - 2
	Local.Label(Sheet, { Name = "Ask"; X = 28; CenterY = 4 + AskH / 2; W = SHEET_W - 56; MaxH = AskH; Text = Ask; Size = 24; Kind = "Bold"; Color = Ink })
	local K = key(CaseId, Q.Id)

	if Compact then -- answer mode: the seal and the insight only
		Local.Seal(Sheet, 30, 42, 44)
		local L = Local.Label(Sheet, { Name = "Insight"; X = 86; Y = 46; W = SHEET_W - 86 - 30; MaxH = 150 - 46; Text = Q.Insight or ""; Size = 20; Kind = "Italic"; Color = Ink })
		if Typed[K] then Typed[K] = nil Local.TypeOut(L) end
		return
	end

	local BX, BY = 30, math.floor(0.24 * H)
	local Kinds = {}
	for _, C in (Model and Model.Clues or {}) do Kinds[C.Id] = C end
	for S = 1, 2 do
		local Slot = Local.New("ImageButton", { Name = "Slot_" .. Q.Id .. "_" .. S; Image = Local.Art("Slot") or Theme.Images.SlotBg; BackgroundTransparency = 1;
			AutoButtonColor = false; Selectable = Q.State ~= "Answered"; Position = UDim2.fromOffset(BX + (S - 1) * 134, BY + 6);
			Size = UDim2.fromOffset(SLOT_W, SLOT_H); ZIndex = 3 }, Sheet)
		local In = if S == 1 then Q.A else Q.B
		local C = In and Kinds[In]
		if C then
			local Piece = Local.CardPiece(C)
			local Img = Local.Art(Piece)
			local Mini = Local.New("ImageLabel", { Name = "Mini"; Image = Img or ""; BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1); ZIndex = 2 }, Slot)
			if not Img then Local.Skin(Mini, COL.Gold:Lerp(COL.Bone, 0.5), COL.Slate) end
		end
		if Held and Q.State ~= "Answered" and not Pending[K] then Local.Stroke(Slot, "QcGlow", COL.Gold, 3, true) end
		Slot.Activated:Connect(function(Input) if Local.PadDup(Input) then return end Local.SlotClick(Q.Id, S) end)
	end

	local SX, SW = BX + 272, SHEET_W - 24 - (BX + 272)
	local Bottom = math.floor(240 / 252 * H) - 4
	if Q.State == "Answered" then
		Local.Seal(Sheet, SX, BY + 2, 56)
		Local.Label(Sheet, { Name = "Answered"; X = SX + 68; CenterY = BY + 30; W = SW - 68; Text = "Answered"; Size = 22; Kind = "Bold"; Color = Red })
		local L = Local.Label(Sheet, { Name = "Insight"; X = SX; Y = BY + 70; W = SW; MaxH = Bottom - (BY + 70); Text = Q.Insight or ""; Size = 20; Kind = "Italic"; Color = Ink })
		if Typed[K] then Typed[K] = nil Local.TypeOut(L) end
		return
	end
	local Hint = Local.HintFor(Q)
	local Text, Kind, Color
	if Pending[K] or Q.State == "Full" then
		Text, Kind, Color = "Checking the pair…", "Italic", Dim
	elseif Hint then
		Text, Kind, Color = (if Q.State == "Half" then "1 of 2 pinned. " else "") .. "Hint: " .. Hint, "Body", Ink
	elseif Q.State == "Half" then
		Text, Kind, Color = "1 of 2 pinned", "Body", Ink
	else
		Text, Kind, Color = "Drop a clue on the question it answers", "Italic", Dim
	end
	Local.Label(Sheet, { Name = "State"; X = SX; Y = BY + 20; W = SW; MaxH = Bottom - (BY + 20); Text = Text; Size = 20; Kind = Kind; Color = Color })
end

-- the Bell Tower seal, tinted crimson (plan ruling 11); never the kit Seal
function Local.Seal(Parent: Instance, X: number, Y: number, Size: number)
	local Id = BellArt and typeof(BellArt.Seal) == "number" and BellArt.Seal > 0 and ("rbxassetid://" .. BellArt.Seal) or nil
	Local.New("ImageLabel", { Name = "Seal"; Image = Id or Theme.Images.Pip; ImageColor3 = COL.Crimson; BackgroundTransparency = 1;
		Position = UDim2.fromOffset(X, Y); Size = UDim2.fromOffset(Size, Size); ZIndex = 4 }, Parent)
end

function Local.AnswerBlock(Scroll: Instance, Y: number): number
	local Def = Cases[CaseId :: string]
	local Options = Def.Deduction and Def.Deduction.Options or {}
	Y += 8
	local T1 = Local.Label(Scroll, { Name = "YourAnswer"; X = 16; Y = Y; W = 700; Text = "Your answer"; Size = 24; Kind = "Bold"; Color = COL.Bone })
	T1:SetAttribute("QcItem", true)
	Y += Local.LineH(24, "Bold") + 2
	local T2 = Local.Label(Scroll, { Name = "PickOne"; X = 16; Y = Y; W = 700; Text = "Pick the answer your clues point to."; Size = 20; Kind = "Italic"; Color = COL.Dim })
	T2:SetAttribute("QcItem", true)
	Y += Local.LineH(20, "Italic") + 10
	for I, Opt in Options do
		local X0, Y0 = 10 + ((I - 1) % 2) * 366, Y + ((I - 1) // 2) * 186
		local Card, Real = Local.Surface("ImageButton", Scroll, "Answer_" .. I, "AnswerCard", UDim2.fromOffset(X0, Y0), UDim2.fromOffset(340, 170))
		Card:SetAttribute("QcItem", true)
		Local.Tag(Card, ANSWER_BOX, if Real then BG.Paper else nil)
		Local.Label(Card, { Name = "Option"; X = 0.12 * 340 + 2; W = 0.76 * 340 - 4; CenterY = 85; MaxH = 0.6 * 170 - 4; Text = tostring(Opt);
			Size = 22; Kind = "Bold"; Color = if Real then COL.Ink else COL.Bone; AlignX = Enum.TextXAlignment.Center })
		Card.Activated:Connect(function(Input) if Local.PadDup(Input) then return end Local.Deduce(I) end)
		Ui.Answers += 1
	end
	return Y + math.ceil(#Options / 2) * 186
end

function Local.SolvedBlock(Scroll: Instance, M: any, Y: number): number
	local Def = Cases[CaseId :: string]
	local Options = Def.Deduction and Def.Deduction.Options or {}
	local Saved = Local.Saved(CaseId) or {}
	local Pick = Saved.Answer or Saved.Option or LastOption[CaseId :: string]
	local Text = if typeof(Pick) == "number" then Options[Pick] elseif typeof(Pick) == "string" then Pick else nil
	Text = Text or Def.Name or ""
	Y += 10
	local Card, Real = Local.Surface("ImageLabel", Scroll, "Chosen", "AnswerCard", UDim2.fromOffset(130, Y), UDim2.fromOffset(480, 240))
	Card:SetAttribute("QcItem", true)
	Local.Tag(Card, ANSWER_BOX, if Real then BG.Paper else nil)
	Local.Label(Card, { Name = "Option"; X = 0.12 * 480 + 2; W = 0.76 * 480 - 4; CenterY = 120; MaxH = 0.6 * 240 - 4; Text = tostring(Text);
		Size = 30; Kind = "Bold"; Color = if Real then COL.Ink else COL.Bone; AlignX = Enum.TextXAlignment.Center })

	-- the stamp: StampInk (a frame only) tinted crimson, holding the live word SOLVED
	local StampImg = Local.Art("StampInk")
	local Stamp = Local.New("ImageLabel", { Name = "Stamp"; Image = StampImg or Theme.Images.FrameThin; ImageColor3 = COL.StampRed; BackgroundTransparency = 1;
		Position = UDim2.fromOffset(130, Y + 210); Size = UDim2.fromOffset(480, 180); Rotation = -6; ZIndex = 6 }, Scroll)
	if not StampImg then Stamp.ScaleType = Enum.ScaleType.Slice Stamp.SliceCenter = Rect.new(32, 32, 96, 96) end
	Stamp:SetAttribute("QcItem", true)
	Local.Tag(Stamp, "0.06,0.1,0.94,0.9", nil)
	local Word = Local.New("TextLabel", { Name = "Solved"; BackgroundTransparency = 1; Position = UDim2.fromOffset(40, 40); Size = UDim2.fromOffset(400, 100);
		Text = "SOLVED"; TextSize = 64; FontFace = FACE.Title; TextColor3 = COL.StampRed; TextXAlignment = Enum.TextXAlignment.Center;
		TextYAlignment = Enum.TextYAlignment.Center; ZIndex = 7 }, Stamp) :: TextLabel
	if Stamping then
		Stamping = false
		Local.Sound("Stamp", 1.2, 0.9)
		Stamp.ImageTransparency = 1
		Word.TextTransparency = 1
		local Info = TweenInfo.new(if Local.Reduced() then 0.2 else 0.16, Enum.EasingStyle.Sine)
		TweenService:Create(Stamp, Info, { ImageTransparency = 0 }):Play()
		TweenService:Create(Word, Info, { TextTransparency = 0 }):Play()
		if not Local.Reduced() then
			local Sc = Local.New("UIScale", { Scale = 1.8 }, Stamp)
			TweenService:Create(Sc, TweenInfo.new(0.18, Enum.EasingStyle.Back), { Scale = 1 }):Play()
		end
	end
	local Tail = Y + 400
	if M.SolvedText and M.SolvedText ~= "" then
		local L, H = Local.Label(Scroll, { Name = "SolvedText"; X = 16; Y = Tail; W = 700; MaxH = 4 * Local.LineH(22, "Italic"); Text = M.SolvedText; Size = 22; Kind = "Italic"; Color = COL.Bone })
		L:SetAttribute("QcItem", true)
		Tail += H
	end
	return Tail + 10
end

---| The foot: control hints per input kind |---

function Local.Foot(Dyn: Instance, H: number)
	local Kind = if Kit.InputKind then Kit.InputKind() else "Keyboard"
	local Y = H - 50
	local function name(Code: Enum.KeyCode, Default: string): string
		if Kit.KeyName then
			local Ok, N = pcall(Kit.KeyName, Code)
			if Ok and typeof(N) == "string" then return N end
		end
		return Default
	end
	local Rows
	if Kind == "Touch" then
		Local.Label(Dyn, { Name = "Hint"; X = 96; CenterY = Y + 20; W = 900; Text = "Tap a clue, then a slot"; Size = 20; Color = COL.Bone })
		return
	elseif Kind == "Gamepad" then
		Rows = { { name(Enum.KeyCode.ButtonA, "A"), "Pick up / pin" }, { name(Enum.KeyCode.ButtonX, "X"), "Inspect" }, { name(Enum.KeyCode.ButtonB, "B"), "Close" } }
	else
		Rows = { { "Click", "Pick up / pin" }, { "Right click", "Inspect" }, { "Esc", "Close" } }
	end
	local X = 96
	for I, R in Rows do
		local KeyW
		if (utf8.len(R[1]) or #R[1]) <= 4 then
			KeyW = Local.Cap(Dyn, X, Y, R[1], 40)
		else
			KeyW = math.ceil(measure(R[1], 20, "Bold", 400).X) + 6
			Local.Label(Dyn, { Name = "Key" .. I; X = X; CenterY = Y + 20; W = KeyW; Text = R[1]; Size = 20; Kind = "Bold"; Color = COL.Gold })
		end
		local LW = math.ceil(measure(R[2], 20, "Body", 400).X) + 6
		Local.Label(Dyn, { Name = "Does" .. I; X = X + KeyW + 10; CenterY = Y + 20; W = LW; Text = R[2]; Size = 20; Color = COL.Bone })
		X += KeyW + 10 + LW + 36
	end
end

---| Threads, culling, the lens |---

function Local.Scale(): number
	if not Ui then return 1 end
	local B = Ui.Board
	return if B.Size.X.Offset > 0 and B.AbsoluteSize.X > 0 then B.AbsoluteSize.X / B.Size.X.Offset else 1
end

function Local.ToBoard(P: Vector2): Vector2 return (P - Ui.Board.AbsolutePosition) / Local.Scale() end

function Local.InView(Obj: GuiObject, Scroll: GuiObject?): boolean
	if not Scroll then return true end
	local A, S, P0, S0 = Obj.AbsolutePosition, Obj.AbsoluteSize, Scroll.AbsolutePosition, Scroll.AbsoluteSize
	return A.X >= P0.X - 2 and A.Y >= P0.Y - 2 and A.X + S.X <= P0.X + S0.X + 2 and A.Y + S.Y <= P0.Y + S0.Y + 2
end

-- texts in a scroller show only when their piece is fully in view (nothing clipped, nothing overlapping the frame)
function Local.Cull()
	if not Ui or not Ui.Dyn then return end
	for _, Name in { "Cards", "Sheets" } do
		local Sc = Ui.Dyn:FindFirstChild(Name)
		if not Sc then continue end
		for _, It in Sc:GetChildren() do
			if not (It:IsA("GuiObject") and It:GetAttribute("QcItem")) then continue end
			local Show = Local.InView(It, Sc) and not (LensId ~= nil and Name == "Cards")
			if It:IsA("TextLabel") then It.Visible = Show end
			for _, L in It:GetDescendants() do if L:IsA("TextLabel") then L.Visible = Show end end
		end
	end
end

function Local.Threads(Animate: boolean)
	if not Ui or not Ui.Dyn or not Model then return end
	local Old = Ui.Dyn:FindFirstChild("Threads")
	if Old then Old:Destroy() end
	local Layer = Local.New("Frame", { Name = "Threads"; BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1); ZIndex = 8 }, Ui.Dyn)
	local Cards = Ui.Dyn:FindFirstChild("Cards") :: GuiObject?
	local Sheets = Ui.Dyn:FindFirstChild("Sheets") :: GuiObject?
	if not Cards or not Sheets then return end
	local Sc = Local.Scale()
	local Img = Local.Art("Thread") or Theme.Images.BarFill
	for _, Q in Model.Questions do
		local K = key(CaseId, Q.Id)
		local Draw = Animate and Fresh[K] == true and Q.State == "Answered"
		if Draw then Fresh[K] = nil end
		for S, Id in { Q.A, Q.B } do
			if not Id then continue end
			local Card = Cards:FindFirstChild("Card_" .. Id, true) :: GuiObject?
			local Slot = Sheets:FindFirstChild("Slot_" .. Q.Id .. "_" .. S, true) :: GuiObject?
			if not (Card and Slot) then continue end
			local Holder = if Card.Parent and Card.Parent:GetAttribute("QcItem") then Card.Parent :: GuiObject else Card
			if not Local.InView(Holder, Cards) or not Local.InView(Slot.Parent :: GuiObject, Sheets) then continue end
			local P1 = Local.ToBoard(Card.AbsolutePosition + Vector2.new(Card.AbsoluteSize.X / 2, 3 * Sc))
			local P2 = Local.ToBoard(Slot.AbsolutePosition + Vector2.new(Slot.AbsoluteSize.X / 2, 8 * Sc))
			local D = P2 - P1
			local Len = D.Magnitude
			local Mid = (P1 + P2) / 2
			local T = Local.New("ImageLabel", { Name = "Thread"; Image = Img; ImageColor3 = COL.Thread; BackgroundTransparency = 1;
				AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromOffset(Mid.X, Mid.Y); Size = UDim2.fromOffset(Len, 6);
				Rotation = math.deg(math.atan2(D.Y, D.X)); ZIndex = 1 }, Layer)
			if Draw and not Local.Reduced() then
				T.Position = UDim2.fromOffset(P1.X, P1.Y)
				T.Size = UDim2.fromOffset(0, 6)
				TweenService:Create(T, TweenInfo.new(0.4, Enum.EasingStyle.Quad), { Position = UDim2.fromOffset(Mid.X, Mid.Y); Size = UDim2.fromOffset(Len, 6) }):Play()
			end
		end
		if Draw then Local.Sound("Tick", 0.7, 0.8) end
	end
end

function Local.Inspect(Id: string?)
	if not Id or not Model then return end
	local C = Local.Clue(Model, Id)
	if not C then return end
	if not C.Found then Local.Mark(Id) return end
	LensId = if LensId == Id then nil else Id
	Local.Render()
end

function Local.Lens(Dyn: Instance, Id: string)
	local C = Local.Clue(Model, Id)
	if not C then LensId = nil return end
	local Def = Cases[CaseId :: string].Clues[Id] or {}
	local W, H = Ui.Board.Size.X.Offset, Ui.Board.Size.Y.Offset
	local Cx, Cy = W / 2, H / 2
	local Card = Ui.Dyn and Ui.Dyn:FindFirstChild("Cards") and (Ui.Dyn.Cards :: Instance):FindFirstChild("Card_" .. Id, true) :: GuiObject?
	if Card and not Ui.Phone then
		task.defer(function() end)
		local P = Local.ToBoard(Card.AbsolutePosition + Card.AbsoluteSize / 2)
		if P.X == P.X and P.X > 0 then Cx, Cy = P.X, P.Y end
	end
	Cx, Cy = math.clamp(Cx, 170, W - 170), math.clamp(Cy, 170, H - 170)
	local Img = Local.Art("Lens")
	local Lens = Local.New("ImageButton", { Name = "Lens"; Image = Img or Theme.Images.OrbRing; ImageColor3 = if Img then rgb(255, 255, 255) else COL.Gold;
		BackgroundTransparency = 1; AutoButtonColor = false; Selectable = false; AnchorPoint = Vector2.new(0.5, 0.5);
		Position = UDim2.fromOffset(Cx, Cy); Size = UDim2.fromOffset(320, 320); ZIndex = 20 }, Dyn)
	Local.New("ImageLabel", { Name = "Glass"; Image = Theme.Images.OrbFill; ImageColor3 = COL.Slate; ImageTransparency = 0.08; BackgroundTransparency = 1;
		AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromScale(0.86, 0.86); ZIndex = 1 }, Lens)
	Local.Tag(Lens, "0.09,0.09,0.91,0.91", nil)
	Local.Label(Lens, { Name = "Full"; X = 30; W = 260; CenterY = 160; MaxH = 250; Text = Def.Text or C.Text or C.Name or Id; Size = 22;
		Color = COL.Bone; AlignX = Enum.TextXAlignment.Center })
	Lens.Activated:Connect(function() LensId = nil Local.Render() end)
	if not Local.Reduced() then
		local Sc = Local.New("UIScale", { Scale = 0.9 }, Lens)
		TweenService:Create(Sc, TweenInfo.new(0.18, Enum.EasingStyle.Back), { Scale = 1 }):Play()
	end
end

---| Playing it |---

-- a gamepad A press is handled by the CAS bind; skip the Activated it also causes
function Local.PadDup(Input: InputObject?): boolean
	return Input ~= nil and Input.KeyCode == Enum.KeyCode.ButtonA and os.clock() - LastPadA < 0.25
end

function Local.Pick(Id: string)
	local C = Local.Clue(Model, Id)
	if not C or not C.Found then return end
	if Held == Id then
		if Ui and Ui.Phone then Local.Inspect(Id) return end
		Held = nil
	else
		Held = Id
		Local.Sound("Tick", 0.6)
	end
	Local.Render()
	if Held and Kit.InputKind and Kit.InputKind() == "Gamepad" then Local.WantFirstSlot = true end
end

function Local.SlotClick(Q: string, S: number)
	local Row = Local.Question(Model, Q)
	if not Row or Row.State == "Answered" or Pending[key(CaseId, Q)] then Local.Sound("Reject", 0.6) return end
	if Held then Local.Pin(Q, S, Held) return end
	local P = PinsBy[CaseId :: string]
	if P and P[Q] and P[Q][S] then -- take that clue back out
		local New = table.clone(P)
		local R = table.clone(P[Q])
		R[S] = nil
		New[Q] = if R[1] or R[2] then R else nil
		PinsBy[CaseId :: string] = New
		Local.Render()
	end
end

-- the one pin path (a drop, a tap, A on a slot, and the probe's WallPin)
function Local.Pin(Q: string, Slot: number, Clue: string): (boolean, string?)
	if not IsOpen or not CaseId then return false, "closed" end
	local M = Local.Build()
	Model = M
	local Row = Local.Question(M, Q)
	if not Row then return false, "no question " .. tostring(Q) end
	if Slot ~= 1 and Slot ~= 2 then return false, "bad slot" end
	local C = Local.Clue(M, Clue)
	if not C or not C.Found then return false, "clue not found" end
	local K = key(CaseId, Q)
	if Row.State == "Answered" then return false, "answered" end
	if Pending[K] then return false, "pending" end
	local New, Pair = QC.Pin(PinsBy[CaseId], Q, Slot, Clue)
	PinsBy[CaseId] = New
	Held = nil
	Local.Sound("Tick", 0.7, 1.1)
	if Pair then
		local At = os.clock()
		Pending[K] = At
		local Case = CaseId
		Packets.QuestAction:Fire({ Action = "Link"; Case = Case; A = Pair.A; B = Pair.B; Question = Q })
		task.delay(4, function() -- no answer (cooldown, dropped): give the slots back without counting a miss
			if Pending[K] == At then
				Pending[K] = nil
				local Now = Case and Cases[Case] and QC.Wall(Cases[Case], Local.Saved(Case), PinsBy[Case])
				local R = Now and Local.Question(Now, Q)
				if not (R and R.State == "Answered") then PinsBy[Case :: string] = QC.Unpin(PinsBy[Case :: string], Q) end
				Local.Render()
			end
		end)
	end
	Local.Render()
	return true, if Pair then "sent" else "pinned"
end

-- which question a hit / miss belongs to: the server's id when it sends one, else the pinned pair
function Local.FindQuestion(D: any): string?
	local Case = tostring(D.Case)
	local Def = Cases[Case]
	if not Def then return nil end
	for _, Q in Def.Questions or {} do
		if Q.Id == D.Question or Q.Id == D.Id then return Q.Id end
	end
	local A, B = tostring(D.A), tostring(D.B)
	for Q, Row in PinsBy[Case] or {} do
		if (Row[1] == A and Row[2] == B) or (Row[1] == B and Row[2] == A) then return Q end
	end
	return nil
end

function Local.OnHit(D: any)
	if typeof(D) ~= "table" then return end
	local Q = Local.FindQuestion(D)
	if Q then
		local K = key(tostring(D.Case), Q)
		Pending[K] = nil
		Fresh[K] = true
		Typed[K] = true
	end
	Local.Sound("Confirm", 0.8)
	Local.Render()
end

function Local.OnMiss(D: any)
	if typeof(D) ~= "table" then return end
	local Case = tostring(D.Case)
	local Q = Local.FindQuestion(D)
	if Q then
		Pending[key(Case, Q)] = nil
		MissBy[Case] = QC.Miss(MissBy[Case], Q)
		PinsBy[Case] = QC.Unpin(PinsBy[Case], Q)
	end
	Local.Sound("Reject", 0.8)
	if not IsOpen or Case ~= CaseId then return end
	Local.Render()
	task.spawn(function()
		RunService.Heartbeat:Wait()
		for _, Id in { D.A, D.B } do Local.Shake(tostring(Id)) end
	end)
end

function Local.Shake(Id: string)
	local Cards = Ui and Ui.Dyn and Ui.Dyn:FindFirstChild("Cards")
	local Card = Cards and Cards:FindFirstChild("Card_" .. Id, true) :: GuiObject?
	if not Card then return end
	if Local.Reduced() then
		local S = Local.Stroke(Card, "QcMiss", COL.Crimson, 3, false)
		task.delay(0.2, function() S:Destroy() end)
		return
	end
	local Home = Card.Position
	task.spawn(function()
		for I = 1, 6 do
			if not Card.Parent then return end
			Card.Position = Home + UDim2.fromOffset(if I % 2 == 0 then -6 else 6, 0)
			task.wait(0.04)
		end
		if Card.Parent then Card.Position = Home end
	end)
end

function Local.Deduce(I: number)
	if not CaseId then return end
	LastOption[CaseId] = I
	Local.Sound("Tick", 0.7)
	Packets.QuestAction:Fire({ Action = "Deduce"; Case = CaseId; Option = I })
end

function Local.OnSolved(D: any)
	if not IsOpen then return end
	if typeof(D) == "table" and D.Case ~= nil and tostring(D.Case) ~= CaseId then return end
	Stamping = true
	task.delay(0.2, Local.Render)
end

---| Console and keys |---

function Local.Select(Name: string?)
	if not Ui or not Ui.Dyn or not IsOpen then return end
	if not (Kit.InputKind and Kit.InputKind() == "Gamepad") then return end
	local Pick = nil
	if Local.WantFirstSlot then
		Local.WantFirstSlot = nil
		for _, D in Ui.Dyn:GetDescendants() do
			if D:IsA("ImageButton") and D.Selectable and string.sub(D.Name, 1, 5) == "Slot_" and D:FindFirstChild("QcGlow") then Pick = D break end
		end
	end
	if not Pick and Name then Pick = Ui.Dyn:FindFirstChild(Name, true) end
	if not Pick then
		local Cards = Ui.Dyn:FindFirstChild("Cards")
		Pick = Cards and Cards:FindFirstChildWhichIsA("ImageButton", true)
		if not Pick then Pick = Ui.Dyn:FindFirstChild("Answer_1", true) end
	end
	if Pick and Pick:IsA("GuiObject") and Pick.Selectable then GuiService.SelectedObject = Pick end
end

function Local.Back()
	if LensId then LensId = nil Local.Render() return end
	if Held then Held = nil Local.Render() return end
	Shared.Close()
end

function Local.Bind()
	if Local.Bound then return end
	Local.Bound = true
	local Begin = Enum.UserInputState.Begin
	ContextActionService:BindActionAtPriority("QcWallBack", function(_, St)
		if St ~= Begin then return Enum.ContextActionResult.Pass end
		Local.Back()
		return Enum.ContextActionResult.Sink
	end, false, 3000, Enum.KeyCode.ButtonB, Enum.KeyCode.Escape)
	ContextActionService:BindActionAtPriority("QcWallInspect", function(_, St)
		if St ~= Begin then return Enum.ContextActionResult.Pass end
		if LensId then LensId = nil Local.Render() return Enum.ContextActionResult.Sink end
		local Sel = GuiService.SelectedObject
		if Sel and Ui and Sel:IsDescendantOf(Ui.Gui) and string.sub(Sel.Name, 1, 5) == "Card_" then Local.Inspect(string.sub(Sel.Name, 6)) end
		return Enum.ContextActionResult.Sink
	end, false, 3000, Enum.KeyCode.ButtonX)
	ContextActionService:BindActionAtPriority("QcWallPick", function(_, St)
		if St ~= Begin then return Enum.ContextActionResult.Pass end
		local Sel = GuiService.SelectedObject
		if not (Sel and Ui and Sel:IsDescendantOf(Ui.Gui)) then return Enum.ContextActionResult.Pass end
		LastPadA = os.clock()
		local N = Sel.Name
		if string.sub(N, 1, 5) == "Card_" then
			local Id = string.sub(N, 6)
			local C = Local.Clue(Model, Id)
			if C and C.Found then Local.Pick(Id) elseif C then Local.Mark(Id) end
		elseif string.sub(N, 1, 5) == "Slot_" then
			local Q, S = string.match(N, "^Slot_(.+)_(%d)$")
			if Q and S then Local.SlotClick(Q, tonumber(S) :: number) end
		elseif string.sub(N, 1, 7) == "Answer_" then
			Local.Deduce(tonumber(string.sub(N, 8)) or 0)
		elseif N == "Close" then
			Shared.Close()
		end
		return Enum.ContextActionResult.Sink
	end, false, 3000, Enum.KeyCode.ButtonA)
end

function Local.Unbind()
	if not Local.Bound then return end
	Local.Bound = false
	for _, A in { "QcWallBack", "QcWallInspect", "QcWallPick" } do ContextActionService:UnbindAction(A) end
end

---| Probe (Studio checks) |---

function Local.Info(): any
	local M = Local.Build()
	if not M then return { Open = IsOpen } end
	local Cards, Sheets = {}, {}
	for _, C in M.Clues do table.insert(Cards, { Id = C.Id; Kind = C.Kind; Found = C.Found }) end
	for _, Q in M.Questions do table.insert(Sheets, { Id = Q.Id; State = Q.State; Hint = Local.HintFor(Q) }) end
	return { Open = IsOpen; Case = CaseId; Ask = Local.Ask(); Progress = M.Progress; Cards = Cards; Sheets = Sheets;
		Answers = if Ui then Ui.Answers else 0; Solved = M.Solved; Held = Held }
end

---| API |---

function Shared.IsOpen(): boolean return IsOpen end

function Shared.Open(Id: string?): boolean
	if not Ui then return false end
	local Want = if typeof(Id) == "string" and Cases[Id] then Id else Local.DefaultCase()
	if not Want then return false end
	if Want ~= CaseId then Held = nil LensId = nil end
	CaseId = Want
	IsOpen = true
	Ui.Gui.Enabled = true
	Player:SetAttribute("NHMenuOpen", true)
	local Blur = Lighting:FindFirstChild("QcBlur") or Instance.new("BlurEffect")
	Blur.Name = "QcBlur";
	(Blur :: BlurEffect).Size = 12
	Blur.Parent = Lighting
	Local.Render()
	return true
end

function Shared.Close()
	if not IsOpen then return end
	IsOpen = false
	Held = nil
	LensId = nil
	Local.Unbind()
	if Ui then
		local Sel = GuiService.SelectedObject
		if Sel and Sel:IsDescendantOf(Ui.Gui) then GuiService.SelectedObject = nil end
		Ui.Gui.Enabled = false
		if Ui.Dyn then Ui.Dyn:Destroy() Ui.Dyn = nil end
	end
	local Blur = Lighting:FindFirstChild("QcBlur")
	if Blur then Blur:Destroy() end
	Player:SetAttribute("NHMenuOpen", nil)
end

function Shared.OnStart()
	Ui = Local.MakeGui()
	local function viewport()
		local P = Kit.Phone and Kit.Phone() or false
		if Ui and P ~= Ui.Phone then Local.Rebuild() end
	end
	local Cam = Workspace.CurrentCamera
	if Cam then Cam:GetPropertyChangedSignal("ViewportSize"):Connect(viewport) end
	if Kit.PreviewChanged then Kit.PreviewChanged:Connect(viewport) end
	if Kit.InputKindChanged then Kit.InputKindChanged:Connect(function() if IsOpen then Local.Render() end end) end
	StateController.ProfileUpdated:Connect(function(_, Action)
		if IsOpen and Action and Action.type == "SetQuests" then Local.Render() end
	end)
	Fx.On("LinkHit", Local.OnHit)
	Fx.On("LinkMiss", Local.OnMiss)
	Fx.On("Solved", Local.OnSolved)
	task.spawn(function()
		local Mod = script.Parent:WaitForChild("HudState", 10)
		if not Mod then return end
		local Ok, Hud = pcall(require, Mod)
		if not Ok or typeof(Hud) ~= "table" or not Hud.Probe then return end
		Hud.Probe("Wall", function(Id: string?) return Shared.Open(Id) end)
		Hud.Probe("WallClose", function() Shared.Close() return true end)
		Hud.Probe("WallPin", function(Q: string, Slot: number, Clue: string)
			local Ok2, Why = Local.Pin(Q, Slot, Clue)
			return { Ok = Ok2; Why = Why }
		end)
		Hud.Probe("WallInfo", Local.Info)
	end)
end

return Shared
