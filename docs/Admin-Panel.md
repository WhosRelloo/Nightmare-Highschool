# Admin Panel: the Staff Console (NH Combat Test)

Staff console, phase 1a (2026-11-23, branch `admin-console`). It replaces the Headmaster's Desk. Press **F3** to open or
close it. Spec: `docs/superpowers/specs/2026-11-23-admin-console-design.md`. Mirror and checks: `tools/admin-console/`
(`pre/` originals, `live/` installed sources, `checks/` the pure and Play checks). The old desk is in
`ServerStorage.NH_Backup.AdminConsole1a_pre_20261123.AdminPanel`. To restore it, move it back into
`StarterPlayerScripts.Controllers.Gui` and put back the `GamepadControls` backup from the same folder (its menu entry was
`NHAdminPanel`; it is now `NHStaffConsole`).

## Who gets which level
Every request is checked on the server, rate-limited and logged. Nobody can target someone of a higher level.

| Level | Who | Gets |
|---|---|---|
| 0 | everyone else | nothing, and no hint the console exists |
| 1 Moderator | group rank 254 | the Moderate side; bans up to 30 days |
| 2 Admin | `Config.Cmdr.Admin` or `Config.Cmdr.Testers` | + the Test side |
| 3 Owner | rank 255+ or `Config.Cmdr.Owner` | + permanent bans, Shutdown, Yen over ¥100,000, race rites |

In Studio everyone is level 3 unless the server sets the player attribute `NHTestLevel` (0-3) or `NHTestNotAdmin` (= 0).
Commands per level (registry): level 1 = 16, level 2 = 65, level 3 = 66.

## Sides, sections and cards
Server cards come from `Features.Admin.Meta` (one entry per command); client cards come from `StaffConsole.Tools.Defs`.

**Moderate side** (level 1 unless marked)
- **Student (12 + 1):** Warn, Mute, Unmute, Freeze, Detention, Spectate, Bring, Go to, Kick (danger), Ban (danger), Unban,
  Note; plus the client card Stop spectating (13 cards on screen).
- **Server (5):** Announce, Server lock (danger), Bring all (danger), Freeze all (danger), Shutdown (danger, level 3).

**Test side** (level 2)
- **Character (16):** Heal, Revive, God mode, Kill (danger), Speed, Race, Tier, Spin height, Height, Build, Transform,
  Give Yen, Give EXP, Give gear, Give spins, Name change.
- **Progress (9 + Inspect):** Set level, Stat points, Grant title, Remove title, All places found, Reset places (danger),
  Club, Start a match, End a match; the client card Inspect (a read-only view of their slot).
- **School (11):** Set time, Clock speed, Skip to a period, Ring the bell, Start a lesson, Discipline points, Clear
  discipline, Lift suspension, Excuse today, Owe detention, Clear detention. Start a lesson offers only rooms with a
  timetabled subject (R102-R105), and a refusal says why (no class right now, already in a lesson, not enrolled, not in the room).
- **Story (3):** Start a quest, Drop a quest (both pick from the quest list; race rites are listed but owner-only),
  Reset quests (danger).
- **World (2):** Full moon tonight, Go to a place.
- **Spawns (6):** Delinquent crew, One delinquent, Wolf pack, Beast, Sparring partner, Clear enemies (danger).
- **Self (2 + client tools):** Invisible, Teleport to a point; the client cards Fly, Noclip, ESP and Ctrl+click teleport.

Arguments are checked on the server (`StaffConsole.CheckArgs`) before a command runs, and a refusal says why.

## Keys and controller
- **Keyboard and mouse:** F3 opens and closes; 1-7 pick a section; Tab switches Moderate / Test; **Ctrl+K** opens the
  palette (it finds by name, help or synonym: "tp" finds Go to; Up / Down move, Return picks); right-click a card to make it
  a favourite. Esc closes: Roblox keeps Escape for its own menu, so the console closes on `GuiService.MenuOpened`, and Esc
  from the palette closes the console too.
- **Controller:** LB / RB change section, the D-pad moves between cards, A runs, Y makes a favourite, B closes. The
  `NHStaffConsole` entry in `GamepadControls` marks the console as a menu.
- **Phone:** the rail and the context card open as overlays that sink taps, so a tap never reaches a card underneath.
- **Favourites** and the last side are saved (1b). With Reduce Motion on, the hold ring fills without
  spinning.

## Danger list (hold 0.8 s to confirm)
Kick, Ban, Kill, Shutdown, Clear enemies, Freeze all, Server lock, Bring all, Reset quests, Reset places. The ring fills
while the mouse button, A or Return is held on the card's Run. Releasing, moving off the button or the selection, losing
window focus, a redraw or closing the console cancels it. Return held while typing (the palette) never runs a danger card.

## Saved records, the Log and saved favourites (1b, 2026-11-23)
- **What is saved, and where** (Studio uses `[Test] ` stores, so it never touches live data):
  - `NHStaffRecords_v1`: each player's notes, warnings, bans and mutes, 50 of each (oldest dropped).
  - `NHStaffLog_v1`: every console action, run or refused, kept by day and by server. Test-side actions are removed
    after 7 days.
  - `NHStaffPrefs_v1`: each staff member's favourites and last side.
- **Warn, Note, Mute, Unmute, Ban and Unban** write the record straight away. The result says "Saved", or "Saved later
  (DataStore busy)" when the write waits and is retried. A note needs text now.
- **Mute lengths:** 10 min, 1 h, 1 day, Until unmuted. A mute holds across rejoins and ends on time.
- **Who may lift a ban:** a permanent ban, or one set before 1b (no ban on record), only the owner; over 30 days an admin;
  30 days or less a moderator. The Unban card shows the ban it would lift once a UserId is typed.
- **History timeline:** the right-hand panel on the Moderate side, for the picked student. A summary line at the top
  ("1 note · 2 bans (lifted) · muted until Wed 25 Nov 05:06"), then newest first. Lifted or ended bans and mutes are
  greyed and marked. The owner's ✕ (hold 0.8 s) removes an entry, and the removal is logged. Removing a ban or mute entry
  doesn't lift it: Unban and Unmute stay the only way. The card version is Remove history entry (owner, danger).
- **The Log section** (Moderate, key 3):
  - a day picker for this week;
  - search by staff, student, UserId or action;
  - the chips All, Moderate, Test and Refused (refused rows are red);
  - 50 rows a page with Prev and Next.
  A row opens that student's history, even if they're offline.
- **Favourites and side** come back the next time you open the console.
- **Limits:**
  - A crash can lose up to 30 s of the log.
  - A mute or ban set in one server reaches a player in another only when they next join (phase 3 adds live delivery).
  - "Not staff" and "Slow down" refusals aren't logged.
- **Cards with many options** (Ban, Mute, Remove history entry) grow taller and wrap their options onto more rows, so
  every option shows without scrolling (2026-11-24).
- **Decisions the 1b plan made** (approved by the owner 2026-11-24):
  - lifting a ban over 30 days needs an admin;
  - log entries keep the UserIds as well as the names;
  - a note can't be empty;
  - Remove history entry takes a UserId, online or not;
  - an offline UserId whose rank can't be read counts as the owner, so a lower rank can't act on them;
  - a failed record read on join leaves that visit unmuted;
  - the Play checks use a Studio-only switch to skip the Roblox ban service;
  - the log is searched and paged on the server;
  - mutes store their length in minutes;
  - bans and mutes that ended on time are greyed like lifted ones.
- Test record: `tools/admin-console/REPORT.md` ("Phase 1b").

## 1b and later
- **1b:** done (above).
- **2:** new Test tools (World, Story, Bell Tower and Form tools) and the REPORTED, TRANSFORMED, WANTED and NEW flags.
- **3:** the Inbox, player reports, flags and health graphs.

## Test record (1a, Studio Play on slot 2, 2026-11-23)
- `console_play_run` (server, through the real `Dispatch`): **PASS, 81 calls**. Every level 0-3 refusal and argument
  refusal, and all 66 registry commands. Kick, Ban, Unban and Shutdown were left out because they would end the session.
  Start a lesson succeeds in R102 during Period 1 (R101 is Homeroom and has no lesson). The run puts the slot back and
  fails on any attribute drift outside a short allow-list.
- `console_play_client`: **PASS**. Sections and cards drawn (Student = 13), "tp" finds Go to, no text under 20 px.
- `console_play_carried`: **PASS**. The phone overlays sink taps (0 leaks), and a student who leaves is unpicked.
- Real input: Freeze all doesn't fire on a 300 ms hold and fires at 1100 ms. Moving the mouse off cancels. A or Return
  held 1100 ms on a selected Run fires; 300 ms doesn't. Return in the palette never fires a danger card. Key Two goes to
  Server. Ctrl+K opens the palette. Esc in the palette closes the console. The scroll position holds through the 1 s refresh.
- Cutover re-check: F3 opens only the console, `PlayerGui` has no `NHAdminPanel`, and all three checks pass again.
- CineState, Seen and Origin were nil before and after every round.
- Not verified: dragging a finger off (touch), a real gamepad, alt-tab (checked in code only).
- Nothing was written outside slot 2. In 1a the staff log and notes live in memory only. The saved stores
  (`NHStaffRecords_v1`, `NHStaffLog_v1`) come in 1b.
- Final review fixes: Go to a place sends the selected student; Club has a "None" choice to take them out; Inspect needs
  level 2 on the server too; "no targeting up" is one tested rule (`StaffConsole.CanTarget`). Re-check: all checks PASS
  (`console_play_run` 87 calls).
- Screenshots: `docs/superpowers/mockups/2026-11-23-admin-console/play-*.png`. Full record: `tools/admin-console/REPORT.md`.

# Before 1a: the Headmaster's Desk (1.8 to 1.75)

Added in 1.8 (2026-11-02). It's a staff panel built only from the game's UI kit (Panel, TabBar, Buttons, Search, Toggles, Sliders, Section headers) with the school crest. Press **F3** to open it.

### Who can open it
- Group rank **254+** in the owning group, the `Config.Cmdr` admin and owner lists, and **anyone in Studio**.
- **Owner-only:** shutdown, permanent bans, and Yen grants over ¥100k. These need the owner rank or `Config.Cmdr` owner.
- **Everyone else** gets nothing, not even a hint that the panel exists.
- **No targeting up:** staff can't target someone of a higher rank.

### Files
| Where | What |
|---|---|
| `ServerScriptService.Services.Features.Admin` | The back end: permission checks, rate limits, the action log, every command |
| `StarterPlayerScripts.Controllers.Gui.AdminPanel` | The panel UI (F3) |
| `ReplicatedStorage.NHAdmin` | Remotes: `Info()` returns `{ Level, Players, Server, Log, Gear, Lists, Locked }`; `Run(Command, TargetUserId?, Args)` returns `ok, message`; `Inspect(UserId)` returns a read-only summary of that student's loaded slot (1.18) |

The Luau sources are kept outside this repo (the repo holds no `.luau` files).

Other UI can open the desk by setting the player attribute `NHAdminOpen` to `true`, `false` or a tab number. The server still decides who gets in.

### Tabs
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
  - (1.63) **Height:** Spin height (a free re-roll), Shortest, Average, Tallest, in the student's race range (`SpinHeight`, `SetHeight`). The student list shows each student's height. The Self tab has Spin my height. See [[Height]].
  - (1.65) **Race** (every race and variant, the base race in gold) and **Tier** (I, II, III): `SetRace` and `SetTier` through `Lineage.AdminSetRace` / `AdminSetTier`. A new race keeps the tier and clears hunger and race looks. The Self tab has My race and My tier. The student list shows the variant and tier. See [[Races-and-Bloodlines]].
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
  - (1.56) **Beast: <name>**, one button per beast in `Config.Beasts`, by name ("Beast: Hellhound", "Beast: Grave Ghoul", "Beast: Night Stalker", "Beast: Bone Spider", "Beast: Crypt Bat"). It spawns that beast 22 studs in front of you, facing you, at any time of day, and it stays until killed or cleared (`SpawnBeast`). "Clear all enemies" removes beasts too, and the alive line counts them. See [[Beasts]].
- **Self:** fly (WASD, Space, Ctrl, Shift for speed), noclip, ESP (names and health through walls), Ctrl+click teleport, invisibility, heal, and stop spectating.
- **Teleport effects (1.75):** your own moves (Go to, Go to a place, Ctrl+click teleport, Cmdr `to`) play the staff flock: crows for admins, bats for the owner. Students you bring land in a small swirl of your birds. While you're invisible, moves are silent. See [[Admin-Teleport-VFX]].
- **Server:** students, uptime, physics FPS, memory, school clock, enemy and wolf counts, and the staff log (the last 200 actions).

### Quality of life (1.18)
- **Find a command:** the search box at the top right looks through every tab. Pick a result to jump to its tab; the button gets a gold ring.
- **Favourites:** right-click any button to pin it to a Favourites row at the top of every tab. Right-click again to unpin. Pins last for this session.
- **Recent students:** the last five students you picked float to the top of the list, tagged "recent".
- **Search by UserId:** the student search also matches a UserId exactly.
- **Copy a UserId:** the selected student's UserId sits in a box next to their name, so you can select it and copy it.
- **Row tags:** rows also show NOTE and IN MENU.

### Safety
- **Server-side:** every request is checked on the server, never trusted from the client. It's rate-limited and written to the action log.
- **Confirm twice:** destructive buttons (Kick, Ban, Kill, Shutdown, Clear enemies) need a second click within 3 seconds.

### Verified
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
