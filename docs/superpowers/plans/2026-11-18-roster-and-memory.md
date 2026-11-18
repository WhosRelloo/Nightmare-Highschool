# Roster & Memory (2.27) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The school's background students become 24 named, rostered students who keep the same look every
server, remember what you did to them across rejoins, introduce themselves, and show in the Students list once met.

**Architecture:**
- **Identity:** `Config.Students` (data) and `Social.Roster` (lookups, seeded randomness) are the roster.
- **Bodies:** `Features.Schedules` makes one body per roster entry instead of 14 anonymous ones.
- **Memory:** `Social.Reputation` saves an entry per rostered student (`Value`, `Met`, `Last`, `Flags`, capped at
  64). `AI.StudentBrain` and its `Talk` read and write it for greetings, introductions, shoves and snacks.
- **The client:** `Controllers.Gui.Students` lists the students you've met.

**Tech Stack:** Roblox Luau in NH Combat Test (placeId 98950102230473), through the Studio MCP and the
`tools/phase4-2270/harness` helpers (`install.py`, `dump.py`, `bridge.py`, `client.py`, `snapshot.lua`, `restore.py`,
`start_play.lua`), run with `python -X utf8 -I`.

**Spec:** `docs/expansion/13-Living-School.md` §2 (2.27), §6, §7 and §8. The deltas this plan makes are listed in
§"Spec deltas" at the end. Record them in doc 13 §9 at release.

## Global Constraints

- Build only in **NH Combat Test**. The Map place is read-only.
- **Backup** before the first edit of each existing script: copy it into `ServerStorage.NH_Backup.Phase4_pre_20261118`.
- **Mirror:**
  - `tools/phase4-2270/pre/` holds the first dump. Already done for Reputation, Config.Reputation, StudentBrain,
    StudentBrain.Talk, StudentBrain.Lines, Schedules, Config.Cliques, Config.NpcBuilds, Strangers,
    Controllers.Gui.Students, TestBridge and Player.Data.
  - Edit `tools/phase4-2270/live/<dotted path>.luau`, then install with
    `python -X utf8 -I tools/phase4-2270/harness/install.py <files>`. It parse-checks first and recreates each
    ModuleScript, keeping its children.
- **Tests** are TestBridge commands (`ServerStorage.NHTestBridge`), run in Play with
  `python -X utf8 -I tools/phase4-2270/harness/bridge.py <Command> '$P'`. They return JSON `{ok, result}`.
- **Test slot 2** only (`start_play.lua` picks it). Snapshot before and restore after any test that changes saved
  state. Never use slot 1 (the owner's).
- **UI:** existing kit pieces only (`Kit.PlayerListRow`, `Theme`). Don't edit `ReplicatedStorage.UI.Components`; the
  peer session "Nightmare Highschool UI kit" owns it.
- **Code style:** `Shared` / `Local` tables, backtick strings, `-- (2.27)` comments on changed lines, no new
  per-frame server loop.
- **Commits:** `git -c user.name=Rello commit`, ending with the Co-Authored-By and Claude-Session lines, on branch
  `phase4-living-school`. Stage only this plan's files.
- **New files:** on E: (the repo is on E:).

---

## File structure

| File (`tools/phase4-2270/live/…`) | Responsibility | New / changed |
|---|---|---|
| `ReplicatedStorage.Config.Students.luau` | The 24 roster entries, `ById`, the set and clique lists | new |
| `ServerScriptService.Services.Social.Roster.luau` | Roster lookups, seeded `Random` per student, live-body binding, `SelfTestForTests` | new |
| `ServerScriptService.Services.Features.Schedules.luau` | One body per roster entry; seeded looks; `NHStudentId`, `RosterId`, `Temper` | changed |
| `ServerScriptService.Services.Social.Reputation.luau` | Saved entries for the cast and roster, `Last`/`Flags`, the 64 cap, `Entry`, flag argument | changed |
| `ServerScriptService.Services.AI.StudentBrain.luau` | Memory from the saved entry; introductions; shove and snack changes; `GreetingForTests` | changed |
| `ServerScriptService.Services.AI.StudentBrain.Talk.luau` | `Attitude` reads the saved state | changed |
| `ServerScriptService.Services.AI.StudentBrain.Lines.luau` | `Intro`, `Greet.Grudge`, `Greet.Grateful` by temper | changed |
| `StarterPlayer.StarterPlayerScripts.Controllers.Gui.Students.luau` | The Classmates group | changed |
| `ServerScriptService.Services.Studio.TestBridge.luau` | `RosterTest`, `RelationshipCapTest`, `MemoryTest`, `Rostered` | changed |
| `tools/phase4-2270/harness/snapshot.lua`, `restore.py` | Also snapshot and restore `Social.Relationships` | changed |

---

### Task 1: The roster data and the Roster service

**Files:**
- Create: `ReplicatedStorage.Config.Students.luau`, `ServerScriptService.Services.Social.Roster.luau`
- Modify: `ServerScriptService.Services.Studio.TestBridge.luau` (add `RosterTest`)
- Modify: `tools/phase4-2270/harness/snapshot.lua`, `restore.py` (Social)

**Interfaces:**
- Produces:
  - `Config.Students.List: { Entry }`, where `Entry = { Id, Name, First, Clique, Year, Bravery, Temper, Set, Bio, SkipChance? }`
  - `Config.Students.ById: { [string]: Entry }`, `Config.Students.Tempers`, `Config.Students.Sets`
  - `Roster.All() -> { Entry }`, `Roster.Get(Id) -> Entry?`, `Roster.IsRostered(Id) -> boolean`
  - `Roster.Rng(Id) -> Random` (seeded by `NpcBuilds.Seed("Roster|"..Id)`)
  - `Roster.Bind(Id, S)`, `Roster.Body(Id) -> S?`
  - `Roster.SelfTestForTests() -> { [string]: any }`

- [x] **Step 1: Write the failing test.** Add to TestBridge, beside `Phase1SelfTest`:

```lua
-- (2.27) the roster's data and seeding (nothing saved)
function Commands.RosterTest(PlayerName: string)
	return DeepCopy(require(game:GetService(`ServerScriptService`).Services.Social.Roster).SelfTestForTests())
end
```

Install TestBridge, start Play (`start_play.lua`), then run `bridge.py RosterTest '$P'`.
Expected: `ok:false` with "Roster is not a valid member" (the module doesn't exist yet).

- [x] **Step 2: Write `Config.Students`** with all 24 rows from doc 13 §8. `First` is the first word of `Name`. Only
  Delinquents have `SkipChance`. The first rows are shown; the other 21 follow the same shape, copied from the doc 13
  table exactly:

```lua
--[[ (2.27) The roster: 24 named students, 3 per clique (docs/expansion/13-Living-School.md §2.1, §8).
	Ids are save keys: never rename one. Temper picks greeting and introduction lines; Set is the timetable set
	(2.28). Bravery feeds NpcBuilds' personality. ]]
local List = {
	{ Id = `OdetteMarsh`; Name = `Odette Marsh`; Clique = `Choir`; Year = 3; Bravery = 0.3; Temper = `Warm`; Set = `A`;
		Bio = `First soprano. Swears the chapel organ plays one note after the hymn ends.` };
	{ Id = `SilasPenwright`; Name = `Silas Penwright`; Clique = `Choir`; Year = 2; Bravery = 0.5; Temper = `Cool`; Set = `B`;
		Bio = `Copies every hymn by hand, and keeps the pages nobody sings.` };
	{ Id = `AgnesLowe`; Name = `Agnes Lowe`; Clique = `Choir`; Year = 1; Bravery = 0.2; Temper = `Shy`; Set = `C`;
		Bio = `New to the Choir. Hums when she's frightened, which is often.` };
	-- … CassiusRook … SloaneMercer, every row of doc 13 §8, in that order. Delinquents add SkipChance:
	-- JaxCalloway 0.2, NicoRuiz 0.15, SloaneMercer 0.15.
}
local ById = {}
for _, E in List do
	E.First = string.match(E.Name, `^(%S+)`)
	ById[E.Id] = E
end
return {
	List = List;
	ById = ById;
	Tempers = { `Warm`, `Cool`, `Sharp`, `Shy`, `Wild` };
	Sets = { `A`, `B`, `C`, `D` };
}
```

- [x] **Step 3: Write `Social.Roster`:**

```lua
--[[ (2.27) Roster (server). Services.Social.Roster: who the rostered students are (Config.Students), each one's
	seeded randomness (the same look every server), and the body Schedules made for them.
	API: All(), Get(Id), IsRostered(Id), Rng(Id), Bind(Id, S), Body(Id), SelfTestForTests() ]]
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local Config = require(ReplicatedStorage.Config.Students)
local NpcBuilds = require(ReplicatedStorage.Config.NpcBuilds)
local Cliques = require(ReplicatedStorage.Config.Cliques)

local Shared = {}
local Bodies = {} :: { [string]: any }

function Shared.All() return Config.List end
function Shared.Get(Id: string) return Config.ById[Id] end
function Shared.IsRostered(Id: string?): boolean return Id ~= nil and Config.ById[Id] ~= nil end
function Shared.Rng(Id: string): Random return Random.new(NpcBuilds.Seed(`Roster|{Id}`)) end
function Shared.Bind(Id: string, S) Bodies[Id] = S end
function Shared.Body(Id: string) return Bodies[Id] end

function Shared.SelfTestForTests()
	local Out = { Count = #Config.List; Bad = {} }
	local PerClique, PerSet, Seen = {}, {}, {}
	for _, E in Config.List do
		if Seen[E.Id] then table.insert(Out.Bad, `dup {E.Id}`) end
		Seen[E.Id] = true
		if not Cliques.Defs[E.Clique] then table.insert(Out.Bad, `clique {E.Id}`) end
		if not table.find(Config.Tempers, E.Temper) then table.insert(Out.Bad, `temper {E.Id}`) end
		if not table.find(Config.Sets, E.Set) then table.insert(Out.Bad, `set {E.Id}`) end
		if typeof(E.Bravery) ~= `number` or E.Bravery < 0 or E.Bravery > 1 then table.insert(Out.Bad, `bravery {E.Id}`) end
		if (E.SkipChance ~= nil) ~= (E.Clique == `Delinquents`) then table.insert(Out.Bad, `skip {E.Id}`) end
		PerClique[E.Clique] = (PerClique[E.Clique] or 0) + 1
		PerSet[E.Set] = (PerSet[E.Set] or 0) + 1
	end
	Out.CliquesOf3 = true
	for Id in Cliques.Defs do if PerClique[Id] ~= 3 then Out.CliquesOf3 = false end end
	Out.SetsOf6 = PerSet.A == 6 and PerSet.B == 6 and PerSet.C == 6 and PerSet.D == 6
	local A, B = Shared.Rng(`OdetteMarsh`), Shared.Rng(`OdetteMarsh`)
	Out.SeedStable = A:NextInteger(1, 1e6) == B:NextInteger(1, 1e6)
	Out.SeedDiffers = Shared.Rng(`OdetteMarsh`):NextInteger(1, 1e6) ~= Shared.Rng(`SilasPenwright`):NextInteger(1, 1e6)
	return Out
end

return Shared
```

- [x] **Step 4: Snapshot and restore the relationships too.**
  - **`snapshot.lua`:** the JSON gains `Relationships = (Prof.Social and Prof.Social.Relationships) or {}`.
  - **`restore.py`:** after `Prof.Quests = Snap.Quests`, add:

```lua
	Prof.Social = Prof.Social or {}
	Prof.Social.Relationships = Snap.Relationships or {}
	require(SSS.Social.Reputation).Sync(P)
```

- [x] **Step 5: Install and run the test.**
  - Stop Play, then run `install.py` on `ReplicatedStorage.Config.Students.luau`,
    `ServerScriptService.Services.Social.Roster.luau` and the TestBridge file.
  - Start Play (`start_play.lua`), then run `bridge.py RosterTest '$P'`.
  - Expected: `Count 24`, `Bad []`, `CliquesOf3 true`, `SetsOf6 true`, `SeedStable true`, `SeedDiffers true`.
  - Take a fresh `_slot2.json` with the new `snapshot.lua` (`client.py` is for the client; use rbxc's `Server` with
    `@snapshot.lua`, as `restore.py` does), and keep it for the whole release.

- [x] **Step 6: Commit**

```bash
git add tools/phase4-2270 docs/superpowers/plans/2026-11-18-roster-and-memory.md
git -c user.name=Rello commit -m "2.27 (1/7): Config.Students roster and the Roster service"
```

---

### Task 2: Schedules makes the roster's bodies

**Files:**
- Modify: `ServerScriptService.Services.Features.Schedules.luau` (`COUNT`, `Local.Look`, `Shared.OnStart`, `Local.Spawn`, `Shared.Debug`)
- Modify: TestBridge (add `Rostered`)

**Interfaces:**
- Consumes: `Roster.All()`, `Roster.Rng(Id)`, `Roster.Bind(Id, S)` (Task 1)
- Produces: each student record `S` gains `S.RosterId`, `S.Name`, `S.First`, `S.Temper`. Each model gets attributes
  `NHStudentId = Id` and `Clique`. `Shared.LookForTests(Id) -> Look` builds a look without spawning.

- [x] **Step 1: Write the failing test.** Add to TestBridge:

```lua
-- (2.27) the roster's bodies: ids on the live students, and a look that is the same when built twice
function Commands.Rostered(PlayerName: string)
	local Sched = require(game:GetService(`ServerScriptService`).Services.Features.Schedules)
	local Ids, Seen = {}, {}
	for _, R in Sched.Debug() do if R.RosterId and not Seen[R.RosterId] then Seen[R.RosterId] = true table.insert(Ids, R.RosterId) end end
	local A, B = Sched.LookForTests(`MaeGorse`), Sched.LookForTests(`MaeGorse`)
	return { Students = #Sched.Debug(); Ids = #Ids;
		SameLook = A.Uniform == B.Uniform and A.Skin == B.Skin and A.HairId == B.HairId and A.Bottoms == B.Bottoms }
end
```

Run `bridge.py Rostered '$P'`. Expected: an error ("LookForTests" is nil).

- [x] **Step 2: Back up `Schedules`** into `NH_Backup.Phase4_pre_20261118`. Then make `Local.Look` take a seeded `Random`.
  Every `math.random(a, b)` inside it becomes `Rng:NextInteger(a, b)`:

```lua
function Local.Look(Rng: Random): any -- (2.27) seeded per roster student: the same look every server
	local Appearance = require(ReplicatedStorage.UI.Appearance)
	local Look = Appearance.Sanitize(nil)
	Look.UseAvatar = false
	Look.Skin = Rng:NextInteger(1, #Appearance.Skins)
	Look.HairColor = Rng:NextInteger(1, #Appearance.HairColors)
	Look.Body = Rng:NextInteger(1, 2)
	Look.Uniform = Appearance.RandomPiece(Appearance.Uniforms, Look, Rng)
	Look.Bottoms = Appearance.RandomPiece(Appearance.BottomsList, Look, Rng)
	Look.EyeSet = if Appearance.IsFemale(Look) then 2 else 1
	Look.Eyes = Rng:NextInteger(1, #Appearance.Eyes)
	local Cat = ReplicatedStorage:FindFirstChild(`NHHairCatalog`)
	if Cat then
		local Pool = {}
		for _, H in Cat:GetChildren() do
			if H:GetAttribute(`Group`) == (if Appearance.IsFemale(Look) then `Female` else `Male`) then table.insert(Pool, H:GetAttribute(`AssetId`)) end
		end
		table.sort(Pool, function(X, Y) return tostring(X) < tostring(Y) end) -- (2.27) child order isn't stable
		if #Pool > 0 then Look.HairId = Pool[Rng:NextInteger(1, #Pool)] end
	end
	Look.Created = true
	return Look
end
```

- **Check before writing:** `Appearance.RandomPiece`'s signature (`ReplicatedStorage.UI.Appearance`). If it has no
  random-source argument, don't edit Appearance: copy its logic into a `Local.PieceFor(List, Look, Rng)` helper in
  Schedules.
- **If `IsFemale` depends on `Body`:** it's set before `Uniform` here, as before.

- [x] **Step 3: Build students from the roster.** In `Shared.OnStart`, replace `for I = 1, COUNT do … end` with a
  loop over `Roster.All()`. Delete `local COUNT = 14`, and make the clique-look picks use `Rng`:

```lua
	local Roster = require(ServerScriptService.Services.Social.Roster) -- (2.27)
	for I, E in Roster.All() do
		local Rng = Roster.Rng(E.Id)
		local Ok, Look = pcall(Local.Look, Rng)
		local Clique = E.Clique
		local AppearanceMod = require(ReplicatedStorage.UI.Appearance)
		if Ok and Look then
			local L = CliqueConfig.Defs[Clique] and CliqueConfig.Defs[Clique].Look
			if L then
				local Female = AppearanceMod.IsFemale(Look)
				local Tops = table.clone(L.Tops or {})
				if Female then for _, T in L.FemaleTops or {} do table.insert(Tops, T) end end
				local Bottoms = if Female and L.FemaleBottoms then L.FemaleBottoms else L.Bottoms
				if #Tops > 0 then Look.Uniform = AppearanceMod.IndexOf(AppearanceMod.Uniforms, Tops[Rng:NextInteger(1, #Tops)]) or Look.Uniform end
				if Bottoms and #Bottoms > 0 then Look.Bottoms = AppearanceMod.IndexOf(AppearanceMod.BottomsList, Bottoms[Rng:NextInteger(1, #Bottoms)]) or Look.Bottoms end
			end
		end
		local Female = Ok and Look and AppearanceMod.IsFemale(Look) or false
		local Build = NpcBuilds.Roll(`Roster|{E.Id}`, Clique, Female)
		Build.Bravery = E.Bravery -- (2.27) the roster's bravery wins over the roll
		if Ok and Look then Look.Body = NpcBuilds.BodyFor(AppearanceMod, Female, Build) or Look.Body end
		local S = { Index = I; RosterId = E.Id; Name = E.Name; First = E.First; Temper = E.Temper;
			Look = if Ok then Look else nil; Club = CLUBS[(I - 1) % #CLUBS + 1]; Clique = Clique; Build = Build;
			Bravery = Build.Bravery; Social = Build.Social; Speed = Build.Speed;
			VoiceSet = if Female then `Girl` else `Boy`;
			Voice = 0.92 + Rng:NextNumber() * 0.16;
		}
		Students[I] = S
		Roster.Bind(E.Id, S)
	end
```

- **The Athletes' club:** keep `Club = CLUBS[...]`. It only matters for Athletes, as before.
- **`IN_CLASS` stays 6:** per-set seating is 2.28.

- [x] **Step 4: Tag the models, and add the test hooks.**
  - **`Local.Spawn`:** after `M:SetAttribute(\`NHScheduled\`, S.Index)`, add
    `if S.RosterId then M:SetAttribute(\`NHStudentId\`, S.RosterId) end -- (2.27)`.
  - **`Shared.Debug`:** each row gains `RosterId = S.RosterId`.
  - **Add** this test hook:

```lua
function Shared.LookForTests(Id: string)
	return Local.Look(require(ServerScriptService.Services.Social.Roster).Rng(Id))
end
```

  - **Update the header comment:** "Fourteen background students" becomes "The roster's 24 students
    (Config.Students, 2.27)".

- [x] **Step 5: Install and run the test.**
  - Install `Schedules` and the TestBridge, start Play, and run `bridge.py Rostered '$P'`.
  - Expected: `Students 24`, `Ids 24`, `SameLook true`.
  - **Then the live check:** `SetTime "07:40"`, so students arrive. Count the models in `workspace.NHSchedule` that
    have `NHStudentId` (Server `execute_luau`). Expect up to 24 as they spawn, and no `[Schedules]` warnings in the
    console.
  - **Stop and start Play,** then check that one id's `NHBuild` attribute and shirt are the same as before.

- [x] **Step 6: Performance check.** With all 24 spawned (`SetTime "12:10"`, lunch), read the Studio `Stats` (server
  heartbeat, client FPS) for 20 s.
  - **Expected:** a client frame rate of 55 or more, and server heartbeat of 55 or more.
  - **If it's lower:** stop and report. Don't trim behaviour in this task.

- [x] **Step 7: Commit** `2.27 (2/7): Schedules makes the roster's 24 bodies, seeded looks`.

---

### Task 3: Saved relationships for the roster and the cast

**Files:**
- Modify: `ServerScriptService.Services.Social.Reputation.luau`, `ReplicatedStorage.Config.Reputation.luau`
  (`SavedCap = 64`)
- Modify: TestBridge (add `RelationshipCapTest`)

**Interfaces:**
- Consumes: `Roster.Get(Id)`, `Roster.IsRostered(Id)` (Task 1), `Config.Npcs` (the named cast)
- Produces:
  - `Reputation.Entry(Player, Id) -> { Value: number, Met: boolean, Last: number, Flags: {[string]: number} }?`
    (a copy)
  - `Reputation.ChangeRelationship(Player, Id, Amount, Reason?, Flag?)`: `Flag` is one of `Fought`, `Helped`,
    `Pranked`, `Lied`
  - `Reputation.Meet(Player, Id)`: for a rostered student, this is the introduction
  - `Reputation.Relationship(Player, Id)`: unchanged signature. A rostered student who isn't `Met` returns state
    `Unknown`.
  - `Reputation.StateOf(Value) -> string` (the state ignoring `Met`)
  - `Reputation.TrimForTests(Rels, Cap, Now) -> { droppedIds }`

- [x] **Step 1: Write the failing test.** Add to TestBridge:

```lua
-- (2.27) the 64-entry cap's drop order, on a stand-in table (nothing saved)
function Commands.RelationshipCapTest(PlayerName: string)
	local Rep = Social()
	local Rels = {}
	-- 60 old Acquaintance students, 3 Friendly, Ezra (important), 1 Hostile: 65 entries, cap 64
	for I = 1, 60 do Rels[`Ac{I}`] = { Value = 0; Met = true; Last = 1000 + I; Flags = {} } end
	for I = 1, 3 do Rels[`Fr{I}`] = { Value = 30; Met = true; Last = 10 + I; Flags = {} } end
	Rels.Ezra = { Value = 0; Met = true; Last = 1; Flags = {} }
	Rels.Ho1 = { Value = -80; Met = true; Last = 2; Flags = {} }
	local Dropped = Rep.TrimForTests(Rels, 64, 5000)
	local Count = 0 for _ in Rels do Count += 1 end
	-- all Acquaintance: the next drop is the oldest non-Trusted, non-Hostile, non-important entry
	local Rels2 = {}
	for I = 1, 63 do Rels2[`Fr{I}`] = { Value = 30; Met = true; Last = 100 + I; Flags = {} } end
	Rels2.Tr = { Value = 90; Met = true; Last = 1; Flags = {} }
	Rels2.Ho = { Value = -90; Met = true; Last = 2; Flags = {} }
	local Dropped2 = Rep.TrimForTests(Rels2, 64, 5000)
	return { Dropped = Dropped; Count = Count; EzraKept = Rels.Ezra ~= nil; HostileKept = Rels.Ho1 ~= nil;
		Dropped2 = Dropped2; TrustedKept = Rels2.Tr ~= nil; HostileKept2 = Rels2.Ho ~= nil }
end
```

Expected before the change: an error (`TrimForTests` is nil).

- [x] **Step 2: Back up `Reputation` and `Config.Reputation`.** Add `SavedCap = 64;` to `Config.Reputation`, under
  `AttackPenalty`. Then replace `Local.Record`, `Shared.Relationship`, `Shared.Meet` and `Shared.ChangeRelationship`
  in `Reputation`, and add the new functions:

```lua
local Roster = require(ServerScriptService.Services.Social.Roster) -- (2.27)
local Cast = require(ReplicatedStorage.Config.Npcs) -- (2.27) the named cast keeps a saved relationship too

-- (2.27) who keeps a saved relationship: the important NPCs (Config.Reputation.Npcs), the named cast (Config.Npcs)
-- and the roster (Config.Students)
function Local.Saved(Id: string): boolean
	return Config.Npcs[Id] ~= nil or Cast[Id] ~= nil or Roster.IsRostered(Id)
end
function Local.NameOf(Id: string): string
	local E = Config.Npcs[Id] or Cast[Id] or Roster.Get(Id)
	return E and E.Name or Id
end
function Shared.StateOf(Value: number): string return Local.StateFor(Value, true) end

-- (2.27) the 64 cap (doc 13 §2.3): drop the oldest Acquaintance first, then the oldest of any state but Trusted and
-- Hostile. Important NPCs (Config.Reputation.Npcs) are never dropped.
function Local.Trim(Rels, Cap: number): { string }
	local Dropped = {}
	local function count() local N = 0 for _ in Rels do N += 1 end return N end
	while count() > Cap do
		local Pick, PickLast, PickPass = nil, math.huge, 3
		for Id, R in Rels do
			if not Config.Npcs[Id] and typeof(R) == `table` then
				local State = Local.StateFor(R.Value or 0, true)
				local Pass = if State == `Acquaintance` then 1 elseif State ~= `Trusted` and State ~= `Hostile` then 2 else 3
				local Last = R.Last or 0
				if Pass < PickPass or (Pass == PickPass and Last < PickLast) then Pick, PickLast, PickPass = Id, Last, Pass end
			end
		end
		if not Pick or PickPass == 3 then break end -- only Trusted, Hostile and important entries left
		Rels[Pick] = nil
		table.insert(Dropped, Pick)
	end
	return Dropped
end
function Shared.TrimForTests(Rels, Cap: number, _Now: number) return Local.Trim(Rels, Cap) end

function Local.Record(Player: Player, NpcId: string)
	local Social = Shared.Get(Player)
	if not Social or not Local.Saved(NpcId) then return nil end
	local Record = Social.Relationships[NpcId]
	if typeof(Record) ~= `table` then
		Record = { Value = 0; Met = false; Last = os.time(); Flags = {} }
		Social.Relationships[NpcId] = Record
		Local.Trim(Social.Relationships, Config.SavedCap or 64)
	end
	-- (2.27) older entries (Ezra, Vesper) gain the new fields
	Record.Last = Record.Last or os.time()
	if typeof(Record.Flags) ~= `table` then Record.Flags = {} end
	return Record
end

function Shared.Entry(Player: Player, NpcId: string)
	local Social = Shared.Get(Player)
	local R = Social and Social.Relationships[NpcId]
	if typeof(R) ~= `table` then return { Value = 0; Met = false; Last = 0; Flags = {} } end
	return { Value = R.Value or 0; Met = R.Met == true; Last = R.Last or 0; Flags = table.clone(R.Flags or {}) }
end

function Shared.Relationship(Player: Player, NpcId: string): (number, string, boolean)
	local E = Shared.Entry(Player, NpcId)
	return E.Value, Local.StateFor(E.Value, E.Met), E.Met
end

function Shared.Meet(Player: Player, NpcId: string)
	local Record = Local.Record(Player, NpcId)
	if not Record or Record.Met then return end
	Record.Met = true
	Record.Last = os.time()
	Shared.Sync(Player)
	Shared.RelationshipChanged:Fire(Player, NpcId, Local.StateFor(Record.Value, true), `Unknown`)
end

local FLAGS = { Fought = true; Helped = true; Pranked = true; Lied = true }
function Shared.ChangeRelationship(Player: Player, NpcId: string, Amount: number, Reason: string?, Flag: string?)
	local Record = Local.Record(Player, NpcId)
	if not Record or (Amount == 0 and not Flag) then return end
	local Rostered = Roster.IsRostered(NpcId)
	local OldState = Local.StateFor(Record.Value, Record.Met)
	if not Rostered then Record.Met = true end -- (2.27) a rostered student is Met only by their introduction
	Record.Value = math.clamp(Record.Value + Amount, -100, 100)
	Record.Last = os.time()
	if Flag and FLAGS[Flag] then Record.Flags[Flag] = (Record.Flags[Flag] or 0) + 1 end
	local NewState = Local.StateFor(Record.Value, Record.Met)
	Shared.Sync(Player)
	if NewState ~= OldState then
		if Record.Met then -- (2.27) no name in a notification before you've learned it
			Notifications.Notify(Player, {
				Title = `{Local.NameOf(NpcId)}: {NewState}`;
				Text = Reason;
				Kind = if Amount > 0 then `Good` else `Bad`;
				Duration = 4;
			})
		end
		Shared.RelationshipChanged:Fire(Player, NpcId, NewState, OldState)
	end
end
```

- **Keep the old call sites working:** Factions, Dialogue, Npcs, Quests and FactionsPanel read `Value` and `Met`,
  which are unchanged. Update the header's API lines with `Entry`, `StateOf` and the `Flag` argument.
- **`Cast` path check:** `ReplicatedStorage.Config.Npcs` must be a plain table keyed by id (Ezra, Hale, Custodian…).
  If `require` returns something else, read its structure and adapt `Local.Saved` and `Local.NameOf`. Don't edit
  `Config.Npcs`.

- [x] **Step 3: Install and run the test.**
  - Install `Reputation`, `Config.Reputation` and the TestBridge, start Play, and run
    `bridge.py RelationshipCapTest '$P'`.
  - Expected: `Dropped ["Ac1"]` (the oldest Acquaintance), `Count 64`, `EzraKept true`, `HostileKept true`,
    `Dropped2 ["Fr1"]`, `TrustedKept true`, `HostileKept2 true`.

- [x] **Step 4: Regression on the real data.**
  - Run `bridge.py Relationship '$P' '"Ezra"'`. Expected: the same `[Value, State, Met]` as before (Ezra wasn't
    touched).
  - Run `bridge.py Relationship '$P' '"OdetteMarsh"' 5`, then the same command with no change. Expected:
    `[5, "Unknown", false]`, with no notification, because she isn't met yet.
  - **Restore slot 2.**

- [x] **Step 5: Commit** `2.27 (3/7): saved relationships for the roster and cast; the 64 cap`.

---

### Task 4: Students remember you, and introduce themselves

**Files:**
- Modify: `ServerScriptService.Services.AI.StudentBrain.luau` (`memo`, `greeting`, `greet`, `NudgeMod.OnShove`,
  `Brain.Fed`, plus a test hook)
- Modify: `ServerScriptService.Services.AI.StudentBrain.Talk.luau` (`Attitude`)
- Modify: `ServerScriptService.Services.AI.StudentBrain.Lines.luau` (`Intro`, `Greet.Grudge`, `Greet.Grateful`)
- Modify: TestBridge (add `MemoryTest`)

**Interfaces:**
- Consumes: `S.RosterId`, `S.First`, `S.Temper` (Task 2); `Reputation.Entry`, `ChangeRelationship(..., Flag)`,
  `Meet` and `StateOf` (Task 3)
- Produces:
  - `Brain.GreetingForTests(S, Player) -> (Moment?, Pool)`. Moment `Intro` means the introduction.
  - The rules:
    - **Shove:** -12 and `Fought`, at most once per 30 s per student and player.
    - **Snack:** `Loved` +8 and `Liked` +5, both with `Helped`, at most once per 10 minutes per student and player.
      `Refuse` changes nothing.
    - **Introduction:** the first greeting when the saved entry isn't `Met` and its value is at least -19.
    - **Grudge pool:** `Flags.Fought >= 1` and value below 0.
    - **Grateful pool:** `Flags.Helped >= 2` and value at least 10.

- [x] **Step 1: Write the failing test.** Add to TestBridge:

```lua
-- (2.27) greetings from the saved memory, on a stand-in student; slot 2's entry for her is put back after
function Commands.MemoryTest(PlayerName: string)
	local SSS = game:GetService(`ServerScriptService`).Services
	local Player = Players:FindFirstChild(PlayerName)
	local Rep, Brain = require(SSS.Social.Reputation), require(SSS.AI.StudentBrain)
	local Id = `OdetteMarsh`
	local Rels = Rep.Get(Player).Relationships
	local Saved = Rels[Id] and table.clone(Rels[Id])
	Rels[Id] = nil
	local S = { Index = 999; RosterId = Id; First = `Odette`; Temper = `Warm`; Clique = `Choir`; Memory = {} }
	local Out = {}
	Out.Fresh = (Brain.GreetingForTests(S, Player))                        -- expect Intro
	Rep.Meet(Player, Id)
	Out.AfterMeet = (Brain.GreetingForTests(S, Player)) ~= `Intro`          -- expect true
	Rep.ChangeRelationship(Player, Id, 12, nil, `Helped`)
	Rep.ChangeRelationship(Player, Id, 12, nil, `Helped`)
	local _, PoolG = Brain.GreetingForTests(S, Player)
	Out.Grateful = PoolG == require(SSS.AI.StudentBrain.Lines).Greet.Grateful.Warm
	Rep.ChangeRelationship(Player, Id, -40, nil, `Fought`)
	local _, PoolF = Brain.GreetingForTests(S, Player)
	Out.Grudge = PoolF == require(SSS.AI.StudentBrain.Lines).Greet.Grudge.Warm
	Rels[Id] = nil
	Rep.ChangeRelationship(Player, Id, -25, nil, `Fought`)                -- a fight before any introduction
	Out.NoIntroAfterFight = (Brain.GreetingForTests(S, Player)) ~= `Intro` -- expect true
	Out.Attitude = require(SSS.AI.StudentBrain.Talk).Attitude(S, Player)   -- Rival: at most Wary
	Rels[Id] = Saved
	Rep.Sync(Player)
	return Out
end
```

Expected before the change: an error (`GreetingForTests` is nil).

- [x] **Step 2: Back up the three files.** Add the line pools to `Lines`: `Intro` is a new top-level table, and
  `Grudge` and `Grateful` go inside `Lines.Greet`. `{First}` is the student's own first name:

```lua
-- (2.27) a rostered student's first greeting: they tell you their name
Lines.Intro = {
	Warm = { `I'm {First}, by the way. Nice to finally meet you.`, `Oh! I'm {First}. Hi.` };
	Cool = { `{First}. Since you're asking.`, `Name's {First}.` };
	Sharp = { `{First}. Remember it.`, `I'm {First}. You'll want to know that.` };
	Shy = { `Um... I'm {First}.`, `I'm {First}... hi.` };
	Wild = { `{First}! That's me. Who are you?`, `Call me {First}. Everyone does.` };
}
```

Inside `Lines.Greet`:

```lua
	-- (2.27) they remember a shove and haven't forgiven it
	Grudge = {
		Warm = { `Oh. You again.`, `I haven't forgotten, you know.` };
		Cool = { `You again.`, `Keep walking.` };
		Sharp = { `Look who's back. Try it again.`, `You owe me an apology.` };
		Shy = { `P-please don't...`, `...not you again.` };
		Wild = { `Round two? Bring it.`, `Oh, it's YOU.` };
	};
	-- (2.27) you've been good to them more than once
	Grateful = {
		Warm = { `Thanks for last time!`, `There you are! You're the best.` };
		Cool = { `Hey. Thanks for before.`, `Good to see you.` };
		Sharp = { `You again. ...Thanks, I guess.`, `I owe you one. Don't make it weird.` };
		Shy = { `Thank you... for before.`, `Hi! I was hoping I'd see you.` };
		Wild = { `My favourite person!`, `Hey hey! It's my friend!` };
	};
```

- [x] **Step 3: Read the saved memory in `StudentBrain`.** Near the other lazy requires, add:

```lua
local function Rep() return require(ServerScriptService.Services.Social.Reputation) end -- (2.27) lazy: no cycle at load
```

In `greeting(S, Rec)`, right after `local G = Lines.Greet` (the check uses `G`), insert:

```lua
	if S.RosterId and Pl then -- (2.27) the saved memory comes first after a fresh fight
		local E = Rep().Entry(Pl, S.RosterId)
		local T = S.Temper or `Warm`
		if os.clock() - (M.Fought or -1e9) >= 300 then
			if not E.Met and E.Value >= -19 then return `Intro`, nil, Lines.Intro[T] or Lines.Intro.Warm end
			if (E.Flags.Fought or 0) >= 1 and E.Value < 0 then return nil, nil, G.Grudge[T] or G.Grudge.Warm end
			if (E.Flags.Helped or 0) >= 2 and E.Value >= 10 then return nil, nil, G.Grateful[T] or G.Grateful.Warm end
		end
	end
```

In `greet(S, Rec)`, replace the `local Said = …` line with:

```lua
	local Said
	if Moment == `Intro` then -- (2.27) they say their name, and you've met
		local Line = Pool[math.random(1, #Pool)]
		sayText(S, (string.gsub(Line, `{First}`, S.First or `me`)))
		Said = true
		pcall(function() Rep().Meet(Pl, S.RosterId) end)
	else
		Said = if Moment then sayMatrix(S, Moment, Pl, Opts, 6, Pool) else say(S, Pool, 6)
	end
```

- **Check `sayText`:** confirm its signature (`sayText(S, Text)`, near line 88). If it has a cooldown or guard, keep
  it.
- **Check the plain pools:** `say(S, Pool, 6)` already handles the Grudge and Grateful pools.

- [x] **Step 4: Record shoves and snacks.** In `NudgeMod.OnShove`, before `sayMatrix`, add:

```lua
	local Pl = Rec and Rec.Player
	if S.RosterId and Pl then -- (2.27) a shove is remembered: -12 and Fought, once per 30 s
		local M = memo(S, Pl)
		if os.clock() - (M.ShoveSaved or -1e9) >= 30 then
			M.ShoveSaved = os.clock()
			pcall(function() Rep().ChangeRelationship(Pl, S.RosterId, -12, nil, `Fought`) end)
		end
	end
```

In `Brain.Fed`, before `return Verdict, S.Clique`, add:

```lua
	if S.RosterId and Verdict ~= `Refuse` then -- (2.27) a snack they took is remembered, once per 10 minutes
		local M = memo(S, Pl)
		if os.clock() - (M.FedSaved or -1e9) >= 600 then
			M.FedSaved = os.clock()
			pcall(function() Rep().ChangeRelationship(Pl, S.RosterId, if Verdict == `Loved` then 8 else 5, nil, `Helped`) end)
		end
	end
```

Then add the test hook, beside `Brain.Fed`:

```lua
function Brain.GreetingForTests(S, Pl: Player)
	local Moment, _, Pool = greeting(S, { Player = Pl })
	return Moment, Pool
end
```

- [x] **Step 5: `Talk.Attitude` reads the saved state.** In `Talk.Attitude`, after the membership line (`if S.Clique
  and Talk.IsMember…`), insert:

```lua
	if S.RosterId then -- (2.27) how this student feels about you, saved: Hostile/Rival cap it, Friendly/Trusted floor it
		local Ok, E = pcall(function()
			return require(ServerScriptService.Services.Social.Reputation).Entry(Player, S.RosterId)
		end)
		if Ok and E then
			local State = require(ServerScriptService.Services.Social.Reputation).StateOf(E.Value)
			if State == `Hostile` then R = math.min(R, Rank.Hostile)
			elseif State == `Rival` then R = math.min(R, Rank.Wary)
			elseif State == `Friendly` then R = math.max(R, Rank.Friendly)
			elseif State == `Trusted` then R = math.max(R, Rank.Respected) end
		end
	end
```

- [x] **Step 6: Install and run the tests.**
  - Install `StudentBrain`, `StudentBrain.Talk`, `StudentBrain.Lines` and the TestBridge. `StudentBrain`'s
    children (`Talk`, `Lines`, …) are kept by `install.py`; install the parent first, then the children.
  - Start Play, run `bridge.py MemoryTest '$P'`, then restore slot 2.
  - Expected: `Fresh "Intro"`, `AfterMeet true`, `Grateful true`, `Grudge true`, `NoIntroAfterFight true`, and
    `Attitude` is `"Wary"` or `"Hostile"`.

- [x] **Step 7: The live rejoin check (the 2.27 acceptance).**
  1. `SetTime "12:10"`. Walk up to a rostered student with `GoTo` to their root. They introduce themselves: the line
     has their first name, and `bridge.py Relationship '$P' '"<Id>"'` shows `Met true`.
  2. Shove them twice, 31 s apart (the TestBridge `Shove` command if there is one; otherwise ask the owner to press
     the shove key). Expected `Value -24` and `Fought 2`.
  3. Stop Play, then start Play again (Studio saves slot 2 to the test DataStore). Walk up to the same student:
     the line comes from `Greet.Grudge[<their Temper>]`.
  4. Give a second student two snacks they accept, 10 minutes apart (wait out the 600 s, or clear `memo`'s
     `FedSaved` from a Server `execute_luau`). Feed through `Brain.Fed(Player, Model, Item)` with a real item from
     `Items.CliqueFood[<their clique>]`. After the second (value 10 or more), their greeting comes from
     `Greet.Grateful[<their Temper>]`.
  5. Restore slot 2.

- [x] **Step 8: Commit** `2.27 (4/7): students remember you; introductions, grudges and thanks`.

---

### Task 5: Classmates in the Students list

**Files:**
- Modify: `StarterPlayer.StarterPlayerScripts.Controllers.Gui.Students.luau`

**Interfaces:**
- Consumes: the client profile's `Social.Relationships` (sent by `Reputation.Sync` as `SetSocial`), and
  `Config.Students.ById`
- Produces: a `Classmates` group under the player groups: each met student's name, with a second line
  `<Clique name> · <State>`, then the start of their `Bio`

- [x] **Step 1: Write the failing check.**
  - From a Client `execute_luau`, open the list: `require(PlayerScripts.Controllers.Gui.Students).Toggle(true)`.
  - Count the children of `PlayerGui.NHStudents.Plate.List` named `Group_Classmates`.
  - Expected now: 0, after meeting a student in Task 4. Snapshot first, then use
    `bridge.py Relationship '$P' '"OdetteMarsh"' 1` and a Server `Reputation.Meet` call.

- [x] **Step 2: Back up the list.** Add the requires and the group:

```lua
local StudentsConfig = require(ReplicatedStorage.Config.Students) -- (2.27) the roster
local CliqueConfig = require(ReplicatedStorage.Config.Cliques)
local RepConfig = require(ReplicatedStorage.Config.Reputation)
local StateController = require(script.Parent.Parent.StateController)

-- (2.27) the rostered students you've met, from your saved relationships
function Local.Classmates(Order: number): number
	local Profile = StateController.GetProfile(false)
	local Rels = Profile and Profile.Social and Profile.Social.Relationships
	if typeof(Rels) ~= `table` then return 0 end
	local Rows = {}
	for Id, R in Rels do
		local E = StudentsConfig.ById[Id]
		if E and typeof(R) == `table` and R.Met then
			local State = `Acquaintance`
			for _, St in RepConfig.RelationshipStates do if (R.Value or 0) <= St.Max then State = St.Name break end end
			local Clique = CliqueConfig.Defs[E.Clique]
			table.insert(Rows, { Name = E.Name; Sub = `{Clique and Clique.Name or E.Clique}  ·  {State}  ·  {E.Bio}` })
		end
	end
	if #Rows == 0 then return 0 end
	table.sort(Rows, function(A, B) return A.Name < B.Name end)
	local Header = new(`Frame`, { Name = `Group_Classmates`; BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 22); LayoutOrder = Order }, Ui.List)
	new(`TextLabel`, {
		BackgroundTransparency = 1; Font = Theme.Fonts.Title; TextSize = 15; TextXAlignment = Enum.TextXAlignment.Left;
		TextColor3 = C.TextDim; Text = `CLASSMATES`; Position = UDim2.fromOffset(4, 4); Size = UDim2.new(1, -40, 1, -4);
	}, Header)
	new(`TextLabel`, {
		BackgroundTransparency = 1; Font = Theme.Fonts.Body; TextSize = 14; TextXAlignment = Enum.TextXAlignment.Right;
		TextColor3 = C.TextFaint; Text = tostring(#Rows); Position = UDim2.fromOffset(0, 4); Size = UDim2.new(1, -4, 1, -4);
	}, Header)
	for I, M in Rows do
		local Row = new(`Frame`, { Name = `Classmate`; BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 48); LayoutOrder = Order + I }, Ui.List)
		Kit.PlayerListRow({ name = M.Name; Size = UDim2.new(1, 0, 0, 30); Parent = Row })
		new(`TextLabel`, {
			BackgroundTransparency = 1; Font = Theme.Fonts.Body; TextSize = 14; TextColor3 = C.TextDim;
			TextXAlignment = Enum.TextXAlignment.Right; Text = M.Sub; TextTruncate = Enum.TextTruncate.AtEnd;
			Position = UDim2.fromOffset(0, 30); Size = UDim2.new(1, -12, 0, 17);
		}, Row)
	end
	return #Rows + 1
end
```

- **Call it:** in `Local.Render`, after the `for _, G in GROUPS do … end` loop, call
  `Local.Classmates(Order + 1000)` before the size and count update.
- **Fit it:** the plate's height is set from the list. Check how `Render` sets it after the loop, and make sure the
  Classmates rows are counted. If the height comes from `Layout.AbsoluteContentSize`, nothing is needed.
- **Refresh it:** in the start-up function, add
  `StateController.ProfileUpdated:Connect(function(_, A) if A and A.type == \`SetSocial\` then Dirty = true if Open then Local.Render() end end end)`.
  Use the module's existing names for the open flag and `Dirty`.
- **Header comment:** add one line about the Classmates group (2.27).

- [x] **Step 3: Install and check.**
  - Install the list, start Play, meet one student (Step 1's calls), and open the list.
  - Expected: one `Group_Classmates` with one `Classmate` row, named "Odette Marsh", and a second line starting
    "The Chapel Choir · Acquaintance".
  - **Screenshot it** (`screen_capture`) to `tools/phase4-2270/review/classmates.jpg`.
  - Restore slot 2.

- [x] **Step 4: Commit** `2.27 (5/7): Classmates in the Students list`.

---

### Task 6: Regression

**Files:** none changed (fixes go back to the task that owns the file).

- [x] **Step 1: The self-tests in one Play session.**
  - **This release:** `RosterTest`, `RelationshipCapTest`, `MemoryTest`, `Rostered`.
  - **Earlier releases:** `CineJudgeTest` (36/36), `CineGraphTest` (9/9), `CineQteTest`, `CineVoteTest`,
    `Phase1SelfTest` and `AfterHoursMigrateTest` (1, 2, 5).
  - **Expected:** this release's values as in Tasks 1 to 4, and the 2.26.0 values for the others. `AfterLeaveEnded`,
    `OldSlotCanStart` and `NewKidBeforeOrientation` read false by design.
- [x] **Step 2: The NPCs that already used relationships.**
  - Run `bridge.py Relationship '$P' '"Ezra"'` and the `Talk` command with Ezra. Expected: his greeting state
    matches his saved value.
  - Open the Factions panel. The leader's relationship line still shows.
- [x] **Step 3: The school day.** At `SetTime` 07:40, 09:10 (class), 12:10 (lunch) and 15:30 (after school),
  students arrive, sit six to a class, queue for lunch and go to clubs, as before. No `[Schedules]` or
  `[StudentBrain]` warnings.
- [x] **Step 4: The console.** No errors from Roster, Reputation, Schedules, StudentBrain, Talk or Students.
- [x] **Step 5: Saving.**
  - Run the rejoin check on slot 4 "Testy". Snapshot it with the same tools, using `ChooseSlot 4`, then restore it.
  - Check the size: `#HttpService:JSONEncode(Profile)` stays under 1 MB.
- [x] **Step 6: Restore slot 2,** then stop Play and run `save_place`.

---

### Task 7: Docs and release 2.27.0

- [x] **Step 1: CHANGELOG `[2.27.0] - <date>: Roster & memory`.**
  - **Contents:** the roster, Schedules, saved memory, introductions, the Classmates list, the TestBridge commands.
  - **Checked:** every number from Task 6.
  - **Not checked:** a two-player run, and phone screens.
  - If another session's hunk is in CHANGELOG, stage only this entry's hunk (`git diff -U0` → keep the `## [2.27.0]`
    hunk → `git apply --cached --unidiff-zero`).
- [x] **Step 2: The other docs.**
  - **README:** a Latest-update line.
  - **Implementation-Status:** a row.
  - **Discord:** a game update in `updates/discord/game-updates/<date>-roster-and-memory.md` ("The students have
    names now…", in player words), and an index line. No announcement; that waits for the end of Phase 2.
  - **Doc 13:** the status line says "2.27 shipped", and §9 gets this plan's spec deltas.
- [x] **Step 3: Vault.** Copy the CHANGELOG, the Discord post, Implementation-Status and doc 13, and add a home-note
  line.
- [x] **Step 4: Commit and merge.**
  - Commit `2.27.0: Roster & memory (24 named students who remember you)`, staging only this plan's files.
  - Merge `phase4-living-school` into `main` with `--no-ff` and a message file
    (`git merge -F <file>`; `-F -` doesn't work). Stash other sessions' working-tree changes around the merge, and pop
    them after.
  - Don't push unless the owner asks.

---

## Outcome (2026-11-18)

All seven tasks done; the numbers are in CHANGELOG `[2.27.0]`. Beyond the plan:
- **Shy students:** students with sociability under 0.5 never greet, so a `remembers()` check lets them speak up.
- **`harness/gamevm.py`:** checks of live state run inside the game, because the MCP's Luau has its own module copies.
- **The frame-rate bar:** 55 fps was above this machine's empty-school baseline (47), so the measure is the change
  with students against that baseline.

## Spec deltas (recorded in doc 13 §9 items 8 to 15)

1. **Field names stay `Value` and `Met`** (not `V`). The client's FactionsPanel and four services read them, so no
   migration is needed; `Last` and `Flags` are added.
2. **`Last` is `os.time()` (real time),** not the in-game day. The cap only needs an order, and "rejoin a day later"
   is real time.
3. **"Fight a rostered student" means a shove.** Players can't hit scheduled students (their parts aren't
   queryable), so a shove (Nudges) is the hostile act that's saved (-12, `Fought`). A snack they accept is the
   helpful one (+8 or +5, `Helped`) until 2.29's scenes add more.
4. **No nameplates:** students have none (`DisplayDistanceType None`). An unmet student stays unnamed everywhere: no
   notification, not in the list. Once met, they're in the Students list's Classmates group with their `Bio`.
5. **`Roster.Plan`, `WhereNow` and `Near` move to the plans that use them** (2.28 timetables, 2.29 witnesses). 2.27's
   Roster is identity only.
6. **The named cast** (`Config.Npcs`) keeps saved entries. `Config.Reputation.Npcs` is unchanged, because it also
   means "attacking them costs standing".

## Self-review

- **Spec coverage (doc 13 §2):**
  - §2.1 is Task 1.
  - §2.2: identity is Task 1, bodies are Task 2, and the movement part is 2.28 (delta 5).
  - §2.3 is Task 3.
  - §2.4 is Task 4.
  - §2.5 is Task 4 (the introduction) and Task 5 (the list).
  - §2.6: the acceptance is Task 4 Step 7 and Task 6.
  - §6's data budget is Task 6 Step 5. §7 is Task 6. §8 is Task 1.
- **Placeholders:** one, on purpose. Task 1 Step 2 shows 3 of 24 rows, and the rest are copied verbatim from doc 13
  §8, which is the single source.
- **Types:**
  - `Entry` (`Value`, `Met`, `Last`, `Flags`) is the same in Tasks 3, 4 and 5.
  - `S.RosterId`, `S.First` and `S.Temper` are set in Task 2 and read in Task 4.
  - `Lines.Intro[T]`, `Lines.Greet.Grudge[T]` and `Lines.Greet.Grateful[T]` are defined in Task 4 Step 2, and
    `MemoryTest` compares them by identity.
- **Known risks:**
  - `Appearance.RandomPiece` may not take a random source (Task 2 Step 2 says what to do).
  - Studio's rejoin may not reload slot 2 from the test DataStore. If it doesn't, check through `Data.GetProfile` after
    `ChooseSlot 2` again, and report.
