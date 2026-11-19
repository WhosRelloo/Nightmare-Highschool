local H = require(game.ServerScriptService.Services.Features.Homes)
local R = H.RoomOf(P)
local d = H.Get(P)
local spots = 0
for _, x in R.Model:GetDescendants() do if x.Name:match("^WallSpot") then spots += 1 end end
local tpls = {} for _, c in game.ServerStorage.NHHomes:GetChildren() do table.insert(tpls, c.Name) end
return "current " .. tostring(d and d.Current) .. " wallspots " .. spots .. " | templates: " .. table.concat(tpls, ",") .. " | pivot " .. tostring(R.Model:GetPivot())
