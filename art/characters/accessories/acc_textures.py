"""Alpha textures for the accessory kits (veils, lace), drawn with PIL at 4x and downsampled for clean threads.

python acc_textures.py [outdir]   (default E:/NH-Work/acc/maps)
  NHAcc_VeilNet.png    1024 tileable: a Victorian diamond veil net with chenille dots, black silk threads (RGBA)
  NHAcc_VeilNetFine.png 1024 tileable: a finer net for the fascinator's birdcage veil
  NHAcc_Lace.png       2048 x 1024: black Chantilly-style lace for the lace masquerade mask (front-projected)
"""
import math, os, random, sys
from PIL import Image, ImageDraw, ImageFilter

OUT = sys.argv[1] if len(sys.argv) > 1 else "E:/NH-Work/acc/maps"
os.makedirs(OUT, exist_ok=True)
THREAD = (14, 12, 16)


def finish(img, size):
    return img.resize(size, Image.LANCZOS)


def veil(name, cells=6, width=9, dot=18, size=1024):
    S = size * 4
    im = Image.new("RGBA", (S, S), (*THREAD, 0))
    d = ImageDraw.Draw(im)
    step = S / cells
    for k in range(-cells, 2 * cells + 1):
        # two families of diagonals: a diamond mesh that tiles
        x0 = k * step
        d.line([(x0, 0), (x0 + S, S)], fill=(*THREAD, 235), width=width * 4 // 3)
        d.line([(x0, S), (x0 + S, 0)], fill=(*THREAD, 235), width=width * 4 // 3)
    random.seed(4)
    for i in range(cells):
        for j in range(cells):
            if (i + j) % 2 == 0:   # chenille dots on every other knot
                cx, cy = (i + 0.5) * step, (j + 0.5) * step
                r = dot * 2
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*THREAD, 250))
    im = im.filter(ImageFilter.GaussianBlur(2))
    finish(im, (size, size)).save(os.path.join(OUT, name))


def lace(name="NHAcc_Lace.png", W=2048, H=1024):
    S = 4
    im = Image.new("RGBA", (W * S, H * S), (*THREAD, 0))
    d = ImageDraw.Draw(im)
    w, h = W * S, H * S
    # the ground: a fine hexagonal tulle
    cell = 26 * S
    for row in range(int(h / (cell * 0.866)) + 2):
        y = row * cell * 0.866
        off = (cell / 2) if row % 2 else 0
        for col in range(int(w / cell) + 2):
            x = col * cell + off
            pts = [(x + cell * 0.5 * math.cos(a), y + cell * 0.5 * math.sin(a)) for a in (math.pi / 3 * k + math.pi / 6 for k in range(6))]
            d.polygon(pts, outline=(*THREAD, 225), width=3 * S)
    # motifs: rosettes and scrolling leaves, heavier cord outlines (the cordonnet)
    random.seed(11)

    def leaf(cx, cy, L, ang, wdt):
        pts = []
        for i in range(24):
            t = i / 23
            r = math.sin(math.pi * t) * wdt
            pts.append((t * L, r))
        for i in range(24):
            t = 1 - i / 23
            r = -math.sin(math.pi * t) * wdt
            pts.append((t * L, r))
        ca, sa = math.cos(ang), math.sin(ang)
        P = [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]
        d.polygon(P, fill=(*THREAD, 235), outline=(*THREAD, 255))
        d.line([(cx, cy), (cx + L * 0.9 * ca, cy + L * 0.9 * sa)], fill=(*THREAD, 0), width=3 * S)

    def rosette(cx, cy, R):
        for k in range(8):
            a = 2 * math.pi * k / 8
            px, py = cx + R * 0.55 * math.cos(a), cy + R * 0.55 * math.sin(a)
            d.ellipse([px - R * 0.36, py - R * 0.36, px + R * 0.36, py + R * 0.36], fill=(*THREAD, 235))
            d.ellipse([px - R * 0.18, py - R * 0.18, px + R * 0.18, py + R * 0.18], fill=(*THREAD, 0))
        d.ellipse([cx - R * 0.3, cy - R * 0.3, cx + R * 0.3, cy + R * 0.3], fill=(*THREAD, 255))
        d.ellipse([cx - R * 1.02, cy - R * 1.02, cx + R * 1.02, cy + R * 1.02], outline=(*THREAD, 255), width=4 * S)

    # symmetric about the centre line (a mask is symmetric)
    motifs = []
    for i in range(15):
        x = random.uniform(0.04, 0.49) * w
        y = random.uniform(0.15, 0.85) * h
        motifs.append((x, y, random.uniform(55, 100) * S))
    for x, y, R in motifs:
        for mx in (x, w - x):
            rosette(mx, y, R)
            for k in range(5):
                a = random.uniform(0, 2 * math.pi)
                leaf(mx + R * 1.1 * math.cos(a), y + R * 1.1 * math.sin(a), R * 1.4, a + (0.4 if mx < w / 2 else -0.4), R * 0.28)
    # a scalloped picot border along the top and bottom
    for edge_y, sgn in ((0, 1), (h, -1)):
        for k in range(0, w, 60 * S):
            d.pieslice([k, edge_y - 40 * S, k + 60 * S, edge_y + 40 * S], 0 if sgn > 0 else 180, 180 if sgn > 0 else 360, fill=(*THREAD, 250))
    im = im.filter(ImageFilter.GaussianBlur(1.5))
    finish(im, (W, H)).save(os.path.join(OUT, name))


if __name__ == "__main__":
    veil("NHAcc_VeilNet.png", cells=5, width=10, dot=20)
    veil("NHAcc_VeilNetFine.png", cells=8, width=8, dot=12)
    lace()
    print("ok", OUT)
