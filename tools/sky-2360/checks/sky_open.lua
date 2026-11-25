-- sky_open (sky-2360 open rows, Client, Play): 02:00 on every moon, Spring and Summer skies, and a moon event the server set.
-- Runs inside the game VM (a LocalScript in PlayerGui) like sky_live, so it reads the live DayCycle.
local P = game.Players.LocalPlayer
local S = Instance.new("LocalScript")
S.Source = [==[
local P = game.Players.LocalPlayer
local W = P.PlayerScripts:FindFirstChild("World", true)
local DC = require(W.DayCycle)
local Cfg = require(game.ReplicatedStorage.Config.DayCycle)
local Fails, Notes = {}, {}
local function Ok(C, What) if not C then table.insert(Fails, What) end end
local function near(a, b, e) return math.abs(a - b) <= (e or 1e-3) end
local function with(Attrs, Fn)
	for K, V in Attrs do P:SetAttribute(K, V) end
	local Ok_, E = pcall(Fn)
	for K in Attrs do P:SetAttribute(K, nil) end
	if not Ok_ then table.insert(Fails, "error: " .. tostring(E)) end
end
local function hasFaces(Set) return Set ~= nil and Cfg.Skies.Sets[Set] ~= nil and Cfg.Skies.Sets[Set].Up ~= nil end
-- 1. 02:00 on every moon: deep night, the same sky as 23:00, and the same 02:00 dimming on every moon
Ok(near(DC.NightWeight(2), 1, 0.01), "NightWeight(2) " .. DC.NightWeight(2))
local Ratio
for _, Moon in { "Waxing", "Full", "New", "Crimson", "Blue" } do
	with({ NHMoonPhasePreview = Moon }, function()
		local Name = Moon
		local A, B = DC.LookAt(2), DC.LookAt(23)
		Ok(DC.SkyAt(2) == DC.SkyAt(23), Name .. ": 02:00 sky " .. tostring(DC.SkyAt(2)) .. " vs 23:00 " .. tostring(DC.SkyAt(23)))
		Ok(hasFaces(DC.SkyAt(2)), Name .. ": 02:00 sky has no faces")
		local R = A.Brightness / B.Brightness
		Ratio = Ratio or R
		Ok(near(R, Ratio, 0.02), ("%s: 02:00/23:00 brightness %.3f, other moons %.3f"):format(Name, R, Ratio))
		table.insert(Notes, ("02:00 %s: sky %s brightness %.2f"):format(Name, tostring(DC.SkyAt(2)), A.Brightness))
	end)
end
-- 2. Spring and Summer: every hour has a sky with faces, and the day is brighter than the night
for _, Se in { "Spring", "Summer" } do
	with({ NHSeasonPreview = Se }, function()
		Ok(DC.Season() == Se, Se .. ": season reads " .. tostring(DC.Season()))
		local Row = {}
		for _, H in { 6, 12, 18.5, 23 } do
			local Set = DC.SkyAt(H)
			Ok(hasFaces(Set), ("%s %.1f: sky %s has no faces"):format(Se, H, tostring(Set)))
			table.insert(Row, ("%.1f=%s/%.2f"):format(H, tostring(Set), DC.LookAt(H).Brightness))
		end
		Ok(DC.LookAt(12).Brightness > DC.LookAt(23).Brightness, Se .. ": noon not brighter than night")
		table.insert(Notes, Se .. ": " .. table.concat(Row, " "))
	end)
end
-- 3. a moon event the server set (workspace NHMoonEventTonight, replicated)
local Ev = workspace:GetAttribute("NHMoonEventTonight")
Ok(Ev == "Crimson", "server event not seen: " .. tostring(Ev))
Ok(DC.Moon() == "Crimson", "Moon() with the server event: " .. tostring(DC.Moon()))
Ok(hasFaces(DC.SkyAt(23)), "event night sky " .. tostring(DC.SkyAt(23)))
table.insert(Notes, ("server event Crimson: Moon %s, 23:00 sky %s brightness %.2f"):format(tostring(DC.Moon()), tostring(DC.SkyAt(23)), DC.LookAt(23).Brightness))
script:SetAttribute("Out", (#Fails == 0 and "PASS sky_open" or ("FAIL\n" .. table.concat(Fails, "\n"))) .. "\n" .. table.concat(Notes, "\n"))
]==]
S.Parent = P.PlayerGui
local T = os.clock()
while S:GetAttribute("Out") == nil and os.clock() - T < 20 do task.wait(0.2) end
local O = S:GetAttribute("Out") S:Destroy()
return tostring(O)
