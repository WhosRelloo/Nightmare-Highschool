--[[
	SchoolClock (server authoritative)

	Owns the official in-game time. Publishes ReplicatedStorage.SchoolClock with:
		Epoch          -- server time when in-game day 0, 00:00 began (clients derive time from it)
		Period / Kind  -- current timetable segment (for convenience / debugging)

	Server API:
		SchoolClock.GetState()            -> SchoolTime.State
		SchoolClock.IsSchoolHours()       -> boolean
		SchoolClock.GetExpMultiplier()    -> 1.2 during school hours, else 1
		SchoolClock.SetTime("HH:MM", Day?) -- jump the clock (admin / testing; this server only)
		SchoolClock.SetSpeed(RealSecondsPerGameHour) -- testing: speed the clock up, keeping the current time
		SchoolClock.PeriodChanged(NewState, OldSegment?)
		SchoolClock.SchoolHoursChanged(IsSchoolHours)
		SchoolClock.IsNight(Window?)      -> in a named night window now (SchoolTime.Windows; default "Night")
		SchoolClock.Phase()               -> "Late" | "Night" | "Dark" | "Dusk" | "Day"
		SchoolClock.Calendar()            -> { Week, Term, Year, WeekCount }
]]

---| Services |---

local Lighting = game:GetService(`Lighting`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

---| Modules |---

local SignalPlus = require(ReplicatedStorage.Packages.SignalPlus)
local Schedule = require(ReplicatedStorage.Config.SchoolSchedule)
local SchoolTime = require(ReplicatedStorage.Functions.SchoolTime)

local TICK = 0.5

local Clock: Configuration = nil
local LastIndex: number? = nil
local LastDay: number? = nil
local LastSchoolHours: boolean? = nil
local LastSegment = nil

local Local = {}
local Shared = {}

Shared.PeriodChanged = SignalPlus()
Shared.SchoolHoursChanged = SignalPlus()

function Shared.GetState(): SchoolTime.State
	return SchoolTime.GetState(Clock:GetAttribute(`Epoch`), workspace:GetServerTimeNow())
end

function Shared.IsSchoolHours(): boolean
	return Shared.GetState().IsSchoolHours
end

-- (2.22.0) shared night windows and the school calendar
function Shared.IsNight(Window: string?): boolean
	return SchoolTime.InWindow(Shared.GetState().Hour, Window or `Night`)
end

function Shared.Phase(): string
	return SchoolTime.Phase(Shared.GetState().Hour)
end

function Shared.Calendar()
	return SchoolTime.Calendar(Shared.GetState().Day)
end

function Shared.GetExpMultiplier(): number
	return if Shared.IsSchoolHours() then Schedule.SchoolHoursExpMultiplier else 1
end

function Shared.SetTime(TimeText: string, Day: number?)
	local Now = workspace:GetServerTimeNow()
	local Current = Shared.GetState()
	Clock:SetAttribute(`Epoch`, SchoolTime.EpochFor(Now, Day or Current.Day, SchoolTime.ParseTime(TimeText)))
	Local.Tick()
end

function Shared.SetSpeed(RealSecondsPerGameHour: number)
	local Current = Shared.GetState()
	Schedule.RealSecondsPerGameHour = RealSecondsPerGameHour
	Clock:SetAttribute(`RealSecondsPerGameHour`, RealSecondsPerGameHour)
	Clock:SetAttribute(`Epoch`, SchoolTime.EpochFor(workspace:GetServerTimeNow(), Current.Day, Current.MinuteOfDay))
	Local.Tick()
end

function Local.Tick()
	local State = Shared.GetState()

	if Schedule.SyncLighting then
		Lighting.ClockTime = State.Hour
	end

	if State.SegmentIndex ~= LastIndex or State.Day ~= LastDay then
		local Old = LastSegment
		LastIndex, LastDay, LastSegment = State.SegmentIndex, State.Day, State.Segment

		Clock:SetAttribute(`Period`, State.Segment.Name)
		Clock:SetAttribute(`Kind`, State.Segment.Kind)
		Shared.PeriodChanged:Fire(State, Old)
	end

	if State.IsSchoolHours ~= LastSchoolHours then
		LastSchoolHours = State.IsSchoolHours
		Clock:SetAttribute(`SchoolHours`, State.IsSchoolHours)
		Shared.SchoolHoursChanged:Fire(State.IsSchoolHours)
	end
end

-- Created at require time so other services can call GetState() from their OnStart.
Clock = ReplicatedStorage:FindFirstChild(`SchoolClock`) :: Configuration
if not Clock then
	Clock = Instance.new(`Configuration`)
	Clock.Name = `SchoolClock`
	local Epoch = if Schedule.ClockMode == `Global`
		then Schedule.GlobalEpoch
		else SchoolTime.EpochFor(workspace:GetServerTimeNow(), 0, SchoolTime.ParseTime(Schedule.StartTime))
	Clock:SetAttribute(`Epoch`, Epoch)
	Clock.Parent = ReplicatedStorage
end

function Shared.OnStart()
	Local.Tick()
	task.spawn(function()
		while true do
			task.wait(TICK)
			Local.Tick()
		end
	end)
end

return Shared
