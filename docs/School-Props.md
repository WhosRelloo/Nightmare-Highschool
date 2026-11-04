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
- `*_Mirror` pieces become a dark reflective finish (SmoothPlastic, reflectance 0.35; Glass read as a pale panel), and `*_Water` pieces hidden water.
- Glow pieces get the `NHCandle` tag and a warm PointLight (lamp, candles, a wider one on the chandelier).
- The football machine's wheels get `SpinHinge` / `SpinAxis` attributes. Nothing spins them yet, and the drill's placeholder machine in `workspace.Sports` is left alone.
- **Rigged on the locker system:** the stall and the sink are tagged `NHLockerProp`. Each has an invisible `NHPropSpot` part linked by a `Placeholder` ObjectValue, which carries the prompt. Model attributes set the prompt text and the auto-close time:
  - **Stall:** "Stall / Open". `Door0` swings **out** 95°, toward the front of the stall, and shuts after 8 s. The setup picks the swing sign from the geometry and its report checks the door opens outward.
  - **Sink:** "Sink / Turn on". The cross heads turn a quarter (hot one way, cold the other), the water shows, and it turns off after 6 s.
  - **Code:** `Services.Features.LockerProps` reads `PromptObject`, `PromptOpen`, `PromptClose` and `AutoClose` (defaults: Locker, Open, Close, 8 s) and skips models outside the workspace. `Controllers.World.LockerDoors` shows parts with a `ShowWhenOpen` transparency while open. Patch: `Studio/patch_lockers_rig.luau`.
- **Placement:** on the owner's call these go on the baseplate for the builder, not into the school. One copy of each sits in `workspace.NHPropsShowcase`, facing the spawn. Batch 4 is in the front row (z 58, from x −100); the table props sit on low slate plinths. Batch 5 is behind (z 70), with the chandelier hanging 6 studs up. Copies are tagged `NHPropBatch4` / `NHPropBatch5`, and `Studio/props_revert4.luau` removes them.
- **Look:** on theme with the Institution (candlelit gothic: ink, bone, wax, paper, brass, crimson `#600E1A`). Wood is kept to the books, crates and small accents. The stall is black marble with brass-inlaid arches, cast-iron pilasters and a crimson enamel door. The clock, coat rack and hall mirror are cast iron, and the picture frame is black lacquer and gilt.

**Batches 6 to 9 setup** (`Studio/props_setup6.luau`, run after importing their FBX files from `art/props/fbx/`):
- Same template steps as batch 4. `*_Pool` is water that always shows (the fountain). `*_Wall` gets the seamless castle stone (the cloister arches). Glow pieces get a warm light and `NHCandle`, except the boiler's fire, which gets `NHAmbient:Embers`.
- **Used with a prompt** (the locker system, as the stall and sink):
  - **Boiler:** "Furnace / Open". The firebox door swings out 100°, and the setup checks it opens outward.
  - **Valve wheel:** "Valve / Turn". The wheel turns 540° about its own axle and goes back after 4 s.
  - **Filing cabinet:** "Cabinet / Open". The top drawer slides out 1.1 studs.
  - **Gramophone:** "Gramophone / Play". The record spins while it plays, for up to 45 s.
- **Always on** (`Controllers.World.Ambient`, only within 60 studs, halved for Reduce Motion):
  - the banner cloths sway (`NHSwing`)
  - the boiler's flue and the pipe vent give off steam (`NHAmbient:Steam` spots)
  - the candles flicker
  - retrofitted on batches 4 and 5: the football machine's wheels spin (`NHSpin`), and the chandelier sways
- **New code:**
  - `Ambient` gains `NHSpin` (`SpinHinge`, `SpinAxis`, `SpinSpeed`, `SpinWhenOpen`) and an optional `SwingPhase` for `NHSwing`.
  - `LockerDoors` gains `SwingAxis` (turn about any axis), `SlideBy` (slide instead of turn) and `SwingTime`.
  - Patch: `Studio/patch_rig2.luau`.
- **Tiled pieces:** `nh_props.TILED` lists pieces that skip the baked atlas and get world-scaled UVs (8 studs a tile) with a seamless set instead: `CloisterArch_Wall` and `CloisterArchNoLamp_Wall` use `NH_CastleStone`.
  - The same stone is the texture-library set **CastleStone** (MaterialVariant `NHCastleStone`, Limestone, 8 studs a tile; see [[Textures]]). A builder can run it across a wall and blend it into the arch.
  - Made by `tools/vfx/make_castle_stone.py`.
- **Placement** on the baseplate for the builder (`workspace.NHPropsShowcase`, tags `NHPropBatch6` to `NHPropBatch9`):
  - batch 6 behind the first rows (z 84)
  - batches 7 and 8 in front (z 44, z 30)
  - the pillars to the west (x −232, z 70)
  - `Studio/props_revert6.luau` removes them.
- **Look:** on theme with the Institution: dark weathered castle stone, moss and ivy, brass, iron and crimson, candlelight, gothic carving. On the owner's notes the courtyard and pillars got a second, more detailed pass. Duplicates of existing models were skipped: the menu set's lamppost, bench, statue, urn, gargoyle and gate, the sports balls and cones.

**Batches 10 to 14 setup** (`Studio/props_setup10.luau`, run after importing their FBX files from `art/props/fbx/`):
- Same template steps as batches 6 to 9.
- **Used with a prompt** (the locker system):
  - **Headmaster's desk:** "Desk / Open". The right drawer slides out 0.9 studs.
  - **Safe** and **curiosity cabinet:** "Safe / Open", "Cabinet / Open". The doors swing out 100°; the cabinet's glass swings with its frame.
  - **Shop fronts:** "Door / Open". The shop doors swing out 95°.
  - **Town door:** "Door / Open". It swings 95° in, into the building.
  - The setup checks each door's direction and prints it.
- **Always on** (`Controllers.World.Ambient`): the awnings, the stall valance and the shop and hanging signs sway (the hanging sign wider), smoke rises from the chimney, embers come off the fireplace, and the candles and lanterns flicker. The desk lamp, the portrait light and the shop and window lights are steady.
- **Glass:** the coffee table's top is smoked (dark, 0.35 transparency); other glass is the usual pale glass.
- **The concession stand:** `Services.Features.Concession` builds the stand from `ServerStorage.NHProps.ConcessionStand` when it is there (patch `Studio/patch_concession.luau`).
  - It sits on the same spot as the plank stand, with its counter's front edge where the old counter's was. The prompt, the lunch queue and Mrs. Okada stay where they were.
  - The CONCESSIONS sign and the menu are drawn on the stand's own blank boards (template attributes `CounterFrontZ`, `SignFace`, `MenuFace`, set by the setup).
  - Without the template the plank stand is built as before.
- **Placement** on the baseplate for the builder: east of the gym (x 198 to 252), ten rows from z 120 north, 14 apart (`workspace.NHPropsShowcase`, tags `NHPropBatch10` to `NHPropBatch14`). The space south of the school is now the Commons. `Studio/props_revert10.luau` removes them.
- **Look:** on theme: dark sooty town stone with soot streaks and moss (darker than the castle stone, which read beige on these pieces), oxblood and crimson enamel, cast iron, brass and gilt, black lacquer and marble, warm gaslight. Wood is kept to crates and a barrel. The wall pieces have their backs flat for a builder's wall, on an 8-stud rhythm.

**Batches 15 to 17 setup** (`Studio/props_setup15.luau`, run after importing their FBX files from `art/props/fbx/`):
- Same template steps as batches 10 to 14. Steam rises over the serving counter's pans and from the coffee machine (`NHAmbient:Steam` spots); the heat lamps, the bakery lamp and the pendant lamp are steady, and the caddy's candle flickers. The pendant lamp's shade is crimson glass.
- **Placement** on the baseplate north of the gym for the builder (x 70 to 136, rows from z 228, 12 apart; tags `NHPropBatch15` to `NHPropBatch17`), clear of the gym, the Ink Studio and the Crimson Parlor. `Studio/props_revert15.luau` removes them.
- **The spire** is one baked piece, so the builder can scale it for bigger towers.

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
| BannerRavens, BannerRovers, BannerWardens | 10.7k (Cloth, Main) | batch 6: club banners: Night Ravens purple with a raven, Grave Rovers green with a grave cross and ball, Iron Wardens iron grey and rust with a shield; the cloth sways |
| BannerVigil, BannerCrimson | 9.5k (Cloth, Main) | batch 6: faction banners: The Vigil ink and gold with a candle, The Crimson Court crimson with a thorned rose; the cloth sways |
| ChessTable | 15.3k | batch 6: marble and iron, a full carved set in bone and ink |
| ArtEasel | 5.0k (Main, Glass) | batch 6: iron easel, a moonlit canvas in progress, palette and brushes |
| Gramophone | 7.4k (Main, Record) | batch 6: brass horn, crimson cabinet; "Gramophone / Play" spins the record |
| Telescope | 3.6k (Main, Glass) | batch 6: brass refractor on an iron tripod |
| FilingCabinet | 8.8k (Main, Drawer0) | batch 6: cast iron with brass label frames; "Cabinet / Open" slides the top drawer out |
| Typewriter | 13.6k | batch 6: black enamel and brass, a typed sheet |
| TeaTrolley | 14.9k | batch 6: iron and brass, teapot, cups, cake stand |
| Pigeonholes | 12.8k | batch 6: staff mail cubbies with letters and parcels |
| BallRack | 14.6k | batch 7: basketballs, soccer balls and footballs on an iron rack |
| Hurdle | 2.0k | batch 7: iron frame, crimson enamel bar |
| TackleDummy | 6.4k | batch 7: padded leather dummy on an iron sled |
| GymMatStack | 6.8k | batch 7: crimson and ink leather mats |
| WaterKeg | 7.4k | batch 7: iron-banded keg with a brass tap and tin cups |
| Scoreboard | 7.1k | batch 7: gothic wall scoreboard with club lamps; to replace the greybox scoreboards at the pitch |
| Boiler | 12.7k (Main, Glow, Door0) | batch 7: riveted boiler; "Furnace / Open" swings the firebox door out on the fire; steam from the flue, embers from the fire |
| PipeRun | 6.6k | batch 7: wall pipes with valves and a gauge; steam from the vent |
| ValveWheel | 3.4k (Main, Wheel) | batch 7: "Valve / Turn" turns the hand wheel one and a half turns |
| CoalPile | 4.1k | batch 7: coal heap with a shovel |
| CoalCart | 7.9k | batch 7: iron coal cart, full |
| Workbench | 7.9k | batch 7: iron bench, vice, tools |
| Fountain | 15.0k (Main, Pool) | batch 8: octagonal gothic fountain, grotesque spouts, a brass raven; the water (Pool) always shows |
| CloisterArch | 15.8k (Main, Wall, Glass, Glow) | batch 8: a cloister bay with a hanging lantern; its wall face (Wall) carries the seamless NHCastleStone |
| CloisterArchNoLamp | 14.7k (Main, Wall) | batch 8: the same arch without the lantern |
| StonePlanter | 15.1k | batch 8: buttressed bed with crimson roses, ferns and ivy |
| Topiary | 14.1k | batch 8: clipped yew in a carved tub |
| Sundial | 5.0k | batch 8: clustered pedestal, brass dial, a crow |
| Well | 12.3k (Main, Glass, Glow) | batch 8: wellhead under an iron canopy and slate roof, lantern |
| Balustrade | 10.0k (Main, Glass, Glow) | batch 8: pierced gothic parapet, tiles every 8 studs, a lantern |
| Memorial | 11.6k (Main, Glow) | batch 8: the founders' memorial spire, votives, iron railing |
| PillarCluster | 14.6k | batch 9: clustered pier, stiff-leaf capital, grotesques |
| PillarOctagon | 15.3k (Main, Glow) | batch 9: octagonal pier, blind tracery, stone ravens, a candle bracket |
| PillarTwisted | 15.8k | batch 9: twisted wine-marble column on crouching grotesques |
| PillarFanVault | 14.9k | batch 9: column springing a fan vault with carved bosses |
| PillarNiche | 7.5k (Main, Glow) | batch 9: square pier with a canopied candle niche |
| PillarMarble | 11.4k | batch 9: black marble with gilt bands and capital |
| PillarIron | 9.6k | batch 9: cast-iron column with traceried brackets |
| Pilaster | 3.6k (Main, Glow) | batch 9: wall pilaster with a blind arch, a crest and a lantern |
| HeadmasterDesk | 16.0k (Main, Drawer0) | batch 10: black lacquer pedestal desk, gilt mouldings, crimson leather top, inkstand, blotter, files, bell; "Desk / Open" slides the right drawer out |
| HeadmasterChair | 11.1k | batch 10: throne-like wingback in tufted crimson leather on a black and gilt frame, carved crest |
| Fireplace | 17.6k (Main, Glow) | batch 10: a wall piece in dark sooty stone, carved gothic overmantel with the crest, iron fire dogs, logs and coals; embers from the fire |
| FounderPortrait | 5.2k (Main, Glow) | batch 10: a wall piece: the founder in oils, side-lit on a dark ground, heavy gilt gothic frame, a brass picture light |
| Safe | 10.0k (Main, Door0) | batch 10: cast iron, brass dial and handle, gilt pinstripes, on castors; "Safe / Open" swings the door out |
| CuriosityCabinet | 12.3k (Main, Door0, Glass) | batch 10: black glass-fronted cabinet of confiscated things (slingshot, skull, potions, a cursed doll, a dagger, cards); "Cabinet / Open" swings the glazed door out |
| OfficeRug | 1.0k | batch 10: 12 x 8 crimson and ink gothic rug with a fringe |
| DeskLamp | 3.8k (Main, Glow) | batch 10: brass, crimson cased-glass shade with gilt ribs; a steady glow |
| FounderBust | 6.2k | batch 10: marble bust of the founder on a black marble plinth with a gilt band |
| SchoolCrest | 8.5k | batch 10: a wall piece: the Institution's shield (raven, moon, key, candle), crossed swords, a parchment scroll |
| DecanterTray | 5.0k (Main, Glass) | batch 10: silver tray, crystal decanters and glasses |
| Hourglass | 5.6k (Main, Glass) | batch 10: brass and black, red sand |
| ShopApothecary | 29.5k (Main, Upper, Display, Glow, Glass, Door0, Cloth) | batch 11: a 12 x 12 shop front (wall piece) in sooty stone and oxblood iron, a lit bay of coloured bottles, a hanging sign that sways; "Door / Open" swings the shop door out |
| ShopCurio | 29.3k (Main, Upper, Display, Glow, Glass, Door0, Cloth) | batch 11: a second shop front in green: an arched window of clocks, masks, candles and a caged raven, gilt balls that sway; "Door / Open" |
| MarketStall | 28.4k (Main, Goods, Stand, Glass, Glow, Cloth) | batch 11: iron-framed stall, crimson and black awning (the valance sways), apples, pumpkins, jars, a lantern |
| HangingSign | 2.9k (Main, Cloth) | batch 11: a wall bracket with an oxblood sign (crescent moon and mortar) that swings |
| Postbox | 5.2k | batch 11: crimson cast-iron pillar box, gothic cap, a crest |
| StreetPump | 4.3k (Main, Pool) | batch 11: cast-iron parish pump over a stone trough of water |
| NewsKiosk | 8.1k (Main, Glass, Glow) | batch 11: octagonal iron kiosk, posters, a domed roof and a lamp |
| TelephoneBooth | 19.7k (Main, Roof, Glass, Glow) | batch 11: gothic cast-iron booth: lancet windows with tracery, an ogee dome with cresting, a lit lantern, a brass telephone inside |
| Bollards | 10.0k | batch 11: three iron bollards with a sagging chain, 8 long |
| IronRailing | 5.7k | batch 11: an 8-stud wrought-iron railing with spear finials on a stone plinth; tiles end to end |
| Signpost | 6.4k | batch 11: fluted iron fingerpost with three symbol boards (school, church, crossroads) and a crow |
| CratePile | 15.2k | batch 11: market crates, sacks, a hooped barrel and a tarpaulin |
| TownDoor | 10.4k (Main, Glass, Door0, Glow) | batch 12: a wall piece: stone arch with a fanlight, a studded oxblood door, a lantern, a step; "Door / Open" swings it in (needs a 4 x 7.6 opening behind) |
| TownWindow | 14.4k (Main, Glass, Glow) | batch 12: a wall piece: sash window in a stone surround, a warm lit room behind with curtains, oxblood iron shutters |
| BayWindow | 12.2k (Main, Glass, Glow) | batch 12: a wall piece: an oriel bay on carved corbels, lead roof, leaded lights, a lit room |
| Chimney | 6.6k | batch 12: brick and stone stack with clay pots; smoke from the middle pot |
| IronBalcony | 14.1k | batch 12: a wall piece: stone slab on scrolled brackets, wrought-iron railing, 8 wide |
| ShopAwning | 11.2k (Main, Cloth) | batch 12: a wall piece: iron-framed crimson and black awning, 8 wide; the valance sways |
| Dormer | 8.7k (Main, Glass, Glow) | batch 12: slate dormer with a gabled stone front and a dim lit window; sits on a 45° roof |
| Drainpipe | 5.1k | batch 12: a wall piece: 12-stud cast-iron downpipe with a hopper head, brackets and a shoe |
| StoneStoop | 5.6k | batch 12: four worn stone steps with iron handrails and a boot scraper |
| TableRound | 13.3k | batch 13: 4 across, black marble with fine veins and a gilt edge on a carved iron claw-foot pedestal (top 3.0) |
| TableOval | 12.4k | batch 13: 8 x 4.5 black lacquer, gilt stringing, a crimson velvet runner, twin pedestals (top 3.0) |
| TableBanquet | 15.0k (Main, Glow) | batch 13: 16 x 3.5 feast table: a thick stone slab on gothic iron trestles, a crimson runner, two candlesticks (top 3.0) |
| TableCafe | 5.3k | batch 13: 2.5 square bistro table, marble top on a cast-iron base (top 2.7) |
| TableHexagon | 10.1k | batch 13: hexagonal library table with a crimson leather inset, a brass edge, six legs and a stretcher (top 3.0) |
| TableDemilune | 11.6k | batch 13: a wall piece: half-moon console, marble top, gilt carved apron, black lacquer cabriole legs (top 3.0) |
| TableCoffee | 8.4k (Main, Glass) | batch 13: low table, smoked glass top on a brass and iron frame, books below (top 1.5) |
| TableSide | 6.0k | batch 13: small tripod side table, marble top with a gallery rail (top 2.5) |
| ConcessionStand | 61.8k (Main, Shelves, Roof, Sign, Cloth, Goods, Glass, Glow) | batch 14: Mrs. Okada's stand remodelled: cast iron and oxblood under a slate roof with cresting and a crow, a crimson and black awning that sways, lanterns, a black marble counter of sweet jars, pastries and potion sodas, snack shelves, blank boards for the sign and menu text |
| ServingCounter | 19.0k (Main, Food, Glass, Glow) | batch 15: 10-stud steam-table counter: black marble top, oxblood gothic panels, brass tray rail, a glass sneeze guard, pans of mash, peas, stew, sausages and something green, heat lamps; steam over the pans |
| TrayRack | 9.5k | batch 15: tall iron trolley rack full of pewter trays and a few dirty plates |
| DrinksDispenser | 7.4k (Main, Glass) | batch 15: counter piece: crimson and amber juice in glass jugs with brass taps, a brass tea urn, cups on a drip tray |
| BakeryCase | 14.4k (Main, Glass, Glow) | batch 15: glass pastry case on a black lacquer base with gilt mouldings and crimson pointed-arch door panels, gilt cresting; pastries, tarts, iced buns and a dark cake |
| CoffeeMachine | 8.3k | batch 15: counter piece: brass and oxblood steam coffee machine with gauges and levers, cups on top; steam from the dome |
| KitchenShelf | 8.9k | batch 15: a wall piece: iron shelf with copper pots and pans, ladles, jars of preserves and sacks |
| DishStack | 11.3k | batch 15: counter piece: stacks of plates and bowls, a cutlery bin and a cup tree |
| CafeteriaTable | 16.0k | batch 16: 10-stud dining table with both benches: black lacquer top with a brass edge and carved initials, gothic iron trestles, crimson leather pads (top 3.0, seats 1.8) |
| CafeChair | 6.7k | batch 16: ornate cast-iron chair with a crimson cushion (seat 1.9) |
| CafeBooth | 16.8k (Main, Table) | batch 16: gothic high-backed booth: two crimson tufted benches with carved pointed-arch backs and a black marble table (seats 1.75, table 2.9) |
| ChalkMenuStand | 6.6k | batch 16: iron A-frame chalkboard with a crest, chalk scribbles and doodles (a cup, a cake, a skull) |
| CondimentCaddy | 3.4k (Main, Glow) | batch 16: table piece: brass caddy with salt and pepper, a sauce bottle, mustard, napkins and a little candle |
| CakeStand | 9.1k (Main, Glass) | batch 16: table piece: three-tier silver stand with black-iced cakes, raspberries and a glass dome |
| PendantLamp | 8.3k (Main, Glow, Glass) | batch 16: hanging iron lamp on a chain with a crimson glass shade (4 tall; hang its top from a ceiling) |
| Spire | 4.9k | batch 17: the memorial's crocketed octagonal spire as a building piece, 12 tall and 3 across, for towers and big roofs; scale it in Studio |
| SpireCross | 5.4k | batch 17: the same spire with the memorial's iron cross and ring on top |
| SkateboardMoonlit, SkateboardBone, SkateboardRavens, SkateboardRovers, SkateboardWardens, SkateboardGargoyle, SkateboardVigil, SkateboardCrimson, SkateboardHeadmaster | 7.8k each (Main, TruckF, TruckB, WheelFL, WheelFR, WheelBL, WheelBR) | batch 18: the nine rideable skateboards; see [[Skateboards]] |

**Placed on the map** (`Studio/props_map.luau`; `Studio/props_map_revert.luau` removes them). 91 copies of the batch 4 to 9 templates, in `workspace.NHPropsMap/<Area>`, tagged `NHPropMap`, named `<Prop>_<Area>_<n>`, with a `MapArea` attribute. Each row of the script gives a prop, an area, x and z, and the way its front faces. Rays find the floor or table top under it, or the wall behind it for wall pieces.

| Area | Copies | Props |
|---|---|---|
| Hall | 24 | PillarMarble ×2 at the west entrance; PillarNiche ×4 along the open south edge; Pilaster ×7 framing the gaps between classrooms; GothicMirror over the west bench; PictureFrame ×3; BannerCrimson and BannerVigil; CeramicVase ×2; PottedPlant ×3 |
| Forecourt | 4 | PillarTwisted ×2 and PillarOctagon ×2: an avenue from spawn to the hall's west end |
| Staff Room | 11 | LunchTray, LunchTrayEmpty, CandleCluster and FlowerVase on the staff table; WallClock over the door; CoatRack, UmbrellaStand, Pigeonholes, TeaTrolley, Gramophone, PictureFrame |
| Archive | 5 | Typewriter, BookStack and OilLamp on the study table; Telescope; BannerVigil outside, on the archive's hall wall by the door |
| Records Office | 4 | FilingCabinet ×2 by the door, OilLamp on the tall cabinet, WallClock |
| Boiler Yard | 8 | Boiler, PipeRun on the west fence, ValveWheel and Workbench on the east fence, CoalPile, CoalCart, PillarIron ×2 at the open north side |
| Quad (between the classrooms and the gym) | 19 | CloisterArchNoLamp ×2 and CloisterArch: an arcade at the quad's west entrance; Fountain on the gym door; Topiary ×2 flanking the door; StonePlanter ×5 against the classroom backs; PillarFanVault, Sundial, Memorial, ArtEasel, ChessTable, Well, Balustrade ×2 |
| Gym | 8 | BannerRavens, BannerRovers and BannerWardens on the entrance wall between the windows; Chandelier ×2 from the roof (no collision); BallRack, GymMatStack, WaterKeg |
| Pitch | 2 | Bleachers ×2 behind the north wall, facing the pitch |
| Football practice | 6 | Hurdle ×3, TackleDummy ×2 and WaterKeg on the north sideline |

- **Kept clear:**
  - **Rite props:** copies stay 1.5 studs from `School.NHRiteProps`. The Archive is a rite room (altar and bookshelves), so it gets only table props and the telescope. In the Boiler Yard the copies sit away from the anvil, ash heap and crate stack, and the boiler's door doesn't swing toward the anvil.
  - **Other no-go spots:** the `MarkWall`s (there is no pilaster at the R105/R106 gap, and the planter behind R103 moved along), the `NHPropSpot_*` placeholders (the Staff Room's south end is kept for the sofa and armchairs), the watcher's patrol round the staff table, and the room exits.
  - **Sports play zones:** the gym's `Court.Bounds` and `Practice.DrillBounds`, and the drill's `TargetBounds` and `RouteBounds`, which cover the whole practice turf.
  - **The classroom gaps:** the 3-stud gaps between classrooms stay open. They are an alley from the hall to the quad.
- **Left out:**
  - **The washroom set** (BathroomMirror, Sink, ToiletStall, TowelRail): the school has no washroom yet.
  - **FootballMachine and Scoreboard:** these went in as swaps for Sports greybox pieces in 1.18.3 (below), except the gym's scoreboard.
- **Checks in the script:** each copy reports any visible part it digs into (pieces shrunk 0.25 so resting contact passes) and any rite prop within 1.5 studs.

**Swapped for the Sports greybox** (`Studio/props_swap.luau`; `Studio/props_swap_revert.luau` shows the greybox again). The Sports code and the greybox parts' positions are unchanged. The greybox parts are hidden (Transparency 1, the old value kept in `NHSwapHidden`) and keep their collision. The copies (tags `NHPropMap` and `NHPropSwap`) have no collision, touch or queries.

- **The drill's throwing machine:**
  - `Football` throws from 1.5 studs above the part with `SportDrillMachine` and rests the ball 2 studs above it, so that part stays where it is.
  - `FootballMachine_Practice_1` stands over it on the turf, facing the routes (−X). Its top is 0.13 below the throw point.
  - The greybox machine, its stand and its two wheels are hidden.
- **The pitch and field scoreboards:**
  - `Matches` writes into the SurfaceGui `Board` on the part with `SportScoreboard`, so that live panel stays.
  - `Scoreboard_Pitch_1` and `Scoreboard_Field_1` are the gothic board scaled 3.29× (24.7 × 19.7) to frame it. The board's face recess (5.6 × 3.1 studs at the prop's own size) sits 0.05 behind the panel, which covers the board's painted digits. The club lamps show above the panel and the crest and finials top it off.
  - The wooden greybox frames are hidden, and the board legs stay as its posts.
- **Not the gym's board:** at that size the crest would go through the gym roof, so the gym keeps its greybox board.

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
- **Imported and placed (1.15.1):** all 20 in `workspace.NHPropsShowcase` with no clashes and no imports left in the workspace. The stall door's sign came out −95° on the real geometry, and the check confirms it opens out.
- **Tested in Play (solo):**
  - **Prompts:** the stall reads "Stall / Open" and turns to "Close" when open; the sink reads "Sink / Turn on".
  - **Opening:** the stall door swung −95° with its centre 0.9 studs in front of the stall, the taps turned −90° / +90°, and the water showed at 0.35.
  - **Closing:** everything went back to 0° and the water hid.
  - **Textures:** all 25 SurfaceAppearances loaded in Play. In the Edit view a few show plain white until Studio finishes fetching them.
- **Not verified yet:** the prompts triggered by a player and the auto-close timers (Open was set directly), the props seen by a second player. Nothing spins the football machine's wheels yet.

**Batches 6 to 9 (2026-11-03):**
- **Baked:** all 42 at 2048 with 64 samples on the GPU, and every piece is under 16k triangles. Maps uploaded, ids in `props.json`. The castle stone was uploaded at 2048 (the arch walls) and at 1024 (the library set).
- **Code, in Play:** `NHSpin` turned a test part 91° in 0.5 s at 180°/s, with no script errors from the patched `Ambient` or `LockerDoors`.
- **Dry run (Edit):** boxes of each prop's real size: 42 placed in four rows, no clashes; removed afterwards.
- **Imported and placed (1.18.1):**
  - all 42 with no clashes and no imports left in the workspace
  - the furnace door opens out (−100° on the real geometry)
  - the football machine's wheels and the chandelier were retrofitted
- **Tested in Play (solo):**
  - **Prompts:** all four read correctly.
  - **Opened:** the furnace door swung out −100°, the valve wheel turned 540°, the drawer slid out, and the record spun at 200°/s.
  - **Closed:** everything went back to rest.
  - **Always on:** the football wheels spin and a banner sways about ±1.6°, both within 60 studs of the camera.
  - **Textures:** every batch 6–9 map loaded on the client, including five that showed a failed fetch in Edit (Studio's caching quirk).
- **Not verified yet:** a player pressing the prompts and the auto-close timers, the steam and ember emitters up close, and a second player's view.

**Placed on the map (2026-11-03, 1.18.2):**
- **Edit:**
  - 91 copies with no clashes and none within 1.5 studs of a rite prop.
  - A box check against every invisible zone left only the whole-room zones and the gym chandeliers, which hang inside `Court.Bounds` and don't collide.
  - Screenshots of every area.
- **Play (solo):**
  - **Prompts:** all 91 copies reached the client, and the five rigged ones were ready with their prompts on the server: "Furnace / Open", "Valve / Turn", "Cabinet / Open" ×2, "Gramophone / Play".
  - **Opened** (Open set from the server):
    - the furnace door turned −100° and moved toward the front (out)
    - the valve wheel turned 540°
    - both drawers slid 1.1 studs out
    - the record spun
  - **Closed:** all went back to rest and the record stopped.
  - **Always on:**
    - the hall's Crimson banner swayed through 3.2°
    - a gym chandelier swayed 1.6°
    - the boiler's embers and a steam vent ran
    - the second vent waits behind the three-nearest-emitters cap, as designed; emitters are off while a player is in the main menu
  - No script errors.
- **Not verified yet:**
  - a player walking the map
  - a player pressing the prompts, and the auto-close timers
  - a second player's view
  - performance with all the copies' lights on a low-end device

**Greybox swaps (2026-11-03, 1.18.3):**
- **Edit:**
  - The three copies are placed; the only overlap is the board legs, which run behind the boards as designed.
  - 91 of 91 rays from the front reach each live panel.
  - Screenshots of both boards and the machine.
- **Play (solo):**
  - **Drill:** "Start Route Runner" started the drill, and the drill ball rested on the new machine, 0.6 above its top.
  - **Machine:** its wheels spin.
  - **Boards:** both panels showed the live status "Stand on a pad to play (0 v 0)" in their gothic frames.
  - No script errors.
- **Not verified yet:**
  - a throw seen leaving the machine: the test runner tripped the drill's own teleport and bounds checks before a route was called
  - a full match on the pitch or field with the score changing

**Batches 10 to 14 (2026-11-04):**
- **Baked:** all 42 at 2048 with 64 samples on the GPU, and every piece is under 16k triangles. Maps uploaded, ids in `props.json`. Sheet `art/props/_batch10_14_final_sheet.png`.
- **Dry run in Studio:** with stand-in boxes, `props_setup10` made all 42 templates, set the concession stand's attributes and placed all 42 rows east of the gym with no clashes. `props_revert10` (MOCKS) cleared it. The door-direction checks need the real models (the stand-ins have no hinge).
- **Concession code:** `patch_concession.luau` applied (8 edits) and the module compiles. With no template yet, the plank stand is still built.
- **Imported and set up (2026-11-04):** the owner imported the 42 FBX files; `props_setup10` made the templates and placed them east of the gym with no clashes, and every door opens the right way on its real hinge (the safe, cabinet and shop doors out, the town door in). Two stray re-imports (Pilaster, Workbench) were deleted. The maps show in Studio.
- **The concession stand in Play:** the stand is the new model, the plank greybox is gone, Mrs. Okada, the prompt and the lunch spots are there, and the CONCESSIONS sign is drawn on the stand's own board. The sign and menu boards' real faces sat 0.2 and 0.48 studs in front of the reported spots (the text would have been hidden inside them), so the setup now measures the boards and the counter with rays; the live template is fixed.
- **Not verified yet:** the textures seen on a client in Play (two Play checks were stopped from outside), the doors and sways in Play, buying from the new stand, and the lunch queue at it.

**Map copies restored (2026-11-04):** eight quad copies had gone missing (cause unknown: the cliques hangouts did not remove them): the Memorial, the Well, the three cloister arches, the ArtEasel, the ChessTable and the PillarFanVault. Re-running `Studio/props_map.luau` (it only adds what is missing) put them back at their spots, with no clashes.

**Batches 15 to 17 (2026-11-04):**
- **Baked:** all 16 at 2048 with 64 samples on the GPU, every piece under 16k triangles. Maps uploaded, ids in `props.json`. Sheet `art/props/_batch15_17_final_sheet.png`.
- **Dry run in Studio:** with stand-in boxes, `props_setup15` made all 16 templates and placed the three rows north of the gym with no clashes.
- **Imported and set up (2026-11-04):** the owner imported the 16 FBX files; `props_setup15` made the templates and placed the three rows north of the gym with no clashes and no stray imports. The maps load in Studio (a few fill in a little later in the Edit view).
- **Not verified yet:** the steam and lights in Play.

