"""Printed atlas for props batch 54, the concession consumables kit (Mrs. Okada's stand). System Python (PIL + numpy) and
headless Edge:

  python art/props/concession_atlas.py            every label, then the atlas
  python art/props/concession_atlas.py <Key> ...  render just those labels (previews in E:/NH-Work/props54/atlas2/render)

ConcessionPrint  every label of the kit, each brand with its own look: can, bottle and cup wraps drawn once all the way round
                 (the front panel centred a quarter of the way along, the back panel with its copy, barcode and the Okada's
                 stamp three quarters along, seamless where the ends meet), bag fronts and backs, carton faces, lids, bands,
                 stencils, the lunch tray liners, the curry tent card, the meal ticket, and plain swatches.

Each label is SVG (concession_svg.py, motifs in concession_motifs.py) rendered by Edge at 2x into three layers: the colour,
the foil mask (gilt and holo foil; the _gilt map) and the emboss (the _height map). Writes
art/props/textures/ConcessionPrint_{color,gilt,height}.png (4096; bake sources only, not uploaded) and
art/props/concession_atlas.json (every region's UV rect, v up). All names, mascots and text are invented and family friendly;
nothing gory.
"""
import json
import math
import os
import random
import sys

import numpy as np
from PIL import Image

import concession_svg as S
import concession_motifs as M
from concession_motifs import INK, BONE, CREAM, CRIMSON, GOLD
from concession_svg import Label

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "textures")
A = 4096
LABELS = {}


def label(key, W, H):
    def deco(fn):
        LABELS[key] = (W, H, fn)
        return fn
    return deco


def alu_bands(L, h=30):
    """Bare aluminium at a can's neck and foot (silver foil)."""
    sv = L.silver()
    L.rect(0, 0, L.W, h, sv, cls="foil")
    L.rect(0, L.H - h, L.W, h, sv, cls="foil")


# ================================================================== drinks

@label("Can_Ramune", 1100, 300)
def can_ramune(L):
    L.rect(0, 0, L.W, L.H, L.lin([(0, "#0b1640"), (0.55, "#1a3a7a"), (1, "#0b1a48")]))
    sv = L.silver()
    rnd = random.Random(31)
    # a star chart round the whole bottle: grid circles, constellations, stars (silver foil)
    for cx in (L.W * 0.08, L.W * 0.58):
        for r in (90, 150, 210):
            L.circle(cx + 140, L.H / 2, r, "none", "#9fb4e0", 1.2, op=0.35)
    for k in range(18):
        x = (k + 0.5) * L.W / 18
        L.line(x, 0, x, L.H, "#9fb4e0", 0.8, op=0.18)
    for cons in ([(30, 60), (70, 40), (110, 70), (150, 50), (190, 90)], [(620, 230), (660, 200), (700, 240), (740, 210)],
                 [(400, 250), (430, 220), (470, 240)]):
        L.poly(cons, "none", sv, 2.2, cls="foil", closed=False)
        for x, y in cons:
            M.star(L, x, y, 9, sv, cls="foil emb")
    for _ in range(90):
        x, y = rnd.uniform(0, L.W), rnd.uniform(36, L.H - 36)
        L.circle(x, y, rnd.choice((1.2, 1.6, 2.4)), "#dfe8ff", op=rnd.uniform(0.5, 1))
    for x in (L.W * 0.03, L.W * 0.47, L.W * 0.53, L.W * 0.97):
        M.sparkle(L, x, L.H * 0.5, 18, sv, cls="foil")
    L.rect(0, 14, L.W, 5, sv, cls="foil")
    L.rect(0, L.H - 19, L.W, 5, sv, cls="foil")
    fx = L.W * 0.25
    L.circle(fx - 205, 128, 46, L.rad([(0, "#e8fbff"), (0.45, "#5ad0e0"), (1, "#0a5a78")], cx=0.35, cy=0.3), "#e8f4ff", 3, cls="emb")
    L.ellipse(fx - 220, 112, 14, 9, "#ffffff", op=0.85)
    M.moon(L, fx + 210, 120, 34, sv, cls="foil emb")
    L.text("MOONWELL", fx + 10, 112, maxw=270, maxh=64, f="dutch", fill=sv, stroke="#06102c", sw=7, cls="foil emb", ls=2,
           shadow=(3, 4, "#000", 0.5))
    L.text("RAMUNE", fx, 184, maxw=250, maxh=40, f="bank", fill="#9fe6ff", ls=6)
    L.text("marble soda  -  pop it, make a wish", fx, 232, maxw=360, maxh=24, f="serifi", fill="#cfe0ff")
    bx = L.W * 0.75
    L.text("HOW TO OPEN", bx - 110, 62, maxw=200, maxh=24, f="bank", fill="#9fe6ff", ls=2)
    for i, s in enumerate(("1  press the plunger down", "2  hear the marble drop", "3  wait for the fizz", "4  make a wish")):
        L.text(s, bx - 110, 98 + i * 30, maxw=210, maxh=19, f="serifi", fill="#dfe8ff")
    M.barcode(L, bx + 40, 70, 150, 70, seed=4, digits="4 902 540 01")
    M.okada_stamp(L, bx + 115, 205, 42, "#dfe8ff")


@label("Can_Barley", 1100, 420)
def can_barley(L):
    alu_bands(L)
    L.rect(0, 30, L.W, L.H - 60, L.lin([(0, "#3a1c0c"), (0.45, "#a4561c"), (0.8, "#e0a24a"), (1, "#f2c878")]))
    g = L.gilt()
    rnd = random.Random(8)
    for i in range(70):
        x = i * L.W / 70 + rnd.uniform(-4, 4)
        M.barley(L, x, L.H - 30, rnd.uniform(70, 110), "#2a1408", lean=rnd.uniform(-0.25, 0.25))
    L.rect(0, L.H - 60, L.W, 30, "#2a1408")
    fx = L.W * 0.25
    L.circle(fx, 150, 92, L.rad([(0, "#fff2c0"), (0.7, "#f2c45a"), (1, "#d08a2a")]), cls="foil emb")
    L.circle(fx, 150, 104, "none", g, 3, cls="foil")
    for k, a in enumerate((-0.5, -0.2, 0.1, 0.4)):
        M.barley(L, fx - 40 + k * 26, 238, 150, g, cls="foil emb", lean=a)
    L.rect(fx - 230, 222, 460, 92, CREAM, "#2a1408", 4, rx=6, cls="emb")
    L.rect(fx - 222, 230, 444, 76, "none", "#7a4a1c", 1.5)
    L.text("HUSKWOOD", fx, 262, maxw=400, maxh=54, f="dutch", fill="#2a1408", ls=3)
    L.text("roasted barley tea", fx, 296, maxw=300, maxh=22, f="serifi", fill="#7a3a12")
    M.starburst(L, fx + 210, 112, 62, L.holo(), ["HARVEST", "MOON", "LIMITED"], "#3a1c0c", cls="foil emb", f="impact")
    bx = L.W * 0.75
    M.back_panel(L, bx, 60, 470, 280, "Brewed slow, served cold",
                 ["Barley from the north field, roasted till it sings.", "No sugar. No nonsense.", "Good for long exams and longer nights.",
                  "Shake gently. Drink before the bell."], "#f6e6c8", "#ffd88a", bg="#2a140888", seed=9, code="4 902 540 02")


@label("Can_Coffee", 1100, 420)
def can_coffee(L):
    alu_bands(L)
    L.rect(0, 30, L.W, L.H - 60, L.lin([(0, "#0c0a0c"), (0.5, "#1e1612"), (1, "#0c0a0c")]))
    g = L.gilt()
    for i in range(22):
        for j in range(4):
            x, y = (i + 0.5 * (j % 2)) * L.W / 22, 70 + j * 90
            M.quatrefoil(L, x, y, 10, "#2a2018")
    L.rect(0, 40, L.W, 4, g, cls="foil")
    L.rect(0, L.H - 44, L.W, 4, g, cls="foil")
    fx = L.W * 0.25
    M.window_candle(L, fx, 150, 120, 190)
    M.raven(L, fx + 28, 228, 120, g, cls="foil emb")
    L.text("Black Vigil", fx, 312, maxw=470, maxh=82, f="black", fill=g, stroke=g, sw=2.4, cls="foil emb", shadow=(3, 4, "#000", 0.6))
    L.text("COFFEE  -  BLACK, UNSWEETENED", fx, 362, maxw=380, maxh=20, f="bank", fill="#e8d8b0", ls=3)
    M.ribbon(L, fx, 62, 230, 30, CRIMSON, "for the night watch", "#f2dca8", f="serifi")
    bx = L.W * 0.75
    M.back_panel(L, bx, 58, 470, 290, "Keep the vigil",
                 ["Dark-roasted by candlelight in the bell tower.", "One can keeps one student awake",
                  "through one very long chapter.", "Do not drink after midnight. (You will anyway.)"], "#e8d8b0", "#e4bc6a",
                 seed=10, code="4 902 540 03")


@label("Can_RedLantern", 1100, 420)
def can_redlantern(L):
    alu_bands(L)
    L.rect(0, 30, L.W, L.H - 60, L.lin([(0, "#140406"), (0.5, "#a01420"), (1, "#140406")], 0, 0, 1, 0))
    hol = L.holo()
    pts = [(0, L.H - 30)]
    rnd = random.Random(5)
    for i in range(45):
        x = i * L.W / 44
        pts.append((x, L.H - 30 - rnd.uniform(40, 140) * (1 if i % 2 else 0.35)))
    pts.append((L.W, L.H - 30))
    L.poly(pts, hol, cls="foil")
    L.poly([(x, y + 40) for x, y in pts[1:-1]] + [(L.W, L.H - 30), (0, L.H - 30)], "#5a0408")
    fx = L.W * 0.25
    M.lantern(L, fx - 170, 160, 210)
    L.path(f"M {fx + 150} 70 l -30 60 l 22 0 l -28 66 l 62 -82 l -24 0 l 24 -44 Z", hol, INK, 3, cls="foil emb")
    L.text("RED", fx + 40, 126, maxw=260, maxh=96, f="impact", fill="#ffe08a", stroke="#1a0204", sw=8, cls="emb", rot=-6,
           shadow=(4, 5, "#000", 0.6))
    L.text("LANTERN", fx + 40, 222, maxw=330, maxh=86, f="impact", fill="#ffe08a", stroke="#1a0204", sw=8, cls="emb", rot=-6,
           shadow=(4, 5, "#000", 0.6))
    L.text("ENERGY  -  KEEP IT LIT", fx + 30, 290, maxw=300, maxh=22, f="bank", fill="#ffffff", ls=3)
    M.starburst(L, fx + 200, 330, 46, "#ffe08a", ["CANDLEWAX", "CHERRY"], "#7a0a10", f="impact")
    bx = L.W * 0.75
    M.back_panel(L, bx, 50, 460, 250, "Warning: very lit",
                 ["One can per student per night.", "Teachers pretend not to see it.", "Contains cherry, cola nut and ambition."],
                 "#ffe8d0", "#ffd36a", bg="#14040688", seed=11, code="4 902 540 04")


@label("Label_Cola", 1000, 300)
def label_cola(L):
    L.rect(0, 0, L.W, L.H, L.lin([(0, "#1a0e10"), (0.5, "#0a0608"), (1, "#1a0e10")]))
    g = L.gilt()
    L.rect(0, 10, L.W, 6, g, cls="foil")
    L.rect(0, L.H - 16, L.W, 6, g, cls="foil")
    M.dots(L, 0, 20, L.W, L.H - 40, "#c01a2a", 25, 2.4, op=0.35)
    fx = L.W * 0.25
    L.circle(fx - 150, 150, 92, L.rad([(0, "#fff0b0"), (1, "#d8a02a")]), cls="foil")
    M.cat(L, fx - 150, 160, 170)
    L.text("Black Cat", fx + 70, 104, maxw=300, maxh=70, f="script", fill=CREAM, stroke="#8a0e1a", sw=6, cls="emb",
           shadow=(3, 3, "#000", 0.6))
    L.text("COLA", fx + 70, 186, maxw=250, maxh=82, f="heavy", fill="#d01a2a", stroke=g, sw=4, cls="emb", ls=4)
    L.text("crossing paths since 1931", fx + 70, 250, maxw=280, maxh=22, f="serifi", fill=GOLD)
    bx = L.W * 0.75
    M.starburst(L, bx - 160, 150, 70, "#e0b24a", ["ICE", "COLD"], "#3a0a0e", f="impact")
    L.text("Nine lives of fizz.", bx + 40, 80, maxw=260, maxh=28, f="serifbi", fill=CREAM)
    L.text("Unlucky only for thirst.", bx + 40, 116, maxw=260, maxh=22, f="serifi", fill="#cfc4ac")
    M.barcode(L, bx - 20, 160, 130, 70, seed=12, digits="4 902 540 05")
    M.okada_stamp(L, bx + 170, 200, 44, GOLD)


@label("Label_GreenTea", 1000, 360)
def label_greentea(L):
    L.rect(0, 0, L.W, L.H, L.lin([(0, "#e8f0dc"), (1, "#c8dcb4")]))
    g = L.gilt()
    rnd = random.Random(14)
    for _ in range(14):
        L.ellipse(rnd.uniform(0, L.W), rnd.uniform(60, 300), rnd.uniform(40, 110), rnd.uniform(20, 50), "#8ab87a", cls="fx", op=0.25,
                  extra=L.blur(14))
    for b in range(9):
        x0 = b * L.W / 9 + 30
        L.path(f"M {x0} 0 Q {x0 + 30} 120 {x0 + 10} 330", "none", "#5a4a30", 3)
        for k in range(12):
            t = k / 12
            M.leaf(L, x0 + 20 * math.sin(t * 3) + 14, 20 + t * 300, 46, 7, 1.3 + rnd.uniform(-0.3, 0.3), "#4e8a46")
    L.rect(0, 0, L.W, 34, "#2e5a2a")
    L.rect(0, L.H - 34, L.W, 34, "#2e5a2a")
    L.rect(0, 30, L.W, 4, g, cls="foil")
    L.rect(0, L.H - 34, L.W, 4, g, cls="foil")
    fx = L.W * 0.25
    L.rect(fx - 210, 96, 420, 170, "#f4f8ec", g, 3, rx=10, cls="emb", op=0.95)
    L.text("Willow Leaf", fx, 160, maxw=370, maxh=88, f="gab", fill="#1e3e1c")
    L.text("GREEN TEA  -  UNSWEETENED", fx, 230, maxw=320, maxh=20, f="bank", fill="#3e6a36", ls=2)
    L.rect(fx + 160, 70, 64, 64, "#b01e24", rx=6, cls="deb")
    M.moon(L, fx + 192, 102, 20, "#f8eadc")
    bx = L.W * 0.75
    M.back_panel(L, bx, 70, 400, 230, "Steeped under the willow",
                 ["First-flush leaves, picked at dawn.", "Clears the head for the second exam."], "#1e3e1c", "#2e5a2a",
                 bg="#f4f8ecdd", seed=15, code="4 902 540 06")


@label("Label_Lemonade", 1000, 320)
def label_lemonade(L):
    L.rect(0, 0, L.W, L.H, L.lin([(0, "#f6ecb8"), (1, "#e2c860")]))
    g = L.gilt()
    rnd = random.Random(16)
    cols = ("#f2d23a", "#ffe98a", "#9ed0e8", "#c8e6a0", "#f2b24a", "#fff4c8")
    for i in range(20):
        for j in range(4):
            x0, y0 = i * L.W / 20, 20 + j * 70
            L.rect(x0, y0, L.W / 20, 70, rnd.choice(cols), INK, 3, op=0.55)
    L.rect(0, 0, L.W, 18, g, cls="foil")
    L.rect(0, L.H - 18, L.W, 18, g, cls="foil")
    fx = L.W * 0.25
    L.path(f"M {fx - 200} 286 L {fx - 200} 112 Q {fx - 200} 46 {fx} 34 Q {fx + 200} 46 {fx + 200} 112 L {fx + 200} 286 Z", "#fff8dc", INK, 10,
           cls="emb", op=0.95)
    L.circle(fx, 88, 46, "none", g, 6, cls="foil emb")
    M.lemon_slice(L, fx, 88, 36)
    L.text("Holy Water", fx, 162, maxw=360, maxh=62, f="black", fill="#5a2a0a", stroke="#5a2a0a", sw=1.6)
    L.text("LEMONADE", fx, 216, maxw=300, maxh=44, f="serif", fill="#9a1a24", ls=4, cls="emb")
    L.text("the chapel's own recipe", fx, 256, maxw=260, maxh=20, f="serifi", fill="#6a4a1a")
    bx = L.W * 0.75
    M.lemon(L, bx - 150, 110, 40)
    M.starburst(L, bx - 150, 220, 52, g, ["BLESSED", "FIZZ"], "#5a2a0a", cls="foil emb", f="serif", rot=8)
    L.rect(bx - 60, 60, 270, 200, "#fff8dc", INK, 3, rx=8, op=0.92)
    L.text("Fizzes a little more", bx + 75, 92, maxw=240, maxh=22, f="serifbi", fill="#5a2a0a")
    L.text("than lemonade should.", bx + 75, 122, maxw=240, maxh=22, f="serifbi", fill="#5a2a0a")
    M.barcode(L, bx - 30, 160, 120, 60, seed=17, digits="4 902 540 07")
    M.okada_stamp(L, bx + 160, 196, 40, "#9a1a24")


# ------------------------------------------------------------------ cartons

def carton_front(L, base, deep, spot, title, nose):
    L.rect(0, 0, L.W, L.H, L.lin([(0, base), (1, deep)]))
    g = L.gilt()
    M.dots(L, 0, 0, L.W, L.H, "#ffffff", 30, 3, op=0.3)
    L.rect(0, 0, L.W, 26, "#fbf6f2")
    M.lace(L, 26, 0, L.W, 20, "#fbf6f2", hole=base)
    M.crest(L, 92, 126, 120)
    L.text("NIGHTMARE HIGH DAIRY", 300, 96, maxw=300, maxh=24, f="bank", fill=INK, ls=1)
    L.text("from the old milking barn", 300, 128, maxw=260, maxh=18, f="serifi", fill="#5a2a3a")
    M.ghost_cow(L, 250, 300, 230, spot=spot, nose=nose)
    L.text(title, 250, 470, maxw=440, maxh=74, f="dutch", fill="#ffffff", stroke=INK, sw=8, cls="emb", shadow=(3, 4, "#000", 0.4))
    L.text("MILK", 250, 540, maxw=240, maxh=64, f="dutch", fill="#ffffff", stroke=INK, sw=8, cls="emb")
    M.ribbon(L, 250, 604, 260, 34, CRIMSON, "fresh from the moo-ghost", "#f8e8d0", f="serifi")
    M.starburst(L, 420, 220, 50, g, ["NEW!", "CREAMIER"], INK, cls="foil emb", f="impact")


def carton_back(L, base, deep, spot, flavour):
    L.rect(0, 0, L.W, L.H, base)
    L.rect(0, 0, L.W, 26, "#fbf6f2")
    M.lace(L, 26, 0, L.W, 20, "#fbf6f2", hole=base)
    L.rect(30, 70, 440, 540, "#fbf6f2", INK, 3, rx=12)
    L.text("MOO-GHOST SAYS", 250, 110, maxw=380, maxh=34, f="dutch", fill=deep)
    lines = ("Drink before the bell.", "Keep cold. Shake well.", f"{flavour}, from cows who", "only graze after dark.",
             "Not for the cafeteria cat.", "Lost? Return to Mrs. Okada.")
    for i, s in enumerate(lines):
        L.text(s, 250, 170 + i * 42, maxw=390, maxh=26, f="serifi", fill=INK)
    M.ghost_cow(L, 130, 500, 110, spot=spot, bell=False)
    M.barcode(L, 230, 440, 190, 60, seed=len(flavour), digits="4 902 540 08")
    M.okada_stamp(L, 400, 565, 34, deep)


def carton_top(L, base, deep, title):
    L.rect(0, 0, L.W, L.H, base)
    L.rect(0, 0, L.W, 20, "#fbf6f2")
    M.lace(L, 20, 0, L.W, 16, "#fbf6f2", hole=base)
    L.text(title, 250, 110, maxw=440, maxh=60, f="dutch", fill="#ffffff", stroke=INK, sw=6, cls="emb")
    L.text("OPEN HERE", 250, 190, maxw=200, maxh=28, f="bank", fill=deep, ls=3)
    for sx in (-1, 1):
        L.poly([(250 + sx * 130, 178), (250 + sx * 150, 190), (250 + sx * 130, 202)], deep)


@label("Carton_Front", 500, 640)
def carton_s_front(L):
    carton_front(L, "#f6c4d0", "#e48aa4", "#d8608a", "STRAWBERRY", "#f8b8c8")
    M.strawberry(L, 70, 590, 60)
    M.strawberry(L, 430, 590, 60)


@label("Carton_Back", 500, 640)
def carton_s_back(L):
    carton_back(L, "#f6c4d0", "#b8406a", "#d8608a", "Strawberry milk")


@label("Carton_Top", 500, 260)
def carton_s_top(L):
    carton_top(L, "#e48aa4", "#8a1a3a", "STRAWBERRY MILK")


@label("ChocoMilk_Front", 500, 640)
def carton_c_front(L):
    carton_front(L, "#c89a72", "#7a4a2a", "#5a321a", "CHOCOLATE", "#e8b8a0")
    for x in (70, 430):
        L.rect(x - 40, 560, 80, 54, "#4a2412", INK, 3, rx=4)
        for i in range(3):
            L.line(x - 40 + (i + 1) * 20, 560, x - 40 + (i + 1) * 20, 614, "#2a1208", 2)
        L.line(x - 40, 587, x + 40, 587, "#2a1208", 2)


@label("ChocoMilk_Back", 500, 640)
def carton_c_back(L):
    carton_back(L, "#c89a72", "#5a321a", "#5a321a", "Chocolate milk")


@label("ChocoMilk_Top", 500, 260)
def carton_c_top(L):
    carton_top(L, "#7a4a2a", "#f2dcc0", "CHOCOLATE MILK")


# ------------------------------------------------------------------ the stand's cups

@label("Cup_Wrap", 1200, 420)
def cup_wrap(L):
    L.rect(0, 0, L.W, L.H, CREAM)
    g = L.gilt()
    M.checker(L, 0, 0, L.W, 40, CRIMSON, "#2a0a10", 20)
    L.rect(0, 40, L.W, 6, g, cls="foil")
    L.rect(0, L.H - 64, L.W, 64, CRIMSON)
    L.rect(0, L.H - 70, L.W, 6, g, cls="foil")
    # a string of paper lanterns and little bats all the way round
    d = "M 0 70 " + " ".join(f"Q {i * 100 + 50} 96 {i * 100 + 100} 70" for i in range(12))
    L.path(d, "none", "#3a2a20", 2)
    for i in range(12):
        x = i * 100 + 50
        if i % 3 == 1:
            M.bat(L, x, 100, 50, body="#2a1430", belly="#4a2a52")
        else:
            M.lantern(L, x, 112, 46, body=CRIMSON if i % 2 else "#d07a2a")
    fx = L.W * 0.25
    M.okada_stamp(L, fx - 150, 250, 92, CRIMSON)
    L.text("OKADA'S", fx + 80, 226, maxw=320, maxh=74, f="dutch", fill=INK, cls="emb", ls=3)
    L.text("CONCESSIONS", fx + 80, 286, maxw=300, maxh=32, f="bank", fill=CRIMSON, ls=5)
    L.text("by the west hall", fx + 80, 322, maxw=220, maxh=22, f="serifi", fill="#5a3a2a")
    bx = L.W * 0.75
    L.text("ON THE MENU TONIGHT", bx, 180, maxw=380, maxh=28, f="bank", fill=CRIMSON, ls=3)
    for i, (a, b) in enumerate((("hot cocoa", "melon soda"), ("pumpkin soup", "barley tea"), ("whatever Mrs. Okada", "says is good"))):
        L.text(a, bx - 110, 222 + i * 32, maxw=200, maxh=22, f="serifi", fill=INK)
        L.text(b, bx + 110, 222 + i * 32, maxw=200, maxh=22, f="serifi", fill=INK)
    for x in (L.W * 0.25, L.W * 0.75):
        L.text("CAREFUL: CONTENTS HOT, MAY BE HAUNTED", x, L.H - 32, maxw=480, maxh=20, f="bank", fill=CREAM, ls=2)


@label("Cocoa_Sleeve", 1100, 200)
def cocoa_sleeve(L):
    L.rect(0, 0, L.W, L.H, "#9a6a40")
    for i in range(110):
        L.rect(i * 10, 0, 4, L.H, "#8a5c36", cls="deb", op=0.6)
    L.rect(0, 0, L.W, 14, "#6a4024")
    L.rect(0, L.H - 14, L.W, 14, "#6a4024")
    for fx in (L.W * 0.25, L.W * 0.75):
        L.circle(fx - 150, 108, 58, "#f2e6d0", INK, 4)
        L.path(f"M {fx - 186} 88 L {fx - 178} 146 L {fx - 122} 146 L {fx - 114} 88 Z", "#5a2a14", INK, 3)
        L.path(f"M {fx - 114} 100 q 22 0 18 20 q -4 16 -20 14", "none", INK, 5)
        M.bat(L, fx - 150, 60, 44, body="#2a1430", belly="#4a2a52")
        L.text("HOT!", fx + 40, 92, maxw=200, maxh=80, f="impact", fill="#f2e6d0", stroke="#3a1a0c", sw=6, cls="emb", rot=-5)
        L.text("hotter than a hellhound's breath", fx + 50, 160, maxw=320, maxh=22, f="serifi", fill="#2a140a")


@label("Ramen_Wrap", 1200, 460)
def ramen_wrap(L):
    L.rect(0, 0, L.W, L.H, L.lin([(0, "#0c0e24"), (0.55, "#2a1a3a"), (1, "#3a0a14")]))
    g = L.gilt()
    rnd = random.Random(21)
    for _ in range(80):
        L.circle(rnd.uniform(0, L.W), rnd.uniform(10, 200), rnd.choice((1.2, 1.8, 2.6)), "#fff4d8", op=rnd.uniform(0.4, 1))
    M.seigaiha(L, 0, L.H - 90, L.W, 90, "#d8a04a", CRIMSON, 30)
    L.rect(0, L.H - 96, L.W, 6, g, cls="foil")
    fx = L.W * 0.25
    L.circle(fx - 170, 120, 76, L.rad([(0, "#fff8dc"), (1, "#f2d48a")]), cls="foil emb")
    M.noodle_bowl(L, fx - 170, 268, 230)
    M.ghost(L, fx - 170, 110, 70, fill="#f4ece0", cheek="#f2a0b8")
    L.text("MIDNIGHT", fx + 110, 140, maxw=330, maxh=76, f="sblack", fill="#fff4d8", stroke=CRIMSON, sw=8, cls="emb",
           shadow=(3, 4, "#000", 0.5))
    L.text("RAMEN", fx + 110, 226, maxw=300, maxh=84, f="sblack", fill=g, stroke=INK, sw=6, cls="foil emb")
    L.text("shoyu  -  soy broth & spring onion", fx + 110, 290, maxw=320, maxh=22, f="serifi", fill="#f2dcb0")
    L.circle(fx + 262, 62, 40, "#fff4d8", CRIMSON, 5)
    L.text("3", fx + 262, 52, size=38, f="sblack", fill=CRIMSON)
    L.text("MIN", fx + 262, 82, size=15, f="bank", fill=CRIMSON)
    bx = L.W * 0.75
    M.back_panel(L, bx, 40, 500, 300, "The midnight method",
                 ["Peel the lid halfway. Add hot water to the line.", "Close. Wait three minutes (count the bells).",
                  "Stir. Slurp loudly. That's the rule.", "Ghosts not included. Usually."], "#f2e6cc", "#ffd88a",
                 bg="#0c0e24cc", seed=22, code="4 902 540 09")


@label("Miso_Wrap", 1200, 420)
def miso_wrap(L):
    L.rect(0, 0, L.W, L.H, L.lin([(0, "#f4e8cc"), (1, "#e2c89a")]))
    g = L.gilt()
    M.seigaiha(L, 0, 0, L.W, 60, "#e2c89a", "#7a4a1c", 30)
    L.rect(0, 60, L.W, 5, g, cls="foil")
    L.rect(0, L.H - 50, L.W, 50, "#5a2e10")
    fx = L.W * 0.25
    L.ellipse(fx - 160, 300, 140, 40, "#7a4a1c")
    L.ellipse(fx - 160, 296, 128, 32, "#c88a3a")
    M.tofu(L, fx - 160, 200, 170)
    L.text("INSTANT", fx + 110, 140, maxw=280, maxh=40, f="bank", fill="#7a3a12", ls=5)
    L.text("MISO", fx + 110, 214, maxw=300, maxh=110, f="sblack", fill="#5a2e10", stroke=g, sw=5, cls="emb")
    L.text("with tofu & wakame", fx + 110, 284, maxw=280, maxh=26, f="serifi", fill="#7a3a12")
    for x in (L.W * 0.25, L.W * 0.75):
        L.text("JUST ADD HOT WATER", x, L.H - 25, maxw=400, maxh=22, f="bank", fill="#f4e8cc", ls=3)
    bx = L.W * 0.75
    M.back_panel(L, bx, 80, 500, 280, "Tofu-kun's soup",
                 ["Warms you from the toes up.", "Red miso, aged in the cellar under the kitchens.", "Stir before you sip."], "#3a1c08",
                 "#7a3a12", bg="#fbf3e2", seed=23, code="4 902 540 10")


# ================================================================== snack bags

def crimps(L, h=42):
    """The heat-sealed crimp bands at a bag's ends, with their teeth (pressed into the height map)."""
    for y0 in (0, L.H - h):
        L.rect(0, y0, L.W, h, "#000", op=0.3)
        for i in range(int(L.W / 10)):
            L.rect(i * 10, y0 + 4, 4, h - 8, "#ffffff", cls="deb", op=0.12)


@label("Crisps_Front", 600, 800)
def crisps_front(L):
    L.rect(0, 0, L.W, L.H, L.lin([(0, "#16141a"), (1, "#0a090c")]))
    hol = L.holo()
    g = L.gilt()
    L.circle(480, 140, 60, L.rad([(0, "#fff8dc"), (1, "#d8c890")]), cls="foil")
    for x, w, h in ((40, 60, 90), (540, 50, 70), (110, 44, 60)):
        L.path(M.tombstone_shape(x, 430, w, h), "#26232c")
    L.path("M 0 470 Q 150 430 300 456 Q 450 480 600 440 L 600 520 L 0 520 Z", "#1e1c22")
    L.path(M.tombstone_shape(300, 270, 300, 330), hol, INK, 5, cls="foil emb")
    L.path(M.tombstone_shape(300, 270, 262, 296), "none", "#ffffff", 2, op=0.6)
    L.text("R.I.P.", 300, 162, maxw=160, maxh=40, f="serif", fill=INK, cls="deb")
    M.skeleton(L, 300, 360, 290)
    L.text("GRAVE", 300, 566, maxw=520, maxh=112, f="impact", fill=BONE, stroke=INK, sw=12, cls="emb", ls=4, shadow=(5, 6, "#000", 0.7))
    L.text("CRISPS", 300, 662, maxw=470, maxh=92, f="impact", fill=g, stroke=INK, sw=10, cls="foil emb", ls=4)
    M.ribbon(L, 300, 722, 340, 38, "#4a7a2a", "SEA SALT & VINEGAR", "#f2f0d8", f="bank")
    M.starburst(L, 118, 160, 70, hol, ["NEW!", "EXTRA", "CRUNCH"], INK, cls="foil emb", f="impact", rot=-14, edge=INK)
    crimps(L)


@label("Crisps_Back", 600, 800)
def crisps_back(L):
    L.rect(0, 0, L.W, L.H, "#121016")
    g = L.gilt()
    L.text("GRAVE CRISPS", 300, 96, maxw=480, maxh=60, f="impact", fill=g, cls="foil emb", ls=3)
    L.text("dug up fresh, every night", 300, 146, maxw=420, maxh=26, f="serifi", fill=BONE)
    L.rect(60, 190, 480, 260, "#1e1b24", g, 3, rx=10)
    L.text("CRUNCH-O-METER", 300, 222, maxw=300, maxh=26, f="bank", fill=g, ls=2)
    L.path("M 140 400 A 160 160 0 0 1 460 400", "none", "#3a3640", 26)
    L.path("M 140 400 A 160 160 0 0 1 430 320", "none", L.holo(), 26, cls="foil")
    L.line(300, 400, 420, 300, BONE, 8)
    L.circle(300, 400, 16, BONE)
    L.text("BONE-SHAKING", 300, 432, maxw=240, maxh=20, f="bank", fill=BONE, ls=2)
    lines = ("Potatoes, sea salt, a splash of vinegar", "and a skeleton who won't stop snacking.",
             "Crunch quietly in the library.", "Share with a friend. Or don't.")
    for i, s in enumerate(lines):
        L.text(s, 300, 494 + i * 36, maxw=480, maxh=24, f="serifi", fill=BONE)
    M.barcode(L, 70, 660, 190, 60, seed=24, digits="4 902 540 11")
    M.skeleton(L, 360, 680, 100)
    M.okada_stamp(L, 490, 690, 46, BONE)
    crimps(L)


@label("Gummies_Front", 600, 760)
def gummies_front(L):
    L.rect(0, 0, L.W, L.H, L.lin([(0, "#5a2a8a"), (1, "#2a0e4a")]))
    M.dots(L, 0, 0, L.W, L.H, "#ffffff", 34, 3, op=0.18)
    # the die-cut window: clear film over a heap of gummy bats
    win = "M 150 430 Q 150 350 300 350 Q 450 350 450 430 L 450 560 Q 450 620 300 620 Q 150 620 150 560 Z"
    L.path(win, "#e8dcf0")
    clip = L.clip(f'<path d="{win}"/>')
    L.begin(extra=clip)
    rnd = random.Random(25)
    for _ in range(34):
        col = rnd.choice(("#c0142a", "#7a2ac0", "#3aa028", "#e8a020"))
        M.gummy_bat(L, rnd.uniform(150, 450), rnd.uniform(360, 630), rnd.uniform(80, 110), col, rot=rnd.uniform(-0.8, 0.8))
    L.path("M 170 380 Q 230 360 260 370 L 200 600 Q 160 580 170 380 Z", "#ffffff", op=0.35)
    L.end()
    L.path(win, "none", "#ffe37a", 8, cls="foil emb")
    M.bat(L, 300, 170, 320)
    L.text("BAT", 300, 318, maxw=220, maxh=86, f="heavy", fill="#ffe37a", stroke="#2a0e4a", sw=10, cls="emb", rot=-4,
           shadow=(4, 5, "#000", 0.5))
    L.text("GUMMIES", 300, 670, maxw=480, maxh=76, f="heavy", fill="#ffe37a", stroke="#2a0e4a", sw=10, cls="emb")
    L.text("blackcurrant  -  cherry  -  lime", 300, 718, maxw=440, maxh=24, f="serifbi", fill="#e8d4ff")
    M.starburst(L, 500, 290, 58, L.holo(), ["SOUR", "WINGS"], "#2a0e4a", cls="foil emb", f="impact", rot=10)
    crimps(L, h=34)


@label("Gummies_Back", 600, 760)
def gummies_back(L):
    L.rect(0, 0, L.W, L.H, "#2a0e4a")
    M.bat(L, 300, 160, 200)
    L.text("BATSY'S FLIGHT GUIDE", 300, 290, maxw=470, maxh=40, f="heavy", fill="#ffe37a")
    for i, (c, s) in enumerate((("#c0142a", "red: cherry, for courage"), ("#5a1aa0", "violet: blackcurrant, for night vision"),
                                ("#3aa028", "green: lime, for speed"), ("#e8a020", "gold: honey, very rare!"))):
        M.gummy_bat(L, 110, 360 + i * 60, 90, c)
        L.text(s, 330, 360 + i * 60, maxw=380, maxh=26, f="serifi", fill="#f0e4ff")
    M.barcode(L, 70, 620, 190, 60, seed=26, digits="4 902 540 12")
    M.okada_stamp(L, 470, 650, 50, "#ffe37a")
    crimps(L, h=34)


@label("Konpeito_Front", 560, 520)
def konpeito_front(L):
    L.rect(0, 0, L.W, L.H, L.lin([(0, "#1a1e4a"), (1, "#0c0e2a")]))
    g = L.gilt()
    rnd = random.Random(27)
    for _ in range(60):
        L.circle(rnd.uniform(0, L.W), rnd.uniform(0, L.H), rnd.choice((1.2, 2, 3)), "#fff4d8", op=rnd.uniform(0.4, 1))
    M.frame(L, 18, 18, L.W - 36, L.H - 36, g, sw=4, cls="foil emb")
    M.star(L, 140, 160, 92, L.lin([(0, "#fff0a0"), (1, "#f2b830")]), cls="emb", stroke=INK, sw=4)
    for sx in (-1, 1):
        L.circle(140 + sx * 22, 160, 8, INK)
        L.ellipse(140 + sx * 38, 182, 10, 6, "#f08aa0", op=0.8)
    L.path("M 124 188 Q 140 202 156 188", "none", INK, 4)
    for i, col in enumerate(("#f6a8c0", "#fff0a0", "#a8d8ff", "#c8f0b0", "#e0c8ff", "#ffffff")):
        M.star(L, 300 + (i % 3) * 70, 120 + (i // 3) * 70, 26, col, n=8, inner=0.66, rot=i * 0.4, stroke=INK, sw=2)
    L.text("KONPEITO", 280, 320, maxw=460, maxh=86, f="dutch", fill=g, stroke=INK, sw=5, cls="foil emb", ls=3)
    L.text("STARS", 280, 396, maxw=260, maxh=50, f="bank", fill="#fff4d8", ls=8)
    L.text("sugar stars, picked from the sky", 280, 448, maxw=420, maxh=24, f="serifi", fill="#d8dcff")


@label("Konpeito_Back", 560, 520)
def konpeito_back(L):
    L.rect(0, 0, L.W, L.H, "#f2e6cc")
    M.frame(L, 18, 18, L.W - 36, L.H - 36, CRIMSON, sw=4)
    M.back_panel(L, 280, 40, 480, 440, "How sugar stars are made",
                 ["A grain of sugar, a copper pan,", "and fourteen nights of patient turning.", "One wish per star. No refunds."], INK,
                 CRIMSON, seed=28, code="4 902 540 13")


@label("Popcorn_Side", 500, 640)
def popcorn_side(L):
    M.stripes(L, 0, 0, L.W, L.H, CREAM, "#b0141e", 100)
    g = L.gilt()
    L.rect(40, 210, 420, 330, "#1a0a0e", g, 6, rx=20, cls="emb")
    for i in range(14):
        L.circle(70 + i * 28.5, 228, 7, "#ffe9a0", cls="foil")
        L.circle(70 + i * 28.5, 522, 7, "#ffe9a0", cls="foil")
    rnd = random.Random(29)
    for _ in range(40):
        L.circle(rnd.uniform(60, 440), rnd.uniform(70, 200), rnd.uniform(16, 26), "#f8eecc", "#d8b878", 2)
    M.ghost(L, 250, 120, 150)
    L.text("SPOOKY", 250, 300, maxw=360, maxh=70, f="impact", fill="#ffe9a0", stroke=CRIMSON, sw=6, cls="emb", ls=4)
    L.text("POP", 250, 400, maxw=280, maxh=130, f="impact", fill="#ffffff", stroke=CRIMSON, sw=8, cls="emb", ls=8)
    L.text("buttered & salted", 250, 480, maxw=300, maxh=28, f="serifi", fill="#f2dca8")
    L.rect(0, 600, L.W, 40, "#1a0a0e")
    L.text("NOW SHOWING", 250, 620, maxw=300, maxh=22, f="bank", fill=g, cls="foil", ls=4)


@label("Popcorn_Back", 500, 640)
def popcorn_back(L):
    M.stripes(L, 0, 0, L.W, L.H, CREAM, "#b0141e", 100)
    L.rect(40, 60, 420, 520, "#fbf3e0", INK, 4, rx=14)
    L.text("TONIGHT'S FEATURE", 250, 110, maxw=360, maxh=34, f="bank", fill=CRIMSON, ls=3)
    L.text("The Haunted Hallway", 250, 170, maxw=360, maxh=46, f="black", fill=INK, stroke=INK, sw=1.2)
    for i, s in enumerate(("Row G, seat 13. Of course.", "Lights out at the bell.", "No talking. No screaming.", "(Some screaming.)")):
        L.text(s, 250, 240 + i * 40, maxw=360, maxh=26, f="serifi", fill=INK)
    L.rect(70, 420, 360, 90, "#e8c860", INK, 3, rx=6)
    L.line(160, 420, 160, 510, INK, 3, extra='stroke-dasharray="6 6"')
    L.text("ADMIT ONE", 295, 465, maxw=230, maxh=38, f="bank", fill=INK, ls=3)
    M.barcode(L, 80, 530, 150, 36, seed=30, digits="4 902 540 14")
    M.okada_stamp(L, 380, 548, 30, CRIMSON)


@label("Imo_Bag", 560, 640)
def imo_bag(L):
    L.rect(0, 0, L.W, L.H, "#a8784a")
    rnd = random.Random(32)
    for _ in range(300):
        x, y = rnd.uniform(0, L.W), rnd.uniform(0, L.H)
        L.line(x, y, x + rnd.uniform(-8, 8), y + rnd.uniform(-3, 3), "#8a5e36", 1, op=0.5)
    for k in (-1, 0, 1):
        L.path(f"M {280 + k * 50} 220 q 20 -30 0 -60 q -20 -30 0 -60", "none", "#f2e6d0", 8, op=0.8)
    L.ellipse(280, 330, 190, 30, "#5a4a3a")
    L.path("M 120 300 Q 140 230 260 236 L 280 320 Q 170 330 120 300 Z", "#7a1a3a", INK, 4)
    L.path("M 300 236 Q 430 230 450 300 Q 400 330 290 320 Z", "#7a1a3a", INK, 4)
    L.ellipse(270, 280, 22, 44, "#f2c24a", INK, 3)
    L.ellipse(300, 280, 22, 44, "#f6cf5a", INK, 3)
    L.text("YAKI-IMO", 280, 430, maxw=470, maxh=96, f="sblack", fill="#3a1608", cls="emb", ls=2)
    L.text("roasted on hot stones", 280, 496, maxw=380, maxh=30, f="serifi", fill="#3a1608")
    L.rect(408, 40, 110, 110, "#b01e24", rx=8, cls="deb")
    L.text("HOT", 463, 95, maxw=90, maxh=54, f="impact", fill="#f8e8d0")
    M.okada_stamp(L, 110, 566, 52, "#3a1608")
    L.text("eat while it's warm", 360, 576, maxw=260, maxh=26, f="hand", fill="#3a1608")


# ================================================================== lids, tins and flat faces

@label("Mints_Lid", 560, 560)
def mints_lid(L):
    L.rect(0, 0, L.W, L.H, "#1e4a56")
    sv = L.silver()
    L.circle(280, 280, 272, sv, cls="foil emb")
    L.circle(280, 280, 244, L.rad([(0, "#3a7e8c"), (1, "#123a44")]))
    for i in range(24):
        a = i * math.pi / 12
        M.quatrefoil(L, 280 + math.cos(a) * 258, 280 + math.sin(a) * 258, 8, "#1e4a56")
    for k in range(5):
        r = 60 + k * 30
        L.path(f"M {280 - r} 280 A {r} {r} 0 0 1 {280 + r * 0.7} {280 - r * 0.7}", "none", sv, 3, cls="foil", op=0.8)
    M.ghost(L, 280, 220, 190)
    L.path("M 330 236 q 60 -10 90 30 q 20 30 -10 40", "none", "#dff8ff", 6, op=0.9)
    for x, y in ((420, 300), (440, 250), (400, 330)):
        M.sparkle(L, x, y, 14, sv, cls="foil")
    L.text("GHOST MINTS", 280, 380, maxw=380, maxh=52, f="dutch", fill=sv, stroke="#0a2228", sw=5, cls="foil emb", ls=2)
    L.text("cold as the grave", 280, 432, maxw=280, maxh=26, f="serifi", fill="#dff8ff")


@label("Mints_Side", 1100, 90)
def mints_side(L):
    L.rect(0, 0, L.W, L.H, "#1e4a56")
    sv = L.silver()
    L.rect(0, 0, L.W, 8, sv, cls="foil")
    L.rect(0, L.H - 8, L.W, 8, sv, cls="foil")
    for i in range(5):
        x = i * L.W / 5 + L.W / 10
        L.text("GHOST MINTS", x - 30, 45, maxw=150, maxh=30, f="bank", fill=sv, cls="foil", ls=2)
        M.ghost(L, x + 80, 48, 50)


@label("Choc_Wrapper", 900, 420)
def choc_wrapper(L):
    L.rect(0, 0, L.W, L.H, L.lin([(0, "#121a4a"), (1, "#070a24")]))
    g = L.gilt()
    rnd = random.Random(33)
    for _ in range(50):
        M.star(L, rnd.uniform(30, L.W - 30), rnd.uniform(30, L.H - 30), rnd.uniform(3, 9), g, cls="foil")
    M.frame(L, 16, 16, L.W - 32, L.H - 32, g, sw=4, cls="foil emb")
    # the sleeping moon in a nightcap
    L.circle(200, 220, 130, L.rad([(0, "#fff8dc"), (1, "#e8c870")]), cls="foil emb")
    L.path("M 150 210 Q 170 224 190 210", "none", "#8a6a2a", 5)
    L.path("M 230 210 Q 250 224 270 210", "none", "#8a6a2a", 5)
    L.path("M 190 262 Q 210 274 230 262", "none", "#8a6a2a", 5)
    L.path("M 92 150 Q 200 40 318 130 Q 360 70 398 50 L 408 70 Q 380 80 350 160 Z", "#3a0a2a", INK, 3)
    L.circle(403, 58, 16, "#ffffff")
    for x, y, s in ((340, 150, 20), (370, 118, 26), (402, 90, 32)):
        L.text("z", x, y, size=s, f="serifbi", fill="#e8e4d8")
    L.text("MOONLIGHT", 610, 168, maxw=440, maxh=78, f="serif", fill=g, stroke="#06082a", sw=3, cls="foil emb", ls=3,
           shadow=(3, 4, "#000", 0.6))
    L.text("dark chocolate  -  72% cocoa", 610, 238, maxw=380, maxh=30, f="serifi", fill="#e8e4d8")
    M.ribbon(L, 610, 304, 300, 40, CRIMSON, "MIDNIGHT EDITION", "#f2dca8", f="bank")
    L.text("Nightmare High tuck shop", 610, 362, maxw=300, maxh=20, f="serifi", fill="#9aa0c8")


@label("Licorice_Band", 900, 200)
def licorice_band(L):
    L.rect(0, 0, L.W, L.H, L.lin([(0, "#2a0a3a"), (1, "#120418")]))
    g = L.gilt()
    L.rect(0, 10, L.W, 5, g, cls="foil")
    L.rect(0, L.H - 15, L.W, 5, g, cls="foil")
    for fx in (L.W * 0.25, L.W * 0.75):
        L.text("Witch's Whips", fx, 84, maxw=340, maxh=70, f="black", fill=g, stroke=g, sw=1.8, cls="foil emb")
        L.text("BLACK LICORICE", fx, 146, maxw=260, maxh=24, f="bank", fill="#e8d8ff", ls=4)
        M.star(L, fx - 196, 100, 16, g, cls="foil")
        M.star(L, fx + 196, 100, 16, g, cls="foil")


@label("Bento_Band", 1000, 200)
def bento_band(L):
    M.seigaiha(L, 0, 0, L.W, L.H, "#a07a3a", "#120e10", 34)
    g = L.gilt()
    L.rect(0, 10, L.W, 6, g, cls="foil")
    L.rect(0, L.H - 16, L.W, 6, g, cls="foil")
    L.rect(250, 30, 500, 140, CRIMSON, g, 4, rx=10, cls="emb")
    M.moon(L, 310, 100, 40, g, cls="foil emb")
    L.text("Night Bento", 530, 92, maxw=360, maxh=70, f="black", fill=g, stroke=g, sw=1.8, cls="foil emb")
    L.text("kept back for the night crowd", 530, 144, maxw=340, maxh=22, f="serifi", fill="#f2dca8")


@label("Onigiri_Band", 900, 160)
def onigiri_band(L):
    L.rect(0, 0, L.W, L.H, "#f4f2ee")
    L.rect(0, 0, L.W, 18, "#b01e24")
    L.rect(0, L.H - 18, L.W, 18, "#b01e24")
    L.circle(90, 80, 44, L.rad([(0, "#ff7a8a"), (1, "#8a0e24")]), INK, 3)
    M.leaf(L, 110, 40, 36, 8, -0.5, "#3a7a2a")
    L.text("UME ONIGIRI", 420, 64, maxw=480, maxh=58, f="sblack", fill=INK, ls=2)
    for i, s in enumerate(("1", "2", "3")):
        x = 260 + i * 160
        L.circle(x, 116, 15, "#b01e24")
        L.text(s, x, 116, size=20, f="sblack", fill="#ffffff")
        if i < 2:
            L.poly([(x + 30, 108), (x + 120, 108), (x + 120, 100), (x + 140, 116), (x + 120, 132), (x + 120, 124), (x + 30, 124)], "#b01e24")
    M.okada_stamp(L, 820, 80, 50, "#b01e24")


@label("Ramen_Lid", 560, 560)
def ramen_lid(L):
    L.rect(0, 0, L.W, L.H, "#f4ecdc")
    g = L.gilt()
    L.circle(280, 280, 272, CRIMSON)
    L.circle(280, 280, 240, "#f4ecdc")
    L.circle(280, 280, 252, "none", g, 5, cls="foil")
    M.noodle_bowl(L, 280, 220, 200)
    L.text("MIDNIGHT", 280, 350, maxw=360, maxh=58, f="sblack", fill=INK, cls="emb")
    L.text("RAMEN", 280, 412, maxw=260, maxh=56, f="sblack", fill=CRIMSON, cls="emb")
    L.text("peel to here", 280, 466, maxw=160, maxh=20, f="serifi", fill=INK)
    L.line(200, 486, 360, 486, INK, 2, extra='stroke-dasharray="8 6"')
    L.circle(450, 130, 42, "#fff4d8", CRIMSON, 5)
    L.text("3", 450, 120, size=38, f="sblack", fill=CRIMSON)
    L.text("MIN", 450, 150, size=15, f="bank", fill=CRIMSON)


@label("Prank_Label", 700, 460)
def prank_label(L):
    L.rect(0, 0, L.W, L.H, "#b8905e")
    M.stripes(L, 0, 0, L.W, 40, "#f2c21a", "#1a1414", 40, angle=45)
    M.stripes(L, 0, L.H - 40, L.W, 40, "#f2c21a", "#1a1414", 40, angle=45)
    M.starburst(L, 190, 180, 116, "#f2c21a", ["KA-", "BOOM!"], "#b01e24", f="impact", edge=INK)
    # a cartoon stink bomb with a lit fuse and a grin
    L.circle(520, 200, 80, "#2a3a2a", INK, 4)
    L.ellipse(495, 175, 20, 12, "#ffffff", op=0.4)
    L.path("M 560 140 q 30 -40 60 -30", "none", "#8a7a5a", 6)
    M.sparkle(L, 624, 108, 22, "#ffd84a")
    for sx in (-1, 1):
        L.circle(520 + sx * 26, 196, 10, "#ffffff")
        L.circle(520 + sx * 26 + 3, 198, 5, INK)
    L.path("M 490 230 Q 520 252 550 230", "none", "#ffffff", 5)
    for k in range(3):
        L.path(f"M {470 + k * 40} 310 q 10 -20 0 -40", "none", "#7aa040", 5, op=0.8)
    L.text("PRANK KIT", 350, 350, maxw=600, maxh=80, f="impact", fill="#1a1414", ls=4, cls="emb")
    L.rect(150, 386, 400, 30, "#b01e24", rx=4)
    L.text("DO NOT OPEN IN CLASS", 350, 401, maxw=380, maxh=20, f="bank", fill="#f8e8d0", ls=3)
    L.text("(we never sold you this)", 560, 70, maxw=240, maxh=24, f="hand", fill="#1c2a6a", rot=4)


@label("Senbei_Sleeve", 600, 400)
def senbei_sleeve(L):
    L.rect(0, 0, L.W, L.H, "#ece0c4")
    L.rect(0, 0, L.W, 30, "#3a1c10")
    L.rect(0, L.H - 30, L.W, 30, "#3a1c10")
    # a woodblock moon over rice paddies, a crane crossing it
    L.circle(160, 150, 90, "#f2c24a")
    for k in range(4):
        L.path(f"M 30 {236 + k * 26} Q 160 {220 + k * 26} 290 {236 + k * 26}", "none", "#5a7a3a", 6)
    # a crane in flight across the moon: neck out, wings raised, legs trailing
    L.path("M 70 168 Q 96 150 120 152", "none", "#f4f0e6", 7)
    L.circle(70, 168, 8, "#f4f0e6")
    L.circle(70, 164, 3.5, "#c01a24")
    L.poly([(58, 170), (40, 176), (60, 174)], INK)
    L.ellipse(150, 154, 38, 14, "#f4f0e6", INK, 2)
    L.path("M 130 150 Q 150 80 210 60 Q 190 110 172 148 Z", "#f4f0e6", INK, 2)
    L.path("M 140 156 Q 180 200 236 196 Q 200 176 168 156 Z", "#e8e2d6", INK, 2)
    L.path("M 160 70 L 200 64 M 170 92 L 196 84", "none", INK, 2)
    L.path("M 186 156 L 248 172 M 186 160 L 246 180", "none", INK, 2.5)
    L.text("SENBEI", 430, 150, maxw=290, maxh=86, f="sblack", fill="#3a1c10", cls="emb", ls=4)
    L.text("soy-glazed rice cracker", 430, 214, maxw=280, maxh=26, f="serifi", fill="#7a3a12")
    L.rect(380, 250, 100, 100, "#b01e24", rx=6, cls="deb")
    L.text("NH", 430, 300, maxw=70, maxh=50, f="black", fill="#f8e8d0", stroke="#f8e8d0", sw=1.5)
    M.okada_stamp(L, 540, 300, 40, "#3a1c10")


@label("MeatLoaf_Stamp", 600, 400)
def meatloaf_stamp(L):
    L.rect(0, 0, L.W, L.H, "#b08458")
    rnd = random.Random(34)
    for _ in range(18):
        L.text("?", rnd.uniform(20, 580), rnd.uniform(20, 380), size=rnd.uniform(30, 60), f="impact", fill="#9a7048", rot=rnd.uniform(-30, 30))
    L.rect(40, 50, 520, 300, "none", "#6a1020", 6, cls="deb")
    L.rect(52, 62, 496, 276, "none", "#6a1020", 2, cls="deb")
    L.text("MYSTERY", 300, 120, maxw=420, maxh=78, f="impact", fill="#6a1020", cls="deb", ls=3)
    L.text("MEAT LOAF", 300, 200, maxw=460, maxh=78, f="impact", fill="#6a1020", cls="deb", ls=3)
    L.text("contents: yes.", 300, 258, maxw=300, maxh=30, f="serifi", fill="#3a1a10")
    M.ribbon(L, 300, 306, 260, 34, "#6a1020", "TUESDAY SPECIAL", "#f2dca8", f="bank")
    L.text("don't ask - Mrs. O.", 460, 374, maxw=200, maxh=22, f="hand", fill="#1c2a6a", rot=-4)


@label("Pudding_Lid", 480, 480)
def pudding_lid(L):
    L.rect(0, 0, L.W, L.H, "#f6eedc")
    g = L.gilt()
    M.dots(L, 0, 0, L.W, L.H, "#e8c86a", 28, 3, op=0.4)
    L.circle(240, 240, 232, "none", g, 10, cls="foil emb")
    M.pudding_mascot(L, 240, 200, 200)
    L.text("CUSTARD", 240, 330, maxw=320, maxh=52, f="dutch", fill="#6a2a0a", cls="emb", ls=2)
    L.text("PUDDING", 240, 384, maxw=300, maxh=48, f="dutch", fill="#6a2a0a", cls="emb", ls=2)
    L.text("with burnt caramel", 240, 424, maxw=220, maxh=22, f="serifi", fill=CRIMSON)


@label("Ecto_Lid", 480, 480)
def ecto_lid(L):
    L.rect(0, 0, L.W, L.H, "#123a2c")
    hol = L.holo()
    L.circle(240, 240, 232, "none", hol, 10, cls="foil emb")
    L.circle(240, 200, 120, "#7affb0", cls="fx", op=0.25, extra=L.blur(20))
    M.ghost(L, 240, 190, 190, fill="#a8ffc8", cheek="#6ad89a")
    L.text("ECTOPLASM", 240, 330, maxw=360, maxh=52, f="impact", fill="#b8ffd0", stroke="#0a2a1e", sw=5, cls="emb", ls=3)
    L.text("JELLY", 240, 384, maxw=200, maxh=44, f="impact", fill=hol, cls="foil emb", ls=6)
    L.text("It wobbles on its own.", 240, 424, maxw=230, maxh=20, f="serifi", fill="#dcffe8")


@label("Soup_Lid", 480, 480)
def soup_lid(L):
    L.rect(0, 0, L.W, L.H, CREAM)
    L.circle(240, 240, 228, "none", CRIMSON, 12)
    M.pumpkin(L, 240, 238, 200)
    L.text_arc("PUMPKIN SOUP", 240, 240, 186, 38, f="dutch", fill=CRIMSON, ls=3)
    L.text_arc("hot - sip slowly", 240, 240, 186, 26, f="serifi", fill=INK, top=False)


@label("FruitCup_Lid", 480, 480)
def fruitcup_lid(L):
    sv = L.silver()
    L.rect(0, 0, L.W, L.H, sv, cls="foil")
    L.circle(240, 240, 220, "#f4ecd8", cls="emb")
    L.circle(240, 240, 220, "none", "#c01a2a", 8)
    M.strawberry(L, 170, 200, 110)
    M.lemon_slice(L, 300, 170, 54)
    L.circle(262, 262, 40, L.rad([(0, "#ffb070"), (1, "#e06a1a")]), INK, 3)
    L.circle(322, 262, 30, L.rad([(0, "#c8a0ff"), (1, "#5a2a8a")]), INK, 3)
    L.text("FRUIT CUP", 240, 350, maxw=320, maxh=56, f="dutch", fill="#c01a2a", cls="emb", ls=2)
    L.text("in light syrup", 240, 396, maxw=200, maxh=22, f="serifi", fill=INK)
    L.poly([(410, 410), (470, 470), (430, 470)], "#c01a2a")


@label("MoonCake_Top", 512, 512)
def mooncake_top(L):
    """Not a label: the moon cake's stamped pastry top (golden; the relief is in the height map)."""
    L.rect(0, 0, L.W, L.H, "#b8762e")
    L.circle(256, 256, 250, L.rad([(0, "#d89a48"), (0.8, "#b87430"), (1, "#8a5220")]))
    for i in range(16):
        a = i * math.pi / 8
        L.ellipse(256 + math.cos(a) * 214, 256 + math.sin(a) * 214, 30, 18, "#c88638", "#7a4418", 3, rot=math.degrees(a), cls="emb")
    L.circle(256, 256, 186, "none", "#7a4418", 6, cls="emb")
    L.circle(256, 256, 170, "#c88a3c", cls="deb")
    M.moon(L, 200, 220, 56, "#e0a24e", cls="emb")
    L.text("NH", 300, 236, maxw=140, maxh=100, f="black", fill="#e0a24e", stroke="#e0a24e", sw=4, cls="emb")
    for i in range(5):
        M.star(L, 170 + i * 43, 330, 13, "#e0a24e", cls="emb")
    L.circle(256, 256, 250, "none", "#6a3a14", 6, op=0.8)


@label("Cookie_Icing", 400, 560)
def cookie_icing(L):
    L.rect(0, 0, L.W, L.H, L.lin([(0, "#b8b0c8"), (1, "#8e86a0")]))
    rnd = random.Random(35)
    for _ in range(40):
        x, y = rnd.uniform(30, 370), rnd.uniform(30, 530)
        L.rect(x, y, 10, 3, rnd.choice(("#f2a0c0", "#a0e0f0", "#f8f0a0", "#ffffff")), rx=1.5,
               extra=f'transform="rotate({rnd.uniform(0, 180):.0f} {x:.1f} {y:.1f})"', cls="emb")
    L.rect(26, 26, L.W - 52, L.H - 52, "none", "#f4f2ee", 10, rx=30, cls="emb")
    L.text("R.I.P.", 200, 210, maxw=280, maxh=92, f="serif", fill="#f4f2ee", stroke="#f4f2ee", sw=3, cls="emb")
    L.text("homework", 200, 300, maxw=280, maxh=58, f="script", fill="#f4f2ee", cls="emb")
    M.ghost(L, 200, 420, 110, fill="#f4f2ee")


@label("Boat_Print", 600, 400)
def boat_print(L):
    L.rect(0, 0, L.W, L.H, "#c8a87a")
    M.checker(L, 0, 0, L.W, 26, "#b01e24", "#f2e6cc", 13)
    M.checker(L, 0, L.H - 26, L.W, 26, "#b01e24", "#f2e6cc", 13)
    M.octopus(L, 140, 190, 220)
    L.text("TAKOYAKI", 400, 160, maxw=330, maxh=70, f="sblack", fill="#3a1608", cls="emb", ls=2)
    L.text("six hot ones, careful!", 400, 222, maxw=300, maxh=28, f="serifi", fill="#7a1a10")
    M.okada_stamp(L, 470, 300, 50, "#b01e24")


@label("Napkin_Plate", 600, 200)
def napkin_plate(L):
    L.rect(0, 0, L.W, L.H, L.gilt(horiz=True), cls="foil")
    L.rect(10, 10, L.W - 20, L.H - 20, "none", "#5a3a10", 4, rx=10, cls="deb")
    L.text("NAPKINS", 300, 86, maxw=420, maxh=80, f="black", fill="#4a2e0c", stroke="#4a2e0c", sw=2, cls="deb")
    L.text("take only what you need", 300, 152, maxw=320, maxh=26, f="serifi", fill="#4a2e0c", cls="deb")
    for x in (44, 556):
        M.quatrefoil(L, x, 100, 22, "#4a2e0c", cls="deb")


@label("Label_Soy", 700, 260)
def label_soy(L):
    L.rect(0, 0, L.W, L.H, "#ece2c8")
    L.rect(0, 0, L.W, 18, "#2a120a")
    L.rect(0, L.H - 18, L.W, 18, "#2a120a")
    for fx in (L.W * 0.25, L.W * 0.75):
        L.text("SHOYU", fx - 10, 112, maxw=240, maxh=90, f="sblack", fill="#2a120a", cls="emb", ls=3)
        L.text("dark soy sauce", fx - 10, 178, maxw=220, maxh=26, f="serifi", fill=CRIMSON)
        L.rect(fx + 120, 50, 40, 40, "#b01e24", rx=4)


@label("Label_Mustard", 700, 260)
def label_mustard(L):
    L.rect(0, 0, L.W, L.H, "#e8b82a")
    L.rect(0, 0, L.W, 18, "#7a1a10")
    L.rect(0, L.H - 18, L.W, 18, "#7a1a10")
    for fx in (L.W * 0.25, L.W * 0.75):
        L.path(f"M {fx - 140} 160 q -20 -40 6 -76 q 4 30 20 34 q -4 -40 24 -62 q 0 50 30 64 q 10 -20 6 -40 q 30 30 14 80 Z", "#d8401a", INK, 2)
        L.text("KARASHI", fx + 40, 110, maxw=230, maxh=70, f="sblack", fill="#3a0e06", cls="emb", ls=2)
        L.text("hot mustard - very hot", fx + 40, 172, maxw=220, maxh=24, f="serifi", fill="#7a1a10")


def jar_label(L, title, sub, col, motif):
    L.rect(0, 0, L.W, L.H, "#efe2c0")
    g = L.gilt()
    L.rect(10, 10, L.W - 20, L.H - 20, "none", g, 5, rx=16, cls="foil emb")
    L.rect(22, 22, L.W - 44, L.H - 44, "none", col, 2, rx=10)
    motif(L)
    L.text(title, 296, 120, maxw=248, maxh=56, f="dutch", fill=col, cls="emb")
    L.text(sub, 296, 180, maxw=230, maxh=28, f="serifi", fill=INK)
    L.text("No. 13", 296, 236, maxw=120, maxh=22, f="bank", fill=col, ls=3)


@label("Jar_Gummies", 460, 300)
def jar_gummies(L):
    jar_label(L, "BAT GUMMIES", "by the scoop", "#4a1a7a", lambda L: M.bat(L, 82, 150, 120))


@label("Jar_Konpeito", 460, 300)
def jar_konpeito(L):
    def m(L):
        for i, c in enumerate(("#f6a8c0", "#fff0a0", "#a8d8ff")):
            M.star(L, 70 + (i % 2) * 40, 100 + i * 50, 24, c, n=8, inner=0.66, stroke=INK, sw=2)
    jar_label(L, "KONPEITO", "sugar stars", CRIMSON, m)


@label("Jar_Mints", 460, 300)
def jar_mints(L):
    jar_label(L, "GHOST MINTS", "two for a coin", "#1e4a56", lambda L: M.ghost(L, 82, 154, 130))


@label("Ramune_Cap", 300, 300)
def ramune_cap(L):
    hol = L.holo()
    L.rect(0, 0, L.W, L.H, hol, cls="foil")
    L.circle(150, 150, 140, "#0b1640", cls="emb")
    L.circle(150, 150, 140, "none", hol, 8, cls="foil")
    L.circle(150, 126, 60, L.rad([(0, "#e8fbff"), (0.45, "#5ad0e0"), (1, "#0a5a78")], cx=0.35, cy=0.3), "#e8f4ff", 3)
    L.ellipse(132, 104, 16, 10, "#ffffff", op=0.9)
    for a in range(5):
        M.star(L, 150 + math.cos(a * 1.2566 - 1.57) * 110, 150 + math.sin(a * 1.2566 - 1.57) * 110, 10, hol, cls="foil")
    L.text("MOONWELL", 150, 222, maxw=170, maxh=28, f="dutch", fill=hol, cls="foil emb", ls=2)


@label("Crate_Stencil", 900, 260)
def crate_stencil(L):
    L.rect(0, 0, L.W, L.H, "#8a6640")
    L.text("MOONWELL RAMUNE", 470, 96, maxw=700, maxh=96, f="bank", fill="#1a120c", op=0.85, ls=6)
    L.text("24 BOTTLES  -  FRAGILE  -  THIS WAY UP", 470, 186, maxw=600, maxh=34, f="bank", fill="#1a120c", op=0.8, ls=3)
    for x in (40, 860):
        L.poly([(x - 10, 230), (x - 10, 170), (x - 30, 170), (x, 130), (x + 30, 170), (x + 10, 170), (x + 10, 230)], "#1a120c", op=0.8)
    L.circle(60, 70, 34, "none", "#1a120c", 5, op=0.8)
    M.star(L, 60, 70, 18, "#1a120c")


@label("Tray_Stencil", 900, 260)
def tray_stencil(L):
    L.rect(0, 0, L.W, L.H, "#7a1420")
    g = L.gilt()
    L.rect(0, 12, L.W, 6, g, cls="foil")
    L.rect(0, L.H - 18, L.W, 6, g, cls="foil")
    M.cat(L, 110, 140, 160)
    L.text("BLACK CAT COLA", 510, 104, maxw=620, maxh=76, f="heavy", fill="#f2e6cc", stroke=INK, sw=5, cls="emb", ls=3)
    L.text("12 CANS  -  ICE COLD  -  FOR MRS. OKADA'S STAND", 510, 184, maxw=620, maxh=26, f="bank", fill=GOLD, ls=2)


# ================================================================== lunch

def refectory_frame(L):
    L.rect(0, 0, L.W, L.H, "#ece0c2")
    rnd = random.Random(36)
    for _ in range(120):
        L.circle(rnd.uniform(0, L.W), rnd.uniform(0, L.H), rnd.uniform(4, 16), "#d8c49a", op=0.25, cls="fx")
    M.frame(L, 20, 20, L.W - 40, L.H - 40, CRIMSON, sw=5, inset=12)


@label("Tray_Mat", 900, 640)
def tray_mat(L):
    refectory_frame(L)
    M.crest(L, 150, 160, 160)
    L.text("Nightmare High", 530, 104, maxw=540, maxh=70, f="black", fill=INK, stroke=INK, sw=1.8)
    L.text("REFECTORY", 530, 172, maxw=360, maxh=36, f="bank", fill=CRIMSON, ls=8)
    L.line(270, 206, 790, 206, CRIMSON, 3)
    L.text("THIS WEEK'S LUNCHES", 450, 262, maxw=440, maxh=30, f="bank", fill=INK, ls=3)
    menu = (("Monday", "Katsu Curry Rice"), ("Tuesday", "Graveyard Shepherd's Pie"), ("Wednesday", "Shoyu Ramen"),
            ("Thursday", "Witching Hour Stew"), ("Friday", "Karaage & Rice"))
    for i, (d, m) in enumerate(menu):
        y = 316 + i * 52
        L.text(d, 230, y, maxw=180, maxh=30, f="serifbi", fill=CRIMSON)
        L.line(330, y + 8, 400, y + 8, INK, 1.5, extra='stroke-dasharray="3 6"')
        L.text(m, 590, y, maxw=360, maxh=32, f="serifr", fill=INK)
    M.raven(L, 790, 555, 90, INK)
    L.text("crumbs feed the crows", 640, 600, maxw=200, maxh=22, f="hand", fill="#1c2a6a", rot=-4)


@label("Tray_MatB", 900, 640)
def tray_matb(L):
    refectory_frame(L)
    L.text("Lunch Period", 450, 96, maxw=560, maxh=74, f="black", fill=INK, stroke=INK, sw=1.8)
    L.text("THE BELLS", 450, 160, maxw=300, maxh=30, f="bank", fill=CRIMSON, ls=8)
    rows = (("12:00", "first bell", "queue at the counter"), ("12:10", "grace", "said by a prefect"), ("12:30", "second bell", "seconds, if any"),
            ("12:50", "third bell", "trays back, crows out"))
    for i, (t, a, b) in enumerate(rows):
        y = 220 + i * 56
        L.circle(130, y, 20, "none", CRIMSON, 3)
        L.line(130, y, 130, y - 12, CRIMSON, 3)
        L.line(130, y, 140, y, CRIMSON, 3)
        L.text(t, 220, y, maxw=110, maxh=30, f="serif", fill=INK)
        L.text(a, 390, y, maxw=180, maxh=28, f="serifbi", fill=CRIMSON)
        L.text(b, 640, y, maxw=280, maxh=26, f="serifi", fill=INK)
    for i, (c1, c2) in enumerate((("#6a1020", "#d6aa58"), ("#1c2e5a", "#c8ccd8"), ("#1e4a2a", "#d6aa58"), ("#3a1a4a", "#c8ccd8"))):
        cx = 180 + i * 180
        L.path(f"M {cx - 40} 470 L {cx + 40} 470 L {cx + 40} 520 Q {cx + 40} 560 {cx} 580 Q {cx - 40} 560 {cx - 40} 520 Z", c1, c2, 5)
        if i % 2:
            M.star(L, cx, 518, 20, c2)
        else:
            M.moon(L, cx, 518, 20, c2)


@label("Curry_Card", 400, 260)
def curry_card(L):
    L.rect(0, 0, L.W, L.H, CREAM)
    M.frame(L, 10, 10, L.W - 20, L.H - 20, CRIMSON, sw=3, inset=8)
    L.text("Katsu Curry", 200, 92, maxw=310, maxh=58, f="black", fill=INK, stroke=INK, sw=1.4)
    L.text("MONDAY", 200, 152, maxw=200, maxh=30, f="bank", fill=CRIMSON, ls=6)
    L.text("mild - medium - dragon", 200, 204, maxw=280, maxh=24, f="serifi", fill=INK)


@label("Lunch_Ticket", 360, 200)
def lunch_ticket(L):
    L.rect(0, 0, L.W, L.H, "#f2d68a")
    L.rect(0, 0, 90, L.H, "#e8c460")
    for k in range(10):
        L.circle(90, 10 + k * 20, 4, "#c8a040")
    L.text("No.", 45, 50, maxw=60, maxh=24, f="serifi", fill=INK)
    L.text("0413", 45, 120, maxw=110, maxh=30, f="bank", fill=CRIMSON, rot=-90)
    L.text("LUNCH", 225, 58, maxw=220, maxh=50, f="dutch", fill=INK, ls=3)
    L.text("ONE TRAY - ONE STUDENT", 225, 106, maxw=240, maxh=20, f="bank", fill=CRIMSON, ls=1)
    M.okada_stamp(L, 305, 158, 30, CRIMSON)
    L.text("valid today", 185, 158, maxw=120, maxh=22, f="hand", fill="#1c2a6a")


# ================================================================== swatches and the atlas

SWATCHES = (("paper", (236, 232, 222), 4, 0), ("kraft", (168, 128, 86), 9, 0), ("cream", (234, 224, 198), 3, 0), ("crimson", (96, 14, 26), 3, 0),
            ("ink", (24, 22, 34), 3, 0), ("gilt", (206, 164, 86), 3, 235), ("alu", (198, 200, 206), 3, 235), ("foil", (176, 180, 190), 6, 245),
            ("ramune", (34, 72, 150), 2, 0), ("barley", (178, 112, 50), 2, 0), ("coffee", (20, 16, 14), 2, 0),
            ("redlantern", (150, 22, 32), 2, 0), ("cola", (18, 12, 14), 2, 0), ("greentea", (46, 90, 42), 2, 0),
            ("lemon", (238, 220, 120), 2, 0), ("pink", (240, 180, 196), 3, 0), ("crisps", (20, 18, 24), 2, 0),
            ("gummies", (70, 30, 120), 2, 0), ("mints", (30, 74, 86), 2, 0), ("choc", (18, 26, 74), 2, 0),
            ("ecto", (18, 58, 44), 2, 0), ("ramenred", (150, 22, 32), 2, 0), ("mustard", (232, 184, 42), 2, 0),
            ("cardboard", (176, 140, 96), 9, 0), ("film", (236, 232, 226), 2, 0), ("holo", (214, 200, 236), 3, 245),
            ("silver", (210, 214, 222), 3, 240), ("tray", (102, 10, 18), 3, 0), ("lacquer", (14, 12, 16), 2, 0),
            ("chocomilk", (200, 154, 114), 3, 0), ("miso", (226, 200, 154), 3, 0))


def swatch(colour, grain, seed, metal):
    g = np.random.default_rng(seed)
    a = np.empty((48, 48, 3), np.float32)
    a[:] = colour
    a += g.normal(0, grain * 0.6, (48, 48))[..., None]
    return (Image.fromarray(np.uint8(np.clip(a, 0, 255))), Image.new("L", (48, 48), metal), Image.new("L", (48, 48), 128))


def pack(sizes, scale):
    """Shelf-pack, tallest first, every label at one scale (swatches stay 48); {key: (x, y, w, h)}, or None if it overflows."""
    x = y = row = 0
    pad = 8
    out = {}
    for key, (w, h) in sorted(sizes.items(), key=lambda kv: -kv[1][1] * (1 if kv[0].startswith("Swatch_") else scale)):
        if not key.startswith("Swatch_"):
            w, h = int(round(w * scale)), int(round(h * scale))
        if x + w + pad > A:
            x, y, row = 0, y + row + pad, 0
        if y + h + pad > A:
            return None
        out[key] = (x + pad // 2, y + pad // 2, w, h)
        x += w + pad
        row = max(row, h)
    return out


def build(keys=None):
    labels = []
    for key, (W, H, fn) in LABELS.items():
        if keys and key not in keys:
            continue
        L = Label(key, W, H)
        fn(L)
        labels.append(L)
    print(f"[atlas] rendering {len(labels)} labels", flush=True)
    return S.render_all(labels)


def main():
    only = [a for a in sys.argv[1:] if not a.startswith("-")]
    layers = build(only or None)
    if only:
        os.makedirs("E:/NH-Work/props54/atlas2", exist_ok=True)
        for k, (c, m, h) in layers.items():
            c.save(f"E:/NH-Work/props54/atlas2/{k}.png")
        return
    sw = {f"Swatch_{n}": swatch(c, g, i * 7 + 3, m) for i, (n, c, g, m) in enumerate(SWATCHES)}
    sizes = {k: (W, H) for k, (W, H, _) in LABELS.items()}
    sizes.update({k: (48, 48) for k in sw})
    lay = None
    for scale in (1.0, 0.96, 0.92, 0.88, 0.84, 0.8, 0.76, 0.72):
        lay = pack(sizes, scale)
        if lay:
            break
    print(f"[atlas] packed at scale {scale}")
    col = Image.new("RGB", (A, A), (40, 34, 30))
    met = Image.new("L", (A, A), 0)
    hgt = Image.new("L", (A, A), 128)
    reg = {}
    for key, (x, y, w, h) in lay.items():
        c, m, hh = layers[key] if key in layers else sw[key]
        if c.size != (w, h):
            c, m, hh = (im.resize((w, h), Image.LANCZOS) for im in (c, m, hh))
        col.paste(c, (x, y))
        met.paste(m, (x, y))
        hgt.paste(hh, (x, y))
        reg[key] = [x / A, 1 - (y + h) / A, (x + w) / A, 1 - y / A]
    col.save(os.path.join(OUT, "ConcessionPrint_color.png"))
    met.save(os.path.join(OUT, "ConcessionPrint_gilt.png"))
    hgt.save(os.path.join(OUT, "ConcessionPrint_height.png"))
    json.dump({"regions": {"ConcessionPrint": reg}}, open(os.path.join(HERE, "concession_atlas.json"), "w"), indent=0)
    print(f"[atlas] ConcessionPrint: {len(reg)} regions")


if __name__ == "__main__":
    main()
