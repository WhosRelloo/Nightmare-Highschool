# Electives, starting with Anatomy: design

Date: 2026-11-25. Branch: `claude/electives-22bb10`. Test place: NH Combat Test (98950102230473).
Mockups: the claude.ai Design canvas "Electives: Anatomy" (five boards: Bench, Registrar, Specimens, Poses, Flow).

## Goal

Give Nightmare Highschool elective classes that you take for a term. Each elective has its own bench minigame,
played with rigged and animated models you pick up and use. Anatomy is the first elective and the reference
for the rest. It is a dissection class on clockwork automatons.

## Scope

In:
- The elective system: the Registrar, a term pick, set periods, and the `Classes.For` helper.
- The Bench engine (`Services.School.Bench` and `Controllers.Gui.Bench`) as planned in `docs/expansion/07-Technical-Architecture.md`.
- Anatomy end to end: three species, five physical tools, nine seated R6 clips, the PBR UI, grading, rewards, and substitutes.

Out (later specs): the other nine electives, exams, and the academic path.

## 1. Electives and the timetable

- **The ten electives (all four groups the owner picked).**
  - The core three: Anatomy, Workshop and Photography.
  - Ceramics and Herbology.
  - Home Ec and Sewing.
  - Art, PE and Theatre.
  - Only Anatomy is open at launch. The others show "Opens in a later term" and open one at a time, each with its own spec.
- **Enrolment.** A student picks one elective a term at the Registrar's desk (a model next to `NHEnrollDesk`),
  using a seal-card board. The pick holds for the term and can change when the next term begins. Pressing
  "Enrol" stamps the timetable with a wax seal.
  The data is `Classes.Electives = {Term = n, Pick = id}`.
- **Periods.** Electives run in Period 3 (10:00 to 10:40) and Period 4 (10:45 to 11:25) on Tuesday and Thursday.
  Those two slots now point to "Elective" in `Config.Classes.Periods`.
- **`Classes.For(segment, day, player)`.** This new helper returns the subject a player has in a slot. For an
  elective slot it gives their pick, or Study Hall if they haven't enrolled. The eight readers of
  `Config.Classes.Periods[Segment.Name]` switch to it: ClockHud, Moments, Timetable, Phone, KitUi, Attendance,
  Activities and Substitutes.
- **Room.** Anatomy is taught in R103 by Mr. Sallow, whose model is a mirrored desk model.

## 2. The bench (shared engine)

- **The view.** A ViewportFrame with a WorldModel, so the Animator plays inside it. It shows a close top-down view
  of the desk: the tray, the specimen and a leather tool roll. The player's seated R6 character sits at the bottom
  edge, and their arms reach into the frame.
- **Who decides.** The client sends intents: `Pick(tool)`, `Use(target, path)`, `Put(spot)` and `Place(part, slot)`.
  The server's game module accepts or rejects each one and keeps the score. The client only animates what the
  server allows.
- **Game modules.** Each elective plugs in through the Activities contract with `Bench = true`:
  `Start(S, Level, StartAt)`, `Tick(S, Now)`, `Handle(S, Action, Data, Now)`, `Score(S)` and `TimeLimit`.
  The modules live in `ServerStorage.Activities.AnatomyBench` and `Controllers.Gui.Activities.AnatomyBench`.
- **Grading.** Accuracy counts 60%, process 25% and time 15%. Grades run A+ to F, and a C passes.
- **Data.** `Classes.Anatomy.Bench = {BestScore, Recipes}` and a `Journal` of specimens you have completed.

## 3. Anatomy

### Species (data in `Config.Anatomy.Species`)

| Specimen | Level | Steps | Organs to place | Twist |
|---|---|---|---|---|
| Clockwork Frog (Rana Horologica) | 1 | Unwind, Trace, Pry, Lift | Heart-pump, Bellows lungs, Gear-gut | none |
| Clockwork Raven | 3 | adds Unscrew (wing plates) | adds Voice-box, Wing spring | from level 4, a Flag slot: one decoy part has to stay in |
| Clockwork Wyvern | 5, or from a substitute's crate | adds Inspect (Loupe) on the hidden seam | adds Fire-gland, Twin hearts | the Fire-gland must come out first or it Recoils |

The Frog row is the approved design. The Raven and Wyvern steps and twists are proposals for the owner to confirm
in the spec review. Adding a species is a data entry plus a rigid-rig model. The engine stays the same.

### The five physical tools

- **The tools and keys.** They sit on a leather roll in this order: **1 Key, 2 Driver, 3 Loupe, 4 Scalpel, 5 Tweezers**.
- **Picking up and putting down.**
  - Pick a tool up by clicking or tapping it, or with keys 1 to 5. It moves to your hand with the Lift clip.
  - Put it down with right-click or B. A tool dropped anywhere on the desk stays where it lands.
  - A tool dropped on the roll goes back to its slot. An empty slot shows a chalk outline.
- **Using tools.** Each tool works on its own part of the specimen:
  - Key: turn the side key to unwind the specimen.
  - Driver: unscrew the plates.
  - Loupe: find the seam.
  - Scalpel: trace the seam.
  - Tweezers: pinch an organ's lug and carry it to its outline on the Specimen card.
- **The models.** Each tool is a rigid-rig model with PBR materials taken from the school's seamless sets (Brass,
  Iron, Leather, DeskWood).
  - Screwdriver: a fluted rosewood handle and a knurled ferrule.
  - Tweezers: tapered arms with knurled pads.
  - Loupe: a knurled bezel, a convex lens and an ebony handle.
  - Pin-key: a trefoil bow.
  - Scalpel: a curved blade on a brass collar.

### The specimens are hollow

- **The shell.** A real wall 4.5 mm thick, lacquered inside, cut open under the belly plate. The plate is a porcelain
  dome on two hinge knuckles and opens like a lid.
- **Inside.** A mechanism deck seated in the wall, with:
  - bellows lungs between brass boards;
  - three spur gears on axles;
  - a mainspring in its barrel;
  - the heart cradle, linked by copper pipes.
- **Carving.** Every outside part that reaches into the hollow is carved flush with the inner wall: the legs, head,
  collar and key shaft. Nothing shows through inside.
- **No clipping.** It is checked in Blender with a BVH triangle-overlap pass (`clipcheck.py`) over every mesh in the
  scene. The only overlaps it allows are a written list of intended joins: rivets, pins, hinges, a seated deck,
  pipe ends and fused organ parts. The concept bench scene and the tool sheet both pass with 0 unexpected
  intersections. The same check runs on every new species before export.

### The R6 clips (seated, house style per the r6-animation-cinematics skill)

| Clip | When it plays |
|---|---|
| BenchIdle | sitting at the bench |
| Unwind | turning the key |
| Trace | following the seam with the scalpel |
| Pry | levering the plate open |
| Lift | picking up a tool or an organ |
| Recoil | after a mistake |
| Loupe | looking through the loupe |
| Write | filling in the Specimen card |
| Done | the final pose |

- **Putting down.** Lift played in reverse.
- **Unpublished clips.** In Studio they play through `KeyframeSequenceProvider:RegisterKeyframeSequence` from a
  ReplicatedStorage folder. The owner publishes them.

### UI (iron and candle family, Anatomy motif: the loupe and the oxblood seal)

- **Source.** The PBR chrome comes from `art/ui/hud/make_anatomy_ui.py`, using the house shader in `make_health_pbr.py`.
- **The pieces:**
  - AnatPlate: the title and timer on an iron plate with a loupe roundel.
  - AnatProcedure: the parchment step list with a brass tack.
  - AnatSpecimen: a porcelain card in a riveted brass frame, with organ outlines.
  - AnatSeal: the grade seal.
  - AnatHold: the hold ring.
  - AnatTag: the tool-key tags.
- **Building it.** The UI is built from `ReplicatedStorage.UI.Theme`, `Components` and `Motion`. The fonts are
  Cinzel and EB Garamond.

## 4. Substitutes

- **Joining the system.** Electives join `Config.Substitutes.Subjects`. The existing rules carry over: `LevelOffset`,
  `TimeMult`, `YenMult`, `DoubleOrNothing`, `Late` and `OnTimeExp`.
- **The Specimen twist.** This twist is new, and each substitute plays it differently:
  - Hollow brings a rare crate. It is the only way to reach the Wyvern before level 5.
  - Lazzaro bets on your grade (double or nothing).
  - Crane holds an Inspection, where every slip costs twice as much accuracy.
  - Moth brings a loose specimen. Its organs are shuffled, and the outlines are hidden until you use the Loupe.

## 5. Rewards

- **The Healer perk.** It grows with your Anatomy level: the medic pouch heals 10% more per level and revives are 8% faster per level.
- **The Specimen Journal.** One page per species you complete, showing your best grade.
- **Mastery.** Earning an A on all three species unlocks the "Anatomist" title and the Brass Loupe Monocle accessory.

## 6. Build and testing

- **Models.**
  - Blender is the source.
  - Multi-piece props use rigid rigs, following `docs/Pipeline-Lessons.md`: the `RIGID` table, then
    `<Prop>_rigid.json`, then import without "rig", then `rigid_rig.py`.
  - Check the import scale, since FBX imports come in about 100× too big.
  - Apply textures with `stage/textures.lua`.
- **Play checks.**
  - Run these in the slot 2 harness: enrol, sit at the bench, the frog end to end with an A, a deliberate Recoil,
    putting a tool down on the desk and on the roll, and a substitute Specimen twist.
  - The cine check runs before and after.
- **Coordination.** Only one session drives NH Combat Test at a time.
- **Results.** `tools/electives/REPORT.md` plus a publish list (models, clips and UI images for the owner to upload).
  The place is never saved without the owner's word.
