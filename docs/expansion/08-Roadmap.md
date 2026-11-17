# 08. Implementation Roadmap

**The order:** foundations first, then the systems most other things depend on (the clock, incidents, the roster, cinematics), then content.

**Review checkpoint:** every phase ends with one. That means a playable-state audit, a CHANGELOG entry and your approval before the next phase begins.

**Where it's built:** everything is built and tested in NH Combat Test. **The Map and production are untouched** until you approve a port.

**Testing standard for every phase:**
- **Inputs:** real input on PC, touch emulation at phone size, and the gamepad.
- **Players:** solo, plus a **two-client local server** for anything multiplayer.
- **Saving:** a rejoin and save check on slot 4 "Testy".
- **Regression:** a sweep of the previous phases' acceptance lists.
- **Errors:** zero console errors from game scripts.

---

## Phase 0: Foundations and fixes (no new features)
**Status: done in NH Combat Test as 2.22.0 (2026-11-17), solo-tested.** The two-client harness run, the canon names and the archive still wait on you. Report: [10](10-Phase0-Report.md).

**Scope:**
1. **Clock:** add `SchoolClock.IsNight` / `Phase` / `Term`, and move the five night windows onto them.
2. **Talk shot:** route the talk cinematic through `CameraLease`.
3. **Social writes:** route `Cliques.Add` through `Reputation.Sync` (the single writer for `Social`). Fortune was already correct.
4. **Canon fixes:** the phone's monitor text, Vesper's location, and the Corvin name clash (pending your call).
5. **Enrollment:** New Kid points new players to the desk (an Enrol step), and auto-start waits until you're in school.
6. **Measure:** the profile size and the place size. Propose an NH_Backup archive plan (only with your OK).
7. **Two-player test harness:** a repeatable local-server test script on TestBridge.
8. **Docs:** refresh Implementation-Status.

**Acceptance:**
- Every night-based system agrees on night.
- No behaviour changes except the fixes listed.
- A two-player harness run passes.

**Risks:** touching shared night logic. Mitigated by a before/after test of chill, wolves, beasts, moon and regions.

## Phase 1: Narrative framework and the prologue
**Scope:**
- The Cine framework (04).
- `NHCine` with Play, Done, Skip and Vote.
- The `Cinematic`, `Decision`, `Kill` and `Enrol` quest objectives.
- The Orientation quest (first-day tutorial).
- The prologue roll-call cut.
- The Chapter 1 cliffhanger cut.
- Mr. Hale and the Night Custodian as talkable/visible NPCs (models from the existing NPC builder).

**Assets:**
- 2 cinematics
- an NPC model for Hale, and one for the Custodian
- subtitle UI

**Acceptance:**
- A new slot gets the prologue once, can skip it on a replay, and lands in Orientation, then New Kid.
- A disconnect mid-cut is recovered on rejoin.
- A two-player group cut vote works.
- The existing ENTER SCHOOL and gate transition are unchanged.

## Phase 2: Living school core
**Scope:**
- `Config.Students` roster (24 students to start).
- Rostered names learned through introduction.
- Expanded Relationships, with memory that persists.
- Teachers (4) and the Headmaster in schedules, with teacher witnesses in class.
- The incident bus and scene director (6 scenes).
- Rumours.
- Broadcast (Gazette plus PA).
- Curfew and night duty.

**Acceptance:**
- An NPC you fought remembers it after a rejoin.
- A fight in class is booked by the teacher.
- A scene becomes a rumour that reaches the Gazette and mutates only in allowed fields.
- The PA announces real state only.
- Curfew catches you in a restricted region at 23:00 and not at 15:00.
- 24 students hold 60 fps.

## Phase 3: Progression and identity
**Scope:**
- Standing Paths.
- The Permanent Record (the L panel's redesign).
- Honours (first 30).
- The trophy wall.
- Uniform variants and path accessories (art pipeline).
- The Today card.

**Acceptance:**
- Each tier is reachable in play, never drops and grants once.
- NPC lines react to tiers.
- The Record's numbers match their sources.
- No new HUD bar.

## Phase 4: Academic redesign
**Scope:**
- The bench engine.
- Chemistry first (5 levels), then Maths, English and History.
- Class-level unlocks.
- Lab Partners.
- Exams.
- Photography and PE electives.
- Then Art and Workshop.
- Anatomy, after you approve the specimen look.

**Acceptance:** per-subject criteria in 05 §7. Phone-size touch and the gamepad are tested, plus a two-client Lab Partners test.

## Phase 5: Retention and recurring
**Scope:**
- Terms and the Yearbook.
- Weekly competitions (sports tournament, decathlon, clique competitions).
- Cross-server weekly phone-arcade boards.
- 24 Archive pages (the placement method you chose).
- Dorm decor slots.
- Legacy marks.

**Acceptance:**
- A term rollover writes the yearbook without resetting anything.
- Weekly boards agree across two servers.
- Every Archive page has lore and is counted once.

## Phase 6: Supernatural and races
**Scope:**
- The beast tracking chain and the Bestiary (needs the four beasts' clips published by you).
- Crisis events (Blackout first).
- Secret traditions (3).
- Race readings for Chapter 1 and the Phase 7 cases.

**Acceptance:**
- **Beast tracking:** traces lead to a lair, the kill is tallied, and the Bestiary updates.
- **Blackout:**
  - lamps go out by region
  - the PA responds
  - it can be ignored safely
  - it pays the people who join in
  - two clients
- **Race readings:** each race gets at least one optional reading per case, and no race is blocked.

## Phase 7: Campaign Chapters 2-3 and investigations
**Scope:**
- Chapter 2 (memory, the Archive as a clue source, Mr. Hale's arc, a two-player case).
- Chapter 3 (bell nights, echo rooms in existing rooms, a Lockdown crisis, the faction-trust decision).
- 4 new cases.

**Acceptance:**
- Solo completion is possible.
- Group cases work with shared evidence and split roles.
- Decisions change the documented outcomes.
- Every cut follows 04 §8.

## Phase 8: Chapters 4-5 and the endings
**Scope:**
- The Bloodline Records (race-varied).
- The Last Attendance finale (group, with a solo path).
- Three endings.
- Graduation (Alumni Prefect).

**Acceptance:**
- All three endings are reachable.
- A solo finale works.
- Endings change the Archive state and titles.
- Nothing ordinary is locked afterward.

## Phase 9: Social integrations
**Scope:**
- The Night FM Midnight Broadcast station.
- The School Archive narrative changes across chapters.
- Rivals (Nemesis).
- The Pecking Order.

**Acceptance:**
- A rival forms only from the documented triggers, can be resolved three ways and never forces PvP.
- Archive entries change at the right chapter beats.

## Phase 10: Polish, performance, regression, and the port plan
**Scope:**
- A full regression on PC, phone and gamepad.
- 4-player load tests.
- A profile-size audit.
- A performance pass (40 students).
- The **port plan for the real campus** (the Map): which tags the builder must add, and which scripts move.

**Acceptance:**
- Zero script errors in a 30-minute 4-player session.
- Every phase's list still passes.
- The port plan is signed off by you and the builder.

---

## The first checkpoint (now)
Please review:
1. The decisions table (02).
2. The story bible's [OPEN] items and the mythology direction (03).
3. Phase 0's scope.

With your OK, I'll start Phase 0. No feature work begins before that.
