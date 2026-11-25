--[[
	Admin.BellTower (server, no OnStart): the console's Bell Tower cards (spec 2026-11-24-admin-console-2 §2), on the
	School section. A group module (see Admin.World). Calls Services.School.Notoriety and HallMonitor's public API.
]]
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local Players = game:GetService(`Players`)
local Cfg = require(ReplicatedStorage.Config.Notoriety)
-- Heat for Bell 1-5: midpoints of each bell's band, so the first cooling tick doesn't drop a bell
local BELL_HEAT = { 17.5, 35, 57.5, 80, 100 }

return function(H)
	local A = H.Meta
	local T = `Test`
	local function nt() return H.svc(`School.Notoriety`) end
	return {
		SetHeat = {
			Meta = { Side = T; Section = `School`; Title = `Set Heat`; Help = `Their notoriety Heat, 0 to 100 (the Bells follow)`; Icon = `Discipline`;
				Level = 2; Target = `required`; Danger = false; Synonyms = { `heat`, `notoriety` };
				Args = { A(`Heat`, `number`, { Min = 0; Max = 100; Required = true }) } };
			Run = function(Admin, Tg, a)
				local N = nt() if not N then return false, `Notoriety is missing` end
				local Old = N.Get(Tg).Heat
				N.SetHeat(Tg, a.Heat)
				return true, `{Tg.Name}: Heat {Old} to {a.Heat} (Bell {N.Get(Tg).Tier})`
			end;
		};
		SetBells = {
			Meta = { Side = T; Section = `School`; Title = `Set Bells`; Help = `Their Bells, 0 to 5 (Bell 3: monitors chase; 4: they converge)`; Icon = `Discipline`;
				Level = 2; Target = `required`; Danger = false; Synonyms = { `bells`, `wanted` };
				Args = { A(`Bells`, `choice`, { Choices = { 0, 1, 2, 3, 4, 5 }; Required = true }) } };
			Run = function(Admin, Tg, a)
				local N = nt() if not N then return false, `Notoriety is missing` end
				local Old = N.Get(Tg).Tier
				N.SetHeat(Tg, if a.Bells == 0 then 0 else BELL_HEAT[a.Bells])
				return true, `{Tg.Name}: Bell {Old} to {a.Bells}`
			end;
		};
		GiveSummons = {
			Meta = { Side = T; Section = `School`; Title = `Give a summons`; Help = `They must report to Room 106 outside class`; Icon = `Jail`;
				Level = 2; Target = `required`; Danger = false; Synonyms = { `summons`, `room 106` };
				Args = { A(`Type`, `choice`, { Label = `Misdeed`; From = `Misdeeds`; Required = true }) } };
			Run = function(Admin, Tg, a)
				local N = nt() if not N then return false, `Notoriety is missing` end
				local Book = require(ReplicatedStorage.Functions.Notoriety).BookType(a.Type)
				if not N.AddSummons(Tg, Book) then return false, `{Tg.Name} already owes {Cfg.SummonsLimit} summonses` end
				return true, `Summons for {Tg.Name}: {Book}`
			end;
		};
		ClearNotoriety = {
			Meta = { Side = T; Section = `School`; Title = `Clear notoriety`; Help = `Heat, Bells and summons cleared (nothing booked)`; Icon = `Discipline`;
				Level = 2; Target = `required`; Danger = true; Synonyms = { `clear heat`, `clear bells` }; Args = {} };
			Run = function(Admin, Tg)
				local N = nt() if not N then return false, `Notoriety is missing` end
				N.Clear(Tg)
				return true, `Cleared {Tg.Name}'s notoriety`
			end;
		};
		HallMonitors = {
			Meta = { Side = T; Section = `School`; Title = `Hall monitors`; Help = `On or off for this server`; Icon = `Spectate`;
				Level = 2; Target = `none`; Danger = true; Synonyms = { `monitors`, `patrol` };
				Args = { A(`On`, `toggle`, { Label = `On`; Required = true }) } };
			Run = function(Admin, _, a)
				local HM = H.svc(`School.HallMonitor`)
				if not (HM and HM.SetEnabled) then return false, `Hall monitors are missing` end
				if HM.IsEnabled() == a.On then return false, `Hall monitors are already {if a.On then `on` else `off`}` end
				HM.SetEnabled(a.On)
				return true, `Hall monitors {if a.On then `on` else `off`}`
			end;
		};
		WhosWanted = {
			Meta = { Side = T; Section = `School`; Title = `Who's Wanted`; Help = `Students at Bell 3 or more`; Icon = `Spectate`;
				Level = 2; Target = `none`; Danger = false; Synonyms = { `wanted list`, `hunted` }; Args = {} };
			Run = function()
				local N = nt() if not N then return false, `Notoriety is missing` end
				local Out = {}
				for _, P in Players:GetPlayers() do
					local S = N.Get(P)
					if S.Tier >= 3 then table.insert(Out, `{P.Name} (Bell {S.Tier}, Heat {math.floor(S.Heat)}, {if S.State ~= `` then S.State else `-`})`) end
				end
				if #Out == 0 then return true, `Nobody is Wanted` end
				return true, `Wanted: ` .. table.concat(Out, `; `)
			end;
		};
	}
end
