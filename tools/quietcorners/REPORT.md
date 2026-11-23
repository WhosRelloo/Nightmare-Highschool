# Quiet Corners: Studio day report (2026-11-23, NH Combat Test, slot 2)

## S1: hand-over, dump, rebase, backup, facts

- Studio was free (Edit). Fresh dump of 15 scripts into `pre/`. Every client controller in `base/` matches `pre/` byte for byte
  (ignoring line endings), so no rebase was needed. `UI.Settings`: live differs from pre only by the four HudMode additions.
- Backup: `ServerStorage.NH_Backup.QuietCorners_pre_20261123`, 14 clones (`harness/_backup.lua`).
- Facts:
  1. `StarterPlayerScripts.Loader` (LocalScript) runs `ReplicatedStorage.ModuleLoader`, which requires each controller and spawns its
     `OnStart`. New modules under `Controllers.Gui` (HudState, EvidenceWall) start automatically.
  2. `Packets.Notify` and `Packets.DialogueEvent` are `Packet.Any`: open tables, extra fields pass. No schema edit.
  3. `Quests.Quests` line 1003: `elseif Action == "Link" and typeof(Message.Case) == "string" then Investigation.Link(Player, Message.Case, Message.A, Message.B)`.
  4. `StatsPanel.Toggle` and `SettingsMenu.Toggle` both exist (the book's Record and Settings tabs call them).
  5. Clue objects are parts with the `QuestObject` attribute (= the object id; `Config.Objects[id].Clue` names the clue), found with
     `Places.Find("QuestObject", id)`. Mapping a clue back to its object is not wired, so "Mark it" stays hidden (EvidenceWall's TODO).

## S2: pure rules and the red round

- `qc_pure` (Edit VM, after installing Functions.QuietCorners and the three art configs): PASS.
- Red round (Play, fresh snapshot): `qc_state` -> `FAIL no NHQuietProbe`, as expected before the client code. Restored.

## S3: round A (QC1, QC2)

Installed in Edit: UI.Settings, SettingsMenu, HudState, KitHud, TopBar, Notifications, PromptUi, Compass, CineUI (no PARSE FAIL).
First pass: every probe check failed `no NHQuietProbe`. Cause: HudState parented the probe (a BindableFunction) to PlayerGui once in
OnStart, and the respawn on EnterSchool clears PlayerGui. Fix: HudState re-creates the probe after each CharacterAdded. Also fixed:
`harness/server.py` put a real newline inside a Lua string literal (parse failure); it now writes `\n`.
After the fix (same round, HudState re-installed):
- `qc_state`: PASS (note: "cut forced (NHCineUI not built yet)").
- `qc_slips`: PASS.
- `server.py qc_notify_server.lua`: `sent`; `probe.py Slips`: `Shown` = ["Clue found", "Queued B", "Queued A"].
- `qc_prompts`: PASS, after moving the second test prompt from 9 to 7 studs. In this place the engine never fired PromptShown for a
  prompt 9 studs away (MaxActivationDistance 15, AlwaysShow, no line of sight); at 7 studs both show. A test geometry change, not a PromptUi change.
- `qc_compass`: PASS.
- R1's `bt_contracts`: timetable hooked, panel for Moments, hidden, card at default Y (200), shown again, card under cluster: all true;
  the in-class line false (outside a class period, as expected).
- `qc_fit`: PASS (Notifications 6, NHCompass 3, QuestJournal 1, NHTopBar 0).
Restored, stopped.
