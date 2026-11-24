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
    is Homeroom, which has no lesson, so it can never start one (the console's room list still offers it).
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

## Not run
- `graphify update .`: graphify is not installed.
