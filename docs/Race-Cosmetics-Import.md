# Race cosmetics: Studio import checklist

The 16 race cosmetics were modelled in Blender on the game's R6 proportions. They're exported as FBX in
`art/races/fbx/`, and their PBR textures are already uploaded (ids in `art/races/fbx/textures.json`).
Roblox needs each mesh brought in once through Studio's 3D Importer, which the tools can't do.

## Steps (about 2 minutes)
1. Open **NH Combat Test** in Studio, in Edit mode.
2. **Bulk import:** go to **File → Import 3D** (or **Avatar → Import 3D**), select **all 16 `.fbx` files** in
   `E:\Nightmare-Highschool\art\races\fbx\` (Ctrl+A in the file picker), and click **Open**.
3. **In the importer** (applies to all files):
   - **File Dimensions / Scale unit:** **Stud**. The models are built 1 unit = 1 stud.
   - **Rig General → Rig Type:** leave it as detected. The five `W_Tail_*` files carry a 7-bone tail rig; keep it.
   - **Insert Using Scene Position:** off.
   - **Import Only As Model:** on, if the option is there.
   - Click **Import**.
4. In the Explorer, create a **Folder** in **ServerStorage** named **`NHRaceCosmetics`**.
   Drag all 16 imported models into it. Keep their names (`V_Ears_Pointed`, `W_Tail_Bushy`, …).
5. Tell Claude "imported". (Done 2026-10-30.) Claude then:
   - checks every piece's size against `manifest.json`
   - adds the SurfaceAppearance (colour, normal, roughness, metalness) to each piece
   - fixes orientation if needed
   - wires the pieces to the race tab and the character

## The 16 pieces
| Race | Pieces | Tier |
|---|---|---|
| Vampire | `V_Ears_Pointed`, `V_Ears_Swept` | I |
| | `V_Ears_LongSwept` | II |
| | `V_Ears_Elder` | III |
| Werewolf | `W_Ears_Upright`, `W_Ears_Tufted`; `W_Tail_Brush`, `W_Tail_Bushy`, `W_Tail_Bobbed` | I |
| | `W_Ears_Torn`, `W_Tail_Shaggy` | II |
| | `W_Ears_Moon`, `W_Tail_Moon` (charcoal + silver, not tinted) | III |
| Ghoul | `G_Stitch_Jaw`, `G_Stitch_Shoulder` | II |
| | `G_Shroud` | III |

The Wraith's breath and wisps are particles (no meshes). The Ghoul's Tier I look is the ghoul uniform (clothing).
