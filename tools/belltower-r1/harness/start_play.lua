local B = game.ServerStorage.NHTestBridge
local P
local t0 = os.clock()
repeat task.wait(0.5) P = game.Players:GetPlayers()[1] until (P and P:GetAttribute("InMainMenu") ~= nil) or os.clock() - t0 > 30
task.wait(3)
B:Invoke("ChooseSlot", P.Name, 2)
B:Invoke("SetTime", "09:57")
B:Invoke("EnterSchool", P.Name)
local t1 = os.clock()
while P:GetAttribute("InMainMenu") and os.clock() - t1 < 15 do task.wait(0.25) end
task.wait(2)
return "inMenu " .. tostring(P:GetAttribute("InMainMenu"))
