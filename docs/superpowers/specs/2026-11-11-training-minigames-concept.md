# Training minigames: concept (2026-11-11)

**Status:** concept for the owner's approval. Nothing is built.

**The owner's ask:** "I want the training system to update each area you work on LIVE and 1 area at a time. (Legs, arms, Torso). It should be like the Baki/Kengan Ashura games on roblox where they have minigames for each, and the minigames get harder as you progress."

**What exists today:**
- Ten body types (`docs/Body-Types.md`), each built from five R6 meshes: torso, two arms, two legs. A build is set only by `Appearance.SetBuild(player, build, step)` (server) or the admin desk. There is no training yet.
- Three level-up stats (`docs/Progression-and-Stats.md`): Might, Grit and Wits.
- The gym kit (props batch 43): punching bag, climbing ropes, rings, wall bars, rowing machine, medicine balls, vaulting box.

## The core idea: three areas, trained separately, shown live

- Every student has three **training areas**, each with its own level from 0 to 20: **Arms**, **Torso** and **Legs**.
- **One area at a time:** a session trains exactly one area. You pick it at the training spot, and that area's minigame starts.
- **Live body:** when a set ends, the trained area's body meshes step up on the spot. A short flex pose and an ember-and-chalk-dust burst on that area show it. The other areas don't change, so a student with big arms and skinny legs looks like that.
  - This works because each body is already five separate meshes. Today a build swaps all five together. Training would swap only that area's meshes: the torso, both arms, or both legs.
- **Build path per area:** each area also drifts toward a shape, chosen by how you train and eat:
  - **Conditioned:** lean muscle, from training while fed.
  - **Heavy:** mass, from eating a lot and lifting heavy.
  - **Lean:** wiry, from lots of reps on an empty stomach.
  - **Average:** the start.

  This keeps the ten existing builds but lets them differ per area. It ties into the QOL kit's snack tin, thermos and the café.
- **Gender:** the female body types (Petite, Toned, Curvy, Strong, Plus) follow the same paths, as today.

## Mesh steps (art)

| Area level | Look |
|---|---|
| 0-4 | the base body |
| 5-9 | step 1 of its path |
| 10-14 | step 2 |
| 15-19 | step 3 (new meshes) |
| 20 | step 4, "peak" (new meshes) |

- **Today:** there are 2 steps per path.
- **Adding steps 3 and 4:** new arm, torso and leg meshes for each path and gender, about 3 paths × 2 steps × 5 meshes × 2 genders = 60 new meshes. The body-types session's pipeline makes them.
- **Rules:** every step stays inside the R6 part boxes (the owner's rule: still R6 proportions), so clothing and animations keep working.

## The owner's training animations (already made)

The owner has animations for sit-ups, push-ups, pull-ups, the barbell and squats. Four are already in NH Combat Test, where `Features.AmbientNpcs` (the `ANIM` table) plays them on the ambient gym students:

| Exercise | Area | Animation ids | What's missing |
|---|---|---|---|
| Push-ups | Arms | idle 111737875654076, rep 112288220550648 | nothing |
| Pull-ups | Arms | idle 134151351487837, rep 115584556914404 | nothing |
| Barbell | Arms and Torso | idle (holding the bar) 136973050103731 | a lift rep, if there is one |
| Sit-ups | Torso | 132757288791974 (one looping rep) | a split idle and rep would make reps crisper |
| Squats | Legs | not in the game yet | the id |

These five are the **main minigames**, one exercise at its own station: a mat for push-ups and sit-ups, the gym's wall bars or a pull-up bar, a weight bench or rack for the barbell, a squat rack. Each player rep plays the rep animation once, and the idle holds between reps, so the body moves with every input. The minigames below are extras that add variety on top.

| Area | Main | Extras |
|---|---|---|
| Arms | push-ups, pull-ups, barbell curls or press | heavy bag, rope climb, bell pull |
| Torso | sit-ups, the barbell (deadlift or bench) | plank, medicine ball, stone lift |
| Legs | squats (with the barbell on the back at higher levels) | stair sprint, jump rope |

**How a rep works in the main five:** a ring shrinks around a brass gauge, and you press when it meets the mark (good, great, perfect). Each rep plays the rep animation, and a combo counter builds. At higher levels the ring speeds up and the windows narrow. "Heavy" reps (hold to grind) and "burnout" sets (as many reps as you can before a stamina bar runs out) mix in, and the weight on the bar visibly grows (plates added).

## The minigames

These are original designs, not copies of another game. Each area has three minigames at different training spots. They all use the same three inputs (tap, hold or release, and direction keys), with gamepad and touch equivalents.

### Arms
1. **Heavy bag combos** (the gym's punching bag): a combo of key prompts appears over the bag. Hit each in its beat window. Hitting all of them lands a finisher that swings the bag.
2. **Rope climb** (the gym's climbing ropes): alternate left and right on a rhythm to climb. A missed beat makes you slip down a little.
3. **Bell-tower pull** (the chapel bell rope): pull and release with the bell's swing. Pull at the top of the arc to ring it. The whole campus hears a good set.

### Torso
1. **Plank balance:** keep a needle centred in a crimson zone while it drifts, using left and right. The drift speeds up, and crows land on your back as distractions.
2. **Medicine-ball partner throws** (the gym's medicine balls): catch and throw on a rhythm with a trainer NPC. The throws come faster and from odd angles.
3. **Stone lift** (an atlas stone in the Back Lot): charge a power bar, release in the green band, then hold balance as you rise.

### Legs
1. **Clock-tower stair sprint:** a real run up the tower stairs, against the clock, with a tap rhythm to keep your stride. Rain makes the stairs slippery.
2. **Squats with a sack:** hold a slider inside a moving band through the down-and-up motion.
3. **Rooftop jump rope:** jump on the beat, with doubles and crosses at higher levels. Missing three times ends the set.

### How they get harder (per area level)

| Level | What changes |
|---|---|
| 0-4 | wide windows, slow tempo, short sets, generous fails |
| 5-9 | tighter windows, longer combos, a fake prompt now and then |
| 10-14 | faster tempo, distractions (lights flicker, crows, rain), mixed directions |
| 15-19 | very tight windows, combos that change mid-set, stamina drain on misses |
| 20 | "Trial" sets: one long set judged by a trainer NPC; a perfect set earns a title |

## Pacing and rules

- **Training XP:** each set gives area XP, scaled by accuracy. A perfect set gives a bonus. A failed set gives a little XP and costs more stamina.
- **Fatigue:** each area has its own soreness. Training the same area again soon gives less XP, which pushes students to rotate arms, torso and legs. Sleeping in your dorm (Homes) or eating clears soreness faster.
- **Daily cap per area:** stops someone grinding a level in one night. Leaving your area at a training spot counts as resting.
- **Food and path:** each set checks a "fed" meter.
  - Fed and accurate: moves the area toward Conditioned.
  - Very fed and heavy minigames (stone lift, sack squats): toward Heavy.
  - Hungry with fast reps (rope, stairs): toward Lean.
- **Stat effects** (small, added on top of the level stats):

| Area | Bonus |
|---|---|
| Arms | a little Might: damage and grip strength |
| Torso | a little Grit: health and posture |
| Legs | sprint speed, stamina and dodge recovery |

  The exact numbers go in `Config.Progression`, for balancing.
- **Watching:** other players can see you train, which helps the gym feel alive. Clique standing with the Athletes rises slightly from training at the gym.

## Technical outline

- **Saving:** `PlayerData.Training = { Arms = { Level, Xp, Path, Sore }, Torso = {...}, Legs = {...}, Fed, LastTrained }`, through ProfileService PlayerData only.
- **Server-authoritative:**
  - The server starts a set and sends its seed (the prompt timings).
  - The client plays the minigame and reports its hits with timestamps.
  - The server checks them against the seed (impossible timings are rejected), awards XP and calls a new `Appearance.SetArea(player, area, path, step)`. That's the per-area version of `SetBuild`, and the only way an area changes.
  - Rate limits and daily caps are applied on the server.
- **Appearance:**
  - `ApplyTo` takes per-area meshes: the torso from one path and step, the arms from another, the legs from a third.
  - The creator still offers only gender.
  - The existing 10 builds map onto the three areas, so saved students keep their bodies.
- **UI:**
  - The minigame HUD uses the game's UI kit: brass gauge frames, crimson zones, ink prompts.
  - A **Training** page in the Student Record shows the three areas, their levels, paths, soreness and next mesh step, beside a live preview of your body.
- **Controls:** keyboard, gamepad and touch for every minigame, and Reduce Motion for the flex and VFX.

## Phases

1. **One full loop:** the training data, Arms only, with the heavy bag and the rope climb, the live arm swap on the existing mesh steps, saving, and the server checks. Play-test, then the owner reviews the feel.
2. **Torso and Legs:** their minigames, fatigue, food and paths.
3. **The new mesh steps 3 and 4,** the Trials, titles, and the Student Record page.
4. **Map place sync.**

## Questions for the owner
- What is the squat animation id, and is there a barbell lift (rep) animation to go with the barbell idle?
- Should training replace the admin Build row for players, with the row kept for staff only? Recommended: yes.
- How fast should a dedicated player reach level 20 in one area? Suggested: about 2-3 weeks of daily play.
- Should Heavy and Lean be choices players can aim for, or only side effects of how they eat and train? Suggested: side effects, with the Training page showing which way each area is drifting.
