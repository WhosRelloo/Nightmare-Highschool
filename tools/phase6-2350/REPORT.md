# 2.35.0 slice 1 acceptance report (Tutorial seamless cinematics)

Run on Studio slot 2 (NH Combat Test), Play, code at commit 4f4645e plus the earlier task commits. Studio throttles when unfocused: runs were
15 fps (median frame 66 ms); every acceleration number uses the real per-sample frame time.

## Step 1: measured checks

| Check | Result |
|---|---|
| CineSeamTest (bridge) | CineSeamTest OK |
| CineRigsTest (bridge) | CineRigsTest OK |
| SeamlessHoldTest (bridge) | Protected, Tutorial, Session, InCine true; Checkpoint `__SeamlessTest:Start`; group TutorialPlayers; not anchored |
| camcheck `__SeamlessTest` | CAM OK. Worst max/median: In pos 1.47, BeatOut pos 2.02 (bound 2.5 x 1.5); release error 0.0001 st, 0.0000 deg; look and day grade ok |
| camcheck `TutorialBus` | CAM OK (hold: frozen frames, drift 0.00000 st, 0.0000 deg, NHCineHold true, Scriptable). The first run said NOT HELD by 0.02 deg: the check measured acos(dot) of identical float32 vectors; fixed to the chord form |
| camcheck `TutorialSneak` | CAM OK (In 1.34, BeatOut 2.95, Out 1.62; release 0.0007 st) |
| camcheck TutorialSneak fail path x5 (BeatIn jerk re-sample) | CAM OK on all 5. BeatIn pos max/median per run: 46.58/20.42, 47.57/20.44, 51.71/19.73, 47.69/20.60, 52.18/19.06. The earlier 73/17 jerk did not reproduce |
| bodycheck `TheBus` | BODY OK: TheBus1 switch peak 72 (p99 76), TheBus2 20, re-seat 34; 0 duplicate frames |
| sneakcheck sneak / fail / skipfence / timeout, after the re-imported house | all four SNEAK OK; lamp rows (on at the wuff, off at the sigh) ok; closest approach 9.10 st |
| Regressions after the fixes | hometowncheck PASS, replayrefused OK, beatcheck OK, skipcheck ok, buscheck BUS OK, holdcheck timeout OK and leave OK, reducecheck OK, dipcheck OK |

Lint note: `[Cine] ... [fix] shot 1 turns ... from the gameplay camera` appeared when the test camera sat in front of the player after a teleport
(same as T10); not a play-path finding.

## Deferred items fixed (commit 4f4645e)

1. Dip token: CineUI.Veil bumps a generation; Dip lifts its veil only if no newer veil or dip claimed it, and if claimed it holds black
   (replaces the other tween). dipcheck: RED on the old code (veil rose to 1.0 inside a second dip; a Veil(1, 0) inside a dip was un-blacked),
   GREEN now (veil stays 0.000 across the second dip, a single dip still lifts).
2. Replay checkpoints: Cine.Play and OnSeg write no checkpoint when S.Replay. Evidence: a `__SeamlessTest` replay left Origin at the earlier
   `TutorialSneak:Fence` (it would have read `__SeamlessTest:...`). Not run RED on the old code.
3. Re-seat vs skip: CineActor.Release bumps Gen synchronously and Cine releases the actor before the skip's dip, so a pending re-seat's root
   write is cancelled (its guard runs right before the write, no yield between). Measured: a Skip sent 5.0, 5.3, 5.5, 5.7 and 5.9 s into the Fence
   segment (spans the re-seat) lands on FenceLand every time (z 4077.50, 2.15 past the far face), standing, facing away, crouch false, seam nil.
4. sneakcheck: the dead 1.3 s sub-window removed (first-pass speed rows use the same 1.5 s window as the crouch rows); SKIP_DELAY parameter added.
5. Resume: the plan's "two-line" resume did not exist in World.Tutorial. Added `Tutorial.Resume(Player)` (checkpoint `<Cut>:<Segment>` -> the set's
   mark named like the segment, else `<Segment>Zone`, else `Start`, 3 studs up), called from Enter and from the respawn connection.

## Step 2: playtest matrix

| Case | Result | Note |
|---|---|---|
| Solo | PASS | Both cuts run end to end: sneak (Garden>Fence, with skip and timeout variants) and bus (arrive, board, hold, timeout release); all checks above |
| Two players | NOT RUN: OWNER | The MCP drives one client (no multi-client mode in start_stop_play; rbxc runs Edit/Server/Client of one session). Hometown's hiding has 33 single-player rows and the collision group was verified; see manual steps below |
| Death mid-beat | PASS | Killed 4 s into the Garden beat: respawned on `Start` (checkpoint `TutorialSneak:Garden`, 3994,3,4104), camera Custom and behind the player (look dot 0.83, 12.6 st). The cut is not restarted (state Started, not Seen). After the sneak is Seen the respawn lands on FenceLand; a bus death mid-cut (10 s) and under the hold (33 s) both respawn at the Stand mark (resumecheck, 5 rows) |
| Rejoin | PASS (bridge Enter) | Stop and Play again: Origin.Checkpoint persisted; the bridge's TutorialEnter put the player on the checkpoint's mark. The production caller of Tutorial.Enter is deferred (not wired in slice 1), so the real rejoin path is not exercised |
| Reduce Motion on | PASS | reducecheck OK: In/Out are 0.2 s dips (0 visible camera changes, veil peak 1.00). Measured with NHReducedMotion on (camcheck motion row, sneak): horizon roll 0.00 to 0.00 deg in every phase, and the Fence shot is 100 % still (no handheld: every frame under 0.003 st and 0.03 deg) |
| Phone | PARTIAL: OWNER | The device emulator is not driven by this harness. Static facts: CineUI.textSize floors subtitle text at 20 px; the skip button is 190 x 64 px at the bottom right with a 48 px seal |

Manual two-player steps (owner): Test > Clients and Servers > Local Server, 2 players, both Play, both reach the tutorial (TutorialEnter).
Watch: (a) each client sees only its own character, Biscuit and bus (the other player never appears, including a tool or accessory equipped later);
(b) walk into the other player's spot: no collision; (c) both start TutorialSneak at once: each has their own Biscuit and bus;
(d) reset one player: they respawn on the checkpoint mark and the other client still does not see them; (e) no `[Hometown]` errors in Output.

## Step 3: house style (no video)

`video_capture` fails with NoSpaceOnDevice (drive C: has 1.3 GB free), so there is no mp4 and no motion_audit.py run. The screen_capture
fallback was tried: it renders one still from a camera position and look point you give it (HUD included); it cannot capture the running
cut or a frame sequence of it, so it gives framing stills only (the Fence key-0 framing was captured: gate centred, far side in view,
level). Substitute: the engine camera sampled every frame (camcheck's `motion` rows: same-phase frame pairs only, so phase boundaries
never count; "still" = under 0.003 st and 0.03 deg a frame).

Findings and fixes (fix round 1):
- Roll: the sneak's one-way roll (-1.83 deg, -3.1 in the glide in) came from the quaternion slerp between two LEVEL cameras that differ in yaw
  and pitch (CFrame:Lerp in Seam.Blend and the glide's rotation slerp tilt the horizon in between). Seam.Rot now slerps the look on its great
  circle and eases the ends' own rolls; Seam.Blend and GlideTrack use it. A second source, on the framed shots of the bus and the test cut
  (-1.4 to -1.6 deg): the screen-placement yaw in Cine.framedCFrame turns about the camera's local up. Levelled there too (Cine.framedCFrame
  is the shared toolkit: every framed shot in the game now has a level horizon).
- Locked camera: the Fence shot is now a moving hold (a 1.7-stud push with a drifting aim, keys, level).
- The bus's held title freeze-frame is deliberate and exempt.

| Cut | Before | After |
|---|---|---|
| `__SeamlessTest` | still 66.8 %, longest 3.37 s, roll -1.40 to 0.00 | still 65.5 %, longest 3.31 s (the walk beat), roll -0.01 to 0.01 |
| `TutorialBus` (to the hold) | still 74.4 %, longest 9.60 s, roll -1.40 to 0.93 | still 74.3 %, longest 9.58 s, roll 0.00 (the freeze-frame hold is exempt; the shots on the parked bus are the rest, see Open rows) |
| `TutorialSneak` sneak path | still 49.5 %, longest 6.16 s, roll -1.83 to 0.00 | still 14.2 %, longest 0.87 s, roll 0.00; Fence shot (phase Cut) 27.5 % still, longest 0.83 s |
| `TutorialSneak` fail path | not measured | still 40.0 %, longest 6.19 s (the 7.2 s Hide beat holds still while Biscuit stares), roll -0.05 to 0.01 |

Real clips are still needed for motion_audit's pixel-level numbers:
`python ~/.claude/skills/r6-animation-cinematics/scripts/motion_audit.py <clip.mp4> OUT --strip <t0> <t1> 30` around the glide in, the doors and the fence.

## Fix round 1 (review CHANGES REQUIRED)

- I1 Dip token: Veil records `VeilTarget`; the dip forces black at its midpoint only if the latest claim still wants black, and lifts unless a
  newer black claim is pending (`VeilGen == Mine or VeilTarget == 0`). Reduce Motion's delayed `Veil(0, 0.1)` in the beat entry is guarded with
  `Cut.Live`. dipcheck gained two cases (a 0.25 dip inside a 0.3 dip at d = 0.01; a `Veil(0, 0.1)` inside a dip): RED on the 4f4645e code
  (both ended black), GREEN now (7 rows).
- I2 Tutorial.Resume: each cut declares `Resume = { Marks = segment -> mark, End = mark }` in Config.Cine (TutorialSneak: Start, Garden, Hide ->
  Start, Fence -> FenceZone, End FenceLand; TutorialBus: Start, Main -> Stand, End Stand). A Seen cut resumes at End; an unmapped segment or a
  missing mark warns and leaves the player where the game put them. checks/resumecheck.py: 5 rows pass.
- Motion: see Step 3. CineSeamTest gained a level-horizon row.
- Minors: M1 and M2 in the matrix; M3 in Step 3; M4 the motion row counts same-phase pairs only.
- Published player clips: all 66 are in Config.CineClips and verified in Play (checks/tutorialclips.lua: every id loads with Length > 0; Length and Looped match the KeyframeSequence and the chain step). TheBus1_WaitBored plays from rbxassetid://74294967099318, FenceOver2 from rbxassetid://137091473855957; bodycheck and sneakcheck resolve through Config.CineClips.
- Older cuts after the framing change: Strikethrough both paths (S and D; the authored -8 deg keyed roll is intact), Collected and RollCall pass. The NPC talk cinematic has no check: unchecked.
- RollCall outlier: one RollCall run read roll -13.5 to 11.1 deg and did not reproduce in 3 reruns (max -0.56). Judged a harness artifact, most likely frames sampled while another camera owned the view.
- Regressions after the last install (fresh Play): CineSeamTest, CineRigsTest, camcheck seamless/bus/sneak/fail, bodycheck, skipcheck,
  reducecheck, beatcheck, hometowncheck, replayrefused, holdcheck timeout and leave, buscheck, dipcheck, sneakcheck x4 and a skip at 5.5 s: all pass.
  Run dipcheck last in a session: it builds a second NHCineUI gui in the client VM that confuses the veil-reading checks.

## Task 14: walking into placed animations (2026-11-22, fresh Play, slot 2)

Studio was unfocused for the whole round: frames ran at 67 ms to 200 ms. Rows that need real-time frames are marked.
- skipcheck: ok (first, as required).
- camcheck: `__SeamlessTest` OK; TutorialSneak OK (BeatOut ok); TutorialBus OK in 2 of 3 runs. The failing run had an In-phase
  edge JERK (pos edge/median 9.7) at 67 ms frames. It did not repeat (the next runs read 1.69 and 0.84). Judged a
  frame artifact, as in the earlier bus runs; an owner watch row is below.
- approachcheck: fence OK (0 slides, 0 spins, idle gap 0, the piece started 0.27 s before the stop, heading 41 deg,
  clearance 0.54 walking up, 0.51 in FenceOver1, 0.15 in FenceOver2's first 0.5 s); bus short OK twice (arrival
  0.03-0.06 studs); bus from the side (-4, 0, 2) OK (arrival 0.17 studs, heading 0.0 after the settle). The check's
  suggested long offset (6, 0, 8) puts the player over the void at this stage (no ground under it), so that variant isn't valid here.
- sneakcheck: skipfence OK; timeout OK (Length 1 and TimeoutPad 2.5 set on the server; the cut ended at 7.9 s on
  FenceLand); sneak and fail pass every row except two that need real-time frames: "dip root jump under black on both
  frames" (at 200 ms frames the 0.3 s dip falls between samples) and the fail path's "walk speed on the second Garden
  pass" (0 moving frames sampled). NOT VERIFIED at real-time frames.
- buscheck BUS OK (TheBus2 at 17.15 s, hidden from 20.75 s, hold from 30.38 s); beatcheck BEAT OK; holdcheck timeout
  OK (10.17 s) and leave OK; resumecheck 5/5; hometowncheck PASS; replayrefused OK.
- bodycheck and dipcheck: NOT RUN this round (they need real-time frames). Both passed after the final fix round,
  and Task 14 changed neither CineUI.Dip nor the re-seat.
- Slot 2 restored from this round's snapshot; CineState {Collected=Seen} before and after, Origin unchanged. Only
  Discipline.LastDecayDay moved, because an in-game day passed.

### Fix round 1 (2026-11-22, review CHANGES REQUIRED; five fresh Play rounds on slot 2, frames at 16.6-17 ms)

Studio ran at full rate this round, so the real-time rows were judged too. RED was shown on the old code first for the new
approachcheck rows.
- **I1, fixed.** FenceOver1 walked on the spot after the stop. Approachcheck WALK ON THE SPOT read 1.47 s on the old code (RED). Now:
  - FenceOver1 enters at the live CrouchWalk's phase and plays at its live Speed (`Chain` Opts `Pace`).
  - Its loop is cued on the arrival.
  - At the stop, a cover track holds the planted pose while FenceOver2 takes over underneath, and the cover fades out over 0.3 s.
  - Walk on the spot is now 0 frames in 4 runs.
- **I2, fixed.** The pace ramps from the walk you have. Two seam stalls were fixed as well: the Begin-ease wait, and `Ctl:Disable()`'s zero move.
  - Seam speed was 10-12 % on the old code (RED); it is now 72-84 %.
- **I3, fixed.** Approach returns "died".
  - `Fallback(Mark, Why, Alive)` places nothing on died/released/nochar, and the callers skip the chain.
  - The fall height comes from a raycast under the mark.
  - Probe (kill as the approach starts): no fallback, no dip, no chain.
- **I4, fixed by timing.** The bus walk starts 0.25 s after the glide, with NearSkip (within 0.5 studs and 45 deg: no walk).
  - Bus camcheck: OK 3 of 3.
- **M1, fixed.** The settle turn runs about the current position. Reseat and Release cancel it. It is capped at 20 deg; a walk more than 45 deg off goes round the lead-in again.
  - Settle measured 4.8-17 deg, residual 0.
- **M2, M4, M5, fixed.**
  - M2: Fallback's place checks liveness, including in the nested dip.
  - M4: AutoRotate is forced on during the walk.
  - M5: an on-screen jump that isn't the re-seat now FAILs.
- **New, found and fixed.** OnNear ignored the ease-out, so the bus's waiting loop began 0.68 s before the stop, over walking legs.
  - New row LEAD (≤ 0.45 s): RED 0.68 s on the old code, now 0.17-0.22 s.
- **Deferred by ruling:** M3, M6, M7, M9, M10.

Results on the final build:
- skipcheck: ok.
- camcheck: `__SeamlessTest`, TutorialSneak and TutorialBus ×3 all OK.
- approachcheck: fence OK, bus short OK, bus side (-4, 0, 2) OK.
  - Walk on the spot 0; seam 81-84 %; settle turn 4.8-17 deg over every fix round 1 run (7-14.5 on these final runs), residual 0; on-screen jumps 0; lead 0.17-0.22 s.
  - Fence clearance: 0.47-0.55 walking up, 0.05-0.06 at the climb.
- sneakcheck: sneak, fail, skipfence and timeout all OK. The dip-under-black rows now pass at real-time frames.
- buscheck: BUS OK (TheBus2 at 17.00 s).
  - One run failed the base-loop row on 177 frames, all before the cut. That was the previous run's leftover cast (NHTutorial still set). After a TutorialLeave it reads 0 frames.
- beatcheck OK; holdcheck timeout OK (10.20 s) and leave OK; resumecheck 5/5; hometowncheck PASS; replayrefused OK.
- bodycheck BODY OK at 60 fps (it covers the TheBus chain only).
- dipcheck DIP OK (run last).

On-screen root placements were audited; the list is in `task-14-report.md`. On screen there are only:
- the capped settle turn;
- the re-seats (pose to identical pose).

Every other move happens at full black.

Slot 2 was restored from each round's fresh snapshot:
- CineState was {Collected=Seen} before and after every round.
- The checkpoint was cleared (Origin `{}`).
- The only difference from the snapshot is Discipline.LastDecayDay (an in-game day passed).

### Fix round 2 (2026-11-22, re-review ADDRESSED WITH FOLLOW-UPS; fresh Play rounds on slot 2, frames at 16.6-17 ms)

- **I-1, fixed.** The NearSkip branch zeroes the move before it returns. A walk handed on through the ease wait or Begin's re-issue
  now stops there.
- **I-2, fixed.**
  - FenceOver1's Pace now comes from root speed: flat velocity / 7, clamped to [0, 1.2].
  - New approachcheck row CADENCE: a walk cycle's speed against v / stride, within 25 %, while v > 0.5.
  - It was not RED on the old code for the fence (2 of 288 frames out): the live CrouchWalk already followed the root there.
  - It did catch the game's own Walk on the bus walk at up to 143 % off. The AnimationController only resets that speed on
    Humanoid.Running events, which lag a pace that changes every frame.
  - Fixes:
    - During an approach, CineActor drives the live Core locomotion track's speed from the root's flat speed every PreAnimation.
    - The turn slow-down (TurnPace) is eased (at most 3 a second). It used to snap a walk from 11 to under 5 studs/s in two frames.
    - TurnPace is floored at 75 % on the way to the lead-in corner.
  - A rate limit on the whole pace was tried and dropped: it broke OnNear's timing (bus side LEAD went to 0.90 s).
  - Ruling taken for the row:
    - HARD for the chain's own walk cycle on every frame, and for the game's locomotion on steady frames (acceleration
      ≤ 15 studs/s²).
    - INFO for the game's own Walk on the start/stop transients (a standing start, the last stud). Those are the same start and
      stop blends the AnimationController shows in normal play, and this slice must use the game's own locomotion.
  - Final: fence 0 of 245-247 frames out, worst 7-15 %; bus short 0 of 4; bus side 0 of 11-12.
  - Transients (info): 1 of 45-46 frames out on the fence; 3 of 13-46 on the bus (worst 35-70 %).
- **I-3, done.** A probe TutorialSneak forced the exit-phase branch. The probe opens the cue at 0.8 studs instead of 0.5 and shifts
  FenceOver1's entry so the exit comes at 0.35 studs left.
  - On the final CineActor, FenceOver2 started WHILE WALKING in 2 of 2 runs (Left 0.40 and 0.43), and the root stopped on that frame.
  - Clearance in FenceOver2's first 0.5 s: 0.20 (0.10-0.12 on the earlier build).
  - Settle -14.2 / -13.9 deg, residual 0; on-screen jumps 0; CADENCE 0 out.
  - With the production values (cue at 0.5, exit aimed at 0.40 studs left), the branch was missed 2 of 2 times. The exit came a frame
    or two after the cue opened, so the cover hand-off ran instead.
  - So in production the branch is rare by design: the window is about 0.5 down to 0.25 studs.
  - The real TutorialSneak was reinstalled after the probe.
- **m-1, fixed.** groundBelow uses RespectCanCollide and casts from 2 studs up. A hit above the point is refused (a mark part may sit
  1 stud into the floor). LastRise is clamped to [1, 6].
- **m-2, fixed.** Approaching / NHApproach is a depth count.
- **m-3, fixed.** On the wrapper's error path the cadence hook is disconnected and the move, WalkSpeed and AutoRotate are put back.
- **m-4, fixed (superseded in fix round 3: NearSkip gates at 45 deg again).** NearSkip only applied within TurnMax (20 deg), and its settle was capped at TurnMax.
  - New run "bus on the mark": placed on Stand, turned 10 deg. OK: 0 walking frames; settle -10.0 deg, residual 0; lead 0.
- **m-5:** left as is, by ruling.

Results on the final build:
- skipcheck: ok.
- approachcheck: fence OK ×2 (seam 83 / 91 %, settle -16.4 / -15.7 deg, clearance 0.60-0.61 walking up and 0.12-0.13 at the climb);
  bus short OK (settle 2.2 deg); bus side OK (settle -19.2 deg); bus on the mark OK.
- sneakcheck: sneak OK ×2 and skipfence OK.
- camcheck bus: OK (In edges 16 against a median of 25).

Over all fix round 2 runs on this build the settle turn is 2.2-19.2 deg, residual 0.

Not re-run (no change to their code paths): camcheck seamless/sneak, sneakcheck fail/timeout, buscheck, beatcheck, holdcheck,
resumecheck, hometowncheck, replayrefused, bodycheck, dipcheck.

Slot 2 was restored from each round's fresh snapshot:
- CineState was {Collected=Seen} before and after.
- Origin `{}` before and after.
- The final snapshot comparison shows no differences.

### Fix round 3 (2026-11-22, review CHANGES REQUIRED, one Important item; one fresh Play round on slot 2)

- **Important, fixed.** The fence SEAM SPEED row was flaky.
  - A walk handed on (Up0 > 0.5) now keeps the turn slow-down at 90 % or more for its first 0.3 s (the hand-on grace).
  - LEAD_IN is 3.5 (was 3.0).
  - The seam speed is now a 5-frame average (was 3). The one failing run kept a steady WalkSpeed of 6.3 (90 %), while per-frame
    displacement alternated 3.1 / 9.4 / 3.6 / 10.7. That is render frames with and without a physics step, so the 3-frame average still
    caught the beat.
  - The row also prints the WalkSpeed asked for. Across 6 runs it never dropped below 6.30 (89-92 %).
  - Results:
    - approachcheck fence 6 of 6 OK with the 5-frame row. Seam 79-91 %; settle -9.6 to -14.7 deg, residual 0.
    - Clearance after the LEAD_IN change: 0.59-0.70 walking up, 0.15-0.23 in FenceOver2's first 0.5 s (was 0.05-0.13).
    - On the 3-frame row before the change: 3 of 4 (one at 68 % at 0.08 s, the jitter above).
    - sneakcheck: the torso faces the fence at 7.5-9.2 deg as FenceOver2 starts (was 14.2-14.4).
- **Minor 1, fixed.** NearSkip gates at 45 deg again, and this one settle may turn up to 45 deg (at most 45 deg/s on average). The only
  other way round is the out-and-back I4 removed. approachcheck allows 45 on the mark.
  - Bus on the mark at 10 deg: OK, turn -10.0.
  - Bus on the mark at 35 deg: OK, turn -30.5 by the 0.6 s sample, residual 4.5, 0 walking frames.
- **Minor 2, fixed.** WalkSpeed and AutoRotate are captured when the depth goes from 0 to 1, and only the outermost approach puts them back.
- **Minor 3, fixed.** The fallback raycast excludes every player's character.
- **Minor 4, fixed.** The near-skip text is current again (45 deg). The CADENCE comment says that on the game's locomotion it proves the
  cadence hook ran, not that the stride constants match each clip.
- **Optional, taken.** The bus Approach has LeadIn = 4 (ARRIVE 0.15 unchanged).
  - The doorway is unaffected: the lead-in sits behind Stand, on the side the short walk starts from.
  - Bus side settle -12.6 deg (was -19.2); bus short 7.5; arrival 0.12 / 0.22 studs.

Results:
- skipcheck: ok.
- approachcheck: fence 6 of 6 OK; bus short OK; bus side OK; bus on the mark OK at 10 deg and at 35 deg.
- sneakcheck:
  - skipfence OK.
  - sneak OK once at real-time frames (17 ms).
  - Two later sneak runs came after Studio fell back to 67 ms frames (unfocused). They passed every row except "the dip's root jump
    happens under black on both frames" (veil 0.32 / 0.36), the known frame-rate artifact. This round didn't touch the dip; it
    passed at 17 ms in rounds 1-2 and in this round's first run.
- camcheck: TutorialSneak OK and TutorialBus OK, both at 67 ms frames.
- buscheck: BUS OK (TheBus2 at 17.08 s).

Slot 2: restored from this round's fresh snapshot. CineState {Collected=Seen} before and after, Origin `{}` before and after; the final
snapshot comparison shows no differences.

## Open rows

- OWNER: sign-off. Watch both cuts at full speed and record your words here.
- OWNER: two players (steps above).
- OWNER: phone-size row in the device emulator (subtitles >= 20 px, the skip a large target).
- OWNER: the fence vault: the top-of-climb pose after the dip, FenceLand, APPROACH_YAW, DIP_AT.
- OWNER: bus boarding with the known door clipping (21-stud bus accepted); the door and driver camera marks.
- OWNER: Fence and Garden camera marks (first guesses), the new Fence push-in, the bus's static shots (the 9.6 s run includes the deliberate held title), and the 6 s still in the Hide beat (fail path).
- Done 2026-11-23: both cuts recorded and motion_audit run (see "Recordings" below).
- OWNER: Task 14: the fence approach (crouch-walk up, the square-up turn, FenceOver1 fading in), the bus walk to Stand,
  the 40-degree vault heading, VAULT_BACK 0.6; watch the bus glide-in for a hitch.
- OWNER: Task 14 fix round 1, watch at full speed:
  - the fence stop and the 0.3 s blend from the planted stop pose into FenceOver2. FenceOver2's own first frames are baked
    crouch-walk frames in place;
  - the corner turn on the way to the vault, which slows to about 66 % (TurnPace);
  - the bus walk starting 0.25 s after the glide.
- DEFERRED (review ruling): M3, M6, M7, M9, M10.
- Done in fix round 1 (Studio at full rate): the sneakcheck sneak and fail dip rows, bodycheck, dipcheck.
- OWNER: Task 14 fix round 2, the exit-phase branch.
  - FenceOver2 started while still walking and the root stopped on it; this only ran when forced by a probe (2 of 2).
  - Clearance 0.20, settle about 14 deg, no jumps.
  - In production it fires only when the walk's exit phase lands 0.5-0.25 studs from the stop. Every other time it's the 0.3 s cover
    blend from the planted stop.
  - Watch either one at full speed.
- Resolved in fix round 3: the torso-faces-fence margin (now 7.5-9.2 deg against 15) and the flaky fence SEAM SPEED row (6 of 6).
- Done 2026-11-23: sneakcheck sneak at real-time frames (881 frames in 11.2 s) on the main build: SNEAK OK, the dip root jump (6.78 studs)
  under a black veil on both frames (worst transparency 0.01).
- Sign-off: pending.

## Regression after the strafes install (2026-11-23, NH Combat Test, slot 2)

The strafes build (phase6-strafes 73fa065) was installed when skipcheck reported "controls still on mid-cut" / "HUD still on".

- **Root cause: harness, not game code.** skipcheck replays `__SeamlessTest`; the server refuses a replay of an unseen cut, so no
  cut played and every row read the idle state. The strafes session started its round without marking `__SeamlessTest` Seen.
  Reproduced: unmarked fails, marked passes. skipcheck now refuses with a precondition message instead of reporting false fails, and
  `harness/round_start.sh` marks it.
- **approachcheck "couldn't run"**: the Wickfield sets stream in only near them. `harness/stream_set.lua` (run by `harness/run_cut.sh`
  with SET=Garden|BusStop) puts the player on the set's start mark first, and approachcheck says so when a set is missing.
- **Cadence:** the strafes build gives the game's walk cycles a stride-matched rate (Config.Locomotion / Functions.Locomotion.Rate).
  approachcheck's CADENCE row follows that rule when Config.Locomotion exists. TutorialSneak's FenceOver1 `Pace` (the CrouchWalk clip
  baked into the chain) uses the same rule, so one clip has one cadence. Before (old Pace, /7): fence CADENCE 2 of 268 out, worst 60 %.
  After: 0 of 261 and 0 of 265, worst 12 %.

Results on the strafes build (round 1 at 50-67 ms frames, unfocused; round 2 at 17 ms):
| Check | Result |
|---|---|
| skipcheck (marked) | ok (same rows as round 3) |
| camcheck `__SeamlessTest` / TutorialSneak / TutorialBus | CAM OK, all three |
| approachcheck bus | APPROACH OK (cadence 0 of 5 out; lead 0.27 s) |
| approachcheck fence, new Pace (x2, 17 ms) | APPROACH OK: seam speed 86 % / 90 %, settle -10.4 / -10.1 deg, clearance 0.18 / 0.19 |
| sneakcheck | SNEAK OK at 17 ms. At 50 ms frames the dip-veil row failed (worst 0.36 / 0.40): a frame landing in the fade, as in round 3 |
| buscheck | BUS OK at 17 ms. At 67 ms the base-loop row failed (240 / 48 frames), as in the earlier unfocused rounds |
| bodycheck | BODY OK |
| dipcheck (last) | DIP OK |

Slot 2: fresh snapshot each round (yen 97), restored after each; marks cleared; TutorialLeave; Play stopped; nothing saved.

## Recordings and motion_audit (2026-11-23, main build, fresh Play, slot 2)

Clips (not committed, 17 MB each): `E:/NH-Work/tutorial-clips/TutorialSneak.mp4`, `TutorialBus.mp4` (arrival, to 14.6 s into the cut: the
capture stops at 30 s) and `TutorialBus_part2.mp4` (from about 13 s into the cut: boarding, pull-away, the held title). Audits in `audit_*` next to them.
Checks run during the recordings: sneakcheck SNEAK OK (every row); buscheck BUS OK twice (settled at 6.80 s, TheBus2 at 16.86 s, hidden
from 20.53 s, hold at 30.17 s with 0 drift, doorway dX 0.06, wheels 0.06 studs off the road).

| Cut (window) | moving | still stretches over 1 s | dup frames in motion | notes |
|---|---|---|---|---|
| `TutorialSneak` (11.4 s) | 56 % | one 3.1 s, from about 7.2 s into the cut (the landing on FenceLand into the fade out) | 14 % | pan p90 533 px/s and zoom p90 140 %/s at the glide in and the vault |
| `TutorialBus` 0-14.6 s | 26 % | 1.0 s, 2.3 s and 3.8 s on the parked bus (arrival, the wait) | 5 % | the arrival settles at 6.8 s |
| `TutorialBus` 13-33 s | 16 % | 2.0 s at the doors, then 13.1 s: the bus pulling away in the dark plus the deliberate held title | 5 % | the pull-away is lights receding in near-black, so it reads as still |

Findings for the owner's watch:
- slot 2's character wears a large red magic-circle back accessory. In the over-the-shoulder shots (the Garden walk, the boarding) it
  covers part of the frame. The cuts don't hide back accessories.
- The bus scene is very dark from the boarding onward; the pull-away reads as two receding lights.
- The 3.1 s still at the end of the vault: the engine camera has a slow drift there (camcheck), but at pixel level it reads as a hold.

