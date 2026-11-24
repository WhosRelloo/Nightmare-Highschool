# Race transformation forms: Studio import checklist (batch 1: wings and horns)

Built by `art/characters/transformations/form_models.py` (meshes) and `form_textures.py` (maps) per
`docs/superpowers/plans/2026-11-22-race-transformations.md` Task 2. The FBX are in **`E:\NH-Work\forms\fbx\`** (not in
the repo); the maps are in **`art/group-upload-forms/`**. Check sheets (rest, fold, flap from 3 angles, re-imported
from the FBX) are in `E:\NH-Work\forms\check\`. Fit data: `E:\NH-Work\forms\forms_fit.json`.

## What's in batch 1

| Files | Pieces per file | Import as rig |
|---|---|---|
| 14 wings: `NHWing_<Style>_L.fbx`, `NHWing_<Style>_R.fbx` for Nocturne, Wyrm, Tattered, Fallen, Ossuary, Wraithveil, Rime | `<Style><Side>Membrane` + `<Style><Side>Frame`, skinned to one skeleton: `Root > Hum > Fore > D1a > D1b ... D4a > D4b` (3-digit styles: Wyrm, Fallen, Rime stop at D3) | **ON** (keep the detected rig) |
| 7 horns: `NHHorns_<Style>.fbx` for Ram, Demon, Wendigo, Thorn, Broken, Sovereign, Bull | `<Style>Horns`, `<Style>Tip` (not Wendigo or Thorn), `SovereignHalo` | **OFF** |

- Each wing file is a **two-piece rig**, the case the pipeline lessons found imports cleanly. One file per side keeps
  Fallen's feathers under the 20k-triangle cap (the largest piece is 15.3k).
- Bind pose is fully spread; the clips (Task 3) fold, flap and flare it.

## Steps

1. Open **NH Combat Test** in Studio, Edit mode.
2. **Wings:** File → Import 3D, select the **14 `NHWing_*.fbx`** files, Open.
   - Scale: leave as detected (built 1 unit = 1 stud, exported like the accessories). Claude checks every size afterwards.
   - **Rig Type:** leave as detected (custom rig, 11 or 9 bones). Insert Using Scene Position: off.
   - Import.
3. **Horns:** File → Import 3D, select the **7 `NHHorns_*.fbx`** files. **Import as rig: OFF.** Import.
4. Make a Folder **`ServerStorage.NHFormsImport`** and drag all 21 imported models into it, **whole** (don't pull the
   MeshParts out: the bones sit on another part of the imported model, see Accessories.md "Bones lost").
5. **Textures:** upload the **21 PNGs in `art/group-upload-forms/`** to the group (15981569), names unchanged.
6. Tell Claude **"imported"**. Claude then finds the image ids, checks sizes and bones against `forms_fit.json`, adds the
   SurfaceAppearances and moves the models to `ReplicatedStorage.Assets.Forms`.

## The maps (one set per material class, tiled; colour comes from the Looks)

| Set | Used by | Maps | AlphaMode |
|---|---|---|---|
| `NHForm_Membrane_*` | Membrane of Nocturne, Wyrm, Tattered | color, normal, rough | Overlay |
| `NHForm_Feather_*` | Fallen Membrane | color, normal, rough | Overlay |
| `NHForm_Cloth_*` | Ossuary Membrane (the grave-cloth tatters) | color, normal, rough | Overlay |
| `NHForm_Mist_*` | Wraithveil Membrane | color (+alpha), normal, rough | Transparency |
| `NHForm_Ice_*` | Rime Membrane | color (+alpha), normal, rough | Transparency |
| `NHForm_Bone_*` | every `*Frame` | color, normal, rough | Overlay |
| `NHForm_Horn_*` | every Horns, Tip and Halo piece | color, normal, rough | Overlay |

- Colour maps are light and near-neutral. **`SurfaceAppearance.Color`** (checked in Studio 2026-11-23) tints them:
  Membrane pieces by `WingPalette`, Frame by `WingFinish`, Horns and Halo by `HornFinish`, Tip by `HornTip`.
- No metal maps: every set is non-metal (Gilded reads through the tint and roughness).
- UVs are world-scaled, so a map tiles at a fixed size on every style (`form_models.TILE`).

## Imported (2026-11-23)

- The owner imported all 21 into Workspace and uploaded the 21 maps. Ids: `art/group-upload-forms/textures.json`
  (one of each name, no duplicates).
- Checked in Studio: scale 1:1 (Nocturne's membrane 3.82 studs wide, as built); every wing arrived as a rig: a
  `RootPart` (transparent) holding the bones (11, or 9 for the 3-digit styles) plus an `AnimationController`; the
  piece names match.
- **The imported forms face +Z** (the left wing on the model's +X). Place them with a 180-degree yaw:
  - wings: `model:PivotTo(delta * model:GetPivot())` with `delta = Torso.CFrame * CFrame.new(0, -3, 0) * yaw180 *
    RootPart.CFrame:Inverse()` (the RootPart is the build origin, 3 studs below the Torso centre at height 1);
  - horns: `Head.CFrame * CFrame.new(centre) * yaw180` for the `<Style>Horns` piece, with `centre` from
    `forms_fit.json` (build axes: x right, y up, z back).
  - Move whole models with `PivotTo`: moving the parts one by one drags the joined rig parts twice.
- `tools/forms/stage/dress_forms.luau` added the SurfaceAppearances (maps by class, AlphaMode, `Color` = the race
  default from Config.Forms; Ossuary's cloth stays linen, `FormTint = "None"`), turned off collisions and queries, set
  the `Form*` attributes, and moved the 21 models to **`ReplicatedStorage.Assets.Forms`**. Not saved.
- Seen in Edit (`Workspace.NHFormsPreview`, 8 dummies, front and back): every wing on the back and every horn on the
  head, maps and tints showing. Wings are at the bind pose (fully spread) there; in Play they move (see Wing motion).

## Worn in Play (2026-11-23)

- `Controllers.Character.FormParts` (client, `tools/forms/live/`, installed in Edit, not saved) puts the pieces on
  every transformed character within 150 studs: `Functions.Forms.Resolve(Player.Race, ParseLooks(Player.RaceLooks))`,
  so no server change. Wings by RootPart, horns by `FormAnchor`, scaled by Torso height / 2 and the Wing size Look,
  tinted from Config.Forms, Hat accessories hidden under horns, the Sovereign halo spinning (still under Reduce Motion).
- Checked on slot 2 (fresh snapshot, restored after; CineState, Seen and Origin unset before and after), through the
  real `Transformation.Start`, with only the Player's `Race` / `RaceLooks` attributes switched (the profile untouched):
  Vampire 1 (Nocturne wings), Vampire 2 (Wyrm wings + Demon horns), Ghoul 1 (Ossuary + Wendigo), Wraith 2 (Rime, head
  clear). Screens from behind, the front and the side; the pieces follow the claw stance; `Transformation.Stop`
  removes them. Test files: `tools/forms/checks/forms_play_start.lua` / `forms_play_end.lua` (run with
  `harness/server.py`).
- The Look slots are in Studio's `Lineage` (checked 2026-11-23): players pick them in Bloodline → Looks.

## Wing motion (Task 3, 2026-11-23)

- **No clips to publish.** `ReplicatedStorage.Functions.FormWings` (`tools/forms/live/`) runs the concepts' own skeleton
  (`hqwing.Wing.skeleton(fold, flap, lag)`) and sets each bone's `Transform` every frame so the bone points where the
  skeleton says (minimal-arc turn from the bind pose; bone lengths never change, so the joints land exactly). One module
  drives all 7 styles and both sides: it reads the side and the digit count off each rig.
- The clips are curves in (fold, flap, lag): **Idle** (3 s breathe, half folded like a cloak), **Flap** (the concepts'
  1.33 s stroke, digits trailing), **Fold** (a 0.4 s tuck on landing) and **Flare** (0.6 s, folded wings throw open past
  spread, on a fresh transform only, not when a character walks back into range).
- `Controllers.Character.FormParts` picks them: Flap at ground speed >= 20 (walk 12-16, sprint 25 / 40.5) or in the air
  (state, or vertical speed > 14 for other players), Idle otherwise, cross-faded; wings beyond 60 studs update every
  other frame. **Reduce Motion:** the still idle pose, no flap or flare.
- Checked: in Edit, the posed bones match the skeleton within 0.03 degrees (spread, idle, flap up/down, folded) and the
  membrane follows; flap sign matches the concept (positive = downstroke). In Play on slot 2 (fresh snapshot, restored
  after; CineState, Seen and Origin unset before and after): Vampire 1 (Nocturne) idles (shoulder bone 19-21 degrees),
  flaps when sprinting (2.5-32 degrees) and jumping, returns to idle on stopping; Vampire 2 (Wyrm, 3 digits) idles. No
  FormParts warnings.

## Batch 2: the body pieces (built 2026-11-23)

Built by `art/characters/transformations/form_bodies.py`: every direction's body pieces raycast-fitted to each of the
12 bodies (NHBodyTypes.blend, Female v2, Standard boxes). Check sheets (every direction, front and back) for Standard,
Female, Heavy, Petite and Plus: `docs/superpowers/mockups/2026-11-22-transformations/batch2/`. Fit data:
`art/characters/transformations/forms_body_fit.json`.

| File (in `E:\NH-Work\forms\fbx\`) | Pieces |
|---|---|
| 12 × `NHFormBody_<body>.fbx` (standard, female, lean, athletic, muscular, stocky, heavy, petite, toned, curvy, strong, plus) | 27 each: V2Spines; W1Mantle, W1CuffL/R, W1ShinL/R; W2Mantle, W2Back, W2ArmL/R, W2Moon; G1Ribs, G1Spine, G1SpurL/R; G2WrapL/R, G2Chest, G2Moss, G2Nails; R1Capelet; R2SpikeL/R, R2Chains, R2Hang, R2RimeL/R |
| `NHFormHead.fbx` | G1Jaw (the Head is the same on every body) |

- Budgets: the heaviest single piece is W2Mantle (9k tris); a worn direction is at most ~28k (W2). Fur locks are
  single-sided (DoubleSided on), no shadows.
- V1 has no body piece (its long ears are the Vampire Ears Look); Werewolf ears and tail stay the race Looks.
- New maps: **`art/group-upload-forms-2/`**: `NHForm_Fur_color/normal/rough` (fur and grave-moss). Everything else reuses
  batch 1's sets (Bone, Cloth, Mist, Ice, Horn); the moon-marks are Neon.

### Steps (owner)

1. NH Combat Test, Edit mode. File → Import 3D, select the **13 files** (`NHFormBody_*.fbx` and `NHFormHead.fbx`).
   **Import as rig: OFF.** Scale as detected. Insert Using Scene Position: off. Import.
2. Leave the 13 models in Workspace (or drag them, whole, into `ServerStorage.NHFormsImport`).
3. Upload the **3 PNGs in `art/group-upload-forms-2/`** to the group (15981569), names unchanged.
4. Tell Claude **"imported"**. Claude finds the Fur ids, regenerates and runs `tools/forms/stage/dress_bodies.luau`
   (`python make_dress_bodies.py <color> <normal> <rough>`): maps, default tints, `FormPart` / `FormOffset` /
   `FormTint`, then `ReplicatedStorage.Assets.Forms.Bodies.<body>` and `Assets.Forms.NHFormHead`.

### In game (installed in Edit 2026-11-23, not saved)

- `FormParts` reads the character's body off its `NHBodyMesh` Torso CharacterMesh (UI.Appearance.Bodies; none =
  standard), wears `<race letter><direction>*` from that body's model on each R6 part (scaled with the part), tints fur
  from the Fur Look, and hides the cape (`NHCape`) while the form is worn.
- **Bloodline → Looks:** a turning preview of you in your form with your current Looks (three-quarters from behind,
  still under Reduce Motion); colour slots (wing colour, wing bone, horn finish, horn tip) are swatches, locked ones
  dimmed with their tier. Checked in Play: the preview dresses a copy of the character (Vampire 2, Ghoul 1, Wraith 1).
- The form Look slots were already in Studio's `Lineage` (identical to `tools/forms/live/ReplicatedStorage.Lineage.luau`).

### Batch 2 imported and checked (2026-11-23)

- All 13 models dressed (Fur ids: color 114240644732622, normal 74799499262759, rough 117583239027412); 27 pieces per
  body in `Assets.Forms.Bodies.<body>`, `G1Jaw` in `Assets.Forms.NHFormHead`.
- Play on slot 2 (snapshot / restored; CineState, Seen, Origin nil before and after): Werewolf 2 with Fur=Russet wears
  its fur tinted 8c4e2c; Wraith 2 wears its ice, rime and chains; a cape put on mid-form is hidden (CapeBody
  transparency 1). Ending the form re-applies the saved look, so an unsaved test cape goes with it (expected).

## What hangs moves (dangles, 2026-11-23)

Only the pieces that hang get motion; fur, bone, ice, the capelet, moss and nails stay welded. The pipeline lessons
say multi-piece skinned imports go wrong, and chains are rigid anyway, so nothing here is skinned:
`Functions.FormDangles` lays rigid links / linen strips along a small rope simulation (90 Hz substeps, any frame
rate), drawn by `FormParts` each frame.

| Piece | Kind | Motion |
|---|---|---|
| Wraith 2 chest chain, back chain | Swag (pinned over both shoulders) | holds its drape on a spring; steps bob it, stops, turns and landings swing it; it may only move out from the body (cap 0.3 studs) |
| Wraith 2 wrist chain | Hang (pinned at the left wrist) | a pendulum under gravity: trails when you run, swings with the arm; each link within 70 deg of down; stays below the arm and outside the leg |
| Ghoul 2 arm-wrap tatters (4 per arm) | Tatter (3 strips each) | as Hang, lighter and catching more air, a flutter at speed; each strip within 65 deg of down; off its arm and outside the leg |

Reduce Motion: the chains on the body hold their drape; hanging things still hang, with no bob or flutter.

Files:
- `art/characters/transformations/form_bodies.py -- --dangles` writes `NHFormDangles.fbx` (Link, TatterSeg, TatterTip
  and every body's tatter-free arm wraps `G2WrapL_<body>` / `G2WrapR_<body>`: 27 meshes) and `forms_dangles.json` (the
  rest nodes per body, copied to `art/characters/transformations/`). A full rebuild now leaves the chains, the wrist
  chain and the tatters out of the body FBXs.
- `tools/forms/stage/make_dangles.py` generates `live/ReplicatedStorage.Config.FormDangles.luau` (the rest nodes) and
  `stage/dress_dangles.luau` (staging).
- `live/ReplicatedStorage.Functions.FormDangles.luau` (the simulation); `FormParts` builds and steps it.

Checked in Play on slot 2 with placeholder parts standing in for the meshes (snapshot / restored each round;
CineState, Seen, Origin nil before and after): Wraith 2 walking, turning and jumping: chest / back chains 0.02 to
0.2 studs off the body, never inside it; the wrist chain swings 6 to 67 deg and settles. Ghoul 2: tatters trail and
flutter, every strip within 65 deg, settled within about 2 s of stopping.

### Imported and staged (2026-11-23)

`dress_dangles.luau` run in Edit (not saved): Link 0.229 x 0.164 x 0.034, TatterSeg / TatterTip 1 x 1 x 0.06 in
`Assets.Forms.Dangles`; 24 arm wraps swapped; 24 baked chains removed. Play on slot 2 (snapshot / restored; CineState,
Seen, Origin nil before and after): Wraith 2 wears 50 real links (chain tint 96aac0) draped on the chest and back
with the wrist chain hanging; Ghoul 2 wears 24 linen strips that trail and flutter, every strip within 65 deg, settled
about 2 s after stopping. No FormParts warnings in the output.

**Per-axis scaling (fixed the same day):** body scales stretch R6 parts unevenly (the test character's arm is 0.91 wide,
1.59 tall), and FormParts scaled the batch 2 pieces by height only, so a wrap 0.90 wide sat inside a 0.91 arm. Body
pieces and dangle rest nodes now scale per axis by `Part.Size / (2,2,1 or 1,2,1)`; the wraps measure 1.03 on that arm.

### Steps (owner, done)

1. Edit mode. File → Import 3D: `E:/NH-Work/forms/fbx/NHFormDangles.fbx`. **Import as rig: OFF.** Import.
2. Leave the model `NHFormDangles` in Workspace (or move it into `ServerStorage.NHFormsImport`).
3. Tell Claude **"imported"**. Claude runs `tools/forms/stage/dress_dangles.luau`: Link / TatterSeg / TatterTip go to
   `Assets.Forms.Dangles` (chain and linen SurfaceAppearances), the tatter-free wraps replace each body's
   `G2WrapL` / `G2WrapR`, and the baked `R2Chains` / `R2Hang` are removed. Until then nothing in game changes
   (`FormParts` only hangs dangles once `Assets.Forms.Dangles` exists).

## Not done yet

- Saving the place (owner's word): everything above is installed and staged in Edit only.
- Placement: the wings attach at the shoulder blades, `(0, 0.72, 0.5)` studs from the Torso centre (Roblox axes);
  horns at the Head centre. Per-piece offsets are in `forms_fit.json` (the importer centres each MeshPart).
