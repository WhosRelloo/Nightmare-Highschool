--[[
	ClockHud (client)
	Top-right panel: day + time, current period and time left, and a school-hours badge.
	Computes time locally from the server's published Epoch (no per-tick network traffic).
	(2.30) A PA line at the top: World.Broadcast's announcements, typed in with a chime (ReplicatedStorage.NHBroadcast).
	(2.36) The Bell Tower cluster: TowerPlate, the timetable Dial with the moon and hand, and the conduct row (Functions.BellTower). Art in Config.BellTowerArt, with kit fallbacks.
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
local BellTower = require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`BellTower`)) -- (2.36) Bell Tower view logic
local Art = require(ReplicatedStorage.Config:WaitForChild(`BellTowerArt`)) -- (2.36) Bell Tower art ids
local DIAL = 176 -- design px
local INK = Color3.fromRGB(58, 26, 20) -- text on paper
local INK_CRIMSON = Color3.fromRGB(122, 16, 24)

local WAYPOINT_LEAD_MINUTES = 15 -- show the room marker this many in-game minutes before class

local Player = Players.LocalPlayer

local Local = {}
local Shared = {}

function Local.Label(Parent: Instance, Name: string, Order: number, Size: number, Bold: boolean): TextLabel
	Size = math.max(Size, BellTower.MIN_TEXT)
	local Label = Instance.new(`TextLabel`)
	Label.Name = Name
	Label.LayoutOrder = Order
	Label.BackgroundTransparency = 1
	Label.Size = UDim2.new(1, 0, 0, Size + 4)
	Label.Font = if Bold then KitTheme.Fonts.Title else KitTheme.Fonts.Body
	Label.TextSize = Size
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

-- (2.36) an art piece from Config.BellTowerArt, or nil while its id is 0 (the caller draws the kit fallback)
function Local.Img(Key: string, Props: { [string]: any }): ImageLabel?
	local Id = BellTower.Image(Art, Key)
	if not Id then return nil end
	local I = Instance.new(`ImageLabel`)
	I.BackgroundTransparency = 1
	I.Image = Id
	local S = Art.Slices[Key]
	if S then
		I.ScaleType = Enum.ScaleType.Slice
		I.SliceCenter = S.Center
		I.SliceScale = S.Scale
	end
	local Parent = Props.Parent
	for K, V in Props do if K ~= `Parent` then (I :: any)[K] = V end end
	I.Parent = Parent
	return I
end

function Local.CreateGui()
	local Gui = Instance.new(`ScreenGui`)
	Gui.Name = `ClockHud`
	Gui.ResetOnSpawn = false
	Gui.DisplayOrder = 4
	Kit.AutoScale(Gui, { phoneScale = 0.5 }) -- same design-px scale as QuestTracker; smaller on phones

	-- (2.36) The Bell Tower cluster. Panel stays ClockHud's ONLY direct Frame child: Timetable (click + placement),
	-- Moments (BellRim) and TouchControls (Top) find it that way.
	local Panel = Instance.new(`Frame`)
	Panel.Name = `Panel`
	Panel.AnchorPoint = Vector2.new(1, 0)
	Panel.Position = UDim2.new(1, -24, 0, 12)
	Panel.Size = UDim2.new(0, 500, 0, 0)
	Panel.AutomaticSize = Enum.AutomaticSize.Y
	Panel.BackgroundTransparency = 1
	Panel.Parent = Gui
	local Stack = Instance.new(`UIListLayout`)
	Stack.SortOrder = Enum.SortOrder.LayoutOrder
	Stack.HorizontalAlignment = Enum.HorizontalAlignment.Right
	Stack.Padding = UDim.new(0, 8)
	Stack.Parent = Panel

	local Head = Instance.new(`Frame`)
	Head.Name = `Head`
	Head.LayoutOrder = 1
	Head.BackgroundTransparency = 1
	Head.Size = UDim2.new(1, 0, 0, 0)
	Head.AutomaticSize = Enum.AutomaticSize.Y
	Head.Parent = Panel

	local HasDial = BellTower.Image(Art, `Dial`) ~= nil and BellTower.Image(Art, `DialHand`) ~= nil
	-- the plate: TowerPlate 9-slice, or the kit's ornate chip while the art isn't uploaded
	local Plate: GuiObject = Local.Img(`TowerPlate`, { Name = `Plate` }) or Instance.new(`Frame`)
	Plate.Name = `Plate`
	Plate.BackgroundTransparency = 1
	Plate.AnchorPoint = Vector2.new(1, 0)
	Plate.Position = if HasDial then UDim2.new(1, -(DIAL - 30), 0, 22) else UDim2.new(1, 0, 0, 0)
	Plate.Size = UDim2.new(0, if HasDial then 340 else 440, 0, 0)
	Plate.AutomaticSize = Enum.AutomaticSize.Y
	Plate.Parent = Head
	if not Plate:IsA(`ImageLabel`) then Kit.Decorate(Plate, { ornamentScale = 0.6, bgTransparency = 0.08 }) end

	local Lines = Instance.new(`Frame`)
	Lines.Name = `Lines`
	Lines.BackgroundTransparency = 1
	Lines.Size = UDim2.new(1, 0, 0, 0)
	Lines.AutomaticSize = Enum.AutomaticSize.Y
	Lines.ZIndex = 2
	Lines.Parent = Plate
	local Pad = Instance.new(`UIPadding`)
	Pad.PaddingTop = UDim.new(0, 14)
	Pad.PaddingBottom = UDim.new(0, 14)
	Pad.PaddingLeft = UDim.new(0, 22)
	Pad.PaddingRight = UDim.new(0, if HasDial then 40 else 24) -- the dial overlaps the plate's right end by 30
	Pad.Parent = Lines
	local Layout = Instance.new(`UIListLayout`)
	Layout.SortOrder = Enum.SortOrder.LayoutOrder
	Layout.HorizontalAlignment = Enum.HorizontalAlignment.Right
	Layout.Padding = UDim.new(0, 2)
	Layout.Parent = Lines

	local Labels = {
		Time = Local.Label(Lines, `Time`, 1, 28, true);
		Period = Local.Label(Lines, `Period`, 2, 20, false);
		Class = Local.Label(Lines, `Class`, 3, 20, true);
		Badge = Local.Label(Lines, `Badge`, 4, 20, true);
		Carry = Local.Label(Lines, `Carry`, 6, 20, false); -- (1.42) a lost item in your hand (Features.LostFound)
	}
	Labels.PA = Local.Label(Lines, `PA`, 0, 20, true) -- (2.30) the PA (World.Broadcast)
	Labels.PA.TextColor3 = KitTheme.Colors.Gold
	Labels.PA.Visible = false
	Kit.Emboss(Labels.Time, Color3.fromRGB(150, 140, 130), 1.4)
	Labels.Badge.TextColor3 = KitTheme.Colors.Gold

	-- the dial: the moon in its window, the rim (today's timetable), the hand
	local Moon = Instance.new(`ImageLabel`)
	Moon.Name = `Moon`
	Moon.BackgroundTransparency = 1
	Moon.ScaleType = Enum.ScaleType.Fit
	Moon.ImageColor3 = Color3.fromRGB(244, 232, 206)
	Moon.Visible = false
	if HasDial then
		local Dial = Instance.new(`Frame`)
		Dial.Name = `Dial`
		Dial.BackgroundTransparency = 1
		Dial.AnchorPoint = Vector2.new(1, 0)
		Dial.Position = UDim2.new(1, 0, 0, 0)
		Dial.Size = UDim2.fromOffset(DIAL, DIAL)
		Dial.ZIndex = 3
		Dial.Parent = Head
		Moon.AnchorPoint = Vector2.new(0.5, 0.5)
		Moon.Position = UDim2.fromScale(0.5, 0.5)
		Moon.Size = UDim2.fromScale(0.35, 0.35)
		Moon.ZIndex = 3
		Moon.Parent = Dial
		Local.Img(`Dial`, { Name = `Face`; Size = UDim2.fromScale(1, 1); ZIndex = 4; Parent = Dial })
		Labels.Hand = Local.Img(`DialHand`, { Name = `Hand`; Size = UDim2.fromScale(1, 1); ZIndex = 5; Parent = Dial })
	else
		-- (1.41) fallback: tonight's moon just left of the day and time
		Moon.AnchorPoint = Vector2.new(1, 0.5)
		Moon.Size = UDim2.fromOffset(30, 30)
		Moon.ZIndex = 3
		Moon.Parent = Labels.Time
	end
	Labels.Moon = Moon
	Labels.MoonInDial = HasDial

	-- the conduct row: a detention slip, the wax seal, the level (replaces the orange record line)
	local Conduct = Instance.new(`Frame`)
	Conduct.Name = `Conduct`
	Conduct.LayoutOrder = 2
	Conduct.BackgroundTransparency = 1
	Conduct.Size = UDim2.new(1, 0, 0, 0)
	Conduct.AutomaticSize = Enum.AutomaticSize.Y
	Conduct.Visible = false
	Conduct.Parent = Panel
	local Row = Instance.new(`UIListLayout`)
	Row.FillDirection = Enum.FillDirection.Horizontal
	Row.HorizontalAlignment = Enum.HorizontalAlignment.Right
	Row.VerticalAlignment = Enum.VerticalAlignment.Center
	Row.SortOrder = Enum.SortOrder.LayoutOrder
	Row.Padding = UDim.new(0, 10)
	Row.Parent = Conduct

	local Slip: GuiObject = Local.Img(`Slip`, { Name = `Slip` }) or Instance.new(`Frame`)
	Slip.Name = `Slip`
	Slip.BackgroundTransparency = 1
	Slip.LayoutOrder = 1
	Slip.Size = UDim2.fromOffset(300, 100)
	Slip.Visible = false
	Slip.Parent = Conduct
	local OnPaper = Slip:IsA(`ImageLabel`)
	if not OnPaper then Kit.Decorate(Slip, { ornament = `thin`, bgTransparency = 0.1 }) end
	local function SlipText(Name: string, Y: number, Font: Enum.Font, Size: number, Color: Color3): TextLabel
		local L = Instance.new(`TextLabel`)
		L.Name = Name
		L.BackgroundTransparency = 1
		L.Position = UDim2.fromOffset(if OnPaper then 64 else 18, Y)
		L.Size = UDim2.new(1, if OnPaper then -76 else -36, 0, Size + 4)
		L.Font = Font
		L.TextSize = Size
		L.TextColor3 = Color
		L.TextXAlignment = Enum.TextXAlignment.Left
		L.TextScaled = false
		L.ZIndex = 3
		L.Text = ``
		L.Parent = Slip
		return L
	end
	local SlipTitle = SlipText(`Title`, 18, KitTheme.Fonts.Title, 22, if OnPaper then INK_CRIMSON else KitTheme.Colors.Gold)
	local SlipLine = SlipText(`Line`, 50, KitTheme.Fonts.Body, 20, if OnPaper then INK else KitTheme.Colors.Text)

	local Seal = Local.Img(`Seal`, { Name = `Seal`; LayoutOrder = 2; Size = UDim2.fromOffset(66, 66); Visible = false; Parent = Conduct })
	local Level = Instance.new(`TextLabel`)
	Level.Name = `Level`
	Level.LayoutOrder = 3
	Level.BackgroundTransparency = 1
	Level.AutomaticSize = Enum.AutomaticSize.X
	Level.Size = UDim2.fromOffset(0, 30)
	Level.Font = KitTheme.Fonts.Title
	Level.TextSize = 22
	Level.TextColor3 = KitTheme.Colors.Text
	Level.Text = ``
	Level.Visible = false
	Level.Parent = Conduct
	local LS = Instance.new(`UIStroke`)
	LS.Thickness = 1.2
	LS.Transparency = 0.25
	LS.Parent = Level
	Labels.Conduct = { Row = Conduct; Slip = Slip; SlipTitle = SlipTitle; SlipLine = SlipLine; Seal = Seal; Level = Level }

	Gui.Parent = Player:WaitForChild(`PlayerGui`)
	return Labels
end

-- (2.36) the conduct row, from the Discipline attributes. Returns whether the Room 106 marker should show.
function Local.UpdateConduct(Labels, IsClass: boolean): boolean
	local C = BellTower.Conduct({
		DisciplineLevel = Player:GetAttribute(`DisciplineLevel`);
		DisciplinePoints = Player:GetAttribute(`DisciplinePoints`);
		DetentionsOwed = Player:GetAttribute(`DetentionsOwed`);
		DetentionActive = Player:GetAttribute(`DetentionActive`);
		DetentionCollected = Player:GetAttribute(`DetentionCollected`);
		DetentionTotal = Player:GetAttribute(`DetentionTotal`);
		Suspended = Player:GetAttribute(`Suspended`);
	}, IsClass)
	local U = Labels.Conduct
	U.Row.Visible = C.Visible
	local S = C.Slips[1]
	U.Slip.Visible = S ~= nil
	if S then
		U.SlipTitle.Text = S.Title
		U.SlipLine.Text = S.Line
	end
	U.Level.Visible = C.Seal ~= nil
	U.Level.Text = C.Text
	U.Level.TextColor3 = if C.Seal then BellTower.Tints[C.Seal]:Lerp(Color3.new(1, 1, 1), 0.35) else KitTheme.Colors.Text
	if U.Seal then
		U.Seal.Visible = C.Seal ~= nil
		if C.Seal then
			U.Seal.Image = (C.Broken and BellTower.Image(Art, `SealBroken`)) or BellTower.Image(Art, `Seal`) or ``
			U.Seal.ImageColor3 = BellTower.Tints[C.Seal]
		end
	end
	return C.Waypoint
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
		Label.TextSize = BellTower.MIN_TEXT
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

-- (2.30) the PA (World.Broadcast): a chime, the line typed in, held, then gone
local PAToken = 0
function Shared.ShowPA(Text: string, Chime: string?)
	local L = Local.Labels and Local.Labels.PA
	if not L then return end
	PAToken += 1
	local Mine = PAToken
	pcall(function()
		local S = Instance.new(`Sound`)
		S.SoundId = Chime or `rbxassetid://9114058995`
		S.Volume = 0.3
		S.Parent = game:GetService(`SoundService`)
		S:Play()
		game:GetService(`Debris`):AddItem(S, 3)
	end)
	L.Visible = true
	for I = 1, #Text do
		if PAToken ~= Mine then return end
		L.Text = `PA  ·  ` .. Text:sub(1, I)
		task.wait(0.025)
	end
	task.wait(math.clamp(#Text * 0.06, 4, 10))
	if PAToken == Mine then L.Visible = false end
end

function Shared.OnStart()
	local Clock = ReplicatedStorage:WaitForChild(`SchoolClock`)
	local Labels = Local.CreateGui()
	Local.Labels = Labels -- (2.30) for ShowPA
	task.spawn(function()
		local R = ReplicatedStorage:WaitForChild(`NHBroadcast`, 60)
		if R then
			R.OnClientEvent:Connect(function(M)
				if typeof(M) == `table` and M.Kind == `PA` and typeof(M.Text) == `string` then task.spawn(Shared.ShowPA, M.Text, M.Chime) end
			end)
		end
	end)

	task.spawn(function()
		while true do
			local Epoch = Clock:GetAttribute(`Epoch`)
			if Epoch then
				local State = SchoolTime.GetState(Epoch, workspace:GetServerTimeNow())
				Labels.Time.Text = `{State.DayName}  {State.ClockText}`

				local EndsAt = SchoolTime.FormatClock(State.Segment.End)
				-- (1.41) the moon: its icon by the time, and its name on the period line at night
				local Phase = Lineage.MoonPhase(State.Day, State.Hour)
				local Night = SchoolTime.IsNight(State.Hour) -- (2.22.0) shared night windows
				local Event = Lineage.MoonEvent and Lineage.MoonEvent(State.Day, State.Hour)
				local Icon = Lineage.MoonIcons and Lineage.MoonIcons[Event or Phase]
				Labels.Moon.Visible = typeof(Icon) == `string` and Icon ~= ``
				if Labels.Moon.Visible then
					Labels.Moon.Image = Icon
					-- the special moons keep their own colour; the four phases take the HUD's bone tint
					Labels.Moon.ImageColor3 = if Event then Color3.new(1, 1, 1) else Color3.fromRGB(244, 232, 206)
					if not Labels.MoonInDial then
						-- TextBounds is in screen pixels; the panel is in design pixels under its UIScale
						local Sg = Labels.Time:FindFirstAncestorOfClass(`ScreenGui`)
						local Sc = Sg and Sg:FindFirstChildWhichIsA(`UIScale`, true)
						local K = if Sc and Sc.Scale > 0 then Sc.Scale else 1
						Labels.Moon.Position = UDim2.new(1, -(Labels.Time.TextBounds.X / K + 10), 0.5, 0)
					end
				end
				if Labels.Hand then Labels.Hand.Rotation = BellTower.HandAngle(State.MinuteOfDay / 60) end -- (2.36)
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

				-- (2.36) Discipline: the conduct row (seal, level, slip) replaces the orange record line
				local DetentionWaypoint = Local.UpdateConduct(Labels, State.Segment.Kind == `Class`)

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
