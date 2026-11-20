# Tutorial seamless cinematics: design

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
