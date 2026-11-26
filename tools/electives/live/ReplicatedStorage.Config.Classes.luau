--[[
	Classes + attendance rules (shared).

	Periods maps each Class segment name in Config.SchoolSchedule to a subject and a room
	(RoomId attribute on the room model / Zone part under workspace.School).
	Everyone has the same timetable for now; personal timetables can come later.
	Subjects are placeholders: the concept doc doesn't name any.

	(Electives) Tuesday and Thursday periods 3 and 4 are elective slots: each player has their term pick there
	(Config.Electives, Services.School.Electives), or Study Hall. Ask Classes.For(SegmentName, Day, PickOrPlayer)
	for the class a player has in a slot; Periods stays the base timetable.
]]

local Electives = if script and script.Parent and script.Parent:FindFirstChild(`Electives`) then require(script.Parent.Electives) else require("Electives")
local SchoolDays = 5 -- Config.SchoolSchedule.DayNames (Monday..Friday); weekday = Day % SchoolDays

local Classes = {
	Periods = {
		[`Homeroom`] = { Subject = `Homeroom`;    Room = `R101` };
		[`Period 1`] = { Subject = `Mathematics`; Room = `R102` };
		[`Period 2`] = { Subject = `Chemistry`;   Room = `R103` };
		[`Period 3`] = { Subject = `English`;     Room = `R104` };
		[`Period 4`] = { Subject = `History`;     Room = `R105` };
	};

	Rooms = {
		R101 = `Room 101`;
		R102 = `Room 102`;
		R103 = `Room 103`;
		R104 = `Room 104`;
		R105 = `Room 105`;
	};

	-- All times are in-game minutes (1 in-game minute = 5 real seconds by default).
	Attendance = {
		GraceMinutes = 3;           -- arriving up to this late still counts as Present
		TardyCutoffFraction = 0.5;  -- arriving after this share of the period counts as Absent
		StayFraction = 0.6;         -- must be in the room this share of the time after arriving, else Left Early
		LateJoinMinMinutes = 10;    -- joined the game mid-class with less time than this left = Excused
		RecentLimit = 20;           -- how many recent records are kept in saved data

		Rewards = {                 -- Yen per result (one payout per class period)
			Present = 5;
			Tardy = 2;
		};
	};
}

Classes.ElectiveSlots = {
	Days = { [1] = true; [3] = true };                       -- Tuesday, Thursday
	Segments = { [`Period 3`] = true; [`Period 4`] = true };
}
Classes.StudyHall = { Subject = `Study Hall`; Room = `R101` }

function Classes.IsElectiveSlot(SegmentName: string, Day: number): boolean
	return typeof(Day) == `number` and Classes.ElectiveSlots.Segments[SegmentName] == true and Classes.ElectiveSlots.Days[Day % SchoolDays] == true
end

-- The class a player has in a slot: { Subject, Room, Elective }, or nil if the segment isn't a class.
-- PickOrPlayer: an elective id, or a Player (reads its ElectivePick attribute, set by Services.School.Electives).
function Classes.For(SegmentName: string, Day: number, PickOrPlayer: any)
	local Base = Classes.Periods[SegmentName]
	if not Base then return nil end
	if not Classes.IsElectiveSlot(SegmentName, Day) then
		return { Subject = Base.Subject; Room = Base.Room; Elective = false }
	end
	local Pick = PickOrPlayer
	if typeof(PickOrPlayer) == `Instance` then Pick = PickOrPlayer:GetAttribute(`ElectivePick`) end
	local Def = Electives.Get(Pick)
	if Def and Def.Open then
		return { Subject = Def.Id; Room = Def.Room; Elective = true }
	end
	return { Subject = Classes.StudyHall.Subject; Room = Classes.StudyHall.Room; Elective = true }
end

return Classes
