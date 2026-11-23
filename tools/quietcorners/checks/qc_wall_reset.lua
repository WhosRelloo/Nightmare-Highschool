-- qc_wall_reset (S4, game VM through server.py): put slot 2's EmptyDesk case back to fresh (no clues, no insights, unsolved), so
-- qc_wall_server and qc_wall see the state they were written for. The round's restore.py puts the real Quests back.
local P = game.Players:GetPlayers()[1]
local Inv = require(game.ServerScriptService.Services.Quests.Investigation)
local C = Inv.Get(P, "EmptyDesk")
if not C then return "FAIL no case" end
C.Clues, C.Insights, C.Solved, C.SolvedText = {}, {}, false, nil
require(game.ServerScriptService.Services.Quests.Quests).SyncForCine(P)
task.wait(1.6) -- LINK_COOLDOWN from any earlier Link
task.wait(0.5) -- (S4) let Quests' deferred Sync go out: server.py destroys this Script on return, which kills a pending defer and leaves PendingSync stuck
return "reset EmptyDesk"
