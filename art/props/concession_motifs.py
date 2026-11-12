"""Drawn motifs for the concession kit's labels (concession_atlas.py): mascots, frames, badges and marks. Every function draws
into a concession_svg.Label at a centre (cx, cy) and a size s (about the figure's height). All invented; nothing gory."""
import math
import random

INK = "#17141c"
BONE = "#efe5cb"
CREAM = "#ece2c8"
CRIMSON = "#6a1020"
GOLD = "#d6aa58"
PI = math.pi


def P(*pts):
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)


def star_pts(cx, cy, r, n=5, inner=0.45, rot=0.0):
    out = []
    for i in range(n * 2):
        a = -PI / 2 + rot + i * PI / n
        rr = r if i % 2 == 0 else r * inner
        out.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    return out


def ring_pts(cx, cy, r, n=48, rx=None):
    rx = rx or r
    return [(cx + math.cos(2 * PI * i / n) * rx, cy + math.sin(2 * PI * i / n) * r) for i in range(n)]


# ------------------------------------------------------------------ marks

def star(L, cx, cy, r, fill, cls="", n=5, inner=0.45, rot=0.0, stroke=None, sw=0):
    L.poly(star_pts(cx, cy, r, n, inner, rot), fill, stroke=stroke, sw=sw, cls=cls)


def sparkle(L, cx, cy, r, fill, cls=""):
    L.poly(star_pts(cx, cy, r, 4, 0.22), fill, cls=cls)


def moon(L, cx, cy, r, fill, cls="", phase=0.32, bg=None):
    """A crescent: a disc with a bite (the bite is a path, so the mask passes stay clean)."""
    k = 1 - phase * 2
    d = (f"M {cx:.2f} {cy - r:.2f} A {r:.2f} {r:.2f} 0 1 0 {cx:.2f} {cy + r:.2f} "
         f"A {r * abs(k) + 0.01:.2f} {r:.2f} 0 1 {1 if k > 0 else 0} {cx:.2f} {cy - r:.2f} Z")
    L.path(d, fill, cls=cls)


def barcode(L, x, y, w, h, ink=INK, bg="#f4efe2", seed=7, digits="4 902 113 54"):
    L.rect(x - w * 0.06, y - h * 0.08, w * 1.12, h * 1.32, bg, rx=3)
    rnd = random.Random(seed)
    xx = x
    while xx < x + w:
        bw = rnd.choice((1.2, 1.2, 2.2, 3.4)) * w / 120
        if rnd.random() < 0.62:
            L.rect(xx, y, bw, h, ink)
        xx += bw + rnd.choice((1.2, 2.0)) * w / 120
    L.text(digits, x + w / 2, y + h * 1.12, size=h * 0.2, f="frank", fill=ink, ls=h * 0.03)


def frame(L, x, y, w, h, col, sw=3, cls="", corner=True, inset=8, double=True, arch=False):
    """A gothic frame: a double rule with quatrefoil corners (and a pointed arch top)."""
    if arch:
        r = w / 2
        d = (f"M {x:.2f} {y + h:.2f} L {x:.2f} {y + r * 0.55:.2f} Q {x:.2f} {y:.2f} {x + w / 2:.2f} {y - r * 0.15:.2f} "
             f"Q {x + w:.2f} {y:.2f} {x + w:.2f} {y + r * 0.55:.2f} L {x + w:.2f} {y + h:.2f} Z")
        L.path(d, "none", col, sw, cls=cls)
        return
    L.rect(x, y, w, h, "none", col, sw, cls=cls)
    if double:
        L.rect(x + inset, y + inset, w - 2 * inset, h - 2 * inset, "none", col, sw * 0.45, cls=cls)
    if corner:
        q = inset * 1.15
        for cx, cy in ((x, y), (x + w, y), (x, y + h), (x + w, y + h)):
            quatrefoil(L, cx, cy, q, col, cls)


def quatrefoil(L, cx, cy, r, fill, cls=""):
    for ox, oy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
        L.circle(cx + ox * r * 0.5, cy + oy * r * 0.5, r * 0.5, fill, cls=cls)


def starburst(L, cx, cy, r, fill, lines, ink, cls="", n=16, f="impact", rot=-12, edge=None):
    L.poly(star_pts(cx + r * 0.05, cy + r * 0.07, r, n, 0.8), "#000", cls="fx", op=0.35)
    L.poly(star_pts(cx, cy, r, n, 0.8), fill, stroke=edge, sw=r * 0.04 if edge else 0, cls=cls)
    k = len(lines)
    for i, s in enumerate(lines):
        L.text(s, cx, cy + (i - (k - 1) / 2) * r * 0.42, maxw=r * 1.25, maxh=r * (0.42 if k > 1 else 0.6), f=f, fill=ink, rot=rot,
               cls="emb")


def ribbon(L, cx, cy, w, h, fill, text, ink, f="serif", cls="", tail="#4a0a14"):
    t = h * 0.5
    L.poly([(cx - w / 2 - t * 1.6, cy - h * 0.25), (cx - w / 2 + t * 0.3, cy - h * 0.25), (cx - w / 2 + t * 0.3, cy + h * 0.75),
            (cx - w / 2 - t * 1.6, cy + h * 0.75), (cx - w / 2 - t * 0.9, cy + h * 0.25)], tail)
    L.poly([(cx + w / 2 + t * 1.6, cy - h * 0.25), (cx + w / 2 - t * 0.3, cy - h * 0.25), (cx + w / 2 - t * 0.3, cy + h * 0.75),
            (cx + w / 2 + t * 1.6, cy + h * 0.75), (cx + w / 2 + t * 0.9, cy + h * 0.25)], tail)
    L.rect(cx - w / 2, cy - h / 2, w, h, fill, cls=cls)
    L.text(text, cx, cy, maxw=w * 0.86, maxh=h * 0.58, f=f, fill=ink, cls="emb")


def okada_stamp(L, cx, cy, r, col, cls="", text="OKADA'S", sub="EST. 1902"):
    L.circle(cx, cy, r, "none", col, r * 0.07, cls=cls)
    L.circle(cx, cy, r * 0.78, "none", col, r * 0.025, cls=cls)
    moon(L, cx - r * 0.08, cy - r * 0.04, r * 0.3, col, cls=cls)
    star(L, cx + r * 0.22, cy - r * 0.14, r * 0.09, col, cls=cls)
    L.text_arc(text, cx, cy, r * 0.86, r * 0.26, f="serif", fill=col, cls=cls, ls=r * 0.03)
    L.text_arc(sub, cx, cy, r * 0.86, r * 0.17, f="serif", fill=col, top=False, cls=cls, ls=r * 0.03)


def crest(L, cx, cy, s, foil_cls="foil emb"):
    """The school shield, s tall: quartered crimson and ink under a gilt cross with a crescent, key, quatrefoil and candle."""
    def p(u, v):
        return (cx + u * s, cy + v * s)
    sh = [(-0.36, -0.42), (0.36, -0.42), (0.36, 0.02), (0.28, 0.24), (0.14, 0.38), (0, 0.46), (-0.14, 0.38), (-0.28, 0.24), (-0.36, 0.02)]
    L.poly([p(u * 1.13, v * 1.09 + 0.004) for u, v in sh], "#000", cls="fx", op=0.4)
    L.poly([p(u * 1.12, v * 1.08) for u, v in sh], L.gilt(), cls=foil_cls)
    L.poly([p(u, v) for u, v in sh], "#7a1222", cls="emb")
    L.poly([p(0, -0.42), p(0.36, -0.42), p(0.36, -0.08), p(0, -0.08)], "#1c1e34", cls="emb")
    L.poly([p(0, -0.08), p(-0.36, -0.08), p(-0.36, 0.02), p(-0.28, 0.24), p(-0.14, 0.38), p(0, 0.46)], "#1c1e34", cls="emb")
    g = L.gilt()
    L.rect(cx - 0.025 * s, cy - 0.42 * s, 0.05 * s, 0.88 * s, g, cls=foil_cls)
    L.rect(cx - 0.36 * s, cy - 0.105 * s, 0.72 * s, 0.05 * s, g, cls=foil_cls)
    moon(L, cx - 0.18 * s, cy - 0.25 * s, 0.1 * s, g, cls=foil_cls)
    kx, ky = p(0.18, -0.25)
    L.circle(kx, ky - 0.06 * s, 0.045 * s, "none", g, 0.02 * s, cls=foil_cls)
    L.rect(kx - 0.012 * s, ky - 0.02 * s, 0.024 * s, 0.15 * s, g, cls=foil_cls)
    L.rect(kx, ky + 0.07 * s, 0.05 * s, 0.025 * s, g, cls=foil_cls)
    quatrefoil(L, *p(-0.16, 0.12), 0.09 * s, g, foil_cls)
    bx, by = p(0.16, 0.14)
    L.rect(bx - 0.025 * s, by - 0.05 * s, 0.05 * s, 0.17 * s, g, cls=foil_cls)
    L.ellipse(bx, by - 0.09 * s, 0.022 * s, 0.035 * s, "#ffcf6a", cls=foil_cls)


def lace(L, y, x0, x1, r, fill, down=True, hole="#000", cls=""):
    """A scalloped lace edge along y from x0 to x1 (scallops hang down, or up), with eyelet holes."""
    n = max(1, int((x1 - x0) / (2 * r)))
    w = (x1 - x0) / n
    sgn = 1 if down else -1
    d = f"M {x0:.2f} {y:.2f} "
    for i in range(n):
        d += f"A {w / 2:.2f} {r:.2f} 0 0 {0 if down else 1} {x0 + (i + 1) * w:.2f} {y:.2f} "
    d += "Z"
    L.path(d, fill, cls=cls)
    for i in range(n):
        L.circle(x0 + (i + 0.5) * w, y + sgn * r * 0.45, r * 0.18, hole)


def back_panel(L, cx, top, w, h, title, lines, ink, accent, bg=None, f_title="serif", f_body="serifi", code="4 902 113 54",
               seed=3, stamp=True):
    """A wrap's back panel: a heading, a few lines of fun copy, a barcode and the Okada's stamp."""
    if bg:
        L.rect(cx - w / 2, top, w, h, bg, rx=6)
    L.text(title, cx, top + h * 0.1, maxw=w * 0.86, maxh=h * 0.11, f=f_title, fill=accent)
    L.line(cx - w * 0.36, top + h * 0.19, cx + w * 0.36, top + h * 0.19, accent, max(1.0, h * 0.008))
    n = len(lines)
    lh = min(h * 0.085, h * 0.48 / max(n, 1))
    for i, s in enumerate(lines):
        L.text(s, cx, top + h * 0.27 + i * lh * 1.15, maxw=w * 0.9, maxh=lh, f=f_body, fill=ink)
    bw = w * 0.34
    barcode(L, cx - w * 0.42, top + h * 0.72, bw, h * 0.16, seed=seed, digits=code)
    if stamp:
        okada_stamp(L, cx + w * 0.28, top + h * 0.8, h * 0.13, accent)


# ------------------------------------------------------------------ mascots

def bone_line(L, pts, w, bone=BONE, ink=INK):
    d = "M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in pts)
    L.path(d, "none", ink, w * 1.55)
    L.path(d, "none", bone, w)
    for x, y in (pts[0], pts[-1]):
        L.circle(x, y, w * 0.85, bone, ink, w * 0.28)


def skeleton(L, cx, cy, s, crisp="#e8b54a"):
    """Crunch, the Grave Crisps skeleton: a big grinning cartoon skull and shoulders, one hand holding a crisp to his grin."""
    o = s * 0.018
    # ribs and spine
    L.path(f"M {cx:.2f} {cy + 0.12 * s:.2f} L {cx:.2f} {cy + 0.5 * s:.2f}", "none", INK, s * 0.07)
    L.path(f"M {cx:.2f} {cy + 0.12 * s:.2f} L {cx:.2f} {cy + 0.5 * s:.2f}", "none", BONE, s * 0.045)
    for i in range(3):
        y = cy + (0.2 + i * 0.1) * s
        ww = (0.22 - i * 0.03) * s
        d = f"M {cx - ww:.2f} {y + 0.04 * s:.2f} Q {cx:.2f} {y - 0.06 * s:.2f} {cx + ww:.2f} {y + 0.04 * s:.2f}"
        L.path(d, "none", INK, s * 0.055)
        L.path(d, "none", BONE, s * 0.032)
    # arms: one waving, one holding the crisp
    bone_line(L, [(cx - 0.18 * s, cy + 0.14 * s), (cx - 0.36 * s, cy + 0.32 * s), (cx - 0.44 * s, cy + 0.08 * s)], s * 0.035)
    bone_line(L, [(cx + 0.18 * s, cy + 0.14 * s), (cx + 0.36 * s, cy + 0.3 * s), (cx + 0.26 * s, cy + 0.02 * s)], s * 0.035)
    # the crisp
    cxp, cyp = cx + 0.24 * s, cy - 0.03 * s
    L.ellipse(cxp, cyp, 0.12 * s, 0.08 * s, crisp, INK, o * 1.2, rot=-20)
    for k in range(3):
        L.path(f"M {cxp - 0.08 * s:.2f} {cyp - 0.03 * s + k * 0.03 * s:.2f} q {0.04 * s:.2f} {-0.02 * s:.2f} {0.16 * s:.2f} {0.0:.2f}", "none",
               "#b9781e", o * 0.8)
    # skull
    hx, hy = cx, cy - 0.16 * s
    L.path(f"M {hx - 0.25 * s:.2f} {hy + 0.02 * s:.2f} A {0.26 * s:.2f} {0.27 * s:.2f} 0 1 1 {hx + 0.25 * s:.2f} {hy + 0.02 * s:.2f} "
           f"L {hx + 0.2 * s:.2f} {hy + 0.13 * s:.2f} Q {hx + 0.16 * s:.2f} {hy + 0.26 * s:.2f} {hx:.2f} {hy + 0.27 * s:.2f} "
           f"Q {hx - 0.16 * s:.2f} {hy + 0.26 * s:.2f} {hx - 0.2 * s:.2f} {hy + 0.13 * s:.2f} Z", BONE, INK, o * 1.4)
    L.ellipse(hx - 0.08 * s, hy - 0.12 * s, 0.07 * s, 0.03 * s, "#ffffff", op=0.55)
    for sx in (-1, 1):
        L.ellipse(hx + sx * 0.1 * s, hy - 0.01 * s, 0.075 * s, 0.085 * s, INK)
        L.circle(hx + sx * 0.1 * s + 0.022 * s, hy - 0.035 * s, 0.022 * s, "#ffffff")
    L.poly([(hx, hy + 0.06 * s), (hx - 0.03 * s, hy + 0.11 * s), (hx + 0.03 * s, hy + 0.11 * s)], INK)
    # the grin
    L.path(f"M {hx - 0.16 * s:.2f} {hy + 0.13 * s:.2f} Q {hx:.2f} {hy + 0.3 * s:.2f} {hx + 0.16 * s:.2f} {hy + 0.13 * s:.2f} "
           f"Q {hx:.2f} {hy + 0.17 * s:.2f} {hx - 0.16 * s:.2f} {hy + 0.13 * s:.2f} Z", INK)
    for k in range(-3, 4):
        x = hx + k * 0.038 * s
        top = hy + 0.15 * s + (0.02 - abs(k) * 0.006) * s
        L.rect(x - 0.015 * s, top, 0.03 * s, 0.035 * s, BONE, rx=0.006 * s)


def bat(L, cx, cy, s, body="#2a1438", belly="#4a2a62", eye="#ffe37a", cls=""):
    """Batsy: a round cartoon bat with big shiny eyes, two tiny fangs and scalloped wings."""
    w = s * 0.62
    for sx in (-1, 1):
        d = (f"M {cx + sx * 0.12 * s:.2f} {cy - 0.06 * s:.2f} Q {cx + sx * 0.45 * s:.2f} {cy - 0.32 * s:.2f} {cx + sx * w:.2f} {cy - 0.12 * s:.2f} "
             f"Q {cx + sx * 0.52 * s:.2f} {cy + 0.0 * s:.2f} {cx + sx * 0.5 * s:.2f} {cy + 0.1 * s:.2f} "
             f"Q {cx + sx * 0.42 * s:.2f} {cy + 0.02 * s:.2f} {cx + sx * 0.34 * s:.2f} {cy + 0.12 * s:.2f} "
             f"Q {cx + sx * 0.27 * s:.2f} {cy + 0.04 * s:.2f} {cx + sx * 0.16 * s:.2f} {cy + 0.12 * s:.2f} Z")
        L.path(d, body, INK, s * 0.012, cls=cls)
        for k in (0.3, 0.42):
            L.path(f"M {cx + sx * 0.14 * s:.2f} {cy - 0.04 * s:.2f} L {cx + sx * k * s:.2f} {cy + 0.06 * s:.2f}", "none", belly, s * 0.012)
    L.ellipse(cx, cy + 0.04 * s, 0.2 * s, 0.22 * s, body, INK, s * 0.012, cls=cls)
    L.ellipse(cx, cy + 0.1 * s, 0.12 * s, 0.13 * s, belly)
    for sx in (-1, 1):
        L.poly([(cx + sx * 0.07 * s, cy - 0.12 * s), (cx + sx * 0.17 * s, cy - 0.32 * s), (cx + sx * 0.19 * s, cy - 0.08 * s)], body, INK,
               s * 0.012, cls=cls)
        L.ellipse(cx + sx * 0.075 * s, cy - 0.02 * s, 0.06 * s, 0.07 * s, eye, INK, s * 0.01)
        L.circle(cx + sx * 0.075 * s, cy - 0.01 * s, 0.035 * s, INK)
        L.circle(cx + sx * 0.075 * s + 0.015 * s, cy - 0.03 * s, 0.013 * s, "#ffffff")
        L.ellipse(cx + sx * 0.14 * s, cy + 0.06 * s, 0.03 * s, 0.018 * s, "#e07aa8", op=0.7)
    L.path(f"M {cx - 0.05 * s:.2f} {cy + 0.07 * s:.2f} Q {cx:.2f} {cy + 0.11 * s:.2f} {cx + 0.05 * s:.2f} {cy + 0.07 * s:.2f}", "none", INK,
           s * 0.012)
    for sx in (-1, 1):
        L.poly([(cx + sx * 0.03 * s, cy + 0.085 * s), (cx + sx * 0.01 * s, cy + 0.085 * s), (cx + sx * 0.02 * s, cy + 0.12 * s)], "#ffffff")


def ghost(L, cx, cy, s, fill="#f4f6f2", cheek="#f2a0b8", eye=INK, cls="", outline=None, face=True):
    w = s * 0.34
    top = cy - s * 0.5
    bot = cy + s * 0.42
    d = (f"M {cx - w:.2f} {cy:.2f} A {w:.2f} {w:.2f} 0 0 1 {cx + w:.2f} {cy:.2f} L {cx + w:.2f} {bot - s * 0.06:.2f} "
         f"Q {cx + w * 0.75:.2f} {bot + s * 0.06:.2f} {cx + w * 0.5:.2f} {bot - s * 0.04:.2f} Q {cx + w * 0.25:.2f} {bot + s * 0.06:.2f} "
         f"{cx:.2f} {bot - s * 0.04:.2f} Q {cx - w * 0.25:.2f} {bot + s * 0.06:.2f} {cx - w * 0.5:.2f} {bot - s * 0.04:.2f} "
         f"Q {cx - w * 0.75:.2f} {bot + s * 0.06:.2f} {cx - w:.2f} {bot - s * 0.06:.2f} Z")
    L.path(d, fill, outline, s * 0.02 if outline else 0, cls=cls)
    if face:
        for sx in (-1, 1):
            L.ellipse(cx + sx * 0.11 * s, cy - 0.04 * s, 0.045 * s, 0.065 * s, eye)
            L.circle(cx + sx * 0.11 * s + 0.014 * s, cy - 0.07 * s, 0.014 * s, "#ffffff")
            L.ellipse(cx + sx * 0.2 * s, cy + 0.06 * s, 0.045 * s, 0.025 * s, cheek, op=0.75)
        L.path(f"M {cx - 0.04 * s:.2f} {cy + 0.06 * s:.2f} Q {cx:.2f} {cy + 0.1 * s:.2f} {cx + 0.04 * s:.2f} {cy + 0.06 * s:.2f}", "none", eye,
               s * 0.016)
    return d


def ghost_cow(L, cx, cy, s, spot="#d86a90", nose="#f5b8c8", bell=True):
    """Moo-ghost, the dairy's mascot: a little ghost with cow spots, stubby horns, floppy ears and a gilt bell."""
    for sx in (-1, 1):
        L.path(f"M {cx + sx * 0.18 * s:.2f} {cy - 0.36 * s:.2f} q {sx * 0.06 * s:.2f} {-0.12 * s:.2f} {sx * 0.12 * s:.2f} {-0.1 * s:.2f} "
               f"q {-sx * 0.02 * s:.2f} {0.08 * s:.2f} {-sx * 0.08 * s:.2f} {0.14 * s:.2f} Z", "#efe2b8", INK, s * 0.012)
        L.ellipse(cx + sx * 0.36 * s, cy - 0.2 * s, 0.11 * s, 0.05 * s, "#f6f4f0", INK, s * 0.012, rot=sx * 25)
    d = ghost(L, cx, cy, s, fill="#f8f6f2", outline=INK, face=False)
    clip = L.clip(f'<path d="{d}"/>')
    L.begin(extra=clip)
    for x, y, r in ((-0.22, -0.28, 0.12), (0.26, 0.05, 0.13), (-0.2, 0.3, 0.1), (0.12, -0.42, 0.07)):
        L.ellipse(cx + x * s, cy + y * s, r * s, r * s * 0.8, spot, rot=30)
    L.end()
    for sx in (-1, 1):
        L.ellipse(cx + sx * 0.11 * s, cy - 0.12 * s, 0.045 * s, 0.06 * s, INK)
        L.circle(cx + sx * 0.11 * s + 0.014 * s, cy - 0.145 * s, 0.014 * s, "#ffffff")
    L.ellipse(cx, cy + 0.02 * s, 0.17 * s, 0.1 * s, nose, INK, s * 0.01)
    for sx in (-1, 1):
        L.ellipse(cx + sx * 0.06 * s, cy + 0.02 * s, 0.022 * s, 0.03 * s, "#a0526a")
    L.path(f"M {cx - 0.04 * s:.2f} {cy + 0.085 * s:.2f} Q {cx:.2f} {cy + 0.11 * s:.2f} {cx + 0.04 * s:.2f} {cy + 0.085 * s:.2f}", "none", INK,
           s * 0.012)
    if bell:
        L.path(f"M {cx - 0.14 * s:.2f} {cy + 0.15 * s:.2f} Q {cx:.2f} {cy + 0.21 * s:.2f} {cx + 0.14 * s:.2f} {cy + 0.15 * s:.2f}", "none",
               CRIMSON, s * 0.03)
        L.path(f"M {cx - 0.05 * s:.2f} {cy + 0.27 * s:.2f} Q {cx - 0.05 * s:.2f} {cy + 0.18 * s:.2f} {cx:.2f} {cy + 0.18 * s:.2f} "
               f"Q {cx + 0.05 * s:.2f} {cy + 0.18 * s:.2f} {cx + 0.05 * s:.2f} {cy + 0.27 * s:.2f} Z", L.gilt(), INK, s * 0.008, cls="foil emb")


RAVEN = [(-0.5, -0.28), (-0.38, -0.36), (-0.3, -0.43), (-0.2, -0.45), (-0.12, -0.4), (-0.08, -0.31), (0.04, -0.25), (0.18, -0.19),
         (0.3, -0.1), (0.42, 0.04), (0.6, 0.22), (0.62, 0.26), (0.5, 0.24), (0.54, 0.3), (0.4, 0.22), (0.26, 0.14), (0.12, 0.14),
         (0.0, 0.12), (-0.1, 0.06), (-0.17, -0.04), (-0.22, -0.16), (-0.3, -0.24), (-0.38, -0.27)]


def raven(L, cx, cy, s, fill, cls="", eye=None):
    """A raven perched, facing left, s tall: heavy beak, ruffled throat, long tail, two clawed feet."""
    L.poly([(cx + u * s, cy + v * s) for u, v in RAVEN], fill, cls=cls)
    for k in range(4):
        x, y = cx + (-0.2 + k * 0.03) * s, cy + (-0.14 + k * 0.05) * s
        L.poly([(x, y), (x - 0.05 * s, y + 0.03 * s), (x + 0.01 * s, y + 0.02 * s)], fill, cls=cls)
    L.path(f"M {cx - 0.06 * s:.2f} {cy - 0.2 * s:.2f} Q {cx + 0.16 * s:.2f} {cy - 0.12 * s:.2f} {cx + 0.42 * s:.2f} {cy + 0.12 * s:.2f}",
           "none", "#000", s * 0.014, op=0.35)
    L.path(f"M {cx + 0.02 * s:.2f} {cy - 0.08 * s:.2f} Q {cx + 0.16 * s:.2f} {cy - 0.02 * s:.2f} {cx + 0.34 * s:.2f} {cy + 0.14 * s:.2f}",
           "none", "#000", s * 0.01, op=0.3)
    for k in (-0.02, 0.08):
        x0, y0 = cx + k * s, cy + 0.12 * s
        L.path(f"M {x0:.2f} {y0:.2f} L {x0 - 0.02 * s:.2f} {y0 + 0.16 * s:.2f} M {x0 - 0.02 * s:.2f} {y0 + 0.16 * s:.2f} "
               f"l {-0.06 * s:.2f} {0.02 * s:.2f} M {x0 - 0.02 * s:.2f} {y0 + 0.16 * s:.2f} l {0.05 * s:.2f} {0.03 * s:.2f}",
               "none", fill, s * 0.02, cls=cls)
    L.circle(cx - 0.27 * s, cy - 0.37 * s, 0.022 * s, eye or "#f8e8b0")


def gummy_bat(L, cx, cy, s, col, rot=0):
    """A translucent gummy candy in a bat shape, with a shine."""
    pts = [(-1, 0), (-0.62, -0.4), (-0.42, -0.1), (-0.18, -0.24), (-0.1, -0.48), (0, -0.3), (0.1, -0.48), (0.18, -0.24), (0.42, -0.1),
           (0.62, -0.4), (1, 0), (0.6, 0.12), (0.3, 0.05), (0, 0.4), (-0.3, 0.05), (-0.6, 0.12)]
    ca, sa = math.cos(rot), math.sin(rot)
    L.poly([(cx + (u * ca - v * sa) * s * 0.5, cy + (u * sa + v * ca) * s * 0.5) for u, v in pts], col, "#000", s * 0.015, op=0.88)
    L.ellipse(cx - 0.12 * s, cy - 0.06 * s, 0.1 * s, 0.035 * s, "#ffffff", op=0.55, rot=math.degrees(rot) - 15)


def cat(L, cx, cy, s, fill="#0b0a0e", eye="#f2d24a", cls=""):
    """A sitting black cat seen from the front, tail curled round its paws, glowing eyes with slit pupils."""
    L.path(f"M {cx + 0.18 * s:.2f} {cy + 0.42 * s:.2f} Q {cx + 0.46 * s:.2f} {cy + 0.42 * s:.2f} {cx + 0.42 * s:.2f} {cy + 0.12 * s:.2f} "
           f"Q {cx + 0.4 * s:.2f} {cy - 0.04 * s:.2f} {cx + 0.48 * s:.2f} {cy - 0.12 * s:.2f}", "none", fill, s * 0.07, cls=cls)
    L.path(f"M {cx - 0.24 * s:.2f} {cy + 0.45 * s:.2f} Q {cx - 0.3 * s:.2f} {cy + 0.05 * s:.2f} {cx - 0.12 * s:.2f} {cy - 0.06 * s:.2f} "
           f"L {cx + 0.12 * s:.2f} {cy - 0.06 * s:.2f} Q {cx + 0.3 * s:.2f} {cy + 0.05 * s:.2f} {cx + 0.24 * s:.2f} {cy + 0.45 * s:.2f} Z",
           fill, cls=cls)
    L.ellipse(cx, cy - 0.2 * s, 0.2 * s, 0.17 * s, fill, cls=cls)
    for sx in (-1, 1):
        L.poly([(cx + sx * 0.18 * s, cy - 0.24 * s), (cx + sx * 0.2 * s, cy - 0.46 * s), (cx + sx * 0.05 * s, cy - 0.33 * s)], fill, cls=cls)
        L.ellipse(cx + sx * 0.08 * s, cy - 0.22 * s, 0.05 * s, 0.035 * s, eye)
        L.ellipse(cx + sx * 0.08 * s, cy - 0.22 * s, 0.012 * s, 0.032 * s, INK)
        for k in (-1, 1):
            L.line(cx + sx * 0.06 * s, cy - 0.14 * s, cx + sx * 0.3 * s, cy - 0.14 * s + k * 0.03 * s, "#8a8478", s * 0.006, op=0.8)


def window_candle(L, cx, cy, w, h, glow="#ffc35a", frame_col="#1a120c"):
    """A gothic lancet window lit from inside: warm panes, leading, a candle on the sill."""
    d = (f"M {cx - w / 2:.2f} {cy + h / 2:.2f} L {cx - w / 2:.2f} {cy - h * 0.1:.2f} Q {cx - w / 2:.2f} {cy - h / 2:.2f} {cx:.2f} {cy - h * 0.58:.2f} "
         f"Q {cx + w / 2:.2f} {cy - h / 2:.2f} {cx + w / 2:.2f} {cy - h * 0.1:.2f} L {cx + w / 2:.2f} {cy + h / 2:.2f} Z")
    L.path(d, L.rad([(0, "#fff0c0"), (0.45, glow), (1, "#8a3a10")], cy=0.7, r=0.75), frame_col, w * 0.06)
    clip = L.clip(f'<path d="{d}"/>')
    L.begin(extra=clip)
    for k in range(1, 3):
        L.line(cx - w / 2 + k * w / 3, cy - h, cx - w / 2 + k * w / 3, cy + h, frame_col, w * 0.025)
    for k in range(1, 4):
        L.line(cx - w, cy - h / 2 + k * h / 4, cx + w, cy - h / 2 + k * h / 4, frame_col, w * 0.025)
    L.end()
    L.rect(cx - w * 0.6, cy + h / 2 - h * 0.02, w * 1.2, h * 0.06, frame_col)
    # the candle
    L.rect(cx - w * 0.05, cy + h * 0.22, w * 0.1, h * 0.26, "#f2e6c8")
    L.ellipse(cx, cy + h * 0.17, w * 0.035, h * 0.05, "#fff6c8")
    L.circle(cx, cy + h * 0.17, w * 0.18, "#ffdd88", cls="fx", op=0.35)


def lantern(L, cx, cy, s, body="#c02428", cap="#141014", glow="#ffd46a", cls=""):
    """A paper chochin lantern, glowing."""
    L.circle(cx, cy, s * 0.62, L.rad([(0, glow, 0.6), (1, glow, 0.0)]), cls="fx")
    L.rect(cx - 0.17 * s, cy - 0.48 * s, 0.34 * s, 0.1 * s, cap, rx=s * 0.02, cls=cls)
    L.rect(cx - 0.17 * s, cy + 0.38 * s, 0.34 * s, 0.1 * s, cap, rx=s * 0.02, cls=cls)
    L.line(cx, cy - 0.62 * s, cx, cy - 0.48 * s, cap, s * 0.025)
    L.ellipse(cx, cy, 0.32 * s, 0.4 * s, L.rad([(0, "#ffb070"), (0.5, body), (1, "#5a0a10")], cx=0.45, cy=0.4, r=0.6), INK, s * 0.012)
    for k in range(-3, 4):
        y = cy + k * 0.1 * s
        rx = 0.32 * s * math.sqrt(max(0.0, 1 - (k * 0.1 / 0.4) ** 2))
        L.ellipse(cx, y, rx, 0.012 * s, "none", "#3a0a0e", s * 0.008, op=0.6)


def barley(L, cx, cy, s, fill, cls="", lean=0.0):
    """An ear of barley, s long, its awns fanning up."""
    a = lean
    ux, uy = math.sin(a), -math.cos(a)
    L.line(cx, cy, cx - ux * s * 0.55, cy - uy * s * 0.55, fill, s * 0.02, cls=cls)
    for i in range(7):
        t = 0.05 + i * 0.065
        bx, by = cx + ux * t * s, cy + uy * t * s
        for side in (-1, 1):
            px, py = -uy * side, ux * side
            gx, gy = bx + px * s * 0.035, by + py * s * 0.035
            L.ellipse(gx, gy, s * 0.03, s * 0.055, fill, cls=cls, rot=math.degrees(a) + side * 25)
            L.line(gx, gy, gx + (ux * 0.9 + px * 0.25) * s * 0.3, gy + (uy * 0.9 + py * 0.25) * s * 0.3, fill, s * 0.006, cls=cls)


def leaf(L, cx, cy, length, width, ang, fill, vein=None, cls=""):
    ca, sa = math.cos(ang), math.sin(ang)
    pts = []
    for i in range(17):
        t = i / 16
        w = math.sin(t * PI) ** 0.9 * width
        pts.append(((t - 0.5) * length, w))
    pts += [(u, -w) for u, w in reversed(pts)]
    L.poly([(cx + u * ca - v * sa, cy + u * sa + v * ca) for u, v in pts], fill, cls=cls)
    if vein:
        L.line(cx - 0.5 * length * ca, cy - 0.5 * length * sa, cx + 0.5 * length * ca, cy + 0.5 * length * sa, vein, width * 0.12, op=0.7)


def lemon(L, cx, cy, r, cls=""):
    L.ellipse(cx, cy, r * 1.25, r, L.rad([(0, "#fff3a0"), (0.6, "#f2d23a"), (1, "#c09a18")], cx=0.4, cy=0.35), INK, r * 0.05, cls=cls)
    L.circle(cx + r * 1.25, cy, r * 0.12, "#c09a18")
    leaf(L, cx - r * 0.9, cy - r * 0.8, r * 1.1, r * 0.3, -0.6, "#4a7a2a", "#2a4a18")


def lemon_slice(L, cx, cy, r):
    L.circle(cx, cy, r, "#f2d23a", INK, r * 0.05)
    L.circle(cx, cy, r * 0.85, "#fff7c6")
    for i in range(8):
        a0 = i * PI / 4 + 0.08
        a1 = (i + 1) * PI / 4 - 0.08
        L.path(f"M {cx:.2f} {cy:.2f} L {cx + math.cos(a0) * r * 0.78:.2f} {cy + math.sin(a0) * r * 0.78:.2f} "
               f"A {r * 0.78:.2f} {r * 0.78:.2f} 0 0 1 {cx + math.cos(a1) * r * 0.78:.2f} {cy + math.sin(a1) * r * 0.78:.2f} Z", "#f7dc5a")


def strawberry(L, cx, cy, s):
    L.path(f"M {cx - 0.3 * s:.2f} {cy - 0.2 * s:.2f} Q {cx:.2f} {cy - 0.36 * s:.2f} {cx + 0.3 * s:.2f} {cy - 0.2 * s:.2f} "
           f"Q {cx + 0.32 * s:.2f} {cy + 0.2 * s:.2f} {cx:.2f} {cy + 0.42 * s:.2f} Q {cx - 0.32 * s:.2f} {cy + 0.2 * s:.2f} {cx - 0.3 * s:.2f} {cy - 0.2 * s:.2f} Z",
           L.rad([(0, "#ff7a8a"), (1, "#a8142c")], cx=0.4, cy=0.35), INK, s * 0.02)
    rnd = random.Random(int(cx * 7 + cy))
    for _ in range(12):
        L.ellipse(cx + rnd.uniform(-0.2, 0.2) * s, cy + rnd.uniform(-0.12, 0.25) * s, s * 0.012, s * 0.02, "#ffe39a")
    for i in range(5):
        leaf(L, cx + math.cos(-PI / 2 + (i - 2) * 0.5) * s * 0.12, cy - 0.28 * s + abs(i - 2) * 0.02 * s, s * 0.22, s * 0.05,
             -PI / 2 + (i - 2) * 0.5, "#3e8a3a")


def noodle_bowl(L, cx, cy, s, bowl="#7a1222", inner="#2a0a10"):
    """A steaming ramen bowl with chashu, a soft egg, nori, naruto and spring onion."""
    for k in (-1, 0, 1):
        x = cx + k * 0.16 * s
        L.path(f"M {x:.2f} {cy - 0.12 * s:.2f} q {0.06 * s:.2f} {-0.1 * s:.2f} 0 {-0.2 * s:.2f} q {-0.06 * s:.2f} {-0.1 * s:.2f} 0 {-0.2 * s:.2f}",
               "none", "#f4ece0", s * 0.025, op=0.75)
    L.ellipse(cx, cy, 0.44 * s, 0.12 * s, inner)
    L.ellipse(cx, cy + 0.01 * s, 0.4 * s, 0.09 * s, "#c9802e")
    for i in range(6):
        L.path(f"M {cx - 0.32 * s + i * 0.1 * s:.2f} {cy:.2f} q {0.03 * s:.2f} {-0.04 * s:.2f} {0.06 * s:.2f} 0 t {0.06 * s:.2f} 0", "none",
               "#f2d48a", s * 0.015)
    L.ellipse(cx - 0.2 * s, cy - 0.01 * s, 0.1 * s, 0.05 * s, "#b86a4a", INK, s * 0.006)
    L.ellipse(cx + 0.06 * s, cy - 0.02 * s, 0.08 * s, 0.05 * s, "#fffaf0", INK, s * 0.006)
    L.ellipse(cx + 0.06 * s, cy - 0.02 * s, 0.04 * s, 0.03 * s, "#f2a21e")
    L.ellipse(cx + 0.22 * s, cy, 0.06 * s, 0.035 * s, "#fffaf0", INK, s * 0.005)
    L.path(f"M {cx + 0.19 * s:.2f} {cy:.2f} q {0.03 * s:.2f} {-0.03 * s:.2f} {0.06 * s:.2f} 0", "none", "#e2507a", s * 0.008)
    L.rect(cx + 0.27 * s, cy - 0.16 * s, 0.09 * s, 0.15 * s, "#1c2a1c")     # a sheet of nori standing up
    L.path(f"M {cx - 0.44 * s:.2f} {cy:.2f} Q {cx - 0.4 * s:.2f} {cy + 0.42 * s:.2f} {cx:.2f} {cy + 0.42 * s:.2f} "
           f"Q {cx + 0.4 * s:.2f} {cy + 0.42 * s:.2f} {cx + 0.44 * s:.2f} {cy:.2f} A {0.44 * s:.2f} {0.12 * s:.2f} 0 0 1 {cx - 0.44 * s:.2f} {cy:.2f} Z",
           bowl, INK, s * 0.012)
    L.path(f"M {cx - 0.3 * s:.2f} {cy + 0.2 * s:.2f} Q {cx:.2f} {cy + 0.3 * s:.2f} {cx + 0.3 * s:.2f} {cy + 0.2 * s:.2f}", "none", GOLD, s * 0.02,
           cls="foil")
    for sx in (-0.05, 0.05):
        L.line(cx + 0.1 * s + sx * s, cy - 0.45 * s, cx + 0.42 * s + sx * s, cy + 0.02 * s, "#d8b070", s * 0.018)


def pumpkin(L, cx, cy, s, face=True):
    for k, rx in ((-1, 0.2), (1, 0.2), (0, 0.22)):
        L.ellipse(cx + k * 0.16 * s, cy, rx * s, 0.3 * s, L.rad([(0, "#ffb54a"), (1, "#c2560e")], cx=0.4, cy=0.35), INK, s * 0.012)
    L.path(f"M {cx:.2f} {cy - 0.28 * s:.2f} q {0.02 * s:.2f} {-0.1 * s:.2f} {0.08 * s:.2f} {-0.14 * s:.2f}", "none", "#4a5a22", s * 0.05)
    if face:
        for sx in (-1, 1):
            L.poly([(cx + sx * 0.14 * s, cy - 0.12 * s), (cx + sx * 0.05 * s, cy - 0.02 * s), (cx + sx * 0.2 * s, cy - 0.02 * s)], "#3a1404")
        L.path(f"M {cx - 0.18 * s:.2f} {cy + 0.06 * s:.2f} Q {cx:.2f} {cy + 0.2 * s:.2f} {cx + 0.18 * s:.2f} {cy + 0.06 * s:.2f} "
               f"Q {cx:.2f} {cy + 0.12 * s:.2f} {cx - 0.18 * s:.2f} {cy + 0.06 * s:.2f} Z", "#3a1404")


def octopus(L, cx, cy, s, fill="#e2604a"):
    """Tako-chan: a cheerful little octopus in a headband (the takoyaki boat's mascot)."""
    for i in range(6):
        a = PI * (0.15 + i * 0.14)
        L.path(f"M {cx + math.cos(a) * 0.12 * s:.2f} {cy + 0.1 * s:.2f} q {math.cos(a) * 0.25 * s:.2f} {0.15 * s:.2f} {math.cos(a) * 0.3 * s:.2f} {0.3 * s:.2f}",
               "none", fill, s * 0.07)
    L.ellipse(cx, cy - 0.06 * s, 0.25 * s, 0.24 * s, fill, INK, s * 0.012)
    L.rect(cx - 0.26 * s, cy - 0.16 * s, 0.52 * s, 0.06 * s, "#f4f0e6", INK, s * 0.006)
    for sx in (-1, 1):
        L.circle(cx + sx * 0.09 * s, cy - 0.02 * s, 0.035 * s, INK)
        L.circle(cx + sx * 0.09 * s + 0.01 * s, cy - 0.035 * s, 0.012 * s, "#ffffff")
    L.ellipse(cx, cy + 0.08 * s, 0.05 * s, 0.035 * s, "#9a2a1e")


def tofu(L, cx, cy, s):
    """Tofu-kun, the miso cup's mascot: a smiling cube with a wakame leaf for hair."""
    L.poly([(cx - 0.3 * s, cy - 0.15 * s), (cx + 0.1 * s, cy - 0.15 * s), (cx + 0.3 * s, cy - 0.3 * s), (cx - 0.1 * s, cy - 0.3 * s)], "#ffffff",
           INK, s * 0.012)
    L.poly([(cx + 0.1 * s, cy - 0.15 * s), (cx + 0.3 * s, cy - 0.3 * s), (cx + 0.3 * s, cy + 0.1 * s), (cx + 0.1 * s, cy + 0.25 * s)], "#d8d2c4",
           INK, s * 0.012)
    L.rect(cx - 0.3 * s, cy - 0.15 * s, 0.4 * s, 0.4 * s, "#f6f2ea", INK, s * 0.012)
    for sx in (-1, 1):
        L.circle(cx - 0.1 * s + sx * 0.08 * s, cy + 0.02 * s, 0.025 * s, INK)
        L.ellipse(cx - 0.1 * s + sx * 0.13 * s, cy + 0.08 * s, 0.03 * s, 0.018 * s, "#f2a0b8", op=0.8)
    L.path(f"M {cx - 0.14 * s:.2f} {cy + 0.08 * s:.2f} Q {cx - 0.1 * s:.2f} {cy + 0.12 * s:.2f} {cx - 0.06 * s:.2f} {cy + 0.08 * s:.2f}", "none", INK,
           s * 0.012)
    leaf(L, cx - 0.02 * s, cy - 0.34 * s, 0.32 * s, 0.07 * s, -0.4, "#2a5a2a", "#183a18")


def pudding_mascot(L, cx, cy, s):
    L.path(f"M {cx - 0.3 * s:.2f} {cy + 0.3 * s:.2f} L {cx - 0.2 * s:.2f} {cy - 0.15 * s:.2f} Q {cx:.2f} {cy - 0.24 * s:.2f} {cx + 0.2 * s:.2f} {cy - 0.15 * s:.2f} "
           f"L {cx + 0.3 * s:.2f} {cy + 0.3 * s:.2f} Q {cx:.2f} {cy + 0.38 * s:.2f} {cx - 0.3 * s:.2f} {cy + 0.3 * s:.2f} Z", "#f6cf5a", INK, s * 0.012)
    L.path(f"M {cx - 0.21 * s:.2f} {cy - 0.12 * s:.2f} Q {cx:.2f} {cy - 0.3 * s:.2f} {cx + 0.21 * s:.2f} {cy - 0.12 * s:.2f} "
           f"Q {cx + 0.16 * s:.2f} {cy - 0.02 * s:.2f} {cx + 0.1 * s:.2f} {cy - 0.06 * s:.2f} Q {cx + 0.02 * s:.2f} {cy + 0.04 * s:.2f} {cx - 0.04 * s:.2f} {cy - 0.06 * s:.2f} "
           f"Q {cx - 0.12 * s:.2f} {cy + 0.02 * s:.2f} {cx - 0.21 * s:.2f} {cy - 0.12 * s:.2f} Z", "#6a2a0a")
    for sx in (-1, 1):
        L.circle(cx + sx * 0.08 * s, cy + 0.08 * s, 0.025 * s, INK)
        L.ellipse(cx + sx * 0.15 * s, cy + 0.14 * s, 0.035 * s, 0.02 * s, "#f08a8a", op=0.8)
    L.path(f"M {cx - 0.04 * s:.2f} {cy + 0.15 * s:.2f} Q {cx:.2f} {cy + 0.19 * s:.2f} {cx + 0.04 * s:.2f} {cy + 0.15 * s:.2f}", "none", INK,
           s * 0.012)


def tombstone_shape(cx, cy, w, h):
    return (f"M {cx - w / 2:.2f} {cy + h / 2:.2f} L {cx - w / 2:.2f} {cy - h / 2 + w / 2:.2f} A {w / 2:.2f} {w / 2:.2f} 0 0 1 "
            f"{cx + w / 2:.2f} {cy - h / 2 + w / 2:.2f} L {cx + w / 2:.2f} {cy + h / 2:.2f} Z")


def seigaiha(L, x, y, w, h, fg, bg, r):
    """Wave scales (seigaiha) filling a box."""
    body = (f'<rect width="{2 * r}" height="{r}" fill="{bg}"/>'
            + "".join(f'<circle cx="{cx}" cy="{cy}" r="{rr}" fill="none" stroke="{fg}" stroke-width="{r * 0.08}"/>'
                      for cx, cy in ((0, r), (2 * r, r), (r, r * 0.5), (r, r * 1.5)) for rr in (r * 0.95, r * 0.7, r * 0.45)))
    L.rect(x, y, w, h, L.pattern(2 * r, r, body))


def checker(L, x, y, w, h, a, b, sq):
    body = f'<rect width="{2 * sq}" height="{2 * sq}" fill="{a}"/><rect width="{sq}" height="{sq}" fill="{b}"/><rect x="{sq}" y="{sq}" width="{sq}" height="{sq}" fill="{b}"/>'
    L.rect(x, y, w, h, L.pattern(2 * sq, 2 * sq, body))


def dots(L, x, y, w, h, col, step, r, op=1.0):
    body = f'<circle cx="{step / 2}" cy="{step / 2}" r="{r}" fill="{col}" opacity="{op}"/><circle cx="0" cy="0" r="{r}" fill="{col}" opacity="{op}"/><circle cx="{step}" cy="{step}" r="{r}" fill="{col}" opacity="{op}"/><circle cx="{step}" cy="0" r="{r}" fill="{col}" opacity="{op}"/><circle cx="0" cy="{step}" r="{r}" fill="{col}" opacity="{op}"/>'
    L.rect(x, y, w, h, L.pattern(step, step, body), cls="fx" if op < 1 else "")


def stripes(L, x, y, w, h, a, b, period, angle=0):
    body = f'<rect width="{period}" height="{period}" fill="{a}"/><rect width="{period / 2}" height="{period}" fill="{b}"/>'
    L.rect(x, y, w, h, L.pattern(period, period, body, f"rotate({angle})" if angle else ""))
