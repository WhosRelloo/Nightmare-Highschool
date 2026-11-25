# Soccer 2 concept: Grave Rovers, after dark

Status: concept for the owner (2026-11-24). It isn't a spec yet. It builds on Soccer 1.1 (`docs/Sports.md`, "Soccer").
Two inputs: a study of the most-played Roblox soccer games (from their videos), and the 24 soccer clips in the
"FIER ANIMATIONS" place. Only mechanics and feel were studied. No code, art, names or characters are taken from any
game.

## 1. What the top games do (from the videos)

### The games
In November 2026 the most-played Roblox soccer games are:
- FIFA Super Soccer (formerly Super League Soccer);
- Realistic Street Soccer;
- Blue Lock: Rivals;
- Illegal Soccer, which launched in May 2026 with a record of about 81k players at once;
- TPS Street Soccer / TPS Ultimate Soccer;
- Touch Football.

They fall into three camps.

| Camp | Games | Hook |
|---|---|---|
| **Simple controls, deep physics** | FIFA Super Soccer, Realistic Street Soccer, TPS, Touch Football | 3-6 actions, but the skill cap comes from the ball: light taps, walls, lobs, timing. Ranked on mobile and in leagues. |
| **Anime abilities** | Blue Lock: Rivals | Styles with 2-3 skill keys (C / V / B), a Flow / Awaken meter, cinematic signature shots. |
| **Party with items** | Illegal Soccer | Pick-up items (grappling hook, barricades, magnet, oil spill, supercharge…), an item-ban vote before each match, wild arenas, ranked placements. |

A ranking creator's verdict on powers is worth keeping: powers are "the worst part" of an otherwise great game, and the
competitive games stay power-free. **Lesson: keep the ranked game clean, and put powers in a separate mode.**

### Controls almost everyone agrees on (PC)

| Input | Action |
|---|---|
| LMB (hold) | Shoot or cross, charged |
| RMB | Pass or low shot |
| Q | Dribble or skill move, with a short window where you can't be tackled. Q while strafing is a side dribble with a speed boost. |
| E | Tackle (a slide) |
| R | Call for the ball |
| Shift | Sprint, with a stamina bar |
| C / Ctrl | Lock the camera (shift lock) |
| T (hold) | Taunt wheel |
| X | Emote |
| Tab | Leaderboard |

Mobile gets the same 4-5 buttons. Every game shows the controls on screen in a corner.

### Skill moves the players actually use

**Camera pitch is a control.**
- Look down and kick: you keep the ball (a feint, or "spam dribble" close control).
- Look down a little less: a "balloon", an air dribble nobody can steal.
- Look up: the shot rises.

**Shots and headers by input order** (FIFA Super Soccer):
- jump, then hold shoot: header;
- jump, then hold pass: power volley;
- hold, then jump: bicycle kick;
- tap the high shot: chip.

**Close control and walls:**
- **Light-tap close control:** tiny touches keep the ball almost stuck to your feet.
- **Wall dribble and wall pass:** on walled pitches, bounce the ball off the boards to beat a defender. You can't be
  tackled while the ball is off you.

**Defending:**
- **Perfect tackle ("perp"):** tackle the instant the ball reaches the receiver.
- **Air snatch / trap:** a tapped header catches a high ball dead instead of bouncing off.
- Baiting a tackle into the dribble window works on every defence.

### The extras that make a goal feel big
- **Points for each action** float up as they happen ("Tackle Evaded +54", "Tackled Player +25", "+Pass",
  "+Volley", "+Goalkeeping", "Last-Minute Equalizer +200").
- **The goal banner** shows the scorer, the assister and the distance ("From 4 meters"). The scorer's stat card flies
  in (goals, saves, MVPs, assists).
- **Replay** of the goal (a "REC" camera frame), a celebration picker, and a team walkout tunnel with kit or keeper
  choice.
- **End-of-match awards:** MVP, Playmaker, Guardian Angel, Box to Box, Striker, Bully, Item Addict, Loot Goblin.
  Everyone gets something.
- **Rules:** a mercy rule, golden goal, a referee calling a penalty, and 10 placement matches leading to a tier.

## 2. Where Soccer 1.1 already stands

**We already have** most of the core:
- a charged shot with late curve;
- pass and call (R);
- a dribble burst with ankle breaks (Q), a feint that counters a tackle (RMB) and a tackle with a steal window (E);
- a keeper with a dive and throw;
- Bloodrush, our version of Flow / Awaken, with race auras;
- stamina, ball-only walls (so the pitch already plays like a street pitch), the mercy rule, golden goal, a goal
  close-up, race perks, drills, club ranks and a tryout.

**The gaps** compared with the top games:
1. **Animation:** kick, charge, pass, volley, header, dribble, feint, the ankle-break fall and the keeper dive are
   **procedural poses** (no clip existed). This is the biggest feel gap.
2. **Ball-control depth:** there's no camera-pitch touch, chip or air trap. Volley and header share one window.
3. **Defence:** no perfect-tackle reward, no fouls, no penalty.
4. **Feedback:** no action points, a thin goal banner, no awards and no replay.
5. **Modes:** only one, the clean game. There's nothing for players who want chaos.

## 3. The FIER ANIMATIONS soccer clips

`Workspace."Soccer Anims".AnimSaves` holds 24 KeyframeSequences on the regular non-bending R6 rig.

| Clip | Used for | Replaces |
|---|---|---|
| Kick Soccerball_R6 | The standing or charged shot | Procedural kick |
| Strike Foward Jog_R6 | The running shot (shooting on the move) | Procedural kick |
| Soccer Pass_R6 | Pass (R) | Procedural pass |
| Chip_R6 | **New:** chip or lob (tap the shot while looking up) | none |
| Scissor Kick_R6 | Volley and bicycle kick (the air strike) | Procedural volley |
| Soccer Penalty Kick_R6 | **New:** penalty and shootout kicks | none |
| Soccer Spin_R6 | Dribble move (Q while strafing) | Procedural dribble or feint |
| Stall Soccerball_R6 | **New:** a sole-stop or stall (look down + kick, or hold Q) to shield and bait a tackle | none |
| Soccer Tackle_R6 | Tackle (E) | Group "SLIDING" clip |
| Soccer Tackled_R6, Soccer Tackled2_R6 | Being tackled (two variants, picked at random) | Procedural fall |
| Soccer Trip_R6 | Ankle break or foul trip | Procedural fall |
| Fallen Idle_R6 | Lying down during the ragdoll or downed time | none |
| Soccer Idle_R6, Offensive Idle_R6 | Match idle without and with the ball (also kick-off and walkout) | Default idle |
| Jog Forward_R6, Jog Backward_R6 | The in-match jog, and the backpedal while defending | Default walk (approved, question 1) |
| Goalkeeper Idle_R6, Goalkeeper StepLeft_R6, Goalkeeper StepRight_R6 | Keeper set stance and sideways shuffle in the box | none |
| Goalkeeper Diving SaveLeft_R6, Goalkeeper Diving SaveRigh_R6 | The keeper's dive, by side | Procedural dive |
| Goalkeeper Catch_R6, Goalkeeper CatchIdle_R6 | Catch and hold (the 6 s hold) | none |

**Still without a clip:**
- the header (keep the procedural pose, or author one in the owner's style);
- the keeper throw (keep "Activate");
- the goal celebration (keep "Isagi Celebration", or add a celebration picker later).

**Before the clips go in:**
1. **Upload.** The clips are local KeyframeSequences, so the owner publishes them to the group to get asset ids
   (`docs/Pipeline-Lessons.md`).
2. **Measure each one:** its length, and the **contact frame**. Add a `Contact` KeyframeMarker so the server's ball
   kick lands on the frame the foot meets the ball, instead of on a fixed delay.
3. **Audit against the house style:** the `r6-animation-cinematics` gates (moving fraction, no frozen or duplicated
   frames, no foot skate). Fix any clip that fails before wiring it in.

## 4. The concept: Soccer 2, "Grave Rovers, after dark"

**One idea:** a clean, skill-first game in the "simple controls, deep physics" camp, which is the biggest audience
and plays well on mobile. On top of it go the extras that make goals feel huge, and a separate cursed night mode for
the party crowd. The horror flavour lives in presentation, Bloodrush and the night mode, never in the ranked rules.

### 2.0: Real animation (the FIER clips)
- Wire all 24 clips (section 3), driven by the `Contact` markers.
- Kick speed and power stay on the server, so the clip only sells it.
- The goal cut follows the house style: a hard cut on the shot's contact frame to a low, dutch angle, then a push-in
  through a moving hold, then the scorer's close-up.

### 2.1: Touch and air
**Camera-pitch touches:**
- Look down + click: a stall or close touch (Stall clip). You keep the ball, and it works as a feint.
- Slightly down: a flick-up for an air dribble.
- Look up: lift.

**Air moves:**
- Header: jump, then click.
- Volley / bicycle kick: click, then jump (Scissor Kick).
- Chip: tap click while looking up (Chip).
- **Air trap:** a tapped header kills a high ball to your feet.

**Close control and walls:**
- **Light-tap dribble:** a short tap moves the ball 3-4 studs ahead, so it stays close.
- **Wall play,** made official: a pass or dribble off the ball-only walls counts as an assist chain, and "Wall Pass"
  shows as an action.

### 2.2: Fouls and penalties
- **Clean Tackle:** a tackle within 0.15 s of the ball reaching the target earns bonus Bloodrush and an action
  pop-up.
- **Fouls:** a slide from behind, or tackling a player already down, is a foul. Coach Mallory acts as referee and
  blows the whistle. A foul in the box is a **penalty**.
- **The penalty:**
  - The kicker aims with the camera and kicks with the Penalty Kick clip.
  - The keeper picks left, centre or right at the moment of the kick, and dives with the Diving Save clips.
- **Shootout:** decides a tied tryout or cup game; it replaces golden goal in cup games only.
- **New drill: Spot Kicks.** Five penalties against an NPC keeper, pass with 3.

### 2.3: Feedback and awards
- **Action points** float up: Clean Tackle, Tackle Evaded, Wall Pass, Chip, Header, Save, Assist,
  Last-Minute Equalizer.
- **Goal banner:** the scorer, the assister and the distance in studs or metres, plus the scorer's club rank card.
- **Instant replay:** the last 4 s of a goal, from a low tracking camera.
- **End-of-match awards:**
  - MVP;
  - Playmaker (assists);
  - Brick Wall (saves);
  - Ankle Taker (ankle breaks);
  - Engine (distance run);
  - Grave Digger (clean tackles).

  Each pays a little club EXP, and the post-game card lists them.
- **Celebration wheel:** owned celebrations, with the clean default kept. T is Bloodrush, so the wheel uses **G**
  (hold).

### 2.4: Night Match, the cursed mode (unranked)
- Starts after 20:00 in-game time from its own pad. The floodlights flicker, and fog rolls in.
- **Curses** to pick up:
  - **Grave Hands:** a patch that roots players.
  - **Fog Bank:** blinds an area.
  - **Bat Swarm:** steals the ball off the target.
  - **Blood Moon Boot:** one super shot.
  - **Coffin Wall:** a short barricade.
  - **Hex Magnet:** pulls the ball.
- **Ban vote:** each team bans one curse before the match.
- **No ranked record** and no club ranked EXP. Rewards are yen, popularity and a "Night Match" award.

### 2.5: Bloodrush signatures
- At a full meter, each race gets one signature move. It can replace the flat +10% shot power.
- Ideas:
  - **Vampire:** a blood-trail curler.
  - **Wraith:** a phase dribble, passing through one tackle.
  - **Ghoul:** a shoulder barge that wins a 50/50.
  - **Werewolf:** a pounce volley.
  - **Priest:** a pass that blesses the receiver's next shot.
  - **Human:** a second wind.
- Each fires with a 0.6-1.0 s cinematic flash, never a long cutscene. Play doesn't stop for it.
- Ranked can keep or drop these (question 2).

### Later (not planned)
- An inter-club **Rivalry Cup** week, using the walkout tunnel, the shootout and a crowd of NPC students (the 2.15
  crowds).
- **Placements** for a school-wide soccer tier.

## 5. Questions for the owner
1. **Movement clips: decided (owner, 2026-11-24).** Yes. During a match, the FIER jogs (forward and backward) and
   idles (Soccer, Offensive, Goalkeeper) replace the default walk and idle. This lifts 1.1's "no movement clips except
   the slide" rule for soccer matches.
2. **Ranked powers.** Should the Bloodrush signatures (2.5) count in ranked games, or only in pickup and Night Match?
   (The top competitive games ban powers.)
3. **Order.** I'd go 2.0 → 2.1 → 2.3 → 2.2 → 2.4 → 2.5: feel first, then extras, then rules, then modes.
4. **Upload.** The FIER clips need publishing to the group before anything can use them in the game. Will you
   publish them, or should they be rebuilt from local KeyframeSequences in NH Combat Test for testing?

## Sources (videos studied with /watch-video, 2026-11-24)
- [Top 10 BEST Roblox Soccer Games in 2026](https://www.youtube.com/watch?v=BdPlkg2F9W8)
- [20 Useful TECHS in Blue Lock Rivals](https://www.youtube.com/watch?v=jsWDHQ6X098)
- [NOOB to WORLD CLASS in Illegal Soccer](https://www.youtube.com/watch?v=z0cIdHolesk)
- [BEST Skills and Dribbling in Realistic Street Soccer](https://www.youtube.com/watch?v=vHFj6nzXPGk) (frames only, no captions)
- [How to become a PRO in FIFA Super Soccer](https://www.youtube.com/watch?v=P2TevG0ts8Y)
- [Scoring a hat-trick in every Roblox soccer game](https://www.youtube.com/watch?v=Yp068cjgF9I)
- Player counts: [rblxdb sports](https://rblxdb.com/games/genre/sports), [Robipedia soccer](https://robipedia.com/tag/soccer)
