# School Props (Blender) and School Surfaces (PBR)

The greybox school is being dressed with modelled props and PBR surface materials, made to the [VFX Design Bible](VFX-Design-Bible.md)'s look: candlelit oak, wrought iron, slate, brass and deep crimson enamel.

## School surfaces
**Tool:** `tools/vfx/make_pbr_materials.py` (numpy).
- It writes seamless 1024² PBR sets (colour, OpenGL normal, roughness, metalness).
- Everything uses integer-period noise, so every map tiles.

**On the school** (MaterialVariants in `MaterialService.NHSchoolPBR`):

| Variant | Base material | Studs per tile | Used on |
|---|---|---|---|
| `NH_Linoleum` | CeramicTiles | 6 | classroom floors (two-tone checker, speckle, grime at the grout) |
| `NH_Boards` | WoodPlanks | 12 | floorboards |
| `NH_DeskWood` | Wood | 8 | wood props, furniture placeholders |
| `NH_PaintedMetal` | Metal | 6 | metal parts (chipped enamel with bare metal) |
| `NH_Slate` | Slate | 10 | slate parts |
| *(built-in Plaster)* | Plaster | - | walls |

**Prop-only sets:** `NH_Leather`, `NH_Brass`, `NH_Limestone`, `NH_Iron`, `NH_Paper`.

**Reversible:**
- Every changed part has the tag `NHPbr` and the attribute `NHPbrFrom = "<Material>|<Variant>"`.
- `Studio/pbr_revert.luau` (session tools) restores them.

## Props
**Tool:** `art/props/nh_props.py`. Run it headless in Blender 5.x:

```bash
"E:/Blender/blender.exe" --background --factory-startup --python art/props/nh_props.py -- <Prop|all> --size 1024 --samples 32
```

Batches 4 and 5 are baked at 2048 on the GPU (about 1–2 minutes a prop on the RX 6600 XT):

```bash
"E:/Blender/blender.exe" --background --factory-startup --python art/props/nh_props.py -- <Prop> --size 2048 --samples 64 --gpu
```

- `--gpu` bakes and renders with Cycles on the GPU (HIP here; CUDA or OptiX where present).
- A 2048 bake reads the same seamless sets made at 2048 from `art/props/source_2k/`, so small props aren't baked from upscaled 1024 sources. That folder isn't committed; make it with `python tools/vfx/make_pbr_materials.py art/props/source_2k 2048`.
- 2048 bakes also pack the UV islands at one texel density, by shape with rotation and an 8-pixel gap. Bake margins scale with the size (16 px at 2048). 1024 bakes are unchanged.
- Roblox takes maps up to 4096, so the 2048 maps are used as they are.
- The log line lists each piece's triangles (Roblox caps a mesh piece at 20k).
- Previews show `*_Glass` pieces as glass and `*_Glow` pieces lit, as they look in Roblox. `PREVIEW_PAD` moves the camera back for tall props, and `OPEN_DEG` sets how far a piece opens in the `_open` preview.

**How a prop is made:**
- **Modelling:** each prop is modelled in studs from bevelled parts and wrought-iron curves.
- **Weathering at bake time:**
  - edge wear: lighter wear on wood and leather, bare metal showing through paint and enamel
  - crevice dirt from ambient occlusion
  - rounded-edge normals
- **Bake:** one 1024 atlas per prop: colour × AO, normal, roughness, metalness.
- **Output:** `art/props/fbx/*.fbx`, `art/props/textures/*`, previews in `art/props/previews/`.
- **Asset ids:** in `art/props/props.json`.

**Rigged props** have several meshes, `<Prop>_<Piece>`:
- **Lockers:** `Body` and `Door0` (`Door1`).
- **Vending machine:** `Body`, `Wares`, `Flap`, `Glass`, `Glow`.
- **Altar:** `Altar`, `Reredos`, `Items`, `Glow`. It's split because Roblox caps a mesh at 20k triangles.
- **Bookshelf:** `Case`, plus each book as its own mesh.
- **Football machine:** `Main`, `WheelL`, `WheelR` (origin on the axle; they can spin about Blender Z), `Glass`.
- **Toilet stall:** `Body` and `Door0` (origin on the hinge).
- **Sink:** `Main`, `TapHot` and `TapCold` (origin on the spindle), `Water`.
- **Mirrors:** `Main` and `Mirror`.

Door, flap and tap origins sit on their hinge lines.

**Batch 2 setup** (`Studio/props_setup2.luau`, run after importing the batch-2 FBX files):
- Measures every template from its parts, so it doesn't depend on the dims above.
- Glass pieces become Glass material; Glow pieces become Neon with a PointLight (amber on the vending machine and candelabra, crimson on the altar).
- Tags the vending machine `NHVendingProp` and the bookcase `NHBookshelfProp`, and marks every book `Book = true`.
- Props with no placeholder (chairs, sofa, altar, candelabra, bookcases) get an invisible anchor part named `NHPropSpot_<key>`, which `props_revert.luau` also removes.
- The Staff Room furniture stays clear of the watcher's patrol loop (x 37–52, z 17–29).

**Batch 3 setup** (`Studio/props_setup3.luau`, run after importing the batch-3 FBX files from `art/props/fbx/`):
- Same template steps as batch 2 (scale, SurfaceAppearance, Glass and Neon pieces, bottom-centre pivot, Atomic streaming). The bench, clock, cabinet and alchemy table collide; the rest don't.
- The sconce's Glow gets a warm PointLight and the `NHCandle` tag; the alchemy table's Glow a soft green light.
- The pendulum gets `NHSwing` with its hinge at the top-centre of its own box (±5°, 2 s), animated by `Controllers.World.Ambient`.
- Placed copies are named `<Prop>_<key>` and tagged `NHPropBatch3`; `Studio/props_revert3.luau` removes them. Every placement reports anything solid it overlaps.
- **Hall layout:** the classroom walls face the hall at z 58.5 with 8-stud doors at the room centres (x 62, 92, 122, 152, 182, 212); the door headers carry the room signs, so nothing hangs on them.

**Batches 4 and 5 setup** (`Studio/props_setup4.luau`, run after importing the batch-4 and batch-5 FBX files from `art/props/fbx/`):
- Same template steps as batch 3. The floor props collide (vase, plant, umbrella stand, coat rack, football machine, bleachers, sink, stall); doors, taps, water and glow don't.
- `*_Mirror` pieces become dark reflective glass, and `*_Water` pieces hidden water.
- Glow pieces get the `NHCandle` tag and a warm PointLight (lamp, candles, a wider one on the chandelier).
- The football machine's wheels get `SpinHinge` / `SpinAxis` attributes. Nothing spins them yet, and the drill's placeholder machine in `workspace.Sports` is left alone.
- **Rigged on the locker system:** the stall and the sink are tagged `NHLockerProp`. Each has an invisible `NHPropSpot` part linked by a `Placeholder` ObjectValue, which carries the prompt. Model attributes set the prompt text and the auto-close time:
  - **Stall:** "Stall / Open". `Door0` swings **out** 95°, toward the front of the stall, and shuts after 8 s. The setup picks the swing sign from the geometry and its report checks the door opens outward.
  - **Sink:** "Sink / Turn on". The cross heads turn a quarter (hot one way, cold the other), the water shows, and it turns off after 6 s.
  - **Code:** `Services.Features.LockerProps` reads `PromptObject`, `PromptOpen`, `PromptClose` and `AutoClose` (defaults: Locker, Open, Close, 8 s) and skips models outside the workspace. `Controllers.World.LockerDoors` shows parts with a `ShowWhenOpen` transparency while open. Patch: `Studio/patch_lockers_rig.luau`.
- **Placement:** on the owner's call these go on the baseplate for the builder, not into the school. One copy of each sits in `workspace.NHPropsShowcase`, facing the spawn. Batch 4 is in the front row (z 58, from x −100); the table props sit on low slate plinths. Batch 5 is behind (z 70), with the chandelier hanging 6 studs up. Copies are tagged `NHPropBatch4` / `NHPropBatch5`, and `Studio/props_revert4.luau` removes them.
- **Look:** on theme with the Institution (candlelit gothic: ink, bone, wax, paper, brass, crimson `#600E1A`). Wood is kept to the books, crates and small accents. The stall is black marble with brass-inlaid arches, cast-iron pilasters and a crimson enamel door. The clock, coat rack and hall mirror are cast iron, and the picture frame is black lacquer and gilt.

| Prop | Triangles | Replaces / goes to |
|---|---|---|
| StudentDesk | 4.8k | `Desk` ×48 (R101–R106) |
| TeacherDesk | 4.7k | `TeacherDesk` ×6 |
| Chalkboard | 6.1k | new, on the wall behind each teacher desk (a `ChalkboardSpot` part) |
| Locker | 10.1k (2 pieces) | the 8 hallway lockers, including Locker113, which carries the quest note |
| HidingLocker | 15.2k (3 pieces) | the Records Office and Staff Room hiding lockers |
| StudentChair | 3.5k (wrought iron to match the desk) | batch 2: behind every student desk (48) |
| TeacherChair | 3.9k | batch 2: tucked into each teacher desk (6) and around the Staff Room table (4) |
| Armchair, Sofa | ~3.4k each | batch 2: the Staff Room lounge on the south wall (2 armchairs, 1 sofa) |
| VendingMachine | 13k (5 pieces) | batch 2: over the hallway `VendingMachine` (quest spot LostSpotC keeps its prompt) |
| TrashCan | 2.3k | batch 2: over R106 `TrashBin` (the detention prompt stays), and one in the Staff Room |
| Bookshelf | 11k (Case + 93 books) | batch 2: 9 bookcases replace the Archive's 13 narrow blocks (5 on the south wall, 2 per side wall) |
| Altar | 26k (4 pieces) | batch 2: the Archive's north-west rite corner, facing the room (crimson glow) |
| Candelabra | 10.3k (2 pieces) | batch 2: either side of the altar |
| GrandfatherClock | 14.9k (Case, Pendulum, Glass) | batch 3: the hall, on R103's wall east of the door; the pendulum swings (`NHSwing`) |
| WallSconce | 3k (Sconce, Glow, Glass) | batch 3: the hall, west of each classroom door (6); the flame flickers (`NHCandle`) |
| HallBench | 5.2k | batch 3: the hall, on the R101, R104 and R106 walls (3) |
| NoticeBoard | 3.2k | batch 3: the hall, on the R102 and R104 walls (2) |
| CelestialGlobe | 4.8k | batch 3: the Archive, in front of the east shelves |
| AlchemyTable | 5.8k (Main, Glass, Glow) | batch 3: the Archive's north-east corner (green potion glow) |
| SchoolBell | 3.7k (Bracket, Bell) | batch 3: high on R104's wall, west of its door |
| TrophyCabinet | 10.8k (Main, Glass) | batch 3: the hall, on R105's wall west of the door (x 172.5) |
| CeramicVase | 6.4k | batch 4: an oxblood-glazed floor urn with brass bands and handles (showcase) |
| FlowerVase | 14.9k (Main, Glass) | batch 4: crimson roses, white lilies and baby's breath in a smoky glass vase |
| PottedPlant | 7.9k | batch 4: an aspidistra in a gadrooned limestone urn |
| LunchTray, LunchTrayEmpty | 5.5k / 2.6k | batch 4: a pewter tray full (mash, mystery meat, peas, roll, jelly, apple, milk) and after lunch |
| BookStack | 9.7k | batch 4: six bound books with an inkwell and a quill |
| OilLamp | 3.9k (Main, Glow, Glass) | batch 4: brass and crimson enamel, glass chimney, flame |
| WallClock | 9.5k (Main, Glass) | batch 4: cast-iron case, brass bezel, crimson crest, glass front |
| PictureFrame | 7.0k | batch 4: the school on its hill under a full moon, black and gilt frame |
| CandleCluster | 6.3k (Main, Glow) | batch 4: seven melted pillar candles on an iron tray |
| UmbrellaStand | 10.3k | batch 4: fluted iron, two umbrellas and a cane |
| CoatRack | 6.8k | batch 4: cast-iron hall stand with a crimson scarf and a satchel |
| FootballMachine | 20.8k (Main, WheelL, WheelR, Glass) | batch 4: the Iron Wardens' steam throwing machine (spinning wheels, crate of footballs) |
| Bleachers | 13.3k | batch 5: four tiers of crimson enamel seats on an iron frame |
| Chandelier | 16.7k (Main, Glow) | batch 5: two-tier wrought iron, 12 candles |
| GothicMirror | 6.8k (Main, Mirror) | batch 5: a tall pointed-arch hall mirror in cast iron |
| BathroomMirror | 2.0k (Main, Mirror) | batch 5: an iron washroom mirror with a brass shelf |
| Sink | 7.3k (Main, TapHot, TapCold, Water) | batch 5: a marble washstand with brass pillar taps (turn on: the taps turn, the water runs) |
| ToiletStall | 17.9k (Body, Door0) | batch 5: black marble and iron with a crimson door that swings out; a toilet with a pull-chain cistern inside |
| TowelRail | 1.6k | batch 5: brass, with a crimson towel |

## In Roblox
**Import:**
1. Use File → Import 3D. FBX comes in at 100× scale with a rotated pivot.
2. `Studio/props_setup.luau` then:
   - scales the props to studs
   - adds each prop's SurfaceAppearance
   - gives each template an unrotated bottom-centre pivot
   - works out each door's swing (`SwingDeg`)
   - files the templates in `ServerStorage.NHProps`
   - places a copy over every placeholder in `workspace.School.NHProps`

**Placeholders stay:**
- Each placeholder is made invisible (`NHPropReplaced`, `NHPropOrigTransparency`) but keeps its collision, attributes, prompts and hiding spots, so gameplay is untouched.
- Each prop links back to its placeholder with an ObjectValue named `Placeholder`.
- Prop meshes don't collide and aren't hit by raycasts.
- `Studio/props_revert.luau` undoes the placement.

**Facing:**
- Student desks face away from the teacher desk, and the student sits at the low edge of the lid.
- The teacher desk's drawers face the teacher.
- The chalkboard hangs on the inner face of the wall behind the teacher desk.
- Hallway lockers face the hall, and hiding lockers face their room.

## Animation
**Lockers:**
- **Server,** `Services.Features.LockerProps`, sets the model attribute `Open`:
  - Hiding lockers swing open and shut whenever someone hides or leaves (the HidePrompt's `UserOnly` changes).
  - Quest lockers open briefly when their quest prompt is used.
  - Other hallway lockers get an Open/Close prompt and close themselves after 8 s.
- **Client,** `Controllers.World.LockerDoors`:
  - It swings each door 105° about its hinge line on every client, over 0.45 s open and 0.4 s closed.
  - It works with StreamingEnabled: doors that arrive later are registered when they stream in.
  - It moves "rider" parts with the door (ObjectValues named `Rider`), such as the quest note on locker 113.
  - With Reduce Motion on, the door snaps open instead of swinging.

**Vending machine and bookshelf** (batch 2):
- **Server,** `Services.Features.SchoolProps`, checks every request (distance, cooldown):
  - **Vending machine:** a "Thump", or the existing quest search, sets `RattleAt`.
  - **Bookshelf:** "Pull a book" unanchors every book with a nudge, so they fall with real physics that everyone sees the same way. After 12 s the books float back over 1.6 s.
- **Client,** `Controllers.World.SchoolProps`:
  - Adds the "Thump" and "Pull a book" prompts locally, and only while no quest prompt on that spot is showing.
  - Plays the rattle: the cabinet rocks on its front edge, the wares jitter, the flap clacks and the sign flickers. Reduce Motion and Reduce Flashing tone it down.

## Verified (Studio)
**Classrooms:** desks, teacher desks and chalkboards render correctly (screenshot).

**Locker doors:**
- **Records Office:** hid in the locker and left it. The door opened to −105° in 0.45 s, held and closed, on both hide and leave (client measurement).
- **Hallway:** a hallway locker opened through `Open`.

**Weathered textures (2026-10-31):** all 76 placed batch-1 props use the weathered bake (classroom and locker-row screenshots). The two end lockers of the hall row were turned sideways by the first placement; all eight now face the hall, and `props_setup.luau` faces the row across the hall.

**Texture ids:**
- All 14 props have their four maps in `art/props/props.json`.
- `Studio/props_ids.py` keeps it current: `set` merges upload results, `luau` writes a re-texture script, and `setup2` fills `props_setup2.luau`.

**Batch 2 (2026-10-31):**
- **Placed:** 48 student chairs, 10 teacher chairs, the Staff Room sofa and armchairs, 2 bins, the vending machine, 9 Archive bookcases, the altar and 2 candelabra.
- **Checked:** every prop sits on its floor (raycast), and the classroom, Staff Room, Archive and vending machine were checked in screenshots.
- **Play:**
  - **Vending rattle:** a Thump set `RattleAt`, and the cabinet rocked up to 2.1° with the flap swinging 34°, then returned exactly to rest.
  - **Book fall:** a Pull unanchored all 93 books, and 38 left the case in 2.5 s. All were back, anchored, at 14.5 s.
  - **Prompts:** all 10 appear.
- **Importer quirks:** the importer's pivot is rotated, and `Model.WorldPivot` is ignored once a PrimaryPart is set. So `props_setup2` sets the PrimaryPart's PivotOffset to a world-axis bottom centre, and `Studio/props_fix_pivots2.luau` repairs copies placed with the old pivot.
- **Streaming:** the vending machine and bookcases use `ModelStreamingMode = Atomic`, and the client waits for the prompt's host piece (`VendingMachine_Body`, `Bookshelf_Case`).
- **Look tweaks in Studio:**
  - vending glass is light and see-through, with a shelf light inside
  - the altar's glow is crimson

**Not verified yet:**
- two-player locker sync, and the rattle and book fall seen from a second player

**Batch 3 (2026-11-03):**
- **Baked:** all 8 at 1024 with 32 samples (previews in `art/props/previews/`, sheet `_batch3_final_sheet.png`), maps uploaded, ids in `props.json`.
- **Dry run:** `props_setup3` placed boxes of each prop's real size: no clashes (the first pass hit R103's sign and the rite bone crate, and both props were moved). The stand-ins were removed afterwards.
- **Imported and placed (1.13.1):** all 16 copies, with no clashes and no imports left in the workspace. The trophy cabinet moved to x 172.5, so it no longer crowds the R105 sconce.
- **Tested:** screenshots of the hall and the Archive. In Play at night the clock's textures show, the pendulum swings and the sconces glow.
- **Clock colour map:** uploaded again as `132406564544469` (same image as before). In the Edit view the clock can look plain grey, because Studio caches a failed download; Play shows it correctly.
- **Not verified yet:** the props seen by a second player.

**Batches 4 and 5 (2026-11-03):**
- **Baked:** all 20 at 2048 with 64 samples on the GPU, from the 2048 sources (previews in `art/props/previews/`, sheet `_batch4_final_sheet.png`). At 100% the maps are sharp (stone pores, grain, leather). Maps uploaded, ids in `props.json`.
- **Owner's notes acted on:** higher-quality and non-blurry textures, on theme with the game, the football drill machine, bleachers, a chandelier, mirrors and a bathroom set with a rigged stall door and sinks, a less wooden stall and set, and a stall door that swings out.
- **Dry run:** `props_setup4` placed boxes of each prop's real size (with door, tap, water, mirror, glass and glow stand-ins) on the baseplate: 20 placed in two rows, no clashes, and the stall door opens out. The stand-ins and their templates were removed afterwards.
- **Locker patch, in Play:** all 11 lockers set up, and the 8 hallway prompts still read "Locker / Open"; templates in ServerStorage are skipped.
- **Not verified yet:** the real import and showcase placement (the owner imports the FBX files); the stall door, taps and water in Play on the imported models; the textures seen in Studio; the props seen by a second player. Nothing spins the football machine's wheels yet.

