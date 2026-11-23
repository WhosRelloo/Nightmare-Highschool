--[[
	Dialogue (client). The server decides everything; this only shows what it sends and returns the chosen index.
	Clicking the line finishes it; walking away (or the Goodbye reply) leaves.
	Talk cinematic (1.35.1): when a conversation opens with an NPC (Data.Model), the camera eases into an over-the-shoulder
	shot of them (a slightly narrower field of view, thin letterbox bars, a soft depth of field, a slow drift), and eases
	back when it ends. Reduce Motion: a cut, no drift. Skipped in the cinematic view, the main menu, first person, and
	when the NPC is far away.

	(2.38) Quiet Corners QC3: all-new art (spec docs/superpowers/specs/2026-11-21-quiet-corners-ui-design.md §8,
	plan 2026-11-22-quiet-corners-ui.md Task R8 and ruling 8). Art ids: Config.DialogueArt; rules: Functions.QuietCorners.
	- Ribbon: a 9-slice parchment ribbon, bottom-left, that grows upward for long lines; the Line (24 px ink) is typed on it
	  (CHARS_PER_SECOND), and the Nib bobs at the right end of the last line once it has finished.
	- Card: CallingCard<local player's race> riding on the ribbon's top margin, with the speaker's clique crest
	  (CrestFlip<Clique>, a 4 x 4 flipbook; no clique = Unaffiliated, never the school Seal), the name (24 px bold caps)
	  and QC.CardSub (clique name · role · relationship, 20 px).
	- Crest: the entrance (drop, press, one light-catch) and an idle catch every 5-8 s, never while a line is typing.
	  Reduce Motion: frame 0 only, one 0.2 s fade. Hide stops it.
	- Replies: ReplyTab<Race> / ReplyTabOn<Race> tabs stacked upward from the bottom-right (step 78, 72 over 5 replies;
	  a reply too long for its tab gets the taller 84 step / 76 tab, never two lines), a number socket, and a Tone mark
	  only when the node's Tones[i] sets one (owner's decision: tones for new content only).
	- Phones: the ribbon spans the bottom and the replies stack above it on the right.
	- No art id yet (0): the kit fallbacks (Kit.Decorate, Kit.ChoiceRow at 44 px with 22 px text).
	- Studio probes (through HudState.Probe): Dialogue(Data), DialogueClose(), DialogueInfo().
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local UserInputService = game:GetService(`UserInputService`)
local TweenService = game:GetService(`TweenService`)
local StarterGui = game:GetService(`StarterGui`)
local TextService = game:GetService(`TextService`) -- (2.38)
local GuiService = game:GetService(`GuiService`) -- (2.38)

---| Modules |---

local Packets = require(ReplicatedStorage.Remotes.Packets)
local CameraLease = require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`CameraLease`)) -- (2.22.0) the talk shot takes a lease
local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`)) -- NH UI kit
local KitColors = Kit.Theme.Colors
local QC = require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`QuietCorners`)) -- (2.38)
local Art = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`DialogueArt`)) -- (2.38)

local Player = Players.LocalPlayer
local CHARS_PER_SECOND = 55

local NUMBER_KEYS = {
	[Enum.KeyCode.One] = 1, [Enum.KeyCode.Two] = 2, [Enum.KeyCode.Three] = 3,
	[Enum.KeyCode.Four] = 4, [Enum.KeyCode.Five] = 5, [Enum.KeyCode.Six] = 6,
	[Enum.KeyCode.Seven] = 7, [Enum.KeyCode.Eight] = 8, [Enum.KeyCode.Nine] = 9,
}

local RELATION_COLORS = {
	Hostile = Color3.fromRGB(230, 80, 80);
	Rival = Color3.fromRGB(240, 150, 90);
	Acquaintance = Color3.fromRGB(200, 200, 200);
	Friendly = Color3.fromRGB(130, 210, 140);
	Trusted = Color3.fromRGB(120, 190, 255);
}

-- (2.38) colours: text, and the art's measured backgrounds (QcBg, for the spec §9 contrast check)
local BONE = Color3.fromRGB(236, 226, 206)
local DIM = Color3.fromRGB(200, 188, 168)
local INK = Color3.fromRGB(40, 22, 16)
local GOLD = KitColors.Gold or Color3.fromRGB(212, 175, 95)
local CARD_IRON = Color3.fromRGB(44, 39, 38)
local RIBBON_PAPER = Color3.fromRGB(169, 155, 133)
local TAB_IRON = Color3.fromRGB(41, 37, 36)
local TAB_VELVET = Color3.fromRGB(131, 47, 55)

-- (2.38) fonts (Enum.Font, so TextService can measure them)
local FONT_BODY = Kit.Theme.Fonts.Body
local FONT_BOLD = Kit.Theme.Fonts.BodyBold or Kit.Theme.Fonts.Title

-- (2.38) layout, design px on 1920 x 1080 (Kit.AutoScale scales the whole gui)
local RIBBON_W, RIBBON_MIN_H = 1100, 150
local RIBBON_X, RIBBON_BOTTOM = 110, 100
local LINE_X0, LINE_W = 0.12, 0.74 -- of the ribbon's width (its text box is 0.10 .. 0.90)
local CARD_W, CARD_H = 520, 120
local CREST_SIZE = UDim2.fromOffset(94, 94)
local TEXT_X, TEXT_W = 121, 371 -- the card's name and sub (its text box ends at 988 / 1040 = 494 px)
local TAB_W, TAB_H, TAB_STEP = 540, 69, 78
local TAB_TALL_H, TAB_TALL_STEP = 76, 84
local TAB_TIGHT_STEP = 72
local KIT_ROW_H, KIT_ROW_STEP = 44, 52
local CHOICES_RIGHT, CHOICES_BOTTOM = 50, 77
local PHONE_GUTTER = 24
local FLIP = QC.FLIP

local Local = {}
local Shared = {}

local Ui = nil
local Current = nil -- { Id, Choices, Tones, Typing, Waiting, Pressed }
local BackpackWas = nil


---| talk cinematic (1.35.1) |---

local RunService = game:GetService(`RunService`)
local Lighting = game:GetService(`Lighting`)
local Shot = nil :: any -- { Model, Home (camera CFrame), Fov, Conn, Bars, Dof, T0 }
local TalkOutUntil = 0 -- (2.22.0) the lease outlives the shot by the ease back out

function Local.Head(M: Model?): BasePart?
	return M and (M:FindFirstChild(`Head`) or M:FindFirstChild(`HumanoidRootPart`)) :: BasePart?
end

function Local.ShotBars(On: boolean)
	local PG = Player:FindFirstChild(`PlayerGui`)
	if not PG then return end
	local G = PG:FindFirstChild(`NHTalkBars`)
	if not G then
		G = Instance.new(`ScreenGui`)
		G.Name = `NHTalkBars`
		G.IgnoreGuiInset = true
		G.ResetOnSpawn = false
		G.DisplayOrder = 3 -- under the dialogue box and the HUD
		G:SetAttribute(`ShowInCinematic`, true)
		for _, Top in { true, false } do
			local B = Instance.new(`Frame`)
			B.Name = if Top then `Top` else `Bottom`
			B.BorderSizePixel = 0
			B.BackgroundColor3 = Color3.new(0, 0, 0)
			B.AnchorPoint = Vector2.new(0, if Top then 0 else 1)
			B.Position = UDim2.fromScale(0, if Top then 0 else 1)
			B.Size = UDim2.fromScale(1, 0)
			B.Parent = G
		end
		G.Parent = PG
	end
	G.Enabled = true
	for _, B in G:GetChildren() do
		if B:IsA(`Frame`) then
			TweenService:Create(B, TweenInfo.new(0.45, Enum.EasingStyle.Quint, Enum.EasingDirection.Out), { Size = UDim2.fromScale(1, if On then 0.055 else 0) }):Play()
		end
	end
end

-- where the camera sits: over your shoulder, looking at the NPC's face
function Local.ShotFrame(M: Model): CFrame?
	local Char = Player.Character
	local Me, Them = Local.Head(Char), Local.Head(M)
	if not (Me and Them) then return nil end
	local Flat = (Them.Position - Me.Position) * Vector3.new(1, 0, 1)
	if Flat.Magnitude < 0.5 then return nil end
	local Fwd = Flat.Unit
	local Right = Fwd:Cross(Vector3.yAxis)
	local At = Me.Position - Fwd * 5.5 + Right * 4.3 + Vector3.new(0, 1, 0)
	local Look = Them.Position + Vector3.new(0, 0.2, 0) + Right * 0.4
	return CFrame.lookAt(At, Look)
end

function Local.ShotIn(M: any)
	if Shot or typeof(M) ~= `Instance` or not M:IsA(`Model`) or not M.Parent then return end
	if Player:GetAttribute(`InMainMenu`) == true then return end
	local Cine = script.Parent:FindFirstChild(`Cinematic`)
	local Ok, C = pcall(function() return Cine and require(Cine) end)
	if Ok and C and C.IsOn and C.IsOn() then return end
	local Cam = workspace.CurrentCamera
	local Char = Player.Character
	local Me, Them = Local.Head(Char), Local.Head(M)
	if not (Cam and Me and Them) or (Me.Position - Them.Position).Magnitude > 20 then return end
	if (Cam.CFrame.Position - Me.Position).Magnitude < 1 then return end -- first person: leave it alone
	local Frame = Local.ShotFrame(M)
	if not Frame then return end
	local Calm = Kit.ReducedMotion()
	Shot = { Model = M; Home = Cam.CFrame; Fov = Cam.FieldOfView; Type = Cam.CameraType; T0 = os.clock() }
	-- (2.22.0) one owner for the camera (Functions.CameraLease): held while talking and for the ease back out
	local Held = CameraLease.Take(`Talk`, function() return Shot ~= nil or os.clock() < TalkOutUntil end, function()
		local F = Shot and Shot.Model.Parent and Local.ShotFrame(Shot.Model)
		if F then Cam.CFrame = F end
	end)
	if not Held then Shot = nil return end
	local Fov = math.max(40, Shot.Fov - 12)
	if Calm then
		Cam.CFrame = Frame
		Cam.FieldOfView = Fov
	else
		TweenService:Create(Cam, TweenInfo.new(0.7, Enum.EasingStyle.Quint, Enum.EasingDirection.Out), { CFrame = Frame; FieldOfView = Fov }):Play()
	end
	Local.ShotBars(true)
	-- a soft depth of field on the NPC
	local Dof = Instance.new(`DepthOfFieldEffect`)
	Dof.Name = `NHTalkDof`
	Dof.FocusDistance = (Frame.Position - Them.Position).Magnitude
	Dof.InFocusRadius = 5
	Dof.NearIntensity = 0
	Dof.FarIntensity = 0
	Dof.Parent = Lighting
	TweenService:Create(Dof, TweenInfo.new(0.6), { FarIntensity = 0.35 }):Play()
	Shot.Dof = Dof
	-- hold the frame (they may shift a little), with a slow drift
	Shot.Conn = RunService.RenderStepped:Connect(function()
		if not Shot then return end
		if not (M.Parent and Player.Character) then Local.ShotOut() return end
		local F = Local.ShotFrame(M)
		if not F or not CameraLease.IsTop(`Talk`) then return end -- a newer lease (a cutscene) has the camera
		if os.clock() - Shot.T0 < 0.75 and not Calm then return end -- the ease-in tween is still running
		local Drift = if Calm then CFrame.identity else CFrame.new(math.sin((os.clock() - Shot.T0) * 0.25) * 0.25, 0, -math.min(os.clock() - Shot.T0, 20) * 0.02)
		Cam.CFrame = Cam.CFrame:Lerp(F * Drift, 0.08)
	end)
end

function Local.ShotOut()
	local S = Shot
	if not S then return end
	Shot = nil
	if S.Conn then S.Conn:Disconnect() end
	Local.ShotBars(false)
	if S.Dof then
		TweenService:Create(S.Dof, TweenInfo.new(0.3), { FarIntensity = 0 }):Play()
		task.delay(0.35, function() S.Dof:Destroy() end)
	end
	local Cam = workspace.CurrentCamera
	if not Cam then CameraLease.Release(`Talk`) return end
	TalkOutUntil = os.clock() + 1
	local function Done()
		if Shot then return end -- a new conversation took the camera again
		TalkOutUntil = 0
		Cam.FieldOfView = S.Fov
		CameraLease.Release(`Talk`) -- the last lease out gives back the normal camera (Custom, your FOV setting)
	end
	if Kit.ReducedMotion() or not CameraLease.IsTop(`Talk`) then Done() return end
	local Tw = TweenService:Create(Cam, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.InOut), { CFrame = S.Home; FieldOfView = S.Fov })
	Tw.Completed:Connect(Done)
	Tw:Play()
end

---| (2.38) helpers |---

local SEAL = {} :: { [string]: boolean } -- the school Seal, retired from new UI (never drawn here)
do
	local S = Kit.Theme.Images and Kit.Theme.Images.Seal
	if typeof(S) == `number` then
		SEAL[`rbxassetid://{S}`] = true
		SEAL[tostring(S)] = true
	elseif typeof(S) == `string` and S ~= `` then
		SEAL[S] = true
	end
end

local CARD_HOME = UDim2.new(0, 10, 0, 30) -- the card's bottom sits 30 px into the ribbon: only its top margin
local TAB_TALL_W = math.floor(TAB_W * TAB_TALL_H / TAB_H + 0.5) -- the taller tab keeps the art's aspect
local CliqueDefs: any = nil
local CrestRun = 0
local CardToken = 0

function Local.Reduced(): boolean
	if Player:GetAttribute(`NHReducedMotion`) == true then return true end
	local Ok, R = pcall(function() return Kit.ReducedMotion and Kit.ReducedMotion() end)
	return Ok and R == true
end

function Local.IsSeal(Image: string): boolean return SEAL[Image] == true end

function Local.Box(B: any): string
	if typeof(B) ~= `table` then return `0,0,1,1` end
	return string.format(`%.4f,%.4f,%.4f,%.4f`, B[1], B[2], B[3], B[4])
end

function Local.OneLine(S: any): string
	return (string.gsub(tostring(S or ``), `%s+`, ` `))
end

function Local.Escape(S: string): string
	return (S:gsub(`&`, `&amp;`):gsub(`<`, `&lt;`):gsub(`>`, `&gt;`))
end

-- design px (TextService measures at the design size; the gui's UIScale scales text and boxes alike)
function Local.Measure(Text: string, Size: number, Font: Enum.Font, Width: number): Vector2
	local Ok, V = pcall(TextService.GetTextSize, TextService, Text, Size, Font, Vector2.new(Width, 10000))
	return if Ok then V else Vector2.new(Width, Size * 1.25)
end

function Local.Fits(Text: string, Size: number, Font: Enum.Font, Width: number): boolean
	return Local.Measure(Text, Size, Font, 100000).X <= Width - 2 -- 2 px slack so UIScale rounding never flips TextFits
end

function Local.Scale(): number
	local S = Ui and Ui.Gui:FindFirstChildWhichIsA(`UIScale`)
	return if S and S.Scale > 0 then S.Scale else 1
end

function Local.CliqueDefs(): any
	if CliqueDefs == nil then
		local Ok, M = pcall(function() return require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`Cliques`, 5)) end)
		CliqueDefs = if Ok and typeof(M) == `table` and typeof(M.Defs) == `table` then M.Defs else false
	end
	return if CliqueDefs then CliqueDefs else nil
end

-- the kit's ornate frame, for art that isn't uploaded yet; any Seal it carries is taken out
function Local.Decorate(Obj: GuiObject, Opts: any)
	if Obj:FindFirstChild(`NHDecor`) then return end
	pcall(Kit.Decorate, Obj, Opts)
	for _, D in Obj:GetDescendants() do
		if (D:IsA(`ImageLabel`) or D:IsA(`ImageButton`)) and Local.IsSeal(D.Image) then
			D.Image = ``
			D.Visible = false
		end
	end
end

function Local.Undecorate(Obj: GuiObject)
	local D = Obj:FindFirstChild(`NHDecor`)
	if D then
		D:Destroy()
		Obj.BackgroundTransparency = 1
		Obj:SetAttribute(`QcA_B`, nil)
	end
end

-- fades: every piece remembers its shown transparency once (QcA_*), and fades between that and 1
function Local.Remember(Root: Instance)
	local List = Root:GetDescendants()
	table.insert(List, Root)
	for _, O in List do
		if O:IsA(`ImageLabel`) or O:IsA(`ImageButton`) then
			if O:GetAttribute(`QcA_I`) == nil then O:SetAttribute(`QcA_I`, O.ImageTransparency) end
		end
		if O:IsA(`TextLabel`) or O:IsA(`TextButton`) then
			if O:GetAttribute(`QcA_T`) == nil then O:SetAttribute(`QcA_T`, O.TextTransparency) end
			if O:GetAttribute(`QcA_K`) == nil then O:SetAttribute(`QcA_K`, O.TextStrokeTransparency) end
		end
		if O:IsA(`UIStroke`) then
			if O:GetAttribute(`QcA_S`) == nil then O:SetAttribute(`QcA_S`, O.Transparency) end
		end
		if O:IsA(`GuiObject`) and O.BackgroundTransparency < 1 then
			if O:GetAttribute(`QcA_B`) == nil then O:SetAttribute(`QcA_B`, O.BackgroundTransparency) end
		end
	end
end

function Local.Fade(Root: Instance, In: boolean, Secs: number, Skip: { Instance }?)
	local Stop = Root.Parent
	local function Skipped(O: Instance): boolean
		if not Skip then return false end
		local X: Instance? = O
		while X and X ~= Stop do
			if table.find(Skip, X) then return true end
			X = X.Parent
		end
		return false
	end
	local Info = TweenInfo.new(math.max(Secs, 0.01), Enum.EasingStyle.Sine)
	local function Go(O: Instance, Prop: string, Attr: string)
		local Base = O:GetAttribute(Attr)
		if typeof(Base) ~= `number` then return end
		local T = if In then Base else 1
		if Secs <= 0 then
			(O :: any)[Prop] = T
		else
			TweenService:Create(O, Info, { [Prop] = T }):Play()
		end
	end
	local List = Root:GetDescendants()
	table.insert(List, Root)
	for _, O in List do
		if Skipped(O) then continue end
		if O:IsA(`ImageLabel`) or O:IsA(`ImageButton`) then Go(O, `ImageTransparency`, `QcA_I`) end
		if O:IsA(`TextLabel`) or O:IsA(`TextButton`) then
			Go(O, `TextTransparency`, `QcA_T`)
			Go(O, `TextStrokeTransparency`, `QcA_K`)
		end
		if O:IsA(`UIStroke`) then Go(O, `Transparency`, `QcA_S`) end
		if O:IsA(`GuiObject`) then Go(O, `BackgroundTransparency`, `QcA_B`) end
	end
end

---| (2.38) building |---

function Local.Label(Parent: Instance, Name: string, X: number, Y: number, W: number, H: number, Size: number, Font: Enum.Font, Color: Color3): TextLabel
	local L = Instance.new(`TextLabel`)
	L.Name = Name
	L.BackgroundTransparency = 1
	L.AnchorPoint = Vector2.new(0, 0.5)
	L.Position = UDim2.fromOffset(X, Y)
	L.Size = UDim2.fromOffset(W, H)
	L.Font = Font
	L.TextSize = Size
	L.TextColor3 = Color
	L.TextScaled = false
	L.TextWrapped = false
	L.TextXAlignment = Enum.TextXAlignment.Left
	L.TextYAlignment = Enum.TextYAlignment.Center
	L.Text = ``
	L.ZIndex = 6
	L.Parent = Parent
	return L
end

function Local.Build()
	local Gui = Instance.new(`ScreenGui`)
	Gui.Name = `Dialogue`
	Gui.ResetOnSpawn = false
	Gui.DisplayOrder = 8
	Gui.Enabled = false
	Kit.AutoScale(Gui, { min = 0.8, max = 1.1; phoneScale = 0.66 }) -- shrink a little on short screens so it never covers the view

	-- (2.38) the ribbon: a 9-slice that grows upward (its bottom edge stays put)
	local Ribbon = Instance.new(`ImageLabel`)
	Ribbon.Name = `Ribbon`
	Ribbon.BackgroundTransparency = 1
	Ribbon.AnchorPoint = Vector2.new(0, 1)
	Ribbon.Position = UDim2.new(0, RIBBON_X, 1, -RIBBON_BOTTOM)
	Ribbon.Size = UDim2.fromOffset(RIBBON_W, RIBBON_MIN_H)
	Ribbon.ScaleType = Enum.ScaleType.Slice
	Ribbon.SliceCenter = (Art.Slices and Art.Slices.Ribbon) or Rect.new(120, 35, 904, 105)
	Ribbon.SliceScale = 1
	Ribbon.Image = ``
	Ribbon.ZIndex = 2
	Ribbon:SetAttribute(`QcBox`, Local.Box(Art.Boxes and Art.Boxes.Ribbon))
	Ribbon.Parent = Gui

	local Line = Instance.new(`TextButton`)
	Line.Name = `Line`
	Line.AutoButtonColor = false
	Line.BackgroundTransparency = 1
	Line.AnchorPoint = Vector2.new(0, 0.5)
	Line.Position = UDim2.fromScale(LINE_X0, 0.5)
	Line.Size = UDim2.new(LINE_W, 0, 0, 0)
	Line.AutomaticSize = Enum.AutomaticSize.Y
	Line.Font = FONT_BODY
	Line.TextSize = 24
	Line.TextWrapped = true
	Line.TextXAlignment = Enum.TextXAlignment.Left
	Line.TextYAlignment = Enum.TextYAlignment.Top
	Line.TextColor3 = INK
	Line.TextStrokeTransparency = 1
	Line.Text = ``
	Line.ZIndex = 3
	Line.Parent = Ribbon

	local Nib = Instance.new(`ImageLabel`)
	Nib.Name = `Nib`
	Nib.BackgroundTransparency = 1
	Nib.AnchorPoint = Vector2.new(0, 0.5)
	Nib.Size = UDim2.fromOffset(28, 28)
	Nib.Image = QC.Image(Art, `Nib`) or ``
	Nib.Visible = false
	Nib.ZIndex = 3
	Nib.Parent = Ribbon

	-- (2.38) the calling card rides on the ribbon's top margin
	local Card = Instance.new(`ImageLabel`)
	Card.Name = `Card`
	Card.BackgroundTransparency = 1
	Card.AnchorPoint = Vector2.new(0, 1)
	Card.Position = CARD_HOME
	Card.Size = UDim2.fromOffset(CARD_W, CARD_H)
	Card.ScaleType = Enum.ScaleType.Stretch
	Card.Image = ``
	Card.ZIndex = 4
	Card:SetAttribute(`QcBox`, Local.Box(Art.Boxes and Art.Boxes.CallingCard))
	Card.Parent = Ribbon

	local Crest = Instance.new(`ImageLabel`)
	Crest.Name = `Crest`
	Crest.BackgroundTransparency = 1
	Crest.AnchorPoint = Vector2.new(0.5, 0.5) -- the drop and the press scale about the socket's centre
	Crest.Position = UDim2.fromOffset(60, 60)
	Crest.Size = CREST_SIZE
	Crest.ScaleType = Enum.ScaleType.Stretch
	Crest.ImageRectSize = Vector2.new(FLIP.Frame, FLIP.Frame)
	Crest.ImageRectOffset = Vector2.zero
	Crest.Image = QC.Crest(Art, nil, true) or ``
	Crest.ZIndex = 6
	Crest.Parent = Card

	local Speaker = Local.Label(Card, `Speaker`, TEXT_X, 44, TEXT_W, 30, 24, FONT_BOLD, BONE)
	local Stroke = Instance.new(`UIStroke`)
	Stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual
	Stroke.Color = Color3.fromRGB(12, 9, 8)
	Stroke.Thickness = 1
	Stroke.Transparency = 0.35
	Stroke.Parent = Speaker
	local Sub = Local.Label(Card, `Sub`, TEXT_X, 89, TEXT_W, 26, 20, FONT_BODY, DIM)
	Sub.RichText = true -- the relation keeps its colour

	-- (2.38) the replies: a transparent holder; the tabs stack upward from its bottom-right
	local Choices = Instance.new(`Frame`)
	Choices.Name = `Choices`
	Choices.BackgroundTransparency = 1
	Choices.AnchorPoint = Vector2.new(1, 1)
	Choices.Position = UDim2.new(1, -CHOICES_RIGHT, 1, -CHOICES_BOTTOM)
	Choices.Size = UDim2.fromOffset(TAB_W, 0)
	Choices.Visible = false
	Choices.Parent = Gui

	local Hint = Instance.new(`TextLabel`)
	Hint.Name = `Hint`
	Hint.BackgroundTransparency = 1
	Hint.AnchorPoint = Vector2.new(1, 1)
	Hint.Position = UDim2.new(1, -CHOICES_RIGHT, 1, -40)
	Hint.Size = UDim2.fromOffset(0, 28)
	Hint.AutomaticSize = Enum.AutomaticSize.X
	Hint.Font = FONT_BODY
	Hint.TextSize = 20
	Hint.TextColor3 = DIM
	Hint.TextStrokeTransparency = 0.5
	Hint.TextXAlignment = Enum.TextXAlignment.Right
	Hint.TextYAlignment = Enum.TextYAlignment.Center
	Hint.Text = ``
	Hint.Parent = Gui

	local NoSel = Instance.new(`ImageLabel`) -- gamepad selection shows as the On tab, not the engine's default box
	NoSel.Name = `NoSelection`
	NoSel.BackgroundTransparency = 1
	NoSel.ImageTransparency = 1
	NoSel.Size = UDim2.fromScale(1, 1)

	Ui = {
		Gui = Gui; Ribbon = Ribbon; Line = Line; Nib = Nib; Card = Card; Crest = Crest; Speaker = Speaker; Sub = Sub;
		Choices = Choices; Hint = Hint; NoSel = NoSel; Tabs = {}; HintN = 4; RibbonH = RIBBON_MIN_H;
		Home = Ribbon.Position; NibHome = UDim2.fromOffset(0, 0); Text = ``; DH = 1080; ChoicesBottom = CHOICES_BOTTOM;
	}

	-- for the keyboard, a gamepad or a touch screen (Kit.InputKind), and again when that changes
	if Kit.InputKindChanged then Kit.InputKindChanged:Connect(Local.HintText) end
	Local.HintText()

	Gui.Parent = Player:WaitForChild(`PlayerGui`)
	Line.Activated:Connect(function() Local.Skip() end)
	Gui:GetPropertyChangedSignal(`AbsoluteSize`):Connect(function()
		if not (Ui and Current) then return end
		Local.Layout()
		if Ui.Choices.Visible then Local.ShowChoices(Current.Choices, Current.Tones) end
	end)
	Local.Remember(Gui)
	return Ui
end

function Local.HintText()
	if not Ui then return end
	local Kind = if Kit.InputKind then Kit.InputKind() else (if UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled then `Touch` else `Keyboard`)
	local N = math.clamp(Ui.HintN or 4, 1, 9)
	Ui.Hint.Text = if Kind == `Touch` then `Tap a reply`
		elseif Kind == `Gamepad` then Kit.PadText("D-pad to choose · {A} to reply · {B} to leave")
		else (if N > 1 then `1-{N} reply` else `1 to reply`) .. ` · click the line to skip · walk away to leave`
end

-- (2.38) the art for the local player's race; no id = the kit's fallback (theme text colours, no QcBg)
function Local.Skin()
	local Race = Player:GetAttribute(`Race`)
	local RibbonId = QC.Image(Art, `Ribbon`)
	if RibbonId then
		Local.Undecorate(Ui.Ribbon)
		Ui.Ribbon.Image = RibbonId
		Ui.Ribbon:SetAttribute(`QcBg`, RIBBON_PAPER)
		Ui.Line.TextColor3 = INK
		Ui.Line.TextStrokeTransparency = 1
	else
		Ui.Ribbon.Image = ``
		Local.Decorate(Ui.Ribbon, { ornamentScale = 0.7 })
		Ui.Ribbon:SetAttribute(`QcBg`, nil)
		Ui.Line.TextColor3 = KitColors.Text
		Ui.Line.TextStrokeTransparency = 0.75
	end
	Ui.Line:SetAttribute(`QcA_K`, Ui.Line.TextStrokeTransparency)
	local CardId = QC.Image(Art, `CallingCard`, Race)
	if CardId then
		Local.Undecorate(Ui.Card)
		Ui.Card.Image = CardId
		Ui.Card:SetAttribute(`QcBg`, CARD_IRON)
	else
		Ui.Card.Image = ``
		Local.Decorate(Ui.Card, { ornament = `thin` })
		Ui.Card:SetAttribute(`QcBg`, nil)
	end
	Ui.Nib.Image = QC.Image(Art, `Nib`) or ``
	Local.Remember(Ui.Gui)
end

-- (2.38) where everything sits for this screen and this line
function Local.Layout()
	if not Ui then return end
	local Cam = workspace.CurrentCamera
	local Vp = if Cam then Cam.ViewportSize else Vector2.new(1920, 1080)
	local KitVp = if Kit.Viewport then select(2, pcall(Kit.Viewport)) else nil -- (S5) Studio's NHPhonePreview counts for the phone layout
	local Phone = QC.Phone(if typeof(KitVp) == `Vector2` then KitVp else Vp)
	local Scale = Local.Scale()
	local Abs = Ui.Gui.AbsoluteSize
	local DW = (if Abs.X > 0 then Abs.X else Vp.X) / Scale
	local DH = (if Abs.Y > 0 then Abs.Y else Vp.Y) / Scale
	local RX = if Phone then PHONE_GUTTER else RIBBON_X
	local RB = if Phone then PHONE_GUTTER else RIBBON_BOTTOM
	local RW = RIBBON_W
	local Stack = Phone
	if Phone then
		RW = math.min(RIBBON_W, DW - 2 * PHONE_GUTTER)
	else
		-- the replies sit right of the ribbon; on a narrow screen the ribbon gives way, then the replies go above it
		local Room = DW - CHOICES_RIGHT - TAB_TALL_W - 24 - RX
		if Room >= 700 then
			RW = math.min(RIBBON_W, Room)
		else
			Stack = true
			RW = math.min(RIBBON_W, DW - RX - CHOICES_RIGHT)
		end
	end
	RW = math.max(RW, 300)
	local LW = math.floor(RW * LINE_W)
	local Text = Ui.Text or ``
	local LH = if Text == `` then 0 else Local.Measure(Text, 24, FONT_BODY, LW).Y
	local RH = math.max(RIBBON_MIN_H, math.ceil((LH + 8) / 0.6)) -- the line stays inside the 0.2 .. 0.8 text box
	Ui.Ribbon.Size = UDim2.fromOffset(RW, RH)
	Ui.Home = UDim2.new(0, RX, 1, -RB)
	if not Ui.Sliding then Ui.Ribbon.Position = Ui.Home end
	Ui.RibbonH = RH
	-- the nib: at the line box's right end, on its last line
	local One = Local.Measure(`Ag`, 24, FONT_BODY, LW).Y
	Ui.NibHome = UDim2.fromOffset(math.floor(RW * (LINE_X0 + LINE_W)) + 4, math.floor(RH / 2 + math.max(LH, One) / 2 - One / 2))
	if Ui.Nib.Visible then Local.NibShow() else Ui.Nib.Position = Ui.NibHome end
	-- the replies
	local Right, Bottom = CHOICES_RIGHT, CHOICES_BOTTOM
	if Stack then
		Right = if Phone then PHONE_GUTTER else CHOICES_RIGHT
		Bottom = RB + RH + 12
		local CardRight = RX + CARD_HOME.X.Offset + CARD_W
		if CardRight + 12 > DW - Right - TAB_TALL_W then Bottom = RB + RH - CARD_HOME.Y.Offset + CARD_H + 12 end -- above the card
	end
	Ui.Choices.Position = UDim2.new(1, -Right, 1, -Bottom)
	Ui.ChoicesBottom = Bottom
	Ui.DH = DH
	Ui.Hint.Visible = not Phone -- on a phone the ribbon spans the bottom; touch replies need no hint
end

function Local.SetBackpack(Open: boolean)
	if Open then
		if BackpackWas == nil then
			local Ok, Was = pcall(function() return StarterGui:GetCoreGuiEnabled(Enum.CoreGuiType.Backpack) end)
			BackpackWas = if Ok then Was else true
		end
		pcall(function() StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.Backpack, false) end)
	elseif BackpackWas ~= nil then
		local Was = BackpackWas
		BackpackWas = nil
		pcall(function() StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.Backpack, Was) end)
	end
end

---| (2.38) the crest and the nib |---

function Local.SetFrame(I: number)
	if not Ui then return end
	Ui.Crest.ImageRectSize = Vector2.new(FLIP.Frame, FLIP.Frame)
	Ui.Crest.ImageRectOffset = QC.FlipOffset(I)
end

function Local.CrestStop()
	CrestRun += 1
	if not Ui then return end
	if Ui.CrestTween then
		Ui.CrestTween:Cancel()
		Ui.CrestTween = nil
	end
	Ui.Crest.Size = CREST_SIZE
	Local.SetFrame(0)
end

-- spec §8: the drop into the socket, the press, one light-catch; then a catch every 5-8 s, never while a line types
function Local.CrestPlay(Calm: boolean)
	Local.CrestStop()
	local My = CrestRun
	local Crest = Ui.Crest
	local function Alive(): boolean return My == CrestRun end
	if Calm then
		-- Reduce Motion: frame 0 only, one 0.2 s fade
		Crest.ImageTransparency = 1
		local T = TweenService:Create(Crest, TweenInfo.new(0.2), { ImageTransparency = 0 })
		Ui.CrestTween = T
		T:Play()
		return
	end
	local function Catch()
		for I = 1, FLIP.Frames - 1 do
			if not Alive() or Local.Reduced() then break end
			Local.SetFrame(I)
			task.wait(1 / FLIP.Fps)
		end
		if Alive() then Local.SetFrame(0) end
	end
	local Size = CREST_SIZE
	local function Scaled(K: number): UDim2
		return UDim2.new(Size.X.Scale * K, Size.X.Offset * K, Size.Y.Scale * K, Size.Y.Offset * K)
	end
	Crest.Size = Scaled(1.18)
	Crest.ImageTransparency = 1
	task.spawn(function()
		task.wait(0.12)
		if not Alive() then return end
		local Drop = TweenService:Create(Crest, TweenInfo.new(0.2, Enum.EasingStyle.Cubic, Enum.EasingDirection.Out), { Size = Size; ImageTransparency = 0 })
		Ui.CrestTween = Drop
		Drop:Play()
		Drop.Completed:Wait()
		if not Alive() then return end
		local Press = TweenService:Create(Crest, TweenInfo.new(0.06, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, 0, true), { Size = Scaled(0.96) })
		Ui.CrestTween = Press
		Press:Play()
		Press.Completed:Wait()
		if not Alive() then return end
		Ui.CrestTween = nil
		Crest.Size = Size
		Crest.ImageTransparency = 0
		Catch() -- the entrance's one catch (the only one allowed while typing)
		while Alive() do
			task.wait(5 + math.random() * 3)
			while Alive() and Current ~= nil and Current.Typing do task.wait(0.25) end
			if Alive() and not Local.Reduced() then Catch() end
		end
	end)
end

function Local.NibStop()
	if not Ui then return end
	if Ui.NibTween then
		Ui.NibTween:Cancel()
		Ui.NibTween = nil
	end
	Ui.Nib.Visible = false
	Ui.Nib.Position = Ui.NibHome
end

function Local.NibShow()
	Local.NibStop()
	if Ui.Nib.Image == `` then return end -- no art yet: no nib
	Ui.Nib.ImageTransparency = 0
	Ui.Nib.Visible = true
	if Local.Reduced() then return end
	local T = TweenService:Create(Ui.Nib, TweenInfo.new(0.6, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true), { Position = Ui.NibHome - UDim2.fromOffset(0, 3) })
	Ui.NibTween = T
	T:Play()
end

-- (2.38) the card's entrance: a 0.18 s fade with a 12 px slide from the left; the name and sub from 0.2 s
function Local.CardIn(Calm: boolean)
	CardToken += 1
	local My = CardToken
	local Card = Ui.Card
	Local.Fade(Card, false, 0)
	Card.Position = CARD_HOME
	if Calm then
		Local.Fade(Card, true, 0.2, { Ui.Crest })
	else
		Card.Position = CARD_HOME - UDim2.fromOffset(12, 0)
		TweenService:Create(Card, TweenInfo.new(0.18, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Position = CARD_HOME }):Play()
		Local.Fade(Card, true, 0.18, { Ui.Crest, Ui.Speaker, Ui.Sub })
		task.delay(0.2, function()
			if My ~= CardToken or not Ui then return end
			Local.Fade(Ui.Speaker, true, 0.18)
			Local.Fade(Ui.Sub, true, 0.18)
		end)
	end
	Local.CrestPlay(Calm)
end

---| (2.38) the replies |---

function Local.Paint()
	if not Ui then return end
	for I, Rec in Ui.Tabs do
		if not Rec.Art then continue end
		local On = I == Ui.Hover or I == Ui.Sel or (Current ~= nil and Current.Pressed == I)
		Rec.Tab.Image = if On then Rec.OnId else Rec.TabId
		Rec.Tab:SetAttribute(`QcBg`, if On then TAB_VELVET else TAB_IRON)
		Rec.Text.TextColor3 = if On then BONE else DIM
		Rec.Text.Font = if On then FONT_BOLD else FONT_BODY
		Rec.Num.TextColor3 = if On then INK else GOLD
	end
end

-- the reply text's left edge and width inside a tab TW wide (the art's text box, less the tone mark)
function Local.TabText(TW: number, HasTone: boolean): (number, number)
	local B = (Art.Boxes and Art.Boxes.ReplyText) or { 132 / 1000, 24 / 128, 948 / 1000, 104 / 128 }
	local X0 = math.floor(TW * B[1]) + 10
	local X1 = math.floor(TW * B[3]) - (if HasTone then 48 else 6)
	return X0, X1 - X0
end

function Local.ShowChoices(Labels: { any }, Tones: { any }?)
	for _, Child in Ui.Choices:GetChildren() do
		if Child:IsA(`GuiObject`) then Child:Destroy() end
	end
	Ui.Tabs = {}
	Ui.Hover = nil
	Ui.Sel = nil
	local N = #Labels
	Ui.HintN = N
	Local.HintText()
	if N == 0 then
		Ui.Choices.Visible = false
		return
	end
	local Race = Player:GetAttribute(`Race`)
	local TabId = QC.Image(Art, `ReplyTab`, Race)
	local OnId = QC.Image(Art, `ReplyTabOn`, Race) or TabId
	local Socket = (Art.Boxes and Art.Boxes.ReplySocket) or { 26 / 1000, 20 / 128, 114 / 1000, 108 / 128 }
	local TextBox = Local.Box(Art.Boxes and Art.Boxes.ReplyText)

	-- measure first: each reply picks its tab (the taller one when it doesn't fit; never two lines)
	local Rows = {}
	for I = 1, N do
		local Text = Local.OneLine(Labels[I])
		local Tone = QC.Tone(Tones and Tones[I])
		local ToneId = if Tone then QC.Image(Art, `Tone` .. Tone) else nil
		local Row = { Text = Text; Tone = Tone; ToneId = ToneId }
		if TabId then
			local TW, TH = TAB_W, TAB_H
			local X0, W = Local.TabText(TW, ToneId ~= nil)
			local Step = if N > 5 then TAB_TIGHT_STEP else TAB_STEP
			if not Local.Fits(Text, 22, FONT_BOLD, W) then
				TW, TH, Step = TAB_TALL_W, TAB_TALL_H, TAB_TALL_STEP
				X0, W = Local.TabText(TW, ToneId ~= nil)
				if not Local.Fits(Text, 22, FONT_BOLD, W) then
					Row.Text = QC.Ellipsize(Text, function(T) return Local.Fits(T, 22, FONT_BOLD, W) end)
				end
			end
			Row.TW, Row.TH, Row.Step, Row.X0, Row.W = TW, TH, Step, X0, W
		else
			local W = TAB_W - 90
			if not Local.Fits(Text, 22, FONT_BOLD, W) then
				Row.Text = QC.Ellipsize(Text, function(T) return Local.Fits(T, 22, FONT_BOLD, W) end)
			end
			Row.TW, Row.TH, Row.Step = TAB_W, KIT_ROW_H, KIT_ROW_STEP
		end
		Rows[I] = Row
	end
	local function Total(): number
		local H = 0
		for I, R in Rows do H += if I == N then R.TH else R.Step end
		return H
	end
	local Room = (Ui.DH or 1080) - (Ui.ChoicesBottom or CHOICES_BOTTOM) - 8
	if Total() > Room then
		for _, R in Rows do R.Step = math.max(R.TH + 2, R.Step - 6) end -- a short screen: tighten the stack
	end

	local Y = 0
	for I, Row in Rows do
		local Rec
		if TabId then
			local Tab = Instance.new(`ImageButton`)
			Tab.Name = `Choice{I}`
			Tab.BackgroundTransparency = 1
			Tab.AutoButtonColor = false
			Tab.ScaleType = Enum.ScaleType.Stretch
			Tab.Image = TabId
			Tab.AnchorPoint = Vector2.new(1, 0)
			Tab.Position = UDim2.new(1, 0, 0, Y)
			Tab.Size = UDim2.fromOffset(Row.TW, Row.TH)
			Tab.Selectable = true
			Tab.SelectionImageObject = Ui.NoSel
			Tab.ZIndex = 3
			Tab:SetAttribute(`QcBox`, TextBox)
			Tab:SetAttribute(`QcBg`, TAB_IRON)

			local Sock = Instance.new(`Frame`) -- a transparent holder: the number sits on the socket art, not on the tab's iron
			Sock.Name = `Socket`
			Sock.BackgroundTransparency = 1
			Sock.Position = UDim2.fromScale(Socket[1], Socket[2])
			Sock.Size = UDim2.fromScale(Socket[3] - Socket[1], Socket[4] - Socket[2])
			Sock.ZIndex = 4
			Sock:SetAttribute(`QcBox`, `0,0,1,1`)
			Sock.Parent = Tab
			local Num = Instance.new(`TextLabel`)
			Num.Name = `Num`
			Num.BackgroundTransparency = 1
			Num.Size = UDim2.fromScale(1, 1)
			Num.Font = FONT_BOLD
			Num.TextSize = 22
			Num.TextColor3 = GOLD
			Num.TextXAlignment = Enum.TextXAlignment.Center
			Num.TextYAlignment = Enum.TextYAlignment.Center
			Num.Text = tostring(I)
			Num.ZIndex = 5
			Num.Parent = Sock

			local Label = Local.Label(Tab, `Text`, Row.X0, math.floor(Row.TH / 2), Row.W, 30, 22, FONT_BODY, DIM)
			Label.ZIndex = 5
			Label.Text = Row.Text

			if Row.ToneId then
				local B = (Art.Boxes and Art.Boxes.ReplyText) or { 0, 0, 948 / 1000, 1 }
				local Mark = Instance.new(`ImageLabel`)
				Mark.Name = `Tone`
				Mark.BackgroundTransparency = 1
				Mark.AnchorPoint = Vector2.new(0, 0.5)
				Mark.Position = UDim2.fromOffset(math.floor(Row.TW * B[3]) - 40, math.floor(Row.TH / 2))
				Mark.Size = UDim2.fromOffset(32, 32)
				Mark.Image = Row.ToneId
				Mark.ZIndex = 5
				Mark.Parent = Tab
			end

			Tab.MouseEnter:Connect(function() Ui.Hover = I Local.Paint() end)
			Tab.MouseLeave:Connect(function() if Ui.Hover == I then Ui.Hover = nil end Local.Paint() end)
			Tab.SelectionGained:Connect(function() Ui.Sel = I Local.Paint() end)
			Tab.SelectionLost:Connect(function() if Ui.Sel == I then Ui.Sel = nil end Local.Paint() end)
			Tab.Activated:Connect(function() Local.Choose(I) end)
			Tab.Parent = Ui.Choices
			Rec = { Art = true; Tab = Tab; Text = Label; Num = Num; TabId = TabId; OnId = OnId; Tone = Row.Tone }
		else
			-- the kit fallback: today's ChoiceRow, 44 px tall with 22 px text
			pcall(Kit.ChoiceRow, {
				Name = `Choice{I}`; index = I; text = Row.Text; LayoutOrder = I; height = KIT_ROW_H;
				onClick = function() Local.Choose(I) end;
				Parent = Ui.Choices;
			})
			local Row2 = Ui.Choices:FindFirstChild(`Choice{I}`)
			if Row2 and Row2:IsA(`GuiObject`) then
				Row2.AnchorPoint = Vector2.new(1, 0)
				Row2.Position = UDim2.new(1, 0, 0, Y)
				Row2.Size = UDim2.fromOffset(TAB_W, KIT_ROW_H)
				local List = Row2:GetDescendants()
				table.insert(List, Row2)
				for _, D in List do
					if (D:IsA(`TextLabel`) or D:IsA(`TextButton`)) and D.Text ~= `` then D.TextSize = math.max(D.TextSize, 22) D.TextScaled = false end
					if (D:IsA(`ImageLabel`) or D:IsA(`ImageButton`)) and Local.IsSeal(D.Image) then D.Image = `` D.Visible = false end
				end
			end
			Rec = { Art = false; Tab = Row2; Tone = Row.Tone }
		end
		Ui.Tabs[I] = Rec
		Y += if I == N then Row.TH else Row.Step
	end
	Ui.Choices.Size = UDim2.fromOffset(TAB_W, Y)
	Local.Paint()
	Local.Remember(Ui.Choices)
	Local.Fade(Ui.Choices, false, 0)
	Ui.Choices.Visible = true
	Local.Fade(Ui.Choices, true, if Local.Reduced() then 0.2 else 0.15)
	local Kind = if Kit.InputKind then Kit.InputKind() else nil
	local First = Ui.Tabs[1] and Ui.Tabs[1].Tab
	if Kind == `Gamepad` and First and First:IsA(`GuiObject`) then GuiService.SelectedObject = First end
end

function Local.Skip()
	if Current and Current.Typing then
		Current.Typing = false
	end
end

function Local.Choose(Index: number)
	if not Current or Current.Waiting then return end
	if Current.Typing then
		Local.Skip()
		return
	end
	if not Current.Choices[Index] then return end
	Current.Waiting = true
	Current.Pressed = Index -- (2.38) the last one pressed shows On
	Local.Paint()
	Packets.DialogueAction:Fire({ Id = Current.Id; Choice = Index })
end

function Local.Leave()
	if not Current then return end
	Packets.DialogueAction:Fire({ Id = Current.Id; Close = true })
	Local.Hide()
end

local ShowToken = 0
local Hiding = false
local SLIDE = UDim2.fromOffset(0, 40) -- (2.38) the ribbon rises from 40 px lower

function Local.Hide()
	Current = nil
	if Ui then
		-- (2.38) stop the crest loop and the nib; a reopen plays the card's entrance again
		Local.CrestStop()
		Local.NibStop()
		CardToken += 1
		Ui.CrestKey = nil
	end
	if Ui and Ui.Gui.Enabled then
		-- slide back down and fade, then switch off (unless a new line opened meanwhile)
		Hiding = true
		ShowToken += 1
		local My = ShowToken
		if not Local.Reduced() then
			Ui.Sliding = true
			TweenService:Create(Ui.Ribbon, TweenInfo.new(0.2, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Position = Ui.Home + SLIDE }):Play()
		end
		Local.Fade(Ui.Ribbon, false, 0.2)
		Local.Fade(Ui.Choices, false, 0.2)
		Local.Fade(Ui.Hint, false, 0.2)
		local Sel = GuiService.SelectedObject
		if Sel and Sel:IsDescendantOf(Ui.Gui) then GuiService.SelectedObject = nil end
		task.delay(0.22, function()
			if My == ShowToken and Ui and not Current then
				Hiding = false
				Ui.Sliding = false
				Ui.Gui.Enabled = false
				Ui.Ribbon.Position = Ui.Home
				Ui.Choices.Visible = false
			end
		end)
	end
	Local.SetBackpack(false)
	Player:SetAttribute(`InDialogue`, nil)
	Local.ShotOut()
end

function Local.ShowNode(Data)
	Ui = Ui or Local.Build()
	Local.Skin()
	local Calm = Local.Reduced()

	-- (2.38) the card: name (24 px bold caps, down to 20 if it must), crest, clique · role · relationship
	local SpeakerText = tostring(Data.Speaker or ``)
	local Name = string.upper(SpeakerText)
	local NameSize = 24
	for _, S in { 24, 22, 20 } do
		NameSize = S
		if Local.Fits(Name, S, FONT_BOLD, TEXT_W) then break end
	end
	if not Local.Fits(Name, NameSize, FONT_BOLD, TEXT_W) then
		Name = QC.Ellipsize(Name, function(T) return Local.Fits(T, NameSize, FONT_BOLD, TEXT_W) end)
	end
	Ui.Speaker.TextSize = NameSize
	Ui.Speaker.Text = Name

	local Clique = QC.CliqueOf(Data)
	local Defs = if Clique then Local.CliqueDefs() else nil
	local Def = Defs and Defs[Clique]
	local CliqueName = if Def and typeof(Def.Name) == `string` then Def.Name else nil
	local Role = if Data.Role ~= nil and tostring(Data.Role) ~= `` then tostring(Data.Role) else nil
	local Relation = if Data.Relationship ~= nil and tostring(Data.Relationship) ~= `` then tostring(Data.Relationship) else nil
	local function SubFits(T: string): boolean return Local.Fits(T, 20, FONT_BODY, TEXT_W) end
	local Plain = QC.CardSub(CliqueName, Role, Relation, SubFits)
	if Plain ~= `` and not SubFits(Plain) then Plain = QC.Ellipsize(Plain, SubFits) end
	local RelColor = Relation and RELATION_COLORS[Relation]
	if RelColor and #Plain > #Relation and string.sub(Plain, -#Relation) == Relation then
		Ui.Sub.Text = Local.Escape(string.sub(Plain, 1, #Plain - #Relation)) .. `<font color="#{RelColor:ToHex()}">{Local.Escape(Relation)}</font>`
	else
		Ui.Sub.Text = Local.Escape(Plain)
	end
	Ui.Crest.Image = QC.Crest(Art, Clique, true) or `` -- no clique = Unaffiliated (never the Seal)

	local Choices = if typeof(Data.Choices) == `table` then Data.Choices else {}
	local Tones = if typeof(Data.Tones) == `table` then Data.Tones else {}
	local Text = tostring(Data.Text or ``)
	local Node = { Id = Data.Id; Choices = Choices; Tones = Tones; Typing = true }
	Current = Node

	Ui.Choices.Visible = false
	Ui.Text = Text
	Ui.Line.Text = Text
	Ui.Line.MaxVisibleGraphemes = if Calm then -1 else 0 -- (2.38) Reduce Motion: no typing
	Local.NibStop()
	Local.Layout()

	local Opening = not Ui.Gui.Enabled or Hiding -- a line arriving mid-hide re-opens the box
	Hiding = false
	ShowToken += 1
	local My = ShowToken
	Ui.Gui.Enabled = true
	if Opening then
		-- the ribbon rises into place and fades in (Reduce Motion: a 0.2 s fade only)
		Local.Fade(Ui.Ribbon, false, 0, { Ui.Card })
		if Calm then
			Ui.Sliding = false
			Ui.Ribbon.Position = Ui.Home
		else
			Ui.Sliding = true
			Ui.Ribbon.Position = Ui.Home + SLIDE
			TweenService:Create(Ui.Ribbon, TweenInfo.new(0.28, Enum.EasingStyle.Quint, Enum.EasingDirection.Out), { Position = Ui.Home }):Play()
			task.delay(0.3, function()
				if My == ShowToken and Ui and Current then
					Ui.Sliding = false
					Ui.Ribbon.Position = Ui.Home
				end
			end)
		end
		Local.Fade(Ui.Ribbon, true, if Calm then 0.2 else 0.22, { Ui.Card })
		Local.Fade(Ui.Hint, true, 0.2)
	end
	-- a new node keeps the card and its crest when the speaker is unchanged
	local Key = SpeakerText .. `|` .. tostring(Clique)
	if Opening or Ui.CrestKey ~= Key then
		Ui.CrestKey = Key
		Local.CardIn(Calm)
	end
	Local.SetBackpack(true)
	Player:SetAttribute(`InDialogue`, true)
	if Opening or not Shot then Local.ShotIn(Data.Model) end

	task.spawn(function()
		local Total = utf8.len(Text) or #Text
		local Started = os.clock()
		while not Calm and Current == Node and Node.Typing do
			local Shown = math.floor((os.clock() - Started) * CHARS_PER_SECOND)
			if Shown >= Total then break end
			Ui.Line.MaxVisibleGraphemes = Shown
			task.wait()
		end
		if Current ~= Node then return end
		Node.Typing = false
		Ui.Line.MaxVisibleGraphemes = -1
		Local.NibShow()
		Local.ShowChoices(Choices, Tones)
	end)
end

-- (2.38) Studio probe: what the dialogue shows now (tools/quietcorners/checks/qc_dialogue*.lua)
function Local.Info()
	if not Ui then return { Replies = {}; Seal = false } end
	local Seal = false
	for _, D in Ui.Gui:GetDescendants() do
		if (D:IsA(`ImageLabel`) or D:IsA(`ImageButton`)) and Local.IsSeal(D.Image) then Seal = true end
	end
	local Replies = {}
	if Current then
		for I, L in Current.Choices do
			local Rec = Ui.Tabs[I]
			local Shown = Rec and Rec.Text and Rec.Text.Text
			table.insert(Replies, { Text = if Shown and Shown ~= `` then Shown else tostring(L); Tone = QC.Tone(Current.Tones[I]) })
		end
	end
	return {
		Crest = Ui.Crest.Image; CrestRect = Ui.Crest.ImageRectSize.X; CrestOffset = tostring(Ui.Crest.ImageRectOffset);
		Name = Ui.Speaker.Text; Sub = Ui.Sub.ContentText; Line = Ui.Line.Text; Replies = Replies;
		RibbonH = Ui.RibbonH or RIBBON_MIN_H; Seal = Seal;
	}
end

function Shared.IsOpen(): boolean
	return Current ~= nil
end

function Shared.OnStart()
	Packets.DialogueEvent.OnClientEvent:Connect(function(Data)
		if typeof(Data) ~= `table` then return end
		if Data.Type == `Node` then
			Local.ShowNode(Data)
		elseif Data.Type == `Close` then
			if Current and (Data.Id == nil or Data.Id == Current.Id) then Local.Hide() end
		end
	end)

	UserInputService.InputBegan:Connect(function(Input, Processed)
		if not Current or Processed then return end
		local Index = NUMBER_KEYS[Input.KeyCode]
		if Index then
			Local.Choose(Index)
		elseif Input.KeyCode == Enum.KeyCode.Escape or Input.KeyCode == Enum.KeyCode.ButtonB then
			Local.Leave()
		end
	end)

	Player.CharacterAdded:Connect(function() if Current then Local.Hide() end end)

	-- (2.38) Studio probes, registered with HudState (loaded lazily, so the load order doesn't matter)
	task.spawn(function()
		local M = script.Parent:WaitForChild(`HudState`, 10)
		if not M then return end
		local Ok, HudState = pcall(require, M)
		if not (Ok and typeof(HudState) == `table` and HudState.Probe) then return end
		HudState.Probe(`Dialogue`, function(Data)
			if typeof(Data) == `table` then Local.ShowNode(Data) end
			return true
		end)
		HudState.Probe(`DialogueClose`, function()
			Local.Hide()
			return true
		end)
		HudState.Probe(`DialogueInfo`, function() return Local.Info() end)
	end)
end

return Shared
