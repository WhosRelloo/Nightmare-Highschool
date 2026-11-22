# Strafe Walks + NPC Gestures Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Every subagent runs on model "opus".

**Goal:**
- **Strafes:** the player strafes in lock-on, shift lock and first person, on any input. Each strafe is a
  counter-rotated, foot-locked clip (the chest squared), blended by direction with phase-synced feet, at 8.5 studs/s.
- **Backward walk:** a reversed Walk.
- **Cadence:** every player gait plays at a stride-matched cadence, and CineActor uses the same rule.
- **NPC gestures:** NPCs use the FIER ANIMATIONS clips where they fit, through a new `StudentBrain.Gestures` service
  and `Config.Gestures`.
- **New places:** the get-up reaction, an infirmary with a Nurse and patients, and bleacher seats with an Athletes
  "watch the match" job.

**Architecture:**
- **Pure maths:** `Functions.Locomotion` and `Functions.Gestures` (VM-tested), with tunables in `Config.Locomotion`
  and `Config.Gestures`.
- **The clips:** extracted read-only from FIER to JSON, baked offline by `tools/phase6-strafes/anim/bake.py`
  (pytest-tested), then built into NH's `ServerStorage.NHGestures` and `ServerStorage.NHPublish.Gestures`.
- **Before the owner publishes:** Studio plays the KeyframeSequences through `RegisterKeyframeSequence` (the Nudges
  pattern), and live servers skip unpublished clips.
- **The strafe speed:** a server cap in `Features.CombatSpeed`, fed by a new `NHStrafe` RemoteEvent.

**Tech Stack:**
- **Game:** Roblox Luau in NH Combat Test (placeId 98950102230473). Scripts are installed from repo mirrors through
  `E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py`.
- **Bake:** Python 3 with numpy and pytest.
- **Read-only sources:** FIER ANIMATIONS (107424155290133) and Map (111107083446202).

**Spec:** `docs/superpowers/specs/2026-11-22-strafes-npc-gestures-design.md`.
**Research:** `docs/superpowers/research/2026-11-22-strafes-npc-gestures-survey.md`.

## Global Constraints

- **Places:**
  - Build only in **NH Combat Test**.
  - **FIER ANIMATIONS: read and copy only.** Never create, edit, delete or save anything there. Every FIER call is a
    read (`execute_luau` returning text).
  - **Map (111107083446202): read only.** Never move, edit or add to its builds.
- **Read first:** `docs/Pipeline-Lessons.md` (on the main checkout) before any Studio step.
- **Studio is shared:**
  - One session drives NH Combat Test at a time.
  - **Studio-modifying tasks (marked [STUDIO]) start only after "Studio released (phase6)"** from the tutorial
    session, or the owner's word that it's free. When done, send "Studio released" back, from Edit mode with slot 2
    restored.
  - Bell Tower R2 is next in the queue.
  - **[STUDIO-READ]** tasks only read (dumps, extracts, surveys). They can run whenever the place is in Edit
    (`get_studio_state`). During someone else's Play, read the Server or Client DataModel; never start or stop Play
    yourself in another session's round.
  - **Never save, close, reload or revert any place.** The owner saves NH Combat Test.
  - **Never edit `ServerStorage.NHTestBridge`**, and never run an ad-hoc script that invokes it outside the harness's
    `start_play.lua`. If the permission system denies anything, stop and report the exact text.
- **Branch:** `phase6-strafes` in the worktree `E:\NH-strafes` (cut from `phase6-tutorial`).
  - Never switch branches in `E:\Nightmare-Highschool`.
  - Commits use `git -c user.name=Rello` and end with:
    ```
    Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
    Claude-Session: https://claude.ai/code/session_016roggwHneH5XgNzN25tniz
    ```
- **Backups:** before the first [STUDIO] edit, copy each changed script to
  `ServerStorage.NH_Backup.Phase6Strafes_pre_<yyyymmdd>`, named `<Service>_<path_with_underscores>`.
- **Mirrors:**
  - `tools/phase6-strafes/pre/` holds the scripts before this plan, and `live/` holds them after. One `.luau` per
    script, named by its dotted path.
  - Studio is changed only by `harness/install.py` from `live/`, in Edit.
  - **The dump (Task S3) is the source of truth.** The older `tools/*/pre` copies are stale.
- **The Play run order** (from phase6; every Play run):
  1. Confirm Edit mode, then install.
  2. Start Play with `start_stop_play`. If it times out, check `get_studio_state`.
  3. Run `harness/start_play.lua` on the Server. This plan's copy sets `SetTime "12:30"`, After School: matches,
     hangouts, monitors on duty.
  4. On the first run of a round, run `harness/snapshot.lua` on the Server and save its JSON to
     `harness/_slot2.json`.
  5. Run the checks.
  6. Run `harness/restore.py` while still in Play. It must print `restored`.
  7. Stop Play.
- **Test slot:** slot 2 only. Never commit `_slot2.json` or the underscore temp files (except `_backup.lua`).
- **House style (owner):**
  - realistic legs, planted feet, no skate, weight;
  - reuse the existing clips;
  - R6 (`r6-animation-cinematics`);
  - **UI: existing assets only** (no new UI is planned here).
- **The spec's numbers, verbatim:**

| Item | Value |
|---|---|
| Strafe speed | 8.5 studs/s cap, walk band only (raw ≤ 20, > FLOOR 8) |
| Strides (1x, 2-stud legs) | Walk 5.9, Sprint 13.5, CrouchWalk 3.5, FastSprint 18.0, Strafe 5.8 |
| Cadence clamp | 0.3 to 2.4 |
| Strafe mode hysteresis / fade | 0.12 s / 0.15 s |
| Gesture caps | MaxActive 6, NearRange 60, Cooldown 20 s, StopFar 80 |
| Scale buckets | 0.8, 0.9, 1.0 (task S2 may drop 0.8) |
| Infirmary spot | centre (214, 6, 24), 26 × 24, opposite R106 |
| Get-up idle | 5-8 s, Dizzy 60 % / InjuredHurt 40 % |
| Infirmary visit | 60-120 s, within an in-game hour of the get-up |

## Task order

**Repo-only (no Studio at all):**
- **R1:** scaffolding.
- **R2:** `Config.Locomotion` and `Functions.Locomotion`, plus `lc_pure.lua`.
- **R3:** the baker transforms (pytest).
- **R4:** `Config.Gestures` and `Functions.Gestures`, plus `gs_pure.lua`.
- **R5:** `StudentBrain.Space` and `StudentBrain.Gestures` (new modules).
- **R6:** the builder Luau for the infirmary and the bleachers (written, not run).
- **R7:** the check scripts.

**Studio, read only:**
- **S1:** surveys (the Map spot, the bleachers, `Sports.Matches`, the UnPackets format).
- **S2:** the FIER extract, plus `scaleprobe` **design**. The probe itself runs in T5.
- **S3:** the NH pre-dump.

**Repo again, on the dumps:**
- **R8:** bake the real clips.
- **R9:** the AnimationController, CineActor and CombatSpeed edits.
- **R10:** the hook edits (StudentBrain, Nudges, Schedules, Scenes, Npcs, HallMonitor, CliqueFights, Seats, Regions,
  AmbientNpcs, Dialogue).

**Studio, modifying (after "Studio released (phase6)"):**
- **T1:** backups.
- **T2:** install the KeyframeSequences.
- **T3:** build the infirmary and the bleachers.
- **T4:** install the scripts and run the Edit checks.
- **T5:** the Play rounds.
- **T6:** screenshots and release.

**Owner steps, then repo:**
- **O1:** the publish list and the id lookup.
- **R11:** docs and the changelog.

---

## File structure

| File | Responsibility | New / changed |
|---|---|---|
| `tools/phase6-strafes/harness/{install.py,dump.py,edit.py,client.py,server.py,snapshot.lua,restore.py,start_play.lua}` | the harness, copied from `tools/phase6-2350/harness` | new |
| `tools/phase6-strafes/anim/extract_fier.luau` | the read-only FIER serialiser | new |
| `tools/phase6-strafes/anim/{bake.py,recipes.json,test_bake.py}` | the transforms, recipes and tests | new |
| `tools/phase6-strafes/anim/src/*.json`, `anim/out/*.lua`, `anim/out/manifest.json`, `anim/REPORT.md` | the extracted and baked clips | new (generated) |
| `tools/phase6-strafes/build/{gestures_ks.luau,infirmary.luau,bleachers.luau,_backup.lua}` | the Edit builders | new |
| `…/live/ReplicatedStorage.Config.Locomotion.luau` | the locomotion numbers and clip ids | new |
| `…/live/ReplicatedStorage.Functions.Locomotion.luau` | Weights, StrafeMode, Rate, Phase | new |
| `…/live/ReplicatedStorage.Config.Gestures.luau` | Clips, Cast, Caps, GetUp, Infirmary, Watch | new |
| `…/live/ReplicatedStorage.Functions.Gestures.luau` | Pick, Bucket | new |
| `…/live/ServerScriptService.Services.AI.StudentBrain.Space.luau` | the clear and room checks shared by Nudges and Gestures | new |
| `…/live/ServerScriptService.Services.AI.StudentBrain.Gestures.luau` | the service, Carry, GetUp and the probe | new |
| `…/live/StarterPlayer.StarterPlayerScripts.Controllers.Character.AnimationController.luau` | the directional blend and stride-matched rates | changed |
| `…/live/StarterPlayer.StarterPlayerScripts.Controllers.CineActor.luau` | `STRIDE` comes from `Config.Locomotion` | changed |
| `…/live/ServerScriptService.Services.Features.CombatSpeed.luau` | the `NHStrafe` remote and the cap | changed |
| `…/live/ServerScriptService.Services.AI.StudentBrain.luau` | fidget, chat, Gawk, Danger | changed |
| `…/live/ServerScriptService.Services.AI.StudentBrain.Nudges.luau` | uses Space | changed |
| `…/live/ServerScriptService.Services.Features.Schedules.luau` | PhoneWalk, Linger, Mingle (Locker), Watch, Infirmary, Replan | changed |
| `…/live/ServerScriptService.Services.World.Scenes.luau`, `…/live/ReplicatedStorage.Config.Scenes.luau` | the `anim` op and its steps | changed |
| `…/live/ServerScriptService.Services.Social.Npcs.luau`, `…/live/ReplicatedStorage.Config.Npcs.luau` | the Post loop; the Nurse | changed |
| `…/live/ServerScriptService.Services.School.HallMonitor.luau` | Point on Confront | changed |
| `…/live/ServerScriptService.Services.Social.CliqueFights.luau` | ScuffleLoser | changed |
| `…/live/ServerScriptService.Services.Features.Seats.luau` | the `Bleacher` kind | changed |
| `…/live/ReplicatedStorage.Config.Regions.luau` | `Infirmary` | changed |
| `…/live/ServerScriptService.Services.Features.AmbientNpcs.luau` | the infirmary patient | changed |
| `tools/phase6-strafes/dialogue/Nurse.luau` | the builder for `ServerStorage.Dialogue.Nurse` | new |
| `tools/phase6-strafes/checks/*.lua` | lc_pure, gs_pure, clipcheck, infirmarycheck, scaleprobe, strafecheck, footcheck, cinegate, gesturecheck, getupcheck, nursecheck, watchcheck | new |
| `CHANGELOG.md`, `docs/Gameplay-and-NPC-Concepts.md` (gestures), a new `docs/Movement.md` and `docs/Infirmary.md`, the spec | docs | changed or new |

(`…` = `tools/phase6-strafes`.)

---

### Task R1: Scaffolding [REPO-ONLY]

**Files:** Create `tools/phase6-strafes/{harness,anim,build,checks,dialogue,live,pre}/`.

- [ ] **Step 1: Copy the harness.**
  - From `tools/phase6-2350/harness/`, copy `install.py dump.py bridge.py client.py snapshot.lua restore.py
    start_play.lua`.
  - In `dump.py` and `install.py`, replace `phase6-2350` with `phase6-strafes`.
  - In `start_play.lua`, change `B:Invoke("SetTime", "21:30")` to `B:Invoke("SetTime", "12:30")`.
- [ ] **Step 2: Add `edit.py` and `server.py`.** They're `client.py` with `"Client"` replaced by `"Edit"` and by
  `"Server"`.
- [ ] **Step 3: Add `.gitignore`** in `tools/phase6-strafes/`:
  ```
  harness/_*
  !build/_backup.lua
  anim/__pycache__/
  ```
- [ ] **Step 4: Commit:** "phase6-strafes: harness and scaffolding".

---

### Task R2: `Config.Locomotion` and `Functions.Locomotion` (pure, TDD) [REPO-ONLY to write; the run needs a read-only VM]

**Files:**
- Create: `…/live/ReplicatedStorage.Config.Locomotion.luau`
- Create: `…/live/ReplicatedStorage.Functions.Locomotion.luau`
- Test: `tools/phase6-strafes/checks/lc_pure.lua`

**Interfaces:** `Functions.Locomotion` is pure. It takes the Config as an argument, so the check can run in any VM
with no installs.

| Member | Returns |
|---|---|
| `Weights(Angle: number): {Walk, Back, Left, Right}` | normalised, sum 1 |
| `StrafeMode(F: {Gait, Locked, MouseLocked, FirstPerson, Blocked}): boolean` | the §1.3 rule |
| `Blocked(Flags: {[string]: any}, Cfg): boolean` | true if any name in `Cfg.Blockers` is truthy |
| `Rate(Ground: number, Stride: number, LegLen: number, Cfg): number` | the clamped cadence |
| `Phase(DomTime, DomLen, SecLen, DomContact, SecContact): number` | the secondary track's TimePosition |

- [ ] **Step 1: Write the failing test** `checks/lc_pure.lua`.
  - Run it in a VM with no game access: any Edit VM, with **no instance writes**.
  - It reads the two sources from the repo through the local HTTP bridge (`python -m http.server 8833 --bind
    127.0.0.1` in `tools/phase6-strafes/live`) and `loadstring`s them.

```lua
local H = game:GetService("HttpService")
local function load(name) return loadstring(H:GetAsync("http://127.0.0.1:8833/" .. name))() end
local Cfg = load("ReplicatedStorage.Config.Locomotion.luau")
local L = load("ReplicatedStorage.Functions.Locomotion.luau")
local Fails = {}
local function Near(G, W, What, Tol) if math.abs(G - W) > (Tol or 1e-3) then table.insert(Fails, What .. ": got " .. G .. " want " .. W) end end
local function Eq(G, W, What) if G ~= W then table.insert(Fails, What .. ": got " .. tostring(G) .. " want " .. tostring(W)) end end
-- weights: forward, left, right, back, diagonals
local W = L.Weights(0) Near(W.Walk, 1, "fwd walk") Near(W.Left + W.Right + W.Back, 0, "fwd rest")
W = L.Weights(-math.pi / 2) Near(W.Left, 1, "left") W = L.Weights(math.pi / 2) Near(W.Right, 1, "right")
W = L.Weights(math.pi) Near(W.Back, 1, "back")
W = L.Weights(math.pi / 4) Near(W.Walk, 0.5, "fwd-right walk") Near(W.Right, 0.5, "fwd-right right")
W = L.Weights(-3 * math.pi / 4) Near(W.Back, 0.5, "back-left back") Near(W.Left, 0.5, "back-left left")
for _, A in { 0.3, 1.2, 2.9, -0.7, -2.2 } do local V = L.Weights(A) Near(V.Walk + V.Back + V.Left + V.Right, 1, "sum " .. A) end
-- strafe mode
Eq(L.StrafeMode({ Gait = "Walk", Locked = true }), true, "locked walk")
Eq(L.StrafeMode({ Gait = "Walk", MouseLocked = true }), true, "shift lock walk")
Eq(L.StrafeMode({ Gait = "Walk", FirstPerson = true }), true, "first person walk")
Eq(L.StrafeMode({ Gait = "Walk" }), false, "free camera walk")
Eq(L.StrafeMode({ Gait = "Sprint", Locked = true }), false, "sprint")
Eq(L.StrafeMode({ Gait = "CrouchWalk", Locked = true }), false, "crouch")
Eq(L.StrafeMode({ Gait = "Walk", Locked = true, Blocked = true }), false, "blocked")
-- blockers
Eq(L.Blocked({ NHApproach = true }, Cfg), true, "approach blocks")
Eq(L.Blocked({ NHCineSeam = "In" }, Cfg), true, "seam blocks")
Eq(L.Blocked({ NHInCine = true }, Cfg), true, "incine blocks")
Eq(L.Blocked({ NHCineHold = true }, Cfg), true, "hold blocks")
Eq(L.Blocked({}, Cfg), false, "nothing blocks")
-- rate: stride-matched, clamped
Near(L.Rate(14.4, Cfg.Stride.Walk, 1.615, Cfg), math.min(Cfg.CadenceMax, 14.4 / (5.9 * 0.8075)), "walk rate", 1e-2)
Near(L.Rate(8.5, Cfg.Stride.Strafe, 1.615, Cfg), 8.5 / (5.8 * 0.8075), "strafe rate", 1e-2)
Near(L.Rate(0.1, Cfg.Stride.Walk, 2, Cfg), Cfg.CadenceMin, "rate floor")
Near(L.Rate(40, Cfg.Stride.Walk, 2, Cfg), Cfg.CadenceMax, "rate cap")
-- phase sync: contact phases line up
Near(L.Phase(0.585, 1.17, 1.03, 0, 0), 0.515, "phase half")
Near(L.Phase(0, 1.17, 1.03, 0.1, 0.3), (0.3 - 0.1) * 1.03 % 1.03, "phase offset")
-- config sanity
Eq(Cfg.StrafeSpeed, 8.5, "strafe speed") Eq(Cfg.WalkBandMax, 20, "walk band")
Eq(typeof(Cfg.Ids.StrafeLeft), "number", "strafe ids")
return #Fails == 0 and "PASS lc_pure" or ("FAIL\n" .. table.concat(Fails, "\n"))
```

- [ ] **Step 2: Run it and see it fail.**
  1. Start the bridge: `cd tools/phase6-strafes/live && python -m http.server 8833 --bind 127.0.0.1`.
  2. Run `python -X utf8 -I tools/phase6-strafes/harness/edit.py tools/phase6-strafes/checks/lc_pure.lua`.
  3. Expected: an HTTP 404 error (the files don't exist yet).

  The NH Edit VM must be readable. Otherwise use the FIER Edit VM through
  `rbxc.py luau "placeId: 107424155290133" Edit`: the script only reads HTTP and computes; nothing is written.
- [ ] **Step 3: Write `ReplicatedStorage.Config.Locomotion.luau`:**

```lua
--[[ (phase6-strafes) Locomotion numbers. Spec: docs/superpowers/specs/2026-11-22-strafes-npc-gestures-design.md §1.
	Strides: studs/s each clip covers at 1x on 2-stud R6 legs (measured by FK, survey §A4 and spec §1.2). ]]
return {
	Ids = {
		-- the square-chest bakes (NHG_StrafeLeft_Square / Right) once published; 0 = use the originals below
		StrafeLeftSquare = 0; StrafeRightSquare = 0;
		StrafeLeft = 126969213208550; StrafeRight = 84541589738848;
	};
	Studio = { StrafeLeftSquare = "NHG_StrafeLeft_Square"; StrafeRightSquare = "NHG_StrafeRight_Square" }; -- ServerStorage.NHGestures
	Stride = { Walk = 5.9; Sprint = 13.5; CrouchWalk = 3.5; FastSprint = 18.0; Strafe = 5.8 };
	ContactPhase = { Walk = 0; Strafe = 0 }; -- left-foot contact as a fraction of the cycle (bake.py manifest fills these)
	Length = { Walk = 1.17; Strafe = 1.033 };
	CadenceMin = 0.3;
	CadenceMax = 2.4;
	StrafeSpeed = 8.5;
	WalkBandMax = 20;
	EnterHold = 0.12;
	Fade = 0.15;
	FirstPersonDist = 1;
	Blockers = { "NHInCine", "NHApproach", "NHCineSeam", "NHCineHold", "NHTutorial", "Transformation", "WolfForm", "NHSkating", "NHEmoting", "Busy" };
	RemoteRate = 10; -- NHStrafe messages per second per player
}
```

- [ ] **Step 4: Write `ReplicatedStorage.Functions.Locomotion.luau`:**

```lua
--!strict
--[[ (phase6-strafes) Pure locomotion maths (no services, no instances). Callers pass Config.Locomotion. ]]
local L = {}

function L.Weights(A: number): { Walk: number, Back: number, Left: number, Right: number }
	local C, S = math.cos(A), math.sin(A)
	local W = { Walk = math.max(0, C), Back = math.max(0, -C), Left = math.max(0, -S), Right = math.max(0, S) }
	local Sum = W.Walk + W.Back + W.Left + W.Right
	if Sum < 1e-6 then return { Walk = 1, Back = 0, Left = 0, Right = 0 } end
	W.Walk /= Sum W.Back /= Sum W.Left /= Sum W.Right /= Sum
	return W
end

function L.StrafeMode(F: { [string]: any }): boolean
	if F.Gait ~= "Walk" or F.Blocked then return false end
	return F.Locked == true or F.MouseLocked == true or F.FirstPerson == true
end

function L.Blocked(Flags: { [string]: any }, Cfg: any): boolean
	for _, N in Cfg.Blockers do
		local V = Flags[N]
		if V ~= nil and V ~= false then return true end
	end
	return false
end

function L.Rate(Ground: number, Stride: number, LegLen: number, Cfg: any): number
	local Per = Stride * math.max(LegLen, 0.1) / 2
	return math.clamp(Ground / Per, Cfg.CadenceMin, Cfg.CadenceMax)
end

-- the secondary track's TimePosition so both clips' left-foot contacts line up
function L.Phase(DomTime: number, DomLen: number, SecLen: number, DomContact: number, SecContact: number): number
	local P = (DomTime / DomLen - DomContact + SecContact) % 1
	return P * SecLen
end

return L
```

- [ ] **Step 5: Run it.** Expected: `PASS lc_pure`.
- [ ] **Step 6: Commit:** "phase6-strafes: Config.Locomotion and Functions.Locomotion (pure, tested)".

---

### Task R3: The baker transforms (pytest, TDD) [REPO-ONLY]

**Files:**
- Create: `tools/phase6-strafes/anim/bake.py`
- Create: `tools/phase6-strafes/anim/recipes.json`
- Test: `tools/phase6-strafes/anim/test_bake.py`

**Interfaces:**
- The clip format, the same as the JSON `extract_fier.luau` writes:
  - `{ "name", "loop", "priority", "frames": [ { "t", "poses": { "<Pose>": { "parent", "cf": [12 floats], "w", "es", "ed" } } } ] }`
  - The `cf` floats are CFrame components (x, y, z, R00..R22).
- **R6 joints:** `C0` and `C1` from the standard R6 (in `bake.py` as `R6`). They're the same as the FIER rigs (survey
  §C3).
- **Functions:**

| Function | Returns |
|---|---|
| `fk(frame) -> {"Torso", "Left Leg", "Right Leg", "lf", "rf"}` | world CFrames, plus foot points (the leg CFrame times (0, -1, 0)) |
| `square_chest(clip, keep_yaw=0.0)` | the clip |
| `foot_lock(clip)` | the clip |
| `loop_cut(clip, drop_max, min_len, blend)` | `(clip, a, b)` |
| `split(clip, a, b)` | `{"KneelIn", "Loop", "StandUp"}` |
| `upper_body(clip)` | the clip |
| `scale(clip, k)` | the clip |
| `strip_root(clip, yaw)` | `(clip, carry)`, with `carry = [[t, dx, dz, dyaw], …]` |
| `decimate(clip, fps)` | the clip |
| `seam(clip)` | the largest joint angle in degrees |
| `stance_speed(clip)` | studs/s |
| `stride(clip)` | studs/s, by the spread method |
| `contact_phase(clip)` | a fraction of the cycle |
| `emit_lua(clip, name)` | Lua text |

- [ ] **Step 1: Write the failing tests** `test_bake.py`. Use synthetic clips so no Studio is needed:

```python
import math, numpy as np, pytest
import bake as B

def walk_clip(yaw_deg=0.0, n=31, length=1.0, stride=1.4, drop=0.0, travel=0.0):
    """A synthetic R6 cycle: legs swing +/-, torso yawed by yaw_deg, dropped by drop, translated by travel (forward)."""
    frames = []
    for i in range(n):
        t = length * i / (n - 1)
        ph = 2 * math.pi * i / (n - 1)
        sw = math.atan2(stride / 2, 2) * math.sin(ph)
        torso = B.cf_from(pos=(0, -travel * i / (n - 1), drop), rz=math.radians(yaw_deg))
        frames.append({"t": t, "poses": {
            "HumanoidRootPart": {"parent": None, "cf": B.IDENT, "w": 1},
            "Torso": {"parent": "HumanoidRootPart", "cf": torso, "w": 1},
            "Left Leg": {"parent": "Torso", "cf": B.cf_from(rz=sw), "w": 1},
            "Right Leg": {"parent": "Torso", "cf": B.cf_from(rz=-sw), "w": 1},
            "Head": {"parent": "Torso", "cf": B.cf_from(rz=math.radians(-yaw_deg * 0.25)), "w": 1},
            "Left Arm": {"parent": "Torso", "cf": B.IDENT, "w": 1},
            "Right Arm": {"parent": "Torso", "cf": B.IDENT, "w": 1},
        }})
    return {"name": "synthetic", "loop": False, "priority": "Action", "frames": frames}

def test_square_chest_removes_yaw_and_keeps_leg_world_rotation():
    src = walk_clip(yaw_deg=58)
    out = B.square_chest(src)
    for fs, fo in zip(src["frames"], out["frames"]):
        assert abs(B.yaw_deg(fo["poses"]["Torso"]["cf"])) < 1.0
        for leg in ("Left Leg", "Right Leg"):
            assert B.angle_between(B.fk(fs)[leg], B.fk(fo)[leg]) < 0.5
    assert abs(B.stance_speed(out) - B.stance_speed(src)) <= 0.05 * B.stance_speed(src)
    assert abs(B.lowest_foot(out) - B.lowest_foot(src)) < 0.05
    assert B.seam(out) < 1.0

def test_square_chest_head_faces_forward():
    out = B.square_chest(walk_clip(yaw_deg=58))
    for f in out["frames"]:
        assert abs(B.world_yaw_deg(B.fk_head(f))) < 1.0

def test_loop_cut_is_seamless_and_stays_in_the_band():
    src = walk_clip(drop=-0.95, n=200, length=6.6)
    out, a, b = B.loop_cut(src, drop_max=-0.8, min_len=3.0, blend=0.3)
    assert b - a >= 3.0 - 1e-6
    assert B.seam(out) <= 1.0
    assert all(f["poses"]["Torso"]["cf"][2] <= -0.8 for f in out["frames"])

def test_split_switches_are_frame_identical():
    src = walk_clip(drop=-0.95, n=200, length=6.6)
    _, a, b = B.loop_cut(src, drop_max=-0.8, min_len=3.0, blend=0.3)
    parts = B.split(src, a, b)
    assert B.pose_distance(parts["KneelIn"]["frames"][-1], parts["Loop"]["frames"][0]) < 1e-6
    assert B.pose_distance(parts["Loop"]["frames"][-1], parts["StandUp"]["frames"][0]) < 1e-6

def test_upper_body_keeps_arms_and_head_only():
    out = B.upper_body(walk_clip())
    for f in out["frames"]:
        assert "Left Leg" not in f["poses"] and "Right Leg" not in f["poses"]
        assert f["poses"]["Torso"]["w"] == 0 and f["poses"]["HumanoidRootPart"]["w"] == 0
        assert {"Head", "Left Arm", "Right Arm"} <= set(f["poses"])

def test_scale_multiplies_translations():
    out = B.scale(walk_clip(drop=-1.5), 0.9)
    assert out["frames"][0]["poses"]["Torso"]["cf"][2] == pytest.approx(-1.35)

def test_strip_root_moves_travel_into_carry():
    src = walk_clip(travel=7.24)
    out, carry = B.strip_root(src, yaw=False)
    for f in out["frames"]:
        x, y = f["poses"]["Torso"]["cf"][0], f["poses"]["Torso"]["cf"][1]
        assert math.hypot(x, y) < 0.05
    assert math.hypot(carry[-1][1], carry[-1][2]) == pytest.approx(7.24, abs=0.05)

def test_decimate_keeps_shape():
    src = walk_clip(n=301, length=10)
    out = B.decimate(src, 15)
    assert len(out["frames"]) <= 152
    assert B.max_joint_error(src, out) < 1.0

def test_stride_matches_synthetic():
    assert B.stride(walk_clip(stride=1.4, length=1.0)) == pytest.approx(2 * B.max_spread(walk_clip(stride=1.4)) / 1.0, rel=1e-3)

def test_emit_lua_round_trip_fields():
    txt = B.emit_lua(walk_clip(), "NHG_Test")
    assert 'Instance.new("KeyframeSequence")' in txt and '"NHG_Test"' in txt and "Loop" in txt
```

- [ ] **Step 2: Run it and see it fail.** `cd tools/phase6-strafes/anim && python -m pytest -q`. Expected: an
  ImportError (no `bake`).
- [ ] **Step 3: Write `bake.py`.**
  - **CFrame helpers:** `cf_from`, `IDENT`, `mul`, `inv`, `rot_only`, `yaw_deg` (the rotation about RootJoint-space Z),
    `world_yaw_deg`, `angle_between`.
  - **The R6 table:**
    - RootJoint `C0` = `C1` = `(0,0,0, -1,0,0, 0,0,1, 0,1,0)`;
    - Left Hip `C0 (-1,-1,0, 0,0,-1, 0,1,0, 1,0,0)`, `C1 (-0.5,1,0, 0,0,-1, 0,1,0, 1,0,0)`;
    - Right Hip `C0 (1,-1,0, 0,0,1, 0,1,0, -1,0,0)`, `C1 (0.5,1,0, 0,0,1, 0,1,0, -1,0,0)`;
    - Neck `C0 (0,1,0, -1,0,0, 0,0,1, 0,1,0)`, `C1 (0,-0.5,0, -1,0,0, 0,0,1, 0,1,0)`;
    - the shoulders as standard.
  - **`fk`** composes `C0 · Pose · C1⁻¹` down the hierarchy.
  - **`square_chest`:**
    - `q = yaw(TorsoPose)`, `T' = Rz(-q + keep) · TorsoPose`.
    - For each leg: `L' = rot_only(inv(mul(T', C0hip)) · mul(T, C0hip) · L)`, keeping `L`'s translation.
    - Head: `H' = Rz(+q - keep) · H`, rotation only, about the neck.
  - **`foot_lock`:** for each frame where a foot is the lowest and below `lowest + 0.08`, adjust that leg's pose
    rotation so its horizontal foot velocity equals the clip's stance value. It's a 2-iteration damped least squares
    on the hip angle, ported from `tools/phase3-2260/anim/footlock.luau`.
  - **`loop_cut`:** search every (a, b) pair in the drop band with `b - a ≥ min_len`, minimising `pose_distance` (the
    weighted joint angles plus the torso height). Bake `blend` seconds of slerp from b's tail to a's head.
  - **`split`:** `KneelIn` = `reverse(frames[b:])` retimed by 1.15, with an ease-in on the first 0.2 s; `Loop` =
    `[a, b]`; `StandUp` = `[b, end]`.
  - **`upper_body`:** drop the leg poses, and set the Torso and HumanoidRootPart `w` to 0.
  - **`scale`:** multiply the translation of every `cf`.
  - **`strip_root`:** the per-frame torso X and Y (and, with `yaw`, the torso yaw) become the carry, sampled at 10 Hz
    and zeroed in the pose.
  - **`decimate`:** resample by slerp and lerp.
  - **`emit_lua`:** the same output shape as `tools/tutorial-anim/build.py`'s builders: `Instance.new` per Keyframe
    and Pose, `Weight`, `EasingStyle Linear`, `Loop` and `Priority`, returning the KeyframeSequence (not parented).
  - **Main:** `python bake.py` reads `recipes.json` and `src/*.json`, writes `out/*.lua`, `out/manifest.json` and
    `REPORT.md`, and exits non-zero if any check in §2.2 fails.
- [ ] **Step 4: Write `recipes.json`**, one entry per row of spec §2.3: name, source file, transforms with
  parameters, loop and priority. For example:
  ```json
  {"name": "NHG_StrafeLeft_Square", "src": "Walk_Stand_Anims__Left_Strafe_Walking_R6",
   "do": [["square_chest", {"keep_yaw": 0}], ["foot_lock", {}]], "loop": true, "priority": "Core"}
  ```
- [ ] **Step 5: Run the tests.** Expected: all pass.
- [ ] **Step 6: Commit:** "phase6-strafes: the clip baker (square chest, foot lock, loop cut, upper body, scale, root
  strip) with tests".

---

### Task R4: `Config.Gestures` and `Functions.Gestures` (pure, TDD) [REPO-ONLY to write; the run needs a read-only VM]

**Files:**
- Create: `…/live/ReplicatedStorage.Config.Gestures.luau`
- Create: `…/live/ReplicatedStorage.Functions.Gestures.luau`
- Test: `checks/gs_pure.lua`

**Interfaces:**
- `Functions.Gestures.Pick(Cast, Hook, Ctx, Roll: () -> number) -> string?`
- `Functions.Gestures.Bucket(LegLen: number, Buckets: {number}) -> number` (the nearest bucket)
- `Functions.Gestures.Name(Base: string, Clip, LegLen: number) -> string` (`Base` or `Base_<bucket>`)

- [ ] **Step 1: Write the failing test** `gs_pure.lua`. It uses the same HTTP load pattern as `lc_pure`.
  - **Pick:**
    - Choir at Hangout → a Pray* name;
    - Athletes at Watch → CheerSeated_Upper;
    - Hostile at Argue → Argue_A;
    - Custodian at Post → one of Rummage, Gather or ReachDown;
    - an unknown clique at Fidget → nil;
    - with `Roll` fixed at 0.99 and `Chance` 0.5 → nil;
    - the weighted pick respects the weights over 1,000 rolls, within 5 %.
  - **Bucket:** 0.83 → 80; 0.88 → 90; 1.02 → 100.
  - **Name:** `KneelInspect` at leg 1.62 → `KneelInspect_80`; `Talk` (no buckets) → `Talk`.
  - **Config sanity:**
    - every `Cast` clip name exists in `Clips`;
    - every `Clips` entry has `Len > 0` and a boolean `Loop`;
    - `Caps.MaxActive == 6`.
- [ ] **Step 2: Run it and see it fail** (404).
- [ ] **Step 3: Write `Config.Gestures`.**
  - `Clips`: the 42 rows of spec §2.3. Each has `Id = 0`, `Studio = "NHG_<Name>"`, `Len` (from the survey; R8
    refreshes it from the manifest), `Loop`, `Priority`, and the `Upper`, `Seated`, `Buckets` and `Carry` flags.
  - `Cast`: the spec §4 table as rules.
  - `Caps = { MaxActive = 6; NearRange = 60; Cooldown = 20; StopFar = 80 }`.
  - `GetUp = { Seconds = { 5, 8 }; Dizzy = 0.6 }`.
  - `Infirmary = { VisitAfter = 3600; Stay = { 60, 120 }; Region = "Infirmary" }`.
  - `Watch = { Rest = 0.25; Weight = 0.6; Burst = 3; Others = 4; Practice = 0.3 }`.
  - `PhoneWalk = 0.2`.
  - `PaceClear = { PhonePace = 2.5; PhonePaceWide = 3.5 }`.
- [ ] **Step 4: Write `Functions.Gestures`.**
  - It's pure.
  - `Pick` keeps the rules whose `Hook` matches and every `Who` key equals `Ctx[key]` (a list value means "any of
    them").
  - It rolls `Chance` (default 1), then makes a weighted pick over that rule's `Clips`.
- [ ] **Step 5: Run it.** Expected: `PASS gs_pure`.
- [ ] **Step 6: Commit:** "phase6-strafes: Config.Gestures and Functions.Gestures (pure, tested)".

---

### Task R5: `StudentBrain.Space` and `StudentBrain.Gestures` (new modules) [REPO-ONLY]

**Files:** Create `…/live/ServerScriptService.Services.AI.StudentBrain.Space.luau` and
`…/live/ServerScriptService.Services.AI.StudentBrain.Gestures.luau`.

**Interfaces:**
- **`Space`:** `Space.Clear(S, Dir, Dist) -> boolean` and `Space.Room(S, Dir, Max) -> number`. Move Nudges'
  `filter`, `clear` and `room` here verbatim; Nudges will require them in R10.
- **`Gestures`** (spec §3.1):
  - `Play(S, Name, Opts?)`, `Stop(S, Fade?)`, `Busy(S)`, `Carry(S, Curve)`, `PickFor(S, Hook, Ctx?)`;
  - the `Downed.OnRecovered` hook;
  - `Gestures.Active() -> number`;
  - the Studio-only probe `ServerStorage.NHGestureProbe`, with the commands `Play(StudentIndex, Name)`,
    `Stop(StudentIndex)`, `State(StudentIndex)`, `Active`, `Carry(StudentIndex, Name)` and `GetUp(StudentIndex)`.

- [ ] **Step 1: Write `Space`.** A verbatim move of the Nudges helpers (`filter`, `clear`, `room`), exported. It
  requires `Services.AI.Nav` for `Nav.Floor`.
- [ ] **Step 2: Write `Gestures`.**
  - **`idOf(Name)`:** Nudges' code, reading `Config.Gestures.Clips[Name].Id`, and in Studio
    `ServerStorage.NHGestures[Clips[Name].Studio]`.
  - **`track(S, Name)`** loads into `S.Tracks[Name]` with `Looped = Clip.Loop` and `Priority = Enum.AnimationPriority[Clip.Priority]`.
  - **`Play`:**
    - **Guard:** `Busy`, `S.Agent.Moving`, `S.Reacting` unless `Force`, the seated rules, the active cap unless
      `Force`, the cooldown unless `Force`, and a player within `NearRange` unless `Force`.
    - **Then:** `NpcBuilds.SetPosture(S.Model, false)`, play the track with `Fade`, set `S.Gesture = Name`, and add
      to the active count.
    - **On `Stopped`:** posture back, remove from the active count, `S.Gesture = nil`.
    - **With `Seconds`:** `task.delay` a stop, guarded by a play token.
    - **With `Carry`** and `Clip.Carry`: spawn `Carry`.
  - **`Carry`:** for each curve step, rotate `(dx, dz)` by the start facing. Then, through `Space.Clear`, move
    `Root.CFrame` by the step and apply `dyaw`, on Heartbeat. Stop short of a wall.
  - **The far stop:** a 1 s Heartbeat sweep stops looping gestures with no player within `StopFar`.
  - **`OnRecovered`** (spec §5):
    - find the student through `Host.Students()` (for `NHScheduled`) or the `NpcId` attribute;
    - skip a player character or `workspace.Live` combat AI (it has `Difficulty` or `Weapon`);
    - play Dizzy or InjuredHurt with `Force` for 5-8 s, with `S.Reacting = true` for that time;
    - set `S.SickUntil = os.clock() + Config.Gestures.Infirmary.VisitAfter`.
  - **`Init(Host)`:** called by `StudentBrain.Init` (R10).
- [ ] **Step 3: Check the parse offline.**
  - Each new file must `loadstring` in a VM: write `checks/parse.lua`, which loads every file under `live/` over the
    HTTP bridge with `loadstring` (not run). It's re-run at every install.
  - Expected: `PASS parse <n>`.
- [ ] **Step 4: Commit:** "phase6-strafes: StudentBrain.Space and StudentBrain.Gestures".

---

### Task R6: The builders: KeyframeSequences, infirmary and bleachers (written, not run) [REPO-ONLY]

**Files:** Create `build/gestures_ks.luau`, `build/infirmary.luau`, `build/bleachers.luau` and `dialogue/Nurse.luau`.

- [ ] **Step 1: `gestures_ks.luau`.**
  - It concatenates `anim/out/*.lua`; R8 regenerates it.
  - It creates `ServerStorage.NHGestures` and `ServerStorage.NHPublish.Gestures`, replacing them if present.
  - It parents every built KeyframeSequence into both, the second as a clone.
  - It returns the counts.
  - It refuses to run unless `game.PlaceId == 98950102230473`. **This guard stops a FIER run.**
- [ ] **Step 2: `infirmary.luau`** (spec §6.2).
  - **Guard:** the place id, as in Step 1.
  - **Build `workspace.School.Infirmary`** by cloning `School.R106`'s wall, floor and door parts as templates:
    - resize them to 26 × 24 and move them to the centre (214, 6, 24);
    - the door goes on the north wall, facing the hallway extension;
    - delete the cloned classroom furniture (desks and chalkboard).
  - **Add:** `Zone` (`RoomId = "Infirmary"`), the markers `NpcPost` (`Nurse`), `NHInfirmaryBed1` and `2` (each with
    `SeatHeight` from the `DormBed` prop's measured top), `NHInfirmarySpot1` and `2`, and `Sign` (Signs kit preset
    `Infirmary`).
  - **Place the props** by cloning from `ServerStorage.NHProps`: 2 × `DormBed`, `GlassCabinetTall`, `FilingCabinet`,
    `TeacherChair`, and a desk cloned from R106's `TeacherDesk`.
  - **The region box:** `workspace.Regions.Infirmary` (26 × 14 × 24), centred at y 28 like the room boxes. Copy the
    R106 box's properties.
  - **Idempotent:** it returns `exists` if `School.Infirmary` is already there.
- [ ] **Step 3: `bleachers.luau`** (spec §7.1).
  - **Guard:** the place id.
  - From the S1 survey numbers (rows, heights, venue), create `NHBleacherSeat` parts under
    `workspace.Sports.<Venue>.NHBleacherSeats`:
    - Anchored, CanCollide off, CanQuery off, Transparency 1;
    - `SeatHeight` and `Venue` attributes;
    - tagged `NHBleacherSeat`;
    - facing the court.
  - **Idempotent.**
- [ ] **Step 4: `dialogue/Nurse.luau`.**
  - It builds `ServerStorage.Dialogue.Nurse` in the same shape as an existing tree. Read `ServerStorage.Dialogue.Hale`
    in S3 and copy its structure.
  - **The lines:** a greeting by time of day; the Wounded or low-health line "You don't look good. Sit down before you
    fall down."; a rumour node; "Off you go."
- [ ] **Step 5: Commit:** "phase6-strafes: builders for the gesture clips, the infirmary, the bleachers and the
  Nurse's dialogue".

---

### Task R7: The check scripts [REPO-ONLY]

**Files:** Create `checks/{clipcheck,infirmarycheck,scaleprobe,strafecheck,footcheck,cinegate,gesturecheck,getupcheck,nursecheck,watchcheck}.lua`.

**Each check returns `PASS <name>` or `FAIL` with its reasons.**

- [ ] **Step 1: `clipcheck.lua` (Edit).**
  - All 42 `NHG_*` KeyframeSequences are in both `NHGestures` and `NHPublish.Gestures`.
  - The Loop flags, priorities and lengths match `Config.Gestures` (±0.02 s).
  - The square strafes have torso yaw ≤ 1° on every frame.
  - The upper-body clips have no leg poses, and their Torso weight is 0.
  - Each bucketed clip's deepest point sits within 0.05 of the floor on an FK rig of its bucket's leg length.
- [ ] **Step 2: `infirmarycheck.lua` (Edit).**
  - `School.Infirmary.Zone` exists with `RoomId = "Infirmary"`.
  - `Regions.Infirmary` exists.
  - `NpcPost = "Nurse"` exists.
  - Two beds with `SeatHeight`.
  - No part overlaps R106, BoilerYard or the hallway extension (`GetPartBoundsInBox` on each).
  - A floor raycast at each marker hits `Infirmary.Floor`.
- [ ] **Step 3: `scaleprobe.lua` (Server, Play).**
  - Clone `AI.AI.Rig` into `workspace.NHScaleProbe` (removed at the end) and play `NHG_KneelInspect_100` through
    `RegisterKeyframeSequence`.
  - After 1 s, read the world Y of the lowest leg corner, relative to the floor.
  - Repeat with the rig's legs at 1.6, by its `Height` scaling.
  - **Return the two penetrations.** If they differ in line with the leg ratio, R6 doesn't rescale and the buckets
    stand. If they're equal, it does rescale: drop the buckets (`Buckets = nil`).
- [ ] **Step 4: `strafecheck.lua` (Client, Play).**
  - Set the Studio-only Player attribute `NHStrafeTest = "Lock"`. AnimationController reads it as `Locked` in
    Studio only.
  - `Humanoid:Move(Vector3.new(1, 0, 0), true)` relative to the camera for 3 s, facing −Z.
  - **Check:**
    - the `StrafeRight` track is playing with weight ≥ 0.9;
    - the Walk weight is ≤ 0.1;
    - the root's flat speed is 8.5 ± 0.6 once the server cap lands (wait 0.5 s);
    - over 2 s at 60 Hz, the stance-foot world slip is ≤ 0.6 studs/s;
    - the torso yaw against the root is ≤ 5° (the square bake).
  - **Then diagonal (1, 0, -1):** Walk and Right weights are both 0.5 ± 0.1, and the left-foot contacts are within
    0.05 of each other's phase.
  - **Then back (0, 0, 1):** the Walk track's speed is below 0.
  - **Clean up:** clear the attribute; the Walk weight returns to 1 within 0.3 s; the speed is back over 12 within 1 s.
- [ ] **Step 5: `footcheck.lua` (Client, Play).**
  - Walk forward 3 s at the live speed, then sprint (fire Sprint `Activate`), then crouch (through the existing
    crouch remote).
  - Record each gait's stance-foot slip and the track speed.
  - **PASS** if Walk slip ≤ 25 % of the ground speed (the `CadenceMax` cap) and Sprint and Crouch slip are each
    ≤ 25 %.
  - The report holds the before and after numbers from the S3 dump's copy, for the owner's Q1.
- [ ] **Step 6: `cinegate.lua` (Client, Play).**
  - With `NHStrafeTest = "Lock"`, set each blocker in turn: Player `NHApproach`, `NHCineSeam = "In"`,
    `NHCineHold`, and Character `NHInCine` (set on the client copy; read only by the blend).
  - Move sideways for 0.5 s.
  - **Check:** the strafe weights stay at 0 and Walk is 1.
- [ ] **Step 7: `gesturecheck.lua` (Server, Play, through `NHGestureProbe`).**
  - Play `Talk` on student 1: the track is playing; `State().Gesture == "Talk"`.
  - Walk the student (`Schedules.Borrow` plus `Agent:MoveTo` through the probe): the gesture stops.
  - Play 7 gestures without `Force`: `Active() == 6`.
  - `Carry(1, "Shove_InPlace")`: the root moves 7.2 ± 0.5 studs in the open, or stops short of a wall when one is
    placed 3 studs ahead.
  - With no player within 80, a looping gesture stops within 1.5 s.
- [ ] **Step 8: `getupcheck.lua` (Server, Play).**
  - `Downed.Down(student)`, then `Downed.Recover(student)`.
  - **Check:** within 0.5 s, `Dizzy` or an `InjuredHurt_*` is playing; `S.Reacting` is true; it ends in 5-8 s;
    `S.SickUntil` is set.
  - A player character recovering: no gesture.
- [ ] **Step 9: `nursecheck.lua` (Server, Play).**
  - During Class (`Schedules.PlanForTests("Class")`), the Nurse model stands inside `Infirmary.Zone` within 3 studs
    of `NpcPost`.
  - Her `Post` gesture is one of the Nurse clips within 30 s.
  - The region lookup at her root returns "The Infirmary".
  - A student with `SickUntil` set walks to a bed or spot within 60 s and plays LayingIdle, InjuredIdle or Dizzy.
- [ ] **Step 10: `watchcheck.lua` (Server, Play).**
  - Start a match through the `Sports.Matches` test entry found in S1. If there's none, use `Matches`' public API
    with two dummy teams.
  - Within 30 s, at least one Athlete not playing is seated on an `NHBleacherSeat` (`S.Seated`). `Sitting` is playing
    and `CheerSeated_Upper` is playing at Action2.
  - End the match: they unseat within 5 s.
- [ ] **Step 11: Commit:** "phase6-strafes: check scripts".

---

### Task S1: Surveys (Map spot, bleachers, Matches, remotes) [STUDIO-READ]

- [ ] **Step 1: The Map spot.**
  - In the Map place (read only: `search_game_tree` and `inspect_instance`; never edit), look at what occupies the
    Map's equivalent of NH's (214, 6, 24) lot.
  - Map region boxes match NH's ids. Compare the `BoilerYard` and `R106` box positions in both places to map the
    coordinates.
  - Record what's there. If it's a built room or corridor, switch the infirmary to the StaffRoom fallback (spec
    §6.1) and note it as a ruling.
- [ ] **Step 2: The bleachers** (NH, read-only `execute_luau`).
  - For each `workspace.Sports.*.Stands.Bleacher*` model and `School.Quests.Ring.Bleachers`, record:
    - each step's top Y, depth and width;
    - its facing;
    - whether its parts are CanQuery;
    - the venue.
  - Save the numbers to `build/bleachers_survey.json`, which R6's builder reads.
- [ ] **Step 3: `Sports.Matches`.**
  - Read its source.
  - Record the public state for "a match is live at a venue" (the fields or signals), the teams' players, any score
    event, and any Studio test entry.
  - Write them into the task report. R10's Watch job needs them.
- [ ] **Step 4: The remotes.**
  - Read `ReplicatedStorage.Remotes` (UnPackets and Packets) to decide whether `NHStrafe` is a plain RemoteEvent (the
    `NHCine` pattern) or a packet definition.
  - **Default:** a RemoteEvent `ReplicatedStorage.Remotes.NHStrafe`, created by CombatSpeed's `OnStart`.
- [ ] **Step 5: The dialogue.** Read the structure of `ServerStorage.Dialogue.Hale` (names, classes, attributes)
  into the report for `dialogue/Nurse.luau`.
- [ ] **Step 6: Commit** `build/bleachers_survey.json` and the report notes: "phase6-strafes: S1 surveys".

### Task S2: The FIER extract [STUDIO-READ, FIER only]

- [ ] **Step 1: Write `anim/extract_fier.luau`.**
  - **Read-only:** it only reads properties and returns a JSON string.
  - It takes a list of `{Folder, Clip}` pairs (the 25 sources in spec §2.3), finds
    `workspace[Folder].AnimSaves[Clip]`, and serialises every Keyframe and Pose into the clip format.
  - **The result is capped per call:** about 28 KB of returned text. Call it once per clip; the long clips go in
    chunks of keyframes, with an `offset` and `count`, then are joined.
- [ ] **Step 2: Run it** with `rbxc.py luau "placeId: 107424155290133" Edit @…` per clip, and write
  `anim/src/<Folder>__<Clip>.json`. **Verify that nothing in FIER changed:** the KeyframeSequence count is still 203,
  read before and after.
- [ ] **Step 3: Commit** `anim/extract_fier.luau` and `anim/src/*.json`: "phase6-strafes: FIER source clips (read-only
  extract)".

### Task S3: The NH pre-dump [STUDIO-READ, NH Edit]

- [ ] **Step 1: Dump,** with the place in Edit:

```bash
cd /e/NH-strafes
python -X utf8 -I tools/phase6-strafes/harness/dump.py StarterPlayer.StarterPlayerScripts.Controllers.Character.AnimationController StarterPlayer.StarterPlayerScripts.Controllers.CineActor ServerScriptService.Services.Features.CombatSpeed ServerScriptService.Services.AI.StudentBrain ServerScriptService.Services.AI.StudentBrain.Nudges ServerScriptService.Services.Features.Schedules ServerScriptService.Services.World.Scenes ReplicatedStorage.Config.Scenes ServerScriptService.Services.Social.Npcs ReplicatedStorage.Config.Npcs ServerScriptService.Services.School.HallMonitor ServerScriptService.Services.Social.CliqueFights ServerScriptService.Services.Features.Seats ReplicatedStorage.Config.Regions ServerScriptService.Services.Features.AmbientNpcs
```

  Expected: 15 lines with byte counts. Copy each file into both `pre/` and `live/`.
- [ ] **Step 2: Diff CineActor.** Diff `pre/…CineActor.luau` against `tools/phase6-2350/live/…CineActor.luau` on
  `phase6-tutorial`'s latest. If Studio is behind the branch, use the branch copy as the base and note it. The
  tutorial session owns that file.
- [ ] **Step 3: Commit:** "phase6-strafes: pre-dump".

---

### Task R8: Bake the real clips [REPO-ONLY]

- [ ] **Step 1: Bake.** Run `cd tools/phase6-strafes/anim && python bake.py`. Expected: 42 pieces, every check in
  §2.2 passing, and `REPORT.md` written.
  - If the Praying `loop_cut` can't find 3 s at seam ≤ 1°, report the best window found, and use `min_len = 2.5` as
    the fallback.
- [ ] **Step 2: Refresh the config.** Copy `manifest.json`'s `Len`, `ContactPhase` and `Carry` into
  `Config.Gestures.Clips`. Set the strafes' `ContactPhase` and `Length` in `Config.Locomotion`, and the Walk contact
  phase from an extract of `113454991107499`: **S3's dump step can read that clip through
  `KeyframeSequenceProvider` in the NH VM, read-only.**
- [ ] **Step 3: Regenerate** `build/gestures_ks.luau` from `out/*.lua`.
- [ ] **Step 4: Re-run the checks.** Run `lc_pure` and `gs_pure` again; expect `PASS`.
- [ ] **Step 5: Commit:** "phase6-strafes: baked gesture and strafe clips, manifest".

### Task R9: AnimationController, CineActor and CombatSpeed [REPO-ONLY, on the dump]

**Files:** Modify the three `live/` copies.

- [ ] **Step 1: AnimationController.** Requires `Config.Locomotion` and `Functions.Locomotion`.
  - **`LoadDirectional()`**, called at the end of `SetTracks` and in `OnCharacterAdded`:
    - load `StrafeLeft` and `StrafeRight` from `Assets.Animations.Movement.StrafeLeft/Right`;
    - in Studio with the square ids at 0, load the `NHG_*_Square` KeyframeSequences through
      `RegisterKeyframeSequence`;
    - Core priority, `Looped = true`;
    - stored in `self.Directional`.
  - **The leg length:** `LegLen = Character["Left Leg"].Size.Y`, re-read on the Character's `Height` attribute
    change.
  - **The Running handler:**
    - replace `:SetSpeed(Speed / 30)`, `/ 24` and `/ 10` with
      `:SetSpeed(Loco.Rate(Speed, Cfg.Stride.FastSprint | Sprint | Walk, LegLen, Cfg))`;
    - the crouch's `math.max(Speed, 1) / 7` becomes `Loco.Rate(math.max(Speed, 1), Cfg.Stride.CrouchWalk, LegLen,
      Cfg)`.
  - **The blend:** a `PreAnimation` connection, created on character add and cleaned by `CharacterTrove`. It:
    1. computes the flags: `Locked` from `LockOn.Core.Locked()` (required lazily) or, in Studio, `NHStrafeTest`;
       `MouseLocked` from `UserInputService.MouseBehavior == LockCenter`; `FirstPerson` from the camera-to-head
       distance under `Cfg.FirstPersonDist`;
    2. computes `Blocked` from `Loco.Blocked` over the Character and Player attributes, `StateManager.HasState(Char,
       BUSY)` as `Busy`, and the emote flag;
    3. computes the gait from `self.Pose` (`Walk` or `Walk8` means Walk);
    4. holds the mode for `EnterHold` to enter;
    5. while it's on and moving: computes `a`, the weights and the rates; sets `self.Pose = "Walk8"`; makes the Walk
       track's speed negative when `Back > Walk`; adjusts each track's weight; phase-syncs the secondary track by
       `Loco.Phase`;
    6. on exit: fades the strafes out over `Fade`, puts Walk back to weight 1, sets `self.Pose = "Walk"`, and fires
       `NHStrafe { On = false }`. On entry it fires `{ On = true }`, deduplicated.
  - **`PlayTrack`:** when `self.Pose == "Walk8"` and `NewPose == "Walk"`, it's a no-op. Any other pose stops the
    strafes first.
- [ ] **Step 2: CineActor.** Replace the `STRIDE` table's use. In its `PreAnimation` cadence loop,
  `T:AdjustSpeed(math.clamp(Flat / Per, 0.05, 2.5))` becomes
  `T:AdjustSpeed(Loco.Rate(Flat, Cfg.Stride[T.Animation.Name], LegLen, Cfg))` for the same four names, keeping the
  0.05 floor. Don't add the strafes.
- [ ] **Step 3: CombatSpeed.**
  - In `OnStart`, create `ReplicatedStorage.Remotes.NHStrafe` (a RemoteEvent) if it's missing.
  - `OnServerEvent`, rate-limited to `Cfg.RemoteRate`, sets `Char:SetAttribute("NHStrafing", On == true or nil)`.
  - In `apply()`, after `Want`:
    `if Char:GetAttribute("NHStrafing") and Raw <= Cfg.WalkBandMax and Raw > FLOOR then Want = math.min(Want, Cfg.StrafeSpeed) end`.
  - Connect `Char:GetAttributeChangedSignal("NHStrafing")` to `apply`.
- [ ] **Step 4: Parse.** Run `parse.lua` over `live/`. Expected: `PASS`.
- [ ] **Step 5: Commit:** "phase6-strafes: directional walk blend, stride-matched cadence, strafe speed cap".

### Task R10: The NPC hooks [REPO-ONLY, on the dump]

**Files:** Modify the `live/` copies listed in the file structure.

- [ ] **Step 1: StudentBrain.**
  - In `Init`, call `Gestures.Init(Host)`.
  - **`fidget`:** add `{ "Gesture", w }`, where `w` is the clique's Fidget rules total weight; the branch calls
    `Gestures.Play(S, Gestures.PickFor(S, "Fidget"), { Seconds = math.random(4, 9) })`.
  - **`chat(A, B)`:**
    - choose `Argue` (Hostile or Wary, or rival cliques per `CliqueConfig`) or Speaker and Listener;
    - per line, `Gestures.Play(Speaker, …)` and `Gestures.Play(Listener, …)`;
    - `Gestures.Stop` both at the end.
  - **`fidgetPhone`:** if a pacing clip fits the clear floor (`Space.Clear` four ways), play `PhonePace` or
    `PhonePaceWide`, else `PhoneTalk`. Skip `J.C0 = … * PHONE_POSE` when a gesture plays.
  - **`React.Gawk`:** 25 % `TalkRant`.
  - **`React.Danger`:** `Duck` with `Force` before backing away.
- [ ] **Step 2: Nudges.** Replace `filter`, `clear` and `room` with `Space.*`. No behaviour change.
- [ ] **Step 3: Schedules.**
  - **`PhoneWalk`:** in `Local.WalkTo` during `Passing`, 20 % of walks get the phone Tool and `PhoneTalk_Upper`,
    stopped on arrival.
  - **`Local.Linger`:** play a Hangout pick per clique; the Choir's Pray chain runs KneelIn, then Loop for 8-20 s,
    then StandUp, through `Gestures.Name`'s bucket.
  - **`Local.Mingle`:** within 6 studs of a hallway locker, `Face`, then `Rummage` for 4-10 s.
  - **`Local.Watch`:** the spec §7.2 job, using S1's `Matches` API and the `NHBleacherSeat` tags.
  - **`Local.Infirmary`:** spec §6.3.
  - **The routing:** in `Local.OnSegment` and `Brain` Replan, `S.SickUntil` takes Infirmary first, and a live match
    takes Watch.
- [ ] **Step 4: Scenes.**
  - Add the `anim` op: `Gestures.Play(Cast[St[2]], St[3], { Force = true; Seconds = St[4]; Carry = true })`.
  - In `Config.Scenes`:
    - Argument: `{ "anim", 1, "Argue_A", 6 }` and `{ "anim", 2, "Argue_B", 6 }` after the faces;
    - Locker: replace `{ "fx", 2, "Shove" }` with `{ "anim", 2, "Shove_InPlace" }` and keep the `fx` mood;
    - Notice: `{ "anim", 1, "Point", 4 }`;
    - Dare: `{ "anim", 2, "ReachDown", 3 }`;
    - EastWing: `{ "anim", 1, "Duck" }` before its `say`.
- [ ] **Step 5: The NPCs.**
  - **`Social.Npcs`:** a Post loop per spawned NPC. Every 12-25 s, with a player within 60, play
    `Gestures.PickFor({ Model, Hum, Root, Tracks }, "Post", { Npc = Id })` for 4-9 s.
  - **`Config.Npcs`:** add the Nurse (spec §6.3).
  - **`HallMonitor`:** on entering Confront, `Point` once.
  - **`CliqueFights`:** the scuffle loser gets `Shove_InPlace` or `ShoveSpin_InPlace` with `Carry`.
- [ ] **Step 6: The infirmary support.**
  - **`Seats`:** `Kind` returns `"Bleacher"` for `NHBleacherSeat`-tagged parts; `Height` already reads `SeatHeight`.
  - **`Config.Regions`:** add `Infirmary = { Title = "The Infirmary"; Priority = <R106's> }`.
  - **`AmbientNpcs`:** one infirmary patient on `NHInfirmaryBed1` with `LayingIdle` during school hours. It's played
    through Gestures' `idOf`, so Studio and live behave the same.
- [ ] **Step 7: Parse.** Run `parse.lua`. Expected: `PASS`.
- [ ] **Step 8: Commit:** "phase6-strafes: NPC gesture hooks, the get-up reaction, infirmary routing, the watch job".

---

### Task T1: Backups [STUDIO, after "Studio released (phase6)"]

- [ ] **Step 1: Write the backup script.** Write `build/_backup.lua`, which clones each of the 15 S3 paths into
  `ServerStorage.NH_Backup.Phase6Strafes_pre_<yyyymmdd>`.
- [ ] **Step 2: Run it.** Run it with `edit.py`. Expect 15 clones.
- [ ] **Step 3: Snapshot.** Take a fresh harness snapshot at the first Play (T5).

### Task T2: Install the KeyframeSequences [STUDIO]

- [ ] **Step 1: Build them.** `python -X utf8 -I tools/phase6-strafes/harness/edit.py tools/phase6-strafes/build/gestures_ks.luau`.
  Expected: `NHGestures 42`, `NHPublish.Gestures 42`.
- [ ] **Step 2: Check them.** `edit.py checks/clipcheck.lua`. Expected: `PASS clipcheck`.

### Task T3: Build the infirmary and the bleachers [STUDIO]

- [ ] **Step 1: The infirmary.** `edit.py build/infirmary.luau`. Expected: `built` (or `exists`).
- [ ] **Step 2: The bleachers.** `edit.py build/bleachers.luau`. Expected: the seat counts per venue.
- [ ] **Step 3: The Nurse's dialogue.** `edit.py dialogue/Nurse.luau`.
- [ ] **Step 4: Check.** `edit.py checks/infirmarycheck.lua`. Expected: `PASS`.
- [ ] **Step 5: A screenshot.** `screen_capture` of the room from the hallway door, saved to
  `docs/img/infirmary-greybox.jpg`.

### Task T4: Install the scripts [STUDIO]

- [ ] **Step 1: Install** every `live/` file with `install.py`, in Edit. That's the 4 new modules (Config and
  Functions for Locomotion and Gestures), the 2 new StudentBrain children, and the 15 changed scripts.
- [ ] **Step 2: Create the Animation instances** in Edit:
  - `ReplicatedStorage.Assets.Animations.Movement.StrafeLeft` (`AnimationId rbxassetid://126969213208550`);
  - `…StrafeRight` (`rbxassetid://84541589738848`).

  They switch to the square ids in O1.
- [ ] **Step 3: Run the pure checks** in the Edit VM (now from the installed modules): `lc_pure`, `gs_pure`. Expect
  `PASS`.

### Task T5: The Play rounds [STUDIO]

Every round follows the Global Constraints run order.

- [ ] **Round A, the scale probe:** run `server.py checks/scaleprobe.lua`.
  - If R6 rescales, drop the buckets in `Config.Gestures`, re-bake (R8) and reinstall (T2), then continue.
  - Record the numbers in the report.
- [ ] **Round B, movement:**
  1. `client.py checks/strafecheck.lua`;
  2. `client.py checks/footcheck.lua`;
  3. `client.py checks/cinegate.lua`.

  All three must `PASS`. Record footcheck's numbers for the owner's Q1.
- [ ] **Round C, NPCs:**
  1. `server.py checks/gesturecheck.lua`;
  2. `getupcheck.lua`;
  3. `nursecheck.lua`;
  4. `watchcheck.lua`.

  All must `PASS`.
- [ ] **Round D, the tutorial regressions** (from `tools/phase6-2350/checks/`, run with that harness's runners), in
  the owner's order:
  1. `skipcheck.lua` first;
  2. `approachcheck.lua` (this covers the `STRIDE` change);
  3. then `sneakcheck.lua`, `buscheck.lua` and `holdcheck.lua`;
  4. `bodycheck.lua` and `dipcheck.lua` last.

  Every one must match its result in `tools/phase6-2350/REPORT.md`.
- [ ] **Each round:** restore (it must print `restored`), then stop Play.

### Task T6: Screenshots and release [STUDIO]

- [ ] **Step 1: Capture.** Use Studio `screen_capture` in Play, with test attributes:
  - a lock-on strafe, side view (square chest);
  - the walk cadence before (from the backup's numbers) and after;
  - the Choir praying;
  - the Nurse with a patient;
  - Athletes cheering on the bleachers;
  - a scene shove.

  Save them to `docs/img/strafes-*.jpg` and `docs/img/gestures-*.jpg`.
- [ ] **Step 2: Release.** Restore, stop, then send "Studio released" to the Bell Tower R2 session.

### Task O1: The publish list and the ids [OWNER, then REPO]

- [ ] **Step 1: Hand the list to the owner.**
  - Give them `anim/out/manifest.json` as a table: the 42 `ServerStorage.NHPublish.Gestures.NHG_*`, plus the two
    square strafes.
  - Ask them to publish each with the "Animation" asset type to **group 15981569**, named exactly as in the table.
- [ ] **Step 2: Find the ids.**
  - In the built-in browser, open a create.roblox.com page.
  - Fetch `itemconfiguration.roblox.com/v1/creations/get-assets?assetType=Animation&groupId=15981569`; it's newest
    first.
  - Map the names to ids, newest of each.
  - **Load-check each one** with `KeyframeSequenceProvider:GetKeyframeSequenceAsync`, read-only, in the NH VM: Length
    ±0.02, Loop and Priority as in the manifest.
- [ ] **Step 3: Fill in the ids.**
  - Fill `Config.Gestures.Clips[*].Id`, and `Config.Locomotion.Ids.StrafeLeftSquare` and `StrafeRightSquare`.
  - Point the two `Assets.Animations.Movement.Strafe*` Animation instances at the square ids. That's a [STUDIO] edit
    in the next free slot.
  - Reinstall, then re-run `strafecheck` and `gesturecheck` with the live ids.

### Task R11: Docs and the changelog [REPO-ONLY]

- [ ] **Step 1: `docs/Movement.md`** (new): the strafe modes, the blend, the speed rule, the cadence rule and the
  numbers, the cine gating, and `NHStrafeTest` (Studio).
- [ ] **Step 2: `docs/Infirmary.md`** (new): the room, the Nurse, patients, get-up routing, the dialogue, and the
  owner's open questions (name, healing).
- [ ] **Step 3: `docs/Gameplay-and-NPC-Concepts.md`:** add a "Gestures (phase6)" section with the casting table,
  hooks, caps, the publish status, and the bleachers and Watch.
- [ ] **Step 4: `CHANGELOG.md`:** an entry with the version decided at merge.
  - what's new;
  - the rulings: the owner's answers and the coordinator's defaults;
  - what was verified: every check by name and result, and the tutorial regressions;
  - what was not checked: two players, the phone layout, live ids if they're still pending;
  - the backup folder.
- [ ] **Step 5: The spec's status line:** "Built in <version> (plan `docs/superpowers/plans/2026-11-22-strafes-npc-gestures.md`)".
- [ ] **Step 6: The graph.** Run `python -m graphify update .`, but don't commit `graphify-out/` unless it's tracked
  on this branch.
- [ ] **Step 7: Commit:** "phase6-strafes: docs and changelog".
