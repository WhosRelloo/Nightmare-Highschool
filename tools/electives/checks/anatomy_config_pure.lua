-- anatomy_config_pure (Task 5)
local function load(name) local Fn = loadstring(__SRC[name]) return Fn() end
local A = load("ReplicatedStorage.Config.Anatomy.luau")
local Fails = {}
local function Eq(G, W, What) if G ~= W then table.insert(Fails, What .. ": got " .. tostring(G) .. " want " .. tostring(W)) end end
Eq(#A.Tools, 5, "five tools") Eq(A.Tools[1], "Key", "1 Key") Eq(A.Tools[5], "Tweezers", "5 Tweezers")
Eq(A.Weights.Accuracy + A.Weights.Process + A.Weights.Time, 1, "weights sum to 1")
Eq(A.SpeciesFor(1).Id, "Frog", "lvl 1 frog") Eq(A.SpeciesFor(2).Id, "Frog", "lvl 2 frog")
Eq(A.SpeciesFor(3).Id, "Raven", "lvl 3 raven") Eq(A.SpeciesFor(5).Id, "Wyvern", "lvl 5 wyvern")
Eq(A.SpeciesFor(1, "Wyvern").Id, "Wyvern", "crate override")
for _, Id in { "Frog", "Raven", "Wyvern" } do
	local S = A.Species[Id]
	local Valid = {} for _, T in A.Tools do Valid[T] = true end
	for _, St in S.Steps do if not Valid[St.Tool] then table.insert(Fails, Id .. " step " .. St.Id .. " bad tool") end end
	local Slots = {} for _, O in S.Organs do if not O.Flag then Eq(Slots[O.Slot], nil, Id .. " slot unique " .. O.Slot) Slots[O.Slot] = true end end
	Eq(S.Steps[#S.Steps].Id, "Lift", Id .. " ends with Lift")
end
local NF = 0 for _, O in A.Species.Frog.Organs do if not O.Flag then NF += 1 end end Eq(NF, 3, "frog organs (not counting the flag)")
if #Fails > 0 then return "FAIL\n" .. table.concat(Fails, "\n") end
return "PASS anatomy_config_pure"
