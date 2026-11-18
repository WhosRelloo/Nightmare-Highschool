--[[
	Discipline rules (shared).

	Violations add points. The ladder level comes from the point total, except Probation and
	Suspension, which last a set number of in-game days once reached. Points come back down
	through good attendance, daily decay, and serving detention. Nothing is permanent.
]]

return {
	-- Lowest point total for each level (checked from the top).
	Levels = {
		{ Name = `Clear`,      MinPoints = 0 };
		{ Name = `Warning`,    MinPoints = 2 };
		{ Name = `Detention`,  MinPoints = 5 };
		{ Name = `Probation`,  MinPoints = 10 };
		{ Name = `Suspension`, MinPoints = 16 };
	};

	Violations = {
		Tardy            = { Points = 1; Text = `Late to class` };
		LeftEarly        = { Points = 2; Text = `Left class early` };
		Absent           = { Points = 3; Text = `Skipped class` };
		Truancy          = { Points = 2; Text = `Caught out of class by a hall monitor` };
		Fighting         = { Points = 4; Text = `Fighting on school grounds` };
		Contraband       = { Points = 3; Text = `Caught with brass knuckles (confiscated)` }; -- (2.14.0) HallMonitor
		SkippedDetention = { Points = 4; Text = `Walked out of detention` };
		Vandalism        = { Points = 3; Text = `Caught painting on school walls` };
		Trespassing      = { Points = 3; Text = `Caught in a restricted area` };
	};

	Recovery = {
		PresentClass = 1;          -- points removed for each Present class
		DailyDecay = 2;            -- points removed per in-game day (applied for offline days too)
		ServedDetention = 4;       -- points removed for completing a detention
	};

	ProbationDays = 2;             -- in-game days on probation after reaching it
	SuspensionDays = 1;            -- in-game days suspended after reaching it
	PointsAfterSuspension = 8;     -- points are reset to this when a suspension ends

	RecentLimit = 20;              -- recent violations kept in saved data

	--| Witnesses |--
	Witness = {
		RecognizeRange = 25;       -- a witness recognises someone within this distance
		FightCooldown = 10;        -- seconds between Fighting reports for the same attacker
	};

	--| Hall monitors |--
	HallMonitor = {
		Count = 1;
		WalkSpeed = 7;             -- patrol pace (the walk clip plays at speed / 5.3, so the feet keep to the ground)
		ChaseSpeed = 15;           -- slower than a sprinting student, so escaping is possible
		SightRange = 45;
		FieldOfView = 140;         -- degrees (truancy needs the student in front; fights are heard)
		CatchRange = 6;
		GiveUpSeconds = 15;
		LoseSightSeconds = 3;
		MaxChaseDistance = 70;     -- from where the chase started
		WaypointTimeout = 8;       -- seconds before skipping a waypoint it can't reach
		RespawnSeconds = 20;       -- after being knocked out / killed
		-- Segment kinds when monitors are on duty. Truancy is only checked during Class.
		DutyKinds = { BeforeSchool = true; Class = true; Passing = true; Break = true; Lunch = true; AfterSchool = true };
	};

	--| (2.8.1) A record with teeth |--
	Record = {
		ProbationRecognizeRange = 40; -- a monitor knows a student on Probation (or Suspension) from this far (else Witness.RecognizeRange)
		NoPassLevels = { Probation = true; Suspension = true }; -- hall passes are refused at these levels (Features.Kit)
		MaxDetentionsOwed = 3;        -- owed detentions stop piling up here (an admin can still add more)
	};

	--| Detention |--
	Detention = {
		Room = `R106`;
		TrashCount = 5;            -- pieces to clean up per session
		LeaveGraceSeconds = 20;    -- real seconds you may step out before it counts as walking out
	};
}
