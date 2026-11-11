# School students in the Map place (1.78.0)

Owner: "Start putting a few school NPC's in the Map place, but COMPLETELY upgrade their pathfinding & awareness".

The Map has **six background students** who live by the school clock on the builder's map. They walk with a new navigator (`Services.AI.Nav`) and notice the world through a new awareness module (`Services.AI.Senses`). Both are written so NH Combat Test's own students (`Features.Schedules`) can use them later.

The sources are copied into `tools/map-students/`.

## What's in the Map

| Piece | What it does |
|---|---|
| `ServerScriptService.Services.AI.Nav` | The navigator: planning, doors, steps, smoothing, avoidance, recovery |
| `ServerScriptService.Services.AI.Senses` | Sight, hearing and reading players |
| `ServerScriptService.Services.Features.MapStudents` | The students: bodies, looks, the school day, reactions |
| `StarterPlayerScripts.Controllers.World.NpcLook` | Client: smooth head turns and speech bubbles |
| `ServerStorage.NHCore.NpcRig` | The students' body (NH Combat Test's NPC rig, 67 parts) |
| `workspace["School NPC Spots"]` | Where students go (see below) |

Everything is tagged `NHCore`. The Map's own `Services.AI.AI.Rig` (only an Animate script, so the admin desk's sparring partner can't spawn) is untouched.

## Where they go

Parts tagged `NHNpcSpot` with a `Kind` attribute, in `workspace["School NPC Spots"]`. They're faint neon discs in Edit and invisible in play. Each spot was placed by checking for floor, room to stand, and a real path from the gate:
- **Gate** (1): just outside the front gate. Students come in and leave here.
- **Yard** (8, four talking pairs): the front yard. Spots with the same `Group` attribute face each other.
- **Inside** (7): the ground-floor halls, used at class and passing times. The classrooms aren't fitted yet.

The folder's `Students` attribute sets how many students there are (6).

**For the builder:**
- Move a spot or turn it: a spot's front is the way a student faces there.
- Add more by copying a spot. Keep the tag and the `Kind`; give pairs the same `Group`.
- **The courtyard has no ground-floor way in yet.** The only route the planner found was up to the second floor and a 31-stud drop out of a window. So the courtyard has no spots; add some once it has a door.

## The day

It follows `School.SchoolClock`:
- **Night and Morning:** off campus.
- **Before School:** they come in through the gate and hang out in the yard.
- **Passing:** they drift between the halls and the yard.
- **Class:** they wait in the halls.
- **Break and Lunch:** the yard, in pairs.
- **After School:** the yard, and from 14:00 a third head home.
- **Evening:** everyone is home by 19:00.

Each student has a personality: bravery (0.1 to 0.85), sociability (0.15 to 0.95) and a walking pace (5.4 to 7 studs/s). Looks are rolled from school clothes only: never the admin kit, and hair matches the body.

## Pathfinding (Services.AI.Nav)

What's new compared with `Features.Schedules`' walker:
- **Doors.** While the game runs, every leaf of a door-kit door (tag `NHDoor`) gets a passable `PathfindingModifier` labelled `NHDoorway`. Locked doors get none, and that updates when a door is locked or unlocked. Walking up to a closed door, a student opens it through `Features.Doors.Toggle`, swinging it away from them like a player would. Frames with no leaf (the builder's archways) are left alone.
- **Steps and ledges.** Students can jump, so they climb the front steps (the planner needs jump links there). Jumps cost extra, so stairs win where both exist.
- **No leaps.** A path with a drop of more than 5 studs is refused.
- **Smoothing.** Students cut straight to the furthest waypoint they have a clear, floored line to (checked at knee and chest height, three rays wide). They never cut past a jump or a doorway.
- **Avoidance.** Students predict where others will be (the closest approach within 1.6 s) and nudge sideways. Players get more room. Students slow behind someone in the way, and never steer backwards. In doorways and on steps they ignore other students, who pass through each other anyway, so doorways never jam.
- **Recovery.** A stuck student escalates: hop the lip, sidestep, then back off and re-plan. "Blocked" from the nav mesh only counts when the way ahead is really shut. A student pushed far from its path re-plans. A goal a student can't reach is remembered for 25 s, by that student only.
- **Planning.** Paths are planned at most three at a time, and each has a 4 s time limit, so a hung planning call never holds the others up.
- **Motion.** The walk clip matches the real speed, the run clip plays above 10 studs/s, and students ease in at the end of a path.
- **Debug:** set the workspace attribute `NHNavDebug` to true in Studio to draw each path (red walk, gold jump, blue doorway). Studio-only attributes on each student: `NHNav` (the path step), `NHNavWhy` (why the last walk ended) and `NHStep` (what the brain is doing).

## Awareness (Services.AI.Senses)

- **Sight:** a 150° view cone with a 50° focus, out to 60 to 80 studs, halved at night. Sneaking students (the Progression stat `NH_Stealth`) are seen from closer. Line of sight is a real raycast to the head or chest: walls, closed doors and props block it, glass and see-through parts don't. Awareness builds over a moment (faster in focus, close up, or if they move) and fades out of sight.
- **Hearing:**
  - fights (every hit, `Downed.OnDamage`);
  - someone downed or finished (a scream);
  - doors opening and closing;
  - someone sprinting up behind.
  Sounds through walls are muffled to two-thirds of their range.
- **Reading a player:**
  - in a fight (`CombatTagUntil`), transformed (`Transformation`) or downed (`DownedUntil`);
  - coming straight at me (about a second away);
  - right up close for over 1.2 s;
  - facing me from close by for 2.5 s (staring);
  - keeping behind me while I walk (following).
- **Budget:** each student thinks 5 times a second with players within 120 studs, and once a second otherwise.

## Reactions (most urgent first)

1. **Danger.** A fight, a monster or a body too close (10 to 22 studs, braver students let it come closer): they say "Whoa!", "Not again..." or "What IS that?", run away, then watch from a distance.
2. **Gawk.** A fight they can see or hear within 55 studs: they stop, turn, and watch until it's been quiet for 6 s.
3. **Make way.** Someone coming straight at them: they step aside (away from where that student is heading) and look at them.
4. **Space.** Someone standing right on top of them: they step back ("Uh... hi?", "Personal space?") and then move to another spot.
5. **Stared at.** They look back. Sociable students say hello ("Hey.", "Evening.", "You new here?"). Shy ones move off after a while.
6. **Followed.** They glance back, walk faster, and might say "Are you following me?".
7. **Glance.** Their head follows whoever they're most aware of. Otherwise they look at the friend they're talking to, at a door that opened, or around now and then.

Students also turn to face a friend who joins them at a spot, and never walk to a spot a player is standing on.

## Tested (Map place, local play-test)

- **Walking, all six students:**
  - in through the gate, up the front steps and through the entrance's double doors (opened by the students);
  - along the ground-floor halls to all seven hall spots, east and west ends included;
  - back out to the yard pairs.
  - No window drop once drops were refused.
- **Pairs:** both faced each other (1.00 / 1.00).
- **Staring:** the most sociable student looked at the player's head within half a second, went Friendly and said "Evening.".
- **Head turn:**
  - with the player 50° to one side, the head turned 50° that way and the body stayed;
  - outside the 75° side vision (81° off), nobody noticed, as intended.
- **Space:** after about 1.3 s the student stepped back 3 studs, and (after the fix) moved to another spot.
- **Danger:** the player marked as in a fight 8 studs away. The student said "Whoa!", ran at 14.5 studs/s to 31 studs away, and watched. Another student about 31 studs away with a view of it watched. One 47 studs off and out of sight stayed calm.
- **Monster:** the player transformed 9 studs away. The student said "What IS that?" and backed off.
- **Make way:** walking straight at a student, it stepped 4 studs aside when the player was about 6 studs away.
- **Performance:** the server held 60 fps (16.7 ms frames, worst 18 ms) with all six walking and sensing.
- No script errors.

## Not tested

- **Followed:** it needs a student walking with a player behind it for 8 s.
- **Hearing a real fight:** combat events can't be raised from the test tools, so the fight was a combat tag on the player.
- **Locked doors**, and a door closing on a student mid-doorway: student parts can't be queried, as in NH Combat Test, so a door may shut behind them after 7 s.
- **Two or more players**, phones and tablets.
- **A whole in-game day** (only Class, Break and After School / Evening were watched).
- **Night vision range.**
