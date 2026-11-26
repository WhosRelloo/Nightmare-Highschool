-- electives_play (Task 4): enrol, the attribute, the term lock, a closed elective refused. Server VM, in Play.
local SSS = game:GetService("ServerScriptService")
local E = require(SSS.Services.School.Electives)
local P = game:GetService("Players"):GetPlayers()[1]
if not P then return "FAIL no player" end
local Fails = {}
local function Eq(G, W, What) if G ~= W then table.insert(Fails, What .. ": got " .. tostring(G) .. " want " .. tostring(W)) end end
local Before = E.PickFor(P)
E.ForceForTests(P, nil)
Eq(P:GetAttribute("ElectivePick"), nil, "cleared")
local ok, why = E.Enrol(P, "Workshop") Eq(ok, false, "closed refused") Eq(why, "Closed", "reason")
ok = E.Enrol(P, "Anatomy") Eq(ok, true, "Anatomy enrols") Eq(P:GetAttribute("ElectivePick"), "Anatomy", "attribute")
ok, why = E.Enrol(P, "Anatomy") Eq(ok, false, "same term again") Eq(why, "Locked", "locked this term")
Eq(E.PickFor(P), "Anatomy", "PickFor") Eq(E.IsLocked(P), true, "IsLocked")
local C = require(game.ReplicatedStorage.Config.Classes)
Eq(C.For("Period 3", 1, P).Subject, "Anatomy", "Classes.For reads the player's pick")
local Desk = game:GetService("CollectionService"):GetTagged("NHRegistrarDesk")[1]
Eq(Desk ~= nil and Desk:FindFirstChild("NHRegistrarPrompt", true) ~= nil, true, "desk prompt")
E.ForceForTests(P, Before)
if #Fails > 0 then return "FAIL\n" .. table.concat(Fails, "\n") end
return "PASS electives_play"
