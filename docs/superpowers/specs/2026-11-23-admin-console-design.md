# The Headmaster's Console: admin panel rebuild (design)

- **Status:** design approved by the owner in chat on 2026-11-23 ("go ahead with the admin panel design"); reviewed the
  same day, and the 8 review picks taken as recommended ("Continue"), folded in below (§2b). Plan for phase 1a:
  `docs/superpowers/plans/2026-11-23-admin-console-1a.md`.
- **Replaces:** the 1.8 / 1.18 "Headmaster's Desk" (`Controllers.Gui.AdminPanel`, `Services.Features.Admin`; doc
  `docs/Admin-Panel.md`). Every one of its 66 commands keeps working, with the same server checks.
- **Mockups:** `docs/superpowers/mockups/2026-11-23-admin-console/` (`moderate-student.png`, `test-world.png`,
  `inbox.png`, `palette.png`).

## 1. Why

The desk was built at 1.18. Since then the game gained the Bell Tower (notoriety, bells, summons, hall monitors), the
tutorial and cutscenes, sky seasons and moons, transformations, Quiet Corners, gestures and more, and none of it is in the
panel. The desk is also hard to read: 9 tabs of identical buttons at 14-16 px, one long scroll per tab, and a tab bar
that can highlight the wrong tab.

## 2. Owner decisions (2026-11-23)

| Question | Decision |
|---|---|
| Who is it for | **Both, split clearly:** a **Moderate** side for staff (live players) and a **Test** side for the owner and testers |
| New tools | **All of:** world & atmosphere, story & cutscenes, Bell Tower & discipline, live server tools |
| Look | **Gothic command console:** dark iron and velvet, crimson and brass trim, big readable text, icon cards, live status tiles |
| History | **Saved across servers:** notes, warnings, ban history and the staff action log, per player, in a DataStore |

## 2b. Review picks (2026-11-23)

| # | Point | Pick |
|---|---|---|
| 1 | Phase 1 too big | Split: **1a** the console, the registry, the 66 commands, levels 0-3, the in-memory log and session favourites; **1b** the saved records, the Log section and saved favourites (§8) |
| 2 | Studio = level 3 for all | Stays the default; a Studio-only `NHTestLevel` attribute (0-3, server-set) plays any level (§6) |
| 3 | Where level 2 comes from | `Config.Cmdr` only: `Admin` and a new `Testers` list; no `Config.Admin` (§6) |
| 4 | The daily log key | One key per server per day, `day_<n>_<JobId>`; Test actions kept 7 days (§7) |
| 5 | Danger list | + Server lock, Bring all, Quest reset, Regions reset (§5) |
| 6 | Mutes | TextChatService gate as today; saved with an end time, applied again on join until it runs out (1b) |
| 7 | Icons | Done: 49 icons with ids in `art/ui/hud/console/icons/icon_ids.json` (§9) |
| 8 | Report feedback | The reporter gets a "Thanks, staff will look" slip only; no status (§7) |

Also: the auto-flag thresholds live in config (`Config.Staff.Flags`), not code.

## 3. Layout

```
┌ top bar ─────────────────────────────────────────────────────────────────────────────────────────┐
│ crest  MODERATE | TEST   [players 14] [fps 60] [12:30 After School] [Waning moon] [Autumn] [lock] │
│                                                    on duty: 3     [Ctrl+K  Find any action…]     │
├ left rail ────────┬ centre: the section ──────────────────────────────────┬ right: context ───────┤
│ search students   │ section tabs (icons + names, 22 px)                    │ the selected student  │
│ ▸ recent (pinned) │ ┌ card ┐ ┌ card ┐ ┌ card ┐                             │ Moderate: history     │
│ row: portrait,    │ │ icon │ │ icon │ │ icon │  title 22 px                │ timeline (saved)      │
│ name, race crest, │ │title │ │title │ │title │  one-line help 20 px        │ Test: live stats      │
│ level, ping,      │ │chips │ │chips │ │chips │  option chips inline        │ (race, tier, Heat,    │
│ flags             │ └──────┘ └──────┘ └──────┘                             │ bells, quests, Yen)   │
│                   │ results feed (last 5 actions, this session)            │                       │
└───────────────────┴────────────────────────────────────────────────────────┴───────────────────────┘
```

- **Size:** 1600 x 900 design px, scaled with the UI kit; text never under 20 px (titles 22-26, help 20).
- **Look:** iron panel frame with brass rivets, velvet card faces, crimson for danger, brass for the active tab, the
  school crest top left. Built from `UI.Components` plus new console art (§9).
- **Flags on a row:** REPORTED, NOTE, MUTED, FROZEN, IN MENU, TRANSFORMED, WANTED (Bell 3+), NEW (first session).
- **Status tiles** update every second from `Info()`; clicking one jumps to its section (the clock to School, the moon to
  World, the lock to Server).

## 4. The two sides and their sections

The switch shows only what your level allows (§6). Each section is a grid of action cards; a card is one action with
its options inline.

### Moderate (staff)
| Section | Cards |
|---|---|
| **Inbox** | player reports (newest first, with the reporter, reason, a chat excerpt and the time); auto-flags (more than 6 knockdowns by one player in 60 s; the same chat line 4 times in 30 s; a kick or ban refused by the API); Claim, Resolve, Dismiss; a resolved report writes to the target's history |
| **Student** (needs a target) | Warn (reason templates + free text), Mute / Unmute (with a duration), Freeze, Jail (detention), Spectate, Bring, Go to, Kick (reason), Ban (1d / 7d / 30d / Permanent, owner-only permanent), Note |
| **Server** | Announce, Server lock, Bring all, Freeze all / Thaw all, Shutdown (owner), health graphs (FPS, memory, ping) over the last 10 minutes |
| **Log** | the saved staff action log: search by staff, target or action; filter by day; open a row to see its target's history |

### Test (owner and testers)
| Section | Cards |
|---|---|
| **Character** | Heal, Revive, God mode, Kill, Speed; Race and sub-race, Tier, Height (spin / shortest / average / tallest), Build; **Transform** and **Form direction** (new); Give Yen, EXP, Spins, Name change, Gear |
| **Progress** | Set level, Stat points, Titles, Places found (all / reset), Clubs, the read-only inspector |
| **School** | Set time / clock speed / skip to a period / ring the bell / start a lesson; Discipline points, Excuse today, Lift suspension, Owe / Clear detention; **Bell Tower (new):** set Heat, set Bells 0-5, trigger a summons, clear notoriety, hall monitors on or off, show who's Wanted |
| **Story (new)** | Start / drop / reset quests; case clues and insights (grant, reset a case); **play any cutscene** (first viewing or replay) and **mark Seen / clear**; **tutorial** enter, jump to a checkpoint (Garden, Fence, Bus), leave |
| **World (new + moved)** | Time presets (Dawn, Noon, Golden, Dusk, Midnight, Witching); **Season** (Autumn, Winter, Spring, Summer, Nightmare); **Moon** (Full, Waxing, Waning, New, Crimson, Blue); **Sky** override and Storm; **"Preview just for me"** toggle (sets the preview attributes on your client only); Go to a place (all regions, or send the target) |
| **Spawns** | Delinquent crew / one by role, Wolf pack, Sparring partner (Easy-Nightmare), each Beast, Clear all enemies (with the alive count) |
| **Self** | Fly, Noclip, ESP, Ctrl+click teleport, Invisible, Stop spectating, the staff teleport flock |

## 5. Interaction

- **Command palette:** Ctrl+K (or the search box) finds any action by name, description or synonym ("tp" finds Go to).
  Enter runs it on the selected student; options open inline.
- **Favourites** are saved per staff member (DataStore, §7) and pinned above every section. Right-click (or long-press
  on touch, Y on a controller) pins or unpins.
- **Danger:** Kick, Ban, Kill, Shutdown, Clear enemies, Freeze all, Server lock, Bring all, Quest reset and Regions
  reset use **hold-to-confirm** (0.8 s ring), never a double-click. Permanent ban asks for a reason.
- **Results** arrive as slips (the Quiet Corners slips) and in the results feed; a refusal says why.
- **Keyboard:** F3 opens and closes; 1-7 switch sections; Tab switches Moderate / Test; arrows move through cards.
- **Controller:** LB / RB sections, D-pad cards, A run, X options, Y favourite.
- **Phone:** the rail becomes a drawer; cards stack in one column; the context card opens as a sheet.
- **Reduce Motion:** no card hover lift, instant section changes.

## 6. Permissions (all checked on the server)

| Level | Who | Gets |
|---|---|---|
| 0 | everyone else | nothing, and no hint the console exists |
| 1 Moderator | group rank 254 | Moderate side; temporary bans up to 30 days |
| 2 Admin | `Config.Cmdr.Admin` or `Config.Cmdr.Testers` (new list in the same file) | + the Test side in live servers |
| 3 Owner | rank 255+ or `Config.Cmdr.Owner` | + permanent bans, Shutdown, Yen over ¥100k, race rites |

- In Studio everyone is level 3 (as today), unless the server set `NHTestLevel` (0-3) on them: then that level, to
  check a staff level in Studio. The old `NHTestNotAdmin` (Fx flocks) still means level 0.
- `NHStaff` (the staff clothing kit) and Fx's flocks keep reading "level 1 or more" = staff, so 0-3 changes nothing for
  them.
- No targeting up: nobody can target someone of a higher level.
- Every request is rate-limited and logged (§7); every Test action in a live server is logged too.

## 7. Data

### The command registry (`ServerScriptService.Services.Features.Admin`, `Commands` table)
Each command: `Id`, `Side` (Moderate / Test), `Section`, `Title`, `Help` (one line), `Icon`, `Level`, `Target`
(none / required / optional), `Args` (a schema: `{ Name, Kind = "number"|"text"|"choice"|"toggle", Min, Max, Choices,
Default }`), `Danger` (bool), `Synonyms`, `Run(Admin, Target, Args) -> ok, message`. The server sends the registry
(without `Run`) in `Info()`; the client draws cards from it, so a new command is one registry entry.
The 66 existing commands move into it unchanged; the new ones are listed in §4.

### Saved records (new `ServerScriptService.Services.Features.StaffRecords`)
- DataStore `NHStaffRecords_v1`, key `u_<UserId>`: `{ Notes = { {By, At, Text} }, Warnings = { {By, At, Reason} },
  Bans = { {By, At, Days, Reason, Lifted?} }, Mutes = { ... }, Reports = { {Id, From, At, Reason, State} } }`, capped
  at 50 entries per list (oldest dropped).
- DataStore `NHStaffLog_v1`, key `day_<n>_<JobId>` (one per server per day, so servers never fight over a key): that
  server's staff actions `{ At, Staff, Action, Target?, Detail }`, capped at 2000. A `day_<n>` index key lists the
  JobIds that wrote that day. The console reads today and the last 6 days; Test actions are not kept past 7 days.
- DataStore `NHStaffPrefs_v1`, key `u_<UserId>`: favourites and the last side used.
- Writes go through UpdateAsync with retries; a failed write keeps the entry in memory and retries on the next one.
  The console shows "History unavailable" if a read fails, never an empty history.

### Reports (new)
- Players report from the phone's menu (Report a player: pick the player, a reason, optional text). The last 20 chat
  lines from that player in this server are attached. Rate limit: 3 reports per player per 10 minutes. The reporter
  gets a "Thanks, staff will look" slip and never a status (so a report can't be used to check on someone).
- Mutes are saved with an end time and applied again when the player joins, until they run out.
- Open reports reach every staff member in the server (an Inbox badge) and are saved to the target's record.
  Cross-server delivery (MessagingService) is in scope for phase 3.

## 8. Phases (each one playable and tested before the next)

1. **1a, the console and the registry:** the new shell (top bar, rail, sections, cards, palette, hold-to-confirm), the
   registry, all 66 commands migrated, levels 0-3, the in-memory log (as today) and favourites for the session.
   **1b, saved records:** `StaffRecords` (notes, warnings, bans, mutes), the saved log and the Log section, saved
   favourites and last side.
2. **The new Test tools:** World (seasons, moons, sky, preview for me), Story (cutscenes, tutorial, cases), the Bell
   Tower cards, Form direction.
3. **Reports:** the player Report flow, the Inbox, auto-flags, MessagingService delivery, health graphs.

## 9. Art

Generated in the Quiet Corners pipeline (`art/ui/hud/`), uploaded by the owner to group 15981569:
console frame (4 quadrants, 1024 max), card face and card face hover, section tab and tab-on, status tile, rail row,
hold-ring, icons (one per section and per card family, 64 px). Fallbacks: the UI kit draws every piece until
its id exists.
**Made (2026-11-23):** 20 pieces in `art/ui/hud/console/*.png` (not uploaded yet) and 49 icons, uploaded, ids in
`art/ui/hud/console/icons/icon_ids.json` and `ICONS.md`.

## 10. Testing

- **Pure (Edit VM):** registry shape (every command has Id, Section, Title, Help, Level, Args schema), args
  validation (out-of-range numbers, unknown choices refused), permission matrix (each level sees and runs exactly
  its commands; no targeting up).
- **Play:** every migrated command run once through the remote with its result checked (the 1.18 test list), on
  slot 2 with a fresh snapshot and restore; records saved and read back across a server restart (Studio: two Play
  sessions); the palette finds every command; hold-to-confirm cancels when released early.
- **Visual:** screenshots of each section on desktop; the owner's mobile session covers phone.
- **Not testable in Studio alone:** cross-server reports, real bans (the Ban API is refused in Studio and kicks instead).

## 11. Out of scope

Appeals, a web dashboard, Discord webhooks, and editing other staff's permissions in-game.
