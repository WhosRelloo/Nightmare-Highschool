local CP = game:GetService("ContentProvider")
local out = {}
for _, n in { "RingBelt", "ClubCup", "PathMedalAthletic" } do
	local SA = game.ReplicatedStorage.NHTrophies[n]:FindFirstChildWhichIsA("SurfaceAppearance", true)
	local st = {}
	CP:PreloadAsync({ SA.ColorMap, SA.NormalMap }, function(id, s) table.insert(st, tostring(s):sub(23)) end)
	table.insert(out, n .. ": " .. table.concat(st, ","))
end
return table.concat(out, " | ")
