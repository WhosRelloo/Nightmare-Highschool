-- note_setup (playtest-blockers, Server, Play, run_live.py): slot 2 is mid-step on New Kid's "Read the note" (stage 4,
-- the stuck state the owner hit). Stand the player at locker 113, facing it, 2.5 studs out.
local Data = require(game.ServerScriptService.Services.Player.Data)
local P = game.Players:GetPlayers()[1]
local Prof = Data.GetProfile(P)
local Q = Prof.Quests
-- slot 2 has moved past New Kid since the owner's report: stage it back to "Read the note" (restore.py puts it back)
if not (Q.Active and Q.Active.NewKid) then
	Q.Done = Q.Done or {} Q.Done.NewKid = nil
	Q.Active = Q.Active or {} Q.Active.EmptyDesk = nil
	Q.Active.NewKid = { Items = {}; Started = os.time(); Data = {}; Stage = 4; Counts = { Enrol = 1; Class = 1; Leader = 1 }; Secret = {} }
	Q.Tracked = `NewKid`
	if Q.Cases and Q.Cases.EmptyDesk then Q.Cases.EmptyDesk.Clues.LockerNote = nil end
	require(game.ServerScriptService.Services.Quests.Quests).SyncForCine(P)
	task.wait(1)
end
local S = Q.Active.NewKid
if S.Stage ~= 4 then return `FAIL New Kid is at stage {S.Stage}, not 4 (the note)` end
local L = workspace.School.Quests.HallwayProps.Locker113
local Prompts = {}
for _, Pr in L:GetChildren() do if Pr:IsA(`ProximityPrompt`) then table.insert(Prompts, Pr.Name .. `:` .. Pr.ActionText) end end
local Front = L.Position + Vector3.new(0, -1.5, 2.5)
P.Character:PivotTo(CFrame.lookAt(Front, Vector3.new(L.Position.X, Front.Y, L.Position.Z)))
return `PASS New Kid stage 4 (Counts Class/Leader/Enrol done); prompts on Locker113: {table.concat(Prompts, `, `)}`
