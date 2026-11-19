"""Printed things in the WickHouse kitchen (the breakfast scene, docs/expansion/15 §5 beat 9). High quality: drawn at 2x,
with the poster helpers (paper fibres, ink, ageing). Out: art/props/textures/<name>_canvas.png.

  WF_Cereal       the cereal box front: CRUNCH MOONS, "now with MORE marshmallow moons!", a grinning moon mascot
                  splashing into a bowl, a "free prize inside" starburst, the nutrition-ish side strip
  WF_Gazette      the morning paper's front page: the masthead, "MYSTERY PRANKSTER STRIKES AT MIDNIGHT", a halftone
                  photo of a flashlight beam on a blurry figure, columns of body text, the weather box
  WF_Envelope     the black admission envelope: heavy black stock, a cream address label typed "To the Parents or
                  Guardians, 14 Alder Lane, Wickfield", the crimson wax crest (Nocte Discimus) over the flap
  WF_Brochure     the school's tri-fold brochure cover, far too cheerful: a sunny painting of the castle-like school,
                  the Nightmare High crest, "Where Every Student Finds Their Place!*" and the fine print
                  ("*Place may be a crypt. Results not guaranteed. Not responsible for curses, bites or eternity.")
  WF_Calendar     the wall calendar: an autumn photo-illustration up top, the month grid with Mom's notes
                  (Picture Day, Bins out, Dentist, "TALK TO HIM/HER??" circled on today)
  WF_DadMug       the mug's wrap: WORLD'S OKAYEST DAD in a bad trophy graphic
  WF_FridgeArt    a crayon drawing on the fridge: the family, Biscuit, a sun, "MY FAMILY" in wobbly letters

  python art/hometown/kitchen_canvases.py [name ...]
"""
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import posters_hq as Q  # noqa: E402  (sets the 2x supersample)
H = Q.H
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))


def cereal():
    L = H.Logo("WF_Cereal", 1024, 1536)
    W, Hh = 1024, 1536
    pg = L.rrect(0, 0, W, Hh, 0)
    L.paint(pg, L.vgrad("#2f2a8c", "#1a1450", 0, Hh))                   # deep night-blue box
    rng = np.random.default_rng(101)
    for _ in range(120):
        x, y, r = rng.uniform(0, W), rng.uniform(0, Hh * 0.55), rng.uniform(1.5, 4)
        L.paint(H.star(L, x, y, r * 2.2, k=0.4), "#ffe68a", alpha=rng.uniform(0.5, 1))
    # the logo: CRUNCH arched, MOONS big, both with a fat outline and a 3D drop
    t1 = L.arc_text("CRUNCH", "lucky", 150, W / 2, 1300, 1060, a_mid=-90, spacing=1.05)
    t2 = L.text("MOONS", "lucky", 250, W / 2, 470, spacing=8)
    for t_, top, bot in ((t1, "#ffffff", "#ffd84a"), (t2, "#ffe14a", "#ff8a1e")):
        drop = np.roll(np.roll(H.Logo.grow(t_, 12), 12 * H.SS, 0), 6 * H.SS, 1)
        L.paint(drop, "#0e0a2c")
        L.paint(H.Logo.grow(t_, 12), "#e8321e")
        L.paint(H.Logo.grow(t_, 6), "#ffffff")
        L.paint(t_, L.vgrad(top, bot, 200, 560))
        L.shade(t_, strength=0.3, blur=3)
    burst = H.star(L, 850, 640, 105, k=0.78, n=14)
    L.paint(H.Logo.grow(burst, 5), "#8a1010")
    L.paint(burst, "#ff3b2e")
    for t_, y in (("NOW WITH", 612), ("MORE", 645), ("MOONS!", 680)):
        L.paint(L.text(t_, "lucky", 28, 850, y, spacing=2), "#ffffff")
    # the bowl and the mascot: a grinning crescent moon cannonballing into milk, marshmallow moons flying
    bx, by = W / 2, 1180
    bowl = L.m(lambda d, s: d.chord(((bx - 380) * s, (by - 260) * s, (bx + 380) * s, (by + 260) * s), 0, 180, fill=255))
    L.paint(H.Logo.grow(bowl, 8), "#0e0a2c")
    L.paint(bowl, L.vgrad("#ff6a6a", "#b81e3a", by, by + 260))
    L.paint(L.rrect(bx - 380, by - 10, bx + 380, by + 18, 12), "#ffffff")
    milk = L.ellipse(bx, by, 370, 70)
    L.paint(milk, "#fffaf0")
    for k in range(9):                                                   # splash droplets
        a = math.pi * (0.15 + 0.7 * k / 8)
        L.paint(L.ellipse(bx + 300 * math.cos(a), by - 60 - 220 * math.sin(a), 18 - (k % 3) * 4), "#fffaf0")
    mx, my = bx + 40, by - 230
    moon = np.clip(L.ellipse(mx, my, 190) - L.ellipse(mx + 110, my - 70, 170), 0, 1)
    L.glow(moon, "#ffe68a", 30, 0.6)
    L.paint(H.Logo.grow(moon, 8), "#0e0a2c")
    L.paint(moon, L.rgrad("#fff6b0", "#f2b630", mx - 80, my, 230))
    L.paint(L.ellipse(mx - 105, my - 40, 18, 22), "#0e0a2c")             # eye
    L.paint(L.ellipse(mx - 100, my - 46, 6), "#ffffff")
    L.paint(L.m(lambda d, s: d.chord(((mx - 150) * s, (my + 10) * s, (mx - 60) * s, (my + 80) * s), 20, 200, fill=255)), "#0e0a2c")
    L.paint(L.ellipse(mx - 128, my + 2, 16, 10), "#ff8aa0", alpha=0.7)    # blush
    for k in range(10):                                                  # marshmallow moons in the air
        x, y = rng.uniform(120, 900), rng.uniform(640, 980)
        r = rng.uniform(22, 36)
        mm = np.clip(L.ellipse(x, y, r) - L.ellipse(x + r * 0.5, y - r * 0.35, r * 0.85), 0, 1)
        L.paint(H.Logo.grow(mm, 4), "#0e0a2c")
        L.paint(mm, ["#ff9ec4", "#9ee6ff", "#fff1a0", "#b8ff9e"][k % 4])
    # bottom strip
    L.paint(L.rrect(0, 1440, W, Hh, 0), "#ffd84a")
    L.paint(L.text("PART OF A COMPLETE BREAKFAST  ·  NET WT 14 OZ", "lucky", 30, W / 2, 1488, spacing=3), "#1a1450")
    Q.save(L, "WF_Cereal")


def gazette():
    L = H.Logo("WF_Gazette", 1024, 1400)
    W, Hh = 1024, 1400
    INK = "#1a1612"
    pg = L.rrect(0, 0, W, Hh, 0)
    L.paint(pg, "#ece4d0")
    Q.fibres(L, 110, 0.05)
    L.paint(L.text("The Wickfield Gazette", "balth", 96, W / 2, 95), INK)
    for y in (30, 150, 160):
        L.paint(L.rrect(30, y, W - 30, y + (4 if y != 160 else 2), 0), INK)
    L.paint(L.text("EST. 1851    ·    THURSDAY EDITION    ·    FIVE CENTS", "georgiab", 18, W / 2, 182, spacing=3), INK)
    L.paint(L.rrect(30, 198, W - 30, 200, 0), INK)
    L.paint(L.text("MYSTERY PRANKSTER", "georgiab", 72, W / 2, 270, spacing=2), INK)
    L.paint(L.text("STRIKES AT MIDNIGHT", "georgiab", 72, W / 2, 350, spacing=2), INK)
    L.paint(L.text("Police baffled; one goose “deeply offended”", "georgiai", 30, W / 2, 412), INK)
    # the photo: a halftone flashlight beam catching a blurred figure by a fence
    px0, py0, px1, py1 = 60, 450, 620, 860
    photo = L.rrect(px0, py0, px1, py1, 0)
    x, y = L.xx / H.SS, L.yy / H.SS
    beam = np.clip(1 - np.abs((y - py0 - 40) - (x - px0) * 0.55) / 120, 0, 1) * np.clip((x - px0) / 400, 0, 1)
    fig = L.ellipse(450, 640, 42, 50) + L.rrect(405, 680, 495, 840, 30)
    shade = np.clip(0.55 - 0.5 * beam + 0.9 * np.clip(fig, 0, 1), 0, 1)
    for k in range(9):
        shade = np.maximum(shade, L.rrect(px0 + k * 62, 760, px0 + k * 62 + 12, py1, 3) * 0.9)
    L.paint(photo, "#ece4d0")
    Q.halftone(L, shade, photo, INK, cell=6, angle=0.78)
    L.paint(np.clip(L.rrect(px0 - 2, py0 - 2, px1 + 2, py1 + 2, 0) - photo, 0, 1), INK)
    L.paint(L.text("A figure flees the scene, 12:21 a.m. (Gazette photo)", "georgiai", 18, (px0 + px1) / 2, py1 + 22), INK)
    # columns of body text: greeked lines, a drop cap, the weather box
    def column(x0, x1, y0, y1, seed, cap=False):
        r = np.random.default_rng(seed)
        yy = y0
        first = True
        while yy < y1:
            w = (x1 - x0) * (r.uniform(0.6, 1.0) if r.random() < 0.15 else 1.0)
            if first and cap:
                L.paint(L.text("W", "georgiab", 64, x0 + 26, yy + 22), INK)
                for k in range(3):
                    L.paint(L.rrect(x0 + 60, yy + k * 17, x1, yy + k * 17 + 7, 2), INK, alpha=0.75)
                yy += 54
                first = False
                continue
            xx = x0
            while xx < x0 + w - 10:
                wl = r.uniform(18, 60)
                L.paint(L.rrect(xx, yy, min(xx + wl, x0 + w), yy + 7, 2), INK, alpha=0.72)
                xx += wl + 7
            yy += 17
    column(650, 960, 455, 860, 111, cap=True)
    column(60, 330, 920, 1340, 112, cap=False)
    column(360, 630, 920, 1340, 113)
    L.paint(L.rrect(660, 920, 964, 1340, 4), INK)
    L.paint(L.rrect(664, 924, 960, 1336, 3), "#ece4d0")
    L.paint(L.text("WEATHER", "georgiab", 28, 812, 960, spacing=4), INK)
    sun = L.ellipse(760, 1060, 40)
    cloud = L.ellipse(830, 1080, 50, 34) + L.ellipse(875, 1065, 36, 30)
    L.paint(sun, INK, alpha=0.75)
    L.paint(np.clip(cloud, 0, 1), INK)
    for t_, y_ in (("Fog by evening.", 1170), ("Low 41°  High 58°", 1210), ("Stay in, kids.", 1250)):
        L.paint(L.text(t_, "georgia", 24, 812, y_), INK)
    Q.age_paper(L, 114, folds=((0.5, "h"),), tape=False)
    Q.save(L, "WF_Gazette")


def envelope():
    L = H.Logo("WF_Envelope", 1536, 1024)
    W, Hh = 1536, 1024
    pg = L.rrect(0, 0, W, Hh, 0)
    L.paint(pg, L.vgrad("#1a1618", "#0c0a0c", 0, Hh))
    Q.fibres(L, 120, 0.12)
    # the flap's edges (embossed lines from the corners to the seal) and a faint gilt border
    for (x0, y0) in ((0, 0), (W, 0)):
        L.paint(L.line([(x0, y0), (W / 2, 520)], 4), "#000000", alpha=0.6)
        L.paint(L.line([(x0 + (6 if x0 == 0 else -6), y0 + 6), (W / 2, 528)], 2), "#3a3436", alpha=0.6)
    L.paint(np.clip(L.rrect(24, 24, W - 24, Hh - 24, 6) - L.rrect(30, 30, W - 30, Hh - 30, 6), 0, 1), "#8a6a30", alpha=0.6)
    # the address label (cream, typed)
    lab = L.rrect(860, 720, 1460, 975, 6)
    L.paint(lab, "#efe6cf")
    Q.fibres(L, 121, 0.04)
    for t_, y_ in (("To the Parents or Guardians", 775), ("14 Alder Lane", 830), ("Wickfield", 885), ("BY HAND. DO NOT FOLD.", 945)):
        L.paint(L.text(t_, "georgia" if y_ < 945 else "georgiab", 34 if y_ < 945 else 22, 1160, y_, spacing=1 if y_ < 945 else 4), "#2a1e1a")
    # the wax crest, from the logo art (scaled into place)
    wax = Image.open(os.path.join(ROOT, "art", "hometown", "logos", "out", "AdmissionWax_color.png")).convert("RGBA").resize((330 * H.SS, 330 * H.SS), Image.LANCZOS)
    a = np.asarray(wax, np.float32)
    x0, y0 = int((W / 2 - 165) * H.SS), int((500 - 165) * H.SS)
    sl = (slice(y0, y0 + a.shape[0]), slice(x0, x0 + a.shape[1]))
    k = a[..., 3:4] / 255.0
    shadow = np.roll(np.roll(a[..., 3] / 255.0, 10 * H.SS, 0), 6 * H.SS, 1)
    L.col[sl] = L.col[sl] * (1 - 0.6 * shadow[..., None])
    L.col[sl] = L.col[sl] * (1 - k) + a[..., :3] * k
    # the wax stands off the paper (its own relief from the logo's height map), glossy; the label sits a little proud
    hm = np.asarray(Image.open(os.path.join(ROOT, "art", "hometown", "logos", "out", "AdmissionWax_height.png")).resize((a.shape[1], a.shape[0]), Image.BILINEAR), np.float32) / 65535.0
    eh = np.zeros((L.H, L.W), np.float32)
    eh[sl] = (1.2 + 1.6 * hm) * k[..., 0]
    eh += 0.25 * lab
    L.extra_h = eh
    waxm = np.zeros((L.H, L.W), np.float32)
    waxm[sl] = k[..., 0]
    L.rough_over = (waxm, 0.18)
    Q.save(L, "WF_Envelope")


def brochure():
    L = H.Logo("WF_Brochure", 1024, 1536)
    W, Hh = 1024, 1536
    pg = L.rrect(0, 0, W, Hh, 0)
    L.paint(pg, "#fbf6ea")
    # a sunny painted scene: blue sky, a big smiling sun, green hills, the school's spires
    sky = L.rrect(60, 300, W - 60, 1000, 20)
    L.paint(sky, L.vgrad("#7ec8f2", "#d8f0ff", 300, 1000))
    sun = L.ellipse(800, 420, 90)
    L.glow(sun, "#fff2a0", 40, 0.8)
    L.paint(sun, "#ffd84a")
    for sx in (-1, 1):
        L.paint(L.ellipse(800 + sx * 28, 405, 9, 12), "#5a3a10")
    L.paint(L.m(lambda d, s: d.arc((760 * s, 410 * s, 840 * s, 470 * s), 20, 160, fill=255, width=int(8 * s))), "#5a3a10")
    for cx_, cy_, sc in ((230, 400, 1.0), (560, 350, 0.8), (380, 470, 0.6)):         # fluffy clouds
        cl = np.clip(L.ellipse(cx_, cy_, 70 * sc, 34 * sc) + L.ellipse(cx_ - 50 * sc, cy_ + 8, 46 * sc, 28 * sc) + L.ellipse(cx_ + 52 * sc, cy_ + 6, 50 * sc, 30 * sc)
                     + L.ellipse(cx_ + 10, cy_ - 24 * sc, 44 * sc, 34 * sc), 0, 1) * sky
        L.paint(cl, L.vgrad("#ffffff", "#dceaf5", cy_ - 60, cy_ + 40))
    far = L.poly([(60, 1000)] + [(60 + i * 30, 800 - 50 * math.sin(i / 4.0 + 1) - 20 * math.sin(i / 1.7)) for i in range(31)] + [(W - 60, 1000)]) * sky
    L.paint(far, L.vgrad("#9ad07a", "#6aa85a", 740, 1000))
    hills = L.poly([(60, 1000)] + [(60 + i * 30, 870 - 50 * math.sin(i / 6.0) - 25 * math.sin(i / 2.3)) for i in range(31)] + [(W - 60, 1000)]) * sky
    L.paint(hills, L.vgrad("#7acb5a", "#3f8a3a", 800, 1000))
    for tx_, ty_, sc in ((140, 860, 1.0), (215, 880, 0.8), (860, 870, 1.1), (930, 890, 0.8)):  # round trees
        L.paint(L.rrect(tx_ - 6 * sc, ty_, tx_ + 6 * sc, ty_ + 60 * sc, 3), "#6a4a2a")
        L.paint(L.ellipse(tx_, ty_ - 10 * sc, 46 * sc, 52 * sc) * sky, L.rgrad("#8ad86a", "#3f8a3a", tx_ - 15, ty_ - 30, 60 * sc))
    path = L.poly([(500, 860), (524, 860), (640, 1000), (384, 1000)]) * sky
    L.paint(path, "#e8d8a8")
    for k in range(24):                                                       # flowers
        fx, fy = 80 + (k * 137) % 860, 930 + (k * 53) % 60
        L.paint(L.ellipse(fx, fy, 6), ["#ff7aa8", "#ffe14a", "#ffffff", "#c88aff"][k % 4])
    # the school: dark gothic block with spires and lit windows, softened by the sunny paint
    sch = np.zeros((L.H, L.W), np.float32)
    sch = np.maximum(sch, L.rrect(300, 640, 724, 860, 4))
    for x, h_ in ((300, 520), (420, 580), (512, 470), (604, 580), (724, 520)):
        sch = np.maximum(sch, L.rrect(x - 30, h_, x + 30, 860, 2))
        sch = np.maximum(sch, L.poly([(x - 38, h_ + 4), (x, h_ - 90), (x + 38, h_ + 4)]))
    sch *= sky
    L.paint(sch, L.vgrad("#5a4a6a", "#3a2e48", 400, 860))
    for i in range(7):
        for j in range(2):
            if i == 3 and j == 1:
                continue
            L.paint(L.rrect(330 + i * 56, 690 + j * 80, 350 + i * 56, 730 + j * 80, 8), "#ffd06a")
    gate = L.rrect(486, 770, 538, 860, 26) * sky
    L.paint(gate, "#2a2032")
    L.paint(L.line([(512, 770), (512, 860)], 2) * sky, "#8a6a3a")
    for x in (300, 420, 512, 604, 724):                                       # little pennants on the spires
        L.paint(L.poly([(x, 440 if x in (420, 604) else (380 if x == 512 else 430)), (x + 26, 450 if x in (420, 604) else (390 if x == 512 else 440)), (x, 460 if x in (420, 604) else (400 if x == 512 else 450))]) * sky, "#c8303a")
    for k in range(5):                                                    # cheerful birds (they are bats)
        bx, by = 200 + k * 90, 380 + (k % 2) * 40
        L.paint(L.stroke_round([(bx - 20, by), (bx - 8, by - 10), (bx, by), (bx + 8, by - 10), (bx + 20, by)], 5), "#3a2e48")
    L.paint(np.clip(L.rrect(56, 296, W - 56, 1004, 22) - sky, 0, 1), "#c9a35a")
    # the crest, the slogan, the fine print
    crest = Image.open(os.path.join(ROOT, "art", "logo", "source.png")).convert("RGBA").resize((300 * H.SS, 297 * H.SS), Image.LANCZOS)
    a = np.asarray(crest, np.float32)
    x0, y0 = int((W / 2 - 150) * H.SS), int(10 * H.SS)
    sl = (slice(y0, y0 + a.shape[0]), slice(x0, x0 + a.shape[1]))
    k = a[..., 3:4] / 255.0
    L.col[sl] = L.col[sl] * (1 - k) + a[..., :3] * k
    L.paint(L.text("Where Every Student", "chela", 76, W / 2, 1090), "#8a1a2a")
    L.paint(L.text("Finds Their Place!*", "chela", 76, W / 2, 1180), "#8a1a2a")
    L.paint(L.text("Boarding · Small classes · Lovely grounds · Night study", "georgiai", 28, W / 2, 1262), "#3a2e2a")
    for i, t_ in enumerate(("*Place may be a crypt. Results not guaranteed. Not responsible for curses,",
                            "bites, hauntings, transformations or eternity. Ask about our Covenant.",
                            "Uniform required. Curfew 10 PM. The bell is not to be rung.")):
        L.paint(L.text(t_, "georgia", 13, W / 2, 1420 + i * 20), "#5a4a40")
    L.paint(L.rrect(W / 3, 0, W / 3 + 2, Hh, 0), "#000000", alpha=0.06)     # the folds of the tri-fold
    Q.fibres(L, 130, 0.03)
    Q.save(L, "WF_Brochure")


def calendar():
    L = H.Logo("WF_Calendar", 1024, 1536)
    W, Hh = 1024, 1536
    pg = L.rrect(0, 0, W, Hh, 0)
    L.paint(pg, "#f8f3e6")
    # the picture: an autumn lane, painterly
    pic = L.rrect(40, 60, W - 40, 680, 4)
    L.paint(pic, L.vgrad("#f2c27a", "#e88a4a", 60, 680))
    for i in range(14):
        x = 60 + i * 70
        L.paint(L.rrect(x, 300 + (i % 3) * 20, x + 14, 680, 4) * pic, "#4a2e1e")
        L.paint(L.ellipse(x + 7, 300 + (i % 3) * 20, 70, 60) * pic, ["#c8501e", "#e8902a", "#a83a1a"][i % 3], alpha=0.9)
    road = L.poly([(W / 2 - 40, 450), (W / 2 + 40, 450), (W - 140, 680), (140, 680)]) * pic
    L.paint(road, "#8a7a6a")
    L.paint(L.rrect(0, 20, W, 30, 0), "#8a8a90")
    for x in range(60, W - 40, 40):
        L.paint(np.clip(L.ellipse(x, 25, 10) - L.ellipse(x, 25, 6), 0, 1), "#5a5a60")
    L.paint(L.text("OCTOBER", "georgiab", 72, W / 2, 750, spacing=14), "#a83a1a")
    days = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
    gx0, gy0, cw, ch = 40, 800, (W - 80) / 7, 110
    for i, d in enumerate(days):
        L.paint(L.text(d, "georgiab", 22, gx0 + cw * (i + 0.5), gy0 + 14), "#3a2e2a")
    for r in range(6):
        for c in range(7):
            n = r * 7 + c - 2
            x0, y0 = gx0 + c * cw, gy0 + 34 + r * ch
            L.paint(np.clip(L.rrect(x0, y0, x0 + cw, y0 + ch, 0) - L.rrect(x0 + 1.5, y0 + 1.5, x0 + cw - 1.5, y0 + ch - 1.5, 0), 0, 1), "#b8ac98")
            if 1 <= n <= 31:
                L.paint(L.text(str(n), "georgia", 22, x0 + 18, y0 + 18), "#3a2e2a")
    notes = {4: "Picture Day", 9: "Bins out", 16: "Bins out", 19: "Dentist 3pm", 23: "Bins out", 27: "Bake sale"}
    for n, t_ in notes.items():
        r, c = divmod(n + 2, 7)
        L.paint(L.text(t_, "chela", 20, gx0 + c * cw + cw / 2, gy0 + 34 + r * ch + 70), "#2a4a8a")
    r, c = divmod(30 + 2, 7)                                                 # today, circled hard in red
    cx_, cy_ = gx0 + c * cw + cw / 2, gy0 + 34 + r * ch + ch / 2
    for k in range(3):
        L.paint(np.clip(L.ellipse(cx_ + k, cy_ - k, cw / 2 - 4 + k * 2, ch / 2 - 6) - L.ellipse(cx_ + k, cy_ - k, cw / 2 - 9 + k * 2, ch / 2 - 11), 0, 1), "#c8201a", alpha=0.85)
    L.paint(L.text("TALK TO", "chela", 22, cx_, cy_ + 2), "#c8201a")
    L.paint(L.text("THEM!!", "chela", 22, cx_, cy_ + 26), "#c8201a")
    Q.fibres(L, 140, 0.03)
    Q.save(L, "WF_Calendar")


def dad_mug():
    L = H.Logo("WF_DadMug", 1536, 512)
    W, Hh = 1536, 512
    L.paint(L.rrect(0, 0, W, Hh, 0), "#f4f1ea")
    cup = L.poly([(620, 140), (916, 140), (880, 300), (656, 300)]) + L.rrect(720, 300, 816, 360, 6) + L.rrect(660, 360, 876, 400, 10)
    for sx in (-1, 1):
        cup = cup + np.clip(L.ellipse(768 + sx * 160, 200, 50, 46) - L.ellipse(768 + sx * 160, 200, 30, 26), 0, 1)
    L.paint(np.clip(cup, 0, 1), L.vgrad("#ffe07a", "#c8901e", 140, 400))
    L.paint(H.star(L, 768, 215, 40), "#ffffff")
    L.paint(L.text("WORLD'S", "lucky", 60, 768, 450, spacing=8), "#1e3a7a")
    for sx, t_ in ((-1, "OKAYEST"), (1, "DAD")):
        L.paint(L.text(t_, "lucky", 110, 768 + sx * 470, 260, spacing=6), "#1e3a7a")
    Q.save(L, "WF_DadMug")


def fridge_art():
    L = H.Logo("WF_FridgeArt", 1024, 768)
    W, Hh = 1024, 768
    L.paint(L.rrect(0, 0, W, Hh, 0), "#fbf8ef")
    Q.fibres(L, 150, 0.04)

    def crayon(pts, w, col, seed):
        m = L.stroke_round(pts, w)
        streak = Q.noise(L, 0.6, seed) > -0.3
        L.paint(m * streak, col, alpha=0.9)
    crayon([(80, 200), (110, 170), (150, 160), (190, 175), (210, 200)], 10, "#f2c21a", 151)
    sun_c = L.ellipse(140, 140, 60)
    L.paint(sun_c * (Q.noise(L, 0.6, 152) > -0.4), "#ffd21a", alpha=0.85)
    for k in range(10):
        a = k * math.pi / 5
        crayon([(140 + 70 * math.cos(a), 140 + 70 * math.sin(a)), (140 + 100 * math.cos(a), 140 + 100 * math.sin(a))], 8, "#ffb01a", 153 + k)
    crayon([(0, 640), (W, 650)], 22, "#4aa83a", 160)
    figs = [(330, 1.0, "#c8301e", "MOM"), (480, 1.15, "#2a5ab8", "DAD"), (620, 0.75, "#8a3ab8", "ME")]
    for x, s, col, nm in figs:
        crayon([(x, 380 - 120 * s)] * 2, 70 * s, col, 170)
        L.paint(L.ellipse(x, 380 - 120 * s, 34 * s), "#f8d8b0")
        crayon([(x - 12 * s, 380 - 125 * s)] * 2, 8, "#222222", 171)
        crayon([(x + 12 * s, 380 - 125 * s)] * 2, 8, "#222222", 172)
        crayon([(x - 14 * s, 380 - 105 * s), (x, 380 - 98 * s), (x + 14 * s, 380 - 105 * s)], 5, "#222222", 173)
        crayon([(x, 380 - 85 * s), (x, 380 + 60 * s)], 10, col, 174)
        crayon([(x - 50 * s, 380 - 40 * s), (x, 380 - 60 * s), (x + 50 * s, 380 - 40 * s)], 9, col, 175)
        crayon([(x, 380 + 60 * s), (x - 30 * s, 630)], 9, col, 176)
        crayon([(x, 380 + 60 * s), (x + 30 * s, 630)], 9, col, 177)
        L.paint(L.text(nm, "chela", 36, x, 220 - 130 * (s - 0.75)), col)
    # Biscuit: a long brown sausage with ears and a waggy tail
    crayon([(760, 580), (900, 580)], 46, "#a86a2a", 180)
    crayon([(760, 560), (760, 560)], 56, "#a86a2a", 181)
    crayon([(745, 560), (735, 610)], 16, "#6a3a12", 182)
    crayon([(900, 570), (950, 520)], 10, "#a86a2a", 183)
    for x in (785, 820, 870, 890):
        crayon([(x, 600), (x, 632)], 10, "#a86a2a", 184)
    L.paint(L.text("BISCUIT", "chela", 34, 830, 500), "#6a3a12")
    L.paint(L.text("MY FAMILY", "chela", 70, 640, 90), "#2a5ab8")
    Q.save(L, "WF_FridgeArt")


if __name__ == "__main__":
    want = sys.argv[1:]
    for fn in (cereal, gazette, envelope, brochure, calendar, dad_mug, fridge_art):
        if not want or fn.__name__ in want:
            fn()
