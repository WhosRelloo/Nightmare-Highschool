# Movement: strafes, the backpedal, and stride-matched cadence (phase6-strafes)

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
  - **Owner ruling:** stride-match walk, sprint and crouch, capped at 2.4×. At the live walk speed of 14.4 the cap
    leaves some slide (owner-visual row V2).
- **CineActor:** its approach cadence uses the same rule, and never the strafes.

## Studio
- **`NHStrafeTest = "Lock"`,** a Player attribute that only works in Studio, makes the controller act as if locked
  on. `tools/phase6-strafes/checks/strafecheck.lua` uses it.
