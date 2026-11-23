# Lighting research (2026-11-23): what the best Roblox lighting does, and what it means for us

The owner asked for a full pass over the Roblox Developer Forum and the best lighting videos, aimed at sunlight and moonlight,
optimized and highest quality. This sets what we learned against the live 2.39 sky pass (`docs/Sky-and-Lighting.md`).

## Sources
**Developer Forum** (read through the forum's JSON, first posts and the highest-scored replies):
- [Let There Be (Unified) Light! Unified Lighting is Fully Live](https://devforum.roblox.com/t/let-there-be-unified-light-unified-lighting-is-fully-live/3401512) (Roblox, 2025; 112k views)
- [Increasing the Minimum Draw Distance to 500 Studs and Other Auto-Quality Level Improvements](https://devforum.roblox.com/t/4977292) (Roblox, 2026-11-05)
- [Test Graphics and Memory on Lower-End Devices With the Performance Simulator](https://devforum.roblox.com/t/4979313) (Roblox, 2026-11-06)
- [Low quality lighting being forced on Android](https://devforum.roblox.com/t/4888683) (2026-09)
- [Smoother Skybox, Atmosphere and Light transitioning](https://devforum.roblox.com/t/4368559) (feature request, 2026-02)
- [Tips on realistic lighting](https://devforum.roblox.com/t/tips-on-realistic-lighting/1261456) (50k views), [Hyper realistic Lighting Settings?](https://devforum.roblox.com/t/hyper-realistic-lighting-settings/915802) (39k),
  [The Complete Guide to Lighting in Roblox Studio](https://devforum.roblox.com/t/the-complete-guide-to-lighting-in-roblox-studio/1876371) (39k), [Guide to Lighting](https://devforum.roblox.com/t/guide-to-lighting/2764787),
  [Improve Lighting (STEP BY STEP)](https://devforum.roblox.com/t/improve-lighting-step-by-step/1387033), [Tips & Tricks for improving your game using Lighting](https://devforum.roblox.com/t/tips-tricks-for-improving-your-game-using-lighting/1062421),
  [Persistent 3D Sun Shafts / Volumetric Light System](https://devforum.roblox.com/t/4906553), [Lighting is now what holds back realism](https://devforum.roblox.com/t/4874817)
- Official docs: [Atmosphere](https://create.roblox.com/docs/environment/atmosphere), [Enhance outdoor environments](https://create.roblox.com/docs/tutorials/use-case-tutorials/lighting/enhance-outdoor-environments)

**Videos** (watched with `/watch-video`: frames read for the property panels, captions where they exist):
- Narrakin, [Realistic Night Lighting Settings](https://www.youtube.com/watch?v=MkjlAEpbEDg) (183k views; no captions, frames only)
- DatBoiEle, [THE Ultimate Lighting Tutorial [ADVANCED]](https://www.youtube.com/watch?v=aq0Fi0R2FAY) (133k; 21 min)
- Develuper, [Make Your Roblox Game Look 10x Better With Lighting](https://www.youtube.com/watch?v=vkEXLmRAQgs) (267k)
- RingWorld Studio, [How I Do Lighting & Atmosphere in Roblox](https://www.youtube.com/watch?v=UlvSrWHESwA)
- BlackDragon Studios, [How to get Moon Rays in Roblox Studio](https://www.youtube.com/watch?v=qRmQ-IU2lH4)

## What the best lighting has in common
1. **Decide the mood first**, then pick the sky, then tune (RingWorld, DatBoiEle).
2. **Warm light, cool shadows.** ColorShift_Top carries the light colour (the side facing the sun or moon); Ambient and
   OutdoorAmbient carry the shadow colour. Day: warm top, cool shadows. Night: silver top, blue shadows (DatBoiEle, the 39k
   "Hyper realistic" thread).
3. **Contrast comes from the key light, not the grade.** Lower EnvironmentDiffuseScale for a stronger light/shadow ratio
   (DatBoiEle); keep EnvironmentSpecularScale near 1 so metal and wet surfaces read (official tutorial).
4. **Moonlight is a real directional light.** The night video keeps Brightness high (3.43) with Ambient 0 and Exposure
   -0.39, so the moon still casts shadows; the darkness comes from contrast, and a warm lantern (PointLight 8.58,
   255,193,92, range 60, shadows on) is the focal point. RingWorld does the same in cold blue with one lamp.
5. **"Moon rays":** SunRays only follow the sun. The trick (BlackDragon) is a night skybox with the sun still up and the
   sun texture swapped for a moon, so the sun's directional light and SunRays become moonlight and moon shafts.
6. **Bloom soft and wide** for a cohesive image: threshold very low (~0.03), size high, intensity low (DatBoiEle); or a
   strong small bloom so things don't smudge. Avoid Blur; DepthOfField only lightly.
7. **Atmosphere:** Density 0.3-0.4 by day (Develuper; official tutorial 0.272), Offset 0 or low, a little light Glare and
   darker Haze. Clouds soften shadows; ShadowSoftness ~0.1-0.2.
8. **Local lights:** two PointLights per lamp, a bright near one with shadows and a wide far one without (RingWorld) - it
   also halves the shadow cost. Glass windows: CastShadow off and a tint so light spills in (DatBoiEle).
9. **Sound is half the atmosphere** (RingWorld): ambience loops per zone and weather.

## Platform facts that set the limits (2025-2026)
- **Unified Lighting:** `Technology` is replaced by `LightingStyle` (Realistic / Soft) and `PrioritizeLightingQuality`.
  Prioritized keeps lighting quality and trades draw distance first. Our place: Realistic + Prioritized (correct for a
  lighting-led game).
- **Auto quality (2026-11-05):** draw distance at the lowest level is now 500 studs; beams no longer drop segments at
  low levels (good for our wisps); **don't** drive effects from `UserGameSettings.SavedQualityLevel` (we don't: SkyMotion
  uses the game's own Effects Quality setting).
- **Performance Simulator (2026-11-06):** test graphics and memory on low-end devices in Studio. This is how the open
  "Q1/Q4/Q10/Q21 and a phone RAM tier" rows of the sky pass get run.
- **Android:** a bug forced low-quality lighting on some phones in Sept 2026 (fixed); Realistic lighting is heavy on
  mid-range phones at high graphics levels. Keep shadowed local lights few.
- **No skybox crossfade** exists yet (open feature request), which is why our sky swaps under a haze swell.

## Set against our 2.39 values
| Where | 2.39 | What the research says | Recommendation |
|---|---|---|---|
| Night key | Brightness 1.2, OutdoorAmbient 96,108,160, Exposure +0.35, EnvDiffuse 0.45 | the moon should be the key light; darkness from contrast | **Moonlit night:** Brightness 2.6, Ambient 26,30,52, OutdoorAmbient 62,72,118, Exposure 0.15, EnvDiffuse 0.3, ColorShift_Top 190,205,255. A/B in Studio: [night-ab.jpg](img/sky-2360/studio/night-ab.jpg) - the ground reads silver and moon shadows show, faces stay readable |
| Day keys | warm ColorShift_Top, slightly cool ambient, Bloom thresholds 0.92-0.97 | warm light / cool shadows; soft wide bloom | keep; test the soft-bloom variant (threshold 0.3, size 48, intensity 0.25) on Golden and Dusk |
| Moon shafts | SunRays 0 at night | moon rays need the sun-as-moon trick | **Optional R2:** at night the client keeps a low sun behind the night sky with `SunTextureId` = the moon art, so SunRays and shadows come from the moon. Needs a Studio test with World.FullMoon (which swells MoonAngularSize) |
| Lamps (map) | single PointLights | two lights per lamp, shadows only on the near one | a map pass (builder) |
| Crimson / Nightmare | the scene washes red | contrast and a focal light keep players readable | lower crimson OutdoorAmbient and tint by ~40 % (owner to confirm) |
| Sound | per area | ambience loops by weather/time | storm and night ambience through SkyMotion (later) |

**Not applied yet.** The moonlit night values were tried at runtime only (not saved). Applying them is a one-line change per
key in `tools/sky-2360/presets.py`, then `gen_config.py`, install, and a re-run of `sky_live` and the screenshot tour.
