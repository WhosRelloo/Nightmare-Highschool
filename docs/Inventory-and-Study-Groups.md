# The Locker, snacks and study groups

Added in 1.10.0. Code lives in Studio; this page is the design and how the pieces connect.

## The Locker (G)
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
  - **Buying:** the counter's prompt carries `NHConcession`, and you must be within 16 studs.
  - **Lunch:** the `NHLunchSpot` markers in front are where the lunch crowd queues.
- **Save data:** `PlayerData.Inventory = { Items = { [id] = count }, Pinned = { id } }`, written with the `SetInventory` action and checked by `Config.Items.Sanitize`.
- **Remotes:** `ReplicatedStorage.NHInventory`. Get, Use, Pin, Drop and Buy (RF), plus Changed (RE).

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
