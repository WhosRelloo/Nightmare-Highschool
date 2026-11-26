# Anatomy: what the owner imports and publishes

Nothing here is uploaded or published yet. Everything is built and in the repo. Until it is imported, the bench draws
stand-in parts from `ReplicatedStorage.Anatomy.Layout`, and the clips play unpublished through
`KeyframeSequenceProvider:RegisterKeyframeSequence`.

Read `docs/Pipeline-Lessons.md` first: rigid rigs for multi-piece props, the import scale, textures, group asset ids.

## 1. Meshes (9 FBX, `art/props/fbx/`)

Import each FBX through the 3D Importer, as the group (15981569), at the scale in Pipeline-Lessons. Every piece
comes in as its own MeshPart named `Anat<Prop>_<Piece>`.

| FBX | Pieces |
| --- | --- |
| `AnatFrog.fbx` | Body, Plate, Mechanism, Head, Legs, SideKey, HeartPump, Lungs, GearGut, FlagCog, CradleGlow |
| `AnatRaven.fbx` | shell, wing plates 1-4, VoiceBox, WingSpring, tail, key, organs |
| `AnatWyvern.fbx` | shell, FireGland (+ Glass, Glow), HeartA, HeartB, GearGut, head, wings, tail, key |
| `AnatToolKey.fbx`, `AnatToolDriver.fbx`, `AnatToolLoupe.fbx`, `AnatToolScalpel.fbx`, `AnatToolTweezers.fbx` | Main (+ LensGlass on the Loupe) |
| `AnatBenchSet.fbx` | Desk, Tray, Wax, Roll, Candle, FlameGlow, Chalk1Glow..Chalk5Glow |

The exact piece list for each prop, with sizes, materials and attach points, is in `art/props/anim/Anat<Prop>_rigid.json`.

After the import, run `tools/electives/stage/anatomy_import.lua` in Edit. It renames, sizes and places every MeshPart
from the Layout, dresses Glow and Glass pieces, and moves the models to `ReplicatedStorage.Anatomy.Models.<Prop>`.
That script has not been run against real imports yet. Check its output.

## 2. Textures (200 PNG, `art/props/textures/Anat*`)

Four maps for every baked piece: `Anat<Prop>_<Piece>_{color,normal,rough,metal}.png`. That is 1024 px for pieces
larger than 0.12 m and 512 px for the rest. Upload them as group images, then fill the `TEXTURES` table at the top of
`stage/anatomy_import.lua` (piece -> { Color, Normal, Rough, Metal } ids) and run it again. It builds a SurfaceAppearance
for each piece.

## 3. Animations (9 clips, `ReplicatedStorage.AnatomyClips.Animations`)

Right-click each KeyframeSequence > Save to Roblox, as the group. Then put the ids in the `AnatomyClips.Clips` map.

| Clip | Used for |
| --- | --- |
| AnatBenchIdle | the seated loop |
| AnatUnwind | Key and Driver turns |
| AnatTrace | the Scalpel trace |
| AnatPry | opening the plate |
| AnatLift | picking up and putting down tools and organs |
| AnatRecoil | slips |
| AnatLoupe | the Inspect step |
| AnatWrite | placing on the Specimen card |
| AnatDone | after the last organ |

Shot list and timings: `tools/electives/anim/clips.md`.

## 4. Journal plates (3 images)

**Done (2026-11-26).** The 512 px crops in `tools/electives/render/out/plates/` are uploaded and the ids are set on each
species in `Config.Anatomy`. They are owned by the owner's account, not the group (see `REPORT.md`).

## 5. Not built yet

- **BrassLoupeMonocle**, the mastery accessory. It isn't modelled and isn't in `Config.Accessories`. Mastery already
  tries to grant it on every lesson and will backfill it once it's in the catalog.
