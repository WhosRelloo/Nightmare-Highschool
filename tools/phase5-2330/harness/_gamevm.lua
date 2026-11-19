local S = Instance.new("Script")
S.Source = [==[
local P = game.Players:GetPlayers()[1]
local ok, r = pcall(function()
local B = game.ServerStorage.NHTestBridge
local H = game:GetService("HttpService")
P.Character:PivotTo(CFrame.new(120, 5, 50)) task.wait(0.5)
local tests = {
  {"TrophyTest", P.Name}, {"HonoursTest", P.Name}, {"RecordTest", P.Name}, {"PathsTest", P.Name}, {"TallyTest", P.Name}, {"PathRewardTest", P.Name}, {"RecognitionTest"},
  {"BroadcastTest", P.Name}, {"CurfewTest", P.Name},
  {"IncidentTest", P.Name}, {"RumourTest", P.Name}, {"RumourSafetyTest", P.Name},
  {"StaffTest", P.Name}, {"StaffPlanTest", P.Name}, {"TimetableTest", P.Name}, {"SleepTest", P.Name},
  {"RosterTest", P.Name}, {"Rostered", P.Name}, {"RelationshipCapTest", P.Name}, {"MemoryTest", P.Name},
  {"CineJudgeTest"}, {"CineGraphTest"}, {"AfterHoursMigrateTest"}, {"CineVoteTest", P.Name},
}
local out = {}
for _, t in tests do
  local ok, a, b = pcall(function() return B:Invoke(table.unpack(t)) end)
  local r = b
  if a ~= true then r = a end
  local s = (typeof(r) == "table") and (function() local o, j = pcall(H.JSONEncode, H, r) return o and j or tostring(r) end)() or tostring(r)
  table.insert(out, t[1] .. ": " .. (ok and "" or "ERR ") .. tostring(a) .. " " .. string.sub(s, 1, 260))
end
return table.concat(out, "\n")

end)
script:SetAttribute("Out", if ok then tostring(r) else ("ERR " .. tostring(r)))
]==]
S.Parent = game.ServerScriptService
local t0 = os.clock()
while S:GetAttribute("Out") == nil and os.clock() - t0 < 110 do task.wait(0.25) end
local r = S:GetAttribute("Out")
S:Destroy()
return tostring(r)