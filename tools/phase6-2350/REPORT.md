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
| Death mid-beat | PASS | Killed 4 s into the Garden beat: respawned on `Start` (checkpoint `TutorialSneak:Garden`, 3994,3,4104), camera Custom and behind the player (look dot 0.83, 12.6 st). The cut is not restarted (state Started, not Seen) |
| Rejoin | PASS | Stop and Play again: Origin.Checkpoint `TutorialSneak:Fence` persisted; TutorialEnter put the player on FenceZone (4012,3,4082). Needed Tutorial.Resume (added) |
| Reduce Motion on | PASS (camera) | reducecheck OK: In/Out are 0.2 s dips (0 visible camera changes, veil peak 1.00); the code strips handheld and Dutch for Ctx.Reduced. Handheld absence not measured numerically |
| Phone | PARTIAL: OWNER | The device emulator is not driven by this harness. Static facts: CineUI.textSize floors subtitle text at 20 px; the skip button is 190 x 64 px at the bottom right with a 48 px seal |

Manual two-player steps (owner): Test > Clients and Servers > Local Server, 2 players, both Play, both reach the tutorial (TutorialEnter).
Watch: (a) each client sees only its own character, Biscuit and bus (the other player never appears, including a tool or accessory equipped later);
(b) walk into the other player's spot: no collision; (c) both start TutorialSneak at once: each has their own Biscuit and bus;
(d) reset one player: they respawn on the checkpoint mark and the other client still does not see them; (e) no `[Hometown]` errors in Output.

## Step 3: house style (no video)

`video_capture` failed with NoSpaceOnDevice (drive C: has 1.3 GB free), so there is no mp4 and no motion_audit.py run. Substitute: numbers from
the engine camera sampled every frame (camcheck's new `motion` row; "still" = under 0.003 st and 0.03 deg per frame):

| Cut | Cut frames | Still fraction | Longest still run | Horizon roll |
|---|---|---|---|---|
| `__SeamlessTest` | 1013 / 16.9 s | 66.8 % | 3.37 s | -1.40 to 0.00 deg |
| `TutorialBus` (to the hold) | 1808 / 30.2 s | 74.4 % | 9.60 s | -1.40 to 0.93 deg |
| `TutorialSneak` (sneak path) | 753 / 12.8 s | 49.5 % | 6.16 s | -1.83 to 0.00 deg |

Against skill section 3: action beats want still under 10 %, roll 0 on ground beats, holds as moving holds. All three are above it, and the sneak (a
ground beat) rolls up to 1.8 deg. These are not directly comparable to motion_audit's pixel-level still fraction (handheld noise sits under the
threshold at 15 fps frames), but they flag fixed shots (bus arrival, Fence) holding a locked camera for 6-9 s. Re-run with real clips:
`python ~/.claude/skills/r6-animation-cinematics/scripts/motion_audit.py <clip.mp4> OUT --strip <t0> <t1> 30` around the glide in, the doors and the fence.

## Open rows

- OWNER: sign-off. Watch both cuts at full speed and record your words here.
- OWNER: two players (steps above).
- OWNER: phone-size row in the device emulator (subtitles >= 20 px, the skip a large target).
- OWNER: the fence vault: the top-of-climb pose after the dip, FenceLand, APPROACH_YAW, DIP_AT.
- OWNER: bus boarding with the known door clipping (21-stud bus accepted); the door and driver camera marks.
- OWNER: Fence and Garden camera marks (first guesses); the stillness numbers above.
- OWNER: record both cuts and run motion_audit (needs disk space on C:).
- Sign-off: pending.
