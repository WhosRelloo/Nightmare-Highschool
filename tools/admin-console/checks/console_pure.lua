local Mod = game.ReplicatedStorage:FindFirstChild("Functions") and game.ReplicatedStorage.Functions:FindFirstChild("StaffConsole")
if not Mod then return "FAIL Functions.StaffConsole missing" end
local S = require(Mod:Clone())
local Fails = {}
local function Eq(Got, Want, What) if Got ~= Want then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end

-- levels
Eq(S.LevelFrom({ Studio = true }), 3, "studio")
Eq(S.LevelFrom({ Studio = true, TestLevel = 1 }), 1, "studio test level 1")
Eq(S.LevelFrom({ Studio = true, TestLevel = 0 }), 0, "studio test level 0")
Eq(S.LevelFrom({ Studio = true, TestLevel = 7 }), 3, "studio bad test level ignored")
Eq(S.LevelFrom({ Studio = true, TestLevel = 1.5 }), 3, "studio fractional test level ignored")
Eq(S.LevelFrom({ Studio = true, NotAdmin = true }), 0, "studio NotAdmin")
Eq(S.LevelFrom({ Studio = true, NotAdmin = true, TestLevel = 2 }), 2, "TestLevel beats NotAdmin")
Eq(S.LevelFrom({ Studio = false, TestLevel = 3, Rank = 0 }), 0, "live ignores TestLevel")
Eq(S.LevelFrom({ Rank = 255 }), 3, "rank 255")
Eq(S.LevelFrom({ Owner = true, Rank = 0 }), 3, "owner list")
Eq(S.LevelFrom({ Admin = true, Rank = 0 }), 2, "admin list")
Eq(S.LevelFrom({ Tester = true, Rank = 0 }), 2, "tester list")
Eq(S.LevelFrom({ Rank = 254 }), 1, "rank 254")
Eq(S.LevelFrom({ Rank = 200 }), 0, "rank 200")
Eq(S.LevelFrom({}), 0, "nothing")

-- args
local Schema = {
	{ Name = "Value"; Kind = "number"; Min = 0; Max = 120 };
	{ Name = "Reason"; Kind = "text"; Max = 5 };
	{ Name = "Pick"; Kind = "choice"; Choices = { "Shortest", "Average", "Tallest" } };
	{ Name = "Quest"; Kind = "choice"; From = "Quests" };
	{ Name = "On"; Kind = "toggle" };
	{ Name = "Position"; Kind = "position" };
}
local Lists = { Quests = { { Id = "Q1"; Name = "One" }, { Id = "Q2"; Name = "Two" } } }
local Ok, Out = S.CheckArgs(Schema, { Value = "16", Reason = "abcdefgh", Pick = "Tallest", Quest = "Q2", On = false, Extra = 1 }, Lists)
Eq(Ok, true, "good args ok")
Eq(Out.Value, 16, "number parsed")
Eq(Out.Reason, "abcde", "text cut to Max")
Eq(Out.Pick, "Tallest", "choice kept")
Eq(Out.Quest, "Q2", "list choice kept")
Eq(Out.On, false, "toggle false kept")
Eq(Out.Extra, nil, "undeclared arg dropped")
Ok, Out = S.CheckArgs(Schema, { Value = 500 }, Lists)
Eq(Ok, false, "out of range refused") Eq(Out, "Value must be 0 to 120", "range message")
Ok, Out = S.CheckArgs(Schema, { Value = "abc" }, Lists)
Eq(Ok, false, "not a number refused") Eq(Out, "Value must be a number", "nan message")
Ok, Out = S.CheckArgs(Schema, { Value = 0 / 0 }, Lists)
Eq(Ok, false, "NaN refused")
Ok, Out = S.CheckArgs(Schema, { Pick = "Huge" }, Lists)
Eq(Ok, false, "unknown choice refused") Eq(Out, "Unknown Pick: Huge", "choice message")
Ok, Out = S.CheckArgs(Schema, { Quest = "Q9" }, Lists)
Eq(Ok, false, "unknown list choice refused")
Ok, Out = S.CheckArgs(Schema, { On = "yes" }, Lists)
Eq(Ok, false, "toggle must be boolean")
Ok, Out = S.CheckArgs(Schema, { Position = "1,2,3" }, Lists)
Eq(Ok, false, "position must be a Vector3")
Ok, Out = S.CheckArgs(Schema, { Position = Vector3.new(1, 2, 3) }, Lists)
Eq(Ok, true, "Vector3 position ok")
Ok, Out = S.CheckArgs(Schema, { Position = Vector3.new(0 / 0, 0, 0) }, Lists)
Eq(Ok, false, "NaN position refused")
Ok, Out = S.CheckArgs(Schema, { Position = Vector3.new(math.huge, 0, 0) }, Lists)
Eq(Ok, false, "inf position refused")
Ok, Out = S.CheckArgs(Schema, { Position = Vector3.new(2e6, 0, 0) }, Lists)
Eq(Ok, false, "huge position refused")
Ok, Out = S.CheckArgs(Schema, nil, Lists)
Eq(Ok, true, "no args ok when none required")
Ok, Out = S.CheckArgs({ { Name = "Text"; Label = "Message"; Kind = "text"; Required = true } }, { Text = "" }, nil)
Eq(Ok, false, "required empty refused") Eq(Out, "Message is needed", "required message uses Label")
Ok, Out = S.CheckArgs({ { Name = "Tier"; Kind = "choice"; Choices = { 1, 2, 3 } } }, { Tier = 2 }, nil)
Eq(Ok, true, "numeric choice ok") Eq(Out.Tier, 2, "numeric choice kept")

-- search
local Defs = {
	{ Title = "Go to"; Help = "Teleport to them"; Synonyms = { "tp" } };
	{ Title = "Bring"; Help = "Pull them to you"; Synonyms = { "summon" } };
	{ Title = "Give Yen"; Help = "Add or take money"; Synonyms = { "cash" } };
	{ Title = "Goto a place"; Help = "Any region"; Synonyms = {} };
}
local R = S.Search(Defs, "tp")
Eq(R[1] and R[1].Title, "Go to", "synonym tp finds Go to")
R = S.Search(Defs, "  go ")
Eq(#R, 2, "go finds two") Eq(R[1].Title, "Go to", "go: alphabetical among prefix hits")
R = S.Search(Defs, "money")
Eq(R[1] and R[1].Title, "Give Yen", "help text search")
Eq(#S.Search(Defs, ""), 0, "empty query finds nothing")
Eq(#S.Search(Defs, "zzz"), 0, "no match")

-- validate
local Good = { Side = "Moderate"; Section = "Student"; Title = "Kick"; Help = "Remove them"; Icon = "Kick"; Level = 1;
	Target = "required"; Args = { { Name = "Reason"; Kind = "text"; Max = 120 } }; Danger = true; Synonyms = { "boot" } }
Eq((S.Validate("Kick", Good)), true, "good def")
local function with(K, V) local D = table.clone(Good) D[K] = V return D end
Eq((S.Validate("X", with("Side", "Nope"))), false, "bad side")
Eq((S.Validate("X", with("Section", "World"))), false, "section not on its side")
Eq((S.Validate("X", with("Level", 4))), false, "bad level")
Eq((S.Validate("X", with("Target", "maybe"))), false, "bad target")
Eq((S.Validate("X", with("Help", ""))), false, "empty help")
Eq((S.Validate("X", with("Args", { { Name = "V"; Kind = "number" } }))), false, "number without Min/Max")
Eq((S.Validate("X", with("Args", { { Name = "V"; Kind = "choice" } }))), false, "choice without Choices/From")
local TestDef = table.clone(Good) TestDef.Side = "Test" TestDef.Section = "Character" TestDef.Level = 1
Eq((S.Validate("X", TestDef)), false, "a Test command below level 2")
local P = S.Public("Kick", Good)
Eq(P.Id, "Kick", "public id") Eq(P.Run, nil, "public has no Run") Eq(P.Title, "Kick", "public title")
Eq(S.DANGER_HOLD, 0.8, "hold time")
Eq(#S.SECTIONS.Test, 7, "test sections") Eq(S.SECTIONS.Moderate[1], "Student", "first moderate section")

if #Fails > 0 then return "FAIL " .. #Fails .. "\n" .. table.concat(Fails, "\n") end
return "PASS console_pure"
