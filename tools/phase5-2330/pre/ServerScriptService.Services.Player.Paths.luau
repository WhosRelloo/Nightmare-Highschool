--[[ (2.31) Standing Paths (server). Services.Player.Paths (docs/expansion/14-Progression-and-Identity.md §3).
	Tiers are computed from data the game already keeps (Config.Paths); only the highest tier reached is saved
	(PlayerData.Progress.Paths, kept by Progression.Sanitize), so a tier never drops. Five counters the old signals
	didn't keep live in Progress.Tally.
	Checks: on join, a 60 s sweep, and a few signals (Check, debounced 2 s per player).
	Player attributes: Path_<Path> = tier, PathTop = the path at tier 3+ with the highest tier (Config order breaks ties).
	API: Evaluate(F), Facts(P), Tier(P, Path), Next(P), Check(P), CheckNow(P), Count(P, Key, N?), Granted (signal),
	     SelfTestForTests(P), FactsOverride (tests) ]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local Config = require(ReplicatedStorage.Config.Paths)
local SignalPlus = require(ReplicatedStorage.Packages.SignalPlus)

local Shared = {}
local Local = {}
Shared.Granted = SignalPlus() -- (Player, Path, Tier, Name)
Shared.FactsOverride = {} :: { [Player]: any }
local Pending = {} :: { [Player]: boolean }
local GRADE = { [`A+`] = 6; A = 5; B = 4; C = 3; D = 2; F = 1 }

local function svc(Path: string)
	local Node = ServerScriptService.Services
	for Seg in Path:gmatch(`[^%.]+`) do Node = Node and Node:FindFirstChild(Seg) end
	if not Node then return nil end
	local Ok, M = pcall(require, Node)
	return if Ok then M else nil
end

---| the facts |---

function Shared.Facts(P: Player)
	if Shared.FactsOverride[P] then return Shared.FactsOverride[P] end
	local Data = svc(`Player.Data`)
	local Prof = Data and Data.GetProfile(P)
	local Prog = svc(`Player.Progression`)
	local Pr = Prog and Prog.Get(P)
	if not (Prof and Pr) then return nil end
	local F = { Subjects = {}; Rep = {}; CliqueTiers = {}; Tally = {} }
	for _, K in Config.Tally do F.Tally[K] = Pr.Tally[K] or 0 end
	F.Passed, F.APlus = 0, false -- (2.32) for Honours: subjects with a pass, an A+ ever
	for Subject, C in Prof.Classes or {} do
		if typeof(C) == `table` then
			F.Subjects[Subject] = tonumber(C.Level) or 1
			if (tonumber(C.Passes) or 0) >= 1 then F.Passed += 1 end
			if C.BestGrade == `A+` then F.APlus = true end
		end
	end
	F.BestStreak = (typeof(Prof.Attendance) == `table` and tonumber(Prof.Attendance.BestStreak)) or 0
	F.Streak = (typeof(Prof.Attendance) == `table` and tonumber(Prof.Attendance.Streak)) or 0
	-- (2.32) conduct: detentions served, and days since the last violation on the record
	F.DetentionsServed, F.DaysClean, F.Today = 0, 10 ^ 6, 0
	pcall(function() F.Today = svc(`School.SchoolClock`).GetState().Day or 0 end)
	pcall(function()
		local D = svc(`School.Discipline`).GetData(P)
		F.DetentionsServed = tonumber(D.DetentionsServed) or 0
		for _, R in D.Recent or {} do
			if typeof(R) == `table` and typeof(R.Day) == `number` then F.DaysClean = math.min(F.DaysClean, F.Today - R.Day) end
		end
	end)
	F.BestCard = 0
	pcall(function()
		local St = svc(`School.ReportCards`).State(P)
		for _, Card in (St and St.Cards) or {} do F.BestCard = math.max(F.BestCard, GRADE[Card.Average or ``] or 0) end
	end)
	local Rep = svc(`Social.Reputation`)
	for Cat in require(ReplicatedStorage.Config.Reputation).Categories do
		F.Rep[Cat] = (Rep and Rep.Value(P, Cat)) or 0
	end
	F.Met, F.Trusted = 0, 0
	pcall(function()
		local Roster = svc(`Social.Roster`)
		for Id, R in Rep.Get(P).Relationships do
			if typeof(R) == `table` and R.Met == true and Roster.IsRostered(Id) then
				F.Met += 1
				if (tonumber(R.Value) or 0) >= 50 then F.Trusted += 1 end -- (2.32) Trusted (Config.Reputation: 50 and up)
			end
		end
	end)
	pcall(function()
		local Cl = svc(`Social.Cliques`)
		for Id, V in Cl.Get(P) or {} do
			if typeof(V) == `number` then F.CliqueTiers[Id] = Cl.Tier(V) end
		end
	end)
	F.FactionRank = 1
	pcall(function()
		local Fa = svc(`Social.Factions`)
		for Id in require(ReplicatedStorage.Config.Factions).Factions do
			local E = Fa.Get(P, Id)
			if E then F.FactionRank = math.max(F.FactionRank, Fa.RankIndex(E.Rank)) end
		end
	end)
	F.Takedowns = (tonumber(Prof.Kills) or 0) + (tonumber(Prof.NPCKills) or 0)
	F.Showdowns = 0
	pcall(function() F.Showdowns = svc(`Social.CliqueShowdowns`).Summary(P).Beaten or 0 end)
	F.ClubRank, F.InClub = `Rookie`, false
	pcall(function()
		local S = svc(`Sports.Clubs`).Get(P)
		if S and S.Club then F.InClub = true F.ClubRank = require(ReplicatedStorage.Config.Sports).RankFor(S.ClubExp) end
	end)
	local Q = svc(`Quests.Quests`)
	F.Orientation = Q ~= nil and Q.IsDone(P, `Orientation`)
	F.AfterHours = Q ~= nil and Q.IsDone(P, `AfterHours`)
	F.FileKept = F.AfterHours and Q.Decided(P, `FileKept`) ~= `Lose`
	F.LineageTier = 1
	F.Tuned = false -- (2.32) Night FM's introduction heard (Features.Phone)
	pcall(function() F.Tuned = svc(`Features.Phone`).Tuned(P) == true end)
	F.StrikeGrade = nil -- (2.32) the Strikethrough's best grade (Quests.CineGrades)
	pcall(function() local G = Q.CineGrades(P) F.StrikeGrade = G and G.Strikethrough and G.Strikethrough.Best end)
	pcall(function() F.LineageTier = require(ReplicatedStorage.Lineage).Sanitize(Prof.Lineage).Tier or 1 end)
	return F
end

---| the evaluator (pure) |---

function Local.Passes(Tier, F): (boolean, { string })
	local Missing = {}
	for _, N in Tier.Need do
		local Ok, R = pcall(N.Test, F)
		if not (Ok and R) then table.insert(Missing, N.Text) end
	end
	return #Missing == 0, Missing
end

-- the highest tier of each path whose conditions hold for these facts
function Shared.Evaluate(F): { [string]: number }
	local Out = {}
	for _, Path in Config.Order do
		local Best = 1
		for I, Tier in Config.Paths[Path].Tiers do
			if I > 1 and (Local.Passes(Tier, F)) then Best = I end
		end
		Out[Path] = Best
	end
	return Out
end

---| saving |---

function Local.Saved(P: Player): ({ [string]: number }?, any?)
	local Prog = svc(`Player.Progression`)
	local Pr = Prog and Prog.Get(P)
	if not Pr then return nil, nil end
	return Pr.Paths, Pr
end
function Local.Save(P: Player, Pr)
	svc(`Player.Data`).UpdateState(P, { type = `SetProgress`; progress = Pr })
end

function Shared.Tier(P: Player, Path: string): (number, string)
	local Saved = Local.Saved(P)
	local T = (Saved and Saved[Path]) or 1
	local Def = Config.Paths[Path]
	return T, Def and Def.Tiers[T] and Def.Tiers[T].Name or ``
end

-- the closest next tier: the one with the fewest missing conditions
function Shared.Next(P: Player)
	local F = Shared.Facts(P)
	if not F then return nil end
	local Best = nil
	for _, Path in Config.Order do
		local T = Shared.Tier(P, Path)
		local Tier = Config.Paths[Path].Tiers[T + 1]
		if Tier then
			local _, Missing = Local.Passes(Tier, F)
			if not Best or #Missing < #Best.Missing then Best = { Path = Path; Tier = T + 1; Name = Tier.Name; Missing = Missing } end
		end
	end
	return Best
end

function Local.Mirror(P: Player, Saved)
	local Top, TopTier = nil, 2
	for _, Path in Config.Order do
		local T = Saved[Path] or 1
		P:SetAttribute(`Path_{Path}`, if T > 1 then T else nil)
		if T > TopTier then Top, TopTier = Path, T end
	end
	P:SetAttribute(`PathTop`, Top)
end

-- grants every tier between the saved one and what the facts hold now; never lowers one
function Shared.CheckNow(P: Player): { { Path: string, Tier: number } }
	local Made = {}
	local F = Shared.Facts(P)
	local Saved, Pr = Local.Saved(P)
	if not (F and Saved and Pr) then return Made end
	local Now = Shared.Evaluate(F)
	for _, Path in Config.Order do
		local Old = Saved[Path] or 1
		for T = Old + 1, Now[Path] do
			Saved[Path] = T
			table.insert(Made, { Path = Path; Tier = T })
		end
	end
	if #Made > 0 then
		Pr.Paths = Saved
		Local.Save(P, Pr)
		for I, G in Made do
			local Tier = Config.Paths[G.Path].Tiers[G.Tier]
			local Last = I == #Made or Made[I + 1].Path ~= G.Path -- the newest tier of this path in this check
			Local.Reward(P, G.Path, G.Tier, Tier, Last)
			Shared.Granted:Fire(P, G.Path, G.Tier, Tier.Name)
		end
	end
	Local.Mirror(P, Saved)
	if not Shared.FactsOverride[P] then -- (2.32) the same facts earn Honours (never test facts)
		pcall(function() svc(`Player.Honours`).CheckFacts(P, F) end)
	end
	return Made
end

-- what a tier gives: its title, a Moments banner (the newest tier of each path only), and from tier 4 a mention on
-- the PA by day or the Midnight Broadcast by night (Services.World.Broadcast; the PA speaks at most once a segment)
function Local.Reward(P: Player, Path: string, T: number, Tier, Last: boolean)
	local Rep = svc(`Social.Reputation`)
	if Tier.Title and Rep then pcall(Rep.AwardTitle, P, Tier.Title) end
	if not Last then return end
	local Fx = svc(`Features.Fx`)
	if Fx then pcall(Fx.Fire, P, `PathTier`, { Path = Path; Tier = T; Name = Tier.Name; Of = #Config.Paths[Path].Tiers }) end
	if T >= 4 then
		local First = P.DisplayName
		pcall(function() local Id = svc(`Player.Identity`) First = Id.Get(P).First or First end)
		local Article = if Tier.Name:match(`^[AEIOU]`) then `an` else `a`
		local Text = Config.Mention:gsub("{Name}", First):gsub("{Article}", Article):gsub("{Tier}", Tier.Name)
		local Bc = svc(`World.Broadcast`)
		if Bc then
			local OnAir = false
			pcall(function() OnAir = Bc.Station(P).OnAir end)
			if OnAir or not Bc.PA(Text) then Bc.Post(`Notable`, Text, `Paths`) end
		end
	end
	Shared.LastReward = { Player = P; Path = Path; Tier = T }
end

function Shared.Check(P: Player)
	if Pending[P] then return end
	Pending[P] = true
	task.delay(2, function()
		Pending[P] = nil
		if P.Parent then pcall(Shared.CheckNow, P) end
	end)
end

---| counters (Progress.Tally) |---

function Shared.Count(P: Player, Key: string, N: number?)
	if not table.find(Config.Tally, Key) then return end
	local Prog = svc(`Player.Progression`)
	local Pr = Prog and Prog.Get(P)
	if not Pr then return end
	Pr.Tally[Key] = (Pr.Tally[Key] or 0) + (N or 1)
	Local.Save(P, Pr)
	Shared.Check(P)
end

---| start |---

function Shared.OnStart()
	local Data = svc(`Player.Data`)
	if Data and Data.ProfileLoaded then
		Data.ProfileLoaded:Connect(function(P) task.delay(5, function() if P.Parent then pcall(Shared.CheckNow, P) end end) end)
	end
	Players.PlayerRemoving:Connect(function(P) Pending[P] = nil Shared.FactsOverride[P] = nil end)
	-- the counters the old signals didn't keep (Progress.Tally); they count from 2.31 on
	local function on(Path: string, Signal: string, Key: string)
		local M = svc(Path)
		local S = M and M[Signal]
		if S and S.Connect then
			S:Connect(function(P) if typeof(P) == `Instance` and P:IsA(`Player`) then Shared.Count(P, Key) end end)
		else
			warn(`[Paths] missing {Path}.{Signal}`)
		end
	end
	on(`Quests.Duels`, `Won`, `DuelWins`)
	on(`Quests.Duels`, `ChampionDefeated`, `Champion`)
	on(`School.HallMonitor`, `Escaped`, `Escapes`)
	-- and the signals that can change a tier, so it shows without waiting for the sweep
	for _, S in { { `Social.Reputation`, `Changed` }, { `Social.Reputation`, `RelationshipChanged` }, { `Social.Factions`, `RankChanged` } } do
		local M = svc(S[1])
		if M and M[S[2]] then M[S[2]]:Connect(function(P) if typeof(P) == `Instance` and P:IsA(`Player`) then Shared.Check(P) end end) end
	end
	task.spawn(function()
		while true do
			task.wait(60)
			for _, P in Players:GetPlayers() do pcall(Shared.CheckNow, P) end
		end
	end)
end

---| tests |---

function Local.ZeroFacts()
	local F = { Subjects = {}; Rep = { Popularity = 0; Intimidation = 0; Trust = 0; Academics = 0 }; CliqueTiers = {}; Tally = {};
		BestStreak = 0; BestCard = 0; Met = 0; FactionRank = 1; Takedowns = 0; Showdowns = 0; ClubRank = `Rookie`;
		Orientation = false; AfterHours = false; FileKept = false; LineageTier = 1;
		Passed = 0; APlus = false; Streak = 0; DetentionsServed = 0; DaysClean = 10 ^ 6; Today = 0; InClub = false; Trusted = 0; Tuned = false }
	for _, K in Config.Tally do F.Tally[K] = 0 end
	return F
end
function Local.MaxFacts()
	local F = Local.ZeroFacts()
	for _, S in { `History`, `Mathematics`, `Chemistry`, `English` } do F.Subjects[S] = 5 end
	F.BestStreak, F.BestCard, F.Met, F.FactionRank, F.Takedowns, F.Showdowns = 30, 6, 24, 5, 200, 2
	F.Rep = { Popularity = 100; Intimidation = 100; Trust = 100; Academics = 100 }
	F.CliqueTiers = { Vigil = `Respected`; Court = `Friendly` }
	F.ClubRank, F.Orientation, F.AfterHours, F.FileKept, F.LineageTier = `Captain`, true, true, true, 3
	F.Tally = { DuelWins = 5; Champion = 1; Beasts = 12; Escapes = 1; Superlatives = 1 }
	return F
end

function Shared.ZeroFactsForTests() return Local.ZeroFacts() end -- (2.32) for the Honours test
function Shared.MaxFactsForTests() return Local.MaxFacts() end

function Shared.SelfTestForTests(P: Player)
	local R = {}
	-- the evaluator on made-up facts
	local Z, M = Shared.Evaluate(Local.ZeroFacts()), Shared.Evaluate(Local.MaxFacts())
	R.ZeroAllOne, R.MaxAllTop = true, true
	for _, Path in Config.Order do
		if Z[Path] ~= 1 then R.ZeroAllOne = false end
		if M[Path] ~= #Config.Paths[Path].Tiers then R.MaxAllTop = false end
	end
	local Honor = Local.ZeroFacts()
	Honor.Subjects = { History = 4; Mathematics = 4; Chemistry = 4; English = 2 }
	Honor.BestStreak, Honor.BestCard = 10, 4
	R.HonorStudent = Shared.Evaluate(Honor).Academic -- 3
	local Uneasy = Local.ZeroFacts() Uneasy.Tally.Beasts = 1
	R.UneasyByBeast = Shared.Evaluate(Uneasy).Supernatural -- 2
	R.FactsLive = Shared.Facts(P) ~= nil
	-- grants on the live player: from 1 to Honor Student, once; then lower facts never drop it
	local Saved, Pr = Local.Saved(P)
	if not (Saved and Pr) then R.NoProfile = true return R end
	local Before = table.clone(Saved)
	local Rep = svc(`Social.Reputation`)
	local Social = Rep.Get(P)
	local TitlesBefore, TitleBefore = table.clone(Social.Titles), Social.Title
	Pr.Paths = {} Local.Save(P, Pr)
	local Grants = 0
	local Con = Shared.Granted:Connect(function(Pl) if Pl == P then Grants += 1 end end)
	Shared.FactsOverride[P] = Honor
	local First = Shared.CheckNow(P)
	local Second = Shared.CheckNow(P)
	Shared.FactsOverride[P] = Local.ZeroFacts()
	Shared.CheckNow(P)
	task.wait(0.1) -- (SignalPlus delivers on a later frame)
	R.AfterDrop = Shared.Tier(P, `Academic`) -- still 3
	R.FirstGrants, R.SecondGrants, R.GrantSignals = #First, #Second, Grants -- 2, 0, 2 (Academic 2 and 3)
	R.TitleGiven = table.find(Rep.Get(P).Titles, `Honor Student`) ~= nil
	R.Attr = P:GetAttribute(`Path_Academic`) -- 3
	Con:Disconnect()
	Shared.FactsOverride[P] = nil
	-- put everything back
	local _, Pr2 = Local.Saved(P)
	Pr2.Paths = Before Local.Save(P, Pr2)
	Social.Titles = TitlesBefore Social.Title = TitleBefore Rep.Sync(P)
	Local.Mirror(P, Before)
	return R
end

function Shared.RewardTestForTests(P: Player)
	local Saved, Pr = Local.Saved(P)
	local Before = table.clone(Saved)
	local Rep = svc(`Social.Reputation`)
	local Social = Rep.Get(P)
	local TitlesBefore, TitleBefore = table.clone(Social.Titles), Social.Title
	local Bc = svc(`World.Broadcast`)
	local Items0 = #Bc.Items()
	Bc.PATestReset()
	Pr.Paths = {} Local.Save(P, Pr)
	local F = Local.MaxFacts()
	F.Rep.Intimidation, F.Takedowns, F.Showdowns, F.Tally.Beasts = 0, 0, 0, 0 -- only Combat stays at 1
	Shared.FactsOverride[P] = F
	Shared.LastReward = nil
	local Made = Shared.CheckNow(P)
	local R = { Made = #Made; Last = Shared.LastReward and `{Shared.LastReward.Path}:{Shared.LastReward.Tier}` or `none`;
		Mentions = #Bc.Items() - Items0; Top = P:GetAttribute(`PathTop`); Academic = P:GetAttribute(`Path_Academic`) }
	Shared.FactsOverride[P] = nil
	local _, Pr2 = Local.Saved(P)
	Pr2.Paths = Before Local.Save(P, Pr2)
	Social.Titles = TitlesBefore Social.Title = TitleBefore Rep.Sync(P)
	Local.Mirror(P, Before)
	return R
end

return Shared
