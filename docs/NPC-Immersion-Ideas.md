# Making the school NPCs feel alive: ideas (2026-11-10)

Owner: "give me concepts on how I can make them feel more immersive". These build on what the Map's students already do (`docs/Map-Students.md`). Each idea names the game systems it would use. Ideas marked **(small)** are a day or less.

## 1. Voices, not just bubbles
- **Voice blips** (small): a short burble of syllables per line, pitched per student (one voice each), the length of the text. It's the Animal Crossing / Undertale trick: no voice acting, but every line is *heard*. A sharper blip for shouts ("Whoa!"), and a lower, slower one at night.
- **Barks**: a few real audio clips for gasps, laughs, "hey!" and a scream when someone's downed, played with the matching lines.
- **Crowd murmur**: a soft chatter loop whose volume follows how many students are near you, so the halls hum at passing time and go dead quiet at night.

## 2. Body language
- **A gesture per line**: a wave on hello, a shrug, pointing, crossed arms when wary, hands on hips, a laugh. Lines.luau can tag each line with a gesture, and the owner's animation pack has most of these.
- **Idle fidgets** (small): checking the phone (`ServerStorage.NHPhoneModel` is already in the Map), stretching, shifting weight, kicking a stone, glancing at the clock tower.
- **Eyes** (small): move the irises on the face strips toward the look target. Blink more when nervous, and stare when shocked (EyeBlink already blinks).
- **Turn the body**: when a head hits its 75° limit, the student turns their whole body.

## 3. Lives of their own
- **Names and routines**: every student gets a name, a clique, a locker, friends and real classes (once the rooms are fitted: `Features.Schedules` already sits them at chairs). They run at the bell when they're late, and queue at the concession stand at lunch.
- **They use the game's systems**:
  - a skateboarder in the yard (`Features.Skateboard`);
  - someone on the phone;
  - a student at the notice board reading the Gazette;
  - someone opening a locker in the locker room.
- **More of them, by period**: 20 to 40 students with cheaper behaviour far away (no sensing beyond 120 studs). The halls packed at passing time, a handful at night.

## 4. They remember you
- **Saved relationships**: keep what each named student thinks of each player in PlayerData (Social.Relationships already exists in NH Combat Test). They'd greet a friend by name, ignore someone they dislike, or flinch at someone who beat them up.
- **Names through Strangers**: press G on a student to introduce yourself. They tell you their name back and show it from then on (`Social.Strangers`).
- **Gossip**: when one student sees you fight, others hear about it. Within a few minutes, students who never saw it say "You're the one who started that fight". Reputation (Popularity, Intimidation) colours every hello.

## 5. Groups and crowds
- **Fight rings**: students who gawk at a fight form a loose ring at a safe distance and cheer or boo (the Gawk lines are already written for both).
- **Walking together**: friends leave a spot together, chat while walking, and wave goodbye when they split up.
- **Students greet each other**: a nod or a hello in passing, and a high five between friends.
- **Clique hangouts**: each clique has its spot and its own lines (Athletes talk practice, the Choir talks hymns, the Ink Club talks drawings that move).

## 6. They notice the world
- **The moon and the dark**: at a full moon they head indoors early and huddle under lamps. When night beasts are about, they run for the building and lock doors behind them.
- **Your state**:
  - low health on the Thornrose bar: "You don't look good. Get to the nurse.";
  - transforming in front of them;
  - an admin's crow teleport: "Did that guy just turn into birds?!".
- **Your fun**: dance back when you emote, "Sick kickflip!" at skateboard tricks, crowding round someone playing a phone game.
- **The building**: hold doors for each other, look up when lights flicker, step over a mopped floor.

## 7. Talking to them
- **A short conversation** with any student, through the existing Dialogue system: ask directions (they point to the room), hear a rumour that hints at a quest, trade a snack, ask about their clique. *This needs your call on keys:* E is doors only (1.67.0), so maybe G (introduce) opens it.
- **Small favours**: "Can you take this to Room 103?", "Have you seen my notebook?". Little quests that reward relationship.

## 8. Things that happen
Short scripted moments the school stages every few minutes near players:
- a bully shoves a first-year;
- someone drops a stack of books;
- two friends argue;
- a student sits crying on the steps;
- a lost first-year asks for the library.
Players can step in or walk past, and the students remember either way.

## 9. Staff
A hall monitor on patrol (NH Combat Test has `School.HallMonitor`), teachers in their doorways shouting "Get to class!", a janitor mopping, the nurse at her door. They make the students' behaviour make sense: they hush when a teacher walks by.

## Where I'd start
1. ~~Voice blips (1) and idle fidgets (2)~~: done in 1.78.2 (phone, stretch, glances, weight shifts).
2. Names through Strangers and remembering you (4).
3. Fight rings and walking together (5).
4. Talking to them (7), once you choose the key.
