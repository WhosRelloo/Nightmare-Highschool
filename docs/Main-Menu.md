# Main Menu and Save Slots: NH Combat Test

**Status:** built and playtested in Studio (single player). The flow is: join → **loading screen** → cinematic intro → main menu → slot picker → edit your student (Look / Name & Clan / Spin Shop) → enter school, where a slim custom **top bar** replaces Roblox's.

The inspiration was two references: a minimal RPG menu with save slots, and a posed hero with VFX. Everything here is an original Nightmare Highschool design.

## What you see

0. **Loading screen** (`ReplicatedFirst.NHLoadingScreen`, the first thing that runs). It's styled as your **admission file** being processed.
   - **Title card:** a blackletter title, "STUDENT FILE No. ####" and "OFFICE OF ADMISSIONS · NIGHT TERM" typed in typewriter type, and the time it was "FILED".
   - **Live background:** behind it is **the real game**. Once the menu is ready, the black backdrop opens onto the courtyard, filmed by a slow 70-second camera glide (`PreRollA` → `PreRollB`), so players watch the academy appear while they wait.
   - **Asset counter:** every content id the client can see (images, meshes, sounds, animations, particle and beam textures, PBR maps, clothing) is collected, de-duplicated and preloaded through the instance that uses it. The bottom of the letterbox shows "RECORDS RECEIVED 0214 / 0406 52% ~6s left", with a hairline crimson progress rule along its top edge. The time left is worked out from the measured load rate.
   - **Details:** typed notes (tips), drifting embers and film grain.
   - **Finish:** a crimson **ADMITTED** rubber stamp slams onto the title, the screen goes black, and the intro starts. A "[ continue ]" button appears after 12 s, and loading carries on in the background.
   - **Hand-off:** sets `LocalPlayer` attribute `NHLoaded`. The menu sets `NHMenuReady` when its camera is in place, and `NHLoadHold = true` holds the stamp for screenshots.
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
5. **Edit your student.** Your real character appears inside the seal, with your full name as the header. A switch on the left picks the panel docked on the right:
   - **Look:** the Wardrobe (UI session), in stage mode.
   - **Name & Clan:** sign the register and spin your clan.
   - **Spin Shop:** Robux spins.

   See [Names-Clans-and-Spin-Shop.md](Names-Clans-and-Spin-Shop.md). A new student starts on Name & Clan and watches the clan reel land first.
   - **The camera cuts per tab:** Look and Outfit get the full body, Face a close-up, Hair a high three-quarter view, Lineage and Name & Clan a low heroic angle, and the Spin Shop the full body.
   - **Rare clans:** an Epic-or-better roll flares the ring in the clan's colour and leans the camera in.
   - **Drag to orbit** around your student. The ring VFX calm down while you edit.
6. **ENTER SCHOOL** (needs a first name: you're sent to the register if you haven't signed): the camera pushes toward the school doors, fades through "The bell is ringing...", and you spawn at the school. The HUD, lighting, camera and controls are all handed back.

**Ambient life:**
- lamps flicker and dust drifts in their light
- windows go dark now and then
- chimneys smoke and ground fog rolls in
- bats circle the tower and lightning flashes
- moss, ribbons, a kite tail and sneakers sway in the wind
- the night grade uses bloom, depth of field that follows the subject, and colour correction

7. **Top bar** (`Controllers.Gui.TopBar`, in school). Roblox's top bar is switched off (`SetCore("TopbarEnabled", false)`). In its place is one small ink-black plate with a gold rim and a faint crimson underline:
   - **Menu:** the game's Settings. Esc still opens Roblox's menu.
   - **Chat:** shows or hides the chat window and input bar, with a crimson pip for messages that arrive while it's hidden. **/** opens chat.
   - **Students:** shows or hides the player list.

   It fades back after a few seconds without the mouse near the top, and wakes when you move there. It sits just right of anything Roblox still draws in the corner (`GuiService.TopbarInset`), and the main menu hides it with the rest of the HUD.

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

**West grounds** (`MenuScene.WestGrounds`, temporary). This is the side the menu cameras look across on the right of the screen, which looked empty before.
- **West Hall:** a 60% copy of the school front, angled toward the courtyard, with lit windows.
- **Dead oaks:** four more procedural oaks.
- **Boundary:** the stone and brick wall with iron fence continues to x = -160.
- **Forest:** two rows of pine silhouettes.
- **Chapel:** the distant chapel is now a dark silhouette with a proper spire and a lit belfry. Its old spire was four loose wedges that read as grey slabs.
- **Town:** 48 more lit windows in the distant town.
- **Distance colour:** the forest and hill shapes are near-black so they read as night silhouettes.

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

## VFX textures

**Soft-edge pass** (`tools/vfx/make_soft_vfx.py`, numpy):
- **Tendrils:** the ring tendrils use `nh_wisp2_v`, nine twisting filaments that tile along the beam and fade to zero at both sides. Each tendril also fades in from the core and out at the tip, so none show straight cut-off lines.
- **Orientation:** Roblox Beams run an image's **vertical** axis along the beam, so the texture is saved rotated. The old texture was the wrong way round, and that caused the hard edges.
- **Shards:** the crystal-shard flipbook (`nh_shards2_2x2`) now fades every sprite out before its cell edge. The old sprites crossed the cell borders, so particles showed sliced edges.
- **Tried and removed:** a wide "halo" layer under each tendril read as flat sheets.

**Blender renders** (Cycles, physically based):

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
| `ReplicatedFirst.NHLoadingScreen` | the loading screen (admission file, asset counter, stamp) |
| `StarterPlayerScripts.Controllers.Gui.TopBar` | the custom top bar |
| `StarterPlayerScripts.Controllers.Gui.Identity` | Name & Clan + Spin Shop panel ([details](Names-Clans-and-Spin-Shop.md)) |
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

**Menu 1.1 (loading, names, top bar, VFX, west grounds):**
- **Loading screen:** counted 385 to 418 assets per run, with 1 failure (a sound the place has no permission for, already broken before). Each run took 11 to 20 s in Studio.
  - The live scene opens behind the title card.
  - The stamp lands, and the hand-off to the intro works.
- **Editing screen:** Name & Clan and Spin Shop were tested with real clicks and keys. See the names doc.
- **Top bar:** Chat, Students and Menu were tested through real key presses. Chat hides the chat window and input, Students hides the player list, and Menu opens Settings. Roblox reports `TopbarEnabled = false`.
- **Tendrils:** checked on screen. Soft filaments, with no cut-off lines.
- **West grounds:** checked under the night grade from the hero and pre-roll shots.

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
- Whether Roblox still shows its own Roblox-logo button with the top bar off. Studio screenshots don't include Roblox's own UI. The custom bar leaves room for it (164 px reported).
- Live servers: slot views use ProfileService `ViewProfileAsync`, and Studio uses the Studio data store.

**Leftover test data:** slot 1 of the Studio test profile was used.

## Audit (Menu 1.2)
Code review of the menu, slots, loading screen and save loader, then live tests. See the CHANGELOG entry for details.

| Found | Fix |
|---|---|
| Menu keys (W/S/Enter) still worked behind Settings and could trigger CONTINUE | `Local.SettingsUp()`: input is ignored while the Settings panel is visible |
| Posed students lost their catalog hair within about 2 s (the accessory's old weld pointed at a destroyed model, so the handle fell) | `Local.WeldAccessories` re-welds each accessory to the matching body attachment |
| Posed students had no race, so race skin and uniforms didn't apply | `Local.Student(..., Race)` sets the `Race` attribute before `ApplyTo` |
| The Bloodline tab's camera shot key didn't exist | `Config.MainMenu.Paths.Creator.Bloodline = CreatorLow` |
| A remote error left slot buttons dead or the screen black; a failed slot list showed no cards | `Choose`/`Enter` are wrapped in pcall; `List` retries 5 times |
| A failed ENTER SCHOOL added another Wardrobe hook each time | One hook per menu visit (`State.WardrobeHooked`) |
| `LastPlayed` was written straight into the profile | `UpdateState` `SetLastPlayed` action, plus the field in `PlayerData` |
| Gamepad couldn't turn the student | Right stick orbits; the Look button is selected on arrival |
