# NH Fist Gear + Heat Meter (group upload)

Owner uploads to group 15981569. Nothing here is uploaded or committed.
Built headless in Blender 5.2 (the MCP live session on :9876 was not running).

## Files

### Hand gear (FBX + 1024 PBR, one material each)
| File | Tris | Size (studs, X x Y x Z) | Weld C0 on the arm (MeshPart centre) | Max reach outside arm | Notes |
|---|---|---|---|---|---|
| `NHGear_HandWraps.fbx` | 1282 | 1.158 x 0.784 x 1.177 | `CFrame.new(0, -0.677, -0.009)` | 0.098 | off-white cloth boxing wraps, X-crossed turns, two tape strips, crimson hem stripe, frayed loose tail |
| `NHGear_WeightedGloves.fbx` | 1066 | 1.166 x 0.733 x 1.198 | `CFrame.new(0, -0.688, -0.016)` | 0.115 | dark leather fingerless glove, quilted pad (crimson thread), riveted iron weight plate with NH crest, crimson wrist strap + brass buckle, knuckle roll |
| `NHGear_BrassKnuckles.fbx` | 1188 | 1.095 x 0.679 x 0.111 | `CFrame.new(0, -0.729, -0.544)` | 0.1008 | tarnished brass duster on the back of the fingers: 4 raised rings, spiked knuckle bosses, skull crest on crimson enamel, nicked edges |

Textures per piece, all 1024x1024 PNG: `<Piece>_Color.png` (sRGB), `_Normal.png` (tangent space, OpenGL +Y, same as Roblox), `_Roughness.png`, `_Metalness.png`.
Use them in a SurfaceAppearance (ColorMap, NormalMap, RoughnessMap, MetalnessMap) on the MeshPart.

### Armory icons (256x256, transparent)
`NHIcon_HandWraps.png`, `NHIcon_WeightedGloves.png`, `NHIcon_BrassKnuckles.png`: 3/4 renders of the baked assets on a dark R6 arm stub that fades out, with warm rim light, crimson + ember glow and a soft drop shadow. Checked at 96 px and 64 px.

### Heat meter: ember brazier on the RIGHT health-bar end cap
| File | Size | Use |
|---|---|---|
| `NHHeat_Frame.png` | 256x256 RGBA | cold dark-iron gothic brazier: open cage bowl, brass rim, spires. Interior is dark sooty iron (empty state). |
| `NHHeat_Fill.png` | 256x256 RGBA | glowing coals + small flame only. The cage straps and rim are already cut out, so draw it **on top of** the Frame (ZIndex +1). |
| `NHHeat_Glow.png` | 384x384 RGBA | soft ember halo for the full-bar pulse (colour in RGB, strength in alpha). Draw **behind** the Frame. |
| `NHHeat_Spark.png` | 64x64 RGBA | single ember spark sprite. |
| `NHHeat_Flare.png` | 256x256 RGBA | radial gold-ember flare burst for EX-skill fire. |

The brief changed from a 1024x96 strip to this brazier, so there is no 9-slice. Frame and Fill are fixed-size art drawn with `ScaleType = Fit`.

## Placement: hand gear on the R6 arm
- Modelled one hand, centred on the arm's bottom end. FBX origin = arm bottom-centre = **(0, -1, 0)** in the arm's local space (studs).
- Each piece is exactly symmetric across the arm's X axis, so the mirror is the same mesh. Use the **same MeshPart and the same offset on both Left Arm and Right Arm**.
- Axes: modelled Z-up and exported Y-up / -Z-forward, so the gear's front faces the character's front (arm local -Z). The weight plate and the knuckle duster sit on the front face of the hand.
- Export convention matches `group-upload-accessories` and `group-upload-training-dummy`: modelled in studs, FBX `global_scale=0.01` (UnitScaleFactor 1). If an import comes in at the wrong size, set `MeshPart.Size` to the stud size in the table.
- Weld (Part0 = arm, Part1 = gear, C1 = identity): `C0` = the value in the table. A MeshPart's CFrame is its bounding-box centre, so C0 is the bbox centre in arm space and **not** (0,-1,0).
  - HandWraps      `CFrame.new(0, -0.677, -0.009)`
  - WeightedGloves `CFrame.new(0, -0.688, -0.016)`
  - BrassKnuckles  `CFrame.new(0, -0.729, -0.544)`
- If you pivot on the FBX origin instead, for example with an Accessory Attachment or `PivotOffset`, the origin offset from the arm centre is `CFrame.new(0, -1, 0)` for all three.
- Gear spans from about 0.07 studs below the hand's end (it wraps over the fist face) to 0.61-0.72 studs up the arm. Nothing reaches more than 0.115 studs outside the arm block.

## Placement: Heat brazier (about 44x44 px on screen, right cap, mirroring the hunger reliquary on the left)
- Frame and Fill: same size and position, AnchorPoint (0.5, 0.5), centred on the right end cap. Fill goes above Frame.
- Glow: 1.5x the Frame size (66x66 when Frame is 44x44), same centre, under the Frame. The halo is centred on the bowl.
- **Fill reveal (bottom to top), in the 256 px source:**
  - coals bottom y = **158**, coals top (heap over the rim) y = **49**, flame tip y = **34**
  - full reveal range = y 34 to 158 (top to bottom). At 44 px that is y 5.8 to 27.2.
  - Suggested setup: put the Fill ImageLabel inside a `ClipsDescendants` Frame anchored at the bottom. Its height = `fillBottomPx - (fillBottomPx - fillTopPx) * heat`, measured from the top of the 44 px box, with the inner image fixed.
- Spark: emit from the coal heap and flame region. Flare: centre on the brazier, scale up and fade.

## Contact sheet
`NHFistGear_Sheet.png`: gear renders (3/4 and fist view, baked maps), texture sets, icons at 256/96/64, the meter pieces, fill states 0/33/66/100%, and an in-context HUD mock at 1:1 and enlarged.

No blood or gore anywhere. The crimson is a hem stripe, thread, leather and enamel only.
