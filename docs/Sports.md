# Sports Clubs

**Status:** basketball (1.0), soccer (1.1) and football (1.2) are built and playable in NH Combat Test, each with two drills, a club and a tryout. Football has been tested solo only.
- Design: [superpowers/specs/2026-10-30-sports-design.md](superpowers/specs/2026-10-30-sports-design.md). Plan: [superpowers/plans/2026-10-30-sports-1.0.md](superpowers/plans/2026-10-30-sports-1.0.md).

## Clubs and coaches
| Club | Sport | Coach (NPC post) | Venue |
|---|---|---|---|
| **Night Ravens** | Basketball | Coach Varga (inside the gym, by the practice end) | Gymnasium, south of the school |
| **Grave Rovers** | Soccer | Coach Mallory (north wall of the pitch) | Pitch, west of the gym |
| **Iron Wardens** | Football | Coach Dunmore (south sideline) | Field, north-west of spawn |

- **Joining:** talk to the coach. You can be in one sports club at a time, independent of factions.
  - Switching clubs resets your club rank to Rookie. Leaving is free.
  - Coaches answer "How am I doing?" with your rank, record, points to the next rank and your best drill score.
- **Club EXP and ranks:** Rookie 0 → Starter 150 → Varsity 500 → Captain 1200. Reaching Captain awards a title ("Ravens Captain").

  | Source | Club EXP |
  |---|---|
  | A passed drill | 10 |
  | A new personal best | +10 |
  | A ranked game played | 25 |
  | A ranked win | +25 |
  | MVP | +15 |

- **Ranked games:** a game counts as ranked when it starts between 12:00 and 20:00 in-game time and at least one member of that sport's club is playing. The win/loss record is kept for members.
- **The Students list** shows a club tag in the club colour (e.g. "Ravens", or "Ravens Captain") for students you know.
- **Tryout:** *Night Ravens Tryout* from Coach Varga: pass the Shootaround (3 spots or more), then play a full basketball game. Reward: 20 yen and +3 popularity.

## Basketball (Highschool Hoops style)
**Controls while you hold the ball**

| Key | Action |
|---|---|
| **E** (hold, release) | Shoot. The kit meter beside you fills; release in the green glow for a perfect shot. Held past the top, the shot goes up late on its own. |
| **Click** | Pass toward where you aim (the open teammate closest to your aim) |
| **Q / R / F / C** | Crossover / behind-the-back / spin / between-the-legs. Moves chain within 0.35 s, and pressing another move in the first 0.2 s cancels into it. |
| **Z** | Euro step. Shoot within 0.9 s for a layup from 4 studs farther out, with the contest cut in half. |
| **G** (hold) | Post up (halves the contest on your next shot) |

**On defence:** **Click** reaches for a steal (4 studs, 1.2 s cooldown). **Jump** to block: one roll per jump, at most one jump every 0.9 s, within 0.4 s of the release and in reach.
- **Phone and gamepad:** while you're in a game or drill, four buttons with the kit's seal art appear: Shoot (R2, hold), Pass/Steal (X), Move (Y, cycles the four moves), Euro (B). Jumping blocks on every device.
- Reaching into a dribble move gets you crossed up: "Ankles!", and a 2.4 s steal cooldown.

**Release feedback:** *Perfect Release* (green), *Slightly Early / Late* (okay), *Very Early / Late* (bad).

**Shooting** (all rolled on the server)
- **Timing:** the hold is measured only on the server (ShootStart to ShootRelease). The client's number is never trusted.
  - The perfect hold is 0.62 s, with a green window of ±0.075 s and an okay window of ±0.17 s.
  - Make chances: green 92%, okay 48%, bad 6%.
- **Contest:** the closest defender in front within 6 studs shrinks the green window by up to 70%.
- **Distance:** make chances fall off beyond 30 studs.
- **Stats:** Wits widens the windows (+0.4% per point).
- **Layup:** inside 6 studs while moving, 82% chance.
- **Dunk:** inside 4 studs with Might 10 or a running start, 95% chance.
- **Points:** 3 points beyond the arc (22 studs from the rim), otherwise 2.
- **Race perks:** Vampire +6% accuracy at night · Wraith +8% steal and block reach · Ghoul −15% chance to be stripped · Human +12% stamina regen · Priest +6% pass accuracy · Werewolf +15% stamina on full-moon nights.

**Rules**
- **Format:** first to 21, or two 4-minute halves. A tie goes to overtime (next score wins, 2-minute cap).
- **Shot clock:** 24 s, reset to 14 after an offensive rebound off a shot.
- **Buzzer-beaters:** a make still in the air when the clock hits zero counts. The clock waits up to 3 s for it.
- **Check ball:** after a score, the other team checks it at the top. There are no steals for 1.5 s.
- **Half court:** when both sides have 2 or fewer players, both teams play the west hoop. A team that wins the ball on a rebound or steal must clear it past the arc before its shot counts.
- **Out of bounds:** the other team's ball.
- **Leaving the game:** getting downed (fighting is allowed), leaving the game, or 5 s outside the court bounds takes you out. A side with nobody left forfeits.
- **Joining:** stand on a team pad by the scorer's table. A 10 s countdown starts when both sides have a player. Late arrivals fill open slots up to 5v5, and teams are balanced at the start.
- **Stamina:** sprinting and dribble moves spend stamina (100, plus Grit). A move with no stamina left fails ("Out of gas").

**Rewards:** Progression EXP in the new **Sport** category, yen and popularity, plus club EXP and record for ranked games.

| Result | EXP | Yen | Popularity |
|---|---|---|---|
| Game played | 40 | 8 | 1 |
| Win | +40 | 12 instead of 8 | 2 instead of 1 |
| MVP | +25 | | |

- **Rewards need:** at least 60 s of live time in the game and at least 60 s played by you.
  - You must have won, caught or rebounded the ball twice, or scored. A check ball handed to you doesn't count.
  - One rewarded game every 3 minutes.
  - A forfeit pays no win bonus and writes no record.
- **Post-game card:** the score, ranked or pickup, MVP, your line (points, assists, rebounds, steals, blocks) and what you earned.

**Drills** (practice end of the gym, E on the purple start pads)
- **Shootaround:** 60 s. Shoot from the lit spot and it moves on after each make. Pass with 3 makes; all 10 ends it early.
- **Cone Dribble:** weave six cones. Hit a dribble move as you round each one, then cross the finish line. Under 60 s passes; the fastest time is your best.
- **Passing:** SportDrill EXP (20), club EXP, a personal best, and the tryout objective.
  - Rewards pay once per drill every 3 minutes; later runs still count for bests.
  - Quitting (X) or leaving the practice court gives nothing.
  - A cone run faster than 4 s, or moving faster than possible between checks (a teleport), doesn't count.

## Soccer (Sports 1.1, Grave Rovers)
Built to play close to a Blue Lock-style Roblox soccer game the user supplied as a reference (`Huh.rbxl`).
- Only the mechanics and feel were studied. No code, characters or assets were copied.

**Controls** (soccer games and drills)

| Key | With the ball | Without it |
|---|---|---|
| **Click** (hold, release) | Shoot. A 0.36 s charge gives full power, aimed with the camera; a tap kicks where you face. Hold **A / D** at full power to curve the ball late. | Volley or header: a 0.3 s kick window strikes the next ball that reaches you |
| **R** | Pass to the teammate nearest your aim (into space if nobody is there) | Call for the ball (teammates see a marker) |
| **Q** | Dribble burst. A tackle landing in it breaks the tackler's ankles (ragdoll 1.9 s). | Keeper in their box: dive |
| **Right-click** | Feint: counters a tackle (the tackler is stunned) | |
| **E** | | Tackle: a lunge with a 0.65 s steal window. A miss stuns you for 1.2 s. |
| **T** | Bloodrush | Bloodrush |

- **Phone and gamepad:** kit-art buttons for Kick (R2), Pass (X), Dribble/Dive (Y), Tackle (B), Feint (L2) and Bloodrush (L1).
- **Combat keys:** while a character carries `SportKeys`, the E (equip), R (heavy) and Q (dodge) combat binds step aside.

**Ball:**
- **Holding and shooting:** the ball sits at your feet (a weld), and the server owns it.
  - Shot velocity is aim × 120 × power, plus lift.
  - Curve is a sideways push that eases out and pulls back late.
  - Rolling friction applies on the ground.
- **Pickup reach:** you trap a loose ball within 4.2 studs. A keeper in their box reaches 6.5, and a diving keeper or a lunging tackler reaches further.
- **Ball-only walls:** invisible walls on the stone-wall line (collision group `SportBallWall`) keep the ball in play. Players walk through them, so there are no throw-ins, corners or goal kicks.
- **Model:** our Blender soccer ball (`ServerStorage.NHSportModels.Soccer`) is the ball's look. Fast balls leave a trail, and high balls show a landing marker.

**Rules:**
- **Format:** 1v1 to 5v5 from the halfway-line pads. First to 10, a 5-goal lead, or the most goals after two 4-minute halves. A tie goes to golden-goal overtime.
- **Goals:** a ball crossing into a goal mouth scores, checked along its whole path so fast shots can't slip through.
  - After a goal there's a 3.5 s celebration: a goal-mouth flare, the scorer's close-up and a pose.
  - Then the team that conceded kicks off from the centre spot.
  - An own goal counts for the other team. An assist is a teammate's pass within 12 s.
- **Keepers:** from 3v3, a player who queues on their side's **keeper pad** becomes the keeper.
  - In their box, the keeper has the long reach and the dive, and clicking with the ball throws it.
  - Holding the ball more than 6 s in the box throws it automatically.
- **Stamina:** sprinting drains it; dribble 11, tackle 20, feint 8. Holding the ball regenerates stamina 35% slower.
- **Bloodrush:** a meter that fills from steals (+10), ankle breaks (+10), goals (+20) and shots on target (+5).
  - At 45 or more, **T** spends it on up to 18 s (scaled by the meter) of +10% shot power and 30% less sprint drain.
  - It shows an aura in your race's colour.
- **Race perks:** Wraith tackle reach, Ghoul strip resistance, Priest pass accuracy, Vampire night shot accuracy, Human stamina regen.

**Drills** (practice ground south of the pitch; E on the green start pads)
- **Target Practice:** 60 s. Shoot from behind the line at the lit corner target. Pass with 4.
- **Wall Passes:** 45 s. Pass into the rebound wall from behind the line and control the return within 3 s. Pass with 8.
- **Rewards:** as in basketball, one rewarded run per drill every 3 minutes.

**Grave Rovers Tryout** (Coach Mallory): pass Target Practice, then play a full soccer game. Reward: 20 yen and +3 popularity.

**Animations** (`Config.Sports.SoccerAnims`): clips from the group library (15981569), the closest fit per move.
- **Rules (the user's call):** no combat clips, and no movement clips except the slide.
- **Used:**
  - **Tackle:** "SLIDING"
  - **Keeper throw:** "Activate"
  - **Goal celebration:** "Isagi Celebration", cut after the 3.5 s goal pause
- **Procedural poses (no fitting clip exists):** kick, charge, pass, volley, header, dribble, feint, the ankle-break fall and the keeper dive.
- **Playback:** every clip plays once, at Action2 priority, and stops with its move. Some movement clips are saved looping, so the loop is turned off.
- **What the group's soccer uploads turned out to be** (each checked for length, rig and moving joints): camera and letterbox cutscene rigs, character ultimates, long character cutscenes and a dragon rig. None are gameplay moves.

**Venue additions** (`Workspace.Sports.Pitch.Soccer`):
- ball-only walls and ceiling
- keeper zones (`SportKeeperZone` = the defending team) and keeper pads (`SportKeeperPad`)
- the practice ground: a target goal with 4 targets and sensors, a rebound wall and sensor, drill pads, balls and bounds

**Code:**
- `Services.Sports.Soccer` (rules and drills) and `Controllers.Gui.Soccer` (controls, meters, poses, effects).
- `Config.Sports.Soccer` and `RaceAura`.
- **Shared changes:**
  - **Ball:** `Kick`, `ReachFor`, friction, and the collision group for soccer balls.
  - **Matches:** keeper pads queue, mercy rule.
  - **Sports client:** gated to basketball input, with shared state and hints exported.

## Football (Sports 1.2, Iron Wardens)
Plays like *Football Fusion 2* (the owner's pick), with an optional quick play call from *NFL Universe Football*. Only the feel was studied; the code and art are original.

**The field:** 60 yards between the goal lines (x -154 west, -34 east), 2 studs a yard, 8-yard end zones, 32 yards wide. Team A (Crimson) scores in the west end zone; B (Ash) in the east.

**A down**
1. **Huddle (6 s, optional):**
   - The QB can call a play with **1-6**: Slants, Verticals, Posts, Curls, Outs or Screen. The routes draw for the offence only.
   - The defence can press **1** (man: your receiver gets a mark) or **2** (zone: a circle) for coverage hints.
   - On 4th down the huddle adds **P** (punt) and, inside 30 yards, **K** (field goal).
2. **Line-up:** the QB is the offence player closest to the ball as the huddle ends. Receivers spread across the field; defenders line up 5 yards off, with one rusher.
3. **Snap:** the QB presses **Space** within 20 s. Late is delay of game (-5 yards).
4. **Rush count:** "1, 2, 3 Mississippi". Defenders can't cross the line until it ends (a throw, handoff or QB crossing the line ends it early).
   - Each defender's own client holds a wall there, which only blocks them, and the server pushes back anyone over the line.
   - Before the snap nobody may cross.
5. **The play ends** on a tackle, out of bounds, a kneel, an incomplete pass, a touchdown or a safety. The ball is spotted there.

**Controls**

| Who | Key | Action |
|---|---|---|
| QB | Z / C, then click (aim with the mouse) | Set the power level (10-100 in steps of 5, also before the snap), then click to throw at it. Low power is a high lob, high power a flat bullet (the HUD bar says LOB / SPIRAL / BULLET). A gold ring shows where it would land. Might adds range. One forward pass a play, from behind the line. |
| QB | F / G | Pump fake / hand off to the closest teammate within 6 studs |
| Anyone | click | Reach for the ball in the air (catch or interception) |
| Anyone | Space / Q | Jump catch / dive (10-stud lunge, +1.5 studs of reach while you click, 20 stamina) |
| Carrier | E / R, F, K | Juke left / right, spin (both break a tackle in their window), kneel |
| Defence | touch, R, C | Tackle, hit stick (25% fumble; a miss stumbles you for 1 s), swat |
| Kicker | hold click and release, O | Kick (aim with the camera), onside (kickoff) |
| Returner | V | Fair catch |
| After a TD | 1 / 2 | Extra point (automatic) / 2-point try from the 5 |

- Touch and gamepad: Action (R2: throw, kick or catch), Dive (B), Juke (Y), Hit / Swat (X), Snap / Fair catch (L1).

**Catching (Football Fusion style)**
- Click to reach. Your arms follow the ball while you reach (up to a second while you hold). Every client draws this for every character, from the server's `F_Reach`.
- The ball snaps into the hands of whoever's reach it touches first along its flight. Reach is 3.75 studs from the shoulders (3.25 for an interception), plus Wraith's +8% and a dive's +1.5: be under the ball.
- Every catch needs a click, a dive catch too (a click anywhere in the dive counts). The click window is 0.25 s, and a whiffed click locks the next one for 0.8 s.
- A faint ring on the grass shows everyone where a ball in the air will come down.
- Thrown balls spiral (nose along the flight, spinning faster on a bullet).
- A click is judged against where the ball was over the last 0.3 s, and a landed ball waits 0.3 s before it's ruled incomplete. This covers network delay.
- Once caught, the ball sits in the right palm, long side forward, and the right arm holds it tucked while you run.

**Kicks:** kickoffs from your own 20, onside kicks (live after 5 yards), punts and field goals all use the kick meter. A ball in the end zone is a touchback at the 12. A field goal must pass between the uprights above the crossbar.

**Scoring and rules**
- Touchdown 6, extra point 1, 2-point try 2, field goal 3, safety 2.
- 4 downs to gain 10, or the ball turns over. A fumble is loose: whoever recovers it has the ball.
- Two 4-minute halves; the clock runs only while the ball is live. Overtime is next score wins. A 35-point lead ends the game.

**Race perks:** Vampire (at night) and Priest throw accuracy, Wraith catch and swat reach, Ghoul a 15% chance to shrug off a touch tackle, Human stamina regen.

**Drills (the practice lanes west of the Field, x -250..-184)**

| Drill | How | Pass |
|---|---|---|
| Route Runner | Stand on the gold spot. The machine calls a route and draws it, then throws to you once you're on the last leg (it leads you along the route). Click to catch. | 6 of 10 |
| QB Targets | Throw from the gold spot through three moving rings at 10, 20 and 30 yards: 1, 2 or 3 points. | 10 points in 60 s |

- Bests are saved on the club sheet (`Drills.RouteRunner`, `Drills.QBTargets`).
- **Iron Wardens Tryout** (Coach Dunmore): pass Route Runner, then play a football game. Reward: 20 yen and +3 popularity.

**Testing tools (Studio only):** TestBridge has these commands:
- `FootballState` (the mode, down, spot, holder, ball and score)
- `FootballDummy(team)` (a test defender that chases the carrier after the count)
- `FootballSpot(down, yardsToGoal)` (put the ball on a down and spot, then huddle)
- `SportForce("Field", name, "", true)` starts a one-player test game

**Not tested yet:** anything between two players, namely:
- a real QB-to-receiver catch and contested catches
- interceptions
- jukes and spins against a tackler
- hit sticks, swats and fumbles
- fair catches, onside recoveries and returns

## Venues (Workspace.Sports)
- **Gymnasium**
  - Gothic stone hall at x 30..190, z 112..192.
  - Court 84×46 studs, rims at 9 studs, three-point arc 22.
  - Bleachers, hanging lamps, a scoreboard, team pads and the scorer's table.
  - Practice end: a practice hoop, 10 Shootaround spots and the cone course.
- **Pitch:** 120×76 studs at x −220..−100, z 107..183. Goals with nets, a low stone wall, floodlights and a scoreboard.
- **Field:** 60 yards plus two 8-yard end zones (2 studs per yard) at x −170..−18, z −190..−126. Yard lines and numbers, goalposts, bleachers, floodlights and a scoreboard.
- **Compass markers:** Gymnasium, Pitch, Football Field.
- **Venue contract (attributes):**
  - `SportVenue` on the model
  - `SportPad` A/B, `SportCourt`, `SportBounds`, `SportBall`, `SportGoal` (the team that scores there), `HalfCourt`, `SportScoreboard`
  - `SportDrill` / `SportDrillStart` / `SportDrillSpot` / `SportGate` / `SportDrillFinish` / `SportDrillBall` / `SportDrillBounds`
  - `NpcPost` (coaches)

## Models (Blender)
- **The four models:** basketball, soccer ball, football and training cone.
  - Modelled in Blender with baked PBR maps: colour, normal and roughness.
  - Files: `art/sports/sports_models.blend`, `art/sports/fbx/*.fbx`, `art/sports/textures/`. Asset ids are in `art/sports/fbx/textures.json`.
  - Previews: `art/sports/showcase_sports.png`.
- **Importing:** import the FBX files with File → Import 3D. A setup script then files them as `ServerStorage.NHSportModels.{Basketball, Soccer, Football, Cone}` with their SurfaceAppearances and swaps the gym cones.
  - `Services.Sports.Ball` uses a model as the ball's look when it exists. Physics stays on a sphere, so the bounce is the same either way.
  - Until then the balls are plain spheres with seams.

## Code (NH Combat Test)
| Module | Job |
|---|---|
| `ReplicatedStorage.Config.Sports` | clubs, ranks, rewards, race perks, basketball tuning, drills; pure `Sanitize`, `RankFor`, `NextRank`, `Perk` |
| `Services.Sports.Clubs` | membership, club EXP and ranks, records, drill bests; `PlayerData.Sports` via `SetSports`; `Club` / `ClubRank` attributes; remotes `NHSports.Get` / `Updated` |
| `Services.Sports.Ball` | the server-owned ball: possess (weld), launch (solved arc), 10 Hz touch / out-of-bounds scan; `HasSportBall` on the carrier |
| `Services.Sports.Matches` | the match core and plug-in API (`Setup, Start, Tick, OnAction, OnRemoved, Stop, Hud, Halftime, Joined`); remotes `Action` (20/s), `Hud`, `Summary`, `Fx` |
| `Services.Sports.Basketball` | the rules above and the drills (prompts on the start pads) |
| `Controllers.Gui.Sports` | the HUD (kit Panel, Text, Bar and VerticalMeter only), input, dribble bounce and poses (PreSimulation), post-game card |
| `ServerStorage.Dialogue.CoachTemplate` + `Varga`, `Mallory`, `Dunmore` | coach trees |

- **Patched:**
  - `PlayerData` / `UpdateState` (`Sports`, `SetSports`)
  - `Config.Progression` (Sport EXP keys, `SportExp`)
  - `Config.Npcs` (coaches)
  - `Config.Quests` (`RavensTryout`), and `Quests` (`Drill` and `SportMatch` objective types)
  - `Students` (club tag)
  - The server `Crouch` and the client binds: M1, M2, Uppercut, Feint, Dodge, Block and Equip step aside while you hold a ball; M1 also in a game; no slide or crouch in sports.
- **TestBridge:** `JoinClub`, `ClubSheet`, `SportForce(venue, a, b, solo)`, `SportState`, `SportAction`, `SportEnd`, `SportClock`, `AwardExp`.
- **Tests:** `Studio/tests/sports_test.luau` (session tools), 60 pure checks: config, sanitize, ranks, launch solver, shot windows, make chances, points.

## Audit (Sports 1.0, 2026-10-30)
**How the end-to-end audit was run:**
- **Code review:** a reviewer read every sports module, and each finding was re-checked against the code.
- **Studio checks:**
  - Every installed module matches its source.
  - The venue contract and integration patches are present, and everything compiles.
  - 60 pure checks pass.
- **Live tests in Play:**
  - junk and spammed remote calls
  - leaving the court, being knocked out, and respawning
  - buzzer-beaters, drills, teleporting, rewards, the HUD, and touch and gamepad bindings

| Found | Fix |
|---|---|
| "Holding a ball" stayed set when a game or drill ended with the ball in hand, so you couldn't steal or block next game | Removing a ball releases it first |
| The client could report a perfect hold time | Hold time is measured only on the server |
| Spamming jump gave near-certain blocks | One block roll per jump, 0.9 s between jumps |
| Offensive rebounds reset the shot clock to 24 and forced a clear; a delayed catch reset it to 14 | Rebounds compare against the shooting team; only rebounds off a shot give 14 |
| Post-up always halved the contest | Needs a defender on your back and you nearly still |
| A bystander (or another driller) on a loose ball blocked pickups; a ball in the bleachers was never out | Only players in that game or drill can pick it up; a ball resting outside the lines is out; a dead ball returns to a check after 8 s |
| Reward farming: check balls counted as touches, forfeits paid wins, drills had no cooldown, cone teleports | Check balls don't count; forfeits pay no win or record; one rewarded game or drill every 3 minutes; cone speed and minimum-time checks |
| The venue HUD overwrote the drill HUD next to the court | Venue HUD goes only to its players and free bystanders |
| The dribble dash ignored the server (no stamina limit) | Dash runs when the server accepts the move |
| Made shots fell through the floor | Collision returns right under the rim |
| A respawn mid-game left a dead ball and stale state | A new character leaves the game; the held check follows the current character |
| Empty games ran forever (solo test) | An empty game ends |
| Smaller fixes | stamina flag cleared, half court turns full court when teams grow, drill prompt reach matches the server, no drills while downed or duelling, pass range checked for named targets, coach join failures handled, buzzer-beaters count |
| No phone or gamepad controls | Kit-art touch and gamepad buttons |

**Two-player test (local server, 2026-10-30):**
- **Steals:** they work, and a reach during a dribble move gets crossed up.
- **Half court:** the clear rule works, and check ball follows a score.
- **Blocks:** 3 of 4 blocked with a jump at the release.
- **Defender pressure:** shrinks the green window (same timing: green open, okay contested).
- **Offensive rebounds:** the shot clock resets to 14.
- **Rewards and forfeit:** a game to 21 paid both players, and a forfeit removed the walker after 5 s and ended the game.
- **Still open:** a real pass needs a 2v2.

### Soccer audit (Sports 1.1)
**How it was run:** a code review of every soccer module (14 findings, all fixed), then live tests in Play, including real key presses.

| Found | Fix |
|---|---|
| A "straight up" aim produced an invalid number that could fake a target hit or a goal | Every aim is made safe; invalid positions never count as inside a sensor; invalid ball speeds are refused |
| Players move their own characters, so a teleporter could shoot from inside the goal or reach the ball from anywhere | Server speed check each tick (75 studs/s): a teleporter loses the ball and can't act or touch it for 1.5 s; shots from inside a goal mouth or off the pitch are refused; drills check too |
| A tackler who won a loose ball still got the miss stun | Winning the ball ends the tackle window |
| Tackle and dribble timers survived a goal or halftime; a tying goal at the buzzer triggered two kickoffs | Timers reset at kickoff and halftime; a goal's kickoff is cancelled by halftime or overtime; the buzzer wait covers the celebration |
| Target Practice didn't feed the ball back after a hit | It feeds the ball back 2.5 s after any shot |
| Volleys didn't reset the dead-ball timer | Every kick resets it |
| A keeper's click volleyed instead of catching | The keeper catches on touch in their box |
| The kick charge could be spammed | One charge per hold |
| A stun restored sprint speed; a kick charge carried over between games | Stuns restore the default walk speed; the charge is cleared when you leave |
| Curve was keyboard-only | Steering left or right while charging curves on gamepad and touch |
| "Out of gas" showed to everyone; intercepted passes counted as assists | The message goes to the tired player only; interceptions clear the last pass |
| Stamina did nothing in either sport | Running out stops sprinting |
| Looping animation clips (the slide) kept playing | Every clip plays once and stops with its move |

## Goal and Bloodrush effects (1.9.0)
- **Goal:**
  - an upright team-colour flare in the goal mouth, three net rings and shards off both posts;
  - the pitch lights pulse once;
  - spectators within 150 studs see it.
  - **GoalCam:** re-entrant, and it eases back behind you.
- **Bloodrush aura:** drawn on each client from the character attribute `SportRush`. It shows race-colour embers and two wisp ribbons on the torso, and flickers out over the last 1.5 s. Colours come from `Lineage`.
