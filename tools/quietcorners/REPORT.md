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
