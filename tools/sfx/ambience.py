#!/usr/bin/env python3
"""Nightmare Highschool - ambience one-shots and spot loops, fully synthesized offline.

The owner: "make sounds ourselves". No samples, no library audio. Built from the same toolkit as the racial grip
SFX (tools/sfx/racial_grips.py): noise, oscillators, modal resonators, formant filters and synthetic rooms.
Deterministic: every sound reseeds its own RNG.

Content rule: NO blood / gore. Sounds are stone, wood, metal, paper, air, water and animals far away.

Two sheets are the upload (so the owner uploads two audio files, not thirty-three):
  NH_Ambience_OneShots.ogg   every one-shot in its own 4 s slot  (played with Sound.PlaybackRegion)
  NH_Ambience_Loops.ogg      every spot loop in its own 10 s slot (played with Sound.LoopRegion)
plus every sound as its own .ogg for listening. manifest.json gives each sound's slot; `--luau` prints the
Config.Ambience.Clips table to paste.

Usage (from the repo root):
    python tools/sfx/ambience.py            # render everything
    python tools/sfx/ambience.py --list
    python tools/sfx/ambience.py --luau     # print the Clips table from manifest.json

Output: art/sfx/ambience/
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy import signal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import racial_grips as rg  # noqa: E402
from racial_grips import (SR, ns, tvec, pk, U, noise, cnoise, srand, env_pts, perc, fade, place,  # noqa: E402
                          scatter_times, lp, hp, bp, tvf, modal_hit, modal_ir, res_grain, glass_grain, thump,
                          stone_knock, creak, rustle, fire, wind, bell, formant_filter, get_ir, write_ogg)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "art" / "sfx" / "ambience"
ONESHOT_SLOT = 4.0
LOOP_SLOT = 10.0
LOOP_LEN = 8.0


def rev(x, kind="hall", wet=0.35, dry=1.0):
    """Mix x with a synthetic room (hall, room, cathedral)."""
    w = signal.fftconvolve(hp(x, 140, 2), get_ir(kind))[:len(x)]
    return dry * x + wet * pk(w) * np.max(np.abs(x))


def far(x, cutoff=2200, kind="hall", wet=0.8):
    """Push a sound far away: dull it, more room than source."""
    return rev(lp(x, cutoff, 2), kind, wet=wet, dry=0.45)


def pad(x, dur):
    out = np.zeros(ns(dur))
    out[:min(len(x), len(out))] = x[:len(out)]
    return out


def norm(x, peak_db=-3.0):
    return pk(x) * 10 ** (peak_db / 20)


def seamless(x, xf=2.0):
    """x is LOOP_LEN + xf long: crossfade its tail into its head (equal power) so it loops."""
    n, m = ns(LOOP_LEN), ns(xf)
    head, tail = x[:m].copy(), x[n:n + m]
    u = np.linspace(0, 1, m)
    y = x[:n].copy()
    y[:m] = head * np.sin(u * np.pi / 2) + tail * np.cos(u * np.pi / 2)
    return y


def metal(freqs, t60, amps=None, dur=1.5, exc=0.003):
    amps = amps if amps is not None else np.linspace(1, 0.3, len(freqs))
    return modal_hit(np.array(freqs) * U(0.97, 1.03), np.full(len(freqs), t60) * np.linspace(1, 0.4, len(freqs)),
                     np.array(amps), dur, exc_len=exc, exc_decay=exc / 3)


def wood(scale=1.0, t60=0.05, dur=0.25):
    fr = np.array([310, 520, 870, 1340, 2050]) * scale * U(0.95, 1.05)
    return modal_hit(fr, t60 * np.array([1, .8, .6, .45, .3]), np.array([1, .7, .45, .3, .15]), dur,
                     exc_len=0.002, exc_decay=0.0006)


def step(heel=1.0):
    """One hard-soled step on stone: heel knock then a softer toe scuff."""
    out = np.zeros(ns(0.3))
    place(out, stone_knock(1.6, 0.05) * heel, 0)
    place(out, bp(noise(ns(0.05)), 900, 5000) * perc(ns(0.05), 0.003, 0.04) * 0.4, 0.06)
    return out


def drop(f0=900, f1=1900, dur=0.09):
    """A water drop: a resonant upward 'plink'."""
    n = ns(dur)
    t = tvec(n)
    f = f0 + (f1 - f0) * (t / dur) ** 0.6
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.02) * np.minimum(t / 0.001, 1)
    return fade(y, 0.0005, 0.005)


def chirp(f0, f1, dur, vib=0.0):
    n = ns(dur)
    t = tvec(n)
    f = np.geomspace(f0, f1, n) * (1 + vib * np.sin(2 * np.pi * 38 * t))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * np.linspace(0, 1, n)) ** 0.7
    return y + 0.15 * np.sin(2 * 2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * np.linspace(0, 1, n))


def voiced(dur, f0_pts, vowel, amp_pts, register="bass", rough=0.3, breath=0.2):
    """A short voiced animal call: a buzzy source through vowel formants."""
    n = ns(dur)
    f0 = env_pts(n, f0_pts) * (1 + 0.02 * srand(n, 18))
    ph = np.cumsum(f0) / SR
    src = 2 * (ph % 1) - 1
    src = src * np.clip(1 + rough * srand(n, 60), 0, None) + breath * noise(n)
    y = formant_filter(src, vowel, register)
    return fade(pk(y) * env_pts(n, amp_pts), 0.004, 0.02)


# ----------------------------------------------------------------------------
# one-shots  (name -> (function, seed))
# ----------------------------------------------------------------------------
def locker_slam():
    out = np.zeros(ns(2.0))
    place(out, metal([180, 297, 452, 610, 845, 1210, 1690, 2380], 0.45, dur=1.4), 0)
    place(out, thump(0.4, 140, 60, t60=0.18, click=0.6, body=0.6) * 0.6, 0)
    place(out, metal([2400, 3650, 5100], 0.05, dur=0.15) * 0.35, 0.03)   # the latch catching
    return far(out, 4500, "hall", 0.5)


def book_drop():
    out = np.zeros(ns(1.6))
    place(out, thump(0.5, 110, 45, t60=0.12, click=0.25, body=0.8, body_lp=500), 0)
    place(out, rustle(0.18, [(0, 900), (0.18, 0)], bright=0.8) * 0.3, 0.005)
    place(out, thump(0.3, 140, 60, t60=0.06, click=0.15, body=0.5) * 0.35, 0.11)   # a bounce
    return far(out, 3000, "hall", 0.55)


def door_far():
    out = np.zeros(ns(2.6))
    place(out, creak(0.5, [(0, 30), (0.5, 60)], [(0, 0.2), (0.25, 0.7), (0.5, 0)], scale=0.7) * 0.25, 0)
    place(out, thump(0.6, 90, 38, t60=0.3, click=0.3, body=0.7), 0.5)
    place(out, metal([1900, 2850, 4100], 0.04, dur=0.12) * 0.3, 0.52)
    return far(out, 1600, "hall", 1.0)


def steps_far():
    out = np.zeros(ns(3.2))
    at = 0.0
    for i in range(6):
        place(out, step(U(0.7, 1.0)) * (0.5 + 0.1 * i), at)
        at += 0.52 + U(-0.03, 0.03)
    out *= env_pts(len(out), [(0, 0.6), (1.6, 1.0), (3.2, 0.5)])
    return far(out, 1800, "hall", 0.9)


def stone_tick():
    out = np.zeros(ns(1.2))
    place(out, stone_knock(U(1.8, 2.4), 0.04) * 0.9, 0)
    if U(0, 1) < 0.7:
        place(out, stone_knock(U(2.4, 3.0), 0.03) * 0.4, U(0.12, 0.3))
    return rev(out, "hall", 0.6)


def pipe_knock():
    out = np.zeros(ns(2.4))
    at = 0.0
    for i in range(3):
        place(out, metal([210, 345, 520, 760, 1040], 0.6, dur=1.2) * (1.0 - 0.25 * i), at)
        at += U(0.18, 0.32)
    return far(out, 2400, "hall", 0.6)


def wood_creak():
    out = creak(1.4, [(0, 18), (0.6, 45), (1.4, 12)], [(0, 0), (0.15, 0.8), (0.9, 0.6), (1.4, 0)], scale=0.55, t60=0.05)
    return rev(pad(out, 2.4), "hall", 0.5)


def keys_far():
    out = np.zeros(ns(2.8))
    for at in scatter_times(1.6, [(0, 18), (0.4, 30), (1.0, 14), (1.6, 0)]):
        place(out, glass_grain(U(2600, 6200), U(0.05, 0.18)) * U(0.2, 0.9), at)
        if U(0, 1) < 0.3:
            place(out, metal([1400, 2300, 3500], 0.08, dur=0.2) * U(0.2, 0.5), at)
    return far(out, 3500, "hall", 1.0)


def draught():
    out = wind(3.0, [(0, 0), (1.1, 0.8), (3.0, 0)], center=520, whistle=0.2)
    return pad(lp(out, 2600), 3.6)


def chalk_tap():
    out = np.zeros(ns(1.8))
    at = 0.0
    for _ in range(int(U(4, 8))):
        place(out, res_grain(U(2200, 4200), U(2, 4), U(0.002, 0.005), noise_len=0.0005) * U(0.5, 1.0), at)
        place(out, bp(noise(ns(0.06)), 3000, 9000) * perc(ns(0.06), 0.002, 0.05) * U(0.1, 0.3), at + 0.004)
        at += U(0.09, 0.22)
    return rev(out, "room", 0.4)


def page_turn():
    out = rustle(0.75, [(0, 0), (0.15, 600), (0.45, 300), (0.75, 0)], bright=1.1, bed=0.45)
    return rev(pad(out, 1.4), "room", 0.3)


def chair_creak():
    out = creak(0.7, [(0, 30), (0.35, 70), (0.7, 25)], [(0, 0), (0.1, 0.9), (0.5, 0.6), (0.7, 0)], scale=0.9, t60=0.035)
    return rev(pad(out, 1.4), "room", 0.35)


def desk_tap():
    out = np.zeros(ns(1.2))
    at = 0.0
    for _ in range(int(U(2, 4))):
        place(out, wood(U(1.2, 1.5), 0.04) * U(0.6, 1.0), at)
        at += U(0.12, 0.2)
    return rev(out, "room", 0.4)


def bird_a():
    out = np.zeros(ns(2.2))
    at = 0.0
    for _ in range(int(U(3, 6))):
        place(out, chirp(U(3200, 3800), U(4800, 5600), U(0.05, 0.09)) * U(0.5, 1.0), at)
        at += U(0.08, 0.16)
    return far(out, 9000, "hall", 0.15)


def bird_b():
    out = np.zeros(ns(2.4))
    place(out, chirp(4200, 2600, 0.32, vib=0.06), 0)
    place(out, chirp(3000, 3900, 0.12) * 0.7, 0.42)
    place(out, chirp(3900, 2800, 0.25, vib=0.05) * 0.8, 0.6)
    return far(out, 9000, "hall", 0.15)


def town_bell():
    out = np.zeros(ns(3.8))
    place(out, bell(196, 3.6, t60=5.0, strike=0.4), 0)
    return far(out, 1800, "cathedral", 0.6)


def owl():
    out = np.zeros(ns(2.8))
    for at, d, f in ((0, 0.42, 370), (0.62, 0.22, 380), (0.9, 0.6, 360)):
        n = ns(d)
        t = tvec(n)
        y = np.sin(2 * np.pi * np.cumsum(np.full(n, f) * (1 + 0.03 * np.sin(np.pi * t / d))) / SR)
        y = (y + 0.08 * noise(n)) * np.sin(np.pi * np.linspace(0, 1, n)) ** 1.2
        place(out, lp(y, 900), at)
    return far(out, 1400, "hall", 0.4)


def crow():
    out = np.zeros(ns(2.4))
    at = 0.0
    for _ in range(int(U(2, 4))):
        d = U(0.24, 0.34)
        place(out, voiced(d, [(0, 520), (d * 0.3, 600), (d, 430)], "a", [(0, 0), (0.03, 1), (d * 0.7, 0.8), (d, 0)],
                          register="alto", rough=1.2, breath=0.5) * U(0.7, 1.0), at)
        at += d + U(0.12, 0.2)
    return far(out, 3800, "hall", 0.3)


def dog_far():
    out = np.zeros(ns(3.0))
    at = 0.0
    for _ in range(int(U(2, 4))):
        d = U(0.16, 0.22)
        place(out, voiced(d, [(0, 420), (d * 0.25, 520), (d, 300)], "a", [(0, 0), (0.015, 1), (d, 0)],
                          register="tenor", rough=0.9, breath=0.4), at)
        at += U(0.32, 0.6)
    return far(out, 1100, "hall", 1.0)


def gutter_drip():
    out = np.zeros(ns(2.4))
    at = 0.0
    for _ in range(int(U(3, 6))):
        f0 = U(700, 1200)
        place(out, drop(f0, f0 * U(1.8, 2.3)) * U(0.4, 1.0), at)
        at += U(0.25, 0.45)
    return rev(out, "hall", 0.3)


def wind_gust():
    out = wind(3.4, [(0, 0), (1.3, 1.0), (2.2, 0.6), (3.4, 0)], center=700, whistle=0.1)
    leaves = rustle(3.4, [(0, 0), (1.3, 400), (3.4, 0)], bright=1.0, bed=0.2)
    return pad(out + 0.25 * leaves, 3.8)


def paper_rustle():
    out = rustle(1.2, [(0, 0), (0.2, 900), (0.6, 200), (0.8, 700), (1.2, 0)], bright=1.0, bed=0.5)
    return rev(pad(out, 1.8), "hall", 0.6)


def book_thump():
    out = np.zeros(ns(2.0))
    place(out, thump(0.6, 100, 40, t60=0.16, click=0.2, body=0.9, body_lp=420), 0)
    return far(out, 2200, "hall", 0.8)


def valve_hiss():
    n = ns(2.6)
    t = tvec(n)
    y = pk(bp(noise(n), 1800, 9000)) * env_pts(n, [(0, 0), (0.05, 1), (1.2, 0.7), (2.4, 0), (2.6, 0)])
    y *= np.clip(1 + 0.25 * srand(n, 30), 0, None)
    out = y + 0.2 * metal([480, 790, 1180], 0.2, dur=2.6) * (t < 2.6)
    return rev(out, "hall", 0.3)


def furnace_clank():
    out = np.zeros(ns(2.6))
    place(out, metal([95, 160, 248, 372, 530, 760, 1050], 1.0, dur=2.2), 0)
    place(out, thump(0.5, 80, 35, t60=0.2, click=0.4, body=0.7) * 0.6, 0)
    place(out, metal([1300, 2100, 3000], 0.06, dur=0.2) * 0.4, 0.15)
    return rev(out, "hall", 0.5)


ONESHOTS = {
    # halls by day
    "locker_slam": (locker_slam, 101), "book_drop": (book_drop, 102), "door_far": (door_far, 103),
    "steps_far": (steps_far, 104),
    # halls at night (the building settling, the custodian far off)
    "stone_tick": (stone_tick, 111), "pipe_knock": (pipe_knock, 112), "wood_creak": (wood_creak, 113),
    "keys_far": (keys_far, 114), "draught": (draught, 115),
    # classrooms
    "chalk_tap": (chalk_tap, 121), "page_turn": (page_turn, 122), "chair_creak": (chair_creak, 123),
    "desk_tap": (desk_tap, 124),
    # outdoors
    "bird_a": (bird_a, 131), "bird_b": (bird_b, 132), "town_bell": (town_bell, 133),
    "owl": (owl, 141), "crow": (crow, 142), "dog_far": (dog_far, 143), "gutter_drip": (gutter_drip, 144),
    "wind_gust": (wind_gust, 145),
    # the Archive
    "paper_rustle": (paper_rustle, 151), "book_thump": (book_thump, 152),
    # the boiler
    "valve_hiss": (valve_hiss, 161), "furnace_clank": (furnace_clank, 162),
}


# ----------------------------------------------------------------------------
# spot loops (each LOOP_LEN seconds, seamless)
# ----------------------------------------------------------------------------
L = LOOP_LEN + 2.0   # rendered length before the seam crossfade


def clock_tick():
    out = np.zeros(ns(L))
    for i in range(int(L)):
        place(out, wood(2.2 if i % 2 == 0 else 1.9, 0.03, 0.12) * 0.9, i * 1.0)
        place(out, metal([3100, 4700], 0.02, dur=0.05) * 0.25, i * 1.0)
    return seamless(rev(out, "room", 0.25))


def radiator_hum():
    n = ns(L)
    t = tvec(n)
    y = sum(a * np.sin(2 * np.pi * f * t) for f, a in ((50, 1.0), (100, 0.5), (150, 0.25), (200, 0.1)))
    y = y * (1 + 0.15 * srand(n, 0.4)) + 0.5 * pk(bp(cnoise(n, 1.5), 120, 900)) * (1 + 0.3 * srand(n, 0.6))
    out = pk(y)
    for at in (2.3, 6.9):   # the odd metal tick as it warms
        place(out, metal([1500, 2400, 3300], 0.03, dur=0.08) * 0.25, at)
    return seamless(out)


def vending_hum():
    n = ns(L)
    t = tvec(n)
    y = sum(a * np.sin(2 * np.pi * f * t) for f, a in ((60, 1.0), (120, 0.7), (180, 0.3), (240, 0.2), (360, 0.08)))
    comp = pk(lp(cnoise(n, 2.0), 300)) * 0.6
    fan = pk(bp(noise(n), 400, 2400)) * 0.2 * (1 + 0.1 * np.sin(2 * np.pi * 23 * t))
    return seamless(pk(pk(y) + comp + fan))


def candle_crackle():
    out = fire(L, [(0, 1), (L, 1)], [(0, 6), (L, 6)], roar=0.08)
    return seamless(lp(out, 7000) * 0.8)


def tap_drip():
    out = np.zeros(ns(L))
    at = 0.3
    while at < L - 0.2:
        place(out, drop(U(950, 1150), U(2000, 2400)) * U(0.6, 1.0), at)
        at += U(1.1, 1.8)
    return seamless(rev(out, "room", 0.5))


def tube_buzz():
    n = ns(L)
    t = tvec(n)
    saw = 2 * ((120 * t) % 1) - 1
    y = bp(saw, 110, 3000) * (1 + 0.05 * srand(n, 3))
    for at in (1.7, 5.2, 5.35):   # flicker clicks
        place(y, res_grain(U(2000, 5000), 3, 0.003) * 0.6, at)
    return seamless(pk(y) * 0.8)


def fire_crackle():
    out = fire(L, [(0, 1), (L, 1)], [(0, 20), (L, 20)], roar=0.4)
    return seamless(out)


LOOPS = {
    "clock_tick": (clock_tick, 201), "radiator_hum": (radiator_hum, 202), "vending_hum": (vending_hum, 203),
    "candle_crackle": (candle_crackle, 204), "tap_drip": (tap_drip, 205), "tube_buzz": (tube_buzz, 206),
    "fire_crackle": (fire_crackle, 207),
}


# ----------------------------------------------------------------------------
def check(name, x, loop=False):
    issues = []
    if not np.all(np.isfinite(x)):
        issues.append("non-finite")
    peak = float(np.max(np.abs(x)))
    rms = float(np.sqrt(np.mean(x ** 2)))
    if peak < 0.05:
        issues.append(f"too quiet (peak {peak:.3f})")
    if loop:
        jump = abs(x[-1] - x[0])
        if jump > 0.05:
            issues.append(f"loop seam jump {jump:.3f}")
    else:
        if abs(x[-1]) > 1e-3:
            issues.append("doesn't end in silence")
    return {"peak_db": round(20 * np.log10(peak + 1e-12), 1), "rms_db": round(20 * np.log10(rms + 1e-12), 1),
            "issues": issues}


def render():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"OneShots": {}, "Loops": {}, "OneShotSlot": ONESHOT_SLOT, "LoopSlot": LOOP_SLOT}
    sheet = np.zeros(ns(ONESHOT_SLOT * len(ONESHOTS)))
    for i, (name, (fn, seed)) in enumerate(ONESHOTS.items()):
        rg.reseed(seed)
        x = fade(norm(fn()), 0.0005, 0.08)
        x = x[:ns(ONESHOT_SLOT - 0.25)]
        x = fade(x, 0.0005, 0.08)
        write_ogg(x, OUT / f"{name}.ogg")
        place(sheet, x, i * ONESHOT_SLOT)
        info = check(name, x)
        manifest["OneShots"][name] = {"Start": i * ONESHOT_SLOT, "Length": round(len(x) / SR, 3), **info}
        print(f"  one-shot {name:14s} {len(x) / SR:5.2f}s  peak {info['peak_db']:6.1f}  {info['issues'] or ''}")
    write_ogg(sheet, OUT / "NH_Ambience_OneShots.ogg")
    lsheet = np.zeros(ns(LOOP_SLOT * len(LOOPS)))
    for i, (name, (fn, seed)) in enumerate(LOOPS.items()):
        rg.reseed(seed)
        x = norm(fn(), -4.0)
        write_ogg(np.tile(x, 3), OUT / f"loop_{name}.ogg")   # 3 laps, to hear the seam
        place(lsheet, x, i * LOOP_SLOT)
        info = check(name, x, loop=True)
        manifest["Loops"][name] = {"Start": i * LOOP_SLOT, "Length": LOOP_LEN, **info}
        print(f"  loop     {name:14s} {len(x) / SR:5.2f}s  peak {info['peak_db']:6.1f}  {info['issues'] or ''}")
    write_ogg(lsheet, OUT / "NH_Ambience_Loops.ogg")
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"sheets: {len(sheet) / SR:.0f}s one-shots, {len(lsheet) / SR:.0f}s loops -> {OUT}")


def luau():
    m = json.loads((OUT / "manifest.json").read_text())
    print("Ambience.Clips = {")
    for name, v in m["OneShots"].items():
        print(f"\t{name} = {{ Sheet = `OneShots`; Start = {v['Start']}; Length = {v['Length']} }};")
    for name, v in m["Loops"].items():
        print(f"\t{name} = {{ Sheet = `Loops`; Start = {v['Start']}; Length = {v['Length']}; Loop = true }};")
    print("}")


if __name__ == "__main__":
    if "--list" in sys.argv:
        print("\n".join(list(ONESHOTS) + [f"loop {k}" for k in LOOPS]))
    elif "--luau" in sys.argv:
        luau()
    else:
        render()
