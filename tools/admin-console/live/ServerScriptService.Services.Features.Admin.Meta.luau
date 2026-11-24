--[[
	Admin.Meta (server only): the console's card data for every Features.Admin command (spec §4, §7).
	Side / Section place the card; Level is the minimum staff level (StaffConsole.LEVEL_NAMES); Target "required" needs a
	selected student; Args are checked by StaffConsole.CheckArgs before Run (lists from Admin.Lists()); Danger cards use
	hold-to-confirm. Owner-only rules inside a Run (permanent bans, Yen over 100k, race rites) stay in that Run.
	No OnStart: Features.Admin requires it. checks/console_registry.lua keeps it in step with Admin's C table.
]]
local function A(Name, Kind, Extra)
	local T = Extra or {}
	T.Name = Name
	T.Kind = Kind
	return T
end
local M = "Moderate"
local T = "Test"

return {
	-- Moderate / Student
	Warn = { Side = M; Section = "Student"; Title = "Warn"; Help = "Send them a staff warning"; Icon = "Warn"; Level = 1; Target = "required"; Danger = false; Synonyms = { "caution" };
		Args = { A("Reason", "text", { Max = 160 }) } };
	Mute = { Side = M; Section = "Student"; Title = "Mute"; Help = "Stop their chat in this server"; Icon = "Mute"; Level = 1; Target = "required"; Danger = false; Synonyms = { "silence" }; Args = {} };
	Unmute = { Side = M; Section = "Student"; Title = "Unmute"; Help = "Give their chat back"; Icon = "Mute"; Level = 1; Target = "required"; Danger = false; Synonyms = { "unsilence" }; Args = {} };
	Freeze = { Side = M; Section = "Student"; Title = "Freeze"; Help = "Hold them in place (again to thaw)"; Icon = "Freeze"; Level = 1; Target = "required"; Danger = false; Synonyms = { "anchor", "thaw" }; Args = {} };
	Jail = { Side = M; Section = "Student"; Title = "Detention"; Help = "Send them to the detention room"; Icon = "Jail"; Level = 1; Target = "required"; Danger = false; Synonyms = { "jail" }; Args = {} };
	Spectate = { Side = M; Section = "Student"; Title = "Spectate"; Help = "Watch them through your camera"; Icon = "Spectate"; Level = 1; Target = "required"; Danger = false; Synonyms = { "watch", "view" }; Args = {} };
	Bring = { Side = M; Section = "Student"; Title = "Bring"; Help = "Pull them to you"; Icon = "Bring"; Level = 1; Target = "required"; Danger = false; Synonyms = { "summon", "tp here" }; Args = {} };
	Goto = { Side = M; Section = "Student"; Title = "Go to"; Help = "Teleport to them"; Icon = "GoTo"; Level = 1; Target = "required"; Danger = false; Synonyms = { "tp", "teleport" }; Args = {} };
	Kick = { Side = M; Section = "Student"; Title = "Kick"; Help = "Remove them from this server"; Icon = "Kick"; Level = 1; Target = "required"; Danger = true; Synonyms = { "boot", "remove" };
		Args = { A("Reason", "text", { Max = 120 }) } };
	Ban = { Side = M; Section = "Student"; Title = "Ban"; Help = "Ban from every server (permanent: owner only)"; Icon = "Ban"; Level = 1; Target = "required"; Danger = true; Synonyms = { "banish" };
		Args = { A("Days", "choice", { Label = "Length"; Choices = { 1, 7, 30, 0 }; Required = true }), A("Reason", "text", { Max = 200 }) } };
	Unban = { Side = M; Section = "Student"; Title = "Unban"; Help = "Lift a ban by UserId"; Icon = "Ban"; Level = 1; Target = "none"; Danger = false; Synonyms = { "pardon" };
		Args = { A("UserId", "number", { Min = 1; Max = 1e12; Required = true }) } };
	Note = { Side = M; Section = "Student"; Title = "Note"; Help = "A staff note on them (empty clears it)"; Icon = "Note"; Level = 1; Target = "required"; Danger = false; Synonyms = { "memo" };
		Args = { A("Text", "text", { Max = 300 }) } };

	-- Moderate / Server
	Announce = { Side = M; Section = "Server"; Title = "Announce"; Help = "A message to everyone in this server"; Icon = "Announce"; Level = 1; Target = "none"; Danger = false; Synonyms = { "broadcast", "message" };
		Args = { A("Text", "text", { Label = "Message"; Max = 200; Required = true }) } };
	ServerLock = { Side = M; Section = "Server"; Title = "Server lock"; Help = "Only staff can join (again to unlock)"; Icon = "Lock"; Level = 1; Target = "none"; Danger = true; Synonyms = { "lock", "unlock" }; Args = {} };
	BringAll = { Side = M; Section = "Server"; Title = "Bring all"; Help = "Pull every student to you"; Icon = "Bring"; Level = 1; Target = "none"; Danger = true; Synonyms = { "summon all" }; Args = {} };
	FreezeAll = { Side = M; Section = "Server"; Title = "Freeze all"; Help = "Freeze or thaw every student"; Icon = "Freeze"; Level = 1; Target = "none"; Danger = true; Synonyms = { "thaw all" };
		Args = { A("On", "toggle", { Label = "Freeze" }) } };
	Shutdown = { Side = M; Section = "Server"; Title = "Shutdown"; Help = "Close this server for everyone"; Icon = "Shutdown"; Level = 3; Target = "none"; Danger = true; Synonyms = { "close server" };
		Args = { A("Reason", "text", { Max = 200 }) } };

	-- Test / Character
	Heal = { Side = T; Section = "Character"; Title = "Heal"; Help = "Full health, posture cleared"; Icon = "Heal"; Level = 2; Target = "required"; Danger = false; Synonyms = { "hp" }; Args = {} };
	Revive = { Side = T; Section = "Character"; Title = "Revive"; Help = "Get them up from downed"; Icon = "Revive"; Level = 2; Target = "required"; Danger = false; Synonyms = { "undown" }; Args = {} };
	God = { Side = T; Section = "Character"; Title = "God mode"; Help = "Never hurt, never downed (again to stop)"; Icon = "God"; Level = 2; Target = "required"; Danger = false; Synonyms = { "invincible", "godmode" }; Args = {} };
	Kill = { Side = T; Section = "Character"; Title = "Kill"; Help = "Drop their health to zero"; Icon = "Kill"; Level = 2; Target = "required"; Danger = true; Synonyms = { "slay" }; Args = {} };
	Speed = { Side = T; Section = "Character"; Title = "Speed"; Help = "Set their walk speed"; Icon = "Speed"; Level = 2; Target = "required"; Danger = false; Synonyms = { "walkspeed", "ws" };
		Args = { A("Value", "number", { Label = "Speed"; Min = 0; Max = 120; Required = true }) } };
	SetRace = { Side = T; Section = "Character"; Title = "Race"; Help = "Set their race and sub-race"; Icon = "Race"; Level = 2; Target = "required"; Danger = false; Synonyms = { "subrace" };
		Args = { A("Sub", "choice", { Label = "Race"; From = "Races"; Required = true }) } };
	SetTier = { Side = T; Section = "Character"; Title = "Tier"; Help = "Set their race tier"; Icon = "Race"; Level = 2; Target = "required"; Danger = false; Synonyms = { "rank" };
		Args = { A("Tier", "choice", { Choices = { 1, 2, 3 }; Required = true }) } };
	SpinHeight = { Side = T; Section = "Character"; Title = "Spin height"; Help = "A free height re-roll"; Icon = "Height"; Level = 2; Target = "required"; Danger = false; Synonyms = { "reroll height" }; Args = {} };
	SetHeight = { Side = T; Section = "Character"; Title = "Height"; Help = "Shortest, average or tallest in their range"; Icon = "Height"; Level = 2; Target = "required"; Danger = false; Synonyms = { "tall", "short" };
		Args = { A("Pick", "choice", { Label = "Height"; Choices = { "Shortest", "Average", "Tallest" }; Required = true }) } };
	SetBuild = { Side = T; Section = "Character"; Title = "Build"; Help = "Their body type and step"; Icon = "Height"; Level = 2; Target = "required"; Danger = false; Synonyms = { "body type" };
		Args = { A("Build", "choice", { Choices = { "Average", "Skinny", "Conditioned", "Heavy" }; Required = true }), A("Step", "number", { Min = 0; Max = 2 }) } };
	Transform = { Side = T; Section = "Character"; Title = "Transform"; Help = "Into their race's form, or back"; Icon = "Transform"; Level = 2; Target = "required"; Danger = false; Synonyms = { "form" }; Args = {} };
	GiveYen = { Side = T; Section = "Character"; Title = "Give Yen"; Help = "Add or take Yen (over ¥100,000: owner)"; Icon = "Yen"; Level = 2; Target = "required"; Danger = false; Synonyms = { "money", "cash" };
		Args = { A("Amount", "number", { Min = -1e7; Max = 1e7; Required = true }) } };
	GiveExp = { Side = T; Section = "Character"; Title = "Give EXP"; Help = "EXP in one category"; Icon = "Exp"; Level = 2; Target = "required"; Danger = false; Synonyms = { "xp" };
		Args = { A("Amount", "number", { Min = 0; Max = 1e6; Required = true }), A("Category", "choice", { Choices = { "Combat", "Class", "Quest", "Social", "Sport" } }) } };
	GiveGear = { Side = T; Section = "Character"; Title = "Give gear"; Help = "Any gear item"; Icon = "Gear"; Level = 2; Target = "required"; Danger = false; Synonyms = { "item" };
		Args = { A("Id", "choice", { Label = "Gear"; From = "Gear"; Required = true }) } };
	GiveSpins = { Side = T; Section = "Character"; Title = "Give spins"; Help = "Race spins"; Icon = "Race"; Level = 2; Target = "required"; Danger = false; Synonyms = { "spin" };
		Args = { A("Amount", "number", { Min = 1; Max = 50; Required = true }) } };
	GiveNameChange = { Side = T; Section = "Character"; Title = "Name change"; Help = "A free name change"; Icon = "SecCharacter"; Level = 2; Target = "required"; Danger = false; Synonyms = { "rename" }; Args = {} };

	-- Test / Progress
	SetLevel = { Side = T; Section = "Progress"; Title = "Set level"; Help = "Their character level"; Icon = "Exp"; Level = 2; Target = "required"; Danger = false; Synonyms = { "lvl" };
		Args = { A("Value", "number", { Label = "Level"; Min = 1; Max = 1000; Required = true }) } };
	SetStatPoints = { Side = T; Section = "Progress"; Title = "Stat points"; Help = "Unspent stat points"; Icon = "Exp"; Level = 2; Target = "required"; Danger = false; Synonyms = { "points" };
		Args = { A("Value", "number", { Label = "Points"; Min = 0; Max = 999; Required = true }) } };
	GrantTitle = { Side = T; Section = "Progress"; Title = "Grant title"; Help = "Give them a title"; Icon = "Exp"; Level = 2; Target = "required"; Danger = false; Synonyms = { "title" };
		Args = { A("Title", "text", { Max = 40; Required = true }) } };
	RemoveTitle = { Side = T; Section = "Progress"; Title = "Remove title"; Help = "Take a title away"; Icon = "Exp"; Level = 2; Target = "required"; Danger = false; Synonyms = { "untitle" };
		Args = { A("Title", "text", { Max = 40; Required = true }) } };
	RegionsAll = { Side = T; Section = "Progress"; Title = "All places found"; Help = "Mark every place found"; Icon = "Clues"; Level = 2; Target = "required"; Danger = false; Synonyms = { "regions", "places" }; Args = {} };
	RegionsReset = { Side = T; Section = "Progress"; Title = "Reset places"; Help = "Forget every place found"; Icon = "Clues"; Level = 2; Target = "required"; Danger = true; Synonyms = { "regions reset" }; Args = {} };
	SetClub = { Side = T; Section = "Progress"; Title = "Club"; Help = "Put them in a club, or None to take them out"; Icon = "SecProgress"; Level = 2; Target = "required"; Danger = false; Synonyms = { "sports", "leave club" };
		Args = { A("Club", "choice", { From = "Clubs"; Required = true }) } };
	MatchStart = { Side = T; Section = "Progress"; Title = "Start a match"; Help = "Force a match at a venue with them"; Icon = "SecProgress"; Level = 2; Target = "required"; Danger = false; Synonyms = { "match" };
		Args = { A("Venue", "choice", { From = "Venues"; Required = true }) } };
	MatchEnd = { Side = T; Section = "Progress"; Title = "End a match"; Help = "End the match at a venue"; Icon = "SecProgress"; Level = 2; Target = "none"; Danger = false; Synonyms = { "stop match" };
		Args = { A("Venue", "choice", { From = "Venues"; Required = true }) } };

	-- Test / School
	SetTime = { Side = T; Section = "School"; Title = "Set time"; Help = "The school clock, HH:MM"; Icon = "Time"; Level = 2; Target = "none"; Danger = false; Synonyms = { "clock", "time" };
		Args = { A("Time", "text", { Max = 5; Required = true }) } };
	ClockSpeed = { Side = T; Section = "School"; Title = "Clock speed"; Help = "Real seconds per school hour"; Icon = "Time"; Level = 2; Target = "none"; Danger = false; Synonyms = { "time speed" };
		Args = { A("Value", "number", { Label = "Seconds"; Min = 2; Max = 600; Required = true }) } };
	SkipToPeriod = { Side = T; Section = "School"; Title = "Skip to a period"; Help = "Jump the clock to a period's start"; Icon = "Time"; Level = 2; Target = "none"; Danger = false; Synonyms = { "period" };
		Args = { A("Segment", "choice", { Label = "Period"; From = "Segments"; Required = true }) } };
	RingBell = { Side = T; Section = "School"; Title = "Ring the bell"; Help = "The school bell, now"; Icon = "SecSchool"; Level = 2; Target = "none"; Danger = false; Synonyms = { "bell" }; Args = {} };
	StartLesson = { Side = T; Section = "School"; Title = "Start a lesson"; Help = "Start a lesson for them in a classroom"; Icon = "SecSchool"; Level = 2; Target = "required"; Danger = false; Synonyms = { "class" };
		Args = { A("Room", "choice", { From = "Rooms"; Required = true }) } };
	SetDisciplinePoints = { Side = T; Section = "School"; Title = "Discipline points"; Help = "Set their discipline points"; Icon = "Discipline"; Level = 2; Target = "required"; Danger = false; Synonyms = { "discipline" };
		Args = { A("Value", "number", { Label = "Points"; Min = 0; Max = 100; Required = true }) } };
	ClearDiscipline = { Side = T; Section = "School"; Title = "Clear discipline"; Help = "Wipe their discipline record"; Icon = "Discipline"; Level = 2; Target = "required"; Danger = false; Synonyms = { "clean record" }; Args = {} };
	LiftSuspension = { Side = T; Section = "School"; Title = "Lift suspension"; Help = "End their suspension"; Icon = "Discipline"; Level = 2; Target = "required"; Danger = false; Synonyms = { "unsuspend" }; Args = {} };
	ExcuseToday = { Side = T; Section = "School"; Title = "Excuse today"; Help = "Clear today's absences"; Icon = "Discipline"; Level = 2; Target = "required"; Danger = false; Synonyms = { "absent" }; Args = {} };
	OweDetention = { Side = T; Section = "School"; Title = "Owe detention"; Help = "Add a detention they owe"; Icon = "Jail"; Level = 2; Target = "required"; Danger = false; Synonyms = { "detention owed" }; Args = {} };
	ClearDetention = { Side = T; Section = "School"; Title = "Clear detention"; Help = "Clear the detentions they owe"; Icon = "Jail"; Level = 2; Target = "required"; Danger = false; Synonyms = { "detention clear" }; Args = {} };

	-- Test / Story
	QuestStart = { Side = T; Section = "Story"; Title = "Start a quest"; Help = "Start a quest by id (rites: owner)"; Icon = "SecStory"; Level = 2; Target = "required"; Danger = false; Synonyms = { "quest" };
		Args = { A("Id", "choice", { Label = "Quest"; From = "Quests"; Required = true }) } };
	QuestAbandon = { Side = T; Section = "Story"; Title = "Drop a quest"; Help = "Drop one of their quests"; Icon = "SecStory"; Level = 2; Target = "required"; Danger = false; Synonyms = { "abandon" };
		Args = { A("Id", "choice", { Label = "Quest"; From = "Quests"; Required = true }) } };
	QuestReset = { Side = T; Section = "Story"; Title = "Reset quests"; Help = "Clear every quest they have"; Icon = "SecStory"; Level = 2; Target = "required"; Danger = true; Synonyms = { "quests reset" }; Args = {} };

	-- Test / World
	FullMoon = { Side = T; Section = "World"; Title = "Full moon tonight"; Help = "Make tonight a full moon"; Icon = "Moon"; Level = 2; Target = "none"; Danger = false; Synonyms = { "moon" }; Args = {} };
	GotoRegion = { Side = T; Section = "World"; Title = "Go to a place"; Help = "You, or the selected student, to any place"; Icon = "GoTo"; Level = 2; Target = "optional"; Danger = false; Synonyms = { "region", "place" };
		Args = { A("Id", "choice", { Label = "Place"; From = "Regions"; Required = true }), A("Send", "toggle", { Label = "Send them" }) } };

	-- Test / Spawns
	SpawnDelinquents = { Side = T; Section = "Spawns"; Title = "Delinquent crew"; Help = "A crew in front of you"; Icon = "Beast"; Level = 2; Target = "none"; Danger = false; Synonyms = { "gang" }; Args = {} };
	SpawnDelinquent = { Side = T; Section = "Spawns"; Title = "One delinquent"; Help = "One by role"; Icon = "Beast"; Level = 2; Target = "none"; Danger = false; Synonyms = { "grunt", "brute" };
		Args = { A("Role", "choice", { Choices = { "Grunt", "Brute", "Leader" } }) } };
	SpawnWolves = { Side = T; Section = "Spawns"; Title = "Wolf pack"; Help = "A wild pack near you"; Icon = "Wolf"; Level = 2; Target = "none"; Danger = false; Synonyms = { "wolves" }; Args = {} };
	SpawnBeast = { Side = T; Section = "Spawns"; Title = "Beast"; Help = "Any beast"; Icon = "Beast"; Level = 2; Target = "none"; Danger = false; Synonyms = { "monster" };
		Args = { A("Beast", "choice", { From = "Beasts"; Required = true }) } };
	SpawnSparring = { Side = T; Section = "Spawns"; Title = "Sparring partner"; Help = "A partner, Easy to Nightmare"; Icon = "Wolf"; Level = 2; Target = "none"; Danger = false; Synonyms = { "spar", "dummy" };
		Args = { A("Tier", "choice", { Label = "Difficulty"; Choices = { "Easy", "Normal", "Hard", "Nightmare" } }) } };
	ClearEnemies = { Side = T; Section = "Spawns"; Title = "Clear enemies"; Help = "Remove every spawned enemy"; Icon = "SecSpawns"; Level = 2; Target = "none"; Danger = true; Synonyms = { "clear", "despawn" }; Args = {} };

	-- Test / Self
	Invisible = { Side = T; Section = "Self"; Title = "Invisible"; Help = "Vanish (again to appear)"; Icon = "Invisible"; Level = 2; Target = "none"; Danger = false; Synonyms = { "vanish", "hide" }; Args = {} };
	TeleportTo = { Side = T; Section = "Self"; Title = "Teleport to a point"; Help = "Ctrl+click in the world"; Icon = "Teleport"; Level = 2; Target = "none"; Danger = false; Synonyms = { "click tp" };
		Args = { A("Position", "position", { Required = true }) } };
}
