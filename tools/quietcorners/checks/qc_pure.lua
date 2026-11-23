local RS = game.ReplicatedStorage
local Mod = RS:FindFirstChild("Functions") and RS.Functions:FindFirstChild("QuietCorners")
if not Mod then return "FAIL Functions.QuietCorners missing" end
local QC = require(Mod:Clone())
local Fails = {}
local function Eq(Got, Want, What) if Got ~= Want then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end
-- races and art (§12 fallback: race -> Human -> kit)
Eq(QC.Race("Wraith"), "Wraith", "race ok") Eq(QC.Race("Dragon"), "Human", "race unknown") Eq(QC.Race(nil), "Human", "race nil")
local Art = { Slip = { Human = 11, Vampire = 12, Ghoul = 0 }, Ticks = 13, Book = 0 }
Eq(QC.Image(Art, "Slip", "Vampire"), "rbxassetid://12", "per race") Eq(QC.Image(Art, "Slip", "Ghoul"), "rbxassetid://11", "race 0 -> Human")
Eq(QC.Image(Art, "Slip", "Priest"), "rbxassetid://11", "race missing -> Human") Eq(QC.Image(Art, "Ticks"), "rbxassetid://13", "shared")
Eq(QC.Image(Art, "Book"), nil, "0 = kit fallback") Eq(QC.Image(Art, "Nope"), nil, "missing piece")
Eq(QC.Image({ Slip = { Human = 0 } }, "Slip", "Wraith"), nil, "no Human = kit fallback")
-- crests: the Unaffiliated rule (spec §8)
local D = { Crest = { Ink = 1, Unaffiliated = 9 }, CrestFlip = { Ink = 2, Unaffiliated = 10 } }
Eq(QC.Crest(D, "Ink"), "rbxassetid://1", "crest Ink") Eq(QC.Crest(D, "Ink", true), "rbxassetid://2", "flip Ink")
Eq(QC.Crest(D, nil, true), "rbxassetid://10", "no clique = Unaffiliated") Eq(QC.Crest(D, "Vigil"), "rbxassetid://9", "no art = Unaffiliated")
Eq(QC.Crest(D, "Seal"), "rbxassetid://9", "never anything else")
Eq(QC.CliqueOf({ Clique = "Pack" }), "Pack", "clique field") Eq(QC.CliqueOf({ Faction = "CrimsonCourt" }), "Court", "faction Court")
Eq(QC.CliqueOf({ Faction = "Vigil" }), "Vigil", "faction Vigil") Eq(QC.CliqueOf({ Role = "Custodian" }), nil, "staff")
Eq(QC.FlipOffset(0), Vector2.new(0, 0), "frame 0") Eq(QC.FlipOffset(5), Vector2.new(256, 256), "frame 5")
Eq(QC.FlipOffset(15), Vector2.new(768, 768), "frame 15") Eq(QC.FlipOffset(99), Vector2.new(768, 768), "clamp")
-- the HUD state (spec §2)
local function St(T) T.Now = T.Now or 100 return QC.State(T) end
Eq(St({ LastActive = 99 }), "Active", "active") Eq(St({ LastActive = 94 }), "Calm", "calm after 6 s")
Eq(St({ LastActive = 99, CombatUntil = 101 }), "Combat", "combat") Eq(St({ LastActive = 99, CombatUntil = 101, Dialogue = true }), "Dialogue", "dialogue over combat")
Eq(St({ Menu = true, Dialogue = true }), "Menu", "menu over dialogue") Eq(St({ Cut = true, Menu = true }), "Cut", "cut over all")
Eq(St({ Lesson = true, LastActive = 99 }), "Lesson", "lesson")
Eq(QC.Mode("Vanish"), "Vanish", "mode") Eq(QC.Mode("Loud"), "Ghost", "mode default")
Eq(QC.HudTarget("Calm", "Ghost", "Compass", false), 0.65, "ghost") Eq(QC.HudTarget("Calm", "Vanish", "Vitals", false), 1, "vanish")
Eq(QC.HudTarget("Calm", "Always", "TopLeft", false), 0, "always") Eq(QC.HudTarget("Calm", "Ghost", "Compass", true), 0, "awake")
Eq(QC.HudTarget("Combat", "Ghost", "Vitals", false), 0, "combat vitals") Eq(QC.HudTarget("Combat", "Always", "TopLeft", false), 0.65, "combat focus")
Eq(QC.HudTarget("Dialogue", "Always", "Vitals", true), 1, "dialogue hides") Eq(QC.HudTarget("Lesson", "Ghost", "TopLeft", false), 0, "lesson top-left")
Eq(QC.HudTarget("Lesson", "Ghost", "Compass", false), 1, "lesson compass") Eq(QC.HudTarget("Active", "Vanish", "Compass", false), 0, "active")
-- slips (spec §3)
Eq(QC.SlipsQueued("Combat"), true, "queue in combat") Eq(QC.SlipsQueued("Calm"), false, "show in calm") Eq(QC.SlipsQueued("Menu"), true, "queue in menu")
Eq(QC.Danger("Bad"), true, "danger") Eq(QC.Danger("Warning"), false, "warning is an event")
Eq(QC.MaxSlips(false), 3, "max pc") Eq(QC.MaxSlips(true), 2, "max phone") Eq(QC.Waiting(2), "2 waiting", "stub") Eq(QC.Waiting(0), "", "no stub")
Eq(QC.SlipOpen({ Title = "Text from Odette Marsh" }), "Texts", "open texts") Eq(QC.SlipOpen({ Title = "New insight" }), "Evidence", "open evidence")
Eq(QC.SlipOpen({ Title = "Hi", Open = "Journal" }), "Journal", "explicit") Eq(QC.SlipOpen({ Title = "Yen" }), nil, "not routed")
Eq(QC.SlipOpen({ Open = "Locker" }), nil, "unknown route")
Eq(QC.Ellipsize("one two three", function(S) return #S <= 10 end), "one two…", "ellipsize") Eq(QC.Ellipsize("short", function() return true end), "short", "fits")
-- prompts
Eq(QC.Nearest({ a = 9, b = 3, c = 7 }), "b", "nearest") Eq(QC.Nearest({}), nil, "none")
Eq(QC.KeySize("E"), 22, "key 1") Eq(QC.KeySize("TAP"), 20, "key 3")
Eq(QC.TagWidth(100), 320, "tag min") Eq(QC.TagWidth(300), 390, "tag grows") Eq(QC.TagWidth(900), 520, "tag max")
Eq(QC.Phone(Vector2.new(844, 390)), true, "phone") Eq(QC.Phone(Vector2.new(1920, 1080)), false, "pc")
-- dialogue
Eq(QC.Tone("Sly"), "Sly", "tone") Eq(QC.Tone("Rude"), nil, "no tone")
local Fit30 = function(S) return #S <= 30 end
Eq(QC.CardSub("The Ink Club", "second year", nil, Fit30), "The Ink Club · second year", "sub")
Eq(QC.CardSub("The Ink Club", "second year", "Friendly", Fit30), "The Ink Club · second year", "relation dropped first")
Eq(QC.CardSub(nil, "Custodian", "Friendly", Fit30), "Custodian · Friendly", "staff")
-- the Evidence Wall (spec §7)
local Case = { Clues = { A = { Name = "a", Kind = "Note", Order = 1 }, B = { Name = "b", Kind = "Photo", Order = 2 },
	C = { Name = "c", Kind = "Record", Order = 3 }, H = { Name = "h", Kind = "Record", Order = 4, Hidden = true } },
	Questions = { { Id = "Q1", Ask = "one?" }, { Id = "Q2", Ask = "two?" }, { Id = "Q3", Ask = "three?", Bonus = true } } }
local W = QC.Wall(Case, { Clues = { A = true, B = true }, Insights = { { Id = "Q1", Text = "yes", A = "A", B = "B" } } }, {})
Eq(#W.Clues, 3, "hidden clue not shown until found") Eq(W.Clues[1].Id, "A", "order") Eq(W.Clues[2].Kind, "Object", "photo without a picture -> Object")
Eq(W.Clues[3].Found, false, "C missing") Eq(W.Questions[1].State, "Answered", "Q1 answered") Eq(W.Questions[2].State, "Empty", "Q2 empty")
Eq(W.Progress, "Clues 2 of 3 · Answered 1 of 2", "progress") Eq(W.Ready, false, "not ready")
local Pins, Send = QC.Pin({}, "Q2", 1, "A") Eq(Send, nil, "half pinned")
Eq(QC.Wall(Case, { Clues = { A = true } }, Pins).Questions[2].State, "Half", "half state")
Pins, Send = QC.Pin(Pins, "Q2", 2, "A") Eq(Send, nil, "one clue twice in a question isn't a pair") Eq(Pins.Q2[1], nil, "moved to slot 2")
Pins, Send = QC.Pin(Pins, "Q2", 1, "C") Eq(Send and Send.Question, "Q2", "pair sent") Eq(Send and Send.A, "C", "pair A") Eq(Send and Send.B, "A", "pair B")
Eq(QC.Unpin(Pins, "Q2").Q2, nil, "unpin")
W = QC.Wall(Case, { Clues = { A = true, B = true, C = true }, Insights = { { Id = "Q1" }, { Id = "Q2" } } }, {})
Eq(W.Ready, true, "ready without the bonus")
local M = {} M = QC.Miss(M, "Q2") Eq(QC.ShowHint(M, "Q2"), false, "1 miss") M = QC.Miss(M, "Q2") Eq(QC.ShowHint(M, "Q2"), true, "2 misses")
-- the configs exist, and the crests are already filled
local Cfg = RS:FindFirstChild("Config")
for _, N in { "QuietCornersArt", "DialogueArt", "EvidenceArt" } do if not (Cfg and Cfg:FindFirstChild(N)) then table.insert(Fails, "Config." .. N .. " missing") end end
if Cfg and Cfg:FindFirstChild("DialogueArt") then
	local DA = require(Cfg.DialogueArt:Clone())
	for _, K in { "Ink", "Vigil", "Court", "Athletes", "Delinquents", "Pack", "Ordinary", "Choir", "Unaffiliated" } do
		Eq(type(DA.Crest[K]) == "number" and DA.Crest[K] > 0, true, "crest id " .. K) Eq(type(DA.CrestFlip[K]) == "number" and DA.CrestFlip[K] > 0, true, "flip id " .. K)
	end
end
return #Fails == 0 and "PASS qc_pure" or ("FAIL\n" .. table.concat(Fails, "\n"))
