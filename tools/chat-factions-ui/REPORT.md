# Chat and Factions UI: report (2026-11-25)

Branch `chat-factions-ui`. Spec: `docs/superpowers/specs/2026-11-25-chat-factions-ui-design.md`.
Plan: `docs/superpowers/plans/2026-11-25-chat-factions-ui.md`.

**Place not saved.** Everything is installed in NH Combat Test (Studio) only.

## Install

Installed with `install_inplace`; no PARSE FAIL, MISSING or CHANGED SINCE lines.
Backup: `ServerStorage.NH_Backup.ChatFactionsUI_pre_20261125`.

| Module | Size |
|---|---|
| `ReplicatedStorage.UI.Motion` (new) | 11568 bytes |
| `StarterPlayer.StarterPlayerScripts.Controllers.Gui.Chat` | 28281 bytes |
| `StarterPlayer.StarterPlayerScripts.Controllers.Gui.FactionsPanel` | 18187 bytes |
| `StarterPlayer.StarterPlayerScripts.Controllers.Gui.QuestJournal` | 43564 bytes |

## Final round

Studio: NH Combat Test, Play round on studio a6945a86-d556-46f2-87fa-476b87c8c2dc (Studio was restarted mid-day; the
earlier id b9e911b4-... closed). Every check passed.

| Check | Output |
|---|---|
| cine (before) | `PASS CineState=nil Seen=nil Origin=nil` |
| `buttons_play` | `PASS buttons_play` |
| `factions_play` | `PASS factions_play` |
| `motion_play` | `PASS motion_play` |
| `chat_play` | `PASS chat_play` |
| cine (after restore) | `PASS CineState=nil Seen=nil Origin=nil` |
| `motion_edit` (Edit, after Play stopped) | `PASS motion_edit` |

Restore: `restored` (slot 2 from the pre-round snapshot). Play stopped.

## Screenshots

- Quiet chat, after about 13 s idle: only the line "Rello  chat check 6481" with a soft dark band behind it. No frame,
  header or bar. No left-edge Factions or Journal buttons.
  ![quiet chat](../../docs/superpowers/mockups/2026-11-25-chat-factions-ui/chat-quiet.jpg)
- Awake chat, after `Chat.Focus()`: iron frame, gold HALLWAY header with the candle, the line, and the "Press / to talk..."
  bar with SEND.
  ![awake chat](../../docs/superpowers/mockups/2026-11-25-chat-factions-ui/chat-awake.jpg)
- Factions panel, about 3 s after `FactionsPanel.Toggle(true)`: "Who's Who After Dark" plaque, x close, candle top-left,
  Reputation with "Title: Night Owl" and four bars (Popularity 100, Intimidation 100, Trust 12, Academics 5), The Vigil
  card in its gold wash, Outsider with 1 of 5 pips lit.
  ![factions open](../../docs/superpowers/mockups/2026-11-25-chat-factions-ui/factions-open.jpg)

## Deviations from the plan

All decided by the controller.

- Candle art lives in `Theme.SubGames` (`CandleBody` / `CandleFlame`), not `Theme.Images`. Both candles are same-size
  overlay squares with the flame anchored at its wick tip (208/256), per Theme.luau's anchor note.
- `Motion.Candle` flickers size and brightness (`ImageColor3`), not `ImageTransparency`, so panel fades own transparency
  (the flame used to pop lit during a close).
- `Motion.Open`, `Close` and `Rise` record fade bases first and hide with zero-length tweens. `Open` starts its fade one
  Heartbeat later (overlapping Open and Rise used to leave sections invisible, and Open's fade used to be lost).
- `Motion.Fill` and `SmokeIn` cache their built targets. `Motion.Pips` sets the exact colour when a pip's tween completes.
- The chat's quiet vignette is sized to the line block (it used to be window-sized and sat below a single line).
- The left-edge Factions and Journal buttons are hidden (owner request, Task 4).
- The checks compare float properties with tolerances.

## Testing side effects

- `factions_play`'s unequip step clears the equipped title. It was put back each round ("Night Owl", confirmed).
- One Play round was cut short when the Studio MCP link died (a stale admin StudioMCP held the hub port). Slot 2 was
  unchanged and was restored from the pre-round snapshot.

## For the owner

- How the look feels in motion, including whether the open-panel animation feels right.
- The candle's speed and size. It is small: about 17 px in the chat header and about 20 px on the panel.
- Whether the quiet chat's dark band reads over bright scenes.
