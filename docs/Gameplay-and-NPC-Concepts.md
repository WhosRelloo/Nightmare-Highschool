# Gameplay and NPC concepts, after a Bully study (2026-11-12)

Owner: "let's make concepts on ways to enhance gameplay and the NPC's, including their immersiveness". Before
writing these, the owner asked for a full study of a Bully: Scholarship Edition longplay (YouTube `nAIHZ5gqnps`,
9 h 26 min, 84 chapters), the game Nightmare Highschool takes after.

**How the video was studied**
- **The dialogue:** the whole transcript, 2,467 dialogue captions read from start to end. It's a no-commentary run,
  so the captions are the game's own lines.
- **The screen:** about 45 frames sampled across every part of the run (free roam, all the class types, the
  holidays, the town, the clique missions and the finale).
- **We copy patterns, never content:** no characters, names, lines, places or story from Bully. Everything below
  is in NH's own world (races, moons, beasts, the Midnight Bell).

These build on what NH already has (`docs/Implementation-Status.md`), and especially on what the students
already do:
- the NPC brain with Nav, Senses, reactions, voices and fidgets (1.86.2);
- the nudges (1.86.3 to 1.86.7);
- `docs/NPC-Immersion-Ideas.md` (2026-11-10), whose voices and fidgets are done.

Sizes: **S** is a day or less, **M** a few days, **L** a week or more.

---

## What makes Bully's school feel alive (what the study found)

1. **Every line says who's talking and how they feel about you.** Ambient lines are keyed by clique, by attitude
   to the player and by the moment. You can tell a clique from its slang without seeing the speaker.
2. **Students judge your clothes.** Remarks about the player's outfit are the most common ambient line in the
   whole run, good and bad, slot by slot (the shoes, the shirt). Cliques have dress codes that open or shut doors.
3. **Your reputation arrives before you do.** Students who never saw a fight have heard about it. A rival's lies
   about you circulate, and a beaten champion's crowd announces the new one.
4. **Authority talks before it acts.** It escalates in steps:
   - a friend's warning;
   - a staff remark that fits the time and place ("shouldn't you be in class?", "it's curfew");
   - a threat to write you up;
   - "Stop!" and a chase;
   - a bust line;
   - the PA calling your name to the office.
5. **Crowds make fights matter.** At a fight or a duel, bystanders do all of this:
   - chant;
   - take bets;
   - comment on how hurt the fighters are;
   - beg them to stop;
   - say they're glad it isn't them.
6. **Classes have a teacher's voice.** Each one has a rule line, encouragement as you play, graded verdicts, and
   an early release for doing well. Classmates mutter about themselves. Class skills come back in the story (the
   rhythm game becomes the holiday pageant).
7. **Small favours, haggled.** NPCs bring petty problems with absurdly high stakes. The player pushes back ("what's
   in it for me?"), they settle on a small payment, and it ends in grudging thanks.
8. **Cliques are conquered, then they turn.** Each clique has:
   - a challenge in its own idiom (boxing, an arcade high score, dodgeball);
   - a turf handover;
   - greetings that flip from hostile to friendly.

   Late on, everything collapses (every clique blames you) and you win it back.
9. **The year moves.** Halloween night (staff away at a party, costumes, scaring), winter snow, Christmas jobs and
   the pageant, the carnival and dates. The look of the whole map changes with the season.
10. **Adults have their own stories.** Feuding teachers and a lunch lady's crush play out where students can see
    and gossip about them. The PA runs all day.

**On screen:**
- **A clock is always up** (school time drives everything), with a minimap carrying named targets.
- **Objectives** show as one centred line, with counters (0/6, 11/20) for collection tasks.
- **One lock-on drives the social verbs:** greet, taunt, give a gift, kiss. A ring shows under the person you're
  locked on to.
- **Beaten students stay down** on the ground for a while.
- **Disguises and outfits are tools:** a mascot suit, a clique's look.
- **The camera is a tool too:** photographs are evidence.
- **Night infiltration:** you climb into dorms by the drainpipes.
- **The commons has playable arcade machines.**

**Things to avoid** (Roblox moderation and NH's rules):
- Bully leans on innuendo, slurs, cruelty to vagrants and the mentally ill, and eating-disorder gossip. None of
  that is needed here.
- No blood, ever (the owner's standing rule).

---

## Part 1: making the students feel alive

### 1. The line matrix (M)
- **What:** every student line is keyed by:
  - **clique**, so each clique has its own slang;
  - **attitude to you**: hostile, wary, neutral, friendly or loyal, from clique standing and the student's memory
    of you;
  - **context**: greet, bumped (the nudges), shoved, sees a fight, sees you break a rule, your outfit, curfew,
    night and the moon, your race, a holiday, you transformed, you're hurt.
- **Why:** it's lesson 1. Today `Lines.luau` keys mostly by context and personality.
- **Built on:**
  - `StudentBrain.Lines` and `MapStudents.Lines`;
  - `Config.Cliques` (which already has reaction lines by standing);
  - the voice blips;
  - `Nudges`, whose bumps get their own lines ("Watch it!", "Sorry, my fault").
- **New:** a `Lines.Pick(S, Context, Attitude)` that falls back from clique to generic, and the writing (roughly 8
  cliques × 5 attitudes × 12 contexts, a few lines each).

### 2. Students notice what you wear (M)
- **What:**
  - Students remark on specific pieces you wear, approving or teasing, by clique taste. The Choir likes the falling
    ruff, the Athletes mock the grimoire.
  - The full clique look (the Wardrobe's one-click look) earns a "you're one of us" from that clique and suspicion
    from its rivals.
  - The hall monitor remarks when you're out of uniform during class periods.
  - Some clique spaces won't let you hang out until you're dressed the part.
- **Built on:** `UI.Appearance` and `Config.Accessories` (each piece already has a name and a kit), `Config.Cliques`
  and its looks, and `School.HallMonitor`.
- **New:** a taste table per clique (likes and dislikes by accessory, kit or colour), an outfit context for the line
  matrix, and a dress-code check on chosen spots.

### 3. The rumour mill (M-L)
- **What:**
  1. Notable things you do become rumours: beating a leader, a showdown, a prank, a beast kill, being seen
     transformed, detention.
  2. A rumour starts with the students who saw it and spreads student to student as they meet (a chance per chat).
  3. It reaches the Midnight Bell after a day.
  4. Students who heard it react to you ("You're the one who…"), even if they never saw it.
  5. A rival clique can plant a false rumour that lowers your standing with a third clique until you disprove it:
     catch the liar, photograph the proof, or ask Sable.
- **Built on:**
  - **Senses:** who saw it, through their witness view.
  - `Social.Superlatives` and the Midnight Bell board.
  - **The phone:** the Gazette and Texts apps.
  - **Discipline witnesses.**
  - **`Features.Fortune`:** Sable already hints at "rumbles" and "dares".
- **New:** a server rumour list (subject, kind, truth, carriers, age), spreading as students chat, and rumour lines
  in the matrix.

### 4. They remember you, by name (M)
*(Carried over from the 2026-11-10 list, still the top ask.)*
- **What:**
  - Press G to introduce yourself. The student tells you their name, and it shows from then on.
  - Saved relationships per student: greeting a friend by name, cold-shouldering someone they dislike, flinching
    from someone who beat them up.
  - They remember the favours you did and the fights you started.
- **Built on:** `Social.Strangers`, `Social.Relationships` (already in PlayerData) and the brain's in-memory `memo`.
- **New:** a fixed roster of named students per place (names, cliques, faces, so they persist), and saving `memo`
  into the relationship.

### 5. Crowds at fights and duels (M)
- **What:** when students gawk at a fight, they form a ring at a safe distance instead of standing scattered. They:
  - chant;
  - shout bets ("Ten yen says the wolf wins");
  - call the state of the fight ("He's still standing?!");
  - beg them to stop (the shy ones);
  - say they're glad it isn't them;
  - hold their phones up to record. The clip becomes a rumour (concept 3) and a Midnight Bell item.

  People pushing through the ring get nudged.
- **Built on:** the brain's Gawk reaction, `Social.CliqueFights` and the rumbles, the nudges, the phone model the
  students already hold, and the duels.
- **New:** ring slots around the fight centre, crowd lines, and a "recorded" flag on the rumour.

### 6. Students live by the clock (S-M)
- **What:**
  - Late students run at the bell.
  - At curfew a rush heads for the dorms, the stragglers glance at the moon, and on a full moon or a new moon
    they're scared to be out.
  - Lunch has a queue at the concession stand.
  - On rain nights students carry umbrellas, and at night lanterns (the QOL kit's own models).
  - On a crimson or blue moon they gather and point at the sky.
- **Built on:** `School.SchoolClock`, `Features.Schedules`, `Features.MoonPhases`, `Config.Kit` (the umbrella and
  lantern models and holds), and the rain nights.
- **New:** clock- and weather-driven activities for the brain, and students holding kit items.

### 7. Staff with lives of their own (M)
- **What:**
  - **Teachers have small running stories** that students see and gossip about: two teachers feuding, a teacher's
    secret, the night janitor who knows too much. Some become quests (concept 11).
  - **The PA speaks through the day:** the bells, rule reminders, a lost-and-found notice. It **calls a player by
    name** to the office when they're wanted.
  - **The hall monitor has a voice ladder** (concept 9).
- **Built on:** `School.HallMonitor`, the substitutes (`School.Substitutes` already has four characters with rules),
  `Features.Phone`, and `Gui.ClockHud` for the PA's text.
- **New:** a PA announcer (text line plus a chime), staff lines in the matrix, and two or three staff mini-arcs.

### 8. Little scenes the school stages (M)
*(From the 2026-11-10 list.)*
- **What:** every few minutes near players, the school stages a short scene. Each one ends with the students
  remembering what you did, and it feeds the rumour mill.
  - a bully pushes a first-year against a locker;
  - someone drops a stack of books;
  - two friends argue;
  - a lost first-year asks for the library;
  - a student crying on the steps.
- **Built on:** the brain (a "scene" job a host can give two or three students), the nudges (the shove clip), and
  `Social.CliqueFights`.
- **New:** a scene director (cooldowns, only near players, never during class), and 6 to 10 scenes.

---

## Part 2: gameplay

### 9. The authority ladder, spoken, with a chase (M-L)
- **What:** NH has the discipline ladder, witnesses, the hall monitor and detention, but they act silently. The
  ladder would speak and escalate:
  1. a friend warns you ("Monitor's coming, act normal");
  2. the monitor remarks to fit the time and place ("Shouldn't you be in Chemistry?", "Curfew, back to your dorm");
  3. a write-up threat;
  4. "Stop!" and a chase;
  5. if caught, a bust line and the walk to detention;
  6. if you escape, the PA calls you to the office (concept 7), and the monitor knows your face until it fades.
- **Hiding during a chase:** lockers, bushes, toilet stalls, and **blending into a crowd of students**. That last
  one is where the nudges and the crowd work pay off: walk with a group and the monitor loses you.
- **Built on:** `Config.Discipline`, `School.HallMonitor` (`Respond`), witnesses, `School.Detention`, and Nav
  (which the monitor could share).
- **New:** monitor lines, a chase state with line-of-sight and a "last seen" search ("I know you're out here…"),
  hiding spots tagged `NHHide`, crowd blending (inside a moving group of three or more), and the PA summons.

### 10. Curfew nights (L)
- **What:**
  - **After curfew, campus becomes the supernatural game:** monitors patrol with lanterns, and beasts hunt in their
    lairs.
  - **Students sneak out** by climbing the drainpipes and dorm windows (the vault can climb, and the window kit
    exists) to:
    - meet a clique;
    - pull a prank;
    - visit the Ink Studio's seer;
    - hunt a beast for its trophy.
  - **Getting back in unseen matters.**
  - **The moon sets the night:** a full moon means more beasts and fewer monitors (they're scared too); a new moon
    means darkness that helps stealth.
- **Built on:** the moon phases, `Features.Beasts` and their lairs, `Features.Homes` (the dorm rooms), the door kit,
  attendance (curfew rules), and the lantern and keys from the QOL kit.
- **New:** night patrol routes, climbable dorm walls (tagged), a "snuck out" state, and night-only quests.

### 11. Favours with a haggle (M)
- **What:**
  - **Named students (concept 4) ask for small favours:** a lost hymnal, a love note delivered, a bully kept off
    them, a forbidden book returned to the library before anyone notices.
  - **Each has absurd stakes** ("My life is OVER if Wren finds it").
  - **There's a haggle choice:** do it for free (+relationship), ask for yen, or ask for a rumour (a hint toward a
    quest).
  - **They pay, and they remember.**
  - **One recurring "trainer" NPC** (an odd night watchman, or a ghost in the chapel loft) teaches a combat move
    each visit for a token item: a beast trophy, a moon-silver coin.
- **Built on:** `Quests.Quests` (dares and jobs already exist), `Features.LostFound` (lost things around the
  hangouts), the Dialogue system, Training, and the combat moves.
- **New:** a favour template set (deliver, find, escort, deter, return), the haggle choice in Dialogue, and the
  trainer and their move list.

### 12. Clique conquest in each clique's own game (M)
- **What:**
  - **NH has leader showdowns.** Add a challenge in each clique's own idiom before the showdown:
    - the Athletes: a dodgeball or sprint match;
    - the Ink Club: a sketch-and-guess duel;
    - the Choir: a rhythm-off on the Lab Mix engine;
    - the scholars: a Match the Past race.
  - **Winning flips the clique's greetings visibly** (the line matrix): hostile → wary → friendly. Their hangout
    welcomes you.
  - **A school-wide "fall from grace" event every few weeks:** someone frames the King or Queen of the School, every
    clique's standing drops, and there's a quest chain to clear your name.
- **Built on:** `Social.CliqueShowdowns`, `Config.Cliques`, the four class minigames (reused as challenge engines),
  and the King or Queen title.
- **New:** one challenge per clique (re-skinned class games), the greeting flip, and the framing event with its
  chain.

### 13. Classes 2.0: a voice, and skills you take out of the room (M-L)
- **What:**
  - **Each teacher gets a voice kit:**
    - a rule line at the start;
    - encouragement while you play;
    - graded verdict lines that match the red-ink stamp;
    - an early dismissal for an A+.
  - **Classmates mutter about themselves** at their desks.
  - **Each class level unlocks something in the world:**
    - **Chemistry → brew items** (stink bombs, a smoke vial for escaping the monitor, a lantern oil that keeps
      beasts back);
    - **English → talk your way out:** an apology that cancels a write-up, or a better haggle;
    - **History → read old things:** plaques and graves give hints, and the founder's secrets lead to a quest
      line;
    - **Mathematics → better odds:** gambling at fight rings, concession prices.
  - **School events reuse class games:** the pageant or a choir night runs on Lab Mix.
- **Built on:** `School.Activities`, `Config.Activities`, the four games, `Features.Inventory` and Items, and
  Discipline.
- **New:** teacher and classmate lines, the unlock table, and the brewed items.

### 14. The school year: seasons and holidays (L)
- **What:** a looping calendar of events, each changing the map's look and the rules for a few days.
  - **All Hallows' Night:**
    - costumes in the Wardrobe;
    - students in costume;
    - the monitors at the staff party, so authority is light;
    - a "scare 3 students" job;
    - the beasts more daring.
  - **Winter term:** snow on the map, breath fog, students in coats and scarves, snowball fights in the yard, and a
    candlelit winter concert.
  - **The Founders' Fair:**
    - prize booths (re-skinned class games);
    - a strength tester;
    - a ride;
    - a date with a friend;
    - fortune telling.
  - **Exam week:** every class doubled for a week, with tighter monitors and a cheating line (photograph a teacher
    selling answers).
- **Built on:** the clock (days and weeks), the moons (each event can lean on a special moon), the Midnight Bell
  (announcements), the prop kits, and the Wardrobe.
- **New:** a calendar service, per-event map dressing (tagged props switched on and off), costumes, and event
  quests.

### 15. A camera in the phone (M)
- **What:** a Camera app on the phone. Photographs are evidence:
  - for quests: a teacher selling answers, a rival clique mid-prank, the true source of a false rumour;
  - for investigation: beast tracks, a clue at a crime scene;
  - for the Midnight Bell: a picture of the week.

  Students react to being photographed: they pose, hide their face, or get angry.
- **Built on:** `Features.Phone` and `Gui.Phone`, `docs/Quests-and-Investigation.md`, and the rumour mill (concept
  3).
- **New:** the Camera app (a viewfinder, and "subjects" tagged by quests), photo checks on the server, and the
  student reactions.

### 16. Disguises (M)
- **What:**
  - Wearing a clique's full look lets you walk their turf unchallenged, until someone who knows you looks closely.
  - A janitor's coat or a staff sash gets you past the monitor at night.
  - A costume (the mascot, a choir robe) is a mission tool.
- **Built on:** `UI.Appearance` (looks are already server-checked), the clique looks, Senses (being looked at
  closely), and HallMonitor.
- **New:** a disguise check (whose look, how close, how long they look), a few staff and mascot outfits, and missions
  that need them.

### 17. Arcade cabinets in the commons (S-M)
- **What:** two or three original cabinet games (a top-down maze, a lane racer) on server high-score tables. Beating a
  clique member's score is a small win for their standing, and the King or Queen's score is a target.
- **Built on:** the minigame framework from `School.Activities`, the Midnight Bell (top scores), and the props.
- **New:** the cabinet prop with an interact, two small games, and high-score boards.

### 18. A voice for the player (S)
- **What:** the player's own short lines on everyday actions:
  - picking things up ("Someone'll miss this");
  - finishing a favour ("Done. You're welcome.");
  - a class pass;
  - a win.

  They're spoken as voice blips in the player's chosen voice set. It's a small thing that gives your character a
  personality. Players pick a temperament in the Wardrobe (cocky, dry, kind), and that picks the line pool.
- **Built on:** `Config.NpcVoice`, the voice blips, and Identity.
- **New:** the player line pools and a temperament setting.

---

## Where I'd start

1. **The line matrix (1) with outfit awareness (2).** It touches every student at once and is mostly writing.
2. **The spoken authority ladder with hiding and crowd blending (9).** It turns the existing discipline system
   into play, and pays off the nudges.
3. **The rumour mill (3) with named students (4).** It's what makes the school remember.
4. **Fight crowds (5)**, then **favours with a haggle (11)**.
5. **The calendar (14)**, starting with All Hallows' Night.

## Your calls

- **Keys:** G already introduces; does it also open the favour or haggle talk? Is hiding E, or a hold?
- **Named students:** how many per place (12, 20, 30), and do you want to name them, or should I?
- **Tone of the crowds and rumours:** how harsh can students be about each other? (No slurs or innuendo either way.)
- **The trainer NPC:** a night watchman, a chapel ghost, or someone else?
- **Which holiday first.**
