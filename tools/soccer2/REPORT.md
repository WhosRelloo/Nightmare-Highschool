# Soccer 2.0: report

Branch `soccer-2`. Plan `docs/superpowers/plans/2026-11-24-soccer-2-0.md`, spec
`docs/superpowers/specs/2026-11-24-soccer-2-0-design.md`. Installed in NH Combat Test (Edit). **Place not saved.**

## Final re-run (Task 6 Step 6, 2026-11-24)

Edit:
```
PASS soccer_pure
PASS soccer_clips_edit (25 clips; SoccerJog 6.754, SoccerJogBack 6.29, KeeperStep 7.129)
```
`soccer_clips_resolve` can't pass in the Edit VM: Studio keeps the pre-install `Config.Sports` require cached there
("attempt to index number with 'Was'"). Play VMs require fresh, so it runs in the Play round (ledger ruling, Task 3).

Play round (slot 2 fresh snapshot, restored after):
```
PASS CineState=nil Seen=nil Origin=nil
PASS soccer_clips_resolve
PASS live, InSport=Pitch
PASS soccer_play_pack
PASS soccer_play_moves
PASS ended
PASS soccer_play_pack_after
FAIL strafecheck            (speed line only: strafe speed 7.00 vs the check's 8.5)
restored
PASS CineState=nil Seen=nil Origin=nil
```
strafecheck: `locomotion-pace` set `Config.Locomotion.StrafeSpeed = 7` in the place (checked in Edit), so its 8.5 is
stale. Its animation lines print fine: StrafeLeft track 1.82x, legs 1.615, stance-foot slip 0.08 studs/s, chest 0.5 deg
off the root's facing. Soccer 2.0 doesn't touch the strafe walk.

## Per task

| Task | Commits | Checks |
|---|---|---|
| 1 Pure timing (`Soccer.Clips` maths) | c465266..b01bac2 | `PASS soccer_pure` |
| 2 Bake (`NHSoccerClips`, `Config.SoccerClips`) | b01bac2..022db3d | `PASS soccer_clips_edit (25 clips; SoccerJog 6.754, SoccerJogBack 6.29, KeeperStep 7.129)` |
| 3 Slots and resolution (`Config.Sports.SoccerAnims`, `Clips.Id`, `Drive`, `DashPath`) | 022db3d..5b79426 | `PASS soccer_clips_resolve` (Play) |
| 4 Kick, charge, moves, falls (`Controllers.Gui.Soccer`) | 5b79426..9523505 | `PASS live, InSport=Pitch`, `PASS soccer_play_moves`, `PASS ended` |
| 5 Soccer pack (`AnimationController.Override`, `SoccerPack`) | 9523505..59acb75 | `PASS soccer_play_pack`, `PASS respawned` (killed mid-match), `PASS soccer_play_pack_after` |
| 6 Demo, audits, docs | 59acb75..936f7a5 (+ report fix) | above |

## Strides and contact times

Strides (root travel per second at 1x): SoccerJog 6.754 (the Jog Forward spread rule gives 6.835, 1.2 % apart),
SoccerJogBack 6.29, KeeperStep 7.129. KeeperStep is the mean of two uneven steps (6.08 and 8.18).

Contact times (s) after the eye check:

| Clip | Contact |
|---|---|
| Strike Foward Jog_R6 | 0.43 |
| KickSoccerball_Right | 0.23 |
| Soccer Pass_R6 | 0.47 |
| Chip_R6 | **0.53** (was 0.47: the foot was still 1.2 high) |
| Scissor Kick_R6 | 0.68 |
| Soccer Penalty Kick_R6 | 0.73 |
| Soccer Spin_R6 | 0.23, 0.60 (0.60 low confidence: could be 0.65-0.70) |
| Soccer Tackle_R6 | **0.53** (was 0.10: the slide's low, forward point is 0.50-0.57) |

**Owner's eye wanted:** Tackle 0.53, Chip 0.53 and Spin 0.60. Shots: `docs/superpowers/mockups/2026-11-24-soccer-2-0/contact-*.png`.

## Demo and audits (Task 6 Step 4)

`soccer_demo.lua` (Client, in a solo match): jog, charge, kick, dribble, backpedal, dive.
`PASS soccer_demo 331 frames, 248396 bytes`. Video `docs/superpowers/mockups/2026-11-24-soccer-2-0/demo.mp4` (re-encoded
to 1280 wide and 30 fps to commit it), dump `demo_dump.json`.

**The video gates are skewed by the capture.** Studio's `video_capture` records 30 fps inside a 60 fps stream (903
frames in 30 s), so `motion_audit.py` sees every frame twice. The demo's waits add up to 9.1 s and the action spans
0.8-10.6 s of video, so the game ran at normal speed. The numbers are reported as measured:

| Gate | Target | Whole 30 s | Action stretch (0.8-10.6 s) |
|---|---|---|---|
| moving fraction | >= 85 % | 21.5 % | 62.2 % |
| frozen frames | < 3 % | 50.1 % | 51.8 % |
| duplicated frames in motion | none | 5.4 % | 26.1 % |
| fall / rise | | 1.11 | 0.82 |
| creeping hold (demo about 2.9-3.6 s) | no frozen frames | | a 1.48 s hold at 2.52 s of the stretch |

**Not passed:** moving fraction, frozen frames, duplicates, and the creeping hold: a 1.48 s hold falls in the creep
window. The doubled frames explain much of the frozen and duplicate figures, but not all of them, and this wasn't verified.
The creep may be too slow to register at this frame size, but that wasn't verified either. Sheets:
`audit/sheet_*.jpg` and `audit_action/sheet_*.jpg`, strips `audit/strip_3.0_4.0.jpg` and `audit_action/strip_2.0_3.0.jpg`,
graph `audit/motion.png`. By eye the sheets show the jog, the charge crouch, the kick, the backpedal and the dive in
order. The character is small in the frame.

Dump audits (`demo_dump.json`, one row per Heartbeat):

**Time base.** The audits assume 60 rows per second. The dump has 331 rows over the demo's 9.1 s of waits, about 36 Hz,
and no timestamps. The figures below are the audits' raw output: multiply their times by about 1.65 and divide their
speeds by about 1.65 to get rough real values. The real times are in brackets. They are estimates because the frame
rate wasn't constant. The demo's own timeline: jog 0.5-2.3 s, charge 2.7 s, kick 3.4 s, dribble 4.3 s, backpedal 5.6 s,
dive 7.5 s.

- **Jitter** (`jitter_audit.py`): no cuts.
  - 24 single-frame pops, including 2.03 (about 3.4), 2.60 (about 4.3), 3.38 (about 5.6), 4.53 (about 7.5) and 4.85 (about 8.0) s.
  - The big ones are 2.60 (torso and head, around the kick and dribble start) and 4.53 (right arm, the dive start).
  - 16 abrupt stops, at 1.43 (about 2.4), 1.65-1.68 (about 2.7), 2.10 (about 3.5), and 4.35-4.45 (about 7.2-7.3) s, among others.
  - Direction reversals peak at 2.5 (12) and 4.0 (14) raw.
  - **Camera not measured:** the demo writes a constant camera rotation, so the audit can't see rotation spikes.
- **Physics** (`physics_audit.py`):
  - The planted foot skates 4.14-10.63 studs/s raw, about 2.5-6.4 real (target < 0.6).
  - Planted-foot slide averages 5.6-15.8 raw, about 3.4-9.6 real.
  - Below the floor:
    - Right Leg 15 frames (min -0.82);
    - Left Leg 2 frames (-0.31);
    - Right Arm 42 frames (-0.81, the dive).
  - One airborne arc and 8 off-balance frames, both in the dive.
  - Fastest root travel: 76 raw, about 46 real studs/s (the dive dash).
- **Not passed:** the skate target. The dump is world space, so root travel (the jog, about 6.75 studs/s) counts as foot
  speed. The audit scripts are sed copies of the skill's video-keypoint scripts, so the skate figure is an upper bound,
  not a measured slide. Pops and abrupt stops aren't only on impact frames: the stops at about 2.4-2.7 s fall at the
  jog's end and the charge. Reported, not re-animated (brief rule). A re-run should record per-row time.

## Cine (every round)

Every Play round recorded `PASS CineState=nil Seen=nil Origin=nil` before and after, with slot 2 restored from that
round's fresh snapshot: Task 3 (1 round), Task 4 (RED, GREEN), Task 5 (RED, GREEN, fix), Task 6 (demo, final).

In the Task 6 demo round, `soccer_match_end.lua` printed `FAIL still InSport` because it was run through `run_check.py
Server`. That gets its own module copies ("no venue"); match checks go through `run_live.py Server`. The match was gone
and `InSport` was left on the player until Play stopped. The final round ran it through `run_live.py`: `PASS ended`.

## Not done

- **Publishing:** the 24 clips play through temporary ids in Studio only. See `tools/soccer2/PUBLISH_LIST.md`.
- **The goal cut** (spec: later).
- **2.1 / 2.2 triggers:** Chip, Stall (2.1) and Penalty (2.2) are baked and have slots, but nothing plays them yet.
- **The video and dump gates:** re-record with per-row time and the real camera rotation in the dump, and a closer
  camera. Studio's capture is 30 fps.
- Deferred minors are listed in the SDD ledger for the final review.

**Place not saved.**
