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
| `chaincheck.luau` | Plays every chain on a temporary R6 dummy in Studio and measures every handoff. |
| `out/` | One KeyframeSequence builder per piece, plus `TutorialAnim.luau` (the plan and a small player for the Cine). |
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
6. **Loops:**
   - Seams carry pose and velocity.
   - A loop is entered and left on fixed phases.
   - The player carries a switch's sub-frame offset into the next piece.
   - It leaves a one-shot within its last tick, so the one-shot never stalls on its final frame.

**Measured (Studio, 60 fps):**
- All 30 baked blends are within 1.18x of their own source clips' peak acceleration, or settle under 45 st/s².
- 19 of the 21 runtime switches peak below the chains' own p99.
- The other two (`Drainpipe1 -> SneakLoop`, `HomeAgain1 -> SneakLoop`) were checked frame by frame offline. They are
  identical to the sneak loop playing on its own at that phase: their peak is the stride, not the switch.

## Build and check (Studio open on NH Combat Test, Edit mode)

```sh
cd tools/tutorial-anim
python -I -X utf8 build.py                      # reads %LOCALAPPDATA%\Roblox\Plugins\RoMixamo.rbxm
RBXC="python -X utf8 -I E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py luau 'placeId: 98950102230473' Edit"
for f in out/*.lua; do $RBXC @$f; done           # -> ServerStorage.NHTutorialAnims
$RBXC @out/_chaincheck.luau                      # measures every handoff
```

A freshly registered clip takes a moment to load, so the check waits for each track. A chain reported as NOT MEASURED
means the dummy never moved. Run the check again.

## Publish (owner)

1. In NH Combat Test, publish each KeyframeSequence in `ServerStorage.NHTutorialAnims` (33 pieces) to the group.
2. Paste the asset ids into `TutorialAnim.Ids` (`out/TutorialAnim.luau`).
3. Add the module as `ReplicatedStorage.Config.TutorialAnim`.

The Cine calls:

```lua
TutorialAnim.Play(animator, "TheBus", TutorialAnim.Ids, { [1] = waitForBusCue })
```

`cues[k]` yields until the loop at step k may end. A piece with `Hold` freezes on its last frame (the cold open's
freeze-frame).

## Not done yet

- The Cine controller (`Controllers.Cine`) does not call `TutorialAnim.Play` yet. Wiring the tutorial run into
  `Config.Cine` is the next code step.
- The foot-lock bake (`tools/phase3-2260/anim/footlock.luau`) has not been run on these pieces. Mixamo -> R6 keeps the
  knees' height but not their bend, so a planted foot can slide slightly in the walking pieces.
