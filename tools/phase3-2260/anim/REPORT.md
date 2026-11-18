# Animation sourcing report (2.26.0, the Strikethrough)

The owner's rule: reuse existing clips, and where none fits, derive from measured related clips.

- **Measured by** `extract.luau`: forward kinematics on each clip's own rig. The R15 ghoul and stalker use
  AnimationConstraints; the R6 clips use the AI rig.
- **Converted by** `convert.py`:
  - R15 arms aim shoulder to wrist and legs hip to ankle, so the elbow and knee fold into the R6 aim.
  - Euler XYZ, as the tool applies `rotation`, with the reading nearest the previous key.
  - Weight-0 placeholder poses are skipped.
  - The source's fastest segment becomes the strike, retimed to the house-style phases.

**Sign check:** the game's Knockback, converted raw and drawn by the animation tool, matches the real clip played on
an R6 dummy at 0.17 s: head to the character's right, body rolled flat, limbs up and to the right. The Knockback is
a real tumble of about 1.9 turns, in steps of 84 to 117 degrees between keys.

## StrikeRise

- **Source:** `GhoulEmerge` (R15, 1.80 s, 6 keys)
- **Source key times:** 0.00, 0.35, 0.70, 1.00, 1.40, 1.80
- **Detected strike:** key 5 (t 1.80 s; aim change 7.6 per s)
- **Target:** 1.6 s; anticipation [0, 0.7], strike [0.7, 0.82], settle [0.82, 1.6]; contacts [0.82]; root drop 0.35 studs
- **Measured:** torso pitch -90 to 14 degrees; root travel 2.48 studs
- **Limb swing** (degrees forward of straight down, min / max): LeftShoulder -171 / 168; RightShoulder -171 / 168; LeftHip -10 / 22; RightHip -8 / 24
- **Retimed keys:** 0.0, 0.175, 0.35, 0.525, 0.7, 0.82, 1.6

## StrikeLunge

- **Source:** `StalkerReach` (R15S, 1.50 s, 5 keys)
- **Source key times:** 0.00, 0.45, 0.62, 0.95, 1.50
- **Detected strike:** key 2 (t 0.62 s; aim change 15.5 per s)
- **Target:** 1.05 s; anticipation [0, 0.38], strike [0.38, 0.47], settle [0.47, 1.05]; contacts [0.47]; root drop 0.3 studs
- **Measured:** torso pitch -76 to 6 degrees; root travel 1.44 studs
- **Limb swing** (degrees forward of straight down, min / max): LeftShoulder -8 / 28; RightShoulder 24 / 137; LeftHip -4 / 58; RightHip -13 / 22
- **Retimed keys:** 0.0, 0.38, 0.47, 0.76, 1.05

## StrikeRecoil

- **Source:** `GhoulStun1` (R15, 0.70 s, 4 keys)
- **Source key times:** 0.00, 0.10, 0.30, 0.70
- **Detected strike:** key 1 (t 0.10 s; aim change 23.7 per s)
- **Target:** 0.8 s; anticipation [0, 0.05], strike [0.05, 0.14], settle [0.14, 0.8]; contacts [0.14]; root drop 0.2 studs
- **Measured:** torso pitch -34 to 4 degrees; root travel 0.14 studs
- **Limb swing** (degrees forward of straight down, min / max): LeftShoulder 48 / 72; RightShoulder 48 / 71; LeftHip -8 / 22; RightHip -6 / 24
- **Retimed keys:** 0.0, 0.14, 0.47, 0.8

## StrikeGrab

- **Source:** `GhoulGrab` (R15, 1.50 s, 7 keys)
- **Source key times:** 0.00, 0.35, 0.50, 0.62, 0.95, 1.10, 1.50
- **Detected strike:** key 2 (t 0.50 s; aim change 30.2 per s)
- **Target:** 1.2 s; anticipation [0, 0.36], strike [0.36, 0.45], settle [0.45, 1.2]; contacts [0.45]; root drop 0.25 studs
- **Measured:** torso pitch -90 to -20 degrees; root travel 1.09 studs
- **Limb swing** (degrees forward of straight down, min / max): LeftShoulder 36 / 129; RightShoulder 35 / 129; LeftHip -10 / 56; RightHip -6 / 46
- **Retimed keys:** 0.0, 0.36, 0.45, 0.637, 0.825, 1.012, 1.2

## StrikeStagger

- **Source:** `GhoulStun1` (R15, 0.70 s, 4 keys)
- **Source key times:** 0.00, 0.10, 0.30, 0.70
- **Detected strike:** key 1 (t 0.10 s; aim change 23.7 per s)
- **Target:** 1.0 s; anticipation [0, 0.04], strike [0.04, 0.15], settle [0.15, 1.0]; contacts [0.15, 0.6]; root drop 0.4 studs
- **Measured:** torso pitch -34 to 4 degrees; root travel 0.14 studs
- **Limb swing** (degrees forward of straight down, min / max): LeftShoulder 48 / 72; RightShoulder 48 / 71; LeftHip -8 / 22; RightHip -6 / 24
- **Retimed keys:** 0.0, 0.15, 0.575, 1.0

## StrikeTug

- **Source:** `FistClinchVictim` (R6, 1.27 s, 39 keys)
- **Source key times:** 0.00, 0.03, 0.07, 0.10, 0.13, 0.17, 0.20, 0.23, 0.27, 0.30, 0.33, 0.37, 0.40, 0.43 ...
- **Detected strike:** key 7 (t 0.23 s; aim change 27.6 per s)
- **Target:** 1.0 s; anticipation [0, 0.3], strike [0.3, 0.5], settle [0.5, 1.0]; contacts []; root drop 0.1 studs; loop
- **Measured:** torso pitch -58 to -11 degrees; root travel 0.49 studs
- **Limb swing** (degrees forward of straight down, min / max): LeftShoulder 28 / 158; RightShoulder 20 / 155; LeftHip 8 / 21; RightHip -9 / 16
- **Retimed keys:** 0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.5, 0.516, 0.532, 0.548, 0.565, 0.581, 0.597 ...

## StrikeShatter

- **Source:** `GhoulDeath` (R15, 1.80 s, 5 keys)
- **Source key times:** 0.00, 0.20, 0.70, 1.15, 1.80
- **Detected strike:** key 1 (t 0.20 s; aim change 10.0 per s)
- **Target:** 1.4 s; anticipation [0, 0.1], strike [0.1, 0.2], settle [0.2, 1.4]; contacts []; root drop 0.5 studs
- **Measured:** torso pitch -88 to -6 degrees; root travel 3.34 studs
- **Limb swing** (degrees forward of straight down, min / max): LeftShoulder 48 / 172; RightShoulder -179 / 177; LeftHip -7 / 22; RightHip -4 / 24
- **Retimed keys:** 0.0, 0.2, 0.6, 1.0, 1.4

## YouTugPull

- **Source:** `FistClinch` (R6, 0.83 s, 26 keys)
- **Source key times:** 0.00, 0.03, 0.07, 0.10, 0.13, 0.17, 0.20, 0.23, 0.27, 0.30, 0.33, 0.37, 0.40, 0.43 ...
- **Detected strike:** key 18 (t 0.60 s; aim change 45.1 per s)
- **Target:** 1.0 s; anticipation [0, 0.3], strike [0.3, 0.5], settle [0.5, 1.0]; contacts []; root drop 0.15 studs; loop
- **Measured:** torso pitch -14 to 7 degrees; root travel 0.26 studs
- **Limb swing** (degrees forward of straight down, min / max): LeftShoulder 52 / 175; RightShoulder 51 / 179; LeftHip -8 / 13; RightHip -16 / 99
- **Retimed keys:** 0.0, 0.018, 0.035, 0.053, 0.071, 0.088, 0.106, 0.124, 0.141, 0.159, 0.176, 0.194, 0.212, 0.229 ...

## YouFinisher

- **Source:** `FistM2` (R6, 1.00 s, 61 keys); FistBodyBlow, Uptilt as reference
- **Source key times:** 0.00, 0.02, 0.03, 0.05, 0.07, 0.08, 0.10, 0.12, 0.13, 0.15, 0.17, 0.18, 0.20, 0.22 ...
- **Detected strike:** key 25 (t 0.42 s; aim change 136.3 per s)
- **Target:** 1.25 s; anticipation [0, 0.4], strike [0.4, 0.48], settle [0.48, 1.25]; contacts [0.48]; root drop 0.4 studs
- **Measured:** torso pitch -173 to 21 degrees; root travel 0.46 studs
- **Limb swing** (degrees forward of straight down, min / max): LeftShoulder -84 / 122; RightShoulder -178 / 163; LeftHip -44 / 25; RightHip -63 / 111
- **Retimed keys:** 0.0, 0.017, 0.033, 0.05, 0.067, 0.083, 0.1, 0.117, 0.133, 0.15, 0.167, 0.183, 0.2, 0.217 ...
