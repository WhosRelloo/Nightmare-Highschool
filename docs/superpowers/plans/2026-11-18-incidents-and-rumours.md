# Incidents & Rumours (2.29) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Things that happen in the school become incidents on one bus. Six small scenes play out where players can see
them. Incidents turn into rumours that students pass on and slightly mangle, and no rumour ever pins on a real player
something they didn't do.

**Architecture:**
- **The bus:** `World.Incidents` is a signal bus with `Emit`/`On`, and it fills in witnesses from `Roster.Near`. Eight
  existing systems emit into it: four already have signals, three get a one-line `Emit`, and the moon is read from its
  workspace attribute. The bus's consumers adjust saved relationships (2.27's flags).
- **Rumours:** `Social.Rumours` turns incidents into rumours. It spreads them through StudentBrain's pair chats when
  bodies are near a player, and off-screen otherwise, at most one hop per rumour every 5 minutes. It mutates details
  under a code-enforced safety rule, and voices them through chats and a Fortune card.
- **Scenes:** `World.Scenes` stages six data-driven scenes (`Config.Scenes`) with cast borrowed from Schedules
  (`Schedules.Borrow`/`Release`, which sets `S.InScene`; 2.28's sleep check already honours it).

**Tech Stack:** Roblox Luau in NH Combat Test (placeId 98950102230473), through the Studio MCP and the
`tools/phase4-2290/harness` helpers (`install.py`, `dump.py`, `bridge.py`, `gamevm.py`, `snapshot.lua`, `restore.py`,
`start_play.lua`, `_stand.lua`, `_far.lua`, `_byrooms.lua`), run with `python -X utf8 -I`.

**Spec:** `docs/expansion/13-Living-School.md` §4 (2.29), §7, and §9's deltas so far. This plan's deltas are at the end.

## Global Constraints

- Build only in **NH Combat Test**. The Map place is read-only.
- **Backup:** before the first edit of a script, copy it into `ServerStorage.NH_Backup.Phase4_pre_20261118`, named
  `<FullName> (2.28)` if an earlier copy exists.
- **Mirror:** `tools/phase4-2290/pre/` (dumped: CliqueFights, Matches, Beasts, Fortune, StudentBrain, Schedules,
  Roster, Reputation, TestBridge, Pranks), edit `live/`, and install with `harness/install.py`.
- **Tests:** TestBridge commands (`bridge.py`), and `gamevm.py` for live state. MCP `execute_luau` has its own module
  copies.
- **Test slot 2** only. Its baseline is `harness/_slot2.json` (the 2.27 snapshot). Restore after any test that saves
  state. A changed `Discipline.LastDecayDay` after clock jumps is expected.
- **The safety rule (spec §4.3), enforced in code:** a rumour about a real player carries only true facts. A player is
  never added as the subject of something they didn't do, never swapped out of their own deed, and no field holding a
  player ever mutates.
- **Art and UI:** existing assets only. ProximityPrompts follow `Social.Npcs`' pattern (`Config.Interaction` keys).
  The scene figure is the existing `ReplicatedStorage.NHCineCast.Strikethrough` template.
- **Code style:** `Shared`/`Local`, backtick strings, `-- (2.29)` on changed lines, no new per-frame server loop. The
  rumour spread runs on a 10 s timer, and the scene director on a 5 s timer.
- **Commits:** `git -c user.name=Rello`, with the Co-Authored-By and Claude-Session lines, on `phase4-living-school`.

---

## File structure

| File (`tools/phase4-2290/live/…`) | Responsibility | New / changed |
|---|---|---|
| `ServerScriptService.Services.World.Incidents.luau` | The bus: `Emit`, `On`, `Recent`; filling witnesses; the relationship consumer; listeners for the existing signals | new |
| `ServerScriptService.Services.Social.CliqueFights.luau`, `Sports.Matches.luau`, `Features.Beasts.luau` | One `Emit` line each | changed |
| `ServerScriptService.Services.Social.Roster.luau` | `Near(Pos, Radius) -> { Id }` | changed |
| `ServerScriptService.Services.Social.Reputation.luau` | `Learn(Player, Id)`: met without the +5 a greeting gives | changed |
| `ReplicatedStorage.Config.Rumours.luau` | Rumour templates by kind, size ladders, the region neighbour rule | new |
| `ServerScriptService.Services.Social.Rumours.luau` | Make, Hop (mutation with safety), Text, the spread timer, ForChat, Heard, RecentFor | new |
| `ServerScriptService.Services.AI.StudentBrain.luau` | `chat`: a student who knows a rumour shares it | changed |
| `ServerScriptService.Services.Features.Fortune.luau` | A `Whisper` hint (the Fool card) from a live rumour | changed |
| `ReplicatedStorage.Config.Scenes.luau` | The six scenes as data | new |
| `ServerScriptService.Services.World.Scenes.luau` | The director: choosing, casting, steps, hooks, outcome | new |
| `ServerScriptService.Services.Features.Schedules.luau` | `Borrow(Pos, Count, Filter)`, `Release(S)`, `HallSpotFor` | changed |
| `ServerScriptService.Services.Studio.TestBridge.luau` | `IncidentTest`, `RumourTest`, `RumourSafetyTest`, `SceneTest` | changed |

---

### Task 1: The incident bus and its emitters

**Files:**
- Create: `ServerScriptService.Services.World.Incidents.luau`
- Modify: `Social.CliqueFights` (`Local.EndScuffle`), `Sports.Matches` (`Match:End`), `Features.Beasts` (the `Sighted` branch), `Social.Roster` (`Near`), TestBridge

**Interfaces:**
- Produces:
  - `Incidents.Emit(I: { Kind: string, Where: Vector3?, Region: string?, Who: { {Id: string|Player, Role: string} }?, Witnesses: {string}?, Severity: number?, Truth: boolean? }) -> I`
    - It fills `I.T` (`os.time()`).
    - It fills `I.Region` from `Where`, using `workspace.Regions` boxes.
    - It fills `I.Witnesses` from `Roster.Near(Where, 40)` when not given.
    - `Truth` defaults to true.
  - `Incidents.On(Kind: string | "*", Fn: (I) -> ()) -> Connection`, `Incidents.Emitted` (signal), `Incidents.Recent(N) -> {I}` (the last 50).
  - `Incidents.RegionAt(Pos) -> string?` (shared by Rumours and Scenes).
  - `Roster.Near(Pos: Vector3, Radius: number) -> { string }`: rostered ids whose `WhereNow().At` is within the radius.
  - **Kinds and roles:**

    | Kind | Roles | Emitted by |
    |---|---|---|
    | `Scuffle` | `Doer` (winning clique id) | CliqueFights |
    | `Downed` | `Doer` (attacker), `Target` | Downed.OnDowned |
    | `Caught` | `Target` (the player) | HallMonitor.Caught, with `Reason` |
    | `Violation` | `Target` (the player) | Discipline.ViolationAdded, with `Type` |
    | `Prank` | `Doer` (the player) | Pranks.Marked |
    | `Match` | `Doer` (winning team name) | Matches |
    | `Beast` | `Doer` (the beast name) | Beasts (Sighted) |
    | `Moon` | (none) | the `NHMoonEvent` attribute |
    | `Scene` | per scene | World.Scenes (Task 4) |

- [ ] **Step 1: Write the failing test.** Add to TestBridge:

```lua
-- (2.29) the incident bus: Emit fills time, region and witnesses; On hears it; the relationship consumer applies flags
function Commands.IncidentTest(PlayerName: string)
	local SSS = game:GetService(`ServerScriptService`).Services
	local Player = Players:FindFirstChild(PlayerName)
	local Inc, Rep = require(SSS.World.Incidents), require(SSS.Social.Reputation)
	local Rels = Rep.Get(Player).Relationships
	local Saved = Rels.MaeGorse and table.clone(Rels.MaeGorse)
	local Heard = {}
	local C = Inc.On(`TestKind`, function(I) table.insert(Heard, I.Kind) end)
	local Hall = workspace.Regions:FindFirstChild(`MainHall`)
	local I = Inc.Emit({ Kind = `TestKind`; Where = Hall and Hall.Position; Who = { { Id = Player; Role = `Doer` } } })
	C:Disconnect()
	local Before = Rep.Entry(Player, `MaeGorse`)
	Inc.Emit({ Kind = `Downed`; Who = { { Id = Player; Role = `Doer` }, { Id = `MaeGorse`; Role = `Target` } } })
	local After = Rep.Entry(Player, `MaeGorse`)
	Rels.MaeGorse = Saved
	Rep.Sync(Player)
	return { Heard = #Heard; Region = I.Region; HasTime = typeof(I.T) == `number`; Truth = I.Truth;
		Witnesses = typeof(I.Witnesses) == `table`; FoughtAdded = (After.Flags.Fought or 0) - (Before.Flags.Fought or 0);
		ValueDelta = After.Value - Before.Value; Recent = #Inc.Recent(5) }
end
```

  Install the TestBridge, start Play, and run `bridge.py IncidentTest '$P'`. Expected: an error (no `World.Incidents`).

- [ ] **Step 2: `Roster.Near`.** Add to `Social.Roster`:

```lua
-- (2.29) rostered students within Radius of Pos (their body, or where they are with no body)
function Shared.Near(Pos: Vector3?, Radius: number): { string }
	local Out = {}
	if not Pos then return Out end
	for _, E in Config.List do
		local W = Shared.WhereNow(E.Id)
		if W.At and (W.At - Pos).Magnitude <= Radius then table.insert(Out, E.Id) end
	end
	return Out
end
```

- [ ] **Step 3: Write `World.Incidents`:**

```lua
--[[ (2.29) Incidents (server). Services.World.Incidents: one bus for things that happen in the school
	(docs/expansion/13-Living-School.md §4.1).
	Emit({ Kind, Where?, Region?, Who = { { Id = Player | npc id, Role = "Doer" | "Target" | "Helper" } }?, Witnesses?,
	       Severity?, Truth? = true, ... }) -> the incident (with T, Region and Witnesses filled in)
	On(Kind | "*", fn) -> connection; Emitted (signal); Recent(N); RegionAt(Pos) -> region name?
	Emitters: CliqueFights (Scuffle), Downed.OnDowned (Downed), HallMonitor.Caught (Caught), Discipline.ViolationAdded
	(Violation), Pranks.Marked (Prank), Matches (Match), Beasts (Beast), NHMoonEvent (Moon), World.Scenes (Scene).
	Consumer here: relationships (a player who downs a rostered student: -15 Fought; helps one: +10 Helped;
	pranks with one present as target: -8 Pranked). ]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local SignalPlus = require(ReplicatedStorage.Packages.SignalPlus)

local Shared = {}
local Local = {}
Shared.Emitted = SignalPlus()
local Log = {} -- newest first, at most 50
local WITNESS_RADIUS = 40

local function svc(Path: string)
	local Node = ServerScriptService.Services
	for Seg in Path:gmatch(`[^%.]+`) do Node = Node and Node:FindFirstChild(Seg) end
	if not Node then return nil end
	local Ok, M = pcall(require, Node)
	return if Ok then M else nil
end

function Shared.RegionAt(Pos: Vector3?): string?
	local Folder = workspace:FindFirstChild(`Regions`)
	if not (Pos and Folder) then return nil end
	local Best, BestVol = nil, math.huge -- the smallest box that holds the point (a room inside a hall wins)
	for _, Box in Folder:GetChildren() do
		if Box:IsA(`BasePart`) then
			local L = Box.CFrame:PointToObjectSpace(Pos)
			local H = Box.Size / 2
			if math.abs(L.X) <= H.X and math.abs(L.Z) <= H.Z then
				local Vol = Box.Size.X * Box.Size.Z
				if Vol < BestVol then Best, BestVol = (Box:GetAttribute(`RegionId`) or Box.Name), Vol end
			end
		end
	end
	return Best
end

function Local.PosOf(Id): Vector3?
	if typeof(Id) == `Instance` and Id:IsA(`Player`) then
		local R = Id.Character and Id.Character:FindFirstChild(`HumanoidRootPart`)
		return R and R.Position
	end
	local Roster = svc(`Social.Roster`)
	local W = Roster and typeof(Id) == `string` and Roster.WhereNow(Id)
	return W and W.At
end

function Shared.Emit(I)
	I.T = os.time()
	if I.Truth == nil then I.Truth = true end
	I.Who = I.Who or {}
	if not I.Where then
		for _, W in I.Who do I.Where = Local.PosOf(W.Id) if I.Where then break end end
	end
	I.Region = I.Region or Shared.RegionAt(I.Where)
	if not I.Witnesses then
		local Roster = svc(`Social.Roster`)
		I.Witnesses = if Roster and I.Where then Roster.Near(I.Where, WITNESS_RADIUS) else {}
	end
	table.insert(Log, 1, I)
	while #Log > 50 do table.remove(Log) end
	Shared.Emitted:Fire(I)
	return I
end

function Shared.On(Kind: string, Fn)
	return Shared.Emitted:Connect(function(I)
		if Kind == `*` or I.Kind == Kind then
			local Ok, Err = pcall(Fn, I)
			if not Ok then warn(`[Incidents] {Kind}: {Err}`) end
		end
	end)
end

function Shared.Recent(N: number?)
	local Out = {}
	for K = 1, math.min(N or 10, #Log) do Out[K] = Log[K] end
	return Out
end

-- the relationship consumer (2.27 flags): only a real player's deed against or for a rostered student counts
function Local.Relationships(I)
	local Rep, Roster = svc(`Social.Reputation`), svc(`Social.Roster`)
	if not (Rep and Roster) then return end
	local Doer, Target, Helper
	for _, W in I.Who do
		if W.Role == `Doer` then Doer = W.Id elseif W.Role == `Target` then Target = W.Id elseif W.Role == `Helper` then Helper = W.Id end
	end
	local function isPlayer(X) return typeof(X) == `Instance` and X:IsA(`Player`) end
	if (I.Kind == `Downed` or I.Kind == `Scene` and I.Hostile) and isPlayer(Doer) and Roster.IsRostered(Target) then
		Rep.ChangeRelationship(Doer, Target, -15, nil, `Fought`)
	end
	if isPlayer(Helper) and Roster.IsRostered(Target) then
		Rep.ChangeRelationship(Helper, Target, 10, nil, `Helped`)
	end
	if I.Kind == `Scene` and I.Pranked and isPlayer(Doer) and Roster.IsRostered(Target) then
		Rep.ChangeRelationship(Doer, Target, -8, nil, `Pranked`)
	end
end

function Shared.OnStart()
	Shared.On(`*`, Local.Relationships)
	-- the systems that already fire signals
	task.defer(function()
		local Downed = svc(`Features.Downed`)
		if Downed then Downed.OnDowned:Connect(function(Target: Model, Attacker: Model?)
			local TP, AP = Players:GetPlayerFromCharacter(Target), Attacker and Players:GetPlayerFromCharacter(Attacker)
			local TId = TP or Target:GetAttribute(`NHStudentId`) or Target:GetAttribute(`NpcId`) or Target.Name
			local AId = AP or (Attacker and (Attacker:GetAttribute(`NHStudentId`) or Attacker:GetAttribute(`NpcId`) or Attacker.Name))
			local R = Target:FindFirstChild(`HumanoidRootPart`)
			Shared.Emit({ Kind = `Downed`; Where = R and R.Position; Severity = 2;
				Who = { { Id = AId; Role = `Doer` }, { Id = TId; Role = `Target` } } })
		end) end
		local HM = svc(`School.HallMonitor`)
		if HM then HM.Caught:Connect(function(Player: Player, Reason: string, LetOff: boolean?)
			Shared.Emit({ Kind = `Caught`; Reason = Reason; LetOff = LetOff == true; Severity = 1; Who = { { Id = Player; Role = `Target` } } })
		end) end
		local Disc = svc(`School.Discipline`)
		if Disc then Disc.ViolationAdded:Connect(function(Player: Player, Record)
			Shared.Emit({ Kind = `Violation`; Type = Record.Type; Witness = Record.Witness; Severity = 1; Who = { { Id = Player; Role = `Target` } } })
		end) end
		local Pranks = svc(`Social.Pranks`)
		if Pranks then Pranks.Marked:Connect(function(Player: Player, WallId: string, Info)
			Shared.Emit({ Kind = `Prank`; Wall = WallId; Seen = Info and (Info.Recognized or Info.Spotted); Severity = 1; Who = { { Id = Player; Role = `Doer` } } })
		end) end
	end)
	workspace:GetAttributeChangedSignal(`NHMoonEvent`):Connect(function()
		local E = workspace:GetAttribute(`NHMoonEvent`)
		if E then Shared.Emit({ Kind = `Moon`; Event = E; Severity = 1 }) end
	end)
end

function Shared.ClearForTests() table.clear(Log) end

return Shared
```

- [ ] **Step 4: The three one-line emitters** (back up each script first).
  - **`CliqueFights`, in `Local.EndScuffle`,** after `Local.CountFeud(Ev.A, Ev.B, Winner)`:

```lua
	pcall(function() -- (2.29) the incident bus
		require(ServerScriptService.Services.World.Incidents).Emit({ Kind = `Scuffle`; Where = workspace:GetAttribute(`NHScuffleVenue`) or Ev.Venue;
			A = Ev.A; B = Ev.B; Winner = Winner; Why = Why; Severity = 2; Who = { { Id = Winner or Ev.A; Role = `Doer` } } })
	end)
```

    **Check:** `Ev.Venue` must hold the scuffle's position. `StartScuffle` sets `workspace:SetAttribute(\`NHScuffleAt\`, Venue)`
    (line 394), so set `Ev.Venue = Venue` on the line before it. Leave out `NHScuffleVenue`, which doesn't exist.
  - **`Matches`, in `Match:End`,** after `local Summary = Local.Reward(self, Winner, Why)`:

```lua
	pcall(function() -- (2.29) the incident bus
		local Root = self.Venue and self.Venue:IsA(`Model`) and self.Venue:GetPivot().Position
		require(game:GetService(`ServerScriptService`).Services.World.Incidents).Emit({ Kind = `Match`; Where = Root; Sport = self.Sport;
			Winner = if Winner then Config.Teams[Winner].Name else nil; Score = table.clone(self.Score); Severity = 1;
			Who = if Winner then { { Id = Config.Teams[Winner].Name; Role = `Doer` } } else {} })
	end)
```

  - **`Beasts`, in the `Sighted` branch,** after `W.Sighted = true`:

```lua
				pcall(function() -- (2.29) the incident bus: a beast was seen
					require(ServerScriptService.Services.World.Incidents).Emit({ Kind = `Beast`; Where = Root.Position;
						Beast = W.Name or W.Model.Name; Severity = 2; Who = { { Id = W.Name or W.Model.Name; Role = `Doer` } } })
				end)
```

    **Check the names** in that scope: the beast's root variable is `Root` (`Hum:MoveTo(Root.Position)` is on the same
    branch). If `W.Name` is nil, `W.Model.Name` is used.

- [ ] **Step 5: Install and run the test.**
  - Install Roster, Incidents, CliqueFights, Matches, Beasts and the TestBridge. Start Play.
  - Run `bridge.py IncidentTest '$P'`. Expected: `Heard 1`, `Region "MainHall"`, `HasTime true`, `Truth true`,
    `Witnesses true`, `FoughtAdded 1`, `ValueDelta -15`, `Recent ≥ 2`.
  - **Live emitters, from `gamevm.py`:**
    - call `Discipline.AddViolation(P, "Tardy", {})`
    - fire `Pranks.Marked:Fire(P, "TestWall", {})`
    - set `workspace:SetAttribute("NHMoonEvent", "Blue")`, then nil
    - **Expected:** `Incidents.Recent(5)` holds `Moon`, `Prank` and `Violation`.
    - Restore slot 2.

- [ ] **Step 6: Commit** `2.29 (1/6): the incident bus; eight emitters; relationship flags from incidents`.

---

### Task 2: Rumours: making, mutating safely, spreading

**Files:**
- Create: `ReplicatedStorage.Config.Rumours.luau`, `ServerScriptService.Services.Social.Rumours.luau`
- Modify: `Social.Reputation` (`Learn`), TestBridge

**Interfaces:**
- Consumes: `Incidents.On`, `Incidents.RegionAt` (Task 1); `Roster.All`, `Roster.WhereNow`, `Roster.Near`
- Produces:
  - **A rumour:** `{ Id: number, Kind: string, Subject: { Id, Role }[], Where: string?, Size: number, T: number, Truth: boolean, Hops: number, Notable: boolean, Knowers: { [rosterId]: true }, LastHop: number, Base = <the true values> }`
  - `Rumours.Make(I) -> rumour?` (only for kinds with a template)
  - `Rumours.Hop(R, Rng: Random) -> rumour`: a copy with `Hops + 1` and at most one mutated field, under the safety rule
  - `Rumours.Text(R) -> string`
  - `Rumours.Live() -> { rumour }` (at most 30)
  - `Rumours.ForChat(SpeakerId, ListenerId) -> rumour?`, `Rumours.Heard(ListenerId, R)`
  - `Rumours.HeardByPlayer(Player, R)`: a rumour naming a rostered student the player can't otherwise meet lets the
    player learn the name (`Reputation.Learn`)
  - `Reputation.Learn(Player, Id)`: sets `Met` without changing `Value`

- [ ] **Step 1: Write the failing tests.** Add to TestBridge:

```lua
-- (2.29) rumours from incidents, their text, and one spread
function Commands.RumourTest(PlayerName: string)
	local SSS = game:GetService(`ServerScriptService`).Services
	local Player = Players:FindFirstChild(PlayerName)
	local Ru = require(SSS.Social.Rumours)
	local I = { Kind = `Downed`; Region = `Commons`; Who = { { Id = Player; Role = `Doer` }, { Id = `MaeGorse`; Role = `Target` } }; Witnesses = { `KitHarrow` }; Truth = true; Severity = 2; T = os.time() }
	local R = Ru.Make(I)
	local Text = R and Ru.Text(R)
	local H = R and Ru.Hop(R, Random.new(7))
	return { Made = R ~= nil; Text = Text; KnowerKit = R and R.Knowers.KitHarrow == true; HopCount = H and H.Hops;
		PlayerStill = H and H.Subject[1].Id == Player; NoTemplate = Ru.Make({ Kind = `Nothing`; Who = {} }) == nil }
end

-- (2.29) the safety rule over many random hops: a player is never added, swapped or moved off their own deed
function Commands.RumourSafetyTest(PlayerName: string)
	local SSS = game:GetService(`ServerScriptService`).Services
	local Player = Players:FindFirstChild(PlayerName)
	local Ru = require(SSS.Social.Rumours)
	local Rng = Random.new(2029)
	local Bad, Mutated = 0, 0
	local Cases = {
		{ Kind = `Downed`; Region = `Commons`; Who = { { Id = Player; Role = `Doer` }, { Id = `MaeGorse`; Role = `Target` } }; Witnesses = { `KitHarrow`, `JaxCalloway` } };
		{ Kind = `Downed`; Region = `MainHall`; Who = { { Id = `RonanFell`; Role = `Doer` }, { Id = Player; Role = `Target` } }; Witnesses = { `KitHarrow` } };
		{ Kind = `Scene`; Scene = `Locker`; Region = `MainHall`; Who = { { Id = `JaxCalloway`; Role = `Doer` }, { Id = `AgnesLowe`; Role = `Target` } }; Witnesses = { `NicoRuiz`, `ClaraWebb` } };
		{ Kind = `Caught`; Reason = `Truancy`; Region = `EastWing`; Who = { { Id = Player; Role = `Target` } }; Witnesses = {} };
	}
	for _, I in Cases do
		I.Truth, I.T, I.Severity = true, os.time(), 2
		for _ = 1, 2500 do
			local R = Ru.Make(I)
			for _ = 1, Rng:NextInteger(1, 6) do
				local Before = R
				R = Ru.Hop(R, Rng)
				if Ru.Text(R) ~= Ru.Text(Before) then Mutated += 1 end
			end
			-- every player in the rumour is in the incident, in the same role; every player in the incident is still there
			for _, S in R.Subject do
				if typeof(S.Id) == `Instance` then
					local Ok = false
					for _, W in I.Who do if W.Id == S.Id and W.Role == S.Role then Ok = true end end
					if not Ok then Bad += 1 end
				end
			end
			for _, W in I.Who do
				if typeof(W.Id) == `Instance` then
					local Still = false
					for _, S in R.Subject do if S.Id == W.Id and S.Role == W.Role then Still = true end end
					if not Still then Bad += 1 end
				end
			end
			-- no rumour about a player may change its place or its size: a mutation there would make it untrue
			local HasPlayer = false
			for _, S in R.Subject do if typeof(S.Id) == `Instance` then HasPlayer = true end end
			if HasPlayer and (R.Where ~= R.Base.Where or R.Size ~= R.Base.Size) then Bad += 1 end
		end
	end
	return { Hops = 10000; Bad = Bad; Mutated = Mutated }
end
```

  Expected before the code: errors (no `Social.Rumours`).

- [ ] **Step 2: `Reputation.Learn`.** Add beside `Meet`:

```lua
-- (2.29) a name heard in a rumour: you now know who they are, and how they feel about you doesn't change
function Shared.Learn(Player: Player, NpcId: string)
	local Record = Local.Record(Player, NpcId)
	if not Record or Record.Met then return end
	Record.Met = true
	Record.Last = os.time()
	Shared.Sync(Player)
	Shared.RelationshipChanged:Fire(Player, NpcId, Local.StateFor(Record.Value, true), `Unknown`)
end
```

- [ ] **Step 3: `Config.Rumours`.** Templates use `{Doer}`, `{Target}`, `{Where}`, `{Size}` and `{Extra}`. Size ladders
  run small to large; a template without `{Size}` has nothing to change there.

```lua
--[[ (2.29) Rumour wording (Social.Rumours). Templates by incident kind (Scene incidents by scene id); Size ladders go
	from mild to wild. Names: a player by their first name, a rostered student by first name, anything else as given. ]]
return {
	Templates = {
		Downed = { `{Doer} {Size} {Target} in {Where}.`, `Heard {Target} got {SizePast} by {Doer} near {Where}.` };
		Scuffle = { `The {Doer} came out on top in a scuffle in {Where}.` };
		Caught = { `A monitor caught {Target} in {Where}. {Extra}` };
		Prank = { `Somebody marked a wall in {Where}. People are saying it was {Doer}.` };
		Match = { `{Doer} won the match. {Extra}` };
		Beast = { `Something like a {Doer} was seen out by {Where}.` };
		Moon = { `They say tonight's moon is {Extra}. Stay in.` };
		Argument = { `{Doer} and {Target} had a {Size} in {Where}.` };
		Locker = { `{Doer} {Size} {Target} into a locker in {Where}.` };
		Notice = { `Someone defaced the notice board in {Where}. {Extra}` };
		EastWing = { `Somebody heard {Size} in the east wing last night.` };
		Figure = { `{Doer} swears there was {Size} at the end of the main hall.` };
		Dare = { `{Doer} dared {Target} to try the Records Office door.` };
	};
	Sizes = {
		Downed = { `knocked down`, `flattened`, `wiped the floor with` };
		DownedPast = { `knocked down`, `flattened`, `destroyed` };
		Argument = { `row`, `screaming match`, `full-on fight` };
		Locker = { `pushed`, `shoved`, `slammed` };
		EastWing = { `footsteps`, `crying`, `someone calling a name` };
		Figure = { `a shadow`, `a girl in old clothes`, `a girl with no face` };
	};
	-- region names as players see them (Config.Regions ids -> words)
	Places = { MainHall = `the main hall`; Commons = `the Commons`; EastWing = `the east wing`; Cafeteria = `the cafeteria`;
		Library = `the library`; Chapel = `the chapel`; Dorms = `the dorms`; Grounds = `the grounds` };
	MaxLive = 30;
	HopSeconds = 300;
	LifeSeconds = 1440; -- one in-game day (24 real minutes at Config.SchoolSchedule's pace); check the pace in Step 4
	MutateChance = 0.2;
}
```

- [ ] **Step 4: Check `LifeSeconds`.** From `gamevm.py`, read the real seconds per in-game day from `SchoolClock` (its
  config's minutes per day). Set `LifeSeconds` to exactly that.

- [ ] **Step 5: Write `Social.Rumours`:**

```lua
--[[ (2.29) Rumours (server). Services.Social.Rumours (docs/expansion/13-Living-School.md §4.3).
	Incidents become rumours. Rostered students who witnessed it know it; it spreads through pair chats (StudentBrain) and,
	off-screen, to a student near a knower, at most one hop per rumour every HopSeconds. Each hop may change one detail
	(MutateChance): the place (a neighbouring region), the size, or an NPC subject (to an NPC who was there).
	THE SAFETY RULE: a rumour about a real player carries only true facts. No player is ever added to a rumour or moved
	to another role, no player is ever swapped out of their own deed, and a rumour holding a player never mutates its
	place or size. RumourSafetyTest checks it over 10,000 hops.
	API: Make(I), Hop(R, Rng), Text(R), Live(), ForChat(SpeakerId, ListenerId), Heard(ListenerId, R), HeardByPlayer(P, R) ]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local Config = require(ReplicatedStorage.Config.Rumours)

local Shared = {}
local Local = {}
local Live = {} :: { any }
local NextId = 0
local Rng = Random.new()

local function svc(Path: string)
	local Node = ServerScriptService.Services
	for Seg in Path:gmatch(`[^%.]+`) do Node = Node and Node:FindFirstChild(Seg) end
	local Ok, M = pcall(require, Node)
	return if Ok then M else nil
end
local function isPlayer(X) return typeof(X) == `Instance` and X:IsA(`Player`) end

function Local.TemplateKey(I): string? return if I.Kind == `Scene` then I.Scene else I.Kind end

function Shared.Make(I)
	local Key = Local.TemplateKey(I)
	if not (Key and Config.Templates[Key]) then return nil end
	NextId += 1
	local Subject = {}
	for _, W in I.Who or {} do table.insert(Subject, { Id = W.Id; Role = W.Role }) end
	local R = { Id = NextId; Kind = I.Kind; Key = Key; Subject = Subject; Where = I.Region; Size = 1; T = I.T or os.time();
		Truth = I.Truth ~= false; Hops = 0; Notable = (I.Severity or 1) >= 3; Knowers = {}; LastHop = os.clock();
		Witnesses = table.clone(I.Witnesses or {}); Extra = I.Extra or I.Reason or I.Event; Template = 1 }
	R.Base = { Where = R.Where; Size = R.Size }
	for _, Id in R.Witnesses do R.Knowers[Id] = true end
	return R
end

function Local.HasPlayer(R): boolean
	for _, S in R.Subject do if isPlayer(S.Id) then return true end end
	return false
end

-- a neighbouring region: the nearest other region box to this one
function Local.Neighbour(Where: string?): string?
	local Folder = workspace:FindFirstChild(`Regions`)
	local From = Folder and Where and Folder:FindFirstChild(Where)
	if not From then return Where end
	local Best, BestD = nil, math.huge
	for _, B in Folder:GetChildren() do
		if B:IsA(`BasePart`) and B ~= From then
			local D = (B.Position - From.Position).Magnitude
			if D < BestD then Best, BestD = B.Name, D end
		end
	end
	return Best or Where
end

function Shared.Hop(R, Rng2: Random)
	local H = table.clone(R)
	H.Subject = {}
	for _, S in R.Subject do table.insert(H.Subject, { Id = S.Id; Role = S.Role }) end
	H.Hops = R.Hops + 1
	H.Knowers = R.Knowers -- the same set: one rumour, mangled as it travels
	if Rng2:NextNumber() >= Config.MutateChance then return H end
	local Safe = not Local.HasPlayer(R) -- THE SAFETY RULE: a rumour with a player in it never mutates
	if not Safe then return H end
	local Choice = Rng2:NextInteger(1, 3)
	local Ladder = Config.Sizes[R.Key]
	if Choice == 1 then
		H.Where = Local.Neighbour(R.Where)
	elseif Choice == 2 and Ladder then
		H.Size = math.clamp(R.Size + 1, 1, #Ladder)
	else
		-- the person: an NPC subject becomes another NPC who was there (never a player: witnesses are rostered ids)
		local Pool = {}
		for _, Id in R.Witnesses do
			local Taken = false
			for _, S in H.Subject do if S.Id == Id then Taken = true end end
			if not Taken then table.insert(Pool, Id) end
		end
		if #Pool > 0 and #H.Subject > 0 then
			local K = Rng2:NextInteger(1, #H.Subject)
			H.Subject[K] = { Id = Pool[Rng2:NextInteger(1, #Pool)]; Role = H.Subject[K].Role }
		end
	end
	return H
end

function Local.Name(Id): string
	if isPlayer(Id) then
		local Ok, N = pcall(function() return require(ServerScriptService.Services.AI.StudentBrain.Talk).FirstName(Id) end)
		return if Ok and N then N else Id.DisplayName
	end
	local Roster = svc(`Social.Roster`)
	local E = Roster and typeof(Id) == `string` and Roster.Get(Id)
	if E then return E.First end
	local Cast = require(ReplicatedStorage.Config.Npcs)
	if Cast[Id] then return Cast[Id].Name end
	return tostring(Id)
end

function Shared.Text(R): string
	local T = Config.Templates[R.Key][R.Template] or Config.Templates[R.Key][1]
	local Ladder = Config.Sizes[R.Key]
	local Past = Config.Sizes[R.Key .. `Past`]
	local Fill = { Where = Config.Places[R.Where or ``] or (if R.Where then R.Where else `school`);
		Size = Ladder and Ladder[R.Size] or ``; SizePast = Past and Past[R.Size] or ``; Extra = if R.Extra then tostring(R.Extra) else `` }
	for _, S in R.Subject do Fill[S.Role] = Fill[S.Role] or Local.Name(S.Id) end
	local Out = T:gsub(`{(%w+)}`, function(K) return Fill[K] or `someone` end)
	return (Out:gsub(`%s+$`, ``))
end

function Shared.Live() return Live end

function Local.Add(R)
	if not R then return end
	table.insert(Live, R)
	while #Live > Config.MaxLive do table.remove(Live, 1) end
end

-- a rumour the speaker knows and the listener doesn't (nil if none)
function Shared.ForChat(SpeakerId: string?, ListenerId: string?)
	if not (SpeakerId and ListenerId) then return nil end
	for _, R in Live do
		if R.Knowers[SpeakerId] and not R.Knowers[ListenerId] then return R end
	end
	return nil
end

-- the listener now knows it; the rumour itself hops (and may change) at most once per HopSeconds
function Shared.Heard(ListenerId: string, R)
	R.Knowers[ListenerId] = true
	if os.clock() - R.LastHop >= Config.HopSeconds then
		local H = Shared.Hop(R, Rng)
		for K, V in H do R[K] = V end
		R.LastHop = os.clock()
	end
end

-- a player overheard it: a rostered student named in it whom the player can't meet any other way (fell out first) is
-- now known by name (doc 13 §2.5)
function Shared.HeardByPlayer(P: Player, R)
	local Rep, Roster = svc(`Social.Reputation`), svc(`Social.Roster`)
	if not (Rep and Roster) then return end
	for _, S in R.Subject do
		if typeof(S.Id) == `string` and Roster.IsRostered(S.Id) then
			local E = Rep.Entry(P, S.Id)
			if not E.Met and E.Value < -19 then Rep.Learn(P, S.Id) end
		end
	end
end

-- off-screen spread: every 10 s, a rumour whose hop is due passes from a knower to a student near them
function Local.Spread()
	local Roster = svc(`Social.Roster`)
	if not Roster then return end
	local Now = os.time()
	for K = #Live, 1, -1 do
		local R = Live[K]
		if Now - R.T > Config.LifeSeconds then table.remove(Live, K) continue end
		if os.clock() - R.LastHop < Config.HopSeconds then continue end
		local Knowers = {}
		for Id in R.Knowers do table.insert(Knowers, Id) end
		if #Knowers == 0 then continue end
		local From = Knowers[Rng:NextInteger(1, #Knowers)]
		local W = Roster.WhereNow(From)
		local Near = W.At and Roster.Near(W.At, 30) or {}
		for _, Id in Near do
			if not R.Knowers[Id] then Shared.Heard(Id, R) break end
		end
	end
end

function Shared.OnStart()
	task.defer(function()
		local Inc = svc(`World.Incidents`)
		if Inc then Inc.On(`*`, function(I) Local.Add(Shared.Make(I)) end) end
	end)
	task.spawn(function()
		while true do
			task.wait(10)
			local Ok, Err = pcall(Local.Spread)
			if not Ok then warn(`[Rumours] {Err}`) end
		end
	end)
end

function Shared.ClearForTests() table.clear(Live) end
function Shared.AgeForTests(R, Seconds: number) R.LastHop -= Seconds end

return Shared
```

- [ ] **Step 6: Install and run the tests.**
  - Install Reputation, `Config.Rumours`, Rumours and the TestBridge, then start Play.
  - Run `bridge.py RumourTest '$P'`. Expected: `Made true`, `Text` like "Ren knocked down Mae in the Commons.",
    `KnowerKit true`, `HopCount 1`, `PlayerStill true`, `NoTemplate true`.
  - Run `bridge.py RumourSafetyTest '$P'`. Expected: `Bad 0`, `Hops 10000`, and `Mutated > 0` (the NPC-only case
    mutates). If `Bad > 0`, stop: the rule is broken, and nothing else may ship until it's fixed.

- [ ] **Step 7: Commit** `2.29 (2/6): rumours; the safety rule (10,000 hops, 0 broken); off-screen spread`.

---

### Task 3: Students pass rumours on; Fortune draws one

**Files:**
- Modify: `ServerScriptService.Services.AI.StudentBrain.luau` (`chat`), `ServerScriptService.Services.Features.Fortune.luau` (`Hint.Whisper`, `ORDER`), TestBridge

**Interfaces:**
- Consumes: `Rumours.ForChat`, `Heard`, `HeardByPlayer`, `Text`, `Live` (Task 2)
- Produces: a pair chat where A tells B the rumour: "Did you hear? <text>", and B answers with a reaction line. A
  player within 12 studs of the speaker is passed to `HeardByPlayer`.

- [ ] **Step 1: The test is live (chats need bodies).** Write `harness/_rumourchat.lua`. It emits a `Locker` scene
  incident with two rostered witnesses who are standing near each other at lunch, then waits up to 90 s for one of them
  to say a line starting "Did you hear?":

```lua
local Inc = require(game.ServerScriptService.Services.World.Incidents)
local Ru = require(game.ServerScriptService.Services.Social.Rumours)
local Sched = workspace.NHSchedule
-- two students with bodies near each other
local A, B
for _, m in Sched:GetChildren() do
	local r = m:FindFirstChild("HumanoidRootPart")
	if r and not A then A = m elseif r and A and (r.Position - A.HumanoidRootPart.Position).Magnitude < 8 then B = m break end
end
if not (A and B) then return "no pair" end
local Aid = A:GetAttribute("NHStudentId")
local I = Inc.Emit({ Kind = "Scene"; Scene = "Locker"; Where = A.HumanoidRootPart.Position; Witnesses = { Aid };
	Who = { { Id = "JaxCalloway"; Role = "Doer" }, { Id = "AgnesLowe"; Role = "Target" } } })
local Said
local c = A:GetAttributeChangedSignal("NHSay"):Connect(function() local t = A:GetAttribute("NHSay") if t:find("^Did you hear") then Said = t end end)
P.Character:PivotTo(A.HumanoidRootPart.CFrame * CFrame.new(0, 0, -6))
local t0 = os.clock()
while not Said and os.clock() - t0 < 90 do task.wait(1) end
c:Disconnect()
local R = Ru.Live()[#Ru.Live()]
return ("said: %s | B knows %s"):format(tostring(Said), tostring(R and R.Knowers[B:GetAttribute("NHStudentId")]))
```

  Run it before the change. Expected: `said: nil`.

- [ ] **Step 2: `chat` shares a rumour.** In StudentBrain's `chat(A, B)`, replace the first line
  (`local Lines2 = Lines.PickChat(A, ctx())`) with:

```lua
	-- (2.29) a rumour A knows and B doesn't comes first (Social.Rumours)
	local Lines2
	local OkR, Ru = pcall(function() return require(ServerScriptService.Services.Social.Rumours) end)
	local Rumour = OkR and Ru and A.RosterId and B.RosterId and Ru.ForChat(A.RosterId, B.RosterId)
	if Rumour then
		Lines2 = { `A: Did you hear? {Ru.Text(Rumour)}`, `B: ` .. Lines.Pick(B, Lines.RumourReply or { `No way.` }, ctx()) }
		Ru.Heard(B.RosterId, Rumour)
		for _, P in Players:GetPlayers() do
			local R = P.Character and P.Character:FindFirstChild(`HumanoidRootPart`)
			if R and A.Root and (R.Position - A.Root.Position).Magnitude <= 12 then pcall(Ru.HeardByPlayer, P, Rumour) end
		end
	else
		Lines2 = Lines.PickChat(A, ctx())
	end
```

  - **The reply pool,** in `StudentBrain.Lines`:
    `Lines.RumourReply = { \`No way.\`, \`Seriously?\`, \`I heard it was worse.\`, \`That's not what I heard.\`, \`Figures.\`, \`Keep your voice down.\` } -- (2.29)`
  - **Check `Lines.Pick`'s signature** (`Lines.Pick(S, Pool, Ctx)`, which `say` uses). It returns a string or nil; use
    `or \`No way.\``.
  - **The chat loop** already splits `"A: …"` / `"B: …"` lines, so nothing else changes.

- [ ] **Step 3: Fortune's Whisper card.** In `Features.Fortune`, before `local ORDER`, add:

```lua
-- (2.29) Sable hears the school's whispers (Social.Rumours): the newest live rumour, if any
function Hint.Whisper(P: Player)
	local Ru = svc(`Social.Rumours`)
	local Live = Ru and Ru.Live()
	local R = Live and Live[#Live]
	if not R then return nil end
	local Text = Ru.Text(R)
	return { Card = `Fool`;
		Vague = `The fool's bell rings with gossip: something happened, and the telling has already changed it.`;
		Plain = `The halls are saying: "{Text}" Whether it's true is another matter.` }
end
```

  Then add `\`Whisper\`` to the end of `ORDER`. **Check:** `Hint.*` functions return `{ Card, Vague, Plain }`, and
  `Card` must be a key of `Shared.Cards`. `Fool` is one (`Hint.Fool` uses it).

- [ ] **Step 4: Install and run.**
  - Install StudentBrain (its children Talk, Lines and Nudges are kept), Lines, Fortune and the TestBridge.
  - Start Play, `SetTime "11:30"`, move to the stand (`_stand.lua`), wait 40 s, and run `gamevm.py _rumourchat.lua`.
    Expected: `said: Did you hear? Jax shoved Agnes into a locker in the main hall.` (or a Size variant), and
    `B knows true`.
  - From `gamevm.py`: `Fortune.ReadForTests(P, "Whisper")` returns the Fool card with that rumour in its Plain text
    (or the Vague text, if Sable's standing is low). Restore slot 2 after, since a Fortune reading saves the day's card.

- [ ] **Step 5: Commit** `2.29 (3/6): students pass rumours on in their chats; Sable's Whisper card`.

---

### Task 4: The scene director and six scenes

**Files:**
- Create: `ReplicatedStorage.Config.Scenes.luau`, `ServerScriptService.Services.World.Scenes.luau`
- Modify: `ServerScriptService.Services.Features.Schedules.luau` (`Borrow`, `Release`, `HallSpotFor`), TestBridge

**Interfaces:**
- Consumes:
  - `Incidents.Emit` and `Incidents.RegionAt` (Task 1)
  - `Brain.GoTo` and `sayText`-like bubbles. Schedules' `S` records have `Model`, `Root`, `Agent`; bubbles use the
    `NHSay` attributes the way `bubble` does.
  - `Config.Interaction` for prompts.
- Produces:
  - `Schedules.Borrow(Pos: Vector3, Count: number, Filter: (S) -> boolean) -> { S }?`: students with bodies within
    40 studs, not seated, not reacting and not in a scene. Each is taken: its job is cancelled and `S.InScene = true`.
    Returns nil if there aren't enough.
  - `Schedules.Release(S)`: `S.InScene = nil`, and its last job is re-run (`ReplanNow`).
  - `Scenes.Run(Id, Pos?) -> (ok, why?)` and `Scenes.Tick()`. The rules: a player within 60 studs of the spot; at most
    one scene per region every 600 s; not while any cut is playing (`workspace:GetAttribute("NHCinePlaying")`, or the
    Cine service's busy check); not in a class period inside a classroom.
  - `Scenes.SayFor(S, Text)`: a bubble over a borrowed student.

- [ ] **Step 1: Write the failing test.** Add to TestBridge:

```lua
-- (2.29) run one scene now at its spot (the player is moved there by the caller); returns how it went
function Commands.SceneTest(PlayerName: string, Id: string)
	local Scenes = require(game:GetService(`ServerScriptService`).Services.World.Scenes)
	local Ok, Why = Scenes.RunForTests(Id)
	return { Ok = Ok; Why = Why; Last = Scenes.LastForTests() }
end
```

  Expected before the code: an error.

- [ ] **Step 2: `Schedules.Borrow` and `Release`.** Add to Schedules:

```lua
-- (2.29) the scene director borrows students with bodies near a spot (World.Scenes) and gives them back after
function Shared.Borrow(Pos: Vector3, Count: number, Filter: ((any) -> boolean)?)
	local Pool = {}
	for _, S in Students do
		if S.Model and S.Root and not S.Seated and not S.Reacting and not S.InScene and not S.Chatting
			and (S.Root.Position - Pos).Magnitude <= 40 and (not Filter or Filter(S)) then
			table.insert(Pool, S)
		end
	end
	if #Pool < Count then return nil end
	table.sort(Pool, function(A, B) return (A.Root.Position - Pos).Magnitude < (B.Root.Position - Pos).Magnitude end)
	local Out = {}
	for K = 1, Count do
		local S = Pool[K]
		S.Job = {} -- cancel the routine (LastJob is kept for Release)
		S.InScene = true
		Local.Pose(S, nil)
		table.insert(Out, S)
	end
	return Out
end

function Shared.Release(S)
	S.InScene = nil
	if S.LastJob and S.Model then
		S.ReplanNow = true
		Local.Assign(S, S.LastJob.Fn, table.unpack(S.LastJob.Args, 1, S.LastJob.Args.n))
	end
end

function Shared.HallSpotFor() return Local.HallSpot() end
function Shared.Students() return Students end
```

- [ ] **Step 3: `Config.Scenes`.** Each scene is data:
  - **`When`:** segment kinds, or `Night = true`.
  - **`Spot`:** how to find the place.
  - **`Cast`:** the count, plus `Rival = true` for two rival cliques.
  - **`Steps`:** `go` (walk to an offset from the spot), `say` (a line; `{A}` and `{B}` are the cast's first names),
    `face`, `wait`, `figure` (show the faded-student template), `prompt` (the player hook), `fx`.
  - **`Outcome`:** the incident the scene emits.

```lua
--[[ (2.29) Scenes (World.Scenes; docs/expansion/13-Living-School.md §4.2). Six small scenes with rostered students,
	staged only where a player can see them (60 studs), at most one per region every 10 minutes, never in a cut or in
	class. Spot kinds: Hall (a hallway spot), Lockers (in front of the hallway lockers), Notice (the main hall's notice
	board), Region:<Id> (the middle of a region box), RecordsDoor. A prompt step waits up to Seconds for a player to press
	it; Pressed / Missed choose the outcome. ]]
return {
	Argument = { When = { `Passing`, `Break`, `Lunch`, `AfterSchool` }; Spot = `Hall`; Cast = { Count = 2; Rival = true };
		Steps = {
			{ `go`, 1, Vector3.new(-1.5, 0, 0) }, { `go`, 2, Vector3.new(1.5, 0, 0) }, { `face`, 1, 2 }, { `face`, 2, 1 },
			{ `say`, 1, `You've got some nerve, {B}.` }, { `wait`, 2 }, { `say`, 2, `Say that again. I dare you.` }, { `wait`, 2 },
			{ `prompt`, 1, `Step in`, 8 },
		};
		Pressed = { Lines = { { 1, `...Fine. Not worth it.` }, { 2, `This isn't over.` } }; Helper = true; Size = 1 };
		Missed = { Lines = { { 2, `Yeah? Come on then!` } }; Size = 3 };
	};
	Locker = { When = { `Passing`, `Break`, `Lunch`, `AfterSchool` }; Spot = `Lockers`; Cast = { Count = 2 };
		Steps = {
			{ `go`, 1, Vector3.new(0, 0, 3) }, { `go`, 2, Vector3.new(0, 0, 1.2) }, { `face`, 1, 2 },
			{ `say`, 1, `In you go, {B}.` }, { `fx`, 2, `Shove` }, { `say`, 2, `Hey! Let me out!` },
			{ `prompt`, 2, `Help out`, 10 },
		};
		Pressed = { Lines = { { 2, `Thanks. I owe you.` } }; Helper = true; Size = 1 };
		Missed = { Lines = { { 1, `Enjoy the dark.` } }; Size = 3 };
	};
	Notice = { When = { `BeforeSchool` }; Spot = `Notice`; Cast = { Count = 2 };
		Steps = {
			{ `go`, 1, Vector3.new(-1.5, 0, 4) }, { `go`, 2, Vector3.new(1.5, 0, 4) }, { `face`, 1, `spot` }, { `face`, 2, `spot` },
			{ `say`, 1, `Who wrote that?` }, { `say`, 2, `"ANSWER THE BELL." In red. Creepy.` }, { `prompt`, 0, `Read it`, 12 },
		};
		Pressed = { Note = `ANSWER THE BELL, scrawled across the timetable in red.`; Size = 1; Extra = `It says "ANSWER THE BELL".` };
		Missed = { Size = 1; Extra = `Nobody saw who did it.` };
	};
	EastWing = { Night = true; Spot = `Region:EastWing`; Cast = { Count = 1 };
		Steps = {
			{ `go`, 1, Vector3.new(0, 0, 0) }, { `say`, 1, `Did you hear that? Footsteps...` }, { `wait`, 3 },
			{ `prompt`, 1, `Go and look`, 10 },
		};
		Pressed = { Lines = { { 1, `Nothing. ...Right?` } }; Size = 1 };
		Missed = { Lines = { { 1, `I'm getting out of here.` } }; Size = 2 };
	};
	Figure = { Night = true; Spot = `Hall`; Cast = { Count = 1 };
		Steps = {
			{ `go`, 1, Vector3.new(0, 0, 0) }, { `figure`, 26, 4 }, { `say`, 1, `There's someone at the end of the hall...` },
			{ `prompt`, 1, `Look up`, 6 },
		};
		Pressed = { Lines = { { 1, `She's gone. You saw her too, right?` } }; Size = 2 };
		Missed = { Lines = { { 1, `I need to sleep more.` } }; Size = 1 };
	};
	Dare = { When = { `AfterSchool`, `Evening` }; Spot = `RecordsDoor`; Cast = { Count = 2 };
		Steps = {
			{ `go`, 1, Vector3.new(-1.5, 0, 3) }, { `go`, 2, Vector3.new(0, 0, 1.5) }, { `face`, 1, 2 },
			{ `say`, 1, `Go on, {B}. Touch the door. I dare you.` }, { `say`, 2, `Fine. It's just a door.` },
			{ `prompt`, 2, `Stop them`, 8 },
		};
		Pressed = { Lines = { { 2, `...Yeah. Maybe not.` } }; Helper = true; Size = 1 };
		Missed = { Lines = { { 2, `It's... cold. Why is it cold?` } }; Size = 2 };
	};
	RegionCooldown = 600;
	SeeRange = 60;
	TickSeconds = 5;
	TryChance = 0.15; -- per tick, when a scene fits the place and time
}
```

- [ ] **Step 4: Write `World.Scenes`:**

```lua
--[[ (2.29) Scenes (server). Services.World.Scenes: the scene director (docs/expansion/13-Living-School.md §4.2).
	Every TickSeconds, for a scene that fits the time, find its spot; if a player is within SeeRange, the region has had no
	scene for RegionCooldown, no cut is playing and it isn't class time in a classroom, roll TryChance and run it:
	borrow the cast (Schedules.Borrow), play the steps, wait on the prompt, emit the outcome as a Scene incident
	(Incidents: rumours, relationships), give the cast back (Schedules.Release).
	API: Run(Id, Pos?), Tick(), RunForTests(Id), LastForTests(), PressForTests(P) ]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local Config = require(ReplicatedStorage.Config.Scenes)
local Interaction = require(ReplicatedStorage.Config.Interaction)

local Shared = {}
local Local = {}
local LastByRegion = {} :: { [string]: number }
local Running = false
local Last = nil
local PressNow: Player? = nil -- tests: PressForTests presses the running scene's prompt

local function svc(Path: string)
	local Node = ServerScriptService.Services
	for Seg in Path:gmatch(`[^%.]+`) do Node = Node and Node:FindFirstChild(Seg) end
	local Ok, M = pcall(require, Node)
	return if Ok then M else nil
end

function Local.Spot(Kind: string): (Vector3?, BasePart?)
	if Kind == `Hall` then
		return svc(`Features.Schedules`).HallSpotFor(), nil
	elseif Kind == `Lockers` then
		local Props = workspace.School.Quests:FindFirstChild(`HallwayProps`)
		local L = Props and Props:FindFirstChild(`Locker`)
		if L then return L:GetPivot().Position + L:GetPivot().LookVector * 0.5, nil end
	elseif Kind == `Notice` then
		local B = workspace.School.NHProps:FindFirstChild(`NoticeBoard_143.5`)
		if B then return B:GetPivot().Position, B.PrimaryPart or B:FindFirstChildWhichIsA(`BasePart`) end
	elseif Kind == `RecordsDoor` then
		local E = workspace:FindFirstChild(`Area_RecordsExit`, true)
		if E then return E.Position, E end
	elseif Kind:sub(1, 7) == `Region:` then
		local B = workspace.Regions:FindFirstChild(Kind:sub(8))
		if B then return Vector3.new(B.Position.X, 4, B.Position.Z), B end
	end
	return nil, nil
end

function Local.Floor(P: Vector3): Vector3
	local Hit = workspace:Raycast(P + Vector3.new(0, 6, 0), Vector3.new(0, -20, 0))
	return if Hit then Hit.Position else P
end

function Local.PlayerNear(P: Vector3, R: number): boolean
	for _, Pl in Players:GetPlayers() do
		local Root = Pl.Character and Pl.Character:FindFirstChild(`HumanoidRootPart`)
		if Root and (Root.Position - P).Magnitude <= R then return true end
	end
	return false
end

function Local.Fits(Def, Seg): boolean
	if Def.Night then return require(ServerScriptService.Services.School.SchoolClock).IsNight() end
	return Def.When ~= nil and Seg ~= nil and table.find(Def.When, Seg.Kind) ~= nil
end

function Local.Say(S, Text: string)
	if not S.Model then return end
	S.SaidAt = os.clock()
	S.Model:SetAttribute(`NHSay`, Text)
	S.Model:SetAttribute(`NHSayFor`, math.clamp(1.8 + #Text * 0.06, 2.4, 6))
	S.Model:SetAttribute(`NHSayAt`, workspace:GetServerTimeNow())
	task.wait(math.clamp(1.4 + #Text * 0.05, 1.8, 4))
end

function Local.Fill(Text: string, Cast): string
	return (Text:gsub(`{A}`, Cast[1] and Cast[1].First or `you`):gsub(`{B}`, Cast[2] and Cast[2].First or `you`))
end

function Local.Figure(Pos: Vector3, Dist: number, Seconds: number)
	local T = ReplicatedStorage:FindFirstChild(`NHCineCast`) and ReplicatedStorage.NHCineCast:FindFirstChild(`Strikethrough`)
	if not T then return end
	local F = T:Clone()
	local Away = (workspace.Regions:FindFirstChild(`MainHall`) and workspace.Regions.MainHall.CFrame.RightVector) or Vector3.xAxis
	F:PivotTo(CFrame.lookAt(Local.Floor(Pos + Away * Dist) + Vector3.new(0, 3, 0), Pos))
	for _, D in F:GetDescendants() do if D:IsA(`BasePart`) then D.Anchored = true D.CanCollide = false D.CanQuery = false end end
	F.Parent = workspace
	task.delay(Seconds, function() F:Destroy() end)
end

function Local.Prompt(S, Spot: BasePart?, Text: string, Seconds: number): Player?
	local Holder = (S and S.Root) or Spot
	if not Holder then task.wait(Seconds) return nil end
	local P = Instance.new(`ProximityPrompt`)
	P.ActionText = Text P.ObjectText = `` P.KeyboardKeyCode = Interaction.PromptKey P.GamepadKeyCode = Interaction.GamepadKey
	P.HoldDuration = 0 P.MaxActivationDistance = 12 P.RequiresLineOfSight = false
	P.Parent = Holder
	local Who = nil
	local C = P.Triggered:Connect(function(Pl) Who = Pl end)
	local T0 = os.clock()
	while not Who and os.clock() - T0 < Seconds do
		task.wait(0.2)
		if PressNow then Who, PressNow = PressNow, nil end
	end
	C:Disconnect() P:Destroy()
	return Who
end

function Shared.Run(Id: string, Pos: Vector3?): (boolean, string?)
	local Def = Config[Id]
	if not (typeof(Def) == `table` and Def.Steps) then return false, `NoScene` end
	if Running then return false, `Busy` end
	local Spot, SpotPart = Local.Spot(Def.Spot)
	Spot = Pos or Spot
	if not Spot then return false, `NoSpot` end
	local Sched, Roster = svc(`Features.Schedules`), svc(`Social.Roster`)
	local Filter = nil
	local Cast = Sched.Borrow(Spot, Def.Cast.Count, Filter)
	if not Cast then return false, `NoCast` end
	if Def.Cast.Rival and #Cast >= 2 then
		local Pairs = require(ReplicatedStorage.Config.Cliques).RivalPairs
		local Rival = false
		for _, P in Pairs do if (P[1] == Cast[1].Clique and P[2] == Cast[2].Clique) or (P[2] == Cast[1].Clique and P[1] == Cast[2].Clique) then Rival = true end end
		if not Rival then for _, S in Cast do Sched.Release(S) end return false, `NoRivals` end
	end
	Running = true
	local Region = svc(`World.Incidents`).RegionAt(Spot) or `school`
	LastByRegion[Region] = os.clock()
	local Pressed: Player? = nil
	local Ok, Err = pcall(function()
		for _, St in Def.Steps do
			local Op = St[1]
			if Op == `go` then
				local S = Cast[St[2]]
				local Goal = Local.Floor(Spot + St[3])
				if S and S.Agent then require(ServerScriptService.Services.AI.StudentBrain).GoTo(S, Goal, function() return S.InScene == true end) end
			elseif Op == `face` then
				local S = Cast[St[2]]
				local At = if St[3] == `spot` then Spot else (Cast[St[3]] and Cast[St[3]].Root and Cast[St[3]].Root.Position)
				if S and S.Agent and At then S.Agent:Face(At) end
			elseif Op == `say` then
				Local.Say(Cast[St[2]], Local.Fill(St[3], Cast))
			elseif Op == `wait` then
				task.wait(St[2])
			elseif Op == `figure` then
				Local.Figure(Spot, St[2], St[3])
			elseif Op == `fx` then
				local S = Cast[St[2]]
				if S and S.Model then S.Model:SetAttribute(`NHMood`, `Startled`) end
			elseif Op == `prompt` then
				Pressed = Local.Prompt(Cast[St[2]], SpotPart, St[3], St[4])
			end
		end
		local Out = if Pressed then Def.Pressed else Def.Missed
		for _, L in Out.Lines or {} do Local.Say(Cast[L[1]], Local.Fill(L[2], Cast)) end
		if Pressed and Out.Note then
			pcall(function() require(ServerScriptService.Services.Features.Notifications).Notify(Pressed, { Title = `The notice board`; Text = Out.Note; Kind = `Info`; Duration = 6 }) end)
		end
		local Who = {}
		if Cast[1] then table.insert(Who, { Id = Cast[1].RosterId; Role = `Doer` }) end
		if Cast[2] then table.insert(Who, { Id = Cast[2].RosterId; Role = `Target` }) end
		if Pressed and Out.Helper then
			table.insert(Who, { Id = Pressed; Role = `Helper` })
			if not Cast[2] then table.insert(Who, { Id = Cast[1].RosterId; Role = `Target` }) end
		end
		local Witnesses = {}
		for _, S in Cast do table.insert(Witnesses, S.RosterId) end
		for _, Id2 in Roster.Near(Spot, 40) do if not table.find(Witnesses, Id2) then table.insert(Witnesses, Id2) end end
		svc(`World.Incidents`).Emit({ Kind = `Scene`; Scene = Id; Where = Spot; Region = Region; Who = Who; Witnesses = Witnesses;
			Severity = Out.Size or 1; Extra = Out.Extra; Pressed = Pressed ~= nil })
		Last = { Id = Id; Region = Region; Cast = #Cast; Pressed = Pressed ~= nil }
	end)
	for _, S in Cast do Sched.Release(S) end
	Running = false
	if not Ok then warn(`[Scenes] {Id}: {Err}`) return false, `Error` end
	return true, nil
end

function Shared.Tick()
	if Running then return end
	if workspace:GetAttribute(`NHCinePlaying`) then return end
	local State = require(ServerScriptService.Services.School.SchoolClock).GetState()
	local Seg = State and State.Segment
	for Id, Def in Config do
		if typeof(Def) ~= `table` or not Def.Steps or not Local.Fits(Def, Seg) then continue end
		local Spot = Local.Spot(Def.Spot)
		if not (Spot and Local.PlayerNear(Spot, Config.SeeRange)) then continue end
		local Region = svc(`World.Incidents`).RegionAt(Spot) or `school`
		if os.clock() - (LastByRegion[Region] or -1e9) < Config.RegionCooldown then continue end
		if Seg and Seg.Kind == `Class` and Region:match(`^R10%d`) then continue end
		if math.random() < Config.TryChance then task.spawn(Shared.Run, Id) return end
	end
end

function Shared.RunForTests(Id: string)
	LastByRegion = {}
	return Shared.Run(Id)
end
function Shared.LastForTests() return Last end
function Shared.PressForTests(P: Player) PressNow = P end

function Shared.OnStart()
	task.spawn(function()
		while true do
			task.wait(Config.TickSeconds)
			local Ok, Err = pcall(Shared.Tick)
			if not Ok then warn(`[Scenes] {Err}`) end
		end
	end)
end

return Shared
```

  **Check before installing:**
  - **The cut flag:** does the Cine service set a workspace attribute while a cut plays? Search `Services.World.Cine`
    for `SetAttribute`. If not, add `workspace:SetAttribute(\`NHCinePlaying\`, true)` when a session starts, and nil
    when it ends, at the points where Cine already records the session start and end. That's a one-line edit each;
    back up Cine first.
  - **The clock:** `SchoolClock.IsNight` exists (2.22).
  - **The cast's names:** a borrowed `S` has `First` (2.27).

- [ ] **Step 5: Install and run each scene once.**
  - Install Schedules, `Config.Scenes`, Scenes, the TestBridge, and Cine if it was edited. Start Play.
  - For each scene, set a fitting time, move the player within 20 studs of its spot (`gamevm.py`), wait 20 s for
    students to settle, and run `bridge.py SceneTest '$P' '"<Id>"'`:

    | Scene | Time | Expected |
    |---|---|---|
    | Argument | `12:10` | `Ok true` (or `NoRivals` / `NoCast`; then retry at another hall spot or time) |
    | Locker | `12:10` | `Ok true` |
    | Notice | `07:40` | `Ok true` |
    | EastWing | `22:30`, player in the East Wing; some students have to be there, so if `NoCast`, use `Scenes.Run("EastWing", <a spot where students are>)` from `gamevm.py` | `Ok true` |
    | Figure | `21:30` | `Ok true` |
    | Dare | `15:30`, player by the Records Office exit | `Ok true` |

  - **After each:** `Incidents.Recent(1)[1]` is a `Scene` incident with that `Scene` id, and `Rumours.Live()` holds its
    rumour, whose `Text` reads correctly. Students go back to their routine: their `NHActivity` is set again within
    10 s.
  - **Pressing a hook:** for one scene (Locker), press the prompt during the test. From `gamevm.py`, press the
    prompt with `Scenes.PressForTests(P)` while the prompt is up; it's picked up within 0.2 s. The incident then has
    a `Helper`, and the target's saved relationship gains `Helped`.
  - **Screenshot** one scene mid-play to `tools/phase4-2290/review/scene_locker.jpg`.
  - Restore slot 2.

- [ ] **Step 6: The director on its own.** Leave Play running at `12:10` near the hall for 5 minutes with no commands.
  Expected: at most one scene per region in that time (`Incidents.Recent`), no `[Scenes]` warnings, and students back
  on their routines.

- [ ] **Step 7: Commit** `2.29 (4/6): the scene director and six scenes`.

---

### Task 5: Regression

- [ ] **Step 1: Self-tests in one session.**
  - **This release:** `IncidentTest`, `RumourTest`, `RumourSafetyTest` (`Bad 0`).
  - **2.28:** `StaffTest`, `StaffPlanTest`, `TimetableTest`, `SleepTest`.
  - **2.27:** `RosterTest`, `Rostered`, `RelationshipCapTest`, `MemoryTest`.
  - **Earlier:** the cutscene and Phase 1 suite.
- [ ] **Step 2: The emitters' own systems still work.**
  - A clique scuffle (`CliqueFights.StartScuffle` from `gamevm.py`) runs and ends, with one `Scuffle` incident.
  - A Fortune reading works.
  - The prologue's two paths are unchanged, and no scene starts during them.
  - 2.28's school day (07:40, 08:05, 09:10, 11:30, 15:30) is unchanged.
- [ ] **Step 3: The console.** No errors from Incidents, Rumours, Scenes, Schedules, StudentBrain, Fortune,
  CliqueFights, Matches or Beasts.
- [ ] **Step 4: Frame rate.** Sample at the lunch stand. It should be within 2 fps of 2.28's 45.3 / 45.1.
- [ ] **Step 5:** Restore slot 2, stop Play, and run `save_place`.

### Task 6: Docs and release 2.29.0

- [ ] **Step 1: CHANGELOG `[2.29.0]`,** with Added, Changed, Checked and Not checked, the safety-test numbers, and
  this plan's deltas.
- [ ] **Step 2: The other docs.**
  - **README:** a Latest-update line.
  - **Implementation-Status:** a row.
  - **Discord:** a game update in `updates/discord/game-updates/<date>-word-gets-around.md`, plus the index.
  - **Doc 13:** the status line and §9 deltas.
- [ ] **Step 3: Vault.** Copy the docs over, and add the home-note line.
- [ ] **Step 4: Commit and merge** (as in 2.28: stage only this plan's files and the CHANGELOG hunk; merge with
  `-F <file>`; stash around the merge). Don't push.

---

## Spec deltas (record in doc 13 §9 at release)

1. **"A figure at a window"** becomes **"a figure at the end of the main hall".** The school building has no windows.
   The figure is the existing faded-student cast template (the Strikethrough), shown for 4 seconds.
2. **The notice board** is `NoticeBoard_143.5` in the main hall. The part tagged `NHNoticeBoard` is the Midnight Bell
   board.
3. **The moon emitter** listens to `MoonPhases`' `NHMoonEvent` attribute rather than editing `MoonPhases`.
4. **Witnesses** are rostered students within 40 studs (`Roster.Near`), not "in the region". Regions are large, and
   their classroom boxes are offset (2.28).
5. **A rumour holding a player never mutates at all.** That's stricter than "only NPC fields may change": it's the
   simplest form of the rule that a test can prove.
6. **Learning a name from a rumour** uses `Reputation.Learn` (met, value unchanged), only for students who fell out
   with you before an introduction.
7. **Rumours' life** is one in-game day (`LifeSeconds`, from the clock's pace), and the rumour list is server-wide and
   not saved, as the spec says.

## Self-review

- **Spec coverage (doc 13 §4):**
  - §4.1, the bus and its emitters, is Task 1.
  - §4.2, the six scenes and their rules, is Task 4.
  - §4.3:
    - rumours, spread, mutation and safety: Task 2
    - voices (CliqueTalk "Rumour" through chats, and Sable's Fortune): Task 3
    - learning a name: Task 2 (`HeardByPlayer`) and Task 3 (`chat`)
  - §4.4, the acceptance, is Tasks 2, 4 and 5.
- **Placeholders:** none. The two runtime checks (Cine's playing flag; `LifeSeconds` from the clock's pace) say exactly
  what to look for and what to write.
- **Types:**
  - `I.Who[k] = { Id, Role }` is used by Incidents, Rumours and Scenes.
  - The rumour fields (`Knowers`, `LastHop`, `Base`, `Witnesses`, `Key`) are the same in `Make`, `Hop`, `Spread` and
    the tests.
  - `Borrow` and `Release` are in Task 4 and used by Scenes only.
- **Known risks:**
  - **Pair chats need two students with bodies standing close.** That's lunch and hangouts, so the live chat test runs
    at lunch.
  - **`Brain.GoTo` blocks the step until the walk ends.** A long walk delays the scene. Spots are chosen within 40
    studs of the borrowed cast.
