-- anatomy_client_setup (Task 11 step 5, Server VM): an Anatomy-enrolled player on a Tuesday period 3 in R103 starts the
-- bench lesson and leaves it running for anatomy_client.lua (Client VM) to drive. Saves the old state on attributes.
local SSS = game:GetService("ServerScriptService")
local Act = require(SSS.Services.School.Activities)
local Clock = require(SSS.Services.School.SchoolClock)
local El = require(SSS.Services.School.Electives)
local P = game:GetService("Players"):GetPlayers()[1]
if not P then return "FAIL no player" end
if Act.IsInActivity(P) then pcall(Act.ActionForTests, P, "Quit", nil) task.wait(3) end
P:SetAttribute("NHTestOldPick", El.PickFor(P) or "")
P:SetAttribute("NHTestOldPass", P:GetAttribute("NHHallPass") or "")
El.ForceForTests(P, "Anatomy")
local Day = Clock.GetState().Day
Clock.SetTime("10:05", Day + ((1 - Day % 5) % 5))
task.wait(0.6)
P:SetAttribute("NHHallPass", "R103")
P:SetAttribute("ClassInRoom", true)
local Ok, Why = Act.StartForTests(P, "R103")
local S = Act.GetSessionForTests(P)
if not (S and S.Subject == "Anatomy") then return "FAIL lesson did not start: " .. tostring(S and S.Subject) .. " " .. tostring(Ok) .. " " .. tostring(Why) .. " slot " .. tostring((Act.SlotFor(P) or {}).Subject) end
return "PASS anatomy_client_setup " .. S.Species.Id .. " twist " .. tostring(S.Twist)
