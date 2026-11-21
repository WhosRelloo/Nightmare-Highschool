local Mod = game.ReplicatedStorage:FindFirstChild("Functions") and game.ReplicatedStorage.Functions:FindFirstChild("BellTower")
if not Mod then return "FAIL Functions.BellTower missing" end
local B = require(Mod:Clone())
local Fails = {}
local function Eq(Got, Want, What) if Got ~= Want then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end
local function Near(Got, Want, What) if math.abs(Got - Want) > 1e-6 then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end

Eq(B.MIN_TEXT, 20, "MIN_TEXT")
-- hand: midnight at the bottom, noon at the top, 6 AM on the left, 6 PM on the right
Near(B.HandAngle(0), 180, "HandAngle(0)")
Near(B.HandAngle(12), 0, "HandAngle(12)")
Near(B.HandAngle(6), 270, "HandAngle(6)")
Near(B.HandAngle(18), 90, "HandAngle(18)")
Near(B.HandAngle(9.95), (9.95 / 24 * 360 + 180) % 360, "HandAngle(9.95)")
-- image lookup
Eq(B.Image({ Dial = 0 }, "Dial"), nil, "Image of 0")
Eq(B.Image({}, "Dial"), nil, "Image of missing")
Eq(B.Image({ Dial = 123 }, "Dial"), "rbxassetid://123", "Image of 123")
-- conduct: clear and owing nothing hides the row
local C = B.Conduct({ DisciplineLevel = "Clear", DisciplinePoints = 0, DetentionsOwed = 0 }, false)
Eq(C.Visible, false, "Clear visible")
-- warning
C = B.Conduct({ DisciplineLevel = "Warning", DisciplinePoints = 3, DetentionsOwed = 0 }, false)
Eq(C.Visible, true, "Warning visible") Eq(C.Seal, "Warning", "Warning seal") Eq(C.Text, "Warning · 3 pts", "Warning text") Eq(#C.Slips, 0, "Warning slips")
-- detention owed, outside class: a slip and a waypoint
C = B.Conduct({ DisciplineLevel = "Detention", DisciplinePoints = 6, DetentionsOwed = 1 }, false)
Eq(C.Seal, "Detention", "Detention seal") Eq(#C.Slips, 1, "owed slips") Eq(C.Slips[1].Title, "Detention owed", "owed title")
Eq(C.Slips[1].Line, "Room 106, outside class", "owed line") Eq(C.Waypoint, true, "owed waypoint outside class")
-- owed, in class: no waypoint
Eq(B.Conduct({ DisciplineLevel = "Detention", DisciplinePoints = 6, DetentionsOwed = 1 }, true).Waypoint, false, "owed waypoint in class")
-- owed twice
Eq(B.Conduct({ DisciplineLevel = "Detention", DisciplinePoints = 6, DetentionsOwed = 2 }, false).Slips[1].Title, "Detention owed ×2", "owed x2 title")
-- a detention under way
C = B.Conduct({ DisciplineLevel = "Detention", DisciplinePoints = 6, DetentionsOwed = 1, DetentionActive = true, DetentionCollected = 2, DetentionTotal = 5 }, false)
Eq(C.Slips[1].Title, "Detention", "active title") Eq(C.Slips[1].Line, "Trash 2/5", "active line") Eq(C.Waypoint, false, "active waypoint")
Eq(B.Conduct({ DisciplineLevel = "Detention", DetentionActive = true, DetentionCollected = 5, DetentionTotal = 5 }, false).Slips[1].Line, "Use the bin to finish", "active done")
-- suspended: broken seal
C = B.Conduct({ DisciplineLevel = "Probation", DisciplinePoints = 19, Suspended = true }, false)
Eq(C.Seal, "Suspension", "Suspended seal") Eq(C.Broken, true, "Suspended broken") Eq(C.Text, "Suspended", "Suspended text")
-- an unknown level shows no seal
Eq(B.Conduct({ DisciplineLevel = "Weird", DetentionsOwed = 0 }, false).Visible, false, "unknown level")
-- pips
Eq(B.Pips(0, 1), nil, "Pips need 1") Eq(B.Pips(0, 7), nil, "Pips need 7")
local Pp = B.Pips(1, 3)
Eq(#Pp, 3, "Pips len") Eq(Pp[1], true, "pip 1") Eq(Pp[2], false, "pip 2") Eq(Pp[3], false, "pip 3")
Eq(B.Pips(9, 3)[3], true, "Pips clamp high") Eq(B.Pips(-2, 2)[1], false, "Pips clamp low")
return #Fails == 0 and "PASS bt_pure" or ("FAIL\n" .. table.concat(Fails, "\n"))
