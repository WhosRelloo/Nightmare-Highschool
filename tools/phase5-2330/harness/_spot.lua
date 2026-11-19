local H = require(game.ServerScriptService.Services.Features.Homes)
local R = H.RoomOf(P)
for _, x in R.Model:GetDescendants() do if x.Name == "NHTrophyShown" and x:GetAttribute("NHTrophy") == "TheRegister" then local p = x:GetPivot().Position return string.format("%.2f,%.2f,%.2f", p.X, p.Y, p.Z) end end
return "none"
