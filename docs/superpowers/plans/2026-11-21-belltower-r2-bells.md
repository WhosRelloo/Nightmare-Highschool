# The Bell Tower R2 · Bells Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Being noticed. Misdeeds that staff witness build **Heat**, and Heat rings up to five **Bells**:
- **Murmur:** something was seen.
- **Noticed:** a description is going round.
- **Named:** a monitor hunts you.
- **Hunted:** every monitor converges, and the PA calls a disturbance.
- **The Tolling:** an emergency PA.

The Bells have a **state**:
- **Hollow:** something was seen, but nobody knows it was you.
- **Tarnished:** they know who you are.
- **Lit:** a monitor can see you right now.
- **Search:** they've lost sight of you and are sweeping the area.

Heat cools off. Being in your timetable's class cools it fastest. Being caught books the violation plus a tier bonus. If you escape but they know your face, a **summons** arrives instead. The HUD shows a swinging bell rail under the dial, and the quest card folds away while you're noticed.

**Architecture:**
- **`ServerScriptService.Services.School.Notoriety`** owns the per-player Heat, tier, state, search and summons. It doesn't edit Discipline's ladder.
- **What feeds it:**
  - `Discipline.ReportIncident`, which is the funnel every staff witness already uses. Discipline calls `Notoriety.OnReport` and receives the catch bonus back.
  - `HallMonitor`, which calls `Notoriety.Witnessed` when a chase starts or a monitor is hit.
  - A watcher for being seen transformed.
- **What it drives:** HallMonitor, through `Respond`, `Converge` and a new "Wanted" chase reason, and `World.Broadcast` for the PA.
- **Pure maths:** `ReplicatedStorage.Functions.Notoriety`, tested in the Edit VM.
- **Tunables:** `ReplicatedStorage.Config.Notoriety`.
- **The client:** reads four Player attributes: `NHBells`, `NHBellState`, `NHSearchWhere` and `NHSummons`.

**Tech Stack:**
- **Game:** Roblox Luau in NH Combat Test (placeId 98950102230473). Scripts are installed from a repo mirror through `E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py`.
- **Tests:** Luau check scripts in the Edit, Server and Client VMs.
- **Art:** Python, with numpy, scipy and Pillow.

**Spec:** `docs/superpowers/specs/2026-11-20-notoriety-timetable-discipline-ui-design.md` §3 (the system), §4 item 2 (the Bell Rail), §7 R2 (acceptance). R1 is merged (2.36.0–2.36.1), and its plan `docs/superpowers/plans/2026-11-20-belltower-r1-cluster.md` holds the HUD contracts R2 must keep.

## Global Constraints

- **Place:**
  - Build only in **NH Combat Test**. The Map place is read-only.
  - Read `docs/Pipeline-Lessons.md` (on the main checkout) before any Studio step.
- **Studio is shared:**
  - One session drives NH Combat Test at a time. Before any install or Play, the controller gets "Studio released (phase6)" from the phase6 session (or confirms with the owner that it's free).
  - When done, it sends "Studio released" back, from Edit mode with slot 2 restored.
  - Never save, close, reload or revert the place.
  - **Never edit `ServerStorage.NHTestBridge`**, and never run an ad-hoc script that invokes it. If the permission system denies anything, stop and report the exact text. Don't work around it.
- **Branch:** `belltower-r2` in the worktree `E:\NH-belltower` (cut from main `8785966`). Never switch branches in `E:\Nightmare-Highschool`. Commits use `git -c user.name=Rello` and end with the Co-Authored-By line.
- **Backups:** before the first edit, copy each changed script to `ServerStorage.NH_Backup.BellTower_R2_pre_20261121`, named `<Service>_<path_with_underscores>`.
- **Mirror:**
  - `tools/belltower-r2/pre/` holds scripts before this plan; `live/` holds them after. One `.luau` per script, named by its dotted path.
  - Studio is changed only by `harness/install.py` from `live/`, in Edit mode.
  - Dump fresh first (Task 1). The live scripts are the source of truth, and R1's polish changed ClockHud and QuestTracker.
- **The Play run order** (from R1; every Play run):
  1. Confirm Edit mode, then install.
  2. Start Play. Use the Studio MCP `start_stop_play`; if it times out, check `get_studio_state`.
  3. Run `start_play.lua` on the Server.
  4. On the first run only, run `snapshot.lua` on the Server and save its JSON to `harness/_slot2.json`.
  5. Run the checks.
  6. Run `restore.py` while still in Play. It must print `restored`.
  7. Stop Play.
- **Test slot:** slot 2 only. Never commit `_slot2.json` or the underscore temp files.
- **Text:** no game text under **20 design px** (`BellTower.MIN_TEXT`).
- **UI:** Bell Tower art and kit components only. A missing art id falls back to the kit. Keep R1's contracts:
  - `ClockHud`'s only direct Frame child is `Panel`.
  - A visible label contains "In class".
  - `ShowPA` still exists.
  - `QuestTracker.Tracker` stays, with AnchorPoint.X above 0.5 on desktop.
- **Accessibility:** `NHReducedMotion` (a Player attribute) means no swing and no toll shake. Every state change also changes words.
- **The spec's numbers, verbatim (§3):**

  | Item | Value |
  |---|---|
  | Heat per misdeed | Truancy 12, Trespassing 20, Fighting 25, Pranks/Vandalism 15, being seen transformed 30, hitting staff 45 |
  | Night gain (22:00–06:00) | ×1.5 |
  | Probation gain | ×1.25 |
  | Tier thresholds | Bell 1 at 10+, 2 at 25+, 3 at 45+, 4 at 70+, 5 at 90+ |
  | Cooling | none while Lit; Search (under 30 s unseen) −1.5/s; after that −3/s |
  | Cooling multipliers | lockers, the Dorms and off campus ×2; alibi (in your class room in class, or serving detention) ×3 |
  | Search radius | 30 to 120 studs, growing with time unseen |
  | Face known | seen within 25 studs, or Lit for 2 s; lasts 1 in-game day |
  | Catch bonus | Bell 3 +1, Bell 4 +2, Bell 5 +3 |
  | Summons | at most 3; ignored after 1 in-game day = Skipped Detention (+4) |

## Rulings and spec deltas (record each in the CHANGELOG)

1. **Witnesses:**
   - In R2, live sight (Lit and Search) comes from the **hall monitors**: the day monitor and night duty.
   - Every staff report (teachers, monitors, custodian) adds Heat through the `Discipline.ReportIncident` funnel.
   - Student witnesses, snitches and heading them off are **R3**.
2. **Identification:**
   - R2 tracks only "face known". You're identified when seen within 25 studs, when Lit for 2 s, or by any recognised report.
   - The witness-note tokens are R3.
   - Until R3: **Hollow** = not identified, **Tarnished** = identified.
3. **Summons:**
   - Served by walking into **Room 106** outside class, because there's no Headmaster's-office area in NH Combat Test yet (spec §3.8 says the office).
   - Issued when the search ends (Heat reaches 0), not at the next period change.
4. **A new violation, `Exposure`** (3 points, "Seen transformed by staff"), so that being seen transformed has something to book. Hitting staff books `Fighting`.
5. **Scope:** watched wings and the map layer are R4, and the notes row is R3. The Lead Card folding (spec §4 item 4) is in R2. `Functions.Notoriety.SearchRadius` is built and tested now; R4's map draws the candle ring from it. Monitors respond to the last-seen point in R2.
6. **The Tolling:** an emergency PA, plus every monitor converging. The Headmaster has no body.
7. **Bell 4's disturbance PA:** goes through `Broadcast.PA` without the emergency flag, so its at-most-once-per-segment limit applies.
8. **Test seam:** a Studio-only `ServerStorage.NHNotorietyProbe` (BindableFunction), created by the Notoriety service itself (`RunService:IsStudio()`).
9. **Version:** 2.37.0.

---

## File structure

| File | Responsibility | New / changed |
|---|---|---|
| `art/ui/hud/make_belltower.py` | `export_r2()`: the bell set for upload | changed |
| `art/group-upload-belltower/Bt{BellHollow,BellTarnished,BellLit,BellGlow,BellRail}.png` | the R2 pieces for the group | new |
| `tools/belltower-r2/harness/*` | a copy of R1's harness; `probe.py` | new |
| `…/live/ReplicatedStorage.Config.Notoriety.luau` | every R2 number | new |
| `…/live/ReplicatedStorage.Functions.Notoriety.luau` | pure Heat maths | new |
| `…/live/ServerScriptService.Services.School.Notoriety.luau` | the service and the probe | new |
| `…/live/ServerScriptService.Services.School.Discipline.luau` | catch bonus in `AddViolation`; `ReportIncident` calls Notoriety | changed |
| `…/live/ReplicatedStorage.Config.Discipline.luau` | `Exposure` violation | changed |
| `…/live/ReplicatedStorage.PlayerData.luau` | `Discipline.Summons`, `Discipline.FaceKnownUntilDay` | changed |
| `…/live/ServerScriptService.Services.School.HallMonitor.luau` | `SeenBy`, `OnCampus`, `Converge`, "Wanted", the `Witnessed` calls, `Caught = true` | changed |
| `…/live/ReplicatedStorage.Functions.BellTower.luau` | `BellStatus`; summons in `Conduct` | changed |
| `…/live/ReplicatedStorage.Config.BellTowerArt.luau` | 5 bell ids | changed |
| `…/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.ClockHud.luau` | the Bell Rail and status line | changed |
| `…/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.QuestTracker.luau` | folds while Bells are up | changed |
| `tools/belltower-r2/checks/{nt_pure,bt_pure_r2,nt_server,bt_bells}.lua` | the checks | new |
| `docs/UI-Kit.md`, `docs/Attendance-and-Discipline.md`, `CHANGELOG.md`, the spec | documentation | changed |

(`…` = `tools/belltower-r2`.)

---

### Task 1: Harness, pre-dump, backups and the loader check

**Files:** Create `tools/belltower-r2/harness/*`, `tools/belltower-r2/pre/*`, `tools/belltower-r2/live/*`.

**Interfaces:** Produces `install.py`, `dump.py`, `edit.py`, `client.py`, `probe.py`, `snapshot.lua`, `restore.py` and `start_play.lua` under `tools/belltower-r2/harness/`.

- [ ] **Step 1: Copy R1's harness.** Copy these from `tools/belltower-r1/harness/` into `tools/belltower-r2/harness/`: `install.py dump.py edit.py client.py bridge.py snapshot.lua restore.py start_play.lua`. In `dump.py`, change `"belltower-r1"` to `"belltower-r2"`. In `install.py`'s docstring, change the path to `tools/belltower-r2/live`. Keep `start_play.lua` at `SetTime "12:30"` (After School: monitors are on duty and no class is running).
- [ ] **Step 2: Create `probe.py`.** It's `bridge.py` aimed at the Notoriety probe:

```python
"""usage: python -X utf8 -I probe.py <Command> [lua literal args...]   e.g. probe.py Get   probe.py Witness '"Truancy"'
Invokes ServerStorage.NHNotorietyProbe (Studio only, made by Services.School.Notoriety) for the first player."""
import os, subprocess, sys
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
PLACE = "placeId: 98950102230473"
TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_probe.lua")
cmd, args = sys.argv[1], sys.argv[2:]
lua_args = ", ".join(args)
open(TMP, "w", encoding="utf-8").write(f'''local H = game:GetService("HttpService")
local P = game.Players:GetPlayers()[1]
local B = game.ServerStorage:FindFirstChild("NHNotorietyProbe")
if not B then return "NO PROBE" end
local r = B:Invoke("{cmd}", P and P.Name{", " + lua_args if lua_args else ""})
local okj, j = pcall(H.JSONEncode, H, r)
return okj and j or tostring(r)''')
r = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", PLACE, "Server", "@" + TMP], capture_output=True, text=True, encoding="utf-8")
print(r.stdout.replace("\r", ""))
```

- [ ] **Step 3: Dump** (in Edit mode, with Studio handed over):

```bash
cd /e/NH-belltower
python -X utf8 -I tools/belltower-r2/harness/dump.py ServerScriptService.Services.School.Discipline ServerScriptService.Services.School.HallMonitor ReplicatedStorage.Config.Discipline ReplicatedStorage.PlayerData ReplicatedStorage.Functions.BellTower ReplicatedStorage.Config.BellTowerArt StarterPlayer.StarterPlayerScripts.Controllers.Gui.ClockHud StarterPlayer.StarterPlayerScripts.Controllers.Gui.QuestTracker
```

Expected: eight lines with byte counts.

- [ ] **Step 4: Back up.** Write `tools/belltower-r2/harness/_backup.lua`. Use R1's `_backup.lua` with the folder `BellTower_R2_pre_20261121` and the eight paths above. Run it with `edit.py`, and check that the folder holds eight clones.
- [ ] **Step 5: Confirm the services loader.**
  - With Studio's `script_grep` for `OnStart()` (or `graphify query "service loader OnStart ServerScriptService"`), find the script that requires every ModuleScript under `ServerScriptService.Services` and calls `OnStart`. World.Broadcast (2.30) was added that way.
  - Write its path into the task report.
  - If new modules are NOT started automatically, stop and report BLOCKED: Task 4 depends on it.
- [ ] **Step 6: Find the Room 106 zone.**
  - Confirm in Edit, read-only, that `workspace.School.R106.Zone` is a BasePart. Detention's `Local.IsInRoom` uses that path.
  - Confirm that `Theme.Images.Bell` exists and is a string (the kit's skull-bell).
  - Report both.
- [ ] **Step 7: Commit** `tools/belltower-r2` (no underscore files except `_backup.lua`): "Bell Tower R2: harness, probe, pre-dump".

---

### Task 2: The bell art for upload

**Files:** Modify `art/ui/hud/make_belltower.py`. Create `art/group-upload-belltower/Bt{BellHollow,BellTarnished,BellLit,BellGlow,BellRail}.png`.

**Interfaces:** Produces 5 PNGs. The owner uploads them to group 15981569. The controller finds the ids itself, in the group's creations (`docs/Pipeline-Lessons.md` "Assets in the group"), and puts them in Task 7.

- [ ] **Step 1: Add the export.** Above `if __name__ == "__main__":`, add the function below, and call it after `export_r1()` in `__main__`.

```python
R2_PIECES = ["BellHollow", "BellTarnished", "BellLit", "BellGlow", "BellRail"]


def export_r2():
    dest = HERE.parents[1] / "group-upload-belltower"
    dest.mkdir(parents=True, exist_ok=True)
    for n in R2_PIECES:
        Image.open(OUT / f"{n}.png").save(dest / f"Bt{n}.png", optimize=True)
    print("exported", len(R2_PIECES), "to", dest)
```

- [ ] **Step 2: Bake.** Run `cd art/ui/hud && python make_belltower.py`. Expected: `exported 9 …`, then `exported 5 …`, then `ok …`. View `out/belltower/_sheet.png` and check that the three bells and the rail are intact.
- [ ] **Step 3: Commit** the script and the 5 PNGs: "Bell Tower R2 art: the bell set for upload". The controller then asks the owner to upload the five `Bt*.png` files. Tasks 3 to 6 don't wait for them.

---

### Task 3: `Config.Notoriety` and `Functions.Notoriety` (pure, TDD)

**Files:**
- Create: `…/live/ReplicatedStorage.Config.Notoriety.luau`
- Create: `…/live/ReplicatedStorage.Functions.Notoriety.luau`
- Test: `tools/belltower-r2/checks/nt_pure.lua`

**Interfaces:** Produces these members of `Functions.Notoriety` (all pure; it reads `ReplicatedStorage.Config.Notoriety` by path):

| Member | Returns |
|---|---|
| `Gain(Type: string, Ctx: {Night: boolean?, Probation: boolean?}): number` | the Heat a misdeed adds |
| `Tier(Heat: number): number` | 0–5 |
| `Bonus(Tier: number): number` | the catch bonus |
| `CoolMult(Mods: {Alibi: boolean?, Hidden: boolean?, Dorms: boolean?, OffCampus: boolean?}): number` | the cooling multiplier |
| `Cool(Heat: number, Dt: number, Since: number, Mult: number): number` | the new Heat |
| `State(Seen: boolean, Since: number, Identified: boolean): string` | `"Lit"`, `"Search"`, `"Tarnished"` or `"Hollow"` |
| `SearchRadius(Since: number): number` | studs |
| `BookType(Misdeed: string): string` | the violation type to book |
| `TierName(Tier: number): string` | the tier's name |

- [ ] **Step 1: Write the failing test** `tools/belltower-r2/checks/nt_pure.lua`:

```lua
local RS = game.ReplicatedStorage
local Mod = RS:FindFirstChild("Functions") and RS.Functions:FindFirstChild("Notoriety")
if not Mod or not (RS:FindFirstChild("Config") and RS.Config:FindFirstChild("Notoriety")) then return "FAIL Notoriety modules missing" end
local F = require(Mod:Clone())
local Fails = {}
local function Eq(Got, Want, What) if Got ~= Want then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end
local function Near(Got, Want, What) if math.abs(Got - Want) > 1e-6 then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end

-- gain (spec §3.2)
Eq(F.Gain("Truancy", {}), 12, "Gain Truancy") Eq(F.Gain("Trespassing", {}), 20, "Gain Trespassing")
Eq(F.Gain("Curfew", {}), 20, "Gain Curfew") Eq(F.Gain("Fighting", {}), 25, "Gain Fighting")
Eq(F.Gain("Vandalism", {}), 15, "Gain Vandalism") Eq(F.Gain("Exposure", {}), 30, "Gain Exposure")
Eq(F.Gain("AssaultStaff", {}), 45, "Gain AssaultStaff") Eq(F.Gain("Absent", {}), 0, "Gain unknown")
Near(F.Gain("Fighting", { Night = true }), 37.5, "Gain night") Near(F.Gain("Fighting", { Probation = true }), 31.25, "Gain probation")
Near(F.Gain("Truancy", { Night = true, Probation = true }), 22.5, "Gain night+probation")
-- tiers 10/25/45/70/90
Eq(F.Tier(0), 0, "Tier 0") Eq(F.Tier(9.99), 0, "Tier 9.99") Eq(F.Tier(10), 1, "Tier 10") Eq(F.Tier(25), 2, "Tier 25")
Eq(F.Tier(44.9), 2, "Tier 44.9") Eq(F.Tier(45), 3, "Tier 45") Eq(F.Tier(70), 4, "Tier 70") Eq(F.Tier(90), 5, "Tier 90") Eq(F.Tier(100), 5, "Tier 100")
-- bonus 0,0,1,2,3
Eq(F.Bonus(0), 0, "Bonus 0") Eq(F.Bonus(2), 0, "Bonus 2") Eq(F.Bonus(3), 1, "Bonus 3") Eq(F.Bonus(4), 2, "Bonus 4") Eq(F.Bonus(5), 3, "Bonus 5")
-- cooling
Eq(F.CoolMult({}), 1, "CoolMult none") Eq(F.CoolMult({ Hidden = true }), 2, "CoolMult hidden") Eq(F.CoolMult({ Dorms = true }), 2, "CoolMult dorms")
Eq(F.CoolMult({ OffCampus = true }), 2, "CoolMult off campus") Eq(F.CoolMult({ Alibi = true, Hidden = true }), 3, "CoolMult alibi wins")
Near(F.Cool(25, 1, 5, 1), 23.5, "Cool search") Near(F.Cool(25, 1, 31, 1), 22, "Cool quiet") Near(F.Cool(25, 1, 5, 3), 20.5, "Cool alibi")
Eq(F.Cool(1, 1, 31, 1), 0, "Cool floor")
-- state
Eq(F.State(true, 0, false), "Lit", "State lit") Eq(F.State(false, 10, false), "Search", "State search")
Eq(F.State(false, 30, false), "Hollow", "State hollow") Eq(F.State(false, 31, true), "Tarnished", "State tarnished")
-- search radius 30..120 over 30 s
Near(F.SearchRadius(0), 30, "Radius 0") Near(F.SearchRadius(15), 75, "Radius 15") Near(F.SearchRadius(60), 120, "Radius cap")
-- booking
Eq(F.BookType("Curfew"), "Trespassing", "Book curfew") Eq(F.BookType("AssaultStaff"), "Fighting", "Book assault") Eq(F.BookType("Truancy"), "Truancy", "Book truancy")
Eq(F.TierName(3), "Named", "TierName 3") Eq(F.TierName(5), "The Tolling", "TierName 5") Eq(F.TierName(0), "", "TierName 0")
return #Fails == 0 and "PASS nt_pure" or ("FAIL\n" .. table.concat(Fails, "\n"))
```

- [ ] **Step 2: Run it and see it fail.** `python -X utf8 -I tools/belltower-r2/harness/edit.py tools/belltower-r2/checks/nt_pure.lua`. Expected: `FAIL Notoriety modules missing`.
- [ ] **Step 3: Write `ReplicatedStorage.Config.Notoriety.luau`:**

```lua
--[[ (2.37) Notoriety: the Bells (spec docs/superpowers/specs/2026-11-20-notoriety-timetable-discipline-ui-design.md §3).
	Read by Functions.Notoriety (pure maths) and Services.School.Notoriety. Templates with {Where} are plain strings. ]]
return {
	-- Heat a witnessed misdeed adds (§3.2)
	Heat = { Truancy = 12; Trespassing = 20; Curfew = 20; Vandalism = 15; Fighting = 25; Contraband = 10; Exposure = 30; AssaultStaff = 45 };
	-- the Discipline violation booked for a misdeed when it isn't its own name
	BookAs = { Curfew = "Trespassing"; AssaultStaff = "Fighting" };
	NightGain = 1.5;        -- 22:00 to 06:00
	ProbationGain = 1.25;   -- Probation or Suspension
	Tiers = { 10, 25, 45, 70, 90 };
	TierNames = { "Murmur", "Noticed", "Named", "Hunted", "The Tolling" };
	TierBonus = { 0, 0, 1, 2, 3 };
	-- cooling (§3.4), per second
	SearchSeconds = 30;
	CoolSearch = 1.5;
	CoolQuiet = 3;
	HideMult = 2;           -- lockers, the Dorms, off campus
	AlibiMult = 3;          -- in your class room during class, or serving detention
	SearchRadius = { Min = 30; Max = 120 };
	-- identification (§3.5, R2: the face only)
	FaceSeenRange = 25;
	FaceLitSeconds = 2;
	-- escalation (§3.3)
	HuntTier = 3;
	ConvergeTier = 4;
	TollTier = 5;
	DisturbancePA = "A disturbance in {Where}. Staff, please attend.";
	TollPA = "All staff: a student is loose in {Where}. Find them.";
	-- summons (§3.8)
	SummonsLimit = 3;
	SummonsDays = 1;
	Tick = 0.25;
}
```

- [ ] **Step 4: Write `ReplicatedStorage.Functions.Notoriety.luau`:**

```lua
--!strict
--[[ (2.37) Notoriety's maths (Config.Notoriety). Pure: no services, no instances. Used by Services.School.Notoriety. ]]
local Config = require(game:GetService("ReplicatedStorage"):WaitForChild("Config"):WaitForChild("Notoriety")) :: any

local Notoriety = {}

function Notoriety.Gain(Type: string, Ctx: { [string]: any }): number
	local Base = Config.Heat[Type] or 0
	local Mult = 1
	if Ctx.Night then Mult *= Config.NightGain end
	if Ctx.Probation then Mult *= Config.ProbationGain end
	return Base * Mult
end

function Notoriety.Tier(Heat: number): number
	for I = #Config.Tiers, 1, -1 do
		if Heat >= Config.Tiers[I] then return I end
	end
	return 0
end

function Notoriety.Bonus(Tier: number): number
	return Config.TierBonus[Tier] or 0
end

function Notoriety.CoolMult(Mods: { [string]: any }): number
	if Mods.Alibi then return Config.AlibiMult end
	if Mods.Hidden or Mods.Dorms or Mods.OffCampus then return Config.HideMult end
	return 1
end

function Notoriety.Cool(Heat: number, Dt: number, Since: number, Mult: number): number
	local Rate = (if Since < Config.SearchSeconds then Config.CoolSearch else Config.CoolQuiet) * Mult
	return math.max(0, Heat - Rate * Dt)
end

function Notoriety.State(Seen: boolean, Since: number, Identified: boolean): string
	if Seen then return "Lit" end
	if Since < Config.SearchSeconds then return "Search" end
	return if Identified then "Tarnished" else "Hollow"
end

function Notoriety.SearchRadius(Since: number): number
	local T = math.clamp(Since / Config.SearchSeconds, 0, 1)
	return Config.SearchRadius.Min + (Config.SearchRadius.Max - Config.SearchRadius.Min) * T
end

function Notoriety.BookType(Misdeed: string): string
	return Config.BookAs[Misdeed] or Misdeed
end

function Notoriety.TierName(Tier: number): string
	return Config.TierNames[Tier] or ""
end

return Notoriety
```

- [ ] **Step 5: Install and run.**

```bash
python -X utf8 -I tools/belltower-r2/harness/install.py tools/belltower-r2/live/ReplicatedStorage.Config.Notoriety.luau tools/belltower-r2/live/ReplicatedStorage.Functions.Notoriety.luau
python -X utf8 -I tools/belltower-r2/harness/edit.py tools/belltower-r2/checks/nt_pure.lua
```

Expected: `PASS nt_pure`.

- [ ] **Step 6: Commit** "Bell Tower R2: Config.Notoriety and Functions.Notoriety (pure, tested)".

---

### Task 4: The Notoriety service, Discipline hooks and data

**Files:**
- Create: `…/live/ServerScriptService.Services.School.Notoriety.luau`
- Modify: `…/live/ServerScriptService.Services.School.Discipline.luau` (`Shared.AddViolation`, `Shared.ReportIncident`)
- Modify: `…/live/ReplicatedStorage.Config.Discipline.luau` (`Violations`)
- Modify: `…/live/ReplicatedStorage.PlayerData.luau` (the `Discipline` table)
- Test: `tools/belltower-r2/checks/nt_server.lua`

**Interfaces:**
- Consumes `Functions.Notoriety` and `Config.Notoriety` (Task 3). It reaches `HallMonitor.SeenBy`, `OnCampus`, `Respond` and `Converge` lazily, through `pcall`. Until Task 5 adds them, those calls are no-ops.
- Produces `Notoriety.OnReport(Incident): number` (the bonus):
  - `Incident.Caught == true` returns `Bonus(tier)` and clears the Heat.
  - `Recognized` marks you identified and adds Heat.
  - Otherwise it only remembers the misdeed for a summons.
- Produces `Notoriety.Witnessed(P: Player, Misdeed: string, Pos: Vector3?, Witness: string?)`, `Notoriety.IsHunted(P): boolean`, `Notoriety.BookType(P): string?` and `Notoriety.Get(P): table`.
- Produces the Player attributes `NHBells` (1–5 or nil), `NHBellState` (`Lit`/`Search`/`Tarnished`/`Hollow` or nil), `NHSearchWhere` (string or nil) and `NHSummons` (count or nil).
- Produces the probe `ServerStorage.NHNotorietyProbe:Invoke(Cmd, PlayerName, ...)`. Commands: `Manual(Seen?, Mods?)`, `Live`, `Reset`, `Witness(Misdeed)`, `Report(Type, Recognized, Caught)`, `Advance(Seconds)`, `Serve`, `AgeSummons(Days)`, `Get` and `Monitors`.
- `Discipline.AddViolation(P, Type, { Witness?, Bonus? })` adds `Bonus` points.

- [ ] **Step 1: Write the failing server check** `tools/belltower-r2/checks/nt_server.lua`. It runs on the Server VM through rbxc, and only drives the probe.

```lua
local B = game.ServerStorage:FindFirstChild("NHNotorietyProbe")
if not B then return "FAIL no NHNotorietyProbe" end
local P = game.Players:GetPlayers()[1]
if not P then return "FAIL no player" end
local N = P.Name
local F = require(game.ReplicatedStorage.Functions.Notoriety) -- pure: a VM copy is fine
local Fails, Notes = {}, {}
local function Ok(C, What) if not C then table.insert(Fails, What) end end
local function Call(...) local R = B:Invoke(...) if type(R) == "table" and R.Error then table.insert(Fails, "probe error: " .. tostring(R.Error)) end return R end

-- 1. a witnessed truancy: Heat = Gain, Lit, not booked
Call("Reset", N) Call("Manual", N, false, {})
local G = Call("Witness", N, "Truancy")
local Want = F.Gain("Truancy", { Night = G.Night, Probation = G.Probation })
Ok(math.abs(G.Heat - Want) < 0.01, "1 heat " .. G.Heat .. " want " .. Want)
Ok(G.Tier == F.Tier(Want), "1 tier " .. G.Tier) Ok(G.Misdeed == "Truancy" and G.Booked == false, "1 misdeed/booked")
Ok(P:GetAttribute("NHBells") == G.Tier, "1 NHBells attribute")
-- 2. unseen for 12 s: it cools to 0, and nobody knew the face, so no summons
G = Call("Advance", N, 12)
Ok(G.Heat == 0 and G.Tier == 0, "2 cooled " .. G.Heat) Ok(G.Summons == 0, "2 no summons") Ok(P:GetAttribute("NHBells") == nil, "2 attribute cleared")
-- 3. a recognised fight: booked (+4) at once, identified, Heat 25+
Call("Reset", N) Call("Manual", N, false, {})
local P0 = Call("Get", N).Points
G = Call("Report", N, "Fighting", true, false)
Ok(G.Points - P0 == 4, "3 points +" .. (G.Points - P0)) Ok(G.Identified == true, "3 identified") Ok(G.Tier >= 2, "3 tier " .. G.Tier)
G = Call("Advance", N, 0.25) Ok(G.State == "Search", "3 search state " .. tostring(G.State))
Ok(P:GetAttribute("NHBellState") == "Search", "3 NHBellState attribute")
G = Call("Advance", N, 40) Ok(G.Heat == 0 and G.Summons == 0, "3 booked fight: no summons")
-- 4. caught at Bell 3: +1 bonus on top of Truancy's 2
Call("Reset", N) Call("Manual", N, false, {})
Call("Witness", N, "Fighting") G = Call("Witness", N, "Fighting")
Ok(G.Tier >= 3, "4 tier " .. G.Tier)
P0 = G.Points
G = Call("Report", N, "Truancy", true, true)
Ok(G.Points - P0 == 2 + F.Bonus(3) or G.Points - P0 == 2 + F.Bonus(4), "4 caught points +" .. (G.Points - P0))
Ok(G.Heat == 0 and G.Tier == 0, "4 cleared on catch")
-- 5. an identified escape becomes a summons; serving books it without the bonus
Call("Reset", N) Call("Manual", N, true, {})
Call("Witness", N, "Vandalism") G = Call("Advance", N, 2.25)
Ok(G.Identified == true, "5 identified after 2 s lit")
Call("Manual", N, false, {}) G = Call("Advance", N, 60)
Ok(G.Summons == 1, "5 summons " .. G.Summons) Ok(P:GetAttribute("NHSummons") == 1, "5 NHSummons attribute")
P0 = G.Points G = Call("Serve", N)
Ok(G.Points - P0 == 3 and G.Summons == 0, "5 served +" .. (G.Points - P0))
-- 6. an ignored summons: Skipped Detention (+4)
Call("Reset", N) Call("Manual", N, true, {}) Call("Witness", N, "Vandalism") Call("Advance", N, 2.25)
Call("Manual", N, false, {}) G = Call("Advance", N, 60)
P0 = G.Points G = Call("AgeSummons", N, 2)
Ok(G.Summons == 0 and G.Points - P0 == 4, "6 expired +" .. (G.Points - P0))
-- 7. the alibi cools three times faster
Call("Reset", N) Call("Manual", N, false, { Alibi = true }) Call("Witness", N, "Fighting")
G = Call("Advance", N, 4)
local W = F.Gain("Fighting", { Night = G.Night, Probation = G.Probation })
Ok(math.abs(G.Heat - math.max(0, W - 1.5 * 3 * 4)) < 0.6, "7 alibi heat " .. G.Heat)
-- 8. escalation at Bell 3 asks a monitor to respond (observed: depends on a monitor within 260 studs)
Call("Reset", N) Call("Manual", N, false, {}) Call("Witness", N, "Fighting") G = Call("Witness", N, "Fighting")
table.insert(Notes, "8 RespondOk=" .. tostring(G.RespondOk) .. " monitors=" .. #Call("Monitors", N))
-- leave it clean
Call("Reset", N) Call("Live", N)
return (#Fails == 0 and "PASS nt_server" or ("FAIL\n" .. table.concat(Fails, "\n"))) .. "\n" .. table.concat(Notes, "\n")
```

- [ ] **Step 2: Run it and see it fail.**
  1. Start Play and run `start_play.lua`, then `snapshot.lua`.
  2. Run `python -X utf8 -I E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py luau "placeId: 98950102230473" Server @tools/belltower-r2/checks/nt_server.lua`.
  3. Run `restore.py`, then stop Play.

  Expected: `FAIL no NHNotorietyProbe`.

- [ ] **Step 3: Add the Exposure violation.** In `ReplicatedStorage.Config.Discipline`'s `Violations` table, add this line after `Trespassing`:

```lua
		Exposure         = { Points = 3; Text = `Seen transformed by staff` }; -- (2.37) Notoriety
```

- [ ] **Step 4: The summons fields.** In `ReplicatedStorage.PlayerData`, inside the `Discipline = { … }` template, add these two lines after `Recent = {};`. ProfileService's `Reconcile` fills them into old saves.

```lua
		Summons = {};               -- (2.37) Notoriety: { { Type, Day, Witness } }, at most 3
		FaceKnownUntilDay = -1;     -- (2.37) Notoriety: staff know your face until this in-game day
```

- [ ] **Step 5: The bonus in `Discipline.AddViolation`.**
  - Right after `local Rule = Config.Violations[Type]` and its guard line, add:

```lua
	local Bonus = math.max(0, math.floor(tonumber(Details and Details.Bonus) or 0)) -- (2.37) Notoriety: caught while hunted
	local Points = Rule.Points + Bonus
```

  - In the `Record` table, change `Points = Rule.Points;` to `Points = Points;`, and add `Bonus = if Bonus > 0 then Bonus else nil;`.
  - In the rest of `AddViolation`, replace every remaining `Rule.Points` with `Points`. That covers `Discipline.Points +=`, `HeldPoints` and the notification.
  - Change the notification's `Text` to:

```lua
		Text = `+{Points} discipline points ({Discipline.Points} total)` .. (if Bonus > 0 then ` · +{Bonus} for running` else ``);
```

- [ ] **Step 6: Notoriety in `Discipline.ReportIncident`.**
  - Add this helper above `Shared.ReportIncident`:

```lua
-- (2.37) Notoriety (Services.School.Notoriety) hears every report; required lazily (it requires this module)
function Local.Notoriety(): any?
	local Ok, M = pcall(function() return require(ServerScriptService.Services.School.Notoriety) end)
	return if Ok then M else nil
end
```

  - Replace the body from `local Suspect = Incident.Suspect` to the end of the function with:

```lua
	local Bonus = 0
	local N = Local.Notoriety()
	if N and N.OnReport then
		local Ok, B = pcall(N.OnReport, Incident)
		if Ok and type(B) == `number` then Bonus = B end
	end

	local Suspect = Incident.Suspect
	if Incident.Recognized and typeof(Suspect) == `Instance` and Suspect:IsA(`Player`) then
		Shared.AddViolation(Suspect, Incident.Type, { Witness = Incident.Witness; Bonus = Bonus })
		return true
	end
	return false
end
```

  - Add `(2.37) Notoriety hears every report (OnReport); a caught report carries the Bonus` to the API block of the header comment.
- [ ] **Step 7: Write the service** `ServerScriptService.Services.School.Notoriety.luau`:

```lua
--[[
	Notoriety (server). Services.School.Notoriety  (2.37, the Bell Tower R2)
	Spec: docs/superpowers/specs/2026-11-20-notoriety-timetable-discipline-ui-design.md §3. Numbers: Config.Notoriety.

	Heat per player from misdeeds that staff witness -> five Bells (Murmur .. The Tolling) and a bell state:
	  Hollow (nobody knows the face), Tarnished (they do), Lit (a monitor sees you), Search (lost sight, < 30 s).
	Heat cools while unseen (faster hidden, fastest with an alibi). Rising tiers escalate: a monitor responds (Bell 3),
	every monitor converges and the PA calls a disturbance (Bell 4), an emergency PA (Bell 5).
	Caught = the violation + the tier bonus (Discipline.ReportIncident asks OnReport). Got away but identified =
	a summons (Discipline.Summons), served in Room 106 outside class; ignored past a day = Skipped Detention.

	Fed by: Discipline.ReportIncident -> Shared.OnReport; HallMonitor (chase start, a hit on a monitor) ->
	Shared.Witnessed; a character seen transforming -> Shared.Witnessed(Exposure).
	Player attributes: NHBells, NHBellState, NHSearchWhere, NHSummons (nil when there's nothing to show).
	Studio only: ServerStorage.NHNotorietyProbe (BindableFunction) for tools/belltower-r2/checks/nt_server.lua.
]]

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local ServerStorage = game:GetService(`ServerStorage`)
local RunService = game:GetService(`RunService`)

local Config = require(ReplicatedStorage.Config.Notoriety)
local F = require(ReplicatedStorage.Functions.Notoriety)
local RegionsConfig = require(ReplicatedStorage.Config.Regions)
local SignalPlus = require(ReplicatedStorage.Packages.SignalPlus)
local SchoolClock = require(ServerScriptService.Services.School.SchoolClock)
local Discipline = require(ServerScriptService.Services.School.Discipline)
local Notifications = require(ServerScriptService.Services.Features.Notifications)

local Local = {}
local Shared = {}
Shared.Changed = SignalPlus() -- (Player, Bells, State)

local States = {} :: { [Player]: any }
local Overrides = {} :: { [Player]: { Seen: boolean?, Mods: any? } } -- the probe's manual mode

---| Helpers |---

function Local.Lazy(Path: { string }): any?
	local Ok, M = pcall(function()
		local I: Instance = ServerScriptService
		for _, Name in Path do I = I:FindFirstChild(Name) :: Instance end
		return require(I :: ModuleScript)
	end)
	return if Ok then M else nil
end
function Local.HallMonitor(): any? return Local.Lazy({ `Services`, `School`, `HallMonitor` }) end
function Local.Broadcast(): any? return Local.Lazy({ `Services`, `World`, `Broadcast` }) end

function Local.Today(): number
	local St = SchoolClock.GetState()
	return St and St.Day or 0
end

function Local.Root(P: Player): BasePart?
	local C = P.Character
	return if C then C:FindFirstChild(`HumanoidRootPart`) :: BasePart? else nil
end

function Local.Get(P: Player)
	local S = States[P]
	if not S then
		S = {
			Heat = 0; Tier = 0; State = ``; T = 0; LastSeenAt = -math.huge; LastSeenPos = nil :: Vector3?; LitFor = 0;
			Misdeed = nil :: string?; Booked = true; Witness = nil :: string?; Identified = false;
			Responded = false; RespondOk = nil :: boolean?; Converged = false; Tolled = false;
		}
		States[P] = S
	end
	return S
end

function Local.FaceKnown(P: Player): boolean
	local D = Discipline.GetData(P)
	return D ~= nil and (D.FaceKnownUntilDay or -1) >= Local.Today()
end

function Local.Identify(P: Player)
	Local.Get(P).Identified = true
	local D = Discipline.GetData(P)
	if D then D.FaceKnownUntilDay = Local.Today() + 1 end
end

-- the region name at a point: the highest-priority box in workspace.Regions (Config.Regions)
function Local.WhereAt(Pos: Vector3?): string
	local Folder = workspace:FindFirstChild(`Regions`)
	if not (Pos and Folder) then return `` end
	local Best, BestPri = nil, -math.huge
	for _, Box in Folder:GetDescendants() do
		if not Box:IsA(`BasePart`) then continue end
		local Def = RegionsConfig.Defs[Box:GetAttribute(`RegionId`) or Box.Name]
		if not Def then continue end
		local L = Box.CFrame:PointToObjectSpace(Pos)
		local H = Box.Size / 2
		if math.abs(L.X) <= H.X and math.abs(L.Y) <= H.Y and math.abs(L.Z) <= H.Z and (Def.Priority or 0) > BestPri then
			Best, BestPri = Def, Def.Priority or 0
		end
	end
	return if Best then (Best.Title or Best.Name) else ``
end

function Local.Context(P: Player)
	local St = SchoolClock.GetState()
	local H = St and St.Hour or 12
	local L = P:GetAttribute(`DisciplineLevel`)
	return { Night = H >= 22 or H < 6; Probation = L == `Probation` or L == `Suspension` }
end

function Local.Mods(P: Player)
	local St = SchoolClock.GetState()
	local Kind = St and St.Segment and St.Segment.Kind
	local C = P.Character
	local Dorms = false
	pcall(function() Dorms = require(ServerScriptService.Services.Features.Regions).Inside(P, `Dorms`) end)
	local Off = false
	local HM = Local.HallMonitor()
	if HM and HM.OnCampus then
		local Ok, On = pcall(HM.OnCampus, P)
		Off = Ok and On == false
	end
	return {
		Alibi = (Kind == `Class` and P:GetAttribute(`ClassInRoom`) == true) or P:GetAttribute(`DetentionActive`) == true;
		Hidden = C ~= nil and C:GetAttribute(`Hidden`) == true;
		Dorms = Dorms;
		OffCampus = Off;
	}
end

function Local.InRoom106(P: Player): boolean
	local School = workspace:FindFirstChild(`School`)
	local Room = School and School:FindFirstChild(`R106`)
	local Zone = Room and Room:FindFirstChild(`Zone`) :: BasePart?
	local Root = Local.Root(P)
	if not (Zone and Root) then return false end
	local L = Zone.CFrame:PointToObjectSpace(Root.Position)
	local H = Zone.Size / 2
	return math.abs(L.X) <= H.X and math.abs(L.Y) <= H.Y and math.abs(L.Z) <= H.Z
end

---| State |---

function Local.Publish(P: Player)
	local S = Local.Get(P)
	local On = S.Tier > 0
	P:SetAttribute(`NHBells`, if On then S.Tier else nil)
	P:SetAttribute(`NHBellState`, if On and S.State ~= `` then S.State else nil)
	P:SetAttribute(`NHSearchWhere`, if On and S.State == `Search` then Local.WhereAt(S.LastSeenPos) else nil)
	local D = Discipline.GetData(P)
	local Count = if D and D.Summons then #D.Summons else 0
	P:SetAttribute(`NHSummons`, if Count > 0 then Count else nil)
end

function Local.Reset(P: Player)
	local S = Local.Get(P)
	S.Heat, S.Tier, S.State, S.LitFor = 0, 0, ``, 0
	S.Misdeed, S.Booked, S.Witness = nil, true, nil
	S.Responded, S.RespondOk, S.Converged, S.Tolled = false, nil, false, false
end

function Local.PA(Template: string, Where: string, Emergency: boolean)
	local B = Local.Broadcast()
	if not (B and B.PA) then return end
	local Text = Template:gsub(`{Where}`, if Where ~= `` then Where else `the school`)
	pcall(B.PA, Text, Emergency)
end

function Local.Escalate(P: Player)
	local S = Local.Get(P)
	local Root = Local.Root(P)
	local Pos = S.LastSeenPos or (if Root then Root.Position else nil)
	if not Pos then return end
	local HM = Local.HallMonitor()
	if S.Tier >= Config.HuntTier and not S.Responded then
		S.Responded = true
		if HM and HM.Respond then
			local Ok, R = pcall(HM.Respond, Pos)
			S.RespondOk = Ok and R == true
		end
	end
	if S.Tier >= Config.ConvergeTier and not S.Converged then
		S.Converged = true
		if HM and HM.Converge then pcall(HM.Converge, Pos) end
		Local.PA(Config.DisturbancePA, Local.WhereAt(Pos), false)
	end
	if S.Tier >= Config.TollTier and not S.Tolled then
		S.Tolled = true
		Local.PA(Config.TollPA, Local.WhereAt(Pos), true)
	end
end

function Local.AddHeat(P: Player, Amount: number)
	if Amount <= 0 then return end
	local S = Local.Get(P)
	local Old = S.Tier
	S.Heat = math.min(100, S.Heat + Amount)
	S.Tier = F.Tier(S.Heat)
	if S.Tier > Old then Local.Escalate(P) end
end

function Local.AddSummons(P: Player, Type: string, Witness: string?)
	local D = Discipline.GetData(P)
	if not D then return end
	D.Summons = D.Summons or {}
	if #D.Summons >= Config.SummonsLimit then return end
	table.insert(D.Summons, { Type = Type; Day = Local.Today(); Witness = Witness or `Staff` })
	Notifications.Notify(P, {
		Title = `Summons`;
		Text = `They know it was you. Report to Room 106 outside class by tomorrow.`;
		Kind = `Warning`;
		Duration = 6;
	})
end

-- the search is over: an identified student who got away gets a summons for what wasn't booked
function Local.Finish(P: Player)
	local S = Local.Get(P)
	if S.Misdeed and not S.Booked and (S.Identified or Local.FaceKnown(P)) then
		Local.AddSummons(P, F.BookType(S.Misdeed), S.Witness)
	end
	Local.Reset(P)
end

function Local.Step(P: Player, Dt: number)
	local S = Local.Get(P)
	if S.Heat <= 0 and S.Tier == 0 then return end
	S.T += Dt
	local O = Overrides[P]
	local Seen, Dist = false, math.huge
	if O and O.Seen ~= nil then
		Seen, Dist = O.Seen == true, 0
	else
		local HM = Local.HallMonitor()
		if HM and HM.SeenBy then
			local Ok, A, D = pcall(HM.SeenBy, P)
			if Ok then Seen, Dist = A == true, (if type(D) == `number` then D else math.huge) end
		end
	end
	if Seen then
		S.LastSeenAt = S.T
		local Root = Local.Root(P)
		if Root then S.LastSeenPos = Root.Position end
		S.LitFor += Dt
		if not S.Identified and (Dist <= Config.FaceSeenRange or S.LitFor >= Config.FaceLitSeconds) then Local.Identify(P) end
	else
		S.LitFor = 0
		local Mods = (if O and O.Mods then O.Mods else Local.Mods(P))
		S.Heat = F.Cool(S.Heat, Dt, S.T - S.LastSeenAt, F.CoolMult(Mods))
		S.Tier = F.Tier(S.Heat)
	end
	S.State = F.State(Seen, S.T - S.LastSeenAt, S.Identified)
	if S.Heat <= 0 then Local.Finish(P) end
	Local.Publish(P)
	Shared.Changed:Fire(P, S.Tier, S.State)
end

function Local.Serve(P: Player)
	local D = Discipline.GetData(P)
	if not (D and D.Summons and #D.Summons > 0) then return end
	local List = D.Summons
	D.Summons = {}
	for _, Sm in List do
		Discipline.AddViolation(P, Sm.Type, { Witness = `{Sm.Witness} (summons)` })
	end
	Notifications.Notify(P, { Title = `Summons answered`; Text = `Booked, without the hunt on top.`; Kind = `Info`; Duration = 5 })
	Local.Publish(P)
end

function Local.Summons(P: Player)
	local D = Discipline.GetData(P)
	if not (D and D.Summons and #D.Summons > 0) then return end
	local Today = Local.Today()
	for I = #D.Summons, 1, -1 do
		if Today > D.Summons[I].Day + Config.SummonsDays then
			table.remove(D.Summons, I)
			Discipline.AddViolation(P, `SkippedDetention`, { Witness = `Summons ignored` })
		end
	end
	local St = SchoolClock.GetState()
	local InClass = St and St.Segment and St.Segment.Kind == `Class`
	if not InClass and Local.InRoom106(P) then Local.Serve(P) end
	Local.Publish(P)
end

---| API |---

function Shared.Witnessed(P: Player, Misdeed: string, Pos: Vector3?, Witness: string?)
	if not (typeof(P) == `Instance` and P:IsA(`Player`)) or P:GetAttribute(`InMainMenu`) == true then return end
	local S = Local.Get(P)
	S.Misdeed, S.Booked, S.Witness = Misdeed, false, Witness
	if Pos then S.LastSeenPos = Pos end
	S.LastSeenAt = S.T
	if Local.FaceKnown(P) then S.Identified = true end
	Local.AddHeat(P, F.Gain(Misdeed, Local.Context(P)))
	if S.Tier > 0 and S.State == `` then S.State = `Lit` end
	Local.Publish(P)
	Shared.Changed:Fire(P, S.Tier, S.State)
end

-- Discipline.ReportIncident calls this for every report; the return is the bonus for a catch
function Shared.OnReport(Incident: any): number
	local P = Incident and Incident.Suspect
	if not (typeof(P) == `Instance` and P:IsA(`Player`)) then return 0 end
	local S = Local.Get(P)
	if Incident.Caught == true then
		local Bonus = F.Bonus(S.Tier)
		Local.Reset(P)
		Local.Publish(P)
		Shared.Changed:Fire(P, 0, ``)
		return Bonus
	end
	if Incident.Recognized == true then
		Local.Identify(P)
		S.Misdeed, S.Booked, S.Witness = Incident.Type, true, Incident.Witness
		if typeof(Incident.Position) == `Vector3` then S.LastSeenPos = Incident.Position end
		S.LastSeenAt = S.T
		Local.AddHeat(P, F.Gain(Incident.Type, Local.Context(P)))
		if S.Tier > 0 and S.State == `` then S.State = `Lit` end
	elseif S.Tier > 0 then
		-- got away: the heat came with the chase; remember what to book if they were identified
		S.Misdeed, S.Booked = Incident.Type, false
	end
	Local.Publish(P)
	Shared.Changed:Fire(P, S.Tier, S.State)
	return 0
end

function Shared.IsHunted(P: Player): boolean
	local S = States[P]
	return S ~= nil and S.Tier >= Config.HuntTier
end

function Shared.BookType(P: Player): string?
	local S = States[P]
	return if S and S.Misdeed then F.BookType(S.Misdeed) else nil
end

function Shared.Get(P: Player)
	local S = Local.Get(P)
	local D = Discipline.GetData(P)
	local Ctx = Local.Context(P)
	return {
		Heat = math.floor(S.Heat * 100 + 0.5) / 100; Tier = S.Tier; State = S.State; Misdeed = S.Misdeed; Booked = S.Booked;
		Identified = S.Identified; RespondOk = S.RespondOk; Summons = if D and D.Summons then #D.Summons else 0;
		Points = if D then D.Points else nil; Level = if D then D.Level else nil; Night = Ctx.Night; Probation = Ctx.Probation;
	}
end

---| The probe (Studio only) |---

function Local.Probe(Cmd: string, Name: string?, ...): any
	if Cmd == `Monitors` then
		local HM = Local.HallMonitor()
		local List = if HM and HM.GetMonitors then HM.GetMonitors() else {}
		local Out = {}
		for _, M in List do table.insert(Out, { Name = M.Name; State = M.State; Reason = M.Reason; Target = M.Target }) end
		return Out
	end
	local P = if Name then Players:FindFirstChild(Name) else nil
	if not (P and P:IsA(`Player`)) then return { Error = `no player` } end
	local A = { ... }
	if Cmd == `Manual` then Overrides[P] = { Seen = A[1]; Mods = A[2] } return true end
	if Cmd == `Live` then Overrides[P] = nil return true end
	if Cmd == `Reset` then
		Local.Reset(P)
		Local.Get(P).Identified = false
		local D = Discipline.GetData(P)
		if D then D.Summons = {} D.FaceKnownUntilDay = -1 end
		Local.Publish(P)
		return true
	end
	if Cmd == `Witness` then Shared.Witnessed(P, A[1], nil, `Probe`) return Shared.Get(P) end
	if Cmd == `Report` then
		Discipline.ReportIncident({ Type = A[1]; Suspect = P; Witness = `Probe`; Recognized = A[2] == true; Caught = A[3] == true })
		return Shared.Get(P)
	end
	if Cmd == `Advance` then
		for _ = 1, math.floor((tonumber(A[1]) or 0) / Config.Tick + 0.5) do Local.Step(P, Config.Tick) end
		return Shared.Get(P)
	end
	if Cmd == `Serve` then Local.Serve(P) return Shared.Get(P) end
	if Cmd == `AgeSummons` then
		local D = Discipline.GetData(P)
		for _, Sm in (if D and D.Summons then D.Summons else {}) do Sm.Day -= (tonumber(A[1]) or 2) end
		Local.Summons(P)
		return Shared.Get(P)
	end
	if Cmd == `Get` then return Shared.Get(P) end
	return { Error = `unknown command {Cmd}` }
end

---| Start |---

function Local.WatchCharacter(P: Player, C: Model)
	C:GetAttributeChangedSignal(`Transformation`):Connect(function()
		local Form = C:GetAttribute(`Transformation`)
		if Form == nil or Form == `` or Form == `Human` or Form == `Priest` then return end
		local HM = Local.HallMonitor()
		if not (HM and HM.SeenBy) then return end
		local Ok, Seen = pcall(HM.SeenBy, P)
		if Ok and Seen == true then
			local Root = Local.Root(P)
			Shared.Witnessed(P, `Exposure`, if Root then Root.Position else nil, `Hall Monitor`)
		end
	end)
end

function Shared.OnStart()
	local function Join(P: Player)
		if P.Character then Local.WatchCharacter(P, P.Character) end
		P.CharacterAdded:Connect(function(C) Local.WatchCharacter(P, C) end)
	end
	for _, P in Players:GetPlayers() do Join(P) end
	Players.PlayerAdded:Connect(Join)
	Players.PlayerRemoving:Connect(function(P) States[P] = nil Overrides[P] = nil end)

	if RunService:IsStudio() then
		local Probe = ServerStorage:FindFirstChild(`NHNotorietyProbe`) or Instance.new(`BindableFunction`)
		Probe.Name = `NHNotorietyProbe`
		Probe.OnInvoke = function(...)
			local Ok, R = pcall(Local.Probe, ...)
			return if Ok then R else { Error = tostring(R) }
		end
		Probe.Parent = ServerStorage
	end

	task.spawn(function()
		while true do
			task.wait(Config.Tick)
			for _, P in Players:GetPlayers() do
				if not Overrides[P] then
					local Ok, Err = pcall(Local.Step, P, Config.Tick)
					if not Ok then warn(`[Notoriety] {Err}`) end
				end
				pcall(Local.Summons, P)
			end
		end
	end)
end

return Shared
```

- [ ] **Step 8: Install** in Edit mode: Config.Discipline, PlayerData, Discipline and Notoriety. Expected: four report lines, and no `PARSE FAIL`.
- [ ] **Step 9: Run `nt_server.lua`** with the Play run order. Expected: `PASS nt_server`, plus a line `8 RespondOk=… monitors=N`. That line is an observation for Task 5. In R2 it's `nil` until HallMonitor gains `Respond` through the lazy path. `Respond` already exists, so expect `true` or `false`.
- [ ] **Step 10: Commit** the five mirrors and the check: "Bell Tower R2: the Notoriety service, Discipline hooks, summons data".

---

### Task 5: HallMonitor joins in

**Files:**
- Modify: `…/live/ServerScriptService.Services.School.HallMonitor.luau` (`StartChase`, `Catch`, the escape branch of `UpdateMonitor`, the patrol scan, `OnDamage`, and new `Shared` functions)
- Test: `tools/belltower-r2/checks/nt_server.lua` (rerun), plus `tools/belltower-r2/checks/nt_monitor.lua` (new)

**Interfaces:**
- Consumes `Notoriety.Witnessed`, `IsHunted` and `BookType` (Task 4).
- Produces `HallMonitor.SeenBy(P: Player): (boolean, number)`, `HallMonitor.OnCampus(P: Player): boolean`, `HallMonitor.Converge(Pos: Vector3): number` (how many responded), and the chase reason `"Wanted"`.

- [ ] **Step 1: Write the failing check** `tools/belltower-r2/checks/nt_monitor.lua`. It runs on the Server VM and is read-only, apart from the probe.

```lua
local B = game.ServerStorage:FindFirstChild("NHNotorietyProbe")
local P = game.Players:GetPlayers()[1]
if not (B and P) then return "FAIL no probe/player" end
local N = P.Name
local Fails = {}
local function Ok(C, What) if not C then table.insert(Fails, What) end end
-- Converge exists: at Bell 4 more than one monitor is sent (when two are on duty)
B:Invoke("Reset", N) B:Invoke("Manual", N, false, {})
B:Invoke("Witness", N, "Fighting") B:Invoke("Witness", N, "Fighting") local G = B:Invoke("Witness", N, "Fighting")
Ok(G.Tier >= 4, "tier " .. tostring(G.Tier))
task.wait(0.5)
local Responding = 0
for _, M in B:Invoke("Monitors", N) do if M.State == "Respond" or M.State == "Chase" then Responding += 1 end end
Ok(Responding >= 1, "no monitor responding at Bell 4")
-- SeenBy through live sight: with Manual(nil) the service asks HallMonitor.SeenBy (no error expected)
B:Invoke("Manual", N, nil, {}) G = B:Invoke("Advance", N, 0.25)
Ok(G.State == "Lit" or G.State == "Search", "state via SeenBy " .. tostring(G.State))
B:Invoke("Reset", N) B:Invoke("Live", N)
return #Fails == 0 and ("PASS nt_monitor (responding " .. Responding .. ")") or ("FAIL\n" .. table.concat(Fails, "\n"))
```

- [ ] **Step 2: Run it before the change** (Play run order). Expected: it FAILS, because Converge is missing and no monitor responds at Bell 4. It may pass on "responding" if `Respond` alone sent one. Record the output either way.
- [ ] **Step 3: The lazy Notoriety accessor.** Add it after `local Shared = {}`:

```lua
-- (2.37) Notoriety (Services.School.Notoriety), required lazily (it calls back into this module)
function Local.Notoriety(): any?
	local Ok, M = pcall(function() return require(ServerScriptService.Services.School.Notoriety) end)
	return if Ok then M else nil
end
```

- [ ] **Step 4: Report chases.** In `Local.StartChase`, after the `Fx.Fire(Player, \`Spotted\`, …)` line, add:

```lua
	-- (2.37) the chase is a witnessed misdeed (a "Wanted" chase is the hunt itself, not a new one)
	if Reason ~= `Wanted` then
		local No = Local.Notoriety()
		local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
		if No and No.Witnessed then pcall(No.Witnessed, Player, Reason, if Root then Root.Position else nil, `Hall Monitor`) end
	end
```

  In its `Local.Say(M, …)` chain, add this branch before the final `else`:

```lua
		elseif Reason == `Wanted` then `There you are! Don't move!`
```

- [ ] **Step 5: The catch books the hunt.**
  - In `Local.Catch`, replace the `Discipline.ReportIncident({ Type = if Reason == \`Curfew\` …` call (the first one inside `if Punish then`) with the block below.
  - In the same function, add `Caught = true;` to the Contraband `ReportIncident` table.
  - Add `elseif Reason == \`Wanted\` then \`Got you. This goes on your record.\`` to the `Local.Say` chain inside `if Punish then`.

```lua
		local Type = if Reason == `Curfew` then `Trespassing` else Reason -- (2.30) curfew is trespassing on the record
		if Reason == `Wanted` then -- (2.37) the hunt books what started it
			local No = Local.Notoriety()
			Type = if No and No.BookType then No.BookType(Player) else nil
		end
		if Type then
			Discipline.ReportIncident({
				Type = Type;
				Suspect = Player;
				Witness = `Hall Monitor`;
				Position = M.Root.Position;
				Recognized = true;
				Caught = true; -- (2.37) Notoriety adds the tier bonus and clears the heat
			})
		end
```

- [ ] **Step 6: A Wanted escape isn't a new report.** In `UpdateMonitor`'s `if Escaped then` branch, wrap the `Discipline.ReportIncident({ … Recognized = false; … })` call in `if M.Reason ~= \`Wanted\` then … end`.
- [ ] **Step 7: Patrol hunts the Wanted.** In `UpdateMonitor`, insert this block right after the `if State.Segment.Kind == \`Class\` or State.Segment.Kind == \`Night\` then … end` patrol scan, and before `if #Route == 0 then return end`:

```lua
	-- (2.37) Bell 3 and up: any monitor on duty chases a hunted student on sight, in any segment
	if Settings.DutyKinds[State.Segment.Kind] then
		local No = Local.Notoriety()
		if No and No.IsHunted then
			local Best, BestDistance = nil, math.huge
			for _, Player in Players:GetPlayers() do
				if not Player.Character or not No.IsHunted(Player) then continue end
				local Visible, Distance = Local.CanSee(M, Player.Character, true)
				if Visible and Distance < BestDistance then Best, BestDistance = Player, Distance end
			end
			if Best then
				Local.StartChase(M, Best, `Wanted`)
				return
			end
		end
	end
```

- [ ] **Step 8: Hitting a monitor is hitting staff.** At the top of `Local.OnDamage`, after `if not Player then return end`, add:

```lua
	-- (2.37) a hit on a monitor itself: hitting staff (Notoriety heat 45, booked as Fighting)
	for _, M in Monitors do
		if M.Model == Target then
			local No = Local.Notoriety()
			local R = Attacker:FindFirstChild(`HumanoidRootPart`) :: BasePart?
			if No and No.Witnessed then pcall(No.Witnessed, Player, `AssaultStaff`, if R then R.Position else nil, `Hall Monitor`) end
			break
		end
	end
```

- [ ] **Step 9: The new Shared functions.** Add them before `function Shared.GetMonitors()`:

```lua
-- (2.37) for Notoriety: is any on-duty monitor seeing this student right now? Returns (seen, nearest distance)
function Shared.SeenBy(Player: Player): (boolean, number)
	local Character = Player.Character
	if not Character then return false, math.huge end
	local State = SchoolClock.GetState()
	if not (State and State.Segment and Settings.DutyKinds[State.Segment.Kind]) then return false, math.huge end
	local Seen, Nearest = false, math.huge
	for _, M in Monitors do
		if not Local.IsActive(M) then continue end
		local Chasing = M.State == `Chase` and M.Target == Player and os.clock() - (M.LastSeen or 0) < 0.5
		local Visible, Distance = Local.CanSee(M, Character, true)
		if Chasing or Visible then
			Seen = true
			Nearest = math.min(Nearest, Distance)
		end
	end
	return Seen, Nearest
end

-- (2.37) for Notoriety: inside the school (Local.OnCampus)
function Shared.OnCampus(Player: Player): boolean
	return Local.OnCampus(Player)
end

-- (2.37) Bell 4: every patrolling monitor on duty within 400 studs heads for the spot. Returns how many went.
function Shared.Converge(Position: Vector3): number
	local State = SchoolClock.GetState()
	if not (State and State.Segment and Settings.DutyKinds[State.Segment.Kind]) then return 0 end
	local Count = 0
	for _, M in Monitors do
		if Local.IsActive(M) and M.State == `Patrol` and (M.Root.Position - Position).Magnitude <= 400 then
			M.RespondAt = Position
			M.RespondDone = nil
			M.RespondUntil = os.clock() + 30
			M.Humanoid.WalkSpeed = Settings.ChaseSpeed
			Local.SetState(M, `Respond`)
			Local.Say(M, `All hands! Over there!`)
			Count += 1
		end
	end
	return Count
end
```

- [ ] **Step 10: Install** HallMonitor in Edit mode. Then run, in one Play cycle, `nt_server.lua` (expect `PASS`, with `8 RespondOk=true` or `false`) and `nt_monitor.lua` (expect `PASS nt_monitor (responding N)` with N ≥ 1). Restore, then stop.
  - If `responding 0` comes from no monitor being on duty or within range, record the `Monitors` output. Then rerun with `start_play.lua`'s time at 12:30, which is already its value.
- [ ] **Step 11: A live hunt (visual).**
  1. In one more Play cycle, run probe `Manual nil {}`, then probe `Witness "Fighting"` twice, so that Bell 3 is live sight.
  2. Walk the character toward a monitor with `character_navigation` or `user_keyboard_input` if available. Otherwise just stand still.
  3. Take a `screen_capture`. Expect the monitor to chase ("There you are! Don't move!") and, on reaching you, book Fighting plus 1 with the toast "· +1 for running".
  4. Record what happened. If you can't drive the character, note "live hunt not driven".
  5. Restore and stop.
- [ ] **Step 12: Commit** the HallMonitor mirror and `nt_monitor.lua`: "Bell Tower R2: hall monitors hunt the Wanted, converge, and feed Notoriety".

---

### Task 6: The Bell Rail on the HUD, and the card folds

**Files:**
- Modify: `…/live/ReplicatedStorage.Functions.BellTower.luau` (`BellStatus`, `TierNames`, `BellTint`; summons in `Conduct`)
- Modify: `…/live/ReplicatedStorage.Config.BellTowerArt.luau` (5 keys, all 0 for now)
- Modify: `…/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.ClockHud.luau` (`CreateGui`; the update loop; `UpdateConduct`)
- Modify: `…/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.QuestTracker.luau` (`UpdateTracker`)
- Test: `tools/belltower-r2/checks/bt_pure_r2.lua`, `tools/belltower-r2/checks/bt_bells.lua`

**Interfaces:**
- Consumes the Player attributes `NHBells`, `NHBellState`, `NHSearchWhere` and `NHSummons` (Task 4).
- Produces `BellTower.BellStatus(Bells, State, Where)`, which returns `{ Visible, Count, State, ArtKey, Tint, Glow, Dim, Swing, Line }`.
- `BellTower.Conduct(A, IsClass)` now also reads `A.NHSummons`.
- Produces `ClockHud.Panel.Bells` (a Frame with `Rail`, `Bell1`…`Bell5` and `Status`), placed between `Head` and `Conduct`.

- [ ] **Step 1: Write the failing pure test** `tools/belltower-r2/checks/bt_pure_r2.lua`:

```lua
local Mod = game.ReplicatedStorage.Functions:FindFirstChild("BellTower")
local B = require(Mod:Clone())
local Fails = {}
local function Eq(Got, Want, What) if Got ~= Want then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end
if not B.BellStatus then return "FAIL BellStatus missing" end
local V = B.BellStatus(nil, nil, nil)
Eq(V.Visible, false, "none visible") Eq(V.Count, 0, "none count")
V = B.BellStatus(3, "Search", "The Library")
Eq(V.Visible, true, "3 visible") Eq(V.Count, 3, "3 count") Eq(V.ArtKey, "BellLit", "search art") Eq(V.Swing, true, "search swings")
Eq(V.Dim, true, "search dims") Eq(V.Glow, false, "search no glow")
Eq(V.Line, '<font color="#C8283C">Named</font> · searching · The Library', "search line")
V = B.BellStatus(2, "Search", "") Eq(V.Line, '<font color="#C8283C">Noticed</font> · searching · nearby', "search nearby")
V = B.BellStatus(4, "Lit", nil) Eq(V.ArtKey, "BellLit", "lit art") Eq(V.Glow, true, "lit glow") Eq(V.Swing, false, "lit still")
Eq(V.Line, '<font color="#C8283C">Hunted</font> · they can see you', "lit line")
V = B.BellStatus(1, "Hollow", nil) Eq(V.ArtKey, "BellHollow", "hollow art") Eq(V.Line, '<font color="#C8283C">Murmur</font> · something was seen', "hollow line")
V = B.BellStatus(5, "Tarnished", nil) Eq(V.ArtKey, "BellTarnished", "tarnished art") Eq(V.Line, '<font color="#C8283C">The Tolling</font> · they know who you are', "tarnished line")
V = B.BellStatus(9, "Weird", nil) Eq(V.Count, 5, "clamp 5") Eq(V.State, "Hollow", "unknown state is Hollow")
-- summons in the conduct row (before an owed detention, after a running one)
local C = B.Conduct({ DisciplineLevel = "Warning", DisciplinePoints = 3, DetentionsOwed = 1, NHSummons = 1 }, false)
Eq(C.Slips[1].Title, "Summons", "summons slip") Eq(C.Slips[1].Line, "Room 106, outside class", "summons line") Eq(C.Waypoint, true, "summons waypoint")
C = B.Conduct({ DisciplineLevel = "Warning", NHSummons = 2 }, true) Eq(C.Slips[1].Title, "Summons ×2", "summons x2") Eq(C.Waypoint, false, "summons in class")
C = B.Conduct({ DisciplineLevel = "Detention", DetentionActive = true, DetentionCollected = 1, DetentionTotal = 5, NHSummons = 1 }, false)
Eq(C.Slips[1].Title, "Detention", "active detention first")
return #Fails == 0 and "PASS bt_pure_r2" or ("FAIL\n" .. table.concat(Fails, "\n"))
```

- [ ] **Step 2: Run it and see it fail** (Edit VM): `FAIL BellStatus missing`. Also rerun `tools/belltower-r1/checks/bt_pure.lua`, which must still `PASS`.
- [ ] **Step 3: `Functions.BellTower`.**
  - Add the block below before `return BellTower`.
  - In `BellTower.Conduct`, replace `elseif Owed > 0 then` with the summons branch shown after it, so the order is: a detention in progress, then summons, then owed.

```lua
-- (2.37) the Bell Rail (R2): tier names, fallback tints, and what the rail shows
BellTower.TierNames = { "Murmur", "Noticed", "Named", "Hunted", "The Tolling" }
BellTower.BellTint = {
	Hollow = Color3.fromRGB(70, 64, 74);
	Tarnished = Color3.fromRGB(110, 150, 128);
	Lit = Color3.fromRGB(235, 205, 120);
	Search = Color3.fromRGB(235, 205, 120);
}

function BellTower.BellStatus(Bells: any, State: any, Where: any)
	local N = math.clamp(math.floor(tonumber(Bells) or 0), 0, 5)
	local S = if State == "Lit" or State == "Search" or State == "Tarnished" or State == "Hollow" then State else "Hollow"
	local Out = { Visible = N > 0; Count = N; State = S; ArtKey = "BellHollow"; Tint = BellTower.BellTint[S];
		Glow = false; Dim = false; Swing = false; Line = "" }
	if N == 0 then return Out end
	Out.ArtKey = if S == "Lit" or S == "Search" then "BellLit" elseif S == "Tarnished" then "BellTarnished" else "BellHollow"
	Out.Glow = S == "Lit"
	Out.Dim = S == "Search"
	Out.Swing = S == "Search"
	local Place = if typeof(Where) == "string" and Where ~= "" then Where else "nearby"
	local Detail = if S == "Lit" then "they can see you"
		elseif S == "Search" then "searching · " .. Place
		elseif S == "Tarnished" then "they know who you are"
		else "something was seen"
	Out.Line = '<font color="#C8283C">' .. BellTower.TierNames[N] .. '</font> · ' .. Detail
	return Out
end
```

```lua
	elseif (tonumber(A.NHSummons) or 0) > 0 then -- (2.37) Notoriety: report to Room 106
		local S = math.floor(tonumber(A.NHSummons) or 0)
		table.insert(Out.Slips, { Title = if S > 1 then `Summons ×{S}` else "Summons", Line = "Room 106, outside class" })
		Out.Waypoint = not IsClass
	elseif Owed > 0 then
```

- [ ] **Step 4: Config.BellTowerArt.** Add these to the `Art` table (ids come in Task 7):

```lua
	BellHollow = 0;    -- (2.37) R2
	BellTarnished = 0;
	BellLit = 0;
	BellGlow = 0;      -- greyscale halo, tinted Gold
	BellRail = 0;
```

- [ ] **Step 5: ClockHud builds the rail.**
  - In `Local.CreateGui`, add the block below after the `Head` frame is built (after `Head.Parent = Panel`).
  - Then change the conduct row's `Conduct.LayoutOrder = 2` to `Conduct.LayoutOrder = 3`.

```lua
	-- (2.37) the Bell Rail (Notoriety R2): shown while NHBells > 0, between the plate and the conduct row
	local BellsRow = Instance.new(`Frame`)
	BellsRow.Name = `Bells`
	BellsRow.LayoutOrder = 2
	BellsRow.BackgroundTransparency = 1
	BellsRow.Size = UDim2.new(1, 0, 0, 126)
	BellsRow.Visible = false
	BellsRow.Parent = Panel
	Local.Img(`BellRail`, { Name = `Rail`; AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, 6, 0, 0); Size = UDim2.fromOffset(450, 71); ZIndex = 2; Parent = BellsRow })
	local BellImgs = {}
	for I = 1, 5 do
		-- bell I hangs from rail hook 5 - I (hooks at x 150 + k * 240 of the 1400 px rail, which is 450 wide at the right edge)
		local HookX = 6 - 450 + (150 + (5 - I) * 240) * 450 / 1400
		local B = Instance.new(`ImageLabel`)
		B.Name = `Bell{I}`
		B.BackgroundTransparency = 1
		B.AnchorPoint = Vector2.new(0.5, 0)
		B.Position = UDim2.new(1, HookX, 0, 20)
		B.Size = UDim2.fromOffset(62, 62)
		B.ZIndex = 3
		B.Visible = false
		B.Parent = BellsRow
		local Glow = Local.Img(`BellGlow`, { Name = `Glow`; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.6);
			Size = UDim2.fromScale(1.9, 1.9); ImageColor3 = KitTheme.Colors.Gold; ImageTransparency = 0.35; ZIndex = 2; Visible = false; Parent = B })
		BellImgs[I] = { Img = B; Glow = Glow }
	end
	local Status = Instance.new(`TextLabel`)
	Status.Name = `Status`
	Status.BackgroundTransparency = 1
	Status.AnchorPoint = Vector2.new(1, 0)
	Status.Position = UDim2.new(1, 0, 0, 94)
	Status.Size = UDim2.new(1, 0, 0, 28)
	Status.Font = KitTheme.Fonts.Body
	Status.TextSize = BellTower.MIN_TEXT
	Status.TextColor3 = KitTheme.Colors.Text
	Status.TextXAlignment = Enum.TextXAlignment.Right
	Status.RichText = true
	Status.Text = ``
	Status.ZIndex = 3
	Status.Parent = BellsRow
	local SS = Instance.new(`UIStroke`)
	SS.Thickness = 1.2
	SS.Transparency = 0.25
	SS.Parent = Status
```

  Before `Gui.Parent = …`, add `Labels.Bells = { Row = BellsRow; Bells = BellImgs; Status = Status; Last = 0; Tweens = {} }`.

- [ ] **Step 6: ClockHud updates the rail.** Add these functions after `Local.UpdateConduct`:

```lua
-- (2.37) one toll when a bell is added (the brass hand bell, lower for each tier); a small kick unless Reduce Motion
function Local.Toll(B: ImageLabel, Count: number)
	pcall(function()
		local S = Instance.new(`Sound`)
		S.SoundId = `rbxassetid://9113584435`
		S.Volume = 0.35
		S.PlaybackSpeed = 1 - 0.08 * Count
		S.Parent = game:GetService(`SoundService`)
		S:Play()
		game:GetService(`Debris`):AddItem(S, 3)
	end)
	if Player:GetAttribute(`NHReducedMotion`) == true then return end
	B.Rotation = 7
	game:GetService(`TweenService`):Create(B, TweenInfo.new(0.6, Enum.EasingStyle.Elastic, Enum.EasingDirection.Out), { Rotation = 0 }):Play()
end

-- (2.37) the rail swings (Search) or stands still
function Local.Swing(U, On: boolean)
	On = On and Player:GetAttribute(`NHReducedMotion`) ~= true
	if On == (U.Swinging == true) then return end
	U.Swinging = On
	for _, T in U.Tweens do T:Cancel() end
	table.clear(U.Tweens)
	for I, E in U.Bells do
		E.Img.Rotation = 0
		if On then
			E.Img.Rotation = -9
			local T = game:GetService(`TweenService`):Create(E.Img, TweenInfo.new(0.6, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true, (I - 1) * 0.12), { Rotation = 9 })
			T:Play()
			table.insert(U.Tweens, T)
		end
	end
end

function Local.UpdateBells(Labels)
	local U = Labels.Bells
	local V = BellTower.BellStatus(Player:GetAttribute(`NHBells`), Player:GetAttribute(`NHBellState`), Player:GetAttribute(`NHSearchWhere`))
	U.Row.Visible = V.Visible
	if not V.Visible then
		U.Last = 0
		Local.Swing(U, false)
		return
	end
	local Img = BellTower.Image(Art, V.ArtKey)
	for I, E in U.Bells do
		E.Img.Visible = I <= V.Count
		E.Img.Image = Img or KitTheme.Images.Bell
		E.Img.ImageColor3 = if Img then Color3.new(1, 1, 1) else V.Tint
		E.Img.ImageTransparency = if V.Dim then 0.35 else 0
		if E.Glow then E.Glow.Visible = V.Glow end
	end
	U.Status.Text = V.Line
	if V.Count > U.Last and V.Count >= 1 then Local.Toll(U.Bells[V.Count].Img, V.Count) end
	U.Last = V.Count
	Local.Swing(U, V.Swing)
end
```

  - In `Local.UpdateConduct`'s attribute table, add `NHSummons = Player:GetAttribute(\`NHSummons\`);`.
  - In the update loop, right after the `local DetentionWaypoint = Local.UpdateConduct(…)` line, add `Local.UpdateBells(Labels) -- (2.37)`.

- [ ] **Step 7: The Lead Card folds.**
  - In `QuestTracker`'s `Local.UpdateTracker`, after `Ui.Card.Visible = true`, add the block below.
  - Then change the line `Ui.Timer.Visible = Ui.Timer.Text ~= \`\`` (added in R1) to `Ui.Timer.Visible = Ui.Timer.Text ~= \`\` and not Folded`.

```lua
	-- (2.37) while the Bells are up, the card folds to its title and the J key
	local Folded = (Player:GetAttribute(`NHBells`) or 0) > 0
	Ui.Objective.Visible = not Folded
	Ui.Pips.Visible = not Folded
```

- [ ] **Step 8: Write the HUD check** `tools/belltower-r2/checks/bt_bells.lua` (Client VM, in Play). It sets client-side attributes only.

```lua
local P = game.Players.LocalPlayer
local PG = P:WaitForChild("PlayerGui")
local Fails = {}
local function Check(C, What) if not C then table.insert(Fails, What) end end
local function Shown(G) local X = G while X and X:IsA("GuiObject") do if not X.Visible then return false end X = X.Parent end return true end
local Panel = PG.ClockHud.Panel
local Frames = 0 for _, K in PG.ClockHud:GetChildren() do if K:IsA("Frame") then Frames += 1 end end
Check(Frames == 1, "Panel must stay ClockHud's only Frame child")
-- Bell 3, searching
P:SetAttribute("NHBells", 3) P:SetAttribute("NHBellState", "Search") P:SetAttribute("NHSearchWhere", "The Library")
task.wait(1.2)
local Row = Panel:FindFirstChild("Bells")
Check(Row and Row.Visible, "rail hidden at Bell 3")
if Row then
	local N = 0 for I = 1, 5 do local B = Row:FindFirstChild("Bell" .. I) if B and B.Visible then N += 1 end end
	Check(N == 3, "bells shown " .. N)
	Check(Row.Status.ContentText == "Named · searching · The Library", "status " .. Row.Status.ContentText)
	Check(Row.Status.TextSize >= 20 and Row.Status.TextFits, "status size/fit")
	Check(Row.AbsolutePosition.Y >= Panel.Head.AbsolutePosition.Y + Panel.Head.AbsoluteSize.Y - 1, "rail under the plate")
end
local T = PG.QuestTracker:FindFirstChild("Tracker")
if T and T.Visible then
	local Obj = T:FindFirstChild("Objective", true)
	Check(Obj and not Shown(Obj), "card not folded")
	Check(T.AnchorPoint.X < 0.5 or T.AbsolutePosition.Y >= Panel.AbsolutePosition.Y + Panel.AbsoluteSize.Y - 1, "tracker overlaps the cluster")
end
-- the floor
for _, L in Panel:GetDescendants() do
	if L:IsA("TextLabel") and L.Text ~= "" and Shown(L) then Check(L.TextSize >= 20, L:GetFullName() .. " size " .. L.TextSize) end
end
-- cleared
P:SetAttribute("NHBells", nil) P:SetAttribute("NHBellState", nil) P:SetAttribute("NHSearchWhere", nil)
task.wait(1.2)
Check(Row and not Row.Visible, "rail still shown at Bell 0")
if T and T.Visible then local Obj = T:FindFirstChild("Objective", true) Check(Obj and Shown(Obj), "card not unfolded") end
return #Fails == 0 and "PASS bt_bells" or ("FAIL\n" .. table.concat(Fails, "\n"))
```

- [ ] **Step 9: Install** in Edit mode: `Functions.BellTower`, `Config.BellTowerArt`, `ClockHud` and `QuestTracker`. Then:
  1. Run `bt_pure_r2.lua` and R1's `bt_pure.lua` in the Edit VM. Expect `PASS` for both.
  2. In one Play cycle, run `bt_bells.lua`, then R1's five `bt_hud*.lua` checks and `bt_contracts.lua` from `tools/belltower-r1/checks/`.
  3. Expect `PASS` for all of them, then restore and stop.

  R1's checks must stay green: the bells row is hidden at Bell 0.
- [ ] **Step 10: Commit** the four mirrors and the two checks: "Bell Tower R2: the Bell Rail and status line on the HUD; the quest card folds".

---

### Task 7: Art ids, screenshots and the visual pass

**Files:** Modify `…/live/ReplicatedStorage.Config.BellTowerArt.luau` (5 ids). Create `docs/img/belltower-r2-{murmur,search,hunted,tolling,summons}.jpg`.

**Interfaces:** Consumes the owner's upload of `BtBell*.png` (Task 2).

- [ ] **Step 1: Find the ids.** The controller finds them itself, following `docs/Pipeline-Lessons.md` "Assets in the group":
  1. In the built-in browser, open a create.roblox.com page.
  2. Fetch `itemconfiguration.roblox.com/v1/creations/get-assets?assetType=Image&groupId=15981569`.
  3. Take the newest `BtBellHollow`, `BtBellTarnished`, `BtBellLit`, `BtBellGlow` and `BtBellRail`.
  4. Fill them into `Config.BellTowerArt`.

  If they aren't uploaded yet, finish on the fallbacks, and list "bell art pending" in the CHANGELOG.
- [ ] **Step 2: Install, then run `bt_bells.lua` again** with the art. Expect `PASS`.
- [ ] **Step 3: Take screenshots.** These are Studio `screen_capture` crops of the top right, using client-side attributes, plus the probe for the summons:
  - **murmur:** `NHBells 1`, `Hollow`
  - **search:** `NHBells 3`, `Search`, `NHSearchWhere "The Library"`. Take two captures 0.3 s apart, so the swing shows.
  - **hunted:** `NHBells 4`, `Lit`
  - **tolling:** `NHBells 5`, `Tarnished`
  - **summons:** a probe `Witness "Vandalism"`, then `Manual true`, `Advance 2.25`, `Manual false`, `Advance 60` (a real summons), then a capture of the conduct row's Summons slip

  Save them to `docs/img/belltower-r2-*.jpg`. Describe each in the report: bell art per state, the glow on Lit, the dimming on Search, the status text at 20 px, the folded card, and any overlap.
- [ ] **Step 4: Restore, stop, and send "Studio released"** to the phase6 session. Commit the ids and the screenshots: "Bell Tower R2: bell art ids, screenshots".

---

### Task 8: Docs and changelog

**Files:** Modify `CHANGELOG.md` (a new `[2.37.0]` entry), `docs/UI-Kit.md` (a new "The Bell Rail (2.37)" section after the Bell Tower cluster), `docs/Attendance-and-Discipline.md` (a new "Notoriety: the Bells (2.37)" section), and the spec's status line.

- [ ] **Step 1: `Attendance-and-Discipline.md`.** Add a section covering:
  - the five Bells with their thresholds and what each does
  - the four states
  - Heat per misdeed
  - cooling and the alibi
  - the catch bonus
  - summons: Room 106, 3 at most, a day to answer, Skipped Detention if ignored
  - the `Exposure` violation
  - the Player attributes
  - `ServerStorage.NHNotorietyProbe` (Studio only)
  - every ruling from this plan's "Rulings and spec deltas"
- [ ] **Step 2: `UI-Kit.md`.** Add a Bell Rail section covering:
  - the art table (5 pieces, `Config.BellTowerArt`) and the kit fallback (`Theme.Images.Bell`, tinted per state)
  - the layout: the row is 126 tall at `LayoutOrder 2`, the rail is 450 × 71, bells are 62 px and hang from hooks `5 − I`, the status line is at y 94 and 20 px
  - `BellTower.BellStatus`
  - the swing and toll, and Reduce Motion
  - the card folding
  - the contracts, which still hold
- [ ] **Step 3: `CHANGELOG.md`.** Write a `[2.37.0]` entry in the file's style:
  - what's new: the service, HallMonitor, the HUD, the data fields
  - the rulings and deltas
  - what was verified: the checks by name with their results, and the live hunt observation
  - what was not checked: two players, students as witnesses (R3), the phone layout, the Headmaster's office
  - the Studio backup folder
- [ ] **Step 4: The spec's status line.** Add "R2 built in 2.37.0 (plan `docs/superpowers/plans/2026-11-21-belltower-r2-bells.md`)", and the summons and office delta.
- [ ] **Step 5: Run `python -m graphify update .`** in `E:\NH-belltower`. `graphify-out/` is untracked; don't commit it. Then commit the docs: "Bell Tower R2: docs and changelog".
