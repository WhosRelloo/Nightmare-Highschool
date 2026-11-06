# Admin Panel: the Headmaster's Desk (NH Combat Test)

Added in 1.8 (2026-11-02). It's a staff panel built only from the game's UI kit (Panel, TabBar, Buttons, Search, Toggles, Sliders, Section headers) with the school crest. Press **F3** to open it.

## Who can open it
- Group rank **254+** in the owning group, the `Config.Cmdr` admin and owner lists, and **anyone in Studio**.
- **Owner-only:** shutdown, permanent bans, and Yen grants over ¥100k. These need the owner rank or `Config.Cmdr` owner.
- **Everyone else** gets nothing, not even a hint that the panel exists.
- **No targeting up:** staff can't target someone of a higher rank.

## Files
| Where | What |
|---|---|
| `ServerScriptService.Services.Features.Admin` | The back end: permission checks, rate limits, the action log, every command |
| `StarterPlayerScripts.Controllers.Gui.AdminPanel` | The panel UI (F3) |
| `ReplicatedStorage.NHAdmin` | Remotes: `Info()` returns `{ Level, Players, Server, Log, Gear, Lists, Locked }`; `Run(Command, TargetUserId?, Args)` returns `ok, message`; `Inspect(UserId)` returns a read-only summary of that student's loaded slot (1.18) |

The Luau sources are kept outside this repo (the repo holds no `.luau` files).

Other UI can open the desk by setting the player attribute `NHAdminOpen` to `true`, `false` or a tab number. The server still decides who gets in.

## Tabs
- **Students:** search, health, race, ping, and tags for owner, staff, muted, frozen and god mode.
- **Moderation:**
  - **Everyone (1.18):** bring everyone to you, freeze everyone, or thaw everyone. These skip staff and anyone in the main menu.
  - **Staff note (1.18):** a note on the selected student, seen by staff in this server. Their row shows NOTE, and the inspector shows the text. Notes are not saved.
  - Warn (with a reason), mute and unmute (blocks chat on every channel), and freeze.
  - Send to detention, spectate, and kick.
  - Ban through the Roblox ban API (in days; permanent bans are owner-only), and unban by UserId.
- **Student:**
  - Heal, revive, god mode, transform, bring, go to, clear the disciplinary record, kill, and a walk-speed slider.
  - Give Yen, Combat EXP, lineage spins or a name change.
  - Give any of the 40 gear pieces (listed by rarity colour).
- **School (1.18):**
  - **Discipline:** set points (the ladder recomputes the level, probation and suspension).
  - **Excuse today:** today's absences, tardies and early leaves become Excused, and their discipline points come back off.
  - **Suspension and detention:** lift a suspension (with its probation; points drop to 9 at most so it doesn't come straight back), clear or add an owed detention, clear the record, or send them to detention.
  - **Lessons:** start a lesson for them in Rooms 101 to 105.
  - **Skip to a period:** any period, always forward (today if it's still ahead, else tomorrow). Night means 21:00. Moving the clock can mark students in school absent for the classes it skips; Excuse today clears that.
  - **Ring the bell.**
- **Progress (1.18):**
  - **Level and stats:** set their level (their EXP is kept if it still fits under the new level's bar) or stat points, and give Class, Quest, Social or Sport EXP.
  - **Titles:** grant or remove any title.
  - **Places found:** mark all 19 found (with the Explorer title, no EXP), or reset them.
  - **The inspector:** a read-only view of their loaded slot. It shows UserId, slot, race, level, EXP, stats, Yen, kills, discipline, attendance totals, titles, places found, club, active quests, phone-game bests and any staff note.
- **Activities (1.18):**
  - **Matches:** start a solo test match for the selected student at the Field, Gymnasium or Pitch, or end the match there.
  - **Clubs:** put them in a club (Iron Wardens, Night Ravens, Grave Rovers) or take them out.
  - **Quests:** start or drop any quest, or reset all of theirs. Race rites are owner-only and hidden from the list.
- **World:**
  - **Clock:** set the school clock (or Morning, Noon, Midnight) and set the clock speed. **Full moon tonight** (1.18) moves the clock to 22:00 on the next full-moon day.
  - **Go to a place (1.18):** a button for each of the 19 regions. A toggle sends the selected student there instead of you.
  - **Announcements:** send one to the whole server.
  - **Server lock (1.18):** while it's on, new players who aren't staff are turned away. Shutting the server down is owner-only.
- **Spawns:** a delinquent crew, a wolf pack (night only), a sparring partner of any difficulty (Easy, Normal, Hard, Nightmare; 1.23), or clear all enemies.
  - (1.56) **Beast: <name>**, one button per beast in `Config.Beasts`, by name ("Beast: Hellhound", "Beast: Grave Ghoul"). It spawns that beast 22 studs in front of you, facing you, at any time of day, and it stays until killed or cleared (`SpawnBeast`). "Clear all enemies" removes beasts too, and the alive line counts them. See [[Beasts]].
- **Self:** fly (WASD, Space, Ctrl, Shift for speed), noclip, ESP (names and health through walls), Ctrl+click teleport, invisibility, heal, and stop spectating.
- **Server:** students, uptime, physics FPS, memory, school clock, enemy and wolf counts, and the staff log (the last 200 actions).

## Quality of life (1.18)
- **Find a command:** the search box at the top right looks through every tab. Pick a result to jump to its tab; the button gets a gold ring.
- **Favourites:** right-click any button to pin it to a Favourites row at the top of every tab. Right-click again to unpin. Pins last for this session.
- **Recent students:** the last five students you picked float to the top of the list, tagged "recent".
- **Search by UserId:** the student search also matches a UserId exactly.
- **Copy a UserId:** the selected student's UserId sits in a box next to their name, so you can select it and copy it.
- **Row tags:** rows also show NOTE and IN MENU.

## Safety
- **Server-side:** every request is checked on the server, never trusted from the client. It's rate-limited and written to the action log.
- **Confirm twice:** destructive buttons (Kick, Ban, Kill, Shutdown, Clear enemies) need a second click within 3 seconds.

## Verified
**[PT]** Every 1.8 command was run in Studio on the spare save slot (slot II), and any data it changed was restored.

**1.18, tested in Studio Play on slot II at 17:30 (after school):**
- **Run through the remotes, with results checked against the saved data:** set points (12, then back to 6), clear detention, owe detention, excuse today (nothing to excuse), stat points (5, then back to 3), grant and remove a test title, staff note (the row flag set, then cleared), server lock on and off, bring, freeze and thaw everyone, ring the bell, go to the Gymnasium.
- **Refusals:** quest start and drop refused correctly: a finished quest, a quest that isn't active, and a race rite not yet open.
- **Clubs and matches:** joined and left a club, and started and ended a Gymnasium match. The saved sports data was unchanged afterwards (no club, no record).
- **The panel itself:** checked on screen. Picking a student fills the target and UserId box and tags them "recent". The School and Progress tabs render, and the inspector reads the slot. Find a command lists results across tabs and jumps to the button with its gold ring. Right-clicking a button pins it to Favourites.
- **Fixes the run turned up:**
  - Skip to a period could go backwards ("Night" was 00:00), so it now always moves forward.
  - Ending an already-ended match claimed success, so now it says there's no match.
  - A quest that won't start now says why.
  - Set level kept no EXP, so now it keeps EXP that still fits.
- **Second run, slot loaded from the main menu (never entered):**
  - **Set level:** 6 to 7 to 6, and the 439 EXP was kept both ways.
  - **Places found:** all (19/19), then reset (0/19).
  - **Clock, with no slot loaded:** Skip to Night went 18:53 to 21:00. Skip to Evening went to 17:00 tomorrow. Full moon tonight went to day 12456 at 22:00, and `Lineage.IsFullMoon` returned true.
  - **Restored afterwards:** the slot was put back exactly (level 6, 423 EXP, 3 stat points, places Main Hall and Room 102, discipline unchanged) with the new TestBridge cleanup commands `RegionSet(name, ids)` and `SetProgressFields(name, fields)`.
- **Not run in Play:** start a lesson (left alone so slot II's class record stays clean) and the Field and Pitch matches. They use the same calls as the Gymnasium one.
