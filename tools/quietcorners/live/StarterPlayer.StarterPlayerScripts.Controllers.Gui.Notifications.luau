--[[
	Notifications (client)
	Fed by Packets.Notify from the server (unchanged): Data = { Title, Text?, Kind? (Info / Good / Warning / Bad / Milestone),
	Duration?, Open? ("Texts" / "Evidence" / "Journal"), Case?, Quest? }.

	(2.38) Quiet Corners QC1: paper slips, top-left under the top bar (replaces the top-centre Kit.Toast stack and its seal).
	Spec docs/superpowers/specs/2026-11-21-quiet-corners-ui-design.md §3; plan 2026-11-22-quiet-corners-ui.md Task R5.
	- Slip<Race> art (Config.QuietCornersArt), 400 x 80, newest on top, at most QC.MaxSlips (3, or 2 on phones).
	  No id = the kit fallback (Kit.Decorate thin, theme text colours).
	- Queued while HudState.SlipsQueued() (combat, cut, dialogue, lesson, menu) behind one "N waiting" stub; Danger
	  (Kind Bad) breaks through. The queue flushes one slip every 0.6 s once the state allows it.
	- Every slip is clickable (owner's decision 2026-11-22): QC.SlipOpen picks Texts (Phone.OpenApp), Evidence or Journal
	  (QuestJournal.OpenPage); anything else opens the book's Notices page.
	- Shared.History(): the session's last 30 notifications, newest first, full text ({ Title, Text, Kind, Time }).
	- Probes (Studio, through HudState.Probe): Slip(Data), Slips(), History().
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local TextService = game:GetService(`TextService`)
local TweenService = game:GetService(`TweenService`)

---| Modules |---

local Packets = require(ReplicatedStorage.Remotes.Packets)
local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`)) -- NH UI kit
local Theme = Kit.Theme or require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Theme`))
local QC = require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`QuietCorners`)) -- (2.38)
local Art = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`QuietCornersArt`)) -- (2.38)
local HudState = require(script.Parent:WaitForChild(`HudState`)) -- (2.38)

local Player = Players.LocalPlayer

-- (2.38) slip layout, design px (the Slip's text box is QcBox of its 400 x 80 art)
local SLIP_W, SLIP_H = 400, 80
local TEXT_X, TEXT_W = 64, 324
local QC_BOX = `0.14,0.06,0.97,0.78`
-- (2.38) measured on the slip paper for spec §9 (4.5:1 at 22 px and under); InkDim / InkRed darkened from the plan's values
local PAPER = Color3.fromRGB(170, 156, 134) -- the slip's text box, measured
local INK = Color3.fromRGB(40, 22, 16)
local INK_RED = Color3.fromRGB(96, 10, 16)
local INK_DIM = Color3.fromRGB(48, 30, 22)
local HISTORY_MAX = 30
local FLUSH_GAP = 0.6
local STUB_ORDER = 2147483647 -- the stub always sits under the slips

local Local = {}
local Shared = {}

local Holder: Frame? = nil
local Live = {} -- (2.38) shown slips, oldest first: { Slot, Slip, Title, Detail, Data, Gone }
local Queue = {} -- (2.38) Data waiting for the state to allow slips
local History = {} -- (2.38) newest first
local Stub = nil -- (2.38) the "N waiting" record
local Order = 0
local Flushing = false

function Local.Reduced(): boolean return Player:GetAttribute(`NHReducedMotion`) == true end

function Local.Phone(): boolean
	-- (S5) the kit's viewport, so Studio's NHPhonePreview counts (the camera's ViewportSize ignores it)
	if Kit.Viewport then
		local Ok, Vp = pcall(Kit.Viewport)
		if Ok and typeof(Vp) == `Vector2` then return QC.Phone(Vp) end
	end
	local Cam = workspace.CurrentCamera
	return Cam ~= nil and QC.Phone(Cam.ViewportSize)
end

function Local.Fits(Text: string, Size: number, Font: Enum.Font): boolean
	local Ok, V = pcall(TextService.GetTextSize, TextService, Text, Size, Font, Vector2.new(2000, 200))
	return Ok and V.X <= TEXT_W - 2 -- 2 px slack so UIScale rounding never flips TextFits
end

function Local.OneLine(S: any): string
	return (string.gsub(tostring(S or ``), `%s+`, ` `))
end

---| Building (2.38) |---

function Local.Label(Parent: Instance, Name: string, Y: number, Size: number, Font: Enum.Font): TextLabel
	local L = Instance.new(`TextLabel`)
	L.Name = Name
	L.BackgroundTransparency = 1
	L.Position = UDim2.fromOffset(TEXT_X, Y)
	L.Size = UDim2.fromOffset(TEXT_W, 24)
	L.Font = Font
	L.TextSize = Size
	L.TextScaled = false
	L.TextWrapped = false
	L.TextXAlignment = Enum.TextXAlignment.Left
	L.TextYAlignment = Enum.TextYAlignment.Center
	L.ZIndex = 3
	L.Text = ``
	L.Parent = Parent
	return L
end

-- the paper art for the local player's race, or the kit's thin ornate frame when the id isn't uploaded yet
function Local.Skin(Rec)
	local Id = QC.Image(Art, `Slip`, Player:GetAttribute(`Race`))
	local Slip = Rec.Slip
	local Kind = Rec.Data and Rec.Data.Kind
	local Red = Kind == `Bad` or Kind == `Warning`
	if Id then
		Slip.Image = Id
		local Decor = Slip:FindFirstChild(`NHDecor`)
		if Decor then Decor:Destroy() end
		Slip:SetAttribute(`QcBg`, PAPER)
		Rec.Title.TextColor3 = if Red then INK_RED else INK
		if Rec.Detail then Rec.Detail.TextColor3 = INK_DIM end
	else
		Slip.Image = ``
		if not Slip:FindFirstChild(`NHDecor`) then pcall(Kit.Decorate, Slip, { ornament = `thin` }) end
		Slip:SetAttribute(`QcBg`, nil)
		local C = Theme.Colors
		Rec.Title.TextColor3 = if Red and C.Danger then C.Danger else C.Text
		if Rec.Detail then Rec.Detail.TextColor3 = C.TextDim or C.Text end
	end
end

-- a transparent CanvasGroup slot (it carries the fade) holding the Slip ImageButton (it carries the slide)
function Local.Build(Name: string, LayoutOrder: number, WithDetail: boolean)
	local Slot = Instance.new(`CanvasGroup`)
	Slot.Name = Name
	Slot.BackgroundTransparency = 1
	Slot.Size = UDim2.fromOffset(SLIP_W, SLIP_H)
	Slot.LayoutOrder = LayoutOrder
	Slot.GroupTransparency = 0

	local Slip = Instance.new(`ImageButton`)
	Slip.Name = `Slip`
	Slip.BackgroundTransparency = 1
	Slip.AutoButtonColor = false
	Slip.Size = UDim2.fromOffset(SLIP_W, SLIP_H)
	Slip.ScaleType = Enum.ScaleType.Stretch
	Slip.Image = ``
	Slip:SetAttribute(`QcBox`, QC_BOX)
	Slip.Parent = Slot

	local Rec = { Slot = Slot; Slip = Slip; Gone = false }
	Rec.Title = Local.Label(Slip, `Title`, 8, 22, Theme.Fonts.Title)
	if WithDetail then Rec.Detail = Local.Label(Slip, `Detail`, 34, 20, Theme.Fonts.Body) end
	return Rec
end

function Local.CreateGui()
	local Gui = Instance.new(`ScreenGui`)
	Kit.AutoScale(Gui)
	Gui.Name = `Notifications`
	Gui.ResetOnSpawn = false
	Gui.IgnoreGuiInset = true -- (2.38)
	Gui.DisplayOrder = 10

	local H = Instance.new(`Frame`)
	H.Name = `Holder`
	H.AnchorPoint = Vector2.new(0, 0)
	H.Size = UDim2.fromOffset(SLIP_W, 272)
	H.BackgroundTransparency = 1
	H.Parent = Gui

	local Layout = Instance.new(`UIListLayout`)
	Layout.FillDirection = Enum.FillDirection.Vertical
	Layout.SortOrder = Enum.SortOrder.LayoutOrder -- newest = the lowest LayoutOrder, on top
	Layout.HorizontalAlignment = Enum.HorizontalAlignment.Left
	Layout.Padding = UDim.new(0, 8)
	Layout.Parent = H

	Holder = H
	Local.Place()

	Stub = Local.Build(`Stub`, STUB_ORDER, false)
	Stub.Slip.Active = false
	Stub.Data = { Kind = `Info` }
	Stub.Slot.Visible = false
	Local.Skin(Stub)
	Stub.Slot.Parent = H

	Gui.Parent = Player:WaitForChild(`PlayerGui`)
end

-- top-left under the top bar: (24, 80) on desktop, (10, 50) on phones
function Local.Place()
	if not Holder then return end
	Holder.Position = if Local.Phone() then UDim2.fromOffset(10, 50) else UDim2.fromOffset(24, 80)
end

---| Showing (2.38) |---

function Local.Remove(Rec, Secs: number)
	if Rec.Gone then return end
	Rec.Gone = true
	local I = table.find(Live, Rec)
	if I then table.remove(Live, I) end
	Rec.Slip.Active = false
	local T = TweenService:Create(Rec.Slot, TweenInfo.new(Secs, Enum.EasingStyle.Sine), { GroupTransparency = 1 })
	T.Completed:Connect(function() Rec.Slot:Destroy() end)
	T:Play()
end

function Local.Open(Data)
	local Target = QC.SlipOpen(Data)
	if Target == `Texts` then
		local Ok, Phone = pcall(require, script.Parent:FindFirstChild(`Phone`))
		if Ok and typeof(Phone) == `table` and Phone.OpenApp then pcall(Phone.OpenApp, `Texts`) end
		return
	end
	local Ok, Journal = pcall(require, script.Parent:FindFirstChild(`QuestJournal`))
	if not (Ok and typeof(Journal) == `table`) then return end
	local Page, Arg = `Notices`, nil
	if Target == `Evidence` then Page, Arg = `Evidence`, Data.Case
	elseif Target == `Journal` then Page, Arg = `Journal`, Data.Quest end
	if Journal.OpenPage then
		pcall(Journal.OpenPage, Page, Arg)
	elseif Journal.Toggle then
		pcall(Journal.Toggle, true)
	end
end

function Local.Show(Data)
	if not Holder then return end
	while #Live >= QC.MaxSlips(Local.Phone()) do Local.Remove(Live[1], 0.15) end -- the oldest fades out

	Order -= 1
	local Rec = Local.Build(`SlipSlot`, Order, true)
	Rec.Data = Data
	local Title = Local.OneLine(Data.Title)
	local Text = Local.OneLine(Data.Text)
	Rec.Name = Title
	Rec.Title.Text = QC.Ellipsize(Title, function(S) return Local.Fits(S, 22, Theme.Fonts.Title) end)
	Rec.Detail.Text = if Text == `` then `` else QC.Ellipsize(Text, function(S) return Local.Fits(S, 20, Theme.Fonts.Body) end)
	Local.Skin(Rec)
	Rec.Slip.Active = true -- every slip opens something (owner's decision)
	Rec.Slip.Activated:Connect(function()
		if Rec.Gone then return end
		Local.Open(Data)
		Local.Remove(Rec, 0.15)
	end)

	-- entrance: 16 px slide from the left with a 0.18 s fade; Reduce Motion: a 0.2 s fade only
	local Reduced = Local.Reduced()
	Rec.Slot.GroupTransparency = 1
	if not Reduced then Rec.Slip.Position = UDim2.fromOffset(-16, 0) end
	Rec.Slot.Parent = Holder
	table.insert(Live, Rec)
	local Secs = if Reduced then 0.2 else 0.18
	TweenService:Create(Rec.Slot, TweenInfo.new(Secs, Enum.EasingStyle.Sine), { GroupTransparency = 0 }):Play()
	if not Reduced then
		TweenService:Create(Rec.Slip, TweenInfo.new(0.18, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Position = UDim2.fromOffset(0, 0) }):Play()
	end
	pcall(Kit.PlaySound, `Tick`, 0.4) -- the kit has no paper rustle (ruling 5)

	local Dur = tonumber(Data.Duration) or (if Data.Kind == `Milestone` then 6 else 4)
	task.delay(Dur, function() Local.Remove(Rec, if Local.Reduced() then 0.2 else 0.3) end)
end

function Local.UpdateStub()
	if not Stub then return end
	local T = QC.Waiting(#Queue)
	Stub.Title.Text = T
	Stub.Slot.Visible = T ~= ``
end

function Local.Flush()
	if Flushing then return end
	Flushing = true
	task.spawn(function()
		while #Queue > 0 and not HudState.SlipsQueued() do
			Local.Show(table.remove(Queue, 1))
			Local.UpdateStub()
			if #Queue > 0 then task.wait(FLUSH_GAP) end
		end
		Flushing = false
		Local.UpdateStub()
	end)
end

function Local.Record(Data)
	table.insert(History, 1, {
		Title = tostring(Data.Title or ``); Text = tostring(Data.Text or ``); Kind = Data.Kind; Time = os.time();
	})
	while #History > HISTORY_MAX do table.remove(History) end
end

function Local.Push(Data)
	if typeof(Data) ~= `table` then return end
	Local.Record(Data)
	if HudState.SlipsQueued() and not QC.Danger(Data.Kind) then
		table.insert(Queue, Data)
		Local.UpdateStub()
		return
	end
	Local.Show(Data)
end

---| API |---

-- (2.38) the session's last 30 notifications, newest first, at full length (the book's Notices page)
function Shared.History()
	local Out = {}
	for I, E in History do Out[I] = table.clone(E) end
	return Out
end

---| Probes (2.38) |---

HudState.Probe(`Slip`, function(Data) Local.Push(Data) return true end)
HudState.Probe(`Slips`, function()
	local Shown = {}
	for I = #Live, 1, -1 do table.insert(Shown, Live[I].Name) end
	local Pos = if Holder then Holder.AbsolutePosition else Vector2.zero
	return { Shown = Shown; Waiting = #Queue; Stub = if Stub then Stub.Title.Text else ``; X = Pos.X; Y = Pos.Y }
end)
HudState.Probe(`History`, function() return Shared.History() end)

function Shared.OnStart()
	Local.CreateGui()
	Packets.Notify.OnClientEvent:Connect(Local.Push)

	-- (2.38) queued slips show once the state allows them
	HudState.Changed.Event:Connect(function()
		if not HudState.SlipsQueued() and #Queue > 0 then Local.Flush() end
		Local.UpdateStub()
	end)

	-- (2.38) re-skin the visible slips when the race changes
	Player:GetAttributeChangedSignal(`Race`):Connect(function()
		for _, Rec in Live do Local.Skin(Rec) end
		if Stub then Local.Skin(Stub) end
	end)

	-- (2.38) desktop / phone placement follows the viewport
	local ViewConn = nil
	local function BindCamera()
		if ViewConn then ViewConn:Disconnect() end
		local Cam = workspace.CurrentCamera
		if Cam then ViewConn = Cam:GetPropertyChangedSignal(`ViewportSize`):Connect(Local.Place) end
		Local.Place()
	end
	workspace:GetPropertyChangedSignal(`CurrentCamera`):Connect(BindCamera)
	BindCamera()
end

return Shared
