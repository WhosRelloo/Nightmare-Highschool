# Developer products and gamepasses: concept

**Date:** 2026-11-13. The owner asked: "Give me a concept on which Dev products to add to the game, update it based on
EVERYTHING we have in the game now. And gamepasses." Then: "I want the products to be cheaper so players will be more
inclined to buy them even if they don't have a bunch of robux. Rerolls should be super cheap. Create designs for all
of them on theme and their prices."

**Status:**
- **Nothing is on sale.** The Spin Shop's 13 developer products are wired up, but every `ProductId` is still 0.
- **The icons are made:** 50 on-theme PBR icons, one for every product, pass and the subscription, in
  `art/group-upload-shop/` (see "The icons").
  - **Uploaded:** 49 to the group, all pending moderation.
    - **Ids:** in `art/group-upload-shop/ids.json`, and in NH Combat Test's `Config.Shop.Icons`. The 13 existing
      products each carry an `Icon` key.
    - **Missing:** `NHShopPassExtraStudents` didn't upload.
  - **Products and passes:** none exist on the experience yet.
- **Related:** [[Names-Clans-and-Spin-Shop]], [[Races-and-Bloodlines]], [[Height]], [[Homes]], [[Phone]],
  [[Skateboards]], [[Accessories]], [[QOL-Kit]], [[Inventory-QOL-Concepts]], [[Main-Menu]], [[Icon-Set]].

## Ground rules

1. **Nothing pay-to-win.** This is the line the game already draws.
   - Inventory QOL: "No Robux-only buffs and no Robux pin slots. Robux can buy cosmetic lunchboxes at most."
   - Training: "no Robux boosts exist".
   - The training streak: "Yen buys only cosmetics and kit".
   - So Robux never buys power, EXP, Yen, or a way out of a consequence.
2. **Race, clan and height stay rolled.** "Race is always rolled by the server; players never pick it." Robux buys
   spins, never a chosen result.
3. **Cosmetics only, and never the earned ones.** Race looks unlock by tier, titles by deeds, trophies by beasts.
4. **Cheap on purpose (owner).** Most things cost less than R$ 100 and rerolls cost a few Robux, so a player with the
   smallest Robux pack can still buy something. The cheapest Robux pack is 80, so nearly everything here fits in it.
5. **Roblox's paid random items rules.** Every spin is a paid random item:
   - **Odds:** all outcomes and their exact odds must show before purchase, including how pity changes them.
   - **Restricted regions:** players there need a fallback (see below).
6. **Every new screen follows the UI rule:** unique, on theme, PBR-textured and animated.
7. **No gore** in anything sold.

## The icons

- **Every icon is a round medallion,** because Roblox crops gamepass icons to a circle (developer products show
  square, and the medallion reads the same in both).
- **The face colour gives the family at a glance:**

  | Family | Face | Rim |
  |---|---|---|
  | Spins and identity | ink | gilt |
  | Wardrobe | crimson | gilt |
  | Personal effects | oak | brass |
  | Moments | midnight blue | silver |
  | Passes | ink, with a laurel wreath | gilt |
  | The subscription | ink, with a laurel wreath | silver |

- **Pack size:** a brass plate at the foot of a pack's medallion carries its count ("x5").
- **How they're made:** the same pipeline as [[Icon-Set]].
  - `art/ui/hud/make_shop_icons.py` draws each design as a relief and material map.
  - `blender_shop_icons_render.py` renders it as real PBR geometry in Cycles: brushed brass, gilt, hammered iron,
    glossy enamel, wax, bone, parchment, and emissive flame.
  - `finish_shop_icons.py` writes `art/group-upload-shop/NHShop<Name>.png` at 512 px.
- **The sheet:** [contact sheet](img/shop-icons-contact.png).

## Developer products (buy as often as you like)

Rows marked **(new)** are not built yet. The others exist in `Config.Shop`.

### Spins: rerolls, super cheap
| Product | Gives | Price | Icon | Design |
|---|---|---|---|---|
| Clan Spin | 1 clan spin | **R$ 5** | `ClanSpins1` | a gilt-edged crimson clan shield (chevron and three stars) inside two chasing reroll arrows |
| Clan Spins x5 | 5 | **R$ 19** | `ClanSpins5` | three shields, blue, crimson and green |
| Clan Spins x15 | 15 | **R$ 49** | `ClanSpins15` | five shields fanned |
| Height Spins x3 | 3 | **R$ 9** | `HeightSpins3` | a notched brass measuring rod, an ivory student and a gilt up-and-down arrow |
| Height Spins x10 | 10 | **R$ 25** | `HeightSpins10` | the same, "x10" |
| Race Spins x3 | 3 | **R$ 15** | `RaceSpins3` | a moon-chalk crescent cradling a crimson faceted gem in a brass bezel, six race marks round it |
| Race Spins x10 | 10 | **R$ 39** | `RaceSpins10` | the same, "x10" |
| Variant Spins x3 | 3 | **R$ 9** | `VariantSpins3` | three hex gems (blue, gold, crimson): the same race, another variant |
| Variant Spins x10 (new) | 10 | **R$ 25** | `VariantSpins10` | the same, "x10" |
| Trait Spins x5 | 5 | **R$ 9** | `TraitSpins5` | three gilt-framed tarot cards with star and moon devices |
| Trait Spins x15 (new) | 15 | **R$ 25** | `TraitSpins15` | the same, "x15" |
| Bloodline Bundle (new) | 3 race + 3 variant + 5 trait | **R$ 25** (R$ 33 apart) | `BloodlineBundle` | the crescent and gem, a tarot card, two variant gems, a "BUNDLE" plate |
| Identity Bundle (new) | 5 clan + 3 height | **R$ 22** (R$ 28 apart) | `IdentityBundle` | the clan shield and the measuring rod |
| Name Change | 1 rename after enrolling | **R$ 25** | `NameChange` | the open school register, a bone quill across it, a crimson wax seal |

### Wardrobe (owned for good)
| Product | Price | Icon | Design |
|---|---|---|---|
| Vamp Cape | **R$ 49** | `CapeVamp` | black cape with a bat-wing hem, a crimson lining, a tall pointed collar, and a silver collar band with a crimson clasp |
| Rogue Cape | **R$ 49** | `CapeRogue` | an oxblood leather cape with a hood and a brass clasp |
| Fur Cape | **R$ 69** | `CapeFur` | an oak-brown cape with a thick ivory fur collar |
| Ravenfeather Cloak (new) | **R$ 59** | `CloakRavenfeather` | a torn black cloak with a hem of feather tips and a silver bat at the throat |
| Moonlit Shroud (new) | **R$ 69** | `CloakMoonlit` | a midnight-blue cloak with a silver lining, a crescent clasp and scattered stars |
| Ashen Wool Cloak (new) | **R$ 59** | `CloakAshen` | an iron-grey wool cloak with a ring brooch |
| Midnight Prefect set (new) | **R$ 79** | `OutfitMidnightPrefect` | an ink blazer with a gilt crest badge on a brass hanger |
| Crimson Gala set (new) | **R$ 99** | `OutfitCrimsonGala` | a long oxblood coat with black lapels and a gilt bat pin |
| Graveyard Formal set (new) | **R$ 79** | `OutfitGraveyardFormal` | an iron-grey waistcoat with bone buttons and a crimson tie |
| Eye-Glow Tint (new) | **R$ 29** | `EyeGlowTint` | an ivory eye with a glowing iris over five tint swatches |

### Personal effects (owned for good)
| Product | Price | Icon | Design |
|---|---|---|---|
| Hellfire Deck (new) | **R$ 39** | `DeckHellfire` | a crimson deck with a gilt star and a flame trail |
| Moonwake Deck (new) | **R$ 59** | `DeckMoonwake` | a midnight-blue deck with a crescent and a moonlight trail |
| Bone Rail Deck (new) | **R$ 49** | `DeckBoneRail` | a ribbed ivory deck on brass trucks |
| Coffin Lunchbox (new) | **R$ 15** | `LunchboxCoffin` | an oak coffin-shaped tin with a brass handle and latch |
| Bat Tin Lunchbox (new) | **R$ 19** | `LunchboxBatTin` | an iron lunch tin with a silver bat |
| Crimson Bento (new) | **R$ 25** | `LunchboxCrimsonBento` | a crimson lacquer box tied with gilt bands |
| Crimson Glass Lantern skin (new) | **R$ 25** | `LanternCrimsonGlass` | an iron lantern with crimson glass and a live flame |
| Bat-Wing Umbrella skin (new) | **R$ 25** | `UmbrellaBatWing` | a black umbrella with a scalloped bat-wing edge |
| Raven Thermos skin (new) | **R$ 25** | `ThermosRaven` | an ink thermos with silver caps and a raven |
| Phone Wallpapers (new) | **R$ 15** | `PhoneWallpapers` | a phone showing a moonlit night sky |
| Phone Case (new) | **R$ 19** | `PhoneCase` | a crimson case with the clan crest |
| Midnight Bell Ringtones (new) | **R$ 15** | `PhoneRingtones` | the brass school bell ringing out |
| Gothic Study decor (new) | **R$ 49** | `DecorGothicStudy` | an oak desk with leather books and a lit candle |
| Moonlit Loft decor (new) | **R$ 79** | `DecorMoonlitLoft` | an arched iron window with the moon in it |
| Crimson Court decor (new) | **R$ 129** | `DecorCrimsonCourt` | a gilt-framed crimson throne-chair, button-tufted |
| Gear Tint (new) | **R$ 15** | `GearTint` | wrapped knuckles over four tint swatches |

### Moments (used up, seen by everyone in the server, at most once every 2 minutes)
| Product | Price | Icon | Design |
|---|---|---|---|
| Lantern Release (new) | **R$ 25** | `MomentLanternRelease` | paper lanterns with live flames rising into the night |
| Crimson Fireworks (new) | **R$ 39** | `MomentCrimsonFireworks` | crimson and gold bursts over the lit bell tower |
| Midnight Bell Shout-out (new) | **R$ 10** | `MomentShoutout` | a brass bell over an unrolled scroll |

- **Gifts:** any cosmetic above can be bought for a classmate (pick them in Classmates).
- **Spins can't be gifted:** they are paid random items, and the receiver wouldn't have seen the odds.

## Gamepasses (one-time, account-wide)
| Pass | What it gives | Price | Icon | Design |
|---|---|---|---|---|
| Extra Students | Two more save slots (4 and 5) | **R$ 149** | `PassExtraStudents` | two students on the slot picker's iron plinths, silver and gilt, "+2" |
| Tailor's Pass | 6 saved outfits per student, recolour owned pieces, open the Wardrobe anywhere outside class and combat | **R$ 99** | `PassTailor` | open steel shears with gilt ring handles under a gold tape measure |
| Collector's Dorm | A loft above your room, and a 12-spot trophy shelf (trophies still earned) | **R$ 129** | `PassCollectorsDorm` | two oak shelves of gilt cups and four crest plaques, with a brass key |
| Gothic Emotes | 8 emotes: a bow, a curtsy, a candle prayer, perching on a desk, a slow clap, a cloak flourish, and more | **R$ 79** | `PassGothicEmotes` | two masquerade masks, crimson sorrowful and ivory smiling, on a gilt ribbon |
| Gramophone | Play Night FM aloud near you, from the game's own tracks only | **R$ 59** | `PassGramophone` | an oak gramophone with a gilt horn and two notes |
| Prefect's Seal (VIP) | A wax-seal crest by your name, a gold name in the list, the Prefects' Lounge (cosmetic), and a cape | **R$ 199** | `PassPrefectsSeal` | a crimson wax seal pressed with a crown over a crescent, oxblood ribbon tails |

All passes have the laurel wreath round the medallion, so they read as a step up from a product.

## Subscription and private servers

- **Night Society (monthly, R$ 99).**
  - **Each month:** one exclusive cosmetic (a cape, cloak or deck) that you keep for good.
  - **Each month:** 5 clan spins and 3 height spins, with the same odds panel.
  - **The whole time you subscribe:** a "Society" seal.
  - **Never included:** Yen, EXP or power.
  - **Icon:** `NightSociety`, a raven before a moon-chalk crescent with a silver key.
  - **Roblox rules:** the minimum is R$ 49, benefits can't be revoked mid-term, there are no tiers, and a Robux price
    can change at most every 60 days.
- **Private servers (R$ 25 a month).**
  - **Who they suit:** study groups, roleplay, filming and clique nights.
  - **What already works:** the server directory doesn't list private servers. Roblox Plus subscribers get them at no
    cost, and you're still paid for their time there.

## Before anything goes on sale (required)

- **Create every product and pass** on the Creator Dashboard, upload the icons (`art/group-upload-shop/`), and paste
  the ids into `Config.Shop`. I'll find the ids on your profile, as for every upload.
- **Odds for every outcome, before purchase.**
  - **Shown today:** the clan register lists each rarity's share and its clans, the Height tab lists height odds, and
    the Bloodline tab lists race odds.
  - **Missing:**
    - Each clan's own odds: the rarity share divided by its clans, or "Odds for each clan listed below: X%".
    - Variant odds (85 / 12 / 3).
    - Trait odds.
    - A plain note on pity: "the 40th spin without Epic or better is guaranteed Epic or better".
- **The restricted-region check.** Where `PolicyService` says paid random items are restricted, the spin products are
  hidden or blocked with a message. Free starting spins still work there, and a free way to earn spins gives those
  players something: a spin for each rite passed and each report card with an A.
- **Spins must stay fair at these prices.** At R$ 5 a spin, nearly everyone can reroll toward a rare race or clan.
  - **Races:** that's fine while races are sidegrades (moon bonuses alternate, and the hunger penalties apply to every
    race).
  - **Clans:** clan perks must stay small or cosmetic. If a clan or race ever gives a real edge, cheap rerolls become
    pay-to-win.

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
- **The Wardrobe:** a "Tailor" section with owned and buyable pieces side by side, previewed on your own student.
- **The phone:** a new **Robux shop** app (a black-lacquer catalogue with a wax-seal "Buy" stamp) for personal effects,
  moments, gifts and passes.
- **Where you'd see the thing anyway:** the dorm for decor, the skate rack for decks, and the kit for lantern skins.
  Each has one small "more styles" button. No pop-ups and no "limited time!" pressure.

## Build notes

- **Purchases:** keep the one `ProcessReceipt` (`Services.Player.Purchases`). Every new grant is another `Kind` in
  `Config.Shop`.
- **Account-wide ownership:** passes, and (your call) cosmetics, need a small account-level store beside the per-slot
  saves. Today nothing is account-wide.
- **Odds:** one shared odds panel in the UI kit for every spin product, with the restricted-region switch.
- **Art still to build:** the new items each need their 3D piece, in the usual PBR pipeline: the cloaks, outfit sets,
  decks, lunchboxes, kit skins, decor sets and emotes. Their icons are ready now.
- **Prices:** these are the owner's "cheap" targets. Roblox reads the real price from each product, and Managed
  Pricing can test them later.

## Your calls

- **Robux cosmetics: per student or the whole account?** I'd make them account-wide and keep spins per student.
- **Moments in the live game:** keep them, or are server-wide effects too loud?
- **Night Society:** have a subscription at all?
- **Stat respec:** I'd leave it out of the shop, or make it earnable only.
- **The Back Lot farm:** it gives about ¥3,600 and 10,800 EXP an hour with no cap (Delinquent audit G). It undercuts
  every Yen price.

## Where I'd start

1. **Make the Spin Shop sellable:** create the products with the new prices and icons, add the full odds panel and the
   restricted-region check, plus a free way to earn spins.
2. **Extra Students and the Tailor's Pass:** the two passes most players want, with no new 3D art.
3. **Capes, cloaks and outfit sets** in the Wardrobe's Tailor section, plus gifting.
4. **Personal effects:** decks, lunchboxes, kit skins and phone styles.
5. **Collector's Dorm, Gothic Emotes, the Gramophone and Prefect's Seal.**
6. **Moments, Night Society and private servers.**

Sources (Roblox creator docs, checked 2026-11-13): [paid random items](https://create.roblox.com/docs/production/monetization/paid-random-items),
[subscriptions](https://create.roblox.com/docs/production/monetization/subscriptions.md),
[monetization overview](https://create.roblox.com/docs/en-us/production/monetization),
[managed pricing](https://create.roblox.com/docs/production/monetization/managed-pricing),
[Roblox Plus](https://create.roblox.com/docs/en-us/production/monetization/roblox-plus.md).
