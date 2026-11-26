-- anatomy_species_after (Server VM): reports the Journal grades the species runs left, then puts back the Anatomy class
-- record (level, Journal), the pick and the hall pass that anatomy_species_setup kept.
local SSS = game:GetService("ServerScriptService")
local HS = game:GetService("HttpService")
local Act = require(SSS.Services.School.Activities)
local El = require(SSS.Services.School.Electives)
local Data = require(SSS.Services.Player.Data)
local P = game:GetService("Players"):GetPlayers()[1]
if Act.IsInActivity(P) then pcall(Act.ActionForTests, P, "Quit", nil) task.wait(1) end
local Prof = Data.GetProfile(P)
local CD = Prof.Classes and Prof.Classes.Anatomy
local J = CD and CD.Journal or {}
local Got = ("raven %s wyvern %s"):format(tostring(J.Raven), tostring(J.Wyvern))
local Old = P:GetAttribute("NHTestOldClass")
if Old ~= nil then
	Prof.Classes.Anatomy = if Old == "" then nil else HS:JSONDecode(Old)
	P:SetAttribute("NHTestOldClass", nil)
end
local Pass = P:GetAttribute("NHTestOldPass")
P:SetAttribute("NHHallPass", if Pass == "" then nil else Pass)
local Pick = P:GetAttribute("NHTestOldPick")
El.ForceForTests(P, if Pick == "" then nil else Pick)
local Back = Prof.Classes.Anatomy
return "PASS anatomy_species_after: " .. Got .. " | put back level " .. tostring(Back and Back.Level) ..
	" journal " .. (if Back and Back.Journal then HS:JSONEncode(Back.Journal) else "none")
