--[[
	Moon phases (server). Services.Features.MoonPhases   (1.41)

	Every 5 s: workspace attributes NHMoonPhase (Full / Waning / New / Waxing: tonight's moon, ReplicatedStorage.Lineage.
	MoonPhase) and NHMoonNight (true from 20:00 to 06:00), and the character attribute NHMoonEyes on every Werewolf while
	a full moon is up (Controllers.Character.NightSight then makes their eyes glow amber for everyone, as night sight does).
	The powers themselves (Werewolf FullMoonPower, Wraith NewMoonPower / NewMoonStealth) are race passives applied by
	Player.Progression; the sky, the grade and the banners are client-side (Controllers.World.MoonPhases, World.FullMoon).
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

local Lineage = require(ReplicatedStorage.Lineage)
local SchoolTime = require(game:GetService("ReplicatedStorage"):WaitForChild("Functions"):WaitForChild("SchoolTime")) -- (2.22.0) shared night windows

local Shared = {}

function Shared.State()
	local Ok, S = pcall(function() return require(ServerScriptService.Services.School.SchoolClock).GetState() end)
	if not (Ok and S) then return nil end
	return { Phase = Lineage.MoonPhase(S.Day, S.Hour); Night = SchoolTime.IsNight(S.Hour); UntilFull = Lineage.NightsUntilFull(S.Day, S.Hour);
		Event = Lineage.MoonEvent(S.Day, S.Hour) }
end

function Shared.Tick()
	local St = Shared.State()
	if not St then return end
	workspace:SetAttribute(`NHMoonPhase`, St.Phase)
	workspace:SetAttribute(`NHMoonNight`, St.Night)
	-- (1.41) tonight's special moon, if any (by day: the coming night's), and while it's up
	workspace:SetAttribute(`NHMoonEventTonight`, St.Event)
	workspace:SetAttribute(`NHMoonEvent`, if St.Night then St.Event else nil)
	local Eyes = St.Night and St.Phase == `Full`
	for _, P in Players:GetPlayers() do
		local C = P.Character
		if C then
			local Race = P:GetAttribute(`Race`)
			-- Werewolves on every full moon; Vampires too under a crimson one
			local Want = Eyes and (Race == `Werewolf` or (Race == `Vampire` and St.Event == `Crimson`)) and P:GetAttribute(`InMainMenu`) ~= true
			if (C:GetAttribute(`NHMoonEyes`) == true) ~= Want then C:SetAttribute(`NHMoonEyes`, if Want then true else nil) end
		end
	end
	return St
end

function Shared.OnStart()
	task.spawn(function()
		while true do
			pcall(Shared.Tick)
			task.wait(5)
		end
	end)
end

return Shared
