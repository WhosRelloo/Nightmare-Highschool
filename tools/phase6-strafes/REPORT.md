# phase6-strafes: build report (2026-11-22/23)

Commits 5297baa..73fa065 on phase6-strafes. Installed in NH Combat Test (Edit); slot 2 restored after every round; nothing saved. FIER ANIMATIONS read only (203 clips before and after).

## Checks without Play
- pytest bake.py: 16 pass; all 42 clips bake with every per-clip check passing.
- lc_pure, gs_pure: pass. Every script parses.
- clipcheck (42 clips in Studio): pass. infirmarycheck (room, region, beds, 64 bleacher seats): pass.

## Round B: movement (pass)
- strafecheck: server cap holds 8.5 studs/s; strafe clip 2.17x; planted foot slides 0.07-0.14 studs/s; chest within 0.3 deg of forward; diagonal 50/50; backpedal = Walk reversed; clean stop on release.
- footcheck: walk at 14.4 hits the 2.4x cap; ~18 % slide (old code 1.44x, ~51 %).
- cinegate: no strafe during cuts, approaches, seamless seam/hold.

## Round C: NPCs + Infirmary (pass)
- gestures: Talk plays; loops stop with no player within 80 studs; shove carries 7.12 studs (7.24 baked).
- get-up: downed -> recovered student plays Dizzy, then walks to the Infirmary and sits on a bed.
- Nurse Agatha Thorne at her post. healcheck: full heal; refused on cooldown / in a fight; cancelled on hit; stub rule set swap proves the pluggable seam.
- watch the match: an Athlete sits on the bleachers, cheers at a score, nobody left seated after the end. Players can sit.
- Fixes during Play: get-up walk starts after the idle; idle starts 0.35 s after recovery; probe positions; Studio debug attributes removed.

## Round D: tutorial regressions (CLEARED 2026-11-23, see tools/phase6-2350/REPORT.md on main)
- skipcheck FAILS ("controls still on mid-cut", "HUD still on"), and fails the same way with AnimationController + CineActor swapped back to pre-change copies. Cause under investigation.
- approachcheck did not run (the fence set never streamed in). checks/approachcheck_loco.lua expects the new cadence rule.

## Owner publish list
42 clips in ServerStorage.NHPublish.Gestures (table in tools/phase6-strafes/anim/PUBLISH_LIST.md). The two Square strafes replace the current strafe ids.

## Open rows
1. Round D regressions.
2. No screenshots (Studio screen capture unreachable): V1 square strafes, V2 18 % walk slide, V3 Praying kneel-in, V4 Infirmary room, V5 treatment gestures, V6 bleachers.
3. Bed seat height guessed at 2.1 studs (needs a viewport look).
4. Not built: the ambient patient on bed 1; the phone prop while walking.
5. The Infirmary spot not checked against the Map (Map closed). NH lot empty: x 199-225, z 13.5-39.5.
6. The 42 publishes, then the ids.

## 2026-11-23: published ids, idcheck, screenshots
- The owner published all 42 clips. Ids filled from the group (a184a91): 22 Id, 6 bucketed Ids (x3), the two square strafes.
  Installed Config.Gestures + Config.Locomotion in NH Combat Test.
- checks/idcheck.lua (Play, client): IDCHECK OK, 42 ids load (Length > 0), each within 0.05 s of the baked Len, Loop matches.
- Round D: the skipcheck "failure" was the harness (an unmarked __SeamlessTest replay); the whole tutorial suite passes on this
  build, and the cadence change is folded into approachcheck / TutorialSneak on main (da0bb56).
- Screenshots: docs/img/strafes-infirmary-room.jpg (3 beds; the room is bare: plain walls, no other furniture, no ceiling at this
  angle; the Nurse was off post at night), docs/img/strafes-square-strafe-pose.jpg (StrafeLeftSquare frozen at 30 %: chest square,
  legs crossing). The pray kneel shot was blocked by a crowded chapel: owner eye.
- Slot 2: fresh snapshot, restored; Play stopped; nothing saved.

## Open rows (updated; closed 2026-11-24 except the owner eye, see the section below)
1. Owner eye: the strafe look in motion, the pray kneel-in, the treatment gestures, the bleachers.
2. The Infirmary room is bare (furniture, cabinets, curtains, a ceiling) and the bed seat height (2.1) is still a guess.
3. Not built: the ambient patient on bed 1; the phone prop while walking.

## 2026-11-24: open rows closed on `phase6-infirmary` (see tools/phase6-infirmary/REPORT.md)
- Row 2: the Infirmary is furnished (ceiling, wainscot, bed curtains, medicine wall, desk, lights); the bed seat height
  2.1 is checked in the viewport and stays.
- Row 3: built: the ambient patient on bed 1 (AmbientNpcs, LayingIdle) and the phone on walking calls (Schedules).
- Row 1: screenshots V1-V6 are in docs/img/infirmary-v*.jpg for the owner's eye check; the checks themselves stay the
  owner's.
