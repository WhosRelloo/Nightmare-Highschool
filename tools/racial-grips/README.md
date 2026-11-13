# Racial grips: paired R6 animation generator (2.6.0, 2.6.2)

Builds an attacker clip and a victim clip in one shared space so hands land on the other body, then hands them to
`animpro.mjs` (roblox-cinematic-animation skill) for its checks, contact sheets and Luau.

| File | What |
|---|---|
| `rig.py` | R6 forward kinematics (Roblox HRP space, z back), contact solve with twist continuity, Hermite quaternion splines |
| `pair.py` | Clip evaluator: reach keys (`victim`/`attacker`/`self`/`world` targets, `slide` segments), baking, contact and ground reports, animpro run |
| `clips/*.py` | One file per grip (`vampire`, `ghoul`, `werewolf`, `wraith`, `priest`, `human`); `_util.py` has plant/fit helpers; `ghoul_eatbody.txt` is the owner's Eat Body clip exported to body space |
| `snap.py` | Full poses at chosen times, for Studio previews (rotations only: no leg slide) |
| `duo.py` | Both bodies rendered together (side + 3/4) at chosen times: `python duo.py priest out.png 0.5 1.6 2.46` |
| `solo.py` | One body alone from side / front / back / 3-4 |
| `sinkcheck.py` | Worst floor penetration per part |
| `pack.py` | Compact KeyframeSequence payload for `ServerStorage.NH_GripAnims.Builder.BuildPacked` |
| `out/*.pack.luau` | The exact payloads installed in NH Combat Test |
| `luau/` | The new game modules (Config.RaceGrips, RaceGripFx); `patches.md` lists the edits to existing scripts |

```
cd tools/racial-grips
python pair.py vampire out        # bake + check one pair (writes out/GripVampire*.json/.lua/_sheet.png ...)
python pack.py out/GripVampire    # print the Studio payload
```
Sounds: `tools/sfx/racial_grips.py` (art/sfx/racial-grips). VFX art: `art/vfx/grips/make_grip_sprites.py`.

## Kneels = the game's crouch (2.6.2)
Kneeling bodies copy the in-game Crouch (rbxassetid://139672322709288, "Crouch idle"), frame 0, on a default R6 rig:
`_util.CROUCH_TORSO / CROUCH_FRONT / CROUCH_BACK`, relative to a standing HRP. Use `kneel_legs(x, z, yaw, front, kid)`
for both hips (`front="RightHip"` mirrors it) and `kneel_root(...)` / `kneel_fit(...)` for the torso. The torso leans,
turns, rolls and sinks about its hip line.

- A hip spec `{"plant": 4x4, "id": ...}` keeps that leg's part fixed in the world.
- Every frame, `rig.plant_solve` finds the hip rotation and the leg's slide off its socket (torso space, `pose[joint + "_off"]`).
- `pair.py` writes the slides to `out/<clip>.tuck.json` as Pose positions.
- `pack.py` adds them to the leg entries, because animpro only rotates limbs.
- The crouch's back knee rests 0.41 under the floor, as in game.
- animpro's groundContact check can't see the slide, so it is waived on the crouching attackers.
