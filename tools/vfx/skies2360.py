"""The 2.36 sky sets (sky-2360 spec): new painters built on make_skyboxes' helpers.

Imported by tools/vfx/make_skyboxes.py, which registers SETS into its SKIES table. Each function takes D, an [...,3] array of
Roblox sky directions (X right, Y up, -Z forward), and returns linear-ish RGB 0..1 like the existing painters.

The moon's path (rises at +X, crosses the -Z side up to ~67 degrees, sets at -X) stays clean: painted cloud banks on
night skies sit low on the -Z side and only climb higher on the +Z side (Roblox draws the moon over the sky, so clouds
painted across its path would look pasted behind it; the moving wisp Beams cross the moon instead).
"""
import numpy as np

import make_skyboxes as M

C, mix, ss, ramp, clouds, put_land, finish, geometry, fbm3 = (
    M.C, M.mix, M.ss, M.ramp, M.clouds, M.put_land, M.finish, M.geometry, M.fbm3)
GOLD, CRIMSON, INKBLUE = M.GOLD, M.CRIMSON, M.INKBLUE

SUNRISE = np.array([0.92, -0.04, -0.40], np.float32)
SUNRISE /= np.linalg.norm(SUNRISE)
SUNSET = M.SUNSET.astype(np.float32)


def moon_clear(x, z, el, low=30.0, high=58.0):
    """Cloud height limit: low on the moon's (-Z) side, higher on the +Z side."""
    back = ss(-0.2, 0.6, z / np.maximum(np.sqrt(x * x + z * z), 1e-4))  # 1 toward +Z
    top = low + (high - low) * back
    return ss(top, top - 16.0, el)


# ------------------------------------------------------------------------------------------------ dawn


def warm_sky(D, S, base_stops, warm_stops, sun_rgb, glow, horizon_lo, horizon_hi, cloud, land, win_amt, seed,
             cover=0.4, stretch=3.0, below=((-90, (16, 16, 22)), (-14, (40, 38, 50)))):
    """A low sun sky: base gradient, warm side toward S, a sun glow, rim-lit cloud deck, land."""
    x, y, z, el, az = geometry(D)
    cs = np.clip(D @ S, -1, 1)
    toward = (cs + 1) / 2
    col = mix(ramp(el, base_stops), ramp(el, warm_stops), np.clip(toward ** 2.4 * 1.1, 0, 1) * ss(65, 0, el))
    col = col + C(sun_rgb)[None, None, :] * ((np.maximum(cs, 0) ** 14) * glow * ss(22, -1, el))[..., None]
    horizon = mix(C(horizon_lo), C(horizon_hi), toward ** 3)
    a, lit, _ = clouds(D, seed, 1.25, cover, 0.2, stretch=stretch, warp=0.5, light=(S[0], S[2]))
    shadow, rim_lo, rim_hi = cloud
    body = mix(C(shadow), mix(C(rim_lo), C(rim_hi), toward ** 1.5), lit ** 1.5 * (0.3 + 0.7 * toward))
    col = mix(col, body, a * ss(-0.5, 5, el) * ss(72, 22, el) * (0.45 + 0.55 * toward) * 0.9)
    col = put_land(col, el, az, horizon, C(land), 0.2, 0.42, 0.55, win_rgb=GOLD, win_amt=win_amt, below=ramp(el, list(below)))
    return col


def sky_dawn(D):
    col = warm_sky(
        D, SUNRISE,
        [(-90, (20, 20, 28)), (-4, (62, 60, 78)), (0, (150, 140, 160)), (6, (140, 136, 166)), (20, (110, 116, 160)),
         (50, (78, 90, 140)), (90, (60, 72, 124))],
        [(-90, (40, 30, 32)), (-3, (150, 120, 110)), (0, (250, 222, 170)), (4, (244, 196, 160)), (12, (214, 150, 158)),
         (26, (150, 120, 160)), (90, (70, 80, 130))],
        (255, 236, 190), 0.5, (150, 140, 160), (250, 222, 170),
        ((96, 92, 124), (210, 150, 170), (255, 220, 190)), (70, 66, 86), 0.12, 23)
    return finish(col, D, 8, 0.025)


# ------------------------------------------------------------------------------------------------ nights


def night_sky(D, zen, mid, hor, glow, wisp_lo, wisp_hi, cover=0.5, amount=0.85, seed=51, land=(16, 16, 28),
              win_amt=0.65, below_hi=(18, 18, 30)):
    """The B-style readable night: a lit horizon band, moonlit cloud banks kept off the moon's path."""
    x, y, z, el, az = geometry(D)
    col = ramp(el, [(-90, (8, 8, 12)), (-5, below_hi), (0, hor), (3, hor), (12, mid), (40, zen), (90, zen)])
    # the town's glow over its roofs, warmest over the east cluster
    tg = np.exp(-((az - 88.0 + 180) % 360 - 180) ** 2 / (2 * 26.0 ** 2)) * np.exp(-np.maximum(el, 0) / 5.0)
    col = col + C(glow)[None, None, :] * (tg * 0.5)[..., None]
    a, lit, _ = clouds(D, seed, 1.4, cover, 0.22, stretch=2.6, warp=0.6, light=(0.6, -0.8))
    a2, lit2, _ = clouds(D, seed + 7, 3.0, cover * 0.7, 0.25, stretch=4.0, warp=0.4, light=(0.6, -0.8), lift=0.3)
    keep = moon_clear(x, z, el)
    col = mix(col, mix(C(wisp_lo), C(wisp_hi), lit ** 1.7), a * ss(-0.5, 4.0, el) * keep * amount)
    col = mix(col, mix(C(wisp_lo), C(wisp_hi), lit2 ** 2), a2 * ss(3, 14, el) * keep * amount * 0.45)
    col = put_land(col, el, az, C(hor), C(land), 0.3, 0.5, 0.66, win_rgb=GOLD, win_amt=win_amt,
                   below=ramp(el, [(-90, (7, 7, 11)), (-14, below_hi)]))
    return col


def sky_night(D):
    return finish(night_sky(D, (22, 30, 70), (40, 56, 110), (90, 110, 170), (70, 60, 70), (36, 44, 90), (176, 196, 236)), D, 5, 0.03)


def sky_night_new(D):
    """New moon: the deepest sky, fewer and dimmer banks; still a clear lit horizon so the skyline reads."""
    col = night_sky(D, (12, 15, 38), (24, 32, 70), (64, 78, 128), (60, 50, 60), (24, 28, 56), (96, 110, 160),
                    cover=0.38, amount=0.7, seed=53, land=(10, 10, 20))
    return finish(col, D, 15, 0.03)


def sky_night_crimson(D):
    col = night_sky(D, (30, 12, 26), (60, 20, 40), (130, 50, 62), (90, 40, 40), (52, 16, 26), (230, 96, 96),
                    cover=0.55, amount=0.9, seed=57, land=(20, 8, 14), win_amt=0.5, below_hi=(22, 10, 16))
    x, y, z, el, az = geometry(D)
    # a faint red corona on the horizon toward the rising moon
    halo = np.exp(-(((az - 90.0 + 180) % 360 - 180) / 50.0) ** 2) * np.exp(-np.maximum(el, 0) / 9.0) * ss(-3.0, 0.5, el)
    col = col + C(CRIMSON)[None, None, :] * (halo * 0.22)[..., None]
    return finish(col, D, 16, 0.03)


def aurora(col, D, strength=0.36):
    x, y, z, el, az = geometry(D)
    ar = np.radians(az)
    circ = np.stack([np.sin(ar) * 2.2, np.cos(ar) * 2.2, np.zeros_like(ar)], -1)
    wander = fbm3(circ + 3.3, 3, 61)
    low = 15.0 + 6.0 * np.sin(ar + 1.2) + (wander - 0.5) * 16.0
    t = (el - low) / 22.0
    curtain = ss(-0.04, 0.05, t) * np.exp(-np.maximum(t, 0) * 2.6) * (t < 1.6)
    rays = fbm3(np.stack([np.sin(ar) * 46, np.cos(ar) * 46, el * 0.05], -1), 4, 71)
    rays = 0.35 + 0.95 * ss(0.35, 0.75, rays)
    side = ss(-0.15, 0.55, z / np.maximum(np.sqrt(x * x + z * z), 1e-4))
    breaks = ss(0.3, 0.6, fbm3(circ * 0.8 + 7.7, 3, 81))
    k = curtain * rays * side * breaks * ss(-1, 3, el)
    hue = np.clip(t * 1.5, 0, 1)
    acol = mix(C((96, 196, 210)), C(INKBLUE), ss(0.0, 0.45, hue))
    acol = mix(acol, C((126, 96, 206)), ss(0.45, 1.0, hue))
    return col + acol * (k * strength)[..., None]


def sky_night_blue(D):
    col = night_sky(D, (16, 30, 72), (30, 60, 116), (84, 130, 180), (50, 60, 80), (28, 50, 96), (170, 214, 240),
                    cover=0.42, amount=0.8, seed=59)
    return finish(aurora(col, D, 0.42), D, 6, 0.03)


def sky_storm(D):
    """The storm, lifted toward the new nights' blue so it sits between them; heavier rain shafts."""
    col = M.sky_storm(D)
    col = col * np.array([0.96, 1.0, 1.1], np.float32) + np.array([0.0, 0.01, 0.03], np.float32)
    return np.clip(col, 0, 1)


# ------------------------------------------------------------------------------------------------ day skies (events)


def day_sky(D, stops, cloud_lo, cloud_hi, cover, horizon, land, land_mix, below, seed, scale=1.25, soft=0.2,
            stretch=1.6, second=0.32, haze=None):
    x, y, z, el, az = geometry(D)
    col = ramp(el, stops)
    col = col + (np.maximum(-z, 0) ** 2 * 0.05 * ss(-2, 30, el))[..., None]
    a, lit, _ = clouds(D, seed, scale, cover, soft, stretch=stretch, light=(0.0, -1.0))
    a2, lit2, _ = clouds(D, seed + 20, 3.2, second, 0.25, stretch=3.0, warp=0.4, light=(0.0, -1.0), lift=0.3)
    body = mix(C(cloud_lo), C(cloud_hi), lit ** 1.3)
    body = mix(body, C(horizon), 0.25 * (1 - ss(0, 12, el)))
    col = mix(col, body, a * ss(-0.5, 7.0, el) * 0.92)
    col = mix(col, mix(C(cloud_lo), C(cloud_hi), lit2), a2 * ss(4, 20, el) * 0.45)
    if haze is not None:
        col = mix(col, C(haze), np.exp(-np.maximum(el, 0) / 7.0) * 0.5)
    col = put_land(col, el, az, C(horizon), C(land), *land_mix, below=ramp(el, below))
    return col


def sky_winter_day(D):
    # a snow-light overcast, kept below the autumn Day's brightness so snow on the ground stays the brightest thing
    col = day_sky(D, [(-90, (64, 66, 74)), (-6, (132, 136, 146)), (0, (198, 202, 210)), (14, (164, 172, 190)),
                      (45, (124, 138, 164)), (90, (102, 118, 150))],
                  (118, 124, 144), (218, 222, 232), 0.52, (198, 202, 210), (184, 188, 200), (0.12, 0.25, 0.25),
                  [(-90, (80, 84, 94)), (-14, (148, 152, 162)), (0, (190, 194, 202))], 111, scale=0.9, soft=0.3)
    return finish(col, D, 21, 0.015)


def sky_spring_day(D):
    col = day_sky(D, [(-90, (58, 66, 60)), (-6, (130, 146, 136)), (0, (222, 226, 212)), (14, (176, 204, 220)),
                      (45, (118, 160, 206)), (90, (92, 136, 192))],
                  (150, 164, 186), (252, 250, 240), 0.42, (222, 226, 212), (120, 150, 112), (0.18, 0.36, 0.3),
                  [(-90, (50, 62, 50)), (-14, (96, 118, 94)), (0, (150, 166, 140))], 113, scale=1.1, soft=0.16, stretch=1.3,
                  haze=(230, 232, 214))
    return finish(col, D, 22, 0.02)


def sky_summer_day(D):
    col = day_sky(D, [(-90, (60, 64, 70)), (-6, (140, 144, 146)), (0, (236, 226, 204)), (10, (170, 196, 224)),
                      (40, (90, 140, 210)), (90, (60, 110, 196))],
                  (160, 170, 196), (255, 252, 244), 0.36, (236, 226, 204), (140, 150, 110), (0.2, 0.4, 0.35),
                  [(-90, (52, 60, 46)), (-14, (110, 120, 90)), (0, (170, 170, 140))], 117, scale=0.9, soft=0.12, stretch=1.1,
                  second=0.2, haze=(246, 236, 210))
    return finish(col, D, 23, 0.02)


# ------------------------------------------------------------------------------------------------ dusks (events)


def dusk_sky(D, base, warm, glow, hl, hh, cloud, land, win_amt, seed, cover=0.46):
    col = warm_sky(D, SUNSET, base, warm, glow, 0.55, hl, hh, cloud, land, win_amt, seed, cover=cover, stretch=4.0,
                   below=((-90, (10, 8, 14)), (-14, (28, 20, 30))))
    return col


def sky_winter_dusk(D):
    col = dusk_sky(D, [(-90, (16, 16, 24)), (-4, (60, 60, 84)), (0, (170, 160, 190)), (8, (140, 136, 180)),
                       (24, (96, 100, 156)), (90, (52, 60, 110))],
                   [(-3, (160, 130, 140)), (0, (255, 214, 190)), (4, (240, 180, 186)), (12, (196, 150, 190)),
                    (28, (130, 120, 176)), (90, (60, 64, 120))],
                   (255, 236, 210), (170, 160, 190), (255, 214, 190), ((90, 90, 130), (200, 160, 190), (255, 224, 210)),
                   (90, 90, 120), 0.3, 121, cover=0.55)
    return finish(col, D, 24, 0.02)


def sky_spring_dusk(D):
    col = dusk_sky(D, [(-90, (16, 14, 22)), (-4, (56, 46, 70)), (0, (150, 100, 130)), (8, (130, 96, 150)),
                       (24, (90, 84, 150)), (90, (48, 54, 112))],
                   [(-3, (170, 110, 100)), (0, (255, 206, 150)), (4, (252, 170, 160)), (12, (232, 130, 170)),
                    (28, (160, 100, 170)), (90, (56, 56, 120))],
                   (255, 220, 170), (150, 100, 130), (255, 206, 150), ((80, 60, 110), (236, 140, 180), (255, 214, 170)),
                   (50, 36, 56), 0.3, 123)
    return finish(col, D, 25, 0.025)


def sky_summer_dusk(D):
    col = dusk_sky(D, [(-90, (16, 12, 14)), (-4, (60, 40, 40)), (0, (170, 100, 70)), (8, (150, 90, 90)),
                       (24, (90, 66, 110)), (90, (40, 40, 90))],
                   [(-3, (180, 100, 50)), (0, (255, 206, 120)), (4, (255, 170, 90)), (12, (236, 120, 80)),
                    (28, (170, 80, 90)), (90, (50, 44, 96))],
                   (255, 220, 150), (170, 100, 70), (255, 206, 120), ((70, 46, 60), (240, 140, 90), (255, 214, 140)),
                   (54, 30, 30), 0.3, 125, cover=0.4)
    return finish(col, D, 26, 0.025)


def sky_nightmare_dusk(D):
    col = dusk_sky(D, [(-90, (12, 6, 8)), (-4, (50, 18, 22)), (0, (150, 50, 50)), (8, (120, 40, 54)),
                       (24, (70, 26, 50)), (90, (30, 14, 34))],
                   [(-3, (160, 50, 30)), (0, (255, 150, 90)), (4, (240, 90, 60)), (12, (200, 40, 50)),
                    (28, (120, 24, 44)), (90, (36, 14, 34))],
                   (255, 180, 110), (150, 50, 50), (255, 150, 90), ((50, 14, 24), (210, 50, 50), (255, 160, 90)),
                   (30, 10, 14), 0.35, 127, cover=0.55)
    return finish(col, D, 27, 0.03)


# ------------------------------------------------------------------------------------------------ nights (events)


def sky_winter_night(D):
    """Snow-bright: the land below the horizon is pale, the sky clear and cold."""
    col = night_sky(D, (18, 26, 58), (36, 52, 100), (98, 116, 170), (60, 56, 70), (40, 52, 96), (190, 206, 240),
                    cover=0.34, amount=0.7, seed=131, land=(44, 50, 74), win_amt=0.6, below_hi=(46, 52, 74))
    return finish(col, D, 31, 0.02)


def sky_spring_night(D):
    col = night_sky(D, (20, 30, 62), (40, 58, 104), (96, 116, 160), (70, 64, 70), (40, 50, 86), (176, 196, 226),
                    cover=0.45, amount=0.8, seed=133)
    x, y, z, el, az = geometry(D)
    col = mix(col, C((110, 124, 160)), np.exp(-np.abs(el - 1.0) / 5.0) * 0.35)  # low mist band
    return finish(col, D, 32, 0.03)


def sky_summer_night(D):
    col = night_sky(D, (26, 34, 76), (46, 62, 116), (110, 120, 170), (90, 70, 70), (40, 50, 96), (190, 204, 240),
                    cover=0.36, amount=0.75, seed=137, win_amt=0.75)
    return finish(col, D, 33, 0.03)


def sky_nightmare_night(D):
    col = night_sky(D, (34, 10, 22), (70, 18, 36), (150, 46, 52), (110, 40, 30), (60, 14, 22), (255, 110, 80),
                    cover=0.6, amount=0.95, seed=139, land=(24, 6, 10), win_amt=0.45, below_hi=(26, 8, 12))
    x, y, z, el, az = geometry(D)
    # embers: bright speckles in the low cloud banks
    sp = fbm3(D * 260.0, 2, 141)
    emb = ss(0.78, 0.86, sp) * ss(-0.5, 3, el) * ss(26, 6, el)
    col = col + C((255, 140, 60))[None, None, :] * (emb * 0.5)[..., None]
    return finish(col, D, 34, 0.03)


SETS = {
    "Dawn": sky_dawn,
    "Night": sky_night,
    "NightNew": sky_night_new,
    "NightCrimson": sky_night_crimson,
    "NightBlue": sky_night_blue,
    "Storm": sky_storm,
    "WinterDay": sky_winter_day, "WinterDusk": sky_winter_dusk, "WinterNight": sky_winter_night,
    "SpringDay": sky_spring_day, "SpringDusk": sky_spring_dusk, "SpringNight": sky_spring_night,
    "SummerDay": sky_summer_day, "SummerDusk": sky_summer_dusk, "SummerNight": sky_summer_night,
    "NightmareDusk": sky_nightmare_dusk, "NightmareNight": sky_nightmare_night,
}
