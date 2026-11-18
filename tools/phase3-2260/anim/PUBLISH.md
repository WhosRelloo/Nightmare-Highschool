# The Strikethrough's clips: build, check and publish (2.26.0)

Nine R6 clips for the Chapter One finale. They are derived from the game's own animations (see `REPORT.md`), and their legs are baked so the feet stay planted.

## Build (Studio open on NH Combat Test, Edit mode)

```sh
cd tools/phase3-2260/anim
RBXC="python -X utf8 -I E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py luau 'placeId: 98950102230473' Edit"
for T in StrikeRise StrikeLunge StrikeRecoil StrikeGrab StrikeStagger StrikeTug StrikeShatter YouTugPull YouFinisher; do
  python -I convert.py $T && python -I ground_fix.py $T 30
  node ~/.claude/skills/roblox-cinematic-animation/scripts/animpro.mjs pose/$T.json --grounded --settle light \
    --sheet review/${T}_sheet.png --graph review/${T}_graph.png --trails review/${T}_trails.png \
    --out out/$T.lua --parent game.ReplicatedStorage.NHCineClips
  $RBXC @out/$T.lua
done
sed 's/__ONLY__/nil/; s/__DEBUG__/nil/' footlock.luau > _run.luau && $RBXC @_run.luau      # the foot-lock bake
sed 's/__VERBOSE__/false/' measure.luau > _m.luau && $RBXC @_m.luau                         # the check
```

### The foot-lock bake (`footlock.luau`)

A non-bending R6 leg is rigid, so a planted foot stays put only if the distance from the hip to the contact point stays fixed.

1. **Samples:** each built clip is sampled at 60 fps on a standard R6 rig (2-stud legs).
2. **Pins:** every foot that touches the floor gets its contact corner pinned where it lands.
3. **Per frame,** the bake solves:
   - **Root height:** exactly reaches the pins. With two pins, the higher need wins and the other foot hovers over its pin.
   - **Root hold:** the root is held back if a hip runs out of reach.
   - **Leg swing:** the smallest swing from the leg's last frame, so a planted foot never twists on the floor.
   - **Roll:** about the hip-to-pin line, if another corner would dip below the floor.
   - **Free legs:** stay above the floor.
4. **Release:** pins ease out over 5 frames, and the root lets down from the height it last held.
5. **Repeats:** the solve runs 4 times, so a foot that the new root height brings down gets its own pin.
6. **Steps:** in `STEPS` clips (StrikeTug), a foot whose source slides it far steps instead: it lifts 0.3, travels and plants.
7. **Output:** the clip is rebuilt as 60 fps Linear keys, keeping its markers, loop and priority.

## Measured (`measure_result.txt`, standard R6 rig, 60 fps)

The **audit** column is the house physics audit's rule: per second, the mean skate of the slower grounded foot (sole within 0.12 of the floor) must stay under 0.4 st/s. No sole may go below the floor by more than 0.15.

| Clip | Audit | Planted frames | Frames over 0.6 st/s | Deepest | Biggest torso step per frame |
|---|---|---|---|---|---|
| StrikeRise | PASS 0.08 | 106 | 1 (touchdown) | 0.00 | 0.23 |
| StrikeLunge | PASS 0.04 | 68 | 1 (touchdown) | 0.00 | 0.41 (the lunge) |
| StrikeRecoil | PASS 0.01 | 75 | 0 | 0.00 | 0.09 |
| StrikeGrab | PASS 0.22 | 98 | 2 (touchdown) | 0.00 | 0.43 (the grab) |
| StrikeStagger | PASS 0.01 | 87 | 0 | 0.00 | 0.08 |
| StrikeTug | PASS 0.07 | 67 | 2 (step landings) | 0.00 | 0.29 |
| StrikeShatter | **FAIL 2.23** | 97 | 5 (0.88 to 0.95 s) | 0.00 | 0.31 |
| YouTugPull | PASS 0.01 | 71 | 0 | 0.00 | 0.16 |
| YouFinisher | PASS 0.01 | 99 | 0 | 0.00 | 0.20 |

Before the bake, planted feet skated at 0.6 to 4.9 st/s on average, and feet sank up to 0.25 into the floor.

**Known issue: StrikeShatter.**
- **What happens:** the source (the ghoul's death) drops the hip straight down over a planted foot. An R15 knee can do that; a rigid R6 leg cannot.
- **Result:** for 5 frames the right foot slides out as the body comes down.
- **Tried:** holding the root up (it cancels the collapse), and swinging the hip around the foot like a felled tree (it popped the root by 2 studs when released).
- **Choices:**
  - Re-author the collapse as a fall, with both feet leaving the floor.
  - A kneel, with the leg swung back.
  - Frame the Pages shot so the feet are out of view.

## Publish (the owner)

1. In Studio, open `ReplicatedStorage.NHCineClips.Animations`.
2. For each of the nine KeyframeSequences: right-click, **Save to Roblox**, and publish under the group.
3. Paste each asset id into `ReplicatedStorage.Config.CineClips`. For example: `StrikeRise = "rbxassetid://<id>"`.
4. Until then the director plays the Studio preview ids, so the cut works in Studio playtests only.
