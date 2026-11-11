--[[
	Config.Training (shared). ReplicatedStorage.Config.Training   (training minigames, phase 1: 2026-11-11)
	docs/Training.md, docs/Training-Design-Note.md. Server: Services.Features.Training. Client: Controllers.Gui.Training.

	Three areas (Arms, Torso, Legs), each 0-20, trained one at a time at a gym station. One minigame for all four main
	stations: a ring shrinks onto the brass mark of a gauge and you press on the mark (Good / Great / Perfect).
	Everything here is shared so the client can draw the plan the server rolled; the server alone scores it.
]]
local Training = {}

Training.MaxLevel = 20
Training.Areas = { `Arms`, `Torso`, `Legs` }
Training.AreaInfo = {
	Arms = { Name = `Arms`; Parts = { `Left Arm`, `Right Arm` }; Icon = `TrainIconArms`; Stat = `Might` };
	Torso = { Name = `Torso`; Parts = { `Torso` }; Icon = `TrainIconTorso`; Stat = `Grit` };
	Legs = { Name = `Legs`; Parts = { `Left Leg`, `Right Leg` }; Icon = `TrainIconLegs`; Stat = `Speed` };
}

-- The stations. Anim ids are the owner's (Features.AmbientNpcs ANIM, plus the new squat pair).
-- Rep: played once per good-or-better rep. Idle: held between reps. SitUp has one looping rep, so its idle holds
-- the rep's first frame (IdleFromRep).
Training.Stations = {
	PushUp = { Name = `Push-ups`; Area = `Arms`; Icon = `TrainStationPushUp`; Idle = 111737875654076; Rep = 112288220550648; Load = `Vest` };
	PullUp = { Name = `Pull-ups`; Area = `Arms`; Icon = `TrainStationPullUp`; Idle = 134151351487837; Rep = 115584556914404; Load = `Vest`; Hang = true };
	SitUp = { Name = `Sit-ups`; Area = `Torso`; Icon = `TrainStationSitUp`; Rep = 132757288791974; IdleFromRep = true; Load = `Belt`; CamSide = -1 };
	Squat = { Name = `Squats`; Area = `Legs`; Icon = `TrainStationSquat`; Idle = 119121474882852; Rep = 88777267068656; Load = `Sandbag` };
}
Training.StationOrder = { `PushUp`, `PullUp`, `SitUp`, `Squat` }

-- The HUD art (art/group-upload-training, 27 images: Blender PBR renders, art/ui/hud/make_training_pbr.py ->
-- blender_training_render.py -> finish_training_ui.py). Group 15981569 image ids by name, filled in after the owner's
-- bulk import. 0 = not imported yet: Controllers.Gui.Training draws kit stand-ins until then.
Training.Art = {
	TrainGauge = 0;
	TrainNeedle = 0;
	TrainRing = 0;
	TrainRingHeavy = 0;
	TrainRingFake = 0;
	TrainMarkGlow = 0;
	TrainRateGood = 0;
	TrainRateGreat = 0;
	TrainRatePerfect = 0;
	TrainRateMiss = 0;
	TrainIconArms = 0;
	TrainIconTorso = 0;
	TrainIconLegs = 0;
	TrainStationPushUp = 0;
	TrainStationPullUp = 0;
	TrainStationSitUp = 0;
	TrainStationSquat = 0;
	TrainBadgeStreak = 0;
	TrainBadgeBest = 0;
	TrainBadgeDaily = 0;
	TrainIconSore = 0;
	TrainGear = 0;
	TrainPlate = 0;
	TrainKey = 0;
	TrainBarFrame = 0;
	TrainBarFill = 0;
	TrainFlame = 0;
}

-- XP to go from area level L to L + 1 (about 540 to Lv 5, 2,200 to Lv 10, 11,400 to Lv 20)
function Training.ToNext(Level: number): number
	return math.floor(60 + 12 * Level ^ 1.6)
end
function Training.TotalTo(Level: number): number
	local T = 0
	for L = 0, Level - 1 do T += Training.ToNext(L) end
	return T
end

-- mesh steps: the level each step starts at. Steps 3 and 4 wait for new meshes (MeshStepsBuilt).
Training.StepLevels = { 5, 10, 15, 20 }
Training.MeshStepsBuilt = 2
function Training.StepFor(Level: number): number
	local S = 0
	for I, L in Training.StepLevels do if Level >= L then S = I end end
	return math.min(S, Training.MeshStepsBuilt)
end
function Training.NextStepLevel(Level: number): number?
	for I, L in Training.StepLevels do
		if Level < L and I <= Training.MeshStepsBuilt then return L end
	end
	return nil
end
-- paths -> Appearance builds
Training.PathBuild = { Average = `Average`; Conditioned = `Conditioned`; Heavy = `Heavy`; Lean = `Skinny` }
Training.BuildPath = { Average = `Average`; Conditioned = `Conditioned`; Heavy = `Heavy`; Skinny = `Lean` }

-- Difficulty by the trained area's level. Times in seconds; windows are half-widths.
Training.Tiers = {
	{ Name = `I`; From = 0; Approach = 1.50; Gap = 1.30; Jitter = 0; Perfect = 0.070; Great = 0.130; Good = 0.210; Reps = 14;
		Fake = 0; Heavy = 0; Hold = 0; Burnout = 0; Stamina = false; Load = 0; Xp = 1.0; Flicker = false };
	{ Name = `II`; From = 5; Approach = 1.30; Gap = 1.15; Jitter = 0; Perfect = 0.060; Great = 0.115; Good = 0.185; Reps = 16;
		Fake = 0.08; Heavy = 0.10; Hold = 0.8; Burnout = 0; Stamina = false; Load = 1; Xp = 1.15; Flicker = false };
	{ Name = `III`; From = 10; Approach = 1.12; Gap = 1.00; Jitter = 0.12; Perfect = 0.050; Great = 0.100; Good = 0.160; Reps = 18;
		Fake = 0.12; Heavy = 0.15; Hold = 1.0; Burnout = 0.25; Stamina = false; Load = 2; Xp = 1.3; Flicker = true };
	{ Name = `IV`; From = 15; Approach = 0.95; Gap = 0.90; Jitter = 0.18; Perfect = 0.042; Great = 0.085; Good = 0.140; Reps = 20;
		Fake = 0.14; Heavy = 0.20; Hold = 1.2; Burnout = 0.35; Stamina = true; Load = 3; Xp = 1.5; Flicker = true };
	{ Name = `V`; From = 20; Approach = 0.90; Gap = 0.85; Jitter = 0.20; Perfect = 0.038; Great = 0.078; Good = 0.130; Reps = 22;
		Fake = 0.15; Heavy = 0.22; Hold = 1.3; Burnout = 0.40; Stamina = true; Load = 3; Xp = 1.7; Flicker = true };
}
function Training.TierFor(Level: number)
	local T = Training.Tiers[1]
	for _, X in Training.Tiers do if Level >= X.From then T = X end end
	return T
end

Training.CountIn = 3.0             -- seconds of 3-2-1 before the first ring's travel starts
Training.FirstRingAt = 0.6         -- the first ring's target = CountIn + FirstRingAt + Approach
Training.Points = { Good = 1; Great = 2; Perfect = 3 }
Training.HeavyMult = 2
Training.ComboStep = 0.02
Training.ComboCap = 25
-- burnout sets: stamina from 100; the gap shrinks per rep
Training.Burnout = { Reps = 30; Shrink = 0.97; MinGap = 0.60; Xp = 1.25;
	Stamina = { Perfect = 4; Great = 0; Good = -6; Miss = -22; Feint = -22; Stray = -10 } }
-- tier IV+ normal sets: a miss costs stamina, four misses end the set
Training.SetStamina = { Perfect = 5; Great = 0; Good = 0; Miss = -25; Feint = -25; Stray = -10 }
Training.FakeBreakAt = 0.75        -- a feint shatters at 75% of its travel

-- retention and fairness
Training.DailyCap = 700            -- XP per area per UTC day
Training.FreshMult = 2             -- the first completed set of each area each day
Training.StreakPer = 0.02
Training.StreakCap = 0.20
Training.StreakYen = { [3] = 60; [7] = 150; [14] = 300; [30] = 500 }
Training.Sore = { PerSet = 14; PerBurnout = 16; DecayEvery = 15; Max = 100; XpAtMax = 0.5 }
Training.Athletes = { PerSet = 1; DailyMax = 8 }
Training.MinRepsForSet = 4         -- a set with fewer counted reps gives no Fresh, streak, PB or standing

-- anti-cheat
Training.Check = { StationRange = 8; BeginGap = 2.0; FutureSlack = 0.6; MinPressGap = 0.08; StalePad = 20;
	BotHits = 10; BotSpread = 0.004 }

-- the ring plan: a pure function of the seed and the tier, so client and server agree
-- returns { Rings = { { T = target time from set start, Kind = "Normal"|"Fake"|"Heavy", Hold = s } }, Burnout, Duration }
function Training.Plan(Seed: number, Level: number)
	local T = Training.TierFor(Level)
	local R = Random.new(Seed)
	local Burn = T.Burnout > 0 and R:NextNumber() < T.Burnout
	local Count = if Burn then Training.Burnout.Reps else T.Reps
	local Gap = T.Gap
	local At = Training.CountIn + Training.FirstRingAt + T.Approach
	local Rings = {}
	local LastFake = false
	for I = 1, Count do
		local Kind = `Normal`
		local X = R:NextNumber()
		if I > 2 and not LastFake and X < T.Fake then
			Kind = `Fake`
		elseif I > 2 and X < T.Fake + T.Heavy and not Burn then
			Kind = `Heavy`
		end
		LastFake = Kind == `Fake`
		table.insert(Rings, { T = At; Kind = Kind; Hold = if Kind == `Heavy` then T.Hold else 0 })
		local G = Gap + (if T.Jitter > 0 then (R:NextNumber() * 2 - 1) * T.Jitter else 0)
		if Kind == `Heavy` then G += T.Hold end
		if Burn then Gap = math.max(Training.Burnout.MinGap, Gap * Training.Burnout.Shrink) end
		At += math.max(0.45, G)
	end
	local Last = Rings[#Rings]
	return { Rings = Rings; Burnout = Burn; Duration = Last.T + Last.Hold + T.Good + 0.4; Tier = T.Name;
		Approach = T.Approach; Stamina = Burn or T.Stamina }
end

-- score a set: Presses = { { T = press time, R = release time? } } (seconds from set start, sorted).
-- Returns the result table the server trusts (and the client previews with the same code).
function Training.Score(PlanT, Level: number, Presses)
	local T = Training.TierFor(Level)
	local Rings = PlanT.Rings
	local Used = {}
	local Res = { Perfect = 0; Great = 0; Good = 0; Miss = 0; Feint = 0; Stray = 0; Reps = 0; Combo = 0; BestCombo = 0;
		Points = 0; Offsets = {}; Ended = nil; Per = {} }
	local Stam = 100
	local StamRules = if PlanT.Burnout then Training.Burnout.Stamina else Training.SetStamina
	-- each ring takes the first unused press inside its Good window
	local Events = {}
	for I, Ring in Rings do
		local Best, BestJ = nil, nil
		for J, P in Presses do
			if not Used[J] then
				local D = P.T - Ring.T
				if math.abs(D) <= T.Good and (Best == nil or math.abs(D) < math.abs(Best)) then Best, BestJ = D, J end
			end
		end
		if BestJ then Used[BestJ] = true end
		table.insert(Events, { At = Ring.T; Ring = Ring; I = I; D = Best; P = BestJ and Presses[BestJ] or nil })
	end
	for J, P in Presses do
		if not Used[J] then table.insert(Events, { At = P.T; Stray = true }) end
	end
	table.sort(Events, function(A, B) return A.At < B.At end)
	local Combo = 0
	for _, E in Events do
		if Res.Ended then break end
		local Kind
		if E.Stray then
			Kind = `Stray`
		elseif E.Ring.Kind == `Fake` then
			Kind = if E.D ~= nil then `Feint` else nil   -- letting a feint pass is right: no event
		elseif E.D == nil then
			Kind = `Miss`
		else
			local A = math.abs(E.D)
			Kind = if A <= T.Perfect then `Perfect` elseif A <= T.Great then `Great` else `Good`
			if E.Ring.Kind == `Heavy` then
				local Rel = E.P and E.P.R
				if not (Rel and Rel - E.P.T >= E.Ring.Hold - 0.05) then Kind = `Miss` end   -- let go too early
			end
		end
		if Kind then
			Res[Kind] += 1
			if Kind == `Perfect` or Kind == `Great` or Kind == `Good` then
				Combo += 1
				Res.Reps += 1
				local Mult = 1 + Training.ComboStep * math.min(Combo, Training.ComboCap)
				local Pts = Training.Points[Kind] * Mult * (if E.Ring.Kind == `Heavy` then Training.HeavyMult else 1)
				Res.Points += Pts
				table.insert(Res.Offsets, E.D)
			else
				Combo = 0
			end
			Res.BestCombo = math.max(Res.BestCombo, Combo)
			if PlanT.Stamina then
				Stam = math.min(100, Stam + (StamRules[Kind] or 0))
				if Stam <= 0 then Res.Ended = E.At end
			end
			table.insert(Res.Per, { I = E.I; Kind = Kind })
		end
	end
	Res.Combo = Combo
	Res.Stamina = Stam
	Res.Points *= T.Xp * (if PlanT.Burnout then Training.Burnout.Xp else 1)
	return Res
end

function Training.Sanitize(Raw)
	local Out = { Arms = {}; Torso = {}; Legs = {}; Fed = 0; LastTrained = 0; Day = -1; Streak = 0; StreakBest = 0;
		StreakPaid = {}; Fresh = {}; DayXp = {}; XpDay = -1; Best = {}; Tut = false; Athletes = { Day = -1; N = 0 }; Seeded = false }
	local R = if typeof(Raw) == `table` then Raw else {}
	local function num(V, Lo, Hi, D) V = tonumber(V) if not V or V ~= V then return D end return math.clamp(V, Lo, Hi) end
	for _, A in Training.Areas do
		local S = if typeof(R[A]) == `table` then R[A] else {}
		Out[A] = {
			Level = math.floor(num(S.Level, 0, Training.MaxLevel, 0));
			Xp = math.floor(num(S.Xp, 0, 1e7, 0));
			Path = if Training.PathBuild[S.Path] then S.Path else `Average`;
			Sore = num(S.Sore, 0, Training.Sore.Max, 0);
			SoreAt = num(S.SoreAt, 0, 1e12, 0);
		}
		Out.Fresh[A] = math.floor(num(typeof(R.Fresh) == `table` and R.Fresh[A], -1, 1e7, -1))
		Out.DayXp[A] = math.floor(num(typeof(R.DayXp) == `table` and R.DayXp[A], 0, 1e7, 0))
	end
	Out.Fed = num(R.Fed, 0, 100, 0)
	Out.LastTrained = num(R.LastTrained, 0, 1e12, 0)
	Out.Day = math.floor(num(R.Day, -1, 1e7, -1))
	Out.XpDay = math.floor(num(R.XpDay, -1, 1e7, -1))
	Out.Streak = math.floor(num(R.Streak, 0, 1e5, 0))
	Out.StreakBest = math.floor(num(R.StreakBest, 0, 1e5, 0))
	if typeof(R.StreakPaid) == `table` then
		for K, V in R.StreakPaid do if Training.StreakYen[tonumber(K)] and V == true then Out.StreakPaid[tostring(K)] = true end end
	end
	if typeof(R.Best) == `table` then
		for Id in Training.Stations do
			local B = R.Best[Id]
			if typeof(B) == `table` then Out.Best[Id] = { Score = math.floor(num(B.Score, 0, 1e6, 0)); Combo = math.floor(num(B.Combo, 0, 1e4, 0)) } end
		end
	end
	Out.Tut = R.Tut == true
	Out.Seeded = R.Seeded == true
	if typeof(R.Athletes) == `table` then Out.Athletes = { Day = math.floor(num(R.Athletes.Day, -1, 1e7, -1)); N = math.floor(num(R.Athletes.N, 0, 1e4, 0)) } end
	return Out
end

-- the soreness now (it wears off with real time)
function Training.SoreNow(S, Now: number): number
	local Gone = math.max(0, Now - (S.SoreAt or 0)) / Training.Sore.DecayEvery
	return math.max(0, (S.Sore or 0) - Gone)
end
function Training.SoreMult(Sore: number): number
	return 1 - (1 - Training.Sore.XpAtMax) * math.clamp(Sore / Training.Sore.Max, 0, 1)
end
function Training.Day(Now: number): number
	return math.floor(Now / 86400)
end

return Training
