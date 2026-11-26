--[[
	School clock + daily timetable (data only; shared by server and client).

	From the concept doc ("School Campus System"):
		- 5 real minutes = 1 in-game hour  -> 1 in-game day = 2 real hours
		- School hours last 4 in-game hours starting around 8 AM (20 real minutes)
		- School missions during school hours give 1.2x EXP
	Note: the doc also says school hours are "10% of the day", but 4 of 24 hours is ~17%.
	The explicit 8 AM + 4 hours is used here; change SchoolHours to adjust.

	Times are "HH:MM" in 24-hour in-game time.
]]

return {
	RealSecondsPerGameHour = 300;   -- 5 real minutes per in-game hour

	-- "Global": every server shows the same in-game time (concept: "Global In-Game Time"),
	-- counted from GlobalEpoch (a Unix timestamp). Needed so a player who rejoins another
	-- server lands in the same class period.
	-- "Local": each server starts at StartTime when it boots (handy for testing).
	ClockMode = `Global`;
	GlobalEpoch = 1704067200;       -- 2024-01-01 00:00 UTC = Monday 00:00 in-game
	StartTime = `07:30`;            -- Local mode only

	SchoolHours = { Start = `08:00`; End = `12:00` };
	SchoolHoursExpMultiplier = 1.2;

	-- Days cycle in this order. The concept wants the 8 AM boost every in-game day,
	-- so there is no weekend by default.
	DayNames = { `Monday`, `Tuesday`, `Wednesday`, `Thursday`, `Friday` };

	SyncLighting = true;            -- drive Lighting.ClockTime from the school clock

	-- Kind: Night | Morning | BeforeSchool | Class | Passing | Break | Lunch | AfterSchool | Evening
	-- Class periods are what attendance will check later.
	Segments = {
		{ Name = `Night`,         Kind = `Night`,        Start = `00:00`, End = `06:00` };
		{ Name = `Morning`,       Kind = `Morning`,      Start = `06:00`, End = `07:30` };
		{ Name = `Before School`, Kind = `BeforeSchool`, Start = `07:30`, End = `08:00` };
		{ Name = `Homeroom`,      Kind = `Class`,        Start = `08:00`, End = `08:20` };
		{ Name = `Period 1`,      Kind = `Class`,        Start = `08:20`, End = `09:00` };
		{ Name = `Passing`,       Kind = `Passing`,      Start = `09:00`, End = `09:05` };
		{ Name = `Period 2`,      Kind = `Class`,        Start = `09:05`, End = `09:45` };
		{ Name = `Break`,         Kind = `Break`,        Start = `09:45`, End = `10:00` };
		{ Name = `Period 3`,      Kind = `Class`,        Start = `10:00`, End = `10:40` };
		{ Name = `Passing`,       Kind = `Passing`,      Start = `10:40`, End = `10:45` };
		{ Name = `Period 4`,      Kind = `Class`,        Start = `10:45`, End = `11:25` };
		{ Name = `Lunch`,         Kind = `Lunch`,        Start = `11:25`, End = `12:00` };
		{ Name = `After School`,  Kind = `AfterSchool`,  Start = `12:00`, End = `17:00` };
		{ Name = `Evening`,       Kind = `Evening`,      Start = `17:00`, End = `21:00` };
		{ Name = `Night`,         Kind = `Night`,        Start = `21:00`, End = `24:00` };
	};
}
