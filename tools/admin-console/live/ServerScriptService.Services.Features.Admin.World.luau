--[[
	Admin.World (server, no OnStart): the console's World cards (spec docs/superpowers/specs/2026-11-24-admin-console-2-design.md §2).
	A group module: Features.Admin calls it with its helpers (H) and merges the cards into the registry.
	Season, Moon tonight and Sky are server-wide: H.ServerWide refuses them below the owner in live servers.
	Preview just for me is a client tool (Controllers.Gui.StaffConsole.Tools), not here.
]]
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local T = `Test`
local PRESETS = { Dawn = `06:00`; Noon = `12:00`; Golden = `17:00`; Dusk = `18:30`; Midnight = `00:00`; Witching = `03:00` }
local SEASONS = { `Autumn`, `Winter`, `Spring`, `Summer`, `Nightmare` }

return function(H)
	local A = H.Meta
	local function clockDay(): (number, number)
		local SC = H.svc(`School.SchoolClock`)
		local S = SC and SC.GetState()
		return S and S.Day or 0, S and S.Hour or 12
	end
	return {
		TimePreset = {
			Meta = { Side = T; Section = `World`; Title = `Time preset`; Help = `Dawn, noon, golden hour, dusk, midnight or the witching hour`;
				Icon = `Time`; Level = 2; Target = `none`; Danger = false; Synonyms = { `dawn`, `dusk`, `midnight` };
				Args = { A(`Preset`, `choice`, { Choices = { `Dawn`, `Noon`, `Golden`, `Dusk`, `Midnight`, `Witching` }; Required = true }) } };
			Run = function(Admin, _, a)
				local SC = H.svc(`School.SchoolClock`)
				if not SC then return false, `The school clock is missing` end
				local At = PRESETS[a.Preset]
				SC.SetTime(At)
				return true, `Clock set to {At} ({a.Preset})`
			end;
		};
		SetSeason = {
			Meta = { Side = T; Section = `World`; Title = `Season`; Help = `The season for the whole server (live: owner)`;
				Icon = `SecWorld`; Level = 2; Target = `none`; Danger = false; Synonyms = { `winter`, `nightmare nights`, `event` };
				Args = { A(`Season`, `choice`, { Choices = SEASONS; Required = true }) } };
			Run = function(Admin, _, a)
				local Ok, Why = H.ServerWide(Admin)
				if not Ok then return false, Why end
				local Old = workspace:GetAttribute(`NHSeason`) or `Autumn`
				workspace:SetAttribute(`NHSeason`, if a.Season == `Autumn` then nil else a.Season)
				return true, `Season: {Old} to {a.Season}`
			end;
		};
		SetMoon = {
			Meta = { Side = T; Section = `World`; Title = `Moon tonight`; Help = `Tonight's moon for the whole server (live: owner)`;
				Icon = `Moon`; Level = 2; Target = `none`; Danger = false; Synonyms = { `crimson`, `blue moon`, `new moon` };
				Args = { A(`Moon`, `choice`, { Choices = { `Auto`, `Full`, `Waxing`, `Waning`, `New`, `Crimson`, `Blue` }; Required = true }) } };
			Run = function(Admin, _, a)
				local Ok, Why = H.ServerWide(Admin)
				if not Ok then return false, Why end
				local Lin = require(ReplicatedStorage.Lineage)
				local Day, Hour = clockDay()
				local Old = Lin.MoonOverride(Day, Hour) or `Auto`
				if a.Moon == `Auto` then
					workspace:SetAttribute(`NHMoonOverride`, nil)
					workspace:SetAttribute(`NHMoonOverrideNight`, nil)
				else
					workspace:SetAttribute(`NHMoonOverrideNight`, Lin.NightOf(Day, Hour))
					workspace:SetAttribute(`NHMoonOverride`, a.Moon)
				end
				pcall(function() H.svc(`Features.MoonPhases`).Tick() end) -- the workspace moon attributes now, not in a second
				return true, `Moon tonight: {Old} to {a.Moon}`
			end;
		};
		SetSky = {
			Meta = { Side = T; Section = `World`; Title = `Sky`; Help = `Storm, or back to the normal sky (live: owner)`;
				Icon = `SecWorld`; Level = 2; Target = `none`; Danger = false; Synonyms = { `storm`, `weather` };
				Args = { A(`Sky`, `choice`, { Choices = { `Auto`, `Storm` }; Required = true }) } };
			Run = function(Admin, _, a)
				local Ok, Why = H.ServerWide(Admin)
				if not Ok then return false, Why end
				local Old = workspace:GetAttribute(`NHSky`) or `Auto`
				workspace:SetAttribute(`NHSky`, if a.Sky == `Auto` then nil else a.Sky)
				return true, `Sky: {Old} to {a.Sky}`
			end;
		};
	}
end
