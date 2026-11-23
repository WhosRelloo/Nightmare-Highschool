--[[ (2.37) Notoriety: the Bells (spec docs/superpowers/specs/2026-11-20-notoriety-timetable-discipline-ui-design.md §3).
	Read by Functions.Notoriety (pure maths) and Services.School.Notoriety. Templates with {Where} are plain strings. ]]
return {
	-- Heat a witnessed misdeed adds (§3.2)
	Heat = { Truancy = 12; Trespassing = 20; Curfew = 20; Vandalism = 15; Fighting = 25; Contraband = 10; Exposure = 30; AssaultStaff = 45 };
	-- the Discipline violation booked for a misdeed when it isn't its own name
	BookAs = { Curfew = "Trespassing"; AssaultStaff = "Fighting" };
	NightGain = 1.5;        -- 22:00 to 06:00
	ProbationGain = 1.25;   -- Probation or Suspension
	Tiers = { 10, 25, 45, 70, 90 };
	TierNames = { "Murmur", "Noticed", "Named", "Hunted", "The Tolling" };
	TierBonus = { 0, 0, 1, 2, 3 };
	-- cooling (§3.4), per second
	SearchSeconds = 30;
	CoolSearch = 1.5;
	CoolQuiet = 3;
	HideMult = 2;           -- lockers, the Dorms, off campus
	AlibiMult = 3;          -- in your class room during class, or serving detention
	SearchRadius = { Min = 30; Max = 120 };
	-- identification (§3.5, R2: the face only)
	FaceSeenRange = 25;
	FaceLitSeconds = 2;
	-- escalation (§3.3)
	HuntTier = 3;
	ConvergeTier = 4;
	TollTier = 5;
	DisturbancePA = "A disturbance in {Where}. Staff, please attend.";
	TollPA = "All staff: a student is loose in {Where}. Find them.";
	-- summons (§3.8)
	SummonsLimit = 3;
	SummonsDays = 1;
	Tick = 0.25;
}
