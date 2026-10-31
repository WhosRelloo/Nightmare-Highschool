# Sports Clubs

**Status:** Sports 1.0 is built in NH Combat Test. Basketball is fully playable: games from 1v1 to 5v5, two drills, the Night Ravens club and its tryout quest.
- The soccer pitch and the football field are built, and both coaches take members, but their rules come in 1.1 (soccer) and 1.2 (football). Their pads read "coming soon".
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
