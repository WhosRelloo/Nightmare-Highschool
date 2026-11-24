# Headmaster's Console, Phase 1a Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** replace the 1.18 Headmaster's Desk with the Headmaster's Console:
- one registry drives every action card;
- all 66 commands are migrated with the same server checks;
- four staff levels (0-3);
- two sides, Moderate and Test, with sections, cards, a command palette, hold-to-confirm, favourites for the session,
  and a results feed;
- built from the console art, with UI-kit fallbacks.

**Architecture:**
- **Pure rules** in a new `ReplicatedStorage.Functions.StaffConsole`: levels, argument checks, search, registry
  validation. They are tested in the Edit VM.
- **Command data** (title, help, icon, level, arguments, danger, synonyms) for the 66 commands lives in a new server-only
  `ServerScriptService.Services.Features.Admin.Meta`.
- **The server** (`Features.Admin`):
  - keeps every `Run` function;
  - checks the level and the arguments against the metadata before a command runs;
  - sends the registry (without `Run`) in `Info()`.
- **The client** is a new `Controllers.Gui.StaffConsole` (shell, input, remotes) with child modules:
  - `Model` (pure state);
  - `View` (layout);
  - `Cards` (cards, options, hold ring);
  - `Palette` (Ctrl+K);
  - `Tools` (Fly, Noclip, ESP, Ctrl+click teleport, spectate, inspect, moved from the old panel).
- **The old** `Controllers.Gui.AdminPanel` moves to `ServerStorage.NH_Backup`.

**Tech Stack:** Luau, the Roblox UI kit (`ReplicatedStorage.UI.Components`, `Theme`), Python harness scripts
(`rbxc.py`), Pillow for the art-id script.

**Spec:** `docs/superpowers/specs/2026-11-23-admin-console-design.md` (§2b holds the review picks this plan follows).

## Global Constraints

- **Studio:**
  - NH Combat Test (placeId 98950102230473) only.
  - One session drives it at a time.
  - Never save, close, reload or revert the place without the owner's word.
  - Use slot 2 only.
  - Take a fresh snapshot at the start of every Play round and restore only from it.
  - Record CineState, Seen and Origin before and after every Play round.
- **Commits:** commit only when the owner says so; every commit message ends with
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Text:** never under 20 design px (titles 22-26, help 20).
- **Layout:** design size 1600 x 900, scaled with `Kit.AutoScale`.
- **Security:**
  - Every request is checked on the server.
  - No targeting up: nobody can act on someone of a higher level.
  - Text other players see goes through `TextService` filtering (as today).
- **Levels:**
  - 0 means nothing, and no console.
  - 1, Moderator: group rank 254.
  - 2, Admin: `Config.Cmdr.Admin` or `Config.Cmdr.Testers`.
  - 3, Owner: rank 255+ or `Config.Cmdr.Owner`.
  - In Studio everyone is level 3, unless the server set `NHTestLevel` (0-3) on them, or `NHTestNotAdmin` (which
    means 0).
  - Owner-only: permanent bans, Shutdown, Yen over ¥100,000, race rites.
  - A moderator's bans are 30 days at most.
- **Danger (hold-to-confirm, 0.8 s):** Kick, Ban, Kill, Shutdown, ClearEnemies, FreezeAll, ServerLock, BringAll,
  QuestReset, RegionsReset.
- **Esc:** Roblox keeps Escape for its own menu, so a bound action never fires. Close on `GuiService.MenuOpened`
  instead (the Evidence Wall lesson, 2026-11-23).
- **Install:**
  - Changed scripts go in place with `tools/admin-console/install_inplace.py`, which keeps the class, children and
    attributes, and backs up to `ServerStorage.NH_Backup.<name>`.
  - New modules go in with `tools/admin-console/install_new.py`.
  - Mirror files live in `tools/admin-console/live/<Dotted.Path>.luau`; the originals are in `tools/admin-console/pre/`
    (already fetched 2026-11-23).
- **Out of scope for 1a:** saved records, the saved log and the Log section, saved favourites (1b); the Inbox,
  reports, auto-flags and health graphs (phase 3); new Test tools (World seasons and moons, Story cutscenes and the
  tutorial, the Bell Tower, Form direction: phase 2); the REPORTED, TRANSFORMED, WANTED and NEW row flags (phases 2-3).

## File structure

| Path (under `tools/admin-console/`) | What |
|---|---|
| `live/ReplicatedStorage.Functions.StaffConsole.luau` | new, pure: `LevelFrom`, `CheckArgs`, `Search`, `Validate`, `Public`, `SECTIONS`, `SIDE_LEVEL`, `DANGER_HOLD` |
| `live/ServerScriptService.Services.Features.Admin.Meta.luau` | new, server-only data: the 66 command entries |
| `live/ServerScriptService.Services.Features.Admin.luau` | modify: levels 0-3, `Dispatch`, the argument check, `Registry` in `Info`, a `Status` remote, owner checks at 3, the 30-day moderator cap, `Lists` additions |
| `live/ReplicatedStorage.Config.Cmdr.luau` | modify: `Testers = {}` |
| `live/ReplicatedStorage.Config.ConsoleArt.luau` | new: the 20 piece ids (0 until uploaded) and the 49 icon ids |
| `live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.luau` | new: the shell (open/close, input, remotes, refresh, probe) |
| `live/...Controllers.Gui.StaffConsole.Model.luau` | new, pure: sides, cards per section, favourites, recent students, rows, feed, flags |
| `live/...Controllers.Gui.StaffConsole.View.luau` | new: the top bar, rail, section tabs, card grid, feed, context |
| `live/...Controllers.Gui.StaffConsole.Cards.luau` | new: one card, its option controls, the picker, the hold ring |
| `live/...Controllers.Gui.StaffConsole.Palette.luau` | new: the Ctrl+K overlay |
| `live/...Controllers.Gui.StaffConsole.Tools.luau` | new: the client-only tools (moved from `AdminPanel`) and their card entries |
| `live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.GamepadControls.luau` | modify: `NHAdminPanel` becomes `NHStaffConsole` |
| `checks/console_pure.lua`, `checks/console_registry.lua`, `checks/console_model.lua` | Edit-VM checks |
| `checks/console_play_server.lua`, `checks/console_play_client.lua` | Play checks |
| `art_ids.py` | writes `Config.ConsoleArt` from `art/ui/hud/console/icons/icon_ids.json` (+ piece ids when uploaded) |
| `install_inplace.py`, `install_new.py`, `run_check.py` | harness |
| `REPORT.md` | results |

`(...)` = `StarterPlayer.StarterPlayerScripts`.

The loader requires every ModuleScript under `Controllers` and `Services`, and calls `OnStart` only where it exists
(`ReplicatedStorage.ModuleLoader`). Child modules (`StaffConsole.View` and the others, and `Admin.Meta`) therefore have
**no** `OnStart` and are required by their parent.

---

### Task 0: Harness

**Files:**
- Create: `tools/admin-console/install_inplace.py` (copy of `tools/locomotion-pace/install_inplace.py`)
- Create: `tools/admin-console/install_new.py` (copy of `E:/NH-transform/tools/forms/harness/install.py`; it parses
  first, keeps an existing instance's children)
- Create: `tools/admin-console/run_check.py`

- [ ] **Step 1: Copy the two installers**

```bash
cd E:/NH-admin
cp E:/NH-main/tools/locomotion-pace/install_inplace.py tools/admin-console/
cp E:/NH-transform/tools/forms/harness/install.py tools/admin-console/install_new.py
```

- [ ] **Step 2: Write `run_check.py`**

```python
"""Run a check file in NH Combat Test. usage: python -X utf8 -I run_check.py <Edit|Server|Client> <check.lua>
Prints the check's result. Exit 1 unless it starts with PASS."""
import subprocess, sys
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
dm, f = sys.argv[1], sys.argv[2]
r = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", "placeId: 98950102230473", dm, "@" + f],
                   capture_output=True, text=True, encoding="utf-8")
out = (r.stdout or "").strip()
print(out or r.stderr[-2000:])
sys.exit(0 if out.startswith("PASS") else 1)
```

- [ ] **Step 3: Try it**

Write `return "PASS hello"` to `tools/admin-console/checks/_hello.lua`.
Run: `python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/_hello.lua`
Expected: `PASS hello`, exit 0. Delete `_hello.lua`.

---

### Task 1: The pure rules (`Functions.StaffConsole`, TDD)

**Files:**
- Create: `tools/admin-console/live/ReplicatedStorage.Functions.StaffConsole.luau`
- Test: `tools/admin-console/checks/console_pure.lua`

**Interfaces:**
- Produces:
  - `LevelFrom(F: { Studio: boolean, TestLevel: any, NotAdmin: boolean, Owner: boolean, Admin: boolean, Tester: boolean, Rank: number }) -> number`
  - `CheckArgs(Schema: { Arg }, Args: any, Lists: { [string]: { any } }?) -> (true, { [string]: any }) | (false, string)`
  - `Search(Defs: { Def }, Query: string) -> { Def }`
  - `Validate(Id: string, D: Def) -> (boolean, string?)`
  - `Public(Id: string, D: Def) -> Def` (a copy with `Id`, without `Run`)
  - `SECTIONS: { Moderate: { string }, Test: { string } }`
  - `SIDE_LEVEL: { Moderate: 1, Test: 2 }`
  - `DANGER_HOLD = 0.8`
  - `Arg = { Name, Label?, Kind = "number"|"text"|"choice"|"toggle"|"position", Min?, Max?, Choices?, From?, Required? }`
  - `Def = { Side, Section, Title, Help, Icon, Level, Target = "none"|"required"|"optional", Args, Danger, Synonyms }`

- [ ] **Step 1: Write the failing check**

`tools/admin-console/checks/console_pure.lua`:

```lua
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
```

- [ ] **Step 2: Run it (no module yet)**

Run: `python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_pure.lua`
Expected: `FAIL Functions.StaffConsole missing`.

- [ ] **Step 3: Write the module**

`tools/admin-console/live/ReplicatedStorage.Functions.StaffConsole.luau`:

```lua
--[[
	StaffConsole (shared, pure): the Headmaster's Console rules (spec docs/superpowers/specs/2026-11-23-admin-console-design.md).
	Levels (§6), argument checks (§7), the palette search (§5), registry validation. No services, no state: the server
	(Features.Admin) and the client (Controllers.Gui.StaffConsole) both use it, and checks/console_pure.lua tests it.
]]
local Shared = {}

Shared.DANGER_HOLD = 0.8
Shared.SECTIONS = {
	Moderate = { "Student", "Server" },
	Test = { "Character", "Progress", "School", "Story", "World", "Spawns", "Self" },
}
Shared.SIDE_LEVEL = { Moderate = 1, Test = 2 }
Shared.LEVEL_NAMES = { "a moderator", "an admin", "the owner" }

local KINDS = { number = true, text = true, choice = true, toggle = true, position = true }
local TARGETS = { none = true, required = true, optional = true }

-- 0 none, 1 moderator, 2 admin, 3 owner. In Studio: 3, or the server-set test level (0-3), or 0 for NHTestNotAdmin.
function Shared.LevelFrom(F: any): number
	if F.Studio then
		local T = tonumber(F.TestLevel)
		if T and T == math.floor(T) and T >= 0 and T <= 3 then return T end
		if F.NotAdmin then return 0 end
		return 3
	end
	local Rank = tonumber(F.Rank) or 0
	if F.Owner or Rank >= 255 then return 3 end
	if F.Admin or F.Tester then return 2 end
	if Rank >= 254 then return 1 end
	return 0
end

local function inList(List: any, V: any): boolean
	for _, It in List or {} do
		if It == V or (typeof(It) == "table" and It.Id == V) then return true end
	end
	return false
end

-- Only declared args come back; missing optional args stay nil (the command's own default applies).
function Shared.CheckArgs(Schema: any, Args: any, Lists: any): (boolean, any)
	Args = if typeof(Args) == "table" then Args else {}
	local Out = {}
	for _, A in Schema or {} do
		local Label = A.Label or A.Name
		local V = Args[A.Name]
		if V == nil or V == "" then
			if A.Required then return false, `{Label} is needed` end
			continue
		end
		if A.Kind == "number" then
			local N = tonumber(V)
			if not N or N ~= N then return false, `{Label} must be a number` end
			if N < A.Min or N > A.Max then return false, `{Label} must be {A.Min} to {A.Max}` end
			Out[A.Name] = N
		elseif A.Kind == "text" then
			if typeof(V) ~= "string" then return false, `{Label} must be text` end
			Out[A.Name] = string.sub(V, 1, A.Max or 200)
		elseif A.Kind == "choice" then
			local Ok = (A.Choices ~= nil and table.find(A.Choices, V) ~= nil) or (A.From ~= nil and inList(Lists and Lists[A.From], V))
			if not Ok then return false, `Unknown {Label}: {tostring(V)}` end
			Out[A.Name] = V
		elseif A.Kind == "toggle" then
			if typeof(V) ~= "boolean" then return false, `{Label} must be on or off` end
			Out[A.Name] = V
		elseif A.Kind == "position" then
			if typeof(V) ~= "Vector3" then return false, `{Label} must be a position` end
			Out[A.Name] = V
		end
	end
	return true, Out
end

-- Title prefix 3, title contains 2, synonym exact 3 / prefix 2, help contains 1; ties by Title.
function Shared.Search(Defs: any, Query: string?): any
	local Q = string.match(string.lower(Query or ""), "^%s*(.-)%s*$") or ""
	if Q == "" then return {} end
	local Hits = {}
	for _, D in Defs do
		local T = string.lower(D.Title)
		local Score = 0
		if string.sub(T, 1, #Q) == Q then Score = 3 elseif string.find(T, Q, 1, true) then Score = 2 end
		for _, W in D.Synonyms or {} do
			local L = string.lower(W)
			if L == Q then Score = math.max(Score, 3) elseif string.sub(L, 1, #Q) == Q then Score = math.max(Score, 2) end
		end
		if Score == 0 and string.find(string.lower(D.Help or ""), Q, 1, true) then Score = 1 end
		if Score > 0 then table.insert(Hits, { Def = D; Score = Score }) end
	end
	table.sort(Hits, function(A, B)
		if A.Score ~= B.Score then return A.Score > B.Score end
		return A.Def.Title < B.Def.Title
	end)
	local Out = {}
	for _, H in Hits do table.insert(Out, H.Def) end
	return Out
end

function Shared.Validate(Id: string, D: any): (boolean, string?)
	local function bad(Why: string) return false, `{Id}: {Why}` end
	if typeof(D) ~= "table" then return bad("not a table") end
	if not Shared.SECTIONS[D.Side] then return bad("Side") end
	if not table.find(Shared.SECTIONS[D.Side], D.Section) then return bad("Section") end
	if typeof(D.Title) ~= "string" or D.Title == "" then return bad("Title") end
	if typeof(D.Help) ~= "string" or D.Help == "" then return bad("Help") end
	if typeof(D.Icon) ~= "string" or D.Icon == "" then return bad("Icon") end
	if not (D.Level == 1 or D.Level == 2 or D.Level == 3) then return bad("Level") end
	if D.Level < Shared.SIDE_LEVEL[D.Side] then return bad("Level below its side") end
	if not TARGETS[D.Target] then return bad("Target") end
	if typeof(D.Args) ~= "table" then return bad("Args") end
	for _, A in D.Args do
		if typeof(A) ~= "table" or typeof(A.Name) ~= "string" or not KINDS[A.Kind] then return bad("an arg") end
		if A.Kind == "number" and not (typeof(A.Min) == "number" and typeof(A.Max) == "number") then return bad(`{A.Name} needs Min and Max`) end
		if A.Kind == "choice" and not (A.Choices or A.From) then return bad(`{A.Name} needs Choices or From`) end
	end
	if typeof(D.Danger) ~= "boolean" then return bad("Danger") end
	if typeof(D.Synonyms) ~= "table" then return bad("Synonyms") end
	return true
end

function Shared.Public(Id: string, D: any): any
	return {
		Id = Id; Side = D.Side; Section = D.Section; Title = D.Title; Help = D.Help; Icon = D.Icon; Level = D.Level;
		Target = D.Target; Args = D.Args; Danger = D.Danger; Synonyms = D.Synonyms; Local = D.Local;
	}
end

return Shared
```

- [ ] **Step 4: Install and run the check**

```bash
python -X utf8 -I tools/admin-console/install_new.py tools/admin-console/live/ReplicatedStorage.Functions.StaffConsole.luau
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_pure.lua
```
Expected: `PASS console_pure`. If a line fails, fix the module, not the check, unless the check contradicts the spec.

- [ ] **Step 5: Commit (on the owner's word)**

```bash
git add tools/admin-console/install_inplace.py tools/admin-console/install_new.py tools/admin-console/run_check.py tools/admin-console/live/ReplicatedStorage.Functions.StaffConsole.luau tools/admin-console/checks/console_pure.lua
git commit -m "Console 1a: StaffConsole pure rules (levels, args, search, validation)"
```

---

### Task 2: The command metadata (`Admin.Meta`) and the registry check

**Files:**
- Create: `tools/admin-console/live/ServerScriptService.Services.Features.Admin.Meta.luau`
- Test: `tools/admin-console/checks/console_registry.lua`

**Interfaces:**
- Consumes: `StaffConsole.Validate`, `StaffConsole.SECTIONS` (Task 1).
- Produces: `Meta: { [CommandId]: Def }`, the 66 ids exactly as the `C.<Id>` tables in `Features.Admin`. List-backed
  choices name a key of `Admin.Lists()`: `Races`, `Gear`, `Quests`, `Regions`, `Clubs`, `Venues`, `Segments`,
  `Beasts`, `Rooms` (Task 3 adds `Races` and `Gear`).

- [ ] **Step 1: Write the failing check**

`tools/admin-console/checks/console_registry.lua`:

```lua
local Admin = game.ServerScriptService.Services.Features:FindFirstChild("Admin")
if not Admin then return "FAIL Features.Admin missing" end
local MetaMod = Admin:FindFirstChild("Meta")
if not MetaMod then return "FAIL Admin.Meta missing" end
local S = require(game.ReplicatedStorage.Functions.StaffConsole:Clone())
local Meta = require(MetaMod:Clone())
local Fails = {}
-- the command ids in Admin's source: every top-level `C.<Id> = {`
local Ids = {}
for Id in string.gmatch("\n" .. Admin.Source, "\nC%.(%w+) = {") do Ids[Id] = true end
local N = 0
for Id in Ids do
	N += 1
	if not Meta[Id] then table.insert(Fails, "no Meta for " .. Id) end
end
for Id, D in Meta do
	if not Ids[Id] then table.insert(Fails, "Meta for a missing command " .. Id) end
	local Ok, Why = S.Validate(Id, D)
	if not Ok then table.insert(Fails, Why) end
end
if N ~= 66 then table.insert(Fails, "commands in Admin: " .. N .. ", want 66") end
-- danger list (spec §5 + §2b)
local DANGER = { Kick = true, Ban = true, Kill = true, Shutdown = true, ClearEnemies = true, FreezeAll = true,
	ServerLock = true, BringAll = true, QuestReset = true, RegionsReset = true }
for Id, D in Meta do
	if (DANGER[Id] == true) ~= (D.Danger == true) then table.insert(Fails, Id .. " danger is " .. tostring(D.Danger)) end
end
-- owner-only by level: Shutdown only (the rest are checked inside Run)
for Id, D in Meta do
	if (D.Level == 3) ~= (Id == "Shutdown") then table.insert(Fails, Id .. " level " .. D.Level) end
end
-- every icon exists in the art config (when it is installed)
local Art = game.ReplicatedStorage.Config:FindFirstChild("ConsoleArt")
if Art then
	local A = require(Art:Clone())
	for Id, D in Meta do if not A.Icons[D.Icon] then table.insert(Fails, Id .. " icon " .. D.Icon .. " has no id") end end
end
-- every section has at least one card
for Side, List in S.SECTIONS do
	for _, Sec in List do
		local Any = false
		for _, D in Meta do if D.Side == Side and D.Section == Sec then Any = true end end
		if not Any then table.insert(Fails, Side .. "/" .. Sec .. " has no server card") end
	end
end
if #Fails > 0 then return "FAIL " .. #Fails .. "\n" .. table.concat(Fails, "\n") end
return "PASS console_registry (" .. N .. " commands)"
```

The Self section's cards are mostly client-only (Task 6). `Invisible` and `TeleportTo` keep it non-empty on the
server.

- [ ] **Step 2: Run it**

Run: `python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_registry.lua`
Expected: `FAIL Admin.Meta missing`.

- [ ] **Step 3: Write the metadata**

`tools/admin-console/live/ServerScriptService.Services.Features.Admin.Meta.luau`:

```lua
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
	GiveSpins = { Side = T; Section = "Character"; Title = "Give spins"; Help = "Race spins"; Icon = "Gear"; Level = 2; Target = "required"; Danger = false; Synonyms = { "spin" };
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
	SetClub = { Side = T; Section = "Progress"; Title = "Club"; Help = "Put them in a club"; Icon = "SecProgress"; Level = 2; Target = "required"; Danger = false; Synonyms = { "sports" };
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
		Args = { A("Id", "text", { Label = "Quest id"; Max = 40; Required = true }) } };
	QuestAbandon = { Side = T; Section = "Story"; Title = "Drop a quest"; Help = "Drop one of their quests"; Icon = "SecStory"; Level = 2; Target = "required"; Danger = false; Synonyms = { "abandon" };
		Args = { A("Id", "text", { Label = "Quest id"; Max = 40; Required = true }) } };
	QuestReset = { Side = T; Section = "Story"; Title = "Reset quests"; Help = "Clear every quest they have"; Icon = "SecStory"; Level = 2; Target = "required"; Danger = true; Synonyms = { "quests reset" }; Args = {} };

	-- Test / World
	FullMoon = { Side = T; Section = "World"; Title = "Full moon tonight"; Help = "Make tonight a full moon"; Icon = "Moon"; Level = 2; Target = "none"; Danger = false; Synonyms = { "moon" }; Args = {} };
	GotoRegion = { Side = T; Section = "World"; Title = "Go to a place"; Help = "You, or the selected student, to any place"; Icon = "GoTo"; Level = 2; Target = "none"; Danger = false; Synonyms = { "region", "place" };
		Args = { A("Id", "choice", { Label = "Place"; From = "Regions"; Required = true }), A("Send", "toggle", { Label = "Send them" }), A("Target", "number", { Min = 1; Max = 1e12 }) } };

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
```

`QuestStart` and `QuestAbandon` take free text, as the desk did, so the owner can still type a `Rite...` id. The `Run` refuses a rite for anyone below level 3.

- [ ] **Step 4: Install and run the check**

```bash
python -X utf8 -I tools/admin-console/install_new.py tools/admin-console/live/ServerScriptService.Services.Features.Admin.Meta.luau
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_registry.lua
```
Expected: `PASS console_registry (66 commands)`. `ConsoleArt` isn't installed yet, so the icon lines are skipped.

The new `Meta` child sits under `Features.Admin`. The loader requires it, gets a table without `OnStart`, and does
nothing else.

- [ ] **Step 5: Commit (on the owner's word)**

```bash
git add tools/admin-console/live/ServerScriptService.Services.Features.Admin.Meta.luau tools/admin-console/checks/console_registry.lua
git commit -m "Console 1a: Admin.Meta, card data for the 66 commands, and the registry check"
```

---

### Task 3: The server (levels 0-3, `Dispatch`, argument checks, `Registry`, `Status`)

**Files:**
- Modify: `tools/admin-console/live/ServerScriptService.Services.Features.Admin.luau` (copy of `pre/`):
  - the header comment (lines 1-17);
  - `Shared.Level` (66-71);
  - `C.Ban` (112-123), `C.GiveYen` (226-236), `C.QuestStart` (661-669), `C.Shutdown` (396);
  - `Shared.Lists` (775-805);
  - `snapshot` (812-847);
  - `OnStart` (849-945).
- Modify: `tools/admin-console/live/ReplicatedStorage.Config.Cmdr.luau` (add `Testers`)
- Test: `tools/admin-console/checks/console_play_server.lua` (Task 8 runs it in Play; Step 6 here runs its Edit half)

**Interfaces:**
- Consumes: `StaffConsole.LevelFrom`, `CheckArgs`, `Validate`, `Public`, `SECTIONS`, `LEVEL_NAMES`; `Admin.Meta`.
- Produces:
  - `Shared.Level(P) -> 0..3`.
  - `Shared.Dispatch(P, Command, TargetUserId, Args) -> (ok, message)`, used by the `Run` remote and the Play check.
  - `Shared.Registry(Level) -> { PublicDef }`.
  - `Info()` adds `Registry` and `Sections`.
  - The new `ReplicatedStorage.NHAdmin.Status` RemoteFunction: `() -> { Server, Players, Locked }` (or `nil` for
    level 0).
  - `NHStaff` attribute = the level (0-3); its readers check `>= 1`, so nothing changes for them.

- [ ] **Step 1: Copy the originals into `live/`**

```bash
cp tools/admin-console/pre/ServerScriptService.Services.Features.Admin.luau tools/admin-console/pre/ReplicatedStorage.Config.Cmdr.luau tools/admin-console/live/
```

- [ ] **Step 2: `Config.Cmdr` gains `Testers`**

In `live/ReplicatedStorage.Config.Cmdr.luau`, after the `Admin = { ... };` block, add:

```lua
	-- (console 1a) testers: level 2 (the Test side) in live servers, no moderation beyond level 1's
	Testers = {
	};
```

and in the type at the bottom add `Testers: { number };` after `Admin: { number };`.

- [ ] **Step 3: Levels**

Replace `Shared.Level` (and its comment) with:

```lua
local StaffConsole = require(ReplicatedStorage.Functions.StaffConsole)
local Meta = require(script:WaitForChild(`Meta`))

-- 0 none, 1 moderator, 2 admin, 3 owner (spec §6). Studio: 3, or the server-set NHTestLevel (0-3); NHTestNotAdmin = 0.
function Shared.Level(P: Player): number
	local c = cmdrCfg()
	local Studio = RunService:IsStudio()
	return StaffConsole.LevelFrom({
		Studio = Studio;
		TestLevel = if Studio then P:GetAttribute(`NHTestLevel`) else nil;
		NotAdmin = Studio and P:GetAttribute(`NHTestNotAdmin`) == true;
		Owner = table.find(c.Owner or {}, P.UserId) ~= nil;
		Admin = table.find(c.Admin or {}, P.UserId) ~= nil;
		Tester = table.find(c.Testers or {}, P.UserId) ~= nil;
		Rank = if Studio then 0 else rankOf(P);
	})
end
```

`cmdrCfg()`'s fallback becomes `{ Admin = {}, Owner = {}, Testers = {} }`.

- [ ] **Step 4: The owner rules move to level 3, and moderator bans are capped at 30 days**

- `C.Ban`: replace `if days == 0 and Shared.Level(A) < 2 then ... end` with:

```lua
	local lvl = Shared.Level(A)
	if days == 0 and lvl < 3 then return false, `Permanent bans are owner-only` end
	if days > 30 and lvl < 2 then return false, `Moderators can ban for up to 30 days` end
```

- `C.GiveYen`: `Shared.Level(A) < 2` becomes `Shared.Level(A) < 3`.
- `C.QuestStart`: `Shared.Level(A) < 2` becomes `Shared.Level(A) < 3`.
- `C.Shutdown = { Level = 2; Run = ...`: delete `Level = 2; ` (the metadata's `Level = 3` gates it now).

- [ ] **Step 5: `Lists` gains `Races` and `Gear`, cached for 10 s**

In `Shared.Lists()`:
- change the first line to
  `local L = { Quests = {}; Regions = {}; Clubs = {}; Venues = {}; Segments = {}; Beasts = {}; Races = {}; Gear = {}; Rooms = { ... } }`;
- before `return L`, add:

```lua
	pcall(function() -- (console 1a) the Race card's choices: every sub-race
		for _, R in require(ReplicatedStorage.Lineage).Races do
			for _, S in R.Subs do table.insert(L.Races, { Id = S.Id; Name = S.Name }) end
		end
	end)
	pcall(function() -- (console 1a) the Give gear card's choices
		for _, it in require(ReplicatedStorage.Config.Gear).Items do table.insert(L.Gear, { Id = it.Id; Name = it.Name }) end
		table.sort(L.Gear, function(x, y) return x.Name < y.Name end)
	end)
```

Rename the function to `local function buildLists()`, and add after it:

```lua
local ListsAt, ListsCache = -math.huge, nil
function Shared.Lists()
	if os.clock() - ListsAt > 10 or not ListsCache then ListsCache = buildLists() ListsAt = os.clock() end
	return ListsCache
end
```

- [ ] **Step 6: `Registry`, split `snapshot`, and `Dispatch`**

Add above `snapshot`:

```lua
function Shared.Registry(Level: number)
	local Out = {}
	for Id, D in Meta do
		if D.Level <= Level then table.insert(Out, StaffConsole.Public(Id, D)) end
	end
	table.sort(Out, function(a, b) return a.Title < b.Title end)
	return Out
end
```

Split `snapshot` into the following, then rewrite `snapshot` to call them:
- `local function playerList()`: the `list` loop as it is.
- `local function serverInfo()`: the `Server = {...}` table, with `enemies`, `wolves`, `beasts` and `clock` computed
  inside it.

```lua
local function snapshot(Admin: Player)
	local lvl = Shared.Level(Admin)
	local gear = {}
	pcall(function() for _, it in require(ReplicatedStorage.Config.Gear).Items do table.insert(gear, { Id = it.Id; Name = it.Name; Rarity = it.Rarity }) end end)
	return {
		Level = lvl; Players = playerList(); Log = Log; Gear = gear; Lists = Shared.Lists(); Locked = Locked; Server = serverInfo();
		Registry = Shared.Registry(lvl); Sections = StaffConsole.SECTIONS;
	}
end
```

Move the `Run.OnServerInvoke` body into a module function (it stays the same except for the metadata, level and
argument checks):

```lua
function Shared.Dispatch(P: Player, Command: any, TargetUserId: any, Args: any)
	local lvl = Shared.Level(P)
	if lvl < 1 then return false, `Not staff` end
	if os.clock() - (LastRun[P] or 0) < 0.15 then return false, `Slow down` end
	LastRun[P] = os.clock()
	local def = typeof(Command) == `string` and C[Command] or nil
	local m = def and Meta[Command]
	if not m then return false, `Unknown command` end
	if m.Level > lvl then return false, `Needs {StaffConsole.LEVEL_NAMES[m.Level]}` end
	local okA, clean = StaffConsole.CheckArgs(m.Args, Args, Shared.Lists())
	if not okA then return false, clean end
	Args = clean
	-- (2026-11-17, Roblox text rules) ... (the filter loop, unchanged)
	for _, K in { `Reason`, `Text`, if Command == `GrantTitle` then `Title` else nil } do
		local Raw = Args[K]
		if typeof(Raw) == `string` and Raw:match(`%S`) then
			local OkF, Out = pcall(function()
				return TextService:FilterStringAsync(Raw:sub(1, 300), P.UserId, Enum.TextFilterContext.PublicChat):GetNonChatStringForBroadcastAsync()
			end)
			if not OkF or typeof(Out) ~= `string` then return false, `The text filter is busy: try again in a moment` end
			Args[K] = Out
		end
	end
	local T
	if m.Target ~= `none` then
		T = Players:GetPlayerByUserId(tonumber(TargetUserId) or 0)
		if not T and m.Target == `required` then return false, `Pick a player first` end
		if T and T ~= P and Shared.Level(T) > lvl then return false, `Can't use that on a higher rank` end
	end
	local ok, a, b = pcall(def.Run, P, T, Args)
	if not ok then warn(`[Admin] {Command} failed: {a}`) return false, `Failed: {tostring(a):sub(1, 120)}` end
	log(P, Command, T and T.Name, typeof(Args.Reason) == `string` and Args.Reason or (Args.Amount and tostring(Args.Amount)) or nil)
	return a, b
end
```

`TeleportTo`'s `Position` arrives as a Vector3 through the remote and passes the `position` check. Every `Run` keeps
its own `num` and `str` guards, so the checks are doubled, never weakened.

In `OnStart`:
- `Run.OnServerInvoke = Shared.Dispatch`.
- Add the `Status` remote next to `Info`:

```lua
	local StatusRF = Instance.new(`RemoteFunction`); StatusRF.Name = `Status`; StatusRF.Parent = Folder
	StatusRF.OnServerInvoke = function(P: Player)
		if Shared.Level(P) < 1 then return nil end
		return { Server = serverInfo(); Players = playerList(); Locked = Locked }
	end
```

- At the top of `OnStart`, before the remotes, add the registry check:

```lua
	for Id in C do if not Meta[Id] then warn(`[Admin] {Id} has no Admin.Meta entry: the console can't show it`) end end
	for Id, D in Meta do
		if not C[Id] then warn(`[Admin] Admin.Meta {Id} has no command`) end
		local Ok, Why = StaffConsole.Validate(Id, D)
		if not Ok then warn(`[Admin] Admin.Meta {Why}`) end
	end
```

- `markStaff` keeps `NHStaff` current when a Studio test level changes:

```lua
	local function markStaff(P: Player)
		local function set()
			task.spawn(function()
				local ok, lvl = pcall(Shared.Level, P)
				if P.Parent then P:SetAttribute(`NHStaff`, ok and lvl or 0) end
			end)
		end
		set()
		if RunService:IsStudio() then
			P:GetAttributeChangedSignal(`NHTestLevel`):Connect(set)
			P:GetAttributeChangedSignal(`NHTestNotAdmin`):Connect(set)
		end
	end
```

- Header comment: change "who can use it" to the 0-3 table. Add `Status() -> { Server, Players, Locked }` and
  `Dispatch` to the remotes list. Add the line "1a (2026-11-23): the console's registry (Admin.Meta), levels 0-3,
  argument checks".

- [ ] **Step 7: The Edit half of the server check**

Write `tools/admin-console/checks/console_play_server.lua` now. Its Edit half checks the module loads and its static
pieces. The Play half is Task 8.

```lua
-- console_play_server.lua: run with Server (Play) for the full matrix, or Edit for the static half.
local RunService = game:GetService("RunService")
local Players = game:GetService("Players")
local Admin = require(game.ServerScriptService.Services.Features.Admin)
local Fails = {}
local function Eq(Got, Want, What) if Got ~= Want then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end
Eq(typeof(Admin.Dispatch), "function", "Dispatch")
Eq(typeof(Admin.Registry), "function", "Registry")
Eq(#Admin.Registry(3), 66, "registry at level 3")
-- level 1: Student 12 + Server 4 (Shutdown is level 3); level 2: those 16 + the Test side's 49
Eq(#Admin.Registry(1), 16, "registry at level 1")
Eq(#Admin.Registry(2), 65, "registry at level 2 (all but Shutdown)")
Eq(#Admin.Registry(0), 0, "registry at level 0")
for _, D in Admin.Registry(3) do if D.Run ~= nil then table.insert(Fails, D.Id .. " leaks Run") end end
local L = Admin.Lists()
Eq(typeof(L.Races), "table", "Lists.Races") Eq(typeof(L.Gear), "table", "Lists.Gear")
if #Fails > 0 then return "FAIL " .. #Fails .. "\n" .. table.concat(Fails, "\n") end
return "PASS console_play_server (static: " .. (if RunService:IsRunning() then "Play" else "Edit") .. ")"
```

The counts come from Task 2's table:
- Student is Warn, Mute, Unmute, Freeze, Jail, Spectate, Bring, Goto, Kick, Ban, Unban and Note: 12.
- Server is Announce, ServerLock, BringAll, FreezeAll and Shutdown: 5.
- The Test side is Character 16, Progress 9, School 11, Story 3, World 2, Spawns 6 and Self 2: 49.

The Play run of every command is `console_play_run.lua` (Task 8).

- [ ] **Step 8: Install and run**

```bash
python -X utf8 -I tools/admin-console/install_inplace.py tools/admin-console/pre tools/admin-console/live AdminConsole1a_pre_20261123 ServerScriptService.Services.Features.Admin ReplicatedStorage.Config.Cmdr
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_play_server.lua
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_registry.lua
```
Expected: `PASS console_play_server (static: Edit)` and `PASS console_registry (66 commands)`.

The old `AdminPanel` still works against this server: `Run`, `Info` and `Inspect` keep their shapes. Its Test-side
buttons now say "Needs an admin" to a level-1 moderator, which is intended.

- [ ] **Step 9: Commit (on the owner's word)**

```bash
git add tools/admin-console/live/ServerScriptService.Services.Features.Admin.luau tools/admin-console/live/ReplicatedStorage.Config.Cmdr.luau tools/admin-console/checks/console_play_server.lua
git commit -m "Console 1a: Admin levels 0-3, Dispatch with metadata and argument checks, Registry, Status"
```

---

### Task 4: The console art config

**Files:**
- Create: `tools/admin-console/art_ids.py`
- Create: `tools/admin-console/live/ReplicatedStorage.Config.ConsoleArt.luau` (generated)

**Interfaces:**
- Produces:
  - `ConsoleArt.Icons: { [IconName]: number }`: all 49.
  - `ConsoleArt.Pieces: { [Piece]: number }`: 20 pieces, 0 = not uploaded.
  - `ConsoleArt.Slice: { [Piece]: { number } }`: the 9-slice centre at design px.
  - `ConsoleArt.Image(Name) -> string?`: `rbxassetid://` or nil.

- [ ] **Step 1: Write `art_ids.py`**

```python
"""Write Config.ConsoleArt from the icon ids (and piece ids when uploaded).
usage: python -X utf8 art_ids.py [pieces.json]   (pieces.json: { "Card": 123, ... }, from the group upload lookup)"""
import json, os, sys
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ART = os.path.join(ROOT, "art", "ui", "hud", "console")
icons = json.load(open(os.path.join(ART, "icons", "icon_ids.json"), encoding="utf-8"))
pieces = json.load(open(sys.argv[1], encoding="utf-8")) if len(sys.argv) > 1 else {}
names = sorted(f[:-4] for f in os.listdir(ART) if f.endswith(".png"))
assert len(names) == 20, names
lines = ["--[[ (console 1a) Headmaster's Console art, group 15981569. Generated by tools/admin-console/art_ids.py:",
         "     icons from art/ui/hud/console/icons/icon_ids.json; pieces 0 until uploaded (the UI kit draws them). ]]",
         "local Shared = {}", "Shared.Icons = {"]
for k in sorted(icons): lines.append(f"\t{k} = {int(icons[k])};")
lines += ["}", "Shared.Pieces = {"]
for n in names: lines.append(f"\t{n} = {int(pieces.get(n, 0))};")
lines += ["}", "-- the 9-slice centre of each piece at design px (half the 2x render), a 20 px border (12 on chips and tabs)",
          "Shared.Slice = {"]
for n in names:
    w, h = Image.open(os.path.join(ART, n + ".png")).size
    w, h = w // 2, h // 2
    m = 12 if n in ("Chip", "ChipOn", "ChipDanger", "Tab", "TabOn", "Search", "Tile") else 20
    if n in ("HoldRing", "Medal", "Crest"): m = 0
    lines.append(f"\t{n} = {{ {m}, {m}, {w - m}, {h - m}, {w}, {h} }};")
lines += ["}",
          "function Shared.Image(Name: string): string?",
          "\tlocal Id = Shared.Icons[Name] or Shared.Pieces[Name]",
          "\tif typeof(Id) == \"number\" and Id > 0 then return \"rbxassetid://\" .. Id end",
          "\treturn nil",
          "end",
          "return Shared", ""]
out = os.path.join(ROOT, "tools", "admin-console", "live", "ReplicatedStorage.Config.ConsoleArt.luau")
open(out, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
print("ok", len(icons), "icons,", sum(1 for n in names if pieces.get(n)), "pieces with ids")
```

The `Slice` values are design px, which is half the 2x render. Images are drawn at design size with
`ImageRectSize` left at 0, so `SliceCenter` uses the **source** pixels. The View multiplies the four values by 2
(`Cards.Slice` in Task 7).

- [ ] **Step 2: Run it, install, re-run the registry check**

```bash
python -X utf8 tools/admin-console/art_ids.py
python -X utf8 -I tools/admin-console/install_new.py tools/admin-console/live/ReplicatedStorage.Config.ConsoleArt.luau
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_registry.lua
```
Expected: `ok 49 icons, 0 pieces with ids`, then `PASS console_registry (66 commands)`. The icon lines run now.

- [ ] **Step 3: (Owner gate, any time) upload the 20 pieces**

1. Copy `art/ui/hud/console/*.png` to `art/group-upload-console/`.
2. The owner uploads them to group 15981569.
3. Look up the ids the way the icons were looked up: in the built-in browser on a create.roblox.com page, fetch
   `itemconfiguration.roblox.com/v1/creations/get-assets?assetType=Image&groupId=15981569&limit=100`, newest first,
   and match by name.
4. Write the ids to `tools/admin-console/pieces.json` and re-run `art_ids.py tools/admin-console/pieces.json`.
5. Install again.

Until then the console uses the UI kit's panels.

- [ ] **Step 4: Commit (on the owner's word)**

```bash
git add tools/admin-console/art_ids.py tools/admin-console/live/ReplicatedStorage.Config.ConsoleArt.luau
git commit -m "Console 1a: Config.ConsoleArt (49 icon ids, piece slots)"
```

---

### Task 5: The client model (`StaffConsole.Model`, pure, TDD)

**Files:**
- Create: `tools/admin-console/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.Model.luau`
- Test: `tools/admin-console/checks/console_model.lua`

**Interfaces:**
- Consumes: the public registry entries (Task 3's `Registry`), the snapshot's `Players` rows.
- Produces:
  - `Model.New() -> State` with `{ Side, Section, Selected, Recent, Favs, Feed, Filter, Level }`.
  - `Model.Sides(Level) -> { string }`
  - `Model.SetLevel(S, Level, Sections)`: keeps `Side` and `Section` valid.
  - `Model.Cards(Defs, Side, Section) -> { Def }`: sorted by `Title`.
  - `Model.ToggleFav(S, Id) -> boolean` (now pinned?)
  - `Model.Favourites(Defs, S) -> { Def }`: in pin order, only those in `Defs`.
  - `Model.Pick(S, UserId)`
  - `Model.Rows(Players, Filter, Recent) -> { Row }`
  - `Model.Push(S, Ok, Text, Title)`: the feed holds 5.
  - `Model.Flags(Row) -> { string }`
  - `Model.Section(S, Index, Sections) -> boolean`: the 1-7 keys.
  - `Model.Ready(Def, Values, Selected) -> (boolean, string?)`: can the card run?

- [ ] **Step 1: Write the failing check**

`tools/admin-console/checks/console_model.lua`:

```lua
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

if #Fails > 0 then return "FAIL " .. #Fails .. "\n" .. table.concat(Fails, "\n") end
return "PASS console_model"
```

The check needs a `StaffConsole` parent to exist. If Task 6 hasn't installed the shell yet, `install_new.py` creates
a Folder named `StaffConsole`. Task 6's install replaces it with the ModuleScript and keeps the children.

- [ ] **Step 2: Run it**

Run: `python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_model.lua`
Expected: `FAIL StaffConsole.Model missing`.

- [ ] **Step 3: Write the model**

```lua
--[[ StaffConsole.Model (client, pure): the console's state rules. No Instances; checks/console_model.lua tests it. ]]
local Model = {}
local RECENT_MAX, FEED_MAX = 5, 5

function Model.New()
	return { Side = "Moderate"; Section = "Student"; Selected = nil :: number?; Recent = {} :: { number };
		Favs = {} :: { string }; Feed = {} :: { any }; Filter = ""; Level = 0 }
end

function Model.Sides(Level: number): { string }
	if Level >= 2 then return { "Moderate", "Test" } end
	if Level >= 1 then return { "Moderate" } end
	return {}
end

function Model.SetLevel(S: any, Level: number, Sections: any)
	S.Level = Level
	local Sides = Model.Sides(Level)
	if not table.find(Sides, S.Side) then S.Side = Sides[1] or "Moderate" S.Section = (Sections[S.Side] or {})[1] end
	if not table.find(Sections[S.Side] or {}, S.Section) then S.Section = (Sections[S.Side] or {})[1] end
end

function Model.Section(S: any, Index: number, Sections: any): boolean
	local Name = (Sections[S.Side] or {})[Index]
	if not Name then return false end
	S.Section = Name
	return true
end

function Model.Cards(Defs: any, Side: string, Section: string): any
	local Out = {}
	for _, D in Defs do if D.Side == Side and D.Section == Section then table.insert(Out, D) end end
	table.sort(Out, function(a, b) return a.Title < b.Title end)
	return Out
end

function Model.ToggleFav(S: any, Id: string): boolean
	local I = table.find(S.Favs, Id)
	if I then table.remove(S.Favs, I) return false end
	table.insert(S.Favs, Id)
	return true
end

function Model.Favourites(Defs: any, S: any): any
	local ById = {}
	for _, D in Defs do ById[D.Id] = D end
	local Out = {}
	for _, Id in S.Favs do if ById[Id] then table.insert(Out, ById[Id]) end end
	return Out
end

function Model.Pick(S: any, UserId: number)
	S.Selected = UserId
	local I = table.find(S.Recent, UserId)
	if I then table.remove(S.Recent, I) end
	table.insert(S.Recent, 1, UserId)
	while #S.Recent > RECENT_MAX do table.remove(S.Recent) end
end

function Model.Rows(Players: any, Filter: string, Recent: { number }): any
	local Q = string.lower(Filter or "")
	local Out = {}
	for _, P in Players or {} do
		if Q == "" or string.find(string.lower(P.Name), Q, 1, true) or string.find(string.lower(P.Display or ""), Q, 1, true) then
			table.insert(Out, P)
		end
	end
	table.sort(Out, function(a, b)
		local ra, rb = table.find(Recent, a.UserId) or math.huge, table.find(Recent, b.UserId) or math.huge
		if ra ~= rb then return ra < rb end
		return string.lower(a.Name) < string.lower(b.Name)
	end)
	return Out
end

function Model.Flags(P: any): { string }
	local Out = {}
	if P.Note then table.insert(Out, "NOTE") end
	if P.Muted then table.insert(Out, "MUTED") end
	if P.Frozen then table.insert(Out, "FROZEN") end
	if P.InMenu then table.insert(Out, "IN MENU") end
	if P.God then table.insert(Out, "GOD") end
	return Out
end

function Model.Push(S: any, Ok: boolean, Text: string, Title: string?)
	table.insert(S.Feed, 1, { Ok = Ok; Text = Text; Title = Title or ""; At = os.clock() })
	while #S.Feed > FEED_MAX do table.remove(S.Feed) end
end

function Model.Ready(Def: any, Values: any, Selected: number?): (boolean, string?)
	if Def.Target == "required" and not Selected then return false, "Pick a student on the left first" end
	for _, A in Def.Args or {} do
		local V = Values[A.Name]
		if A.Required and (V == nil or V == "") then return false, `{A.Label or A.Name} is needed` end
	end
	return true
end

return Model
```

Expected flag order in the check: Players[3] has Note, Frozen, InMenu and God. The model emits NOTE, MUTED, FROZEN,
IN MENU, GOD, so Players[3] reads `NOTE,FROZEN,IN MENU,GOD`. That matches the check.

- [ ] **Step 4: Install and run**

```bash
python -X utf8 -I tools/admin-console/install_new.py tools/admin-console/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.Model.luau
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_model.lua
```
Expected: `PASS console_model`.

The installer may create a **Folder** `StaffConsole`. The loader skips Folders and would require `Model`, which has
no `OnStart`, so this is harmless until Task 6.

- [ ] **Step 5: Commit (on the owner's word)**

```bash
git add tools/admin-console/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.Model.luau tools/admin-console/checks/console_model.lua
git commit -m "Console 1a: StaffConsole.Model (sides, cards, favourites, recent, rows, flags, feed)"
```

---

### Task 6: The client tools (`StaffConsole.Tools`), moved from the desk

**Files:**
- Create: `tools/admin-console/live/...Controllers.Gui.StaffConsole.Tools.luau`
- Read: `tools/admin-console/pre/...Controllers.Gui.AdminPanel.luau`:
  - the Fly, Noclip, ESP and Ctrl+click helpers: `setFly`, `setNoclip`, `setEsp`, and the `InputBegan` handler near
    lines 880-889;
  - the `Client` event handler (893-899).

**Interfaces:**
- Consumes: a `Run(Id, Args?, Target?)` function the shell passes in `Tools.Init`.
- Produces:
  - `Tools.Init(Run: (string, any?, number?) -> ())`
  - `Tools.Defs: { Def }`: client cards with `Local = true`, so the View draws them like server cards and the shell
    calls `Tools.Do(Id, Values, Selected)` instead of the remote.
  - `Tools.Do(Id, Values, Selected) -> (boolean, string)`
  - `Tools.State() -> { Fly, Noclip, Esp, ClickTp }`

- [ ] **Step 1: Move the code**

Copy these from `pre/...AdminPanel.luau` **unchanged** into the new module:
- the self-tool state and helpers (`Tools`, `Conns`, `setFly`, `setNoclip`, `setEsp` and their locals);
- the Ctrl+click handler;
- the `Client` event (`Spectate`) handler;
- the `CharacterAdded` re-fly.

Then wrap them:

```lua
--[[ StaffConsole.Tools (client): the console's own-client tools, moved from the 1.18 desk (AdminPanel) unchanged:
	Fly (WASD / Space / Ctrl, Shift for speed), Noclip, ESP (names + health through walls), Ctrl+click teleport, Stop
	spectating, and the Inspect card (Features.Admin's Inspect remote). Level 2 (the Test side), except Stop
	spectating (level 1, the Student section). No OnStart: StaffConsole calls Init. ]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local Player = Players.LocalPlayer
local Tools = {}
local Run = nil :: any
local On = { Fly = false; Noclip = false; Esp = false; ClickTp = false }
-- (paste: the desk's setFly / setNoclip / setEsp and their locals, renaming its `Tools` table to `On`)

local function card(Id, Section, Title, Help, Icon, Level, Target, Synonyms)
	return { Id = Id; Side = if Level >= 2 then "Test" else "Moderate"; Section = Section; Title = Title; Help = Help; Icon = Icon;
		Level = Level; Target = Target; Args = {}; Danger = false; Synonyms = Synonyms; Local = true }
end
Tools.Defs = {
	card("ToolFly", "Self", "Fly", "WASD, Space up, Ctrl down, Shift faster (again to land)", "Speed", 2, "none", { "fly" }),
	card("ToolNoclip", "Self", "Noclip", "Walk through walls (again to stop)", "Teleport", 2, "none", { "clip" }),
	card("ToolEsp", "Self", "ESP", "Names and health through walls", "Spectate", 2, "none", { "wallhack", "esp" }),
	card("ToolClickTp", "Self", "Ctrl+click teleport", "Hold Ctrl and click the world to go there", "Teleport", 2, "none", { "click tp" }),
	card("ToolUnspectate", "Student", "Stop spectating", "Your camera back on you", "Spectate", 1, "none", { "unspectate" }),
	card("ToolInspect", "Progress", "Inspect", "Their loaded slot, read only (in the side panel)", "SecProgress", 2, "required", { "inspector" }),
}

function Tools.State() return table.clone(On) end

function Tools.Do(Id: string, _Values: any, Selected: number?): (boolean, string)
	if Id == "ToolFly" then On.Fly = not On.Fly setFly(On.Fly) return true, if On.Fly then "Flying" else "Landed" end
	if Id == "ToolNoclip" then On.Noclip = not On.Noclip setNoclip(On.Noclip) return true, if On.Noclip then "Noclip on" else "Noclip off" end
	if Id == "ToolEsp" then On.Esp = not On.Esp setEsp(On.Esp) return true, if On.Esp then "ESP on" else "ESP off" end
	if Id == "ToolClickTp" then On.ClickTp = not On.ClickTp return true, if On.ClickTp then "Ctrl+click teleport on" else "Ctrl+click teleport off" end
	if Id == "ToolUnspectate" then
		local H = Player.Character and Player.Character:FindFirstChildWhichIsA("Humanoid")
		if H then workspace.CurrentCamera.CameraSubject = H end
		return true, "Camera back on you"
	end
	if Id == "ToolInspect" then return Selected ~= nil, if Selected then "Inspecting" else "Pick a student first" end
	return false, "Unknown tool"
end

function Tools.Inspect(UserId: number): any
	local F = ReplicatedStorage:FindFirstChild("NHAdmin")
	if not F then return nil end
	local Ok, R = pcall(F.Inspect.InvokeServer, F.Inspect, UserId)
	return if Ok then R else nil
end

function Tools.Init(RunFn: any)
	Run = RunFn
	-- (paste: the desk's Ctrl+click InputBegan handler, calling Run("TeleportTo", { Position = m.Hit.Position }))
	-- (paste: the desk's Client OnClientEvent Spectate handler)
	Player.CharacterAdded:Connect(function() if On.Fly then task.wait(1) setFly(true) end end)
end

return Tools
```

The Ctrl+click handler checks `On.ClickTp` and `UserInputService:IsKeyDown(Enum.KeyCode.LeftControl)` exactly as the
desk did. `Run` is the shell's run with the signature `(Id, Args, Target)`.

- [ ] **Step 2: Parse check**

Install:

```bash
python -X utf8 -I tools/admin-console/install_new.py "tools/admin-console/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.Tools.luau"
```

Expected: the path and a byte count, with no `PARSE FAIL`.

Then run this in Edit:

```lua
local T = require(game.StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.Tools:Clone())
return (#T.Defs == 6 and typeof(T.Do) == "function") and "PASS tools" or "FAIL tools"
```

Expected: `PASS tools`. Requiring it in Edit has no `LocalPlayer`. If `Players.LocalPlayer` is nil there, guard any
top-level use with `if Player then`.

- [ ] **Step 3: Commit (on the owner's word)**

```bash
git add "tools/admin-console/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.Tools.luau"
git commit -m "Console 1a: StaffConsole.Tools (the desk's self tools and the inspector as cards)"
```

---

### Task 7: The shell, view, cards and palette

**Files:**
- Create: `live/...Controllers.Gui.StaffConsole.luau` (the shell: `OnStart`)
- Create: `live/...Controllers.Gui.StaffConsole.View.luau`
- Create: `live/...Controllers.Gui.StaffConsole.Cards.luau`
- Create: `live/...Controllers.Gui.StaffConsole.Palette.luau`

**Interfaces:**
- Consumes: `Model` (Task 5), `Tools` (Task 6), `StaffConsole` (Task 1), `ConsoleArt` (Task 4); the remotes `Info`,
  `Status`, `Run` and `Inspect` (Task 3); `Kit` (`ReplicatedStorage.UI.Components`: `AutoScale`, `Panel`, `Button`,
  `Phone`, `ReducedMotion`, `PlaySound`, `Toast`) and `Theme.FontFaces`.
- Produces:
  - `StaffConsole.Toggle(On: boolean?)`, `StaffConsole.IsOpen()`.
  - The Studio probe through `HudState.Probe`: `Console(Cmd, ...)` with these commands:
    - `Open`, `Close`;
    - `Side(Name)`, `Section(Name)`;
    - `Search(Q) -> { Ids }`;
    - `Info() -> { Open, Side, Section, Cards = { Ids }, Feed = { Text }, Level }`;
    - `Pick(UserId)`.
  - `ScreenGui` `NHStaffConsole`: `Board` (1600 x 900 design) → `TopBar`, `Rail`, `Centre`, `Context`, `Palette`.
    Cards are named `Card_<Id>` with a `Run` button; option controls are named `Opt_<ArgName>`.

**Layout (design px, from the rendered pieces):**

| Region | Rect | Art (fallback) |
|---|---|---|
| Board | 0,0 1600x900 | `Frame` (Kit.Panel) |
| Crest | 768,14 64x72 | `Crest` (none) |
| Side switch | 56,22 two 150x44, 8 apart | `Tab` / `TabOn` (Kit.Button) |
| Palette box | 380,24 290x40, "Ctrl+K  Find any action…" 20 px | `Search` (Frame) |
| Status tiles | 880,18 four 150x56, 10 apart: Players, FPS, Clock, Lock | `Tile` (Frame) |
| Rail | 40,110 394x744; search 92,126 290x40; rows 91,180 292x70, step 76 (scrolling to 840) | `Side`, `Search`, `Row` / `RowOn` |
| Section tabs | 450,110 across 772: width = floor((772 - (n-1)*6) / n), height 44; icon 32 + name 20 | `Tab` / `TabOn` |
| Favourites strip | 450,160 772x40 chips (hidden when empty; then cards start at 160) | `Chip` / `ChipOn` |
| Cards | 450,206 scrolling 772x540; 2 columns 380x168, 12 apart, step 180 | `Card` / `CardHot` |
| Feed | 450,756 774x120; the last 5 results, 20 px, crimson when refused | `Feed` |
| Context | 1240,110 320x696 (the Close button sits below it at 1440,820) | `Rail` |
| Bottom buttons | y 820, 120x44: Close at 1440; on phones also Students at 1180 and Details at 1310 | (Frame) |

**Card (380 x 168):**
- the icon well at 16,16, 56x56 (`ConsoleArt.Image(Def.Icon)`, falling back to the section icon `Sec<Section>`);
- the title at 84,14, 260 wide, 22 bold;
- the help at 84,44, 280x44, 20, wrapped;
- the options row at 16,100, 252x44, scrolling horizontally;
- the Run button at 276,112, 92x44 ("Run"; "Hold" on danger cards, with the `HoldRing` 44x44 over it);
- right-click or Y pins it (`Model.ToggleFav`).

**Options per arg kind:**
- `choice` with `Choices` and 5 or fewer: chips;
- `choice` with more than 5, or with `From`: a chip that opens the picker (a 360x420 scrolling list over the card
  grid, 20 px rows);
- `number`: a 100x44 TextBox, digits only;
- `text`: a 220x44 TextBox;
- `toggle`: an On/Off chip;
- `position`: no control (the card's Run says "Use Ctrl+click").

- [ ] **Step 1: `Cards.luau`**

```lua
--[[ StaffConsole.Cards (client): one action card, its option controls, the list picker and the hold ring (spec §4-§5). ]]
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Kit = require(ReplicatedStorage:WaitForChild("UI"):WaitForChild("Components"))
local Theme = Kit.Theme
local Art = require(ReplicatedStorage:WaitForChild("Config"):WaitForChild("ConsoleArt"))
local SC = require(ReplicatedStorage:WaitForChild("Functions"):WaitForChild("StaffConsole"))
local Cards = {}

local rgb = Color3.fromRGB
Cards.COL = {
	Iron = rgb(26, 23, 29); IronHi = rgb(44, 39, 48); Velvet = rgb(54, 10, 22); Brass = rgb(214, 170, 96);
	Bone = rgb(236, 226, 206); Dim = rgb(196, 184, 166); Crimson = rgb(214, 50, 62); Good = rgb(150, 200, 140);
}
local COL = Cards.COL
local FACE = { Body = Theme.FontFaces.Body; Bold = Theme.FontFaces.BodyBold; Title = Font.new(Theme.FontFaces.Title.Family, Enum.FontWeight.Bold) }

function Cards.New(Class: string, Props: any, Parent: Instance?): any
	local I = Instance.new(Class)
	for K, V in Props do (I :: any)[K] = V end
	if Parent then I.Parent = Parent end
	return I
end
local New = Cards.New

-- an art piece as a sliced ImageLabel, or a plain iron frame until its id exists
function Cards.Piece(Name: string, Parent: Instance, Pos: UDim2, Size: UDim2, Extra: any?): GuiObject
	local Img = Art.Image(Name)
	local Obj
	if Img then
		local S = Art.Slice[Name]
		Obj = New("ImageLabel", { Name = Name; Image = Img; BackgroundTransparency = 1; Position = Pos; Size = Size;
			ScaleType = if S[1] > 0 then Enum.ScaleType.Slice else Enum.ScaleType.Stretch;
			SliceCenter = Rect.new(S[1] * 2, S[2] * 2, S[3] * 2, S[4] * 2); SliceScale = 0.5 }, Parent)
	else
		Obj = New("Frame", { Name = Name; BackgroundColor3 = COL.Iron; BorderSizePixel = 0; Position = Pos; Size = Size }, Parent)
		New("UICorner", { CornerRadius = UDim.new(0, 10) }, Obj)
		New("UIStroke", { Color = COL.Brass; Thickness = 1.5; Transparency = 0.35 }, Obj)
	end
	for K, V in Extra or {} do (Obj :: any)[K] = V end
	return Obj
end

function Cards.Text(Parent: Instance, Name: string, Text: string, Size: number, Face: Font, Color: Color3, Pos: UDim2, Box: UDim2, Wrap: boolean?): TextLabel
	return New("TextLabel", { Name = Name; Text = Text; TextSize = math.max(20, Size); FontFace = Face; TextColor3 = Color;
		BackgroundTransparency = 1; Position = Pos; Size = Box; TextWrapped = Wrap == true; TextTruncate = if Wrap then Enum.TextTruncate.None else Enum.TextTruncate.AtEnd;
		TextXAlignment = Enum.TextXAlignment.Left; TextYAlignment = Enum.TextYAlignment.Top }, Parent)
end

function Cards.Icon(Parent: Instance, Def: any, Pos: UDim2, Size: number)
	local Img = Art.Image(Def.Icon) or Art.Image("Sec" .. tostring(Def.Section))
	if not Img then return end
	New("ImageLabel", { Name = "Icon"; Image = Img; BackgroundTransparency = 1; Position = Pos; Size = UDim2.fromOffset(Size, Size) }, Parent)
end

local function chip(Parent: Instance, Name: string, Text: string, On: boolean, Danger: boolean?, W: number?): TextButton
	local Piece = if Danger then "ChipDanger" elseif On then "ChipOn" else "Chip"
	local Holder = Cards.Piece(Piece, Parent, UDim2.new(), UDim2.fromOffset(W or 96, 40))
	local B = New("TextButton", { Name = Name; Text = Text; TextSize = 20; FontFace = FACE.Bold; TextColor3 = if On then COL.Iron else COL.Bone;
		BackgroundTransparency = if Art.Image(Piece) then 1 else 0; BackgroundColor3 = if On then COL.Brass else COL.IronHi;
		Size = UDim2.fromScale(1, 1); AutoButtonColor = true; Selectable = true }, Holder)
	return B
end

-- Values[ArgName] holds the card's current option values (the shell keeps one table per card id).
-- Opts = { OnPick: (Arg, Choices, Done) -> () } opens the shared picker for long lists.
function Cards.Options(Row: Instance, Def: any, Values: any, Lists: any, Opts: any)
	for _, A in Def.Args do
		local Label = A.Label or A.Name
		if A.Kind == "choice" then
			local Choices = A.Choices
			if Choices and #Choices <= 5 and not A.From then
				for _, C in Choices do
					local Text = if A.Name == "Days" then (if C == 0 then "Forever" else C .. "d") elseif A.Name == "Tier" and typeof(C) == "number" then ({ "I", "II", "III" })[C] else tostring(C)
					local B = chip(Row, "Opt_" .. A.Name .. "_" .. tostring(C), Text, Values[A.Name] == C, A.Name == "Days" and C == 0)
					B.Activated:Connect(function() Values[A.Name] = C Opts.Redraw() end)
				end
			else
				local List = Choices or (Lists and Lists[A.From]) or {}
				local Cur = Values[A.Name]
				local Shown = Label
				for _, It in List do if It == Cur or (typeof(It) == "table" and It.Id == Cur) then Shown = if typeof(It) == "table" then It.Name else tostring(It) end end
				local B = chip(Row, "Opt_" .. A.Name, Shown .. " ▾", Cur ~= nil, false, 200)
				B.Activated:Connect(function()
					Opts.OnPick(A, List, function(V) Values[A.Name] = V Opts.Redraw() end)
				end)
			end
		elseif A.Kind == "number" or A.Kind == "text" then
			local Box = New("TextBox", { Name = "Opt_" .. A.Name; PlaceholderText = Label; Text = if Values[A.Name] ~= nil then tostring(Values[A.Name]) else "";
				TextSize = 20; FontFace = FACE.Body; TextColor3 = COL.Bone; PlaceholderColor3 = COL.Dim; BackgroundColor3 = COL.IronHi;
				ClearTextOnFocus = false; Size = UDim2.fromOffset(if A.Kind == "number" then 100 else 220, 40); TextXAlignment = Enum.TextXAlignment.Left }, Row)
			New("UICorner", { CornerRadius = UDim.new(0, 8) }, Box)
			New("UIPadding", { PaddingLeft = UDim.new(0, 10) }, Box)
			Box:GetPropertyChangedSignal("Text"):Connect(function()
				if A.Kind == "number" then
					local Clean = string.gsub(Box.Text, "[^%d%-%.]", "")
					if Clean ~= Box.Text then Box.Text = Clean return end
					Values[A.Name] = tonumber(Clean)
				else
					Values[A.Name] = Box.Text
				end
			end)
		elseif A.Kind == "toggle" then
			local On = Values[A.Name] ~= false
			Values[A.Name] = On
			local B = chip(Row, "Opt_" .. A.Name, Label .. (if On then ": on" else ": off"), On, false, 160)
			B.Activated:Connect(function() Values[A.Name] = not (Values[A.Name] ~= false) Opts.Redraw() end)
		end
	end
end

-- the hold ring: a danger card's Run button runs only after a 0.8 s hold; letting go early cancels
function Cards.Hold(Button: GuiButton, Ring: GuiObject?, Reduced: boolean, OnDone: () -> ())
	local Holding = nil :: any
	local function stop()
		if Holding then Holding.Tween:Cancel() Holding = nil end
		if Ring then (Ring :: any).ImageTransparency = 1 end
	end
	Button.InputBegan:Connect(function(I)
		local T = I.UserInputType
		if not (T == Enum.UserInputType.MouseButton1 or T == Enum.UserInputType.Touch or I.KeyCode == Enum.KeyCode.ButtonA or I.KeyCode == Enum.KeyCode.Return) then return end
		stop()
		local Token = {}
		local V = Instance.new("NumberValue")
		local Tw = TweenService:Create(V, TweenInfo.new(SC.DANGER_HOLD, Enum.EasingStyle.Linear), { Value = 1 })
		Holding = { Token = Token; Tween = Tw }
		if Ring then
			V.Changed:Connect(function(X) (Ring :: any).ImageTransparency = 1 - X * 0.9 if not Reduced then (Ring :: any).Rotation = X * 360 end end)
		end
		Tw.Completed:Connect(function(State)
			if State == Enum.PlaybackState.Completed and Holding and Holding.Token == Token then
				Holding = nil
				if Ring then (Ring :: any).ImageTransparency = 1 end
				OnDone()
			end
			V:Destroy()
		end)
		Tw:Play()
	end)
	Button.InputEnded:Connect(stop)
	Button.MouseLeave:Connect(stop)
end

-- one card. Opts = { Values, Lists, Selected, Fav: boolean, OnRun(Def, Values), OnFav(Def), OnPick, Redraw, Reduced }
function Cards.Card(Parent: Instance, Def: any, Pos: UDim2, Opts: any): GuiObject
	local C = Cards.Piece("Card", Parent, Pos, UDim2.fromOffset(380, 168), { Name = "Card_" .. Def.Id })
	Cards.Icon(C, Def, UDim2.fromOffset(16, 16), 56)
	Cards.Text(C, "Title", (if Opts.Fav then "★ " else "") .. Def.Title, 22, FACE.Bold, if Def.Danger then COL.Crimson else COL.Bone, UDim2.fromOffset(84, 14), UDim2.fromOffset(260, 28))
	Cards.Text(C, "Help", Def.Help, 20, FACE.Body, COL.Dim, UDim2.fromOffset(84, 44), UDim2.fromOffset(280, 50), true)
	local Row = New("ScrollingFrame", { Name = "Options"; BackgroundTransparency = 1; Position = UDim2.fromOffset(16, 104); Size = UDim2.fromOffset(252, 48);
		CanvasSize = UDim2.new(); AutomaticCanvasSize = Enum.AutomaticSize.X; ScrollingDirection = Enum.ScrollingDirection.X; ScrollBarThickness = 4; Selectable = false }, C)
	New("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal; Padding = UDim.new(0, 6); SortOrder = Enum.SortOrder.LayoutOrder }, Row)
	Cards.Options(Row, Def, Opts.Values, Opts.Lists, Opts)
	local NeedsPos = false
	for _, A in Def.Args do if A.Kind == "position" then NeedsPos = true end end
	local Label = if NeedsPos then "Ctrl+click" elseif Def.Danger then "Hold" else "Run"
	local RunB = New("TextButton", { Name = "Run"; Text = Label; TextSize = 20; FontFace = FACE.Bold; TextColor3 = if Def.Danger then COL.Bone else COL.Iron;
		BackgroundColor3 = if Def.Danger then COL.Velvet else COL.Brass; Position = UDim2.fromOffset(276, 112); Size = UDim2.fromOffset(92, 44);
		AutoButtonColor = true; Selectable = not NeedsPos; Active = not NeedsPos }, C)
	New("UICorner", { CornerRadius = UDim.new(0, 8) }, RunB)
	if not NeedsPos then
		if Def.Danger then
			local Ring = New("ImageLabel", { Name = "HoldRing"; Image = Art.Image("HoldRing") or "rbxassetid://0"; BackgroundTransparency = 1; ImageTransparency = 1;
				AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromOffset(44, 44); ZIndex = 3 }, RunB)
			Cards.Hold(RunB, Ring, Opts.Reduced, function() Opts.OnRun(Def, Opts.Values) end)
		else
			RunB.Activated:Connect(function() Opts.OnRun(Def, Opts.Values) end)
		end
	end
	C.InputBegan:Connect(function(I)
		if I.UserInputType == Enum.UserInputType.MouseButton2 then Opts.OnFav(Def) end
	end)
	if not Opts.Reduced then
		C.MouseEnter:Connect(function() C.Position = Pos - UDim2.fromOffset(0, 2) end)
		C.MouseLeave:Connect(function() C.Position = Pos end)
	end
	return C
end

-- the shared list picker over the card grid
function Cards.Picker(Parent: Instance, Title: string, List: any, Done: (any) -> ()): GuiObject
	local P = Cards.Piece("Side", Parent, UDim2.fromOffset(656, 170), UDim2.fromOffset(360, 460), { Name = "Picker"; ZIndex = 20 })
	Cards.Text(P, "Title", Title, 22, FACE.Bold, COL.Brass, UDim2.fromOffset(20, 14), UDim2.fromOffset(260, 28))
	local X = New("TextButton", { Name = "Close"; Text = "✕"; TextSize = 22; FontFace = FACE.Bold; TextColor3 = COL.Bone; BackgroundTransparency = 1;
		Position = UDim2.fromOffset(308, 8); Size = UDim2.fromOffset(40, 40); ZIndex = 21 }, P)
	X.Activated:Connect(function() P:Destroy() end)
	local L = New("ScrollingFrame", { Name = "List"; BackgroundTransparency = 1; Position = UDim2.fromOffset(16, 56); Size = UDim2.fromOffset(328, 390);
		CanvasSize = UDim2.new(); AutomaticCanvasSize = Enum.AutomaticSize.Y; ScrollBarThickness = 6; ZIndex = 21 }, P)
	New("UIListLayout", { Padding = UDim.new(0, 4) }, L)
	for _, It in List do
		local V, Text = It, tostring(It)
		if typeof(It) == "table" then V, Text = It.Id, It.Name or tostring(It.Id) end
		local B = New("TextButton", { Name = "Pick_" .. tostring(V); Text = Text; TextSize = 20; FontFace = FACE.Body; TextColor3 = COL.Bone; BackgroundColor3 = COL.IronHi;
			Size = UDim2.new(1, -8, 0, 40); TextXAlignment = Enum.TextXAlignment.Left; ZIndex = 22 }, L)
		New("UIPadding", { PaddingLeft = UDim.new(0, 10) }, B)
		B.Activated:Connect(function() P:Destroy() Done(V) end)
	end
	return P
end

Cards.FACE = FACE
return Cards
```

- [ ] **Step 2: `View.luau`**

```lua
--[[ StaffConsole.View (client): draws the console from the shell's state (spec §3). Redraw(Ctx) rebuilds the dynamic
	parts; the board and frame are built once. Ctx = { S (Model state), Info, Status, Defs (server + tools), Values,
	Lists, Inspect, Handlers = { Side, Section, Pick, Filter, Run, Fav, Palette, Close, Pick } }. ]]
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local Kit = require(ReplicatedStorage:WaitForChild("UI"):WaitForChild("Components"))
local Art = require(ReplicatedStorage:WaitForChild("Config"):WaitForChild("ConsoleArt"))
local Cards = require(script.Parent:WaitForChild("Cards"))
local Model = require(script.Parent:WaitForChild("Model"))
local New, Piece, Text, COL, FACE = Cards.New, Cards.Piece, Cards.Text, Cards.COL, Cards.FACE
local View = {}

function View.Build(): any
	local Gui = New("ScreenGui", { Name = "NHStaffConsole"; ResetOnSpawn = false; DisplayOrder = 40; IgnoreGuiInset = true; Enabled = false;
		ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, Players.LocalPlayer:WaitForChild("PlayerGui"))
	New("TextButton", { Name = "Scrim"; Text = ""; AutoButtonColor = false; Selectable = false; BackgroundColor3 = Color3.new(0, 0, 0);
		BackgroundTransparency = 0.45; Size = UDim2.fromScale(1, 1) }, Gui)
	local Board = New("Frame", { Name = "Board"; BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5);
		Size = UDim2.fromOffset(1600, 900) }, Gui)
	if Kit.Phone and Kit.Phone() then Kit.AutoScale(Gui) else Kit.AutoScale(Gui, { fitWidth = 1600; fitHeight = 900; fitMargin = 16 }) end
	local Frame = Piece("Frame", Board, UDim2.new(), UDim2.fromScale(1, 1))
	if not Art.Image("Frame") then (Frame :: any).BackgroundColor3 = Color3.fromRGB(18, 16, 21) end
	if Art.Image("Crest") then New("ImageLabel", { Name = "Crest"; Image = Art.Image("Crest"); BackgroundTransparency = 1; Position = UDim2.fromOffset(768, 14); Size = UDim2.fromOffset(64, 72) }, Board) end
	return { Gui = Gui; Board = Board; Dyn = nil :: Instance? }
end

local function tile(Parent: Instance, X: number, Name: string, Label: string, Value: string, OnClick: (() -> ())?)
	local T = Piece("Tile", Parent, UDim2.fromOffset(X, 18), UDim2.fromOffset(150, 56), { Name = "Tile_" .. Name })
	Text(T, "Label", Label, 20, FACE.Body, COL.Dim, UDim2.fromOffset(12, 4), UDim2.fromOffset(130, 24))
	Text(T, "Value", Value, 22, FACE.Bold, COL.Bone, UDim2.fromOffset(12, 26), UDim2.fromOffset(130, 28))
	if OnClick then
		local B = New("TextButton", { Name = "Hit"; Text = ""; BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1) }, T)
		B.Activated:Connect(OnClick)
	end
end

local function topBar(Dyn: Instance, Ctx: any)
	local S, H = Ctx.S, Ctx.Handlers
	for I, Side in Model.Sides(S.Level) do
		local On = Side == S.Side
		local P = Piece(if On then "TabOn" else "Tab", Dyn, UDim2.fromOffset(56 + (I - 1) * 158, 22), UDim2.fromOffset(150, 44), { Name = "Side_" .. Side })
		local B = New("TextButton", { Name = "Hit"; Text = string.upper(Side); TextSize = 22; FontFace = FACE.Bold; TextColor3 = if On then COL.Iron else COL.Bone;
			BackgroundTransparency = if Art.Image("Tab") then 1 else 0; BackgroundColor3 = if On then COL.Brass else COL.IronHi; Size = UDim2.fromScale(1, 1) }, P)
		B.Activated:Connect(function() H.Side(Side) end)
	end
	local Pal = Piece("Search", Dyn, UDim2.fromOffset(380, 24), UDim2.fromOffset(290, 40), { Name = "PaletteBox" })
	local PB = New("TextButton", { Name = "Hit"; Text = "Ctrl+K  Find any action…"; TextSize = 20; FontFace = FACE.Body; TextColor3 = COL.Dim; BackgroundTransparency = 1;
		Size = UDim2.fromScale(1, 1); TextXAlignment = Enum.TextXAlignment.Left }, Pal)
	New("UIPadding", { PaddingLeft = UDim.new(0, 14) }, PB)
	PB.Activated:Connect(H.Palette)
	local St = Ctx.Status and Ctx.Status.Server or {}
	tile(Dyn, 880, "Players", "Players", `{St.Players or "?"}/{St.MaxPlayers or "?"}`, nil)
	tile(Dyn, 1040, "Fps", "Server FPS", tostring(St.Fps or "?"), nil)
	tile(Dyn, 1200, "Clock", "School time", St.Clock or "—", function() if S.Level >= 2 then H.Side("Test") H.Section("School") end end)
	tile(Dyn, 1360, "Lock", "Server", if Ctx.Status and Ctx.Status.Locked then "Locked" else "Open", function() H.Side("Moderate") H.Section("Server") end)
end

local function rail(Dyn: Instance, Ctx: any)
	local S, H = Ctx.S, Ctx.Handlers
	Piece("Side", Dyn, UDim2.fromOffset(40, 110), UDim2.fromOffset(394, 744), { Name = "Rail" })
	local Box = New("TextBox", { Name = "StudentSearch"; PlaceholderText = "Search students"; Text = S.Filter; TextSize = 20; FontFace = FACE.Body;
		TextColor3 = COL.Bone; PlaceholderColor3 = COL.Dim; BackgroundColor3 = COL.IronHi; ClearTextOnFocus = false;
		Position = UDim2.fromOffset(92, 126); Size = UDim2.fromOffset(290, 40); TextXAlignment = Enum.TextXAlignment.Left }, Dyn)
	New("UIPadding", { PaddingLeft = UDim.new(0, 12) }, Box)
	Box.FocusLost:Connect(function() H.Filter(Box.Text) end)
	Box:GetPropertyChangedSignal("Text"):Connect(function() S.Filter = Box.Text end)
	local L = New("ScrollingFrame", { Name = "Rows"; BackgroundTransparency = 1; Position = UDim2.fromOffset(91, 180); Size = UDim2.fromOffset(300, 660);
		CanvasSize = UDim2.new(); AutomaticCanvasSize = Enum.AutomaticSize.Y; ScrollBarThickness = 6; Selectable = false }, Dyn)
	New("UIListLayout", { Padding = UDim.new(0, 6) }, L)
	local Rows = Model.Rows(Ctx.Status and Ctx.Status.Players or (Ctx.Info and Ctx.Info.Players) or {}, S.Filter, S.Recent)
	for _, P in Rows do
		local On = P.UserId == S.Selected
		local R = Piece(if On then "RowOn" else "Row", L, UDim2.new(), UDim2.fromOffset(292, 70), { Name = "Row_" .. P.UserId })
		Text(R, "Name", P.Display ~= P.Name and `{P.Display} (@{P.Name})` or P.Name, 22, FACE.Bold, if On then COL.Brass else COL.Bone, UDim2.fromOffset(14, 6), UDim2.fromOffset(268, 28))
		local Flags = Model.Flags(P)
		Text(R, "Sub", `{P.Sub or P.Race or "?"} · {P.Ping or 0} ms` .. (if #Flags > 0 then "  " .. table.concat(Flags, " ") else ""), 20, FACE.Body,
			if #Flags > 0 then COL.Crimson else COL.Dim, UDim2.fromOffset(14, 36), UDim2.fromOffset(268, 26))
		local B = New("TextButton", { Name = "Hit"; Text = ""; BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1) }, R)
		B.Activated:Connect(function() H.Pick(P.UserId) end)
	end
end

local function sections(Dyn: Instance, Ctx: any)
	local S, H = Ctx.S, Ctx.Handlers
	local List = (Ctx.Info and Ctx.Info.Sections or {})[S.Side] or {}
	local N = math.max(1, #List)
	local W = math.floor((Ctx.W - (N - 1) * 6) / N)
	for I, Name in List do
		local On = Name == S.Section
		local P = Piece(if On then "TabOn" else "Tab", Dyn, UDim2.fromOffset(Ctx.X + (I - 1) * (W + 6), 110), UDim2.fromOffset(W, 44), { Name = "Section_" .. Name })
		local B = New("TextButton", { Name = "Hit"; Text = ""; BackgroundTransparency = if Art.Image("Tab") then 1 else 0; BackgroundColor3 = if On then COL.Brass else COL.IronHi; Size = UDim2.fromScale(1, 1) }, P)
		local Img = Art.Image("Sec" .. Name)
		local TX = 8
		if Img and W >= 140 then New("ImageLabel", { Image = Img; BackgroundTransparency = 1; Position = UDim2.fromOffset(6, 6); Size = UDim2.fromOffset(32, 32) }, P) TX = 42 end
		Text(P, "Label", Name, 20, FACE.Bold, if On then COL.Iron else COL.Bone, UDim2.fromOffset(TX, 10), UDim2.fromOffset(W - TX - 4, 26))
		B.Activated:Connect(function() H.Section(Name) end)
	end
end

local function grid(Dyn: Instance, Ctx: any)
	local S, H = Ctx.S, Ctx.Handlers
	local Favs = Model.Favourites(Ctx.Defs, S)
	local Top = 160
	if #Favs > 0 then
		local Strip = New("ScrollingFrame", { Name = "Favourites"; BackgroundTransparency = 1; Position = UDim2.fromOffset(Ctx.X, 160); Size = UDim2.fromOffset(Ctx.W, 44);
			CanvasSize = UDim2.new(); AutomaticCanvasSize = Enum.AutomaticSize.X; ScrollingDirection = Enum.ScrollingDirection.X; ScrollBarThickness = 4 }, Dyn)
		New("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal; Padding = UDim.new(0, 6) }, Strip)
		for _, D in Favs do
			local B = New("TextButton", { Name = "Fav_" .. D.Id; Text = "★ " .. D.Title; TextSize = 20; FontFace = FACE.Bold; TextColor3 = COL.Iron; BackgroundColor3 = COL.Brass;
				AutomaticSize = Enum.AutomaticSize.X; Size = UDim2.fromOffset(0, 40) }, Strip)
			New("UIPadding", { PaddingLeft = UDim.new(0, 12); PaddingRight = UDim.new(0, 12) }, B)
			B.Activated:Connect(function() H.Side(D.Side) H.Section(D.Section) end)
		end
		Top = 206
	end
	local G = New("ScrollingFrame", { Name = "Cards"; BackgroundTransparency = 1; Position = UDim2.fromOffset(Ctx.X, Top); Size = UDim2.fromOffset(Ctx.W + 8, 746 - Top);
		CanvasSize = UDim2.new(); AutomaticCanvasSize = Enum.AutomaticSize.Y; ScrollBarThickness = 6; Selectable = false }, Dyn)
	local List = Model.Cards(Ctx.Defs, S.Side, S.Section)
	local Cols = math.max(1, math.floor((Ctx.W + 12) / 392))
	for I, D in List do
		local Col, Row = (I - 1) % Cols, (I - 1) // Cols
		Ctx.Values[D.Id] = Ctx.Values[D.Id] or {}
		Cards.Card(G, D, UDim2.fromOffset(Col * 392, Row * 180), {
			Values = Ctx.Values[D.Id]; Lists = Ctx.Lists; Fav = table.find(S.Favs, D.Id) ~= nil; Reduced = Ctx.Reduced;
			OnRun = H.Run; OnFav = H.Fav; Redraw = H.Redraw;
			OnPick = function(A, Choices, Done) Cards.Picker(Dyn, A.Label or A.Name, Choices, Done) end;
		})
	end
	if #List == 0 then Text(G, "Empty", "Nothing here for your level.", 20, FACE.Body, COL.Dim, UDim2.fromOffset(8, 8), UDim2.fromOffset(700, 30)) end
end

local function feed(Dyn: Instance, Ctx: any)
	local F = Piece("Feed", Dyn, UDim2.fromOffset(Ctx.X, 756), UDim2.fromOffset(774, 120), { Name = "Feed" })
	for I, E in Ctx.S.Feed do
		if I > 4 then break end
		Text(F, "Line" .. I, (if E.Ok then "✓ " else "✕ ") .. E.Text, 20, FACE.Body, if E.Ok then COL.Good else COL.Crimson,
			UDim2.fromOffset(18, 8 + (I - 1) * 26), UDim2.fromOffset(740, 26))
	end
	if #Ctx.S.Feed == 0 then Text(F, "Hint", "Results show here.", 20, FACE.Body, COL.Dim, UDim2.fromOffset(18, 8), UDim2.fromOffset(740, 26)) end
end

local function context(Dyn: Instance, Ctx: any)
	local S = Ctx.S
	local C = Piece("Rail", Dyn, UDim2.fromOffset(1240, 110), UDim2.fromOffset(320, 696), { Name = "Context" })
	local Body = New("ScrollingFrame", { Name = "Body"; BackgroundTransparency = 1; Position = UDim2.fromOffset(20, 20); Size = UDim2.fromOffset(284, 656);
		CanvasSize = UDim2.new(); AutomaticCanvasSize = Enum.AutomaticSize.Y; ScrollBarThickness = 6 }, C)
	New("UIListLayout", { Padding = UDim.new(0, 6); SortOrder = Enum.SortOrder.LayoutOrder }, Body)
	local N = 0
	local function line(T: string, Size: number?, Color: Color3?, Bold: boolean?)
		N += 1
		local L = Text(Body, "L" .. N, T, Size or 20, if Bold then FACE.Bold else FACE.Body, Color or COL.Bone, UDim2.new(), UDim2.new(1, -8, 0, 0), true)
		L.AutomaticSize = Enum.AutomaticSize.Y
		L.LayoutOrder = N
	end
	local Players = (Ctx.Status and Ctx.Status.Players) or (Ctx.Info and Ctx.Info.Players) or {}
	local P
	for _, R in Players do if R.UserId == S.Selected then P = R end end
	if S.Side == "Moderate" and S.Section == "Server" then
		line("Action log (this server)", 22, COL.Brass, true)
		for I, E in (Ctx.Info and Ctx.Info.Log) or {} do
			if I > 12 then break end
			line(`{os.date("%H:%M", E.T)} {E.Admin}: {E.Command} {E.Target}`, 20, COL.Dim)
		end
		return
	end
	if not P then line("Pick a student on the left.", 20, COL.Dim) return end
	line(P.Display or P.Name, 26, COL.Brass, true)
	N += 1
	local Id = New("TextBox", { Name = "UserId"; Text = tostring(P.UserId); TextEditable = false; ClearTextOnFocus = false; TextSize = 20; FontFace = FACE.Body;
		TextColor3 = COL.Dim; BackgroundColor3 = COL.IronHi; Size = UDim2.new(1, -8, 0, 36); LayoutOrder = N }, Body)
	New("UICorner", { CornerRadius = UDim.new(0, 6) }, Id)
	line(`{P.Sub or P.Race or "?"}{if P.Tier then " · Tier " .. ({ "I", "II", "III" })[P.Tier] else ""}{if P.Height then " · " .. P.Height else ""}`)
	line(`Health {P.Health}/{P.MaxHealth} · {P.Ping} ms · staff level {P.Level}`)
	local Flags = Model.Flags(P)
	if #Flags > 0 then line(table.concat(Flags, "  "), 20, COL.Crimson, true) end
	local I = Ctx.Inspect
	if S.Side == "Test" and I and I.UserId == P.UserId then
		line("Inspector", 22, COL.Brass, true)
		line(`Slot {I.Slot or "?"} · ¥{I.Yen} · Level {I.Level or "?"} ({I.Exp or 0} EXP, {I.Points or 0} points)`)
		line(`Discipline {I.Discipline.Points or 0} ({I.Discipline.Level or "Clear"}), owes {I.Discipline.Owed or 0}`)
		line(`Places {I.Regions}/{I.RegionsTotal} · Club {I.Club ~= "" and I.Club or "none"}`)
		line(`Title {I.Title ~= "" and I.Title or "none"} · {#I.Titles} titles`)
		if #I.Quests > 0 then line("Quests: " .. table.concat(I.Quests, ", ")) end
		if I.Note then line(`Note ({I.Note.By}): {I.Note.Text}`, 20, COL.Dim) end
	end
end

function View.Redraw(U: any, Ctx: any)
	if U.Dyn then U.Dyn:Destroy() end
	local Dyn = New("Frame", { Name = "Dyn"; BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1) }, U.Board)
	U.Dyn = Dyn
	-- phones: the centre takes the whole board (3 card columns); the rail and the context open over it (spec §5)
	local Phone = Kit.Phone and Kit.Phone() or false
	Ctx.X, Ctx.W = if Phone then 40 else 450, if Phone then 1520 else 772
	local function button(Name: string, Label: string, X: number, Fn: () -> (), Color: Color3)
		local B = New("TextButton", { Name = Name; Text = Label; TextSize = 20; FontFace = FACE.Bold; TextColor3 = COL.Bone; BackgroundColor3 = Color;
			Position = UDim2.fromOffset(X, 820); Size = UDim2.fromOffset(120, 44); ZIndex = 5 }, Dyn)
		New("UICorner", { CornerRadius = UDim.new(0, 8) }, B)
		B.Activated:Connect(Fn)
	end
	topBar(Dyn, Ctx)
	sections(Dyn, Ctx)
	grid(Dyn, Ctx)
	feed(Dyn, Ctx)
	if Phone then
		button("Students", "Students", 1180, Ctx.Handlers.PhoneRail, COL.IronHi)
		button("Details", "Details", 1310, Ctx.Handlers.PhoneContext, COL.IronHi)
		if Ctx.S.PhoneRail then rail(Dyn, Ctx) end
		if Ctx.S.PhoneContext then context(Dyn, Ctx) end
	else
		rail(Dyn, Ctx)
		context(Dyn, Ctx)
	end
	button("Close", "Close", 1440, Ctx.Handlers.Close, COL.Velvet)
end

return View
```

**Phones** (`Kit.Phone()`) use `Kit.AutoScale(Gui)`, which clamps the board to the screen through
`Kit.ClampPanels` and the kit's phone scale. The centre then spans the board, and **Students** and **Details** open
the rail and the context over it. The owner's mobile session judges whether text reads on a real phone (spec §10). If
it doesn't, 1b redraws the phone layout at 800 x 450.

- [ ] **Step 3: `Palette.luau`**

```lua
--[[ StaffConsole.Palette (client): Ctrl+K finds any action by title, help or synonym (StaffConsole.Search). Enter runs the
	top result when it needs no options and isn't dangerous; otherwise it jumps to the card. ]]
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SC = require(ReplicatedStorage:WaitForChild("Functions"):WaitForChild("StaffConsole"))
local Cards = require(script.Parent:WaitForChild("Cards"))
local New, Piece, Text, COL, FACE = Cards.New, Cards.Piece, Cards.Text, Cards.COL, Cards.FACE
local Palette = {}

-- Opts = { Defs, OnRun(Def), OnJump(Def) }
function Palette.Open(Board: Instance, Opts: any): GuiObject
	local Old = Board:FindFirstChild("Palette")
	if Old then Old:Destroy() end
	local P = Piece("Side", Board, UDim2.fromOffset(440, 120), UDim2.fromOffset(720, 540), { Name = "Palette"; ZIndex = 30 })
	local Box = New("TextBox", { Name = "Query"; PlaceholderText = "Find any action…"; Text = ""; TextSize = 24; FontFace = FACE.Body; TextColor3 = COL.Bone;
		PlaceholderColor3 = COL.Dim; BackgroundColor3 = COL.IronHi; ClearTextOnFocus = false; Position = UDim2.fromOffset(24, 20); Size = UDim2.fromOffset(672, 52);
		TextXAlignment = Enum.TextXAlignment.Left; ZIndex = 31 }, P)
	New("UIPadding", { PaddingLeft = UDim.new(0, 14) }, Box)
	local L = New("Frame", { Name = "Results"; BackgroundTransparency = 1; Position = UDim2.fromOffset(24, 84); Size = UDim2.fromOffset(672, 440); ZIndex = 31 }, P)
	New("UIListLayout", { Padding = UDim.new(0, 4) }, L)
	local Hits, Hi = {}, 1
	local function draw()
		for _, C in L:GetChildren() do if C:IsA("GuiObject") then C:Destroy() end end
		for I, D in Hits do
			if I > 8 then break end
			local R = New("TextButton", { Name = "Hit_" .. D.Id; Text = ""; BackgroundColor3 = if I == Hi then COL.Velvet else COL.IronHi; Size = UDim2.new(1, 0, 0, 50); ZIndex = 32 }, L)
			Cards.Icon(R, D, UDim2.fromOffset(8, 5), 40)
			Text(R, "Title", D.Title, 22, FACE.Bold, if D.Danger then COL.Crimson else COL.Bone, UDim2.fromOffset(58, 4), UDim2.fromOffset(380, 28))
			Text(R, "Where", `{D.Side} · {D.Section}`, 20, FACE.Body, COL.Dim, UDim2.fromOffset(440, 10), UDim2.fromOffset(224, 26))
			for _, K in R:GetDescendants() do if K:IsA("GuiObject") then K.ZIndex = 33 end end
			R.Activated:Connect(function() Hi = I Palette.Choose(P, Hits[Hi], Opts) end)
		end
	end
	Box:GetPropertyChangedSignal("Text"):Connect(function() Hits = SC.Search(Opts.Defs, Box.Text) Hi = 1 draw() end)
	Box.FocusLost:Connect(function(Enter) if Enter and Hits[Hi] then Palette.Choose(P, Hits[Hi], Opts) end end)
	P:SetAttribute("Open", true)
	Palette.Move = function(D: number) if #Hits > 0 then Hi = math.clamp(Hi + D, 1, math.min(8, #Hits)) draw() end end
	task.defer(function() Box:CaptureFocus() end)
	return P
end

function Palette.Choose(P: Instance, D: any, Opts: any)
	P:Destroy()
	if not D then return end
	if #D.Args == 0 and not D.Danger then Opts.OnRun(D) else Opts.OnJump(D) end
end

return Palette
```

- [ ] **Step 4: The shell `StaffConsole.luau`**

```lua
--[[
	StaffConsole (client): the Headmaster's Console (spec docs/superpowers/specs/2026-11-23-admin-console-design.md, 1a).
	F3 toggles it for staff (the server decides); NHAdminOpen (other UI, tests) opens it. Moderate / Test sides, sections,
	cards from the server's registry (Info().Registry) plus StaffConsole.Tools' own-client cards, Ctrl+K palette,
	hold-to-confirm on danger cards, favourites and recent students for the session, a results feed.
	Keys: F3 open/close, 1-7 sections, Tab side, Ctrl+K palette, Esc closes (on GuiService.MenuOpened: Roblox keeps
	Escape). Controller: LB / RB sections, A run, Y favourite, B closes.
	Studio probe (HudState.Probe "Console"): Open, Close, Side, Section, Search, Info, Pick.
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")
local ContextActionService = game:GetService("ContextActionService")
local GuiService = game:GetService("GuiService")
local Kit = require(ReplicatedStorage:WaitForChild("UI"):WaitForChild("Components"))
local SC = require(ReplicatedStorage:WaitForChild("Functions"):WaitForChild("StaffConsole"))
local Model = require(script:WaitForChild("Model"))
local View = require(script:WaitForChild("View"))
local Palette = require(script:WaitForChild("Palette"))
local Tools = require(script:WaitForChild("Tools"))

local Player = Players.LocalPlayer
local Shared = {}
local S = Model.New()
local U = nil :: any
local Open = false
local Info, Status, Inspect = nil :: any, nil :: any, nil :: any
local Values = {} :: { [string]: any }
local Busy = false

local function remotes()
	local F = ReplicatedStorage:FindFirstChild("NHAdmin")
	if not (F and F:GetAttribute("Ready")) then return nil end
	return F
end

local function defs(): any
	local Out = {}
	for _, D in (Info and Info.Registry) or {} do table.insert(Out, D) end
	for _, D in Tools.Defs do if D.Level <= S.Level then table.insert(Out, D) end end
	return Out
end

local function ctx(): any
	return { S = S; Info = Info; Status = Status; Defs = defs(); Values = Values; Lists = Info and Info.Lists; Inspect = Inspect;
		Reduced = Kit.ReducedMotion and Kit.ReducedMotion() or false; Handlers = Shared.Handlers }
end

-- a redraw rebuilds the dynamic layer, so the gamepad selection is found again by its full name
function Shared.Redraw()
	if not (U and Open) then return end
	local Sel = GuiService.SelectedObject
	local Name = if Sel and Sel:IsDescendantOf(U.Gui) then Sel:GetFullName() else nil
	View.Redraw(U, ctx())
	if Name then
		for _, D in U.Gui:GetDescendants() do
			if D:IsA("GuiObject") and D:GetFullName() == Name then GuiService.SelectedObject = D break end
		end
	end
end

local function run(D: any, Vals: any)
	Vals = Vals or {}
	local Ok, Why = Model.Ready(D, Vals, S.Selected)
	if not Ok then Model.Push(S, false, Why :: string, D.Title) Shared.Redraw() return end
	if D.Local then
		local Ok2, Msg = Tools.Do(D.Id, Vals, S.Selected)
		if D.Id == "ToolInspect" and Ok2 and S.Selected then Inspect = Tools.Inspect(S.Selected) end
		Model.Push(S, Ok2, Msg, D.Title)
		Shared.Redraw()
		return
	end
	local F = remotes()
	if not F or Busy then return end
	Busy = true
	local Target = if D.Target ~= "none" then S.Selected else nil
	local OkCall, A, B = pcall(F.Run.InvokeServer, F.Run, D.Id, Target, Vals)
	Busy = false
	Model.Push(S, OkCall and A == true, if OkCall then tostring(B or (if A then "Done" else "Failed")) else "Request failed", D.Title)
	pcall(Kit.PlaySound, if OkCall and A then "Click" else "Error", 0.6)
	task.spawn(Shared.Refresh)
end

-- Tools' Ctrl+click and other callers: run by id
local function runId(Id: string, Args: any?, _Target: number?)
	for _, D in defs() do if D.Id == Id then run(D, Args) return end end
end

function Shared.Refresh()
	local F = remotes()
	if not F then return end
	local Ok, R = pcall(F.Info.InvokeServer, F.Info)
	if Ok then
		Info = R
		Model.SetLevel(S, (R and R.Level) or 0, (R and R.Sections) or SC.SECTIONS)
	end
	Shared.Redraw()
end

local function refreshStatus()
	local F = remotes()
	if not (F and Open and F:FindFirstChild("Status")) then return end
	local Ok, R = pcall(F.Status.InvokeServer, F.Status)
	if Ok and R then Status = R Shared.Redraw() end
end

local function bind()
	ContextActionService:BindActionAtPriority("NHConsolePad", function(Name, St, I)
		if St ~= Enum.UserInputState.Begin then return Enum.ContextActionResult.Pass end
		local Sections = (Info and Info.Sections) or SC.SECTIONS
		local List = Sections[S.Side] or {}
		local Cur = table.find(List, S.Section) or 1
		if I.KeyCode == Enum.KeyCode.ButtonL1 then Model.Section(S, math.max(1, Cur - 1), Sections) Shared.Redraw()
		elseif I.KeyCode == Enum.KeyCode.ButtonR1 then Model.Section(S, math.min(#List, Cur + 1), Sections) Shared.Redraw()
		elseif I.KeyCode == Enum.KeyCode.ButtonB then Shared.Toggle(false)
		elseif I.KeyCode == Enum.KeyCode.ButtonY then
			local Sel = GuiService.SelectedObject
			local CardObj = Sel and Sel:FindFirstAncestorWhichIsA("GuiObject")
			while CardObj and not string.match(CardObj.Name, "^Card_") do CardObj = CardObj.Parent :: any end
			if CardObj then Model.ToggleFav(S, string.sub(CardObj.Name, 6)) Shared.Redraw() end
		end
		return Enum.ContextActionResult.Sink
	end, false, 3000, Enum.KeyCode.ButtonL1, Enum.KeyCode.ButtonR1, Enum.KeyCode.ButtonB, Enum.KeyCode.ButtonY)
end

function Shared.Toggle(On: boolean?)
	local Want = if On == nil then not Open else On
	if Want and S.Level < 1 then Shared.Refresh() if S.Level < 1 then return end end
	Open = Want
	if not U then U = View.Build() end
	U.Gui.Enabled = Open
	Player:SetAttribute("NHMenuOpen", if Open then true else nil)
	if Open then bind() Shared.Refresh() task.spawn(refreshStatus)
	else
		ContextActionService:UnbindAction("NHConsolePad")
		local Sel = GuiService.SelectedObject
		if Sel and U and Sel:IsDescendantOf(U.Gui) then GuiService.SelectedObject = nil end
	end
end

function Shared.IsOpen() return Open end

Shared.Handlers = {
	Side = function(Side: string) if table.find(Model.Sides(S.Level), Side) then S.Side = Side S.Section = ((Info and Info.Sections or SC.SECTIONS)[Side] or {})[1] Shared.Redraw() end end;
	Section = function(Name: string) if table.find((Info and Info.Sections or SC.SECTIONS)[S.Side] or {}, Name) then S.Section = Name Shared.Redraw() end end;
	Pick = function(UserId: number) Model.Pick(S, UserId) Inspect = nil S.PhoneRail = false Shared.Redraw() end;
	PhoneRail = function() S.PhoneRail = not S.PhoneRail S.PhoneContext = false Shared.Redraw() end;
	PhoneContext = function() S.PhoneContext = not S.PhoneContext S.PhoneRail = false Shared.Redraw() end;
	Filter = function(Q: string) S.Filter = Q Shared.Redraw() end;
	Run = function(D: any, Vals: any) task.spawn(run, D, Vals) end;
	Fav = function(D: any) Model.ToggleFav(S, D.Id) Shared.Redraw() end;
	Redraw = function() Shared.Redraw() end;
	Close = function() Shared.Toggle(false) end;
	Palette = function()
		if not U then return end
		Palette.Open(U.Board, { Defs = defs();
			OnRun = function(D) task.spawn(run, D, Values[D.Id] or {}) end;
			OnJump = function(D) S.Side = D.Side S.Section = D.Section Shared.Redraw() end })
	end;
}

function Shared.OnStart()
	Tools.Init(runId)
	UserInputService.InputBegan:Connect(function(I, Processed)
		if I.KeyCode == Enum.KeyCode.F3 and not Processed then Shared.Toggle() return end
		if not Open then return end
		local Typing = UserInputService:GetFocusedTextBox() ~= nil
		local Ctrl = UserInputService:IsKeyDown(Enum.KeyCode.LeftControl) or UserInputService:IsKeyDown(Enum.KeyCode.RightControl)
		if I.KeyCode == Enum.KeyCode.K and Ctrl then Shared.Handlers.Palette() return end
		if Typing then
			if I.KeyCode == Enum.KeyCode.Up and Palette.Move then Palette.Move(-1) elseif I.KeyCode == Enum.KeyCode.Down and Palette.Move then Palette.Move(1) end
			return
		end
		if I.KeyCode == Enum.KeyCode.Tab then
			local Sides = Model.Sides(S.Level)
			Shared.Handlers.Side(Sides[(table.find(Sides, S.Side) or 1) % #Sides + 1])
			return
		end
		local N = I.KeyCode.Value - Enum.KeyCode.One.Value + 1
		if N >= 1 and N <= 7 and Model.Section(S, N, (Info and Info.Sections) or SC.SECTIONS) then Shared.Redraw() end
	end)
	-- Esc: Roblox opens its menu and never hands Escape to the game, so close with it
	GuiService.MenuOpened:Connect(function() if Open then Shared.Toggle(false) end end)
	Player:GetAttributeChangedSignal("NHAdminOpen"):Connect(function()
		local V = Player:GetAttribute("NHAdminOpen")
		if V ~= nil then Shared.Toggle(V == true) end
	end)
	task.spawn(function()
		while true do
			task.wait(1)
			if Open then pcall(refreshStatus) end
		end
	end)
	task.spawn(function()
		local Mod = script.Parent:WaitForChild("HudState", 10)
		if not Mod then return end
		local Ok, Hud = pcall(require, Mod)
		if not Ok or typeof(Hud) ~= "table" or not Hud.Probe then return end
		Hud.Probe("Console", function(Cmd: string, A: any)
			if Cmd == "Open" then Shared.Toggle(true) return Open end
			if Cmd == "Close" then Shared.Toggle(false) return Open end
			if Cmd == "Side" then Shared.Handlers.Side(A) return S.Side end
			if Cmd == "Section" then Shared.Handlers.Section(A) return S.Section end
			if Cmd == "Pick" then Shared.Handlers.Pick(A) return S.Selected end
			if Cmd == "Search" then local R = {} for _, D in SC.Search(defs(), A) do table.insert(R, D.Id) end return R end
			if Cmd == "Info" then
				local Ids = {}
				for _, D in Model.Cards(defs(), S.Side, S.Section) do table.insert(Ids, D.Id) end
				local Feed = {}
				for _, E in S.Feed do table.insert(Feed, E.Text) end
				return { Open = Open; Side = S.Side; Section = S.Section; Cards = Ids; Feed = Feed; Level = S.Level; Selected = S.Selected }
			end
			return nil
		end)
	end)
end

return Shared
```

- [ ] **Step 5: Install the four modules**

Install the shell first, so the Folder that Task 5 may have created becomes the ModuleScript and keeps its children.

```bash
python -X utf8 -I tools/admin-console/install_new.py "tools/admin-console/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.luau"
python -X utf8 -I tools/admin-console/install_new.py "tools/admin-console/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.Cards.luau" "tools/admin-console/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.View.luau" "tools/admin-console/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.Palette.luau"
```

Then confirm in Edit:
- `Controllers.Gui.StaffConsole` is a ModuleScript;
- it has the children `Model`, `Tools`, `Cards`, `View` and `Palette`;
- no `PARSE FAIL` was printed.

**`install_new.py` and a Folder:** when it replaces a Folder named `StaffConsole`, it moves the Folder's children to
the new ModuleScript. That is what its `for _, K in Old:GetChildren()` loop does.

**F3 is shared with the old desk until Task 9.** Both open on F3 between Task 7 and Task 9, which is acceptable in
Studio. Task 9 removes the desk.

- [ ] **Step 6: Commit (on the owner's word)**

```bash
git add tools/admin-console/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole*.luau
git commit -m "Console 1a: the console shell, view, cards (hold ring, picker) and Ctrl+K palette"
```

---

### Task 8: Play checks

**Files:**
- Create: `tools/admin-console/checks/console_play_run.lua` (server, Play; the Play half)
- Create: `tools/admin-console/checks/console_play_client.lua` (client, Play)
- Use: `E:/NH-transform/tools/forms/harness/round_start.sh` and `restore.py` (the slot 2 snapshot and restore), and
  the scratchpad `cine.lua`, which records the attributes:

```lua
local P = game.Players:GetPlayers()[1]
return string.format("CineState=%s Seen=%s Origin=%s", tostring(P:GetAttribute("CineState")), tostring(P:GetAttribute("Seen")), tostring(P:GetAttribute("Origin")))
```

- [ ] **Step 1: Write the server Play check**

`tools/admin-console/checks/console_play_run.lua`:

```lua
-- Server, Play, slot 2: every migrated command through Admin.Dispatch once, plus the level and argument refusals.
local Players = game:GetService("Players")
local Admin = require(game.ServerScriptService.Services.Features.Admin)
local P = Players:GetPlayers()[1]
if not P then return "FAIL no player" end
local Fails, Ran = {}, 0
local function go(Cmd, Args, Target)
	task.wait(0.2) -- Dispatch's 0.15 s rate limit
	return Admin.Dispatch(P, Cmd, Target, Args or {})
end
local function want(Ok, Cmd, Args, Target, Expect)
	local A, B = go(Cmd, Args, Target)
	Ran += 1
	if (A == true) ~= Ok then table.insert(Fails, `{Cmd}: got {tostring(A)} {tostring(B)}`) return end
	if Expect and not string.find(tostring(B), Expect, 1, true) then table.insert(Fails, `{Cmd}: message "{tostring(B)}", want "{Expect}"`) end
end
local Me = P.UserId
-- record what this run changes outside slot 2, to put back at the end
local Before = { Sub = P:GetAttribute("SubRace") or P:GetAttribute("Race"); Tier = P:GetAttribute("RaceTier") }

-- levels (NHTestLevel, Studio only)
P:SetAttribute("NHTestLevel", 1)
task.wait(0.3)
want(false, "Heal", {}, Me, "Needs an admin")
want(false, "Shutdown", {}, nil, "Needs the owner")
want(true, "Warn", { Reason = "console test" }, Me)
P:SetAttribute("NHTestLevel", 2)
task.wait(0.3)
want(false, "Ban", { Days = 0; Reason = "test" }, Me, "Permanent bans are owner-only")
want(false, "GiveYen", { Amount = 200000 }, Me, "needs an owner")
P:SetAttribute("NHTestLevel", 0)
task.wait(0.3)
want(false, "Warn", {}, Me, "Not staff")
P:SetAttribute("NHTestLevel", nil)
task.wait(0.3)

-- arguments
want(false, "Speed", { Value = 500 }, Me, "Speed must be 0 to 120")
want(false, "SetHeight", { Pick = "Huge" }, Me, "Unknown Height")
want(false, "SpawnSparring", { Tier = "Godlike" }, nil, "Unknown Difficulty")
want(false, "Announce", { Text = "" }, nil, "Message is needed")
want(false, "Heal", {}, nil, "Pick a player first")

-- every safe command once (Kick, Ban, Unban and Shutdown are left out: they would end the Play session)
local L = Admin.Lists()
local function first(K) local I = L[K] and L[K][1] return I and (if typeof(I) == "table" then I.Id else I) end
local Runs = {
	{ "Mute" }, { "Unmute" }, { "Freeze" }, { "Freeze" }, { "Jail" }, { "Spectate" }, { "Bring" }, { "Goto" },
	{ "Note", { Text = "console test" } }, { "Note", { Text = "" } },
	{ "Announce", { Text = "Console test, please ignore" } }, { "ServerLock" }, { "ServerLock" }, { "BringAll" },
	{ "FreezeAll", { On = true } }, { "FreezeAll", { On = false } },
	{ "Heal" }, { "Revive" }, { "God" }, { "God" }, { "Speed", { Value = 16 } },
	{ "SetRace", { Sub = Before.Sub } }, { "SetTier", { Tier = Before.Tier or 1 } }, { "SetHeight", { Pick = "Average" } },
	{ "SpinHeight" }, { "SetBuild", { Build = "Average"; Step = 0 } }, { "Transform" }, { "Transform" },
	{ "GiveYen", { Amount = 10 } }, { "GiveYen", { Amount = -10 } }, { "GiveExp", { Amount = 10; Category = "Combat" } },
	{ "GiveGear", { Id = first("Gear") } }, { "GiveSpins", { Amount = 1 } }, { "GiveNameChange" },
	{ "SetLevel", { Value = 5 } }, { "SetStatPoints", { Value = 3 } }, { "GrantTitle", { Title = "Tester" } }, { "RemoveTitle", { Title = "Tester" } },
	{ "RegionsAll" }, { "RegionsReset" }, { "SetClub", { Club = first("Clubs") } },
	{ "MatchStart", { Venue = first("Venues") } }, { "MatchEnd", { Venue = first("Venues") }, true },
	{ "SetTime", { Time = "12:30" }, true }, { "ClockSpeed", { Value = 60 }, true }, { "SkipToPeriod", { Segment = first("Segments") }, true }, { "RingBell", nil, true },
	{ "StartLesson", { Room = "R101" } }, { "SetDisciplinePoints", { Value = 0 } }, { "ClearDiscipline" }, { "LiftSuspension" }, { "ExcuseToday" },
	{ "OweDetention" }, { "ClearDetention" },
	{ "QuestStart", { Id = first("Quests") } }, { "QuestAbandon", { Id = first("Quests") } }, { "QuestReset" },
	{ "FullMoon", nil, true }, { "GotoRegion", { Id = first("Regions") }, true },
	{ "SpawnDelinquents", nil, true }, { "SpawnDelinquent", { Role = "Brute" }, true }, { "SpawnWolves", nil, true },
	{ "SpawnBeast", { Beast = first("Beasts") }, true }, { "SpawnSparring", { Tier = "Easy" }, true }, { "ClearEnemies", nil, true },
	{ "Invisible", nil, true }, { "Invisible", nil, true },
	{ "TeleportTo", { Position = (P.Character and P.Character:GetPivot().Position or Vector3.zero) + Vector3.new(0, 0, 4) }, true },
	{ "Kill" }, -- last: the respawn
}
local Seen = {}
for _, R in Runs do
	local Cmd, Args, NoTarget = R[1], R[2], R[3]
	Seen[Cmd] = true
	local A, B = go(Cmd, Args, if NoTarget then nil else Me)
	Ran += 1
	if A ~= true then table.insert(Fails, `{Cmd} refused: {tostring(B)}`) end
end
for _, Id in { "Kick", "Ban", "Unban", "Shutdown" } do Seen[Id] = true end
for _, D in Admin.Registry(3) do if not Seen[D.Id] then table.insert(Fails, D.Id .. " not run") end end
P:SetAttribute("NHTestLevel", nil)
if #Fails > 0 then return "FAIL " .. #Fails .. " of " .. Ran .. "\n" .. table.concat(Fails, "\n") end
return "PASS console_play_run (" .. Ran .. " calls)"
```

Some commands may fairly be refused in a given state. For example, `MatchStart` without a venue, `StartLesson`
outside school hours, or `QuestAbandon` of a quest that isn't active. If one is refused, read the `Run`'s message:
- if it's a state message (as in the 1.18 test list), move that command to a `StateOk` list that only needs **a
  message**, not `true`;
- never loosen the level or argument lines.

- [ ] **Step 2: Write the client Play check**

`tools/admin-console/checks/console_play_client.lua`, run with `Client`:

```lua
local P = game.Players.LocalPlayer
local B = P.PlayerGui:WaitForChild("NHQuietProbe", 10)
if not B then return "FAIL no probe" end
local Fails = {}
local function Eq(Got, Want, What) if Got ~= Want then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end
Eq(B:Invoke("Console", "Open"), true, "opens")
task.wait(1)
local G = P.PlayerGui:FindFirstChild("NHStaffConsole")
Eq(G and G.Enabled, true, "gui on")
local I = B:Invoke("Console", "Info")
Eq(I.Level, 3, "studio level") Eq(I.Side, "Moderate", "start side") Eq(I.Section, "Student", "start section")
Eq(#I.Cards, 13, "student cards (12 + Stop spectating)")
Eq(B:Invoke("Console", "Side", "Test"), "Test", "test side")
for _, Sec in { "Character", "Progress", "School", "Story", "World", "Spawns", "Self" } do
	Eq(B:Invoke("Console", "Section", Sec), Sec, "section " .. Sec)
	task.wait(0.3)
	local Cards = B:Invoke("Console", "Info").Cards
	if #Cards == 0 then table.insert(Fails, Sec .. " has no cards") end
	for _, Id in Cards do
		if not G:FindFirstChild("Card_" .. Id, true) then table.insert(Fails, "no Card_" .. Id .. " drawn in " .. Sec) end
	end
end
local R = B:Invoke("Console", "Search", "tp")
Eq(R[1], "Goto", "tp finds Go to")
-- every text label at 20+ px
for _, L in G:GetDescendants() do
	if (L:IsA("TextLabel") or L:IsA("TextButton") or L:IsA("TextBox")) and L.Text ~= "" and L.TextSize < 20 then
		table.insert(Fails, "small text " .. L:GetFullName() .. " " .. L.TextSize)
	end
end
if #Fails > 0 then return "FAIL " .. #Fails .. "\n" .. table.concat(Fails, "\n") end
return "PASS console_play_client"
```

The Student count is 12 server cards plus the client card "Stop spectating" (level 1), which makes 13. Recount from
Task 2 and Task 6 before running.

- [ ] **Step 3: Run the Play round**

1. `start_stop_play` start.
2. `bash E:/NH-transform/tools/forms/harness/round_start.sh` (fresh slot 2 snapshot).
3. Record `cine.lua`.
4. `python -X utf8 -I tools/admin-console/run_check.py Server tools/admin-console/checks/console_play_run.lua`
   - Expected: `PASS console_play_run (N calls)`.
5. `python -X utf8 -I tools/admin-console/run_check.py Client tools/admin-console/checks/console_play_client.lua`
   - Expected: `PASS console_play_client`.
6. **The hold ring, with real input:**
   - Go to the Moderate side's Server section and find `Card_FreezeAll`'s `Run`.
   - `user_mouse_input`: `moveTo` the `instance_path` `LocalPlayer.PlayerGui.NHStaffConsole.Board.Dyn.Cards.Card_FreezeAll.Run`,
     `mouseButtonDown`, wait 300 ms, `mouseButtonUp`.
     - Expected: `Info().Feed` is unchanged (cancelled).
   - Repeat with a 1100 ms wait.
     - Expected: the feed's first line is "Froze 0 student(s)" or "Thawed 0 student(s)".
7. **Keys, with real input:**
   - `user_keyboard_input` keyPress `Two`: Expected: `Section` = `Server`.
   - LeftControl down, K, LeftControl up: Expected: `Board.Palette` exists.
   - Escape: Expected: `Info().Open` = false, `NHMenuOpen` nil.
   - Press Escape again to close the Roblox menu.
8. **Screenshots:** `screen_capture` of the Moderate Student and Server sections, and each Test section. Save them to
   `docs/superpowers/mockups/2026-11-23-admin-console/play-<side>-<section>.png`.
9. Run `restore.py`, record `cine.lua` again, and stop Play.
10. Write the results in `REPORT.md`:
    - the PASS lines and the call count;
    - any state-refused commands, and why;
    - CineState, Seen and Origin before and after;
    - the screenshots.

- [ ] **Step 4: Fix what failed, and repeat Step 3 until both checks pass**

- [ ] **Step 5: Commit (on the owner's word)**

```bash
git add tools/admin-console/checks/console_play_run.lua tools/admin-console/checks/console_play_client.lua tools/admin-console/REPORT.md docs/superpowers/mockups/2026-11-23-admin-console/play-*.png
git commit -m "Console 1a: Play checks (66 commands through Dispatch, levels, args, sections, hold ring, keys)"
```

---

### Task 9: Cutover and docs

**Files:**
- Modify: `live/...Controllers.Gui.GamepadControls.luau` (fetch it first into `pre/` with the chunked fetcher, then
  copy it to `live/`)
- Move (Studio): `Controllers.Gui.AdminPanel` to `ServerStorage.NH_Backup.AdminConsole1a_pre_20261123.AdminPanel`
- Modify: `docs/Admin-Panel.md`, `CHANGELOG.md`

- [ ] **Step 1: GamepadControls**

Fetch `StarterPlayer.StarterPlayerScripts.Controllers.Gui.GamepadControls` into `pre/` and copy it to `live/`.
Change `NHAdminPanel = { \`Gui\`, \`AdminPanel\` };` to `NHStaffConsole = { \`Gui\`, \`StaffConsole\` };`.

Read the table's comment first: if it maps ScreenGui names to controllers for B-to-close, the new console's own B
binding (Task 7) makes the entry optional. Keep it so the gamepad layer knows the console is a menu.

Install it in place:

```bash
python -X utf8 -I tools/admin-console/install_inplace.py tools/admin-console/pre tools/admin-console/live AdminConsole1a_pre_20261123 StarterPlayer.StarterPlayerScripts.Controllers.Gui.GamepadControls
```

- [ ] **Step 2: Move the old desk to the backup**

Run in Edit:

```lua
local G = game.StarterPlayer.StarterPlayerScripts.Controllers.Gui
local Old = G:FindFirstChild("AdminPanel")
if not Old then return "already moved" end
local Root = game.ServerStorage:FindFirstChild("NH_Backup")
local F = Root:FindFirstChild("AdminConsole1a_pre_20261123") or Instance.new("Folder")
F.Name = "AdminConsole1a_pre_20261123"
F.Parent = Root
Old.Parent = F
return "moved " .. Old:GetFullName()
```

This is a move, not a delete. To put the desk back, move it back.

- [ ] **Step 3: Play check again**

Run Task 8 Step 3, items 1-5 and 9:
- F3 now opens only the console;
- `PlayerGui` has no `NHAdminPanel`;
- both checks still pass.

- [ ] **Step 4: Docs**

`docs/Admin-Panel.md`: replace the desk description with the console:
- who gets which level (the §6 table);
- the sides and sections with every card (from `Admin.Meta` and `Tools.Defs`);
- the keys and controller buttons;
- the danger list;
- "1b and later" (saved records, Log, Inbox, reports, new Test tools);
- the test record from `REPORT.md`.

Keep the 1.18 section as history under a "Before 1a" heading.

`CHANGELOG.md`: add a section at the top, following the file's existing format, with these bullets:
- the console replaces the desk;
- levels 0-3 (Testers list);
- 66 commands with argument checks;
- the danger hold;
- Ctrl+K;
- favourites for the session;
- the Esc fix pattern;
- "Not saved: the place needs the owner's word to save."

- [ ] **Step 5: Mirror back to main's tools and run `graphify update .`**

`graphify` isn't installed. If it isn't, say so in `REPORT.md`. Otherwise run `graphify update .`.

- [ ] **Step 6: Commit (on the owner's word)**

```bash
git add tools/admin-console docs/Admin-Panel.md CHANGELOG.md
git commit -m "Console 1a: cutover (desk to NH_Backup, GamepadControls), docs and changelog"
```

---

## Self-review notes (2026-11-23)

- **Spec coverage, 1a:**

| Requirement | Where |
|---|---|
| §3 layout | Task 7 table |
| §4 Student and Server sections | Meta |
| §4 Test sections | Meta + Tools; the new phase 2 tools are out of scope |
| §5 palette | Task 7 |
| §5 favourites (session) | Model |
| §5 danger hold | Cards.Hold, list in Global Constraints |
| §5 results feed | View.feed |
| §5 keyboard and controller | shell |
| §5 phone | View phone branch |
| §5 reduce motion | Ctx.Reduced |
| §6 levels, no targeting up, Studio switch | Tasks 1 and 3 |
| §7 registry | Tasks 2-3 |
| §9 art | Task 4 |
| §10 pure checks | Tasks 1, 2, 5 |
| §10 Play checks | Task 8 |

- **Left to later phases on purpose:** saved records, the Log section, saved favourites (1b); the Inbox, reports,
  flags and health graphs (3); World, Story, Bell Tower and Form tools (2); the REPORTED, TRANSFORMED, WANTED and NEW
  flags (2-3).
- **Counts to recheck while executing:** registry by level (level 1 = 16, level 2 = 65, level 3 = 66; Task 3 Step 7)
  and Student cards on the client (13; Task 8 Step 2).
