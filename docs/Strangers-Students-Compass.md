# Strangers, the Students List, the Compass and the Shift-Lock Cursor: NH Combat Test

**Status:** built and tested with **two real players** (a Studio local server with 2 clients). Some fixes from that run still need one more two-player pass; see "Verified".

## Stranger system
You only see a student's name once you've learned it.

**Over their head** (`Controllers.Gui.Strangers`):
- **Someone you know:** their full name in the UI kit's title font, with the clan in its rarity colour and their faction's seal (the kit's candle / blood-drop icons). Seen from 60 studs.
- **A stranger:** just *Stranger* in faint italic, only within 18 studs, so crowds stay clean.
- Roblox's own name tag is off for every player.

**How you learn a name:**
- **Introductions.** Walk up to a stranger who doesn't know you, and the game's own prompt (PromptUi) offers **[G] Introduce yourself**. They learn your name, and a notification tells them who you are ("A stranger introduced themselves — Ada Lowell."). They can introduce themselves back the same way.
  - The key is **G**, not E, so E still draws your weapon when people are nearby. Equip now ignores prompts that don't use E.
  - The server checks it: you're both in school, within 14 studs, you've signed the register, it isn't a repeat, and there's a 2-second rate limit.
- **Factions.** Members of the same faction know each other.

**Saving:** who you know is saved per student, as `PlayerData.Known = { ["<UserId>:<Slot>"] = true }` (action `SetKnown`, capped at 1000). A save slot is its own student, so your slot II character has to meet people again.

**Names are private.** They no longer go out on public player attributes or `Humanoid.DisplayName`, which every client could read.
- The server (`Services.Social.Strangers`) sends each player only the names they know: `ReplicatedStorage.NHStrangers.Names` carries `{ Known = { [userId] = { Name, First, Clan, Rarity, Faction } }, KnowsMe = { [userId] = true } }`, re-sent whenever it changes.
- The only public flag is `Signed` (true once you've signed the register). The main menu gets your own name from `Controllers.Gui.Identity`.
- Duel messages no longer show account names: "Your opponent went down." / "You went down."

## Students list (replaces Roblox's player list)
- **Replaces Roblox's list:** `Controllers.Gui.Students` keeps Roblox's own list switched off. The main menu no longer turns it back on when you enter school.
- **Closed by default.** **Tab** or the top bar's **Students** button opens it as a narrow ink-and-gold panel under the top bar, at most 40% of the screen tall (it scrolls past that). The same key or button closes it.
- **Grouped by faction:** The Vigil, The Crimson Court, then Unaffiliated. Empty groups are hidden, and each header has a count.
- **Rows:** each row is the UI kit's `PlayerListRow`: student file number, faction seal and full name, with you in gold. A second line shows rank, title and clan rarity.
- **Strangers** show as *Stranger*, with no number and no details.

## Compass (`Controllers.Gui.Compass`)
A slim strip across the top centre, in the top bar's style with faded ends. It shrinks on narrow screens so it never runs into the top bar.
- **Directions:** N, E, S and W in the title font (N in crimson), with ticks every 15°. North is −Z.
- **Places of interest**, each shown only within its range, using existing kit icons:

| Place | From the map | Icon | Range |
|---|---|---|---|
| Classrooms | `RoomId` + `Subject` | quill | 90 studs |
| Faction bases | model with `Faction = <id>` | candle / blood drop | 400 studs |
| Duel ring | model holding `DuelPad` parts | seal | 300 studs |
| Quest NPCs | `NpcPost = <npc id>` | pip | 120 studs |
| Anything else | `Compass = "Label"` (+ `CompassIcon`, `CompassRange`) | any kit image | 200 studs by default |

- **Your tracked quest objective** is always shown in gold, and pinned to the edge when it's behind you.
- **Readout:** whatever you're facing is named under the strip, with its distance in studs.
- **Notifications:** the game's toasts now drop in just under the compass.

## Shift-lock cursor (`Controllers.Gui.ShiftLockCursor`)
- **Design:** a dark wrought-iron ring with gold hour ticks, gold-tipped spear-point finials at the quarters and a crimson diamond, with a dark halo so it reads on bright scenes. It's 44 × 44 pixels.
- **Hook:** it uses Roblox's official one, a `CursorImage` StringValue under the PlayerModule's `MouseLockController`.
- **Art:** `tools/vfx/make_cursor.py`.

## Two-player test (Studio local server, 2 clients)
Each step was run on the two clients and checked on the server, using real keys and clicks unless noted.

| Area | Result |
|---|---|
| Join, loading, menu | Each client got its own loading screen (375 to 391 assets) and its own menu. |
| Saves | Both players picked slot I together. The profiles are separate (different clans and races). |
| Names and clans | Simultaneous spins gave independent results with separate pity. Both signed different names (server test commands). |
| Enter school | Both entered. Names locked; HUD, top bar and lighting came back. |
| Private names | No name attributes. `Humanoid.DisplayName` is "Student". Each client was sent only the names it knows. |
| Introductions | **G/E prompt test:** Player1 held the key on "Introduce yourself", and Player2 got the notification and a green "Ada Lowell" nameplate. Repeats are refused, the result is saved (`-1:1`), and it's one-way until the other student introduces back. |
| Students list | Opened from the top bar with both players listed. Found and fixed: Tab didn't open it, the text was too dark, and Roblox's own list came back after the menu. |
| Compass | Live, with markers. The readout named "Dex Moreno · 95 studs". Found and fixed: it overlapped the top bar on narrow windows. |
| Shift-lock cursor | Shift locked the mouse (`LockCenter`), and `MouseIcon` was the NH cursor. |
| PvP combat | 3 hits took Player2 from 100 to 88 HP. |
| Down, carry, grip | Downed (test command), then **V** carried Player2 on the shoulder while walking. **B** gripped, and the kill was saved (`Kills` = 1). Player2 respawned at school. |
| Duel | Both stood on the pads: countdown, then the duel, with both Protected. A down meant "You won the duel!", and the loser was picked back up. Found and fixed: the account name was shown, and a new countdown started while they still stood on the pads. |
| Leaving | Player2 was disconnected. No server errors, Player1 was unaffected, and its name list updated. |

**Fixed during the run:**
- Nameplates missing when a character spawned: its head arrives a moment late.
- Tab blocked: Roblox marks Tab as already handled.
- The list's gradient dimmed its text.
- Roblox's player list re-enabled by the menu.
- The compass overlapping the top bar.
- E being taken by the introduce prompt: moved to G.
- Two duel problems: account names in messages, and instant rematches.

**Still to check (next two-player run):**
- Those fixes, on fresh code.
- Chat between players. Typing in chat wasn't run, at your request.
- Rejoining after leaving, and that known names persist.
- A discipline report on a witnessed fight.
