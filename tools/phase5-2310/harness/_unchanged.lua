local SSS = game.ServerScriptService.Services
local Prog = require(SSS.Player.Progression)
local Paths = require(SSS.Player.Paths)
local out = {}
-- put a tier in, then EXP and a point spend must keep it
local F = Paths.Facts(P)
F.Subjects = { History = 4; Mathematics = 4; Chemistry = 4; English = 2 } F.BestStreak = 10 F.BestCard = 4
Paths.FactsOverride[P] = F Paths.CheckNow(P) Paths.FactsOverride[P] = nil
local A = Prog.Get(P)
local gain = Prog.AwardForTests(P, 50, "Class")
local B = Prog.Get(P)
table.insert(out, string.format("award +%d: L%d E%d -> L%d E%d, Academic %s", gain, A.Level, A.Exp, B.Level, B.Exp, tostring(B.Paths.Academic)))
if B.Points > 0 then
  local ok = Prog.Spend(P, "Wits", 1)
  local C = Prog.Get(P)
  table.insert(out, "spend ok " .. tostring(ok) .. " points " .. B.Points .. "->" .. C.Points .. " Academic " .. tostring(C.Paths.Academic))
else table.insert(out, "no points to spend") end
-- Hale still opens with his roll-call line
local Tree = require(game.ServerStorage.Dialogue.Hale)
local fake = { PathTier = function() return 4 end; Decided = function() return nil end; Objective = function() return nil end; Member = function() return false end; State = function() return "Acquaintance" end }
table.insert(out, "Hale: " .. tostring(Tree.Nodes.Hub.Text(fake)))
return table.concat(out, "\n")
