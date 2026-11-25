# The Infirmary and Nurse Agatha Thorne (phase6-strafes)

**Spec:** `docs/superpowers/specs/2026-11-22-strafes-npc-gestures-design.md` §5-§6.

## The room
- **`workspace.School.Infirmary`** is a new greybox room south of the hallway extension, opposite R106.
  - It spans x 199–225 and z 13.5–39.5, with the floor at y 1.1.
  - The door is in the north wall at x 215–219, between the hallway's potted plant and its vase.
- **Built from:** walls and floor cloned from R106, with props from `ServerStorage.NHProps`:
  - two DormBeds;
  - GlassCabinetTall, FilingCabinet and TeacherChair.
- **Builder:** `tools/phase6-strafes/build/infirmary.luau`.
- **Furnishing (phase6-infirmary):** `tools/phase6-infirmary/build/dress.luau` (re-runnable: it rebuilds
  `Infirmary.Dressing` and the `Props.Dress_*` models).
  - A coffered plaster ceiling on oak beams; oak wainscot, dado and cornice; a cased door.
  - Bed curtains: iron rails hung from the beams with bone-linen curtains, drawn back at each bed and closed between
    the beds. Nothing in the dressing collides except the ceiling, so patients walk through the curtain gap.
  - The medicine wall (east): apothecary drawers, the glass cabinet, the filing cabinet; on the south wall a jar shelf,
    the first-aid case, a sink with a mirror and towel rail.
  - The Nurse's desk (lamp, microscope, hourglass, test tubes, jars) with her chair; nightstands with lamps at both bed
    heads; a step stool, a damask rug, the anatomy skeleton, a radiator, a clock, a portrait and the rules board.
  - Light: two pendant lamps and three sconces with warm point lights, and the nightstand lamps.
- **Bed seat height:** 2.1 studs over the floor, checked in the viewport (2026-11-24): a sitting student's hips rest on
  the blanket.
- **The region:** `Regions.Infirmary` and `Config.Regions.Defs.Infirmary`.
- **Markers:**
  - `NursePost` (`NpcPost = "Nurse"`);
  - `NHInfirmaryBed1` and `NHInfirmaryBed2`, each with `SeatHeight`;
  - `NHInfirmarySpot1` and `NHInfirmarySpot2`.
- **Neither place had an infirmary before.** The Map place only has a showcase plaque.

## The Nurse
- **`Config.Npcs.Nurse`:** "Nurse Agatha Thorne", School Nurse.
  - She's at her post during the school day (Homeroom, Class and Other), and off campus otherwise.
  - Her dialogue tree is `ServerStorage.Dialogue.Nurse`.
- **At her post** she plays Inspect, ReachDown or KneelInspect every 12–25 s.

## Treating players: minimal and pluggable
An in-depth injury system, with custom injury models per body type, is coming as its own design. This build adds **no
injury states, visuals or models**. It has one entry point and a small swappable rule set.

- **`Features.Infirmary.Treat(Player)`** is called by the Nurse's "Get patched up" prompt (F, hold 0.5 s, within 8
  studs) and by her dialogue choice.
- **The interaction:**
  - The player and the Nurse face each other.
  - The player is slowed, as the Kit bandage does, and plays the Kit's own FirstAid clip.
  - The Nurse plays Inspect, then ReachDown.
  - It takes 3 s.
- **It cancels** on a hit, on being downed, when a combat tag starts, or when you walk away ("Hold still.").
- **`Features.Infirmary.Care`** holds the rules. The injury system replaces it through `Infirmary.SetCare`.
  - `CanTreat`: refused while combat-tagged, downed or carried; within the cooldown; or when you're not hurt.
  - `Apply`: full health, `NHBandagedUntil` set (as the Kit bandage does), `NHWounded` cleared, and the cooldown
    started.
  - `Cost`: free.
- **Owner defaults,** in `Config.Gestures.Treat` (confirm after playing):
  - free;
  - 3 s;
  - a full heal;
  - a 180 s cooldown per player, kept for the session only;
  - within 8 studs; it cancels past 6 more.
- **Health today, which this fits in with:**
  - `Progression` regenerates 2 % a second out of combat.
  - The Kit bandage channels for 2.5 s and heals 25 over 5 s.

## Patients
- **A student who gets back up after being downed** plays Dizzy or InjuredHurt for 5–8 s (`StudentBrain.Gestures`).
  The next time they replan outside class, they go to the infirmary:
  - they sit on the edge of a free bed, or stand at a spot with InjuredIdle or Dizzy;
  - for 60–120 s;
  - then they go back to their job.
- **Staff** who get back up play the same idle at their post.
- **Players and combat AI** never get it.
- **The ambient patient** (`Features.AmbientNpcs`, phase6-infirmary) lies on bed 1 with LayingIdle while the Nurse is
  on duty and no student has the bed. They appear and leave only with no player within 30 studs. The bed carries
  `NHAmbientPatient` while they're there; Schedules marks a bed a student is using with `NHInfirmaryTaken`.
- **Where sick students go:** bed 2, then the two standing spots, then bed 1 if the ambient patient isn't on it.
