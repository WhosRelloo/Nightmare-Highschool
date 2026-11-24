# Staff Console, Phase 1b Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** the console remembers:
- saved player records (warnings, notes, bans, mutes) with a history timeline;
- a saved, searchable staff log with its own Log section;
- saved favourites and the last side;
- mute lengths, owner-only permanent unbans and owner-only, logged removal of history entries.

**Architecture:**
- **Pure rules** in a new shared `ReplicatedStorage.Functions.StaffRecords`: the record shape and 50 cap, mute end times,
  the unban rule, log keys and the Test cutoff, the log entry shape and 2000 cap, merging, filtering and paging, prefs
  cleaning. Tested in the Edit VM.
- **A new server service** `ServerScriptService.Services.Features.StaffRecords` owns the three DataStores (`[Test] `
  prefix in Studio): records (straight writes, 3 tries, a pending list), the buffered log (saved every 30 s and on
  close) and prefs (saved 5 s after the last change). Its store calls go through one getter, so an Edit check runs it
  against fake stores.
- **`Features.Admin`** writes records from Warn, Note, Mute, Unmute, Ban and Unban, adds `RemoveRecordEntry`, logs
  every `Dispatch` call, re-applies open mutes on join, and adds four remotes (`History`, `LogDay`, `Prefs`,
  `SavePrefs`).
- **The client** gains a history timeline in the right-hand panel, a Log section on the Moderate side, a Length choice
  on Mute, a ban preview on Unban, and favourites and the side that persist.

**Tech Stack:** Luau, Roblox DataStoreService, the UI kit (`ReplicatedStorage.UI.Components`), the 1a harness in
`tools/admin-console/` (`rbxc.py`, `install_new.py`, `install_inplace.py`, `run_check.py`, `run_live.py`, `shot.py`).

**Spec:** `docs/superpowers/specs/2026-11-23-admin-console-1b-design.md` (this plan follows it; where it settles
something the spec leaves open, that is listed under "Spec deltas" below). Parent spec:
`docs/superpowers/specs/2026-11-23-admin-console-design.md`.

**Where:** worktree `E:/NH-admin`, branch `admin-console-1b` (1a plus the polish round plus the art commit, then the 1b
spec). Every path below is relative to `E:/NH-admin` unless it starts with a drive.

## Global Constraints

- **Studio:**
  - NH Combat Test (placeId 98950102230473) only.
  - One session drives it at a time.
  - Never save, close, reload or revert the place without the owner's word.
  - Use slot 2 only.
  - Take a fresh snapshot at the start of every Play round and restore only from it.
  - Record CineState, Seen and Origin before and after every Play round.
- **Stores:** in Studio every store name starts with `[Test] ` (the `Player.Data` / `Social.Superlatives` pattern). A Play
  check refuses to run unless `StaffRecords.PREFIX == "[Test] "`. Play checks remove their own record entries at the end.
- **Commits:** commit only when the owner says so; every commit message ends with
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Text:** never under 20 design px (titles 22-26).
- **Layout:** design size 1600 x 900, scaled with `Kit.AutoScale` (unchanged from 1a).
- **Security:**
  - Every request is checked on the server; the four new remotes check the level first (level 1).
  - No targeting up (`StaffConsole.CanTarget`) on every record command and on reading someone's history.
  - Text other players see goes through `TextService` filtering (Dispatch already filters `Reason` and `Text`).
- **Owner decisions (spec §1):**
  - Mute lengths: 10 min, 1 h, 1 day, Until unmuted.
  - A permanent ban can be lifted only at level 3; a ban of 30 days or less from level 1.
  - Removing history entries: level 3 only, and every removal is logged.
  - The saved log is buffered per server and saved in batches.
- **Caps:** 50 entries per record list (oldest dropped); 2000 entries per log key (oldest dropped); log `Detail` 120
  characters; 50 log rows per page; the log reads today and the 6 days before; Test-side log keys removed after 7 days.
- **Timings:** record writes 3 tries with backoff (1 s, 2 s); pending writes retried every 30 s; history and log days
  cached 60 s; log saved every 30 s and in `BindToClose`; prefs saved 5 s after the last change and on leave.
- **Danger (hold-to-confirm, 0.8 s):** the 1a list plus `RemoveRecordEntry`.
- **Install:**
  - Changed scripts go in place with `install_inplace.py tools/admin-console/pre1b tools/admin-console/live
    AdminConsole1b_20261123 <Dotted.Path> ...` (it refuses if Studio differs from `pre1b/`).
  - New modules go in with `install_new.py <live file> ...`.
- **Out of scope (spec §7):** reports, the Inbox and auto-flags (phase 3); MessagingService delivery (a mute or ban set
  in one server reaches a player elsewhere only when they next join); health graphs; new Test tools (phase 2).

## Spec deltas (settled by this plan; approved by the owner 2026-11-24)

1. **Bans over 30 days** need level 2 to lift (the spec covers 0 and 1-30; this matches who may set them).
2. **The log skips two refusals:** `Not staff` and `Slow down`. They would let anyone flood the 2000-entry key.
   Every other run or refused call is logged.
3. **Log entries carry `StaffId` and `TargetId`** as well as the names, so search by UserId and "open a row" work.
4. **Note needs text.** The 1a "empty clears it" goes: notes are history now, and only `RemoveRecordEntry` takes one
   away.
5. **A new target mode `"user"`:** a picked UserId, online or not. Only `RemoveRecordEntry` uses it. Warn, Note, Mute
   and Ban still need the student in the server.
6. **An offline UserId's staff level** comes from `Config.Cmdr` and the group rank (`GroupService:GetGroupsAsync`,
   cached 10 min). If the lookup fails, it counts as level 3, so no targeting up fails closed.
7. **A failed record read on join leaves the player unmuted** for that visit, with a warning in output. They are
   muted again on their next join.
8. **`Admin.TestSkipBanApi`** (Studio only) lets the Play checks write ban records without calling the Roblox Ban API
   or kicking the only player.
9. **`LogDay` filters and pages on the server** (`Filter = { Query, Chip, Page }`), so a busy day never crosses the
   remote whole.
10. **Mute stores its choice as `Minutes`** (10, 60, 1440, 0).
11. **Bans and mutes that ended on time are greyed** like lifted ones (marked "ended" instead of "lifted").

## File structure

| Path (under `tools/admin-console/`) | What |
|---|---|
| `live/ReplicatedStorage.Functions.StaffRecords.luau` | new, pure, shared: record, log and prefs rules |
| `live/ServerScriptService.Services.Features.StaffRecords.luau` | new, server: the three stores, cache, pending list, log buffer, day reads, prefs |
| `live/ReplicatedStorage.Functions.StaffConsole.luau` | modify: `SECTIONS.Moderate` gains `Log`, `CARDLESS`, target mode `user` |
| `live/ServerScriptService.Services.Features.Admin.Meta.luau` | modify: Mute `Minutes`, Note needs text, Unban help, `RemoveRecordEntry` |
| `live/ServerScriptService.Services.Features.Admin.luau` | modify: record writes, `RemoveRecordEntry`, logging, `LevelOf`, mute on join and expiry, 4 remotes |
| `live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.Model.luau` | modify, pure: offline pick, prefs, timeline, summary, Unban note, log labels |
| `live/...Controllers.Gui.StaffConsole.Cards.luau` | modify: choice `Labels`, `Cards.Chip`, a card `Note` line |
| `live/...Controllers.Gui.StaffConsole.View.luau` | modify: the Log section, the history timeline, offline header, Unban note |
| `live/...Controllers.Gui.StaffConsole.luau` | modify: the new remotes, history and log fetches, prefs, handlers, probe |
| `pre1b/` | new: copy of `live/` before 1b (what Studio runs now; `install_inplace.py` compares against it) |
| `checks/records_rules.lua` | new, Edit: the pure rules |
| `checks/records_store.lua` | new, Edit: the service against fake stores |
| `checks/console_pure.lua`, `checks/console_registry.lua`, `checks/console_model.lua`, `checks/console_play_server.lua` | modify |
| `checks/console_play_run.lua`, `checks/console_play_client.lua` | modify |
| `checks/records_play_a.lua`, `checks/records_play_b.lua`, `checks/records_cleanup.lua` | new, Play, server |
| `checks/records_play_client.lua` | new, Play, client (through the `NHQuietProbe` probe) |
| `REPORT.md` | add the 1b section |

`(...)` = `StarterPlayer.StarterPlayerScripts`. As in 1a, child modules (`StaffConsole.Model` and the rest,
`Admin.Meta`) have no `OnStart`. `Features.StaffRecords` is a service: the loader requires it and calls its `OnStart`.

---

### Task 0: Baseline

**Files:**
- Create: `tools/admin-console/pre1b/` (a copy of `tools/admin-console/live/`)

- [ ] **Step 1: Check the worktree**

```bash
cd E:/NH-admin
git status -sb
git log --oneline -3
```
Expected: `## admin-console-1b`, clean, HEAD is `Console 1b spec: ...` on top of `Staff console: wire the uploaded art ...`.

- [ ] **Step 2: Snapshot the mirrors**

```bash
cp -r tools/admin-console/live tools/admin-console/pre1b
```

- [ ] **Step 3: Baseline checks (Edit)**

```bash
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_pure.lua
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_registry.lua
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_model.lua
```
Expected: `PASS console_pure`, `PASS console_registry (66 commands)`, `PASS console_model`. If one fails, Studio is not on
the 1a + polish + art build: stop and tell the owner.

---

### Task 1: The pure record rules (`Functions.StaffRecords`, TDD)

**Files:**
- Create: `tools/admin-console/live/ReplicatedStorage.Functions.StaffRecords.luau`
- Test: `tools/admin-console/checks/records_rules.lua`

**Interfaces:**
- Produces (every later task uses these names):
  - constants `CAP = 50`, `LOG_CAP = 2000`, `DETAIL_MAX = 120`, `FAVS_MAX = 40`,
    `LISTS = { "Notes", "Warnings", "Bans", "Mutes" }`, `KIND = { Notes = "Note", Warnings = "Warn", Bans = "Ban", Mutes = "Mute" }`,
    `MUTE_CHOICES = { 10, 60, 1440, 0 }`, `MUTE_LABELS = { "10 min", "1 h", "1 day", "Until unmuted" }`
  - `Blank() -> Record`; `Normalize(V: any) -> Record`; `Push(Rec, List, Entry) -> Rec`
  - `MuteUntil(Minutes, Now) -> number`; `MuteOn(M, Now) -> boolean`; `OpenMute(Rec, Now) -> Entry?`; `MuteLabel(M) -> string`
  - `BanOn(B, Now) -> boolean`; `OpenBan(Rec) -> Entry?`; `UnbanLevel(Ban?) -> 1|2|3`
  - `Find(Rec, List, At, By) -> number?`; `Remove(Rec, List, At, By) -> Entry?`; `EntryText(List, E) -> string`
  - `Summary(Rec, Now, Clock?: (number) -> string) -> string`; `Timeline(Rec) -> { { List, Kind, Entry, Seq } }` (newest first)
  - `Day(Now) -> number`; `LogKey(Day, Job, Test?) -> string`; `IndexKey(Day, Test?) -> string`; `TestCutoff(Day) -> number`
  - `LogEntry(F) -> { At, Staff, StaffId, Action, Target?, TargetId?, Detail, Side, Ok }`; `CapLog(L) -> L`
  - `MergeDay(Lists) -> { Entry }` (each list oldest first; result newest first; on a tie the later list wins)
  - `LogMatch(E, Query?, Chip?) -> boolean`; `Page(Rows, Page, Per) -> (Rows, Page, Pages)`
  - `CleanFavs(Favs, Known?: { [string]: true }) -> { string }`; `CleanSide(Side) -> "Moderate"|"Test"|nil`
  - `Record = { Notes = { {By, At, Text} }, Warnings = { {By, At, Reason} }, Bans = { {By, At, Days, Reason, Lifted?} }, Mutes = { {By, At, Until, Reason?, Lifted?} }, Reports = {} }`,
    each list oldest first; `Lifted = { By, At }`.

- [ ] **Step 1: Write the failing check**

`tools/admin-console/checks/records_rules.lua`:

```lua
local Mod = game.ReplicatedStorage:FindFirstChild("Functions") and game.ReplicatedStorage.Functions:FindFirstChild("StaffRecords")
if not Mod then return "FAIL Functions.StaffRecords missing" end
local R = require(Mod:Clone())
local Fails = {}
local function Eq(Got, Want, What) if Got ~= Want then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end

-- the record shape and the cap of 50
local Rec = R.Normalize(nil)
for _, L in { "Notes", "Warnings", "Bans", "Mutes", "Reports" } do Eq(typeof(Rec[L]), "table", "blank has " .. L) end
local N2 = R.Normalize({ Warnings = { { At = 5; By = 1 }, "junk", { By = 2 } }; Notes = "junk" })
Eq(#N2.Warnings, 1, "normalize keeps only entries with At") Eq(#N2.Notes, 0, "normalize drops a list that isn't a table")
for I = 1, 51 do R.Push(Rec, "Warnings", { At = I; By = 1; Reason = "w" .. I }) end
Eq(#Rec.Warnings, 50, "cap 50") Eq(Rec.Warnings[1].At, 2, "oldest dropped first") Eq(Rec.Warnings[50].At, 51, "newest last")

-- a mute's end time and whether it is still on
Eq(R.MuteUntil(10, 1000), 1600, "10 min") Eq(R.MuteUntil(60, 1000), 4600, "1 h")
Eq(R.MuteUntil(1440, 1000), 87400, "1 day") Eq(R.MuteUntil(0, 1000), 0, "until unmuted")
Eq(R.MuteOn({ At = 1000; Until = 1600 }, 1599), true, "on before the end")
Eq(R.MuteOn({ At = 1000; Until = 1600 }, 1600), false, "off at the end")
Eq(R.MuteOn({ At = 1000; Until = 0 }, 1e9), true, "until unmuted stays on")
Eq(R.MuteOn({ At = 1000; Until = 0; Lifted = { By = 1; At = 1100 } }, 1200), false, "lifted is off")
local M = R.Blank()
R.Push(M, "Mutes", { At = 1; By = 1; Until = 0; Lifted = { By = 1; At = 2 } })
R.Push(M, "Mutes", { At = 3; By = 1; Until = 700 })
Eq(R.OpenMute(M, 500) and R.OpenMute(M, 500).At, 3, "open mute found")
Eq(R.OpenMute(M, 800), nil, "an ended mute is not open")
Eq(R.MuteLabel({ At = 0; Until = 600 }), "10 min", "label 10 min")
Eq(R.MuteLabel({ At = 0; Until = 86400 }), "1 day", "label 1 day")
Eq(R.MuteLabel({ At = 0; Until = 0 }), "Until unmuted", "label until unmuted")

-- the unban rule
Eq(R.UnbanLevel({ Days = 0 }), 3, "permanent needs 3")
Eq(R.UnbanLevel({ Days = 7 }), 1, "7 days needs 1") Eq(R.UnbanLevel({ Days = 30 }), 1, "30 days needs 1")
Eq(R.UnbanLevel({ Days = 90 }), 2, "over 30 days needs 2")
Eq(R.UnbanLevel(nil), 3, "no ban on record counts as permanent")
local B = R.Blank()
R.Push(B, "Bans", { At = 10; By = 1; Days = 0; Lifted = { By = 1; At = 20 } })
R.Push(B, "Bans", { At = 30; By = 2; Days = 7 })
Eq(R.OpenBan(B) and R.OpenBan(B).At, 30, "the latest unlifted ban")
B.Bans[2].Lifted = { By = 1; At = 40 }
Eq(R.OpenBan(B), nil, "no open ban when all are lifted")
Eq(R.BanOn({ At = 0; Days = 7 }, 6 * 86400), true, "a 7-day ban is on at day 6")
Eq(R.BanOn({ At = 0; Days = 7 }, 8 * 86400), false, "and ended at day 8")
Eq(R.BanOn({ At = 0; Days = 0 }, 1e9), true, "permanent stays on")
Eq(R.BanOn({ At = 0; Days = 0; Lifted = { By = 1; At = 5 } }, 10), false, "lifted is off")

-- find and remove by At + By, and the text an entry shows
local F = R.Blank()
R.Push(F, "Notes", { At = 5; By = 1; Text = "a" }) R.Push(F, "Notes", { At = 5; By = 2; Text = "b" })
Eq(R.Find(F, "Notes", 5, 2), 2, "find by At and By")
local Gone = R.Remove(F, "Notes", 5, 2)
Eq(Gone and Gone.Text, "b", "remove returns the entry") Eq(#F.Notes, 1, "one left")
Eq(R.Remove(F, "Notes", 9, 9), nil, "a missing entry")
Eq(R.EntryText("Bans", { Days = 7; Reason = "spam" }), "7-day ban: spam", "ban text")
Eq(R.EntryText("Bans", { Days = 0 }), "Permanent ban", "permanent ban text")
Eq(R.EntryText("Mutes", { At = 0; Until = 3600; Reason = "caps" }), "Muted (1 h): caps", "mute text")
Eq(R.EntryText("Warnings", { Reason = "" }), "Warned", "empty warning text")
Eq(R.EntryText("Notes", { Text = "hi" }), "hi", "note text")

-- the summary line and the timeline
local S = R.Blank()
R.Push(S, "Warnings", { At = 1; By = 1; Reason = "a" }) R.Push(S, "Warnings", { At = 2; By = 1; Reason = "b" })
R.Push(S, "Warnings", { At = 3; By = 1; Reason = "c" })
R.Push(S, "Bans", { At = 4; By = 1; Days = 7; Lifted = { By = 1; At = 5 } })
R.Push(S, "Mutes", { At = 6; By = 1; Until = 1000 })
Eq(R.Summary(S, 10, function(T) return "@" .. T end), "3 warnings · 1 ban (lifted) · muted until @1000", "summary")
Eq(R.Summary(R.Blank(), 10), "No history", "empty summary")
local OnBan = R.Blank()
R.Push(OnBan, "Bans", { At = 0; By = 1; Days = 0 })
Eq(R.Summary(OnBan, 10), "1 ban (active)", "active ban summary")
local TL = R.Timeline(S)
Eq(#TL, 5, "timeline has every entry") Eq(TL[1].Kind, "Mute", "newest first") Eq(TL[5].Entry.Reason, "a", "oldest last")

-- log keys, the Test cutoff (day n-7), the entry shape, the cap of 2000
Eq(R.Day(86400 * 3 + 5), 3, "day number")
Eq(R.LogKey(3, "job"), "day_3_job", "log key") Eq(R.LogKey(3, "job", true), "test_day_3_job", "test log key")
Eq(R.IndexKey(3), "day_3", "index key") Eq(R.IndexKey(3, true), "test_day_3", "test index key")
Eq(R.TestCutoff(20), 13, "test cutoff n-7")
local E = R.LogEntry({ At = 9; Staff = "mod"; StaffId = 1; Action = "Warn"; Target = "kid"; TargetId = 2; Detail = string.rep("x", 200); Side = "Weird"; Ok = 1 })
Eq(#E.Detail, 120, "detail cut to 120") Eq(E.Side, "Moderate", "an unknown side is Moderate") Eq(E.Ok, false, "Ok must be true")
Eq(E.TargetId, 2, "target id kept") Eq(E.StaffId, 1, "staff id kept")
Eq(R.LogEntry({ Side = "Test"; Ok = true }).Side, "Test", "the Test side kept")
local Big = {}
for I = 1, 2005 do Big[I] = { At = I } end
local Capped = R.CapLog(Big)
Eq(#Capped, 2000, "log cap 2000") Eq(Capped[1].At, 6, "the oldest log entries dropped") Eq(Capped[2000].At, 2005, "the newest kept")
local Merged = R.MergeDay({ { { At = 1; Action = "a" }, { At = 3; Action = "c" } }, { { At = 2; Action = "b" }, { At = 3; Action = "d" } } })
Eq(Merged[1].Action, "d", "merge: newest first, the later list wins a tie") Eq(Merged[2].Action, "c", "then c") Eq(Merged[4].Action, "a", "oldest last")

-- filter and pages
local Row = { Staff = "Mod"; Target = "Kid"; TargetId = 123; Action = "Warn"; Side = "Moderate"; Ok = false }
Eq(R.LogMatch(Row, "", "All"), true, "all") Eq(R.LogMatch(Row, "mod", "All"), true, "staff name")
Eq(R.LogMatch(Row, "12", "All"), true, "target UserId") Eq(R.LogMatch(Row, "warn", "Refused"), true, "refused chip")
Eq(R.LogMatch(Row, "", "Test"), false, "test chip") Eq(R.LogMatch(Row, "", "Moderate"), true, "moderate chip")
Eq(R.LogMatch(Row, "zzz", "All"), false, "no match")
local Rows = {}
for I = 1, 120 do Rows[I] = I end
local Pg, P, Ps = R.Page(Rows, 3, 50)
Eq(#Pg, 20, "the last page has 20") Eq(P, 3, "page 3") Eq(Ps, 3, "3 pages")
Eq(select(2, R.Page(Rows, 9, 50)), 3, "page clamped") Eq(select(3, R.Page({}, 1, 50)), 1, "an empty day has one page")

-- prefs drop unknown ids
local Fv = R.CleanFavs({ "Warn", 5, "Gone", "Warn", string.rep("x", 41) }, { Warn = true; Goto = true })
Eq(#Fv, 1, "unknown, repeated and bad ids dropped") Eq(Fv[1], "Warn", "a known id kept")
Eq(#R.CleanFavs({ "A", "B" }, nil), 2, "no known set keeps strings") Eq(#R.CleanFavs("junk", nil), 0, "not a list")
Eq(R.CleanSide("Test"), "Test", "side kept") Eq(R.CleanSide("Nope"), nil, "bad side dropped")

if #Fails > 0 then return "FAIL " .. #Fails .. "\n" .. table.concat(Fails, "\n") end
return "PASS records_rules"
```

- [ ] **Step 2: Run it (no module yet)**

Run: `python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/records_rules.lua`
Expected: `FAIL Functions.StaffRecords missing`.

- [ ] **Step 3: Write the module**

`tools/admin-console/live/ReplicatedStorage.Functions.StaffRecords.luau`:

```lua
--[[
	StaffRecords (shared, pure): the rules for the console's saved records, the saved staff log and saved favourites
	(spec docs/superpowers/specs/2026-11-23-admin-console-1b-design.md §2-§4). No services, no state. The server
	(Features.StaffRecords, Features.Admin) and the client (StaffConsole.Model) use it; checks/records_rules.lua tests it.
	Record lists are oldest first. By is a staff UserId; At and Until are os.time(); Until = 0 means until unmuted;
	Days = 0 means permanent; Lifted = { By, At }.
]]
local R = {}

R.CAP = 50
R.LOG_CAP = 2000
R.DETAIL_MAX = 120
R.FAVS_MAX = 40
R.LISTS = { "Notes", "Warnings", "Bans", "Mutes" }
R.KIND = { Notes = "Note", Warnings = "Warn", Bans = "Ban", Mutes = "Mute" }
R.MUTE_CHOICES = { 10, 60, 1440, 0 }
R.MUTE_LABELS = { "10 min", "1 h", "1 day", "Until unmuted" }
local SIDES = { Moderate = true, Test = true }

local function plural(N: number, Word: string): string
	return `{N} {Word}{if N == 1 then "" else "s"}`
end

function R.Blank(): any
	return { Notes = {}, Warnings = {}, Bans = {}, Mutes = {}, Reports = {} }
end

-- a stored value (or nil) as a record with every list; entries that aren't tables with a number At are dropped
function R.Normalize(V: any): any
	local Out = R.Blank()
	if typeof(V) ~= "table" then return Out end
	for _, Name in R.LISTS do
		local L = V[Name]
		if typeof(L) ~= "table" then continue end
		for _, E in L do
			if typeof(E) == "table" and typeof(E.At) == "number" then table.insert(Out[Name], E) end
		end
	end
	if typeof(V.Reports) == "table" then Out.Reports = V.Reports end
	return Out
end

-- the newest goes on the end; the oldest drop off past CAP
function R.Push(Rec: any, List: string, Entry: any): any
	local L = Rec[List]
	table.insert(L, Entry)
	while #L > R.CAP do table.remove(L, 1) end
	return Rec
end

function R.MuteUntil(Minutes: number, Now: number): number
	if Minutes == 0 then return 0 end
	return Now + Minutes * 60
end

function R.MuteOn(M: any, Now: number): boolean
	if typeof(M) ~= "table" or M.Lifted then return false end
	return M.Until == 0 or (typeof(M.Until) == "number" and M.Until > Now)
end

function R.OpenMute(Rec: any, Now: number): any
	for I = #Rec.Mutes, 1, -1 do
		if R.MuteOn(Rec.Mutes[I], Now) then return Rec.Mutes[I] end
	end
	return nil
end

function R.MuteLabel(M: any): string
	if M.Until == 0 then return R.MUTE_LABELS[4] end
	local Min = math.floor(((M.Until or 0) - (M.At or 0)) / 60 + 0.5)
	local I = table.find(R.MUTE_CHOICES, Min)
	return if I then R.MUTE_LABELS[I] else `{Min} min`
end

function R.BanOn(B: any, Now: number): boolean
	if typeof(B) ~= "table" or B.Lifted then return false end
	local D = tonumber(B.Days) or 0
	return D == 0 or (B.At or 0) + D * 86400 > Now
end

-- the latest ban nobody has lifted (it may have ended on time: lifting it is still allowed, and harmless)
function R.OpenBan(Rec: any): any
	for I = #Rec.Bans, 1, -1 do
		if not Rec.Bans[I].Lifted then return Rec.Bans[I] end
	end
	return nil
end

-- the staff level that may lift a ban: permanent 3, over 30 days 2, else 1; no ban on record (set before 1b) is permanent
function R.UnbanLevel(Ban: any): number
	if typeof(Ban) ~= "table" then return 3 end
	local D = tonumber(Ban.Days) or 0
	if D == 0 then return 3 end
	if D > 30 then return 2 end
	return 1
end

function R.Find(Rec: any, List: string, At: number, By: number): number?
	for I, E in Rec[List] or {} do
		if E.At == At and E.By == By then return I end
	end
	return nil
end

function R.Remove(Rec: any, List: string, At: number, By: number): any
	local I = R.Find(Rec, List, At, By)
	if not I then return nil end
	return table.remove(Rec[List], I)
end

function R.EntryText(List: string, E: any): string
	local Why = if typeof(E.Reason) == "string" and E.Reason ~= "" then ": " .. E.Reason else ""
	if List == "Notes" then return tostring(E.Text or "") end
	if List == "Warnings" then return if Why ~= "" then E.Reason else "Warned" end
	if List == "Bans" then return (if (tonumber(E.Days) or 0) == 0 then "Permanent ban" else `{E.Days}-day ban`) .. Why end
	if List == "Mutes" then return `Muted ({R.MuteLabel(E)})` .. Why end
	return ""
end

-- "3 warnings · 1 note · 1 ban (lifted) · muted until 14:20"; Clock formats Until (default: local HH:MM today,
-- else with the day, so a 1-day mute doesn't read as already over)
function R.Summary(Rec: any, Now: number, Clock: ((number) -> string)?): string
	local Fmt = Clock or function(T: number): string
		return os.date(if os.date("%Y%m%d", T) == os.date("%Y%m%d", Now) then "%H:%M" else "%a %d %b %H:%M", T)
	end
	local Parts = {}
	if #Rec.Warnings > 0 then table.insert(Parts, plural(#Rec.Warnings, "warning")) end
	if #Rec.Notes > 0 then table.insert(Parts, plural(#Rec.Notes, "note")) end
	if #Rec.Bans > 0 then
		local Any, AllLifted = false, true
		for _, Bn in Rec.Bans do
			if R.BanOn(Bn, Now) then Any = true end
			if not Bn.Lifted then AllLifted = false end
		end
		table.insert(Parts, plural(#Rec.Bans, "ban") .. (if Any then " (active)" elseif AllLifted then " (lifted)" else " (ended)"))
	end
	local M = R.OpenMute(Rec, Now)
	if M then table.insert(Parts, if M.Until == 0 then "muted until unmuted" else "muted until " .. Fmt(M.Until)) end
	return if #Parts > 0 then table.concat(Parts, " · ") else "No history"
end

-- every entry, newest first: { List, Kind, Entry, Seq }
function R.Timeline(Rec: any): any
	local Out = {}
	for _, List in R.LISTS do
		for I, E in Rec[List] do table.insert(Out, { List = List; Kind = R.KIND[List]; Entry = E; Seq = I }) end
	end
	table.sort(Out, function(A, B)
		if A.Entry.At ~= B.Entry.At then return A.Entry.At > B.Entry.At end
		if A.List ~= B.List then return A.List < B.List end
		return A.Seq > B.Seq
	end)
	return Out
end

---------------------------------------------------------------- the saved log
function R.Day(Now: number): number return Now // 86400 end
function R.LogKey(Day: number, Job: string, Test: boolean?): string return `{if Test then "test_" else ""}day_{Day}_{Job}` end
function R.IndexKey(Day: number, Test: boolean?): string return `{if Test then "test_" else ""}day_{Day}` end
function R.TestCutoff(Day: number): number return Day - 7 end

function R.LogEntry(F: any): any
	return {
		At = tonumber(F.At) or 0; Staff = string.sub(tostring(F.Staff or "?"), 1, 40); StaffId = tonumber(F.StaffId) or 0;
		Action = string.sub(tostring(F.Action or "?"), 1, 40);
		Target = if F.Target ~= nil then string.sub(tostring(F.Target), 1, 40) else nil; TargetId = tonumber(F.TargetId);
		Detail = string.sub(tostring(F.Detail or ""), 1, R.DETAIL_MAX);
		Side = if F.Side == "Test" then "Test" else "Moderate"; Ok = F.Ok == true;
	}
end

function R.CapLog(L: { any }): { any }
	local N = #L
	if N <= R.LOG_CAP then return L end
	return table.move(L, N - R.LOG_CAP + 1, N, 1, {})
end

-- Lists: each oldest first (a server's key, or this server's unsaved buffer last). Newest first out; a tie in the
-- same second keeps the later list's and later position's entry first
function R.MergeDay(Lists: { { any } }): { any }
	local All = {}
	for LI, L in Lists do
		for I, E in L do table.insert(All, { E = E; K = LI * 1e6 + I }) end
	end
	table.sort(All, function(A, B)
		if A.E.At ~= B.E.At then return A.E.At > B.E.At end
		return A.K > B.K
	end)
	local Out = table.create(#All)
	for I, X in All do Out[I] = X.E end
	return Out
end

-- Chip: "All" | "Moderate" | "Test" | "Refused"; Query: staff name, target name or UserId, or action
function R.LogMatch(E: any, Query: string?, Chip: string?): boolean
	if Chip == "Moderate" and E.Side ~= "Moderate" then return false end
	if Chip == "Test" and E.Side ~= "Test" then return false end
	if Chip == "Refused" and E.Ok then return false end
	local Q = string.lower(string.match(Query or "", "^%s*(.-)%s*$") or "")
	if Q == "" then return true end
	for _, Field in { E.Staff, E.Target, E.Action, if E.TargetId then tostring(E.TargetId) else nil } do
		if typeof(Field) == "string" and string.find(string.lower(Field), Q, 1, true) then return true end
	end
	return false
end

function R.Page(Rows: { any }, Page: any, Per: number): ({ any }, number, number)
	local Pages = math.max(1, math.ceil(#Rows / Per))
	local P = math.clamp(math.floor(tonumber(Page) or 1), 1, Pages)
	local Out = {}
	for I = (P - 1) * Per + 1, math.min(#Rows, P * Per) do table.insert(Out, Rows[I]) end
	return Out, P, Pages
end

---------------------------------------------------------------- saved favourites
-- strings only, no repeats, at most FAVS_MAX; with Known, only ids in it (the client drops ids no longer in the registry)
function R.CleanFavs(Favs: any, Known: any): { string }
	local Out, Seen = {}, {}
	if typeof(Favs) ~= "table" then return Out end
	for _, Id in Favs do
		if typeof(Id) == "string" and #Id <= 40 and not Seen[Id] and (Known == nil or Known[Id]) then
			Seen[Id] = true
			table.insert(Out, Id)
			if #Out >= R.FAVS_MAX then break end
		end
	end
	return Out
end

function R.CleanSide(Side: any): string?
	return if typeof(Side) == "string" and SIDES[Side] then Side else nil
end

return R
```

- [ ] **Step 4: Install and run the check**

```bash
python -X utf8 -I tools/admin-console/install_new.py tools/admin-console/live/ReplicatedStorage.Functions.StaffRecords.luau
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/records_rules.lua
```
Expected: `PASS records_rules`. If a line fails, fix the module, not the check, unless the check contradicts the spec.

- [ ] **Step 5: Commit (on the owner's word)**

```bash
git add tools/admin-console/pre1b tools/admin-console/live/ReplicatedStorage.Functions.StaffRecords.luau tools/admin-console/checks/records_rules.lua
git commit -m "Console 1b: StaffRecords pure rules (record shape and cap, mutes, unban rule, log keys, merge, filter, prefs)"
```

---

### Task 2: The records service (`Features.StaffRecords`, TDD with fake stores)

**Files:**
- Create: `tools/admin-console/live/ServerScriptService.Services.Features.StaffRecords.luau`
- Test: `tools/admin-console/checks/records_store.lua`

**Interfaces:**
- Consumes: everything from Task 1 (`require(ReplicatedStorage.Functions.StaffRecords)`).
- Produces (Task 3 and the Play checks use these):
  - `PREFIX: string` (`"[Test] "` in Studio), `BACKOFF = { 1, 2 }`, `CACHE_S = 60`, `PREFS_DELAY = 5`, `Clock: () -> number`
  - `SetStoresForTest(Get: (Name: string) -> store)` (Edit checks only)
  - `JobKey() -> string` (`"studio"` in Studio, else `game.JobId`)
  - `Get(UserId, Fresh?) -> (Record?, Err?)` (Err = `"History unavailable"`)
  - `Cached(UserId) -> Record?` (no yield)
  - `Write(UserId, Mutate: (Record) -> ()) -> (Record, Saved: boolean)`; `Status(Saved) -> "Saved" | "Saved later (DataStore busy)"`
  - `RetryPending()`
  - `RemoveEntry(UserId, List, At, By) -> (Entry?, Saved?, Err?)` (Err = `"No such entry"` or the read error)
  - `LogAdd(Fields)`; `FlushLog() -> boolean`
  - `LogDay(Offset: 0..6, Filter?: { Query?, Chip?, Page? }) -> ({ Day, Rows, Total, Page, Pages }?, Err?)` (Err = `"Log unavailable"` or `"Pick a day this week"`)
  - `PrefsGet(UserId) -> ({ Favs, Side? }?, Err?)` (Err = `"Favourites unavailable"`); `PrefsSet(UserId, Favs, Side)`;
    `PrefsFlush(UserId?, All?)`
  - `NameOf(UserId) -> string`
  - `OnStart()` (the loader calls it: the 30 s and 1 s loops, PlayerRemoving, BindToClose)
- Store keys: `NHStaffRecords_v1` `u_<UserId>`; `NHStaffLog_v1` `day_<n>_<Job>`, `day_<n>`, `test_day_<n>_<Job>`,
  `test_day_<n>`; `NHStaffPrefs_v1` `u_<UserId>`.

- [ ] **Step 1: Write the failing check**

`tools/admin-console/checks/records_store.lua`:

```lua
-- Edit: Features.StaffRecords against fake DataStores (no real store is touched). Values are copied in and out, as
-- real stores serialize them; Fail = N makes the next N calls on that store error.
local Mod = game.ServerScriptService.Services.Features:FindFirstChild("StaffRecords")
if not Mod then return "FAIL Features.StaffRecords missing" end
local SR = require(Mod:Clone())
local Rules = require(game.ReplicatedStorage.Functions.StaffRecords)
local Fails = {}
local function Eq(Got, Want, What) if Got ~= Want then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end
local function deep(V) if typeof(V) ~= "table" then return V end local O = {} for K, X in V do O[K] = deep(X) end return O end
local Fakes = {}
local function fake(Name)
	if Fakes[Name] then return Fakes[Name] end
	local S = { Data = {}; Fail = 0 }
	local function gate() if S.Fail > 0 then S.Fail -= 1 error("DataStore busy (fake)") end end
	function S:GetAsync(K) gate() return deep(S.Data[K]) end
	function S:SetAsync(K, V) gate() S.Data[K] = deep(V) end
	function S:RemoveAsync(K) gate() local V = S.Data[K] S.Data[K] = nil return V end
	function S:UpdateAsync(K, Fn) gate() if S.Slow then task.wait(S.Slow) end local V = Fn(deep(S.Data[K])) if V ~= nil then S.Data[K] = deep(V) end return deep(S.Data[K]) end
	Fakes[Name] = S
	return S
end
SR.SetStoresForTest(fake)
SR.BACKOFF = { 0, 0 }
SR.CACHE_S = 0
SR.PREFS_DELAY = 0
local Day = 20000
SR.Clock = function() return Day * 86400 + 3600 end
local Rec, Log, Prefs = fake("NHStaffRecords_v1"), fake("NHStaffLog_v1"), fake("NHStaffPrefs_v1")

-- 1. a write lands and reads back
local R1, S1 = SR.Write(1, function(R) Rules.Push(R, "Warnings", { By = 9; At = 100; Reason = "a" }) end)
Eq(S1, true, "write saved") Eq(R1 and #R1.Warnings, 1, "write returns the record")
Eq(Rec.Data.u_1 and #Rec.Data.u_1.Warnings, 1, "the store has it")
local G1 = SR.Get(1, true)
Eq(G1 and #G1.Warnings, 1, "read back")
Eq(SR.Status(true), "Saved", "status saved") Eq(SR.Status(false), "Saved later (DataStore busy)", "status later")

-- 2. two failed tries, then the third lands
Rec.Fail = 2
local _, S2 = SR.Write(1, function(R) Rules.Push(R, "Notes", { By = 9; At = 101; Text = "n" }) end)
Eq(S2, true, "saved on the third try")

-- 3. three failures: pending, shown already, retried once
Rec.Fail = 3
local R3, S3 = SR.Write(1, function(R) Rules.Push(R, "Warnings", { By = 9; At = 102; Reason = "b" }) end)
Eq(S3, false, "a busy write is not saved") Eq(R3 and #R3.Warnings, 2, "but shows in the console's copy")
Eq(#Rec.Data.u_1.Warnings, 1, "the store is unchanged")
local G3 = SR.Get(1, true)
Eq(G3 and #G3.Warnings, 2, "a fresh read still shows the waiting write")
SR.RetryPending()
Eq(#Rec.Data.u_1.Warnings, 2, "the retry saved it")
SR.RetryPending()
Eq(#Rec.Data.u_1.Warnings, 2, "and only once")

-- 3b. a waiting write goes with the next write for that player
Rec.Fail = 3
SR.Write(1, function(R) Rules.Push(R, "Warnings", { By = 9; At = 103; Reason = "c" }) end)
SR.Write(1, function(R) Rules.Push(R, "Warnings", { By = 9; At = 104; Reason = "d" }) end)
Eq(#Rec.Data.u_1.Warnings, 4, "the next write carried the waiting one")

-- 4. a failed read is an error, never an empty history
Rec.Fail = 3
local G4, E4 = SR.Get(1, true)
Eq(G4, nil, "a failed read gives no record") Eq(E4, "History unavailable", "failed read message")

-- 5. the cap of 50 through writes
for I = 1, 51 do SR.Write(2, function(R) Rules.Push(R, "Warnings", { By = 9; At = I; Reason = "w" }) end) end
Eq(#Rec.Data.u_2.Warnings, 50, "cap 50 in the store") Eq(Rec.Data.u_2.Warnings[1].At, 2, "the oldest dropped")

-- 6. removing one entry
local Gone, S6 = SR.RemoveEntry(1, "Warnings", 102, 9)
Eq(Gone and Gone.Reason, "b", "removed the matching entry") Eq(S6, true, "the removal saved")
Eq(#Rec.Data.u_1.Warnings, 3, "three left")
local Miss, _, E6 = SR.RemoveEntry(1, "Warnings", 999, 9)
Eq(Miss, nil, "no such entry") Eq(E6, "No such entry", "missing entry message")

-- 7. the log: buffered, flushed into this server's keys with an index, read back newest first, filtered
local T = Day * 86400 + 100
SR.LogAdd({ At = T; Staff = "mod"; StaffId = 9; Action = "Warn"; Target = "kid"; TargetId = 1; Detail = "Warned kid"; Side = "Moderate"; Ok = true })
SR.LogAdd({ At = T + 1; Staff = "mod"; StaffId = 9; Action = "Ban"; Target = "kid"; TargetId = 1; Detail = "Permanent bans are owner-only"; Side = "Moderate"; Ok = false })
SR.LogAdd({ At = T + 2; Staff = "mod"; StaffId = 9; Action = "Heal"; Detail = "Healed"; Side = "Test"; Ok = true })
local D0 = SR.LogDay(0, {})
Eq(D0 and D0.Total, 3, "unsaved entries show already")
Eq(SR.FlushLog(), true, "flush ok")
Eq(#(Log.Data[`day_{Day}_studio`] or {}), 2, "the Moderate key has 2")
Eq(#(Log.Data[`test_day_{Day}_studio`] or {}), 1, "the Test key has 1")
Eq(table.find(Log.Data[`day_{Day}`] or {}, "studio") ~= nil, true, "the index has this server")
Eq(table.find(Log.Data[`test_day_{Day}`] or {}, "studio") ~= nil, true, "the Test index has this server")
local D1 = SR.LogDay(0, {})
Eq(D1 and D1.Total, 3, "read back 3") Eq(D1 and D1.Rows[1].Action, "Heal", "newest first")
Eq(SR.LogDay(0, { Chip = "Refused" }).Total, 1, "refused chip") Eq(SR.LogDay(0, { Chip = "Test" }).Total, 1, "test chip")
Eq(SR.LogDay(0, { Query = "KID" }).Total, 2, "search by target name")
Eq(SR.LogDay(1, {}).Total, 0, "an empty day is empty, not an error")
Eq(SR.LogDay(7, {}), nil, "only this week")

-- 8. the cap of 2000 per key
local Old = {}
for I = 1, 1999 do Old[I] = { At = T - 5000 + I; Staff = "x"; Action = "Old"; Detail = ""; Side = "Moderate"; Ok = true } end
Log.Data[`day_{Day}_studio`] = Old
for I = 1, 5 do SR.LogAdd({ At = T + 10 + I; Staff = "mod"; Action = "New"; Side = "Moderate"; Ok = true }) end
SR.FlushLog()
local K = Log.Data[`day_{Day}_studio`]
Eq(#K, 2000, "the key is capped at 2000") Eq(K[1] and K[1].At, T - 5000 + 5, "the oldest dropped") Eq(K[2000] and K[2000].Action, "New", "the newest kept")

-- 9. a failed flush keeps its entries for the next one
Log.Fail = 3
SR.LogAdd({ At = T + 50; Staff = "mod"; Action = "Kept"; Side = "Moderate"; Ok = true })
Eq(SR.FlushLog(), false, "a busy flush says so")
Eq(SR.LogDay(0, { Query = "Kept" }).Total, 1, "the kept entry still shows")
Eq(SR.FlushLog(), true, "the next flush is ok")
local Found = false
for _, E in Log.Data[`day_{Day}_studio`] do if E.Action == "Kept" then Found = true end end
Eq(Found, true, "the kept entry was saved")

-- 10. a failed day read is an error, never an empty day
Log.Fail = 3
local D10, E10 = SR.LogDay(0, {})
Eq(D10, nil, "a failed day read gives nothing") Eq(E10, "Log unavailable", "failed day message")
Log.Fail = 0

-- 11. the first Test write on day n removes day n-7's Test keys and index; Moderate keys stay
local N1 = Day + 1
SR.Clock = function() return N1 * 86400 + 60 end
Log.Data[`test_day_{N1 - 7}`] = { "jobA" }
Log.Data[`test_day_{N1 - 7}_jobA`] = { { At = (N1 - 7) * 86400; Action = "OldTest"; Side = "Test"; Ok = true } }
Log.Data[`day_{N1 - 7}_jobA`] = { { At = (N1 - 7) * 86400; Action = "OldModerate"; Side = "Moderate"; Ok = true } }
SR.LogAdd({ At = N1 * 86400 + 10; Staff = "mod"; Action = "Heal"; Side = "Test"; Ok = true })
SR.FlushLog()
Eq(Log.Data[`test_day_{N1 - 7}_jobA`], nil, "the old Test key removed")
Eq(Log.Data[`test_day_{N1 - 7}`], nil, "the old Test index removed")
Eq(Log.Data[`day_{N1 - 7}_jobA`] ~= nil, true, "Moderate keys are kept")

-- 12. prefs: kept in memory, saved after the delay (0 here), cleaned on the way in and out
SR.PrefsSet(9, { "Warn", 5, "Warn" }, "Test")
local P1 = SR.PrefsGet(9)
Eq(P1 and #P1.Favs, 1, "prefs cleaned on set") Eq(P1 and P1.Side, "Test", "side kept")
SR.PrefsFlush()
Eq(Prefs.Data.u_9 and Prefs.Data.u_9.Side, "Test", "prefs saved")
Prefs.Data.u_9 = { Favs = { "Goto", {}, "Goto" }; Side = "Bad" }
local P2 = SR.PrefsGet(9)
Eq(P2 and #P2.Favs, 1, "stored prefs cleaned on read") Eq(P2 and P2.Side, nil, "a bad side dropped")
Prefs.Fail = 3
local P3, E3p = SR.PrefsGet(10)
Eq(P3, nil, "a failed prefs read") Eq(E3p, "Favourites unavailable", "prefs message")

-- 13. a flush already running (the 30 s loop) doesn't hide entries: they stay readable while it writes, and a second
-- FlushLog waits for it, so "flush, then read" finds everything logged before the call
SR.Clock = function() return Day * 86400 + 3600 end
Log.Slow = 0.3
SR.LogAdd({ At = T + 60; Staff = "mod"; Action = "Racing"; Side = "Moderate"; Ok = false })
task.spawn(SR.FlushLog)
task.wait(0.05)
Eq(SR.LogDay(0, { Query = "Racing" }).Total, 1, "an entry being written still shows")
SR.LogAdd({ At = T + 61; Staff = "mod"; Action = "Racing"; Side = "Moderate"; Ok = false })
Eq(SR.FlushLog(), true, "the second flush waits, then saves")
Log.Slow = nil
local Racing = 0
for _, E in Log.Data[`day_{Day}_studio`] do if E.Action == "Racing" then Racing += 1 end end
Eq(Racing, 2, "both racing entries saved, once each")
Eq(SR.LogDay(0, { Query = "Racing"; Chip = "Refused" }).Total, 2, "and read back once each")

if #Fails > 0 then return "FAIL " .. #Fails .. "\n" .. table.concat(Fails, "\n") end
return "PASS records_store"
```

- [ ] **Step 2: Run it (no module yet)**

Run: `python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/records_store.lua`
Expected: `FAIL Features.StaffRecords missing`.

- [ ] **Step 3: Write the service**

`tools/admin-console/live/ServerScriptService.Services.Features.StaffRecords.luau`:

```lua
--[[
	StaffRecords (server): the console's saved records, the saved staff log and saved favourites
	(spec docs/superpowers/specs/2026-11-23-admin-console-1b-design.md §2-§4). The rules are in Functions.StaffRecords.
	Stores (Studio adds the prefix "[Test] "):
	  NHStaffRecords_v1  u_<UserId>                    a player's record
	  NHStaffLog_v1      day_<n>_<Job> / day_<n>        this server's Moderate entries for day n / the servers that wrote it
	                     test_day_<n>_<Job> / test_day_<n>   the same for Test actions (removed after 7 days)
	  NHStaffPrefs_v1    u_<UserId>                    { Favs, Side }
	Records are written straight away (3 tries). A failed write waits in Pending: it shows in the console's copy, goes
	with the next write for that player and is retried every 30 s. The log is buffered and saved every 30 s and on
	close (a crash can lose up to 30 s of it). Prefs are saved 5 s after the last change and on leave.
	Features.Admin calls it. checks/records_store.lua tests it in Edit against fake stores (SetStoresForTest).
]]
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local DataStoreService = game:GetService("DataStoreService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Rules = require(ReplicatedStorage:WaitForChild("Functions"):WaitForChild("StaffRecords"))

local Shared = {}
Shared.PREFIX = if RunService:IsStudio() then "[Test] " else ""
Shared.BACKOFF = { 1, 2 }
Shared.CACHE_S = 60
Shared.PREFS_DELAY = 5
Shared.Clock = function(): number return os.time() end

local Stores = {} :: { [string]: any }
local Override = nil :: ((string) -> any)?
local Cache = {} :: { [number]: { Rec: any, At: number, Partial: boolean? } }
local Pending = {} :: { [number]: { (any) -> () } }
local Busy = {} :: { [number]: boolean }
local Buffer = {} :: { any }
local InFlight = {} :: { [string]: { any } } -- log key -> entries a running FlushLog is still writing
local FlushBusy = false
local Indexed = {} :: { [string]: boolean }
local Swept = {} :: { [number]: boolean }
local DayCache = {} :: { [number]: { Lists: { { any } }, At: number } }
local Prefs = {} :: { [number]: { Favs: { string }, Side: string?, At: number } }
local Names = {} :: { [number]: string }

function Shared.SetStoresForTest(Get: (string) -> any)
	Override = Get
	Stores = {}
end

local function store(Name: string): any
	if Override then return Override(Name) end
	Stores[Name] = Stores[Name] or DataStoreService:GetDataStore(Shared.PREFIX .. Name)
	return Stores[Name]
end

-- 3 tries, waiting BACKOFF[1] then BACKOFF[2] between them
local function tries(Fn: () -> any): (boolean, any)
	for I = 1, 3 do
		local Ok, A = pcall(Fn)
		if Ok then return true, A end
		if I < 3 then task.wait(Shared.BACKOFF[I] or 0) end
	end
	return false, nil
end

local function key(UserId: number): string return `u_{UserId}` end

function Shared.JobKey(): string
	-- Studio (Edit and Play) has a JobId of its own, but the spec keeps Studio on one key: day_<n>_studio
	return if RunService:IsStudio() or game.JobId == "" then "studio" else game.JobId
end

function Shared.Status(Saved: boolean): string
	return if Saved then "Saved" else "Saved later (DataStore busy)"
end

---------------------------------------------------------------- records
function Shared.Cached(UserId: number): any
	local C = Cache[UserId]
	return C and C.Rec
end

function Shared.Get(UserId: number, Fresh: boolean?): (any, string?)
	local C = Cache[UserId]
	if C and not C.Partial and not Fresh and os.clock() - C.At < Shared.CACHE_S then return C.Rec end
	local S = store("NHStaffRecords_v1")
	local Ok, V = tries(function() return S:GetAsync(key(UserId)) end)
	if not Ok then return nil, "History unavailable" end
	local Rec = Rules.Normalize(V)
	for _, M in Pending[UserId] or {} do M(Rec) end -- writes still waiting show already
	Cache[UserId] = { Rec = Rec; At = os.clock() }
	return Rec
end

-- Mutate changes a record in place and must be pure: UpdateAsync may call it more than once. One write per player at
-- a time, so a waiting write is never applied twice.
function Shared.Write(UserId: number, Mutate: (any) -> ()): (any, boolean)
	while Busy[UserId] do task.wait() end
	Busy[UserId] = true
	local Queue = Pending[UserId] or {}
	table.insert(Queue, Mutate)
	Pending[UserId] = Queue
	local S = store("NHStaffRecords_v1")
	local Ok, V = tries(function()
		return S:UpdateAsync(key(UserId), function(Old)
			local Rec = Rules.Normalize(Old)
			for _, M in Queue do M(Rec) end
			return Rec
		end)
	end)
	local Out
	if Ok then
		Pending[UserId] = nil
		Cache[UserId] = { Rec = Rules.Normalize(V); At = os.clock() }
		Out = Cache[UserId].Rec
	else
		local C = Cache[UserId]
		if C then
			Mutate(C.Rec)
		else
			local Rec = Rules.Blank()
			for _, M in Queue do M(Rec) end
			Cache[UserId] = { Rec = Rec; At = os.clock(); Partial = true } -- Get reads the store again before trusting it
		end
		Out = Cache[UserId].Rec
	end
	Busy[UserId] = nil
	return Out, Ok
end

function Shared.RetryPending()
	local Ids = {}
	for Id in Pending do table.insert(Ids, Id) end
	for _, Id in Ids do
		if Pending[Id] then Shared.Write(Id, function() end) end
	end
end

function Shared.RemoveEntry(UserId: number, List: string, At: number, By: number): (any, boolean?, string?)
	local Rec, Err = Shared.Get(UserId, true)
	if not Rec then return nil, nil, Err end
	local I = Rules.Find(Rec, List, At, By)
	if not I then return nil, nil, "No such entry" end
	local Entry = Rec[List][I]
	local _, Saved = Shared.Write(UserId, function(R) Rules.Remove(R, List, At, By) end)
	return Entry, Saved
end

---------------------------------------------------------------- the saved log
function Shared.LogAdd(F: any)
	table.insert(Buffer, Rules.LogEntry(F))
	if #Buffer > Rules.LOG_CAP then Buffer = Rules.CapLog(Buffer) end
end

-- the first Test write on a day removes day n-7's Test keys and their index (best effort)
local function sweepTest(Day: number)
	if Swept[Day] then return end
	Swept[Day] = true
	local S = store("NHStaffLog_v1")
	local Old = Rules.TestCutoff(Day)
	local Ok, Jobs = pcall(function() return S:GetAsync(Rules.IndexKey(Old, true)) end)
	if not Ok then warn(`[StaffRecords] Test log clean-up of day {Old} failed: {Jobs}`) return end
	for _, Job in (if typeof(Jobs) == "table" then Jobs else {}) do
		local Ok2, Err = pcall(function() S:RemoveAsync(Rules.LogKey(Old, Job, true)) end)
		if not Ok2 then warn(`[StaffRecords] Test log clean-up of {Job} on day {Old} failed: {Err}`) end
	end
	local Ok3, Err3 = pcall(function() S:RemoveAsync(Rules.IndexKey(Old, true)) end)
	if not Ok3 then warn(`[StaffRecords] Test log index clean-up of day {Old} failed: {Err3}`) end
end

-- one flush at a time: a second call waits for the running one, then saves what's left, so "FlushLog() then read"
-- always finds every entry logged before the call. Entries being written stay readable (InFlight) until their key saves.
-- The index first (a reader treats a listed key that doesn't exist yet as empty), then the entries.
local function flushBatch(Batch: { any }, Failed: { any }): boolean
	local Job = Shared.JobKey()
	local Groups, Order = {}, {}
	for _, E in Batch do
		local Day, Test = Rules.Day(E.At), E.Side == "Test"
		local K = Rules.LogKey(Day, Job, Test)
		if not Groups[K] then Groups[K] = { Day = Day; Test = Test; Entries = {} } table.insert(Order, K) end
		table.insert(Groups[K].Entries, E)
	end
	for _, K in Order do InFlight[K] = Groups[K].Entries end
	local S = store("NHStaffLog_v1")
	local AllOk = true
	for _, K in Order do
		local G = Groups[K]
		if G.Test then sweepTest(G.Day) end
		local IK = Rules.IndexKey(G.Day, G.Test)
		local Ok = Indexed[IK] == true
		if not Ok then
			Ok = (tries(function()
				return S:UpdateAsync(IK, function(Old)
					local L = if typeof(Old) == "table" then Old else {}
					if not table.find(L, Job) then table.insert(L, Job) end
					return L
				end)
			end))
			if Ok then Indexed[IK] = true end
		end
		if Ok then
			Ok = (tries(function()
				return S:UpdateAsync(K, function(Old)
					local L = if typeof(Old) == "table" then Old else {}
					for _, E in G.Entries do table.insert(L, E) end
					return Rules.CapLog(L)
				end)
			end))
		end
		if Ok then
			DayCache[G.Day] = nil
		else
			AllOk = false
			for _, E in G.Entries do table.insert(Failed, E) end
		end
		InFlight[K] = nil
	end
	return AllOk
end

function Shared.FlushLog(): boolean
	while FlushBusy do task.wait() end
	if #Buffer == 0 then return true end
	FlushBusy = true
	local Batch, Failed = Buffer, {}
	Buffer = {}
	local Ran, AllOk = pcall(flushBatch, Batch, Failed)
	if not Ran then
		warn(`[StaffRecords] log save failed: {AllOk}`)
		Failed, AllOk = Batch, false -- a key saved before the error may get these again: a repeat beats a loss
	end
	table.clear(InFlight)
	-- the failed ones go back in front of anything logged meanwhile
	local Since = Buffer
	Buffer = Failed
	for _, E in Since do table.insert(Buffer, E) end
	if #Buffer > Rules.LOG_CAP then Buffer = Rules.CapLog(Buffer) end
	FlushBusy = false
	return AllOk
end

local function readDay(Day: number): ({ { any } }?, string?)
	local C = DayCache[Day]
	if C and os.clock() - C.At < Shared.CACHE_S then return C.Lists end
	local S = store("NHStaffLog_v1")
	local Lists = {}
	for _, Test in { false, true } do
		local Ok, Jobs = tries(function() return S:GetAsync(Rules.IndexKey(Day, Test)) end)
		if not Ok then return nil, "Log unavailable" end
		for _, Job in (if typeof(Jobs) == "table" then Jobs else {}) do
			local Ok2, L = tries(function() return S:GetAsync(Rules.LogKey(Day, Job, Test)) end)
			if not Ok2 then return nil, "Log unavailable" end
			if typeof(L) == "table" then table.insert(Lists, L) end
		end
	end
	DayCache[Day] = { Lists = Lists; At = os.clock() }
	return Lists
end

-- Offset 0 = today .. 6; Filter = { Query?, Chip? ("All"|"Moderate"|"Test"|"Refused"), Page? }. This server's unsaved
-- entries for that day are included, so an action shows before the next save.
function Shared.LogDay(Offset: any, Filter: any): (any, string?)
	local Off = tonumber(Offset)
	if not Off or Off ~= math.floor(Off) or Off < 0 or Off > 6 then return nil, "Pick a day this week" end
	local Day = Rules.Day(Shared.Clock()) - Off
	local Saved, Err = readDay(Day)
	if not Saved then return nil, Err end
	local Mine = {}
	for _, L in InFlight do for _, E in L do if Rules.Day(E.At) == Day then table.insert(Mine, E) end end end
	for _, E in Buffer do if Rules.Day(E.At) == Day then table.insert(Mine, E) end end
	local Lists = table.clone(Saved)
	table.insert(Lists, Mine)
	local All = Rules.MergeDay(Lists)
	local F = if typeof(Filter) == "table" then Filter else {}
	local Query = if typeof(F.Query) == "string" then string.sub(F.Query, 1, 60) else ""
	local Chip = if F.Chip == "Moderate" or F.Chip == "Test" or F.Chip == "Refused" then F.Chip else "All"
	local Hits = {}
	for _, E in All do if Rules.LogMatch(E, Query, Chip) then table.insert(Hits, E) end end
	local Rows, Page, Pages = Rules.Page(Hits, F.Page, 50)
	return { Day = Day; Rows = Rows; Total = #Hits; Page = Page; Pages = Pages }
end

---------------------------------------------------------------- saved favourites and last side
function Shared.PrefsGet(UserId: number): (any, string?)
	local Mine = Prefs[UserId]
	if Mine then return { Favs = table.clone(Mine.Favs); Side = Mine.Side } end
	local S = store("NHStaffPrefs_v1")
	local Ok, V = tries(function() return S:GetAsync(key(UserId)) end)
	if not Ok then return nil, "Favourites unavailable" end
	local T = if typeof(V) == "table" then V else {}
	return { Favs = Rules.CleanFavs(T.Favs, nil); Side = Rules.CleanSide(T.Side) }
end

function Shared.PrefsSet(UserId: number, Favs: any, Side: any)
	Prefs[UserId] = { Favs = Rules.CleanFavs(Favs, nil); Side = Rules.CleanSide(Side); At = os.clock() }
end

-- no args: the ones untouched for PREFS_DELAY s (the 1 s loop); UserId: that one now; All: every one now (on close)
function Shared.PrefsFlush(UserId: number?, All: boolean?)
	local S = store("NHStaffPrefs_v1")
	local Ids = {}
	for Id in Prefs do table.insert(Ids, Id) end
	for _, Id in Ids do
		local P = Prefs[Id]
		if not P then continue end
		if UserId ~= nil and Id ~= UserId then continue end
		if UserId == nil and not All and os.clock() - P.At < Shared.PREFS_DELAY then continue end
		local Ok = tries(function() return S:SetAsync(key(Id), { Favs = P.Favs; Side = P.Side }) end)
		if Ok and Prefs[Id] == P then Prefs[Id] = nil end
	end
end

---------------------------------------------------------------- names
function Shared.NameOf(UserId: number): string
	local P = Players:GetPlayerByUserId(UserId)
	if P then return P.Name end
	if Names[UserId] then return Names[UserId] end
	local Ok, N = pcall(Players.GetNameFromUserIdAsync, Players, UserId)
	if Ok and typeof(N) == "string" then Names[UserId] = N return N end
	return tostring(UserId)
end

function Shared.OnStart()
	task.spawn(function()
		while true do
			task.wait(30)
			pcall(Shared.FlushLog)
			pcall(Shared.RetryPending)
		end
	end)
	task.spawn(function()
		while true do
			task.wait(1)
			pcall(Shared.PrefsFlush)
		end
	end)
	Players.PlayerRemoving:Connect(function(P) task.spawn(Shared.PrefsFlush, P.UserId) end)
	game:BindToClose(function()
		local Left = 3
		for _, Fn in { Shared.FlushLog, function() Shared.PrefsFlush(nil, true) end, Shared.RetryPending } do
			task.spawn(function() pcall(Fn) Left -= 1 end)
		end
		local T0 = os.clock()
		while Left > 0 and os.clock() - T0 < 25 do task.wait(0.1) end
	end)
end

return Shared
```

- [ ] **Step 4: Install and run the check**

```bash
python -X utf8 -I tools/admin-console/install_new.py tools/admin-console/live/ServerScriptService.Services.Features.StaffRecords.luau
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/records_store.lua
```
Expected: `PASS records_store`.

Installing a new service in Edit is safe: nothing calls it until Task 3, and its `OnStart` only runs in Play.

- [ ] **Step 5: Commit (on the owner's word)**

```bash
git add tools/admin-console/live/ServerScriptService.Services.Features.StaffRecords.luau tools/admin-console/checks/records_store.lua
git commit -m "Console 1b: StaffRecords service (records with pending retry, buffered day log with Test clean-up, prefs)"
```

---

### Task 3: The server wiring (`StaffConsole`, `Admin.Meta`, `Features.Admin`)

**Files:**
- Modify: `tools/admin-console/live/ReplicatedStorage.Functions.StaffConsole.luau`
- Modify: `tools/admin-console/live/ServerScriptService.Services.Features.Admin.Meta.luau`
- Modify: `tools/admin-console/live/ServerScriptService.Services.Features.Admin.luau`
- Modify: `tools/admin-console/checks/console_pure.lua`, `checks/console_registry.lua`, `checks/console_play_server.lua`, `checks/console_play_run.lua`
- Create: `tools/admin-console/checks/records_play_a.lua`, `tools/admin-console/checks/records_cleanup.lua`

**Interfaces:**
- Consumes: Task 1 rules (`Records.*`), Task 2 service (`StaffRecords.*`).
- Produces:
  - `StaffConsole.SECTIONS.Moderate = { "Student", "Server", "Log" }`; `StaffConsole.CARDLESS = { Log = true }`;
    `Target = "user"` is valid.
  - `Admin.LevelOf(UserId) -> number`; `Admin.MutedUntil(UserId) -> number?`; `Admin.TestSkipBanApi: boolean`.
  - `Run(Admin, Target?, Args, TargetId?)`: Dispatch now passes the target's UserId as a 4th argument.
  - Remotes in `ReplicatedStorage.NHAdmin`:
    - `History(UserId) -> { Ok = true, UserId, Name, Record }` or `{ Ok = false, Error }` (nil below level 1). Every
      entry, and every `Lifted`, carries `ByName`.
    - `LogDay(Offset, Filter) -> { Ok = true, Day, Rows, Total, Page, Pages }` or `{ Ok = false, Error }`.
    - `Prefs() -> { Ok = true, Favs, Side }` or `{ Ok = false, Error }`.
    - `SavePrefs(Favs, Side) -> boolean`.
  - Command `RemoveRecordEntry` (Moderate, Student, level 3, Danger, `Target = "user"`, Args `List`, `At`, `By`).
  - Mute's arg `Minutes` (choice 10/60/1440/0, with `Labels`).

- [ ] **Step 1: Extend the pure check first**

In `checks/console_pure.lua`, before the final `if #Fails > 0` line, add:

```lua
-- 1b: the Log section (no cards) and the "user" target (a UserId, online or not)
Eq(S.SECTIONS.Moderate[3], "Log", "Log is the third Moderate section")
Eq(S.CARDLESS and S.CARDLESS.Log, true, "Log has no cards")
local UserDef = table.clone(Good) UserDef.Target = "user" UserDef.Level = 3
Eq((S.Validate("RemoveRecordEntry", UserDef)), true, "target mode user is valid")
```

Run: `python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_pure.lua`
Expected: `FAIL 3` (Log missing, CARDLESS missing, user target refused).

- [ ] **Step 2: `StaffConsole` changes**

In `live/ReplicatedStorage.Functions.StaffConsole.luau`:

Replace

```lua
	Moderate = { "Student", "Server" },
```

with

```lua
	Moderate = { "Student", "Server", "Log" },
```

After the `Shared.SIDE_LEVEL = ...` line, add:

```lua
-- sections the console draws itself, with no cards (1b: the saved staff log). The registry check skips them.
Shared.CARDLESS = { Log = true }
```

Replace

```lua
local TARGETS = { none = true, required = true, optional = true }
```

with

```lua
-- user (1b): a picked UserId, online or not; Run gets it as its 4th argument (Remove history entry)
local TARGETS = { none = true, required = true, optional = true, user = true }
```

- [ ] **Step 3: `Admin.Meta` changes**

In `live/ServerScriptService.Services.Features.Admin.Meta.luau`:

Replace the `Mute` entry with:

```lua
	Mute = { Side = M; Section = "Student"; Title = "Mute"; Help = "Stop their chat (saved: it holds if they rejoin)"; Icon = "Mute"; Level = 1; Target = "required"; Danger = false; Synonyms = { "silence" };
		Args = { A("Minutes", "choice", { Label = "Length"; Choices = { 10, 60, 1440, 0 }; Labels = { "10 min", "1 h", "1 day", "Until unmuted" }; Required = true }),
			A("Reason", "text", { Max = 120 }) } };
```

Replace the `Unban` entry's `Help` with `"Lift a ban by UserId (permanent: owner only)"`.

Replace the `Note` entry with:

```lua
	Note = { Side = M; Section = "Student"; Title = "Note"; Help = "A staff note on their record"; Icon = "Note"; Level = 1; Target = "required"; Danger = false; Synonyms = { "memo" };
		Args = { A("Text", "text", { Label = "Note"; Max = 300; Required = true }) } };
```

After the `Note` entry, add:

```lua
	RemoveRecordEntry = { Side = M; Section = "Student"; Title = "Remove history entry"; Help = "Take one entry off their record (logged)"; Icon = "Note"; Level = 3; Target = "user"; Danger = true; Synonyms = { "erase", "delete record" };
		Args = { A("List", "choice", { Choices = { "Notes", "Warnings", "Bans", "Mutes" }; Required = true }),
			A("At", "number", { Label = "Time"; Min = 0; Max = 1e10; Required = true }),
			A("By", "number", { Label = "Staff UserId"; Min = -1e12; Max = 1e12; Required = true }) } };
```

(`By` may be negative: Studio's local-server test players have negative UserIds.)

- [ ] **Step 4: Update the registry check**

In `checks/console_registry.lua`:
- `if N ~= 66 then ... want 66` becomes `if N ~= 67 then table.insert(Fails, "commands in Admin: " .. N .. ", want 67") end`.
- Add `RemoveRecordEntry = true` to `DANGER`.
- Replace the owner-only block with:

```lua
-- owner-only by level: Shutdown and Remove history entry (the rest are checked inside Run)
local OWNER = { Shutdown = true, RemoveRecordEntry = true }
for Id, D in Meta do
	if (D.Level == 3) ~= (OWNER[Id] == true) then table.insert(Fails, Id .. " level " .. D.Level) end
end
-- only Remove history entry takes an offline UserId
for Id, D in Meta do
	if (D.Target == "user") ~= (Id == "RemoveRecordEntry") then table.insert(Fails, Id .. " target " .. D.Target) end
end
```

- In "every section has at least one card", skip cardless sections:

```lua
	for _, Sec in List do
		if S.CARDLESS and S.CARDLESS[Sec] then continue end
```

In `checks/console_play_server.lua`: `Eq(#Admin.Registry(3), 66, ...)` becomes `67`. Level 1 stays 16 and level 2
stays 65 (the new command is level 3). Update its comment to "level 1: Student 12 + Server 4".

- [ ] **Step 5: `Features.Admin`: requires, state, levels for any UserId**

In `live/ServerScriptService.Services.Features.Admin.luau`:

Add to the header comment, after the 1a line:

```lua
	1b (2026-11-23): saved records (Warn, Note, Mute, Unmute, Ban, Unban write them; Remove history entry is owner-only
	and logged), mute lengths re-applied on join, the saved staff log (every Dispatch call except "Not staff" and
	"Slow down"), and the History, LogDay, Prefs and SavePrefs remotes. Stores: Features.StaffRecords.
```

and add the new remotes to the remotes list in the header:

```lua
	                                      History(UserId) -> { Ok, UserId, Name, Record } | { Ok = false, Error }
	                                      LogDay(Offset, Filter) -> { Ok, Day, Rows, Total, Page, Pages } | { Ok = false, Error }
	                                      Prefs() -> { Ok, Favs, Side };  SavePrefs(Favs, Side) -> boolean
```

After `local Stats = game:GetService(\`Stats\`)` add `local GroupService = game:GetService(\`GroupService\`)`.

After `local Meta = require(script:WaitForChild(\`Meta\`))` add:

```lua
local Records = require(ReplicatedStorage.Functions.StaffRecords)
local StaffRecords = require(ServerScriptService.Services.Features.StaffRecords)
```

Replace `local Muted = {} :: { [number]: boolean }` with:

```lua
local Muted = {} :: { [number]: number } -- UserId -> Until (os.time(); 0 = until unmuted); filled from the saved record on join
```

After `local Folder, ClientEvent` add:

```lua
-- Studio only: the Play checks set it so Ban and Unban write the record without the Roblox Ban API (or a kick)
Shared.TestSkipBanApi = false
local OfflineRank = {} :: { [number]: { R: number, At: number } }
```

After `function Shared.Level(P: Player): number ... end` add:

```lua
-- a UserId's group rank without a Player (cached 10 min); nil when the lookup fails
local function rankOfId(UserId: number): number?
	if game.CreatorType ~= Enum.CreatorType.Group then return if UserId == game.CreatorId then 255 else 0 end
	local C = OfflineRank[UserId]
	if C and os.clock() - C.At < 600 then return C.R end
	local Ok, Groups = pcall(GroupService.GetGroupsAsync, GroupService, UserId)
	if not Ok then return nil end
	local R = 0
	for _, G in Groups do if G.Id == game.CreatorId then R = G.Rank end end
	OfflineRank[UserId] = { R = R; At = os.clock() }
	return R
end

-- the staff level of any UserId: their own level when they're here; else the lists and the group rank. A failed
-- lookup counts as the owner, so "no targeting up" fails closed.
function Shared.LevelOf(UserId: number): number
	local P = Players:GetPlayerByUserId(UserId)
	if P then return Shared.Level(P) end
	local Rank = rankOfId(UserId)
	if Rank == nil then return 3 end
	local c = cmdrCfg()
	return StaffConsole.LevelFrom({
		Studio = false;
		Owner = table.find(c.Owner or {}, UserId) ~= nil;
		Admin = table.find(c.Admin or {}, UserId) ~= nil;
		Tester = table.find(c.Testers or {}, UserId) ~= nil;
		Rank = Rank;
	})
end

function Shared.MutedUntil(UserId: number): number? return Muted[UserId] end

local function saved(Msg: string, Ok: boolean): string return `{Msg} · {StaffRecords.Status(Ok)}` end
```

- [ ] **Step 6: `Features.Admin`: the record commands**

Replace `C.Ban`, `C.Unban`, `C.Mute`, `C.Unmute` and `C.Warn` with:

```lua
C.Ban = { Target = true; Run = function(A, T, a)
	local days = num(a.Days, 0, 3650, 1)
	local lvl = Shared.Level(A)
	if days == 0 and lvl < 3 then return false, `Permanent bans are owner-only` end
	if days > 30 and lvl < 2 then return false, `Moderators can ban for up to 30 days` end
	local reason = str(a.Reason, 200)
	-- the record first: a kick ends T, the record only needs the UserId
	local Entry = { By = A.UserId; At = os.time(); Days = days; Reason = reason }
	local _, Saved = StaffRecords.Write(T.UserId, function(R) Records.Push(R, `Bans`, Entry) end)
	local Length = if days == 0 then `ever` else days .. ` day(s)`
	if Shared.TestSkipBanApi and RunService:IsStudio() then return true, saved(`Banned {T.Name} for {Length} (test: Ban API skipped)`, Saved) end
	local ok, err = pcall(Players.BanAsync, Players, {
		UserIds = { T.UserId }; ApplyToUniverse = true;
		Duration = if days == 0 then -1 else math.floor(days * 86400);
		DisplayReason = if reason ~= `` then reason else `Banned by staff`; PrivateReason = `By {A.Name} ({A.UserId})`;
	})
	if not ok then T:Kick(`Banned by staff: {reason}`) return true, saved(`Ban API unavailable here ({err}); kicked instead`, Saved) end
	return true, saved(`Banned {T.Name} for {Length}`, Saved)
end }
-- (1b) the latest ban not lifted decides who may lift it: permanent (or none on record, set before 1b) the owner;
-- over 30 days an admin; else a moderator
C.Unban = { Run = function(A, _, a)
	local id = tonumber(a.UserId)
	if not id then return false, `Enter a UserId` end
	local lvl = Shared.Level(A)
	if not StaffConsole.CanTarget(lvl, Shared.LevelOf(id), id == A.UserId) then return false, `Can't use that on a higher rank` end
	local Rec, Err = StaffRecords.Get(id, true)
	if not Rec then return false, `{Err}: try again` end
	local Ban = Records.OpenBan(Rec)
	local Need = Records.UnbanLevel(Ban)
	if lvl < Need then
		return false, if Need == 3 then `Permanent bans can only be lifted by the owner` else `A ban over 30 days needs an admin to lift`
	end
	if not (Shared.TestSkipBanApi and RunService:IsStudio()) then
		local ok, err = pcall(Players.UnbanAsync, Players, { UserIds = { id }; ApplyToUniverse = true })
		if not ok then return false, tostring(err) end
	end
	if not Ban then return true, `Unbanned {id} (no ban on record)` end
	local At, By, Now = Ban.At, Ban.By, os.time()
	local _, Saved = StaffRecords.Write(id, function(R)
		local I = Records.Find(R, `Bans`, At, By)
		if I then R.Bans[I].Lifted = { By = A.UserId; At = Now } end
	end)
	return true, saved(`Unbanned {id}`, Saved)
end }
C.Mute = { Target = true; Run = function(A, T, a)
	local Now = os.time()
	local Until = Records.MuteUntil(tonumber(a.Minutes) or 0, Now)
	Muted[T.UserId] = Until
	local reason = str(a.Reason, 120)
	local Entry = { By = A.UserId; At = Now; Until = Until; Reason = if reason ~= `` then reason else nil }
	local _, Saved = StaffRecords.Write(T.UserId, function(R) Records.Push(R, `Mutes`, Entry) end)
	local Label = Records.MuteLabel(Entry)
	notify(T, `You've been muted`, if Until == 0 then `Staff muted your chat` else `Staff muted your chat for {Label}`, `Warning`)
	return true, saved(`Muted {T.Name} ({Label})`, Saved)
end }
C.Unmute = { Target = true; Run = function(A, T)
	Muted[T.UserId] = nil
	local Now = os.time()
	local _, Saved = StaffRecords.Write(T.UserId, function(R)
		for _, M in R.Mutes do if Records.MuteOn(M, Now) then M.Lifted = { By = A.UserId; At = Now } end end
	end)
	notify(T, `Chat restored`, nil, `Good`)
	return true, saved(`Unmuted {T.Name}`, Saved)
end }
C.Warn = { Target = true; Run = function(A, T, a)
	local reason = str(a.Reason, 160)
	notify(T, `Warning from staff`, if reason ~= `` then reason else `Please follow the school rules`, `Bad`)
	local Entry = { By = A.UserId; At = os.time(); Reason = reason }
	local _, Saved = StaffRecords.Write(T.UserId, function(R) Records.Push(R, `Warnings`, Entry) end)
	return true, saved(`Warned {T.Name}`, Saved)
end }
```

Delete the line `local Notes = {} :: { [number]: { Text: string, By: string, T: number } } -- staff notes ...` and
`function Shared.NoteFor(UserId: number) return Notes[UserId] end` (nothing else calls `NoteFor`: checked across
`tools/*/live` on 2026-11-23).

Replace `C.Note` with:

```lua
C.Note = { Target = true; Run = function(A, T, a)
	local text = str(a.Text, 300)
	if text == `` then return false, `Note is needed` end
	local Entry = { By = A.UserId; At = os.time(); Text = text }
	local _, Saved = StaffRecords.Write(T.UserId, function(R) Records.Push(R, `Notes`, Entry) end)
	return true, saved(`Noted on {T.Name}`, Saved)
end }
-- (1b) owner-only (Meta Level 3), Danger; TargetId is the picked UserId, who may be offline. Removing a ban or mute
-- entry doesn't lift it: Unban and Unmute stay the only way. The result message (the log's Detail) has the entry's text.
C.RemoveRecordEntry = { Target = true; Run = function(A, T, a, TargetId)
	local Entry, Saved, Err = StaffRecords.RemoveEntry(TargetId, a.List, a.At, a.By)
	if not Entry then return false, Err end
	local Who = if T then T.Name else StaffRecords.NameOf(TargetId)
	return true, saved(`Removed from {Who}'s {string.lower(a.List)}: {Records.EntryText(a.List, Entry)}`, Saved)
end }
```

In `Shared.Inspect`, replace `Note = Notes[T.UserId];` with `Note = latestNote(T.UserId);` and add above
`function Shared.Inspect`:

```lua
-- the newest saved note, for the inspector
local function latestNote(UserId: number)
	local R = StaffRecords.Cached(UserId)
	local N = R and R.Notes[#R.Notes]
	return if N then { Text = N.Text; By = StaffRecords.NameOf(N.By); T = N.At } else nil
end
```

In `playerList()`, replace `Muted = Muted[P.UserId] == true;` with `Muted = Muted[P.UserId] ~= nil;` and
`Note = Notes[P.UserId] ~= nil;` with `Note = hasNote(P.UserId);`, and add above `local function playerList()`:

```lua
local function hasNote(UserId: number): boolean
	local R = StaffRecords.Cached(UserId)
	return R ~= nil and #R.Notes > 0
end
```

- [ ] **Step 7: `Features.Admin`: Dispatch logs every call and knows the `user` target**

Replace the whole `function Shared.Dispatch(...) ... end` with:

```lua
-- returns ok, message, and the target's name and UserId for the log
local function dispatch(P: Player, lvl: number, Command: any, TargetUserId: any, Args: any): (any, any, string?, number?)
	local def = typeof(Command) == `string` and C[Command] or nil
	local m = def and Meta[Command]
	if not m then return false, `Unknown command` end
	if m.Level > lvl then return false, `Needs {StaffConsole.LEVEL_NAMES[m.Level]}` end
	local okA, clean = StaffConsole.CheckArgs(m.Args, Args, Shared.Lists())
	if not okA then return false, clean end
	Args = clean
	-- (2026-11-17, Roblox text rules) text staff type that other players see (kick / ban / warn / shutdown reasons,
	-- announcements, staff notes, granted titles, the action log) goes through Roblox's filter first, as the
	-- sender's broadcast text. If the filter can't answer, the command doesn't run: unfiltered text is never sent.
	for _, K in { `Reason`, `Text`, if Command == `GrantTitle` then `Title` else nil } do
		local Raw = Args[K]
		if typeof(Raw) == `string` and Raw:match(`%S`) then
			local OkF, Out = pcall(function()
				return TextService:FilterStringAsync(Raw:sub(1, 300), P.UserId, Enum.TextFilterContext.PublicChat):GetNonChatStringForBroadcastAsync()
			end)
			if not OkF or typeof(Out) ~= `string` then return false, `The text filter is busy: try again in a moment` end
			Args[K] = Out
		end
	end
	local T, TargetId
	if m.Target == `user` then
		TargetId = tonumber(TargetUserId)
		if not TargetId then return false, `Pick a student first` end
		T = Players:GetPlayerByUserId(TargetId)
		if not StaffConsole.CanTarget(lvl, Shared.LevelOf(TargetId), TargetId == P.UserId) then
			return false, `Can't use that on a higher rank`, StaffRecords.NameOf(TargetId), TargetId
		end
	elseif m.Target ~= `none` then
		T = Players:GetPlayerByUserId(tonumber(TargetUserId) or 0)
		if not T and m.Target == `required` then return false, `Pick a player first` end
		if T and not StaffConsole.CanTarget(lvl, Shared.Level(T), T == P) then return false, `Can't use that on a higher rank`, T.Name, T.UserId end
		TargetId = T and T.UserId
	elseif Command == `Unban` then
		TargetId = tonumber(Args.UserId)
	end
	local TName = if T then T.Name elseif TargetId then StaffRecords.NameOf(TargetId) else nil
	local ok, a, b = pcall(def.Run, P, T, Args, TargetId)
	if not ok then warn(`[Admin] {Command} failed: {a}`) return false, `Failed: {tostring(a):sub(1, 120)}`, TName, TargetId end
	log(P, Command, T and T.Name, typeof(Args.Reason) == `string` and Args.Reason or (Args.Amount and tostring(Args.Amount)) or nil)
	return a, b, TName, TargetId
end

function Shared.Dispatch(P: Player, Command: any, TargetUserId: any, Args: any)
	local lvl = Shared.Level(P)
	if lvl < 1 then return false, `Not staff` end
	if os.clock() - (LastRun[P] or 0) < 0.15 then return false, `Slow down` end
	LastRun[P] = os.clock()
	local a, b, TName, TargetId = dispatch(P, lvl, Command, TargetUserId, Args)
	-- (1b) the saved log: every call past the two checks above, run or refused (Features.StaffRecords buffers it)
	local m = typeof(Command) == `string` and Meta[Command] or nil
	StaffRecords.LogAdd({
		At = os.time(); Staff = P.Name; StaffId = P.UserId; Action = if typeof(Command) == `string` then Command else `?`;
		Target = TName; TargetId = TargetId; Detail = tostring(b or ``); Side = m and m.Side; Ok = a == true;
	})
	return a, b
end
```

- [ ] **Step 8: `Features.Admin`: the remotes, mutes on join and on time**

In `Shared.OnStart`, after the `StatusRF` lines, add:

```lua
	-- (1b) record, log and prefs remotes: level 1, checked here
	-- at most 8 reads a second per player: the console makes short bursts (a log row opens its history, the Unban card
	-- checks a record while the log loads), so a flat gap between calls would refuse real use
	local Reads = {} :: { [Player]: { number } }
	local function slow(P: Player): boolean
		local Now = os.clock()
		local L = Reads[P] or {}
		while L[1] and Now - L[1] > 1 do table.remove(L, 1) end
		Reads[P] = L
		if #L >= 8 then return true end
		table.insert(L, Now)
		return false
	end
	-- a copy of the record with ByName on every entry and every Lifted (the client shows names, not UserIds)
	local function withNames(Rec: any): any
		local Out = Records.Blank()
		for _, List in Records.LISTS do
			for _, E in Rec[List] do
				local Copy = table.clone(E)
				Copy.ByName = StaffRecords.NameOf(E.By)
				if typeof(E.Lifted) == `table` then Copy.Lifted = table.clone(E.Lifted) Copy.Lifted.ByName = StaffRecords.NameOf(E.Lifted.By) end
				table.insert(Out[List], Copy)
			end
		end
		return Out
	end
	local HistoryRF = Instance.new(`RemoteFunction`); HistoryRF.Name = `History`; HistoryRF.Parent = Folder
	HistoryRF.OnServerInvoke = function(P: Player, UserId: any)
		local lvl = Shared.Level(P)
		if lvl < 1 then return nil end
		if slow(P) then return { Ok = false; Error = `Slow down` } end
		local Id = tonumber(UserId)
		if not Id or Id ~= math.floor(Id) then return { Ok = false; Error = `Bad UserId` } end
		if not StaffConsole.CanTarget(lvl, Shared.LevelOf(Id), Id == P.UserId) then return { Ok = false; Error = `Can't view a higher rank's history` } end
		local Rec, Err = StaffRecords.Get(Id)
		if not Rec then return { Ok = false; Error = Err } end
		return { Ok = true; UserId = Id; Name = StaffRecords.NameOf(Id); Record = withNames(Rec) }
	end
	local LogRF = Instance.new(`RemoteFunction`); LogRF.Name = `LogDay`; LogRF.Parent = Folder
	LogRF.OnServerInvoke = function(P: Player, Offset: any, Filter: any)
		if Shared.Level(P) < 1 then return nil end
		if slow(P) then return { Ok = false; Error = `Slow down` } end
		local R, Err = StaffRecords.LogDay(Offset, Filter)
		if not R then return { Ok = false; Error = Err } end
		R.Ok = true
		return R
	end
	local PrefsRF = Instance.new(`RemoteFunction`); PrefsRF.Name = `Prefs`; PrefsRF.Parent = Folder
	PrefsRF.OnServerInvoke = function(P: Player)
		if Shared.Level(P) < 1 then return nil end
		local R, Err = StaffRecords.PrefsGet(P.UserId)
		if not R then return { Ok = false; Error = Err } end
		R.Ok = true
		return R
	end
	local SavePrefsRF = Instance.new(`RemoteFunction`); SavePrefsRF.Name = `SavePrefs`; SavePrefsRF.Parent = Folder
	SavePrefsRF.OnServerInvoke = function(P: Player, Favs: any, Side: any)
		if Shared.Level(P) < 1 then return false end
		StaffRecords.PrefsSet(P.UserId, Favs, Side)
		return true
	end
```

In the mute gate (`ch.ShouldDeliverCallback`), replace `return not (src and Muted[src.UserId])` with
`return not (src and Muted[src.UserId] ~= nil)`.

After the god-mode `RunService.Heartbeat` block, add:

```lua
	-- (1b) timed mutes end on time while they're here
	task.spawn(function()
		while true do
			task.wait(1)
			local Now = os.time()
			for Id, Until in Muted do
				if Until ~= 0 and Until <= Now then
					Muted[Id] = nil
					local P = Players:GetPlayerByUserId(Id)
					if P then notify(P, `Chat restored`, `Your mute has ended`, `Good`) end
				end
			end
		end
	end)
```

Replace

```lua
	Players.PlayerRemoving:Connect(function(P) God[P] = nil Frozen[P] = nil RankCache[P] = nil LastRun[P] = nil end)
	Players.PlayerAdded:Connect(function(P)
```

with

```lua
	Players.PlayerRemoving:Connect(function(P) God[P] = nil Frozen[P] = nil RankCache[P] = nil LastRun[P] = nil Reads[P] = nil Muted[P.UserId] = nil end)
	-- (1b) an open mute on their saved record is applied again when they join (and the record stays cached for the
	-- NOTE / MUTED row flags). A failed read leaves them unmuted for this visit (spec delta 7).
	local function loadRecord(P: Player)
		local Rec, Err = StaffRecords.Get(P.UserId, true)
		if not Rec then warn(`[Admin] record read for {P.Name} failed ({Err}): an open mute isn't applied this visit`) return end
		local M = Records.OpenMute(Rec, os.time())
		if M and P.Parent then Muted[P.UserId] = M.Until end
	end
	for _, P in Players:GetPlayers() do task.spawn(loadRecord, P) end
	Players.PlayerAdded:Connect(function(P)
		task.spawn(loadRecord, P)
```

- [ ] **Step 9: Install the three and run the Edit checks**

```bash
python -X utf8 -I tools/admin-console/install_inplace.py tools/admin-console/pre1b tools/admin-console/live AdminConsole1b_20261123 ReplicatedStorage.Functions.StaffConsole ServerScriptService.Services.Features.Admin.Meta ServerScriptService.Services.Features.Admin
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_pure.lua
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_registry.lua
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_play_server.lua
```
Expected: `PASS console_pure`, `PASS console_registry (67 commands)`, `PASS console_play_server (static: Edit)`.
Then copy the installed files into `pre1b/`, so later in-place installs compare against what Studio now runs:

```bash
cp tools/admin-console/live/ReplicatedStorage.Functions.StaffConsole.luau tools/admin-console/live/ServerScriptService.Services.Features.Admin.Meta.luau tools/admin-console/live/ServerScriptService.Services.Features.Admin.luau tools/admin-console/pre1b/
```

- [ ] **Step 10: Update `console_play_run.lua` for 1b**

In `checks/console_play_run.lua`:
- After `local Me = P.UserId` add `local T0 = os.time() -- (1b) this run's record entries are the ones By Me since T0`.
- In `Runs`, replace `{ "Mute" }, { "Unmute" },` with `{ "Mute", { Minutes = 10; Reason = "console test" } }, { "Unmute" },`.
- Replace `{ "Note", { Text = "console test" } }, { "Note", { Text = "" } },` with `{ "Note", { Text = "console test" } },`.
- After `want(false, "SetClub", { Club = "" }, Me, "Club is needed")` add:

```lua
-- (1b) a note needs text now (removing one is the owner's Remove history entry)
want(false, "Note", { Text = "" }, Me, "Note is needed")
want(false, "Mute", {}, Me, "Length is needed")
```

- Replace the line `for _, Id in { "Kick", "Ban", "Unban", "Shutdown" } do Seen[Id] = true end` with:

```lua
-- (1b) clean up this run's saved record entries, as the owner, through the new command (so it runs too)
do
	local SR = require(SSS.Features.StaffRecords)
	local Rec = SR.Get(Me, true)
	local N = 0
	for _, List in { "Notes", "Warnings", "Bans", "Mutes" } do
		for _, E in table.clone(Rec and Rec[List] or {}) do
			if E.By == Me and E.At >= T0 then want(true, "RemoveRecordEntry", { List = List; At = E.At; By = E.By }, Me, "Removed") N += 1 end
		end
	end
	if N == 0 then table.insert(Fails, "no record entries from this run to clean up (Warn, Mute and Note should have written some)") end
	Seen.RemoveRecordEntry = true
end
for _, Id in { "Kick", "Ban", "Unban", "Shutdown" } do Seen[Id] = true end
```

- [ ] **Step 11: Write `records_play_a.lua` and `records_cleanup.lua`**

`tools/admin-console/checks/records_play_a.lua`:

```lua
-- records_play_a.lua: Server, Play, slot 2, [Test] stores only. Run with run_live.py (the game's own VM).
-- 1b spec §6, the first half: Warn, Note, Mute (each length) and Ban written through the real Dispatch and read back
-- from the store; the unban rule at levels 1 and 3; Remove history entry refused at 2, passes at 3 and is logged; the
-- log saved and read back. It leaves an open 1-day mute ("1b restart") and a marker key (its start time and the owner's
-- prefs before the round) for records_play_b.lua and records_cleanup.lua.
local Players = game:GetService("Players")
local DataStoreService = game:GetService("DataStoreService")
local RunService = game:GetService("RunService")
local SSS = game.ServerScriptService.Services
local Admin = require(SSS.Features.Admin)
local SR = require(SSS.Features.StaffRecords)
local P = Players:GetPlayers()[1]
if not P then return "FAIL no player" end
if not RunService:IsStudio() or SR.PREFIX ~= "[Test] " then return "FAIL not on the [Test] stores" end
local Me, T0 = P.UserId, os.time()
local Fails, Ran = {}, 0
local function go(Cmd, Args, Target)
	task.wait(0.2) -- Dispatch's 0.15 s rate limit
	if script:GetAttribute("Stop") then error("stopped by run_live.py (timeout)", 0) end
	return Admin.Dispatch(P, Cmd, Target, Args or {})
end
local function want(Ok, Cmd, Args, Target, Expect)
	local A, B = go(Cmd, Args, Target)
	Ran += 1
	if (A == true) ~= Ok then table.insert(Fails, `{Cmd}: got {tostring(A)} {tostring(B)}`) return end
	if Expect and not string.find(tostring(B), Expect, 1, true) then table.insert(Fails, `{Cmd}: "{tostring(B)}", want "{Expect}"`) end
end
local function level(N) P:SetAttribute("NHTestLevel", N) task.wait(0.3) end
local function body()
	local PS = DataStoreService:GetDataStore("[Test] NHStaffPrefs_v1")
	PS:SetAsync("check1b_" .. Me, { T0 = T0; Prefs = PS:GetAsync("u_" .. Me) })
	Admin.TestSkipBanApi = true
	want(true, "Warn", { Reason = "1b test warn" }, Me, "Saved")
	want(true, "Note", { Text = "1b test note" }, Me, "Saved")
	want(false, "Note", { Text = "" }, Me, "Note is needed")
	for _, Min in { 10, 60, 1440, 0 } do
		want(true, "Mute", { Minutes = Min; Reason = "1b test" }, Me, "Saved")
		local U = Admin.MutedUntil(Me)
		if U == nil or (Min == 0 and U ~= 0) or (Min > 0 and math.abs(U - (os.time() + Min * 60)) > 3) then
			table.insert(Fails, `Mute {Min}: MutedUntil is {tostring(U)}`)
		end
		want(true, "Unmute", {}, Me, "Saved")
		if Admin.MutedUntil(Me) ~= nil then table.insert(Fails, `Unmute after {Min}: still muted`) end
	end
	level(3) want(true, "Ban", { Days = 0; Reason = "1b test" }, Me, "Ban API skipped")
	level(1) want(false, "Unban", { UserId = Me }, nil, "Permanent bans can only be lifted by the owner")
	level(3) want(true, "Unban", { UserId = Me }, nil, "Unbanned")
	level(1) want(true, "Ban", { Days = 7; Reason = "1b test" }, Me, "Ban API skipped")
	want(true, "Unban", { UserId = Me }, nil, "Unbanned")
	level(nil)

	-- read back from the store, not the cache
	local Rec, Err = SR.Get(Me, true)
	if not Rec then table.insert(Fails, "read back: " .. tostring(Err)) return end
	local function mine(List, Pred)
		local N = 0
		for _, E in Rec[List] do if E.By == Me and E.At >= T0 and Pred(E) then N += 1 end end
		return N
	end
	if mine("Warnings", function(E) return E.Reason == "1b test warn" end) ~= 1 then table.insert(Fails, "the warning didn't read back") end
	if mine("Notes", function(E) return E.Text == "1b test note" end) ~= 1 then table.insert(Fails, "the note didn't read back") end
	for _, Min in { 10, 60, 1440 } do
		if mine("Mutes", function(E) return E.Until - E.At == Min * 60 and E.Lifted ~= nil end) ~= 1 then
			table.insert(Fails, `the {Min} min mute didn't read back lifted`)
		end
	end
	if mine("Mutes", function(E) return E.Until == 0 and E.Lifted ~= nil end) ~= 1 then table.insert(Fails, "the until-unmuted mute didn't read back lifted") end
	if mine("Bans", function(E) return E.Days == 0 and E.Lifted ~= nil end) ~= 1 then table.insert(Fails, "the permanent ban didn't read back lifted") end
	if mine("Bans", function(E) return E.Days == 7 and E.Lifted ~= nil end) ~= 1 then table.insert(Fails, "the 7-day ban didn't read back lifted") end

	-- Remove history entry: refused at 2, passes at 3, logged
	local W
	for _, E in Rec.Warnings do if E.Reason == "1b test warn" and E.By == Me and E.At >= T0 then W = E end end
	if W then
		level(2) want(false, "RemoveRecordEntry", { List = "Warnings"; At = W.At; By = W.By }, Me, "Needs the owner")
		level(nil) want(true, "RemoveRecordEntry", { List = "Warnings"; At = W.At; By = W.By }, Me, "Removed")
		local Rec2 = SR.Get(Me, true)
		for _, E in Rec2 and Rec2.Warnings or {} do
			if E.At == W.At and E.By == W.By and E.Reason == W.Reason then table.insert(Fails, "the warning is still there after RemoveRecordEntry") end
		end
	end

	-- the log: saved, then today read back from the store
	if not SR.FlushLog() then table.insert(Fails, "FlushLog failed") end
	local Day = SR.LogDay(0, { Query = "RemoveRecordEntry" })
	local Removed, Refused = false, false
	for _, E in Day and Day.Rows or {} do
		if E.At >= T0 and E.StaffId == Me then
			if E.Ok and string.find(E.Detail, "1b test warn", 1, true) then Removed = true end
			if not E.Ok and string.find(E.Detail, "Needs the owner", 1, true) then Refused = true end
		end
	end
	if not Removed then table.insert(Fails, "the removal isn't in today's log with the entry's text") end
	if not Refused then table.insert(Fails, "the refused removal isn't in today's log") end
	local Ref = SR.LogDay(0, { Chip = "Refused"; Query = "Unban" })
	if not (Ref and Ref.Total >= 1) then table.insert(Fails, "the refused Unban isn't under the Refused chip") end

	-- for the restart: an open mute
	want(true, "Mute", { Minutes = 1440; Reason = "1b restart" }, Me, "Saved")
end
local OkRun, Err = xpcall(body, debug.traceback)
if not OkRun then table.insert(Fails, "run stopped: " .. tostring(Err):sub(1, 300)) end
P:SetAttribute("NHTestLevel", nil)
Admin.TestSkipBanApi = false
if #Fails > 0 then return "FAIL " .. #Fails .. " of " .. Ran .. "\n" .. table.concat(Fails, "\n") end
return `PASS records_play_a ({Ran} calls; T0 {T0})`
```

`tools/admin-console/checks/records_cleanup.lua`:

```lua
-- records_cleanup.lua: Server, Play, [Test] stores only. Run with run_live.py after records_play_a (and, in the
-- restart round, after records_play_b). As the owner, through RemoveRecordEntry: unmute, then remove every record entry
-- By the owner since records_play_a's start (the marker's T0). Then put the owner's prefs back as they were before the
-- round and delete the marker.
local Players = game:GetService("Players")
local DataStoreService = game:GetService("DataStoreService")
local RunService = game:GetService("RunService")
local SSS = game.ServerScriptService.Services
local Admin = require(SSS.Features.Admin)
local SR = require(SSS.Features.StaffRecords)
local P = Players:GetPlayers()[1]
if not P then return "FAIL no player" end
if not RunService:IsStudio() or SR.PREFIX ~= "[Test] " then return "FAIL not on the [Test] stores" end
local Me = P.UserId
local PS = DataStoreService:GetDataStore("[Test] NHStaffPrefs_v1")
local Marker = PS:GetAsync("check1b_" .. Me)
if typeof(Marker) ~= "table" or typeof(Marker.T0) ~= "number" then return "FAIL no marker from records_play_a" end
local T0 = Marker.T0
local Fails, Removed = {}, 0
P:SetAttribute("NHTestLevel", nil)
task.wait(0.3)
local function go(Cmd, Args, Target)
	task.wait(0.2)
	return Admin.Dispatch(P, Cmd, Target, Args or {})
end
local A, B = go("Unmute", {}, Me)
if A ~= true then table.insert(Fails, "Unmute: " .. tostring(B)) end
local Rec = SR.Get(Me, true)
if not Rec then return "FAIL record read failed: run again" end
for _, List in { "Notes", "Warnings", "Bans", "Mutes" } do
	for _, E in table.clone(Rec[List]) do
		if E.By == Me and E.At >= T0 then
			local A2, B2 = go("RemoveRecordEntry", { List = List; At = E.At; By = E.By }, Me)
			if A2 == true then Removed += 1 else table.insert(Fails, `remove {List} {E.At}: {tostring(B2)}`) end
		end
	end
end
local After = SR.Get(Me, true)
for _, List in { "Notes", "Warnings", "Bans", "Mutes" } do
	for _, E in After and After[List] or {} do
		if E.By == Me and E.At >= T0 then table.insert(Fails, `left behind: {List} at {E.At}`) end
	end
end
-- prefs as before the round: a waiting save goes first, so it can't land after the put-back
SR.PrefsFlush(Me)
if typeof(Marker.Prefs) == "table" then PS:SetAsync("u_" .. Me, Marker.Prefs) else PS:RemoveAsync("u_" .. Me) end
PS:RemoveAsync("check1b_" .. Me)
if #Fails > 0 then return "FAIL " .. #Fails .. "\n" .. table.concat(Fails, "\n") end
return `PASS records_cleanup (removed {Removed})`
```

- [ ] **Step 12: The first Play round (server only)**

1. `start_stop_play` start.
2. `bash E:/NH-transform/tools/forms/harness/round_start.sh` (a fresh slot 2 snapshot).
3. Record `cine.lua` (scratchpad; the 1a Task 8 snippet: CineState, Seen, Origin).
4. `python -X utf8 -I tools/admin-console/run_live.py tools/admin-console/checks/console_play_server.lua 60` → `PASS console_play_server (static: Play)`.
5. `python -X utf8 -I tools/admin-console/run_live.py tools/admin-console/checks/console_play_run.lua 300` → `PASS console_play_run (N calls)`.
6. `python -X utf8 -I tools/admin-console/run_live.py tools/admin-console/checks/records_play_a.lua 240` → `PASS records_play_a (...)`.
7. `python -X utf8 -I tools/admin-console/run_live.py tools/admin-console/checks/records_cleanup.lua 240` → `PASS records_cleanup (removed N)`.
8. `restore.py`, record `cine.lua` again, `start_stop_play` stop.

Fix what fails and repeat the round until all four pass. Write the PASS lines in `REPORT.md` under a new
"## Phase 1b" heading, with CineState, Seen and Origin before and after.

- [ ] **Step 13: Commit (on the owner's word)**

```bash
git add tools/admin-console/live tools/admin-console/pre1b tools/admin-console/checks tools/admin-console/REPORT.md
git commit -m "Console 1b: server wiring (saved Warn/Note/Mute/Ban/Unban, Remove history entry, staff log, mutes on join, History/LogDay/Prefs remotes)"
```

---

### Task 4: The client model (`StaffConsole.Model`, pure, TDD)

**Files:**
- Modify: `tools/admin-console/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.Model.luau`
- Test: `tools/admin-console/checks/console_model.lua`

**Interfaces:**
- Consumes: `Functions.StaffRecords` (Task 1).
- Produces (Task 5 uses these):
  - `Model.New()` adds `Offline = false`, `Log = { Day = 0, Query = "", Chip = "All", Page = 1 }`,
    `PrefsTried = false`, `PrefsOk = false`.
  - `Model.Pick(S, UserId, Offline?)`.
  - `Model.Ready(Def, Values, Selected, Lists?, Offline?)`: `Target = "user"` needs a pick; `"required"` refuses an
    offline pick.
  - `Model.LoadPrefs(S, Prefs, Defs, Sections)`.
  - `Model.Timeline(Rec, Level, Now) -> { { Kind, List, At, By, Who, Text, State: "lifted"|"ended"|nil, Lifted: boolean, CanRemove: boolean } }`.
  - `Model.Summary(Rec, Now, Clock?) -> string`.
  - `Model.UnbanNote(H, Clock?) -> string?`.
  - `Model.DayLabel(Offset, Now) -> string`; `Model.LogHead(E, Clock?) -> string`.

- [ ] **Step 1: Write the failing checks**

In `checks/console_model.lua`, before the final `if #Fails > 0` line, add:

```lua
-- 1b: offline picks, user targets, prefs, the timeline, the summary, the Unban note, log labels
local S2 = M.New()
Eq(S2.Log and S2.Log.Day, 0, "log starts on today") Eq(S2.Log and S2.Log.Chip, "All", "log starts on All")
M.Pick(S2, 9, true)
Eq(S2.Offline, true, "an offline pick") Eq(S2.Selected, 9, "picked 9")
M.Pick(S2, 3)
Eq(S2.Offline, false, "an online pick")
Eq((M.Ready({ Id = "W"; Target = "required"; Args = {} }, {}, 9, nil, true)), false, "required needs them in the server")
Eq(select(2, M.Ready({ Id = "W"; Target = "required"; Args = {} }, {}, 9, nil, true)), "They're not in this server: only their history works", "offline message")
Eq((M.Ready({ Id = "R"; Target = "user"; Args = {} }, {}, nil)), false, "user target needs a pick")
Eq((M.Ready({ Id = "R"; Target = "user"; Args = {} }, {}, 9, nil, true)), true, "user target works offline")

local SECTIONS1B = { Moderate = { "Student", "Server", "Log" }, Test = { "Character", "Progress", "School", "Story", "World", "Spawns", "Self" } }
local S3 = M.New()
M.SetLevel(S3, 2, SECTIONS1B)
M.LoadPrefs(S3, { Favs = { "Warn", "Gone", "Warn" }; Side = "Test" }, { { Id = "Warn" }, { Id = "Goto" } }, SECTIONS1B)
Eq(#S3.Favs, 1, "prefs: unknown and repeated ids dropped") Eq(S3.Favs[1], "Warn", "prefs: known fav kept")
Eq(S3.Side, "Test", "prefs: saved side") Eq(S3.Section, "Character", "prefs: the side's first section")
local S4 = M.New()
M.SetLevel(S4, 1, SECTIONS1B)
M.LoadPrefs(S4, { Favs = {}; Side = "Test" }, {}, SECTIONS1B)
Eq(S4.Side, "Moderate", "prefs: a side the level doesn't allow is ignored")

local Rec = {
	Warnings = { { By = 1; At = 100; Reason = "spam"; ByName = "mod" } };
	Notes = { { By = 1; At = 300; Text = "watch them"; ByName = "mod" } };
	Bans = { { By = 2; At = 200; Days = 7; Reason = "x"; Lifted = { By = 2; At = 250 } } };
	Mutes = { { By = 1; At = 400; Until = 0 } };
}
local TL = M.Timeline(Rec, 3, 1000)
Eq(#TL, 4, "timeline entries") Eq(TL[1].Kind, "Mute", "newest first") Eq(TL[1].Lifted, false, "an open mute isn't greyed")
Eq(TL[2].Kind, "Note", "then the note") Eq(TL[2].Who, "mod", "who: ByName")
Eq(TL[3].Kind, "Ban", "then the ban") Eq(TL[3].State, "lifted", "a lifted ban") Eq(TL[3].Lifted, true, "greyed")
Eq(TL[3].Who, "2", "who without ByName: the UserId") Eq(TL[3].Text, "7-day ban: x", "ban text")
Eq(TL[4].Kind, "Warn", "oldest last") Eq(TL[1].CanRemove, true, "the owner can remove")
Eq(M.Timeline(Rec, 2, 1000)[1].CanRemove, false, "an admin can't")
Eq(M.Timeline({ Mutes = { { By = 1; At = 0; Until = 600 } } }, 3, 1000)[1].State, "ended", "a mute that ended on time")
Eq(M.Summary(Rec, 1000), "1 warning · 1 note · 1 ban (lifted) · muted until unmuted", "summary")
local D = function() return "D" end
Eq(M.UnbanNote(nil, D), nil, "no note while loading")
Eq(M.UnbanNote({ Ok = false; Error = "History unavailable" }, D), "History unavailable", "unban note: the error")
Eq(M.UnbanNote({ Ok = true; Record = {} }, D), "No ban on record: counts as permanent (owner only)", "unban note: none")
Eq(M.UnbanNote({ Ok = true; Record = { Bans = { { By = 2; At = 5; Days = 0; ByName = "boss" } } } }, D), "Lifts: permanent ban by boss, D (owner only)", "unban note: permanent")
Eq(M.UnbanNote({ Ok = true; Record = { Bans = { { By = 2; At = 5; Days = 7; ByName = "mod" } } } }, D), "Lifts: 7-day ban by mod, D", "unban note: 7 days")
Eq(M.DayLabel(0, 86400 * 10 + 5), "Today", "day 0") Eq(M.DayLabel(1, 86400 * 10 + 5), "Yesterday", "day 1")
Eq(M.DayLabel(2, 86400 * 10 + 5), "Fri 09", "day 2 (UTC day 8 = Fri 9 Jan 1970)")
Eq(M.LogHead({ At = 0; Staff = "mod"; Action = "Warn"; Target = "kid" }, function() return "09:00" end), "09:00 · mod · Warn · kid", "log head")
Eq(M.LogHead({ At = 0; Staff = "mod"; Action = "Announce" }, function() return "09:00" end), "09:00 · mod · Announce", "log head without a target")
```

Run: `python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_model.lua`
Expected: `FAIL` with the new lines failing (`Log` nil, `LoadPrefs`, `Timeline` missing, ...).

- [ ] **Step 2: Write the model changes**

In `live/...Controllers.Gui.StaffConsole.Model.luau`:

Replace the header comment and the first lines up to `function Model.New() ... end` with:

```lua
--[[ StaffConsole.Model (client, pure): the console's state rules. No Instances; checks/console_model.lua tests it.
	1b: offline picks (from the Log), saved prefs, the history timeline and summary, the Unban note, log labels. ]]
local Records = require(game:GetService("ReplicatedStorage"):WaitForChild("Functions"):WaitForChild("StaffRecords"))
local Model = {}
local RECENT_MAX, FEED_MAX = 5, 5

function Model.New()
	return { Side = "Moderate"; Section = "Student"; Selected = nil :: number?; Offline = false; Recent = {} :: { number };
		Favs = {} :: { string }; Feed = {} :: { any }; Filter = ""; Level = 0;
		Log = { Day = 0; Query = ""; Chip = "All"; Page = 1 }; PrefsTried = false; PrefsOk = false }
end
```

Replace `function Model.Pick(S: any, UserId: number) ... end` with:

```lua
-- Offline: picked from the Log, not in this server (only their history works)
function Model.Pick(S: any, UserId: number, Offline: boolean?)
	S.Selected = UserId
	S.Offline = Offline == true
	local I = table.find(S.Recent, UserId)
	if I then table.remove(S.Recent, I) end
	table.insert(S.Recent, 1, UserId)
	while #S.Recent > RECENT_MAX do table.remove(S.Recent) end
end
```

Replace the first line of `Model.Ready` and its target check:

```lua
function Model.Ready(Def: any, Values: any, Selected: number?, Lists: any?, Offline: boolean?): (boolean, string?, any)
	if (Def.Target == "required" or Def.Target == "user") and not Selected then return false, "Pick a student on the left first", nil end
	if Def.Target == "required" and Offline then return false, "They're not in this server: only their history works", nil end
```

(the rest of `Ready` stays). Before `return Model`, add:

```lua
-- saved favourites and side (spec 1b §4): ids no longer in the registry are dropped; a side the level can't open is ignored
function Model.LoadPrefs(S: any, P: any, Defs: any, Sections: any)
	if typeof(P) ~= "table" then return end
	local Known = {}
	for _, D in Defs do Known[D.Id] = true end
	S.Favs = Records.CleanFavs(P.Favs, Known)
	local Side = Records.CleanSide(P.Side)
	if Side and table.find(Model.Sides(S.Level), Side) then
		S.Side = Side
		S.Section = (Sections[Side] or {})[1]
	end
end

-- the history timeline: newest first; lifted, or ended on time, bans and mutes are greyed; the owner may remove
function Model.Timeline(Rec: any, Level: number, Now: number): any
	local Out = {}
	for _, T in Records.Timeline(Records.Normalize(Rec)) do
		local E = T.Entry
		local State = nil
		if T.List == "Bans" or T.List == "Mutes" then
			if E.Lifted then State = "lifted"
			elseif (T.List == "Bans" and not Records.BanOn(E, Now)) or (T.List == "Mutes" and not Records.MuteOn(E, Now)) then State = "ended" end
		end
		table.insert(Out, { Kind = T.Kind; List = T.List; At = E.At; By = E.By; Who = E.ByName or tostring(E.By);
			Text = Records.EntryText(T.List, E); State = State; Lifted = State ~= nil; CanRemove = Level >= 3 })
	end
	return Out
end

function Model.Summary(Rec: any, Now: number, Clock: ((number) -> string)?): string
	return Records.Summary(Records.Normalize(Rec), Now, Clock)
end

-- the line the Unban card shows: the ban it would lift (H = the History result for the typed UserId; nil = loading)
function Model.UnbanNote(H: any, Clock: ((number) -> string)?): string?
	if H == nil then return nil end
	if not H.Ok then return H.Error or "History unavailable" end
	local Ban = Records.OpenBan(Records.Normalize(H.Record))
	if not Ban then return "No ban on record: counts as permanent (owner only)" end
	local Fmt = Clock or function(T: number): string return os.date("%d %b", T) end
	local Length = if (tonumber(Ban.Days) or 0) == 0 then "permanent" else `{Ban.Days}-day`
	return `Lifts: {Length} ban by {Ban.ByName or tostring(Ban.By)}, {Fmt(Ban.At)}{if Records.UnbanLevel(Ban) == 3 then " (owner only)" else ""}`
end

-- log days are UTC days (the server's keys), so the labels are too
function Model.DayLabel(Offset: number, Now: number): string
	if Offset == 0 then return "Today" end
	if Offset == 1 then return "Yesterday" end
	return os.date("!%a %d", (Records.Day(Now) - Offset) * 86400)
end

function Model.LogHead(E: any, Clock: ((number) -> string)?): string
	local Fmt = Clock or function(T: number): string return os.date("%H:%M", T) end
	return `{Fmt(E.At)} · {E.Staff} · {E.Action}{if E.Target then " · " .. E.Target else ""}`
end
```

- [ ] **Step 3: Install and run the check**

```bash
python -X utf8 -I tools/admin-console/install_inplace.py tools/admin-console/pre1b tools/admin-console/live AdminConsole1b_20261123 StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.Model
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_model.lua
cp tools/admin-console/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.Model.luau tools/admin-console/pre1b/
```
Expected: `PASS console_model`.

- [ ] **Step 4: Commit (on the owner's word)**

```bash
git add tools/admin-console/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.Model.luau tools/admin-console/pre1b tools/admin-console/checks/console_model.lua
git commit -m "Console 1b: model (offline picks, saved prefs, history timeline and summary, Unban note, log labels)"
```

---

### Task 5: The console UI (Cards, View, shell) and the client check

**Files:**
- Modify: `tools/admin-console/live/...Controllers.Gui.StaffConsole.Cards.luau`
- Modify: `tools/admin-console/live/...Controllers.Gui.StaffConsole.View.luau`
- Modify: `tools/admin-console/live/...Controllers.Gui.StaffConsole.luau`
- Modify: `tools/admin-console/checks/console_play_client.lua`
- Create: `tools/admin-console/checks/records_play_client.lua`

**Interfaces:**
- Consumes: Task 3 remotes (`History`, `LogDay`, `Prefs`, `SavePrefs`) and command `RemoveRecordEntry`; Task 4 Model.
- Produces:
  - `Cards.Chip(Parent, Name, Text, On, Danger?, W?) -> TextButton` (the 1a local `chip`, now public).
  - Card `Opts.Note: string?` (shown in place of the help, in brass).
  - `Ctx` gains `History` (the picked student's History result), `HistoryFor(UserId)` and `LogResult`.
  - `Ctx.Handlers` gains `LogDay(Offset)`, `LogQuery(Q)`, `LogChip(Chip)`, `LogPage(Delta)`, `OpenLogRow(E)`,
    `WantHistory(UserId)` and `Remove(Row)`.
  - Probe commands `Log`, `OpenRow`, `History`, `Fav` and `Prefs`.
- Instance names the checks look for: `LogDays`, `Day_0`..`Day_6`, `LogSearch`, `LogChips`, `Chip_All`, `Chip_Moderate`,
  `Chip_Test`, `Chip_Refused`, `LogRows`, `LogRow_<i>`, `LogPrev`, `LogNext`, `LogPage`, `Entry_<i>` (with `Remove`
  at level 3) in the context `Body`.

- [ ] **Step 1: Cards**

In `live/...StaffConsole.Cards.luau`:

After `local function chip(...) ... end`, add `Cards.Chip = chip`.

In `Cards.Options`, replace

```lua
				for _, C in Choices do
					local Text = if A.Name == "Days" then (if C == 0 then "Forever" else C .. "d") elseif A.Name == "Tier" and typeof(C) == "number" then ({ "I", "II", "III" })[C] else tostring(C)
```

with

```lua
				for I, C in Choices do
					-- (1b) Labels (Mute's lengths) name each choice in order
					local Text = if A.Labels and A.Labels[I] then A.Labels[I]
						elseif A.Name == "Days" then (if C == 0 then "Forever" else C .. "d")
						elseif A.Name == "Tier" and typeof(C) == "number" then ({ "I", "II", "III" })[C] else tostring(C)
```

In `Cards.Card`, change its comment to
`-- one card. Opts = { Values, Lists, Selected, Fav: boolean, OnRun(Def, Values), OnFav(Def), OnPick, Redraw, Reduced, Note? }`
and replace the `Help` line with:

```lua
	-- (1b) Note: a line in place of the help (the Unban card shows the ban it would lift)
	Cards.Text(C, "Help", Opts.Note or Def.Help, 20, FACE.Body, if Opts.Note then COL.Brass else COL.Dim, UDim2.fromOffset(76, 44), UDim2.fromOffset(284, 50), true)
```

- [ ] **Step 2: View: the Unban note, the Log section, the timeline**

In `live/...StaffConsole.View.luau`:

Update the header's `Ctx` description to add `History, HistoryFor, LogResult` and the new handlers.

In `grid`, replace these two lines (after `Ctx.Values[D.Id] = Ctx.Values[D.Id] or {}`):

```lua
		Cards.Card(G, D, UDim2.fromOffset(Col * 392, Row * 180), {
			Values = Ctx.Values[D.Id]; Lists = Ctx.Lists; Fav = table.find(S.Favs, D.Id) ~= nil; Reduced = Ctx.Reduced;
```

with the block below. `H` is `grid`'s own `Ctx.Handlers`. The shell's redraw waits while a text box is focused
(`mustWait`), so the note appears once the UserId box loses focus and the history reply arrives.

```lua
		local Note = nil
		if D.Id == "Unban" then
			local Id = tonumber(Ctx.Values.Unban and Ctx.Values.Unban.UserId)
			if Id then
				H.WantHistory(Id)
				Note = Model.UnbanNote(Ctx.HistoryFor(Id)) or "Checking their record…"
			end
		end
		Cards.Card(G, D, UDim2.fromOffset(Col * 392, Row * 180), {
			Values = Ctx.Values[D.Id]; Lists = Ctx.Lists; Fav = table.find(S.Favs, D.Id) ~= nil; Reduced = Ctx.Reduced; Note = Note;
```

(the rest of the opts table stays).

Add after `grid`:

```lua
-- the Log section (spec 1b §5): a day picker (today and the 6 days before), search, chips, 50 rows a page. A row opens
-- its target's history in the right-hand panel, even if they're offline.
local function logView(Dyn: Instance, Ctx: any)
	local H, L = Ctx.Handlers, Ctx.S.Log
	local X, W = Ctx.X, Ctx.W
	local function strip(Name: string, PX: number, PY: number, PW: number): Instance
		local F = New("Frame", { Name = Name; BackgroundTransparency = 1; Position = UDim2.fromOffset(PX, PY); Size = UDim2.fromOffset(PW, 40) }, Dyn)
		New("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal; Padding = UDim.new(0, 6); SortOrder = Enum.SortOrder.LayoutOrder }, F)
		return F
	end
	local Days = strip("LogDays", X, 160, W)
	local Now = os.time()
	for Off = 0, 6 do
		local B = Cards.Chip(Days, "Day_" .. Off, Model.DayLabel(Off, Now), L.Day == Off)
		local Holder = B.Parent :: any
		Holder.LayoutOrder = Off
		B.Activated:Connect(function() H.LogDay(Off) end)
	end
	local Box = New("TextBox", { Name = "LogSearch"; PlaceholderText = "Staff, student, UserId or action"; Text = L.Query; TextSize = 20; FontFace = FACE.Body;
		TextColor3 = COL.Bone; PlaceholderColor3 = COL.Dim; BackgroundColor3 = COL.IronHi; ClearTextOnFocus = false;
		Position = UDim2.fromOffset(X, 208); Size = UDim2.fromOffset(330, 40); TextXAlignment = Enum.TextXAlignment.Left }, Dyn)
	New("UICorner", { CornerRadius = UDim.new(0, 8) }, Box)
	New("UIPadding", { PaddingLeft = UDim.new(0, 12); PaddingRight = UDim.new(0, 8) }, Box)
	Box.FocusLost:Connect(function() H.LogQuery(Box.Text) end)
	local Chips = strip("LogChips", X + 340, 210, W - 340)
	for I, C in { "All", "Moderate", "Test", "Refused" } do
		local B = Cards.Chip(Chips, "Chip_" .. C, C, L.Chip == C)
		local Holder = B.Parent :: any
		Holder.LayoutOrder = I
		B.Activated:Connect(function() H.LogChip(C) end)
	end
	local List = New("ScrollingFrame", { Name = "LogRows"; BackgroundTransparency = 1; Position = UDim2.fromOffset(X, 258); Size = UDim2.fromOffset(W + 8, 438);
		CanvasSize = UDim2.new(); AutomaticCanvasSize = Enum.AutomaticSize.Y; ScrollBarThickness = 6; Selectable = false }, Dyn)
	New("UIListLayout", { Padding = UDim.new(0, 4); SortOrder = Enum.SortOrder.LayoutOrder }, List)
	local R = Ctx.LogResult
	if R == nil then Text(List, "Status", "Loading…", 20, FACE.Body, COL.Dim, UDim2.new(), UDim2.fromOffset(W, 28)) return end
	if not R.Ok then Text(List, "Status", R.Error or "Log unavailable", 20, FACE.Bold, COL.Crimson, UDim2.new(), UDim2.fromOffset(W, 28)) return end
	for I, E in R.Rows do
		local B = New("TextButton", { Name = "LogRow_" .. I; Text = ""; AutoButtonColor = true; BackgroundColor3 = COL.IronHi; BackgroundTransparency = 0.3;
			Size = UDim2.fromOffset(W - 4, 52); LayoutOrder = I }, List)
		New("UICorner", { CornerRadius = UDim.new(0, 6) }, B)
		Text(B, "Head", Model.LogHead(E), 20, FACE.Bold, if E.Ok then COL.Bone else COL.Crimson, UDim2.fromOffset(10, 3), UDim2.new(1, -20, 0, 24))
		Text(B, "Detail", if E.Detail ~= "" then E.Detail else "—", 20, FACE.Body, COL.Dim, UDim2.fromOffset(10, 26), UDim2.new(1, -20, 0, 24))
		B.Activated:Connect(function() H.OpenLogRow(E) end)
	end
	if #R.Rows == 0 then Text(List, "Status", "Nothing logged for this day.", 20, FACE.Body, COL.Dim, UDim2.new(), UDim2.fromOffset(W, 28)) end
	local function pageButton(Name: string, Label: string, PX: number, Delta: number, On: boolean)
		local B = New("TextButton", { Name = Name; Text = Label; TextSize = 20; FontFace = FACE.Bold; TextColor3 = if On then COL.Bone else COL.Dim;
			BackgroundColor3 = COL.IronHi; AutoButtonColor = On; Active = On; Position = UDim2.fromOffset(PX, 702); Size = UDim2.fromOffset(100, 40) }, Dyn)
		New("UICorner", { CornerRadius = UDim.new(0, 8) }, B)
		if On then B.Activated:Connect(function() H.LogPage(Delta) end) end
	end
	pageButton("LogPrev", "Prev", X, -1, R.Page > 1)
	local Pg = Text(Dyn, "LogPage", `Page {R.Page} of {R.Pages} · {R.Total} entries`, 20, FACE.Body, COL.Dim, UDim2.fromOffset(X + 110, 710), UDim2.fromOffset(W - 220, 28))
	Pg.TextXAlignment = Enum.TextXAlignment.Center
	pageButton("LogNext", "Next", X + W - 100, 1, R.Page < R.Pages)
end
```

Add before `local function context`:

```lua
-- the saved record (spec 1b §5): the summary line, then newest first with one icon per kind; lifted or ended bans and
-- mutes greyed; at level 3 a remove button on each, with the 0.8 s hold
local function history(Body: Instance, Ctx: any, Next: () -> number, line: (string, number?, Color3?, boolean?) -> ())
	local H = Ctx.History
	line("History", 22, COL.Brass, true)
	if H == nil then line("Loading…", 20, COL.Dim) return end
	if not H.Ok then line(H.Error or "History unavailable", 20, COL.Crimson, true) return end
	local Now = os.time()
	local Rows = Model.Timeline(H.Record, Ctx.S.Level, Now)
	if #Rows == 0 then line("Nothing on record.", 20, COL.Dim) return end
	line(Model.Summary(H.Record, Now), 20, COL.Bone, true)
	for I, R in Rows do
		local F = New("Frame", { Name = "Entry_" .. I; BackgroundTransparency = 1; Size = UDim2.new(1, -8, 0, 0); AutomaticSize = Enum.AutomaticSize.Y; LayoutOrder = Next() }, Body)
		New("UIPadding", { PaddingBottom = UDim.new(0, 6) }, F)
		local Img = Art.Image(R.Kind)
		if Img then
			New("ImageLabel", { Name = "Icon"; Image = Img; BackgroundTransparency = 1; ImageTransparency = if R.Lifted then 0.5 else 0;
				Position = UDim2.fromOffset(0, 2); Size = UDim2.fromOffset(28, 28) }, F)
		end
		local Right = if R.CanRemove then 44 else 0
		Text(F, "Head", `{R.Who} · {os.date("%d %b %H:%M", R.At)}`, 20, FACE.Body, COL.Dim,
			UDim2.fromOffset(34, 0), UDim2.new(1, -34 - Right, 0, 24))
		-- the state goes after the text, which wraps: at the end of the head line it was cut off
		local Body2 = Text(F, "Text", (if R.Text ~= "" then R.Text else R.Kind) .. (if R.State then ` ({R.State})` else ""), 20, FACE.Body, if R.Lifted then COL.Dim else COL.Bone,
			UDim2.fromOffset(34, 24), UDim2.new(1, -34 - Right, 0, 0), true)
		Body2.AutomaticSize = Enum.AutomaticSize.Y
		if R.Lifted then Body2.TextTransparency = 0.35 end
		if R.CanRemove then
			local B = New("TextButton", { Name = "Remove"; Text = "✕"; TextSize = 20; FontFace = FACE.Bold; TextColor3 = COL.Bone; BackgroundColor3 = COL.Velvet;
				AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, 0, 0, 4); Size = UDim2.fromOffset(36, 36) }, F)
			New("UICorner", { CornerRadius = UDim.new(0, 8) }, B)
			local Ring = New("ImageLabel", { Name = "HoldRing"; Image = Art.Image("HoldRing") or "rbxassetid://0"; BackgroundTransparency = 1; ImageTransparency = 1;
				AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromOffset(36, 36); ZIndex = 3 }, B)
			Cards.Hold(B, Ring, Ctx.Reduced, function() Ctx.Handlers.Remove(R) end)
		end
	end
end
```

In `context`, replace everything from `if not P then line("Pick a student on the left.", 20, COL.Dim) return end`
to the end of the function with:

```lua
	if not P and not (S.Selected and S.Offline) then line("Pick a student on the left.", 20, COL.Dim) return end
	local function idBox(UserId: number)
		N += 1
		local Id = New("TextBox", { Name = "UserId"; Text = tostring(UserId); TextEditable = false; ClearTextOnFocus = false; TextSize = 20; FontFace = FACE.Body;
			TextColor3 = COL.Dim; BackgroundColor3 = COL.IronHi; Size = UDim2.new(1, -8, 0, 36); LayoutOrder = N }, Body)
		New("UICorner", { CornerRadius = UDim.new(0, 6) }, Id)
	end
	if P then
		line(P.Display or P.Name, 26, COL.Brass, true)
		idBox(P.UserId)
		line(`{P.Sub or P.Race or "?"}{if P.Tier then " · Tier " .. ({ "I", "II", "III" })[P.Tier] else ""}{if P.Height then " · " .. P.Height else ""}`)
		line(`Health {P.Health}/{P.MaxHealth} · {P.Ping} ms · staff level {P.Level}`)
		local Flags = Model.Flags(P)
		if #Flags > 0 then line(table.concat(Flags, "  "), 20, COL.Crimson, true) end
		local I = Ctx.Inspect
		if S.Side == "Test" and I and I.UserId == P.UserId then
			line("Inspector", 22, COL.Brass, true)
			line(`Slot {I.Slot or "?"} · ¥{I.Yen} · Level {I.Level or "?"} ({I.Exp or 0} EXP, {I.Points or 0} points)`)
			line(`Discipline {I.Discipline.Points or 0} ({I.Discipline.Level or "Clear"}), owes {I.Discipline.Owed or 0}`)
			line(`Places {I.Regions}/{I.RegionsTotal} · Club {I.Club ~= "" and I.Club or "none"}`)
			line(`Title {I.Title ~= "" and I.Title or "none"} · {#I.Titles} titles`)
			if #I.Quests > 0 then line("Quests: " .. table.concat(I.Quests, ", ")) end
			if I.Note then line(`Note ({I.Note.By}): {I.Note.Text}`, 20, COL.Dim) end
		end
	else
		local H = Ctx.History
		line(if H and H.Ok and H.Name then H.Name else `UserId {S.Selected}`, 26, COL.Brass, true)
		idBox(S.Selected)
		line("Not in this server", 20, COL.Dim)
	end
	if S.Side == "Moderate" then history(Body, Ctx, function() N += 1 return N end, line) end
end
```

In `View.Redraw`, replace `grid(Dyn, Ctx)` with:

```lua
	if Ctx.S.Side == "Moderate" and Ctx.S.Section == "Log" then logView(Dyn, Ctx) else grid(Dyn, Ctx) end
```

- [ ] **Step 3: The shell**

In `live/...StaffConsole.luau`:

Add to the header comment:

```lua
	1b: the picked student's saved history (History remote, cached 30 s here), the Log section (LogDay), saved
	favourites and side (Prefs on the first open, SavePrefs on every change). Probe adds: Log, OpenRow, History, Fav, Prefs.
```

After `local Busy = false` add:

```lua
local Hist = {} :: { [number]: { At: number, R: any, Loading: boolean? } }
local LogResult = nil :: any
local LogToken = 0
-- commands that change a saved record: the history is fetched again after one runs
local RECORD = { Warn = true, Note = true, Mute = true, Unmute = true, Ban = true, Unban = true, RemoveRecordEntry = true }
-- defined after mustWait (they use it); declared here so run() above them can call them
local fetchHistory, wantHistory, fetchLog, loadPrefs, savePrefs
```

Replace `local function ctx(): any ... end` with:

```lua
local function ctx(): any
	local Sel = S.Selected and Hist[S.Selected]
	return { S = S; Info = Info; Status = Status; Defs = defs(); Values = Values; Lists = Info and Info.Lists; Inspect = Inspect;
		Reduced = Kit.ReducedMotion and Kit.ReducedMotion() or false; Handlers = Shared.Handlers;
		History = Sel and Sel.R; LogResult = LogResult;
		HistoryFor = function(Id: number) local H = Hist[Id] return H and H.R end }
end
```

After `local function mustWait(): boolean ... end`, add:

```lua
function fetchHistory(UserId: number?): any
	local F = remotes()
	if not (F and UserId and F:FindFirstChild("History")) then return nil end
	Hist[UserId] = { At = os.clock(); R = Hist[UserId] and Hist[UserId].R; Loading = true }
	local Ok, R = pcall(F.History.InvokeServer, F.History, UserId)
	local Res = if Ok and typeof(R) == "table" then R else { Ok = false; Error = "History unavailable" }
	Hist[UserId] = { At = os.clock(); R = Res }
	if not mustWait() then Shared.Redraw(true) end
	return Res
end

function wantHistory(UserId: number?, Force: boolean?)
	if not UserId then return end
	local H = Hist[UserId]
	if H and (H.Loading or (not Force and os.clock() - H.At < 30)) then return end
	task.spawn(fetchHistory, UserId)
end

function fetchLog(): any
	local F = remotes()
	if not (F and F:FindFirstChild("LogDay")) then return nil end
	LogToken += 1
	local Mine = LogToken
	local L = S.Log
	local Ok, R = pcall(F.LogDay.InvokeServer, F.LogDay, L.Day, { Query = L.Query; Chip = L.Chip; Page = L.Page })
	if Mine ~= LogToken then return LogResult end -- a newer request won
	LogResult = if Ok and typeof(R) == "table" then R else { Ok = false; Error = "Log unavailable" }
	if LogResult.Ok then L.Page = LogResult.Page end
	if not mustWait() then Shared.Redraw() end
	return LogResult
end

-- saved favourites and side: read on the first open, written on every change (the server saves 5 s after the last)
function loadPrefs()
	if S.PrefsTried then return end
	local F = remotes()
	if not (F and F:FindFirstChild("Prefs")) then return end
	S.PrefsTried = true
	local Ok, R = pcall(F.Prefs.InvokeServer, F.Prefs)
	if Ok and typeof(R) == "table" and R.Ok then
		S.PrefsOk = true
		Model.LoadPrefs(S, R, defs(), (Info and Info.Sections) or SC.SECTIONS)
	else
		Model.Push(S, false, "Saved favourites unavailable: changes this visit won't be kept", "Favourites")
	end
end

-- never over the stored ones when they couldn't be read
function savePrefs()
	local F = remotes()
	if not (F and S.PrefsOk and F:FindFirstChild("SavePrefs")) then return end
	task.spawn(pcall, F.SavePrefs.InvokeServer, F.SavePrefs, table.clone(S.Favs), S.Side)
end
```

In `run`, replace

```lua
	local Ok, Why, Clean = Model.Ready(D, Vals, S.Selected, Info and Info.Lists)
```

with

```lua
	local Ok, Why, Clean = Model.Ready(D, Vals, S.Selected, Info and Info.Lists, S.Offline)
```

and replace its last line `task.spawn(Shared.Refresh)` with:

```lua
	task.spawn(Shared.Refresh)
	if RECORD[D.Id] then
		local Who = if D.Id == "Unban" then tonumber(Vals.UserId) else S.Selected
		if Who then task.spawn(fetchHistory, Who) end
	end
	if S.Side == "Moderate" and S.Section == "Log" then task.spawn(fetchLog) end
```

In `prune`, add as its first line: `if S.Offline then return end -- picked from the Log: never in the player list`.

In `Shared.Refresh`, after `prune(R and R.Players)` add `if (R and R.Level or 0) >= 1 then loadPrefs() end`.

In `bind`'s `ButtonY` branch, replace
`if CardObj then Model.ToggleFav(S, string.sub(CardObj.Name, 6)) Shared.Redraw() end` with
`if CardObj then Model.ToggleFav(S, string.sub(CardObj.Name, 6)) savePrefs() Shared.Redraw() end`.

Replace the `Side`, `Section`, `Pick` and `Fav` handlers with:

```lua
	Side = function(Side: string)
		if not table.find(Model.Sides(S.Level), Side) then return end
		S.Side = Side
		S.Section = ((Info and Info.Sections or SC.SECTIONS)[Side] or {})[1]
		savePrefs()
		Shared.Redraw()
		if Side == "Moderate" then wantHistory(S.Selected) end
	end;
	Section = function(Name: string)
		if not table.find((Info and Info.Sections or SC.SECTIONS)[S.Side] or {}, Name) then return end
		S.Section = Name
		if Name == "Log" then LogResult = nil task.spawn(fetchLog) end
		Shared.Redraw()
	end;
	Pick = function(UserId: number)
		Model.Pick(S, UserId, false) Inspect = nil S.PhoneRail = false Shared.Redraw()
		if S.Side == "Moderate" then wantHistory(UserId, true) end
	end;
```

```lua
	Fav = function(D: any) Model.ToggleFav(S, D.Id) savePrefs() Shared.Redraw() end;
```

and add these handlers to the same table:

```lua
	LogDay = function(Off: number) S.Log.Day = Off S.Log.Page = 1 LogResult = nil Shared.Redraw() task.spawn(fetchLog) end;
	LogQuery = function(Q: string) if Q == S.Log.Query then return end S.Log.Query = Q S.Log.Page = 1 task.spawn(fetchLog) end;
	LogChip = function(C: string) S.Log.Chip = C S.Log.Page = 1 Shared.Redraw() task.spawn(fetchLog) end;
	LogPage = function(Delta: number) S.Log.Page = math.max(1, S.Log.Page + Delta) task.spawn(fetchLog) end;
	OpenLogRow = function(E: any)
		if not E.TargetId then return end
		local Here = false
		for _, P in (Status and Status.Players) or (Info and Info.Players) or {} do if P.UserId == E.TargetId then Here = true end end
		Model.Pick(S, E.TargetId, not Here)
		Inspect = nil
		Shared.Redraw()
		wantHistory(E.TargetId, true)
	end;
	WantHistory = function(Id: number) wantHistory(Id) end;
	Remove = function(Row: any)
		for _, D in defs() do
			if D.Id == "RemoveRecordEntry" then task.spawn(run, D, { List = Row.List; At = Row.At; By = Row.By }) return end
		end
	end;
```

In the probe, before `return nil` at the end of the probe function, add:

```lua
				if Cmd == "Log" then -- A = { Day?, Query?, Chip?, Page? }: open the Log section with these and return what it shows
					if typeof(A) == "table" then
						if A.Day ~= nil then S.Log.Day = A.Day end
						if A.Query ~= nil then S.Log.Query = A.Query end
						if A.Chip ~= nil then S.Log.Chip = A.Chip end
						if A.Page ~= nil then S.Log.Page = A.Page end
					end
					S.Side = "Moderate" S.Section = "Log" -- not through Handlers.Side: a probe never saves prefs
					local R = fetchLog()
					local Rows = {}
					for _, E in (R and R.Rows) or {} do table.insert(Rows, { Text = Model.LogHead(E); Ok = E.Ok; TargetId = E.TargetId; Action = E.Action }) end
					return { Ok = R and R.Ok; Error = R and R.Error; Total = R and R.Total; Page = R and R.Page; Pages = R and R.Pages; Rows = Rows }
				end
				if Cmd == "OpenRow" then
					local E = LogResult and LogResult.Rows and LogResult.Rows[A]
					if E then Shared.Handlers.OpenLogRow(E) end
					return S.Selected
				end
				if Cmd == "History" then
					local Id = tonumber(A) or S.Selected
					if Id and Id ~= S.Selected then Model.Pick(S, Id, Players:GetPlayerByUserId(Id) == nil) end
					local R = fetchHistory(Id)
					Shared.Redraw()
					local Ok2 = R and R.Ok
					return { Ok = Ok2; Error = R and R.Error; Summary = if Ok2 then Model.Summary(R.Record, os.time()) else nil;
						Count = if Ok2 then #Model.Timeline(R.Record, S.Level, os.time()) else 0 }
				end
				if Cmd == "Fav" then Shared.Handlers.Fav({ Id = A }) return table.clone(S.Favs) end
				if Cmd == "Prefs" then return { Favs = table.clone(S.Favs); Side = S.Side; Ok = S.PrefsOk } end
```

- [ ] **Step 4: Update `console_play_client.lua`**

Replace `Eq(#I.Cards, 13, "student cards (12 + Stop spectating)")` with
`Eq(#I.Cards, 14, "student cards (13 + Stop spectating)")`.

Add before the small-text scan:

```lua
-- (1b) the Log section draws (rows may be empty on a fresh day; the chrome is always there)
local L = B:Invoke("Console", "Log", { Day = 0; Query = ""; Chip = "All"; Page = 1 })
Eq(L.Ok, true, "log reads today")
task.wait(0.5)
for _, N in { "LogDays", "Day_0", "Day_6", "LogSearch", "Chip_All", "Chip_Refused", "LogRows", "LogPrev", "LogNext", "LogPage" } do
	if not G:FindFirstChild(N, true) then table.insert(Fails, "Log section: no " .. N) end
end
```

- [ ] **Step 5: Write `records_play_client.lua`**

`tools/admin-console/checks/records_play_client.lua`:

```lua
-- records_play_client.lua: Client, Play (through the NHQuietProbe probe). Run after records_play_a in the same round, or
-- after the restart (Restart = true reads back the saved side and favourite from the real-input step). The Log section
-- (day, search, chips, paging, a row opens its target's history) and the history timeline with its remove buttons.
local Restart = false -- Task 6 sets it to true for the round after the restart
local P = game.Players.LocalPlayer
local B = P.PlayerGui:WaitForChild("NHQuietProbe", 10)
if not B then return "FAIL no probe" end
local Fails = {}
local function Eq(Got, Want, What) if Got ~= Want then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end
Eq(B:Invoke("Console", "Open"), true, "opens")
task.wait(2)
local G = P.PlayerGui:FindFirstChild("NHStaffConsole")
if Restart then
	-- before anything changes the side: what the real-input round saved
	local I = B:Invoke("Console", "Info")
	Eq(I.Side, "Test", "opens on the saved side")
	local Pr = B:Invoke("Console", "Prefs")
	Eq(Pr.Ok, true, "prefs read")
	Eq(table.find(Pr.Favs, "Warn") ~= nil, true, "the saved favourite came back")
end
-- the Log section
local L = B:Invoke("Console", "Log", { Day = 0; Query = ""; Chip = "All"; Page = 1 })
Eq(L.Ok, true, "today's log reads")
if L.Ok then
	if L.Total < 1 then table.insert(Fails, "today's log is empty after records_play_a") end
	if #L.Rows > 50 then table.insert(Fails, "more than 50 rows on a page") end
	if L.Total > 50 then
		local L2 = B:Invoke("Console", "Log", { Page = 2 })
		Eq(L2.Page, 2, "page 2") if L2.Rows[1] and L.Rows[1] and L2.Rows[1].Text == L.Rows[1].Text then table.insert(Fails, "page 2 shows page 1") end
		B:Invoke("Console", "Log", { Page = 1 })
	end
end
local Rf = B:Invoke("Console", "Log", { Chip = "Refused"; Query = ""; Page = 1 })
for _, R in Rf.Rows or {} do if R.Ok then table.insert(Fails, "a run row under Refused: " .. R.Text) end end
local Rm = B:Invoke("Console", "Log", { Chip = "All"; Query = "RemoveRecordEntry"; Page = 1 })
if not (Rm.Ok and Rm.Total >= 1) then table.insert(Fails, "search finds no RemoveRecordEntry row") end
local Yd = B:Invoke("Console", "Log", { Day = 1; Query = ""; Page = 1 })
Eq(Yd.Ok, true, "yesterday reads (empty is fine, unavailable is not)")
B:Invoke("Console", "Log", { Day = 0; Query = "RemoveRecordEntry"; Page = 1 })
-- a row opens its target's history
Eq(B:Invoke("Console", "OpenRow", 1), P.UserId, "the row picked its target")
local H = B:Invoke("Console", "History", P.UserId)
Eq(H.Ok, true, "history reads")
if H.Ok then
	if not string.find(H.Summary or "", "note", 1, true) then table.insert(Fails, "summary has no note: " .. tostring(H.Summary)) end
	if not string.find(H.Summary or "", "muted until", 1, true) then table.insert(Fails, "summary has no open mute: " .. tostring(H.Summary)) end
	if H.Count < 1 then table.insert(Fails, "no timeline entries") end
end
task.wait(0.5)
local E1 = G and G:FindFirstChild("Entry_1", true)
if not E1 then table.insert(Fails, "no timeline entry drawn") elseif not E1:FindFirstChild("Remove") then table.insert(Fails, "no remove button at level 3") end
-- text at 20 px or more
for _, X in G:GetDescendants() do
	if (X:IsA("TextLabel") or X:IsA("TextButton") or X:IsA("TextBox")) and X.Text ~= "" and X.TextSize < 20 then
		table.insert(Fails, "small text " .. X:GetFullName() .. " " .. X.TextSize)
	end
end
if #Fails > 0 then return "FAIL " .. #Fails .. "\n" .. table.concat(Fails, "\n") end
return "PASS records_play_client" .. (if Restart then " (after restart)" else "")
```

- [ ] **Step 6: Install and run a Play round**

```bash
python -X utf8 -I tools/admin-console/install_inplace.py tools/admin-console/pre1b tools/admin-console/live AdminConsole1b_20261123 StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.Cards StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole.View StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole
cp tools/admin-console/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.StaffConsole*.luau tools/admin-console/pre1b/
```

Then the round:
1. `start_stop_play` start; `round_start.sh`; record `cine.lua`.
2. `run_live.py checks/records_play_a.lua 240` → PASS.
3. `run_check.py Client checks/console_play_client.lua` → `PASS console_play_client`.
4. `run_check.py Client checks/records_play_client.lua` → `PASS records_play_client`.
5. `run_live.py checks/records_cleanup.lua 240` → PASS.
6. `restore.py`, record `cine.lua`, stop.

Fix and repeat until all pass. Add the PASS lines to `REPORT.md`.

- [ ] **Step 7: Commit (on the owner's word)**

```bash
git add tools/admin-console/live tools/admin-console/pre1b tools/admin-console/checks tools/admin-console/REPORT.md
git commit -m "Console 1b: history timeline, Log section, Mute length, Unban preview, saved favourites and side"
```

---

### Task 6: The restart round, real input and screenshots

**Files:**
- Create: `tools/admin-console/checks/records_play_b.lua`
- Modify: `tools/admin-console/REPORT.md`
- Create: `docs/superpowers/mockups/2026-11-23-admin-console/play-1b-log.png`, `play-1b-timeline.png`

**Interfaces:**
- Consumes: `records_play_a.lua` (it leaves the open "1b restart" mute and the marker), `records_play_client.lua` with
  `Restart = true`, `records_cleanup.lua`.

- [ ] **Step 1: Write `records_play_b.lua`**

```lua
-- records_play_b.lua: Server, Play, after stopping Play and starting it again (1b spec §6 "Across a restart"). The
-- open mute from records_play_a was applied again on join; the record and today's log read back the same. It changes
-- nothing: records_cleanup.lua runs after it.
local Players = game:GetService("Players")
local DataStoreService = game:GetService("DataStoreService")
local RunService = game:GetService("RunService")
local SSS = game.ServerScriptService.Services
local Admin = require(SSS.Features.Admin)
local SR = require(SSS.Features.StaffRecords)
local P = Players:GetPlayers()[1]
if not P then return "FAIL no player" end
if not RunService:IsStudio() or SR.PREFIX ~= "[Test] " then return "FAIL not on the [Test] stores" end
local Me = P.UserId
local Marker = DataStoreService:GetDataStore("[Test] NHStaffPrefs_v1"):GetAsync("check1b_" .. Me)
if typeof(Marker) ~= "table" then return "FAIL no marker from records_play_a" end
local T0 = Marker.T0
local Fails = {}
-- the open mute, applied on join (Admin reads the record in PlayerAdded)
local t = os.clock()
while Admin.MutedUntil(Me) == nil and os.clock() - t < 15 do task.wait(0.5) end
local U = Admin.MutedUntil(Me)
if not (U and U > os.time()) then table.insert(Fails, `the open mute wasn't applied on join: {tostring(U)}`) end
-- the record reads back
local Rec, Err = SR.Get(Me, true)
if not Rec then return "FAIL record read: " .. tostring(Err) end
local function has(List, Pred) for _, E in Rec[List] do if E.By == Me and E.At >= T0 and Pred(E) then return true end end return false end
if not has("Notes", function(E) return E.Text == "1b test note" end) then table.insert(Fails, "the note is gone after the restart") end
if not has("Mutes", function(E) return E.Reason == "1b restart" and E.Lifted == nil end) then table.insert(Fails, "the open mute is gone from the record") end
if not has("Bans", function(E) return E.Days == 0 and E.Lifted ~= nil end) then table.insert(Fails, "the lifted permanent ban is gone") end
if has("Warnings", function(E) return E.Reason == "1b test warn" end) then table.insert(Fails, "the removed warning came back") end
-- today's log from the store (saved by records_play_a's flush and the first session's BindToClose)
local Day = SR.LogDay(0, { Query = "RemoveRecordEntry" })
local Found = false
for _, E in Day and Day.Rows or {} do
	if E.At >= T0 and E.StaffId == Me and E.Ok and string.find(E.Detail, "1b test warn", 1, true) then Found = true end
end
if not Found then table.insert(Fails, "the removal row isn't in today's log after the restart") end
if #Fails > 0 then return "FAIL " .. #Fails .. "\n" .. table.concat(Fails, "\n") end
return "PASS records_play_b"
```

- [ ] **Step 2: First session**

1. `start_stop_play` start; `round_start.sh`; record `cine.lua`.
2. `run_live.py checks/console_play_run.lua 300` → PASS (it also puts today's log over 50 rows, for paging).
3. `run_live.py checks/records_play_a.lua 240` → PASS.
4. **Real input: a favourite and the side.**
   - `user_keyboard_input` keyPress `F3`: the console opens.
   - Right-click `LocalPlayer.PlayerGui.NHStaffConsole.Board.Dyn.Cards.Card_Warn` with `user_mouse_input`
     (`moveTo` the `instance_path`, then the right button down and up). If the tool has no right button, use the probe
     `Fav` with `"Warn"` and write in `REPORT.md` that the favourite went through the probe.
   - Click `...Dyn.Side_Test.Hit` with `user_mouse_input` (`moveTo`, `mouseButtonDown`, `mouseButtonUp`).
   - Wait 7 s (the 5 s save delay and the 1 s loop).
5. **Real input: the Log section** (Moderate side, Log tab `...Dyn.Section_Log.Hit`):
   - click `Day_1` then `Day_0`;
   - click `LogSearch`, type `Warn`, press Return;
   - click `Chip_Refused`, then `Chip_All`;
   - clear the search; if `LogNext` is active, click it and check `LogPage` says "Page 2 of ...".
   - After each step, read `Board.Dyn.LogPage.Text` (`inspect_instance`) and write what it said in `REPORT.md`.
6. **Screenshot of the Log section:** `python -X utf8 -I tools/admin-console/shot.py docs/superpowers/mockups/2026-11-23-admin-console/play-1b-log.png`.
7. `start_stop_play` stop. (The first session's `BindToClose` saves the log buffer and any prefs.)

- [ ] **Step 3: Second session (across the restart)**

1. `start_stop_play` start; `round_start.sh` (a fresh snapshot for this round); record `cine.lua`.
2. Set `local Restart = true` in a copy of `records_play_client.lua` written to the scratchpad, and run that copy:
   `run_check.py Client <scratchpad>/records_play_client_restart.lua` → `PASS records_play_client (after restart)`.
3. `run_live.py checks/records_play_b.lua 120` → `PASS records_play_b`.
4. **Real input: the timeline's remove hold.**
   - On the Moderate side, Student section, pick yourself (`...Dyn.Row_<UserId>.Hit`). The timeline shows the 1b entries.
   - Hold `...Context.Body.Entry_1.Remove` for 300 ms (`mouseButtonDown`, wait, `mouseButtonUp`). Expected: the probe's
     `History` count is unchanged (cancelled).
   - Hold it again for 1100 ms. Expected: the feed's first line starts with "Removed from", and the `History` count is
     one less.
5. **Screenshot of the timeline:** `shot.py docs/superpowers/mockups/2026-11-23-admin-console/play-1b-timeline.png`.
6. `run_live.py checks/records_cleanup.lua 240` → `PASS records_cleanup (removed N)`.
7. `restore.py`, record `cine.lua`, `start_stop_play` stop.

- [ ] **Step 4: Fix what failed and repeat Steps 2-3 until every check passes**

If a round stops halfway, run `records_cleanup.lua` in a fresh Play session before starting again, so the next round
starts with no leftover 1b entries.

- [ ] **Step 5: Report**

Add to `REPORT.md`'s "Phase 1b":
- every PASS line (both sessions) and the call counts;
- the real-input results (Log steps with the `LogPage` text, the hold cancel and the hold run, favourite and side);
- whether the favourite went through the mouse or the probe;
- CineState, Seen and Origin before and after each session;
- the two screenshots.

- [ ] **Step 6: Commit (on the owner's word)**

```bash
git add tools/admin-console/checks/records_play_b.lua tools/admin-console/REPORT.md docs/superpowers/mockups/2026-11-23-admin-console/play-1b-*.png
git commit -m "Console 1b: restart round (records, log, prefs and the open mute survive), real input, screenshots"
```

---

### Task 7: Docs, final regression and the spec status

**Files:**
- Modify: `docs/Admin-Panel.md`, `CHANGELOG.md`
- Modify: `docs/superpowers/specs/2026-11-23-admin-console-1b-design.md` (the status line only)
- Modify: `tools/admin-console/REPORT.md`

- [ ] **Step 1: Final Edit regression**

```bash
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/records_rules.lua
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/records_store.lua
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_pure.lua
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_registry.lua
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_model.lua
python -X utf8 -I tools/admin-console/run_check.py Edit tools/admin-console/checks/console_play_server.lua
```
Expected: all six PASS (`console_registry (67 commands)`).

Also check that Studio matches every mirror: run `install_inplace.py tools/admin-console/live tools/admin-console/live
AdminConsole1b_verify <every changed Dotted.Path>`. It refuses if any live Source differs from `live/`. Only a
"no change" result counts as a match: if it reports writes, Studio had drifted, so record that in `REPORT.md`.

- [ ] **Step 2: `docs/Admin-Panel.md`**

Add a section "Saved records, the Log and saved favourites (1b, 2026-11-23)" after the console description:
- **What is saved, and where:** `NHStaffRecords_v1` (notes, warnings, bans, mutes; 50 each), `NHStaffLog_v1` (every
  console action, kept by day and server; Test actions 7 days), `NHStaffPrefs_v1` (favourites, last side). Studio uses
  `[Test] ` stores.
- **Mute lengths:** 10 min, 1 h, 1 day, Until unmuted. A mute holds across rejoins and ends on time.
- **Who may lift a ban:** permanent (or set before 1b) the owner; over 30 days an admin; 30 days or less a moderator.
- **History timeline:** the right-hand panel on the Moderate side. Greyed rows were lifted or ended. The owner's ✕
  (hold 0.8 s) removes an entry, which is logged; removing a ban or mute entry doesn't lift it.
- **The Log section:** a day picker for this week, search (staff, student, UserId, action), the chips All / Moderate /
  Test / Refused, and 50 rows a page. Clicking a row opens that student's history, even if they're offline.
- **Limits:** a crash can lose up to 30 s of the log. A mute or ban set in one server reaches a player in another only
  when they next join (phase 3 adds live delivery). "Not staff" and "Slow down" refusals aren't logged.
- The spec deltas (copy the list from this plan).

Update the "1b and later" line so it lists only the phase 2-3 items.

- [ ] **Step 3: `CHANGELOG.md`**

Add a section at the top, in the file's existing format, with these bullets:
- Staff console 1b: saved player records (warnings, notes, bans, mutes) with a history timeline;
- mute lengths, held across rejoins;
- owner-only lifting of permanent bans; owner-only, logged removal of history entries;
- the saved staff log with a Log section (day, search, chips, pages);
- saved favourites and last side;
- "Not saved: the place needs the owner's word to save."

- [ ] **Step 4: Spec status, graph**

In the 1b spec, change the status line to
`Status: approved by the owner (2026-11-23); implemented on branch admin-console-1b (plan docs/superpowers/plans/2026-11-23-admin-console-1b.md).`

Run `graphify update .` if `graphify` is installed. Otherwise, write in `REPORT.md` that it wasn't run.

- [ ] **Step 5: Commit (on the owner's word)**

```bash
git add docs/Admin-Panel.md CHANGELOG.md docs/superpowers/specs/2026-11-23-admin-console-1b-design.md tools/admin-console/REPORT.md
git commit -m "Console 1b: docs, changelog, spec status"
```

Then the owner chooses: merge `admin-console-1b` into `main`, or open a PR (superpowers:finishing-a-development-branch).

---

## Self-review notes (2026-11-23)

- **Spec coverage, 1b:**

| Requirement | Where |
|---|---|
| §1 owner decisions | Global Constraints; Task 1 `UnbanLevel`, `MUTE_CHOICES`; Task 3 Meta (Level 3, Danger) |
| §2 store names and `[Test] ` prefix | Task 2 `PREFIX`, `store()`; Play checks refuse without it |
| §2 record shape, 50 cap | Task 1 `Normalize`, `Push`; checks `records_rules` and `records_store` §5 |
| §2 writes: 3 tries, pending, 30 s retry, "Saved" / "Saved later" | Task 2 `Write`, `RetryPending`, `Status`, `OnStart`; Task 3 `saved()` |
| §2 reads: cached 60 s, "History unavailable" | Task 2 `Get`; Task 3 `History` remote; Task 5 `history()` |
| §2 mutes on join, lifted on time, Unmute writes Lifted | Task 3 `loadRecord`, the 1 s loop, `C.Unmute`; `records_play_b` |
| §2 bans and unbans (rule, Lifted, API) | Task 3 `C.Ban`, `C.Unban`; `records_play_a` |
| §2 Remove history entry (level 3, Danger, logged, doesn't lift) | Task 3 Meta and `C.RemoveRecordEntry`; `records_play_a` |
| §2 no targeting up on every record command and on history | Task 3 `dispatch()` (`user`), `C.Unban`, `History` remote, `LevelOf` |
| §3 every Dispatch call buffered; Detail 120 | Task 3 `Shared.Dispatch`; Task 1 `LogEntry` |
| §3 saving every 30 s and on close; day keys, index, 2000 cap, Studio key | Task 2 `FlushLog`, `OnStart`; `records_store` §7-§9 |
| §3 Test keys and the 7-day clean-up | Task 2 `sweepTest`; `records_store` §11 |
| §3 reading one day, merged newest first, cached, "Log unavailable" | Task 2 `readDay`, `LogDay`; `records_store` §7, §10 |
| §4 prefs (read on first open, 5 s, on leave, unknown ids dropped, saved side) | Task 2 prefs; Task 4 `LoadPrefs`; Task 5 `loadPrefs`/`savePrefs`; Task 6 restart |
| §5 timeline, summary, greyed, remove with hold | Task 4 `Timeline`, `Summary`; Task 5 `history()` |
| §5 row flags from the saved record | Task 3 `playerList` (`hasNote`, `Muted`) |
| §5 Log section (day, search, chips, rows, 50 a page, open row, 20 px) | Task 5 `logView`, handlers; `records_play_client`; Task 6 real input |
| §5 Mute Length, Unban preview, Remove history entry card | Task 3 Meta; Task 5 Cards `Labels`, `Note` |
| §5 new remotes with level checks | Task 3 Step 8 |
| §6 pure checks | `records_rules`, `records_store`, `console_model` |
| §6 Play checks, restart, real input, screenshots, clean-up | Tasks 3, 5, 6 (`records_play_a`, `_b`, `_client`, `_cleanup`, `console_play_run`) |
| §7 out of scope | Global Constraints |

- **Counts to recheck while executing:** registry 67 at level 3, 65 at level 2, 16 at level 1; Student cards in the
  client 14 (13 server + Stop spectating).
- **Names used across tasks:** `Records` (Admin's local for `Functions.StaffRecords`), `StaffRecords` (Admin's
  local for `Features.StaffRecords`), `SR` (the checks' local for the service), `Rules` (the service's local for the
  pure module). `Shared.LevelOf`, `Shared.MutedUntil` and `Shared.TestSkipBanApi` are on `Features.Admin`.
