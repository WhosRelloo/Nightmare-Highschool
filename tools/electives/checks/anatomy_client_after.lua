-- anatomy_client_after (Server VM): the frog's Journal grade from the client run; puts the pick and hall pass back.
local SSS = game:GetService("ServerScriptService")
local Act = require(SSS.Services.School.Activities)
local El = require(SSS.Services.School.Electives)
local Data = require(SSS.Services.Player.Data)
local P = game:GetService("Players"):GetPlayers()[1]
if Act.IsInActivity(P) then pcall(Act.ActionForTests, P, "Quit", nil) task.wait(1) end
local CD = Data.GetProfile(P).Classes.Anatomy
local G = CD and CD.Journal and CD.Journal.Frog
local Pass = P:GetAttribute("NHTestOldPass")
P:SetAttribute("NHHallPass", if Pass == "" then nil else Pass)
local Pick = P:GetAttribute("NHTestOldPick")
El.ForceForTests(P, if Pick == "" then nil else Pick)
if not G then return "FAIL no journal grade" end
return "PASS anatomy_client_after: frog " .. tostring(G)
