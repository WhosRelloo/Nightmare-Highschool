# Tutorial seamless cinematics: design

**Status:** slice 1 shipped in 2.35.0 (plan: docs/superpowers/plans/2026-11-20-tutorial-seamless-cinematics-slice1.md).
**Date:** 2026-11-20
**Place:** NH Combat Test (98950102230473), `Workspace.Hometown` (Wickfield). The Map place is not touched.
**Builds on:**
- doc 04 (the Cine framework);
- doc 12 (interactive cutscenes: segment graphs and prompts);
- doc 15 (the tutorial run);
- `tools/tutorial-anim` (the R6 animation chains: `TutorialAnim`, pieces that switch on identical frames).

**Owner's answers:**
- **"Play like GTA 6's":** seamless handoffs, walk-and-talk scenes, and a film-like camera look. The in-world
  cinematic camera toggle is not wanted for now.
- **Other tutorial players:** hidden. Each player gets a private Wickfield.
- **Approach:** A, extend the existing Cine. No separate tutorial director, and no camera rails in place of cutscenes.

## Goal

You can't see the seam between playing and watching:
- The camera glides from your live view into the scene and lands back behind your shoulder.
- Your own character is the actor.
- You come out of a scene already moving.
- Quieter beats never take control away: the camera, lines and other characters are scripted around you while you
  walk.

Every handoff is measured, not judged by eye: no frame of the camera or the body may move harder than the motion around
it.

## 1. Architecture

Everything extends the existing Cine. Nothing is duplicated.

| Piece | Change |
|---|---|
| Cut modules (`ReplicatedStorage.Cinematics.<Id>`) | A cut may set `seamless = true`. A segment may be `shots` (as now) or a `beat` (§3). |
| Director (`Controllers.Cine`) | A **seamless path** next to the clone path: your real character is the actor, the camera glides in and out, and the HUD fades. The clone path stays for multi-viewer story cuts (doc 04 §5). |
| Actor driver (new: `Controllers.Cine.Actor`) | Walks or turns the real character onto its mark in-world, plays `TutorialAnim` chains, re-seats the root at the end of a chain and hands control back mid-stride. |
| Beat runner (new: `Controllers.Cine.Beat`) | Walk-and-talk: the camera rigs, lines and cues around a player who keeps moving (§3). |
| Look (in `ReplicatedStorage.Cine`, the shot library) | The film look (§4.1), so every cut gets it. |
| Privacy (new: `Controllers.Hometown`) | Hides other tutorial players and runs the client-side cast (§4.2). |
| Server (`Services.World.Cine`) | Same shape: who sees what, "seen", timeouts, skip, prompt judging. It adds checkpoints (§4.3). |

**Source of truth:** the build starts from the live scripts in NH Combat Test. The repo's copies under `tools/phase*/`
date from 2.26 and may be behind.

## 2. Seamless handoffs

### 2.1 In
- **Marks:**
  - A cut starts from where the player is.
  - If a shot needs the actor on a mark within 4 studs, the Actor driver walks or turns them there. It uses the game's
    own walk clip at its measured pace (as `Controllers.Cine` does for actors today).
  - If the mark is further away, the cut's marks are authored relative to the player's current CFrame.
  - Never a teleport, except Skip (§2.3).
- **Input:** movement input eases to zero over 0.3 s; the humanoid decelerates naturally.
- **Camera:**
  - It glides from the live camera's CFrame and FOV into shot 1 over 0.6-1.0 s (longer for a bigger change), along a
    curved path with an ease-in-out. It never cuts on entry.
  - Shot 1 of every seamless cut is staged near a gameplay angle, so the glide stays short.
  - `Cine.analyze` flags a shot 1 that needs more than 90° of turn or 12 studs of travel.
- **Screen:**
  - The HUD fades out over 0.4 s. There are no letterbox bars on seamless cuts; the grade and DOF carry the "cinema".
  - Bars stay only for the cold open's freeze-frame title card.
- **Body:** the real character plays `TutorialAnim` pieces at Action priority over its normal Animate, through
  `TutorialAnim.Play`. Pieces switch instantly on identical frames, carrying the sub-frame offset.

### 2.2 Out
- **The last piece** ends in the pose of the next gameplay state: a walk stride, a crouch or standing.
- **The re-seat:** on that frame the Actor driver moves the HumanoidRootPart under where the body ended (heading and
  ground position) and zeroes the torso offset in the same frame, so nothing visibly moves. `tools/tutorial-anim/build.py` adds
  `EndOffset = { X, Z, Yaw }` to every piece for this.
- **Blending back:** the game's idle or walk then blends back in over 0.25 s.
- **The camera's last shot** lands exactly where the Custom camera will be: behind the shoulder, at the player's zoom
  and FOV. When the lease is released, the Custom camera takes over from that exact CFrame. The camera seam check
  (§5) proves zero jump.
- **Control** returns when the exit glide starts, not after it. A direction already held carries straight on.

### 2.3 Skip
- **Hold-to-skip** jumps to the cut's end state.
- That jump is the one place a fade is allowed: a 0.25 s dip to black, during which the actor is placed at the end
  mark and the camera at its gameplay position.

## 3. Walk-and-talk beats

A segment can be a `beat` instead of `shots`:

```lua
Garden = { beat = {
    rig = "Follow",                       -- "Follow" | "Lead" | "Side" | "Frame"
    frame = { also = "Biscuit", lens = 35, low = true },
    move = { speed = 0.7, sprint = false, crouch = true },
    lines = { { on = "start", who = "You", text = "Okay. Quiet. Very quiet." } },
    cues  = { { on = "near:Biscuit:8", run = "BiscuitWakes" } },
    prompt = nil,                         -- an optional doc 12 prompt (Press, Mash, ...), judged by the server as now
    ends  = { on = "enter:FenceZone", next = "FenceOver" },
} }
```

### Camera rigs
Each rig is a spring-damped camera around the player:

| Rig | What it does |
|---|---|
| Follow | A low shoulder camera that drifts to keep `frame.also` in shot. |
| Lead | Ahead of the player at hip height, looking back, for chases. |
| Side | A tracking dolly running parallel to the player's travel. |
| Frame | Eases toward a point of interest as the player nears it. |

- **Nudging:** the mouse or stick can push the camera about ±25°, and it springs back over 0.6 s.
- **Control mapping:** on Lead and Side, movement is mapped to the beat's travel direction, not the camera, so the
  controls never invert.

### Movement limits
- `move.speed` scales WalkSpeed. `sprint = false` blocks the sprint state, and `crouch = true` holds crouch.
- The beat's zone is closed by Wickfield's own layout; a beat never adds invisible walls.

### Lines and cues
- **Triggers:** `start`, `t:<seconds>`, `enter:<zone>`, `near:<actor>:<studs>`, `idle:<seconds>`, `prompt:<result>`.
- **Lines:** a line plays subtitles plus `FaceTalk` visemes. If the player rushes ahead, lines carry on.
- **Waiting:** a character waiting on the player plays a living idle loop (a `TutorialAnim` loop); nobody freezes.
- **Prompts:** a Press prompt inside a beat (the hedge dive) uses the doc 12 prompt and slow-mo without leaving the
  beat.

### Endings
`ends` moves straight into the next segment, a `shots` cut or another beat. The handoff between a beat and a cut
uses §2.

### The tutorial's split (doc 15 §5)

| Kind | Beats |
|---|---|
| Walk-and-talk | 2 (sneaking out past Biscuit), 3 (crossing to THE PLAN), 6 (the getaway), 9 (breakfast) |
| Full cinematic, seamless in and out | 1 (cold open), 4 (each prank's climax), 5 (the slip), 7 (home, the parents in the dark), 8 (the excuses), 10 (the bus) |

## 4. Look, privacy and safety

### 4.1 The film look (`ReplicatedStorage.Cine`)
- **Lenses:** shots give a focal length in mm (19-85). Vertical FOV = 2·atan(24 / 2f), as on a full-frame sensor.
- **Handheld:** two layered noise octaves (0.4 and 1.1 Hz) on rotation, plus 0.02 stud of drift on position.
  - Amplitude by shot `feel`: `calm` 0.08°, `tense` 0.25°, `chase` 0.6°.
  - Off under Reduce Motion or Camera Shake off.
- **Focus:**
  - The `DepthOfFieldEffect` focus distance follows the subject's head (a raycast from the camera), with a 0.3 s
    eased pull whenever the subject changes.
  - The in-focus radius shrinks with focal length.
- **Grade:** per-scene presets of a `ColorCorrectionEffect` plus `BloomEffect`. They ease over 1 s when the player
  crosses between interior and exterior.

  | Preset | Look |
  |---|---|
  | `Night` | Teal shadows, sodium highlights. |
  | `Morning` | Warm. |
  | `BusStop` | Cold and desaturated; the bus's lamps glow. |

  A vignette and film grain are added only if the UI kit already has the art. No new uploads are needed.
- **HUD:** it fades out and back in over 0.4 s, through `CineUI`.

### 4.2 Private Wickfield (`Controllers.Hometown`)
- **Who counts:** the Tutorial service sets the attribute `NHTutorial` on a player while they're in Wickfield.
- **Hiding:** while the local player has `NHTutorial`, every other player with it is hidden on this client:
  - `LocalTransparencyModifier` = 1 on their parts and decals;
  - their name tag off;
  - their character's sounds muted.
- **Collisions:** the server puts tutorial characters in a `TutorialPlayers` collision group that doesn't collide
  with itself.
- **The cast:** Biscuit, the goose, Mom, Dad, the watchman and the bus driver are spawned on the client, per player.
  NPC states (asleep, awake, at the table) are private.
- **The server** still owns progress and judges prompts.

### 4.3 Safety
- **Checkpoints:**
  - Every beat and cut start writes `Progress.Origin.Checkpoint` (the segment id) on the server. `Progression.Sanitize`
    keeps it.
  - Death, respawn or a rejoin puts the player at that checkpoint's mark, with the camera already behind them.
- **Timeouts:** the server's cut timeout (length + 5 s) stays. A beat has no timeout because the player drives it,
  but leaving Wickfield ends the tutorial session.
- **Reduce Motion:** glides become 0.2 s dissolves, with no handheld noise and no Dutch roll. Prompt windows widen as
  in doc 12.

## 5. Testing and acceptance

### First slice
Both halves are proved before the rest:
1. **The Bus (beat 10):**
   - free-roam at the stop;
   - a seamless glide into the arrival (BrakeStop, DoorsOpen, DriverTurn);
   - `TheBus` animation chain;
   - boarding;
   - the freeze on the title card.
2. **Sneaking out past Biscuit (beat 2):** the first beat, with the Follow rig, Biscuit's cue and the soft fail
   (the bedroom light flicks on, you crouch and wait).

The rest of the run follows, beat by beat, in doc 15's order.

### Measured checks
- **Camera seam check** (new: `tools/tutorial-anim/camcheck.luau`):
  - It records the camera CFrame and FOV every frame through each glide in and out.
  - It passes if no frame's angular or linear acceleration exceeds 1.5x the glide's own median, and if the first
    frame after the lease is released matches the last frame under it (position to 0.01 stud, angle to 0.1°).
- **Body seam check:** `chaincheck.luau` adapted to the real character, measuring every piece switch and the root
  re-seat. A switch passes at or under the chain's own p99, as now.
- **Lint:** `Cine.analyze` shows no `[fix]`, including the §2.1 shot-1 check.

### Playtests
- Solo.
- Two players in Wickfield at once: each sees only themself and their own cast, with no collisions.
- Death mid-beat, and a rejoin: both resume at the checkpoint.
- Reduce Motion.
- Phone size and 1080p.

### House style
- `motion_audit.py` on captures of each slice.
- The owner watches it at full speed and signs off.

## 6. Out of scope
- An in-world cinematic camera the player toggles during gameplay.
- Converting the existing story cuts (Prologue, COLLECTED, the Strikethrough) to the seamless path. They can opt in
  later with `seamless = true`.
- The Map place.

## Spec deltas

These are the choices the build made while implementing slice 1 (2.35.0).
Where one differs from the text above, the delta wins.
Each ends with its reason.

1. **The clips' folder.**
   - Tutorial pieces live in `ReplicatedStorage.NHCineClips.Tutorial`, not `ServerStorage.NHTutorialAnims`.
   - The client resolves clips with the director's `Ctx.Clip`: a published id in `Config.CineClips`, else a preview id
     registered from the KeyframeSequence.
   - Reason: `ServerStorage` isn't visible to the client.
2. **The re-seat (amended: the settle is in the last piece).**
   - The last one-shot piece of every chain ends at rest.
     `build.py` appends 10 frames of its own motion dying out (0.82 per frame), then a 2-frame hold.
   - Each piece also gets a `<Piece>_End` clip: its final settled pose, with the torso's ground offset and heading
     taken out. It carries two identical keyframes, because one keyframe gives a track no length.
   - `Play` plays the last piece to its end and holds it.
   - The re-seat moves the root by `EndOffset` and switches to `_End` in the same engine step.
   - `EndOffset` is scaled by the character's scale. The first build forgot this and stepped 0.04 stud at a scale of 1.03.
   - `_End` then fades out over 0.25 s into the game's idle or walk.
   - Chains that end on a loop don't re-seat. They hand back through `Release`, because the game's own crouch is the
     same pose.
   - Reason: switching one still pose to an identical still pose has no velocity to step, so frame-level timing
     slack can't show.
     An `_End` that only froze the last frame stopped moving limbs dead, which showed as a 3 cm arm step.
3. **The glide out.**
   - It's a blend layer on the live Custom camera, not a scripted path to a computed target. Two RenderStep binds:
     - before the camera module, the layer puts back the Custom camera's own last CFrame, so the module never reads
       the blend;
     - after it, the layer saves that CFrame and writes the blend.
   - Reason: the endpoint is whatever the Custom camera renders, so the release can't jump.
4. **Glide-in tracking, and Reduce Motion.**
   - The glide in re-evaluates shot 1's first frame every frame, so a walking player doesn't jump at the end of the glide.
   - Grade and DOF scale with the glide's ease on entry and ease back over the blend-out. Handheld noise ramps in over
     shot 1's first 0.3 s.
   - Under Reduce Motion, both glides become a 0.2 s fade through black: the camera cuts while the screen is black.
   - Reason: Roblox can't cross-dissolve two cameras, and the first build popped the grade, DOF and handheld.
5. **Movement on Lead and Side rigs.**
   - The beat swaps the PlayerModule ControlModule's `moveFunction`, so the stick is read against the beat's travel
     direction.
   - Travel is the authored `frame.travel` mark, else the heading to the `ends` enter-zone mark, else the player's facing.
   - Reason: controls must never invert when the camera runs alongside or ahead.
6. **The crouch is the game's own** (owner, 2026-11-20).
   - Playable sneaking uses `Assets.Animations.Default.Movement.Crouch` and `CrouchWalk`, which the
     AnimationController plays while `Services.Player.Crouch` holds crouch.
     A beat holds it through the server (the `BeatCrouch` message).
   - The chains are built from 30 fps samples of those clips (`tools/tutorial-anim/game/`), so a cinematic piece
     starts and ends on the game's exact crouch pose. That replaces the Mixamo `SneakLoop`.
   - `Tutorial.Leave` stands the player if a beat left them crouched.
   - Reason: a second crouch look would pop at every handoff.
7. **The bus and the Wick house are rigid rigs.**
   - They're plain meshes joined by Motor6Ds, built in Studio by `tools/phase6-2350/stage/bus_rig.py` (with
     `bus_rig.lua`) and `stage/rigid_rig.py` (with `rigid_rig_WickHouse.lua`) from `art/props/anim/WFBlackBus_rigid.json`
     and `WickHouse_rigid.json`. The clips are KeyframeSequences generated from the same JSON.
   - Biscuit and the garden gate stay skinned.
   - Reason: Studio's skinned import laid the bus and the house out wrong (wheels, hood and windows displaced). The cause
     of the bad bone rests was never found. Biscuit's import is fine.
8. **Rigs keep a base loop on whenever they're visible.**
   - The bus plays `EngineIdle` from the moment its cast copy exists. Biscuit plays `Sleep`; `Hometown` casts him as
     soon as `NHTutorial` is set.
   - Other clips play over the base loop.
   - Reason: a rig is never drawn bare, and the scene is never dead (an idling engine, a sleeping dog).
9. **Seamless cuts reject `Def.Actors` and `Def.Clock`.**
   - The director warns and ignores them.
   - Reason: the per-player cast belongs to `Hometown`, and a clock restored after the blend pops in view.
10. **A held title is tutorial-only.**
    - `Def.EndHold` (the bus's freeze on the title card) applies only while the player has `NHTutorial`, and never on a
      replay.
    - A safety release dips and ends the cut if no next `Play` arrives within 10 s.
    - Outside Wickfield the cut doesn't move or animate the shared bus.
    - Reason: otherwise a replay, or a run with no Prologue behind it, would strand on the held frame.
11. **`Replay = false` for `TutorialSneak` and `TutorialBus`.**
    - Reason: a journal replay outside Wickfield would walk the real character on Wickfield-framed shots, and a beat
      suspends the server timeout, so it would never end.
      Seamless replay staging still needs a design.
12. **The fence vault lands on `FenceLand`.**
    - The vault is an in-place clip (1.66 studs, mostly sideways). The root is moved to the `FenceLand` mark, 2.15
      studs past the far face, under a 0.3 s dip at the top of the climb.
    - A Skip or a Timeout before that point uses `Ctx.OnBlack` to place the player on `FenceLand` under the skip's own dip.
    - Reason: the clip's travel can't clear the fence. A skip must not strand the player on the house side.
13. **`CineUI`'s `Dip` and `Veil` use a generation token.**
    - Every `Veil` bumps a counter. A dip lifts its veil only if no newer veil or dip claimed the screen, and a claimed
      dip holds black.
    - Reason: overlapping dips (a skip inside the fence dip) lifted each other's black early.
14. **Replays write no checkpoints.**
    - `Cine.Play` and `OnSeg` skip the write when the run is a replay.
    - Reason: a replay would overwrite the tutorial's real resume point.
15. **`Tutorial.Resume` resumes at the checkpoint's mark.**
    - It runs on `Tutorial.Enter` and on every respawn in Wickfield. It puts the player on a mark of the cut's set, 3
      studs up.
    - Each cut declares its own map in `Config.Cine`: `Resume = { Marks = { <segment> = <mark> }, End = <mark> }`.
      - `TutorialSneak`: Start, Garden and Hide map to `Start`; Fence maps to `FenceZone`; `End` is `FenceLand`.
      - `TutorialBus`: Start and Main map to `Stand`; `End` is `Stand`.
    - A cut that is finished (Seen) resumes at its `End` mark, never at a mid-cut mark.
    - A checkpoint whose cut has no map, an unmapped segment or a missing mark warns and leaves the player where the game
      put them.
    - Slice 1 has no production caller of `Tutorial.Enter` yet. The TestBridge drives it.
    - Reason: guessing marks by name stranded a player behind what they had already done.
16. **Leaving Wickfield ends any cine session.**
    - `Tutorial.Leave` ends a running cut with `How = "Aborted"`. A disconnect ends it with `How = "Left"`.
    - Neither marks the cut Seen, so a returning player sees it again.
    - `OnFinish` still fires; handlers must treat `Left` and `Aborted` as not completed.
    - Reason: a cut must not outlive Wickfield, and a leaver shouldn't lose a scene they never watched.
17. **A graded cut holds only the exposure.**
    - `DayCycle.HoldExposure(name, on)` pauses the exposure write. The rest of the day grade runs on.
    - Reason: holding the whole cycle snapped the night grade off as a glide began.
18. **Wickfield's staging tools** are in `tools/phase6-2350/stage/`:
    - `hometown.lua`: fits and places the imported models, and writes the marks and sets;
    - `textures.lua`: applies the SurfaceAppearances;
    - `bus_rig.py` and `rigid_rig.py`: build the rigid rigs and their clips (delta 7).
    - Re-run them after any re-import. `hometown.lua` skips a rigid rig so it isn't re-fitted.
19. **The Dip token tracks what the screen wants.**
    - `CineUI.Veil` records `VeilTarget` as well as bumping its generation.
    - A dip forces black at its midpoint only if the latest claim still wants black.
      It lifts unless a newer black claim is pending (`VeilGen == Mine or VeilTarget == 0`).
    - Reduce Motion's delayed `Veil(0, 0.1)` in the beat entry is guarded with `Cut.Live`.
    - Reason: the first token (delta 13) could leave the screen black for good when the newer claim was a lift or a
      shorter dip that had already lifted.
20. **Framed shots have a level horizon.**
    - `Seam.Rot` slerps the look on its great circle and eases the ends' own rolls. `Seam.Blend` and the glide use it.
    - `Cine.framedCFrame` turns the screen-placement yaw about world up, so the horizon stays level before any authored roll.
    - An authored `roll` (a Dutch angle) is kept.
    - `Cine.framedCFrame` is the shared toolkit, so every framed shot in the game now has a level horizon.
      The Strikethrough, Collected and RollCall cuts were re-checked.
    - Reason: the slerp between two level cameras tilted the horizon in between (up to -1.8 deg), and the old placement
      yaw tilted framed shots (up to -1.6 deg). House style wants roll 0 on ground beats.
21. **Placed animations start with an on-foot approach (`CineActor.Approach`), owner request 2026-11-21.**
    - When an animation needs the character at a mark (the fence, the bus door), the character gets there on foot and flows
      straight into it. Nothing is lerped, slid or teleported on screen; a root move is allowed only under full black.
    - `Approach(Mark, { Gait, LeadIn, Arrive, BlendLead, OnNear })` drives the Humanoid at the gait's speed (Walk = the player's
      walk speed, Run = 25, Crouch/Sneak = 7), so the game's own Walk, Sprint and CrouchWalk tracks play. No new animations.
    - It arrives facing the mark: it walks to a lead-in point `LeadIn` studs behind the mark along its facing (skipped when
      already within 30 degrees of the mark's heading and in line), then straight onto the mark. The few degrees left at the
      stop turn over the next 0.45 s or more (45 degrees a second at most), inside the next piece's fade-in.
    - `OnNear` fires `BlendLead` (0.2 s) before arrival; the cut starts the chain there. `CineActor.Chain` takes
      `Opts.FadeIn` for the first piece only (pieces 2+ still switch instantly) and `Opts.Entry` (the phase a first loop
      enters at, so the loop's exit can be timed to a shot). `CineActor.Preload` fetches every piece and `_End` pose.
      `Controllers.Hometown` preloads FenceOver and TheBus when NHTutorial is set.
    - Steering is `Humanoid:Move` toward the waypoint every frame. `MoveTo` was tried first: it stops about a stud short of its
      point and times out after 8 s.
    - Fallback: a walk that is blocked (no progress for 3 s), times out or falls ends with `CineActor.Fallback`: a `CineUI.Dip`
      and a placement, with a warning.
    - Events marked `noShift` run on the segment's own clock, so the approach starts as the beat ends, through the glide in.
      `Ctx.Clock()` and `Ctx.Glide()` expose the clock; `Ctx.HoldEnd(fn)` holds a segment's end (3 s at most) while `fn()` is true,
      so a re-seat still waiting for its clip never lands under the blend out.
    - The fence: the vault mark is FenceZone turned 40 degrees left (FenceOver2's first frame faces 40 degrees right of its root)
      and 0.6 studs back from the fence, measured so the body clears the gate during FenceOver1. The Garden beat ends 3.5 studs
      from FenceZone (`enter:FenceZone:3.5`), so it never ends with you against the gate.
    - The bus: `Approach(Stand, Walk)` from wherever you stand; the waiting loop enters at the phase that puts its exit on the
      "You step on" shot, whenever you arrive.
    - Other spots where the root is placed, audited: the fence dip and `Ctx.OnBlack` placements (under black), the chain re-seat
      (a pose-to-identical-pose switch), `Tutorial.Resume` (on entering or respawning, not during a cut), the non-seamless cut's
      `Arrive` (before the cut). None is on screen.
22. **A cut with beats lists them in `Config.Cine Cuts[Id].Beats`.**
    - Each walk-and-talk beat segment must be listed (`Beats = { Garden = true; Hide = true }`). The server holds the timeout only
      while a listed beat runs, so an unlisted beat is timed out mid-beat (Length + TimeoutPad) and the cut ends under the player.
