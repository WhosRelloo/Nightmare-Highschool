"""NH race transformations: tileable SurfaceAppearance maps for the form pieces (Blender 5.2 headless, numpy only).

E:/Blender/blender.exe -b --factory-startup -P form_textures.py -- --out <repo>/art/group-upload-forms

Every colour map is light and near-neutral: the Looks colour it through SurfaceAppearance.Color (palette on the
Membrane pieces, finish on Frame and Horns, tip on Tip). The pieces' UVs are world-scaled (form_models.TILE), so one
set per material class serves every style. Periodic (FFT) noise, so every map tiles without seams.
Writes NHForm_<Set>_color.png (+ alpha where the set is see-through), _normal, _rough, _metal. --only Fur,Bone: just those.
"""
import bpy, os, sys
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[argv.index("--out") + 1] if "--out" in argv else "E:/NH-Work/forms/textures"
ONLY = argv[argv.index("--only") + 1].split(",") if "--only" in argv else None   # e.g. --only Fur (the others are
os.makedirs(OUT, exist_ok=True)                                                   # still computed, so the rng stays in step)
rng = np.random.default_rng(23)


def noise(n, beta=2.0, lo=1.0, hi=None, aniso=(1.0, 1.0)):
    """periodic 1/f^beta noise in 0..1; aniso stretches the frequencies (streaks)."""
    w = rng.standard_normal((n, n))
    fx = np.fft.fftfreq(n)[None, :] * n * aniso[0]
    fy = np.fft.fftfreq(n)[:, None] * n * aniso[1]
    f = np.sqrt(fx * fx + fy * fy)
    f[0, 0] = 1
    filt = 1.0 / f ** (beta / 2)
    filt[f < lo] = 0
    if hi:
        filt[f > hi] = 0
    r = np.real(np.fft.ifft2(np.fft.fft2(w) * filt))
    return (r - r.min()) / (r.max() - r.min() + 1e-9)


def ridged(n, beta=2.2, lo=2):
    r = 1 - np.abs(noise(n, beta, lo) * 2 - 1)
    for _ in range(2):          # soften the crease so the normal map has no pixel grain
        r = (r + np.roll(r, 1, 0) + np.roll(r, -1, 0) + np.roll(r, 1, 1) + np.roll(r, -1, 1)) / 5
    return r


def cells(n, k=40, sharp=8.0):
    """periodic Worley crackle: distance to the nearest of k points (wrapped)."""
    g = int(round(k ** 0.5))         # jittered grid: no two seeds close together (close pairs smear into wedges)
    pts = [((i + 0.5 + rng.uniform(-0.35, 0.35)) * n / g, (j + 0.5 + rng.uniform(-0.35, 0.35)) * n / g)
           for i in range(g) for j in range(g)]
    yy, xx = np.mgrid[0:n, 0:n]
    d1 = np.full((n, n), 1e9); d2 = np.full((n, n), 1e9)
    for px, py in pts:
        dx = np.abs(xx - px); dx = np.minimum(dx, n - dx)
        dy = np.abs(yy - py); dy = np.minimum(dy, n - dy)
        d = np.sqrt(dx * dx + dy * dy)
        d2 = np.where(d < d1, d1, np.minimum(d2, d)); d1 = np.minimum(d1, d)
    return np.clip((d2 - d1 - 1.0) / sharp, 0, 1) ** 0.5     # 0 on the crack (a few px wide), 1 inside a cell


def normal_from(h, strength):
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * strength
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * strength
    nz = np.ones_like(h)
    l = np.sqrt(gx * gx + gy * gy + nz * nz)
    return np.stack([(-gx / l) * 0.5 + 0.5, (gy / l) * 0.5 + 0.5, (nz / l) * 0.5 + 0.5], -1)


def save(name, arr, alpha=None):
    n = arr.shape[0]
    if arr.ndim == 2:
        arr = np.stack([arr] * 3, -1)
    a = np.ones((n, n)) if alpha is None else alpha
    rgba = np.concatenate([np.clip(arr, 0, 1), a[..., None]], -1)
    img = bpy.data.images.new(name, n, n, alpha=alpha is not None)
    img.pixels.foreach_set(np.flipud(rgba).astype(np.float32).ravel())
    img.filepath_raw = os.path.join(OUT, name + ".png"); img.file_format = "PNG"
    img.save()
    print("wrote", img.filepath_raw)


def write_set(nm, h, col, rough, metal, nstr, alpha=None):
    if ONLY and nm not in ONLY:
        return
    save(f"NHForm_{nm}_color", col, alpha)
    save(f"NHForm_{nm}_normal", normal_from(h, nstr))
    save(f"NHForm_{nm}_rough", rough)
    if metal:                     # a flat 0 map is the SurfaceAppearance default: don't make the owner upload it
        save(f"NHForm_{nm}_metal", np.full(h.shape, metal))


N = 1024
# Membrane (bat, drake, tattered): leathery wrinkles, fine veinlets, a soft mottle
wr = ridged(N, 3.4, 3, ); fine = noise(N, 2.4, 24); mott = noise(N, 2.6, 1)
veinlet = np.clip((ridged(N, 3.0, 4) - 0.86) * 6, 0, 1)
h = wr * 0.62 + fine * 0.06 + veinlet * 0.32
col = 0.78 + 0.14 * mott - 0.16 * veinlet - 0.04 * fine
write_set("Membrane", h, np.stack([col, col * 0.97, col * 0.97], -1), 0.45 + 0.15 * fine - 0.1 * veinlet, 0.0, 14.0)

# Feather (fallen): barbs as fine streaks, a soft sheen band
barbs = noise(N, 1.4, 20, aniso=(0.12, 1.0)); band = noise(N, 2.4, 1)
h = barbs * 0.8 + band * 0.2
col = 0.74 + 0.16 * band + 0.08 * (barbs - 0.5)
write_set("Feather", h, col, 0.38 + 0.2 * (1 - barbs), 0.0, 5.0)

# Cloth (ossuary grave linen): a weave, frays, grime
yy, xx = np.mgrid[0:N, 0:N] / N
weave = (0.5 + 0.5 * np.sin(xx * 2 * np.pi * 96)) * (0.5 + 0.5 * np.sin(yy * 2 * np.pi * 96))
grime = noise(N, 2.2, 1)
h = weave * 0.6 + noise(N, 1.6, 10) * 0.4
col = 0.86 - 0.28 * grime ** 1.5 - 0.06 * weave
write_set("Cloth", h, np.stack([col, col * 0.98, col * 0.92], -1), 0.85 + 0.1 * grime, 0.0, 3.0)

# Mist (wraithveil): wisps with see-through gaps (AlphaMode Transparency)
wisp = noise(N, 2.2, 2, aniso=(0.35, 1.0)); wisp2 = noise(N, 1.8, 6)
a = np.clip(0.25 + 0.7 * wisp * (0.6 + 0.4 * wisp2), 0, 1)
col = 0.82 + 0.18 * wisp
write_set("Mist", wisp, col, 0.25 + 0.1 * wisp2, 0.0, 1.5, alpha=a)

# Ice (rime): crackle with frosted cells, mostly see-through
n2 = 512
cr = cells(n2, 36, 3.0); frost = noise(n2, 1.4, 20)
h = cr * 0.7 + frost * 0.3
col = 0.9 + 0.1 * cr - 0.12 * (1 - cr)
write_set("Ice", h, np.stack([col * 0.93, col * 0.98, col], -1), 0.08 + 0.35 * frost * (1 - cr) + 0.3 * (1 - cr), 0.0, 7.0,
          alpha=np.clip(0.55 + 0.35 * (1 - cr) + 0.1 * frost, 0, 1))

# Bone (wing frames): porous, polished on the ridges
pores = np.clip((noise(n2, 0.9, 60) - 0.7) * 3, 0, 1); grain = noise(n2, 2.0, 2, aniso=(1.0, 0.3)); mot = noise(n2, 2.6, 1)
h = grain * 0.6 - pores * 0.4 + 0.4
col = 0.86 + 0.1 * mot - 0.18 * pores
write_set("Bone", h, np.stack([col, col * 0.97, col * 0.92], -1), 0.42 + 0.25 * pores + 0.1 * (1 - grain), 0.0, 5.0)

# Horn (horns, tips, halo): keratin streaks and growth rings
streak = noise(n2, 1.6, 6, aniso=(0.15, 1.0)); rings = 0.5 + 0.5 * np.sin(np.mgrid[0:n2, 0:n2][0] / n2 * 2 * np.pi * 10)
h = streak * 0.5 + rings * 0.5
col = 0.8 + 0.14 * streak - 0.08 * rings
write_set("Horn", h, col, 0.3 + 0.25 * (1 - streak), 0.0, 6.0)

# Fur (werewolf mantles, cuffs; grave-moss): strands along V (the pieces' locks run their V down the lock), clumps
fs = noise(n2, 1.2, 30, aniso=(0.06, 1.0)); clump = noise(n2, 2.4, 2); fine = noise(n2, 1.0, 60, aniso=(0.1, 1.0))
h = fs * 0.65 + clump * 0.2 + fine * 0.15
col = 0.7 + 0.2 * clump + 0.14 * (fs - 0.5) + 0.05 * (fine - 0.5)
write_set("Fur", h, np.stack([col, col * 0.97, col * 0.94], -1), 0.62 + 0.22 * (1 - fs), 0.0, 6.0)
