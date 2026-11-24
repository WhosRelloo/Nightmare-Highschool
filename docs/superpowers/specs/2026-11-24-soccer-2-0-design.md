# Soccer 2.0: the FIER clips in Soccer 1.1 (design)

**Status:** design approved by the owner 2026-11-24; waiting for the owner's review of this written spec.
**Concept:** `docs/superpowers/research/2026-11-24-soccer-2-concept.md`, section 3 (the clip map) and "2.0".
**Place:** NH Combat Test (placeId 98950102230473). The soccer code lives only in Studio; the repo holds the bake
script, copies of every edited module under `tools/soccer2/live/`, and the checks under `tools/soccer2/checks/`.

## Goal
Every soccer move that has a FIER clip plays that clip, foot meets ball on the contact frame, and during a match the
FIER jogs and idles replace the default walk and idle. The server rules (ball speed, power, timings, who wins a
tackle) do not change. Clips that need new mechanics (Chip, Stall, Penalty) are baked and slotted now and triggered
in 2.1 and 2.2.

## Decisions (owner, 2026-11-24)
- **Approach A:** clips play in place; the game moves the HumanoidRootPart by each clip's measured travel.
- Kicks jump to just before contact, so the foot meets the ball within about 0.05 s of the server's kick.
- A charged kick holds its wind-up as a creeping hold, never frozen.
- Kick Soccerball is mirrored to the right foot.
- The jog replaces the walk during a match, with cadence matched like the strafes; sprint keeps the game's run.
- **The goal cut moves out of 2.0** into its own later step (it needs a short replay, since the scoring shot isn't
  known at contact).

## Non-goals
- No server rule changes, no new inputs, no new mechanics (chip, stall, penalties, fouls are 2.1 / 2.2).
- No new clips: the header, the keeper throw ("Activate") and the celebration ("Isagi Celebration") stay as they are.
- No publishing by Claude: the owner publishes the baked clips to group 15981569 and the ids go into Config.

## 1. The bake (Edit mode, run once, re-runnable)
**Script:** `tools/soccer2/bake_soccer_clips.lua`, run with `execute_luau` in Edit mode.

- **Source:** the 24 KeyframeSequences in `Workspace."Soccer Anims".AnimSaves`. They are read, never changed.
- **Output:** `ReplicatedStorage.NHSoccerClips`, one KeyframeSequence per clip (same names), plus
  `KickSoccerball_Right` (the mirror). A re-run deletes and rebuilds the folder.
- **Data:** the bake writes the ModuleScript `ReplicatedStorage.Config.SoccerClips`:
  `[ClipName] = { Length, ContactAt?, Loop, Path? }`. Nothing in it is typed by hand.

### 1.1 Removing the baked travel
Positions are read in HumanoidRootPart space: the Torso pose position (the RootJoint Transform) rotated by the
RootJoint C0 rotation (+X right, +Y up, −Z forward). Height (Y) and every rotation are kept. Two modes:

| Mode | Clips | What is removed | What the game does |
|---|---|---|---|
| **Loop** | Jog Forward, Goalkeeper CatchIdle | the straight ramp from the first key's X/Z to the last key's (keeps the in-cycle sway) | the jog's ground speed is the player's own movement |
| **Path** | Chip, Penalty, Spin, Tackled, Trip, Diving SaveLeft, Diving SaveRigh, StepLeft, StepRight | the whole X/Z offset from the first key | `Local.DashPath` replays the removed path (section 4) |

For **Path** clips the removed offset is sampled at 30 fps into `Path = { {t, x, z}, ... }` (HRP space, studs).
Diving SaveRigh's travel was baked 3.2 forward while the roll goes right; Path mode removes it, and its `Path` is
rebuilt as its X/Z mirror of Diving SaveLeft's, scaled to its own length, so the dive goes right.
Clips not listed (all idles, Kick Soccerball, Pass, Scissor Kick, Strike Foward Jog, Tackle, Tackled2, Fallen Idle,
Stall, Jog Backward, Goalkeeper Idle and Catch) keep their positions as baked: they were measured in place.

### 1.2 Contact markers
A `KeyframeMarker` named `Contact` is added at `ContactAt`. These times come from the peak leg speed and are checked by
eye on a 30 fps strip around each one before wiring (`r6-animation-cinematics` review step); a wrong one is moved in
the bake's table and the bake re-run.

| Clip | ContactAt (s) |
|---|---|
| Strike Foward Jog_R6 | 0.43 |
| Kick Soccerball_R6 (left) and KickSoccerball_Right | 0.23 |
| Soccer Pass_R6 | 0.47 |
| Chip_R6 | 0.47 |
| Scissor Kick_R6 | 0.68 |
| Soccer Penalty Kick_R6 | 0.73 |
| Soccer Spin_R6 | 0.23 (a second `Contact` marker at 0.60) |
| Soccer Tackle_R6 | 0.10 |

### 1.3 The mirror (Kick Soccerball to the right foot)
For each pose: swap the Left/Right Arm and Left/Right Leg poses. For every joint, build its Torso-space transform
`T = C0 * Transform * C1:Inverse()`, mirror it across the Torso's YZ plane (`M * T * M`, with `M` = X scaled by −1),
then solve for the opposite joint: `Transform' = C0'^-1 * (M T M) * C1'`. The Torso pose (RootJoint) and the Head are
mirrored in place the same way. Done this way the R6 shoulder and hip C0 rotations can't twist the result.

### 1.4 Loops
`Loop = true` for Soccer Idle, Offensive Idle, Goalkeeper Idle, Goalkeeper CatchIdle, Goalkeeper StepLeft and StepRight, Jog Forward, Jog Backward and
Fallen Idle. The client sets `Looped` on the track (the KeyframeSequences stay as published, Loop false).

## 2. Config
`Config.Sports.SoccerAnims` changes from `Slot = id` to `Slot = { Id: number?, Clip: string }`:

| Slot | Clip | Played on |
|---|---|---|
| KickRun | Strike Foward Jog_R6 | `S_Kick` Kind Shot while the root's flat speed ≥ 6 studs/s |
| Kick | KickSoccerball_Right | `S_Kick` Kind Shot otherwise, and `S_Charge` |
| Pass | Soccer Pass_R6 | `S_Kick` Pass and `S_Pass` |
| Volley | Scissor Kick_R6 | `S_Kick` Volley |
| Dribble / Feint | Soccer Spin_R6 | `S_Dribble` / `S_Feint` |
| Tackle | Soccer Tackle_R6 | `S_Tackle` (replaces the group "SLIDING" clip) |
| Tackled | Soccer Tackled_R6 or Tackled2_R6, picked at random | `S_Stolen` and `S_Stun` from a tackle |
| Trip | Soccer Trip_R6 | `S_Ankles` |
| Fallen | Fallen Idle_R6 | after Tackled / Trip ends, until the stun ends |
| KeeperIdle, KeeperStepLeft, KeeperStepRight | Goalkeeper Idle / StepLeft / StepRight | the keeper's movement (section 5) |
| KeeperDiveLeft, KeeperDiveRight | Diving SaveLeft / SaveRigh | `S_Dive` by `Side` |
| KeeperCatch, KeeperCatchIdle | Goalkeeper Catch / CatchIdle | the keeper picks up the ball, then the hold |
| Chip, Stall, Penalty | Chip / Stall Soccerball / Soccer Penalty Kick | nothing in 2.0 (2.1 and 2.2) |
| KeeperThrow, Celebrate, Header | unchanged | unchanged |

- **Which one plays:** a published `Id` wins. Without one, in Studio the client registers `NHSoccerClips[Clip]` with
  `KeyframeSequenceProvider:RegisterKeyframeSequence` (the `NHLocoClips` precedent in `AnimationController`) and plays
  that. In a live server with no `Id`, the 1.1 procedural pose plays, as today.
- `LENGTH` / `STOP_AFTER` for clip slots come from `Config.SoccerClips[Clip].Length`; the procedural lengths stay for
  procedural poses.

## 3. Kicks and contact timing (`Controllers.Gui.Soccer`)
- **`S_Charge`:** plays the Kick slot from 0 at speed 1. At `ContactAt − 0.10` the speed drops to 0.05 (the creeping
  hold) until `S_Kick` or the charge ends. A cancelled charge stops the track over 0.2 s.
- **`S_Kick`:** sets the track's `TimePosition` to `ContactAt − 0.05` and speed 1, so the foot meets the ball 0.05 s
  after the server's kick. A tap with no charge starts the clip at that point straight away.
- **Spin** (dribble / feint) starts at 0: its travel starts with the move, and the server's ball already follows the
  dribbler. If planning finds the server keeps the ball at a fixed lead, the clip's playback speed is scaled so its
  path takes the 1.1 dash time instead.
- All clip tracks stay at `Action2`, `Looped = false` except the loops in 1.4, cut by `STOP_AFTER`.

## 4. Clips that move the body
- **New `Local.DashPath(Root, Path, Speed)`** in `Controllers.Gui.Soccer`: each frame it sets the existing
  LinearVelocity to the path's velocity between the two samples around the track's `TimePosition`, turned from HRP
  space to world by the root's facing at the start. It stops when the track ends or stops, and gives up the
  LinearVelocity to `Local.Dash` if a new move starts.
- **Used by:** Spin, Tackled, Trip and both dives. Tackle keeps the 1.1 slide `Local.Dash` (its clip has no travel).
  The keeper steps never use it: they play under the player's own movement (section 5), so their `Path` is only
  removed, not replayed.
- **Ground:** DashPath only moves on X/Z; the Humanoid keeps the height, so a dive never sinks into the pitch.

## 5. The match walk and idle (the Soccer pack)
- **New pack:** `ReplicatedStorage.Assets.Animations.Soccer.Movement` with `Idle` (Soccer Idle) and `Walk` (Jog
  Forward). `Sprint`, `FastSprint`, `Jump`, `Fall`, `Land`, `Crouch` and `CrouchWalk` are copies of Default's, so
  sprinting keeps the game's run.
- **When it's on:** `Controllers.Character.AnimationController` watches the Player's `InSport` attribute (it survives
  respawns; the Character's copy doesn't). When `InSport` is set and
  `Workspace.Sports[InSport]:GetAttribute("SportVenue") == "Soccer"`, it runs
  `StopAllTracks():SetTracks(Soccer.Movement):PlayTrack("Idle", 0.2)`. When `InSport` clears it restores the pack the
  way `Transformation`'s `restorePack` does (weapon pack, else Default). Transformation already does nothing during
  `InSport`, so the two never fight.
- **Idle variants:** Offensive Idle while the Character has `HasSportBall`; Goalkeeper Idle while the player is the
  keeper. The keeper flag is the Soccer service's existing one if planning finds it; if there is none, the plan adds the
  Character attribute `SoccerKeeper` set by `Services.Sports.Soccer` when it picks the keeper.
- **Cadence:** the bake measures Jog Forward's and Jog Backward's strides with the strafe baker's spread method and
  writes them to `Config.Locomotion.Stride` as `SoccerJog` and `SoccerJogBack`. The Walk track's rate is
  `Functions.Locomotion.Rate(flat root speed, Stride.SoccerJog, LegLen)`, capped at `CadenceMax`.
- **Backward:** in the strafe blend (`Walk8`), the `Back` weight plays Jog Backward (its own track at a positive
  rate) instead of the reversed Walk while the Soccer pack is on. The strafe tracks stay the shared ones.
- **Keeper side steps:** while the keeper is in StrafeMode, the Left / Right weights play Goalkeeper StepLeft /
  StepRight instead of the shared strafes, looped, at `Rate(flat root speed, Stride.KeeperStep, LegLen)`. The bake
  measures `KeeperStep` from the two step clips' removed paths (their average side travel per second at 1x).

## 6. Error handling
- A missing `NHSoccerClips` entry or a failed `RegisterKeyframeSequence` falls back to the slot's procedural pose and
  warns once per clip.
- A clip track that fails to load never blocks the server's move: the pose is visual only.
- If `Workspace.Sports[InSport]` is missing, the pack stays as it is.
- Leaving a match mid-move stops every soccer track and the DashPath before the pack is restored.

## 7. Testing (slot 2 rules: fresh snapshot each Play round, restore only from it, record CineState / Seen / Origin)
- **Edit check `soccer_clips_edit.lua`:**
  - 25 KeyframeSequences in `NHSoccerClips` (24 + the mirror), each with a `Config.SoccerClips` entry.
  - Every Loop and Path clip drifts < 0.1 stud on X/Z from its first key (Loop: after the ramp).
  - Each clip in the 1.2 table has a `Contact` marker within 1 frame of its time.
  - The mirror's fastest limb around contact is the Right Leg.
  - `Config.Locomotion.Stride.SoccerJog` and `SoccerJogBack` exist and are between 3 and 7; `KeeperStep` exists and
    is above 0.
- **Play check `soccer_play_client.lua`** (a match started through the harness):
  - The Soccer pack is on after `InSport` is set and off after it clears; Offensive Idle with the ball.
  - At `S_Kick`, the kick track's `TimePosition` is `ContactAt − 0.05` (±0.02 s).
  - DashPath distances are within 10 % of each clip's `Path` end.
  - The Walk track's rate follows `Rate(...)` within 5 %.
- **Look and feel:** a recorded match (jog, charged shot, running shot, pass, spin, tackle and fall, keeper dive and
  catch), then `motion_audit.py`, `jitter_audit.py` and `physics_audit.py`. The jog's planted foot skates < 0.6
  studs/s; no frozen frames during the creeping hold. Screenshots under
  `docs/superpowers/mockups/2026-11-24-soccer-2-0/`, and the owner watches it at full speed.

## 8. Checked during planning (each has its default above)
1. Whether the server keeps the dribbled ball at a fixed lead (section 3 default: the clip speed scales).
2. The keeper flag's name (section 5 default: add `SoccerKeeper`).
3. Which server events mark being tackled and the stun's end (section 2 assumes `S_Stolen`, `S_Stun`, `S_Ankles`).
4. How `AnimationController` exposes `Walk8` and the `Back` track, so the Soccer pack can swap Back and the keeper
   strafes without touching the shared tracks.
