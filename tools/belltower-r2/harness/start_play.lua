local B = game.ServerStorage.NHTestBridge
local P
local t0 = os.clock()
repeat task.wait(0.5) P = game.Players:GetPlayers()[1] until (P and P:GetAttribute("InMainMenu") ~= nil) or os.clock() - t0 > 30
task.wait(3)
B:Invoke("ChooseSlot", P.Name, 2)
-- (2.36.1) After School, outside every class period. 09:57 was in Break with Period 3 fifteen real seconds away,
-- so each Play run booked a real Absent on slot 2 and restore.py kept it. The next class (Homeroom) is ~19 game hours off.
B:Invoke("SetTime", "12:30")
B:Invoke("EnterSchool", P.Name)
local t1 = os.clock()
while P:GetAttribute("InMainMenu") and os.clock() - t1 < 15 do task.wait(0.25) end
task.wait(2)
return "inMenu " .. tostring(P:GetAttribute("InMainMenu"))
