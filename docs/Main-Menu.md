# Main Menu and Save Slots: NH Combat Test

**Status:** built and playtested in Studio (single player). The flow is: join → cinematic intro → main menu → slot picker → edit your student → enter school.

The inspiration was two references: a minimal RPG menu with save slots, and a posed hero with VFX. Everything here is an original Nightmare Highschool design.

## What you see

1. **Intro fly-in, about 12 s.** You can skip it with any key or a click.
   - The camera starts high above the academy at night.
   - It sweeps past the clock tower, whose hands show the real school time.
   - It looks out through the iron gate (gargoyles on the pillars, blurred bars in the foreground).
   - It swings around the courtyard and lands on your student.
2. **Hero shot.** Your student floats in an "ascension" pose inside a crimson **clock seal**.
   - Twelve glowing hour ticks are set into a black rune-stone disc, with the hands stopped near midnight.
   - Behind them stands a ring of carved stone with energy tearing out of it: crimson plasma tendrils, lit crystal shards and sparks, embers off the seal, crimson smoke and a pulsing core glow.
   - Both hands smoulder with a crimson aura.
   - The student wears the look from your most recent slot.
3. **Main menu** (title top-left, letterbox bars, vignette):
   - **CONTINUE:** your last slot, straight into school.
   - **PLAY:** the slot picker.
   - **SETTINGS:** the UI kit's settings panel.
   - **CREDITS:** a camera move up to the tower, plus a credits panel.

   The highlighted item gets a thin gold plate with diamond knobs and a crimson glow. Use W/S or the arrows, Enter to select, mouse hover and click, or a gamepad.
4. **Slot picker.** The camera moves to three stone plinths in front of the school steps. Each slot's student stands on a plinth under its own spotlight; empty slots show a shimmering crimson ghost.
   - Each card shows your name, race (or "not yet revealed"), title, faction rank, Yen, quests done, takedowns and when you last played.
   - The hovered card lifts, its spotlight brightens and its student turns toward you.
   - Use A/D or the arrows, Enter to play, and Backspace to go back.
5. **Edit your student.** Your real character appears inside the seal, and the Wardrobe (UI session) docks on the right in stage mode.
   - **The camera cuts per tab:** Look and Outfit get the full body, Face a close-up, Hair a high three-quarter view, and Lineage a low heroic angle.
   - **Drag to orbit** around your student. The ring VFX calm down while you edit.
6. **ENTER SCHOOL:** the camera pushes toward the school doors, fades through "The bell is ringing...", and you spawn at the school. The HUD, lighting, camera and controls are all handed back.

**Ambient life:**
- lamps flicker and dust drifts in their light
- windows go dark now and then
- chimneys smoke and ground fog rolls in
- bats circle the tower and lightning flashes
- moss, ribbons, a kite tail and sneakers sway in the wind
- the night grade uses bloom, depth of field that follows the subject, and colour correction

## Camera

- **Paths:** each move is one **Catmull-Rom spline** through all its shots, with a single smootherstep ease over the whole path, so a multi-shot fly-through never stops between shots.
- **Follow:** a critically damped follow on top means a new move always continues from where the camera is.
- **Feel:** slow two-octave handheld drift and damped mouse parallax (reduced while editing).

## Save slots (server: `Services.Player.Slots`, `Services.Player.Data`)

- **Each slot is its own save:** its own race roll, quests, factions, Yen and record. Slot 1 is the save that existed before slots (key `{UserId}'s Data`); slots 2 and 3 are `{UserId}'s Data|Slot2` / `|Slot3`. Nothing was lost.
- **Loading:** the profile loads (and is session-locked) only when you pick a slot. The slot picker uses read-only views, so it never locks a save.
- **Spawning:** `Players.CharacterAutoLoads` is off. Slots spawns your character on the editing stage, then at the school when you enter. It also respawns you after death (after `Players.RespawnTime`).
- **No combat in the menu:** `ActionManager` refuses every action while `InMainMenu` is true.
- **Menu avatar:** your Roblox avatar is built once on the server as an R6 model (`ReplicatedStorage.NHMenuAvatars.<UserId>`). The client copies it and dresses each copy with that slot's saved look (`UI.Appearance.ApplyTo`).
- **Remotes:** `ReplicatedStorage.NHSlots.{List, Choose, Enter}` RemoteFunctions, rate-limited and validated on the server.
- **Turning it off:** set `Config.MainMenu.Enabled = false`. You then auto-load slot 1 as before (also restore `Players.CharacterAutoLoads` to true).

## Scene (`workspace.MenuScene`, a persistent streaming model 1500 studs above the school)

**PBR materials** (MaterialVariants generated for this scene, each with colour, normal and roughness maps):

| Variant | Used for |
|---|---|
| `NH_WetCobble` | wet courtyard cobblestone |
| `NH_OldBrick` | Victorian school brick |
| `NH_GothicStone` | gothic stone |
| `NH_WroughtIron` | wrought iron |
| `NH_SlateRoof` | slate roof |
| `NH_OakDoor` | oak |
| `NH_DeadGrass` | dead grass with leaves |
| `NH_RuneStone` | rune stone |
| `NH_DeadBark` | dead oak bark |

**Built pieces:**

| Area | What's there |
|---|---|
| School front | windows with mullions, sills and keystones; buttresses; quoins; dormers; chimneys; downpipes and gutter; wall lanterns; step railings; faction banners |
| Clock tower | working clock hands, belfry with a bell, battlements, pinnacles, lancet windows |
| Wings and distance | side wings; distant chapel, town roofline, forest and hills |
| Courtyard | gate with "NIGHTMARE HIGHSCHOOL" arch and fence, curbs, hedges, bollards, puddles, drain, small graveyard |
| Trees | six procedural dead oaks (about 4,800 pieces): bent, tapered limbs with root flare, side branches, snapped stubs, twig fans and hanging grey moss |
| Tree details | sneakers thrown over a branch, Crimson Court ribbons, a snagged kite, a broken birdhouse |

**AI-generated meshes** (Studio mesh generation):

- gargoyles
- Victorian street lamps
- a bronze founder's statue
- benches
- stone urns
- a bike rack with a bicycle
- a notice board with posters
- leaf and paper litter
- crows
- ivy

**Map contract** (attributes, so the builder can replace any of it):

| Attribute | Meaning |
|---|---|
| `MenuShot = <name>` | camera keyframes |
| `MenuStage = Hero / Creator / Slot1..3` | where students stand |
| `VfxCore` | ring centre |
| `RuneGlow` | pulsing parts |
| `ClockFace` / `ClockHand = Hour\|Minute` | the tower clock |
| `Window` + `Lit` | flickering windows |
| `Flicker` | lamps |
| `Smoke` | chimneys |
| `Sway` | wind |
| `SlotLight = n` | slot spotlights |

## VFX textures (rendered in Blender Cycles, physically based)

`tools/vfx/render_vfx.py` renders white sprites with alpha that Roblox tints:
- **volumetric smoke:** Principled Volume with 4D noise, lit by a warm key and a cool rim; 16 frames in a 4×4 flipbook
- **tileable plasma wisp** for the tendril beams: noise in cylindrical coordinates, so it scrolls seamlessly
- **ember** with a four-point star
- **lit crystal shards:** faceted Principled BSDF with coat, 4 variants in a 2×2 flipbook, drawn along their direction of travel
- **soft volumetric mist sheet**

The asset ids are in `Config.MainMenu.Textures`. Re-run with:

```bash
"E:/Blender/blender.exe" --background --factory-startup --python tools/vfx/render_vfx.py -- <outdir> [smoke wisp ember shards fog]
```

(Use a short output path: Blender can't open files past Windows' 260-character limit.)

## Files

| Where | What |
|---|---|
| `ReplicatedStorage.Config.MainMenu` | on/off, slot count, title, camera paths, credits, VFX texture ids |
| `ServerScriptService.Services.Player.Slots` | slot list, choose, enter, spawn/respawn, menu avatar |
| `ServerScriptService.Services.Player.Data` | `LoadSlot`, `ViewSlot`, `SlotKey`, `GetSlot` (profile loads per slot) |
| `StarterPlayerScripts.Controllers.Gui.MainMenu` | camera, lighting grade, students, VFX, UI, flow |
| `workspace.MenuScene` | the scene |
| `ServerStorage.MenuProps` | the generated props (templates) |
| `tools/vfx/` | the Blender render script and the rendered sprites |

## Verified (Studio playtests, single player)

**Flow:**
- Intro → menu, with real Space/S/Enter presses.
- PLAY with a real click → slot cards with real save data.
- Enter on slot I → editing: the real character on the stage, Wardrobe docked, and the Face tab cutting the camera to a close-up.
- ENTER SCHOOL with a real click → spawned at the school with the HUD, Custom camera and daytime lighting restored.
- CONTINUE also goes straight into school.

**Screenshots checked:** the gate shot through the bars, the hero shot, the slot screen, editing, entering and after entering.

**Bugs found and fixed:**
- students faced away from the camera
- slot order was mirrored against the cards
- the HUD re-enabled itself when the character spawned
- the intro flew through the ring and the student
- the Wardrobe button showed on the main menu
- the slot list loading late reset your selection
- glaring windows behind the slots
- the camera stopped between shots: replaced by the spline and damped follow

**Not tested:**
- Two players. Each player has their own menu, but two people choosing slots at once was not tried.
- Phones and touch: drag-to-orbit uses touch input, but no device test was done.
- The newest camera and texture changes were made after the last full playtest.
- Live servers: slot views use ProfileService `ViewProfileAsync`, and Studio uses the Studio data store.

**Leftover test data:** slot 1 of the Studio test profile was used.
