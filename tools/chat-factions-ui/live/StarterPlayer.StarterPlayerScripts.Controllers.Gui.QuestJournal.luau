--[[
	Quest journal (client). Toggle with J, the Phone's Journal app, the gamepad quick menu, or the top bar (the
	left-edge button is hidden since 2026-11-25, chat-factions-ui).
	(2.38, Quiet Corners QC4) The journal is the open book (spec docs/superpowers/specs/2026-11-21-quiet-corners-ui-design.md §6,
	plan docs/superpowers/plans/2026-11-22-quiet-corners-ui.md Task R10):
		- the book: Config.QuietCornersArt BookTL/TR/BL/BR quadrants (1660 x 943 design), BookCorner<Race> on its corners,
		  over the world behind the kit Shadow scrim (0.42) and a Lighting BlurEffect QcBlur. With no quadrant ids it draws
		  today's Components.Panel instead (the kit fallback), and the text goes back to the theme colours.
		- leather tabs (BookTab / BookTabOn) off the right board: Journal, Evidence, Record, Settings, Notices.
		    Journal   left page: "THE JOURNAL" and one lead per active quest on Bell Tower LeadCard art, then Done / Failed
		              (and cutscenes to watch again); right page: the selected quest in ink, with Track / Abandon
		    Evidence  closes the book and opens Controllers.Gui.EvidenceWall (the wall replaced the old Case Files tab)
		    Record    closes the book and opens the Permanent Record (Controllers.Gui.StatsPanel)
		    Settings  closes the book and opens Controllers.Gui.SettingsMenu
		    Notices   the session's notifications at full length (Controllers.Gui.Notifications.History)
		- phones (shorter side under 600): one page at a time; a lead (or a notice) slides to its detail page and
		  "‹ Journal" comes back. NHReducedMotion cuts instead of sliding.
		- keys: J toggles, Esc closes; gamepad LB / RB step the tabs and B closes; touch taps a tab or the X.
	Sets the Player attribute NHMenuOpen while the book is open (HudState's Menu state).
	API: Toggle(Open?), SelectTab(Index) (1 Journal, 2 Evidence, 3 Record, 4 Settings, 5 Notices), OpenPage(Page, Arg?),
	     IsOpen(). Probes (Studio, through HudState.Probe): Book(Open), BookTab(Name), BookInfo().
	Every action goes to the server as Packets.QuestAction; the server decides the outcome.
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local UserInputService = game:GetService(`UserInputService`)
local ContextActionService = game:GetService(`ContextActionService`) -- (2.38) LB / RB / B while the book is open
local GuiService = game:GetService(`GuiService`) -- (2.38)
local Lighting = game:GetService(`Lighting`) -- (2.38) QcBlur
local TextService = game:GetService(`TextService`) -- (2.38) shortening lead lines to their card
local TweenService = game:GetService(`TweenService`)
local Typing = require(game:GetService(`ReplicatedStorage`):WaitForChild(`Packages`):WaitForChild(`Bind`):WaitForChild(`Typing`)) -- (2.1.0) one "is the player typing?" for every key

---| Modules |---

local Theme = require(ReplicatedStorage.UI.Theme)
local Components = require(ReplicatedStorage.UI.Components)
local Packets = require(ReplicatedStorage.Remotes.Packets)
local QuestConfig = require(ReplicatedStorage.Config.Quests)
local Npcs = require(ReplicatedStorage.Config.Npcs)
local StateController = require(script.Parent.Parent.StateController)
local QC = require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`QuietCorners`)) -- (2.38)
local Art = require(ReplicatedStorage.Config:WaitForChild(`QuietCornersArt`)) -- (2.38)
-- (2.38) the Bell Tower's LeadCard and fang pips (R1); optional, so a missing module only drops to the kit look
local BtOk, BtArt = pcall(function() return require(ReplicatedStorage.Config:WaitForChild(`BellTowerArt`, 5)) end)
local BellArt = if BtOk and typeof(BtArt) == `table` then BtArt else {}
local BfOk, BtFns = pcall(function() return require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`BellTower`, 5)) end)
local BellTower = if BfOk and typeof(BtFns) == `table` then BtFns else nil

local Player = Players.LocalPlayer
local C = Theme.Colors
local TOGGLE_KEY = Enum.KeyCode.J

-- (2.38) design sizes (mockup menu(): the book is 1660 x 943, f = 1660 / 2048)
local BOOK_W, BOOK_H = 1660, 943
local HALF_W = BOOK_W / 2
local TAB_W, TAB_H, TAB_X, TAB_Y, TAB_STEP = 150, 60, 1636, 120, 92
local TAB_OUT = TAB_X + TAB_W - BOOK_W -- how far the tabs hang off the right board (126)
local CARD_W, CARD_H = 520, 150
local TABS = { `Journal`, `Evidence`, `Record`, `Settings`, `Notices` }
local IN_BOOK = { Journal = true; Notices = true } :: { [string]: boolean }

-- (2.38) ink on paper (measured contrast on the page (181,162,130): spec §9 wants 4.5:1 at 22 px and under)
local INK = Color3.fromRGB(40, 22, 16)
local INK_DIM = Color3.fromRGB(48, 30, 22)
local INK_RED = Color3.fromRGB(96, 10, 16)
local PAGE = Color3.fromRGB(181, 162, 130)
local LEATHER = Color3.fromRGB(99, 76, 68)
local BONE = Color3.fromRGB(236, 226, 206)
local TAB_DIM = Color3.fromRGB(220, 208, 188)

local BODY = Theme.Fonts.Body
local BOLD = Theme.Fonts.BodyBold or Theme.Fonts.Title
local TITLE = Theme.Fonts.Title

local Local = {}
local Shared = {}

local Ui = nil
local Tab = 1             -- (2.38) the in-book page: 1 Journal or 5 Notices
local Side = `Left`       -- (2.38) phones: which page shows
local Selected = nil :: string?   -- (2.38) the quest on the right page
local Notice = 1          -- (2.38) the notice on the right page (index into History, newest first)
local Blur = nil :: BlurEffect?
local Leads = 0

---| Helpers |---

function Local.Reduced(): boolean return Player:GetAttribute(`NHReducedMotion`) == true end
function Local.Race(): string return QC.Race(Player:GetAttribute(`Race`)) end
function Local.Esc(S: any): string
	return (tostring(S or ``):gsub(`&`, `&amp;`):gsub(`<`, `&lt;`):gsub(`>`, `&gt;`))
end

-- (2.38) the ink mapping: on paper the theme roles become ink; on the kit fallback they stay the theme's
function Local.Col(Role: string): Color3
	local Paper = Ui and Ui.OnPaper
	if Role == `Dim` then return if Paper then INK_DIM else C.TextDim end
	if Role == `Red` then return if Paper then INK_RED else C.Crimson end
	if Role == `Head` then return if Paper then INK else C.Gold end
	return if Paper then INK else C.Text
end

function Local.Label(Parent: Instance, Order: number, Text: string, Size: number, Color: Color3, Props: { [string]: any }?): TextLabel
	local P = Props or {}
	local L = Instance.new(`TextLabel`)
	L.Name = P.Name or `Line`
	L.BackgroundTransparency = 1
	L.BorderSizePixel = 0
	L.RichText = P.RichText ~= false
	L.TextWrapped = true
	L.Font = P.Font or BODY
	L.TextSize = math.max(Size, QC.MIN_TEXT)
	L.TextColor3 = Color
	L.TextXAlignment = P.Align or Enum.TextXAlignment.Left
	L.TextYAlignment = P.YAlign or Enum.TextYAlignment.Top
	if P.Size then
		L.Size = P.Size
	else
		L.Size = UDim2.new(1, -8, 0, 0)
		L.AutomaticSize = Enum.AutomaticSize.Y
	end
	if P.Position then L.Position = P.Position end
	L.LayoutOrder = Order
	L.Text = Text
	L.Parent = Parent
	return L
end

-- (2.38) a section rule (the kit Divider; Local.Block's slate cards don't sit on paper)
function Local.Rule(Parent: Instance, Order: number)
	if Components.Divider then
		local Ok = pcall(Components.Divider, { Name = `Rule`; Size = UDim2.new(1, -8, 0, 16); LayoutOrder = Order; Parent = Parent })
		if Ok then return end
	end
	local Img = Theme.Images and Theme.Images.Divider
	if Img then
		local D = Instance.new(`ImageLabel`)
		D.Name = `Rule`
		D.BackgroundTransparency = 1
		D.Image = Img
		D.ScaleType = Enum.ScaleType.Fit
		D.Size = UDim2.new(1, -8, 0, 16)
		D.LayoutOrder = Order
		D.Parent = Parent
	end
end

function Local.Row(Parent: Instance, Order: number, Height: number?): Frame
	local R = Instance.new(`Frame`)
	R.Name = `Row`
	R.BackgroundTransparency = 1
	R.Size = UDim2.new(1, -8, 0, Height or 44)
	R.LayoutOrder = Order
	R.Parent = Parent
	local Layout = Instance.new(`UIListLayout`)
	Layout.FillDirection = Enum.FillDirection.Horizontal
	Layout.VerticalAlignment = Enum.VerticalAlignment.Center
	Layout.SortOrder = Enum.SortOrder.LayoutOrder
	Layout.Padding = UDim.new(0, 8)
	Layout.Parent = R
	return R
end

function Local.Button(Parent: Instance, Order: number, Text: string, Style: string?, Width: number?, OnClick: () -> ())
	return Components.Button({
		text = Text; style = Style or `default`; textSize = 20; onClick = function() OnClick() end;
		Size = UDim2.fromOffset(Width or 160, 44); LayoutOrder = Order; Parent = Parent;
	})
end

function Local.Send(Message)
	Packets.QuestAction:Fire(Message)
end

-- (2.38) a kit-button row on the page: its own QcBox (no QcBg), so the fit check doesn't read button text against the paper
function Local.ButtonRow(Parent: Instance, Order: number): Frame
	local R = Local.Row(Parent, Order)
	R.Name = `Buttons`
	R:SetAttribute(`QcBox`, `0,0,1,1`)
	return R
end

function Local.Scroller(Name: string, Parent: Instance, Size: UDim2): ScrollingFrame
	local S = Instance.new(`ScrollingFrame`)
	S.Name = Name
	S.BackgroundTransparency = 1
	S.BorderSizePixel = 0
	S.Size = Size
	S.CanvasSize = UDim2.new()
	S.AutomaticCanvasSize = Enum.AutomaticSize.Y
	S.ScrollingDirection = Enum.ScrollingDirection.Y
	S.ScrollBarThickness = 6
	S.ScrollBarImageColor3 = INK_DIM
	S.Parent = Parent
	local Layout = Instance.new(`UIListLayout`)
	Layout.SortOrder = Enum.SortOrder.LayoutOrder
	Layout.Padding = UDim.new(0, 10)
	Layout.Parent = S
	local Pad = Instance.new(`UIPadding`)
	Pad.PaddingLeft = UDim.new(0, 6)
	Pad.PaddingRight = UDim.new(0, 10)
	Pad.PaddingTop = UDim.new(0, 4)
	Pad.PaddingBottom = UDim.new(0, 8)
	Pad.Parent = S
	return S
end

function Local.Clear(Parent: Instance)
	for _, Child in Parent:GetChildren() do
		if Child:IsA(`GuiObject`) then Child:Destroy() end
	end
end

-- (2.38) shorten at a word until it fits a W x H box at Size (TextService; Theme.Fonts are Enum.Font)
function Local.Fit(Text: string, Size: number, Font: any, W: number, H: number): string
	if typeof(Font) ~= `EnumItem` then return Text end
	return QC.Ellipsize(Text, function(S)
		local Ok, V = pcall(TextService.GetTextSize, TextService, S, Size, Font, Vector2.new(W - 2, 4000))
		return Ok and V.X <= W - 2 and V.Y <= H - 2
	end)
end

function Local.Lazy(Name: string): any?
	local M = script.Parent:FindFirstChild(Name)
	if not M then return nil end
	local Ok, Mod = pcall(require, M)
	return if Ok and typeof(Mod) == `table` then Mod else nil
end

function Local.Phone(): boolean
	if Components.Phone then
		local Ok, V = pcall(Components.Phone)
		if Ok and V then return true end
	end
	local Cam = workspace.CurrentCamera
	return Cam ~= nil and QC.Phone(Cam.ViewportSize)
end

function Local.InputKind(): string
	if Components.InputKind then
		local Ok, K = pcall(Components.InputKind)
		if Ok and typeof(K) == `string` then return K end
	end
	return if UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled then `Touch` else `Keyboard`
end

---| Build |---

function Local.Build()
	local Gui = Instance.new(`ScreenGui`)
	Gui.Name = `QuestJournal`
	Gui.ResetOnSpawn = false
	Gui.DisplayOrder = 7
	Gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	Gui.Parent = Player:WaitForChild(`PlayerGui`)
	Components.AutoScale(Gui)

	local Toggle = Components.Button({
		text = if UserInputService.KeyboardEnabled then `Journal [J]` else `Journal`;
		style = `ghost`; onClick = function() Shared.Toggle() end;
		Name = `Toggle`; AnchorPoint = Vector2.new(0, 0.5); Position = UDim2.new(0, 8, 0.5, 78); -- where it sat under the old left-edge Factions button
		Size = UDim2.fromOffset(150, 44); Parent = Gui;
	})
	Toggle.Visible = false -- (chat-factions-ui, owner 2026-11-25) no left-edge button: J, the Phone or the quick menu
	-- phones: the old beside-the-column spot (kept so the hidden button's layout is unchanged if it is shown again)
	local function PhonePlace()
		if Components.Phone and Components.Phone() then
			Toggle.Position = UDim2.new(0, 148, 0.5, -55)
		else
			Toggle.Position = UDim2.new(0, 8, 0.5, 78)
		end
	end
	PhonePlace()
	if Components.PreviewChanged then Components.PreviewChanged:Connect(PhonePlace) end
	if workspace.CurrentCamera then workspace.CurrentCamera:GetPropertyChangedSignal(`ViewportSize`):Connect(PhonePlace) end

	-- (2.38) the scrim: the kit Shadow at 0.42 (an image, never a plain frame), oversized so the UIScale never uncovers an edge
	local Scrim = nil
	local ShadowImg = Theme.Images and Theme.Images.Shadow
	if ShadowImg then
		Scrim = Instance.new(`ImageLabel`)
		Scrim.Name = `Scrim`
		Scrim.BackgroundTransparency = 1
		Scrim.Image = ShadowImg
		Scrim.ImageColor3 = Color3.new(0, 0, 0)
		Scrim.ImageTransparency = 0.42
		Scrim.ScaleType = Enum.ScaleType.Stretch
		Scrim.AnchorPoint = Vector2.new(0.5, 0.5)
		Scrim.Position = UDim2.fromScale(0.5, 0.5)
		Scrim.Size = UDim2.fromScale(4, 4)
		Scrim.Active = true -- clicks don't fall through to the world
		Scrim.Visible = false
		Scrim.ZIndex = 0
		Scrim.Parent = Gui
	end

	-- (2.38) Panel keeps its name: a transparent frame holding the book (desktop 1660 x 943; phones show one 830-wide page)
	local Panel = Instance.new(`Frame`)
	Panel.Name = `Panel`
	Panel.BackgroundTransparency = 1
	Panel.BorderSizePixel = 0
	Panel.AnchorPoint = Vector2.new(0.5, 0.5)
	Panel.Position = UDim2.new(0.5, -TAB_OUT / 2, 0.5, 0)
	Panel.Size = UDim2.fromOffset(BOOK_W, BOOK_H)
	Panel.Visible = false
	Panel.ZIndex = 1
	Panel.Parent = Gui
	local Fit = Instance.new(`UIScale`)
	Fit.Name = `BookFit`
	Fit.Parent = Panel

	local Clip = Instance.new(`Frame`)
	Clip.Name = `Clip`
	Clip.BackgroundTransparency = 1
	Clip.BorderSizePixel = 0
	Clip.Size = UDim2.fromScale(1, 1)
	Clip.ClipsDescendants = true
	Clip.Parent = Panel

	local Spread = Instance.new(`Frame`)
	Spread.Name = `Spread`
	Spread.BackgroundTransparency = 1
	Spread.BorderSizePixel = 0
	Spread.Size = UDim2.fromOffset(BOOK_W, BOOK_H)
	Spread.ZIndex = 2
	Spread.Parent = Clip

	-- the quadrants (each 830 x 471.5), drawn edge to edge; all four or none (plan ruling 4)
	local Quads = {}
	for I, Q in { `BookTL`, `BookTR`, `BookBL`, `BookBR` } do
		local Id = QC.Image(Art, Q)
		if Id then
			local Img = Instance.new(`ImageLabel`)
			Img.Name = Q
			Img.BackgroundTransparency = 1
			Img.Image = Id
			Img.ScaleType = Enum.ScaleType.Stretch
			Img.Position = UDim2.fromOffset(if I % 2 == 0 then HALF_W else 0, if I > 2 then BOOK_H / 2 else 0)
			Img.Size = UDim2.fromOffset(HALF_W, BOOK_H / 2)
			Img.Parent = Spread
			table.insert(Quads, Img)
		end
	end
	local OnPaper = #Quads == 4
	local Board = nil
	if not OnPaper then
		for _, Q in Quads do Q:Destroy() end
		table.clear(Quads)
		-- the kit fallback: today's ornate panel behind the pages (in Clip, so phones get a whole 830-wide board)
		Board = Components.Panel({ Name = `Board`; Size = UDim2.fromScale(1, 1); Parent = Clip })
		if typeof(Board) == `Instance` and Board:IsA(`GuiObject`) then Board.ZIndex = 1 end
	end

	-- BookCorner<Race> at the four corners of the board (none until uploaded; decoration only)
	local CornerId = QC.Image(Art, `BookCorner`, Local.Race())
	if CornerId and OnPaper then
		for I, At in { Vector2.new(0, 0), Vector2.new(1, 0), Vector2.new(1, 1), Vector2.new(0, 1) } do
			local K = Instance.new(`ImageLabel`)
			K.Name = `Corner{I}`
			K.BackgroundTransparency = 1
			K.Image = CornerId
			K.AnchorPoint = At
			K.Position = UDim2.fromOffset(At.X * BOOK_W, At.Y * BOOK_H)
			K.Size = UDim2.fromOffset(120, 120)
			K.Rotation = (I - 1) * 90
			K.ZIndex = 3
			K.Parent = Spread
		end
	end

	-- the two pages, in their measured text boxes (Boxes.BookLeft / BookRight of the 2048 x 1164 art)
	local function Page(Name: string, B: { number }): Frame
		local F = Instance.new(`Frame`)
		F.Name = Name
		F.BackgroundTransparency = 1
		F.BorderSizePixel = 0
		F.Position = UDim2.fromOffset(B[1] * BOOK_W, B[2] * BOOK_H)
		F.Size = UDim2.fromOffset((B[3] - B[1]) * BOOK_W, (B[4] - B[2]) * BOOK_H)
		F.ZIndex = 4
		F:SetAttribute(`QcBox`, `0,0,1,1`)
		if OnPaper then F:SetAttribute(`QcBg`, PAGE) end
		F.Parent = Spread
		return F
	end
	local Left = Page(`Left`, Art.Boxes.BookLeft)
	local Right = Page(`Right`, Art.Boxes.BookRight)
	local Body = Local.Scroller(`Body`, Left, UDim2.fromScale(1, 1))
	local Detail = Local.Scroller(`Detail`, Right, UDim2.new(1, 0, 1, -52))
	local Foot = Instance.new(`Frame`)
	Foot.Name = `Foot`
	Foot.BackgroundTransparency = 1
	Foot.AnchorPoint = Vector2.new(0, 1)
	Foot.Position = UDim2.new(0, 6, 1, -2)
	Foot.Size = UDim2.new(1, -12, 0, 44)
	Foot.Parent = Right
	local FootLayout = Instance.new(`UIListLayout`)
	FootLayout.FillDirection = Enum.FillDirection.Horizontal
	FootLayout.VerticalAlignment = Enum.VerticalAlignment.Center
	FootLayout.SortOrder = Enum.SortOrder.LayoutOrder
	FootLayout.Padding = UDim.new(0, 8)
	FootLayout.Parent = Foot

	-- the tab column (rebuilt on every render so the On art follows the page)
	local Tabs = Instance.new(`Frame`)
	Tabs.Name = `Tabs`
	Tabs.BackgroundTransparency = 1
	Tabs.Size = UDim2.fromScale(1, 1)
	Tabs.ZIndex = 5
	Tabs.Parent = Panel

	local Close = Components.Button({
		text = `X`; style = `ghost`; textSize = 20; onClick = function() Shared.Toggle(false) end;
		Name = `Close`; AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -12, 0, 14);
		Size = UDim2.fromOffset(48, 44); Parent = Panel;
	})
	return {
		Gui = Gui; Toggle = Toggle; Scrim = Scrim; Panel = Panel; Fit = Fit; Clip = Clip; Spread = Spread; Board = Board;
		Quads = Quads; OnPaper = OnPaper; Left = Left; Right = Right; Body = Body; Detail = Detail; Foot = Foot;
		Tabs = Tabs; Close = Close; Back = nil; Phone = false;
	}
end

-- (2.38) desktop: the spread, centred with the tabs; phones: one page, and Side picks which. Fits the screen with BookFit.
function Local.Layout()
	if not Ui then return end
	local Phone = Local.Phone()
	Ui.Phone = Phone
	local W = if Phone then HALF_W else BOOK_W
	Ui.Panel.Size = UDim2.fromOffset(W, BOOK_H)
	Ui.Spread.Position = UDim2.fromOffset(if Phone and Side == `Right` then -HALF_W else 0, 0)
	Ui.Left.Visible = not Phone or Side == `Left`
	Ui.Right.Visible = not Phone or Side == `Right`
	-- the back tab exists only while a phone shows the right page (a hidden kit button would still be read by the checks)
	local WantBack = Phone and Side == `Right`
	if WantBack and not (Ui.Back and Ui.Back.Parent) then
		Ui.Back = Components.Button({
			text = if Tab == 5 then `‹ Notices` else `‹ Journal`; style = `ghost`; textSize = 20;
			onClick = function() Local.Slide(`Left`) end;
			Name = `Back`; Position = UDim2.fromOffset(14, 14); Size = UDim2.fromOffset(170, 44); Parent = Ui.Panel;
		})
	elseif not WantBack and Ui.Back then
		Ui.Back:Destroy()
		Ui.Back = nil
	end
	local Cam = workspace.CurrentCamera
	local Auto = Ui.Gui:FindFirstChild(`NHAutoScale`)
	local AS = if Auto and Auto:IsA(`UIScale`) and Auto.Scale > 0 then Auto.Scale else 1
	local Vp = if Cam then Cam.ViewportSize / AS else Vector2.new(1920, 1080)
	local F = math.min(1, Vp.X / (W + TAB_OUT + 24), Vp.Y / (BOOK_H + 24))
	Ui.Fit.Scale = math.max(0.3, F)
	Ui.Panel.Position = UDim2.new(0.5, -TAB_OUT * Ui.Fit.Scale / 2, 0.5, 0)
	Local.RenderTabs()
end

-- (2.38) phones: slide to a page (Reduce Motion: a cut)
function Local.Slide(To: string)
	Side = To
	if not Ui then return end
	if Ui.Phone then
		local Goal = UDim2.fromOffset(if To == `Right` then -HALF_W else 0, 0)
		Ui.Left.Visible = true
		Ui.Right.Visible = true
		if Local.Reduced() or not Ui.Panel.Visible then
			Ui.Spread.Position = Goal
			Local.Layout()
		else
			local T = TweenService:Create(Ui.Spread, TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Position = Goal })
			T.Completed:Connect(function() if Side == To then Local.Layout() end end)
			T:Play()
		end
	end
end

---| Tabs (2.38) |---

function Local.RenderTabs()
	if not Ui then return end
	Local.Clear(Ui.Tabs)
	local X = (if Ui.Phone then HALF_W else BOOK_W) - (BOOK_W - TAB_X)
	local Off, On = QC.Image(Art, `BookTab`), QC.Image(Art, `BookTabOn`)
	for I, Name in TABS do
		local Here = I == Tab
		local Pos = UDim2.fromOffset(X, TAB_Y + (I - 1) * TAB_STEP)
		if Off and On then
			local B = Instance.new(`ImageButton`)
			B.Name = `Tab_{Name}`
			B.BackgroundTransparency = 1
			B.Image = if Here then On else Off
			B.ScaleType = Enum.ScaleType.Stretch
			B.Position = Pos
			B.Size = UDim2.fromOffset(TAB_W, TAB_H)
			B.AutoButtonColor = false
			B.ZIndex = 5
			B:SetAttribute(`QcBox`, `0.17,0.1,0.94,0.9`)
			B:SetAttribute(`QcBg`, LEATHER)
			B.Parent = Ui.Tabs
			Local.Label(B, 1, Name, 20, if Here then BONE else TAB_DIM, {
				Name = `Label`; RichText = false; Font = if Here then BOLD else BODY;
				Position = UDim2.fromOffset(26, 6); Size = UDim2.fromOffset(114, 48); YAlign = Enum.TextYAlignment.Center;
			}).ZIndex = 6
			B.Activated:Connect(function() Local.ClickTab(I) end)
		else
			-- the kit fallback: today's buttons (gold for the open page)
			local B = Components.Button({
				text = Name; style = if Here then `gold` else `default`; textSize = 20;
				onClick = function() Local.ClickTab(I) end;
				Name = `Tab_{Name}`; Position = Pos; Size = UDim2.fromOffset(TAB_W, TAB_H); Parent = Ui.Tabs;
			})
			if typeof(B) == `Instance` and B:IsA(`GuiObject`) then B.ZIndex = 5 end
		end
	end
end

function Local.ClickTab(I: number)
	local Name = TABS[I]
	if not Name then return end
	pcall(Components.PlaySound, `Tick`, 0.6)
	if Name == `Evidence` then
		Shared.Toggle(false)
		local Wall = Local.Lazy(`EvidenceWall`)
		if Wall and Wall.Open then task.spawn(pcall, Wall.Open) end
	elseif Name == `Record` then
		Shared.Toggle(false)
		-- (2.38) the Permanent Record (M); "StatsPanel" is the name in the 2.32 dump, S1 confirms it in Studio
		local Record = Local.Lazy(`StatsPanel`)
		if Record and Record.Toggle then task.spawn(pcall, Record.Toggle, true) end -- it asks the server first (yields)
	elseif Name == `Settings` then
		Shared.Toggle(false)
		local Settings = Local.Lazy(`SettingsMenu`)
		if Settings and Settings.Toggle then task.spawn(pcall, Settings.Toggle, true) end
	else
		if Tab ~= I then
			Tab = I
			Notice = 1
			Side = `Left`
			if Ui then Ui.Spread.Position = UDim2.fromOffset(0, 0) end -- a page change cuts (no page turn today)
		end
		Local.Layout()
		Local.Render()
	end
end

---| Journal pages (2.38) |---

function Local.SortedActive(Q): { string }
	local Ids = {}
	for Id in Q.Active or {} do if QuestConfig.Quests[Id] then table.insert(Ids, Id) end end -- (audit) a removed quest id in a save crashed the sort
	table.sort(Ids, function(A, B)
		if A == Q.Tracked then return true end
		if B == Q.Tracked then return false end
		local DA, DB = QuestConfig.Quests[A], QuestConfig.Quests[B]
		if (DA.Category == `Main`) ~= (DB.Category == `Main`) then return DA.Category == `Main` end
		return DA.Name < DB.Name
	end)
	return Ids
end

function Local.Current(Def, State)
	local Obj = Def.Objectives and Def.Objectives[State.Stage]
	if not Obj then return nil, 0, 1 end
	local Need = Obj.Count or 1
	return Obj, (State.Counts or {})[Obj.Id] or 0, Need
end

-- one lead on the Bell Tower LeadCard (title band 150..880 x 30..92 of 1000 x 300; the tracked one full, the rest at 0.88)
function Local.LeadCard(Parent: Instance, Order: number, Id: string, State, Q)
	local Def = QuestConfig.Quests[Id]
	local Tracked = Q.Tracked == Id
	local Full = Tracked or Selected == Id
	local Fade = if Full then 0 else 0.12
	local Img = QC.Image(BellArt, `LeadCard`)
	local Card = Instance.new(`ImageButton`)
	Card.Name = `Lead_{Id}`
	Card.BackgroundTransparency = 1
	Card.AutoButtonColor = false
	Card.Size = UDim2.fromOffset(CARD_W, CARD_H)
	Card.LayoutOrder = Order
	Card.Selectable = true
	Card.Parent = Parent
	local Paper = Img ~= nil and BellArt.Slices and BellArt.Slices.LeadCard
	if Paper then
		Card.Image = Img :: string
		Card.ScaleType = Enum.ScaleType.Slice
		Card.SliceCenter = BellArt.Slices.LeadCard.Center
		Card.SliceScale = BellArt.Slices.LeadCard.Scale
		Card.ImageTransparency = Fade
		Card:SetAttribute(`QcBox`, `0.15,0.08,0.88,0.94`)
		Card:SetAttribute(`QcBg`, PAGE) -- the LeadCard parchment is as light as the page
	else
		Card.Image = ``
		pcall(Components.Decorate, Card, { ornament = `slot`; shadow = false; bgColor = Color3.fromRGB(78, 70, 88); frameColor = if Full then C.Gold else C.RowFrame })
	end
	local Ink = if Paper then INK else (if Def.Category == `Main` then C.Gold else C.Text)
	local Dim = if Paper then INK_DIM else C.TextDim
	local TX, TW = math.floor(0.15 * CARD_W), math.floor(0.73 * CARD_W)
	local Title = Local.Label(Card, 1, Local.Fit(Def.Name, 22, BOLD, TW, 32), 22, Ink, {
		Name = `Title`; RichText = false; Font = BOLD; Position = UDim2.fromOffset(TX, 13); Size = UDim2.fromOffset(TW, 32);
		YAlign = Enum.TextYAlignment.Center;
	})
	local Obj, Have, Need = Local.Current(Def, State)
	local Line = if Obj then Obj.Text .. (if Need > 1 then ` ({Have} of {Need})` else ``) else (Def.Summary or ``)
	if Tracked then Line = `Tracked · {Line}` end
	if State.Deadline then
		local Left = math.max(0, State.Deadline - workspace:GetServerTimeNow())
		Line = string.format(`%s · %d:%02d left`, Line, Left // 60, Left % 60)
	end
	local Sub = Local.Label(Card, 2, Local.Fit(Line, 20, BODY, TW, 76), 20, Dim, {
		Name = `Line`; RichText = false; Position = UDim2.fromOffset(TX, 52); Size = UDim2.fromOffset(TW, 76);
	})
	Title.TextTransparency = Fade
	Sub.TextTransparency = Fade
	for _, L in { Title, Sub } do L.ZIndex = Card.ZIndex + 2 end
	Card.Activated:Connect(function()
		Selected = Id
		pcall(Components.PlaySound, `Tick`, 0.5)
		Local.Render()
		if Ui and Ui.Phone then Local.Slide(`Right`) end
	end)
	return Card
end

function Local.RenderJournalLeft(Q)
	local Body = Ui.Body
	local Order = 0
	local function Next() Order += 1 return Order end
	Local.Label(Body, Next(), `THE JOURNAL`, 34, Local.Col(`Head`), { Name = `Heading`; RichText = false; Font = TITLE })
	Local.Label(Body, Next(), `<i>Leads you are following</i>`, 20, Local.Col(`Dim`), { Name = `Sub` })

	local Ids = Local.SortedActive(Q)
	Leads = #Ids
	if #Ids == 0 then
		Local.Label(Body, Next(), `No active quests. Talk to people around campus; some of them need a hand.`, 22, Local.Col(`Text`))
	end
	for _, Id in Ids do Local.LeadCard(Body, Next(), Id, Q.Active[Id], Q) end

	local Done = {}
	for Id in Q.Done or {} do
		local Def = QuestConfig.Quests[Id]
		if Def then table.insert(Done, Def) end
	end
	table.sort(Done, function(A, B) return A.Name < B.Name end)
	local Failed = {}
	for Id, Reason in Q.Failed or {} do
		local Def = QuestConfig.Quests[Id]
		if Def and not (Q.Active or {})[Id] then
			local Giver = Def.Giver and Npcs[Def.Giver]
			table.insert(Failed, `<b>{Def.Name}</b>: {tostring(Reason)}{if Giver then ` Talk to {Giver.Name} to try again.` else ``}`)
		end
	end
	if #Done > 0 or #Failed > 0 then Local.Rule(Body, Next()) end
	if #Done > 0 then
		Local.Label(Body, Next(), `Done ({#Done})`, 20, Local.Col(`Text`), { Name = `Done`; RichText = false; Font = BOLD })
		local Names = {}
		for _, Def in Done do table.insert(Names, Def.Name .. (if Def.Repeatable then ` (daily)` else ``)) end
		Local.Label(Body, Next(), table.concat(Names, ` · `), 20, Local.Col(`Dim`), { Name = `DoneList`; RichText = false })
		for _, Def in Done do
			if Def.Ending then Local.Label(Body, Next(), `<b>{Def.Name}</b>: <i>{Def.Ending}</i>`, 20, Local.Col(`Dim`), { Name = `Ending` }) end
		end
	end
	if #Failed > 0 then
		Local.Label(Body, Next(), `Failed ({#Failed})`, 20, Local.Col(`Red`), { Name = `Failed`; RichText = false; Font = BOLD })
		for _, Line in Failed do Local.Label(Body, Next(), Line, 20, Local.Col(`Dim`), { Name = `FailedLine` }) end
	end

	-- (2.24.0) cutscenes you've seen, to watch again (Controllers.Cine.Replay: the server plays it, always skippable)
	local CineOk, CineConfig = pcall(function() return require(ReplicatedStorage.Config.Cine) end)
	local Seen = {}
	local Grades = if typeof(Q.CineGrades) == `table` then Q.CineGrades else {} -- (2.25.0) best grade per interactive cut
	for Id, Mark in (if typeof(Q.Cine) == `table` then Q.Cine else {}) do
		local Cut = CineOk and CineConfig.Cuts[Id]
		if Mark == `Seen` and Cut and Cut.Replay and not Cut.Hidden then table.insert(Seen, { Id = Id; Name = Cut.Name; ShowGrade = Cut.ShowGrade ~= false }) end
	end
	if #Seen > 0 then
		table.sort(Seen, function(A, B) return A.Name < B.Name end)
		Local.Rule(Body, Next())
		Local.Label(Body, Next(), `Cutscenes`, 22, Local.Col(`Text`), { Name = `Cutscenes`; RichText = false; Font = BOLD })
		for _, Cut in Seen do
			local R = Local.ButtonRow(Body, Next())
			local Grade = if Grades[Cut.Id] and Cut.ShowGrade then `   {tostring(Grades[Cut.Id].Best)}` else ``
			local W = 721 - 6 - 10 - 8 - 168 -- the left page less the padding and the button
			Local.Label(R, 1, Local.Fit(Cut.Name .. Grade, 20, BODY, W, 44), 20, Local.Col(`Dim`), {
				Name = `Cut`; RichText = false; Size = UDim2.fromOffset(W, 44); YAlign = Enum.TextYAlignment.Center;
			})
			Local.Button(R, 2, `Watch again`, `default`, 160, function()
				local Ok, Director = pcall(function() return require(script.Parent.Parent:WaitForChild(`Cine`)) end)
				if not Ok or Director.IsPlaying() then return end
				Shared.Toggle(false)
				Director.Replay(Cut.Id)
			end)
		end
	end
end

function Local.RenderJournalRight(Q)
	local Box = Ui.Detail
	local Order = 0
	local function Next() Order += 1 return Order end
	local Id = Selected
	local State = Id and (Q.Active or {})[Id]
	local Def = Id and QuestConfig.Quests[Id]
	if not (State and Def) then
		Local.Label(Box, Next(), `Pick a lead to read it here.`, 22, Local.Col(`Dim`), { Name = `Empty`; RichText = false })
		return
	end
	local Tag = if Def.Category == `Main` then `Main · Chapter {Def.Chapter or 1}`
		elseif Def.Dare then `Dare · gone at 6 AM` -- (1.33) a clique leader's daily dare
		elseif Def.Category == `Clique` then `Clique`
		else `Side quest`
	local Giver = Def.Giver and Npcs[Def.Giver]
	Local.Label(Box, Next(), Def.Name, 32, Local.Col(`Head`), { Name = `Title`; RichText = false; Font = TITLE })
	Local.Label(Box, Next(), `<i>{Tag}{if Giver then ` · from {Giver.Name}` else ``}</i>`, 20, Local.Col(`Dim`), { Name = `From` })
	if Def.Summary and Def.Summary ~= `` then Local.Label(Box, Next(), Def.Summary, 22, Local.Col(`Text`), { Name = `Summary` }) end

	for Index, Obj in Def.Objectives or {} do
		local Count = (State.Counts or {})[Obj.Id] or 0
		local Need = Obj.Count or 1
		local Done = Count >= Need
		if Index == State.Stage and not Done then
			Local.Label(Box, Next(), `Next: {Obj.Text}`, 22, Local.Col(`Red`), { Name = `Next`; RichText = false; Font = BOLD })
			-- fang pips (2 to 6) and the count
			local Pips = if BellTower and BellTower.Pips then BellTower.Pips(Count, Need) else nil
			local Fang, Empty = QC.Image(BellArt, `PipFang`), QC.Image(BellArt, `PipEmpty`)
			if Need > 1 then
				local R = Local.Row(Box, Next(), 50)
				R.Name = `Pips`
				if Pips and Fang and Empty then
					for P, Filled in Pips do
						local Img = Instance.new(`ImageLabel`)
						Img.Name = `Pip{P}`
						Img.BackgroundTransparency = 1
						Img.Image = if Filled then Fang else Empty
						Img.Size = UDim2.fromOffset(46, 46)
						Img.LayoutOrder = P
						Img.Parent = R
					end
				end
				local N = Local.Label(R, 99, `{Count} of {Need}`, 20, Local.Col(`Dim`), {
					Name = `Count`; RichText = false; Size = UDim2.fromOffset(0, 46); YAlign = Enum.TextYAlignment.Center;
				})
				N.AutomaticSize = Enum.AutomaticSize.X
				N.TextWrapped = false
			end
		elseif Done then
			Local.Label(Box, Next(), `✓  {Obj.Text}`, 20, Local.Col(`Dim`), { Name = `Did`; RichText = false })
		else
			Local.Label(Box, Next(), `·  {Obj.Text}{if Obj.Optional then ` (optional)` else ``}`, 20, Local.Col(`Dim`), { Name = `Later`; RichText = false })
		end
	end
	if State.Deadline then
		local Left = math.max(0, State.Deadline - workspace:GetServerTimeNow())
		Local.Label(Box, Next(), string.format(`Time left: %d:%02d`, Left // 60, Left % 60), 22, Local.Col(`Red`), { Name = `Timer`; RichText = false; Font = BOLD })
	end

	local Tracked = Q.Tracked == Id
	if Tracked then Local.Label(Box, Next(), `<i>You are following this lead.</i>`, 20, Local.Col(`Dim`), { Name = `Following` }) end
	local Buttons = Local.ButtonRow(Box, Next())
	if not Tracked then
		Local.Button(Buttons, 1, `Track`, `gold`, 160, function() Local.Send({ Action = `Track`; Quest = Id }) end)
	end
	-- (audit) owner: no Abandon for rite or showdown quests (the server refuses them too)
	if Def.Category ~= `Main` and Def.Category ~= `Rite` and not Def.Showdown then
		Local.Button(Buttons, 2, `Abandon`, `crimson`, 160, function() Local.Send({ Action = `Abandon`; Quest = Id }) end)
	end
	if #Buttons:GetChildren() <= 1 then Buttons:Destroy() end
end

---| Notices pages (2.38) |---

function Local.History(): { any }
	local N = Local.Lazy(`Notifications`)
	if N and N.History then
		local Ok, H = pcall(N.History)
		if Ok and typeof(H) == `table` then return H end
	end
	return {}
end

function Local.When(T: any): string
	if typeof(T) ~= `number` then return `` end
	local S = os.date(`%I:%M %p`, T)
	return (tostring(S):gsub(`^0`, ``))
end

function Local.RenderNotices()
	local Body, Box = Ui.Body, Ui.Detail
	local Order = 0
	local function Next() Order += 1 return Order end
	Local.Label(Body, Next(), `NOTICES`, 34, Local.Col(`Head`), { Name = `Heading`; RichText = false; Font = TITLE })
	Local.Label(Body, Next(), `<i>What you heard this session</i>`, 20, Local.Col(`Dim`), { Name = `Sub` })
	local H = Local.History()
	if #H == 0 then
		Local.Label(Body, Next(), `No notices yet.`, 22, Local.Col(`Text`), { Name = `Empty`; RichText = false })
		return
	end
	Notice = math.clamp(Notice, 1, #H)
	for I, E in H do
		local Row = Instance.new(`TextButton`)
		Row.Name = `Notice{I}`
		Row.BackgroundTransparency = 1
		Row.BorderSizePixel = 0
		Row.Text = ``
		Row.AutoButtonColor = false
		Row.Selectable = true
		Row.Size = UDim2.new(1, -8, 0, 0)
		Row.AutomaticSize = Enum.AutomaticSize.Y
		Row.LayoutOrder = Next()
		Row.Parent = Body
		local L = Instance.new(`UIListLayout`)
		L.SortOrder = Enum.SortOrder.LayoutOrder
		L.Padding = UDim.new(0, 2)
		L.Parent = Row
		local Here = I == Notice
		Local.Label(Row, 1, tostring(E.Title or ``), 22, if Here then Local.Col(`Red`) else Local.Col(`Text`), { Name = `Title`; RichText = false; Font = BOLD; Size = nil })
		local When = Local.When(E.Time)
		if When ~= `` then Local.Label(Row, 2, When, 20, Local.Col(`Dim`), { Name = `Time`; RichText = false }) end
		Row.Activated:Connect(function()
			Notice = I
			pcall(Components.PlaySound, `Tick`, 0.5)
			Local.Render()
			if Ui and Ui.Phone then Local.Slide(`Right`) end
		end)
	end
	local E = H[Notice]
	Local.Label(Box, 1, tostring(E.Title or ``), 32, Local.Col(`Head`), { Name = `Title`; RichText = false; Font = TITLE })
	local When = Local.When(E.Time)
	if When ~= `` then Local.Label(Box, 2, `<i>{Local.Esc(When)}</i>`, 20, Local.Col(`Dim`), { Name = `Time` }) end
	if tostring(E.Text or ``) ~= `` then Local.Label(Box, 3, tostring(E.Text), 22, Local.Col(`Text`), { Name = `Text`; RichText = false }) end
end

---| Footer (2.38) |---

function Local.RenderFoot()
	if not Ui then return end
	Local.Clear(Ui.Foot)
	local Kind = Local.InputKind()
	local Items = if Kind == `Gamepad` then { { `LB`, `Tab` }, { `RB`, `Tab` }, { `A`, `Track` }, { `B`, `Close` } }
		elseif Kind == `Touch` then { { nil, `Tap a tab` }, { `X`, `Close` } }
		else { { nil, `Click a tab` }, { `Esc`, `Close` } }
	local Cap = QC.Image(Art, `PromptCap`, Local.Race())
	local N = 0
	for _, It in Items do
		local Key, Text = It[1], It[2]
		if Key then
			N += 1
			if Cap then
				local W = 40
				local Ok, V = pcall(TextService.GetTextSize, TextService, Key, 20, BOLD, Vector2.new(400, 40))
				if Ok then W = math.max(40, math.ceil(V.X / 0.8) + 4) end
				local K = Instance.new(`ImageLabel`)
				K.Name = `Cap{N}`
				K.BackgroundTransparency = 1
				K.Image = Cap
				K.ScaleType = Enum.ScaleType.Slice
				K.SliceCenter = Rect.new(40, 40, 88, 88)
				K.SliceScale = 0.3
				K.Size = UDim2.fromOffset(W, 40)
				K.LayoutOrder = N * 2 - 1
				K:SetAttribute(`QcBox`, `0.1,0.1,0.9,0.9`) -- the cap's own box (the key is gold on brass, not ink on paper)
				K.Parent = Ui.Foot
				Local.Label(K, 1, Key, 20, C.Gold, {
					Name = `Key`; RichText = false; Font = BOLD; Align = Enum.TextXAlignment.Center; YAlign = Enum.TextYAlignment.Center;
					Position = UDim2.fromScale(0.1, 0.1); Size = UDim2.fromScale(0.8, 0.8);
				}).TextWrapped = false
			else
				local K = Local.Label(Ui.Foot, N * 2 - 1, Key, 20, Local.Col(`Text`), {
					Name = `Key{N}`; RichText = false; Font = BOLD; Size = UDim2.fromOffset(0, 40); YAlign = Enum.TextYAlignment.Center;
				})
				K.AutomaticSize = Enum.AutomaticSize.X
				K.TextWrapped = false
			end
		end
		N += 1
		local L = Local.Label(Ui.Foot, N * 2, Text, 20, Local.Col(`Dim`), {
			Name = `Hint{N}`; RichText = false; Size = UDim2.fromOffset(0, 40); YAlign = Enum.TextYAlignment.Center;
		})
		L.AutomaticSize = Enum.AutomaticSize.X
		L.TextWrapped = false
		local Gap = Instance.new(`UIPadding`)
		Gap.PaddingRight = UDim.new(0, 18)
		Gap.Parent = L
	end
end

---| Render |---

function Local.Render()
	if not Ui or not Ui.Panel.Visible then return end
	local KeepL, KeepR = Ui.Body.CanvasPosition, Ui.Detail.CanvasPosition
	Local.Clear(Ui.Body)
	Local.Clear(Ui.Detail)
	Local.RenderTabs()
	Local.RenderFoot()
	if Tab == 5 then
		Leads = 0
		Local.RenderNotices()
	else
		local Q = (StateController.GetProfile(false) or {}).Quests
		if typeof(Q) ~= `table` then
			Local.Label(Ui.Body, 1, `Loading...`, 22, Local.Col(`Dim`), { RichText = false })
			return
		end
		local Active = Q.Active or {}
		if not (Selected and Active[Selected] and QuestConfig.Quests[Selected]) then
			Selected = nil
			if Q.Tracked and Active[Q.Tracked] and QuestConfig.Quests[Q.Tracked] then Selected = Q.Tracked
			else Selected = Local.SortedActive(Q)[1] end
		end
		Local.RenderJournalLeft(Q)
		Local.RenderJournalRight(Q)
	end
	task.defer(function()
		if not Ui then return end
		Ui.Body.CanvasPosition = KeepL
		Ui.Detail.CanvasPosition = KeepR
	end)
end

---| Open / close (2.38) |---

local PadBound = false
function Local.Pad(On: boolean)
	if On == PadBound then return end
	PadBound = On
	if not On then
		ContextActionService:UnbindAction(`NHBookTabs`)
		ContextActionService:UnbindAction(`NHBookClose`)
		return
	end
	ContextActionService:BindActionAtPriority(`NHBookTabs`, function(_, State, Io)
		if State ~= Enum.UserInputState.Begin then return Enum.ContextActionResult.Sink end
		local Step = if Io.KeyCode == Enum.KeyCode.ButtonR1 then 1 else -1
		Local.ClickTab((Tab - 1 + Step) % #TABS + 1)
		return Enum.ContextActionResult.Sink
	end, false, 3000, Enum.KeyCode.ButtonL1, Enum.KeyCode.ButtonR1)
	ContextActionService:BindActionAtPriority(`NHBookClose`, function(_, State)
		if State ~= Enum.UserInputState.Begin then return Enum.ContextActionResult.Sink end
		if Ui and Ui.Phone and Side == `Right` then Local.Slide(`Left`) else Shared.Toggle(false) end
		return Enum.ContextActionResult.Sink
	end, false, 3000, Enum.KeyCode.ButtonB)
end

function Local.SelectFirst()
	if not Ui or Local.InputKind() ~= `Gamepad` then return end
	task.defer(function()
		if not Ui then return end
		local Best, BestY = nil, math.huge
		for _, D in Ui.Body:GetDescendants() do
			if D:IsA(`GuiButton`) and D.Visible and D.Selectable and D.AbsolutePosition.Y < BestY then Best, BestY = D, D.AbsolutePosition.Y end
		end
		if Best then GuiService.SelectedObject = Best end
	end)
end

---| API |---

function Shared.IsOpen(): boolean return Ui ~= nil and Ui.Panel.Visible end

function Shared.Toggle(Open: boolean?)
	if not Ui then return end
	if Open == nil then Open = not Ui.Panel.Visible end
	local Was = Ui.Panel.Visible
	if Open == Was then
		if Open then Local.Render() end
		return
	end
	Ui.Panel.Visible = Open
	if Ui.Scrim then Ui.Scrim.Visible = Open end
	Ui.Toggle.Visible = false -- (chat-factions-ui) the left-edge button stays hidden, open or closed
	Local.Pad(Open)
	if Open then
		Player:SetAttribute(`NHMenuOpen`, true)
		if not (Blur and Blur.Parent) then
			local B = Instance.new(`BlurEffect`)
			B.Name = `QcBlur`
			B.Size = 12
			B.Parent = Lighting
			Blur = B
		end
		Local.Layout()
		Local.Render()
		Local.SelectFirst()
	else
		if Blur then Blur:Destroy() Blur = nil end
		if GuiService.SelectedObject and GuiService.SelectedObject:IsDescendantOf(Ui.Gui) then GuiService.SelectedObject = nil end
		Player:SetAttribute(`NHMenuOpen`, nil)
		Side = `Left`
	end
end

-- (2.38) 1 Journal, 2 Evidence (opens the wall), 3 Record, 4 Settings, 5 Notices
function Shared.SelectTab(Index: number)
	if not TABS[Index] then return end
	if IN_BOOK[TABS[Index]] then
		Tab = Index
		Notice = 1
		Side = `Left`
		if Ui then
			Ui.Spread.Position = UDim2.fromOffset(0, 0)
			if Ui.Panel.Visible then Local.Layout() end
		end
		Local.Render()
	else
		Local.ClickTab(Index)
	end
end

-- (2.38) open the book on a page: "Journal" (Arg = a quest id to select), "Evidence" (Arg = a case id; the wall), "Notices"
function Shared.OpenPage(Page: string, Arg: any?)
	if Page == `Evidence` then
		Shared.Toggle(false)
		local Wall = Local.Lazy(`EvidenceWall`)
		if Wall and Wall.Open then task.spawn(pcall, Wall.Open, if typeof(Arg) == `string` then Arg else nil) end
		return
	end
	Tab = if Page == `Notices` then 5 else 1
	Notice = 1
	Side = `Left`
	if Tab == 1 and typeof(Arg) == `string` and QuestConfig.Quests[Arg] then
		Selected = Arg
		Side = `Right` -- phones go straight to the quest's page
	end
	if Ui and Ui.Panel.Visible then
		Local.Layout() -- places the spread for Side (phones)
		Local.Render()
	else
		Shared.Toggle(true)
	end
end

---| Probes (2.38, Studio: tools/quietcorners/checks/qc_book.lua) |---

function Local.Probes()
	local Ok, HudState = pcall(function() return require(script.Parent:WaitForChild(`HudState`, 10)) end)
	if not (Ok and typeof(HudState) == `table` and HudState.Probe) then return end
	HudState.Probe(`Book`, function(Open: boolean?)
		Shared.Toggle(Open == true)
		return Shared.IsOpen()
	end)
	HudState.Probe(`BookTab`, function(Name: string)
		local I = table.find(TABS, Name)
		if not I then return false end
		Local.ClickTab(I)
		return true
	end)
	HudState.Probe(`BookInfo`, function()
		local Title = nil
		if Tab == 1 and Selected and QuestConfig.Quests[Selected] then Title = QuestConfig.Quests[Selected].Name end
		return {
			Open = Shared.IsOpen();
			Tab = TABS[Tab];
			Pages = if Ui and Ui.Phone then Side else `Two`;
			Leads = Leads;
			Detail = Title;
			Quadrants = if Ui then #Ui.Quads else 0;
		}
	end)
end

function Shared.OnStart()
	Ui = Local.Build()
	UserInputService.InputBegan:Connect(function(Input, Processed)
		if Input.KeyCode == Enum.KeyCode.Escape then -- (2.38) Esc closes the book
			if Shared.IsOpen() then Shared.Toggle(false) end
			return
		end
		if Processed or Input.KeyCode ~= TOGGLE_KEY then return end
		if Typing.Active() then return end
		Shared.Toggle()
	end)
	StateController.ProfileUpdated:Connect(function(_, Action)
		if Action and Action.type == `SetQuests` then Local.Render() end
	end)
	local Cam = workspace.CurrentCamera
	if Cam then Cam:GetPropertyChangedSignal(`ViewportSize`):Connect(function() if Shared.IsOpen() then Local.Layout() end end) end
	if Components.PreviewChanged then Components.PreviewChanged:Connect(function() if Shared.IsOpen() then Local.Layout() end end) end
	if Components.InputKindChanged then Components.InputKindChanged:Connect(function() if Shared.IsOpen() then Local.RenderFoot() end end) end
	task.spawn(Local.Probes)
end

return Shared
