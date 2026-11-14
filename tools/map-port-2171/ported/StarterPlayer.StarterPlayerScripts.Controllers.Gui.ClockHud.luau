--[[
	ClockHud (client)
	Top-right panel: day + time, current period and time left, and a school-hours badge.
	Computes time locally from the server's published Epoch (no per-tick network traffic).
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

---| Modules |---

local Schedule = require(ReplicatedStorage.Config.SchoolSchedule)
local Classes = require(ReplicatedStorage.Config.Classes)
local Activities = require(ReplicatedStorage.Config.Activities)
local SchoolTime = require(ReplicatedStorage.Functions.SchoolTime)
local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`)) -- NH UI kit
local KitTheme = Kit.Theme
local Lineage = require(ReplicatedStorage:WaitForChild(`Lineage`)) -- (1.41) moon phases

local WAYPOINT_LEAD_MINUTES = 15 -- show the room marker this many in-game minutes before class

local Player = Players.LocalPlayer

local Local = {}
local Shared = {}

function Local.Label(Parent: Instance, Name: string, Order: number, Size: number, Bold: boolean): TextLabel
	local Label = Instance.new(`TextLabel`)
	Label.Name = Name
	Label.LayoutOrder = Order
	Label.BackgroundTransparency = 1
	Label.Size = UDim2.new(1, 0, 0, Size + 6)
	Label.Font = if Bold then KitTheme.Fonts.Title else KitTheme.Fonts.Body
	Label.TextSize = if Bold then Size else Size + 3 -- Garamond runs small
	Label.TextColor3 = KitTheme.Colors.Text
	Label.TextXAlignment = Enum.TextXAlignment.Right
	Label.TextWrapped = true
	Label.AutomaticSize = Enum.AutomaticSize.Y
	Label.Text = ``

	local Stroke = Instance.new(`UIStroke`)
	Stroke.Thickness = 1.2
	Stroke.Color = Color3.new(0, 0, 0)
	Stroke.Transparency = 0.25
	Stroke.Parent = Label

	Label.Parent = Parent
	return Label
end

function Local.CreateGui()
	local Gui = Instance.new(`ScreenGui`)
	Gui.Name = `ClockHud`
	Gui.ResetOnSpawn = false
	Gui.DisplayOrder = 4
	Kit.AutoScale(Gui, { phoneScale = 0.5 }) -- same design-px scale as QuestTracker, so the tracker card (y 200) always sits below; smaller on phones

	-- Ornate kit chip, auto-height. Art in Panel.NHDecor, labels in Panel.Lines.
	local Panel = Instance.new(`Frame`)
	Panel.Name = `Panel`
	Panel.AnchorPoint = Vector2.new(1, 0)
	Panel.Position = UDim2.new(1, -30, 0, 12) -- keeps the drop shadow on screen
	Panel.Size = UDim2.new(0, 430, 0, 0)
	Panel.AutomaticSize = Enum.AutomaticSize.Y
	Panel.BackgroundTransparency = 1
	Panel.Parent = Gui
	Kit.Decorate(Panel, { ornamentScale = 0.6, bgTransparency = 0.08 })

	local Lines = Instance.new(`Frame`)
	Lines.Name = `Lines`
	Lines.BackgroundTransparency = 1
	Lines.Size = UDim2.new(1, 0, 0, 0)
	Lines.AutomaticSize = Enum.AutomaticSize.Y
	Lines.ZIndex = 2
	Lines.Parent = Panel
	local Pad = Instance.new(`UIPadding`)
	Pad.PaddingTop = UDim.new(0, 14)
	Pad.PaddingBottom = UDim.new(0, 14)
	Pad.PaddingLeft = UDim.new(0, 24)
	Pad.PaddingRight = UDim.new(0, 24)
	Pad.Parent = Lines

	local Layout = Instance.new(`UIListLayout`)
	Layout.SortOrder = Enum.SortOrder.LayoutOrder
	Layout.HorizontalAlignment = Enum.HorizontalAlignment.Right
	Layout.Padding = UDim.new(0, 2)
	Layout.Parent = Lines

	local Labels = {
		Time = Local.Label(Lines, `Time`, 1, 21, true);
		Period = Local.Label(Lines, `Period`, 2, 14, false);
		Class = Local.Label(Lines, `Class`, 3, 14, true);
		Badge = Local.Label(Lines, `Badge`, 4, 13, true);
		Record = Local.Label(Lines, `Record`, 5, 13, true);
		Carry = Local.Label(Lines, `Carry`, 6, 13, false); -- (1.42) a lost item in your hand (Features.LostFound)
	}
	Kit.Emboss(Labels.Time, Color3.fromRGB(150, 140, 130), 1.4)
	Labels.Badge.TextColor3 = KitTheme.Colors.Gold
	-- (1.41) tonight's moon, just left of the day and time (Lineage.MoonIcons; hidden until the icons are set)
	local Moon = Instance.new(`ImageLabel`)
	Moon.Name = `Moon`
	Moon.BackgroundTransparency = 1
	Moon.AnchorPoint = Vector2.new(1, 0.5)
	Moon.Size = UDim2.fromOffset(26, 26)
	Moon.ScaleType = Enum.ScaleType.Fit
	Moon.ImageColor3 = Color3.fromRGB(244, 232, 206)
	Moon.Visible = false
	Moon.ZIndex = 3
	Moon.Parent = Labels.Time
	Labels.Moon = Moon

	Gui.Parent = Player:WaitForChild(`PlayerGui`)
	return Labels
end

-- The class happening now, or the next one later today.
function Local.GetClassInfo(State): (any, boolean)
	if State.Segment.Kind == `Class` then
		local Class = Classes.Periods[State.Segment.Name]
		if Class then return { Period = State.Segment.Name, Class = Class, Start = State.Segment.Start }, true end
	end

	for Index = State.SegmentIndex + 1, #SchoolTime.Segments do
		local Segment = SchoolTime.Segments[Index]
		local Class = Segment.Kind == `Class` and Classes.Periods[Segment.Name]
		if Class then
			return { Period = Segment.Name, Class = Class, Start = Segment.Start }, false
		end
	end
	return nil, false
end

local Waypoint: BillboardGui? = nil

function Local.UpdateWaypoint(RoomId: string?, Text: string)
	local School = workspace:FindFirstChild(`School`)
	local Room = RoomId and School and School:FindFirstChild(RoomId)
	local Door = Room and Room:FindFirstChild(`Door`)

	if not Door then
		if Waypoint then Waypoint.Enabled = false end
		return
	end

	-- rebuild if it was wiped (PlayerGui clears reset-on-spawn guis when you respawn)
	if Waypoint and not (Waypoint.Parent and Waypoint:FindFirstChild(`Label`)) then
		Waypoint:Destroy()
		Waypoint = nil
	end
	if not Waypoint then
		Waypoint = Instance.new(`BillboardGui`)
		Waypoint.Name = `ClassWaypoint`
		Waypoint.ResetOnSpawn = false
		Waypoint.AlwaysOnTop = true
		Waypoint.Size = UDim2.new(0, 220, 0, 44)
		Waypoint.StudsOffset = Vector3.new(0, 5, 0)
		Waypoint.LightInfluence = 0

		local Label = Instance.new(`TextLabel`)
		Label.Name = `Label`
		Label.Size = UDim2.fromScale(1, 1)
		Label.BackgroundColor3 = KitTheme.Colors.Ink
		Label.BackgroundTransparency = 0.15
		Label.Font = KitTheme.Fonts.Title
		Label.TextSize = 18
		Label.TextColor3 = KitTheme.Colors.Gold
		Label.TextStrokeTransparency = 0.4
		Label.Parent = Waypoint
		Kit.Slice(`FrameThin`, KitTheme.Colors.Gold:Lerp(KitTheme.Colors.Iron, 0.5), { SliceScale = 0.35, Parent = Label })

		Waypoint.Parent = Player:WaitForChild(`PlayerGui`)
	end

	local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`)
	local Distance = if Root then math.floor((Root.Position - Door.Position).Magnitude) else 0

	Waypoint.Adornee = Door
	local Label = Waypoint:FindFirstChild(`Label`) :: TextLabel?
	if Label then Label.Text = `{Text}\n{Distance} studs` end
	Waypoint.Enabled = true
end

function Shared.OnStart()
	local Clock = ReplicatedStorage:WaitForChild(`SchoolClock`)
	local Labels = Local.CreateGui()

	task.spawn(function()
		while true do
			local Epoch = Clock:GetAttribute(`Epoch`)
			if Epoch then
				local State = SchoolTime.GetState(Epoch, workspace:GetServerTimeNow())
				Labels.Time.Text = `{State.DayName}  {State.ClockText}`

				local EndsAt = SchoolTime.FormatClock(State.Segment.End)
				-- (1.41) the moon: its icon by the time, and its name on the period line at night
				local Phase = Lineage.MoonPhase(State.Day, State.Hour)
				local Night = State.Hour >= 20 or State.Hour < 6
				local Event = Lineage.MoonEvent and Lineage.MoonEvent(State.Day, State.Hour)
				local Icon = Lineage.MoonIcons and Lineage.MoonIcons[Event or Phase]
				Labels.Moon.Visible = typeof(Icon) == `string` and Icon ~= ``
				if Labels.Moon.Visible then
					Labels.Moon.Image = Icon
					-- the special moons keep their own colour; the four phases take the HUD's bone tint
					Labels.Moon.ImageColor3 = if Event then Color3.new(1, 1, 1) else Color3.fromRGB(244, 232, 206)
					-- TextBounds is in screen pixels; the panel is in design pixels under its UIScale
					local Sg = Labels.Time:FindFirstAncestorOfClass(`ScreenGui`)
					local Sc = Sg and Sg:FindFirstChildWhichIsA(`UIScale`, true)
					local K = if Sc and Sc.Scale > 0 then Sc.Scale else 1
					Labels.Moon.Position = UDim2.new(1, -(Labels.Time.TextBounds.X / K + 10), 0.5, 0)
				end
				local MoonName = if Event then Lineage.MoonEvents[Event].Name else Lineage.MoonPhaseNames[Phase]
				Labels.Period.Text = `{State.Segment.Name}  (until {EndsAt})` .. (if Night then `  \u{00B7}  {MoonName or ``}` else ``)

				local Lost = Player:GetAttribute(`NHLostItemText`)
				local Errand = Player:GetAttribute(`NHErrandText`) -- (1.47) a substitute's errand (School.Substitutes)
				Labels.Carry.Visible = typeof(Lost) == `string` or typeof(Errand) == `string`
				Labels.Carry.Text = if typeof(Errand) == `string` then Errand elseif typeof(Lost) == `string` then `Carrying: {Lost}` else ``
				Labels.Badge.Visible = State.IsSchoolHours
				Labels.Badge.Text = `School hours: {Schedule.SchoolHoursExpMultiplier}x EXP`

				-- Class guidance + room marker
				local Info, Now = Local.GetClassInfo(State)
				local RoomName = Info and (Classes.Rooms[Info.Class.Room] or Info.Class.Room)
				local ShowWaypoint = false

				-- (2.7.3) suspended: classes are off-limits today (Services.School.Discipline), so no "NOT IN CLASS" or room marker
				local Suspended = Player:GetAttribute(`Suspended`) == true
				if Info and Now and Suspended then
					Labels.Class.Text = `{Info.Class.Subject} · {RoomName} · Suspended: stay off campus (Bruno has work at the Back Lot)`
					Labels.Class.TextColor3 = Color3.fromRGB(255, 170, 80)
				elseif Info and Now then
					local InRoom = Player:GetAttribute(`ClassInRoom`) == true
					local LessonKey = `D{State.Day}-S{State.SegmentIndex}`
					local LessonOpen = Activities.Subjects[Info.Class.Subject] ~= nil and Player:GetAttribute(`LessonPassedKey`) ~= LessonKey
					Labels.Class.Text = if InRoom
						then `{Info.Class.Subject} · {RoomName} · In class` .. (if LessonOpen then `  ·  [E] Start lesson at the teacher's desk` else `  ·  Lesson passed`)
						else `{Info.Class.Subject} · {RoomName} · NOT IN CLASS`
					Labels.Class.TextColor3 = if InRoom then Color3.fromRGB(130, 220, 140) else Color3.fromRGB(255, 120, 110)
					ShowWaypoint = not InRoom
				elseif Info then
					Labels.Class.Text = `Next: {Info.Class.Subject} · {RoomName} at {SchoolTime.FormatClock(Info.Start)}`
					Labels.Class.TextColor3 = Color3.fromRGB(200, 210, 230)
					ShowWaypoint = not Suspended and (Info.Start - State.MinuteOfDay) <= WAYPOINT_LEAD_MINUTES
				else
					Labels.Class.Text = ``
				end
				Labels.Class.Visible = Labels.Class.Text ~= ``

				-- Discipline record / detention
				local Level = Player:GetAttribute(`DisciplineLevel`)
				local Points = Player:GetAttribute(`DisciplinePoints`) or 0
				local Owed = Player:GetAttribute(`DetentionsOwed`) or 0
				local Orange = Color3.fromRGB(255, 170, 80)
				local DetentionWaypoint = false

				if Player:GetAttribute(`DetentionActive`) then
					local Done = Player:GetAttribute(`DetentionCollected`) or 0
					local Total = Player:GetAttribute(`DetentionTotal`) or 0
					Labels.Record.Text = if Done >= Total
						then `Detention: use the bin to finish`
						else `Detention: trash {Done}/{Total}`
					Labels.Record.TextColor3 = Orange
				elseif Owed > 0 then
					Labels.Record.Text = `Detention owed: Room 106 (outside class)`
					Labels.Record.TextColor3 = Orange
					DetentionWaypoint = State.Segment.Kind ~= `Class`
				elseif Level and Level ~= `Clear` then
					Labels.Record.Text = `Record: {Level} ({Points} pts)`
					Labels.Record.TextColor3 = if Level == `Warning` then Color3.fromRGB(255, 214, 102) else Color3.fromRGB(255, 120, 110)
				else
					Labels.Record.Text = ``
				end
				Labels.Record.Visible = Labels.Record.Text ~= ``

				if ShowWaypoint and Info then
					Local.UpdateWaypoint(Info.Class.Room, `{Info.Class.Subject} · {RoomName}`)
				elseif DetentionWaypoint then
					Local.UpdateWaypoint(`R106`, `Detention · Room 106`)
				else
					Local.UpdateWaypoint(nil, ``)
				end
			end
			task.wait(0.5)
		end
	end)
end

return Shared
