# Names, Clans and the Spin Shop: NH Combat Test

**Status:** built and playtested in Studio (single player). The Robux products are wired up but **not on sale yet**: their Developer Product ids still have to be created (see "Turning the shop on").

Every student now has a full name: **`<first name> <clan>`**, for example *Mara Ravenscar*.
- **First name:** typed by the player.
- **Clan:** the family name, **rolled by the server** and never chosen, just like race.

## Where players see it
- **Editing screen** (after picking a save slot): a section switch on the left.
  - **Look:** the Wardrobe.
  - **Name & Clan:** the register.
  - **Spin Shop:** Robux products.

  Each section has its own camera move: Name & Clan gets a low heroic angle, the Spin Shop the full body.
- **A new student** first watches the clan reel roll to their family name, then gets the cursor in the name box.
- **The header** above the switch shows the full name (e.g. **MARA RAVENSCAR**). It waits for the reel to land before updating, so it never spoils a spin.
- **Slot cards** show the name, with the clan in its rarity colour. Students without a first name yet read "Unsigned *Clan*".
- **In school** the character's name over its head (`Humanoid.DisplayName`) is the full name.
- **The Wardrobe's Lineage tab** (UI kit) has a "Get more spins" button that opens the Spin Shop.

## Name & Clan tab
- **The register:** a big name plate previews the full name live as you type, with the clan's rarity and odds ("EPIC CLAN · 1 in 67").
  - **Rules:** 3 to 14 letters. A single space, ' or - may go between letters, so "Mary-Ann", "O'Neil" and "Rose Lee" all work. The server title-cases it ("mara" becomes "Mara").
  - **Filter:** the server checks the name with Roblox's text filter (`TextService:FilterStringAsync`, broadcast context) and refuses anything the filter changes.
  - **Renames:** free until you first **enter school** with that student. Entering locks the name, and after that each rename costs one **Name Change**.
- **You must sign before you enter.** ENTER SCHOOL and CONTINUE send you to the register first: the name field pulses crimson, the placeholder reads "Write your first name here", and the cursor is already in the box. The server refuses `Enter` with "NeedName" too.
- **Your clan:** a slot-machine reel (kit `SpinReel`) with the clan's lore line and its **perk**. The reel always lands on the server's result, and rarer clans spin longer.
  - **Epic and better** land with a rarity burst, a ring flare in the clan's colour, and the camera leaning in.
- **Pity meter:** "Epic or better guaranteed within N spins".
- **Odds:** each rarity's share, with the clans in it.

## Clans (`ReplicatedStorage.Config.Clans`)
All 28 clans are original names. Each has a lore line and a perk.

| Rarity | Share | Clans |
|---|---|---|
| Cursed | 0.5% | Hollowmere, Nocturne |
| Legendary | 2.5% | Vauclair, Mortlake, Saint-Alder |
| Epic | 6% | Ravenscar, Greymoor, Duskmere, Holloway |
| Rare | 13% | Ashgrove, Blackwood, Calloway, Thorne, Wren |
| Uncommon | 26% | Whitlock, Garrow, Kestrel, Ambrose, Lowell, Sallow |
| Common | 52% | Harlow, Pike, Mercer, Fenwick, Abbott, Tully, Marsh, Danby |

- **Odds within a rarity:** the clans share the rarity's percentage evenly.
- **No repeats:** a spin never lands on the clan you already have, as long as that rarity has another.
- **Pity:** after **40 spins in a row** without Epic or better, the next spin is Epic or better.
- **Spins:** a new student gets a free first roll plus **3 clan spins**. Spins are free while testing in Studio (`Clans.FreeInStudio`, the same as Lineage).
- **Perks** are data only for now, like the Lineage traits. Each text says "Planned: ..." and nothing changes gameplay until the stat system exists.

## Spin Shop (`ReplicatedStorage.Config.Shop`)
| Product | Gives | Price hint |
|---|---|---|
| Clan1 / Clan5 / Clan15 | 1 / 5 / 15 clan spins ("Popular", "Best value") | R$ 49 / 199 / 499 |
| Race3 / Race10 | 3 / 10 race spins | R$ 129 / 349 |
| Variant3 | 3 variant spins | R$ 99 |
| Trait5 | 5 trait spins | R$ 99 |
| NameChange | 1 rename after enrolling | R$ 99 |

- **Where spins go:** to the **student you're playing** (that save slot).
- **"You have":** each group shows how many you own.
- **Prices:** the hints are placeholders. Once a product id is set, the real Robux price is read from Roblox.

### Turning the shop on
1. On the Creator Dashboard, open your experience, then **Monetization → Developer Products**, and create one product per row above.
2. Paste each id into `ProductId` in `Config.Shop`. A product with `ProductId = 0` shows "not on sale yet".
3. Test a purchase in Studio. Roblox runs test purchases there without charging.

## Server
**`Services.Player.Identity`**: names, clans and spins.
- **Saving:** stores `PlayerData.Identity = { First, Clan, Spins, Pity, Rolls, NameChanges, Locked }` through the `SetIdentity` action.
- **Attributes:** mirrors read-only `FirstName`, `Clan`, `ClanRarity` and `RPName` on the player.
- **Remotes:** `ReplicatedStorage.NHIdentity`, rate-limited:
  - `Get`, `SetName` and `SpinClan` (RemoteFunctions)
  - `Updated` (a RemoteEvent the server fires after a purchase)

**`Services.Player.Purchases`**: the game's **only** `MarketplaceService.ProcessReceipt`.
- **Granted once:** each receipt id is stored in `PlayerData.Purchases` (action `SetPurchases`, the last 100 are kept). A repeated receipt is granted only once.
- **No save loaded yet:** if the player is still on the main menu, the receipt waits (`NotProcessedYet`) and Roblox offers it again later.
- **Where grants go:**
  - Clan spins go to Identity.
  - Race, variant and trait spins go to the Lineage owner's hook, `Lineage.GrantSpins` (UI kit).
  - Name changes go to Identity.

**`Services.Player.Slots`**: the slot summaries now include `First`, `Clan` and `ClanRarity`, and `Enter` needs a first name.

**Client:** `Controllers.Gui.Identity`, the panel. API:
- `Toggle(on)`, `OpenTab("Name" | "Shop")`, `GetTab()`, `SetStageMode(on)`
- `Reveal()`, `Prompt(text)`, `HasName()`, `IsBusy()`
- Signals: `TabChanged` and `Rolled(clanId, rarity)`

**Test bridge:** `Identity`, `SetName`, `SpinClan`, and `GrantProduct(name, key, receiptId)`. The last one runs the real receipt handler with a made-up receipt.

## Verified (Studio)
- **Name rules:** "mara" becomes "Mara", "o'neil" becomes "O'Neil", and "Mary-Ann" and "Rose Lee" are accepted. "X", "Bob123", "a--b", three-word names and 16-letter names are refused.
- **Odds over 10,000 rolls:** Common 51.9%, Uncommon 25.9%, Rare 12.8%, Epic 6.3%, Legendary 2.5%, Cursed 0.6%. The longest run without Epic or better was 39, which shows pity works.
- **New slot:** a free first roll on load. Entering without a name is refused. Signing works and sets the overhead name. Entering school locks the name.
- **Receipts:** a granted receipt repeated does nothing, so nothing is granted twice. Clan, race and name-change grants all land in the save.
- **Real clicks and keys:**
  - The new-student reveal played ("The Ravenscar family claims you. (Epic)").
  - **Spin clan** rolled and landed on Harlow, and the pity bar moved.
  - **Spin Shop** opened and the camera moved.
  - The slot cards show names.
- **Fixed during testing:**
  - The update event was named `Changed`, which clashed with Roblox's own `.Changed`, so it's now `Updated`.
  - The header showed the new clan before the reel landed.

## Not tested
- Real Robux purchases. The product ids don't exist yet.
- Two players at once.
- Phones.
- The text filter on live servers. In Studio it lets most text through.
