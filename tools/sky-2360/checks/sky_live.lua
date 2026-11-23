-- sky_live (2.36, sky-2360): World.DayCycle + World.SkyMotion in Play (Client VM). It runs its checks inside the game VM
-- (a LocalScript in PlayerGui) so it reads the controllers' live state, not a fresh module copy.
local P = game.Players.LocalPlayer
local S = Instance.new("LocalScript")
S.Source = [==[
local P = game.Players.LocalPlayer
local Lighting = game:GetService("Lighting")
local W = P.PlayerScripts:FindFirstChild("World", true)
local DC = require(W.DayCycle)
local SM = require(W.SkyMotion)
local Fails, Notes = {}, {}
local function Ok(C, What) if not C then table.insert(Fails, What) end end
local function near(a, b, e) return math.abs(a - b) <= (e or 1e-3) end
local function rgb(c) return string.format("%d,%d,%d", c.R * 255 + 0.5, c.G * 255 + 0.5, c.B * 255 + 0.5) end
local function with(Attrs, Fn)
	for K, V in Attrs do P:SetAttribute(K, V) end
	local Ok_, E = pcall(Fn)
	for K in Attrs do P:SetAttribute(K, nil) end
	if not Ok_ then table.insert(Fails, "error: " .. tostring(E)) end
end
-- moons at 23:00 (NightWeight 1)
local Base = DC.LookAt(23)
table.insert(Notes, ("night base: Brightness %.2f Exposure %.2f Ambient %s"):format(Base.Brightness, Base.ExposureCompensation, rgb(Base.Ambient)))
with({ NHMoonPhasePreview = "Full" }, function()
	local L = DC.LookAt(23)
	Ok(near(L.Brightness, Base.Brightness * 1.25, 0.02), "full: brightness x1.25 " .. L.Brightness)
	Ok(DC.SkyAt(23) == "Night", "full: sky " .. tostring(DC.SkyAt(23)))
end)
with({ NHMoonPhasePreview = "New" }, function()
	local L = DC.LookAt(23)
	Ok(near(L.Brightness, Base.Brightness * 0.4, 0.02), "new: brightness x0.4 " .. L.Brightness)
	Ok(DC.SkyAt(23) == "NightNew", "new: sky " .. tostring(DC.SkyAt(23)))
	Ok(rgb(L.Tint) == "210,216,255", "new: tint " .. rgb(L.Tint))
end)
with({ NHMoonPhasePreview = "Crimson" }, function()
	Ok(DC.SkyAt(23) == "NightCrimson", "crimson: sky " .. tostring(DC.SkyAt(23)))
	Ok(rgb(DC.LookAt(23).OutdoorAmbient) == "130,70,84", "crimson: outdoor " .. rgb(DC.LookAt(23).OutdoorAmbient))
	Ok(DC.SkyAt(12) == "Day", "crimson: the day sky untouched " .. tostring(DC.SkyAt(12)))
	local Noon = DC.LookAt(12)
	Ok(rgb(Noon.OutdoorAmbient) ~= "130,70,84", "crimson: no modifier at noon")
end)
with({ NHMoonPhasePreview = "Blue" }, function() Ok(DC.SkyAt(23) == "NightBlue", "blue: sky " .. tostring(DC.SkyAt(23))) end)
-- NightWeight
Ok(DC.NightWeight(12) == 0 and DC.NightWeight(23) == 1 and DC.NightWeight(2) == 1, "nightweight ends")
Ok(DC.NightWeight(19.25) > 0.2 and DC.NightWeight(19.25) < 0.8, "nightweight ramps " .. DC.NightWeight(19.25))
-- seasons
with({ NHSeasonPreview = "Winter" }, function()
	Ok(DC.SkyAt(12) == "WinterDay" and DC.SkyAt(18) == "WinterDusk" and DC.SkyAt(23) == "WinterNight", "winter skies")
	Ok(near(DC.LookAt(12).Density, 0.38), "winter day density " .. DC.LookAt(12).Density)
	Ok(DC.SkyAt(6) == "Dawn", "winter keeps autumn's dawn")
end)
with({ NHSeasonPreview = "Summer" }, function()
	Ok(DC.SkyAt(20) == "SummerDusk", "summer: dusk runs to 20.6, got " .. tostring(DC.SkyAt(20)))
	Ok(DC.SkyAt(21) == "SummerNight", "summer night at 21")
end)
with({ NHSeasonPreview = "Nightmare" }, function()
	Ok(DC.Moon() == "Crimson", "nightmare moon " .. tostring(DC.Moon()))
	Ok(DC.SkyAt(23) == "NightmareNight", "nightmare night sky wins over crimson: " .. tostring(DC.SkyAt(23)))
	Ok(DC.SkyAt(18) == "NightmareDusk", "nightmare dusk")
	Ok(DC.SkyAt(12) == "Day", "nightmare keeps the day")
end)
with({ NHSeasonPreview = "Nightmare", NHMoonPhasePreview = "Blue" }, function()
	Ok(DC.SkyAt(23) == "NightBlue", "an event moon over the season's moon: " .. tostring(DC.SkyAt(23)))
end)
with({ NHSkyPreview = "Storm" }, function() Ok(DC.SkyAt(12) == "Storm", "storm override") end)
-- the live look
task.wait(4) -- a swap started while the previews flipped settles (SwapSeconds 3)
local Hour = DC.Hour()
local Want = DC.LookAt(Hour)
Ok(DC.Active(), "DayCycle active")
Ok(near(Lighting.Brightness, Want.Brightness, 0.02), ("live brightness %.2f want %.2f"):format(Lighting.Brightness, Want.Brightness))
Ok(rgb(Lighting.ColorShift_Top) == rgb(Want.ColorShiftTop), "colorshift top " .. rgb(Lighting.ColorShift_Top))
Ok(near(Lighting.EnvironmentDiffuseScale, Want.EnvDiffuse, 0.02), "env diffuse " .. Lighting.EnvironmentDiffuseScale)
local C = workspace.Terrain:FindFirstChildOfClass("Clouds")
Ok(C ~= nil and near(C.Cover, Want.CloudCover, 0.02), "clouds " .. tostring(C and C.Cover))
Ok(Lighting:FindFirstChildOfClass("SunRaysEffect") ~= nil, "sunrays")
for _, N in { "NHMoonGrade", "NHNewMoonGrade", "NHMoonEventGrade" } do Ok(Lighting:FindFirstChild(N) == nil, N .. " still present") end
local Sky = Lighting:FindFirstChildOfClass("Sky")
local Set = DC.SkyAt(Hour)
local Cfg = require(game.ReplicatedStorage.Config.DayCycle)
Ok(Set ~= nil and Sky.SkyboxUp == "rbxassetid://" .. Cfg.Skies.Sets[Set].Up, "sky faces " .. tostring(Set) .. " " .. Sky.SkyboxUp)
local Pre = DC.Preloaded()
Ok(#Pre >= 1 and #Pre <= 3, "preloaded " .. table.concat(Pre, ","))
local I = SM.Info()
table.insert(Notes, ("hour %.2f set %s preloaded %s | motion tier %s beams %d weight %.2f wind %s"):format(Hour, tostring(Set), table.concat(Pre, ","), I.Tier, I.Beams, I.Weight, tostring(I.Wind)))
Ok(I.Active and I.Wind.Magnitude > 0, "wind set")
script:SetAttribute("Out", (#Fails == 0 and "PASS sky_live" or ("FAIL\n" .. table.concat(Fails, "\n"))) .. "\n" .. table.concat(Notes, "\n"))
]==]
S.Parent = P.PlayerGui
local T = os.clock()
while S:GetAttribute("Out") == nil and os.clock() - T < 20 do task.wait(0.2) end
local O = S:GetAttribute("Out") S:Destroy()
return tostring(O)
