# Staff console 1a: report

Plan: `docs/superpowers/plans/2026-11-23-admin-console-1a.md`. Spec: `docs/superpowers/specs/2026-11-23-admin-console-design.md`.
Place: NH Combat Test (placeId 98950102230473), slot 2 only. The place is **not saved**: it needs the owner's word.

## Edit checks
- `checks/console_pure.lua`, `console_registry.lua` (66 commands; level 1 = 16, level 2 = 65, level 3 = 66),
  `console_model.lua`, `console_tools.lua`, `console_hold.lua`: PASS after the last install.

## Play checks (Task 8, round 3, after fix round 1)
Run through `run_live.py`, which runs each check as a Script or LocalScript inside the game's own VM (the MCP's
`execute_luau` VMs get a fresh module graph, where `Admin.OnStart` never ran and no profiles are loaded).
- `PASS console_play_run (81 calls)`: 12 level and argument refusals, plus all 66 registry commands through the real
  `Admin.Dispatch` (Kick, Ban, Unban and Shutdown left out: they would end the Play session).
  - State-refused: none (`StateOk` is empty). Start a lesson is tested for success in R102 during Period 1. The brief's R101
    is Homeroom, which has no lesson, so it can never start one (the polish round took it out of the room list).
  - The run always puts slot 2 back (`xpcall`, then `putBack`), even on a timeout: `run_live.py` sets a `Stop` attribute
    rather than destroying the script. Saved values are copied into the existing profile tables in place.
  - Attribute drift fails the run unless it is on the allow-list. Only DetentionsOwed drifted, and `restore.py` puts it back.
- `PASS console_play_client`: the start side and section, 13 Student cards, every Test section drawn, "tp" finds Go to,
  no text under 20 px.
- `PASS console_play_carried` (Task 7 carry-ins): on the phone layout, the rail sink covers 12 card points with 0 leaks,
  and a 144-point grid finds 0 leaks on each overlay; a student who leaves is unpicked.

## Real input (`user_mouse_input`, `user_keyboard_input`)
- Freeze all: a 300 ms hold leaves the feed unchanged; 1100 ms gives "Froze 0 student(s)". Mouse drag-off cancels.
- A and Return on the selected Run: 300 ms doesn't fire, 1100 ms fires. Moving the selection off mid-hold cancels.
- With Freeze all selected, Ctrl+K then holding Return for 1100 ms: nothing fires, and the selection is cleared.
- Key Two goes to Server. Ctrl+K opens the palette. Esc in the palette closes the console (Open = false, NHMenuOpen nil).
- The scroll position holds through the 1 s status refresh.
- Not verified: dragging a finger off (touch), a real gamepad (the MCP sends A as a keyboard key), alt-tab
  (`WindowFocusReleased` cancels; checked in code only).

## Game fixes made during Task 8
- `StaffConsole.Cards` `Hold`: a GuiButton's InputBegan never fires for Return or gamepad A, so A / Return are read from
  `UserInputService` while the Run is selected (ignored while a TextBox has focus, or within 0.25 s of one losing it). Moving
  the pointer or the selection off, or `WindowFocusReleased`, cancels.
- The palette: Esc only dropped the box's focus, so Esc from the palette now closes the console. Opening the palette clears
  the selected console button.
- Backups: `ServerStorage.NH_Backup.StaffConsole_preTask8` and `StaffConsole_preTask8r1`.

## Cutover (Task 9)
- `GamepadControls`: `NHAdminPanel = { Gui, AdminPanel }` became `NHStaffConsole = { Gui, StaffConsole }` (installed in place).
- `Controllers.Gui.AdminPanel` moved (not deleted) to `ServerStorage.NH_Backup.AdminConsole1a_pre_20261123`.
- Re-check: PASS run (81), client and carried. A real F3 press toggles `NHStaffConsole`, and `PlayerGui` has no `NHAdminPanel`.

## Slot 2
CineState, Seen and Origin were nil before and after every Play round (Tasks 7, 8 and 9, and the restore after the
interrupted Task 8 run).

## Outside slot 2
Nothing. In 1a the staff log and staff notes are in memory only (`Admin.luau` Log and Notes), and they are gone when the
server stops. `NHStaffRecords_v1` and `NHStaffLog_v1` are the 1b design (spec §7): no script in the place names them, and
`ListDataStoresAsync("NHStaff")` returns no stores (checked in the final fix round). An earlier draft of this report said
otherwise, and it was wrong.

## Final review fixes (49bc83c)
- Go to a place sends the selected student again (`Target = "optional"`).
- Club has a "None (leave their club)" choice.
- The Inspect remote needs level 2, the same as the console card.
- "No targeting up" is one pure rule, `StaffConsole.CanTarget` (only a higher level is refused), used by Dispatch and Inspect
  and tested in `console_pure`.
- Studio matched every `live/` mirror byte for byte before and after the install.
- Re-check: PASS console_pure, registry (16/65/66), play_server, model, tools; in Play, PASS console_play_run (87 calls),
  console_play_client and console_play_carried. CineState, Seen and Origin were nil before and after.

## Screenshots
`docs/superpowers/mockups/2026-11-23-admin-console/play-{moderate-student,moderate-server,test-character,test-progress,test-school,test-story,test-world,test-spawns,test-self}.png`

## Polish round (branch `admin-console-polish`, 2643e91)
- Give spins uses the Race icon (it was the Gear icon, same as Give gear).
- Lesson rooms come from the timetable rooms that have a subject (`lessonRooms()`): R102-R105. R101 is refused.
- The Start a lesson refusal gives the real reason (already in a lesson, not enrolled, no class in that room now, not in the
  room). A student already in a lesson is now refused; before, the console said "Started".
- Start and Drop a quest pick from `Lists.Quests`. Race rites are listed as "Race rite: ..." but `Run` still refuses them
  below level 3.
- Remove title matches the typed text or its filtered form, so a title the filter changed can still be removed.
- Comments fixed in `Admin.luau`, `Config.Cmdr` and `install_new.py`.
- Checks: PASS console_pure, console_registry (66), play_server; in Play, PASS console_play_run (100 calls, now with the rite gate: level 2 refused on every rite), console_play_client
  and console_play_carried. CineState, Seen and Origin were nil before and after. Backup: `NH_Backup.AdminConsolePolish_20261123`.

## Console art and layout (branch `admin-console-polish`)
- `Config.ConsoleArt` has all 20 uploaded piece ids. Only chips and tabs are 9-sliced (12 px). Every other piece is
  stretched whole: slicing smeared the card's icon well, and Roblox shrinks uploads over 1024 px (Frame, Feed, Rail, Side).
- Layout lined up to the art: the card icon is centred in its well (40 px at 18, 18), with the text to its right and the
  options and Run inside the corner brackets. Chips fit their text. Each student row shows a headshot in its well. Section
  labels are centred, the tiles are wider (the school time fits), and the student search uses the Search art.
- Two fixes for art defects, done in code so nothing needs re-uploading:
  - the Frame upload has a stray brass plate at its centre, which is covered with a patch of the frame's own leather;
  - the TabOn gem is redrawn at its own size on tabs that aren't 150 px wide.
- Checks: PASS console_pure, console_play_client, console_play_carried. CineState, Seen and Origin were nil before and
  after every round. Backups: `NH_Backup.ConsoleArt_pieces*`, `ConsoleLayout_20261123`, `ConsoleLayout2_20261123`.

## Not run
- `graphify update .`: graphify is not installed.

## Phase 1b (branch `admin-console-1b`, plan `docs/superpowers/plans/2026-11-23-admin-console-1b.md`)

### Edit checks (2026-11-24)
- Baseline before 1b: `PASS console_pure`, `PASS console_registry (66 commands)`, `PASS console_model`.
- `PASS records_rules`, `PASS records_store`, `PASS console_pure`, `PASS console_registry (67 commands)`,
  `PASS console_play_server (static: Edit)`.

### Fixes found while running the plan
- `JobKey()`: Studio has a JobId in Edit and Play, so the spec's `day_<n>_studio` key now comes from
  `RunService:IsStudio()`, not from an empty JobId (records_store caught it).
- `FlushLog()` race: the 30 s loop's save could hold entries while a second `FlushLog` returned at once, so
  "flush, then read" missed them (records_play_a round 1: the refused removal and the refused Unban). Now one save
  runs at a time and entries being written stay readable. records_store case 13 covers it.

### Play round, server (Task 3, round 2)
- Cine before: CineState=nil Seen=nil Origin=nil. Fresh slot 2 snapshot (round_start.sh).
- `PASS console_play_server (static: Play)`
- `PASS console_play_run (104 calls)`
- `PASS records_play_a (19 calls)`
- `PASS records_cleanup (removed 8)`
- restore.py, cine after: CineState=nil Seen=nil Origin=nil.
- Round 1 (before the FlushLog fix): console_play_server and console_play_run passed, records_play_a failed 2 of 19
  (the race above), and records_cleanup passed (removed 8).
- Model (Task 4): `PASS console_model`.

### More fixes found while running the plan
- `pre1b/` Cards, View and ConsoleArt had CRLF endings and Studio has LF, so `install_inplace.py` refused them (a long
  bracket turns each CRLF into two newlines). The `pre1b/` copies are now LF; Studio's text matched them line for line.
- View: `(B.Parent :: any).LayoutOrder = ...` at the start of a line is ambiguous Luau (it reads as a call on the line
  before), so the install's parse check refused it. Now `local Holder = B.Parent :: any` first.
- Shell: `run()` calls the history and log fetches, which the plan defined later as locals. They're now declared
  before `run()` and defined after `mustWait()`.
- The History / LogDay read limit was a flat 0.1 s gap, which refused the console's own bursts (a log row opens its
  history at once): records_play_client failed 3. Now at most 8 reads a second per player.

### Play round, client (Task 5, round 2)
- Cine before and after: CineState=nil Seen=nil Origin=nil; fresh snapshot, restore.py at the end.
- `PASS records_play_a (19 calls)`, `PASS console_play_client` (14 Student cards), `PASS records_play_client`,
  `PASS records_cleanup (removed 8)`.
- Round 1 (flat 0.1 s limit): records_play_client failed 3 (a log search and a history read refused as "Slow down",
  so no timeline drawn).

### Restart round (Task 6)
- Session A (fresh snapshot; cine before and after nil/nil/nil): `PASS console_play_run (104 calls)`,
  `PASS records_play_a (19 calls)`. Today's log then held 434 entries over 9 pages.
- Real input, session A:
  - Right-click on Card_Warn (real mouse, `user_mouse_input`): Warn became a favourite.
  - Tab (real key): Moderate to Test, and the store then held `{ Side = Test, Favs = { Warn } }` after 7 s.
  - Key Three opened the Log section. Typing "Warn" into LogSearch plus Return gave "Page 1 of 1 · 8 entries"; clearing
    it gave "Page 1 of 9 · 434 entries".
  - Not by mouse: day chips, filter chips, Prev / Next. A synthetic left click never fires `GuiButton.Activated`
    (tried the Side tab, the Log tab by position and by instance path; none fired). Right clicks and holds work because
    cards and the hold ring listen for InputBegan / InputEnded. Days, chips and paging were driven through the probe
    (records_play_client: Page 2, Refused, Day 1).
- Stop Play, start Play (session B; fresh snapshot; cine before and after nil/nil/nil):
  - `PASS records_play_client (after restart)`: opened on the Test side with Warn still a favourite.
  - `PASS records_play_b`: the open 1-day mute was applied again on join; the note, the lifted ban and the removal
    row read back; the removed warning stayed gone.
  - Remove hold on the timeline (real mouse on `Entry_1.Remove`): 300 ms left 8 entries (cancelled); 1100 ms gave
    "Removed from WhosRello's mutes: Muted (1 day): 1b restart · Saved" and 7 entries.
  - `PASS records_cleanup (removed 7)`; the owner's stored prefs were back to none.
- Two fixes from the screenshots, checked in one more round (`PASS records_play_a`, `PASS records_cleanup (removed 8)`):
  - The summary named only the time ("muted until 04:58") for a mute ending tomorrow. Now it adds the day when it isn't
    today: "muted until Wed 25 Nov 05:06".
  - "· lifted" at the end of a timeline head line was cut off. It now follows the entry text: "7-day ban: 1b test (lifted)".
- Screenshots: `docs/superpowers/mockups/2026-11-23-admin-console/play-1b-log.png`, `play-1b-timeline.png`.

### Crowded cards fixed (2026-11-24)
- Cards whose options don't fit one 230 px row now grow taller (`Cards.Card`): the options wrap onto 332 px rows under
  the help text, and Run sits beside the last row when it has room, else under it. `View` stacks each row of cards by its
  tallest card. Ban is 202 px tall, Mute 244, Remove history entry 246; the rest stay 168.
- `console_play_client` now also checks, on Student, Server and every Test section, that each option is inside its card
  and clear of Run, Run is inside the card, no two cards overlap, and Ban, Mute and Remove history entry use the tall
  layout: `PASS console_play_client`. Slot 2 restored; cine nil/nil/nil before and after.
- Screenshots: `docs/superpowers/mockups/2026-11-23-admin-console/play-1b-cards-ban.png`,
  `play-1b-cards-mute-remove.png`.
- The plan's decisions (its "Spec deltas") were approved by the owner on 2026-11-24.

### Open issues for the owner
- ~~Removing a mute entry doesn't lift the mute.~~ Fixed in phase 2 (2026-11-24, see below): removing a mute that is
  still on lifts it, unless another mute on the record is still on.
- graphify isn't installed, so `graphify update .` wasn't run.

## Phase 2 (branch `claude/admin-console-2-895704`, plan `docs/superpowers/plans/2026-11-24-admin-console-2.md`)

19 new cards (18 server, 1 client tool), so 85 server commands, plus the TRANSFORMED, WANTED, NEW and IN CUTSCENE flags
and the new context-card lines. Spec: `docs/superpowers/specs/2026-11-24-admin-console-2-design.md`. Backup in Studio:
`ServerStorage.NH_Backup.AdminConsole2_20261124`. The place is not saved; that needs the owner's word.

### Edit checks (2026-11-24, after the final install)
`PASS console_registry (85 commands)`, `PASS console_pure`, `PASS console_model`, `PASS console_play_server`,
`PASS console_tools`, `PASS console2_lineage`.

### Play round (slot 2, final)
- `PASS console_mute_remove`: an active mute removed lifts it, two mutes with one removed still mutes, an ended mute
  changes nothing, and a ban entry removed doesn't unban. The staff record is put back.
- `PASS console2_play_run (41 calls)`: every phase 2 card through `Admin.Dispatch`, including:
  - level 2 refused on Season, Moon and Sky in live-server mode;
  - Set Bells 4 bringing the monitors;
  - Hall monitors off, then on;
  - a replay that writes nothing;
  - a tutorial enter, then jumps to Garden, Fence and Bus, then leave;
  - Give a clue, then Reset a case.
- `PASS console2_play_client`: Preview just for me changes only your own sky, and the four flags draw.
- `PASS console_play_run (104 calls)` and `PASS console_play_client`, the 1a/1b checks, still pass. Both are
  order-dependent:
  - `console_play_run` failed once on a dare that wasn't open at that clock time, and passed on the rerun.
  - `console_play_client` needs a fresh Play with the staff prefs cleared and the Prologue finished. It failed in a
    dirty session and passed fresh.
- **Slot 2** is Human. Form direction was tested by making it a Vampire at Tier I for the check, then putting that back.
  The saved FormDirection went from nil to "2", then "1", then back to nil.
- **Slot 2 cine state:** `{Prologue=Seen}` before the round. Another session's Play had run the Prologue. It is empty
  after the round, with Seen and Origin nil, as in 1b. The staff prefs are put back to `{Side=Test, Favs={}}`.
- **Screenshots:** in `docs/superpowers/mockups/2026-11-23-admin-console/`: `play2-test-world.png`,
  `play2-test-story.png`, `play2-test-school.png`, and `play2-row-flags.png` (WANTED).

### Fixes found while running the plan
- Moon tonight: a non-Full moon counts the next full moon from tomorrow. SetMoon refuses when there is no school clock.
- Tutorial: jump to always resumes the student at the mark, and names the mark (or says it couldn't place them).
- The NEW flag and the inspector no longer break the list when a service is missing.
- Form direction called a helper before it was defined, so it now gets the profile directly. A replayed cutscene no
  longer leaves a Started or Seen mark.
- Final review:
  - Set Heat 0 and Set Bells 0 keep owed summons, so only Clear notoriety drops them.
  - Set Bells puts Heat at the middle of the bell (17.5, 35, 57.5, 80, 100), so the first cooling tick doesn't drop a bell.
  - Preview just for me can show Autumn.
  - The checks now put back the clock, the club, race hunger and the Bells attributes.
- 1b open issue: removing a mute entry that is still on lifts the mute, and the log says so.

### For the owner
- Heat cools fast (about 1.5 a second while searched, 3 a second once quiet), so a bell set from the console lasts
  only seconds unless a monitor sees the student. That's the game's tuning, not a console bug.
- Hall monitors on/off is a whole-server change, but in live servers it is level 2 plus a hold. Only Season, Moon and
  Sky are owner-only, as the spec says.
