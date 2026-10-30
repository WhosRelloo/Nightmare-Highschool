"""HQ pass: re-render all ornament as embossed, grimy metal with a dark outline.
Output stays greyscale (tint with ImageColor3). Run: python gen_hq.py <outdir>"""
import math, sys, os, random
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

OUT = sys.argv[1]
sys.argv = [sys.argv[0], OUT]
import gen_tex as G

LIGHT = np.array([-0.55, -0.75, 0.9])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def _pad(a, p, wrap):
    if wrap == "x":
        a = np.pad(a, ((0, 0), (p, p)), mode="wrap")
        return np.pad(a, ((p, p), (0, 0)), mode="constant")
    if wrap == "y":
        a = np.pad(a, ((p, p), (0, 0)), mode="wrap")
        return np.pad(a, ((0, 0), (p, p)), mode="constant")
    if wrap == "edge":
        return np.pad(a, p, mode="edge")
    return np.pad(a, p, mode="constant")


def _blur(a, r, wrap=None):
    p = int(r * 3) + 2
    x = _pad(a, p, wrap).astype(np.float32)
    ks = np.arange(-p, p + 1)
    ker = np.exp(-(ks ** 2) / (2 * r * r)); ker /= ker.sum()
    h, w = x.shape
    t = np.zeros((h, w - 2 * p), np.float32)
    for i, kv in enumerate(ker):
        t += kv * x[:, i:i + w - 2 * p]
    o = np.zeros((h - 2 * p, w - 2 * p), np.float32)
    for i, kv in enumerate(ker):
        o += kv * t[i:i + h - 2 * p, :]
    return o


def _dilate(a, r, wrap=None):
    p = r + 1
    im = Image.fromarray((_pad(a, p, wrap) * 255).astype(np.uint8))
    out = np.asarray(im.filter(ImageFilter.MaxFilter(2 * r + 1)), np.float32) / 255
    return out[p:-p, p:-p]


def _ggx(n, l, v, rough, f0):
    """Cook-Torrance GGX specular * NdotL for per-pixel normals n (h,w,3)."""
    hv = l + v; hv = hv / np.linalg.norm(hv)
    nl = np.clip((n * l).sum(2), 0, 1)
    nv = np.clip((n * v).sum(2), 1e-3, 1)
    nh = np.clip((n * hv).sum(2), 0, 1)
    vh = max(float(np.dot(v, hv)), 1e-3)
    a2 = (rough * rough) ** 2
    D = a2 / (math.pi * (nh * nh * (a2 - 1) + 1) ** 2)
    kk = (rough + 1) ** 2 / 8
    Gs = (nl / (nl * (1 - kk) + kk)) * (nv / (nv * (1 - kk) + kk))
    F = f0 + (1 - f0) * (1 - vh) ** 5
    return D * F * Gs / (4 * np.maximum(nl * nv, 1e-3)) * nl, nl


def metal(alpha255, seed, shade=0.25, wrap=None, k=1.0, outline=True, base=0.30, exposure=1.4):
    """Baked PBR metal. alpha255: 0..255 mask. k: pixel scale (texture px per design px / 4).
    Maps: height->normal, albedo (aged iron + grime), roughness (polished vs pitted), metalness=1."""
    a = np.clip(alpha255 / 255.0, 0, 1)
    h, w = a.shape
    # height: rounded stroke profile + fine hammered noise
    hgt = _blur(a, 1.6 * k, wrap) * 0.6 + _blur(a, 4.0 * k, wrap) * 0.4
    ham = G.fbm(w, h, seed + 500, base=max(2, int(6 * k)), octaves=2)
    hh = hgt * (6.0 / max(k, 0.5)) + ham * 0.35 * a
    gy, gx = np.gradient(hh)
    n = np.dstack([-gx, -gy, np.ones_like(gx)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    # material maps
    gr = G.fbm(w, h, seed + 300, base=max(8, int(48 * k)), octaves=4)        # grime mask
    pit = G.fbm(w, h, seed + 400, base=max(2, int(4 * k)), octaves=2)        # pitting
    grime = np.clip((gr - 0.42) * 2.4, 0, 1)
    albedo = (0.92 - 0.42 * grime) * (0.9 + 0.12 * pit)                      # metal F0 (greyscale)
    rough = np.clip(0.30 + 0.45 * grime + 0.12 * pit, 0.12, 0.95)
    ao = 0.55 + 0.45 * np.clip(hgt * 1.7, 0, 1)                               # cavities between strokes
    v = np.array([0.0, 0.0, 1.0])
    key = np.array([-0.55, -0.75, 0.9]); key /= np.linalg.norm(key)
    rim = np.array([0.7, 0.6, 0.45]); rim /= np.linalg.norm(rim)
    sk, nlk = _ggx(n, key, v, rough, albedo)
    sr, _ = _ggx(n, rim, v, rough, albedo)
    up = np.clip(-n[..., 1] * 0.5 + 0.5, 0, 1)                                # hemispheric env
    env = albedo * (0.24 + 0.30 * up) * (1.0 - 0.5 * rough)
    lum = (env + sk * 2.4 + sr * 0.6 + albedo * nlk * 0.12) * ao
    lum = lum / (1 + lum * 0.35)                                              # soft tone-map
    lum = np.clip(lum * exposure, 0, 1)
    if outline:
        o = _blur(_dilate(a, max(1, int(round(1.5 * k))), wrap), 1.2 * k, wrap)
        sh = np.clip(o * 1.6, 0, 1) * 0.92
        alpha = a + sh * (1 - a)
        rgb = np.where(alpha > 1e-4, (lum * a) / np.maximum(alpha, 1e-4), 0)
    else:
        alpha, rgb = a, lum
    rgb8 = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    a8 = (np.clip(alpha, 0, 1) * 255).astype(np.uint8)
    return Image.merge("RGBA", [Image.fromarray(rgb8)] * 3 + [Image.fromarray(a8)])


# patch the old pipeline so every generator gets the metal look
_K = {"v": 1.0}
G.to_rgba = lambda alpha, seed, shade=0.25: metal(alpha, seed, shade, None, _K["v"])


def save(img, name):
    img.save(os.path.join(OUT, name + ".png"))


# ---------------------------------------------------------------- re-render
_K["v"] = 0.6; G.thin_frame()
_K["v"] = 1.0; G.bar_frame(); G.orb_ring()
_K["v"] = 0.8; G.divider()
_K["v"] = 0.5; G.knob()
_K["v"] = 1.0; G.bell()
G.orb_fill(); G.wax_seal(); G.soft_shadow()

# icons
import importlib
_K["v"] = 0.7
sys.argv = [sys.argv[0], OUT]
import gen_icons  # noqa: E402  (re-runs with patched to_rgba)

# ------------------------------------------- corner + edge (wrap-aware)
import gen_frame2 as F  # noqa: E402  regenerates masks; we re-finish below
c = F.corner()
e = F.edge_tile()
def fin(L, name, seed, wrap):
    a = G.wear(np.asarray(L, np.float32), seed, 0.3)
    save(metal(a, seed, 0.28, wrap, 1.0), name)
fin(c, "corner_tl", 41, "edge")
fin(c.transpose(Image.FLIP_LEFT_RIGHT), "corner_tr", 42, "edge")
fin(c.transpose(Image.FLIP_TOP_BOTTOM), "corner_bl", 43, "edge")
fin(c.transpose(Image.ROTATE_180), "corner_br", 44, "edge")
fin(e, "edge_t", 45, "x")
fin(e.transpose(Image.FLIP_TOP_BOTTOM), "edge_b", 46, "x")
fin(e.transpose(Image.TRANSPOSE), "edge_l", 47, "y")
fin(e.transpose(Image.TRANSPOSE).transpose(Image.FLIP_LEFT_RIGHT), "edge_r", 48, "y")

# ------------------------------------------------ new: ornate slot frame
def slot_frame(S=192, name="frame_slot", seed=61):
    p = G.Pen(S, S)
    o, i = 6, 15
    for (a, b) in [((o, o), (S - o, o)), ((o, S - o), (S - o, S - o)), ((o, o), (o, S - o)), ((S - o, o), (S - o, S - o))]:
        p.line(a, b, 3.2)
    for (a, b) in [((i, i), (S - i, i)), ((i, S - i), (S - i, S - i)), ((i, i), (i, S - i)), ((S - i, i), (S - i, S - i))]:
        p.line(a, b, 1.4)
    base = p.result()
    C = 48
    q = G.Pen(C, C)
    q.poly([(o - 3, o - 3), (o + 16, o - 3), (o + 9, o + 3), (o + 3, o + 9), (o - 3, o + 16)])  # corner bracket plate
    q.dot(o + 2, o + 2, 2.6, 0)
    q.stroke(G.spiral(i + 9, i + 9, 7, 1.5, math.pi * 1.25, math.pi * 1.6), 2.4, 1.1)
    q.poly(G.diamond(i + 3, i + 3, 3.2))
    q.poly([(30, o - 1), (34, o - 6), (38, o - 1)])
    q.poly([(o - 1, 30), (o - 6, 34), (o - 1, 38)])
    cs = G.mirror_corners(q.result(), C)
    for kk, im in cs.items():
        x = 0 if kk[1] == "l" else S - C
        y = 0 if kk[0] == "t" else S - C
        region = base.crop((x, y, x + C, y + C))
        base.paste(Image.fromarray(np.maximum(np.asarray(region), np.asarray(im))), (x, y))
    a = G.wear(np.asarray(base, np.float32), seed, 0.3)
    save(metal(a, seed, 0.25, "edge", 0.7), name)


def slot_bg(S=128, name="slot_bg", seed=63):
    y, x = np.mgrid[0:S, 0:S].astype(np.float32)
    d = np.maximum(np.abs(x - S / 2), np.abs(y - S / 2)) / (S / 2)
    inner = np.clip(1 - d ** 3 * 0.85, 0, 1)
    n = G.fbm(S, S, seed, base=32, octaves=5)
    lum = (0.25 + 0.55 * n) * inner
    lum += np.exp(-((x - S * 0.5) ** 2 + (y - S * 0.42) ** 2) / (2 * (S * 0.3) ** 2)) * 0.18
    Image.fromarray((np.clip(lum, 0, 1) * 255).astype(np.uint8)).convert("RGB").save(os.path.join(OUT, name + ".png"))


# ---------------------------------------------- new: health bar end caps
def bar_cap(name="bar_cap_l", seed=71):
    """64x64 design (256px). Rails meet at outer y=4 / inner y=14 (top) and mirrored bottom,
    matching EdgeT/EdgeB tiles placed at the bar's top/bottom."""
    K = 4
    p = G.Pen(64 * K, 64 * K)
    def P(pts): return [(x * K, y * K) for x, y in pts]
    def st(pts, w0, w1=None, v=255): p.stroke(P(pts), w0 * K, (w1 if w1 is not None else w0) * K, v)
    def dot(x, y, r, v=255): p.dot(x * K, y * K, r * K, v)
    def poly(pts, v=255): p.poly(P(pts), v)
    cy = 32
    # rails continuing to the right edge
    st([(44, 4), (65, 4)], 2.2); st([(48, 14), (65, 14)], 1.1)
    st([(44, 60), (65, 60)], 2.2); st([(48, 50), (65, 50)], 1.1)
    # end post
    st([(46, 2), (46, 62)], 3.4)
    poly(G.diamond(46, 3, 3.6)); poly(G.diamond(46, 61, 3.6))
    # finial: pierced diamond + spike
    poly(G.diamond(20, cy, 13)); poly(G.diamond(20, cy, 7.5), 0); poly(G.diamond(20, cy, 3.6))
    poly([(1, cy), (8, cy - 3.2), (8, cy + 3.2)])
    st([(33, cy), (46, cy)], 2.6)
    # scrolls from the finial up/down to the post
    st(G.bezier((22, cy - 13), (24, cy - 24), (36, cy - 26), (45, cy - 22)), 2.4, 1.8)
    st(G.bezier((22, cy + 13), (24, cy + 24), (36, cy + 26), (45, cy + 22)), 2.4, 1.8)
    st(G.spiral(32, cy - 13, 5.5, 1.2, math.pi * 0.5, math.pi * 1.5), 1.9, 0.9)
    st(G.spiral(32, cy + 13, 5.5, 1.2, -math.pi * 0.5, -math.pi * 1.5), 1.9, 0.9)
    poly(G.leaf((12, cy - 9), math.radians(-120), 9, 2.2)); poly(G.leaf((12, cy + 9), math.radians(120), 9, 2.2))
    a = G.wear(np.asarray(p.result().resize((256, 256), Image.LANCZOS), np.float32), seed, 0.25)
    img = metal(a, seed, 0.25, "edge", 1.0)
    save(img, "bar_cap_l")
    save(img.transpose(Image.FLIP_LEFT_RIGHT), "bar_cap_r")


def bar_fill(W=512, H=96, seed=75):
    """horizontally tileable veined blood/ink with a glossy top"""
    n = G.fbm(W, H, seed, base=48, octaves=6)
    r = 1 - np.abs(G.fbm(W, H, seed + 9, base=32, octaves=4) * 2 - 1)  # ridged veins
    veins = np.clip((r - 0.82) * 6, 0, 1)
    y = np.mgrid[0:H, 0:W][0].astype(np.float32) / H
    v = 1 - np.abs(y - 0.45) ** 1.6 * 1.4
    lum = (0.55 + 0.45 * n - 0.35 * veins) * np.clip(v, 0.15, 1)
    gloss = np.exp(-((y - 0.2) ** 2) / 0.004) * 0.35
    lum = np.clip(lum + gloss, 0, 1)
    Image.fromarray((lum * 255).astype(np.uint8)).convert("RGB").save(os.path.join(OUT, "bar_fill.png"))


def glow(S=256):
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    r = np.hypot(xx - S / 2, yy - S / 2) / (S / 2)
    a = np.clip(1 - r, 0, 1) ** 2.2
    w = np.full((S, S), 255, np.uint8)
    Image.merge("RGBA", [Image.fromarray(w)] * 3 + [Image.fromarray((a * 255).astype(np.uint8))]).save(os.path.join(OUT, "glow.png"))


def panel_bg(S=512, seed=21):
    """slate with chalk smudges, grain and strong inner edge shadow"""
    G.panel_bg(S, "panel_bg", seed)
    base = np.asarray(Image.open(os.path.join(OUT, "panel_bg.png")).convert("L"), np.float32) / 255
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    e = np.minimum(np.minimum(xx, S - 1 - xx), np.minimum(yy, S - 1 - yy)) / (S * 0.12)
    edge = np.clip(e, 0, 1) ** 0.8
    grain = G.fbm(S, S, seed + 77, base=2, octaves=1)
    lum = base * (0.35 + 0.65 * edge) * (0.9 + 0.2 * grain)
    Image.fromarray((np.clip(lum, 0, 1) * 255).astype(np.uint8)).convert("RGB").save(os.path.join(OUT, "panel_bg.png"))


slot_frame(); slot_bg(); bar_cap(); bar_fill(); glow(); panel_bg()

# ---------------------------------------------- review composites
def tinted(name, tint):
    im = Image.open(os.path.join(OUT, name + ".png")).convert("RGBA")
    arr = np.asarray(im, np.float32); arr[..., :3] *= np.array(tint) / 255
    return Image.fromarray(arr.astype(np.uint8))

W, H, K = 360, 220, 4
bgi = Image.open(os.path.join(OUT, "panel_bg.png")).convert("RGB").resize((W * K, H * K))
pane = Image.fromarray((np.asarray(bgi, np.float32) * np.array([52, 46, 60]) / 255).astype(np.uint8)).convert("RGBA")
iron = (178, 172, 186)
def put(name, x, y, w=None, h=None, tile=False):
    im = tinted(name, iron)
    if tile:
        for xx in range(0, w, im.width):
            for yy in range(0, h, im.height):
                pane.alpha_composite(im.crop((0, 0, min(im.width, w - xx), min(im.height, h - yy))), (x + xx, y + yy))
    else:
        pane.alpha_composite(im, (x, y))
C, E = 56, 20
put("edge_t", C*K, 0, (W - 2*C)*K, E*K, True); put("edge_b", C*K, (H - E)*K, (W - 2*C)*K, E*K, True)
put("edge_l", 0, C*K, E*K, (H - 2*C)*K, True); put("edge_r", (W - E)*K, C*K, E*K, (H - 2*C)*K, True)
put("corner_tl", 0, 0); put("corner_tr", (W - C)*K, 0); put("corner_bl", 0, (H - C)*K); put("corner_br", (W-C)*K, (H-C)*K)
# slot in the middle
slot = tinted("frame_slot", iron).resize((78 * K, 78 * K), Image.LANCZOS)
pane.alpha_composite(slot, (60 * K, 70 * K))
bell = tinted("bell", (228, 222, 208)).resize((80 * K, 80 * K), Image.LANCZOS)
pane.alpha_composite(bell, (170 * K, 70 * K))
cap = tinted("bar_cap_l", iron); pane.alpha_composite(cap, (250 * K, 80 * K))
pane.resize((W * 2, H * 2), Image.LANCZOS).save(os.path.join(OUT, "_hq_2x.png"))
print("ok")
