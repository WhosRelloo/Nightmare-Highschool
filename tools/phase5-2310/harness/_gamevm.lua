local S = Instance.new("Script")
S.Source = [==[
local P = game.Players:GetPlayers()[1]
local ok, r = pcall(function()
local SSS = game.ServerScriptService.Services
local Pr = require(SSS.Player.Progression).Get(P)
local t = {} for k, v in Pr.Paths do table.insert(t, k .. "=" .. v) end
return "Level " .. Pr.Level .. " Exp " .. Pr.Exp .. " paths " .. table.concat(t, ",")

end)
script:SetAttribute("Out", if ok then tostring(r) else ("ERR " .. tostring(r)))
]==]
S.Parent = game.ServerScriptService
local t0 = os.clock()
while S:GetAttribute("Out") == nil and os.clock() - t0 < 110 do task.wait(0.25) end
local r = S:GetAttribute("Out")
S:Destroy()
return tostring(r)