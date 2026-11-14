--[[
	AdminPanel (client): the Headmaster's Desk. F3 toggles it for staff (the server decides who is staff).
	Built only from the game's UI kit (ReplicatedStorage.UI.Components / Theme): Panel, TabBar, Button, SearchBar,
	Toggle, Slider, SectionHeader, Plate, Divider, Toast + Theme images (Crest, SlotBg, Glow).

	Left: every student in the server (search, health, race, flags). Right: tabbed commands on the selected
	student, the world, spawns, your own tools, and the server log. Every action goes through
	ReplicatedStorage.NHAdmin.Run and is checked again on the server.

	Self tools that run here: Fly (WASD / Space / Ctrl, Shift for speed), Noclip, ESP (names + health through
	walls), Click-teleport (Ctrl + click), Spectate.

	1.18: School, Progress and Activities tabs (and a bigger World tab) for the systems added since the desk shipped,
	plus QOL: "Find a command" searches every tab and jumps to the button; right-click any button to pin it to a
	Favourites row on every tab (this session); the last five students you picked float to the top; the selected
	student's UserId sits in a box you can copy from; Bring / Freeze / Thaw everyone; staff notes; server lock;
	a read-only inspector of a student's loaded slot (Progress tab).
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local UserInputService = game:GetService(`UserInputService`)

local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))
local Theme = require(ReplicatedStorage.UI.Theme)
local Col = Theme.Colors

local Player = Players.LocalPlayer
local Shared = {}

local Ui = nil
local State = { Level = 0; Selected = nil; Tab = 1; Info = nil; Filter = ``; Recent = {} :: { number }; Jump = nil :: string?; SendTarget = false }
State.Fields = {} :: { [string]: string } -- (audit) every text field's current text, by placeholder (pinned buttons read it)
local Tools = { Fly = false; Noclip = false; Esp = false; ClickTp = false }
local Conns = {}

local TABS = { `Moderation`, `Student`, `School`, `Progress`, `Activities`, `World`, `Spawns`, `Self`, `Server` }
local Index = {} :: { { Label: string, Tab: number } } -- every command button, for the command search
local Favs = {} :: { [string]: { Tab: number, OnClick: () -> (), Style: string? } } -- right-clicked buttons (this session)
local Rendering = 0 -- the tab being built (so buttons know where they live)
local Indexing = false
local Live = {} :: { [string]: any } -- (audit) the Spawns / Server labels the 3 s refresh updates in place

---------------------------------------------------------------- remote helpers

local function remotes()
	local F = ReplicatedStorage:FindFirstChild(`NHAdmin`)
	if not (F and F:GetAttribute(`Ready`)) then return nil end
	return F
end

local Busy = false
local function run(Command: string, NeedsTarget: boolean?, Args: { [string]: any }?, Target: number?) -- (audit) Target: act on someone without selecting them
	local F = remotes()
	if not F or Busy then return end
	if NeedsTarget and not (Target or State.Selected) then Shared.Status(`Pick a student on the left first`, true) return end
	Busy = true
	local token = {}
	Shared.Token = token
	task.delay(6, function() if Shared.Token == token then Busy = false end end)
	local ok, a, b = pcall(F.Run.InvokeServer, F.Run, Command, NeedsTarget and (Target or State.Selected) or nil, Args or {})
	if Shared.Token == token then Busy = false end
	if not ok then Shared.Status(`Request failed`, true) return end
	Shared.Status(tostring(b or (a and `Done` or `Failed`)), not a)
	task.defer(Shared.Refresh)
end

local function info()
	local F = remotes()
	if not F then return nil end
	local ok, r = pcall(F.Info.InvokeServer, F.Info)
	return ok and r or nil
end

---------------------------------------------------------------- small builders (kit-styled)

local function label(Parent: Instance, Text: string, Size: number?, Color: Color3?, Order: number?, Align: Enum.TextXAlignment?)
	local L = Instance.new(`TextLabel`)
	L.BackgroundTransparency = 1
	L.Size = UDim2.new(1, 0, 0, (Size or 18) + 8)
	L.Font = Theme.Fonts.Body
	L.TextSize = Size or 18
	L.TextColor3 = Color or Col.Text
	L.TextXAlignment = Align or Enum.TextXAlignment.Left
	L.TextWrapped = true
	L.RichText = true
	L.Text = Text
	L.LayoutOrder = Order or 0
	L.Parent = Parent
	return L
end

local function list(Parent: Instance, Pad: number?, Horizontal: boolean?)
	local L = Instance.new(`UIListLayout`)
	L.Padding = UDim.new(0, Pad or 6)
	L.SortOrder = Enum.SortOrder.LayoutOrder
	if Horizontal then L.FillDirection = Enum.FillDirection.Horizontal; L.VerticalAlignment = Enum.VerticalAlignment.Center end
	L.Parent = Parent
	return L
end

local function frame(Parent: Instance, Size: UDim2, Order: number?)
	local F = Instance.new(`Frame`)
	F.BackgroundTransparency = 1
	F.Size = Size
	F.LayoutOrder = Order or 0
	F.Parent = Parent
	return F
end

local function scroll(Parent: Instance, Size: UDim2, Order: number?)
	local S = Instance.new(`ScrollingFrame`)
	S.BackgroundTransparency = 1
	S.BorderSizePixel = 0
	S.Size = Size
	S.LayoutOrder = Order or 0
	S.ScrollBarThickness = 6
	S.ScrollBarImageColor3 = Col.Gold
	S.AutomaticCanvasSize = Enum.AutomaticSize.Y
	S.CanvasSize = UDim2.new()
	S.Parent = Parent
	return S
end

local function button(Parent: Instance, Text: string, OnClick: () -> (), Style: string?, Width: number?, Order: number?)
	-- crimson (destructive) buttons need a second click within 3 seconds
	local armed = 0
	local B, BApi
	B, BApi = Kit.Button({ text = Text; style = Style; textSize = 18; onClick = function()
		if Style == `crimson` then
			if os.clock() - armed > 3 then
				armed = os.clock()
				if BApi and BApi.Label then BApi.Label.Text = `Confirm?` end
				Shared.Status(`Click {Text} again to confirm`, true)
				task.delay(3, function() if BApi and BApi.Label and os.clock() - armed >= 3 then BApi.Label.Text = Text end end)
				return
			end
			armed = 0
			if BApi and BApi.Label then BApi.Label.Text = Text end
		end
		OnClick()
	end })
	B.Size = UDim2.fromOffset(Width or 178, 40)
	B.LayoutOrder = Order or 0
	B.Name = Text
	B.Parent = Parent
	-- QOL: every button is findable by the command search; right-click pins it to the favourites row
	if Rendering > 0 then
		if Indexing then table.insert(Index, { Label = Text; Tab = Rendering }) end
		if B:IsA(`GuiButton`) then
			local Home = Rendering
			B.MouseButton2Click:Connect(function()
				if Favs[Text] then
					Favs[Text] = nil
					Shared.Status(`Unpinned {Text}`)
				else
					Favs[Text] = { Tab = Home; OnClick = OnClick; Style = Style }
					Shared.Status(`Pinned {Text} to your favourites (right-click it again to unpin)`)
				end
				task.defer(Shared.RenderTab)
			end)
		end
	end
	return B
end

local function grid(Parent: Instance, Order: number?, CellW: number?)
	local G = frame(Parent, UDim2.new(1, 0, 0, 0), Order)
	G.AutomaticSize = Enum.AutomaticSize.Y
	local L = Instance.new(`UIGridLayout`)
	L.CellSize = UDim2.fromOffset(CellW or 178, 40)
	L.CellPadding = UDim2.fromOffset(10, 10)
	L.SortOrder = Enum.SortOrder.LayoutOrder
	L.Parent = G
	return G
end

local function field(Parent: Instance, Placeholder: string, Width: number, Order: number?)
	local Bar, Api = Kit.SearchBar({ placeholder = Placeholder })
	Bar.Size = UDim2.fromOffset(Width, 40)
	Bar.LayoutOrder = Order or 0
	Bar.Parent = Parent
	-- (audit) the text lives in State.Fields (kept across rebuilds) and callers read .Text through a proxy, so a pinned
	-- favourite reads what is typed now, not the destroyed box it was pinned from
	local Box = Api.TextBox
	Box.Text = State.Fields[Placeholder] or ``
	Box:GetPropertyChangedSignal(`Text`):Connect(function() State.Fields[Placeholder] = Box.Text end)
	return setmetatable({}, { __index = function(_, K) if K == `Text` then return State.Fields[Placeholder] or `` end return nil end })
end

local function header(Parent: Instance, Text: string, Order: number)
	local H = Kit.SectionHeader({ text = Text; textSize = 20 })
	H.Size = UDim2.new(1, 0, 0, 30)
	H.LayoutOrder = Order
	H.Parent = Parent
	return H
end

---------------------------------------------------------------- self tools (client side)

local function root()
	local C = Player.Character
	return C and C:FindFirstChild(`HumanoidRootPart`), C and C:FindFirstChildWhichIsA(`Humanoid`)
end

local function setFly(on: boolean)
	Tools.Fly = on
	if Conns.Fly then Conns.Fly:Disconnect() Conns.Fly = nil end
	local R, H = root()
	if not (R and H) then return end
	local att = R:FindFirstChild(`NHFlyAtt`)
	if not on then
		for _, n in { `NHFlyAtt`, `NHFlyVel`, `NHFlyGyro` } do local x = R:FindFirstChild(n) if x then x:Destroy() end end
		H.PlatformStand = false
		return
	end
	att = Instance.new(`Attachment`); att.Name = `NHFlyAtt`; att.Parent = R
	local lv = Instance.new(`LinearVelocity`); lv.Name = `NHFlyVel`; lv.Attachment0 = att; lv.MaxForce = 1e6
	lv.RelativeTo = Enum.ActuatorRelativeTo.World; lv.VectorVelocity = Vector3.zero; lv.Parent = R
	local ao = Instance.new(`AlignOrientation`); ao.Name = `NHFlyGyro`; ao.Mode = Enum.OrientationAlignmentMode.OneAttachment
	ao.Attachment0 = att; ao.Responsiveness = 60; ao.MaxTorque = 1e6; ao.Parent = R
	H.PlatformStand = true
	Conns.Fly = RunService.RenderStepped:Connect(function()
		local cam = workspace.CurrentCamera
		if not (R.Parent and cam) then return end
		local d = Vector3.zero
		local cf = cam.CFrame
		if UserInputService:IsKeyDown(Enum.KeyCode.W) then d += cf.LookVector end
		if UserInputService:IsKeyDown(Enum.KeyCode.S) then d -= cf.LookVector end
		if UserInputService:IsKeyDown(Enum.KeyCode.D) then d += cf.RightVector end
		if UserInputService:IsKeyDown(Enum.KeyCode.A) then d -= cf.RightVector end
		if UserInputService:IsKeyDown(Enum.KeyCode.Space) then d += Vector3.yAxis end
		if UserInputService:IsKeyDown(Enum.KeyCode.LeftControl) then d -= Vector3.yAxis end
		local speed = UserInputService:IsKeyDown(Enum.KeyCode.LeftShift) and 140 or 60
		lv.VectorVelocity = if d.Magnitude > 0 then d.Unit * speed else Vector3.zero
		ao.CFrame = CFrame.lookAt(Vector3.zero, Vector3.new(cf.LookVector.X, 0, cf.LookVector.Z).Unit)
	end)
end

local function setNoclip(on: boolean)
	Tools.Noclip = on
	if Conns.Noclip then Conns.Noclip:Disconnect() Conns.Noclip = nil end
	if on then
		Conns.Noclip = RunService.Stepped:Connect(function()
			local C = Player.Character
			if not C then return end
			for _, p in C:GetDescendants() do if p:IsA(`BasePart`) and p.CanCollide then p.CanCollide = false end end
		end)
	end
end

local EspFolder
local function setEsp(on: boolean)
	Tools.Esp = on
	if Conns.Esp then Conns.Esp:Disconnect() Conns.Esp = nil end
	if EspFolder then EspFolder:Destroy() EspFolder = nil end
	if not on then return end
	EspFolder = Instance.new(`Folder`); EspFolder.Name = `NHAdminEsp`; EspFolder.Parent = workspace.CurrentCamera
	local function refresh()
		if not EspFolder then return end
		EspFolder:ClearAllChildren()
		for _, P in Players:GetPlayers() do
			local C = P.Character
			if P ~= Player and C and C:FindFirstChild(`Head`) then
				local h = Instance.new(`Highlight`); h.Adornee = C; h.FillTransparency = 0.8; h.FillColor = Col.Crimson
				h.OutlineColor = Col.Gold; h.DepthMode = Enum.HighlightDepthMode.AlwaysOnTop; h.Parent = EspFolder
				local b = Instance.new(`BillboardGui`); b.Adornee = C.Head; b.Size = UDim2.fromOffset(200, 40); b.StudsOffset = Vector3.new(0, 2.6, 0)
				b.AlwaysOnTop = true; b.Parent = EspFolder
				local hum = C:FindFirstChildWhichIsA(`Humanoid`)
				local l = label(b, `{P.DisplayName}  ·  {hum and math.floor(hum.Health) or 0} HP`, 16, Col.Gold, 0, Enum.TextXAlignment.Center)
				l.Size = UDim2.fromScale(1, 1); l.TextStrokeTransparency = 0.3
			end
		end
	end
	refresh()
	local t = 0
	Conns.Esp = RunService.Heartbeat:Connect(function(dt) t += dt if t > 1 then t = 0 refresh() end end)
end

local function setClickTp(on: boolean)
	Tools.ClickTp = on
end

---------------------------------------------------------------- the panel

local function playerRow(Parent: Instance, P: any, Order: number)
	local selected = State.Selected == P.UserId
	local B = Instance.new(`ImageButton`)
	B.Name = P.Name
	B.Size = UDim2.new(1, -8, 0, 58)
	B.LayoutOrder = Order
	B.Image = Theme.Images.SlotBg
	B.ImageColor3 = selected and Col.Gold or Col.IronDim
	B.ImageTransparency = selected and 0.2 or 0.45
	B.ScaleType = Enum.ScaleType.Slice
	B.SliceCenter = Rect.new(16, 16, 48, 48)
	B.BackgroundTransparency = 1
	B.AutoButtonColor = true
	B.Parent = Parent
	local n = label(B, `<b>{P.Display}</b>  <font color="#9a8f80">@{P.Name}</font>`, 18, selected and Col.Gold or Col.Text)
	n.Position = UDim2.fromOffset(12, 4); n.Size = UDim2.new(1, -24, 0, 24)
	local flags = {}
	if P.Level == 2 then table.insert(flags, `<font color="#e2b75c">OWNER</font>`) elseif P.Level == 1 then table.insert(flags, `<font color="#e2b75c">STAFF</font>`) end
	if P.Muted then table.insert(flags, `MUTED`) end
	if P.Frozen then table.insert(flags, `FROZEN`) end
	if P.God then table.insert(flags, `GOD`) end
	if P.Note then table.insert(flags, `<font color="#e2b75c">NOTE</font>`) end
	if P.InMenu then table.insert(flags, `IN MENU`) end
	if table.find(State.Recent, P.UserId) then table.insert(flags, `<font color="#9a8f80">recent</font>`) end
	local sub = label(B, `{tostring(P.Sub or P.Race)}{if P.Tier then ` ` .. (({ `I`, `II`, `III` })[P.Tier] or ``) else ``}{if P.Height then `  ·  {P.Height}` else ``}  ·  {P.Health}/{P.MaxHealth} HP  ·  {P.Ping} ms  {table.concat(flags, `  `)}`, 14, Col.TextDim)
	sub.Position = UDim2.fromOffset(12, 30); sub.Size = UDim2.new(1, -24, 0, 20)
	B.Activated:Connect(function()
		State.Selected = P.UserId
		-- QOL: the last five students you picked float to the top
		local i = table.find(State.Recent, P.UserId)
		if i then table.remove(State.Recent, i) end
		table.insert(State.Recent, 1, P.UserId)
		while #State.Recent > 5 do table.remove(State.Recent) end
		Shared.RenderPlayers()
		Shared.RenderTab()
	end)
end

function Shared.RenderPlayers()
	if not (Ui and State.Info) then return end
	local L = Ui.PlayerList
	for _, c in L:GetChildren() do if c:IsA(`GuiObject`) then c:Destroy() end end
	local f = State.Filter:lower()
	local n = 0
	for i, P in State.Info.Players do
		if f == `` or P.Name:lower():find(f, 1, true) or P.Display:lower():find(f, 1, true) or tostring(P.UserId) == f then
			n += 1
			local r = table.find(State.Recent, P.UserId)
			playerRow(L, P, if r then r else 10 + i)
		end
	end
	Ui.Count.Text = `{n} / {#State.Info.Players} students`
end

local function selectedName(): string
	if not (State.Selected and State.Info) then return `nobody` end
	for _, P in State.Info.Players do if P.UserId == State.Selected then return P.Display end end
	return `nobody`
end

-- (audit) the Server tab's lines and staff log and the Spawns count, shared by the build and the 3 s refresh
local function serverLines(): (string, string)
	local s = State.Info and State.Info.Server or {}
	return `Students <b>{s.Players or 0}/{s.MaxPlayers or 0}</b>   ·   Uptime <b>{math.floor((s.Uptime or 0) / 60)} min</b>   ·   Physics <b>{s.Fps or 0} fps</b>   ·   Memory <b>{s.Memory or 0} MB</b>`,
		`Clock <b>{s.Clock or `?`}</b>   ·   Enemies <b>{s.Enemies or 0}</b>   ·   Wolves <b>{s.Wolves or 0}</b>   ·   Server <font color="#9a8f80">{s.JobId or ``}</font>`
end

local function logKey(): string
	local L = State.Info and State.Info.Log or {}
	local Last = L[#L]
	return `{#L}:{L[1] and L[1].T or 0}:{Last and Last.T or 0}:{Last and Last.Command or ``}`
end

local function fillLog(lg: Instance)
	for _, c in lg:GetChildren() do if c:IsA(`GuiObject`) then c:Destroy() end end
	for i, e in (State.Info and State.Info.Log or {}) do
		local when = os.date(`%H:%M:%S`, e.T)
		label(lg, `<font color="#9a8f80">{when}</font>  <b>{e.Admin}</b>  {e.Command}  {e.Target}  <font color="#9a8f80">{e.Detail}</font>`, 16, Col.Text, i)
	end
	if not State.Info or #State.Info.Log == 0 then label(lg, `Nothing yet.`, 16, Col.TextDim, 1) end
end

local function aliveText(): string
	return `Alive now: {State.Info.Server.Enemies} delinquents/AI, {State.Info.Server.Wolves} wolves, {State.Info.Server.Beasts or 0} beasts`
end

function Shared.RenderTab(Into: Instance?, TabIndex: number?)
	if not Ui then return end
	local Body = Into or Ui.Body
	if not Into then table.clear(Live) end -- (audit)
	for _, c in Body:GetChildren() do if c:IsA(`GuiObject`) then c:Destroy() end end
	local tab = TABS[TabIndex or State.Tab]
	if not Into then
		Ui.Target.Text = `Target: <b>{selectedName()}</b>`
		Ui.UserId.Text = if State.Selected then tostring(State.Selected) else ``
	end
	local o = 0
	local function nxt() o += 1 return o end

	-- favourites: the buttons you right-clicked, on every tab
	if not Into and next(Favs) then
		header(Body, `Favourites`, nxt())
		local fg = grid(Body, nxt())
		local names = {}
		for n in Favs do table.insert(names, n) end
		table.sort(names)
		Rendering = 0 -- (pinned copies are not indexed again)
		for i, n in names do button(fg, n, Favs[n].OnClick, Favs[n].Style, nil, i) end
	end
	Rendering = TabIndex or State.Tab

	if tab == `Moderation` then
		header(Body, `Discipline a student`, nxt())
		local row = frame(Body, UDim2.new(1, 0, 0, 40), nxt()); list(row, 10, true)
		local reason = field(row, `Reason (shown to them)`, 420, 1)
		local days = field(row, `Ban days (0 = forever)`, 220, 2)
		local g = grid(Body, nxt())
		button(g, `Warn`, function() run(`Warn`, true, { Reason = reason.Text }) end, `gold`)
		button(g, `Mute`, function() run(`Mute`, true) end)
		button(g, `Unmute`, function() run(`Unmute`, true) end)
		button(g, `Freeze / Thaw`, function() run(`Freeze`, true) end)
		button(g, `Send to Detention`, function() run(`Jail`, true) end)
		button(g, `Spectate`, function() run(`Spectate`, true) end)
		button(g, `Kick`, function() run(`Kick`, true, { Reason = reason.Text }) end, `crimson`)
		button(g, `Ban`, function() run(`Ban`, true, { Reason = reason.Text; Days = days.Text }) end, `crimson`)
		header(Body, `Everyone`, nxt())
		local ge = grid(Body, nxt())
		button(ge, `Bring everyone`, function() run(`BringAll`) end, `gold`)
		button(ge, `Freeze everyone`, function() run(`FreezeAll`, false, { On = true }) end)
		button(ge, `Thaw everyone`, function() run(`FreezeAll`, false, { On = false }) end)
		header(Body, `Staff note (seen by staff in this server)`, nxt())
		local rown = frame(Body, UDim2.new(1, 0, 0, 40), nxt()); list(rown, 10, true)
		local note = field(rown, `Note on the selected student (empty clears it)`, 520, 1)
		button(rown, `Save note`, function() run(`Note`, true, { Text = note.Text }) end, `gold`, 160, 2)
		header(Body, `Lift a ban`, nxt())
		local row2 = frame(Body, UDim2.new(1, 0, 0, 40), nxt()); list(row2, 10, true)
		local uid = field(row2, `UserId`, 300, 1)
		button(row2, `Unban`, function() run(`Unban`, false, { UserId = uid.Text }) end, `gold`, 160, 2)
	elseif tab == `Student` then
		header(Body, `Body`, nxt())
		local g = grid(Body, nxt())
		button(g, `Heal`, function() run(`Heal`, true) end, `gold`)
		button(g, `Revive`, function() run(`Revive`, true) end, `gold`)
		button(g, `God mode`, function() run(`God`, true) end)
		button(g, `Transform`, function() run(`Transform`, true) end)
		button(g, `Bring here`, function() run(`Bring`, true) end)
		button(g, `Go to`, function() run(`Goto`, true) end)
		button(g, `Clear record`, function() run(`ClearDiscipline`, true) end)
		button(g, `Kill`, function() run(`Kill`, true) end, `crimson`)
		local sp = Kit.Slider({ label = `Walk speed`; min = 0; max = 120; step = 1; value = 16; format = function(v) return tostring(math.floor(v)) end;
			onReleased = function(v) run(`Speed`, true, { Value = v }) end })
		sp.Size = UDim2.new(1, 0, 0, 40); sp.LayoutOrder = nxt(); sp.Parent = Body
		-- (height, 1.63) re-roll or set the selected student's height (in their race's range)
		header(Body, `Height`, nxt())
		local gh = grid(Body, nxt())
		button(gh, `Spin height`, function() run(`SpinHeight`, true) end, `gold`)
		button(gh, `Shortest`, function() run(`SetHeight`, true, { Pick = `Shortest` }) end)
		button(gh, `Average`, function() run(`SetHeight`, true, { Pick = `Average` }) end)
		button(gh, `Tallest`, function() run(`SetHeight`, true, { Pick = `Tallest` }) end)
		-- (body types, 2026-11-10) the selected student's build: Average or a training build and step (saved)
		header(Body, `Build`, nxt())
		local gb = grid(Body, nxt())
		for _, Bd in { { `Average`, `Average`, 0 }, { `Skinny`, `Skinny`, 1 }, { `Conditioned I`, `Conditioned`, 1 },
			{ `Conditioned II`, `Conditioned`, 2 }, { `Heavy I`, `Heavy`, 1 }, { `Heavy II`, `Heavy`, 2 } } do
			button(gb, Bd[1], function() run(`SetBuild`, true, { Build = Bd[2], Step = Bd[3] }) end)
		end
		-- (race, 1.65) every race and variant, and tiers I to III (the server checks and saves through Lineage)
		local function raceButtons(Target: number?)
			local okL, L = pcall(require, ReplicatedStorage:WaitForChild(`Lineage`))
			if not okL then return end
			local gr = grid(Body, nxt())
			for _, R in L.Races do
				for _, S in R.Subs do
					button(gr, S.Name, function() run(`SetRace`, true, { Sub = S.Id }, Target) end, if S.Id == R.Id then `gold` else nil)
				end
			end
		end
		local function tierButtons(Target: number?)
			local gt = grid(Body, nxt())
			for T, Name in { `Tier I`, `Tier II`, `Tier III` } do
				button(gt, Name, function() run(`SetTier`, true, { Tier = T }, Target) end, if T == 3 then `gold` else nil)
			end
		end
		header(Body, `Race (gold: the base race, then its variants)`, nxt())
		raceButtons(nil)
		header(Body, `Tier`, nxt())
		tierButtons(nil)
		header(Body, `Rewards`, nxt())
		local row = frame(Body, UDim2.new(1, 0, 0, 40), nxt()); list(row, 10, true)
		local amt = field(row, `Amount`, 200, 1)
		button(row, `Give Yen`, function() run(`GiveYen`, true, { Amount = amt.Text }) end, `gold`, 160, 2)
		button(row, `Give Combat EXP`, function() run(`GiveExp`, true, { Amount = amt.Text; Category = `Combat` }) end, `gold`, 200, 3)
		button(row, `Lineage spins`, function() run(`GiveSpins`, true, { Amount = amt.Text }) end, nil, 170, 4)
		local row2 = frame(Body, UDim2.new(1, 0, 0, 40), nxt()); list(row2, 10, true)
		button(row2, `Name change`, function() run(`GiveNameChange`, true) end, nil, 170, 1)
		header(Body, `Give gear`, nxt())
		local gs = scroll(Body, UDim2.new(1, 0, 0, 150), nxt())
		local gg = Instance.new(`UIGridLayout`); gg.CellSize = UDim2.fromOffset(178, 36); gg.CellPadding = UDim2.fromOffset(8, 8); gg.SortOrder = Enum.SortOrder.LayoutOrder; gg.Parent = gs
		for i, it in (State.Info and State.Info.Gear or {}) do
			local b = button(gs, it.Name, function() run(`GiveGear`, true, { Id = it.Id }) end, nil, 178, i)
			local rc = Theme.Rarity and Theme.Rarity[it.Rarity]
			if typeof(rc) == `Color3` then b:FindFirstChildWhichIsA(`TextLabel`, true).TextColor3 = rc end
		end
	elseif tab == `School` then
		local L = State.Info and State.Info.Lists or {}
		header(Body, `Discipline record`, nxt())
		local row = frame(Body, UDim2.new(1, 0, 0, 40), nxt()); list(row, 10, true)
		local pts = field(row, `Points (0-100)`, 200, 1)
		button(row, `Set points`, function() run(`SetDisciplinePoints`, true, { Value = pts.Text }) end, `gold`, 160, 2)
		local g = grid(Body, nxt())
		button(g, `Excuse today`, function() run(`ExcuseToday`, true) end, `gold`)
		button(g, `Lift suspension`, function() run(`LiftSuspension`, true) end)
		button(g, `Clear detention`, function() run(`ClearDetention`, true) end)
		button(g, `Owe detention`, function() run(`OweDetention`, true) end)
		button(g, `Clear record`, function() run(`ClearDiscipline`, true) end)
		button(g, `Send to Detention`, function() run(`Jail`, true) end)
		label(Body, `Excuse today turns today's absences into excused ones and takes their points back off.`, 15, Col.TextDim, nxt())
		header(Body, `Start a lesson for them`, nxt())
		local g2 = grid(Body, nxt(), 140)
		for _, room in L.Rooms or {} do button(g2, `Room {room:sub(2)}`, function() run(`StartLesson`, true, { Room = room }) end, nil, 140) end
		header(Body, `Skip to a period`, nxt())
		local g3 = grid(Body, nxt(), 150)
		for _, seg in L.Segments or {} do button(g3, seg, function() run(`SkipToPeriod`, false, { Segment = seg }) end, nil, 150) end
		label(Body, `Moving the clock can mark students in school absent for the classes it skips; Excuse today clears that.`, 15, Col.TextDim, nxt())
		local g4 = grid(Body, nxt())
		button(g4, `Ring the bell`, function() run(`RingBell`) end, `gold`)
	elseif tab == `Progress` then
		header(Body, `Level and stats`, nxt())
		local row = frame(Body, UDim2.new(1, 0, 0, 40), nxt()); list(row, 10, true)
		local v = field(row, `Number`, 160, 1)
		button(row, `Set level`, function() run(`SetLevel`, true, { Value = v.Text }) end, `gold`, 150, 2)
		button(row, `Set stat points`, function() run(`SetStatPoints`, true, { Value = v.Text }) end, nil, 180, 3)
		local row2 = frame(Body, UDim2.new(1, 0, 0, 40), nxt()); list(row2, 10, true)
		local e = field(row2, `EXP amount`, 160, 1)
		for i, cat in { `Class`, `Quest`, `Social`, `Sport` } do
			button(row2, `+ {cat} EXP`, function() run(`GiveExp`, true, { Amount = e.Text; Category = cat }) end, nil, 150, i + 1)
		end
		header(Body, `Titles`, nxt())
		local row3 = frame(Body, UDim2.new(1, 0, 0, 40), nxt()); list(row3, 10, true)
		local t = field(row3, `Title (e.g. Explorer)`, 300, 1)
		button(row3, `Grant title`, function() run(`GrantTitle`, true, { Title = t.Text }) end, `gold`, 160, 2)
		button(row3, `Remove title`, function() run(`RemoveTitle`, true, { Title = t.Text }) end, nil, 170, 3)
		header(Body, `Places found (regions)`, nxt())
		local g = grid(Body, nxt())
		button(g, `Found every place`, function() run(`RegionsAll`, true) end, `gold`)
		button(g, `Reset places`, function() run(`RegionsReset`, true) end)
		header(Body, `Inspector (their loaded slot, read-only)`, nxt())
		local box = frame(Body, UDim2.new(1, 0, 0, 0), nxt()); box.AutomaticSize = Enum.AutomaticSize.Y; list(box, 2)
		if not State.Selected then
			label(box, `Pick a student on the left.`, 16, Col.TextDim, 1)
		elseif not Into then -- (not while the search index builds tabs off screen)
			label(box, `Loading...`, 16, Col.TextDim, 1)
			local want = State.Selected
			task.spawn(function()
				local F = remotes()
				local ok, r = pcall(function() return F and F:FindFirstChild(`Inspect`) and F.Inspect:InvokeServer(want) end)
				if not box.Parent or State.Selected ~= want then return end
				for _, ch in box:GetChildren() do if ch:IsA(`GuiObject`) then ch:Destroy() end end
				if not (ok and typeof(r) == `table`) then label(box, `No record loaded for them.`, 16, Col.Danger, 1) return end
				local function line(i, k, v) label(box, `<font color="#9a8f80">{k}</font>  {v}`, 16, Col.Text, i) end
				local st = r.Stats or {}
				local d = r.Discipline or {}
				local a = r.Attendance or {}
				line(1, `Student`, `<b>{r.Name}</b>  ·  UserId {r.UserId}  ·  slot {tostring(r.Slot)}  ·  {tostring(r.Race or `?`)}`)
				line(2, `Progress`, `level {tostring(r.Level)}  ·  {tostring(r.Exp)} EXP  ·  {tostring(r.Points)} stat points  ·  Might {st.Might or 0}, Grit {st.Grit or 0}, Wits {st.Wits or 0}`)
				line(3, `Money`, `¥{r.Yen}  ·  {r.Kills} kills`)
				line(4, `Discipline`, `{tostring(d.Points)} points ({tostring(d.Level)})  ·  owes {tostring(d.Owed)} detention(s){if (d.Suspended or -1) >= 0 then `  ·  suspended until day {d.Suspended}` else ``}{if (d.Probation or -1) >= 0 then `  ·  probation until day {d.Probation}` else ``}`)
				line(5, `Attendance`, `present {a.Present or 0}  ·  absent {a.Absent or 0}  ·  tardy {a.Tardy or 0}  ·  excused {a.Excused or 0}`)
				line(6, `Titles`, if #r.Titles > 0 then table.concat(r.Titles, `, `) .. (if r.Title ~= `` then `  (wearing {r.Title})` else ``) else `none`)
				line(7, `Places`, `{r.Regions} / {r.RegionsTotal} found  ·  club {if r.Club ~= `` then r.Club else `none`}`)
				line(8, `Quests`, if #r.Quests > 0 then table.concat(r.Quests, `, `) else `none active`)
				local ar = {}
				for k, n in r.Arcade or {} do table.insert(ar, `{k} {n}`) end
				line(9, `Phone games`, if #ar > 0 then table.concat(ar, `  ·  `) else `no scores yet`)
				if r.Note then line(10, `Staff note`, `{r.Note.Text}  <font color="#9a8f80">({r.Note.By})</font>`) end
			end)
		end
	elseif tab == `Activities` then
		local L = State.Info and State.Info.Lists or {}
		header(Body, `Matches (the selected student plays a solo test match)`, nxt())
		for i, venue in L.Venues or {} do
			local r = frame(Body, UDim2.new(1, 0, 0, 40), nxt()); list(r, 10, true)
			label(r, `<b>{venue}</b>`, 18, Col.Text, 1).Size = UDim2.fromOffset(170, 40)
			button(r, `Start ({venue})`, function() run(`MatchStart`, true, { Venue = venue }) end, `gold`, 220, 2)
			button(r, `End ({venue})`, function() run(`MatchEnd`, false, { Venue = venue }) end, `crimson`, 200, 3)
		end
		header(Body, `Clubs`, nxt())
		local g = grid(Body, nxt(), 200)
		for _, c in L.Clubs or {} do button(g, c.Name, function() run(`SetClub`, true, { Club = c.Id }) end, nil, 200) end
		button(g, `Leave club`, function() run(`SetClub`, true, { Club = `` }) end, nil, 200)
		header(Body, `Quests`, nxt())
		local qs = scroll(Body, UDim2.new(1, 0, 0, 200), nxt()); list(qs, 6)
		for i, q in L.Quests or {} do
			local r = frame(qs, UDim2.new(1, -10, 0, 40), i); list(r, 10, true)
			label(r, q.Name, 17, Col.Text, 1).Size = UDim2.fromOffset(300, 40)
			button(r, `Start`, function() run(`QuestStart`, true, { Id = q.Id }) end, `gold`, 110, 2)
			button(r, `Drop`, function() run(`QuestAbandon`, true, { Id = q.Id }) end, nil, 110, 3)
		end
		local g2 = grid(Body, nxt())
		button(g2, `Reset all their quests`, function() run(`QuestReset`, true) end, `crimson`, 230)
	elseif tab == `World` then
		local L = State.Info and State.Info.Lists or {}
		header(Body, `School clock`, nxt())
		local row = frame(Body, UDim2.new(1, 0, 0, 40), nxt()); list(row, 10, true)
		local t = field(row, `HH:MM`, 160, 1)
		button(row, `Set time`, function() run(`SetTime`, false, { Time = t.Text }) end, `gold`, 150, 2)
		button(row, `Morning`, function() run(`SetTime`, false, { Time = `07:30` }) end, nil, 130, 3)
		button(row, `Noon`, function() run(`SetTime`, false, { Time = `12:00` }) end, nil, 110, 4)
		button(row, `Midnight`, function() run(`SetTime`, false, { Time = `00:00` }) end, nil, 130, 5)
		local row1 = frame(Body, UDim2.new(1, 0, 0, 40), nxt()); list(row1, 10, true)
		button(row1, `Full moon tonight`, function() run(`FullMoon`) end, `gold`, 220, 1)
		local sp = Kit.Slider({ label = `Seconds per game hour`; min = 2; max = 600; step = 1; value = 60; format = function(v) return tostring(math.floor(v)) .. ` s` end;
			onReleased = function(v) run(`ClockSpeed`, false, { Value = v }) end })
		sp.Size = UDim2.new(1, 0, 0, 40); sp.LayoutOrder = nxt(); sp.Parent = Body
		header(Body, `Go to a place`, nxt())
		local send = Kit.Toggle({ value = State.SendTarget == true; onChanged = function(v) State.SendTarget = v end })
		local sr = frame(Body, UDim2.new(1, 0, 0, 40), nxt()); list(sr, 12, true)
		send.LayoutOrder = 1; send.Parent = sr
		label(sr, `<b>Send the selected student</b>  <font color="#9a8f80">instead of going yourself</font>`, 17, Col.Text, 2).Size = UDim2.new(1, -110, 1, 0)
		local g = grid(Body, nxt(), 200)
		for _, r in L.Regions or {} do
			button(g, r.Name, function() run(`GotoRegion`, false, { Id = r.Id; Send = State.SendTarget == true; Target = State.Selected }) end, nil, 200)
		end
		header(Body, `Announcement`, nxt())
		local row2 = frame(Body, UDim2.new(1, 0, 0, 40), nxt()); list(row2, 10, true)
		local msg = field(row2, `Message to every student`, 520, 1)
		button(row2, `Announce`, function() run(`Announce`, false, { Text = msg.Text }) end, `gold`, 160, 2)
		header(Body, `Server`, nxt())
		local row3 = frame(Body, UDim2.new(1, 0, 0, 40), nxt()); list(row3, 10, true)
		button(row3, if State.Info and State.Info.Locked then `Unlock server` else `Lock server`, function() run(`ServerLock`) end, nil, 180, 1)
		local why = field(row3, `Reason`, 300, 2)
		button(row3, `Shut down server`, function() run(`Shutdown`, false, { Reason = why.Text }) end, `crimson`, 220, 3)
	elseif tab == `Spawns` then
		header(Body, `Enemies`, nxt())
		local g = grid(Body, nxt(), 230)
		button(g, `Delinquent crew`, function() run(`SpawnDelinquents`) end, `gold`, 230)
		button(g, `Wolf pack (night)`, function() run(`SpawnWolves`) end, `gold`, 230)
		-- (beasts) one of each beast, in front of you, any time of day
		for _, Bst in (State.Info and State.Info.Lists and State.Info.Lists.Beasts) or {} do
			local Id = if typeof(Bst) == `table` then Bst.Id else Bst
			local Label = if typeof(Bst) == `table` then Bst.Name else Bst
			button(g, `Beast: {Label}`, function() run(`SpawnBeast`, false, { Beast = Id }) end, `gold`, 230)
		end
		for _, Tier in { `Easy`, `Normal`, `Hard`, `Nightmare` } do
			button(g, `Sparring: {Tier}`, function() run(`SpawnSparring`, false, { Tier = Tier }) end, if Tier == `Nightmare` then `crimson` else nil, 230)
		end
		button(g, `Clear all enemies`, function() run(`ClearEnemies`) end, `crimson`, 230)
		if State.Info then
			local alive = label(Body, aliveText(), 17, Col.TextDim, nxt())
			if not Into then Live.Alive = alive end -- (audit) the refresh updates this label in place
		end
	elseif tab == `Self` then
		header(Body, `Your tools`, nxt())
		local function toggleRow(Text: string, Hint: string, Value: boolean, On: (boolean) -> ())
			local r = frame(Body, UDim2.new(1, 0, 0, 40), nxt()); list(r, 12, true)
			local tg = Kit.Toggle({ value = Value; onChanged = On }); tg.LayoutOrder = 1; tg.Parent = r
			local l = label(r, `<b>{Text}</b>  <font color="#9a8f80">{Hint}</font>`, 18); l.Size = UDim2.new(1, -110, 1, 0); l.LayoutOrder = 2
		end
		toggleRow(`Fly`, `WASD, Space up, Ctrl down, Shift faster`, Tools.Fly, setFly)
		toggleRow(`Noclip`, `walk through walls`, Tools.Noclip, setNoclip)
		toggleRow(`ESP`, `names and health through walls`, Tools.Esp, setEsp)
		toggleRow(`Click teleport`, `Ctrl + click a spot`, Tools.ClickTp, setClickTp)
		local g = grid(Body, nxt())
		button(g, `Invisible`, function() run(`Invisible`) end)
		button(g, `Heal me`, function() run(`Heal`, true, nil, Player.UserId) end, `gold`) -- (audit) no longer changes the selected student
		button(g, `Spin my height`, function() run(`SpinHeight`, true, nil, Player.UserId) end) -- (height, 1.63)
		button(g, `Stop spectating`, function()
			local _, H = root()
			if H then workspace.CurrentCamera.CameraSubject = H end
			Shared.Status(`Camera back on you`)
		end)
		-- (race, 1.65) every race and variant, and tiers I to III (the server checks and saves through Lineage)
		local function raceButtons(Target: number?)
			local okL, L = pcall(require, ReplicatedStorage:WaitForChild(`Lineage`))
			if not okL then return end
			local gr = grid(Body, nxt())
			for _, R in L.Races do
				for _, S in R.Subs do
					button(gr, S.Name, function() run(`SetRace`, true, { Sub = S.Id }, Target) end, if S.Id == R.Id then `gold` else nil)
				end
			end
		end
		local function tierButtons(Target: number?)
			local gt = grid(Body, nxt())
			for T, Name in { `Tier I`, `Tier II`, `Tier III` } do
				button(gt, Name, function() run(`SetTier`, true, { Tier = T }, Target) end, if T == 3 then `gold` else nil)
			end
		end
		header(Body, `My race`, nxt())
		raceButtons(Player.UserId)
		header(Body, `My tier`, nxt())
		tierButtons(Player.UserId)
	elseif tab == `Server` then
		header(Body, `This server`, nxt())
		-- (audit) built once; the 3 s refresh updates these labels and the log in place (Shared.Refresh)
		local l1, l2 = serverLines()
		local stats = label(Body, l1, 18, Col.Text, nxt())
		local clock = label(Body, l2, 16, Col.TextDim, nxt())
		header(Body, `Staff log`, nxt())
		local lg = scroll(Body, UDim2.new(1, 0, 0, 300), nxt()); list(lg, 2)
		fillLog(lg)
		if not Into then Live.Stats, Live.Clock, Live.Log, Live.LogKey = stats, clock, lg, logKey() end
	end
	Rendering = 0

	-- the command search jumped here: scroll to the button and ring it in gold for a moment
	local want = if Into then nil else State.Jump
	if want then
		State.Jump = nil
		task.defer(function()
			local B = Body:FindFirstChild(want, true)
			if not (B and B:IsA(`GuiObject`)) then return end
			Body.CanvasPosition = Vector2.new(0, math.max(0, B.AbsolutePosition.Y - Body.AbsolutePosition.Y + Body.CanvasPosition.Y - 60))
			local St = Instance.new(`UIStroke`)
			St.Color = Col.Gold
			St.Thickness = 3
			St.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
			St.Parent = B
			task.delay(1.8, function() St:Destroy() end)
		end)
	end
end

-- the command search's index: build every tab once, off screen, and note each button's label and tab
function Shared.BuildIndex()
	if not Ui then return end
	table.clear(Index)
	local Scratch = Instance.new(`Frame`)
	Scratch.Visible = false
	Scratch.Parent = Ui.Gui
	list(Scratch, 2)
	Indexing = true
	for i in TABS do pcall(Shared.RenderTab, Scratch, i) end
	Indexing = false
	Rendering = 0
	Scratch:Destroy()
end

function Shared.Search(Text: string)
	if not Ui then return end
	local R = Ui.Results
	for _, c in R:GetChildren() do if c:IsA(`GuiObject`) then c:Destroy() end end
	local q = Text:lower()
	if q == `` then R.Visible = false return end
	local n, seen = 0, {}
	for _, e in Index do
		local key = e.Label .. e.Tab
		if not seen[key] and e.Label:lower():find(q, 1, true) then
			seen[key] = true
			n += 1
			if n > 10 then break end
			local B = Instance.new(`TextButton`)
			B.Size = UDim2.new(1, 0, 0, 32)
			B.BackgroundColor3 = Col.Well
			B.BackgroundTransparency = 0.05
			B.BorderSizePixel = 0
			B.AutoButtonColor = true
			B.RichText = true
			B.Font = Theme.Fonts.Body
			B.TextSize = 17
			B.TextColor3 = Col.Text
			B.TextXAlignment = Enum.TextXAlignment.Left
			B.Text = `   <b>{e.Label}</b>   <font color="#9a8f80">{TABS[e.Tab]}</font>`
			B.LayoutOrder = n
			B.ZIndex = 31
			B.Parent = R
			B.Activated:Connect(function()
				R.Visible = false
				Ui.SearchApi:Set(``)
				State.Tab = e.Tab
				State.Jump = e.Label
				Ui.TabsApi:Select(e.Tab, true)
				Shared.RenderTab()
			end)
		end
	end
	if n == 0 then label(R, `   No command called that`, 16, Col.TextDim, 1).ZIndex = 31 end
	R.Visible = true
end

function Shared.Status(Text: string, Bad: boolean?)
	if not Ui then return end
	Ui.Status.Text = Text
	Ui.Status.TextColor3 = Bad and Col.Danger or Col.Gold
end

function Shared.Refresh()
	if not (Ui and Ui.Panel.Visible) then return end
	local r = info()
	if not r then return end
	State.Info = r
	State.Level = r.Level
	Shared.RenderPlayers()
	-- (audit) no rebuild any more (it reset crimson confirms and the log's scroll): update the live labels in place
	if TABS[State.Tab] == `Spawns` and Live.Alive and Live.Alive.Parent then Live.Alive.Text = aliveText() end
	if TABS[State.Tab] == `Server` and Live.Stats and Live.Stats.Parent then
		local l1, l2 = serverLines()
		Live.Stats.Text, Live.Clock.Text = l1, l2
		local k = logKey()
		if Live.Log and Live.Log.Parent and k ~= Live.LogKey then Live.LogKey = k fillLog(Live.Log) end
	end
end

local function build()
	local Gui = Instance.new(`ScreenGui`)
	Gui.Name = `NHAdminPanel`
	Gui.ResetOnSpawn = false
	Gui.DisplayOrder = 40
	Gui.IgnoreGuiInset = true
	Gui.Parent = Player:WaitForChild(`PlayerGui`)
	Kit.AutoScale(Gui)
	local Panel, Api = Kit.Panel({ title = `Headmaster's Desk`; Name = `Panel`; AnchorPoint = Vector2.new(0.5, 0.5);
		Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromOffset(1240, 720); Visible = false; Parent = Gui })
	local C = Api.Content

	-- left column: crest, search, students
	local Left = frame(C, UDim2.new(0, 330, 1, 0)); list(Left, 8)
	local Top = frame(Left, UDim2.new(1, 0, 0, 72), 1); list(Top, 10, true)
	local crest = Instance.new(`ImageLabel`); crest.BackgroundTransparency = 1; crest.Image = Theme.Images.Crest
	crest.Size = UDim2.fromOffset(72, 72); crest.ScaleType = Enum.ScaleType.Fit; crest.LayoutOrder = 1; crest.Parent = Top
	local tl = frame(Top, UDim2.new(1, -82, 1, 0), 2); list(tl, 0)
	label(tl, `<b>STAFF ONLY</b>`, 20, Col.Gold, 1)
	local Count = label(tl, ``, 16, Col.TextDim, 2)
	local Search, SApi = Kit.SearchBar({ placeholder = `Search students`; onChanged = function(t) State.Filter = t Shared.RenderPlayers() end })
	Search.Size = UDim2.new(1, 0, 0, 40); Search.LayoutOrder = 2; Search.Parent = Left
	local PlayerList = scroll(Left, UDim2.new(1, 0, 1, -170), 3); list(PlayerList, 6)

	-- right column: target line, tabs, body, status
	local Right = frame(C, UDim2.new(1, -350, 1, 0)); Right.Position = UDim2.fromOffset(350, 0); list(Right, 8)
	local TopRow = frame(Right, UDim2.new(1, 0, 0, 40), 1); list(TopRow, 10, true)
	local Target = label(TopRow, ``, 20, Col.Text, 1)
	Target.Size = UDim2.new(1, -560, 1, 0)
	-- QOL: the selected student's UserId, selectable so you can copy it (Ctrl+C)
	local Uid = Instance.new(`TextBox`)
	Uid.Name = `UserId`
	Uid.Size = UDim2.fromOffset(170, 34)
	Uid.BackgroundColor3 = Col.Well
	Uid.BorderSizePixel = 0
	Uid.Font = Theme.Fonts.Body
	Uid.TextSize = 16
	Uid.TextColor3 = Col.TextDim
	Uid.PlaceholderText = `UserId`
	Uid.Text = ``
	Uid.TextEditable = false
	Uid.ClearTextOnFocus = false
	Uid.LayoutOrder = 2
	Uid.Parent = TopRow
	local Search, SearchApi = Kit.SearchBar({ placeholder = `Find a command`; onChanged = function(t) Shared.Search(t) end })
	Search.Size = UDim2.fromOffset(360, 40); Search.LayoutOrder = 3; Search.Parent = TopRow
	local Results = scroll(Right, UDim2.fromOffset(360, 330), 0)
	Results.Name = `Results`
	Results.AnchorPoint = Vector2.new(1, 0)
	Results.Visible = false
	Results.ZIndex = 30
	Results.BackgroundTransparency = 0.02
	Results.BackgroundColor3 = Col.Ink
	list(Results, 2)
	local Tabs, TabsApi = Kit.TabBar({ tabs = TABS; selected = 1; textSize = 16; onChanged = function(i) State.Tab = i Shared.RenderTab() end })
	Tabs.LayoutOrder = 2; Tabs.Parent = Right
	local Body = scroll(Right, UDim2.new(1, 0, 1, -150), 3); list(Body, 10)
	local pad = Instance.new(`UIPadding`); pad.PaddingRight = UDim.new(0, 12); pad.PaddingTop = UDim.new(0, 4); pad.Parent = Body
	local Status = label(Right, `F3 closes the desk`, 17, Col.Gold, 4)

	local close = Kit.Button({ text = `Close`; style = `ghost`; textSize = 16; onClick = function() Shared.Toggle(false) end })
	close.Size = UDim2.fromOffset(96, 32); close.AnchorPoint = Vector2.new(1, 0); close.Position = UDim2.new(1, -28, 0, 26); close.ZIndex = 20; close.Parent = Panel

	-- the results float over the tabs, under the search box (outside the column's list layout)
	Results.Parent = Panel
	Results.Position = UDim2.new(1, -40, 0, 128)
	Ui = { Gui = Gui; Panel = Panel; PlayerList = PlayerList; Count = Count; Target = Target; Body = Body; Status = Status;
		UserId = Uid; Results = Results; SearchApi = SearchApi; TabsApi = TabsApi }
end

function Shared.Toggle(force: boolean?)
	if not remotes() then return end
	if not Ui then build() end
	local open = if force == nil then not Ui.Panel.Visible else force
	if open then
		local r = info()
		if not r then return end -- not staff: nothing opens, no hint that it exists
		State.Info = r
		State.Level = r.Level
		Ui.Panel.Visible = true
		Shared.BuildIndex()
		Shared.RenderPlayers()
		Shared.RenderTab()
	else
		Ui.Panel.Visible = false
	end
end

function Shared.OnStart()
	UserInputService.InputBegan:Connect(function(input, gp)
		if input.KeyCode == Enum.KeyCode.F3 and not gp then Shared.Toggle() end
		if Tools.ClickTp and input.UserInputType == Enum.UserInputType.MouseButton1 and not gp
			and UserInputService:IsKeyDown(Enum.KeyCode.LeftControl) then
			local m = Player:GetMouse()
			if m.Hit then run(`TeleportTo`, false, { Position = m.Hit.Position }) end
		end
	end)
	task.spawn(function()
		local F = ReplicatedStorage:WaitForChild(`NHAdmin`, 60)
		if not F then return end
		F:WaitForChild(`Client`).OnClientEvent:Connect(function(kind, target)
			if kind == `Spectate` and typeof(target) == `Instance` then
				local c = target.Character
				local h = c and c:FindFirstChildWhichIsA(`Humanoid`)
				if h then workspace.CurrentCamera.CameraSubject = h end
			end
		end)
	end)
	task.spawn(function()
		while true do
			task.wait(3)
			pcall(Shared.Refresh)
		end
	end)
	Player.CharacterAdded:Connect(function()
		if Tools.Fly then task.wait(1) setFly(true) end
	end)
	-- other UI (a TopBar button, tests) can open the desk by setting this attribute; the server still decides
	Player:GetAttributeChangedSignal(`NHAdminOpen`):Connect(function()
		local v = Player:GetAttribute(`NHAdminOpen`)
		if v ~= nil then Shared.Toggle(v == true) end
		if typeof(v) == `number` then State.Tab = math.clamp(v, 1, #TABS) Shared.Toggle(true) Shared.RenderTab() end
	end)
end

return Shared
