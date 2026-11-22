# The tutorial's animation chains: build, check and publish

The tutorial's character animation (doc 15, §5), built from the **RoMixamo** plugin's offline library and the house
style (`r6-animation-cinematics`). Every clip is on the regular, non-bending R6 rig. The chains are made so that
moving from one animation to the next never pops.

## What is here

| File | What |
|---|---|
| `chains.json` | The clips (RoMixamo catalog entries) and the 12 chains, beat by beat. Edit this to change the run. |
| `build.py` | Converts, bakes the blends, writes `out/`, `REPORT.md` and the check harness. |
| `mixamo_r6.py` | RoMixamo clip -> R6 KeyframeSequence. It ports the plugin's own `Convert2R6` and matches the plugin's output to 3 decimals (checked against `Shoved Reaction With Spin_R6` in the FIER ANIMATIONS place). |
| `rbxm_peek.py`, `rbxm_rig.py`, `rigs.json` | Read-only readers for the plugin's `.rbxm`: the clip data, and the template rigs' joint offsets. |
| `mixamo_catalog.json` | The plugin's catalog: 2,446 clips with names and descriptions. Search it for new picks. |
| `game/`, `extract_game.py`, `extract_game.luau` | 30 fps samples of the game's own `Crouch` and `CrouchWalk` clips. The chains that sneak start and end on them. `extract_game.py` regenerates `game/*.json` from Studio. |
| `chaincheck.luau` | Plays every chain on a temporary R6 dummy in Studio and measures every handoff. |
| `test_build.py` | The offline tests for `build.py` (no RoMixamo or Studio needed). |
| `out/` | One KeyframeSequence builder per piece and per `<Piece>_End` pose, plus `TutorialAnim.luau` (the plan and a small player for the Cine). |
| `REPORT.md`, `review/chaincheck_result.txt` | How each handoff was made, and what Studio measured. |

## How the chains stay smooth

1. **Pieces:** a chain is cut into pieces at its loops.
   - Each run of one-shots between loops is baked into ONE clip.
   - Each loop is its own clip.
   - All blending happens offline. At runtime the Cine only switches pieces at frames where the poses are identical,
     with no fade (a fade would start from the rig's default pose).
2. **Cut points:** each handoff is cut where pose AND motion agree best, checked 3 frames either side.
3. **Re-seat:** B's heading and ground position are baked into its torso, so the actor's root never moves during a
   blend.
4. **Velocity carries through:**
   - The blend continues A past the cut and pre-rolls B before it.
   - Far-apart poses get a staged blend (torso first, then legs, then arms, head last).
5. **Window length:** each window is the shortest one that adds no motion the two source clips don't already have
   (at most 15 % over them). Into a near-still idle, it settles under 45 st/s².
6. **Ends:**
   - The last one-shot of a chain ends at rest: its motion dies out over 10 frames, then 2 identical frames hold.
   - Each piece also has a `<Piece>_End` clip: its final pose, still.
   - `CineActor.Reseat` moves the root by the piece's `EndOffset` and switches to `_End` in the same step, so nothing
     visibly moves. Spec delta 2 has the reasons.
7. **Loops:**
   - Seams carry pose and velocity.
   - A loop is entered and left on fixed phases.
   - The player carries a switch's sub-frame offset into the next piece.
   - It leaves a one-shot within its last tick, so the one-shot never stalls on its final frame.

**Measured (Studio, 60 fps):**
- All 30 baked blends are within 1.18x of their own source clips' peak acceleration, or settle under 45 st/s².
- 19 of the 21 runtime switches peak below the chains' own p99.
- Sneaking is the game's own crouch now. The Mixamo `SneakLoop` is gone, so those two switches are gone with it.
- The newest Studio run (after the game-crouch change) measured 21 runtime switches, all at or under their chains' p99.
  The output is in `review/chaincheck_result.txt`.

## Build and check (Studio open on NH Combat Test, Edit mode)

```sh
cd tools/tutorial-anim
python -I -X utf8 test_build.py                 # offline tests, no Studio needed
python -I -X utf8 build.py                      # reads %LOCALAPPDATA%\Roblox\Plugins\RoMixamo.rbxm
RBXC="python -X utf8 -I E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py luau 'placeId: 98950102230473' Edit"
for f in out/*.lua; do $RBXC @$f; done           # -> ReplicatedStorage.NHCineClips.Tutorial
$RBXC @out/_chaincheck.luau                      # measures every handoff
```

- Each builder registers its clip and stores the result as the sequence's `PreviewId` attribute.
- In Studio, the Cine plays a clip from that preview id until a published id is set.
- The clips are in `ReplicatedStorage`, not `ServerStorage`, because the client plays them.

A freshly registered clip takes a moment to load, so the check waits for each track. A chain reported as NOT MEASURED
means the dummy never moved. Run the check again.

## Publish (owner)

1. In NH Combat Test, publish each KeyframeSequence in `ReplicatedStorage.NHCineClips.Tutorial` to the group.
   That is 33 pieces and their 33 `_End` poses, 66 in all.
2. Paste each asset id into `Config.CineClips`, under the piece's name, for example `TheBus1_WaitBored = "rbxassetid://<id>";`.
   - The director's `Ctx.Clip` reads a published id from there first.
   - An empty or missing entry falls back to the Studio preview id, which only works in Studio.
3. `TutorialAnim` (`ReplicatedStorage.Config.TutorialAnim`) holds the plan and the player. It has no id table.

The Cine calls:

```lua
TutorialAnim.Play(animator, "TheBus", Ctx.Clip, { [1] = waitForBusCue }, onSwitch, isCancelled)
```

- `Ctx.Clip` is the `resolve` argument: piece name to animation id.
- `cues[k]` yields until the loop at step k may end.
- `onSwitch` is called as each piece starts.
- `isCancelled` is checked in every wait. Once it returns true, `Play` stops its tracks and returns (the Skip path).
- A piece with `Hold` freezes on its last frame (the cold open's freeze-frame).
- The last one-shot of a chain also holds its final frame until `CineActor.Reseat` or `Release` stops it.

## Status

- `Controllers.Cine` and `Controllers.CineActor` call `TutorialAnim.Play` (2.35.0). `TutorialSneak` and `TutorialBus` use it.
- The other chains are built and checked but have no cut yet.
- The foot-lock bake (`tools/phase3-2260/anim/footlock.luau`) has not been run on these pieces. Mixamo -> R6 keeps the
  knees' height but not their bend, so a planted foot can slide slightly in the walking pieces.
