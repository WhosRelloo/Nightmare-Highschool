# Races, Bloodlines and Evolution: design (NH Combat Test)

**Status:** approved design, not built yet. Numbers are a balance **proposal**; they live in config and are meant to be tuned.
**Sources:** the concept doc (Human / Priest / Vampire, sub-races by spin, 3 kill-based race tiers, "don't get bit! Or.. maybe you do") and the user's 2026-10-30 brief (add Werewolf, Ghoul and Wraith; race cosmetics modelled in Blender; a gothic-castle, Castlevania-like *feel* with original designs only; race passives, balanced; racial skills later).

## Goals
- Six races, all rolled by the server. Players never choose a race (standing rule).
- Each race looks distinct: race-only cosmetics and skin palettes, unlocked in stages.
- Each race plays a little differently: a passive with a strength and a drawback, scaling with tier.
- A race evolves through three tiers by filling a race-specific **hunger** and finishing a **rite**.
- Humans and Priests can be **turned** by a monster player's bite, and they choose whether to accept.

## Not in scope
- Racial skills, movesets and classes (the doc's Priest and Vampire moves, Tainted, Dracula's Descendent…). They come later and plug into race and tier.
- Transformation abilities. Only the existing transformed *looks* (the `Transformation` attribute) are hooked.
- Curing a monster back to human. The race spin still rerolls.

## Approach
Extend the existing **Lineage** system rather than build a parallel one:
- One roll, one save (`PlayerData.Lineage` via `SetLineage`), one place in the UI.
- Lineage was built by the UI-kit session. It hands race code over to the race work before any edit, so two sessions never edit the same files.
- New logic goes in small modules with one job each (below). `ReplicatedStorage.Lineage` stays the single config for races.

## 1. Roster

| Race | Roll | Sub-races (spin rarity: weight) | Tier I → II → III |
|---|---|---|---|
| Human | 40% | Human (Common 90) / Superhuman (Rare 10) | Townsfolk → Hunter → Slayer |
| Priest | 25% | Priest (Uncommon 85) / Grand Priest (Epic 12) / Pope (Legendary 3) | Acolyte → Exorcist → Saint |
| Vampire | 15% | Vampire (Uncommon 85) / Nobleblood (Epic 12) / Royal Vamp (Legendary 3) | Fledgling → Night Gentry → Elder |
| Werewolf | 10% | Werewolf (Uncommon 85) / Bloodmoon (Epic 12) / Alpha (Legendary 3) | Cursed → Moonbound → Feral Lord |
| Ghoul | 6% | Ghoul (Rare 85) / Ghast (Epic 12) / Crypt Lord (Legendary 3) | Starveling → Grave-eater → Charnel Lord |
| Wraith | 4% | Wraith (Rare 85) / Revenant (Epic 12) / Hollow King (Legendary 3) | Whisper → Shroud → Dirge |

- **Families:** Vampire, Ghoul and Wraith are **Undead**. Werewolf is **Cursed**. Vampire, Werewolf, Ghoul and Wraith together are **Monsters**. Human and Priest are **Mortal**.
- **Sub-races** multiply the race passive's numbers: base ×1.0, Rare/Epic ×1.15, Legendary ×1.3. The doc's "more moves / more classes" benefits arrive with racial skills.
- **Existing saves:** current races and sub-races are untouched. Only new rolls can land on the new races.

## 2. Passives (balance proposal)
Values are for Tier **I / II / III**, before the sub-race multiplier. They are applied through the same effect pipeline as stats, clan perks and traits (`Progression.Effects` → character attributes → `Downed.ApplyDamage`, `DamageLogic`, `Quests.Stealth`, `Humanoid.MaxHealth`, EXP awards).

| Race | Passive name | Strengths | Drawback |
|---|---|---|---|
| Human | **Stubborn Will** | +8 / 10 / 12% all EXP · −4 / 6 / 8% guard strain · Slayer (III): +8% damage vs Monsters | none, but no night power, and can be turned |
| Priest | **Consecrated** | +6 / 9 / 12% damage vs Undead · −6 / 9 / 12% damage taken from Undead · +5% class EXP | −5% damage at night |
| Vampire | **Night Blood** | +6 / 9 / 12% damage at night · kills and executions heal 4 / 6 / 8% max health | −5% damage by day |
| Werewolf | **Moon-Blooded** | +10 / 15 / 20 max health · +5 / 8 / 10% damage at night (×1.5 on a full-moon night) | +10% chance to be spotted while sneaking |
| Ghoul | **Grave Hunger** | −5 / 8 / 10% damage taken · regenerates 1 / 1.5 / 2 HP/s below 30% health · executions heal 6 / 9 / 12% max health | −10% class EXP |
| Wraith | **Unseen** | −10 / 15 / 20% chance to be spotted · −6 / 9 / 12% guard strain · +6 / 9 / 12% night EXP | −10 max health |

**Balance rules:**
- Every race has one survival lever and one damage or utility lever, plus a drawback (Human's drawback is having no night power).
- Night favours Monsters, day favours Mortals. Priests counter Undead, and Human Slayers counter all Monsters.
- No passive goes above 16% at Legendary Tier III (12 × 1.3 ≈ 15.6%).

**New effect keys** (added to `Config.Progression.Active` and read in `Downed.ApplyDamage`):
- `DamageVsUndead`, `DamageVsMonster`, `DamageTakenFromUndead`, `DamageByDay`, `HealOnKill`, `FullMoonNightPower`.
- The race of each side is read from the read-only `Race` attribute.
- **Full moon:** every 4th in-game night (`SchoolClock`). It's shown in the clock HUD.

## 3. Looks
**Starter set at Tier I, grander versions unlocked at II and III.** The server checks every choice against race, sub-race and tier, and clamps skin colour to the race palette (in `Appearance.Sanitize`).

| Race | Starter (I) | Tier II | Tier III | Skin |
|---|---|---|---|---|
| Vampire | Sharp ears: Pointed, Swept | Long Swept ears | Elder ears (taller, finely ridged) | **Pale or dark tones only:** 5 pale (porcelain, alabaster, bone, ash-ivory, moon-grey) and 4 dark (umber, ebony, night-brown, obsidian) |
| Werewolf | Wolf ears: Upright, Tufted · Tail: Brush, Bushy, Bobbed · fur colour (6) | Shaggy tail · Torn ear | Silver moon-marked tail and ears | Normal tones (the transformed form keeps its own look) |
| Ghoul | Ghoul uniform (when wearing the school uniform) | Stitch straps (shoulder and jaw) | Grave shroud scarf | **Ghoul palette only:** grave grey, corpse green, bruise violet, ashen, bile, cellar blue |
| Wraith | Cold breath + thin cold wisps (pale blue) | Wisp colour: grave green, violet | Frost-tipped fingers | Normal tones |
| Human / Priest | none this pass (Priest keeps the Chapel cross pin look style) | none | none | Normal tones |

- **Wraith subtlety:** breath is a short puff every 4–6 s. Wisps are 2–3 thin particles per hand and shoulder, half as visible by day.
- **3D cosmetics are modelled in Blender:** ears, tails, stitch straps and the shroud.
  - Low poly (under 2k triangles each), single material, PBR textures, matching the hand-made ornate style.
  - Exported as FBX into the repo's `art/races/` folder. **User step:** import each FBX through Studio's 3D Importer (no API key is used). A checklist ships with the files.
  - Fitted as Accessories on the R15 head and torso attachments and stored in `ServerStorage.NHRaceCosmetics`.
- **Fur colour** tints the ear and tail meshes (`VertexColor` or `Color`).
- **Ghoul uniform:** shirt and pants templates (torn, stitched, stained versions of the uniform), made with the clothing pipeline. It's worn instead of `NHUniformShirt` and `NHUniformPants` when the race is Ghoul and the uniform is on.
- **Saving:** `PlayerData.Lineage.Cosmetics = { Ears, Tail, Fur, Wisp, Extras = {} }`, written only by the server.

## 4. Evolution: hunger + rite
- **Hunger meter per race:**
  - Vampire **Blood:** night kills, grip executions.
  - Werewolf **the Hunt:** kills at night, double on full moon.
  - Ghoul **Feeding:** executions, double for grip executions.
  - Wraith **Souls:** kills, plus executions while unseen.
  - Human **Resolve:** kills, double vs Monsters.
  - Priest **Faith:** kills of Undead, attending chapel-themed lessons.
- **Thresholds** use the doc's kill numbers: **25 hunger** unlocks the Tier II rite, **100** the Tier III rite. One ordinary kill = 1 hunger before bonuses.
- **Rites** are short quests in the existing quest system: one objective chain, race-themed, at night where it fits.
  - Example: the vampire Tier II rite *"The Font Below"*: go to the chapel undercroft after midnight and drink at the font. The full rite list is written during Phase 3.
  - Finishing a rite raises `Lineage.Tier`, plays an evolution moment (ember burst, tier title card) and unlocks that tier's cosmetics.
- **Tier source changes** from "computed from kills on join" to "earned and saved".
  - Existing saves keep their current kill-based tier, so nobody drops.
  - `RaceTier` stays the public attribute.
- **Saving:** `PlayerData.Lineage.Hunger` (number) and `Lineage.Rites = { [2] = bool, [3] = bool }`.

## 5. Turning (the bite)
- **Who:** a Monster player at **Tier II or higher**, gripping a **downed Mortal** (Human or Priest), gets a **Turn** option beside Execute.
  - Vampire and Ghoul bite. Werewolf bites only at **night**. Wraith uses a soul-touch.
- **Victim choice:** "Accept the bite? You become a <Race> (Tier I) and lose your <old race>." **Accept** or **Refuse**, 15 s, refused by default.
  - **Accept:** race becomes the biter's base race (common sub-race), Tier I, hunger 0. Spins and traits are kept.
  - **Refuse:** the grip continues as normal (no execution forced).
- **Limits:** no turning in duels or safe zones. One successful turn per biter per in-game day. Rate-limited, and the server checks everything.
- The biter gains hunger (+5).

## 6. UI: the Bloodline tab
- **Creator nav:** Look / **Bloodline** / Name & Clan / Spin Shop. In school it opens from the Student Record.
- **Contents:**
  - race crest and name (gothic ironwork frame), sub-race, tier title
  - the existing race spin reel and odds
  - the cosmetics picker (locked items show "Tier II" / "Tier III")
  - the passive in plain words (generated from config, like clan perks)
  - the hunger meter and the next rite
  - traits (moved here from the Wardrobe's Lineage tab, which then points here)
- **Look tab:** the skin picker only shows the race's palette. Custom HEX is clamped server-side.
- **UI audit standard:** 18 px minimum design size, contrast at least 3:1.

## Units (each with one job)
| Unit | Side | Job |
|---|---|---|
| `ReplicatedStorage.Lineage` (extended) | shared | races, sub-races, families, tiers, palettes, cosmetics list, passives, hunger sources, rites (data only) |
| `Lineage.Passives(race, sub, tier)` | shared | returns the effect table, so the UI text and the server apply the same numbers |
| `Services.Races.Cosmetics` | server | validates cosmetic choices, attaches accessories, particles and ghoul clothing, clamps skin |
| `Services.Races.Evolution` | server | hunger awards from game signals, rite unlocks, tier-ups, save |
| `Services.Races.Turning` | server | bite offer, victim prompt, race change |
| `Controllers.Gui.Bloodline` | client | the tab |
| `Progression.Effects` (patched) | server | merges race passives with stats, clan and traits |
| `Downed.ApplyDamage` (patched) | server | the new vs-race and day/full-moon keys |

**Remotes:** `NHRace.Get`, `NHRace.SetCosmetic`, `NHRace.Updated`, `NHRace.TurnOffer` / `TurnAnswer`. All are rate-limited and validated.

## Build order
1. **Phase 1:** roster and odds, families, passives (+ new effect keys), race skin palettes, the Bloodline tab with the spin and passive text. *Playtest:* roll each race via the test bridge; check palette clamping, passive numbers in a hit, and night/day.
2. **Phase 2:** Blender cosmetics, the user's import step, then the cosmetics service, the picker, wraith particles and the ghoul uniform. *Playtest:* screenshot each race with each starter cosmetic, and check that a locked cosmetic is refused.
3. **Phase 3:** hunger, rites, tier-ups, the evolution moment, the bite. *Playtest:* hunger from real kills, one full rite, and the bite accepted and refused (two players).

**Test bridge commands:** `SetRace(name, race, sub)`, `GiveHunger(name, n)`, `CompleteRite(name, tier)`, `Bite(biter, victim)`.

## Risks
- **Mesh import is manual.** Phase 2 waits on the user's import step.
- **Balance is unplayed.** All numbers are in config, and the doc for this feature records them as a proposal.
- **Shared files** (Lineage, Wardrobe, Appearance, Downed): the UI-kit session hands them over first. Every edit is announced to the other sessions.
