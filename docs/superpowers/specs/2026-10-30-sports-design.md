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
- **Roles each play:** QB (offence picks), receivers, defenders, one pass rusher (defence picks).
- **Huddle (8 s):** the offence chooses a play from a playbook card (6 plays: slant, go, post, curl, out, screen per receiver). The routes draw on the field for the offence only; the defence picks man or zone.
- **Snap:** the QB snaps with **Space**. The rusher waits for a 3 s count ("Mississippi") before rushing.
  - **Throwing:** the QB aims with the mouse and holds click for power; a lead marker shows on the target; Might adds range.
- **Receiving:** the catch window opens when the ball is within 6 studs. Click to catch (timing and contest decide); a dive (**Q**) extends reach and costs stamina; jukes (**E/R**) and spin (**F**) after the catch.
- **Defence:** tackle (**click**, contact range; ends the play); interception = defender catch; swat (a timed click deflection).
- **Rules:** a 60-yard field; 4 downs to gain 10 yards; touchdowns 6, with a simple extra point (1 automatic, or a 2-point try from the 5); turnover on downs; a field goal option on 4th down from inside 30 (a kick meter); two 4-minute halves.
- **Expanded over the reference:** playbook and route preview, defensive schemes, the rush count, field goals, and 2-point tries.
- **Drills:** *Route Runner* (catch from a throwing machine on chosen routes); *QB Targets* (moving rings).

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
