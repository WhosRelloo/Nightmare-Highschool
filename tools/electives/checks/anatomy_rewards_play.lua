-- anatomy_rewards_play (Task 12, Server VM): the Healer perk numbers at level 5, then mastery: with every species at A in
-- the Journal, one more lesson grants the title Anatomist once (a second pass grants nothing), and the monocle is tried
-- (anatomy-loupe-monocle: Grant owns it at once; the Wardrobe shows it once its template is in NHAccessories). Everything it touches is put back at the end.
local SSS = game:GetService("ServerScriptService")
local RS = game:GetService("ReplicatedStorage")
local Act = require(SSS.Services.School.Activities)
local Clock = require(SSS.Services.School.SchoolClock)
local El = require(SSS.Services.School.Electives)
local Data = require(SSS.Services.Player.Data)
local Rep = require(SSS.Services.Social.Reputation)
local Anat = require(RS.Config.Anatomy)
local P = game:GetService("Players"):GetPlayers()[1]
if not P then return "FAIL no player" end
local Lines, Fails = {}, {}
local function need(C, What) if not C then table.insert(Fails, What) end end

local Prof = Data.GetProfile(P)
Prof.Classes = Prof.Classes or {}
local Had = Prof.Classes.Anatomy
local Save = Had and table.clone(Had) or nil
if Save and Save.Journal then Save.Journal = table.clone(Save.Journal) end
local Social = Rep.Get(P)
local OldTitles, OldTitle = table.clone(Social.Titles), Social.Title
local OldPick, OldPass = El.PickFor(P), P:GetAttribute("NHHallPass")
local function putBack()
	Prof.Classes.Anatomy = Save
	Social.Titles = OldTitles
	Social.Title = OldTitle
	pcall(Rep.Sync, P)
	P:SetAttribute("NHHallPass", OldPass)
	El.ForceForTests(P, OldPick)
end

-- 1. a level-5 record: the perk numbers the (future) heal / revive hooks would read
local CD = Prof.Classes.Anatomy or {}
Prof.Classes.Anatomy = CD
CD.Level = 5
local L = CD.Level
need(math.abs(Anat.HealMult(L) - 1.4) < 1e-6, "HealMult(5) " .. Anat.HealMult(L))
need(math.abs(Anat.ReviveMult(L) - 0.68) < 1e-6, "ReviveMult(5) " .. Anat.ReviveMult(L))
table.insert(Lines, ("lvl 5 heal x%.2f revive x%.2f"):format(Anat.HealMult(L), Anat.ReviveMult(L)))

-- 2. every species at A; back to level 1 so the lesson deals the frog; no title yet
CD.Level = 1
CD.Journal = { Frog = "A"; Raven = "A"; Wyvern = "A" }
CD.Mastered = nil
local i = table.find(Social.Titles, Anat.Mastery.Title)
if i then table.remove(Social.Titles, i) end
if Social.Title == Anat.Mastery.Title then Social.Title = "" end
need(Act.JournalHandler == El.CheckMastery, "Activities.JournalHandler is not Electives.CheckMastery")

-- 3. one more lesson (a clean frog through the test hooks)
El.ForceForTests(P, "Anatomy")
local Day = Clock.GetState().Day
Clock.SetTime("10:05", Day + ((1 - Day % 5) % 5))
task.wait(0.6)
P:SetAttribute("NHHallPass", "R103")
P:SetAttribute("ClassInRoom", true)
Act.StartForTests(P, "R103")
local S = Act.GetSessionForTests(P)
if not (S and S.Subject == "Anatomy") then putBack() return "FAIL lesson did not start as Anatomy" end
task.wait(S.StartAt - os.clock() + 0.1)
local function A(a, d) Act.ActionForTests(P, a, d) task.wait(0.15) end
A("Pick", { Tool = "Key" }) for _ = 1, 8 do A("Use", { Target = "SideKey" }) end
local Pts = {} for I = 0, 40 do local t = I / 40 * 2 * math.pi * 0.97 table.insert(Pts, { math.cos(t), math.sin(t) * 1.3 }) end
A("Pick", { Tool = "Scalpel" }) A("Use", { Target = "Seam", Points = Pts })
A("Pick", { Tool = "Driver" }) A("Use", { Target = "Plate" })
A("Pick", { Tool = "Tweezers" })
for _, O in { { "HeartPump", "Heart" }, { "Lungs", "Lungs" }, { "GearGut", "Gut" } } do A("Use", { Target = "Organ", Organ = O[1] }) A("Place", { Organ = O[1], Slot = O[2] }) end
task.wait(0.8)
need(not Act.IsInActivity(P), "still in the lesson")

-- 4. granted once
local Count = 0 for _, T in Social.Titles do if T == Anat.Mastery.Title then Count += 1 end end
need(Count == 1, "title count " .. Count)
need(CD.Mastered == true, "Mastered not set")
local Again = El.CheckMastery(P, "Anatomy", CD)
need(Again and Again.Title == false, "second pass granted the title again")
local InCatalog = require(RS.Config.Accessories).ById[Anat.Mastery.Accessory] ~= nil
table.insert(Lines, "title x" .. Count .. ", mastered " .. tostring(CD.Mastered) .. ", monocle in catalog " .. tostring(InCatalog) .. ", frog " .. tostring(CD.Journal.Frog))
-- not mastered: one species below A grants nothing
local Low = { Journal = { Frog = "A"; Raven = "B"; Wyvern = "A" } }
need(El.CheckMastery(P, "Anatomy", Low) == nil, "a B still granted mastery")

putBack()
if #Fails > 0 then return "FAIL anatomy_rewards_play: " .. table.concat(Fails, "; ") .. " | " .. table.concat(Lines, "; ") end
return "PASS anatomy_rewards_play: " .. table.concat(Lines, "; ")
