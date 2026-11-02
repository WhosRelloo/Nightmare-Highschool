# Admin Panel: the Headmaster's Desk (NH Combat Test)

Added in 1.8 (2026-11-02). It's a staff panel built only from the game's UI kit (Panel, TabBar, Buttons, Search, Toggles, Sliders, Section headers) with the school crest. Press **F3** to open it.

## Who can open it
- Group rank **254+** in the owning group, the `Config.Cmdr` admin and owner lists, and **anyone in Studio**.
- **Owner-only:** shutdown, permanent bans, and Yen grants over ¥100k. These need the owner rank or `Config.Cmdr` owner.
- **Everyone else** gets nothing, not even a hint that the panel exists.
- **No targeting up:** staff can't target someone of a higher rank.

## Files
| Where | What |
|---|---|
| `ServerScriptService.Services.Features.Admin` | The back end: permission checks, rate limits, the action log, every command |
| `StarterPlayerScripts.Controllers.Gui.AdminPanel` | The panel UI (F3) |
| `ReplicatedStorage.NHAdmin` | Remotes: `Info()` returns `{ Level, Players, Server, Log, Gear, Places }`; `Run(Command, TargetUserId?, Args)` returns `ok, message` |

The Luau sources are kept outside this repo (the repo holds no `.luau` files).

Other UI can open the desk by setting the player attribute `NHAdminOpen` to `true`, `false` or a tab number. The server still decides who gets in.

## Tabs
- **Students:** search, health, race, ping, and tags for owner, staff, muted, frozen and god mode.
- **Moderation:**
  - Warn (with a reason), mute and unmute (blocks chat on every channel), and freeze.
  - Send to detention, spectate, and kick.
  - Ban through the Roblox ban API (in days; permanent bans are owner-only), and unban by UserId.
- **Student:**
  - Heal, revive, god mode, transform, bring, go to, clear the disciplinary record, kill, and a walk-speed slider.
  - Give Yen, Combat EXP, lineage spins or a name change.
  - Give any of the 40 gear pieces (listed by rarity colour).
- **World:** set the school clock (or Morning, Noon, Midnight), set the clock speed, send a server-wide announcement, or shut down the server (owner-only).
- **Spawns:** a delinquent crew, a wolf pack (night only), a sparring partner, or clear all enemies.
- **Self:** fly (WASD, Space, Ctrl, Shift for speed), noclip, ESP (names and health through walls), Ctrl+click teleport, invisibility, heal, and stop spectating.
- **Server:** students, uptime, physics FPS, memory, school clock, enemy and wolf counts, and the staff log (the last 200 actions).

## Safety
- **Server-side:** every request is checked on the server, never trusted from the client. It's rate-limited and written to the action log.
- **Confirm twice:** destructive buttons (Kick, Ban, Kill, Shutdown, Clear enemies) need a second click within 3 seconds.

## Verified
**[PT]** Every command was run in Studio on the spare save slot (slot II), and any data it changed was restored.
