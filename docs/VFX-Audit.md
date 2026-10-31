# VFX Audit (Deliverable A): noncombat

Up: [[VFX-Design-Bible]] · [[Nightmare Highschool]]

**Method:** code review of 177 noncombat scripts dumped read-only from the NH Combat Test place, plus a world and effect inventory and Edit-mode screenshots. Combat, movement and third-party packages were skipped by design. Nothing here has been live-verified unless it says so.

**Not dumped:** the end of `UI.Components` (SpinReel), `Gui.Bloodline`, `Functions.EmitManager`.

**World inventory:**
- 334 ParticleEmitters in the place: 309 in the combat/movement effects library, 14 in the combat Visuals package, 6 on the Flashstep part, and none in the school.
- Lights: 35 PointLights, 12 SpotLights and 8 SurfaceLights, mostly in the menu set and sports venues.
- The school has 10 static PointLights and no particle emitters.
- 45 Sounds, all combat or animation; nothing in the world.


## Part I: School life and the world

Code review of the Studio dump (read-only). Not yet live-verified.

`Services.X:N` means ServerScriptService.Services.X line N; `Controllers.X:N` means StarterPlayerScripts.Controllers.X line N.

**What's excluded:**
- `StateController.ScreenFX.Red` is damage feedback (its only caller is Posture_Break), so it's out of scope.
- `ScreenFX.Darken`, `Blur` and `FOV` are generic tweens that can be reused **unmodified**, per the vault decision "FX overlays stay as they are".

### Part 1: Inventory
| Mechanic | Current VFX | Scripts | Shortcomings | Recommendation | Class | Diff |
|---|---|---|---|---|---|---|
| Day/night cycle | The server writes only `Lighting.ClockTime` (every 0.5 s). Everything else is fixed: Ambient 000000, OutdoorAmbient 464646, Brightness 2, FogEnd 100000, plus the Sky/Atmosphere/Bloom/SunRays/DoF children. Night is the default flat navy. | SchoolClock:70-75; Config.SchoolSchedule:32 `SyncLighting`. `workspace.Map.LightingSettings` is an unused duplicate. | No dawn, dusk or night grade; the "Nightmare" hours look like a dim noon; the server's ClockTime fights the MainMenu (F5) | Client DayCycle with lighting keyframes on a LightingStack (C) | Improvement | M |
| Night & full moon | **None.** Both change damage and EXP. | Lineage:49,211-216; Progression:110-121,135-137,175; Evolution:46-51 | Players can't tell their night or full-moon perks are active | Full-moon layer (D) | New VFX | S |
| Location lighting | Static PointLights: Archive 3, Boiler 1, Rite props 5, Quests 1. Cast NPCs carry a faction PointLight (range 10, brightness 0.8). Classrooms and hallway have no lights. No emitters anywhere in workspace.School. | inventory2; Npcs:97-103 | No reaction to time of day; interiors have no light at night | Tagged `NHLamp` fixtures toggled by DayCycle; archive dust; boiler steam and embers | New VFX | M |
| Bell / period change | **None.** Only the ClockHud text changes. | SchoolClock:77-84 (`Period`/`Kind` attributes) | A class lasts about 3 m 20 s real time and passing about 25 s; no cue at all with ShowClock off | School Bell (A) | New VFX | S |
| ClockHud + class waypoint | Text panel with green/red class line; flat gold door label | ClockHud:121-169,175-247 | Colour alone carries the meaning; the waypoint stays visible with ShowClock off | Pulse while truant; a passing-time Beam; an icon beside the coloured text | Improvement | S |
| Attendance | Toasts at period end | Attendance:193-200,267-274 | No cue for arriving; results come as a toast burst | "Seated" chime; a coloured result banner | New VFX | S |
| Hall monitor | Gold tag, a 2.5 s bubble, walk speed 10→15 during a chase | HallMonitor:82-92,192-244,313-326,426-461; `MonitorState`:188 (nothing reads it) | The target is never told (F4) | "Spotted!" (B) | New VFX | S |
| Discipline | Toasts plus the ClockHud record line | Discipline:135-140,168-173,196-201 | A level change looks the same as a minor note | Red-ink record stamp; gold wash when it improves | Improvement | S |
| Detention (R106) | Grey "Trash" boxes with prompts; destroyed instantly on pickup | Detention:89-176,213-222 | No feedback; everyone sees everyone's trash (F1) | Detention clean-up (F) | Improvement | S |
| Class activities ×4 | Chalkboard UI, colour tints, PERFECT/GOOD/SLIP, BOOM label, board jitter, grade stamp | Activities client:118-392; renderers | Silent; colour-only feedback; the shake ignores the setting (F9) | Lesson juice (J) | Improvement | M |
| Night Study | Same chalkboard with a "Night Study" subtitle | Hangouts:107-120,50-84 | Identical to class | Warm archive candle flicker; sepia board | Improvement | S |
| MarkWalls | Sigil text toggled instantly; scrubbed at 600 s | Pranks:47-55,63-112,145-157 | Pop-in | Sigil paint & scrub (G) | Improvement | S |
| Stealth zones | Watcher, bubble, HUD eye meter; caught = teleport | Stealth:67-144,206-233,286-310; QT:332-348 | Danger is invisible in the world | Watcher flashlight (H); fade on caught | New VFX | S |
| Lockers | Pivot and anchor; `Hidden` attribute; prompt text shared by everyone | Stealth:327-385 | No motion; the body may show; the prompt can stick (F2) | Locker hide (I) | Improvement | S |
| Quest objects & rite props | Static gold Highlight and a marker; rite verbs change nothing; dropped items glow for everyone | QT:298-330,182-195; Quests:518-672; Config.Quests:46-60 | No pulse, no completion beat | `InteractableGlow` helper; rite ignition (K) | Infra / New VFX | M |
| ProximityPrompts | PromptUi key cap with fill and pop | PromptUi:56-196 | Pops on success even when the server rejects the action; no sound; no rejected state | Sounds plus dimming driven by client state | Infra | S |
| Toasts | Up to 4 stacked | Notifications:31-46; client:18,52-78 | Bursts at the bell | Merge into the bell card | Improvement | S |
| Ambient audio | **None** in the world. The only sounds are 41 combat ones in Assets.Sounds. SoundGroups NH_Master > NH_Effects/NH_Music exist. | UI.Settings:189-216 | The school is silent | Zone soundscape; set SoundGroup NH_Effects explicitly (looped sounds auto-route to Music) | Infra | M |
| Doors/locks/switches | **Not found.** `Room.Door` exists only as the waypoint target. | — | — | Optional | — | — |
| Weather/outdoors | **Not found.** Terrain is empty. | — | — | Optional | — | — |

### Part 2: Concepts

**A. School Bell & Period Card (P0)**
- **Trigger:** `ReplicatedStorage.SchoolClock` attribute `Period` changes (SchoolClock:81). Ignore the first value after joining.
- **Look:**
  - A brass bell icon and an ink banner under the compass, e.g. "PERIOD 2 · Chemistry · Room 103".
  - A gold rim flash on the ClockHud.
  - The red waypoint pulses ×2 if you're not in class.
- **Timing:** the bell plays at 0 s, the banner eases in over 0.25 s, holds 2.5 s and fades over 0.4 s.
- **Build:**
  - client `Controllers.Gui.SchoolBell`
  - Kit UI
  - NH_Effects sound
  - class info from the same source as ClockHud.GetClassInfo
- **Also:** the end-of-class card summarises that tick's toasts.
- **Done when:** it rings once per change and never on join; it's readable on mobile; it follows the Effects volume.

**B. "Spotted!" monitor alert (P0)**
- **Server change:** set and clear `Model:SetAttribute("MonitorTarget", UserId)` in StartChase, EndChase and Catch.
- **Target client only:**
  - an orange Highlight (outline only) on the monitor
  - a "!" billboard
  - a whistle sound
  - a pulse from the existing Darken vignette
- **Caught:** a 0.3 s desaturate and a red "!" stamp.
- **Escaped:** the Highlight fades and the "!" becomes "?".
- **Done when:** it shows within 0.3 s, only the target sees it, and it clears on every exit.

**C. Day-Night Grade (P1, infra)**
- **Keyframes:**
  - dawn 6: pink-gold
  - day: as now
  - dusk 17–20: amber, OutdoorAmbient about 50
  - night 20–6: blue-violet, Atmosphere density about 0.4, OutdoorAmbient about 35, saturation −0.15, Bloom up slightly
- **Build:**
  - client `Controllers.World.DayCycle` with its own ColorCorrection
  - a small **LightingStack**: layers push overrides, and pop restores the current base rather than an old snapshot
  - MainMenu `Grade` moves onto the stack (F5)
- **Done when:** there are no pops, the menu round trip is clean, and interiors stay readable.

**D. Full-Moon Night (P2)**
- **When:** `Lineage.IsFullMoon` from 20:00.
- **Look:**
  - MoonAngularSize tweens 11→18 over 20 s
  - a pale-crimson tint
  - a "The moon is full" card
  - a slightly stronger grade for Werewolves and Vampires

**F. Detention clean-up (P1)**
- **Only the owner sees their trash:** other clients set LocalTransparencyModifier to 1 and turn the prompt off.
- **Look:**
  - pieces bob with a sparkle
  - pickup throws a 6-particle paper burst with a crumple sound
  - the bin gets a lid thunk, a puff and a "Detention served" card
- **Budget:** at most 5 emitters.

**G. Sigil paint & scrub (P2)**
- **Trigger:** watch `Mark.Sigil.Visible`.
- **Paint:** a UIGradient wipe over 1.2 s, drips and a spray hiss.
- **Scrub:** a 2 s fade through grey with suds.
- **Join rule:** skip the animation if the sigil is already showing when you join.

**H. Watcher flashlight (P1)**
- **Light:** a head SpotLight with Angle = FOV and Range = ViewRange from `Config.Stealth`.
- **Night cone:** a faint Beam cone at night that turns orange at suspicion ≥0.45 and red at ≥0.75 (local only).
- **Budget:** at most 2 lights.
- **Done when:** the lit area matches where detection fills.

**I. Locker hide (P2)**
- **On hide:** everyone fades the hidden character out over 0.15 s, with a clank sound.
- **Local view:** a slat vignette (Darken, T=0.2) and the HIDDEN eye.
- **Done when:** a reset while hidden leaves nothing behind.

**J. Lesson juice (P2)**
- **Sounds:** a chalk tap, a ding or buzz, a combo rise.
- **Grade stamp:** it slams in with an ink splat; A+ gets a gold shimmer, F a red scribble.
- **BOOM:** a 0.1 s flash with a green smoke flipbook.
- **Build:** add `Sound` and `Burst` to the renderer Api.
- **Accessibility:** route the shake through `NHShakeScale`, add ✓/✗ glyphs, and make the flash optional.

**K. Rite candle ignition (P3)**
- **Votives:** on the client, for that player only: a flame emitter, a flickering PointLight and smoke.
- **Also:** a CrackedBell ring with dust and an ArchiveWard glyph that glows in.
- **Clears** when the quest is abandoned or completed.

**Optional (need approval):**
- weather (fog, rain, thunder)
- doors that close at the bell
- a Records Office lock at 17:00
- curfew and lights-out
- Nightmare events (jumpscares, power outages, apparitions; listed at Implementation-Status:125 but not built)
- a shared Lab BOOM puff that needs a broadcast
- Boiler machinery

### Part 3: Findings

**F1 (P1). Everyone sees everyone's detention trash.**
- The `Owner` attribute sits on the piece, but the client filter checks `DropOwner` on the prompt.
- Pressing someone else's trash pops but does nothing.
- Two players' pieces stack on the same spots.

**F2 (P1). Locker prompt text is shared and sticks after a respawn.**
- The text says "Leave · Occupied" for everyone.
- CharacterAdded doesn't reset it.

**F3 (P0). There is no bell,** although lesson text says "(The bell rang.)".

**F4 (P0). The chase target is never told.**
- The only warning is an 80-stud bubble that isn't AlwaysOnTop.
- That breaks the "escaping is possible" design.

**F5 (P2). The MainMenu restore puts back a stale ClockTime and Shadows setting.**
- `MainMenu:249,254,298`; ClockTime is forced to 0.4 every frame at :1540.

**F6 (P2). "Night" means two things.**
- Powers, EXP and the full moon use Hour ≥20 or <6.
- The timetable's Night segment starts at 21:00, and 20–21 shows as "Evening".
- Needs a decision; nightfall VFX use ≥20.

**F7 (P2). Toast burst at the bell.** Up to 4 toasts in one tick, with the oldest evicted.

**F8 (P2). A lesson cancelled during the 3-2-1 still builds its board.**
- The board flashes for about 0.65 s over "Lesson cancelled".
- Fix: check `Lesson.Ended` after the loop.

**F9 (P3).** The lesson board shake ignores `NHShakeScale`.

**F10 (P3).** The dropped quest item's light and box replicate to everyone.

**F11 (P3).** `ModuleLoader:22-26` swallows require errors without a warning.

**Helpers to reuse:**
- **PromptUi:** one place for sounds and the rejected state.
- **QT Highlight:** becomes `InteractableGlow`.
- **Activities renderer:** its Api gets `Sound` and `Burst`.
- **ScreenFX:** Darken and Blur, unmodified.
- **EmitManager:** has Emit, CloneSound, ShakeCamera (honours NHShakeScale), SpawnGroup, EnableParticle and IsMyCharacter. It's combat infrastructure; read it, don't modify it.
- **Functions.SchoolTime:** the client computes Hour, Segment and Day locally.
- **Settings SoundGroups.**
- **Kit components.**

**Pattern:**
- **One-shots:** `Packets.Replicate` → `StateController.<Category>.<Effect>`. New world effects go in `StateController.World`.
- **Prefer attributes over remotes.** These are already there:
  - `SchoolClock` Epoch, Period, Kind, SchoolHours
  - player attributes ClassRoom, ClassInRoom, Discipline*, Detention*, StealthZone, Detection, DetectionSeen
  - character attribute `Hidden`
  - NPC attributes Role, MonitorState, WatcherZone
- **Only new server attribute needed:** `MonitorTarget`.
- **Controllers:** any ModuleScript under PlayerScripts.Controllers with `OnStart` is auto-loaded.

## Part II: Quests, investigation and the supernatural

Code review of the Studio dump (read-only); not yet live-verified. References are `<dump name>:line`.

Short names:
- `Quests` = Services.Quests.Quests
- `Stealth` = Services.Quests.Stealth
- `Invest` = Services.Quests.Investigation
- `QT` = Controllers.Gui.QuestTracker
- `QJ` = Controllers.Gui.QuestJournal
- `EvoS` = Services.Player.Evolution
- `EvoC` = Controllers.Gui.Evolution
- `Turn` = Services.Player.Turning
- `RC` = Services.Player.RaceCosmetics
- `Kit` = ReplicatedStorage.UI.Components

Not dumped: Controllers.Gui.Bloodline, Functions.EmitManager, the locker geometry.

Not found in the code: collectibles, inventory, jumpscares or paranormal events, secret areas, portals, any setter for `Transformation`, a reduce-flashing setting.

### Part 1: Inventory
| Mechanic | Current VFX | Scripts | Shortcomings | Recommendation | Class | Diff |
|---|---|---|---|---|---|---|
| Quest start | Toast "New quest" (6 s); the tracker card pops in | Quests:301-303; QT:274 | Generic; main and side quests look the same | Quest-beat banner (C1) | Improvement | S |
| Objective progress | Toast "(n/N)" or the next objective; tracker text swaps silently (0.25 s) | Quests:383,393,416; QT:262-296 | No tick or pulse | Line flash, strike-through, count bump (C1) | Improvement | S |
| Quest complete + Ending | Toast (7 s) plus an Ending toast (12 s) | Quests:325-328 | The Ending is truncated to one line (P0-1) | Banner and Story Card (C1) | Improvement | S/M |
| Fail / abandon | "Quest failed" or "abandoned" toast | Quests:336-370,717-719 | The card just disappears | Fail banner and fade (C1) | Improvement | S |
| Timed countdown | Red "Time left" text | QT:279-284; QJ:209-212 | No urgency | Pulse under 60 s and under 10 s | New VFX | S |
| Waypoint marker | AlwaysOnTop plate "◆ name / N studs" (fixed 200×48), 4 Hz; the compass pins it too | QT:181-195,205-296; Compass:12-13,226-230 | No beacon, off-screen arrow or arrival cue. On a miss it scans the whole workspace 4×/s (QT:36-47) | Edge arrow, near beacon, miss cache (C2) | Improvement + infra | M |
| Quest-object prompts | Prompt only when relevant; gold Highlight on the tagged part | Quests:587-606; QT:298-330 | Only one part of each rite prop is outlined; the Highlight vanishes instantly; full workspace scan on every sync | Adorn the model, fade out, use FX (C3, C9) | Improvement | S |
| Hidden search (Lost and Found) | "Nothing here" toast | Quests:553-563 | No world feedback | Dust puff on a miss, glint on the find | New VFX | S |
| Dropped quest item | Server Part plus PointLight in workspace.QuestDrops, visible to everyone | Quests:610-671; QT:326-327 | Contradicts the docs (owner-only) | Owner-only beacon (C8) | Improvement (bug) | S |
| Clue found | "Clue: X" toast; the Highlight pops off | Invest:69-84; Quests:533-541 | The core investigation moment is just a toast | Ink shimmer, fly to the journal (C3) | New VFX | M |
| Evidence-board link | Gold card selection; result shown in a toast | QJ:294-333; Invest:86-110 | No visual link; failures give no feedback | Red string, pin, shake (C4) | New VFX | M |
| Deduction | Buttons and a toast | QJ:336-351; Invest:112-137 | The climax is a truncated toast | SOLVED stamp (C4) | New VFX | S |
| Detection meter | Top-centre bar, gold → crimson | QT:146-179,332-348; Stealth:274-317 | On screen only | "?"/"!" over the watcher plus a vignette (C5) | New VFX | S/M |
| Watchers | Grey rig with a red tag and a Gotham speech bubble; pops in and out | Stealth:67-144,166-167,237-246 | Pop-in; the bubble is off-kit | Presence fade (C13); restyle the bubble | Improvement | S |
| Caught | Bubble and toast, then an instant PivotTo | Stealth:206-233 | Hard teleport | Fade to black "thrown out" (C7) | New VFX | S |
| Locker hide | Body anchored inside the locker; camera unchanged | Stealth:327-364 | Third-person view on a body inside a part | Locker POV (C6) | New VFX | S |
| Rite props (13) | Static greybox props with 5 PointLights; interacting only shows a toast | rite_props.luau:37-137; Config.Quests:46-59,211-310 | Votives are already lit (P0-3) | RiteFX library (C9) | New VFX + fix | M |
| Rite opens | "Your blood stirs" toast (truncated) | EvoS:89-101 | Not auto-tracked (Quests:299) | Rite banner; track on start | Improvement | S |
| Hunger | `RaceHunger` attribute set (Lineage:447); no client reader in the dump | Lineage:443-452 | Can't verify | Optional | Optional | — |
| Tier-up cutscene | Strong: per-race poses, shots, particles, lights, grade, letterbox, title, Skip; within 140 studs | EvoC:93-542; EvoS:136-160 | Wraith flicker bug (P0-2); shake ignores the setting; placeholder bats; toast lost; no audio | Fixes and polish (C11) | Improvement | M |
| Bite offer | "T Turn them" hint and an Accept card with a countdown | EvoC:559-623; Turn:80-102 | Fine | Optional edge pulse | Improvement | S |
| Turning (accepted) | Toasts only; looks pop on 0.2 s later | Turn:104-124; RC:218-235 | A life-changing moment with no visuals | "The Blood Takes" (C10) | New VFX | M |
| Race cosmetics | Server meshes; Wraith breath and wisps; day/night fade; TailSway | RC:50-215 | Every dusk and dawn rebuilds everything, so it pops (RC:242-255) | Tween the emitters instead | Improvement | S |
| Transformation attr | Eye and outfit hook exists; nothing sets it | UI.Appearance:20-23,148-188,1193-1201 | Dormant | Optional | Optional | — |
| Talkable NPCs | Faction tint, PointLight, name tag; respawn pops in | Npcs:48-105,147-149,181-188,199 | No quest-giver indicator; pop-in | Giver seals (C12); fade (C13) | New VFX | M |
| Dialogue | Kit box with typewriter text; Enabled toggle | Dialogue client:45-249 | Hard toggle | P3: slide-in; speaker rim | Improvement | S |
| Strangers reveal | Nameplate text swaps instantly | Strangers client:159-167 | Instant | P3: ink write-on | Improvement | S |
| MarkWalls | Sigil Visible toggled instantly | Social.Pranks:47-55,89-96 | No paint-on | P3: wipe-in | Improvement | S |
| Full moon | No visual | Lineage:210-216; Quests:139,145 | Players can't tell | Moon signal (C14) | New VFX | S |

### Part 2: Concepts

**Key hook.** `UpdateState` replaces `PlayerData.Quests` (Functions.UpdateState:120-122). The client can diff the previous table on `ProfileUpdated` "SetQuests" (QT:369) with no server change. The first sync after joining is only a baseline.

**C1 Quest Beat Banner + Story Card (P1; fixes P0-1).**
- *Trigger:* the diff of Active, Stage, Counts, Done, Failed and Category Rite.
- *Banner:* a seal stamps in under the compass. Gold for Main, iron for Side, race tint for Rite, cracked crimson for a fail.
- *Tracker:* the line flashes, a finished line strikes through, the count bumps.
- *Story Card:* a parchment panel with wrapped typewriter text.
- *Timing:* seal scale 1.6→1 over 0.18 s (Back); the banner shows 2.2–3 s. Queued, with at most one on screen.
- *Build:* client `Controllers.Gui.QuestBeats` using Kit images. Add a `Story` flag to `Notifications.Notify`.
- *Rules:* shake follows `NHShakeScale`; hidden while `NH_Evolving`.
- *Done when:* full texts are readable; nothing fires on join.

**C2 Waypoint upgrade (P1, infra).**
- The plate scales with distance, and an edge chevron points to off-screen targets.
- Within 25 studs: a ground ring and a Beam, plus one pulse on arrival.
- Add a miss cache to `FindPart` (like `Places.Find`).

**C3 Clue Discovered (P1).**
- *Trigger:* a new key in `Cases[c].Clues`, mapped to its object through `Objects[id].Clue`.
- *Look:* the Highlight flashes, 12–20 ink sparkles rise, and a "+CLUE" slip flies to the Journal button (about 1.5 s).
- Fade the Highlight out instead of destroying it.
- *Reused by:* the Lost and Found search and C9.

**C4 Evidence string + SOLVED (P2).**
- A crimson string joins the two saved cards (Invest:101), with pins and typewriter text.
- A wrong pair shakes the cards.
- When the case is solved, the journal darkens and a SOLVED stamp lands.

**C5 Watcher awareness (P1).**
- A "?" over the watcher between 0.25 and 0.45 detection, turning into a crimson "!" at 0.75.
- A side vignette that respects the Vignette setting.
- Extend QT.UpdateEye, and restyle `Local.Say` to the Kit.

**C6 Locker POV (P2).**
- Triggered by the `Hidden` attribute.
- Slatted vent overlay, saturation −0.3, FOV −6, the camera behind the locker front, 0.25 s transitions.
- Restore the camera like EvoC:395-413, and hide the race-look emitters while hidden.

**C7 Thrown Out (P1).**
- Server: `Packets.Replicate:FireClient(Player,"Quests","Caught",{User=Char})` before Stealth:218.
- Client `StateController.Quests.Caught`: a 0.35 s fade to black with a CAUGHT stamp, then fade back in through the existing Blur.

**C8 Owner-only dropped item (P0 fix).**
- The server part becomes invisible with no light.
- The owner's client builds its own visual from the `DropOwner` attribute: glint and bob, with a gold burst on pickup.
- Other players see nothing.

**C9 RiteFX (P1; votive P0).**
- *Trigger:* `Counts` goes 0→1 on an Interact objective for a rite object.
- *Votives:* start unlit, then ignite.
- *Font:* blood ripple plus red mist.
- *Bell:* swings ±12° with a shock ring.
- *Mirror:* frost creeps over it.
- *Stack:* silver steam.
- *Ash:* embers.
- *Ward:* scratches glow, then cool.
- *Iron:* sparks.
- *Crate:* grave dust.
- *Stone:* a dawn shaft.
- *Budget:* each 1–2.5 s, under 100 particles, local only.

**C10 The Blood Takes (P1).**
- *Trigger:* Turn:117-123 sends a new `NHTurn.Turned:FireAllClients(Victim, Race)`.
- *Victim:* three heartbeat vignette pulses in the race colour, desaturate, then the race grade.
- *Everyone else (within 140 studs):* a 2.5 s lite version of the tier-up effects that peaks over the look rebuild.
- *Shared code:* move the effects into a `RaceFX` module.
- *Limits:* brightness change under 0.15, no strobing.

**C11 Tier-up fixes + polish.**
- Fix P0-2, the shake setting and the lost toast.
- Replace the bat sparkles with a flipbook, add per-race sound, add a Tier III afterglow.
- Move the palette into `RaceFX`.
- Test 6 races × Tiers II and III.

**C12 Quest-giver seals (P1).**
- The client mirrors `Offers`/`CanStart`.
- Seal over the NPC: gold = offer, iron = active, ✓ = turn-in, ↺ = retry.
- At most 8 billboards, MaxDistance 80.

**C13 Presence fade (P2, infra).**
- The server sets `Departing` and delays the Destroy by 0.8 s.
- The client fades the model in or out over 0.7 s with a smoke puff at the feet.
- Reused for teleports home.

**C14 Full-moon signal (P2).**
- From 20:00 on a full-moon night: a bigger moon, a cool tint and a one-time banner.
- Werewolves get a 3 s silver edge.
- Must not fight SyncLighting (SchoolSchedule:32), and must match `TimeOk`.

**Optional (need approval):**
- jumpscares or paranormal events
- collectibles or lore pickups
- watcher vision cones (would change difficulty)
- a Transformation burst (needs a trigger first)
- hunger feed floats or a heartbeat (needs a cue from EvoS.Feed)
- secret areas or portals

### Part 3: Findings
**P0**
1. **Toasts cut story text to one line.** The body is one 18 px line with TextTruncate.AtEnd (Kit:789) in a 380 px holder. This truncates:
   - insights
   - "Case breakthrough"
   - the chapter Ending
   - "Your blood stirs"
   - "Turned"
   - the stealth checkpoint message
2. **Wraith tier-up flicker never flickers.** EvoC:312 does `LocalTransparencyModifier = max(current, F)` and never resets it. The body sits at about 0.6 from t ≈ 4 s, then snaps opaque at cleanup. Fix: base + F.
3. **Votives are already lit.** rite_props.luau:65-66 builds them lit, so "Light the votive candle" changes nothing.
4. **Dropped quest items are visible to everyone** (Quests:620-648).
5. **A locker stays "Leave · Occupied"** after a respawn while hidden (Stealth:422-428).

**P1**
- **Shake setting ignored:** the tier-up shake doesn't apply NHShakeScale (EvoC:455-458).
- **"Evolved" toast never seen:** it's hidden while the cutscene hides the HUD (EvoS:151 vs EvoC:392-394).
- **Rites not tracked or labelled:** a rite isn't auto-tracked when another quest is (Quests:299), and the journal labels rites "SIDE QUEST" and lets you abandon them.
- **Wraith pop:** dusk and dawn rebuild the Wraith looks.
- **Workspace scans:** FindPart scans the whole workspace (9.6k-instance MenuScene included) 4×/s on a miss.
- **Packets.Loaded read once:** risk to verify (Remotes.Packets:55; StateController:52).

**Helpers to reuse**
- EvoC effect helpers and palettes, moved into `RaceFX`.
- RC emitter helpers.
- Kit: tween, Toast, FadeOut, DangerAlert, Panel, Emboss.
- QT target logic.
- ScreenFX: Blur, FOV, Darken, Red.
- `EmitManager.ShakeCamera` (honours NHShakeScale).
- Places lookups.

**How effects are fired**
1. **`Packets.Replicate`:** for one-shot effects, through `StateController.<Category>.<Effect>`. Effects take `function(Character, Params)` and are culled by `Params.Distance` (default 300). New ones belong in folders such as `StateController.Quests.*` or `.Race.*`.
2. **Per-feature RemoteEvent folders:** for flows that need a reply (NHEvolve, NHTurn, NHStrangers).
3. **Attributes:** the client reads state attributes and the SetQuests push directly.
4. **Notifications:** `Notify(Player,{Title,Text,Kind,Duration})`. Extend it rather than adding a parallel channel.

## Part III: Progression, UI, menus, sports and transitions

Code review of the Studio dump. Not yet live-verified.

**Not in the dump:**
- the end of UI.Components after line 2980, which includes SpinReel and the end of CharacterPreview
- Controllers.Gui.Bloodline
- Functions.EmitManager

**Who owns what:**
- **UI kit session:** UI.* (Components, Theme, Settings, ServerDirectory), KitHud, PromptUi, and the reskins (Notifications, ClockHud, DownedHud, FactionsPanel, Dialogue, Activities).
- **Quest session (this one):** Services.*, QuestTracker/Journal, and race code (Lineage, Evolution).
- **No listed owner:** MainMenu, Progress, the Identity client, the Sports/Soccer clients, NHLoadingScreen and Config.*.

### Part 1: Inventory
| Mechanic | Current VFX | Scripts | Shortcomings | Recommendation | Diff | Owner |
|---|---|---|---|---|---|---|
| Level-up | Server ember emitter on HRP, Emit(60) the same frame it's created, destroyed after 2 s; "Level N!" toast | Progression 192-199, 204-222 | Server-authored, so it ignores settings; clients may never see the Emit (verify); just a puff | Client "Bell Toll" (#2) | M | quest |
| EXP strip | Hairline fill tween 0.7 s, ember tip flare, "+N reason" float | Progress 78-175 | **On level-up the fill drains backwards**; the numeral swaps instantly | Wrap: fill → sweep → stamp → refill | S | none listed |
| Stat spend | None (the sheet rebuilds) | Progress ~177; Progression.Spend 226-239 | No confirmation | Value tick and gold underline | S | StatSheet = UI kit |
| Toasts | Kit.Toast with no entrance; FadeOut; the 5th toast destroys the oldest | Notifications client 52-80; Kit 758-815 | No entrance or hierarchy; eviction pops | Slide in; "Milestone" tier (#4) | S/M | UI kit |
| Yen | Plate text snaps | KitHud 202-206, 310 | No gain/loss feedback | Count-up and ±¥ chip (#5) | S | UI kit |
| Clan spin reel | SpinReel; Epic+ big "RARITY" text burst | Identity 352-360, 425-468 | Rare and below land silently | Rarity reveal (#6) | M | SpinReel = UI kit |
| Menu clan Surge | Tendrils recolour; full-screen colour flash 0.45-0.7; FOV kick | MainMenu 1218-1251, 1318-1324, 236-238 | Flash with no reduced-flash option; overlapping surges restore the colour early | Route through the helper | S | none |
| Race/variant/trait reels | Not dumped; probably SpinReel | Gui.Bloodline | — | Same as #6 | S | quest |
| Spin Shop purchase | Status text; **no confirmation of the actual grant** | Identity 663-667; Purchases 33-73 | Missing feedback for a paid action | Milestone toast and counter tick (#7) | S | quest |
| Tier-up cutscene | 10 s camera, letterbox, title, default-texture particles, lights, Neon beam, CC, brightness spikes, shake | Evolution 32-34, 177-487 | Ignores NHShakeScale; brightness spike with no option; off-style default textures | nh_* textures; respect settings | M | quest |
| Main menu | 14 crimson tendril beams, glow, shards, sparks, embers, smoke, 6 fog emitters, lamp dust, lightning, bats; full grade | MainMenu 247-786; Config.MainMenu.Textures | High quality; no quality scaling; lightning has no reduced-flash option | Quality tier; gate the lightning | S | none |
| Loading screen | UI embers, per-frame grain, spark progress, ADMITTED stamp slam with jolt | NHLoadingScreen 108-437 | Jolt and grain ignore reduced motion | Read the engine reduced-motion flag (verify the API) | S | none |
| Enter school | Gate path, black fade, "The bell is ringing...", fade in; FOV forced to 70 | MainMenu 1336-1415 | Plain; **can override the player's FOV** | Iris "Bell" transition (#8); use Settings FOV | M | none |
| Respawn | Hard cut at the spawn; maybe the default ForceField | Slots 168-180 | Abrupt and off-style | "Roll call" (#9) | S/M | quest |
| Recover / Fated revive | Nothing visible; the Fated case is a toast | Downed 356-377; Progression 337-357 | No get-up payoff | "Second chance" (#10), get-up only | M | quest (combat-adjacent) |
| Teleports | PivotTo cut or TeleportAsync with no TeleportGui | Stealth 216-219; Duels 236-237; ServerDirectory 315, 341 | Disorienting | Teleport veil (#11) | S | mixed |
| Soccer ball trail / marker / ring | Client trail when V>45; Neon landing disc; Neon pickup ring | Soccer client 357-482 | Flat Neon discs | Soft-edge versions | S | none |
| Soccer goal | 3 Neon rings at the goal-box centre; Celebrate; GoalCam 2.6 s | Soccer client 409-492; server 434-458 | **Rings lie flat (horizontal)**; spectators get nothing; GoalCam isn't re-entrant | Goal celebration (#12) | M | mixed |
| Soccer Bloodrush | Server sparkle aura (default texture); client ring and shake | Server 649-679; client 74-94, 493-496 | Default texture; server-side; unscaled shake | Bloodrush revamp (#13) | M | quest server |
| Soccer feedback | Charge billboard; shakes 0.25-1.6; text | Soccer 81-110, 243-511 | Every shake bypasses NHShakeScale | Route through the helper | S | none |
| Drills | Target opacity change; "Target!" text | Server Soccer 785-857 | Opacity change only | Pulse and burst on a hit | S | quest |
| Basketball | Swish sparkles + Neon ring; dunk ring; grade text | Sports client 176-489 | Default sparkle; the ring casts a shadow | nh textures; gold rim on a perfect release | S | none |
| Post-game card | Kit.Panel text; closes after 12 s | Sports 196-238 | No win/lose/personal-best moment | Result reveal (#14) | S | Panel = UI kit |
| Proximity prompts | Gold key-cap fill; 1.12 pop | PromptUi 158-194 | Good | — | — | UI kit |
| Factions / Strangers / Compass | Toasts; Students plate fades | various | Join and rank-up look routine | Milestone tier | S | mixed |
| Activities shake | Board shake 6×0.03 s | Activities 182-191 | Ignores the setting | Scale it | S | UI kit |
| VFX settings | CameraShake → NHShakeScale (only EmitManager reads it); Shadows; Vignette; FOV. **No reduced motion, reduced flash or quality setting.** | UI.Settings 13-58, 240-286 | The "0% turns it off" note is wrong outside combat | Add ReducedFlash, ReducedMotion and EffectsQuality, mirrored to attributes | S | UI kit |

### Part 2: Concepts
1. **NH Cosmetic FX helper (P1, infra).**
   - *Where:* client `Controllers.Fx` (not under UI.*), plus one `NHFx` remote modelled on `NHSports.Fx`.
   - *Building blocks:* Burst (nh_ember, shards, smoke), Ring (replaces the 3 duplicate Neon rings), ScreenFlash, Shake (× NHShakeScale), Veil, UiPop and UiCount.
   - *Behaviour:* reads the NHShakeScale, NHReducedFlash, NHReducedMotion and NHFxQuality attributes; pools parts in workspace.NHFx; culls beyond 150 studs.
   - *Done when:* with CameraShake at 0% the camera is still everywhere, and reduced flash removes every flash above 0.25 alpha.
2. **Level-up "Bell Toll" (P1).**
   - *Owner:* the strip fills to 100%, a sweep crosses it, the Roman numeral stamps in, and a 0.2 vignette shows.
   - *World:* an ember column (~40), a gold ground ring and a warm light pulse. Other players see only the column, within 80 studs.
   - *Timing:* about 1.5 s.
   - *Changes:* remove the server emitter; `NHFx("LevelUp")`.
   - *Done when:* the bar never goes backwards, observers see it, and a multi-level gain plays once.
3. **EXP gain tick (P3).** "+N" pops and three sparks run along the new segment.
4. **Milestone toast tier (P1, UI kit).**
   - *Look:* a wax seal stamps in, a single gold shimmer runs across the title, and it slides in.
   - *Used for:* level-up, quest complete, reputation, faction join and rank, purchases.
5. **Yen chip (P2, UI kit).** A count-up and a ±¥N chip.
6. **Rarity reveal (P2).** Tiered from a glint (Common) up to a Surge with a world burst (Legendary/Cursed). A shared `RarityReveal`.
7. **Purchase-granted confirmation (P1).** A Milestone toast plus a counter tick, shown only after the grant succeeds.
8. **Enter-school "Bell" transition (P2).** A clock-seal iris close and open, then a location card; uses the Settings FOV.
9. **"Roll call" respawn (P1).**
   - *Owner:* a 0.5 s veil and the colour coming back over 0.8 s.
   - *Others:* a violet smoke puff and a chalk ring at the feet.
   - Never on the first menu spawn.
10. **"Second chance" get-up (P2).** A candle-gold wisp; Fated adds a clock-hand sigil and embers. Get-up only, never the downed or carry visuals.
11. **Teleport veil (P2).** Fade out 0.25 s, move, fade in 0.4 s, with smoke at both ends; a TeleportGui for server hops.
12. **Goal celebration (P2).**
    - An upright team-colour flare in the goal mouth and 3 net rings.
    - Shards from the posts; the pitch lights pulse for 1 s.
    - Spectators within 150 studs see it.
    - The GoalCam eases back and is re-entrant.
13. **Bloodrush revamp (P2).**
    - Client race-colour embers and 2 wisp ribbons on the torso; nothing trails along the movement path.
    - The aura flickers out over the last 1.5 s.
    - Driven by `SportRush` for late joiners; remove the server emitter.
14. **Result card reveal (P3).** Scales in, team-colour title, a personal-best stamp, and the reward counts up.

**Optional (need approval):** achievements, a level badge on nameplates, world loot, a spectator goal replay, a daily streak.

### Part 3: Findings
1. **(Confirmed)** The EXP bar drains backwards on level-up (Progress 138-145).
2. **(Verify)** The level-up Emit happens on the server the same frame the emitter is created, so clients may miss it (Progression 204-222).
3. **(Verify)** Goal flare rings are flat horizontal discs (Soccer 398-404, 488).
4. **(Race)** MainMenu forces FOV 70 (1401), which can override the saved FOV.
5. **(Verify)** A tab switch mid-spin may leave the clan reel stuck Busy (Identity 137-141 / 455).
6. GoalCam isn't re-entrant (Soccer 409-429).
7. No confirmation that a purchase was granted (Purchases 63-73).
8. **(Minor)** Toast eviction pops; overlapping Surges restore the colour early; the swish ring casts a shadow.

**Accessibility**
- **NHShakeScale isn't read outside combat:** Soccer, Evolution, the loading-screen jolt, the Activities board and the menu FOV kick all ignore it.
- **No reduced-motion, reduced-flash or quality setting.** These flash or flicker with no way to turn them off:
  - the menu lightning (2 flashes every 8-18 s)
  - the Surge flash
  - Evolution brightness spikes
  - the per-frame grain
- **Colour use is OK:** rarity, team and grade always come with text.

**Reuse**
- Kit.tween, Theme.Tween, FadeOut, Toast, SpinReel, Bar and Theme.Images.
- Merge Soccer Ring, Sports Swish and Sports Shock.
- The Config.MainMenu.Textures set and the tools/vfx pipeline. Evolution, the Soccer aura and Swish still use default rbxasset textures.

**Pattern**
- The good model: the server decides and broadcasts `NHSports.Fx:FireAllClients(kind, data)`, and clients draw in a pcall'd `Local.Fx`. Evolution works the same way: clients draw within 140 studs.
- **Exceptions:** the level-up and Bloodrush emitters are parented on the server.
- **Rule:** cosmetics are client-only (via `NHFx` or attributes), culled by distance and settings-aware; the server never parents emitters for cosmetics.
