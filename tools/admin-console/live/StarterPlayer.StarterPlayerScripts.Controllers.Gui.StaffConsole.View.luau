--[[ StaffConsole.View (client): draws the console from the shell's state (spec §3). Redraw(Ctx) rebuilds the dynamic
	parts; the board and frame are built once. Ctx = { S (Model state), Info, Status, Defs (server + tools), Values,
	Lists, Inspect, History, HistoryFor(UserId), LogResult, Handlers = { Side, Section, Pick, Filter, Run, Fav, Palette, Close,
	LogDay, LogQuery, LogChip, LogPage, OpenLogRow, WantHistory, Remove } }. ]]
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local Kit = require(ReplicatedStorage:WaitForChild("UI"):WaitForChild("Components"))
local Art = require(ReplicatedStorage:WaitForChild("Config"):WaitForChild("ConsoleArt"))
local Cards = require(script.Parent:WaitForChild("Cards"))
local Model = require(script.Parent:WaitForChild("Model"))
local New, Piece, Text, COL, FACE = Cards.New, Cards.Piece, Cards.Text, Cards.COL, Cards.FACE
local View = {}

function View.Build(): any
	local Gui = New("ScreenGui", { Name = "NHStaffConsole"; ResetOnSpawn = false; DisplayOrder = 40; IgnoreGuiInset = true; Enabled = false;
		ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, Players.LocalPlayer:WaitForChild("PlayerGui"))
	New("TextButton", { Name = "Scrim"; Text = ""; AutoButtonColor = false; Selectable = false; BackgroundColor3 = Color3.new(0, 0, 0);
		BackgroundTransparency = 0.45; Size = UDim2.fromScale(1, 1) }, Gui)
	local Board = New("Frame", { Name = "Board"; BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5);
		Size = UDim2.fromOffset(1600, 900) }, Gui)
	if Kit.Phone and Kit.Phone() then Kit.AutoScale(Gui) else Kit.AutoScale(Gui, { fitWidth = 1600; fitHeight = 900; fitMargin = 16 }) end
	local Frame = Piece("Frame", Board, UDim2.new(), UDim2.fromScale(1, 1))
	if not Art.Image("Frame") then (Frame :: any).BackgroundColor3 = Color3.fromRGB(18, 16, 21) end
	if Art.Image("Frame") then
		-- the uploaded Frame has a stray brass plate baked in at its centre (design 730-870 x 414-492), which shows between
		-- the card columns: cover it with a patch of the frame's own leather 400 px to its left. Roblox keeps the upload at
		-- 1024x576, so the rect is in those pixels (0.64 a design px).
		New("ImageLabel", { Name = "PlateCover"; Image = Art.Image("Frame"); BackgroundTransparency = 1; Position = UDim2.fromOffset(730, 414);
			Size = UDim2.fromOffset(140, 78); ImageRectOffset = Vector2.new(330 * 0.64, 414 * 0.64); ImageRectSize = Vector2.new(140 * 0.64, 78 * 0.64) }, Board)
	end
	if Art.Image("Crest") then New("ImageLabel", { Name = "Crest"; Image = Art.Image("Crest"); BackgroundTransparency = 1; Position = UDim2.fromOffset(768, 14); Size = UDim2.fromOffset(64, 72) }, Board) end
	return { Gui = Gui; Board = Board; Dyn = nil :: Instance? }
end

local function tile(Parent: Instance, X: number, Name: string, Label: string, Value: string, OnClick: (() -> ())?)
	-- the tile's brass rim is 6 px: the two lines sit inside it
	local T = Piece("Tile", Parent, UDim2.fromOffset(X, 16), UDim2.fromOffset(166, 60), { Name = "Tile_" .. Name })
	Text(T, "Label", Label, 20, FACE.Body, COL.Dim, UDim2.fromOffset(14, 8), UDim2.fromOffset(140, 22))
	Text(T, "Value", Value, 20, FACE.Bold, COL.Bone, UDim2.fromOffset(14, 30), UDim2.fromOffset(140, 22))
	if OnClick then
		local B = New("TextButton", { Name = "Hit"; Text = ""; BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1) }, T)
		B.Activated:Connect(OnClick)
	end
end

local function topBar(Dyn: Instance, Ctx: any)
	local S, H = Ctx.S, Ctx.Handlers
	for I, Side in Model.Sides(S.Level) do
		local On = Side == S.Side
		local P = Piece(if On then "TabOn" else "Tab", Dyn, UDim2.fromOffset(56 + (I - 1) * 158, 22), UDim2.fromOffset(150, 44), { Name = "Side_" .. Side })
		local B = New("TextButton", { Name = "Hit"; Text = string.upper(Side); TextSize = 22; FontFace = FACE.Bold; TextColor3 = if On then COL.Iron else COL.Bone;
			BackgroundTransparency = if Art.Image("Tab") then 1 else 0; BackgroundColor3 = if On then COL.Brass else COL.IronHi; Size = UDim2.fromScale(1, 1) }, P)
		B.Activated:Connect(function() H.Side(Side) end)
	end
	local Pal = Piece("Search", Dyn, UDim2.fromOffset(380, 24), UDim2.fromOffset(290, 40), { Name = "PaletteBox" })
	local PB = New("TextButton", { Name = "Hit"; Text = "Ctrl+K  Find any action…"; TextSize = 20; FontFace = FACE.Body; TextColor3 = COL.Dim; BackgroundTransparency = 1;
		Size = UDim2.fromScale(1, 1); TextXAlignment = Enum.TextXAlignment.Left }, Pal)
	New("UIPadding", { PaddingLeft = UDim.new(0, 14) }, PB)
	PB.Activated:Connect(H.Palette)
	local St = Ctx.Status and Ctx.Status.Server or {}
	tile(Dyn, 860, "Players", "Players", `{St.Players or "?"}/{St.MaxPlayers or "?"}`, nil)
	tile(Dyn, 1034, "Fps", "Server FPS", tostring(St.Fps or "?"), nil)
	tile(Dyn, 1208, "Clock", "School time", St.Clock or "—", function() if S.Level >= 2 then H.Side("Test") H.Section("School") end end)
	tile(Dyn, 1382, "Lock", "Server", if Ctx.Status and Ctx.Status.Locked then "Locked" else "Open", function() H.Side("Moderate") H.Section("Server") end)
end

-- phones: the rail and the context open over the cards; a blank button under each takes the taps that land in its gaps,
-- so they never reach the card buttons beneath (art pieces and labels don't sink input)
local function sink(Dyn: Instance, Ctx: any, Name: string, X: number, Y: number, W: number, H: number)
	if not Ctx.Phone then return end
	New("TextButton", { Name = Name; Text = ""; AutoButtonColor = false; Selectable = false; Active = true; BackgroundTransparency = 1;
		Position = UDim2.fromOffset(X, Y); Size = UDim2.fromOffset(W, H) }, Dyn)
end

local function rail(Dyn: Instance, Ctx: any)
	local S, H = Ctx.S, Ctx.Handlers
	sink(Dyn, Ctx, "RailSink", 40, 110, 394, 744)
	Piece("Side", Dyn, UDim2.fromOffset(40, 110), UDim2.fromOffset(394, 744), { Name = "Rail" })
	local Box = New("TextBox", { Name = "StudentSearch"; PlaceholderText = "Search students"; Text = S.Filter; TextSize = 20; FontFace = FACE.Body;
		TextColor3 = COL.Bone; PlaceholderColor3 = COL.Dim; BackgroundColor3 = COL.IronHi; BackgroundTransparency = if Art.Image("Search") then 1 else 0;
		ClearTextOnFocus = false; Position = UDim2.fromOffset(91, 128); Size = UDim2.fromOffset(292, 40); TextXAlignment = Enum.TextXAlignment.Left; ZIndex = 2 }, Dyn)
	New("UIPadding", { PaddingLeft = UDim.new(0, 16); PaddingRight = UDim.new(0, 12) }, Box)
	Piece("Search", Dyn, UDim2.fromOffset(91, 128), UDim2.fromOffset(292, 40), { Name = "StudentSearchArt" })
	Box.FocusLost:Connect(function() H.Filter(Box.Text) end)
	Box:GetPropertyChangedSignal("Text"):Connect(function() S.Filter = Box.Text end)
	local L = New("ScrollingFrame", { Name = "Rows"; BackgroundTransparency = 1; Position = UDim2.fromOffset(91, 180); Size = UDim2.fromOffset(300, 660);
		CanvasSize = UDim2.new(); AutomaticCanvasSize = Enum.AutomaticSize.Y; ScrollBarThickness = 6; Selectable = false }, Dyn)
	New("UIListLayout", { Padding = UDim.new(0, 6) }, L)
	local Rows = Model.Rows(Ctx.Status and Ctx.Status.Players or (Ctx.Info and Ctx.Info.Players) or {}, S.Filter, S.Recent)
	for _, P in Rows do
		local On = P.UserId == S.Selected
		local R = Piece(if On then "RowOn" else "Row", L, UDim2.new(), UDim2.fromOffset(292, 70), { Name = "Row_" .. P.UserId })
		-- the row art's portrait well: a ring centred at (33, 36), about 42 px across inside; the text starts right of it
		local Face = New("ImageLabel", { Name = "Face"; Image = `rbxthumb://type=AvatarHeadShot&id={P.UserId}&w=48&h=48`; BackgroundTransparency = 1;
			Position = UDim2.fromOffset(14, 17); Size = UDim2.fromOffset(38, 38) }, R)
		New("UICorner", { CornerRadius = UDim.new(0.5, 0) }, Face)
		Text(R, "Name", P.Display ~= P.Name and `{P.Display} (@{P.Name})` or P.Name, 22, FACE.Bold, if On then COL.Brass else COL.Bone, UDim2.fromOffset(66, 9), UDim2.fromOffset(214, 28))
		local Flags = Model.Flags(P)
		Text(R, "Sub", `{P.Sub or P.Race or "?"} · {P.Ping or 0} ms` .. (if #Flags > 0 then "  " .. table.concat(Flags, " ") else ""), 20, FACE.Body,
			if #Flags > 0 then COL.Crimson else COL.Dim, UDim2.fromOffset(66, 36), UDim2.fromOffset(214, 24))
		local B = New("TextButton", { Name = "Hit"; Text = ""; BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1) }, R)
		B.Activated:Connect(function() H.Pick(P.UserId) end)
	end
end

local function sections(Dyn: Instance, Ctx: any)
	local S, H = Ctx.S, Ctx.Handlers
	local List = (Ctx.Info and Ctx.Info.Sections or {})[S.Side] or {}
	local N = math.max(1, #List)
	local W = math.floor((Ctx.W - (N - 1) * 6) / N)
	for I, Name in List do
		local On = Name == S.Section
		local P = Piece(if On then "TabOn" else "Tab", Dyn, UDim2.fromOffset(Ctx.X + (I - 1) * (W + 6), 110), UDim2.fromOffset(W, 44), { Name = "Section_" .. Name })
		local B = New("TextButton", { Name = "Hit"; Text = ""; BackgroundTransparency = if Art.Image("Tab") then 1 else 0; BackgroundColor3 = if On then COL.Brass else COL.IronHi; Size = UDim2.fromScale(1, 1) }, P)
		-- TabOn has a red gem at its bottom centre (design 69-81 x 33-44, 300x88 upload so no downscale). The tab is 9-sliced,
		-- so at any width but its own 150 the gem is stretched or squashed: cover it with the plain rim beside it, then draw
		-- the gem again at its own size in the middle
		if On and Art.Image("TabOn") and W ~= 150 then
			local Half = math.ceil(6 * math.max(1, (W - 24) / 126)) + 2
			New("ImageLabel", { Name = "GemCover"; Image = Art.Image("TabOn"); BackgroundTransparency = 1; ImageRectOffset = Vector2.new(40, 64);
				ImageRectSize = Vector2.new(40, 24); Position = UDim2.fromOffset(math.floor(W / 2) - Half, 32); Size = UDim2.fromOffset(Half * 2, 12) }, P)
			New("ImageLabel", { Name = "Gem"; Image = Art.Image("TabOn"); BackgroundTransparency = 1; ImageRectOffset = Vector2.new(138, 66);
				ImageRectSize = Vector2.new(24, 22); Position = UDim2.fromOffset(math.floor(W / 2) - 6, 33); Size = UDim2.fromOffset(12, 11) }, P)
		end
		local Img = Art.Image("Sec" .. Name)
		local TX = 8
		if Img and W >= 140 then New("ImageLabel", { Image = Img; BackgroundTransparency = 1; Position = UDim2.fromOffset(6, 6); Size = UDim2.fromOffset(32, 32) }, P) TX = 42 end
		local Lbl = Text(P, "Label", Name, 20, FACE.Bold, if On then COL.Iron else COL.Bone, UDim2.fromOffset(TX, 0), UDim2.new(1, -TX - 8, 1, 0))
		Lbl.TextYAlignment = Enum.TextYAlignment.Center
		if TX == 8 then Lbl.TextXAlignment = Enum.TextXAlignment.Center end
		B.Activated:Connect(function() H.Section(Name) end)
	end
end

local function grid(Dyn: Instance, Ctx: any)
	local S, H = Ctx.S, Ctx.Handlers
	local Favs = Model.Favourites(Ctx.Defs, S)
	local Top = 160
	if #Favs > 0 then
		local Strip = New("ScrollingFrame", { Name = "Favourites"; BackgroundTransparency = 1; Position = UDim2.fromOffset(Ctx.X, 160); Size = UDim2.fromOffset(Ctx.W, 44);
			CanvasSize = UDim2.new(); AutomaticCanvasSize = Enum.AutomaticSize.X; ScrollingDirection = Enum.ScrollingDirection.X; ScrollBarThickness = 4 }, Dyn)
		New("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal; Padding = UDim.new(0, 6) }, Strip)
		for _, D in Favs do
			local B = New("TextButton", { Name = "Fav_" .. D.Id; Text = "★ " .. D.Title; TextSize = 20; FontFace = FACE.Bold; TextColor3 = COL.Iron; BackgroundColor3 = COL.Brass;
				AutomaticSize = Enum.AutomaticSize.X; Size = UDim2.fromOffset(0, 40) }, Strip)
			New("UIPadding", { PaddingLeft = UDim.new(0, 12); PaddingRight = UDim.new(0, 12) }, B)
			B.Activated:Connect(function() H.Side(D.Side) H.Section(D.Section) end)
		end
		Top = 206
	end
	local G = New("ScrollingFrame", { Name = "Cards"; BackgroundTransparency = 1; Position = UDim2.fromOffset(Ctx.X, Top); Size = UDim2.fromOffset(Ctx.W + 8, 746 - Top);
		CanvasSize = UDim2.new(); AutomaticCanvasSize = Enum.AutomaticSize.Y; ScrollBarThickness = 6; Selectable = false }, Dyn)
	local List = Model.Cards(Ctx.Defs, S.Side, S.Section)
	local Cols = math.max(1, math.floor((Ctx.W + 12) / 392))
	for I, D in List do
		local Col, Row = (I - 1) % Cols, (I - 1) // Cols
		Ctx.Values[D.Id] = Ctx.Values[D.Id] or {}
		local Note = nil
		if D.Id == "Unban" then
			local Id = tonumber(Ctx.Values.Unban and Ctx.Values.Unban.UserId)
			if Id then
				H.WantHistory(Id)
				Note = Model.UnbanNote(Ctx.HistoryFor(Id)) or "Checking their record…"
			end
		end
		Cards.Card(G, D, UDim2.fromOffset(Col * 392, Row * 180), {
			Values = Ctx.Values[D.Id]; Lists = Ctx.Lists; Fav = table.find(S.Favs, D.Id) ~= nil; Reduced = Ctx.Reduced; Note = Note;
			OnRun = H.Run; OnFav = H.Fav; Redraw = H.Redraw;
			-- on the board, not the dynamic layer, so the shell's status refresh doesn't take it away (it waits for it)
			OnPick = function(A, Choices, Done) Cards.Picker(Dyn.Parent :: Instance, A.Label or A.Name, Choices, Done) end;
		})
	end
	if #List == 0 then Text(G, "Empty", "Nothing here for your level.", 20, FACE.Body, COL.Dim, UDim2.fromOffset(8, 8), UDim2.fromOffset(700, 30)) end
end

local function feed(Dyn: Instance, Ctx: any)
	local F = Piece("Feed", Dyn, UDim2.fromOffset(Ctx.X, 756), UDim2.fromOffset(774, 120), { Name = "Feed" })
	for I, E in Ctx.S.Feed do
		if I > 5 then break end -- the last 5 results (layout table), 22 px rows inside the 120 px feed
		Text(F, "Line" .. I, (if E.Ok then "✓ " else "✕ ") .. E.Text, 20, FACE.Body, if E.Ok then COL.Good else COL.Crimson,
			UDim2.fromOffset(18, 8 + (I - 1) * 22), UDim2.fromOffset(740, 22))
	end
	if #Ctx.S.Feed == 0 then Text(F, "Hint", "Results show here.", 20, FACE.Body, COL.Dim, UDim2.fromOffset(18, 8), UDim2.fromOffset(740, 26)) end
end

-- the Log section (spec 1b §5): a day picker (today and the 6 days before), search, chips, 50 rows a page. A row opens
-- its target's history in the right-hand panel, even if they're offline.
local function logView(Dyn: Instance, Ctx: any)
	local H, L = Ctx.Handlers, Ctx.S.Log
	local X, W = Ctx.X, Ctx.W
	local function strip(Name: string, PX: number, PY: number, PW: number): Instance
		local F = New("Frame", { Name = Name; BackgroundTransparency = 1; Position = UDim2.fromOffset(PX, PY); Size = UDim2.fromOffset(PW, 40) }, Dyn)
		New("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal; Padding = UDim.new(0, 6); SortOrder = Enum.SortOrder.LayoutOrder }, F)
		return F
	end
	local Days = strip("LogDays", X, 160, W)
	local Now = os.time()
	for Off = 0, 6 do
		local B = Cards.Chip(Days, "Day_" .. Off, Model.DayLabel(Off, Now), L.Day == Off)
		local Holder = B.Parent :: any
		Holder.LayoutOrder = Off
		B.Activated:Connect(function() H.LogDay(Off) end)
	end
	local Box = New("TextBox", { Name = "LogSearch"; PlaceholderText = "Staff, student, UserId or action"; Text = L.Query; TextSize = 20; FontFace = FACE.Body;
		TextColor3 = COL.Bone; PlaceholderColor3 = COL.Dim; BackgroundColor3 = COL.IronHi; ClearTextOnFocus = false;
		Position = UDim2.fromOffset(X, 208); Size = UDim2.fromOffset(330, 40); TextXAlignment = Enum.TextXAlignment.Left }, Dyn)
	New("UICorner", { CornerRadius = UDim.new(0, 8) }, Box)
	New("UIPadding", { PaddingLeft = UDim.new(0, 12); PaddingRight = UDim.new(0, 8) }, Box)
	Box.FocusLost:Connect(function() H.LogQuery(Box.Text) end)
	local Chips = strip("LogChips", X + 340, 210, W - 340)
	for I, C in { "All", "Moderate", "Test", "Refused" } do
		local B = Cards.Chip(Chips, "Chip_" .. C, C, L.Chip == C)
		local Holder = B.Parent :: any
		Holder.LayoutOrder = I
		B.Activated:Connect(function() H.LogChip(C) end)
	end
	local List = New("ScrollingFrame", { Name = "LogRows"; BackgroundTransparency = 1; Position = UDim2.fromOffset(X, 258); Size = UDim2.fromOffset(W + 8, 438);
		CanvasSize = UDim2.new(); AutomaticCanvasSize = Enum.AutomaticSize.Y; ScrollBarThickness = 6; Selectable = false }, Dyn)
	New("UIListLayout", { Padding = UDim.new(0, 4); SortOrder = Enum.SortOrder.LayoutOrder }, List)
	local R = Ctx.LogResult
	if R == nil then Text(List, "Status", "Loading…", 20, FACE.Body, COL.Dim, UDim2.new(), UDim2.fromOffset(W, 28)) return end
	if not R.Ok then Text(List, "Status", R.Error or "Log unavailable", 20, FACE.Bold, COL.Crimson, UDim2.new(), UDim2.fromOffset(W, 28)) return end
	for I, E in R.Rows do
		local B = New("TextButton", { Name = "LogRow_" .. I; Text = ""; AutoButtonColor = true; BackgroundColor3 = COL.IronHi; BackgroundTransparency = 0.3;
			Size = UDim2.fromOffset(W - 4, 52); LayoutOrder = I }, List)
		New("UICorner", { CornerRadius = UDim.new(0, 6) }, B)
		Text(B, "Head", Model.LogHead(E), 20, FACE.Bold, if E.Ok then COL.Bone else COL.Crimson, UDim2.fromOffset(10, 3), UDim2.new(1, -20, 0, 24))
		Text(B, "Detail", if E.Detail ~= "" then E.Detail else "—", 20, FACE.Body, COL.Dim, UDim2.fromOffset(10, 26), UDim2.new(1, -20, 0, 24))
		B.Activated:Connect(function() H.OpenLogRow(E) end)
	end
	if #R.Rows == 0 then Text(List, "Status", "Nothing logged for this day.", 20, FACE.Body, COL.Dim, UDim2.new(), UDim2.fromOffset(W, 28)) end
	local function pageButton(Name: string, Label: string, PX: number, Delta: number, On: boolean)
		local B = New("TextButton", { Name = Name; Text = Label; TextSize = 20; FontFace = FACE.Bold; TextColor3 = if On then COL.Bone else COL.Dim;
			BackgroundColor3 = COL.IronHi; AutoButtonColor = On; Active = On; Position = UDim2.fromOffset(PX, 702); Size = UDim2.fromOffset(100, 40) }, Dyn)
		New("UICorner", { CornerRadius = UDim.new(0, 8) }, B)
		if On then B.Activated:Connect(function() H.LogPage(Delta) end) end
	end
	pageButton("LogPrev", "Prev", X, -1, R.Page > 1)
	local Pg = Text(Dyn, "LogPage", `Page {R.Page} of {R.Pages} · {R.Total} entries`, 20, FACE.Body, COL.Dim, UDim2.fromOffset(X + 110, 710), UDim2.fromOffset(W - 220, 28))
	Pg.TextXAlignment = Enum.TextXAlignment.Center
	pageButton("LogNext", "Next", X + W - 100, 1, R.Page < R.Pages)
end

-- the saved record (spec 1b §5): the summary line, then newest first with one icon per kind; lifted or ended bans and
-- mutes greyed; at level 3 a remove button on each, with the 0.8 s hold
local function history(Body: Instance, Ctx: any, Next: () -> number, line: (string, number?, Color3?, boolean?) -> ())
	local H = Ctx.History
	line("History", 22, COL.Brass, true)
	if H == nil then line("Loading…", 20, COL.Dim) return end
	if not H.Ok then line(H.Error or "History unavailable", 20, COL.Crimson, true) return end
	local Now = os.time()
	local Rows = Model.Timeline(H.Record, Ctx.S.Level, Now)
	if #Rows == 0 then line("Nothing on record.", 20, COL.Dim) return end
	line(Model.Summary(H.Record, Now), 20, COL.Bone, true)
	for I, R in Rows do
		local F = New("Frame", { Name = "Entry_" .. I; BackgroundTransparency = 1; Size = UDim2.new(1, -8, 0, 0); AutomaticSize = Enum.AutomaticSize.Y; LayoutOrder = Next() }, Body)
		New("UIPadding", { PaddingBottom = UDim.new(0, 6) }, F)
		local Img = Art.Image(R.Kind)
		if Img then
			New("ImageLabel", { Name = "Icon"; Image = Img; BackgroundTransparency = 1; ImageTransparency = if R.Lifted then 0.5 else 0;
				Position = UDim2.fromOffset(0, 2); Size = UDim2.fromOffset(28, 28) }, F)
		end
		local Right = if R.CanRemove then 44 else 0
		Text(F, "Head", `{R.Who} · {os.date("%d %b %H:%M", R.At)}`, 20, FACE.Body, COL.Dim,
			UDim2.fromOffset(34, 0), UDim2.new(1, -34 - Right, 0, 24))
		-- the state goes after the text, which wraps: at the end of the head line it was cut off
		local Body2 = Text(F, "Text", (if R.Text ~= "" then R.Text else R.Kind) .. (if R.State then ` ({R.State})` else ""), 20, FACE.Body, if R.Lifted then COL.Dim else COL.Bone,
			UDim2.fromOffset(34, 24), UDim2.new(1, -34 - Right, 0, 0), true)
		Body2.AutomaticSize = Enum.AutomaticSize.Y
		if R.Lifted then Body2.TextTransparency = 0.35 end
		if R.CanRemove then
			local B = New("TextButton", { Name = "Remove"; Text = "✕"; TextSize = 20; FontFace = FACE.Bold; TextColor3 = COL.Bone; BackgroundColor3 = COL.Velvet;
				AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, 0, 0, 4); Size = UDim2.fromOffset(36, 36) }, F)
			New("UICorner", { CornerRadius = UDim.new(0, 8) }, B)
			local Ring = New("ImageLabel", { Name = "HoldRing"; Image = Art.Image("HoldRing") or "rbxassetid://0"; BackgroundTransparency = 1; ImageTransparency = 1;
				AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromOffset(36, 36); ZIndex = 3 }, B)
			Cards.Hold(B, Ring, Ctx.Reduced, function() Ctx.Handlers.Remove(R) end)
		end
	end
end

local function context(Dyn: Instance, Ctx: any)
	local S = Ctx.S
	sink(Dyn, Ctx, "ContextSink", 1240, 110, 320, 696)
	local C = Piece("Rail", Dyn, UDim2.fromOffset(1240, 110), UDim2.fromOffset(320, 696), { Name = "Context" })
	local Body = New("ScrollingFrame", { Name = "Body"; BackgroundTransparency = 1; Position = UDim2.fromOffset(20, 20); Size = UDim2.fromOffset(284, 656);
		CanvasSize = UDim2.new(); AutomaticCanvasSize = Enum.AutomaticSize.Y; ScrollBarThickness = 6 }, C)
	New("UIListLayout", { Padding = UDim.new(0, 6); SortOrder = Enum.SortOrder.LayoutOrder }, Body)
	local N = 0
	local function line(T: string, Size: number?, Color: Color3?, Bold: boolean?)
		N += 1
		local L = Text(Body, "L" .. N, T, Size or 20, if Bold then FACE.Bold else FACE.Body, Color or COL.Bone, UDim2.new(), UDim2.new(1, -8, 0, 0), true)
		L.AutomaticSize = Enum.AutomaticSize.Y
		L.LayoutOrder = N
	end
	local Players = (Ctx.Status and Ctx.Status.Players) or (Ctx.Info and Ctx.Info.Players) or {}
	local P
	for _, R in Players do if R.UserId == S.Selected then P = R end end
	if S.Side == "Moderate" and S.Section == "Server" then
		line("Action log (this server)", 22, COL.Brass, true)
		for I, E in (Ctx.Info and Ctx.Info.Log) or {} do
			if I > 12 then break end
			line(`{os.date("%H:%M", E.T)} {E.Admin}: {E.Command} {E.Target}`, 20, COL.Dim)
		end
		return
	end
	if not P and not (S.Selected and S.Offline) then line("Pick a student on the left.", 20, COL.Dim) return end
	local function idBox(UserId: number)
		N += 1
		local Id = New("TextBox", { Name = "UserId"; Text = tostring(UserId); TextEditable = false; ClearTextOnFocus = false; TextSize = 20; FontFace = FACE.Body;
			TextColor3 = COL.Dim; BackgroundColor3 = COL.IronHi; Size = UDim2.new(1, -8, 0, 36); LayoutOrder = N }, Body)
		New("UICorner", { CornerRadius = UDim.new(0, 6) }, Id)
	end
	if P then
		line(P.Display or P.Name, 26, COL.Brass, true)
		idBox(P.UserId)
		line(`{P.Sub or P.Race or "?"}{if P.Tier then " · Tier " .. ({ "I", "II", "III" })[P.Tier] else ""}{if P.Height then " · " .. P.Height else ""}`)
		line(`Health {P.Health}/{P.MaxHealth} · {P.Ping} ms · staff level {P.Level}`)
		local Flags = Model.Flags(P)
		if #Flags > 0 then line(table.concat(Flags, "  "), 20, COL.Crimson, true) end
		local I = Ctx.Inspect
		if S.Side == "Test" and I and I.UserId == P.UserId then
			line("Inspector", 22, COL.Brass, true)
			line(`Slot {I.Slot or "?"} · ¥{I.Yen} · Level {I.Level or "?"} ({I.Exp or 0} EXP, {I.Points or 0} points)`)
			line(`Discipline {I.Discipline.Points or 0} ({I.Discipline.Level or "Clear"}), owes {I.Discipline.Owed or 0}`)
			line(`Places {I.Regions}/{I.RegionsTotal} · Club {I.Club ~= "" and I.Club or "none"}`)
			line(`Title {I.Title ~= "" and I.Title or "none"} · {#I.Titles} titles`)
			if #I.Quests > 0 then line("Quests: " .. table.concat(I.Quests, ", ")) end
			if I.Note then line(`Note ({I.Note.By}): {I.Note.Text}`, 20, COL.Dim) end
		end
	else
		local H = Ctx.History
		line(if H and H.Ok and H.Name then H.Name else `UserId {S.Selected}`, 26, COL.Brass, true)
		idBox(S.Selected)
		line("Not in this server", 20, COL.Dim)
	end
	if S.Side == "Moderate" then history(Body, Ctx, function() N += 1 return N end, line) end
end

function View.Redraw(U: any, Ctx: any)
	if U.Dyn then U.Dyn:Destroy() end
	local OldPicker = U.Board:FindFirstChild("Picker") -- it belongs to a card of the layer being rebuilt
	if OldPicker then OldPicker:Destroy() end
	local Dyn = New("Frame", { Name = "Dyn"; BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1) }, U.Board)
	U.Dyn = Dyn
	-- phones: the centre takes the whole board (3 card columns); the rail and the context open over it (spec §5)
	local Phone = Kit.Phone and Kit.Phone() or false
	Ctx.X, Ctx.W = if Phone then 40 else 450, if Phone then 1520 else 772
	Ctx.Phone = Phone
	local function button(Name: string, Label: string, X: number, Fn: () -> (), Color: Color3)
		local B = New("TextButton", { Name = Name; Text = Label; TextSize = 20; FontFace = FACE.Bold; TextColor3 = COL.Bone; BackgroundColor3 = Color;
			Position = UDim2.fromOffset(X, 820); Size = UDim2.fromOffset(120, 44); ZIndex = 5 }, Dyn)
		New("UICorner", { CornerRadius = UDim.new(0, 8) }, B)
		B.Activated:Connect(Fn)
	end
	topBar(Dyn, Ctx)
	sections(Dyn, Ctx)
	if Ctx.S.Side == "Moderate" and Ctx.S.Section == "Log" then logView(Dyn, Ctx) else grid(Dyn, Ctx) end
	feed(Dyn, Ctx)
	if Phone then
		button("Students", "Students", 1180, Ctx.Handlers.PhoneRail, COL.IronHi)
		button("Details", "Details", 1310, Ctx.Handlers.PhoneContext, COL.IronHi)
		if Ctx.S.PhoneRail then rail(Dyn, Ctx) end
		if Ctx.S.PhoneContext then context(Dyn, Ctx) end
	else
		rail(Dyn, Ctx)
		context(Dyn, Ctx)
	end
	button("Close", "Close", 1440, Ctx.Handlers.Close, COL.Velvet)
end

return View
