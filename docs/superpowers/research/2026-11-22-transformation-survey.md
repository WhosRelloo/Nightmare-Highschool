# Race transformations: survey (read-only)

- **Date:** 2026-11-23. **Branch:** `race-transformations` in `E:\NH-transform`.
- **Sources:** the repo docs and the Studio mirror `Studio/audit_all/live2` (read only).

## 1. How transformations work today

| Race | Today | Code |
|---|---|---|
| Vampire, Ghoul, Wraith; Werewolf Tier I | **T** toggles the `Transformation` attribute (Tier III adds `TransformationStage = 2`). That gives race eyes, the claw stance (the client swaps to `Assets.Animations.Transformation`) and the transformed outfit. **No 3D body change.** | `Services.Features.Transformation`, `ActionManager.Misc.Transform`, `Controllers.Character.Transformation` |
| Werewolf Tier II+ | The **full wolf**: the body hides and `ServerStorage.NHWolf.Wolf` is welded in its place. Click bites, R jump-bites. | the same, plus `WolfBite` and `WolfLeap` |
| Human, Priest | No transformation (`CAN` lists only the four monsters). Priests have a "Priest" outfit variant. | — |

**The rest of the system:**
- **Outfits:** every piece has a transformed version per form (`UI.FormVariants`, 280 templates; [Clothing-and-Faces](../../Clothing-and-Faces.md) §2).
- **Limits:** a transformation lasts 60 s, then a 30 s cooldown. Being downed or stunned ends it.
- **Race cosmetics** (`RaceCosmetics`, `NHRaceLooks`):
  - Vampire ears; Werewolf ears, tail and fur colour; Ghoul grave wear; Wraith wisps and frost;
  - Looks unlock by tier, and they're chosen in the Bloodline tab's **Looks** section;
  - the server validates them (`NHLineage.SetLook`).
- **These designs:** 3D **augmentations** layered over the student's body while transformed: wings, horns, fur, bone, shroud, ice. They plug into the same `Transformation` attribute.

## 2. The race × transformation list

| Race | Forms designed here | Note |
|---|---|---|
| Vampire | V1 Nocturne, V2 Night Sovereign | — |
| Werewolf | W1 Moonbound, W2 Feral Lord (the hybrid, Tier I to II) | The full wolf at Tier II+ stays the owner's rigged wolf. |
| Ghoul | G1 Ossuary, G2 Gravecloth | — |
| Wraith | R1 Hollow Shroud, R2 Frost Revenant | — |
| Human, Priest | none today | **Open question:** a Priest "Sanctified" form (Fallen-style feathered wings in Dove, the Sovereign halo) is ready to show if wanted. |

## 3. The body matrix every form must fit

- **Bodies:** the same 12 as the injury survey. Male: Standard, Lean, Athletic, Muscular, Stocky, Heavy. Female: Female, Petite, Toned, Strong, Curvy, Plus. All are inside the R6 boxes, and only depth varies (0.87 to 1.23).
- **Heights:** uniform scale per race:
  - Vampire 0.90 to 1.22;
  - Werewolf 0.95 to 1.22;
  - Ghoul 0.82 to 1.14;
  - Wraith 0.90 to 1.22.
- **Concept coverage:** every race sheet shows each direction on a male at the race's tallest height and a female at its shortest. Eight bodies are used across the sheets: Muscular, Petite, Athletic, Curvy, Heavy, Toned, Plus, Lean, plus Stocky, Standard and Strong in places.
- **Fitting method:** fur and bone are raycast onto each body's real surface. Wings and horns anchor to the shoulder blades and the head, which are identical on every body, so they need only the height scale.

## 4. Roblox limits that shape the build

- **MeshParts:** at most 20k tris each. Accessories weld to `Torso` or `Head` attachments.
- **SurfaceAppearance:** colour, normal, metalness and roughness at up to 1024².
- **Wings animate** through a rigged MeshPart: Bones driven by an AnimationTrack. A Bone-skinned wing per style keeps the flap clip shared across styles (see the spec, §5).
