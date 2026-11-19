local S = Instance.new("Script")
S.Source = [==[
local P = game.Players:GetPlayers()[1]
local ok, r = pcall(function()
local SSS = game.ServerScriptService.Services
local Paths = require(SSS.Player.Paths)
local Prog = require(SSS.Player.Progression)
local Pr = Prog.Get(P) Pr.Paths = {} require(SSS.Player.Data).UpdateState(P, { type = "SetProgress"; progress = Pr })
local F = Paths.Facts(P)
F.Subjects = { History = 4; Mathematics = 4; Chemistry = 4; English = 2 } F.BestStreak = 10 F.BestCard = 4
Paths.FactsOverride[P] = F
local Made = Paths.CheckNow(P)
Paths.FactsOverride[P] = nil
local t = {} for _, g in Made do table.insert(t, g.Path .. g.Tier) end
return table.concat(t, ",")

end)
script:SetAttribute("Out", if ok then tostring(r) else ("ERR " .. tostring(r)))
]==]
S.Parent = game.ServerScriptService
local t0 = os.clock()
while S:GetAttribute("Out") == nil and os.clock() - t0 < 110 do task.wait(0.25) end
local r = S:GetAttribute("Out")
S:Destroy()
return tostring(r)