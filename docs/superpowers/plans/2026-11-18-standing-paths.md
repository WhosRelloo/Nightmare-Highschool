# Standing Paths (2.31) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Five Standing Paths whose tiers are computed from data the game already keeps. The highest tier is saved
and never drops; reaching one grants a title, a banner and (tier 4+) a broadcast mention, and students, two faction
leaders and three teachers react to it.

**Architecture:**
- **A new server module,** `Services.Player.Paths`, does the work in three steps:
  - It gathers a snapshot of facts from existing services (`Local.Facts`).
  - It evaluates the tiers with a pure function (`Shared.Evaluate`) against `Config.Paths`.
  - It saves only the highest tier reached in `Progress.Paths`, with five new counters in `Progress.Tally`.
- **`Progression.Sanitize` must keep both fields.** Today it drops every field it doesn't know about.
- **When it checks:** on join, on a 60-second sweep, and on a few signals for immediacy.
- **NPCs read player attributes** (`Path_<Path>`, `PathTop`) and a new dialogue `ctx.PathTier`.

**Tech Stack:** Luau (Roblox), installed through the rbxc bridge (`tools/phase5-2310/harness`); TestBridge self-tests
run in the game VM.

**Spec:** `docs/expansion/14-Progression-and-Identity.md` §1 to §3, §7, §8 and §10.

## Global Constraints

- No new HUD bar. Progress shows in titles, banners, NPC lines and (2.32) the Record.
- Granted on the server, once. A tier never drops (the saved value only ever rises).
- Tiers read existing data; the only new saved data is `Progress.Paths` and `Progress.Tally`.
- NH Combat Test only (placeId 98950102230473). The Map place stays untouched.
- No Seal icon in new UI. New UI from the kit's art and styles (here: the existing Moments banner).
- NPC lines: 60 characters at most, no gore, slurs or innuendo (Config.CliqueTalk's rule).
- Tests use slot 2 only (never slot 1), snapshot first, restore after. Set the clock to a LATER hour on the same day
  (21:30 by `start_play.lua`).
- Commits: `git -c user.name=Rello commit`, ending with the session's Co-Authored-By / Claude-Session lines.
- Install only in Edit mode (`harness/install.py`); an install during Play is lost.

---

## File structure

| File (mirror `tools/phase5-2310/live/<dotted path>.luau`) | Change |
|---|---|
| `ReplicatedStorage.Config.Paths` | **new**: the five paths, tiers, titles and conditions |
| `ServerScriptService.Services.Player.Paths` | **new**: facts, evaluator, saving, counters, rewards, attributes, test hooks |
| `ServerScriptService.Services.Player.Progression` | `Sanitize` keeps `Paths` and `Tally` |
| `ServerScriptService.Services.Features.Beasts` | one line in `Reward`: count the beast |
| `ServerScriptService.Services.Social.Superlatives` | one line in `Local.Grant`: count a won superlative |
| `StarterPlayer.StarterPlayerScripts.Controllers.Gui.Moments` | a `PathTier` banner |
| `ReplicatedStorage.Config.Broadcast` | a `Notable` kicker |
| `StarterPlayer.StarterPlayerScripts.Controllers.Gui.PhoneRadio` | the `Notable` kicker in the station's map |
| `ReplicatedStorage.Config.CliqueTalk.Generic` | a `Path` moment |
| `ServerScriptService.Services.AI.StudentBrain` | the `Path` greeting branch |
| `ServerScriptService.Services.Social.Dialogue` | `ctx.PathTier(Path)` |
| `ServerStorage.Dialogue.GiverTemplate`, `.LeaderTemplate` | `PathGreeting` / `PathHub` |
| `ServerStorage.Dialogue.{Sallow,Pryce,Whitlock,Ezra,Vesper}` | one path line each |
| `ServerScriptService.Services.Studio.TestBridge` | `PathsTest`, `TallyTest`, `PathRewardTest`, `RecognitionTest` |
| `tools/phase5-2310/harness/snapshot.lua`, `restore.py` | also cover Progress, titles and Phone |

---

### Task 1: Paths data, the evaluator and saving

**Files:**
- Create: `live/ReplicatedStorage.Config.Paths.luau`, `live/ServerScriptService.Services.Player.Paths.luau`
- Modify: `live/ServerScriptService.Services.Player.Progression.luau` (`Shared.Sanitize`, lines 57-70)
- Modify: `live/ServerScriptService.Services.Studio.TestBridge.luau` (append before `return Shared`)
- Modify: `harness/snapshot.lua`, `harness/restore.py`

**Interfaces:**
- Produces:
  - `Paths.Evaluate(F) -> { [Path]: number }` (pure)
  - `Paths.Facts(P) -> F?`
  - `Paths.Tier(P, Path) -> (number, string)`
  - `Paths.Next(P) -> { Path, Tier, Name, Missing: { string } }?`
  - `Paths.CheckNow(P) -> { { Path, Tier } }` (the grants made)
  - `Paths.Check(P)` (debounced, 2 s)
  - `Paths.Granted` (SignalPlus: Player, Path, Tier, Name)
  - `Paths.SelfTestForTests(P)`
  - `Paths.FactsOverride: { [Player]: F }` (tests only)
  - `Config.Paths.Order`, `Config.Paths.Paths[Path].Tiers[i] = { Name, Title?, Need = { { Text, Test } } }`

- [ ] **Step 1: Back up and mirror.** In Edit, copy every module this plan changes into
  `ServerStorage.NH_Backup.Phase5_pre_20261118` (a "(2.30)" suffix where a copy exists). Then dump each into
  `pre/` and `live/`:

```bash
cd /e/Nightmare-Highschool/tools/phase5-2310
python -X utf8 -I harness/dump.py ServerScriptService.Services.Player.Progression ServerScriptService.Services.Features.Beasts ServerScriptService.Services.Social.Superlatives StarterPlayer.StarterPlayerScripts.Controllers.Gui.Moments ReplicatedStorage.Config.Broadcast StarterPlayer.StarterPlayerScripts.Controllers.Gui.PhoneRadio ReplicatedStorage.Config.CliqueTalk.Generic ServerScriptService.Services.AI.StudentBrain ServerScriptService.Services.Social.Dialogue ServerStorage.Dialogue.GiverTemplate ServerStorage.Dialogue.LeaderTemplate ServerStorage.Dialogue.Sallow ServerStorage.Dialogue.Pryce ServerStorage.Dialogue.Whitlock ServerStorage.Dialogue.Ezra ServerStorage.Dialogue.Vesper ServerScriptService.Services.Studio.TestBridge
```

  Expected: one "N bytes" line per path. (A wrong path makes `dump.py` loop forever: stop it and fix the path.)

- [ ] **Step 2: Snapshot and restore cover the new data.** In `harness/snapshot.lua`, extend the encoded table with
  `Progress = Prof.Progress; Titles = Prof.Social and Prof.Social.Titles or {}; Title = Prof.Social and
  Prof.Social.Title or ""; Phone = Prof.Phone`. In `restore.py`'s Luau, after the Relationships line, add:

```lua
	if Snap.Progress then Prof.Progress = Snap.Progress end -- (2.31) paths and counters
	Prof.Social.Titles = Snap.Titles or Prof.Social.Titles
	if Snap.Title then Prof.Social.Title = Snap.Title end
	if Snap.Phone then Prof.Phone = Snap.Phone end -- (2.30 found the snapshot missed it)
	for _, Path in { "Academic", "Social", "Combat", "Athletic", "Supernatural" } do P:SetAttribute("Path_" .. Path, nil) end
	P:SetAttribute("PathTop", nil)
```

  Then start Play, run `python -X utf8 -I harness/gamevm.py start_play.lua`, take the snapshot
  (`python -X utf8 -I harness/gamevm.py snapshot.lua > harness/_slot2.json`; check it parses), and stop Play.

- [ ] **Step 3: Write the failing test.** Append to TestBridge (before `return Shared`):

```lua
-- (2.31) Standing Paths: the evaluator on made-up facts, then grants on the live player (put back after)
function Commands.PathsTest(PlayerName: string)
	return DeepCopy(require(ServerScriptService.Services.Player.Paths).SelfTestForTests(Players:FindFirstChild(PlayerName)))
end
```

- [ ] **Step 4: Run it, expect failure.** Install TestBridge, start Play, `start_play.lua`, then
  `python -X utf8 -I harness/bridge.py PathsTest '$P'`. Expected: an error (`Paths` is not a valid member).

- [ ] **Step 5: `Progression.Sanitize` keeps the new fields.** In `Shared.Sanitize`, change the first line to
  `local Out = { Level = 1; Exp = 0; Points = 0; Stats = {}; FatedDay = -1; Paths = {}; Tally = {} }` and, before
  `return Out` at the end of the function, add:

```lua
	-- (2.31) Standing Paths (Services.Player.Paths): the highest tier reached per path, and its counters
	local PathsCfg = require(ReplicatedStorage.Config.Paths)
	if typeof(Raw.Paths) == `table` then
		for _, Path in PathsCfg.Order do
			local T = num(Raw.Paths[Path], 1, #PathsCfg.Paths[Path].Tiers)
			if T then Out.Paths[Path] = T end
		end
	end
	if typeof(Raw.Tally) == `table` then
		for _, K in PathsCfg.Tally do
			local N = num(Raw.Tally[K], 0, 10 ^ 7)
			if N then Out.Tally[K] = N end
		end
	end
```

- [ ] **Step 6: Create `Config.Paths`.**

```lua
--[[ (2.31) Standing Paths (docs/expansion/14-Progression-and-Identity.md §3.1). Read by Services.Player.Paths.
	Each tier: Name, Title (granted through Reputation.AwardTitle; tier 1 grants none), Need = { { Text, Test(F) } }, all
	of which must pass. F is the facts snapshot Paths.Facts builds:
	  Subjects = { [Subject] = class level 1..5 }, BestStreak, BestCard (the best kept report card's average: A+ 6, A 5,
	  B 4, C 3, D 2, F 1, none 0), Rep = { Popularity, Intimidation, Trust, Academics } (0..100), Met (rostered classmates
	  met), CliqueTiers = { [CliqueId] = tier name }, FactionRank (best rank index, 1 Outsider .. 5 Inner Circle),
	  Takedowns (Kills + NPCKills), Showdowns (clique leaders beaten), ClubRank (Rookie .. Captain), Orientation,
	  AfterHours, FileKept (booleans), LineageTier, and Tally = { DuelWins, Champion, Beasts, Escapes, Superlatives }. ]]
local Paths = {}

local function atLeast(F, Level: number): number
	local N = 0
	for _, L in F.Subjects do if L >= Level then N += 1 end end
	return N
end
local function cliques(F, Tiers: { string }): number
	local N = 0
	for _, T in F.CliqueTiers do if table.find(Tiers, T) then N += 1 end end
	return N
end
local function need(Text: string, Test) return { Text = Text; Test = Test } end
local CLUB = { Rookie = 1; Starter = 2; Varsity = 3; Captain = 4 }

Paths.Order = { `Academic`, `Social`, `Combat`, `Athletic`, `Supernatural` }
Paths.Tally = { `DuelWins`, `Champion`, `Beasts`, `Escapes`, `Superlatives` }
Paths.Subjects = 4

Paths.Paths = {
	Academic = { Tiers = {
		{ Name = `Freshman Nobody`; Need = {} };
		{ Name = `Recognized Student`; Title = `Recognized Student`; Need = {
			need(`2 subjects at level 2`, function(F) return atLeast(F, 2) >= 2 end);
			need(`a 3-day attendance streak`, function(F) return F.BestStreak >= 3 end) } };
		{ Name = `Honor Student`; Title = `Honor Student`; Need = {
			need(`3 subjects at level 4`, function(F) return atLeast(F, 4) >= 3 end);
			need(`a B report card`, function(F) return F.BestCard >= 4 end);
			need(`a 10-day attendance streak`, function(F) return F.BestStreak >= 10 end) } };
		{ Name = `Academic Elite`; Title = `Academic Elite`; Need = {
			need(`every subject at level 5`, function(F) return atLeast(F, 5) >= Paths.Subjects end);
			need(`an A report card`, function(F) return F.BestCard >= 5 end);
			need(`Academics 50`, function(F) return F.Rep.Academics >= 50 end) } };
	} };
	Social = { Tiers = {
		{ Name = `Unknown`; Need = {} };
		{ Name = `Recognized`; Title = `Recognized`; Need = {
			need(`meet 5 classmates`, function(F) return F.Met >= 5 end) } };
		{ Name = `Popular`; Title = `Popular`; Need = {
			need(`meet 12 classmates`, function(F) return F.Met >= 12 end);
			need(`Popularity 25`, function(F) return F.Rep.Popularity >= 25 end);
			need(`Friendly with 2 cliques`, function(F) return cliques(F, { `Friendly`, `Respected` }) >= 2 end) } };
		{ Name = `Influential`; Title = `Influential`; Need = {
			need(`Member of a faction`, function(F) return F.FactionRank >= 3 end);
			need(`Popularity 50`, function(F) return F.Rep.Popularity >= 50 end);
			need(`Respected by a clique`, function(F) return cliques(F, { `Respected` }) >= 1 end) } };
		{ Name = `School Legend`; Title = `School Legend`; Need = {
			need(`a faction's Inner Circle`, function(F) return F.FactionRank >= 5 end);
			need(`Popularity 80`, function(F) return F.Rep.Popularity >= 80 end);
			need(`meet all 24 classmates`, function(F) return F.Met >= 24 end);
			need(`win a weekly superlative`, function(F) return F.Tally.Superlatives >= 1 end) } };
	} };
	Combat = { Tiers = {
		{ Name = `Beginner`; Need = {} };
		{ Name = `Street Fighter`; Title = `Street Fighter`; Need = {
			need(`5 takedowns`, function(F) return F.Takedowns >= 5 end) } };
		{ Name = `Enforcer`; Title = `Enforcer`; Need = {
			need(`25 takedowns`, function(F) return F.Takedowns >= 25 end);
			need(`win 3 duels`, function(F) return F.Tally.DuelWins >= 3 end);
			need(`Intimidation 25`, function(F) return F.Rep.Intimidation >= 25 end) } };
		{ Name = `Notorious`; Title = `Notorious`; Need = {
			need(`75 takedowns`, function(F) return F.Takedowns >= 75 end);
			need(`win a clique showdown`, function(F) return F.Showdowns >= 1 end);
			need(`3 beasts`, function(F) return F.Tally.Beasts >= 3 end);
			need(`Intimidation 50`, function(F) return F.Rep.Intimidation >= 50 end) } };
		{ Name = `Feared`; Title = `Feared`; Need = {
			need(`150 takedowns`, function(F) return F.Takedowns >= 150 end);
			need(`beat the Ring's champion`, function(F) return F.Tally.Champion >= 1 end);
			need(`Intimidation 80`, function(F) return F.Rep.Intimidation >= 80 end) } };
	} };
	Athletic = { Tiers = { -- exactly the sports club rank (Config.Sports), never recomputed
		{ Name = `Rookie`; Need = {} };
		{ Name = `Starter`; Title = `Starter`; Need = { need(`Starter in your club`, function(F) return (CLUB[F.ClubRank] or 1) >= 2 end) } };
		{ Name = `Varsity`; Title = `Varsity`; Need = { need(`Varsity in your club`, function(F) return (CLUB[F.ClubRank] or 1) >= 3 end) } };
		{ Name = `Captain`; Title = `Captain`; Need = { need(`Captain of your club`, function(F) return (CLUB[F.ClubRank] or 1) >= 4 end) } };
	} };
	Supernatural = { Tiers = {
		{ Name = `Unaware`; Need = {} };
		{ Name = `Uneasy`; Title = `Uneasy`; Need = {
			need(`finish Orientation, or meet a beast`, function(F) return F.Orientation or F.Tally.Beasts >= 1 end) } };
		{ Name = `Initiated`; Title = `Initiated`; Need = {
			need(`finish After Hours`, function(F) return F.AfterHours end);
			need(`lineage tier 2, or 5 beasts`, function(F) return F.LineageTier >= 2 or F.Tally.Beasts >= 5 end) } };
		{ Name = `Keeper of Secrets`; Title = `Keeper of Secrets`; Need = {
			need(`keep the file in After Hours`, function(F) return F.FileKept end);
			need(`lineage tier 3, or 10 beasts`, function(F) return F.LineageTier >= 3 or F.Tally.Beasts >= 10 end) } };
	} };
}

-- the lines that mention a student by tier (Services.World.Broadcast), tier 4 and up
Paths.Mention = "Congratulations to {Name}, now {Article} {Tier}." -- (a plain string: {Name} is filled by Paths, not interpolated)

return Paths
```

- [ ] **Step 7: Create `Services.Player.Paths`.**

```lua
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
	for Subject, C in Prof.Classes or {} do
		if typeof(C) == `table` then F.Subjects[Subject] = tonumber(C.Level) or 1 end
	end
	F.BestStreak = (typeof(Prof.Attendance) == `table` and tonumber(Prof.Attendance.BestStreak)) or 0
	F.BestCard = 0
	pcall(function()
		local St = svc(`School.ReportCards`).State(P)
		for _, Card in (St and St.Cards) or {} do F.BestCard = math.max(F.BestCard, GRADE[Card.Average or ``] or 0) end
	end)
	local Rep = svc(`Social.Reputation`)
	for Cat in require(ReplicatedStorage.Config.Reputation).Categories do
		F.Rep[Cat] = (Rep and Rep.Value(P, Cat)) or 0
	end
	F.Met = 0
	pcall(function()
		local Roster = svc(`Social.Roster`)
		for Id, R in Rep.Get(P).Relationships do
			if typeof(R) == `table` and R.Met == true and Roster.IsRostered(Id) then F.Met += 1 end
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
	F.ClubRank = `Rookie`
	pcall(function()
		local S = svc(`Sports.Clubs`).Get(P)
		if S and S.Club then F.ClubRank = require(ReplicatedStorage.Config.Sports).RankFor(S.ClubExp) end
	end)
	local Q = svc(`Quests.Quests`)
	F.Orientation = Q ~= nil and Q.IsDone(P, `Orientation`)
	F.AfterHours = Q ~= nil and Q.IsDone(P, `AfterHours`)
	F.FileKept = F.AfterHours and Q.Decided(P, `FileKept`) ~= `Lose`
	F.LineageTier = 1
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
	return Made
end

-- what a tier gives: its title (Task 3 adds the banner, attributes and the broadcast mention)
function Local.Reward(P: Player, Path: string, T: number, Tier, Last: boolean)
	local Rep = svc(`Social.Reputation`)
	if Tier.Title and Rep then pcall(Rep.AwardTitle, P, Tier.Title) end
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
		Orientation = false; AfterHours = false; FileKept = false; LineageTier = 1 }
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

return Shared
```

  (In the live part, `Honor` reaches Academic 3 only: its beasts, Orientation and met count are all zero, so
  `FirstGrants` is 2. **Expected values are in Step 9.**)

- [ ] **Step 8: Install.** Stop Play. In Edit:

```bash
python -X utf8 -I harness/install.py live/ReplicatedStorage.Config.Paths.luau live/ServerScriptService.Services.Player.Paths.luau live/ServerScriptService.Services.Player.Progression.luau live/ServerScriptService.Services.Studio.TestBridge.luau
```

  Expected: four lines with sizes, no PARSE FAIL.

- [ ] **Step 9: Run the test, expect pass.** Start Play, `start_play.lua`, `bridge.py PathsTest '$P'`. Expected:
  `ZeroAllOne true, MaxAllTop true, HonorStudent 3, UneasyByBeast 2, FactsLive true, FirstGrants 2, SecondGrants 0,
  GrantSignals 2, AfterDrop 3, TitleGiven true, Attr 3`. Then in the game VM check the slot's real tiers:
  `return HttpService:JSONEncode(require(SSS.Player.Paths).Facts(P))` (each field a number or boolean), and that
  `Progression.Get(P).Paths` holds whatever the real facts earn. Restore slot 2 (`restored`).

- [ ] **Step 10: Commit.**

```bash
git add tools/phase5-2310 && git -c user.name=Rello commit -m "2.31 (1/6): Standing Paths: Config.Paths, the evaluator, saved tiers that never drop"
```

---

### Task 2: The counters

**Files:**
- Modify: `live/ServerScriptService.Services.Player.Paths.luau` (`Shared.OnStart`)
- Modify: `live/ServerScriptService.Services.Features.Beasts.luau` (`Shared.Reward`, about line 976)
- Modify: `live/ServerScriptService.Services.Social.Superlatives.luau` (`Local.Grant`, about line 219)
- Modify: TestBridge

**Interfaces:**
- Consumes: `Paths.Count(P, Key, N?)`, `Config.Paths.Tally`
- Produces: `Progress.Tally.{DuelWins, Champion, Beasts, Escapes, Superlatives}` rising from the live signals

- [ ] **Step 1: Failing test.** TestBridge:

```lua
-- (2.31) the five counters, each from its real signal; put back after
function Commands.TallyTest(PlayerName: string)
	local SSS = ServerScriptService.Services
	local P = Players:FindFirstChild(PlayerName)
	local Prog = require(SSS.Player.Progression)
	local Before = table.clone(Prog.Get(P).Tally)
	require(SSS.Quests.Duels).Won:Fire(P)
	require(SSS.Quests.Duels).ChampionDefeated:Fire(P)
	require(SSS.School.HallMonitor).Escaped:Fire(P, `Curfew`)
	require(SSS.Features.Beasts).Reward(P, { Name = `Test beast`; Reward = {} })
	task.wait(0.5)
	local After = Prog.Get(P).Tally
	local Out = {}
	for _, K in { `DuelWins`, `Champion`, `Escapes`, `Beasts` } do Out[K] = (After[K] or 0) - (Before[K] or 0) end
	local Pr = Prog.Get(P) Pr.Tally = Before
	require(SSS.Player.Data).UpdateState(P, { type = `SetProgress`; progress = Pr })
	return Out
end
```

- [ ] **Step 2: Run, expect failure:** install TestBridge, Play, `bridge.py TallyTest '$P'`. Expected all 0.
- [ ] **Step 3: Hook the signals.** In `Paths.OnStart`, before the sweep loop:

```lua
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
```

- [ ] **Step 4: Beasts.** In `Beasts.Shared.Reward`, as its first line:
  `pcall(function() require(ServerScriptService.Services.Player.Paths).Count(P, \`Beasts\`) end) -- (2.31) Standing Paths`
- [ ] **Step 5: Superlatives.** In `Local.Grant`, directly before `Social.TempTitles[D.Title] = Until`, add:

```lua
			if Social.TempTitles[D.Title] ~= Until then -- (2.31) a superlative won (counted once per award and week)
				pcall(function() require(game:GetService(`ServerScriptService`).Services.Player.Paths).Count(P, `Superlatives`) end)
			end
```

- [ ] **Step 6: Install** Paths, Beasts, Superlatives and TestBridge (Edit). **Run** `TallyTest`. Expected:
  `DuelWins 1, Champion 1, Escapes 1, Beasts 1`. Then run `PathsTest` again (still passing). Restore slot 2.
- [ ] **Step 7: Commit** `2.31 (2/6): the counters (duels, the champion, beasts, escapes, superlatives)`.

---

### Task 3: What a tier gives (banner, attributes, the broadcast mention)

**Files:**
- Modify: `live/ServerScriptService.Services.Player.Paths.luau` (`Local.Reward`)
- Modify: `live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.Moments.luau`
- Modify: `live/ReplicatedStorage.Config.Broadcast.luau`, `live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.PhoneRadio.luau`
- Modify: TestBridge

**Interfaces:**
- Consumes: `Fx.Fire(P, Kind, Data)` (`Services.Features.Fx`), `Broadcast.PA(Text) -> boolean`,
  `Broadcast.Post(Kind, Text, Source)`
- Produces: NHFx `PathTier { Path, Tier, Name, Of }`; Broadcast item Kind `Notable`

- [ ] **Step 1: Failing test.** TestBridge:

```lua
-- (2.31) reaching a tier: the banner event, and a broadcast mention from tier 4 (put back after)
function Commands.PathRewardTest(PlayerName: string)
	local SSS = ServerScriptService.Services
	local P = Players:FindFirstChild(PlayerName)
	local Paths = require(SSS.Player.Paths)
	return DeepCopy(Paths.RewardTestForTests(P))
end
```

- [ ] **Step 2: Run, expect failure** (`RewardTestForTests` is nil).
- [ ] **Step 3: `Local.Reward` gives everything.** Replace it in Paths:

```lua
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
```

  And add the test hook above `return Shared`:

```lua
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
```

- [ ] **Step 4: The banner (client).** In Moments, next to `Fx.On(\`QuestBeat\`, Local.QuestBeat)`, add
  `Fx.On(\`PathTier\`, Local.PathTier)`, and above the "P1-5 Clue Discovered" section:

```lua
---| (2.31) Standing Path tier |---

function Local.PathTier(D)
	if typeof(D) ~= `table` or typeof(D.Name) ~= `string` then return end
	Local.Enqueue(function()
		Local.Banner({ Caption = `Standing: {D.Path or ``}`; Title = string.upper(D.Name); Text = `The {D.Path} path, tier {D.Tier} of {D.Of}.`;
			Color = GOLD; Icon = `IconBannerQuestDone`; Sound = `Chime`; Hold = 3.2 })
	end)
end
```

- [ ] **Step 5: The `Notable` kicker.** `Config.Broadcast.Kickers` gains `Notable = \`SHOUT-OUT\``. In PhoneRadio's
  `Shared.Station`, the `Kick` table gains `Notable = \`SHOUT-OUT\``.
- [ ] **Step 6: Install** Paths, Moments, Config.Broadcast, PhoneRadio and TestBridge (Edit). **Run**
  `PathRewardTest`. Expected: `Made` 13 (every tier above 1 of Academic 3, Social 4, Athletic 3 and Supernatural 3;
  Combat stays at 1; recount if Config changes), `Last` "Supernatural:4", `Mentions` 4 (one per path whose newest tier
  is 4+: Academic, Social, Athletic, Supernatural; at 21:30 the station is on air, so all are `Notable` posts), `Top`
  "Social" (tier 5 is the highest), `Academic` 4. Then run `PathsTest` and `TallyTest` again (passing).
- [ ] **Step 7: See it.** In Play, from the client VM set nothing; in the game VM run `Paths.CheckNow(P)` with a
  `FactsOverride` that reaches Honor Student only, take a screenshot of the banner, save it as
  `review/path_banner.jpg`, and put the slot back (`PathsTest`'s restore pattern, or restore.py). Open Night FM's
  Station after a tier-4 test to see a SHOUT-OUT card.
- [ ] **Step 8: Commit** `2.31 (3/6): reaching a tier: the title, a banner, and a shout-out from tier 4`.

---

### Task 4: NPCs recognise it

**Files:**
- Modify: `live/ReplicatedStorage.Config.CliqueTalk.Generic.luau`, `live/ServerScriptService.Services.AI.StudentBrain.luau`
- Modify: `live/ServerScriptService.Services.Social.Dialogue.luau` (`Local.Context`)
- Modify: `live/ServerStorage.Dialogue.GiverTemplate.luau`, `live/ServerStorage.Dialogue.LeaderTemplate.luau`
- Modify: `live/ServerStorage.Dialogue.{Sallow,Pryce,Whitlock,Ezra,Vesper}.luau`
- Modify: TestBridge

**Interfaces:**
- Consumes: player attributes `PathTop`, `Path_<Path>` (Task 1); `Paths.Tier(P, Path)`
- Produces: CliqueTalk moment `Path[<Path>][Attitude|Any]`; `ctx.PathTier(Path) -> number`; template fields
  `PathGreeting = { Path, Tier, Text }` (GiverTemplate) and `PathHub = { Path, Tier, Text }` (LeaderTemplate)

- [ ] **Step 1: Failing test.** TestBridge:

```lua
-- (2.31) NPCs and paths: the student pool, and each tree's line with a fake ctx at tier 3 and at tier 1
function Commands.RecognitionTest()
	local Talk = require(ServerScriptService.Services.AI.StudentBrain.Talk)
	local Out = { Pools = {} }
	for _, Path in { `Academic`, `Social`, `Combat`, `Athletic`, `Supernatural` } do
		local Pool = Talk.Pool(nil, `Path`, `Neutral`, Path)
		Out.Pools[Path] = Pool and #Pool or 0
	end
	local Trees = game:GetService(`ServerStorage`).Dialogue
	local function fake(Tier: number)
		return { PathTier = function() return Tier end; Member = function() return false end; State = function() return `Acquaintance` end;
			Decided = function() return nil end; Objective = function() return nil end }
	end
	Out.Lines = {}
	for _, Name in { `Sallow`, `Pryce`, `Whitlock`, `Ezra`, `Vesper` } do
		local Tree = require(Trees[Name]) -- the templates return { Start, Nodes }
		local Hub = Tree.Nodes and Tree.Nodes.Hub
		local T = Hub and Hub.Text
		local At3 = if typeof(T) == `function` then T(fake(3)) else T
		local At1 = if typeof(T) == `function` then T(fake(1)) else T
		Out.Lines[Name] = { Differs = At3 ~= At1; At3 = At3 }
	end
	return Out
end
```

- [ ] **Step 2: Run, expect failure:** every pool 0, every `Differs` false. (First check which node opens each
  tree: `GiverTemplate` and `LeaderTemplate` both build `Nodes.Hub`; if a template's opening node has another id,
  use that id in the test and in Step 5.)
- [ ] **Step 3: The `Path` moment.** In `CliqueTalk.Generic`, add (≤ 60 characters a line):

```lua
	-- (2.31) a Standing Path at tier 3+ (the player's PathTop): StudentBrain greets with it now and then
	Path = {
		Academic = { Any = { `That's the honor student.`, `Top of the class, that one.`, `Heard you aced another test.` } };
		Social = { Any = { `Everyone knows you, huh?`, "Oh, it's {Name}. Of course it is.", `You know everyone here.` } };
		Combat = { Any = { `Don't start with that one.`, `I heard about you. Respect.`, `Easy. I'm not looking for trouble.` } };
		Athletic = { Any = { "Good game last week, {Name}.", `There's the varsity star.`, `Saving a seat at the next match.` } };
		Supernatural = { Any = { `You've seen things. I can tell.`, `You were out the night it rang.`, `People say you know about Mira.` } };
	};
```

- [ ] **Step 4: StudentBrain.** In `greeting(S, Rec)`, directly before
  `local Race = Pl and Pl:GetAttribute(\`Race\`)`, add:

```lua
	local Top = Pl and Pl:GetAttribute(`PathTop`) -- (2.31) a Standing Path at tier 3+: "That's the honor student."
	if Top and math.random() < 0.25 then return `Path`, { Sub = Top }, daily(C) end
```

- [ ] **Step 5: Dialogue.** In `Local.Context`, after `function ctx.Rep(...)`, add:

```lua
	function ctx.PathTier(Path: string) -- (2.31) Standing Paths (Services.Player.Paths)
		local Ok, T = pcall(function() return require(ServerScriptService.Services.Player.Paths).Tier(Player, Path) end)
		return if Ok and typeof(T) == `number` then T else 1
	end
```

  In GiverTemplate, replace `Text = L.Greeting;` in `Nodes.Hub` with:

```lua
		Text = function(ctx) -- (2.31) a Standing Path line first, once the student has earned it
			local PG = L.PathGreeting
			if PG and ctx.PathTier and ctx.PathTier(PG.Path) >= PG.Tier then return PG.Text end
			if typeof(L.Greeting) == `function` then return L.Greeting(ctx) end
			return L.Greeting
		end;
```

  Add `PathGreeting = { Path, Tier, Text }?,` to its header comment. In LeaderTemplate's `Nodes.Hub.Text`, as its
  first line: `if L.PathHub and ctx.PathTier and ctx.PathTier(L.PathHub.Path) >= L.PathHub.Tier then return L.PathHub.Text end`
  (and `PathHub = { Path, Tier, Text }?,` in its header).
- [ ] **Step 6: The five lines.** Add to each tree's table:
  - Sallow: `PathGreeting = { Path = \`Academic\`; Tier = 3; Text = \`The honor student. Sit where I can see your working.\` };`
  - Pryce: `PathGreeting = { Path = \`Social\`; Tier = 3; Text = \`Ah, the star of the corridor! Enter to applause.\` };`
  - Whitlock: `PathGreeting = { Path = \`Supernatural\`; Tier = 3; Text = \`You've been reading the old records. Careful which ones.\` };`
  - Ezra: `PathHub = { Path = \`Academic\`; Tier = 3; Text = \`Honor Student now. The Vigil notices names like yours.\` };`
  - Vesper: `PathHub = { Path = \`Combat\`; Tier = 3; Text = \`Enforcer. The Court has been hearing your name.\` };`
- [ ] **Step 7: Install** the ten files (Edit). **Run** `RecognitionTest`. Expected: every pool 3; every
  `Differs` true, with each `At3` the line above.
- [ ] **Step 8: Live.** In Play, after `PathsTest`'s pattern sets `Path_Academic = 3` and `PathTop = "Academic"` (a
  `FactsOverride` reaching Honor Student, then `CheckNow`), stand by students for up to 2 minutes and read the
  bubbles (client VM: BillboardGui text under `workspace.Live`) for a `Path` line, then talk to Ms. Sallow. Screenshot
  `review/path_greeting.jpg`. Restore slot 2.
- [ ] **Step 9: Commit** `2.31 (4/6): students, two faction leaders and three teachers recognise your path`.

---

### Task 5: Regression

- [ ] **Step 1: Self-tests in one session:** `PathsTest`, `TallyTest`, `PathRewardTest`, `RecognitionTest`; 2.30
  (`BroadcastTest`, `CurfewTest`); 2.29 (`IncidentTest`, `RumourTest`, `RumourSafetyTest`); 2.28 (`StaffTest`,
  `StaffPlanTest`, `TimetableTest`, `SleepTest`); 2.27 (`RosterTest`, `Rostered`, `RelationshipCapTest`,
  `MemoryTest`); the cutscene suite (`CineJudgeTest`, `CineGraphTest`, `AfterHoursMigrateTest`, `CineVoteTest`).
- [ ] **Step 2: Unchanged behaviour.**
  - Level up (`AwardForTests`): the Bell Toll banner as before, and Level/EXP intact (`Progression.Get`).
  - Spend a point in M: still works and still saves (Sanitize change).
  - A real rejoin keeps `Progress.Paths` (stop Play, start, `Progression.Get(P).Paths` unchanged).
  - Duels, a beast kill and a superlative grant still pay as before.
  - Greetings still vary (intro, grudge, race, clique lines); talking to Hale still asks the roll-call question.
- [ ] **Step 3: The console:** no errors from Paths, Progression, Beasts, Superlatives, Moments, StudentBrain,
  Dialogue or the five trees.
- [ ] **Step 4:** restore slot 2 and check it, stop Play, `save_place`.

### Task 6: Docs and release 2.31.0

- [ ] **Step 1:** CHANGELOG `[2.31.0]` (stage only this hunk), README, Implementation-Status, a Discord game update
  (`updates/discord/game-updates/<date>-standing-paths.md`) and its index line.
- [ ] **Step 2:** doc 14's status ("2.31 shipped") and §10's new deltas (below).
- [ ] **Step 3:** vault copies (CHANGELOG entry, the post, doc 14) and the home-note line.
- [ ] **Step 4:** commit, then merge `phase5-progression` into `main` with `--no-ff -F <file>`, stashing unrelated
  working changes around it. Don't push.

## Spec deltas (record in doc 14 §10 at release)

1. **The evaluator is its own module,** `Services.Player.Paths`, not code inside `Progression` (24 KB already). Its
   data still lives in `Progress`, and `Progression.Sanitize` keeps it.
2. **The counters:** `Superlatives` replaces `Showdowns`, because showdown wins are already saved
   (`Social.Showdowns.Won`); a won superlative was saved nowhere.
3. **NPC recognition:** students (all cliques, through `Generic`), Ezra and Vesper, and Ms. Sallow, Mr. Pryce and Dr.
   Whitlock. Mr. Hale keeps his Orientation lines; clique leaders and coaches can gain lines later.
4. **The broadcast mention** is a PA line by day, or a `SHOUT-OUT` item on the Midnight Broadcast when the station is
   on air (or when the PA has already spoken this segment).
5. **Checks** run on join, every 60 seconds, and on reputation, relationship, faction-rank and counter changes.

## Self-review
- **Spec coverage:** §3.1 (Config.Paths) is Task 1 Step 6; §3.2 (the evaluator, `Tier`, `Next`, `CheckForTests` as
  `CheckNow` / `SelfTestForTests`) is Task 1; §3.3 (title, banner, Record entry, mention) is Tasks 1 and 3 (the Record
  entry waits for 2.32 by the spec's own rule); §3.4 (students, leaders, teachers) is Task 4; §3.5 acceptance is
  Tasks 1 to 5; §7's `Progress.Paths` and `Progress.Tally` are Task 1 Step 5; §8's backups and slot rules are Task 1
  Steps 1-2 and Task 5.
- **Placeholders:** none; every code step has its code.
- **Names:** `Paths.Count`, `Paths.Check`, `Paths.CheckNow`, `Paths.Tier`, `Paths.Facts`, `Paths.FactsOverride`,
  `Paths.Granted`, `Paths.SelfTestForTests`, `Paths.RewardTestForTests`, `Config.Paths.Order` / `.Tally` / `.Paths` /
  `.Mention`, attributes `Path_<Path>` and `PathTop`, Fx `PathTier`, Broadcast kind `Notable`, `ctx.PathTier`,
  `PathGreeting`, `PathHub`: used the same way in every task.
