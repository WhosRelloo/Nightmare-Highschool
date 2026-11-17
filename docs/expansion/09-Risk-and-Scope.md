# 09. Risk and Scope Report

## 1. Conflicts with existing functionality (stopped and documented, not changed)

| Conflict | Detail | Proposal |
|---|---|---|
| "Evolution" name | Already means the race tier-up (`Player.Evolution`, `NHEvolve`) | Call the new feature **Standing Paths** |
| "Student Record" / "Report Card" | The L panel and the weekly phone card | L panel becomes **Permanent Record**; "Report Card" stays the weekly card |
| Five standing systems | Reputation, Factions, Cliques, Relationships, Sports ClubExp | No new bar; paths and the hierarchy are derived from these |
| `Social` block writers | Fortune and `Cliques.Add` write outside `Reputation.Sync` | Fix in Phase 0 before relationships grow |
| Talk shot camera | Bypasses `CameraLease` | Fix in Phase 0; Cine depends on the lease |
| Night windows | Five definitions | Unify in Phase 0 |
| New Kid vs enrollment | The tutorial never tells you to enrol; New Kid auto-starts in the editor | Orientation quest plus an `Enrol` objective |
| Canon clashes | Corvin twice; 1887 vs 1893; Vesper's post; Thaddeus Crane's surname | Your call (03 §1) |

## 2. Unnecessary duplication avoided
- **Relationships:** no new relationship store. `Social.Relationships` is extended.
- **Achievements:** no achievements system. Honours are entries in the existing Record.
- **Notifications:** no new notification channel. Broadcast feeds the Gazette, Night FM and the PA from one source.
- **Clothing:** no new clothing or cosmetic framework. Path unlocks are rows in the existing wardrobe and owned lists.
- **Quests:** no new quest system. Four objective types are added to `Quests`.
- **Factions:** no new faction system. Clique competitions extend `CliqueEvents` and `Superlatives`.
- **Timetables:** no second timetable. Electives extend `Config.Classes` and Attendance.

## 3. Performance risks

| Risk | Mitigation |
|---|---|
| 40 NPC students | Abstract simulation far away, existing brain throttles; measured in Phase 2/10 |
| Scenes and rumours spam | Region and hop rate limits |
| Bench viewports on phones | Fewer than 150 parts, no physics, lower texture sizes on mobile |
| Server loops | No new per-frame server loops; merge the per-player 1 s / 5 s loops |
| Place size (NH_Backup holds 35k instances) | Archive plan in Phase 0, only with your OK |

## 4. Data risks
- **Profile size:** one profile holds every slot. Measure it in Phase 0 and add a warning at 1 MB.
- **Every change is additive with a Sanitize.** The store names and slot keys are never changed.
- **Migration test:** load an old save (Testy before the change), check every new field defaults, and check that nothing is lost.

## 5. Deferred features and the reasons

| Feature | Why deferred |
|---|---|
| Physical arcade cabinets | A map change. Phone-arcade weekly boards come instead. |
| New elective rooms, dorm builds, a trophy room, a bell tower interior | A map change. Listed for the builder below. |
| Graduation ceremony | Needs the Chapter 5 ending written first |
| The Hollow (third faction) | Not requested; it stays a rumour in the lore |
| Fighting styles, weapon mastery | You put them on hold |
| Four beasts in live servers | Their clips need publishing (your account) |

## 6. Features needing your approval before work
1. The mythology direction (03 §2) and the canon conflict fixes (03 §1).
2. The anatomy specimen look (05 §6): a wax teaching model or a clockwork specimen.
3. The Archive page placement method:
   - **Runtime anchors:** data-only coordinates near existing objects, created at runtime in a separate `NHSystems` folder. The builds stay untouched.
   - **Builder tags:** the builder adds a tag to chosen props.
4. Lab Partners and group cuts (they change classroom multiplayer).
5. Curfew hours (22:00-06:00 proposed).
6. The crisis frequency (at most one a week proposed).
7. Porting to the Map place: when, and in what order.
8. Clean-up of `NH_Backup` and the TEMP models in NH Combat Test's workspace.

## 7. Requirements for the builder (documented, not built)
These would improve features, but none of them is required for the phases above:
- **Classroom tags:** each real classroom on the Map needs the same tags as the greybox: a `Zone` with RoomId, a `Door` and a `TeacherDesk`, plus seats for 12-20.
- **Missing places:** a chapel interior, a bell-tower stair and belfry, a basement corridor (the sealed doors), a Records Office with filing cabinets, an Archive with a restricted shelf, and a Staff Room.
- **Optional rooms:** an art room, a workshop, a darkroom (Photography), an arcade nook, and a dorm hall with numbered rooms.
- **Region boxes:** move them over the real rooms. They're already placed in a row for him.
- **Tag list for the systems:** `NHDoor`, `NHLamp`, `NHNoticeBoard`, `NHNpcSpot`, `NHBeastLair`, `NHWolfSpawn`, the HidingSpot lockers, and the QuestObject spots for cases.

## 8. Scope honesty
- This is a multi-month programme. Phases 0-3 are the foundation and can ship on their own. Phases 4-9 each stand alone once their dependencies are in.
- Nothing is marked complete until its acceptance list passes in a playtest, including two clients where it applies.
