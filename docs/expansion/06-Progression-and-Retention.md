# 06. Progression and Retention Framework

## 1. Principles
- **Reward skill, effort, discovery and participation**, never time spent alone.
- **No punishment for breaks:**
  - **Already in place:** hunger has an offline floor; discipline points decay.
  - **New:** streaks pause rather than reset after 3 missed days and resume where they stopped.
  - **New:** dailies don't stack pressure; three a day at most.
- **No daily login rewards.**
- **No paid shortcuts to progression or story** (the Spin Shop stays cosmetic and rerolls only).

## 2. Goal ladder

| Horizon | Goals (all from existing or specified systems) | Typical length |
|---|---|---|
| **Short term** (a session) | Attend 1-2 classes and get a grade. One dare or job. A rumour heard or a scene seen. One relationship step. A training set. A phone arcade best. One Photography assignment. | 20-60 min |
| **Medium term** (a week to a month) | Class levels 3-5. A report-card B+. A sports rank-up. A clique membership rank. A Standing Path tier. One investigation case. Faction rank. Weekly competitions. A rival resolved. | 1-4 weeks |
| **Long term** (months) | Campaign chapters. All five paths at top tier. The Ring Championship. A full bestiary. All 24 Archive pages. A 3-term yearbook. Legacy marks after level 50. Graduation (deferred). | 2+ months |

## 3. Identity: "you are becoming somebody"
- **How it's visible:**
  - **On you:** path titles and wardrobe unlocks (02 §3.1), and the Permanent Record.
  - **Your room and things:** the trophy wall and the dorm room state.
  - **In the world:** NPC lines and the Gazette.
- **Recognition scales with tier:**
  - **Tier 2:** NPCs nod to you.
  - **Tier 3:** students ask you for things (they become quest givers for small favours).
  - **Tier 4:** your name appears in the Gazette and on the PA.
  - **Top tier:** a portrait in the Archive's "Notables" wall.

## 4. Honours (the achievement structure)
Honours are **earned entries in the Permanent Record**, not a separate system or bar.

**Structure:**
- About 60 Honours across 8 groups:
  - Academics
  - Conduct
  - Athletics
  - Combat
  - Society
  - Supernatural
  - Story
  - Secrets (hidden)
- Each Honour is a condition read from existing data; only the earned date is stored (`Progress.Honours[id] = day`).
- Some Honours grant a title or a cosmetic. Most are recognition only.

**Examples:**

| Group | Honour |
|---|---|
| Academics | Perfect Term (all subjects A or better) |
| Conduct | Never Late (30-day streak) |
| Athletics | Triple Club (rank Starter in all three sports) |
| Combat | Untouchable (win a duel without being hit) |
| Society | Friend of the Ink (Trusted with Wren) |
| Supernatural | Night Owl (existing title), Bestiary Complete |
| Story | Chapter titles |
| Secrets (hidden) | Didn't Answer (stayed silent at the 3 AM bell) |

## 5. Balance guidelines

**Yen economy (current):**
- A lesson pays ¥6-20, a quest ¥15-40, a beast ¥24-60.
- Kit items cost ¥80-180; the Katana costs ¥1000.
- New rewards stay inside these bands.

**EXP:**
- New content uses `Progression.Award` with the existing keys and categories.
- An hour of varied play should give about the same EXP whatever activity it's spent on, so no single activity is the "farm".
- The Back Lot farm (audit finding J) gets a diminishing-returns cap.

**Weekly competitions:**
- **Placements:** top 3 get a title for the week (the Superlatives pattern), and everyone who plays gets a participation stamp in the Record.
- **No exclusive power.**

**Collectibles:** 24 Archive pages, each with lore and placed with intent. No hundreds of pickups.

**Time gates:** only fiction-driven ones:
- night-only areas
- moon nights
- class periods
- the weekly cadence of competitions

No timers exist just to stretch playtime.

## 6. Session hooks that respect the player
- **The phone's "Today" card:**
  - what's on now, e.g. "Chemistry in 3 min, R103"
  - one rumour
  - the next path step
  - an open case lead

  It doesn't nag.
- **Returning after a break:** a short "While you were away" Gazette page, built from the Broadcast log of notable events.
