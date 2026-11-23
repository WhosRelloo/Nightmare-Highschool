# Strafe walks + NPC gestures: design (phase6, Studio queue item 2)

- **Status:** design. Not built.
- **Branch:** `phase6-strafes` in the worktree `E:\NH-strafes`, cut from `phase6-tutorial` (the cine flags
  `NHApproach`, `NHCineSeam`, `NHCineHold` and `NHInCine` live there).
- **Research:** `docs/superpowers/research/2026-11-22-strafes-npc-gestures-survey.md`. All numbers quoted here come
  from it or from the measurements in §1.2. The survey was read-only.
- **Version:** decided at merge, after the tutorial (2.35.0) and the Bell Tower R2 (2.37.0). Probably 2.38.0.

## 0. The owner's rulings (2026-11-22)

1. **Counter-rotated strafes:** bake copies of both strafe clips with the chest squared to face forward and the legs
   untouched.
2. **Strafe speed:** movement slows to about **8.5 studs/s** while strafing, in lock-on, shift lock and first
   person.
3. **Injured and dizzy idles go in both places:**
   - the get-up reaction after being downed, now;
   - **a new Nurse NPC with an infirmary spot**. Neither place has an infirmary, so one is added (§6).
4. **Seated cheering:** add bleacher seats, and give the Athletes a "watch the match" scheduled job.

Second round of rulings (2026-11-22, later):
5. **The stride fix applies to walk, sprint AND crouch**, capped at 2.4x playback (`CadenceMax`).
6. **The Nurse treats players.** It's gameplay, but kept **minimal and pluggable** (§6.4): an `Infirmary.Treat(Player)`
   entry point, the bandage interaction and its gestures, with the heal amount and rules behind a tiny interface.
   - **An in-depth injury system** (custom injury models per body type) is coming as its own design and plan, and will
     replace that interface.
   - **This build makes no injury states, injury visuals or injury models.**
7. **Players can sit on the bleachers too** (§7.1).
8. **The Nurse is "Nurse Agatha Thorne".**
9. **The Praying kneel-in** (the stand-up reversed, slower) is accepted provisionally, as an owner-visual row (§12).

The coordinator's defaults:
- A reversed Walk is the backward walk for now.
- Touch and gamepad strafe whenever the same modes are active.
- The player's Walk playback-speed finding gets a fix if it's real. It is real (§1.2).

House style, for every clip:
- realistic legs, planted feet, no skate, weight;
- reuse the existing clips;
- the R6 rig (`r6-animation-cinematics`).

**FIER ANIMATIONS is read and copy only.** Never modify or save it.

---

## 1. Player locomotion: strafes, the backward walk and stride-matched cadence

### 1.1 Where it lives
- **`Controllers.Character.AnimationController`** (client) keeps owning locomotion.
- **New: `ReplicatedStorage.Functions.Locomotion`.** Pure: no services, no instances, so it's testable in a VM.
- **New: `ReplicatedStorage.Config.Locomotion`.** The numbers.
- **The strafe tracks:** `ReplicatedStorage.Assets.Animations.Movement.StrafeLeft` and `.StrafeRight`.
  - These are shared Animation instances beside Crouch and CrouchWalk, not one per weapon pack.
  - AnimationController loads them **outside `TrackTable`**, in a `Directional` table.
    - `SetTracks` clears `TrackTable`, and the `UpdateWeapon` path runs `StopAllTracks` first.
    - So the directional tracks are re-created after every `SetTracks`, through a small `LoadDirectional()` it calls
      at its end.
  - They load at **`Core`** priority with **`Looped = true`**. The clips are published Loop=false at Action.

### 1.2 Measured strides (fact base)
- **Method:** forward kinematics with the standard R6 Motor6D C0 and C1, sampled at 120 Hz.
- **Stride:** two times the largest horizontal distance between the feet, divided by the cycle length, in studs per
  second at 1x on 2-stud legs.
- **Cross-checks:**
  - The stance-foot velocity agrees within about 10 %.
  - NPCs were measured live at 5.3 studs/s on 1.8-stud legs, which is 5.9 on 2-stud legs.

| Clip | Id | Length | Stride, 1x, 2-stud legs | AnimationController divisor now | Correct divisor at 1.615-stud legs |
|---|---|---|---|---|---|
| Walk | 113454991107499 | 1.17 s | **5.9** (6.08 raw) | 10 | 4.8 |
| Sprint | 71702488451945 | 0.58 s | 13.5 (13.88) | 24 | 10.9 |
| CrouchWalk | 112732055140240 | 1.33 s | 3.5 (3.59) | 7 | 2.8 |
| FastSprint | 126968549934352 | 0.50 s | 18.0 (18.53) | 30 | 14.5 |
| Strafe L/R | 126969213208550 / 84541589738848 | 1.03 s | 5.8 (5.95) | none | 4.7 |

- **Finding: real.** Every player gait plays at about half the cadence its ground speed needs, so the feet skate
  forward about 2x.
  - At 14.4 studs/s, Walk plays at 1.44x and should play at about 3.0x.
  - NPCs are already correct: `AI.AI.Animate` and Schedules use speed / 5.3 times their stride factor.
- **The fix:** `Functions.Locomotion.Rate(GroundSpeed, Stride, LegLen) = GroundSpeed / (Stride * LegLen / 2)`.
  - It's clamped to `[Config.CadenceMin, Config.CadenceMax]`.
  - The leg length comes from `Character["Left Leg"].Size.Y`, read once per character and again on the `Height`
    attribute change.
- **Risk: a fast cadence.** A 14.4 studs/s "walk" on 1.6-stud legs is really a jog. At a full stride match it plays
  about 3x, which reads as speed-walking.
  - The cap `CadenceMax = 2.4` leaves about 20 % slide at 14.4, against about 50 % today.
  - **Owner ruling: ship the stride fix for Walk, Sprint and Crouch (and FastSprint, which uses the same rule), capped
    at 2.4x.** The footcheck numbers and screenshots go in the report as an owner-visual row (§12).
- **CineActor stays in step.**
  - `Controllers.CineActor`'s `STRIDE` table (Walk 10, CrouchWalk 7, Sprint 24, FastSprint 30) copies today's
    divisors.
  - It changes to read `Config.Locomotion.Stride` through the same `Rate` function, so cut approaches keep the same
    cadence rule as play.
  - **The tutorial's `approachcheck` must pass again after this** (§11).

### 1.3 When the directional blend runs
`Functions.Locomotion.StrafeMode(F)` returns true when all of these hold:
- `F.Gait == "Walk"`. Not Sprint, FastSprint, Crouch or CrouchWalk: those keep today's behaviour in v1.
- `F.Locked or F.MouseLocked or F.FirstPerson`:
  - `Locked`: `LockOn.Core.Locked() ~= nil`.
  - `MouseLocked`: `UserInputService.MouseBehavior == Enum.MouseBehavior.LockCenter`. That's shift lock (Left Alt);
    first person sets it too on mouse.
  - `FirstPerson`: the camera-to-head distance is under 1 stud. This covers touch and gamepad first person.
- No blocker. These keep the plain Walk:
  - the Character attribute `NHInCine`;
  - the Player attributes `NHApproach`, `NHCineSeam`, `NHCineHold` and `NHTutorial`;
  - the Character attributes `Transformation`, `WolfForm` and the Skateboard flag;
  - `StateManager` states `Dodge`, `Sliding`, `Ragdoll`, `Downed`, `Carried`, `Gripped`, `Gripping` and
    `Paralyzed` (the LockOn `BUSY` list);
  - a playing emote (`Controllers.Character.Emotes`).
- **Hysteresis:** the mode must hold for `Config.EnterHold` (0.12 s) to start, and the blend fades out over
  `Config.Fade` (0.15 s).

### 1.4 The blend
- **Each frame** (`RunService.PreAnimation`, only while moving in StrafeMode):
  - `Local = Root.CFrame:VectorToObjectSpace(Hum.MoveDirection)`, and `a = atan2(Local.X, -Local.Z)`.
  - **`Functions.Locomotion.Weights(a)`** returns `{ Walk = max(0, cos a), Back = max(0, -cos a), Left =
    max(0, -sin a), Right = max(0, sin a) }`, normalised to sum to 1.
- **Back** is the `Walk` track at a negative rate. With no backward clip, Back and Walk share one track, and the sign
  of the rate is the sign of `cos a`.
- **Rates:** each track's rate is `Rate(flat root speed, Stride[clip], LegLen)`.
- **Phase sync:** the strafe and the walk cycles differ (1.03 s and 1.17 s).
  - The secondary track is phase-locked to the dominant one: each frame its `TimePosition` follows the dominant
    track's phase plus `ContactPhase[clip]`.
  - `ContactPhase` is the baked left-foot-contact phase of each clip, exported by the baker into
    `Config.Locomotion`.
  - So the feet contact together on the diagonals (no foot mush).
- **Pose state:** AnimationController's single-pose model gets a pseudo-pose, `Walk8`.
  - While it's active, `PlayTrack` doesn't stop the Walk track. The weights drive it instead.
  - Leaving StrafeMode sets the Walk weight back to 1 over `Fade` and stops the strafes.

### 1.5 The speed rule (8.5 studs/s)
- **The server is authoritative.** The client tells the server when the blend starts and stops:
  - a new RemoteEvent `ReplicatedStorage.Remotes.NHStrafe`, `{ On = bool }`;
  - created by the server `Features.CombatSpeed` at start;
  - rate-limited to 10 a second per player.
- **The server sets the Character attribute `NHStrafing`.**
  - `CombatSpeed.apply()` caps the result: `if Strafing and Raw <= Config.WalkBandMax (20) and Raw > FLOOR then
    Want = math.min(Want, Config.StrafeSpeed (8.5))`.
  - It's a cap, so the hunger bands, a combat tag and kit slows still slow further.
  - It can only slow a player down, so trusting the client's boolean is safe.
  - It's cleared on character removal.
- **Latency:** for about one ping after the strafe starts, you move at the walk speed. That's accepted.
- **Strafe playback at 8.5:** on 1.615-stud legs that's 8.5 / 4.7 = **1.8x**.

### 1.6 Facing
Unchanged:
- LockOn still turns the root to the target.
- Shift lock and first person turn it with the camera.

Only the legs and the chest animation change.

---

## 2. The clip bake (repo tool, offline)

### 2.1 How the bake works
- **Extract.** `tools/phase6-strafes/anim/extract_fier.luau` runs **read-only** in the FIER ANIMATIONS Edit VM.
  - It serialises the chosen KeyframeSequences: Keyframe times, Pose names and parents, CFrame components, Weight,
    EasingStyle and EasingDirection.
  - Output: JSON at `tools/phase6-strafes/anim/src/<Clip>.json`.
  - It never writes to FIER. It's run through `rbxc.py luau "placeId: 107424155290133" Edit @…`, and the result is
    returned as text.
- **Bake.** `tools/phase6-strafes/anim/bake.py` (Python with numpy) reads `src/`, applies the transforms in §2.2
  from `anim/recipes.json`, and writes:
  - `anim/out/<Name>.lua`: a builder that creates the KeyframeSequence (the same shape as
    `tools/tutorial-anim/out/*.lua`);
  - `anim/out/manifest.json`: per clip, the length, loop flag, priority, contact phase, carry curve, scale bucket
    and checks;
  - `anim/REPORT.md`: a per-clip before/after table of the checks.
- **Test.** `tools/phase6-strafes/anim/test_bake.py` (pytest) checks every transform on synthetic clips. That's
  repo-only TDD.

### 2.2 The transforms
| Transform | What it does | Checks (in `test_bake.py` and `clipcheck.lua`) |
|---|---|---|
| `square_chest(KeepYaw = 0)` | Per frame: decompose the Torso pose's rotation about the RootJoint-space Z axis (the world vertical, by R6 RootJoint `C0`); remove the yaw (down to `KeepYaw`). **Legs:** recompute each Hip pose so the leg's world rotation is unchanged (`Pose' = rot((Torso' C0hip)^-1 Torso C0hip Pose)`), keeping the hip pivot (no leg translation is added, so no gap at the socket). **Head:** drop the head's counter-yaw too, so the head faces forward. Arms stay in torso space. | Torso yaw ≤ 1° on every frame; each leg's world rotation within 0.5° of the source; stance-foot velocity within 5 % of the source; the lowest foot Y within 0.05 of the source; seam 0 |
| `foot_lock` | After `square_chest`: the existing `tools/phase3-2260/anim/footlock.luau` method, ported as a Python pass. While a foot is the lowest and below contact height, hold its horizontal velocity at the stance value, so the feet are truly planted | Stance-foot jitter under 0.05 studs per frame |
| `loop_cut(Window, Blend)` | Find the frames a and b inside `Window` (for Praying: the kneeling part, torso drop under -0.8) with the smallest weighted pose distance and b - a at least 3 s. Cut [a, b] and bake a `Blend` (0.3 s) cross-blend of b toward a into its tail, so the loop is seamless | Seam ≤ 1°; no frame outside the window's drop band |
| `split(At)` | Praying → `PrayLoop` (the cut), `PrayStandUp` (b to the end, a one-shot) and `PrayKneelIn`: the time-reversed stand-up, retimed 1.15x slower with an ease-in on the first 0.2 s. Accepted provisionally by the owner; it stays an owner-visual row (§12). The ends match the loop's frames exactly, so the switches are frame-identical, as in the tutorial chains | The pose distance at each switch is 0 |
| `upper_body` | Keep only Head, Left Arm and Right Arm. Set the `HumanoidRootPart` and `Torso` Pose `Weight = 0` (they stay as parents), and drop both legs. The walk, idle or sitting underneath keeps the torso and legs | No leg poses; Torso and root weight 0 |
| `scale(k)` | Multiply every pose translation by `k` (the leg length / 2). Buckets: **k = 0.8, 0.9, 1.0**. Applied only to clips whose root drop is under -0.6 (Kneeling Inspecting, Gathering Objects, the Pray parts, Injured Hurting Idle) | The deepest knee or shin point on the matching rig sits within 0.05 of the floor |
| `strip_root(Yaw = true)` | Move the Torso pose's horizontal translation (RootJoint-space X and Y) and, with `Yaw`, its vertical-axis rotation into a **carry curve** `{ t, dx, dz, dyaw }` in root space at 10 Hz. Leave the vertical translation and the tilt. The runtime moves the root along the curve (§3.4) | Residual horizontal torso travel under 0.05 studs; the integrated carry equals the source travel (7.24 for Shove Reaction, 5.56 plus 159° for the spin version) |
| `decimate(15)` | For clips longer than 20 s (both Arguing takes, Talking On Phone and both phone-pacing clips), resample to 15 fps | Max joint error under 1° |
| `loop(true)` | Set `Loop = true` on every loopable clip (seam 0 in the survey) | n/a |

### 2.3 The baked set (the publish list)
Every piece is named `NHG_<Name>`. Every one is built into NH's `ServerStorage.NHGestures`, mirrored into
`ServerStorage.NHPublish.Gestures` for the owner to publish to group 15981569, and found afterwards with
`itemconfiguration…get-assets?assetType=Animation&groupId=15981569`, newest first.

| # | NHG_ name | Source (FIER folder / clip) | Transforms | Loop | Priority |
|---|---|---|---|---|---|
| 1 | StrafeLeft_Square | Walk / Stand Anims / Left Strafe Walking_R6 | square_chest, foot_lock, loop | yes | Core |
| 2 | StrafeRight_Square | … / Right Strafe Walking_R6 | square_chest, foot_lock, loop | yes | Core |
| 3 | Talk | Cinematic / NPC Gestures / Talking2_R6 | loop | yes | Action |
| 4 | TalkRant | … / TalkingGoinCrazy_R6 | loop | yes | Action |
| 5 | Argue_A | … / Standing Arguing_R6 | decimate, loop | yes | Action |
| 6 | Argue_B | … / Standing Arguing2_R6 | decimate, loop | yes | Action |
| 7 | Point | … / Pointing Forward_R6 | loop | yes | Action |
| 8 | PhoneTalk | … / Talking On Phone_R6 | decimate, loop | yes | Action |
| 9 | PhoneTalk_Upper | … / Talking On Phone_R6 | decimate, upper_body, loop | yes | Action |
| 10 | PhonePace | … / Pacing And Talking On A Phone_R6 | decimate, loop | yes | Action |
| 11 | PhonePaceWide | … / Talking Phone Pacing_R6 | decimate, loop | yes | Action |
| 12-14 | PrayKneelIn_{80,90,100} | … / Praying_R6 | split, scale | no | Action |
| 15-17 | PrayLoop_{80,90,100} | … / Praying_R6 | loop_cut, scale, loop | yes | Action |
| 18-20 | PrayStandUp_{80,90,100} | … / Praying_R6 | split, scale | no | Action |
| 21-23 | KneelInspect_{80,90,100} | … / Kneeling Inspecting_R6 | scale, loop | yes | Action |
| 24 | Inspect | Interaction Anims / Inspecting_R6 | loop | yes | Action |
| 25 | ReachDown | Cinematic / NPC Gestures / Reaching Down_R6 | loop | yes | Action |
| 26 | Rummage | Interaction Anims / Rummaging_R6 | loop | yes | Action |
| 27-29 | Gather_{80,90,100} | Interaction Anims / Gathering Objects_R6 | scale, loop | yes | Action |
| 30 | Shove_InPlace | Cinematic / NPC Gestures / Shove Reaction_R6 | strip_root | no | Action2 |
| 31 | ShoveSpin_InPlace | … / Shoved Reaction With Spin_R6 | strip_root(Yaw) | no | Action2 |
| 32 | InjuredIdle | Injured Anims / Injured Idle_R6 | loop | yes | Action |
| 33-35 | InjuredHurt_{80,90,100} | Injured Anims / Injured Hurting Idle_R6 | scale, loop | yes | Action |
| 36 | Dizzy | Idle Anims / Dizzy Idle_R6 | loop | yes | Action |
| 37 | LayingIdle | Idle Anims / Laying Idle_R6 | loop | yes | Action |
| 38 | CheerSeated_Upper | Cinematic / NPC Gestures / Cheering While Sitting_R6 | upper_body, loop | yes | Action2 (over Sitting) |
| 39 | Bored | Idle Anims / Bored_R6 | loop | yes | Action |
| 40 | SadIdle | Idle Anims / Sad Idle_R6 | loop | yes | Action |
| 41 | Duck | Idle Anims / Ducking_R6 | none (a one-shot) | no | Action2 |
| 42 | OrcIdle | Idle Anims / Orc Idle_R6 | loop | yes | Action |

- **That's 42 pieces.**
- The scale buckets can shrink to two (90 and 100) if `scaleprobe` (§11, task S2) shows that the 80 bucket isn't
  needed.
- **The strafes are a new publish too** (1 and 2). Until they're published, AnimationController uses the two
  published originals (126969213208550 / 84541589738848). In Studio it uses the `NHG_` KeyframeSequences through
  `RegisterKeyframeSequence`.

---

## 3. NPC gestures

### 3.1 `ServerScriptService.Services.AI.StudentBrain.Gestures` (new)
- **The pattern is `StudentBrain.Nudges`:**
  - `idOf(Name)` returns the published id from `Config.Gestures.Clips[Name].Id`.
  - Otherwise, **in Studio**, it registers `ServerStorage.NHGestures[Name]` with
    `KeyframeSequenceProvider:RegisterKeyframeSequence`.
  - Otherwise it returns nil, and the gesture is skipped on live servers until published.
- **API:**
  - `Gestures.Play(S, Name, Opts?) -> AnimationTrack?`
    - `Opts`: `Seconds`, `Fade` (0.25), `Speed`, `Weight`, `Carry` (bool), `Force` (bool: ignores the cap, for
      reactions and scenes).
  - `Gestures.Stop(S, Fade?)`.
  - `Gestures.Busy(S)`.
  - `Gestures.Pick(S, Hook, Ctx) -> Name?`: a pure pick through `Functions.Gestures`.
  - `Gestures.Scaled(S, Base) -> Name`: picks the `_80`, `_90` or `_100` bucket from the student's
    `Left Leg.Size.Y / 2`.
- **Tracks** load into `S.Tracks[Name]`.
  - Schedules' `Local.Pose(S, nil)`, which every `WalkTo` calls, already stops every non-locomotion track in
    `S.Tracks`. So a student who walks off ends the gesture with no extra code.
  - `Gestures.Play` refuses while `S.Agent.Moving`, `S.Reacting` (unless `Force`), `S.Seated` (only for clips not
    marked `Seated`) or `S.Leaning`.
- **Conflicts:** while a gesture plays,
  - `NpcBuilds.SetPosture(S.Model, false)` is called (straight posture: it moves joints too) and restored after;
  - the phone fidget's shoulder `C0` override is never applied.
- **Caps** (`Config.Gestures.Caps`):
  - `MaxActive` = 6 server-wide (`Force` ignores it);
  - `NearRange` = 60: a player must be within it, the same as `Brain.Idle`;
  - `Cooldown` = 20 s per student;
  - `StopFar` = 80: a looping gesture stops when no player is within it.
- **Studio-only probe:** `ServerStorage.NHGestureProbe`, a BindableFunction created by Gestures itself
  (`RunService:IsStudio()`). It's for the checks. It's not `NHTestBridge`, which is never edited.

### 3.2 `ReplicatedStorage.Config.Gestures` and `Functions.Gestures`
- **`Clips[Name]`:** `{ Id = 0, Src = "<FIER path>", Len, Loop, Priority, Legs, Seated, Upper, Carry = {…}?,
  Buckets = {80, 90, 100}?, ContactPhase? }`. The baker's `manifest.json` fills it.
- **`Cast`:** a list of rules `{ Hook, Who = { Clique?, Role?, Npc?, Activity?, Segment?, Temper?, Attitude? },
  Clips = { {Name, Weight} }, Chance }`.
- **`Functions.Gestures.Pick(Rules, Hook, Ctx, Rng)`** is pure. Its rules:
  - match all of `Who`;
  - weighted pick;
  - nil when nothing matches or the `Chance` roll fails.
- It's tested in a VM (`gs_pure.lua`).

### 3.3 The hooks
| Hook | Where | What |
|---|---|---|
| `Fidget` | `StudentBrain.fidget` | A `{ "Gesture", w }` entry in the pool. Its weight comes from the clique's `Cast` rules (0 when none match). Seated students get only `Seated` clips |
| `ChatSpeaker` / `ChatListener` | `StudentBrain.chat(A, B)` | Each line, the speaker plays `Talk` or `TalkRant`, and the listener `Bored`, or `SadIdle` for the Shy temper. Both stop on `Brain.Urgent` or any movement (the checks already there) |
| `Argue` | `chat(A, B)` with `Talk.Attitude` Hostile or Wary, or rival cliques (`Config.Cliques`); the `Argument` scene | `Argue_A` on A and `Argue_B` on B, started together (a paired take) |
| `Phone` | `StudentBrain.fidgetPhone` | Standing: `PhoneTalk`. At a Linger or Mingle spot with 2.5 studs clear (raycasts): `PhonePace`, or `PhonePaceWide` with 3.5 studs. The phone Tool stays; the `PHONE_POSE` C0 override is skipped |
| `PhoneWalk` | Schedules `Local.WalkTo` during `Passing` (20 % of walks) | `PhoneTalk_Upper` over the walk, with the Tool in hand; stopped at arrival |
| `Scene` | `World.Scenes`: a new step op `{ "anim", CastIdx, Name, Seconds? }` | Argument: Argue_A and Argue_B. Locker: `Shove_InPlace` on cast 2 (replaces the bare `fx`), with carry. Notice: `Point` on cast 1. Dare: `ReachDown` on cast 2. EastWing: `Duck` at "Footsteps..." |
| `Post` | `Social.Npcs`, staff at their post with a player near | Custodian: `Rummage`, `Gather_*`, `ReachDown`. Teachers: `Point`, `Talk`. Ashgrave: `Inspect`. Coaches: `Point`. Nurse: §6 |
| `Confront` | `School.HallMonitor`, entering Confront | `Point` (once) |
| `Gawk` | `React.Gawk` near a Scuffle | 25 %: `TalkRant` (egging it on) |
| `Danger` | `React.Danger` with a Beast or a transformed player | `Duck` before backing away |
| `ScuffleLoser` | `Social.CliqueFights` | `Shove_InPlace` or `ShoveSpin_InPlace` with carry |
| `Hangout` | Schedules `Local.Linger` by clique | Choir at The Chapel: `PrayKneelIn`, then `PrayLoop` for 8-20 s, then `PrayStandUp`. Vigil at The Archive: `KneelInspect`, `Inspect`. Pack on moon nights: `OrcIdle`. Court and Delinquents: `Bored` |
| `Locker` | Schedules `Local.Mingle` near `School.Quests.HallwayProps.Locker*` | Face the locker, then `Rummage` for 4-10 s |
| `GetUp` | `Downed.OnRecovered` (§5) | Dizzy or InjuredHurt |
| `Watch` | Schedules `Local.Watch` (§7) | `CheerSeated_Upper` |

Nudges keeps its three custom bump clips; nothing above replaces them.

### 3.4 Root-motion carry (the shoves)
- **`Gestures.Carry(S, Curve, Seconds)`** moves the root along the baked curve.
  - It rotates the curve into the root's facing at the start.
  - It applies `dyaw` to the root.
- **Collision:** it uses the same wall and floor checks as `Nudges` (`clear`, `room`).
  - Those move into a shared `StudentBrain.Space` module, which Nudges and Gestures both require.
  - **The carry stops short of walls**, and the clip still plays (as Nudges does).

### 3.5 Reduce Motion
- `NHReducedMotion` governs camera and UI motion. NPC character animation isn't camera motion, so gestures and the
  strafes don't change under it.
- The client's procedural Stretch fidget keeps its existing Reduce Motion skip.

---

## 4. The casting table (v1)
| Who / when | Hook | Clip(s) |
|---|---|---|
| Clique chatter (any clique) | ChatSpeaker / ChatListener | Talk, TalkRant / Bored, SadIdle |
| Arguments (Hostile, Wary or rival pairs; the Argument scene) | Argue, Scene | Argue_A + Argue_B |
| Students between classes | Phone, PhoneWalk | PhonePace, PhonePaceWide (at a spot); PhoneTalk; PhoneTalk_Upper (walking) |
| Choir at The Chapel | Hangout | PrayKneelIn, PrayLoop, PrayStandUp (bucketed) |
| Athletes seated at a match | Watch | CheerSeated_Upper over Sitting |
| Athletes standing (Club) | Fidget | Point |
| Staff and the Vigil (The Archive) | Hangout, Post | KneelInspect (bucketed), Inspect |
| Lockers | Locker | Rummage |
| Custodian (by day) | Post | Rummage, Gather (bucketed), ReachDown |
| Shoves at incidents | Scene (Locker), ScuffleLoser | Shove_InPlace, ShoveSpin_InPlace (+ carry) |
| Get up after being downed (NPCs) | GetUp | Dizzy, InjuredHurt (bucketed), InjuredIdle |
| Nurse's office: patients | Infirmary (§6) | LayingIdle (on a bed), InjuredIdle, Dizzy |
| Nurse | Post (§6) | Inspect, KneelInspect (at the bed), ReachDown, Talk |
| Danger and monsters | Danger | Duck |
| Fight onlookers | Gawk | TalkRant |
| Hall monitor confronting | Confront | Point |
| Teachers and coaches at posts | Post | Point, Talk (Ashgrave: Inspect) |
| Notice and Dare scenes | Scene | Point; ReachDown |
| The Pack on moon nights | Hangout | OrcIdle |
| Court and Delinquents | Hangout, Fidget | Bored |

Later (v2, not in this plan):
- the door clips with `Features.Doors`;
- Left/Right Turn 90 for the brain's "Shift";
- NPC strafes for `React.Space` and monitors closing in.

---

## 5. The get-up reaction (after being downed)
- **The hook:** `Downed.OnRecovered(Target)` connects in `StudentBrain.Gestures`.
- **Who it applies to:** only when `Target` is **not a player's character**, and is either
  - a scheduled student (`NHScheduled`), with its record from `Host.Students()`;
  - or a `Social.Npcs` NPC (`NpcId`).
- Combat AI (delinquents, beasts) and players are untouched: a server clip on a player would fight their controls.
- **Students:**
  - Set `S.Reacting = true` for `GetUp.Seconds` (5-8 s), stop the Agent, and play `Dizzy` (60 %) or the scaled
    `InjuredHurt` (40 %).
  - Then mark `S.SickUntil = now + Config.Infirmary.VisitAfter` (an in-game hour), so the next `Replan` walks them to
    the infirmary (§6.3).
- **Staff:** the same clip, standing at the post.

---

## 6. The infirmary and the Nurse

### 6.1 Where
- **Neither place has an infirmary.**
  - NH Combat Test has no Infirmary instance or region.
  - The Map place has only a showcase plaque (`Workspace.Signs.BrassPlaque_ShowcaseInfirmary`) and the Signs kit's
    `Infirmary` preset. Its region boxes match NH's, with no infirmary.
- **The spot:** the **free lot on the south side of the hallway extension, opposite R106.**
  - Centre (214, 6, 24), about 26 x 24 studs (x 201-227, z 12-36).
  - It sits between BoilerYard (x 167-197) and the east end. Its north wall faces the hallway extension (z 44-58).
  - `GetPartBoundsInBox` there finds **no parts**; the floor ray hits `Map.Baseplate` at y 0.9.
  - The room is built in NH Combat Test only, in the same greybox as R106 (`School.R106`'s parts are the template).
- **Before building,** a read-only look at the Map place confirms the spot doesn't clash with its real layout
  (task S1). If it clashes, the fallback is the StaffRoom's west half (StaffRoom region, x 53-81).

### 6.2 The build (Studio task)
- **`workspace.School.Infirmary`** (Model) contains:
  - `Floor` (y 1.1), the walls `WallWest`, `WallEast`, `WallSouth`, `WallNorthL`, `WallNorthR` and `WallNorthTop`,
    and a `Door`;
  - `Zone` (a BasePart with `RoomId = "Infirmary"`);
  - `Sign`, the Signs kit preset `Infirmary`;
  - the markers `NHPropSpot_*`, `NpcPost` (`Nurse`), `NHInfirmaryBed1` and `2` (each with `SeatHeight`), and
    `NHInfirmarySpot1` and `2` (standing patients).
- **Props, reused from `ServerStorage.NHProps`:** 2 x `DormBed`, 1 x `GlassCabinetTall`, 1 x `FilingCabinet`,
  1 x `TeacherChair`, 1 x desk (as R106's `TeacherDesk`). Placed by `tools/phase6-strafes/build/infirmary.luau` in
  Edit.
- **The region:** a new `workspace.Regions` box `Infirmary` (26 x 14 x 24, the same height as R106's), and
  `Config.Regions.Defs.Infirmary` (Title "The Infirmary", Priority as R106's).
- **The rest is untouched:** the door kit, `Features.Doors` and the Map place's builds. The Map place is read-only.

### 6.3 The Nurse NPC and the patients
- **`Config.Npcs.Nurse`:**
  - Name **"Nurse Agatha Thorne"** (owner).
  - `Role = "School Nurse"`, `Dialogue = "Nurse"`.
  - `Posts = { Homeroom = "Nurse", Class = "Nurse", Other = "Nurse" }`, so she's in during the school day and off
    campus otherwise.
  - Color: muted teal (`Color3.fromRGB(110, 160, 150)`).
- **Dialogue:** a new `ServerStorage.Dialogue.Nurse` tree, short:
  - a greeting by time of day;
  - "You don't look good." when the player is Wounded (`NHWounded`) or under 50 % health;
  - a rumour line (from `Social.Rumours`, as other talkables do).
  - **A "Get patched up" choice** in her dialogue (and her `ProximityPrompt`) calls `Infirmary.Treat(Player)` (§6.4).
- **Her idle:** a `Post` loop alternating `Inspect` at the cabinet, `KneelInspect_*` beside an occupied bed,
  `ReachDown`, and `Talk` when a player is within 8 studs.
- **Patients:**
  - Students with `S.SickUntil` (§5) get an `Infirmary` job from `Schedules.Replan` before their normal segment job:
    - walk to a free `NHInfirmaryBed` and lie or sit with `LayingIdle`, or to an `NHInfirmarySpot` with
      `InjuredIdle` or `Dizzy`;
    - for 60-120 s (real time), then back to the segment job.
  - With no sick students, one **ambient patient** (a `Features.AmbientNpcs` scenery figure, anchored, no AI) lies on
    bed 1 with `LayingIdle` during school hours.

---

### 6.4 Treating players (minimal and pluggable)
**Scope:** an entry point, the interaction and its gestures. The rules sit behind a small interface (`Care`) that the
coming injury system replaces. **Nothing here adds injury states, visuals or models.**

How health works today (read 2026-11-22), which this fits in with:
- **Out-of-combat regen:** `Player.Progression` regenerates 2 % of MaxHealth a second once `CombatTagUntil` has
  passed. It doesn't run while downed (`DownedUntil`), in the main menu, or while `NHChilled`.
- **Low-health regen:** a race or bloodline effect (`LowHealthRegen`) below 30 %.
- **Max health:** `MaxHealth` is 100 plus the Effects bonus.
- **The Kit bandage:** `Features.Kit` `Local.Bandage` channels `Kit.Aid.Channel` seconds at `Kit.Aid.ChannelSpeed`
  (it sets `NHKitSlow`), cancels on a hit or a down, and heals `Kit.Aid.Heal` over `Kit.Aid.Duration`.
  - It sets `NHBandagedUntil = now + Kit.Aid.Clears` and clears `NHWounded`.
  - `NHWounded` is Kit's own flag: under the `Kit.Wounded.Threshold` of health, and not bandaged. It slows walking
    10 % through CombatSpeed.

**New: `ServerScriptService.Services.Features.Infirmary`:**
- **`Infirmary.Treat(P) -> (ok, reason?)`** is the only entry point. The Nurse's `ProximityPrompt` and her dialogue
  choice call it, and so will the injury system later.
- **It asks `Infirmary.Care.CanTreat(P)`, then runs the interaction:**
  - Face each other.
  - The player is planted (`NHKitSlow = 0.01`) and plays the Kit's existing `FirstAid` clip (93493041203096). That's
    reuse, not a new clip.
  - The Nurse plays `Inspect`, then `ReachDown`, through Gestures, with `Force`.
  - It lasts `Config.Gestures.Treat.Seconds` (3 s).
- **It cancels** on damage (health drops), on being downed, on walking more than 6 studs away, or on a combat tag
  starting. The message is "Hold still."
- **On completion,** `Care.Apply(P)` runs.
- **The interface, `Infirmary.Care`:** a child ModuleScript, the default that the injury system swaps out.

| Member | Default rule (tunables in `Config.Gestures.Treat`, every one flagged "owner default") |
|---|---|
| `CanTreat(P) -> (bool, string?)` | refused if combat-tagged ("Not while you're fighting."), downed or carried ("Lie still, help is coming."), on cooldown (`Cooldown` 180 s per player: "Come back in a few minutes."), or at full health and not `NHWounded` ("You're fine. Off you go.") |
| `Apply(P)` | `Health = MaxHealth` (`Heal = "Full"`); `NHBandagedUntil = now + Kit.Aid.Clears`; `NHWounded = nil`; start the cooldown |
| `Cost(P) -> number` | 0 (`Price = 0`, free) |

- **Server-authoritative.** It's reached only through the Nurse's `ProximityPrompt` (`MaxActivationDistance` 8) and
  the dialogue choice, the same proximity and dialogue pattern as the other talkables (`Social.Npcs` and
  `Social.Dialogue`).
- **Cooldowns** are kept per player for the session; they're not saved.
- **A Studio-only seam** is added to `NHGestureProbe`: `Treat(PlayerName)` and `ResetCooldown(PlayerName)`.

## 7. The bleachers and the "watch the match" job

### 7.1 Seats
- **Survey first (S1, read-only):** the bleacher geometry under `workspace.Sports.Gymnasium.Stands.Bleacher*` and
  `School.Quests.Ring.Bleachers`: the rows, the seat-top heights, and whether they take queries.
- **Bleacher seats are small seat "props":** one Model `BleacherSeat_<n>` per sitting place, so both the NPC and
  the player seat code treat them like chairs.
  - Each holds an invisible anchored `Base` part (CanCollide, CanQuery and CanTouch off; Transparency 1), with its
    pivot on the step and facing the court.
  - Attributes: `SeatHeight` (the step's top above the pivot) and `Venue`. Tagged `NHBleacherSeat`.
  - They're placed by `tools/phase6-strafes/build/bleachers.luau` in Edit, under `workspace.Sports.<Venue>.NHBleacherSeats`.
  - `Seats.Kind` already returns `BleacherSeat` from the name prefix, and `Seats.Height` already honours
    `SeatHeight`.
- **Players (owner):** `Features.PlayerSeats` `KINDS` gains `BleacherSeat = true`.
  - Every bleacher seat gets the same invisible Seat and "Sit" prompt as the classroom chairs.
  - The client's `Controllers.World.PlayerSeat` plays the students' Sitting pose and settles the hips (unchanged).
  - A seat a student is on or heading for refuses (`Schedules.ChairTaken` covers bleacher seats too), and students
    skip a seat a player sits in (`PlayerSeats.IsOccupied`).
  - **Players don't get the cheer** in v1; it's for NPCs only.

### 7.2 The job
- **`Schedules.Local.Watch(S, Job)`:**
  - **When:** a `Sports.Matches` match is live (its public state is read in the dump task). Every Athlete not on a
    team that match, and up to 4 other students during After School, walks to a free `NHBleacherSeat` near that
    venue.
  - **There:** they sit through `Local.Sit` (the `Sitting` clip), then loop `CheerSeated_Upper` at Action2 over it.
  - **Bursts:** on a score event they get 3 s of full-speed cheering; otherwise 0.6 weight with speed 0.8, and 25 %
    of watchers rest (no cheer).
  - **When it ends:** at the match's end, `Local.Unseat`, then the normal job.
- **`Local.OnSegment`** assigns `Watch` instead of `Club` or `Hangout` while a match is live.
- **Nobody is pulled out of class.**
- **Gym club time with no match:** 30 % of the Athletes at the Gymnasium sit and watch the practice for a while with
  the same cheer at 0.4 weight.

---

## 8. Performance
- **Students:** 24 rostered students, with bodies only within 160-180 studs of a player (`Schedules.SleepWake`).
  - Gestures add at most one track per student, cached in `S.Tracks` and gone with the body.
  - `MaxActive` 6 and `NearRange` 60 limit replication.
  - The long clips are decimated to 15 fps.
- **The infirmary:** at most 1 nurse, 2 bed patients, 2 standing patients and 1 ambient patient.
- **The bleachers:** at most 3 Athletes plus 4 others per venue.
- **The client:** the strafe blend is one `PreAnimation` connection, live only while moving in StrafeMode, with
  three tracks.

---

## 9. What each file changes (summary)
- **New:**
  - `Config.Locomotion`, `Functions.Locomotion`, `Config.Gestures`, `Functions.Gestures`;
  - `StudentBrain.Gestures`, `StudentBrain.Space`;
  - the infirmary and bleacher builders, the bake tools and the checks.
- **Changed:**
  - AnimationController, CineActor (`STRIDE`), CombatSpeed (the remote and the cap);
  - StudentBrain (fidget, chat, Gawk, Danger), Nudges (it uses Space);
  - Schedules (PhoneWalk, Linger, Mingle, Watch, Infirmary, Replan);
  - Scenes (the `anim` op), Config.Scenes, Social.Npcs (Post), Config.Npcs (Nurse), HallMonitor (Confront),
    CliqueFights (ScuffleLoser), Downed (nothing: Gestures connects to `OnRecovered`);
  - Seats (Bleacher), Config.Regions (Infirmary), AmbientNpcs (the patient);
  - `ServerStorage.Dialogue.Nurse` (new).

---

## 10. Open questions for the owner
All of the first round's questions are answered (§0, rulings 5-9).
1. **Treat defaults** (§6.4): free, 3 s, a full heal, refused in a fight or while downed, a 3-minute cooldown. These
   are the owner's defaults as set by the coordinator, all tunable in `Config.Gestures.Treat`. Confirm them after
   playing.

## 11. Verification (summary; the plan has the steps)
- **Pure checks in a VM:**
  - `lc_pure.lua`: Weights, StrafeMode, Rate and the gate list;
  - `gs_pure.lua`: Pick.
- **Offline:** `test_bake.py` (pytest) for every transform.
- **Edit:** `clipcheck.lua` (the 42 KeyframeSequences: lengths, loops, seams, the square-chest yaw, upper-body
  weights, scale knees) and `infirmarycheck.lua` (the room, the region, the posts and the beds).
- **Play:**
  - `scaleprobe.lua`: does R6 rescale translations? It decides the buckets.
  - `strafecheck.lua`: a forced mode through the Studio-only Player attribute `NHStrafeTest`; the weights; the speed
    is about 8.5; the stance-foot slip is under 0.6 studs/s.
  - `footcheck.lua`: Walk, Sprint and Crouch slip before and after.
  - `cinegate.lua`: with `NHApproach`, `NHCineSeam` or `NHInCine` set, the strafe weight stays 0.
  - `gesturecheck.lua`, `getupcheck.lua`, `nursecheck.lua`, `watchcheck.lua`;
  - `healcheck.lua`: Treat's refusals and the full heal;
  - `playerseatcheck.lua`: a player sits on a bleacher seat, and a student skips it.
- **The tutorial regressions,** in the owner's order: `phase6-2350` `skipcheck` first, then `approachcheck` (after
  the `STRIDE` change), with `bodycheck` and `dipcheck` last.
- **Screenshots** for the owner: the strafe in lock-on (square chest), the walk cadence before and after, Praying,
  the infirmary, the bleachers.

## 12. Owner-visual rows (to judge in the T6 screenshots)
| Row | What to look at |
|---|---|
| V1 | The square-chest strafes in lock-on: the chest faces the target, the feet stay planted |
| V2 | Walk, Sprint and Crouch cadence at the 2.4x cap: how much slide is left |
| V3 | The Praying kneel-in (the stand-up reversed, slower): accepted provisionally |
| V4 | The infirmary greybox and its props |
| V5 | Treat: the bandage gestures on both sides |
| V6 | Athletes cheering on the bleachers; a player seated beside them |

## 13. Build deltas (phase6-strafes build, 2026-11-22)
1. **Infirmary position:** re-measured in NH. It spans x 199–225 and z 13.5–39.5 (centre 212, 26.5), with the door at
   x 215–219. The earlier centre, (214, 6, 24), would have run into the hallway's edge props. The Map place was
   closed during the build, so it wasn't re-surveyed. Neither place has an infirmary.
2. **Treat slows the player rather than freezing them.** It sets `NHKitSlow` to 0.3, because CombatSpeed clamps it
   at 0.3. That's the Kit bandage's way.
3. **Bleachers:** 64 seats, at the Gymnasium (3 banks × 2 rows × 8) and the Field (1 bank × 2 × 8). The Pitch's
   mesh bleachers and the Ring's prop aren't seated in v1.
4. **The strafe strides use the planted-foot ground speed** (4.76 and 4.84), not the spread method. The spread method
   overstates a sideways step.
5. **The square-chest foot lock leaves the lowest foot 0.06 below the rest floor.** It's an R6 rigid-leg limit.
6. **The Praying stand-up** starts from the loop's end pose and eases into the source, so it doesn't replay the
   kneel. KneelIn is that stand-up reversed: 4.2 s; StandUp is 3.6 s.
7. **No local HTTP bridge:** the Studio Assistant refuses 127.0.0.1. `harness/pure.py` inlines the sources instead.
8. **Deferred:**
   - the AmbientNpcs patient lying on bed 1;
   - the phone Tool during PhoneWalk (the gesture plays without the phone prop);
   - `scaleprobe` (the scale buckets stay; R6 KeyframeSequence translations are absolute).
