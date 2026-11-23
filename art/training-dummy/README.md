# NH Training Dummy (R6, PBR)

A beaten gym / boxing-club training dummy for the combat dummies, built on the standard **non-bending R6 rig**:
six rigid parts with true R6 proportions. Each part can replace the matching part of a stock R6 rig, the Motor6Ds
stay as they are, and every R6 animation plays unchanged. It has no blood or gore. The wear is scuffs, punch dents,
dust, duct tape, chipped paint and a little brown rust on the steel.

- **Torso**: stitched dark-brown leather heavy bag. It has a faded painted target on the chest with punch dents
  and polished, scratched leather around it, two black webbing belts with steel buckles on the front and riveted
  steel plates on the back, duct-tape repairs (an X on the chest, a patch, strips on the right side, black gaffer
  tape on the back), and a spray stencil on the back: "No. 3 / N.H. / BOXING CLUB / PROPERTY OF NIGHTMARE HIGH
  ATHLETICS".
- **Head**: a faceless stitched leather sack (the R6 head shape, about 1.2 studs across) with a centre seam, a
  duct-tape X on the face, a padded headguard band, a webbing crown strap and rivets.
- **Arms**: olive canvas sleeves with corner seams and boxing hand-wraps over the fists. The right arm has a
  duct-tape wrap. The left arm has a strap and a gaffer patch.
- **Legs**: dark canvas with rubber boot cuffs and ribbed soles. The right leg has a knee strap and a tape X. The
  left leg has a gaffer wrap.

Previews: `previews/preview_front.png`, `preview_three_quarter.png`, `preview_back.png`, `preview_posed.png`
(posed on the rig), `preview_closeup.png` (bake detail) and `preview_sheet.png` (all five).

## Files

| File | What |
|---|---|
| `fbx/NH_TrainingDummy.fbx` | **For Studio.** All six parts as plain meshes, assembled at the R6 rig offsets, with one material per texture set |
| `fbx/NH_TrainingDummy_Rigged.fbx` | The same parts skinned to an R6 armature (see Rig). For Blender, Moon or other animation tools |
| `rig_training_dummy.luau` | Studio command bar: builds the full R6 rig from the imported parts, or swaps them into the existing dummies |
| `textures/dummy_<set>_color.png` | ColorMap (albedo, sRGB), 1024² |
| `textures/dummy_<set>_normal.png` | NormalMap (tangent space, OpenGL / +Y), 1024², baked high to low |
| `textures/dummy_<set>_roughness.png` | RoughnessMap, 1024² |
| `textures/dummy_<set>_metalness.png` | MetalnessMap, 1024² (buckles, plates, rivets) |
| `NH_TrainingDummy.blend` | The rigged low poly (armature `R6_Rig`) with the final materials and the preview lights and camera |
| `build_training_dummy.py` | Rebuilds everything: the low and high poly, the bakes, the textures, the FBX, the previews and the `.blend` |
| `make_stencils.py`, `src/stencil_back.png` | The back stencil mask (Pillow) |
| `build_report.json` | Tri counts, bounding boxes and UV coverage, written by the build |

There are three texture sets: **Head** (Head), **Torso** (Torso) and **Limbs** (the four limbs share one atlas).
That makes 12 PNGs to upload.

## Parts

| Part | Tris | Verts | Roblox size X × Y × Z (studs) | Texture set |
|---|---|---|---|---|
| `Head` | 1144 | 662 | 1.30 × 1.28 × 1.30 | Head |
| `Torso` | 688 | 438 | 2.06 × 2.00 × 1.09 | Torso |
| `Left Arm` | 384 | 226 | 1.06 × 2.00 × 1.06 | Limbs |
| `Right Arm` | 288 | 146 | 1.03 × 2.00 × 1.03 | Limbs |
| `Left Leg` | 288 | 146 | 1.02 × 2.00 × 1.02 | Limbs |
| `Right Leg` | 384 | 226 | 1.07 × 2.00 × 1.07 | Limbs |
| **Total** | **3176** | | | |

UV coverage of the 1024² atlases: Head 64%, Torso 63%, Limbs 66%.

The R6 part sizes are Torso 2×2×1, arms and legs 1×2×1, and Head 2×1×1 (the stock head mesh shows about
1.2×1.2×1.2). The meshes keep those boxes. Belts, straps, wraps and buckles stand a few hundredths of a stud
proud. **Every part's bounding box is centred on the part's origin**, because Roblox's 3D importer re-centres each
mesh on its bounding box. That way no part drifts off its Motor6D.

Low poly is used in game. The high poly exists only for the bake: the same analytic surface sampled about every
0.0065 studs, with real displacement for the stitching, seams, punch dents, creases, tape edges, webbing ribs,
hand-wrap layers, boot ribs and rivets. It isn't kept in the `.blend`; the script recreates it.

## Import into Studio (owner)

Upload under **group 15981569** as usual. Nothing here has been uploaded.

**Upload staging:** `art/group-upload-training-dummy/` has the same files named like the other kits:
`NHDummy_TrainingDummy.fbx` (the same file as `fbx/NH_TrainingDummy.fbx`) and
`NHDummy_{Head,Torso,Limbs}_{color,normal,roughness,metalness}.png` (the same files as `textures/dummy_*`).
Upload from either place.

**Uploaded (group 15981569, 2026-11-13)**. `rig_training_dummy.luau` applies these ids:

| Set | ColorMap | NormalMap | RoughnessMap | MetalnessMap |
|---|---|---|---|---|
| Head | 90720393713973 | 72363495474083 | 126110504698334 | 140283783889253 |
| Torso | 109506468309208 | 118756881567200 | 116033294607755 | 84948339306528 |
| Limbs | 104824909650697 | 133613699384500 | 96622949065240 | 120915706016519 |

In NH Combat Test the imported kit is `Workspace.NHDummy_TrainingDummy` and the rigged dummy is
`Workspace.NH Training Dummy`, built 8 studs to its +X.

**Swapped into the combat dummies (2026-11-13)**: all six rigs in `ServerScriptService.Services.Studio.Dummy.Npcs`
(Parry, Attacking, PostureBreak, Inf Dummy, Blocking at 0.9 scale; ParryTrade at 0.8) now use the dummy MeshParts,
scaled to each rig's own scaled joints. Their Motor6Ds, attachments and values are unchanged. The originals are
backed up in `ServerStorage._DummyNpcs_PreTrainingDummy_Backup`.

1. **Upload the 12 textures** (Asset Manager → Bulk Import, or Creator Hub → group → Decals/Images). Note each
   image id. Keep the set and map name straight, for example `dummy_torso_normal`.
2. **Import the mesh**: File → Import 3D → `fbx/NH_TrainingDummy.fbx`, with the creator set to the group.
   - Leave *Import as a single mesh* (merge) **off**, so you get six MeshParts named `Head`, `Torso`,
     `Left Arm`, `Right Arm`, `Left Leg`, `Right Leg` inside one model.
   - The units are already set (the FBX is written at 0.01, the same as the other NH kits). The Torso should
     come in at about 2.06 × 2.00 × 1.09 studs.
   - Import this plain-mesh FBX, not the rigged one. Studio would turn the armature into Bones and skinned meshes,
     and R6 animations drive Motor6Ds, not Bones.
3. **Add a SurfaceAppearance to each MeshPart** with that part's set:
   - `Head` → `dummy_head_*`
   - `Torso` → `dummy_torso_*`
   - `Left Arm`, `Right Arm`, `Left Leg`, `Right Leg` → `dummy_limbs_*`

   Set ColorMap, NormalMap, RoughnessMap and MetalnessMap. Leave AlphaMode on Overlay; the ColorMap has no
   transparency.
4. Set each MeshPart to **CollisionFidelity = Box** and **RenderFidelity = Automatic**, and turn **DoubleSided off**.
5. **Rig it.** Rename the imported model to `NH_TrainingDummy`, then run `rig_training_dummy.luau` in the
   command bar. Use NH Combat Test (or a copy), never production.
   - `MODE = "build"` (the default) makes **`NH Training Dummy`**, a complete R6 rig next to the kit. It has a
     Humanoid (RigType R6) with an Animator, a HumanoidRootPart (2×2×1, invisible), the six stock R6 Motor6Ds
     (RootJoint, Neck, Left/Right Shoulder, Left/Right Hip, with the stock C0/C1 values, so every R6 animation plays
     unchanged) and the 19 stock R6 attachments (Right/LeftGrip, shoulders, feet, hat, face, waist and so on).
     `ANCHOR = true` pins it in place as a static target. To make it a combat dummy, drop it into
     `ServerScriptService.Services.Studio.Dummy.Npcs`.
   - `MODE = "swap"` re-skins every existing rig in `ServerScriptService.Services.Studio.Dummy.Npcs`. It replaces
     each part with the dummy MeshPart but keeps that rig's own Motor6Ds, attachments, attributes and scripts, and it
     removes Shirt, Pants, BodyColors and CharacterMesh so they don't fight the SurfaceAppearance.
   - The builder was checked in NH Combat Test's edit DataModel with stand-in parts parented to `nil`, so nothing was
     added to the place. The parts landed at the exact R6 offsets (Head +1.5, arms ±1.5, legs ±0.5 / −2), with all
     six joints, 19 attachments and an Animator.

   *Optional:* if hitboxes must use the exact R6 sizes, set `Torso.Size = 2,2,1` and the limbs to `1,2,1` after
   rigging. The mesh scales down by about 4%, which is hard to see.

## Rig (Blender / rigged FBX)

`R6_Rig` has seven bones: `HumanoidRootPart`, then `Torso` (the RootJoint), then `Head` (Neck), `Right Arm` /
`Left Arm` (Shoulders) and `Right Leg` / `Left Leg` (Hips). Each bone's head sits at the stock R6 Motor6D pivot:
the Torso centre, the top of the Torso, (±1, +0.5) for the shoulders and (±1, −1) for the hips, relative to the
Torso. Each part is in one vertex group at 100%, so the rig is rigid and non-bending like R6. Every part's origin
stays at its own centre. `previews/preview_posed.png` is a guard pose set on this rig. The `.blend` is saved in
rest pose.

## Rebuild

```
python make_stencils.py
E:/Blender/blender.exe -b --factory-startup -P build_training_dummy.py -- [--samples 128] [--no-render] [--views front,posed]
```

The build bakes on the GPU (HIP on this machine) and takes a few minutes.
