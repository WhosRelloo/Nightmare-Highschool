# The Bell Tower R1 · The cluster Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the look of the top-right clock panel and the quest card with the Bell Tower art:
- a timetable **Dial** with a moving hand and the moon in its window
- the time lines on an iron **TowerPlate**
- a **Conduct Seal** and detention **Slip**, in place of the orange fifth line
- the parchment **Lead Card** with fang **pips** and a **J Journal** key

There are no new rules: every number and line comes from the same source as today. No text is under 20 design px.

**Architecture:**
- **Two new modules:**
  - `ReplicatedStorage.Config.BellTowerArt`: asset ids and 9-slice data. 0 means not uploaded.
  - `ReplicatedStorage.Functions.BellTower`: pure view logic (hand angle, the conduct row, pips, image lookup).
    Tests drive it.
- **Two rebuilt controllers:**
  - `Controllers.Gui.ClockHud` keeps its name, its `Panel` frame, its labels and `ShowPA`, and its update loop.
    Only `CreateGui` and the record block change.
  - `Controllers.Gui.QuestTracker` keeps `Tracker`, its update logic, the detection meter and the marker. The card
    becomes the Lead Card, and it follows the bottom of the clock panel.
- **Fallback:** every image falls back to today's kit look while its id is 0, so the code can ship before the art
  is uploaded.
- **Spec delta:** spec §4 named a new `Controllers.Gui.BellTower` controller. This plan rebuilds `ClockHud` and
  `QuestTracker` in place instead, because five other scripts depend on their instance names: Timetable, Moments,
  TouchControls, SchoolFx and GamepadControls.

**Tech Stack:**
- **Game:** Roblox Luau in NH Combat Test (placeId 98950102230473), installed from a repo mirror through
  `E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py`.
- **Art:** Python 3 (numpy, scipy, Pillow), in `art/ui/hud/make_belltower.py`.
- **Tests:** Luau check scripts, run in the Edit VM (pure module) and the Client VM (the HUD in Play).

**Spec:** `docs/superpowers/specs/2026-11-20-notoriety-timetable-discipline-ui-design.md` (approved 2026-11-20), §4
items 1, 3 and 4, §6 and §7 R1. Mockups: <https://claude.ai/artifact/NiejF4HWaeEze5GzdBNsbF>.

## Global Constraints

- **When:**
  - Start only when the owner says Studio is free. The phase6 tutorial plan uses NH Combat Test and is changing
    `Controllers.Cine`, `CineUI`, `CineActor`, `World.Cine`, `World.Tutorial`, `Progression`, `TestBridge` and
    `tools/phase6-2350`.
  - This plan touches none of those. **Never edit `ServerStorage.NHTestBridge`.**
- **Branch:**
  - Work in a git worktree, so you never switch branches in the shared checkout:
    `git worktree add ../NH-belltower -b belltower-r1 <base>`.
  - `<base>` is `main`, unless the owner names another branch.
  - Commits use `git -c user.name=Rello` and end with the Co-Authored-By line.
- **Place:** build only in **NH Combat Test**. The Map place is read-only.
- **Backups:** before the first edit, copy each changed script to `ServerStorage.NH_Backup.BellTower_pre_20261120`,
  named `<Service>_<path_with_underscores>`.
- **Mirror:**
  - `tools/belltower-r1/pre/` holds scripts before this plan; `tools/belltower-r1/live/` holds them after.
  - One `.luau` per script, named by its dotted path.
  - Studio is changed only by `harness/install.py` from `live/`, in **Edit** mode. Never edit `.Source` in place.
  - The live scripts in Studio are the source of truth: dump them first (Task 1).
- **Text:** no game text under **20 design px** (`BellTower.MIN_TEXT = 20`).
- **UI:**
  - only kit components and the Bell Tower art; no plain grey frames; `PromptUi` stays for prompts
  - don't edit `ReplicatedStorage.UI.Components` or `Theme`
- **Contracts to keep** (other scripts read these):

  | Contract | Read by |
  |---|---|
  | ScreenGui `ClockHud`, whose **only direct Frame child** is `Panel` | Timetable (`FindFirstChildWhichIsA("Frame")`, click hook, placement), Moments (`BellRim` overlay), TouchControls (Top) |
  | A visible TextLabel whose text contains `In class` | SchoolFx |
  | `ClockHud.Shared.ShowPA(Text, Chime?)` | the `NHBroadcast` hook inside ClockHud |
  | ScreenGui `QuestTracker` with a GuiObject `Tracker`, AnchorPoint.X above 0.5 on desktop | TouchControls |
  | ScreenGui names in hide lists | GamepadControls, TouchControls, `UI.Settings` (ShowClock) |
- **Test slot:** slot 2 only.
  - These checks change attributes on the **client only** and save nothing.
  - Even so, take `harness/snapshot.lua` before entering the school, and run `restore.py` after. It must print
    `restored`.
- **Version:** the next minor after the one on `main` when this lands (2.36.0 if 2.35.x is the latest).

---

## File structure

| File | Responsibility | New / changed |
|---|---|---|
| `art/ui/hud/make_belltower.py` | engraves a sun and a crescent on the Dial; `export_r1()` copies the R1 pieces to the upload folder | changed |
| `art/group-upload-belltower/Bt*.png` | the 9 R1 pieces for the owner to upload to group 15981569 | new |
| `tools/belltower-r1/harness/*` | a copy of the phase6 harness with its paths set to `belltower-r1`, plus `edit.py` | new |
| `tools/belltower-r1/live/ReplicatedStorage.Config.BellTowerArt.luau` | ids and 9-slice data | new |
| `tools/belltower-r1/live/ReplicatedStorage.Functions.BellTower.luau` | pure view logic | new |
| `tools/belltower-r1/checks/bt_pure.lua` | Edit-VM test of `Functions.BellTower` | new |
| `tools/belltower-r1/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.ClockHud.luau` | the plate, dial and conduct row | changed |
| `tools/belltower-r1/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.QuestTracker.luau` | the Lead Card, pips, J key, following the clock; marker text at 20 px | changed |
| `tools/belltower-r1/checks/bt_hud.lua` | Client-VM check of the HUD in Play | new |
| `docs/UI-Kit.md`, `docs/Attendance-and-Discipline.md`, `CHANGELOG.md`, the spec's status line | documentation | changed |

---

### Task 0: Branch, worktree and the design commit

**Files:**
- Create (by copy): `docs/superpowers/specs/2026-11-20-notoriety-timetable-discipline-ui-design.md`,
  `docs/superpowers/mockups/2026-11-20-belltower/**`, `art/ui/hud/make_belltower.py`, this plan
- These were left untracked in the main checkout (`E:\Nightmare-Highschool`) by the design session.

**Interfaces:** Produces the `belltower-r1` branch in `E:\NH-belltower`.

- [ ] **Step 1: Make the worktree.** From `E:\Nightmare-Highschool`:
  `git worktree add ../NH-belltower -b belltower-r1 main`. Use the owner's branch if they named one.
- [ ] **Step 2: Copy the design files in.** Copy the four paths above from `E:\Nightmare-Highschool` into the same
  relative paths under `E:\NH-belltower`. Don't copy `art/ui/hud/out/belltower/`: it's regenerated output.
- [ ] **Step 3: Commit.**

```bash
cd /e/NH-belltower
git add docs/superpowers/specs/2026-11-20-notoriety-timetable-discipline-ui-design.md docs/superpowers/mockups/2026-11-20-belltower docs/superpowers/plans/2026-11-20-belltower-r1-cluster.md art/ui/hud/make_belltower.py
git -c user.name=Rello commit -m "Bell Tower: notoriety/timetable/discipline HUD design, mockups, concept art script, R1 plan

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

All later paths in this plan are under `E:\NH-belltower`.

---

### Task 1: Harness and the pre-dump

**Files:**
- Create: `tools/belltower-r1/harness/{install.py,dump.py,client.py,edit.py,bridge.py,snapshot.lua,restore.py,start_play.lua}`
- Create: `tools/belltower-r1/pre/*.luau`, `tools/belltower-r1/live/*.luau` (by dump)

**Interfaces:** Produces:
- `python -X utf8 -I tools/belltower-r1/harness/install.py <live files>`
- `python -X utf8 -I tools/belltower-r1/harness/edit.py <file.lua>` (runs in the Edit VM)
- `python -X utf8 -I tools/belltower-r1/harness/client.py <file.lua>` (runs in the Client VM in Play)

- [ ] **Step 1: Copy the harness.** Copy these files from `tools/phase6-2350/harness/` into
  `tools/belltower-r1/harness/` (copies only; the phase6 folder isn't touched):
  `install.py dump.py client.py bridge.py snapshot.lua restore.py start_play.lua`.
- [ ] **Step 2: Point the copies at this plan.**
  - In `dump.py`, change `"phase6-2350"` to `"belltower-r1"`.
  - In `install.py`'s docstring, change the path to `tools/belltower-r1/live`.
  - In `start_play.lua`, change `B:Invoke("SetTime", "21:30")` to `B:Invoke("SetTime", "09:57")`, so the first
    check runs in the Break before Period 3.
- [ ] **Step 3: Create `edit.py`.** Run with `python -X utf8 -I edit.py <file.lua>`.

```python
"""usage: python -X utf8 -I edit.py <file.lua>   (runs the file in NH Combat Test's Edit VM)"""
import subprocess, sys
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
r = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", "placeId: 98950102230473", "Edit", "@" + sys.argv[1]],
                   capture_output=True, text=True, encoding="utf-8")
print(r.stdout.replace("\r", ""), r.stderr.replace("\r", ""))
```

- [ ] **Step 4: Dump the two controllers** (Studio in Edit mode):

```bash
cd /e/NH-belltower
python -X utf8 -I tools/belltower-r1/harness/dump.py StarterPlayer.StarterPlayerScripts.Controllers.Gui.ClockHud StarterPlayer.StarterPlayerScripts.Controllers.Gui.QuestTracker
```

Expected: two lines with byte counts (about 13 KB and 15 KB), plus `pre/` and `live/` copies.

- [ ] **Step 5: Back up in Studio.** Run in Edit with `edit.py`, from a file `tools/belltower-r1/harness/_backup.lua`:

```lua
local Folder = game.ServerStorage:FindFirstChild("NH_Backup") or Instance.new("Folder", game.ServerStorage)
Folder.Name = "NH_Backup"
local B = Folder:FindFirstChild("BellTower_pre_20261120") or Instance.new("Folder", Folder)
B.Name = "BellTower_pre_20261120"
local Out = {}
for _, Path in { "StarterPlayer.StarterPlayerScripts.Controllers.Gui.ClockHud", "StarterPlayer.StarterPlayerScripts.Controllers.Gui.QuestTracker" } do
	local I = game
	for Part in string.gmatch(Path, "[^%.]+") do I = I:FindFirstChild(Part) end
	local Name = Path:gsub("%.", "_")
	if not B:FindFirstChild(Name) then local C = I:Clone() C.Name = Name C.Parent = B end
	table.insert(Out, Name)
end
return table.concat(Out, ", ")
```

Expected: both names printed. Check in Studio that `ServerStorage.NH_Backup.BellTower_pre_20261120` holds both.

- [ ] **Step 6: Commit.** `git add tools/belltower-r1` and commit: "Bell Tower R1: harness and pre-dump of ClockHud and
  QuestTracker".

---

### Task 2: The R1 art (dial emblems, export, upload)

**Files:**
- Modify: `art/ui/hud/make_belltower.py`, in `dial()` and the `__main__` block
- Create: `art/group-upload-belltower/` (9 PNGs)

**Interfaces:** Produces the files `BtDial.png BtDialHand.png BtTowerPlate.png BtSeal.png BtSealBroken.png BtSlip.png
BtLeadCard.png BtPipEmpty.png BtPipFang.png`. The owner uploads them, and their ids go into `Config.BellTowerArt`
(Task 3) under the same names without `Bt`.

- [ ] **Step 1: Engrave a sun at noon and a crescent at midnight.** In `dial()`, insert this just after the line
  `tick = P.polymask((S, S), ticks)`, then add `emblem` to `is_brass`:
  `is_brass = np.clip(bezel + brs + ring + tick + bead + riv + dots * face + emblem, 0, 1)`.

```python
    # a raised sun at noon (top) and a crescent at midnight (bottom) on the face
    sx, sy = c, c - 160
    rays = []
    for k in range(12):
        a = k * math.pi / 6
        ux, uy = math.cos(a), math.sin(a)
        px, py = -uy, ux
        rays.append([(sx + ux * 17 + px * 3, sy + uy * 17 + py * 3), (sx + ux * 26, sy + uy * 26),
                     (sx + ux * 17 - px * 3, sy + uy * 17 - py * 3)])
    sun = np.clip(P.polymask((S, S), rays, [(sx - 13, sy - 13, sx + 13, sy + 13)]), 0, 1)
    mx, my = c, c + 160
    cres = np.clip(P.polymask((S, S), [], [(mx - 16, my - 16, mx + 16, my + 16)])
                   - P.polymask((S, S), [], [(mx - 9, my - 20, mx + 19, my + 10)]), 0, 1)
    emblem = np.clip(sun + cres, 0, 1) * (R < 236)
```

  The height line goes after the face is set (after
  `Hf = np.maximum(Hf, tick * (0.5 + 0.15 * P.dome(dist(tick), 3)))`):

```python
    Hf = np.maximum(Hf, emblem * (0.42 + 0.15 * P.dome(dist(emblem), 4)))
```

- [ ] **Step 2: Add `export_r1()`** above `if __name__ == "__main__":`, and call it last in `__main__`.

```python
R1_PIECES = ["Dial", "DialHand", "TowerPlate", "Seal", "SealBroken", "Slip", "LeadCard", "PipEmpty", "PipFang"]


def export_r1():
    dest = HERE.parents[1] / "group-upload-belltower"
    dest.mkdir(parents=True, exist_ok=True)
    for n in R1_PIECES:
        Image.open(OUT / f"{n}.png").save(dest / f"Bt{n}.png", optimize=True)
    print("exported", len(R1_PIECES), "to", dest)
```

- [ ] **Step 3: Bake and look.** Run `cd art/ui/hud && python make_belltower.py`. Expected: `exported 9 to
  …group-upload-belltower` and `ok …`. Open `out/belltower/_sheet.png` and check two things: the sun reads at the top
  of the dial and the crescent at the bottom, and neither one touches the moon window's bead (radius 112).
- [ ] **Step 4: Ask the owner to upload.** The owner uploads `art/group-upload-belltower/*.png` to group 15981569 (as
  with the Record and Night FM art) and pastes the ids. Don't wait for them: Tasks 3 to 5 run on the fallbacks, and
  Task 6 fills in the ids.
- [ ] **Step 5: Commit** `art/ui/hud/make_belltower.py` and `art/group-upload-belltower/`: "Bell Tower R1 art: dial
  emblems, upload set".

---

### Task 3: `Config.BellTowerArt` and `Functions.BellTower` (pure, TDD)

**Files:**
- Create: `tools/belltower-r1/live/ReplicatedStorage.Config.BellTowerArt.luau`
- Create: `tools/belltower-r1/live/ReplicatedStorage.Functions.BellTower.luau`
- Test: `tools/belltower-r1/checks/bt_pure.lua`

**Interfaces:** Produces:
- `BellTowerArt[Key]: number` (0 = missing)
- `BellTowerArt.Slices[Key] = { Center: Rect, Scale: number }`
- `BellTower.MIN_TEXT: number` (20)
- `BellTower.Tints: { [Level]: Color3 }` for `Warning`, `Detention`, `Probation`, `Suspension`
- `BellTower.Image(Art, Key: string): string?` (an `rbxassetid://` string, or nil when the id is 0 or missing)
- `BellTower.HandAngle(Hour: number): number` (degrees 0 to 360; midnight 180, noon 0)
- `BellTower.Conduct(A: {[string]: any}, IsClass: boolean)` returns
  `{ Visible: boolean, Seal: string?, Broken: boolean, Text: string, Slips: {{Title: string, Line: string}}, Waypoint: boolean }`
- `BellTower.Pips(Have: number, Need: number): {boolean}?` (nil unless Need is 2 to 6)

- [ ] **Step 1: Write the failing test** `tools/belltower-r1/checks/bt_pure.lua`:

```lua
local Mod = game.ReplicatedStorage:FindFirstChild("Functions") and game.ReplicatedStorage.Functions:FindFirstChild("BellTower")
if not Mod then return "FAIL Functions.BellTower missing" end
local B = require(Mod:Clone())
local Fails = {}
local function Eq(Got, Want, What) if Got ~= Want then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end
local function Near(Got, Want, What) if math.abs(Got - Want) > 1e-6 then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end

Eq(B.MIN_TEXT, 20, "MIN_TEXT")
-- hand: midnight at the bottom, noon at the top, 6 AM on the left, 6 PM on the right
Near(B.HandAngle(0), 180, "HandAngle(0)")
Near(B.HandAngle(12), 0, "HandAngle(12)")
Near(B.HandAngle(6), 270, "HandAngle(6)")
Near(B.HandAngle(18), 90, "HandAngle(18)")
Near(B.HandAngle(9.95), (9.95 / 24 * 360 + 180) % 360, "HandAngle(9.95)")
-- image lookup
Eq(B.Image({ Dial = 0 }, "Dial"), nil, "Image of 0")
Eq(B.Image({}, "Dial"), nil, "Image of missing")
Eq(B.Image({ Dial = 123 }, "Dial"), "rbxassetid://123", "Image of 123")
-- conduct: clear and owing nothing hides the row
local C = B.Conduct({ DisciplineLevel = "Clear", DisciplinePoints = 0, DetentionsOwed = 0 }, false)
Eq(C.Visible, false, "Clear visible")
-- warning
C = B.Conduct({ DisciplineLevel = "Warning", DisciplinePoints = 3, DetentionsOwed = 0 }, false)
Eq(C.Visible, true, "Warning visible") Eq(C.Seal, "Warning", "Warning seal") Eq(C.Text, "Warning · 3 pts", "Warning text") Eq(#C.Slips, 0, "Warning slips")
-- detention owed, outside class: a slip and a waypoint
C = B.Conduct({ DisciplineLevel = "Detention", DisciplinePoints = 6, DetentionsOwed = 1 }, false)
Eq(C.Seal, "Detention", "Detention seal") Eq(#C.Slips, 1, "owed slips") Eq(C.Slips[1].Title, "Detention owed", "owed title")
Eq(C.Slips[1].Line, "Room 106, outside class", "owed line") Eq(C.Waypoint, true, "owed waypoint outside class")
-- owed, in class: no waypoint
Eq(B.Conduct({ DisciplineLevel = "Detention", DisciplinePoints = 6, DetentionsOwed = 1 }, true).Waypoint, false, "owed waypoint in class")
-- owed twice
Eq(B.Conduct({ DisciplineLevel = "Detention", DisciplinePoints = 6, DetentionsOwed = 2 }, false).Slips[1].Title, "Detention owed ×2", "owed x2 title")
-- a detention under way
C = B.Conduct({ DisciplineLevel = "Detention", DisciplinePoints = 6, DetentionsOwed = 1, DetentionActive = true, DetentionCollected = 2, DetentionTotal = 5 }, false)
Eq(C.Slips[1].Title, "Detention", "active title") Eq(C.Slips[1].Line, "Trash 2/5", "active line") Eq(C.Waypoint, false, "active waypoint")
Eq(B.Conduct({ DisciplineLevel = "Detention", DetentionActive = true, DetentionCollected = 5, DetentionTotal = 5 }, false).Slips[1].Line, "Use the bin to finish", "active done")
-- suspended: broken seal
C = B.Conduct({ DisciplineLevel = "Probation", DisciplinePoints = 19, Suspended = true }, false)
Eq(C.Seal, "Suspension", "Suspended seal") Eq(C.Broken, true, "Suspended broken") Eq(C.Text, "Suspended", "Suspended text")
-- an unknown level shows no seal
Eq(B.Conduct({ DisciplineLevel = "Weird", DetentionsOwed = 0 }, false).Visible, false, "unknown level")
-- pips
Eq(B.Pips(0, 1), nil, "Pips need 1") Eq(B.Pips(0, 7), nil, "Pips need 7")
local Pp = B.Pips(1, 3)
Eq(#Pp, 3, "Pips len") Eq(Pp[1], true, "pip 1") Eq(Pp[2], false, "pip 2") Eq(Pp[3], false, "pip 3")
Eq(B.Pips(9, 3)[3], true, "Pips clamp high") Eq(B.Pips(-2, 2)[1], false, "Pips clamp low")
return #Fails == 0 and "PASS bt_pure" or ("FAIL\n" .. table.concat(Fails, "\n"))
```

- [ ] **Step 2: Run it and see it fail.** `python -X utf8 -I tools/belltower-r1/harness/edit.py
  tools/belltower-r1/checks/bt_pure.lua`. Expected: `FAIL Functions.BellTower missing`.
- [ ] **Step 3: Write `ReplicatedStorage.Config.BellTowerArt.luau`:**

```lua
--[[ (2.36) The Bell Tower HUD art: art/group-upload-belltower, group 15981569, baked by art/ui/hud/make_belltower.py.
	An id of 0 means "not uploaded yet". The HUD then draws that piece's kit fallback (Functions.BellTower.Image).
	Slices: 9-slice centres in source pixels and the SliceScale that draws them at the HUD's design size. ]]
local Art = {
	Dial = 0;
	DialHand = 0;
	TowerPlate = 0;
	Seal = 0;
	SealBroken = 0;
	Slip = 0;
	LeadCard = 0;
	PipEmpty = 0;
	PipFang = 0;
}
Art.Slices = {
	TowerPlate = { Center = Rect.new(60, 60, 540, 140); Scale = 0.5 };
	LeadCard = { Center = Rect.new(140, 130, 880, 250); Scale = 0.47 };
	Slip = { Center = Rect.new(90, 40, 380, 110); Scale = 0.68 };
}
return Art
```

- [ ] **Step 4: Write `ReplicatedStorage.Functions.BellTower.luau`:**

```lua
--!strict
--[[ (2.36) The Bell Tower HUD's view logic (spec: docs/superpowers/specs/2026-11-20-notoriety-timetable-discipline-ui-design.md §4).
	Pure: no services, no instances. ClockHud and QuestTracker draw what these return. ]]
local BellTower = {}

BellTower.MIN_TEXT = 20 -- the owner's floor for game text, in design px

-- Conduct seal tints (ImageColor3 over the greyscale Seal)
BellTower.Tints = {
	Warning = Color3.fromRGB(255, 168, 72);
	Detention = Color3.fromRGB(219, 31, 41);
	Probation = Color3.fromRGB(107, 15, 26);
	Suspension = Color3.fromRGB(51, 43, 48);
}

function BellTower.Image(Art: { [string]: any }, Key: string): string?
	local Id = Art[Key]
	if typeof(Id) == "number" and Id > 0 then return "rbxassetid://" .. tostring(Id) end
	return nil
end

-- The dial's hand: midnight at the bottom, noon at the top (the rim art is baked the same way).
function BellTower.HandAngle(Hour: number): number
	return ((Hour / 24) * 360 + 180) % 360
end

-- What the conduct row shows, from the Discipline attributes (Services.School.Discipline / Detention).
function BellTower.Conduct(A: { [string]: any }, IsClass: boolean)
	local Level = A.DisciplineLevel
	if A.Suspended == true then Level = "Suspension" end
	local Points = tonumber(A.DisciplinePoints) or 0
	local Owed = math.max(0, math.floor(tonumber(A.DetentionsOwed) or 0))
	local Out = { Visible = false, Seal = nil :: string?, Broken = false, Text = "", Slips = {} :: { { Title: string, Line: string } }, Waypoint = false }
	if typeof(Level) == "string" and Level ~= "Clear" and BellTower.Tints[Level] then
		Out.Seal = Level
		Out.Broken = Level == "Suspension"
		Out.Text = if Level == "Suspension" then "Suspended" else `{Level} · {Points} pts`
	end
	if A.DetentionActive == true then
		local Done = tonumber(A.DetentionCollected) or 0
		local Total = tonumber(A.DetentionTotal) or 0
		table.insert(Out.Slips, { Title = "Detention", Line = if Done >= Total then "Use the bin to finish" else `Trash {Done}/{Total}` })
	elseif Owed > 0 then
		table.insert(Out.Slips, { Title = if Owed > 1 then `Detention owed ×{Owed}` else "Detention owed", Line = "Room 106, outside class" })
		Out.Waypoint = not IsClass
	end
	Out.Visible = Out.Seal ~= nil or #Out.Slips > 0
	return Out
end

-- Fang pips for a counted objective (2 to 6); nil means "show the count as text".
function BellTower.Pips(Have: number, Need: number): { boolean }?
	local N = math.floor(tonumber(Need) or 1)
	if N < 2 or N > 6 then return nil end
	local H = math.clamp(math.floor(tonumber(Have) or 0), 0, N)
	local P = {}
	for I = 1, N do P[I] = I <= H end
	return P
end

return BellTower
```

- [ ] **Step 5: Install and run the test.**

```bash
python -X utf8 -I tools/belltower-r1/harness/install.py tools/belltower-r1/live/ReplicatedStorage.Config.BellTowerArt.luau tools/belltower-r1/live/ReplicatedStorage.Functions.BellTower.luau
python -X utf8 -I tools/belltower-r1/harness/edit.py tools/belltower-r1/checks/bt_pure.lua
```

Expected: the install report lists both modules, then `PASS bt_pure`.

- [ ] **Step 6: Commit** the two modules and the check: "Bell Tower R1: Config.BellTowerArt and Functions.BellTower
  (pure, tested)".

---

### Task 4: ClockHud, the plate, dial and conduct row

**Files:**
- Modify: `tools/belltower-r1/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.ClockHud.luau`. The line numbers
  are those of the dumped file, which matches Studio as of 2026-11-20.
- Test: `tools/belltower-r1/checks/bt_hud.lua` (written here, run again in Tasks 5 and 6)

**Interfaces:**
- Consumes `BellTower.Image`, `HandAngle`, `Conduct`, `Tints`, `MIN_TEXT`, and `BellTowerArt` / `.Slices` (Task 3).
- Produces `ClockHud.Panel` (the cluster), with children `Head` (`Plate`, optional `Dial` with `Moon`/`Face`/`Hand`)
  and `Conduct` (`Slip`, `Seal`, `Level`). The labels `Time`, `Period`, `Class`, `Badge`, `Carry` and `PA` keep their
  names.

- [ ] **Step 1: Write the failing HUD check** `tools/belltower-r1/checks/bt_hud.lua`. It runs in the Client VM in
  Play. It sets a test state on the local player's attributes (client-side only) and checks the HUD.

```lua
local P = game.Players.LocalPlayer
local PG = P:WaitForChild("PlayerGui")
local Fails = {}
local function Check(Ok, What) if not Ok then table.insert(Fails, What) end end
local function Shown(G)
	local X = G
	while X and X:IsA("GuiObject") do if not X.Visible then return false end X = X.Parent end
	return true
end
local State = ... or "owed" -- "owed" | "warning" | "clear" | "active" | "suspended"
local Sets = {
	clear = { DisciplineLevel = "Clear", DisciplinePoints = 0, DetentionsOwed = 0, DetentionActive = false, Suspended = false },
	warning = { DisciplineLevel = "Warning", DisciplinePoints = 3, DetentionsOwed = 0, DetentionActive = false, Suspended = false },
	owed = { DisciplineLevel = "Detention", DisciplinePoints = 6, DetentionsOwed = 1, DetentionActive = false, Suspended = false },
	active = { DisciplineLevel = "Detention", DisciplinePoints = 6, DetentionsOwed = 1, DetentionActive = true, DetentionCollected = 2, DetentionTotal = 5, Suspended = false },
	suspended = { DisciplineLevel = "Suspension", DisciplinePoints = 19, DetentionsOwed = 0, DetentionActive = false, Suspended = true },
}
for K, V in Sets[State] do P:SetAttribute(K, V) end
task.wait(1.2) -- ClockHud ticks every 0.5 s

local Hud = PG:FindFirstChild("ClockHud")
local Panel = Hud and Hud:FindFirstChild("Panel")
Check(Panel ~= nil, "ClockHud.Panel missing")
if not Panel then return "FAIL\n" .. table.concat(Fails, "\n") end
local Frames = 0
for _, K in Hud:GetChildren() do if K:IsA("Frame") then Frames += 1 end end
Check(Frames == 1 and Hud:FindFirstChildWhichIsA("Frame") == Panel, "Panel must be ClockHud's only Frame child")
Check(Panel:FindFirstChild("Head") and Panel.Head:FindFirstChild("Plate"), "Head.Plate missing")
local Conduct = Panel:FindFirstChild("Conduct")
Check(Conduct ~= nil, "Conduct row missing")
if Conduct then
	local WantVisible = State ~= "clear"
	Check(Conduct.Visible == WantVisible, "Conduct.Visible " .. tostring(Conduct.Visible) .. " for " .. State)
	if State == "owed" then Check(Conduct.Slip.Visible and Conduct.Slip.Title.Text == "Detention owed", "owed slip") end
	if State == "active" then Check(Conduct.Slip.Line.Text == "Trash 2/5", "active slip line") end
	if State == "warning" then Check(Conduct.Level.Text == "Warning · 3 pts", "warning level text: " .. Conduct.Level.Text) end
	if State == "suspended" then Check(Conduct.Level.Text == "Suspended", "suspended text") end
end
-- the hand follows the clock
local Dial = Panel.Head:FindFirstChild("Dial")
if Dial then
	local ST = require(game.ReplicatedStorage.Functions.SchoolTime)
	local S = ST.GetState(game.ReplicatedStorage.SchoolClock:GetAttribute("Epoch"), workspace:GetServerTimeNow())
	local Want = ((S.MinuteOfDay / 60) / 24 * 360 + 180) % 360
	local D = math.abs(Dial.Hand.Rotation - Want)
	Check(math.min(D, 360 - D) < 1.5, "hand off by " .. D)
	Check(Dial.Moon.Visible, "moon not in the dial window")
end
-- the house text floor, and nothing cut off
for _, G in { Hud, PG:FindFirstChild("QuestTracker") } do
	for _, L in (G and G:GetDescendants() or {}) do
		if (L:IsA("TextLabel") or L:IsA("TextButton")) and L.Text ~= "" and Shown(L) and not L:FindFirstAncestorWhichIsA("BillboardGui") then
			Check(L.TextSize >= 20, L:GetFullName() .. " TextSize " .. L.TextSize)
			Check(L.TextFits, L:GetFullName() .. " text doesn't fit")
		end
	end
end
-- contracts
Check(Panel:GetAttribute("NHTimetableHooked") == true, "Timetable click hook missing")
local QT = PG:FindFirstChild("QuestTracker")
local T = QT and QT:FindFirstChild("Tracker")
Check(T ~= nil, "QuestTracker.Tracker missing")
if T and T.Visible and T.AnchorPoint.X > 0.5 then
	Check(T.AbsolutePosition.Y >= Panel.AbsolutePosition.Y + Panel.AbsoluteSize.Y - 1, "tracker overlaps the clock cluster")
end
return #Fails == 0 and ("PASS bt_hud " .. State) or ("FAIL " .. State .. "\n" .. table.concat(Fails, "\n"))
```

  `client.py` passes no arguments, so `...` is nil and the default state `owed` is used. To check another state,
  copy the file and change the default (for example `bt_hud_warning.lua` with `or "warning"`).

- [ ] **Step 2: Run it against today's HUD and see it fail.**
  1. Start Play with the Studio MCP `start_stop_play`.
  2. Run `tools/belltower-r1/harness/snapshot.lua` (Server), then `start_play.lua` (Server).
  3. Run `python -X utf8 -I tools/belltower-r1/harness/client.py tools/belltower-r1/checks/bt_hud.lua`.

  Expected: `FAIL owed`, with `Head.Plate missing`, `Conduct row missing` and TextSize lines under 20. Stop Play and
  run `restore.py` (it must print `restored`).
- [ ] **Step 3: Add the requires and constants.** After `local Lineage = …` (line 21), add:

```lua
local BellTower = require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`BellTower`)) -- (2.36) Bell Tower view logic
local Art = require(ReplicatedStorage.Config:WaitForChild(`BellTowerArt`)) -- (2.36) Bell Tower art ids
local DIAL = 176 -- design px
local INK = Color3.fromRGB(58, 26, 20) -- text on paper
local INK_CRIMSON = Color3.fromRGB(122, 16, 24)
```

- [ ] **Step 4: Replace `Local.Label` (lines 30-52).** The size is now exact (the old code added 3 for Garamond), and
  never under the floor.

```lua
function Local.Label(Parent: Instance, Name: string, Order: number, Size: number, Bold: boolean): TextLabel
	Size = math.max(Size, BellTower.MIN_TEXT)
	local Label = Instance.new(`TextLabel`)
	Label.Name = Name
	Label.LayoutOrder = Order
	Label.BackgroundTransparency = 1
	Label.Size = UDim2.new(1, 0, 0, Size + 4)
	Label.Font = if Bold then KitTheme.Fonts.Title else KitTheme.Fonts.Body
	Label.TextSize = Size
	Label.TextColor3 = KitTheme.Colors.Text
	Label.TextXAlignment = Enum.TextXAlignment.Right
	Label.TextWrapped = true
	Label.AutomaticSize = Enum.AutomaticSize.Y
	Label.Text = ``

	local Stroke = Instance.new(`UIStroke`)
	Stroke.Thickness = 1.2
	Stroke.Color = Color3.new(0, 0, 0)
	Stroke.Transparency = 0.25
	Stroke.Parent = Label

	Label.Parent = Parent
	return Label
end

-- (2.36) an art piece from Config.BellTowerArt, or nil while its id is 0 (the caller draws the kit fallback)
function Local.Img(Key: string, Props: { [string]: any }): ImageLabel?
	local Id = BellTower.Image(Art, Key)
	if not Id then return nil end
	local I = Instance.new(`ImageLabel`)
	I.BackgroundTransparency = 1
	I.Image = Id
	local S = Art.Slices[Key]
	if S then
		I.ScaleType = Enum.ScaleType.Slice
		I.SliceCenter = S.Center
		I.SliceScale = S.Scale
	end
	local Parent = Props.Parent
	for K, V in Props do if K ~= `Parent` then (I :: any)[K] = V end end
	I.Parent = Parent
	return I
end
```

- [ ] **Step 5: Replace `Local.CreateGui` (lines 54-121):**

```lua
function Local.CreateGui()
	local Gui = Instance.new(`ScreenGui`)
	Gui.Name = `ClockHud`
	Gui.ResetOnSpawn = false
	Gui.DisplayOrder = 4
	Kit.AutoScale(Gui, { phoneScale = 0.5 }) -- same design-px scale as QuestTracker; smaller on phones

	-- (2.36) The Bell Tower cluster. Panel stays ClockHud's ONLY direct Frame child: Timetable (click + placement),
	-- Moments (BellRim) and TouchControls (Top) find it that way.
	local Panel = Instance.new(`Frame`)
	Panel.Name = `Panel`
	Panel.AnchorPoint = Vector2.new(1, 0)
	Panel.Position = UDim2.new(1, -24, 0, 12)
	Panel.Size = UDim2.new(0, 500, 0, 0)
	Panel.AutomaticSize = Enum.AutomaticSize.Y
	Panel.BackgroundTransparency = 1
	Panel.Parent = Gui
	local Stack = Instance.new(`UIListLayout`)
	Stack.SortOrder = Enum.SortOrder.LayoutOrder
	Stack.HorizontalAlignment = Enum.HorizontalAlignment.Right
	Stack.Padding = UDim.new(0, 8)
	Stack.Parent = Panel

	local Head = Instance.new(`Frame`)
	Head.Name = `Head`
	Head.LayoutOrder = 1
	Head.BackgroundTransparency = 1
	Head.Size = UDim2.new(1, 0, 0, 0)
	Head.AutomaticSize = Enum.AutomaticSize.Y
	Head.Parent = Panel

	local HasDial = BellTower.Image(Art, `Dial`) ~= nil and BellTower.Image(Art, `DialHand`) ~= nil
	-- the plate: TowerPlate 9-slice, or the kit's ornate chip while the art isn't uploaded
	local Plate: GuiObject = Local.Img(`TowerPlate`, { Name = `Plate` }) or Instance.new(`Frame`)
	Plate.Name = `Plate`
	Plate.BackgroundTransparency = 1
	Plate.AnchorPoint = Vector2.new(1, 0)
	Plate.Position = if HasDial then UDim2.new(1, -(DIAL - 30), 0, 22) else UDim2.new(1, 0, 0, 0)
	Plate.Size = UDim2.new(0, if HasDial then 340 else 440, 0, 0)
	Plate.AutomaticSize = Enum.AutomaticSize.Y
	Plate.Parent = Head
	if not Plate:IsA(`ImageLabel`) then Kit.Decorate(Plate, { ornamentScale = 0.6, bgTransparency = 0.08 }) end

	local Lines = Instance.new(`Frame`)
	Lines.Name = `Lines`
	Lines.BackgroundTransparency = 1
	Lines.Size = UDim2.new(1, 0, 0, 0)
	Lines.AutomaticSize = Enum.AutomaticSize.Y
	Lines.ZIndex = 2
	Lines.Parent = Plate
	local Pad = Instance.new(`UIPadding`)
	Pad.PaddingTop = UDim.new(0, 14)
	Pad.PaddingBottom = UDim.new(0, 14)
	Pad.PaddingLeft = UDim.new(0, 22)
	Pad.PaddingRight = UDim.new(0, if HasDial then 40 else 24) -- the dial overlaps the plate's right end by 30
	Pad.Parent = Lines
	local Layout = Instance.new(`UIListLayout`)
	Layout.SortOrder = Enum.SortOrder.LayoutOrder
	Layout.HorizontalAlignment = Enum.HorizontalAlignment.Right
	Layout.Padding = UDim.new(0, 2)
	Layout.Parent = Lines

	local Labels = {
		Time = Local.Label(Lines, `Time`, 1, 28, true);
		Period = Local.Label(Lines, `Period`, 2, 20, false);
		Class = Local.Label(Lines, `Class`, 3, 20, true);
		Badge = Local.Label(Lines, `Badge`, 4, 20, true);
		Carry = Local.Label(Lines, `Carry`, 6, 20, false); -- (1.42) a lost item in your hand (Features.LostFound)
	}
	Labels.PA = Local.Label(Lines, `PA`, 0, 20, true) -- (2.30) the PA (World.Broadcast)
	Labels.PA.TextColor3 = KitTheme.Colors.Gold
	Labels.PA.Visible = false
	Kit.Emboss(Labels.Time, Color3.fromRGB(150, 140, 130), 1.4)
	Labels.Badge.TextColor3 = KitTheme.Colors.Gold

	-- the dial: the moon in its window, the rim (today's timetable), the hand
	local Moon = Instance.new(`ImageLabel`)
	Moon.Name = `Moon`
	Moon.BackgroundTransparency = 1
	Moon.ScaleType = Enum.ScaleType.Fit
	Moon.ImageColor3 = Color3.fromRGB(244, 232, 206)
	Moon.Visible = false
	if HasDial then
		local Dial = Instance.new(`Frame`)
		Dial.Name = `Dial`
		Dial.BackgroundTransparency = 1
		Dial.AnchorPoint = Vector2.new(1, 0)
		Dial.Position = UDim2.new(1, 0, 0, 0)
		Dial.Size = UDim2.fromOffset(DIAL, DIAL)
		Dial.ZIndex = 3
		Dial.Parent = Head
		Moon.AnchorPoint = Vector2.new(0.5, 0.5)
		Moon.Position = UDim2.fromScale(0.5, 0.5)
		Moon.Size = UDim2.fromScale(0.35, 0.35)
		Moon.ZIndex = 3
		Moon.Parent = Dial
		Local.Img(`Dial`, { Name = `Face`; Size = UDim2.fromScale(1, 1); ZIndex = 4; Parent = Dial })
		Labels.Hand = Local.Img(`DialHand`, { Name = `Hand`; Size = UDim2.fromScale(1, 1); ZIndex = 5; Parent = Dial })
	else
		-- (1.41) fallback: tonight's moon just left of the day and time
		Moon.AnchorPoint = Vector2.new(1, 0.5)
		Moon.Size = UDim2.fromOffset(30, 30)
		Moon.ZIndex = 3
		Moon.Parent = Labels.Time
	end
	Labels.Moon = Moon
	Labels.MoonInDial = HasDial

	-- the conduct row: a detention slip, the wax seal, the level (replaces the orange record line)
	local Conduct = Instance.new(`Frame`)
	Conduct.Name = `Conduct`
	Conduct.LayoutOrder = 2
	Conduct.BackgroundTransparency = 1
	Conduct.Size = UDim2.new(1, 0, 0, 0)
	Conduct.AutomaticSize = Enum.AutomaticSize.Y
	Conduct.Visible = false
	Conduct.Parent = Panel
	local Row = Instance.new(`UIListLayout`)
	Row.FillDirection = Enum.FillDirection.Horizontal
	Row.HorizontalAlignment = Enum.HorizontalAlignment.Right
	Row.VerticalAlignment = Enum.VerticalAlignment.Center
	Row.SortOrder = Enum.SortOrder.LayoutOrder
	Row.Padding = UDim.new(0, 10)
	Row.Parent = Conduct

	local Slip: GuiObject = Local.Img(`Slip`, { Name = `Slip` }) or Instance.new(`Frame`)
	Slip.Name = `Slip`
	Slip.BackgroundTransparency = 1
	Slip.LayoutOrder = 1
	Slip.Size = UDim2.fromOffset(300, 100)
	Slip.Visible = false
	Slip.Parent = Conduct
	local OnPaper = Slip:IsA(`ImageLabel`)
	if not OnPaper then Kit.Decorate(Slip, { ornament = `thin`, bgTransparency = 0.1 }) end
	local function SlipText(Name: string, Y: number, Font: Enum.Font, Size: number, Color: Color3): TextLabel
		local L = Instance.new(`TextLabel`)
		L.Name = Name
		L.BackgroundTransparency = 1
		L.Position = UDim2.fromOffset(if OnPaper then 64 else 18, Y)
		L.Size = UDim2.new(1, if OnPaper then -76 else -36, 0, Size + 4)
		L.Font = Font
		L.TextSize = Size
		L.TextColor3 = Color
		L.TextXAlignment = Enum.TextXAlignment.Left
		L.TextScaled = false
		L.ZIndex = 3
		L.Text = ``
		L.Parent = Slip
		return L
	end
	local SlipTitle = SlipText(`Title`, 18, KitTheme.Fonts.Title, 22, if OnPaper then INK_CRIMSON else KitTheme.Colors.Gold)
	local SlipLine = SlipText(`Line`, 50, KitTheme.Fonts.Body, 20, if OnPaper then INK else KitTheme.Colors.Text)

	local Seal = Local.Img(`Seal`, { Name = `Seal`; LayoutOrder = 2; Size = UDim2.fromOffset(66, 66); Visible = false; Parent = Conduct })
	local Level = Instance.new(`TextLabel`)
	Level.Name = `Level`
	Level.LayoutOrder = 3
	Level.BackgroundTransparency = 1
	Level.AutomaticSize = Enum.AutomaticSize.X
	Level.Size = UDim2.fromOffset(0, 30)
	Level.Font = KitTheme.Fonts.Title
	Level.TextSize = 22
	Level.TextColor3 = KitTheme.Colors.Text
	Level.Text = ``
	Level.Visible = false
	Level.Parent = Conduct
	local LS = Instance.new(`UIStroke`)
	LS.Thickness = 1.2
	LS.Transparency = 0.25
	LS.Parent = Level
	Labels.Conduct = { Row = Conduct; Slip = Slip; SlipTitle = SlipTitle; SlipLine = SlipLine; Seal = Seal; Level = Level }

	Gui.Parent = Player:WaitForChild(`PlayerGui`)
	return Labels
end

-- (2.36) the conduct row, from the Discipline attributes. Returns whether the Room 106 marker should show.
function Local.UpdateConduct(Labels, IsClass: boolean): boolean
	local C = BellTower.Conduct({
		DisciplineLevel = Player:GetAttribute(`DisciplineLevel`);
		DisciplinePoints = Player:GetAttribute(`DisciplinePoints`);
		DetentionsOwed = Player:GetAttribute(`DetentionsOwed`);
		DetentionActive = Player:GetAttribute(`DetentionActive`);
		DetentionCollected = Player:GetAttribute(`DetentionCollected`);
		DetentionTotal = Player:GetAttribute(`DetentionTotal`);
		Suspended = Player:GetAttribute(`Suspended`);
	}, IsClass)
	local U = Labels.Conduct
	U.Row.Visible = C.Visible
	local S = C.Slips[1]
	U.Slip.Visible = S ~= nil
	if S then
		U.SlipTitle.Text = S.Title
		U.SlipLine.Text = S.Line
	end
	U.Level.Visible = C.Seal ~= nil
	U.Level.Text = C.Text
	U.Level.TextColor3 = if C.Seal then BellTower.Tints[C.Seal]:Lerp(Color3.new(1, 1, 1), 0.35) else KitTheme.Colors.Text
	if U.Seal then
		U.Seal.Visible = C.Seal ~= nil
		if C.Seal then
			U.Seal.Image = (C.Broken and BellTower.Image(Art, `SealBroken`)) or BellTower.Image(Art, `Seal`) or ``
			U.Seal.ImageColor3 = BellTower.Tints[C.Seal]
		end
	end
	return C.Waypoint
end
```

- [ ] **Step 6: Waypoint text at the floor.** In `Local.UpdateWaypoint`, change `Label.TextSize = 18` to
  `Label.TextSize = BellTower.MIN_TEXT`.
- [ ] **Step 7: The moon and the hand in the update loop.** Replace the block from
  `Labels.Moon.Visible = typeof(Icon) == …` through its `end` (lines 241-251) with this:

```lua
				Labels.Moon.Visible = typeof(Icon) == `string` and Icon ~= ``
				if Labels.Moon.Visible then
					Labels.Moon.Image = Icon
					-- the special moons keep their own colour; the four phases take the HUD's bone tint
					Labels.Moon.ImageColor3 = if Event then Color3.new(1, 1, 1) else Color3.fromRGB(244, 232, 206)
					if not Labels.MoonInDial then
						-- TextBounds is in screen pixels; the panel is in design pixels under its UIScale
						local Sg = Labels.Time:FindFirstAncestorOfClass(`ScreenGui`)
						local Sc = Sg and Sg:FindFirstChildWhichIsA(`UIScale`, true)
						local K = if Sc and Sc.Scale > 0 then Sc.Scale else 1
						Labels.Moon.Position = UDim2.new(1, -(Labels.Time.TextBounds.X / K + 10), 0.5, 0)
					end
				end
				if Labels.Hand then Labels.Hand.Rotation = BellTower.HandAngle(State.MinuteOfDay / 60) end -- (2.36)
```

- [ ] **Step 8: Replace the record block.** Replace everything from `-- Discipline record / detention` through
  `Labels.Record.Visible = Labels.Record.Text ~= ``` (lines 290-314) with:

```lua
				-- (2.36) Discipline: the conduct row (seal, level, slip) replaces the orange record line
				local DetentionWaypoint = Local.UpdateConduct(Labels, State.Segment.Kind == `Class`)
```

  The waypoint lines after it (`if ShowWaypoint and Info then …`) stay as they are. They already read
  `DetentionWaypoint`.
- [ ] **Step 9: Update the header comment.** Append one line to the `--[[ … ]]` at the top: `(2.36) The Bell Tower
  cluster: TowerPlate, the timetable Dial with the moon and hand, and the conduct row (Functions.BellTower). Art in
  Config.BellTowerArt, with kit fallbacks.`
- [ ] **Step 10: Install and parse.** Stop Play first (Edit mode), then run `python -X utf8 -I
  tools/belltower-r1/harness/install.py
  tools/belltower-r1/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.ClockHud.luau`. Expected: one report
  line, and no `PARSE FAIL`.
- [ ] **Step 11: Run the HUD check on the fallbacks** (ids are still 0).
  1. Start Play and run `snapshot.lua` and `start_play.lua`.
  2. Run `client.py` with `bt_hud.lua` (state `owed`), then with the `warning`, `clear`, `active` and `suspended`
     copies.
  3. Stop Play and run `restore.py`.

  Expected: every ClockHud line passes. The only failures left are QuestTracker's, which Task 5 fixes: the
  `TextSize 18` of `Footer` and `Timer`, and `tracker overlaps the clock cluster`.
- [ ] **Step 12: Screenshot for the record.** In the `owed` state, take a Studio MCP `screen_capture`. Save it to
  `docs/img/belltower-r1-fallback.jpg`.
- [ ] **Step 13: Commit** the ClockHud mirror and the checks: "Bell Tower R1: ClockHud plate, dial and conduct row
  (kit fallbacks)".

---

### Task 5: QuestTracker, the Lead Card

**Files:**
- Modify: `tools/belltower-r1/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.QuestTracker.luau`. The line
  numbers are those of the dumped file.
- Test: `tools/belltower-r1/checks/bt_hud.lua` (from Task 4)

**Interfaces:**
- Consumes `BellTower.Image`, `Pips` and `MIN_TEXT`, `BellTowerArt.Slices.LeadCard`, and `ClockHud.Panel`.
- Produces `QuestTracker.Tracker`, still an AnchorPoint (1, 0) card on desktop and (0, 0) on phones, with `Content`
  holding `QuestName`, `Objective`, `Foot` (`Pips`, `Key`, `Footer`) and `Timer`.

- [ ] **Step 1: Add the requires and constants.** After `local StateController = …` (line 22), add:

```lua
local UserInputService = game:GetService(`UserInputService`)
local BellTower = require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`BellTower`)) -- (2.36)
local Art = require(ReplicatedStorage.Config:WaitForChild(`BellTowerArt`)) -- (2.36)
local PAPER_INK = Color3.fromRGB(43, 29, 18)
local PAPER_CRIMSON = Color3.fromRGB(110, 14, 24)
```

- [ ] **Step 2: Replace the tracker card block.** Replace everything in `Local.Build` from `-- Tracker card (under the
  clock, top right)` through the `Timer` label (lines 130-175) with:

```lua
	-- (2.36) The Lead Card (Bell Tower): parchment in a brass clip, or the kit's ornate panel while the art isn't uploaded.
	local CardArt = BellTower.Image(Art, `LeadCard`)
	local OnPaper = CardArt ~= nil
	local Card: GuiObject, Content: GuiObject
	if OnPaper then
		local Img = Instance.new(`ImageLabel`)
		Img.Name = `Tracker`
		Img.BackgroundTransparency = 1
		Img.Image = CardArt :: string
		Img.ScaleType = Enum.ScaleType.Slice
		Img.SliceCenter = Art.Slices.LeadCard.Center
		Img.SliceScale = Art.Slices.LeadCard.Scale
		Img.AnchorPoint = Vector2.new(1, 0)
		Img.Position = UDim2.new(1, -24, 0, 200)
		Img.Size = UDim2.new(0, 470, 0, 0)
		Img.AutomaticSize = Enum.AutomaticSize.Y
		Img.Visible = false
		Img.Parent = Gui
		Card = Img
		local F = Instance.new(`Frame`)
		F.Name = `Content`
		F.BackgroundTransparency = 1
		F.Size = UDim2.new(1, 0, 0, 0)
		F.AutomaticSize = Enum.AutomaticSize.Y
		F.Parent = Img
		local Pad = Instance.new(`UIPadding`)
		Pad.PaddingTop = UDim.new(0, 16)
		Pad.PaddingBottom = UDim.new(0, 20)
		Pad.PaddingLeft = UDim.new(0, 70) -- clear of the brass clip
		Pad.PaddingRight = UDim.new(0, 56) -- clear of the ribbon
		Pad.Parent = F
		Content = F
	else
		local Api
		Card, Api = Components.Panel({
			ornament = `ornate`; ornamentScale = 0.6;
			Name = `Tracker`;
			AnchorPoint = Vector2.new(1, 0);
			Position = UDim2.new(1, -24, 0, 200);
			Size = UDim2.fromOffset(420, 176);
			Visible = false;
			Parent = Gui;
		})
		Content = Api.Content
	end
	local List = Instance.new(`UIListLayout`)
	List.SortOrder = Enum.SortOrder.LayoutOrder
	List.Padding = UDim.new(0, 4)
	List.Parent = Content
	-- phones: the left column under the compass (the right side holds the touch buttons)
	local function PhonePlace()
		if Components.Phone and Components.Phone() then
			Card.AnchorPoint = Vector2.new(0, 0)
			Card.Position = UDim2.new(0, 24, 0, 120)
		else
			Card.AnchorPoint = Vector2.new(1, 0)
			Card.Position = UDim2.new(1, -24, 0, Card.Position.Y.Offset)
		end
	end
	PhonePlace()
	if Components.PreviewChanged then Components.PreviewChanged:Connect(PhonePlace) end
	if workspace.CurrentCamera then workspace.CurrentCamera:GetPropertyChangedSignal(`ViewportSize`):Connect(PhonePlace) end
	local Ink = if OnPaper then PAPER_INK else C.Text
	local Name = Components.Text({
		Name = `QuestName`; Text = ``; Font = Theme.Fonts.Title; TextSize = 24;
		TextColor3 = C.Gold; TextXAlignment = Enum.TextXAlignment.Left; LayoutOrder = 1;
		Size = UDim2.new(1, 0, 0, 30); Parent = Content;
	})
	if not OnPaper then Components.Emboss(Name, Color3.fromRGB(150, 118, 70), 1.4) end
	local Objective = Components.Text({
		Name = `Objective`; Text = ``; Font = Theme.Fonts.Body; TextSize = BellTower.MIN_TEXT;
		TextColor3 = Ink; TextWrapped = true; TextXAlignment = Enum.TextXAlignment.Left;
		TextYAlignment = Enum.TextYAlignment.Top; RichText = true; LayoutOrder = 2;
		Size = UDim2.new(1, 0, 0, 0); AutomaticSize = Enum.AutomaticSize.Y; Parent = Content;
	})
	local Timer = Components.Text({
		Name = `Timer`; Text = ``; Font = Theme.Fonts.BodyBold; TextSize = BellTower.MIN_TEXT;
		TextColor3 = if OnPaper then PAPER_CRIMSON else C.Danger; TextXAlignment = Enum.TextXAlignment.Left;
		LayoutOrder = 3; Visible = false; Size = UDim2.new(1, 0, 0, 24); Parent = Content;
	})
	-- the foot: fang pips on the left, the J Journal key on the right
	local Foot = Instance.new(`Frame`)
	Foot.Name = `Foot`
	Foot.LayoutOrder = 4
	Foot.BackgroundTransparency = 1
	Foot.Size = UDim2.new(1, 0, 0, 36)
	Foot.Parent = Content
	local Pips = Instance.new(`Frame`)
	Pips.Name = `Pips`
	Pips.BackgroundTransparency = 1
	Pips.Size = UDim2.new(0.6, 0, 1, 0)
	Pips.Parent = Foot
	local PipRow = Instance.new(`UIListLayout`)
	PipRow.FillDirection = Enum.FillDirection.Horizontal
	PipRow.VerticalAlignment = Enum.VerticalAlignment.Center
	PipRow.SortOrder = Enum.SortOrder.LayoutOrder
	PipRow.Padding = UDim.new(0, 2)
	PipRow.Parent = Pips
	local Keyboard = UserInputService.KeyboardEnabled
	local Key = Instance.new(`TextLabel`)
	Key.Name = `Key`
	Key.AnchorPoint = Vector2.new(1, 0.5)
	Key.Position = UDim2.new(1, -96, 0.5, 0)
	Key.Size = UDim2.fromOffset(30, 30)
	Key.BackgroundColor3 = C.Ink
	Key.Font = Theme.Fonts.Title
	Key.TextSize = BellTower.MIN_TEXT
	Key.TextColor3 = C.Gold
	Key.Text = `J`
	Key.Visible = Keyboard
	Key.Parent = Foot
	local KeyCorner = Instance.new(`UICorner`)
	KeyCorner.CornerRadius = UDim.new(0, 4)
	KeyCorner.Parent = Key
	local KeyStroke = Instance.new(`UIStroke`)
	KeyStroke.Color = C.GoldDeep
	KeyStroke.Thickness = 2
	KeyStroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	KeyStroke.Parent = Key
	local Footer = Components.Text({
		Name = `Footer`; Text = `Journal`; Font = Theme.Fonts.Body; TextSize = BellTower.MIN_TEXT;
		TextColor3 = if OnPaper then PAPER_INK else C.TextDim; TextXAlignment = Enum.TextXAlignment.Right;
		AnchorPoint = Vector2.new(1, 0.5); Position = UDim2.new(1, 0, 0.5, 0); Size = UDim2.fromOffset(90, 26); Parent = Foot;
	})
```

  The `return { … }` at the end of `Local.Build` becomes:

```lua
	return {
		Gui = Gui; Card = Card; Name = Name; Objective = Objective; Timer = Timer; Footer = Footer;
		Pips = Pips; PipKey = ``; OnPaper = OnPaper; HasPips = BellTower.Image(Art, `PipFang`) ~= nil and BellTower.Image(Art, `PipEmpty`) ~= nil;
		Eye = Eye; EyeLabel = EyeLabel; Fill = Fill; Marker = Marker; MarkerLabel = MarkerLabel;
	}
```

- [ ] **Step 3: Marker text at the floor.** In `Local.Build`'s marker block, change `TextSize = 18` to
  `TextSize = BellTower.MIN_TEXT`.
- [ ] **Step 4: The objective line can leave out its count.** Replace `Local.ObjectiveLine` (lines 282-292) with:

```lua
function Local.ObjectiveLine(Q, Id: string, State, Obj, WithCount: boolean): string
	local Need = Obj.Count or 1
	local Have = (State.Counts or {})[Obj.Id] or 0
	local Text = Obj.Text
	if WithCount and Need > 1 then Text ..= `  ({Have}/{Need})` end
	if Obj.Item and State.Items and State.Items[Obj.Item] == `Dropped` then
		local Item = QuestConfig.Items[Obj.Item]
		local Red = if Ui and Ui.OnPaper then PAPER_CRIMSON else C.Danger
		Text = `<font color="#{Red:ToHex()}">You dropped the {Item and Item.Name or Obj.Item}! Pick it back up.</font>`
	end
	return Text
end

-- (2.36) fang pips for a counted objective; rebuilt only when the count changes
function Local.SetPips(List: { boolean }?, Have: number, Need: number)
	local Key = if List then `{Have}/{Need}` else ``
	if Ui.PipKey == Key then return end
	Ui.PipKey = Key
	for _, K in Ui.Pips:GetChildren() do if K:IsA(`GuiObject`) then K:Destroy() end end
	if not List then return end
	for I, Filled in List do
		local Img = Instance.new(`ImageLabel`)
		Img.Name = `Pip{I}`
		Img.LayoutOrder = I
		Img.BackgroundTransparency = 1
		Img.Size = UDim2.fromOffset(34, 34)
		Img.Image = BellTower.Image(Art, if Filled then `PipFang` else `PipEmpty`) or ``
		Img.Parent = Ui.Pips
	end
	local Count = Instance.new(`TextLabel`)
	Count.Name = `Count`
	Count.LayoutOrder = 99
	Count.BackgroundTransparency = 1
	Count.AutomaticSize = Enum.AutomaticSize.X
	Count.Size = UDim2.fromOffset(0, 30)
	Count.Font = Theme.Fonts.Body
	Count.TextSize = BellTower.MIN_TEXT
	Count.TextColor3 = if Ui.OnPaper then PAPER_INK else C.Text
	Count.Text = `  {Have}/{Need}`
	Count.Parent = Ui.Pips
end

-- (2.36) hang the card under the clock cluster (it grows with the PA line, the plate and the conduct row)
function Local.Follow()
	if Ui.Card.AnchorPoint.X < 0.5 then return end -- phones keep their left-column spot
	local Hud = Player.PlayerGui:FindFirstChild(`ClockHud`)
	local Panel = Hud and Hud:IsA(`ScreenGui`) and Hud.Enabled and Hud:FindFirstChild(`Panel`)
	if not (Panel and Panel:IsA(`GuiObject`)) then return end
	local U = Ui.Gui:FindFirstChild(`NHAutoScale`)
	local Scale = if U and U:IsA(`UIScale`) and U.Scale > 0 then U.Scale else 1
	local Want = math.floor((Panel.AbsolutePosition.Y + Panel.AbsoluteSize.Y) / Scale + 12)
	if math.abs(Ui.Card.Position.Y.Offset - Want) > 1 then Ui.Card.Position = UDim2.new(1, -24, 0, Want) end
end
```

- [ ] **Step 5: Use them in `Local.UpdateTracker`.**
  - Replace `Ui.Objective.Text = Local.ObjectiveLine(Q, Id, State, Obj)` with:

```lua
	local Need = Obj.Count or 1
	local Have = (State.Counts or {})[Obj.Id] or 0
	local PipList = if Ui.HasPips then BellTower.Pips(Have, Need) else nil
	Ui.Objective.Text = Local.ObjectiveLine(Q, Id, State, Obj, PipList == nil)
	Local.SetPips(PipList, Have, Need)
	Local.Follow()
```

  - In the same function, change `Ui.Name.TextColor3 = if Def.Category == `Main` then C.Gold else C.Text` to:

```lua
	Ui.Name.TextColor3 = if Ui.OnPaper then (if Def.Category == `Main` then PAPER_CRIMSON else PAPER_INK)
		else (if Def.Category == `Main` then C.Gold else C.Text)
```

  - After the timer `if State.Deadline … end` block, add `Ui.Timer.Visible = Ui.Timer.Text ~= ``.
- [ ] **Step 6: Install.** In Edit, run `install.py` with
  `tools/belltower-r1/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.QuestTracker.luau`. Expected: one
  report line and no `PARSE FAIL`.
- [ ] **Step 7: Run the HUD check, five states, on the fallbacks.** Do it as in Task 4 Step 11: snapshot, play,
  checks, stop, restore. Expected: `PASS bt_hud <state>` for all five.
  - The tracker shows only when slot 2 has a tracked quest. If it has none, give it one through the Journal UI
    (Track), and note that this saves. `restore.py` puts it back afterwards.
- [ ] **Step 8: Commit** the QuestTracker mirror: "Bell Tower R1: the Lead Card quest tracker (pips, J key, follows
  the clock)".

---

### Task 6: The art ids, contracts and screenshots

**Files:**
- Modify: `tools/belltower-r1/live/ReplicatedStorage.Config.BellTowerArt.luau` (ids)
- Create: `docs/img/belltower-r1-{calm,owed,active,suspended,fallback}.jpg`

**Interfaces:** Consumes the owner's 9 asset ids from Task 2 Step 4.

- [ ] **Step 1: Fill in the ids.** Put the owner's ids into `Config.BellTowerArt`: `Dial`, `DialHand`, `TowerPlate`,
  `Seal`, `SealBroken`, `Slip`, `LeadCard`, `PipEmpty`, `PipFang`. Install it in Edit. If the ids haven't arrived,
  stop here, report "R1 done on fallbacks; art ids pending", and skip to Task 7. The screenshots wait for the ids.
- [ ] **Step 2: Run the HUD check with the art.** Do it as in Task 4 Step 11, all five states. Expected:
  `PASS bt_hud <state>`, now including the hand (within 1.5° of the clock) and the moon in the dial.
- [ ] **Step 3: Check the contracts in Play.** Run one client file, `checks/bt_contracts.lua`:

```lua
local P = game.Players.LocalPlayer
local PG = P.PlayerGui
local Out = {}
local Panel = PG.ClockHud.Panel
-- Timetable's click hook is on the cluster (the real click is Step 3b)
table.insert(Out, "timetable hooked " .. tostring(Panel:GetAttribute("NHTimetableHooked") == true))
-- where to click: the dial's centre, in screen px (for Step 3b)
local Dial = Panel.Head:FindFirstChild("Dial") or Panel.Head.Plate
local Inset = game:GetService("GuiService"):GetGuiInset()
table.insert(Out, ("click at %d,%d"):format(Dial.AbsolutePosition.X + Dial.AbsoluteSize.X / 2, Dial.AbsolutePosition.Y + Dial.AbsoluteSize.Y / 2 + Inset.Y))
-- Moments' bell rim still finds the panel
table.insert(Out, "panel for Moments " .. tostring(PG.ClockHud:FindFirstChild("Panel") ~= nil))
-- SchoolFx's "In class" line exists when ClassInRoom
P:SetAttribute("ClassInRoom", true) task.wait(1)
local Found = false
for _, D in PG.ClockHud:GetDescendants() do if D:IsA("TextLabel") and D.Visible and D.Text:find("In class", 1, true) then Found = true end end
table.insert(Out, "in-class line " .. tostring(Found) .. " (needs a class period; false outside class is expected)")
P:SetAttribute("ClassInRoom", nil)
-- Settings ShowClock hides the whole cluster
PG.ClockHud.Enabled = false task.wait(0.3) table.insert(Out, "hidden " .. tostring(not PG.ClockHud.Enabled)) PG.ClockHud.Enabled = true
return table.concat(Out, "\n")
```

  Expected: `timetable hooked true`, `panel for Moments true` and `hidden true`. For the "In class" line, run it
  once with `start_play.lua` set to `SetTime "09:10"` (Period 2). There it must say `in-class line true`.
- [ ] **Step 3b: Click the dial for real.** Send one left click to the printed `click at x,y` with the Studio MCP
  `user_mouse_input`, then take a `screen_capture`. Expected: the Timetable opens, hanging below the whole cluster
  (seal row included) and not over it. Click again to close it.
- [ ] **Step 4: Check the PA line.** In Play, on the Server, run
  `game.ReplicatedStorage.NHBroadcast:FireAllClients({ Kind = "PA", Text = "Assembly in the Main Hall at noon." })`.
  Expected: the gold PA line types in on the plate, above the time, at 20 px, and the tracker card moves down to
  stay below it.
- [ ] **Step 5: Take screenshots** with the Studio MCP `screen_capture`, cropped to the top right. Take one each for
  the calm (Clear, a tracked quest with a count), owed, active and suspended states, and save them to `docs/img/`
  under the names above. Compare them with the mockup's "Class soon" and "Curfew night" frames: same layout and
  order, with the text 20 px or more.
- [ ] **Step 6: Phone.** If the Studio device emulator is available, set it to a phone (under 600 px on the short
  side) and check that:
  - the cluster scales (phoneScale 0.5)
  - the Lead Card sits in the left column under the compass
  - nothing overlaps the touch buttons

  If it isn't available, write "phone layout not seen" in the CHANGELOG entry (Task 7).
- [ ] **Step 7: Restore and commit.** Stop Play and run `restore.py` (it must print `restored`). Commit the ids and
  the screenshots: "Bell Tower R1: art ids, contract checks, screenshots".

---

### Task 7: Docs, graph and the PR-ready state

**Files:**
- Modify: `docs/UI-Kit.md`, in the "Reskinned game UI and in-play HUD" table (the `ClockHud` row), plus a new
  `### The Bell Tower cluster (2.36)` section after `### KitHud`
- Modify: `docs/Attendance-and-Discipline.md`, its **HUD** line in the Detention section
- Modify: `docs/School-Simulation.md`, the ClockHud bullet under "How it works"
- Modify: `CHANGELOG.md`, a new top entry
- Modify: the spec's status line

- [ ] **Step 1: `UI-Kit.md`.**
  - Change the `ClockHud` row to: "The Bell Tower cluster (2.36): the timetable Dial with the moon and hand, the time
    lines on an iron TowerPlate, and the conduct row (wax seal, level, detention slip). Kit fallbacks while an art id
    is 0."
  - Add the new section. It lists:
    - the art table: the 9 pieces, their sizes, `Config.BellTowerArt`, and the 9-slice data from Task 3
    - the layout numbers: Panel 500 wide; Dial 176; Plate 340, overlapping the dial by 30; the conduct row; the Lead
      Card at 470 wide, 70/56 padding, following the clock + 12
    - `Functions.BellTower`'s API
    - the 20 px floor
    - the fallbacks
    - the contracts table from Global Constraints
- [ ] **Step 2: `Attendance-and-Discipline.md`.** Change "**HUD:** the clock panel has a fifth line: …" to: "**HUD
  (2.36):** the conduct row under the clock: a wax seal tinted by level with "Warning · 3 pts", and a detention slip
  ("Detention owed · Room 106, outside class", or "Trash 2/5" during a session). The Room 106 marker still shows
  outside class time."
- [ ] **Step 3: `School-Simulation.md`.** Change the ClockHud bullet to name the dial: "a top-right cluster: the
  timetable dial (the hand at now, the moon in its window), the day and time, the period and when it ends, and the
  school-hours badge."
- [ ] **Step 4: `CHANGELOG.md`.** Add an entry in the file's style, under the next version: "## [2.36.0] -
  <date>: The Bell Tower, R1: the clock, conduct and quest cluster". It says:
  - what changed (Task 4 and Task 5 in plain words)
  - the art and where its ids live
  - that no rules changed
  - the text floor
  - what was verified (the five `bt_hud` states, the contracts, the PA)
  - what wasn't (the phone, if not seen; two players)
  - the Studio backup folder
- [ ] **Step 5: The spec's status line.** Add: "R1 built in 2.36.0 (plan
  `docs/superpowers/plans/2026-11-20-belltower-r1-cluster.md`)." Also add the spec delta: ClockHud and QuestTracker
  were rebuilt in place instead of getting a new controller (see this plan's Architecture).
- [ ] **Step 6: The graph.** Run `cd /e/NH-belltower && python -m graphify update .`. Expected: it finishes without
  errors.
- [ ] **Step 7: Commit** the docs and the graph: "Bell Tower R1: docs (UI-Kit, Attendance & Discipline, School
  Simulation), changelog, graph". Then report to the owner with the branch name, the screenshots, and anything not
  verified.
