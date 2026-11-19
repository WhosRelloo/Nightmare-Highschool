# 05. Class Redesign Specifications

## 1. Constraints and the approach

**What's there today:**
- Lessons are UI overlays with the character frozen at the desk.
- The framework (`School.Activities`) is solid: server-judged, graded, rewarded, and wired into attendance, report cards, factions and quests.

**What the redesign must not do:**
- It must **not add props or furniture to the map** (protection rule).

**The approach: the Bench.**
- A lesson opens a **3D workbench rendered in a ViewportFrame** over the desk view: a camera looking down at a tabletop, with real 3D models of the tools and materials.
- The models are taken from the existing prop libraries: the electives kit, the art-room kit, specimen jars, the chemistry glassware in `NHProps`, and new small models from the Blender pipeline where needed.
- The character sits at their desk in the real room (`PlayerSeats`), so classmates see them working.

**How interaction works:**
- Everything is drag, tap and hold, with **no precise-mouse-only input**.
- Each action has a large touch target and a gamepad path: a D-pad focus ring, A to grab, the stick to move, triggers to pour or press.
- **The server judges every action:** the client sends intents ("pour 12 ml from beaker A into flask B"), and the server simulates and scores. Clients render only.

**What stays:**
- The existing games remain as **Pop Quiz warm-ups** (the first 60 s of a lesson at class level 1-2) and as substitute twists.
- A bench lesson is the main course.

**Grading:**
- **Scale:** the same scale (A+ to F); a C passes.
- **Score parts:**
  - accuracy, 60%
  - process (the right order, no hazards), 25%
  - time, 15%
- **The rule:** speed never decides a grade alone.

**New mechanics per class level** (levels 1-5 already exist per subject):
- Each level **adds a mechanic**, not just a tighter timer.
- Level 3 unlocks a subject title.
- Level 5 unlocks a subject accessory and **Advanced Study**, a harder after-school variant at Night Study that pays Vigil standing, as today.

**Multiplayer:**
- Lessons stay personal by default. Classmates in the same period each run their own bench, and everyone can see them working at their desks.
- **Lab Partners (optional):** two players at adjacent desks can pair (prompt "Be my lab partner"). They share one bench with split roles. Each gets the shared grade, with a +5% teamwork bonus.

**Exams (new):**
- In the last school day of each term, one period per subject runs a mixed-mechanic exam.
- Exam grades feed the Academic path and the report card.

## 2. Mathematics: Applied Problem Solving

**The bench:** a drafting board, a brass ruler, a protractor, compasses, number tiles and a balance scale.

| Level | Mechanic added | Task example |
|---|---|---|
| 1 | Measure | Drag the ruler along a drawn shape and read the length; enter it on tiles. |
| 2 | Calculate | From the measured sides, compute the area or perimeter of a room plan (a blueprint of a school room). |
| 3 | Balance | Put number and operator tiles on a balance scale to make both sides equal (equations as physical weight). |
| 4 | Construct | Compasses and ruler constructions: bisect, draw a perpendicular, copy an angle, with tolerance checks. |
| 5 | Blueprint | A multi-step plan: "the bell rope must reach 3.2 m below the beam". Combine measuring, the scale and construction. |

- **Fail states:** a wrong reading (it can be retried, at an accuracy cost), or tiles that don't balance.
- **Hazards:** none. **Rewards:** Academic path, the title "Mathematician", the accessory "Brass Protractor Pin".
- **Story hook:** History and Maths blueprints of the bell tower (Chapter 3 clues).

## 3. Chemistry: the Practical Laboratory (priority)

**The bench:**
- **Glassware:** graduated cylinders, beakers, flasks, a pipette.
- **Ingredients:** labelled reagent bottles.
- **Heat and measurement:** a burner with a dial, a thermometer, a pressure gauge on the sealed flask.
- **The rest:** a recipe card and a waste jar.

| Level | Mechanic added | What you do |
|---|---|---|
| 1 | Measure and pour | Read the recipe, pick the bottle, pour into the graduated cylinder to the line (hold to pour; the meniscus shows), then transfer it. |
| 2 | Order | Mix in the right sequence; the wrong order gives a visible wrong reaction (colour, fizz), not instant failure. |
| 3 | Heat | Hold the temperature in a band with the burner dial while the reaction runs; overshoot boils over. |
| 4 | Pressure | A sealed flask: vent the valve to keep the pressure gauge in the green while heating; ignore it and it pops (a soot puff, no injury). |
| 5 | Unknown | Identify an unknown reagent with tests (flame colour, litmus, precipitate), then brew the counter-agent. |

- **What you see:** reactions are shown, not described: colour changes, foam, smoke, glow (`Fx` particles inside the ViewportFrame).
- **Fail states:** overflow, a wrong product, a pressure pop. Safety lapses lower the Process score.
- **Rewards (all earned in play):**
  - **Recipes**, unlocked by level:
    - Smoke Vial (L2), feeding into the prank system's equipment slot (`CliquePranks`);
    - Warming Draught (L3), an alternative to tea that clears Chill;
    - Glow Ink (L4), which marks walls faintly in the dark (Court flavour);
    - Ward Salt (L5), which deters a beast's approach for 10 s (Supernatural path).
  - **How you get them:** recipes are crafted at the Lab bench after class from ingredients bought at the existing shops.
  - **Lab access:** Advanced Lab Access at level 5.
- **Balance:** consumables are small, short and not pay-to-win; they can't be bought with Robux.

## 4. English: Writing and Communication

**The bench:** a writing desk with a typewriter, loose word tiles, a red pen, an inkwell and paper documents.

| Level | Mechanic added | Task |
|---|---|---|
| 1 | Sentence tiles | Build a correct sentence from movable word tiles (grammar is validated). |
| 2 | Proofread | Circle the errors in a short document with the red pen, then fix each one from choices. |
| 3 | Order | Arrange paragraph cards into a coherent story (cause and effect are checked). |
| 4 | Persuade | Build an argument: a claim, two evidence cards and a rebuttal, scored by fit. It's used later in dialogue. |
| 5 | Inconsistency | Read two accounts of one event and mark the contradictions. Tied to investigations. |

- **Rewards:**
  - **Persuasion level** unlocks *Persuade* choices in Dialogue (`ctx.Skill.English >= 4`), for example talking a monitor out of a write-up once a day.
  - Title "Wordsmith".

## 5. History: Historical Reconstruction

**The bench:**
- an artifact tray: coins, letters, photographs, medals
- a magnifier
- a timeline rail
- a folder of records

| Level | Mechanic added | Task |
|---|---|---|
| 1 | Examine | Rotate an artifact in 3D and find its date mark or crest with the magnifier. |
| 2 | Timeline | Place event cards on the rail in order (the founding in 1887, the bell in 1893, the fire...). |
| 3 | Match | Match documents to people by handwriting, seal and date. |
| 4 | Reconstruct | Rebuild an event from clues: who stood where (a top-down plan). |
| 5 | Record check | Find the forged or altered entry in a set of school records. |

- **The mystery:** History content is drawn from the story bible's [CANON] and approved [PROPOSED] lore. Some level 5 sets contain **real clues**: an altered register that adds a case Clue (`Grants{Case, Clue}` already exists on objectives).
- **Rewards:** Archive pages, lore, the title "Archivist", and access to the restricted Archive shelf (Chapter 2).

## 6. Electives (no new rooms)

| Elective | Where | Mechanic | Status |
|---|---|---|---|
| **Photography** | The whole campus (existing phone Camera) | Assignments: "a student mid-laugh", "the bell tower at dusk", "a reflection". The server checks the subject is in frame, plus distance, time and lighting from the camera pose. Photos go into a portfolio, and **story photos can catch things that aren't there**. | Approved, first |
| **PE** | The existing Gymnasium and Field | Drills (an obstacle line from existing training stations), dodgeball (an arena variant built on `Sports.Ball`), timed runs. | Approved |
| **Art** | A rotating existing classroom (the period's room), bench view | Trace, then sketch (follow the path), then paint (fill regions with mixed colours), then recreate from memory under time. Shares canvases with the Ink clique's Mural Duel. | Approved |
| **Workshop** | A rotating room, bench view | Follow a blueprint: pick the tools, assemble, fasten, test. Repair broken things (a lantern, a lock), which feeds the QOL kit's repair. | Approved |
| **Anatomy** (the dissection lab, revised) | Chemistry room, bench view | **Specimen look approved 2026-11-18 (the owner: "rigged and animated creatures", a mix):** level 1 is a **clockwork specimen** (a brass-and-porcelain automaton animal, gears ticking, panels that open on clockwork organs); later levels are **uncanny school creatures** preserved by the school (for example a two-headed bone bat, a mandrake toad, an ink eel), **rigged and animated**: they breathe, twitch and wriggle when you cut wrong. Insides are stylised (glowing organs, crystal bone, ink), never blood or gore. Five stages: prep and instrument choice, landmarks, opening in the right sequence (panels lift), identify organs, bones and tissues and spot the *abnormality*, then write the specimen report. Co-op roles: Lead, Assistant, Recorder. | Revised; needs your OK on the specimen look |

**Elective timetable:**
- Periods 3-4 on two days a week become **Elective** periods, and each student picks one elective per term at the Registrar (the Enrollment desk).
- This needs a per-student timetable (Schedules and Attendance both read it).

## 7. Acceptance criteria (per subject)
- **Each level adds its mechanic** and can be played on PC, touch and gamepad.
- **The server rejects impossible actions:**
  - pouring a reagent you don't hold
  - finishing before the minimum time
  - more than 20 actions a second
- **Grades:**
  - the score parts add up to the grade
  - the grade lands in Attendance, ReportCards, the class level and Path conditions
- **Lab Partners** works with two real clients, including when one disconnects mid-lesson: the other continues solo.
- **Phone layout** is tested at phone size (touch targets 44 px or more after AutoScale).
- **Performance:** the bench holds 60 fps on mid-range devices, with fewer than 150 parts in the viewport.
- **Visual identity:** each subject's bench looks distinct and fits the game (PBR textures, animated, per the UI rule).
