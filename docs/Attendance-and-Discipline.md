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

**HUD:** the clock panel has a fifth line: "Record: Warning (3 pts)", "Detention owed: Room 106 (outside class)" (plus a door marker outside class time), or "Detention: trash 2/5".

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
