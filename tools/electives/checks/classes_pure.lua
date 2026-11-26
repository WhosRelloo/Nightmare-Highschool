-- classes_pure (electives Task 1). usage: python -X utf8 -I tools/electives/harness/pure.py tools/electives/checks/classes_pure.lua
local function load(name)
	local Src = __SRC and __SRC[name]
	if not Src then error("FAIL source not inlined: " .. name) end
	local Fn, Err = loadstring(Src)
	if not Fn then error("FAIL parse " .. name .. ": " .. tostring(Err)) end
	return Fn()
end
local Fails = {}
local function Eq(G, W, What) if G ~= W then table.insert(Fails, What .. ": got " .. tostring(G) .. " want " .. tostring(W)) end end
local E = load("ReplicatedStorage.Config.Electives.luau")
local n, open = 0, 0
for Id, D in E.List do n += 1 if D.Open then open += 1 end Eq(D.Id, Id, "id matches key " .. Id) end
Eq(n, 10, "ten electives") Eq(open, 1, "one open") Eq(E.Get("Anatomy").Room, "R103", "Anatomy room")
Eq(E.Get("Nope"), nil, "unknown id")
local RealRequire = require
getfenv().require = function(M) if M == "Electives" then return E end return RealRequire(M) end
local C = load("ReplicatedStorage.Config.Classes.luau")
Eq(C.For("Period 3", 0, "Anatomy").Subject, "English", "Monday P3 stays English")
Eq(C.For("Period 3", 1, "Anatomy").Subject, "Anatomy", "Tuesday P3 is the pick")
Eq(C.For("Period 4", 3, "Anatomy").Room, "R103", "Thursday P4 room")
Eq(C.For("Period 4", 3, "Anatomy").Elective, true, "flagged elective")
Eq(C.For("Period 3", 6, "Anatomy").Subject, "Anatomy", "day 6 is a Tuesday (6 % 5 = 1)")
Eq(C.For("Period 3", 1, nil).Subject, "Study Hall", "no pick: study hall")
Eq(C.For("Period 3", 1, "Workshop").Subject, "Study Hall", "a closed elective: study hall")
Eq(C.For("Period 2", 1, "Anatomy").Subject, "Chemistry", "other periods untouched")
Eq(C.For("Lunch", 1, "Anatomy"), nil, "not a class")
Eq(C.IsElectiveSlot("Period 4", 1), true, "slot yes") Eq(C.IsElectiveSlot("Period 2", 1), false, "slot no")
Eq(C.Periods["Period 3"].Subject, "English", "base table unchanged")
if #Fails > 0 then return "FAIL\n" .. table.concat(Fails, "\n") end
return "PASS classes_pure"
