# Sky and lighting (2.36, sky-2360)

The approved design is `docs/superpowers/specs/2026-11-21-sky-2360-design.md` (owner approval, 2026-11-21). This doc is
the working reference: the preset table, the moon and event modifiers, the sky-motion tiers, what to upload, how to wire
it, and how to test it. **Live in NH Combat Test from 2.39.0 (2026-11-23)**; the Studio results are in the last section and
the CHANGELOG.

## Owner rules
- **Nights are dark but readable.** Compared with 2.16, the blue ambient and the exposure go up and the contrast goes
  down. The darkness comes from contrast with lamps and lit windows, not from crushing everything to black.
- **Autumn is permanent.** Winter, Spring, Summer and Nightmare Nights are event seasons only.
- **Full sky motion:** drifting clouds, the night wisp ring, storm flashes, and a slow sky turn (gated on a seam check).
- **19 sky sets**, 6 faces each at 1024.

## Previews
| Sheet | What it shows |
|---|---|
| `art/skies-preview/NHSkies_Sheet.jpg` | all 19 skies as 360° panoramas, re-projected from the faces that get uploaded |
| `art/skies-preview/NHSky<Set>_preview.png` | one set: panorama, two cube corners and the zenith (where seams would show) |
| `art/skies-preview/seams.txt` | every face edge measured; worst excess per set |
| `docs/img/sky-2360/Sky2360_Autumn.jpg` | the seven autumn times of day, plus the 2.16 night for comparison |
| `docs/img/sky-2360/Sky2360_Moons.jpg` | full, new, crimson and blue moon nights, and the storm |
| `docs/img/sky-2360/Sky2360_Events.jpg` | Winter, Spring, Summer and Nightmare Nights |

The scene previews are a Blender approximation of Roblox (painted sky as the background and the ambient light, a sun or
moon key, distance fog for the Atmosphere, lamps and lit windows). Use them to judge the look and compare variants, not
as exact Roblox values. Two students stand on the path, one in a dark outfit and one in the crimson uniform: both
must stay readable at night.

Rebuild everything:
```
python tools/vfx/make_skyboxes.py                 # 114 faces + art/skies-preview (about 15 min on 10 workers)
python tools/sky-2360/contact_sheet.py
python tools/vfx/make_wisps.py
python tools/sky-2360/gen_config.py               # the proposed Config.DayCycle
python tools/sky-2360/equirect.py E:/tmp/pano
python tools/sky-2360/equirect.py E:/tmp/pano216 2048 <a folder with the 2.16 NHSkyNight_*.png> Night   # then rename to Old_Night.png in E:/tmp/pano
E:/Blender/blender.exe -b --factory-startup -P tools/sky-2360/preview_scene.py -- E:/tmp/pano E:/tmp/raw
python tools/sky-2360/post.py E:/tmp/raw
```

## 1. Sky sets
| Set | Shown | Status |
|---|---|---|
| `Day` | 08:00 to 17:36 | unchanged; 2026-11-13 ids stay |
| `Dusk` | 17:36 to 19:36 | unchanged; 2026-11-13 ids stay |
| `Dawn` | 05:36 to 08:00 | **new**: painted on its own (rose-gold, sun at +X). The old turned-dusk dawn is dropped |
| `Night` | 19:36 to 05:36 (full, waxing, waning moons) | **repainted** in the B style: an ink-blue zenith, a lit horizon band, moonlit cloud banks kept off the moon's path |
| `NightNew` | a new-moon night | **new**: the deepest sky, still with a lit horizon so the skyline reads |
| `NightCrimson` | a crimson-moon night | **new**: blood-dark cloud undersides with a red rim, a red corona where the moon rises |
| `NightBlue` | a blue-moon night | **repainted**: the aurora band on the +Z side, in the new style |
| `Storm` | workspace `NHSky = "Storm"` | **restyled**: the 2.16 storm, nudged toward the new nights' blue |
| `WinterDay` / `WinterDusk` / `WinterNight` | the Winter event | **new**: a snow-light overcast, a lilac-gold dusk, a cold clear night |
| `SpringDay` / `SpringDusk` / `SpringNight` | the Spring event | **new**: a soft green-gold day, a pink dusk, a misty night |
| `SummerDay` / `SummerDusk` / `SummerNight` | the Summer event | **new**: a high, warm day, a long amber dusk, a short bright night |
| `NightmareDusk` / `NightmareNight` | Nightmare Nights | **new**: a blood-red dusk, then a crimson night with ember-lit clouds |

The painters keep make_skyboxes' rules:
- **No moon and no stars are painted.** Roblox draws them.
- **The moon's path stays clean.** It rises at +X, crosses the −Z side and sets at −X. Night clouds sit low on the −Z
  side and only climb on the +Z side, and the moving wisp Beams are what cross the moon.
- **The house palette applies.**

## 2. Time-of-day keys (autumn)
The client blends neighbouring keys by school hour with a smoothstep, as it does today.

| Hour | Key | Sky (swap) |
|---|---|---|
| 0 | Night | Night |
| 1 to 4 | Witching | Night |
| 5 | Night | Night |
| 6 | Dawn | Dawn (from 5.6) |
| 7.5 | Morning | Day (from 8.0) |
| 9.5 to 16 | Day | Day |
| 17 | Golden | Day |
| 18.5 | Dusk | Dusk (from 17.6) |
| 20 to 24 | Night | Night (from 19.6) |

Values in Roblox units (colours 0-255). The single source is `tools/sky-2360/presets.py`.

| Key | Ambient | OutdoorAmb | Bright | ColorShift Top / Bottom | EnvDiff / EnvSpec | Exposure | Atmos Density / Offset / Haze / Glare | Atmos Color / Decay | Clouds Cover / Density / Color | Grade Bright / Contrast / Sat / Tint | Bloom Int / Size / Thresh | SunRays Int / Spread |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Dawn | 34,30,40 | 120,104,118 | 2.0 | 255,206,170 / 60,44,76 | 0.6 / 0.6 | 0.05 | 0.34 / 0.2 / 1.4 / 0.6 | 230,200,196 / 150,120,140 | 0.55 / 0.45 / 255,214,196 | 0 / 0.04 / -0.04 / 255,236,226 | 0.9 / 32 / 0.95 | 0.06 / 0.6 |
| Morning | 24,24,30 | 110,110,116 | 2.6 | 255,240,220 / 0,0,0 | 0.8 / 0.8 | 0 | 0.3 / 0.25 / 0.6 / 0.3 | 210,206,200 / 120,124,136 | 0.5 / 0.4 / 240,236,232 | 0 / 0.04 / -0.04 / 255,250,244 | 0.6 / 24 / 0.95 | 0.03 / 0.5 |
| Day | 20,20,26 | 100,100,108 | 3.0 | 255,246,232 / 0,0,0 | 1.0 / 1.0 | 0 | 0.28 / 0.25 / 0.3 / 0 | 199,199,204 / 106,112,125 | 0.45 / 0.35 / 236,236,240 | 0 / 0.04 / -0.06 / 255,252,246 | 0.5 / 24 / 0.97 | 0 / 0 |
| Golden | 30,24,24 | 124,104,92 | 2.4 | 255,200,140 / 0,0,0 | 0.8 / 0.8 | 0 | 0.31 / 0.22 / 1.0 / 0.8 | 230,190,150 / 150,100,90 | 0.5 / 0.45 / 255,210,170 | 0 / 0.05 / 0 / 255,236,214 | 0.8 / 32 / 0.94 | 0.08 / 0.7 |
| Dusk | 30,22,32 | 118,86,100 | 1.8 | 255,160,120 / 60,44,76 | 0.6 / 0.6 | 0.05 | 0.33 / 0.2 / 1.6 / 0.4 | 214,160,150 / 120,76,100 | 0.55 / 0.5 / 230,140,140 | 0 / 0.06 / -0.04 / 255,226,214 | 1.0 / 36 / 0.92 | 0.06 / 0.6 |
| **Night** | **44,48,78** | **96,108,160** | 1.2 | 170,190,255 / 30,34,60 | 0.45 / 0.7 | **0.35** | 0.3 / 0.15 / 1.0 / 0 | 100,112,170 / 40,44,84 | 0.5 / 0.35 / 150,166,214 | 0.02 / **-0.02** / -0.06 / 220,226,255 | 1.1 / 40 / 0.9 | 0 / 0 |
| Witching | 38,40,70 | 84,92,144 | 1.0 | 160,176,240 / 30,34,60 | 0.4 / 0.7 | 0.3 | 0.34 / 0.12 / 1.3 / 0 | 90,100,160 / 34,38,76 | 0.6 / 0.4 / 130,146,200 | 0 / 0 / -0.1 / 214,220,255 | 1.1 / 40 / 0.9 | 0 / 0 |
| *2.16 night (before)* | 30,28,46 | 76,70,114 | 1.6 | none | none | 0.1 | 0.36 / 0.1 / 1.6 / 0 | 96,90,140 / 44,36,72 | none | -0.02 / 0.1 / -0.15 / 212,206,255 | 1.15 | none |

Lighting (Edit) stays `LightingStyle = Realistic` with `PrioritizeLightingQuality` on.

## 3. Moon modifiers
Applied on top of the blended key and scaled by **NightWeight**: 0 at 18.5 rising to 1 at 20, and 1 until 5 falling to
0 at 6.5. `Mul` multiplies, `Add` adds, `Set` lerps toward the value.

| Moon | Sky | Changes |
|---|---|---|
| Full | Night | Brightness ×1.25, Exposure +0.05. World.FullMoon still swells the moon to 18; the werewolf effects are unchanged. |
| Waxing, waning | Night | none (the base night) |
| New | `NightNew` | Brightness ×0.4; Ambient +6,6,12 (it stays readable without the moon); Saturation −0.12; tint 210,216,255; StarCount 5000 (World.MoonPhases owns the stars) |
| Crimson | `NightCrimson` | OutdoorAmbient 130,70,84; ColorShift_Top 255,120,120; Atmos Color 150,70,80 and Decay 70,20,30; Clouds 180,80,90; tint 255,214,214; Contrast +0.04 |
| Blue | `NightBlue` | OutdoorAmbient 90,130,190; ColorShift_Top 160,210,255; Atmos Color 90,130,180; tint 210,232,255 |

## 4. Event seasons
Workspace attribute `NHSeason` = `Winter` | `Spring` | `Summer` | `Nightmare` (nil = Autumn). Each event swaps the sky
sets in its schedule slots and layers partial key overrides. Fields it doesn't name keep autumn's values.

| Event | Skies | Key overrides |
|---|---|---|
| Winter | WinterDay / WinterDusk / WinterNight | Morning: OutdoorAmb 114,118,130, Clouds 232,236,244. Day: OutdoorAmb 120,126,140, Density 0.38, Atmos Color 220,226,236, Clouds 0.7 / 236,240,248, tint 244,248,255. Night: OutdoorAmb 110,124,170, Exposure 0.4 (snow brightens). Witching: OutdoorAmb 100,112,160, Exposure 0.35. |
| Spring | SpringDay / SpringDusk / SpringNight | Day: ColorShift_Top 255,250,220, Clouds 0.4 / 250,246,236, Saturation −0.02 (autumn +0.04). Dusk: ColorShift_Top 255,170,170, Clouds 240,170,190. Night: Density 0.36 (mist). |
| Summer | SummerDay / SummerDusk / SummerNight | Day: Brightness 3.2, Haze 0.2, Density 0.25, ColorShift_Top 255,240,210. Dusk: ColorShift_Top 255,180,110, Atmos Color 230,170,130. Night: Exposure 0.45. The evening keys and sky swaps move an hour later (night from 21:00). |
| Nightmare | NightmareDusk / NightmareNight | Dusk: ColorShift_Top 255,90,80, Atmos Color 200,90,80, Clouds 200,70,70, tint 255,214,206. Night: the crimson-moon modifier every night, with the `NightmareNight` sky. |

The Winter Morning and Witching rows, and Summer's Atmos Color at dusk, are small additions beyond the spec, so the
blends don't snap back to autumn between keys. Snow and rain particles belong to the ambience system and aren't part
of this pass.

## 5. Sky motion (new `Controllers.World.SkyMotion`)
| Layer | Behaviour | High | Medium | Low |
|---|---|---|---|---|
| Clouds | `workspace.GlobalWind` drives the drift (slow; 3× in a storm). Cover, Density and Color come from the key. | on | on | on, half wind |
| Wisp ring | Curved Beams with `NHWisp_A` / `NHWisp_B` (1024×256, tiling in U, white with alpha), hung between Attachments on a client-only anchor that follows the camera (CanCollide, CanQuery and CastShadow off, Transparency 1). The engine scrolls them (`TextureSpeed` 0.01-0.03, no per-frame script). `LightInfluence` 0; `Color` is the key's cloud colour; they fade in with NightWeight. | 3 beams | 1 beam | off |
| Storm flashes | Atmosphere Glare and Haze plus a grade-brightness pulse: 0.08-0.25 s, 2-3 flickers, at most 3 Hz, never white. Reduce Flashing gives one soft pulse. | on | on | on |
| Sky turn | `SkyboxOrientation.Y` +2° per in-game hour, wrapping at the sky swap | gated | gated | off |

- **The tier** comes from the game's own Effects Quality setting. It drops one step while the average frame time stays
  over 22 ms for 5 s. It never reads `UserGameSettings.SavedQualityLevel`, which is discouraged and planned for removal.
- **The sky turn** ships only if a Studio test shows no Atmosphere seam at QL21 and QL1. The Atmosphere ignores
  `SkyboxOrientation` (a bug reported in Aug 2026).

## 6. Upload list (owner)
Upload to group 15981569 from `art/group-upload-skies/`:
- **102 sky faces:** `NHSky<Set>_<Face>.png` for the 17 sets other than Day and Dusk (Dawn, Night, NightNew,
  NightCrimson, NightBlue, Storm, and the 11 event sets). The Day and Dusk files are byte-for-byte regenerations of the
  2026-11-13 uploads, so there's no need to re-upload them.
- **2 wisp textures:** `NHWisp_A.png` and `NHWisp_B.png`.

Night, NightBlue and Storm keep their file names but are new paintings. The 2.16 ids stay listed in the proposed
config as `Skies.Sets216`, so a rollback is a copy-paste.

## 7. Wiring plan (Studio, after the upload)
1. **Find the ids** in group 15981569 and fill `Skies.Sets.<Set>.<Face>` and `Motion.Wisps.Textures` in
   `tools/sky-2360/proposed/ReplicatedStorage.Config.DayCycle.luau`. Then rerun nothing: paste it over
   `ReplicatedStorage.Config.DayCycle` in NH Combat Test. It keeps every 2.16 field, so the current controller still
   runs on it (it just ignores the new fields) while step 2 is done.
2. **`Controllers.World.DayCycle`:**
   - **Write the new fields:** `ColorShift_Top/Bottom`, `EnvironmentDiffuseScale`, `EnvironmentSpecularScale`,
     `Terrain.Clouds` (Cover, Density, Color; create the Clouds if missing), Bloom Size and Threshold, and `SunRays`
     (create if missing; Intensity 0 outside dawn, golden hour and dusk).
   - **Season:** read `workspace:GetAttribute("NHSeason")`. Merge `Seasons[S].Looks[key]` over each key, use
     `Seasons[S].Keys` and `Schedule` when present, and map the schedule's set through `Seasons[S].Skies`.
   - **Moon:** pick `Moon[name]` from `workspace.NHMoonEventTonight` (`Crimson` / `Blue`), else the Lineage phase
     (`Full` / `New` / `Waxing` / `Waning`), else `Seasons[S].Moon`. Apply Mul, Add and Set at NightWeight. Its `Sky`
     replaces `Night` (Nightmare's own `NightmareNight` wins over the crimson modifier's sky).
   - **Colour adds:** Luau `Color3` can't be added, so add channel-wise and clamp.
   - **Preload:** replace the preload-everything loop with `Skies.Preload = "ShownAndNext"`. Preload the shown set
     and the next one in the schedule (plus the moon or season replacement for the coming night). Event sets load only
     while their event is on, and Storm only when `NHSky` asks for it. 19 sets × 6 faces at 1024 is too much to keep
     resident on phones.
   - **Dawn:** drop the turn handling (`Schedule` entries no longer carry a third value; keep reading it as 0).
3. **One grade:** World.FullMoon stops writing `NHMoonGrade` and World.MoonPhases stops writing `NHNewMoonGrade`.
   Their numbers now live in `Moon.Full` and `Moon.New`. They keep the moon texture, its size, the stars, the banners
   and the eyes.
4. **Cine `Looks`:** they keep their own grade during cuts. Retune `Night` to match the new night: tint 214,228,240
   stays, contrast 0.1 to 0.04.
5. **Night sight:** recheck its grade against the brighter base, so it still reads as a boost.
6. **`Controllers.World.SkyMotion`:** a new controller that reads `Config.DayCycle.Motion`. It stays out of the main
   menu and the seamless cuts, like DayCycle (hook `DayCycle.Suspend`).
7. **Test:**
   - Performance Simulator at Q1, Q4, Q10 and Q21, a phone RAM tier, and a console profile (players report much
     darker nights on PS5).
   - Check 23:00 and 02:00 on every moon, and 06:00, 12:00, 17:00 and 18:30.
   - Set each `NHSeason` once, and `NHSky = "Storm"`.
   - Check the school and the Wickfield hometown (4000, 0, 4000).
   - The sky-turn seam check at QL21 and QL1 before `Motion.SkyTurn.Enabled` goes on.
   - Watch client memory with every event off: only two sky sets should be resident.

## Studio results (2026-11-23)
- Installed: `Config.DayCycle` (the proposed config, ids filled), `World.DayCycle`, `World.FullMoon`, `World.MoonPhases`,
  `Config.Cine`, and the new `World.SkyMotion`. Mirror `tools/sky-2360/live/`; backup `ServerStorage.NH_Backup.Sky2360_pre_20261123`.
- `tools/sky-2360/checks/sky_live.lua` (Play, Client VM): PASS. `tools/sky-2360/harness/shot.sh <hour> [Attr=value]` holds the
  look at an hour with the preview attributes, for screenshots. Screenshots: `docs/img/sky-2360/studio/`.
- Moon order as built: the event moon, then the season's moon, then the phase (so Nightmare Nights is crimson every night).
- The wisps glow (LightEmission 1, Brightness 2.5): the textures are mostly clear and vanished unlit.
- Studio test: `NHSkyTierPreview` forces SkyMotion's tier (Studio's frame times drop it to Low).
- Still to test: the Performance Simulator tiers, a phone RAM tier, a console profile, 02:00 on every moon, Spring and Summer,
  Wickfield, client memory, the sky-turn seam check (SkyTurn stays off), and Night Sight against the brighter night.

## Files
| Path | What |
|---|---|
| `tools/vfx/make_skyboxes.py` | the painter: faces, previews, seam report (registers skies2360's sets) |
| `tools/vfx/skies2360.py` | the 17 new painters |
| `tools/vfx/make_wisps.py` | the wisp textures |
| `tools/sky-2360/presets.py` | the keys, moon modifiers and seasons (single source) |
| `tools/sky-2360/gen_config.py` | writes the proposed config from presets.py |
| `tools/sky-2360/proposed/ReplicatedStorage.Config.DayCycle.luau` | the proposed config, ids empty except Day and Dusk |
| `tools/sky-2360/contact_sheet.py`, `equirect.py`, `preview_scene.py`, `post.py` | the preview pipeline |
| `art/group-upload-skies/` | the faces and wisps to upload |
| `art/skies-preview/`, `docs/img/sky-2360/` | the previews |
