#!/usr/bin/env python3
"""Nightmare Highschool - racial grip finisher SFX, fully synthesized offline.

No samples, no library audio: every sound is built here from noise, oscillators,
modal resonators, formant filters, granular clouds and a synthetic stone-hall
impulse response.  Deterministic (each cue reseeds its own RNG).

Content rule: NO blood / gore.  Impacts are made from stone, wood, bone-as-dry-wood,
cloth, air and supernatural textures only.

Usage (from the repo root):
    python tools/sfx/racial_grips.py                 # render all cues + previews + checks
    python tools/sfx/racial_grips.py grip_vampire    # render one (or several) cues
    python tools/sfx/racial_grips.py --list          # list cue names
    python tools/sfx/racial_grips.py --check         # only re-run checks on existing .ogg files
    python tools/sfx/racial_grips.py --no-preview    # skip spectrogram PNGs

Output: art/sfx/racial-grips/<name>.ogg, manifest.json, previews/<name>.png
Retiming: every cue has a BEATS dict at the top of its function (seconds from clip start).
"""
import argparse
import json
import struct
import subprocess
import sys
import zlib
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SR = 48000
NYQ_SAFE = 0.45 * SR
TAIL = 1.0                 # seconds of ring-out after the animation clip
PEAK_DBFS = -1.0
ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "art" / "sfx" / "racial-grips"
PREV_DIR = OUT_DIR / "previews"

RNG = np.random.default_rng(0)


def reseed(seed):
    global RNG
    RNG = np.random.default_rng(seed)


# ----------------------------------------------------------------------------
# basic helpers
# ----------------------------------------------------------------------------
def ns(sec):
    return max(0, int(round(sec * SR)))


def tvec(n):
    return np.arange(n) / SR


def db(x):
    return 10.0 ** (np.asarray(x) / 20.0)


def pk(x):
    m = np.max(np.abs(x)) if len(x) else 0.0
    return x / m if m > 1e-12 else x


def U(a, b, size=None):
    return RNG.uniform(a, b, size)


def noise(n):
    return RNG.standard_normal(n)


def cnoise(n, alpha=1.0):
    """Coloured noise via FFT shaping (power ~ 1/f^alpha). Periodic in n."""
    X = np.fft.rfft(RNG.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = f[1]
    X *= f ** (-alpha / 2.0)
    x = np.fft.irfft(X, n)
    return x / (np.std(x) + 1e-12)


def srand(n, rate):
    """Smooth random control signal, unit std, bandwidth ~ rate Hz."""
    m = max(n, int(8 * SR / rate))          # long enough for a stable std, then cut
    k = int(m / SR * rate) + 4
    pts = RNG.standard_normal(k)
    x = np.interp(np.arange(m) * rate / SR, np.arange(k), pts)
    w = max(1, int(SR / rate))
    x = uniform_filter1d(x, w, mode="nearest")
    return (x / (np.std(x) + 1e-12))[:n]


def env_pts(n, pts):
    ts, vs = zip(*pts)
    return np.interp(tvec(n), ts, vs)


def perc(n, att, t60):
    t = tvec(n)
    return np.minimum(t / max(att, 1e-5), 1.0) * np.exp(-6.91 * np.maximum(t - att, 0) / t60)


def fade(x, fin=0.003, fout=0.005):
    x = x.copy()
    a, b = ns(fin), ns(fout)
    if a:
        x[:a] *= np.linspace(0, 1, a)
    if b:
        x[-b:] *= np.linspace(1, 0, b)
    return x


def place(buf, sig, at):
    i = int(round(at * SR))
    if i < 0:
        sig = sig[-i:]
        i = 0
    if i >= len(buf) or len(sig) == 0:
        return
    m = min(len(sig), len(buf) - i)
    buf[i:i + m] += sig[:m]


def scatter_times(dur, dens_pts, res=0.001):
    """Poisson event times with a piecewise-linear density (events/s)."""
    tg = np.arange(0, dur, res)
    ts, vs = zip(*dens_pts)
    d = np.clip(np.interp(tg, ts, vs), 0, None)
    cum = np.cumsum(d) * res
    total = cum[-1]
    k = RNG.poisson(total)
    u = np.sort(RNG.uniform(0, total, k))
    return np.interp(u, cum, tg)


# ----------------------------------------------------------------------------
# filters
# ----------------------------------------------------------------------------
def _fc(f):
    return float(np.clip(f, 10.0, NYQ_SAFE))


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, _fc(f), "lowpass", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, _fc(f), "highpass", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(signal.butter(order, [_fc(lo), _fc(hi)], "bandpass", fs=SR, output="sos"), x)


def _rbj(kind, f, q):
    w = 2 * np.pi * _fc(f) / SR
    cw, sw = np.cos(w), np.sin(w)
    al = sw / (2 * max(q, 0.05))
    if kind == "bp":
        b = (al, 0.0, -al)
    elif kind == "lp":
        b = ((1 - cw) / 2, 1 - cw, (1 - cw) / 2)
    else:  # hp
        b = ((1 + cw) / 2, -(1 + cw), (1 + cw) / 2)
    a0 = 1 + al
    return np.array(b) / a0, np.array((1.0, -2 * cw / a0, (1 - al) / a0))


def tvf(x, f, q=0.707, kind="bp", block=48):
    """Time-varying RBJ biquad, coefficients updated per block (state carried)."""
    n = len(x)
    f = np.broadcast_to(np.asarray(f, float), (n,))
    q = np.broadcast_to(np.asarray(q, float), (n,))
    y = np.empty(n)
    zi = np.zeros(2)
    for i in range(0, n, block):
        b, a = _rbj(kind, f[i], q[i])
        y[i:i + block], zi = signal.lfilter(b, a, x[i:i + block], zi=zi)
    return y


def drive(x, k=2.0, os_=4):
    """Oversampled tanh saturation (no aliasing)."""
    u = signal.resample_poly(x, os_, 1)
    u = np.tanh(k * u) / np.tanh(k)
    return signal.resample_poly(u, 1, os_)[:len(x)]


# ----------------------------------------------------------------------------
# oscillators / resonators
# ----------------------------------------------------------------------------
def blep_saw(freq, n=None, phase0=None):
    """Band-limited (polyBLEP) sawtooth with arbitrary frequency curve."""
    if n is None:
        n = len(freq)
    f = np.broadcast_to(np.asarray(freq, float), (n,))
    dt = np.clip(f / SR, 1e-7, 0.45)
    p = (np.cumsum(dt) + (RNG.random() if phase0 is None else phase0)) % 1.0
    y = 2 * p - 1
    m = p < dt
    x = p[m] / dt[m]
    y[m] -= x + x - x * x - 1
    m = p > 1 - dt
    x = (p[m] - 1) / dt[m]
    y[m] -= x * x + x + x + 1
    return y


def modal_ir(freqs, t60s, amps, dur, phase="zero"):
    freqs = np.asarray(freqs, float)
    t60s = np.broadcast_to(np.asarray(t60s, float), freqs.shape)
    amps = np.broadcast_to(np.asarray(amps, float), freqs.shape)
    keep = freqs < NYQ_SAFE
    freqs, t60s, amps = freqs[keep], t60s[keep], amps[keep]
    n = ns(dur)
    t = tvec(n)
    ph = RNG.random(len(freqs)) * 2 * np.pi if phase == "rand" else np.zeros(len(freqs))
    out = np.zeros(n)
    for f, T, a, p in zip(freqs, t60s, amps, ph):
        out += a * np.exp(-6.91 * t / T) * np.sin(2 * np.pi * f * t + p)
    return out


def res_grain(fc, q, decay, noise_len=0.0006, dur=None):
    """Noise-excited resonant ping: ticks, crackles, pebbles."""
    dur = dur or min(decay * 6 + 0.003, 0.25)
    n = max(ns(dur), 8)
    t = tvec(n)
    x = noise(n) * np.exp(-t / noise_len)
    b, a = _rbj("bp", fc, q)
    y = signal.lfilter(b, a, x) * np.exp(-t / decay)
    return pk(y)


def glass_grain(f0, t60, dur=None):
    ratios = np.array([1.0, 2.756, 5.404, 8.933])
    amps = np.array([1.0, 0.5, 0.28, 0.14])
    det = 1 + U(-0.004, 0.004, 4)
    dur = dur or min(t60 * 1.1 + 0.01, 3.0)
    y = modal_ir(f0 * ratios * det, t60 * np.array([1, .7, .5, .35]), amps, dur)
    n = len(y)
    y *= np.minimum(tvec(n) / 0.0004, 1)
    return pk(y)


# ----------------------------------------------------------------------------
# reverb
# ----------------------------------------------------------------------------
IR_SPECS = {
    "hall": dict(rt=2.1, pre=0.016, n_er=12, seed=9001, bands=(1.25, 1.0, 0.8, 0.55, 0.33)),
    "cathedral": dict(rt=4.4, pre=0.032, n_er=14, seed=9002, bands=(1.3, 1.0, 0.8, 0.5, 0.3)),
    "room": dict(rt=0.65, pre=0.005, n_er=8, seed=9003, bands=(1.1, 1.0, 0.8, 0.6, 0.4)),
}
_IRS = {}


def get_ir(name):
    if name in _IRS:
        return _IRS[name]
    s = IR_SPECS[name]
    rng = np.random.default_rng(s["seed"])
    rt = s["rt"]
    n = ns(min(rt * 1.25, 5.5))
    t = tvec(n)
    edges = [(None, 220), (220, 900), (900, 3200), (3200, 8000), (8000, None)]
    ir = np.zeros(n)
    for (lo, hi), m in zip(edges, s["bands"]):
        w = rng.standard_normal(n)
        if lo is None:
            w = lp(w, hi, 4)
        elif hi is None:
            w = hp(w, lo, 4)
        else:
            w = bp(w, lo, hi, 2)
        ir += w * np.exp(-6.91 * t / (rt * m))
    ir *= 1 - np.exp(-t / 0.025)          # diffuse build-up
    lvl = np.std(ir[ns(0.03):ns(0.08)])
    for _ in range(s["n_er"]):          # discrete early reflections off stone
        d = rng.uniform(0.003, 0.075)
        g = rng.uniform(2.0, 5.0) * np.exp(-d / 0.06) * rng.choice([-1, 1])
        ir[ns(d)] += g * lvl
    ir = np.concatenate([np.zeros(ns(s["pre"])), ir])
    ir /= np.sqrt(np.sum(ir ** 2))
    _IRS[name] = ir
    return ir


def reverse_swell(sig, rev="hall", length=0.6):
    """Reverse-reverb: wet-only reverb of sig, reversed, ends where sig starts."""
    wet = signal.fftconvolve(sig, get_ir(rev))[:ns(length)]
    r = wet[::-1].copy()
    r *= np.linspace(0, 1, len(r)) ** 0.5
    return fade(pk(r), 0.01, 0.006)


class Bus:
    def __init__(self, dur):
        self.n = ns(dur)
        self.dry = np.zeros(self.n)
        self.wet = {}

    def add(self, sig, at=0.0, gain=1.0, send=0.0, rev="hall"):
        sig = np.asarray(sig) * gain
        place(self.dry, sig, at)
        if send > 0:
            buf = self.wet.setdefault(rev, np.zeros(self.n))
            place(buf, sig * send, at)

    def mix(self, wet_gain=1.0):
        out = self.dry.copy()
        for k, buf in self.wet.items():
            out += wet_gain * signal.fftconvolve(hp(buf, 140, 2), get_ir(k))[:self.n]   # no muddy low reverb
        return out


# ----------------------------------------------------------------------------
# formants
# ----------------------------------------------------------------------------
# (F1..F5 Hz, amplitude dB, bandwidth Hz) - classic sung-vowel formant table
FORMANTS = {
    "bass": {
        "a": ([600, 1040, 2250, 2450, 2750], [0, -7, -9, -9, -20], [60, 70, 110, 120, 130]),
        "e": ([400, 1620, 2400, 2800, 3100], [0, -12, -9, -12, -18], [40, 80, 100, 120, 120]),
        "i": ([250, 1750, 2600, 3050, 3340], [0, -30, -16, -22, -28], [60, 90, 100, 120, 120]),
        "o": ([400, 750, 2400, 2600, 2900], [0, -11, -21, -20, -40], [40, 80, 100, 120, 120]),
        "u": ([350, 600, 2400, 2675, 2950], [0, -20, -32, -28, -36], [40, 80, 100, 120, 120]),
    },
    "tenor": {
        "a": ([650, 1080, 2650, 2900, 3250], [0, -6, -7, -8, -22], [80, 90, 120, 130, 140]),
        "e": ([400, 1700, 2600, 3200, 3580], [0, -14, -12, -14, -20], [70, 80, 100, 120, 120]),
        "i": ([290, 1870, 2800, 3250, 3540], [0, -15, -18, -20, -30], [40, 90, 100, 120, 120]),
        "o": ([400, 800, 2600, 2800, 3000], [0, -10, -12, -12, -26], [40, 80, 100, 120, 120]),
        "u": ([350, 600, 2700, 2900, 3300], [0, -20, -17, -14, -26], [40, 60, 100, 120, 120]),
    },
    "alto": {
        "a": ([800, 1150, 2800, 3500, 4950], [0, -4, -20, -36, -60], [80, 90, 120, 130, 140]),
        "e": ([400, 1600, 2700, 3300, 4950], [0, -24, -30, -35, -60], [60, 80, 120, 150, 200]),
        "i": ([350, 1700, 2700, 3700, 4950], [0, -20, -30, -36, -60], [50, 100, 120, 150, 200]),
        "o": ([450, 800, 2830, 3500, 4950], [0, -9, -16, -28, -55], [70, 80, 100, 130, 135]),
        "u": ([325, 700, 2530, 3500, 4950], [0, -12, -30, -40, -64], [50, 60, 170, 180, 200]),
    },
    "soprano": {
        "a": ([800, 1150, 2900, 3900, 4950], [0, -6, -32, -20, -50], [80, 90, 120, 130, 140]),
        "e": ([350, 2000, 2800, 3600, 4950], [0, -20, -15, -40, -56], [60, 100, 120, 150, 200]),
        "i": ([270, 2140, 2950, 3900, 4950], [0, -12, -26, -26, -44], [60, 90, 100, 120, 120]),
        "o": ([450, 800, 2830, 3800, 4950], [0, -11, -22, -22, -50], [70, 80, 100, 130, 135]),
        "u": ([325, 700, 2700, 3800, 4950], [0, -16, -35, -40, -60], [50, 60, 170, 180, 200]),
    },
}


def formant_filter(x, vowel, register="bass", shift=1.0, bw_mul=1.0, nform=5):
    """Bandpass-bank formant filter; vowel = 'a' or [(t, 'a'), (t, 'o'), ...]."""
    n = len(x)
    keys = [(0.0, vowel)] if isinstance(vowel, str) else list(vowel)
    ts = [k[0] for k in keys]
    tab = FORMANTS[register]
    F = np.array([tab[v][0] for _, v in keys], float)
    A = np.array([tab[v][1] for _, v in keys], float)
    B = np.array([tab[v][2] for _, v in keys], float)
    tt = tvec(n)
    sh = np.broadcast_to(np.asarray(shift, float), (n,))
    y = np.zeros(n)
    for i in range(nform):
        Fi = np.interp(tt, ts, F[:, i]) * sh
        Ai = db(np.interp(tt, ts, A[:, i]))
        Bi = np.interp(tt, ts, B[:, i]) * bw_mul * np.sqrt(sh)
        y += Ai * tvf(x, Fi, Fi / Bi, "bp")
    return y


# ----------------------------------------------------------------------------
# sound elements
# ----------------------------------------------------------------------------
def thump(dur=0.6, f0=120.0, f1=40.0, pdecay=0.04, t60=0.35, click=0.4, body=0.5, sat=1.5, body_lp=280):
    """Sub-bass impact: pitch-dropping sine + noise body + click transient."""
    n = ns(dur)
    t = tvec(n)
    f = f1 + (f0 - f1) * np.exp(-t / pdecay)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(t / 0.0012, 1) * np.exp(-6.91 * t / t60)
    if sat > 0:
        y = np.tanh(sat * y) / np.tanh(sat)
    if body > 0:
        y = y + body * pk(lp(noise(n), body_lp, 2)) * np.exp(-t / 0.035) * np.minimum(t / 0.001, 1)
    if click > 0:
        y = y + click * pk(hp(noise(n), 2000, 2)) * np.exp(-t / 0.0012)
    return fade(y, 0, 0.01)


def whoosh(dur, f_start, f_peak, f_end, peak=0.5, q=1.0, shape=2.0, flutter=0.0, low=0.3):
    n = ns(dur)
    u = np.linspace(0, 1, n)
    up = np.clip(u / peak, 0, 1)
    dn = np.clip((u - peak) / (1 - peak + 1e-9), 0, 1)
    f = np.where(u < peak, f_start * (f_peak / f_start) ** up, f_peak * (f_end / f_peak) ** dn)
    env = np.where(u < peak, up ** shape, (1 - dn) ** (shape * 0.7))
    x = noise(n)
    y = tvf(x, f, q, "bp") + low * tvf(x, f * 0.5, 0.7, "lp")
    if flutter:
        y *= np.clip(1 + flutter * srand(n, 28), 0, None)
    return fade(pk(y * env), 0.002, 0.01)


def rustle(dur, dens_pts, bright=1.0, bed=0.25):
    """Cloth: granular crinkles + soft filtered bed."""
    n = ns(dur)
    out = np.zeros(n)
    for at in scatter_times(dur, dens_pts):
        d = U(0.006, 0.035)
        m = ns(d)
        g = noise(m) * np.sin(np.pi * np.linspace(0, 1, m)) ** 0.6
        b, a = _rbj("bp", U(1000, 5200) * bright, U(0.6, 1.5))
        place(out, signal.lfilter(b, a, g) * U(0.15, 1.0), at)
    ts, vs = zip(*dens_pts)
    den = np.interp(tvec(n), ts, vs)
    bedsig = bp(noise(n), 500 * bright, 5000 * bright) * (den / (max(vs) + 1e-9)) * np.clip(1 + 0.6 * srand(n, 14), 0, None)
    return fade(pk(pk(out) + bed * pk(bedsig)), 0.003, 0.01)


def wing_flap(bright=1.0):
    d = U(0.028, 0.06)
    n = ns(d + 0.02)
    t = tvec(n)
    env = np.minimum(t / 0.0035, 1) * np.exp(-np.maximum(t - 0.0035, 0) / (d * 0.32))
    flutter = 1 + 0.55 * np.sin(2 * np.pi * U(50, 120) * t + U(0, 6.28))
    x = noise(n)
    b, a = _rbj("bp", U(380, 1400) * bright, U(0.7, 1.4))
    y = signal.lfilter(b, a, x)
    b2, a2 = _rbj("lp", 240, 0.7)
    y = (pk(y) + 0.4 * pk(signal.lfilter(b2, a2, x))) * env * flutter
    snap = res_grain(U(2500, 5500) * bright, 2.0, 0.0012)
    s = ns(U(0.002, 0.008))
    m = min(len(snap), n - s)
    y[s:s + m] += 0.35 * snap[:m] * np.max(np.abs(y))
    return pk(y)


def bat_chirp():
    n = ns(U(0.008, 0.018))
    f = np.linspace(U(8500, 10500), U(5200, 6500), n)
    y = tvf(noise(n), f, 9, "bp") * np.sin(np.pi * np.linspace(0, 1, n))
    return pk(y)


def bat_swarm(total, spawn, n_bats=26, spread=0.05, disperse=2.3, disperse_len=0.8, bright=1.0,
              rate=(8.0, 13.0), chirps=10):
    out = np.zeros(ns(total))
    for _ in range(n_bats):
        t_on = spawn + RNG.exponential(spread)
        r = U(*rate)
        of = U(0.5, 1.6)
        oph = U(0, 2 * np.pi)
        d_off = disperse + U(-0.15, 0.4)
        d_len = disperse_len * U(0.6, 1.4)
        base = U(0.45, 1.0)
        t = t_on
        while t < total - 0.09:
            age = t - t_on
            near = 0.5 + 0.5 * np.sin(2 * np.pi * of * age + oph)
            g = base * (0.3 + 0.7 * near) * (1 + 0.9 * np.exp(-age / 0.15))
            if t > d_off:
                g *= np.exp(-(t - d_off) / d_len * 2.5)
            if g < 0.02:
                break
            place(out, wing_flap(bright * (0.8 + 0.45 * near)) * g, t)
            t += U(0.85, 1.15) / r
    for _ in range(chirps):
        place(out, bat_chirp() * U(0.08, 0.2), spawn + U(0.02, max(0.1, disperse - spawn + 0.5)))
    # swirling air of the swarm
    n = len(out)
    tt = tvec(n)
    act = np.clip((tt - spawn) / 0.05, 0, 1) * np.where(tt > disperse, np.exp(-(tt - disperse) / disperse_len * 2), 1.0)
    swirl_f = 650 * 1.8 ** np.sin(2 * np.pi * 1.3 * tt)
    air = tvf(noise(n), swirl_f, 1.1, "bp") * act * np.clip(1 + 0.5 * srand(n, 9), 0, None)
    return pk(out) + 0.12 * pk(air)


def heartbeat(gap=0.28, muff=200, strength=1.0, lub_only=False):
    """Deep muffled lub-dub."""
    n = ns(gap + 0.5)
    out = np.zeros(n)
    lub = thump(0.42, 72, 36, pdecay=0.03, t60=0.24, click=0.0, body=0.7, sat=2.2, body_lp=160)
    knock = res_grain(105, 1.6, 0.045, noise_len=0.004)
    place(out, lub, 0)
    place(out, 0.3 * knock, 0)
    if not lub_only:
        dub = thump(0.34, 90, 44, pdecay=0.022, t60=0.17, click=0.0, body=0.6, sat=2.2, body_lp=180)
        place(out, 0.72 * dub, gap)
        place(out, 0.22 * res_grain(130, 1.6, 0.035, noise_len=0.003), gap)
    out = lp(out, muff, 2) + 0.12 * lp(out, muff * 2.5, 2)
    out = drive(pk(out), 1.6)
    return fade(pk(out) * strength, 0.001, 0.02)


def shimmer(dur, base=1800, n_part=14, spread=(1.0, 3.6), att=0.06, t60=0.6, sparkle=18, air=0.08):
    n = ns(dur)
    t = tvec(n)
    y = np.zeros(n)
    for k in range(n_part):
        f = base * U(*spread)
        drift = 1 + 0.004 * srand(n, 3)
        trem = 1 + 0.45 * np.sin(2 * np.pi * U(3, 8) * t + U(0, 6.28))
        y += U(0.3, 1.0) * trem * np.sin(2 * np.pi * np.cumsum(f * drift) / SR + U(0, 6.28))
    env = np.minimum(t / att, 1) * np.exp(-6.91 * np.maximum(t - att, 0) / t60)
    y = pk(y) * env
    sp = np.zeros(n)
    for at in scatter_times(dur, [(0, sparkle), (dur * 0.5, sparkle * 0.6), (dur, 0)]):
        place(sp, glass_grain(base * U(1.2, 4.5), U(0.05, 0.2)) * U(0.2, 1.0), at)
    y = y + 0.4 * pk(sp) * env + air * pk(hp(noise(n), 7000)) * env
    return fade(pk(y), 0.004, 0.02)


def strings(notes, dur, amp_pts, cut_pts, voices=5, detune=10, vib=0.004, bow=0.08):
    """Dark string-section cluster: detuned polyBLEP saws, filter envelope, bow noise."""
    n = ns(dur)
    t = tvec(n)
    y = np.zeros(n)
    for f in notes:
        for _ in range(voices):
            fv = f * 2 ** (U(-detune, detune) / 1200)
            v = 1 + vib * np.sin(2 * np.pi * U(4.6, 6.0) * t + U(0, 6.28)) * np.minimum(t / 0.3, 1)
            y += blep_saw(fv * v * (1 + 0.0015 * srand(n, 2)))
    y /= np.sqrt(len(notes) * voices)
    cut = env_pts(n, cut_pts)
    y = tvf(tvf(y, cut, 0.6, "lp"), cut * 1.1, 0.6, "lp")
    body = 0.5 * tvf(y, 280, 2.0) + 0.35 * tvf(y, 720, 2.0) + 0.2 * tvf(y, 1500, 1.5)
    y = y + body
    bown = tvf(noise(n), cut * 1.6, 0.8, "bp")
    y = pk(y) + bow * pk(bown)
    return fade(pk(y) * env_pts(n, amp_pts), 0.002, 0.02)


def choir(notes, dur, vowel, amp_pts, register="soprano", voices=3, detune=10, vib=0.006, vib_rate=5.3,
          pitch_mult=None, breath=0.12, shift=1.0, bw_mul=1.0, tilt=2600):
    n = ns(dur)
    t = tvec(n)
    pm = 1.0 if pitch_mult is None else pitch_mult
    src = np.zeros(n)
    for f in notes:
        for _ in range(voices):
            vr = vib_rate * U(0.85, 1.15)
            v = 1 + vib * np.sin(2 * np.pi * vr * t + U(0, 6.28)) * np.minimum(t / 0.3, 1)
            src += blep_saw(f * 2 ** (U(-detune, detune) / 1200) * pm * v * (1 + 0.002 * srand(n, 4)))
    src = lp(src, tilt, 1) / np.sqrt(len(notes) * voices)
    src = pk(src) + breath * noise(n) * 0.5
    y = formant_filter(src, vowel, register, shift, bw_mul)
    return fade(pk(y) * env_pts(n, amp_pts), 0.003, 0.02)


def growl(dur, f0_pts, vowel, amp_pts, register="bass", shift=0.85, bw_mul=2.0, noise_mix=0.5, rough=0.6,
          jitter=0.05, sub=0.6, drive_k=2.5, shake=None, irregular=0.25):
    """Formant-filtered growl: jittery saw + subharmonic + noise, AM roughness, saturation."""
    n = ns(dur)
    t = tvec(n)
    f0 = env_pts(n, f0_pts) * (1 + jitter * srand(n, 22))
    shk = np.zeros(n)
    if shake:
        rate, depth = shake
        shk = depth * np.sin(2 * np.pi * rate * t)
        f0 = f0 * (1 + 0.25 * shk)
    v = blep_saw(f0) + sub * blep_saw(f0 * 0.5)
    am = np.clip(1 + rough * srand(n, 38), 0, None)
    exc = v * am * (1 - noise_mix) + noise_mix * 1.4 * noise(n) * np.clip(1 + 0.7 * srand(n, 30), 0, None)
    sh = shift * (1 + 0.04 * srand(n, 3)) * (1 + 0.07 * shk)
    y = formant_filter(exc, vowel, register, sh, bw_mul)
    y = pk(y) + 0.2 * (1 - noise_mix) * pk(lp(v * am, 220))
    if drive_k:
        y = drive(pk(y), drive_k)
    y = lp(y, 6000, 2)
    env = env_pts(n, amp_pts) * (1 - irregular + irregular * np.clip(0.5 + 0.5 * srand(n, 7), 0, 1.3))
    if shake:
        env *= 1 - 0.45 * (0.5 + 0.5 * np.sin(2 * np.pi * shake[0] * t + 1.0)) * shake[1]
    return fade(pk(y) * env, 0.003, 0.02)


def howl(dur, f0_pts, amp_pts, vib_pts, bright_pts, vib_rate=5.2, breath=0.2):
    """Wolf howl: additive harmonics weighted by an 'oo' formant envelope + breath."""
    n = ns(dur)
    t = tvec(n)
    f0 = env_pts(n, f0_pts)
    vd = env_pts(n, vib_pts)
    f0 = f0 * (1 + vd * np.sin(2 * np.pi * vib_rate * t * (1 + 0.05 * srand(n, 1))) + 0.004 * srand(n, 6))
    ph = 2 * np.pi * np.cumsum(f0) / SR
    tilt = env_pts(n, bright_pts)
    y = np.zeros(n)
    for k in range(1, 20):
        fk = k * f0
        if fk.min() > NYQ_SAFE:
            break
        form = (1.0 / (1 + ((fk - 640) / 330) ** 2) + 0.4 / (1 + ((fk - 1250) / 380) ** 2)
                + 0.12 / (1 + ((fk - 2700) / 600) ** 2) + 0.03)
        amp = form * k ** (-tilt) * np.clip((NYQ_SAFE - fk) / 2000, 0, 1)
        y += amp * np.sin(k * ph + U(0, 6.28))
    y = pk(y)
    x = noise(n)
    br = pk(tvf(x, f0, 5, "bp")) * 0.5 + pk(tvf(x, f0 * 2, 4, "bp")) * 0.3 + pk(bp(x, 1400, 4500)) * 0.25
    y = (y + breath * br) * np.clip(1 + 0.06 * srand(n, 25), 0, None)
    return fade(pk(y) * env_pts(n, amp_pts), 0.004, 0.03)


def bell(prime, dur, t60=6.0, strike=0.5):
    """Church bell: inharmonic minor-third bell partials, warbling pairs, FM strike clang."""
    parts = [(0.5, 0.2, 1.0), (1.0, 0.45, 0.8), (1.183, 0.5, 0.62), (1.506, 0.24, 0.48), (2.0, 0.7, 0.42),
             (2.514, 0.3, 0.32), (2.662, 0.26, 0.3), (3.011, 0.22, 0.25), (4.166, 0.17, 0.18),
             (5.433, 0.12, 0.13), (6.796, 0.09, 0.1), (8.215, 0.06, 0.08), (9.84, 0.04, 0.06), (11.45, 0.03, 0.05)]
    n = ns(dur)
    t = tvec(n)
    y = np.zeros(n)
    for ratio, a, tf in parts:
        f = prime * ratio
        if f > 17000:
            continue
        for _ in range(2):
            fd = f * (1 + U(-0.0012, 0.0012))
            y += a * 0.5 * np.exp(-6.91 * t / (t60 * tf)) * np.sin(2 * np.pi * fd * t + U(0, 6.28))
    y *= np.minimum(t / 0.0008, 1)
    fc, fm = prime * 3.7, prime * 5.2
    idx = 5.0 * np.exp(-t / 0.03)
    clang = np.sin(2 * np.pi * fc * t + idx * np.sin(2 * np.pi * fm * t)) * np.exp(-t / 0.07)
    hit = pk(hp(noise(n), 1500)) * np.exp(-t / 0.01)
    y = pk(y) + strike * (0.35 * clang + 0.35 * hit)
    return fade(pk(y), 0.0005, 0.05)


def modal_hit(freqs, t60s, amps, dur, exc_len=0.004, exc_decay=0.0012):
    m = ns(exc_len)
    exc = noise(m) * np.exp(-tvec(m) / exc_decay)
    exc[0] += 3.0
    ir = modal_ir(freqs, t60s, amps, dur)
    return pk(signal.fftconvolve(exc, ir)[:ns(dur)])


def bone_clack(f0=None, t60=None):
    f0 = f0 or U(700, 1500)
    t60 = t60 or U(0.03, 0.07)
    ratios = np.array([1, 1.58 + U(-.05, .05), 2.41 + U(-.08, .08), 3.53 + U(-.1, .1), 4.9])
    fr = np.concatenate([f0 * ratios, [f0 * U(0.28, 0.4)]])
    t6 = np.concatenate([t60 * np.array([1, .8, .6, .45, .3]), [t60 * 1.4]])
    am = np.array([1, .7, .5, .35, .2, .6])
    return modal_hit(fr, t6, am, t60 * 2 + 0.02, exc_len=0.0015, exc_decay=0.0004)


def stone_knock(scale=1.0, t60=0.12):
    fr = np.array([170, 290, 455, 640, 980, 1460, 2100]) * scale * U(0.95, 1.05)
    t6 = t60 * np.array([1, .9, .75, .6, .45, .35, .25])
    am = np.array([1, .8, .6, .45, .3, .2, .12])
    return modal_hit(fr, t6, am, t60 * 1.6 + 0.02, exc_len=0.006, exc_decay=0.0015)


def gravel(dur, count, spread=0.03, f_lo=900, f_hi=5000, low_frac=0.25, decay_mul=1.0, start=0.0):
    out = np.zeros(ns(dur))
    for _ in range(count):
        at = start + RNG.gamma(1.4, spread)
        if at > dur - 0.03:
            continue
        if RNG.random() < low_frac:
            g = res_grain(U(180, 650), U(2, 5), U(0.008, 0.02) * decay_mul, noise_len=0.001) * U(0.3, 0.9)
        else:
            g = res_grain(U(f_lo, f_hi), U(3, 10), U(0.002, 0.008) * decay_mul, noise_len=0.0004) * U(0.15, 1.0)
        place(out, g * np.exp(-(at - start) / (spread * 4 + 0.05)), at)
    return pk(out)


def stone_crack(dur=1.2, size=1.0):
    n = ns(dur)
    t = tvec(n)
    out = np.zeros(n)
    place(out, pk(hp(noise(ns(0.004)), 600)) * np.exp(-tvec(ns(0.004)) / 0.001), 0)
    for i in range(int(5 + 3 * size)):
        at = RNG.exponential(0.02)
        place(out, res_grain(U(1200, 4500), U(1.2, 3), U(0.001, 0.004), noise_len=0.0006) * U(0.4, 1.0), at)
    for at in scatter_times(dur, [(0, 900 * size), (0.08, 400 * size), (0.4, 40), (dur, 0)]):
        place(out, res_grain(U(700, 6000), U(1.5, 6), U(0.0006, 0.003), noise_len=0.0003) * U(0.05, 0.6) * np.exp(-at / 0.25), at)
    rumble = pk(lp(cnoise(n, 2.0), 140, 2)) * perc(n, 0.02, 0.9 * size)
    th = thump(dur, 95, 32, pdecay=0.05, t60=0.5 * size, click=0.2, body=0.6, sat=1.8)
    return pk(pk(out) + 0.7 * rumble + 0.8 * th)


def grind(dur, f_pts, amp_pts, density=250, rough=0.8, rumble=0.4):
    n = ns(dur)
    f = env_pts(n, f_pts)
    a = env_pts(n, amp_pts)
    x = noise(n)
    am = np.clip(1 + rough * srand(n, 35), 0, None)
    base = (pk(tvf(x, f, 1.8)) + 0.5 * pk(tvf(x, f * 2.3, 2.5))) * am
    ticks = np.zeros(n)
    amax = max(v for _, v in amp_pts) + 1e-9
    dens = [(tt_, density * v / amax) for tt_, v in amp_pts]
    for at in scatter_times(dur, dens):
        place(ticks, res_grain(U(600, 4000), U(2, 8), U(0.001, 0.005)) * U(0.1, 1.0), at)
    rum = pk(lp(cnoise(n, 2.0), 130, 2))
    y = pk(base) * 0.7 + pk(ticks) * 0.6 + rumble * rum
    return fade(pk(y) * a, 0.005, 0.02)


def creak(dur, rate_pts, amp_pts, modes=(480, 760, 1150, 1700, 2450), t60=0.03, scale=1.0, jitter=0.25):
    """Stick-slip friction creak exciting wooden modes."""
    n = ns(dur)
    rate = env_pts(n, rate_pts) * np.clip(1 + jitter * srand(n, 25), 0.2, None)
    ph = np.cumsum(rate) / SR
    idx = np.nonzero(np.diff(np.floor(ph)) > 0)[0]
    imp = np.zeros(n)
    imp[idx] = U(0.4, 1.0, len(idx))
    imp *= env_pts(n, amp_pts)
    fr = np.array(modes) * scale * U(0.96, 1.04, len(modes))
    ir = modal_ir(fr, t60 * np.linspace(1, 0.5, len(fr)), np.linspace(1, 0.4, len(fr)), t60 * 3 + 0.01)
    y = signal.fftconvolve(imp, ir)[:n]
    fric = bp(noise(n), 1500, 5000) * uniform_filter1d(np.abs(imp), ns(0.01))
    return fade(pk(pk(y) + 0.3 * pk(fric)), 0.003, 0.02)


def frost(dur, click_pts, tinkle_pts, lo=3000, hi=12000):
    n = ns(dur)
    out = np.zeros(n)
    for at in scatter_times(dur, click_pts):
        place(out, res_grain(U(lo, hi), U(1.5, 5), U(0.0005, 0.002), noise_len=0.0003) * U(0.1, 1.0), at)
    tk = np.zeros(n)
    for at in scatter_times(dur, tinkle_pts):
        place(tk, glass_grain(U(2500, 8000), U(0.06, 0.3)) * U(0.15, 1.0), at)
    return fade(pk(pk(out) + 0.6 * pk(tk)), 0.002, 0.02)


def shatter(dur=1.0, count=70):
    n = ns(dur)
    t = tvec(n)
    out = pk(hp(noise(n), 2500)) * perc(n, 0.0008, 0.08) * 0.8
    for _ in range(count):
        at = min(RNG.exponential(0.1), dur - 0.05)
        place(out, glass_grain(U(1800, 7500), U(0.08, 0.5)) * U(0.15, 1.0) * np.exp(-at / 0.3), at)
    for _ in range(5):
        place(out, glass_grain(U(900, 1700), U(0.3, 0.8)) * U(0.4, 0.8), U(0, 0.02))
    return fade(pk(out), 0.0005, 0.03)


def ash(dur, amp_pts, dens_pts, lp_pts):
    n = ns(dur)
    hiss = tvf(hp(noise(n), 1200), env_pts(n, lp_pts), 0.7, "lp") * np.clip(1 + 0.3 * srand(n, 10), 0, None)
    cr = np.zeros(n)
    for at in scatter_times(dur, dens_pts):
        place(cr, res_grain(U(1500, 7000), U(1, 3), U(0.0006, 0.003), noise_len=0.0003) * U(0.05, 0.5), at)
    y = pk(hiss) * 0.6 + pk(cr) * 0.7
    return fade(pk(y) * env_pts(n, amp_pts), 0.004, 0.03)


def fire(dur, amp_pts, dens_pts, roar=0.35):
    n = ns(dur)
    cr = np.zeros(n)
    for at in scatter_times(dur, dens_pts):
        a = min(RNG.pareto(2.5) * 0.3 + 0.1, 1.0)
        place(cr, res_grain(U(900, 5500), U(1, 4), U(0.0008, 0.004), noise_len=0.0005) * a, at)
        if RNG.random() < 0.08:   # ember
            place(cr, res_grain(U(4500, 9000), U(6, 12), U(0.004, 0.01)) * a * 0.4, at + U(0.01, 0.2))
    hiss = pk(bp(noise(n), 2000, 9000)) * np.clip(1 + 0.5 * srand(n, 12), 0, None)
    rr = pk(lp(noise(n), 380)) * np.clip(1 + 0.6 * srand(n, 6), 0, None)
    y = pk(cr) + 0.35 * hiss + roar * rr
    return fade(pk(y) * env_pts(n, amp_pts), 0.003, 0.03)


def smoke_burst(dur=0.6):
    n = ns(dur)
    t = tvec(n)
    fc = 6500 * np.exp(-t / 0.22) + 1200
    y = tvf(noise(n), fc, 0.8) * perc(n, 0.006, 0.45) * np.clip(1 + 0.5 * srand(n, 30), 0, None)
    puff = pk(lp(noise(n), 450)) * perc(n, 0.004, 0.14)
    return fade(pk(pk(y) + 0.5 * puff), 0.001, 0.02)


def shockwave(dur=1.2, size=1.0, f0=95.0):
    n = ns(dur)
    t = tvec(n)
    sub = thump(dur, f0, 33, pdecay=0.08, t60=0.8 * size, click=0.3, body=0.6, sat=1.8)
    blast = pk(tvf(noise(n), 120 + 2900 * np.exp(-t / 0.07), 0.7, "lp")) * perc(n, 0.004, 0.7 * size)
    air = pk(tvf(noise(n), 160 + 800 * np.exp(-t / 0.15), 0.9, "bp")) * perc(n, 0.01, 0.5 * size)
    return fade(pk(sub + 0.7 * blast + 0.35 * air), 0.0005, 0.03)


def wind(dur, amp_pts, center=900, whistle=0.12):
    n = ns(dur)
    x = cnoise(n, 1.0)
    fc = center * 1.6 ** np.clip(0.7 * srand(n, 0.8), -1.5, 1.5)
    y = pk(tvf(x, fc, 1.2)) + 0.25 * pk(hp(noise(n), 5000)) * np.clip(1 + 0.5 * srand(n, 2), 0, None)
    y += whistle * pk(tvf(x, center * 1.25 * (1 + 0.12 * srand(n, 0.5)), 14))
    return fade(pk(y) * env_pts(n, amp_pts) * np.clip(1 + 0.25 * srand(n, 1.5), 0, None), 0.01, 0.03)


def whisper_cloud(dur, dens_pts, shift=1.0, gmin=0.08, gmax=0.25):
    WV = [[(700, 130), (1220, 140), (2600, 200)], [(500, 120), (1900, 150), (2600, 200)],
          [(320, 100), (2300, 160), (3000, 220)], [(450, 110), (850, 120), (2600, 200)],
          [(350, 100), (700, 120), (2500, 200)]]
    n = ns(dur)
    out = np.zeros(n)
    for at in scatter_times(dur, dens_pts):
        d = U(gmin, gmax)
        m = ns(d)
        x = noise(m)
        sh = shift * U(0.85, 1.25)
        y = np.zeros(m)
        for f, bw in WV[RNG.integers(len(WV))]:
            b, a = _rbj("bp", f * sh, f / (bw * 1.5))
            y += signal.lfilter(b, a, x)
        u = np.linspace(0, 1, m)
        y = pk(y) * np.sin(np.pi * u) ** 1.5
        cons = RNG.integers(3)
        if cons < 2:
            lo, hi = ((4500, 9500), (2000, 5000))[cons]
            c = pk(bp(noise(m), lo, hi)) * np.exp(-u / 0.12) * np.minimum(u / 0.03, 1) * 0.7
            y = y + c
        place(out, y * U(0.3, 1.0), at)
    return fade(pk(out), 0.005, 0.03)


def swirl(dur, f_lo=300, f_hi=3200, rate_pts=((0, 3.0), (1, 14.0)), q=2.5):
    n = ns(dur)
    rp = [(a * dur, b) for a, b in rate_pts]
    ph = 2 * np.pi * np.cumsum(env_pts(n, rp)) / SR
    fc = np.sqrt(f_lo * f_hi) * (f_hi / f_lo) ** (0.5 * np.sin(ph))
    y = tvf(noise(n), fc, q) * (0.6 + 0.4 * np.sin(ph + np.pi / 2))
    return fade(pk(y), 0.005, 0.005)


def tear(dur=0.12, f0=400, f1=9000):
    n = ns(dur)
    u = np.linspace(0, 1, n)
    x = noise(n)
    y = tvf(x, f0 * (f1 / f0) ** u, 1.2) + 0.5 * pk(hp(x, 3000))
    blk = ns(0.003)
    gate = np.repeat(RNG.random(n // blk + 1) > 0.35, blk)[:n].astype(float)
    gate = uniform_filter1d(gate, ns(0.001)) * 0.7 + 0.3
    env = np.minimum(u / 0.04, 1) * (0.6 + 0.4 * u)
    return fade(pk(y * gate * env), 0.001, 0.004)


def demon_voice(dur, f0=46, amp=1.0, pitch_mult=None, ringf=31.0, drive_k=3.0):
    n = ns(dur)
    t = tvec(n)
    env = np.zeros(n)
    keys = []
    tc = 0.0
    while tc < dur:
        L = U(0.12, 0.34)
        keys.append((tc + L * 0.3, "aoue"[RNG.integers(4)]))
        m = ns(L)
        u = np.linspace(0, 1, m)
        e = np.minimum(u / 0.25, 1) * np.clip((1 - u) / 0.35, 0, 1) * U(0.5, 1.0)
        i = ns(tc)
        k = min(m, n - i)
        env[i:i + k] = np.maximum(env[i:i + k], e[:k])
        tc += L * U(0.8, 1.05)
    env = 0.25 + 0.75 * uniform_filter1d(env, ns(0.02))
    pm = np.ones(n) if pitch_mult is None else pitch_mult
    fa = f0 * pm * (1 + 0.09 * srand(n, 14))
    src = blep_saw(fa) + 0.7 * blep_saw(fa * 0.5) + 0.9 * noise(n) * np.clip(1 + 0.6 * srand(n, 25), 0, None)
    y = formant_filter(src, keys, "bass", 0.62 * pm ** 0.6, 1.6)
    rm = np.sin(2 * np.pi * np.cumsum(ringf * pm) / SR)
    y = pk(y)
    y = 0.55 * y * rm + 0.45 * y
    y = drive(pk(y), drive_k)
    y = lp(y, 5000)
    return fade(pk(y) * env * amp, 0.004, 0.03)


def low_drone(dur, freqs, amp_pts, cut=260, wobble=0.004):
    n = ns(dur)
    y = np.zeros(n)
    for f in freqs:
        y += blep_saw(f * (1 + wobble * srand(n, 0.4)))
    y = lp(lp(y, cut, 2), cut * 1.4, 2)
    y = pk(y) + 0.3 * pk(lp(cnoise(n, 2.0), cut * 0.6))
    return fade(pk(y) * env_pts(n, amp_pts), 0.02, 0.05)


# ----------------------------------------------------------------------------
# mastering
# ----------------------------------------------------------------------------
def limiter(x, thr_db=-3.0, win=0.008):
    x = x / (np.max(np.abs(x)) + 1e-12)
    W = ns(win) | 1
    g = np.minimum(1.0, db(thr_db) / np.maximum(np.abs(x), 1e-12))
    g = minimum_filter1d(g, W, mode="nearest")
    g = uniform_filter1d(g, W, mode="nearest")
    return x * g


def gate(x, t0, t1, ramp=0.002, floor=0.0):
    g = np.ones(len(x))
    a, b, r = ns(t0), ns(t1), ns(ramp)
    g[a:b] = floor
    g[a - r:a] = np.linspace(1, floor, r)
    g[b:b + r] = np.linspace(floor, 1, r)
    return x * g


def master(x, total, thr_db=-3.0, tail_fade=0.4):
    x = x[:ns(total)]
    if len(x) < ns(total):
        x = np.pad(x, (0, ns(total) - len(x)))
    x = hp(x, 32, 2)
    x = limiter(x, thr_db)
    x = fade(x, 0.003, 0.0)
    tf = ns(tail_fade)
    x[-tf:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, tf))
    x -= np.mean(x) * 0  # hp already removes DC
    return pk(x) * db(PEAK_DBFS)


# ----------------------------------------------------------------------------
# cues
# ----------------------------------------------------------------------------
CUES = {}


def cue(name, seed):
    def deco(fn):
        def run():
            reseed(seed)
            return fn()
        CUES[name] = run
        return fn
    return deco


@cue("grip_vampire", seed=101)
def grip_vampire():
    BEATS = dict(haul=0.00, hiss=0.55, bite=0.95, drink1=1.20, drink2=1.60, drink3=2.00,
                 release=2.30, settle=2.60, last_beat=2.90)
    CLIP = 3.0
    B = BEATS
    total = CLIP + TAIL
    bus = Bus(total)
    # 0.00 collar haul: cloth whoosh + crinkle + grab
    bus.add(whoosh(0.5, 250, 1300, 420, peak=0.35, q=0.8, flutter=0.4), B["haul"], 0.5, send=0.25)
    bus.add(rustle(0.45, [(0, 60), (0.12, 220), (0.45, 5)]), B["haul"], 0.35, send=0.15)
    bus.add(thump(0.3, 90, 50, t60=0.12, click=0.15, body=0.8, sat=1.2), B["haul"] + 0.03, 0.3, send=0.1)
    # 0.55 low breath / hiss
    n = ns(0.6)
    t = tvec(n)
    hz = noise(n)
    hiss = pk(bp(hz, 3000, 8500)) + 0.5 * pk(tvf(hz, 1700, 3)) + 0.3 * pk(tvf(hz, 2700, 4))
    hiss *= env_pts(n, [(0, 0), (0.06, 1), (0.3, 0.8), (0.6, 0)]) * np.clip(1 + 0.25 * srand(n, 12), 0, None)
    breath = growl(0.6, [(0, 85), (0.6, 75)], [(0, "o"), (0.3, "a")], [(0, 0), (0.08, 1), (0.6, 0)],
                   register="bass", shift=0.9, bw_mul=3, noise_mix=0.9, rough=0.4, drive_k=1.5)
    bus.add(reverse_swell(pk(lp(noise(ns(0.15)), 1500)) * np.hanning(ns(0.15)), length=0.2), B["hiss"] - 0.2, 0.12)
    bus.add(pk(hiss), B["hiss"], 0.32, send=0.35)
    bus.add(breath, B["hiss"], 0.25, send=0.3)
    # 0.95 bite: bat burst + dark string sting + sub + fang glint
    bats = bat_swarm(total, B["bite"], n_bats=28, spread=0.05, disperse=B["release"], disperse_len=0.9)
    duck = np.ones(len(bats))
    for key in ("drink1", "drink2", "drink3"):     # sidechain: bats tuck under each heartbeat
        tt = tvec(len(bats)) - B[key]
        duck *= 1 - 0.6 * np.where(tt > -0.02, np.exp(-np.maximum(tt, 0) / 0.25), 0) * np.clip((tt + 0.02) / 0.02, 0, 1)
    bus.add(bats * duck, 0, 0.5, send=0.3)
    bus.add(whoosh(0.35, 300, 1700, 380, peak=0.1, q=0.9, flutter=0.5), B["bite"] - 0.03, 0.55, send=0.3)
    sting_notes = [73.42, 77.78, 110.0, 116.54, 155.56, 233.08]
    st = strings(sting_notes, 2.4, [(0, 0), (0.04, 1), (0.5, 0.45), (1.3, 0.25), (2.4, 0)],
                 [(0, 300), (0.05, 2600), (0.6, 900), (2.4, 400)])
    bus.add(st, B["bite"], 0.55, send=0.5)
    bus.add(reverse_swell(st[:ns(0.25)], length=0.45), B["bite"] - 0.45, 0.22)
    bus.add(thump(0.9, 95, 32, t60=0.55, click=0.5, body=0.5), B["bite"], 0.85, send=0.2)
    bus.add(glass_grain(3150, 0.5), B["bite"], 0.18, send=0.5)
    # seductive dark 'oo' pad under the drinking
    pad = choir([293.66, 349.23, 440.0], 1.8, [(0, "u"), (1.0, "o"), (1.8, "u")],
                [(0, 0), (0.4, 1), (1.2, 0.8), (1.8, 0)], register="soprano", breath=0.25)
    bus.add(pad, B["bite"] + 0.1, 0.09, send=0.7)
    # drink pulses: heartbeat slowing / weakening, ethereal shimmer each
    for i, key in enumerate(["drink1", "drink2", "drink3"]):
        s = [1.0, 0.72, 0.5][i]
        hb = heartbeat(gap=[0.26, 0.31, 0.37][i], muff=[230, 200, 170][i])
        bus.add(hb, B[key], 0.95 * s, send=0.15)
        bus.add(reverse_swell(hb, length=0.3), B[key] - 0.3, 0.18 * s)
        bus.add(shimmer(0.75, base=1500 + 250 * i, t60=0.6), B[key] + 0.02, 0.16 * s, send=0.7)
    # release + settle + final heartbeat
    bus.add(whoosh(0.35, 900, 600, 200, peak=0.2, q=0.8, flutter=0.4), B["release"], 0.3, send=0.3)
    bus.add(rustle(0.3, [(0, 150), (0.3, 0)]), B["release"], 0.2)
    bus.add(thump(0.5, 85, 40, t60=0.25, click=0.25, body=0.9, sat=1.4), B["settle"], 0.6, send=0.25)
    bus.add(rustle(0.35, [(0, 200), (0.35, 0)], bright=0.8), B["settle"], 0.25, send=0.15)
    bus.add(gravel(0.4, 12, spread=0.02, low_frac=0.4), B["settle"] + 0.01, 0.1)
    bus.add(heartbeat(muff=150, lub_only=True), B["last_beat"], 0.3, send=0.2)
    bus.add(low_drone(3.2, [36.71, 55.0, 77.78], [(0, 0), (0.5, 0.6), (2.0, 1.0), (3.2, 0)], cut=200),
            0.5, 0.12, send=0.2)
    mix = bus.mix()
    return dict(audio=master(mix, total), beats=BEATS, clip=CLIP,
                checks=["bite", "drink1", "drink2", "drink3", "settle"],
                description="Vampire grip: collar-haul cloth whoosh, low hiss, bite = bat-wing burst + dark "
                            "string sting, three slowing muffled heartbeats with ethereal shimmer, release, "
                            "body settles, bats disperse, final heartbeat stops.")


@cue("grip_ghoul", seed=202)
def grip_ghoul():
    BEATS = dict(crack=0.15, spikes_start=0.30, spikes_end=0.90, growl_start=0.90,
                 lunge1=1.20, lunge2=1.80, lunge3=2.40, lunge4=2.90, growl_end=3.20, crumble=3.30)
    CLIP = 3.5
    B = BEATS
    total = CLIP + TAIL
    bus = Bus(total)
    # stone floor cracking
    bus.add(stone_crack(1.3, 1.0), B["crack"], 0.9, send=0.35)
    # bone spikes rising
    sp_times = np.linspace(B["spikes_start"], B["spikes_end"] - 0.04, 7) + U(-0.02, 0.02, 7)
    for i, ts in enumerate(sp_times):
        big = 1.0 + 0.6 * (i == len(sp_times) - 1)
        for j in range(RNG.integers(2, 5)):
            bus.add(bone_clack(U(650, 1400) * (0.9 + 0.03 * i)), ts + j * U(0.008, 0.02), 0.32 * big * U(0.6, 1), send=0.3)
        bus.add(grind(0.14, [(0, 300), (0.14, 1300)], [(0, 0), (0.1, 1), (0.14, 0)], density=500), ts - 0.1, 0.18)
    bus.add(grind(0.75, [(0, 220), (0.7, 1400)], [(0, 0), (0.5, 0.8), (0.7, 1), (0.75, 0)], density=300),
            B["spikes_start"] - 0.05, 0.3, send=0.25)
    bus.add(thump(0.5, 80, 35, t60=0.3, click=0.2), B["spikes_end"], 0.45, send=0.2)
    # guttural growl bed with surges at the lunges
    gdur = B["growl_end"] - B["growl_start"] + 0.25
    lunges = [B["lunge1"], B["lunge2"], B["lunge3"], B["lunge4"]]
    amp = [(0, 0), (0.15, 0.6)]
    for L in lunges:
        r = L - B["growl_start"]
        amp += [(r - 0.12, 0.55), (r, 1.0), (r + 0.18, 0.6)]
    amp += [(gdur - 0.25, 0.5), (gdur, 0)]
    f0 = [(0, 68)] + [(L - B["growl_start"], 84) for L in lunges] + [(gdur, 58)]
    vow = [(i * 0.3, "oau"[RNG.integers(3)]) for i in range(int(gdur / 0.3) + 1)]
    bus.add(growl(gdur, f0, vow, amp, shift=0.72, bw_mul=2.2, noise_mix=0.55, rough=0.8, drive_k=2.5, irregular=0.35),
            B["growl_start"], 0.55, send=0.3)
    # feeding lunges: stone/gravel crunch, hollow knock, sub
    for i, L in enumerate(lunges):
        sc = U(0.9, 1.1)
        bus.add(whoosh(0.16, 250, 900, 500, peak=0.9, q=0.9), L - 0.15, 0.25)
        bus.add(thump(0.45, 100 * sc, 38, t60=0.25, click=0.4, body=0.7), L, 0.7, send=0.2)
        bus.add(gravel(0.4, 110, spread=0.025, low_frac=0.3), L, 0.55, send=0.25)
        bus.add(stone_knock(sc, 0.13), L, 0.5, send=0.3)
        bus.add(growl(0.25, [(0, 110), (0.25, 90)], "a", [(0, 0), (0.01, 1), (0.25, 0)], shift=0.8,
                      noise_mix=0.6, drive_k=3), L, 0.3, send=0.2)
    # sickly drone
    dr = low_drone(3.4, [82.41, 87.31, 116.54], [(0, 0), (0.6, 1), (2.9, 1), (3.4, 0)], cut=420, wobble=0.012)
    n = ns(3.4)
    sick = pk(tvf(cnoise(n, 1.0), 1750 * (1 + 0.1 * srand(n, 0.6)), 16)) * env_pts(n, [(0, 0), (0.8, 1), (3.0, 1), (3.4, 0)])
    bus.add(dr, 0.5, 0.2, send=0.2)
    bus.add(sick, 0.5, 0.05, send=0.4)
    # cage crumbles to dust, cracks grind shut
    C = B["crumble"]
    for at in scatter_times(0.6, [(0, 160), (0.15, 90), (0.6, 0)]):
        bus.add(bone_clack(U(500, 1300) * (1 - 0.4 * at)), C + at, U(0.1, 0.32) * np.exp(-at / 0.3), send=0.3)
    bus.add(gravel(0.9, 200, spread=0.08, low_frac=0.35), C, 0.45, send=0.3)
    bus.add(ash(1.0, [(0, 0), (0.05, 1), (1.0, 0)], [(0, 300), (1.0, 0)], [(0, 9000), (1.0, 2500)]), C, 0.3, send=0.3)
    bus.add(thump(0.6, 80, 34, t60=0.35, click=0.3, body=0.8), C, 0.55, send=0.2)
    bus.add(grind(0.55, [(0, 900), (0.55, 200)], [(0, 0.3), (0.1, 1), (0.5, 0.6), (0.55, 0)], density=200),
            C + 0.05, 0.3, send=0.2)
    bus.add(stone_knock(0.7, 0.18), C + 0.58, 0.35, send=0.3)
    bus.add(thump(0.4, 70, 32, t60=0.25, click=0.15), C + 0.58, 0.4)
    mix = bus.mix()
    return dict(audio=master(mix, total), beats=BEATS, clip=CLIP,
                checks=["crack", "lunge1", "lunge2", "lunge3", "lunge4", "crumble"],
                description="Ghoul grip: stone floor cracks, bone spikes clack/grind up, irregular guttural "
                            "growl bed with four stone/gravel crunch lunges over a sickly drone, bone cage "
                            "crumbles to dust and cracks grind shut.")


@cue("grip_werewolf", seed=303)
def grip_werewolf():
    BEATS = dict(snarl=0.10, pounce=0.40, swipe1=0.65, swipe2=0.95, swipe3=1.25,
                 shake_start=1.60, shake_end=2.00, howl=2.10, howl_end=2.75)
    CLIP = 2.8
    B = BEATS
    total = CLIP + TAIL
    bus = Bus(total)
    bus.add(growl(0.38, [(0, 125), (0.08, 160), (0.38, 110)], [(0, "u"), (0.07, "a"), (0.38, "a")],
                  [(0, 0), (0.012, 1), (0.25, 0.8), (0.38, 0)], shift=0.95, bw_mul=1.6, noise_mix=0.45,
                  rough=0.9, drive_k=3.5), B["snarl"], 0.75, send=0.25)
    bus.add(pk(hp(noise(ns(0.3)), 2500)) * perc(ns(0.3), 0.01, 0.25), B["snarl"], 0.12)
    # pounce / pin
    bus.add(whoosh(0.22, 200, 800, 300, peak=0.9, q=0.8), B["pounce"] - 0.2, 0.35)
    bus.add(thump(0.7, 115, 34, t60=0.4, click=0.5, body=0.9), B["pounce"], 1.0, send=0.25)
    bus.add(rustle(0.3, [(0, 260), (0.3, 0)], bright=0.8), B["pounce"], 0.3)
    bus.add(gravel(0.4, 40, spread=0.03, low_frac=0.4), B["pounce"] + 0.005, 0.25, send=0.2)
    # three claw swipes
    for i, key in enumerate(["swipe1", "swipe2", "swipe3"]):
        T = B[key]
        sc = [1.0, 1.08, 0.94][i]
        bus.add(whoosh(0.17, 900 * sc, 5200 * sc, 2400, peak=0.88, q=1.6, shape=2.5), T - 0.15, 0.55, send=0.2)
        for c in range(4):
            m = ns(0.09)
            tt = tvec(m)
            x = noise(m) * perc(m, 0.001, 0.07)
            y = np.zeros(m)
            for _ in range(3):
                f = U(2200, 7000) * sc
                y += tvf(x, f * (1 - 0.15 * tt / 0.09), U(12, 25))
            y = pk(y) + 0.4 * pk(bp(x, 1500, 6000))
            bus.add(y, T + c * 0.007, 0.22, send=0.3)
        bus.add(gravel(0.1, 50, spread=0.01, f_lo=1500, f_hi=6000, low_frac=0.0), T, 0.18)
        bus.add(thump(0.35, 95, 40, t60=0.18, click=0.25, body=0.8, body_lp=250), T + 0.004, 0.55)
        bus.add(growl(0.18, [(0, 105), (0.18, 95)], "a", [(0, 0), (0.015, 1), (0.18, 0)], shift=0.9,
                      noise_mix=0.5, drive_k=3), T - 0.03, 0.3, send=0.2)
    # violent shaking growl
    sdur = B["shake_end"] - B["shake_start"] + 0.12
    bus.add(growl(sdur, [(0, 100), (0.2, 135), (sdur, 105)], [(0, "a"), (0.2, "o"), (0.35, "a")],
                  [(0, 0), (0.03, 1), (sdur - 0.1, 0.9), (sdur, 0)], shift=0.9, bw_mul=1.8, noise_mix=0.45,
                  rough=1.0, drive_k=4, shake=(9.0, 0.8)), B["shake_start"], 0.75, send=0.25)
    k = 0
    for ts in np.arange(B["shake_start"], B["shake_end"], 1 / 9.0):
        bus.add(thump(0.2, 80, 45, t60=0.08, click=0.1, body=0.6), ts, 0.18)
        bus.add(rustle(0.1, [(0, 400), (0.1, 0)]), ts, 0.15)
        k += 1
    # shockwave + howl + dust
    H = B["howl"]
    bus.add(shockwave(1.3, 1.0), H, 0.9, send=0.3)
    bus.add(ash(1.0, [(0, 0), (0.05, 1), (1.0, 0)], [(0, 200), (1.0, 0)], [(0, 8000), (1.0, 2000)]), H + 0.03, 0.22, send=0.2)
    bus.add(gravel(0.8, 80, spread=0.06, low_frac=0.4), H + 0.02, 0.2, send=0.3)
    hd = 1.05
    hw = howl(hd, [(0, 400), (0.08, 430), (0.33, 700), (0.62, 690), (0.92, 500), (hd, 470)],
              [(0, 0), (0.12, 0.85), (0.35, 1), (0.65, 0.95), (0.9, 0.5), (hd, 0)],
              [(0, 0.0), (0.3, 0.004), (0.5, 0.012), (hd, 0.016)],
              [(0, 1.6), (0.35, 0.95), (0.65, 1.0), (hd, 1.5)], breath=0.22)
    bus.add(hw, H + 0.02, 0.6, send=0.55)
    hw2 = howl(hd, [(0, 395), (0.08, 425), (0.33, 692), (0.62, 683), (0.92, 494), (hd, 465)],
               [(0, 0), (0.15, 0.7), (0.35, 1), (0.65, 0.9), (0.9, 0.4), (hd, 0)],
               [(0, 0.0), (0.3, 0.005), (0.5, 0.012), (hd, 0.015)],
               [(0, 1.7), (0.35, 1.1), (0.65, 1.1), (hd, 1.6)], breath=0.3)
    bus.add(hw2, H + 0.035, 0.25, send=0.6)
    mix = bus.mix()
    return dict(audio=master(mix, total), beats=BEATS, clip=CLIP,
                checks=["snarl", "pounce", "swipe1", "swipe2", "swipe3", "howl"],
                description="Werewolf grip: formant snarl, heavy pounce pin, three claw swipes (air rip + "
                            "metallic rake + dull thump), violent shaking growl, shockwave whoomp and a full "
                            "rising/falling formant wolf howl with dust and reverb tail.")


@cue("grip_wraith", seed=404)
def grip_wraith():
    BEATS = dict(frost=0.00, frost_end=0.50, palm=0.60, pull_start=0.70, pull_end=2.20, yank=2.25,
                 swirl_start=2.40, swirl_end=2.80, pulse=2.85)
    CLIP = 3.0
    B = BEATS
    total = CLIP + TAIL
    bus = Bus(total)
    # frost spreads, room goes cold
    bus.add(frost(0.65, [(0, 40), (0.3, 320), (0.5, 220), (0.65, 0)], [(0, 4), (0.4, 22), (0.65, 0)]),
            B["frost"], 0.32, send=0.45)
    bus.add(wind(total, [(0, 0), (0.4, 0.8), (1.0, 0.5), (2.2, 0.7), (2.3, 0.15), (2.85, 0.4), (total, 0.1)],
                 center=850, whistle=0.15), 0, 0.2, send=0.3)
    # palm strike: cold thump + glassy chime
    bus.add(lp(thump(0.5, 90, 40, t60=0.25, click=0.3, body=0.9), 600), B["palm"], 0.8, send=0.2)
    chime = modal_hit(1318.5 * np.array([1, 1.004, 2.756, 2.77, 5.404, 8.933]), [1.4, 1.3, 0.9, 0.85, 0.5, 0.3],
                      [1, 0.8, 0.5, 0.4, 0.25, 0.12], 1.8)
    bus.add(chime, B["palm"], 0.3, send=0.6)
    bus.add(frost(0.3, [(0, 600), (0.3, 0)], [(0, 30), (0.3, 0)]), B["palm"], 0.25, send=0.4)
    # soul being pulled out
    P0, P1 = B["pull_start"], B["pull_end"]
    pd = B["yank"] - P0 + 0.02
    n = ns(pd)
    u = np.linspace(0, 1, n)
    pm = 2 ** ((5 * u ** 1.6) / 12)                     # rises a fourth, accelerating
    amp = [(0, 0), (0.3, 0.45), (pd * 0.8, 0.9), (pd - 0.09, 1.0), (pd - 0.055, 0.35), (pd - 0.02, 0.3), (pd, 0)]  # pre-yank dip
    ch = choir([293.66, 311.13, 440.0], pd, [(0, "u"), (pd * 0.6, "o"), (pd, "a")], amp,
               register="alto", pitch_mult=pm, breath=0.3, vib=0.008)
    bus.add(ch, P0, 0.4, send=0.6)
    bt = np.zeros(n)
    beat = 1.0 + 8.0 * u ** 1.5
    for base in (110.0, 165.0, 220.0, 330.0):
        f = base * pm
        bt += blep_saw(f) + blep_saw(f + beat)
    bt = lp(pk(bt), 1600) * env_pts(n, amp)
    bus.add(pk(bt) * env_pts(n, amp), P0, 0.16, send=0.4)
    bus.add(whisper_cloud(pd, [(0, 4), (pd * 0.7, 26), (pd, 40)], shift=1.0), P0, 0.3, send=0.5)
    ten = pk(tvf(noise(n), 700 * (3.5 ** u), 8)) * u ** 1.5
    rum = pk(tvf(cnoise(n, 2.0), 80 + 320 * u, 0.7, "lp")) * u
    bus.add(ten, P0, 0.12, send=0.4)
    bus.add(rum, P0, 0.35)
    # yank: tearing whoosh, then a silence gap
    bus.add(tear(0.09), B["yank"], 2.0, send=0.15)
    bus.add(thump(0.25, 120, 60, t60=0.1, click=0.6, body=0.2), B["yank"], 0.5)
    # swirl into the fist: reverse reverb + accelerating swirl
    sw_len = B["pulse"] - B["swirl_start"]
    src = whisper_cloud(0.3, [(0, 60), (0.3, 0)]) + choir([587.33, 622.25], 0.3, "a", [(0, 1), (0.3, 0)], "alto")
    bus.add(reverse_swell(src, "hall", sw_len), B["pulse"] - sw_len, 0.55)
    bus.add(swirl(sw_len, 300, 4000, ((0, 3.0), (1, 16.0))) * np.linspace(0.1, 1, ns(sw_len)) ** 1.5,
            B["swirl_start"], 0.3, send=0.3)
    # cold pulse + frost shatter + ghostly tail
    bus.add(thump(0.8, 85, 34, t60=0.45, click=0.4, body=0.6), B["pulse"], 0.9, send=0.25)
    bus.add(shatter(1.0, 80), B["pulse"], 0.45, send=0.5)
    bus.add(frost(0.6, [(0, 500), (0.6, 0)], [(0, 40), (0.6, 0)]), B["pulse"], 0.25, send=0.4)
    bus.add(choir([293.66, 440.0, 466.16], 1.1, "u", [(0, 0), (0.15, 1), (1.1, 0)], "soprano", breath=0.4),
            B["pulse"] + 0.05, 0.12, send=0.8)
    bus.add(whisper_cloud(1.0, [(0, 12), (1.0, 0)]), B["pulse"] + 0.1, 0.12, send=0.7)
    mix = bus.mix()
    gs, ge = B["yank"] + 0.09, B["swirl_start"]
    mix = gate(mix, gs, ge, ramp=0.004, floor=0.02)
    return dict(audio=master(mix, total, thr_db=-5.5), beats=BEATS, clip=CLIP,
                checks=["palm", "yank", "pulse"],
                description="Wraith grip: frost crackles spread with icy wind, cold palm thump + glass chime, "
                            "rising detuned ghost-choir/whisper soul pull, spectral tearing yank into a silence "
                            "gap, reverse-reverb swirl into the fist, cold pulse with frost shattering.")


@cue("grip_priest", seed=505)
def grip_priest():
    BEATS = dict(kneel=0.00, kneel_end=0.50, cross=0.60, cross_full=0.90, demon_start=0.90,
                 spasm1=1.10, spasm2=1.60, spasm3=2.00, demon_end=2.40, bell=2.45)
    CLIP = 3.2
    B = BEATS
    total = CLIP + TAIL
    bus = Bus(total)
    R = "cathedral"
    bus.add(rustle(0.55, [(0, 80), (0.2, 260), (0.5, 40), (0.55, 0)], bright=0.85), B["kneel"], 0.35, send=0.2, rev=R)
    bus.add(thump(0.35, 80, 45, t60=0.12, click=0.15, body=0.8), 0.36, 0.3, send=0.15, rev=R)
    # holy cross forming: bright choir + gold sparkle
    hd = B["bell"] - B["cross"] + 0.5
    amp = [(0, 0), (0.3, 1.0), (0.5, 0.75)]
    for k in ("spasm1", "spasm2", "spasm3"):
        r = B[k] - B["cross"]
        amp += [(r - 0.02, 0.7), (r + 0.05, 0.4), (r + 0.3, 0.7)]
    amp += [(B["bell"] - B["cross"], 0.75), (B["bell"] - B["cross"] + 0.08, 1.0), (hd, 0)]
    holy = choir([293.66, 369.99, 440.0, 587.33, 739.99], hd, [(0, "o"), (0.3, "a")], amp,
                 register="soprano", voices=3, breath=0.15, vib=0.005)
    bus.add(holy, B["cross"], 0.42, send=0.6, rev=R)
    org = np.zeros(ns(hd))
    t = tvec(ns(hd))
    for f in (146.83, 220.0, 293.66, 440.0, 587.33, 880.0, 1174.66):
        org += np.sin(2 * np.pi * f * t + U(0, 6.28)) * (146.83 / f) ** 0.5 * (1 + 0.15 * np.sin(2 * np.pi * U(4, 6) * t))
    bus.add(pk(org) * env_pts(ns(hd), amp), B["cross"], 0.12, send=0.5, rev=R)
    gd = B["cross_full"] - B["cross"] + 0.5
    gold = np.zeros(ns(gd))
    for at in scatter_times(gd, [(0, 20), (0.3, 70), (gd, 5)]):
        f = 1800 * 2 ** (at / gd * 2.0) * U(0.9, 1.15)
        place(gold, glass_grain(f, U(0.1, 0.35)) * U(0.2, 1), at)
    bus.add(pk(gold), B["cross"], 0.22, send=0.6, rev=R)
    bus.add(shimmer(1.0, base=2400, t60=0.8, att=0.25), B["cross"], 0.12, send=0.7, rev=R)
    # demonic voice fighting back, then tearing upward and burning out
    D0 = B["demon_start"]
    dd = B["bell"] - D0 + 0.55
    n = ns(dd)
    tt = tvec(n) + D0
    pm = np.where(tt < B["bell"], 1.0, 2 ** (np.clip(tt - B["bell"], 0, None) / 0.5 * 2.0))
    dam = np.interp(tt, [D0, D0 + 0.12, B["bell"] - 0.02, B["bell"] + 0.08, B["bell"] + 0.5, D0 + dd],
                    [0, 0.85, 1.0, 1.0, 0.0, 0.0])
    dv = demon_voice(dd, 46, pitch_mult=pm) * dam
    bus.add(dv, D0, 0.65, send=0.35, rev=R)
    for k in ("spasm1", "spasm2", "spasm3"):
        T = B[k]
        bus.add(thump(0.5, 100, 36, t60=0.3, click=0.5, body=0.8), T, 0.8, send=0.25, rev=R)
        bus.add(stone_knock(U(0.8, 1.0), 0.1), T, 0.35, send=0.3, rev=R)
        bus.add(smoke_burst(0.6), T + 0.005, 0.4, send=0.3, rev=R)
        bus.add(growl(0.3, [(0, 70), (0.3, 55)], "a", [(0, 0), (0.015, 1), (0.3, 0)], shift=0.65,
                      noise_mix=0.6, drive_k=4), T, 0.4, send=0.3, rev=R)
    # final strike: bell + flash + shockwave + fire
    Bl = B["bell"]
    bus.add(bell(196.0, total - Bl, t60=7.0), Bl, 0.9, send=0.45, rev=R)
    bus.add(reverse_swell(pk(hp(noise(ns(0.2)), 3000)) * perc(ns(0.2), 0.001, 0.1), R, 0.35), Bl - 0.35, 0.25)
    bus.add(whoosh(0.5, 9000, 4000, 1800, peak=0.03, q=0.7, low=0.0), Bl, 0.35, send=0.4, rev=R)
    bus.add(shockwave(1.4, 1.1), Bl, 0.75, send=0.3, rev=R)
    bus.add(fire(1.2, [(0, 0), (0.05, 1), (0.5, 0.6), (1.2, 0)], [(0, 250), (0.6, 80), (1.2, 10)], roar=0.4),
            Bl + 0.03, 0.3, send=0.3, rev=R)
    mix = bus.mix()
    return dict(audio=master(mix, total), beats=BEATS, clip=CLIP,
                checks=["spasm1", "spasm2", "spasm3", "bell"],
                description="Priest grip: robe rustle kneel, bright holy choir cross with gold sparkle, a "
                            "distorted ring-modulated demon voice fighting back with three spasm hits and "
                            "ink-smoke hisses, then a huge church bell toll + flash + shockwave as the demon "
                            "voice tears upward and burns out into embers; cathedral tail.")


@cue("grip_human", seed=606)
def grip_human():
    BEATS = dict(knee=0.30, stake=0.60, struggle_start=0.80, struggle_end=1.70, raise_stake=1.80, strike=2.00,
                 ash_end=2.60)
    CLIP = 2.6
    HITSTOP = 0.060
    B = BEATS
    total = CLIP + TAIL
    bus = Bus(total)
    # knee drop
    bus.add(whoosh(0.25, 200, 700, 300, peak=0.9, q=0.8), B["knee"] - 0.23, 0.3)
    bus.add(thump(0.6, 105, 38, t60=0.32, click=0.45, body=0.9), B["knee"], 1.0, send=0.2)
    bus.add(rustle(0.4, [(0, 300), (0.4, 0)], bright=0.8), B["knee"], 0.35, send=0.15)
    bus.add(stone_knock(1.2, 0.08), B["knee"], 0.2)
    # silver glint shing
    bus.add(whoosh(0.09, 2000, 9000, 6000, peak=0.9, q=1.2, low=0.0), B["stake"] - 0.085, 0.35, send=0.3)
    freqs = np.sort(U(2800, 13000, 24))
    shing = modal_hit(freqs, U(0.3, 1.1, 24), U(0.3, 1.0, 24) * (2800 / freqs) ** 0.3, 1.3, exc_len=0.02, exc_decay=0.004)
    bus.add(shing, B["stake"], 0.45, send=0.45)
    bus.add(glass_grain(5274, 0.9), B["stake"] + 0.01, 0.2, send=0.5)
    # struggle: wooden creaks, grip tension, rustles
    S0, S1 = B["struggle_start"], B["struggle_end"]
    for i, ts in enumerate(np.linspace(S0, S1 - 0.25, 5) + U(-0.04, 0.04, 5)):
        d = U(0.15, 0.3)
        bus.add(creak(d, [(0, U(30, 50)), (d * 0.5, U(70, 110)), (d, U(35, 60))], [(0, 0), (0.03, 1), (d - 0.03, 0.8), (d, 0)],
                      scale=U(0.85, 1.2), t60=0.03), ts, 0.75, send=0.25)
    for ts in np.linspace(S0 + 0.1, S1 - 0.1, 3):
        d = 0.18
        bus.add(creak(d, [(0, 140), (d, 220)], [(0, 0), (0.04, 1), (d, 0)], modes=(1250, 1900, 2700, 3600), t60=0.012),
                ts, 0.3, send=0.2)
    sd = S1 - S0 + 0.1
    n = ns(sd)
    tens = pk(tvf(cnoise(n, 1.0), 300 + 500 * np.linspace(0, 1, n), 1.5)) * env_pts(n, [(0, 0), (0.2, 0.6), (sd, 1)])
    tens *= 1 - 0.4 * (0.5 + 0.5 * np.sin(2 * np.pi * 7 * tvec(n)))
    bus.add(tens, S0, 0.25, send=0.2)
    bus.add(rustle(sd, [(0, 50), (0.3, 120), (0.6, 60), (sd, 100)], bright=0.9), S0, 0.45, send=0.15)
    for ts in (S0 + 0.25, S0 + 0.6):
        bus.add(thump(0.25, 80, 45, t60=0.1, click=0.1, body=0.7), ts, 0.35)
    # raise + strike
    bus.add(whoosh(0.3, 300, 1400, 600, peak=0.45, q=0.9, flutter=0.3), B["raise_stake"] - 0.08, 0.4, send=0.2)
    bus.add(whoosh(0.12, 500, 2400, 1200, peak=0.92, q=1.0), B["strike"] - 0.115, 0.4)
    St = B["strike"]
    thock = modal_hit([185, 410, 655, 990, 1430, 2080, 2900], [0.22, 0.15, 0.11, 0.08, 0.06, 0.045, 0.035],
                      [1, .8, .7, .55, .4, .3, .2], 0.5, exc_len=0.003, exc_decay=0.0008)
    bus.add(thock, St, 0.9, send=0.35)
    bus.add(thump(0.9, 125, 34, t60=0.6, click=0.7, body=0.8), St, 1.0, send=0.2)
    bus.add(pk(hp(noise(ns(0.01)), 3000)) * np.exp(-tvec(ns(0.01)) / 0.0015), St, 0.5)
    bus.add(gravel(0.3, 40, spread=0.02, low_frac=0.3), St, 0.2, send=0.3)
    # ash / dust drifting away
    ad = 1.4
    bus.add(ash(ad, [(0, 0), (0.08, 1), (0.6, 0.6), (ad, 0)], [(0, 400), (0.6, 120), (ad, 0)], [(0, 9500), (ad, 1800)]),
            St + 0.05, 0.4, send=0.35)
    bus.add(whoosh(1.0, 1500, 900, 300, peak=0.15, q=0.7, flutter=0.3, low=0.1), St + 0.1, 0.15, send=0.4)
    mix = bus.mix()
    mix = gate(mix, St + 0.028, St + 0.028 + HITSTOP, ramp=0.002)
    return dict(audio=master(mix, total, thr_db=-6.0), beats=dict(BEATS, hitstop_gap=HITSTOP), clip=CLIP,
                checks=["knee", "stake", "strike"],
                description="Human grip: knee drop thud, silver glint shing as the stake appears, wooden "
                            "creaks/grip tension struggle, raise whoosh, deep wooden THOCK with sub hit and a "
                            "60 ms hit-stop silence, ash/dust hiss drifting away.")


@cue("grip_human_monster_ash", seed=607)
def grip_human_monster_ash():
    BEATS = dict(start=0.00, exhale=0.15, crumble_peak=0.25)
    LEN = 1.5
    B = BEATS
    bus = Bus(LEN)
    bus.add(whoosh(0.7, 500, 2600, 800, peak=0.25, q=0.7, flutter=0.3, low=0.15), B["start"], 0.45, send=0.4)
    bus.add(ash(1.3, [(0, 0), (0.06, 0.8), (B["crumble_peak"], 1), (1.3, 0)], [(0, 300), (0.25, 700), (1.3, 0)],
                [(0, 10000), (1.3, 2000)]), B["start"] + 0.02, 0.6, send=0.35)
    bus.add(gravel(1.0, 160, spread=0.1, f_lo=1200, f_hi=6000, low_frac=0.1, decay_mul=0.6), B["start"] + 0.03, 0.25)
    ex = growl(0.85, [(0, 90), (0.85, 70)], [(0, "a"), (0.85, "u")], [(0, 0), (0.2, 1), (0.85, 0)],
               register="tenor", shift=0.8, bw_mul=2.5, noise_mix=0.95, rough=0.2, drive_k=0, irregular=0.1)
    bus.add(ex, B["exhale"], 0.25, send=0.8)
    mix = bus.mix()
    return dict(audio=master(mix, LEN, tail_fade=0.3), beats=BEATS, clip=LEN, checks=[],
                description="Monster-target layer for the human grip: pale whoosh, dry crumbling ash "
                            "disintegration and a faint ghostly exhale.")


@cue("grip_victim_heartbeat", seed=701)
def grip_victim_heartbeat():
    PERIOD = 4.0
    BPM = 75.0          # 5 beats fit the 4.0 s loop exactly (~70 bpm feel)
    GAP = 0.27
    FIRST = 0.06
    BEATS = {f"beat{i + 1}": round(FIRST + i * 60 / BPM, 4) for i in range(5)}
    N = ns(PERIOD)
    one = np.zeros(N)
    benv = np.zeros(N)
    for i, bt in enumerate(BEATS.values()):
        hb = heartbeat(gap=GAP, muff=190, strength=U(0.92, 1.0))
        idx = (ns(bt) + np.arange(len(hb))) % N           # circular placement
        np.add.at(one, idx, hb)
        e = np.exp(-tvec(ns(0.5)) / 0.15)
        np.add.at(benv, (ns(bt) + np.arange(len(e))) % N, e)
    t = tvec(N)
    drone = np.zeros(N)
    for f in (55.0, 58.25, 82.5):                      # integer cycles per 4 s -> periodic
        drone += blep_saw(f * (1 + 0.003 * np.sin(2 * np.pi * 0.25 * t)), N, phase0=0.0)
    rumble = cnoise(N, 2.0)                            # FFT noise is periodic in N
    air = cnoise(N, 1.0)
    tiled = lambda x: np.tile(x, 3)
    d3 = lp(lp(tiled(drone), 220, 2), 300, 2)
    r3 = lp(tiled(rumble), 140, 2) * tiled(1 + 0.3 * np.sin(2 * np.pi * 0.5 * t))
    a3 = bp(tiled(air), 300, 1200) * tiled(0.5 + 0.5 * np.sin(2 * np.pi * 0.25 * t) ** 2)
    duck = tiled(1 - 0.35 * np.clip(benv, 0, 1))
    bed = (0.5 * pk(d3) + 0.4 * pk(r3) + 0.05 * pk(a3)) * duck
    hb3 = tiled(one)
    wet = signal.fftconvolve(hb3 * 0.25 + bed * 0.15, get_ir("room"))[:3 * N]
    x = pk(hb3) * 1.0 + 0.32 * bed + wet * 0.6
    x = hp(x, 28, 2)
    x = limiter(x, -2.5)
    out = pk(x[2 * N:3 * N]) * db(PEAK_DBFS)
    return dict(audio=out, beats=dict(BEATS, bpm=BPM, loop_length=PERIOD), clip=PERIOD, loop=True,
                checks=list(BEATS.keys()),
                description="Seamless 4.0 s loop for the victim's screen: muffled heavy heartbeat (75 bpm, 5 "
                            "beats per loop) over a low dark drone that ducks with each beat.")


@cue("grip_finish_sting", seed=801)
def grip_finish_sting():
    BEATS = dict(hit=0.00)
    LEN = 1.2
    bus = Bus(LEN)
    bus.add(thump(1.2, 115, 36, t60=0.8, click=0.8, body=0.8, sat=2.0), 0, 1.0, send=0.25)
    st = strings([55.0, 58.27, 82.41, 87.31, 110.0, 155.56], 1.2, [(0, 1), (0.08, 0.8), (0.4, 0.4), (1.2, 0)],
                 [(0, 3500), (0.1, 900), (0.5, 350), (1.2, 250)], voices=6, detune=14, bow=0.15)
    bus.add(st, 0, 0.7, send=0.45)
    boom = modal_hit([62, 97, 141, 203, 288, 391, 517], [1.2, 0.9, 0.7, 0.5, 0.4, 0.3, 0.2],
                     [1, .8, .6, .5, .35, .25, .15], 1.2, exc_len=0.01, exc_decay=0.003)
    bus.add(boom, 0, 0.45, send=0.3)
    bus.add(choir([55.0, 82.41, 87.31, 110.0], LEN, [(0, "a"), (0.5, "o")], [(0, 0), (0.015, 1), (0.3, 0.5), (LEN, 0)],
                  register="bass", voices=3, detune=16, breath=0.3, tilt=1800), 0, 0.35, send=0.4)
    bus.add(pk(tvf(noise(ns(0.6)), 100 + 3000 * np.exp(-tvec(ns(0.6)) / 0.05), 0.7, "lp")) * perc(ns(0.6), 0.002, 0.4),
            0, 0.5, send=0.3)
    mix = bus.mix()
    return dict(audio=master(mix, LEN, tail_fade=0.35), beats=BEATS, clip=LEN, checks=[],
                description="Generic dark low kill sting for the gripper's hit-stop: sub boom, low dissonant "
                            "string cluster stab, dark metallic resonance.")


@cue("sub_royal_bats_gold", seed=901)
def sub_royal_bats_gold():
    BEATS = dict(burst=0.00)
    LEN = 1.6
    bus = Bus(LEN)
    bus.add(bat_swarm(LEN, 0.0, n_bats=22, spread=0.04, disperse=0.45, disperse_len=0.6, bright=1.3, chirps=6),
            0, 0.75, send=0.3)
    bus.add(whoosh(0.35, 400, 2400, 600, peak=0.12, q=0.9, flutter=0.5), 0, 0.5, send=0.3)
    sp = np.zeros(ns(LEN))
    notes = [1760.0, 2217.5, 2637.0, 3520.0, 4434.9]
    for at in scatter_times(1.2, [(0, 60), (0.3, 40), (1.2, 0)]):
        place(sp, glass_grain(notes[RNG.integers(5)] * U(0.998, 1.002), U(0.2, 0.6)) * U(0.2, 1), at)
    bus.add(pk(sp), 0.02, 0.3, send=0.6)
    bus.add(shimmer(1.3, base=2200, t60=0.9, att=0.05), 0.0, 0.18, send=0.6)
    bus.add(choir([880.0, 1108.73, 1318.51], 1.3, "a", [(0, 0), (0.15, 1), (1.3, 0)], "soprano", breath=0.3),
            0.0, 0.08, send=0.7)
    mix = bus.mix()
    return dict(audio=master(mix, LEN, tail_fade=0.4), beats=BEATS, clip=LEN, checks=[],
                description="Royal vampire extra: shimmering golden bat-wing burst with bright sparkle.")


@cue("sub_alpha_double_shock", seed=902)
def sub_alpha_double_shock():
    BEATS = dict(shock1=0.00, shock2=0.22)
    LEN = 1.5
    bus = Bus(LEN)
    bus.add(shockwave(1.2, 0.8, f0=100), BEATS["shock1"], 0.75, send=0.3)
    bus.add(shockwave(1.3, 1.2, f0=80), BEATS["shock2"], 1.0, send=0.35)
    bus.add(gravel(1.0, 100, spread=0.06, low_frac=0.4), BEATS["shock1"] + 0.01, 0.25, send=0.3)
    bus.add(gravel(1.0, 140, spread=0.08, low_frac=0.4), BEATS["shock2"] + 0.01, 0.3, send=0.3)
    bus.add(ash(1.2, [(0, 0), (0.05, 1), (1.2, 0)], [(0, 200), (1.2, 0)], [(0, 8000), (1.2, 2000)]),
            BEATS["shock2"], 0.25, send=0.3)
    mix = bus.mix()
    return dict(audio=master(mix, LEN, tail_fade=0.4), beats=BEATS, clip=LEN, checks=["shock2"],
                description="Alpha werewolf extra: two stacked shockwave whoomps with debris and dust.")


@cue("sub_crypt_cage_tall", seed=903)
def sub_crypt_cage_tall():
    BEATS = dict(rise=0.00, top=0.90)
    LEN = 1.8
    bus = Bus(LEN)
    bus.add(grind(1.0, [(0, 120), (0.9, 900)], [(0, 0), (0.7, 0.9), (0.9, 1), (1.0, 0)], density=350, rumble=0.7),
            0, 0.5, send=0.35)
    for i, ts in enumerate(np.linspace(0.05, 0.85, 12) + U(-0.02, 0.02, 12)):
        for j in range(RNG.integers(2, 5)):
            bus.add(bone_clack(U(450, 1000) * (0.85 + 0.04 * i)), ts + j * U(0.008, 0.02), 0.3 * U(0.6, 1), send=0.35)
    bus.add(creak(0.8, [(0, 25), (0.8, 60)], [(0, 0), (0.2, 1), (0.8, 0)], modes=(150, 260, 410, 620), t60=0.05),
            0.1, 0.3, send=0.35)
    for j in range(6):
        bus.add(bone_clack(U(500, 900)), BEATS["top"] + j * 0.012, 0.45, send=0.4)
    bus.add(thump(0.8, 85, 30, t60=0.5, click=0.4, body=0.8), BEATS["top"], 0.9, send=0.3)
    bus.add(gravel(0.6, 80, spread=0.05, low_frac=0.4), BEATS["top"], 0.3, send=0.3)
    mix = bus.mix()
    return dict(audio=master(mix, LEN, tail_fade=0.4), beats=BEATS, clip=LEN, checks=["top"],
                description="Crypt ghoul extra: bigger, deeper bone cage rise with deep grinding and a heavy top-out.")


@cue("sub_hollow_frost_crown", seed=904)
def sub_hollow_frost_crown():
    BEATS = dict(form=0.00, crown=0.70)
    LEN = 1.6
    bus = Bus(LEN)
    bus.add(frost(0.9, [(0, 60), (0.6, 350), (0.9, 0)], [(0, 5), (0.6, 25), (0.9, 0)]), 0, 0.3, send=0.45)
    arp = [1046.5, 1244.5, 1480.0, 1568.0, 2093.0, 2489.0, 2960.0]
    for i, f in enumerate(arp):
        bus.add(glass_grain(f, 0.5), BEATS["crown"] * (i / len(arp)) ** 0.7, 0.18, send=0.6)
    cr = modal_hit(np.array([1046.5, 1050.5, 1108.7, 1480.0, 1484.0, 2093.0, 2960.0]) * np.array([1, 1, 1, 1, 1, 2.756 / 2, 1]),
                   [1.2, 1.1, 1.0, 1.0, 0.9, 0.6, 0.5], [.6, .5, .6, .7, .5, .35, .3], 0.9)
    bus.add(cr, BEATS["crown"], 0.4, send=0.6)
    bus.add(lp(thump(0.4, 90, 45, t60=0.2, click=0.3, body=0.5), 700), BEATS["crown"], 0.4, send=0.3)
    bus.add(wind(LEN, [(0, 0), (0.5, 1), (LEN, 0)], center=1100, whistle=0.06), 0, 0.15, send=0.3)
    bus.add(choir([523.25, 554.37, 739.99], 1.0, "u", [(0, 0), (0.2, 1), (1.0, 0)], "soprano", breath=0.4),
            BEATS["crown"] - 0.1, 0.1, send=0.7)
    mix = bus.mix()
    return dict(audio=master(mix, LEN, tail_fade=0.4), beats=BEATS, clip=LEN, checks=["crown"],
                description="Hollow wraith extra: crystalline frost crown forming - rising glass arpeggio "
                            "converging into an eerie detuned glass chord.")


@cue("sub_pope_twin_bell", seed=905)
def sub_pope_twin_bell():
    BEATS = dict(bell1=0.00, bell2=0.30)
    LEN = 2.0
    bus = Bus(LEN)
    bus.add(bell(220.0, LEN, t60=6.0), BEATS["bell1"], 0.7, send=0.5, rev="cathedral")
    bus.add(bell(330.0, LEN, t60=5.0, strike=0.9), BEATS["bell2"], 0.7, send=0.5, rev="cathedral")
    bus.add(thump(0.6, 90, 40, t60=0.3, click=0.2, body=0.4), BEATS["bell1"], 0.3)
    bus.add(shimmer(1.5, base=2600, t60=1.2, att=0.1), 0.05, 0.08, send=0.6, rev="cathedral")
    mix = bus.mix()
    return dict(audio=master(mix, LEN, tail_fade=0.5), beats=BEATS, clip=LEN, checks=["bell2"],
                description="Pope priest extra: two church bells a perfect fifth apart (A3 then E4) in a cathedral.")


@cue("sub_super_crater", seed=906)
def sub_super_crater():
    BEATS = dict(impact=0.00)
    LEN = 1.6
    bus = Bus(LEN)
    bus.add(stone_crack(1.5, 1.6), 0, 0.8, send=0.3)
    bus.add(thump(1.4, 105, 34, t60=0.9, click=0.8, body=0.9, sat=2.2), 0, 1.0, send=0.25)
    bus.add(shockwave(1.4, 1.2, f0=85), 0.01, 0.6, send=0.3)
    bus.add(gravel(1.4, 320, spread=0.12, low_frac=0.4), 0.02, 0.4, send=0.35)
    bus.add(ash(1.4, [(0, 0), (0.08, 1), (1.4, 0)], [(0, 250), (1.4, 0)], [(0, 8000), (1.4, 1800)]), 0.05, 0.25, send=0.3)
    mix = bus.mix()
    return dict(audio=master(mix, LEN, tail_fade=0.4), beats=BEATS, clip=LEN, checks=[],
                description="Super human extra: ground-crack crater impact with sub boom, shockwave and debris rain.")


# ----------------------------------------------------------------------------
# IO: ogg, png
# ----------------------------------------------------------------------------
def write_ogg(x, path):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1",
                    "-i", "pipe:0", "-c:a", "libvorbis", "-q:a", "8", str(path)],
                   input=x.astype("<f4").tobytes(), check=True)


def read_ogg(path):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(path), "-f", "f32le", "-ac", "1",
                        "-ar", str(SR), "pipe:1"], capture_output=True, check=True)
    return np.frombuffer(p.stdout, dtype="<f4").astype(float)


def write_png(path, rgb):
    h, w, _ = rgb.shape
    raw = b"".join(b"\x00" + rgb[y].tobytes() for y in range(h))

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    Path(path).write_bytes(png)


_CMAP = np.array([[0, 0, 4], [31, 12, 72], [85, 15, 109], [136, 34, 106], [186, 54, 85], [227, 89, 51],
                  [249, 140, 10], [249, 201, 50], [252, 255, 164]], float)


def cmap(v):
    v = np.clip(v, 0, 1) * (len(_CMAP) - 1)
    i = np.minimum(v.astype(int), len(_CMAP) - 2)
    f = (v - i)[..., None]
    return (_CMAP[i] * (1 - f) + _CMAP[i + 1] * f).astype(np.uint8)


def spectrogram_png(x, path, beats, clip):
    W, HS, HW, HT = 1000, 380, 90, 12
    hop = max(32, len(x) // W)
    nfft = 2048
    f, t, Z = signal.stft(x, SR, nperseg=nfft, noverlap=nfft - hop)
    mag = 20 * np.log10(np.abs(Z) + 1e-9)
    top = mag.max()
    v = (mag - (top - 90)) / 90
    rows = np.geomspace(20, 22000, HS)[::-1]
    ri = np.clip(np.searchsorted(f, rows), 0, len(f) - 1)
    ci = np.clip(np.round(np.linspace(0, len(t) - 1, W)).astype(int), 0, len(t) - 1)
    spec = cmap(v[ri][:, ci])
    dur = len(x) / SR
    for fl in (100, 1000, 10000):
        r = int(np.argmin(np.abs(rows - fl)))
        spec[r, ::4] = (90, 90, 90)
    wave = np.full((HW, W, 3), 12, np.uint8)
    edges = np.linspace(0, len(x), W + 1).astype(int)
    for c in range(W):
        seg = x[edges[c]:max(edges[c + 1], edges[c] + 1)]
        lo_, hi_ = seg.min(), seg.max()
        a = int((1 - (hi_ + 1) / 2) * (HW - 1))
        b = int((1 - (lo_ + 1) / 2) * (HW - 1))
        wave[a:b + 1, c] = (120, 200, 255)
    wave[HW // 2, :] = (60, 60, 60)
    ticks = np.zeros((HT, W, 3), np.uint8)
    for s in np.arange(0, dur + 1e-9, 0.1):
        c = min(int(s / dur * (W - 1)), W - 1)
        ticks[: (HT if abs(s * 2 - round(s * 2)) < 1e-6 else HT // 3), c] = (200, 200, 200)
    img = np.concatenate([wave, spec, ticks], axis=0)
    for name, bt in beats.items():
        if not isinstance(bt, (int, float)) or bt > dur or name in ("bpm", "loop_length", "hitstop_gap"):
            continue
        c = min(int(bt / dur * (W - 1)), W - 1)
        img[:HW, c] = (80, 255, 160)
        img[HW:HW + HS:3, c] = (80, 255, 160)
    c = min(int(clip / dur * (W - 1)), W - 1)
    img[:, c] = (255, 60, 60)
    write_png(path, img)


# ----------------------------------------------------------------------------
# checks
# ----------------------------------------------------------------------------
def onset_strength(x):
    hop = 120
    f, t, Z = signal.stft(x, SR, nperseg=512, noverlap=512 - hop)
    S = np.log1p(200 * np.abs(Z) / (np.abs(Z).max() + 1e-12))
    flux = np.maximum(0, np.diff(S, axis=1)).sum(0)
    return t[1:], flux


def check_audio(name, x, info):
    rep = {}
    peak = np.max(np.abs(x))
    rep["len_s"] = round(len(x) / SR, 3)
    rep["peak_dbfs"] = round(20 * np.log10(peak + 1e-12), 2)
    rep["rms_dbfs"] = round(20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12), 2)
    rep["clipped"] = int(np.sum(np.abs(x) >= 0.999))
    rep["dc"] = round(float(np.mean(x)), 6)
    d = np.abs(np.diff(x))
    p99 = np.percentile(d, 99.5)
    if info.get("loop"):
        jump = abs(x[0] - x[-1])
        rep["loop_jump"] = round(float(jump), 5)
        rep["loop_ok"] = bool(jump <= max(p99, 1e-4))
    else:
        rep["start_abs"] = round(float(abs(x[0])), 5)
        rep["end_abs"] = round(float(np.max(np.abs(x[-ns(0.005):]))), 5)
    # spectral richness: 1/3-octave bands within 40 dB of loudest
    F = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2
    fr = np.fft.rfftfreq(len(x), 1 / SR)
    edges = 20 * 2 ** (np.arange(0, 31) / 3)
    be = np.array([F[(fr >= edges[i]) & (fr < edges[i + 1])].sum() for i in range(30)])
    bdb = 10 * np.log10(be + 1e-20)
    rep["bands_40db"] = int(np.sum(bdb > bdb.max() - 40))
    rep["peak_bin_frac"] = round(float(F.max() / F.sum()), 4)
    # beat onsets: (a) energy envelope - steepest rise of a 10 ms RMS envelope (dB) and the jump in level
    # versus the 150 ms before; (b) spectral flux ratio.  Pass if the onset is within 25 ms and either
    # the level jumps >= 4 dB or the flux peak is >= 2x its local baseline.
    xc, off = (np.tile(x, 2), len(x) / SR) if info.get("loop") else (x, 0.0)
    hop = 48
    e = uniform_filter1d(xc ** 2, ns(0.010))[::hop]
    edb = 10 * np.log10(e + 1e-12)
    te = np.arange(len(edb)) * hop / SR
    de = np.gradient(uniform_filter1d(edb, 3))
    t, fl = onset_strength(xc)
    res = {}
    ok = True
    for k in info.get("checks", []):
        b = info["beats"][k] + off
        w = (te >= b - 0.035) & (te <= b + 0.035)
        i = np.argmax(np.where(w, de, -1e9))
        pre = (te >= b - 0.16) & (te <= b - 0.012)
        post = (te >= b) & (te <= b + 0.05)
        jump = edb[post].max() - np.median(edb[pre])
        dt = te[i] - b
        wf = (t >= b - 0.035) & (t <= b + 0.045)
        bf = (t >= b - 0.35) & (t <= b - 0.05)
        j = np.argmax(np.where(wf, fl, -1))
        ratio = fl[j] / (np.median(fl[bf]) + 1e-9)
        good = bool(abs(dt) <= 0.025 and (jump >= 4.0 or (ratio >= 2.0 and abs(t[j] - b) <= 0.025)))
        ok = bool(ok and good)
        res[k] = f"{dt * 1000:+.0f}ms +{jump:.1f}dB flux x{ratio:.1f}{'' if good else ' FAIL'}"
    rep["onsets"] = res
    rep["onsets_ok"] = ok
    return rep


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------
def render(names, previews=True):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PREV_DIR.mkdir(parents=True, exist_ok=True)
    man_path = OUT_DIR / "manifest.json"
    manifest = json.loads(man_path.read_text()) if man_path.exists() else {}
    reports = {}
    for name in names:
        info = CUES[name]()
        x = info["audio"]
        assert len(x) / SR < 20.0
        path = OUT_DIR / f"{name}.ogg"
        write_ogg(x, path)
        dec = read_ogg(path)
        if previews:
            spectrogram_png(dec, PREV_DIR / f"{name}.png", info["beats"], info["clip"])
        manifest[name] = dict(file=f"{name}.ogg", length_s=round(len(dec) / SR, 3),
                              beats={k: v for k, v in info["beats"].items()}, description=info["description"])
        rep = check_audio(name, dec, info)
        rep["src_vs_dec_len"] = len(x) == len(dec)
        reports[name] = rep
        print(name, json.dumps(rep))
    ordered = {k: manifest[k] for k in CUES if k in manifest}
    man_path.write_text(json.dumps(ordered, indent=2))
    return reports


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cues", nargs="*", help="cue names (default: all)")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--no-preview", action="store_true")
    ap.add_argument("--check", action="store_true", help="only check existing .ogg files")
    a = ap.parse_args()
    if a.list:
        print("\n".join(CUES))
        return
    names = a.cues or list(CUES)
    bad = [c for c in names if c not in CUES]
    if bad:
        sys.exit(f"unknown cue(s): {bad}; use --list")
    if a.check:
        man = json.loads((OUT_DIR / "manifest.json").read_text())
        for name in names:
            reseed(0)
            info = CUES[name]()
            dec = read_ogg(OUT_DIR / f"{name}.ogg")
            print(name, json.dumps(check_audio(name, dec, info)))
        return
    render(names, previews=not a.no_preview)


if __name__ == "__main__":
    main()
