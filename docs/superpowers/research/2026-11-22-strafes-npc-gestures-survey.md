# Survey: strafe walks + NPC gestures (phase6, Studio queue item 2)

Date: 2026-11-22. Read-only survey. Nothing was installed, edited, saved or played in any Studio place.

How it was read:
- **FIER ANIMATIONS** (107424155290133): in Edit, with read-only `execute_luau` walks of `workspace.*.AnimSaves`.
  - The pose maths was done on CFrame values only.
  - The two published strafe ids were fetched with `KeyframeSequenceProvider:GetKeyframeSequenceAsync`. The fetched
    copy was never parented, and it was destroyed straight away.
- **NH Combat Test** (98950102230473): another session had it in Play for the tutorial fix round.
  - Scripts were read from the running Server and Client DataModels with `script_read`, `script_grep` and `Source`
    reads.
  - Scripts and config don't change between Edit and Play, but the instance counts below are a snapshot taken during
    a tutorial Play round.
  - **Re-check anything load-bearing in Edit before building.**

---

## A. Movement (NH Combat Test)

### A1. Where locomotion is chosen today
- **`StarterPlayer.StarterPlayerScripts.Controllers.Character.AnimationController`** (client, 431 lines) is the custom
  controller.
  - `OnCharacterAdded` destroys the stock `Animate` script.
  - It then loads a pack: `ReplicatedStorage.Assets.Animations.Weapons.<Profile.Weapon>.Movement` when equipped, or
    `Default.Movement` otherwise.
  - Pose selection lives in the `Humanoid.Running` handler (lines 201-225), and runs on **speed only**:
    - `FastSprint` when WalkSpeed or speed is over 40, at speed / 30;
    - `Sprint` when over 20, at speed / 24;
    - otherwise `Walk`, at speed / 10.
  - Crouch: when the `Crouch` attribute is set, `CrouchPose` uses `CrouchWalk` at max(speed, 1) / 7, or `Crouch`.
  - Jump, Fall and Land are on their own events.
- **It never looks at direction.** `MoveDirection` against the facing is never compared, so moving sideways or
  backwards plays the forward Walk.
- `Animate:PlayTrack` keeps exactly one active pose (`self.Pose`), stops the old track and remembers its TimePosition.
  - Priorities are set in `SetTracks`: Idle and Jump use `Idle`; Land uses `Movement`; Walk, Sprint, FastSprint, Fall,
    Crouch and CrouchWalk use **`Core`**.
- On a weapon change (`ProfileUpdated` with `UpdateWeapon`), it runs `StopAllTracks()` (every playing track on the
  Animator), then `SetTracks(pack)`. That clears the whole `TrackTable` and re-kicks Walk.
- `Controllers.Character.InputController.Movement.Sprint` only fires `UnPackets.Sprint` with `Activate` or `Release`.
  - The server sets WalkSpeed: Walk is 12 to 14.4 (hunger bands; 14.4 live), Run is 25.
  - It also honours the `NHBeatNoSprint` attribute.
- `Movement.Dodge` is the only client code that reads direction (dot against Look and Right), for the 4-way Dash clips
  in `Assets.Animations.Movement.Dash` (LookVector, BackVector, LeftVector, RightVector).
- **Rig: R6** (`Humanoid.RigType` R6).
  - The player body is height-scaled: live, legs were 1.615 studs and the torso 1.85 x 1.74 x 0.93.
  - School NPCs use `ServerScriptService.Services.AI.AI.Rig`, a 0.9-scale R6 (torso 1.8 x 1.8 x 0.9, legs 1.8),
    plus `NpcBuilds` heights.

Movement ids now (the pack folders):

| Pose | Default / Fist | Katana | Claws / Transformation |
|---|---|---|---|
| Idle | 116858893264840 (Fist: 119260489965589) | 79627943505900 | 109833901087174 |
| Walk | 113454991107499 | 97636443549600 | 125327708143110 |
| Sprint | 71702488451945 | 81460407724092 | 71702488451945 |
| FastSprint | 126968549934352 | same | same |
| Jump / Fall / Land | 133312166780518 / 119185528677030 / 90775551383967 | Fall 180436148 | same as Default |
| Crouch / CrouchWalk | 139672322709288 / 112732055140240 | same | same |

There are no strafe or backward clips anywhere. `grep Strafe` and `grep 126969213208550` both return nothing.

### A2. Facing modes where strafes apply
Three modes keep the body from turning toward the move:
1. **Lock-on** (`InputController.Combat.LockOn.Core`).
   - Middle mouse toggles it, and only while equipped.
   - `Lock` sets `Humanoid.AutoRotate = false`, then on each `RenderStepped` turns the root to face the target (unless
     the player is busy: Dodge, Sliding, Ragdoll and so on).
   - It lets go when the target drops or is more than 40 studs away, on unequip, or in the main menu.
   - This is the clearest strafe case: WASD moves you camera-relative while your chest stays on the opponent.
   - Gamepad and touch get only a per-swing aim assist, with no continuous lock.
2. **Shift lock.** `StarterPlayer.EnableMouseLockOption = true`.
   - `Controllers.Character.ShiftLockKey` rebinds it to **Left Alt** (Left Shift is Sprint).
   - The stock CameraModule turns the character with the camera, and `UserInputService.MouseBehavior == LockCenter`
     while it's on.
3. **First person.** `CameraMinZoomDistance` is 0.5, so a full zoom-in also turns the body with the camera.

No other system faces the body while moving:
- Block doesn't touch AutoRotate.
- The Skateboard and the Football dive set AutoRotate off, but for their own movement: no strafes there.

**When to play the strafes:** on the local player whenever the move direction is mostly sideways relative to the root
(see A4). That only happens in the three modes above, because with AutoRotate on, the body turns into the move within
about 0.1-0.2 s.
- Add a short hysteresis (about 0.12 s) so a sharp turn in free camera doesn't flash a strafe frame.
- Also gate on the modes explicitly:
  `LockOn.Core.Locked() ~= nil or UserInputService.MouseBehavior == LockCenter or Hum.AutoRotate == false`.

### A3. Backward walk
- There is none. Moving back in lock-on or shift lock plays the forward Walk while the body slides backwards.
- Options:
  - (a) Play `Walk` at a negative speed (`AdjustSpeed(-k)`). It costs no new asset, but a reversed walk shows the
    heel-strike backwards.
  - (b) FIER `Jog Backward_R6` (Soccer Anims, 0.80 s, in place, seam 0) for a backpedal run.
  - (c) FIER `Injured Walk Backwards_R6` (1.67 s, loopable) is styled as injured, so not for normal movement.
- Recommendation: (a) now, and ask the owner for a real backward-walk clip if (a) reads badly.

### A4. What to change, and how to blend
- **File:** `Controllers.Character.AnimationController` only.
  - `SetTracks`: load `StrafeLeft` and `StrafeRight` at **`Core`** priority (the same layer as Walk), with
    `Looped = true`, because the published clips are Loop=false.
  - Best kept in a shared folder (`ReplicatedStorage.Assets.Animations.Movement.StrafeLeft` / `StrafeRight`, beside
    Crouch and CrouchWalk). If they go in each weapon pack instead, they must be added to Default, Fist, Katana, Claws
    and Transformation. `SetTracks` clears `TrackTable` and the pack swap calls `StopAllTracks`, so either re-add them
    after every `SetTracks` or keep them outside `TrackTable`.
  - `Humanoid.Running` handler: in the Walk band only (not Sprint, FastSprint or crouch), take
    `Local = Root.CFrame:VectorToObjectSpace(Hum.MoveDirection)` and `a = atan2(Local.X, -Local.Z)`.
  - Blend by weights rather than switching poses:
    - Walk weight `max(0, cos a)`;
    - StrafeLeft or StrafeRight weight `|sin a|`;
    - backward: Walk at negative speed, weight `max(0, -cos a)`.
    - Normalise the weights, keep all the active tracks playing (`AdjustWeight` each frame from a `PreAnimation` or
      `Heartbeat` step, not only on `Running` events, which lag), and fade the strafes out over 0.15 s when the mode
      ends.
  - `PlayTrack` has a one-pose model (`self.Pose`), so add a small "directional walk" state (`self.Pose =
    "Walk8"`) whose tracks are driven by weight, so `PlayTrack` doesn't stop them.
  - Crouch, Sprint, FastSprint, Jump and Fall keep the current behaviour. Sprinting sideways in shift lock stays the
    Sprint clip in v1.
- **Speed:** the strafe clips cover about **5.4 studs/s at 1x on a 2-stud leg**.
  - That was measured from stance-foot travel, using forward kinematics with the rig's own Motor6D C0/C1. Left:
    +5.41 X; Right: -5.34 X.
  - On the player's 1.615-stud legs that is about **4.36 studs/s at 1x**, so the playback speed is
    `speed / (5.4 * Leg.Size.Y / 2)`.
  - At WalkSpeed 14.4 that is **3.3x**, which looks frantic, and anything lower skates.
  - Recommendation: lower WalkSpeed while strafing (for example, 0.6 x walk, about 8.5 studs/s, about 1.9x), like
    most action games do in a lock-on.
  - This is an owner call (Q2). The same pace maths applies to Walk.
  - Aside: the player's `Walk` uses speed / 10 while NPCs measured the same clip at 5.3 studs/s at 1x on 1.8-stud
    legs. The player walk may play slow for its ground speed. Worth a dipcheck, but out of scope here.
- **Strafe clip shape:** read this before wiring.
  - Both clips turn the **torso about 58 degrees about the vertical axis toward the travel side** for the whole cycle.
  - The head turns back only about 15 degrees, and the legs cross over.
  - So in a lock-on the chest points about 58 degrees off the target and the head about 43 degrees off.
  - This is how RoMixamo's `Convert2R6` bakes a Mixamo strafe onto a non-bending R6 (the hips can't turn sideways).
  - The owner should see it in a viewport before it ships (Q1).
  - If it reads wrong, a counter-rotated variant (torso yaw reduced to about 20 degrees and the head brought to 0) can
    be baked with `tools/tutorial-anim/build.py` tooling.
- **Cinematics:** `Controllers.CineActor.Approach` sets `Hum.AutoRotate = true` and drives `Hum:Move`.
  - Each `PreAnimation`, it rewrites the speed of **every playing Core track whose `Animation.Name` is in
    `STRIDE`** (Walk, CrouchWalk, Sprint, FastSprint).
  - Strafes named `StrafeLeft` / `StrafeRight` would not be speed-controlled there, and if one were playing it would
    skate.
  - Gate the strafe blend off (Walk weight 1, strafes 0) whenever any of these is set:
    - `Character:GetAttribute("NHInCine")` (set by the server in `World.Cine`);
    - `Player:GetAttribute("NHApproach")`;
    - `Player:GetAttribute("NHCineSeam")`;
    - `Player:GetAttribute("NHCineHold")`.
  - Also gate on an `NHTutorial` lock if one is active.
  - With AutoRotate forced on during approaches, the angle test would rarely fire anyway, but the explicit gate makes
    it certain.
  - Do **not** add the strafes to `STRIDE`.
- **Published ids (checked read-only):**

| Asset | Name | Creator | Loop | Priority | Length | Keyframes |
|---|---|---|---|---|---|---|
| 126969213208550 | Left Strafe Walking_R6 | Nightmare Highschool (group) | false | Action | 1.033 s | 32 |
| 84541589738848 | Right Strafe Walking_R6 | Nightmare Highschool (group) | false | Action | 1.033 s | 32 |

  - They match the FIER sources.
  - **Set `Looped = true` and `Priority = Core` at load.** Left at Action, they would cover attacks' lower layers.
  - Both are in place: no root drift, and seam 0 (the first and last frames are identical), so they loop cleanly.
- **NPCs (extra):** the same strafes would suit students backing off.
  - `React.Space`'s `Agent:Shuffle` plus `Face` moves them back or sideways while facing.
  - Hall monitors closing in would suit them too.
  - Optional v2: `AI.AI.Animate` and Schedules' `Hum.Running` have no direction logic either.

---

## B. NPC animation (NH Combat Test)

### B1. Who animates how
| NPC group | Spawner / owner | Locomotion | Other clips today |
|---|---|---|---|
| 24 rostered students (3 per clique x 8: Vigil, Court, Athletes, Delinquents, Pack, Ordinary, Choir, Ink) | `Features.Schedules` (clones `AI.AI.Rig` into `workspace.NHSchedule`, destroys its Animate) | `Local.Track` plus their own `Hum.Running`: Default pack Walk / Idle / Sprint at `Movement` priority; Walk at speed / (5.3 x Stride); `Build.Idle` speed | `Sitting 103637860968444`, `Lean 129824051499811`, `Eat 126575676069500`, `SitChill 124142826216078` through `Local.Pose(S, name)` (looped, Action) |
| Their "life" | `AI.StudentBrain` (Nav, Senses, Lines, Talk) | n/a | Reactions Danger, Gawk, MakeWay, Space and glance; `Brain.Idle` (fidgets every 6-14 s and chats every 12-28 s, only with a player within 60 studs); `chat(A, B)` (face each other, alternate lines, look-at); fidgets Phone (a real Tool plus a shoulder C0 override), Stretch (client procedural, `NHFidget`), LookUp, LookBehind and Shift (a root turn); LeanOnWall |
| Bump reactions | `StudentBrain.Nudges` | n/a | **`Nudge_Left 130323933959810`, `Nudge_Right 75884392039987`, `Shove_Forward 102977211838873`** (custom; root motion done in code by `slide()`) |
| Head turns, voices, bubbles | client `Controllers.World.NpcLook` | n/a | Head look within 140 studs; Stretch fidget |
| Staff and talkable NPCs (Config.Npcs: Ezra, Vesper, Dex, Pip, Bruno, Rhys, Lucien, Wren, Sable, three coaches, Hale, Night Custodian, Sallow, Pryce, Whitlock, Ashgrave) | `Social.Npcs` (posts by segment; fade between posts) | the `AI.AI.Animate` server Script (Default Idle / Walk at Core, speed / 5.3) | none: they just stand at their post |
| Hall monitor (Count = 1) | `School.HallMonitor` | `AI.AI.Animate` | none (Patrol, Chase, Confront states) |
| Ambient scenery (12 in `workspace.NHAmbient`) | `Features.AmbientNpcs` (anchored, no AI) | none | gym push-ups, sit-ups and pull-ups, side-lay, barber, eating, prisoner, sitting variants, barbell, lean |
| Substitutes | `School.Substitutes` | n/a | SitChill |
| Scenes (six staged moments) | `World.Scenes` plus `Config.Scenes` | borrowed students | steps `go`, `face`, `say`, `wait`, `figure`, **`fx`** (sets only `NHMood = Startled`: the Locker scene's "Shove" has no animation), `prompt` |
| Combat AI (delinquents and so on in `workspace.Live`) | `AI.AI.*` | `AI.AI.Animate` | combat |

Missing:
- **There is no nurse, nurse's office, infirmary or janitor role in the game.**
  - `Nurse` appears only in dialogue lines (CliqueTalk), and no workspace instance is named Infirmary, Nurse or Sick.
  - The **Night Custodian** (Config.Npcs `Custodian`) is the janitor. He "sweeps the main hallway by day" in the
    config text, but he just stands at his post. By night he's the Records Office stealth watcher.
- **There are no spectators.**
  - Bleachers exist (`workspace.Sports.Gymnasium.Stands.Bleacher` x many, `School.Quests.Ring.Bleachers`), but they
    aren't in `Features.Seats.Heights`.
  - Athletes go to their club and idle there; there's no "watch the match" job.

### B2. Where a gesture system hooks in
The pattern to copy is **`StudentBrain.Nudges`**:
- an `IDS` table of published ids (group 15981569);
- with an id of 0, Studio plays `ServerStorage.<Folder>.<Name>` through
  `KeyframeSequenceProvider:RegisterKeyframeSequence`;
- live servers skip the clip.

So the FIER copies can be wired and tested before the owner publishes, and the ids are filled in afterwards.

Proposed:
- **New `ServerScriptService.Services.AI.StudentBrain.Gestures`** (server).
  - `Gestures.Play(S, Name, Opts)` and `Gestures.Stop(S)`.
  - It loads into `S.Tracks[Name]`, so Schedules' `Local.Pose(S, nil)`, which every `WalkTo` calls, already stops a
    gesture when the student walks off.
  - Priority Action, or Action2 for reactions.
  - It honours `busyNow`, `S.Seated` (only the seated clips when seated) and Reduce Motion (a client concern only for
    procedural moves).
  - A global cap of about 6 gestures playing at once, and only with a player within 60 studs, as `Brain.Idle`
    already gates.
- **New `ReplicatedStorage.Config.Gestures`**: one row per clip.
  - Fields: `Id` (0 until published), `Src` (the ServerStorage KS name), `Len`, `Loop`, `Legs` (true = the full body;
    false = an upper-body variant), `Seated`, `RootMotion` (studs: needs a code carry or a strip), `Weight`.
  - A cast table keyed by clique, role and activity, with weights.
  - Studio source folder: `ServerStorage.NHGestures` (the copies), plus `ServerStorage.NHPublish.Gestures` for the
    owner's publish list.
- **Hooks:**
  1. `StudentBrain.fidget(S, Valid)`: add `{ "Gesture", w }` to the pool, with the weight from the clique row. The
     clique comes from `S.Clique`; the activity from `NHActivity`, the `S.Activity` job name and `ctx().Kind`.
  2. `StudentBrain.chat(A, B)`: on each line, the speaker plays a talk gesture (`Talking2`, `TalkingGoinCrazy`) and
     the listener an idle (`Bored`, or `Sad Idle` for the Shy temper).
     - With a Hostile or Wary attitude (`Talk.Attitude`) or rival cliques, both play `Standing Arguing` and
       `Standing Arguing2`.
     - Those two are the same length (20.80 s, 625 frames) and look like a paired take.
     - Stop on `Brain.Urgent` or when someone moves (that check already exists).
  3. `fidgetPhone`: a phone variant that plays `Talking On Phone` (or one of the pacing clips at a Linger or Mingle
     spot).
     - It must **not** apply the `PHONE_POSE` shoulder C0 override, which would fight the clip's arm.
     - Check that the Tool grip lands at the ear.
  4. `World.Scenes`: add an `anim` op, `{ "anim", castIdx, "Name", seconds? }`.
     - Argument: the Arguing pair.
     - Locker: `Shove Reaction` on cast 2 instead of the bare `fx`.
     - Notice: `Pointing Forward` on cast 1.
     - Dare: `Reaching Down` for the door touch.
     - EastWing: `Ducking` at the "Footsteps" line.
  5. `Social.Npcs` (staff posts): a light idle-gesture loop while at the post with a player near.
     - Custodian: Rummaging, Gathering Objects, Reaching Down.
     - Teachers: Pointing Forward, Talking2.
     - Ashgrave: Inspecting.
     - Coaches: Pointing Forward.
     - This needs a small hook, because `AI.AI.Animate` owns their Idle (Core). Gestures at Action sit on top.
  6. `School.HallMonitor` Confront state: `Pointing Forward`.
  7. Incidents and reactions: `React.Gawk` near a Scuffle can play `TalkingGoinCrazy` (some students egg it on);
     `React.Danger` near a Beast can play `Ducking`.
     - `Shove Reaction` and `Shoved Reaction With Spin` would suit the loser of a CliqueFights scuffle, or a
       Nudges-style heavy-hit variant.
     - `Nudges` already owns ordinary bumps; don't replace its custom clips.
  8. Downed recovery (`Features.Downed`): `Standing Up`, then `Injured Hurting Idle` or `Dizzy Idle`. This is a
     sensible home for "nurse's office" idles until a nurse exists (Q5).

### B3. Performance
- **Counts:**
  - 24 roster students, spawned only near players: wake at 160 studs, sleep at 180 (`Schedules.SleepWake`). A
    despawned student's tracks go with the model.
  - About 20 staff and talkables; 1 hall monitor; 12 anchored ambient NPCs.
  - Combat AI and beasts in `workspace.Live`. At survey time: 27 non-player Humanoids in `Live`, plus 8 NHBeasts and
    3 NHWolves. That snapshot was a tutorial Play round, so it isn't representative.
  - 61 Humanoids in workspace in all.
- **Streaming:** StreamingEnabled, Target 1024, Min 64, Integrity `PauseOutsideLoadedArea`.
  - Server Animators replicate their tracks.
  - The client NpcLook only works within 140 studs.
- **Cost of gestures:**
  - One extra cached track per student (LoadAnimation once into `S.Tracks`).
  - The FIER clips are dense 30 fps bakes: the phone and pacing clips have 1,130-1,268 keyframes over 37-42 s.
    That is fine for memory, but consider decimating the long ones to 15 fps when copying them in (see C4).
  - Gating on a near player and a concurrency cap keeps the replication churn small.

---

## C. FIER ANIMATIONS inventory

All **203 KeyframeSequences** live under `workspace.<Folder>.AnimSaves`. Every source model is a standard **R6**
(`Humanoid.RigType` R6, torso 2 x 2 x 1, legs 1 x 2 x 1, Motor6D RootJoint and Hips). Every clip keys exactly Head,
HumanoidRootPart, Torso, both arms and both legs.

All have **Loop = false and Priority = Action**: loop flags must be set at runtime or when copying. They are 30 fps
bakes from RoMixamo `Convert2R6` (`tools/tutorial-anim/mixamo_r6.py` reproduces its output). Every joint name matches
NH's R6, so **every clip plays on NH's rigs**. See C3 for the caveats.

Columns:
- **seam** = the largest joint angle between the first and last frame (0 means the clip loops cleanly);
- **travel** = the root translation baked in (studs);
- **drop** = the lowest torso offset (negative = crouched or kneeling).

### C1. `Cinematic / NPC Gestures` (28)
| Clip | Len | Seam | Travel | Drop | Notes |
|---|---|---|---|---|---|
| Talking2_R6 | 3.77 | 0 | 0 | -0.07 | loops; standing talk |
| TalkingGoinCrazy_R6 | 4.80 | 0 | 0 | -0.18 | loops; animated rant |
| Standing Arguing_R6 | 20.80 | 0 | 0.8 lateral sway | -0.17 | loops; same length as Arguing2: a paired take |
| Standing Arguing2_R6 | 20.80 | 0 | 0.5 | -0.18 | loops |
| Talking On Phone_R6 | 38.83 | 0 | 0.8 | -0.11 | loops; standing |
| Pacing And Talking On A Phone_R6 | 37.63 | 0 | 1.15 lateral | -0.19 | loops; turns around (torso yaw up to 163 degrees): paces in place within about 1 stud |
| Talking Phone Pacing_R6 | 42.23 | 0 | 1.93 lateral | -0.21 | loops; wider pace (about 2 studs) |
| Pointing Forward_R6 | 4.70 | 0 | 0.27 | -0.10 | loops |
| Praying_R6 | 6.87 | **124** | Z 1.1 | -1.16 | **one-shot**: starts kneeling (-0.95) and ends standing. To loop, cut a kneel-hold section |
| Kneeling Inspecting_R6 | 4.93 | 0 | 0 | **-1.60** | loops; one knee down the whole clip |
| Reaching Down_R6 | 3.00 | 0 | 0.1 | -0.21 | loops; bends at the waist about 81 degrees |
| Cheering While Sitting_R6 | 4.33 | 0 | 0.26 | -0.87 (throughout) | loops; **legs max 36 degrees**: probably not a 90-degree seated leg pose. Needs a viewport check on a seat (Q6) |
| Shove Reaction_R6 | 2.43 | 1 | **7.24 forward** | -0.20 | one-shot with big baked travel: strip it to code carry (as Nudges does) or it snaps back |
| Shoved Reaction With Spin_R6 | 4.53 | 159 | 5.56 plus a spin | -0.42 | one-shot; same root-motion issue |
| Entry_R6 | 7.30 | 0 | 2.4 | -1.09 | dramatic entrance; root travel |
| Corkscrew Evade_R6 | 2.50 | 85 | 6.3 lateral | n/a | combat or cine |
| JumpingKickWall_R6 | 2.10 | 60 | 3.4 | n/a | parkour |
| Box Jump_R6 | 3.90 | 0 | Z 2.0 | n/a | parkour |
| Open Door Outwards_R6 / Opening Door Inwards_R6 | 4.10 / 6.37 | 0 | 1.4 / 0.85 | n/a | loopable; door use (extra fit with Features.Doors) |
| Climbing Down Wall, Climbing Down, Climbing Ladder, Climbing To Top, Climbing, Climbing2, Rope Climb, Sprint To Wall Climb | 0.77-4.00 | various | various | n/a | traversal; not gestures |

### C2. Other folders (gesture-relevant)
| Folder / clip | Len | Seam | Drop | Notes |
|---|---|---|---|---|
| Idle Anims / Dizzy Idle_R6 | 4.27 | 0 | -0.12 | loops |
| Idle Anims / Injured Idle_R6 (also in Injured Anims) | 9.33 | 0 | -0.22 | loops; hunched |
| Injured Anims / Injured Hurting Idle_R6 | 6.03 | 0 | -0.95 at the deepest | loops; doubles over |
| Idle Anims / Bored_R6 | 10.67 | 0 | -0.08 | loops; great listener and waiting idle |
| Idle Anims / Sad Idle_R6 | 2.67 | 0 | -0.08 | loops |
| Idle Anims / Box Idle_R6 | 6.30 | 0 | n/a | loops; holding a box or a boxing stance (unclear) |
| Idle Anims / Orc Idle_R6 | 5.33 | 0 | n/a | heavy, hunched: The Pack, or a moon-night student |
| Idle Anims / Laying Idle_R6 | 2.13 | 0 | torso pitched -89 degrees | lying; cot or floor (the AmbientNpcs SideLay exists already) |
| Idle Anims / Ducking_R6 | 1.53 | 146 | n/a | one-shot cower; Danger reaction |
| Idle Anims / Falling, Hanging Idle, Hanging, Hostage Villain, Standing Torch Idle 01 | n/a | 0 | n/a | situational |
| Interaction Anims / Rummaging_R6 | 4.83 | 0 | -0.18 | loops; in place, bent forward: lockers and bins |
| Interaction Anims / Inspecting_R6 | 3.17 | 0 | -0.16 | loops; looking at something at chest height |
| Interaction Anims / Gathering Objects_R6 | 5.97 | 0 | -1.52 | loops; squats and picks up (janitor) |
| Interaction Anims / Pushing, Moving Object, Pulling Lever, Torch x2 | n/a | some | n/a | props needed |
| Movement Anims / Swatting Bugs_R6 | 6.67 | 0 | n/a | **8.4 studs of baked travel**: a walking clip |
| Movement Anims / Walking Carrying Box | 2.87 | 0 | n/a | 7.3 studs of travel: a walk cycle with root motion, so it needs stripping for in-place use |
| Walk / Stand Anims / Left Strafe Walking_R6, Right Strafe Walking_R6 | 1.03 | 0 | -0.35 | the published strafes (A4) |
| Walk / Stand Anims / Left Turn 90, Right Turn 90, Left Turn | 0.93-1.63 | 90-176 | n/a | turn-in-place: could replace the brain's "Shift" root lerp |
| Walk / Stand Anims / Low Crawl_R6 | 2.33 | 0 | n/a | 3.8 studs of travel |
| Injured Anims / Injured Walk, Injured Run, Injured Walk Backwards, Injured Run Backwards (and Left Turn) | 0.5-1.67 | about 0 | n/a | in-place injured locomotion (low-HP player or post-downed student) |
| Quick Movement Anims / Standing Up_R6 | 6.07 | n/a | n/a | getting up from the floor (Downed recovery) |
| Soccer Anims (24) | n/a | n/a | n/a | Jog Backward 0.80 s (a back-pedal option, A3), Goalkeeper Idle, Fallen Idle, tackles and kicks (Sports) |
| Zombie Anims (16) | n/a | n/a | n/a | Agonizing 11.6 s, Getting Bit, Scream: Beasts and Moon events |
| Attacker / Victim Anims (9 + 9) | n/a | n/a | n/a | paired takedowns, hostage, assassinations (Stealth or grips) |
| WhosRello (66) | n/a | n/a | n/a | the 2.35.0 tutorial chains and `_End` poses; already in use; ignore |

### C3. Rig and joint flags (playing FIER clips on NH)
- **Joints:** they all match (R6 Head, Torso, both arms and both legs; RootJoint is a Motor6D). Nothing is
  unplayable.
- **Scale:**
  - The FIER clips were authored on a 2-stud-leg rig. NH students have 1.8-stud legs times `NpcBuilds` height, and
    players about 1.6.
  - R6 KeyframeSequence **translations are in studs and are not rescaled** on R6. Confirm this in Play (Q7).
  - Clips with a deep root drop (Kneeling Inspecting -1.60, Gathering Objects -1.52, Praying -0.95 to -1.16,
    Injured Hurting -0.95, Cheering While Sitting -0.87) will push the knees and shins about 10-20 % into the floor on
    smaller bodies.
  - Fix while copying: scale the Torso pose translation by `Leg/2` per build bucket, or offset HipHeight during the
    clip.
- **Root motion:** Shove Reaction (7.2), Shoved With Spin (5.6 plus a spin), Entry (2.4), Swatting Bugs (8.4),
  Walking Carrying Box (7.3), Low Crawl (3.8) and the climbs bake travel into the Torso pose.
  - On a Humanoid that stays put they snap back at the end.
  - Strip the horizontal travel into a code carry, as `Nudges.slide()` does, with the wall and floor checks.
- **Legs keyed everywhere:**
  - Each gesture replaces the idle's legs (planted, since the root holds still) but can't play over a walk.
  - For "talking while walking" or a phone between classes, make **upper-body-only variants**: drop the leg and
    lower Torso poses (as Nudge_Left / Nudge_Right leave the hips unkeyed).
- **Sitting:** Cheering While Sitting needs a seat base pose.
  - The Schedules `Sitting` clip is Action, and this one is Action too and keys the legs.
  - Play it at Action2 on a seated student, or make an arms-and-torso-only variant over `Sitting`.
  - The bleachers would need Seat heights (B1).
- **Owner style:** realistic legs, planted feet, no skate, weight.
  - The standing gestures are in place (root still, seam 0), so feet stay planted.
  - The pacing clips do walk 1-2 studs and turn: run them only where there's that much clear floor, and never during
    `Agent.Moving`.
  - Strafes: match playback to ground speed (A4) or they skate.
- **Not useful as NPC gestures:** the climbs, flips, kicks, Corkscrew Evade, JumpingKickWall, Box Jump (traversal or
  combat) and the WhosRello tutorial set.

### C4. Copy plan (when Studio is free)
1. Read each chosen KS from FIER (never save FIER).
2. Serialize it through the Studio MCP file bridge or a Luau string dump, and rebuild it in NH under
   `ServerStorage.NHGestures`.
3. Set Loop, rename to `NHG_<Name>`, apply the C3 fixes (root-motion strip, upper-body variants, height scaling), and
   optionally decimate to 15 fps.
4. Mirror into `ServerStorage.NHPublish.Gestures` for the owner's publish list.
5. After the owner publishes, find the ids in group 15981569:
   `itemconfiguration.roblox.com/v1/creations/get-assets?assetType=Animation&groupId=15981569` (newest first).
6. Load-check the Length and Loop of each one and fill in `Config.Gestures`.

---

## Candidate casting table (first pass plus suggestions)

| Who / when | Hook | Clip(s) | Variant needed | Status |
|---|---|---|---|---|
| Clique chatter (any clique, pairs) | `chat(A, B)` | Talking2, TalkingGoinCrazy (speaker); Bored, Sad Idle (listener) | none | owner's pick |
| Arguments (Hostile or rival pair, the Argument scene) | `chat`, Scenes `anim` | Standing Arguing + Standing Arguing2 (paired, 20.8 s) | none | owner's pick |
| Students between classes (Passing, Mingle, Linger) | fidget "Phone" | Pacing And Talking On A Phone, Talking Phone Pacing (at a spot); Talking On Phone (standing) | an upper-body Talking On Phone for walking with the phone; drop the shoulder C0 override | owner's pick |
| Choir (The Chapel hangout) | fidget (Choir) | Praying | cut a loopable kneel-hold (plus kneel-in and stand-up ends); height scale | owner's pick |
| Athletes, seated | a new spectator job, or a seated fidget | Cheering While Sitting | needs a seat (bleacher Seat heights) and a viewport check of the legs | owner's pick, blocked (Q6) |
| Athletes, standing (extra) | fidget (Athletes, Club) | Pointing Forward (calling plays); Goalkeeper Idle (Leo, the keeper) | none | suggestion |
| Staff and the Vigil (The Archive, patrols) | fidget (Vigil); Social.Npcs posts | Kneeling Inspecting; Inspecting (standing) | height scale | owner's pick |
| Lockers | fidget near `HallwayProps.Locker`; Locker scene | Rummaging | face the locker; it's in place | owner's pick |
| Janitor (the Night Custodian by day) | Social.Npcs post loop | Rummaging, Gathering Objects, Reaching Down | height scale (Gathering) | owner's pick |
| Shoves (incidents) | Scenes `anim` (Locker); CliqueFights scuffle loser | Shove Reaction, Shoved Reaction With Spin | **strip the root motion into a code carry** | owner's pick; Nudges keeps the bumps |
| Nurse's office | **no nurse or office exists** | Injured Idle, Injured Hurting Idle, Dizzy Idle (plus Laying Idle on a cot) | n/a | blocked (Q5); suggest Downed recovery |
| Downed recovery (extra) | `Features.Downed` | Standing Up, then Dizzy Idle or Injured Hurting Idle for a few seconds | none | suggestion |
| Danger and monsters (extra) | `React.Danger`, Beasts | Ducking (cower) | none | suggestion |
| Fight gawkers (extra) | `React.Gawk` | TalkingGoinCrazy (egging on) | none | suggestion |
| Hall monitor Confront (extra) | `HallMonitor` | Pointing Forward | none | suggestion |
| Teachers and coaches at posts (extra) | Social.Npcs | Pointing Forward, Talking2; Ashgrave Inspecting | none | suggestion |
| Notice board scene (extra) | Scenes `anim` | Pointing Forward | none | suggestion |
| Dare scene (extra) | Scenes `anim` | Reaching Down (touching the door) | none | suggestion |
| The Pack on moon nights (extra) | fidget (Pack, NHMoonEventOn) | Orc Idle | none | suggestion |
| Court and Delinquents (extra) | fidget | Bored (aloof); Standing Arguing with rivals | none | suggestion |
| Doors (extra, v2) | Nav or Features.Doors | Open Door Outwards, Opening Door Inwards | timing with the door swing | suggestion |
| Turning in place (extra, v2) | brain "Shift" fidget, `Agent:Face` | Left Turn 90, Right Turn 90 | none | suggestion: replaces a root lerp with stepping feet |

---

## D. Risks and open questions for the owner

1. **Q1: the strafe torso turn.** Both strafe clips turn the chest about 58 degrees toward the travel side, with the
   head about 43 degrees off. In a lock-on you won't square up to the target. Is that OK, or should a counter-rotated
   variant be baked?
2. **Q2: strafe speed.** At the current walk (14.4) the clip needs 3.3x playback to keep the feet planted. Is it OK
   to slow movement while strafing (for example, about 8.5 studs/s), or would you prefer faster-looking footwork
   (skating, or a new clip)?
3. **Q3: when strafes play.** Is it lock-on, shift lock (Left Alt) and first person? Should touch and gamepad (no
   continuous lock) ever strafe?
4. **Q4: a backward walk.** Is a reversed Walk acceptable for now, or will you supply a backward-walk clip? (FIER has
   only the Soccer Jog Backward and Injured Walk Backwards.)
5. **Q5: the nurse's office.** There's no nurse, office or janitor role. Should we add an infirmary spot with an
   ambient patient (anchored, like AmbientNpcs) and/or a Nurse NPC, or use the injured and dizzy idles for students
   getting up after being downed?
6. **Q6: Athletes cheering while seated.** There is no spectator system, and the bleachers aren't seats. Should we
   add bleacher seats plus a "watch the match" job during Matches, or drop that cast? The clip's legs need a viewport
   check.
7. **Q7: scale (risk).** NH bodies are smaller than FIER's 2-stud-leg rig, and R6 animation translations probably
   don't rescale. Kneels and squats may sink 10-20 %. Plan: height-scaled copies, then a dipcheck in Play.
8. **Root motion (risk).** The shove clips carry 5-7 studs. They must be stripped into a code carry with wall and
   floor checks, or students will snap back or slide into walls.
9. **Publish dependency (risk).** Until the gesture clips are published to the group, live servers play nothing;
   only Studio has the `RegisterKeyframeSequence` fallback. The publish list will be about 15-20 clips, plus variants.
10. **Fighting existing overrides (risk).**
    - The phone fidget's shoulder C0 override, and `NpcBuilds.SetPosture`, which changes joints while standing, may
      fight the gestures. Disable both while a gesture plays.
    - `AI.AI.Animate` (staff and monitors) plays Idle at Core, and gestures layer at Action: fine.
11. **AnimationController pack swaps (risk).** `UpdateWeapon` runs `StopAllTracks` plus `SetTracks` (which clears
    `TrackTable`). The strafe tracks must be re-added after every pack load, or kept outside `TrackTable`, or they
    vanish after the first equip.
12. **Cinematics (risk).** Gate the strafes on `NHInCine`, `NHApproach`, `NHCineSeam` and `NHCineHold`, and keep
    them out of CineActor's `STRIDE`, so a cut never shows a strafe or a skating strafe.
13. **Studio time.** All the copy and wiring work needs NH Combat Test in Edit, and the tutorial session has it now.
    The survey numbers come from a tutorial Play round. Re-verify the counts and the script state in Edit first.
14. **Aside:** the player's Walk plays at speed / 10, while the same clip was measured at 5.3 studs/s at 1x on
    1.8-stud NPC legs. Is the player's walk under-speed (sliding)? Worth a dipcheck.
