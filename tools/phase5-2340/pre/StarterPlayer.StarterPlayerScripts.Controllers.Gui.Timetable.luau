--[[
	Timetable (client). Controllers.Gui.Timetable   (click the clock in the top-right; click again or X to close)
	The whole school day on one card (Config.SchoolSchedule segments, Config.Classes periods):
	  * every segment from Before School to Night: the time, the name, and for classes the subject and room
	  * where you are now: the current segment is lit gold with a bar for how much of it has passed, past ones dim,
	    and a line at the top: "Now: Period 2 · Chemistry · Room 103, ends 9:45 AM" plus what's next
	  * your attendance today on each class you've had (Present / Tardy / Absent / Left early / Excused, and the
	    lesson grade if you played it), from your profile's Attendance.Recent
	  * a detention you owe, if any
	Built from the UI kit (Panel, Bar, Button, Text; Theme colours). Live: it ticks while open.
	API: Toggle(on?), IsOpen()
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local GuiService = game:GetService(`GuiService`)

local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))
local Classes = require(ReplicatedStorage.Config.Classes)
local SchoolTime = require(ReplicatedStorage.Functions.SchoolTime)

local Player = Players.LocalPlayer
local Theme = Kit.Theme
local C = Theme.Colors
local Fonts = Theme.Fonts
local GOOD = Color3.fromRGB(150, 205, 140)
local BAD = Color3.fromRGB(235, 120, 110)
local WARN = Color3.fromRGB(240, 180, 90)
local STATUS = {
	Present = { `Present`, GOOD }; Tardy = { `Tardy`, WARN }; Absent = { `Absent`, BAD };
	LeftEarly = { `Left early`, BAD }; Excused = { `Excused`, C.TextDim };
}
local SHOW = { BeforeSchool = true; Class = true; Passing = true; Break = true; Lunch = true; AfterSchool = true; Evening = true; Night = true }

local Shared = {}
local Local = {}
local Ui = nil
local Rows = {}
local LastKey = nil

function Local.Label(Parent: Instance, Text: string, Size: number, Props)
	local T = Kit.Text({ Text = Text; TextSize = Size; TextColor3 = C.Text; RichText = true; TextXAlignment = Enum.TextXAlignment.Left; Parent = Parent })
	for K, V in Props or {} do T[K] = V end
	return T
end

function Local.State()
	local Clock = ReplicatedStorage:FindFirstChild(`SchoolClock`)
	local Epoch = Clock and Clock:GetAttribute(`Epoch`)
	if not Epoch then return nil end
	return SchoolTime.GetState(Epoch, workspace:GetServerTimeNow())
end

-- your profile, without ever waiting on it
function Local.Profile()
	local Out = nil
	local Done = false
	task.spawn(function()
		local Ok, P = pcall(function()
			return require(Player.PlayerScripts:WaitForChild(`Controllers`):WaitForChild(`StateController`)).GetProfile()
		end)
		if Ok then Out = P end
		Done = true
	end)
	return if Done then Out else nil
end

function Local.Build()
	local G = Instance.new(`ScreenGui`)
	G.Name = `NHTimetable`
	G.ResetOnSpawn = false
	G.DisplayOrder = 12
	G.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	G.Enabled = false
	G.Parent = Player:WaitForChild(`PlayerGui`)
	Kit.AutoScale(G)
	-- 540 wide so the card's left edge stays clear of the health bar; Local.Place drops it below the clock panel
	local Panel, Api = Kit.Panel({ title = `Timetable`; Name = `Panel`; AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -24, 0, 150);
		Size = UDim2.fromOffset(540, 640); Parent = G })
	local B = Api.Content
	local Day = Local.Label(B, ``, 20, { Name = `Day`; Font = Fonts.Title; TextColor3 = C.Gold; Position = UDim2.fromOffset(6, 0); Size = UDim2.new(1, -60, 0, 24) })
	local Now = Local.Label(B, ``, 15, { Name = `Now`; TextWrapped = true; Position = UDim2.fromOffset(6, 26); Size = UDim2.new(1, -12, 0, 40); TextYAlignment = Enum.TextYAlignment.Top })
	Kit.Button({ text = `X`; style = `ghost`; textSize = 16; Size = UDim2.fromOffset(36, 32); AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -2, 0, -4); Parent = B;
		onClick = function() Shared.Toggle(false) end })
	Kit.Divider({ Position = UDim2.fromOffset(6, 68); Size = UDim2.new(1, -12, 0, 14); Parent = B })
	local List = Instance.new(`Frame`)
	List.Name = `List`
	List.BackgroundTransparency = 1
	List.Position = UDim2.fromOffset(0, 86)
	List.Size = UDim2.new(1, 0, 1, -116)
	List.Parent = B
	local L = Instance.new(`UIListLayout`)
	L.SortOrder = Enum.SortOrder.LayoutOrder
	L.Padding = UDim.new(0, 2)
	L.Parent = List
	-- centred and inset, so the frame's bottom corners never cover its first and last letters
	local Foot = Local.Label(B, ``, 13, { Name = `Foot`; TextColor3 = C.TextDim; TextXAlignment = Enum.TextXAlignment.Center;
		TextTruncate = Enum.TextTruncate.AtEnd; Position = UDim2.new(0, 28, 1, -24); Size = UDim2.new(1, -56, 0, 20) })
	Ui = { Gui = G; Panel = Panel; Day = Day; Now = Now; List = List; Foot = Foot }
end

function Local.Render(State)
	if not (Ui and State) then return end
	for _, Ch in Ui.List:GetChildren() do if not Ch:IsA(`UIBase`) then Ch:Destroy() end end
	table.clear(Rows)
	Ui.Day.Text = `{State.DayName}  \u{00B7}  {State.ClockText}`
	-- today's attendance from your profile
	local Profile = Local.Profile()
	local Today = {}
	for _, R in (Profile and Profile.Attendance and Profile.Attendance.Recent) or {} do
		if R.Day == State.Day and R.Period and not Today[R.Period] then Today[R.Period] = R end
	end
	local Order = 0
	for Index, Seg in SchoolTime.Segments do
		if not SHOW[Seg.Kind] then continue end
		if Seg.Kind == `Night` and Seg.Start < 600 then continue end -- the early-morning half of the night
		Order += 1
		local Class = Seg.Kind == `Class` and Classes.Periods[Seg.Name]
		local Small = Seg.Kind == `Passing`
		local H = if Small then 20 else 34
		local Row = Instance.new(`Frame`)
		Row.Name = `Row`
		Row.BackgroundColor3 = C.Ink
		Row.BackgroundTransparency = if Small then 1 else 0.55
		Row.BorderSizePixel = 0
		Row.Size = UDim2.new(1, -8, 0, H)
		Row.LayoutOrder = Order
		Row.Parent = Ui.List
		local Rim = Instance.new(`UIStroke`)
		Rim.Color = C.Gold
		Rim.Thickness = 1
		Rim.Transparency = 1
		Rim.Parent = Row
		local Time = Local.Label(Row, `{SchoolTime.FormatClock(Seg.Start)}`, if Small then 12 else 14,
			{ Font = Fonts.Title; TextColor3 = C.TextDim; Position = UDim2.fromOffset(8, 0); Size = UDim2.new(0, 84, 1, 0) })
		-- "Homeroom · Homeroom" reads as a typo: show the subject only when it says something new
		local Title = if Class and Class.Subject ~= Seg.Name then `{Seg.Name}  <font color="#{C.TextDim:ToHex()}">\u{00B7}</font>  {Class.Subject}` else Seg.Name
		local Name = Local.Label(Row, Title, if Small then 12 else 17, { Font = if Small then Fonts.Body else Fonts.Title;
			TextColor3 = if Small then C.TextDim else C.Text; Position = UDim2.fromOffset(96, 0); Size = UDim2.new(1, -250, 1, 0) })
		local Where = Local.Label(Row, if Class then (Classes.Rooms[Class.Room] or Class.Room) else ``, 15,
			{ TextColor3 = C.Text:Lerp(C.TextDim, 0.35); TextXAlignment = Enum.TextXAlignment.Right; AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -96, 0, 0); Size = UDim2.fromOffset(110, H) })
		local Rec = Class and Today[Seg.Name]
		local Tag = STATUS[Rec and Rec.Status or ``]
		local Chip = Local.Label(Row, if Tag then Tag[1] .. (if Rec.ActivityGrade then `  {Rec.ActivityGrade}` else ``) else ``, 13,
			{ Font = Fonts.Title; TextColor3 = if Tag then Tag[2] else C.TextDim; TextXAlignment = Enum.TextXAlignment.Right;
			AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -8, 0, 0); Size = UDim2.fromOffset(84, H) })
		local Fill = Instance.new(`Frame`)
		Fill.Name = `Progress`
		Fill.BackgroundColor3 = C.Gold
		Fill.BackgroundTransparency = 0.82
		Fill.BorderSizePixel = 0
		Fill.Size = UDim2.fromScale(0, 1)
		Fill.ZIndex = 0
		Fill.Parent = Row
		Rows[Index] = { Row = Row; Rim = Rim; Fill = Fill; Name = Name; Time = Time; Where = Where; Chip = Chip; Seg = Seg; Small = Small; Class = Class }
	end
	local Owed = Player:GetAttribute(`DetentionsOwed`) or 0
	Ui.Foot.Text = if Owed > 0 then `<font color="#{BAD:ToHex()}">Detention owed: Room 106, outside class time.</font>` else `Click the clock again to close.  Classes give 1.2x EXP in school hours.`
	Local.Tick(State)
end

-- the live part: what's now, what's next, the gold row and its progress
function Local.Tick(State)
	if not (Ui and State) then return end
	Ui.Day.Text = `{State.DayName}  \u{00B7}  {State.ClockText}`
	local Mod = State.MinuteOfDay
	for Index, R in Rows do
		local Seg = R.Seg
		local Live = Index == State.SegmentIndex
		local Past = Seg.End <= Mod and not Live
		R.Rim.Transparency = if Live then 0.2 else 1
		R.Row.BackgroundTransparency = if R.Small then 1 elseif Live then 0.3 else 0.55
		local K = if Live then math.clamp((Mod - Seg.Start) / math.max(1, Seg.End - Seg.Start), 0, 1) else 0
		R.Fill.Size = UDim2.fromScale(K, 1)
		local Fade = if Past then 0.45 else 0
		R.Name.TextTransparency, R.Time.TextTransparency, R.Where.TextTransparency = Fade, Fade, Fade
		R.Time.TextColor3 = if Live then C.Gold else C.TextDim
		if Live and R.Class and R.Chip.Text == `` then R.Chip.Text = `Now` R.Chip.TextColor3 = C.Gold end
	end
	-- the line at the top
	local Seg = State.Segment
	local Class = Seg.Kind == `Class` and Classes.Periods[Seg.Name]
	local Ends = SchoolTime.FormatClock(Seg.End)
	local Line = if Class then `<b>Now:</b> {Seg.Name} \u{00B7} {Class.Subject} \u{00B7} {Classes.Rooms[Class.Room] or Class.Room}, ends {Ends}`
		else `<b>Now:</b> {Seg.Name}, until {Ends}`
	local Next
	for I = State.SegmentIndex + 1, #SchoolTime.Segments do
		local S = SchoolTime.Segments[I]
		local Cl = S.Kind == `Class` and Classes.Periods[S.Name]
		if Cl then Next = `<b>Next class:</b> {Cl.Subject} in {Classes.Rooms[Cl.Room] or Cl.Room} at {SchoolTime.FormatClock(S.Start)}` break end
	end
	Ui.Now.Text = Line .. `\n` .. (Next or `<font color="#{C.TextDim:ToHex()}">No more classes today.</font>`)
	local Key = `{State.Day}:{State.SegmentIndex}`
	if LastKey and Key ~= LastKey then Local.Render(State) end -- a new segment: attendance may have changed
	LastKey = Key
end

-- top edge in screen pixels (a ScreenGui that keeps the top inset measures from below it)
function Local.ScreenTop(G: GuiObject): number
	local Sg = G:FindFirstAncestorWhichIsA(`ScreenGui`)
	local Inset = if Sg and Sg.IgnoreGuiInset then 0 else GuiService:GetGuiInset().Y
	return G.AbsolutePosition.Y + Inset
end

-- hang the card just below the clock panel (its title tab used to overlap the clock's bottom edge)
function Local.Place()
	if not Ui then return end
	local Hud = Player.PlayerGui:FindFirstChild(`ClockHud`)
	local Clock = Hud and Hud:FindFirstChildWhichIsA(`Frame`)
	if not Clock then return end
	local U = Ui.Gui:FindFirstChild(`NHAutoScale`)
	local Scale = if U and U:IsA(`UIScale`) and U.Scale > 0 then U.Scale else 1
	-- the panel's title tab rises about 18 design px above its top edge
	local Want = Local.ScreenTop(Clock) + Clock.AbsoluteSize.Y + 12 + 18 * Scale
	local Have = Local.ScreenTop(Ui.Panel)
	local Offset = Ui.Panel.Position.Y.Offset + (Want - Have) / Scale
	if math.abs(Want - Have) > 1 then Ui.Panel.Position = UDim2.new(1, -24, 0, Offset) end
end

function Shared.IsOpen(): boolean return Ui ~= nil and Ui.Gui.Enabled end

function Shared.Toggle(On: boolean?)
	if not Ui then Local.Build() end
	if On == nil then On = not Ui.Gui.Enabled end
	if On and Player:GetAttribute(`InMainMenu`) == true then return end
	if On then
		LastKey = nil
		Local.Render(Local.State())
		pcall(Kit.PlaySound, `Tick`)
	end
	Ui.Gui.Enabled = On
	if On then task.defer(Local.Place) end
end

-- the clock in the top-right opens it. (Fix 2026-11-02: a full-size button inside the clock panel made the panel,
-- which sizes itself to its contents, stretch down the whole screen. The panel now takes the click itself.)
function Local.HookClock()
	local PG = Player:WaitForChild(`PlayerGui`)
	local Hud = PG:WaitForChild(`ClockHud`, 30)
	if not Hud then return end
	local Panel = Hud:FindFirstChildWhichIsA(`Frame`)
	if not Panel or Panel:GetAttribute(`NHTimetableHooked`) then return end
	Panel:SetAttribute(`NHTimetableHooked`, true)
	Panel.Active = true
	Panel.InputBegan:Connect(function(Input)
		if Input.UserInputType == Enum.UserInputType.MouseButton1 or Input.UserInputType == Enum.UserInputType.Touch then
			Shared.Toggle()
		end
	end)
end

function Shared.OnStart()
	task.spawn(Local.HookClock)
	local Acc = 0
	RunService.Heartbeat:Connect(function(Dt)
		Acc += Dt
		if Acc < 0.5 then return end
		Acc = 0
		if Ui and Ui.Gui.Enabled then
			if Player:GetAttribute(`InMainMenu`) == true then Ui.Gui.Enabled = false return end
			Local.Place() -- follows the clock if the screen size changes
			Local.Tick(Local.State())
		end
	end)
end

return Shared
