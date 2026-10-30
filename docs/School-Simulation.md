# School Simulation: NH Combat Test

**Status:** the school clock and timetable are built and verified. Attendance, classes, and NPC schedules aren't built yet.

## Clock

The numbers come from the concept doc (School Campus System):

| Setting | Value | Where |
|---|---|---|
| Real time per in-game hour | 5 minutes (so 1 in-game minute = 5 s and 1 day = 2 real hours) | `Config.SchoolSchedule.RealSecondsPerGameHour` |
| Clock mode | **Global**: every server shows the same time, counted from `GlobalEpoch` (2024-01-01 UTC). `Local` mode starts each server at `StartTime` (7:30 AM). | `ClockMode`, `GlobalEpoch`, `StartTime` |
| School hours | 8:00 AM–12:00 PM (20 real minutes) | `SchoolHours` |
| EXP multiplier in school hours | 1.2× | `SchoolHoursExpMultiplier` |
| Day cycle | Monday–Friday repeating. There are no weekends, because the concept wants the 8 AM boost every in-game day. | `DayNames` |
| Lighting | `Lighting.ClockTime` follows the clock | `SyncLighting` |

**Doc inconsistency:** the concept says school hours are "10% of the day", but 8 AM + 4 hours is about 17%. The explicit 8 AM + 4 hours is used here; change `SchoolHours` if 10% was intended.

## Timetable (`Config.SchoolSchedule.Segments`)

| Time | Segment | Kind |
|---|---|---|
| 0:00–6:00 | Night | Night |
| 6:00–7:30 | Morning | Morning |
| 7:30–8:00 | Before School | BeforeSchool |
| 8:00–8:20 | Homeroom | Class |
| 8:20–9:00 | Period 1 | Class |
| 9:00–9:05 | Passing | Passing |
| 9:05–9:45 | Period 2 | Class |
| 9:45–10:00 | Break | Break |
| 10:00–10:40 | Period 3 | Class |
| 10:40–10:45 | Passing | Passing |
| 10:45–11:25 | Period 4 | Class |
| 11:25–12:00 | Lunch | Lunch |
| 12:00–17:00 | After School | AfterSchool |
| 17:00–21:00 | Evening | Evening |
| 21:00–24:00 | Night | Night |

A 40-minute class is about 3 minutes 20 seconds of real time, and a passing period is 25 real seconds. Subjects, teachers, and rooms aren't assigned to periods yet. The concept doc doesn't name any.

## How it works

- **`Services.School.SchoolClock`** (server) owns the time.
  - It publishes `ReplicatedStorage.SchoolClock` with these attributes:
    - `Epoch`: the server time at which in-game day 0, 00:00 began
    - `Period`, `Kind`, `SchoolHours`
  - Clients compute the current time themselves from `Epoch` and `workspace:GetServerTimeNow()`, so the clock sends **no network traffic per tick**.
  - API:
    - `GetState()`
    - `IsSchoolHours()`
    - `GetExpMultiplier()`
    - `SetTime("HH:MM", Day?)`
    - signals: `PeriodChanged(State, OldSegment)`, `SchoolHoursChanged(bool)`
- **`ReplicatedStorage.Functions.SchoolTime`** holds the pure time math that server and client share: parse and format times, find the current segment, and build the state.
- **`StarterPlayerScripts.Controllers.Gui.ClockHud`** is a top-right panel showing:
  - the day and time
  - the current period and when it ends
  - a "School hours: 1.2x EXP" badge during school hours

## Verified (Studio playtest)

- The clock starts at 7:30 AM and advances 1 in-game minute every 5 real seconds.
- At 7:59 → 8:00 the segment becomes Homeroom, school hours turn on, and EXP is 1.2×.
- At 11:59 → 12:00 the segment becomes After School, school hours turn off, and EXP is 1×.
- At 23:59 → 0:00 the day changes from Monday to Tuesday and Lighting.ClockTime is 0.
- `PeriodChanged` fires once per transition.
- The HUD shows "Tuesday 9:20 AM / Period 2 (until 9:45 AM) / School hours: 1.2x EXP" (checked by screenshot).

## Next

1. ~~Classrooms and attendance~~: **done**, see `Attendance-and-Discipline.md`. Subjects and rooms per period are in `Config.Classes`. The HUD shows your current or next class and marks the room door.
2. **NPC schedules** driven by `PeriodChanged`.
3. **Timetable UI** (a full schedule view) and waypoints to the next class.
