# Fists first, and the armory (2.5.0)

The owner's request (2026-11-12): "I want all students to start off with the "Fist" Class then can buy a katana from
the armory shop keeper."

The owner's decisions:
- **Existing saves:** "Everyone to Fist". A katana had never been sold: every save got one by default (`PlayerData`)
  or picked it free at the class locker, so there was no bought katana to keep.
- **Price:** ¥1,000.
- **Claws:** locked for now, with no way to unlock them yet. Admins can still grant them.
- **Where:** a small placeholder armory in each place. In the Map it sits by the Locker Room Placeholder.

Live in NH Combat Test and the Map. CHANGELOG 2.5.0 has the test record.

## How it works

- **Every student starts on Fist.** `PlayerData.Weapon` defaults to `Fist`. Fist has had its full moveset since 1.6
  (see [[Combat-System]]): the four-hit combo, the running straight, the downslam, the crit, block, parry, grip, and the
  Z / X / C skills.
- **What you own is saved** in `PlayerData.Armory = { Owned = { [class] = true }, V }`. Fist is always owned.
- **The migration** (`Config.Armory.Migrate`, run by `Services.Player.Data` on every profile load, right after
  `Reconcile`):
  - **V1, once per save:** `Weapon = Fist`, nothing else owned, `V = 1`.
  - **Every load:** a class you don't own goes back to Fist.
- **The class locker only offers what you own** (`Features.ClassLocker`):
  - Katana, before you buy it: "Sold at the armory for ¥1000." and an **At the armory** button. Picking it anyway is
    refused with "Buy it at the armory first."
  - Claws: "Locked for now." and a **Locked** button. Picking them anyway is refused with "That class is locked for now."
  - The 60 s cooldown and "put your weapon away first (E)" are unchanged.
- **The armourer** (`Features.Armory`): an NPC stands on each part tagged `NHArmoryKeeper`, facing that part's front.
  "Browse" opens the **Iron Vigil Armoury** window (`Gui.ArmoryUi`, built from the UI kit like the kit counters):
  - **Fists:** free, "Your class" or "Owned".
  - **Katana:** **Buy ¥1000**, then "Owned".
  - **Claws:** **Locked**.
  - The window shows your Yen, closes when you walk more than 18 studs away, and closes when you use another prompt
    (the class locker beside it).
- **Buying** (`NHArmory.Buy`):
  - Checked by the server: the class must be on sale and not already owned, you must be within 16 studs of something
    tagged `NHArmoryShop` (the armourer or the counter), and you need the Yen.
  - Charges the Yen through `Data.UpdateState` (`UpdateYen`) and marks the class owned. It doesn't switch you: you
    switch at a class locker, the same way classes were switched before.
- **Admins:** `Cmdr` `adjustWeapon` also grants the class, so an admin-set class survives the next load.
- **NPCs and dummies** keep the Katana default they had (`EntityLoader` sets it for non-players), so delinquents,
  clique fights and the combat dummies are unchanged.

## The placeholder armory

`tools/armory-2xx/build_placeholder.luau` builds the "Armory Placeholder" folder: an open-front booth 22 by 14 studs and
11 tall, with a slate floor, brick walls, a roof and two warm lights. In it:
- the batch-46 props, cloned from the showcase with the same facing to their wall: the ArmoryCounter (tagged
  `NHArmoryShop`), KatanaStand, PlateArmourStand, ShieldWall and the hanging ArmorySign;
- `ArmourerSpot` (tagged `NHArmoryKeeper`), where the armourer stands behind the counter;
- a **class locker** (tagged `NHClassLocker`), so you can switch right after buying.

| Place | Where | Open side faces |
|---|---|---|
| NH Combat Test | (72, 0.9, -8), south of the school | south |
| Map | (-838, -7.96, -101), east of the Locker Room Placeholder | west, toward it |

In the Map the folder and its pieces are tagged `NHCore`. The builder can move or delete the folder in one go, or tag a
real counter `NHArmoryShop` and a real spot `NHArmoryKeeper` (attribute `KeeperName` for the prompt's name) when the
real armory is built.

## The Map

- The Map has never saved anything: its `Data` builds a fresh profile on every join. Students start on Fist there too,
  and a katana bought in the Map lasts until you leave.
- New in the Map: `Features.ClassLocker` and `Gui.ClassLocker` (it had no class locker), `Config.Armory`,
  `Features.Armory` and `Gui.ArmoryUi`.
- Patched: `PlayerData`, `Player.Data` (the migration in `LoadSlot`) and `EntityLoader`. The Map has no Cmdr.
- The Map's `AI.Rig` is only a stub, so the armourer there is a plain R6 body
  (`CreateHumanoidModelFromDescription`) dressed by `UI.Appearance`.

## Code

| What | Where |
|---|---|
| Stock, price, the save, the migration, the shop's name | `ReplicatedStorage.Config.Armory` |
| The armourer, buying, the remotes `ReplicatedStorage.NHArmory` (Info, Buy) | `ServerScriptService.Services.Features.Armory` |
| The armoury window | `StarterPlayer.StarterPlayerScripts.Controllers.Gui.ArmoryUi` |
| Only owned classes can be picked | `Services.Features.ClassLocker`, `Controllers.Gui.ClassLocker` |
| Fist by default, `Armory = {}` | `ReplicatedStorage.PlayerData` |
| The migration on load | `Services.Player.Data` |
| NPCs keep Katana | `Services.Managers.EntityLoader` |
| Admin grant | `Cmdr.Commands.Adjust.AdjustWeaponServer` (NH Combat Test) |
| Studio test hook (runs inside the game's module) | `ServerStorage.NHArmoryTest:Invoke("State" \| "Yen", playerName, n)` |

Every patched line is marked `(armory)`. Backups are in `ServerStorage.NH_Backup.Armory_pre_20261112` in both places.
