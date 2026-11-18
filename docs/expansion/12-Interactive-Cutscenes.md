# 12. Interactive cutscenes (QTE cinematics)

**Status:** approved 2026-11-17. **Part A** (§2 to §5, §7, §9) shipped in **2.25.0** (plan: `docs/superpowers/plans/2026-11-17-interactive-cutscenes-framework.md`). **Part B** (§6 the finale, §8 animation sourcing) shipped in **2.26.0** (plan: `docs/superpowers/plans/2026-11-17-strikethrough-finale.md`).
**Builds on:** the Phase 1 Cine framework (doc 04 and doc 11): `Services.World.Cine` (server), `Controllers.Cine` (director), `Controllers.Gui.CineUI`, `Config.Cine` and `ReplicatedStorage.Cinematics.<Id>`.
**Target:** NH Combat Test first. The Map gets the same marks and modules at port time (doc 11, "Sets, not coordinates").

## 1. What it is

Story mode gets interactive cutscenes in the style of the cinematic-QTE fighting genre:
- **Fights:** set-piece fights play as directed scenes, and the player drives them with timed prompts.
- **Story beats:** quieter cuts get small prompts.

The owner's decisions:

| Question | Decision |
|---|---|
| Scope | Fights **and** story beats |
| A missed prompt | The cut **never stops**: a miss plays a different branch, and the scene ends with a **grade** (S to D) |
| Several viewers (study group) | **Everyone plays**; the branch follows the **team result**; each player gets their own grade |
| First fight | A **new Chapter One finale** before COLLECTED |
| Architecture | **A: the server judges; the cut is a segment graph.** It must work just as well for **a single player** |
| Animation | Reuse existing clips first. A missing clip is derived from analysis of the closest existing clips. Leg positioning must be realistic (section 8) |

## 2. Prompt types

| Prompt | Input | Window | Presentation |
|---|---|---|---|
| **Press** | The shown key on the beat | Perfect ±0.12 s, Good ±0.25 s, otherwise Miss | World slow-mo 0.15x as a *moving hold* (the camera keeps pushing, debris drifts); snaps to full speed on the hit |
| **Mash** | Tap repeatedly | 1.6–2.5 s; success at a target rate (default 7 taps/s, 5 on touch) | A clash: bodies locked, shake grows with the meter |
| **Direction** | One of 2–4 directions | 0.9 s; a wrong pick or no pick is a Miss | Slow-mo 0.1x; the attack's path drawn as a smear arc |
| **Hold** | Hold, release in a zone | A zone on a filling ring, ±0.15 s | Charging a finisher; the release lands it |
| **Choice** | A timed dialogue choice, 2–3 answers | 4–6 s; no answer means the default branch | No slow-mo; the scene breathes |

- **Keys:** PC uses the combat family (M1, F, E, Space); gamepad uses the face buttons; touch gets large on-screen buttons where the thumbs already are.
- **Prompt art:** built only from the UI kit's brass and paper art (the existing-assets rule).
- **Reduce Motion:** keeps the slow-mo, drops the shake, and widens every window by 30%.
- **Chapter One story beats:**
  - **Prologue:** a Press for "Here." when Hale reads your name. A miss means you answer late (Hale: "...Here, apparently.").
  - **COLLECTED:** stays watch-only.

## 3. The segment graph

A cut module's `Build(Ctx)` may return `segments` instead of `shots`. A cut with `shots` is one segment, so every Phase 1 cut stays valid.

```lua
return {
  start = "Intro",
  segments = {
    Intro = { shots = {...}, events = {...},
              prompt = { kind = "Press", key = "Strike", at = 3.2, beat = 3.45, slow = 0.15,
                         onPerfect = "Counter", onGood = "Counter", onMiss = "TakeHit", flag = nil } },
    Counter = { shots = {...}, next = "Clash" },
    TakeHit = { shots = {...}, next = "Clash" },
    Clash   = { shots = {...}, prompt = { kind = "Mash", at = 1.0, dur = 2.2, rate = 7,
                                          onWin = "Finisher", onLose = "Thrown", flag = "FileKept" } },
    ...
    End     = { shots = {...} },            -- no next and no prompt: the cut ends
  },
}
```

**Rules:**
- **Branches rejoin.** Every path ends at a segment with no `next`.
- **Lengths.** For an interactive cut, `Config.Cine` `Length` is the longest path's length, used for the timeout. `Cine.Validate` checks it against the graph.
- **No loops.** Every target must exist. `Cine.Validate(cut)` checks both in Studio and fails loudly.
- **What carries across.** Actors, props, the set, the grade and the flags carry across segments. Only the shot list changes, so a branch is a cut on the beat, never a reload.
- **One prompt per segment.** Its window closes before the segment's end. The tail plays as a slow-mo hold until the branch is known (at least 0.6 s).
- **Analysis.** `Cine.analyze` runs on every segment and on every full path (for continuity).
- **Config.** `Config.Cine.Cuts[Id]` gains `Interactive = true` and `Rewards = { S = 15, A = 10, B = 5 }`.

## 4. Network flow (`ReplicatedStorage.NHCine`, the existing remote)

| Message | Direction | Content |
|---|---|---|
| `Play` | server to client | as today, plus `Solo` and `Interactive` |
| `Segment` | server to client | `{ Session, Name, StartAt }`; a group cut only: everyone starts the segment on the same frame |
| `Input` | client to server | `{ Session, Seg, Times = { server-clock press times } }`, or `Pick` for a Direction or Choice |
| `Branch` | server to client | `{ Session, Seg, Next, StartAt = now + 0.25 s }`; a group cut only |
| `Where` | client to server | a group client that heard no `Branch` 1.5 s after the window closed; the server replies with `Segment` |
| `End` | server to client | as today, plus `{ Grade, Points, Max, Perfects }` |

- **Judge (`ReplicatedStorage.Cine.Judge`):** a pure function, shared by both sides, that turns `(prompt, presses)` into an outcome and points.
- **Server reception:** the server keeps only presses within the window ± 0.5 s, rate-limited as now.
- **Missing input:** a viewer with no `Input` by the window's close + 0.35 s counts as a Miss.
- **Team result:**
  - the majority outcome of the viewers still watching
  - a tie goes to the better outcome
  - a leaver recounts the majority, as the skip vote does
- **Solo:**
  - The client judges its own presses with the same Judge and branches on the frame of the press: no network wait.
  - The server re-judges the reported presses for the grade, the rewards and the flags.
  - If the two disagree (lag, tampering), the server's verdict counts and a warning is logged. The screen never rewinds.
- **Group:** clients wait for `Branch`. It lands inside the slow-mo hold.
- **Skip in an interactive cut:**
  - A replay or a group vote jumps to the final segment.
  - Unplayed prompts count as Miss.
  - A first solo viewing offers no Skip (as now).
- **Rejoin mid-cut:** the cut plays again from the top with Skip offered (as now). The broken run's results are discarded.

## 5. Grades and consequences

- **Points:** Perfect 3, Good 2, a won Mash or a hit Hold 2, a right Direction or a Choice 1, a Miss 0.
- **Grade:** the share of the most points possible **on the path taken**. S ≥ 90%, A ≥ 75%, B ≥ 55%, C ≥ 35%, otherwise D.
- **Grade card:** a brass grade card after the last shot.
- **What a grade changes:**
  - **First viewing:** a Yen bonus by grade.
  - **Flags:** one story flag per fight (a key prompt's outcome), saved in `Quests.Decisions` and readable by later cuts and dialogue. A flag is visible but never locks anything.
  - **Journal:** keeps the best grade per cut. "Watch again" can raise it, and pays nothing twice.
- **Saved:** `Quests.Cine[Id]` stays `"Started"` / `"Seen"`, and a new `Quests.CineGrades[Id] = { Best, Points }` holds the grades.

## 6. Chapter One finale: "The Strikethrough"

- **Lore (doc 03):**
  - Claimed students are written into the Unwritten, and the Night Custodian only moves their files.
  - What comes for Mira's file is an **Unwritten**: a faded student from the 1893 roll, ink bleeding from its edges, its face a scratched-out smudge, torn register pages circling it.
  - It's on the R6 body, with ink and page VFX, nothing blocky.
- **Where:** Room 102 at night (built in the Map). After Hours gains a Reach stage, "Take Mira's file back to her desk". Then this fight plays, then COLLECTED.

| # | Segment | Prompt | Branches |
|---|---|---|---|
| 1 | You lay the file on her desk. The bell rings at the wrong hour; ink seeps through the desk | none | |
| 2 | It rises behind the desk and lunges | **Direction** (left or right) | Dodge: you slip aside. Miss: thrown into the desks |
| 3 | It comes again | **Press** | Perfect or Good: you shove a desk into it and it staggers. Miss: it grabs your wrist |
| 4 | A tug of war over the file | **Mash** | Win: the file stays whole (flag `FileKept = true`). Lose: half tears away |
| 5 | The finisher | **Hold** | Hit: it shatters into pages. Miss: it fades as the bell stops |
| 6 | Rejoin; silence; then COLLECTED | none | COLLECTED's insert shows a **torn** page when `FileKept` is false |

About 35–45 s depending on the path.

## 7. Director changes (`Controllers.Cine`)

- **Segments:** play the start segment; at a segment's end, go to `next`, the solo verdict or the server's `Branch`.
- **Prompts:** a prompt layer in `CineUI` (kit art) plus input capture through `ContextActionService`, bound only while a prompt is open (sunk, so combat doesn't fire).
- **World time:** slow-mo holds use the toolkit's `timescale` and `hitstop` events, which slow the actors' clips and VFX while the camera keeps real time.
- **Actors can play clips:** the clone keeps its `Animator`, so existing animations play on actors (section 8). The procedural pose layer stays for the small things (breathing, looks, sitting) and is switched off per joint while a clip drives that joint.

## 8. Animation sourcing (owner's rule)

1. **Reuse first.** Every motion in a cut is mapped to an existing clip when one fits. The cut's header lists the mapping.
2. **Derive what's missing.** When nothing fits:
   - Read the closest existing clips' KeyframeSequences (`KeyframeSequenceProvider`): joint angles, key timing, spacing, stance width, root height.
   - Build the new clip from those numbers with animpro (pose JSON), so it matches the game's own set.
   - Name the source clips in the clip's header.
3. **Realistic legs.**
   - Planted feet don't slide (< 0.6 studs/s).
   - Stance width is plausible.
   - Weight shifts over the supporting leg before the free leg moves.
   - The root height follows the legs: no floating, no sinking below the floor; contacts compress 0.2–0.5 studs and recover.
   - Steps land with heel or toe contact timing taken from the source clips.
   - Checked with the house-style physics and jitter audits (`r6-animation-cinematics`).
4. **House style.** Saddy references: slow, creeping anticipation; a 4–7 frame strike; a long follow-through; moving holds; hitstop and impact frames on hits; no rigid one-piece pivots.

**First mapping for the finale:**

| Motion | Source |
|---|---|
| It rises from the desk | GraveGhoul **Emerge** |
| Its lunge | NightStalker **Reach** / GraveGhoul **Attack1** |
| It grabs your wrist | GraveGhoul **Grab** |
| You dodge left or right | Movement **Dash** Left / Right Vector |
| You're thrown into the desks | Default **Knockback**, then the movement **Land** |
| You stagger it with a desk | Fist **Shove**, plus its **Stun1** |
| The tug of war | Fist **Clinch / ClinchVictim** (derived into a two-handed pull if no clip fits) |
| Hit reactions | Default **Hit 1–4**, **Posture Break** |
| The finisher | to be derived from Fist **M2**, **BodyBlow** and Default **Uptilt** if no existing clip fits |
| The fade / shatter | VFX on its **Death** clip |
| Idle and sitting (story cuts) | AmbientNpcs sitting / lean clips; the procedural pose layer |

## 9. Testing

- **Judge:** a TestBridge `CineJudgeTest` on the pure Judge: the Perfect, Good and Miss edges, mash rates, a late or empty `Input`.
- **Solo parity:** client prediction vs. server verdict on the same scripted presses; every case must match.
- **Group:** stand-in viewers (like `CineVoteTest`) for the majority, a tie, a leaver and `Where` recovery. Then the owner runs Studio's 2-player test (steps in the report).
- **Paths:** `Cine.Validate` plus `Cine.analyze` on every segment and every path. Captures of each prompt's hold and each branch's first frame. The owner watches at full speed.
- **Clean-up:** the camera returns to Custom; no `Cine*` leftovers; no console errors; combat input works right after the cut.

## 10. Out of scope (for now)

- Interactive cuts in Chapters 2–5. The framework supports them; their scenes come with those chapters.
- Online leaderboards for grades.
- Voice acting.

## 11. Spec deltas (implementation choices in 2.25.0)

1. **Where the judge lives:** `ReplicatedStorage.Functions.CineJudge`, not `ReplicatedStorage.Cine.Judge`. The toolkit's
   installer recreates `ReplicatedStorage.Cine` and would drop a child module.
2. **Branch table:** a prompt's branches are one table, `on = { <Outcome> = "<Segment>", Else = "<Segment>"? }`.
3. **Time base:** input times are seconds after the prompt **opens** on that client, and every window is measured from
   the open (`beat`, `dur`, `zoneAt`).
4. **Grades and skips:** a grade is recorded only when an interactive cut plays to its end. A skip ends the cut as
   before and keeps the old best.
5. **Story beats:** `Config.Cine` `ShowGrade = false` turns the grade card off. The prologue's single prompt shows no
   grade card.
6. **Test cuts:** `Config.Cine` `Hidden = true` keeps a cut out of the Journal (`__QteTest`).
