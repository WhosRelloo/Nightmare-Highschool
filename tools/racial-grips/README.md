# Racial grips: paired R6 animation generator (2.6.0)

Builds an attacker clip and a victim clip in one shared space so hands land on the other body, then hands them to
`animpro.mjs` (roblox-cinematic-animation skill) for its checks, contact sheets and Luau.

| File | What |
|---|---|
| `rig.py` | R6 forward kinematics (Roblox HRP space, z back), contact solve with twist continuity, Hermite quaternion splines |
| `pair.py` | Clip evaluator: reach keys (`victim`/`attacker`/`self`/`world` targets, `slide` segments), baking, contact and ground reports, animpro run |
| `clips/*.py` | One file per grip (`vampire`, `ghoul`, `werewolf`, `wraith`, `priest`, `human`); `_util.py` has plant/fit helpers; `ghoul_eatbody.txt` is the owner's Eat Body clip exported to body space |
| `snap.py` | Full poses at chosen times, for Studio previews |
| `pack.py` | Compact KeyframeSequence payload for `ServerStorage.NH_GripAnims.Builder.BuildPacked` |
| `out/*.pack.luau` | The exact payloads installed in NH Combat Test |
| `luau/` | The new game modules (Config.RaceGrips, RaceGripFx); `patches.md` lists the edits to existing scripts |

```
cd tools/racial-grips
python pair.py vampire out        # bake + check one pair (writes out/GripVampire*.json/.lua/_sheet.png ...)
python pack.py out/GripVampire    # print the Studio payload
```
Sounds: `tools/sfx/racial_grips.py` (art/sfx/racial-grips). VFX art: `art/vfx/grips/make_grip_sprites.py`.
