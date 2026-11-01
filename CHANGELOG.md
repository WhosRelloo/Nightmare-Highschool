# Changelog: Nightmare Highschool

All notable changes to the NH Combat Test dev place. The newest entries come first.

## [1.6] - 2026-11-01: Fists, race actions, enrollment and the School Store

A combat class, race-specific finishers, a new-student flow, and a batch of requested fixes.

### Added
- **Fist class (owner's animations):**
  - Runs on the same combat code as the Katana (four-hit M1 combo, running attack, downslam, crit, aerial crit, block and parry, grip), with its own timings and a shorter reach.
  - The Fist animations have no Hit/EndLag markers. Contact times were read off each clip's keyframes (fastest limb, checked against Katana's real markers) and stored in `Config.Weapons.Fist.Markers`. A marker that exists in a clip always wins (`ServerStorage.Packages.AnimMarkers`).
  - Skills on **Z / X / C**: Question Mark Kick (launch), Body Slam and Bear Hug (startup lunge, then a paired grab and victim animation, then the finisher; grabs go through a guard).
  - The skill slots sit bottom-right, built from the UI kit's item slots. A veil drains and the seconds count down while each one cools down.
- **Race actions on N (finish a downed body):**
  - Vampire: **Blood Drain**. Ghoul and Werewolf: **Eat Body**. Wraith: **Soul Siphon** (pale wisps spiral out of the body). Human and Priest: **Exorcise** (a gold light column; only works on the unholy).
  - Each one heals you and feeds your race hunger. Feeding is no longer automatic after a grip.
  - Exorcise and Soul Siphon use a placeholder kneel clip until dedicated animations exist.
- **Enrollment:** new students start in their own clothes.
  - They enrol at the **Enrollment desk** outside the Records Office by picking one of three uniforms (Black Blazer, Navy Vest or Charcoal Cardigan, with trousers or the tartan skirt by body type; race recolours apply).
  - You can't start a class until you've enrolled.
  - Existing students count as enrolled and keep what they wear.
- **School Store** (the vending machine): every school top for ¥250, sorted into tabs (Official, Vests, Polos, Jackets & PE, Owned).
- **Try-on preview** on the enrollment and store screens: your own character wears whatever you point at.
- **Wardrobe stations:** the wardrobe now opens only from a locker-room wardrobe ("Change Outfit" prompt; tag a part `NHWardrobe` to add one) and closes when you walk away. The K key and HUD button are gone, and the server refuses look changes made anywhere else. One placeholder station sits by the hallway lockers.

### Changed
- **You're slower in combat:** walk and sprint speed drop by 20% while you're combat-tagged.
- **Slide into a run:** if you're still holding Shift when a slide ends, you go straight back to a full-speed sprint.
- **Capes fit like the owner's R6 rigs:** each cape stores its exact fit (`NH_TorsoFit`), scaled to your body, so it sits on your shoulders and back instead of hanging off one side. The sway now bends every cloth chain the same way (the side chains used to twist).

### Fixed
- **Fist animations were being overridden:** the Fist equip clip (the looped idle stance) never ended, so it covered every attack and the Fist idle, walk and run never loaded. The crit now plays at Action4 with a short ease in and plays to the end.
- **Cape templates** no longer carry animation-editor data (about 5,000 instances each).

### Notes
- A Studio-only hitbox debug box can be left behind by an interrupted attack. Players never see it.
- Recovered: `M1`'s two child modules (Running M1, Aerial M1) were restored from cloud version 237 after a module rebuild dropped them. A copy is in `ServerStorage.NH_Backup`.

## [VFX 1.5] - 2026-11-01: Stealth and the supernatural, all-new tier-ups, capes, combat tag

VFX Batch 3, a full PBR rebuild of the tier-up cutscenes, and a set of requested fixes and features.

### Added
- **Watcher awareness (P1-10):**
  - A "?" appears over a stealth-zone watcher once you're 25% noticed, and firms up as the meter rises. At 75% it becomes a crimson "!" and the screen edges darken (this follows the Vignette setting).
  - After dark, the night custodian carries a flickering torch (a real light, seen by everyone).
  - The watcher's speech bubble uses the UI kit look.
- **Thrown out (P1-11):** when a watcher catches you, they grab you with the new caught animations (watcher 110064849600468, you 124875544038575). The screen then fades to a "THROWN OUT" stamp while you're walked to the door. The old "Caught!" toast is gone.
- **Quest-giver seals (P1-14):** a wax seal over NPCs who have something for you. The server works these out and they update whenever your quests change.
  - Gold "!": a quest to start.
  - Gold "✓": talk to them.
  - Gold "↺": retry a failed quest.
  - Iron "…": a quest you're still doing for them.
  - At most 8 show at once, and only within 80 studs.
- **Rite props answer you (P1-12):** each rite prop reacts when your rite uses it. These effects are only visible to you.
  - Blood ripples and red mist in the font.
  - The cracked bell swings (about 11°) with a shock ring.
  - Frost creeps over the mirror.
  - Silver steam from the stack, embers from the ash.
  - The ward's scratches glow, then cool.
  - Sparks fly off the iron.
  - Grave dust rises from the crate, and a dawn shaft lights the stone.
- **Votives (P0-3):** the three votive candles now start **unlit**. They light, with a burst of embers, when your rite counts them, then flicker gently.
- **Detention (P1-16):** a dust-and-glint puff for each piece of trash you pick up, and a gold flourish at the bin when you finish.
- **The Blood Takes (P1-13):**
  - When a bite turns someone, that player gets three heartbeat pulses at the screen edges in their new race's colour; the colour drains, then their race's tint washes in.
  - Anyone within 140 studs sees blood-coloured smoke and rising embers.
- **Tier-ups rebuilt with PBR set pieces (P1-17, owner request):**
  - Every race gets a glowing ground sigil (a second, counter-turning ring at Tier III), a light column and a climax shockwave.
  - Fifteen new Blender-modelled meshes carry baked colour, normal, roughness and metalness maps (`art/vfx/evolve`, templates in `ReplicatedStorage.NHEvolveFX`).
  - **Vampire:** a wet blood pool spreads under them, a bat swarm circles, then veined blood crystals erupt.
  - **Werewolf:** three claw slashes, then the howl cracks the floor and throws rock while a huge moon rises behind them.
  - **Ghoul:** grave mounds heave up, one with an R6-style skull, and bone spurs claw out of the earth through drifting spores.
  - **Wraith:** ice creeps across the floor, frost falls, and ice spikes burst up.
  - **Human:** an iron hunter's sigil forges behind their back, and silver stakes slam down in a ring with sparks.
  - **Priest:** a gilded cross rises behind them, a gilded halo settles over their head, and feathers fall.
  - Erupting pieces stay out of the cutscene camera's view. The cutscene's own effects now use the nh_* sprites (no default Roblox smoke or sparkles), and Tier III leaves a 5-second afterglow.
  - The "Evolved" message is now a banner that waits for the cutscene to end; before, the toast used to expire unseen behind it.
- **Combat tag:** any combat hit tags both players for 30 seconds. A padlock emblem with a glowing skull keyhole, chains and barbed wire shows "DANGER" and a countdown; it stamps in, beats like a heart and flickers in the last 5 seconds.
  - **"mb all"** (or "my bad all") in chat ends every fight you're in. Each person you traded hits with drops out of combat unless they're fighting someone else, and gets a small "X said mb" note.
- **Capes in the Spin Shop:** the Vamp, Rogue and Fur Cape.
  - Owned by the student you buy them on; the server stops anyone wearing a cape they haven't bought.
  - Worn from Wardrobe → Outfit → Cape.
  - They sway like cloth on every client: back when you run, against your turns, fluttering in the air, gently breathing at rest. Reduce Motion halves this.
  - Product ids are still 0 ("not on sale yet").
- **Body shape:** the Wardrobe's Look tab offers Standard or Female (your Female Body torso).
- **Waypoint upgrade (P1-15):**
  - An edge chevron with the distance points to off-screen targets, kept clear of the HUD.
  - The marker shrinks with distance.
  - Within 25 studs there's a ground ring and a light column, with one gold pulse when you arrive.

### Changed
- **Sprint is hold Left Shift** (it used to be double-tap W). Saved W bindings move over automatically. **Shift lock is Left Alt.**
- **Colour wheel:** it no longer turns into a black disc on dark colours; the hues stay visible.
- **Ghoul and Wraith looks:** the Ghoul's jaw stitches sat inside the head and now sit on the face. The Wraith's breath, wisps and frost were nearly invisible, especially by day, and are now clearly readable with the nh_* sprites.
- **Quest tracker:** it no longer rescans the whole map every 0.25 s when a target is out of view.

### Security
- **The Female Body model contained a Studio-only phishing script.** It showed a fake "Roblox Studio" window with a command box and a copy button, built to trick a developer into running code. It was disabled and moved to `ServerStorage.NHQuarantine`; nothing else had been planted.

### Verified (Studio, Play)
- **Keys:** holding Shift sprints at speed 25, and mouse lock is bound to Left Alt.
- **Stealth:** watcher "?" at 0.30 detection, "!" at 0.82, then the THROWN OUT stamp (client log, through the real stealth path). The custodian's torch is on at 21:30.
- **Seals:** Dex shows "↺" for the failed Special Delivery (screenshot).
- **Rite props:** votives start unlit and light at 0.43 brightness; the bell swings 10.8° and comes back exactly to rest; all 11 rite effects fire without errors.
- **Tier-ups:** all six races played through the real Evolve path, with screenshots for every race. The "Evolved" banner arrived 0.2 s after the cutscene ended.
- **Wardrobe:** the colour wheel, brightness bar and swatches all save; Female body saved and applied.
- **Combat tag:** the tag and countdown showed after a real hit (screenshot), and "mb all" cleared it.
- **Capes:** all three were measured on the body (the Fur Cape needed its own offset). While sprinting, the cape tip swings from 0.64 to 1.76 studs behind the torso.

### Not yet
- **Re-bake:** IceSpike, MoonDisc and BloodPool weren't re-baked with the latest finer veins and deeper moon craters; the PC ran out of memory.
- **Two-player:** "mb all" between two real players, and other players' view of the tier-ups and capes.
- **Owner's animation list:** idles, gym, emotes, fist moves and the rest still need their ids.
## [VFX 1.4.1] - 2026-10-31: Banners stay clear of conversations

### Fixed
- **Quest banners covered the dialogue replies.**
  - **Why:** quests are accepted by choosing a reply, so the "New quest" banner fired while the dialogue box was still open, and the banner's low-centre spot sat over the replies.
  - **Now:** Moment banners wait up to 6 s for a conversation to end. If it's still open, or one opens while a banner is up, the banner rises to sit just above the dialogue box, then drops back when the box closes. (`Controllers.Gui.Moments`, using the `InDialogue` attribute.)

### Verified (Studio playtest)
- **Setup:** a real conversation with Ezra (4 replies) at a 1680×683 viewport.
- **Banner fired mid-conversation:** it was held, appeared at 6.3 s, and lifted 111 px, ending 10 px above the box.
- **No conversation:** the banner shows at once in its usual spot.
- **Conversation opened mid-banner:** the banner lifts to the same 10 px gap.
- **Conversation closed mid-banner:** it drops back.
- **Console:** no errors.

## [VFX 1.4] - 2026-10-31: The bell rings, the monitor spots you, and the big moments get their own banner

VFX Batch 2 ("core feedback"). Big moments now show as one gold-framed banner, low on screen and clear of the toast stack, and only one plays at a time. Each banner **replaces** that beat's old toast, so nothing shows twice. Everything follows Camera Shake, Reduce Motion and Reduce Flashing, and waits while you're in the main menu or mid tier-up.

### Added
- **School bell and period card (P0-8):** when the period changes, a brass hand bell rings and a card names the period, subject, room and end time (e.g. "Period 2 · Chemistry · Room 103 · until 9:45 AM").
  - The clock panel's rim flashes gold, and the red class marker pulses twice when a class starts.
  - It rings at class start and end, passing time, break, lunch and the end of classes. "Before School" gets a quiet card with no bell. Morning, evening and night stay silent.
  - It never rings when you join or while you're in the menu.
- **"Spotted!" (P0-9):** when a hall monitor starts chasing you, and only you, the monitor gets an orange outline and a "!" over its head, a whistle blows and the screen edges darken.
  - **Caught:** the screen drains of colour for a moment and a red "! CAUGHT" stamp lands.
  - **Escaped:** the "!" turns into a "?" and the alert fades.
  - It clears on every exit: going to class, getting downed, the monitor going off duty, respawning.
- **Quest beats (P1-4):** banners for a new quest, a new objective, quest complete and quest failed.
  - Main quests are gold, side quests are chalk, rites use your race colour, and failures are red. Each also has a word and a mark (! » ✓ ✗), so colour is never the only cue.
  - A quest's ending text plays as its own "Epilogue" banner. Long text wraps and the banner grows to fit, so story text is never cut off.
- **Clue discovered (P1-5):** gold-and-ink sparkles rise from the object and it flashes gold, then a "+ CLUE" slip with the clue's name flies into the Journal button.
- **Level-up "Bell Toll" (P1-6):** a gold banner with your new level stamped on the seal, a bell and a small camera nudge. Players within 80 studs see an ember column, a gold ring at your feet and a warm light. A multi-level jump plays once.
- **Purchase confirmed (P1-8):** after a Spin Shop grant really goes through, a banner says what you got (e.g. "+5 Clan spins").
- **Roll call (P1-9):** respawning fades in from black while the colour comes back. Other players nearby see a violet smoke puff and a chalk ring where you appear. It never plays on the menu spawn or when entering school.

### Changed
- **Server:** quests (start, objective, complete, fail), clue found, level-up and purchase-granted now fire `NHFx` events instead of toasts. Smaller updates, such as objective counts, optional objectives and "already in your case file", are still toasts.
- **Level-up:** the server no longer parents its own ember emitter, which clients might never have seen (P0-10).
- **Quest complete:** its banner now plays before any level-up the rewards cause.

### Verified (Studio, Play)
- **Bell:** jumping the clock to 8:19 and then 8:20 played the Homeroom card, then the Period 1 card (screenshot).
- **Quest chain through the real server path, on spare slot II:**
  - Attend gave a "New objective" banner (screenshot).
  - Reading the locker note showed the clue slip (screenshot), then completed New Kid. The reward EXP gave a level-up banner (screenshot), and The Empty Desk started.
- **Banner order (client log):** a purchase banner (real receipt path), then "New quest", then "Quest failed" (deadline), in that order.
- **Spotted (real HallMonitor):**
  - Caught: the "! CAUGHT" stamp showed (screenshot).
  - Escape: the "!" changed to "?" 3.7 s into the chase, and the outline and mark were gone 1.75 s later (client log).
- **Roll call:** after dying, the veil and the desaturated colour started on the new character (client log).
- **Re-check after the fixes:** a long objective wraps fully, and the clue slip fits its text (screenshots).
- **Console:** no errors from the new code, and the two new sound ids load with no access errors.

### Not yet
- **Not seen yet:** the Epilogue banner (New Kid has no ending text), the clock-rim flash, the marker pulse, and the clue slip's flight into the Journal.
- **Order fix:** the "complete before level-up" fix is only checked by reading the code.
- **Other players' view:** the level-up column and the respawn puff haven't been watched from a second player.
- **Settings:** Reduce Motion and Reduce Flashing haven't been tried with these effects, and phone layout hasn't been checked.

## [VFX 1.3] - 2026-10-31: Chairs, a staff lounge, a living Archive and a vending machine you can thump

### Added
- **Seating everywhere:**
  - a wrought-iron chair behind every student desk (48)
  - a high-backed oak chair tucked into each teacher desk (6)
- **Staff Room lounge:**
  - a crimson chesterfield and two wingback armchairs along the back wall
  - four teacher chairs round the staff table
  - a wrought-iron bin
  - All of it stays clear of the watcher's patrol route.
- **Hallway vending machine:** a gothic iron vending machine over the vending-machine quest spot.
  - **Thump** it and it rattles for everyone: the cabinet rocks, the wares jump, the flap clacks and the sign flickers.
  - It also rattles when the vending-machine quest spot is searched, and its quest prompt still works.
  - Reduce Motion and Reduce Flashing tone it down.
- **The Archive:**
  - **Bookcases:** nine oak bookcases with pointed crests replace the old shelf blocks, 93 books each.
  - **Pull a book:** the whole case spills its books onto the floor with real physics, the same for everyone. After 12 seconds they drift back onto the shelves.
  - **Altar:** a carved stone altar with its reredos now stands in the north-west rite corner, lit by a crimson window and candles.
  - **Candelabra:** a standing wrought-iron candelabrum on each side of the altar.
- **R106 bin:** the detention bin is now a wrought-iron basket. Its detention prompt is unchanged.

### Fixed
- **Prop pivots:** batch-2 props came in lying on their backs.
  - **Cause:** the importer's rotated pivot, plus `Model.WorldPivot` being ignored once a model has a PrimaryPart.
  - **Fix:** the setup now sets the PrimaryPart's PivotOffset directly.
- **Prop prompts:** the vending and bookcase prompts didn't appear with streaming on, because the model arrived before its parts.
  - The client now waits for the piece that hosts the prompt.
  - Both models stream in whole (Atomic).

### Verified (Studio)
- **Placement (screenshots):**
  - a classroom with its chairs
  - the Staff Room
  - the Archive's bookcases and the altar, with a candelabrum each side
  - the vending machine
  - Every prop sits on its floor (raycast check).
- **Vending rattle (Play):** a Thump from the client set `RattleAt` on the server. On the client the cabinet rocked up to 2.1° and the flap swung 34°, then everything returned exactly to rest.
- **Book fall (Play):**
  - **Fall:** a Pull from the client unanchored all 93 books, and after 2.5 s 38 had left the case and most lay on the floor (screenshot).
  - **Restore:** after 14.5 s all were back, anchored and in the case.
- **Prompts (Play):** all 10 appear (9 bookcases and the vending machine), and Thump is enabled while the quest prompt is off.

### Not yet
- **Import leftover:** a second teacher-desk import was found floating over the school and moved to `ServerStorage.NHPropsImportLeftovers`.
- **Two-player check:** the rattle and the book fall haven't been watched from a second player.

## [VFX 1.2] - 2026-10-31: Weathered props, batch 2 ready, lesson test fixes

### Changed
- **School props look worn in.** Desks, teacher desks, chalkboards and lockers were re-baked with:
  - chipped enamel and bare metal on edges
  - dirt in the crevices
  - softened edges
  - new brass, iron, leather and paper materials
- **Batch-2 designs upgraded before import:**
  - **Student chair:** now matches the desk's wrought-iron work: raked back legs, a pointed-arch back with the desk's rose, brass finials (3.5k triangles, was 296).
  - **Candelabrum:** now has scroll feet, a basket-twist iron column, a drip tray, four scroll arms and a tall centre candle, with wax drips.
  - **Gables and crests:** the vending machine, bookcase and altar get solid pointed gables, and the teacher chair a pointed crest with pinnacles. These replace wavy curves.
  - **Leather:** the grain is about 2.5× finer, so chairs and sofas read as leather, not stucco.
  - **Bin:** the paper in it is properly crumpled.
- **Rarity reveal on spins:** the clan reel and the race reel now land with the UI kit's rarity reveal: a glint, then glows and rings that grow with rarity, and the near-miss stop for Legendary and Cursed.

### Fixed
- **End lockers:** the two lockers at the ends of the hall row were turned sideways. All eight now face the hall.
- **Test bridge:**
  - `NightStudy` with an unknown player name returns false instead of erroring.
  - New Lab Mix auto-player: `AutoLab(name, accuracy)`, or `StartLesson(name, room, accuracy)`. Lab Mix is a rhythm game judged on server time, so tool-driven tests could never hit a note, and the beaker blew after six misses (the real rule).

### Verified (Studio)
- **New textures:** screenshots of a classroom and the hall locker row show them on all 76 placed props: 48 desks, 6 teacher desks, 6 chalkboards, 10 lockers.
- **End lockers:** they face the hall (screenshot).
- **Lab Mix auto-player (Play):**
  - It hit 20 of 22 notes, and the lesson ended normally.
  - The UI kit then checked Lab Mix's new UI live with it.
- **Night Study (Play):**
  - An unknown name returns false.
  - The real name, at 21:00 by the Archive table, starts a session.

### Not yet
- **Rarity reveal:** the UI kit checked it on a Legendary test spin, but not inside the Identity or Bloodline reels.
- **Batch 2 import:** waiting for the FBX import in Studio. Then `props_setup2` places everything, and the vending rattle and book fall get tested.

## [UI 1.14] - 2026-10-31: Class lessons get the full UI-kit treatment

The user asked to "make the actual minigame ui higher quality with the existing ui we have in game". Everything here uses existing UI-kit art only: plates, slot and thin frames, seals, the HUD orb, the candle icon and the divider.

### Changed
- **Kit typography:** lessons use the kit's Fantasy title face and Garamond book face instead of the cartoon fonts (LuckiestGuy, PermanentMarker, PatrickHand). The chalkboard stays as the classroom's identity.
- **Board header:** the lesson's name ("POP QUIZ", "WORD SCRAMBLE", "MATCH THE PAST", ...) sits on a gold kit plate hanging from the frame, with the subject and level beneath.
  - Score and the lesson clock each have their own framed plate; the clock has the kit's candle icon.
  - A time bar under the header burns down, gold, turning crimson for the last 10 seconds.
- **Buttons, letter tiles, lab pads and memory cards** are kit slots: a dark well with an iron-gold slot frame and a soft top light.
  - On hover the frame turns gold and the button lifts slightly; on press it sinks.
  - Right and wrong still tint green and red, now with the ✓/✗ glyph.
- **Timers inside the games** (per question, per word) are kit progress bars.
- **Framing:** the Lab Mix lanes and beaker get kit frames, and face-down memory cards show a gold wax seal behind the "?".
- **Countdown:** the 3-2-1 is stamped into the HUD's gold orb, with a tick each second.
- **Report card:** the result is now a kit panel instead of a paper sheet.
  - It has a "Report Card" header and the course line.
  - The grade sits in a wax seal coloured by the grade: gold A, blue B, silver C, amber D, crimson F. It still slams in, with wax drops; A shimmers and F gets crossed out.
  - The score has a bar that fills.
  - Result lines carry ✓ / ✗ / • marks.
  - At the bottom: a divider, the teacher's remark in quotes, and a gold Close button.
- Reduce Motion: no lifts, pops or slams, just fades.

### Verified (Studio playtest, real lessons via the test bridge)
- **Pop Quiz (Mathematics):**
  - The countdown orb stamps each second, and the gold title plate, score and clock plates and the time bar all show.
  - A right answer goes green with a ✓ and "Correct!"; a wrong one goes red with "Nope." and the right answer shown green.
  - The report card shows a crimson F seal with the cross-out and wax drops, "Score 13%" with its bar, "✗ Failed", the remark and a gold Close.
- **Word Scramble (English):** framed letter slots and tiles, the kit-styled Shuffle / Clear / Skip buttons, and the word timer bar.
- **Match the Past (History):** wax-seal card backs, and a flipped card reading "EVENT · First Moon landing".
- **Fixed during testing:** the title plate's own layer hid its text, and the slot frames were inset by the button's text padding.
- **Lab Mix (Chemistry), seen live with the quest session's new test-bridge auto-player (85% accuracy):** framed lanes, kit D/F/J/K pads, the gold-framed beaker and "PERFECT ✓". The run ended on a gold "A" report card ("Score 96%", "• Practice round: no rewards.").

### Fixed (UI 1.14.1)
- **Lab Mix leftover note outlines:** a hit or missed ingredient faded its fill but left its chalk outline sitting at the bottom of the lane. The whole note now fades and hides. (Checked by reading the code; it was never caught on screen.)
- **Rarity reveal rings drew over the result text:** on a Legendary spin, the gold ring burst covered the name. Rings now sit behind the reel's text and burst out past its edges. Verified on a "Hollow King · Legendary" test spin: the name reads cleanly, with the ring and glint behind and across.

## [VFX 1.1] - 2026-10-31: Real nights, PBR school surfaces, the first modelled props

### Added
- **Blue-violet nights.** The school now has a day-night grade:
  - **Times:** pink-gold dawn (6:00–8:00), amber dusk (16:30–18:30), and a moody blue-violet night from 20:00, still as bright overall as before.
  - **How it works:** `Controllers.World.DayCycle` blends keyframes from `Config.DayCycle` by the school clock. It steps aside while the main menu owns the lighting.
  - **Menu hand-off fixed:** coming back from the menu, it puts back the real time of day and your Shadows setting (the menu used to restore a stale snapshot).
  - Crimson **Nightmare Nights** come later as a school event.
- **One shared effects toolbox** (`Controllers.Fx`, with a server `NHFx` event):
  - bursts, rings, light pulses, flashes, shakes, veils and UI pops
  - all of them follow the Camera Shake, Reduce Motion, Reduce Flashing and Effects Quality settings
  - Soccer, the tier-up cutscene and the main menu's shake, FOV kick, Surge flash and lightning now go through it, so Camera Shake 0% means no shake anywhere and Reduce Flashing calms the menu lightning
- **PBR school surfaces:**
  - new seamless 1024² materials: worn linoleum tiles, floorboards, varnished desk wood, chipped painted metal, layered slate
  - classroom floors, desks and metal now catch the light, and walls use Roblox's plaster
  - the change is fully reversible
- **Modelled school props** (Blender, baked PBR, in the gothic school style):
  - gothic iron-frame **student desks** (48)
  - oak **teacher desks** with crimson leather tops (6)
  - a carved **chalkboard** in every classroom (6)
  - crimson enamel **lockers** with arched panels, a quatrefoil vent, strap hinges, a padlock and a real interior (8 hallway, 2 hiding)
  - Each old block stays underneath, invisible, so gameplay, prompts and hiding spots are unchanged.
- **Lockers open and close:**
  - Hiding lockers swing open and shut when someone hides or leaves.
  - Locker 113 opens when you search it, and its quest note swings with the door.
  - The other hallway lockers have an Open/Close prompt.
  - Every player sees the same doors.

### Fixed
- **EXP bar position:** it sat one top-bar height too high, over the health bar's top rail. It's now just under the bar.

### Verified (Studio playtest)
- **Night:**
  - **Hand-off:** at 23:17 the grade took over after the menu, the sun matched the school time and Shadows stayed on.
  - **Brightness:** the first night grade was too dark (dark outfits became silhouettes), so it was brightened and checked again.
- **Surfaces:**
  - **Floor tiles:** a close-up shows the tiles, grout and speckle.
  - **Desks and archive:** varnished desks and the candlelit archive render correctly.
- **Props:** a classroom with desks, teacher desk and chalkboard renders correctly.
- **Lockers:**
  - **Hiding locker:** a hide-and-leave opened the door to 105° in 0.45 s and closed it again, both times. Measured on the client.
- **EXP strip:** it measures at y 535–548, under the bar and above the hotbar.

### Not yet
- **Not verified live:** the toolbox's own effects aren't used by a new effect yet, and the routed shakes were checked by code review.
- **Prop textures:** being re-baked with edge wear, crevice dirt and new leather, brass, stone, iron and paper materials.
- **Batch 2 is modelled and waiting to be imported:** chairs (student, teacher, armchair, sofa), trash can, candelabra, a rattling vending machine, a carved altar with its reredos, and a bookshelf whose books fall.

## [UI 1.13] - 2026-10-30: Lesson juice, rarity reveals, a dialogue box that slides in

### Added
- **Lesson juice** (VFX bible P2-11): class activities now sound and feel like something.
  - **Sounds:**
    - A chalk tap on every board button.
    - A bell ping for a right answer, pitched higher with each step of a streak or combo.
    - A dull thump for a wrong one.
    - In Lab Mix: PERFECT, GOOD and SLIP each have their own sound.
  - **✓ / ✗ glyphs:** a glyph pops off the answer you picked, with a puff of chalk dust, so right and wrong are never colour-only.
  - **The grade stamp slams onto the result sheet** (1.6× → 1×) with a stamp sound and a spatter of red ink. A grades get a gold shimmer across the letter; an F gets crossed out with two red scribbles.
  - **BOOM:** when the Lab Mix beaker goes off, there's a quick flash (softer with Reduce Flashing) and a cloud of green smoke.
  - **Timer pulse:** in the last 10 seconds the lesson timer turns red and pulses each second, ticking for the last 5.
- **Rarity reveal** (P2-14, the UI kit's part): a shared `RarityReveal` with one tier per rarity.
  - **Common:** a glint.
  - **Uncommon:** adds a soft flash.
  - **Rare:** adds a ring burst in the rarity colour.
  - **Epic:** two rings and a chime.
  - **Legendary / Cursed:** a "Surge" with a double glow pulse, three rings and the stamp sound, after the near-miss spin.
  - Spin reels play it when the result entry carries a `rarity`. The world burst for Legendary/Cursed is the quest session's part.
- **Dialogue slides in:** the dialogue box rises into place and fades in when a conversation starts, and slides down and fades when it ends. A soft glow in the speaker's colour runs along its top edge and brightens when a new character speaks.
- Everything here follows Reduce Motion (fades only) and Reduce Flashing.

### Fixed
- **Fading panels back in:** the kit's FadeIn now returns every element to how it was built, even after a FadeOut. Before, a panel faded out and then back in would have stayed invisible.

### Verified (Studio playtest, using the test bridge)
- A Chemistry Lab Mix lesson was started for real.
- The F stamp slammed in with ink spatter and both scribbles.
- The BOOM fired: a flash and 7 green smoke puffs.
- No errors from the lesson, kit or dialogue code.
- **Checked by code review only:**
  - The ✓/✗ glyph bursts, because every Lab Mix run ended at once, before any note could be hit. That's the quest session's area.
  - The timer pulse.
  - The dialogue slide-in, because Play was stopped from outside before I reached it.
  - The rarity tiers on a live reel; the reel's near-miss was tested in UI 1.12.

## [UI 1.12] - 2026-10-30: Milestone toasts, prompt sounds and refusals, the near-miss reel

### Added
- **Milestone notifications** (VFX bible P1-7): a gold notification for the big moments: level-up, quest complete, faction join or rank, purchases.
  - The wax seal stamps in (1.6× → 1×, with a stamp sound) and one gold shimmer runs across the title.
  - It stays up 6 s.
  - Server code sends it with `Kind = "Milestone"` on the existing notification packet.
- **Every notification now has an entrance:** it fades in and settles into place. When a fifth one pushes the oldest out, the oldest fades instead of vanishing.
- **Prompt sounds:**
  - A typewriter-key click when you start holding a prompt.
  - A small desk-bell ping when it goes through.
  - All UI sounds follow the Effects volume.
- **Refused prompts:** when the server turns an action down, the prompt says so. The key cap flashes red and the gold fill drains, the cap gives a small shake, the action line reads "✗ <reason>" (for example "✗ Locked until 3 PM") for a moment, and a knob-jiggle sound plays.
  - Only the player who was refused sees it.
  - Server code: set the prompt attribute `NHRejected` to `"<UserId>|<reason>|<anything unique>"`.
  - Client code: call `PromptUi.Reject(prompt, reason)`.
- **Near-miss spin** (VFX bible P2-14 / P3): when a spin reel lands on a Legendary or Cursed result, it slows as if it will stop one short, hangs a beat, then clicks over onto the result with a small overshoot.
  - Callers mark the result entry with `rarity = "Legendary"` / `"Cursed"`, or `nearMiss = true`.
- **Reduce Motion is respected throughout:** no stamp, shimmer, shake or near-miss, just fades.

### Verified (Studio playtest)
- All four new sounds load in the game.
- Milestone notification: the stamp sound plays, the seal settles, and the shimmer runs. A normal notification fades in and settles.
- Refused prompt: "✗ Locked until 3 PM" shows, then the prompt goes back to "Open locker" after 1.6 s.
- Reel: a Legendary result stops one short, hangs about 0.6 s, overshoots and settles exactly on the result. A Common result lands normally.
- **Fixed during testing:** the sound helper referenced a service before the kit declared it, which would have thrown an error from every prompt.
- **Not shown in screenshots:** the prompt's billboard. This Studio screen capture doesn't draw billboards at all (a plain test billboard didn't show either), so the refusal was checked from the prompt's actual text, colours and sound.

## [UI 1.11] - 2026-10-30: A proper Yen purse on the HUD

### Changed
- **The Yen display is redesigned.** It used to be a tiny bare box floating above the health bar's right end, partly covered by the bar's end ornament. It's now a framed plate just past the bar's right end ornament, centred on the bar, mirroring the posture meter on the left.
  - It shows a gold coin, made from the HUD's orb art with a ¥ stamp, and the amount in the gold title font.
  - It stays clear of the hotbar (at any slot count), the bar's end ornament and the EXP strip under the bar.

### Added
- **Yen changes you can see** (VFX bible P2-15): when you earn or spend Yen, the amount counts up or down to the new total, the coin gives a small pulse, and a "+¥N" (green) or "−¥N" (red) chip floats up off the plate and fades.
  - Loading your profile or swapping save slots just sets the number, with no chip.
  - Reduce Motion keeps the chip but drops the rise and the pulse.

### Fixed
- Swapping save slots now updates the Yen shown. A full profile load used to leave the old slot's amount up until the next Yen change.

### Verified (Studio playtest, 1400×683 and 1684×683)
- The plate sits beside the bar, centred on it, with nothing overlapping.
- These Yen changes were fed in through a temporary Studio-only test hook, since removed:
  - First load shows 407 with no chip.
  - A real change counts 407 → 532 with a "+¥125" chip.
  - A profile load jumps silently to 9,000.
  - A silent update in the middle of a count wins and settles on 407.
  - With Reduce Motion, "−¥50" shows without the rise or the coin pulse.

## [VFX 1.0] - 2026-10-30: Noncombat VFX revamp begins (audit, design bible, first fixes)

### Added
- **The VFX design bible and audit** (`docs/VFX-Design-Bible.md`, `docs/VFX-Audit.md`).
  - The audit is a code review of 177 noncombat scripts plus the world inventory.
  - The bible sets the style (the candlelit Institution vs the Blood), the palette and what each colour means, effect tiers and budgets, accessibility rules and the effect architecture.
  - It also holds a P0–P4 catalog and roadmap.
  - Running, movement and combat VFX are out of scope.
- **Owner-only objects** (`Controllers.World.OwnedObjects`): the server tags an object for one player, and every other client hides it, including its lights and prompts. "Exclusive" prompts work for one player at a time.

### Fixed
- **Wraith tier-up flicker:** the body now flickers and comes back, instead of sticking about 60% see-through until the end.
- **EXP bar on level-up:** it fills to the end, stamps the new level and refills from empty. It used to slide backwards.
- **Entering school keeps your field of view:** the menu no longer forces 70.
- **Dropped quest items and detention trash are visible only to their owner.** Other players used to see glowing boxes and "Pick up · Trash" prompts that did nothing for them.
- **Lockers:**
  - Respawning while hidden no longer leaves a locker stuck on "Leave · Occupied".
  - Only the person hiding sees "Leave".
- **Soccer goal rings** now burst upright out of the goal mouth, sized to the goal. They used to lie flat inside the goal box.
- **From the UI-kit session (UI 1.10):**
  - long story toasts wrap instead of being cut off
  - a lesson cancelled during the countdown no longer flashes its board
  - new **Reduce Motion**, **Reduce Flashing** and **High-quality Effects** settings

### Verified (Studio playtest)
- **FOV:** with FOV saved at 85, entering school through the real CONTINUE flow kept the camera at 85. The setting was put back to 70 afterwards.
- **EXP bar:** a display-only level-up (IV→V) climbed to the end, switched numerals and refilled to 15%, never moving backwards.
- **Wraith flicker:** in a display-only Wraith Tier III cutscene, transparency moved between 0.25 and 0.60 from 3 to 8.5 s, then returned to 0.
- **Owner-only objects:** with two tagged test boxes, the other player's box, light and prompt were hidden on screen and my own stayed. An exclusive prompt turned off when held by someone else and on when held by me.
- **Locker:** hid in the Records Office locker, respawned while hidden, and the prompt read "Hide · Locker" again.
- **Goal rings:** a server goal effect drew three rings at the west goal mouth with a horizontal axis (upright).
- No new script errors.

### Not yet
- **Not seen:**
  - The goal rings' new look wasn't caught in a screenshot (verified by measurement only).
  - The real dropped-item and detention paths were code-reviewed; the hiding module was tested with tagged test boxes.
  - Two-player checks are still to do.
- **Next batches:**
  - the shared effects toolbox
  - the day/night grade (blue-violet nights)
  - the school bell
  - the "Spotted!" hall-monitor alert
  - quest and clue moments
  - level-up, respawn and purchase feedback
  - **Nightmare Nights** (crimson nights as a school event) comes last.

## [UI 1.10] - 2026-10-30: Comfort settings, readable story toasts, clean lesson cancels (VFX revamp, part 1)

### Added
- **Comfort and effects settings** (VFX bible P1-2):
  - **Reduce Motion** and **Reduce Flashing**, in a new Camera > Comfort section.
  - **High-quality Effects**, under Graphics.
  - They're saved to your profile, and the game's effects read them from the player attributes `NHReducedMotion`, `NHReducedFlash` and `NHFxQuality` ("High" or "Low").
  - **Starting values:** until you change them, Reduce Motion follows your device's reduced-motion setting where Roblox provides one, and High-quality Effects follows your Roblox graphics level (levels 1-3 start on Low).

### Fixed
- **Story text no longer cut off** (P0-1): notification bodies used to be one line ending in "…", hiding chapter endings, case insights, "Case breakthrough", "Your blood stirs", "Turned" and the stealth checkpoint text.
  - Long text now wraps and the notification grows to fit, up to about 5 lines, then ends in "…".
  - Short notifications look exactly as before.
- **A cancelled lesson no longer flashes its board** (P0-13): if a lesson was cancelled during the 3-2-1 countdown, the board and timer still appeared over "Lesson cancelled" about 0.65 s later. The countdown now stops, and a board built at that moment is thrown away.
- **The lesson board shake** now follows Settings > Camera Shake (0% turns it off), and Reduce Motion halves it.

### Verified (Studio playtest)
- The three new player attributes are set at load. Toggling Reduce Motion in the menu sets `NHReducedMotion` and saves it, and toggling it back works too.
- The Comfort section and High-quality Effects show in the Settings menu.
- Notifications:
  - A 4-line story notification shows all its text.
  - A very long one stops at about 5 lines with "…".
  - A short one is still the 54 px single line, and a title-only one is unchanged.
- **Checked by code review only:** the lesson-cancel fix. It needs a real lesson cancelled mid-countdown.

## [Races 1.3] - 2026-10-30: A race spin starts you over at Tier I

### Changed
- **A race spin now resets your tier, the same as the bite.** You start at Tier I with hunger 0 and your race looks cleared; your traits and spins are kept. Tiers are earned through each race's own rites, so a new race starts from the beginning. Before this, a Tier III Vampire who spun into a Wraith stayed Tier III without doing a single Wraith rite.
- **A variant spin is unchanged:** it keeps your race, tier and hunger.
- **The Bloodline tab says so** before you spin: "A race spin ... starts you over at Tier I (hunger and race looks reset); a variant spin keeps your race and tier."
- **Old saves can't jump back up:** a spin also marks the record as already migrated, so the old kill-count tier can never lift a freshly reset tier.

### Verified (Studio playtest, spare slot II)
- **Race spin:** slot II was set to a Tier III Vampire with hunger 30 and Pointed ears, then spun through the real spin remote as the player. It became a Werewolf (Bloodmoon) at Tier I, with hunger 0, no looks and the same traits. The character's `Race` and `RaceTier` updated live.
- **Variant spin:** at Tier II with hunger 12, it kept Tier II and hunger 12.
- **Afterwards:** slot II was restored exactly to its earlier state, and the console showed no script errors.

## [UI 1.9.3] - 2026-10-30: Looks are saved by name, and catalog hair stays on in menus

### Changed
- **Saved looks use fixed IDs, not list positions:** before, a look was saved as "eyes option 5" or "top 18". Adding, removing or reordering options would silently change everyone's saved look. Now each choice is saved by a fixed ID ("doe" eyes, "red-vest", skin "#D8B492").
  - Every eye shape, brow, mouth, top, bottom, skin tone, hair style, hair colour and eye colour has an ID that never changes. New options get new IDs, and existing IDs are never changed or reused.
  - **Existing saves convert automatically** the first time each save slot loads.
  - A save slot that hasn't converted yet is read through a frozen copy of today's list order. It stays correct even after the lists change, and nobody has to log in first.

### Fixed
- **Catalog hair fell off on the client:** the main menu's student copies (and any other copy built on the client) lost their catalog hair within about 2 s; it dropped out of the world.
  - The cached hair kept a dead weld from the temporary model Roblox builds to load it, and on the client `AddAccessory` doesn't build a new one.
  - Now the old weld is stripped when the hair is cached, and the hair is welded to the matching head attachment whenever no weld was made.

### Verified (Studio playtest)
- Your slot 1 save was converted live, and is now stored by ID (leather-jacket, ripped-jeans, calm, arched, frown, ...). Slot 3, not loaded since, is still in the old format and reads correctly.
- A look sent by ID from the client is applied by the server (the mouth changed), and the original look was restored exactly.
- 12 of 12 checks in Edit pass:
  - Old saves read as before.
  - Converting a look to IDs and back gives the identical look.
  - Bad values fall back to the defaults.
  - After a simulated reorder (Gym shirt moved to the front), both an old-format save and a new-format save still show the Gym shirt.
- Pal Hair on a copy built on the client stays welded to the head (0.19 studs up, steady for 3 s), with the painted face showing. Server-side hair still welds normally.

## [Menu 1.2] - 2026-10-30: Character customization and main menu audit

The whole customization path was audited end to end: the main menu, save slots, the Wardrobe, names and clans, and the Bloodline tab. The method was a code review of every module, then live tests in Play with real keys and clicks. The Wardrobe and appearance fixes are in [UI 1.9.2]; this entry covers the rest.

### Fixed
- **A slow name check could undo purchases and the enrolment lock.** Setting your first name waits on Roblox's text filter, then saved a copy of your record taken before the wait.
  - A spin purchase that landed during the wait was wiped.
  - Entering school during the wait unlocked your name again, so you could rename for free.
  - Now the record is re-read after the filter, the lock is re-checked, and only the name changes. A save-slot switch during the wait is refused.
- **Menu keys worked behind Settings.** With Settings open from the main menu, W/S moved the hidden menu and Enter could trigger CONTINUE and send you into school. Menu keys now do nothing while Settings is open.
- **Posed students in the menu were bald.** Catalog hair on the menu's client-side copies kept a weld to the model it was built from, so it fell out of the world within about 2 seconds. Accessories on menu copies are now re-welded to the body.
- **Posed students ignored race.** The menu copies had no race, so Vampire and Ghoul skin and uniforms showed wrong on the plinths. Each copy now carries its slot's race.
- **The Bloodline tab used the wrong camera shot.** It asked for a shot named `Bloodline` but the config called it `Lineage`, so it fell back to the body shot. It now gets the low heroic angle.
- **Dead buttons on a network error.** If picking a slot or entering school errored, every slot button stayed dead or the screen stayed black. Both calls are now protected, and the slot list retries up to 5 times instead of showing no cards.
- **Repeated hooks:** each failed ENTER SCHOOL added another Wardrobe camera hook. Now there is one per menu visit.
- **Bloodline tab showed old data** right after a spin or look change, because it redrew from the profile copy before that had updated. It keeps the server's answer for 3 seconds.
- **"Last played" saved outside the save rules.** It was written straight into the profile. It now goes through `UpdateState` (new `SetLastPlayed` action) and is in the `PlayerData` schema.
- **Gamepad:** the right stick turns your student in the creator, and the creator's Look button gets selection focus when you arrive on a gamepad.

### Checked and fine
- No client path can set race, tier, spins or name changes.
- Slot numbers are validated on the server (whole numbers 1 to 3 only).
- ENTER SCHOOL needs a loaded slot and a name, checked on the server.

### Verified (Studio playtest)
- **Wardrobe:** all four tabs open. A Face change updates the live head strips and the preview together and saves to the profile; the original look was put back afterwards. The preview skin colour matches the live character.
- **Main menu, real keys and clicks:** loading screen → intro → menu.
  - With Settings open, S, S, Enter left the menu untouched, and after closing Settings the menu keys worked again.
  - PLAY → slot cards with real data → slot I → creator → Bloodline (new camera shot) → ENTER SCHOOL. The HUD came back and "last played" saved.
- **Plinth students:** all four copies keep their accessories (the hero and slot I wear their catalog hair), each with its slot's race.
- Every changed script compiles; the console showed no script errors.

### Not yet
- **Decided:** a race spin now resets you to Tier I, like the bite. See [Races 1.3].
- **Not tested live:**
  - the name-filter race (code review only)
  - the Bloodline refresh after a spin (spinning would have re-rolled the test character's Legendary bloodline)
  - gamepad and phone
- **Left as is:**
  - The menu hints show keyboard keys on every device.
  - The loading screen's "continue" is mouse/touch only; it is optional, since the screen finishes on its own.
  - Hiding other players on the menu scans their characters 15 times a second.

## [UI 1.9.2] - 2026-10-30: Customization audit fixes (look, hair, Wardrobe saving)

### Fixed
- **Faces vanished on non-classic heads:** on mesh or avatar heads, the painted face is drawn with decals. The avatar-face guard hid those decals on the second apply at spawn, leaving those players faceless. The guard now skips our five face layers and still hides a late avatar face.
- **Doubled hair and crosses at spawn:** the two applies at spawn could overlap while a catalog hair loaded, wearing two hairs and two look folders.
  - The hair lookup now happens before anything on the character changes.
  - A newer apply makes an older, still-waiting one give up.
  - All old copies are cleared, not just the first.
- **Bald after a hair-lookup hiccup:** a brief Roblox catalog error used to save Hair ID 0 and hide your other hair.
  - Your other hair now stays unless the catalog hair actually goes on.
  - A saved Hair ID is cleared only when the ID definitely isn't a hair.
- **Hair-lookup spam:**
  - Failed lookups are cached for 30 s.
  - The hair cache is capped.
  - Each player gets one new uncached lookup every 1.5 s.
  - Re-sending an unchanged look no longer saves or rebuilds.
- **Wardrobe could overwrite your saved look with defaults:**
  - Edits are blocked ("Loading your look...") until your saved look has loaded.
  - After a save-slot swap, the Wardrobe re-reads the new slot's look before any edit can save.
  - A queued save is dropped when the profile changes.
  - A save sends a copy of the look as it was when you clicked.
- **Colour wheel:** after a drag, the swatch highlight and the "Custom colour #" note now update.
- **Stashed avatar clothes and hair** are also cleaned up when a character is removed or a player leaves, not only when the character is destroyed.

### Verified (Studio playtest, test copies of a character)
- Mesh-part head: after two applies, the iris, main, brows and mouth all stay visible, and a late avatar face decal is still hidden.
- Two overlapping applies with an uncached hair (Lavender Updo): the older one is dropped, leaving exactly 1 hair and 1 look folder.
- A hair ID that fails to load keeps the built hair (5 parts) and isn't marked "not a hair".
- Stash folders are removed on cleanup.
- The Wardrobe opens with the saved look, and the console shows no script errors.
- **Checked by code review only:** the save-slot swap gap in the Wardrobe, and the colour-wheel redraw.

### Not yet
- Looks are still saved as list positions (eyes, brows, mouth, uniform, bottoms), so reordering a list would change saved looks. Moving to stable ids needs a one-time migration.

## [Sports 1.1] - 2026-10-30: Soccer and the Grave Rovers

### Added
- **Soccer on the west pitch**, built to play close to the Blue Lock-style reference place you supplied (only the mechanics were studied; no code, characters or assets copied).
  - **Shooting:** hold and release click. A 0.36 s charge gives full power, aimed with the camera; at full power, A or D curves the ball late.
  - **On the ball:** **R** passes to the teammate you aim at, **Q** is a dribble burst that breaks a tackler's ankles, and **right-click** feints.
  - **Without the ball:** **E** tackles (a miss leaves you stunned), and **click** volleys or heads the next ball.
  - **Keepers:** from 3v3, keeper pads give a keeper with a long reach, a dive (Q) and a throw (click) in their box.
  - **Bloodrush (T):** a meter fed by steals, ankle breaks and goals. It gives a burst of shot power and speed with an aura in your race's colour.
  - **Match flow:** the ball stays in play (ball-only walls). First to 10, a 5-goal lead, or the most goals at time, with golden-goal overtime.
  - **After a goal:** a goal flare, the scorer's close-up and a celebration, then kickoff to the team that conceded.
- **Drills** on the new practice ground south of the pitch: **Target Practice** (lit corner targets) and **Wall Passes** (first-time passing off a rebound wall).
- **Grave Rovers Tryout** from Coach Mallory, who now coaches for real.
- **Our Blender balls in play:** the basketball, soccer ball and football models are imported with their PBR textures and used as the ball look.
- **Animations from the group library** (no combat clips, no movement clips except the slide):
  - "SLIDING" for tackles
  - "Activate" for keeper throws
  - "Isagi Celebration" after goals
  - Procedural poses for everything else
- **Phone and gamepad buttons** for soccer, in kit art.

### Fixed
- **The ball sat inside the player's body:** possession dropped the hold offset. Basketballs now sit in the hand and soccer balls at the feet.
- **Models and seams far from the ball:** they were welded before the ball moved to its spawn point.
- **Fast balls skipped sensors:** a fast ball could pass through a goal or target sensor between checks. Sensors now test the ball's whole path.
- **Leftover feedback text:** "Perfect Release" and "Clean pass!" left a faint outline on screen after fading.
- **Stamina did nothing:** running out now stops sprinting, in basketball and soccer.

### Audit (end to end)
- **How it was audited:** a code review of every soccer module, then live tests in Play.
- **Fixed:**
  - Invalid "straight up" aims that could fake a target hit or a goal.
  - **Teleport cheating:** players move their own characters, so the server now checks movement speed; a teleporter loses the ball and can't act for 1.5 s, and shots from inside a goal mouth or off the pitch are refused.
  - A tackler who won a loose ball still got the miss stun.
  - Tackle and dribble timers carried over a goal or halftime.
  - A tying goal at the buzzer triggered two kickoffs.
  - Target Practice didn't feed the ball back after a hit.
  - The dead-ball timer during volleys.
  - The keeper volleyed instead of catching.
  - The kick charge could be spammed.
  - A stun restored sprint speed.
  - A stale kick charge carried over between games.
  - Curve for gamepad and touch.
  - "Out of gas" showed to everyone.
  - Intercepted passes counted as assists.
  - Looping animation clips kept playing after the move.

### Verified (Studio playtest)
- **Shots and Bloodrush:** goals, curve (about 10 studs each way), kickoff after a goal, two goals filling Bloodrush to 50 and T spending it (crimson aura).
- **Drills:** Target Practice 4/4 and Wall Passes 4/4.
- **Real keys:** Q dribble and E tackle. The slide plays once, E doesn't equip a weapon in a game, and a missed tackle stuns.
- **Goal celebration** clip.
- **Ball model** at the feet.
- **Tests:** 81 pure checks, including the path sensor and invalid aims.

### Not yet
- **Two players:** tackles, steals, feints and ankle breaks need at least two players; keepers need 3v3.
- **Missing clips:** your group has no non-combat kick, pass, dribble, dive or header clips, so those stay procedural poses.
- **The training cone model:** not imported, so the gym cones are still cylinders.

## [UI 1.9.1] - 2026-10-30: Class waypoint survives respawning

### Fixed
- **Class / detention waypoint:** respawning (e.g. after a sports match or a death) made the clock HUD throw "Label is not a valid member of BillboardGui 'ClassWaypoint'" every half second, and the marker never came back.
  - Respawning wipes reset-on-spawn GUIs, and the marker was one of them. The script kept using the wiped copy.
  - The marker now survives respawns, and it's rebuilt if it ever goes missing anyway.
  - Verified in Play: after a respawn, the "Detention · Room 106" marker stays up, its distance keeps updating, and the console stays clean.

## [Sports 1.0] - 2026-10-30: Sports clubs and basketball

### Added
- **Clubs:** Night Ravens (basketball, Coach Varga), Grave Rovers (soccer, Coach Mallory) and Iron Wardens (football, Coach Dunmore).
  - Join, switch or quit through the coach. Ranks run Rookie → Starter → Varsity → Captain, and Captain earns a title.
  - Members keep a win/loss record from ranked club games (12:00–20:00 in-game).
  - Club tags show in the Students list.
- **Venues:** a gothic stone gymnasium south of the school, with:
  - a full court, bleachers, hanging lamps and a scoreboard
  - a practice end with a hoop, Shootaround spots and a cone course
  - Next to it: a walled soccer pitch and a floodlit football field, all with compass markers.
- **Basketball, Highschool Hoops style:** games from 1v1 to 5v5, joined from the team pads.
  - **E** hold/release shot with a kit meter and Perfect/Early/Late feedback.
  - **Q R F C** dribble moves that chain and cancel, **Z** euro step, **G** post up.
  - **Click** passes where you aim. On defence, click steals and jumping blocks.
  - **Rules:**
    - contested shots, layups and dunks, threes, and stamina
    - a 24 s shot clock, check ball, half court with clearing for 1v1 and 2v2
    - halftime, overtime and buzzer-beaters
  - Race perks apply in games.
  - Getting downed, leaving or walking off for 5 s takes you out.
  - **Rewards:** Sport EXP, yen and popularity; club EXP and record for ranked games; a post-game card with MVP and your line.
- **Drills:** Shootaround (10 spots, 60 s) and Cone Dribble (weave six cones with moves). Best scores are saved.
- **Night Ravens Tryout:** a quest from Coach Varga: pass the Shootaround, then play a full game.
- **Blender models:** a basketball, soccer ball, football and training cone with baked PBR maps (`art/sports`).
  - They load as the ball look once you import the FBX files. Until then the balls are plain spheres.
- **Phone and gamepad controls:** kit-art buttons for Shoot, Pass/Steal, Move and Euro.

### Changed
- While you carry a ball, the combat keys (click, Q, R, F, E, Dodge, Block) step aside, and you can't slide or crouch in a game.

### Audit (end to end)
- **How it was audited:**
  - A code review of every sports module.
  - Studio checks: installed code matches its source, and the venue setup and patches are complete.
  - Live tests in Play.
- **Fixed:**
  - "Holding a ball" stuck after a game or drill ended (it blocked steals and blocks).
  - A client-reported perfect shot timing (timing is now measured only on the server).
  - Block spam.
  - Offensive-rebound shot clock and clearing.
  - Post-up without a defender.
  - Bystanders blocking ball pickups, and a ball stuck in the bleachers.
  - Four reward farms: check-ball touches, forfeits, drill repeats, cone teleporting.
  - The venue HUD overwriting the drill HUD.
  - A client dash that ignored the server and stamina.
  - Made shots falling through the floor.
  - Respawning mid-game.
  - Empty games that never ended.
  - Buzzer-beaters that didn't count.
  - Several smaller edge cases.

### Verified (Studio playtest)
- **Real keys:** E shot with the meter, Q crossover and Z euro step (the dash comes after server approval).
- **Through the test bridge:**
  - joining through Coach Varga
  - both drills: bests saved, club EXP, the 3-minute reward cooldown, the teleport run rejected
  - a full solo-test game: 2s and 3s, check ball, shot clock, halftime, a buzzer-beater counted, a ranked record, MVP, rewards, tryout completed
  - removal on a knockout and on walking off the court
  - 205 junk and spammed remote calls with no errors
  - 60 pure checks

### Verified (two-player local server test, 2026-10-30)
- **The queue:** both pads filled, a 10 s countdown ran, and a half-court 1v1 went live (Crimson ball).
- **Steals:** a reach during a crossover failed and showed **"Crossed up!"** on the defender's screen. A steal on a standing ball handler worked; possession and the shot clock flipped.
- **Half-court clear:** a shot inside the arc right after a steal was refused. After clearing past the arc it went up and scored 2, and check ball went to the other team.
- **Blocks:** with a jump at the release, 3 of 4 shots were blocked (a 60% roll), and the fourth went in. Without a jump, perfect-timed shots stayed green.
- **Defender pressure:** at the same release timing (about 0.67 s), 3/3 open shots were green and 3/3 shots with a defender a stud away were okay (1 made).
- **Offensive rebounds:** the shot clock went from 11.4 back up to 14, with no clear needed.
- **Passing:** a 1v1 pass with no teammate keeps the ball. A real pass needs a 2v2.
- **Game to 21:** both players were paid: +12 yen for the win, +8 yen for playing.
- **Forfeit:** the opponent walked off, was removed after 5 s, and the game ended "Forfeit" for Crimson. The 3-minute reward cooldown held.
- **The bite (Races 1.2), with real T presses and real clicks:**
  - A Tier II Vampire gripped a downed Human, and T opened the accept / fight-off card.
  - **Accept** turned the Human into a Tier I Vampire; the grip ended and the biter's hunger rose.
  - A second bite the same day was refused with a reason.
  - The next night, **Fight it off** kept the victim Human.
- **Console:** no sports or bite errors.

### Not yet
- **Passing in a real game:** needs a 2v2 (four players).
- **Soccer and football:** their rules are Sports 1.1 and 1.2.
- **Imported models:** the Blender models are waiting on File → Import 3D.

## [Races 1.2] - 2026-10-30: Evolve your bloodline: hunger, rites, tier-up cutscenes and the bite

### Added
- **Hunger:** every race fills its own meter (Vampire *Blood*, Werewolf *the Hunt*, Ghoul *Feeding*, Wraith *Souls*, Human *Resolve*, Priest *Faith*).
  - It fills from kills and grip finishes, weighted by race: vampires and werewolves feed best at night (werewolves most of all under a full moon), ghouls from finishing, and priests also from attending class.
  - The meter shows in the Bloodline tab.
- **Rites:** 25 hunger opens the Tier II rite and 100 opens Tier III. There are 12 short night quests, one per race and tier:
  - Vampire: *The Font Below*, *The Blood Ledger*
  - Werewolf: *First Hunt* (full moon), *The Ring at Moonrise*
  - Ghoul: *Grave-eater*, *Charnel Feast*
  - Wraith: *Shroud*, *Dirge* (both stealth)
  - Human: *The Hunter's Mark*, *Slayer's Oath*
  - Priest: *Exorcism*, *Sainthood*
  - 13 new rite objects (a stone font, a blood ledger, a cracked bell, votive candles and more) are placed in the Archive, Boiler Yard, Staff Room, Records Office and Duel Ring.
- **Tier-up cutscenes:** finishing a rite plays about 10 s of choreography made just for that race.
  - Authored camera shots, procedural body poses, race effects and colour grading, a letterbox, and a gold title card.
  - It waits until you're safe; you're frozen and can't be hurt while it plays, and it's skippable after the first time.
  - Players nearby see the pose and effects.
- **The bite:** a Tier II+ monster gripping a downed Human or Priest can press **T** to offer the turn; the victim has 15 s to accept or fight it off.
  - One turn per biter per in-game day; never in duels; werewolves only bite at night.
- **Earned tiers:** tiers now come from rites, not kill counts. Existing saves keep the tier they already had.

### Fixed
- **Tail sway:** tails are now actually posed every frame. The pose used to be written after physics, so the next frame's animation overwrote it before it rendered.

### Verified (Studio playtest)
- Hunger rose to 30 and *The Font Below* opened by itself.
- **The rite, played for real:** at night, walking into the Archive cleared step 1, and holding E at the font finished the quest. The student evolved to **Night Gentry**, the cutscene played, and they were unfrozen afterwards.
- **Cutscenes:** Vampire, Werewolf, Ghoul and Priest were checked in frames. Measured on the Priest: the body knelt (dropping about 1 stud), then rose with arms raised and head back.
- **Cutscene polish from testing:** the HUD hides during a cutscene, and the camera stays in front of walls in small rooms.
- **Pure checks:** 160 pass, including that every rite's objects and areas exist in the map.

### Not yet
- **The bite:** two players are needed, so it's only code-reviewed.
- **Not yet played through:** the other 11 rites, the Wraith and Human cutscenes, and the Tier III effects.

## [Races 1.1] - 2026-10-30: Race looks: ears, tails, grave wear and cold wisps

### Added
- **Race cosmetics modelled in Blender** on the game's R6 proportions, with PBR textures (colour, normal, roughness, and metalness on the silver Moon pieces):
  - **Vampire ears:** Pointed and Swept (Tier I), Long Swept (II), Elder (III). They take the player's skin tone.
  - **Werewolf ears:** Upright and Tufted (I), Torn (II), Moon-marked (III).
  - **Werewolf tails:** Brush, Bushy and Bobbed (I), Shaggy (II), Moon-marked (III). Six fur colours tint the ears and tail; the Moon pieces are charcoal and silver.
  - **Ghoul:** stitched jaw wrap and chest strap (II), and a tattered grave shroud (III).
  - **Wraith:** a faint cold breath every few seconds and thin cold wisps from the shoulders and hands, half as visible by day. Wisp colours at Tier II, frost-tipped fingers at Tier III.
- **Animated tails:** each tail has a 7-bone rig. Tails sway gently at rest, swing out when you turn or strafe, lift when you run and bounce when you land. This runs on each player's own screen only.
- **Looks picker** in the Bloodline tab. The server checks every choice against your race and tier; locked options show the tier they unlock at. Saved per student.
- **Ghoul school uniform:** a Ghoul wearing the school uniform gets a torn, re-stitched, grave-stained version of the same uniform (clothing and UI-kit sessions).

### Fixed
- **Floating ears and faces:** this game's bodies are scaled to 0.9, so every piece now scales with the real body. The vampire ears press against the head, and the painted face wraps the head's true curve (UI-kit session). Nothing clips into the body.

### Verified (Studio playtest)
- Vampire, Werewolf, Ghoul and Wraith looks attached and seated, checked from several angles.
- Picking looks saves and re-dresses the character; a locked choice falls back to a Tier I look.
- A tail swayed at rest (tip up to about 5 degrees) and lifted while sprinting (the lift direction was also checked on the rig).
- Wraith wisps showed at night.

### Not yet
- The darker ghoul shroud and strap colours haven't been seen in a playtest yet (uploaded after the last test).
- Two-player checks; how the looks behave during transformations.

## [UI 1.9] - 2026-10-30: Wardrobe preview never cuts your character off, faces sit flush, ghoul uniforms

### Added
- **Ghoul school uniforms:** Ghouls in school uniform now wear torn, grave-stained versions of it, drawn by the clothing session. Skin shows through the tears.
  - Red Vest, Red Shirt, Black Vest and Black Shirt each swap for their ghoul version.
  - The standard uniform trousers swap for ghoul jeans. If you picked other bottoms, you keep them.
  - Other tops, avatar mode, and the full-transformation outfit are unchanged. A race change re-dresses you straight away.

### Fixed
- **Wardrobe preview camera:** your character is now framed head to feet, centred, with a margin, at every window size.
  - Before, the shot was taken once, often while your character was still loading, and then kept. The head ended up jammed under the TURN AROUND bar with empty space below.
  - The camera is now worked out from your character's real height, its turn-around width, the preview's shape and the camera's field of view. It's redone on every outfit change and every resize.
  - Sheathed weapons (the katana on your back) and held tools no longer count toward the shot, so they don't shrink your character. Hair, accessories and future ears and tails still count.
- **Creator layout:** in the main-menu creator, the Wardrobe panel now sits between the menu's letterbox bars, so its Done button can't hide under the bottom bar. This matches the Register panel.
- **Faces sit on the head:** the painted face (eyes, brows, mouth, veins) floated about 0.02 studs off the cheeks.
  - The cause was the face shell using half the head's width as its radius. The classic head's visible curve is 0.48 of its width (0.54 studs on this game's 0.9-scale heads).
  - The strips now sit on that curve, and the art is sized to the head's visible width, so it wraps the same angle as before.
  - Each flat strip is placed so its edges, not its centre, touch the curve, so no strip edge pokes out. Old faces rebuild automatically.
  - In a grazing close-up along the cheek, only the 0.006-stud anti-flicker gap now shows past the head outline. That's well under a pixel at normal camera distances, and nothing flickers.

### Verified (Studio playtest)
- School Wardrobe (K) at 1287x600 and 1571x600: centred head to feet, steady through the turn-around spin.
- Ghoul uniforms, on a test copy of a character:
  - All 4 uniform tops, plus the trousers, switch to the ghoul versions.
  - Jeans are kept, and the Navy Vest is unchanged.
  - A Human gets the normal uniform, and avatar mode is unchanged.
  - The ghoul Black Vest renders correctly in game.
- **Not yet checked live:** the creator layout. It mirrors the Register panel's fit, which was already verified.

## [Races 1.0] - 2026-10-30: Six bloodlines, race passives, the Bloodline tab, and crouching

### Added
- **Three new races:** **Werewolf, Ghoul and Wraith** join Human, Priest and Vampire.
  - Still rolled by the server and never picked. Odds: Human 40%, Priest 25%, Vampire 15%, Werewolf 10%, Ghoul 6%, Wraith 4%.
  - Each new race has three sub-races (Bloodmoon/Alpha, Ghast/Crypt Lord, Revenant/Hollow King) and three tier titles.
- **Race passives, balanced:** every race has strengths that grow with its tier, plus one drawback.
  - Rarer sub-races boost the strengths (x1.15 / x1.3), never the drawback.
  - Night favours monsters and day favours mortals. Priests hit the undead harder, Human Slayers hit all monsters harder, and every 4th night is a full moon for werewolves.
- **Bloodline tab** (creator: Look / Bloodline / Name & Clan / Spin Shop; in school, from the Student Record):
  - the race crest and tier title, and the race and variant spins with odds
  - the passive and its drawback, and what Tier II and III give
  - your traits
- **Skin palettes:** Vampires get pale or dark tones only, and Ghouls a ghoul-only palette (clamped by the UI-kit session, in both outfit modes).
- **Crouching:** hold **Left Ctrl** to crouch and crouch-walk, with your two new animations and a small camera dip.
  - Crouching halves how fast stealth watchers notice you.
  - Ctrl while sprinting slides (Slide moved from C).

### Changed
- **No duplicate tabs:** the Wardrobe's Lineage tab is removed (Look / Face / Hair / Outfit). In the creator, the Register panel hides its own tab strip, since the menu buttons pick the tab.
- **Fits the screen:** the docked Register panel now sits between the menu's letterbox bars instead of running under the bottom one.
- **Student Record:** shows "Vampire · Tier I, Fledgling", the race passive and its drawback.
- **Low-health regeneration** now reads "heal N HP/s when badly hurt".

### Fixed
- **Doubled hooks:** a leftover copy of the Progression module made every progression hook run twice (double EXP and double heals). It's removed.

### Verified (Studio playtest)
- **Damage multipliers (with Might 2):**

  | Case | Multiplier |
  |---|---|
  | Vampire by day | 0.98 |
  | Vampire at night | 1.09 |
  | Alpha Werewolf on a normal night | 1.095 |
  | Alpha Werewolf on a full-moon night | 1.1275 |
  | Priest hitting a Vampire | x1.06 |

  The Werewolf's max health was 115.
- **Heals:** a Ghoul execution healed exactly 6%, and a Vampire kill 4%.
- **Bloodline tab:** spins and renders in the creator and in school.
- **Crouch:**
  - Hold, walk and release work, and the speed is restored.
  - Sprint + Ctrl slides, and a jump stands you up.
- **Pure checks:** 87 pass.

### Not yet
- Race cosmetics modelled in Blender (Phase 2).
- Hunger, rites, the tier-up cutscene and the turning bite (Phase 3).
- Two-player checks, and crouch on phones and gamepads.

## [UI 1.8] - 2026-10-30: Readable on every screen (UI audit pass)

### Changed
- **Bigger UI on laptops:** the kit's auto-scale shrinks more gently below full HD (scale^0.6), so 1280x720 gets 0.78 instead of 0.67 and 1366x768 gets 0.82. Text that rendered at 10-11 px on laptops is now readable.
- **Bigger text everywhere:** small text 15 -> 18, body 18 -> 20, headers 23, titles 28. Hard-coded sizes in the Wardrobe, Settings, HUD (yen), clock, dialogue, prompts and the factions panel were raised to at least 18 design px.
- **Panels fit short screens:** a new `FitToScreen` keeps the Wardrobe and Settings panels inside the window (their contents scroll) instead of overflowing on short windows and landscape phones.
- **Consistent scaling:** Notifications and the Factions panel now scale like the rest of the kit, so the Factions [P] button matches the buttons under it.
- **Tidier edges:** the clock panel moved in so its shadow stays on screen, and the yen counter sits clear of the EXP strip.
- **Lineage tab:** each trait now shows its effect, for example "+10% EXP at night", and marks planned ones "(planned)", using Progression's descriptions.
- **Race tier rises mid-session:** Lineage re-checks kills every 15 s, so a new tier no longer waits for the next load.
- **Race skin palettes:** Vampire and Ghoul skin always lands on its bloodline's tones (Vampire: pale or deathly dark; Ghoul: grey-green and bruised).
  - It applies in the uniform and in your own Roblox outfit, where the avatar's skin shifts to the nearest tone.
  - The Wardrobe shows only those tones.
  - Your saved choice is kept, so a race change (for example Vampire to Human) gives your own skin back.
  - Roblox's avatar loader can no longer undo the uniform or palette skin after spawning.
- **Transformations follow the race:** a transformed character wears its race's outfit (with matching eyes and mouth): Vampire, Werewolf, Ghoul, Wraith or Priest. Humans keep their clothes. `Transformation` can be a form name, a race or sub-race, or simply `true` (uses the rolled race). `Appearance.FormOf(character)` resolves it.
- **No duplicate Settings button:** on keyboard devices the left-edge Settings button is hidden, since the top bar's Menu button opens Settings, and the Wardrobe button moves up into its place.

### Verified
- Play test at 1287x600: the HUD, Wardrobe, Settings and Factions panel all fit and read clearly. The Wardrobe footer shows the student's name.

## [UI Audit 1.0] - 2026-10-30: Every screen checked for legibility, layering and scaling

### Fixed
- **EXP strip drawing over panels:** the strip sat on a layer above Factions, the Journal and Settings, so its line cut across them. It's now on the HUD's own layer, under every panel.
- **Small text** on laptops (the UI scales to about two-thirds on a 720p screen):
  - EXP level numeral and gain
  - Student Record rows (and the Grit text running into its **+** button)
  - Students list sub-lines
  - compass intercardinals
  - Name & Clan notes, odds, clan tag and pity line
  - Spin Shop labels and badges
  - the loading screen stamp
- **Faint text (2.9:1 contrast):**
  - Name & Clan and Spin Shop notes
  - the main menu key hint, version line, "Drag to turn your student" and the SLOT I/II/III labels
- **Daylight:** the compass and top bar read navy blue over a bright sky. Their backings are darker now.
- **Students list:** a scrollbar appeared with a single student. The list height now counts its padding.

### Reported to the UI kit (not changed here)
- **Scaling:** the kit's linear scaling makes 15–17px text render at 10–11px on laptops. A gentler curve or a text floor was suggested.
- **Small text:** Wardrobe, Settings, Journal, quest tracker, clock and hotbar labels.
- **Edges:** shadows run past the right edge.
- **Consistency:**
  - Notifications aren't scaled.
  - The Factions button is twice the size of its neighbours.
  - The left button stack repeats the top bar.
- **Phones:** panels overflow phones in landscape.

See [docs/UI-Audit.md](docs/UI-Audit.md).

- **Quest Tracker:** moved in to line up with the clock (x = −30), so its shadow stays on screen.
- **Quest Tracker and bigger kit text:** with the kit's new sizes (small 18, body 20), the "[J] Journal" footer overflowed its 16px row onto the card border, and the objective box only fit two lines. The card is now 140 tall (was 112), the objective box 64 (was 52, room for three lines) and the footer/timer 20. Checked in Play: no overlap, and a long objective needs 40 of 64.
- **Quest Journal:** checked against the bigger text. Text rows size themselves, tab and quest rows fit, and the longest deduction answer (19 characters) fits its 230px button. Nothing to change.

### Verified (Studio playtest)
- **Menu labels:** light and 18px.
- **Clan tag:** reads "COMMON CLAN" with its space.
- **Panels:** the EXP strip stays under the Factions panel.
- **Compass:** dark in daylight.
- **Students list:** no stray scrollbar.
- **Record:** the Grit text wraps clear of its button.

### Not tested
- Real phones, gamepad navigation, dialogue, activities, the downed screen and the duel HUD.

## [Progression 1.0] - 2026-10-30: Levels, stats, real perks and traits

### Added
- **EXP and levels (1 to 50).** EXP comes from:
  - class: attending, passing lessons
  - quests
  - combat: duels, the Ring champion, executions
  - factions: joining, new ranks
  - introductions, and slipping away from hall monitors

  Everything is **1.2× in school hours**, as the concept doc says. Level-ups give 3 stat points, a notification and an ember burst.
- **Stats:** **Might** (+damage), **Grit** (+max health, slower guard strain) and **Wits** (+class and quest EXP, harder to spot). Spend points in the **Student Record** (**L**, or the new book button on the top bar).
- **Clan perks and lineage traits now do things:**
  - **Active:** damage dealt/taken, max health, guard strain, stealth, EXP by kind, school-hours and night EXP, night power, low-health healing, and Fated's daily get-back-up.
  - **Planned:** walk speed, parry, prices, popularity and clue sense. These say "(planned)" until their systems exist.
  - Clan perk texts are generated from the real effects.
- **EXP strip:** a subtle hairline under the health bar.
  - Clock ticks, gold warming to crimson with an ember tip, and the level as a Roman numeral.
  - The knob glows when points are waiting. It rests faint and wakes when you earn EXP.
- **Levels on show:** students you know show "Lv N" on their nameplate and in the Students list.

### Fixed
- **CONTINUE swallowing keys:** on a student who'd never saved a look, CONTINUE played the new-student reveal in the background, and its hidden name box then kept the keyboard in school. CONTINUE now skips the reveal, the register only takes focus while visible, and the menu waits longer for the signed flag on slow loads.
- **L key:** the record key is read even though the game's keybind package marks every key as handled.

### Verified (Studio playtest)
- **Level-ups:** 500 quest EXP became 525 with the Harlow perk, Level 1 to 4, saved across a restart.
- **Real EXP source:** a grip execution gave +20 EXP.
- **Spending:** **+** by key raised Might (damage ×1.03, so a 10-damage hit dealt 10.30) and Grit (max health 102).
- **UI:** the record opens with L and the top bar. The EXP strip wakes on gain.
- **Not yet:** a live play-through of every EXP source, Fated, regeneration, and two players.

## [Social 1.0] - 2026-10-30: Strangers, Students list, compass, shift-lock cursor

### Added
- **Stranger system:** you only see a student's name once you've learned it.
  - **Known students:** their full name shows over their head, with the clan in its rarity colour and their faction's seal.
  - **Everyone else:** a faint *Stranger*, only up close.
  - **Learning names:** walk up and press **G** to introduce yourself. They get a notification with your name. Members of the same faction also know each other.
  - **Saving:** who you know is saved per student (`PlayerData.Known`).
- **Students list** (replaces Roblox's player list):
  - Grouped by faction: The Vigil, The Crimson Court, Unaffiliated.
  - Closed by default. Open it with **Tab** or the top bar's Students button.
  - Built from the UI kit's player rows. Strangers show as *Stranger*.
- **Compass** across the top centre:
  - Shows N, E, S, W, plus markers for classrooms, faction bases, the duel ring and quest NPCs.
  - Your tracked quest objective is always shown, pinned to the edge when behind you, and whatever you face is named with its distance.
  - Places come from map attributes, and the builder can tag more with `Compass = "Label"`.
- **Shift-lock cursor:** a dark wrought-iron ring with gold hour ticks, spear-point finials and a crimson diamond (44 px).

### Changed
- **Names are private.** They're no longer on public player attributes or Roblox's name tag. The server sends each player only the names they know. The public `Signed` flag replaces `FirstName`, `RPName`, `Clan` and `ClanRarity`.
- **E stays free for Equip** near other players: introductions use G, and Equip only gives way to prompts that use E.
- **Duel messages** no longer show account names. After a duel, both fighters must step off the pads before a rematch countdown can start.
- **Notifications** now appear just below the compass.

### Fixed
- Nameplates were missing when a character spawned, because its head arrives a moment later.
- Tab didn't open the Students list, because Roblox marks Tab as already handled.
- The Students list text was too dark: its background gradient was tinting the text.
- Roblox's player list came back after leaving the main menu.
- The compass overlapped the top bar on narrow windows.
- Other players' characters overlapped yours on the main-menu editing stage. They're now hidden on your screen while you're in the menu.
- **Changelog:** the Menu 1.0 and Menu 1.1 entries had been lost when the file was rewritten from an older copy. They're restored below.

### Verified (two-player Studio test)
- **Joining:** both players got their own loading screen and menu, and picked saves at the same time with separate data.
- **Names and clans:** simultaneous clan spins and name signing worked, then both entered school.
- **Privacy and introductions:** names stay private, and the introduction prompt works by key press, with a notification and a coloured nameplate.
- **New UI:** the Students list, compass and shift-lock cursor work.
- **Combat:** PvP hits landed. **V** carry, **B** grip with the kill saved, then a respawn.
- **Duels and leaving:** a duel ran on the pads, and leaving worked without errors.
- **Second run:** every fix was re-checked on fresh code in a new session: E equips and G introduces next to a stranger, there's no duel rematch while standing on the pads, and known names persisted across sessions, per student.
- **Not yet:** chat between players and discipline reports.

## [Menu 1.1] - 2026-10-30: Names and clans, Spin Shop, loading screen, top bar

### Added
- **Full names:** every student is now `<first name> <clan>`, for example *Mara Ravenscar*.
  - The first name is typed in the **register** (Name & Clan tab). It's checked by Roblox's text filter, and only letters are allowed: 3 to 14, with a space, ' or - between them.
  - It's free to change until you enter school. After that you need a Name Change.
  - It shows over your head, in the editing-screen header, and on the slot cards.
- **Clans** (family names), **rolled by the server** and never chosen. There are 28 original clans in 6 rarities:
  - Common 52%, Uncommon 26%, Rare 13%, Epic 6%, Legendary 2.5%, Cursed 0.5%.
  - **Pity:** Epic or better is guaranteed after 40 spins in a row without one.
  - **Spins:** a free first roll plus 3 clan spins.
  - Each clan has a lore line and a perk (data only for now).
  - **The reel:** it lands on the server's result, and rare clans flare the ring in their colour and lean the camera in.
- **Spin Shop (Robux):** clan spins (1 / 5 / 15), race spins (3 / 10), variant spins (3), trait spins (5) and a Name Change.
  - `Services.Player.Purchases` is the game's only receipt handler, and it never grants a receipt twice.
  - **Not on sale yet:** the Developer Product ids have to be created on the Creator Dashboard and pasted into `Config.Shop`.
- **Editing-screen sections:** **Look** (the Wardrobe), **Name & Clan** and **Spin Shop**, each with its own camera move. A new student meets their clan first.
- **Loading screen** (ReplicatedFirst), styled as your admission file:
  - A blackletter title card, with typewritten file details and notes.
  - Behind it, the **real courtyard**, filmed by a slow camera glide.
  - An **asset counter**: "RECORDS RECEIVED done / total", percent, and time left, on a hairline crimson progress rule.
  - A crimson **ADMITTED** stamp when everything has arrived.
- **Custom top bar:** Roblox's top bar is switched off. In its place, one slim ink-and-gold plate with **Menu** (Settings), **Chat** (with an unread pip) and **Students** (player list). It fades back when you're not using it.
- **West grounds** for the menu scene (the side the cameras look across, which looked empty):
  - A West Hall and four more dead oaks.
  - The wall and iron fence carry on along that side.
  - Two rows of forest silhouettes and 48 more lit town windows.
  - A proper chapel spire.

### Changed
- **Ring VFX:** new soft-filament tendril texture. It tiles along the beam and fades out at both sides. The tendrils also fade in from the core.
  - The crystal-shard sprites now fade out before their flipbook cell edges. **No more cut-off lines.**
- The distant forest and hills are now night silhouettes.
- Pressing ENTER SCHOOL without a first name now makes the register obvious: the field pulses, the placeholder reads "Write your first name here", and the cursor is in the box.

### Fixed
- **The old tendril texture was mapped the wrong way round.** Roblox Beams run the image's vertical axis along the beam, which caused the hard edges.
- The identity update event was named `Changed`, which clashed with Roblox's built-in `.Changed`, so purchases errored after granting. It's now `Updated`.
- The editing-screen header showed a new clan before the reel landed.
- The loading counter reported meshes as failed, because they were preloaded as id strings. It now preloads through each asset's instance.

### Verified (Studio)
- **Name rules:** good names title-cased, bad names refused.
- **Odds over 10,000 rolls:** matched the config. The longest run without Epic or better was 39, so pity works.
- **Receipts:** a repeated receipt changed nothing. Clan, race and name-change grants land in the save.
- **Real clicks and keys:** reveal, spin, Spin Shop and the top-bar buttons.
- **Loading screen:** 385 to 418 assets per run, 1 failed (the place has no permission for one sound).

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
- **Higher-quality uniform variants:** all 14 variant tops and 7 bottoms now use the clothing session's upgraded art (smooth edges, shading, shadows, creases). Saved choices carry over, since they're stored by position, not by ID.
- **Civilian clothes** (clothing session):
  - **Tops:** Blood Moon Hoodie, Leather Jacket, Open Flannel, Victorian Waistcoat, Hussar Coat and "The Hollow" Band Tee.
  - **Bottoms:** Cargo + Boots, Black Jeans + Boots, Striped Joggers, Pinstripes + Riding Boots, and Black Skirt + Fishnets.
  - That makes 24 tops and 13 bottoms in all.
- **Transformation outfits:** setting the `Transformation` attribute (Vampire, Wolf, Ghoul, Wraith, or the new clothing-only Priest) dresses the form's outfit automatically.
  - If you're in your Roblox outfit, only the shirt and pants swap; accessories and hair stay.
  - Clearing the attribute puts your look back.
- **Spin shop hooks:** `Lineage.GrantSpins(player, kind, amount)` (server) for purchases. The Lineage tab gets a "Get more spins" button once the Identity shop exists.

### Changed
- The posture meter now sits beside the health bar. It used to collide with the menu buttons on wide screens.
- Notifications sit at y = 72, below the top-centre compass (previously moved at runtime by the compass).
- The Wardrobe preview says "Enrolled as <your student's name>" (Identity, private to you), or "a new student" before you sign. It used to show the Roblox display name.

### Fixed
- **Save slots** (the main menu): Settings and the Wardrobe now re-read the profile when a slot loads, so saved settings come back after picking a slot. Shadows-off persisted across a rejoin in the live test.
- **Avatar clothes drawing over the uniform** after a save-slot spawn: Roblox could finish loading the avatar after the look was applied. The look is now re-applied on `CharacterAppearanceLoaded`, and late avatar clothing, accessories, BodyColors and face are tucked away while the uniform or painted face is on. If Roblox's avatar loader takes the uniform off, it's put straight back, so there's no moment without clothes. Switching back to your own outfit still restores everything. Found and verified in Play by the quest session.
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
