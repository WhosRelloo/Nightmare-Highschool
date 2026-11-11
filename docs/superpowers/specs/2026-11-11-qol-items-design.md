# QOL items kit: design

**Status:** approved as proposed by the owner (2026-11-11), all four new systems included; built in 1.80.0 (`docs/QOL-Kit.md`).
**Owner's ask:** 12 everyday-carry items players hold and use, modelled in 3D to the top quality bar (the utility group was dropped).
**Renders:** `E:\NH-Work\qol\renders\` (in-hand on the R6 body, close-ups, solo shots); builder `art/characters/qol/nh_qol.py`, printed art `art/characters/qol/qol_prints.py`.

## What exists (NH Combat Test, surveyed 2026-11-11)

| System | What's there | What the kit reuses |
|---|---|---|
| Hotbar | `Gui.KitHud`: Backpack Tools, 6 slots growing to 9, keys 1-9 | Kit items are Tools, like the snacks and the phone |
| Inventory | `Features.Inventory`, `Config.Items`: snacks pinned as Tools (up to 4), `Grant`, `Take`, `Buy` near a stand | The saved record (`PlayerData.Inventory`), the eating clip, the Heal cooldown |
| Shops | Only the concession stand (`NHConcession`, Mrs. Okada). MORROW & VANE, THE WICK & KETTLE and LANTERNLIGHT BOOKS exist as interiors in the Map place (props batch 45) | New counters for the kit |
| Health | Max 100 + effects; out-of-combat regen 2%/s; `CombatTagUntil` (30 s); Downed at 0 | The snack tin, the pouch |
| Stamina | **None**, except in sports matches (`Config.Sports.Stamina`) | The thermos refills posture, plus stamina in a match |
| Posture | 0-100, regen 12/s after 2.5 s | The thermos |
| Timetable | Same classes for everyone (`Config.Classes`); `Gui.Timetable` (clock click, phone app); no "next class" API | The card opens it; a shared `NextClass()` helper |
| Compass | `Gui.Compass` strip (always on); `World.Waypoint` follows only the quest marker | The pocket compass adds its own target |
| Hall monitor | `School.HallMonitor`: catches truants in Class periods (+2 Truancy points); `IsTruant` skips some states; the `NHHallPass` attribute exists but also grants attendance | A new `NHPassUntil` check in `IsTruant` |
| Studying | Class EXP from attendance and lessons; effect key `ClassExp`; the Archive (Restricted) has Night Study | The library book's effect |
| Homes | Free dorm for everyone; `Homes.Enter`; no keys | The key ring gates the door |
| Lost & Found | `Features.LostFound`: pick-up prompts, return or box | Lost keys |
| Night | 20:00-06:00, readable night look; no darkness penalty; NightSight for four races | The lantern |
| Weather, cold, fall damage, low-health effects | **None** | Proposed below (owner's call) |

## The rules every item follows

- **Owned for good** by the student (save slot), kept in the Locker beside the snacks: `PlayerData.Inventory.Kit` through ProfileService only (`SetInventory`, cleaned by a new `Config.Kit.Sanitize`). Never droppable, never traded.
- **Hotbar:** pin up to **3 kit items** in the Locker (as well as the 4 snack pins). They become Tools in the hotbar. The **key ring** is worn on the hip and needs no slot. The **hand warmer** works from your pocket; pin it only to light it.
- **Holding:** equip it and the arm takes the item's hold pose straight away: the server turns the shoulder joints, as the phone does. That works before any animation is published. The hold and use clips (KeyframeSequences, listed at the end) replace the poses once the owner publishes them.
- **Server-authoritative:** every use goes through one `NHKit` remote folder, rate-limited the way the inventory is. The server checks:
  - ownership, counts, cooldowns and charges
  - combat tag, downed, carrying, main menu
  - the distance to the counter for buying and refilling
  
  The client never sends an amount or an effect.

## Where you get them

| Counter | Where (Map place) | In NH Combat Test | Sells |
|---|---|---|---|
| **MORROW & VANE** | the general store's counter | a stand-in counter tagged `NHKitShop` (Shop = Sundries) | lantern, lamp oil, compass, umbrella, first-aid pouch, bandages, hand warmer, charcoal |
| **THE WICK & KETTLE** | the café counter | stand-in (Shop = Cafe) | thermos and refills, snack tin and refills |
| **The Office** | the Main Hall office | stand-in (Shop = Office) | hall pass, a new set of keys |
| **The Archive desk** | the Archive | stand-in (Shop = Archive) | library card, borrowing and returning books |
| **Starter kit** | given at enrolment (existing students get it on their next join) | | campus map, timetable card, dorm key ring |

## The 12 items

| # | Item | Price | What it does | Hotbar |
|---|---|---|---|---|
| 1 | **Hand lantern** | ¥150; oil ¥15 | Click to light or put out. The light is a warm PointLight on the flame: range 22, brightness 1.6, colour (255, 170, 90), with shadows and a soft flicker. Everyone sees it. A full tank lasts **15 real minutes lit** (about 3 game hours). It drains only while lit. Refill to full at MORROW & VANE. | slot |
| 2 | **Folding campus map** | starter | Click to open the paper map screen. It is drawn from the Regions boxes, so it works in both places. It shows each place and what kind it is (school, sports, turf, out of bounds), a live **you-are-here** arrow, and your **next class** with its room and start time. Click a place to drop a **waypoint** pin; the compass follows it. No stats. | slot |
| 3 | **Pocket compass** | ¥120 | While held, the needle on the model swings to your target, and a brass dial at the bottom of the screen gives the target's name and how far it is. The target is the first that applies: your map waypoint, your tracked quest, your next class (school hours), your dorm door (evening and night), or north. It's shown on your screen only. | slot |
| 4 | **Umbrella** | ¥180 | Equip to open it. While it's open and you're falling, your fall speed is capped at **28 studs/s** (a normal drop reaches 60-100). There's no glide, no sideways push and no effect going up. It won't open while you're combat-tagged, and getting tagged closes it. Rain: see Option W. | slot |
| 5 | **Class timetable card** | starter | While held, a small card shows **Now** (the period, subject, room and minutes left) and **Next**, plus today's attendance chips. Click to open the full Timetable. No stats. | slot |
| 6 | **Dorm key ring** | starter; a new set ¥50 | Worn on the left hip, where it sways and jingles quietly when you walk or run. "Enter your room" needs your keys; without them the door rattles and the prompt sends you to the Office. **Losing them (option K):** when another student downs you, there's a **10%** chance your keys drop where you fell, as a Lost & Found glint ("Dorm keys"). Anyone can return them to you, or hand them in at the box, and gets ¥10 for it. The Office cuts a new set for ¥50 at any time; the old set stops working. Invited guests still get in. | none (worn) |
| 7 | **Hall pass** | ¥40, one a day | A brass paddle with **3 punches**. Click to show it: one punch, and for **60 real seconds** (12 game minutes) the hall monitor won't stop you. If it's already chasing you, showing the pass within 3 s ends the chase ("Carry on."). One punch per class period. It does **not** count as attendance (you're still late or absent), and it doesn't cover Forbidden rooms or fights. | slot |
| 8 | **Library card and books** | card free; books free to borrow | Sign up at the Archive desk, then borrow **one book at a time**: one for each subject (Mathematics, Chemistry, English, History) plus *A History of the Night Schools* (no subject). While the book is pinned: **+3% Class EXP**, and **+10%** on its subject's lessons. It's due back in **3 school days**. Overdue, the effect stops and the fine is ¥10 a day (at most ¥30), paid at the desk; there are no new loans until it's paid. | slot |
| 9 | **Thermos** | ¥100 (comes full of tea); refill ¥20 | Holds 4 cups. A sip takes 1.2 s: **−30 posture** (your guard recovers), half that while combat-tagged, and **+35 stamina** in a sports match. Cooldown 20 s. Refill with **tea** (it also clears the Chill, Option C) or **coffee** (also a snack buff: +2% Class EXP for 3 min, sharing the one-buff rule) at THE WICK & KETTLE. | slot |
| 10 | **Snack tin** | ¥80 (6 biscuits); refill ¥30 | Eat a biscuit (the existing eating clip, 1.1 s): **+15 health over 4 s**. **Out of combat only.** It shares the food "full" cooldown (12 s). Refill at THE WICK & KETTLE. | slot |
| 11 | **First-aid pouch** | ¥90 (3 bandages); refill ¥25 | Bandaging takes 2.5 s; you can walk slowly, and taking damage cancels it without using the bandage. It gives **+25 health over 5 s** and clears **Wounded** (Option L) for 2 minutes. Not while downed. | slot |
| 12 | **Hand warmer** | ¥110 (one night of charcoal); charcoal ¥10 | Option C (recommended): while it's lit, the Chill can't touch you. It works from your pocket, so it needs no slot. A stick burns for one game night (about 50 real minutes). Option B (no new system): **+5% guard** (posture gain) outdoors at night while it's lit. | pocket |

## New systems the items need (the owner decides each)

- **Option C, the Night Chill (recommended):**
  - When: outdoors (the Grounds, Sports or Turf regions, or no region at all) between 21:00 and 06:00.
  - How it starts: after 60 s outside you get **Chilled**.
  - What it does: frost-breath puffs and frost at the screen edges, **posture recovers 25% slower**, and **out-of-combat health regen pauses**.
  - How it ends: it fades 15 s after you go indoors, drink tea, or light a hand warmer.
  - Races: Wraiths and Vampires are immune; Werewolves take twice as long to chill.
- **Option L, Wounded:** below **25% health**:
  - a slow heartbeat
  - ink-dark screen edges (no red, no blood)
  - **−10% walk speed** out of combat (it never stacks below CombatSpeed's floor)
  
  A bandage clears it for 2 minutes. The alternative is the same without the speed loss.
- **Option W, Rain nights:**
  - 1 night in 4 rains for 2-4 game hours, server-chosen at 20:00.
  - On clients: rain particles and sound, a darker sky, and a wet sheen on characters.
  - An open umbrella, or being indoors, keeps you dry.
  - Soaked counts as Chilled at once (with Option C).
  
  Without it, the umbrella is the slow fall plus the look.
- **Option K, lost keys:** the 10% drop when you're downed. The alternative is that keys are never lost, only replaced if the owner wants a fee sink.

## Exploits we test (play test, slot 4 "Testy")

- **Buying and refilling:** fails away from the counter, without enough Yen, or when full. Spamming the remote is rate-limited.
- **Using:** fails while downed, carried, in the menu or with no charges. The snack tin and bandage fail while combat-tagged.
- **Remotes:** a fake call (another item id, a negative count, a target position) is ignored.
- **Hall pass:** the window is set on the server; the client can't extend it. A second punch in the same period is refused.
- **Umbrella:** it can't open while tagged; the fall cap stops when the server clears `NHUmbrellaOpen`; no upward or sideways help.
- **Oil, charcoal and loans:** they run on the server clock, so leaving and rejoining doesn't refill them.
- **Lost keys:** only the owner can use dropped keys, and returning them pays at most once.

## Models (Blender, `art/characters/qol/nh_qol.py`)

- **The builder:** it reuses the accessory kit's materials, bake and R6 mannequin (`nh_acc.py`, which it doesn't edit). The final bake is 2048 PBR, one atlas per item.
- **Extra pieces:**
  - Glow (Neon): the lantern flame, the warmer's coals
  - Glass: the lantern globe, the compass crystal
  - moving pieces: the compass needle, the tin lid
- **Printed art:** paper and labels come from `qol_prints.py` (PIL) and are baked into the atlas. All names are invented.
- **Size:** every piece is far under the 20.48-stud import cap (the umbrella, the biggest, is 4.5 across).
- **Clearance:** the builder checks every item in its hold pose against the R6 body: no intersecting triangles, nothing deeper than 0.003 inside, and the held point within 0.04 of the hand. The key ring is checked against the leg swing and the arm sweep. Before the import, every body type is run through the accessory checks.

## Animations for the owner to publish (KeyframeSequences)

| Item | Hold | Use |
|---|---|---|
| Lantern | LanternHold | LanternLight |
| Map | MapHold (two hands) | MapUnfold |
| Compass | CompassHold | CompassFlip |
| Umbrella | UmbrellaHold | UmbrellaOpen |
| Timetable card | CardHold | none |
| Key ring | none | KeyTurn (at the door) |
| Hall pass | none | PassShow |
| Library book | BookCarry | BookRead |
| Thermos | ThermosHold | ThermosSip |
| Snack tin | TinHold | uses the existing eating clip |
| First-aid pouch | PouchCarry | BandageWrap |
| Hand warmer | none | WarmerRub |

## What the Map place needs (for the hair-and-UI port session)

- The four counters tagged `NHKitShop` (attribute `Shop` = Sundries / Cafe / Office / Archive):
  - MORROW & VANE's counter
  - THE WICK & KETTLE's counter
  - the Office in the Main Hall
  - the Archive desk
- These scripts synced:
  - `Config.Kit`
  - `Features.Kit`
  - the patched `Inventory`, `HallMonitor`, `Homes`, `Progression` and `LostFound`
  - the client `Kit*` controllers (map, compass, card, umbrella, chill)
- The Regions boxes must cover the campus, because the paper map is drawn from them.
- Rain and Chill only if approved.
