# Line matrix + outfits: play test (Task 8)

- **Date:** 2026-11-12
- **Place:** NH Combat Test (98950102230473), Studio Play solo
- **Save:** slot 4 "Testy" only (Human, Fenwick). Loaded with TestBridge `ChooseSlot 4`, then `EnterSchool`.
- **Temporary set-up, restored afterwards:** `SlotCount = 4; -- NH TEMP slot test: set back to 3` in `Config.MainMenu`, and `ReplicatedStorage` attribute `NHTestNoMenuKeys = true`. After Stop, Edit shows `SlotCount = 3;`, the attribute is nil and no "NH TEMP" text is left.
- **Nothing was chat-typed from the player.**

## How the live brain was read

`execute_luau`'s `require` gets its own module copy, so it can't see the live student records. For Play only, I added a
throw-away server Script, `NHTask8Probe`. It is gone after Stop and was never in Edit or saved. It runs in the game's own
VM and does three things:

- **Collects records.** It wraps `Brain.Urgent`, `Idle`, `GoTo`, `LeanOnWall` and `OnBump` as pass-throughs that note each
  student record `S`.
- **Logs speech.** It records every `NHSay` change on `NHBrain` models with `os.clock()`, and classifies each line against
  `Config.CliqueTalk` (`<Clique>.<Moment>[.<Sub>].<Attitude>`). A blank classification means the line came from the old
  `StudentBrain.Lines` pools, not the matrix.
- **Provides test hooks:**
  - resets `S.Memory[UserId].Outfit` / `Greeted` and `S.SaidAt` (the brief's `Outfit = -1e9`);
  - applies a test look with `UI.Appearance.ApplyTo` on Testy's sanitized profile look plus overrides (never saved);
  - sets a clique standing directly on the profile table, then runs `Cliques.SyncTiers`.

Two more throw-away Play-only scripts helped with specific checks:

- `NHTask8Notify` wrapped `Notifications.Notify` to record the Night Study notification text.
- `NHTask8Seal` could force `Quests.CanStart` results for the leader-marker isolation check.

A greeting is triggered for real: Testy stands still about 6 studs in front of the student, facing them, until the
Senses "Staring" path fires. Then `greet()` runs its usual dice: outfit 35%, race 30%, clique greet 60%, else today's
pool. I reset the memory between tries until the wanted moment came up.

## Results

| # | Check | Result |
|---|-------|--------|
| 2 | `NHWear` stamped | **PASS** |
| 3a | Athletes look: Athletes FullLook, Ink RivalLook | **PASS** |
| 3b | Ink look: Ink FullLook, Athletes RivalLook | **PASS** |
| 3c | `grimoire-chained` in front of an Athletes student: Mocks | **PASS** |
| 4 | Attitude tone at -50 / -20 / 0 / 30 / 70 | **PASS** (with a tone note) |
| 5.1 | Night Study refused undressed, with a Vigil DressCode notification | **PASS** |
| 5.2 | Night Study starts in `vigil-vest` | **PASS** |
| 5.3 | Leader at Neutral, undressed: `[Quest]` leads to DressCode; dressed: offer | **PASS** (with a note) |
| 5.4 | Hangout entry DressCode line, once per 120 s | **FAIL** (the regions are too high in this place) |
| 6.1 | Bump / Crowded / Shoved | **PASS** |
| 6.2 | Clique-less student greets / mutters | greets **PASS**; mutters **NOT TESTED** |
| 6.3 | No new console errors | **PASS** |
| X1 | Bump then shove double | **PASS** (reads natural; see the note) |
| X2 | Leader "!" marker for an undressed Neutral player | **PASS** |
| X3 | Other `Quests.CanStart` callers | **PASS** |
| X4 | `[StudentBrain] dressWatch:` / `[CliqueTalk]` warnings | **PASS** (none) |

### Step 2: `NHWear` is stamped: PASS

Server: `Character:GetAttribute("NHWear")` = `velvet-corset|velvet-midi|`.
Testy's sanitized profile look is `Uniform=44 (velvet-corset)`, `Bottoms=32 (velvet-midi)`, `Acc=""`, `UseAvatar=false`. The two match.

Every test look also re-stamped `NHWear` at once:

- `varsity-jacket|striped-joggers|`
- `black-shirt|uniform-trousers|`
- `velvet-corset|velvet-midi|grimoire-chained`
- `vigil-vest|velvet-midi|`

This stands in for Task 3's dummy test.

### Step 3: Outfit remarks: PASS

Athletes standing was -31 (Wary) and Ink -18 (Wary), so the Wary cells were expected. `Talk.Outfit` on the live
records agreed with each line before it was said.

| Look | Student | `NHSay` | Cell |
|---|---|---|---|
| Athletes (`varsity-jacket` + `striped-joggers`) | Athletes #12 | "Kit's right. Now show me a lap." | `Athletes.Outfit.FullLook.Wary` |
| Athletes | Ink #5 | "Gym clothes, here? Who sent you?" | `Ink.Outfit.RivalLook.Wary` |
| Ink (`black-shirt` + `uniform-trousers`) | Ink #5 | "Dressed like us. Can you draw?" | `Ink.Outfit.FullLook.Wary` |
| Ink | Athletes #12 | "Moody look. You one of the art crowd?" | `Athletes.Outfit.RivalLook.Wary` |
| Own clothes + `grimoire-chained` | Athletes #12 | "Is the chained grimoire for extra credit?" | `Athletes.Outfit.Mocks.Any` (`Talk.Outfit` -> `Mocks`, "chained grimoire") |

Before each outfit line, the student said ordinary greetings from the matching attitude pool, for example Ink #5:
"Testy. Here to look, or to judge?" and "Hm. You smell like gym mats." (`Ink.Greet.Wary`). `{Name}` filled in as "Testy".

### Step 4: Attitude tone: PASS

Standing was set directly on the profile table, then `SyncTiers`. This gives the same `CliqueTier_Athletes` as
`AddStanding`, without the rival share or the notifications.

| Standing | Tier and `Talk.Attitude` | Greet line | Cell |
|---|---|---|---|
| -50 | Hostile | "You again? Coach warned us about you." | `Athletes.Greet.Hostile` |
| -50 | Hostile | "Human. Easiest tackle of my life." (race moment) | `Athletes.Race.Human.Hostile` |
| -20 | Wary | "Hm. Didn't see you at practice." | `Athletes.Greet.Wary` |
| 0 | Neutral | "Hey. Got a spare water bottle?" | `Athletes.Greet.Neutral` |
| 30 | Friendly | "Testy! Good hustle yesterday." | `Athletes.Greet.Friendly` |
| 70 | Respected | "Testy! Saved you the good ball." | `Athletes.Greet.Respected` |

A first pass on student #12 also gave "Sup. Don't step on the free-throw line." (Neutral) and "Up top, Testy!"
(Friendly), until that model despawned at the AfterSchool replan. The rows above are from #4.

**Tone note (not a bug against the spec).** The greeting code uses the clique matrix only 60% of the time. Otherwise it
falls through to the met-before / night / today's pools, which ignore attitude. So a Hostile Athletes student said
"Hi." and a Respected one said "Hey." just before their matrix lines. This is the spec's order ("their clique, met
before, night, time of day"), but at the extremes (Hostile / Respected) a flat "Hi." undercuts the tone. Consider letting
Hostile and Respected students skip the plain daily hello.

### Step 5: Dress codes

**5.1: PASS.** Vigil 0 (Neutral), wearing `velvet-corset`, inside the Archive study zone. `Cliques.Dressed(Vigil)` = false.
TestBridge `NightStudy` returned `false`, with the notification:
`Not dressed for the Archive | No vest, no stacks. Sorry.` (`Vigil.DressCode.Any`).

**5.2: PASS.** Look switched to `vigil-vest`, so `Dressed` = true. `NightStudy` returned `true`.
Side effect: this sets `Social.StudyHour` on Testy's profile, which is normal for a started study.

**5.3: PASS, with a note.** Ezra, Vigil standing 0, undressed. `CanStart(CliqueVigil1)` = `false, DressCode`.

- Hub choices: `What is the Vigil? / I want in. / Your candle club is a joke. / [Quest] Lamplighter / Got a dare for me? / See you around.`
- `[Quest] Lamplighter` goes to node `Q_DressCode`. The client dialogue line reads "Readers only. Charcoal and a vest."
  (`Vigil.DressCode.Any`). Choices: `Fair enough. / Bye.`
- In `vigil-vest`, `CanStart` = `true, Ok`. Re-entering the hub, `[Quest] Lamplighter` goes to `Q_Offer`: "The lamps by
  the Archive have gone dark three nights running. ... Light them for me, after dark." I declined, and no quest was started.
- **Note (minor):** hub choices are built when the hub opens. I changed clothes while the hub was already open, and the
  old `[Quest]` choice still led to `Q_DressCode` until the hub was re-opened ("Fair enough." then back). A real player
  can't change clothes mid-dialogue, so this is low risk.

**5.4: FAIL.** No hangout DressCode line fires for a player on the floor in this place.

Repro:

1. Set Athletes to 0 (Neutral) and wear your own clothes, so `Dressed(Athletes)` = false.
2. Run `SchedulePlan Break`. Athletes #4 and #12 settle in the gym at about (95, 4, 175).
3. Walk Testy (`Humanoid:MoveTo`) from 50 studs south to 6 studs in front of #4.

Result: no `DressCode` line. #4 only said "Yo. You catch the game Friday?" (`Athletes.Greet.Neutral`).

Cause, measured: every hangout box in `workspace.Regions` floats above the ground. `hangoutOf` checks
`|L.Y| <= Size.Y/2 + 6`, so a root at y about 4 is never inside.

| Box | Y range (with the +6) | Floor / player root |
|---|---|---|
| Gymnasium (centre Y 41.9, size 98x40x60) | 15.9 to 67.9 | floor about 1, root about 4 |
| Archive | 13.8 to 41.8 | about 1 |
| Chapel / CrimsonParlor / Den / Commons | 15.2 to 45.2 | 0.9 to 1.3 |
| InkStudio | 15.2 to 43.2 | about 1 |
| BackLot | 11.9 to 53.9 | about 1 |

The boxes also look offset sideways. The Archive region box is centred at (113.9, 27.8, 38). The Archive study zone
(`School.Archive.Zone`) is at (92, 6.9, 22).

The rest of the logic works when the root is inside the box. I anchored Testy at (95, 18, 172), inside the box and
14 studs from #4:

- **In:** 0.8 s later #4 said "Varsity jacket or gym shirt. Rules." (`Athletes.DressCode.Any`). PASS.
- **Out and back in within 120 s:** dropped to y 5 (outside), then back to y 18. No second line. PASS.

**Fix to dispatch:** either move or resize the hangout boxes in NH Combat Test's `workspace.Regions` so they reach the
floor, or make `hangoutOf` ignore height or measure from the floor. Also check the Map place's boxes.
`Features.Regions.Inside` uses the same boxes with a 6-stud margin, so it has the same blind spot.

Separately, `hangoutOf` finds boxes with `FindFirstChild(Def.Hangout)` (by name, first match). `Features.Regions`
matches the `RegionId` attribute across all boxes. They agree today, because each box's name equals its RegionId and
there is one box per hangout.

### Step 6: Bumps, crowding, shoves; no regressions

**Bump: PASS.** Testy walked (speed about 14) through Ordinary #14 and #1 from the front, 1 stud off-centre.
`NHNudgeWhy` = `MakeWay: speed 14, ... dist 2.3`. Lines heard:

- "Whoa! Okay. Nobody panic." (`Ordinary.Bump.Any`)
- "Oops. Was that you or me?" (`Ordinary.Bump.Any`)
- "Sorry! I wasn't looking. Were you?" (`Ordinary.Bump.Any`)

The first two tries on Athletes #4 gave no line: a greeting 2 s earlier held the brain's 10 s talk cooldown, and the
bump line only rolls 60% anyway.

**Crowded: PASS.** Teleporting into the lunch crowd gave:

- "You're in my light." (`Vigil.Crowded.Any`)
- "Do you mind? This is couture." (`Court.Crowded.Any`)
- "Oh. Hi. You're kind of in my bubble." (`Ordinary.Crowded.Any`)
- "Can you scoot? Just a little?" (`Ordinary.Crowded.Any`)
- "Mind the candle, please." (`Vigil.Crowded.Any`)

**Shoved: PASS.** WalkSpeed was set to 26 for the run and then put back. Testy sprinted into Ordinary #14 from behind,
with room ahead. `NHNudgeWhy` = `MakeWay: speed 26, push.look 0.68, behind true, room 7.0, dist 2.8`, then
`NHNudge` = `Shove at 57247.05`.

- t=57246.67: "No running in the halls!" (old `Lines.Sprint` pool, said as the reaction starts)
- t=57248.27: "Ow. I was just standing here." (`Ordinary.Shoved.Any`), when the student looks back

**Clique-less student.** No brain student in this place lacks a clique: `Config.Cliques.Students` covers all 14, and the
default is "Ordinary". For the test I cleared `S.Clique` on Choir #7 and then restored it.

- **Greets: PASS.** It greeted from today's pools as before: "Hey. Long day, huh?", "Evening.", and the stared line
  "Take a picture, it lasts longer." Its crowd line fell back to Generic: "You're kind of close." (`Generic.Crowded.Any`).
- **Mutters: NOT TESTED.** #7 was stuck with `NHStep` = "walk failed: unreachable", so it never entered `Idle`, where
  mutters live. No other student was tried before time ran out.
- The `NHAmbient` set-piece NPCs (Push-up kid and others) are not brain students. Their client-side Chatter was not checked.

**Console: PASS.** Server and client `LogService` history, ignoring asset-permission noise, showed only:

- the usual start-up warnings (`| AI |: LOADED`, `No existing players found...`, the Assistant plugin version notice,
  the animation loader);
- one error from my own snippet (`AssistantCommand:11` indexing a despawned student), which is not game code.

There were no `[StudentBrain]`, `[CliqueTalk]`, `[Schedules]`, `[QuestSeals]` or quest/dialogue errors.

### Extra checks

**X1: Bump then shove: PASS (natural).** A sprint into someone from behind gives two lines. The first is the reaction
line, then 1.6 s later (1.22 s after contact) comes the Shoved line as they turn round: "No running in the halls!"
followed by "Ow. I was just standing here." It reads as one beat: a warning, then the complaint, with the look-back
animation in between. It doesn't read as noise.

Things to know:

- **The first line is the old Sprint pool, not the matrix.** `React.MakeWay` says `Lines.Sprint` when `Rec.Speed > 18`,
  so a shove (which needs speed 20 or more) never gets a clique Bump line first. Only the second line has the clique's
  voice.
- **A matrix Bump line followed by a Shoved line** needs the sensed speed to be 18 or less while the contact speed is
  20 or more (the 0.6 s ram memory). I didn't see that happen.
- **Teleport artefact.** Teleporting next to a student can make Senses read a huge speed. One stroll test got "Slow
  down!" (Sprint pool) right after a teleport. That's a test artefact, not a game bug.

**X2: Leader marker: PASS.** Undressed and Neutral with the Vigil, Testy saw Ezra's `NHQuestSeal` with the Offer icon
(`rbxassetid://118658855836011` = `IconNpcOffer`).

Every leader also has a startable dare today, which would raise the marker anyway. To isolate the DressCode case, I
used `NHTask8Seal` to force Ezra's three dares to `NotToday`. The Offer seal stayed over Ezra after the 15 s resend.

Control: forcing `CliqueVigil1` to `Locked` as well made Ezra's seal disappear. Dex's and Pip's seals stayed, as they
should. Wrapper removed afterwards.

**X3: Other `Quests.CanStart` callers: PASS.**

- `Quests.Start(CliqueVigil1)` while undressed returns `false` cleanly, through TestBridge `StartQuest`.
- `Phone` (lines 345 and 404) and `CliqueEvents` (line 62) only ask about dares. Dares are exempt from the dress code, so
  they never see "DressCode". If they did, Phone would fall back to "You can't take that dare right now."
- No `Auto` quest has a clique, so the auto-start at `Quests:501` is unaffected.
- `Offers` is only called from `Dialogue` (`WithDressCode = true`). No client script mentions DressCode.
- The seal map (`Quests:143`) keeps the Offer state for DressCode, as tested in X2.

**X4: New warnings: PASS.** No `[StudentBrain] dressWatch:` or `[CliqueTalk]` warning appeared all session.

## Environment noise seen

- NH Combat Test has combat dummies and Delinquent AI. During the AfterSchool and gym runs, "Ink Club Prankster" and
  "Varsity Bruiser" NPCs fought near Testy (Testy's `HitCounter` = 2), so students around kept saying FightSeen, Flee and
  relief lines. Examples: "Keep score! Somebody keep score!" (`Athletes.FightSeen.Any`) and "Someone get a teacher!"
  (`Generic.Flee.Any`). These lines are correct for that moment. They just made the greeting tests slower.
- Athletes #4 showed "Club: Archive" as its AfterSchool activity. Clubs come from the student index, not the clique. Out
  of scope.

## Not tested

- **A second player:** two players' `Visits` and memories, and one student remarking to two players. Studio solo only.
- **Clique-less mutters** (see 6.2).
- **Hangout entry at the real floor level.** It fails, as above, so the "once per visit" rule was only proven with the
  raised root.
- **Real Wardrobe changes.** Looks were applied with `ApplyTo` server-side, not through the Wardrobe UI and the `Set`
  remote. `NHWear` stamping is inside `ApplyTo`, so both paths share it.

## Restored after the test

- **Testy's standings,** back to the values at the start: Vigil 0, Court 0, Athletes -31, Delinquents 0, Pack 62,
  Ordinary 0, Choir -15, Ink -18.
- **Testy's look:** the profile look was re-applied (`velvet-corset|velvet-midi|`). The profile `Appearance` was never
  written. Race was never touched (still `Human`).
- **Quests:** no quest started (`CliqueVigil1` still `DressCode`).
- **Play:** I stopped the Play session I had started. Edit now has `SlotCount = 3;`, no `NHTestNoMenuKeys`, and no probe
  scripts.

## Play-test fixes (Task 7, fix round 2)

Two `StudentBrain` fixes came out of the run above. Both were applied live in Edit (checksum 2707957, 35462 b = the repo
file), then checked in a short Play session on slot 4 "Testy" only (`SlotCount = 4` and `NHTestNoMenuKeys` for the run,
both restored). Nothing was chat-typed, and no other slot was loaded. A throw-away Play-only probe script gathered the
student records and logged `NHSay`; it is gone.

**1. Hangout entry at floor level (was 5.4 FAIL): PASS.** `hangoutOf` now matches the box's X/Z footprint, with a vertical
band from 20 studs under the box's bottom face to 6 over its top face (boxes stay where they are; other systems use them).

- Set-up: Athletes 0 (Neutral), own clothes (`velvet-corset|velvet-midi|`), so `Cliques.Dressed(Athletes)` = false.
  `SchedulePlan Break`. Athletes #4 and #12 settled in the Gymnasium at about (95, 4, 160 to 177).
- Testy was placed outside the box at (95, 4.5, 118), waited 3 s, then walked with `Humanoid:MoveTo` to (95, 4, 165). Her root stayed at y about 4.3.
- Result: one `DressCode` line from the nearest Athletes student, #4: "Locker room's team only. Kit up."
  (`Athletes.DressCode.Any`). No second line came after it for that visit.
- A later walk-in at Hostile gave the Hostile cell: "Out. Team only. Bench is outside." (`Athletes.DressCode.Hostile`).

**2. Strong attitudes always greet from the matrix: PASS.** In `greeting()`, step 6 now computes `Talk.Attitude(S, Pl)`
(in a pcall, "Neutral" on failure). Hostile, Wary and Respected always return the clique `Greet` with `{ Attitude = A }`. Neutral
and Friendly keep the 60% roll. The fallback pool is unchanged.

- Athletes standing set to -50 (Hostile) on Testy. 8 staring tries on #4 and #12.
- #12 (Wary, because it had met Testy 4 or more times, which lifts Hostile one step) greeted seven times, all from the matrix:
  "Testy. Sign-up sheet's by the door.", "Hm. Didn't see you at practice.", "You lost? The gym's not a hallway.",
  "Trying out, or just standing there?" (all `Athletes.Greet.Wary`), and one race line "Human. Don't get hurt on my
  court." (`Athletes.Race.Human.Wary`). No plain daily hello ("Hi.", "Hey.") came before or between them.
- #4 (Hostile) mostly said stare and flee lines ("Please stop looking at me.", "...", "Um. Bye."), which come from
  the Senses stare path, not the greeting. A pure `Athletes.Greet.Hostile` line was **not** caught in this short run
  (the Wary matrix cells were, and the Hostile one was seen in the earlier run). The code path is the same for both attitudes.
- Console: no `[StudentBrain] dressWatch:` or `[CliqueTalk]` warning.

**Restored:** Testy's Athletes standing back to -31 (Vigil 0, Court 0, Delinquents 0, Pack 62, Ordinary 0, Choir -15,
Ink -18, as before); `SlotCount = 3;`, `NHTestNoMenuKeys` cleared, no "NH TEMP" text, probe script gone, Play stopped.
