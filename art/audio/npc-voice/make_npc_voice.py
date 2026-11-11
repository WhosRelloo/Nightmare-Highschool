"""
NPC voice blips (1.78.3). Owner: "Make some custom sound effects for the voice blips", then "Make it sound more human
like, and make variants for boys, girls, enemies, and authority npc's" and "make sure it isn't annoying".

A small formant ("Klatt-style") speech synthesizer. Each file is one spoken syllable (about 0.13 s):
  * the voice source is a glottal flow pulse with real throat irregularity: jitter (pitch wobble), shimmer (loudness
    wobble), breath that puffs with each vocal cycle, a spectral tilt (softer highs), and for rough voices a little
    vocal fry (every other pulse weaker, the gravel in a growl);
  * five formants in cascade shape it into a vowel, and after a consonant the formants glide in from where that
    consonant puts the tongue (t: high F2, k: F2 near F3, m: a nasal murmur), which is what makes it sound spoken;
  * the pitch rises a touch and falls (speech declination), with each take slightly different.
Not annoying, on purpose: soft 14 ms attacks and smooth releases (no clicks), everything above ~4.2 kHz rolled off (no
hiss or harshness), every syllable levelled to the same loudness (-17 dB RMS, peaks under -4 dB), and the rough voices kept
mild.

Four voice sets, each with its own pitch, throat length (formant scale) and texture:
  Boy        a teenage boy: 150 Hz, formants x1.04, a little breath
  Girl       a teenage girl: 230 Hz, formants x1.17, breathier and softer
  Enemy      delinquents and anything hostile: 112 Hz, formants x0.96, some vocal fry and a firmer edge
  Authority  teachers, the hall monitor, staff: 102 Hz, formants x0.90, steady, clear and unhurried
In game, Controllers.World.NpcLook pitches a set by each NPC's NHVoice (about +-8%), so every student still sounds
different within their set.

Output (mono 16-bit 44.1 kHz WAV, which Roblox accepts) in ./out, 10 files per set, 40 in all:
  NHVoice_<Set>_A, _E, _I, _O, _U, _Uh   vowels
  NHVoice_<Set>_Ma, _Ta, _Ka             with an m / t / k start
  NHVoice_<Set>_Hum                       a hesitant "mm..." for "..."
  ../preview_<Set>.wav and ../preview_all.wav   lines to listen to before uploading

Run: python make_npc_voice.py
"""
import os
import numpy as np
from scipy.io import wavfile
from scipy.signal import lfilter, butter

SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')

# vowel formants (Hz) for an adult-ish reference tract; each set scales them by its tract length
VOWELS = {
    'A': (750, 1220, 2600, 3500, 4200),
    'E': (500, 1800, 2550, 3500, 4200),
    'I': (300, 2250, 2950, 3600, 4300),
    'O': (480, 860, 2500, 3400, 4200),
    'U': (330, 800, 2400, 3400, 4200),
    'Uh': (600, 1350, 2500, 3450, 4200),
}
BANDWIDTHS = (70, 90, 130, 200, 260)
# where each consonant puts the formants as the vowel begins (F1, F2, F3)
LOCUS = {'t': (300, 1800, 2700), 'k': (300, 2000, 2400), 'm': (250, 1000, 2300)}

SETS = {
    #            f0    scale  breath  jitter shimmer fry   tilt  dur    edge
    'Boy':       (150, 1.04, 0.10,  0.008, 0.05, 0.00, 0.80, 0.130, 0.0),
    'Girl':      (230, 1.17, 0.16,  0.007, 0.05, 0.00, 0.86, 0.125, 0.0),
    'Enemy':     (112, 0.96, 0.13,  0.014, 0.09, 0.22, 0.72, 0.135, 0.35),
    'Authority': (102, 0.90, 0.07,  0.005, 0.03, 0.04, 0.78, 0.150, 0.0),
}


def resonator(x, f, bw):
    r = np.exp(-np.pi * bw / SR)
    th = 2 * np.pi * min(f, SR * 0.45) / SR
    return lfilter([1 - r], [1, -2 * r * np.cos(th), r * r], x)


def tv_resonator(x, f_track, bw):
    """A resonator whose frequency moves sample by sample (formant transitions)."""
    y = np.zeros_like(x)
    y1 = y2 = 0.0
    r = np.exp(-np.pi * bw / SR)
    for n in range(len(x)):
        th = 2 * np.pi * min(f_track[n], SR * 0.45) / SR
        a1, a2 = 2 * r * np.cos(th), -r * r
        yn = (1 - r) * x[n] + a1 * y1 + a2 * y2
        y[n] = yn
        y2, y1 = y1, yn
    return y


def source(rng, n, f0_curve, breath, jitter, shimmer, fry, tilt):
    """Glottal flow derivative with jitter / shimmer / fry, breath gated by the open phase, and spectral tilt."""
    out = np.zeros(n)
    open_gate = np.zeros(n)
    t = 0.0
    k = 0
    pulse = 0
    while True:
        f0 = f0_curve[min(int(t * SR), n - 1)] * (1 + rng.normal(0, jitter))
        period = 1.0 / f0
        start = int(t * SR)
        length = int(period * SR)
        if start >= n:
            break
        amp = 1 + rng.normal(0, shimmer)
        if fry > 0 and pulse % 2 == 1:
            amp *= 1 - fry  # every other pulse weaker: gravel
        m = np.arange(length) / max(length, 1)
        # Rosenberg glottal flow, then differentiate
        flow = np.where(m < 0.42, 0.5 * (1 - np.cos(np.pi * m / 0.42)), np.where(m < 0.6, np.cos(np.pi * (m - 0.42) / 0.36), 0.0))
        d = np.diff(np.concatenate([[0], flow])) * amp
        end = min(start + length, n)
        out[start:end] += d[:end - start]
        open_gate[start:end] = (m < 0.6)[:end - start]
        t += period
        pulse += 1
        k += 1
    # spectral tilt: real voices are darker than a raw pulse
    out = lfilter([1 - tilt], [1, -tilt], out)
    noise = rng.normal(0, 1, n)
    b, a = butter(2, [500 / (SR / 2), 5000 / (SR / 2)], 'band')
    asp = lfilter(b, a, noise) * (0.35 + 0.65 * open_gate) * breath * 0.08
    return out + asp


def envelope(n, attack=0.014, release=0.06):
    t = np.arange(n) / SR
    dur = n / SR
    a = 0.5 * (1 - np.cos(np.pi * np.clip(t / attack, 0, 1)))  # smooth: no click
    r = 0.5 * (1 - np.cos(np.pi * np.clip((dur - t) / release, 0, 1)))
    return a * r


def syllable(rng, cfg, vowel, onset=None):
    f0, scale, breath, jitter, shimmer, fry, tilt, dur, edge = cfg
    dur *= 0.94 + 0.12 * rng.random()
    n = int(SR * dur)
    t = np.arange(n) / SR
    # pitch: a small rise into the syllable then a fall, slightly different every take
    peak = 0.25 + 0.15 * rng.random()
    contour = 1 + 0.035 * np.sin(np.pi * np.clip(t / (dur * peak * 2), 0, 1)) - 0.06 * (t / dur)
    f0_curve = f0 * contour * (1 + 0.006 * np.sin(2 * np.pi * (4.5 + rng.random()) * t))
    src = source(rng, n, f0_curve, breath, jitter, shimmer, fry, tilt)
    target = [f * scale for f in VOWELS[vowel]]
    # formant tracks: glide from the consonant's locus over 35 ms, else steady (with a hint of drift)
    tracks = []
    for i, f in enumerate(target):
        tr = np.full(n, f) * (1 + 0.01 * np.sin(2 * np.pi * 2 * t + i))
        if onset in LOCUS and i < 3:
            lo = LOCUS[onset][i] * scale
            glide = np.clip(t / 0.035, 0, 1)
            tr = lo + (tr - lo) * (0.5 * (1 - np.cos(np.pi * glide)))
        tracks.append(tr)
    y = src
    for i, (tr, bw) in enumerate(zip(tracks, BANDWIDTHS)):
        y = tv_resonator(y, tr, bw * (1.15 if i == 0 and cfg is SETS['Authority'] else 1))
    y *= envelope(n)
    if onset == 'm':
        k = int(SR * 0.04)
        murmur = resonator(src[:k], 250 * scale, 60) + 0.15 * resonator(src[:k], 2400 * scale, 300)
        # the lips-closed hum, a little quieter than the vowel it opens into
        murmur *= 0.55 * (np.max(np.abs(y[k:])) or 1) / (np.max(np.abs(murmur)) or 1)
        fade = 0.5 * (1 - np.cos(np.pi * np.linspace(0, 1, k)))
        y[:k] = y[:k] * fade + murmur * (1 - fade) * envelope(k, 0.01, 0.02)
    elif onset in ('t', 'k'):
        k = int(SR * (0.010 if onset == 't' else 0.014))
        lo, hi = (2400, 4200) if onset == 't' else (1300, 2800)
        b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], 'band')
        burst = lfilter(b, a, rng.normal(0, 1, k)) * envelope(k, 0.002, 0.008)
        # soft, never louder than the vowel: a hint of a consonant, not a hiss or a click
        burst *= (0.16 if onset == 't' else 0.2) * (np.max(np.abs(y)) or 1) / (np.max(np.abs(burst)) or 1)
        y = np.concatenate([burst, y[:-k]])
    if edge > 0:
        y = np.tanh(y * (1 + 3 * edge) / (np.max(np.abs(y)) or 1)) / np.tanh(1 + 3 * edge)  # a firmer, gruffer edge
    return y


def hum(rng, cfg):
    f0, scale, breath, jitter, shimmer, fry, tilt, dur, edge = cfg
    n = int(SR * 0.34)
    t = np.arange(n) / SR
    f0_curve = f0 * 0.95 * (1 - 0.07 * t / 0.34) * (1 + 0.01 * np.sin(2 * np.pi * 4 * t))
    src = source(rng, n, f0_curve, breath * 1.3, jitter, shimmer, fry, tilt)
    y = resonator(src, 260 * scale, 60) + 0.18 * resonator(src, 2300 * scale, 250)
    return y * envelope(n, 0.04, 0.16)


def soften(x):
    """Roll off the harsh top end and level it: nothing shrill, nothing loud."""
    b, a = butter(4, 4200 / (SR / 2), 'low')
    x = lfilter(b, a, x)
    b, a = butter(2, 90 / (SR / 2), 'high')
    x = lfilter(b, a, x)
    x = x - np.mean(x)
    # level by loudness (RMS), not peak, so no syllable sticks out of a line; then make sure no peak tops -4 dB
    rms = np.sqrt(np.mean(x ** 2)) or 1
    x = x / rms * (10 ** (-17 / 20))
    p = np.max(np.abs(x))
    if p > 10 ** (-4 / 20):
        x *= 10 ** (-4 / 20) / p
    return x


def write(path, x):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    wavfile.write(path, SR, np.int16(np.clip(x, -1, 1) * 32767))


def pitch_shift(x, factor):
    idx = np.arange(0, len(x) - 1, factor)
    return np.interp(idx, np.arange(len(x)), x)


def sentence(rng, bank, voice=1.0, gap=0.105):
    """How NpcLook plays a line: one syllable per chunk, a pause at a comma, the last two rising for a question."""
    order = ['Ka', 'E', 'O', 'Uh', 'Ta', 'A', None, 'Ma', 'I', 'U', 'E', 'O']
    line = np.zeros(int(SR * 1.8))
    at = 0.05
    for i, s in enumerate(order):
        if s is None:
            at += 0.18
            continue
        rise = 1.12 if i >= len(order) - 2 else 1
        x = pitch_shift(bank[s], voice * (0.97 + 0.06 * rng.random()) * rise) * 0.9
        k = int(at * SR)
        line[k:k + len(x)] += x[:len(line) - k]
        at += gap + 0.02 * rng.random()
    return line


def main():
    report = []
    previews = []
    for name, cfg in SETS.items():
        rng = np.random.default_rng(abs(hash(name)) % (2 ** 32) if False else {'Boy': 11, 'Girl': 23, 'Enemy': 37, 'Authority': 41}[name])
        bank = {}
        for v in VOWELS:
            bank[v] = soften(syllable(rng, cfg, v))
        bank['Ma'] = soften(syllable(rng, cfg, 'A', 'm'))
        bank['Ta'] = soften(syllable(rng, cfg, 'E', 't'))
        bank['Ka'] = soften(syllable(rng, cfg, 'O', 'k'))
        bank['Hum'] = soften(hum(rng, cfg)) * 0.8
        for k, x in bank.items():
            write(os.path.join(OUT, f'NHVoice_{name}_{k}.wav'), x)
            spec = np.abs(np.fft.rfft(x * np.hanning(len(x))))
            freqs = np.fft.rfftfreq(len(x), 1 / SR)
            report.append(f'{name:9s} {k:3s} {len(x) / SR * 1000:4.0f} ms  centre {np.sum(freqs * spec) / np.sum(spec):5.0f} Hz  energy above 4 kHz {100 * np.sum(spec[freqs > 4000] ** 2) / np.sum(spec ** 2):4.1f}%')
        gap = 0.12 if name == 'Authority' else 0.105
        p = np.concatenate([sentence(rng, bank, 0.94, gap), np.zeros(int(SR * 0.3)), sentence(rng, bank, 1.06, gap), np.zeros(int(SR * 0.3)), bank['Hum'], np.zeros(int(SR * 0.4))])
        write(os.path.join(HERE, f'preview_{name}.wav'), p * 0.9)
        previews.append(p)
    write(os.path.join(HERE, 'preview_all.wav'), np.concatenate(previews) * 0.9)
    old = os.path.join(HERE, 'preview_sentence.wav')
    if os.path.exists(old):
        os.remove(old)
    for f in os.listdir(OUT):  # the first set (one voice) is replaced by the four sets
        if f.count('_') == 1:
            os.remove(os.path.join(OUT, f))
    print('\n'.join(report))


if __name__ == '__main__':
    main()
