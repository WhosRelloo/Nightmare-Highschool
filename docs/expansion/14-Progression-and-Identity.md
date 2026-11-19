# 14. Progression and Identity (Expansion Phase 3)

**Status:** approved 2026-11-18. **2.31 shipped** (plan: `docs/superpowers/plans/2026-11-18-standing-paths.md`; its
deltas are §10 items 9 to 13). **2.32 shipped** (no separate plan: the owner reshaped the look during the build;
deltas 14 to 18). **2.33 shipped** (deltas 19 to 22). 2.34 is next.

**Sources:** doc 02 §3.1 to §3.3, doc 06 §3, §4 and §6, doc 07 (`Progression`, `Phone`, `Homes`), and doc 08 Phase 3.
This spec makes them buildable. §10 lists where it differs from them.

**The owner's answers (2026-11-18):**
- **The Permanent Record is M.** Today's Report Card panel becomes its first tab, "Student".
- **I model the path art:** the uniform variants, the path accessories and the new trophies.
- **The Today card is a widget on the phone's home screen.**
- **The release split** is option 1: four releases, data first and art last.

**Releases:** each one is playable and tested before the next starts.

| Release | Name | Builds |
|---|---|---|
| **2.31** | Standing Paths | `Config.Paths`, the Paths evaluator in `Progression`, `Progress.Paths`, `Progress.Tally`, titles, NPC recognition |
| **2.32** | The Permanent Record & Honours | M becomes the school file (9 tabs), `Progress.Record` (Notable Entries), `Config.Honours` (the first 30), `Progress.Honours` |
| **2.33** | Trophies | new trophy sources and models, the 12-slot dorm trophy wall, the Trophy Case tab with 3D turntables |
| **2.34** | Path wardrobe & the Today card | 3 uniform variants and 3 path accessories (modelled), unlocked by tiers; the phone's Today widget |

---

## 1. Rules for the whole phase

- **No new HUD bar.** Progress shows in the Record, in titles, in what you wear, in your room and in how people talk
  to you.
- **Granted on the server, once.** Tiers, Honours, trophies and unlocks are granted by the server, and each only once.
- **Nothing drops.** A path tier, once reached, stays. A bad week can't take it back.
- **Reads existing data.** Tiers and Honours are conditions on data the game already keeps. The only new saved data is:
  - the highest tier per path
  - the day each Honour was earned
  - the Notable Entries log
  - five counters that the existing signals didn't keep
- **Art:** PBR in the house style, with no Seal icon. 3D models are built on PaintRigV3 and are never blocky. New UI is
  built from the kit's art and styles.
- **Places:** NH Combat Test only. The Map place stays untouched.

## 2. Architecture

```
existing signals ──> Progression.Paths.Check(Player) ──> Progress.Paths (highest tier)
 (EXP awards, class results,       │                     ├> Reputation.AwardTitle (the tier's title)
  attendance, quests, ranks,       │                     ├> Moments banner, Record entry
  duels, beasts, escapes,          │                     └> (2.34) the tier's wardrobe unlock
  showdowns, join)                 └> Honours.Check ──> Progress.Honours[id] = day ──> Record entry
Progress.Tally (5 new counters) <── Duels.Won, Duels.ChampionDefeated, Beasts kills, HallMonitor.Escaped, CliqueShowdowns wins
Gui.StatsPanel (M) <── Progression.Sheet + Record tabs (all read-only, built on the server)
Phone home <── Today widget (Phone.Today: Schedules, Rumours, Paths, Quests)
```

- **The evaluator lives in `Progression`** (doc 07). It listens to the signals Progression already uses for EXP, plus
  the four below. It never edits the systems it reads.
- **One check per event, debounced.** Many signals in a frame cause one check. A check is cheap: about 20 reads of a
  profile already in memory.
- **New counters** (`Progress.Tally`), each fed by a signal that already fires:
  - `DuelWins`: from `Duels.Won`
  - `Champion`: from `Duels.ChampionDefeated`
  - `Beasts`: from the Beasts kill reward
  - `Escapes`: from `HallMonitor.Escaped`
  - `Showdowns`: wins, from `CliqueShowdowns`

  They count from this release on (§10).

## 3. Release 2.31: Standing Paths

### 3.1 `ReplicatedStorage.Config.Paths`
Five paths. Each tier is a small set of AND conditions; where a line says "or", either side passes. The first tier of
each path is where everyone starts. The plan confirms each number against the live data (for example the reputation
scale); a changed number is recorded in §10.

**Academic** (subjects: History, Mathematics, Chemistry, English; class level 1 to 5; grades A+ 97, A 90, B 80, C 70)

| Tier | Name | Conditions |
|---|---|---|
| 1 | Freshman Nobody | (start) |
| 2 | Recognized Student | 2 subjects at level 2+; best attendance streak 3+ |
| 3 | Honor Student | 3 subjects at level 4+; a delivered report card averaging B or better; best attendance streak 10+ |
| 4 | Academic Elite | all 4 subjects at level 5; a report card averaging A or better; Academics reputation 50+ |

**Social**

| Tier | Name | Conditions |
|---|---|---|
| 1 | Unknown | (start) |
| 2 | Recognized | 5 classmates met |
| 3 | Popular | 12 classmates met; Popularity 25+; Friendly or better with 2 cliques |
| 4 | Influential | a faction rank of Member or higher; Popularity 50+; Respected by 1 clique |
| 5 | School Legend | Inner Circle in a faction; Popularity 80+; all 24 classmates met; a weekly superlative won |

**Combat** (takedowns = `Kills` + `NPCKills`)

| Tier | Name | Conditions |
|---|---|---|
| 1 | Beginner | (start) |
| 2 | Street Fighter | 5 takedowns |
| 3 | Enforcer | 25 takedowns; 3 duel wins; Intimidation 25+ |
| 4 | Notorious | 75 takedowns; a clique showdown won; 3 beasts; Intimidation 50+ |
| 5 | Feared | 150 takedowns; the Ring's champion beaten; Intimidation 80+ |

**Athletic:** exactly your sports club rank (Rookie → Starter → Varsity → Captain). It is mirrored, never
recomputed. Not being in a club counts as Rookie.

**Supernatural**

| Tier | Name | Conditions |
|---|---|---|
| 1 | Unaware | (start) |
| 2 | Uneasy | Orientation done (you've seen the empty desk), or 1 beast |
| 3 | Initiated | After Hours done; lineage tier 2+, or 5 beasts |
| 4 | Keeper of Secrets | After Hours finished with the file kept; lineage tier 3+, or 10 beasts |

(Lineage tiers come from the race tier-up, "Evolution". A student with no race tier passes the line through beasts
instead.)

### 3.2 The evaluator (`Progression.Paths`)
- **`Check(Player)`:** for each path, find the highest tier whose conditions hold now. If it's above the saved tier,
  grant every tier between, in order. It never lowers a tier.
- **When it runs:** on join, and on the signals in §2 (debounced to one check per 2 seconds per player).
- **API:** `Tier(Player, Path) -> number, string`, `Next(Player) -> { Path, Tier, Missing: { string } }` (the step the
  Today card shows), and `CheckForTests(Player)`.

### 3.3 What reaching a tier gives you
- **A title** through `Reputation.AwardTitle`, named after the tier ("Honor Student"). You equip it as now.
- **A Moments banner** in the existing "Bell Toll" style: "HONOR STUDENT: The Academic path, tier 3".
- **A Record entry** (once 2.32 exists; tiers earned before 2.32 are written into the Record when it arrives).
- **From tier 4 up, a mention:** a PA line by day ("Congratulations to {Name}, now an Honor Student.") or a Midnight
  Broadcast item by night, through `World.Broadcast`. At most one a segment, like every PA.
- **(2.34) The tier's wardrobe unlock** (§6).

### 3.4 NPCs recognise it
- **Students:** a new `Path` moment in `Config.CliqueTalk` (60 characters at most, no gore, slurs or innuendo). When a
  student greets or reacts to you, and you hold a tier 3+ path, they may use its line ("That's the honor student.",
  "Don't start with that one. Feared."). It's read through `Talk.Pick`, one chance in four, so it isn't every line.
- **Leaders and staff:** Dialogue gets `ctx.PathTier[Path]`. Each faction leader and each teacher gets one line that
  changes from tier 3 up (for example Ms. Sallow for Academic, the Ring's champion for Combat).

### 3.5 2.31 acceptance
- Each tier of each path is reachable in play. The test reaches each one by setting the data it reads, in a test slot.
- A tier never drops: lower the data, check, and the tier stays.
- The title and the banner arrive once: check twice, still one.
- A student and a leader use a path line.
- The tier survives a rejoin.
- No new HUD bar.

## 4. Release 2.32: the Permanent Record & Honours

### 4.1 The school file (M)
- **M (and the top bar's Record button) opens it.** It's a manila folder in the UI kit's style, with paper tabs down
  the side. "Report Card" stays the name of the weekly phone card.
- **Tabs, and what each shows** (every number comes from its source):

| Tab | Shows | Source |
|---|---|---|
| Student | Today's Report Card panel: name, race and tier, level and EXP, points with +1, Might, Grit, Wits, abilities | `Progression.Sheet` (unchanged) |
| Academics | each subject's level, passes and best grade; the last 3 report cards' averages | `Profile.Classes`, `ReportCards.List` |
| Attendance & Conduct | streak and best streak, present / tardy / absent totals, discipline level and points, detentions owed and served | `Profile.Attendance`, `Profile.Discipline` |
| Athletics | club, rank, record, drill bests | `Sports.Clubs.Sheet` |
| Combat | takedowns, duel wins, Ring champion, showdowns, beasts, escapes | `Kills`, `NPCKills`, `Progress.Tally` |
| Factions & Cliques | each faction's rank, each clique's tier, classmates met | `Factions`, `Cliques.Tier`, `Reputation` |
| Paths & Titles | the five paths: tier name, the next tier's missing conditions; titles earned (equip from here) | `Progress.Paths`, `Config.Paths`, `Social.Titles` |
| Honours | the 30, by group: earned (with the day) or not; Secrets show as a sealed envelope until earned | `Progress.Honours`, `Config.Honours` |
| Notable Entries | the last 40 dated entries, newest first | `Progress.Record` |

- **Size:** it fits at 1080p and on a phone screen. Every text label passes the existing fit check (no cut-offs, no
  overlaps).

### 4.2 Notable Entries (`Progress.Record`)
- **What it is:** a short, dated log written in the school's voice: "Week 3: Promoted to Honor Student." "Week 5:
  Student displayed unusual composure during the east-wing incident."
- **What writes one:** path tiers, Honours, trophies (2.33), quest completions, a suspension served, a Ring title.
- **How much it keeps:** 40 entries; the oldest drops off.
- **Rules:** added on the server only, each event once (each entry carries a key, and a key is never written twice).

### 4.3 Honours (`ReplicatedStorage.Config.Honours`)
- **Each one** is an id, a group, a name, a line of text, a condition on existing data, and optionally a title.
- **Saved:** only the day it was earned (`Progress.Honours[id] = day`).
- **Earning one:** a small banner, and a Record entry.
- **Checked by** the same debounced check as the paths.

**The first 30:**

| Group | Honour | Condition |
|---|---|---|
| Academics | First Pass | pass any lesson |
| | Well Rounded | pass every subject at least once |
| | Top Marks | an A+ in a lesson |
| | Mastery | a subject at level 5 |
| | Honor Roll | a report card averaging B or better |
| Conduct | Present and Correct | a 5-day attendance streak |
| | Never Late | a 30-day best streak |
| | Time Served | serve a detention |
| | Slipped Away | get away from a hall monitor |
| | Spotless | a 14-day attendance streak with no violation in that time |
| Athletics | Signed Up | join a sports club |
| | Starter | reach Starter |
| | Varsity | reach Varsity |
| | Captain | reach Captain |
| Combat | First Takedown | 1 takedown |
| | Duelist | win a duel |
| | Champion of the Ring | beat the Ring's champion |
| | Beast Hunter | kill a beast |
| | Showdown | win a clique showdown |
| Society | Introductions | meet 10 classmates |
| | A Friend | a rostered classmate at Trusted |
| | Inner Circle | Inner Circle in any faction |
| | Respected | Respected by a clique |
| | Superlative | win a weekly superlative |
| Story | Roll Call | finish Orientation |
| | After Hours | finish After Hours |
| | Kept the File | finish After Hours with the file kept |
| | Evolved | reach lineage tier 2 |
| Secrets (hidden) | Tuned In | hear Night FM's introduction |
| | Flawless | an S grade on the Strikethrough |

### 4.4 2.32 acceptance
- Every number on every tab matches its source (a self-test reads both and compares them).
- Entries and Honours are added on the server, once each.
- Tiers earned in 2.31 appear in the Record.
- The file works at 1080p and at phone size, and passes the fit check.
- No new HUD bar.

## 5. Release 2.33: Trophies

### 5.1 New trophy sources
`Config.Items.Trophies` gains five trophies. Each is granted once, through the existing trophy flow (kept in the
Locker, never sold or used):

| Trophy | Earned by |
|---|---|
| Club Cup | your club wins a weekly match (`Sports.Matches`) |
| Honour Roll Plaque | a report card averaging A or better |
| Ring Belt | beating the Ring's champion |
| The Register (Chapter One) | finishing After Hours |
| Path Medal (×5) | reaching a path's top tier, one per path |

The rare beast trophies stay as they are.

### 5.2 The models
I model each trophy (PBR, in the house style, sculpt quality) and stage it in `art/group-upload-trophies/` for you to
import. Until a model is in, the trophy shows its silhouette in the case.

### 5.3 The dorm trophy wall
- **The shelf becomes a 12-slot wall,** in your private room copy only, never the dorm build.
- **You choose what goes up,** from the trophies you own, in the existing room-adjust mode.
- **Collector's Dorm** keeps its loft idea, but trophies are always earned.

### 5.4 The Trophy Case (a Locker tab)
- **What it shows:** every trophy, owned or a silhouette. Each owned one sits on a plinth in a ViewportFrame and
  turns slowly. Click one for its name, the day it was earned, and its line.

### 5.5 2.33 acceptance
- Each new trophy is granted once, from its real source.
- The wall shows 12 slots, places a trophy, and keeps it across a rejoin.
- The case shows owned trophies turning, and silhouettes for the rest.

## 6. Release 2.34: Path wardrobe & the Today card

### 6.1 The path wardrobe (modelled)
- **Three uniform variants,** as new rows in the existing uniform catalog:
  - rolled sleeves
  - a loosened tie
  - a worn blazer
- **Three path accessories**, as new rows in the accessory catalog:
  - an academic pin
  - a scarred knuckle wrap
  - a silver sigil

  The varsity jacket already exists (Athletes).
- **How they're made:** with the existing accessory pipeline (the `art/characters/accessories` batch scripts), fitted
  on PaintRigV3, in PBR and sculpt quality. Staged in `art/group-upload-pathwear/` for you to import.
- **Unlocks**, granted into your existing owned lists and worn at the wardrobe stations:

| Unlock | Path and tier |
|---|---|
| Rolled sleeves | Social 3 (Popular) |
| Loosened tie | Combat 3 (Enforcer) |
| Worn blazer | Supernatural 3 (Initiated) |
| Academic pin | Academic 3 (Honor Student) |
| Varsity jacket | Athletic 3 (Varsity) |
| Scarred knuckle wrap | Combat 4 (Notorious) |
| Silver sigil | Supernatural 4 (Keeper of Secrets) |

  A tier reached before 2.34 grants its unlock when 2.34 arrives.

### 6.2 The Today card
- **Where:** a widget at the top of the phone's home screen, above the app grid.
- **Four quiet lines**, each shown only when there's something real to say:
  - **Now:** what's on, from your timetable: "Chemistry in 3 min, R103", or "Lunch until 12:00".
  - **Heard:** one live rumour (`Social.Rumours`).
  - **Next step:** your closest path tier and what it's missing: "Honor Student: a B report card."
  - **Lead:** your tracked quest's current objective.
- **Tap a line** to open its app: Timetable, Gazette, the Record (M) or the Journal.
- **It never nags:** no notifications, no badges, no red dots. It refreshes when you open the phone.

### 6.3 2.34 acceptance
- Each unlock arrives once, at its tier, and can be worn at a wardrobe station.
- Tiers reached before 2.34 get their unlocks.
- The Today card shows only true lines, and every tap opens the right app.
- No new HUD bar.

## 7. Data changes (additive, migrated by `Sanitize`)

| Field | Owner | Shape | Size |
|---|---|---|---|
| `Progress.Paths` | Progression | `{ [Path] = tier }` (5) | tiny |
| `Progress.Tally` | Progression | `{ DuelWins, Champion, Beasts, Escapes, Showdowns }` | tiny |
| `Progress.Honours` | Progression | `{ [id] = day }` (30 now, about 60 later) | under 2 KB |
| `Progress.Record` | Progression | the last 40 `{ Day, Key, Text }` | under 4 KB |
| owned lists | Identity / Inventory | new rows in the existing lists | tiny |
| the trophy wall | Homes | 12 slots instead of 4 | tiny |

## 8. Testing and safety (every release)
- **Self-tests** on the TestBridge:
  - `PathsTest`: every tier reachable, none drops, grants once.
  - `HonoursTest`: each condition, granted once.
  - `RecordTest`: every tab's numbers match their source.
  - `TrophyTest`: each source grants once, the wall keeps its layout.
  - `TodayTest`: only true lines.
- **In Play:** slot 2, snapshot first and restored after (Phone data included, since 2.30 showed the snapshot misses
  it).
- **Every earlier suite** is re-run each release (2.27 to 2.30, the cutscenes).
- **The console:** no errors from changed modules.
- **Studio:** a backup copy of every changed module before the first install.

## 9. Not in Phase 3
- exams (Phase 4); the bestiary and Archive pages (Phase 6); the case board (Phase 7)
- the yearbook, school years and Legacy marks (doc 02 §3.4)
- the Decisions tab (it waits for quest choices in Chapter 2)
- the Archive's "Notables" portrait wall (top-tier recognition)
- students giving you small favours at tier 3 (doc 06 §3); it needs a favour system

## 10. Differences from docs 02, 06 and 07
1. **The Permanent Record is M, not L.** L is Factions now. Today's Report Card panel becomes the file's first tab.
2. **Tiers read only data that exists.** The Academic path uses report cards and class levels (no exams yet). The
   Supernatural path uses Orientation, After Hours, lineage tiers and beasts (no case progress or Archive pages yet).
3. **Five new counters** (`Progress.Tally`) start at 0 in 2.31. Duel wins, champion wins, beasts, escapes and showdown
   wins from before 2.31 weren't kept anywhere, so they can't be counted.
4. **Honours: 30 in 7 groups,** not 60 in 8. Supernatural and Story are one group (Story) until Phase 6 adds the
   bestiary.
5. **The trophy wall is 12 slots in your private room copy**, chosen in room-adjust mode.
6. **The Trophy Case is a Locker tab**, not a separate screen.
7. **No "students ask you for things" at tier 3** (it needs a favour system; §9).
8. **Wardrobe unlocks:** seven, one per tier listed in §6.1, not one per tier for every path.
9. **(2.31) The evaluator is its own module,** `Services.Player.Paths`, not code inside `Progression` (already 24 KB).
   Its data still lives in `Progress`, and `Progression.Sanitize` now keeps `Paths` and `Tally` (it used to drop
   unknown fields).
10. **(2.31) The counters:** `Superlatives` replaces `Showdowns`. Showdown wins are already saved
    (`Social.Showdowns.Won`); a won weekly superlative was saved nowhere.
11. **(2.31) NPC recognition:** students (every clique, through `CliqueTalk.Generic`), Ezra and Vesper, and Ms.
    Sallow, Mr. Pryce and Dr. Whitlock. Mr. Hale keeps his Orientation lines; clique leaders and coaches can gain lines
    later.
12. **(2.31) The tier-4 mention** is a PA line by day, or a SHOUT-OUT item (Broadcast kind `Notable`) on the Midnight
    Broadcast when the station is on air or the PA has already spoken this segment.
13. **(2.31) Checks** run on join, every 60 seconds, and on reputation, relationship, faction-rank and counter
    changes.
14. **(2.32) The Record's look** follows the owner's brief rather than a manila folder: a gothic bound dossier in its
    own PBR art, with a cover, nameplate, emblem and ambient effect for each race, and animation (open, page turns,
    glints, honour stamps).
15. **(2.32) Honours are their own module,** `Services.Player.Honours`, read from the Standing Paths' facts (checked on
    every path check), saved as `Progress.Honours`.
16. **(2.32) Notable Entries** also log a return from suspension; tiers from 2.31 are written in on join.
17. **(2.32) The Decisions tab** stays out (as §9 says); the Student tab is the old report card on the new page.
18. **(2.32) No plan file:** the menu's look changed several times at the owner's direction during the build, so the
    work followed this spec directly.
19. **(2.33) The Trophy Case is in the Permanent Record** (the Honours page, now "Honours & Trophies"), not a Locker
    tab: the Record already has the art, and every recognition is in one place.
20. **(2.33) The trophy wall fills itself** in the order trophies are listed; there's no choosing in room-adjust mode
    yet. It's three of the room's trophy shelves on the right wall (12 spots), placed by markers so the real, larger
    dorms can move it.
21. **(2.33) The Club Cup** is won by any ranked club game won (`Tally.MatchWins`), not only a weekly tournament
    (there's no tournament system yet).
22. **(2.33) The models are one piece each** (props batch 48), shown in a ViewportFrame in the case and as a clone on
    the wall; nothing in the dorm template was moved, only the TrophyWall added.
