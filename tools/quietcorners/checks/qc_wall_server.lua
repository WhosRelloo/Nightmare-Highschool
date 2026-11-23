local P = game.Players:GetPlayers()[1]
local Inv = require(game.ServerScriptService.Services.Quests.Investigation)
for _, C in { "LockerNote", "DeskCarving", "AttendanceSheet", "ArchiveCard" } do Inv.Grant(P, "EmptyDesk", C) end
local Out = {}
local A = Inv.Link(P, "EmptyDesk", "DeskCarving", "AttendanceSheet", "Originals") table.insert(Out, "right pair, wrong question -> " .. tostring(A))
task.wait(1.6) -- LINK_COOLDOWN
local B = Inv.Link(P, "EmptyDesk", "DeskCarving", "AttendanceSheet", "Erased") table.insert(Out, "right pair, right question -> " .. tostring(B))
task.wait(0.5) -- (S4) let Quests' deferred Sync go out: server.py destroys this Script on return, which kills a pending defer and leaves PendingSync stuck
local Pass = A == false and B == true
return (Pass and "PASS qc_wall_server\n" or "FAIL qc_wall_server\n") .. table.concat(Out, "\n")
