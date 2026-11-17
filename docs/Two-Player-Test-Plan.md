# Two-Player Test Plan: NH Combat Test

Run as a Studio **local server with 2 clients** (Test tab → Clients and Servers → 2 Players → Start). Studio shows three windows: the Server plus Player1 and Player2. Each one is driven separately.

Each check is marked **[S]** server state, **[C1]** / **[C2]** a client, or **[B]** both clients.

## 1. Join, loading screen and main menu
- [ ] [B] Each client gets its own loading screen and counter, and both reach the menu (`NHLoaded`).
- [ ] [B] Each menu shows its own player's students. Neither sees the other's MenuScene copies.
- [ ] [S] Both players have `InMainMenu = true` and no character until they pick a slot.

## 2. Save slots at the same time
- [ ] [C1] and [C2] pick a slot at almost the same moment. Both load (`Slot` set, profiles loaded) with no lock errors.
- [ ] [S] The two profiles are separate (different keys, different Yen, Lineage and Identity).
- [ ] [B] Each creator stage shows only its own player. Each client's character sits on the stage on its own screen. **Known design question:** both use the same Creator stage position, so they overlap in world space.

## 3. Names and clans
- [ ] [B] Both spin their clan at the same time. Each gets its own result, and pity counts stay separate.
- [ ] [B] Both sign different names. Overhead `DisplayName` shows the right full name to the *other* player once in school.
- [ ] [B] Rate limits: spam-spinning on one client doesn't affect the other.

## 4. Entering school
- [ ] [B] Both enter. The HUD, top bar, camera and lighting come back on both.
- [ ] [B] Each sees the other's character in the school, in the right outfit (uniform vs avatar), with the right face.
- [ ] [S] `Players.CharacterAutoLoads = false` and both respawn after death.

## 5. Top bar and chat
- [ ] [C1] chats and [C2] receives it. With chat hidden on [C2], the unread pip appears.
- [ ] [B] The Students list shows both players (CoreGui PlayerList).

## 6. Combat between players
- [ ] [C1] hits [C2] with M1: damage and posture apply, and [C2]'s HUD updates.
- [ ] [C2] blocks and parries [C1].
- [ ] Downed: [C1] downs [C2]. Carry (V) moves [C2], and grip (B) executes. Kill credit (`Kills`) goes to [C1].
- [ ] A disconnect while being carried leaves no stuck state on the carrier.
- [ ] Discipline: a witnessed fight during school hours reports the right player.

## 7. Quests and social
- [ ] PvP duel (Settle It): [C1] challenges [C2], both get the duel. The winner and loser are recorded correctly.
- [ ] Faction standing changes on one player don't leak to the other.
- [ ] A quest object picked up by [C1] still works for [C2] (per-player state).

## 8. Leaving
- [ ] [C2] leaves mid-session. [S] releases the profile with no errors, and [C1] is unaffected.
- [ ] [C2] rejoins the same slot. The data persisted (name, clan, outfit).

## 9. The repeatable harness (Phase 0, 2.22.0)

A fixed run to use after every phase of the expansion plan (`docs/expansion/08-Roadmap.md`). It uses only `ServerStorage.NHTestBridge` commands in the **Server** window, plus the slot remotes in each client window, so it can be repeated exactly.

**Setup:**
- **Studio:** Test tab → Clients and Servers → **2 Players** → Start.
- **Who loads:** the test players are `Player1` and `Player2` (UserIds -1 and -2, Studio data only). Never load the owner's real students.
- **Server window:**
  ```lua
  B = game.ServerStorage.NHTestBridge
  ```
- **Each client window:** enter school.
  ```lua
  local S = game.ReplicatedStorage.NHSlots
  S.List:InvokeServer()
  S.Choose:InvokeServer(1)
  S.Enter:InvokeServer()
  ```
  Then set `workspace.CurrentCamera.CameraType = Enum.CameraType.Custom`.

| # | Check | How | Pass when |
|---|---|---|---|
| H1 | One clock | `B:Invoke("SetTime", "19:45")` | Both ClockHuds read 7:45 PM. 3 wolves spawn (the Prowl window). `workspace.NHMoonNight` is false until 20:00. |
| H2 | Night proper | `B:Invoke("SetTime", "20:30")` | `NHMoonNight` is true within 5 s on both clients. Night races get their night effects. |
| H3 | Night chill | `B:Invoke("SetTime", "21:30")`, then both stand on the Field for 60 s | Both are `NHChilled`, except Vampires and Wraiths. |
| H4 | Morning | `B:Invoke("SetTime", "05:45")`, then `"12:00"` | 05:45: it's still night, wolves start leaving, lamps stay lit. 12:00: everything is off. |
| H5 | Introductions | `B:Invoke("Introduce", "Player1", "Player2")`, then `B:Invoke("Strangers", "Player2")` | Player2 knows Player1's name. Player1 still sees Player2 as a Stranger. |
| H6 | Clique standing sync | `B:Invoke("CliqueAdd", "Player1", "Ink", 10)` | Player1's client copy of `Social.Cliques.Ink` changes in the same second. Player2's doesn't. |
| H7 | Talk camera | Both players talk to Ezra at the same moment (real E presses) | Both get the over-shoulder shot. When they leave, both cameras return to Custom at their own FOV setting. |
| H8 | Enrol step | `B:Invoke("EnrolSelfTest", "Player1")` | Returns StageNew = Enrol, StageAfterEnrol = Class, StageEnrolled = Class, MigratedOldStage2 = Leader, MigratedTwice = Leader, DeskTagged = 1. The quests come back unchanged. |
| H9 | Combat between them | Player1 hits Player2 with M1. Player1 downs them (`B:Invoke("Damage", ...)` or real hits), then carries (V) and grips (B). | Damage, carry and grip as in section 6. `Kills` goes to Player1. |
| H10 | Disconnect | Close Player2's window mid-carry, then rejoin the same slot | No server errors, Player1 isn't stuck, and Player2's data is back. |

**Result log:** add a row under Results with the date, version, the H-numbers that passed, and any failure with its console line.

## Results
(filled in during the run)
- 2026-11-17 (2.22.0): H1-H4 and H8 were run **with one player** on slot 4 "Testy" (the MCP can only start a one-player Play). The full two-client run still needs Studio's 2 Players test, started by hand.
