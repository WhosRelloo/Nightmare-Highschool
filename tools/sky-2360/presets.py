"""Sky-2360 lighting presets: the one source of truth for the time-of-day keys, moon modifiers and event seasons.

Values are Roblox units (colours 0-255). Two scripts read this file:
  tools/sky-2360/gen_config.py      writes tools/sky-2360/proposed/ReplicatedStorage.Config.DayCycle.luau
  tools/sky-2360/preview_scene.py   (Blender) renders a preview of every variant into docs/img/sky-2360/
Spec: docs/superpowers/specs/2026-11-21-sky-2360-design.md, section 2-3. Table: docs/Sky-and-Lighting.md.

Look fields (every key has all of them):
  Ambient, OutdoorAmbient, Brightness, ColorShiftTop, ColorShiftBottom, EnvDiffuse, EnvSpecular, ExposureCompensation
  Density, Offset, Haze, Glare, AtmosphereColor, Decay                       (Atmosphere)
  CloudCover, CloudDensity, CloudColor                                         (workspace.Terrain.Clouds)
  GradeBrightness, Contrast, Saturation, Tint                                  (NHDayGrade ColorCorrection)
  Bloom, BloomSize, BloomThreshold                                             (Lighting.Bloom)
  SunRays, SunRaysSpread                                                       (Lighting.SunRays)
"""

NIGHT_BOTTOM = (30, 34, 60)
TWILIGHT_BOTTOM = (60, 44, 76)
NONE = (0, 0, 0)


def look(amb, out, bright, top, bottom, env, exp, atm, atm_col, cloud, grade, bloom, rays):
    return {
        "Ambient": amb, "OutdoorAmbient": out, "Brightness": bright,
        "ColorShiftTop": top, "ColorShiftBottom": bottom, "EnvDiffuse": env[0], "EnvSpecular": env[1],
        "ExposureCompensation": exp,
        "Density": atm[0], "Offset": atm[1], "Haze": atm[2], "Glare": atm[3],
        "AtmosphereColor": atm_col[0], "Decay": atm_col[1],
        "CloudCover": cloud[0], "CloudDensity": cloud[1], "CloudColor": cloud[2],
        "GradeBrightness": grade[0], "Contrast": grade[1], "Saturation": grade[2], "Tint": grade[3],
        "Bloom": bloom[0], "BloomSize": bloom[1], "BloomThreshold": bloom[2],
        "SunRays": rays[0], "SunRaysSpread": rays[1],
    }


# ------------------------------------------------------------------ autumn (permanent) keys
LOOKS = {
    "Dawn": look((34, 30, 40), (120, 104, 118), 2.0, (255, 206, 170), TWILIGHT_BOTTOM, (0.6, 0.6), 0.05,
                 (0.34, 0.20, 1.4, 0.6), ((230, 200, 196), (150, 120, 140)), (0.55, 0.45, (255, 214, 196)),
                 (0, 0.04, -0.04, (255, 236, 226)), (0.9, 32, 0.95), (0.06, 0.6)),
    "Morning": look((24, 24, 30), (110, 110, 116), 2.6, (255, 240, 220), NONE, (0.8, 0.8), 0.0,
                    (0.30, 0.25, 0.6, 0.3), ((210, 206, 200), (120, 124, 136)), (0.50, 0.40, (240, 236, 232)),
                    (0, 0.04, -0.04, (255, 250, 244)), (0.6, 24, 0.95), (0.03, 0.5)),
    "Day": look((20, 20, 26), (100, 100, 108), 3.0, (255, 246, 232), NONE, (1.0, 1.0), 0.0,
                (0.28, 0.25, 0.3, 0.0), ((199, 199, 204), (106, 112, 125)), (0.45, 0.35, (236, 236, 240)),
                (0, 0.04, -0.06, (255, 252, 246)), (0.5, 24, 0.97), (0.0, 0.0)),
    "Golden": look((30, 24, 24), (124, 104, 92), 2.4, (255, 200, 140), NONE, (0.8, 0.8), 0.0,
                   (0.31, 0.22, 1.0, 0.8), ((230, 190, 150), (150, 100, 90)), (0.50, 0.45, (255, 210, 170)),
                   (0, 0.05, 0.0, (255, 236, 214)), (0.8, 32, 0.94), (0.08, 0.7)),
    "Dusk": look((30, 22, 32), (118, 86, 100), 1.8, (255, 160, 120), TWILIGHT_BOTTOM, (0.6, 0.6), 0.05,
                 (0.33, 0.20, 1.6, 0.4), ((214, 160, 150), (120, 76, 100)), (0.55, 0.50, (230, 140, 140)),
                 (0, 0.06, -0.04, (255, 226, 214)), (1.0, 36, 0.92), (0.06, 0.6)),
    # the owner's night rule: ambient and exposure up, contrast down vs 2.16; darkness comes from lamps and windows
    "Night": look((44, 48, 78), (96, 108, 160), 1.2, (170, 190, 255), NIGHT_BOTTOM, (0.45, 0.7), 0.35,
                  (0.30, 0.15, 1.0, 0.0), ((100, 112, 170), (40, 44, 84)), (0.50, 0.35, (150, 166, 214)),
                  (0.02, -0.02, -0.06, (220, 226, 255)), (1.1, 40, 0.90), (0.0, 0.0)),
    "Witching": look((38, 40, 70), (84, 92, 144), 1.0, (160, 176, 240), NIGHT_BOTTOM, (0.4, 0.7), 0.30,
                     (0.34, 0.12, 1.3, 0.0), ((90, 100, 160), (34, 38, 76)), (0.60, 0.40, (130, 146, 200)),
                     (0, 0.0, -0.10, (214, 220, 255)), (1.1, 40, 0.90), (0.0, 0.0)),
}

# 2.16's night, for comparison renders only (not written to the config)
OLD_NIGHT = dict(LOOKS["Night"], Ambient=(30, 28, 46), OutdoorAmbient=(76, 70, 114), Brightness=1.6,
                 ColorShiftTop=(0, 0, 0), ColorShiftBottom=(0, 0, 0), EnvDiffuse=0.0, EnvSpecular=0.0,
                 ExposureCompensation=0.1, Density=0.36, Offset=0.1, Haze=1.6, AtmosphereColor=(96, 90, 140),
                 Decay=(44, 36, 72), CloudCover=0.0, GradeBrightness=-0.02, Contrast=0.1, Saturation=-0.15,
                 Tint=(212, 206, 255), Bloom=1.15)

# { hour, key }: sorted; the client blends neighbours with smoothstep, the first and last wrap at midnight
KEYS = [(0, "Night"), (1, "Witching"), (4, "Witching"), (5, "Night"), (6, "Dawn"), (7.5, "Morning"), (9.5, "Day"),
        (16, "Day"), (17, "Golden"), (18.5, "Dusk"), (20, "Night"), (24, "Night")]

# { from hour, sky set }: swaps sit where the haze is already up. Dawn has its own painting now (no turned dusk faces)
SCHEDULE = [(0, "Night"), (5.6, "Dawn"), (8.0, "Day"), (17.6, "Dusk"), (19.6, "Night")]

# "how much night it is": 0 at 18.5 rising to 1 at 20; 1 until 5 falling to 0 at 6.5. Moon modifiers scale by it.
NIGHT_WEIGHT = {"Rise": (18.5, 20.0), "Fall": (5.0, 6.5)}

# ------------------------------------------------------------------ moon modifiers (on top of the blended key)
# Mul multiplies, Add adds (colours channel-wise), Set lerps toward the value; all weighted by NIGHT_WEIGHT.
MOON = {
    "Full": {"Mul": {"Brightness": 1.25}, "Add": {"ExposureCompensation": 0.05}},
    "Waxing": {}, "Waning": {},
    "New": {"Sky": "NightNew", "Mul": {"Brightness": 0.4},
            "Add": {"Ambient": (6, 6, 12), "Saturation": -0.12}, "Set": {"Tint": (210, 216, 255)}, "StarCount": 5000},
    "Crimson": {"Sky": "NightCrimson",
                "Set": {"OutdoorAmbient": (130, 70, 84), "ColorShiftTop": (255, 120, 120), "AtmosphereColor": (150, 70, 80),
                        "Decay": (70, 20, 30), "CloudColor": (180, 80, 90), "Tint": (255, 214, 214)},
                "Add": {"Contrast": 0.04}},
    "Blue": {"Sky": "NightBlue",
             "Set": {"OutdoorAmbient": (90, 130, 190), "ColorShiftTop": (160, 210, 255), "AtmosphereColor": (90, 130, 180),
                     "Tint": (210, 232, 255)}},
}

# ------------------------------------------------------------------ event seasons (workspace attribute NHSeason)
# Skies: which set replaces Day / Dusk / Night. Looks: partial overrides by key name (fields not named keep autumn's).
SEASONS = {
    "Winter": {
        "Skies": {"Day": "WinterDay", "Dusk": "WinterDusk", "Night": "WinterNight"},
        "Looks": {
            "Morning": {"OutdoorAmbient": (114, 118, 130), "CloudColor": (232, 236, 244)},
            "Day": {"OutdoorAmbient": (120, 126, 140), "Density": 0.38, "AtmosphereColor": (220, 226, 236),
                    "CloudCover": 0.7, "CloudColor": (236, 240, 248), "Tint": (244, 248, 255)},
            "Night": {"OutdoorAmbient": (110, 124, 170), "ExposureCompensation": 0.4},
            "Witching": {"OutdoorAmbient": (100, 112, 160), "ExposureCompensation": 0.35},
        },
    },
    "Spring": {
        "Skies": {"Day": "SpringDay", "Dusk": "SpringDusk", "Night": "SpringNight"},
        "Looks": {
            "Day": {"ColorShiftTop": (255, 250, 220), "CloudCover": 0.4, "CloudColor": (250, 246, 236), "Saturation": -0.02},
            "Dusk": {"ColorShiftTop": (255, 170, 170), "CloudColor": (240, 170, 190)},
            "Night": {"Density": 0.36},
        },
    },
    "Summer": {
        "Skies": {"Day": "SummerDay", "Dusk": "SummerDusk", "Night": "SummerNight"},
        "Looks": {
            "Day": {"Brightness": 3.2, "Haze": 0.2, "Density": 0.25, "ColorShiftTop": (255, 240, 210)},
            "Dusk": {"ColorShiftTop": (255, 180, 110), "AtmosphereColor": (230, 170, 130)},
            "Night": {"ExposureCompensation": 0.45},
        },
        # the short summer night: the evening keys move an hour later
        "Keys": [(0, "Night"), (1, "Witching"), (4, "Witching"), (5, "Night"), (6, "Dawn"), (7.5, "Morning"),
                 (9.5, "Day"), (17, "Day"), (18, "Golden"), (19.5, "Dusk"), (21, "Night"), (24, "Night")],
        "Schedule": [(0, "Night"), (5.6, "Dawn"), (8.0, "Day"), (18.6, "Dusk"), (20.6, "Night")],
    },
    "Nightmare": {
        "Skies": {"Dusk": "NightmareDusk", "Night": "NightmareNight"},
        "Looks": {
            "Dusk": {"ColorShiftTop": (255, 90, 80), "AtmosphereColor": (200, 90, 80), "CloudColor": (200, 70, 70),
                     "Tint": (255, 214, 206)},
        },
        "Moon": "Crimson",   # the crimson-moon modifier every night (its sky is replaced by NightmareNight)
    },
}

SETS = ["Day", "Dusk", "Dawn", "Night", "NightNew", "NightCrimson", "NightBlue", "Storm",
        "WinterDay", "WinterDusk", "WinterNight", "SpringDay", "SpringDusk", "SpringNight",
        "SummerDay", "SummerDusk", "SummerNight", "NightmareDusk", "NightmareNight"]


def resolve(key, season=None, moon=None):
    """The full look for one key, with a season's overrides and a moon modifier at full night weight (for previews)."""
    out = dict(LOOKS[key])
    if season:
        out.update(SEASONS[season]["Looks"].get(key, {}))
        moon = moon or (SEASONS[season].get("Moon") if key in ("Night", "Witching") else None)
    if moon and key in ("Night", "Witching"):
        m = MOON[moon]
        for k, v in m.get("Mul", {}).items():
            out[k] = out[k] * v
        for k, v in m.get("Add", {}).items():
            out[k] = tuple(min(255, a + b) for a, b in zip(out[k], v)) if isinstance(v, tuple) else out[k] + v
        out.update(m.get("Set", {}))
    return out
