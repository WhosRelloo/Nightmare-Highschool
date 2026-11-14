# Hunger and the body: expansion concept

**Date:** 2026-11-13. **Status:** the owner picked **phases 1 and 2**, which are built in NH Combat Test as Hunger 1.0
(see [[Hunger]]). The "Your calls" went unanswered, so the build uses each call's recommended option. Phases 3 to 6 are
still concepts.

The owner asked: "create an expansion concept on hunger for the races and how they can become fat, skinny, etc. from
not eating. For any UI I want them to be unique, on theme, high quality with pbr, and animated."

Standing rules this keeps:
- No blood or gore.
- Race is never picked by the player.
- Everything saves through ProfileService `PlayerData`, written only by the server.
- Art is uploaded under group 15981569.

Related: [[Races-and-Bloodlines]], [[Racial-Grips]], [[Body-Types]], [[Training]], [[NPC-Builds]], [[QOL-Kit]],
[[Inventory-QOL-Concepts]], [[Combat-Audit-and-Concepts]] (section D).

## What was read

- **Races:** [Races-and-Bloodlines](Races-and-Bloodlines.md) and the design spec
  ([2026-10-30-races-design](superpowers/specs/2026-10-30-races-design.md)). This covers the six races, their families,
  sub-race boosts, passives and moons, and **Races 1.2's hunger**.
- **Feeding:** [Racial-Grips](Racial-Grips.md): The Kiss, Eat Body, Maul, Soul Siphon, Exorcism and Hunter's Stake.
  Each one heals and feeds race hunger through `Features.RaceAction`.
- **Food:** `Config.Items`, which holds the 53 foods and drinks: 31 heals (Onigiri 15 up to Raven's Roast 125) and 22
  buffs (Ramune, Hot Cocoa and so on). Also:
  - the concession stand (1.8) and the lunch trays you eat down (1.95.0);
  - the Bell Wheel snack wheel and Best food (1.96.0);
  - the taste book and feeding students (2.2.0).
- **Bodies:**
  - [Body-Types](Body-Types.md): ten R6 bodies on four builds, Average, Skinny (Lean), Conditioned and Heavy.
  - [Female-Body](Female-Body.md).
  - [NPC-Builds](NPC-Builds.md): seeded by clique.
  - [Training](Training.md): per-area `Areas`, `Appearance.SetArea`, the paths Average / Conditioned / Heavy / Lean.
- **Save:** `Studio/live/pg/PlayerData.luau`, and `PlayerData.Training` with its **reserved `Fed` field** (0 to 100,
  already sanitised in `Config.Training.Sanitize`).
- **Clock:** 5 real minutes is one game hour, so one game day is 2 real hours.
- **Owner's earlier "things to avoid"** ([Gameplay-and-NPC-Concepts](Gameplay-and-NPC-Concepts.md)): no
  eating-disorder gossip.

## What already exists, and what that means here

| Already there | What it means for this concept |
|---|---|
| **Races 1.2 "Hunger"** (`PlayerData.Lineage.Hunger`, `RaceHunger`) only ever **goes up**, from kills and grip finishes, and opens the rites at 25 and 100. It's a progress meter, not a need. | The new need can't share the name. This doc calls the new need **Hunger** and the old meter by each race's own word, under **Bloodline** (Blood, the Hunt, Feeding, Souls, Resolve, Faith). It's the first *Your call*. Feeding still fills both. |
| **Training's plan:** "Food steering toward Heavy or Lean is phase 2", and `Training.Fed` is reserved. The training spec already says Conditioned comes from training while fed, Heavy from eating a lot and lifting heavy, and Lean from reps on an empty stomach. | This concept **is** that phase 2. It uses the same paths, the same per-area meshes and the same `Appearance` code. It doesn't add a second body system. |
| **The ten body meshes per area** (CharacterMeshes inside the R6 boxes, the same joints and animations) | The look is already R6-safe. Builds come from swapping meshes, never from scaling parts. |
| **Food heals over time** and shares a 12 s "full" cooldown | That cooldown is the natural eating rate limit, so it stays. |
| **No combat stamina meter.** Stamina exists only inside Training's burnout sets. | "Stamina" here means sprint speed and Training's burnout stamina. A combat stamina bar is out of scope. |

## The core loop

1. **Hunger** (0 to 100, *how fed you are now*) falls while you play and rises when you eat your race's food.
2. **Reserve** (−100 to +100, hidden, *where your body is heading*) builds while you're stuffed and drains while you're
   hungry.
3. When Reserve crosses a line, **one body area moves one step**: torso first, then legs, then arms. This is
   telegraphed a day ahead and limited to one change per area per real day.
4. **Training** decides *which kind* of change it is. Training while fed builds muscle (Conditioned), not mass.

Doing nothing special is always safe. A student who eats a lunch meal and a snack or two each play hour stays **Fed**
and keeps their body as it is.

### Hunger bands

| Band | Hunger | What it does (all races; race twists below) |
|---|---|---|
| **Stuffed** | 90 to 100 | Food coma for 2 min: −6% sprint. Soreness clears 2x faster. Reserve **+1 a minute**. |
| **Full** | 70 to 90 | Well fed: Training XP x1.1, soreness clears 1.5x faster. Reserve +0.25 a minute. |
| **Fed** | 40 to 70 | Neutral. Reserve slowly settles toward 0. |
| **Peckish** | 20 to 40 | Neutral. Reserve slowly settles toward 0. This is where the offline floor sits. |
| **Hungry** | 5 to 20 | −4% damage, posture recovers 20% slower. Your stomach growls, which raises the chance to be spotted by 5% for a moment. Reserve **−1 a minute**. |
| **Starving** | 0 to 5 | −8% damage, the race's low-health heal is off, class EXP −10%. Monsters frenzy (see the race table). Reserve −1.5 a minute. **Never any health loss or death.** |

**Decay:** about 33 an hour of play (0.55 a real minute), so Full to Peckish takes about 1.5 hours. A lunch meal is +40,
a stand snack +10 to +20, and a drink +4.

| Food size | Examples | Hunger |
|---|---|---|
| Small snack (heals up to 15) | Senbei, Grave Crisps, Onigiri, Popcorn | +8 |
| Snack (heals 16 to 40) | Melon Bread, Nikuman, Dango, Taiyaki, Curry Bread | +14 |
| Big snack (heals 41 to 80) | Yakisoba Bun, Cup Ramen, Pumpkin Soup, Night Bento | +24 |
| Lunch meal (`Lunch = true`) | Katsu Curry, Shoyu Ramen, Witching Hour Stew | +40 |
| Drinks and sweets (buffs) | Ramune, Hot Cocoa, Strawberry Milk, Bat Gummies | +4 |

This lives as `Hunger` on each item in `Config.Items`, with the defaults worked out from `Heal`. It's tunable per item.

## Per-race hunger

Every race fills the same 0 to 100 bar. What fills it, how fast it falls, and what an empty one does are the race's own.
**All feeding stays gore-free:** the grips already have no blood (2.6.0 removed the red bursts), and nothing new shows
blood, wounds or flesh.

| Race | Feeds on | Plain food | Decay | Race twist |
|---|---|---|---|---|
| **Human** | cafeteria food | 100% | 1x | **Steady:** the plainest race. *Superhuman:* a fast metabolism, 1.2x decay, but Training XP while Fed rises to x1.15. |
| **Priest** | food, and **fasting** | 100%. Holy Water Lemonade counts as a snack (+14). | 1x | **Fasting:** while Peckish (20 to 40) a Priest is *Fasting*, with **+4% damage vs the undead** on top of Consecrated (*Grand Priest* +5%, *Pope* +6%). Fasting *is* the play, a reason to stay hungry on purpose. The vessel marks the band with a gilt notch. Hungry and Starving still apply below 20. |
| **Vampire** | **The Kiss** (grip): +45. **Sanguine Tonic** (new): +25. | 25%: they taste it (the taste book still counts) but it barely sates. | 1.25x by day, 0.75x at night | **Crimson moon:** no decay all night. *Nobleblood / Royal Vamp:* a refined palate, the Tonic gives +30 / +35. **Starving frenzy:** +6% damage, but the eye glow (Night sight's crimson) comes on by itself, and students who see it get uneasy (see *School and social*). |
| **Werewolf** | anything meaty: x1.5 (Nikuman, Yakitori, Karaage Set, Mystery Meat Loaf, Raven's Roast, Shepherd's Pie). **Maul** (grip): +35. A beast kill in the woods: +20. | sweets x0.5 | 1x. **2x on a full moon** (the Hunt). | The hardest race to make Heavy: Reserve gain is x0.6, and its training leans Conditioned. *Bloodmoon / Alpha:* full-moon decay x2.2 / x2.4, but meaty food x1.7 / x1.9. **Starving frenzy:** +6% damage and +5% sprint, but social prompts (talk, offer, introduce) are off until fed. |
| **Ghoul** | **Eat Body** (grip): +55. **Mystery Meat Loaf**: +25, the one cafeteria food a ghoul keeps down (a lore joke the menu already sets up). **Charnel Tins** (new): +20. | 0%. Ordinary food tastes of ash; the taste book still counts it. | 0.6x: **the Gorge**. Ghouls eat rarely and big. | A full ghoul (Stuffed) gets **−4% damage taken** for the whole band, on top of Grave Hunger. *Ghast / Crypt Lord:* decay 0.5x / 0.4x. **Starving frenzy:** +8% damage, Grave Hunger's low-health heal is off, and nearby NPC students back away. |
| **Wraith** | **Soul Siphon** (grip): +40. **Warmth:** standing within 10 studs of a lit candle, lantern or hand lantern (QOL kit) gives +2 a minute; being unseen in a crowd of 4+ students gives +3 a minute (feeding on unease, never shown). | 0%. Wraiths don't eat (the taste book stays closed to them, or counts smell; *Your call*). | 1x. **0.5x on a new moon.** | Wraiths don't gain or lose weight. Their body state is **Fade** instead (see below). *Revenant / Hollow King:* the warmth radius is 14 / 18. |

**What's new, all small:**
- **Sanguine Tonic:** a squat black-glass bottle with a crimson wax seal; the liquid is never shown. Sold only at night,
  by a **night vendor** at the boiler yard, for ¥60. Drinking it uses the existing drink clip.
- **Charnel Tins:** a dented tin with a stencilled skull and a grave-moss label. Sold by the same vendor for ¥45. The tin
  is opened and eaten with a fork and no contents shown, the same way the lunch trays end on clean dishes.
- **A turn** (the bite, `Lineage.Turn`) sets Hunger to 60 and Reserve to 0, so a new monster doesn't start starving.

### How it ties into what exists

- **Racial grips** stay the monsters' main meal. They already call `Features.RaceAction`, so one extra line feeds the
  new Hunger. They still feed the Bloodline (rite) meter exactly as today.
- **Passives:** Starving turns off the race's healing passives (the Ghoul's low-health heal, the Vampire's heal on a
  kill). Full keeps them as they are, so being fed is the normal state and starving is the cost.
- **Moons:** the crimson moon stops Vampire decay, the full moon doubles Werewolf decay, and the new moon halves Wraith
  decay. The moon banner can mention it ("The Hunt runs hot tonight").
- **Combat section D** (being built in another session; this concept only adds hooks, no numbers of its own):
  - **Race-flavoured fists (D.17):** the Vampire's "sip of health on the ender" also gives +2 Hunger. Other races' ender
    effects don't feed.
  - **Heat meter (D.18):** a **Hungry or Starving monster builds Heat 15% faster** (the hunt sharpens you). Humans and
    Priests get nothing from hunger here; a Fasting Priest gets +10%.
- **Race damage** goes through the existing effect keys (`DamageDealt`, `DamageVsUndead`, `DamageTaken`). The hunger
  bands are one more effect source, "Hunger", in `Progression.Effects`, beside "TasteBook" and the snack buff.

## Body: builds that drift

### Which builds, and what moves them

The paths are Training's: **Average, Lean, Conditioned, Heavy**. Steps I and II exist as meshes for every area and
gender. Steps III and IV wait on new meshes (`MeshStepsBuilt = 2`).

| You... | Reserve | What changes |
|---|---|---|
| stay Stuffed a lot and don't train | rises to +60 | one area moves **toward Heavy**: Average → Heavy I → Heavy II (Stocky/Curvy → Heavy/Plus) |
| stay Hungry a lot and don't train | falls to −60 | one area moves **toward Lean**: Average → Lean I (Lean/Petite) |
| train while Full or Fed | spent by the set | as today: Conditioned XP. Being Full adds x1.1. |
| train **heavy reps** while Stuffed | spent at 2x | the set's XP pushes that area along **Heavy** (Training's "mass" path) instead of Conditioned |
| train **burnout sets** while Peckish or Hungry | spent at 2x | the set's XP pushes that area along **Lean** ("wiry") |
| eat normally (Fed and Peckish) | settles to 0 | nothing: the body holds |

**The rules that keep it fair:**
- **One step at a time, one area at a time,** and at most **one change per area per real day** (UTC, like Training's
  Fresh).
- **Order:** the torso changes first, then the legs, then the arms. Mixed bodies (a Heavy torso on Lean legs) are
  allowed, as Training already allows.
- **Going back:** Heavy steps back down toward Average only while you're Hungry. Lean steps back up only while you're
  Full. Fed holds what you have, so **there's no upkeep chore**.
- **Muscle is sticky:** Conditioned never drifts from eating alone. Only a full real day spent Starving takes one
  Conditioned step back, and training gives it back at the next change.
- **Telegraphed:** a change shows on the Tailor's Gauge (below) **one real day ahead**, with the area's needle quivering
  and a ↗ or ↘ chip. You can always turn it around.
- **Never offline:** Reserve doesn't move while you're away.
- **This needs one code change:** `Appearance.SetArea` never lowers an area today. Drift needs a new server-only
  `Appearance.ShiftArea(player, area, path, step)` that can step down or switch path. Training keeps calling `SetArea`
  as it does now.

### The look stays R6-safe

- **Meshes, not scaling:** builds are the existing CharacterMeshes per area (`NHBodyMesh`). No part's `Size`, Motor6D,
  HRP or joint changes, so every combat clip, grip and the crouch-kneel plays exactly as before. R15 body scaling isn't
  used; on R6 it would break the rig.
- **Hitboxes don't grow:** `HitBox` uses fixed boxes, not body meshes, so a Heavy student isn't easier to hit. That's
  the fairness line.
- **Measured fits to re-check on the deepest bodies** (Heavy is 1.22 deep, Plus and Curvy 1.19 to 1.23):
  - racial grip weld offsets: hands on a deeper chest;
  - capes (`NH_TorsoFit`);
  - Training's loads, which already fit by `DEPTH`;
  - the clothing atlas, which the 1.69.0 import already passed.
- **Height** never changes from food.

### Wraith Fade (instead of weight)

A Wraith's body doesn't gain or lose; it **fades**:

| Hunger | Fade | Look | Effect |
|---|---|---|---|
| 40+ | Solid | as now | none |
| 20 to 40 | Thin | body parts 0.15 transparent, wisps double | −5% chance to be spotted |
| 5 to 20 | Fading | 0.3 transparent, a frost edge, footsteps silent | −10% chance to be spotted, −8 max health |
| 0 to 5 | Hollow | 0.45 transparent, the cold wisps trail | −15% chance to be spotted, −15 max health, no Unseen EXP |

This is R6-safe: the server only sets the parts' `Transparency` (the face, hair and race looks follow it), so
everyone sees the same Fade and no joint or mesh changes. Fade is
a trade, not only a penalty: a hungry Wraith is a better sneak and a worse fighter. It returns the moment they feed.

### What each build changes (stats)

These come on top of what Training already gives Conditioned (Arms damage, Torso health and posture, Legs sprint).
Each step is a side-grade. Every row stays under one Common gear piece's budget, the same line the snack buffs keep.

| Area | Lean I / II | Heavy I / II |
|---|---|---|
| **Torso** | −3 / −6 max health, −4 / −8% chance to be spotted | +4 / +8 max health, −4 / −8% guard strain |
| **Arms** | grips finish 4 / 8% faster (racial grips and the B grip, so a lean monster feeds faster) | +6 / +12% posture damage on heavies, body blows and the clinch's knee |
| **Legs** | +2 / +4% sprint, +10 / +20 starting stamina in Training's burnout sets | −15 / −30% knockback taken (shoves, wall splats and enders travel less), −2 / −4% sprint |

- **New effect keys:** `KnockbackTaken`, `PostureDamage` and `GripSpeed`. The rest use existing keys (`MaxHealth`,
  `Stealth`, `PostureGain`, `SprintSpeed`).
- **Effect source:** the bonuses show in the Report Card as their own source, **"Build"**.

### School and social

- **Lunch:** eating a lunch meal at the lunch tables during Lunch (11:25 to 12:00) with two or more of your clique
  nearby is a **shared meal**: +10 Hunger and +1 clique standing, once a day.
- **Class:** Full or Fed is *brain food*, +5% class EXP. Starving is −10%, and the teacher may say "Eat something before
  my class."
- **Feeding other players:** the 2.2.0 "Offer" prompt also works on a Hungry player. It feeds them, and it's a social
  gesture (+1 standing between your cliques, once a day).
- **Starving monsters are noticed.** A starving Vampire's eyes glow and a starving Ghoul's students back away. Students
  who notice spread a rumour line ("Did you see their eyes?"). A hall monitor who sees glowing eyes in school hours
  watches you more closely (+25% spot chance for 2 game hours). There's no write-up just for being hungry.
- **Dorms (Homes):** a **mini-fridge** in your room stores up to 6 foods. Eating at your own table gives +5 Hunger on top
  ("breakfast").
- **NPC students:** keep their seeded clique builds (2.3.0). They don't drift. They can be seen eating at lunch.

**Tone rule (owner's earlier "no eating-disorder gossip"):** NPCs and UI comment on **hunger**, never on **body size**.
- **Never on screen:** "fat" or "skinny", jokes about a body, or praise for not eating.
- **Builds use the game's names:** Lean, Average, Conditioned, Stocky, Heavy, Petite, Curvy, Plus and so on.
- **The drift moment is framed as the school tailor refitting your uniform**, which is neutral, on theme and kind.
- **The Priest's fast is a rite of faith,** shown as a holy fast, not as weight loss.

## Starvation and overfeeding: fun, not a chore

- **No death and no health drain from hunger, ever.** The worst a Starving student gets is the band's penalties, and
  monsters get a frenzy that's partly a reward.
- **Offline:**
  - Hunger falls at a quarter of the rate while you're away, and **never below 35** (Peckish).
  - If you logged off below 35, it stays where it was.
  - You never come back Hungry from being away.
- **Reserve and builds never move offline.**
- **New students** start at 70 (Full), Reserve 0.
- **A fair minimum, for players who ignore all this:** Peckish is neutral, and decay is slow enough that one lunch
  meal per game day (two real hours) keeps you out of Hungry. Ignoring food costs a little damage in fights, never your
  character.
- **Overfeeding** is capped by the existing 12 s "full" cooldown, and Stuffed's food coma (−6% sprint for 2 min) is the
  only short-term cost.
- **Best food** (the snack wheel's middle) picks for health when you're hurt and for hunger when you're not. "You're not
  hurt." becomes "You're not hungry." only when both are full.
- **Settings > Interface > Hunger:** "Show the vessel always / when it changes / never". Growls can be muted.

## Save data and anti-exploit

**Save (ProfileService `PlayerData` only):**
- A new `PlayerData.Body = { Hunger, Reserve, LastTick, Changed = { [area] = day }, Pending = { [area] = { path, step,
  day } }, Fade, Fast }`, written through a new `Data.UpdateState` action **`SetBody`** and sanitised by
  `Config.Body.Sanitize`.
- `Training.Fed` (reserved, always 0 today) is migrated into `Body.Hunger` once and then ignored.
- Mirrored to the client only as character attributes (`Hunger`, `HungerBand`, `Reserve` rounded to its direction,
  `Fade`), the same way `RaceHunger` is.
- The body itself still saves where it does now: `Appearance.Areas`, through `SetAppearance`.

**Anti-exploit (the server decides everything):**
- **The client never sends a hunger value.** Eating goes through `Inventory.Use`, which is already server-side and
  rate-limited by the 12 s "full" cooldown. Grips feed from `Features.RaceAction` on the server.
- **Decay** is worked out from server `os.time()` deltas (`LastTick`), clamped to the session, so changing the client
  clock or freezing the client does nothing.
- **Warmth for Wraiths** is checked on the server every 10 s against real light sources (tagged lights that are on) and
  server-side detection.
- **Caps:**
  - Reserve can move at most 60 in a real day.
  - Each area can change once per real day.
  - The Sanguine Tonic and Charnel Tins have a daily buy limit (`DailyLimit = 6`), like the Prank Kit.
- **The look guard** already throws away any client-sent `Areas`; `ShiftArea` is server-only, like `SetArea`.
- **Admin desk:** a Hunger and Reserve row under Build, logged like `SetBuild`. **Test bridge:**
  `Body(name, "Get" | "SetHunger", n | "SetReserve", n | "Tick", minutes)`. Both are server-only and gated as they are
  today.

## UI: unique, on theme, PBR, animated

Every piece is made like the Training set, the Bell Wheel and Thornrose:
- **Rendered:** in headless Blender (Cycles), as real displaced geometry with full PBR materials (black iron, brass,
  gilt, pewter, silver, glass with transmission, enamel and wax).
- **Lit:** with the HUD's light rig (a warm key from the top left, a soft box, a cool fill and a candle rim).
- **Finished:** supersampled 2x, with edges bled and resized premultiplied (no dark fringe).
- **Uploaded:** under the group, and preloaded when the HUD builds.
- **Motion:** runs in one render loop, as the Bell Wheel does. Reduce Flashing turns pulses into fades.

### 1. The vessel (HUD hunger meter)

A **reliquary** about 84 px tall, sitting on the left cap of the Thornrose health bar like a gem in a setting:
- **The case:** a black-iron Gothic case with a pointed arch, a quatrefoil base and a gilt finial.
- **The window:** a glass front showing the race's contents.
- **The plate:** an enamel band plate under it names the band in the race's words.

| Race | Contents behind the glass | Finial and trim | Band words (Stuffed → Starving) |
|---|---|---|---|
| Human | warm amber broth, steam curling off the top | a brass lunch bell | Stuffed · Full · Fed · Peckish · Hungry · Starving |
| Priest | holy water with pale gold motes rising, and a gilt notch on the Fasting band | a silver sun-cross | Sated · Blessed · Fed · **Fasting** · Hungry · Faint |
| Vampire | **no liquid**: a faceted garnet heart in smoked black glass. Its inner light is the level, and it beats. | bat-wing filigree | Gorged · Sated · Fed · Thirsting · Parched · Starving |
| Werewolf | a silver moon disc that fills like a phase, crescent to full | claw-scratched iron and fur tufts | Gorged · Full · Fed · Prowling · Ravenous · Starving |
| Ghoul | an acid-green grave flame on a wick over an ember bed. The flame height is the level. | a grave-lantern cap and a chain | Gorged · Full · Fed · Gnawing · Hollow · Frenzied |
| Wraith | a cold blue soul-wisp in a bell jar. Brightness and solidity are the level. | frosted silver | Warm · Kindled · Steady · Thin · Fading · Hollow |

**Art pieces per race:**
- the case;
- the contents strip, drawn tall and clipped to the level, with a surface or crest sprite riding on top;
- the glass front, with highlights in an additive layer;
- the glow sprite;
- a frost or crack overlay;
- the band plate (9-slice).

That's six races x 6 pieces, plus the shared notch, splash and mote sprites: about 40 images.

**Motion:**
- **Idle:**
  - the surface breathes ±1 px on a 2.4 s cycle;
  - motes, steam or embers drift;
  - the candle-rim highlight slides across the glass every 6 s;
  - the Vampire's heart beats at 0.8 Hz, and at 1 Hz at night.
- **Moving:** sprinting sloshes the broth and holy water; the surface tilts with your speed on a damped spring. The
  wolf's moon and the ghoul's flame lean instead.
- **Eating:**
  - the food's own icon (the snack wheel's socket art) arcs into the top of the vessel in 0.35 s;
  - a splash ring flares;
  - the level rises with an ease-out over the food's eat time, matching the heal-over-time;
  - "+14" drifts up in the kit's title font.
  - For a grip feed, the race's own grip VFX colour streams into the vessel from the body instead.
- **Band change:** the enamel plate turns over like the clock's moon icon (a 0.3 s flip) to the new word.
- **Hungry:**
  - an iron "growl" shake, 2 px for 0.3 s, about every 40 s, with a soft stomach sound;
  - frost or hairline cracks creep in from the case's corners.
- **Starving:**
  - the glow pulses with a 0.9 Hz heartbeat;
  - a soft vignette darkens the screen edges;
  - for monsters, the frenzy flares the vessel in the race colour once, the moment it starts.
  - Under Reduce Flashing, the pulse becomes a steady dim glow.
- **Resting:** while you're Fed and nothing changes for 20 s, it fades to 40%, and it wakes on any change (like the EXP
  strip).

### 2. The Tailor's Gauge (body-state readout)

A new **Body** page in the Report Card (L), beside Training's page:
- **Left:** your own character in 3D, as in the Locker.
- **Right:** three **tailor's dials**, one each for Torso, Arms and Legs:
  - brass faces engraved LEAN · AVERAGE · HEAVY, with a gilt CONDITIONED notch above the middle;
  - a blued-steel needle with a thimble tip;
  - a cloth tape measure curled round the rim.
- **Under each dial:** the area's build ("Torso · Stocky (Heavy I)") and its effect.
- **When a change is pending:** a chalk line marks it ("Let out tomorrow" / "Taken in tomorrow").

**Motion:**
- the needles swing on a damped spring when the page opens;
- a pending change makes the needle **quiver** and a ↗ or ↘ chalk arrow draw itself in;
- hovering a dial lifts it and unrolls its tape a little.

The same dials appear as a 3-dial **mini gauge** under the vessel for 5 s whenever Reserve tips toward a change. So the
warning is on the HUD too, not only in a menu.

### 3. Feedback moments

- **The refitting** (a build changes):
  - a gilt **tape measure** snaps around the changed area of your character (a ring sprite on a Beam, 0.4 s);
  - chalk tailor's marks swirl round it, and the mesh swaps under the swirl;
  - a pewter-framed card slides up: "Your uniform's been let out: Torso → Stocky", with the before and after figures
    cross-fading in two small 3D views.
  - Nearby players see the tape and chalk (`NHFx`, FireNear 40), like Training's step-up.
- **Wraith Fade steps:** frost blooms across the body and fades into the new transparency over 1 s, with a cold chime.
- **Frenzy:**
  - **Vampire and Werewolf:** the eye glow flares on;
  - **Ghoul:** the vessel's flame roars up.
  - A one-line banner in the race's voice: "The hunger has you."
  - This happens once per Starving spell, not on a loop.
- **Fasting (Priest):** gold motes rise off your shoulders and a soft choir note plays as you enter the band.
- **Shared meal:** a gilt place-setting icon pops over the table with the clique's crest.
- **The snack wheel:** each socket's count pill gets a small Hunger chip (+14). For races that don't sate on it, food
  sockets show "ash" grey with the hunger chip struck through, so a ghoul sees at a glance that only the Meat Loaf works.

## Phases

| Phase | What | Size |
|---|---|---|
| **1. The need** | `Config.Body` (bands, races, sub-race and moon factors), `Services.Features.Body` (decay, offline floor, feeding from `Inventory.Use` and `RaceAction`), `PlayerData.Body` + `SetBody`, the band effects as the "Hunger" source in `Progression.Effects`, the test bridge and the admin row. A stand-in vessel from the UI kit. | **M** |
| **2. The vessels** | Six race vessels plus the shared sprites, rendered in Blender and uploaded. All the motion above, the band plates, the snack wheel chips, the settings toggle. | **M** |
| **3. Drift** | Reserve, `Appearance.ShiftArea`, the order, caps and telegraph rules, Training steering (heavy reps to Heavy, burnout to Lean), the Build stats and the three new effect keys, the Tailor's Gauge page, the refitting moment. Re-check grip welds, capes and loads on the deepest bodies. | **L** |
| **4. Race specials** | Priest fasting, the Vampire's Tonic and the night vendor, Ghoul Charnel Tins and the Gorge, the Werewolf's full-moon burn and meaty foods, Wraith warmth and **Fade**, the frenzies, the section D hooks. | **M** |
| **5. School and social** | Shared meals, brain food in class, offering food to players, monsters noticed by students and monitors, the rumour lines, the dorm fridge, teacher and student lines about hunger (never about bodies). | **M** |
| **6. The Map** | Port to the Map place once the Map has the body types and the Training areas. | **S** |

**Where I'd start:** Phase 1 and 2 together, so the owner can feel the need before any body ever changes. Then 3,
because that's the "fat, skinny" part, and it's the biggest.

## Your calls

1. **Names:** the new need is **Hunger** and the old rite meter becomes each race's word under **Bloodline**
   (recommended), or the new need is called **Appetite** and the old meter keeps "Hunger"?
2. **Aiming for a build:** can players steer to Heavy or Lean on purpose by how they eat (recommended, since it's
   telegraphed and reversible), or only as a side effect? The training spec suggested side effects only.
3. **Hunger's floor:** no health loss ever (recommended), or a slow drain to 50% max health while Starving?
4. **Offline floor:** decay at a quarter of the rate, never below 35 (recommended). Or pause hunger entirely offline?
5. **Ghoul and Wraith with plain food:** Ghouls get 0% (ash) and Wraiths don't eat (recommended), or 25% for both so
   they can snack in a pinch?
6. **The Vampire's Tonic and Ghoul's Charnel Tins from a night vendor:** OK as new items? They're opaque containers;
   nothing red or fleshy is ever shown.
7. **The frenzy:** keep the Starving monster frenzy (a damage boost with social costs), or make Starving a plain
   penalty for everyone?
8. **Wraith Fade:** OK instead of weight changes, with a Wraith's stealth growing as it fades?
9. **The tailor framing:** OK for the build change moment ("Your uniform's been let out")?
10. **Steps III and IV:** new Heavy and Lean meshes for steps III and IV (a bigger, slower art job), or stop at II?
11. **NPC students:** keep their seeded builds (recommended), or let regulars at the stand drift too?
