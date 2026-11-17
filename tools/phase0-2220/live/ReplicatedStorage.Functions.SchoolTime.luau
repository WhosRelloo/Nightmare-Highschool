--[[
	SchoolTime (shared, pure functions)

	The server publishes one number: ReplicatedStorage.SchoolClock:GetAttribute("Epoch"),
	the server time at which in-game day 0, 00:00 began. Server and clients both derive
	the current in-game time from workspace:GetServerTimeNow(), so nothing is sent per tick.
]]

---| Services |---

local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

---| Modules |---

local Schedule = require(ReplicatedStorage.Config.SchoolSchedule)

export type Segment = { Name: string, Kind: string, Start: number, End: number }
export type State = {
	Day: number;            -- 0-based in-game day count
	DayName: string;
	MinuteOfDay: number;    -- 0..1440 (fractional)
	Hour: number;           -- 0..24 (fractional), for Lighting.ClockTime
	ClockText: string;      -- e.g. "8:35 AM"
	Segment: Segment;
	SegmentIndex: number;
	MinutesLeft: number;    -- in-game minutes until the segment ends
	IsSchoolHours: boolean;
}

local SchoolTime = {}

function SchoolTime.ParseTime(Text: string): number
	local H, M = string.match(Text, `^(%d+):(%d+)$`)
	assert(H and M, `SchoolSchedule: bad time '{Text}' (use HH:MM)`)
	return tonumber(H) * 60 + tonumber(M)
end

function SchoolTime.FormatClock(MinuteOfDay: number): string
	local Total = math.floor(MinuteOfDay) % 1440
	local Hour24 = Total // 60
	local Minute = Total % 60
	local Suffix = if Hour24 < 12 then `AM` else `PM`
	local Hour12 = Hour24 % 12
	if Hour12 == 0 then Hour12 = 12 end
	return string.format(`%d:%02d %s`, Hour12, Minute, Suffix)
end

-- Parsed once.
local Segments = {} :: { Segment }
for _, Raw in Schedule.Segments do
	table.insert(Segments, {
		Name = Raw.Name;
		Kind = Raw.Kind;
		Start = SchoolTime.ParseTime(Raw.Start);
		End = SchoolTime.ParseTime(Raw.End);
	})
end

local SchoolStart = SchoolTime.ParseTime(Schedule.SchoolHours.Start)
local SchoolEnd = SchoolTime.ParseTime(Schedule.SchoolHours.End)

SchoolTime.Segments = Segments

function SchoolTime.SecondsPerGameMinute(): number
	-- The server may override the speed for testing (SchoolClock.SetSpeed).
	local Clock = ReplicatedStorage:FindFirstChild(`SchoolClock`)
	local Override = Clock and Clock:GetAttribute(`RealSecondsPerGameHour`)
	return (Override or Schedule.RealSecondsPerGameHour) / 60
end

function SchoolTime.GetSegment(MinuteOfDay: number): (Segment, number)
	for Index, Segment in Segments do
		if MinuteOfDay >= Segment.Start and MinuteOfDay < Segment.End then
			return Segment, Index
		end
	end
	return Segments[#Segments], #Segments
end

function SchoolTime.IsSchoolHours(MinuteOfDay: number): boolean
	return MinuteOfDay >= SchoolStart and MinuteOfDay < SchoolEnd
end

-- Epoch: server time when in-game day 0 at 00:00 began. Now: workspace:GetServerTimeNow().
function SchoolTime.GetState(Epoch: number, Now: number): State
	local TotalMinutes = math.max(0, (Now - Epoch) / SchoolTime.SecondsPerGameMinute())
	local Day = math.floor(TotalMinutes / 1440)
	local MinuteOfDay = TotalMinutes - Day * 1440
	local Segment, Index = SchoolTime.GetSegment(MinuteOfDay)

	return {
		Day = Day;
		DayName = Schedule.DayNames[(Day % #Schedule.DayNames) + 1];
		MinuteOfDay = MinuteOfDay;
		Hour = MinuteOfDay / 60;
		ClockText = SchoolTime.FormatClock(MinuteOfDay);
		Segment = Segment;
		SegmentIndex = Index;
		MinutesLeft = Segment.End - MinuteOfDay;
		IsSchoolHours = SchoolTime.IsSchoolHours(MinuteOfDay);
	}
end

---| Night windows (2.22.0, Phase 0) |---
-- Every system that asks "is it night?" names one of these windows instead of keeping its own hours.
-- School-clock hours (the same as Lighting.ClockTime). From is inclusive; the window wraps past midnight.
SchoolTime.Windows = {
	Dusk  = { From = 18.5; To = 6.5 };  -- lamps, ambience and region night text (Config.Ambience, Config.Regions)
	Dark  = { From = 19.5; To = 6 };    -- what students see and feel (AI.Senses, StudentBrain, the Spotted lantern)
	Prowl = { From = 19.5; To = 5.5 };  -- beasts and wild wolves are out (Config.Beasts, Features.WildWolves)
	Night = { From = 20; To = 6 };      -- the night proper: races, the moon, hunger, rites, the bite, the clock HUD
	Late  = { From = 21; To = 6 };      -- night chill (Config.Kit.Chill), the schedule's Night segment
}

function SchoolTime.InWindow(Hour: number?, Name: string?): boolean
	if typeof(Hour) ~= `number` then return false end
	local W = SchoolTime.Windows[Name or `Night`]
	assert(W, `SchoolTime: no night window '{Name}'`)
	return Hour >= W.From or Hour < W.To
end

function SchoolTime.IsNight(Hour: number?): boolean
	return SchoolTime.InWindow(Hour, `Night`)
end

-- The darkest window the hour is in: "Late", "Night", "Dark", "Dusk", or "Day".
function SchoolTime.Phase(Hour: number?): string
	for _, Name in { `Late`, `Night`, `Dark`, `Dusk` } do
		if SchoolTime.InWindow(Hour, Name) then return Name end
	end
	return `Day`
end

-- School calendar: a week is the schedule's school days (DayNames), a term is 12 weeks, a year is 3 terms (all 1-based).
SchoolTime.WeeksPerTerm = 12
SchoolTime.TermsPerYear = 3
function SchoolTime.Calendar(Day: number): { Week: number, Term: number, Year: number, WeekCount: number }
	local Weeks = Day // #Schedule.DayNames
	local Terms = Weeks // SchoolTime.WeeksPerTerm
	return {
		Week = Weeks % SchoolTime.WeeksPerTerm + 1;
		Term = Terms % SchoolTime.TermsPerYear + 1;
		Year = Terms // SchoolTime.TermsPerYear + 1;
		WeekCount = Weeks + 1;
	}
end

-- Epoch that makes "now" read as the given in-game day + time.
function SchoolTime.EpochFor(Now: number, Day: number, MinuteOfDay: number): number
	return Now - (Day * 1440 + MinuteOfDay) * SchoolTime.SecondsPerGameMinute()
end

return SchoolTime
