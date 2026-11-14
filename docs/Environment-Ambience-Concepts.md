# Environment and ambience: audit and concepts

**Date:** 2026-11-13. The owner asked: "go through the ENTIRE game, github, obsidian vault, graphify, etc. and give me a
list of concept ideas for all environmental & ambient VFX and SFX that need to be in the game to make it the most
immersive", after researching "video game immersion, ambience, lighting, skybox enhancements, etc." with `/watch-video`,
using "the more high quality and informative videos". Related: [[VFX-Design-Bible]], [[VFX-Audit]], [[Map-Core-Preview]],
[[Beasts]], [[School-Simulation]], [[Regions]], [[QOL-Kit]], [[Homes]], [[Combat-Audit-and-Concepts]].

Nothing was built and nothing was committed. Both Studio places were only read.

**Built in 2.17.0** (the owner: "Yes, foundations", "make sounds ourselves", region boxes on the Map "lined up so we
can move them and size them however we want"):
- **1. The mixer:** `Controllers.World.AmbienceMix`, with the Bed, Weather, Spot and OneShot groups, the fight duck,
  and the cutscene fade.
- **2. Three layers:** `Controllers.World.AmbientSounds`, with spot sounds by the `NHAmbientSound:<Kind>` tag and the
  one-shot pool by bed and time.
- **3. Room reverb:** in AmbienceMix, from `Config.Ambience.Reverb`.
- **6. The Map's region boxes:** 29 boxes lined up above the school, waiting to be placed. Library, Cafeteria, Dorms
  and Graveyard were added as places.
- **7. Our own sounds (started):** `tools/sfx/ambience.py`, with 25 one-shots and 7 loops on two sheets waiting to be
  uploaded.
- **Still to do from section A:** 4 (openness) and 5 (zone looks). None of the scripts are on the Map yet.

**House rules:**
- **No blood or gore anywhere.** Crimson means light, glass, wax, silk and the moon, never wounds.
- **Every new UI is unique, on theme, PBR-textured and animated**, like the seal, the clock and the posture bar.
- **Ambience stays under the game.** It never hides a footstep, a tell, a monitor's whistle or a beast's cue.

## What was read

- **Research:** 11 videos (GDC talks, a Digital Foundry deep dive, two Roblox lighting breakdowns). Each was run through
  the `/watch-video` pipeline with 50 frames, and the frames were read against the transcript. See "What I learned".
- **The repo:**
  - **Docs:** the VFX bible, the VFX audit, the Map core preview, Beasts, School Simulation, Regions, QOL Kit (rain
    nights and Night Chill), Homes and Combat Audit.
  - **The changelog:** 1.36.0 (the lamp kit), 1.41.0 (moon phases), 1.80.0 (rain nights), VFX 1.1 (real nights) and
    1.13.0 (lamps and the soundscape).
  - **Pipelines:** `tools/vfx` (the `nh_*` particle textures, PBR and roof makers) and `tools/sfx/racial_grips.py`. That
    script is an offline synthesiser with a stone-hall impulse response, already used for the grip sounds.
- **The graph:** `graphify query` on ambience, lighting and weather. It pointed to `Controllers.World.*` and
  `Regions`. There is no `graphify-out/wiki`.
- **The vault:**
  - `Memory/Decisions.md`: D1-D6 of the VFX revamp, the no-gore warning (2026-11-04), moon phases, and "fights get full
    lighting, camera and VFX detail".
  - `Studio Places.md`, `Next Up.md` and the Discord update notes.
- **GitHub:** the `gh` CLI isn't installed and the GitHub connector failed to connect, so I read the local history
  instead. That's 370 commits, the same history as `origin` (WhosRelloo/Nightmare-Highschool).
- **Studio, read only:**
  - **The Map:** read in Edit.
  - **NH Combat Test:** it was in Play when I started. I didn't touch the Play session; by the time I read it, the other
    session had stopped Play, so I read it in Edit.
  - **What I read in both:** Lighting and its children, the Sky, post effects, Clouds, SoundService, the ambience tags,
    lights and emitters, regions, `Config.Ambience`, `Config.DayCycle`, and the headers of `Soundscape`, `MoonPhases`,
    `FullMoon`, `KitFx` (rain), `SpookyTree`, `BeastGaze`, `SchoolFx` and `Chatter`.
  - **Not opened:** production (Nightmare High [Wave - 1]).

## What exists today

| System | What it does | Where |
|---|---|---|
| Day cycle | Four looks blended by the school clock: Night 0-5.5, Dawn 6.5, Day 8-16.5, Dusk 18.5, Night from 20. The night look is Ambient (30,28,46), OutdoorAmbient (76,70,114), Brightness 1.6, Atmosphere Density 0.36 and Haze 1.6, Bloom 1.15, Saturation -0.15, tint (212,206,255). | `Controllers.World.DayCycle`, `Config.DayCycle` |
| Lamps, candles, emitters | `NHLamp` lamps come on 18:30 and go off 6:30. `NHCandle` flames flicker. `NHAmbient:Dust/Steam/Embers/Fog` emitters run 3 at a time, within 120 studs, at up to 10 a second. | `Controllers.World.Ambient`, `Config.Ambience` |
| Soundscape | One bed at a time, with a 2.5 s crossfade, through the Music & Ambience volume. Beds: Outdoor 0.35, Indoor (halls) 0.22, Classroom 0.14, Archive 0.2 (eerie choir at night), Boiler Yard 0.26. Each has a day and a night loop. A ray up checks for a roof. | `Controllers.World.Soundscape` |
| Moons | The full moon swells (MoonAngularSize 11 → 18) under a pale-crimson grade. A new moon gets a darker, cooler grade and 5,000 stars. Crimson and blue moons each have their own grade, moon texture and banner. Werewolf eyes glow amber. | `World.FullMoon`, `World.MoonPhases`, `Lineage` |
| Rain nights | From 20:00, a 1 in 4 chance of 2-4 hours of rain. It falls at 900 drops a second around the camera (not indoors), with one loop (`5911952995`, 0.55) and a slightly darker grade. Players get Soaked, then the Chill. | `World.KitFx` |
| Night Chill | Outdoors 21:00-06:00: frost breath and frost at the screen edges. | `World.KitFx` |
| Dead oaks | They sway, groan every 7-13 s, and reach toward you within 16 studs. | `World.SpookyTree` |
| Beasts | The Hellhound's fire mane, the Night Stalker's shadow wisps and foot mist, the Crypt Bat's crimson wing streaks, the bone spider hanging over its lair, and BeastGaze (the Stalker freezes while watched). | `Features.Beasts` |
| Life | Chatter bubbles, the bell (`9113584435`), the seated chime, the Night Study candle warmth, regions and the place cards. | `Chatter`, `Moments`, `SchoolFx`, `Regions` |

**What the two places look like (Studio, read only):**

| | The Map | NH Combat Test |
|---|---|---|
| Lighting (Edit) | Brightness 3, Ambient and OutdoorAmbient (70,70,70), ClockTime 14.5 | Brightness 2, Ambient 0, OutdoorAmbient 70, ClockTime 13 |
| Fog | FogEnd 100,000 (off) | the same |
| Atmosphere | Density 0.30, Offset 0.25, Haze 0, Glare 0 | the same |
| Bloom, SunRays, DepthOfField | Bloom 1 / Size 24 / Threshold 2; SunRays 0.01, Spread 0.1 (effectively off); DepthOfField off | the same |
| Sky | a custom moon (`6444320592`), 3,000 stars, one skybox for every hour | the same |
| Clouds | **none** | **none** |
| SoundService | **AmbientReverb NoReverb**; no SoundGroups saved (the volume groups are made at run time) | the same |
| Sounds placed in the world | **0** | 27 |
| Ambience tags | 317 lamps, 1,253 candles, 511 ember emitters, 8 steam, **0 dust, 0 fog**, 150 swings | 46 lamps, 250 candles, 14 embers, 17 steam, 1 dust, 0 fog |
| Lights | 1,486 PointLights, 45 of them casting shadows | n/a |
| Regions and lairs | **no `workspace.Regions`, no `NHBeastLair`** | 25 region boxes, 5 lairs, 3 dorm doors |
| Lighting.Technology | the MCP isn't allowed to read it | n/a |

**What's missing, in short:**
1. **Sound is one layer.** There's a bed, but no 3D spot sounds and no random one-shots. The research's most repeated rule
   is three layers (below).
2. **No reverb, and nothing ducks the ambience.** Every room sounds the same; a fight and a quiet hall get the same
   ambience level.
3. **Only five beds.** There's nothing of its own for the cafeteria, gym, library, chapel, dorms, graveyard, the turf
   hangouts or the sports fields.
4. **The sky and air are flat.** There are no clouds, no daytime haze and no fog emitters placed anywhere. The god rays
   are off, and one skybox serves every hour.
5. **Rain is a particle curtain and a loop.** Nothing changes on a roof or a window, and there's no thunder, puddles or
   wet surfaces.
6. **The Map has none of the hooks.** There are no region boxes, so the soundscape zones, place cards and discovery all
   have nothing to read there. There are no lairs and no dust or fog tags. Its 1,253 candles and 511 ember emitters are
   already capped by the 3-emitter rule.

## What I learned (the research)

**How the videos were picked:** I ran 17 YouTube searches and compared about 170 candidates by source, length, views and
depth. I chose GDC talks by the studios' own audio and art leads, one Digital Foundry deep dive, and the two most
detailed Roblox breakdowns: they show every value on screen. I skipped short "make your game 10x better" clips and
engine tutorials, and INSIDE's rendering talk, which is mostly for programmers.

| # | Video | Why it was picked |
|---|---|---|
| 1 | [Finding Space For Sound: Environmental Acoustics in The Division 2](https://www.youtube.com/watch?v=mN56EauPhPQ) (GDC, 38 min) | Massive's audio director and audio programmer give real algorithms and numbers |
| 2 | [Designing the Bustling Soundscape of New York City in Marvel's Spider-Man](https://www.youtube.com/watch?v=idGHSezExTs) (GDC 2019, 58 min) | layering, distance bands, night changes, budgets, ducking |
| 3 | [The Sound of Horror: Resident Evil 7](https://www.youtube.com/watch?v=By_dCUApwkw) (GDC 2017, 66 min) | a haunted house, from Capcom's composer, sound programmer and designer |
| 4 | [A Plague Tale Audio Design: Not Only Squeaks](https://www.youtube.com/watch?v=HLikRVSxUWk) (GDC, 21 min) | swarms, and telegraphing a creature by sound |
| 5 | [Interior Design and Environment Art: Mastering Space, Mastering Place](https://www.youtube.com/watch?v=WWXsmnlmADc) (GDC 2015, 61 min) | wayfinding, zoning, lived-in rooms |
| 6 | [The Art of Firewatch](https://www.youtube.com/watch?v=SdxQ3HlhTE8) (GDC 2015, 27 min) | the sky, colour scripts, stylised fog, mood palettes |
| 7 | [Tech Focus: Volumetric Lighting, God Rays and Fog](https://www.youtube.com/watch?v=G0sYTrX3VHI) (Digital Foundry, 20 min) | every way games fake god rays and fog, and what gives each one away |
| 8 | [Can We Do It with Particles? VFX Learnings from Returnal](https://www.youtube.com/watch?v=qbkb8ap7vts) (GDC, 27 min) | environmental particles that react to the player |
| 9 | [How Big Budget AAA Games Render Clouds](https://www.youtube.com/watch?v=Qj_tK_mdRcA) (SimonDev, 11 min) | how sky depth and cloud light work |
| 10 | [How I Do Lighting & Atmosphere in Roblox](https://www.youtube.com/watch?v=UlvSrWHESwA) (RingWorld Studio, 12 min) | full Roblox day and night presets on screen |
| 11 | [Roblox: Atmosphere and Custom Lighting Zones](https://www.youtube.com/watch?v=UYnn9JF8qCc) (Emancyphur, 13 min) | Atmosphere ranges and how its properties depend on each other, plus code that tweens a look per zone |


**Caveats:**
- **Plague Tale:** its English captions failed (YouTube rate-limited them), so its notes come from the slides.
- **Sparse frames:** 50 frames over an hour is one every 70-80 s, so some slides were missed.
- **My numbers:** where an idea below gives a number the videos didn't, it's marked *(suggested)*.

### Sound (S1-S11)
- **S1. Three layers.** A 2D low room-tone bed, 3D spot sounds on props, and random one-shots. RE7 had 5 spot sounds in
  one kitchen (19:52-21:27). Spider-Man's bed has every recognisable sound stripped out, so nothing stands out on repeat
  (06:01). The Division gives each room a seamless 15-second room tone (30:26).
- **S2. Distance bands.** One-shots are mixed separately as close, medium, far and "sky" (Spider-Man 07:32).
- **S3. Smooth values, not switches.** The Division measures "openness" with 3 rays a frame, 12 directions over 4
  frames, smoothed over about 0.5 s, ignoring changes under 5% (13:05-14:36). That one value drives reverb, echo and
  one-shot density (15:36). Spider-Man does the same with height and with the people and cars around the player
  (17:58-23:45).
- **S4. Reverb follows the room.** RE7 chooses it from the room a sound is in, which cost about a third of the
  hand-placed method (23:16). The Division baked 2,500+ rooms (26:43). Spider-Man generated its reverb zones (15:56).
- **S5. Only walls block sound.** Geometry is tagged as blocking or not, so railings and fences don't muffle (Division
  09:19). Occlusion depends on the material in between (RE7).
- **S6. Restraint.** "Made everything flat, turned it down" (Spider-Man 14:42). Too many scary sounds and players get used
  to them (RE7 05:13). Dropping the level or going silent before a scare works best (RE7 22:55, 54:03).
- **S7. Ducking.** Combat and music duck the ambience: "in combat the city goes way down". Cutscenes lose the close,
  distracting layers but keep the bed, so there's no audible hole (Spider-Man 55:07).
- **S8. Night changes the sound, not just the level.** Spider-Man re-EQs its night beds colder with more low-mids, uses a
  different reverb, and switches to night one-shots: dogs, street racing (23:45).
- **S9. Weather plays on the world.** The Division plays rain and wind on silent props by material, and rain overhead
  strongly sells being indoors (34:25). Spider-Man sets rain loudness from a ray to the ground (17:58).
- **S10. Musical grammar.** A stinger every time the rats appear, and the same stinger later says it's safe to pass.
  Breathing and music layers follow two shared values: detection and the nearest guard's distance. A heartbeat plays
  only when the detection state changes (Plague Tale 13:36-18:16).
- **S11. Sounds from motion.** Squeaks and foley come from animation speed and bone speed crossing a threshold (RE7 26:18,
  Plague Tale 09:21). Audio updates are thinned out so they don't cause frame spikes (RE7 34:07).

### Light, sky and air (V1-V10)
- **V1. The sky is half the screen and drives the lighting.** Firewatch's sky was tuned by eye rather than physically
  correct, and its sky, sun and fog colours blend as you cross trigger volumes (Firewatch 08:19-10:23).
- **V2. Fog stays clear near you and gains colour with distance.** The first ~25% of Firewatch's fog strip is
  transparent, about 6 value bands step lighter with distance, and the distance is cool behind a warm foreground
  (Firewatch 06:45-13:27).
- **V3. One scene, many moods from the palette alone** (Firewatch 13:27). This is exactly the full, new, crimson and blue
  moons.
- **V4. A colour script per area** (Firewatch 16:02). **Detail signals importance** (23:49).
- **V5. Wayfinding:**
  - **Identity:** each wing gets a landmark and its own colour (Interior Design 09:55).
  - **Repetition:** identical repeating halls disorient, which suits only a nightmare (12:57).
  - **Zoning:** split big rooms with floors, rugs, dropped ceilings and pendant lights (14:29).
  - **Welcome and refusal:** an open door spilling light invites you in; a chained door refuses you (38:05).
- **V6. Mystery and pacing.** Glimpse something far away and unexplained (21:39). Spread novelty out: "everything is
  memorable, nothing is memorable" (29:20). Tight spaces should release into big ones (29:50). **Lived-in rooms show
  their owner** (36:03).
- **V7. God rays need something to break them,** like window tracery or tree trunks (DF 00:38, 10:40). Light cards fade
  as you get close, so they never read as cards (06:45). Unreal (1998) gave each torch its own tinted fog, flickering in
  time with the flame (07:47). Knee-height fog is a mood tool (16:01). A hard fog cut-off line gives the trick away
  (17:04). Red Dead Redemption 2 puts warm gas-lamp halos in cool fog (17:46).
- **V8. The world reacts to the player.** Returnal's fluid grid follows the player, so grass, particles and fog all
  stir (18:06). Wall "murals" knocked loose drift and come back (21:12). Their regret: effects only programmers could
  tweak (06:33).
- **V9. Sky depth.** Big near clouds and small hazy far ones, plus a silver lining from forward scattering (SimonDev
  03:41, 09:56).
- **V10. Roblox values:**
  - **RingWorld:**
    - **Night:** Ambient (12,12,12) on an Atmosphere of Density 0.479, Haze 2, Decay (190,195,197), with Clouds at
      Cover 0.754 and Density 1. One focal light, and two PointLights per lamp: a bright short core plus a dim long
      spill (07:04-09:03).
    - **Day:** Atmosphere Density 0.239, Haze 1.79, Glare 0.27, with SunRays at 0.077 / Spread 0.815 (03:40-05:38).
    - **Storage:** presets kept as Lighting folders.
  - **Emancyphur:**
    - **Dependencies:** Glare needs Haze > 0, and Decay needs both. Haze and Glare run 0-10; Density and Offset run 0-1.
    - **Haunted fog:** Density 0.643, Haze 2.56, Glare 2.44, Decay (85,85,127) (02:48).
    - **Zones:** invisible parts carry their look as attributes, which the client tweens in over 1 s (Sine, Out), one
      zone at a time.

## Concepts

Sizes: **S** is about a day, **M** a few days, **L** a week or more. Every idea follows the VFX bible: client-side
only, tag-driven (rule W1), with the Ambient tier's budgets (10 particles a second per emitter, 3 emitters, 120 studs).
Every idea honours Reduce Motion, Reduce Flashing (never above 3 Hz, full-screen at most 0.25) and Effects Quality.

### A. Foundations (the rest builds on these)

1. **The ambience mixer (M).**
   - **What it is:** SoundGroups for Ambience, Weather, One-shots and World, under the existing Music & Ambience
     volume.
   - **Ducking:** a CompressorSoundEffect with its SideChain set to a Combat group pulls the ambience down while you're
     combat-tagged, and returns it slowly.
   - **Cutscenes and talk shots:** these drop the one-shots and spot sounds and keep the bed (S7).
   - **Numbers:** *(suggested)* -6 dB in a fight, a 0.1 s attack and a 1.5 s release.
   - **SFX:** none of its own.
   - **Why:** S6, S7. Ambience can never drown a tell.
   - **Builds on:** Soundscape's `NH_Master.NH_Music` route, `CombatTag`, the talk cinematic, `Gui.Cinematic`.
2. **Three-layer ambience engine (M).** Extend Soundscape from one bed to three layers:
   - **Bed:** the 2D bed, as today.
   - **Spot sounds:** 3D sounds on tagged props: `NHAmbientSound:<Kind>` (a clock, a radiator, a vending machine, a
     candle cluster, a pipe), each with an InverseTapered rolloff.
   - **One-shot pool:** random one-shots per zone and per day or night, picked from distance bands (close, medium, far,
     sky).
   - **Limits:** *(suggested)* one every 6-20 s, ±40% timing, ±5% pitch and ±2 dB per play, no repeat of the last 3, at
     most 4 at once. Spot sounds switch off beyond their hearing range (Spider-Man's crash lesson).
   - **Why:** S1, S2.
   - **Builds on:** `Config.Ambience.Beds`/`ZoneBed`, rule W1, the `Ambient` controller's nearest-first culling.
3. **Room reverb (S).**
   - **What it is:** each zone names a `ReverbType` (halls StoneCorridor, classrooms Room, library LivingRoom, chapel
     ConcertHall, gym Arena, boiler SewerPipe, dorms LivingRoom, bathrooms Bathroom, outdoors Plain, graveyard Forest).
   - **How:** the client sets `SoundService.AmbientReverb` on entry.
   - **SFX:** footsteps, fists and voices finally sound like the room they're in.
   - **Why:** S4. One setting per zone, like RE7's room-based pick.
   - **Builds on:** the soundscape's zones and the region boxes.
   - **Note:** AmbientReverb applies to every sound. If UI clicks pick up a tail, move world sounds to the newer Audio
     API (`AudioReverb` on a world bus).
4. **Openness value (M).**
   - **What it is:** an openness value (0 to 1), smoothed over 0.5 s, from a few rays a frame spread round and up, like
     The Division's.
   - **What it drives:** the indoor and outdoor crossfade, wind level, the outdoor echo, one-shot density, and how strong
     the rain sounds. It replaces today's single roof ray.
   - **Why:** S3, S5. Only parts tagged as walls count, so iron railings and the dead oaks don't muffle.
   - **Builds on:** Soundscape's roof raycast, the KitFx rain's "inside" check.
5. **Zone looks (M).**
   - **What it is:** region boxes carry optional look attributes (Atmosphere Density, Haze, Color and Decay, an
     exposure offset, a tint). The client tweens them in over 1-2 s (Sine) on top of DayCycle, one zone at a time.
   - **What changes:** the library is dusty-warm, the chapel cool with candle gold, the boiler yard hazy amber, the
     graveyard low-fogged.
   - **Why:** V1 (Firewatch's volumes) and V10 (Emancyphur's pattern).
   - **Builds on:** `Regions` (priority, then the smaller box), and DayCycle and LightingStack, so it never fights a
     menu or cutscene layer.
6. **The Map's hooks (S, builder plus a script).**
   - **What it is:** `workspace.Regions` boxes, soundscape zones, `NHBeastLair` spots, and dust and fog tags for the
     Map, plus a check that lists anything untagged.
   - **Why:** without them, everything in this doc is silent on the Map, which has no regions, no lairs, no dust and no
     fog today.
   - **Builds on:** `build_regions.luau`, the Map core add-on (`NHCore`).
7. **Original sound pack (M, ongoing).**
   - **What it is:** use the offline synthesiser (`tools/sfx`, with its stone-hall impulse response) to make our own
     one-shots: stone settling, wood ticks, a far bell, chains, the chapel organ hum, wind through tracery. They're
     original, gore-free and need no licence.
   - **Why:** S1. Variety comes cheap when sounds are generated.
   - **Builds on:** `racial_grips.py`, decision D4 (Creator Store sounds stay as the fallback).

### B. The school by area

**The halls (the Main Hall, the East Wing, stairs, lockers)**

8. **Lived-in halls by period (S).**
   - **SFX:** a distant-student murmur under the bed during passing periods and lunch (it swells for the 25 real seconds
     between classes). Locker slams and a dropped book as close one-shots; footsteps on stone far off.
   - **VFX:** dust motes in the sun shafts through the hall windows by day.
   - **Why:** S1, S3 (density follows activity, like Spider-Man's crowd count).
   - **Builds on:** `PeriodChanged`, the hall bed (`9116260218`), `NHAmbient:Dust` (none placed on the Map yet).
9. **After-hours halls (S).**
   - **When:** after 21:00.
   - **SFX:** the murmur goes. The bed turns colder (S8): a low draught, the building settling (stone ticks, a pipe knock
     every 20-60 s), the hall clock's tick close by, and the custodian's cart and keys far off.
   - **VFX:** thin knee-height fog creeps in at the ends of the long corridors.
   - **Why:** S6, S8, V7.
   - **Builds on:** the night bed (`9118747853`), the custodian in `Chatter`.
10. **Lamplight with halos (S).**
    - **VFX:** every hall sconce gets RingWorld's two lights (a bright 6-8 stud core plus a dim 20-stud spill) and a soft
      sprite halo that fades as you get close. A slow flicker comes from the existing smooth noise.
    - **Why:** V7 (warm halos in cool air) and V10.
    - **Builds on:** `NHCandle` flicker, the lamp kit (batch 19), the 45-shadow-light budget (keep spill lights
      shadowless).
11. **Light through the tracery (M).**
    - **VFX:** Beam "god ray" cards from the gothic windows at dawn and dusk only, angled to the sun. They fade as you
      get near and are hidden when the sun is behind the wall.
    - **Why:** V7. Tracery is exactly what breaks a light shaft up.
    - **Builds on:** the window kit, DayCycle's dawn and dusk keys, SunRays (0.01 today).
12. **Wayfinding colour per wing (S).**
    - **VFX:** each wing's lamps and banners carry one accent (the Main Hall candle gold, the East Wing ink blue) and one
      landmark light: a lit portrait, a stained-glass glow.
    - **Why:** V5.
    - **Builds on:** the region cards, the art and tapestry kits, the Theme palette.

**The classrooms (R101-R106)**

13. **Class in session (S).**
    - **SFX:** the classroom bed (0.14), plus chalk taps and scratches from the board, a page turn, a chair creak, the
      clock tick, and a teacher's murmur bleeding faintly through the door from outside.
    - **VFX:** chalk dust puffs when the board is written on; dust motes in the window light.
    - **Why:** S1, S11 (chalk sounds from the board animation).
    - **Builds on:** lesson boards (`Activities`), `SchoolFx`'s seated chime, the chalkboard props.
14. **Subject flavour (S).**
    - **Chemistry:** a glass clink and a faint burner hiss; a thin wisp over the benches.
    - **History:** the map rustling.
    - **Detention (R106):** dead quiet: one clock, a dripping tap, a dim cold light.
    - **Why:** V4 (detail signals importance), S6.
    - **Builds on:** `Config.Classes` rooms.
15. **The empty classroom at night (S).**
    - **VFX:** moonlight through the windows (a cool spill), chairs as silhouettes.
    - **SFX:** a draught, the board's chalk ledge ticking as it cools, and a rare desk-lid tap.
    - **Why:** S6.
    - **Builds on:** the night grade.

**The cafeteria and the Commons**

16. **Lunch rush (S).**
    - **SFX:** a new Cafeteria bed. A clatter of trays and cutlery that swells for Lunch (11:25-12:00), the queue's
      chatter, the fryer and steam-table hiss as spot sounds, and the till.
    - **VFX:** steam off the counters and bowls; warm lamps over the serving line.
    - **Why:** S1, S3 (the crowd count drives the bed's level).
    - **Builds on:** the Lunch segment, the concession stand, the `NHLunchSpot` queue, `TrayFx`, the `NHAmbient:Steam`
      tag.
17. **After lunch (S).**
    - **SFX:** the room empties to a hum (a fridge, a buzzing tube).
    - **VFX:** a slow drift of steam off the dish window.
    - **Why:** S6 (quiet makes the rush land).

**The gym and the sports fields**

18. **The gym's voice (S).**
    - **SFX:** an Arena reverb, ball bounces and sneaker squeaks as one-shots during club hours, the scoreboard buzz, and
      the hum of the high lamps.
    - **VFX:** chalk and dust in the high window light.
    - **Why:** S4, S11 (squeaks from players' turns).
    - **Builds on:** Sports, the pitch floodlights (`NHLamp`).
19. **Floodlit pitch at night (S).**
    - **VFX:** moths and dust in the floodlight cones, and halo sprites on the heads.
    - **SFX:** the lamps' buzz. A crowd swell is already part of the goal flare.
    - **Why:** V7.
    - **Builds on:** the 4 floodlights' 18:30 switch-on, the goal celebration.

**The library and the Archive**

20. **Hush (S).**
    - **SFX:** a new Library bed: near silence, paper, a far cough, the fire's tick, the librarian's stamp.
    - **Mix:** one-shot density is the lowest in the school, and talking volume feels louder by contrast.
    - **VFX:** heavy dust motes in the lamp light; candle halos on the reading tables.
    - **Why:** S6, V4.
    - **Builds on:** the library kit (batch 30), the library card, `NHCandle`.
21. **The Archive after dark (S).**
    - **SFX:** keep its eerie choir bed and add rare paper rustles that move between the shelves, the book-fall prop's
      thump, and a page turning by itself (once a visit at most).
    - **VFX:** dust stirred into the air when you pass close to a shelf.
    - **Why:** S6 and V8 (the room reacts to you).
    - **Builds on:** the Archive bed (`9125602882`), the book-fall bookcases, `NHAmbient:Dust`.

**The dorms and your room**

22. **The dorm wing (S).**
    - **SFX:** a LivingRoom reverb. Muffled music through a door, a laugh, a shower running far off, the radiator's
      knock.
    - **When:** after curfew the wing quiets to the radiator and wind at the windows.
    - **Why:** S1, S8.
    - **Builds on:** `NHDormWing`, `NHHomeDoor`, `Features.Homes`.
23. **Your room follows your grades (S).**
    - **VFX:** Spotless gets warm steady light and a calm clock. Lived-in gets a lamp a little dimmer. A wreck gets
      flicker, a dripping tap and a buzzing bulb.
    - **SFX:** rain on the window on rain nights. Night FM plays from the radio when the phone app is on.
    - **Why:** V6 (lived-in rooms show their owner) and S9.
    - **Builds on:** the room's five states and the `NHHomeLight` attribute, the phone's Night FM.

**The chapel**

24. **Sanctuary (M).**
    - **SFX:** a ConcertHall reverb. A faint organ drone (synthesised), the Chapel Choir faintly from the loft in the
      evening, and the creak of the pews.
    - **VFX:** votive glow, incense smoke curling in the light, coloured light from the stained glass on the floor
      (Beams).
    - **Why:** S4, V7.
    - **Builds on:** the Chapel region, the votives and altar (`ObjectFx`), the Priest race.
25. **The safe room (S).**
    - **What it is:** the chapel is where the sound calms: the beast stingers stop and the bed warms. It's the one place
      at night that feels safe.
    - **Why:** RE7's safe-room music and S10.
    - **Builds on:** Night Chill (the chapel roof already clears it).

**The boiler yard**

26. **The machine (S).**
    - **SFX:** keep the boiler bed. Add pressure-valve hisses with a steam burst, pipe knocks, a furnace door's clank
      and a fan's rattle, in the SewerPipe or Hangar reverb.
    - **VFX:** steam bursts timed to the hiss, ember spit from the firebox, a hot orange spill from the furnace door
      flickering in time with it.
    - **Why:** S1; V7 (light and fog tinted together, as in Unreal 1998).
    - **Builds on:** `NHAmbient:Steam/Embers`, the boiler bed (`9112839511`), the Hellhound's lair.
27. **Hellhound territory (S).**
    - **When:** at night near the lair.
    - **SFX:** the boiler's hum drops a little (S6). A low growl rolls round the yard (far band) before it shows.
    - **VFX:** cinders drift on the air.
    - **Why:** S10 (a telegraph, not a trick).
    - **Builds on:** `Features.Beasts`, the Hellhound's fire mane.

**The graveyard** (waiting for the builder; the ghoul's lair is a placeholder)

28. **Ground fog among the stones (M).**
    - **VFX:** knee-height `NHAmbient:Fog` volumes between the graves, night only, removed on Low quality. A haunted-fog
      Atmosphere zone (V10, Emancyphur's 0.64 Density, 2.5 Haze, a violet Decay) under a pale moon.
    - **SFX:** a Forest reverb; wind through the yews, a crow's call, the iron gate's slow creak.
    - **Why:** V7 (knee-height fog), V2.
    - **Builds on:** the defined but never-placed Fog emitter, zone looks (5).
29. **The ground stirs (S).**
    - **When:** a Grave Ghoul's emerge.
    - **VFX:** earth crumbs and fog pushed out in a ring (no gore).
    - **SFX:** a deep grinding and a scrape, and the crows going quiet a second before.
    - **Why:** S6, S10 (silence as the tell), V8.
    - **Builds on:** the ghoul's Emerge clip.

**The grounds (the front yard, courtyards, gate, the Back Lot, the West Edge)**

30. **Wind (M).**
    - **What it is:** one wind value drives everything: `workspace.GlobalWind` sways terrain grass and pushes particles
      (`WindAffectsDrag`), the wind bed swells, the dead oaks sway harder, and leaves skitter on the ground. Gusts
      every 20-60 s.
    - **Why:** V8 (one shared simulation moves grass, particles and sound), S3.
    - **Builds on:** `SpookyTree` (raise its sway amplitude with the gust), the grass sets.
31. **Falling leaves and ash (S).**
    - **VFX:** a few leaves from the dead oaks (2-4 a second near a tree, *suggested*), carried by the wind.
    - **SFX:** the leaves' skitter on stone.
    - **Why:** V8.
    - **Builds on:** the DeadOak prop, `NHAmbient` (a new Leaves kind).
32. **Night outside (S).**
    - **SFX:** keep the crickets bed and add a far-band owl, a distant dog, the town bell beyond the gate at the hour,
      and wind in the gutters.
    - **VFX:** lamp halos on the gas lamps; fireflies in summer only, if seasons come.
    - **Why:** S2, S8.
    - **Builds on:** the outdoor night bed (`9112764573`), the gas lamps.
33. **The bell tower (S).**
    - **SFX:** the school bell heard across the grounds, delayed and echoed by distance, not only on the HUD.
    - **VFX:** crows lift from the roof when it rings.
    - **Why:** S2 (the "sky" band) and V6 (a landmark you hear).
    - **Builds on:** the bell sound (`9113584435`), `PeriodChanged`, the crow flock art (`art/vfx/crow`).

**Turf and hangouts (the Crimson Parlor, the Den, the Ink Studio, the Staff Room, the Records Office)**

34. **A sound and light signature per hangout (S each).**
    - **The Crimson Parlor:** a gramophone waltz on a far speaker, crimson silk lamps and velvet hush.
    - **The Den:** a fire pit's crackle, a low radio, embers.
    - **The Ink Studio:** a nib's scratch and the tarot table's candle.
    - **The Staff Room:** a kettle, ticking, a typewriter.
    - **The Records Office:** a filing drawer, a hum, one cold lamp: forbidden and unwelcoming.
    - **Why:** V5 (identity), V6.
    - **Builds on:** `NHCliqueAreas`, region kinds (Turf or Forbidden), the seer table.
35. **Doors that invite or refuse (S).**
    - **VFX:** forbidden doors show a thin cold line of light under them. Open, welcoming rooms spill warm light into the
      hall.
    - **SFX:** a locked door's rattle.
    - **Why:** V5 (Interior Design's admittance through light).
    - **Builds on:** the door kit, the Forbidden region kind, the dorm keys.

### C. Time of day

36. **Dawn chorus and the first bell (S).**
    - **When:** 6:00-8:00.
    - **SFX:** birds come in (far, then medium), the boiler wakes up, the town stirs beyond the gate.
    - **VFX:** low mist burns off the lawns between 6:30 and 7:30, and dust shafts appear in the east windows.
    - **Why:** S8, V3.
    - **Builds on:** the Dawn key (6.5), the morning fog idea (28).
37. **Daytime haze (S).**
    - **What it is:** daytime Atmosphere Haze goes from 0 to a little *(suggested 0.8-1.2, Glare 0.2)* so the far
      grounds sit back in the air.
    - **Why:** V2.
    - **Builds on:** `Config.DayCycle.Day`.
38. **Dusk (S).**
    - **When:** 16:30-18:30.
    - **VFX:** long amber god rays through the windows (11), and the lamps lighting one by one (they already stagger).
    - **SFX:** the day birds fade out and the crickets fade in over 20 game minutes, and the lamps' click and hiss as they
      light.
    - **Why:** S8, V3.
    - **Builds on:** `NHLamp`'s 18:30 stagger.
39. **Curfew and lights-out (M, needs a curfew rule).**
    - **When:** at 22:00 *(suggested)*.
    - **VFX:** the halls' lamps step down to night lights, room by room, with a soft click.
    - **SFX:** the far bell, and the custodian's keys locking the doors.
    - **Why:** V6 (the light changes tell a story), S6.
    - **Builds on:** VFX bible "optional: curfew and lights-out", `Doors`.

### D. Weather

40. **Rain you hear on things (M).**
    - **SFX:**
      - **On roofs:** a roof drum overhead, by roof material: slate, lead or glass.
      - **On glass:** streaks on the windows.
      - **Gutters:** gutters running and drains gurgling.
      - **Leaves:** a soft hiss on the leaves.
      - **How:** all of it is driven by the openness value (4) and played on silent tagged props (S9).
    - **VFX:** splash rings on the ground around you, and drips falling off the eaves.
    - **Why:** S9. Rain overhead is the strongest "you're indoors" cue.
    - **Builds on:** KitFx rain (`NHRain`), the roof kit's materials, the rain loop.
41. **Wet world (M).**
    - **VFX:** during and after rain, the ground darkens and gets shinier (a MaterialVariant swap or a lower roughness on
      key paths), with puddle decals that ripple. It dries over one game hour.
    - **SFX:** wet footsteps.
    - **Why:** V4.
    - **Builds on:** the PBR materials (`tools/vfx/make_pbr_materials.py`), the grass sets.
42. **Thunderstorms (M).**
    - **What it is:** a stronger form of a rain night (1 in 3 rain nights, *suggested*).
    - **VFX:** sky flashes (an Atmosphere and grade pulse, never a white screen, never above 3 Hz). Under Reduce
      Flashing it's a slow glow, as with the menu's lightning.
    - **SFX:** thunder delayed by distance, 1-6 s after the flash, rolling in the far and sky bands.
    - **Why:** S2, the accessibility rules.
    - **Builds on:** the main menu's lightning and its Reduce Flashing version, `Fx.ScreenFlash`.
43. **Fog nights (M, new weather).**
    - **When:** a 1 in 6 night *(suggested)*.
    - **VFX:** the Atmosphere thickens to about 0.6 Density near the ground, with knee fog on the grounds and lamps as
      haloed islands.
    - **SFX:** foghorn-like boiler blasts, damped birds, and footsteps that sound closer.
    - **Effect on play:** beasts are seen later but heard earlier, so their telegraphs matter more.
    - **Why:** V2, V7, S10.
    - **Builds on:** zone looks, the Fog emitter, `NHRain`'s weather slot.
44. **Wind and frost (S, a Night Chill extension).**
    - **What it is:** frost creeps on the windows on Chill nights. Your breath already shows; let others' breath show too.
    - **SFX:** a colder wind bed.
    - **Why:** S8.
    - **Builds on:** Night Chill's frost breath and screen frost.
45. **A weather mark on the clock (S, UI).**
    - **What it is:** the clock shows tonight's weather beside the moon icon (rain, storm, fog), in a new PBR animated
      glyph set made like the moon icons (falling-line rain, drifting fog).
    - **What else:** the Midnight Bell's SKYWATCH forecasts it.
    - **Why:** V6. Players look forward to the weather.
    - **Builds on:** the clock's moon icons, SKYWATCH.

### E. Moon phases and events

46. **The sky wears the phase (M).**
    - **What it is:** each phase is a palette swap of the same night (V3):
      - **Full:** a bright silver rim light and stronger moon shadows.
      - **New:** darkest, starriest, with a bigger focal pull to lamps.
      - **Waxing and waning:** in between.
    - **How:** DayCycle's night key gets a per-phase look (Ambient, OutdoorAmbient, Atmosphere Decay).
    - **Why:** V1, V3.
    - **Builds on:** `NHMoonGrade`, `NHNewMoonGrade`, the 6 moon textures.
47. **Full-moon soundscape (S).**
    - **SFX:** a far wolf call now and then, crickets thinning, and a high, airy pad faint under the night bed.
    - **VFX:** the full moon lifts the knee fog's brightness.
    - **Why:** S8, S10.
    - **Builds on:** `World.FullMoon`, the Werewolf amber eyes.
48. **The crimson moon (M).**
    - **VFX:**
      - **Air and sky:** crimson Atmosphere Decay, a red rim on clouds near the moon, crimson glints in the fog.
      - **Lamps:** a slow pulse of the candle light toward crimson (glass and wax, never blood).
      - **Rare dramatic moment:** a red bloom on the stained glass.
    - **SFX:** the crickets stop. A low choral drone joins the bed, and a far bell tolls once at midnight. The Archive
      choir is louder.
    - **Why:** V3, S6, S8.
    - **Builds on:** the crimson grade and its moon texture (hairline fissures, a red corona), its banner and front page,
      the Vampires' crimson eyes, the shelved Nightmare Nights (P4-1).
49. **The blue moon (M).**
    - **VFX:** frost-bright rims on everything moonlit, a pale halo ring in the haze, cold Decay, and the chapel's glass
      glowing silver-blue.
    - **SFX:** a glassy, bell-like air tone, the wind dropping to calm, and the chapel's organ drone clearer.
    - **Why:** V3.
    - **Builds on:** the blue grade and its halo texture, the Priests' bonus, the chapel (24).
50. **Moonrise moment (S).**
    - **When:** on special-moon nights at 20:00.
    - **What it is:** the bed dips to near silence for 3 s, a low swell plays, and then the banner shows: silence before
      the moment.
    - **Why:** S6, S10 (musical grammar).
    - **Builds on:** the moon banners (`Moments`).
51. **Nightmare Nights, ambience part (L, shelved by the owner).**
    - **What it is:** if the event comes back, it gets its own colour script (crimson grade, a large pale-crimson moon,
      a banner), symmetrical "wrong" corridors with repeated details on purpose, which V5 says disorient, and a curfew
      bell.
    - **Why:** V4, V5.
    - **Builds on:** P4-1.

### F. Beasts at night

52. **Telegraph grammar (M).**
    - **What it is:** every beast gets three sound states:
      - **Near:** a far-band call, heard before it's seen.
      - **Hunting you:** a close one-shot plus a low layer under the bed.
      - **Gone:** a short release cue, the "safe" stinger.
    - **How:** the ambience reads two shared values, the nearest beast's distance and whether it's targeting you. A
      heartbeat plays only when the state changes.
    - **Why:** S10 (Plague Tale's two shared values and its stingers).
    - **Builds on:** `Features.Beasts`' targeting, `BeastGaze`'s "beast near" check, the Wounded heartbeat.
53. **The world reacts to beasts (S).**
    - **What it is:** when a beast is near, the night one-shots stop (crickets and birds go silent), the nearest lamps
      flicker once, and crows lift.
    - **Why:** S6 and V8 (silence as the tell, the world stirring).
    - **Builds on:** `NHCandle` flicker, the crow art.
54. **Per-beast signatures (S each).**
    - **Night Stalker:** a cold hush and its foot mist thickening while you look away, plus a faint cloth rustle when it
      moves; it freezes when watched.
    - **Bone Spider:** dry clicking on stone above you and thin threads in the lamp light.
    - **Crypt Bat:** wingbeats in the far band, then a screech with crimson streaks.
    - **Hellhound:** see 27.
    - **Why:** S11 (sound from bone speed: clicks from the leg tips, wingbeats from the wing joints).
    - **Builds on:** each beast's rig and clips, the Stalker's mist and the bat's streaks.
55. **No fake tells (rule).**
    - **What it is:** RE7's trick of random wood clicks being mistaken for enemies is good for unease, but no random
      ambience may copy a beast's real cue or the critical Kanji sound. Spooky one-shots stay wood, stone and air.
    - **Why:** S6, and fairness in combat.

### G. Lighting and skybox

56. **Night presets, retuned (S).**
    - **What it is:** a darker, more contrasty night that stays readable. Lower Ambient and keep OutdoorAmbient
      blue-violet. Add Atmosphere Haze about 2 with a cool Decay (RingWorld's 0.48 Density and Haze 2 as a reference),
      and let the lamps do the shaping.
    - **Why:** V7, V10. One focal light per view.
    - **Builds on:** `Config.DayCycle.Night`, D3's "readable" rule (dark outfits mustn't become silhouettes again).
57. **Clouds (S).**
    - **What it is:** a Terrain `Clouds` instance tuned per look:
      - **Day:** a light cover.
      - **Dusk:** coloured from the grade.
      - **Rain nights:** heavy (Cover about 0.75, Density about 1, like RingWorld).
      - **Full moon:** thin, so the moon shows.
    - **How:** clouds move with `GlobalWind`.
    - **Why:** V1, V9.
    - **Builds on:** nothing (there are no clouds today).
58. **A sky per time of day (M, art).**
    - **What it is:** painted gothic skyboxes for day, dusk, night and storm, made with the `tools/vfx` pipeline. Night
      gets a distant town silhouette and a faint aurora-like band on blue-moon nights. DayCycle swaps or blends them
      (two Sky layers can't blend, so the swap hides at dusk and dawn under the haze).
    - **Why:** V1 ("the sky is half the screen").
    - **Builds on:** the custom moons, `Sky.StarCount` swaps, the main-menu sky.
59. **Sun and moon rays (S).**
    - **What it is:** SunRays from 0.01 to about 0.05-0.08 at dawn and dusk, with a wide spread (RingWorld's 0.077 /
      0.815). Lower at night, so the moon gets a soft glow without blowing out.
    - **Why:** V7.
    - **Builds on:** Lighting.SunRays, the bible's "never raise global Bloom" rule (this doesn't).
60. **Lamp light that matches the source (S).**
    - **What it is:**
      - **Gas lamps:** about 2,700 K *(suggested)*.
      - **Candles:** deeper and redder.
      - **Floodlights:** a colder white.
      - **The Records Office:** a cold fluorescent green-white.
    - **Why:** V4 (colour by meaning), V7.
    - **Builds on:** the lamp kit, `NHLamp`, `NHCandle`.
61. **Local fog by light (S).**
    - **What it is:** each torch and brazier gets a faint tinted haze sprite that flickers with its flame, the 1998
      Unreal trick.
    - **Why:** V7.
    - **Builds on:** `NHCandle`'s smooth-noise flicker, the `nh_fog` texture.
62. **Interior and exterior exposure (S).**
    - **What it is:** stepping out of a dark hall into moonlight eases the exposure over about 1.5 s, like eyes
      adjusting.
    - **Why:** V1 (Firewatch's blends across volumes), V10 (a 1-2 s Sine tween).
    - **Builds on:** zone looks (5), `ExposureCompensation` in DayCycle.
63. **Lighting quality check (S).**
    - **What it is:** confirm `Lighting.Technology` is Future in both places (the MCP can't read it). Check the shadow
      lights on screen stay at 8 or fewer (the Map has 45 shadow-casting PointLights) and that candle emitters are
      capped.
    - **Why:** the bible's performance rules.

### H. Accessibility and settings

64. **Separate Ambience and Music sliders (S, UI).**
    - **What it is:** today one slider covers both. Add an Ambience slider (and Weather inside it) in Settings, drawn in
      the kit's PBR style with a sound-wave needle animation.
    - **Why:** S7. Players who want silence keep the music, or the other way round.
    - **Builds on:** `UI.Settings`, the mixer (1).
65. **Effects Quality for ambience (S).**
    - **What it is:**
      - **Low:** drops fog volumes, halves rain drops, mutes far one-shots, turns off god-ray Beams.
      - **High:** adds splash rings and leaves.
    - **Builds on:** the existing Effects Quality setting.

## Where I'd start

| Order | Concepts | Why |
|---|---|---|
| 1 | 1, 2, 3, 6 | The mixer, three layers, reverb and the Map's hooks. Without them everything else is either silent on the Map or drowns the fight. |
| 2 | 56, 57, 59, 37 | Night, clouds, rays and haze. A few hours of values that change every screenshot. |
| 3 | 8, 9, 13, 16, 20, 26 | The halls, classrooms, lunch, library and boiler: where players spend most of the day. |
| 4 | 40, 42, 30 | Rain on things, thunder and wind: the weather finally touches the world. |
| 5 | 46-50, 52-54 | Moons and beasts: the supernatural nights become something you hear and see coming. |
| 6 | 28, 24, 58 | The graveyard, the chapel and new skies: these wait on the builder and on art. |

## Your calls

- **Sound source:** keep Roblox's free Creator Store sounds (D4), make our own with the synthesiser, or both? I'd use
  both: the stores for beds and loops, synthesised one-shots for variety.
- **Reverb everywhere:** `AmbientReverb` gives fights, voices and footsteps the room's echo too. Is that what you want,
  or should combat stay dry?
- **Scare one-shots:** RE7-style random creaks and knocks in empty halls at night. How often? I'd say rare: about one per
  minute in the quietest places, never in a fight.
- **New weather:** the bible lists weather as "needs your approval". Should thunderstorms (42) and fog nights (43) join
  the rain nights? What about seasons (fireflies, frost, snow)?
- **Curfew and lights-out (39):** it needs a school rule as well as the look.
- **Nightmare Nights:** it's still shelved. Should the crimson moon ideas (48) stand in for it for now?
- **Skyboxes (58):** new painted skies need art and an upload. Make them, or keep tuning the current sky?
- **The Map:** the region boxes, zones and tags in the Map are the builder's place. Should I hand the builder a tagging
  list, or tag it myself through the `NHCore` add-on?
- **Lighting.Technology:** please check that it's Future in both places (Lighting > Technology); the MCP can't read it.
