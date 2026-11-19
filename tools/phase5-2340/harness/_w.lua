local B = game.ServerStorage.NHTestBridge
local H = game:GetService("HttpService")
local P = game.Players:GetPlayers()[1]
local out = {}
for _, t in { {"WardrobeTest", P.Name}, {"TodayTest", P.Name}, {"PathsTest", P.Name}, {"PathRewardTest", P.Name}, {"TrophyTest", P.Name} } do
  local ok, a, b = pcall(function() return B:Invoke(table.unpack(t)) end)
  local r = if a ~= true then a else b
  local s = (typeof(r) == "table") and (function() local o, j = pcall(H.JSONEncode, H, r) return o and j or tostring(r) end)() or tostring(r)
  table.insert(out, t[1] .. ": " .. (ok and "" or "ERR ") .. tostring(a) .. " " .. string.sub(s, 1, 400))
end
return table.concat(out, "\n")
