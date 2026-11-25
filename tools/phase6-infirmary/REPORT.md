# phase6-infirmary: build report (2026-11-24)

The open rows from `tools/phase6-strafes/REPORT.md` ("Open rows (updated)"). Branch `phase6-infirmary`, cut from `main`
(6c018f0). Installed in NH Combat Test (Edit). Two Play rounds on slot 2, each with a fresh snapshot, cine recorded before
and after (CineState / Seen / Origin nil every time), restored, Play stopped. Nothing saved.

## What was built
| Row | Built | Where |
|---|---|---|
| The bare Infirmary | Furnished: coffered plaster ceiling on oak beams; oak wainscot, dado, cornice, door casing; iron curtain rails with bone-linen bed curtains (drawn back at each bed, closed between the beds); the medicine wall (apothecary drawers, glass cabinet, filing cabinet); a jar shelf, the first-aid case, sink, mirror and towel rail on the south wall; the Nurse's desk (lamp, microscope, hourglass, test tubes, jars) with her chair; nightstands and lamps at both bed heads; step stool, damask rug, anatomy skeleton, radiator, clock, portrait, rules board; two pendant lamps and three sconces with warm point lights | `build/dress.luau` (Edit, re-runnable: rebuilds `Infirmary.Dressing` + `Props.Dress_*`) |
| Bed seat height | **2.1 stays.** Checked in the viewport: a student sitting on bed 2's edge has the hips on the blanket (torso bottom 3.24, bedding top 3.20) | `docs/img/infirmary-bed-seat-height.jpg` |
| Ambient patient, bed 1 | `Features.AmbientNpcs`: a scenery student lies on bed 1 with LayingIdle while the Nurse is on duty and no student has the bed; shows / leaves only with no player within 30 studs. Laid by `Local.LieOn` (turned head-to-pillow, torso centred, body on the bedding top) | `live/ServerScriptService.Services.Features.AmbientNpcs.luau` |
| Sick students' bed order | Bed 2, then the two standing spots, then bed 1 only when the patient isn't on it (`NHAmbientPatient` on the bed; Schedules sets `NHInfirmaryTaken` on a place in use) | `live/ServerScriptService.Services.Features.Schedules.luau` |
| Phone while walking | `Schedules.WalkTo`: a walking call (PhoneWalk, PhoneTalk_Upper) equips StudentBrain's fidget phone, removed when the walk ends; none if the student already holds a phone | same |
| Test probe | `ServerStorage.NHInfirmaryProbe` (Studio only): Patient show / hide / get, Place, Phone, PhoneOff, Walk, SitBed | AmbientNpcs `Local.Probe`, Schedules `Shared.InfirmaryForTests` |

Backups: `ServerStorage.NH_Backup.phase6infirmary_pre` (the originals), `_stage1`..`_stage3` (the in-between installs).

## Checks
- Edit: `checks/roomcheck.lua` PASS (31 pleats, 3 rails, 9 lights, 34 props, nothing collides but the ceiling, every prop
  inside the walls, the spots / Nurse post / bed edges clear). `phase6-strafes/checks/infirmarycheck.lua` PASS.
- Play round 1: patientcheck PASS (the loop showed the patient on its own; torso (202.60, 3.58, 19.90), head toward the
  pillow at z 21.09, flat, on the bedding top 3.20; first place for a sick student = bed 2). roomcheck PASS.
  phonecheck FAIL: the probe walk hit the 20 s gesture cooldown (the call clip never started). The probe now clears the
  cooldown before its walk; the game's own cooldown and 20 % roll are unchanged.
- Play round 2: phonecheck PASS (phone in the right hand while walking, 31 studs on PhoneTalk_Upper; gone after);
  patientcheck PASS; roomcheck PASS. Regressions from phase6-strafes: getupcheck PASS (a recovered student goes to the
  infirmary), healcheck PASS, nursecheck PASS, footcheck PASS (live walk 9.29 studs/s, Walk track 1.56x, stance-foot
  slip 0.27 studs/s = 3 %).
- gesturecheck FAIL on one row: the shove carry measured 10.33 then 8.23 studs (limit 7.8, baked 7.24). This branch
  doesn't touch `StudentBrain.Gestures` or the carry; likely the student's own stroll adds to it (NPC gait changed in
  `locomotion-pace` after phase6-strafes). Open row below.

## Map check
Not done: the Map place (111107083446202) isn't open in any Studio, and opening it is the owner's call. The room sits on
the NH lot recorded as empty (x 199-225, z 13.5-39.5); `infirmarycheck` finds nothing of the room overlapping R106,
BoilerYard or the hallway in NH Combat Test.

## Screenshots for the owner's eye checks
| | What | File |
|---|---|---|
| V1 | Square strafe in motion (lock-on, chest square to camera, legs crossing): two frames | `docs/img/infirmary-v1-square-strafe.jpg` |
| V2 | The walk at the live speed (10; footcheck: 3 % slip). The 18 % figure was the old 14.4 walk, before `locomotion-pace` | `docs/img/infirmary-v2-walk.jpg` |
| V3 | Praying kneel-in, the real bucketed clip frozen at 25 / 50 / 80 % | `docs/img/infirmary-v3-pray-kneel-in.jpg` |
| V4 | The Infirmary: from the door, toward the beds, and in Play (the Nurse at her post) | `docs/img/infirmary-v4-room-door.jpg`, `-room-beds.jpg`, `-room-play.jpg` |
| V5 | Treatment: the Nurse's Inspect and ReachDown with the player's FirstAid (clips held looped for the photo; the real treatment is 3 s) | `docs/img/infirmary-v5-treat-inspect.jpg`, `-treat-reachdown.jpg` |
| V6 | Bleachers: an Athlete seated, cheering at a score | `docs/img/infirmary-v6-bleachers.jpg` |
| + | The ambient patient on bed 1; the phone on a walking call; the bed seat height | `docs/img/infirmary-patient-bed1.jpg`, `-phone-walk.jpg`, `-bed-seat-height.jpg` |

## Seen in the screenshots (for the owner)
- **ReachDown clips into the player:** at the treatment's 3-stud spacing the Nurse's bow puts her head and arms into the
  player's chest (V5 ReachDown).
- **The Nurse has no look:** Nurse Agatha Thorne renders as the plain default rig (bald, smiley face, green shirt), not
  a uniformed staff member.
- **Bleacher pile-up:** several students stacked into each other on the Gymnasium's bottom row near seat 66_1_1 during a
  match (`docs/img/infirmary-v6-bleachers-pileup.jpg`).
- The patient's LayingIdle is a knees-up, hands-behind-the-head rest; read it from above as "lounging" rather than "ill".

## Open rows
1. Owner eye: V1-V6 (above), the furnishing, the patient's pose.
2. gesturecheck's shove carry overshoots (8.2-10.3 studs vs 7.8): not from this branch.
3. ReachDown clipping, the Nurse's missing look, the bleacher pile-up (above).
4. The Map place check (needs the Map open).
