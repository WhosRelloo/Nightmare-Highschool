-- anatomy_client (Task 11 step 5, Client VM): drives the running bench through the renderer's Studio hooks, pausing at
-- the moments to screenshot (NHShot attribute on the player: start, trace, held, desk, done). A clean frog, one
-- tool put on the desk, and one deliberate wrong outline (the Recoil clip must play).
local P = game:GetService("Players").LocalPlayer
local t0 = os.clock()
while not _G.NHAnatomyBench and os.clock() - t0 < 20 do task.wait(0.2) end
local B = _G.NHAnatomyBench
if not B then return "FAIL no bench renderer" end
local Log = {}
local function shot(name, hold) P:SetAttribute("NHShot", name) task.wait(hold or 4) end
local function W(s) task.wait(s or 0.35) end
local St = B:_TestState()
table.insert(Log, "rig " .. tostring(St.Rig) .. " tracks " .. St.Tracks .. " real " .. tostring(St.Real))
shot("start")
B:_TestKey(1) W()
for _ = 1, 8 do B:_TestUse("SideKey") W(0.3) end
B:_TestKey(4) W(0.6)
P:SetAttribute("NHShot", "trace")
local n = B:_TestTrace(nil, 0.08)
W(1.5)
table.insert(Log, "trace pts " .. n .. " step " .. B:_TestState().Step)
B:_TestKey(2) W()
B:_TestUse("Plate") W(1.4)
B:_TestPut("Desk", Vector3.new(4.4, 0, 2.6)) W(1.2) -- a desk spot in view, right of the roll
shot("desk", 3)
table.insert(Log, "driver " .. tostring(B:_TestState().Tools.Driver) .. " plate " .. tostring(B:_TestState().PlateOpen))
B:_TestKey(5) W()
local Order = { { "HeartPump", "Heart" }, { "Lungs", "Lungs" }, { "GearGut", "Gut" } }
local Recoil = false
for i, O in Order do
	B:_TestUse("Organ", O[1]) W(0.6)
	if i == 1 then shot("held", 3) end
	if i == 2 then
		B:_TestPlace("Heart") -- wrong outline on purpose
		task.wait(0.15)
		for _, Name in B:_TestState().Playing do if Name == "AnatRecoil" then Recoil = true end end
		W(1.1)
		B:_TestUse("Organ", O[1]) W(0.6)
	end
	B:_TestPlace(O[2]) W(0.6)
end
table.insert(Log, "recoil " .. tostring(Recoil))
shot("done", 5)
local G = P.PlayerGui:FindFirstChild("Lesson")
local Grade = "?"
if G then for _, X in G:GetDescendants() do if X:IsA("TextLabel") and string.match(X.Text, "^[ABCDF][%+%-]?$") then Grade = X.Text end end end
table.insert(Log, "grade " .. Grade)
if not Recoil then return "FAIL recoil did not play; " .. table.concat(Log, "; ") end
return "PASS anatomy_client: " .. table.concat(Log, "; ")
