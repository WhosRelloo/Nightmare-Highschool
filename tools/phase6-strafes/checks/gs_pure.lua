-- gs_pure (phase6-strafes R4): Functions.Gestures + Config.Gestures, inlined by harness/pure.py. Pure: writes nothing.
local function load(name)
	local Src = __SRC and __SRC[name]
	if not Src then error("FAIL source not inlined: " .. name) end
	local Fn, Err = loadstring(Src)
	if not Fn then error("FAIL parse " .. name .. ": " .. tostring(Err)) end
	return Fn()
end
local Cfg = load("ReplicatedStorage.Config.Gestures.luau")
local G = load("ReplicatedStorage.Functions.Gestures.luau")
local Fails = {}
local function Eq(Got, Want, What) if Got ~= Want then table.insert(Fails, What .. ": got " .. tostring(Got) .. " want " .. tostring(Want)) end end
local function Ok(C, What) if not C then table.insert(Fails, What) end end
local Rng = Random.new(7)
local function roll() return Rng:NextNumber() end
local function always() return 0 end
-- picks
local P = G.Pick(Cfg.Cast, "Hangout", { Clique = "Choir" }, always)
Ok(P and P:sub(1, 4) == "Pray", "choir hangout prays: " .. tostring(P))
Eq(G.Pick(Cfg.Cast, "Watch", { Clique = "Athletes" }, always), "CheerSeated_Upper", "athletes watch")
Eq(G.Pick(Cfg.Cast, "Argue", { Attitude = "Hostile" }, always), "Argue_A", "argue")
local Cu = G.Pick(Cfg.Cast, "Post", { Npc = "Custodian" }, roll)
Ok(Cu == "Rummage" or Cu == "Gather" or Cu == "ReachDown", "custodian post: " .. tostring(Cu))
Eq(G.Pick(Cfg.Cast, "Fidget", { Clique = "Nope" }, always), nil, "unknown clique fidget")
Eq(G.Pick(Cfg.Cast, "Gawk", {}, function() return 0.99 end), nil, "chance roll fails")
Eq(G.Pick(Cfg.Cast, "Hangout", { Clique = "Pack", Moon = false }, always), nil, "pack without the moon")
Eq(G.Pick(Cfg.Cast, "Hangout", { Clique = "Pack", Moon = true }, always), "OrcIdle", "pack on a moon night")
Eq(G.Pick(Cfg.Cast, "ChatListener", { Temper = "Shy" }, always), "SadIdle", "shy listener")
Eq(G.Pick(Cfg.Cast, "Patient", { Spot = "Bed" }, always), "LayingIdle", "bed patient")
-- weights over 1000 rolls
local Test = { { Hook = "X"; Who = {}; Clips = { { "A", 3 }, { "B", 1 } }; Chance = 1 } }
local N = 0
local R2 = Random.new(11)
for _ = 1, 1000 do if G.Pick(Test, "X", {}, function() return R2:NextNumber() end) == "A" then N += 1 end end
Ok(math.abs(N / 1000 - 0.75) < 0.05, "weighted pick " .. N)
-- buckets and names
Eq(G.Bucket(1.66, { 80, 90, 100 }), 80, "bucket 0.83")
Eq(G.Bucket(1.76, { 80, 90, 100 }), 90, "bucket 0.88")
Eq(G.Bucket(2.04, { 80, 90, 100 }), 100, "bucket 1.02")
Eq(G.Name("KneelInspect", Cfg.Clips.KneelInspect, 1.62), "KneelInspect_80", "name bucketed")
Eq(G.Name("Talk", Cfg.Clips.Talk, 1.62), "Talk", "name plain")
-- config sanity
for _, R in Cfg.Cast do for _, C in R.Clips do Ok(Cfg.Clips[C[1]] ~= nil, "cast clip missing: " .. C[1]) end end
local Count = 0
for Name, C in Cfg.Clips do
	Count += 1
	Ok(type(C.Len) == "number" and C.Len > 0, Name .. " Len") Ok(type(C.Loop) == "boolean", Name .. " Loop")
	Ok(Enum.AnimationPriority[C.Priority] ~= nil, Name .. " Priority")
end
Eq(Count, 28, "clip bases")
Eq(Cfg.Caps.MaxActive, 6, "cap") Eq(Cfg.Treat.Cooldown, 180, "treat cooldown") Eq(Cfg.Treat.Price, 0, "treat free")
return #Fails == 0 and "PASS gs_pure" or ("FAIL\n" .. table.concat(Fails, "\n"))
