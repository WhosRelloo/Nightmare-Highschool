# 04. Cinematic Framework Specification

## 1. What exists (reuse, don't duplicate)

| Piece | Where | Reuse as |
|---|---|---|
| Camera ownership | `ReplicatedStorage.Functions.CameraLease` (Still/Resume callbacks, released on respawn) | The only way a cut takes the camera |
| Spline shots | MainMenu (`Config.MainMenu.Paths`, Catmull-Rom over MenuShot parts, damped follow) | Path moves |
| Server/client cutscene handshake | `NHEvolve.Play` / `Done`, 16 s timeout, skip once seen (`Lineage.Seen`) | Template for `Cine` sync and recovery |
| Talk shot | `Gui.Dialogue` (over-shoulder, FOV −12, letterbox, DOF, drift) | Dialogue staging. It must be moved onto `CameraLease` first. |
| Banners | `Gui.Moments` | Chapter cards, quest beats |
| Audio | AmbienceMix "cutscene fade" | Ducks the world under a cut |
| Settings | Reduce Motion, Camera Shake | Respected by every shot |
| Faces | `Character.FaceTalk` (visemes, 6 expressions; `NHSay`) | Speaking characters |
| Toolkit | The `roblox-cinematic-animation` skill's `Cine.lua` (shot list player: sizes, lenses, moves, DOF, grade, cards, events, hitstop, `Cine.analyze`) and `Capture.lua` | The Director's core, adapted to this game |

## 2. Components (new only where needed)

| Component | Responsibility |
|---|---|
| **Cine Director** (client, `Controllers.Cine`) | Plays a shot list. It takes `CameraLease`, frames by shot size, sets the lens in mm, and runs moves (dolly, track, orbit, push-in, dolly zoom), handheld noise, Dutch roll, DOF, grade, letterbox and title cards, then releases the lease. |
| **Scene Timeline** | Data per cut (`ReplicatedStorage.Cinematics.<Id>`): shots, durations, and events at times (anim, VFX, sound, line, fade). Authored in Lua tables and linted with `Cine.analyze`. |
| **Character Director** | Puts actors on marks (a client-side clone or the real NPC), plays clips with Animator priorities, and drives faces through `NHSay`. Players appear as **local clones**, so their real character stays where it is. |
| **VFX / Audio Director** | Events: `Fx` kinds, ambience fades, a music sting, SFX. They reuse the AmbienceMix groups. |
| **Subtitles** | One bottom-third line in the UI kit's dialogue style: speaker name and text, timed by the line. It is always on for spoken lines and kept readable at mobile scale. |
| **Cine server** (`Services.World.Cine`) | Decides who sees which cut: `Cine.Play(players, id, opts)`. It saves "seen" per slot, handles group skip votes and recovers from disconnects. It extends the `NHEvolve` Play/Done pattern into one remote, `NHCine` (Play, Done, Skip, Vote). |
| **Input lock** | During a cut, movement, combat and UI keys are locked through the existing StateManager state (as in `InActivity`). Esc / B / a tap on Skip is always allowed once the cut has been seen, or by group vote. |

## 3. Camera direction (house style: the `r6-animation-cinematics` skill)
- **The language:**
  - establishing wides (19-24 mm, still)
  - over-the-shoulder for conversations (50 mm)
  - close-ups for reveals (85 mm)
  - tracking for walks
  - a Dutch angle (±10-15°) only for wrongness
  - one dolly zoom per chapter at most (the "the bell rings" moment)
- **Pacing:** varied shot lengths, most of them static, cut on action or line, never across the 180° line.
- **Impacts:** a hard cut on the impact frame, then a slow push-in through a moving hold.
- **Reduce Motion:** moves become cuts, and there is no shake or Dutch roll.

## 4. Gameplay-to-cinematic transitions
- **In:** ease the gameplay camera into shot 1 over 0.4-0.8 s, matching the FOV. Never a pop.
- **Out:** the last shot lands behind the player's shoulder, then the lease is released and control returns with a 0.3 s input grace.
- **Mid-gameplay beats:** short "beats" (under 4 s, no letterbox) for quest moments, such as the camera glancing at a changed photograph. They don't lock movement for more than the beat.
- **Seamless cuts (2.35.0):** a cut with `Seamless = true` in `Config.Cine` glides in from the live camera, uses the real character, fades the HUD and blends out onto the Custom camera; see `docs/superpowers/specs/2026-11-20-tutorial-seamless-cinematics-design.md`.

## 5. Multiplayer behaviour
- **Personal cuts** (story beats for one student) play only for that player. Others nearby see nothing, and the player's real character stays in place, protected from damage for the cut (`Protected` state, as in duels).
- **Group cuts** (a 2-4 player case finale) play for the case's party only:
  - synchronised by server start time (`GetServerTimeNow`);
  - **skip vote:** a majority skips; anyone who has already seen the cut votes skip automatically.
- **Unrelated players** are never pulled into a cut.
- **Disconnects:**
  - **The viewer leaves:** the cut ends for them and the story step is saved before the cut starts. The beat's progress never depends on finishing the cut.
  - **On rejoin:** an unseen required cut replays once, with a skip offered.

## 6. Recovery and safety
- **Timeout:** each cut has a server timeout of its length plus 5 s, after which `Done` is forced.
- **Respawn or death:** both release the lease (CameraLease already does this).
- **Rewards:** granted by the quest step, never by the cut.

## 7. Mobile
- Letterbox bars are thin on narrow screens.
- Subtitles stay at 20 px minimum (at the kit's AutoScale).
- Skip is a large tap target.
- Cuts are tested at phone size and at 1080p.

## 8. Acceptance (each cut)
- `Cine.analyze` shows no `[fix]`.
- Captured key frames have been reviewed.
- Tested solo, as a group of 2 with a skip vote, and through a disconnect and rejoin.
- Reduce Motion works.
- The camera returns to Custom.
- No `Cine*` objects are left behind.
- You watch it in real time and approve it.

## 9. First cuts to build (in this order)
1. **Prologue roll call** (about 25 s): the gate, the bell, the extra name.
2. **COLLECTED** (Chapter 1 end, about 12 s).
3. **The changed photograph** (a Chapter 2 beat, under 4 s).
4. **The bell at 3 AM** (a crisis opener, about 15 s).

The talk shot is migrated onto the Director as its "dialogue" preset.
