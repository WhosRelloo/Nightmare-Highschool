# Implementation Status: NH Combat Test

Last updated: 2026-10-29. Done: Milestone 0, a combat pass (`Combat-System.md`), clock and timetable (`School-Simulation.md`), attendance and discipline (`Attendance-and-Discipline.md`), class activities (`Class-Activities.md`), and factions and reputation (`Factions-and-Reputation.md`).

How each result was checked:
- **[PT]** Studio playtest
- **[PT-real]** playtest using real keyboard or mouse input
- **[CR]** code review only

## Done this session

| Change | Where | Verified |
|---|---|---|
| Fixed mouse keybinds (M1, Feint) after Roblox renamed `KeyCode.Unknown` to `None` | `ReplicatedStorage.Packages.Bind.Keybinds` | **[PT-real]** M1 combo 1→4, damage lands |
| Keybind callback errors now `warn` the real message | same | [CR] |
| Moved 7 inert duplicate dummies out of `workspace.Live` | `ServerStorage._InertLiveDummies_Backup` | [PT] Live now holds only the working dummies at play time |
| Added Studio-only test bridge | `ServerScriptService.Services.Studio.TestBridge` → `ServerStorage.NHTestBridge` | [PT] used for every NPC test below |
| Audit docs | `Docs/Project-Audit.md`, this file | n/a |
| **AI stunlock fix**: NPCs cap attack strings and back off on long stuns, then give a free window | `AI.NPCController` (Stunlock guard), `Config.NPC` | [PT] player stunned 52% of the time (was 80%), longest chain 2.3 s |
| **AI death handling**: state `Dead`, leaves the active list, `AI.NPCDefeated(npc, killer)`, corpse removed after 4 s, optional respawn | `AI.AI`, `Config.NPC` | [PT] |
| **AI Agro tag leak fixed**, and NPCs ignore downed targets | `AI.NPCController` | [PT] |
| **Posture breaks on the hit that fills the bar** (it used to break one hit late), and **posture now regenerates**: 2.5 s delay, then 12/s, halved while blocking | `DamageLogic`, `Features.Posture`, `Config.Combat` | [PT] 90 + one hit breaks the guard; drains at 6/s while blocking |
| **Generic `Action` remote locked** behind an empty allow-list, and Dodge checks its direction before granting i-frames. Sprint/Block also accept only `Activate`/`Release`. | `ActionManager`, `Movement.Dodge` | [PT] forged `Action("Dodge")` and `Action("Template")` reach the server and are ignored. A real Q dodge still works. |
| **Kills saved**: `Kills` (players) and `NPCKills` are added to player data, plus a Kills leaderboard column. Grip executions count. | `PlayerData`, `Functions.UpdateState`, `Player.Data`, `Features.KillTracker` | [PT-real] a B grip took NPCKills 0→1, and it survived a session restart |
| **Quests, investigation, stealth, duels**: framework, a provisional Chapter 1 (3 main quests: New Kid → The Empty Desk investigation → After Hours stealth), 5 side quests (delivery, lost item, champion, PvP duel, Answer Key heist), evidence board, watchers and lockers, duel ring, Journal (J) and tracker using the NH UI kit. Every location is found by part attributes, so it moves to the real map. | `Config.Quests/Cases/Stealth/Npcs`, `ServerStorage.QuestSecrets`, `Services.Quests.*`, `Gui.QuestJournal`, `Gui.QuestTracker`, `workspace.School.Quests` (temp) | **[PT]** every quest end to end, plus [PT-real] E pickup, J and the journal tab click. 4 bugs found and fixed. PvP was tested with a dummy as the 2nd fighter. See Quests-and-Investigation.md. |
| **Factions and reputation** (Nightmare Highschool theme): The Vigil (Ezra Vale, Library Archive) and The Crimson Court (Vesper Crane, Boiler Yard), with ranks, initiation, rivalry, perks, missions, titles, 4 reputation scores, saved leader relationships, server dialogue, Night Study, wall marking with witnesses, and the Factions panel (P) | `Config.Factions`, `Config.Reputation`, `Services.Social.*`, `ServerStorage.Dialogue.*`, `Gui.Dialogue`, `Gui.FactionsPanel`, `workspace.School.{Archive, BoilerYard, MarkWalls}` | **[PT]**, plus [PT-real] key 2 in dialogue, P for the panel, and a title-button click. Both faction loops, every perk, the Court mission, the witness paths and the attack penalty. 5 bugs found and fixed (see Factions-and-Reputation.md). |
| **Class activities**: Pop Quiz (math), Lab Mix rhythm (chemistry), Word Scramble (English), Match the Past memory (history), on a chalkboard UI with a grade stamp, class levels 1–5, Yen, and the grade on the attendance record | `Config.Activities`, `ServerStorage.Activities.*`, `School.Activities`, `Gui.Activities.*` | **[PT-real]** all 4 games graded end to end (B, A+, A+, A+ runs), plus rewards and level-ups, fail and retry, practice, leaving the room, the bell, and the attendance grade. Two Lab Mix timing bugs were found and fixed (see Class-Activities.md). |
| **Discipline ladder** (Clear → Warning → Detention → Probation → Suspension) with saved record, recovery and daily decay | `Config.Discipline`, `School.Discipline`, `PlayerData.Discipline` | [PT] full ladder up and back down |
| **Witness rules** (only recognized suspects are punished) and **fight reporting** | `Discipline.ReportIncident`, `Downed.OnDamage` | [PT] |
| **Hall monitor NPC**: patrol, spot, chase, catch or escape, let go on entering class, investigate distant fights, unstick logic | `School.HallMonitor`, `workspace.School.PatrolRoute` | [PT] all paths |
| **Detention**: Room 106, collect trash with E and use the bin; walking out is a violation; the bell pauses it | `School.Detention`, `workspace.School.R106` | [PT-real] key presses; walk-out and bell [PT] |
| **Attendance**: five temporary classrooms; Present/Tardy/Left Early/Absent/Excused saved per class period; Yen rewards; streaks; a HUD class line and door marker | `workspace.School`, `Config.Classes`, `School.Attendance`, `PlayerData.Attendance`, `Gui.ClockHud` | [PT] all 5 outcomes, duplicate guard, persistence and the rejoin case (see Attendance-and-Discipline.md) |
| **Global clock**: every server shares one in-game time | `Config.SchoolSchedule.ClockMode` | [PT] |
| **Notifications**: server `Notify(Player, …)` and client toasts | `Features.Notifications`, `Gui.Notifications`, `Packets.Notify` | [PT] the toast appears after a rejoin (screenshot) |
| **School clock and HUD clock** | `Config.SchoolSchedule`, `Functions.SchoolTime`, `School.SchoolClock`, `Gui.ClockHud` | [PT] see School-Simulation.md |
| **Downed / Carry (V) / Grip (B)** with your crawl, idle and Katana grip animations | `Features.Downed`, `Config.Downed`, DamageLogic, Burn, ActionManager, StateManager, Packets, input modules, `Gui.DownedHud` | **[PT-real]** V, B and the crawl with real keys. [PT] everything else (see Combat-System.md). |

Nothing was changed in the production place.

## Verified working [PT]

- **Player combat:**
  - Equip (E) **[PT-real]**
  - M1 4-hit combo **[PT-real]**
  - Knockback and stun
  - Respawn re-initializes the character: it goes to Live, the weapon is on its back, collision group is `Entity`, and equipping works.
- **Dummies:** Parry, Attacking, ParryTrade, Blocking, PostureBreak, and Inf Dummy all behave as designed.
- **AI NPC:**
  - targets the nearest player
  - chases and slides in
  - uses M1, M2 (posture break), and Uppercut (launch)
  - takes damage
  - drops the target beyond 100 studs
- **Persistence:** the profile loads and leaderstats (Yen) are created.

## Known bugs (prioritized)

**Combat and NPC issues, fix first. These affect playtesting today:**

1. ~~The AI stunlocks players.~~ **Fixed.** The player is now stunned about 52% of the time, down from 80%. The limits are tunable in `Config.NPC`. [PT]
2. ~~AI death is not handled.~~ **Fixed.** Dead NPCs now leave the active list, fire `NPCDefeated` with the killer, and their corpse is removed. Respawn is optional. [PT]
3. **Players have no defeat handling.** *Partly fixed:* the downed state, the grip execute with kill credit, and `Downed.OnDefeated` are in. There is still no health regen outside of recovering from downed (the default Health script is deleted), and kills aren't saved to player data yet. [PT]
4. ~~The Blocking posture break lands one hit late, and posture never regenerates.~~ **Fixed.** [PT]
5. ~~The AI `Agro` tag grows without limit.~~ **Fixed.** There is now one tag per target, and a dead or downed owner frees it. [PT]
6. **AI pathfinding is unused.** NPCs move in straight lines and cannot route around walls. They have no return-home behaviour. [CR, PT]
7. **TrackService never frees tracks.** Every `Play` loads and keeps a track for the life of the character, and long-lived dummies may hit the animator's track limit. [CR]
8. **Aerial M2 has no effective cooldown** because it uses the wrong cooldown key. [CR]
9. **Studio dummy loops never end.** `while Humanoid.Health >= 0` stays true after death. One `return` inside the setup loop also aborts every remaining dummy. [CR]
10. **`EntityLoader.OnStart` can miss respawns.** It sets up characters of players already in the game but never connects `CharacterAdded` for them, so a player who joins before it starts misses respawn setup. Respawn worked in Studio. [CR]

**Security (server trusts the client). All from code review, not exploit-tested:**

11. ~~The `UnPackets.Sprint` and `Block` handlers call `ActionManager[State]` with a string from the client.~~ **False positive.** `Packet.Actions` only encodes `Activate` or `Release`. The handlers now also check this explicitly.
12. ~~`UnPackets.Action` lets a client activate any action module by name (free i-frames, the no-cooldown Template skill).~~ **Fixed** with an allow-list. Dodge also validates its direction now. [PT]
13. **Block and Sprint press/release travel over unreliable remotes.** A dropped release can leave block or sprint stuck on.
14. **No remote has rate limits or distance checks.** Reach depends on the client-owned character position.

**Tooling:**

15. **Cmdr admin is unusable for the developer.** It is restricted to hard-coded IDs (4283953723, 1219061975, 3585755651), and the developer account (37484441) isn't one of them.

## Dead or incomplete content (kept, not deleted)

- **Vows (Fists, Flames).** Activation is commented out, and both need a `Hands` weapon type that doesn't exist.
- **M2 assets for Fist, LongSword, Trident.** No weapon config exists for them.
- **Missing mechanics.** Ragdoll never happens. Perfect-dodge gives no reward. `AirWeld` is unused.
- **Empty or unused modules.** `GuiController` and `SkillController` are empty, and `Services.AI.Spawn` is commented out.

## Not started (from the master prompt and the concept doc)

- ~~School simulation~~ **Done** (clock, timetable, classes, attendance, discipline, detention, hall monitors). Still to do: NPC schedules and a timetable UI.
- ~~Social systems~~ **Done** for two factions. Still to do: The Ordinary and The Hollow (rumoured only), and relationships with ordinary students.
- **Content systems:** inventory, personal lockers, clubs, jobs, events. *Done:* dialogue, quests, investigation, stealth, duels.
- **Progression from the concept doc:** races, classes, EXP and levels
- **UI:** HUD, timetable UI, quest journal, notifications, settings
- **Input:** mobile and gamepad controls
- **World:** school map. The place is currently a flat baseplate.

## Downed / Carry / Grip: open items

- **Carry animations wired in.** Carry and Carried both play, and the body rests on the left shoulder. The offset was tuned with still screenshots only; check it in motion and adjust `Config.Downed.CarryOffset` if needed.
- **Grip animations:** only Katana has a grip pair. Other weapons fall back to Katana. The victim's position relative to the gripper is set by `Config.Downed.GripVictimOffset`; adjust it if the animations don't line up.
- **No mobile buttons for V/B.** This matches the rest of combat, which has no touch input yet.
- **Not tested with two real players** (one carrying or gripping the other), or with a disconnect while being carried.

## Next recommended work

1. ~~Milestone 4: attendance~~ **Done.**
2. ~~Discipline, hall monitor, detention~~ **Done.** See Attendance-and-Discipline.md.
3. ~~Milestone 5, class activities~~ **Done**: 4 minigames.
3. ~~Factions and reputation~~ **Done.**
3. **Next options:**
   - quests and investigation (they can reuse the dialogue engine)
   - the nightmare systems
   - two-player testing of everything so far
4. ~~Decision needed: the interaction key~~ **Decided: E**, with `Config.Interaction` as the shared setting. E is context-sensitive: it interacts while a prompt is showing and equips otherwise. [PT-real]
4. **Shared foundation**, still to do: a NotificationService and toast UI, a unified InteractionService built on ProximityPrompts, and EXP and level data (the school-hours 1.2× hook is ready in `SchoolClock.GetExpMultiplier()`).

## Decisions needed from the developer

- **Stunlock fix approach:** slower AI attacks, or a stun-immunity window after a stun ends.
- **School-hours length:** 4 in-game hours, or 10% of the day as the doc says. The two numbers disagree.
- **Admin access:** add the developer account (37484441) to `Config.Cmdr`?
- **Whether the docs should live in the GitHub repo**, which is currently empty.
