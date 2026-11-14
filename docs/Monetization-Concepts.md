# Developer products and gamepasses: concept

**Date:** 2026-11-13. The owner asked: "Give me a concept on which Dev products to add to the game, update it based on
EVERYTHING we have in the game now. And gamepasses."

Nothing here is built. The game sells nothing yet: the Spin Shop's 13 developer products are wired up, but every
`ProductId` is still 0. Related: [[Names-Clans-and-Spin-Shop]], [[Races-and-Bloodlines]], [[Height]], [[Homes]],
[[Phone]], [[Skateboards]], [[Accessories]], [[QOL-Kit]], [[Inventory-QOL-Concepts]], [[Main-Menu]].

## Ground rules

1. **Nothing pay-to-win.** This is the line the game already draws.
   - Inventory QOL: "No Robux-only buffs and no Robux pin slots. Robux can buy cosmetic lunchboxes at most."
   - Training: "no Robux boosts exist".
   - The training streak: "Yen buys only cosmetics and kit".
   - So Robux never buys power, EXP, Yen, or a way out of a consequence.
2. **Race, clan and height stay rolled.** "Race is always rolled by the server; players never pick it." Robux can buy
   spins, never a chosen result.
3. **Cosmetics only from Robux, and never the earned ones.** Race looks unlock by tier, titles by deeds, trophies by
   beasts. Those stay earned, or they stop meaning anything.
4. **Roblox's paid random items rules.** Every spin is a paid random item:
   - **Odds:** all outcomes and their exact odds must show before purchase, including how pity changes them.
   - **Restricted regions:** players there need a fallback (see below).
5. **Every new screen follows the UI rule:** unique, on theme, PBR-textured and animated.
6. **No gore** in anything sold.

## What's on the shelf today (Spin Shop, `Config.Shop`)

| Product | Gives | Price hint |
|---|---|---|
| Clan1 / Clan5 / Clan15 | 1 / 5 / 15 clan spins | R$ 49 / 199 / 499 |
| Height3 / Height10 | 3 / 10 height spins | R$ 49 / 149 |
| Race3 / Race10 | 3 / 10 race spins | R$ 129 / 349 |
| Variant3 | 3 variant spins | R$ 99 |
| Trait5 | 5 trait spins | R$ 99 |
| NameChange | 1 rename after enrolling | R$ 99 |
| Vamp Cape / Rogue Cape / Fur Cape | a cape, owned for good by this student | R$ 149 / 149 / 199 |

**Before any of it goes on sale (required):**
- **Create the products** on the Creator Dashboard (Monetization > Developer Products) and paste the ids into
  `Config.Shop`. I'll find the ids on your profile, as for every upload.
- **Odds for every outcome, before purchase.**
  - **Shown today:** the clan register lists each rarity's share and its clans, the Height tab lists height odds, and
    the Bloodline tab lists race odds.
  - **Missing:**
    - Each clan's own odds: the rarity share divided by its clans, or the line "Odds for each clan listed below: X%".
    - Variant odds (85 / 12 / 3).
    - Trait odds.
    - A plain note on pity: "the 40th spin without Epic or better is guaranteed Epic or better".
- **The restricted-region check.** Where `PolicyService` says paid random items are restricted
  (`ArePaidRandomItemsRestricted`), the spin products must be hidden or blocked with a message.
  - Free starting spins still work there.
  - I'd also add a free way to earn spins, so those players aren't stuck: a spin for each rite passed and each
    report card with an A.
- **A fairness check on spins.** Races have passives, and clans have planned perks.
  - **Races:** paid race spins are only fair while races are sidegrades, never a ranking, so a Vampire isn't simply
    better than a Human. They are now: the moon bonuses alternate, and the hunger penalties apply to every race.
  - **Clans:** clan perks should stay small or cosmetic, or clan spins become pay-to-win.

## Developer products to add (repeatable purchases)

Prices are starting points. Managed Pricing (Roblox's price optimisation plus regional pricing) can test them once the
prices are read from Roblox instead of hard-coded, as the shop already does.

### A. Lineage spins (round out the Spin Shop)
| Product | Gives | Price |
|---|---|---|
| Variant10 | 10 variant spins | R$ 249 |
| Trait15 | 15 trait spins | R$ 249 |
| Bloodline Bundle | 3 race + 3 variant + 5 trait spins | R$ 279 (vs 327 apart) |
| Identity Bundle | 5 clan + 3 height spins | R$ 219 (vs 248 apart) |

Each pack needs the same odds panel as the single spins.

### B. Wardrobe (owned for good, like the capes)
- **Cloaks:** the 3D PBR cloaks (another session built them) sold like the capes. **R$ 149-249** each.
- **Outfit sets:** a top, bottoms and an accessory with their own look, e.g. "Midnight Prefect", "Crimson Gala",
  "Graveyard Formal". **R$ 199-299.**
  - Never a clique's own pieces: those stay members-only.
  - Never Kit B regalia or admin capes: those stay staff-only.
- **Eye-glow tints** within your race's own look (a Vampire's crimson goes darker or brighter). **R$ 99.** Never another
  race's eyes, and never a tier look.

### C. Personal effects (owned for good)
- **Skateboard decks:** Robux-only decks with an animated grip-tape glow and a light trail. **R$ 149-399.** The Yen boards
  stay as they are.
- **Lunchboxes:** the one item the Inventory QOL concept already allows. They're a cosmetic container that holds the
  same lunch as everyone else's. **R$ 49-99.**
- **Lantern, umbrella and thermos skins:** for the kit items, the same use with a different look, e.g. a crimson glass
  lantern or a bat-wing umbrella. **R$ 79-99.**
- **Phone styles:** animated wallpapers, a case skin on the phone frame, and ringtones for the Midnight Bell. **R$ 49-79.**
- **Dorm decor sets:** furniture and wall themes (a Gothic Study, a Moonlit Loft, the Crimson Court).
  - They decorate on top of the room's report-card state, so a wreck is still a wreck underneath.
  - **R$ 199-499.**
- **Hand-gear tints:** a colour for wraps or gloves you already own. **R$ 49.** Gear's stats stay what the armory sells.

### D. Moments (consumable and seen by everyone, rate-limited)
- **Lantern Release:** paper lanterns rise over the campus for every player in the server. A toast reads "<name> lit
  lanterns for Nightmare High". **R$ 99.**
- **Crimson Fireworks:** at night only, over the bell tower, with the crimson-moon palette. **R$ 149.**
- **A Midnight Bell shout-out:** one filtered line in everyone's phone news app for an hour. **R$ 49.**
- **Rules for all three:**
  - They're cosmetic only.
  - Each one runs at most once every 2 minutes per server, with no stacking.
  - They follow Reduce Flashing and Reduce Motion.

### E. Gifts
- **Any cosmetic can be bought for someone else:** pick a student in the server from Classmates, and it lands in their
  save with a toast.
- **Spins can't be gifted.** They are paid random items, and a gift would hand an odds-disclosed purchase to someone
  who didn't see the odds.

## Gamepasses (one-time, account-wide)

| Pass | What it gives | Price |
|---|---|---|
| **Extra Students** | Two more save slots (4 and 5): `SlotCount` becomes per-player (3, or 5 with the pass). The classic RPG pass, with no power at all. | R$ 399 |
| **Tailor's Pass** | 6 saved outfits per student, recolour any owned piece, and open the Wardrobe anywhere outside class and combat (stations stay for everyone else). | R$ 249 |
| **Collector's Dorm** | A loft above your dorm room (more decorating space), and the trophy shelf grows from 4 to 12 display spots. Trophies are still earned from beasts. | R$ 349 |
| **Gothic Emotes** | 8 emotes in the house animation style, e.g. a bow, a curtsy, a candle prayer, perching on a desk, a slow clap, a cloak flourish. | R$ 199 |
| **Gramophone** | Play your Night FM station aloud to students nearby, from the game's own licensed tracks only (no audio ids). | R$ 149 |
| **Prefect's Seal** (VIP) | A wax-seal crest beside your name (overhead, chat, Classmates), a gold name in the student list, the Prefects' Lounge (a cosmetic hangout, no loot or shortcuts), and one exclusive cape. | R$ 499 |

Account-wide means a pass works on every student. That's the main reason to make these passes, not products.

## Subscription and private servers

- **Night Society (optional monthly subscription, about R$ 299 a month):**
  - **Each month:** one exclusive cosmetic (a cape, cloak or deck) that you keep for good.
  - **Each month:** 5 clan spins and 3 height spins, with the same odds panel.
  - **The whole time you subscribe:** a "Society" seal.
  - **Never included:** Yen, EXP or power.
  - **Roblox rules:** benefits can't be revoked mid-term, subscriptions can't be tiered (no Bronze/Silver/Gold), and a
    Robux price can change at most every 60 days. Roblox Plus subscribers don't get it free (only private servers).
- **Private servers (about R$ 99 a month):**
  - **Who they suit:** study groups, roleplay, filming trailers and clique nights.
  - **What already works:** the server directory doesn't list private servers. Roblox Plus subscribers get paid
    private servers at no cost, and you're still paid for their time there.

## Not for sale, ever (the red lines)

| Not for Robux | Why |
|---|---|
| Yen | Yen buys the katana, brass knuckles and weighted gloves, so Robux Yen is Robux power. |
| EXP, training XP, stat points, levels | "no Robux boosts exist" (Training). |
| Weapons, classes, hand gear, Heat, EX | Combat power. |
| Revives, getting up from downed, a fated revive | They skip a fight's outcome. |
| Hunger refills or food | Hunger changes damage, stealth and EXP. Lunchboxes are a cosmetic container only. |
| Skipping detention or suspension, erasing discipline points, hall passes | The school has to have teeth (2.8.1). |
| Choosing a race, clan or height | Always rolled. |
| Race looks, titles, trophies, taste-book milestones | Earned; the milestones also give +1 max health. |

## Where they're sold

- **The Spin Shop** (the editing screen after picking a slot): spins and bundles.
- **The Wardrobe:** a "Tailor" section for capes, cloaks, outfit sets and tints. It shows owned pieces and buyable ones
  side by side, with a preview on your own student.
- **The phone:** a new **Robux shop** app (a black-lacquer catalogue with a wax-seal "Buy" stamp) for personal effects,
  moments, gifts and passes.
- **Where you'd see the thing anyway:** the dorm for decor, the skate rack for decks, and the kit for lantern skins.
  Each has one small "more styles" button that opens the right page. No pop-ups and no "limited time!" pressure.

## Build notes

- **Purchases:** keep the one `ProcessReceipt` (`Services.Player.Purchases`). Every new grant is another `Kind` in
  `Config.Shop`.
- **Account-wide ownership:** passes, and (your call below) cosmetics, need a small account-level store beside the
  per-slot saves. Today nothing is account-wide, and receipts live in each student's save.
- **Odds:** one shared odds panel in the UI kit, used by every spin product, with the restricted-region switch.
- **Art per group:** cloaks (exist), outfit sets, lunchboxes, kit skins, decks, decor and emotes. Each goes through the
  usual PBR pipeline and group upload.

## Your calls

- **Robux cosmetics: per student or the whole account?** Today a cape belongs to one student. I'd make Robux cosmetics
  account-wide (nobody wants to buy a cape three times) and keep spins per student, since a spin acts on one student.
- **Moments in the live game:** keep them, or are server-wide effects too loud?
- **Night Society:** have a subscription at all?
- **Stat respec:** reassigning Might, Grit and Wits points is mild convenience but still touches power. I'd leave it out
  of the shop, or make it earnable only.
- **The Back Lot farm:** it gives about ¥3,600 and 10,800 EXP an hour with no cap (Delinquent audit G). It isn't Robux,
  but an uncapped Yen farm undercuts every Yen price this concept leaves alone.
- **Prices:** the numbers above are starting points; Managed Pricing can test them once the products exist.

## Where I'd start

1. **Make the Spin Shop sellable:** create the products, add the full odds panel and the restricted-region check, plus
   a free way to earn spins.
2. **Extra Students and the Tailor's Pass:** the two passes most players want, with no new art.
3. **Capes, cloaks and outfit sets** in the Wardrobe's Tailor section, plus gifting.
4. **Personal effects:** decks, lunchboxes, kit skins and phone styles.
5. **Collector's Dorm, Gothic Emotes, the Gramophone and Prefect's Seal.**
6. **Moments, Night Society and private servers.**

Sources (Roblox creator docs, checked 2026-11-13): [paid random items](https://create.roblox.com/docs/production/monetization/paid-random-items),
[subscriptions](https://create.roblox.com/docs/production/monetization/subscriptions.md),
[monetization overview](https://create.roblox.com/docs/en-us/production/monetization),
[managed pricing](https://create.roblox.com/docs/production/monetization/managed-pricing),
[Roblox Plus](https://create.roblox.com/docs/en-us/production/monetization/roblox-plus.md).
