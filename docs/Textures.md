# Textures (builder sets)

25 tileable PBR texture sets for building NH Combat Test, made 2026-11-03.
- **Where they're from:** 14 match the gritty night-town style of the owner's reference screenshots; 10 are Nightmare High's own gothic sets.
- **Original work:** everything is generated from scratch by `art/textures/nh_textures.py`. Nothing is copied from another game.
- **CastleStone** came later, with props batch 8: the cloister arch's own wall stone, made by `tools/vfx/make_castle_stone.py` from the 2048 limestone set the props use. The arch's wall piece uses the same stone at the same scale (8 studs a tile), so a wall built in `NHCastleStone` blends into the arch.

## Using them in Studio
Every set is a **MaterialVariant** in `MaterialService`, named `NH<Name>`. Pick one in either of two ways:
- In the **Material Manager**.
- On a part: set `Material` to the base below and `MaterialVariant` to the name.

A ready-made sample wall, one 12 × 12 block per set, is in `ServerStorage.NHTextureSwatches`; drag it out to compare.

| Set | Variant | Base material | Studs per tile | Looks like |
|---|---|---|---|---|
| ParquetWood | NHParquetWood | WoodPlanks | 8 | warm orange basket-weave parquet |
| FloorPlanks | NHFloorPlanks | WoodPlanks | 12 | worn classroom floorboards |
| RedBrick | NHRedBrick | Brick | 8 | dark maroon brick, sooty |
| StoneBlock | NHStoneBlock | Brick | 10 | grey-blue cut stone walls |
| Cobblestone | NHCobblestone | Cobblestone | 8 | small dark granite setts |
| HexTile | NHHexTile | Pavement | 10 | red-brown hex pavers |
| Pavers | NHPavers | Pavement | 12 | big grey stone slabs |
| Concrete | NHConcrete | Concrete | 16 | stained, pitted concrete |
| PaintedMetal | NHPaintedMetal | Metal | 8 | maroon steel, scratched to bare metal and rust |
| DirtyTile | NHDirtyTile | Plaster | 8 | old white wall tile, missing tiles |
| DarkPlaster | NHDarkPlaster | Plaster | 12 | near-black scuffed plaster |
| CheckerMarble | NHCheckerMarble | Marble | 8 | cream and brown checker floor |
| OldBoards | NHOldBoards | Wood | 10 | weathered boards, peeling blue paint |
| SnowGround | NHSnowGround | Snow | 16 | packed snow |
| DamaskWallpaper | NHDamaskWallpaper | Fabric | 6 | crimson wallpaper with a gold damask lattice |
| CrimsonVelvet | NHCrimsonVelvet | Fabric | 6 | crushed crimson velvet |
| GothicStone | NHGothicStone | Limestone | 10 | cathedral ashlar with moss and rain streaks |
| WroughtIron | NHWroughtIron | DiamondPlate | 8 | black iron lattice with rivets |
| StainedGlass | NHStainedGlass | SmoothPlastic | 8 | leaded jewel-coloured glass |
| BloodMarble | NHBloodMarble | Marble | 10 | polished black marble, crimson veins |
| GothicOakPanel | NHGothicOakPanel | Wood | 8 | dark oak raised wall panels |
| RuneSlate | NHRuneSlate | Slate | 12 | slate slabs carved with crimson-lit runes |
| MossyFlagstone | NHMossyFlagstone | Slate | 12 | irregular flagstones, moss in the joints |
| QuatrefoilTile | NHQuatrefoilTile | Marble | 6 | cathedral floor with black quatrefoils |
| CastleStone | NHCastleStone | Limestone | 8 | the courtyard cloister arch's weathered grey castle stone (no joints), so a wall blends into the arch; made by `tools/vfx/make_castle_stone.py` |

Asset ids for every map are in `art/textures/textures.json`.

## How they're made
Run:

    "E:/Blender/blender.exe" -b --factory-startup --python art/textures/nh_textures.py -- [names...]

It runs in background Blender (numpy) and takes about 22 minutes for all 24.

- **Tiling:** every pattern and every noise lattice wraps, so each map tiles with no seams.
- **Noise:** periodic gradient (Perlin) noise, domain warping for organic shapes, and Voronoi for stones and glass.
- **Finishing pass for every set:**
  - cavity shading baked into the colour (Roblox materials have no AO slot)
  - grunge: packed dirt, grime, drips, dust and scuffs; the amount per set is in `GRUNGE`
  - worn high edges
  - micro detail in the normals
  - roughness that rises with the dirt
- **Files:**
  - 2048 masters go to `art/textures/_master/`. They stay local and out of git; the script rebuilds them.
  - 1024 game copies go to `art/textures/<Name>/`. Roblox caps uploaded images at 1024.
  - Maps are `<Name>_color`, `_normal` (OpenGL), `_rough` and `_metal`.
- **Previews:** `nh_textures_preview.py` renders each set with the props' preview lights on a bevelled block on a floor of the same material, into `_lit_sheet.png`. `_sheet.png` is the flat colour sheet, 2 × 2 so seams would show.
- **Updating:** after an upload, replace the ids in `textures.json`. Then run `Studio/tex_variants.luau`, a scratch script that updates the variants in place.
