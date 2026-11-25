-- note_after (playtest-blockers, Server, Play, run_live.py): after a real E press at locker 113, New Kid's note step
-- is done (the quest moved past stage 4 or completed) and the LockerNote clue is in the Empty Desk case file.
local Data = require(game.ServerScriptService.Services.Player.Data)
local P = game.Players:GetPlayers()[1]
local Q = Data.GetProfile(P).Quests
local S = Q.Active and Q.Active.NewKid
local Done = Q.Done and Q.Done.NewKid ~= nil or false
local Clue = Q.Cases and Q.Cases.EmptyDesk and Q.Cases.EmptyDesk.Clues and Q.Cases.EmptyDesk.Clues.LockerNote
if S and S.Stage == 4 and (S.Counts.Note or 0) < 1 then return `FAIL New Kid is still on the note` end
if not (Done and Clue) then return `FAIL New Kid done=` .. tostring(Done) .. ` clue=` .. tostring(Clue ~= nil) end
local Next = Q.Active and Q.Active.EmptyDesk ~= nil
return string.format(`PASS note read: New Kid %s; EmptyDesk active %s; LockerNote clue %s`,
	if S then `stage ` .. S.Stage else (if Done then `completed` else `gone`), tostring(Next), tostring(Clue ~= nil))
