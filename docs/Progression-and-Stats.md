# Progression and Stats: NH Combat Test

**Status:** built and playtested in Studio (one player). The numbers are a **proposal**, so tune them in `Config.Progression`.

The concept doc asks for:
- a Verdant Moon-style stat system
- kill-count race tiers (3 per race)
- 1.2× EXP for school missions during school hours

This adds EXP, levels, three stats, and real effects for the clan perks and lineage traits, which were "planned" text until now.

## Levels and EXP
- **Levels:** 1 to **50**. EXP to the next level is `100 + 45 × (L − 1)^1.35`, so 100 to reach level 2, 145 for level 3, and about 3,400 at the top.
- **Stat points:** each level gives **3**.
- **Where EXP comes from:** existing game signals, so no system had to change to send it.

| Source | EXP | Kind |
|---|---|---|
| Attend class on time / late | 40 / 20 | Class |
| Pass a lesson (not practice) | 30 + 0–30 by grade | Class |
| Main quest / side quest (or the quest's `Rewards.Exp`) | 150 / 80 | Quest |
| Win a duel / beat the Ring champion | 40 / 120 | Combat |
| Execute an NPC / a student (grip) | 20 / 40 | Combat |
| Join a faction / reach a new rank | 50 / 60 | Social |
| Introduce yourself to a stranger | 5 | Social |
| Slip away from a hall monitor | 15 | Stealth |

- **Multipliers:** every award is multiplied by `SchoolClock.GetExpMultiplier()`, which is **1.2× in school hours** as the concept doc says, and by your EXP bonuses for that kind of EXP.
- **Level-up:** a notification ("Level 7! +3 stat points"), an ember burst on your character, and the public `Level` attribute updates.

## Stats (spend points in your Student Record)
| Stat | Per point |
|---|---|
| **Might** | +1.5% damage dealt |
| **Grit** | +2 max health, −0.4% guard strain (posture fills slower) |
| **Wits** | +1% class EXP, +0.8% quest EXP, −0.6% chance to be spotted while sneaking |

Each stat caps at 60.

## What perks and traits do now
Effects from stats, your clan perk and your lineage traits are added together, then applied where the game already does the work. Each clan's perk text in Name & Clan is now generated from these real effects.

| Effect | Where it's applied |
|---|---|
| Damage dealt / taken | `Downed.ApplyDamage`, which every hit goes through. Uses the character attributes `NH_DamageDealt` and `NH_DamageTaken`. |
| Guard strain | `DamageLogic` posture gain (`NH_PostureGain`) |
| Being spotted | `Quests.Stealth` detection rate (`NH_Stealth`) |
| Max health | `Humanoid.MaxHealth` (health keeps its percentage) |
| Class / quest / combat / social / stealth EXP, EXP in school hours, EXP at night | EXP awards |
| Damage at night (Moonlit, Duskmere…) | refreshed every second from the school clock |
| Healing when badly hurt (Second Wind, Holloway) | regenerates below 30% health |
| Daily second chance (Fated) | once per in-game day, you get back up from downed (not in duels) |

**Not active yet:** walk speed, parry window, shop prices, popularity, awareness and clue sense. They're stored and shown with "(planned)", and wait for the systems they need.

## Where you see it
- **Student Record** (**L**, or the top bar's new book button). It's built from the UI kit's `StatSheet`.
  - Your name, level, an EXP bar, points to spend, race and tier, and takedowns.
  - The three stats, each with a **+** button and what your points give.
  - **Bonuses:** your clan perk and each trait in plain words.
- **EXP strip:** a subtle hairline just under the health bar.
  - Clock-tick marks every tenth, and candle gold warming to crimson with an ember at the tip.
  - Your level as a Roman numeral by the kit's diamond knob. The knob glows crimson while you have points to spend.
  - It rests faint and wakes when you earn EXP, with "+34 Lesson" drifting up.
- **Students list and nameplates:** students you know show "Lv 7", and "Lv 7 · rank" on nameplates.

## Saving and code
- **Saving:** `PlayerData.Progress = { Level, Exp, Points, Stats = { Might, Grit, Wits }, FatedDay }`, via the action `SetProgress`, per student.
- **Server:** `Services.Player.Progression` (`Award`, `Spend`, `Sheet`, `Effects`, `Apply`).
  - Remotes: `ReplicatedStorage.NHProgress` (`Get`, `Spend` rate-limited, `Updated`).
- **Client:** `Controllers.Gui.Progress`.
- **Config:** `ReplicatedStorage.Config.Progression` (curve, stats, EXP table, clan effects, `Describe`).
- **Test bridge:** `GiveExp(name, amount, kind?)`, `Progress(name)`, `SpendStat(name, stat, n?)`.

## Verified (Studio playtest, one player)
- **New student:** Level 1, 0/100. The clan perk (Harlow, +5% quest EXP) and traits (Bookworm +8% class EXP; Quick Feet walk speed shown as *planned*) appear on the sheet.
- **Level-ups:** 500 quest EXP became **525** with the perk, going from Level 1 to **Level 4** with 9 points. It was saved, and still there after a restart.
- **Real EXP source:** executing a training dummy with grip gave +20 EXP through `Downed.OnExecuted`.
- **Spending points:** **+** pressed by key twice on Might and once on Grit gave Might 2 (`NH_DamageDealt` = 1.03) and Grit 1 (**max health 102**).
- **Damage bonus:** a 10-damage hit from that student dealt **10.30**.
- **Record and strip:** the record opens with **L** and from the top bar. The strip shows the level numeral, wakes and shows "+120" when EXP comes in, then fades back.

**Fixed during the test:**
- The game's keybind package marks every key as handled, so L (like Tab) is now read directly.
- **CONTINUE focus bug.** CONTINUE on a student who had never saved a look played the new-student clan reveal in the background, and its name box then grabbed the keyboard in school, swallowing every key. Now:
  - CONTINUE never plays the reveal.
  - The register only takes focus while it's visible, and lets go when hidden.
  - The menu waits up to 3 s for the "signed" flag on slow loads.
- Effect text showed "+0%" for empty stats, and small values rounded to "−0%".

**Not tested:**
- EXP from attendance, lessons, quests, duels and factions in a live play-through. These are hooked to their signals and code-reviewed only.
- The Fated revive and the low-health regeneration.
- Two players seeing each other's level.

**Race tiers:** the tier is stored by Lineage (UI kit session) from total takedowns (0 / 25 / 100) when a save loads. Updating it mid-session as kills come in is left to Lineage.
