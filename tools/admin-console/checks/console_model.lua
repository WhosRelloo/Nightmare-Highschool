local G = game.StarterPlayer.StarterPlayerScripts.Controllers.Gui
local Root = G:FindFirstChild("StaffConsole")
local Mod = Root and Root:FindFirstChild("Model")
if not Mod then return "FAIL StaffConsole.Model missing" end
local M = require(Mod:Clone())
local Fails = {}
local function Eq(Got, Want, What) if Got ~= Want then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end
local SECTIONS = { Moderate = { "Student", "Server" }, Test = { "Character", "Progress", "School", "Story", "World", "Spawns", "Self" } }

Eq(#M.Sides(1), 1, "level 1 sides") Eq(M.Sides(1)[1], "Moderate", "level 1 side")
Eq(#M.Sides(2), 2, "level 2 sides") Eq(#M.Sides(0), 0, "level 0 sides")

local S = M.New()
Eq(S.Side, "Moderate", "start side") Eq(S.Section, "Student", "start section")
S.Side = "Test" S.Section = "World"
M.SetLevel(S, 1, SECTIONS)
Eq(S.Side, "Moderate", "dropping to level 1 leaves Test") Eq(S.Section, "Student", "and resets the section")
M.SetLevel(S, 3, SECTIONS)
Eq(M.Section(S, 2, SECTIONS), true, "key 2 on Moderate") Eq(S.Section, "Server", "key 2 = Server")
Eq(M.Section(S, 5, SECTIONS), false, "key 5 on Moderate does nothing") Eq(S.Section, "Server", "still Server")

local Defs = {
	{ Id = "Kick"; Side = "Moderate"; Section = "Student"; Title = "Kick"; Target = "required"; Args = {} };
	{ Id = "Warn"; Side = "Moderate"; Section = "Student"; Title = "Warn"; Target = "required"; Args = {} };
	{ Id = "Bring"; Side = "Moderate"; Section = "Student"; Title = "Bring"; Target = "required"; Args = {} };
	{ Id = "Announce"; Side = "Moderate"; Section = "Server"; Title = "Announce"; Target = "none";
		Args = { { Name = "Text"; Kind = "text"; Required = true; Label = "Message" } } };
	{ Id = "Heal"; Side = "Test"; Section = "Character"; Title = "Heal"; Target = "required"; Args = {} };
}
local C = M.Cards(Defs, "Moderate", "Student")
Eq(#C, 3, "student cards") Eq(C[1].Id, "Bring", "sorted by title")

Eq(M.ToggleFav(S, "Warn"), true, "pin Warn") Eq(M.ToggleFav(S, "Heal"), true, "pin Heal")
local F = M.Favourites(Defs, S)
Eq(#F, 2, "two favourites") Eq(F[1].Id, "Warn", "pin order")
Eq(#M.Favourites({ Defs[1] }, S), 0, "favourites outside the registry are hidden")
Eq(M.ToggleFav(S, "Warn"), false, "unpin Warn") Eq(#M.Favourites(Defs, S), 1, "one favourite left")

for I = 1, 7 do M.Pick(S, I) end
M.Pick(S, 3)
Eq(S.Selected, 3, "selected") Eq(#S.Recent, 5, "recent holds 5") Eq(S.Recent[1], 3, "re-pick moves to front")
Eq(table.find(S.Recent, 2), nil, "oldest dropped")

local Players = {
	{ UserId = 1; Name = "alpha"; Display = "Alpha"; Muted = true };
	{ UserId = 2; Name = "bravo"; Display = "Bee" };
	{ UserId = 3; Name = "charlie"; Display = "Chuck"; Frozen = true; Note = true; InMenu = true; God = true };
}
local R = M.Rows(Players, "", { 3 })
Eq(R[1].UserId, 3, "recent first") Eq(R[2].UserId, 1, "then by name")
Eq(#M.Rows(Players, "bee", {}), 1, "filter matches display names")
Eq(#M.Rows(Players, "ALP", {}), 1, "filter ignores case")
local Fl = M.Flags(Players[3])
Eq(table.concat(Fl, ","), "NOTE,FROZEN,IN MENU,GOD", "flags order")
Eq(#M.Flags(Players[2]), 0, "no flags")

for I = 1, 7 do M.Push(S, I % 2 == 0, "msg" .. I, "T") end
Eq(#S.Feed, 5, "feed holds 5") Eq(S.Feed[1].Text, "msg7", "newest first") Eq(S.Feed[1].Ok, false, "ok kept")

local Ok, Why = M.Ready(Defs[1], {}, nil)
Eq(Ok, false, "target needed") Eq(Why, "Pick a student on the left first", "target message")
Eq((M.Ready(Defs[1], {}, 5)), true, "target given")
Ok, Why = M.Ready(Defs[4], {}, nil)
Eq(Ok, false, "required arg missing") Eq(Why, "Message is needed", "required message")
Eq((M.Ready(Defs[4], { Text = "hi" }, nil)), true, "required arg given")

local Rich = { Id = "Rich"; Target = "none"; Args = {
	{ Name = "N"; Kind = "number"; Required = true; Label = "Amount"; Min = 1; Max = 10 };
	{ Name = "C"; Kind = "choice"; Label = "Kind"; Choices = { "a", "b" } } } }
Eq((M.Ready(Rich, { N = 11 }, nil)), false, "number above Max refused")
Eq((M.Ready(Rich, { N = "abc" }, nil)), false, "non-numeric number refused")
Eq((M.Ready(Rich, { N = 5; C = "z" }, nil)), false, "unknown choice refused")
Eq((M.Ready(Rich, { N = "5"; C = "a" }, nil)), true, "valid filled card passes")
Eq((M.Ready({ Id = "Opt"; Target = "optional"; Args = {} }, {}, nil)), true, "optional target needs no pick")
local OkC, WhyC, Clean = M.Ready(Rich, { N = "5"; C = "a"; Extra = 1 }, nil)
Eq(OkC, true, "clean: ready") Eq(WhyC, nil, "clean: no reason")
Eq(typeof(Clean), "table", "clean values returned") Eq(Clean and Clean.N, 5, "clean number is a number") Eq(Clean and Clean.Extra, nil, "undeclared arg dropped")
Eq(select(3, M.Ready(Rich, { N = 11 }, nil)), nil, "refused card returns no values")

-- 1b: offline picks, user targets, prefs, the timeline, the summary, the Unban note, log labels
local S2 = M.New()
Eq(S2.Log and S2.Log.Day, 0, "log starts on today") Eq(S2.Log and S2.Log.Chip, "All", "log starts on All")
M.Pick(S2, 9, true)
Eq(S2.Offline, true, "an offline pick") Eq(S2.Selected, 9, "picked 9")
M.Pick(S2, 3)
Eq(S2.Offline, false, "an online pick")
Eq((M.Ready({ Id = "W"; Target = "required"; Args = {} }, {}, 9, nil, true)), false, "required needs them in the server")
Eq(select(2, M.Ready({ Id = "W"; Target = "required"; Args = {} }, {}, 9, nil, true)), "They're not in this server: only their history works", "offline message")
Eq((M.Ready({ Id = "R"; Target = "user"; Args = {} }, {}, nil)), false, "user target needs a pick")
Eq((M.Ready({ Id = "R"; Target = "user"; Args = {} }, {}, 9, nil, true)), true, "user target works offline")

local SECTIONS1B = { Moderate = { "Student", "Server", "Log" }, Test = { "Character", "Progress", "School", "Story", "World", "Spawns", "Self" } }
local S3 = M.New()
M.SetLevel(S3, 2, SECTIONS1B)
M.LoadPrefs(S3, { Favs = { "Warn", "Gone", "Warn" }; Side = "Test" }, { { Id = "Warn" }, { Id = "Goto" } }, SECTIONS1B)
Eq(#S3.Favs, 1, "prefs: unknown and repeated ids dropped") Eq(S3.Favs[1], "Warn", "prefs: known fav kept")
Eq(S3.Side, "Test", "prefs: saved side") Eq(S3.Section, "Character", "prefs: the side's first section")
local S4 = M.New()
M.SetLevel(S4, 1, SECTIONS1B)
M.LoadPrefs(S4, { Favs = {}; Side = "Test" }, {}, SECTIONS1B)
Eq(S4.Side, "Moderate", "prefs: a side the level doesn't allow is ignored")

local Rec = {
	Warnings = { { By = 1; At = 100; Reason = "spam"; ByName = "mod" } };
	Notes = { { By = 1; At = 300; Text = "watch them"; ByName = "mod" } };
	Bans = { { By = 2; At = 200; Days = 7; Reason = "x"; Lifted = { By = 2; At = 250 } } };
	Mutes = { { By = 1; At = 400; Until = 0 } };
}
local TL = M.Timeline(Rec, 3, 1000)
Eq(#TL, 4, "timeline entries") Eq(TL[1].Kind, "Mute", "newest first") Eq(TL[1].Lifted, false, "an open mute isn't greyed")
Eq(TL[2].Kind, "Note", "then the note") Eq(TL[2].Who, "mod", "who: ByName")
Eq(TL[3].Kind, "Ban", "then the ban") Eq(TL[3].State, "lifted", "a lifted ban") Eq(TL[3].Lifted, true, "greyed")
Eq(TL[3].Who, "2", "who without ByName: the UserId") Eq(TL[3].Text, "7-day ban: x", "ban text")
Eq(TL[4].Kind, "Warn", "oldest last") Eq(TL[1].CanRemove, true, "the owner can remove")
Eq(M.Timeline(Rec, 2, 1000)[1].CanRemove, false, "an admin can't")
Eq(M.Timeline({ Mutes = { { By = 1; At = 0; Until = 600 } } }, 3, 1000)[1].State, "ended", "a mute that ended on time")
Eq(M.Summary(Rec, 1000), "1 warning · 1 note · 1 ban (lifted) · muted until unmuted", "summary")
local D = function() return "D" end
Eq(M.UnbanNote(nil, D), nil, "no note while loading")
Eq(M.UnbanNote({ Ok = false; Error = "History unavailable" }, D), "History unavailable", "unban note: the error")
Eq(M.UnbanNote({ Ok = true; Record = {} }, D), "No ban on record: counts as permanent (owner only)", "unban note: none")
Eq(M.UnbanNote({ Ok = true; Record = { Bans = { { By = 2; At = 5; Days = 0; ByName = "boss" } } } }, D), "Lifts: permanent ban by boss, D (owner only)", "unban note: permanent")
Eq(M.UnbanNote({ Ok = true; Record = { Bans = { { By = 2; At = 5; Days = 7; ByName = "mod" } } } }, D), "Lifts: 7-day ban by mod, D", "unban note: 7 days")
Eq(M.DayLabel(0, 86400 * 10 + 5), "Today", "day 0") Eq(M.DayLabel(1, 86400 * 10 + 5), "Yesterday", "day 1")
Eq(M.DayLabel(2, 86400 * 10 + 5), "Fri 09", "day 2 (UTC day 8 = Fri 9 Jan 1970)")
Eq(M.LogHead({ At = 0; Staff = "mod"; Action = "Warn"; Target = "kid" }, function() return "09:00" end), "09:00 · mod · Warn · kid", "log head")
Eq(M.LogHead({ At = 0; Staff = "mod"; Action = "Announce" }, function() return "09:00" end), "09:00 · mod · Announce", "log head without a target")
-- (phase 2) the four new flags, after the old ones
local F2 = M.Flags({ Note = true; Transformed = true; Bells = 3; New = true; InCutscene = true })
Eq(table.concat(F2, ","), "NOTE,TRANSFORMED,WANTED,NEW,IN CUTSCENE", "phase 2 flags in order")
Eq(table.concat(M.Flags({ Bells = 2 }), ","), "", "Bell 2 is not WANTED")
Eq(table.concat(M.Flags({ Bells = 5 }), ","), "WANTED", "Bell 5 is WANTED")
Eq(table.concat(M.Flags({ Transformed = false; New = false; InCutscene = false }), ","), "", "false flags stay off")
if #Fails > 0 then return "FAIL " .. #Fails .. "\n" .. table.concat(Fails, "\n") end
return "PASS console_model"
