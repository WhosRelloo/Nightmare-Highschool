# Movement: speeds, gaits, strafes, the backpedal, and stride-matched cadence

- **Spec:** `docs/superpowers/specs/2026-11-22-strafes-npc-gestures-design.md` §1.
- **Code:** `Controllers.Character.AnimationController` (client), `Config.Locomotion` and `Functions.Locomotion`
  (pure), `Features.CombatSpeed` (the speed cap), and `Controllers.CineActor` (the approach cadence).

## When you strafe
The directional walk runs when all of these are true:
- you're at **walk speed**: not sprinting, fast-sprinting or crouching;
- one of the **facing modes** is on, from any input:
  - **lock-on** (middle mouse, while equipped);
  - **shift lock** (Left Alt);
  - **first person**;
- **nothing blocks it**:
  - a cut (`NHInCine`) or an approach (`NHApproach`);
  - a seamless seam or hold (`NHCineSeam`, `NHCineHold`);
  - the tutorial;
  - a transformation or wolf form;
  - a busy state (dodge, slide, ragdoll, downed, carried, gripped, paralysed);
  - AutoRotate turned off by something other than lock-on (the skateboard, the football dive).

The mode has to hold for 0.12 s before the blend starts, and it fades out over 0.15 s.

## The blend
- **The move angle** against your facing blends four things:
  - **Walk** forward;
  - **Walk at a negative speed** for backwards. This backpedal is the stand-in until there's a backward clip;
  - **StrafeLeft** and **StrafeRight**.
- **Contact sync:** the strafe's left-foot contact is phase-locked to the walk's, so the feet meet on the diagonals.
- **The strafe clips** are counter-rotated copies of the owner's Left/Right Strafe Walking, so the chest faces
  forward and the legs keep their world motion:
  - `NHG_StrafeLeft_Square` / `NHG_StrafeRight_Square`, baked by `tools/phase6-strafes/anim/bake.py`.
  - Until they're published, live servers play the originals (126969213208550 / 84541589738848), and Studio plays
    the local KeyframeSequences in `ReplicatedStorage.NHLocoClips`.

## Speed and cadence
- **The strafe speed cap:** 8.5 studs/s.
  - The client tells the server through `ReplicatedStorage.Remotes.NHStrafe`. The server sets the Character
    attribute `NHStrafing`, and CombatSpeed caps the walk band at `StrafeSpeed`.
  - It's a cap, so hunger, a combat tag and kit slows still apply.
- **Cadence:** every gait plays at the rate that keeps the planted foot still:
  `rate = ground speed / (Stride[gait] × leg length / 2)`, clamped to 0.3–2.4×.
  - **Strides,** in studs/s at 1× on 2-stud legs: Walk 5.9, Sprint 13.5, CrouchWalk 3.5, FastSprint 18.0.
  - **The strafes,** by their planted-foot speed: 4.76 left, 4.84 right.
  - **Before:** the controller used fixed divisors (10 / 24 / 7 / 30), so the feet slid about 2×.
  - **Owner ruling:** stride-match walk, sprint and crouch, capped at 2.4×. At the old walk speed of 14.4 the cap
    left some slide (owner-visual row V2); the walk is 10 now (below), so nothing hits the cap.
- **CineActor:** its approach cadence uses the same rule, and never the strafes.

## Studio
- **`NHStrafeTest = "Lock"`,** a Player attribute that only works in Studio, makes the controller act as if locked
  on. `tools/phase6-strafes/checks/strafecheck.lua` uses it.

## Speeds and gaits (locomotion-pace, 2026-11-23)
The owner: the running speed and animation were too fast, and NPCs should follow the players' animation rules.

- **Speeds:** `Config.Locomotion.Speeds` is the one place they live.

  | Speed | Now | Was | Written by |
  |---|---|---|---|
  | Walk | 10 | 12 after a sprint, 14.4 after any state, 16 at spawn | Sprint's release and cancel, every StateManager reset, Crouch, Evolution, Cine, `StarterPlayer.CharacterWalkSpeed`, the `StarterCharacter` and AI rig Humanoids (they override `CharacterWalkSpeed`) |
  | Sprint | 22 | 25 | Sprint |
  | Fast sprint | 30, after 2 s (`FastAfter`) | 40.5 | Sprint (a slide carries straight into it) |
  | Walk while attacking | 7 | 10 | StateManager `Attacking` |
  | Carrying someone | 8 | 12 | `Config.Downed.CarryWalkSpeed` |
  | NPC patrol | 10 | 12 | `Config.NPC.PatrolSpeed` |

  Unchanged: crouch 7, crawl 4, stuns and slows 5, FlashStep 40, the NPC chase and sprint tiers (15–18 / 19–24).
  The two top tiers (23, 24) now outrun a player's first two seconds of sprint (22); the fast sprint (30) still
  outruns all of them.
- **Gaits:** `Functions.Locomotion.Gait(Set, Ground, Cfg)` picks the clip from the faster of the set speed and the
  ground speed: Walk up to `Gaits.WalkMax` (12), Sprint up to `Gaits.SprintMax` (26), FastSprint above. The same call
  runs in the player's `AnimationController`, the AI NPCs' `Services.AI.AI.Animate`, and the schedule students
  (`Features.Schedules`; they have no fast sprint, so Sprint plays above 12). Before, players and AI NPCs switched at 20
  and 40, and students ran above 10.
- **Rates:** all three use `Loco.Rate` with their own leg length (AI NPCs read `Left Leg` again 2 s after spawn and when
  `Height` changes). Before, AI NPCs used fixed divisors (speed / 5.3, / 24, / 30) and students `WALK_PACE` 5.3 /
  `RUN_PACE` 16 times leg / 1.8.
- **Jump, fall and land:** AI NPCs now skip the jump and fall clips while sprinting and play the `Land` one-shot on
  touchdown, the way players do.
- **What the clips play at now** (2-stud legs): walk 1.69×, sprint 1.63×, fast sprint 1.67×. Shorter bodies step
  quicker to keep their feet planted: on a 0.86-height player (1.615-stud legs) it's about 2.06× for all three, where
  before the walk and fast sprint hit the 2.4× cap and slid.
- **Measured in Play** (2026-11-23, slot 2): `tools/locomotion-pace/REPORT.md`.
