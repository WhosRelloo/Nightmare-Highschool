# Fist moves: bespoke clips built on the game's own fist M1s (2.12.0)

Four R6 clips for the fist string enders and the clinch. Each one starts on the exact pose of the clip it interrupts and
ends on the fist idle's first frame, so they join the owner's M1s without a pop.

| Clip | Starts on | Ends on | Markers (speed 1) | Plays from |
| --- | --- | --- | --- | --- |
| `FistShove` | M1.1 at 0.45 s | Idle | Hit 0.333, EndLag 0.467 | `Combat.Ender` (M2 after hit 1) |
| `FistBodyBlow` | M1.3 at 0.40 s | Idle | Hit 0.367, EndLag 0.500 | `Combat.Ender` (M2 after hit 3) |
| `FistClinch` | Block at 0 | Idle | Hit 0.367, EndLag 0.700 | `Combat.Clinch` (M1 while blocking) |
| `FistClinchVictim` | Idle (the reaction starts) | Idle | none | `Combat.Clinch`, on the one caught |

The clinch pair was authored 2.9 studs apart, face to face. `Combat.Clinch` puts the caught one there before playing
the victim clip. Its time 0 is attacker time 0.133, so the knee lands at 0.234 of the victim clip.

## How the owner's fist clips are built (the baseline)

- **Non-bending R6.** Six parts, six Motor6Ds.
- **Limb slides.** Every limb also carries a Pose position, Moon-style: the arms are pulled in about 1.2 studs in the
  guard and slid forward up to about 1.3 studs on a punch, and the legs are tucked. A new clip without those slides
  jumps about a stud at every seam.
- **The idle's soles sit at y = -3.234** relative to the root, with the slides included. The new keys are planted
  there (`fist_poses.SOLE`).
- **Torso-space slide sizes measured from the M1s:**
  - Wind-up: about +0.6 to +0.8 back.
  - Punch: about -1.1 to -1.3 forward.
  - Height: about -0.5 to -0.85.

## Files

| Path | What |
| --- | --- |
| `ref/*.txt` | The live clips exported to body space, one keyframe per line, with `<Joint>_o` slides. `stage/` does the export with `luau/export.luau`. Idle and Block come back truncated from Studio; only their starts are used. |
| `fist_poses.py` | The baseline as poses: `pose(clip, t)`, `key()`, `blend()` (slerp, slides lerped), `offs()` / `slide()` (torso-space slides), `split()` and `bake_offs()` (the slide track, monotone cubic). |
| `clips/*.py` | The three clip definitions (keys, markers, the victim track). |
| `run.py` | Bakes and checks a clip with the racial-grips generator (`tools/racial-grips/pair.py`), writing to `out/`: JSON, Lua, sheets, graphs, trails, plus `<name>.offs.json`. |
| `pack.py` | Packs a baked clip, slides included, into one `BuildPacked` call for Studio. `--to` cuts the end; `--from` trims the start. |
| `luau/NH_FistAnims.Builder.luau` | `ServerStorage.NH_FistAnims.Builder`. It builds the KeyframeSequence, names the Hit / EndLag keyframes (the game's `AnimMarkers` reads keyframe names), and sets a `PreviewId`. |
| `stage/` | `dump.py` (runs Luau in Studio; set `STUDIO`), `pose.py` (poses 6 R6 rigs `R1`..`R6` in `workspace.NHAnimStage` at given times), `seam.py` (each part's position and rotation, relative to the root, on both sides of every join). |
| `studio/` | The three live scripts after 2.12.0, their originals in `pre/`, and `patches.py` (the exact edits). |

## Rebuild

```
python run.py fist_shove
python pack.py out/FistShove > build.luau            # run it in Studio's Edit datamodel
python pack.py out/FistBodyBlow > build.luau
python pack.py out/FistClinch --to 0.867 > build.luau
python pack.py out/FistClinchVictim --from 0.1333 > build.luau
python stage/seam.py                                  # every seam should be millimetres
```

## Publishing (the owner)

Published 2026-11-13 and set in `Fist.Moves`:

- `FistShove`: 99575689929104
- `FistBodyBlow`: 115837677569118
- `FistClinch`: 105787080820844
- `FistClinchVictim`: 127085112840973

To republish after a rebuild:

1. Publish the four KeyframeSequences in `ServerStorage.NH_FistAnims` to group 15981569: right-click each, then
   **Save to Roblox**.
2. Paste each id into the matching Animation under `ReplicatedStorage.Assets.Animations.Weapons.Fist.Moves`: `Shove`,
   `BodyBlow`, `Clinch`, `ClinchVictim`.

While an id is empty the code plays the old stand-in: M1.4, M1.3, or the M2 at 1.25 speed. To test before publishing,
in a play session's server, register each sequence with `KeyframeSequenceProvider:RegisterKeyframeSequence` and set the
Moves ids to the result. In Studio the client resolves the server's temporary ids.
