# The Locker, snacks and study groups

Added in 1.10.0. Code lives in Studio; this page is the design and how the pieces connect.

## The Locker (` key)

G is the introduce-yourself key; the Locker moved to the backquote on 2026-11-02. The inventory audit (1.90.1) fixed 17
bugs; see the CHANGELOG and `docs/Inventory-QOL-Concepts.md`.

- **Empty pins:** a pinned snack you've run out of keeps its pouch slot for the restock. It gives way when you pin or buy
  something else, and clicking it clears it.
`Controllers.Gui.Locker`. The layout follows the owner's inventory reference (2026-11-02):

| Area | What it shows |
|---|---|
| Character (left) | your character in the kit `CharacterPreview`. Slots: Head, Face, Neck (worn gear) on the left; Weapon class and Snack buff on the right |
| Gear Scale (under it) | what your worn gear adds up to (damage, toughness, health, guard, stealth, night power, combat and all EXP) |
| Backpack (right) | tabs All, Gear and Snacks; a grid where each slot shows the item in 3D (gear template or snack prop); hover tooltips; the selected item's actions under the grid |
| Pouch (under it) | the four snacks pinned to your hotbar |

- **Snacks:** Use, To pouch or Unpin, Drop (click twice).
- **Gear:** read-only here. You still change it at a locker-room wardrobe (Outfit tab), as before.
- **Hotbar:** pinned snacks are Backpack Tools with `NHItem`, `Rarity` and `Count` attributes. That's why the existing hotbar (`Gui.KitHud`) shows them with no changes. Equip one and click to use it.

## Snacks and the concession stand
`Config.Items`, `Services.Features.Inventory`, `Services.Features.Concession`.

| Snack | Price | Effect |
|---|---|---|
| Onigiri | 25 | +15 health over 3 s |
| Melon Bread | 40 | +30 health over 6 s |
| Yakisoba Bun | 80 | +50 health over 8 s |
| Night Bento | 200 | +80 health over 10 s |
| Ramune | 35 | +0.6% guard for 3 min |
| Barley Tea | 45 | +0.8% stealth for 3 min |
| Canned Coffee | 60 | +3% class EXP, +2% quest EXP for 5 min |
| Red Lantern | 150 | +1% damage, +2 max health for 3 min |

- **Food:** heals over its duration, half as much while combat-tagged. All food shares a 12 s "full" cooldown.
- **Using:** takes 1.1 s, with the owner's eating clip.
- **Drinks:** one snack buff at a time; a new one replaces the old. The buff is an effect source in `Progression.Effects`, like gear. It isn't saved, so it ends if you leave.
- **Limits:** stacks cap at 20, and the pouch holds 4.
- **The stand:** built from parts outside the west end of the hallway. Tag a part `NHConcessionSpot` to place it by hand.
  - **The model:** when `ServerStorage.NHProps.ConcessionStand` is there (props batch 14), the stand is that model: gothic cast iron and oxblood under a slate roof, with the sign and menu drawn on its boards. Otherwise it is built from parts. See [[School-Props]].
  - **Buying:** the counter's prompt carries `NHConcession`, and you must be within 16 studs.
  - **Lunch:** the `NHLunchSpot` markers in front are where the lunch crowd queues.
- **Skateboards:** the Locker's Boards tab lists all nine boards; equip yours, buy the rest. See [[Skateboards]].
- **Trophies (1.56):** a rare drop from a beast you kill (`Config.Items.Trophies`, `Kind = Trophy`: the Hellhound's Ember Tooth, from 1.57 the Grave Ghoul's Grave-Dirt Locket, from 1.59 the Night Stalker's Finger-Bone, from 1.60 the Bone Spider's Fang, from 1.61 the Crypt Bat's Wing-Claw). It shows under All with its own model, labelled Trophy, with a Drop-only card. It's never sold at the stand, pinned to the hotbar or used, and it saves with your other items. See [[Beasts]].
- **Save data:** `PlayerData.Inventory = { Items = { [id] = count }, Pinned = { id }, Boards = { Owned = { id }, Equipped = id } }`, written with the `SetInventory` action and checked by `Config.Items.Sanitize`.
- **Remotes:** `ReplicatedStorage.NHInventory`. Get, Use, Pin, Drop and Buy (RF), plus Changed (RE).

## The concession kit (1.90)

Props batch 54 ([[School-Props]]): every item the stand sells is modelled now, with its own packaging, and 26 snacks were added (40 on sale). Lunch meals wait for a lunch period.

| New snack | Price | Effect |
|---|---|---|
| Takoyaki Boat | 55 | +35 health over 6 s |
| Nikuman | 35 | +22 over 4 s |
| Curry Bread | 50 | +32 over 5 s |
| Cup Ramen | 90 | +55 over 9 s |
| Roast Sweet Potato | 45 | +28 over 5 s |
| Yakitori Skewers | 30 | +18 over 3 s |
| Pumpkin Soup | 120 | +65 over 10 s |
| Senbei | 15 | +8 over 2 s |
| Grave Crisps | 20 | +10 over 2 s |
| Popcorn | 25 | +14 over 3 s |
| Dango | 30 | +18 over 3 s |
| Taiyaki | 40 | +26 over 5 s |
| Custard Pudding | 45 | +28 over 5 s |
| Tombstone Cookie | 20 | +12 over 2 s |
| Cream Puff | 35 | +20 over 4 s |
| Bat Gummies | 20 | +0.4% stealth, 2 min |
| Candy Apple | 30 | +0.4% guard, 2 min |
| Ghost Mints | 25 | +1% quest EXP, 2 min |
| Konpeito Stars | 25 | +1% class EXP, 2 min |
| Licorice Whips | 20 | +1% combat EXP, 2 min |
| Moonlight Chocolate | 40 | +1 max health, 3 min |
| Strawberry Milk | 30 | +1 max health, 3 min |
| Hot Cocoa | 40 | +0.5% toughness, 3 min |
| Melon Soda | 35 | +1.5% quest EXP, 3 min |
| Black Cat Cola | 45 | +0.5% damage, 3 min |
| Green Tea | 40 | +2% class EXP, 3 min |

- **Lunch meals** (`Items.Lunch`, `Lunch = true`): Katsu Curry 180 (+100 over 12 s), Shoyu Ramen 170 (+95), Karaage Set 190 (+105), Grilled Mackerel Set 160 (+90), Omurice 170 (+95), Witching Hour Stew 200 (+115 over 14 s), Graveyard Shepherd's Pie 200 (+115), Pumpkin Gratin 180 (+105), Raven's Roast 220 (+125); extras Fruit Cup 40 (+22), Side Salad 35 (+18), Rice Bowl 30 (+20), Miso Soup 30 (+15), Chocolate Milk 35 (+1 max health, 3 min). They are in `Items.ById` (they save and can be granted) but not in `Items.List`, and `Items.OnSale` says no until a lunch period sets `ReplicatedStorage`'s `NHLunchOpen` attribute (`Items.LunchOpen()`). A lunch period should add them to the stand's menu (or its own counter) and set the attribute.
- **Hand props:** the hotbar Tool's Handle and the Locker's 3D slot are `ReplicatedStorage.NHSnacks.<Id>` (a `Handle` MeshPart, glass welded under it, an `NHGrip` CFrame attribute) when it's there, the old generated part when it isn't.
- **The stand's menu board** lists the first eight regular items and "+ N more at the counter"; the buy menu scrolls through all 40.
- **Test hook:** `ServerStorage.NHTestBridge` `GrantItem(name, id, n)` puts items in a test student's Locker through `Inventory.Grant` (Studio only).

## Study groups (U)
`Services.Features.Party`, `Controllers.Gui.StudyGroup`.

- **Size:** up to four. The inviter becomes the leader. Only the leader invites or removes.
- **Names:** invites and the member list show a name only if you know it (`Strangers.Knows`); otherwise "A stranger".
- **EXP:** +10% on all EXP while another member is within 150 studs. 25% of your combat EXP goes to every member within 150 studs (category `Group`, so it never chains).
- **Not saved:** leaving the server or going back to the main menu leaves the group. A group of one breaks up.
- **Player attributes:** `NHParty` (group id) and `NHPartyLeader`.
- **Remotes:** `ReplicatedStorage.NHParty`. Get, Invite, Respond, Leave, Kick and Candidates (RF), plus Changed and Invited (RE).
- **Not built:** no friendly-fire rule. Members can still hit each other, because combat is off-limits without the owner's say-so.

## The Report Card (L)
`Controllers.Gui.StatsPanel` is three kit panels side by side:

| Panel | Contents |
|---|---|
| Report Card | name, race and tier, level and EXP, points, and the Might, Grit and Wits cards with +1 |
| Abilities | the combined effects (a `StatSheet`) |
| Record | takedowns, attendance, discipline, and where every bonus comes from |

- **Data:** comes from `NHProgress.Get`. The sheet now carries `Record`, `GearText` and `SnackText`.
- **Opening:** `Gui.Progress.Toggle` hands off to it, so the old record panel is gone, and so is the top bar's Record button behaviour.

## The daily special (1.39)

One lunch item each school day, sold only on its day (the 6 AM event day), one per student, ¥30, a 5-minute snack buff with a twist for some races:

| Day | Special | Everyone | Twist |
|---|---|---|---|
| Monday | Garlic Bread | +2% toughness | Humans double; Vampires -2% damage instead |
| Tuesday | Mystery Meat Loaf | +2% combat EXP | Ghouls double |
| Wednesday | Moon Cake | +1% guard | Werewolves double |
| Thursday | Holy Water Lemonade | +2 max health | Priests double; Vampires and Wraiths -1% stealth instead |
| Friday | Ectoplasm Jelly | +2% class EXP | Wraiths double; Humans get nothing |

`Config.Items`: `Special = 1..5`, `Race = { [race] = { Mult } or { Effects }, Note }`, `Items.TodaySpecial()`, `Items.OnSale(It)`, `Items.EffectsFor(It, Race)`, `Items.RaceNote(It, Race)`. The shop shows it first ("Today: ...") with your race's note; the stand's menu board has a "Today:" line; the Midnight Bell and the notice board print it.
