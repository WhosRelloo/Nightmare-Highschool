# NH painted skies (group upload)

The owner uploaded all 30 faces to group 15981569 on 2026-11-13.

| Set | Bk | Dn | Ft | Lf | Rt | Up |
|---|---|---|---|---|---|---|
| Day | 103651333736497 | 77333463665975 | 119988626923704 | 82325193338630 | 98736878816049 | 96123202776655 |
| Dusk | 130059050523371 | 109620867877755 | 134244672227710 | 92637844935076 | 123188875952160 | 104447967963998 |
| Night | 125002822187171 | 84581077978179 | 111974113063539 | 129398379328271 | 103371164387111 | 71407617919019 |
| NightBlue | 79114995657347 | 125521770406965 | 137444634128484 | 139377898630563 | 114576978634954 | 83837514923669 |
| Storm | 140004647918133 | 75870366649344 | 138974617955349 | 81795809687373 | 128479768841317 | 127658888445040 |

These ids are in `Config.DayCycle.Skies.Sets` in NH Combat Test.
Made with `python tools/vfx/make_skyboxes.py` (numpy + PIL, 1024 x 1024 a face). Rerun it to remake every face and
the review sheet. Concept 58 in `docs/Environment-Ambience-Concepts.md`.

**Review sheet:** `art/skies-preview/NHSkies_Preview.png`. It sits outside this folder, so a bulk upload doesn't pick
it up. For each sky it shows a 360° panorama and three perspective views at the cube's corners and zenith, all
re-projected from these PNGs. `art/skies-preview/seams.txt` measures every face edge.

## Files: 5 sets x 6 faces = 30 PNGs

| Set | Faces | Shown |
|---|---|---|
| `NHSkyDay_*` | Bk Dn Ft Lf Rt Up | 07:00 to 17:36 |
| `NHSkyDusk_*` | Bk Dn Ft Lf Rt Up | 17:36 to 19:36 (dusk); 05:42 to 07:00 (dawn, the same faces turned −133° by `SkyboxOrientation`) |
| `NHSkyNight_*` | Bk Dn Ft Lf Rt Up | 19:36 to 05:42 |
| `NHSkyNightBlue_*` | Bk Dn Ft Lf Rt Up | in place of Night on a blue-moon night |
| `NHSkyStorm_*` | Bk Dn Ft Lf Rt Up | when `workspace` attribute `NHSky = "Storm"` is set (no weather system yet) |

**What each sky looks like:**
- **Day:** a muted, cool gothic day. The zenith is blue-grey, the horizon is bone haze, and painted clouds are lit
  from the sun's side.
- **Dusk:** a candle-gold glow where the sun sets, crimson-mauve above it and a violet zenith. Opposite the sun is a
  pink belt over the cool earth shadow, and the streaky clouds are rimmed in gold.
- **Night:** an ink zenith with a faint ink-blue horizon and thin moonlit wisps. A faint, distant town silhouette runs
  round the horizon: spires, roofs, towers and a few candle-lit windows. The biggest cluster is in the east, where
  the moon rises.
- **NightBlue:** the night plus a faint aurora-like band in ink blue, cold teal and violet. It's on the +Z side, away
  from the moon's path.
- **Storm:** a low, heavy ceiling of rolling dark cloud, a thin cold break on one horizon, and rain curtains.

**What isn't painted:**
- **The moon:** Roblox's Sky draws it, using `Lineage.MoonTextures` set by `World.MoonPhases` and `World.FullMoon`.
- **The stars:** `Sky.StarCount`.

The upper sky stays dark and clean where the moon travels: it rises at +X, crosses the −Z side and sets at −X.

## Wiring the ids

Put each uploaded id into `ReplicatedStorage.Config.DayCycle` → `Skies.Sets.<Set>.<Face>` in NH Combat Test. The
face names match the file suffix: `NHSkyNight_Lf.png` goes in `Sets.Night.Lf`. Each id can be a number or
`"rbxassetid://..."`. A set with any face empty is skipped and the place's own sky stays, so sets can be filled one at
a time.

**Face orientation (measured in Studio):** Roblox shows `SkyboxLf` on the +X side and `SkyboxRt` on the −X side.
Keep the files paired with the property that has the same suffix, and they line up.
