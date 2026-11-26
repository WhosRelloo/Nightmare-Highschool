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
- **Journal plates** show a name card until `Config.Anatomy.Species[Id].Plate` is set to an uploaded image id.
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

## Follow-ups for the owner

- **Healer perk has no consumer.** `Config.Anatomy.HealMult(Level)` (+10% per level) and `ReviveMult(Level)` (-8% time
  per level) exist and are tested, but nothing reads them. The game has no item heal and no player-to-player revive:
  downed players get up on a timer (`Features.Downed`, `Config.DownedDuration`). The Registrar card already promises
  "First-aid pouch heals +10% per level" and "Revive downed friends faster". Building a friend revive (hold E on a
  downed player) and a first-aid pouch is a new gameplay system. **The owner said "Later, log it" (2026-11-25):**
  neither is built. When they are, they should read `HealMult` / `ReviveMult` from the student's Anatomy level.
- **BrassLoupeMonocle** is not modelled and not in `Config.Accessories`. Mastery calls `Accessories.Grant` on every
  lesson, so it backfills once the accessory is added.
- **Import and publish:** see `PUBLISH_LIST.md` (9 FBX files, 200 textures, 9 clips, 3 plates).
- **The Specimens, Poses and Flow canvas boards** from the design stage are unpublished drafts.
