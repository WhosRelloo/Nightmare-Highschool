# Anatomy clips: seated R6 shot list

Nine one-shot/loop clips for the student at the bench, built from the pose JSON here with
`roblox-cinematic-animation/scripts/animpro.mjs` (spline, overlap, moving holds `--life 0.6`) and installed by
`make_clips.py` into `ReplicatedStorage.AnatomyClips.Animations` (unpublished; the renderer registers them with
`KeyframeSequenceProvider:RegisterKeyframeSequence`). `clips_map.lua` writes the `Clips` map (step -> clip).

Seated: both hips aimed forward (thighs on the stool), the torso and arms carry everything. The rest pose leans 12°
over the bench with both hands near the tray. No knees or elbows (non-bending R6).

| Clip | Length | Contact | Keys (Right Arm aim [right, up, forward]; torso lean/twist) | Notes |
| --- | --- | --- | --- | --- |
| AnatBenchIdle (loop) | 4.0 s | 1.7 | rest; 1.7 lean -13.5 twist +1.5; 2.6 lean -12.5 twist -1 | alive rest, breathing |
| AnatUnwind | 1.03 s | 0.45 | 0.24 wind back [0.62,-0.25,0.5] twist +7; 0.45 turn [0.62,-0.5,0.78] twist -6; 0.62 overshoot | Key/Driver turns (Unwind, Unscrew) |
| AnatTrace | 1.63 s | 0.35 | 0.2 lift [-0.05,-0.5,0.85]; 0.35 blade down; 0.9 sweep right [0.32,-0.68,0.86]; 1.3 back | head bows -18° over the seam |
| AnatPry | 0.93 s | 0.5 | 0.28 press down [0.15,-0.8,0.75] lean -17; 0.5 lever up [0.15,-0.42,0.92] lean -8 | |
| AnatLift | 0.83 s | 0.4 | 0.22 reach; 0.4 pinch [0.22,-0.82,0.72], root forward/down 0.2; 0.62 lift [0.2,-0.34,0.82] | pick, lift organ; reversed = put down |
| AnatRecoil | 0.83 s | 0.08 | 0.08 jerk back [0.35,-0.25,0.5], root back 0.2; 0.22 peak; 0.5, 0.8 settle | slips (fast in, slow out) |
| AnatLoupe | 1.23 s | 0.5 | 0.3 raise; 0.5 lean in -22, head -22; 0.95 hold, drifting | Inspect step |
| AnatWrite | 1.43 s | 0.4 | 0.25 to the card [0.38,-0.62,0.62]; small scribble 0.4-1.05 | placing on the Specimen card |
| AnatDone | 1.23 s | 0.6 | 0.3 lean in; 0.6 sit back +4°, arms off the bench; 0.85 nod | after the last organ |

Lint: every clip passes animpro's checks; Lift was given a forward root commit (seated hips cannot drop) and Recoil
keeps two `consider` notes (a reaction starts from a dead stop by design).

Prop motion (plate opening, organs lifting, key turning) is tweened by the renderer from `Anatomy.Layout` bones
instead of prop KeyframeSequences: the props are anchored pieces, not Motor6D rigs, until the owner imports them.
