# Quiet Corners UI Implementation Plan (one day)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Every subagent runs on model `opus`.

**Goal:** The whole-screen Quiet Corners UI in one focused day, built from art that's already baked:
- **QC1, the HUD state:** one HUD state (Active, Calm, Combat, Cut, Dialogue, Lesson, Menu) and the `HudMode` setting (Always, Ghost or Vanish; Ghost is the default).
- **QC1, slips:** paper event slips, top-left, replace the top-centre toast stack.
- **QC2, trims:** race-trimmed prompts on the object, a re-arted compass strip and the CineUI skip ring.
- **QC3, dialogue:** the calling card with an animated clique crest, the ribbon, reply tabs and tone marks.
- **QC4, the book:** the Journal as the open book.
- **QC5, the Evidence Wall:** the wall replaces the Case Files tab, and the server checks each pair against one question.

Every new or restyled piece meets the owner's rules:
- It's built only from existing art: the kit, the Bell Tower set and the new Quiet Corners, Evidence and Dialogue sets.
- No text is under 20 design px, and nothing clips or overlaps.
- It has a phone layout.
- It never uses `Theme.Images.Seal`.
- Anyone without a clique shows the Unaffiliated crest.
- Reduce Motion is respected (the crest shows frame 0 only).

**Architecture:**
- **One pure module, `ReplicatedStorage.Functions.QuietCorners`,** holds every rule that can be tested without instances: the state machine, the HudMode targets, art lookup with fallbacks, crest choice, flipbook frames, slip routing and queueing, prompt sizing, card lines and the Evidence Wall model.
- **One state controller, `Controllers.Gui.HudState`,** owns the state:
  - It publishes the state as `NHHudState` and fades three clusters through CanvasGroups it adopts: `TopLeft` (NHTopBar), `Compass` (NHCompass) and `Vitals` (KitHud.Bottom).
  - It owns the Studio-only client probe `PlayerGui.NHQuietProbe`, a BindableFunction that the checks invoke from their own VM.
- **One new screen, `Controllers.Gui.EvidenceWall`.**
- **Everything else is a restyle in place** of an existing controller: Notifications, PromptUi, Compass, Dialogue, QuestJournal, CineUI (the skip ring only), KitHud and TopBar (adoption only), and SettingsMenu with `UI.Settings` (HudMode).
- **Three art-id configs:** `Config.QuietCornersArt`, `Config.DialogueArt` and `Config.EvidenceArt`.
- **The server changes are small:**
  - `Social.Dialogue` sends `Clique` and `Tones`.
  - `Quests.Investigation.Link` takes a question id.
  - `Quests.Quests` passes the question id through.
  - `Config.Cases` gains `Questions` and clue `Kind`s.
- **The Bell Tower (ClockHud, QuestTracker) isn't touched today.** R2 is changing ClockHud on `belltower-r2` (ruling 2).

**Tech Stack:**
- **Game:** Roblox Luau in NH Combat Test (placeId 98950102230473). Code is installed from the repo mirror through `E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py`.
- **Checks:** Luau check scripts in the Edit VM (pure), the Client VM (through the probe) and the game VM (`server.py`, a runtime Script).
- **Art staging and the ids filler:** Python with Pillow.

**Spec:** `docs/superpowers/specs/2026-11-21-quiet-corners-ui-design.md`:
- §2: the state table and HudMode.
- §3: slips and prompts.
- §4: trims.
- §5: the compass.
- §6: the book.
- §7: the Evidence Wall.
- §8: dialogue and the crest animation.
- §9: the fit check.
- §12: the piece list.
- §13: QC1 to QC5 acceptance.

Mockups are in `docs/superpowers/mockups/2026-11-21-quietcorners/`. Every layout number below comes from `art/ui/hud/make_quietcorners_mockups.py`, in design px at 1920 x 1080.

**Base for the repo tasks:** read-only copies of the live client controllers, taken from NH Combat Test in Edit on 2026-11-22, are in `E:\qc-read\`. They are Compass, Dialogue, KitHud, Notifications, PromptUi, QuestJournal, SettingsMenu, TopBar, CineUI, ClockHud, QuestTracker, HungerVessel, KitUi and CombatTag. Live `ClockHud` matched `tools/belltower-r1/live` byte for byte, so R2 isn't installed yet. Task S1 dumps fresh copies and diffs them against this base before anything is installed.

## Global Constraints

- **Place:**
  - Build only in **NH Combat Test**. The Map place is read-only.
  - Read `E:\Nightmare-Highschool\docs\Pipeline-Lessons.md` (read it there; don't touch that checkout) before any Studio step.
- **Studio is shared:**
  - One session drives NH Combat Test at a time. During planning another agent was in Play there.
  - Before any install or Play, the controller gets "Studio released" from whoever holds the place (today, the belltower-r2 / phase6 session), or confirms with the owner that it's free.
  - When done, it sends "Studio released" back, from Edit mode with slot 2 restored.
  - Never save, close, reload or revert the place.
  - **Never edit `ServerStorage.NHTestBridge`.** Only the harness's `start_play.lua` (ChooseSlot, SetTime, EnterSchool) talks to it, and no ad-hoc script invokes it.
  - If the permission system denies anything, stop and report the exact text. Don't work around it.
- **Branch:**
  - The branch is `ui-quietcorners` in the worktree `E:\NH-ui`. Never switch branches in `E:\Nightmare-Highschool`.
  - Don't touch `E:\NH-main`, `E:\NH-strafes`, `E:\NH-injury` or `E:\NH-transform`.
  - Commits use `git -c user.name=Rello` and end with:

    ```
    Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
    Claude-Session: https://claude.ai/code/session_016roggwHneH5XgNzN25tniz
    ```
  - Don't push.
- **Backups:** before the first Studio edit, clone each script this plan changes to `ServerStorage.NH_Backup.QuietCorners_pre_<YYYYMMDD>` (the Studio day's date), named `<Service>_<path_with_underscores>`.
- **Mirror** (`tools/quietcorners/`):
  - `base/` holds the 2026-11-22 reads (Task R0). `pre/` holds the fresh dump of the Studio day (Task S1). `live/` holds the scripts after this plan. There is one `.luau` per script, named by its dotted path.
  - Studio is changed only by `harness/install.py` from `live/`, in Edit mode. It installs fresh instances and keeps their children.
  - If `pre/` differs from `base/` for a script that `live/` changes, rebase with `git merge-file live/X base/X pre/X` before installing.
- **Every Play round, in order:**
  1. Confirm Edit mode, then install.
  2. Start Play. Use the Studio MCP `start_stop_play`; if it times out, check `get_studio_state`.
  3. Run `start_play.lua` on the Server. It sets the time to 12:30, after school, so no Absent is booked.
  4. **Take a fresh snapshot every round:** run `snapshot.lua` on the Server and save its JSON to `harness/_slot2.json`.
  5. Run the checks.
  6. Run `restore.py` while still in Play. It must print `restored`.
  7. Stop Play.
- **Test slot:** slot 2 only. Never commit `_slot2.json` or the underscore temp files (except `_backup.lua`).
- **Client attributes:** checks may set client-side Player attributes (`NHHudMode`, `InDialogue`, `NHMenuOpen`, `Race`, `NHReducedMotion`). Each check puts back what it changed. Never use the bridge's `SetRace` (it saves).
- **R1/R2 contracts stay:**
  - `ClockHud`'s only direct Frame child is `Panel`, and `Panel.Bells` (R2) isn't touched.
  - A visible label contains "In class".
  - `ClockHud.Shared.ShowPA` exists.
  - `QuestTracker.Tracker` stays an ImageLabel, with AnchorPoint.X above 0.5 on desktop.
  - The ScreenGui names in the hide lists (GamepadControls, TouchControls, `UI.Settings`) don't change: `KitHud`, `ClockHud`, `QuestTracker`, `Notifications`, `Dialogue`, `QuestJournal`, `NHCompass`, `NHTopBar`.
  - Task S3 reruns R1's `bt_contracts.lua` to prove it.
- **UI art:**
  - Use only the kit, `Config.BellTowerArt`, and the three new configs. A missing id falls back to the Human trim, then to today's kit art, so nothing breaks before upload.
  - No plain default frames: containers are transparent, and every visible surface is an image or a kit builder.
  - Never `Theme.Images.Seal` in new or restyled UI. The checks scan for it.
- **Text:** at least `QuietCorners.MIN_TEXT` (20) design px. `TextFits`, no overlaps, and inside the art's text box. `qc_fit.lua` checks all of this.
- **Accessibility:**
  - `NHReducedMotion` means 0.2 s cross-fades only: no slides, shakes, typing, nib bob or page turns, and the crest stays on frame 0.
  - `NHReducedFlash` means no glow pulses.
- **Phones** (shorter side under 600): slips at most 2, the book one page at a time, the wall as a tray plus a list, and dialogue at the 0.66 phone scale.

## Rulings and spec deltas (record each in the CHANGELOG)

1. **One-day scope.**
   - QC1 to QC5 ship lean, as listed in the decision table.
   - Book tabs today: **Journal, Evidence, Record, Settings**. Record opens the Permanent Record (M), and Settings opens the Settings panel. Almanac (Bell Tower R4) and Ledger come later.
2. **The Bell Tower isn't touched today.**
   - It doesn't ghost, fold or hide on the new states, and `PlateTrim<Race>` isn't applied. R2 is rewriting ClockHud and QuestTracker on `belltower-r2`, and touching them now would collide.
   - `NHHudState` is published, so the later hook (about 10 lines: hide `Panel` in Dialogue/Menu; in Combat, hide `Plate` and `Conduct` and the card) lands with or after the R2 merge.
   - Until then the Bell Tower stays full in every state, which also satisfies "Vanish keeps the dial".
3. **Fading goes through CanvasGroups.**
   - `HudState.Adopt` wraps a cluster's top-level pieces in a full-width CanvasGroup `QcFade`, pinned to the top or bottom edge with a fixed design height, so positions don't move.
   - The DOWNED alert stays outside (danger breaks through).
   - NHCineUI already fades top-level CanvasGroups during seamless cuts and puts them back to what they were. That is the calm level, which is exactly spec §2's "returns to calm, not full".
   - During a Cut, HudState doesn't tween.
4. **Uploads are capped at 1024 px.**
   - `Book` and `Wall` upload as 4 quadrants each (TL/TR/BL/BR, at most 1024 x 582). They are drawn edge to edge, instead of the spec's 9-slice split.
   - Other pieces over 1024 are downscaled to 1024: CompassStrip, PlateTrim, CasePlate, QuestionSheet, CallingCard and Ribbon. They stay at 1x density or more at their design size.
5. **The slip detail is one line,** shortened at a word with "…" to fit the slip's text box.
   - **Routing:** `Data.Open` (`Texts`, `Evidence` or `Journal`) wins; otherwise the title decides ("Text from…" goes to Texts; "New insight", "Clue…" and "Case breakthrough" go to Evidence; "Quest…" and "Objective…" go to the Journal).
   - Unrouted slips aren't clickable.
   - The paper-rustle sound is the kit's `Tick`; the kit has no paper sound.
6. **Danger:** a slip with `Kind == "Bad"` breaks through every queue. `DangerAlert` (DOWNED) and the Bell Tower are untouched.
7. **The peek:** pressing Tab or View wakes every cluster for 4 s at once (no 0.3 s hold). Tab still opens Students. See open question 3.
8. **Dialogue:**
   - The ribbon is a 9-slice that grows upward for long lines. The card rides on the ribbon's top margin.
   - The nib bobs at the right end of the last line box. It doesn't track the exact last glyph.
   - The card's trim and the reply tabs follow the **local player's** race (spec §4); the crest follows the **speaker's** clique.
   - Replies stack upward from the bottom-right. Over 5 replies, the step tightens from 78 to 72.
9. **Clue kinds:** `Photo` needs a `Photo` image id on the clue. Until one exists it draws as `Object`.
   - The Empty Desk: LockerNote is a Note, DeskCarving an Object, AttendanceSheet and ArchiveCard are Records, and MiraFile is a Record with `Hidden = true` (shown once found, never as "Not found yet").
10. **Questions are public** (`Config.Cases[...].Questions`, spec §7.4), with `Bonus = true` on Warned.
    - The wall turns to "Your answer" when every non-bonus question is answered. The server's `Needs` still decides.
    - `Link` with a question id checks only that link, so a right pair in the wrong question is a miss.
    - `Link` without one still works (old clients).
11. **The "Answered" seal on a question sheet** is the Bell Tower `Seal` art tinted crimson (as in the mockup), not the kit seal.
12. **Version:** 2.38.0, assuming R2 ships as 2.37.0. If QC merges first, the owner picks the order.
13. **Ink palette, fixed for contrast** (measured 2026-11-22 with Pillow from each art's text box; spec §9):
    - The mockup's `InkDim` (92, 62, 46) and `InkRed` (130, 18, 24) give only 3.6:1 to 3.8:1 on the paper (170, 156, 134). The case-plate text (44, 26, 12) gives 2.8:1 on brass.
    - The game uses Ink (40, 22, 16), **InkDim (48, 30, 22)**, **InkRed (96, 10, 16)** and **plate ink (24, 14, 8)**.
    - Inactive book-tab labels use (220, 208, 188), because DIM fails on the leather tab (99, 76, 68).
    - On the selected reply tab (velvet (131, 47, 55)), the reply text is Bone.
    - **Measured `QcBg` values:**
      - Slip, PromptTag, QuestionSheet, CardNote and AnswerCard paper: (170, 156, 134)
      - Ribbon: (169, 155, 133)
      - Book page: (181, 162, 130)
      - CardRecord: (160, 137, 106)
      - CardObject: (163, 132, 88)
      - CasePlate: (133, 93, 36)
      - CallingCard iron: (44, 39, 38)
      - ReplyTab: (41, 37, 36)
      - PromptCap: (46, 41, 40)
      - CompassStrip: (47, 43, 42)

## Decision for the owner: what Quiet Corners replaces, restyles or adds

| Part today | Controller | Today | Decision | Recommendation and why |
|---|---|---|---|---|
| **Vitals and hotbar** (Thornrose, posture briar, Yen, hotbar, DOWNED) | `Gui.KitHud` | bottom-centre, re-arted 1.74 to 1.77; hides in dialogue and lessons | **Keep, plus join the state.** `Bottom` is adopted as the `Vitals` cluster: Ghost/Vanish/Combat/Dialogue, low-health keep-awake, and a 4 px crimson `Thread` health line in Vanish. The art doesn't change. | **Keep.** Thornrose is recent, owner-picked art, and the spec's bottom zone is exactly it. DOWNED stays outside the fade (danger). |
| **Compass** | `Gui.Compass` | top-centre strip of plain ink frames, letters at 18/15 px, readout at 15 px | **Restyle in place:** `CompassStrip<Race>`, `CompassLubber<Race>` and tiled `CompassTicks`; letters at 24/20; readout at 20; letters kept 16 px off icons. Same markers, range rules and API (`Toggle`, `SetRegion`). Adopted as the `Compass` cluster. | **Restyle.** It's the owner's choice ("keep today's strip format, new art only"), and today's text is under the floor. |
| **Event toasts → slips** | `Gui.Notifications` | top-centre `Kit.Toast` stack (it carries the wax seal), at most 4 | **Replace** the visuals in the same controller: `Slip<Race>` paper slips top-left under the top bar, at most 3 (2 on phones), newest on top, queued in combat/cut/dialogue/menu with a "N waiting" stub, click to open. `Packets.Notify` is unchanged. | **Replace.** It's the spec's layout, it frees the centre, and the seal goes. |
| **Prompts** | `Gui.PromptUi` | engraved billboard on the object; plain ink frames; text 14 to 19 px | **Restyle in place:** `PromptCap<Race>` with key and hold fill, `PromptTag<Race>` (9-slice, grows to fit), and `PromptPip<Race>` for the non-nearest prompts. Text at 22/20. `KeepDefaultStyle`, `Reject` and `NHRejected` are kept. | **Restyle.** It's already on the object, which matches the spec; only the art and the nearest-only rule are new. Today's text is under the floor. |
| **Journal** | `Gui.QuestJournal` | kit ornate panel; tabs Quests and Case Files | **Restyle into the open book** (Book quadrants, BookTab/BookTabOn, BookCorner<Race>). The left page lists leads on Bell Tower `LeadCard` art; the right page holds the selected quest's detail in ink. Tabs: Journal, Evidence (opens the wall), Record, Settings. Name, `Toggle` and `SelectTab` are kept. | **Restyle, lean.** It's the first thing to cut if the day runs long (it falls back to today's Journal). Almanac and Ledger wait for their systems. |
| **Case Files → Evidence Wall** | `Gui.QuestJournal` tab 2 | pick two clues and press Connect | **Add** `Gui.EvidenceWall` (full screen, menu state) and **remove** the Case Files tab (its tab opens the wall). Server: `Link(..., Question)`. | **Add.** The owner asked for "way cooler and way easier to understand". |
| **Dialogue** | `Gui.Dialogue` | compact kit ornate box, speaker in faction colour, `ChoiceRow` replies, text 15 to 19 px | **Replace the visuals:** `CallingCard<Race>`, the animated `Crest<Clique>` (Unaffiliated when there's no clique), `Ribbon`, `ReplyTab<Race>`/`ReplyTabOn<Race>`, `Tone*` and `Nib`. The packets, talk cinematic, keys, InDialogue and backpack handling are kept. The server sends `Clique` and `Tones`. | **Replace.** The owner asked for "completely new art". The crests are already uploaded. |
| **Top bar** (Menu, Chat, Students) | `Gui.TopBar` | top-left | **Keep, plus join the state** (adopted as the `TopLeft` cluster). | **Keep.** The slips sit under it. |
| **Bell Tower** (dial, plate, conduct, Bell Rail, lead card) | `Gui.ClockHud`, `Gui.QuestTracker` | top-right (R1 merged; R2 on `belltower-r2`) | **Not today** (ruling 2): no PlateTrim, fold or hide. `NHHudState` is ready for the hook. | **Defer** until after the R2 merge, to avoid a ClockHud collision. About 30 minutes then. |
| **CineUI skip button** | `Gui.CineUI` | a wax-seal button (`Theme.Images.Seal`) | **Restyle** to `SkipRing<Race>`, a one-line image swap. The subtitle seal stays (open question 5). | **Restyle.** It costs minutes and removes one seal. |

## File structure

| File | Responsibility | New / changed |
|---|---|---|
| `art/ui/hud/export_quietcorners_upload.py` | stages the 125 upload images (quadrants, the 1024 cap, tiers) and the manifest | new |
| `art/group-upload-quietcorners/{A,B,C}/*.png`, `upload-manifest.json` | the upload set | new |
| `tools/quietcorners/base/*.luau` | the 2026-11-22 reads (rebase base) | new |
| `tools/quietcorners/harness/*` | R1's harness, retargeted, plus `probe.py`, `server.py` and `ids.py` (with `test_ids.py`) | new |
| `…/live/ReplicatedStorage.Functions.QuietCorners.luau` | the pure rules | new |
| `…/live/ReplicatedStorage.Config.{QuietCornersArt,DialogueArt,EvidenceArt}.luau` | art ids, 9-slice rects and text boxes | new |
| `…/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.HudState.luau` | the state, the clusters and the probe | new |
| `…/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.EvidenceWall.luau` | the wall | new |
| `…/live/…Controllers.Gui.Notifications.luau` | the slips (visual rewrite) | changed |
| `…/live/…Controllers.Gui.PromptUi.luau` | cap, tag, pip and fill | changed |
| `…/live/…Controllers.Gui.Compass.luau` | strip, lubber, ticks, text sizes, adoption | changed |
| `…/live/…Controllers.Gui.Dialogue.luau` | card, crest, ribbon, tabs and tones | changed |
| `…/live/…Controllers.Gui.QuestJournal.luau` | the book | changed |
| `…/live/…Controllers.Gui.{KitHud,TopBar}.luau` | adoption, wake calls and the Vanish thread | changed |
| `…/live/…Controllers.Gui.CineUI.luau` | the skip ring image | changed |
| `…/live/…Controllers.Gui.SettingsMenu.luau`, `…/live/ReplicatedStorage.UI.Settings.luau` | HudMode | changed |
| `…/live/ReplicatedStorage.Config.Cases.luau` | clue `Kind`/`Order`/`Hidden`, `Questions`, `Number` | changed (Studio day) |
| `…/live/ServerScriptService.Services.Social.Dialogue.luau` | `Clique` and `Tones` in the node | changed (Studio day) |
| `…/live/ServerScriptService.Services.Quests.{Investigation,Quests}.luau` | the question id, `Open = "Evidence"` | changed (Studio day) |
| `tools/quietcorners/checks/*.lua` | `qc_pure`, `qc_state`, `qc_slips`, `qc_notify_server`, `qc_prompts`, `qc_compass`, `qc_dialogue`, `qc_dialogue_real`, `qc_wall_server`, `qc_wall`, `qc_book`, `qc_fit` | new |
| `docs/UI-Kit.md`, `docs/Quests-and-Investigation.md`, `CHANGELOG.md`, the spec | documentation | changed |

(`…` = `tools/quietcorners`; `…Controllers.Gui` = `StarterPlayer.StarterPlayerScripts.Controllers.Gui`.)

## Time budget

| Part | Tasks | Estimate |
|---|---|---|
| Repo only, 7 h of work | R0 to R3 in series (about 1 h 45 min), then R4 to R11 as parallel subagents (each 25 to 75 min; the longest, R9, is about 75 min) | about **3 h wall clock** |
| Studio | S1 to S6 | about **5 h** |
| **The day** | | **about 8 h**. The cut line, if late: S4's book (QuestJournal stays as today), then the wall's phone tray polish |

---

# Part 1: repo-only tasks (no Studio)

### Task R0: The base copies (5 min)

**Files:** Create `tools/quietcorners/base/*.luau`.

- [ ] **Step 1: Copy the reads.** Copy every `E:\qc-read\*.luau` into `tools/quietcorners/base/`, keeping the file names.
- [ ] **Step 2: Commit** "Quiet Corners: base copies of the live client controllers (2026-11-22 reads)".

### Task R1: Stage the art for upload (25 min)

**Files:** Create `art/ui/hud/export_quietcorners_upload.py`, `art/group-upload-quietcorners/{A,B,C}/*.png` and `art/group-upload-quietcorners/upload-manifest.json`.

**Interfaces:** Produces 125 PNGs named `Qc*` (Quiet Corners), `Ev*` (Evidence) and `Dl*` (Dialogue). The 18 crests are already uploaded (`out/dialogue/ids.json`) and are skipped.

- [ ] **Step 1: Write the script.**

```python
"""Stage the Quiet Corners, Evidence Wall and dialogue art for the group upload (group 15981569).
Roblox caps images at 1024 px: Book and Wall split into quadrants, anything else over 1024 is downscaled.
usage: cd art/ui/hud && python export_quietcorners_upload.py
Writes art/group-upload-quietcorners/{A,B,C}/<Prefix><Name>.png and upload-manifest.json.
Tiers: A = Human + shared (drawn today), B = the other five races, C = not drawn today (PlateTrim, Cork)."""
import json
from collections import Counter
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
DEST = HERE.parents[1] / "group-upload-quietcorners"
RACES = ["Human", "Priest", "Vampire", "Werewolf", "Ghoul", "Wraith"]
SETS = {"quietcorners": "Qc", "evidence": "Ev", "dialogue": "Dl"}
QUADS = {"Book", "Wall"}
LATER = {"Cork"} | {f"PlateTrim{r}" for r in RACES}
CAP = 1024


def tier(name):
    if name in LATER:
        return "C"
    race = next((r for r in RACES if name.endswith(r)), None)
    return "B" if race and race != "Human" else "A"


def main():
    done = set(json.loads((OUT / "dialogue" / "ids.json").read_text()))
    manifest = []
    for sub, prefix in SETS.items():
        for src in sorted((OUT / sub).glob("*.png")):
            name = src.stem
            if name.startswith("_") or name in done:
                continue
            im = Image.open(src).convert("RGBA")
            if name in QUADS:
                w, h = im.size
                hw, hh = w // 2, h // 2
                pieces = [(name + k, im.crop(b)) for k, b in (("TL", (0, 0, hw, hh)), ("TR", (hw, 0, w, hh)),
                                                              ("BL", (0, hh, hw, h)), ("BR", (hw, hh, w, h)))]
            else:
                pieces = [(name, im)]
            for key, piece in pieces:
                if max(piece.size) > CAP:
                    k = CAP / max(piece.size)
                    piece = piece.resize((round(piece.width * k), round(piece.height * k)), Image.LANCZOS)
                t = tier(name)
                (DEST / t).mkdir(parents=True, exist_ok=True)
                file = f"{prefix}{key}.png"
                piece.save(DEST / t / file, optimize=True)
                manifest.append({"file": file, "tier": t, "key": key, "set": sub, "size": list(piece.size), "source": src.name})
    (DEST / "upload-manifest.json").write_text(json.dumps(manifest, indent=1))
    assert all(max(m["size"]) <= CAP for m in manifest)
    print("staged", len(manifest), dict(sorted(Counter(m["tier"] for m in manifest).items())))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it.** `cd art/ui/hud && python export_quietcorners_upload.py`. Expected: `staged 125 {'A': 43, 'B': 75, 'C': 7}`.
  - This was dry-run while planning, with the same counts.
  - View `A/QcBookTL.png` and `A/DlRibbon.png` and check that the quadrant edges line up and the ribbon is intact.
- [ ] **Step 3: Commit** the script, the three folders and the manifest: "Quiet Corners art: the upload set (125 images, 1024 cap, tiers A/B/C)".
- [ ] **Step 4: Ask the owner to upload.**
  - The order is `A/` first (43 images: everything today needs at the Human trim), then `B/` (75), then `C/` (7, any time). The files go to group 15981569, keeping the file names.
  - Nothing waits on the upload: every piece falls back until Task S5.

### Task R2: The harness, the probe runner, the game-VM runner and the ids filler (25 min)

**Files:** Create `tools/quietcorners/harness/{install.py,dump.py,edit.py,client.py,snapshot.lua,restore.py,start_play.lua,probe.py,server.py,ids.py,test_ids.py}`.

**Interfaces:**
- `probe.py <Command> [lua literal args]` invokes `PlayerGui.NHQuietProbe` in the Client VM and prints JSON.
- `server.py <file.lua>` runs a file inside the game VM as a runtime Script; the file ends with `return <string>`.
- `ids.py <get-assets.json>...` fills the three art configs in `live/`.

- [ ] **Step 1: Copy R1's harness.** Copy these from `tools/belltower-r1/harness/` into `tools/quietcorners/harness/`: `install.py dump.py edit.py client.py snapshot.lua restore.py start_play.lua`.
  - In `dump.py`, change the `"belltower-r1"` folder to `"quietcorners"`.
  - In `install.py`'s docstring, change the path to `tools/quietcorners/live`.
  - Keep `start_play.lua` at `SetTime "12:30"`.
- [ ] **Step 2: Write `probe.py`.**

```python
"""usage: python -X utf8 -I probe.py <Command> [lua literal args...]   e.g. probe.py Get   probe.py Slip '{Title="Hi", Text="x"}'
Invokes PlayerGui.NHQuietProbe (Studio only, made by Controllers.Gui.HudState) in the Client VM; prints JSON."""
import os, subprocess, sys
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_probe.lua")
cmd, args = sys.argv[1], sys.argv[2:]
open(TMP, "w", encoding="utf-8").write(f'''local H = game:GetService("HttpService")
local B = game.Players.LocalPlayer.PlayerGui:FindFirstChild("NHQuietProbe")
if not B then return "NO PROBE" end
local r = B:Invoke("{cmd}"{", " + ", ".join(args) if args else ""})
local okj, j = pcall(H.JSONEncode, H, r)
return okj and j or tostring(r)''')
r = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", "placeId: 98950102230473", "Client", "@" + TMP],
                   capture_output=True, text=True, encoding="utf-8")
print(r.stdout.replace("\r", ""))
```

- [ ] **Step 3: Write `server.py`.** It uses the `snapshot.lua` pattern, which reaches the real services, unlike a sandbox require.

```python
"""usage: python -X utf8 -I server.py <file.lua>   runs the file INSIDE the game VM (a runtime Script in
ServerScriptService), so it reaches the real services. The file must end with `return <string>`. Play mode only."""
import os, subprocess, sys
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
HERE = os.path.dirname(os.path.abspath(__file__))
body = open(sys.argv[1], encoding="utf-8").read()
n = 2
while ("]" + "=" * n + "]") in body:
    n += 1
o, c = "[" + "=" * n + "[", "]" + "=" * n + "]"
lua = ('local S = Instance.new("Script")\n'
       f'S.Source = "local ok, r = pcall(function()\\n" .. {o}{body}{c} .. "\\nend) script:SetAttribute(\'Out\', ok and tostring(r) or (\'ERR \' .. tostring(r)))"\n'
       'S.Parent = game.ServerScriptService\n'
       'local t0 = os.clock()\n'
       'while S:GetAttribute("Out") == nil and os.clock() - t0 < 60 do task.wait(0.25) end\n'
       'local r = S:GetAttribute("Out")\nS:Destroy()\nreturn tostring(r)')
tmp = os.path.join(HERE, "_server.lua")
open(tmp, "w", encoding="utf-8").write(lua)
r = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", "placeId: 98950102230473", "Server", "@" + tmp],
                   capture_output=True, text=True, encoding="utf-8")
print(r.stdout.replace("\r", ""))
```

- [ ] **Step 4: Write `test_ids.py` (failing first), then `ids.py`.** The test:

```python
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
d = tempfile.mkdtemp()
cfg = os.path.join(d, "ReplicatedStorage.Config.QuietCornersArt.luau")
open(cfg, "w").write("return {\n\tSlip = { Human = 0; Vampire = 0 };\n\tCompassTicks = 0;\n\tBookTL = 5;\n}\n")
dump = os.path.join(d, "a.json")
json.dump([{"assetId": 9, "name": "QcSlipHuman"}, {"assetId": 8, "name": "QcSlipHuman"},
           {"assetId": 7, "name": "QcCompassTicks"}, {"assetId": 6, "name": "QcBookTL"}], open(dump, "w"))
out = subprocess.run([sys.executable, os.path.join(HERE, "ids.py"), "--live", d, dump], capture_output=True, text=True).stdout
t = open(cfg).read()
assert "Human = 9;" in t, t            # newest wins
assert "Vampire = 0;" in t, t          # not uploaded: stays 0
assert "CompassTicks = 7;" in t, t
assert "BookTL = 5;" in t, t           # already set: never overwritten
assert "missing" in out and "QcSlipVampire" in out, out
print("PASS test_ids")
```

Run `python tools/quietcorners/harness/test_ids.py`. Expected: it fails, because `ids.py` doesn't exist yet. Then write `ids.py`:

```python
"""Fill the Quiet Corners art ids from get-assets dumps (newest first), as fetched from a create.roblox.com tab:
itemconfiguration.roblox.com/v1/creations/get-assets?assetType=Image&groupId=15981569 (one page per file, 1.5 s apart).
usage: python -X utf8 -I ids.py [--live DIR] <page.json>...
Only `= 0` entries are filled. Per-race tables are one line: `\tSlip = { Human = 0; Priest = 0; ... };`."""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:]
live = os.path.join(os.path.dirname(HERE), "live")
if args and args[0] == "--live":
    live, args = args[1], args[2:]
ids = {}
for f in args:
    data = json.load(open(f, encoding="utf-8"))
    rows = data.get("data", data) if isinstance(data, dict) else data
    for row in rows:
        name, aid = row.get("name"), row.get("assetId") or row.get("id")
        if name and aid and name not in ids:
            ids[name] = int(aid)
PREFIX = {"QuietCornersArt": "Qc", "DialogueArt": "Dl", "EvidenceArt": "Ev"}
missing = []
for cfg, prefix in PREFIX.items():
    path = os.path.join(live, f"ReplicatedStorage.Config.{cfg}.luau")
    if not os.path.exists(path):
        continue
    out = []
    for line in open(path, encoding="utf-8").read().split("\n"):
        m = re.match(r"^\t(\w+) = \{(.*)\};", line)
        if m and m.group(1) not in ("Crest", "CrestFlip", "Slices", "Boxes"):
            piece = m.group(1)
            def fill(mm, piece=piece):
                key = f"{prefix}{piece}{mm.group(1)}"
                if mm.group(2) != "0":
                    return mm.group(0)
                if key in ids:
                    return f"{mm.group(1)} = {ids[key]}"
                missing.append(key)
                return mm.group(0)
            line = line[:m.start(2)] + re.sub(r"(\w+) = (\d+)", fill, m.group(2)) + line[m.end(2):]
        else:
            m = re.match(r"^\t(\w+) = (\d+);", line)
            if m and m.group(2) == "0":
                key = prefix + m.group(1)
                if key in ids:
                    line = f"\t{m.group(1)} = {ids[key]};" + line[m.end():]
                else:
                    missing.append(key)
        out.append(line)
    open(path, "w", encoding="utf-8", newline="").write("\n".join(out))
print("filled from", len(ids), "names;", "missing:", " ".join(missing) if missing else "none")
```

Run `test_ids.py` again. Expected: `PASS test_ids`.
- [ ] **Step 5: Commit** `tools/quietcorners/harness` (no underscore files): "Quiet Corners: harness, client probe runner, game-VM runner, ids filler (tested)".

### Task R3: The pure rules and the art configs (45 min, TDD; the check runs in S2)

**Files:**
- Create: `…/live/ReplicatedStorage.Functions.QuietCorners.luau`
- Create: `…/live/ReplicatedStorage.Config.{QuietCornersArt,DialogueArt,EvidenceArt}.luau`
- Test: `tools/quietcorners/checks/qc_pure.lua`

**Interfaces:** Produces these members of `Functions.QuietCorners`. All are pure; `Vector2` is the only engine type used.

| Member | Returns |
|---|---|
| `MIN_TEXT`, `RACES`, `CLIQUES`, `GHOST` (0.65), `FOCUS` (0.65), `CALM_AFTER` (6), `COMBAT_FOR` (4), `WAKE_FOR` (4), `FLIP` | constants |
| `Race(R)` | a valid race, else `"Human"` |
| `Image(Art, Piece, Race?)` | `rbxassetid://` string: race → Human → nil (nil = draw the kit fallback) |
| `CliqueOf(Npc)` | `Npc.Clique`, or the faction's clique (Vigil, CrimsonCourt → Court), or nil |
| `Crest(Art, Clique, Flip?)` | the clique's crest, else `Unaffiliated`; never the Seal |
| `FlipOffset(I)` | `ImageRectOffset` for frame I (4 x 4 of 256) |
| `Mode(M)` | `"Always"`, `"Ghost"` or `"Vanish"` (default Ghost) |
| `State(Inputs)` | Cut > Menu > Dialogue > Lesson > Combat > Calm > Active |
| `HudTarget(State, Mode, Cluster, Awake)` | the cluster's GroupTransparency |
| `SlipsQueued(State)`, `Danger(Kind)`, `MaxSlips(Phone)`, `Waiting(N)`, `SlipOpen(Data)`, `Ellipsize(Text, Fits)` | the slip rules |
| `Nearest(Dists)`, `KeySize(Key)`, `TagWidth(TextW)`, `Phone(Viewport)` | the prompt and layout rules |
| `Tone(T)`, `CardSub(Clique, Role, Relation, Fits)` | the dialogue lines |
| `Wall(Case, Saved, Pins)`, `Pin(Pins, Q, Slot, Clue)`, `Unpin(Pins, Q)`, `Miss(M, Q)`, `ShowHint(M, Q)` | the Evidence Wall model |

- [ ] **Step 1: Write the failing test** `tools/quietcorners/checks/qc_pure.lua`:

```lua
local RS = game.ReplicatedStorage
local Mod = RS:FindFirstChild("Functions") and RS.Functions:FindFirstChild("QuietCorners")
if not Mod then return "FAIL Functions.QuietCorners missing" end
local QC = require(Mod:Clone())
local Fails = {}
local function Eq(Got, Want, What) if Got ~= Want then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end
-- races and art (§12 fallback: race -> Human -> kit)
Eq(QC.Race("Wraith"), "Wraith", "race ok") Eq(QC.Race("Dragon"), "Human", "race unknown") Eq(QC.Race(nil), "Human", "race nil")
local Art = { Slip = { Human = 11, Vampire = 12, Ghoul = 0 }, Ticks = 13, Book = 0 }
Eq(QC.Image(Art, "Slip", "Vampire"), "rbxassetid://12", "per race") Eq(QC.Image(Art, "Slip", "Ghoul"), "rbxassetid://11", "race 0 -> Human")
Eq(QC.Image(Art, "Slip", "Priest"), "rbxassetid://11", "race missing -> Human") Eq(QC.Image(Art, "Ticks"), "rbxassetid://13", "shared")
Eq(QC.Image(Art, "Book"), nil, "0 = kit fallback") Eq(QC.Image(Art, "Nope"), nil, "missing piece")
Eq(QC.Image({ Slip = { Human = 0 } }, "Slip", "Wraith"), nil, "no Human = kit fallback")
-- crests: the Unaffiliated rule (spec §8)
local D = { Crest = { Ink = 1, Unaffiliated = 9 }, CrestFlip = { Ink = 2, Unaffiliated = 10 } }
Eq(QC.Crest(D, "Ink"), "rbxassetid://1", "crest Ink") Eq(QC.Crest(D, "Ink", true), "rbxassetid://2", "flip Ink")
Eq(QC.Crest(D, nil, true), "rbxassetid://10", "no clique = Unaffiliated") Eq(QC.Crest(D, "Vigil"), "rbxassetid://9", "no art = Unaffiliated")
Eq(QC.Crest(D, "Seal"), "rbxassetid://9", "never anything else")
Eq(QC.CliqueOf({ Clique = "Pack" }), "Pack", "clique field") Eq(QC.CliqueOf({ Faction = "CrimsonCourt" }), "Court", "faction Court")
Eq(QC.CliqueOf({ Faction = "Vigil" }), "Vigil", "faction Vigil") Eq(QC.CliqueOf({ Role = "Custodian" }), nil, "staff")
Eq(QC.FlipOffset(0), Vector2.new(0, 0), "frame 0") Eq(QC.FlipOffset(5), Vector2.new(256, 256), "frame 5")
Eq(QC.FlipOffset(15), Vector2.new(768, 768), "frame 15") Eq(QC.FlipOffset(99), Vector2.new(768, 768), "clamp")
-- the HUD state (spec §2)
local function St(T) T.Now = T.Now or 100 return QC.State(T) end
Eq(St({ LastActive = 99 }), "Active", "active") Eq(St({ LastActive = 94 }), "Calm", "calm after 6 s")
Eq(St({ LastActive = 99, CombatUntil = 101 }), "Combat", "combat") Eq(St({ LastActive = 99, CombatUntil = 101, Dialogue = true }), "Dialogue", "dialogue over combat")
Eq(St({ Menu = true, Dialogue = true }), "Menu", "menu over dialogue") Eq(St({ Cut = true, Menu = true }), "Cut", "cut over all")
Eq(St({ Lesson = true, LastActive = 99 }), "Lesson", "lesson")
Eq(QC.Mode("Vanish"), "Vanish", "mode") Eq(QC.Mode("Loud"), "Ghost", "mode default")
Eq(QC.HudTarget("Calm", "Ghost", "Compass", false), 0.65, "ghost") Eq(QC.HudTarget("Calm", "Vanish", "Vitals", false), 1, "vanish")
Eq(QC.HudTarget("Calm", "Always", "TopLeft", false), 0, "always") Eq(QC.HudTarget("Calm", "Ghost", "Compass", true), 0, "awake")
Eq(QC.HudTarget("Combat", "Ghost", "Vitals", false), 0, "combat vitals") Eq(QC.HudTarget("Combat", "Always", "TopLeft", false), 0.65, "combat focus")
Eq(QC.HudTarget("Dialogue", "Always", "Vitals", true), 1, "dialogue hides") Eq(QC.HudTarget("Lesson", "Ghost", "TopLeft", false), 0, "lesson top-left")
Eq(QC.HudTarget("Lesson", "Ghost", "Compass", false), 1, "lesson compass") Eq(QC.HudTarget("Active", "Vanish", "Compass", false), 0, "active")
-- slips (spec §3)
Eq(QC.SlipsQueued("Combat"), true, "queue in combat") Eq(QC.SlipsQueued("Calm"), false, "show in calm") Eq(QC.SlipsQueued("Menu"), true, "queue in menu")
Eq(QC.Danger("Bad"), true, "danger") Eq(QC.Danger("Warning"), false, "warning is an event")
Eq(QC.MaxSlips(false), 3, "max pc") Eq(QC.MaxSlips(true), 2, "max phone") Eq(QC.Waiting(2), "2 waiting", "stub") Eq(QC.Waiting(0), "", "no stub")
Eq(QC.SlipOpen({ Title = "Text from Odette Marsh" }), "Texts", "open texts") Eq(QC.SlipOpen({ Title = "New insight" }), "Evidence", "open evidence")
Eq(QC.SlipOpen({ Title = "Hi", Open = "Journal" }), "Journal", "explicit") Eq(QC.SlipOpen({ Title = "Yen" }), nil, "not routed")
Eq(QC.SlipOpen({ Open = "Locker" }), nil, "unknown route")
Eq(QC.Ellipsize("one two three", function(S) return #S <= 10 end), "one two…", "ellipsize") Eq(QC.Ellipsize("short", function() return true end), "short", "fits")
-- prompts
Eq(QC.Nearest({ a = 9, b = 3, c = 7 }), "b", "nearest") Eq(QC.Nearest({}), nil, "none")
Eq(QC.KeySize("E"), 22, "key 1") Eq(QC.KeySize("TAP"), 20, "key 3")
Eq(QC.TagWidth(100), 320, "tag min") Eq(QC.TagWidth(300), 390, "tag grows") Eq(QC.TagWidth(900), 520, "tag max")
Eq(QC.Phone(Vector2.new(844, 390)), true, "phone") Eq(QC.Phone(Vector2.new(1920, 1080)), false, "pc")
-- dialogue
Eq(QC.Tone("Sly"), "Sly", "tone") Eq(QC.Tone("Rude"), nil, "no tone")
local Fit30 = function(S) return #S <= 30 end
Eq(QC.CardSub("The Ink Club", "second year", nil, Fit30), "The Ink Club · second year", "sub")
Eq(QC.CardSub("The Ink Club", "second year", "Friendly", Fit30), "The Ink Club · second year", "relation dropped first")
Eq(QC.CardSub(nil, "Custodian", "Friendly", Fit30), "Custodian · Friendly", "staff")
-- the Evidence Wall (spec §7)
local Case = { Clues = { A = { Name = "a", Kind = "Note", Order = 1 }, B = { Name = "b", Kind = "Photo", Order = 2 },
	C = { Name = "c", Kind = "Record", Order = 3 }, H = { Name = "h", Kind = "Record", Order = 4, Hidden = true } },
	Questions = { { Id = "Q1", Ask = "one?" }, { Id = "Q2", Ask = "two?" }, { Id = "Q3", Ask = "three?", Bonus = true } } }
local W = QC.Wall(Case, { Clues = { A = true, B = true }, Insights = { { Id = "Q1", Text = "yes", A = "A", B = "B" } } }, {})
Eq(#W.Clues, 3, "hidden clue not shown until found") Eq(W.Clues[1].Id, "A", "order") Eq(W.Clues[2].Kind, "Object", "photo without a picture -> Object")
Eq(W.Clues[3].Found, false, "C missing") Eq(W.Questions[1].State, "Answered", "Q1 answered") Eq(W.Questions[2].State, "Empty", "Q2 empty")
Eq(W.Progress, "Clues 2 of 3 · Answered 1 of 2", "progress") Eq(W.Ready, false, "not ready")
local Pins, Send = QC.Pin({}, "Q2", 1, "A") Eq(Send, nil, "half pinned")
Eq(QC.Wall(Case, { Clues = { A = true } }, Pins).Questions[2].State, "Half", "half state")
Pins, Send = QC.Pin(Pins, "Q2", 2, "A") Eq(Send, nil, "one clue twice in a question isn't a pair") Eq(Pins.Q2[1], nil, "moved to slot 2")
Pins, Send = QC.Pin(Pins, "Q2", 1, "C") Eq(Send and Send.Question, "Q2", "pair sent") Eq(Send and Send.A, "C", "pair A") Eq(Send and Send.B, "A", "pair B")
Eq(QC.Unpin(Pins, "Q2").Q2, nil, "unpin")
W = QC.Wall(Case, { Clues = { A = true, B = true, C = true }, Insights = { { Id = "Q1" }, { Id = "Q2" } } }, {})
Eq(W.Ready, true, "ready without the bonus")
local M = {} M = QC.Miss(M, "Q2") Eq(QC.ShowHint(M, "Q2"), false, "1 miss") M = QC.Miss(M, "Q2") Eq(QC.ShowHint(M, "Q2"), true, "2 misses")
-- the configs exist, and the crests are already filled
local Cfg = RS:FindFirstChild("Config")
for _, N in { "QuietCornersArt", "DialogueArt", "EvidenceArt" } do if not (Cfg and Cfg:FindFirstChild(N)) then table.insert(Fails, "Config." .. N .. " missing") end end
if Cfg and Cfg:FindFirstChild("DialogueArt") then
	local DA = require(Cfg.DialogueArt:Clone())
	for _, K in { "Ink", "Vigil", "Court", "Athletes", "Delinquents", "Pack", "Ordinary", "Choir", "Unaffiliated" } do
		Eq(type(DA.Crest[K]) == "number" and DA.Crest[K] > 0, true, "crest id " .. K) Eq(type(DA.CrestFlip[K]) == "number" and DA.CrestFlip[K] > 0, true, "flip id " .. K)
	end
end
return #Fails == 0 and "PASS qc_pure" or ("FAIL\n" .. table.concat(Fails, "\n"))
```

- [ ] **Step 2: Write `ReplicatedStorage.Functions.QuietCorners.luau`:**

```lua
--!strict
--[[ (2.38) Quiet Corners: the pure rules (spec docs/superpowers/specs/2026-11-21-quiet-corners-ui-design.md).
	No services, no instances (Vector2 only). Read by Controllers.Gui.{HudState, Notifications, PromptUi, Compass, Dialogue,
	EvidenceWall, QuestJournal}. Tested by tools/quietcorners/checks/qc_pure.lua in the Edit VM. ]]
local QC = {}

QC.MIN_TEXT = 20
QC.RACES = { "Human", "Priest", "Vampire", "Werewolf", "Ghoul", "Wraith" }
QC.CLIQUES = { "Vigil", "Court", "Athletes", "Delinquents", "Pack", "Ordinary", "Choir", "Ink" }
QC.FACTION_CLIQUE = { Vigil = "Vigil", CrimsonCourt = "Court" } :: { [string]: string }
QC.TONES = { Kind = true, Sly = true, Threat = true, Ask = true } :: { [string]: boolean }
QC.GHOST = 0.65      -- Ghost: 35% visible
QC.FOCUS = 0.65      -- combat: the top-left and the compass at 35%
QC.CALM_AFTER = 6
QC.COMBAT_FOR = 4
QC.WAKE_FOR = 4
QC.FLIP = { Frame = 256, Cols = 4, Frames = 16, Fps = 15 }

local function valid(List: { string }, V: any): boolean return typeof(V) == "string" and table.find(List, V) ~= nil end
local function asset(Id: any): string? return if typeof(Id) == "number" and Id > 0 then "rbxassetid://" .. Id else nil end

function QC.Race(R: any): string return if valid(QC.RACES, R) then R else "Human" end

-- Art[Piece] is an id (a shared piece) or { [Race] = id }; a missing race falls back to Human; nil = the kit fallback
function QC.Image(Art: any, Piece: string, Race: any?): string?
	local V = Art and Art[Piece]
	if typeof(V) == "table" then return asset(V[QC.Race(Race)]) or asset(V.Human) end
	return asset(V)
end

function QC.CliqueOf(Npc: any): string?
	if typeof(Npc) ~= "table" then return nil end
	if valid(QC.CLIQUES, Npc.Clique) then return Npc.Clique end
	return QC.FACTION_CLIQUE[Npc.Faction or ""]
end

-- the speaker's crest: never empty and never the school Seal; no clique (staff, townsfolk, new students) = Unaffiliated
function QC.Crest(Art: any, Clique: any, Flip: boolean?): string?
	local Set = Art and Art[if Flip then "CrestFlip" else "Crest"]
	if typeof(Set) ~= "table" then return nil end
	return asset(Set[if valid(QC.CLIQUES, Clique) then Clique else "Unaffiliated"]) or asset(Set.Unaffiliated)
end

function QC.FlipOffset(I: number): Vector2
	local N = math.clamp(math.floor(I), 0, QC.FLIP.Frames - 1)
	return Vector2.new((N % QC.FLIP.Cols) * QC.FLIP.Frame, (N // QC.FLIP.Cols) * QC.FLIP.Frame)
end

function QC.Mode(M: any): string return if M == "Always" or M == "Vanish" then M else "Ghost" end

function QC.State(I: any): string
	if I.Cut then return "Cut" end
	if I.Menu then return "Menu" end
	if I.Dialogue then return "Dialogue" end
	if I.Lesson then return "Lesson" end
	if (I.CombatUntil or 0) > I.Now then return "Combat" end
	if I.Now - (I.LastActive or -math.huge) >= QC.CALM_AFTER then return "Calm" end
	return "Active"
end

-- a cluster ("TopLeft", "Compass", "Vitals"): its GroupTransparency. Awake = it changed, was hovered, or Tab/View peeked.
function QC.HudTarget(State: string, Mode: string, Cluster: string, Awake: boolean?): number
	if State == "Cut" or State == "Dialogue" or State == "Menu" then return 1 end
	if State == "Lesson" then return if Cluster == "TopLeft" then 0 else 1 end
	if State == "Combat" then return if Cluster == "Vitals" or Awake then 0 else QC.FOCUS end
	if State == "Calm" and not Awake then
		if Mode == "Always" then return 0 end
		if Mode == "Vanish" then return 1 end
		return QC.GHOST
	end
	return 0
end

function QC.SlipsQueued(State: string): boolean return State ~= "Active" and State ~= "Calm" end
function QC.Danger(Kind: any): boolean return Kind == "Bad" end
function QC.MaxSlips(Phone: boolean): number return if Phone then 2 else 3 end
function QC.Waiting(N: number): string return if N > 0 then N .. " waiting" else "" end

function QC.SlipOpen(Data: any): string?
	if typeof(Data) ~= "table" then return nil end
	if Data.Open == "Texts" or Data.Open == "Evidence" or Data.Open == "Journal" then return Data.Open end
	if Data.Open ~= nil then return nil end
	local T = tostring(Data.Title or "")
	if T:find("^Text from") then return "Texts" end
	if T == "New insight" or T == "Case breakthrough" or T:find("^Clue") then return "Evidence" end
	if T:find("^Quest") or T:find("^Objective") then return "Journal" end
	return nil
end

-- shorten at a word with "…" until Fits says yes (Fits measures with TextService on the client)
function QC.Ellipsize(Text: string, Fits: (string) -> boolean): string
	if Fits(Text) then return Text end
	local Words = string.split(Text, " ")
	while #Words > 1 do
		table.remove(Words)
		local T = table.concat(Words, " ") .. "…"
		if Fits(T) then return T end
	end
	return "…"
end

function QC.Nearest(Dists: { [any]: number }): any?
	local Best, D = nil, math.huge
	for K, V in Dists do if V < D then Best, D = K, V end end
	return Best
end
function QC.KeySize(Key: string): number return if (utf8.len(Key) or #Key) == 1 then 22 else 20 end
-- PromptTag's text box is 0.11 .. 0.90 of its width (measured from the art); the tag is a 9-slice, 320 to 520 wide
function QC.TagWidth(TextW: number): number return math.clamp(math.ceil((TextW + 8) / 0.79), 320, 520) end
function QC.Phone(Vp: Vector2): boolean return math.min(Vp.X, Vp.Y) < 600 end

function QC.Tone(T: any): string? return if typeof(T) == "string" and QC.TONES[T] then T else nil end

-- the card's second line: drop the relation first, then the clique, until it fits
function QC.CardSub(Clique: string?, Role: string?, Relation: string?, Fits: (string) -> boolean): string
	local function join(...) local P = {} for I = 1, select("#", ...) do local S = select(I, ...) if S and S ~= "" then table.insert(P, S) end end return table.concat(P, " · ") end
	for _, T in { join(Clique, Role, Relation), join(Clique, Role), join(Role, Relation), join(Role), join(Clique) } do
		if T ~= "" and Fits(T) then return T end
	end
	return join(Role) ~= "" and join(Role) or join(Clique)
end

-- the Evidence Wall's model for one case. Saved = Quests.Cases[CaseId] ({ Clues, Insights, Solved, SolvedText }); Pins = client-only
function QC.Wall(Case: any, Saved: any, Pins: any)
	Saved = Saved or {}
	Pins = Pins or {}
	local Found = Saved.Clues or {}
	local Insight = {}
	for _, I in Saved.Insights or {} do if I.Id then Insight[I.Id] = I end end
	local Clues, NFound, NTotal = {}, 0, 0
	for Id, C in Case.Clues or {} do
		local Has = Found[Id] ~= nil and Found[Id] ~= false
		if C.Hidden and not Has then continue end
		NTotal += 1
		if Has then NFound += 1 end
		local Kind = if C.Kind == "Photo" and not C.Photo then "Object"
			elseif C.Kind == "Note" or C.Kind == "Record" or C.Kind == "Object" or C.Kind == "Photo" then C.Kind else "Note"
		table.insert(Clues, { Id = Id; Name = C.Name; Where = C.Where; Text = C.Text; Kind = Kind; Photo = C.Photo; Found = Has; Order = C.Order or 99 })
	end
	table.sort(Clues, function(A, B)
		if A.Found ~= B.Found then return A.Found end
		if A.Order ~= B.Order then return A.Order < B.Order end
		return A.Id < B.Id
	end)
	local Questions, NAns, NNeed = {}, 0, 0
	for _, Q in Case.Questions or {} do
		local I = Insight[Q.Id]
		local Row = Pins[Q.Id] or {}
		local N = (if Row[1] then 1 else 0) + (if Row[2] then 1 else 0)
		if not Q.Bonus then
			NNeed += 1
			if I then NAns += 1 end
		end
		table.insert(Questions, { Id = Q.Id; Ask = Q.Ask; Hint = Q.Hint; Bonus = Q.Bonus == true;
			State = if I then "Answered" elseif N == 2 then "Full" elseif N == 1 then "Half" else "Empty";
			Insight = I and I.Text; A = (I and I.A) or Row[1]; B = (I and I.B) or Row[2] })
	end
	return { Clues = Clues; Questions = Questions; Found = NFound; Total = NTotal; Answered = NAns; Needed = NNeed;
		Ready = NNeed > 0 and NAns >= NNeed; Solved = Saved.Solved == true; SolvedText = Saved.SolvedText;
		Progress = ("Clues %d of %d · Answered %d of %d"):format(NFound, NTotal, NAns, NNeed) }
end

-- pin a clue in a question's slot (1 or 2); returns the new pins and, once both slots hold different clues, the pair to send
function QC.Pin(Pins: any, Q: string, Slot: number, Clue: string)
	local P = table.clone(Pins or {})
	local Row = table.clone(P[Q] or {})
	if Row[3 - Slot] == Clue then Row[3 - Slot] = nil end
	Row[Slot] = Clue
	P[Q] = Row
	if Row[1] and Row[2] then return P, { Question = Q; A = Row[1]; B = Row[2] } end
	return P, nil
end
function QC.Unpin(Pins: any, Q: string) local P = table.clone(Pins or {}) P[Q] = nil return P end
function QC.Miss(M: any, Q: string) local C = table.clone(M or {}) C[Q] = (C[Q] or 0) + 1 return C end
function QC.ShowHint(M: any, Q: string): boolean return ((M or {})[Q] or 0) >= 2 end

return QC
```

- [ ] **Step 3: Write the three configs.** Per-race tables go on one line each (`ids.py` parses them). `Boxes` are text boxes as fractions of each piece's size, measured from the art in the mockup script. `Slices` are in the staged image's pixels.

`ReplicatedStorage.Config.QuietCornersArt.luau`:

```lua
--[[ (2.38) Quiet Corners art ids (group 15981569). Staged by art/ui/hud/export_quietcorners_upload.py as
	Qc<Piece><Race>.png / Qc<Piece>.png; filled by tools/quietcorners/harness/ids.py. 0 = not uploaded:
	Functions.QuietCorners.Image falls back to the Human trim, then the controller draws today's kit art. ]]
return {
	Slip = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 };
	PromptCap = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 };
	PromptTag = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 };
	PromptPip = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 };
	CompassStrip = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 };
	CompassLubber = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 };
	SkipRing = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 };
	BookCorner = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 };
	PlateTrim = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 }; -- tier C: the Bell Tower plate, after R2
	PromptCapFill = 0;
	SkipRingFill = 0;
	CompassTicks = 0;      -- greyscale, tinted bone; 600 x 48 = 30 degrees
	BookTab = 0;
	BookTabOn = 0;
	BookTL = 0;            -- the book, in quadrants (1024 x 582 each)
	BookTR = 0;
	BookBL = 0;
	BookBR = 0;
	Slices = {
		PromptTag = Rect.new(80, 16, 560, 112);   -- 640 x 128
	};
	Boxes = {
		Slip = { 0.14, 0.06, 0.97, 0.78 };
		PromptTag = { 0.11, 0.08, 0.90, 0.92 };
		PromptCap = { 0.12, 0.15, 0.88, 0.85 };
		CompassStrip = { 24 / 560, 8.4 / 52, 536 / 560, 43.6 / 52 };
		BookLeft = { 110 / 2048, 96 / 1164, 1000 / 2048, 1068 / 1164 };
		BookRight = { 1170 / 2048, 96 / 1164, 1938 / 2048, 1068 / 1164 };
	};
}
```

`ReplicatedStorage.Config.DialogueArt.luau`. Its crest ids are copied from `art/ui/hud/out/dialogue/ids.json`; the ids filler skips the `Crest` and `CrestFlip` lines.

```lua
--[[ (2.38) Dialogue art ids (group 15981569). Crests uploaded 2026-11-22 (art/ui/hud/out/dialogue/ids.json).
	Staged as Dl<Piece>[<Race>].png; filled by tools/quietcorners/harness/ids.py. ]]
return {
	Crest = { Athletes = 125526182544004; Choir = 115415145538112; Court = 131064465186809; Delinquents = 89893229015938; Ink = 119107806148335; Ordinary = 103447597440204; Pack = 129141861458358; Unaffiliated = 133870303290329; Vigil = 114860166389267 };
	CrestFlip = { Athletes = 76316749978761; Choir = 107120128277090; Court = 87270020294102; Delinquents = 122740491517693; Ink = 101114883166304; Ordinary = 119699734867052; Pack = 105408956760891; Unaffiliated = 92428028361207; Vigil = 74478677001800 };
	CallingCard = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 };
	ReplyTab = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 };
	ReplyTabOn = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 };
	Ribbon = 0;            -- 1024 x 140 (downscaled from 2048 x 280), a 9-slice
	Nib = 0;
	ToneKind = 0;
	ToneSly = 0;
	ToneThreat = 0;
	ToneAsk = 0;
	Slices = {
		Ribbon = Rect.new(120, 35, 904, 105);
	};
	Boxes = {
		CallingCard = { 235 / 1040, 34 / 240, 988 / 1040, 206 / 240 };
		Ribbon = { 0.10, 0.20, 0.90, 0.80 };
		ReplySocket = { 26 / 1000, 20 / 128, 114 / 1000, 108 / 128 };
		ReplyText = { 132 / 1000, 24 / 128, 948 / 1000, 104 / 128 };
	};
}
```

`ReplicatedStorage.Config.EvidenceArt.luau`:

```lua
--[[ (2.38) Evidence Wall art ids (group 15981569). Staged as Ev<Piece>[<Race>].png; filled by tools/quietcorners/harness/ids.py. ]]
return {
	CasePlate = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 };
	AnswerCard = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 };
	Lens = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 };
	Tack = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 };
	CardNote = 0;
	CardRecord = 0;
	CardObject = 0;
	CardPhoto = 0;
	CardMissing = 0;       -- greyscale, tinted chalk
	Slot = 0;
	QuestionSheet = 0;
	StampInk = 0;          -- a frame only: SOLVED is live text in it
	Thread = 0;            -- greyscale, tinted crimson
	Cork = 0;              -- tier C (unused: the wall is drawn in quadrants)
	WallTL = 0;
	WallTR = 0;
	WallBL = 0;
	WallBR = 0;
	Boxes = {
		CasePlate = { 64 / 1600, 26 / 200, 1536 / 1600, 174 / 200 };
		SheetAsk = { 22 / 720, 4 / 252, 698 / 720, 0.195 };
		SheetBody = { 30 / 720, 0.24, 696 / 720, 240 / 252 };
		CardNote = { 38 / 220, 24 / 300, 210 / 220, 292 / 300 };
		CardRecord = { 12 / 220, 8 / 300, 205 / 220, 292 / 300 };
		CardObject = { 12 / 220, 48 / 300, 208 / 220, 292 / 300 };
		CardPhoto = { 14 / 220, 196 / 300, 206 / 220, 292 / 300 };
		CardMissing = { 14 / 220, 14 / 300, 206 / 220, 286 / 300 };
	};
}
```

- [ ] **Step 4: Commit** "Quiet Corners: Functions.QuietCorners (pure rules), the three art configs, qc_pure check". The check runs in S2.

### Task R4: HudState, HudMode, and the three clusters (50 min)

**Files:**
- Create: `…/live/…Controllers.Gui.HudState.luau`
- Modify (from `base/`): `…/live/…Controllers.Gui.{KitHud,TopBar,SettingsMenu}.luau`
- Modify (from the newest `ReplicatedStorage.UI.Settings` mirror, `tools/weapon-visibility/`): `…/live/ReplicatedStorage.UI.Settings.luau`. S1 rebases this onto the fresh dump.
- Test: `tools/quietcorners/checks/qc_state.lua`

**Interfaces:**
- **HudState produces:**
  - `Get(): string` and `Changed` (BindableEvent, fired with the state).
  - `Adopt(Gui, Cluster, Names?, Edge, Height): CanvasGroup`, `Wake(Cluster?)`, `Poke(Kind)` and `SlipsQueued(): boolean`.
  - `Probe(Name, Fn)`, which registers a probe command.
  - The Player attribute `NHHudState`.
  - It reads `NHHudMode`, `InDialogue`, `NHMenuOpen`, `PlayerGui.NHCineUI.Enabled`, `PlayerGui.Lesson`, `CombatTagUntil`, the Humanoid health and the `Posture` attribute.
- **The probe's built-in commands:** `Get`, `Force(State?)`, `Poke(Kind)`, `Wake(Cluster?)` and `Idle`.
- **`UI.Settings`:** `HudMode` (default `"Ghost"`, `Choices.HudMode = { "Always", "Ghost", "Vanish" }`), applied as `NHHudMode`.

- [ ] **Step 1: Write the failing check** `tools/quietcorners/checks/qc_state.lua` (Client VM, in Play):

```lua
local P = game.Players.LocalPlayer
local PG = P:WaitForChild("PlayerGui")
local Probe = PG:FindFirstChild("NHQuietProbe")
if not Probe then return "FAIL no NHQuietProbe" end
local Fails, Notes = {}, {}
local function Ok(C, W) if not C then table.insert(Fails, W) end end
local function Near(A, B) return typeof(A) == "number" and math.abs(A - B) < 0.01 end
local function G() return Probe:Invoke("Get") end
local ModeWas = P:GetAttribute("NHHudMode")
local S = G()
for _, N in { "TopLeft", "Compass", "Vitals" } do Ok(S.Groups[N] ~= nil, "cluster not adopted: " .. N) end
Ok(PG.ClockHud:FindFirstChild("QcFade") == nil and PG.QuestTracker:FindFirstChild("QcFade") == nil, "the Bell Tower must not be adopted (ruling 2)")
Ok(PG.KitHud:FindFirstChild("Downed") and PG.KitHud.Downed.Parent == PG.KitHud, "DOWNED must stay outside the fade")
-- Ghost / Vanish / Always in calm
P:SetAttribute("NHHudMode", "Ghost") Probe:Invoke("Force", nil) Probe:Invoke("Idle") task.wait(0.8) S = G()
Ok(S.State == "Calm", "calm: " .. tostring(S.State)) Ok(P:GetAttribute("NHHudState") == "Calm", "NHHudState attribute")
for _, N in { "TopLeft", "Compass", "Vitals" } do Ok(Near(S.Targets[N], 0.65), "ghost " .. N .. " " .. tostring(S.Targets[N])) end
P:SetAttribute("NHHudMode", "Vanish") task.wait(0.4) S = G() Ok(S.Targets.Compass == 1, "vanish compass")
local Thread = PG.KitHud:FindFirstChild("QcThread", true) Ok(Thread and Thread.Visible, "Vanish health thread")
P:SetAttribute("NHHudMode", "Always") task.wait(0.4) S = G() Ok(S.Targets.Compass == 0, "always compass")
-- combat focus, and its end 4 s after the last hit
P:SetAttribute("NHHudMode", "Ghost") Probe:Invoke("Poke", "Hit") task.wait(0.4) S = G()
Ok(S.State == "Combat", "combat: " .. tostring(S.State)) Ok(S.Targets.Vitals == 0 and Near(S.Targets.TopLeft, 0.65) and Near(S.Targets.Compass, 0.65), "combat targets")
task.wait(4.6) S = G() Ok(S.State ~= "Combat", "combat still on 4.6 s after the hit")
-- dialogue and menu hide all three
P:SetAttribute("InDialogue", true) task.wait(0.4) S = G() Ok(S.State == "Dialogue" and S.Targets.Compass == 1 and S.Targets.TopLeft == 1, "dialogue")
P:SetAttribute("InDialogue", nil)
P:SetAttribute("NHMenuOpen", true) task.wait(0.4) S = G() Ok(S.State == "Menu" and S.Targets.Vitals == 1, "menu") P:SetAttribute("NHMenuOpen", nil)
-- a cut: the real NHCineUI if built, else forced; leaving it lands on Calm, not Active
local Cine = PG:FindFirstChild("NHCineUI")
if Cine and not Cine.Enabled then Cine.Enabled = true task.wait(0.4) S = G() Ok(S.State == "Cut", "cut via NHCineUI") Cine.Enabled = false
else Probe:Invoke("Force", "Cut") task.wait(0.2) Probe:Invoke("Force", nil) table.insert(Notes, "cut forced (NHCineUI not built yet)") end
task.wait(0.4) S = G() Ok(S.State == "Calm", "after a cut: " .. tostring(S.State) .. " (spec: calm, not full)")
-- waking one cluster
Probe:Invoke("Wake", "Compass") task.wait(0.8) S = G()
Ok(S.Targets.Compass == 0 and Near(S.Targets.TopLeft, 0.65), "wake only the compass")
local Fade = PG.NHCompass:FindFirstChild("QcFade") Ok(Fade and Fade:IsA("CanvasGroup") and Fade.GroupTransparency < 0.05, "the compass group follows")
-- Settings: HudMode is a real setting
local Settings = require(game.ReplicatedStorage.UI.Settings)
Ok(Settings.Choices and Settings.Choices.HudMode and #Settings.Choices.HudMode == 3, "Settings.Choices.HudMode")
P:SetAttribute("NHHudMode", ModeWas)
return (#Fails == 0 and "PASS qc_state" or ("FAIL\n" .. table.concat(Fails, "\n"))) .. "\n" .. table.concat(Notes, "\n")
```

- [ ] **Step 2: Write `Controllers.Gui.HudState.luau`:**

```lua
--[[
	HudState (client). Controllers.Gui.HudState  (2.38, Quiet Corners QC1)
	Spec: docs/superpowers/specs/2026-11-21-quiet-corners-ui-design.md §2. Rules: ReplicatedStorage.Functions.QuietCorners.

	One HUD state: Active, Calm (6 s with no movement), Combat (a hit taken, a Posture change, CombatTagUntil; it ends 4 s after
	the last), Cut (PlayerGui.NHCineUI is on), Dialogue (InDialogue), Lesson (PlayerGui.Lesson), Menu (NHMenuOpen: the book,
	the Evidence Wall). Published as the Player attribute NHHudState. HudMode (Settings) arrives as NHHudMode.
	Clusters are CanvasGroups adopted from their controllers (Adopt): TopLeft (NHTopBar), Compass (NHCompass), Vitals
	(KitHud.Bottom). Only their GroupTransparency is tweened. The Bell Tower is never adopted (plan ruling 2).
	In a Cut, NHCineUI fades the same groups and puts them back; HudState waits and comes back at Calm (spec §2).
	Waking: Wake(Cluster) (a change in it) or hovering it = full for 4 s; Tab / View = every cluster; health under 25% keeps
	Vitals awake. Studio only: PlayerGui.NHQuietProbe (BindableFunction) for tools/quietcorners/checks.
	API: Get(), Changed, Adopt(Gui, Cluster, Names?, Edge, Height), Wake(Cluster?), Poke(Kind), SlipsQueued(), Probe(Name, Fn)
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")

local QC = require(ReplicatedStorage:WaitForChild("Functions"):WaitForChild("QuietCorners"))

local Player = Players.LocalPlayer
local Local = {}
local Shared = {}
Shared.Changed = Instance.new("BindableEvent")

local Clusters = {} :: { [string]: { Group: CanvasGroup, Target: number?, AwakeUntil: number } }
local State = "Active"
local LastActive = os.clock()
local CombatUntil = 0
local Forced: string? = nil
local Probes = {} :: { [string]: (...any) -> any }

function Local.Reduced(): boolean return Player:GetAttribute("NHReducedMotion") == true end

function Local.LowHealth(): boolean
	local C = Player.Character
	local H = C and C:FindFirstChildOfClass("Humanoid")
	return H ~= nil and H.MaxHealth > 0 and H.Health / H.MaxHealth < 0.25
end

function Local.Inputs()
	local PG = Player:FindFirstChild("PlayerGui")
	local Cine = PG and PG:FindFirstChild("NHCineUI")
	return {
		Cut = Cine ~= nil and (Cine :: any).Enabled == true;
		Menu = Player:GetAttribute("NHMenuOpen") == true;
		Dialogue = Player:GetAttribute("InDialogue") == true;
		Lesson = PG ~= nil and PG:FindFirstChild("Lesson") ~= nil;
		Now = os.clock(); CombatUntil = CombatUntil; LastActive = LastActive;
	}
end

function Local.Apply(Instant: boolean?)
	local Now = os.clock()
	local New = Forced or QC.State(Local.Inputs())
	if New ~= State then
		local Was = State
		State = New
		Player:SetAttribute("NHHudState", State)
		if Was == "Cut" then LastActive = -math.huge end -- back to calm, never a flash to full
		Shared.Changed:Fire(State)
	end
	if State == "Cut" then return end -- NHCineUI owns the fade
	local Mode = QC.Mode(Player:GetAttribute("NHHudMode"))
	local Low = Local.LowHealth()
	for Name, C in Clusters do
		if not C.Group.Parent then Clusters[Name] = nil continue end
		local T = QC.HudTarget(State, Mode, Name, C.AwakeUntil > Now or (Name == "Vitals" and Low))
		if T ~= C.Target then
			C.Target = T
			local Secs = if Instant then 0 elseif Local.Reduced() then 0.2 elseif State == "Calm" then 0.6 else 0.25
			TweenService:Create(C.Group, TweenInfo.new(Secs, Enum.EasingStyle.Sine), { GroupTransparency = T }):Play()
		end
	end
end

-- wrap a cluster's top-level pieces in one CanvasGroup, pinned to the top or bottom edge, full width, Height design px tall
function Shared.Adopt(Gui: ScreenGui, Cluster: string, Names: { string }?, Edge: string, Height: number): CanvasGroup
	local G = Gui:FindFirstChild("QcFade") :: CanvasGroup?
	if not G then
		local New = Instance.new("CanvasGroup")
		New.Name = "QcFade"
		New.BackgroundTransparency = 1
		New.AnchorPoint = Vector2.new(0, if Edge == "Bottom" then 1 else 0)
		New.Position = UDim2.fromScale(0, if Edge == "Bottom" then 1 else 0)
		New.Size = UDim2.new(1, 0, 0, Height)
		New.Parent = Gui
		G = New
	end
	local Group = G :: CanvasGroup
	for _, Child in Gui:GetChildren() do
		if Child ~= Group and Child:IsA("GuiObject") and (Names == nil or table.find(Names, Child.Name) ~= nil) then Child.Parent = Group end
	end
	Clusters[Cluster] = { Group = Group; Target = nil; AwakeUntil = 0 }
	Group.MouseEnter:Connect(function() Shared.Wake(Cluster) end)
	Local.Apply(true)
	return Group
end

function Shared.Wake(Cluster: string?)
	local Until = os.clock() + QC.WAKE_FOR
	for Name, C in Clusters do if Cluster == nil or Name == Cluster then C.AwakeUntil = Until end end
	Local.Apply()
end

function Shared.Poke(Kind: string)
	if Kind == "Hit" then CombatUntil = os.clock() + QC.COMBAT_FOR end
	Local.Apply()
end

function Shared.Get(): string return State end
function Shared.SlipsQueued(): boolean return QC.SlipsQueued(State) end
function Shared.Probe(Name: string, Fn: (...any) -> any) Probes[Name] = Fn end

function Local.BindCharacter(C: Model)
	local H = C:WaitForChild("Humanoid", 10) :: Humanoid?
	if not H then return end
	local Last = H.Health
	H.HealthChanged:Connect(function(V)
		if V < Last - 0.5 then Shared.Poke("Hit") end
		Last = V
		Local.Apply()
	end)
	for _, I in { C, H } do I:GetAttributeChangedSignal("Posture"):Connect(function() Shared.Poke("Hit") end) end
end

Probes.Get = function()
	local T, Gs = {}, {}
	for N, C in Clusters do T[N] = C.Target Gs[N] = C.Group:GetFullName() end
	return { State = State; Mode = QC.Mode(Player:GetAttribute("NHHudMode")); Targets = T; Groups = Gs }
end
Probes.Force = function(S: string?) Forced = S Local.Apply() return State end
Probes.Poke = function(K: string) Shared.Poke(K) return State end
Probes.Wake = function(C: string?) Shared.Wake(C) return true end
Probes.Idle = function() LastActive = -math.huge for _, C in Clusters do C.AwakeUntil = 0 end Local.Apply() return State end

function Shared.OnStart()
	Player:SetAttribute("NHHudState", State)
	if Player.Character then task.spawn(Local.BindCharacter, Player.Character) end
	Player.CharacterAdded:Connect(Local.BindCharacter)
	Player:GetAttributeChangedSignal("CombatTagUntil"):Connect(function() Shared.Poke("Hit") end)
	for _, A in { "NHHudMode", "InDialogue", "NHMenuOpen" } do Player:GetAttributeChangedSignal(A):Connect(function() Local.Apply() end) end
	UserInputService.InputBegan:Connect(function(Input)
		if Input.KeyCode == Enum.KeyCode.Tab or Input.KeyCode == Enum.KeyCode.ButtonSelect then Shared.Wake(nil) end
	end)
	local Acc = 0
	RunService.Heartbeat:Connect(function(Dt)
		Acc += Dt
		if Acc < 0.1 then return end
		Acc = 0
		local C = Player.Character
		local H = C and C:FindFirstChildOfClass("Humanoid")
		if H and H.MoveDirection.Magnitude > 0.1 and State ~= "Cut" then LastActive = os.clock() end
		Local.Apply()
	end)
	if RunService:IsStudio() then
		local PG = Player:WaitForChild("PlayerGui")
		local B = PG:FindFirstChild("NHQuietProbe") or Instance.new("BindableFunction")
		B.Name = "NHQuietProbe"
		B.OnInvoke = function(Cmd, ...)
			local Fn = Probes[Cmd]
			if not Fn then return { Error = "unknown command " .. tostring(Cmd) } end
			local Ok, R = pcall(Fn, ...)
			return if Ok then R else { Error = tostring(R) }
		end
		B.Parent = PG
	end
end

return Shared
```

- [ ] **Step 3: Adopt the clusters.**
  - **KitHud** (`base/`):
    - At the end of `Shared.OnStart`, after `Ui` is built, add `require(script.Parent.HudState).Adopt(Ui.Gui, "Vitals", { "Bottom" }, "Bottom", 420)`. 420 design px covers the touch lift.
    - In `Local.OnHealth`, `Local.Render` and `Local.SetYen` (only when `Animate`), add `pcall(function() require(script.Parent.HudState).Wake("Vitals") end)`.
    - **The Vanish thread:** in `Local.Build`, after `Downed`, add an ImageLabel `QcThread`, parented to `Gui` (outside the fade):
      - Image `QuietCorners.Image(EvidenceArt, "Thread")`, ImageColor3 `Colors.Crimson`. If the id is 0, use `Kit.Theme.Images.Divider` tinted crimson.
      - AnchorPoint (0.5, 1), Position (0.5, 0, 1, -2), Size `(600 * health, 4)`.
      - Visible only while `NHHudState == "Calm"` and `NHHudMode == "Vanish"`, listening to both attributes.
      - `Local.OnHealth` sets its width.
  - **TopBar** (`base/`): at the end of its `OnStart`, after the gui is built, add `require(script.Parent.HudState).Adopt(Gui, "TopLeft", nil, "Top", 140)`.
  - **Compass:** this goes in Task R7, as `Adopt(Gui, "Compass", { "Compass" }, "Top", 130)`.
- [ ] **Step 4: HudMode.**
  - In `UI.Settings`:
    - Add `HudMode = "Ghost",` to the defaults beside `ShowClock`.
    - Add `HudMode = { "Always", "Ghost", "Vanish" },` to `Settings.Choices`.
    - Add `HudMode = function(v) Players.LocalPlayer:SetAttribute("NHHudMode", v) end,` to the apply table beside `ShowClock`.
    - Add the line `HudMode -> LocalPlayer attribute NHHudMode, read by Controllers.Gui.HudState (2.38)` to the header.
  - In `SettingsMenu`'s Interface section, after `Show Clock`, add `Local.Cycle("HUD when idle", "HudMode", 5, function(V) return V end)`. If 5 collides, renumber the later rows by one.
- [ ] **Step 5: Commit** the five mirrors and `qc_state.lua`: "Quiet Corners QC1: HudState, HudMode, the TopLeft / Compass / Vitals clusters".

### Task R5: The slips (35 min)

**Files:** Modify `…/live/…Controllers.Gui.Notifications.luau` (rewrite of the visuals from `base/`). Test: `tools/quietcorners/checks/qc_slips.lua` and `tools/quietcorners/checks/qc_notify_server.lua`.

**Interfaces:**
- Consumes `Packets.Notify` (unchanged), `HudState` (`SlipsQueued`, `Changed`, `Probe`), `QuietCorners`, and `Config.QuietCornersArt`.
- For routing it calls `Phone.OpenApp("Texts")`, `EvidenceWall.Open(Case?)` and `QuestJournal.Toggle(true)`, each lazily through `pcall`.
- Probe commands: `Slip(Data)` (shows it as if it came from the server) and `Slips()`, which returns `{ Shown = { titles }, Waiting = n, Stub = text, X = px, Y = px }`.

**Build** (design px; ScreenGui `Notifications`, DisplayOrder 10, IgnoreGuiInset true, `Kit.AutoScale`):

| Piece | Spec |
|---|---|
| `Holder` | a transparent Frame, AnchorPoint (0, 0), Position (0, 24, 0, 80) on desktop and (0, 10, 0, 50) on phones (`QC.Phone`), Size (0, 400, 0, 272). UIListLayout, vertical, Padding 8, SortOrder LayoutOrder (newest = the lowest LayoutOrder, on top) |
| `Slip` | ImageButton 400 x 80, Image `Image(Art, "Slip", Race)`, AutoButtonColor false, `Active` only when routed, attribute `QcBox = "0.14,0.06,0.97,0.78"` |
| `Title` | TextLabel at (64, 8), size (324, 24): 22 px, `Theme.Fonts.Title` bold, Ink `Color3.fromRGB(40, 22, 16)`; `Kind` Bad or Warning uses InkRed `(130, 18, 24)` |
| `Detail` | TextLabel at (64, 34), size (324, 24): 20 px, InkDim `(92, 62, 46)`, `QC.Ellipsize` with `TextService:GetTextSize(..., 20, Font, 2000).X <= 324` |
| Stub | the same art with Title only: `QC.Waiting(n)`, LayoutOrder = math.huge |
| Fallback (no id) | ImageButton transparent + `Kit.Decorate(Slip, { ornament = "thin" })`; text in `Theme.Colors.Text` / `TextDim` |

- [ ] **Step 1: Write the failing check** `qc_slips.lua` (Client VM):

```lua
local P = game.Players.LocalPlayer
local PG = P.PlayerGui
local Probe = PG:FindFirstChild("NHQuietProbe")
if not Probe then return "FAIL no NHQuietProbe" end
local Fails = {}
local function Ok(C, W) if not C then table.insert(Fails, W) end end
Probe:Invoke("Force", "Active")
for I = 1, 4 do Probe:Invoke("Slip", { Title = "Slip " .. I; Text = "A detail line that is long enough to need shortening at a word boundary, surely"; Kind = "Info"; Duration = 30 }) end
task.wait(0.6)
local S = Probe:Invoke("Slips")
Ok(#S.Shown == 3, "max 3 shown, got " .. #S.Shown) Ok(S.Shown[1] == "Slip 4", "newest on top: " .. tostring(S.Shown[1]))
local Vp = workspace.CurrentCamera.ViewportSize
Ok(S.X < Vp.X * 0.25 and S.Y < Vp.Y * 0.3, "top-left")
for _, L in PG.Notifications:GetDescendants() do
	if L:IsA("TextLabel") and L.Text ~= "" and L.Visible then Ok(L.TextSize >= 20 and L.TextFits, L.Name .. " size/fit " .. L.TextSize) end
	if L:IsA("ImageLabel") or L:IsA("ImageButton") then Ok(L.Image ~= require(game.ReplicatedStorage.UI.Theme).Images.Seal, "the Seal is drawn") end
end
-- combat queues; danger breaks through; the queue flushes after
Probe:Invoke("Force", "Combat")
Probe:Invoke("Slip", { Title = "Queued A"; Text = "x"; Duration = 30 }) Probe:Invoke("Slip", { Title = "Queued B"; Text = "x"; Duration = 30 })
Probe:Invoke("Slip", { Title = "Danger"; Text = "x"; Kind = "Bad"; Duration = 30 })
task.wait(0.5) S = Probe:Invoke("Slips")
Ok(table.find(S.Shown, "Danger") ~= nil, "danger shown in combat") Ok(table.find(S.Shown, "Queued A") == nil, "event queued in combat")
Ok(S.Stub == "2 waiting", "stub: " .. tostring(S.Stub))
Probe:Invoke("Force", nil) Probe:Invoke("Force", "Active") task.wait(1.2) S = Probe:Invoke("Slips")
Ok(table.find(S.Shown, "Queued B") ~= nil, "queued slips show after combat")
Probe:Invoke("Force", nil)
return #Fails == 0 and "PASS qc_slips" or ("FAIL\n" .. table.concat(Fails, "\n"))
```

  `qc_notify_server.lua` (game VM, through `server.py`). It proves the real server path still lands:

```lua
local P = game.Players:GetPlayers()[1]
require(game.ServerScriptService.Services.Features.Notifications).Notify(P, { Title = "Clue found"; Text = "The server path"; Kind = "Info"; Duration = 8 })
task.wait(1)
local Found = false
-- client GUIs don't replicate: the client half reads PlayerGui.Notifications (qc_slips); here, just prove no error
return "sent"
```

  After `server.py qc_notify_server.lua` prints `sent`, run `probe.py Slips` within 8 s. Expected: `Shown` contains `"Clue found"`.
- [ ] **Step 2: Rewrite `Notifications`.**
  - Keep the header's packet contract, and add the 2.38 lines.
  - **Logic:**
    - `Local.Push(Data)`: if `HudState.SlipsQueued()` and not `QC.Danger(Data.Kind)`, append to `Queue` and refresh the stub. Otherwise call `Local.Show(Data)`.
    - `Local.Show`: evict the oldest past `QC.MaxSlips(Phone)` (fade out 0.15), build the slip, slide it 16 px in from the left with a 0.18 s fade (Reduce Motion: a 0.2 s fade only), play `Kit.PlaySound("Tick", 0.4)`, and fade it out after `Data.Duration or (Milestone 6 else 4)`.
    - `HudState.Changed`: when no longer queued, show the queued slips one at a time, 0.6 s apart, as room frees up.
    - **Click:** `QC.SlipOpen(Data)` picks the target: `Texts` calls `Phone.OpenApp("Texts")`, `Evidence` calls `EvidenceWall.Open(Data.Case)`, and `Journal` calls `QuestJournal.Toggle(true)`. All go through `pcall(require, script.Parent.X)`.
    - **Race:** `Player:GetAttributeChangedSignal("Race")` re-skins the visible slips.
  - Register the probe commands `Slip` and `Slips`.
- [ ] **Step 3: Commit** "Quiet Corners QC1: paper slips top-left (queue, danger, stub, routing)".

### Task R6: The prompts (35 min)

**Files:** Modify `…/live/…Controllers.Gui.PromptUi.luau` (from `base/`). Test: `tools/quietcorners/checks/qc_prompts.lua`.

**Interfaces:**
- Kept unchanged: `Shared.Reject`, `NHRejected`, `KeepDefaultStyle`, the PromptShown/PromptHidden flow, and the billboard name `NHPrompt`.
- Probe command `Prompts()`: `{ { Name, Nearest, Cap, Tag, Pip, Key, Action, ActionSize, ObjectSize, Fits } }`.

**Build** (design px, BillboardGui as today, `AlwaysOnTop`):

| Piece | Spec |
|---|---|
| `Key` (the cap) | ImageButton 56 x 56 at (0, 4), Image `PromptCap<Race>`, attribute `QcBox` |
| `Well` / `Fill` | the Well is a transparent clip (ClipsDescendants) inside the cap's box. The Fill is an ImageLabel `PromptCapFill`, ImageColor3 `Colors.Gold`, anchored at the bottom; the Well's height goes from 0 to 1 over `HoldDuration` (Linear) |
| `KeyText` | 22 px (one character) or 20 px (`QC.KeySize`), bold, Gold, inside the box 0.12 to 0.88; text from `Kit.KeyName` / `TAP` as today |
| `Text` (the tag) | ImageLabel at (50, 0), 9-slice `Slices.PromptTag`, SliceScale 0.5, Size (`QC.TagWidth(max(actionW, objectW))`, 64), Image `PromptTag<Race>` |
| `Action` | 22 px bold Ink, at y 21 (centred), x 0.11 of the width + 4; centred at y 32 when there's no ObjectText |
| `Object` | 20 px InkDim, at y 45 |
| `Pip` | ImageLabel 26 x 26, centred, `PromptPip<Race>`, ImageTransparency 0.15 |
| Board size | (50 + tag width, 64) |
| Fallback (no ids) | today's FrameSlot look, with the text raised to 22/20 and the board widened to fit |

**Nearest:** a Heartbeat loop every 0.1 s takes `QC.Nearest` of the distances from the character's root to each shown prompt's adornee. The nearest shows Key and Text; the others show only the Pip. Reject: the Fill's ImageColor3 goes crimson, then the drain and shake as today.

- [ ] **Step 1: Write the failing check** `qc_prompts.lua` (Client VM). It makes two client-local prompts in front of the character:

```lua
local P = game.Players.LocalPlayer
local Probe = P.PlayerGui:FindFirstChild("NHQuietProbe")
if not Probe then return "FAIL no NHQuietProbe" end
local Root = P.Character and P.Character:FindFirstChild("HumanoidRootPart")
if not Root then return "FAIL no character" end
local Fails = {}
local function Ok(C, W) if not C then table.insert(Fails, W) end end
local Parts = {}
for I, D in { 5, 9 } do
	local Part = Instance.new("Part") Part.Anchored = true Part.CanCollide = false Part.Transparency = 1 Part.Size = Vector3.one
	Part.CFrame = Root.CFrame * CFrame.new(I == 1 and -2 or 2, 0, -D) Part.Name = "QcPromptTest" .. I Part.Parent = workspace
	local Pr = Instance.new("ProximityPrompt") Pr.ActionText = I == 1 and "Open" or "Read" Pr.ObjectText = "Mathematics · Room 12"
	Pr.MaxActivationDistance = 15 Pr.RequiresLineOfSight = false Pr.HoldDuration = 1 Pr.Exclusivity = Enum.ProximityPromptExclusivity.AlwaysShow Pr.Parent = Part
	table.insert(Parts, Part)
end
task.wait(1.2)
local L = Probe:Invoke("Prompts")
local Near, Far
for _, E in L do if E.Name == "Open" then Near = E elseif E.Name == "Read" then Far = E end end
Ok(Near and Near.Nearest and Near.Cap and Near.Tag and not Near.Pip, "nearest shows cap and tag")
Ok(Far and not Far.Nearest and Far.Pip and not Far.Tag, "the other shows a pip only")
Ok(Near and Near.ActionSize >= 22 and Near.ObjectSize >= 20 and Near.Fits, "text sizes/fit")
-- the hold fill rises
local Pr = Parts[1]:FindFirstChildOfClass("ProximityPrompt")
Pr:InputHoldBegin() task.wait(0.5)
local Board = nil
for _, B in P.PlayerGui:GetChildren() do if B.Name == "NHPrompt" and B.Adornee == Parts[1] then Board = B end end
local Well = Board and Board:FindFirstChild("Well", true)
Ok(Well and Well.Size.Y.Scale > 0.2 and Well.Size.Y.Scale < 0.9, "fill mid-hold " .. tostring(Well and Well.Size.Y.Scale))
Pr:InputHoldEnd()
for _, Part in Parts do Part:Destroy() end
return #Fails == 0 and "PASS qc_prompts" or ("FAIL\n" .. table.concat(Fails, "\n"))
```

- [ ] **Step 2: Re-art `PromptUi`** to the table, and register `Prompts` with `HudState.Probe`.
- [ ] **Step 3: Commit** "Quiet Corners QC2: prompts re-arted (cap, tag, pip, hold fill; nearest only)".

### Task R7: The compass and the skip ring (25 min)

**Files:** Modify `…/live/…Controllers.Gui.Compass.luau` and `…/live/…Controllers.Gui.CineUI.luau` (from `base/`). Test: `tools/quietcorners/checks/qc_compass.lua`.

**Build** (the Compass keeps its scan, markers, ranges, FOV 160, readout rules and API):

| Piece | Spec |
|---|---|
| `HEIGHT` | 52 (was 32); `Root` Size (WIDTH, 52 + 30) |
| `Back` | ImageLabel `CompassStrip<Race>`, Size (WIDTH, 52). Fallback: today's ink Frame and gradient |
| `Ticks` | a transparent clip over the channel box (24 .. WIDTH - 24, 8.4 .. 43.6). Child ImageLabel `Tile`: `CompassTicks`, ImageColor3 bone `(236, 226, 206)`, `ScaleType.Tile`, TileSize (WIDTH / FOV * 30, channel height), Size (channel width + 2 tiles). Each step: X offset `-((heading % 30) / 30) * tile`. Fallback: today's tick frames |
| Letters | N/E/S/W at 24 bold (N crimson), NE/SE/SW/NW at 20, DIM. A letter is hidden when within 16 px of a visible marker or the objective |
| `Notch` (the lubber) | ImageLabel `CompassLubber<Race>`, 48 x 60, AnchorPoint (0.5, 0), Position (0.5, 0, 0, -8). Fallback: today's Knob |
| `Readout` | 20 px (was 15), at y 58, height 24 |
| Adoption | at the end of `Shared.OnStart`, `HudState.Adopt(Gui, "Compass", { "Compass" }, "Top", 130)`. When the readout's text changes, `HudState.Wake("Compass")` |
| Race | `Race` changed: re-skin `Back` and `Notch` |

**CineUI:** in `Local.Build`, where `SkipSeal` is made, use `QuietCorners.Image(QuietCornersArt, "SkipRing", Race)` when it isn't nil (with ImageColor3 white). Otherwise keep today's image. Change nothing else in CineUI.

- [ ] **Step 1: Write the failing check** `qc_compass.lua` (Client VM):

```lua
local P = game.Players.LocalPlayer
local PG = P.PlayerGui
local QC = require(game.ReplicatedStorage.Functions.QuietCorners)
local Art = require(game.ReplicatedStorage.Config.QuietCornersArt)
local Fails = {}
local function Ok(C, W) if not C then table.insert(Fails, W) end end
local Root = PG.NHCompass:FindFirstChild("Compass", true)
Ok(Root and Root.Parent.Name == "QcFade", "compass adopted")
local Back = Root and Root:FindFirstChild("Back")
local Want = QC.Image(Art, "CompassStrip", P:GetAttribute("Race"))
if Want then Ok(Back and Back:IsA("ImageLabel") and Back.Image == Want, "strip art") else Ok(Back ~= nil, "fallback back") end
for _, L in Root:GetDescendants() do
	if L:IsA("TextLabel") and L.Visible and L.Text ~= "" then Ok(L.TextSize >= 20, "text " .. L.Text .. " " .. L.TextSize) end
end
local RaceWas = P:GetAttribute("Race")
P:SetAttribute("Race", "Vampire") task.wait(0.3)
local WantV = QC.Image(Art, "CompassStrip", "Vampire")
if WantV then Ok(Back.Image == WantV, "race re-skin") end
P:SetAttribute("Race", RaceWas)
return #Fails == 0 and "PASS qc_compass" or ("FAIL\n" .. table.concat(Fails, "\n"))
```

- [ ] **Step 2: Re-art the Compass and swap the skip ring.**
- [ ] **Step 3: Commit** "Quiet Corners QC2: the compass strip re-arted (strip, lubber, ticks, 20 px floor); CineUI skip ring".

### Task R8: Dialogue (60 min)

**Files:**
- Modify: `…/live/…Controllers.Gui.Dialogue.luau` (from `base/`)
- Test: `tools/quietcorners/checks/qc_dialogue.lua` and `tools/quietcorners/checks/qc_dialogue_real.lua`
- The server edit (`Social.Dialogue`) is written in S4, against the fresh dump.

**Interfaces:**
- Consumes the node fields `Clique` (string?) and `Tones` ({ string? }, parallel to `Choices`), added in S4. Both are optional, so the client works without them (Unaffiliated, no tone marks).
- Kept unchanged: `Packets.DialogueEvent`/`DialogueAction`, `InDialogue`, the talk cinematic (`ShotIn`/`ShotOut`), `SetBackpack`, number keys, `Shared.IsOpen`, and the gui name `Dialogue`.
- Probe commands: `Dialogue(Data)` (calls `Local.ShowNode(Data)` without a Model), `DialogueClose()` and `DialogueInfo()`.
  - `DialogueInfo()` returns `{ Crest, CrestRect, CrestOffset, Name, Sub, Line, Replies = { { Text, Tone } }, RibbonH, Seal = boolean }`.

**Build** (ScreenGui `Dialogue`, DisplayOrder 8, `Kit.AutoScale(Gui, { min = 0.8, max = 1.1; phoneScale = 0.66 })` as today; design px on 1920 x 1080; bottom-anchored):

| Piece | Spec |
|---|---|
| `Ribbon` | ImageLabel, AnchorPoint (0, 1), Position (0, 110, 1, -100), Size (1100, 150) at minimum. 9-slice `Slices.Ribbon`, SliceScale 1. Its height = max(150, line height / 0.6). `QcBox` "0.10,0.20,0.90,0.80" |
| `Line` | TextButton in the ribbon box: x 0.12 to 0.86 of the width, centred vertically. 24 px `Fonts.Body`, Ink, TextWrapped, AutomaticSize Y, `MaxVisibleGraphemes` typewriter as today (`CHARS_PER_SECOND` 55). Clicking it skips |
| `Nib` | ImageLabel 28 x 28 at the line box's right end, on its last line. After typing, it bobs 3 px at 1.2 s (none with Reduce Motion) |
| `Card` | ImageLabel `CallingCard<Race>` (the local player's race), 520 x 120, a child of the Ribbon: AnchorPoint (0, 1), Position (0, 10, 0, 30), so it overlaps only the ribbon's top margin. `QcBox` from `Boxes.CallingCard` |
| `Crest` | ImageLabel in the card's socket: centre (60, 60), 94 x 94, AnchorPoint (0.5, 0.5). Image `QC.Crest(DialogueArt, Data.Clique, true)`, ImageRectSize 256 x 256, frame 0 |
| `Speaker` | TextLabel at x 121, centre y 44, width 377: 24 px bold, upper case, Bone `(236, 226, 206)` with a UIStroke |
| `Sub` | TextLabel at x 121, centre y 89: 20 px DIM `(200, 188, 168)`. `QC.CardSub(CliqueName, Data.Role, Relation, fits)`, measured with TextService at 20 px in 377 px. The relation colour stays as RichText |
| `Choices` | a transparent Frame, AnchorPoint (1, 1), Position (1, -50, 1, -77), width 540. Tabs stack upward with a 78 step (72 when there are more than 5 replies) |
| `Choice{i}` | ImageButton 540 x 69, `ReplyTab<Race>`, or `ReplyTabOn<Race>` when hovered, gamepad-selected, or the last one pressed |
| `Choice{i}.Num` | in the socket box: 22 px bold, Gold (Ink on `On`) |
| `Choice{i}.Text` | in the text box: 22 px, DIM (Bone and bold on `On`), TextWrapped off. If it doesn't fit, the step grows to 84 and the tab to 76 for that reply (two lines aren't allowed) |
| `Choice{i}.Tone` | ImageLabel 32 x 32 at the text box's right end − 40, `Tone<Tone>`, only when `QC.Tone(Data.Tones[i])` |
| `Hint` | bottom right, at (1, -50, 1, -40): 20 px DIM, the input-kind text as today, "1-4 reply · click the line to skip · walk away to leave" |
| Phone | the AutoScale phone scale of 0.66 already applies. The Choices stack sits above the ribbon at the right (AnchorPoint (1, 1), Position (1, -24, 1, -(ribbon top + 12))). Touch buttons are hidden in dialogue already |
| Fallback (no ids) | Card: transparent plus `Kit.Decorate(Card, { ornament = "thin" })`. Ribbon: `Kit.Decorate`. Tabs: `Kit.ChoiceRow` at height 44 with 22 px text. The crest always draws (its ids are set) |

**The crest animation.** Use the spec §8 sketch as written, with `QC.FlipOffset`:
- **The entrance:** the card fades in over 0.18 s with a 12 px slide. At 0.12 s the crest drops from 118 % and transparent to 100 % over 0.2 s (Cubic Out), then presses to 96 % and back over 0.12 s (Sine InOut), then plays one catch.
- **Idle:** a random 5 to 8 s on frame 0, then frames 1 to 15 at 15 fps. It never plays while `Current.Typing`.
- **Stop:** a new node keeps the same crest if the speaker is unchanged; `Local.Hide` stops it.
- **Reduce Motion:** frame 0 only, with a single 0.2 s fade.

- [ ] **Step 1: Write the failing check** `qc_dialogue.lua` (Client VM):

```lua
local P = game.Players.LocalPlayer
local PG = P.PlayerGui
local Probe = PG:FindFirstChild("NHQuietProbe")
if not Probe then return "FAIL no NHQuietProbe" end
local QC = require(game.ReplicatedStorage.Functions.QuietCorners)
local DA = require(game.ReplicatedStorage.Config.DialogueArt)
local Seal = require(game.ReplicatedStorage.UI.Theme).Images.Seal
local Fails = {}
local function Ok(C, W) if not C then table.insert(Fails, W) end end
local RMWas = P:GetAttribute("NHReducedMotion")
P:SetAttribute("NHReducedMotion", false)
Probe:Invoke("Dialogue", { Type = "Node"; Id = 9001; Speaker = "Odette Marsh"; Role = "second year"; Clique = "Ink"; Relationship = "Friendly";
	Text = "You came back. Nobody comes back after their first night in Room 106."; Choices = { "What happened in Room 106?", "Maybe you could show me around?", "Pay her ¥10 to keep quiet", "Stay out of my way." };
	Tones = { "Ask", "Kind", "Sly", "Threat" } })
task.wait(2.5)
local I = Probe:Invoke("DialogueInfo")
Ok(I.Crest == QC.Crest(DA, "Ink", true), "Ink crest flipbook") Ok(I.CrestRect == 256, "ImageRectSize 256")
Ok(I.Name == "ODETTE MARSH", "name caps: " .. tostring(I.Name)) Ok(I.Sub:find("The Ink Club", 1, true) ~= nil, "sub: " .. tostring(I.Sub))
Ok(#I.Replies == 4 and I.Replies[3].Tone == "Sly", "replies and tones") Ok(I.Seal == false, "the Seal is drawn somewhere")
Ok(P:GetAttribute("InDialogue") == true, "InDialogue")
for _, L in PG.Dialogue:GetDescendants() do
	if (L:IsA("TextLabel") or L:IsA("TextButton")) and L.Visible and L.Text ~= "" then Ok(L.TextSize >= 20 and L.TextFits, L:GetFullName() .. " " .. L.TextSize) end
end
-- no clique: the Unaffiliated crest; Reduce Motion: frame 0 only
P:SetAttribute("NHReducedMotion", true)
Probe:Invoke("Dialogue", { Type = "Node"; Id = 9002; Speaker = "Wendell Price"; Role = "Custodian"; Text = "Mind the wet floor. And don't go past the boiler room after the last bell, whatever you hear. I mean it, every word of it, all of it, truly."; Choices = { "What's past the boiler room?" } })
local Moved = false
for _ = 1, 20 do task.wait(0.1) I = Probe:Invoke("DialogueInfo") if I.CrestOffset ~= "0, 0" then Moved = true end end
Ok(I.Crest == QC.Crest(DA, nil, true), "Unaffiliated crest") Ok(not Moved, "Reduce Motion: the crest left frame 0")
Ok(I.RibbonH >= 150, "ribbon height") Ok(PG.Dialogue:FindFirstChild("Line", true).TextFits, "long line fits (the ribbon grew)")
Probe:Invoke("DialogueClose")
P:SetAttribute("NHReducedMotion", RMWas)
return #Fails == 0 and "PASS qc_dialogue" or ("FAIL\n" .. table.concat(Fails, "\n"))
```

  `qc_dialogue_real.lua` (Client VM). It talks to a real NPC through its prompt, the way the barber was tested:

```lua
local P = game.Players.LocalPlayer
local Root = P.Character and P.Character:FindFirstChild("HumanoidRootPart")
local Best, D = nil, math.huge
for _, Pr in workspace:GetDescendants() do
	if Pr:IsA("ProximityPrompt") and Pr.Enabled and (Pr.ActionText == "Talk" or Pr.ActionText:find("Talk")) then
		local Part = Pr.Parent:IsA("BasePart") and Pr.Parent or Pr.Parent:FindFirstChildWhichIsA("BasePart", true)
		if Part and (Part.Position - Root.Position).Magnitude < D then Best, D = Pr, (Part.Position - Root.Position).Magnitude end
	end
end
if not Best then return "SKIP no Talk prompt in workspace" end
local Home = Root.CFrame
local Part = Best.Parent:IsA("BasePart") and Best.Parent or Best.Parent:FindFirstChildWhichIsA("BasePart", true)
Root.CFrame = CFrame.new(Part.Position + Part.CFrame.LookVector * 4, Part.Position)
task.wait(1) Best:InputHoldBegin() task.wait(math.max(0.1, Best.HoldDuration) + 0.1) Best:InputHoldEnd()
task.wait(2)
local I = P.PlayerGui.NHQuietProbe:Invoke("DialogueInfo")
local Seal = require(game.ReplicatedStorage.UI.Theme).Images.Seal
local Out = ("speaker=%s crest=%s seal=%s replies=%d"):format(tostring(I.Name), tostring(I.Crest), tostring(I.Seal), I.Replies and #I.Replies or -1)
P.PlayerGui.NHQuietProbe:Invoke("DialogueClose")
Root.CFrame = Home
return ((I.Crest and I.Crest ~= "" and I.Crest ~= Seal and I.Seal == false) and "PASS qc_dialogue_real " or "FAIL qc_dialogue_real ") .. Out
```

- [ ] **Step 2: Rebuild `Dialogue`'s visuals.**
  - Replace `Local.Build`, `Local.ShowChoices` and the visual part of `Local.ShowNode` and `Local.Hide`. Keep the talk cinematic block, `Choose`, `Leave`, `Skip`, the packets and `OnStart`.
  - `ShowChoices(Labels, Tones)` takes the tones from `Data.Tones`.
  - Clique name: `require(ReplicatedStorage.Config.Cliques).Defs[Data.Clique].Name`.
  - Register `Dialogue`, `DialogueClose` (calls `Local.Hide`) and `DialogueInfo` with `HudState.Probe`.
- [ ] **Step 3: Commit** "Quiet Corners QC3: dialogue (calling card, animated clique crest, ribbon, reply tabs, tone marks)".

### Task R9: The Evidence Wall (75 min)

**Files:**
- Create: `…/live/…Controllers.Gui.EvidenceWall.luau`
- Test: `tools/quietcorners/checks/qc_wall.lua` and `tools/quietcorners/checks/qc_wall_server.lua`
- The server and config edits (`Config.Cases`, `Investigation`, `Quests`) are written in S4, against the fresh dump.

**Interfaces:**
- Consumes `Config.Cases` (S4 adds `Questions`, clue `Kind`/`Order`/`Hidden`, and `Number`), `StateController.GetProfile(false).Quests.Cases`, `Packets.QuestAction`, the NHFx events `LinkHit`/`LinkMiss`/`Solved` (through `Fx.On`, as QuestJournal does), `QuietCorners.Wall/Pin/Unpin/Miss/ShowHint`, `Config.EvidenceArt` and `Config.BellTowerArt.Seal`.
- Produces `EvidenceWall.Open(CaseId?)`, `EvidenceWall.Close()` and `EvidenceWall.IsOpen()`.
- It sends `{ Action = "Link"; Case; A; B; Question }` and `{ Action = "Deduce"; Case; Option }`.
- It sets `NHMenuOpen` while open.
- Probe commands: `Wall(CaseId?)`, `WallClose()`, `WallPin(Q, Slot, Clue)` and `WallInfo()`.
  - `WallInfo()` returns `{ Ask, Progress, Cards = { { Id, Kind, Found } }, Sheets = { { Id, State, Hint } }, Answers = n, Solved }`.

**Build** (ScreenGui `NHEvidenceWall`, DisplayOrder 30, `Kit.AutoScale`, `Kit.ClampPanels` on phones; a 1920 x 1080 design canvas `Board`, centred):

| Piece | Spec (mockup `wall_base`, `card`, `sheet`, `evidence_wall`, `evidence_answer`) |
|---|---|
| Scrim | `Kit.Theme.Images.Shadow`, full screen, ImageTransparency 0.42 (not a plain frame), plus a Lighting BlurEffect `QcBlur` (Size 12) while open |
| `Wall` | 4 ImageLabels `WallTL`..`WallBR`, each 960 x 540. Fallback: a `Kit.Panel` ornate frame, 1800 x 960 |
| `Plate` | `CasePlate<Race>` at (560, 70), 800 x 100. The Ask (deduction question) at 28 px bold `(44, 26, 12)` in `Boxes.CasePlate` |
| Header | "CASE 0N" at (92, 104), 22 bold Gold; the case name at (92, 134), 20 Bone; Progress at (1830, 104), right-aligned, 22 bold Bone; "Answered n of m" at (1830, 134), 20 DIM |
| `Cards` | a ScrollingFrame over x 90..1070, y 210..1000, a 3-column grid of 220 x 300 cards (columns at 100, 370, 640; rows 230, 590, …). Card kinds per the mockup boxes: kind word 20 bold InkRed, name 22 bold Ink, where 20 InkDim, quote 20 italic Ink. `Tack<Race>` 30 x 30 at the top centre |
| Missing | `CardMissing` tinted chalk. "Not found yet" 22 bold, the name 20, "Somewhere in <Where>." 20 italic DIM, and an "X Mark it" key cap (`PromptCap` art at 40 px with a 20 px label) |
| `Sheets` | `QuestionSheet` 720 x 252 at x 1110, y 190 + i·264. Ask at 24 bold in `Boxes.SheetAsk`; two `Slot`s 120 x 164 at (body x, body y + 6) and (+134). State text: Empty "Drop a clue on the question it answers" (20 italic InkDim); Half the Hint if `QC.ShowHint`, else "1 of 2 pinned"; Answered the Bell Tower Seal (56 px, tinted crimson) + "Answered" 22 bold InkRed + the insight, 20 italic |
| Mini cards | the card art at 120 x 164 in a slot (no text) |
| `Thread` | per pinned pair: an ImageLabel `Thread` tinted Crimson, from the card's tack to the slot's top centre. Size (distance, 6), AnchorPoint (0.5, 0.5) at the midpoint, Rotation = atan2 |
| Answer mode | when `Ready` and not `Solved`: answered sheets compact to 160 tall (y 190 + i·170), and `AnswerCard<Race>` 340 x 170 per option in a 2 x 2 grid under them, with the option text 22 bold Ink |
| Solved | the chosen card centres (480 x 240). `StampInk` 480 x 180, tinted crimson, holds "SOLVED" at 64 px `Fonts.Title` bold crimson. Then the `SolvedText` at 22 |
| `Lens` | Inspect (X / right click): `Lens<Race>` 320 x 320 over the card, with the full text at 22 in a 260-wide box, wrapped |
| Foot | key caps at y 1030: "A Pick up / pin", "X Inspect", "B Close" (keyboard and mouse: "Click Pick up / pin", "Right click Inspect", "Esc Close"; touch: "Tap a clue, then a slot"), all 20 px |
| Phone (short side under 600) | the plate stays on top. The clues go in a horizontal tray along the bottom (mini cards 120 x 164 with the name under each at 20 px, ScrollingFrame X). The questions stack in a vertical ScrollingFrame between them. Tap a clue, then tap a slot |
| Console | `GuiService.SelectedObject` moves across cards and slots; A picks up and pins; X inspects; B puts a held card back, or closes. The binds go through `ContextActionService` while open |

**Flow:**
1. Pick up a clue: `Held = ClueId`, and every non-answered slot gets a gold `UIStroke` glow (no pulse under Reduce Flash).
2. Drop it in a slot: `QC.Pin`. When it returns a pair, send `Link` with `Question`.
3. `LinkHit` (Case, A, B): re-render, the thread draws in (0.4 s; instant with Reduce Motion) and the insight types out.
4. `LinkMiss`: `QC.Miss`, `QC.Unpin`, and both cards shake (Reduce Motion: a 0.2 s red UIStroke).
5. Answer cards send `Deduce`. `Solved` stamps (Reduce Motion: a fade).
6. Re-render on `ProfileUpdated` `SetQuests`.

- [ ] **Step 1: Write the failing checks.** `qc_wall_server.lua` (game VM, through `server.py`, after S4's server edit):

```lua
local P = game.Players:GetPlayers()[1]
local Inv = require(game.ServerScriptService.Services.Quests.Investigation)
for _, C in { "LockerNote", "DeskCarving", "AttendanceSheet", "ArchiveCard" } do Inv.Grant(P, "EmptyDesk", C) end
local Out = {}
local A = Inv.Link(P, "EmptyDesk", "DeskCarving", "AttendanceSheet", "Originals") table.insert(Out, "right pair, wrong question -> " .. tostring(A))
task.wait(1.6) -- LINK_COOLDOWN
local B = Inv.Link(P, "EmptyDesk", "DeskCarving", "AttendanceSheet", "Erased") table.insert(Out, "right pair, right question -> " .. tostring(B))
local Pass = A == false and B == true
return (Pass and "PASS qc_wall_server\n" or "FAIL qc_wall_server\n") .. table.concat(Out, "\n")
```

  `qc_wall.lua` (Client VM; run after `qc_wall_server`, so Erased is answered and four clues are found):

```lua
local P = game.Players.LocalPlayer
local Probe = P.PlayerGui:FindFirstChild("NHQuietProbe")
if not Probe then return "FAIL no NHQuietProbe" end
local Fails = {}
local function Ok(C, W) if not C then table.insert(Fails, W) end end
Probe:Invoke("Wall", "EmptyDesk") task.wait(1)
local I = Probe:Invoke("WallInfo")
Ok(I.Ask == "Where is Mira Holt's original record kept?", "plate ask") Ok(I.Progress == "Clues 4 of 4 · Answered 1 of 2", "progress: " .. tostring(I.Progress))
Ok(#I.Cards == 4, "cards " .. #I.Cards) Ok(#I.Sheets == 3 and I.Sheets[1].State == "Answered", "sheets")
Ok(P:GetAttribute("NHMenuOpen") == true and P:GetAttribute("NHHudState") == "Menu", "menu state")
for _, L in P.PlayerGui.NHEvidenceWall:GetDescendants() do
	if L:IsA("TextLabel") and L.Visible and L.Text ~= "" then Ok(L.TextSize >= 20 and L.TextFits, L:GetFullName() .. " " .. L.TextSize) end
end
-- pin the Originals pair through the real wall
Probe:Invoke("WallPin", "Originals", 1, "AttendanceSheet") Probe:Invoke("WallPin", "Originals", 2, "ArchiveCard")
task.wait(2.5) I = Probe:Invoke("WallInfo")
Ok(I.Sheets[2].State == "Answered", "Originals answered via the wall: " .. tostring(I.Sheets[2].State))
Ok(I.Answers == 4, "answer cards shown when ready: " .. tostring(I.Answers))
Probe:Invoke("WallClose") task.wait(0.4)
Ok(P:GetAttribute("NHMenuOpen") ~= true, "menu closed")
return #Fails == 0 and "PASS qc_wall" or ("FAIL\n" .. table.concat(Fails, "\n"))
```

- [ ] **Step 2: Write `EvidenceWall`** to the table and the flow, and register its probe commands.
- [ ] **Step 3: Commit** "Quiet Corners QC5: the Evidence Wall (client)".

### Task R10: The book (45 min)

**Files:** Modify `…/live/…Controllers.Gui.QuestJournal.luau` (from `base/`). Test: `tools/quietcorners/checks/qc_book.lua`.

**Interfaces:**
- Kept unchanged: the ScreenGui `QuestJournal`, the `Toggle` button, `Shared.Toggle(Open?)`, `Shared.SelectTab(Index)` (2 now opens the wall), the J key and the `Ui.Panel` name.
- Produces `NHMenuOpen` while open.
- Probe commands: `Book(Open)`, `BookTab(Name)` and `BookInfo()`.
  - `BookInfo()` returns `{ Open, Tab, Pages = "Two" | "Left" | "Right", Leads = n, Detail = title, Quadrants = n }`.

**Build** (mockup `menu()`; the book is 1660 x 943, centred; f = 1660 / 2048):

| Piece | Spec |
|---|---|
| Scrim | as on the wall: Shadow at 0.42, plus `QcBlur` |
| `Panel` | a transparent Frame 1660 x 943 (keeps its name), AnchorPoint (0.5, 0.5), centred, Visible false |
| Quadrants | `BookTL/TR/BL/BR`, each 830 x 471.5. Fallback: today's `Components.Panel` (no quadrant ids, the old look) |
| Corners | `BookCorner<Race>` 120 x 120 at the board's four corners (rotated 0/90/180/270) |
| Tabs | ImageButtons `Tab_Journal`, `Tab_Evidence`, `Tab_Record` and `Tab_Settings`, 150 x 60 at (1636, 120 + i·92) of the book, `BookTabOn`/`BookTab`, label 20 bold Bone/DIM. Gamepad LB/RB step them |
| `Close` | `Components.Button` ghost "X", 48 x 44, at the board's top right |
| Left page `Body` | a ScrollingFrame in `Boxes.BookLeft`. "THE JOURNAL" 34 bold Ink, "Leads you are following" 20 italic InkDim, then one lead per active quest on Bell Tower `LeadCard` art (9-slice `BellTowerArt.Slices.LeadCard`, 520 x 150, title 22 bold Ink, line 20 InkDim; the tracked one is full, others at 0.88). Then "Done (n)" and "Failed (n)" lines, 20 px |
| Right page `Detail` | a ScrollingFrame in `Boxes.BookRight`. The selected quest: title 32 bold Ink, "Started … · from …" 20 italic InkDim, body 22 Ink (wrapped), "Next: …" 22 bold InkRed, fang pips (`PipFang`/`PipEmpty` 46 px) and the count at 20, and the Track / Abandon buttons (`Components.Button`) |
| Footer | key caps at the right page's bottom (`Components.InputKind`): LB/RB Tab · A Track · B Close (pad), "Click a tab · Esc Close" (keys), "Tap a tab · X" (touch), 20 px |
| Ink | `Local.Block` in book mode returns a transparent frame with a `Components.Divider` under it (no slate). Text colours map from the theme to ink: Text → Ink, TextDim/TextFaint → InkDim, Gold → Ink bold, On/Crimson → InkRed |
| Tab actions | Evidence: close the book, `EvidenceWall.Open()`. Record: close, `StatsPanel.Toggle(true)` (S1 confirms the name). Settings: close, `SettingsMenu.Toggle(true)` |
| Phone (shorter side under 600) | one page at a time: TL+BL (the left page) as the index; tapping a lead slides to TR+BR (the right page), with a "‹ Journal" tab on the left board to come back. Reduce Motion: a cut |

- [ ] **Step 1: Write the failing check** `qc_book.lua` (Client VM):

```lua
local P = game.Players.LocalPlayer
local Probe = P.PlayerGui:FindFirstChild("NHQuietProbe")
if not Probe then return "FAIL no NHQuietProbe" end
local Fails = {}
local function Ok(C, W) if not C then table.insert(Fails, W) end end
Probe:Invoke("Book", true) task.wait(0.8)
local I = Probe:Invoke("BookInfo")
Ok(I.Open and I.Tab == "Journal", "open on Journal") Ok(I.Pages == "Two", "two pages on desktop")
Ok(P:GetAttribute("NHMenuOpen") == true, "menu state")
local Panel = P.PlayerGui.QuestJournal.Panel
local Ink = Color3.fromRGB(40, 22, 16)
for _, L in Panel:GetDescendants() do
	if L:IsA("TextLabel") and L.Visible and L.Text ~= "" then
		Ok(L.TextSize >= 20 and L.TextFits, L:GetFullName() .. " " .. L.TextSize)
	end
end
for _, T in { "Journal", "Evidence", "Record", "Settings" } do Ok(Panel:FindFirstChild("Tab_" .. T, true) ~= nil, "tab " .. T) end
Probe:Invoke("BookTab", "Evidence") task.wait(0.8)
Ok(P.PlayerGui:FindFirstChild("NHEvidenceWall") and P.PlayerGui.NHEvidenceWall.Enabled, "Evidence tab opens the wall")
Probe:Invoke("WallClose") Probe:Invoke("Book", false) task.wait(0.4)
Ok(P:GetAttribute("NHMenuOpen") ~= true, "closed")
return #Fails == 0 and "PASS qc_book" or ("FAIL\n" .. table.concat(Fails, "\n"))
```

- [ ] **Step 2: Restyle `QuestJournal`** to the table. Remove `RenderCases` and the evidence strings (the wall replaces them); keep `RenderQuests`' data logic for the leads and the detail.
- [ ] **Step 3: Commit** "Quiet Corners QC4: the Journal as the open book (Journal, Evidence, Record, Settings)".

### Task R11: The fit check (15 min)

**Files:** Create `tools/quietcorners/checks/qc_fit.lua` (Client VM). It's spec §9 in game:
- every visible text at least 20 px and `TextFits`;
- no two texts in one gui overlapping, using the text rect from `TextBounds` and the alignment;
- each text inside its nearest art ancestor's `QcBox`;
- WCAG contrast against the art's `QcBg` attribute when set (3:1, or 4.5:1 for 22 px and under), with the luminance computed in Lua;
- no `Theme.Images.Seal` in the scanned guis.

```lua
local P = game.Players.LocalPlayer
local PG = P.PlayerGui
local Seal = require(game.ReplicatedStorage.UI.Theme).Images.Seal
local Fails, Seen = {}, {}
local function Ok(C, W) if not C then table.insert(Fails, W) end end
local function Shown(G) local X = G while X and X:IsA("GuiObject") do if not X.Visible then return false end X = X.Parent end return true end
local function Rect(L)
	local B, P0, S = L.TextBounds, L.AbsolutePosition, L.AbsoluteSize
	local X = if L.TextXAlignment == Enum.TextXAlignment.Left then P0.X elseif L.TextXAlignment == Enum.TextXAlignment.Right then P0.X + S.X - B.X else P0.X + (S.X - B.X) / 2
	local Y = if L.TextYAlignment == Enum.TextYAlignment.Top then P0.Y elseif L.TextYAlignment == Enum.TextYAlignment.Bottom then P0.Y + S.Y - B.Y else P0.Y + (S.Y - B.Y) / 2
	return X, Y, X + B.X, Y + B.Y
end
local function Lum(C) local function f(v) return if v <= 0.03928 then v / 12.92 else ((v + 0.055) / 1.055) ^ 2.4 end return 0.2126 * f(C.R) + 0.7152 * f(C.G) + 0.0722 * f(C.B) end
for _, Name in { "Notifications", "NHCompass", "Dialogue", "NHEvidenceWall", "QuestJournal", "NHTopBar" } do
	local G = PG:FindFirstChild(Name)
	if not (G and G.Enabled) then continue end
	local Texts = {}
	for _, L in G:GetDescendants() do
		if (L:IsA("ImageLabel") or L:IsA("ImageButton")) and Shown(L) then Ok(L.Image ~= Seal, Name .. ": Seal at " .. L:GetFullName()) end
		if (L:IsA("TextLabel") or L:IsA("TextButton")) and L.Text ~= "" and Shown(L) and L.TextTransparency < 0.9 then
			Ok(L.TextSize >= 20, L:GetFullName() .. " size " .. L.TextSize) Ok(L.TextFits, L:GetFullName() .. " doesn't fit")
			local x0, y0, x1, y1 = Rect(L)
			for _, O in Texts do if x0 < O[3] - 2 and O[1] < x1 - 2 and y0 < O[4] - 2 and O[2] < y1 - 2 then table.insert(Fails, "overlap: " .. L:GetFullName() .. " / " .. O[5]) end end
			table.insert(Texts, { x0, y0, x1, y1, L:GetFullName() })
			local A = L.Parent
			while A and A:IsA("GuiObject") and A:GetAttribute("QcBox") == nil do A = A.Parent end
			if A and A:IsA("GuiObject") then
				local b = string.split(A:GetAttribute("QcBox"), ",")
				local ax, ay, aw, ah = A.AbsolutePosition.X, A.AbsolutePosition.Y, A.AbsoluteSize.X, A.AbsoluteSize.Y
				Ok(x0 >= ax + tonumber(b[1]) * aw - 2 and x1 <= ax + tonumber(b[3]) * aw + 2 and y0 >= ay + tonumber(b[2]) * ah - 2 and y1 <= ay + tonumber(b[4]) * ah + 2, "outside its art box: " .. L:GetFullName())
				local Bg = A:GetAttribute("QcBg")
				if typeof(Bg) == "Color3" then
					local l1, l2 = Lum(L.TextColor3), Lum(Bg)
					local R = (math.max(l1, l2) + 0.05) / (math.min(l1, l2) + 0.05)
					Ok(R >= (if L.TextSize > 22 then 3 else 4.5), ("contrast %.1f: %s"):format(R, L:GetFullName()))
				end
			end
		end
	end
	table.insert(Seen, Name .. " " .. #Texts)
end
return (#Fails == 0 and "PASS qc_fit (" or "FAIL qc_fit (") .. table.concat(Seen, ", ") .. ")\n" .. table.concat(Fails, "\n")
```

The controllers set `QcBg` on their art pieces to the paper or iron colour sampled from the art's text box: paper `(222, 204, 170)`, iron `(40, 38, 44)`. Measure these in R1 with Pillow and put them in each config's `Boxes` comment.

- [ ] **Step 1: Commit** `qc_fit.lua`: "Quiet Corners: the in-game fit check (size, fit, overlap, art box, contrast, no Seal)".

---

# Part 2: Studio tasks (about 5 h)

### Task S1: Hand-over, fresh dump, rebase, backups and the loader (25 min)

- [ ] **Step 1:** Get "Studio released" (see Global Constraints). Confirm Edit mode with `get_studio_state`.
- [ ] **Step 2: Dump** into `tools/quietcorners/pre` (and `live` for the files R-tasks didn't create):

```bash
cd /e/NH-ui
G=StarterPlayer.StarterPlayerScripts.Controllers.Gui
python -X utf8 -I tools/quietcorners/harness/dump.py $G.Notifications $G.PromptUi $G.Compass $G.Dialogue $G.QuestJournal $G.KitHud $G.TopBar $G.SettingsMenu $G.CineUI ReplicatedStorage.UI.Settings ReplicatedStorage.Config.Cases ServerScriptService.Services.Social.Dialogue ServerScriptService.Services.Quests.Investigation ServerScriptService.Services.Quests.Quests ReplicatedStorage.Remotes.Packets
```

  Expected: 15 lines with byte counts. `dump.py` writes `live/` only when the file is missing, so R-task files are kept. Check that in `dump.py` before running.
- [ ] **Step 3: Rebase.**
  - For each client file in `live/`, `diff base/X pre/X`. If they differ, run `git merge-file live/X base/X pre/X`.
  - Resolve any conflict by keeping the live change and re-applying the fresh code. Commit "Quiet Corners: fresh pre-dump, rebased".
- [ ] **Step 4: Back up.**
  - Write `harness/_backup.lua` from R1's, with the folder `QuietCorners_pre_<YYYYMMDD>` and the 14 changed paths (everything in the dump except Packets).
  - Run it with `edit.py` and check that the folder holds 14 clones.
- [ ] **Step 5: Confirm five facts** (Edit, read-only; write them into the task report):
  1. The client controller loader starts every ModuleScript under `Controllers.Gui` with `OnStart`. Find it with `script_grep` for `OnStart()` in StarterPlayerScripts. If new modules aren't started automatically, stop and report BLOCKED: HudState and EvidenceWall need it.
  2. `Packets.Notify` and `Packets.DialogueEvent` take an open table, not a typed struct, so extra fields pass. If either is typed, add `Open`/`Case` and `Clique`/`Tones` to its schema in S4.
  3. The QuestAction handler's Link branch in `Quests.Quests`, and how it calls `Investigation.Link`.
  4. The names of `StatsPanel`'s open function and `SettingsMenu.Toggle`.
  5. The attribute that marks a clue's world object (from `Quests.Places`, for "Mark it"). If there's none, "Mark it" is hidden.

### Task S2: The pure rules in the Edit VM, and the red round (15 min)

- [ ] **Step 1: Install** the pure module and the configs, then run the pure check:

```bash
python -X utf8 -I tools/quietcorners/harness/install.py tools/quietcorners/live/ReplicatedStorage.Functions.QuietCorners.luau tools/quietcorners/live/ReplicatedStorage.Config.QuietCornersArt.luau tools/quietcorners/live/ReplicatedStorage.Config.DialogueArt.luau tools/quietcorners/live/ReplicatedStorage.Config.EvidenceArt.luau
python -X utf8 -I tools/quietcorners/harness/edit.py tools/quietcorners/checks/qc_pure.lua
```

  Expected: four report lines, then `PASS qc_pure`. If it fails, fix `Functions.QuietCorners` (not the test) and repeat.
- [ ] **Step 2: The red round.** Do one Play round (the full order, with a fresh snapshot). Run `qc_state.lua` through `client.py`.
  - Expected: `FAIL no NHQuietProbe`.
  - Restore, then stop. This proves the checks fail before the code exists. The other client checks share the same first line.

### Task S3: Round A, QC1 and QC2 (state, slips, prompts, compass) (75 min)

- [ ] **Step 1: Install** in Edit:
  - `UI.Settings`, `SettingsMenu` and `HudState`
  - `KitHud`, `TopBar` and `Notifications`
  - `PromptUi`, `Compass` and `CineUI`

  Expected: nine report lines, and no `PARSE FAIL`.
- [ ] **Step 2: Play round A** (a fresh snapshot). Run:
  1. `qc_state.lua` (expect `PASS qc_state`);
  2. `qc_slips.lua` (expect `PASS qc_slips`);
  3. `server.py qc_notify_server.lua`, then `probe.py Slips` (expect `"Clue found"` in `Shown`);
  4. `qc_prompts.lua` (expect `PASS qc_prompts`);
  5. `qc_compass.lua` (expect `PASS qc_compass`);
  6. R1's `tools/belltower-r1/checks/bt_contracts.lua` (expect the same lines as R1's record: timetable hooked, panel for Moments, hidden/shown);
  7. `qc_fit.lua` (expect `PASS qc_fit` over Notifications, NHCompass and NHTopBar).

  Restore, then stop.
- [ ] **Step 3: Fix loop.** For any FAIL: fix the live mirror, re-install that file in Edit, and repeat round A. Allow at most two repeats. After that, record the failure and move on.
- [ ] **Step 4: Commit** the mirrors as installed: "Quiet Corners QC1–QC2 installed and checked (round A)".

### Task S4: Round B, QC3 to QC5 (dialogue, wall, book) with the server edits (90 min)

- [ ] **Step 1: `Config.Cases`** (`live/`, from `pre/`):
  - Add `Number = 1;` to EmptyDesk.
  - Add these to its clues: `Kind = "Note"; Order = 1` (LockerNote), `Kind = "Object"; Order = 2` (DeskCarving), `Kind = "Record"; Order = 3` (AttendanceSheet), `Kind = "Record"; Order = 4` (ArchiveCard) and `Kind = "Record"; Order = 5; Hidden = true` (MiraFile).
  - Add:

```lua
		Questions = { -- (2.38) the Evidence Wall: one per link (Ids match ServerStorage.QuestSecrets); which clues belong stays secret
			{ Id = `Erased`; Ask = `What is happening to Mira?`; Hint = `Her desk and the register both lost something.` };
			{ Id = `Originals`; Ask = `Where did the original register go?`; Hint = `Try where the school keeps its books.` };
			{ Id = `Warned`; Ask = `Who else knew?`; Hint = `Someone told you exactly where to look.`; Bonus = true };
		};
```

- [ ] **Step 2: `Investigation.Link`.**
  - Change the signature to `Shared.Link(Player, CaseId, A, B, Question: string?)`.
  - After the `A == B` guard, add `if Question ~= nil and (typeof(Question) ~= "string" or #Question > 32) then return false, "" end`.
  - In the loop, match only when `(Question == nil or Link.Id == Question)`. The miss branch (`LinkMiss`) is unchanged, so a right pair in the wrong question is a miss.
  - Add `Open = "Evidence"; Case = CaseId;` to the "New insight", "That doesn't fit" and "Case breakthrough" notify tables. If S1 found `Packets.Notify` typed, add the fields to its schema.
  - Add `(2.38) Link takes the question id (the Evidence Wall)` to the header.
- [ ] **Step 3: `Quests.Quests`.** In the QuestAction Link branch found in S1, pass `if typeof(Message.Question) == "string" then Message.Question else nil` as the fifth argument.
- [ ] **Step 4: `Social.Dialogue`.**
  - Above the `Packets.DialogueEvent:FireClient` in the node sender, add:

```lua
	-- (2.38) Quiet Corners: the speaker's clique crest (none = Unaffiliated on the client) and each reply's tone mark
	local Clique = Npc.Clique or (if Npc.Faction == `Vigil` then `Vigil` elseif Npc.Faction == `CrimsonCourt` then `Court` else nil) or ctx.CliqueId
	local Tones = {}
	for I, Choice in Offered do Tones[I] = if typeof(Choice.Tone) == `string` then Choice.Tone else false end
```

  - Add `Clique = Clique; Tones = Tones;` to the fired table. If S1 found the packet typed, add both to its schema.
- [ ] **Step 5: Install** in Edit: `Config.Cases`, `Investigation`, `Quests`, `Social.Dialogue`, `Dialogue`, `EvidenceWall` and `QuestJournal` (and `Packets` if changed). Expected: report lines and no `PARSE FAIL`.
- [ ] **Step 6: Play round B** (a fresh snapshot; it covers `Quests`, so the granted clues and insights are restored). Run:
  1. `qc_dialogue.lua` (expect `PASS qc_dialogue`);
  2. `qc_dialogue_real.lua` (expect `PASS qc_dialogue_real speaker=… crest=rbxassetid://…`, or `SKIP` when no Talk prompt is loaded; record which NPC);
  3. `server.py qc_wall_server.lua` (expect `PASS qc_wall_server` with `wrong question -> false` and `right question -> true`);
  4. `qc_wall.lua` (expect `PASS qc_wall`);
  5. `qc_book.lua` (expect `PASS qc_book`);
  6. `qc_fit.lua` with the wall open (`probe.py Wall '"EmptyDesk"'` first), then with the book open, then with a dialogue node up (expect `PASS qc_fit` each time).

  Restore (expect `restored`), then stop.
- [ ] **Step 7: Fix loop** as in S3. **The cut line:** if `qc_book` still fails after two repeats, re-install `pre/…QuestJournal.luau` (today's Journal; the wall still opens from slips) and record "book deferred".
- [ ] **Step 8: Commit** "Quiet Corners QC3–QC5 installed and checked (round B): server question id, dialogue clique and tones".

### Task S5: Art ids, phone pass and screenshots (60 min)

- [ ] **Step 1: Find the ids.** Follow `Pipeline-Lessons.md` "Assets in the group":
  1. In the built-in browser, on a create.roblox.com tab, fetch `itemconfiguration.roblox.com/v1/creations/get-assets?assetType=Image&groupId=15981569`, one page at a time, 1.5 s apart.
  2. Save each page to `tools/quietcorners/harness/_assets_N.json`.
  3. Run `python -X utf8 -I tools/quietcorners/harness/ids.py tools/quietcorners/harness/_assets_*.json`. It prints the missing names: whatever isn't uploaded yet stays on the fallback.
- [ ] **Step 2: Check the sizes.** In a Client-VM script, for each filled id, read `AssetService:CreateEditableImageAsync(Content.fromAssetId(id)).Size` in a pcall. Expect each to match `upload-manifest.json`. A smaller size means Roblox downscaled it: record it, and re-stage that piece smaller.
- [ ] **Step 3: Install** the three configs. In one Play round (a fresh snapshot), run every check from S3 and S4 again with the art. Expect them all to `PASS`.
- [ ] **Step 4: The phone pass.**
  - In the same round, set the kit's phone preview (`NHPhonePreview`, 844 x 390, as in R1's phone check).
  - Run `qc_fit.lua` with slips, then the wall, then the book, then a dialogue node.
  - Expect a PASS each time, slips capped at 2, the book in one-page mode, and the wall as a tray.
  - Then clear the preview.
- [ ] **Step 5: Screenshots** (`screen_capture`, one at a time) to `docs/img/quietcorners-*.jpg`:
  - `ghost` (calm, Ghost) and `combat` (after `probe.py Poke '"Hit"'`)
  - `slips` (3 slips + the stub), `prompt` (the test prompts from `qc_prompts`, kept up) and `compass`
  - `dialogue-ink` and `dialogue-unaffiliated` (probe nodes)
  - `wall`, `wall-answer` and `book`
  - `phone-wall` and `phone-book`

  Transient UI goes up through probe commands with a long `Duration`. Compare each with the mockup of the same name, and describe the differences in the report.
- [ ] **Step 6: Restore, stop, and commit** the configs, the screenshots and the filled `ids.json`: "Quiet Corners: art ids, size check, phone pass, screenshots".

### Task S6: Release Studio, then docs (30 min)

- [ ] **Step 1:** In Edit mode with slot 2 restored, send "Studio released".
- [ ] **Step 2: `docs/UI-Kit.md`.** Add a "Quiet Corners (2.38)" section covering:
  - the decision table as built;
  - `HudState` (the states, HudMode, Adopt, the probe);
  - each restyled controller's layout and fallbacks;
  - the three art configs and the 1024 rule;
  - the contracts that still hold;
  - what wasn't checked.
- [ ] **Step 3: `docs/Quests-and-Investigation.md`.** Replace the Case Files description with the Evidence Wall: the questions, `Link`'s question id, the phone and console controls.
- [ ] **Step 4: `CHANGELOG.md`.** Write a `[2.38.0]` entry in the file's style:
  - what's new;
  - every ruling above;
  - each check by name and result;
  - what wasn't checked: two players, a real phone, the Bell Tower hook (deferred), photo clues, Almanac and Ledger;
  - the backup folder.
- [ ] **Step 5: The spec's status line.** Add "QC1–QC5 built lean in 2.38.0 (plan `docs/superpowers/plans/2026-11-22-quiet-corners-ui.md`); the Bell Tower trims and fold wait for R2".
- [ ] **Step 6:** Run `python -m graphify update .` (don't commit `graphify-out/`). Commit the docs: "Quiet Corners: docs and changelog (2.38.0)".

---

## The owner's upload list

All files are in `art/group-upload-quietcorners/`, staged by Task R1. The upload goes to group 15981569, keeping the file names. **The 18 crests and crest flipbooks are already uploaded**; nothing else in `out/quietcorners` (60), `out/evidence` (35) or `out/dialogue` (24 of 42) has an id yet. After the Book and Wall are split into quadrants, that makes **125 images**.

| Tier | When | Count | Files |
|---|---|---|---|
| **A** | before the Studio day (drawn today, Human trim) | 43 | `QcSlipHuman`, `QcPromptCapHuman`, `QcPromptTagHuman`, `QcPromptPipHuman`, `QcPromptCapFill`, `QcCompassStripHuman`, `QcCompassLubberHuman`, `QcCompassTicks`, `QcSkipRingHuman`, `QcSkipRingFill`, `QcBookTL/TR/BL/BR`, `QcBookTab`, `QcBookTabOn`, `QcBookCornerHuman` · `DlCallingCardHuman`, `DlReplyTabHuman`, `DlReplyTabOnHuman`, `DlRibbon`, `DlNib`, `DlToneKind`, `DlToneSly`, `DlToneThreat`, `DlToneAsk` · `EvWallTL/TR/BL/BR`, `EvCasePlateHuman`, `EvCardPhoto`, `EvCardNote`, `EvCardRecord`, `EvCardObject`, `EvCardMissing`, `EvSlot`, `EvQuestionSheet`, `EvTackHuman`, `EvThread`, `EvAnswerCardHuman`, `EvLensHuman`, `EvStampInk` |
| **B** | any time (until then, the other races fall back to Human) | 75 | for each of Priest, Vampire, Werewolf, Ghoul and Wraith: `QcSlip`, `QcPromptCap`, `QcPromptTag`, `QcPromptPip`, `QcCompassStrip`, `QcCompassLubber`, `QcSkipRing`, `QcBookCorner`, `DlCallingCard`, `DlReplyTab`, `DlReplyTabOn`, `EvCasePlate`, `EvTack`, `EvAnswerCard`, `EvLens` (each `<Piece><Race>.png`) |
| **C** | later (not drawn today) | 7 | `QcPlateTrim{Human,Priest,Vampire,Werewolf,Ghoul,Wraith}` (the Bell Tower plate, after R2), `EvCork` |

## Owner's decisions (2026-11-22)

The owner approved the plan as recommended:
- **Every replace / restyle / add decision** in the decision table.
- **The peek:** Tab and View also wake the HUD (ruling 7 stands).
- **The Bell Tower:** after the R2 merge, it folds in combat, hides in menus, and gets the `PlateTrim<Race>` plate. That is a follow-up task once R2 is in; it's not part of today.
- **The cut line:** if the day runs long, the book is cut first.

Defaults for the other questions:
1. **Long notifications (Q4):** clicking a slip opens the book on the related page:
   - a quest step opens the Journal at that quest;
   - a clue or insight opens the Evidence page (the wall);
   - texts still open the phone's Texts app.
   - Any slip with no page opens the book's **Notices** page, a log of the session's notifications at full length.
   - Every slip is clickable. This replaces ruling 5's "unrouted slips aren't clickable".
   - The book gains a fifth tab, `Notices`, which fills the mockup's fifth tab slot. `Notifications` keeps the last 30 notifications (`Shared.History()`).
   - `QuestJournal.OpenPage(Page, Arg?)` opens a page: `"Journal"` (with the quest id), `"Evidence"` (with the case id) or `"Notices"`.
2. **The subtitle seal and the Texts app avatars (Q5):** swapping them for crests is a follow-up, not now.
3. **Photo clues (Q6):** they show as Object cards for now (ruling 9 stands).
4. **Tone marks (Q7):** no tones are written for existing NPC replies. Tones are for new content only, and the client shows a mark only when a choice sets `Tone`.

## Questions answered (kept for the record)

1. **The day's scope.** Is a lean book (Journal, Evidence, Record and Settings tabs; no Almanac or Ledger) acceptable for today? If the day runs long, it's the first thing cut, and today's Journal stays.
2. **The Bell Tower hook.** Should the Bell Tower fold in combat and hide in dialogue and menus right after the R2 merge, along with the `PlateTrim<Race>` plate? It's about 30 minutes once R2 is in. Or should it stay full by design, as the danger home?
3. **The Tab peek.** Tab already opens the Students list. Is "any Tab or View press also wakes the HUD for 4 s" all right, or should the peek move to another key (spec: hold 0.3 s)?
4. **Long notifications.** Slips show one shortened line. Should long ones (for example, the insight text) also open something? Insights already route to the wall.
5. **The CineUI subtitle seal and the Texts app avatars.** Both still use the wax seal (`Theme.Images.Seal`). Swap them for the speaker's crest in a follow-up (spec §14)?
6. **Photo clues.** Should each Photo clue get a baked image (the spec's recommendation)? Until then, DeskCarving shows as an Object tag.
7. **Tone marks.** Replies only show a tone when the dialogue file sets `Tone` on the choice. Should tones be written for the existing NPCs (Custodian, Hale, Ezra, Vesper, Ashgrave, Pryce, Sallow, Whitlock and the templates), or should marks appear only as new lines are written?
