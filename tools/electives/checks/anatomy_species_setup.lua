-- anatomy_species_setup (Server VM): like anatomy_client_setup, but at a class level that deals the Raven (3) or the
-- Wyvern (5). LEVEL is replaced by the runner (sed). The old level and Journal are kept on attributes for
-- anatomy_species_after.lua to put back.
local LEVEL = 3
local SSS = game:GetService("ServerScriptService")
local HS = game:GetService("HttpService")
local Act = require(SSS.Services.School.Activities)
local Clock = require(SSS.Services.School.SchoolClock)
local El = require(SSS.Services.School.Electives)
local Data = require(SSS.Services.Player.Data)
local P = game:GetService("Players"):GetPlayers()[1]
if not P then return "FAIL no player" end
if Act.IsInActivity(P) then pcall(Act.ActionForTests, P, "Quit", nil) task.wait(3) end
local Prof = Data.GetProfile(P)
Prof.Classes = Prof.Classes or {}
local First = P:GetAttribute("NHTestOldClass") == nil
if First then   -- the first setup of a round keeps the true state
	P:SetAttribute("NHTestOldClass", if Prof.Classes.Anatomy then HS:JSONEncode(Prof.Classes.Anatomy) else "")
	P:SetAttribute("NHTestOldPick", El.PickFor(P) or "")
	P:SetAttribute("NHTestOldPass", P:GetAttribute("NHHallPass") or "")
end
local CD = Prof.Classes.Anatomy or {}
Prof.Classes.Anatomy = CD
CD.Level = LEVEL
if First then CD.Journal = {} end   -- a blank Journal: mastery cannot fire on the tester during the run (put back after)
El.ForceForTests(P, "Anatomy")
local Day = Clock.GetState().Day
Clock.SetTime("10:05", Day + ((1 - Day % 5) % 5))
task.wait(0.6)
P:SetAttribute("NHHallPass", "R103")
P:SetAttribute("ClassInRoom", true)
local Ok, Why = Act.StartForTests(P, "R103")
local S = Act.GetSessionForTests(P)
if not (S and S.Subject == "Anatomy") then return "FAIL lesson did not start: " .. tostring(Ok) .. " " .. tostring(Why) end
return "PASS anatomy_species_setup level " .. LEVEL .. " " .. S.Species.Id .. " twist " .. tostring(S.Twist)
