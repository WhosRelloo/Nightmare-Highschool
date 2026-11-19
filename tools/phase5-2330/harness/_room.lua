local H = require(game.ServerScriptService.Services.Features.Homes)
local ok, e = pcall(H.Enter, P)
task.wait(2)
local R = H.RoomOf(P)
local piv = R and R.Model:GetPivot()
local shown = 0
for _, d in R.Model:GetDescendants() do if d.Name == "NHTrophyShown" then shown += 1 end end
return tostring(ok) .. " " .. tostring(e) .. " pivot " .. tostring(piv and piv.Position) .. " shown " .. shown
