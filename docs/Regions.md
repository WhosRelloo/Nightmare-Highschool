# Regions: place names, discovery and rewards

Walk into a named place and a quiet title card names it, just under the compass. Your first visit to each place counts as a discovery. It saves per slot, gives EXP, and finding every place earns the title **Explorer**. Added in 1.16.0, 2026-11-03.

## What you see
- **The card** sits under the compass for about 3 seconds (4.4 for a discovery) and fades:
  - a smoky band behind it
  - a small spaced **kicker** ("ROOM 101", "NIGHTMARE HIGH", "STAFF ONLY", "DELINQUENT TURF")
  - the **name** in the title font, burning in left to right with a bright edge
  - a pip that turns into place, with the kit divider drawing out from it both ways
  - a dim italic line, and a faint glow breathing behind the name
- **Danger places** are crimson, and the name flickers like a candle. These are the Forbidden places, faction turf, and Restricted places after dark (with their night text and the kicker "OUT OF BOUNDS AFTER DARK").
- **A first visit** adds a row: the wax seal stamps down with a burst of glow, then "DISCOVERED N / 19", then a pip for every place, with the new one lighting up and a soft bell.
- **The compass:** when you face nothing, its readout names the place you're in (◇ The Main Hall). While a card shows, the readout stays clear.
- **The arrival card** (leaving the main menu) now names your region too.

### When it doesn't show
- **Steadiness:** you must stay 0.5 s in a place before its card shows, and the same place won't show again within 45 s unless it's a first visit.
- **School Grounds** is the catch-all, so it never shows a card.
- **After the main menu:** no card for 7 s, because the arrival card names the place. That first place only gets a card if it's a new discovery.
- **No compass, no card:** none while the compass is switched off.
- **Cinematic view** (`\`) keeps the cards; they sit just below the top letterbox bar.
- **Toasts** step down out of the card's way while it shows.
- **Reduce Motion:** the card just fades.

## The places (19 to find)
| Id | Card name | Kind | Priority |
|---|---|---|---|
| MainHall | The Main Hall | School | 2 |
| EastWing | The East Wing | School | 2 |
| R101–R106 | Homeroom, Mathematics, Chemistry, English, History, Detention (kicker "Room 10x") | School | 5 |
| Archive | The Archive | Restricted | 5 |
| BoilerYard | The Boiler Yard | Restricted | 5 |
| StaffRoom | The Staff Room | Forbidden | 5 |
| RecordsOffice | The Records Office | Forbidden | 5 |
| Ring | The Ring | School | 5 |
| Gymnasium | The Gymnasium | Sports | 4 |
| Pitch | The West Pitch | Sports | 4 |
| Field | The North Field | Sports | 4 |
| PracticeLanes | The Practice Lanes | Sports | 4 |
| BackLot | The Back Lot | Turf | 3 |
| WestEdge | The West Edge | Turf | 3 |
| Grounds | School Grounds (not counted, no card) | Grounds | 1 |

Each place's daytime and night line is in `ReplicatedStorage.Config.Regions`. Where boxes overlap, the highest Priority wins, then the smaller box.

## For the builder: the boxes
The region boxes are invisible, non-colliding parts in `workspace.Regions`. That model is Persistent, so the boxes never stream out. Each part has the attribute `RegionId` set to one of the ids above.

Most boxes were built from what's already in the map:
- **Halls:** the floors.
- **Rooms, the Archive, the Boiler Yard and the Staff Room:** their zones.
- **Records Office and the Ring:** their floors.
- **Sports grounds:** each court plus 7 studs all round.
- **Practice lanes:** both of their bounds together.
- **Back Lot, West Edge and Grounds:** drawn by hand.

To move a place, move or resize its box. To add a place:
1. Add a box with a new `RegionId`.
2. Add an entry to `Config.Regions.Defs` (Name, Kind, Priority, Text, and optionally Night, Kicker, Title).

The total count updates on its own. The build script is a scratch Edit script, `build_regions.luau`. It rebuilds the model in place.

## How it works
- **Client: `Controllers.World.Regions`**
  - checks your position 4 times a second, draws the card and feeds the compass label
  - the card has its own ScreenGui `NHRegionCards` (DisplayOrder 1001, attribute `ShowInCinematic`), scaled like the compass
- **Server: `Services.Features.Regions`**
  - Remotes are in `ReplicatedStorage.NHRegions`: `Get` and `Enter`.
  - **On a first visit** the client calls `Enter`. The server then:
    1. checks you aren't in the menu and that you really are inside that box (6 studs of slack)
    2. rate-limits the call to one per 0.3 s
    3. saves the place to `PlayerData.Regions.Found` (UpdateState `SetRegions`)
    4. gives `Config.Progression.Exp.RegionFound` (15 Quest EXP)
    5. when all 19 are found, calls `Reputation.AwardTitle(Player, "Explorer")`
- **Cinematic:** `Controllers.Gui.Cinematic` now skips any ScreenGui with the attribute `ShowInCinematic = true`.
- **Compass:** `Controllers.Gui.Compass.SetRegion(name, colour)` is the new label API.
- **Test hooks:**
  - TestBridge `RegionState(name)` and `RegionReset(name)`
  - the player attribute `NHRegionCardHold = seconds` keeps a card up longer, for screenshots

## The seal (new art)
`Theme.Images.Seal` is now a 512 PBR wax seal (`130174890638243`, was `119862801131834`):
- **What it shows:** a scalloped, dripping wax blob with a raised lip, pressed with a bevelled ring, 12 clock ticks and the school's diamond-cross emblem with a pearl.
- **How it's made:** baked by `art/ui/hud/make_seal_pbr.py` with the health bar's PBR shader (GGX specular, AO from height).
- **Colour:** it's greyscale, so `ImageColor3` tints it everywhere it's used (gold on the arrival and region cards, crimson for danger, rarity colours on gems). Preview: `art/ui/hud/out/seal_v2/preview.png`.

## Tested (Studio Play, slot II, at night)
- **Discovery:** walked into the Main Hall, Rooms 101–104 and the Staff Room. Each saved once and showed its discovery card. Then all 19: the count reached 19 / 19 and the title Explorer was awarded.
- **Cards:** the gold card (Mathematics, Chemistry) and the crimson card (The Staff Room) both rendered.
- **Cinematic view:** with it on, Room 104's card showed under the letterbox bar while every other GUI stayed hidden. The compass came back after leaving it.
- **Compass label:** named the region when facing nothing.
- **Console:** no errors.
- **Cleanup:** the test slot's places were reset afterwards. The test EXP and the Explorer title stay on that slot.
- **Not tested:** two players, Reduce Motion, the arrival card's new region name, and toasts arriving during a card.
