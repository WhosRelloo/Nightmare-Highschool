local H = require(game.ServerScriptService.Services.Features.Homes)
local R = H.RoomOf(P)
local piv = R.Model:GetPivot()
for _, x in R.Model:GetDescendants() do if x.Name == "NHTrophyShown" and x:GetAttribute("NHTrophy") == "TheRegister" then local cf = piv:ToObjectSpace(x:GetPivot()) local _, s = x:GetBoundingBox() return string.format("local pos %.2f %.2f %.2f | front (-Z) points %.2f %.2f %.2f | size %.2f %.2f %.2f | class %s", cf.X, cf.Y, cf.Z, -cf.LookVector.X, -cf.LookVector.Y, -cf.LookVector.Z, s.X, s.Y, s.Z, x.ClassName) end end
return "none"
