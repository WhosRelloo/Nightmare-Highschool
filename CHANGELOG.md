# Changelog: Nightmare Highschool

All notable changes to the NH Combat Test dev place. The newest entries come first.

## [1.12.0] - 2026-11-02: The phone, the timetable, and two bug fixes

### Added
- **The phone.** Every student spawns with a **Phone** in their hotbar, built from the owner's model (`ServerStorage.NHPhoneModel`) with the crest glowing on its screen.
  - **Opening it:** equip it, or press **Y**, and you raise it in front of your face; everyone sees the pose. The server turns the right shoulder and a solved grip stands the phone upright, screen to the face, back and lenses out.
  - **The screen:** slides up at the bottom-right, laid out like a modern smartphone (owner's reference) but dressed for the school:
    - a rounded iron body with a polished-gold edge and side buttons, and the kit's PBR slate grain;
    - a notch with a lens and a status bar with the school clock;
    - a 4-wide grid of rounded enamel app icons (the kit's glyph art pressed into a slot well);
    - page dots, a frosted dock, and red badges (money received, a new paper each day).
  - **Labels:** outlined and shadowed so they read on every wallpaper.
  - **Input:** it never captures input, so combat and movement keep working with it up.
  - **Apps:**

    | App | Where | What it does |
    |---|---|---|
    | **Wallet** | dock | Send Yen to a classmate (pick, type, confirm): 1 to 5,000 at a time, 5 s apart, never from the menu or while downed. Both sides get a toast and a history line. |
    | **Night FM** | dock | Play any public Roblox audio ID, only you hear it: title lookup, play/pause, stop, loop, volume, progress and recent IDs. It keeps playing with the phone away, and the hotbar slot shows a note. |
    | **Classmates** | dock | Everyone in the building, with names only if you know them. Send Yen or invite them to your study group. |
    | **Camera** | dock | The cinematic view. |
    | **The Midnight Bell** | grid | The school paper, written live: the moon tonight, the top students in the building (names only if you know them), the discipline report, the stand's special, club notices and a rumour column. |
    | **Timetable** | grid | Opens the timetable. |
    | **Study Group** | grid | Opens the study group drawer. |
    | **Factions** | grid | Opens the factions panel. |
    | **Style** | grid | Eight preset wallpapers (Crimson Ink, Violet Night, Blood Moon, Vigil Candle, Court Velvet, Grave Fog, Midnight Blue, Ash), or your own image or decal ID. Saved, and only you see it. |
    | **Options** | grid | Opens Options. |

    Per the owner, there's no Report Card, Locker or Journal in the phone.
  - **Saved:** `PlayerData.Phone` (history, recent IDs, wallpaper), with the `SetPhone` action. Y is reserved in the key settings.
  - **Files:** `Services.Features.Phone`, `Controllers.Gui.Phone` (new).
- **The timetable.** Click the clock at the top-right (`Controllers.Gui.Timetable`, new).
  - **The day:** every segment from Before School to Night, with times, subjects and rooms.
  - **Now:** the current segment lit gold with a progress bar, a "Now / Next class" line, and earlier segments dimmed.
  - **Your attendance:** today's result on each class you've had, with the lesson grade.
  - **Detention:** any detention you owe.

### Fixed
- **Top bar never faded back.** Since 1.10 the Study Group button overwrote the bar's fade container (`Ui.Group`), so every fade and wake tween errored ("Unable to cast value to Object", found with a startup error probe). The button now has its own field (`Gui.TopBar`).
- **Combat movers errored on clients** that hadn't loaded a character yet (streamed out or mid-respawn): "LinearVelocity:31 attempt to index nil with 'LinearStore'". The client replay now skips characters it can't register (`Functions.LinearVelocity`, a two-line guard; combat behaviour unchanged).
- **Phone text boxes** (Night FM ID, Wallet amount, Style image) passed gsub's match count into `tonumber` as a base and errored. They now read digits through one helper.
- **Backups:** `ServerStorage.NH_Backup.Keys_pre` (`Phone_original`, `LinearVelocity`, `Settings`).

### Verified
**[PT]** on save slot II:
- **The tool:** the phone arrives in the backpack on spawn. Equipping it opens the screen, and the pose and grip were checked from the front.
- **Layout check:** every screen (home, Wallet, Night FM, Midnight Bell, Classmates, Style) passed an automated check for cut-off text (`TextFits`), elements outside the screen, and overlaps.
- **Night FM:** played an ID and showed its real title.
- **Style:** applied and saved Violet Night.
- **Midnight Bell:** rendered live data.
- **Wallet:** refuses sending to yourself or to anyone absent.
- **Top bar:** no startup errors left after the fix.
- **Restored:** slot II's phone data was reset after testing.

### Not tested yet
- A real two-player Wallet transfer, and Classmates with other students in it.

## [1.11.0] - 2026-11-02: New menu keys, the study group dock, a cinematic view, and a camera audit

### Changed
- **Menu keys remapped.** Every menu key now sits on the right side of the keyboard, away from combat and movement.

  | Key | Opens | Notes |
  |---|---|---|
  | ` | Locker | was G, which clashed with "Introduce yourself" and the sports Post key |
  | P | Options | was M |
  | M | Report Card | was L |
  | L | Factions | was P |
  | J | Journal | unchanged |
  | U | Study Group | unchanged |
  | Tab | Students | unchanged |
  | \\ | Cinematic view | new |

  - **Reserved keys:** all of them, plus G (Introduce yourself), are reserved, so no combat rebind can take them.
  - **Labels:** the settings key list, top-bar tooltips and panel buttons ("Factions [L]", "Options [P]") are updated.
  - **Files:** `UI.Settings` (ReservedKeys, FixedKeys), `Gui.{SettingsMenu,FactionsPanel,Progress,Locker,StatsPanel,TopBar}`.
- **The study group moved to a dock in the bottom-left corner** (`Gui.StudyGroup` rebuilt).
  - **Rows:** one slim row per groupmate: a race-coloured edge, name and level, a hairline health bar (the kit's veined fill) with a gold posture thread, and distance.
  - **States:** rows dim when a member is too far for the shared EXP, show DOWN when they're downed, and flash when they're hit. A gold "+10% EXP" chip lights when anyone is near.
  - **Resting:** the dock rests faint and wakes on hover or a hit. Alone, it's one faint "Study Group U" chip.
  - **Drawer (U or the chip):** invite, remove (leader) and leave. Invites slide in above the dock.

### Added
- **Cinematic view (\\, or the top bar's film button)** (`Gui.Cinematic`, new).
  - **Hides:** every ScreenGui, every world name tag, Roblox's chat, player list and emote menu, and the mouse.
  - **Adds:** black letterbox bars that slide in, each with a gold rule and the kit's diamond knob; an ink vignette; a light filmic grade (contrast up, colour down, a gentle far blur); and a title card ("C I N E M A T I C" with the crest) with a "\\ return" hint that fades away.
  - **Restoring:** anything that tries to show itself while the view is on is held back, then restored when you leave.
  - **Limits:** not available in the main menu.
- **`Functions.CameraLease`** (new): one owner for the scripted camera.
  - **How it works:** the barber and wardrobe stations, the locker hide, tier-up cutscenes and the goal cam take a lease instead of setting CameraType and FieldOfView themselves.
  - **Handing back:** when the last lease ends, the normal camera returns at your Settings field of view. A lease whose owner stopped caring ends by itself. Respawning ends all leases. When a newer lease ends, the older one gets its shot back.

### Fixed (camera audit)
- **Hiding in a locker showed a black screen.** The camera was placed inside the locker door, because the head's ray can't hit the door's parts. It now finds the locker prop and sits just outside the door, looking out through the slats (`World.LockerPOV`). It also can't run in the main menu, where it used to take over the menu's camera.
- **The barber camera.** It framed you from the front, but the barber stands there, so it ended up inside him (a faded dark blob) with you badly framed.
  - **Now:** a three-quarter profile from the more open side, with the barber faded just for you while his book is open.
  - **Light:** a soft warm key light on you (only you see it) at the barber and wardrobes, so hair and clothes read at night (`Gui.Wardrobe`).
- **Cameras could get stuck or keep a station's zoom** when two camera moments overlapped. Fixed by the lease in `Gui.Wardrobe`, `Gui.Evolution`, `Gui.Soccer` (goal cam) and `World.LockerPOV`.
- **The follow camera made a new Tween every frame** to track the torso. It now eases there directly (`Gui.Camera`).
- **The Locker inventory's character preview** left an empty strip and cut off your feet. It now frames you head to toe.
- **The pouch showed snacks you'd run out of.**
- **Cinematic view:** leaving it now restores every interface. Roblox delivers property signals late, so the view now counts its own switch-offs instead of mistaking them for requests.
- **Backups:** `ServerStorage.NH_Backup.{Keys_pre,Cameras_pre}`.

### Docs
- Discord posts are split by channel: `updates/discord/game-updates/` (every release) and `updates/discord/announcements/` (big waves only), with an index in `updates/discord/README.md`. The first announcement is **The Living School** (1.10 to 1.11).

### Verified
**[PT]** on save slot II:
- **Locker hide:** the camera sits outside the door (inside nothing), with the room visible through the slats. Leaving gives back a Custom camera at your FOV.
- **Barber:** a lit three-quarter hair shot with the barber faded. Hiding in a locker while the barber panel was still open stacked and unstacked the leases cleanly.
- **Cinematic:** nothing visible while it's on (20 world name tags hidden too). After leaving, every interface is back exactly as it was, and the mouse is back.
- **Study group dock:** shown with a group state sent from the server: live health, distance, "away" rows and the +10% chip.
- **Locker preview:** head to toe.
- **Keys:** checked in code and the settings list. Studio's test tools can't press keys in the game.
- **Restored:** slot II's discipline went back to Detention, 8 points, 1 owed. Moving the test clock had run a day's decay.

## [1.10.0] - 2026-11-02: The Locker, the concession stand, study groups, the Report Card, and a school that keeps its own timetable

### Added
- **NPC daily schedules.** 14 background students now live by the timetable (`Services.Features.Schedules`). They keep the same faces all day.
  - **Night and early morning:** off campus.
  - **Before school:** they walk in from the gate and mill about the hallway.
  - **Class periods:** six of them take seats in that period's room, which leaves chairs free for players. The rest are "in the east wing".
  - **Passing and break:** the hallway, walking, chatting and leaning on the wall.
  - **Lunch:** the concession stand. Six queue at the counter and the rest eat in a loose arc in front of it.
  - **After school:** each student has a club (gym, field, pitch or archive). A third go home from 14:00.
  - **Evening:** they drift home, and everyone is gone by 19:00.
  - **How they move:** PathfindingService, sized for the 8-stud doorways. If there's no path they stay put rather than walk through walls.
  - **Players:** the students never collide with players (collision group `NHWalkers`).
  - **Animations:** Roblox's default R6 walk and idle, and the owner's sitting, leaning and eating clips.
- **The concession stand.** Mrs. Okada's snack kiosk sits just outside the west end of the main hallway (`Services.Features.Concession`, compass "Concession Stand").
  - **Build:** a striped awning, a CONCESSIONS sign, a menu board, snacks on the counter and two lanterns.
  - **Menu:** hold E at the counter to open it, then Buy 1 or Buy 5.
  - **Snacks** (`Config.Items`):
    - **Food heals over a few seconds**, half as much while you're combat-tagged, and shares a 12 s "full" cooldown: Onigiri ¥25, Melon Bread ¥40, Yakisoba Bun ¥80, Night Bento ¥200.
    - **Drinks give one snack buff at a time:** Ramune (guard), Barley Tea (stealth), Canned Coffee (class and quest EXP), Red Lantern (damage and health).
    - **Balance:** every buff stays under one Common gear piece's budget.
- **The Locker (G, or the new top-bar button).** Your inventory, laid out like the owner's reference (`Controllers.Gui.Locker`).
  - **Left:** your character, with equipment slots around it: Head, Face and Neck gear, your Weapon class and your Snack buff. Under it, the Gear Scale adds up what your worn gear gives.
  - **Right:** the Backpack, with tabs All, Gear and Snacks. Each slot shows the item in 3D and has a hover tooltip.
    - **Snacks:** Use, To pouch or Unpin, Drop (with a confirm).
    - **Gear:** shows whether you're wearing it. You still change gear at a wardrobe.
  - **Pouch:** your four hotbar snacks.
  - **Hotbar:** pinned snacks are real Tools, so they sit on the existing hotbar. Equip one and click to eat or drink it.
  - **Save data:** `PlayerData.Inventory` and the `SetInventory` action.
- **Study groups (U, or the new top-bar button).** A party of up to four (`Services.Features.Party`, `Controllers.Gui.StudyGroup`).
  - **Inviting:** invite anyone in the server. You only see names you've learned (Strangers). The invite card has Accept, Decline and a 20 s fuse.
  - **The panel:** each member's race, level, live health and posture, a crown for the leader, and Remove for the leader.
  - **Shared EXP:** +10% EXP while a member is within 150 studs, and members nearby get a quarter of your combat EXP.
  - **Ending:** leaving, going back to the menu or leaving the server takes you out. A group of one breaks up.
- **The Report Card (L, or the Record button).** A new stats panel that replaces the old record (`Controllers.Gui.StatsPanel`).
  - **Report Card:** your name, race and tier, level and EXP, points to spend, and Might, Grit and Wits, each with what one point gives and a +1 button.
  - **Abilities:** everything adds up to max health, damage, toughness, guard, night and full-moon power, healing, stealth, and every EXP bonus.
  - **Record:** takedowns, attendance, discipline, and where every bonus comes from (clan, race passive and drawback, traits, gear, snack).
- **Top bar:** two new buttons, Locker [G] and Study Group [U]. The Record tooltip now reads "Report Card [L]". G, U, L and H are reserved in the keybind settings.

### Fixed
- **Gear chests lay on their side.** The imported chest mesh was Z-up, so every chest spawned lying on its back. The template was turned upright and the lock now faces the room, with the back against the nearest wall. The model's pivot was reset so placement keeps it upright, and the lid still hinges open from its back edge.
  - **Backup:** `ServerStorage.NH_Backup.Systems_pre.NHChestModel_preUpright`.

### Changed
- **Progression:** active snack buffs count as an effect source. Study group bonus and share are part of `Award`. The sheet carries `Record` (name, attendance, discipline, classes), plus `GearText` and `SnackText`.
- **Backups** of every patched module are in `ServerStorage.NH_Backup.Systems_pre`.

### Verified
**[PT]** on save slot II:
- **Inventory:**
  - Granted snacks show up in the hotbar with counts.
  - Ramune's buff appears on the sheet and in combat attributes, and a second sip is refused.
  - Melon Bread heals, and the "full" cooldown holds.
  - Buying from too far away is refused. Buying at the counter took ¥50 for two Onigiri.
- **Schedules:**
  - In a planned Period 1, 5 of 6 students were seated at R102's desks facing the chalkboard within 40 s; the sixth was still walking from a club.
  - In a planned lunch, 13 or 14 students were within 22 studs of the stand.
  - The evening plan sent the even-numbered students home.
- **Panels:**
  - The Locker, the stand menu, the Report Card and the Study Group panel render from kit pieces, with screenshots checked.
  - The Study Group's solo paths work: inviting yourself or someone absent is refused, an expired invite is refused, and leaving with no group does nothing.
- **Chests:** placed chests stand upright in Play, and the lid opens correctly.
- **Restored:** slot II's discipline (back to Detention, 8 points; earlier playtests had run into class time and logged 3 absences), Yen (¥180) and inventory (empty).

### Not tested yet
- A real two-player study group: invites, shared EXP, the live health bars of another member.
- A full in-game day of schedules on the live clock. Periods were planned through `Schedules.PlanForTests` so the clock didn't mark the test student absent.

## [1.9.3] - 2026-11-02: VFX Batch 5 (polish) and an anti-teleport check

### Added
- **Anti-teleport check (security #14 follow-up).**
  - **What it does:** four times a second the server compares each player's position with the last one. A sideways jump faster than 100 studs a second (plus 25 studs of lag slack) or a climb faster than 60 studs a second (plus 20) counts as a teleport. The player is put back where they were and the attribute `NHTeleportFlags` counts up. Nobody is kicked. Falling is never limited.
  - **What it lets through:** every move the game makes itself (entering school, admin bring and go-to, the veil, duels, sports set pieces, stealth thrown-out, the menu stage, respawn). Those are made by server scripts, and a server script setting a CFrame fires the root's changed signal on the server, which client physics never does. So none of those call sites needed changes.
  - **Also skipped:** admins (level 1+; the attribute `NHAntiTeleportTest` turns that off for testing), players in the main menu, seated or dead players, anchored roots, and roots the server owns (downed or gripped).
  - **Files:** `Services.Features.AntiTeleport` (new).
- **School polish (VFX P3).** In `Controllers.World.SchoolFx` (new):
  - **Seated chime:** when you take your seat in class, a soft desk bell plays and the clock HUD's "In class" line pops.
  - **Discipline record stamp:** when your record gets worse, the new level (WARNING, DETENTION, PROBATION, SUSPENSION) slams in under the clock in red ink with the Stamp sound. When it gets better, a gold "Record improved" banner shows.
  - **Night Study candle warmth:** while a Night Study lesson is up, the screen edges glow a flickering candle amber and the picture warms to sepia.
  - Nothing fires on join, only on changes. All of it follows the Reduced motion setting.

### Changed
- **Soft rings everywhere (VFX P3).** `Fx.Ring` now draws the kit's soft ring art on a decal instead of a hard Neon cylinder. This covers every effect that uses it (goals, shocks, swishes, seals). A new `Fx.SoftDisc` helper lays any soft decal flat or facing a direction.
- **Soccer landing marker:** a soft gold ring with a faint inner glow, instead of a flat Neon disc.
- **Basketball:** a swish now uses the game's own ember sprites (plus gold shards for a three) and soft rings through the net, instead of default sparkles. The dunk shock is a soft ring.
- **Sports result card reveal:** the card scales in. The winner's title takes their team colour. Rewards count up from zero. A drill personal best stamps in.
- **EXP gain tick:** the "+N" pops, and three gold sparks run along the new part of the EXP bar.
- **Strangers write-on:** when you learn someone's name, it writes itself on like ink (never on join).
- **Files:** `Controllers.Fx`, `Gui.Soccer`, `Gui.Sports`, `Gui.Progress`, `Gui.Strangers`. Backups are in `ServerStorage.NH_Backup.Batch5_pre`.

### Verified
**[PT]** on save slot II:
- **Anti-teleport:**
  - a 150-stud client teleport and a 120-stud fly-up were both caught and put back;
  - a server move of 80 studs, a 60 studs/s physics run for 1.5 s and a 120-stud fall were not flagged.
- **SchoolFx:**
  - the stamp shows PROBATION and cleans up, and the improved banner shows;
  - the seated pop fires (it waits for the HUD's next tick);
  - the Night Study tint and edges come on with a Night Study board and leave with it.
- **Toolbox and sports:**
  - flat and upright soft rings, which clean themselves up;
  - swish: two rings, ember and shard emitters; dunk shock ring;
  - the drill card scales from 0.82, counts the reward up to +40 and stamps PERSONAL BEST.
- **EXP tick:** the "+60" popped to 1.3, with three sparks.
- **Not tested live:** the Strangers write-on (it needs a second player) and the soccer marker during a real kick (it uses the same tested `SoftDisc`).

## [1.9.2] - 2026-11-02: Every NPC gets a real face and outfit

### Fixed
- **Quest characters and staff showed Roblox's default smile on a recoloured rig.**
  - **Who:** Bruno, Pip, Ezra, Vesper, Dex, Coaches Varga, Mallory and Dunmore, the Hall Monitor and the stealth watchers (Mr. Hale).
  - **Why:** they were only ever given a hair.
  - **Fix:** they now get a full look through the same appearance system as the students: face art (eyes, brows, mouth), skin, outfit and their catalog hair.
  - **Outfits:**
    - the Vigil and Crimson Court leaders wear their faction vests;
    - the coaches wear P.E. shirts or a varsity jacket;
    - Bruno, keeper of the ring, wears a leather jacket;
    - Dex, the courier, wears a flannel;
    - staff wear a blazer or cardigan.
  - **Kept:** the faction light.
  - **Files:** `Services.Features.NpcLooks` (new: `Apply` and `Specs`), used by `Social.Npcs`, `School.HallMonitor` and `Quests.Stealth`.

### Verified
**[PT]**
- **Coverage:** all 27 non-dummy NPCs have the face art, a shirt and hair.
- **Bruno up close:** game eyes, angry brows, a scowl, a leather jacket and his re-seated Fighter Crop.

## [1.9.1] - 2026-11-02: Customization cameras, Male/Female hair, enemies off campus, NPC hair fixed

### Changed
- **Customization cameras frame what you're editing, in the space the panels leave free.**
  - **The problem:** in the main-menu creator, the camera centred your student while the edit panel covered the right of the screen. The feet fell under the letterbox, and dragging to turn the student swung them away, because the orbit pivoted on the scene's origin.
  - **Creator shots:** each one is now built live from your student, keeping its angle and lens: the whole body for Look, Outfit, Bloodline, Name and Shop; the face for Face; the whole hairstyle for Hair.
  - **Placement:** the shot is centred in the free area between the left menu, the panel and the letterbox. It's framed again 0.75 s later, once the panel has slid into place.
  - **Orbit:** dragging turns the camera around your student.
  - **Wardrobe stations and the barber:** the panel docks on the right like the creator's, and the world camera frames you in the space beside it (your whole outfit at a wardrobe, your hair at the barber). It picks an angle nothing blocks, or fades whatever is in the way, just for you. Closing the panel or walking away gives your camera back.
  - **Files:** `ReplicatedStorage.Functions.FrameCamera` (new, shared), `Gui.MainMenu` (camera framing and orbit only; the menu's look is unchanged), `Gui.Wardrobe`.
- **Hair styles split by Male and Female.**
  - **Barber's book:** shows **Male** and **Female** sections, with your body type's first.
  - **Catalog:** each hair's `Group` now follows the owner's export folders (`Males_*` / `Females_*`), giving 15 Male and 20 Female. Ten male cuts were tagged "Any", so ambient NPCs (which match `Group` exactly) never wore them. They do now.
- **Delinquents and wolves moved away from the school.** Their spots are markers in `workspace.Map.NHHangouts`:
  - **Delinquent crews** hang out in the empty south-east lot, "The Back Lot" on the compass, instead of the Field, the Pitch and the Boiler Yard.
  - **Wolves** roam the west edge and the south-west corner at night instead of the Boiler Yard.
- **The barber** works out of the nook between the Records Office and the Boiler Yard, facing the hallway, instead of standing in the corridor in front of the lockers (`Features.AmbientNpcs`).

### Fixed
- **NPC hair sat in the wrong place on two catalog cuts.**
  - **Affected:** Fighter Crop and Fluffy Messy sat about 0.7 studs too low, hanging at the back of the neck or on the shoulders (Bruno Vance, Mr. Hale, some delinquents).
  - **Found by:** measuring every catalog hair's surface on a test head with rays. The other 33 were already right.
  - **Fix:** both are raised, and Fighter Crop is also brought forward, in the catalog itself, so players get the fix too. The originals are kept in `ServerStorage.NH_Backup.NHHairCatalog_preFit`.

### Verified
**[PT]**
- **Creator Body:** hair top at y 246 and feet at y 662, inside the free 85–726 band, centred at x ≈ 700 between the menu (355) and the panel (1054). Before, the feet were cut off at 696.
- **Creator Face and Hair:** each fills the free area. Name & Clan keeps its low angle.
- **Barber:** opens docked, with the camera on your hair and the barber faded or avoided.
- **Delinquents:** spawned at about (180, −175).
- **Wolves:** appeared at (−240, −233), (−224, −47) and (−215, −6).
- **Bruno's hair:** now at (0.00, 0.17, 0.11) on his head.
- **Barber:** at (158.6, 28), facing the hallway, with the prompt working.
- **Still open:** Bruno Vance still shows the default Roblox face (not the Nightmare High face art). That's a separate Social NPC appearance issue.

## [1.9.0] - 2026-11-02: VFX Batch 4 complete (case files, goals, Bloodrush)

### Added
- **Evidence string and SOLVED (P2-13)** in the Journal's Case Files.
  - **Strings:** each insight is a crimson thread with pins, joining its two clue cards down the board's left edge.
  - **New link:** a confirmed link draws its string in, and the insight text types out.
  - **Wrong pair:** both cards shake and flash red.
  - **Solving the case:** the journal darkens and a crimson SOLVED stamp slams in with the case name.
  - **Files:** `Investigation` sends NHFx `LinkHit` / `LinkMiss` / `Solved`, drawn by `Controllers.Gui.QuestJournal`.
- **Goal celebration (P2-5):**
  - an upright team-colour flare and light in the goal mouth, three net rings and shards off both posts;
  - the pitch lights pulse for a second;
  - spectators within 150 studs see it.
  - **GoalCam:** now re-entrant, and it eases back behind you instead of snapping.
- **Bloodrush revamp (P2-6).** The aura is drawn on every client from the `SportRush` attribute, so late joiners see it.
  - **Look:** race-colour embers and two wisp ribbons locked to the torso, with nothing trailing behind you. It flickers out over the last 1.5 s.
  - **Colours** now come from `Lineage`. The old `Config.Sports.RaceAura` disagreed with it.
  - **Server:** the default-texture sparkle emitter is no longer created.

### Fixed
- **Soccer effects ignored your settings.** The soccer client's effect handler was also called `Local.Fx`, which replaced the shared FX toolbox getter. Every soccer shake, flash and ring ignored your camera-shake and reduced-flashing settings and used a local fallback. The handler is now `Local.OnFx`.

### Verified
**[PT]**
- **Case files (slot II, solved case):** 3 threads and 6 pins drawn. The wrong pair shook both cards. The stamp slammed from 1.8 with a slight overshoot, the journal darkened to 45%, it held about 2 s, then faded.
- **Bloodrush:** the aura appeared, flickered in the last 1.5 s, then cleared.
- **Goal by the west goal:** flare, light, 3 rings, both post shards, and the pitch lights went 2.2 → 3.96 → 2.2.
- **Not tested in Play:** the GoalCam changes only run in a live match, so they were checked by code reading.

### Batch 4 status
- **Tested:** P2-1, P2-4, P2-5, P2-6, P2-7, P2-8, P2-9, P2-10, P2-12 and P2-13.
- **Done earlier (UI kit):** P2-11, P2-14 and P2-15.
- **Waiting on decision D5:** P2-2 and P2-3.

## [1.8.9] - 2026-11-02: Painted sigils, and no more prisoner idle

### Added
- **Sigil paint and scrub (VFX P2-9).**
  - **Paint:** a faction mark wipes onto the wall left to right over 1.2 s, and drips run down from it. The drips fade after a few seconds.
  - **Scrub:** the mark fades through grey over 2 s with soap suds.
  - **On join:** marks already up when you join just show.
  - **Files:** `Controllers.World.SigilFx`. The server state (`Services.Social.Pranks`) is unchanged.
  - **Still to add:** a spray-hiss sound, once a Creator Store sound is picked (D4).

### Changed
- **Players no longer play the prisoner idle in detention** (owner request). The loop that played it while you stood still in Room 106 is removed from `Controllers.Character.ContextAnims`. The ambient detention kid NPC keeps its pose.

### Verified
**[PT]**
- **Sigils:** TheAlley's sigil painted with 5 drips. On reset it went grey, faded over about 1.3 s, then handed back to the server's hidden state with its colour restored.
- **Detention:** standing still in Room 106 with a detention active, only the normal stance plays.
- **Test cleanup:** my locker test had added a Trespassing violation to the spare save slot II. It was removed and the points restored to 12.

## [1.8.8] - 2026-11-02: Arrivals, veils, lockers and fades (VFX Batch 4)

### Added
- **Enter-school arrival (P2-4).** When you leave the main menu for school, once the menu's own fade has cleared:
  - a gold clock seal stamps in at the centre of the screen and opens outward, with a soft bell;
  - a card names where you are (the nearest named place, classroom or faction base, else "School grounds") with the day and time.
  - The main menu itself is unchanged. `Controllers.World.Arrival`.
- **Teleport veil (P2-7).** Moving into the duel ring, and the admin panel's bring and go-to, now fade your screen to ink, puff violet smoke where you stood, move you under the veil, then puff smoke where you land.
  - **Server hops** (the Main Menu button, the server browser) show a crest card that says "Leaving school..." instead of Roblox's default screen.
  - **Files:** `Services.Features.Fx.VeilMove`, `Controllers.World.Veil`.
- **Locker hide (P2-10).**
  - **Hiding:** your camera moves to the locker door and looks out through vent slats, desaturated, with a slightly narrower FOV. Your race-look emitters pause.
  - **Others:** they see you fade out with a muffled clank, and fade back when you step out.
  - **Respawn:** a reset or death while hidden leaves nothing behind.
  - **Files:** `Controllers.World.LockerPOV`.
- **Presence fade (P2-12).** Stealth watchers coming on or off duty and talkable NPCs respawning fade in and out over 0.7 s, with a soft smoke puff, instead of popping. The server flags them with `Presence`, and on removal sets `Departing` and waits 0.8 s. `Controllers.World.Presence`.

### Verified
**[PT]**
- **Arrival:** the seal showed 2.2 s after entering, then the card ("Archive", "Monday · 12:01 PM").
- **Veil:** the screen was fully covered in 0.2 s, the move happened under the cover, it faded back over 0.4 s, and smoke puffed at both ends. The hold was then raised to 0.2 s to allow for network latency.
- **Locker:** camera at the door, FOV 64, saturation -0.3, slats and the HIDDEN eye. Stepping out restored everything, and so did a respawn while hidden.
- **Presence:** fade in over 0.6 s, fade out over 0.5 s, then removed.

## [1.8.7] - 2026-11-02: Night sight, the full moon and second chances

### Added
- **Night sight (H) for night races.** Vampires, Werewolves, Ghouls and Wraiths press **H** to see in the dark.
  - **You:** a personal light lifts the dark around you, under a sharp, desaturated hunter's grade with a hint of your race colour.
  - **Everyone:** your eyes glow in your race colour. Vampire is crimson, Werewolf amber, Ghoul acid green and Wraith ice blue.
  - **How the glow works:** each face strip gets an unlit copy of the iris behind the face, and the normal iris is hidden. The glow shows through the eye opening, blinks still cover it, and a small light at the eyes tints the face.
  - **Server-owned:** the state is the character attribute `NightSight`, so everyone sees it. Humans and Priests can't turn it on.
  - **Turns off** when you die, respawn, go back to the menu, or stop being a night race.
  - **Files:** `Services.Features.NightSight` (remote `ReplicatedStorage.NHNightSight`) and `Controllers.Character.NightSight`.
- **Full-moon night (VFX P2-1).** From 20:00 on a full-moon night (every 4th night, the same rule that boosts night powers):
  - the moon swells from 11 to 18 over 20 s;
  - a cool, pale-crimson moonlight grade fades in, stronger for Werewolves and Vampires;
  - a "The moon is full" banner shows once a night;
  - Werewolves get a 3 s silver edge around the screen.
  - It all eases back at dawn, and stays out of the main menu.
  - **Files:** `Controllers.World.FullMoon`, which has its own `NHMoonGrade` layer and never touches DayCycle's properties. `Controllers.Gui.Moments` gained a public `Banner(Opts)`.
- **"Second chance" get-up (VFX P2-8).** When a student gets back up from downed, players within 120 studs see:
  - a candle-gold wisp, a gold ring at the feet and a warm light pulse;
  - for **Fated** (the once-a-day revive): a clock-face sigil turns under them, its hand sweeping once, with crimson-gold embers.
  - It plays for the get-up only, never the downed, carry or grip visuals, and not for NPCs.
  - **Files:** `Controllers.World.GetUp`, NHFx `GetUp` from `Downed.Recover`. Progression marks a Fated revive with `NHFated`.

### Verified
**[PT]** on the spare save slot II (a Werewolf):
- **Night sight:** on through the real remote, with all 12 face strips glowing amber, the normal iris hidden, and the eye light, personal light and grade on. Off removes everything and restores the iris. A Human is refused.
- **Full moon (night 8, 21:00):** the moon reached 18, the strong grade applied, the banner showed at 2.5 s and the silver edge at 3.1 s. At dawn the moon went back to 11 and the grade to neutral.
- **Get-up:** the wisp, embers and ring drew, and the Fated sigil appeared. The sigil now finds the ground with a raycast, because a downed body sits low.

## [1.8.6] - 2026-11-02: Known bugs cleared

All seven open bugs from the Implementation-Status list are fixed and Play-tested.

### Fixed
- **#7 Animation tracks were never freed.**
  - **The bug:** every `TrackService.Play` loaded a fresh track and kept it for the life of the character, so long-lived delinquents, wolves and dummies crept toward the animator's track limit, after which animations stop playing.
  - **The fix:** each animator now keeps one loaded track per animation and reuses it. Older handles to the same animation are retired, and their stop listeners are disconnected. Everything is freed when the character goes away. Cleanup also remembers the Animator, so it works on destroyed characters.
- **#8 The aerial heavy (Aerial M2) had no cooldown.**
  - **The bug:** each weapon's aerial module set its cooldown under its own script name, at the `EndLag` marker (which raced the end of the move), while the gate checked `Aerial M2`.
  - **The fix:** the cooldown is now set under `Aerial M2` when the move starts, for its end lag plus 2 s (the `ENDLAG_COOLDOWNS` every module declared but never used). A press during the cooldown does nothing instead of falling through to a ground M2 played mid-air.
- **#13 Stuck sprint or block.** Sprint, Block, Crouch and Equip now travel over reliable remotes, so a dropped "Release" can't leave them on. Attacks and dodges stay unreliable, where a lost packet is just a missed press.
- **#3 No health regeneration.** Once your combat tag runs out (30 s after your last exchange), you heal 2% of max health a second. There's no regen while tagged, downed or in the menu. It stacks with the low-health traits.
- **#14 No rate limits or reach check:**
  - **Rate limit:** each combat input is capped at 15 events a second per player; extras are dropped.
  - **Reach check:** a player's hit can't land on a target more than 30 studs away.
  - **Not yet covered:** a full anti-teleport check is a separate design job, because entering school, the admin "bring" and menus all teleport legitimately.
- **#6 AI walked straight into walls.**
  - **Line of sight:** NPCs check it to their goal every 0.25 s (rays at chest and knee height). With a clear line the chase is unchanged.
  - **Pathing:** when blocked, they compute a path in the background (at most once a second, and only if the target moved), follow its waypoints, jump where the path says to, and face where they're walking.
  - **Patrols and return home:** patrols use the same pathing, and an NPC with no patrol route walks back home when it loses its target.
- **#9 Studio dummies:**
  - Their loops ended only when health dropped *below* zero, so they never ended. They now stop at death or removal.
  - A missing Humanoid skips that one dummy instead of aborting the rest.
- **#10 Missed respawns.** `EntityLoader` now connects `CharacterAdded` for players who joined before it started.
- **NPC setup:** every NPC made its own unprotected web call (`GetHumanoidDescriptionFromUserId`, always the same fallback id). It's now cached and wrapped in `pcall`, so NPC setup drops from 0.23 s to 0.015 s after the first.

### Verified (Play)
- **Track cache:**
  - 16 M1 presses gave three full combos at unchanged timing.
  - Each fighter keeps only 4 loaded tracks.
  - The cache is freed on removal.
- **Aerial M2:** fires, is refused straight after, and fires again after the cooldown, for Katana, Fist and Claws.
- **Sprint and block:** on and off through the real client path, over `RemoteEvent`s.
- **Regen:** +2.3 HP/s on a 117 HP student, and nothing while tagged.
- **Rate limit:** 50 M1 packets in about 1.7 s, 30 reached the server.
- **Reach:** a hit at 5 studs lands, and one at 40 studs is refused.
- **Pathing:** an AI fighter went around a 40-stud wall and reached its target in 2.1 s.
- **Respawn:** a respawned Claws student is set up in `Live` and re-equipped.

## [1.8.5] - 2026-11-02: Delinquents go down

### Changed
- **Delinquents go down like students instead of dying outright.** A beaten delinquent drops to the ground for 15 s. In that time you can:
  - **Carry** them (V).
  - **Grip** them (B) to finish them.
  - Use your **race finisher** (N): drain, eat, siphon or exorcise.
  - Leave them, and they get back up at 25% health and pick the fight back up.
- **Rewards:** a finish pays the finisher the delinquent's EXP and Yen and counts as an NPC kill.
- **Interrupting:** like any grip, getting hit by the rest of the crew interrupts it. Clear the crew first, or carry the body away.

### Fixed
- **Downed AI enemies (delinquents, the sparring partner) kept crawling** toward wherever they were walking when they went down. They now stay where they fall.

### Not changed
- **Wild wolves still die outright.** The grip and finisher animations are made for people, not a four-legged wolf.

### Verified
**[PT]** On an isolated delinquent, using the spare save slot (restored afterwards):
- Downed with no drift.
- Carried on the shoulder with the "[V] Drop [B] Grip" hint, and dropped.
- Grip finish at 3.0 s.
- Werewolf race finisher at 4.2 s: +¥10 and +1 NPC kill.
- A delinquent left alone got back up after 15.3 s.

## [1.8.4] - 2026-11-02: Fist and Claws combat audit, fluid movement, back to menu

### Fixed
- **Fist and Claws running attacks never dealt damage.** The running-straight clip has no readable `Hit` marker when the swing starts, so the server's timing code errored out. It now has a fallback `Hit` of 0.33 s (the clip's own "Hit" keyframe), and both classes land the running attack at 6, 10 and 14 studs.
- **Fist and Claws overshot their targets.** Two movers fought each other: a server lunge stacked on the shared running lunge, and a server hover and dive stacked on Katana's forward glide. Now:
  - The running attack uses one shared lunge at the weapon's own speed. It stops when someone is 3 studs in front of you, like Katana's does.
  - The downslam skips the glide. It holds your height but keeps your jump's drift, and the dive is timed to the ground so you land on the impact frame from any jump height.
  - If someone is within 11 studs ahead, the dive curves to land in front of them.
  - A second hit sweep 0.07 s later catches a target the dive reaches a frame late.
- **Claws hits had no effect or sound.** The Claws damage type (Slash) had no hit effect, block effect, hit sound, swing sound or block sound. Each now has one.
- **Pressing an action on cooldown cancelled what you were doing.** For example, a dash pressed during its cooldown ended your sprint. Cooldowns are now checked before the current action is cancelled.

### Added
- **The Claws class starts with claws on.** Spawning as a Claws student attaches the Specter Claws to both arms, already equipped with the Claws stance. Switching class in the locker stows them.
- **Dashing hands back to the run.** If sprint is still held when a dash ends (forward, back or side), you go straight into a full-speed run (40.5) instead of walking.
- **"Main Menu" button** in the Settings panel footer (top bar Menu, or M). It's a UI kit crimson button: click once to arm it, then again within 4 s to confirm. You go back to the normal loading screen and main menu with your progress saved, and you can choose any slot. It's refused while you're combat-tagged or downed, and it's hidden in the menu itself. It rejoins the same server through a teleport, so in Studio it only shows a "live game only" note.

### Measured (dummy tests, all three weapons)
- **M1 combo rhythm** already matched Katana's:
  - Hits at 0.30 / 0.87 / 1.47 / 2.08 s (Katana), 0.38 / 0.82 / 1.31 / 1.86 s (Fist) and 0.35 / 0.77 / 1.32 / 1.87 s (Claws).
  - All three restart after about 1.1 s.
- **Hits now landing:**
  - **Running attack:** Fist and Claws at 0.33 s, Katana at 0.50 s.
  - **Downslam (Fist and Claws):** from 8 and 14 studs up, with targets below or up to 9 studs ahead.
  - **M2:** all three. Katana lands two hits.
- **Still open:** Claws borrows the Fist attack animations until Claws clips exist.

## [1.8.3] - 2026-11-02: Full audit, chest rotations

### Fixed
- **Gear chests stand upright and face the room.** The imported chest kept its FBX pivot about 100 studs from the mesh, so chests swung around it, landed away from their spots and faced random ways. The pivot is now the chest's centre. Each chest sits with its back a hand's width off the nearest wall and the lock facing open space. In the open it faces the spot's direction. It re-checks the floor after moving, so it never ends up hanging off a ledge.
- **Mr. Hale walked through the staff-room table** on every patrol lap (his route ran along its edge, beside the coffee counter). The table moved 1.5 studs to open a clear path.
- **Gear store:** a failed save during a purchase could leave the player stuck on "One moment..." until they rejoined. The busy flag is now always cleared.

### Audit (no change needed)
- **Scripts:** all 438 compile, with no empty sources. A full in-game day and night across nine areas showed no server errors and no client errors.
- **World:** no parts fall out of the world or slide loose.
- **Data:** all 40 gear items have templates, all 35 hairs are rigged and grouped, every NPC hair ID is valid, every quest giver exists, and both stealth routes are present.
- **Purchases:** the store, gear and enrollment handlers all check distance, ownership, price and IDs on the server.
- **Delinquent kill reward** checked live: +¥10 and +30 Combat EXP for a Grunt.
- **School day:** "After School" from 12:00 is by design. The timetable runs four in-game school hours.
- **Left as is:**
  - Debug `warn(true)` lines in combat state code (Block, DownSlam, VowFlame, Posture Break, the skill template), because combat is off-limits here.
  - A raw table print on the client.
  - The HUD Yen label is exactly as wide as its text, which is fine.

## [1.8.2] - 2026-11-02: NPCs get real hair and stand where they should

### Added
- **Every NPC wears one of the owner's catalog hairs:**
  - The 12 ambient students get a random hair for their body type.
  - Each quest character has a fixed hair: Vesper Crane long straight, Coach Mallory a low ponytail, Pip short, Ezra slicked back, Coach Varga, Dex spiky, Bruno a Baki cut, Coach Dunmore locs.
  - The Hall Monitor, Mr. Hale and the Night Custodian have hair too. Delinquents already did.

### Fixed
- **Ambient students floated about 3 studs in the air.** The rig's pivot sits at its feet, not its root, so "pivot = floor + 3" put the feet 3 studs up. They're now placed by the root and their feet are snapped to the floor.
- **Posed students** (lying, sit-ups, push-ups, kneeling in detention, leaning) are settled again once their animation is actually playing. The body rests on whatever is under each limb, so nobody hovers or sinks into the floor.
- **Seated students** (sofa, armchair, desk chair) now sit on the cushion with their hips over the seat. They used to hang in mid-air in front of it or sink through it.
- **Walls and props:** students are nudged out of walls and props after posing. The leaning kid was standing inside the lost-property bin, and another student was half inside a hallway wall.
- **Floor checks** skip invisible colliders. The detention kid had been placed on top of an invisible trash-bin box.

## [1.8.1] - 2026-11-02: Wolves fight fair

### Changed
- **Wild wolves follow a fixed, readable pattern** instead of random bites.
  - **Cycle:** Bite → Bite → hop back → Leap, the same every time, with a short circling breather between steps. When a wolf spots you, it howls (calling the pack) and circles before its first bite.
  - **Every attack has a tell:** the wolf stops, crouches, and its eyes and outline glow red, 0.5 s before a bite and 0.85 s before a leap. Hitting it during the wind-up interrupts the attack.
  - **Bites** only land if you're still in front of its jaws. Back off or sidestep during the tell to dodge.
  - **The leap** locks onto where you stood when the tell ended, so a sidestep makes it sail past. After landing, the wolf pants for **1.4 s**, your free window to punish.
  - **One attacker at a time:** the rest of the pack circles wide and waits its turn. A wolf that gets stunned, stuck or posture-broken gives up its turn so it never stalls the fight.
  - **Measured on a student standing still against three wolves:** one hit every 2.5 to 3 s (5 per bite, 8 per leap), and never two tells at once.

### Fixed
- Wolf leaps (and the bite lunge) never actually moved the wolf. The Humanoid cancelled the velocity. Both now use a short scripted arc or step-in.
- A wolf could get stuck just outside bite range (its hips are far behind its jaws). Range is now measured from the head.

## [1.8] - 2026-11-02: The Headmaster's Desk (admin panel)

### Added
- **Admin panel, F3 for staff.** It's built only from the game's UI kit (Panel, TabBar, Buttons, Search, Toggles, Sliders, Section headers) with the school crest.
  - **Who can open it:** the group's rank 254+, the `Config.Cmdr` admin and owner lists, and anyone in Studio. Everyone else gets nothing, not even a hint that it exists.
  - **Server-side checks:** every action is checked on the server, rate-limited and logged. Staff can't target a higher rank.
  - **Students list:** search, health, race, ping, and owner, staff, muted, frozen and god tags.
  - **Moderation:** warn (with reason), mute and unmute (blocks chat on every channel), freeze, send to detention, spectate, kick, and ban (Roblox ban API, in days; permanent bans are owner-only), plus unban by UserId.
  - **Student:**
    - Heal, revive, god mode, transform, bring, go to, clear disciplinary record, kill, walk-speed slider.
    - Give Yen (over ¥100k needs an owner), Combat EXP, lineage spins or a name change.
    - Give any of the 40 gear pieces (listed by rarity colour).
  - **World:** set the school clock (or Morning, Noon, Midnight), clock speed, a server-wide announcement, and shut down the server (owner-only).
  - **Spawns:** a delinquent crew, a wolf pack (night only), a sparring partner, and clear all enemies.
  - **Self:** fly (WASD, Space, Ctrl, Shift for speed), noclip, ESP (names and health through walls), Ctrl+click teleport, invisible, heal, stop spectating.
  - **Server:** students, uptime, physics FPS, memory, school clock, enemy and wolf counts, and the staff log (last 200 actions).
  - **Destructive buttons** (Kick, Ban, Kill, Shutdown, Clear enemies) need a second click within 3 seconds.
- Other UI can open the desk by setting the player attribute `NHAdminOpen` (true, false, or a tab number). The server still decides who gets in.

## [1.7.1] - 2026-11-01: Delinquents and the real Gear Chest

### Added
- **Delinquents (PVE):** crews of street delinquents hang around the Field, the Pitch and the Boiler Yard, and pick fights with anyone who gets close.
  - Roles:
    - **Delinquent:** 100 HP, worth 30 EXP and ¥10.
    - **Delinquent Brute:** 170 HP, slower, worth 45 EXP and ¥15.
    - **Gang Leader** (rare): 220 HP, sharper, worth 85 EXP and ¥30.
  - They use the Fist moveset through the regular combat AI, dress in street clothes (leather jackets, flannels, band tees, ripped jeans) and wear the rigged catalog hairs.
  - Up to 6 at a time. Crews refill every 20 seconds, never within 45 studs of a student.
  - Tag a part `NHDelinquentSpawn` to add a hangout.
- **Combat AI skill (`Config.Skill`, 0 to 1):** scales how often an AI blocks, parries, dodges, feints and uppercuts. The sparring demon stays at 1. Delinquents are 0.12 to 0.45.

### Changed
- **Gear chests use the owner-imported model** (`ServerStorage.NHChestModel`, PBR). The lid now swings up and back on its rear hinge, showing the loot inside.

## [1.7] - 2026-11-01: Claws, wolves, gear chests, living hair and faces

### Added
- **Claws class:** the owner's claws idle and walk, a slashing M1 set with its own reach, and two skills:
  - **Slash Barrage** (Z): five quick hits.
  - **Ripper's Waltz** (X): a startup, a paired grab, a victim animation and the finisher.
- **Wolves (the owner's rigged wolf, used both ways):**
  - **Wild wolves** roam the Boiler Yard at night, three at a time. They bite, leap, howl to call the pack, stagger and guard-break. Each one is worth 40 EXP and ¥15.
  - **Werewolf form:** at Tier 2 or higher, T turns a Werewolf into the wolf, with its own bite and leap.
- **3D gear (40 pieces):** masks, scarves, hats, chains and more, each with a rarity and small, capped stat bonuses.
  - Found in **gear chests** around the school, which respawn every 8 minutes. A duplicate pays out Yen instead.
  - Also sold in the School Store's Accessories tab, with a try-on preview.
- **Gear Chest model:** dark oak with iron straps and a velvet bed of loot (R6 skull, tomes, candle, dagger, coins, crucifix). It's built in Blender with PBR textures. The game uses a stand-in until it's imported.
- **Living hair:** all 35 of the owner's catalog hairs are rigged with bone chains per lock.
  - Roots and hair lying on the scalp never move; only the hanging strands sway, with movement, turns, falls and wind.
  - Rigged with `tools/hair-rig/nh_hair_autorig.py` from the owner's OBJ exports. It's fitted to the R6 head through each hair's HairAttachment.
- **Faces blink:** every 2.5 to 6 seconds (sometimes twice), using lids drawn per eye shape. Faces squint while you're combat-tagged.
- **10 more brow styles:** Sleek, Flat Thick, High Arch, Sharp Arch, Worried, Angry, Feathered, Wisp, Tapered and Rounded, each fitted to every eye shape (21 styles in all).
- **NPC life:** sitting, thinking, chilling, leaning and barbell idles for ambient students. A gym regular now lifts.
- **Body Slam** has its victim animation.
- **Class locker:** a locker in the hallway lets you switch class (60 second cooldown).

### Changed
- **The Wardrobe is outfit only.** Hair and hair colour moved to the **Barber** NPC, who has a book of every hair.
- The "Use my Roblox outfit" toggle and the Roblox face option are gone. Old saves fall back to standard eyes.
- **Fist touch-ups:** the aerial M1 hovers, then dives with a tall hitbox that lands reliably. The running attack lunges and sweeps twice, and hits harder.
- Catalog hairs are sized down 12% to fit the head.

### Fixed
- Rigid hair no longer swings as one piece from the root.
- Grabs always release both characters, even if the grab is interrupted.
- The "NH dummy" no longer shows on the main menu.

### Notes
- The aerial dive's downward speed isn't visible yet. The tall hitbox covers it.
- Exorcise and Soul Siphon still use the placeholder kneel clip.
- The owner's raw hair exports (`Hair OBJ's/`) and the rigged FBX files (`Hair FBX/`) stay out of git.

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
