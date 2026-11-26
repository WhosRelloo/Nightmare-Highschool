--[[
	Classes + attendance rules (shared).

	Periods maps each Class segment name in Config.SchoolSchedule to a subject and a room
	(RoomId attribute on the room model / Zone part under workspace.School).
	Everyone has the same timetable for now; personal timetables can come later.
	Subjects are placeholders: the concept doc doesn't name any.
]]

return {
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
