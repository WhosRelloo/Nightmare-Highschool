"""Thornrose: the health bar v4 the owner picked (concept C of make_health_v4_concepts.py), as game pieces, plus the
posture rail restyled to match. Baked with make_health_pbr's shader.

Pieces (art/ui/hud/out/thornrose/), for KitHud's 600 x 50 health bar and 600 x 24 posture rail:
  ThornFrame.png    2400x300  the briar: two twisted black-iron vines with brass-tipped thorns along the top and the
                              bottom, a brass bead round the window, closed rosebud ends. Window x 150..2250, y 120..200
                              (transparent). Drawn 600 x 75 in game, 15 px above the bar's box.
  ThornVelvet.png    512x96   greyscale crimson-velvet fill (tiles; tinted per form)
  ThornRose.png      512x512  the iron rose (three rings of petals, brass petal edges) with a round hole for the glass
  ThornGlass.png     256x256  greyscale glass heart (tinted per form; sits behind the rose)
  PostureBriar.png  2400x96   the posture rail in the same briar: a twisted-iron band with small thorns, rosebud ends,
                              an iron leaf cradle under the rose. Window x 150..2250, y 28..68, like PostureFrame.
  preview.png                 the pieces placed as KitHud places them, in a few states

  python make_health_thornrose.py
"""
import importlib.util
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


hp = _load("hp", "make_health_pbr.py")
v4 = _load("v4", "make_health_v4_concepts.py")
mask, bake, glass_disc, to_img, tint, tiled, font, glow = v4.mask, v4.bake, v4.glass_disc, v4.to_img, v4.tint, v4.tiled, v4.font, v4.glow

OUT = HERE / "out" / "thornrose"
OUT.mkdir(parents=True, exist_ok=True)
POSTURE = HERE / "out" / "posture"
W = 2400
FH, FCY = 300, 160                    # frame canvas height and window centre (4x)
X0, X1, Y0, Y1 = 150, 2250, 120, 200  # window (4x)


def save(img, name):
    img.save(OUT / name, optimize=True)
    return OUT / name


def bud_pts(bx, cy, side, length=140, width=50):
    """A closed rosebud: round at the bar end, pointed outward."""
    pts = []
    for k in range(61):
        t = k / 60 * 2 * math.pi
        x = length / 2 * (1 - math.cos(t))
        y = width * math.sin(t) * (1 - x / (length * 1.07))
        pts.append((bx + side * x, cy + y))
    return pts


# ---------------------------------------------------------------- health frame
def frame():
    H, cy = FH, FCY

    def vines(d, s):
        for base in (Y0 - 26, Y1 + 26):
            for ph in (0, math.pi):
                pts = []
                for x in range(110, W - 110, 6):
                    if abs(x - W / 2) < 150:   # the rose covers the middle
                        if pts:
                            d.line(pts, fill=255, width=int(13 * s), joint="curve")
                            pts = []
                        continue
                    pts.append((x * s, (base + 9 * math.sin(x / 70 + ph)) * s))
                if pts:
                    d.line(pts, fill=255, width=int(13 * s), joint="curve")

    def thorn_list():
        out = []
        for base, sgn, ln in ((Y0 - 26, -1, 36), (Y1 + 26, 1, 18)):   # the bottom thorns are short: the posture rail hangs there
            for j, x in enumerate(range(230, W - 230, 120)):
                if abs(x - W / 2) < 210:
                    continue
                y = base + 9 * math.sin(x / 70)
                lean = 1 if j % 2 == 0 else -1
                out.append((x, y, x + lean * ln * 0.72, y + sgn * ln))
        return out

    def thorns(d, s):
        for x, y, tx, ty in thorn_list():
            d.polygon([((x - 15) * s, y * s), ((x + 15) * s, y * s), (tx * s, ty * s)], fill=255)

    def tips(d, s):
        for x, y, tx, ty in thorn_list():
            mx, my = tx * 0.6 + x * 0.4, ty * 0.6 + y * 0.4
            d.polygon([((mx - 6) * s, my * s), ((mx + 6) * s, my * s), (tx * s, ty * s)], fill=255)

    def bead(d, s):
        d.rectangle(((X0 - 10) * s, (Y0 - 10) * s, (X1 + 10) * s, (Y1 + 10) * s), fill=255)
        d.rectangle((X0 * s, Y0 * s, X1 * s, Y1 * s), fill=0)

    def buds(d, s):
        for side in (-1, 1):
            bx = 150 if side < 0 else W - 150
            d.polygon([(p[0] * s, p[1] * s) for p in bud_pts(bx, cy, side)], fill=255)
            for dy in (-1, 1):
                d.polygon([(bx * s, (cy + dy * 26) * s), ((bx + side * 78) * s, (cy + dy * 50) * s), ((bx + side * 44) * s, (cy + dy * 14) * s)], fill=255)

    def bud_lines(d, s):
        for side in (-1, 1):
            bx = 150 if side < 0 else W - 150
            for ox, r in ((34, 30), (68, 20)):
                cx = bx + side * ox
                a0, a1 = (100, 260) if side < 0 else (-80, 80)
                d.arc(((cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s), a0, a1, fill=255, width=int(6 * s))

    win = mask(W, H, lambda d, s: d.rectangle((X0 * s, Y0 * s, X1 * s, Y1 * s), fill=255))
    backing = mask(W, H, lambda d, s: d.rectangle((140 * s, (Y0 - 6) * s, (W - 140) * s, (Y1 + 6) * s), fill=255))
    layers = [
        (np.clip(backing - win, 0, 1), 0.25, 0.2, 8, "blackiron"),
        (mask(W, H, vines), 0.5, 0.45, 8, "blackiron"),
        (mask(W, H, thorns), 0.5, 0.35, 5, "blackiron"),
        (mask(W, H, tips), 0.7, 0.2, 3, "brass"),
        (mask(W, H, bead), 0.55, 0.25, 4, "brass"),
        (mask(W, H, buds), 0.5, 0.5, 26, "blackiron"),
        (mask(W, H, bud_lines), 0.75, 0.1, 2, "brass"),
    ]
    return save(bake(W, H, layers, seed=31), "ThornFrame.png")


# ---------------------------------------------------------------- rose (8x of its 72.5 design px)
def rose():
    S = 512
    k = S / 290           # the 4x concept rose spanned 290 px
    c = S / 2
    rings = ((7, 126, 52), (6, 98, 46), (5, 72, 40))

    def petals(d, s):
        for ring, (n, rad, pr) in enumerate(rings):
            for j in range(n):
                a = j / n * 2 * math.pi + ring * 0.4
                px, py = c + math.cos(a) * rad * 0.62 * k, c + math.sin(a) * rad * 0.62 * k
                d.ellipse(((px - pr * k) * s, (py - pr * k) * s, (px + pr * k) * s, (py + pr * k) * s), fill=255)

    def edges(d, s):
        for ring, (n, rad, pr) in enumerate(rings):
            for j in range(n):
                a = j / n * 2 * math.pi + ring * 0.4
                px, py = c + math.cos(a) * rad * 0.62 * k, c + math.sin(a) * rad * 0.62 * k
                d.arc(((px - pr * k) * s, (py - pr * k) * s, (px + pr * k) * s, (py + pr * k) * s), math.degrees(a) - 80, math.degrees(a) + 80, fill=255, width=int(8 * k * s))

    hole = mask(S, S, lambda d, s: d.ellipse(((c - 70 * k) * s, (c - 70 * k) * s, (c + 70 * k) * s, (c + 70 * k) * s), fill=255))
    pm = np.clip(mask(S, S, petals) - hole, 0, 1)
    em = mask(S, S, edges) * pm
    return save(bake(S, S, [(pm, 0.6, 0.45, 18 * k, "blackiron"), (em, 0.98, 0.12, 3 * k, "brass")], seed=33), "ThornRose.png")


def glass():
    return save(glass_disc(256, (255, 255, 255), 1.0), "ThornGlass.png")


def velvet():
    Wt, Ht = 512, 96
    YY, XX = np.mgrid[0:Ht, 0:Wt].astype(np.float32)
    t = YY / (Ht - 1)
    pile = hp.periodic_noise(Ht, Wt, (1.2, 3), 41) * 0.05
    fold = np.sin(XX / Wt * 2 * np.pi * 3 + hp.periodic_noise(Ht, Wt, (20, 60), 42) * 0.8) * 0.09
    v = 0.5 + 0.3 * np.sin(np.pi * t) + fold + pile + np.exp(-((t - 0.3) / 0.12) ** 2) * 0.18
    v = np.clip(v * 1.1, 0, 1)
    return save(to_img(np.dstack([v, v, v]), np.ones((Ht, Wt))), "ThornVelvet.png")


# ---------------------------------------------------------------- posture rail in the same briar
def posture_briar():
    H = 96
    WX0, WX1, WY0, WY1 = 150, 2250, 28, 68

    def band(d, s):
        d.rectangle((130 * s, 14 * s, (W - 130) * s, 82 * s), fill=255)

    def strands(d, s):  # a rope twist of two thin strands along the top and the bottom edges
        for base in (15, 81):
            for ph in (0, math.pi):
                pts = []
                for x in range(140, W - 140, 5):
                    if abs(x - W / 2) < 200:
                        if pts:
                            d.line(pts, fill=255, width=int(8 * s), joint="curve")
                            pts = []
                        continue
                    pts.append((x * s, (base + 5 * math.sin(x / 34 + ph)) * s))
                if pts:
                    d.line(pts, fill=255, width=int(8 * s), joint="curve")

    def thorn_list():
        out = []
        for base, sgn in ((15, -1), (81, 1)):
            for j, x in enumerate(range(300, W - 300, 170)):
                if abs(x - W / 2) < 250:
                    continue
                lean = 1 if j % 2 == 0 else -1
                out.append((x, base, x + lean * 9, base + sgn * 14))
        return out

    def thorns(d, s):
        for x, y, tx, ty in thorn_list():
            d.polygon([((x - 8) * s, y * s), ((x + 8) * s, y * s), (tx * s, ty * s)], fill=255)

    def tips(d, s):
        for x, y, tx, ty in thorn_list():
            mx, my = tx * 0.55 + x * 0.45, ty * 0.55 + y * 0.45
            d.polygon([((mx - 4) * s, my * s), ((mx + 4) * s, my * s), (tx * s, ty * s)], fill=255)

    def bead(d, s):
        d.rectangle(((WX0 - 6) * s, (WY0 - 6) * s, (WX1 + 6) * s, (WY1 + 6) * s), fill=255)
        d.rectangle((WX0 * s, WY0 * s, WX1 * s, WY1 * s), fill=0)

    def buds(d, s):
        for side in (-1, 1):
            bx = 150 if side < 0 else W - 150
            d.polygon([(p[0] * s, p[1] * s) for p in bud_pts(bx, 48, side, 130, 36)], fill=255)
            for dy in (-1, 1):
                d.polygon([(bx * s, (48 + dy * 18) * s), ((bx + side * 66) * s, (48 + dy * 36) * s), ((bx + side * 38) * s, (48 + dy * 10) * s)], fill=255)

    def bud_lines(d, s):
        for side in (-1, 1):
            bx = 150 if side < 0 else W - 150
            for ox, r in ((30, 22), (60, 14)):
                cx = bx + side * ox
                a0, a1 = (100, 260) if side < 0 else (-80, 80)
                d.arc(((cx - r) * s, (48 - r) * s, (cx + r) * s, (48 + r) * s), a0, a1, fill=255, width=int(5 * s))

    # the cradle: two iron leaves rising under the rose, cut round where the rose sits (rose centre 24 design px
    # above the rail's box, radius ~33 design px -> 4x: centre y -96, r 138 with a small clearance)
    def leaves(d, s):
        cx = W / 2
        for side in (-1, 1):
            pts = []
            for k in range(41):
                t = k / 40
                x = cx + side * (40 + 170 * t)
                y = 90 - 74 * math.sin(math.pi * (0.15 + 0.85 * t)) * (1 - 0.3 * t)
                pts.append((x * s, y * s))
            for k in range(40, -1, -1):
                t = k / 40
                x = cx + side * (40 + 170 * t)
                y = 94 - 8 * math.sin(math.pi * t)
                pts.append((x * s, y * s))
            d.polygon(pts, fill=255)
        d.ellipse(((cx - 60) * s, 60 * s, (cx + 60) * s, 96 * s), fill=255)

    def veins(d, s):
        cx = W / 2
        for side in (-1, 1):
            d.line([((cx + side * 50) * s, 86 * s), ((cx + side * 190) * s, 40 * s)], fill=255, width=int(5 * s))

    cut = mask(W, H, lambda d, s: d.ellipse(((W / 2 - 142) * s, (-96 - 142) * s, (W / 2 + 142) * s, (-96 + 142) * s), fill=255))
    win = mask(W, H, lambda d, s: d.rectangle((WX0 * s, WY0 * s, WX1 * s, WY1 * s), fill=255))
    lv = np.clip(mask(W, H, leaves) - cut, 0, 1)
    layers = [
        (np.clip(mask(W, H, band) - win, 0, 1), 0.28, 0.25, 6, "blackiron"),
        (mask(W, H, strands), 0.5, 0.4, 4, "blackiron"),
        (mask(W, H, thorns), 0.5, 0.3, 3, "blackiron"),
        (mask(W, H, tips), 0.7, 0.15, 2, "brass"),
        (mask(W, H, bead), 0.55, 0.25, 3, "brass"),
        (mask(W, H, buds), 0.5, 0.5, 18, "blackiron"),
        (mask(W, H, bud_lines), 0.75, 0.1, 2, "brass"),
        (lv, 0.6, 0.45, 14, "blackiron"),
        (mask(W, H, veins) * lv, 0.85, 0.1, 2, "brass"),
    ]
    return save(bake(W, H, layers, seed=35), "PostureBriar.png")


# ---------------------------------------------------------------- preview: placed exactly as KitHud places them
SC = 2


def place_health(c, ox, oy, frac, fill, glass_col):
    """Health root at (ox, oy) design px, 600 x 50: track 37.5..562.5 x 15..35, frame 600 x 75 at y -15, orb 72.5 at centre."""
    tw, th = 525, 20
    track = Image.new("RGBA", (int(tw * SC), int(th * SC)), (8, 5, 7, 255))
    fw = int(track.size[0] * frac)
    if fw > 0:
        tile = tint(Image.open(OUT / "ThornVelvet.png"), fill, 1.05).resize((int(107 * SC), int(th * SC)), Image.LANCZOS)
        track.alpha_composite(tiled(tile, fw, track.size[1]).crop((0, 0, fw, track.size[1])))
    c.alpha_composite(track, (int((ox + 37.5) * SC), int((oy + 15) * SC)))
    fr = Image.open(OUT / "ThornFrame.png").resize((600 * SC, 75 * SC), Image.LANCZOS)
    c.alpha_composite(fr, (int(ox * SC), int((oy - 15) * SC)))
    o = 72.5
    g = tint(Image.open(OUT / "ThornGlass.png"), glass_col, 1.0).resize((int(o * 0.6 * SC),) * 2, Image.LANCZOS)
    cx, cy = (ox + 300) * SC, (oy + 25) * SC
    c.alpha_composite(g, (int(cx - g.size[0] / 2), int(cy - g.size[1] / 2)))
    r = Image.open(OUT / "ThornRose.png").resize((int(o * SC),) * 2, Image.LANCZOS)
    c.alpha_composite(r, (int(cx - r.size[0] / 2), int(cy - r.size[1] / 2)))
    d = ImageDraw.Draw(c)
    d.text((cx, cy), f"{round(frac * 100)}%", font=font(int(16 * SC)), fill=(240, 232, 218), anchor="mm", stroke_width=3, stroke_fill=(24, 8, 10))


def preview():
    pp = v4.pp
    pp.SC = SC
    pp.GOLD, pp.EMBER = (226, 168, 72), (255, 122, 46)
    states = [
        ("Full, posture 35%", 0.82, (150, 22, 34), (210, 44, 60), 0.35, "calm"),
        ("Hurt, posture 88% (warning)", 0.38, (150, 22, 34), (210, 44, 60), 0.88, "warn"),
        ("Vampire form", 0.82, (118, 8, 24), (220, 34, 52), 0.0, "calm"),
        ("Wraith form", 0.6, (70, 112, 152), (158, 220, 255), 0.5, "calm"),
    ]
    cw, ch = 680, 110
    out = Image.new("RGBA", (cw * SC, (ch * len(states) + 10) * SC), (14, 11, 16, 255))
    for i, (label, frac, fill, gcol, post, pst) in enumerate(states):
        ox, oy = 40, i * ch + 40
        ImageDraw.Draw(out).text((ox * SC, (oy - 34) * SC), label, font=font(13 * SC), fill=(235, 205, 120))
        tmp = Image.new("RGBA", out.size)
        pp.posture_rail(tmp, ox, oy + 49, post, pst, centre_out=True, frame_img=OUT / "PostureBriar.png")
        out.alpha_composite(tmp)
        place_health(out, ox, oy, frac, fill, gcol)
    out.save(OUT / "preview.png")


if __name__ == "__main__":
    for f in (frame, rose, glass, velvet, posture_briar):
        print(f())
    preview()
    print(OUT / "preview.png")
