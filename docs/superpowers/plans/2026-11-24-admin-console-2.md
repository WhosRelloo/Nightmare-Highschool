# Staff Console, Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** the Test side gains the World, Story, Bell Tower and Form direction tools, and student rows gain the
TRANSFORMED, WANTED, NEW and IN CUTSCENE flags.

**Architecture:**
- **Three group modules** beside Admin (`Admin.World`, `Admin.Story`, `Admin.BellTower`). Each is a function
  `(H) -> { [Id] = { Meta, Run } }`. `H` is a small table of Admin's helpers. Admin merges the groups into `C` and
  `Meta` when it loads, and errors on a clash. Dispatch, levels, logging and the client are unchanged, so each new
  card is a registry entry.
- **Small public calls in the game systems:** `Notoriety.SetHeat / Clear / AddSummons`, `HallMonitor.SetEnabled /
  IsEnabled`, `Investigation.ResetCase`, and a "tonight's moon" override in `Lineage` (one workspace attribute pair,
  read by `MoonPhase`, `MoonEvent` and `IsFullMoon`).
- **The pure rule** `StaffConsole.ServerWideOk(Level, Studio)` gates Season, Moon and Sky. A Studio-only
  `Admin.TestLiveMode` flag lets the Play check try the live rule.
- **Preview just for me** is a client tool card (`StaffConsole.Tools`, like Fly and ESP). It sets the sky's existing
  preview attributes on the local player.

**Tech Stack:** Luau, the 1a/1b harness in `tools/admin-console/` (`run_check.py`, `run_live.py`, `install_new.py`,
`install_inplace.py`, `shot.py`), the Roblox Studio MCP through `E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py`.

**Spec:** `docs/superpowers/specs/2026-11-24-admin-console-2-design.md`. Parent spec:
`docs/superpowers/specs/2026-11-23-admin-console-design.md`. Where this plan settles something the spec leaves open,
or changes it, see "Spec deltas" below. The owner approves them before Task 1.

**Where:** worktree `E:/Nightmare-Highschool/.claude/worktrees/admin-console-2-895704`, branch
`claude/admin-console-2-895704`. Every path below is relative to it.

## Global Constraints

- **Studio:**
  - NH Combat Test (placeId 98950102230473) only. Slot 2 only.
  - Never save, close, reload or revert the place without the owner's word. Never call `save_place`.
  - Another session (Soccer 2.0, `E:/NH-soccer2`) uses the same place. **Before every install round and every Play
    round, ask the owner whether Studio is free.** Wait for a yes. Edit-VM checks (`run_check.py Edit`) only read and
    are fine at any time.
  - Take a fresh snapshot at the start of every Play round and restore only from it. Record CineState, Seen and
    Origin before and after every Play round.
- **Commits:** local only, never push. Every commit message ends with
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Docs:** subagents can't write `.md` files. The controller writes `REPORT.md` and any doc changes.
- **Text:** never under 20 design px. Short, plain sentences in every refusal and result.
- **Security:** every request is checked on the server (Dispatch, unchanged). No targeting up. Server-wide World cards
  (`SetSeason`, `SetMoon`, `SetSky`) are allowed in Studio, and in live servers only at level 3. The refusal reads
  exactly `Owner only in live servers; use Preview just for me`.
- **Danger (hold-to-confirm, 0.8 s):** the 1b list plus `ResetCase`, `ClearNotoriety` and `HallMonitors`.
- **Counts:** 67 server commands today, plus 18 = **85**. Client tool cards: 6 today, plus 1 (`ToolPreview`) = 7.
  The 19 new cards are 18 server cards and 1 client card.
- **Install:**
  - Changed scripts: `python -X utf8 -I tools/admin-console/install_inplace.py tools/admin-console/pre2
    tools/admin-console/live AdminConsole2_20261124 <Dotted.Path> ...` (it refuses if Studio differs from `pre2/`).
  - New modules: `python -X utf8 -I tools/admin-console/install_new.py tools/admin-console/live/<Dotted.Path>.luau ...`
  - After each install round, copy the installed files from `live/` into `pre2/`, so the next in-place install
    compares against what Studio now runs.
- **Out of scope:** reports, the Inbox, auto-flags, health graphs, REPORTED (phase 3); new sky art; a Headmaster body.

## Spec deltas (settled by this plan; approved by the owner 2026-11-24)

1. **Preview just for me is a client tool card** (`ToolPreview` in `StaffConsole.Tools`), like Fly and ESP, instead of
   a server Meta entry with `Local = true`. Same result: it never reaches the server and is not logged. The registry
   has 85 server commands, not 86.
2. **No new preview attribute.** `Controllers.World.DayCycle` already takes any moon name (Crimson and Blue too) from
   `NHMoonPhasePreview`, and none of `NHSeasonPreview`, `NHMoonPhasePreview` or `NHSkyPreview` is Studio-gated. For
   Full, the card also sets `NHMoonPreview = true` (World.FullMoon's big moon).
3. **Moon tonight works through a Lineage override**, not by setting the workspace attributes (Features.MoonPhases
   overwrites them every tick from `Lineage.MoonPhase(Day, Hour)`). `workspace.NHMoonOverride` (the name) and
   `workspace.NHMoonOverrideNight` (the night number, `Lineage.NightOf`) make tonight that moon for everything that
   reads Lineage: the sky, the clock HUD, werewolf eyes and the moon powers. It ends by itself when the night ends.
   The card gains a seventh choice, **Auto**, which clears it.
4. **Give a clue is one choice** listing "Case: Clue" (Ids `"<CaseId>/<ClueId>"`), because the console's chips can't
   depend on another chip. Reset a case keeps its Case choice.
5. **Form direction's chips read "Direction 1" and "Direction 2"** (the names differ per race and the chips are
   shared). The result names the race's direction, for example "Set Kaito's form to Nightstalker (direction 2)".
6. **NEW means "hasn't seen the Prologue (Roll Call) yet"**, because the profile keeps no join count. That is a new
   student in practice, and it needs no new saved data.
7. **Hall monitors off despawns them, and on spawns them again.** `workspace.NHMonitorsOff = true` while off. The
   state is not saved: a new server starts with them on.
8. **Set Bells 0 and Set Heat 0 run Clear notoriety** (no summons added, nothing booked).
9. **Lowering Heat re-arms the escalation steps above the new bell.** So Set Bells 4, then 2, then 4 brings the
   monitors twice.

## File structure

| Path (under `tools/admin-console/`) | What |
|---|---|
| `fetch.py` | new: pull the current Source of named scripts from Studio into a folder |
| `pre2/` | new: what Studio runs before phase 2 (fetched in Task 0) |
| `live/ReplicatedStorage.Functions.StaffConsole.luau` | modify: `ServerWideOk`, `SERVER_WIDE_REFUSAL` |
| `live/ReplicatedStorage.Lineage.luau` | modify: the moon override |
| `live/ServerScriptService.Services.Features.Admin.luau` | modify: `H`, the group merge, `TestLiveMode`, lists, player list, inspector, `FormDirection` |
| `live/ServerScriptService.Services.Features.Admin.Meta.luau` | modify: `FormDirection` |
| `live/ServerScriptService.Services.Features.Admin.World.luau` | new: TimePreset, SetSeason, SetMoon, SetSky |
| `live/ServerScriptService.Services.Features.Admin.Story.luau` | new: PlayCutscene, CutsceneSeen, TutorialEnter, TutorialJump, TutorialLeave, GiveClue, ResetCase |
| `live/ServerScriptService.Services.Features.Admin.BellTower.luau` | new: SetHeat, SetBells, GiveSummons, ClearNotoriety, HallMonitors, WhosWanted |
| `live/ServerScriptService.Services.School.Notoriety.luau` | modify: `SetHeat`, `Clear`, `AddSummons` |
| `live/ServerScriptService.Services.School.HallMonitor.luau` | modify: `SetEnabled`, `IsEnabled` |
| `live/ServerScriptService.Services.Quests.Investigation.luau` | modify: `ResetCase` |
| `live/(...)Controllers.Gui.StaffConsole.Model.luau` | modify: the 4 flags, the Test context lines |
| `live/(...)Controllers.Gui.StaffConsole.Tools.luau` | modify: `ToolPreview` |
| `live/(...)Controllers.Gui.StaffConsole.View.luau` | modify: the context card's new lines |
| `checks/console_pure.lua`, `checks/console_model.lua`, `checks/console_registry.lua` | modify |
| `checks/console2_lineage.lua` | new, Edit: the moon override |
| `checks/console2_play_run.lua` | new, Play, server: every new card through Dispatch |
| `checks/console2_play_client.lua` | new, Play, client: preview, flags, context card |
| `REPORT.md` | add the phase 2 section (controller) |

`(...)` = `StarterPlayer.StarterPlayerScripts`. The group modules are children of `Features.Admin` with no `OnStart`,
like `Admin.Meta`. In each mirror file name the module's own name is the last part:
`ServerScriptService.Services.Features.Admin.World.luau` installs as `Features.Admin.World`.

---

### Task 0: Baseline and fresh copies

**Files:**
- Create: `tools/admin-console/fetch.py`
- Create: `tools/admin-console/pre2/` (fetched from Studio)
- Modify: `tools/admin-console/live/` (the fetched copies of the systems this phase touches)

**Interfaces:**
- Produces: `pre2/<Dotted.Path>.luau` and the same files in `live/`, for every script any later task changes.

- [ ] **Step 1: Check the worktree**

```bash
cd E:/Nightmare-Highschool/.claude/worktrees/admin-console-2-895704
git status -sb
git log --oneline -3
```
Expected: `## claude/admin-console-2-895704`, clean, HEAD is this plan's commit, then `Console 2 spec: ...`, then
`739067a Staff console 1b: crowded cards grow taller; plan decisions approved`.

- [ ] **Step 2: Write `fetch.py`**

```python
"""Pull scripts' current Source from NH Combat Test (Edit). usage: python -X utf8 -I fetch.py <out_dir> <Dotted.Path> [...]
Writes <out_dir>/<Dotted.Path>.luau byte for byte. Exit 1 if any path is missing."""
import json, os, subprocess, sys
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
PLACE = "placeId: 98950102230473"
HERE = os.path.dirname(os.path.abspath(__file__))
out, paths = sys.argv[1], sys.argv[2:]
os.makedirs(out, exist_ok=True)
bad = 0
for p in paths:
    segs = ", ".join('"%s"' % s for s in p.split("."))
    lua = ('local N = game for _, S in {%s} do N = N and N:FindFirstChild(S) end\n'
           'if not N then return "MISSING" end\n'
           'return game:GetService("HttpService"):JSONEncode({ S = N.Source })' % segs)
    f = os.path.join(HERE, "_fetch.lua")
    open(f, "w", encoding="utf-8").write(lua)
    r = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", PLACE, "Edit", "@" + f],
                       capture_output=True, text=True, encoding="utf-8")
    txt = (r.stdout or "").strip()
    if not txt.startswith("{"):
        print("MISSING", p, txt[:200]); bad += 1; continue
    src = json.loads(txt)["S"]
    open(os.path.join(out, p + ".luau"), "w", encoding="utf-8", newline="").write(src)
    print("ok", p, len(src))
sys.exit(1 if bad else 0)
```

Run `python -X utf8 -I tools/admin-console/fetch.py E:/ClaudeTemp/fetchtest ReplicatedStorage.Lineage`.
Expected: `ok ReplicatedStorage.Lineage <n>`. If the result is cut short (rbxc's output limit), fall back to reading
the script with the MCP's `script_read` tool and save it by hand. Note that in `REPORT.md`.

- [ ] **Step 3: Fetch everything this phase touches**

```bash
python -X utf8 -I tools/admin-console/fetch.py tools/admin-console/pre2 \
  ReplicatedStorage.Functions.StaffConsole ReplicatedStorage.Lineage \
  ServerScriptService.Services.Features.Admin ServerScriptService.Services.Features.Admin.Meta \
  ServerScriptService.Services.School.Notoriety ServerScriptService.Services.School.HallMonitor \
  ServerScriptService.Services.Quests.Investigation \
  StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.Model \
  StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.Tools \
  StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.View
```
Then compare the console files with the repo mirrors:
```bash
for f in ReplicatedStorage.Functions.StaffConsole ServerScriptService.Services.Features.Admin ServerScriptService.Services.Features.Admin.Meta StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.Model StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.Tools StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.View; do cmp tools/admin-console/pre2/$f.luau tools/admin-console/live/$f.luau && echo "same $f"; done
```
Expected: `same` for all six (1b's install left them equal). If one differs, Studio has changes the repo doesn't
know about: stop and tell the owner. Then copy the four system scripts and Lineage into `live/`:
```bash
for f in ReplicatedStorage.Lineage ServerScriptService.Services.School.Notoriety ServerScriptService.Services.School.HallMonitor ServerScriptService.Services.Quests.Investigation; do cp tools/admin-console/pre2/$f.luau tools/admin-console/live/$f.luau; done
```

- [ ] **Step 4: Check the facts the later tasks rely on**

Each line must match. If one doesn't, stop and tell the owner (the task that uses it needs a change).
```bash
cd tools/admin-console/pre2
grep -n "^function Local.AddSummons(P: Player, Type: string, Witness: string?)" ServerScriptService.Services.School.Notoriety.luau
grep -n "^function Local.Escalate(P: Player)" ServerScriptService.Services.School.Notoriety.luau
grep -n "^function Local.Reset(P: Player)" ServerScriptService.Services.School.Notoriety.luau
grep -n "^function Local.Publish(P: Player)" ServerScriptService.Services.School.Notoriety.luau
grep -n "^local Monitors = {}" ServerScriptService.Services.School.HallMonitor.luau
grep -n "^function Local.Spawn(Slot: number)" ServerScriptService.Services.School.HallMonitor.luau
grep -n "^function Local.EndChase(M)" ServerScriptService.Services.School.HallMonitor.luau
grep -n "if Monitors\[Slot\] == M then" ServerScriptService.Services.School.HallMonitor.luau
grep -n "^function Shared.Get(Player: Player, CaseId: string)" ServerScriptService.Services.Quests.Investigation.luau
grep -n "^function Lineage.MoonPhase(day, hour)" ReplicatedStorage.Lineage.luau
grep -n "^function Lineage.MoonEvent(day, hour)" ReplicatedStorage.Lineage.luau
grep -n "^function Lineage.IsFullMoon(day, hour)" ReplicatedStorage.Lineage.luau
cd ../../..
```
And in Studio (Edit, the MCP's `script_grep`, or `execute_luau` with `require` on clones):
- `ServerScriptService.Services.World.Cine` has `Shared.Play(List, CutId, Opts)`, `Shared.IsWatching(Player, CutId?)`.
- `ServerScriptService.Services.Quests.Quests` has `Shared.CineState(Player)` and `Shared.SyncForCine(Player)`.
- `ServerScriptService.Services.World.Tutorial` has `Enter`, `Leave`, `Checkpoint(Player, CutId, Segment)`,
  `CheckpointOf`, `Resume`.
- `ReplicatedStorage.Config.Cine.Cuts.TutorialSneak.Resume.Marks` has `Garden` and `Fence`;
  `Cuts.TutorialBus.Resume.Marks` has `Start`.
- `ReplicatedStorage.Config.Notoriety` has the Bell thresholds. Note the field name and values (the docs say Bell
  1-5 at 10, 25, 45, 70, 90) and the misdeed table's name (the Heat-per-misdeed rows). Write both into Task 5's
  `THRESHOLDS` and `MISDEEDS` lines before starting Task 5.
- The form Look is saved at `Data.GetProfile(P).Lineage.Looks.FormDirection`, and
  `Services.Player.RaceCosmetics.Queue(P)` re-applies race looks. Find the script that handles the player's own
  Look change (`grep -rn "FormDirection\|SetLook" ` with the MCP's `script_grep`), note how it tells the client
  (an attribute or a remote), and write it into Task 7 Step 3's `applyForm` before starting Task 7.

- [ ] **Step 5: Baseline checks (Edit)**

```bash
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_pure.lua
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_registry.lua
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_model.lua
```
Expected: `PASS console_pure`, `PASS console_registry (67 commands)`, `PASS console_model`.

- [ ] **Step 6: Commit**

```bash
git add tools/admin-console/fetch.py tools/admin-console/pre2 tools/admin-console/live
git commit -m "Console 2: fetch script and the pre-phase-2 copies

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 1: The pure rules (`ServerWideOk`, the four flags)

**Files:**
- Modify: `tools/admin-console/live/ReplicatedStorage.Functions.StaffConsole.luau`
- Modify: `tools/admin-console/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.Model.luau`
- Test: `tools/admin-console/checks/console_pure.lua`, `tools/admin-console/checks/console_model.lua`

**Interfaces:**
- Produces:
  - `StaffConsole.SERVER_WIDE_REFUSAL = "Owner only in live servers; use Preview just for me"`
  - `StaffConsole.ServerWideOk(Level: number, Studio: boolean) -> (boolean, string?)`
  - `Model.Flags(P)` also reads `P.Transformed: boolean?`, `P.Bells: number?`, `P.New: boolean?`,
    `P.InCutscene: boolean?` and adds `"TRANSFORMED"`, `"WANTED"` (Bells >= 3), `"NEW"`, `"IN CUTSCENE"`, in that
    order, after the existing flags.

- [ ] **Step 1: Write the failing checks**

In `checks/console_pure.lua`, before `if #Fails > 0`:
```lua
-- (phase 2) server-wide World cards: Studio always; live only the owner
Eq(S.ServerWideOk(2, true), true, "studio level 2 server-wide")
Eq(S.ServerWideOk(0, true), true, "studio level 0 server-wide (Dispatch refuses level 0 earlier)")
Eq(S.ServerWideOk(3, false), true, "live owner server-wide")
local Ok2, Why2 = S.ServerWideOk(2, false)
Eq(Ok2, false, "live level 2 refused") Eq(Why2, "Owner only in live servers; use Preview just for me", "the refusal")
Eq(S.ServerWideOk(1, false), false, "live level 1 refused")
Eq(S.ServerWideOk(nil, false), false, "live no level refused")
Eq(S.SERVER_WIDE_REFUSAL, "Owner only in live servers; use Preview just for me", "refusal constant")
```
In `checks/console_model.lua`, before `if #Fails > 0`:
```lua
-- (phase 2) the four new flags, after the old ones
local F2 = M.Flags({ Note = true; Transformed = true; Bells = 3; New = true; InCutscene = true })
Eq(table.concat(F2, ","), "NOTE,TRANSFORMED,WANTED,NEW,IN CUTSCENE", "phase 2 flags in order")
Eq(table.concat(M.Flags({ Bells = 2 }), ","), "", "Bell 2 is not WANTED")
Eq(table.concat(M.Flags({ Bells = 5 }), ","), "WANTED", "Bell 5 is WANTED")
Eq(table.concat(M.Flags({ Transformed = false; New = false; InCutscene = false }), ","), "", "false flags stay off")
```

- [ ] **Step 2: Implement**

In `ReplicatedStorage.Functions.StaffConsole.luau`, after `Shared.LEVEL_NAMES = ...`:
```lua
-- (phase 2) Season, Moon tonight and Sky change the world for the whole server: allowed in Studio, and in a live
-- server only for the owner. Testers there use Preview just for me (a client tool).
Shared.SERVER_WIDE_REFUSAL = "Owner only in live servers; use Preview just for me"
function Shared.ServerWideOk(Level: number?, Studio: boolean): (boolean, string?)
	if Studio then return true end
	if (tonumber(Level) or 0) >= 3 then return true end
	return false, Shared.SERVER_WIDE_REFUSAL
end
```
In `Controllers.Gui.StaffConsole.Model.luau`, replace `Model.Flags` with:
```lua
function Model.Flags(P: any): { string }
	local Out = {}
	if P.Note then table.insert(Out, "NOTE") end
	if P.Muted then table.insert(Out, "MUTED") end
	if P.Frozen then table.insert(Out, "FROZEN") end
	if P.InMenu then table.insert(Out, "IN MENU") end
	if P.God then table.insert(Out, "GOD") end
	-- (phase 2) from the player list: the Transformation attribute, NHBells, the Prologue not seen yet, a cut or Wickfield
	if P.Transformed == true then table.insert(Out, "TRANSFORMED") end
	if (tonumber(P.Bells) or 0) >= 3 then table.insert(Out, "WANTED") end
	if P.New == true then table.insert(Out, "NEW") end
	if P.InCutscene == true then table.insert(Out, "IN CUTSCENE") end
	return Out
end
```

- [ ] **Step 3: Install (ask the owner first) and run**

```bash
python -X utf8 -I tools/admin-console/install_inplace.py tools/admin-console/pre2 tools/admin-console/live AdminConsole2_20261124 ReplicatedStorage.Functions.StaffConsole StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.Model
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_pure.lua
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_model.lua
```
Expected: `PASS console_pure`, `PASS console_model`. (Before the install, the same checks print FAIL with
`attempt to call a nil value` for `ServerWideOk` and a wrong flags string. That is the failing step.)
Then copy both files from `live/` into `pre2/`.

- [ ] **Step 4: Commit**

```bash
git add tools/admin-console
git commit -m "Console 2: the server-wide rule and the four new row flags (pure)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: The group plumbing in Admin

**Files:**
- Modify: `tools/admin-console/live/ServerScriptService.Services.Features.Admin.luau`
- Test: `tools/admin-console/checks/console_registry.lua`

**Interfaces:**
- Consumes: `StaffConsole.ServerWideOk` (Task 1).
- Produces (the group modules in Tasks 3, 5 and 6 rely on these exact names):
  - A group module returns `function(H) -> { [Id: string]: { Meta: MetaEntry, Run: (Admin, Target, Args, TargetId) -> (boolean, string) } }`.
    It must not call `H` while building the table (the registry check calls it with a stub).
  - `H = { svc: (path: string) -> any?, str: (v: any, max: number) -> string, profile: (P) -> (Profile?, Data?),
    today: () -> number, Level: (P) -> number, ServerWide: (A: Player) -> (boolean, string?),
    notify: (P, Title, Text?, Kind?) -> (), Meta: (Name, Kind, Extra?) -> ArgSchema }`
  - `Admin.GROUPS = { "World", "Story", "BellTower" }` (a missing child module is skipped with a warning).
  - `Admin.TestLiveMode: boolean` (Studio only; `ServerWide` treats Studio as live while it is true).

- [ ] **Step 1: Write the failing check**

Replace the id-collecting block and the count in `checks/console_registry.lua` (from `-- the command ids in
Admin's source` through `if N ~= 67 ...`) with:
```lua
-- the command ids in Admin's source (every top-level `C.<Id> = {`) plus each group module's ids
local Ids = {}
for Id in string.gmatch("\n" .. Admin.Source, "\nC%.(%w+) = {") do Ids[Id] = true end
local Stub = setmetatable({}, { __index = function() return function() error("a group called H while building") end end })
Stub.Meta = function(Name, Kind, Extra) local T = Extra or {} T.Name = Name T.Kind = Kind return T end
local GroupMeta = {}
for _, G in { "World", "Story", "BellTower" } do
	local Mod = Admin:FindFirstChild(G)
	if not Mod then table.insert(Fails, "Admin." .. G .. " missing") continue end
	local OkB, Built = pcall(require(Mod:Clone()), Stub)
	if not OkB then table.insert(Fails, "Admin." .. G .. ": " .. tostring(Built)) continue end
	for Id, E in Built do
		if Ids[Id] or GroupMeta[Id] then table.insert(Fails, "id taken twice: " .. Id) end
		Ids[Id] = true
		GroupMeta[Id] = E.Meta
		if typeof(E.Run) ~= "function" then table.insert(Fails, Id .. " has no Run") end
	end
end
for Id, D in GroupMeta do Meta[Id] = D end
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
if N ~= 85 then table.insert(Fails, "commands: " .. N .. ", want 85") end
-- (phase 2) the 18 new server cards are all there
for _, Id in { "TimePreset", "SetSeason", "SetMoon", "SetSky", "PlayCutscene", "CutsceneSeen", "TutorialEnter",
	"TutorialJump", "TutorialLeave", "GiveClue", "ResetCase", "SetHeat", "SetBells", "GiveSummons", "ClearNotoriety",
	"HallMonitors", "WhosWanted", "FormDirection" } do
	if not Ids[Id] then table.insert(Fails, "missing phase 2 card " .. Id) end
end
```
In the same file, add `ResetCase = true, ClearNotoriety = true, HallMonitors = true` to `DANGER`.

Run `python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_registry.lua`.
Expected: FAIL, listing `Admin.World missing`, `Admin.Story missing`, `Admin.BellTower missing`, `commands: 67, want
85` and the missing cards. This check passes only at the end of Task 7. Tasks 3, 5 and 6 each shrink its list.

- [ ] **Step 2: Add `H`, the merge and `TestLiveMode` to Admin**

In `Admin.luau`, after `Shared.TestSkipBanApi = false` add:
```lua
-- (phase 2, Studio only) the Play check sets this to try the live-server rule for Season, Moon and Sky
Shared.TestLiveMode = false
```
Directly above `-- the desk's pick lists (sent with Info)` (so `svc`, `str`, `profile`, `today` and `notify` exist),
add:
```lua
---------------------------------------------------------------- (phase 2) group modules

-- Season, Moon tonight and Sky: Studio always (unless the Play check asks for the live rule); live, the owner only
function Shared.ServerWide(A: Player): (boolean, string?)
	local Studio = RunService:IsStudio() and not Shared.TestLiveMode
	return StaffConsole.ServerWideOk(Shared.Level(A), Studio)
end

local H = {
	svc = svc; str = str; profile = profile; today = today; Level = function(P) return Shared.Level(P) end;
	ServerWide = function(A) return Shared.ServerWide(A) end; notify = notify;
	Meta = function(Name: string, Kind: string, Extra: any?) local T = Extra or {} T.Name = Name T.Kind = Kind return T end;
}
Shared.GROUPS = { `World`, `Story`, `BellTower` }
for _, Name in Shared.GROUPS do
	local Mod = script:FindFirstChild(Name)
	if not Mod then warn(`[Admin] Admin.{Name} missing: its cards are not in the console`) continue end
	for Id, E in require(Mod)(H) do
		if C[Id] or Meta[Id] then error(`[Admin] Admin.{Name}: the id {Id} is already taken`) end
		C[Id] = { Run = E.Run }
		Meta[Id] = E.Meta
	end
end
```
`Shared.OnStart` already warns about a C entry with no Meta and validates every Meta entry, so merged cards are
checked at start too.

- [ ] **Step 3: Install (ask the owner first) and check that nothing broke**

```bash
python -X utf8 -I tools/admin-console/install_inplace.py tools/admin-console/pre2 tools/admin-console/live AdminConsole2_20261124 ServerScriptService.Services.Features.Admin
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_play_server.lua
```
Expected: the in-place install reports success, and `console_play_server` passes as before. In Studio's Output there
are three warnings, `Admin.World missing`, `Admin.Story missing` and `Admin.BellTower missing`, the next time the
game starts (not now: Edit mode doesn't run OnStart). Copy `Admin.luau` from `live/` into `pre2/`.

- [ ] **Step 4: Commit**

```bash
git add tools/admin-console
git commit -m "Console 2: group modules merge into the registry; the server-wide helper

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: World (the moon override and `Admin.World`)

**Files:**
- Modify: `tools/admin-console/live/ReplicatedStorage.Lineage.luau`
- Create: `tools/admin-console/live/ServerScriptService.Services.Features.Admin.World.luau`
- Test: `tools/admin-console/checks/console2_lineage.lua`

**Interfaces:**
- Consumes: `H` (Task 2).
- Produces:
  - `Lineage.MoonOverride(day, hour) -> string?`: the override name when `workspace.NHMoonOverrideNight ==
    Lineage.NightOf(day, hour)`, else nil.
  - `Lineage.MOON_CHOICES = { "Full", "Waxing", "Waning", "New", "Crimson", "Blue" }`
  - Cards `TimePreset`, `SetSeason`, `SetMoon`, `SetSky`.

- [ ] **Step 1: Write the failing check**

`tools/admin-console/checks/console2_lineage.lua` (Edit VM; it sets the two workspace attributes and always puts them
back):
```lua
local L = require(game.ReplicatedStorage.Lineage:Clone())
local Fails = {}
local function Eq(Got, Want, What) if Got ~= Want then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end
local W = workspace
local Old = { W:GetAttribute("NHMoonOverride"), W:GetAttribute("NHMoonOverrideNight") }
local ok, err = pcall(function()
	W:SetAttribute("NHMoonOverride", nil) W:SetAttribute("NHMoonOverrideNight", nil)
	-- no override: the cycle as before (night 1 Waning, night 2 New, night 4 Full; night 16 is the Blue event, night 32 Crimson)
	Eq(L.MoonPhase(1, 22), "Waning", "plain phase") Eq(L.MoonPhase(2, 22), "New", "plain night 2")
	Eq(L.IsFullMoon(4, 22), true, "plain full") Eq(L.MoonEvent(16, 22), "Blue", "plain event 16") Eq(L.MoonEvent(32, 22), "Crimson", "plain event 32")
	Eq(L.MoonOverride(1, 22), nil, "no override")
	-- tonight (night 1) is Full
	W:SetAttribute("NHMoonOverride", "Full") W:SetAttribute("NHMoonOverrideNight", 1)
	Eq(L.MoonPhase(1, 22), "Full", "override at 22:00") Eq(L.MoonPhase(2, 3), "Full", "still night 1 at 03:00 next day")
	Eq(L.MoonPhase(1, 12), "Full", "by day the coming night") Eq(L.IsFullMoon(1, 22), true, "override full")
	Eq(L.NightsUntilFull(1, 22), 0, "full tonight")
	Eq(L.MoonPhase(2, 22), "New", "the next night is back on the cycle")
	-- New is not full
	W:SetAttribute("NHMoonOverride", "New")
	Eq(L.MoonPhase(1, 22), "New", "override new") Eq(L.IsFullMoon(1, 22), false, "New is not full")
	-- Crimson: a full moon with the crimson event
	W:SetAttribute("NHMoonOverride", "Crimson")
	Eq(L.MoonPhase(1, 22), "Full", "crimson is a full phase") Eq(L.MoonEvent(1, 22), "Crimson", "crimson event")
	Eq(L.IsFullMoon(1, 22), true, "crimson is full")
	-- an ordinary moon on an event night: the event goes
	W:SetAttribute("NHMoonOverride", "Waxing") W:SetAttribute("NHMoonOverrideNight", 16)
	Eq(L.MoonEvent(16, 22), nil, "an ordinary moon has no event") Eq(L.MoonPhase(16, 22), "Waxing", "waxing on night 16")
	-- junk is ignored
	W:SetAttribute("NHMoonOverride", "Purple") Eq(L.MoonPhase(16, 22), "Full", "unknown override ignored")
end)
W:SetAttribute("NHMoonOverride", Old[1]) W:SetAttribute("NHMoonOverrideNight", Old[2])
if not ok then return "FAIL error: " .. tostring(err) end
if #Fails > 0 then return "FAIL " .. #Fails .. "\n" .. table.concat(Fails, "\n") end
return "PASS console2_lineage"
```
Run it. Expected: `FAIL error: attempt to call a nil value (field 'MoonOverride')`.

- [ ] **Step 2: Implement the override in Lineage**

After `function Lineage.NightOf(day, hour) ... end` add:
```lua
-- (console 2) the staff console's "Moon tonight": workspace NHMoonOverride (a moon name) for the night
-- NHMoonOverrideNight (Lineage.NightOf). It ends by itself when that night is over. Replicated, so both sides agree.
Lineage.MOON_CHOICES = { "Full", "Waxing", "Waning", "New", "Crimson", "Blue" }
function Lineage.MoonOverride(day, hour)
	if type(day) ~= "number" or type(hour) ~= "number" then return nil end
	local Name = workspace:GetAttribute("NHMoonOverride")
	if type(Name) ~= "string" or not table.find(Lineage.MOON_CHOICES, Name) then return nil end
	if workspace:GetAttribute("NHMoonOverrideNight") ~= Lineage.NightOf(day, hour) then return nil end
	return Name
end
```
Then, as the first lines after each function's type check:
- `Lineage.MoonPhase`: `local O = Lineage.MoonOverride(day, hour) if O then return if O == "Crimson" or O == "Blue" then "Full" else O end`
- `Lineage.MoonEvent`: `local O = Lineage.MoonOverride(day, hour) if O then return if O == "Crimson" or O == "Blue" then O else nil end`
- `Lineage.IsFullMoon` (after its night-window check): `if Lineage.MoonOverride(day, hour) then return Lineage.MoonPhase(day, hour) == "Full" end`
- `Lineage.NightsUntilFull`: `if Lineage.MoonPhase(day, hour) == "Full" and Lineage.MoonOverride(day, hour) then return 0 end`

`Lineage.NightOf` must be defined above `MoonOverride`. It is (Task 0 Step 4 checked the order). If `IsFullMoon`
comes before `NightOf` in the file, that's fine: Luau resolves `Lineage.X` when the function runs.

- [ ] **Step 3: Write `Admin.World`**

`tools/admin-console/live/ServerScriptService.Services.Features.Admin.World.luau`:
```lua
--[[
	Admin.World (server, no OnStart): the console's World cards (spec docs/superpowers/specs/2026-11-24-admin-console-2-design.md §2).
	A group module: Features.Admin calls it with its helpers (H) and merges the cards into the registry.
	Season, Moon tonight and Sky are server-wide: H.ServerWide refuses them below the owner in live servers.
	Preview just for me is a client tool (Controllers.Gui.StaffConsole.Tools), not here.
]]
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local M, T = `Moderate`, `Test`
local PRESETS = { Dawn = `06:00`; Noon = `12:00`; Golden = `17:00`; Dusk = `18:30`; Midnight = `00:00`; Witching = `03:00` }
local SEASONS = { `Autumn`, `Winter`, `Spring`, `Summer`, `Nightmare` }

return function(H)
	local A = H.Meta
	local function clockDay(): (number, number)
		local SC = H.svc(`School.SchoolClock`)
		local S = SC and SC.GetState()
		return S and S.Day or 0, S and S.Hour or 12
	end
	return {
		TimePreset = {
			Meta = { Side = T; Section = `World`; Title = `Time preset`; Help = `Dawn, noon, golden hour, dusk, midnight or the witching hour`;
				Icon = `Time`; Level = 2; Target = `none`; Danger = false; Synonyms = { `dawn`, `dusk`, `midnight` };
				Args = { A(`Preset`, `choice`, { Choices = { `Dawn`, `Noon`, `Golden`, `Dusk`, `Midnight`, `Witching` }; Required = true }) } };
			Run = function(Admin, _, a)
				local SC = H.svc(`School.SchoolClock`)
				if not SC then return false, `The school clock is missing` end
				local At = PRESETS[a.Preset]
				SC.SetTime(At)
				return true, `Clock set to {At} ({a.Preset})`
			end;
		};
		SetSeason = {
			Meta = { Side = T; Section = `World`; Title = `Season`; Help = `The season for the whole server (live: owner)`;
				Icon = `SecWorld`; Level = 2; Target = `none`; Danger = false; Synonyms = { `winter`, `nightmare nights`, `event` };
				Args = { A(`Season`, `choice`, { Choices = SEASONS; Required = true }) } };
			Run = function(Admin, _, a)
				local Ok, Why = H.ServerWide(Admin)
				if not Ok then return false, Why end
				local Old = workspace:GetAttribute(`NHSeason`) or `Autumn`
				workspace:SetAttribute(`NHSeason`, if a.Season == `Autumn` then nil else a.Season)
				return true, `Season: {Old} to {a.Season}`
			end;
		};
		SetMoon = {
			Meta = { Side = T; Section = `World`; Title = `Moon tonight`; Help = `Tonight's moon for the whole server (live: owner)`;
				Icon = `Moon`; Level = 2; Target = `none`; Danger = false; Synonyms = { `crimson`, `blue moon`, `new moon` };
				Args = { A(`Moon`, `choice`, { Choices = { `Auto`, `Full`, `Waxing`, `Waning`, `New`, `Crimson`, `Blue` }; Required = true }) } };
			Run = function(Admin, _, a)
				local Ok, Why = H.ServerWide(Admin)
				if not Ok then return false, Why end
				local Lin = require(ReplicatedStorage.Lineage)
				local Day, Hour = clockDay()
				local Old = Lin.MoonOverride(Day, Hour) or `Auto`
				if a.Moon == `Auto` then
					workspace:SetAttribute(`NHMoonOverride`, nil)
					workspace:SetAttribute(`NHMoonOverrideNight`, nil)
				else
					workspace:SetAttribute(`NHMoonOverrideNight`, Lin.NightOf(Day, Hour))
					workspace:SetAttribute(`NHMoonOverride`, a.Moon)
				end
				pcall(function() H.svc(`Features.MoonPhases`).Tick() end) -- the workspace moon attributes now, not in a second
				return true, `Moon tonight: {Old} to {a.Moon}`
			end;
		};
		SetSky = {
			Meta = { Side = T; Section = `World`; Title = `Sky`; Help = `Storm, or back to the normal sky (live: owner)`;
				Icon = `SecWorld`; Level = 2; Target = `none`; Danger = false; Synonyms = { `storm`, `weather` };
				Args = { A(`Sky`, `choice`, { Choices = { `Auto`, `Storm` }; Required = true }) } };
			Run = function(Admin, _, a)
				local Ok, Why = H.ServerWide(Admin)
				if not Ok then return false, Why end
				local Old = workspace:GetAttribute(`NHSky`) or `Auto`
				workspace:SetAttribute(`NHSky`, if a.Sky == `Auto` then nil else a.Sky)
				return true, `Sky: {Old} to {a.Sky}`
			end;
		};
	}
end
```
Remove the unused `M` local if Selene or Studio's linter flags it. Check `Config.ConsoleArt.Icons` has `Time`, `Moon`
and `SecWorld` (`grep -n "SecWorld\|Moon =\|Time =" tools/admin-console/live/ReplicatedStorage.Config.ConsoleArt.luau`).
If `SecWorld` is missing, use `Moon` for Season and Sky.

- [ ] **Step 4: Install (ask the owner first) and run**

```bash
python -X utf8 -I tools/admin-console/install_inplace.py tools/admin-console/pre2 tools/admin-console/live AdminConsole2_20261124 ReplicatedStorage.Lineage
python -X utf8 -I tools/admin-console/install_new.py tools/admin-console/live/ServerScriptService.Services.Features.Admin.World.luau
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console2_lineage.lua
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_registry.lua
```
Expected: `PASS console2_lineage`. The registry check still FAILs, but no longer lists `Admin.World missing` or the
four World cards. Copy `Lineage` and `Admin.World` from `live/` into `pre2/`.

- [ ] **Step 5: Commit**

```bash
git add tools/admin-console
git commit -m "Console 2: World cards (time presets, season, moon tonight, sky) and the Lineage moon override

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Preview just for me (client tool)

**Files:**
- Modify: `tools/admin-console/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.Tools.luau`
- Test: `tools/admin-console/checks/console_tools.lua`

**Interfaces:**
- Produces: tool card `ToolPreview` (Test / World, level 2, Target none) with args `Season`, `Moon`, `Sky` (choices,
  each with `Off`). `Tools.Do("ToolPreview", Values)` sets or clears `NHSeasonPreview`, `NHMoonPhasePreview`,
  `NHMoonPreview` (true only for Full) and `NHSkyPreview` on `Players.LocalPlayer`, and returns `(true, "Preview: ...")`.
  `Tools.PreviewAttrs(Values) -> { [string]: any }` (pure) is what it applies.

- [ ] **Step 1: Write the failing check**

Look at `checks/console_tools.lua` for its `Eq` and how it loads `Tools` (a clone of the module). Before its
`if #Fails > 0`, add:
```lua
-- (phase 2) Preview just for me
local PV
for _, D in T.Defs do if D.Id == "ToolPreview" then PV = D end end
Eq(PV ~= nil, true, "ToolPreview card")
if PV then Eq(PV.Section, "World", "preview section") Eq(PV.Level, 2, "preview level") Eq(#PV.Args, 3, "preview args") end
local A1 = T.PreviewAttrs({ Season = "Winter"; Moon = "Full"; Sky = "Storm" })
Eq(A1.NHSeasonPreview, "Winter", "season") Eq(A1.NHMoonPhasePreview, "Full", "moon") Eq(A1.NHMoonPreview, true, "full moon size")
Eq(A1.NHSkyPreview, "Storm", "sky")
local A2 = T.PreviewAttrs({ Season = "Off"; Moon = "Crimson"; Sky = "Off" })
Eq(A2.NHSeasonPreview, nil, "season off") Eq(A2.NHMoonPhasePreview, "Crimson", "crimson") Eq(A2.NHMoonPreview, nil, "not full")
Eq(A2.NHSkyPreview, nil, "sky off")
local A3 = T.PreviewAttrs({ Season = "Autumn" })
Eq(A3.NHSeasonPreview, nil, "Autumn is the normal season: no preview") Eq(A3.NHMoonPhasePreview, nil, "missing moon is off")
```
(If the check names the module something other than `T`, use its name.) Run it: FAIL (no `ToolPreview`).

- [ ] **Step 2: Implement**

In `Tools.luau`, after `Tools.Defs = { ... }` add:
```lua
-- (phase 2) Preview just for me: the sky's own preview attributes on this client only (DayCycle, MoonPhases,
-- FullMoon and SkyMotion read them). Nothing goes to the server, so it isn't logged and testers may use it live.
local PV = card("ToolPreview", "World", "Preview just for me", "A season, moon or sky on your screen only", "Moon", 2, "none", { "preview", "my sky" })
PV.Args = {
	{ Name = "Season"; Kind = "choice"; Choices = { "Off", "Autumn", "Winter", "Spring", "Summer", "Nightmare" } };
	{ Name = "Moon"; Kind = "choice"; Choices = { "Off", "Full", "Waxing", "Waning", "New", "Crimson", "Blue" } };
	{ Name = "Sky"; Kind = "choice"; Choices = { "Off", "Storm" } };
}
table.insert(Tools.Defs, PV)

function Tools.PreviewAttrs(V: any): { [string]: any }
	V = V or {}
	local function on(X) return if X ~= nil and X ~= "Off" then X else nil end
	local Season = on(V.Season)
	if Season == "Autumn" then Season = nil end
	local Moon = on(V.Moon)
	return { NHSeasonPreview = Season; NHMoonPhasePreview = Moon; NHMoonPreview = if Moon == "Full" then true else nil; NHSkyPreview = on(V.Sky) }
end
```
In `Tools.Do`, before `return false, "Unknown tool"`:
```lua
	if Id == "ToolPreview" then
		local A = Tools.PreviewAttrs(_Values)
		for _, K in { "NHSeasonPreview", "NHMoonPhasePreview", "NHMoonPreview", "NHSkyPreview" } do Player:SetAttribute(K, A[K]) end
		local Parts = {}
		if A.NHSeasonPreview then table.insert(Parts, A.NHSeasonPreview) end
		if A.NHMoonPhasePreview then table.insert(Parts, A.NHMoonPhasePreview .. " moon") end
		if A.NHSkyPreview then table.insert(Parts, A.NHSkyPreview) end
		return true, if #Parts > 0 then "Preview on your screen: " .. table.concat(Parts, ", ") else "Preview off"
	end
```
Also update the module's header comment to list "Preview just for me".

- [ ] **Step 3: Install (ask the owner first) and run**

```bash
python -X utf8 -I tools/admin-console/install_inplace.py tools/admin-console/pre2 tools/admin-console/live AdminConsole2_20261124 StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.Tools
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_tools.lua
```
Expected: `PASS console_tools`. Copy `Tools` into `pre2/`.

- [ ] **Step 4: Commit**

```bash
git add tools/admin-console
git commit -m "Console 2: Preview just for me (client tool)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Bell Tower (Notoriety and HallMonitor calls, `Admin.BellTower`)

**Files:**
- Modify: `tools/admin-console/live/ServerScriptService.Services.School.Notoriety.luau`
- Modify: `tools/admin-console/live/ServerScriptService.Services.School.HallMonitor.luau`
- Create: `tools/admin-console/live/ServerScriptService.Services.Features.Admin.BellTower.luau`
- Test: `tools/admin-console/checks/console2_play_run.lua` (its Bell Tower block, run in Task 8)

**Interfaces:**
- Consumes: `H` (Task 2).
- Produces:
  - `Notoriety.SetHeat(P: Player, Heat: number)`: clamps to 0-100. At 0 it calls `Clear`. Otherwise sets Heat,
    re-tiers (`F.Tier`), re-arms the steps above the new bell (spec delta 9), marks them seen now (so the search starts
    from here), runs `Escalate` if the bell rose, sets state `Lit` if it was empty, then publishes and fires `Changed`.
  - `Notoriety.Clear(P: Player)`: `Local.Reset`, drops every summons (nothing booked), publishes, fires `Changed`.
  - `Notoriety.AddSummons(P: Player, Type: string) -> boolean`: false when the cap (`Config.SummonsLimit`) is full.
  - `HallMonitor.SetEnabled(On: boolean)` and `HallMonitor.IsEnabled() -> boolean`. Off ends every chase, destroys the
    monitors and leaves the slots empty. On spawns every empty slot. Mirrors `workspace.NHMonitorsOff`.
  - Cards `SetHeat`, `SetBells`, `GiveSummons`, `ClearNotoriety`, `HallMonitors`, `WhosWanted`.

- [ ] **Step 1: Notoriety's public calls**

In `Notoriety.luau`, after `function Shared.Get(P: Player) ... end` add:
```lua
-- (console 2) the staff console's Bell Tower cards
function Shared.Clear(P: Player)
	Local.Reset(P)
	local D = Discipline.GetData(P)
	if D then D.Summons = {} end
	Local.Publish(P)
	local S = Local.Get(P)
	Shared.Changed:Fire(P, S.Tier, S.State)
end

function Shared.SetHeat(P: Player, Heat: number)
	Heat = math.clamp(tonumber(Heat) or 0, 0, 100)
	if Heat <= 0 then Shared.Clear(P) return end
	local S = Local.Get(P)
	local Old = S.Tier
	S.Heat = Heat
	S.Tier = F.Tier(Heat)
	-- lowering re-arms the steps above the new bell, so raising again runs them again
	if S.Tier < Config.HuntTier then S.Responded, S.RespondOk = false, nil end
	if S.Tier < Config.ConvergeTier then S.Converged = false end
	if S.Tier < Config.TollTier then S.Tolled = false end
	S.LastSeenAt = S.T
	local Root = Local.Root(P)
	if Root then S.LastSeenPos = Root.Position end
	if S.Tier > Old then Local.Escalate(P) end
	if S.Tier > 0 and S.State == `` then S.State = `Lit` end
	Local.Publish(P)
	Shared.Changed:Fire(P, S.Tier, S.State)
end

function Shared.AddSummons(P: Player, Type: string): boolean
	local D = Discipline.GetData(P)
	if not D then return false end
	if D.Summons and #D.Summons >= Config.SummonsLimit then return false end
	Local.AddSummons(P, Type, `Staff`)
	Local.Publish(P)
	return true
end
```

- [ ] **Step 2: HallMonitor's on/off**

In `HallMonitor.luau`, after `local Monitors = {} :: { any }` add `local Off = false`. In `Local.Spawn(Slot)`, as its
first line: `if Off then return end`. After `function Shared.GetMonitors() ... end` add:
```lua
-- (console 2) the staff console's Hall monitors card. Not saved: a new server starts with them on.
function Shared.IsEnabled(): boolean return not Off end

function Shared.SetEnabled(On: boolean)
	if On == not Off then return end
	Off = not On
	workspace:SetAttribute(`NHMonitorsOff`, if Off then true else nil)
	if Off then
		for Slot, M in Monitors do
			pcall(Local.EndChase, M)
			Monitors[Slot] = nil -- before Destroy: the respawn watcher checks Monitors[Slot] == M
			if M.Model and M.Model.Parent then M.Model:Destroy() end
		end
	else
		for Slot = 1, Settings.Count do
			if not Monitors[Slot] then task.spawn(Local.Spawn, Slot) end
		end
	end
end
```
Check the field name for the monitor's model in `Local.Spawn` (Task 0's copy): the code above assumes `M.Model`. If
`Local.Spawn` stores it under another name, use that name.

- [ ] **Step 3: Write `Admin.BellTower`**

Fill in the two lines marked from Task 0 Step 4 (`THRESHOLDS`: the config field with the Bell thresholds;
`MISDEEDS`: the Heat-per-misdeed table's name).
```lua
--[[
	Admin.BellTower (server, no OnStart): the console's Bell Tower cards (spec 2026-11-24-admin-console-2 §2), on the
	School section. A group module (see Admin.World). Calls Services.School.Notoriety and HallMonitor's public API.
]]
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local Players = game:GetService(`Players`)
local Cfg = require(ReplicatedStorage.Config.Notoriety)
local THRESHOLDS = Cfg.Thresholds -- (Task 0 Step 4) the Bell 1-5 Heat thresholds, e.g. { 10, 25, 45, 70, 90 }
local MISDEEDS = Cfg.Gain -- (Task 0 Step 4) the Heat-per-misdeed rows, keyed by misdeed

return function(H)
	local A = H.Meta
	local T = `Test`
	local function nt() return H.svc(`School.Notoriety`) end
	local Types = {}
	for K in MISDEEDS do table.insert(Types, K) end
	table.sort(Types)
	return {
		SetHeat = {
			Meta = { Side = T; Section = `School`; Title = `Set Heat`; Help = `Their notoriety Heat, 0 to 100 (the Bells follow)`; Icon = `Discipline`;
				Level = 2; Target = `required`; Danger = false; Synonyms = { `heat`, `notoriety` };
				Args = { A(`Heat`, `number`, { Min = 0; Max = 100; Required = true }) } };
			Run = function(Admin, Tg, a)
				local N = nt() if not N then return false, `Notoriety is missing` end
				local Old = N.Get(Tg).Heat
				N.SetHeat(Tg, a.Heat)
				return true, `{Tg.Name}: Heat {Old} to {a.Heat} (Bell {N.Get(Tg).Tier})`
			end;
		};
		SetBells = {
			Meta = { Side = T; Section = `School`; Title = `Set Bells`; Help = `Their Bells, 0 to 5 (Bell 3: monitors chase; 4: they converge)`; Icon = `Discipline`;
				Level = 2; Target = `required`; Danger = false; Synonyms = { `bells`, `wanted` };
				Args = { A(`Bells`, `choice`, { Choices = { 0, 1, 2, 3, 4, 5 }; Required = true }) } };
			Run = function(Admin, Tg, a)
				local N = nt() if not N then return false, `Notoriety is missing` end
				local Old = N.Get(Tg).Tier
				N.SetHeat(Tg, if a.Bells == 0 then 0 else THRESHOLDS[a.Bells])
				return true, `{Tg.Name}: Bell {Old} to {a.Bells}`
			end;
		};
		GiveSummons = {
			Meta = { Side = T; Section = `School`; Title = `Give a summons`; Help = `They must report to Room 106 outside class`; Icon = `Jail`;
				Level = 2; Target = `required`; Danger = false; Synonyms = { `summons`, `room 106` };
				Args = { A(`Type`, `choice`, { Label = `Misdeed`; From = `Misdeeds`; Required = true }) } };
			Run = function(Admin, Tg, a)
				local N = nt() if not N then return false, `Notoriety is missing` end
				local Book = require(ReplicatedStorage.Functions.Notoriety).BookType(a.Type)
				if not N.AddSummons(Tg, Book) then return false, `{Tg.Name} already owes {Cfg.SummonsLimit} summonses` end
				return true, `Summons for {Tg.Name}: {Book}`
			end;
		};
		ClearNotoriety = {
			Meta = { Side = T; Section = `School`; Title = `Clear notoriety`; Help = `Heat, Bells and summons cleared (nothing booked)`; Icon = `Discipline`;
				Level = 2; Target = `required`; Danger = true; Synonyms = { `clear heat`, `clear bells` }; Args = {} };
			Run = function(Admin, Tg)
				local N = nt() if not N then return false, `Notoriety is missing` end
				N.Clear(Tg)
				return true, `Cleared {Tg.Name}'s notoriety`
			end;
		};
		HallMonitors = {
			Meta = { Side = T; Section = `School`; Title = `Hall monitors`; Help = `On or off for this server`; Icon = `Spectate`;
				Level = 2; Target = `none`; Danger = true; Synonyms = { `monitors`, `patrol` };
				Args = { A(`On`, `toggle`, { Label = `On`; Required = true }) } };
			Run = function(Admin, _, a)
				local HM = H.svc(`School.HallMonitor`)
				if not (HM and HM.SetEnabled) then return false, `Hall monitors are missing` end
				if HM.IsEnabled() == a.On then return false, `Hall monitors are already {if a.On then `on` else `off`}` end
				HM.SetEnabled(a.On)
				return true, `Hall monitors {if a.On then `on` else `off`}`
			end;
		};
		WhosWanted = {
			Meta = { Side = T; Section = `School`; Title = `Who's Wanted`; Help = `Students at Bell 3 or more`; Icon = `Spectate`;
				Level = 2; Target = `none`; Danger = false; Synonyms = { `wanted list`, `hunted` }; Args = {} };
			Run = function()
				local N = nt() if not N then return false, `Notoriety is missing` end
				local Out = {}
				for _, P in Players:GetPlayers() do
					local S = N.Get(P)
					if S.Tier >= 3 then table.insert(Out, `{P.Name} (Bell {S.Tier}, Heat {math.floor(S.Heat)}, {if S.State ~= `` then S.State else `-`})`) end
				end
				if #Out == 0 then return true, `Nobody is Wanted` end
				return true, `Wanted: ` .. table.concat(Out, `; `)
			end;
		};
	}
end
```
`Get` is safe for a player with no state: it makes a zero state. `GiveSummons` reads `From = "Misdeeds"`. Task 7 adds
`Misdeeds` to `Admin.Lists()`. `Toggle` args with `Required = true` accept `false` (CheckArgs only treats nil and ""
as missing).

- [ ] **Step 4: Install (ask the owner first) and check**

```bash
python -X utf8 -I tools/admin-console/install_inplace.py tools/admin-console/pre2 tools/admin-console/live AdminConsole2_20261124 ServerScriptService.Services.School.Notoriety ServerScriptService.Services.School.HallMonitor
python -X utf8 -I tools/admin-console/install_new.py tools/admin-console/live/ServerScriptService.Services.Features.Admin.BellTower.luau
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_registry.lua
python -X utf8 -I E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py luau "placeId: 98950102230473" Edit @tools/belltower-r2/checks/nt_pure.lua
```
Expected: the registry list no longer names the BellTower cards. `nt_pure` still passes (the pure maths didn't
change). Copy the three files into `pre2/`.

- [ ] **Step 5: Commit**

```bash
git add tools/admin-console
git commit -m "Console 2: Bell Tower cards; Notoriety SetHeat/Clear/AddSummons and hall monitors on/off

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Story (`Investigation.ResetCase`, `Admin.Story`)

**Files:**
- Modify: `tools/admin-console/live/ServerScriptService.Services.Quests.Investigation.luau`
- Create: `tools/admin-console/live/ServerScriptService.Services.Features.Admin.Story.luau`

**Interfaces:**
- Consumes: `H` (Task 2). Lists `Cutscenes`, `Clues`, `Cases` (added in Task 7).
- Produces:
  - `Investigation.ResetCase(Player, CaseId) -> boolean`: empties that case's `Clues`, `Insights` and `Solved`, then
    `Hooks.Sync` and `Hooks.Changed(Player, CaseId, "Clues")`.
  - A local `CHECKPOINTS = { Garden = "TutorialSneak:Garden", Fence = "TutorialSneak:Fence", Bus = "TutorialBus:Start" }`
    (not exported).
  - Cards `PlayCutscene`, `CutsceneSeen`, `TutorialEnter`, `TutorialJump`, `TutorialLeave`, `GiveClue`, `ResetCase`.

- [ ] **Step 1: `Investigation.ResetCase`**

After `function Shared.Grant(...) ... end` add:
```lua
-- (console 2) the staff console's Reset a case: clues, links (Insights) and the deduction for one case
function Shared.ResetCase(Player: Player, CaseId: string): boolean
	local C = Shared.Get(Player, CaseId)
	if not C then return false end
	C.Clues, C.Insights, C.Solved = {}, {}, false
	Hooks.Sync(Player)
	Hooks.Changed(Player, CaseId, `Clues`)
	return true
end
```
Check in Task 0's copy that the case table has no other per-case fields (for example a deduction cooldown or tries
count). If it has, clear those too, and say so in the commit message.

- [ ] **Step 2: Write `Admin.Story`**

```lua
--[[
	Admin.Story (server, no OnStart): the console's cutscene, tutorial and case cards (spec 2026-11-24-admin-console-2 §2).
	A group module (see Admin.World). Cutscene state lives in the Quests block (Quests.CineState: CutId -> "Started" |
	"Seen"); a replay (the default) writes nothing.
]]
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
-- the tutorial's three jump points, as Tutorial.Checkpoint strings (Config.Cine Cuts[..].Resume maps each to a mark)
local CHECKPOINTS = { Garden = `TutorialSneak:Garden`; Fence = `TutorialSneak:Fence`; Bus = `TutorialBus:Start` }

return function(H)
	local A = H.Meta
	local T = `Test`
	local function cine() return H.svc(`World.Cine`) end
	local function tut() return H.svc(`World.Tutorial`) end
	local function cutName(Id) local C = require(ReplicatedStorage.Config.Cine).Cuts[Id] return C and C.Name or Id end
	return {
		PlayCutscene = {
			Meta = { Side = T; Section = `Story`; Title = `Play a cutscene`; Help = `For you, or the selected student (Replay saves nothing)`; Icon = `SecStory`;
				Level = 2; Target = `optional`; Danger = false; Synonyms = { `cutscene`, `cine`, `replay` };
				Args = { A(`Id`, `choice`, { Label = `Cutscene`; From = `Cutscenes`; Required = true }), A(`Replay`, `toggle`, { Default = true }) } };
			Run = function(Admin, Tg, a)
				local Cn = cine() if not Cn then return false, `Cine is missing` end
				local Who = Tg or Admin
				if Cn.IsWatching(Who) then return false, `{Who.Name} is in a cutscene already` end
				local Replay = a.Replay ~= false
				local Id = Cn.Play({ Who }, a.Id, { Replay = Replay; Skippable = true })
				if not Id then return false, `Couldn't play it for {Who.Name} (in the menu, or no character)` end
				return true, `Playing {cutName(a.Id)} for {Who.Name}{if Replay then ` (replay)` else ` (first viewing)`}`
			end;
		};
		CutsceneSeen = {
			Meta = { Side = T; Section = `Story`; Title = `Cutscene seen`; Help = `Mark a cutscene Seen, or Clear it`; Icon = `SecStory`;
				Level = 2; Target = `required`; Danger = false; Synonyms = { `seen`, `unsee` };
				Args = { A(`Id`, `choice`, { Label = `Cutscene`; From = `Cutscenes`; Required = true }), A(`Mark`, `choice`, { Choices = { `Seen`, `Clear` }; Required = true }) } };
			Run = function(Admin, Tg, a)
				local Q = H.svc(`Quests.Quests`)
				local S = Q and Q.CineState(Tg)
				if not S then return false, `Their quest data isn't loaded` end
				S[a.Id] = if a.Mark == `Seen` then `Seen` else nil
				Q.SyncForCine(Tg)
				return true, `{cutName(a.Id)}: {if a.Mark == `Seen` then `seen` else `cleared`} for {Tg.Name}`
			end;
		};
		TutorialEnter = {
			Meta = { Side = T; Section = `Story`; Title = `Tutorial: enter`; Help = `Put them in Wickfield, at their checkpoint`; Icon = `SecStory`;
				Level = 2; Target = `required`; Danger = false; Synonyms = { `tutorial`, `wickfield` }; Args = {} };
			Run = function(Admin, Tg)
				local Tu = tut() if not Tu then return false, `Tutorial is missing` end
				Tu.Enter(Tg)
				return true, `{Tg.Name} is in the tutorial ({Tu.CheckpointOf(Tg) or `no checkpoint`})`
			end;
		};
		TutorialJump = {
			Meta = { Side = T; Section = `Story`; Title = `Tutorial: jump to`; Help = `The garden, the fence or the bus`; Icon = `SecStory`;
				Level = 2; Target = `required`; Danger = false; Synonyms = { `checkpoint` };
				Args = { A(`Checkpoint`, `choice`, { Choices = { `Garden`, `Fence`, `Bus` }; Required = true }) } };
			Run = function(Admin, Tg, a)
				local Tu = tut() if not Tu then return false, `Tutorial is missing` end
				local Cut, Seg = CHECKPOINTS[a.Checkpoint]:match(`^([%w_]+):([%w_]+)$`)
				Tu.Checkpoint(Tg, Cut, Seg)
				if Tg:GetAttribute(`NHTutorial`) == true then Tu.Resume(Tg) else Tu.Enter(Tg) end
				return true, `{Tg.Name}: tutorial at the {string.lower(a.Checkpoint)}`
			end;
		};
		TutorialLeave = {
			Meta = { Side = T; Section = `Story`; Title = `Tutorial: leave`; Help = `Take them out of Wickfield`; Icon = `SecStory`;
				Level = 2; Target = `required`; Danger = false; Synonyms = { `leave tutorial` }; Args = {} };
			Run = function(Admin, Tg)
				local Tu = tut() if not Tu then return false, `Tutorial is missing` end
				if Tg:GetAttribute(`NHTutorial`) ~= true then return false, `{Tg.Name} is not in the tutorial` end
				Tu.Leave(Tg)
				return true, `{Tg.Name} left the tutorial`
			end;
		};
		GiveClue = {
			Meta = { Side = T; Section = `Story`; Title = `Give a clue`; Help = `One clue from a case`; Icon = `Clues`;
				Level = 2; Target = `required`; Danger = false; Synonyms = { `clue`, `evidence` };
				Args = { A(`Clue`, `choice`, { From = `Clues`; Required = true }) } };
			Run = function(Admin, Tg, a)
				local Inv = H.svc(`Quests.Investigation`)
				if not Inv then return false, `Investigation is missing` end
				local Case, Clue = tostring(a.Clue):match(`^([%w_]+)/([%w_]+)$`)
				if not Case then return false, `No such clue in that case` end
				if Inv.HasClue(Tg, Case, Clue) then return false, `{Tg.Name} has that clue already` end
				if not Inv.Grant(Tg, Case, Clue) then return false, `No such clue in that case` end
				return true, `Gave {Tg.Name} a clue: {Clue}`
			end;
		};
		ResetCase = {
			Meta = { Side = T; Section = `Story`; Title = `Reset a case`; Help = `Clear its clues, links and deduction`; Icon = `Clues`;
				Level = 2; Target = `required`; Danger = true; Synonyms = { `case reset` };
				Args = { A(`Case`, `choice`, { From = `Cases`; Required = true }) } };
			Run = function(Admin, Tg, a)
				local Inv = H.svc(`Quests.Investigation`)
				if not (Inv and Inv.ResetCase) then return false, `Investigation is missing` end
				if not Inv.ResetCase(Tg, a.Case) then return false, `Their case data isn't loaded` end
				return true, `Reset {a.Case} for {Tg.Name}`
			end;
		};
	}
end
```
Check `Cine.Play`'s `Skippable` option (Task 0 copy of `World.Cine`: `Opts.Skippable == true` lets anyone
skip it). Staff testing a cut want to skip, so it is set. Check that `PlayCutscene`'s `Replay` toggle with `Default =
true` is drawn on by default by `Cards.luau`. If the console ignores `Default`, `Run` still treats a missing value as
on (`a.Replay ~= false`).

- [ ] **Step 3: Install (ask the owner first) and check**

```bash
python -X utf8 -I tools/admin-console/install_inplace.py tools/admin-console/pre2 tools/admin-console/live AdminConsole2_20261124 ServerScriptService.Services.Quests.Investigation
python -X utf8 -I tools/admin-console/install_new.py tools/admin-console/live/ServerScriptService.Services.Features.Admin.Story.luau
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_registry.lua
```
Expected: the only registry failures left are `FormDirection` (missing card, and the count `84, want 85`). Copy both
files into `pre2/`.

- [ ] **Step 4: Commit**

```bash
git add tools/admin-console
git commit -m "Console 2: Story cards (cutscenes, tutorial, clues, reset a case)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Form direction, the lists, the player list, the context card

**Files:**
- Modify: `tools/admin-console/live/ServerScriptService.Services.Features.Admin.luau`
- Modify: `tools/admin-console/live/ServerScriptService.Services.Features.Admin.Meta.luau`
- Modify: `tools/admin-console/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.View.luau`
- Test: `tools/admin-console/checks/console_registry.lua` (passes now)

**Interfaces:**
- Consumes: Tasks 1-6.
- Produces:
  - `Admin.Lists()` gains `Cutscenes = { {Id, Name} }` (Config.Cine Cuts without `Hidden`), `Cases = { {Id, Name} }`,
    `Clues = { {Id = "<Case>/<Clue>", Name = "<Case name>: <Clue name>"} }`, `Misdeeds = { {Id, Name} }`.
  - The player list rows gain `Transformed`, `Bells`, `BellState`, `Summons`, `InCutscene`, `New`.
  - `Admin.Inspect` gains `Heat`, `Bells`, `BellState`, `Summons`, `FormDirection`, `Checkpoint`.
  - Card `FormDirection`.

- [ ] **Step 1: The lists**

In `buildLists()`, add `Cutscenes = {}; Cases = {}; Clues = {}; Misdeeds = {}` to `L`, and before `return L`:
```lua
	pcall(function() -- (console 2) Play a cutscene / Cutscene seen
		for id, c in require(ReplicatedStorage.Config.Cine).Cuts do
			if not c.Hidden then table.insert(L.Cutscenes, { Id = id; Name = c.Name or id }) end
		end
		table.sort(L.Cutscenes, function(x, y) return x.Name < y.Name end)
	end)
	pcall(function() -- (console 2) Give a clue / Reset a case
		for caseId, c in require(ReplicatedStorage.Config.Cases) do
			table.insert(L.Cases, { Id = caseId; Name = c.Name or caseId })
			for clueId, k in c.Clues or {} do
				table.insert(L.Clues, { Id = `{caseId}/{clueId}`; Name = `{c.Name or caseId}: {k.Name or clueId}`; Order = (c.Number or 0) * 100 + (k.Order or 0) })
			end
		end
		table.sort(L.Cases, function(x, y) return x.Name < y.Name end)
		table.sort(L.Clues, function(x, y) return x.Order < y.Order end)
	end)
	pcall(function() -- (console 2) Give a summons: the misdeeds Notoriety knows (Task 5's MISDEEDS table)
		local Cfg = require(ReplicatedStorage.Config.Notoriety)
		for id in Cfg.Gain do table.insert(L.Misdeeds, { Id = id; Name = id }) end -- (Task 0 Step 4) same name as Admin.BellTower's MISDEEDS
		table.sort(L.Misdeeds, function(x, y) return x.Name < y.Name end)
	end)
```

- [ ] **Step 2: The player list and the inspector**

In `playerList()`, before the loop add:
```lua
	local Q = svc(`Quests.Quests`)
	local Cn = svc(`World.Cine`)
```
and add to each row (after `InMenu = ...`):
```lua
			-- (console 2) the four new flags and the Bell Tower lines
			Transformed = C0 ~= nil and C0:GetAttribute(`Transformation`) ~= nil;
			Bells = P:GetAttribute(`NHBells`); BellState = P:GetAttribute(`NHBellState`); Summons = P:GetAttribute(`NHSummons`);
			InCutscene = P:GetAttribute(`NHTutorial`) == true or (Cn ~= nil and Cn.IsWatching(P));
			New = (function() local Ok, S = pcall(Q.CineState, P) return Ok and typeof(S) == `table` and S.Prologue ~= `Seen` end)();
```
In `Shared.Inspect`, before `return {`:
```lua
	local Nt = svc(`School.Notoriety`)
	local nt = Nt and Nt.Get(T) or {}
	local Tu = svc(`World.Tutorial`)
	local Lin = typeof(Prof.Lineage) == `table` and Prof.Lineage or {}
```
and add to the returned table:
```lua
		Heat = nt.Heat; Bells = nt.Tier; BellState = nt.State; Summons = nt.Summons;
		FormDirection = typeof(Lin.Looks) == `table` and Lin.Looks.FormDirection or nil;
		Checkpoint = Tu and Tu.CheckpointOf(T) or nil;
```

- [ ] **Step 3: Form direction**

In `Admin.Meta.luau`, in `-- Test / Character` after `Transform`:
```lua
	FormDirection = { Side = T; Section = "Character"; Title = "Form direction"; Help = "Which of their race's two forms they turn into"; Icon = "Transform"; Level = 2; Target = "required"; Danger = false; Synonyms = { "form look" };
		Args = { A("Direction", "choice", { Choices = { "1", "2" }; Labels = { "Direction 1", "Direction 2" }; Required = true }) } };
```
In `Admin.luau`, after `C.Transform = ...`, add the card. `applyForm` is what Task 0 Step 4 found: how the game
tells the client and the character that the Look changed. Write that call in place of the marked line.
```lua
-- (console 2) the form's direction: Lineage.Looks.FormDirection ("1" / "2"), as the player's own Look slot sets it
C.FormDirection = { Target = true; Run = function(A, T, a)
	local Prof = profile(T)
	if not Prof then return false, `Their profile isn't loaded` end
	local Race = T:GetAttribute(`Race`)
	local Forms = require(ReplicatedStorage.Config.Forms)
	local R = Race and Forms.Races and Forms.Races[Race]
	if not (R and R.Directions) then return false, `{T.Name} has no form (no race form at Tier I)` end
	local Dir
	for _, D in R.Directions do if D.Id == a.Direction then Dir = D end end
	if not Dir then return false, `Their race has no direction {a.Direction}` end
	Prof.Lineage = typeof(Prof.Lineage) == `table` and Prof.Lineage or {}
	Prof.Lineage.Looks = typeof(Prof.Lineage.Looks) == `table` and Prof.Lineage.Looks or {}
	Prof.Lineage.Looks.FormDirection = Dir.Id
	local RC = svc(`Player.RaceCosmetics`)
	if RC and RC.Queue then RC.Queue(T) end
	-- (Task 0 Step 4) applyForm: the same refresh the player's own Look change does (an attribute or a remote)
	return true, `Set {T.Name}'s form to {Dir.Name} (direction {Dir.Id})`
end }
```

- [ ] **Step 4: The context card's new lines**

In `View.luau`, find the Test side's context card (where it draws `Inspect` values: grep `Inspect.` near the `line(`
calls around line 300-340). After the existing discipline line, add:
```lua
		if I.Heat ~= nil then
			line(`Heat {math.floor(I.Heat)} · Bell {I.Bells or 0}{if I.BellState and I.BellState ~= "" then " · " .. I.BellState else ""}{if (I.Summons or 0) > 0 then ` · {I.Summons} summons` else ""}`, 20, COL.Body)
		end
		if I.FormDirection then line(`Form direction {I.FormDirection}`, 20, COL.Body) end
		if I.Checkpoint then line(`Tutorial: {I.Checkpoint}`, 20, COL.Body) end
```
Use the local names the View already uses (`I` for the inspect table, `line`, `COL.Body`). Read the surrounding 20
lines first and match them; if the colour is named differently (for example `COL.Text`), use that.

- [ ] **Step 5: Install (ask the owner first) and run**

```bash
python -X utf8 -I tools/admin-console/install_inplace.py tools/admin-console/pre2 tools/admin-console/live AdminConsole2_20261124 ServerScriptService.Services.Features.Admin ServerScriptService.Services.Features.Admin.Meta StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.View
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_registry.lua
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_pure.lua
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_model.lua
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_play_server.lua
```
Expected: `PASS console_registry (85 commands)`, and the other three PASS. Copy the three files into `pre2/`.

- [ ] **Step 6: Commit**

```bash
git add tools/admin-console
git commit -m "Console 2: Form direction, the new pick lists, row flags and context lines

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Play checks, screenshots and the report

**Files:**
- Create: `tools/admin-console/checks/console2_play_run.lua`
- Create: `tools/admin-console/checks/console2_play_client.lua`
- Modify: `tools/admin-console/REPORT.md` (controller)

**Interfaces:**
- Consumes: everything above, through `Admin.Dispatch(P, Cmd, TargetUserId, Args)` and the console client's probe.

- [ ] **Step 1: Write the server Play check**

`checks/console2_play_run.lua`, run with `run_live.py` inside the game's VM. It takes slot 2's state first and always
puts it back (an `xpcall` around the run, as `console_play_run.lua` does).
```lua
-- Server, Play, slot 2: every phase 2 card through Admin.Dispatch, then everything put back.
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local SSS = game.ServerScriptService.Services
local Admin = require(SSS.Features.Admin)
local Data = require(SSS.Player.Data)
local Nt = require(SSS.School.Notoriety)
local HM = require(SSS.School.HallMonitor)
local Q = require(SSS.Quests.Quests)
local Tu = require(SSS.World.Tutorial)
local Cine = require(SSS.World.Cine)
local P = Players:GetPlayers()[1]
if not P then return "FAIL no player" end
local Prof = Data.GetProfile(P)
if not Prof then return "FAIL no profile loaded (run this with run_live.py)" end
local Fails, Ran = {}, 0
local function go(Cmd, Args, Target)
	task.wait(0.2)
	if script:GetAttribute("Stop") then error("stopped by run_live.py (timeout)", 0) end
	return Admin.Dispatch(P, Cmd, Target, Args or {})
end
local function want(Ok, Cmd, Args, Target, Expect)
	local A, B = go(Cmd, Args, Target)
	Ran += 1
	if (A == true) ~= Ok then table.insert(Fails, `{Cmd}: got {tostring(A)} {tostring(B)}`) return B end
	if Expect and not string.find(tostring(B), Expect, 1, true) then table.insert(Fails, `{Cmd}: "{tostring(B)}", want "{Expect}"`) end
	return B
end
local function deep(T) if typeof(T) ~= "table" then return T end local O = {} for K, V in T do O[K] = deep(V) end return O end
local function json(V)
	if typeof(V) ~= "table" then return typeof(V) .. ":" .. tostring(V) end
	local Ks = {} for K in V do table.insert(Ks, K) end
	table.sort(Ks, function(a, b) return tostring(a) < tostring(b) end)
	local Out = {} for _, K in Ks do table.insert(Out, tostring(K) .. "=" .. json(V[K])) end
	return "{" .. table.concat(Out, ",") .. "}"
end
local KEYS = { "Quests", "Discipline", "Lineage", "Progress" }
local Saved = {} for _, K in KEYS do Saved[K] = deep(Prof[K]) end
local WA = { "NHSeason", "NHSky", "NHMoonOverride", "NHMoonOverrideNight", "NHMonitorsOff" }
local W0 = {} for _, K in WA do W0[K] = workspace:GetAttribute(K) end
local Clock = require(SSS.School.SchoolClock)
local St0 = Clock.GetState()
local Me = P.UserId

local function putBack()
	Admin.TestLiveMode = false
	P:SetAttribute("NHTestLevel", nil)
	pcall(Nt.Clear, P)
	if not HM.IsEnabled() then HM.SetEnabled(true) end
	if P:GetAttribute("NHTutorial") == true then pcall(Tu.Leave, P) end
	pcall(Cine.EndFor, P, "Aborted")
	for _, K in KEYS do
		local Cur, Old = Prof[K], Saved[K]
		if typeof(Cur) == "table" and typeof(Old) == "table" then
			for Key in Cur do Cur[Key] = nil end
			for Key, V in Old do Cur[Key] = deep(V) end
		else
			Prof[K] = deep(Old)
		end
	end
	pcall(Q.SyncForCine, P)
	for _, K in WA do workspace:SetAttribute(K, W0[K]) end
	pcall(Clock.SetTime, string.format("%02d:%02d", St0.Hour, St0.Minute or 0), St0.Day)
end

local Ok, Err = xpcall(function()
	-- World
	want(true, "TimePreset", { Preset = "Dusk" }, nil, "18:30")
	want(true, "SetSeason", { Season = "Winter" }, nil, "to Winter")
	if workspace:GetAttribute("NHSeason") ~= "Winter" then table.insert(Fails, "NHSeason not Winter") end
	want(true, "SetSeason", { Season = "Autumn" }, nil, "to Autumn")
	if workspace:GetAttribute("NHSeason") ~= nil then table.insert(Fails, "Autumn should clear NHSeason") end
	want(true, "SetMoon", { Moon = "Crimson" }, nil, "to Crimson")
	if workspace:GetAttribute("NHMoonEventTonight") ~= "Crimson" then table.insert(Fails, "MoonPhases didn't pick up Crimson") end
	want(true, "SetMoon", { Moon = "Auto" }, nil, "to Auto")
	want(true, "SetSky", { Sky = "Storm" }, nil, "to Storm")
	want(true, "SetSky", { Sky = "Auto" }, nil, "to Auto")
	-- the live rule: level 2 refused, level 3 allowed
	Admin.TestLiveMode = true
	P:SetAttribute("NHTestLevel", 2) task.wait(0.3)
	for _, C in { { "SetSeason", { Season = "Winter" } }, { "SetMoon", { Moon = "New" } }, { "SetSky", { Sky = "Storm" } } } do
		want(false, C[1], C[2], nil, "Owner only in live servers")
	end
	want(true, "TimePreset", { Preset = "Noon" }) -- not server-wide in the owner's sense: level 2 is fine
	P:SetAttribute("NHTestLevel", 3) task.wait(0.3)
	want(true, "SetSky", { Sky = "Storm" }) want(true, "SetSky", { Sky = "Auto" })
	P:SetAttribute("NHTestLevel", nil) Admin.TestLiveMode = false task.wait(0.3)

	-- Bell Tower (on yourself: no targeting up in Studio)
	want(true, "SetHeat", { Heat = 30 }, Me, "Bell 2")
	if P:GetAttribute("NHBells") ~= 2 then table.insert(Fails, "NHBells not 2 after Heat 30") end
	want(true, "SetBells", { Bells = 4 }, Me, "to 4")
	if P:GetAttribute("NHBells") ~= 4 then table.insert(Fails, "NHBells not 4") end
	want(true, "WhosWanted", {}, nil, P.Name)
	want(true, "GiveSummons", { Type = (Admin.Lists().Misdeeds[1] or {}).Id }, Me, "Summons for")
	if (P:GetAttribute("NHSummons") or 0) < 1 then table.insert(Fails, "no summons owed") end
	want(true, "ClearNotoriety", {}, Me, "Cleared")
	if P:GetAttribute("NHBells") ~= nil or P:GetAttribute("NHSummons") ~= nil then table.insert(Fails, "Clear left bells or summons") end
	want(true, "SetBells", { Bells = 0 }, Me, "to 0")
	want(true, "HallMonitors", { On = false }, nil, "off")
	if workspace:GetAttribute("NHMonitorsOff") ~= true or #HM.GetMonitors() ~= 0 then table.insert(Fails, "monitors still about") end
	want(false, "HallMonitors", { On = false }, nil, "already off")
	want(true, "HallMonitors", { On = true }, nil, "on")
	task.wait(3)
	if #HM.GetMonitors() == 0 then table.insert(Fails, "no monitors after On") end
	want(false, "SetHeat", { Heat = 101 }, Me, "0 to 100")

	-- Story
	local Cuts = Admin.Lists().Cutscenes
	local Cut = Cuts[1] and Cuts[1].Id
	if not Cut then table.insert(Fails, "no cutscenes listed") else
		local Before = json(Q.CineState(P))
		want(true, "PlayCutscene", { Id = Cut; Replay = true }, nil, "(replay)")
		task.wait(1) Cine.EndFor(P, "Aborted") task.wait(1)
		if json(Q.CineState(P)) ~= Before then table.insert(Fails, "a replay changed the cine state") end
		want(true, "CutsceneSeen", { Id = Cut; Mark = "Seen" }, Me, "seen")
		if Q.CineState(P)[Cut] ~= "Seen" then table.insert(Fails, "Seen not written") end
		want(true, "CutsceneSeen", { Id = Cut; Mark = "Clear" }, Me, "cleared")
		if Q.CineState(P)[Cut] ~= nil then table.insert(Fails, "Clear left a mark") end
		want(false, "PlayCutscene", { Id = "NoSuchCut" }, nil, "Unknown")
	end
	want(true, "TutorialEnter", {}, Me, "in the tutorial")
	for _, Cp in { "Garden", "Fence", "Bus" } do want(true, "TutorialJump", { Checkpoint = Cp }, Me, string.lower(Cp)) end
	want(true, "TutorialLeave", {}, Me, "left")
	want(false, "TutorialLeave", {}, Me, "not in the tutorial")
	local Clue = Admin.Lists().Clues[1]
	if not Clue then table.insert(Fails, "no clues listed") else
		local Case = Clue.Id:match("^([%w_]+)/")
		want(true, "ResetCase", { Case = Case }, Me, "Reset")
		want(true, "GiveClue", { Clue = Clue.Id }, Me, "Gave")
		want(false, "GiveClue", { Clue = Clue.Id }, Me, "already")
		want(true, "ResetCase", { Case = Case }, Me, "Reset")
	end
	want(false, "GiveClue", { Clue = "Nope/Nope" }, Me, "Unknown")

	-- Form direction (on a race with a form; a race without one is refused)
	local HasForm = require(RS.Config.Forms).Races[P:GetAttribute("Race") or ""] ~= nil
	if HasForm then
		want(true, "FormDirection", { Direction = "2" }, Me, "direction 2")
		want(true, "FormDirection", { Direction = "1" }, Me, "direction 1")
	else
		want(false, "FormDirection", { Direction = "1" }, Me, "has no form")
	end
end, debug.traceback)
putBack()
-- slot 2 must be exactly as it was
for _, K in KEYS do if json(Prof[K]) ~= json(Saved[K]) then table.insert(Fails, "slot 2 " .. K .. " not put back") end end
for _, K in WA do if workspace:GetAttribute(K) ~= W0[K] then table.insert(Fails, "workspace " .. K .. " not put back") end end
if not Ok then return "FAIL error: " .. tostring(Err) end
if #Fails > 0 then return "FAIL " .. #Fails .. " of " .. Ran .. "\n" .. table.concat(Fails, "\n") end
return "PASS console2_play_run (" .. Ran .. " calls)"
```
`PlayCutscene` refuses an unknown id in `CheckArgs` with `Unknown Cutscene: NoSuchCut`, which the `"Unknown"` match
covers. The same goes for `GiveClue`. If the Play player's race has a form, the Form direction block runs both
directions. Note in `REPORT.md` which race slot 2 had.

- [ ] **Step 2: Write the client Play check**

`checks/console2_play_client.lua`, run with `run_live.py <file> 120 Client`. Look at `console_play_client.lua` for how
it reaches the running console (the `NHQuietProbe` / controller probe) and reuse that exactly. The check:
```lua
-- Client, Play: Preview just for me, the four flags, and the context card's lines.
local Players = game:GetService("Players")
local Me = Players.LocalPlayer
local G = Me.PlayerScripts:FindFirstChild("Controllers"):FindFirstChild("Gui")
local Tools = require(G.StaffConsole.Tools)
local Model = require(G.StaffConsole.Model)
local Fails = {}
local function Eq(Got, Want, What) if Got ~= Want then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end
local Keys = { "NHSeasonPreview", "NHMoonPhasePreview", "NHMoonPreview", "NHSkyPreview" }
local Old = {} for _, K in Keys do Old[K] = Me:GetAttribute(K) end
local ok, err = pcall(function()
	local Ok1, Msg = Tools.Do("ToolPreview", { Season = "Winter"; Moon = "Crimson"; Sky = "Storm" })
	Eq(Ok1, true, "preview ok") Eq(Me:GetAttribute("NHSeasonPreview"), "Winter", "season preview set")
	Eq(workspace:GetAttribute("NHSeason"), nil, "the server season is untouched")
	local DC = require(Me.PlayerScripts.Controllers.World.DayCycle)
	Eq(DC.Season(), "Winter", "DayCycle sees the preview") Eq(DC.Moon(), "Crimson", "DayCycle moon preview")
	task.wait(2)
	Tools.Do("ToolPreview", { Season = "Off"; Moon = "Off"; Sky = "Off" })
	for _, K in Keys do Eq(Me:GetAttribute(K), nil, K .. " cleared") end
	-- flags as the rail draws them
	Eq(table.concat(Model.Flags({ Transformed = true; Bells = 4; New = true; InCutscene = true }), ","), "TRANSFORMED,WANTED,NEW,IN CUTSCENE", "flags")
end)
for _, K in Keys do Me:SetAttribute(K, Old[K]) end
if not ok then return "FAIL error: " .. tostring(err) end
if #Fails > 0 then return "FAIL " .. #Fails .. "\n" .. table.concat(Fails, "\n") end
return "PASS console2_play_client"
```
If `Controllers.World.DayCycle`'s `require` from a LocalScript gives a fresh copy (not the running one), `Season()`
and `Moon()` still read the attributes live, so the check holds.

- [ ] **Step 3: Run the Play round (ask the owner first)**

1. Ask the owner whether Studio is free. Wait for a yes.
2. Take a fresh snapshot of slot 2, as in 1b (`tools/admin-console` snapshot step). Record CineState, Seen and Origin.
3. Start Play (`start_stop_play`), wait for the profile to load.
4. Run:
```bash
python -X utf8 -I tools/admin-console/run_live.py tools/admin-console/checks/console2_play_run.lua 300
python -X utf8 -I tools/admin-console/run_live.py tools/admin-console/checks/console2_play_client.lua 120 Client
python -X utf8 -I tools/admin-console/run_live.py tools/admin-console/checks/console_play_run.lua 300
python -X utf8 -I tools/admin-console/run_live.py tools/admin-console/checks/console_play_client.lua 120 Client
```
Expected: `PASS console2_play_run (N calls)`, `PASS console2_play_client`, and the two 1a/1b checks still PASS.
5. Screenshots with `shot.py`: the World, Story and School sections on the Test side, and a row showing a flag
   (Set Bells 3 on yourself first, then Clear notoriety after the shot). Save to
   `docs/superpowers/mockups/2026-11-23-admin-console/play2-{test-world,test-story,test-school,row-flags}.png`.
6. Stop Play. Record CineState, Seen and Origin again; they must match step 2.

If a check fails, fix it in the task that owns the code (the Interfaces blocks name each owner), install again (ask
the owner) and re-run this step.

- [ ] **Step 4: The report and the docs (controller)**

Add a "Phase 2" section to `tools/admin-console/REPORT.md`: the checks and their results, the call count, slot 2
before and after, screenshots, the race slot 2 had, the backups (`NH_Backup.AdminConsole2_20261124`), and anything
Task 0 Step 4 changed in the plan. Add the new cards to `docs/Admin-Panel.md`'s command list, and the new public calls
to `docs/Attendance-and-Discipline.md` (Notoriety API line, Hall monitor section) and `docs/Sky-and-Lighting.md` (the
moon override).

- [ ] **Step 5: Commit**

```bash
git add tools/admin-console docs
git commit -m "Console 2: Play checks, screenshots and the report

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

The place is not saved. Tell the owner it needs their word to save.
