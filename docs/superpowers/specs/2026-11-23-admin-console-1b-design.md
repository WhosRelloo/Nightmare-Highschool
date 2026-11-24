# The Staff Console, phase 1b: saved records, the Log, saved favourites (design)

Status: design approved in chat by the owner (2026-11-23); implemented on branch admin-console-1b (plan docs/superpowers/plans/2026-11-23-admin-console-1b.md); the plan's decisions are waiting for the owner's review.
Parent spec: `docs/superpowers/specs/2026-11-23-admin-console-design.md` (§2b picks 1, 4 and 6; §5; §7 "Saved records";
§8 phase 1b; §10). This file narrows and settles that spec for 1b. Where they differ, this file wins for 1b.
Builds on: branch `admin-console-polish` (1a plus the polish round).

## 1. Owner decisions (2026-11-23)

| Question | Decision |
|---|---|
| Mute lengths | **10 min, 1 h, 1 day, Until unmuted** (a choice on the Mute card) |
| Lifting a permanent ban | **Owner only** (level 3). Temporary bans (30 days or less) can be lifted from level 1 |
| Removing history entries | **Owner only, and logged.** Every removal is written to the staff log |
| The saved log | **Buffered per server**, saved in batches (§3), not one write per action |

## 2. Saved records (`ServerScriptService.Services.Features.StaffRecords`, new)

- **Store names.** In Studio every store gets the prefix `[Test] ` (the pattern `Player.Data` and `Social.Superlatives`
  use), so Studio never touches live records.
- **`NHStaffRecords_v1`**, key `u_<UserId>`:
  `{ Notes = { {By, At, Text} }, Warnings = { {By, At, Reason} }, Bans = { {By, At, Days, Reason, Lifted?} },
  Mutes = { {By, At, Until, Reason?, Lifted?} }, Reports = {} }`. `By` is the staff UserId, and `At` and `Until` are
  `os.time()`. `Until = 0` means until unmuted. `Days = 0` means permanent. `Reports` is kept empty for phase 3. Each
  list is capped at 50 entries, and the oldest entry is dropped first.
- **Writes** happen straight away (UpdateAsync, 3 tries with backoff) on Warn, Note, Ban, Unban, Mute, Unmute and Remove
  history entry. A failed write stays in a per-player pending list in memory and is retried on the next write for that
  player and every 30 s. The results feed says "Saved" or "Saved later (DataStore busy)".
- **Reads** happen when a staff member picks a player, online or offline (by UserId), and are cached on the server for
  60 s. A write updates the cache. A failed read returns an error, and the console shows "History unavailable", never an
  empty history.
- **Mutes on join.** When a player joins, the server reads their record. If a mute has not been lifted and has not ended
  (`Until == 0` or `Until > os.time()`), it is applied again through the same TextChatService gate as today, and
  lifted on time while they are in the server. Unmute writes `Lifted` on the open mute.
- **Bans and unbans.** Ban writes the ban (with Days) to the record, as well as calling the Roblox Ban API as today.
  Unban finds the latest ban without `Lifted`:
  - `Days = 0` (permanent): level 3 only. Lower levels get "Permanent bans can only be lifted by the owner".
  - `Days` from 1 to 30: level 1 and up.
  - No ban on record (bans set before 1b): treated as permanent, so level 3 only.
  - It writes `Lifted = { By, At }` and calls the Unban API as today.
- **Remove history entry** (new command `RemoveRecordEntry`, level 3, Danger). The args are the list (Notes, Warnings,
  Bans or Mutes) and the entry's `At` plus `By` (its identity). It removes that entry and logs the removal with the
  entry's text. Removing a ban or mute entry does not lift it: Unban and Unmute stay the only way to do that.
- **No targeting up** (`StaffConsole.CanTarget`) applies to every record command, and to reading the history of
  someone of a higher level.

## 3. The saved log (`NHStaffLog_v1`)

- Every `Admin.Dispatch` call (run or refused) adds `{ At, Staff, Action, Target?, Detail, Side, Ok }` to the server's
  buffer. `Detail` is the result message, cut to 120 characters. The 1a in-memory log stays as it is.
- **Saving.** Every 30 s, and in `game:BindToClose`, the buffer is appended to the key `day_<n>_<JobId>` (`n` =
  `os.time() // 86400`). When a server writes a day for the first time, it adds its JobId to the index key `day_<n>`
  (UpdateAsync, a set). Each key holds at most 2000 entries, and the oldest are dropped. In Studio the JobId is empty, so
  the key is `day_<n>_studio`.
- **Test actions** (`Side = "Test"`) go to the separate keys `test_day_<n>_<JobId>` and the index `test_day_<n>`. When a
  server first writes on day `n`, it reads `test_day_<n-7>` and removes those keys and the index (best effort, and
  logged to output if it fails). So Test actions are not kept past 7 days.
- **Reading.** The console asks for one day at a time (today and the 6 days before). The server reads that day's index,
  then each JobId key (Moderate and Test together), merges them newest first, and caches the merged day for 60 s. A day
  that fails to read returns an error: "Log unavailable", not an empty day.
- A crash can lose up to the last 30 s of the log. The player records in §2 do not wait for this save.

## 4. Saved favourites and last side (`NHStaffPrefs_v1`)

- Key `u_<UserId>`: `{ Favs = { Id... }, Side = "Moderate"|"Test" }`.
- Read when a staff member first opens the console in a server. Written 5 s after the last change, and when they leave.
  Ids that are no longer in the registry are dropped when they are read.
- The console opens on the saved side (if their level allows it). Favourites work as in 1a, but they persist.

## 5. The console

- **History timeline** (right-hand side, Moderate side, with a student picked): newest first, with one icon per kind
  (Warn, Note, Ban, Mute) and who, when and the text. Lifted bans and mutes are greyed out. At level 3 each entry has a
  remove button with the 0.8 s hold. Above the timeline is a summary line, for example
  "3 warnings · 1 ban (lifted) · muted until 14:20".
- **Row flags.** NOTE and MUTED come from the saved record (they are still there after a rejoin).
- **Log section** (Moderate side, icon `SecLog`, level 1):
  - a day picker (Today and the 6 days before);
  - a search box (staff name, target name or UserId, action);
  - the chips All, Moderate, Test, Refused;
  - rows of time · staff · action · target · detail, 50 per page with Prev and Next.
  Opening a row picks its target and shows that target's history, even if they're offline. Text stays at 20 px or more.
- **Cards.**
  - Mute gets a `Length` choice (10 min, 1 h, 1 day, Until unmuted).
  - Unban shows the ban it would lift (its length and who set it) before it runs.
  - New card Remove history entry (Moderate, Student, level 3, Danger). The timeline's remove button is its shortcut.
- **New remotes** (in `ReplicatedStorage.NHAdmin`, each checking the level on the server):
  - `History(UserId)` (level 1, with no targeting up);
  - `LogDay(DayOffset, Filter?)` (level 1);
  - `Prefs()` and `SavePrefs(Favs, Side)` (level 1).
  Everything else goes through `Run` and `Dispatch` as in 1a.

## 6. Testing

- **Pure (Edit VM):**
  - the record shape and the 50 cap;
  - the unban rule (permanent needs 3, temporary needs 1, a ban with no record counts as permanent);
  - a mute's end time (10 min, 1 h, 1 day, until unmuted) and whether it is still on;
  - the Test-key cutoff (day n-7) and the log entry shape;
  - the cap of 2000 per key;
  - prefs drop unknown ids.
- **Play (slot 2, fresh snapshot, restore and cine before and after, `[Test] ` stores only):**
  - Warn, Note, Mute (each length) and Ban (Studio uses the kick fallback) are written through the real Dispatch and
    read back.
  - Unban: refused at level 1 for a permanent ban, passes at level 3, and passes at level 1 for a 7-day ban.
  - Remove history entry: refused at level 2, passes at level 3, and is logged.
  - The log is saved and then read back.
  - **Across a restart:** stop Play and start a second Play session. Records, the log day and prefs (favourites and side)
    read back the same, and an open mute is applied again on join.
- **Real input:** the Log section (day picker, search, chips, paging), the timeline's remove hold, and a favourite and
  the side surviving a restart. Screenshots of the Log section and the timeline.
- **Test data clean-up:** the Play check removes its own `[Test] ` record entries at the end (as the owner, using the
  new command), so repeated runs don't fill the test stores.

## 7. Out of scope for 1b

Reports, the Inbox and auto-flags (phase 3); cross-server delivery through MessagingService (phase 3: a mute or ban set
in one server reaches a player in another only when they next join); health graphs (phase 3); new Test tools (phase 2).
