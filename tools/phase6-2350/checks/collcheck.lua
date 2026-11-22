-- collcheck (final fix round): Tutorial.Enter puts parts added to the character later (a Tool's handle) into the tutorial collision
-- group; Leave drops the watcher and puts the character back in Default. Server VM, Play, slot 2 (TutorialEnter / TutorialLeave through
-- the bridge are done here directly through the service).
local P = game.Players:GetPlayers()[1]
local T = require(game.ServerScriptService.Services.World.Tutorial)
local Out = {}
local function row(Ok, Text) table.insert(Out, (Ok and "ok   " or "FAIL ") .. Text) end
T.Enter(P)
local A = Instance.new("Part") A.Name = "__LateA" A.Parent = P.Character
task.wait(0.2)
row(A.CollisionGroup == "TutorialPlayers", "a part added after Enter joins the tutorial group (" .. A.CollisionGroup .. ")")
T.Leave(P)
local B = Instance.new("Part") B.Name = "__LateB" B.Parent = P.Character
task.wait(0.2)
row(B.CollisionGroup == "Default", "a part added after Leave stays Default (" .. B.CollisionGroup .. ")")
row(A.CollisionGroup == "Default", "the character is back in Default after Leave (" .. A.CollisionGroup .. ")")
A:Destroy() B:Destroy()
local Pass = true for _, r in Out do if r:sub(1, 4) == "FAIL" then Pass = false end end
return (Pass and "COLL OK\n" or "COLL FAIL\n") .. table.concat(Out, "\n")
