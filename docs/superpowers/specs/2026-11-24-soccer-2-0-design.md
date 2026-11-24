# Soccer 2.0: the FIER clips in Soccer 1.1 (design)

**Status:** design approved by the owner 2026-11-24. The owner said "Continue" on the written spec (2026-11-24); the
planning checks below were settled from the Studio code the same day, and the dash rule (section 4) follows the
recommended option the owner continued with.
**Concept:** `docs/superpowers/research/2026-11-24-soccer-2-concept.md`, section 3 (the clip map) and "2.0".
**Plan:** `docs/superpowers/plans/2026-11-24-soccer-2-0.md`.
**Place:** NH Combat Test (placeId 98950102230473). The soccer code lives only in Studio; the repo holds the bake
script, copies of every edited module under `tools/soccer2/live/` (originals under `tools/soccer2/pre/`), and the
checks under `tools/soccer2/checks/`.

## Goal
Every soccer move that has a FIER clip plays that clip, foot meets ball on the contact frame, and during a match the
FIER jogs and idles replace the default walk and idle. The server rules (ball speed, power, timings, who wins a
tackle) and the 1.1 movement distances do not change. Clips that need new mechanics (Chip, Stall, Penalty) are baked
and slotted now and triggered in 2.1 and 2.2.

## Decisions (owner, 2026-11-24)
- **Approach A:** clips play in place; the game moves the HumanoidRootPart.
- Kicks jump to just before contact, so the foot meets the ball within about 0.05 s of the server's kick.
- A charged kick holds its wind-up as a creeping hold, never frozen.
- Kick Soccerball is mirrored to the right foot.
- The jog replaces the walk during a match, with cadence matched like the strafes; sprint keeps the game's run.
- **The goal cut moves out of 2.0** into its own later step (it needs a short replay, since the scoring shot isn't
  known at contact).
- **The dive and the dribble keep their 1.1 distances and timing** (17 studs in 0.5 s, 11 studs in 0.4 s). The body
  follows the clip's own travel curve stretched to that distance, and the clip plays up to 2x faster through its
  travel (section 4).

## Non-goals
- No server changes at all, no new inputs, no new mechanics (chip, stall, penalties, fouls are 2.1 / 2.2).
- No new clips: the header and the celebration stay as they are; the keeper throw keeps "Activate".
- No publishing by Claude: the owner publishes the baked clips to group 15981569 and the ids go into Config.

## 1. The bake (Edit mode, run once, re-runnable)
**Script:** `tools/soccer2/bake/bake_soccer_clips.lua`, run in Edit mode with `tools/admin-console/run_check.py`.

- **Source:** the 24 KeyframeSequences in `Workspace."Soccer Anims".AnimSaves`. They are read, never changed.
- **Output:** `ReplicatedStorage.NHSoccerClips`, one KeyframeSequence per clip (same names), plus
  `KickSoccerball_Right` (the mirror): 25 in all. A re-run deletes and rebuilds the folder.
- **Data:** the bake writes the ModuleScript `ReplicatedStorage.Config.SoccerClips`:
  `{ Clips = { [ClipName] = { Length, ContactAt?, Contacts?, Loop, Path? } }, Stride = { SoccerJog, SoccerJogBack,
  KeeperStep } }`. Nothing in it is typed by hand.

### 1.1 Removing the baked travel
Positions are read in HumanoidRootPart space: the Torso pose position (the RootJoint Transform) rotated by the
RootJoint C0 rotation (+X right, +Y up, −Z forward). Height (Y) and every rotation are kept. Two modes:

| Mode | Clips | What is removed |
|---|---|---|
| **Loop** | Jog Forward, Goalkeeper CatchIdle | the straight ramp from the first key's X/Z to the last key's (keeps the in-cycle sway) |
| **Path** | Chip, Penalty, Spin, Tackled, Trip, Diving SaveLeft, Diving SaveRigh, StepLeft, StepRight | the whole X/Z offset from the first key |

For **Path** clips the removed offset is sampled at 30 fps into `Path = { {t, x, z}, ... }` (HRP space, studs).
Diving SaveRigh's baked travel is 2.6 studs forward while the roll goes right; its `Path` is rebuilt as Diving
SaveLeft's with X negated, time-scaled to its own length. Clips not listed keep their positions as baked (measured in
place).

Measured travel (2026-11-24, HRP space, 10 % / 90 % of the peak): Spin 9.9 forward, 0.13-1.13 s; Diving SaveLeft 7.9
left at the peak (5.9 at the end), 0.53-1.57 s; Tackled 2.0 left; Trip 3.5 right; StepLeft 3.2, StepRight 4.1; Jog
Forward 5.6 per 0.83 s cycle; Chip 13.7 forward; Penalty 8.0.

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
| Soccer Spin_R6 | 0.23 (`Contacts = {0.23, 0.60}`, two markers) |
| Soccer Tackle_R6 | 0.10 |

### 1.3 The mirror (Kick Soccerball to the right foot)
For each pose: swap the Left/Right Arm and Left/Right Leg poses. For every joint, build its Torso-space transform
`T = C0 * Transform * C1:Inverse()`, mirror it across the Torso's YZ plane (`M * T * M`, with `M` = X scaled by −1),
then solve for the opposite joint: `Transform' = C0'^-1 * (M T M) * C1'`. The Torso pose (RootJoint, in HRP space with
the RootJoint's C0/C1) and the Head (Neck) are mirrored in place the same way. The C0/C1 come from the "Soccer Anims"
rig's own Motor6Ds.

### 1.4 Loops and strides
- **Loops:** the bake sets `Loop = true` on its copies of Soccer Idle, Offensive Idle, Goalkeeper Idle, Goalkeeper
  CatchIdle, Goalkeeper StepLeft and StepRight, Jog Forward, Jog Backward and Fallen Idle (so the published clips
  loop too). The source clips stay Loop false.
- **Strides** (ground speed at 1x on 2-stud legs, the `Config.Locomotion.Stride` unit):
  - `SoccerJog` = Jog Forward's removed ramp / its length (5.6 / 0.83 ≈ 6.7);
  - `SoccerJogBack` = 2 × the largest fore-aft foot spread / length (the strafe baker's spread rule), from the rig's
    hip C0/C1 and the leg poses;
  - `KeeperStep` = the mean of StepLeft's and StepRight's removed side travel / length (≈ 7.1).

## 2. Config
`Config.Sports.SoccerAnims` changes from `Slot = id` to `Slot = { Id: number?, Clip: string?, Was: number? }`:
- **Which one plays:** a published `Id` wins. Without one, in Studio the client registers `NHSoccerClips[Clip]` with
  `KeyframeSequenceProvider:RegisterKeyframeSequence` (the `NHLocoClips` precedent in `AnimationController`). In a
  live server with no `Id`, `Was` (the 1.1 clip, if there was one) plays, else the 1.1 procedural pose.
- Clip timing data (`ContactAt`, `Path`, `Length`) is used only when the FIER clip itself plays.

| Slot | Clip | Played on |
|---|---|---|
| KickRun | Strike Foward Jog_R6 | `S_Kick` Kind Shot / Swing while the kicker's flat speed ≥ 6 studs/s |
| Kick | KickSoccerball_Right | `S_Charge`, and `S_Kick` Shot / Swing otherwise |
| Pass | Soccer Pass_R6 | `S_Kick` Pass and `S_Pass` |
| Volley | Scissor Kick_R6 | `S_Kick` Volley |
| Dribble, Feint | Soccer Spin_R6 | `S_Dribble`, `S_Feint` |
| Tackle | Soccer Tackle_R6 (`Was` 98978935956373, "SLIDING") | `S_Tackle` |
| Tackled, Tackled2 | Soccer Tackled_R6, Soccer Tackled2_R6 (picked at random) | `S_Stolen`, on `From` (the carrier who lost the ball) |
| Trip | Soccer Trip_R6 | `S_Ankles`, on `Player` (the tackler whose ankles broke, or who was feinted) |
| Fallen | Fallen Idle_R6 | after Tackled / Trip ends, while the Character's `SportStun` is still in the future |
| KeeperDiveLeft, KeeperDiveRight | Diving SaveLeft / SaveRigh | `S_Dive`, by the side of `Dir` against the root's RightVector |
| KeeperCatch, KeeperCatchIdle | Goalkeeper Catch / CatchIdle | `S_Pickup` for the local player as keeper in the zone, then while they hold the ball |
| Idle, IdleBall, KeeperIdle | Soccer Idle / Offensive Idle / Goalkeeper Idle | the Soccer pack (section 5) |
| Jog, JogBack | Jog Forward / Jog Backward | the Soccer pack |
| KeeperStepLeft, KeeperStepRight | Goalkeeper StepLeft / StepRight | the Soccer pack, the keeper's strafes |
| Chip, Stall, Penalty | Chip / Stall Soccerball / Soccer Penalty Kick | nothing in 2.0 (2.1 and 2.2) |
| KeeperThrow, Celebrate | unchanged ids ("Activate", "Isagi Celebration") | unchanged |
| Header | none | the procedural pose, unchanged |

## 3. Kicks and contact timing (`Controllers.Gui.Soccer`)
`Lead = 0.05`, `Margin = 0.10`.
- **`S_Charge`:** plays the Kick slot from 0 at speed 1. At `HoldAt = ContactAt − Margin` the speed drops to
  `Creep = Lead / T.Kick.MaxHold`, so the clip reaches `ContactAt − Lead` exactly when the charge would auto-release:
  always moving, never past the kick point. A charge with no kick stops the track after `T.Kick.MaxHold + 0.5` s.
- **`S_Kick`:** plays the kick's slot at `TimePosition = max(ContactAt − Lead, the charge track's position)` and speed
  1, so the foot meets the ball 0.05 s after the server's kick. A tap with no charge starts there straight away. A
  running shot (KickRun) replaces the charge track.
- **Pass and Volley** start at `ContactAt − Lead` too.
- One soccer clip plays at a time per character: starting one stops the others (fade 0.08 s).
- FIER clips play to their end (Looped false except the loops above); the 1.1 `LENGTH` cut applies only to `Was` clips
  and procedural poses. `STOP_AFTER` (the celebration) is unchanged.

## 4. Clips that move the body
**The rule:** a move keeps its 1.1 distance and timing; the clip only shapes the motion.

- **The window:** each Path clip's travel window `[t0, t1]` is where its path distance passes 10 % and 90 % of its
  peak. The clip starts at `TimePosition = t0` and plays at `Rate = clamp((t1 − t0) / DashTime, 1, 2)` until `t1`,
  then at 1x. The dash lasts `(t1 − t0) / Rate`.
- **The dash:** `Clips.DashPath` drives the existing LinearVelocity along the 1.1 direction. Its speed follows the clip's
  own progress through the window, `Progress(t)` = the path's distance from `t0` along the window's displacement,
  divided by the window's length (0 → 1), times the 1.1 distance. The body ends exactly the 1.1 distance away.
- **Numbers:**

| Move | 1.1 | Window | Rate | Dash time |
|---|---|---|---|---|
| Dive | 17 studs (34 × 0.5) in 0.5 s | 0.53-1.57 s | 2.0 | 0.52 s |
| Dribble | 11 studs (22 / 0.4 × 0.5 × 0.4) in 0.4 s | 0.13-1.13 s | 2.0 | 0.50 s |

  The server's windows (Diving 1.2 s, Dribbling 0.4 s) are unchanged; the dash starts on the event, as in 1.1.
- **Every client** plays the clip with the same rate (`Clips.Drive`); only the mover's own client runs the dash.
- **Feint:** Spin plays from 0 at 1x in place (1.1 had no dash). **Tackle:** the 1.1 slide dash is unchanged (the clip
  has no travel). **Tackled / Trip:** the 1.1 push (`S_Stolen`'s `Push`) and the ankle ragdoll carry the body; their
  path is removed and not replayed.
- **Falls follow the stun:** Tackled and Trip stop (fade 0.25 s) when the Character's `SportStun` passes, so nobody
  walks in a falling pose; Fallen Idle covers any stun left after the fall clip ends.
- A new dash (1.1 `Local.Dash` or `DashPath`) cancels a running `DashPath`.

## 5. The match walk and idle (`Controllers.Character.SoccerPack`)
- **When it's on:** the local player's `InSport` attribute names a venue whose `SportVenue` is `"Soccer"` (the venue
  is `Workspace.Sports.Pitch`). It's checked on every `InSport` change and after a respawn.
- **The pack** is built at runtime (Studio plays registered temporary ids, so it can't be a saved folder): Default's
  Movement Animations, with `Idle` = the Idle slot and `Walk` = the Jog slot. Sprint, FastSprint, Jump, Fall, Land,
  Crouch and CrouchWalk stay Default's, so sprinting keeps the game's run. It's applied with
  `StopAllTracks():SetTracks(Pack):PlayTrack("Idle", 0.2)`.
- **`AnimationController.Override(O)`** (new): while set, `O.Stride` overrides the stride per gait (`Walk` =
  `SoccerJog`, `Back` = `SoccerJogBack`, and for the keeper `StrafeLeft` / `StrafeRight` = `KeeperStep`), `O.Back`
  adds a real backpedal track to the directional walk (Jog Backward at a positive rate, instead of the reversed
  Walk), and `O.Left` / `O.Right` replace the strafe tracks (the keeper's steps). `UpdateWeapon` leaves the pack
  alone while an override is set. `Override(nil)` clears it.
- **Idle variants:** Offensive Idle while the Character has `HasSportBall`; Goalkeeper Idle while
  `Sports.State().Keeper` and `.InZone`; else Soccer Idle. Swapped with `UpdateTrack("Idle", ...)` and the Idle
  priority set again.
- **The keeper:** while `Keeper` and `InZone`, the override also carries the step tracks and `KeeperStep`. Going in or
  out of the zone re-applies the override.
- **Leaving:** `Override(nil)`, any soccer track stopped, then the pack Transformation's `restorePack` would pick:
  the weapon pack when the Humanoid has `Equip` and the Character a `Weapon`, else Default.
- **Cadence:** every rate goes through `Functions.Locomotion.Rate`, capped at `CadenceMax` (2.4).

## 6. Error handling
- A missing `NHSoccerClips` entry or a failed `RegisterKeyframeSequence` falls back to `Was`, then the procedural pose,
  and warns once per clip.
- A missing `Config.SoccerClips` means no timing data: clips play from 0 at 1x and the 1.1 dashes run.
- A clip that fails to load never blocks the server's move: the pose is visual only.
- If the Idle or Jog slot can't resolve, the Soccer pack isn't applied (the Default pack stays).
- Leaving a match mid-move stops every soccer track and the dash before the pack is restored.

## 7. Testing (slot 2 rules: a fresh snapshot each Play round, restore only from it, record CineState / Seen / Origin before and after)
- **Pure check `soccer_pure.lua`** (VM, no instances): `Functions.SoccerAnim` start times, hold and creep, windows,
  fit (rate cap and dash time), progress (0 at `t0`, 1 at `t1`, monotonic), kick and dive slot picks.
- **Edit check `soccer_clips_edit.lua`:** 25 clips in `NHSoccerClips`, each with a `Config.SoccerClips` entry; Loop and
  Path clips drift < 0.1 stud on X/Z (Loop: after the ramp); `Contact` markers within 1 frame of the table; the
  mirror's fastest limb around contact is the Right Leg; the loop flags; strides between 3 and 9.
- **Play check `soccer_play_client.lua`** (a solo match started with `Matches.ForceStart("Pitch", {P}, {}, true)`):
  the pack goes on with `InSport` and off when the match ends; the Idle and Walk tracks are the FIER clips; Offensive
  Idle with the ball; a kick's `TimePosition` at `S_Kick` is `ContactAt − 0.05` (±0.02 s); a dribble moves 11 studs
  ±10 %; the Walk rate follows `Rate(...)` within 5 %; the weapon pack is back after the match.
- **Look and feel:** a recorded match (jog, charged shot, running shot, pass, spin, tackle and fall, keeper dive and
  catch), then `motion_audit.py`, `jitter_audit.py` and `physics_audit.py`. The jog's planted foot skates < 0.6
  studs/s; no frozen frames during the creeping hold. Screenshots under
  `docs/superpowers/mockups/2026-11-24-soccer-2-0/`, and the owner watches it at full speed.

## 8. Settled during planning (2026-11-24, from the Studio code)
1. **The dribbled ball** is welded to the carrier (`Services.Sports.Ball`), so it follows any dash.
2. **The keeper flag** is the client's own match state: `Sports.State().Keeper` and `.InZone`. No new attribute.
3. **Events:** tackled = `S_Stolen` (`From` lost the ball, `Push` is the shove); broken ankles or a failed tackle on a
   feint = `S_Ankles` (`Player` is the one who falls); the stun ends at the Character's `SportStun` (server time).
4. **The directional walk** keeps the strafes in `AnimationController`'s `Directional` table and plays the backpedal as
   the Walk track at a negative rate; `Override` adds a `Back` entry and swaps `Left` / `Right` there.
5. **1.1 dive side bug:** `S_Dive` passed `-Side` to the pose, so a filled dive slot would have played the wrong side.
   2.0 picks the slot from the side directly (`DiveSlot`).
