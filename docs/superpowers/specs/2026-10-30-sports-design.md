# Sports Clubs: Basketball, Soccer, Football (design)

**Status:** approved design, not built. All numbers are tuning proposals kept in config.
**User brief (2026-10-30):** real sports systems for the clubs that integrate seamlessly with the game and are fully audited for bugs.
- References (play-style only, no copied content):
  - basketball like *Highschool Hoops* (dribble moves, post tech, dribble cancels)
  - soccer like a *Blue Lock*-style R6 system
  - football like *Football Fusion 2*, expanded
- Original art, names and builds.

## Decisions (from the user)
- Players only, plus solo drills (no NPC teammates).
- Both pickup games and club membership with ranked club matches.
- Skill-based and grounded, plus one small race perk each.
- Fighting is allowed during matches; getting downed takes you out of the match.
- A gymnasium and two separate fields; teams from 1v1 to 5v5 (football from 2v2).

## 1. Clubs
| Club | Sport | Venue | Coach NPC |
|---|---|---|---|
| **Night Ravens** | Basketball | Gymnasium | Coach Varga |
| **Grave Rovers** | Soccer | Pitch | Coach Mallory |
| **Iron Wardens** | Football | Field | Coach Dunmore |

- **Joining:** talk to the coach. One sports club at a time, independent of factions. Leaving costs nothing; rejoining another club resets club rank.
- **Club EXP and ranks:** Rookie (0) → Starter (150) → Varsity (500) → Captain (1200).
  - EXP sources: drills (5–20), matches (played 25, won +25), MVP +15.
  - Captain gets a title ("Ravens Captain"…). Your club tag shows in the Students list and on known nameplates.
- **Ranked club matches:** after school (from 12:00 to 20:00 in-game). A match counts as ranked when at least one club member of that sport plays.
  - The win/loss record is kept on the club member.
- **Pickup:** anytime, anyone; same rules, no club EXP for non-members.
- **Rewards:** progression EXP with a new **Sport** category (+ `SportExp` effect key), yen, and popularity (Reputation).
- **Saving:** `PlayerData.Sports = { Club, ClubExp, Record = { [sport] = { W, L } }, Drills = { best scores } }` via action `SetSports`; server-only writes.

## 2. Shared match core (`Services.Sports.*`)
- **Venue contract:** found by attribute, like quests.
  - `SportVenue = <sport>`, `SportPad = "A" | "B"`, `SportBall` spawn, `SportGoal = "A" | "B"` (hoop / goal / end zone)
  - `SportBounds` (playing area), `SportDrill = <id>`, plus scoreboard SurfaceGuis
- **Queue:** stand on a team pad.
  - **Start:** when each side has the minimum (basketball and soccer 1, football 2), a 10 s countdown starts; later arrivals fill open slots up to 5v5.
  - Teams are rebalanced at start (sizes differ by at most 1).
  - **Leaving:** step off the pads before the start, or walk out of `SportBounds` for 5 s during a match.
- **States:** Waiting → Countdown → Live (with sport phases) → Halftime → Live → End (summary and rewards) → Waiting.
  - Overtime on a tie: next score wins, with a 2-minute cap, then a tie.
- **Ball:**
  - **Physics and possession:** one physics ball per venue; the server sets network ownership to the possessor (or the server when loose).
  - **Holding:** a possessed ball is welded to the carrier, in hand for basketball and football, at the feet for soccer.
  - **Releases** (shot, pass, kick, throw) are requested by the client with direction and power; the server checks possession, the cooldown and the power cap (from stats), then applies the impulse.
  - **Pickup:** a loose ball is picked up by touch, within 3.5 studs of the ball, server-checked.
- **Fighting:** allowed.
  - Downed (Downed.OnDowned) → removed from the match, ball dropped; can rejoin an open slot after recovering.
  - Discipline still applies as normal.
- **Stats:** Might +0.3%/point shot, kick and throw power; Grit +0.5%/point stamina and tackle resistance; Wits +0.4%/point timing window.
- **Race perks (sports only):**

  | Race | Perk |
  |---|---|
  | Vampire | +6% shot/kick accuracy at night |
  | Werewolf | +15% sprint stamina on full-moon nights |
  | Ghoul | −15% chance to be stripped or tackled |
  | Wraith | +8% steal and intercept reach |
  | Human | +12% stamina regen |
  | Priest | +6% pass accuracy |

- **Stamina:** sprinting, dribble moves and dives spend stamina; it shows as a thin HUD bar during matches.
- **Display:** scoreboard and clock on the venue board and a HUD bar; a post-game card (score, MVP, rewards).
- **Integration:**
  - compass markers for the venues
  - the Students list shows your club
  - a short "Tryouts" side quest per club (meet the coach, finish a drill, play one match)
  - the shift-lock cursor and Ctrl crouch are unaffected (crouch is disabled in matches)

## 3. Basketball (Gymnasium, full court; 1v1 uses a half court)
- **Controls:** **left click hold/release** to shoot (timing meter), **E** pass to the teammate you're facing, and dribble moves on **Q** (crossover), **R** (behind-the-back), **F** (spin), **C** (between-the-legs).
  - Moves chain within 0.35 s; pressing another move during the first 0.2 s cancels into it (the *dribble cancel*).
  - **Post up:** hold **G** with your back to a defender within 4 studs to back down slowly; click for a post fade, or Q for a hook.
- **Shooting:**
  - the green window shrinks with defender closeness (contest) and distance
  - layup inside 6 studs while moving; dunk inside 4 studs with Might ≥ 10 or a running start
  - 3 points beyond the arc
- **Defence:** steal (**click** while not holding the ball; reach 4 studs, a 1.2 s cooldown, a foul on a whiff into the body); block (jump-timed within 3 studs of the shot); rebounds go to touch.
- **Rules:** 24 s shot clock; first to 21 (2s and 3s) or two 4-minute halves; check ball at the top after a score; make-it-take-it off.
- **Drills:** *Shootaround* (10 spots, timed, score); *Cone Dribble* (move-chain course, time).

## 4. Soccer (Pitch)
- **Controls:** the ball stays at your feet while you move with it; **Shift** sprint; **E** ground pass; **R** lofted pass; **left click** hold/release to shoot (power meter, curve from the mouse offset); **F** standing tackle; **C** slide tackle (stamina; a foul if it hits the body without the ball first).
- **Goalkeeper:** at 3v3 and up, one player per side opts in on the keeper pad. They catch inside the box (no carry limit, 6 s hold) and dive on **Q/E**.
- **Rules:** kickoff; out of bounds gives a throw-in, a corner or a goal kick (simplified: the ball is placed, and the nearest opponent takes it); two 4-minute halves; no offside.
- **Drills:** *Target Practice* (hit corner targets, power and curve); *Wall Passes* (one-touch timing).

## 5. Football (Field; 2v2 to 5v5)
**Style (owner, 2026-11-03):** play like *Football Fusion 2*: freeform pickup football with manual throwing, catching and tackling and a full kicking game, plus an optional quick play call borrowed from *NFL Universe Football*. Original code, names and art; every number below is a tuning proposal kept in `Config.Sports.Football`.

**The field:** 60 yards between the goal lines at 2 studs per yard (x −154 to −34), 8-yard end zones, 32 yards wide (z −190 to −126), goalposts at both ends.

**A play, start to finish**
1. **Huddle (6 s, optional):** the offence's QB can press **1–6** to call a play (Slants, Verticals, Posts, Curls, Outs, Screen). The routes draw on the field for the offence only. The defence can press **1** (man) or **2** (zone) to show each defender a coverage hint. Nobody has to call anything: when the huddle ends, the play is freeform.
   - On 4th down the huddle also offers **P** (punt) and, inside 30 yards of the goal line, **K** (field goal).
2. **Line up:** both sides are placed at the line of scrimmage: the QB 4 yards behind the ball, receivers spread across the field, defenders 5 yards off. Players can move before the snap, but nobody may cross the line.
3. **The snap:** the QB presses **Space** within a 20 s play clock (late: delay of game, −5 yards). The QB is whoever stands closest to the ball when the huddle ends.
4. **The rush count:** after the snap, a "1 Mississippi, 2 Mississippi, 3 Mississippi" count shows. Until it ends, defenders can't cross the line (a wall only defenders collide with). A throw, a handoff or the QB crossing the line ends the count early.
5. **The play ends** on a tackle, a carrier leaving the field, a touchdown, a kneel, a safety, or an incomplete pass (the ball touches the ground uncaught). The ball is spotted where the play ended.

**Controls**
| Who | Key | Action |
|---|---|---|
| QB | **aim with the mouse, hold click, release** | Throw toward the aim point. Holding charges power (0–100 over 1.2 s); power sets speed and range, so an under-charged deep throw falls short. Might adds range. A lead marker shows where the ball will land. |
| QB | **F** | Pump fake (the arm motion, no ball) |
| QB | **G** | Hand off to the teammate closest to you within 6 studs (behind the line only) |
| QB | — | Can run. Past the line, the QB can't throw forward any more. |
| Anyone | **click** (ball in the air) | Catch: works within the catch radius (5 studs from your hands; Wits widens it). If several players try, the closest with the best timing wins. Spamming adds a 0.6 s cooldown. A defender's catch is an interception. |
| Anyone | **Space** | Jump: a jump catch reaches higher |
| Anyone | **Q** | Dive: a 10-stud lunge, +2 studs of catch radius in the air, then 0.8 s on the ground. Costs 20 stamina. |
| Carrier | **E / R** | Juke left / right (a 6-stud side step with a 0.25 s tackle-break window, 1.2 s cooldown, stamina) |
| Carrier | **F** | Spin (same break window, 1.5 s cooldown) |
| Carrier | **K** | Kneel: down where you stand |
| Defender | **touch** | Tackle: touching the carrier downs them |
| Defender | **R** | Hit stick: a 6-stud lunge. A hit tackles with a 25% fumble chance; a miss stumbles you for 1 s. |
| Defender | **C** | Swat: knocks a ball within 6 studs to the ground (always incomplete) |
| Returner | **V** | Fair catch on a kick (no return; the ball is spotted where it's caught) |

**Kicks**
- **Kickoff** at the start of each half and after every score: the kicker (the kicking side's player closest to the tee) holds and releases click on a **kick meter** (power, plus accuracy from the release timing). A kick into the end zone that isn't returned is a touchback at the 12.
  - **Onside:** the kicker presses **O** first for a short kick. Either side can recover it once it's travelled 5 yards.
- **Punt:** on 4th down, from the huddle. Same kick meter.
- **Field goal:** on 4th down inside 30 yards of the goal line. The kick meter, and it's good if the ball passes between the uprights above the crossbar: 3 points.

**Scoring and rules**
- Touchdown 6. Then the scorer's side picks: **1** for the extra point (automatic, 1 point) or **2** for a 2-point try from the 5.
- Safety (the carrier is downed in their own end zone): 2 points, and the other side gets the ball.
- 4 downs to gain 10 yards, or the ball turns over on downs. A fumble is loose: anyone can recover it.
- Two 4-minute halves. The clock runs only while the ball is live. A tie goes to the shared overtime (next score wins, 2-minute cap).
- Penalties: false start and delay of game (−5 yards, replay the down).

**Race perks** (the shared table): Vampire throw accuracy at night, Werewolf sprint stamina on full-moon nights, Ghoul 15% chance to shrug off a touch tackle, Wraith +8% catch and swat reach, Human stamina regen, Priest +6% throw accuracy.

**Drills:** *Route Runner* (a throwing machine throws to you on a chosen route; score catches) and *QB Targets* (throw through moving rings downfield; score points).
**Tryout:** *Iron Wardens Tryout* from Coach Dunmore: pass a drill, then play one match.
**Testing solo:** a Studio-only test mode lowers the minimum to one player and can add a test defender (a dummy that chases the carrier), so tackles, kicks and drills can be tested without a second player. Real games are players only.

## 6. Venues (built in Studio)
- **Gymnasium:** gothic stone and dark-wood hall, a full court with lines, two hoops (backboard, rim, net), bleachers, hanging lights and a scoreboard.
- **Pitch:** grass with chalk lines, goals with nets, low walls, lights and a scoreboard.
- **Field:** turf with yard lines and numbers, end zones, goalposts, bleachers, lights and a scoreboard.
- **Placement:** open ground near the school, reachable on foot, with compass markers.

## 7. Bug audit (required by the user)
- Per sport: pure tests for the rules (scoring, clocks, downs, shot clock); network edge cases (possession steal races, the ball leaving the bounds, players leaving mid-play, downed mid-shot); exploit checks (spammed remotes, impossible power and direction, teleport pickups).
- Code review of all sports modules by a reviewer agent.
- Solo playtests of every drill and the queue flow; a two-player test of matches (the user's planned two-player pass).

## Build order
1. **Sports 1.0:** clubs, the shared core, all three venues, basketball and its drills.
2. **Sports 1.1:** soccer.
3. **Sports 1.2:** football.
4. **Sports 1.3:** the full audit and fixes; then the two-player test (bite + matches).
