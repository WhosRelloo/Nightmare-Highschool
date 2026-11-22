# NH painted skies (group upload)

**2.36 (sky-2360): 19 sets x 6 faces = 114 PNGs at 1024, plus 2 wisp textures.** Design, presets and wiring:
`docs/Sky-and-Lighting.md`.

## To upload (owner)
Upload to group 15981569:
- **102 faces:** every `NHSky<Set>_<Face>.png` **except** `NHSkyDay_*` and `NHSkyDusk_*`. Those 12 files are
  byte-identical to the 2026-11-13 uploads, and their ids below stay live.
- **2 wisps:** `NHWisp_A.png` and `NHWisp_B.png` (1024 x 256, white with alpha, for the SkyMotion Beams).

`NHSkyNight_*`, `NHSkyNightBlue_*` and `NHSkyStorm_*` keep their 2.16 names but are **new paintings**. Upload them
again; their old ids are listed below for rollback.

The ids go into `tools/sky-2360/proposed/ReplicatedStorage.Config.DayCycle.luau`: `Skies.Sets.<Set>.<Face>`, and
`Motion.Wisps.Textures.A/B`. The face names match the file suffix, so `NHSkyNight_Lf.png` goes in `Sets.Night.Lf`.

## Sets
| Set | Shown |
|---|---|
| `Day` | 08:00 to 17:36 (unchanged) |
| `Dusk` | 17:36 to 19:36 (unchanged) |
| `Dawn` | 05:36 to 08:00 (new; replaces the turned dusk faces) |
| `Night` | 19:36 to 05:36 on full, waxing and waning moons (repainted, brighter B style) |
| `NightNew` / `NightCrimson` / `NightBlue` | new-moon, crimson-moon and blue-moon nights |
| `Storm` | workspace `NHSky = "Storm"` (restyled) |
| `WinterDay` `WinterDusk` `WinterNight` | the Winter event |
| `SpringDay` `SpringDusk` `SpringNight` | the Spring event |
| `SummerDay` `SummerDusk` `SummerNight` | the Summer event |
| `NightmareDusk` `NightmareNight` | Nightmare Nights |

The moon and the stars aren't painted (Roblox draws them), and the upper sky stays clean along the moon's path.

## Live ids (2026-11-13 uploads)
| Set | Bk | Dn | Ft | Lf | Rt | Up |
|---|---|---|---|---|---|---|
| Day | 103651333736497 | 77333463665975 | 119988626923704 | 82325193338630 | 98736878816049 | 96123202776655 |
| Dusk | 130059050523371 | 109620867877755 | 134244672227710 | 92637844935076 | 123188875952160 | 104447967963998 |
| Night (2.16 painting) | 125002822187171 | 84581077978179 | 111974113063539 | 129398379328271 | 103371164387111 | 71407617919019 |
| NightBlue (2.16 painting) | 79114995657347 | 125521770406965 | 137444634128484 | 139377898630563 | 114576978634954 | 83837514923669 |
| Storm (2.16 painting) | 140004647918133 | 75870366649344 | 138974617955349 | 81795809687373 | 128479768841317 | 127658888445040 |

## Remaking them
`python tools/vfx/make_skyboxes.py` remakes every face (numpy + PIL; about 15 minutes with `NH_SKY_WORKERS=10`) and
writes the previews to `art/skies-preview/`: one `NHSky<Set>_preview.png` per set (a 360° panorama, two cube corners
and the zenith, all re-projected from these PNGs) and `seams.txt` (every face edge measured). The large combined
`NHSkies_Preview.png` isn't committed. `python tools/sky-2360/contact_sheet.py` builds the compact
`NHSkies_Sheet.jpg`, and `python tools/vfx/make_wisps.py` remakes the wisps. Both preview folders sit outside this
folder, so a bulk upload doesn't pick them up.

**Face orientation (measured in Studio):** Roblox shows `SkyboxLf` on the +X side and `SkyboxRt` on the −X side. Keep
each file paired with the property that has the same suffix, and they line up.
