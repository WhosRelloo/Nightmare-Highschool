# Changelog: Nightmare Highschool

All notable changes to the NH Combat Test dev place. The newest entries come first.

## [Menu 1.0] - 2026-10-30: Cinematic main menu and save slots

### Added
- **Main menu:** a cinematic night courtyard in front of the academy. It has wet cobblestone, Victorian brick, gothic stone, a clock tower with working hands, an iron gate with gargoyles, and dead oaks hung with moss, a pair of sneakers and Crimson Court ribbons.
  - Every surface uses PBR materials: colour, normal and roughness maps.
  - Your student floats in a crimson clock seal while energy tears out of a stone ring behind them.
  - Ambient life: lamps flicker, windows die, chimneys smoke, bats circle the tower and lightning flashes.
- **Camera:** a skippable intro fly-in, then smooth spline moves between every screen, with handheld drift and mouse parallax.
- **Menu items:** CONTINUE, PLAY, SETTINGS and CREDITS (keyboard, mouse and gamepad).
- **Save slots:** three students, each with their own save (race roll, quests, factions, Yen and record). Slot 1 is your existing save, so nothing is lost.
  - Each card shows race, title, faction rank, Yen, quests, takedowns and when you last played.
  - Each slot's student stands on a lit plinth; empty slots are a crimson ghost.
- **Edit your student:** after picking a slot, your real character steps into the seal and the Wardrobe docks beside them.
  - The camera cuts for each tab: face close-up, hair three-quarter view, full body, low angle.
  - Drag to orbit.
  - ENTER SCHOOL pushes the camera to the doors and fades you into school.
- **VFX textures rendered in Blender Cycles:** volumetric smoke (a 4x4 flipbook), tileable plasma for the tendrils, lit crystal shards (2x2), embers and mist. The render script is `tools/vfx/render_vfx.py`.

### Changed
- **Saves:** your profile now loads when you pick a slot, not on join. The server spawns and respawns characters (`CharacterAutoLoads` is off), and combat is blocked while you're in the menu.

### Verified
- Live playtest with real clicks and keys: intro, menu, slots, editing (the Face-tab camera cut), entering school with the HUD, camera and lighting restored, and Continue.
- Camera speed measured during the intro: it ramps smoothly with no stops between shots.
- **Not tested yet:** two players, and phones.

## [UI 1.6] - 2026-10-30: One save system; "Look" instead of race

### Changed
- **Settings, Wardrobe looks and "Last joined" now save in your main profile (ProfileService)**, like reputation and quests, instead of in separate DataStores. Saving, session locking and rejoining are all handled by the profile system.
  - `PlayerData` gains `Settings`, `Appearance` and `LastJoined`.
  - `UpdateState` gains the actions `SetSettings`, `SetAppearance` and `SetLastJoined`.
  - The server validates and rate-limits every request before saving it.
- **Wardrobe:** the race picker is now a cosmetic **Look**: Scholar, Chapel (gold cross pin) or Nightborn (pale skin, red glint). Race is a rolled gameplay system and is never chosen in the mirror. The wardrobe only sets the cosmetic `LookStyle` attribute.

### Removed
- The DataStores `NH_Settings_v1`, `NH_Appearance_v1` and `NH_LastJoined_v1`. No code references them anymore.

### Verified
- In edit mode: everything compiles, the new profile actions apply to a default profile, defaults fill in, and a `Race` key sent by a client is dropped.
- **Still to do:** a live playtest. Studio's Play button is stuck and needs a manual Stop, then Play.

## [UI 1.5] - 2026-10-30: Wardrobe (character creator) and "Last joined"

### Added
- **Wardrobe** (press **K**, or the Wardrobe button on the left): make your student, with a live preview of your own character.
  - **Race:** Human, Priest (gold cross pin) or Vampire (pale skin, red glint in the eyes). It's cosmetic for now and has no gameplay effect. It sets a `Race` attribute on the player and character for future systems.
  - **"Use my Roblox outfit"** (on by default): your Roblox clothes stay. Turn it off to wear the NH uniform with the skin and hair you pick. Your outfit is stashed, not deleted, and comes back when you switch it on again.
  - **Uniforms:** Night Form, Chapel Grey and Archive Navy (blazer, collar, tie, school crest).
  - **Looks:** 6 skin tones, 4 hairstyles (Neat Crop, Fringe, Long, Bun) and 6 hair colours. All of it is built from original parts.
  - It opens by itself the first time a player joins a live game, but never in Studio.
  - The look is applied by the server (after the Roblox avatar loads), saved to `NH_Appearance_v1`, and re-applied on every respawn.
- **"Last joined"** on the server select screen shows the campus you were at before this one, with the date (`NH_LastJoined_v1`). New players see "First time on campus".

### Verified
- In edit mode, the real look builder dressed three test students: a Human in Night Form, a Priest in Chapel Grey and a Vampire in Archive Navy.
- The Wardrobe window rendered with its live preview.
- Data validation: an unknown race or an out-of-range choice falls back to the defaults.
- The last-joined text formats correctly.
- **Not yet tested in a live playtest:** Studio's Play control was stuck at the time. Still to check: saving, re-applying on spawn, and the outfit stash and restore.

## [UI 1.4] - 2026-10-30: Settings menu

### Added
- **Settings menu** (press **M**, or the Settings button on the left). Every option really works and saves to your profile.
  - **Controls:** rebind Block, Dodge, Sprint, Slide, Heavy Attack, Feint, Carry and Grip. Keys owned by other systems (E, P, J, M, Space, LMB, 1-9, I/O) can't be taken, and duplicates are refused.
  - **Audio:** Master, Combat Effects, and Music & Ambience volume.
  - **Camera:** Field of View (60-100°) and Camera Shake strength (0% turns it off).
  - **Interface:** UI Scale (80-120%, scales every NH panel), Show HUD, Show Clock.
  - **Graphics:** Shadows, Screen Vignette.
  - **Reset to defaults.**
- Settings save to their own DataStore (`NH_Settings_v1`), separate from game progress. They're validated on the server (ranges clamped, bad keys refused) and written when you leave.

### Changed
- The input controller can now rebind actions at runtime. Camera shake now respects the player's Camera Shake setting.

### Verified in a live playtest, with real input
- M opens the menu. O can't be used, because Roblox's camera reserves I and O for zoom.
- Rebinding Dodge Q → G: afterwards Q did nothing, and G dodged 8.9 studs.
- Shadows off turned off the game's shadows. Clicking the FOV slider set the camera to 80°.
- After leaving the game, the saved record held Dodge = G, Shadows off and FOV 80. The test record was then cleared.
- On join, the defaults loaded and applied (volumes, FOV 70, shake 100%), and game sounds were routed into the volume groups.

## [UI 1.3] - 2026-10-30: Posture meter goes live

### Changed
- **Posture meter** (bottom-left) now follows your real guard. It reads the server's existing posture value, which fills when you block hits and drains after 2.5 s.
  - It shifts from candle-gold to blood-red as it fills, and the label turns red above 80%.
  - When your guard breaks, the label flashes **BROKEN**.

### Verified in a live playtest
- **Server to HUD:** posture set on the server at 45 and 92 shows on the HUD at 45% and 92%, and the colour shifts.
- **Break:** a 95 → 0 break flashes BROKEN, then the label returns to POSTURE.

## [UI 1.2] - 2026-10-30: Playtest pass

### Changed
- The DOWNED alert's subtitle and countdown are larger.
- The posture meter label is larger and readable.

### Verified in a live playtest, with real key presses
- **Hotbar:** 1 equips your tool (the slot glows gold); pressing 1 again unequips it.
- **Dialogue:**
  - E on Pip opens the compact box (464×149 px on a 600 px-tall window), and the bottom HUD hides.
  - 2 picks a reply and closes it, and the HUD returns.
  - Number keys don't fire the hotbar while you're talking.
- **Yen** updates live (¥327 → ¥347 from a quest reward).
- **Interaction prompt** renders as the engraved E key cap with "Pip Larkin / Talk".
- **Clock** ends above the quest tracker.
- **Console:** no UI errors.

## [UI 1.1] - 2026-10-30: Quest UI polish

### Changed
- **Quest tracker:**
  - The card and the stealth detection meter use the same ornate chip as the clock.
  - The detection bar is an iron-framed meter.
  - The objective marker is an engraved gold plate.
- **Quest journal:** quest, clue and insight blocks are bracket-cornered kit cards. A picked clue gets a gold frame and a warm fill instead of a flat colour, and hovering a clue lights its frame.
- **Clock HUD** now scales with the screen like the quest tracker, so the tracker card always sits below it.

### Fixed
- Auto-sized kit cards no longer have an empty band underneath. The clock panel now matches its text exactly.

### Verified
- **In a live playtest:** the new HUD (health, hotbar, Yen, posture meter, DOWNED alert), all 30 prompts switched to the custom style, the core health and backpack hidden, and the clock fitting its text.

## [UI 1.0] - 2026-10-30: "After Dark" UI overhaul

### Added
- **NH UI kit** (`ReplicatedStorage.UI`): a shared Theme plus Components builders for:
  - panels, tabs, buttons, toggles, sliders and keybind rows
  - item slots and grids, search, stat sheet, danger alert, player list and dialogue
  - health bar, hotbar and meters, toasts, choice rows and bars
  - server rows and browser, character preview and credits
- **Original gothic art** with PBR lighting baked into every texture: iron-gate arcade borders, chalk-smudged slate, wax-seal rarity gems, a cracked skull-bell, a clock-face health orb, and candle, blood-drop, quill and cross icons.
- **In-play HUD** (`Controllers.Gui.KitHud`):
  - a health bar with a % orb, plus a delayed "ghost" segment showing recent damage
  - a hotbar built from your Backpack tools: click, tap or press 1-9
  - live Yen
  - a posture meter
  - a DOWNED alert with the get-up countdown
- **Gothic interaction prompts** (`Controllers.Gui.PromptUi`): an engraved [E] key cap that fills with candle-gold while you hold, plus the object and action text. Touch players hold the key cap.
- **Server selection screen**:
  - a live campus list: a MemoryStore heartbeat, refreshing every 8 s, with Join and Quick Join
  - an in-game period and faction crest on each server
  - a character preview that mirrors your actual character and updates live
- **UI previews** in StarterGui. They're saved disabled and never show in a real game.

### Changed
- **NPC dialogue:**
  - The box is smaller and sits lower, so it no longer covers the view.
  - The ornate frame takes the speaker's faction colour, and replies are numbered rows.
  - The box scales down on short screens.
- **Notifications** are engraved toasts with a wax seal coloured by type.
- **Clock HUD** is an ornate chip, and the class waypoint is an engraved plate.
- **Downed prompt** is an engraved plate above the health bar. It turns red when you're downed or gripped.
- **Factions panel (P):**
  - an ornate panel with a "Who's Who After Dark" plaque
  - bracket-cornered faction cards and iron progress bars
  - kit buttons for the toggle, close and titles
- **Class lessons:** the chalkboard has an iron ornament frame over a slate-green board, replacing the wood border.
- The Roblox **core health bar and backpack hotbar** are replaced by the new HUD. The HUD hides during dialogue and lessons, and number keys are ignored then.

### Fixed
- Leaving a lesson no longer turns the core backpack back on when the new hotbar is active.
- Ornate frames on auto-sized UI no longer stretch to fill the screen.

### Known issues / next
- Posture isn't sent to the client yet, so the meter stays empty until combat sets a `Posture` attribute.
- The quest tracker and quest journal aren't reskinned yet; that waits until the quest work settles.
- The flash, damage-tint and vignette screen effects are unchanged on purpose.
- "Last joined" on the server screen needs saved data.
- The credits list uses placeholder names.
- Still to check in a full playtest: the HUD, prompts and new dialogue size in live play, touch on a real phone, and server teleports (which only run in a published game).
