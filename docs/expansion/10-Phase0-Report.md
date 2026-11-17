# 10. Phase 0 Report: Foundations and fixes (2.22.0)

**Date:** 2026-11-17. **Place:** NH Combat Test only. The Map and production were not touched.
**Mirror:** `tools/phase0-2220/` (`live/` is after, `pre/` is before), 25 scripts.
**Studio backup:** `ServerStorage.NH_Backup.Phase0_pre_20261117`.

## 1. What changed

| # | Fix | Scripts | Behaviour change |
|---|---|---|---|
| 1 | **One set of night windows.** | See below | Only the Spotted lantern |
| 2 | **The talk shot takes a camera lease.** | `Controllers.Gui.Dialogue` | None |
| 3 | **`Social` has one writer.** | `Social.Cliques` | The client copy is now correct |
| 4 | **The Gazette's night front page tells the truth.** | `Features.Phone` | Text only |
| 5 | **New Kid starts with enrolment, and auto quests wait for school.** | `Config.Quests`, `Quests.Quests`, `Gui.QuestTracker`, `Studio.TestBridge` | New step for new students |

**1. Night windows.**
- **The windows:** `Functions.SchoolTime.Windows` names five, in school-clock hours:

  | Window | Hours | Used by |
  |---|---|---|
  | Dusk | 18:30-6:30 | Lamps, ambience, region night text |
  | Dark | 19:30-6:00 | What students see |
  | Prowl | 19:30-5:30 | Beasts and wolves |
  | Night | 20:00-6:00 | Races, moon, hunger, rites, the bite, the clock HUD |
  | Late | 21:00-6:00 | Night chill and the schedule's Night segment |

- **The API:**
  - `SchoolTime`: `InWindow(hour, name)`, `IsNight`, `Phase`, and `Calendar(day)`, which gives Week, Term and Year (12-week terms, 3-term years).
  - `SchoolClock`: `IsNight(window?)`, `Phase()`, `Calendar()`.
- **Where each script used to keep its own hours:** the scripts below now name a window instead.
  - Shared and config: `Lineage`, `Config.Kit` (chill), `Config.Beasts`, `Config.Ambience`, `Config.Regions`.
  - Server: `Player.Evolution`, `Player.Turning`, `Player.Progression`, `Features.Phone`, `Features.MoonPhases`, `Features.Body`, `AI.StudentBrain`, `AI.Senses`, `Features.WildWolves`.
  - Client: `Gui.ClockHud`, `Gui.HungerVessel`, `World.Spotted`.
- **The one behaviour change:** the client's "spotted" lantern used 19:30-6:30. It now uses Dark (19:30-6:00), the same darkness the server's `AI.Senses` uses.

**2. The talk shot.** Opening a conversation now takes the `CameraLease` "Talk":
- It only writes the camera while it's the newest lease, so a cutscene that starts mid-conversation wins.
- It hands the camera back through the lease, instead of setting `CameraType` itself.
- Only the main menu, which owns the menu camera, still sets `CameraType` directly.

**3. `Social` has one writer.** `Social.Cliques.Add` changed standing in the save but never called `Reputation.Sync`, so the client's copy of `Social` went stale. It now syncs, batched once a frame.

**4. The Gazette's night front page.** The hall monitors are off duty at night, so the line now reads: "Night Study runs at the Archive table after dark. The hall monitors have gone home, but the Night Custodian keeps the Records Office: stay out of restricted areas."

**5. New Kid and enrolment.**
- **The new first step:** "Enrol at the Enrollment desk outside the Records Office and pick your uniform".
  - It's a new `Enrol` objective type.
  - The tracker waypoint uses a new `Kind = "Tag"` and points at `NHEnrollDesk`.
  - Enrolling sets `Enrolled`, and that moves the quest on.
  - A student who is already enrolled skips the step at once.
- **Old saves:** a New Kid saved before this keeps its place.
  - Stages are saved as indexes, so New Kid gained `Version = 2; StageShift = 1`.
  - On load, a version-1 save moves forward one stage, once.
- **Auto quests:**
  - **Before:** they started when a slot was chosen, while the student was still in the editor.
  - **Now:** they start once you walk into school (`InMainMenu` becomes false).
- **Test hook:** `NHTestBridge:Invoke("EnrolSelfTest", name)` runs all of this on the real code, then puts the player's quests back exactly as they were.

**Correction to the audit:** `Features.Fortune` was listed as a second `Social` writer. It isn't. It edits `Social` through `Reputation.Get` and then calls `Reputation.Sync`, which is the intended pattern. No change was needed.

## 2. Tests (NH Combat Test, Play, slot 4 "Testy")

| Check | Result |
|---|---|
| 480 sampled hours: every new window against the old formula, in all 7 places | 0 differences |
| 19:00 | Not night; no wolves |
| 19:45 | 3 wolves and 8 beasts out (Prowl); `NHMoonNight` still false; ClockHud 7:46 PM |
| 20:30 | `NHMoonNight` true (it republishes within 5 s); phase Night |
| 21:30, standing on the Field | Phase Late; Testy (Human) chilled after about 60 s outdoors |
| 05:45 | Still night (moon); the wolves left on the next 10 s check after 5:30; 44/46 lamps lit |
| 12:00 | Phase Day; moon night off |
| Enrol self-test | Already enrolled → Class. Not enrolled → Enrol, then Class after enrolling. An old stage-2 save → Leader, and loading it twice doesn't move it again. The desk tag is found. Testy's quests were the same before and after (4 done, 8 active). |
| A real old save | Testy's own New Kid was on its old stage 3 (Note). On load it moved to stage 4, still Note; the tracker showed "Someone jammed a note into locker 113". |
| Talk shot | Talking to Ezra: Scriptable camera, FOV 58 (70 − 12), letterbox bars, depth of field. A frame captured in Studio showed Ezra Vale over Testy's shoulder with the dialogue box. Closing with a real key (6): the camera returned to Custom, FOV 70, following the Humanoid, with the bars and blur gone. |
| Clique standing | `CliqueAdd(Ink, +3)`: the client received a 3,555-byte state update 0.13 s later (the whole `Social` table). Ink was put back to -18 afterwards. |
| Console | No errors from game scripts (only the existing asset-permission warnings). |
| Restored | `SlotCount` 3, `NHTestNoMenuKeys` cleared, camera Custom |

**Not tested:**
- **Two players.** The MCP can only start a one-player Play. The repeatable two-client harness is now written in `docs/Two-Player-Test-Plan.md` §9 (H1-H10) and needs Studio's 2 Players test, started by hand.
- **Opening a conversation with a real E press.** In this Play window, no `ProximityPrompt` showed at all, not even Ezra's at 3 studs. No game script hides prompts (`ProximityPromptService.Enabled` was true), so this looks like the background test window rather than the game. The conversation was opened through the server's own talk path instead. Please press E on Ezra once in a normal playtest.
- **Prompt competition near Ezra (an observation, not a Phase 0 change).** Talk prompts are "one per key", so a bookshelf prompt about 5 studs away wins E over Ezra's prompt about 7 studs away. A player has to stand right in front of him.

## 3. Measurements

**Save size:**
- Each save slot is its own ProfileService key (`"<UserId>'s Data"` for slot 1, `"...|Slot<N>"` for the others). So Roblox's 4 MB limit applies to each slot, not to all slots together. The audit said otherwise; this corrects it.
- Testy's whole save is **20.7 KB** (0.5% of the limit). The largest blocks:

  | Block | Size |
  |---|---|
  | Phone | 6.0 KB |
  | Social | 3.8 KB |
  | Attendance | 2.7 KB |
  | Discipline | 2.3 KB |
  | Inventory | 1.5 KB |
  | Quests | 1.0 KB |

- The expansion's planned additions (about 12 KB per slot at most) leave plenty of room.

**Place size (instances):**

| Where | Instances |
|---|---|
| ServerStorage | 118,670 |
| Workspace | 45,102 |
| ServerScriptService | 24,593 |
| ReplicatedStorage | 3,902 |
| StarterPlayer | 234 |

**Backups and leftovers** (ServerStorage unless noted):

| Item | Instances | What it is |
|---|---|---|
| `NH_Backup` | 35,861 in 169 folders | Biggest: `Combat_preAudit_1102` 24,273, `HairImports_100x` 5,029, `Hair_v2_import_leftovers` 3,861, `Hair_v1` 1,273 |
| `_InertLiveDummies_Backup` | 24,288 | Old dummy NPCs |
| `_DummyNpcs_PreTrainingDummy_Backup` | 24,220 | Old dummy NPCs |
| `Capes_Originals` | 15,858 | The capes before fitting |
| Workspace `MenuScene` | 10,032 | In use (the main menu) |
| Workspace `NHPropsShowcase` | 6,954 | A props showcase |
| Workspace `Vamp Cape`, `Fur Cape`, `Rogue Cape` | 5,153 + 5,827 + 4,875 | Cape models standing in the workspace |
| Workspace `Sean White` | 2,451 | A character model |
| Workspace `Crouch (Idle)`, `Crouch walk` | 1,601 + 648 | Stray KeyframeSequences |
| Workspace `NHTEMP_SpiderParts`, `NHTEMP_BatB` | 4 + 12 | Beast leftovers |

## 4. Archive (done 2026-11-17, 2.22.1)

**The owner approved it ("Yes, archive them").**
- **Exported first:** 15 items, 22.8 MB, 123,471 instances, to verified `.rbxm` files listed in `archive/studio-backups/2026-11/MANIFEST.md`.
- **The place now:** ServerStorage dropped from 118,670 to 19,865 instances, Workspace from 45,102 to 20,020, and `NH_Backup` from 35,861 to 1,425.
- **Kept:** `Sean White` (the gym barbell comes from it).
- **Checked after:** a Play run started with no script errors.

The original proposal follows, for the record.

### The proposal
**The aim:** cut the place by about 100,000 instances (roughly half of ServerStorage) without losing anything.

1. **Export first:** save each item below as an `.rbxm` file in `E:\Nightmare-Highschool\archive\studio-backups\2026-11\`, named after its Studio path, and commit the list of files with sizes. (The files themselves can stay out of git if they're large.)
2. **Then remove from NH Combat Test (about 99,000 instances):**
   - `_InertLiveDummies_Backup` and `_DummyNpcs_PreTrainingDummy_Backup` (about 48,500), superseded by the training dummy.
   - `NH_Backup.Combat_preAudit_1102` (24,273), from before the 11-02 combat audit, which has shipped and been playtested many times since.
   - The hair import leftovers: `HairImports_100x`, `Hair_v2_import_leftovers`, `Hair_v1` (about 10,200). The live hair catalog is elsewhere.
   - `Capes_Originals` (15,858), once you confirm the fitted capes are final.
3. **Move out of the workspace into ServerStorage** (or remove after export):
   - `NHPropsShowcase`
   - the three standing cape models
   - `Sean White`
   - the two Crouch KeyframeSequences
   - `NHTEMP_SpiderParts` and `NHTEMP_BatB`

   These are loaded on every client today.
4. **Keep:**
   - every backup folder from the last 14 days (the `*_pre_202611*` folders), until its feature has been playtested;
   - `MenuScene` (in use).
5. **From now on:** each session's `*_pre` backups are exported and removed once the change is playtested and committed, because the repo mirror (`tools/<feature>/pre/`) already keeps the old scripts.

## 5. What's left from Phase 0
- **Two players:** the two-client run of the harness (H1-H10), started by you in Studio.
- **Canon names:** Corvin, Vesper's post, and Crane. They wait for your decision (03 §1).
- **The archive:** carried out only after your OK.
