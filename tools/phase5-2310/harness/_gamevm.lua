local S = Instance.new("Script")
S.Source = [==[
local P = game.Players:GetPlayers()[1]
local ok, r = pcall(function()
local B = game.ServerStorage.NHTestBridge
local P
local t0 = os.clock()
repeat task.wait(0.5) P = game.Players:GetPlayers()[1] until (P and P:GetAttribute("InMainMenu") ~= nil) or os.clock() - t0 > 30
task.wait(3)
B:Invoke("ChooseSlot", P.Name, 2)
B:Invoke("SetTime", "21:30")
B:Invoke("EnterSchool", P.Name)
local t1 = os.clock()
while P:GetAttribute("InMainMenu") and os.clock() - t1 < 15 do task.wait(0.25) end
task.wait(2)
return "inMenu " .. tostring(P:GetAttribute("InMainMenu"))

end)
script:SetAttribute("Out", if ok then tostring(r) else ("ERR " .. tostring(r)))
]==]
S.Parent = game.ServerScriptService
local t0 = os.clock()
while S:GetAttribute("Out") == nil and os.clock() - t0 < 110 do task.wait(0.25) end
local r = S:GetAttribute("Out")
S:Destroy()
return tostring(r)