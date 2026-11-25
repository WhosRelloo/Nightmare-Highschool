# Chat and Factions panel: iron and candle, quiet (design)

Date: 2026-11-25. Branch `chat-factions-ui` (from `main` at 2.40.0). Place: NH Combat Test, Edit installs, Play checks in slot 2.
Mockups (approved by the owner on 2026-11-25): the "NH Chat Directions" canvas, artboards **Chat: iron and candle, quiet**
and **Factions panel** (https://claude.ai/artifact/FoddZEToJYXSaaU1P8sNKK).

## Goal

Rebuild the top-left chat window and the Factions panel (P) so they share one look: the UI kit's iron frame and candle,
as quiet as the "Whispers" direction. They should be animated, but subtly. Player-facing behaviour stays what it is
today; only the look and motion change.

## Scope

- In: `StarterPlayer.StarterPlayerScripts.Controllers.Gui.Chat`, `StarterPlayer.StarterPlayerScripts.Controllers.Gui.FactionsPanel`,
  and a new shared module, `ReplicatedStorage.UI.Motion`, for the animation helpers both use.
- Out: Roblox's bubble chat (it stays as `Chat.StyleBubbles` sets it), the TopBar, the server side (`Features.ChatAccess`,
  `SocialAction`), the faction data and rules, the other kit screens. `UI.Components` and `UI.Theme` aren't edited;
  anything new goes in `UI.Motion`.

## What stays exactly as it is

Chat (from the 2.1.0 header of `Gui.Chat`):
- Messages go through TextChatService. The bar sends with `TextChannel:SendAsync`, and the window shows
  `TextChatService.MessageReceived`, so filtering, chat commands, `FaceTalk` and the TopBar's unread pip work unchanged.
- Roblox's window and bar stay off. `NHCanChat == false` means no window and no bar; nil shows them.
- / to talk, Enter sends, Esc leaves (the draft stays), and Up / Down recall what you sent. While the bar has focus, no
  game key fires (`Packages.Bind.Typing`).
- The public API: `Shared.Build`, `SetShown`, `IsShown`, `Focus`, `OnStart` and `Preview`, with the same signatures.
  The main menu and the cinematic view still hide it, and the TopBar's Chat button still toggles it.
- `MAX_LINES` 120, `MAX_CHARS` 200, `SEND_GAP` 0.6, and the per-player name inks (you are candle gold). Whispers are
  marked.

Factions panel:
- P and the left-edge Factions button toggle it (touch placement is unchanged), and Close closes it.
- It reads only `PlayerData.Social`, through the same `StateController.ProfileUpdated` re-render.
- It shows the same content in the same order: Reputation (and the equipped title), one card per faction in
  `Config.Factions.Factions` (name, tagline, rank, status, standing, the initiation, mission, activity and perk lines
  as today), Titles (Equip / unequip through `Packets.SocialAction` `EquipTitle`), and Rumours (`Config.Factions.Planned`).
- `Shared.Toggle(Open?)` and `Shared.OnStart` keep their signatures.

## The look

Both screens:
- Iron and candle: a dark panel (`rgba(26,24,28)` to `rgba(14,13,16)`, about 0.92-0.96 opaque) with a fine iron edge
  (`#3d3325`), a candle-gold header (`#e3b45c`) in the kit's display font, and a small lit candle beside the title.
- Body text is the kit's serif in warm off-white (`#e6dfd0`), with dim lines in `#a89f8e`.
- Faction colours come from `Config.Factions` (`Def.Color`), never hard-coded.

Chat:
- **Quiet:** no panel, frame, header or bar, just the lines, each with a soft dark shadow (`TextStrokeTransparency` and
  a faint shadow label) so it reads over any scene. A soft dark vignette sits behind the line block and fades with the
  lines.
- **Awake** (on /, the mouse over the window, or a new message): the panel, the iron edge, the header (channel name,
  candle, count) and the input bar fade up over about 0.25 s.
- **Fading back:** after `IDLE_AFTER` (10 s) quiet with the bar unfocused and the mouse away, the frame fades out over
  about 0.6 s and the lines stay at their quiet opacity. This replaces today's `SetFaded`, which dims the whole window.
- The bar keeps a SEND button (gold), the caret, and the "Say" label.

Factions panel:
- The title is "Who's Who After Dark", with the candle. The Close button is an × in a thin iron box.
- Each faction card has a faint wash of its colour and a fine edge in that colour.
- Rank is shown as five pips (Outsider to Inner Circle), filled up to the player's rank in the faction colour.
- The reputation bar is a slim bar in candle gold.
- Titles are buttons, and the worn one is gold. Rumours are italic and dim.

## Motion

All motion goes through `UI.Motion`. With `Kit.ReducedMotion()` on, every helper sets its end state at once, and
flicker, glow and shimmer don't run.

| Helper | Used for | Motion |
|---|---|---|
| `Motion.SmokeIn(Label, Delay?)` | each new chat line; Rumours lines | from transparent, 8 px left and letter-spaced, to settled, over 0.35 s (Quad Out). A shadow label follows. |
| `Motion.Wake(Group, On)` | the chat frame, header and bar | the group's transparency fades up (0.25 s) or down (0.6 s) together; an interrupted tween is replaced, never stacked. |
| `Motion.Candle(Flame)` | the candle in both headers | a flicker on one Heartbeat-driven loop shared by every candle: size and transparency wobble, about 1.7 s a cycle, stopped when the flame leaves the DataModel or is hidden. |
| `Motion.Glint(Stroke, Base, Lit)` | the chat frame's iron edge; the faction cards' edges | a slow colour breath between two colours, about 5 s a cycle, on the shared loop. |
| `Motion.Rise(Items, Step)` | Factions panel sections on open | each item fades up and moves 6 px up, staggered by `Step` (0.15 s). |
| `Motion.Fill(Bar, Fraction)` | the reputation bar | it fills from 0 over 1.1 s after the panel opens. |
| `Motion.Pips(Pips, Count, Color)` | rank pips | they light one at a time, 0.15 s apart. |
| `Motion.Open(Panel)` / `Motion.Close(Panel)` | the Factions panel | it scales from 0.985 and rises 10 px while fading in over 0.3 s; Close is the reverse over 0.2 s, then hides it. |

The shared loop runs only while something is animating: it disconnects when no candle or glint is registered. One
Heartbeat connection serves both screens.

## Performance and safety

- The chat still caps at `MAX_LINES`. Smoke-in runs only on new lines, never on the backlog when the window is rebuilt.
- One TweenService tween per line at most. No per-frame work while the chat is quiet and idle, except the shared candle
  and glint loop, which stops while the frame is hidden.
- RichText escaping stays (`Local.Escape`). Player text is never formatted as markup.

## Checks

- **Edit:** a `Motion` pure check that runs every helper on a throwaway ScreenGui and asserts end states, with
  ReducedMotion on and off. A preview check: `Chat.Preview` and a new `FactionsPanel.Preview(Gui, Social)` build without
  errors, and their screenshots are compared with the mockups.
- **Play (slot 2, restored):**
  - A chat check (Client): send a message and see it arrive in the window. Then:
    - after `IDLE_AFTER` the frame is hidden and the lines stay;
    - / wakes it and focuses the bar;
    - Esc keeps the draft;
    - Up recalls the last line;
    - `SetShown(false)` hides everything.
  - With `NHCanChat=false` there's no window.
  - A Factions check (Client): P opens it; the reputation bar's end size matches the server's reputation, the pips
    match the rank, and Equip title sends `SocialAction`. With ReducedMotion on, everything is at its end state at once.
  - Screenshots of quiet chat, awake chat, and the open panel go in `docs/superpowers/mockups/2026-11-25-chat-factions-ui/`.
- Every round records cine `PASS` before and after, as usual.

## Install

Use `install_inplace.py`: the orig is a scratch fetch of the three modules as Studio has them, the backup is
`ChatFactionsUI_pre_20261125`, and `UI.Motion` is a new ModuleScript under `ReplicatedStorage.UI`. Edit only.
Mirrors go in `tools/chat-factions-ui/live/`. The place is not saved without the owner's word.
