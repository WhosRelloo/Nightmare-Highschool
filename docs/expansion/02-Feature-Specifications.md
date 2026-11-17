# 02. Feature Specifications and Concept Decisions

Every concept in the master prompt is sorted into one of four groups:
- **Approved:** build it as described, on the named existing systems.
- **Revised:** build it, but changed so it extends what exists rather than duplicating it.
- **Deferred:** not now; the reason is given.
- **Rejected:** not built; the reason is given.

For each item, "Extends" names the existing system it grows from and "New" names what has to be added.

Hard rules applied everywhere:
- No new reputation or EXP bar.
- No map edits.
- No pay-to-win.
- Server-authoritative rewards.
- Saved per student (save slot).

Related documents:
- [05](05-Class-Redesign.md): the class designs.
- [03](03-Story-Bible.md): the story.
- [04](04-Cinematic-Framework.md): cinematics.
- [06](06-Progression-and-Retention.md): goals and balance.
- [07](07-Technical-Architecture.md): modules and data.

## Decision table

| # | Concept | Decision | Short reason |
|---|---|---|---|
| 3.1 | Student Evolution | **Revised** as *Standing Paths* | "Evolution" is the race tier-up already. The paths read existing data and add no bars. |
| 3.2 | Personal Student Record | **Revised** as *the Permanent Record* | Extends the L panel's Record (`Progression.Sheet`/`RecordFor`) instead of adding a new screen. |
| 3.3 | Trophy Room | **Revised** | Grows the Locker trophy case and the dorm trophy shelf. No new room. |
| 3.4 | Legacy and Graduation | **Revised** (school years) / **Deferred** (graduation) | No wipes. A yearbook and legacy ranks after level 50 now; graduation waits for the campaign end. |
| 4.1 | Persistent relationships | **Approved** | Extend `Social.Relationships` to the named cast and to rostered students. |
| 4.2 | Dynamic hierarchy | **Revised** | Read from turf, showdowns, superlatives and ranks. No new score. |
| 4.3 | Rumour network | **Approved** | New `Social.Rumours`, fed by an incident bus. |
| 4.4 | Campus incidents | **Approved** | A thin incident bus plus a scene director over the existing systems. |
| 4.5 | NPC schedules | **Approved** | Extend `Schedules`. Add teachers and staff. |
| 4.6 | Staff stories and PA | **Approved** | One `Broadcast` service with a PA output. |
| 4.7 | Clique competitions | **Approved** | Extend `CliqueEvents` and `Superlatives`. |
| 5.1-5.5 | Class redesign | **Approved** | New game modules on the existing `Activities` interface, in a hands-on bench view. |
| 5.6 | Electives | **Revised** | Photography (phone camera) and PE (existing venues) first. Art and Workshop rotate into existing rooms. New rooms are a builder request. |
| 5.7 | Dissection lab | **Revised** | A stylised anatomy teaching model (wax/porcelain), no animals and no gore. |
| 6.1 | School year | **Revised** | Terms and a yearbook on the global clock. Nothing is reset. |
| 6.2 | Weekly competitions | **Approved** | Reuse the `Superlatives` OrderedDataStore pattern. |
| 6.3 | Physical arcade machines | **Deferred** (physical) | Cabinets are a map change. Cross-server weekly boards for the phone arcade come now. |
| 6.4 | Secret collectibles | **Approved** (small, curated) | 24 "Unwritten Archive" pages tied to lore. How they're placed needs your call (see 09). |
| 6.5 | Dorm customization | **Revised** | Decor slots in the existing private room copy. The dorm build itself is never edited. |
| 7.1 | After-hours / curfew | **Approved** | One night window, a curfew rule in HallMonitor plus the Night Custodian, and restricted regions enforced on the server. |
| 7.2 | Beast tracking | **Approved** | Traces, sightings, a bestiary and a Kill objective. Needs the beast clips published. |
| 7.3 | Crisis events | **Revised** | Rare (about one a week), each tied to the story and opt-in to join. Blackout and lockdown use the existing lamp and door tags. |
| 7.4 | Secret traditions | **Approved** (small) | Tied to moon events and lore props. |
| 8.x | Story, prologue, tutorial, chapters, investigations, choices | **Approved** | On the quest framework; see [03](03-Story-Bible.md). |
| 9 | Cinematic framework | **Approved** | A `Cine` director on `CameraLease` plus the `NHEvolve` handshake; see [04](04-Cinematic-Framework.md). |
| 10 | Race integration | **Approved** | Per-race readings and optional discoveries. One shared campaign. |
| 11.1 | Midnight Broadcast | **Revised** | One content source feeding the Gazette, a Night FM station and the PA. |
| 11.2 | School Reputation Archive | **Revised** as *the School Archive / Yearbook* | It's part of the mystery (records changing). No stats page. |
| 11.3 | Personal Nemesis | **Revised** | A rival record inside `Social.Relationships`, reusing grudges and showdowns. |
| — | Anything that sells power, EXP, Yen or story access | **Rejected** | Your no-pay-to-win rule. |
| — | A second reputation, faction, relationship, inventory, quest or training system | **Rejected** | Duplication. |
| — | New buildings, rooms or cabinets, or moving builds | **Rejected** (until you approve) | Map protection rule. They're listed for the builder instead. |

---

## 3. Character progression and identity

### 3.1 Standing Paths (revised "Student Evolution")
**Goal:** your accomplishments show, in what you wear, how people address you, what opens up and how you're seen.

**Mechanism:** five paths. Each path's tier is **computed from data the game already keeps**. Only the *highest tier reached* is saved (`Progress.Paths[Path] = tier`), so a bad week never takes a tier back.

| Path | Tiers | Reads (existing data) |
|---|---|---|
| Academic | Freshman Nobody → Recognized Student → Honor Student → Academic Elite | Class levels and passes, report-card averages, attendance streak, exam results (new, see 05), Academics reputation |
| Social | Unknown → Recognized → Popular → Influential → School Legend | Popularity reputation, clique tiers and membership rank, faction rank, superlatives won, people introduced (`Known` count) |
| Combat | Beginner → Street Fighter → Enforcer → Notorious → Feared | Intimidation reputation, duel wins and Ring Champion, showdowns won, NPCKills/Kills, beast kills (new tally) |
| Athletic | Rookie → Starter → Varsity → Captain | **Exactly the existing sports rank** (`Sports.Club` rank). Mirrored here, never recomputed. |
| Supernatural | Unaware → Uneasy → Initiated → Keeper of Secrets | Lineage tier and rites, case progress, archive pages found, beasts tracked, chapters cleared |

**Thresholds:** each tier is a small set of AND conditions in `Config.Paths`, for example *Honor Student = 3 subjects at class level 4 or higher, a B average on the last report card, and a 10-day attendance streak*.

**Rewards for reaching a tier:**
- **A title**, through `Reputation.AwardTitle`.
- **One wardrobe unlock**, granted into the existing owned lists (`Identity.Uniforms` / `Accessories` / `Gear`).
- **NPCs recognise it:**
  - a new "Path" moment in `Config.CliqueTalk`, so students say things like "That's the honor student", read through `Talk.Pick`;
  - Dialogue `ctx.PathTier`, so leaders change their lines.
- **A Moments banner** ("Bell Toll" style) and a Midnight Bell mention.

**Visible appearance, built on the existing wardrobe:**
- **Uniform variants:** rolled sleeves, a loosened tie and a worn blazer, unlocked by path tiers. They're new rows in the existing Appearance catalog.
- **Path accessories:** an academic pin, a varsity jacket (already Athletes), a scarred knuckle wrap (Combat), a silver sigil (Supernatural).

**New:** `Config.Paths`, a `Paths` evaluator inside `Progression` (on its existing signals), the `Progress.Paths` field, the CliqueTalk moments, and the wardrobe rows.

**Acceptance:**
- Each tier is reachable through play alone.
- A tier never drops.
- The title and unlock arrive once.
- An NPC line references the tier.
- The tier survives a rejoin.
- No new bar appears on the HUD.

### 3.2 The Permanent Record (revised "Personal Student Record")
- **Extends:** the L panel's Record (`Progression.Sheet` / `RecordFor`, `Gui.StatsPanel`).
- **What it becomes:** a school file. It's a manila folder in the UI-kit style, with tabs for Academics, Attendance & Conduct, Athletics, Combat, Factions & Cliques, Honours & Titles, Story and Decisions.
- **Data:** every line is existing data, except two additions:
  - a short **Notable Entries** log (`Progress.Record`, the last 40 dated lines), such as "Week 3: Solved the Empty Desk" or "Took the Ring Championship";
  - the **Decisions** list, which comes from quest choices (see 03).
- **Tone:** an entry reads like a file, written by the school: "Student displayed unusual composure during the east-wing incident."
- **Naming:** "Report Card" stays for the weekly phone card, and the L panel is renamed "Permanent Record", so the two names no longer clash.
- **Acceptance:**
  - every number matches its source;
  - entries are added server-side and only once;
  - it works on mobile at 1080p and at phone size.

### 3.3 Trophy Room (revised)
- **Extends:** the Locker trophy case (silhouettes), the dorm trophy shelf (`Homes`, 4 slots) and `Config.Items.Trophies`.
- **New trophy sources:**
  - sports championships (weekly tournament wins)
  - academic awards (an A+ term)
  - the Ring Championship
  - chapter completions
  - rare beast trophies (these exist already)
- **The dorm shelf:** grows to a 12-slot display wall, using only the private room copy, never the dorm build. Collector's Dorm (the pass) keeps its loft idea, but **trophies are always earned**.
- **The case:** a "Trophy Case" UI adds a 3D ViewportFrame turntable for each trophy.

### 3.4 Legacy and school years (revised / deferred)
- **School years:** each 12 in-game weeks is a **term**, and 3 terms make a year. The year is shown on the record and the slot card: Year 1, 2, 3 and so on.
- **Nothing is reset.** Your record keeps every year.
- **The Yearbook:**
  - at the end of each term, a page with your portrait (a ViewportFrame of your character), your tiers, your titles and one superlative;
  - it's kept in `Progress.Yearbook` (one compact entry a term);
  - it's shown in the School Archive (11.2).
- **Legacy ranks after level 50:** EXP over the cap turns into **Legacy marks**, a counter shown as a seal on the record. Each 5 marks unlocks one cosmetic (a seal colour or frame). No power.
- **Graduation (deferred):** a cinematic graduation tied to the Chapter 5 ending. Graduates keep playing as "Alumni Prefects", a title and a cosmetic. This waits until the campaign end is written.

## 4. Living school and social simulation

### 4.1 Persistent relationships (approved)
**Named NPCs:** extend `Config.Reputation.Npcs` from 2 NPCs to the whole named cast:
- the leaders
- Sable
- the coaches
- Mrs. Okada
- the substitutes
- the new staff NPCs: the Headmaster, the Night Custodian, Mr. Hale and the teachers

**Background students** get a **stable roster**:
- `Config.Students`: 24-40 named students, each with a clique, build and personality (it extends `Config.Cliques.Students` and `Config.NpcBuilds`).
- **Names follow the Strangers rule:** you learn a student's name when they introduce themselves, which happens once your relationship with them is at least Acquaintance.

**Behaviour sets moved:**

| Behaviour | Change |
|---|---|
| Helping | e.g. answering their call for help in an incident |
| Supporting | |
| Shared activities | the same lesson, the same team |
| Quest done | |
| Embarrassing | being pranked by you |
| Fighting | |
| Betraying | e.g. lying on their behalf in an investigation |

Each change goes through `Reputation.ChangeRelationship` with a reason.

**Storage:**
- One compact entry per NPC in `Social.Relationships[npcId] = {V, Met, Last, Flags}`.
- `StudentBrain.Memory` is backed by it, so NPCs remember you across sessions.
- `Talk.Attitude` reads it.
- **Cap:** 64 entries; the oldest Acquaintance-level entries are dropped first.

**Acceptance:**
- Fight a rostered student, rejoin a day later, and they still react to it.
- Help them twice and their greeting changes.

### 4.2 Dynamic hierarchy (revised)
- **Mechanism:** a server-wide "pecking order", computed every 10 minutes from turf holders, showdowns won, superlatives, faction and clique ranks, and Path tiers. Nothing new is stored.
- **Where it shows:**
  - the Gazette's "The Pecking Order" column
  - NPC lines (who they defer to)
  - a crown icon in the Students list for the top 3
- **Rostered NPC students have their own standing** inside their clique: Leader, Lieutenant or member, using the existing membership ranks. It changes through events: a student who wins a scuffle rises, and one who's humiliated falls. Those changes are logged as rumours.

### 4.3 Rumour network (approved)
- **New:** `Social.Rumours`.
- **Sources:** the incident bus (4.4) emits facts such as:
  - X downed Y at the Commons
  - the Hellhound was seen at the Boiler Yard
  - Ravens won 3-1
  - someone was in the Records Office after hours
- **A rumour holds:** a fact id, a subject, a location, a time and a **truth value**.
- **Spread:** rumours spread through student pair-chats (`Brain.Idle`), at most one hop per 5 minutes and region by region.
- **Mutation:** each hop has a 20% chance to change one detail: the place, the person (only to someone who was present) or the size.
- **Rumours never claim a real player did something they didn't do.** The details that can change are about NPCs or the place and scale only, and that's enforced in code.
- **Output:**
  - the Gazette's WHISPERS (replacing the 7 fixed strings)
  - a "Rumour" moment in `Config.CliqueTalk`
  - Sable's Fortune
  - Night FM's "Caller Line" segment
- **Server-wide and not saved:** only rumours flagged *Notable* are written into the Archive.

### 4.4 Campus incidents (approved)
- **New:**
  - `Services.World.Incidents`, a `SignalPlus` bus with `Incidents.Emit({Kind, Where, Who, Witnesses, Severity})`;
  - a small **scene director** that stages scenes from data (`Config.Scenes`): two students arguing, someone shoved into a locker, a vandalised notice board, a sound in the east wing, a figure at a window. Each scene has 2-4 NPCs and a duration, and only happens where players can see it.
- **Emitters:** CliqueFights, HallMonitor, Discipline, Downed, Beasts, Sports, Pranks and MoonPhases.
- **Consequence:** a scene's outcome feeds rumours, relationships and Discipline (a teacher witness).
- **Rate:** at most 1 scene per region per 10 minutes, so scenes don't turn into repeated random quests.

### 4.5 NPC schedules (approved)
- **Extends:** `Features.Schedules` and `StudentBrain`. Moves them onto the `SchoolClock.PeriodChanged` event.
- **New roles:**
  - **Teachers:** one per subject, at the TeacherDesk in class periods and in the Staff Room otherwise. They witness fights and tardiness in class through `Discipline.ReportIncident`.
  - **The Night Custodian:** patrols restricted regions at night.
  - **The Headmaster:** office hours, and appears at assemblies and crises.
  - **Mrs. Okada:** lunch, as now.
- **Per-student timetables:** each rostered student has a subject list. "In class" seats that period's roster, which replaces the 6-seat cap and the "east wing" fallback.
- **Performance:**
  - students more than 160 studs from every player are **simulated abstractly**: their position is computed from the schedule, with no pathing;
  - brains run only near players (the 5 Hz / 1 Hz rule stays);
  - the target is 24-40 students at 60 fps.

### 4.6 Staff stories and PA (approved)
The PA is one output of the **Broadcast** service (11.1). Announcements are *context-aware*. Each one is triggered by a real state and limited to 1 per period plus emergencies:
- the bell schedule
- assemblies
- an attendance warning, sent only to the student it's about, through their phone
- a match tonight
- a substitute today
- a missing student (story)
- curfew in force
- a crisis

**Presentation:**
- a chime
- a ClockHud line with a typed text
- talking-face PA speakers on the existing `NHLamp` / hall props
- the voice is text only, with subtitles

**Staff mini-arcs:** each teacher has 2-3 short dialogue arcs that unlock through relationship and Path tier (Mr. Hale, for example). They're delivered as small Side quests.

### 4.7 Clique competitions (approved)
- **Extends:** `CliqueEvents` (daily dares) and `Superlatives` (weekly).
- **Each clique gets one weekly competition** that matches its identity:

| Clique | Competition |
|---|---|
| Athletes | Field Day |
| Ink | Mural Duel: the Art lesson's mechanic in the Ink Studio |
| Choir | Candle Vigil Marathon |
| Pack | Courier Run: time trial deliveries |
| Delinquents | Lot Brawl |
| Ordinary | Helping Hands: the most incidents resolved |
| Vigil | Lamp Watch |
| Court | Masquerade |

- **Scoring:** members score for their clique; the week's winner holds the clique's turf banner and a title.
- **Solo-friendly:** individual scores also count toward personal Superlatives.

## 5. Academics (summary; full design in [05](05-Class-Redesign.md))
- **The lessons:** the four core lessons gain a **hands-on bench mode**, a 3D ViewportFrame workbench over the desk, so they need no map props.
  - **Maths:** applied problems (measuring, construction, balancing).
  - **Chemistry:** the practical lab (measuring, order, heat, pressure).
  - **English:** sentences from word tiles, proofreading, argument building.
  - **History:** artifacts, timelines, record inconsistencies (wired to the mystery).
- **Mechanics, not speed:** each subject adds a **new mechanic per class level**; timers are never the only change.
- **Kept as they are:** the existing games stay as "Pop Quiz" warm-ups and substitute twists.
- **Electives:**
  - **Photography:** phone-camera assignments in the existing world.
  - **PE:** drills at the existing Gymnasium and Field.
  - **Art and Workshop:** benches in a rotating existing room.
  - **Anatomy:** a stylised teaching model.
- **Class levels unlock things:** level 3 gives a subject title, and level 5 gives a subject accessory plus Advanced Study, a harder after-school variant at Night Study.

## 6. Retention (summary; full framework in [06](06-Progression-and-Retention.md))
- **Terms and the yearbook:** as in 3.4.
- **Weekly competitions:** a sports tournament, Academic Decathlon week, the clique competitions, and the faction "Lamp vs Mark" week.
- **The phone arcade:** cross-server weekly boards. No physical cabinets.
- **24 Unwritten Archive pages:** each is a lore fragment, and the set completes a secret chapter.
- **Dorm decor:** dorm decor slots.

## 7. Supernatural gameplay

### 7.1 After hours and curfew (approved)
- **One night window:** `SchoolClock.IsNight()`, used by every system. The current five windows become derived offsets ("dusk", "night", "deep night").
- **Curfew** runs from 22:00 to 06:00:
  - Being in Kind=Restricted regions, or outside your dorm wing, is *after-hours*.
  - **The Night Custodian** and a **night monitor** (a night duty kind for HallMonitor) patrol. They use the existing stealth meter and lockers.
  - **Caught:** a Trespassing violation, plus a confiscation of the item you were carrying for the night, if any.
- **The reward for the risk:**
  - night-only clues, rumours and archive pages
  - beasts
  - rites
  - Night Study
- **Fix:** the phone's "monitors on their rounds" text becomes true.

### 7.2 Beast tracking (approved)
- **Before a spawn:** each beast spawn is preceded by **traces**, written as rumours and as clue props at the lair region: claw marks, a cold patch, scattered feathers.
- **The Bestiary:** a phone app page. Each beast has unknown, sighted, tracked and defeated states, plus lore, from `Config.Beasts`.
- **Tracking:**
  - Follow the traces (a Clues objective) and reach the lair.
  - Use the right counter (a Priest relic, Vampire night sight, a wolf's scent) for an advantage.
  - The new **Kill objective** type and the beast **kill tally** feed the Combat and Supernatural paths.
- **Co-op:** optional, through the study group.
- **Blocked until you publish the clips:** the four beasts whose animation clips are unpublished.

### 7.3 Academy crisis events (revised)
- **Blackout:**
  - the `NHLamp` lamps go out by region
  - students huddle (Schedules)
  - the PA calls for calm
  - something moves in the dark (scene director plus a beast or a story figure)
  - players restore the boiler (Boiler Yard) together or alone
- **Lockdown:** `NHDoor`s lock, everyone goes to their rooms, and a story beat plays (a missing student).
- **Bell incident:** the bell rings at a wrong hour (story).
- **Frequency:** at most one crisis per real week per server. Crises are **opt-in**: you can carry on with ordinary school life, and the crisis hands out its own rewards.
- **Every crisis connects to the schedules, PA, rumours, quests and the archive.**

### 7.4 Secret traditions (approved, small)
Each one is tied to a moon event and lore props, and rewards rumours, an archive page or a title. Three to start:
- **The Lantern Count:** a Vigil candle ritual on a new moon.
- **The Crimson Roll Call:** the Court names the missing on a Crimson moon.
- **Don't Answer:** you stay silent at the 3 AM bell; a Mira-linked tradition.

## 8. Story and quests (see [03](03-Story-Bible.md))
- **The prologue:** a cinematic over the existing ENTER SCHOOL flow.
- **The first-day tutorial:** an "Orientation" quest that leads into New Kid and teaches enrollment.
- **The campaign:** five chapters on the quest framework.
- **Investigations:** 6+ new cases, including two-player and 2-4 player cases with shared evidence and split roles.
- **Choices:** stored in `Quests.Decisions`; they change dialogue, relationships and case outcomes.
- **Side content:** optional and never required.

## 11. Social and immersive integrations

### 11.1 Midnight Broadcast (revised)
**Answering the integration questions:**

| Question | Answer |
|---|---|
| What exists | Night FM, a personal audio-ID player; the Midnight Bell, generated per viewer; notice boards; texts. |
| What's missing | Server-side content, a station, and a PA. |
| What to build | One `World.Broadcast` content service that produces "items" (announcements, incident reports, interviews, caller-line rumours, story transmissions). |
| Outputs | Gazette articles; a **Night FM "Midnight Broadcast" station** (text segments with sound, 21:00-03:00, alongside the personal player); the PA by day. |
| Story link | Story transmissions are chapter beats ("a voice reads a roll call with one name too many"). |
| Multiplayer and saving | Server-wide; the per-player read state is saved in `Phone`. |
| Duplication | None. Three outputs share one source. |

### 11.2 The School Archive and Yearbook (revised)
- **Where:** a UI reached at the Archive (the existing library region and Ezra's post).
- **What's in it:**
  - portraits of former students (yearbooks, yours included)
  - historical photographs
  - sports and academic records
  - major incidents
  - faction history
- **Its narrative purpose:**
  - entries change as the campaign advances
  - names fade from photos
  - records conflict
  - *altered* entries become clues (the Archive is a Clues source for cases)
- **Not a stats page:** your own entries are written in-world, in the school's voice.

### 11.3 Personal Nemesis (revised)
- **Mechanism:** a **rival** is a Relationship entry with the `Rival` flag. It forms naturally after repeated conflict:
  - 3+ fights with one rostered student or leader
  - losing a showdown twice
  - an investigation choice that betrays them
  - sports rivalries (beating the same team captain)
- **What a rival does:**
  - texts you challenges (`Phone.AddText`)
  - interrupts you at moments that make sense (a scene director scene)
  - offers rematches (the Duel objective)
  - talks about you to others (rumours)
- **Resolving it:** win three, make peace through a quest, or turn the rival into a friend.
- **Player-vs-player rivalries:** only through opt-in duels and sports. The system never forces PvP.
