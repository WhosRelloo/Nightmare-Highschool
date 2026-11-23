# Attendance and Discipline: NH Combat Test

**Status:** attendance, the discipline ladder, witnesses, the hall monitor, and detention are built and verified in Studio playtests (single player). The discipline section is at the bottom of this doc.

## Classrooms (temporary)

`workspace.School` is placeholder geometry on the baseplate, flagged with the attribute `Temporary = true`. It contains:

- a hallway
- five rooms: R101–R105
- in each room: walls with a doorway, desks, and a sign
- an invisible `Door` marker, which the waypoint points at
- an invisible `Zone` box with a `RoomId` attribute, which attendance checks

The real school map only needs the same thing: a `Zone` part with `RoomId` in each classroom, plus a `Door` part for the waypoint.

| Period (from `Config.SchoolSchedule`) | Subject | Room |
|---|---|---|
| Homeroom 8:00–8:20 | Homeroom | R101 |
| Period 1 8:20–9:00 | Mathematics | R102 |
| Period 2 9:05–9:45 | Chemistry | R103 |
| Period 3 10:00–10:40 | English | R104 |
| Period 4 10:45–11:25 | History | R105 |

The subjects are placeholders, since the concept doc names none. They're set in `Config.Classes.Periods`. Every student has the same timetable for now.

## Rules (`Config.Classes.Attendance`, in-game minutes)

| Result | When | Reward | Streak |
|---|---|---|---|
| **Present** | arrived within 3 min of the bell and stayed | +5 Yen | +1 |
| **Tardy** | arrived later, but before half the period had passed, and stayed | +2 Yen | kept |
| **Left Early** | arrived, but spent less than 60% of the remaining time in the room | — | reset |
| **Absent** | never arrived, or arrived after half the period | — | reset |
| **Excused** | joined the game mid-class with under 10 min left | — | kept |

At the default speed, 1 in-game minute is 5 real seconds. So the grace period is 15 s, and a class lasts about 3 min 20 s.

## How it works

`Services.School.Attendance` runs on the server every second during a `Class` period:

1. **Room check.** It checks whether each player's root part is inside the period's room `Zone`. This is a server-side box test, not Touched events.
2. **Tracking.** It keeps an `InProgress` record in the player's saved data: arrival time, minutes in the room, and when they joined.
3. **Finalizing.** When the period ends, it computes the result and then:
   - saves it (totals, streak, the last 20 records)
   - pays the reward
   - sends a notification
   - fires `Attendance.Recorded(Player, Record)`

**Edge cases and anti-exploit:**

- **Global clock.** All servers share one in-game time, counted from `GlobalEpoch` in `Config.SchoolSchedule` (`ClockMode = "Global"`, as the concept doc specifies). A player who rejoins any server lands in the same period.
- **Leaving mid-class.** The unfinished record is saved, then finalized the next time the player is seen. Quitting can't erase a skip. A toast tells them the result when they come back.
- **Duplicates.** A period that's already recorded (it's the last record or in the recent list) is never recorded or paid again.
- **Clock jumps.** Presence only builds up from real elapsed time, so an admin moving the clock can't fill the presence meter.
- **Dead or missing character** counts as not in the room.

**For the client:**

- player attributes `ClassRoom` and `ClassInRoom`
- `Gui.ClockHud` shows a class line: "Mathematics · Room 102 · In class", "· NOT IN CLASS" in red, or "Next: … at 8:20 AM"
- a marker over the room door (`ClassWaypoint`) with the distance in studs. It appears 15 in-game minutes before class, and during class while you're not in the room.

## Notifications (shared foundation)

On the server, `Services.Features.Notifications.Notify(Player, {Title, Text, Kind, Duration})` sends a message.

- **Kinds:** Info, Good, Warning, Bad
- **Display:** toasts appear top-center, up to 4 at a time (`Controllers.Gui.Notifications`)
- **Network:** they go over the reliable packet `Packets.Notify`
- **Joining players:** messages are held for 6 s after a player joins, so their UI has loaded

## Verified (Studio, single player, clock sped up to 0.5 s per in-game minute)

One scripted morning run produced every outcome correctly:

| Period | What the test did | Result |
|---|---|---|
| Homeroom | joined at 8:15 | **Excused** |
| Math | in the room from 8:16 | **Present**, arrived 8:21, 38 min, +5 Yen |
| Chemistry | entered at 9:12 | **Tardy**, arrived 9:13, +2 Yen |
| English | left at 10:10 | **Left Early**, 8 min in the room |
| History | never entered | **Absent** |

Totals were 1 of each, the streak reset, the best streak is 1, and Yen went 0 → 7.

Other checks:

- **HUD:** it showed In class / NOT IN CLASS / Next correctly at each step. The door marker was enabled on R104 with the distance.
- **Duplicate:** replaying an already-recorded Period 1 in the room added no record and no Yen.
- **Persistence:** records survived a play-session restart.
- **Rejoin:** quitting mid-Math (10 min in) and rejoining finalized it as **Left Early**, and the "Period 1: Mathematics · Left early" toast appeared after joining (screenshot).

**Not tested:**

- two players at once
- a real second server, for the global clock across servers
- mobile layout of the HUD

**Note:** the test runs wrote attendance records and 7 Yen into the developer's **Studio** test profile (`[Test] Studio's Data |1S|`). This is not production data.

---

# Discipline

## Ladder (`Config.Discipline`)

| Level | Points | Effect |
|---|---|---|
| Clear | 0+ | — |
| Warning | 2+ | Shown on the HUD |
| Detention | 5+ | Reaching it from below **owes 1 detention** |
| Probation | 10+ | Lasts **2 in-game days** once reached. No privileges are restricted yet; the hook is the `DisciplineLevel` attribute. |
| Suspension | 16+ | Lasts **1 in-game day**. Classes aren't expected: attendance skips you, and a half-tracked class is dropped instead of counted Absent. The hall monitor ignores you. When it ends, points drop to 8 and Probation starts. |

**Violations and points:**

| Violation | Points |
|---|---|
| Tardy | 1 |
| Left Early | 2 |
| Absent | 3 |
| Truancy (caught by a hall monitor) | 2 |
| Fighting | 4 |
| Skipped Detention | 4 |

**Recovery:**

- −1 per **Present** class
- −2 per in-game day (offline days count too)
- −4 per **served detention**

Nothing is permanent.

**Saved data:** `PlayerData.Discipline` holds the points, level, detentions owed and served, probation and suspension end days, last decay day, and the 20 most recent violations.

**For the client:** player attributes `DisciplineLevel`, `DisciplinePoints`, `DetentionsOwed`, and `Suspended`. Every change sends a toast.

**Service:** `Services.School.Discipline`.

- **API:**
  - `AddViolation`
  - `Reduce`
  - `ServeDetention`
  - `ReportIncident`
  - `GetData`
  - `IsSuspended`
- **Signals:** `ViolationAdded`, `LevelChanged`, `DetentionServed`
- **Attendance feed:** results come in as violations with the witness set to "Teacher".

## Witnesses

Systems report what they see with `Discipline.ReportIncident({Type, Suspect, Witness, Position, Recognized})`. Every incident is logged (the 50 most recent, server-side).

**Only a recognized suspect is punished.** If you escape before being recognized, the incident is logged with `Recognized = false` and can't be pinned on you later.

## Hall monitor (`Services.School.HallMonitor`, tuning in `Config.Discipline.HallMonitor`)

**Body:** an NPC built from the existing AI rig, with a "Hall Monitor" name tag and speech bubbles. It spawns at `workspace.School.MonitorSpawn`.

**When it works:** Before School through After School, patrolling `workspace.School.PatrolRoute`. Off duty, it waits at the spawn.

**Truancy (class periods only):**

- It notices a student who is not in their classroom when the student is:
  - within 45 studs
  - inside its 140° field of view
  - not hidden behind a wall
- It chases at speed 15, which is slower than sprinting, so escaping is possible.
- **Catch** (within 6 studs): "Get to class!" and a Truancy violation. A student can only be caught once per period.
- **Escape:** the chase ends after 15 s, after 3 s out of sight, or after 70 studs. The incident is logged as unrecognized and the student gets a toast: "You slipped away from the hall monitor."
- **Walking into class mid-chase:** it lets you go ("That's more like it.").

**Fighting (any time it is on duty):**

- Any combat hit by a student that it can see counts. It doesn't need you in its field of view, since fights are noisy.
- Within 25 studs: recognized, and a Fighting violation right away.
- Farther away: it investigates (chases), and a catch counts.
- Reports are limited to one per attacker every 10 s.
- **Combat-allowed areas:** parts tagged `CombatAllowed` (CollectionService) mark places where fighting is fine, such as a future gym ring.

**Never stuck:** with no progress it jumps; after 8 s it skips the waypoint; after 16 s it teleports to the waypoint.

**Downed or killed:** it can be downed and gripped like any NPC. It stops working while downed and respawns 20 s after dying.

## Detention (`Services.School.Detention`, room `workspace.School.R106`)

1. **Start:** if you owe a detention, walking into Room 106 outside class time starts a session. Five pieces of trash spawn for you.
2. **Collect:** hold **E** on each piece. Only your own pieces work, and the server checks range.
3. **Finish:** hold **E** on the bin. You get `ServeDetention`: owed −1 and points −4.

**Rules:**

- **Walking out:** leaving the room for more than 20 s is a Skipped Detention violation, and the detention is still owed.
- **Class bell:** the session pauses with no penalty. Go to class, then come back.
- **Disconnect:** the session just ends and the detention stays owed. **Nothing locks the player in.**
- **Story hook:** `Detention.Completed(Player)`, for story clues later.

**Interaction key: E** (chosen by the developer). It's set in `ReplicatedStorage.Config.Interaction` (`PromptKey = E`, `GamepadKey = ButtonX`), and every prompt should use that config.

E is also Equip, so it's context-sensitive. While any prompt is showing, E interacts and does **not** toggle the weapon (`InputController.General.Equip` tracks shown prompts). Otherwise E equips as before.

Verified with real presses:

- E next to trash picked it up (1/5) and equip stayed false.
- E away from any prompt toggled equip from false to true.

**HUD (2.36):** the conduct row under the clock: a wax seal tinted by level with "Warning · 3 pts", and a detention slip ("Detention owed · Room 106, outside class", or "Trash 2/5" during a session). The Room 106 marker still shows outside class time. The seal and slip are Bell Tower art (`Config.BellTowerArt`), with kit fallbacks; see [UI Kit](UI-Kit.md#the-bell-tower-cluster-236).

## Verified (Studio, single player)

- **Ladder:**
  - Tardy → 1 Clear
  - +Left Early → 3 Warning
  - +Absent → 6 Detention, 1 owed
  - +Absent → 9
  - +Truancy → 11 Probation until day +2
  - +Fighting → 15
  - +Fighting → 19 Suspension (flag on)
  - next day → 8 Probation, suspension over
  - +2 days → 4 Warning
  - +3 days → 0 Clear
- **Hall monitor, truancy:**
  - spotted at 25 studs during Period 1, caught in 2 s, Truancy +2 (witness: Hall Monitor)
  - **escape:** gave up after 3.2 s, incident `recognized=false`, no points
  - **walking into English mid-chase:** let go, no incident
- **Hall monitor, fights:**
  - hit an NPC 12 studs from the monitor: Fighting +4 immediately
  - hit from 35 studs: the monitor investigated, caught me in 2 s, Fighting +4
- **Detention, with real G-key presses:** session started on entry with the toast and HUD "trash 0/5"; 5/5 pieces collected; bin → owed 1→0, served 1, points 6→2, Detention → Warning. (Prompts only appear when their spot is on screen, which is normal Roblox behavior.)
- **Walking out:** after 22 s outside, Skipped Detention +4, which re-entered Detention level and owed another detention.
- **Class bell:** paused with no penalty.
- **Errors:** no script errors.

**Not tested:**

- two players, such as the monitor choosing between students, or one student escaping while another is caught
- how the monitor moves through crowded halls or real map geometry. The temp hallway is a straight line, and it doesn't path-find around obstacles.
- mobile prompts and HUD

## Next

1. **Class activities** (Milestone 5): at least two real activities, such as a math timed quiz and a chemistry ingredient match. Results feed attendance and rewards.
2. **Probation restrictions and suspension gameplay**, such as off-campus tasks to get reinstated. The current hooks are only the level and the `Suspended` attribute.
3. **More witnesses:** teachers in classrooms reporting fights, using the same `ReportIncident`.

## Detention animation (1.8.9)
Players no longer play the prisoner idle while standing in detention (owner request, 2026-11-02). The ambient detention kid in Room 106 still uses it.

## Report cards (1.40)

Every class that's recorded (`Local.Finalize`) and every violation also goes to the week's report card (`School.ReportCards.Class` / `Violation` / `Detention`); see [Phone](Phone.md#report-cards-and-the-app-icons-140).

## Delinquent audit fixes (2.7.3)

See [Delinquent-System-Audit](Delinquent-System-Audit.md) for the whole audit.

- **The menu doesn't count.** Attendance skips a student whose `InMainMenu` is true. That includes the creator and the
  wardrobe after picking a slot. "First seen" waits for Enter, so entering mid-class is a late join (Excused near the
  end).
- **Suspension.**
  - Violations while suspended are kept in `Discipline.HeldPoints`. When the suspension ends, points become 8 plus
    the held points, with a toast. That can suspend you again.
  - The clock HUD shows "Suspended: stay out of class today" in orange, with no room marker.
- **Hall monitor.** A monitor responding to a clique scuffle (`Respond`) no longer turns to chase a hit it sees on the
  way.

## A record with teeth (2.8.1)

Probation and Suspension now change how school treats you. Tuning is in `Config.Discipline.Record`.

| Level | What changes |
|---|---|
| **Probation** | A hall monitor recognises your fights (and paint) from **40 studs** instead of 25, so it books them on the spot. **Hall passes are void**: the Office refuses them and no punch is used. |
| **Suspension** | Everything Probation does. In addition, **stay off campus during class**: a monitor that sees you inside the school chases you for **Trespassing** (+3, held over the suspension), and leaving campus ends the chase. **Bruno has work** for you at the Back Lot. |

- **Campus:** any `Config.Regions` place of Kind `School`, or `workspace.School`'s rooms (`R101`...) and halls
  (`Hallway`...). The second test is needed in NH Combat Test, where the region boxes sit above the greybox school.
- **Bruno's suspension jobs** (`Config.Quests`, `Requires = { Suspended = true }`). They are daily and skip the clique
  dress code.
  - **Muscle for Hire:** win a scuffle or rumble for the Delinquents.
  - **Day Off:** prank the Ordinary's Commons. That's on campus, so doing it in class time risks Trespassing.
  - Each pays ¥25 and +8 Delinquents.
- **Owed detentions** stop growing at 3 (`MaxDetentionsOwed`). An admin can still add more.

## Notoriety: the Bells (2.37)


Being noticed. Misdeeds that staff witness build **Heat** (0 to 100), and Heat rings up to five **Bells**. It is a live layer over the record: Notoriety never edits the Discipline ladder or its numbers, and it books only through `Discipline.ReportIncident` / `AddViolation`. Spec: `docs/superpowers/specs/2026-11-20-notoriety-timetable-discipline-ui-design.md` §3. Plan: `docs/superpowers/plans/2026-11-21-belltower-r2-bells.md`. Mirror: `tools/belltower-r2/`.

- **Service:** `ServerScriptService.Services.School.Notoriety` (per-player Heat, tier, state, search and summons; ticks every 0.25 s).
- **Maths:** `ReplicatedStorage.Functions.Notoriety` (pure; tested by `tools/belltower-r2/checks/nt_pure.lua` in the Edit VM).
- **Tuning:** `ReplicatedStorage.Config.Notoriety` (every number below).

### The five Bells

| Bell | Heat | Name | What the school does in R2 |
|---|---|---|---|
| 1 | 10+ | **Murmur** | the Bell Rail shows; no staff action yet |
| 2 | 25+ | **Noticed** | the Bell Rail shows; no staff action yet |
| 3 | 45+ | **Named** | one hall monitor responds to the last-seen point (`HallMonitor.Respond`). Any monitor on duty who sees you chases you on sight (the **Wanted** chase, in any duty segment) |
| 4 | 70+ | **Hunted** | every patrolling monitor on duty within 400 studs converges on the spot (`HallMonitor.Converge`), and the PA calls "A disturbance in {Where}. Staff, please attend." (no emergency flag, so at most once per segment) |
| 5 | 90+ | **The Tolling** | an emergency PA: "All staff: a student is loose in {Where}. Find them." The Headmaster has no body yet |

Each step runs once per rise (`Responded`, `Converged`, `Tolled`), and resets when the Heat clears.

### The four states

| State | Means |
|---|---|
| **Lit** | a hall monitor can see you right now (`HallMonitor.SeenBy`: on duty, line of sight with field of view, or chasing you and saw you in the last 0.5 s) |
| **Search** | they lost sight of you less than 30 s ago and are working from the last-seen point |
| **Tarnished** | the search is over, and they know who you are |
| **Hollow** | the search is over, and nobody knows it was you |

### Heat per witnessed misdeed

| Misdeed | Heat | Booked as |
|---|---|---|
| Truancy | 12 | Truancy |
| Trespassing, Curfew | 20 | Trespassing |
| Vandalism (pranks, paint) | 15 | Vandalism |
| Fighting | 25 | Fighting |
| Contraband | 10 | Contraband |
| Exposure (seen transformed by a monitor) | 30 | Exposure |
| AssaultStaff (a hit on a hall monitor) | 45 | Fighting |

- **Night** (22:00 to 06:00): ×1.5. **Probation or Suspension:** ×1.25. Both stack (Truancy at night on probation is 22.5).
- A misdeed with no row adds no Heat.
- **Where it comes from:**
  - every staff report through `Discipline.ReportIncident`, which calls `Notoriety.OnReport`
  - a hall monitor starting a chase (not a Wanted chase, which is the hunt itself)
  - a hit on a hall monitor
  - a character whose `Transformation` attribute turns on while a hall monitor sees them

### Cooling

- **None while Lit.** In Search (under 30 s unseen) Heat falls 1.5 a second, then 3 a second.
- **×2** in a locker (`Hidden` on the character), in the Dorms, or off campus.
- **×3 with an alibi:** in your timetable's room during a class (`ClassInRoom`), or serving detention (`DetentionActive`). The alibi wins over the ×2.
- **The search radius** grows from 30 to 120 studs over the 30 s (`Functions.Notoriety.SearchRadius`). It's built for R4's map candles; in R2 monitors go to the last-seen point.
- At Heat 0 the Bells clear.

### Identified (the face)

- You're identified when a monitor sees you within 25 studs, sees you for 2 s (Lit), or a staff report recognises you.
- Staff then know your face until the end of the next in-game day (`Discipline.FaceKnownUntilDay`, saved). A new misdeed in that time starts identified.

### Caught, escaped, summoned

- **Caught:** a hall monitor's catch reports with `Caught = true`. `OnReport` returns the tier bonus (Bell 3 +1, Bell 4 +2, Bell 5 +3) and clears the Heat. `AddViolation(P, Type, { Bonus })` adds it, and the toast ends "· +N for running". The Contraband catch also carries `Caught = true`.
- **A Wanted catch** books what started the hunt (`Notoriety.BookType`). A Wanted escape files no new report.
- **Escaped and identified:** when the Heat reaches 0, a misdeed that wasn't booked becomes a **summons**. The toast reads "They know it was you. Report to Room 106 outside class by tomorrow."
  - At most 3 are kept, in `Discipline.Summons` (`{ Type, Day, Witness }`, saved).
  - **Serve:** walk into Room 106 (`workspace.School.R106.Zone`) outside class. Every summons is booked at once, **without** the tier bonus.
  - **Ignore:** a summons more than 1 in-game day old is dropped and books **Skipped Detention** (+4).
- **Escaped and unidentified:** nothing is booked (as before).

### The `Exposure` violation

`Config.Discipline.Violations.Exposure`: 3 points, "Seen transformed by staff". It exists so that being seen transformed has something to book.

### Player attributes (the client reads only these)

| Attribute | Values |
|---|---|
| `NHBells` | 1 to 5, or nil at 0 |
| `NHBellState` | `Lit`, `Search`, `Tarnished`, `Hollow`, or nil |
| `NHSearchWhere` | the region title at the last-seen point while in Search, or nil |
| `NHSummons` | the number of summons owed, or nil |

Server signal: `Notoriety.Changed(Player, Bells, State)`. Server API: `Witnessed(P, Misdeed, Pos?, Witness?)`, `OnReport(Incident) -> bonus`, `IsHunted(P)`, `BookType(P)` and `Get(P)`.

### The test probe (Studio only)

`ServerStorage.NHNotorietyProbe` is a BindableFunction made by the service when `RunService:IsStudio()`. It's driven by `tools/belltower-r2/harness/probe.py` and `checks/nt_server.lua`. Call it as `Invoke(Cmd, PlayerName, ...)`:

| Command | Does |
|---|---|
| `Manual(Seen?, Mods?)` | stops the live tick for that player; `Seen` true or false fixes sight, nil asks `HallMonitor.SeenBy` |
| `Live` | resumes the live tick |
| `Reset` | clears Heat, identification, summons and the face |
| `Witness(Misdeed)`, `Report(Type, Recognized, Caught)` | feed the service |
| `Advance(Seconds)` | steps it in 0.25 s ticks |
| `Serve`, `AgeSummons(Days)` | the summons paths |
| `Get`, `Monitors` | read the state |

### Rulings and spec deltas (R2)

1. **Witnesses:** live sight (Lit and Search) comes from the hall monitors (the day monitor and night duty). Every staff report (teachers, monitors, custodian) adds Heat through `ReportIncident`. Student witnesses, snitches and heading them off are R3.
2. **Identification:** only the face is tracked (25 studs, Lit 2 s, or a recognised report). Witness-note tokens are R3, so until then Hollow means not identified and Tarnished means identified.
3. **Summons:** served in Room 106 outside class (NH Combat Test has no Headmaster's office; spec §3.8 says the office). Issued when the search ends (Heat 0), not at the next period change.
4. **`Exposure`** (3 points) is new. Hitting staff books `Fighting`.
5. **Scope:** watched wings and the map layer are R4; the notes row is R3. The Lead Card folding is in R2. `SearchRadius` is built and tested now; in R2 monitors respond to the last-seen point.
6. **The Tolling:** an emergency PA plus every monitor converging. The Headmaster has no body.
7. **Bell 4's PA** goes through `Broadcast.PA` without the emergency flag, so its once-per-segment limit applies.
8. **Test seam:** the Studio-only `ServerStorage.NHNotorietyProbe`.
9. **Version:** 2.37.0.
10. **Contraband Heat 10:** in `Config.Notoriety` but not in spec §3.2, which has no contraband row.
11. **The probation multiplier** also applies on Suspension (the spec says Probation).
12. **Bells 1 and 2** draw no staff response in R2. The spec's "nearest staff walks to look" (Bell 1) and "recognise on sight" (Bell 2) wait for R3's notes. **Bell 5** cools like any other Bell; the spec's "ends only when caught, in the Dorms or off campus" and the campus-wide search are not built.
13. **Quest witness reasons:** `HallMonitor.CheckWitness` is also called by Quests with the objective's `Witness` value. A reason with no row in `Config.Notoriety.Heat` adds no Heat, but it still becomes the stored misdeed, which a later Wanted catch books (`BookType` passes unknown names through). Not checked in Studio: check the quest `Witness` values against `Config.Heat` and against `Config.Discipline.Violations`.

### Verified

**Checked (2026-11-23, NH Combat Test, slot 2):** `nt_pure` PASS (Edit VM); `nt_server` PASS and `nt_monitor` PASS (responding 1) in Play. The live hunt was driven the same day: the monitor confronted (`Wanted`) and booked Fighting with `Bonus 1`; the summons toast and slip were photographed ([img](img/belltower-r2-summons.jpg)). Not checked: quest witness reasons, two players. Backup: `ServerStorage.NH_Backup.BellTower_R2_pre_20261121`.
