"""The Ashby House canvases (PBR via posters_hq.save).

  WF_PortraitAshby       old Mrs Ashby in oils, 1890s: a dark varnished ground, a high-collared black dress with a cameo,
                         grey hair in a bun, a long pale face, thin pressed lips, crackle in the varnish. The eye whites are
                         painted; the irises are separate rigged pieces on the prop (they follow you)
  WF_PortraitAshbySmile  the same, smiling: a thin, far-too-wide smile (the game swaps the canvas when you look back)
  WF_Condemned           the council's notice nailed to the door: CONDEMNED, UNSAFE STRUCTURE, KEEP OUT, by order of the
                         Wickfield Building Inspector, 1987, faded and rain-streaked
  WF_Timetable           the bus stop timetable, Route 4, last bus 10:40 PM, and a marker warning underneath
  WF_BusBlind            the black bus's destination blind: route 13, NIGHTMARE HIGH in amber

  python art/hometown/ashby_canvases.py [portrait|condemned|timetable|blind|side|plate|sign|band]
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import posters_hq as Q  # noqa: E402
H = Q.H
Q.PBR["WF_PortraitAshby"] = dict(rough=0.3, ink_rough=0.35, ink_lift=0.25, strength=3.0)
Q.PBR["WF_PortraitAshbySmile"] = Q.PBR["WF_PortraitAshby"]
Q.PBR["WF_Condemned"] = dict(rough=0.85, ink_rough=0.7, ink_lift=0.15, strength=2.5)

EYES = ((-62, 395), (62, 395))      # eye centres on the 768 x 1024 canvas, relative to x = 384


def portrait(smile=False):
    L = H.Logo("WF_PortraitAshbySmile" if smile else "WF_PortraitAshby", 768, 1024)
    W, Hh, cx = 768, 1024, 384
    pg = L.rrect(0, 0, W, Hh, 0)
    L.paint(pg, L.rgrad("#4a3a28", "#120c08", cx - 60, 380, 620))       # a warm dark ground, lighter behind the head
    def brush(mask, a, b, seed, scale=6):
        """painterly fill: two tones mixed by directional brush noise"""
        n = Q.noise(L, scale, seed) * 0.5 + 0.5
        st = Q.noise(L, 1.2, seed + 1)
        col = H.rgb(a) * (1 - n[..., None]) + H.rgb(b) * n[..., None]
        col *= (1 + 0.06 * st[..., None])
        L.col = L.col * (1 - mask[..., None]) + col * mask[..., None]
        L.a = np.maximum(L.a, mask)
    # the dress: shoulders and a high collar, a cameo at the throat
    dress = L.poly([(40, 1024), (60, 800), (170, 700), (300, 655), (468, 655), (598, 700), (708, 800), (728, 1024)])
    brush(dress, "#0c0a0c", "#2a2228", 300, 10)
    collar = L.poly([(318, 660), (450, 660), (440, 560), (328, 560)])
    brush(collar, "#141014", "#2e2830", 301, 4)
    for k in range(6):
        L.paint(L.rrect(322, 568 + k * 16, 446, 571 + k * 16, 1), "#3a3238", alpha=0.6)
    cam = L.ellipse(cx, 690, 38, 48)
    L.paint(L.grow(cam, 5), "#b8893a")
    brush(cam, "#e8d8c8", "#c8a890", 302, 3)
    L.paint(L.ellipse(cx + 4, 680, 14, 22), "#d8c0a8")
    # the neck and the face: a long pale oval, painterly shadow down the right side
    neck = L.rrect(cx - 48, 470, cx + 48, 600, 30)
    brush(neck, "#c8a88c", "#8a6a54", 303, 5)
    face = L.ellipse(cx, 390, 125, 160)
    brush(face, "#e2c4a6", "#b08868", 304, 7)
    shadow = np.clip((L.xx / H.SS - (cx + 20)) / 110, 0, 1) * face
    L.col = L.col * (1 - 0.35 * shadow[..., None])
    # the hair: grey, swept up into a bun on top
    hair = np.clip(L.ellipse(cx, 300, 140, 110) - L.ellipse(cx, 360, 118, 120), 0, 1) + L.ellipse(cx, 205, 70, 52)
    brush(np.clip(hair, 0, 1), "#8a8680", "#c8c4bc", 305, 3)
    for k in range(8):                                          # strands
        a_ = math.pi * (0.15 + 0.7 * k / 7)
        L.paint(L.stroke_round([(cx + 125 * math.cos(a_ + math.pi), 330 - 60 * math.sin(a_)), (cx, 250)], 2), "#6a6660", alpha=0.6)
    # the features: hollow eyes (whites painted, the irises are on the prop), a long nose, thin lips
    for dx, ey in EYES:
        sock = L.ellipse(cx + dx, ey, 44, 26)
        L.paint(L.grow(sock, 6), "#8a6450", alpha=0.6)
        L.paint(sock, "#e8e0d0")
        L.paint(np.clip(L.ellipse(cx + dx, ey - 6, 46, 26) - L.ellipse(cx + dx, ey + 8, 46, 28), 0, 1), "#6a4434", alpha=0.85)   # heavy lids
        L.paint(L.stroke_round([(cx + dx - 46, ey - 44), (cx + dx + 40, ey - 52)], 7), "#6a6460")                                # brows
    L.paint(L.stroke_round([(cx + 4, 410), (cx + 10, 470), (cx - 8, 482)], 6), "#9a7058", alpha=0.8)
    if smile:
        mouth = L.m(lambda d, s: d.chord(((cx - 92) * s, 448 * s, (cx + 92) * s, 522 * s), 0, 180, fill=255))
        L.paint(mouth, "#3a1410")
        for k in range(9):                                      # small, even teeth
            L.paint(L.rrect(cx - 72 + k * 16, 486, cx - 60 + k * 16, 499, 3), "#e8dcc4")
        L.paint(L.stroke_round([(cx - 96, 484), (cx - 50, 486), (cx, 487), (cx + 50, 486), (cx + 96, 484)], 4), "#7a3a30")
    else:
        L.paint(L.stroke_round([(cx - 45, 520), (cx, 516), (cx + 45, 520)], 6), "#7a3a30")
    # varnish: yellowed, a crackle network, darker toward the edges
    L.col = L.col * np.array([1.0, 0.94, 0.78], np.float32)
    cr = np.abs(Q.noise(L, 5, 310)) < 0.006
    L.col = np.where(cr[..., None], L.col * 0.86, L.col)
    x, y = L.xx / H.SS / W - 0.5, L.yy / H.SS / Hh - 0.5
    L.col *= (1 - 0.6 * np.clip(np.hypot(x, y) - 0.25, 0, 1))[..., None]
    L.crease_h = cr.astype(np.float32) * 0.8
    Q.save(L, L.name)


def condemned():
    L = H.Logo("WF_Condemned", 768, 1024)
    W, Hh = 768, 1024
    pg = L.rrect(0, 0, W, Hh, 0)
    L.paint(pg, "#f0ead2")
    Q.fibres(L, 320, 0.05)
    L.paint(L.rrect(30, 30, W - 30, 200, 0), "#b8201a")
    L.paint(L.text("CONDEMNED", "georgiab", 82, W / 2, 118, spacing=4), "#f6efe0")
    for t, f, px, y in (("UNSAFE STRUCTURE", "georgiab", 54, 290), ("KEEP OUT", "georgiab", 80, 400), ("This building has been found unfit", "georgia", 30, 520),
                        ("for human occupancy. Entry is", "georgia", 30, 560), ("prohibited by order of the", "georgia", 30, 600),
                        ("Wickfield Building Inspector.", "georgia", 30, 640), ("No. 1987-0413", "georgiab", 30, 760),
                        ("ALSO: PLEASE STOP KNOCKING", "georgiai", 26, 900)):
        L.paint(L.text(t, f, px, W / 2, y, spacing=2), "#1a1612")
    L.paint(L.stroke_round([(200, 830), (260, 800), (330, 840), (420, 800), (520, 830)], 4), "#1a2a6a")   # a signature
    # rain streaks, rust from the nails, fading
    for k in range(18):
        x = 40 + k * 40 + (k * 37) % 23
        L.paint(L.rrect(x, 0, x + 6, Hh, 3), "#9a8a6a", alpha=0.12)
    for x, y in ((50, 50), (W - 50, 50), (50, Hh - 50), (W - 50, Hh - 50)):
        L.paint(L.ellipse(x, y + 30, 14, 60), "#8a4a1a", alpha=0.5)
        L.paint(L.ellipse(x, y, 10), "#3a2a20")
    L.col = L.col * 0.92 + 18
    Q.age_paper(L, 321, folds=(), tape=False)
    Q.save(L, "WF_Condemned")


Q.PBR["WF_Timetable"] = dict(rough=0.2, ink_rough=0.25, ink_lift=0.1, strength=1.5)


def timetable():
    """the bus stop's timetable behind its scratched perspex: Wickfield Transit, Route 4, the last bus 10:40 PM; someone has
    written underneath in marker 'there's another one. don't get on it.'"""
    L = H.Logo("WF_Timetable", 768, 1024)
    W, Hh = 768, 1024
    L.paint(L.rrect(0, 0, W, Hh, 0), "#f4f2ea")
    L.paint(L.rrect(0, 0, W, 150, 0), "#1f4a32")
    L.paint(L.text("WICKFIELD TRANSIT", "georgiab", 48, W / 2, 60, spacing=4), "#f4ead2")
    L.paint(L.text("ROUTE 4  ·  ALDER LANE – TOWN SQUARE – PEMBROOK", "georgia", 22, W / 2, 115, spacing=2), "#e3b23c")
    times = ["6:10 AM", "7:05 AM", "8:00 AM", "9:15 AM", "11:30 AM", "1:45 PM", "3:20 PM", "4:40 PM", "6:05 PM", "8:30 PM", "10:40 PM"]
    for i, t in enumerate(times):
        y = 200 + i * 52
        L.paint(L.rrect(60, y - 22, W - 60, y + 22, 4), "#e8e4d8" if i % 2 else "#f4f2ea")
        L.paint(L.text(t, "georgiab", 30, 200, y), "#1a1612")
        L.paint(L.text("Mon – Sat" if i < 10 else "LAST BUS", "georgia", 24, 540, y), "#1a1612" if i < 10 else "#b8201a")
    L.paint(L.text("No service after 10:40 PM.", "georgiai", 28, W / 2, 810), "#3a3230")
    INK = "#1a1a2a"
    m = L.text("there's another one.", "chela", 40, W / 2, 890)
    L.paint(m * (Q.noise(L, 0.5, 600) > -0.5), INK)
    m = L.text("don't get on it.", "chela", 40, W / 2, 945)
    L.paint(m * (Q.noise(L, 0.5, 601) > -0.5), "#b8201a")
    # scratches on the perspex
    rng = np.random.default_rng(602)
    for _ in range(40):
        x0, y0 = rng.uniform(0, W), rng.uniform(0, Hh)
        a = rng.uniform(0, math.pi)
        ln = rng.uniform(20, 160)
        L.paint(L.line([(x0, y0), (x0 + ln * math.cos(a), y0 + ln * math.sin(a))], 1), "#ffffff", alpha=0.35)
    Q.save(L, "WF_Timetable")


Q.PBR["WF_BusBlind"] = dict(rough=0.35, ink_rough=0.3, ink_lift=0.05, strength=1.0)


def bus_blind():
    """the black bus's destination blind: a worn roller of black linen, amber letters lit from behind, route 13 in a box,
    NIGHTMARE HIGH; the roll's creases and a faint second destination (WICKFIELD) bleeding through from the last turn"""
    L = H.Logo("WF_BusBlind", 1792, 256)
    W, Hh = 1792, 256
    L.paint(L.rrect(0, 0, W, Hh, 0), "#0b0a0c")
    Q.fibres(L, 700, 0.04)
    L.paint(L.text("WICKFIELD", "georgiab", 120, W / 2 + 120, 128 - 210, spacing=10), "#e3a040", alpha=0.08)
    L.paint(L.rrect(40, 40, 240, 216, 10), "#e8a43a")
    L.paint(L.rrect(52, 52, 228, 204, 6), "#0b0a0c")
    L.paint(L.text("13", "georgiab", 120, 140, 132), "#f2b552")
    glow = L.text("NIGHTMARE HIGH", "georgiab", 128, W / 2 + 110, 132, spacing=12)
    L.paint(glow, "#f2b552")
    L.paint(L.text("NIGHTMARE HIGH", "georgiab", 128, W / 2 + 110, 132, spacing=12) * (Q.noise(L, 0.6, 700) > 0.55), "#6a3a10", alpha=0.6)
    for x in (430, 980, 1500):     # roller creases
        L.paint(L.rrect(x, 0, x + 3, Hh, 1), "#000000", alpha=0.6)
        L.paint(L.rrect(x + 3, 0, x + 5, Hh, 1), "#3a3436", alpha=0.4)
    Q.save(L, "WF_BusBlind")


Q.PBR["WF_BusSide"] = dict(rough=0.3, ink_rough=0.18, ink_lift=0.2, strength=2.0)
Q.PBR["WF_BusPlate"] = dict(rough=0.4, ink_rough=0.25, ink_lift=0.5, strength=4.0)
Q.PBR["WF_BusSign"] = dict(rough=0.35, ink_rough=0.3, ink_lift=0.08, strength=1.5)
Q.PBR["WF_ShelterBand"] = dict(rough=0.4, ink_rough=0.35, ink_lift=0.05, strength=1.2)


def _gold(L, txt, font, px, x, y, spacing=0):
    """gold leaf lettering: a dark drop shadow, a deep gold body, a pale highlight along the top edge"""
    L.paint(L.text(txt, font, px, x + px * 0.04, y + px * 0.05, spacing=spacing), "#000000", alpha=0.85)
    m = L.text(txt, font, px, x, y, spacing=spacing)
    L.paint(m, "#a8782a")
    L.paint(m * (L.text(txt, font, px, x, y - px * 0.035, spacing=spacing) < 0.5), "#f6dc8a")
    L.paint(m * (Q.noise(L, 0.4, 801) > 0.6), "#6a4a1a", alpha=0.5)


def bus_side():
    """the letterboard over the black bus's windows: NIGHTMARE HIGHSCHOOL in gold leaf, a crimson pin line above and
    below with curled ends, the fleet number 13 at each end"""
    L = H.Logo("WF_BusSide", 2560, 256)
    W, Hh = 2560, 256
    L.paint(L.rrect(0, 0, W, Hh, 0), "#09080a")
    Q.fibres(L, 802, 0.03)
    for y in (34, 222):
        L.paint(L.rrect(150, y - 3, W - 150, y + 3, 3), "#8a0f18")
        for x in (150, W - 150):
            L.paint(L.ellipse(x, y, 14), "#8a0f18")
            L.paint(L.ellipse(x, y, 8), "#09080a")
    _gold(L, "NIGHTMARE HIGHSCHOOL", "georgiab", 118, W / 2, 132, spacing=14)
    for x in (78, W - 78):
        _gold(L, "13", "georgiab", 64, x, 132)
    Q.save(L, "WF_BusSide")


def bus_plate():
    """the bus's plate: black enamel, a crimson rim, raised silver NH 1313 and a line of small text that should not exist"""
    L = H.Logo("WF_BusPlate", 1024, 512)
    W, Hh = 1024, 512
    L.paint(L.rrect(0, 0, W, Hh, 40), "#b8b4ac")
    L.paint(L.rrect(14, 14, W - 14, Hh - 14, 32), "#7a0c14")
    L.paint(L.rrect(30, 30, W - 30, Hh - 30, 24), "#0c0b0d")
    L.paint(L.text("NIGHT TRANSPORT", "georgiab", 44, W / 2, 86, spacing=10), "#c9c3b6")
    L.paint(L.text("NH 1313", "georgiab", 168, W / 2 + 6, 284, spacing=10), "#000000", alpha=0.8)
    L.paint(L.text("NH 1313", "georgiab", 168, W / 2, 276, spacing=10), "#d8d4cc")
    L.paint(L.text("NO RETURN SERVICE", "georgia", 36, W / 2, 440, spacing=8), "#9a948a")
    for x, y in ((80, 80), (W - 80, 80), (80, Hh - 80), (W - 80, Hh - 80)):
        L.paint(L.ellipse(x, y, 18), "#8a867e")
        L.paint(L.ellipse(x, y, 6), "#3a3836")
    Q.age_paper(L, 803, folds=(), tape=False)
    Q.save(L, "WF_BusPlate")


def bus_sign():
    """the stop's flag: enamelled steel, a white top band (BUS STOP), the route 4 roundel, WICKFIELD TRANSIT and the
    oak leaf; chipped at the corners and a sticker someone has half peeled off"""
    L = H.Logo("WF_BusSign", 768, 1024)
    W, Hh = 768, 1024
    L.paint(L.rrect(0, 0, W, Hh, 60), "#1f4a32")
    L.paint(L.rrect(16, 16, W - 16, Hh - 16, 48), "#f2eee2", alpha=1.0)
    L.paint(L.rrect(30, 30, W - 30, Hh - 30, 40), "#1f4a32")
    L.paint(L.rrect(30, 30, W - 30, 250, 40), "#f2eee2")
    L.paint(L.text("BUS", "georgiab", 96, W / 2, 95, spacing=16), "#1f4a32")
    L.paint(L.text("STOP", "georgiab", 96, W / 2, 195, spacing=16), "#1f4a32")
    L.paint(L.ellipse(W / 2, 500, 175), "#f2eee2")
    L.paint(L.ellipse(W / 2, 500, 150), "#e3b23c")
    L.paint(L.text("4", "georgiab", 230, W / 2, 512), "#1a1612")
    L.paint(L.text("WICKFIELD", "georgiab", 70, W / 2, 770, spacing=6), "#f2eee2")
    L.paint(L.text("TRANSIT", "georgiab", 70, W / 2, 850, spacing=18), "#f2eee2")
    L.paint(L.text("Alder Lane", "georgiai", 40, W / 2, 930), "#e3b23c")
    rng = np.random.default_rng(804)
    for x, y in ((40, 40), (W - 40, 40), (40, Hh - 40), (W - 40, Hh - 40), (W - 40, 520), (60, 700)):
        for _ in range(4):
            L.paint(L.ellipse(x + rng.uniform(-14, 14), y + rng.uniform(-14, 14), rng.uniform(3, 8)), "#5a3a26", alpha=0.85)
    L.paint(L.rrect(520, 640, 690, 720, 8), "#c8c2b0")                   # the peeled sticker
    L.paint(L.text("GO PUMAS", "georgiab", 26, 600, 680), "#7a1a12", alpha=0.6)
    Q.save(L, "WF_BusSign")


def shelter_band():
    """the shelter's fascia: WICKFIELD TRANSIT, the stop's name, the route roundel"""
    L = H.Logo("WF_ShelterBand", 2560, 256)
    W, Hh = 2560, 256
    L.paint(L.rrect(0, 0, W, Hh, 0), "#1f4a32")
    L.paint(L.rrect(0, 18, W, 24, 0), "#e3b23c")
    L.paint(L.rrect(0, Hh - 24, W, Hh - 18, 0), "#e3b23c")
    L.paint(L.text("WICKFIELD TRANSIT", "georgiab", 84, 860, 132, spacing=8), "#f2eee2")
    L.paint(L.text("ALDER LANE STOP", "georgia", 60, 1820, 132, spacing=6), "#e3b23c")
    L.paint(L.ellipse(W - 140, 128, 84), "#f2eee2")
    L.paint(L.ellipse(W - 140, 128, 70), "#e3b23c")
    L.paint(L.text("4", "georgiab", 100, W - 140, 134), "#1a1612")
    L.paint(L.ellipse(140, 128, 84), "#f2eee2")
    L.paint(L.ellipse(140, 128, 70), "#e3b23c")
    L.paint(L.text("4", "georgiab", 100, 140, 134), "#1a1612")
    for k in range(30):
        x = 40 + k * 86
        L.paint(L.rrect(x, 30, x + 4, Hh - 30, 2), "#0a1a10", alpha=0.18)  # rain streaks
    Q.save(L, "WF_ShelterBand")


if __name__ == "__main__":
    want = sys.argv[1:]
    jobs = {"portrait": lambda: (portrait(False), portrait(True)), "condemned": condemned, "timetable": timetable, "blind": bus_blind, "side": bus_side, "plate": bus_plate, "sign": bus_sign, "band": shelter_band}
    for k, fn in jobs.items():
        if not want or k in want:
            fn()
