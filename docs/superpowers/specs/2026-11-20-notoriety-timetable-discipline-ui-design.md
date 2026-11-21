# The Bell Tower: notoriety, timetable, discipline and quest HUD (design)

**Status:** design approved in chat on 2026-11-20 (direction A, Sections 1 and 2). This written spec is waiting for the owner's
review. No game code has been written.
**R1 status:** R1 built in 2.36.0 (plan `docs/superpowers/plans/2026-11-20-belltower-r1-cluster.md`). The art ids in
`Config.BellTowerArt` are not filled yet, so R1 runs on the kit fallbacks until the owner's 9 ids are pasted in.
**Spec delta:** ClockHud and QuestTracker were rebuilt in place instead of getting a new `Controllers.Gui.BellTower`,
because Timetable, Moments, TouchControls, SchoolFx and GamepadControls depend on their instance names (see the plan's
Architecture).
**Mockups:** <https://claude.ai/artifact/NiejF4HWaeEze5GzdBNsbF> (source:
`docs/superpowers/mockups/2026-11-20-belltower/index.html`).
**Concept art:** `art/ui/hud/make_belltower.py` writes the set to `art/ui/hud/out/belltower/`. It's baked with the Thornrose
shader (`make_health_pbr.py`).
**Owner's decisions (2026-11-20):**
- new baked art (not a reskin), direction **A, the Bell Tower**, with new art for the whole wanted UI
- notoriety is **a live heat layer over the Discipline record**, not a replacement for it
- witnesses are **staff, prefects (hall monitors) and students**
- witnesses keep **monster-themed notes** of what they know

---

## 1. What GTA 6 does (research)

GTA VI launched on 19 Nov 2026. Rockstar has not published how the system works inside. The claims below are
graded by source.

| Claim | Grade | Source |
|---|---|---|
| Police respond only when "someone witness[es] the crime, or an alarm" goes off | **Rockstar** (Rob Nelson, via IGN's demo) | [Engadget, 19 Nov 2026](https://www.engadget.com/2322564/gta-6-wanted-level-star-system-details/) |
| "Our dispatch is extremely specific in what it knows" | **Rockstar** (Nelson) | same; [Newsweek](https://www.newsweek.com/gta-6s-new-police-system-ends-the-easy-getaway-with-flock-like-cameras-12743394) |
| Six-star wanted level | **Rockstar footage** (Aug 2026 Extended Look) | [GTA Intel](https://gtaintel.com/news/gta-6-wanted-system-what-we-expect) |
| What police know ("heat") outlasts the stars. You shed it by changing clothes, covering your face, or ditching or torching the car | **Rockstar footage** | GTA Intel |
| Star states: hollow (they don't know who), grey (partial description), solid white (in sight), flashing (sight lost), red (lost them, they'll re-engage if they recognise you) | **Hands-on press**. The outlets **disagree** on the colours | Engadget (19 Nov, relaying GameSpot); [Engadget, 18 Nov](https://www.engadget.com/2320983/gta-6s-cops-will-remember-you-thanks-to-the-heat-system/); Newsweek |
| Icons under the stars for camera, accomplice, outfit, face, weapon and vehicle. More icons means you're easier to identify | **Hands-on press** | Engadget, 18 Nov |
| Area heat: repeated crimes in an area bring more patrols, the area shows as "Hot" on the map, and it cools over time | **Hands-on press** | Engadget, 18 Nov |
| No police blips on the minimap | **Footage and press** | GTA Intel; Engadget |
| Civilians call 911. Hurting civilians lowers a separate Criminal Profile | **Press, unattributed** | Newsweek |
| Search circles (red at 1 to 5 stars, the whole map at 6) | **One creator's preview, unconfirmed** | GTA Intel |
| A traffic-camera plate reader | **Leaked footage, speculation** | Newsweek |
| Cooldown timings, how many stars each crime earns, and what each tier sends | **Unpublished** | |

**What we take from it:**
1. A misdeed only matters if it's **witnessed**.
2. The system tracks **what witnesses know** separately from **how hot things are**.
3. The stars change **state** as well as count.
4. Area heat outlasts the chase.
5. Searchers are **not** drawn on the map.

**What we leave out:** cameras, vehicles, and any reputation hit for hurting civilians. The school already has
Reputation and Paths for that.

## 2. Today (read before changing anything)

| Piece | Where | Today |
|---|---|---|
| Clock | `Services.School.SchoolClock`, `Functions.SchoolTime`, `Config.SchoolSchedule` | Global clock: 1 in-game minute is 5 s. The segments are in `School-Simulation.md`. Curfew runs 22:00 to 06:00 (2.30). |
| Timetable | `Config.Classes.Periods`, `Controllers.Gui.Timetable` (click the clock) | A list of the day's segments, with attendance and any detention owed |
| HUD | `Controllers.Gui.ClockHud`, `Controllers.Gui.QuestTracker` | The owner's screenshot: an ornate moon and time panel with a fifth line for discipline in orange, and a quest card with "[J] Journal" at `TextSmall` (**18 px**, below the house minimum of 20) |
| Discipline | `Services.School.Discipline`, `Config.Discipline` | The ladder (Clear, Warning 2, Detention 5, Probation 10, Suspension 16), violations, decay, detentions owed (capped at 3). `ReportIncident({Type, Suspect, Witness, Position, Recognized})`: **only a recognised suspect is punished.** |
| Witnesses | `HallMonitor` (day monitor, `NightDuty`), teachers at their desks (2.28), the Night Custodian | Each one either books a violation or chases |
| Stealth | `Quests.Stealth`, `Config.Stealth`, `AI.Senses`, `Controllers.World.Spotted` | A detection meter in quest zones, with a crouch multiplier, lockers, and the "?"/"!" and Spotted effects |
| Incidents and rumours | `World.Incidents` (the bus), `Social.Rumours`, `World.Broadcast` | Emitters go into the bus. Its consumers are Reputation, Discipline and Rumours. A rumour about a real player carries only true facts. |
| Roster and memory | `Social.Roster`, `Social.Reputation`, `AI.StudentBrain` | 24 named students and their saved relationships |
| UI kit | `ReplicatedStorage.UI.Components`, `Theme` | The rules are in `UI-Kit.md`. Fonts: Fantasy for titles, Garamond for body. |

## 3. The "Noticed" system: the Bells

### 3.1 Architecture
- **A new server service, `ServerScriptService.Services.School.Notoriety`.**
  - It owns each player's **Heat** (0 to 100), **Bells** (0 to 5), **bell state**, **notes**, **search** and
    **pending reports**.
  - It plugs into the existing bus. It listens on `Incidents.On(...)`, and the existing emitters raise misdeeds
    there. It writes the record only through `Discipline.ReportIncident` / `AddViolation`.
  - It never edits Discipline's ladder or its numbers.
- **Config:** `ReplicatedStorage.Config.Notoriety` holds every number in this section, for tuning.
- **The client reads attributes only:**

  | Attribute | Values |
  |---|---|
  | `NHBells` | 0 to 5 |
  | `NHBellState` | `Hollow`, `Tarnished`, `Lit`, `Search` |
  | `NHNotes` | a comma list of note kinds |
  | `NHSearchWhere` | the region name |
  | `NHReportBy` | the witness's name while a student is on their way to report |

  Watched wings are a `ReplicatedStorage.Notoriety` folder of region attributes.
- **Signals:** `Notoriety.Changed(player, bells, state)`, `Notoriety.Caught(player, tier)`,
  `Notoriety.Escaped(player, identified)`.

```
Emitters ─> Incidents.Emit(misdeed) ─> Notoriety.Witness (who saw it, what they saw)
   staff / monitor ──────────────> Heat + notes, report at once
   student ─> snitch roll ─> walks to staff ─(intercepted?)─> report
Notoriety ─> HallMonitor / NightDuty / Custodian (investigate, hunt, converge)
Caught + identified ─> Discipline.ReportIncident (Recognized = true, tier bonus)
Escaped + identified ─> Summons slip (Discipline detention owed / office)
Escaped, unidentified ─> logged, Recognized = false (as today)
```

### 3.2 Misdeeds (Heat added when witnessed)
| Misdeed | Source (existing) | Heat |
|---|---|---|
| Out of class in a class period | `HallMonitor` truancy sight, `Attendance` | 12 |
| Trespassing (forbidden or restricted region, after curfew) | 2.30 curfew, 2.8.1 suspension | 20 |
| Fighting a student | combat hit seen | 25 |
| Pranks and paint | `Cliques` prank | 15 |
| Transforming, or feeding, in sight of anyone who isn't in on it | `Transformation` attribute, Hunger | 30 |
| Hitting staff, or downing a monitor | combat on a staff NPC | 45 |
| Gripping or downing a witness | combat on the reporting student | 35, plus a new witness check |

- **Night:** from 22:00 to 06:00, Heat gained is ×1.5 ("one step faster").
- **Probation:** Heat gained is ×1.25.
- **Combat-allowed areas** (`CombatAllowed` tag) add nothing.

### 3.3 The five Bells
| Bell | Heat | Name | What the school does |
|---|---|---|---|
| 1 | 10+ | **Murmur** | The nearest on-duty staff member walks to the spot to look. |
| 2 | 25+ | **Noticed** | Your description circulates. Staff and monitors in that region **recognise you on sight** if your notes match (see §3.5). |
| 3 | 45+ | **Named** | One monitor is sent to hunt you, using today's chase code. |
| 4 | 70+ | **Hunted** | Every on-duty monitor, plus the Custodian at night, converges on the search ring. The PA calls "a disturbance" (`Broadcast`, at most once per period). |
| 5 | 90+ | **The Tolling** | Headmaster Ashgrave is involved. The search covers the whole campus, and there's a PA announcement. It ends only when you're caught, reach the Dorms, or leave campus. |

### 3.4 Bell state and cooling
- **States:**
  - **Hollow:** nobody knows who you are (no identifying notes).
  - **Tarnished:** there's a partial description (notes, but not identified).
  - **Lit:** a staff member or monitor can see you, by `AI.Senses` line of sight.
  - **Search:** line of sight was broken less than 30 s ago. Searchers sweep from your last-seen point.
- **Cooling (per real second; none while Lit):**
  - Search: −1.5. After 30 s unseen the search ends, the state becomes Hollow or Tarnished, and cooling is −3.
  - Lockers, the Dorms, and off campus: ×2.
  - **Alibi:** being in your timetable's room during a class (`ClassInRoom`), or in Room 106 serving detention: ×3.
- **The search area** is a ring around the last-seen point. Its radius grows with time unseen, from 30 to 120 studs.
  The ring is shown on the map as candles; searchers are never shown.
- **Ending:** at Heat 0 the Bells clear. Notes stay as described in §3.5.

### 3.5 Witness notes (what they know)
| Note | Learned when | Shed by |
|---|---|---|
| **Face** | seen within 25 studs, or while Lit for 2 s or more | can't be shed; it fades **1 in-game day** after the last sighting (saved) |
| **Outfit** | any sighting | changing top or uniform at a wardrobe, locker or the Dorms |
| **Form** | seen transformed | reverting your form, then 20 s unseen |
| **Clique** | seen wearing clique colours (the dress code) | changing out of the colours |
| **Weapon** | seen holding a weapon tool | unequip it, then 20 s unseen |
| **Companion** | seen with a party member | 20 s more than 40 studs from them |

- **Identified** means Face is known, or 3 or more other notes are known. Only an identified player can be
  booked, which keeps today's `Recognized` rule.
- Notes belong to the school (server-wide), not to one witness. Everyone on duty knows what anyone on duty
  reported.

### 3.6 Student witnesses and the report on its way
- **Students** within sight roll to snitch:
  - **Base chance by clique** (`Config.Notoriety.Snitch`): Vigil-leaning 0.5, Ordinary 0.35, Court 0.25,
    Delinquents 0.05.
  - **Scaled by your relationship** (`Reputation`): friends 0.3×, rivals 1.5×.
  - Your own clique never reports you.
- **A snitch walks** to the nearest staff member (`Roster`) and has at most 60 s to get there. `NHReportBy`
  shows their name, so the HUD can say *"Odette Marsh is going to tell Mr. Hale"*, with a waypoint.
- **Heading them off:**
  - **Talk:** the `Talk.Attitude` check.
  - **Pay:** ¥10 per Bell.
  - **Lean on them:** needs clique standing Tier 2 or more.

  Each of these writes a `Reputation` flag. Gripping or downing the snitch is a new misdeed, witnessed by
  whoever saw it.
- **If the report lands,** its notes and Heat are applied, with the witness's name.
- **Rumours** still come from the incident, and the true-facts safety rule doesn't change.

### 3.7 Watched wings (area heat)
- **What feeds it:** each region keeps a Watch score from the misdeeds witnessed in it.
- **Watched:** at 40 or more, the region is **Watched** for **2 in-game hours**.
  - Monitor routes are weighted towards it.
  - Awareness range there is ×1.25.
  - It shows as a crimson hatch on the map and in the Almanac.
- **Server-wide**, not saved.

### 3.8 Into the record (Discipline)
- **Caught while identified:**
  - The misdeed's existing violation (Truancy, Fighting, Trespassing, and so on), plus a **tier bonus**: Bell 3
    +1, Bell 4 +2, Bell 5 +3.
  - The witness is the catcher, or the first reporter.
  - HallMonitor's existing confiscation still applies.
- **Escaped but identified:**
  - A **Summons** slip arrives at the next period change.
  - To serve it, report to the Headmaster's office within 1 in-game day. The misdeed is booked **without** the tier
    bonus, which is the reward for turning yourself in.
  - Ignoring it is **Skipped Detention** (+4), as today.
  - Saved as `PlayerData.Notoriety.Summons` (at most 3).
- **Escaped and unidentified:** logged with `Recognized = false`. Nothing is booked.
- **Exempt:**
  - story stages and cutscenes (as curfew already is)
  - quest stealth zones, which keep their own meter and rewind (`Quests.Stealth`), so nothing is punished twice
  - Suspension, where today's held-points rule applies

## 4. The HUD: the Bell Tower cluster

**The house rules apply throughout:**
- no text under 20 design px
- no plain grey frames and no default prompts (the kit's `PromptUi` stays)
- every state is shown by shape or words as well as colour

**Layout:** top-right, 470 design px wide, stacked top to bottom. The new controller is `Controllers.Gui.BellTower`.
It replaces the visuals of `ClockHud` and `QuestTracker`. Their public functions and attributes are kept, as every
kit reskin does.

1. **The Dial** (176 px).
   - **Art:** `Dial` + `DialHand` + the existing moon icons in the window.
   - **Rim:** today's timetable, baked from `Config.SchoolSchedule`: crimson enamel for class periods, brass for
     breaks, blackened iron with stars for curfew. Midnight is at the bottom and noon at the top.
   - **Hand:** turns smoothly to now. Reduce Motion makes it step once a minute.
   - **Text** on a `TowerPlate`, to the left of the dial:
     - day and time, title font, 28 px
     - the segment and when it ends, with the moon, 20 px
     - a **Now** line, 20 px. It's gold normally, amber for warnings (*NOT IN CLASS*, *Curfew: dorms only*,
       *Suspended: stay off campus*) and gold for the alibi hint.
   - **Clicking it** opens the Almanac.
   - **If the timetable changes,** the rim must be rebaked; §8 records this as a limit.
2. **The Bell Rail** (shown only while Bells are 1 or more).
   - **Arrival:** `BellRail` swings in from the right edge. Each new Bell drops onto its hook with one toll.
   - **Bell art by state:** `BellHollow`, `BellTarnished`, `BellLit` (with a `BellGlow` tinted Gold). In the
     Search state, the bells swing ±9° and dim on each beat.
   - **Notes:** a row of tokens (`NoteFace`, `NoteOutfit`, `NoteForm`, `NoteClique`, `NoteWeapon`,
     `NoteCompanion`), 44 px each. A note that isn't known isn't drawn.
   - **Status line, 20 px:** the tier name in crimson, then the detail (*"Searching · last seen: the Library ·
     0:42"*). A second amber line shows a report on its way.
3. **The Conduct Seal.**
   - **Art:** `Seal` (greyscale, tinted per level: Warning amber, Detention crimson, Probation deep crimson);
     `SealBroken` for Suspension.
   - **Text, 22 px:** the level and points.
   - **Slips:** each owed detention or summons is a `Slip`, 20 px text (*"Detention owed · Room 106, after class"*).
   - **Hidden** while you're Clear and owe nothing.
   - **Clicking it** opens the Conduct Ledger.
   - It replaces today's orange fifth line.
4. **The Lead Card.**
   - **Art:** `LeadCard` (parchment in a brass hinge clip, with a crimson ribbon).
   - **Text:** the title at 24 px, the objective at 20 px.
   - **Progress:** `PipEmpty` / `PipFang`, with the count at 20 px.
   - **The Journal key:** a kit key-cap with **J Journal** at 20 px. Today's "[J] Journal" is 18 px.
   - **Folding:** while Bells are 1 or more, it folds to its title line.

**Sound:**
- **The toll:** the existing desk-bell or school-bell audio, pitched down per tier.
- **The Search beat:** a soft ticking.
- **Mixing:** both go through `NH_Effects`.

**Phone:**
- The cluster scales through `AutoScale`, and the dial drops to 140 px.
- The notes row wraps under the bells.
- Text stays at 20 design px or more, so the kit's phone scale floor (`PhoneTouchMin`) still decides how big that
  is on screen.
- Every tappable target is at least 44 px.

**Accessibility:**
- **`NHReducedMotion`:** no swing, toll shake or hand sweep.
- **`NHReducedFlash`:** no glow pulse.
- **Words always change with state** (Murmur, Noticed, Named, Hunted, the Tolling, Searching).
- `Controllers.World.Spotted` keeps its world effects, and its "?"/"!" now follow `NHBellState`.

## 5. The full-screen views
All four use the same art family and the kit's `Panel`/`Decorate` rules. The frames are `TowerPlate` 9-slices with a
title plaque.

| View | Opened by | Contents |
|---|---|---|
| **The Almanac** (replaces the visuals of `Gui.Timetable`) | clicking the dial; gamepad menu "Timetable" | **Left:** the big dial (600 px) with the hand at now. **Right:** Now / Next / Tomorrow; **Today**, each period with its attendance stamp (Present, Tardy, Absent, from `Attendance.Recent`); **Owed** (detention, summons); **Coming nights**, the next 7 nights' moons (full, crimson, blue) with the quests they unlock; **Watched wings tonight**. |
| **The Conduct Ledger** (new) | clicking the seal; a button on the Record's (M) Conduct tab | The ladder as five seals on a brass rail with the current one enlarged; points and the next threshold; the decay forecast (*"Clear in 2 days if you keep your head down"*, from the existing decay rules); slips owed (click one to set its waypoint); recent entries on parchment, each with its points and witness (*"Reported by Odette Marsh to Mr. Hale"*), including unidentified incidents that booked nothing. |
| **The Journal** (reskins `Gui.QuestJournal`) | J; the phone | The tracked lead as a large Lead Card; the other leads as folded cards in a rack, each with a Track button. |
| **The map layer** (on the existing map) | the map | Watched wings in a crimson hatch with the time left; the search ring as candles (`Candle`), some guttering out as the search shrinks; your marker. Searchers are never drawn. |

## 6. Art (new bake, direction A)
`art/ui/hud/make_belltower.py`, using the same GGX shader and the school's Brass, Iron and Paper materials as
Thornrose. The concept versions are baked. Before upload, the final versions need a 2x quality pass: a crown finial on
the dial, numerals on the rim, and the Face token's mask silhouette.

| Piece | Size | Tinted in game |
|---|---|---|
| `Dial`, `DialHand` | 640 | no |
| `BellHollow`, `BellTarnished`, `BellLit` | 256 | no |
| `BellGlow` | 256 | yes (Gold) |
| `BellRail` | 1400 x 220 | no |
| `NoteFace` / `NoteOutfit` / `NoteForm` / `NoteClique` / `NoteWeapon` / `NoteCompanion` | 200 | no |
| `Seal`, `SealBroken` | 256 | yes (per level) |
| `Slip` | 420 x 150 | no |
| `LeadCard` | 1000 x 300 | no |
| `PipEmpty`, `PipFang` | 96 | no |
| `TowerPlate` (9-slice, centre 60..540 x 60..140) | 600 x 200 | no |
| `Candle` | 128 x 192 | no |

The ids go in a new `Config.BellTowerArt` (the pattern of `Config.HeatArt`). If an id is missing, today's kit panel
draws instead, so nothing breaks before upload.

## 7. Releases (each one playable and tested before the next)
| Release | Builds | Acceptance |
|---|---|---|
| **R1 · The cluster** | art upload; `BellTower` controller with the Dial, Conduct Seal and Lead Card; no new rules | The screenshot's information, same sources, new art; no text under 20 px (fit check); phone layout |
| **R2 · Bells** | `Notoriety` service, staff and monitor witnesses, the five tiers, the four states, search and cooling, alibi, Discipline hookup, summons | `NotorietyTest`: a fight seen by a monitor raises Heat and Bells; escaping unidentified books nothing; caught while identified books the violation plus the tier bonus; an alibi cools ×3; a curfew trespass gains ×1.5 |
| **R3 · Witnesses** | notes and shedding, student snitches, the report on its way and heading it off, the Spotted hookup | Each note is learned and shed by its rule; a Delinquent witness almost never reports; heading off a snitch stops the report; `RumourSafetyTest` still passes |
| **R4 · The views** | the Almanac, Conduct Ledger and Journal reskins, the map layer, watched wings | Each view's numbers match their source; a watched wing expires after 2 in-game hours |

Testing follows the repo's existing practice: single-player Studio runs with the clock sped up, plus scripted tests
through the test bridge. A two-player run is needed before R3 ships, because snitches choosing between players and
shared notes haven't been tested with two players.

## 8. Limits and open questions
- **The baked rim:** the Dial's rim is today's fixed schedule. Per-student timetables or a changed schedule would mean
  rebaking it, or drawing the arcs as separate rotated segments. **Recommendation:** keep it baked until the schedule
  changes.
- **Tuning:** every number in §3 is a first guess. They're in `Config.Notoriety` so they can be tuned in playtests.
- **The Tolling (Bell 5):** in this design the Headmaster joins only as a PA voice and a campus-wide search.
  Giving him a body in the chase is out of scope.
- **Prefects:** in this design the existing hall monitors and night-duty monitors are the "prefects". Student prefects
  from the roster would be a later addition.

## 9. Not in this design
- security cameras and alarms; the closest is the Records Office "alarm" stage of After Hours, which keeps its own
  rules
- vehicles
- a Criminal Profile; Paths and Reputation already cover standing
- any change to the Discipline ladder's thresholds, decay or detention rules
