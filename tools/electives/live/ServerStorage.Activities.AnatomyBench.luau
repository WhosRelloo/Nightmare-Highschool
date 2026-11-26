--[[
	Anatomy: "The Bench" (server logic). The client sends intents; this judges them.
	Steps run in order (Config.Anatomy.Species[*].Steps); the last step, Lift, repeats until every non-Flag organ
	is placed on its slot. A slip (wrong target, lifting out of turn, a flag organ, a wrong slot) costs accuracy and
	starts a Recoil during which input is ignored. Using the wrong tool costs process, not accuracy.
	Substitutes' Specimen twist: Hollow brings the Wyvern (crate), Crane doubles slip cost (Inspection),
	Moth shuffles the organs and hides the slots until the Loupe is used on the card. Lazzaro's bet is his rule.
]]
local Cfg = getfenv().__AnatomyConfig or require(game:GetService(`ReplicatedStorage`).Config.Anatomy)

local Bench = {}
Bench.Bench = true

local function Twist(S): string?
	local Sub = S.Sub
	if not (Sub and Sub.Twist == `Specimen` and Sub.Sub) then return nil end
	local N = Sub.Sub.Name or ``
	if N:find(`Hollow`) then return `Crate` end
	if N:find(`Crane`) then return `Inspection` end
	if N:find(`Moth`) then return `Loose` end
	if N:find(`Lazzaro`) then return `Bet` end
	return nil
end

function Bench.TimeLimit(Level: number): number
	return Cfg.SpeciesFor(Level).TimeLimit
end

-- the limit for this session's specimen (a substitute's crate can bring a bigger one than the level would)
function Bench.TimeLimitFor(S): number
	return S.Species and S.Species.TimeLimit or Bench.TimeLimit(S.BenchLevel or 1)
end

function Bench.Start(S, Level: number, StartAt: number)
	S.Twist = Twist(S)
	local Species = Cfg.SpeciesFor(Level, if S.Twist == `Crate` then `Wyvern` else nil)
	S.Species = Species
	S.BenchLevel = Level -- (S.Level is the class level Activities saves)
	S.StartAt = StartAt
	S.StepIndex = 1
	S.Count = 0
	S.LastUse = -math.huge
	S.Hand = nil
	S.Holding = nil
	S.Slips = 0
	S.WrongTool = 0
	S.TraceAccuracy = 0
	S.Placed = {}
	S.PlacedCount = 0
	S.RecoilUntil = -math.huge
	S.FinishedAt = nil
	S.Revealed = S.Twist ~= `Loose`
	S.Organs = {}
	for _, O in Species.Organs do
		if not O.Flag or Level >= (Species.FlagFrom or math.huge) then table.insert(S.Organs, O) end
	end
	S.Need = 0
	for _, O in S.Organs do if not O.Flag then S.Need += 1 end end
	if S.Twist == `Loose` then
		local Rng = Random.new()
		for I = #S.Organs, 2, -1 do local J = Rng:NextInteger(1, I) S.Organs[I], S.Organs[J] = S.Organs[J], S.Organs[I] end
	end
	local Organs = {}
	for _, O in S.Organs do table.insert(Organs, { Id = O.Id; Name = O.Name; Slot = if S.Revealed then O.Slot else nil }) end
	local Steps = {}
	for _, St in Species.Steps do table.insert(Steps, { Id = St.Id; Tool = St.Tool; Target = St.Target; Count = St.Count }) end
	return { Species = Species.Id; Name = Species.Name; Latin = Species.Latin; Tools = Cfg.Tools; Steps = Steps;
		Organs = Organs; TimeLimit = Species.TimeLimit; Twist = S.Twist; Level = Level }
end

local function Organ(S, Id)
	for _, O in S.Organs do if O.Id == Id then return O end end
	return nil
end

local function Slip(S, Now, Why)
	S.Slips += 1
	S.RecoilUntil = Now + Cfg.RecoilSeconds
	S.Holding = nil
	return { Ok = false; Slip = true; Recoil = true; Why = Why; Hand = S.Hand; Step = S.StepIndex }
end

local function Advance(S)
	S.StepIndex += 1
	S.Count = 0
end

local function JudgeTrace(S, Points): (boolean, number)
	if typeof(Points) ~= `table` or #Points < 8 or #Points > 400 then return false, 0 end
	local Rx, Ry = S.Species.Seam.Rx, S.Species.Seam.Ry
	local Good, Angles = 0, {}
	for _, P in Points do
		if typeof(P) ~= `table` or typeof(P[1]) ~= `number` or typeof(P[2]) ~= `number` then return false, 0 end
		local x, y = P[1] / Rx, P[2] / Ry
		local r = math.sqrt(x * x + y * y)
		if math.abs(r - 1) <= Cfg.TraceTolerance then Good += 1 end
		table.insert(Angles, math.atan2(y, x))
	end
	table.sort(Angles)
	local Gap = (Angles[1] + 2 * math.pi) - Angles[#Angles]
	for I = 2, #Angles do Gap = math.max(Gap, Angles[I] - Angles[I - 1]) end
	local Sweep = (2 * math.pi - Gap) / (2 * math.pi)
	return Sweep >= Cfg.TraceCoverage, Good / #Points
end

function Bench.Handle(S, Action: string, Data: any, Now: number)
	if S.FinishedAt or Now < S.StartAt - 0.5 or Now < S.RecoilUntil then return nil, false end
	if typeof(Data) ~= `table` then Data = {} end
	local Step = S.Species.Steps[S.StepIndex]

	if Action == `Pick` then
		local Valid = table.find(Cfg.Tools, Data.Tool)
		if not Valid or S.Holding then return nil, false end
		S.Hand = Data.Tool
		return { Ok = true; Hand = S.Hand; Step = S.StepIndex }, false
	elseif Action == `Put` then
		if S.Holding then return nil, false end -- set the organ down on the card first
		S.Hand = nil
		return { Ok = true; Hand = nil; Spot = if Data.Spot == `Desk` then `Desk` else `Roll` }, false
	elseif Action == `Use` then
		if not S.Hand then return nil, false end
		-- the Loupe on the card reveals hidden slots at any time (Moth's loose specimen)
		if S.Hand == `Loupe` and Data.Target == `Card` then
			if S.Revealed then return { Ok = true }, false end
			S.Revealed = true
			local Reveal = {}
			for _, O in S.Organs do Reveal[O.Id] = O.Slot end
			return { Ok = true; Reveal = Reveal }, false
		end
		if Data.Target ~= Step.Target then
			if Step.Id == `Lift` or Data.Target == `Organ` then return Slip(S, Now, `NotYet`), false end
			return { Ok = false; Why = `WrongTarget` }, false
		end
		if S.Hand ~= Step.Tool then
			S.WrongTool += 1
			return { Ok = false; Why = `WrongTool`; Step = S.StepIndex }, false
		end
		if Step.Id == `Trace` then
			local Ok, Acc = JudgeTrace(S, Data.Points)
			if not Ok then return { Ok = false; Why = `Incomplete` }, false end
			S.TraceAccuracy = Acc
			Advance(S)
			return { Ok = true; Step = S.StepIndex; TraceAccuracy = Acc }, false
		elseif Step.Id == `Lift` then
			local O = Organ(S, Data.Organ)
			if not O or S.Placed[O.Id] or S.Holding then return nil, false end
			if O.Flag then return Slip(S, Now, `Flag`), false end
			if not O.First then
				for _, F in S.Organs do
					if F.First and not S.Placed[F.Id] then return Slip(S, Now, `FirstOrgan`), false end
				end
			end
			S.Holding = O.Id
			return { Ok = true; Holding = O.Id }, false
		elseif Step.Count then
			if Now - S.LastUse < Cfg.UseInterval then return nil, false end
			S.LastUse = Now
			S.Count += 1
			if S.Count >= Step.Count then Advance(S) end
			return { Ok = true; Step = S.StepIndex; Progress = S.Count }, false
		else
			Advance(S)
			return { Ok = true; Step = S.StepIndex }, false
		end
	elseif Action == `Place` then
		local O = S.Holding and Organ(S, S.Holding)
		if not O or Data.Organ ~= O.Id then return nil, false end
		if Data.Slot ~= O.Slot then return Slip(S, Now, `WrongSlot`), false end
		S.Placed[O.Id] = true
		S.PlacedCount += 1
		S.Holding = nil
		local Done = S.PlacedCount >= S.Need
		if Done then S.FinishedAt = Now end
		return { Ok = true; Placed = O.Id; Done = Done }, Done
	end
	return nil, false
end

function Bench.Tick(S, Now: number)
	return false, nil
end

function Bench.Breakdown(S)
	local Steps = #S.Species.Steps
	local StepDone = if S.FinishedAt then 1 else math.clamp((S.StepIndex - 1) / Steps, 0, 1)
	local Organs = if S.Need > 0 then S.PlacedCount / S.Need else 1
	local Cost = Cfg.SlipCost * (if S.Twist == `Inspection` then 2 else 1)
	local Accuracy = math.clamp((S.TraceAccuracy * 0.4 + Organs * 0.6) - S.Slips * Cost, 0, 1)
	local Process = math.clamp(StepDone - S.WrongTool * Cfg.WrongToolCost, 0, 1)
	local Time = 0
	if S.FinishedAt then
		local Used = S.FinishedAt - S.StartAt
		local Par, Limit = S.Species.Par, S.Species.TimeLimit
		Time = if Used <= Par then 1 else math.clamp(1 - (Used - Par) / (Limit - Par), 0, 1)
	end
	return { Accuracy = Accuracy; Process = Process; Time = Time }
end

function Bench.Score(S): (number, number)
	local B = Bench.Breakdown(S)
	local W = Cfg.Weights
	return math.floor((B.Accuracy * W.Accuracy + B.Process * W.Process + B.Time * W.Time) * 100 + 0.5), 100
end

return Bench
