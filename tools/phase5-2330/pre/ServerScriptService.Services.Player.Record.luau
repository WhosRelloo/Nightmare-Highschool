--[[ (2.32) The Permanent Record (server). Services.Player.Record (docs/expansion/14-Progression-and-Identity.md §4).
	Notable Entries: a short log written in the school's voice, newest first, 40 kept (PlayerData.Progress.Record), each
	written once (its key is remembered in Progress.RecordSeen). Written by: path tiers, Honours, main-quest completions,
	the Ring championship, a return from suspension. Tiers earned before 2.32 are written in on join.
	The file: FileFor(P) builds every tab the M menu shows (except Student, which is Progression.Sheet), every number
	read from its source. Remote: ReplicatedStorage.NHProgress.File (RF) -> FileFor(P).
	API: Add(P, Key, Text) -> boolean, FileFor(P), SelfTestForTests(P) ]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local PathsCfg = require(ReplicatedStorage.Config.Paths)
local HonCfg = require(ReplicatedStorage.Config.Honours)

local Shared = {}
local Local = {}

local function svc(Path: string)
	local Node = ServerScriptService.Services
	for Seg in Path:gmatch(`[^%.]+`) do Node = Node and Node:FindFirstChild(Seg) end
	if not Node then return nil end
	local Ok, M = pcall(require, Node)
	return if Ok then M else nil
end

-- the school's voice for a path tier
local PATH_LINE = {
	Academic = "Entered on the honour roll as {Tier}.";
	Social = "Noted by the office: {Tier} among the student body.";
	Combat = "Flagged by the hall monitors as {Tier}.";
	Athletic = "Promoted to {Tier} by the coaching staff.";
	Supernatural = "Annotated in red ink: {Tier}.";
}

function Local.When(): (number, string)
	local Day, When = 0, ``
	pcall(function()
		local Clock = svc(`School.SchoolClock`)
		Day = Clock.GetState().Day or 0
		local C = Clock.Calendar()
		When = `Term {C.Term}, Week {C.Week}`
	end)
	return Day, When
end

function Shared.Add(P: Player, Key: string, Text: string): boolean
	local Prog = svc(`Player.Progression`)
	local Pr = Prog and Prog.Get(P)
	if not Pr or Pr.RecordSeen[Key] then return false end
	local Day, When = Local.When()
	Pr.RecordSeen[Key] = true
	table.insert(Pr.Record, 1, { Day = Day; When = When; Key = Key; Text = Text })
	while #Pr.Record > 40 do table.remove(Pr.Record) end
	svc(`Player.Data`).UpdateState(P, { type = `SetProgress`; progress = Pr })
	return true
end

function Local.TierLine(Path: string, T: number): string
	local Tier = PathsCfg.Paths[Path].Tiers[T]
	return ((PATH_LINE[Path] or "Recognised as {Tier}."):gsub("{Tier}", Tier.Name))
end

-- tiers earned before the Record existed, written in once
function Local.Backfill(P: Player)
	local Prog = svc(`Player.Progression`)
	local Pr = Prog and Prog.Get(P)
	if not Pr then return end
	for _, Path in PathsCfg.Order do
		for T = 2, Pr.Paths[Path] or 1 do Shared.Add(P, `Path:{Path}:{T}`, Local.TierLine(Path, T)) end
	end
end

---| the file (every tab but Student) |---

local function row(L: string, V: any, Tone: string?, Extra)
	local R = { L = L; V = tostring(V); Tone = Tone }
	for K, X in Extra or {} do R[K] = X end
	return R
end

function Shared.FileFor(P: Player)
	local Data = svc(`Player.Data`)
	local Prof = Data and Data.GetProfile(P)
	local Prog = svc(`Player.Progression`)
	local Pr = Prog and Prog.Get(P)
	if not (Prof and Pr) then return nil end
	local File = {}

	-- Academics
	local Subjects = {}
	local Activities = require(ReplicatedStorage.Config.Activities)
	for Name in Activities.Subjects do
		local C = (Prof.Classes or {})[Name]
		local Level = (typeof(C) == `table` and tonumber(C.Level)) or 1
		local Passes = (typeof(C) == `table` and tonumber(C.Passes)) or 0
		local Best = (typeof(C) == `table` and C.BestGrade ~= `` and C.BestGrade) or `\u{2014}`
		table.insert(Subjects, row(Name, `Level {Level}`, nil, { Pips = { Level, Activities.MaxLevel }; Hint = `{Passes} lesson{Passes == 1 and `` or `s`} passed \u{00B7} best grade {Best}` }))
	end
	table.sort(Subjects, function(A, B) return A.L < B.L end)
	local Cards = {}
	pcall(function()
		local St = svc(`School.ReportCards`).State(P)
		for I, Card in (St and St.Cards) or {} do
			if I > 3 then break end
			table.insert(Cards, row(`Week {Card.Week or `?`}`, Card.Average or `No grades`, if Card.Average and (Card.Average == `A+` or Card.Average == `A` or Card.Average == `B`) then `good` elseif Card.Average == `D` or Card.Average == `F` then `bad` else nil,
				{ Hint = `{(Card.Attendance or {}).Attended or 0} of {(Card.Attendance or {}).Total or 0} classes \u{00B7} {Card.Conduct or `Clear`}` }))
		end
	end)
	if #Cards == 0 then Cards = { row(`No report cards yet`, ``, `dim`, { Hint = `One arrives at the end of each school week.` }) } end
	File.Academics = { Title = `Academics`; Blurb = `Your subjects and your report cards. Pass lessons to level a subject up.`;
		Sections = { { H = `Subjects`; Icon = `Academics`; Rows = Subjects }, { H = `Report cards`; Icon = `Entries`; Rows = Cards } } }

	-- Attendance & Conduct
	local A = Prof.Attendance or {}
	local T = A.Totals or {}
	local D = {}
	pcall(function() D = svc(`School.Discipline`).GetData(P) or {} end)
	local Lv = D.Level or `Clear`
	local LEVELS = { Clear = 0; Warning = 1; Detention = 2; Probation = 3; Suspension = 4 }
	File.Attendance = { Title = `Attendance & Conduct`; Blurb = `Every class you were marked for, and your standing with the school.`;
		Sections = {
			{ H = `Attendance`; Icon = `Attendance`; Rows = {
				row(`Present`, T.Present or 0, `good`), row(`Late`, T.Tardy or 0, if (T.Tardy or 0) > 0 then `bad` else nil),
				row(`Absent`, T.Absent or 0, if (T.Absent or 0) > 0 then `bad` else nil),
				row(`Streak`, `{A.Streak or 0} days`, nil, { Hint = `Your best: {A.BestStreak or 0} days in a row.` }) } };
			{ H = `Conduct`; Icon = `Secret`; Rows = {
				row(`Standing`, Lv, if Lv == `Clear` then `good` else `bad`, { Pips = { LEVELS[Lv] or 0, 4; Bad = true } }),
				row(`Discipline points`, D.Points or 0, if (D.Points or 0) > 0 then `bad` else nil, { Hint = `Points fade with good behaviour.` }),
				row(`Detentions owed`, D.DetentionsOwed or 0, if (D.DetentionsOwed or 0) > 0 then `bad` else nil),
				row(`Detentions served`, D.DetentionsServed or 0) } };
		} }

	-- Athletics
	local Sheet = nil
	pcall(function() Sheet = svc(`Sports.Clubs`).Sheet(P) end)
	local ARows = {}
	if Sheet and Sheet.Club then
		local ClubName = Sheet.Club
		pcall(function() ClubName = require(ReplicatedStorage.Config.Sports).Clubs[Sheet.Club].Name end)
		table.insert(ARows, row(`Club`, ClubName))
		table.insert(ARows, row(`Rank`, Sheet.Rank or `Rookie`, nil, { Pips = { Sheet.RankIndex or 1, 4 };
			Hint = if Sheet.Next then `{Sheet.Next.Name} at {Sheet.Next.Min} club EXP (you have {Sheet.ClubExp or 0}).` else `The top rank.` }))
		for K, V in Sheet.Record or {} do if typeof(V) == `number` then table.insert(ARows, row(K, V)) end end
	else
		table.insert(ARows, row(`No club yet`, ``, `dim`, { Hint = `Join the Soccer, Basketball or Football club at the sports fields.` }))
	end
	local Drills = {}
	for K, V in (Sheet and Sheet.Drills) or {} do if typeof(V) == `number` then table.insert(Drills, row(K, V)) end end
	File.Athletics = { Title = `Athletics`; Blurb = `Your club, your rank in it, and your record on the field.`;
		Sections = { { H = `Club`; Icon = `Athletics`; Rows = ARows }, if #Drills > 0 then { H = `Drill bests`; Icon = `Paths`; Rows = Drills } else nil } }

	-- Combat
	local Tally = Pr.Tally
	local Shows = 0
	pcall(function() Shows = svc(`Social.CliqueShowdowns`).Summary(P).Beaten or 0 end)
	File.Combat = { Title = `Combat`; Blurb = `Every fight the school knows about. Counts from duels on began in 2.31.`;
		Sections = {
			{ H = `Takedowns`; Icon = `Combat`; Rows = { row(`Students downed`, Prof.Kills or 0), row(`Others downed`, Prof.NPCKills or 0) } };
			{ H = `Contests`; Icon = `Might`; Rows = {
				row(`Duels won`, Tally.DuelWins or 0), row(`Ring champion beaten`, if (Tally.Champion or 0) > 0 then `Yes` else `Not yet`, if (Tally.Champion or 0) > 0 then `good` else `dim`),
				row(`Clique leaders beaten`, `{Shows} of {#require(ReplicatedStorage.Config.Cliques).Order}`), row(`Beasts brought down`, Tally.Beasts or 0),
				row(`Hall monitors escaped`, Tally.Escapes or 0) } };
		} }

	-- Factions & Cliques
	local FRows, CRows = {}, {}
	pcall(function()
		local Fa = svc(`Social.Factions`)
		for Id, Def in require(ReplicatedStorage.Config.Factions).Factions do
			local E = Fa.Get(P, Id)
			local Rank = (E and E.Rank) or `Outsider`
			table.insert(FRows, row(Def.Name or Id, Rank, if E and E.Member then `good` else nil, { Pips = { Fa.RankIndex(Rank), 5 }; Hint = if E and E.Member then `A member.` else `Not a member.` }))
		end
	end)
	table.sort(FRows, function(A, B) return A.L < B.L end)
	pcall(function()
		local Cl = svc(`Social.Cliques`)
		local Defs = require(ReplicatedStorage.Config.Cliques)
		local V = Cl.Get(P) or {}
		for _, Id in Defs.Order do
			local Tier = Cl.Tier(tonumber(V[Id]) or 0)
			table.insert(CRows, row(Defs.Defs[Id].Name, Tier, if Tier == `Respected` or Tier == `Friendly` then `good` elseif Tier == `Hostile` or Tier == `Wary` then `bad` else nil))
		end
	end)
	local Met = 0
	pcall(function()
		local Roster = svc(`Social.Roster`)
		for Id, R in svc(`Social.Reputation`).Get(P).Relationships do if typeof(R) == `table` and R.Met == true and Roster.IsRostered(Id) then Met += 1 end end
	end)
	local RepRows = {}
	for Cat in require(ReplicatedStorage.Config.Reputation).Categories do
		local V = 0
		pcall(function() V = svc(`Social.Reputation`).Value(P, Cat) end)
		table.insert(RepRows, row(Cat, `{V} / 100`))
	end
	table.sort(RepRows, function(A, B) return A.L < B.L end)
	table.insert(RepRows, row(`Classmates met`, `{Met} of 24`))
	File.Factions = { Title = `Factions & Cliques`; Blurb = `Where you stand with the school's groups, and with the school itself.`;
		Sections = { { H = `Factions`; Icon = `Factions`; Rows = FRows }, { H = `Cliques`; Icon = `Social`; Rows = CRows }, { H = `Reputation`; Icon = `Student`; Rows = RepRows } } }

	-- Paths & Titles
	local Paths = svc(`Player.Paths`)
	local F = Paths and Paths.Facts(P)
	local Cards2 = {}
	for _, Path in PathsCfg.Order do
		local Tiers = PathsCfg.Paths[Path].Tiers
		local Tn = Pr.Paths[Path] or 1
		local NextTier = Tiers[Tn + 1]
		local Missing = {}
		if NextTier and F then
			for _, N in NextTier.Need do
				local Ok, Yes = pcall(N.Test, F)
				if not (Ok and Yes) then table.insert(Missing, N.Text) end
			end
		end
		table.insert(Cards2, { Path = Path; Tier = Tn; Of = #Tiers; Name = Tiers[Tn].Name; Next = NextTier and NextTier.Name; Missing = Missing })
	end
	local Social = svc(`Social.Reputation`).Get(P)
	File.Paths = { Title = `Paths & Titles`; Blurb = `Who you're becoming. A tier, once earned, is never taken away.`;
		Cards = Cards2; Titles = table.clone(Social.Titles or {}); Equipped = Social.Title or `` }

	-- Honours
	local Groups = {}
	local Earned = 0
	for _, G in HonCfg.Groups do
		local Items = {}
		for _, H in HonCfg.List do
			if H.Group == G.Id then
				local Day = Pr.Honours[H.Id]
				if Day then Earned += 1 end
				local Secret = H.Hidden and not Day
				table.insert(Items, { Id = H.Id; Name = if Secret then `Sealed` else H.Name; Text = if Secret then `A secret. Find it to open it.` else H.Text;
					Earned = Day ~= nil; Secret = Secret })
			end
		end
		table.insert(Groups, { Id = G.Id; Name = G.Name; Icon = G.Icon; Items = Items })
	end
	File.Honours = { Title = `Honours`; Blurb = `What the school has recognised you for: {Earned} of {#HonCfg.List} earned.`; Groups = Groups; Earned = Earned; Of = #HonCfg.List }

	-- Notable Entries
	local List = {}
	for _, E in Pr.Record do table.insert(List, { When = E.When; Text = E.Text }) end
	File.Entries = { Title = `Notable Entries`; Blurb = `What the school has written about you, newest first.`; List = List }
	return File
end

---| start |---

function Shared.OnStart()
	task.defer(function()
		local Folder = ReplicatedStorage:WaitForChild(`NHProgress`, 30)
		if Folder and not Folder:FindFirstChild(`File`) then
			local RF = Instance.new(`RemoteFunction`)
			RF.Name = `File`
			RF.Parent = Folder
			local Last = {} :: { [Player]: number }
			RF.OnServerInvoke = function(P)
				local Now = os.clock()
				if Last[P] and Now - Last[P] < 0.4 then return nil end
				Last[P] = Now
				local Ok, F = pcall(Shared.FileFor, P)
				return if Ok then F else nil
			end
			Players.PlayerRemoving:Connect(function(P) Last[P] = nil end)
		end
	end)
	local Data = svc(`Player.Data`)
	if Data and Data.ProfileLoaded then
		Data.ProfileLoaded:Connect(function(P) task.delay(8, function() if P.Parent then pcall(Local.Backfill, P) end end) end)
	end
	task.defer(function()
		local Paths = svc(`Player.Paths`)
		if Paths then
			Paths.Granted:Connect(function(P, Path, T) pcall(Shared.Add, P, `Path:{Path}:{T}`, Local.TierLine(Path, T)) end)
		end
		local Q = svc(`Quests.Quests`)
		if Q and Q.Completed then
			Q.Completed:Connect(function(P, Id)
				local Def = require(ReplicatedStorage.Config.Quests).Quests[Id]
				if not (Def and (Def.Chapter or Def.Category == `Main`)) then return end
				if Id == `AfterHours` and Q.Decided(P, `FileKept`) ~= `Lose` then
					pcall(Shared.Add, P, `Quest:{Id}`, `Student displayed unusual composure in Room 102 after dark. The file was recovered.`)
				else
					pcall(Shared.Add, P, `Quest:{Id}`, `Completed: {Def.Name}.`)
				end
			end)
		end
		local Duels = svc(`Quests.Duels`)
		if Duels and Duels.ChampionDefeated then
			Duels.ChampionDefeated:Connect(function(P) pcall(Shared.Add, P, `Champion`, `Took the Ring Championship.`) end)
		end
		local Disc = svc(`School.Discipline`)
		if Disc and Disc.LevelChanged then
			Disc.LevelChanged:Connect(function(P, New, Old)
				if Old == `Suspension` and New ~= `Suspension` then
					local Day = Local.When()
					pcall(Shared.Add, P, `Suspension:{Day}`, `Returned from suspension. The office expects better.`)
				end
			end)
		end
	end)
end

---| tests |---

function Shared.SelfTestForTests(P: Player)
	local Prog = svc(`Player.Progression`)
	local Pr = Prog.Get(P)
	local RecBefore, SeenBefore = table.clone(Pr.Record), table.clone(Pr.RecordSeen)
	local R = {}
	R.First = Shared.Add(P, `Test:One`, `A test entry.`)
	R.Again = Shared.Add(P, `Test:One`, `A test entry.`)
	for I = 1, 45 do Shared.Add(P, `Test:N{I}`, `Entry {I}.`) end
	local After = Prog.Get(P).Record
	R.Kept, R.Newest = #After, After[1] and After[1].Text
	R.HasWhen = After[1] ~= nil and After[1].When ~= ``
	local Pr2 = Prog.Get(P)
	Pr2.Record, Pr2.RecordSeen = RecBefore, SeenBefore
	svc(`Player.Data`).UpdateState(P, { type = `SetProgress`; progress = Pr2 })
	-- the file: every number against its source
	local F = Shared.FileFor(P)
	local Prof = svc(`Player.Data`).GetProfile(P)
	local Checks, Bad = 0, {}
	local function eq(Name, A, B) Checks += 1 if tostring(A) ~= tostring(B) then table.insert(Bad, `{Name}: {A} vs {B}`) end end
	local Tot = (Prof.Attendance or {}).Totals or {}
	eq(`Present`, F.Attendance.Sections[1].Rows[1].V, Tot.Present or 0)
	eq(`Absent`, F.Attendance.Sections[1].Rows[3].V, Tot.Absent or 0)
	eq(`Points`, F.Attendance.Sections[2].Rows[2].V, svc(`School.Discipline`).GetData(P).Points or 0)
	eq(`Kills`, F.Combat.Sections[1].Rows[1].V, Prof.Kills or 0)
	eq(`NPCKills`, F.Combat.Sections[1].Rows[2].V, Prof.NPCKills or 0)
	eq(`DuelWins`, F.Combat.Sections[2].Rows[1].V, Prog.Get(P).Tally.DuelWins or 0)
	for _, Rw in F.Academics.Sections[1].Rows do
		local C = (Prof.Classes or {})[Rw.L]
		eq(`Level {Rw.L}`, Rw.Pips[1], (typeof(C) == `table` and tonumber(C.Level)) or 1)
	end
	for _, Rw in F.Factions.Sections[3].Rows do
		if Rw.L ~= `Classmates met` then eq(`Rep {Rw.L}`, Rw.V, `{svc(`Social.Reputation`).Value(P, Rw.L)} / 100`) end
	end
	local Earned = 0
	for _ in Prog.Get(P).Honours do Earned += 1 end
	eq(`Honours earned`, F.Honours.Earned, Earned)
	for _, C in F.Paths.Cards do eq(`Path {C.Path}`, C.Tier, Prog.Get(P).Paths[C.Path] or 1) end
	R.FileChecks, R.FileBad = Checks, Bad
	R.Tabs = 0
	for _ in F do R.Tabs += 1 end
	return R
end

return Shared
