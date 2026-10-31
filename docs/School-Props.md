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

Door and flap origins sit on their hinge lines.

| Prop | Triangles | Replaces / goes to |
|---|---|---|
| StudentDesk | 4.8k | `Desk` ×48 (R101–R106) |
| TeacherDesk | 4.7k | `TeacherDesk` ×6 |
| Chalkboard | 6.1k | new, on the wall behind each teacher desk (a `ChalkboardSpot` part) |
| Locker | 10.1k (2 pieces) | the 8 hallway lockers, including Locker113, which carries the quest note |
| HidingLocker | 15.2k (3 pieces) | the Records Office and Staff Room hiding lockers |
| StudentChair, TeacherChair, Armchair, Sofa, TrashCan, Candelabra, VendingMachine, Altar, Bookshelf | 0.3k–26k | batch 2: modelled, waiting to be imported |

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

**Not verified yet:**
- the new batch-1 textures with weathering
- two-player locker sync
- batch 2, which is not imported yet
