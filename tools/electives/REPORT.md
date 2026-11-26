# Electives + Anatomy: report (2026-11-25)

Branch `claude/electives-22bb10`, not pushed or merged. NH Combat Test (placeId 98950102230473): everything below is
installed in Edit. **The place is not saved.** Saving is the owner's call. The backups are in
`ServerStorage.NH_Backup.*` (latest: `Electives_Task12_20261125`).

Spec: `docs/superpowers/specs/2026-11-25-electives-anatomy-design.md`. Plan: `docs/superpowers/plans/2026-11-25-electives-anatomy.md`.
Overview for players and devs: the "Electives and Anatomy" section of `docs/Class-Activities.md`.
Import and publish steps for the owner: `PUBLISH_LIST.md`.

## What was built

| Task | What | Where |
| --- | --- | --- |
| 1-3 | `Config.Electives`, `Classes.For` (Tue/Thu periods 3-4); every timetable reader, server and client, goes through it | `live/` |
| 4 | Registrar desk (`NHRegistrarDesk`), Electives service, `ElectivePick`, board UI, remotes | `live/` |
| 5-6 | `Config.Anatomy` (species, steps, organs, 60/25/15 weights) and `ServerStorage.Activities.AnatomyBench` (server judging, twists) | `live/` |
| 7 | Anatomy as an Activities subject in Bench mode; breakdown and species on the result; the Journal; Substitutes (Specimen twist, elective days only) | `live/` |
| 8 | Frog, Raven, Wyvern, 5 tools and the bench set as rigid props: clip-checked rest pose, FBX files, PBR bakes, `Anatomy.Layout` | `render/`, `art/props/` |
| 9 | Nine seated R6 clips with Contact markers, and the `Clips` map | `anim/` |
| 10 | Bench mode in the lesson UI (full-screen content, Quit bottom-left, `SetTimerLabel`) | `live/...Gui.Activities` |
| 11 | The bench renderer: a ViewportFrame scene, your R6 at the bench, physical tools (pick, use, put down), trace, plate, organs, slips | `live/...Activities.AnatomyBench` |
| 12 | Healer perk numbers, mastery (title + monocle), the Specimen Journal in the phone's Report Card app | `Config.Anatomy`, `School.Electives`, `Features.Phone`, `Gui.Phone` |
| 13 | This report, `PUBLISH_LIST.md`, the docs section | |

## Checks (all PASS)

Pure: `classes_pure`, `anatomy_config_pure`, `anatomy_bench_pure`.
Edit: `registrar_desk_edit`, `slots_edit`, `slots_client_edit`, `anatomy_models_edit` (9 props in the layout, 0 imported), `anatomy_clips_edit` (9 clips).
Play (slot 2, restored afterwards; cine check passed before and after each round):

- `electives_play`, `anatomy_play`: Task 7 round.
- `anatomy_client_setup` + `anatomy_client` + `anatomy_client_after`: the renderer driven through its Studio hooks.
  - The rig loaded, with 9 tracks. The trace took 81 points.
  - The Driver was put down on the desk and the plate opened.
  - A deliberate wrong outline played AnatRecoil.
  - Grade A (95%). The Journal kept the Frog's best grade, A+.
- `anatomy_rewards_play`:
  - At level 5, heal is x1.40 and revive is x0.68.
  - With all three species at A, one lesson granted the Anatomist title exactly once, and a second pass granted nothing.
  - A B on any species grants nothing.
  - The monocle was tried and is not in the catalog yet.
  - All state was put back afterwards.
- Client: the phone's `Reports` reply carries `Journal = { Grades = { Frog = "A+" }, Mastered = false }`.

Screenshots of the client round: `shots/bench_{start,trace,desk,held,done}.jpg`.
Close-up renders (the Journal plates once uploaded): `render/out/{Frog,Raven,Wyvern}_close.png`.

## Deviations from the plan

- **Prop motion is tweened, not keyframed.** The plate opening, key turns and organ lifts are tweened by the renderer
  from the `Anatomy.Layout` bones. The props are anchored pieces, not Motor6D rigs, so they have no KeyframeSequences.
- **Stand-ins until import.** The meshes, textures and clips are the owner's to import and publish. Until then the
  bench draws stand-in parts from the Layout (`Real=false`) and plays the clips unpublished through
  `KeyframeSequenceProvider:RegisterKeyframeSequence`. `stage/anatomy_import.lua` is written but has not been run
  against real imports.
- **No IK on the arms.** The tool in hand follows the pointer; the R6 plays the clips.
- **Journal plates** are uploaded and wired (see below). A species with no grade still shows the pencil ring.
- **graphify** is not installed on this machine (`graphify` is not on PATH), so `graphify update .` was not run.

## Known issues seen in the screenshots (for the next pass)

1. **The stand-ins look crude.** The frog is a flat disc with a dome, the tools are flat slabs on the roll, and the
   organs under the plate are hard to see (only the heart's red bead reads). This should mostly go away with the real
   meshes. If the owner wants the stand-ins to read better before the import, the shapes in `buildProp` can be made rounder.
2. **The held tool and organ aren't visible in the hook-driven run.** They follow the mouse, and the test hooks don't
   move it, so they sat out of frame. The same goes for the R6 arms: the camera frames the plate, and the arms are
   below the view. Both need a look with a real mouse in a hand playtest. If the arms never show, move
   `SEAT_CF` / the camera, or drop the dummy.
3. **The Driver put on the desk at (6.5, 0, -1) is outside the camera frame.** The desk zone is wider than the view.
   Either clamp desk drops to the visible area or pull the camera back.
4. **The Raven and Wyvern close-ups** have a blurred, near-camera piece of the head in the top-left corner. Crop it
   off when making the plate images.
5. **The report card says "practice"** because slot 2 had already passed this period. That is expected.

## Owner import (2026-11-25, later)

The owner imported the 9 FBX files and published the 9 clips to the group. `stage/anatomy_import.lua` ran in Edit, and
all 61 pieces went to `ReplicatedStorage.Anatomy.Models`. `anatomy_models_edit` now reports 9 imported models.
Two fixes to the script came out of the first real run:
- **Uniform scale.** Every piece came in at 10x. The script now divides by the median axis ratio, because the
  Layout's 0.05-stud minimum would have fattened the glows, the desk and the wing plates.
- **180-degree turn kept.** The importer turns every mesh 180 degrees about Y, and `CFrame.new(Centre)` dropped that.
  The Driver lay handle-first and the Loupe's ring was away from its glass.

The ids were read from the group's creations (`itemconfiguration.roblox.com/v1/creations/get-assets`, through the
built-in browser):
- **Textures:** 196 maps for 49 pieces, all moderation Green. `stage/anatomy_image_ids.txt` holds the ids, and
  `stage/anatomy_textures.lua` (generated from it) puts a SurfaceAppearance on each piece. The 12 Glow and Glass pieces
  have no bake and keep Neon or Glass. Screenshot: `shots/import_textured.jpg`.
- **Clips:** the 9 published ids are in `AnatomyClips.Clips.Ids`. The renderer loads them first and only falls back to
  `RegisterKeyframeSequence` for a clip with no id.
- Note: `ContentProvider:PreloadAsync` reports Failure through `execute_luau` even for textures the game already uses.
  Judge by a screenshot taken a few seconds after the maps are applied.

### Play round with the real models (2026-11-26)

`anatomy_client` PASS with the real models (`real true`): 9 tracks, a 143-point trace, the Driver on the desk, the
plate open, AnatRecoil on the wrong outline, grade A. `anatomy_client_after` PASS (frog A+). Slot 2 restored, cine
passed before and after, place not saved. Shots: `shots/real_{start,trace,open}.jpg`.

What it showed:
- The frog, its eyes, studs, dial plate and legs, and all five tools render in the bench. The open plate shows the
  hollow body with the cradle inside.
- **Still to fix:**
  1. In the ViewportFrame the brass reads flat and orange: the viewport has no environment lighting for the PBR
     maps. Try `ViewportFrame.Ambient` / `LightColor` / `LightDirection`, or a WorldModel lit from the camera side.
  2. The tool-button bar covers the lower half of the tools on the roll. Raise the camera target or shrink the bar.
  3. The tool in hand is still out of frame in the hook-driven run (see known issue 2 above).
  4. A dark diagonal shape crosses the upper left during the trace. It may be the R6 arm at 3.25x scale. Check
     with a real mouse.
  5. Lifted organs sit beside the frog's head instead of on the card's outline spot.

### Bench visual fixes (2026-11-26)

The five issues above were fixed, and the Play round passed again: `anatomy_client` PASS (real true, 9 tracks, a
140-point trace, recoil, grade A). Shots: `shots/fix_{start,key,open}.jpg`.
1. **Lighting:** neutral key light and a stronger ambient, instead of the dim orange light. The first try washed the
   brass out, so the ambient was lowered to (112, 104, 96). That second value has not been seen in Play yet.
2. **Framing:** the camera is at (0, 9, 9.75) looking at (0, 0, 1.3). The frog's head is about 11% from the top and
   the whole roll sits above the button bar.
3. and 5. **Held tool and organ:** over a panel or outside the view, the tool in hand waits at its last point (or
   above the specimen), so it and the organ on the tweezers stay in frame. A desk put-down over a panel goes back to
   the roll. The test hooks aim each tool at its target, and the test's desk spot is now in view.
4. **R6 clone:** no accessories, no face, and the head is hidden, so the hair and crown no longer cross the view.
   The sleeves show at the bottom corners as the arms reach in.

### Journal plates (2026-11-26)

The three close-ups were cropped to 512 px squares (`render/out/plates/AnatPlate_*.png`). The Raven and Wyvern crops
leave out the blurred piece in the top-left corner. They were uploaded through Studio and their ids are in
`Config.Anatomy.Species.*.Plate`: Frog 99000128465951, Raven 124681137363813, Wyvern 100444371073403. Installed in Edit
(backup `Electives_Plates_20261126`); `anatomy_config_pure` PASS.
- The upload went to the owner's user account (37484441), not the group: Studio's uploader has no group option. Images
  are not permission-locked like animations, so they load in the group's place. If the owner wants them group-owned,
  re-upload the three PNGs as the group and swap the ids.
- The Wyvern image was still in moderation review when it was wired.
- Not yet seen in the phone in Play.

### Brass Loupe Monocle (2026-11-26)

Built at the accessory standard (`art/characters/accessories/nh_kitc_monocle.py`). It's a jeweller's loupe over the
right painted eye (x -0.205, z 1.49), with these parts:
- a knurled gold eye ring sitting 0.012 off the face;
- a flared brass barrel with two turned bands;
- a bezel with three steel screws and a dark glass lens;
- a hinge lug, and a fine gold chain down the cheek to a teardrop fob at the jaw.

The piece is one Head MeshPart, `LoupeMonocle` (10,180 tris), with a 2048 baked atlas.
- **Catalog:** `anatomy-loupe-monocle` in `Config.Accessories`, Slot `Face`, `Earned = true` with an `Earn` line (the
  Standing Path pattern: never sold). `Config.Anatomy.Mastery.Accessory` now names that id. Both are installed in Edit
  (backup `Electives_Monocle_20261126`).
  - There is no Eyes slot yet (Kit C's C4 isn't built), so the monocle takes the Mask slot and isn't worn with a mask.
- **Checks:**
  - `acc_check.py` passes, 0 fails: no clipping on any of the 12 bodies, gap 0.012.
  - `acc_hairfit.py`: 18 of 35 hairs fit (a radial scale k 1.02..1.13; it's in `MASKS`, worn like a mask). The other
    17 still wear it, untucked (the 1.88 rule).
- **Renders:** `shots/monocle_{close,close_f,front34}.jpg`.
- **Owner import:** `art/group-upload-accessories/anatomy-monocle/` holds the FBX and 4 maps. After the import, run
  `tools/accessories/assemble_anatomy_monocle.luau` with the map ids filled in.
  - Mastery's `Grant` adds it to a master's owned list now (it doesn't check for the template).
  - `Accessories.Ready` keeps it out of the Wardrobe until the template is in `NHAccessories`.

## Follow-ups for the owner

- **Healer perk has no consumer.** `Config.Anatomy.HealMult(Level)` (+10% per level) and `ReviveMult(Level)` (-8% time
  per level) exist and are tested, but nothing reads them. The game has no item heal and no player-to-player revive:
  downed players get up on a timer (`Features.Downed`, `Config.DownedDuration`). The Registrar card already promises
  "First-aid pouch heals +10% per level" and "Revive downed friends faster". Building a friend revive (hold E on a
  downed player) and a first-aid pouch is a new gameplay system. **The owner said "Later, log it" (2026-11-25):**
  neither is built. When they are, they should read `HealMult` / `ReviveMult` from the student's Anatomy level.
- **The monocle template** waits for the owner's import (see "Brass Loupe Monocle" above and `PUBLISH_LIST.md`).
- **Import and publish:** see `PUBLISH_LIST.md` (9 FBX files, 200 textures, 9 clips, 3 plates).
- **The Specimens, Poses and Flow canvas boards** from the design stage are unpublished drafts.
