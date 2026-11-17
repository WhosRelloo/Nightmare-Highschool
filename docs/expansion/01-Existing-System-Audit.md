# 01. Existing-System Audit (Phase One)

**Date:** 2026-11-17. **Scope:** the whole repository and the live NH Combat Test place (placeId 98950102230473), read only.
**Method:**
- Five parallel audits, each run against the live place's scripts first (Studio MCP, read only), then the repo mirrors, then the docs.
- Nothing was edited, and the map places were only looked at.
- The code is at **2.20.0**.

**Status key:**

| Mark | Meaning |
|---|---|
| **T** | Implemented, and tested in a Studio playtest (single player unless it says 2P) |
| **U** | Implemented, untested |
| **P** | Partial |
| **Plan** | Only in a design or concept doc |
| **X** | Absent |

**Two documents are stale:**
- `docs/Implementation-Status.md` stops at about 1.89 (2026-11-05).
- `docs/Project-Audit.md` still lists the clock, classes, attendance and discipline as missing.

Treat this audit, the CHANGELOG and the live code as the current truth.

---

## 1. The places

| Place | What it is | Rule |
|---|---|---|
| NH Combat Test (98950102230473) | The dev place. Every system lives here. Its school is a **greybox**: rooms R101-R106 are `Temporary` parts. | Systems are built and tested here. |
| The Map (111107083446202) | The builder's real campus. It runs a cut-down "core": combat, movement, moon, wardrobe, an in-memory Data stand-in with no saving, MapStudents, and delinquent/wolf spawns. It has **no quests, phone, sports or school loop**. | **Off limits** for builds. Scripts are ported there only when you ask. |
| Nightmare High [Wave - 1] (11109987840) | Production. | Never touched. |

**What this means for the expansion:** everything in this plan is built and proven in NH Combat Test first. Shipping it means porting the school, quest and phone layers to the real campus (the Map). That is a large, separate step, and it needs the builder's rooms to carry the same tags (see the map requirements list in [09](09-Risk-and-Scope.md)).

## 2. System inventory

### 2.1 School simulation

| System | Status | Where | Notes |
|---|---|---|---|
| Global clock | **T** | `School.SchoolClock`, `Config.SchoolSchedule`, `Functions.SchoolTime`, `Gui.ClockHud` | 5 real minutes per game hour; the same time on every server; Mon-Fri. `PeriodChanged` is fired, but **no production system listens to it** (each one polls). |
| Timetable | **T** | `Config.Classes.Periods`, `Gui.Timetable` | Homeroom plus Maths R102, Chemistry R103, English R104, History R105. One timetable for everyone; no electives. |
| Attendance | **T** | `School.Attendance` | A server box test on the room's Zone. Present, Tardy, LeftEarly, Absent or Excused. Feeds EXP, Evolution, Discipline, Quests and ReportCards. |
| Discipline | **T** | `School.Discipline`, `HallMonitor`, `Detention` | Points ladder from Warning to Suspension, with decay. `ReportIncident` takes a witness. **No teachers witness anything.** |
| Report cards | **T** (partly) | `School.ReportCards`, phone app | Weekly cards, Mr. Hale's comment, an allowance, the parents (Homes). |
| Substitutes | **T** (hooks) | `School.Substitutes` | 4 named substitutes with rules and twists (swap, game, errand). A ready-made "modifier" layer. |
| Enrollment | **T** | `School.Enrollment`, `Gui.Enrollment` | A starter uniform at the desk. You must enrol before you can start a lesson. |
| Library books | **T** | `Features.Kit` | One loan at a time; +3% class EXP and +10% on the book's subject. |
| NPC schedules | **T** (14 students) | `Features.Schedules`, `AI.StudentBrain` | Class (6 seats), passing, break, lunch, clubs, home by 19:00. **No teachers, no personal timetables.** |

### 2.2 Academics

**The shared framework (T):** the lesson framework is `School.Activities`, `ServerStorage.Activities.*` and `Gui.Activities`.
- **How a lesson starts:** a TeacherDesk prompt during the class period, then an intro, the game, and a grade sheet.
- **Server-judged:** rate-limited, and leaving the room cancels the lesson.
- **Grades:** A+ 97 / A 90 / B 80 / C 70 / D 60.
- **Rewards:** Yen A+ 20 to C 6, class level +1 (max 5) once a period, and EXP through Progression.
- **Interface:** each game module implements Start / Handle / Tick / Score / TimeLimit.

| Lesson | Status | How it plays today |
|---|---|---|
| Maths "Pop Quiz" | **T** | 8 multiple-choice questions, keys 1-4. The operations grow by level. Timers drop from 8 s to 4 s. |
| Chemistry "Lab Mix" | **T** | A 4-lane rhythm game (D F J K) with a bubble meter that ends in BOOM. |
| English "Word Scramble" | **T** | Unscramble 5 words; type or tap. |
| History "Match the Past" | **T** | Event/era memory pairs; the server reveals the cards. |
| Candle Vigil, Séance Sequence | **T** | Substitute-only reaction and Simon games. |
| Night Study | **T** | A random class game at the Archive table after hours. Pays Vigil standing. |
| Electives (Art, Photography, Workshop, PE), dissection, homework | **X** | Art props exist: the electives kit (batch 38), the art-room kit (batch 41) and SignKit icons. |

**Gaps:**
- Every lesson is a UI overlay with the character frozen. Nothing is hands-on in the world.
- Class levels unlock nothing.
- Nothing has been tested with two players, on a phone or on a gamepad.

### 2.3 Progression and identity

| System | Status | Where | Notes |
|---|---|---|---|
| EXP, levels, stats | **T** | `Player.Progression`, `Config.Progression` | Level cap 50; Might, Grit and Wits. `Award()` is the **only** way EXP is given. At level 50 EXP is zeroed and nothing progresses. |
| Effects | **T** | `Progression.Effects` / `Apply` | The **only** place where buffs are added up (stats, clan, traits, race, gear, kit, training, snacks, hunger). |
| Yen | **T** | `UpdateYen` | About 15 sources and 12 sinks; no second currency. |
| Class levels | **T** | `PlayerData.Classes` | Levels 1-5 per subject; they only set difficulty. |
| Reputation | **T** | `Social.Reputation` | 4 axes from 0 to 100: Popularity, Intimidation, Trust, Academics. |
| Titles | **T** | `Social.Titles` / `Title`, `Superlatives` | Earned from cliques, sports captain, King/Queen and weekly superlatives (temporary). |
| Achievements, badges, weapon mastery | **X** | | |
| Race "Evolution" | **T** | `Player.Evolution`, `Gui.Evolution`, `NHEvolve` | Hunger leads to a rite quest, then a tier-up cutscene. **The name "Evolution" is taken.** |
| Identity | **T** | `Player.Identity`, `Gui.Identity` | The register: name, clan, spins, height, gear, accessories. |
| Spin Shop | **T** | `Config.Shop`, `Player.Purchases` | 14 live products (2.20.0). Cosmetic and reroll only. |

**What already keeps a record:**
- **Lifetime counts:** Kills, NPCKills, attendance totals and best streak, class passes and best grades, training bests and best streak, the sports record, quests done, regions found, arcade bests, lineage tier, clique and faction ranks.
- **The record panel:** `Progression.Sheet()` and `RecordFor()` already build one for the L panel (`Gui.StatsPanel`).

### 2.4 Combat and training

**Combat (T, real input):**
- **Weapons:** Fist (the default), Katana (Armory) and Claws (admin only).
- **The core:**
  - M1 strings and enders
  - uppercut, then an air combo, then a downslam
  - M2, Z/X/C skills, the Heat meter and EX skills
  - block, parry and posture
  - dodge and feint
  - hand gear
  - race enders
  - fight crowds
  - tag assists
- **Downed, carry and grip:** combat never kills; only a grip finishes someone. Racial grips and the bite (Turning) are built.
- **PvP:** duels at the Ring, plus the Ring Champion. Open fights are policed by the hall monitor.
- **NPC combat:** delinquent tiers, beasts, wolves, clique fights and showdowns.

**Not built or dormant:**
- Weapon mastery: absent.
- Fighting styles: on hold.
- Vow: dormant (its call is commented out).

**Training (T, slot 4):**
- Push-ups, pull-ups, sit-ups and squats feed the Arms, Torso and Legs areas.
- Personal bests, streaks and soreness.
- Body meshes change with training.
- Not tested: a second player, real touch input, burnout.

### 2.5 Customization

**Built and tested (T):**
- **Wearables:** the Wardrobe (K, at stations), uniforms, capes, gear (3D head gear with stats), accessories (Kit A/B/C, cosmetic).
- **Containers:** the Locker (snacks, specials, the trophy case with silhouettes) and the snack wheel.
- **The QOL kit:** 12 items.
- **The Armory.**

**Dorm rooms (T):**
- A private copy for each student.
- Five states that follow the report card.
- A 4-slot trophy shelf.
- Invite/Visit is untested with two players.

### 2.6 Social

| System | Status | Notes |
|---|---|---|
| Factions (Vigil, Crimson Court) | **T** | Standing and 5 ranks, perks, one mission each, leaders Ezra and Vesper. A third faction, the Hollow, is a rumour only. |
| Cliques (8) | **T** | Standing, membership ranks, dares, jobs, showdowns, King/Queen, turf, rumbles, pranks, weekly superlatives. Open audit findings A-J (`Delinquent-System-Audit.md`). |
| NPC relationships | **P** | `Social.Relationships` has a full API but **only Ezra and Vesper** are recorded. The other leaders feel about you only through their clique's standing. |
| NPC memory | **P** | `StudentBrain.Memory` remembers Met, Greeted and Fought, but only for the session and only for that one student. |
| Dialogue | **T** | Server-checked trees in `ServerStorage.Dialogue.*`, plus the talk cinematic. Background students can't be talked to. |
| Strangers / introductions | **T** (2P) | Between players only. NPC students have no names. |
| Study groups (Party) | **T** | Up to 4 players and an EXP bonus. Despite the name, it has no academic content. |
| Phone | **T** | Wallet, Night FM (a personal audio-ID player with no content), Midnight Bell (generated per viewer), Texts (`Phone.AddText`), Report Card, Cliques, Timetable, Camera, 3 arcade games. |
| Midnight Bell | **T** | Moon front pages, top 3, discipline counts, superlatives, the special of the day. Its **WHISPERS are 7 fixed strings**. Mirrored on the notice boards. |
| Notifications | **T** | `Notify` / `NotifyAll`, `CliqueFights.Announce`, admin Announce. |
| PA system, rumour network, incident log | **X** | All three are only in the concept docs. |
| Lost & Found, Fortune (Sable) | **T** | Fortune already reads live server state for its hints. |

### 2.7 Story, quests, cinematics, onboarding

| System | Status | Notes |
|---|---|---|
| Quest framework | **T** | `Quests.*` and `Config.Quests`. 17 objective types, including Clues/Link/Deduce, Stealth, Defeat, Duel, Lesson, Prank and SportMatch. Categories: Main, Side, Rite, Clique, Job, Dare. Saved per slot. Failures can be recovered from. |
| Main story | **P** | Chapter 1 only, marked "provisional": New Kid, then The Empty Desk, then After Hours. It ends with "STATUS: COLLECTED. To be continued." |
| Investigation | **T** | One case (EmptyDesk). The evidence board itself is generic. |
| Stealth | **T** | Two zones: Records Office (the Night Custodian) and Staff Room (Mr. Hale). |
| Side, rite and clique quests | **T** | 8 side quests, 12 rites, and 8 cliques with a 2-quest chain, a showdown, 3 dares and 3 jobs each. |
| Characters | **T** | Ezra, Vesper, Dex, Pip, Bruno, Rhys, Lucien, Wren, Sable, three coaches, Mrs. Okada, four substitutes. **Mira Holt, the Headmaster, Mr. Hale and the Night Custodian have no model or dialogue.** |
| Cutscene framework | **X** | The pieces exist: the menu's spline shots, `CameraLease`, the `NHEvolve` Play/Done handshake, Moments banners, Reduce Motion. |
| Onboarding | **T** | Loading screen, then the intro fly-in, the menu, 3 save slots, the editor, ENTER SCHOOL (the gate push and fade), and the enrollment desk. **No tutorial.** New Kid never tells you to enrol, and it starts while you're still in the editor. |

### 2.8 Supernatural and world

| System | Status | Notes |
|---|---|---|
| Races (6) | **T** | Human 40, Priest 25, Vampire 15, Werewolf 10, Ghoul 6, Wraith 4, each with 2 sub-races and 3 tiers. Traits are data only. |
| Race actions, transformation, night sight | **T** | N grip finishes; T transforms (four races; a Werewolf at Tier II+ becomes a full wolf); H gives night sight. |
| Moon | **T** | A 4-night cycle, with Crimson and Blue moons every 16th night. Published as workspace attributes. |
| Hunger (Body) | **T** | A 0-100 need. Phases 3-6 of its concept are planned only. |
| Beasts | **P** | The Hellhound works in live servers. Four more beasts **only run in Studio** until their clips are published. No kill tally or bestiary; no Kill objective. |
| Wolves | **T** | Up to 3 at night. |
| Night chill, rain nights | **T** | |
| Curfew / after hours | **P** | Restricted regions are display only. Hall monitors are **off duty at night**, yet the phone says they're on rounds. The Night Custodian guards only the Records Office. |
| Lockdown, blackout | **X** | |
| Sports | **T** | Basketball and soccer; football tested solo. Clubs, ranks Rookie to Captain, tryouts, drills. |
| Arcade | **T** | 3 phone games, a top 5 per server, plausibility checks. No cabinets. |
| Regions | **T** | 25 boxes in NH Combat Test (no Library, Cafeteria, Dorms or Graveyard). 29 on the Map, including those four, placed in a row for the builder to move. |
| Platform | **T** | Touch arcs, a full gamepad map, `AutoScale`, AntiTeleport (it snaps players back and never kicks), a rate limit on each feature's remotes, ProfileService slots. |

## 3. Summary lists

### 3.1 Fully implemented (verified in code and tested)
**School:** the clock, timetable, attendance, discipline, detention, substitutes, enrollment and library.
**Lessons:** the 4 class games plus the 2 substitute games, and Night Study.
**Progression:** EXP, stats and effects; Yen; class levels; titles; reputation.
**Combat:** Fist and Katana, the air combo, downed/carry/grip, duels and training.
**Customization:** wardrobe, gear, accessories, locker, snack wheel, QOL kit and dorm rooms.
**Social:** factions, cliques and their quests, dialogue, strangers, the phone, the Midnight Bell, Lost & Found and Fortune.
**Story:** the quest framework, the evidence board and stealth.
**Supernatural:** races, transformation, moon, hunger, Hellhound, wolves, chill and rain.
**Other:** sports, the phone arcade, regions, touch and gamepad controls, the Spin Shop.

### 3.2 Partially implemented
- **Main story:** only Chapter 1, and it's provisional.
- **NPC relationships and memory:** only 2 NPCs are recorded, and student memory lasts only the session.
- **Beasts:** 4 of 5 work only in Studio.
- **Curfew:** display only.
- **Others:**
  - Evolution body steps III and IV are waiting on meshes.
  - Hunger phases 3-6 are planned.
  - Painted skies are waiting on uploads.
  - Vow is dormant.
  - Claws are admin only.

### 3.3 Planned, not built
- **Social:** the rumour mill, PA announcer, scene director and NPC student names.
- **Classes:** class-level unlocks, and Art, Gym and Music.
- **Factions:** the Hollow.
- **Beasts:** the Stone Gargoyle.
- **Combat:** fighting styles.
- **Story:** Chapter 2 and further cases.
- **The rest of the concept docs:** `Gameplay-and-NPC-Concepts.md` and `Environment-Ambience-Concepts.md`.

### 3.4 Existing systems that can be expanded (the main hooks)
- `Activities` game-module interface, `Substitutes` modifiers, `Classes.Periods`.
- `Schedules` + `StudentBrain` (Talk.Attitude, Talk.Pick moments, Memory), `Senses`, `HallMonitor`, `Discipline.ReportIncident`.
- `SchoolClock.PeriodChanged` (unused event bus).
- `Reputation` + `Social.Relationships` (extend the NPC list), `Titles`, `Superlatives` (cross-server weekly OrderedDataStores).
- `Progression.Award` / `Effects` / `Sheet` / `RecordFor`.
- `Quests` (17 objective types, Chapter field, Next/Requires, Cases, Stealth zones), `Dialogue` trees + ctx.
- `Phone.AddText`, `Phone.Gazette`, `NoticeBoard`, `Notifications`, `Fx` + `Gui.Moments`.
- `CameraLease`, MainMenu spline shots, `NHEvolve` Play/Done handshake, AmbienceMix cutscene fade.
- Locker trophy case + `Homes` trophy shelf, `Config.Items.Trophies`.
- `MoonPhases` workspace attributes, `Regions` (Kind=Restricted), `Config.Stealth`, `NHLamp` / `NHDoor` tags.

### 3.5 Needs new functionality
- **Lessons:**
  - hands-on lesson modes (a 3D bench in the UI; see [05](05-Class-Redesign.md))
  - teacher NPCs
  - per-student or elective timetables
- **School life:**
  - a central incident bus
  - rumours
  - a PA
  - a broadcast content service
  - a curfew rule
  - crisis events
- **Records:**
  - a bestiary and kill tally
  - a Kill objective
  - achievements (as earned "Honours", not a new bar)
- **Story:**
  - a cinematic director
  - a prologue and first-day tutorial
  - Chapters 2-5
  - more cases
  - named NPC students
  - NPCs for Mira, the Headmaster and the Night Custodian

### 3.6 Dependencies between systems (the important ones)
- **Data:** every saved feature writes a whole block through `UpdateState` (`Set<Block>`), so each block needs **one owner**. `Social` is owned by `Reputation.Sync` (Fortune and `Cliques.Add` break this today).
- **EXP:** goes only through `Progression.Award`.
- **Buffs:** go only through `Progression.Effects` / `Apply`.
- **The clock:** Attendance, Activities, Schedules, HallMonitor, Kit chill, Beasts, Wolves and MoonPhases all read time. They use **five different night windows** today.
- **Lesson results:** `Activities.Finished` feeds Progression, Factions, Quests, Reputation, ReportCards and Attendance.
- **Downing:** `Downed.OnDowned` / `OnExecuted` feed Progression, KillTracker, Discipline (through witnesses) and Quests.

### 3.7 Reusable assets
- **Props:**
  - 162 props in `ServerStorage.NHProps`
  - the electives kit (herbology, home ec, sewing, photography, woodshop, ceramics, drama)
  - the art-room kit
  - specimen jars and easels
  - SignKit icons for every subject
  - the 14 rite props
- **Art and UI:**
  - the PBR icon pipeline (`make_seal_icons`, `make_shop_icons`, `make_kit_ui`)
  - the UI kit (`UI.Components`, Theme)
  - the substitute-game art
- **Systems with content:**
  - talking faces (visemes and 6 expressions)
  - the Moments banners
  - the evidence-board VFX
  - the stealth meter
  - the menu's spline camera
  - the ambience mixer and sheets

### 3.8 Must remain untouched
- **The map:** every build on the Map place, and the greybox geometry in NH Combat Test (rooms, props, terrain). Systems may *read* them and attach to their tags only.
- **Production:** never touched.
- **Data store names:** the ProfileService store names (`"Production's DatSa"` is load-bearing), slot keys, and the existing `PlayerData` field shapes (only additive changes, each with a Sanitize).
- **Characters and story:** existing characters, dialogue, quests and Chapter 1 beats; the race roster, rolls and odds; enrollment and ENTER SCHOOL.
- **Combat:** the timings you approved for fists, and `Downed`'s rule that combat never kills.

## 4. Open findings worth fixing before the expansion (no new features)
1. **Night windows:** five different definitions of "night". Centralise them in `SchoolClock`.
2. **Talk cinematic:** it bypasses `CameraLease`. Route it through the lease.
3. **Social writes:** `Cliques.Add` and `Fortune` write `Social` outside `Reputation.Sync`.
4. **Phone text:** it says hall monitors patrol at night; they don't.
5. **Vesper's location:** the Boiler Yard in her dialogue, the Crimson Parlor in her showdown.
6. **Canon clash:** "Corvin Ashgrave" (Headmaster portrait) vs "Corvin Crane" (Court twin).
7. **Enrollment:** New Kid never tells a new player to enrol.
8. **Place size:** `NH_Backup` holds 35,829 instances, and stray TEMP models sit in the workspace. They bloat the place and swamp script searches. Clean them up only with your OK.
9. **Beasts:** four beasts' clips are unpublished, so they never spawn in live servers.
10. **Stale docs:** `Implementation-Status.md`, `Project-Audit.md`, and `Phone.md`'s app list.
