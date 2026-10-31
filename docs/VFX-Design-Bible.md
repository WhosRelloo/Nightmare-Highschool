# VFX Design Bible: noncombat revamp

Up: [[Nightmare Highschool]] · Audit: [[VFX-Audit]] · Related: [[Main-Menu]], [[UI-Kit]], [[Races-and-Bloodlines]], [[Quests-and-Investigation]], [[School-Simulation]], [[Sports]], [[Progression-and-Stats]]

This is the central note for the noncombat VFX revamp: style guide, catalog, roadmap, status and decisions. Read it before touching any effect.

**Status labels:** Proposed · Approved · In Progress · Implemented · Tested · Needs Revision · Blocked. Nothing gets a label it hasn't earned.

## Scope

**Out of scope (never touched):**
- running, sprinting and their trails
- movement particles
- dash and movement abilities
- combat attacks and weapon trails
- hit impacts and reactions
- combat abilities and attack animations
- every effect in `ReplicatedStorage.Assets.Effects`: BlockHit, CombatFX, Parry, HitType, MovementFX, Vows, FlameStatus and ScreenEffects. All of that library is combat or movement.
- `StateController.ScreenFX.Red`, which is damage feedback

**Reused, never modified:**
- `ScreenFX.Darken` and `ScreenFX.Blur`
- `EmitManager` and `CameraShaker`, which are combat infrastructure. New code may copy their contract, such as honouring `NHShakeScale`.

## What the audit found (summary)
Full detail is in [[VFX-Audit]].

**1. The world is a greybox.**
- Classrooms are about 22 bare parts each, the hallway is 1 part and the map is a baseplate.
- The polished environments are the main menu set, plus the Archive and Boiler Yard at a sketch level.
- So world effects must attach to **tags**, not placeholder parts (rule W1 below).

**2. Most of the game's moments are plain toasts.**
- Quest beats, clues, deductions, rites, the turning, purchases and level-ups.
- The toast body is cut to one line, which hides story text: the chapter Ending, insights, "Your blood stirs".

**3. Night is invisible.**
- The server only writes `ClockTime`. Night and the full moon change damage and EXP, but nothing on screen shows them.
- The school is silent: no bell, no ambience.

**4. Two strong existing pieces set the bar:**
- the main-menu VFX, built with the `tools/vfx` Blender + numpy pipeline and the `nh_*` textures
- the Evolution tier-up cutscene

**5. Accessibility gaps.**
- The CameraShake setting only reaches combat code.
- There is no reduced-motion, reduced-flash or effects-quality setting.
- The menu lightning and Surge flashes are unguarded.

## Style guide

### Visual themes
- **The Institution.** Candlelit gothic school after dark: chalk, ink, wax, paper, brass, dust and steam. Warm, physical and grounded.
- **The Blood.** Supernatural bloodlines bleeding through: crimson tendrils, embers, crystal shards, frost and wisps. Cold or blood-coloured light, with motion that feels slightly wrong (slow drift, curling, counter-rotation).
- **Rule:** institutional feedback (bells, grades, quests, discipline, sports) uses the Institution look. Supernatural looks appear **only** when a supernatural system fires: race, rite, tier-up, turning, full moon or Bloodrush. This keeps the supernatural special.

### Palette and meaning
Single source: `ReplicatedStorage.UI.Theme`, plus `Lineage` race colours.

| Name | Hex | Means |
|---|---|---|
| Ink | `#07060A` / Base `#0E0C12` | Darkness, transitions, veils |
| Bone / Chalk | `#E4DED0` / `#DEE0D6` | Neutral information, dust, paper |
| Candle Gold | `#EBCD78` | The Institution: success, guidance, quest, reward, "look here" |
| Crimson | `#C8283C` (deep `#600E1A`) | Blood and the supernatural; the Crimson Court |
| Danger | `#D62E3A` | Warnings only: caught, failed, violation |
| Ink Blue | `#5C80D2` | Information, mana, calm night |
| Chalk Green | `#78AA60` | Correct, OK, stamina |
| Race colours | from `Lineage.Races[*].Color` | That race's effects, auras and grades |
| Rarity | `Theme.Rarity` | Reels, reveals, rewards |

**Race colours have one source:** `Lineage`. `Config.Sports.RaceAura` disagrees with it (Werewolf is blue there, brown in Lineage), so it is to be pointed at Lineage.

### Common vs rare vs major (visual hierarchy)
| Tier | Examples | Duration | Particles | Screen | Light |
|---|---|---|---|---|---|
| **Ambient** | dust motes, steam, candle flicker, fog | always on, near the player | ≤10/s per emitter, ≤3 emitters in view | none | static or slow flicker |
| **Feedback** | prompt confirm, pickup, correct answer | ≤0.6 s | ≤12 | none | none |
| **Moment** | clue found, quest complete, level-up, bell, spotted, respawn | 1–2.5 s | ≤60 | edges only (≤0.25 alpha) | one pulse ≤2 brightness, range ≤12 |
| **Event** | tier-up, turning, full moon, enter school, goal | 2.5–10 s | ≤150 | grade and letterbox allowed | scripted |

At most **one Moment** plays per player at a time (queue them), and at most **one full-screen effect** at once.

### Particles
- **Textures:** only the `nh_*` set from `tools/vfx`: smoke_4x4, wisp, wisp2_v, ember, shards_2x2, fog. No default Roblox sparkle, smoke or fire textures in new work.
- **Size:** Feedback 0.2–0.6 studs, Moments 0.4–1.5, fog up to 12.
- **Speed:** Institution particles fall or settle (dust, paper). Blood particles rise and drift slowly (0.5–3 studs/s) with gentle rotation.
- **Lifetime:** Feedback 0.3–0.8 s, Moments 0.6–2 s, Ambient 3–8 s.
- **Edges:** always soft. Every sprite fades to zero before its cell edge (see the Main-Menu "soft-edge pass").

### Lighting and glow
- Never raise global Bloom above the current scene value; glow comes from local lights and soft sprites.
- Neon only for tiny cores and lines, never large surfaces.
- Moment lights: range ≤12, brightness ≤2, and they fade out.
- Flicker uses smooth noise, never random snaps.

### Distortion and transparency
- No heat-haze or refraction (not available cheaply in Roblox).
- Fades use `LocalTransparencyModifier` or tweens of at least 0.15 s.
- No hard pops for things appearing or disappearing: NPCs, items and marks fade in and out.

### Intensity and timing
- **In:** 0.15–0.35 s, Back or Quint easing.
- **Hold:** as needed.
- **Out:** 0.3–0.6 s, Sine.
- Stamps (seal, grade, ADMITTED) overshoot from 1.4–1.6× to 1×.
- Screen effects ease; nothing snaps.

### Avoiding noise
- Every effect needs a reason: a state change the player should notice.
- Never both a toast and a banner for the same beat.
- Never stack two effects on the same object.
- Ambient effects only within 120 studs, and only while their location is relevant.

### Accessibility (required)
- **Shake:** every shake is multiplied by `NHShakeScale` (the CameraShake setting). At 0 there is no shake anywhere.
- **Flash:**
  - Never above 3 Hz.
  - New setting **Reduced flashing**: full-screen alpha capped at 0.25, menu lightning becomes a slow glow.
- **Motion:**
  - New setting **Reduced motion** (defaults to the engine flag): stamps and irises become fades, and there is no FOV kick.
  - The loading screen reads the engine flag, because settings haven't loaded yet.
- **Meaning is never colour-only:** always add an icon, a shape or text (✓/✗, "!", "?").
- Story text is never cut off.

### Performance (Roblox)
- **Client-side only:** cosmetics are drawn on the client from the existing hooks: one `NHFx` remote, replicated attributes, `SetQuests` diffs, or `NHSports.Fx`.
- **No server emitters:** the server never parents ParticleEmitters for pure cosmetics.
- **Distance culling:** a player's own effects always show; other players' Moments within 80 studs, world Events within 150.
- **Budgets:**
  - Highlights: ≤8 for VFX (the engine cap is 31)
  - shadow-casting lights in view: ≤8
- **Pooling:** ring and plane parts are pooled in `workspace.NHFx`. No per-frame loops except active tweens.
- **Quality tier:** a new `EffectsQuality` setting (or the engine quality level) halves particle rates and removes fog layers on low quality.

### World rule (greybox)
- **W1.** Ambient and location effects attach to **CollectionService tags** (`NHLamp`, `NHAmbient:Dust|Steam|Embers|Fog`, `NHCandle`), not to named placeholder parts. When the real map arrives, tagging its parts brings the effects with it.

## Architecture (proposed, needs approval)
- **`Controllers.Fx` (client):**
  - The single, settings-aware toolbox: `Burst`, `Ring`, `Plane`, `Light`, `ScreenFlash`, `Shake`, `Veil`, `UiPop`, `UiCount`, `Stamp`.
  - Reads `NHShakeScale`, `NHReducedFlash`, `NHReducedMotion` and `NHFxQuality`; pools; culls.
  - Replaces three duplicate Neon-ring implementations (Soccer Ring, Sports Swish, Sports Shock).
- **`NHFx` RemoteEvent (server → client):** for server-decided cosmetic moments (level-up, respawn, turning, caught, recover). Modelled on `NHSports.Fx`. Everything else stays on attributes and existing remotes.
- **`Controllers.World.DayCycle` + `LightingStack` (client):** a day/night grade from `Functions.SchoolTime` keyframes. Layers (Menu, Evolution, Cutscene) push overrides, and popping restores the *current* base rather than a stale snapshot. This fixes the MainMenu lighting restore.
- **Shared `RaceFX`:** the Evolution effect helpers and race palettes, extracted so the turning, full moon and rites reuse them.
- **Tools:** the `tools/vfx` Blender + numpy pipeline for textures and flipbooks; Blender for meshes only where geometry beats particles (clock-hand sigil, bell, net flare). "VFX Studio" is not a tool this session can reach: there is no MCP or API for it. Effects are built natively in Studio instead.

## Catalog
Owner: **Q** = quest session (this one), **UI** = UI-kit session, **—** = no listed owner. Source letters refer to [[VFX-Audit]]. All entries are **Proposed** unless noted.

### P0: broken or missing critical feedback
| ID | Effect / fix | Source | Owner |
|---|---|---|---|
| P0-1 | **Tested (UI kit, UI 1.10)**: Story text cut off: wrap long toast bodies, or move them to a Story Card | Quests C1 / F | UI (Kit.Toast) + Q |
| P0-2 | **Tested**: Wraith tier-up flicker stuck (it writes `max(current,F)` and never resets) | Quests P0-2 | Q (Evolution) |
| P0-3 | Votive candles already lit; "light the votive" changes nothing | Quests P0-3 | Q (rite props) |
| P0-4 | **Implemented** (module tested; drop path code-reviewed): Dropped quest items glow for everyone (the docs say owner-only) | Quests P0-4 / World F10 | Q |
| P0-5 | **Tested**: Locker prompt shared and stuck on "Leave · Occupied" after a respawn | World F2 | Q (Stealth) |
| P0-6 | **Implemented** (module tested; trash path code-reviewed): Detention trash visible and pressable for everyone | World F1 | Q (Detention + QuestTracker) |
| P0-7 | **Tested**: EXP bar drains backwards on level-up | UI F1 | — (Progress) |
| P0-8 | **School Bell & Period Card**: there is no bell at all | World A / F3 | Q (new module) |
| P0-9 | **"Spotted!"**: the chase target is never told | World B / F4 | Q (HallMonitor + new client) |
| P0-10 | Level-up burst may never reach clients (server Emit) | UI F2 | Q |
| P0-11 | **Tested** (measured, not seen on screen): Goal flare rings lie flat | UI F3 | — / Q |
| P0-12 | **Tested**: Enter school can reset FOV to 70 | UI F4 | — (MainMenu) |
| P0-13 | **Implemented (UI kit, code-checked)**: Lesson cancelled during the 3-2-1 still flashes its board | World F8 | UI (Activities) |

### P1: high-impact and reusable
| ID | Effect | Source | Owner |
|---|---|---|---|
| P1-1 | **Implemented** (installed; routed shakes code-reviewed): `Controllers.Fx` helper + `NHFx` remote; every noncombat shake via `NHShakeScale` | UI #1 | Q (new) |
| P1-2 | **Tested (UI kit, UI 1.10)**: Reduced flashing / Reduced motion / Effects quality settings | UI P3 | UI (Settings) |
| P1-3 | **Tested**: DayCycle grade + LightingStack (fixes the menu restore) | World C / F5 | Q (new) + MainMenu |
| P1-4 | Quest Beat banner + Story Card; tracker line flash | Quests C1 | Q (new) + UI (Notify flag) |
| P1-5 | Clue Discovered (ink shimmer, "+CLUE" slip into the journal) | Quests C3 | Q |
| P1-6 | Level-up "Bell Toll" (strip wrap, numeral stamp, ember column) | UI #2 | Q + — |
| P1-7 | **Tested (UI kit, UI 1.12)**: Milestone toast tier (seal stamp, shimmer). Use `Kind = "Milestone"` | UI #4 | UI |
| P1-8 | Purchase-granted confirmation | UI #7 | Q |
| P1-9 | "Roll call" respawn | UI #9 | Q |
| P1-10 | Watcher awareness ("?" / "!") + watcher flashlight cone | Quests C5 / World H | Q |
| P1-11 | Thrown Out (fade on caught) | Quests C7 | Q |
| P1-12 | RiteFX: votive ignition, bell, font, mirror frost, and so on | Quests C9 / World K | Q |
| P1-13 | The Blood Takes (turning transition) + shared `RaceFX` | Quests C10 | Q |
| P1-14 | Quest-giver seals over NPCs | Quests C12 | Q |
| P1-15 | Waypoint upgrade (edge arrow, near beacon, scan cache) | Quests C2 | Q |
| P1-16 | Detention clean-up (owner-only trash, pickup burst, bin) | World F | Q |
| P1-17 | Tier-up polish: `nh_*` textures, honour shake and flash, keep the toast | Quests C11 / UI | Q |

### P2: signature experiences
| ID | Effect | Source | Owner |
|---|---|---|---|
| P2-1 | Full-moon night (moon size and tint, banner) | World D / Quests C14 | Q |
| P2-2 | Tagged lamps and ambient emitters (archive dust, boiler steam and embers, candle flicker at night) | World inventory | Q (W1) |
| P2-3 | Ambient zone soundscape | World inventory | Q |
| P2-4 | Enter-school "Bell" iris transition + location card | UI #8 | — |
| P2-5 | Goal celebration (upright flare, net rings, light pulse, spectators) | UI #12 | — / Q |
| P2-6 | Bloodrush aura revamp (client, ribbons, ends cleanly) | UI #13 | Q |
| P2-7 | Teleport veil | UI #11 | Q |
| P2-8 | "Second chance" get-up (Recover / Fated) | UI #10 | Q |
| P2-9 | Sigil paint & scrub | World G | Q |
| P2-10 | Locker POV / hide fade | World I / Quests C6 | Q |
| P2-11 | **Tested (UI kit, UI 1.13)**: Lesson juice (sounds, stamp slam, BOOM). Glyph bursts code-checked | World J | UI |
| P2-12 | Presence fade for NPCs and watchers | Quests C13 | Q |
| P2-13 | Evidence string + SOLVED stamp | Quests C4 | Q |
| P2-14 | **UI part implemented (UI 1.12/1.13)**: Rarity reveal (clan / race / variant). `Kit.RarityReveal` tiers + SpinReel near-miss; callers pass `rarity` on the final entry. World burst still Q | UI #6 | Q + UI (SpinReel) |
| P2-15 | **Tested (UI kit, UI 1.11)**: Yen chip | UI #5 | UI |

### P3: polish
- EXP gain tick
- result card reveal
- dialogue slide-in (**implemented, UI 1.13**, with speaker rim; code-checked)
- Strangers write-on
- seated chime
- discipline record stamp
- Night Study candle warmth
- timer pulse (**implemented, UI 1.13**: lesson timer, last 10 s)
- prompt sounds and rejected state (**tested, UI 1.12**)
- soft-edge soccer markers
- basketball `nh_*` sparkles

### P4: after everything else (user-scheduled)
| ID | Effect / feature | Notes | Owner |
|---|---|---|---|
| P4-1 | **Nightmare Nights**: crimson nights run as a school event | The user approved the idea. It needs its own design pass: how the school schedule announces it, what changes in the school, and the trigger (full moon or the event calendar). Visuals: crimson grade, a large pale-crimson moon, a "Nightmare Night" banner when night falls. Builds on DayCycle (P1-3) and the full-moon work (P2-1). | Q |

### Optional (need your approval; no mechanic exists)
- jumpscares and "nightmare events"
- weather
- doors and locks
- curfew and lights-out
- collectibles or lore pickups
- portals
- watcher vision cones that change difficulty
- achievements
- a Transformation burst (nothing sets the attribute yet)
- hunger feed cues

## Roadmap (proposed order)
1. **Batch 0: P0 fixes in this session's files.** P0-2, 3, 4, 5, 6, 7, 10, 11, 12. Small and independent, each tested in Play.
2. **Batch 1: foundations.** P1-1 Fx helper, P1-2 settings (UI kit), P1-3 DayCycle. Everything after this depends on it.
3. **Batch 2: core feedback.**
   - P0-8 Bell and P0-9 Spotted (these need sounds)
   - P1-4 Quest Beat + P0-1 Story Card
   - P1-5 Clue, P1-6 Level-up, P1-8 Purchase, P1-9 Respawn
4. **Batch 3: stealth and the supernatural.** P1-10, 11, 12, 13, 14, 15, 16, 17.
5. **Batch 4: signature.** P2 in the order listed. P2-2 and P2-3 wait for decision D5.
6. **Batch 5: polish.** P3.

**Independent:** Batch 0 items, P1-14, P2-9, P2-13.
**Need the Fx helper first:** everything that bursts, shakes or flashes.
**Need DayCycle first:** P2-1, P2-2, P2-3.

## Decisions
- **D1 Architecture: Approved (2026-10-30).** `Controllers.Fx` + `NHFx` + DayCycle/LightingStack + shared `RaceFX`, as above.
- **D2 Accessibility settings: Approved.** Add Reduced flashing, Reduced motion and Effects quality to Settings. The UI-kit session owns `UI.Settings`, so it is asked to add them.
- **D3 Night look: Approved, with a change.**
  - Normal nights (20:00–6:00) get a **moody blue-violet** grade.
  - **Crimson nights are called "Nightmare Nights"** (user, 2026-10-30). They tie into the school system as a **school event**, and are scheduled **after everything else** in this roadmap (catalog P4-1).
  - Until then, the planned link is to the existing full-moon rule (every 4th night, `Lineage.IsFullMoon`, which already boosts powers). The event design decides the final trigger.
- **D4 Sounds: Approved.** Use Roblox's free Creator Store audio (Roblox-made). Every sound id is listed in the asset inventory so it can be swapped.
- **D5 World effects on the greybox: assumption.** Build them tag-driven (rule W1) but schedule them late (P2-2/3). Reversible.
- **D6 "Night" starts at 20:00: assumption.** This matches powers, EXP and the full moon. The timetable's "Evening" segment (20–21) is left alone, so night visuals start at 20:00. Reversible.

## Status log
- 2026-10-30: Phase 1 audit done (code review of 177 dumped noncombat scripts, world inventory, screenshots of the greybox). Style guide, catalog and roadmap drafted. **Nothing implemented yet.**
- 2026-10-30: **Batch 0 (VFX 1.0)** Play-tested: P0-2, P0-5, P0-7, P0-11, P0-12 Tested; P0-4/P0-6 Implemented via `Controllers.World.OwnedObjects` (tested with tagged test boxes; real paths code-reviewed). The UI kit shipped P0-1, P0-13 and P1-2 (UI 1.10). Next: Batch 1 (Fx toolbox, DayCycle).
- 2026-10-31: **VFX 1.1.** P1-1 toolbox Implemented, P1-3 DayCycle Tested (night brightened after the first look). Added outside the catalog at the user's request: PBR school surfaces, Blender props batch 1 (desks, teacher desks, chalkboards, lockers) with locker door animation (Tested). See [[School-Props]]. Batch 2 (chairs, lounge, vending machine with rattle, altar, bookshelf with book fall) is modelled and waiting for import.
- 2026-10-31: **VFX 1.2.** The weathered prop bake is live on batch 1. Batch-2 designs were upgraded (wrought-iron student chair, full candelabrum, solid pointed gables, finer leather) and textured. The clan and race reels pass rarity to the kit reveal (P2-14, code-reviewed). The hall locker row is fixed.
- 2026-10-31: **VFX 1.3.** Batch-2 props are placed and Play-tested: chairs, the Staff Room lounge, the vending machine with its rattle, 9 Archive bookcases with the book fall, and the altar. The candelabra is waiting for its import.
