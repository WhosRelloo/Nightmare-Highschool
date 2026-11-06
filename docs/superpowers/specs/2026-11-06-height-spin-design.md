# Height spin: design

**Status:** design, for the owner's review (2026-11-06). Nothing is built yet.
**Owner's asks:** "create a good height system for the game that works with everything we currently have. (Concept first)"; on the concept: "I like it. Make the height system a spin system within those ranges."

## The idea

Every student has a height. Like race and clan, it's **rolled by the server, never chosen**. A new student gets a free first roll on a reel, and more height spins come free with a new student or from the Spin Shop. Each race has its own height range, and where you land in that range has a rarity: the middle is Common, and both very short and very tall are rare.

Height is **cosmetic only**. It never changes reach, health, speed or damage, so fights stay fair.

## The roll

A roll picks a number **p** between 0 and 1, evenly. `p` is your place within your race's range: 0 is the shortest that race gets, 1 the tallest. Your height is `lerp(race min, race max, p)`. The band `p` falls in gives the rarity:

| p | Band | Rarity | Share |
|---|---|---|---|
| under 0.01 | Pint-Sized | Legendary | 1% |
| 0.01 to 0.05 | Tiny | Epic | 4% |
| 0.05 to 0.15 | Small | Rare | 10% |
| 0.15 to 0.30 | Short | Uncommon | 15% |
| 0.30 to 0.70 | Average | Common | 40% |
| 0.70 to 0.85 | Tall | Uncommon | 15% |
| 0.85 to 0.95 | Very Tall | Rare | 10% |
| 0.95 to 0.99 | Towering | Epic | 4% |
| over 0.99 | Giant | Legendary | 1% |

- **Both ends are rare.** Short and tall are equally hard to get, so neither is the "right" roll.
- **No repeats:** a spin never lands in the band you already have.
- **Pity:** after **30 spins in a row** without Epic or better, the next spin is Epic or better (either end).
- **Odds shown:** the reel shows each band's share, as the clan reel does.

## The ranges (by race)

Heights are a scale on today's body: 1.00 is today's size, shown as **5'9"**. Inches are `scale × 69`, rounded.

| Race | Range | Shortest to tallest |
|---|---|---|
| Human | 0.92 to 1.08 | 5'3" to 6'3" |
| Priest | 0.92 to 1.08 | 5'3" to 6'3" |
| Vampire | 0.95 to 1.10 | 5'6" to 6'4" |
| Werewolf | 1.00 to 1.12 | 5'9" to 6'5" |
| Ghoul | 0.90 to 1.04 | 5'2" to 6'0" |
| Wraith | 0.96 to 1.10 | 5'6" to 6'4" |

- **A race spin keeps your place.** The save stores `p`, not inches, so a Towering Human who becomes a Werewolf is still Towering, just in the Werewolf range. Race spins don't cost or give height spins.
- The ranges and bands are data (`Config.Heights`), so they're easy to tune.

## Spins and the shop

- **A new student:** a free first roll (the reveal) plus **2 height spins**.
- **Existing students** (saves from before this): a free first roll the next time the slot loads, with the reveal. Until then they stay 5'9".
- **Spin Shop:** two new products, **Height3** and **Height10** (3 / 10 height spins), with placeholder price hints R$ 49 / 149 and `ProductId = 0` until the owner creates them, like the others. Grants go through `Services.Player.Purchases`, once per receipt.
- **Free in Studio** while testing, like clan and race spins.

## Where players see it

- **Name & Clan tab:** a **Height** reel under the clan reel. It shows the result as `6'2" · Very Tall` in the rarity's colour, plus "1 in 10". Epic and better land with the same rarity burst as clans, and the camera pulls back to full body so you see yourself grow or shrink. A **Spin height** button with "You have N", and the pity bar.
- **The Spin Shop:** a Height group with "You have N".
- **Slot cards:** the height next to the name, e.g. "Mara Ravenscar · 6'2"".
- **In school:** you simply are that height. The student card (phone / Students) shows it.

## How the body is scaled

- Players use the classic R6 body (`StarterPlayer.StarterCharacter`), which has no body-height sliders (those are R15 only). So the **whole character is scaled evenly** with `Model:ScaleTo(scale)`, as some NPC rigs already are (0.9).
- Scaling evenly keeps faces (the SurfaceGui strips on the head), clothes, hair, accessories, tails, capes and race looks in proportion. Stretching only the legs and torso would warp the faces and clothing, so it's not used.
- **The server applies it** whenever the character is rebuilt: spawn, slot load, respawn, after the look is applied, after a race spin, and in and out of Werewolf form. The client never sets it.
- **First build step:** a quick check that `ScaleTo` on this R6 rig keeps the face strips, accessories, the sway controllers (hair, cape, tail) and the animations correct. If anything breaks, it's fixed there before anything else is built.

## Saving

- `PlayerData.Identity.Height = { P, Band, Spins, Pity }`, through Identity's `SetIdentity` action (ProfileService only).
- The server rolls `p`. A client can only ask to spin. A value from a client is never trusted.
- Read-only attributes on the player: `HeightScale`, `HeightBand`, `HeightText` (e.g. `6'2"`).

## Making everything height-aware

Each item is checked in a play-test at the shortest and tallest heights.

| System | What changes |
|---|---|
| Spawn / respawn / race spin / Werewolf form | the scale is re-applied after each rebuild |
| Main menu avatar, creator preview, talk cinematic | cameras frame the head, not a fixed height |
| Seats and class desks (`Features.Seats`) | hips and thighs settle for the scaled body; `Unclip` still works |
| Vault | its knee / waist / head heights scale with the body |
| Skateboards | the deck offset stays right on a scaled body |
| Downed carry, the ghoul's grab | hold positions scale with both bodies |
| Football / soccer | catching and kicking reach scale with the body |
| Overhead names and tags | they follow the head |
| Combat | check how hits are detected. If a bigger body is easier to hit, hits are measured from the body's centre instead, so height stays fair |
| NPC students | each gets a height from its name (the Human range), so the school looks varied; their sitting and walking code already measures their legs |

## Build order

1. The `ScaleTo` check (above).
2. `Config.Heights`, the roll, spins, pity and saving in `Services.Player.Identity`, the shop products and grants.
3. Applying the scale on the server, at every rebuild.
4. The Height reel, the shop group, slot cards and the student card.
5. The height-aware pass (the table above) and NPC heights.
6. Play-tests at the shortest and tallest heights, then the records (changelog, Discord post, docs, vault).

## Not in this

- Body build (slim / broad). It could come later on the same scaling.
- Any gameplay effect of height.
