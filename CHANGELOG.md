# Changelog: Nightmare Highschool

All notable changes to the NH Combat Test dev place. The newest entries come first.

## [UI 1.7] - 2026-10-30: Wardrobe 2.0, painted eyes, lineage spins

### Added
- **Wardrobe tabs:** Look, Face, Hair, Outfit and Lineage.
- **Painted eyes:** original, high-res art for classic heads.
  - 8 shapes: Sharp, Hooded, Fierce, Doe, Sleepless, Cat (slit pupil), Gentle and Calm.
  - Each shape has a **Male** and a **Female** eye set. The female set has fuller lashes, a longer wing and lower lashes.
  - The iris is a separate tinted layer, so eye colour can be anything: 7 presets plus a colour wheel or HEX.
  - "Roblox face" keeps your own face.
- **Brows** are a separate layer, so you can pick them on their own. There are 11 styles plus None: Straight, Arched, Angled, Soft, Thick, Thin, Furrowed, Raised, and the extra-thick Bold, Heavy and Bushy.
  - They're drawn with fine hair strokes and match your hair colour, or a colour you pick.
  - Every style is fitted to every eye shape, so a brow never touches the lashes on any variant.
- **Mouths** are a separate layer too, drawn cel-shaded anime-style (modelled on an open × width mouth grid): a thin wine-coloured outline, a maroon / rose interior, a tooth crescent and a soft lower-lip shadow.
  - There are 20 styles plus None: Neutral, Smile, Flat, Smirk, Hint, Grin, Small, Ooh, Open, Talk, Laugh, Shout and Pout.
  - **Frowns:** Frown, Scowl, Sulk and Grimace.
  - **Anime extras:** Cat (":3"), Fang and Shark.
  - Each has a "Fuller lips" option with glossy pink lips.
- **Sharp faces that sit on the skin:** faces are drawn as SurfaceGuis on 12 strips that wrap the head 0.006 studs above the skin, so they stay full-resolution on every graphics setting (decals got down-sampled and looked crunchy). Previews convert them to decals automatically, and your own face hides in first person.
- **Nothing overlaps:** the art generator checks every face piece against every other and refuses to ship any overlap, for example brow on lashes, under-eye lines on lower lashes, or veins on line work.
- **Transformation eyes:** every shape, in both sets, has transformation versions. Gameplay switches them by setting the character attribute `Transformation`; players can't pick them.
  - Vampire: a crimson iris with a blade-shaped slit pupil, a glowing rim and a dark sigil ring, plus bloodshot whites, veins and an under-eye shadow.
  - Wolf: a huge amber iris, a ragged feral pupil with a gold rim and starburst, and a yellowed sclera.
  - Ghoul: a milky iris, a pinprick pupil, sunken sockets, bloodshot whites, and many branching veins spreading over the skin.
  - Wraith: blank glowing eyes with a halo. *Proposed:* it isn't in the concept doc.
  - **Second stage** (`TransformationStage = 2`): vampires and ghouls get **jet-black sclera**.
  - Transformations also swap the mouth: vampire fangs with a single crimson bead, a wolf snarl with gums and canines, a ghoul's jagged grin with split, stitched corners, and a hollow wraith mouth trailing smoke.
  - **Veins** are a separate layer, tinted from the character's own skin colour, so they look natural on any skin tone. They're shaded with a raised, lit edge and a bruised halo.
- **Colour picker** (a new kit component, `ColorPicker`): a hue wheel, a brightness bar, a HEX box and presets. It's used for skin, hair, eye and brow colour.
- **Catalog hair:** paste any Roblox hair accessory ID. The server checks it, loads it and saves it. Optional recolouring. Your avatar's own hair is hidden while it's worn.
- **"None"** hairstyle.
- **Lineage** (from the concept doc), rolled on the server and never chosen:
  - Races: Human 50% / Priest 30% / Vampire 20%.
  - Variants: Superhuman; Grand Priest and Pope; Nobleblood and Royal Vamp.
  - 2 trait slots, drawn from 13 proposed traits (Common to Legendary).
  - New students get a free first roll, then 3 race, 3 variant and 5 trait rerolls. There's a slot-machine reel (a new kit component, `SpinReel`) and an odds readout.
  - It's saved in `PlayerData.Lineage` (action `SetLineage`), and the server mirrors the `Race`, `SubRace`, `RaceTier` and `Traits` attributes.
  - A `Tier` (1 to 3) is stored for the concept doc's kill-count race tiers, worked out from grip executions. The thresholds (0 / 25 / 100) are a proposal.
- **Official uniforms:** Red Vest, Red Shirt, Black Vest and Black Shirt, with the school trousers. These are the Nightmare Highschool group's clothing, replacing the built blazer.
- **More outfits** (made from the uniform templates by the clothing session):
  - **Tops:** 14 more, for 18 in all: Navy / Forest / Charcoal / Vigil / Crimson Court vests; Navy / Forest / Ivory / Crimson / Delinquent polos; Black Blazer, Charcoal Cardigan, Varsity Jacket, and the Gym / PE Shirt.
  - **Bottoms (new choice):** Uniform Trousers, Dark Indigo / Black / Ripped Jeans, Charcoal Slacks, Khaki Trousers, Khaki Shorts and a Pleated Tartan Skirt. Skin shows through where the clothing is open.
- **Spin shop hooks:** `Lineage.GrantSpins(player, kind, amount)` (server) for purchases. The Lineage tab gets a "Get more spins" button once the Identity shop exists.

### Changed
- The posture meter now sits beside the health bar. It used to collide with the menu buttons on wide screens.

### Fixed
- **Save slots** (the main menu): Settings and the Wardrobe now re-read the profile when a slot loads, so saved settings come back after picking a slot. Shadows-off persisted across a rejoin in the live test.
- **Lineage, "Last joined" and the look** now run when a profile loads (`Data.ProfileLoaded`), not on join, so they work when the profile loads later from the main menu.

### Verified (live playtest)
- The official uniform (Black Shirt) and the Nightborn look came back after a rejoin.
- The face renders on the live character. All 12 strips measured 0.006 studs above the skin, welded.
- The free first lineage roll happened on profile load: Priest, with Early Riser and Light Sleeper.
- A race spin landed on Human, with the reel animation and odds updating.
- The posture meter no longer overlaps the menu buttons.
- The Wardrobe's main-menu stage mode works in the quest session's creator.

### Notes
- Traits are data only until the stat system exists.
- Spins aren't used up in Studio.
- 420 face textures, all generated by `Tools/ui-textures`, with automatic no-overlap checks.

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
