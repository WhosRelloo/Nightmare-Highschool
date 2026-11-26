-- anatomy_play (Task 7): on a Tuesday period 3, an Anatomy-enrolled player starts the R103 lesson and runs a clean
-- frog through the test hooks; the result lands in the Journal. Then the Moth Specimen twist hides the slots. Server VM.
local SSS = game:GetService("ServerScriptService")
local Act = require(SSS.Services.School.Activities)
local Clock = require(SSS.Services.School.SchoolClock)
local El = require(SSS.Services.School.Electives)
local Subs = require(SSS.Services.School.Substitutes)
local Data = require(SSS.Services.Player.Data)
local P = game:GetService("Players"):GetPlayers()[1]
if not P then return "FAIL no player" end
local Before = El.PickFor(P)
El.ForceForTests(P, "Anatomy")
local Day = Clock.GetState().Day
local Tue = Day + ((1 - Day % 5) % 5) -- the next (or this) Tuesday
Clock.SetTime("10:05", Tue)
task.wait(0.6)
local OldPass = P:GetAttribute("NHHallPass")
P:SetAttribute("NHHallPass", "R103") -- Attendance counts a hall pass to the room as being in class
P:SetAttribute("ClassInRoom", true)
local Lines = {}
local function Started()
	local ok = Act.StartForTests(P, "R103")
	local S = Act.GetSessionForTests(P)
	return S
end
local S = Started()
if not (S and S.Subject == "Anatomy") then return "FAIL lesson did not start as Anatomy: " .. tostring(S and S.Subject) .. " slot " .. tostring((Act.SlotFor(P) or {}).Subject) end
table.insert(Lines, "started " .. S.Species.Id .. " limit " .. math.floor(S.EndsAt - os.clock()))
task.wait(S.StartAt - os.clock() + 0.1)
local function A(a, d)
	local ok = Act.ActionForTests(P, a, d)
	task.wait(0.15)
	return ok
end
A("Pick", { Tool = "Key" }) for _ = 1, 8 do A("Use", { Target = "SideKey" }) end
local Pts = {} for I = 0, 40 do local t = I / 40 * 2 * math.pi * 0.97 table.insert(Pts, { math.cos(t), math.sin(t) * 1.3 }) end
A("Pick", { Tool = "Scalpel" }) A("Use", { Target = "Seam", Points = Pts })
A("Pick", { Tool = "Driver" }) A("Use", { Target = "Plate" })
A("Pick", { Tool = "Tweezers" })
for _, O in { { "HeartPump", "Heart" }, { "Lungs", "Lungs" }, { "GearGut", "Gut" } } do A("Use", { Target = "Organ", Organ = O[1] }) A("Place", { Organ = O[1], Slot = O[2] }) end
task.wait(0.6)
if Act.IsInActivity(P) then return "FAIL still in the lesson at step " .. tostring(S.StepIndex) .. " placed " .. tostring(S.PlacedCount) end
local CD = Data.GetProfile(P).Classes.Anatomy
if not (CD and CD.Journal and CD.Journal.Frog) then P:SetAttribute("NHHallPass", OldPass) return "FAIL no journal entry; step " .. tostring(S.StepIndex) .. " placed " .. tostring(S.PlacedCount) .. " finished " .. tostring(S.FinishedAt) end
table.insert(Lines, "frog grade " .. CD.Journal.Frog)
-- Moth's loose specimen
Subs.ForceForTests("Anatomy", "Moth", "Specimen")
S = Started()
if not S then Subs.ClearForTests() return "FAIL Moth lesson did not start" end
local Hidden = true
for _, O in S.Organs do if S.Revealed then Hidden = false end end
table.insert(Lines, "moth twist " .. tostring(S.Twist) .. " hidden " .. tostring(Hidden))
local R = Act.ActionForTests(P, "Quit", nil)
pcall(function() Subs.ClearForTests() end)
P:SetAttribute("NHHallPass", OldPass)
El.ForceForTests(P, Before)
if S.Twist ~= "Loose" or not Hidden then return "FAIL twist " .. table.concat(Lines, "; ") end
return "PASS anatomy_play: " .. table.concat(Lines, "; ")
