-- anatomy_bench_pure (Task 6): a clean frog run, slips, wrong tool, flag, trace judging, the Wyvern's first-organ rule, the twists.
local function load(name) local Fn = loadstring(__SRC[name]) return Fn() end
local Cfg = load("ReplicatedStorage.Config.Anatomy.luau")
getfenv().__AnatomyConfig = Cfg -- the module takes its config from here when run outside the place
local B = load("ServerStorage.Activities.AnatomyBench.luau")
local Fails = {}
local function Eq(G, W, What) if G ~= W then table.insert(Fails, What .. ": got " .. tostring(G) .. " want " .. tostring(W)) end end
local function Ring(Rx, Ry, N, Noise) local P = {} for I = 0, N do local a = I / N * 2 * math.pi * 0.97 table.insert(P, { math.cos(a) * Rx * (1 + (Noise or 0)), math.sin(a) * Ry * (1 + (Noise or 0)) }) end return P end
local function Run(S, Steps)
	local t = 0
	for _, A in Steps do t += 0.3 local R, F = B.Handle(S, A[1], A[2], S.StartAt + t) if F then return R, true, t end end
	return nil, false, t
end
local function Frog(S)
	local Steps = { { "Pick", { Tool = "Key" } } }
	for _ = 1, 8 do table.insert(Steps, { "Use", { Target = "SideKey" } }) end
	table.insert(Steps, { "Pick", { Tool = "Scalpel" } })
	table.insert(Steps, { "Use", { Target = "Seam", Points = Ring(1, 1.3, 40) } })
	table.insert(Steps, { "Pick", { Tool = "Driver" } })
	table.insert(Steps, { "Use", { Target = "Plate" } })
	table.insert(Steps, { "Pick", { Tool = "Tweezers" } })
	for _, O in { { "HeartPump", "Heart" }, { "Lungs", "Lungs" }, { "GearGut", "Gut" } } do
		table.insert(Steps, { "Use", { Target = "Organ", Organ = O[1] } })
		table.insert(Steps, { "Place", { Organ = O[1], Slot = O[2] } })
	end
	return Steps
end
-- 1) a clean level-1 frog finishes with an A or better
local S = {} B.Start(S, 1, 0)
Eq(S.Species.Id, "Frog", "species")
local _, Done = Run(S, Frog(S))
Eq(Done, true, "clean run finishes")
local Score = B.Score(S)
if Score < 90 then table.insert(Fails, "clean run scored " .. Score) end
-- 2) wrong tool: using the Scalpel on the key costs process, not progress
S = {} B.Start(S, 1, 0)
local R = B.Handle(S, "Pick", { Tool = "Scalpel" }, 1)
R = B.Handle(S, "Use", { Target = "SideKey" }, 1.5)
Eq(R.Ok, false, "wrong tool refused") Eq(S.WrongTool, 1, "wrong tool counted") Eq(S.StepIndex, 1, "still on Unwind")
-- 3) a slip (lifting an organ before the plate is open) starts a recoil that swallows input
S = {} B.Start(S, 1, 0)
B.Handle(S, "Pick", { Tool = "Tweezers" }, 1)
R = B.Handle(S, "Use", { Target = "Organ", Organ = "HeartPump" }, 1.2)
Eq(R.Slip, true, "early lift slips") Eq(R.Recoil, true, "recoil flagged")
Eq(B.Handle(S, "Pick", { Tool = "Key" }, 1.5), nil, "input ignored during recoil")
Eq(B.Handle(S, "Pick", { Tool = "Key" }, 2.1).Hand, "Key", "input back after recoil")
-- 4) a sloppy trace scores lower accuracy than a clean one, and too little sweep is refused
local function TraceOnly(Points)
	local T = {} B.Start(T, 1, 0)
	B.Handle(T, "Pick", { Tool = "Key" }, 1) for i = 1, 8 do B.Handle(T, "Use", { Target = "SideKey" }, 1 + i * 0.2) end
	B.Handle(T, "Pick", { Tool = "Scalpel" }, 3)
	return T, B.Handle(T, "Use", { Target = "Seam", Points = Points }, 4)
end
local Clean = TraceOnly(Ring(1, 1.3, 40)).TraceAccuracy
local Messy = TraceOnly(Ring(1, 1.3, 40, 0.12)).TraceAccuracy
if not (Clean > 0.95 and Messy < Clean) then table.insert(Fails, ("trace accuracy clean %.2f messy %.2f"):format(Clean, Messy)) end
local Half = {} for I = 0, 20 do local a = I / 20 * math.pi table.insert(Half, { math.cos(a), math.sin(a) * 1.3 }) end
local _, HR = TraceOnly(Half) Eq(HR.Ok, false, "half a seam is not a trace")
-- 5) the Flag organ appears from level 4 (a Raven) and lifting it is a slip; below level 4 there is none
S = {} B.Start(S, 4, 0)
local HasFlag = false for _, O in S.Organs do if O.Flag then HasFlag = true end end
Eq(S.Species.Id, "Raven", "level 4 is a raven") Eq(HasFlag, true, "flag from level 4")
S.StepIndex = #S.Species.Steps S.Hand = "Tweezers"
Eq(B.Handle(S, "Use", { Target = "Organ", Organ = "FlagCog" }, 5).Slip, true, "lifting the flag slips")
S = {} B.Start(S, 2, 0) local NoFlag = true for _, O in S.Organs do if O.Flag then NoFlag = false end end Eq(NoFlag, true, "no flag below level 4")
-- 6) the Wyvern: lifting anything before the Fire-gland recoils
S = { Sub = { Twist = "Specimen"; Sub = { Name = "Mx. Ashgrove Hollow" } } } B.Start(S, 1, 0)
Eq(S.Species.Id, "Wyvern", "Hollow's crate brings the Wyvern at level 1")
S.StepIndex = #S.Species.Steps S.Hand = "Tweezers" -- jump to Lift for the rule test
R = B.Handle(S, "Use", { Target = "Organ", Organ = "HeartA" }, 5)
Eq(R.Slip, true, "heart before fire-gland slips")
R = B.Handle(S, "Use", { Target = "Organ", Organ = "FireGland" }, 6) Eq(R.Holding, "FireGland", "fire-gland first is fine")
-- 7) Crane's Inspection doubles the slip cost
local A1 = {} B.Start(A1, 1, 0) A1.Slips = 2 A1.TraceAccuracy = 1 A1.PlacedCount = A1.Need
local A2 = { Sub = { Twist = "Specimen"; Sub = { Name = "Mr. Thaddeus Crane" } } } B.Start(A2, 1, 0) A2.Slips = 2 A2.TraceAccuracy = 1 A2.PlacedCount = A2.Need
if not (B.Breakdown(A2).Accuracy < B.Breakdown(A1).Accuracy) then table.insert(Fails, "inspection should cost more") end
-- 8) Moth's loose specimen hides the slots until the Loupe is used on the card
S = { Sub = { Twist = "Specimen"; Sub = { Name = "Miss Delphine Moth" } } }
local Info = B.Start(S, 1, 0)
Eq(Info.Organs[1].Slot, nil, "slots hidden")
B.Handle(S, "Pick", { Tool = "Loupe" }, 1)
R = B.Handle(S, "Use", { Target = "Card" }, 1.3) Eq(R.Reveal ~= nil, true, "loupe reveals")
if #Fails > 0 then return "FAIL\n" .. table.concat(Fails, "\n") end
return "PASS anatomy_bench_pure"
