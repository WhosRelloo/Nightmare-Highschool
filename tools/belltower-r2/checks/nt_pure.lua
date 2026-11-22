local RS = game.ReplicatedStorage
local Mod = RS:FindFirstChild("Functions") and RS.Functions:FindFirstChild("Notoriety")
if not Mod or not (RS:FindFirstChild("Config") and RS.Config:FindFirstChild("Notoriety")) then return "FAIL Notoriety modules missing" end
local F = require(Mod:Clone())
local Fails = {}
local function Eq(Got, Want, What) if Got ~= Want then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end
local function Near(Got, Want, What) if math.abs(Got - Want) > 1e-6 then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end

-- gain (spec §3.2)
Eq(F.Gain("Truancy", {}), 12, "Gain Truancy") Eq(F.Gain("Trespassing", {}), 20, "Gain Trespassing")
Eq(F.Gain("Curfew", {}), 20, "Gain Curfew") Eq(F.Gain("Fighting", {}), 25, "Gain Fighting")
Eq(F.Gain("Vandalism", {}), 15, "Gain Vandalism") Eq(F.Gain("Exposure", {}), 30, "Gain Exposure")
Eq(F.Gain("AssaultStaff", {}), 45, "Gain AssaultStaff") Eq(F.Gain("Absent", {}), 0, "Gain unknown")
Near(F.Gain("Fighting", { Night = true }), 37.5, "Gain night") Near(F.Gain("Fighting", { Probation = true }), 31.25, "Gain probation")
Near(F.Gain("Truancy", { Night = true, Probation = true }), 22.5, "Gain night+probation")
-- tiers 10/25/45/70/90
Eq(F.Tier(0), 0, "Tier 0") Eq(F.Tier(9.99), 0, "Tier 9.99") Eq(F.Tier(10), 1, "Tier 10") Eq(F.Tier(25), 2, "Tier 25")
Eq(F.Tier(44.9), 2, "Tier 44.9") Eq(F.Tier(45), 3, "Tier 45") Eq(F.Tier(70), 4, "Tier 70") Eq(F.Tier(90), 5, "Tier 90") Eq(F.Tier(100), 5, "Tier 100")
-- bonus 0,0,1,2,3
Eq(F.Bonus(0), 0, "Bonus 0") Eq(F.Bonus(2), 0, "Bonus 2") Eq(F.Bonus(3), 1, "Bonus 3") Eq(F.Bonus(4), 2, "Bonus 4") Eq(F.Bonus(5), 3, "Bonus 5")
-- cooling
Eq(F.CoolMult({}), 1, "CoolMult none") Eq(F.CoolMult({ Hidden = true }), 2, "CoolMult hidden") Eq(F.CoolMult({ Dorms = true }), 2, "CoolMult dorms")
Eq(F.CoolMult({ OffCampus = true }), 2, "CoolMult off campus") Eq(F.CoolMult({ Alibi = true, Hidden = true }), 3, "CoolMult alibi wins")
Near(F.Cool(25, 1, 5, 1), 23.5, "Cool search") Near(F.Cool(25, 1, 31, 1), 22, "Cool quiet") Near(F.Cool(25, 1, 5, 3), 20.5, "Cool alibi")
Eq(F.Cool(1, 1, 31, 1), 0, "Cool floor")
-- state
Eq(F.State(true, 0, false), "Lit", "State lit") Eq(F.State(false, 10, false), "Search", "State search")
Eq(F.State(false, 30, false), "Hollow", "State hollow") Eq(F.State(false, 31, true), "Tarnished", "State tarnished")
-- search radius 30..120 over 30 s
Near(F.SearchRadius(0), 30, "Radius 0") Near(F.SearchRadius(15), 75, "Radius 15") Near(F.SearchRadius(60), 120, "Radius cap")
-- booking
Eq(F.BookType("Curfew"), "Trespassing", "Book curfew") Eq(F.BookType("AssaultStaff"), "Fighting", "Book assault") Eq(F.BookType("Truancy"), "Truancy", "Book truancy")
Eq(F.TierName(3), "Named", "TierName 3") Eq(F.TierName(5), "The Tolling", "TierName 5") Eq(F.TierName(0), "", "TierName 0")
return #Fails == 0 and "PASS nt_pure" or ("FAIL\n" .. table.concat(Fails, "\n"))
