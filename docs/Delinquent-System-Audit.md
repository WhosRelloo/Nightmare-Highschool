# Delinquent System Audit (2.7.3, 2026-11-13)

The owner asked: "Look through everything on the game and everything you've learned." This is a full audit of the
Delinquent system in NH Combat Test, the fixes made in 2.7.3, the open design questions, and ranked concepts for
expanding it.

## What "the Delinquent system" is

It is three systems that meet at the Back Lot and the hall monitor:

| Part | Where (live, NH Combat Test) | What it does |
|---|---|---|
| **Street crews** (PVE) | `Services.Features.Delinquents` | Crews of 2-4 (`Delinquent`, `Delinquent Brute`, rarely a `Gang Leader`) at the Back Lot (`NHDelinquentSpawn` parts). Easy / Normal / Hard tiers. They go down (carry, grip, race finisher) and pay Combat EXP and Yen. Up to 6 alive, refilled every 20 s out of sight. |
| **The Delinquents clique** | `Social.Cliques`, `CliqueFights`, `CliquePranks`, `CliqueShowdowns`, `CliqueMembership`, `CliqueEvents`, `Config.Cliques`, `Config.Quests` | Bruno Vance's Greasers. Back Lot turf, rival of the Ordinary. Clique quests, daily jobs (Hold the Line, Payback, Guard Duty) and dares, scuffles, rumbles, pranks, Bruno's showdown, membership and a crew, a 25% Boards discount. |
| **Discipline** (becoming a delinquent) | `School.Attendance`, `School.Discipline`, `School.HallMonitor`, `School.Detention`, `Config.Discipline`, `Gui.ClockHud` | Attendance results and witnessed fights or vandalism add points. The ladder is Clear, Warning, Detention, Probation, Suspension. The hall monitor chases truants and fighters, and detention is served in Room 106. |

Saved data, all through ProfileService PlayerData: `Attendance`, `Discipline` (written with `UpdateState SetAttendance`
/ `SetDiscipline`), `Social.Cliques`, `Social.Showdowns`, `Social.Membership`. The crews keep nothing.

### State flow

```
class period ─ Attendance (1 s box test) ─ bell ─ Finalize ─ Recorded ─┐
hall monitor (truancy / fight / paint) ─ ReportIncident (recognised) ──┼─ Discipline.AddViolation ─ Recompute ─ level
detention walk-out ────────────────────────────────────────────────────┘        │
                                                         Present class / daily decay / ServeDetention ─ Reduce
Recompute: reaching Detention from below owes 1 · Probation 2 days · Suspension until the next day, then 8 points + Probation
```

### Remotes

Nothing in these systems trusts client input:

- `NHCliques.Get`, `Leave` and `Today` take no input and are rate-limited.
- `Changed` and `Say` only go from server to client.
- Trash, bin, prank, clean and watch are server-side ProximityPrompts, and each one re-checks the owner and range.
- The hall pass (`Features.Kit.ShowPass`) is checked on the server: once per period, punches, and only for Truancy
  within its chase grace.
- The Boards discount is worked out on the server.

## Bugs fixed in 2.7.3

Every fix was tested in Play on slot 4 "Testy". The evidence is in `CHANGELOG.md` 2.7.3.

| # | Bug | Fix |
|---|---|---|
| 1 | **Booked Absent from the character creator.** After picking a slot you're still in the menu (creator or wardrobe), but attendance already tracked you. Spending a class period there booked Absent and +3 points. | `School.Attendance`: nothing is tracked while `InMainMenu` is true, and "first seen" waits for Enter. Entering late in a class counts as a late join (Excused near the end). |
| 2 | **A suspended student was sent to class.** The clock HUD showed "NOT IN CLASS" in red and a waypoint to the room. | `Gui.ClockHud`: "Suspended: stay out of class today" in orange, and no room marker. |
| 3 | **Suspension was a free pass.** Points earned while suspended were wiped when it ended (reset to 8). | `School.Discipline`: they're held in `Discipline.HeldPoints` and added back on top of the 8, with a toast. Enough of them suspends you again. |
| 4 | **A monitor on its way to break up a scuffle got distracted.** If it saw a hit on the way, it started a chase, and leaving `Respond` ran the scuffle's "arrived" callback, so the scuffle ended as "Monitor" before it got there. | `School.HallMonitor`: in `Respond` it keeps going (`OnDamage` and `CheckWitness`). |
| 5 | **Guard Duty (Bruno's daily job) could be wasted.** The rival's prank came 30 s after the job started, wherever you were, and that was the job's one sure prank. | `Social.CliquePranks.GuardDuty`: the prank waits until you're within 80 studs of the guarded hangout (up to 40 min). |
| 6 | **Downs paid after the fight ended.** A scuffle or rumble fighter downed in the second before fighters walk off still paid +6 standing. | `Social.CliqueFights.OnDowned`: only while that scuffle or rumble is live, as `OnHit` already checked. |
| 7 | **The Delinquents sent backup against Delinquents.** When a street-crew Delinquent hit a Delinquents member, two Back Lot Toughs spawned to fight it. The backup check only knew event fighters. | `Social.CliqueFights.Backup`: the attacker's clique also comes from its `Clique` attribute or `Config.Cliques.Npcs` by name. |

## Findings left for the owner (design decisions, not changed)

| # | Finding | Evidence | Options |
|---|---|---|---|
| A | **Fighting violations during fights the game asks for.** Rumbles ("Pick a side", AfterSchool at the Commons), Commons scuffles and Guard Duty stops are all monitor duty. A helper within 25 studs of a monitor is booked +4 Fighting per 10 s. | `HallMonitor.OnDamage` only exempts `CombatAllowed` zones; `NHCliqueFighter` is set and never read. | Leave it as the risk of fighting on school grounds; exempt hits on event fighters; or cover the rumble venue with a temporary `CombatAllowed` part, as showdowns do. |
| B | **The street crews aren't really the clique.** `Config.Cliques.Npcs` maps `Delinquent` and `Delinquent Brute` to the Delinquents, but the crews never get the `Clique` tag. Downing one changes no standing: tested, Delinquents 0 → 0 and Ordinary 2 → 2. `Cliques.md` says "Downing a Delinquent gives The Ordinary +2". `Gang Leader` isn't mapped at all. | Runtime test, 2.7.3 | Make them a separate gang (concept 3), or tag them and accept the standing swing. |
| C | **Delinquents members are jumped at the Commons at any hour,** class included and during a rumble. | `CliqueFights` TurfStep has no segment check and no live-event check. | Skip confrontations in class and during a live scuffle or rumble. |
| D | **Winning Bruno's showdown can lower your Delinquents standing.** Downing Bruno and his ring costs -8 each; the win only tops up below 60. | `CliqueShowdowns` L310-311 | Skip the down penalty for showdown fighters. |
| E | **Anyone can beat Bruno for you.** The win only checks that the leader is out. | `CliqueShowdowns` L269 | Credit the win only if the challenger landed the down. |
| F | **Commons scuffles usually end as "Monitor".** The monitor is sent 4 s in. In the 2.7.3 test it took the full 30 s give-up to "arrive", and the scuffle still ended as Monitor. Hold the Line needs 2 wins a day. | Play test, 2.7.3 | Send the monitor later (15-20 s) or fix its route to the Commons. |
| G | **The PVE crews are an uncapped Yen and EXP farm.** Two grunts every 20 s is roughly ¥3,600 and 10,800 Combat EXP an hour from the Back Lot. A Present class pays ¥5. | `Features.Delinquents` | Diminishing returns per hour, or a nightly "crew's out of cash" cap. |
| H | **Owed detentions pile up.** Every climb back to Detention owes one more, and Testy owes 6. Owing has no consequence. | `Discipline.Recompute` | Cap owed at 2-3, and make Probation restrict something (concept 1). |
| I | **Clique standing is written outside UpdateState.** `Cliques.Add` mutates the profile; it saves, but the client's PlayerData copy goes stale until the next `Reputation.Sync`. | `Social.Cliques` L66-89 | Call `Reputation.Sync` in `Add`, and add a `StandingChanged` signal. |
| J | Smaller items | | A prank-started confrontation skips the duel and showdown checks. Two players can farm +3 by cleaning each other's pranks. `CliqueMembership.TestAs` is never cleared (Studio only). The Lieutenant bonus is checked after the job's own reward. |

The full clique audit, with line numbers, is in `tools/delinquent-audit/clique-findings.md`. Findings F3 and F9 there were checked at runtime: F3 (standing) was refuted, and F9 was fixed.

## Concepts for enhancing and expanding it (ranked)

Ranked by how much they add to the game for the effort. Effort: S is about a day, M is 2-4 days, L is a week or more.

1. **A record with teeth (Probation and Suspension that matter).** Effort: M. **Built in 2.8.1** (see `Attendance-and-Discipline.md`).
   - **Player:** on Probation, the hall monitor recognises you from 40 studs instead of 25, and hall passes are
     refused. On Suspension, you're barred from campus during class: the gates close, and being caught inside is
     Trespassing. Bruno's crew welcomes you at the Back Lot with "suspension jobs".
   - **Fits:** the `DisciplineLevel` and `Suspended` attributes already exist and nothing reads them yet.
     `HallMonitor.CatchFilter` and `Config.Discipline.Witness` hold the ranges, the Trespassing violation exists,
     and Bruno's jobs live in `Config.Quests`.
   - Also fixes finding H.
2. **Notoriety: a delinquent reputation track.** Effort: M.
   - **Player:** Notoriety climbs from hall-monitor escapes, unrecognised incidents, pranks, scuffle wins and
     showdowns. It earns titles (Hall Ghost, Back Lot Legend), Delinquents standing, and wariness from the Ordinary
     and the Vigil. High notoriety makes the monitor look for you by name.
   - **Fits:** hook `HallMonitor.Escaped`, `Discipline.ViolationAdded`, `Quests.Completed` and a new
     `Cliques.StandingChanged` signal. Titles go through `Reputation.AwardTitle`. The weekly
     `Superlatives` "Most Likely to Be Expelled" already exists.
3. **Make the street crews their own gang: "The Rejects".** Effort: S-M.
   - **Player:** the hostile crews become kids Bruno threw out. They hold the Back Lot's edge and jump anyone,
     Delinquents included. Bruno pays you to clear them, and the Ordinary thank you.
   - **Fits:** resolves finding B. Add a hostile entry to `Config.Cliques`, tag the crews, and give them a leader
     NPC for a showdown. Their downs would feed Delinquents jobs, such as a new "Clear the Rejects" `Type = Defeat`.
4. **Skipping class as a game: escape routes and hiding.** Effort: M.
   - **Player:** slip out of class through the Back Lot gate, hide in lockers or stalls when the monitor turns the
     corner, and forge a hall pass at the Back Lot. A Delinquents member's perk is a forged pass that works once a
     day.
   - **Fits:** `Quests.Stealth` already does hiding and watchers, and `Features.Kit` has the hall pass and its
     punches. The `Perk_Shadowstep` pattern (Crimson Court) shows how to add a clique perk.
5. **Detention you remember.** Effort: S-M.
   - **Player:** rotating tasks: scrub graffiti (real `Vandalism` walls and prank messes), shelve library books, or
     help the lunch lady. A detention kid NPC trades rumours, and a lore clue drops on your third detention.
   - **Fits:** `Detention.Completed` was left as a story hook. `CliquePranks` messes and the walls system already
     clean up, and the R106 kid is already there.
6. **Race-flavoured trouble.** Effort: M.
   - **Player:** Vampires and Wraiths get a curfew game at night: the night custodian works as a hall monitor
     after 10 PM. Werewolves on a full moon risk a "Lost control" violation if they fight on campus. Wraiths slip
     monitors more easily.
   - **Fits:** `HallMonitor.DutyKinds`, the Night segment, the `Lineage.MoonEvent` calendar, and the
     `Perk_Shadowstep` lose-sight multiplier. Never lets players set Race: it only reads it.
7. **Bruno's crew ranks earn real power.** Effort: M-L.
   - **Player:** a Lieutenant can call a scuffle on the Ordinary, run a protection racket on Ordinary NPCs for Yen
     (each collection risks a witness), and pick who joins the crew.
   - **Fits:** `CliqueMembership` ranks and the crew, `CliqueFights.StartScuffle`, and
     `Discipline.ReportIncident` for the risk.
8. **Teacher and student witnesses ("snitches").** Effort: M.
   - **Player:** teachers in classrooms book fights they see. Ordinary and Vigil students may report you unless
     you're Respected with them. A Delinquents member can lean on a witness to keep quiet.
   - **Fits:** this is the "Next" item in `Attendance-and-Discipline.md`. It reuses `ReportIncident` and
     `Recognized`, with clique standing as the snitch filter.
9. **A "Most Wanted" notice board.** Effort: S.
   - **Player:** the school board lists the server's three most notorious students this week, with their
     mugshot pose.
   - **Fits:** the notice board (`Commands.BoardRefresh`) and `Superlatives`. Pairs with concept 2.
10. **Fair PVE economy.** Effort: S.
    - **Player:** the Back Lot crews pay full for the first few each hour, then less ("they're broke"). A crew
      leader drops a rare item once a night.
    - **Fits:** finding G, in `Features.Delinquents` `NPCDefeated`.
