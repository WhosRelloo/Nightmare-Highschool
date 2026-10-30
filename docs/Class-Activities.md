# Class Activities: NH Combat Test

The lessons follow Bully's class loop: you sit a short, timed, arcade-style minigame, the teacher grades it, and passing unlocks the next class level. All the content is original, and the genres are ones kids already play a lot.

| Class (room) | Game | Genre | How it plays |
|---|---|---|---|
| Mathematics (R102) | **Pop Quiz** | timed quiz | 8 questions, 4 chalk answer boxes (keys **1–4** or tap), a shrinking timer per question, and streaks. Level 1 is + and −, then ×, then ÷, then two-step problems. The timer per question goes from 8 s down to 4 s. |
| Chemistry (R103) | **Lab Mix** | rhythm | Ingredients fall down 4 lanes. Press **D F J K** (or tap the pads) as each one crosses the line. Slips and misses fill the **bubble meter**, and when it's full you get **BOOM**. Higher levels mean more notes, faster tempo, and quick double-steps. |
| English (R104) | **Word Scramble** | word puzzle | 5 scrambled school words. Type or tap the letters, then **Enter** to check. You also get Backspace, Shuffle, Clear, and Skip. Words go from 4 letters up to 10 ("ATTENDANCE", "NIGHTMARE"). |
| History (R105) | **Match the Past** | memory | Face-down index cards. Flip two to pair each event with its era (e.g. Moon landing ↔ 1969). There are 4 pairs at level 1 and 8 pairs at level 5. |

Homeroom has no minigame.

## Flow

1. **Start:** during that class, in the room, walk up to the **teacher's desk** and hold **E** ("Start lesson"). The clock panel also says "[E] Start lesson at the teacher's desk".
2. **Intro:** a chalkboard opens with the title, the subject and your level, a rules line, and a **3-2-1** countdown. Your character is frozen and combat is locked while you play (`InActivity` state). Backpack hotkeys are off.
3. **Play** the game. Your score and the lesson timer are shown on the board. **Leave lesson** quits.
4. **Grade sheet:** a lined paper sheet with a **red-ink grade stamp**, your score %, PASSED or FAILED, the rewards, and an original teacher one-liner.

## Grading and rewards (`ReplicatedStorage.Config.Activities`)

**Grades:** A+ ≥ 97, A ≥ 90, B ≥ 80, C ≥ 70, D ≥ 60, F below that. **C or better passes.**

**Passing:**

- pays Yen: A+ 20, A 15, B 10, C 6
- raises your **class level** by 1, up to 5 (harder next time)
- both happen **once per class period**

**Failing:** you can retry during the same period.

**Practice:** replaying a period you already passed is marked practice and gives no rewards.

**Attendance:** the period's attendance record gets the best lesson grade (`ActivityGrade`), and the end-of-class toast shows it.

**Saved data:** `PlayerData.Classes[Subject]` holds `Level`, `Passes`, `BestGrade` and `LastRewardKey`.

**Cancelled (no grade):** leaving the room, quitting, or disconnecting. **The bell** ends the lesson and grades what you finished.

## Anti-cheat (server authoritative)

The server generates every question, word, card layout, and note chart, and judges every action.

| Game | What the server enforces |
|---|---|
| Math | Answers must be for the current question and arrive before the deadline, plus 0.6 s for latency. Old questions and junk data are ignored. |
| Words | Answers must arrive before the word's deadline. Guesses longer than 20 characters are rejected. |
| Memory | A card's text is only revealed when the server flips it, so the client never has the layout. Re-flipping a card and out-of-range indexes are ignored. |
| Lab Mix | Each press is judged by **when it reaches the server**, minus the player's ping (capped at 0.35 s). The client draws the chart but can't fake timing. Mashing every lane counts as slips and blows the beaker. |

**Everywhere:** a limit of 20 actions per second, actions only count for your own session, and rewards come only from the server.

## Files

| Where | What |
|---|---|
| `ReplicatedStorage.Config.Activities` | Subjects → game type, titles, grades, rewards, teacher lines |
| `ServerStorage.Activities.{MathQuiz, LabRhythm, WordScramble, MemoryMatch}` | Each game's rules and judging (server) |
| `ServerScriptService.Services.School.Activities` | Desk prompts, sessions, validation, grading, rewards, cancel rules. `Activities.Finished(Player, Subject, Result)` signal. |
| `StarterPlayerScripts.Controllers.Gui.Activities` (+ 4 child screens) | Chalkboard UI, intro, timer, grade sheet |
| `ReplicatedStorage.Remotes.Packets` | `ActivityEvent` (server → client), `ActivityAction` (client → server) |

## Verified in Studio playtests (single player)

Some checks used real key presses or mouse clicks; others used a test script.

| Game | Run | Result |
|---|---|---|
| Pop Quiz | **real keys** 1–4 | 7/8 (one wrong on purpose) = 88% → **B** stamp, PASSED, +10 Yen, Level 2 unlocked. "Correct! / x4 STREAK! / Nope." feedback, and the right answer shows green, the wrong one red. |
| Word Scramble | **real typing** | A wrong word gave "Not a word we're looking for", then a retry. Backspace undo, "BULLY" → "Nice!", and a **mouse click** on a tile fills the slot. |
| Match the Past | **mouse clicks** | A mismatch flipped back and counted (Misses 1). Running out of time gave **F**, "FAILED: you can retry". The retry was a perfect run: 100% → **A+**, +20 Yen, Level 2. |
| Lab Mix | **real D key**, plus an auto-player that watches the falling ingredients and sends hits | The D press was judged by the server (SLIP!, bubble meter rose). Level 1 → **B**, Level 2 → **A+**, Level 3 → **A+ with 20/20 Perfect** (after the two timing fixes below). |

**Rules:**

| Rule | Result |
|---|---|
| **Desk prompt** | A real E press started the lesson. The HUD shows "[E] Start lesson…", then "Lesson passed". |
| **Leaving the room** | "Lesson cancelled. You left the classroom.", no grade, and you can move again. |
| **The bell** | The lesson ended with `Reason = Bell` and graded what was done. |
| **Practice** | A replay after passing was marked practice: no Yen, no level. |
| **Fail and retry** | A failed run kept the level, saved best grade F, and allowed a retry. |
| **Attendance** | The period record got `ActivityGrade = A+`. The toast read "Period 2: Chemistry · Left early · Lesson grade A+". The Left Early is only because the test jumped the clock. |
| **Errors** | No script errors. |

**Bugs found and fixed during testing:**

1. **Lab Mix lagged the beat.**
   - *Problem:* the client started its song clock when the screen finished building, not when the start message arrived, so a perfectly timed press was judged late.
   - *Fix:* the client now uses `GameStartClock` (message arrival + intro).
2. **A fixed pipeline delay.** After fix 1, hits were still about 79 ms late even with ~0 ping, because the packet library sends on frame boundaries both ways. The server now subtracts a 75 ms `PIPELINE_DELAY` as well as ping. Measured after the fix: mean +19 ms, 20/20 Perfect.
3. **All-"Good" Lab runs scored 100%.** Scoring is now Perfect = 1 and Good = 0.8, so an all-Good run is a B.

**Test note:** each tool round trip is slower than the 8 s and 22 s timers, so the runs used the test-only `SlowLesson` command and an auto-player. Real players don't need either.

**Not tested:**

- two players in one class
- mobile and touch layout. The board scales and every action has a tap target, but no phone test has been done.
- real-server ping. Ping is subtracted from timing, but only Studio's ~0 ping was measured.

## Earlier checks

**Server game logic, simulated in edit mode:**

- **Math:** perfect runs score 8/8 at levels 1–5. Late answers, answers to old questions, and junk data aren't counted. 300 generated questions all had 4 distinct options including the answer.
- **Words:** a perfect run scores 5/5. A wrong guess can be retried. A correct word after time runs out doesn't count. A 500-character guess is rejected.
- **Memory:** perfect runs score 100% at levels 1 and 5. 10 misses then solving scores 64%. A double flip or an out-of-range index is rejected, and a flip only reveals that one card.
- **Lab Mix:**
  - on-beat play scores 100% (levels 1 and 5, and with 200 ms ping)
  - always 0.15 s off ("Good") scores **80%**. After testing I changed the scoring so precision matters; before, it was 100%.
  - 0.35 s late misses everything and explodes
  - mashing all lanes gets 2 of 16 hits and explodes


## Ideas for later

- Teacher NPCs at the desks, using the same `ReportIncident` to report fights in class.
- More subjects: Art (a pattern or drawing challenge), Gym (a timed obstacle course), Music (a rhythm variant).
- Class level rewards like Bully's class unlocks, e.g. an item or ability at levels 3 and 5. This needs your call on what each class unlocks.
