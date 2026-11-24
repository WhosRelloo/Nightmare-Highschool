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

if #Fails > 0 then return "FAIL " .. #Fails .. "\n" .. table.concat(Fails, "\n") end
return "PASS console_model"
