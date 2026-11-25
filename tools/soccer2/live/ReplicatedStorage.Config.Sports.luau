--[[
	Sports (Config): clubs, ranks, rewards, race perks and per-sport tuning. Numbers are a PROPOSAL.
	Spec: docs/superpowers/specs/2026-10-30-sports-design.md
	Saved per student: PlayerData.Sports = { Club, ClubExp, Record = { [sport] = { W, L } }, Drills = { [drill] = best } }
]]

local rgb = Color3.fromRGB
local Sports = {}

Sports.Clubs = {
	Basketball = { Id = `Basketball`; Name = `Night Ravens`; Sport = `Basketball`; Coach = `Varga`; Color = rgb(120, 70, 160); Short = `Ravens` };
	Soccer = { Id = `Soccer`; Name = `Grave Rovers`; Sport = `Soccer`; Coach = `Mallory`; Color = rgb(70, 140, 90); Short = `Rovers` };
	Football = { Id = `Football`; Name = `Iron Wardens`; Sport = `Football`; Coach = `Dunmore`; Color = rgb(170, 60, 50); Short = `Wardens` };
}
Sports.Ranks = {
	{ Name = `Rookie`; Min = 0 }, { Name = `Starter`; Min = 150 }, { Name = `Varsity`; Min = 500 }, { Name = `Captain`; Min = 1200 },
}
Sports.ClubExp = { Drill = 10; DrillBest = 10; Played = 25; Won = 25; Mvp = 15 }
Sports.Rewards = { Played = { Yen = 8; Popularity = 1 }; Won = { Yen = 12; Popularity = 2 } }
Sports.ClubHours = { From = 12; To = 20 }      -- ranked club matches count between these in-game hours
Sports.Teams = {
	A = { Name = `Crimson`; Color = rgb(190, 50, 60) };
	B = { Name = `Ash`; Color = rgb(150, 150, 170) };
}

-- small race edges, sports only (Services.Sports.* reads these)
Sports.RacePerks = {
	Vampire = { NightAccuracy = 0.06 };
	Werewolf = { FullMoonStamina = 0.15 };
	Ghoul = { StripResist = 0.15 };
	Wraith = { Reach = 0.08 };
	Human = { StaminaRegen = 0.12 };
	Priest = { PassAccuracy = 0.06 };
}
Sports.StatScale = { Might = 0.003; Grit = 0.005; Wits = 0.004 }   -- per stat point

Sports.Stamina = { Max = 100; RegenPerSecond = 14; Sprint = 18; Move = 9; Dive = 20 }

Sports.Basketball = {
	MinPerSide = 1; MaxPerSide = 5; HalfCourtUpTo = 2;      -- 1v1 and 2v2 play one hoop
	WinScore = 21; HalfSeconds = 240; ShotClock = 24; ResetAfterReach = 14;
	Countdown = 10; Halftime = 10;
	Shot = {
		PerfectHold = 0.62;       -- seconds held for a perfect release
		Green = 0.075;            -- ± seconds counted as green (before contest / Wits)
		Okay = 0.17;              -- ± seconds counted as okay
		MakeGreen = 0.92; MakeOkay = 0.48; MakeBad = 0.06;
		ContestRange = 6;         -- defenders within this many studs reduce the green window
		ContestShrink = 0.7;      -- a defender right on you takes away 70% of the green window
		LongRange = 30;           -- beyond this distance from the rim the make chance falls off
		Layup = 6; Dunk = 4; DunkMight = 10; LayupMake = 0.82; DunkMake = 0.95;
		ThreeRadius = 22;         -- arc radius from the rim (studs)
	};
	Pass = { Range = 60; Speed = 70 };
	Steal = { Reach = 4; Cooldown = 1.2; Base = 0.35; StandingBonus = 0.2; MoveImmune = 0.35; ReachInCooldown = 2.4 };
	Block = { Reach = 3.2; Window = 0.4; Chance = 0.6; JumpCooldown = 0.9 };   -- one block roll per jump
	Moves = {
		Crossover = { Key = `Q`; Dash = 7; Time = 0.32 };
		BehindBack = { Key = `R`; Dash = 6; Time = 0.36 };
		Spin = { Key = `F`; Dash = 8; Time = 0.42 };
		Between = { Key = `C`; Dash = 4; Time = 0.28 };
		-- euro step: a long side step on the drive; shoot (E) within Window s for a layup from Reach studs farther out,
		-- with the contest cut to ContestCut
		Euro = { Key = `Z`; Dash = 9; Time = 0.45; Window = 0.9; Reach = 4; ContestCut = 0.5 };
	};
	ChainWindow = 0.35; CancelWindow = 0.2;
	Post = { Range = 4; Speed = 4; Fade = 0.55; Hook = 0.62 };
	PickupRange = 3.5;
}

Sports.Soccer = {
	MinPerSide = 1; MaxPerSide = 5; KeeperFrom = 3;            -- keeper pads count from 3v3
	WinScore = 10; MercyLead = 5; HalfSeconds = 240; Countdown = 10; Halftime = 10;
	Kick = {
		ChargeTime = 0.36;          -- seconds of holding for a full-power shot
		MinPower = 0.3; MaxHold = 1.6;
		Speed = 120;                -- studs/s at full power
		Lift = 24;                  -- extra upward speed for flat aims (lift * (0.9 - |aim.y|))
		AimYMin = 0.04; AimYMax = 0.85; MaxUp = 90;
		Curve = 40; CurveTime = 0.7; CurveBack = 0.25;   -- side push at full charge, then bends back
		Cooldown = 0.45;
		KickWindow = 0.3;           -- a kick pressed without the ball strikes a ball arriving within this (volley)
		VolleyPower = 1.0; HeaderPower = 0.45;
	};
	Pass = { Range = 90; Cooldown = 0.8; MinPower = 0.25; MaxPower = 1.1; Per = 1 / 55 };   -- power = distance * Per
	Tackle = { Reach = 5.5; Window = 0.65; Dash = 26; Stamina = 20; Cooldown = 2; MissStun = 1.2; HitStun = 0.9 };
	Dribble = { Dash = 22; Time = 0.4; Stamina = 11; Cooldown = 2; AnkleRagdoll = 1.9 };
	Feint = { Window = 0.45; Cooldown = 4.5; Stamina = 8 };
	Keeper = { Reach = 6.5; DiveDash = 34; DiveTime = 0.5; DiveCooldown = 1.9; HoldMax = 6; ThrowCharge = 0.7; ThrowSpeed = 80 };
	PickupRange = 4.2; DodgeOnPickup = 0.13;
	MaxSpeed = 75;              -- studs/s between ticks; faster than any dash or sprint, so it means a teleport
	Bloodrush = { Min = 45; Seconds = 18; Steal = 10; Ankles = 10; Goal = 20; OnTarget = 5; Speed = 0.1; Power = 0.1; Drain = 0.7 };   -- Speed: +10% walk speed (client)
	GoalPause = 3.5;            -- seconds of celebration before kickoff
}

-- Football (Sports 1.2): plays like Football Fusion 2 with an optional quick play call. Field facts come from the venue
-- (GoalLineWest/East, YardStuds attributes on workspace.Sports.Field). Yards below are field yards (2 studs each).
Sports.Football = {
	MinPerSide = 2; MaxPerSide = 5;
	WinScore = math.huge; MercyLead = 35; ScoreWord = `point`; StartWord = `kickoff`;
	HalfSeconds = 240; Countdown = 10; Halftime = 10;
	Huddle = 6;               -- seconds to call a play (optional)
	PlayClock = 20;           -- seconds to snap once lined up
	RushCount = 3;            -- "Mississippi" seconds before defenders may cross the line
	DeadPause = 2.2;          -- seconds between the end of a play and the next huddle
	ScorePause = 3;           -- celebration after a touchdown / field goal / safety
	ConvertPick = 6;          -- seconds to pick the extra point (1) or a 2-point try (2)
	ToGo = 10; Downs = 4;
	TouchbackYard = 12;       -- a touchback puts the ball on your own 12
	KickoffYard = 20;         -- kickoffs from your own 20
	FieldGoalRange = 30;      -- a field goal can be tried from inside 30 yards of the goal line
	TwoPointYard = 5;
	Penalty = 5;              -- false start / delay of game
	MaxSpeed = 75;            -- studs/s between ticks; faster means a teleport
	Throw = {
		-- power levels (Football Fusion style): the QB sets a power with Z / C, then clicks to throw at it.
		-- Low power floats a lofted spiral; high power is a flat, fast bullet.
		MinPower = 10; MaxPower = 100; Step = 5; DefaultPower = 60;
		MinSpeed = 45; MaxSpeed = 115;   -- launch speed at power 0 and 100
		Gravity = 110;        -- passes and kicks float: a lift force cancels part of the world's gravity
		Spread = 2.2;         -- studs of random miss at 40 studs (accuracy perks shrink it)
		Spin = { Min = 18; Max = 45 };   -- the spiral (radians/s about the ball's long axis), by power
		Cooldown = 0.6;
	};
	Catch = {
		Radius = 3.75;        -- studs from the catcher's shoulders to the ball: be under it, not near it
		Window = 0.25;        -- a click catches what comes in reach within this (the server also looks back for network delay)
		Spam = 0.8;           -- a whiffed click locks the next one out this long
		DefenderRadius = 3.25; -- interceptions are a little harder
	};
	Tackle = { Touch = 3.4; HitStick = 4.6; HitWindow = 0.35; HitDash = 30; HitCooldown = 2.5; MissStun = 1; Fumble = 0.25; Stamina = 15 };
	Juke = { Dash = 30; Time = 0.2; Break = 0.25; Cooldown = 1.2; Stamina = 12; Stun = 0.8 };
	Spin = { Break = 0.3; Cooldown = 1.5; Stamina = 14 };
	-- a free leap (Football Fusion style): your run's momentum plus a push, a little lift, any direction, mid-air too;
	-- you can steer a bit in the air; Float cancels part of gravity in flight (a low, flat layout). Air = the time in flight (reach bonus lasts all of it), Down = the time on the turf after
	Dive = { Speed = 36; Carry = 1.25; MaxSpeed = 52; Lift = 28; Float = 0.5; Air = 0.5; Reach = 1.5; Down = 0.4; Cooldown = 1.0; Stamina = 15 };
	Swat = { Reach = 6; Cooldown = 1.4 };
	Handoff = { Range = 6 };
	Kick = {
		ChargeTime = 1.0; MaxHold = 2.0;
		MinSpeed = 40; MaxSpeed = 120;
		Angle = { Kickoff = 40; Punt = 50; FieldGoal = 32; Onside = 12 };
		AimCone = 25;         -- degrees either side of straight downfield
		AutoAfter = 10;       -- an untaken kickoff goes on its own
		OnsideYards = 5;      -- an onside kick is live once it has gone this far
	};
	-- quick plays: the QB presses 1-6 in the huddle. Routes per receiver slot (outside first), as
	-- { forward yards, inward yards } waypoints from the receiver's spot (negative inward = toward the sideline)
	Plays = {
		{ Name = `Slants`; Routes = { { { 2, 0 }, { 8, 6 } } } };
		{ Name = `Verticals`; Routes = { { { 26, 0 } } } };
		{ Name = `Posts`; Routes = { { { 8, 0 }, { 22, 8 } }, { { 10, 0 }, { 8, 0 } } } };
		{ Name = `Curls`; Routes = { { { 10, 0 }, { 8, 1 } } } };
		{ Name = `Outs`; Routes = { { { 6, 0 }, { 6, -9 } }, { { 12, 0 }, { 12, -8 } } } };
		{ Name = `Screen`; Routes = { { { -1, 0 }, { -1, 5 } }, { { 20, 0 } } } };
	};
	Coverage = { `Man`, `Zone` };
}

-- the race colour of a Bloodrush aura
Sports.RaceAura = {
	Vampire = rgb(170, 20, 40); Werewolf = rgb(170, 190, 230); Ghoul = rgb(120, 160, 90);
	Wraith = rgb(150, 220, 235); Human = rgb(230, 190, 90); Priest = rgb(250, 240, 200);
}

-- (soccer-2.0) Animation slots: { Id = published asset id; Clip = a ReplicatedStorage.NHSoccerClips name; Was = the 1.1 id }.
-- Id wins. Without one, Studio plays the baked Clip (tools/soccer2/bake/bake_soccer_clips.lua) and a live server plays Was,
-- else the procedural pose in Controllers.Gui.Soccer. The owner publishes the NHSoccerClips copies to the group (15981569)
-- and puts each id here (tools/soccer2/PUBLISH_LIST.md). All R6. The owner lifted 1.1's "no movement clips except the
-- slide" for soccer matches (2026-11-24). Spec: docs/superpowers/specs/2026-11-24-soccer-2-0-design.md §2.
Sports.SoccerAnims = {
	KickRun = { Clip = `Strike Foward Jog_R6` };          -- the running shot (6+ studs/s)
	Kick = { Clip = `KickSoccerball_Right` };              -- the standing / charged shot (the right-foot mirror)
	Pass = { Clip = `Soccer Pass_R6` };
	Volley = { Clip = `Scissor Kick_R6` };
	Dribble = { Clip = `Soccer Spin_R6` };
	Feint = { Clip = `Soccer Spin_R6` };
	Tackle = { Clip = `Soccer Tackle_R6`; Was = 98978935956373 };   -- was "SLIDING"
	Tackled = { Clip = `Soccer Tackled_R6` };
	Tackled2 = { Clip = `Soccer Tackled2_R6` };
	Trip = { Clip = `Soccer Trip_R6` };                    -- broken ankles, or a tackle into a feint
	Fallen = { Clip = `Fallen Idle_R6` };                  -- the rest of a stun after a fall
	KeeperDiveLeft = { Clip = `Goalkeeper Diving SaveLeft_R6` };
	KeeperDiveRight = { Clip = `Goalkeeper Diving SaveRigh_R6` };
	KeeperCatch = { Clip = `Goalkeeper Catch_R6` };
	KeeperCatchIdle = { Clip = `Goalkeeper CatchIdle_R6` };
	KeeperIdle = { Clip = `Goalkeeper Idle_R6` };
	KeeperStepLeft = { Clip = `Goalkeeper StepLeft_R6` };
	KeeperStepRight = { Clip = `Goalkeeper StepRight_R6` };
	Idle = { Clip = `Soccer Idle_R6` };                    -- the match idle (Controllers.Character.SoccerPack)
	IdleBall = { Clip = `Offensive Idle_R6` };             -- with the ball
	Jog = { Clip = `Jog Forward_R6` };                     -- the match walk
	JogBack = { Clip = `Jog Backward_R6` };                -- the backpedal
	Chip = { Clip = `Chip_R6` };                           -- 2.1
	Stall = { Clip = `Stall Soccerball_R6` };              -- 2.1
	Penalty = { Clip = `Soccer Penalty Kick_R6` };         -- 2.2
	KeeperThrow = { Id = 126461164655749 };                -- "Activate" (0.5 s, both arms forward)
	Celebrate = { Id = 73569467689521 };                   -- "Isagi Celebration" (cut after the goal pause)
}

Sports.Drills = {
	Shootaround = { Sport = `Basketball`; Name = `Shootaround`; Seconds = 60; Spots = 10; Text = `Score from each spot before time runs out.` };
	ConeDribble = { Sport = `Basketball`; Name = `Cone Dribble`; Text = `Weave the cones with dribble moves. Fastest time wins.` };
	TargetPractice = { Sport = `Soccer`; Name = `Target Practice`; Seconds = 60; Goal = 4; Text = `Hit the lit corner targets from behind the line.` };
	WallPasses = { Sport = `Soccer`; Name = `Wall Passes`; Seconds = 45; Goal = 8; Text = `Pass into the wall and control the rebound. Count your clean passes.` };
	RouteRunner = { Sport = `Football`; Name = `Route Runner`; Seconds = 75; Throws = 10; Goal = 6; Text = `Run the called route and catch the machine's throw. Six catches passes.` };
	QBTargets = { Sport = `Football`; Name = `QB Targets`; Seconds = 60; Goal = 10; Text = `Throw through the moving rings: 1, 2 or 3 points by distance. Ten points passes.` };
}

---| pure helpers |---

function Sports.RankFor(exp: number): (string, number)
	local Name, Index = Sports.Ranks[1].Name, 1
	for I, R in Sports.Ranks do
		if (exp or 0) >= R.Min then Name, Index = R.Name, I end
	end
	return Name, Index
end

function Sports.NextRank(exp: number)
	for _, R in Sports.Ranks do
		if (exp or 0) < R.Min then return R end
	end
	return nil
end

function Sports.Sanitize(raw)
	local out = { Club = nil; ClubExp = 0; Record = {}; Drills = {} }
	if type(raw) ~= `table` then return out end
	if type(raw.Club) == `string` and Sports.Clubs[raw.Club] then out.Club = raw.Club end
	if type(raw.ClubExp) == `number` and raw.ClubExp == raw.ClubExp then out.ClubExp = math.clamp(math.floor(raw.ClubExp), 0, 10 ^ 7) end
	if type(raw.Record) == `table` then
		for Sport in Sports.Clubs do
			local R = raw.Record[Sport]
			if type(R) == `table` then
				out.Record[Sport] = { W = math.clamp(math.floor(tonumber(R.W) or 0), 0, 10 ^ 6); L = math.clamp(math.floor(tonumber(R.L) or 0), 0, 10 ^ 6) }
			end
		end
	end
	if type(raw.Drills) == `table` then
		for Id in Sports.Drills do
			local V = raw.Drills[Id]
			if type(V) == `number` and V == V and V > 0 then out.Drills[Id] = math.min(V, 10 ^ 6) end
		end
	end
	return out
end

-- Perk value for a race (0 when none)
function Sports.Perk(race: string?, key: string): number
	local P = race and Sports.RacePerks[race]
	return P and P[key] or 0
end

return Sports
