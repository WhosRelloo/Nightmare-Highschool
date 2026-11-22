# Tutorial seamless cinematics, slice 1 (2.35.0) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Two playable proofs of the GTA-style seamless tutorial cinematics:
- **The Bus:** free-roam at the stop, a seamless glide into the bus's arrival and boarding, and the title freeze.
- **Sneaking out past Biscuit:** a walk-and-talk beat in which you keep control.

Every camera and body seam is measured, not judged by eye.

**Architecture:** This extends the Cine framework (doc 04, doc 12). Nothing is duplicated.
- **Server:** a cut marked `Seamless` in `Config.Cine` gets a server hold that protects the player without anchoring
  them.
- **Director:** `Controllers.Cine` takes a seamless path:
  - the real character is the actor, driven by a new `Controllers.CineActor` with `TutorialAnim` chains;
  - a glide in from the live camera, built with a new pure `Functions.CineSeam`;
  - a HUD fade, and a blend-out layer onto the Custom camera.
- **Beats:** a segment may be a `beat`, run by a new `Controllers.CineBeat` with pure camera rigs in
  `Functions.CineRigs`.
- **Wickfield:** a new server `World.Tutorial` and client `Controllers.Hometown` make it private per player.

**Tech Stack:**
- **Game:** Roblox Luau in NH Combat Test (placeId 98950102230473). Scripts are installed from a repo mirror through
  the Studio MCP bridge (`E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py`).
- **Tests:**
  - Python `unittest` for `tools/tutorial-anim`;
  - the game VM through `ServerStorage.NHTestBridge`;
  - the client VM through execute_luau.
- **Art:** the Blender FBX in `art/props/fbx/`, imported into Studio by the owner.

**Spec:** `docs/superpowers/specs/2026-11-20-tutorial-seamless-cinematics-design.md` (approved 2026-11-20). Read it with
doc 04, doc 12 §3 and doc 15 §5.

## Global Constraints

- **Place:**
  - Build only in **NH Combat Test**. The Map place (111107083446202) is read-only.
  - Wickfield lives at `Workspace.Hometown`.
  - Its cut sets live in `Workspace.NHCineSets.<Set>` as mark parts, the same as every cut.
- **Backups:** back up every script before its first edit to `ServerStorage.NH_Backup.Phase6_pre_20261120` (a copy
  named `<Service>_<path_with_underscores>`).
- **Mirror:**
  - `tools/phase6-2350/pre/` holds scripts before this plan; `tools/phase6-2350/live/` holds them after. One `.luau`
    per script, named by its dotted path.
  - Studio is changed only by installing from `live/` (`harness/install.py`). Never edit `.Source` in place.
  - The live scripts in Studio are the source of truth. Dump them first (Task 1); the repo's older `tools/phase*`
    copies may be stale.
- **Studio state:** Studio must be in **Edit** mode to install.
- **Test quirk:** execute_luau resets the camera type at the end of every call, so start and observe a cut in the
  **same** client call.
- **Test slot:** slot 2 only. Snapshot it before a state-changing test and restore it exactly afterwards
  (`harness/snapshot.lua`, `restore.py`).
- **UI:** only the UI kit's existing art and styles. Text is never below 20 px.
- **Rigs:** animation stays on the non-bending R6 rig (`r6-animation-cinematics` §0).
- **The spec's numbers, verbatim:**

  | Item | Value |
  |---|---|
  | Walk-to-mark limit | 4 studs |
  | Input ease-out | 0.3 s |
  | Glide in | 0.6-1.0 s |
  | HUD fade | 0.4 s |
  | Idle blend after the re-seat | 0.25 s |
  | Skip dip | 0.25 s |
  | Camera nudge | ±25°, springing back over 0.6 s |
  | Handheld | `calm` 0.08°, `tense` 0.25°, `chase` 0.6° (two octaves, 0.4 and 1.1 Hz) |
  | Focus pull | 0.3 s |
  | Grade ease | 1 s |
  | Reduce Motion | glides become 0.2 s dissolves |
  | Shot-1 lint | more than 90° of turn or 12 studs of travel is flagged |
  | Camera seam check | no frame over 1.5x the glide's median acceleration; the release frame within 0.01 stud and 0.1° |
  | Body seam check | at or under the chain's own p99 |

- **Commits:** `git -c user.name=Rello commit`, ending with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
  Commit only this plan's files; the working tree holds other sessions' changes.

## Spec deltas (implementation choices; recorded in the spec by Task 13)

1. **The clips' folder:** tutorial pieces live in `ReplicatedStorage.NHCineClips.Tutorial`, not
   `ServerStorage.NHTutorialAnims`. The client resolves clips with the director's existing `Ctx.Clip`: published ids
   in `Config.CineClips`, else a preview id registered from the KeyframeSequence. `ServerStorage` isn't visible to
   the client.
2. **The re-seat:** each piece gets a one-keyframe `<Piece>_End` clip: its last pose with the torso's ground offset
   and heading taken out. The re-seat moves the root by the piece's `EndOffset` and switches to `_End` on the same
   frame (the body is unchanged). `_End` then fades out over 0.25 s into the game's idle or walk.
3. **The glide out:** a blend layer on the live Custom camera, not a scripted path to a computed target. Two
   RenderStep binds:
   - before the camera module, the layer puts back the Custom camera's own last CFrame, so the module never reads the
     blend;
   - after it, the layer saves that CFrame and writes the blend.

   The endpoint is whatever the Custom camera renders, so the release can't jump.
4. **Movement on Lead and Side rigs:** the beat swaps the PlayerModule ControlModule's `moveFunction`, so the stick
   is read against the beat's travel direction.
5. **The crouch is the game's own** (owner, 2026-11-20).
   - **Playable sneaking:** it uses `Assets.Animations.Default.Movement.Crouch` and `CrouchWalk`, which the
     AnimationController plays while `Services.Player.Crouch` holds crouch; a beat holds it through the server.
   - **The chains:** they're built from 30 fps samples of those same clips, so a cinematic piece starts and ends on
     the game's exact crouch pose. That replaces the Mixamo `SneakLoop`.

---

## File structure

| Studio path (mirror `tools/phase6-2350/live/<path>.luau`) | Responsibility | New / changed |
|---|---|---|
| `ReplicatedStorage.Cine` | Adds `Cine.cameraAt(cut, t)` and handheld `feel` presets | changed |
| `ReplicatedStorage.Functions.CineSeam` | Pure: glide length, glide keys, shot-1 lint, blend math | new |
| `ReplicatedStorage.Functions.CineRigs` | Pure: Follow / Lead / Side / Frame camera targets, nudge spring | new |
| `ReplicatedStorage.Config.Cine` | `Seamless`, `Looks` (grades), the two new cuts | changed |
| `ReplicatedStorage.Config.TutorialAnim` | The chain plan and player (generated by `tools/tutorial-anim/build.py`) | new |
| `ReplicatedStorage.Cinematics.TutorialBus` | The bus cut (seamless shots) | new |
| `ReplicatedStorage.Cinematics.TutorialSneak` | The garden beat (walk-and-talk) | new |
| `ServerScriptService.Services.World.Cine` | Seamless hold (no anchor), checkpoint on start, `Seamless` in the Play message | changed |
| `ServerScriptService.Services.World.Tutorial` | Enter and leave Wickfield, `NHTutorial`, collision group, checkpoint resume | new |
| `ServerScriptService.Services.Player.Progression` | `Origin = { Checkpoint }` in `Sanitize` | changed |
| `ServerScriptService.Services.Studio.TestBridge` | `TutorialEnter`, `TutorialLeave`, `Origin` | changed |
| `StarterPlayer.StarterPlayerScripts.Controllers.CineActor` | The real character as actor: walk to mark, play chain, re-seat, release | new |
| `StarterPlayer.StarterPlayerScripts.Controllers.CineBeat` | Walk-and-talk runner: rig camera, lines and cues, movement limits, ends | new |
| `StarterPlayer.StarterPlayerScripts.Controllers.Cine` | The seamless path, `beat` segments, the blend-out, the skip dip | changed |
| `StarterPlayer.StarterPlayerScripts.Controllers.Gui.CineUI` | `FadeHud(On, Seconds)` (no bars), `Dip(Seconds)` | changed |
| `StarterPlayer.StarterPlayerScripts.Controllers.Hometown` | Hides other tutorial players; spawns the per-player cast | new |

Tools: `tools/tutorial-anim/build.py` (changed), `tools/tutorial-anim/test_build.py` (new),
`tools/phase6-2350/harness/*` (copied), `tools/phase6-2350/checks/camcheck.lua`, `bodycheck.lua` (new),
`tools/phase6-2350/stage/hometown.lua` (new).

---

### Task 1: Harness, mirror and backups

**Files:**
- Create: `tools/phase6-2350/harness/` (copied from `tools/phase5-2340/harness/`, then re-pointed).
- Create: `tools/phase6-2350/pre/*.luau` and `tools/phase6-2350/live/*.luau` (dumps).

**Interfaces:**
- Produces: `harness/install.py <live files...>`, `harness/dump.py <dotted paths...>`,
  `harness/bridge.py <Command> [args]`, `harness/client.py <file.lua>`, `harness/start_play.lua`,
  `harness/snapshot.lua`, `harness/restore.py`. These are the same contracts as in
  `docs/superpowers/plans/2026-11-17-interactive-cutscenes-framework.md` Task 1.

- [ ] **Step 1: Copy the harness and re-point it**

```bash
cd /e/Nightmare-Highschool/tools
mkdir -p phase6-2350/harness phase6-2350/checks phase6-2350/stage
cp phase5-2340/harness/{install.py,dump.py,bridge.py,client.py,gamevm.py} phase6-2350/harness/
cp phase4-2300/harness/{start_play.lua,snapshot.lua,restore.py} phase6-2350/harness/
grep -l "phase5-2340\|phase4-2300" phase6-2350/harness/* | xargs -r sed -i 's/phase5-2340/phase6-2350/g; s/phase4-2300/phase6-2350/g'
grep -n "ROOT\|HERE" phase6-2350/harness/dump.py phase6-2350/harness/install.py
```

Expected: `ROOT` / `HERE` are derived from `__file__` (no hard-coded phase), so the copies write under `phase6-2350/`.

- [ ] **Step 2: Dump every script this plan edits (Studio in Edit)**

```bash
cd /e/Nightmare-Highschool/tools/phase6-2350/harness
python -X utf8 -I dump.py ReplicatedStorage.Cine ReplicatedStorage.Config.Cine \
  ServerScriptService.Services.World.Cine ServerScriptService.Services.Player.Progression \
  ServerScriptService.Services.Studio.TestBridge StarterPlayer.StarterPlayerScripts.Controllers.Cine \
  StarterPlayer.StarterPlayerScripts.Controllers.Gui.CineUI
```

Expected: seven lines `<path> <bytes> bytes`. The sizes match Studio (on 2026-11-20 they were 49949, 2725, 26924,
25643, 74589, 42660 and 27151).

- [ ] **Step 3: Back them up in Studio** (execute_luau, Edit, NH Combat Test)

```lua
local Root = game.ServerStorage:FindFirstChild("NH_Backup") or Instance.new("Folder", game.ServerStorage)
Root.Name = "NH_Backup"
local F = Root:FindFirstChild("Phase6_pre_20261120") or Instance.new("Folder", Root)
F.Name = "Phase6_pre_20261120"
local Paths = { "ReplicatedStorage.Cine", "ReplicatedStorage.Config.Cine", "ServerScriptService.Services.World.Cine",
	"ServerScriptService.Services.Player.Progression", "ServerScriptService.Services.Studio.TestBridge",
	"StarterPlayer.StarterPlayerScripts.Controllers.Cine", "StarterPlayer.StarterPlayerScripts.Controllers.Gui.CineUI" }
local Out = {}
for _, P in Paths do
	local I = game
	for Part in P:gmatch("[^%.]+") do I = I:FindFirstChild(Part) end
	local Name = P:gsub("%.", "_")
	if not F:FindFirstChild(Name) then local C = I:Clone() C.Name = Name C.Parent = F end
	table.insert(Out, Name)
end
return table.concat(Out, "\n")
```

Expected: seven names.

- [ ] **Step 4: Commit**

```bash
cd /e/Nightmare-Highschool
git add tools/phase6-2350/harness/*.py tools/phase6-2350/harness/*.lua tools/phase6-2350/pre tools/phase6-2350/live
git -c user.name=Rello commit -m "2.35.0 harness: mirror and backups for the seamless tutorial cinematics

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Wickfield's first stage (owner import + placement)

**Files:**
- Create: `tools/phase6-2350/stage/hometown.lua` (arranges imported models and writes the set marks).
- Create: `tools/phase6-2350/checks/assets.lua` (verifies the stage).

**Interfaces:**
- Produces, in Studio:
  - `Workspace.Hometown.BusStop` (model `WFBusStop`);
  - `Workspace.Hometown.BlackBus` (a model with an `AnimationController` and `Animator`, its parts `WFBlackBus_*`, and
    its clips in `AnimSaves`: `BrakeStop`, `EngineIdle`, `DoorsOpen`, `DoorsClose`, `WipersSweep`, `DriverTurn`,
    `PullAway`);
  - `Workspace.Hometown.Garden` (`WFWickHouse`, `WFKennel`, `WFBiscuit`, `WFPicketFence`, `WFPicketGate`).
- Produces the sets, as anchored, invisible, non-colliding 1x1x1 parts:
  - `Workspace.NHCineSets.BusStop`: `Stand`, `BusStart`, `BusStop`, `BusAway`, `Door`, `Board`, `CamWide`,
    `CamLookWide`, `CamDoor`, `CamDriver`;
  - `Workspace.NHCineSets.Garden`: `Start`, `Biscuit`, `FenceZone`, `LightWindow`, `Hide`.
- Produces `Config.CineClips` entries for the bus clips: `BusBrakeStop`, `BusDoorsOpen`, `BusDriverTurn`,
  `BusPullAway`, `BusEngineIdle`.

- [ ] **Step 1 (owner): import the FBX with Studio's 3D Importer** into NH Combat Test, Edit mode:
  1. Import `art/props/fbx/WFBusStop.fbx`, `WFBlackBus.fbx`, `WFWickHouse.fbx`, `WFKennel.fbx`, `WFBiscuit.fbx`,
     `WFPicketFence.fbx` and `WFPicketGate.fbx` with their `art/props/textures/<Name>_{color,normal,rough,metal}.png`
     maps. Use one SurfaceAppearance per piece, as every earlier prop batch did.
  2. For `WFBlackBus` and `WFBiscuit`, tick **Import as rig** so the armature imports as Bones under an
     `AnimationController`. The FBX's baked actions arrive as KeyframeSequences.
  3. Publish the bus's seven clips to the group. Paste the ids into `ReplicatedStorage.Config.CineClips` as
     `BusBrakeStop`, `BusDoorsOpen`, `BusDriverTurn`, `BusPullAway` and `BusEngineIdle`.
  4. Leave the models anywhere in Workspace. Step 2 places them.

- [ ] **Step 2: Write the placement script** `tools/phase6-2350/stage/hometown.lua`. It's idempotent: it moves the
  imported models under `Workspace.Hometown` at fixed offsets from the Hometown origin, far from the school, and
  rewrites both sets.

```lua
-- tools/phase6-2350/stage/hometown.lua (Edit mode). Arranges the imported Wickfield props and writes the cut sets.
local ORIGIN = CFrame.new(4000, 0, 4000) -- Wickfield's corner, away from the school (doc 15 §2)
local H = workspace:FindFirstChild("Hometown") or Instance.new("Folder")
H.Name = "Hometown"
H.Parent = workspace
local function take(name, into, cf)
	local M = workspace:FindFirstChild(name, true)
	if not M then return name .. " MISSING" end
	local Folder = H:FindFirstChild(into) or Instance.new("Folder")
	Folder.Name = into
	Folder.Parent = H
	M.Parent = Folder
	M:PivotTo(ORIGIN * cf)
	return name .. " ok"
end
local Report = {
	-- the stop faces -Y in Blender = -Z in Roblox; the road runs along X in front of it
	take("WFBusStop", "BusStop", CFrame.new(0, 0, 0)),
	take("WFBlackBus", "BlackBus", CFrame.new(-30, 0, -5.6) * CFrame.Angles(0, math.rad(-90), 0)),
	take("WFWickHouse", "Garden", CFrame.new(0, 0, 120)),
	take("WFKennel", "Garden", CFrame.new(14, 0, 96)),
	take("WFBiscuit", "Garden", CFrame.new(14, 0, 93)),
	take("WFPicketFence", "Garden", CFrame.new(0, 0, 80)),
	take("WFPicketGate", "Garden", CFrame.new(12, 0, 80)),
}
local Sets = workspace:FindFirstChild("NHCineSets") or Instance.new("Folder")
Sets.Name = "NHCineSets"
Sets.Parent = workspace
local function set(name, marks)
	local S = Sets:FindFirstChild(name)
	if S then S:Destroy() end
	S = Instance.new("Folder")
	S.Name = name
	S.Parent = Sets
	for mark, cf in marks do
		local P = Instance.new("Part")
		P.Name = mark
		P.Size = Vector3.one
		P.Anchored, P.CanCollide, P.CanQuery, P.CanTouch = true, false, false, false
		P.Transparency = 1
		P.CFrame = ORIGIN * cf
		P.Parent = S
	end
end
set("BusStop", {
	Stand = CFrame.new(1.5, 0.75, -1.6),                                    -- by the kerb, facing the road (-Z)
	BusStart = CFrame.new(-60, 0, -5.6) * CFrame.Angles(0, math.rad(-90), 0),
	BusStop = CFrame.new(-2, 0, -5.6) * CFrame.Angles(0, math.rad(-90), 0),  -- the doors line up with Stand
	BusAway = CFrame.new(90, 0, -5.6) * CFrame.Angles(0, math.rad(-90), 0),
	Door = CFrame.new(1.5, 0.75, -3.4),
	Board = CFrame.new(1.5, 2.9, -6.2),
	CamWide = CFrame.new(-14, 2.2, 6),  CamLookWide = CFrame.new(-6, 4, -5),
	CamDoor = CFrame.new(6, 3.4, -1.0), CamDriver = CFrame.new(0, 8.5, -16),
})
set("Garden", {
	Start = CFrame.new(-6, 0, 104), Biscuit = CFrame.new(14, 0, 93), FenceZone = CFrame.new(12, 0, 81),
	LightWindow = CFrame.new(0, 14, 108), Hide = CFrame.new(4, 0, 92),
})
return table.concat(Report, "\n")
```

- [ ] **Step 3: Write the check** `tools/phase6-2350/checks/assets.lua`

```lua
local Need = {
	"Workspace.Hometown.BusStop.WFBusStop", "Workspace.Hometown.BlackBus.WFBlackBus", "Workspace.Hometown.Garden.WFBiscuit",
	"Workspace.NHCineSets.BusStop.Stand", "Workspace.NHCineSets.BusStop.BusStop", "Workspace.NHCineSets.Garden.Biscuit",
}
local Bad = {}
for _, P in Need do
	local I = game
	for Part in P:gmatch("[^%.]+") do I = I and I:FindFirstChild(Part) end
	if not I then table.insert(Bad, "missing " .. P) end
end
local Bus = workspace.Hometown and workspace.Hometown:FindFirstChild("BlackBus")
Bus = Bus and Bus:FindFirstChild("WFBlackBus")
local Ctl = Bus and Bus:FindFirstChildWhichIsA("AnimationController", true)
if not (Ctl and Ctl:FindFirstChildOfClass("Animator")) then table.insert(Bad, "bus has no AnimationController/Animator") end
local Clips = require(game.ReplicatedStorage.Config.CineClips)
for _, K in { "BusBrakeStop", "BusDoorsOpen", "BusDriverTurn", "BusPullAway", "BusEngineIdle" } do
	if typeof(Clips[K]) ~= "string" or Clips[K] == "" then table.insert(Bad, "no clip id " .. K) end
end
return if #Bad == 0 then "ASSETS OK" else table.concat(Bad, "\n")
```

- [ ] **Step 4: Run them.**

```bash
python -X utf8 -I E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py luau 'placeId: 98950102230473' Edit @tools/phase6-2350/stage/hometown.lua
python -X utf8 -I E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py luau 'placeId: 98950102230473' Edit @tools/phase6-2350/checks/assets.lua
```

Expected: every `take` is `ok`, then `ASSETS OK`.

- [ ] **Step 5: Owner saves the place. Then commit.**

```bash
git add tools/phase6-2350/stage/hometown.lua tools/phase6-2350/checks/assets.lua
git -c user.name=Rello commit -m "2.35.0 stage: Wickfield's bus stop and garden, cut sets BusStop and Garden

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Tutorial clips: end offsets, `_End` poses, the client folder, a resolver-based player

**Files:**
- Modify: `tools/tutorial-anim/build.py`
- Create: `tools/tutorial-anim/test_build.py`
- Create: `tools/phase6-2350/live/ReplicatedStorage.Config.TutorialAnim.luau` (copied from `out/TutorialAnim.luau`).

**Interfaces:**
- Produces:
  - `Config.TutorialAnim.Chains[Chain] = { { Piece, Length, Loop?, Entry?, Exit?, Hold?, EndOffset = { X, Z, Yaw } } }`
  - `TutorialAnim.Play(animator: Animator, chain: string, resolve: (string) -> string?, cues: { [number]: () -> () }?, onSwitch: ((string) -> ())?) -> { [string]: AnimationTrack }`
  - Clips in `ReplicatedStorage.NHCineClips.Tutorial`: `<Piece>` and `<Piece>_End`.
  - Python: `build.end_offset(q_torso, p_torso) -> {"X","Z","Yaw"}` and `build.end_pose(q, p) -> (q, p)`.

- [ ] **Step 1: Write the failing test** `tools/tutorial-anim/test_build.py`

```python
"""python -I -X utf8 -m unittest tools/tutorial-anim/test_build.py  (no RoMixamo needed)"""
import math, os, sys, unittest
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build as B
import mixamo_r6 as MX


def torso_world(q, p, hrp=np.eye(4)):
    c0, c1 = MX.R6M["RootJoint"]
    T = np.eye(4); T[:3, :3] = B.qmat(q); T[:3, 3] = p
    return hrp @ c0 @ T @ MX.inv(c1)


class EndOffset(unittest.TestCase):
    def test_reseat_keeps_the_body_still(self):
        # a torso 1.2 studs sideways, 3.4 forward, half a stud up, turned 70 degrees, tilted 10
        q = B.qmul(B.zq(math.radians(70)), np.array([math.sin(math.radians(5)), 0, 0, math.cos(math.radians(5))]))
        p = np.array([1.2, 3.4, 0.5])
        off = B.end_offset(q, p)
        hrp = np.eye(4)
        hrp_new = hrp @ np.array(MX.M([off["X"], 0, off["Z"], *B.yaw_matrix(math.radians(off["Yaw"])).reshape(-1)]))
        eq, ep = B.end_pose(q, p)
        before = torso_world(q, p, hrp)
        after = torso_world(eq, ep, hrp_new)
        self.assertTrue(np.allclose(before, after, atol=1e-6), (before, after))

    def test_end_pose_keeps_height_and_tilt(self):
        q = B.qmul(B.zq(1.0), np.array([0.1, 0, 0, math.sqrt(1 - 0.01)]))
        p = np.array([2.0, -1.0, 0.7])
        eq, ep = B.end_pose(q, p)
        self.assertAlmostEqual(ep[2], 0.7)
        self.assertAlmostEqual(ep[0], 0.0)
        self.assertAlmostEqual(ep[1], 0.0)
        self.assertAlmostEqual(B.yaw_of(eq), 0.0, places=6)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to see it fail**

Run: `cd /e/Nightmare-Highschool && python -I -X utf8 -m unittest tools/tutorial-anim/test_build.py`
Expected: `AttributeError: module 'build' has no attribute 'end_offset'`

- [ ] **Step 3: Implement** (in `build.py`, after `def seat(...)`)

```python
def yaw_matrix(a):
    """the HumanoidRootPart-space rotation about up (Y) by a radians"""
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def end_offset(q, p):
    """the root move that puts the HumanoidRootPart under the torso's last ground position and heading. Torso pose space
    is X sideways, Y forward/back, Z up; under the R6 RootJoint (C0 rotation (-1,0,0; 0,0,1; 0,1,0)) that is HRP
    (-X, Z, Y). A turn about pose Z is a turn about HRP Y with the same sign."""
    return {"X": round(float(-p[0]), 4), "Z": round(float(p[1]), 4), "Yaw": round(math.degrees(yaw_of(q)), 3)}


def end_pose(q, p):
    """the same torso with its ground offset and heading taken out (tilt and height kept): the _End clip's pose"""
    return tilt(q), np.array([0.0, 0.0, float(p[2])])
```

Then make the test's HRP move match the Luau re-seat: `hrp * CFrame.new(X, 0, Z) * CFrame.Angles(0, rad(Yaw), 0)`.
`MX.M` takes Roblox components, and the test builds it from `yaw_matrix`, so the two agree.

- [ ] **Step 4: Run the test again**

Run: `python -I -X utf8 -m unittest tools/tutorial-anim/test_build.py`
Expected: `OK` (2 tests). If `test_reseat_keeps_the_body_still` fails on rotation only, the yaw sign is flipped: use
`-yaw_of(q)` in `end_offset` and re-run until it passes. The test, not the comment, is the authority.

- [ ] **Step 5: Write `EndOffset` into the plan, generate the `_End` clips and move the folder.** In `build.py`:
  1. Set `FOLDER = "Tutorial"`.
  2. In `write_lua`, build the parent as `game.ReplicatedStorage:FindFirstChild("NHCineClips")`, created if missing,
     then its `Tutorial` folder.
  3. In `main`, after `write_lua(c)` for each piece:

```python
            eq, ep = end_pose(c.q[-1][0], c.p[-1][0])
            endq, endp = c.q[-1].copy(), c.p[-1].copy()
            endq[0], endp[0] = eq, ep
            write_lua(Clip(f"{c.name}_End", np.array([endq, endq]), np.array([endp, endp]), loop=False))
            e["EndOffset"] = end_offset(c.q[-1][0], c.p[-1][0])
```

  Teach `lua_val` to write a dict as `{ X = .., Z = .., Yaw = .. }`.

- [ ] **Step 6: Make `Play` take a resolver and report switches.** In `PLAYER`, change the signature to
  `function TutorialAnim.Play(animator: Animator, chain: string, resolve: (string) -> string?, cues: { [number]: () -> () }?, onSwitch: ((string) -> ())?)`.
  - Load each piece with `a.AnimationId = resolve(st.Piece) or ""`, skipping any piece that resolves to `""`.
  - Call `if onSwitch then onSwitch(st.Piece) end` right after each `t:Play(0)`.
  - Replace the `Ids` table comment with: "resolve: piece name -> animation id (the director passes `Ctx.Clip`);
    onSwitch: called as each piece starts (the body check marks the switches)".

- [ ] **Step 6b: The game's own crouch as source clips** (owner, 2026-11-20: "I already have a crouch animation
  for the main game"). The chains enter and leave the sneak on the game's real crouch, so a cinematic piece hands
  over to gameplay on an identical pose.
  - **The clips:** `ReplicatedStorage.Assets.Animations.Default.Movement.Crouch` (rbxassetid://139672322709288) and
    `CrouchWalk` (rbxassetid://112732055140240). `Controllers.Character.AnimationController` plays them whenever
    `Services.Player.Crouch` holds crouch.

  1. Create `tools/tutorial-anim/extract_game.luau`. It samples a game clip on an R6 dummy at 30 fps; each joint's
     `Motor6D.Transform` is the same pose CFrame a KeyframeSequence's `Pose.CFrame` holds:

```lua
-- tools/tutorial-anim/extract_game.luau (Edit mode): a game animation sampled at 30 fps on a standard R6 dummy -> JSON
local PATH = "__PATH__" -- e.g. Default.Movement.CrouchWalk, under ReplicatedStorage.Assets.Animations
local Players, Http = game:GetService("Players"), game:GetService("HttpService")
local A = game.ReplicatedStorage.Assets.Animations
for Part in PATH:gmatch("[^%.]+") do A = A[Part] end
local D = Players:CreateHumanoidModelFromDescription(Instance.new("HumanoidDescription"), Enum.HumanoidRigType.R6)
D:PivotTo(CFrame.new(0, 600, 0))
D.HumanoidRootPart.Anchored = true
D.Parent = workspace
local An = D.Humanoid:FindFirstChildOfClass("Animator")
local T = An:LoadAnimation(A)
T.Looped = true
T:Play(0)
local T0 = os.clock()
while T.Length == 0 and os.clock() - T0 < 15 do task.wait(0.1) end
local M = { Torso = D.HumanoidRootPart.RootJoint, Head = D.Torso.Neck, ["Left Arm"] = D.Torso["Left Shoulder"],
	["Right Arm"] = D.Torso["Right Shoulder"], ["Left Leg"] = D.Torso["Left Hip"], ["Right Leg"] = D.Torso["Right Hip"] }
local Frames = {}
local N = math.max(1, math.floor(T.Length * 30 + 0.5))
for F = 0, N do
	T.TimePosition = math.min(F / 30, T.Length - 1e-3)
	An:StepAnimations(0)
	local Row = { t = F / 30 }
	for Name, Motor in M do Row[Name] = { Motor.Transform:GetComponents() } end
	table.insert(Frames, Row)
end
D:Destroy()
return Http:JSONEncode({ path = PATH; length = T.Length; frames = Frames })
```

  2. Extract both clips into `tools/tutorial-anim/game/`:

```bash
cd /e/Nightmare-Highschool/tools/tutorial-anim && mkdir -p game
for P in Default.Movement.Crouch Default.Movement.CrouchWalk; do
  sed "s/__PATH__/$P/" extract_game.luau > _x.luau
  python -X utf8 -I E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py luau 'placeId: 98950102230473' Edit @_x.luau > game/${P##*.}.json
done
python -I -X utf8 -c "import json; [print(n, len(json.load(open(f'game/{n}.json'))['frames'])) for n in ('Crouch','CrouchWalk')]"
```

  Expected: two lines with frame counts of at least 2.

  3. In `build.py`, accept a `game` source. Then add a test to `test_build.py`, `test_game_clip_loads`: it loads
     `game/Crouch.json` through `load_game` and asserts the clip has its frame count and unit quaternions. Run it
     first and expect it to fail (`load_game` missing), then make it pass.

```python
def load_game(name):
    """a clip sampled from the game's own animation (extract_game.luau): Motor6D.Transform per joint per frame"""
    d = json.load(open(os.path.join(HERE, "game", f"{name}.json"), encoding="utf-8"))
    return [(f["t"], {j: MX.M(f[j]) for j in JOINTS}) for f in d["frames"]]
```

     In `main`, where clips are converted, add:

```python
        if "game" in c:
            frames = load_game(c["game"])
        else:
            _, d = MX.load_anim(rbxm, c["src"], cat)
            frames = MX.convert(d, inplace=c.get("inplace", False))
        clip = Clip.from_frames(name, frames, c.get("loop", False))
```

  4. In `chains.json`, add the two clips. The game's loops are already seamless, so they skip the build's seam pass:
     add `if clip.loop and "game" not in c: seam_loop(clip)` in `main`.

```json
  "GameCrouch": {"game": "Crouch", "loop": true},
  "GameCrouchWalk": {"game": "CrouchWalk", "loop": true},
```

     Then replace `SneakLoop` with the game's crouch in every chain, so the cinematic pieces and the playable sneak
     look the same:

```json
  "Drainpipe": ["WallClimbDown", "HangDrop", "GameCrouch"],
  "BiscuitStirs": ["GameCrouchWalk", "LookBackNervous", "SneakRight", "GameCrouchWalk"],
  "FenceOver": ["GameCrouchWalk", "ClimbThrough"],
  "HomeAgain": ["PullUpLedge", "GameCrouchWalk", "LieDown", "SleepLoop", "LieLookAround"],
```

     Drop the now-unused `SneakLoop` entry. A chain that ends in `GameCrouch` hands over on the game's own crouch
     pose. The re-seat's `_End` clip then fades out over 0.25 s while `Services.Player.Crouch` (held by the beat)
     plays the same Crouch track underneath, so nothing changes on screen.

- [ ] **Step 7: Rebuild, install the clips and the module, then check.**

```bash
cd /e/Nightmare-Highschool/tools/tutorial-anim
python -I -X utf8 build.py
for f in out/*.lua; do python -X utf8 -I E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py luau 'placeId: 98950102230473' Edit @$f; done | grep -c built
cp out/TutorialAnim.luau ../phase6-2350/live/ReplicatedStorage.Config.TutorialAnim.luau
python -X utf8 -I ../phase6-2350/harness/install.py ../phase6-2350/live/ReplicatedStorage.Config.TutorialAnim.luau
```

Expected:
- `built` once per piece plus once per `_End` clip (twice the piece count; `build.py` prints the piece count);
- `build.py`'s blend audit: every handoff within 1.15x of its sources, or under 45 st/s², including the new
  `GameCrouch` / `GameCrouchWalk` ones;
- install prints `ReplicatedStorage.Config.TutorialAnim <bytes>`;
- `python -I -X utf8 -m unittest test_build.py` still passes.

Remove the old `ServerStorage.NHTutorialAnims` folder in Studio once the new folder is confirmed.

- [ ] **Step 8: Commit**

```bash
cd /e/Nightmare-Highschool
git add tools/tutorial-anim/build.py tools/tutorial-anim/test_build.py tools/tutorial-anim/extract_game.luau tools/tutorial-anim/game tools/tutorial-anim/chains.json tools/tutorial-anim/out tools/tutorial-anim/REPORT.md tools/phase6-2350/live/ReplicatedStorage.Config.TutorialAnim.luau
git -c user.name=Rello commit -m "2.35.0 tutorial clips: end offsets and _End poses for the invisible re-seat, client folder, resolver player

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: `CineSeam` (pure) and the library's `cameraAt` and `feel`

**Files:**
- Create: `tools/phase6-2350/live/ReplicatedStorage.Functions.CineSeam.luau`
- Modify: `tools/phase6-2350/live/ReplicatedStorage.Cine.luau`
- Modify: `tools/phase6-2350/live/ServerScriptService.Services.Studio.TestBridge.luau` (add `CineSeamTest`)

**Interfaces:**
- Produces (`require(ReplicatedStorage.Functions.CineSeam)`):
  - `Seam.Length(FromCF: CFrame, ToCF: CFrame, Reduced: boolean?) -> number`: 0.6-1.0 s by distance and turn; 0.2
    under Reduce Motion.
  - `Seam.Keys(FromCF, FromFov, ToCF, ToFov, Length) -> { {t, pos, look, fov} }`: three keys on a curve (a mid key
    lifted and pulled to the side) for the library's `camera.keys`.
  - `Seam.Lint(FromCF, ToCF) -> string?`: `"[fix] shot 1 turns N deg / travels M studs"` when it's over 90° or 12
    studs.
  - `Seam.Blend(A: CFrame, B: CFrame, E: number) -> CFrame` and `Seam.Ease(U) -> number` (smootherstep).
- Produces (`ReplicatedStorage.Cine`):
  - `Cine.cameraAt(cut, t) -> (CFrame, number)`: the camera a cut shows at time t, without noise.
  - `noise = "calm" | "tense" | "chase"`: the spec's peak amplitudes.

- [ ] **Step 1: Write the failing test** (add to `TestBridge`, beside the other `*Test` commands)

```lua
-- (2.35.0) CineSeam: the glide's length, keys and lint
function Commands.CineSeamTest()
	local Seam = require(ReplicatedStorage.Functions.CineSeam)
	local Fails = {}
	local function check(C, Msg) if not C then table.insert(Fails, Msg) end end
	local A = CFrame.lookAt(Vector3.new(0, 5, 10), Vector3.new(0, 5, 0))
	local Near = A * CFrame.new(1, 0, -1)
	local Far = CFrame.lookAt(Vector3.new(14, 5, -6), Vector3.new(0, 5, 0))
	check(math.abs(Seam.Length(A, A) - 0.6) < 1e-6, "zero move glides 0.6 s")
	check(Seam.Length(A, Far) <= 1.0 and Seam.Length(A, Far) > Seam.Length(A, Near), "longer move glides longer, at most 1.0 s")
	check(math.abs(Seam.Length(A, Far, true) - 0.2) < 1e-6, "Reduce Motion: 0.2 s dissolve")
	local K = Seam.Keys(A, 70, Far, 40, 0.8)
	check(#K == 3 and K[1].t == 0 and math.abs(K[3].t - 0.8) < 1e-6, "three keys over the length")
	check((K[1].pos - A.Position).Magnitude < 1e-4 and (K[3].pos - Far.Position).Magnitude < 1e-4, "keys start and end on the cameras")
	check(K[1].fov == 70 and K[3].fov == 40, "fov carried")
	local Mid = (A.Position + Far.Position) / 2
	check((K[2].pos - Mid).Magnitude > 0.3, "the middle key bends the path")
	check(Seam.Lint(A, Near) == nil, "a short glide passes lint")
	check(Seam.Lint(A, CFrame.lookAt(Vector3.new(0, 5, -30), Vector3.new(0, 5, 0))) ~= nil, "a long glide is flagged")
	check(math.abs(Seam.Ease(0)) < 1e-9 and math.abs(Seam.Ease(1) - 1) < 1e-9 and math.abs(Seam.Ease(0.5) - 0.5) < 1e-9, "smootherstep")
	local Cine = require(ReplicatedStorage.Cine)
	local Cf, Fov = Cine.cameraAt({ shots = { { dur = 2, camera = { cframe = Far, lens = 50 } } } }, 1)
	check((Cf.Position - Far.Position).Magnitude < 1e-4 and math.abs(Fov - Cine.mmToFov(50)) < 1e-4, "cameraAt evaluates a shot")
	return #Fails == 0 and "CineSeamTest OK" or table.concat(Fails, "; ")
end
```

- [ ] **Step 2: Install the TestBridge and run it to see it fail**

```bash
cd /e/Nightmare-Highschool/tools/phase6-2350/harness
python -X utf8 -I install.py ../live/ServerScriptService.Services.Studio.TestBridge.luau
```

Start Play (Studio), then run `python -X utf8 -I bridge.py CineSeamTest`.
Expected: an error, because `ReplicatedStorage.Functions.CineSeam` isn't a valid member. Then stop Play.

- [ ] **Step 3: Implement `CineSeam`** (`live/ReplicatedStorage.Functions.CineSeam.luau`)

```lua
--!strict
--[[
	CineSeam (shared, pure). ReplicatedStorage.Functions.CineSeam   (2.35.0, spec 2026-11-20 §2)
	The glide between the live gameplay camera and a seamless cut's first shot: how long, which path, and the lint that
	keeps shot 1 close to a gameplay angle. No side effects; the director turns Keys into a camera.keys shot.
]]
local Seam = {}

local MIN, MAX, DISSOLVE = 0.6, 1.0, 0.2
local LINT_TURN, LINT_TRAVEL = 90, 12

function Seam.Ease(U: number): number
	U = math.clamp(U, 0, 1)
	return U * U * U * (U * (6 * U - 15) + 10)
end

local function turn(A: CFrame, B: CFrame): number
	return math.deg(math.acos(math.clamp(A.LookVector:Dot(B.LookVector), -1, 1)))
end

function Seam.Length(FromCF: CFrame, ToCF: CFrame, Reduced: boolean?): number
	if Reduced then return DISSOLVE end
	local Travel = (ToCF.Position - FromCF.Position).Magnitude
	local Amount = math.clamp(math.max(Travel / LINT_TRAVEL, turn(FromCF, ToCF) / LINT_TURN), 0, 1)
	return MIN + (MAX - MIN) * Amount
end

function Seam.Keys(FromCF: CFrame, FromFov: number, ToCF: CFrame, ToFov: number, Length: number)
	-- a curved path: the middle key lifts a little and swings out to the side the camera turns from, so the glide
	-- reads as a camera operator's move, not a straight dolly
	local A, B = FromCF.Position, ToCF.Position
	local Mid = (A + B) / 2
	local Span = (B - A).Magnitude
	local Side = FromCF.RightVector * (if FromCF.LookVector:Cross(ToCF.LookVector).Y > 0 then -1 else 1)
	local Bend = math.clamp(Span * 0.18, 0.4, 2.5)
	local MidPos = Mid + Side * Bend + Vector3.new(0, Bend * 0.35, 0)
	local LookA = A + FromCF.LookVector * 10
	local LookB = B + ToCF.LookVector * 10
	return {
		{ t = 0; pos = A; look = LookA; fov = FromFov },
		{ t = Length / 2; pos = MidPos; look = LookA:Lerp(LookB, 0.5); fov = (FromFov + ToFov) / 2 },
		{ t = Length; pos = B; look = LookB; fov = ToFov },
	}
end

function Seam.Lint(FromCF: CFrame, ToCF: CFrame): string?
	local Turn = turn(FromCF, ToCF)
	local Travel = (ToCF.Position - FromCF.Position).Magnitude
	if Turn > LINT_TURN or Travel > LINT_TRAVEL then
		return string.format("[fix] shot 1 turns %d deg / travels %.1f studs from the gameplay camera (max %d / %d)",
			math.floor(Turn + 0.5), Travel, LINT_TURN, LINT_TRAVEL)
	end
	return nil
end

function Seam.Blend(A: CFrame, B: CFrame, E: number): CFrame
	return A:Lerp(B, math.clamp(E, 0, 1))
end

return Seam
```

- [ ] **Step 4: Add `cameraAt` and `feel` to `ReplicatedStorage.Cine`**

In `noisePreset`, before `local p = NOISE[name]`, insert:

```lua
	-- (2.35.0) feel presets: the peak handheld amplitude a seamless cut asks for, on the lens's own preset
	local FEEL = { calm = 0.08, tense = 0.25, chase = 0.6 }
	if FEEL[name] then
		local lens = fov > 45 and "wide" or (fov < 20 and "tele" or "normal")
		local p = NOISE["handheld_" .. lens .. (if name == "chase" then "_strong" else "_mild")]
		local peak = 0
		for _, l in p.x do peak += 0.5 * l[1] end
		return { p = p, gain = FEEL[name] / math.max(peak, 1e-6) }
	end
```

After `local function viewportAspect(cam) ... end` and `evalCamera`, add:

```lua
-- (2.35.0) the camera a cut shows at time t, without handheld noise (the seamless glide aims at shot 1's first frame)
function Cine.cameraAt(cut, t)
	local c = compile(cut)
	local sh = shotAt(c, t)
	local cf, fov = evalCamera(c, sh, t - sh.start, viewportAspect(workspace.CurrentCamera), {}, false)
	return cf, fov
end
```

- [ ] **Step 5: Install and run the test**

```bash
python -X utf8 -I install.py ../live/ReplicatedStorage.Functions.CineSeam.luau ../live/ReplicatedStorage.Cine.luau
```

Start Play, then run `python -X utf8 -I bridge.py CineSeamTest`. Expected: `{"ok":true,"result":"CineSeamTest OK"}`.
Stop Play.

- [ ] **Step 6: Regression:** the old cuts still lint clean. In Edit, run execute_luau
  `local C = require(game.ReplicatedStorage.Cine) return C.analyze(require(game.ReplicatedStorage.Cinematics.Collected).Build ~= nil and "ok" or "?")`.
  That only proves the module still loads. Then run the existing `bridge.py CineJudgeTest` and expect it to pass
  as before.

- [ ] **Step 7: Commit**

```bash
git add tools/phase6-2350/live/ReplicatedStorage.Functions.CineSeam.luau tools/phase6-2350/live/ReplicatedStorage.Cine.luau tools/phase6-2350/live/ServerScriptService.Services.Studio.TestBridge.luau
git -c user.name=Rello commit -m "2.35.0 CineSeam: glide length, curved keys and the shot-1 lint; Cine.cameraAt and handheld feel presets

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Server: seamless hold, checkpoints, Origin, the Tutorial service

**Files:**
- Modify: `live/ServerScriptService.Services.World.Cine.luau`
- Modify: `live/ServerScriptService.Services.Player.Progression.luau`
- Modify: `live/ReplicatedStorage.Config.Cine.luau`
- Create: `live/ServerScriptService.Services.World.Tutorial.luau`
- Modify: `live/ServerScriptService.Services.Studio.TestBridge.luau` (`TutorialEnter`, `TutorialLeave`, `Origin`,
  `SeamlessHoldTest`)

**Interfaces:**
- `Config.Cine.Cuts[Id].Seamless = true`: the server sends `Seamless = true` in `Play`, and holds the player
  without anchoring.
- `Progression.Sanitize` keeps `Origin = { Checkpoint = string? }`, where Checkpoint is `"<CutId>:<Segment>"`, at
  most 60 characters. `Progression.SetCheckpoint(Player, Value: string?)` saves it. `Progression.Get` returns a
  sanitised **copy**, so writes must go through `Local.Save`.
- `Tutorial.Enter(Player) -> boolean`: sets `NHTutorial`, the collision group and the checkpoint resume.
- `Tutorial.Leave(Player)`, `Tutorial.Checkpoint(Player, CutId, Segment)`, `Tutorial.CheckpointOf(Player) -> string?`

- [ ] **Step 1: Write the failing test** (TestBridge)

```lua
-- (2.35.0) a seamless cut holds without anchoring, protects, and writes the checkpoint
function Commands.SeamlessHoldTest(PlayerName: string)
	local Player = Players:FindFirstChild(PlayerName)
	local Cine = CineService()
	local Tut = require(ServerScriptService.Services.World.Tutorial)
	assert(Tut.Enter(Player), "enter")
	local Id = Cine.Play({ Player }, "__SeamlessTest", {})
	task.wait(0.2)
	local C = Player.Character
	local Out = {
		Session = Id ~= nil;
		Anchored = C.HumanoidRootPart.Anchored;
		Protected = C:GetAttribute("Protected") == true;
		InCine = C:GetAttribute("NHInCine") == true;
		Checkpoint = Tut.CheckpointOf(Player);
		Tutorial = Player:GetAttribute("NHTutorial") == true;
		Group = C.HumanoidRootPart.CollisionGroup;
	}
	Cine.EndForTests(Player)
	Tut.Leave(Player)
	Out.AfterTutorial = Player:GetAttribute("NHTutorial")
	return Out
end
```

- [ ] **Step 2: Run it to see it fail.** Install the TestBridge, start Play, run `start_play.lua` on Server, snapshot
  slot 2, then run `bridge.py SeamlessHoldTest $P`.
  Expected: an error, because `Services.World.Tutorial` isn't a valid member.

- [ ] **Step 3: `Config.Cine`**: add to `Cuts`:

```lua
		-- (2.35.0) seamless (spec 2026-11-20): the real character acts, the camera glides in and out, nothing anchors
		__SeamlessTest = { Name = `Seamless test`; Length = 8; Set = `BusStop`; Seamless = true; Replay = true; Hidden = true };
		TutorialBus = { Name = `The Bus`; Length = 34; Set = `BusStop`; Seamless = true; Replay = true };
		TutorialSneak = { Name = `Sneaking Out`; Length = 90; Set = `Garden`; Seamless = true; Replay = true };
```

Also add, at the top level of the returned table:

```lua
	-- (2.35.0) per-scene grades for seamless cuts, eased over 1 s (spec §4.1)
	Looks = {
		Night = { contrast = 0.1; saturation = -0.12; tint = { 214, 228, 240 }; bloom = { intensity = 0.55; size = 40; threshold = 0.92 } };
		Morning = { contrast = 0.06; saturation = 0.04; tint = { 255, 238, 214 }; bloom = { intensity = 0.4; size = 32; threshold = 0.95 } };
		BusStop = { contrast = 0.14; saturation = -0.28; tint = { 206, 220, 232 }; bloom = { intensity = 0.7; size = 48; threshold = 0.9 } };
	};
	GradeEase = 1.0;
```

- [ ] **Step 4: `Progression.Sanitize`**: before `return Out`, add:

```lua
	-- (2.35.0) the tutorial's resume point (Services.World.Tutorial): "<CutId>:<Segment>"
	Out.Origin = {}
	if typeof(Raw.Origin) == `table` and typeof(Raw.Origin.Checkpoint) == `string` then
		Out.Origin.Checkpoint = Raw.Origin.Checkpoint:sub(1, 60)
	end
```

Also add `Origin = {}` to the `Out` initialiser on its first line. Then add, after `Local.Save`:

```lua
-- (2.35.0) the tutorial's resume point; Get returns a sanitised copy, so the write goes through Save
function Shared.SetCheckpoint(Player: Player, Value: string?)
	local P = Shared.Get(Player)
	if not P then return end
	P.Origin = P.Origin or {}
	P.Origin.Checkpoint = if Value then Value:sub(1, 60) else nil
	Local.Save(Player, P)
end
```

- [ ] **Step 5: `World.Cine`: a seamless hold, and the Play message.** Add `Local.HoldSeamless` after `Local.Hold`:

```lua
-- (2.35.0) a seamless cut: the player's own client drives their character (it walks to marks, plays the chain), so
-- nothing anchors and speed isn't zeroed here; they're protected and marked in a cut, and the client locks input
function Local.HoldSeamless(Player: Player): (() -> ())?
	local Character = Player.Character
	if not (Character and Character:FindFirstChildOfClass(`Humanoid`)) then return nil end
	local WasProtected = Character:GetAttribute(`Protected`)
	Character:SetAttribute(`Protected`, true)
	Character:SetAttribute(`NHInCine`, true)
	return function()
		if not Character.Parent then return end
		Character:SetAttribute(`NHInCine`, nil)
		Character:SetAttribute(`Protected`, WasProtected)
	end
end
```

In `Shared.Play`, replace `local Release = Local.Hold(Player)` with:

```lua
		local Release = if Cut.Seamless then Local.HoldSeamless(Player) else Local.Hold(Player)
```

A seamless cut never uses `Arrive`: change the `Arrive` line's condition to
`not Cut.Seamless and not SeenBefore and not Opts.Skippable and Local.SetMark(...)`. In the `Local.Send(... Kind = "Play" ...)`
table, add `Seamless = Cut.Seamless == true;`. After `Local.Mark(Player, CutId, "Started")`, add:

```lua
		if Cut.Seamless then pcall(function() require(script.Parent.Tutorial).Checkpoint(Player, CutId, `Start`) end) end
```

In `Local.OnSeg` (the client reports each segment), add at its end:

```lua
	if Config.Cuts[S.CutId] and Config.Cuts[S.CutId].Seamless and typeof(M.Name) == `string` then
		pcall(function() require(script.Parent.Tutorial).Checkpoint(Player, S.CutId, M.Name) end)
	end
```

Add a test helper next to `SessionsForTests`:

```lua
function Shared.EndForTests(Player: Player)
	local Id = ByPlayer[Player]
	local S = Id and Sessions[Id]
	if S then Local.End(S, Player, `Skipped`) end
end
```

- [ ] **Step 6: Create `World.Tutorial`**

```lua
--!strict
--[[
	Tutorial (server). ServerScriptService.Services.World.Tutorial   (2.35.0, spec 2026-11-20 §4.2-§4.3)
	Who's in Wickfield, privately: the NHTutorial attribute (the client hides other tutorial players), a collision group
	that doesn't collide with itself, and the resume checkpoint saved in Progress.Origin.Checkpoint. This slice only
	enters and leaves; the run's beat order (doc 15 §5) comes with the full tutorial.
]]
local Players = game:GetService(`Players`)
local PhysicsService = game:GetService(`PhysicsService`)
local ServerScriptService = game:GetService(`ServerScriptService`)

local GROUP = `TutorialPlayers`
local Shared = {}
local Inside: { [Player]: RBXScriptConnection } = {}

local function progression() return require(ServerScriptService.Services.Player.Progression) end

local function setGroup(Character: Model?, Group: string)
	if not Character then return end
	for _, D in Character:GetDescendants() do
		if D:IsA(`BasePart`) then D.CollisionGroup = Group end
	end
end

function Shared.Checkpoint(Player: Player, CutId: string, Segment: string)
	progression().SetCheckpoint(Player, `{CutId}:{Segment}`)
end

function Shared.CheckpointOf(Player: Player): string?
	local P = progression().Get(Player)
	return P and P.Origin and P.Origin.Checkpoint or nil
end

function Shared.Enter(Player: Player): boolean
	if Inside[Player] then return true end
	Player:SetAttribute(`NHTutorial`, true)
	setGroup(Player.Character, GROUP)
	Inside[Player] = Player.CharacterAdded:Connect(function(C)
		C:WaitForChild(`HumanoidRootPart`, 5)
		setGroup(C, GROUP)
	end)
	return true
end

function Shared.Leave(Player: Player)
	local Cn = Inside[Player]
	if Cn then Cn:Disconnect() end
	Inside[Player] = nil
	Player:SetAttribute(`NHTutorial`, nil)
	setGroup(Player.Character, `Default`)
end

function Shared.OnStart()
	pcall(function() PhysicsService:RegisterCollisionGroup(GROUP) end)
	PhysicsService:CollisionGroupSetCollidable(GROUP, GROUP, false)
	Players.PlayerRemoving:Connect(function(P) Shared.Leave(P) end)
end

return Shared
```

Add TestBridge commands:

```lua
function Commands.TutorialEnter(PlayerName: string) return require(ServerScriptService.Services.World.Tutorial).Enter(Players:FindFirstChild(PlayerName)) end
function Commands.TutorialLeave(PlayerName: string) require(ServerScriptService.Services.World.Tutorial).Leave(Players:FindFirstChild(PlayerName)) return true end
function Commands.Origin(PlayerName: string) return DeepCopy(require(ServerScriptService.Services.Player.Progression).Get(Players:FindFirstChild(PlayerName)).Origin) end
```

`ReplicatedStorage.ModuleLoader` (run by both `Loader` scripts) requires every module and calls its `OnStart`, so
`World.Tutorial` needs no registration. The same holds for the new client controllers.

Add the crouch hold for beats (Task 8) to `World.Cine`'s `Local.OnMessage` while you're here. It holds the game's
own crouch, so the AnimationController plays your Crouch / CrouchWalk:

```lua
	-- (2.35.0) a walk-and-talk beat holds crouch (spec §3 move.crouch): the server's Crouch service owns the state
	if Message.Kind == `BeatCrouch` and Player:GetAttribute(`NHTutorial`) == true then
		local Crouch = require(ServerScriptService.Services.Player.Crouch)
		if Message.On == true then Crouch.Crouch(Player) else Crouch.Stand(Player) end
		return
	end
```

- [ ] **Step 7: Install and run the test**

```bash
python -X utf8 -I install.py ../live/ReplicatedStorage.Config.Cine.luau ../live/ServerScriptService.Services.World.Cine.luau ../live/ServerScriptService.Services.Player.Progression.luau ../live/ServerScriptService.Services.World.Tutorial.luau ../live/ServerScriptService.Services.Studio.TestBridge.luau
```

Start Play, run `start_play.lua`, snapshot, then run `bridge.py SeamlessHoldTest $P`.
Expected: `Session = true`, `Anchored = false`, `Protected = true`, `InCine = true`, `Checkpoint = "__SeamlessTest:Start"`,
`Tutorial = true`, `Group = "TutorialPlayers"`, and `AfterTutorial = null`. Then run `restore.py` and stop Play.

Also run the existing `bridge.py PlayCut $P '"Collected"' true` and expect a session id. The anchored path is
unchanged.

- [ ] **Step 8: Commit**

```bash
git add tools/phase6-2350/live/ReplicatedStorage.Config.Cine.luau tools/phase6-2350/live/ServerScriptService.Services.World.Cine.luau tools/phase6-2350/live/ServerScriptService.Services.Player.Progression.luau tools/phase6-2350/live/ServerScriptService.Services.World.Tutorial.luau tools/phase6-2350/live/ServerScriptService.Services.Studio.TestBridge.luau
git -c user.name=Rello commit -m "2.35.0 server: seamless hold without anchoring, tutorial checkpoints in Progress.Origin, World.Tutorial

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: `CineActor`: the real character as actor

**Files:**
- Create: `live/StarterPlayer.StarterPlayerScripts.Controllers.CineActor.luau`
- Create: `tools/phase6-2350/checks/bodycheck.lua`

**Interfaces:**
- Consumes: `Config.TutorialAnim` (Task 3), a resolver `(Name) -> string?` (the director's `Ctx.Clip`).
- Produces (`require(Controllers.CineActor)`):
  - `Actor.Begin() -> ()`: eases movement input to zero over 0.3 s, then disables the ControlModule.
  - `Actor.WalkTo(Mark: CFrame, MaxStuds: number?) -> boolean`: walks or turns to the mark if it's within 4 studs;
    returns false if it's further (the cut must be authored relative instead).
  - `Actor.Chain(Chain: string, Resolve, Cues?) -> { [string]: AnimationTrack }`: plays a `TutorialAnim` chain and
    yields until it ends.
  - `Actor.Reseat(Piece: string, Offset: { X, Z, Yaw }, Resolve) -> ()`: the invisible re-seat (spec delta 2).
  - `Actor.Release() -> ()`: re-enables controls; the `_End` track fades out over 0.25 s.

- [ ] **Step 1: Write the failing body check** `tools/phase6-2350/checks/bodycheck.lua` (Client VM). It plays a
  chain on the local character through `CineActor` and measures every switch and the re-seat at 60 fps, with the
  same ratio test as `tools/tutorial-anim/chaincheck.luau` (at or under the chain's own p99, or under 45 st/s²):

```lua
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Actor = require(Players.LocalPlayer.PlayerScripts.Controllers.CineActor)
local TA = require(game.ReplicatedStorage.Config.TutorialAnim)
local Folder = game.ReplicatedStorage.NHCineClips.Tutorial
local function resolve(Name)
	local Seq = Folder:FindFirstChild(Name)
	if not Seq then return nil end
	return Seq:GetAttribute("PreviewId") or tostring(game:GetService("AnimationClipProvider"):RegisterAnimationClip(Seq))
end
local C = Players.LocalPlayer.Character
local Parts = { "Torso", "Head", "Left Arm", "Right Arm", "Left Leg", "Right Leg" }
local Samples, Marks = {}, {}
local Conn = RunService.RenderStepped:Connect(function()
	local P = {}
	for _, N in Parts do table.insert(P, C[N].Position) table.insert(P, (C[N].CFrame * CFrame.new(0, -1, 0)).Position) end
	table.insert(Samples, P)
end)
local Chain = "TheBus"
Actor.Begin()
for _, St in TA.Chains[Chain] do St._at = nil end
local Tracks = Actor.Chain(Chain, resolve, nil, function(Piece) table.insert(Marks, { at = #Samples, name = "switch " .. Piece }) end)
local Last = TA.Chains[Chain][#TA.Chains[Chain]]
table.insert(Marks, { at = #Samples, name = "reseat " .. Last.Piece })
Actor.Reseat(Last.Piece, Last.EndOffset, resolve)
task.wait(0.6)
Actor.Release()
Conn:Disconnect()
local Acc = {}
for i = 3, #Samples do
	local M = 0
	for j = 1, #Samples[i] do
		local A = (Samples[i][j] - 2 * Samples[i - 1][j] + Samples[i - 2][j]).Magnitude * 3600
		if A > M then M = A end
	end
	Acc[i] = M
end
local Near, Inside = {}, {}
for _, Mk in Marks do for i = Mk.at - 4, Mk.at + 4 do Near[i] = true end end
for i = 3, #Samples do if not Near[i] then table.insert(Inside, Acc[i]) end end
table.sort(Inside)
local P99 = Inside[math.max(1, math.floor(#Inside * 0.99))] or 1
local Lines, Pass = {}, true
for _, Mk in Marks do
	local Peak = 0
	for i = Mk.at - 4, Mk.at + 4 do if Acc[i] and Acc[i] > Peak then Peak = Acc[i] end end
	local Ok = Peak <= P99 or Peak <= 45
	Pass = Pass and Ok
	table.insert(Lines, string.format("%s peak %.0f (p99 %.0f) %s", Mk.name, Peak, P99, Ok and "ok" or "POP"))
end
return (Pass and "BODY OK\n" or "BODY POP\n") .. table.concat(Lines, "\n")
```

- [ ] **Step 2: Run it to see it fail.** Start Play, run `start_play.lua`, then `client.py ../checks/bodycheck.lua`.
  Expected: an error, `CineActor is not a valid member`.

- [ ] **Step 3: Implement `CineActor`**

```lua
--!strict
--[[
	CineActor (client). StarterPlayer.StarterPlayerScripts.Controllers.CineActor   (2.35.0, spec 2026-11-20 §2)
	The player's own character as a seamless cut's actor: input eases out, it walks to marks (never a teleport), it plays
	TutorialAnim chains over its normal Animate, and at the end its root is re-seated under the body on the same frame
	the _End pose takes over, so nothing moves; then the game's idle/walk blends back in.
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)

local Player = Players.LocalPlayer
local Shared = {}
local Held = false
local EndTrack: AnimationTrack? = nil
local SpeedWas: number? = nil

local function controls()
	local Ok, C = pcall(function() return require(Player.PlayerScripts:WaitForChild(`PlayerModule`)):GetControls() end)
	return if Ok then C else nil
end
local function parts()
	local C = Player.Character
	local Hum = C and C:FindFirstChildOfClass(`Humanoid`)
	local Root = C and C:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	local Animator = Hum and Hum:FindFirstChildOfClass(`Animator`)
	return C, Hum, Root, Animator
end

function Shared.Begin()
	if Held then return end
	Held = true
	local _, Hum = parts()
	if Hum then
		SpeedWas = Hum.WalkSpeed
		local T0, S0 = os.clock(), Hum.WalkSpeed
		while os.clock() - T0 < 0.3 do                       -- input eases out (spec §2.1): 0.3 s
			Hum.WalkSpeed = S0 * (1 - (os.clock() - T0) / 0.3)
			RunService.Heartbeat:Wait()
		end
		Hum.WalkSpeed = SpeedWas :: number
	end
	local Ctl = controls()
	if Ctl then Ctl:Disable() end
end

function Shared.WalkTo(Mark: CFrame, MaxStuds: number?): boolean
	local _, Hum, Root = parts()
	if not (Hum and Root) then return false end
	local Goal = Mark.Position + Vector3.new(0, Root.Position.Y - Mark.Position.Y, 0)
	local Dist = (Goal - Root.Position) * Vector3.new(1, 0, 1)
	if Dist.Magnitude > (MaxStuds or 4) then return false end
	if Dist.Magnitude > 0.25 then
		Hum:MoveTo(Goal)
		local T0 = os.clock()
		while ((Goal - Root.Position) * Vector3.new(1, 0, 1)).Magnitude > 0.35 and os.clock() - T0 < 3 do RunService.Heartbeat:Wait() end
		Hum:Move(Vector3.zero)
	end
	-- turn to the mark's heading over 0.35 s
	local From = Root.CFrame
	local To = CFrame.new(Root.Position) * (Mark - Mark.Position)
	local T0 = os.clock()
	while os.clock() - T0 < 0.35 do
		local A = (os.clock() - T0) / 0.35
		Root.CFrame = From:Lerp(To, A * A * (3 - 2 * A))
		RunService.Heartbeat:Wait()
	end
	Root.CFrame = To
	return true
end

function Shared.Chain(Chain: string, Resolve: (string) -> string?, Cues: any?, OnSwitch: ((string) -> ())?)
	local _, _, _, Animator = parts()
	assert(Animator, `no Animator`)
	local TA = require(ReplicatedStorage.Config.TutorialAnim)
	return TA.Play(Animator, Chain, Resolve, Cues, OnSwitch)
end

function Shared.Reseat(Piece: string, Offset: { X: number, Z: number, Yaw: number }, Resolve: (string) -> string?)
	local _, _, Root, Animator = parts()
	if not (Root and Animator) then return end
	local A = Instance.new(`Animation`)
	A.AnimationId = Resolve(Piece .. `_End`) or ``
	local T = Animator:LoadAnimation(A)
	T.Priority = Enum.AnimationPriority.Action4
	-- the same frame: the root moves under the body and the _End pose (offset taken out) takes over; nothing moves
	T:Play(0)
	Root.CFrame = Root.CFrame * CFrame.new(Offset.X, 0, Offset.Z) * CFrame.Angles(0, math.rad(Offset.Yaw), 0)
	for _, Other in Animator:GetPlayingAnimationTracks() do
		if Other ~= T and Other.Priority == Enum.AnimationPriority.Action then Other:Stop(0) end
	end
	EndTrack = T
end

function Shared.Release()
	if EndTrack then EndTrack:Stop(0.25) EndTrack = nil end -- the game's idle/walk blends back in (spec §2.2)
	local Ctl = controls()
	if Ctl then Ctl:Enable() end
	Held = false
end

function Shared.OnStart() end

return Shared
```

- [ ] **Step 4: Install, then run the body check**

```bash
python -X utf8 -I install.py ../live/StarterPlayer.StarterPlayerScripts.Controllers.CineActor.luau
```

Start Play, run `start_play.lua`, then `client.py ../checks/bodycheck.lua`.
Expected: `BODY OK`, with every switch and the `reseat` line marked `ok`.

If the re-seat line POPs:
- the Python test passing proves the maths;
- so check that `Reseat` sets `Root.CFrame` on the same frame as `T:Play(0)`;
- then check that `Action4` outranks the chain's `Action` tracks.

- [ ] **Step 5: Commit**

```bash
git add tools/phase6-2350/live/StarterPlayer.StarterPlayerScripts.Controllers.CineActor.luau tools/phase6-2350/checks/bodycheck.lua tools/tutorial-anim/build.py tools/tutorial-anim/out/TutorialAnim.luau tools/phase6-2350/live/ReplicatedStorage.Config.TutorialAnim.luau
git -c user.name=Rello commit -m "2.35.0 CineActor: the real character walks to marks, plays chains and re-seats invisibly (body check passes)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: The director's seamless path (glide in, HUD fade, blend out, skip dip)

**Files:**
- Modify: `live/StarterPlayer.StarterPlayerScripts.Controllers.Cine.luau`
- Modify: `live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.CineUI.luau`
- Create: `tools/phase6-2350/checks/camcheck.lua`
- Create: `live/ReplicatedStorage.Cinematics.__SeamlessTest.luau`

**Interfaces:**
- Consumes: `CineSeam` (Task 4); `Cine.cameraAt` (Task 4); `CineActor` (Task 6); the `Seamless` field of the Play
  message (Task 5).
- Produces:
  - `CineUI.FadeHud(On: boolean, Seconds: number)`: hides or restores the other GUIs and the core GUI with a fade.
    No bars.
  - `CineUI.Dip(Seconds: number)`: black in and out (skip only).
  - Director: `Local.GlideIn(Cut, Shots) -> Shots`: prepends the glide shot.
  - Director: `Local.BlendOut(Cut, FromCF, FromFov, Seconds)`: the two-bind layer (spec delta 3).
  - `Player:SetAttribute("NHCineSeam", "In" | "Cut" | "Out" | nil)`: the checks read the phase.

- [ ] **Step 1: The test cut** `live/ReplicatedStorage.Cinematics.__SeamlessTest.luau`. It's 8 s, with two shots
  staged near the player, and the player's own character as the actor:

```lua
local Def = { Set = `BusStop`; Seamless = true }
function Def.Build(Ctx)
	local Me = Ctx.Self
	return { grade = nil; shots = {
		{ name = `Over shoulder`; dur = 3; subject = Me; noise = `calm`; dof = true;
		  camera = { frame = { size = `MS`; yaw = 160; pitch = 6; lens = 35 }; to = { size = `MCU` }; ease = `inout` } };
		{ name = `Side`; dur = 3; subject = Me; noise = `tense`; dof = true;
		  camera = { frame = { size = `MCU`; yaw = 110; pitch = 2; lens = 50 } } };
		{ name = `Back to you`; dur = 2; subject = Me; noise = `calm`;
		  camera = { frame = { size = `MS`; yaw = 180; pitch = 10; lens = 35 } } };
	} }
end
return Def
```

- [ ] **Step 2: Write the failing camera check** `tools/phase6-2350/checks/camcheck.lua` (Client VM, a single call:
  the execute_luau camera quirk). It plays `__SeamlessTest` through the bridge's server path, records the camera
  every RenderStepped (after the camera), and checks the glide in, the blend out, and the release frame:

```lua
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Player = Players.LocalPlayer
local Cam = workspace.CurrentCamera
local Rows = {}
local Name = "CamCheck_" .. tostring(math.random(1e6))
RunService:BindToRenderStep(Name, Enum.RenderPriority.Last.Value, function()
	table.insert(Rows, { cf = Cam.CFrame; fov = Cam.FieldOfView; phase = Player:GetAttribute("NHCineSeam") or "Play"; t = os.clock() })
end)
game.ReplicatedStorage:WaitForChild("NHCine"):FireServer({ Kind = "Replay"; Id = "__SeamlessTest" })
local T0 = os.clock()
repeat task.wait(0.1) until (Player:GetAttribute("NHCineSeam") == nil and #Rows > 60 and os.clock() - T0 > 3) or os.clock() - T0 > 20
task.wait(1.2)
RunService:UnbindFromRenderStep(Name)
local function acc(i)
	local a, b, c = Rows[i - 2].cf.Position, Rows[i - 1].cf.Position, Rows[i].cf.Position
	return (c - 2 * b + a).Magnitude
end
local Report, Pass = {}, true
for _, Phase in { "In", "Out" } do
	local Idx = {}
	for i = 3, #Rows do if Rows[i].phase == Phase then table.insert(Idx, i) end end
	if #Idx < 5 then Pass = false table.insert(Report, Phase .. ": not seen") continue end
	local A = {}
	for _, i in Idx do table.insert(A, acc(i)) end
	local Sorted = table.clone(A)
	table.sort(Sorted)
	local Median = math.max(Sorted[math.floor(#Sorted / 2) + 1], 1e-5)
	local Max = Sorted[#Sorted]
	-- the frames either side of the phase too: entering and leaving the glide must not jerk
	local Edge = math.max(acc(math.max(3, Idx[1])), acc(math.min(#Rows, Idx[#Idx] + 1)))
	local Ok = Max <= 1.5 * Median * 4 and Edge <= 1.5 * Median * 4
	Pass = Pass and Ok
	table.insert(Report, string.format("%s: %d frames, median %.4f, max %.4f, edges %.4f %s", Phase, #Idx, Median, Max, Edge, Ok and "ok" or "JERK"))
end
-- the release: the first "Play" frame after "Out" equals the last "Out" frame's target (the Custom camera)
local LastOut
for i = #Rows, 1, -1 do if Rows[i].phase == "Out" then LastOut = i break end end
if LastOut and Rows[LastOut + 1] then
	local A, B = Rows[LastOut].cf, Rows[LastOut + 1].cf
	local D = (A.Position - B.Position).Magnitude
	local Ang = math.deg(math.acos(math.clamp(A.LookVector:Dot(B.LookVector), -1, 1)))
	local Move = acc(LastOut + 1)
	local Ok = D <= 0.01 + Move * 2 and Ang <= 0.1 + Move * 20
	Pass = Pass and Ok
	table.insert(Report, string.format("release: %.4f studs, %.3f deg %s", D, Ang, Ok and "ok" or "JUMP"))
end
return (Pass and "CAM OK\n" or "CAM JERK\n") .. table.concat(Report, "\n")
```

The ratio uses `1.5 * median * 4`: an eased glide's peak acceleration is about 4x its median for smootherstep.
Calibrate it on the first passing run, record the measured ratio in `REPORT.md`, and keep the 1.5x headroom on top.

- [ ] **Step 3: Run it to see it fail.** Install the test cut and start Play. Run `start_play.lua`, then
  `bridge.py TutorialEnter $P` and `client.py ../checks/camcheck.lua`.
  Expected: `CAM JERK` with `In: not seen`. Today's path veils to black and doesn't glide.

- [ ] **Step 4: CineUI.** Add after `Shared.Hide`:

```lua
-- (2.35.0) seamless cuts: no bars; the rest of the HUD fades out and back in (spec §2.1 / §4.1)
function Shared.FadeHud(On: boolean, Seconds: number)
	if not Ui then Local.Build() end
	if On then
		Local.HideOthers()
		Ui.Gui.Enabled = true
		Ui.Top.Size = UDim2.fromScale(1, 0)
		Ui.Bottom.Size = UDim2.fromScale(1, 0)
		Ui.Sub.Position = UDim2.new(0.5, 0, 1, -24)
	else
		Local.RestoreOthers()
	end
end

-- (2.35.0) the one black in a seamless cut: skip's jump to the end state (spec §2.3)
function Shared.Dip(Seconds: number)
	if not Ui then Local.Build() end
	Ui.Gui.Enabled = true
	Shared.Veil(1, Seconds / 2)
	task.wait(Seconds / 2)
	Shared.Veil(0, Seconds / 2)
end
```

`HideOthers` disables LayerCollectors at once. For the 0.4 s fade, wrap each hidden ScreenGui's top frames in a
`CanvasGroup` tween where the GUI already uses one (the UI kit's panels do). Otherwise toggle at the midpoint of the
0.4 s, under the veil-free glide.

- [ ] **Step 5: The director.** In `Local.Play`, after `local Def = require(Module)` and the `Cut` table, branch.
  Seamless cuts skip `Gui.Veil(1, 0)`, `HideLive`, `MakeActor` for `Self`, and `Arrive`:

```lua
	Cut.Seamless = Message.Seamless == true
	local Gui = UI()
	if not Cut.Seamless then Gui.Veil(1, 0) end
```

Wrap `Local.HideLive(Cut)` in `if not Cut.Seamless then ... end`. Replace the `Gui.Show(...)` call with:

```lua
	if Cut.Seamless then
		Gui.FadeHud(true, 0.4)
		Gui.SetSkippable(Message.Skippable == true)
		Player:SetAttribute(`NHCineSeam`, `In`)
		task.spawn(function() require(script.Parent.CineActor).Begin() end)
	else
		Gui.Show({ Skippable = Message.Skippable; Group = Cut.Group; Votes = Message.Votes; Need = Message.Need })
		Gui.Veil(1, 0)
	end
```

Wrap `if not Built.keepBlack then Gui.Veil(0, ...) end` with `not Cut.Seamless and`.

In `Local.PlaySegment`, for the start segment of a seamless cut, prepend the glide:

```lua
	local Shots = Local.Strip(Cut, Seg.shots)
	if Cut.Seamless and not Cut.Glided then
		Cut.Glided = true
		Shots = Local.GlideIn(Cut, Shots)
	end
```

Pass `shots = Shots` instead of `shots = Local.Strip(Cut, Seg.shots)`. Add:

```lua
function Local.GlideIn(Cut, Shots)
	local Seam = require(ReplicatedStorage.Functions.CineSeam)
	local Lib = CineLib()
	local Cam = workspace.CurrentCamera
	local FromCF, FromFov = Cam.CFrame, Cam.FieldOfView
	local ToCF, ToFov = Lib.cameraAt({ letterbox = nil; shots = { Shots[1] } }, 0)
	local Lint = Seam.Lint(FromCF, ToCF)
	if Lint then warn(`[Cine] {Cut.Id}: {Lint}`) end
	local Len = Seam.Length(FromCF, ToCF, Cut.Ctx.Reduced)
	local Glide = { name = `GlideIn`; dur = Len; dof = Shots[1].dof; subject = Shots[1].subject;
		camera = { keys = Seam.Keys(FromCF, FromFov, ToCF, ToFov, Len); ease = `inout` } }
	task.delay(Len, function() if Cut.Live then Player:SetAttribute(`NHCineSeam`, `Cut`) end end)
	local Out = { Glide }
	for _, S in Shots do table.insert(Out, S) end
	return Out
end
```

The glide shifts the segment's own events by `Len`. In `PlaySegment`, when the glide was added, add `Len` to every
event's `t` in `Cut.Events` (`for _, E in Cut.Events do E.t = (E.t or 0) + Len end`) before sorting. Keep `Len` on
`Cut.GlideLen` so the prompt's `at` is shifted the same way: `H.time >= Node.prompt.at + (Cut.GlideLen or 0)` on
the start segment.

In `Local.Finish`, for a seamless cut ending `Done`, release with the blend instead of the veil:

```lua
	if Cut.Seamless and How == `Done` then
		local Cam = workspace.CurrentCamera
		local FromCF, FromFov = Cam.CFrame, Cam.FieldOfView
		if Cut.Handle then pcall(function() Cut.Handle:stop() end) end
		Player:SetAttribute(`NHCineSeam`, `Out`)
		require(script.Parent.CineActor).Release()         -- control returns as the glide starts (spec §2.2)
		CameraLease.Release(LEASE)
		Local.BlendOut(Cut, FromCF, FromFov, if Cut.Ctx and Cut.Ctx.Reduced then 0.2 else 0.8)
		Player:SetAttribute(`NHCineSeam`, nil)
		UI().FadeHud(false, 0.4)
	end
```

Put this block before the existing `local Black = ...` line. In the rest of `Finish`:
- skip the veil and `Gui.Hide`/`Gui.Veil` calls when `Cut.Seamless and How == "Done"`;
- a seamless `Skipped` uses `UI().Dip(0.25)` instead of `Veil(1, 0.25)`;
- a seamless `Skipped` also calls `CineActor.Release()`.

Add the blend layer:

```lua
-- (2.35.0) the glide out onto the live Custom camera (spec delta 3): the camera module reads Camera.CFrame back every
-- frame, so before it runs we put back its own last CFrame; after it runs we save that and write the blend. The
-- endpoint is whatever the Custom camera renders: the release can't jump.
function Local.BlendOut(Cut, FromCF: CFrame, FromFov: number, Seconds: number)
	local Seam = require(ReplicatedStorage.Functions.CineSeam)
	local Cam = workspace.CurrentCamera
	local Own: CFrame? = nil
	local OwnFov: number? = nil
	local T0 = os.clock()
	local Pre, Post = `NHCineBlendPre`, `NHCineBlendPost`
	RunService:BindToRenderStep(Pre, Enum.RenderPriority.Camera.Value - 1, function()
		if Own then Cam.CFrame = Own end
		if OwnFov then Cam.FieldOfView = OwnFov end
	end)
	RunService:BindToRenderStep(Post, Enum.RenderPriority.Camera.Value + 1, function()
		Own, OwnFov = Cam.CFrame, Cam.FieldOfView
		local E = Seam.Ease((os.clock() - T0) / Seconds)
		Cam.CFrame = Seam.Blend(FromCF, Own :: CFrame, E)
		Cam.FieldOfView = FromFov + ((OwnFov :: number) - FromFov) * E
	end)
	while os.clock() - T0 < Seconds do RunService.RenderStepped:Wait() end
	RunService:UnbindFromRenderStep(Post)
	RunService.RenderStepped:Wait()                          -- one frame where Pre still restores the module's own CFrame
	RunService:UnbindFromRenderStep(Pre)
end
```

- [ ] **Step 6: Install and run the camera check**

```bash
python -X utf8 -I install.py ../live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.CineUI.luau ../live/StarterPlayer.StarterPlayerScripts.Controllers.Cine.luau ../live/ReplicatedStorage.Cinematics.__SeamlessTest.luau
```

Start Play, run `start_play.lua`, `bridge.py TutorialEnter $P`, then `client.py ../checks/camcheck.lua`.
Expected: `CAM OK`, with the `In`, `Out` and `release` lines all `ok`. Then run `bridge.py CineState $P` and expect no
live session.

- [ ] **Step 7: Regression:** run `bridge.py PlayCut $P '"Collected"' true`. Watch it, or use the old plan's capture,
  and confirm it still veils in and out with bars. That's the clone path, unchanged.

- [ ] **Step 8: Commit**

```bash
git add tools/phase6-2350/live/StarterPlayer.StarterPlayerScripts.Controllers.Cine.luau tools/phase6-2350/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.CineUI.luau tools/phase6-2350/live/ReplicatedStorage.Cinematics.__SeamlessTest.luau tools/phase6-2350/checks/camcheck.lua
git -c user.name=Rello commit -m "2.35.0 director: seamless path (glide in from the live camera, HUD fade, blend out onto Custom, skip dip); camera check passes

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: `CineRigs` (pure) and the `CineBeat` runner

**Files:**
- Create: `live/ReplicatedStorage.Functions.CineRigs.luau`
- Create: `live/StarterPlayer.StarterPlayerScripts.Controllers.CineBeat.luau`
- Modify: `live/StarterPlayer.StarterPlayerScripts.Controllers.Cine.luau` (`beat` segments)
- Modify: `live/ServerScriptService.Services.Studio.TestBridge.luau` (`CineRigsTest`)

**Interfaces:**
- Produces (`CineRigs`):
  - `Rigs.Target(Rig: string, Player: CFrame, Also: Vector3?, Travel: Vector3, Opts) -> (CFrame, number)`: the
    camera's goal and FOV. `Opts = { lens, low, height?, dist? }`.
  - `Rigs.Nudge(State, InputDelta: Vector2, Dt) -> Vector2`: degrees of yaw and pitch, clamped to ±25°, springing
    back over 0.6 s.
  - `Rigs.Damp(Current: CFrame, Goal: CFrame, Dt, Halflife: number) -> CFrame`
- Produces (`CineBeat`): `Beat.Run(Cut, SegName: string, Spec, Ctx) -> string?`, which yields until the beat ends
  and returns the next segment's name.
  - Spec fields: `rig`, `frame = { also, lens, low }`, `move = { speed, sprint, crouch }`, `lines`, `cues`, `prompt`,
    `ends = { on, next }`.
  - Triggers: `start`, `t:<s>`, `enter:<Mark>`, `near:<Actor>:<studs>`, `idle:<s>`, `prompt:<Outcome>`.

- [ ] **Step 1: Write the failing test** (TestBridge)

```lua
function Commands.CineRigsTest()
	local Rigs = require(ReplicatedStorage.Functions.CineRigs)
	local Fails = {}
	local function check(C, M) if not C then table.insert(Fails, M) end end
	local P = CFrame.new(0, 3, 0)                   -- the player at the origin, facing -Z
	local Travel = Vector3.new(0, 0, -1)
	local F, FFov = Rigs.Target("Follow", P, nil, Travel, { lens = 35 })
	check(F.Position.Z > 0 and F.LookVector.Z < 0, "Follow sits behind and looks the way you go")
	local L = Rigs.Target("Lead", P, nil, Travel, { lens = 28 })
	check(L.Position.Z < 0 and L.LookVector.Z > 0 and L.Position.Y < 4.5, "Lead sits ahead, looks back, at hip height")
	local S = Rigs.Target("Side", P, nil, Travel, { lens = 35 })
	check(math.abs(S.Position.X) > 4 and math.abs(S.LookVector.X) > 0.8, "Side runs beside you")
	local Fr = Rigs.Target("Frame", P, Vector3.new(0, 4, -20), Travel, { lens = 35 })
	check(Fr.LookVector:Dot((Vector3.new(0, 4, -20) - Fr.Position).Unit) > 0.9, "Frame looks toward the point of interest")
	local Also = Rigs.Target("Follow", P, Vector3.new(8, 3, -6), Travel, { lens = 35 })
	check(Also.LookVector.X > F.LookVector.X, "Follow drifts toward the second subject")
	local St = { yaw = 0, pitch = 0 }
	local N = Rigs.Nudge(St, Vector2.new(400, 0), 0.016)
	check(math.abs(N.X) <= 25.0001, "nudge clamps to 25 degrees")
	for _ = 1, 60 do N = Rigs.Nudge(St, Vector2.zero, 1 / 60) end
	check(math.abs(N.X) < 2, "nudge springs back within about 0.6 s")
	check(math.abs(FFov - require(ReplicatedStorage.Cine).mmToFov(35)) < 1e-4, "lens to FOV")
	return #Fails == 0 and "CineRigsTest OK" or table.concat(Fails, "; ")
end
```

- [ ] **Step 2: Run it to see it fail.** Install the TestBridge, start Play, run `bridge.py CineRigsTest`.
  Expected: an error, `CineRigs is not a valid member`. Stop Play.

- [ ] **Step 3: Implement `CineRigs`**

```lua
--!strict
--[[
	CineRigs (shared, pure). ReplicatedStorage.Functions.CineRigs   (2.35.0, spec 2026-11-20 §3)
	Walk-and-talk camera goals around a player who keeps moving: Follow (low shoulder, drifts to keep a second subject in
	frame), Lead (ahead at hip height, looking back), Side (a dolly beside you), Frame (eases toward a point of interest).
	The runner damps toward these goals and adds the player's nudge.
]]
local Rigs = {}
local function fov(mm: number): number return math.deg(2 * math.atan(10.125 / mm)) end

function Rigs.Target(Rig: string, Player: CFrame, Also: Vector3?, Travel: Vector3, Opts): (CFrame, number)
	local Flat = Vector3.new(Travel.X, 0, Travel.Z)
	local Fwd = if Flat.Magnitude > 1e-3 then Flat.Unit else Player.LookVector
	local Right = Fwd:Cross(Vector3.yAxis).Unit
	local Head = Player.Position + Vector3.new(0, 1.5, 0)
	local Low = Opts.low == true
	local Lens = Opts.lens or 35
	local Pos, Look
	if Rig == `Lead` then
		Pos = Player.Position + Fwd * (Opts.dist or 9) + Vector3.new(0, Opts.height or 0.6, 0)
		Look = Head - Vector3.new(0, 0.4, 0)
	elseif Rig == `Side` then
		Pos = Player.Position + Right * (Opts.dist or 9) + Fwd * 1.5 + Vector3.new(0, Opts.height or 1.6, 0)
		Look = Head + Fwd * 1.5
	elseif Rig == `Frame` and Also then
		Pos = Player.Position - Fwd * (Opts.dist or 8) + Right * 2.2 + Vector3.new(0, Opts.height or 2.4, 0)
		Look = Head:Lerp(Also, 0.55)
	else -- Follow
		Pos = Player.Position - Fwd * (Opts.dist or 8) + Right * 2.0 + Vector3.new(0, Opts.height or (if Low then 1.2 else 2.6), 0)
		Look = if Also then Head:Lerp(Also, 0.3) else Head + Fwd * 4
	end
	return CFrame.lookAt(Pos, Look), fov(Lens)
end

function Rigs.Nudge(State, InputDelta: Vector2, Dt: number): Vector2
	-- mouse/stick pushes up to 25 degrees; it springs back with a 0.15 s half-life (about 0.6 s to settle)
	State.yaw = math.clamp(State.yaw - InputDelta.X * 0.25, -25, 25)
	State.pitch = math.clamp(State.pitch - InputDelta.Y * 0.25, -25, 25)
	if InputDelta.Magnitude < 1e-3 then
		local K = 0.5 ^ (Dt / 0.15)
		State.yaw *= K
		State.pitch *= K
	end
	return Vector2.new(State.yaw, State.pitch)
end

function Rigs.Damp(Current: CFrame, Goal: CFrame, Dt: number, Halflife: number): CFrame
	return Current:Lerp(Goal, 1 - 0.5 ^ (Dt / math.max(Halflife, 1e-3)))
end

return Rigs
```

- [ ] **Step 4: Run the test.** Install `CineRigs` and the TestBridge, start Play, run `bridge.py CineRigsTest`.
  Expected: `CineRigsTest OK`.

- [ ] **Step 5: Implement `CineBeat`**

```lua
--!strict
--[[
	CineBeat (client). StarterPlayer.StarterPlayerScripts.Controllers.CineBeat   (2.35.0, spec 2026-11-20 §3)
	A walk-and-talk segment: the player keeps moving; the camera follows a CineRigs rig (nudgeable), lines and cues fire
	on time / place / proximity / idle / a prompt's result, and the beat ends on its trigger, returning the next segment.
	On Lead and Side rigs the stick is read against the beat's travel direction (spec delta 4).
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local UserInputService = game:GetService(`UserInputService`)

local Player = Players.LocalPlayer
local Shared = {}

local function controls()
	local Ok, C = pcall(function() return require(Player.PlayerScripts:WaitForChild(`PlayerModule`)):GetControls() end)
	return if Ok then C else nil
end

local function trigger(On: string, Ctx, Clock: number, Root: BasePart, Idle: number, Results): boolean
	if On == `start` then return Clock >= 0 end
	local Kind, A, B = On:match(`^(%a+):([^:]+):?(.*)$`)
	if Kind == `t` then return Clock >= tonumber(A) :: number end
	if Kind == `idle` then return Idle >= tonumber(A) :: number end
	if Kind == `enter` then
		local M = Ctx.Mark(A)
		return M ~= nil and ((M.Position - Root.Position) * Vector3.new(1, 0, 1)).Magnitude <= math.max(M.Size.X, M.Size.Z, 4)
	end
	if Kind == `near` then
		local Who = Ctx.Actor(A) or (Ctx.Mark(A) and Ctx.Mark(A))
		local Pos = if Who and Who:IsA(`Model`) then Who:GetPivot().Position elseif Who then (Who :: BasePart).Position else nil
		return Pos ~= nil and (Pos - Root.Position).Magnitude <= (tonumber(B) or 8)
	end
	if Kind == `prompt` then return Results[A] == true end
	return false
end

function Shared.Run(Cut, SegName: string, Spec, Ctx): string?
	local Rigs = require(ReplicatedStorage.Functions.CineRigs)
	local UI = require(script.Parent.Gui.CineUI)
	local C = Player.Character
	local Hum = C and C:FindFirstChildOfClass(`Humanoid`)
	local Root = C and C:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	if not (Hum and Root) then return Spec.ends and Spec.ends.next end
	local Cam = workspace.CurrentCamera
	local Move = Spec.move or {}
	local SpeedWas = Hum.WalkSpeed
	Hum.WalkSpeed = SpeedWas * (Move.speed or 1)
	Player:SetAttribute(`NHBeatNoSprint`, if Move.sprint == false then true else nil)  -- Movement.Sprint reads this
	local Remote = ReplicatedStorage:WaitForChild(`NHCine`)
	if Move.crouch then Remote:FireServer({ Kind = `BeatCrouch`; On = true }) end       -- the game's own crouch (spec delta 5)
	local Travel = Root.CFrame.LookVector
	local Ctl = controls()
	local MoveWas = Ctl and (Ctl :: any).moveFunction
	if Ctl and (Spec.rig == `Lead` or Spec.rig == `Side`) and typeof(MoveWas) == `function` then
		(Ctl :: any).moveFunction = function(P, Vec: Vector3, _Relative: boolean)
			-- the stick against the beat's travel direction, never the camera's
			local Fwd = Vector3.new(Travel.X, 0, Travel.Z).Unit
			local Right = Fwd:Cross(Vector3.yAxis)
			MoveWas(P, Right * Vec.X + Fwd * -Vec.Z, false)
		end
	end
	local Fired, Results, Clock, Idle = {}, {}, 0, 0
	local NudgeState = { yaw = 0, pitch = 0 }
	local Goal, GoalFov = Rigs.Target(Spec.rig or `Follow`, Root.CFrame, nil, Travel, Spec.frame or {})
	local Current = Cam.CFrame
	local Next: string? = nil
	local Done = false
	local Conn = RunService:BindToRenderStep(`NHBeat`, Enum.RenderPriority.Camera.Value + 1, function(Dt)
		Clock += Dt
		local Vel = Root.AssemblyLinearVelocity * Vector3.new(1, 0, 1)
		if Vel.Magnitude > 2 then Travel = Travel:Lerp(Vel.Unit, math.min(1, Dt * 2)) Idle = 0 else Idle += Dt end
		local Also = nil
		if Spec.frame and Spec.frame.also then
			local A = Ctx.Actor(Spec.frame.also) or Ctx.Mark(Spec.frame.also)
			Also = if A and A:IsA(`Model`) then A:GetPivot().Position elseif A then (A :: BasePart).Position else nil
		end
		Goal, GoalFov = Rigs.Target(Spec.rig or `Follow`, Root.CFrame, Also, Travel, Spec.frame or {})
		local N = Rigs.Nudge(NudgeState, UserInputService:GetMouseDelta(), Dt)
		Current = Rigs.Damp(Current, Goal, Dt, 0.18)
		Cam.CFrame = Current * CFrame.Angles(math.rad(N.Y), math.rad(N.X), 0)
		Cam.FieldOfView += (GoalFov - Cam.FieldOfView) * math.min(1, Dt * 4)
		for I, L in Spec.lines or {} do
			if not Fired[`L` .. I] and trigger(L.on, Ctx, Clock, Root, Idle, Results) then
				Fired[`L` .. I] = true
				UI.Subtitle(L.who, L.text, L.secs or math.max(2, #L.text / 14))
			end
		end
		for I, Q in Spec.cues or {} do
			if not Fired[`C` .. I] and trigger(Q.on, Ctx, Clock, Root, Idle, Results) then
				Fired[`C` .. I] = true
				local Fn = Cut.Built.cues and Cut.Built.cues[Q.run]
				if Fn then task.spawn(Fn, Ctx) end
			end
		end
		if Spec.ends and not Done and trigger(Spec.ends.on, Ctx, Clock, Root, Idle, Results) then
			Done = true
			Next = Spec.ends.next
		end
	end)
	while not Done and Cut.Live do RunService.RenderStepped:Wait() end
	RunService:UnbindFromRenderStep(`NHBeat`)
	Hum.WalkSpeed = SpeedWas
	Player:SetAttribute(`NHBeatNoSprint`, nil)
	if Move.crouch then Remote:FireServer({ Kind = `BeatCrouch`; On = false }) end
	if Ctl and MoveWas then (Ctl :: any).moveFunction = MoveWas end
	return Next
end

function Shared.OnStart() end

return Shared
```

**Sprint:**
1. Dump `StarterPlayer.StarterPlayerScripts.Controllers.Character.InputController.Movement.Sprint`; it's not in Task
   1's list, so back it up the same way.
2. At the top of its sprint-start handler, the function bound to the Sprint input, add
   `if game:GetService("Players").LocalPlayer:GetAttribute("NHBeatNoSprint") then return end`.
3. Put it in this task's install.

**Crouch:** it's the game's own crouch (spec delta 5). The server's `Services.Player.Crouch` (`Crouch`, `Stand`,
`IsCrouched`; it sets the `Crouch` attribute) holds it through the `BeatCrouch` message added in Task 5, and the
AnimationController plays `Default.Movement.Crouch` / `CrouchWalk`.

The beat camera is Scriptable under the Cine lease, but controls stay **enabled**: the beat never calls
`CineActor.Begin`.

- [ ] **Step 6: The director runs `beat` segments.** In `Local.PlaySegment`, before building shots, add:

```lua
	if Seg.beat then
		Cut.Seg = Name
		Player:SetAttribute(`NHCinePath`, (Cut.Path or ``) .. (if Cut.Path then `>` else ``) .. Name)
		if Cut.Interactive then send({ Kind = `Seg`; Session = Cut.Session; Name = Name; At = workspace:GetServerTimeNow() }) end
		task.spawn(function()
			local Next = require(script.Parent.CineBeat).Run(Cut, Name, Seg.beat, Cut.Ctx)
			if Cut.Live then
				if Next then Local.PlaySegment(Cut, Next) else task.spawn(Local.EndGraph, Cut) end
			end
		end)
		return
	end
```

Also send `Seg` for non-interactive seamless cuts, so the server's checkpoint hook (Task 5) sees every segment:
change the existing `if Cut.Interactive then send({ Kind = "Seg" ...` to `if Cut.Interactive or Cut.Seamless then`.
In `World.Cine`'s `Local.OnSeg`, accept `Seg` for seamless sessions without a graph: return early after the
checkpoint write when `S.Graph == nil`.

- [ ] **Step 7: Install, and smoke-test a beat.** Add a second segment to `__SeamlessTest`:
  `Walk = { beat = { rig = "Follow"; lines = { { on = "start"; who = "You"; text = "Test." } }; ends = { on = "t:4" } } }`,
  with `start = "Main"` and `Main = { shots = ...; next = "Walk" }`. Use the `segments` form, as in doc 12 §3.

  Play, then run `TutorialEnter` and `camcheck.lua`. Expected:
  - `CAM OK`;
  - while the beat runs, `Player:GetAttribute("NHCinePath")` ends with `>Walk`;
  - pressing W in the client during the beat moves the character (controls on).

- [ ] **Step 8: Commit**

```bash
git add tools/phase6-2350/live/ReplicatedStorage.Functions.CineRigs.luau tools/phase6-2350/live/StarterPlayer.StarterPlayerScripts.Controllers.CineBeat.luau tools/phase6-2350/live/StarterPlayer.StarterPlayerScripts.Controllers.Cine.luau tools/phase6-2350/live/ServerScriptService.Services.Studio.TestBridge.luau tools/phase6-2350/live/ServerScriptService.Services.World.Cine.luau tools/phase6-2350/live/ReplicatedStorage.Cinematics.__SeamlessTest.luau
git -c user.name=Rello commit -m "2.35.0 walk-and-talk: CineRigs camera goals and the CineBeat runner; the director plays beat segments

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Private Wickfield (`Controllers.Hometown`)

**Files:**
- Create: `live/StarterPlayer.StarterPlayerScripts.Controllers.Hometown.luau`

**Interfaces:**
- Consumes: `NHTutorial` (Task 5).
- Produces:
  - `Hometown.Hidden(Other: Player) -> boolean`.
  - `Hometown.Cast(Name: string) -> Model?`: a per-player client copy of a Wickfield NPC model from
    `Workspace.Hometown.<Folder>`, under `Workspace.NHHometownCast`. The server copy is hidden locally.

- [ ] **Step 1: Implement**

```lua
--!strict
--[[
	Hometown (client). StarterPlayer.StarterPlayerScripts.Controllers.Hometown   (2.35.0, spec 2026-11-20 §4.2)
	While you're in Wickfield (NHTutorial), every other player in it is hidden on your screen (parts, decals, name tag,
	sounds), and the cast (Biscuit, the parents, the watchman, the driver) is your own local copy, so each player's scenes
	and NPC states are private.
]]
local Players = game:GetService(`Players`)
local RunService = game:GetService(`RunService`)

local Player = Players.LocalPlayer
local Shared = {}
local Cast: { [string]: Model } = {}

local function hideCharacter(C: Model, Hide: boolean)
	for _, D in C:GetDescendants() do
		if D:IsA(`BasePart`) or D:IsA(`Decal`) then (D :: any).LocalTransparencyModifier = if Hide then 1 else 0 end
		if D:IsA(`Sound`) then D.Volume = if Hide then 0 else (D:GetAttribute(`NHVol`) or D.Volume) end
		if D:IsA(`BillboardGui`) then D.Enabled = not Hide end
	end
	local Hum = C:FindFirstChildOfClass(`Humanoid`)
	if Hum then Hum.DisplayDistanceType = if Hide then Enum.HumanoidDisplayDistanceType.None else Enum.HumanoidDisplayDistanceType.Viewer end
end

function Shared.Hidden(Other: Player): boolean
	return Other ~= Player and Player:GetAttribute(`NHTutorial`) == true and Other:GetAttribute(`NHTutorial`) == true
end

function Shared.Cast(Name: string): Model?
	if Cast[Name] and Cast[Name].Parent then return Cast[Name] end
	local H = workspace:FindFirstChild(`Hometown`)
	local Src = H and H:FindFirstChild(Name, true)
	if not (Src and Src:IsA(`Model`)) then return nil end
	local Folder = workspace:FindFirstChild(`NHHometownCast`) or Instance.new(`Folder`)
	Folder.Name = `NHHometownCast`
	Folder.Parent = workspace
	local M = Src:Clone()
	M.Parent = Folder
	hideCharacter(Src, true)
	Cast[Name] = M
	return M
end

function Shared.OnStart()
	RunService.Heartbeat:Connect(function()
		if Player:GetAttribute(`NHTutorial`) ~= true then return end
		for _, Other in Players:GetPlayers() do
			local C = Other.Character
			if C and Other ~= Player then
				local Want = Shared.Hidden(Other)
				if C:GetAttribute(`NHHiddenLocal`) ~= Want then
					C:SetAttribute(`NHHiddenLocal`, Want)
					hideCharacter(C, Want)
				end
			end
		end
	end)
	Player:GetAttributeChangedSignal(`NHTutorial`):Connect(function()
		if Player:GetAttribute(`NHTutorial`) == true then return end
		for _, Other in Players:GetPlayers() do
			if Other.Character and Other.Character:GetAttribute(`NHHiddenLocal`) then
				Other.Character:SetAttribute(`NHHiddenLocal`, false)
				hideCharacter(Other.Character, false)
			end
		end
		local F = workspace:FindFirstChild(`NHHometownCast`)
		if F then F:Destroy() end
		table.clear(Cast)
	end)
end

return Shared
```

`NHHiddenLocal` is set on the client only, so it never replicates and every client keeps its own value.

- [ ] **Step 2: Install, then run the two-player test (owner-assisted).** Studio's Test tab: **Local Server** with
  **2 players**.
  1. In each client's command bar, call `TutorialEnter` through the server window's command bar:
     `require(game.ServerScriptService.Services.World.Tutorial).Enter(game.Players:GetPlayers()[1])` and the same
     for `[2]`.
  2. Expected:
     - each client sees no other player;
     - walking into each other passes through (`TutorialPlayers` doesn't collide with itself);
     - after `Leave` for both, each sees the other again.
  3. Record the result in `tools/phase6-2350/review/two_player.md`.

- [ ] **Step 3: Commit**

```bash
git add tools/phase6-2350/live/StarterPlayer.StarterPlayerScripts.Controllers.Hometown.luau tools/phase6-2350/review/two_player.md
git -c user.name=Rello commit -m "2.35.0 private Wickfield: other tutorial players hidden locally, per-player cast

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 10: The Bus (`Cinematics.TutorialBus`)

**Files:**
- Create: `live/ReplicatedStorage.Cinematics.TutorialBus.luau`

**Interfaces:**
- Consumes:
  - set `BusStop` (Task 2);
  - `Config.CineClips` `Bus*` ids;
  - `Config.TutorialAnim` chain `TheBus`;
  - `CineActor` (`Ctx.Clip` as the resolver);
  - `Config.Cine.Looks.BusStop`.

- [ ] **Step 1: Write the cut**

```lua
--[[
	TutorialBus (doc 15 §5 beat 10, the ending). Seamless: you're waiting at the stop (TheBus chain's loop), the camera
	glides in over your shoulder, the black bus pulls in out of the fog (BrakeStop), the doors hiss open (DoorsOpen), the
	driver turns his head (DriverTurn), you step on (the chain's BoardBus), the doors close, it pulls away, and the frame
	freezes on the title card. Set BusStop (tools/phase6-2350/stage/hometown.lua).
]]
local Config = require(game:GetService(`ReplicatedStorage`).Config.Cine)
local Def = { Set = `BusStop`; Seamless = true; Clock = 23.2 }

function Def.Build(Ctx)
	local Me = Ctx.Self
	local Bus = workspace.Hometown.BlackBus:FindFirstChild(`WFBlackBus`)
	local Actor = require(game:GetService(`Players`).LocalPlayer.PlayerScripts.Controllers.CineActor)
	local BusAnimator = Bus:FindFirstChildWhichIsA(`Animator`, true)
	local function play(Clip: string)
		local Id = Ctx.Clip(Clip)
		if not (BusAnimator and Id) then return end
		local A = Instance.new(`Animation`)
		A.AnimationId = Id
		BusAnimator:LoadAnimation(A):Play(0.1)
	end
	return {
		grade = Config.Looks.BusStop;
		cues = {};
		events = {
			-- Local.Fire's own kinds: `call` spawns E.call(Ctx); the bus clips play on its AnimationController's Animator
			{ t = 0; call = function()
				Bus:PivotTo(Ctx.CF(`BusStart`))
				Actor.WalkTo(Ctx.CF(`Stand`), 4)
				Actor.Chain(`TheBus`, Ctx.Clip, { [1] = function() task.wait(6.5) end })
			end };
			{ t = 1.0; call = function()
				-- the last 58 studs to the stop over 5.5 s, decelerating; BrakeStop plays as it arrives
				local From, To = Ctx.CF(`BusStart`), Ctx.CF(`BusStop`)
				local T0 = os.clock()
				while os.clock() - T0 < 5.5 do
					local U = (os.clock() - T0) / 5.5
					Bus:PivotTo(From:Lerp(To, 1 - (1 - U) ^ 3))
					game:GetService(`RunService`).RenderStepped:Wait()
				end
				Bus:PivotTo(To)
			end };
			{ t = 5.3; call = function() play(`BusBrakeStop`) end };
			{ t = 7.4; call = function() play(`BusDoorsOpen`) end };
			{ t = 9.6; call = function() play(`BusDriverTurn`) end };
			{ t = 15.5; call = function()
				play(`BusPullAway`)
				local From, To = Ctx.CF(`BusStop`), Ctx.CF(`BusAway`)
				local T0 = os.clock()
				while os.clock() - T0 < 6 do
					local U = (os.clock() - T0) / 6
					Bus:PivotTo(From:Lerp(To, U * U * U))
					game:GetService(`RunService`).RenderStepped:Wait()
				end
			end };
		};
		shots = {
			{ name = `Waiting`; dur = 4.0; subject = Me; noise = `calm`; dof = true;
			  camera = { frame = { size = `MS`; yaw = 155; pitch = 6; lens = 35 }; to = { size = `MCU` }; ease = `inout` } };
			{ name = `Out of the fog`; dur = 3.2; subject = Bus; noise = `tense`; dof = true;
			  camera = { cframe = CFrame.lookAt(Ctx.Pos(`CamWide`), Ctx.Pos(`CamLookWide`)); lens = 24 } };
			{ name = `The doors`; dur = 2.4; subject = Bus; noise = `calm`; dof = { focus = Ctx.Pos(`Door`) };
			  camera = { cframe = CFrame.lookAt(Ctx.Pos(`CamDoor`), Ctx.Pos(`Door`)); lens = 50 } };
			{ name = `The driver`; dur = 3.2; subject = Bus; noise = `calm`; dof = true;
			  camera = { cframe = CFrame.lookAt(Ctx.Pos(`CamDriver`), Ctx.Pos(`Board`) + Vector3.new(-3.4, 5.4, -2)); lens = 85 } };
			{ name = `You step on`; dur = 2.8; subject = Me; noise = `calm`; dof = true;
			  camera = { frame = { size = `MS`; yaw = 200; pitch = 4; lens = 35 } } };
			{ name = `Away`; dur = 6.0; subject = Bus; noise = `calm`;
			  camera = { cframe = CFrame.lookAt(Ctx.Pos(`CamWide`), Ctx.Pos(`BusAway`)); lens = 28; }; };
			{ name = `Title`; dur = 3.0; role = `card`; card = { text = `NIGHTMARE HIGHSCHOOL`; style = `title` }; fadeIn = 0.15 };
		};
	}
end

return Def
```

The cut ends on the title card. That's the tutorial's end, so there's no glide out: `Def.EndHold = true` makes
`Finish` keep the title until the Prologue starts. Add `if Cut.Def.EndHold then ... end` around the blend-out in
`Finish`.

- [ ] **Step 2: Lint.** Edit-mode execute_luau, with the Studio player standing at the stop:
  `print(require(game.ReplicatedStorage.Cine).analyze(<Built shots>))` through `Controllers.Cine`'s
  `BuildForTests("TutorialBus")`. Expected: no `[fix]` lines. `CineSeam.Lint` from shot 1 should be `nil` when you
  stand on `Stand`.

- [ ] **Step 3: Run it.** Play, then `start_play.lua`, `TutorialEnter $P`, and `PlayCut $P '"TutorialBus"' false`.
  In a separate client call, run `camcheck.lua` with `Id = "TutorialBus"` (parameterise the check's `Id` at its
  top). Then run `bodycheck.lua` with `Chain = "TheBus"`. Expected: `CAM OK` and `BODY OK`.

- [ ] **Step 4: Commit**

```bash
git add tools/phase6-2350/live/ReplicatedStorage.Cinematics.TutorialBus.luau tools/phase6-2350/live/StarterPlayer.StarterPlayerScripts.Controllers.Cine.luau tools/phase6-2350/checks/camcheck.lua tools/phase6-2350/checks/bodycheck.lua
git -c user.name=Rello commit -m "2.35.0 The Bus: the tutorial's ending as a seamless cut (camera and body checks pass)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 11: Sneaking out past Biscuit (`Cinematics.TutorialSneak`)

**Files:**
- Create: `live/ReplicatedStorage.Cinematics.TutorialSneak.luau`

**Interfaces:**
- Consumes:
  - set `Garden` (Task 2);
  - `Hometown.Cast("WFBiscuit")` (Task 9);
  - `CineBeat` (Task 8);
  - `CineActor` and the chains `BiscuitStirs` and `FenceOver` (Task 3);
  - `Config.Cine.Looks.Night`.

- [ ] **Step 1: Write the cut** (segments: a beat, the soft-fail branch, the fence cut)

```lua
--[[
	TutorialSneak (doc 15 §5 beat 2). Seamless walk-and-talk: you crouch across the back garden past Biscuit's kennel
	(Follow rig, Biscuit kept in frame). Stand up near him and he gives one bored "wuff", the bedroom light flicks on and
	you have to crouch and wait (soft fail: the Hide beat until the light goes off). Reach the fence and a short seamless
	cut plays the FenceOver chain, then control comes straight back on the far side.
]]
local Config = require(game:GetService(`ReplicatedStorage`).Config.Cine)
local Def = { Set = `Garden`; Seamless = true; Clock = 23.9 }

function Def.Build(Ctx)
	local Home = require(game:GetService(`Players`).LocalPlayer.PlayerScripts.Controllers.Hometown)
	local Actor = require(game:GetService(`Players`).LocalPlayer.PlayerScripts.Controllers.CineActor)
	local Biscuit = Home.Cast(`WFBiscuit`)
	local Light = Ctx.Prop(`BedroomLight`, { Size = Vector3.new(4, 5, 0.2); CFrame = Ctx.CF(`LightWindow`); Color = Color3.fromRGB(255, 210, 140);
		Material = Enum.Material.Neon; Transparency = 1 })
	local Built = {}
	Built.grade = Config.Looks.Night
	Built.cues = {
		BiscuitWakes = function()
			if not Biscuit then return end
			local Me = game:GetService(`Players`).LocalPlayer
			-- standing (not crouched) near him: the wuff and the light (the soft fail). Services.Player.Crouch sets `Crouch`
			local Crouched = (Me.Character and Me.Character:GetAttribute(`Crouch`)) or Me:GetAttribute(`Crouch`)
			if not Crouched then
				require(Me.PlayerScripts.Controllers.Gui.CineUI).Subtitle(`Biscuit`, `Wuff.`, 1.5)
				Light.Transparency = 0
				Built.Fail = true
			end
		end;
	}
	Built.segments = {
		Garden = { beat = {
			rig = `Follow`; frame = { also = `Biscuit`; lens = 35; low = true };
			move = { speed = 0.7; sprint = false; crouch = true };
			lines = { { on = `start`; who = `You`; text = `Okay. Quiet. Very quiet.` } };
			cues = { { on = `near:Biscuit:8`; run = `BiscuitWakes` } };
			ends = { on = `enter:FenceZone`; next = `Fence` };
		} };
		Hide = { beat = {
			rig = `Frame`; frame = { also = `LightWindow`; lens = 40 };
			move = { speed = 0; crouch = true };
			lines = { { on = `start`; who = `You`; text = `Don't. Move.` } };
			ends = { on = `t:4`; next = `Garden` };
		} };
		Fence = { shots = {
			{ name = `Over the fence`; dur = 3.0; subject = Ctx.Self; noise = `tense`; dof = true;
			  camera = { frame = { size = `MS`; yaw = 120; pitch = 8; lens = 28 }; to = { size = `MS`; yaw = 160 }; ease = `inout` } };
		}; events = { { t = 0; call = function() Actor.Begin() Actor.Chain(`FenceOver`, Ctx.Clip) end } } };
	}
	return Built
end

return Def
```

The `Garden` beat's cue sets `Built.Fail`. Make the beat's `ends` choose the soft fail: give the `Garden` beat a
second end trigger with `ends = { { on = "fail"; next = "Hide" }, { on = "enter:FenceZone"; next = "Fence" } }`, and
have `CineBeat`'s `trigger` treat `on = "fail"` as `Cut.Built.Fail == true` (clearing it when it fires). Extend
`CineBeat` to accept `ends` as one table or a list of tables, and add that line to `trigger` in this task's install.
The `Garden` beat holds the game's own crouch through the server (`move.crouch`; spec delta 5), so you sneak past
Biscuit with your own Crouch / CrouchWalk animations. The wuff only fires if you deliberately stand up.
- **Re-asserting crouch:** `CineBeat` re-sends `BeatCrouch` (`On = true`) when the `Crouch` attribute drops while
  `move.crouch` is set, and shows the line "Stay low." That's two lines in its render step, part of this task's
  install.
- **The fence:** the `FenceOver` chain now starts on `GameCrouchWalk` (Task 3 Step 6b), so the cut picks up from
  exactly the pose you were sneaking in.

- [ ] **Step 2: Run it (owner plays it).**
  1. Play, then `start_play.lua`, `TutorialEnter $P`, and `PlayCut $P '"TutorialSneak"' false`.
  2. Expected:
     - you can move the whole time in `Garden`;
     - the camera keeps Biscuit in frame;
     - standing within 8 studs of him triggers the wuff and the light, then `Hide`, then back to `Garden`;
     - reaching the fence plays `FenceOver` and hands control back.
  3. `camcheck.lua` (Id `TutorialSneak`) must say `CAM OK`.
  4. Then run `bridge.py Origin $P`. Expected: `Checkpoint` = `TutorialSneak:Fence` after the fence.

- [ ] **Step 3: Commit**

```bash
git add tools/phase6-2350/live/ReplicatedStorage.Cinematics.TutorialSneak.luau tools/phase6-2350/live/StarterPlayer.StarterPlayerScripts.Controllers.CineBeat.luau
git -c user.name=Rello commit -m "2.35.0 Sneaking out past Biscuit: the first walk-and-talk beat (soft fail, seamless fence)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 12: Acceptance pass

**Files:**
- Create: `tools/phase6-2350/REPORT.md`

- [ ] **Step 1: Run the measured checks and paste their output into `REPORT.md`:**
  - `CineSeamTest`, `CineRigsTest`, `SeamlessHoldTest` (bridge);
  - `camcheck.lua` for `__SeamlessTest`, `TutorialBus` and `TutorialSneak`;
  - `bodycheck.lua` for `TheBus`.

  All must pass.
- [ ] **Step 2: Run the playtest matrix and record each row as pass or fail, with a note:**

  | Case | Expected |
  |---|---|
  | Solo | Both cuts work. |
  | Two players (Task 9) | Each sees a private Wickfield; no collisions. |
  | Death mid-beat | Reset in `Garden`: you respawn at the checkpoint's mark (`TutorialSneak:Garden`), camera behind you. |
  | Rejoin | Stop and Play again: the checkpoint resumes. |
  | Reduce Motion on | Glides are 0.2 s dissolves; no handheld. |
  | Phone | Studio's device emulator at phone size: subtitles ≥ 20 px, the skip is a large target. |

  The checkpoint resume itself (placing the player at the mark) is a two-line addition to `World.Tutorial.Enter`.
  Read `CheckpointOf(Player)`; if it's set, `PivotTo` that set's first mark for the segment, plus 3 studs up. Add it
  here if the rejoin row fails.
- [ ] **Step 3: House style.** Capture both cuts as recordings, then:
  1. Run `python ~/.claude/skills/r6-animation-cinematics/scripts/motion_audit.py <clip.mp4> OUT --strip <t0> <t1> 30`
     around the glide in, the doors, and the fence.
  2. Compare against the skill's §2-§3:
     - the camera's still fraction;
     - roll 0 on the ground beats;
     - moving holds.
  3. Note the numbers in `REPORT.md`.
- [ ] **Step 4: The owner watches both at full speed and signs off.** Record their words in `REPORT.md`.
- [ ] **Step 5: Commit**

```bash
git add tools/phase6-2350/REPORT.md
git -c user.name=Rello commit -m "2.35.0 acceptance: measured checks, playtest matrix, motion audit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 13: Docs and release

**Files:**
- Modify: `docs/superpowers/specs/2026-11-20-tutorial-seamless-cinematics-design.md` (status, spec deltas)
- Modify: `docs/expansion/04-Cinematic-Framework.md` §4 (a pointer to seamless cuts)
- Modify: `docs/expansion/15-Tutorial-The-Last-Normal-Night.md` §9 (slice 1 done)
- Modify: `CHANGELOG.md` (2.35.0)

- [ ] **Step 1: Spec.**
  1. Add `**Status:** slice 1 shipped in 2.35.0 (plan: docs/superpowers/plans/2026-11-20-tutorial-seamless-cinematics-slice1.md).`
     under the title.
  2. Add a `## Spec deltas` section that copies this plan's four deltas.
- [ ] **Step 2: Doc 04 §4.** Add one bullet:
  `**Seamless cuts (2.35.0):** a cut with Seamless = true in Config.Cine glides in from the live camera, uses the real character, fades the HUD and blends out onto the Custom camera; see docs/superpowers/specs/2026-11-20-tutorial-seamless-cinematics-design.md.`
- [ ] **Step 3: Doc 15 §9.** Mark "The bus stop and the black bus" and the beat-2 sneak as built in 2.35.0, slice 1.
- [ ] **Step 4: CHANGELOG.** Add a `## [2.35.0] - <date>: Seamless cinematics, slice 1 (Tutorial)` section above
  2.34.0, in the file's existing style. Commit only that hunk:
  `git add -p CHANGELOG.md`, and stage only the 2.35.0 lines.
- [ ] **Step 5: Mirror check.** For every file in `tools/phase6-2350/live/`, `dump.py` it again into a temporary
  folder and `diff` it against `live/`. Expected: no differences (Studio matches the mirror).
- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/specs/2026-11-20-tutorial-seamless-cinematics-design.md docs/expansion/04-Cinematic-Framework.md docs/expansion/15-Tutorial-The-Last-Normal-Night.md
git -c user.name=Rello commit -m "2.35.0 docs: seamless cinematics slice 1 (spec deltas, doc 04 pointer, doc 15 progress, changelog)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Self-review (run while writing)

- **Spec coverage:**

  | Spec section | Task |
  |---|---|
  | §1 architecture | Tasks 4-9 |
  | §2.1 marks, input, glide, screen, body | Tasks 6, 7 (screen: `FadeHud`; no bars) |
  | §2.2 the re-seat, camera out, control | Tasks 3, 6, 7 |
  | §2.3 skip dip | Task 7 |
  | §3 beats, rigs, nudge, mapping, lines and cues, prompts, ends | Tasks 8, 11 |
  | §3 prompts inside beats | The beat's `prompt` field. Doc 12 prompts reuse `Local.OpenPrompt`; wire it in `CineBeat` when the getaway beat (a later slice) needs it. Slice 1's two scenes have no prompt. |
  | §4.1 lenses, handheld feel, focus, grades | Task 4 (feel), Task 5 (`Looks`); lenses and focus are the library's existing `lens` / `dof` |
  | §4.1 grade ease over 1 s | `Config.Cine.GradeEase`, applied by the director when a beat crosses interior and exterior. Slice 1 has no interior; it's built with the breakfast beat. |
  | §4.2 privacy, collision, cast | Tasks 5, 9 |
  | §4.3 checkpoints, timeouts, Reduce Motion | Tasks 5, 7, 12 |
  | §5 first slice and checks | Tasks 10-12 |
  | §6 out of scope | Respected |

- **Names used across tasks:**
  - `CineSeam.{Length, Keys, Lint, Blend, Ease}` and `Cine.cameraAt`;
  - `CineActor.{Begin, WalkTo, Chain, Reseat, Release}`;
  - `CineRigs.{Target, Nudge, Damp}` and `CineBeat.Run`;
  - `Hometown.{Hidden, Cast}`;
  - `Tutorial.{Enter, Leave, Checkpoint, CheckpointOf}`;
  - `CineUI.{FadeHud, Dip}`;
  - `TutorialAnim.Play(animator, chain, resolve, cues, onSwitch)`.

  These are consistent across the tasks.
