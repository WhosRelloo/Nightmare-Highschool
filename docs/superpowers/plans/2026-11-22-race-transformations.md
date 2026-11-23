# Race Transformations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** while transformed, each monster race wears sculpted 3D augmentations over the student's own body:
- wings, horns, fur, bone, grave-cloth, ice and spectral pieces;
- animated, customizable, fitted to all 12 body meshes and every height;
- still readable as a student.

**Gate:** build nothing until the owner picks the directions and the style lists (spec §8).

**Architecture:**
- **Data:**
  - `ReplicatedStorage.Config.Forms`: the races' forms, their parts, the allowed wing and horn styles, palettes, finishes and tier unlocks;
  - `Lineage.Looks` gains the new slots, validated by `NHLineage.SetLook`.
- **Server:** `Services.Features.Transformation` sets `Transformation` as today. A new `Services.Player.FormLooks` resolves the player's Looks into an `NHFormLook` attribute (a compact string).
- **Client:** `Controllers.Character.FormParts`:
  - clones the pieces from `ReplicatedStorage.Assets.Forms` for every transformed character within 150 studs;
  - welds them to the Torso and Head attachments, scaled by height;
  - applies the palette SurfaceAppearances;
  - plays the wing clips (idle, flap, fold, flare) on the wing Bone rig, and spins the halo.
- **The full wolf at Tier II+** stays as it is.

**Tech Stack:**
- Blender 5.2 headless (`art/characters/transformations/`):
  - `hqwing.py`: the wing and horn generators;
  - `transform_concepts.py`: per-race parts;
  - `nhfig.py`: fitting helpers.
- PaintRigV3 proportions; NHBodyTypes.
- Luau; the phase harness.

**Spec:** `docs/superpowers/specs/2026-11-22-race-transformations-design.md`.

## Global Constraints

- **Owner rules:**
  - cool, high quality, on theme, no gore;
  - animated and customizable;
  - **still look like students**: face and uniform readable; no werewolf muzzle; no fur on the head; Wraith heads clear; no Wraith lower-body shroud; no claws on any race; no thumb or fingertip hooks on wings;
  - sculpted geometry only.
- **Art:**
  - PaintRigV3 opened read-only;
  - no blocky organics;
  - PBR maps per material;
  - check every style on every body from 3 angles before baking.
- **Fit:**
  - wings and horns anchor to body-independent points (the shoulder blades, the head), with height scale only;
  - fur, bone and wraps get 12 raycast-fitted variants per region.
- **Studio:**
  - NH Combat Test only, on slot 2;
  - a fresh snapshot each round;
  - never save, close or revert;
  - one Studio driver at a time.

## File structure

| Path | What |
|---|---|
| `art/characters/transformations/hqwing.py` | the wing skeleton, the 7 wing styles, the 7 horn styles, palettes and finishes (concept generator, promoted) |
| `art/characters/transformations/form_models.py` | new: bakes every style as a Roblox-ready mesh: the wing Bone rig and skin weights, horns, per-body fur, bone and wrap regions; FBX at 0.01 scale, -Y forward, centred |
| `art/characters/transformations/form_clips.py` | new: the wing clips (idle, flap, fold, flare) as KeyframeSequences on the wing rig, from `Wing.skeleton()` |
| `art/group-upload-forms/` | the textures for upload |
| `tools/forms/live/ReplicatedStorage.Config.Forms.luau` | new |
| `tools/forms/live/ReplicatedStorage.Lineage.luau` | modify: the new Look slots and their tier unlocks |
| `tools/forms/live/ServerScriptService.Services.Player.FormLooks.luau` | new |
| `tools/forms/live/StarterPlayer.StarterPlayerScripts.Controllers.Character.FormParts.luau` | new |
| `tools/forms/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.Bloodline.luau` | modify: the Looks section gets the new slots, with a 3D preview |
| `tools/forms/checks/{forms_pure,forms_fit,forms_anim,forms_looks}.lua` | checks |

## Part 1: repo tasks

### Task 1: Config and the Looks (pure, TDD)

- [ ] `forms_pure`:
  - each race's allowed styles;
  - tier unlocks;
  - `ResolveLooks` falls back to a Tier I option above your tier;
  - `NHFormLook` encode and decode;
  - `SetLook` rejects styles a race can't use.
- [ ] Write `Config.Forms` and the `Lineage` additions until it passes. Commit.

### Task 2: Bake the models

- [ ] `form_models.py`:
  - the wing per style as a skinned mesh, with Bones `Hum`, `Fore`, `D1a`/`D1b` to `D4a`/`D4b` (no thumb), and weights from the skeleton;
  - the horns per style;
  - fur, bone and wrap regions per body (12), raycast-fitted as in the concepts.
- [ ] PBR bakes: palette and finish sets as SurfaceAppearance textures (1024² membrane and feathers, 512² bones and horns).
- [ ] `forms_fit` (Python): no vertex inside a body, everything centred, tri budgets met (spec §7). A check sheet per body.
- [ ] Commit the scripts, the fit JSON and the sheets. The FBX go to `E:/NH-Work/forms`.

### Task 3: The wing clips

- [ ] `form_clips.py` writes KeyframeSequences for the wing rig:
  - Idle (a breathe, 3 s loop);
  - Flap (1.33 s loop, the digits trailing);
  - Fold (0.4 s);
  - Flare (0.6 s, on transform).
- [ ] The owner publishes them to the group. I find the ids myself.

### Task 4: The client and the server

- [ ] `FormLooks`: resolves Looks into `NHFormLook` on join, on a Look change and on transform.
- [ ] `FormParts`:
  - weld, scale and skin;
  - play the clips: Idle while standing, Flap while sprinting or airborne, Fold on landing;
  - Reduce Motion holds the idle;
  - hide hats and fold capes while transformed.
- [ ] The Bloodline Looks section: the new slots and a viewport preview of the student wearing them.
- [ ] Commit.

## Part 2: Studio tasks

- [ ] **The owner** imports the mesh set and uploads the textures, then says "imported". I find the ids.
- [ ] **Round A:** `forms_looks` (set Looks, the server rejects bad ones) and `forms_pure` in the Edit VM.
- [ ] **Round B:** `forms_fit` in Play: every race × direction × 12 bodies through admin `SetBuild` and `SetRace`, with screenshots from 3 angles, against capes, hats, coats and race cosmetics.
- [ ] **Round C:** `forms_anim`: the flap plays on sprint and jump, the fold on land, Reduce Motion is honoured, frame time stays under budget with 10 transformed players.
- [ ] **Round D, regressions:** Transformation (T, duration, cooldown), the full wolf, combat, Downed, grips.
- [ ] Docs, CHANGELOG, and the Discord post after the testing gate.
