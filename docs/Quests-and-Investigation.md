# Quests, Investigation, Stealth and Duels: NH Combat Test

**Status:** built and verified in Studio playtests (single player). This covers:

- the quest framework
- 3 main-story quests (Chapter 1)
- 5 side quests: delivery, lost item, champion fight, PvP duel, and a stealth heist
- investigation with an evidence board
- stealth with lockers and watchers
- the duel ring
- the journal (**J**) and the on-screen tracker

The journal and tracker use the new Nightmare Highschool UI kit (`ReplicatedStorage.UI`).

> **Story note:** the concept doc doesn't define a storyline, so Chapter 1 ("The Empty Desk" mystery about a student named Mira Holt) is **original and provisional**. It sets up a mystery without explaining it. Replace or extend it when the real story is decided. All quest text lives in config files, not code.

## The quests

| Quest | Type | Giver | What you do | Reward |
|---|---|---|---|---|
| **New Kid** | Main, Ch. 1 | starts by itself | attend a class → meet a faction leader → read the note jammed in locker 113 | 15 Yen, Popularity |
| **The Empty Desk** | Main, investigation | follows New Kid | find 4 clues (Room 102 desk, Room 101 register, Archive borrowing card, plus the locker note) → connect them on the evidence board → answer "Where is her original record kept?" | 25 Yen, Trust, Academics |
| **After Hours** | Main, **stealth** | follows The Empty Desk | after 5 PM, sneak into the Records Office past the Night Custodian, take Mira's file, get out unseen | 40 Yen, Trust, title **Night Owl**, final clue, end-of-chapter text |
| **Special Delivery** | Side, delivery, **daily** | Dex (courier) | carry a package to Pip within 30 in-game minutes. Getting downed drops it. | 20 Yen, Trust |
| **Lost and Found** | Side, search | Pip | find Pip's charm (it's in one of 3 spots, picked at random). Optionally ask Dex, who tells you which spot. Return it. | 20 Yen, Popularity, Trust |
| **King of the Ring** | Side, fight | Bruno | ask Bruno to call out his champion, then down him in the ring | 30 Yen, Intimidation, title **Ringleader** |
| **Settle It in the Ring** | Side, **PvP**, daily | Bruno (after King) | win a ring duel against another student | 15 Yen, Intimidation |
| **The Answer Key** | Side, **stealth**, faction | Vesper (not offered to Vigil members) | sneak into the staff room past Mr. Hale, swipe the answer key, get out, bring it to Vesper | 20 Yen, Court +10, Vigil −5, Popularity |

**New NPCs (original):**

- **Dex Moreno**, Campus Courier
- **Pip Larkin**, a first-year
- **Bruno Vance**, Keeper of the Ring
- **Night Custodian** (Records Office, evenings and nights)
- **Mr. Hale**, chemistry teacher (staff room, school day)

**Lore lines:** each NPC has small-talk lines that hint at the mystery. For example, Pip can't remember Mira's face, and Dex mentions doors that lock from the inside.

## How it plays

- **Getting quests:** from NPC dialogue. Replies show as **[Quest] Name**, **About "Name"...** (progress) and **[Try again] Name** (after a failure). Turn-ins happen when you talk to the NPC, and they open with a thank-you line.
- **Tracker:** under the clock, it shows the tracked quest, the current objective with its count, and a countdown for timed quests. A **◆ marker** shows the distance to the target: an NPC, an object, an area, or your dropped item.
- **Quest objects:** prompts (E) only appear for things you currently need, with a soft gold outline. There are no invisible interaction points.
- **Journal (J, or the Journal button for touch):**
  - **Quests tab:** active quests with every objective (✓ done, ◆ current, ○ later), Track, and Abandon (side quests only), plus failed and completed quests and the chapter ending text.
  - **Case Files tab:** your clues with where you found them. Tap two clues and press **Connect**. Below that are your insights and the deduction question.
- **Stealth:**
  - Inside a watched zone, an eye meter shows the zone name and "unseen", "SOMEONE SEES YOU" or "HIDDEN".
  - The meter fills while the watcher can see you: within range, inside a 100–110° view cone, and with clear line of sight. Running fills it 1.7× faster; standing still fills it at 0.6×.
  - Watchers stop and say a suspicious line at about 45%.
  - Lockers (E) hide you completely.
  - **Caught:** you're walked out to the entrance, get a **Trespassing** violation (+3 discipline points), and the quest rewinds to its checkpoint. Any item you took is taken back.
  - Hitting a watcher counts as getting caught.
- **Duels:** two students stand on the two ring pads for 3 seconds.
  - First one downed loses. Leaving the ring forfeits. A duel lasts at most 2 minutes, then it's a draw.
  - Both fighters are **Protected**: nobody can grip or carry them, and the loser is picked back up right away.
  - The ring is tagged `CombatAllowed`, so hall monitors ignore fights there.
  - Beating the same opponent counts for credit at most once per in-game hour, which stops win-trading.

## Failure and recovery (Part 10.5)

| Situation | Result |
|---|---|
| Timed quest runs out | The quest fails with the reason; the giver offers **[Try again]** |
| Downed while carrying a droppable item | The item drops as a glowing box only you can see and pick up. The marker points to it, and the giver refuses delivery until you have it back. |
| Caught in a stealth zone | Rewinds to the checkpoint. The quest isn't failed. |
| Disconnect | Everything is saved. A dropped item is back in your hands on rejoin. |
| Old or broken save (e.g. a missing secret) | Repaired on load: a hidden search gets a new hidden spot |
| Abandon | Side quests only. Main quests can't be abandoned. |

## Server authority

- Progress only comes from server events: attendance results, lesson results, dialogue opening (server-side range check), quest-object prompts (12-stud range, busy and rate checks), quest areas (server box test every 0.5 s), Downed, Stealth and Duels.
- The client can send only four requests: **Track**, **Abandon**, **Link** and **Deduce**.
- Link and Deduce are checked against `ServerStorage.QuestSecrets`, so the client never sees which clues connect or which answer is right. A wrong deduction has an 8 s cooldown, so spamming answers doesn't work.
- The hidden location of Pip's charm is stored in each quest's `Secret`, which is **left out of the copy sent to the client**.

## Map checklist for the builder

Everything is found by **attributes**, so the real map just needs parts with these. The current pieces in `workspace.School.Quests` are temporary placeholders (`Temporary = true`).

| Attribute on a BasePart | Value | Used for |
|---|---|---|
| `NpcPost` | `Ezra`, `Vesper`, `Dex`, `Pip`, `Bruno` | where each NPC stands (they walk back here) |
| `QuestObject` | `LockerNote`, `DeskCarving`, `AttendanceSheet`, `ArchiveCard`, `MiraFile`, `AnswerKey`, `LostSpotA`, `LostSpotB`, `LostSpotC` | things you use (E prompt and gold outline are added automatically) |
| `QuestArea` | `RecordsOffice`, `RecordsExit`, `StaffRoom`, `StaffExit`, `DuelRing` | invisible box volumes. Make them `CanQuery = false` so they don't block line of sight. Tag `DuelRing` with `CombatAllowed`. |
| `WatcherRoute` + `Order` | `RecordsRoute` / `StaffRoute`, then 1, 2, 3… | the patrol points for each watcher |
| `HidingSpot` | `true` | lockers you can hide in. The part's front face (−Z / LookVector) is where you step out. |
| `DuelPad` | `1`, `2` | the two ring pads |

**Line of sight:** any part with `CanQuery` on blocks a watcher's view, so real walls and cabinets give cover automatically. Glass is the exception: it blocks the view unless you turn its `CanQuery` off.

## Files

| Where | What |
|---|---|
| `ReplicatedStorage.Config.Quests` | every quest, objective, item and quest object: text, rewards, rules |
| `ReplicatedStorage.Config.Cases` | case clues and deduction questions (public text) |
| `ServerStorage.QuestSecrets` | which clues connect, and the answers (server only) |
| `ReplicatedStorage.Config.Stealth` | zones, watchers, detection tuning |
| `ReplicatedStorage.Config.Npcs` | the cast: name, role, colour, dialogue tree |
| `ServerScriptService.Services.Quests.Quests` | quest engine: start, progress, complete, fail, items, drops, checkpoints, sync |
| `…Quests.Investigation` | clues, links, deduction |
| `…Quests.Stealth` | watchers, detection, lockers, getting caught |
| `…Quests.Duels` | ring duels and the champion |
| `…Quests.Places` | finds map parts by attribute |
| `ServerStorage.Dialogue.{QuestChoices, GiverTemplate, Dex, Pip, Bruno}` | quest dialogue (the leaders use QuestChoices too) |
| `StarterPlayerScripts.Controllers.Gui.{QuestJournal, QuestTracker}` | client UI (NH UI kit) |
| `Remotes.Packets.QuestAction` | the only client→server quest packet |

**Other changes:**

- `Services.Social.Npcs`: spawns everyone in `Config.Npcs` at their `NpcPost`.
- `Services.Social.Dialogue`: quest hooks and non-faction NPCs.
- `Features.Downed`: `Protected` blocks grip and carry.
- `AI.NPCController`: `Config.FixedTarget` for scripted fights.
- `Config.Discipline`: the `Trespassing` violation.
- `PlayerData.Quests` and `UpdateState` `SetQuests`.

**Data structure:** objectives run in order. Optional objectives count at any time while the quest is active. Objective types: Attend, Talk, Interact, Collect (with optional hidden spot), Deliver, Reach (optionally holding an item), Clues, Link, Deduce, Defeat, Duel, Lesson. Objectives can have a time window (e.g. after hours) and can grant clues.

## Verified in Studio playtests (single player)

**Main story**

| What | Result |
|---|---|
| New Kid | starts by itself. Class → stage 2. Talking to Vesper → stage 3. Using the note from too far away does nothing; up close it completes, pays Yen, starts The Empty Desk, and grants clue 1/4. |
| Investigation | 3 clues found in the world (2/4 → 4/4). Deduce before linking: refused. Wrong pair: "don't seem to fit". 2 correct links, then a duplicate refused. Wrong answer, then "take a moment" (cooldown), then the right answer solves it → After Hours starts. |
| Journal | J opens it. Both tabs render with the kit: objectives, clues with locations, insights, solved text (screenshots). A real click switched tabs. |
| After Hours | the file is refused before 5 PM. The custodian spawns at 18:00 and is gone by day. Standing in view at 20 studs: the meter filled (12 → 92%), then caught in 2.7 s, thrown out, +3 points. In a locker the meter stays at 0. Caught while holding the file: the file is taken back and it rewinds to "take the file". Clean run → done, title Night Owl, final clue added. |
| Detection HUD | "Records Office · SOMEONE SEES YOU" with a red bar, and the custodian's "...Hello?" bubble (screenshot) |

**Side quests**

| What | Result |
|---|---|
| Special Delivery | offered and accepted through Dex's dialogue, with a 150 s timer. Downed → package dropped (glowing box, owner only). Pip refuses it while it's on the floor. A **real E press** picked it up. Delivered → +20 Yen, and once per day. Next day: a forced timeout → "You ran out of time", and Dex offers **[Try again]**. |
| Lost and Found | Dex's tip named the right spot. The wrong spot: "Not here". The right spot gives the charm. Pip opens with her **thank-you line** and the quest completes. |
| King of the Ring | Bruno calls out the champion (it only fights you). Losing: the champion leaves and the quest stays active. Rematch and win: done, title Ringleader. Gripping the downed champion is refused. |
| Settle It (PvP) | **A dummy stood in for the second player.** Leaving the ring forfeits (no credit). A win completes the quest. The loser is picked back up (25 HP) and unprotected afterwards. |
| The Answer Key | locked for Vigil members. After leaving the Vigil, Vesper offers it. Swipe → exit → deliver: Court +10, Vigil −7.5 (−5 plus the usual rival share). |

**Bugs found and fixed during testing:**

1. **Four Mr. Hales spawned.** The stealth loop ran every frame, and spawning a watcher takes a moment, so each frame started another spawn. It now runs on one thread.
2. **The hidden charm spot was erased.** The save helper (`Data.UpdateState`) also writes the trimmed client copy back into the server's save. Quests now send the client copy directly. Saves that were already broken are repaired on load.
3. **NPCs skipped their thank-you line** because the completion signal arrived after the dialogue had picked its first line. Completions during a conversation are now collected directly.
4. **Long chapter-ending text was cut off** in the toast. It's now also shown in the journal's Completed list.

**Not tested:**

- **Two real players**, including a real PvP duel started from the pads. The pad countdown code is written but needs 2 players. Studio's multi-client test (Test → Clients: 2) would cover it.
- the client copy actually leaving out the secret. This was checked by reading the code, not by capturing a packet.
- mobile and touch layout
- a full real-time walk-through. Tests used teleports and the test bridge for speed, with real key presses for E, J and the journal tab.

**Known UI issue (UI-kit session, in progress):** the reskinned clock panel is drawn far taller than its content and covered the tracker in screenshots. I raised the tracker's draw order and told that session.

**Studio test profile now holds:** all quests except Special Delivery (active) completed, the titles Night Owl and Ringleader, the Vigil left, and some discipline points from the catch tests. Clear it with the TestBridge `ResetQuests`, `ResetSocial` and `SetDiscipline` commands.

## Ideas for later

- Chapter 2 once the story is decided (the hooks are ready: `Next`, `Requires`, cases)
- More cases using the same evidence board
- Rivalry quests that use the duel ring ("Bruno's rival wants a rematch")
- Teacher NPCs in classrooms as watchers for cheating quests
