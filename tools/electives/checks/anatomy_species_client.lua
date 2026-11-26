-- anatomy_species_client (Client VM): drives whichever species the running bench dealt through the renderer's Studio
-- hooks, following that species' own Steps (Unwind, Unscrew the wing plates, Inspect with the Loupe, Trace, Pry, Lift
-- with the First organ first). Holds at NHShot moments for screenshots: start, mid (after the species' own step),
-- open, done.
local P = game:GetService("Players").LocalPlayer
local t0 = os.clock()
while not _G.NHAnatomyBench and os.clock() - t0 < 20 do task.wait(0.2) end
local B = _G.NHAnatomyBench
if not B then return "FAIL no bench renderer" end
local Def = B.Def
if not Def then return "FAIL bench has no species" end
local Log = {}
local function shot(name, hold) P:SetAttribute("NHShot", name) task.wait(hold or 6) end
local function W(s) task.wait(s or 0.35) end
local KEY = { Key = 1; Driver = 2; Loupe = 3; Scalpel = 4; Tweezers = 5 }
local St = B:_TestState()
table.insert(Log, Def.Id .. " rig " .. tostring(St.Rig) .. " tracks " .. St.Tracks .. " real " .. tostring(St.Real))
shot("start")
for _, Step in Def.Steps do
	if Step.Id == "Unwind" then
		B:_TestKey(KEY.Key) W()
		for _ = 1, Step.Count do B:_TestUse("SideKey") W(0.3) end
	elseif Step.Id == "Unscrew" then
		B:_TestKey(KEY.Driver) W()
		for _ = 1, Step.Count do B:_TestUse("WingPlate") W(0.7) end
		shot("mid")
	elseif Step.Id == "Inspect" then
		B:_TestKey(KEY.Loupe) W()
		B:_TestUse("HiddenSeam") W(1.5)
		shot("mid")
	elseif Step.Id == "Trace" then
		B:_TestKey(KEY.Scalpel) W(0.6)
		local n = B:_TestTrace(nil, 0.06)
		W(1.5)
		table.insert(Log, "trace pts " .. n)
	elseif Step.Id == "Pry" then
		B:_TestKey(KEY.Driver) W()
		B:_TestUse("Plate") W(1.6)
		table.insert(Log, "plate " .. tostring(B:_TestState().PlateOpen))
		shot("open")
	elseif Step.Id == "Lift" then
		B:_TestKey(KEY.Tweezers) W()
		local Order = {}
		for _, O in Def.Organs do if O.First then table.insert(Order, O) end end
		for _, O in Def.Organs do if not O.First and not O.Flag then table.insert(Order, O) end end
		for _, O in Order do
			B:_TestUse("Organ", O.Id) W(0.6)
			if not B:_TestPlace(O.Slot) then table.insert(Log, "no slot " .. O.Slot) end
			W(0.6)
		end
	end
	table.insert(Log, Step.Id .. "->" .. tostring(B:_TestState().Step))
end
shot("done", 6)
local G = P.PlayerGui:FindFirstChild("Lesson")
local Grade = "?"
if G then for _, X in G:GetDescendants() do if X:IsA("TextLabel") and string.match(X.Text, "^[ABCDF][%+%-]?$") then Grade = X.Text end end end
table.insert(Log, "grade " .. Grade)
if Grade == "?" then return "FAIL no grade shown; " .. table.concat(Log, "; ") end
return "PASS anatomy_species_client: " .. table.concat(Log, "; ")
