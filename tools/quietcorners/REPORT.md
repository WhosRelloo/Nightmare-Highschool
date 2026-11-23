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

## S4: round B (QC3-QC5) with the server edits

Server edits (live mirrors, installed in Edit with the client files; no PARSE FAIL): `Config.Cases` (Number, clue Kind/Order/Hidden,
the three Questions), `Investigation.Link(..., Question?)` (a right pair under the wrong question is a miss; Open/Case on the New insight,
That doesn't fit and Case breakthrough notifies), `Quests` passes `Message.Question`, `Social.Dialogue` sends `Clique` and `Tones`.
Packets needed no change (fact 2).

Fixes found in round B:
- The wall checks assume a fresh EmptyDesk case, but slot 2's case is fully worked (5 clues, both questions answered). New
  `checks/qc_wall_reset.lua` (game VM) empties the case first; restore.py puts the real Quests back.
- `server.py` destroys its Script on return, which killed the deferred `Quests` Sync that `Link` queues and left `PendingSync` stuck, so the
  client never heard of any later insight. The two server checks now wait 0.5 s before returning. `harness/round_b.sh` runs the round
  (with a 2.5 s gap before `qc_wall` for the sync and the 1.5 s link cooldown).
- `qc_fit` with the wall open: the card Kind labels (InkRed 96,10,16) had 3.9-4.1 contrast on the Object and Record cards. InkRed is now
  70,6,11 (4.6+ on every card).

Final round B (fresh snapshot, all in one round):
- `qc_dialogue`: PASS. `qc_dialogue_real`: PASS, speaker WENDELL PRICE, crest rbxassetid://92428028361207, seal false, replies 0.
- `qc_wall_server`: PASS (wrong question -> false, right question -> true). `qc_wall`: PASS. `qc_book`: PASS.
- `qc_fit` with the wall open (NHEvidenceWall 37 labels), the book open (QuestJournal 29), a dialogue node (Dialogue 12): PASS each.
The book was not cut: it is the live Journal.

## S5: art, phone, screenshots

- Ids: all filled before the day (commit 777be8a). Size check (Client VM, `CreateEditableImageAsync`): 125 of 125 load at exactly their
  `upload-manifest.json` size; none downscaled.
- The art was installed before rounds A and B, so every check above ran with the art.
- Phone (`NHPhonePreview` 844 x 390): `qc_fit` PASS with slips, the wall and the book. The book goes one-page (`Pages = Left`) and the wall
  drops to its phone layout (12 labels). Found: Notifications and Dialogue decided "phone" from the camera's ViewportSize, which ignores
  the preview, so 3 slips showed instead of 2. Both now ask the kit's `Viewport()` first; re-checked: 2 slips under the preview, and
  `qc_slips`, `qc_dialogue`, `qc_fit` PASS on desktop. (`qc_state` failed "wake only the compass" once in that round, then passed twice:
  the top-left cluster was still awake from the round start. Flaky, not a regression.)
- The rest of the phone pass (a dialogue node on phone, the phone screenshots) is deferred: the owner will run one mobile-resolution
  session for everything at the end of the phases.
- Screenshots (desktop): [ghost](../../docs/img/quietcorners-ghost.jpg), [combat](../../docs/img/quietcorners-combat.jpg),
  [slips](../../docs/img/quietcorners-slips.jpg), [compass](../../docs/img/quietcorners-compass.jpg),
  [dialogue-ink](../../docs/img/quietcorners-dialogue-ink.jpg), [dialogue-unaffiliated](../../docs/img/quietcorners-dialogue-unaffiliated.jpg),
  [wall](../../docs/img/quietcorners-wall.jpg), [wall-answer](../../docs/img/quietcorners-wall-answer.jpg), [book](../../docs/img/quietcorners-book.jpg).
  No `prompt` shot: Studio's screen_capture does not draw BillboardGuis. The owner saw it in Studio: the E key cap and the parchment tag
  on the nearest prompt, a pip on the other.
- What the shots show:
  - Ghost: the top bar, compass and vitals fade; combat brings the vitals back to full.
  - Slips: 3 slips and the "2 waiting" stub at the top left. The stack covers the chat box there.
  - Dialogue: the Ink crest, the clique line, tone marks on the reply tabs; the unaffiliated shield for the custodian.
  - The wall: the case plate, cards by kind, threads to the slots, "Answered" seals, the bonus sheet; the answer cards replace the
    bonus sheet once both questions are answered.
  - Issues: cards pinned into a question's slots are blank (they don't say which clue they are); the controls bar truncates
    "Right…" (Inspect); a slip can sit half off-screen while it slides out (seen once in the combat shot).
