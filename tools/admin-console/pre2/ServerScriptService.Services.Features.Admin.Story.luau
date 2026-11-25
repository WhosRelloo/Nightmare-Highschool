--[[
	Admin.Story (server, no OnStart): the console's cutscene, tutorial and case cards (spec 2026-11-24-admin-console-2 §2).
	A group module (see Admin.World). Cutscene state lives in the Quests block (Quests.CineState: CutId -> "Started" |
	"Seen"); a replay (the default) writes nothing.
]]
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
-- the tutorial's three jump points, as Tutorial.Checkpoint strings (Config.Cine Cuts[..].Resume maps each to a mark)
local CHECKPOINTS = { Garden = `TutorialSneak:Garden`; Fence = `TutorialSneak:Fence`; Bus = `TutorialBus:Start` }

return function(H)
	local A = H.Meta
	local T = `Test`
	local function cine() return H.svc(`World.Cine`) end
	local function tut() return H.svc(`World.Tutorial`) end
	local function cutName(Id) local C = require(ReplicatedStorage.Config.Cine).Cuts[Id] return C and C.Name or Id end
	return {
		PlayCutscene = {
			Meta = { Side = T; Section = `Story`; Title = `Play a cutscene`; Help = `For you, or the selected student (Replay saves nothing)`; Icon = `SecStory`;
				Level = 2; Target = `optional`; Danger = false; Synonyms = { `cutscene`, `cine`, `replay` };
				Args = { A(`Id`, `choice`, { Label = `Cutscene`; From = `Cutscenes`; Required = true }), A(`Replay`, `toggle`, { Default = true }) } };
			Run = function(Admin, Tg, a)
				local Cn = cine() if not Cn then return false, `Cine is missing` end
				local Who = Tg or Admin
				if Cn.IsWatching(Who) then return false, `{Who.Name} is in a cutscene already` end
				local Replay = a.Replay ~= false
				-- Cine.Play marks the cut Started (and Seen when it ends); a replay saves nothing, so put the old mark back at the end
				local Q = if Replay then H.svc(`Quests.Quests`) else nil
				local Prev = if Q then (Q.CineState(Who) or {})[a.Id] else nil
				local Id = Cn.Play({ Who }, a.Id, { Replay = Replay; Skippable = true; OnFinish = if Q then function(Viewer)
					local S = Q.CineState(Viewer)
					if S then S[a.Id] = Prev pcall(Q.SyncForCine, Viewer) end
				end else nil })
				if Id and Q then
					local S = Q.CineState(Who)
					if S then S[a.Id] = Prev pcall(Q.SyncForCine, Who) end -- restored now too, so the mark never shows even if the cut is cut short
				end
				if not Id then return false, `Couldn't play it for {Who.Name} (in the menu, or no character)` end
				return true, `Playing {cutName(a.Id)} for {Who.Name}{if Replay then ` (replay)` else ` (first viewing)`}`
			end;
		};
		CutsceneSeen = {
			Meta = { Side = T; Section = `Story`; Title = `Cutscene seen`; Help = `Mark a cutscene Seen, or Clear it`; Icon = `SecStory`;
				Level = 2; Target = `required`; Danger = false; Synonyms = { `seen`, `unsee` };
				Args = { A(`Id`, `choice`, { Label = `Cutscene`; From = `Cutscenes`; Required = true }), A(`Mark`, `choice`, { Choices = { `Seen`, `Clear` }; Required = true }) } };
			Run = function(Admin, Tg, a)
				local Q = H.svc(`Quests.Quests`)
				local S = Q and Q.CineState(Tg)
				if not S then return false, `Their quest data isn't loaded` end
				S[a.Id] = if a.Mark == `Seen` then `Seen` else nil
				Q.SyncForCine(Tg)
				return true, `{cutName(a.Id)}: {if a.Mark == `Seen` then `seen` else `cleared`} for {Tg.Name}`
			end;
		};
		TutorialEnter = {
			Meta = { Side = T; Section = `Story`; Title = `Tutorial: enter`; Help = `Put them in Wickfield, at their checkpoint`; Icon = `SecStory`;
				Level = 2; Target = `required`; Danger = false; Synonyms = { `tutorial`, `wickfield` }; Args = {} };
			Run = function(Admin, Tg)
				local Tu = tut() if not Tu then return false, `Tutorial is missing` end
				Tu.Enter(Tg)
				return true, `{Tg.Name} is in the tutorial ({Tu.CheckpointOf(Tg) or `no checkpoint`})`
			end;
		};
		TutorialJump = {
			Meta = { Side = T; Section = `Story`; Title = `Tutorial: jump to`; Help = `The garden, the fence or the bus`; Icon = `SecStory`;
				Level = 2; Target = `required`; Danger = false; Synonyms = { `checkpoint` };
				Args = { A(`Checkpoint`, `choice`, { Choices = { `Garden`, `Fence`, `Bus` }; Required = true }) } };
			Run = function(Admin, Tg, a)
				local Tu = tut() if not Tu then return false, `Tutorial is missing` end
				local Cut, Seg = CHECKPOINTS[a.Checkpoint]:match(`^([%w_]+):([%w_]+)$`)
				Tu.Checkpoint(Tg, Cut, Seg)
				if Tg:GetAttribute(`NHTutorial`) ~= true then Tu.Enter(Tg) end
				local Mark = Tu.Resume(Tg)
				if not Mark then return false, `Couldn't place {Tg.Name} (no character or mark)` end
				return true, `{Tg.Name}: tutorial at the {string.lower(a.Checkpoint)} (mark {Mark})`
			end;
		};
		TutorialLeave = {
			Meta = { Side = T; Section = `Story`; Title = `Tutorial: leave`; Help = `Take them out of Wickfield`; Icon = `SecStory`;
				Level = 2; Target = `required`; Danger = false; Synonyms = { `leave tutorial` }; Args = {} };
			Run = function(Admin, Tg)
				local Tu = tut() if not Tu then return false, `Tutorial is missing` end
				if Tg:GetAttribute(`NHTutorial`) ~= true then return false, `{Tg.Name} is not in the tutorial` end
				Tu.Leave(Tg)
				return true, `{Tg.Name} left the tutorial`
			end;
		};
		GiveClue = {
			Meta = { Side = T; Section = `Story`; Title = `Give a clue`; Help = `One clue from a case`; Icon = `Clues`;
				Level = 2; Target = `required`; Danger = false; Synonyms = { `clue`, `evidence` };
				Args = { A(`Clue`, `choice`, { From = `Clues`; Required = true }) } };
			Run = function(Admin, Tg, a)
				local Inv = H.svc(`Quests.Investigation`)
				if not Inv then return false, `Investigation is missing` end
				local Case, Clue = tostring(a.Clue):match(`^([%w_]+)/([%w_]+)$`)
				if not Case then return false, `No such clue in that case` end
				if Inv.HasClue(Tg, Case, Clue) then return false, `{Tg.Name} has that clue already` end
				if not Inv.Grant(Tg, Case, Clue) then return false, `No such clue in that case` end
				return true, `Gave {Tg.Name} a clue: {Clue}`
			end;
		};
		ResetCase = {
			Meta = { Side = T; Section = `Story`; Title = `Reset a case`; Help = `Clear its clues, links and deduction`; Icon = `Clues`;
				Level = 2; Target = `required`; Danger = true; Synonyms = { `case reset` };
				Args = { A(`Case`, `choice`, { From = `Cases`; Required = true }) } };
			Run = function(Admin, Tg, a)
				local Inv = H.svc(`Quests.Investigation`)
				if not (Inv and Inv.ResetCase) then return false, `Investigation is missing` end
				if not Inv.ResetCase(Tg, a.Case) then return false, `Their case data isn't loaded` end
				return true, `Reset {a.Case} for {Tg.Name}`
			end;
		};
	}
end
