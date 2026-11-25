# The Staff Console, phase 2: the new Test tools and row flags (design)

Status: design approved in chat by the owner (2026-11-24), section by section, then the written spec. The plan and its 9 spec deltas were approved the same day. Plan:
(`docs/superpowers/plans/2026-11-24-admin-console-2.md`).
Parent spec: `docs/superpowers/specs/2026-11-23-admin-console-design.md` (§4 Test side, §8 phase 2). This file narrows
and settles that spec for phase 2. Where they differ, this file wins for phase 2.
Builds on: main at 739067a (phases 1a and 1b merged). Branch: `claude/admin-console-2-895704`.

## 1. Owner decisions (2026-11-24)

| Question | Decision |
|---|---|
| How to ship | **One phase, grouped:** the new Test cards (World, Story, Bell Tower, Forms) and 4 row flags. The approved list (§2) is 19 cards; "about 20" was the estimate |
| Who may change the world for a whole live server | **The owner only.** In live servers, testers (level 2) get "Preview just for me". In Studio everyone can do both |
| Fourth row flag | **IN CUTSCENE** (with TRANSFORMED, WANTED and NEW). REPORTED waits for phase 3 |
| Where the new cards live | **Group modules** beside Admin, merged into the registry (§3) |

## 2. The new cards (19)

The registry has 67 entries today (the 66 commands plus 1b's Remove history entry). Phase 2 adds 19, so 86 in all.
Every card is level 2 unless it says otherwise. "Target" is as in the parent spec §7.

### World (Test / World)
The existing Go to a place and Full moon tonight cards stay as they are.

| Id | Title | Target | Args | Notes |
|---|---|---|---|---|
| `TimePreset` | Time preset | none | `Preset` choice: Dawn, Noon, Golden, Dusk, Midnight, Witching | Sets the school clock, like Set time. The hours come from `Config.DayCycle` keys |
| `SetSeason` | Season | none | `Season` choice: Autumn, Winter, Spring, Summer, Nightmare | Sets `workspace.NHSeason` (Autumn = nil). **Server-wide** |
| `SetMoon` | Moon tonight | none | `Moon` choice: Full, Waxing, Waning, New, Crimson, Blue | Crimson and Blue set `NHMoonEventTonight`; the four phases set tonight's Lineage phase. **Server-wide** |
| `SetSky` | Sky | none | `Sky` choice: Auto, Storm | Sets `workspace.NHSky` (Auto = nil). **Server-wide** |
| `PreviewForMe` | Preview just for me | none | `Season`, `Moon`, `Sky` choices, each with "Off" | **Client only** (§3.4): `Meta.Local = true`, so the console runs it on your client and never calls Dispatch. Its server `Run` refuses ("This runs on your own screen") |

**Server-wide** cards are level 2 in Studio and level 3 in live servers. Testers in live servers still see the card, but
it is refused with "Owner only in live servers; use Preview just for me". This works like the race rites.

### Story (Test / Story)

| Id | Title | Target | Args | Notes |
|---|---|---|---|---|
| `PlayCutscene` | Play a cutscene | optional (you, or the selected student) | `Id` choice (from the cutscene list); `Replay` toggle, default on | Replay saves nothing. With Replay off, it is a real first viewing and writes progress as the game does |
| `CutsceneSeen` | Cutscene seen | required | `Id` choice; `Mark` choice: Seen, Clear | Writes the Cine state for that cutscene |
| `TutorialEnter` | Tutorial: enter | required | none | `Tutorial.Enter` |
| `TutorialJump` | Tutorial: jump to | required | `Checkpoint` choice: Garden, Fence, Bus | Sets the checkpoint, then resumes there |
| `TutorialLeave` | Tutorial: leave | required | none | `Tutorial.Leave(P, "Staff")` |
| `GiveClue` | Give a clue | required | `Case` choice; `Clue` choice (that case's clues) | `Investigation.Grant` |
| `ResetCase` | Reset a case | required | `Case` choice | **Danger** (hold). Clears that case's clues, links and deduction |

### Bell Tower (Test / School)

| Id | Title | Target | Args | Notes |
|---|---|---|---|---|
| `SetHeat` | Set Heat | required | `Heat` number 0-100 | Re-tiers the Bells and runs the normal escalation |
| `SetBells` | Set Bells | required | `Bells` choice 0-5 | Sets Heat to that bell's threshold (`Config.Notoriety`), then as Set Heat. Bell 4 really brings the monitors |
| `GiveSummons` | Give a summons | required | `Type` choice (misdeed types) | Adds a summons. The cap of 3 holds |
| `ClearNotoriety` | Clear notoriety | required | none | **Danger** (hold). Heat 0, Bells cleared, summons dropped (none booked) |
| `HallMonitors` | Hall monitors | none | `On` toggle | Off: the monitors stand down and despawn. On: they spawn again. **Danger** (hold), both ways |
| `WhosWanted` | Who's Wanted | none | none | Lists the students at Bell 3 or more, with Heat and state, in the results feed |

### Character (Test / Character)

| Id | Title | Target | Args | Notes |
|---|---|---|---|---|
| `FormDirection` | Form direction | required | `Direction` choice: 1, 2 (the chips show the race's names) | Sets `Looks.FormDirection`, as the Look slot does |

### Row flags and the context card
- **New flags:** TRANSFORMED (the `Transformation` character attribute), WANTED (`NHBells` 3 or more), NEW (first
  session, from the profile) and IN CUTSCENE (`NHCinePlaying` for them, or `NHTutorial`).
- **The Test context card** adds Heat, Bells, bell state, summons owed, form direction and the tutorial checkpoint.

## 3. How it's built

### 3.1 Group modules
- New server modules, children of `Features.Admin`: `Admin.World`, `Admin.Story` and `Admin.BellTower`. Each returns
  `{ [Id] = { Meta = { ... }, Run = function(Admin, Target, Args) -> ok, message } }`, with `Meta` in the `Admin.Meta`
  shape.
- At start, Admin merges each group into its `C` table and into the Meta it sends. A clash with an id already taken
  stops the start with an error, so it can't pass silently.
- `FormDirection` is one entry, so it goes in `Admin.luau` and `Admin.Meta` directly.
- Dispatch, levels 0-3, "no targeting up" (`StaffConsole.CanTarget`), rate limits, the staff log, favourites and the
  palette don't change. A new card is a registry entry, as the parent spec §7 says.

### 3.2 The live-server owner rule
One shared helper, `ServerWide(Admin) -> ok, reason`: allowed in Studio, and allowed in a live server only at level 3.
`SetSeason`, `SetMoon` and `SetSky` call it first. It is pure and tested at every level, in Studio and live.

### 3.3 Small additions to the game systems
Public calls only. Nothing else in these systems changes.
- **`Services.School.Notoriety`:** `SetHeat(P, Heat)` (clamped 0-100; re-tiers, publishes the attributes and runs
  `Escalate`, as a rise does), `Clear(P)` (Heat 0, state and summons cleared, nothing booked) and
  `AddSummons(P, Type)` (the existing internal add, made public).
- **`Services.School.HallMonitor`:** `SetEnabled(On)` and `IsEnabled()`. Off ends every chase, despawns the monitors and
  stops new spawns. On spawns them again. Mirrored to `workspace.NHMonitorsOff = true` while off.
- **`Services.Quests.Investigation`:** `ResetCase(P, CaseId)` (that case's clues, links and deduction).
- **The World cards** set the attributes the sky already reads (`NHSeason`, `NHMoonEventTonight`, the Lineage phase,
  `NHSky`). No change to the sky code.

### 3.4 Preview just for me
It runs only on the client: the console sees `Meta.Local` and runs the card itself, so it is not in the staff log. It sets `NHSeasonPreview`, `NHMoonPhasePreview` and `NHSkyPreview` on your own player, and
"Off" removes them. Nothing goes to the server.
- The plan's first step checks whether `Controllers.World.DayCycle` (and SkyMotion, FullMoon and MoonPhases) read
  these attributes only in Studio. If so, the gate opens to players whose console level is 2 or more.
- Crimson and Blue need an event-moon preview attribute (`NHMoonEventPreview`) if none exists. That is a small
  addition to the sky's moon pick.

### 3.5 Lists and flags
- `Admin.Lists()` adds: Cutscenes (from `ReplicatedStorage.Cinematics`, without the `__` test cuts), Cases and each
  case's Clues (`Config.Cases`), Misdeeds (`Config.Notoriety`), and FormDirections per race (`Config.Forms`).
- The player list Admin already builds adds `Transformed`, `Bells`, `BellState`, `Summons`, `InCutscene` and `New`.
  The inspector adds `Heat` and the tutorial checkpoint. `StaffConsole.Model.Flags` draws the four new flags.

### 3.6 Before any change
The repo's mirrors may be stale. The plan pulls fresh copies of every script it touches from Studio first, into
`tools/admin-console/pre2/`. Installs use the existing `install_inplace.py` / `install_new.py`, with a backup in
`ServerStorage.NH_Backup` first.

## 4. Refusals, safety and logging
- **Refusals say why.** For example: "Owner only in live servers; use Preview just for me", "They have no form at
  Tier I", "Not in the tutorial", "No such clue in that case", "They're in a cutscene already".
- **Danger (hold to confirm):** Reset a case, Clear notoriety, Hall monitors (on or off). Season, Moon and Sky don't need a
  hold: they are owner-only in live servers and easy to undo.
- **Logging:** every new card except Preview just for me goes to the saved staff log through Dispatch, as today. The World cards log the old and
  the new value, so a change can be put back.

## 5. Testing
- **Pure (Edit VM):** registry shape for the 19 new ids, no clashes, 86 in all; `PreviewForMe` is the only `Local` card; `ServerWide` at levels 0-3 in Studio
  and live; argument checks (Heat out of range, an unknown clue, a bad checkpoint); the flag rules.
- **Play (`run_live.py`, slot 2, snapshot and restore):** every new card through the real `Admin.Dispatch`, including:
  Set Bells 4 bringing the monitors; Hall monitors off, then on; a cutscene replay that writes nothing; a first viewing
  that marks Seen, then Clear; tutorial enter, jump to each checkpoint, then leave; Give a clue, then Reset a case;
  Form direction 1 and 2; and level 2 (`NHTestLevel`) refused on Season, Moon and Sky in a live-server mode.
- **Slot 2 and the server put back:** CineState, Seen, Origin, `Discipline.Summons`, the case data and
  `Looks.FormDirection` are compared before and after. `NHSeason`, `NHSky`, the moon and the monitors are restored at the
  end of the run.
- **Client:** Preview just for me changes your own sky only, the 4 flags show, and the context card has its new lines.
- **Screenshots:** the World, Story and School sections, and a flagged row.

## 6. Studio rules
- Place NH Combat Test (98950102230473), slot 2 only. Never save, close, reload or revert without the owner's word.
- Another session (Soccer 2.0) uses the same place. No Play or install while the owner says soccer work is in Studio.
  Every install or Play round starts only after checking with the owner.
- Local commits only.

## 7. Out of scope
Reports, the Inbox, auto-flags, health graphs and the REPORTED flag (phase 3). New sky art. A body for the Headmaster.
