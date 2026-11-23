# Roadmap to the next test build (November 2026)

Written 2026-11-22. The **testing gate** is everything in section A, merged into one build in NH Combat Test. The Discord update posts (2.16.0, 2.35.0, 2.36.x and the new release) go out only once the gate is reached (owner rule).

## A. Must finish before testing

### 1. Tutorial slice 1 (2.35.0): done, merged (PR #1). Owner checks left
- [ ] Watch both cuts at full speed: the fence stop into the vault, the corner slow-down, the bus walk after the glide.
- [ ] Sign off the vault, the bus boarding (door clipping accepted), the camera marks and the resume.
- [ ] Two-player test (tools/phase6-2350/REPORT.md, docs/Two-Player-Test-Plan.md).
- [ ] Phone-size check: subtitles at least 20 px, and the skip button a large target.

### 2. Strafes + NPC gestures (branch phase6-strafes): building
- [ ] Repo work: Locomotion maths, bake.py, the Gestures system, checks.
- [ ] Read-only Studio: the infirmary spot vs the Map, the FIER clip extract, the script dump.
- [ ] Install: 42 clips, the infirmary, the bleacher seats, the scripts. Tests, including the tutorial regressions (the stride fix changes the walk-ups).
- [ ] Owner: publish the 42 clips, including the two square-chest strafes. Then look up the ids.
- [ ] Review, fix rounds, merge.
- [ ] Owner checks: the pray kneel-in, the strafe look, the remaining foot slide (~20% at the 2.4x cap), Nurse Agatha Thorne's simple heal.

### 3. Bell Tower R2: Bells (branch belltower-r2, 2.37.0): repo half done
- [ ] Fresh dump, then the Discipline, HallMonitor, Bell Rail HUD and QuestTracker edits.
- [ ] Install, tests, screenshots, docs "checked" lines, review, merge.
- [ ] Owner decisions:
  - Contraband adds 10 Heat;
  - probation's x1.25 also applies on suspension;
  - Bells 1-2 get no staff response, and Bell 5 has no end rule or campus-wide search;
  - hitting a monitor in a sparring area still adds Heat.

### 4. 2360 skies (branch sky-2360): art and ids done
- [ ] Check the proposal against the live Config.DayCycle. Wire the new DayCycle controller and SkyMotion, and load only the current and next set.
- [ ] Performance Simulator low-end pass; night readability, especially crimson and Nightmare nights.
- [ ] Merge: sky-2360's Night, NightBlue and Storm win over the 2.16 originals.

### 5. Quiet Corners UI (branch ui-quietcorners): design, art and crest ids done
- [ ] Implementation plan: the HUD layout, the Journal, the evidence wall, and the dialogue cards with the 9 animated crests (the Unaffiliated crest for anyone without a clique, never the Seal).
- [ ] Decide which current HUD parts it replaces.
- [ ] Build, install, tests (phone layout included), review, merge.

### 6. Housekeeping
- [ ] Commit the generated art and update .gitignore (in progress).
- [ ] Owner: check art/props/doors_batch25.json in the working folder (it lost its texture ids).
- [ ] Merge everything into main, bump the version, and remove the merged worktrees.
- [ ] Then the Discord posts.

## B. Later test rounds (started, paused)
- **Injury system** (E:\NH-injury, branch injury-system):
  - design and concept renders, then owner approval;
  - models for every body type;
  - the gameplay: body parts, severity tiers, supernatural injuries by race;
  - treatment items and the Nurse's procedures.
  - Gothic, no gore.
- **Race transformations** (E:\NH-transform, branch race-transformations):
  - survey, then 2-3 concepts per race, then the owner's picks;
  - full models fitted to every body type and gender, and the wiring.

## C. Not started
- Bell Tower R3 (witnesses) and R4 (the Almanac, Conduct Ledger, Journal redo, map layer): each needs a plan.
- Bell Tower polish:
  - UIShadow, contrast checks, the Input Action Manager, a Performance Simulator pass;
  - UI Particles once it leaves beta.
- Tutorial follow-ups:
  - production Tutorial.Enter, and the title hold against the Prologue;
  - journal replays;
  - server-judged beat prompts;
  - slice 2: the getaway, breakfast, arriving at school, the first homeroom.
- DevForum audits:
  - 2-4: shapecast hitboxes, wedge ramps, fog at quality level 1;
  - 5: the custom chat moves to TextChatService before May 2027.
- docs/Enhancement-Concepts-2026-11.md (28 items). Suggested order:
  1. A1, the tutorial;
  2. C8 (Bell Tower R2-R4) with B6 (the sneak loop);
  3. B4, impact hit reactions;
  4. B5, school parkour;
  5. D12, a lighting pass per region;
  6. G20, the daily school day;
  7. the rest.
