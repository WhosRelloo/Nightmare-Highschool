# 13. The Living School (Expansion Phase 2)

**Status:** approved 2026-11-18. **2.27 shipped** (plan: `docs/superpowers/plans/2026-11-18-roster-and-memory.md`;
its deltas are §9 items 8 to 15). **2.28 shipped** (plan: `docs/superpowers/plans/2026-11-18-staff-school-day.md`;
deltas 16 to 23). **2.29 shipped** (plan: `docs/superpowers/plans/2026-11-18-incidents-and-rumours.md`;
deltas 24 to 32). **2.30 shipped** (plan: `docs/superpowers/plans/2026-11-18-broadcast-and-curfew.md`; deltas 33 to
40). **Phase 2 complete (2.27 to 2.30).**

**Sources:** doc 02 §4.1 to §4.6, §7.1 and §11.1, doc 07 §2 to §7, and doc 08 Phase 2. This spec makes them
buildable; where it differs from them, §9 says so.

**Releases:** Phase 2 ships as four releases, each playable and tested before the next starts.

| Release | Name | Builds |
|---|---|---|
| **2.27** | Roster & memory | `Config.Students` (24), `Social.Roster`, saved relationships (64 cap), introductions |
| **2.28** | Staff in the school day | 4 teachers and the Headmaster on schedules, per-student timetables, teacher witnesses, the off-screen simulation |
| **2.29** | Incidents & rumours | `World.Incidents` (the bus and the scene director, 6 scenes), `Social.Rumours` |
| **2.30** | Broadcast & curfew | `World.Broadcast` (Gazette, PA, Night FM station), curfew 22:00 to 06:00, night duty |

---

## 1. Architecture

**The approach** is a roster layer over the NPC code that works (approach A in chat). The other two were a rewrite of
Schedules and StudentBrain (it risks all NPC behaviour) and names only (it fails doc 08's acceptance).

- **Identity:** `Social.Roster` owns who each student is, their timetable and where they are now.
- **Bodies:** `Features.Schedules` keeps its movement code (Spawn, WalkTo, Sit, Mingle, Lunch, Club) and asks
  `Roster` who goes where.
- **Behaviour:** `AI.StudentBrain` keeps its reactions. Its memory of each player is saved through `Reputation`.
- **New services listen; they don't edit:** each later release adds a service that plugs in through signals.

```
SchoolClock.PeriodChanged ─> Roster.Plan ─> Schedules (bodies near players)
                                         └> abstract spots (everyone else)
Reputation.Relationships <─> StudentBrain memory, Talk.Attitude, introductions
Emitters ─> Incidents.Emit ─┬> Reputation (Helped/Fought/…)
                            ├> Discipline (teacher witness)
                            └> Rumours ─> Broadcast ─> Gazette · PA · Night FM
HallMonitor night duty + Custodian patrol ─> Discipline (Trespassing) during curfew
```

**Signals:** `Roster.Moved(id, spot)`, `Reputation.RelationshipChanged` (it exists), `Incidents.Emitted(incident)`,
`Rumours.Spread(rumour, region)`, `Broadcast.Posted(item)`.

**Conventions** are those of doc 07 §1: `Shared`/`Local` tables, `OnStart`, `Config.*` data modules, and server
authority for every reward and record.

---

## 2. Release 2.27: Roster & memory

### 2.1 `ReplicatedStorage.Config.Students`
24 entries, 3 per clique. The draft roster is in §8 for the owner to edit. Each entry has:

| Field | Meaning |
|---|---|
| `Id` | stable key, e.g. `OdetteMarsh` (used by saves; never renamed) |
| `Name` | full name |
| `Clique` | one of the 8 `Config.Cliques.Defs` keys |
| `Year` | 1 to 4 |
| `Bravery` | 0 to 1, read by `NpcBuilds.Personality` (pace, height, posture) and by reactions |
| `Temper` | `Warm`, `Cool`, `Sharp`, `Shy` or `Wild`: picks greeting and reaction pools |
| `Set` | `A`, `B`, `C` or `D`: the timetable set (§3.3) |
| `Build` | an `NpcBuilds` seed, so the same student always looks the same |
| `Bio` | one line, shown on their Students card once they've introduced themselves |
| `SkipChance` | Delinquents only: the chance per class period that they skip |

`Config.Cliques.Students` (the 14 anonymous slots) is replaced by the roster. Its clique counts are kept as the
minimum per clique.

### 2.2 `ServerScriptService.Services.Social.Roster`
- **`Roster.Get(id)`:** the entry plus live state (`Spot`, `Embodied`).
- **`Roster.Plan(period)`:** for each student, a spot for that period: a seat in a classroom, a lunch slot, a club,
  a hall spot, the gate (arriving or leaving), or `Away` (skipping or gone home). Students are never planned into
  the Staff Room.
- **`Roster.WhereNow(id)`:** where they are, embodied or not. Off-screen students are at their planned spot, and
  travel takes the planned time with no pathing.
- **`Roster.Near(region)`:** who is in a region now, for witnesses (2.29).
- **Signals:** `Roster.Moved(id, spot)`.

### 2.3 Saved relationships (`Social.Reputation`)
- **The list grows:** `Config.Reputation.Npcs` covers the named cast (`Config.Npcs`: the leaders, Sable, the coaches,
  Mrs. Okada, Mr. Hale, the Custodian, the new staff) plus the roster.
- **The entry:** `Social.Relationships[id] = { V, Met, Last, Flags }`:
  - `V` is the value, -100 to 100, with the existing `RelationshipStates`
  - `Met` is a boolean
  - `Last` is the in-game day of the last change
  - `Flags` holds counts: `{ Fought = n, Helped = n, Pranked = n, Lied = n }`
- **Migration:** the existing `{ Value, Met }` entries for Ezra and Vesper become `{ V, Met, Last = today, Flags = {} }`
  in `Sanitize`.
- **Cap:** 64 entries. When it's full, the oldest (`Last`) entry in the Acquaintance state is dropped first, then the
  oldest of any state except Trusted and Hostile.
- **`ChangeRelationship(player, id, amount, reason, flag?)`** is the only writer. `flag` adds to the count.
  Notifications fire for the named cast as now. For rostered students they fire only on a state change.

### 2.4 StudentBrain memory
- `memo(S, Pl)` reads its `Met`, `Greeted` and `Fought` from the saved entry (`Met`, `Last`, `Flags.Fought`) when the
  student is rostered. `Greeted` stays per session.
- `Fought` and `Helped` are recorded through `ChangeRelationship` (fight: -15 and `Fought`; help in a scene: +10
  and `Helped`).
- **Greeting pools** gain lines keyed on flags and state, for example "You again." (Fought, Rival) and "Thanks for
  last time." (Helped). They're picked by `Temper`.
- `Talk.Attitude` reads the saved state.

### 2.5 Introductions
- A rostered student shows as "a Vigil student" (their clique's name) on their nameplate and in the Students list.
- **They introduce themselves** the first time you talk to them, if your relationship is Acquaintance or better. The
  student says their name, and `Met` is set.
- **Start with a fight**, and the relationship falls to Rival before any introduction. Then you learn their name only
  from other students (a rumour that names them, in 2.29) or by bringing the relationship back to Acquaintance and
  talking again.
- **The Students list** (Tab) gets a Roster tab: the students you've met, with their clique, state and `Bio`.

### 2.6 2.27 acceptance
- The roster spawns all 24, each with the same look every time.
- Fight a rostered student, leave, rejoin a day later: they still react to it ("You again.").
- Help one twice: their greeting changes.
- Introductions follow §2.5, and the 64 cap drops entries in the stated order (`RelationshipCapTest`).
- Old saves keep Ezra and Vesper.

---

## 3. Release 2.28: Staff in the school day

### 3.1 The staff (`Config.Npcs`, made with the existing NPC builder)

| Id | Name | Subject / role | Day | Room |
|---|---|---|---|---|
| `Sallow` | Ms. Ingrid Sallow | Mathematics | class periods at the TeacherDesk, otherwise the Staff Room | Room 102 |
| `Hale` | Mr. Hale (exists) | Chemistry; homeroom register | Homeroom in Room 102 for the roll call, then Chemistry | Room 103 |
| `Pryce` | Mr. Edmund Pryce | English | as Sallow | Room 104 |
| `Whitlock` | Dr. Constance Whitlock | History | as Sallow | Room 105 |
| `Ashgrave` | Headmaster Corvin Ashgrave | the Headmaster | office hours (Periods 1 to 3) in his office, assemblies, crises | a new office mark |
| `Custodian` | the Night Custodian (exists) | | sweeps the main hall by day; night patrol in 2.30 | |
| `Okada` | Mrs. Okada (exists) | | unchanged | |

- **Draft personalities** (for review):
  - **Sallow:** exact, dry, keeps a ruler she never uses.
  - **Pryce:** theatrical, reads the register as if it were a play, kind to the quiet ones.
  - **Whitlock:** the school's own historian. She knows the False Explanation by heart and believes it.
- **The Headmaster's office:** there's no office area in the place. The 2.28 plan surveys the building (read-only on
  the Map) for a room off the Main Hall and adds an `Area_HeadmasterOffice` box and marks in NH Combat Test.
- **Staff mini-arcs** (doc 02 §4.6) are not in Phase 2 (§9).

### 3.2 Teachers as witnesses
- **When:** a teacher is at their TeacherDesk (the period is a class period and their body is there or, off-screen,
  their spot is) and has line of sight from the head to the event (a raycast, ignoring characters).
- **What:**
  - a fight, or hitting a student, inside that teacher's room
  - lateness: `Attendance` still decides tardiness; the teacher only adds their name
- **How:** `Discipline.ReportIncident({ Type, Player, Witness = teacherId, Where })`. The violation reads
  "Reported by Mr. Hale". With no teacher there, nothing changes from today.

### 3.3 Per-student timetables
- **Sets:** the 24 students are in four sets of six (`Set` A to D). In each class period, every subject room hosts one
  set, and the sets rotate:

| | Room 102 Maths | Room 103 Chemistry | Room 104 English | Room 105 History |
|---|---|---|---|---|
| Period 1 | A | B | C | D |
| Period 2 | D | A | B | C |
| Period 3 | C | D | A | B |
| Period 4 | B | C | D | A |

- **The player's timetable** (`Config.Classes.Periods`) is unchanged. Whichever room you attend, six named students and
  the teacher are there.
- **Homeroom:** as many students as Room 101's chairs allow (sets A and B first); the rest have study hall in The
  Library. The 2.24 roll call cut is unchanged.
- **The 6-seat cap and the "east wing" fallback** in `Schedules` go. A room seats its set, and extras stand at the back.
- **Skipping:** a Delinquent skips a class period with their `SkipChance`, and spends it at The Back Lot or The Den.

### 3.4 The off-screen simulation
- **Bodies** exist only within 160 studs of a player. A student leaving that range is despawned at once, and one
  entering is spawned at their `WhereNow` spot.
- **Brains** run at 5 Hz near players and 1 Hz otherwise, at most 3 path plans at once, and there's no new per-frame
  server loop.
- **Target:** 24 students and 6 staff at 60 fps on server and client.

### 3.5 2.28 acceptance
- A fight in class is booked by that room's teacher, and not when the teacher is in the Staff Room (`WitnessTest`).
- Each class period's rooms seat the sets in §3.3.
- Off-screen students are where `WhereNow` says when you walk in.
- 60 fps with everyone loaded (Studio profiler).

---

## 4. Release 2.29: Incidents & rumours

### 4.1 `ServerScriptService.Services.World.Incidents`, the bus
- **`Incidents.Emit({ Kind, Where, Who, Witnesses?, Severity, Truth = true })`:**
  - `Who` lists players and NPC ids with a role each (`Doer`, `Target`, `Helper`)
  - `Witnesses` is filled from `Roster.Near(Where)` and the staff spots if it isn't given
- **`Incidents.On(kind, fn)`** and the `Incidents.Emitted` signal.
- **Emitters:** a one-line `Emit` in code that already runs:
  - clique fights
  - HallMonitor catches
  - Discipline violations
  - Downed
  - beast sightings
  - Sports results
  - pranks
  - moon events
- **Consumers:** Reputation (the `Helped`, `Fought`, `Pranked` and `Lied` flags from §2.3), Discipline (a teacher
  witness), and Rumours.

### 4.2 The scene director (`ReplicatedStorage.Config.Scenes`)
Six scenes, each with a cast of 2 to 4 rostered NPCs, a length, where it can happen and optional player hooks:

| # | Scene | Where / when | Cast | Player hook | Outcome |
|---|---|---|---|---|---|
| 1 | **The argument** | halls, The Commons; day | 2, from rival cliques (`RivalPairs`) | step between them (Supporting) | a rumour, or a scuffle if nobody steps in |
| 2 | **Into the locker** | a hall with lockers; day | 1 doer, 1 target, 0 to 2 watchers | help the target out (Helping) | a rumour; the doer's clique standing rises unless you help |
| 3 | **The notice board** | the Main Hall board; morning | 1 to 2 gawkers | read it (a clue line) | a rumour about who did it (the true answer is an NPC) |
| 4 | **A sound in the east wing** | The East Wing; night | 1 to 2 students who heard it | go and look | a night-only rumour |
| 5 | **A figure at the window** | a window facing the grounds; night | 1 to 2 students who saw it | look up (a Forgotten Student hint, from 03) | a rumour that grows on every hop |
| 6 | **The dare** | the Records Office door; dusk | 2 to 3, one dared | dare them back, or stop them | a rumour; the dared one may get a Trespassing violation of their own |

- **Rules:**
  - only in a region where a player can see it
  - at most 1 per region every 10 minutes
  - never during a cutscene, or in a class period inside a classroom
- **Bodies:** scenes use the same bodies as `Schedules`. A cast member is borrowed and handed back when the scene ends.

### 4.3 `ServerScriptService.Services.Social.Rumours`
- **A rumour:** `{ Fact, Subject, Where, When, Truth, Hops, Notable }`, made from an incident.
- **Spread:**
  - through student pair-chats (`StudentBrain`'s `chat`), and off-screen between two students in the same region
  - at most one hop every 5 minutes per rumour, region by region
  - at most 30 live, and each expires after 1 in-game day
- **Mutation:** each hop has a 20% chance to change one detail:
  - the place, to a neighbouring region
  - the size ("shoved" can become "slammed")
  - the person, but only to an NPC who was present
- **The safety rule, enforced in code:** a rumour about a real player carries only true facts. A player can't be
  added as the subject of a deed they didn't do, and a player who is the subject can't be swapped out of their deed
  for someone else's. Mutation is blocked for any field holding a player. `RumourSafetyTest` runs 10,000 random hops.
- **Hearing them:** a "Rumour" moment in `Config.CliqueTalk` (students say them aloud), and Sable's Fortune can draw
  one. A rumour can name a rostered student, which is how you can learn a name you never got (§2.5).
- **Not saved:** they're server-wide. Rumours marked `Notable` are saved only once the Archive exists (Phase 3).

### 4.4 2.29 acceptance
- Each of the six scenes runs, follows its rules and emits its incident (`IncidentTest`).
- A scene becomes a rumour that changes only in the allowed details.
- `RumourSafetyTest` passes.

---

## 5. Release 2.30: Broadcast & curfew

### 5.1 `ServerScriptService.Services.World.Broadcast`
- **Items:** `{ Id, Kind, Text, When, Source }`. The kinds are `Announcement`, `IncidentReport`, `CallerLine` (a
  rumour, which keeps the safety rule), and `Transmission` (a chapter beat). They're server-wide, in a rolling list
  of 40.
- **`Config.Broadcast`:** the PA triggers, the text templates, and the Night FM segment order.

### 5.2 The three outputs
- **The Gazette (Phone):** WHISPERS takes live rumours in place of its 7 fixed strings, with the fixed strings as the
  fallback. Campus takes the day's incident reports.
- **The PA, by day:**
  - a chime, a typed line on the ClockHud, and a talking-face speaker (existing hall props and kit art); text only
  - at most 1 per period, except emergencies
  - triggered only by real state: the bell, an assembly, a match tonight, a substitute, curfew in force, a crisis, and
    the missing student (story)
  - an attendance warning goes only to the student it's about, through their phone
- **Night FM, 21:00 to 03:00:** a "Midnight Broadcast" station beside the personal player. It plays text segments
  with a sound bed from existing audio: caller lines, incident reports and transmissions.
- **Saving:** `Phone.Broadcast` holds the last item read, so only newer items show as new.

### 5.3 Curfew
- **When:** 22:00 to 06:00, from `SchoolClock` (2.22).
- **After hours means:**
  - in a `Restricted` region (The Graveyard, The Boiler Yard, The Archive)
  - in a `Forbidden` region (The Staff Room, The Records Office)
  - or in a `School` region other than The Dorms
- **Allowed:** `Grounds`, `Turf`, `Sports` and The Dorms.
- **Patrols:**
  - the Night Custodian walks the Forbidden and Restricted rooms
  - a night monitor, a new `NightDuty` kind in HallMonitor, walks the halls
  - both use the existing stealth meter, line of sight and locker hiding
- **Caught:** the existing Trespassing violation, plus HallMonitor's existing confiscation of an item you're
  carrying, if any. No new penalties.
- **Story stages:** the After Hours quest's own night stages and every cutscene are exempt.
- **The phone:** its "monitors on their rounds" line becomes true.
- **Rewards for the risk** already exist: night clues, beasts, rites and the night-only scenes and rumours (2.29).

### 5.4 2.30 acceptance
- The PA announces only real events, at most one per period (`BroadcastTest`).
- WHISPERS shows live rumours.
- Night FM's station plays from 21:00 to 03:00.
- Curfew catches you in the Records Office at 23:00 and not at 15:00, and not on After Hours' night stages
  (`CurfewTest`).

---

## 6. Data changes (additive, migrated by `Sanitize`)

| Field | Owner | Shape | Budget |
|---|---|---|---|
| `Social.Relationships` | Reputation | up to 64 × `{ V, Met, Last, Flags }` | under 4 KB |
| `Phone.Broadcast` | Phone | the last item id read | tiny |

Nothing else is saved. Roster state, incidents and rumours are server-wide and rebuilt each server.

---

## 7. Testing and safety (every release)

- **Self-tests (TestBridge):** `RosterTest`, `RelationshipCapTest` (2.27), `WitnessTest` (2.28), `IncidentTest`,
  `RumourSafetyTest` (2.29), `BroadcastTest`, `CurfewTest` (2.30), plus the Phase 1 and cutscene regression suite.
- **Live checks:** on slot 2, snapshotted before and restored after; the acceptance items in §2.6, §3.5, §4.4 and §5.4.
- **Performance:** 24 students and the staff at 60 fps (the Studio profiler).
- **Saving:** a rejoin and save check on slot 4 "Testy", and a profile-size check that warns above 1 MB.
- **For the owner:** the two-client local server test (group scenes, shared rumours) and a phone-size check.
- **Rules:**
  - Build only in NH Combat Test. The Map is read-only, and its marks go in a port table.
  - Back up each script before its first edit (`ServerStorage.NH_Backup.<Release>_pre_<date>`).
  - Mirror the files in `tools/phase4-2270/` (and 2280, 2290, 2300).
  - Use existing art, UI and effects only, with no blocky organic props.
  - Each release gets its CHANGELOG entry, Discord post, status row and vault copy. Phase 2 ends with an
    #announcements wave post.

---

## 8. Draft roster (for the owner's review)

Original names; none borrow a real person. Surnames already in use (Vale, Vance, Crane, Hale, Larkin, Vey, Mallory,
Varga, Ashby, Moreno, Grey, Thorne, Dunmore, Ashgrave, Holt) are avoided.

| Id | Name | Clique | Year | Bravery | Temper | Set | Bio |
|---|---|---|---|---|---|---|---|
| OdetteMarsh | Odette Marsh | Choir | 3 | 0.3 | Warm | A | First soprano. Swears the chapel organ plays one note after the hymn ends. |
| SilasPenwright | Silas Penwright | Choir | 2 | 0.5 | Cool | B | Copies every hymn by hand, and keeps the pages nobody sings. |
| AgnesLowe | Agnes Lowe | Choir | 1 | 0.2 | Shy | C | New to the Choir. Hums when she's frightened, which is often. |
| CassiusRook | Cassius Rook | Court | 4 | 0.8 | Sharp | D | Vesper's right hand. Smiles at you the way a cat smiles at a bird. |
| MargueriteDray | Marguerite Dray | Court | 3 | 0.6 | Cool | A | Collects favours like other people collect stamps. |
| TeodorBlackwell | Teodor Blackwell | Court | 2 | 0.5 | Sharp | B | Old family, older manners. Never seen eating in daylight. |
| ImogenHart | Imogen Hart | Vigil | 3 | 0.8 | Cool | C | Ezra's best tracker. Writes every patrol in a notebook she won't show anyone. |
| FelixCorran | Felix Corran | Vigil | 2 | 0.7 | Warm | D | Joined the Vigil to be brave. Still working on it, loudly. |
| NadiaStroud | Nadia Stroud | Vigil | 4 | 0.9 | Sharp | A | Has been on night watch so long she sleeps standing up. |
| JuniperFenn | Juniper Fenn | Ink | 2 | 0.4 | Wild | B | Draws the school's corridors from memory, and some that aren't there. |
| OttoKesler | Otto Kesler | Ink | 3 | 0.3 | Cool | C | Prints the Ink Club's zine. Knows which rumours are true and sells the rest. |
| BeatrixLull | Beatrix Lull | Ink | 1 | 0.5 | Warm | D | Sable's newest student. Reads tea leaves badly and palms worse. |
| MarcusAdeyemi | Marcus Adeyemi | Athletes | 4 | 0.9 | Warm | A | Sprinter. Says the north field is faster at night, and won't say why. |
| TamsinRowe | Tamsin Rowe | Athletes | 2 | 0.7 | Sharp | B | Captain's pick for the Ravens. Plays like she's being chased. |
| LeoBrandt | Leo Brandt | Athletes | 3 | 0.6 | Cool | C | Goalkeeper. Has never let in a goal after midnight. |
| ClaraWebb | Clara Webb | Ordinary | 1 | 0.3 | Warm | D | Just wants to get through the term. The term has other ideas. |
| SamPettigrew | Sam Pettigrew | Ordinary | 2 | 0.4 | Shy | A | Sits by the window in every class. Sometimes waves at nobody. |
| HenryMoss | Henry Moss | Ordinary | 3 | 0.5 | Cool | B | Runs a quiet trade in homework. Cash, snacks or secrets. |
| RonanFell | Ronan Fell | Pack | 3 | 0.8 | Wild | C | Howls at the full moon for a laugh. Mostly for a laugh. |
| KitHarrow | Kit Harrow | Pack | 2 | 0.6 | Warm | D | Loyal to the Pack first, the school second, homework a distant fifth. |
| MaeGorse | Mae Gorse | Pack | 4 | 0.9 | Sharp | A | Leads the Pack's night runs. Nobody has ever beaten her back to the dorms. |
| JaxCalloway | Jax Calloway | Delinquents | 3 | 0.8 | Wild | B | Has a detention record longer than his attendance record. Skip chance 0.2. |
| NicoRuiz | Nico Ruiz | Delinquents | 2 | 0.6 | Cool | C | Picks locks for practice. Has never been caught, which worries him. Skip chance 0.15. |
| SloaneMercer | Sloane Mercer | Delinquents | 4 | 0.7 | Sharp | D | Runs the Back Lot dice game. The house always wins; she is the house. Skip chance 0.15. |

Each set has 6 students; every clique is spread over at least three sets.

---

## 9. Differences from docs 02 and 07, and what's left out

1. **24 students**, the low end of doc 02's 24 to 40, matching doc 08.
2. **Staff mini-arcs** (doc 02 §4.6) move out of Phase 2. They're dialogue content and fit Chapter 2.
3. **The Pecking Order** (doc 02 §4.2), **clique competitions** (§4.7) and **Crisis** events (§7.3) aren't in Phase 2.
4. **Curfew's "outside your dorm wing"** is read as "in the school building outside The Dorms"; there are no
   per-player wings.
5. **Curfew covers `Forbidden` regions too** (the Staff Room and the Records Office), not only `Restricted` ones;
   `Config.Regions` already has both kinds.
6. **Notable rumours** are saved only once the Archive exists (Phase 3).
7. **Introductions** are triggered by the first conversation, not by pressing G (the player-to-player rule stays
   as it is in `Strangers`).
8. **(2.27) Field names stay `Value` and `Met`,** not `V`. The client's Factions panel and four services read them, so
   old saves need no migration; `Last` and `Flags` are added.
9. **(2.27) `Last` is `os.time()`** (real time), not the in-game day.
10. **(2.27) "Fight a rostered student" means a shove.** Players can't hit scheduled students, so a shove is the hostile
    act that's saved (-12, `Fought`). An accepted snack is the helpful one (+8 or +5, `Helped`) until 2.29's scenes.
11. **(2.27) No nameplates:** students have none. An unmet student is unnamed everywhere; a met one is in the Students
    list's Classmates group with their bio.
12. **(2.27) `Roster.Plan`, `WhereNow` and `Near`** move to the releases that use them (2.28 and 2.29).
13. **(2.27) The named cast** (`Config.Npcs`) keeps saved entries; `Config.Reputation.Npcs` still means "attacking them
    costs standing".
14. **(2.27) Shy students speak up when there's something saved to say.** Sociability under 0.5 never greeted, which
    would have left half the roster unable to introduce themselves.
15. **(2.27) The size estimate:** a full 64-entry block with every flag set is about 7.3 KB, not under 4 KB. That's still
    far under the 1 MB warning.
16. **(2.28) The Headmaster's office:** the place has no office, portrait or office area. Ashgrave keeps office hours
    beside the Records Office door during class periods.
17. **(2.28) Assemblies and crises** don't exist yet, so the Headmaster doesn't appear at them.
18. **(2.28) Staff move between posts by fading** (as 2.24's Custodian does), not by walking.
19. **(2.28) Homeroom:** sets C and D take Mr. Hale's register in Room 102, not study hall in the Library. A full room
    stands at the back.
20. **(2.28) Mr. Hale is never in the Staff Room.** He's at his Room 102 desk whenever he isn't teaching Chemistry in
    Room 103, so Orientation (which sends new students to him at any hour) always works. Sallow has no homeroom post.
21. **(2.28) Late marks name the room's timetabled teacher** for that period. Attendance is recorded as the period ends,
    often after the teacher has left the desk.
22. **(2.28) The room is found from the classroom folder's bounds,** not `Features.Regions`. Its R10x boxes sit about
    one room east of the actual rooms (logged for the owner, not changed).
23. **(2.28) Mira's empty desk is never a seat** (`Area_MiraDesk` is left out of Room 102's chairs).
24. **(2.29) "A figure at a window"** became **"a figure at the end of the main hall".** The school building has no
    windows. The figure is the existing faded-student cast template (the Strikethrough), shown for 4 seconds.
25. **(2.29) The notice board** is `NoticeBoard_143.5` in the main hall. The part tagged `NHNoticeBoard` is the Midnight
    Bell board.
26. **(2.29) The two night scenes run at dusk** (the Evening segment). Every student has gone home by Night, so a Night
    scene could never be cast.
27. **(2.29) The moon emitter** listens to `MoonPhases`' `NHMoonEvent` attribute rather than editing `MoonPhases`.
28. **(2.29) Witnesses** are rostered students within 40 studs, not "in the region". The `workspace.Regions` boxes
    don't line up with this place's rooms, so `Incidents.RegionAt` reads them the way Fortune does, and each scene
    names its own place.
29. **(2.29) A rumour holding a player never changes at all.** That's stricter than "only NPC fields may change": it's
    the simplest form of the rule that a test can prove (10,000 hops, 0 broken).
30. **(2.29) Learning a name from a rumour** uses `Reputation.Learn` (met, value unchanged), only for students who fell
    out with you before an introduction.
31. **(2.29) A rumour's life** is one in-game day: 7,200 real seconds at the clock's 300 seconds per game hour.
32. **(2.29) Argument casts a rival pair on purpose:** its second student comes from the first one's rival clique.
33. **(2.30) No PA speakers on the hall props.** The PA is a chime and a typed line on the ClockHud, within the kit-only
    art rule; a speaker prop needs art.
34. **(2.30) The station's sound** is the owner's voice clips (host, hall monitors, PSA, lore), played when you tune
    in, not a continuous audio bed. Players' own tracks keep playing underneath, ducked.
35. **(2.30) Curfew's patrol** walks the hall monitor's existing indoor route. The Records Office keeps its own night
    watcher (the Night Custodian, Stealth). The restricted outdoor areas (Graveyard, Boiler Yard) aren't patrolled:
    they aren't "in the building", so they aren't after hours under this rule.
36. **(2.30) "In the building"** is HallMonitor's `OnCampus` (rooms and hallways), since the Regions boxes don't line
    up. This place has no Dorms box; the real dorms are instanced homes, outside the building anyway.
37. **(2.30) Confiscation on a curfew catch** uses the existing contraband rule (brass knuckles). There's no new
    "carried for the night" rule.
38. **(2.30) The phone's "monitors on their rounds" line** no longer exists (2.22 removed it), so there's nothing to
    make true.
39. **(2.30) "A match tonight" and "an assembly"** are announced only when those systems report one. There's no
    assembly system yet.
40. **(2.30) Night FM was remade** at the owner's request: home, library, now playing and station in
    `Controllers.Gui.PhoneRadio`, in PBR art of its own. Liked tracks are saved per slot (`Phone.Liked`, 30 at most).
