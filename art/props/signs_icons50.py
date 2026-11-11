"""Batch 50 (signs): the sign icon set (art/props/signs_icons50.py; a copy of E:/NH-Work/props50/icons50.py).

Each icon is drawn as vector layers in a 256 x 256 box. A layer is (fill, cut): `fill` is white SVG, `cut` is SVG drawn
black into that layer's mask (engraved lines and holes). Every layer is also knocked out by the layers above it, with a
gap of GAP units, so overlapping parts read as separate pieces without any dark outline.

  python icons50.py [names...]     writes svg/<Name>.svg and renders out/<Name>.png (1024, white + emboss, alpha)
  python icons50.py --sheet        also writes the icon sheet

The PNG is white with a soft emboss (light from the top left) in its RGB and the shape in its alpha, so a Decal or
ImageLabel tints it to gilt, ink or bone with Color3. The RGB of transparent pixels is bled from the shape, so there
are no dark fringes when Roblox filters it.
"""
import math
import re
import os
import subprocess
import sys

HERE = "E:/NH-Work/props50"            # the working folder (svg/, out/ and the sheets); the PNGs ship in art/group-upload/signs-icons-batch50
SVG = os.path.join(HERE, "icons", "svg")
OUT = os.path.join(HERE, "icons", "out")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
GAP = 9


def P(d, extra=""):
    return f'<path d="{d}" {extra}/>'


def S(d, w, cap="round"):          # a white (or, in a cut, black) stroke
    return f'<path d="{d}" fill="none" stroke-width="{w}" stroke-linecap="{cap}" stroke-linejoin="round"/>'


def C(cx, cy, r):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}"/>'


def R(x, y, w, h, rx=0, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" {extra}/>'


def E(cx, cy, rx, ry, rot=0):
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" transform="rotate({rot} {cx} {cy})"/>'


def G(t, *body):
    return f'<g transform="{t}">' + "".join(body) + "</g>"


def RING(cx, cy, r, w):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke-width="{w}"/>'


def star4(cx, cy, r, k=0.28):
    pts = []
    for i in range(8):
        a = i * math.pi / 4 - math.pi / 2
        rr = r if i % 2 == 0 else r * k
        pts.append(f"{cx + rr * math.cos(a):.1f} {cy + rr * math.sin(a):.1f}")
    return P("M" + " L".join(pts) + " Z")


def star5(cx, cy, r, k=0.42, rot=0):
    pts = []
    for i in range(10):
        a = i * math.pi / 5 - math.pi / 2 + math.radians(rot)
        rr = r if i % 2 == 0 else r * k
        pts.append(f"{cx + rr * math.cos(a):.1f} {cy + rr * math.sin(a):.1f}")
    return P("M" + " L".join(pts) + " Z")


def poly(pts):
    return P("M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + " Z")


def crescent(cx, cy, r, dx, dy, r2=None):
    """A crescent as one layer: the disc, with an offset disc cut away (returns fill, cut)."""
    return C(cx, cy, r), C(cx + dx, cy + dy, r2 or r * 0.86)


# ------------------------------------------------------------------ figures for the restroom signs

def boy(t=""):
    body = P("M96 92 L160 92 C174 92 182 102 182 116 L182 168 C182 176 168 176 168 168 L168 124 L164 124 "
             "L164 232 C164 242 140 242 140 232 L140 172 L116 172 L116 232 C116 242 92 242 92 232 L92 124 L88 124 "
             "L88 168 C88 176 74 176 74 168 L74 116 C74 102 82 92 96 92 Z")
    head = C(128, 56, 26)
    hair = P("M101 52 C100 30 116 22 132 24 C150 25 160 36 156 52 C146 40 128 36 112 44 C108 46 104 50 101 52 Z")
    cut = P("M120 96 L136 96 L131 104 L134 136 L128 144 L122 136 L125 104 Z")
    return [(G(t, head, body), G(t, cut))]


def girl(t=""):
    dress = P("M104 92 L152 92 C164 92 172 100 176 110 L196 162 C199 170 187 175 183 168 L166 128 L190 196 "
              "L156 196 L156 234 C156 243 136 243 136 234 L136 196 L120 196 L120 234 C120 243 100 243 100 234 "
              "L100 196 L66 196 L90 128 L73 168 C69 175 57 170 60 162 L80 110 C84 100 92 92 104 92 Z")
    head = C(128, 58, 25)
    bow = P("M128 28 L104 14 C96 12 94 40 104 38 Z") + P("M128 28 L152 14 C160 12 162 40 152 38 Z") + C(128, 28, 8)
    hair = P("M103 60 C96 74 96 92 90 100 C102 98 108 86 110 74 Z") + P("M153 60 C160 74 160 92 166 100 "
                                                                       "C154 98 148 86 146 74 Z")
    cut = (S("M112 150 L104 194", 5) + S("M128 150 L128 194", 5) + S("M144 150 L152 194", 5)
           + S("M92 138 Q128 148 164 138", 6) + S("M128 28 L128 28", 1))
    return [(G(t, head, dress), G(t, cut)), (G(t, bow), "")]


# ------------------------------------------------------------------ the icons

def icons():
    I = {}

    # --- classes (Config.Classes: Homeroom R101 ... Detention R106)
    I["Homeroom"] = [  # the roll-call register on a clipboard, three names ticked
        (R(52, 40, 152, 196, 14), S("M76 96 L94 112 L118 82", 10) + S("M132 100 L184 100", 9)
         + S("M76 146 L94 162 L118 132", 10) + S("M132 150 L184 150", 9)
         + S("M80 196 L112 196", 9) + S("M132 198 L184 198", 9)),
        (R(92, 24, 72, 34, 10), C(128, 38, 7)),
    ]
    I["Mathematics"] = [  # a drafting compass over a divided rule
        (R(28, 214, 200, 26, 5), "".join(S(f"M{x} 214 L{x} {226 if i % 2 else 232}", 5) for i, x in
                                         enumerate(range(44, 220, 18)))),
        (C(128, 40, 16) + R(122, 14, 12, 18, 3) + S("M128 50 L76 196", 18) + S("M128 50 L180 196", 18)
         + P("M70 190 L82 194 L70 214 Z") + P("M186 190 L174 194 L186 214 Z") + S("M98 138 Q128 152 158 138", 9),
         C(128, 40, 6)),
    ]
    I["Chemistry"] = [  # a round flask, its liquid line and bubbles
        (R(104, 50, 48, 14, 5) + R(112, 58, 32, 66) + C(128, 174, 60) + C(142, 34, 9) + C(120, 20, 6) + C(156, 14, 5),
         S("M76 168 Q102 182 128 170 T180 168", 7) + C(108, 198, 7) + C(146, 206, 9) + C(132, 186, 4)
         + S("M100 140 C92 150 88 160 88 172", 6)),
    ]
    I["English"] = [  # a quill and its flourish
        (S("M36 222 C72 204 104 236 144 216 S206 204 224 220", 8), ""),
        (P("M214 22 C152 30 98 86 76 166 L72 184 L86 176 C102 148 122 126 146 110 C184 92 208 64 214 22 Z")
         + P("M68 176 L52 216 L82 190 Z"),
         S("M204 36 C158 74 116 118 84 172", 5) + S("M182 54 L206 50", 4) + S("M164 72 L194 70", 4)
         + S("M146 92 L178 92", 4) + S("M128 112 L160 116", 4) + S("M162 64 L150 42", 4) + S("M142 86 L124 66", 4)
         + S("M122 110 L106 92", 4)),
    ]
    I["History"] = [  # an hourglass, half run
        (R(56, 26, 144, 20, 6) + R(56, 210, 144, 20, 6) + S("M70 46 L70 210", 10) + S("M186 46 L186 210", 10)
         + S("M96 46 C96 98 124 112 124 128 C124 144 96 158 96 210", 7) + S("M160 46 C160 98 132 112 132 128 "
                                                                              "C132 144 160 158 160 210", 7)
         + P("M106 206 C114 178 142 178 150 206 Z") + P("M108 84 L148 84 C142 104 134 112 128 122 C122 112 114 104 "
                                                                        "108 84 Z") + S("M128 124 L128 188", 4),
         ""),
    ]
    I["Detention"] = [  # a slate of tally marks (writing lines, counting days)
        (R(30, 50, 196, 150, 12), R(46, 66, 164, 118, 6, 'fill="none" stroke-width="7"')
         + "".join(S(f"M{x} 92 L{x} 160", 9) for x in (76, 100, 124, 148)) + S("M64 150 L162 100", 9)
         + S("M184 96 L184 160", 9)),
        (R(150, 204, 64, 16, 5, 'transform="rotate(-12 182 212)"'), ""),
    ]

    # --- electives (batch 38) and the arts
    I["Herbology"] = [  # a sprouting pot
        (R(74, 156, 108, 20, 6) + P("M84 170 L172 170 L160 230 L96 230 Z"), S("M88 196 Q128 206 168 196", 6)),
        (P("M128 154 C100 140 80 108 88 76 C114 88 130 120 128 154 Z")
         + P("M128 154 C156 140 176 108 168 76 C142 88 126 120 128 154 Z")
         + P("M128 146 C110 108 114 66 128 30 C142 66 146 108 128 146 Z"),
         S("M126 148 C114 128 104 108 96 88", 5) + S("M130 148 C142 128 152 108 160 88", 5) + S("M128 140 L128 52", 5)),
    ]
    I["HomeEconomics"] = [  # a teapot
        (E(122, 158, 68, 54) + P("M188 150 C206 140 214 116 230 102 L238 110 C226 132 216 162 190 180 Z")
         + R(86, 206, 72, 14, 5),
         S("M60 150 Q122 168 184 150", 6) + S("M86 186 Q122 198 158 186", 5)),
        (S("M60 126 C26 126 28 186 66 180", 14), ""),
        (P("M90 108 Q122 82 154 108 Z") + C(122, 82, 11), ""),
        (S("M206 70 C194 56 214 46 202 28", 7) + S("M182 62 C172 50 188 42 178 28", 6), ""),
    ]
    I["Sewing"] = [  # a cotton reel and a threaded needle
        (R(52, 46, 104, 24, 8) + R(52, 188, 104, 24, 8) + R(66, 66, 76, 126),
         "".join(S(f"M66 {y} L142 {y - 14}", 5) for y in range(92, 196, 16))),
        (P("M196 30 L210 30 L208 214 L203 240 L198 214 Z") + S("M142 122 C176 110 188 80 203 56", 4),
         E(203, 52, 3, 11)),
    ]
    I["Photography"] = [  # a box camera
        (R(30, 84, 196, 124, 14) + R(56, 62, 52, 28, 6) + R(166, 70, 34, 18, 4),
         RING(128, 146, 44, 9) + C(128, 146, 18) + R(44, 102, 30, 16, 4) + S("M30 120 L84 120", 0)),
    ]
    I["Woodshop"] = [  # a saw crossed by a hammer
        (G("rotate(36 128 128)", P("M110 22 L150 22 L146 168 L114 168 Z") + R(102, 164, 56, 58, 16)),
         G("rotate(36 128 128)", R(116, 178, 28, 28, 9) + "".join(P(f"M110 {y} L118 {y + 6} L110 {y + 12} Z")
                                                               for y in range(30, 160, 14)))),
        (G("rotate(-38 128 128)", R(118, 74, 20, 156, 8) + P("M78 40 L170 40 C180 40 182 50 182 58 L182 74 L88 74 "
                                                               "C74 74 66 62 66 54 C66 46 70 40 78 40 Z")),
         G("rotate(-38 128 128)", S("M126 96 L126 210", 4))),
    ]
    I["Ceramics"] = [  # an amphora on the wheel
        (E(128, 238, 84, 10), ""),
        (P("M106 34 L150 34 L150 44 C142 50 140 62 142 74 C178 90 194 128 186 166 C180 198 162 216 142 222 L114 222 "
           "C94 216 76 198 70 166 C62 128 78 90 114 74 C116 62 114 50 106 44 Z")
         + S("M114 80 C82 74 74 104 90 120", 10) + S("M142 80 C174 74 182 104 166 120", 10),
         S("M78 132 Q128 148 178 132", 6) + S("M74 170 Q128 186 182 170", 6) + S("M96 150 L112 150", 5)
         + S("M144 150 L160 150", 5)),
    ]
    mask = ("M-46 -52 C-20 -64 20 -64 46 -52 C52 -10 40 32 0 58 C-40 32 -52 -10 -46 -52 Z")
    I["Drama"] = [  # tragedy behind comedy
        (G("translate(92 100) rotate(-16)", P(mask)),
         G("translate(92 100) rotate(-16)", P("M-30 -22 Q-18 -14 -8 -24 Q-18 -30 -30 -22 Z")
           + P("M30 -22 Q18 -14 8 -24 Q18 -30 30 -22 Z") + P("M-20 30 Q0 12 20 30 Q0 22 -20 30 Z")
           + S("M-26 -36 Q-18 -42 -8 -38", 4) + S("M26 -36 Q18 -42 8 -38", 4))),
        (G("translate(166 150) rotate(14)", P(mask)),
         G("translate(166 150) rotate(14)", P("M-30 -20 Q-18 -32 -6 -20 Q-18 -24 -30 -20 Z")
           + P("M30 -20 Q18 -32 6 -20 Q18 -24 30 -20 Z") + P("M-24 12 Q0 44 24 12 Q0 24 -24 12 Z"))),
    ]
    I["Art"] = [  # a palette and a brush
        (P("M128 46 C68 46 28 86 32 134 C36 182 84 214 132 208 C162 204 158 182 150 172 C140 160 152 144 168 148 "
           "C200 154 226 136 222 104 C216 68 178 46 128 46 Z"),
         C(80, 100, 13) + C(116, 76, 13) + C(160, 80, 13) + C(190, 108, 11) + C(70, 148, 12) + E(112, 172, 16, 12)),
        (S("M232 26 L172 128", 12) + P("M164 124 L180 134 L170 150 L156 142 Z")
         + P("M156 142 L170 150 C162 176 140 194 124 196 C128 178 140 156 156 142 Z"), ""),
    ]
    I["Music"] = [  # a lyre
        (P("M98 184 L158 184 L150 220 L106 220 Z") + S("M98 186 C54 160 54 96 86 70 C96 62 92 46 80 44", 15)
         + S("M158 186 C202 160 202 96 170 70 C160 62 164 46 176 44", 15) + R(76, 84, 104, 14, 6) + C(78, 42, 11)
         + C(178, 42, 11) + "".join(S(f"M{x} 98 L{x} 186", 4) for x in (106, 120, 136, 150)), ""),
    ]
    I["Choir"] = [  # two beamed notes
        (E(86, 196, 30, 21, -20) + E(178, 176, 30, 21, -20) + R(102, 66, 14, 128) + R(194, 46, 14, 128)
         + P("M102 60 L208 38 L208 74 L102 96 Z"), S("M116 116 L194 100", 7)),
    ]
    I["Gym"] = [  # a pair of globe dumbbells
        (G("rotate(-28 128 128)", C(60, 128, 42) + C(196, 128, 42) + R(92, 114, 72, 28, 8)),
         G("rotate(-28 128 128)", S("M40 108 C46 98 56 92 66 92", 7) + S("M176 108 C182 98 192 92 202 92", 7))),
    ]
    I["Alchemy"] = [  # the squared circle: circle, triangle, square, circle
        (RING(128, 128, 106, 9) + poly([(128, 34), (212, 180), (44, 180)]).replace("/>", ' fill="none" stroke-width="9" stroke-linejoin="round"/>')
         + R(92, 90, 72, 72, 0, 'fill="none" stroke-width="8"') + RING(128, 126, 30, 8) + C(128, 126, 9), ""),
    ]
    I["Astronomy"] = [  # a crescent among stars
        (C(112, 136, 78), C(150, 112, 72)),
        (star4(184, 172, 30) + star4(200, 52, 22) + star4(140, 40, 12) + star4(218, 116, 10), ""),
    ]
    I["Seance"] = [  # a planchette with its seeing glass
        (P("M128 26 C170 60 208 116 206 164 C204 204 170 224 128 224 C86 224 52 204 50 164 C48 116 86 60 128 26 Z"),
         RING(128, 150, 34, 10) + C(128, 150, 10) + C(80, 196, 9) + C(176, 196, 9) + C(128, 70, 7)),
        (star4(36, 54, 18) + star4(220, 44, 14) + star4(226, 226, 12), ""),
    ]

    # --- rooms
    I["Library"] = [  # books on a shelf, one leaning
        (R(24, 214, 208, 18, 4), ""),
        (R(36, 70, 34, 144, 5) + R(76, 46, 40, 168, 5) + R(122, 86, 30, 128, 5),
         S("M36 92 L70 92", 6) + S("M36 192 L70 192", 6) + S("M76 70 L116 70", 6) + S("M76 190 L116 190", 6)
         + R(86, 104, 20, 40, 3) + S("M122 106 L152 106", 5) + S("M122 194 L152 194", 5)),
        (G("rotate(22 172 214)", R(160, 64, 38, 150, 5)), G("rotate(22 172 214)", S("M160 88 L198 88", 6)
                                                            + S("M160 190 L198 190", 6))),
    ]
    I["Archive"] = [  # a scroll with its wax seal
        (R(58, 72, 140, 112) + R(40, 52, 176, 32, 16) + R(40, 170, 176, 32, 16),
         S("M80 102 L176 102", 6) + S("M80 122 L176 122", 6) + S("M80 142 L150 142", 6) + C(52, 68, 6) + C(204, 186, 6)),
        (C(172, 204, 28), star5(172, 204, 14)),
    ]
    I["RecordsOffice"] = [  # a cabinet of three drawers
        (R(48, 28, 160, 210, 10) + R(60, 236, 20, 10) + R(176, 236, 20, 10),
         S("M48 96 L208 96", 8) + S("M48 166 L208 166", 8) + R(98, 52, 60, 14, 6) + R(98, 122, 60, 14, 6)
         + R(98, 192, 60, 14, 6) + R(112, 36, 32, 10, 2) + R(112, 106, 32, 10, 2) + R(112, 176, 32, 10, 2)),
    ]
    I["Infirmary"] = [  # the rod and its serpent (no red cross)
        (R(120, 30, 16, 206, 7) + C(128, 28, 13), ""),
        (S("M128 214 C86 202 88 176 128 166 C168 156 170 130 128 122 C88 114 90 88 128 80 C152 76 160 62 152 52", 15)
         + E(150, 46, 15, 11, -20), C(155, 42, 3)),
    ]
    I["Headmaster"] = [  # the mortarboard and its tassel
        (P("M74 116 L74 164 C102 184 154 184 182 164 L182 116 L128 140 Z"), S("M90 170 Q128 184 166 170", 0)),
        (P("M128 50 L232 94 L128 138 L24 94 Z"), C(128, 94, 7)),
        (S("M128 94 L206 112 L206 176", 6) + P("M198 172 L214 172 L220 206 L192 206 Z"), S("M200 186 L212 186", 3)),
    ]
    I["StaffRoom"] = [  # a cup of tea
        (E(122, 204, 96, 16), ""),
        (P("M54 104 L190 104 C188 160 162 190 122 190 C82 190 56 160 54 104 Z"), S("M70 126 Q122 140 174 126", 6)),
        (S("M186 120 C222 116 222 162 176 162", 13), ""),
        (S("M98 82 C86 66 108 56 96 38", 7) + S("M130 82 C118 64 142 54 128 30", 7) + S("M160 82 C150 68 168 58 158 44", 6),
         ""),
    ]
    I["Lounge"] = [  # a wingback armchair
        (P("M68 140 L68 62 C68 40 84 32 128 32 C172 32 188 40 188 62 L188 140 Z"), S("M128 48 L128 128", 0)
         + C(98, 80, 5) + C(128, 74, 5) + C(158, 80, 5) + C(112, 108, 5) + C(144, 108, 5)),
        (R(68, 140, 120, 42, 8) + R(70, 196, 14, 36, 4) + R(172, 196, 14, 36, 4) + R(60, 178, 136, 22, 6), ""),
        (R(32, 104, 40, 92, 18) + R(184, 104, 40, 92, 18), ""),
    ]
    I["Cafeteria"] = [  # a plate between fork and knife
        (C(128, 132, 66), RING(128, 132, 44, 7)),
        (R(32, 124, 14, 104, 6) + P("M24 40 L32 40 L32 92 L35 92 L35 40 L43 40 L43 92 L46 92 L46 40 L54 40 L54 104 "
                                    "C54 118 46 124 39 124 C32 124 24 118 24 104 Z")
         + P("M214 40 C232 60 234 110 222 128 L222 228 L208 228 L208 40 Z"), ""),
    ]
    I["Chapel"] = [  # a lancet window of two lights and a rose
        (P("M56 232 L56 122 C56 72 96 40 128 24 C160 40 200 72 200 122 L200 232 Z"),
         S("M128 132 L128 232", 9) + P("M80 232 L80 150 C80 136 92 126 104 120 C116 126 120 136 120 150 L120 232 Z")
         + P("M136 232 L136 150 C136 136 140 126 152 120 C164 126 176 136 176 150 L176 232 Z")
         + RING(128, 86, 24, 7) + C(128, 86, 6) + S("M128 62 L128 110", 4) + S("M104 86 L152 86", 4)),
    ]
    I["Dormitory"] = [  # a bed under a crescent moon
        (R(28, 116, 22, 116, 6) + R(206, 146, 22, 86, 6) + R(28, 168, 200, 36, 6) + R(56, 140, 46, 28, 12)
         + R(104, 148, 102, 20, 6), S("M50 184 L206 184", 0)),
        (C(176, 66, 38), C(196, 52, 33)),
        (star4(110, 50, 14) + star4(78, 80, 9), ""),
    ]
    I["CommonRoom"] = [  # a fireplace burning
        (R(28, 66, 200, 22, 5) + R(40, 52, 176, 16, 4) + R(48, 88, 34, 132) + R(174, 88, 34, 132) + R(28, 218, 200, 16, 4)
         + P("M82 88 L174 88 L174 102 C150 102 106 102 82 102 Z"), ""),
        (P("M128 208 C96 204 92 178 104 160 C108 172 116 176 118 170 C112 150 124 132 140 120 C138 140 150 148 154 164 "
           "C158 156 160 150 158 142 C172 158 170 204 128 208 Z") + R(96, 206, 64, 10, 4),
         P("M128 200 C114 198 112 186 120 176 C122 184 128 186 130 182 C128 172 134 164 140 160 C140 172 146 178 146 186 "
           "C146 196 138 200 128 200 Z")),
    ]
    I["LockerRoom"] = [  # a pair of lockers
        (R(36, 28, 88, 208, 8) + R(132, 28, 88, 208, 8),
         "".join(S(f"M54 {y} L106 {y}", 5) + S(f"M150 {y} L202 {y}", 5) for y in (48, 60, 72))
         + R(96, 120, 10, 34, 4) + R(150, 120, 10, 34, 4) + S("M54 206 L106 206", 5) + S("M150 206 L202 206", 5)),
    ]
    I["BoilerRoom"] = [  # a valve wheel
        (RING(128, 128, 92, 16) + "".join(S(f"M128 128 L{128 + 90 * math.cos(math.radians(a)):.1f} "
                                            f"{128 + 90 * math.sin(math.radians(a)):.1f}", 11) for a in range(0, 360, 60))
         + C(128, 128, 26) + "".join(C(round(128 + 92 * math.cos(math.radians(a + 30)), 1),
                                       round(128 + 92 * math.sin(math.radians(a + 30)), 1), 12) for a in range(0, 360, 60)),
         C(128, 128, 10)),
    ]
    I["BellTower"] = [  # a great bell in its yoke
        (R(30, 26, 196, 20, 6) + R(112, 44, 32, 18, 4), ""),
        (P("M76 182 C76 116 92 70 128 64 C164 70 180 116 180 182 L204 202 L52 202 Z") + C(128, 222, 15),
         S("M84 158 Q128 146 172 158", 7) + S("M106 178 C104 132 112 96 124 82", 6)),
    ]
    I["Crypt"] = [  # a coffin-shaped door and its keyhole
        (P("M100 20 L156 20 L196 76 L172 236 L84 236 L60 76 Z"),
         P("M104 34 L152 34 L182 78 L160 222 L96 222 L74 78 Z").replace("/>", ' fill="none" stroke-width="6"/>')
         + C(128, 118, 15) + P("M120 124 L136 124 L142 160 L114 160 Z")),
    ]
    I["InkStudio"] = [  # an inkwell and a dipping nib
        (P("M68 156 L188 156 L200 226 L56 226 Z") + R(98, 128, 60, 30, 6), S("M70 182 L186 182", 6)),
        (G("translate(146 112) rotate(24)", P("M0 44 L-15 -8 L-15 -40 L15 -40 L15 -8 Z") + R(-10, -118, 20, 80, 8)),
         G("translate(146 112) rotate(24)", S("M0 44 L0 2", 4) + C(0, -2, 6))),
    ]
    I["Courtyard"] = [  # the dead oak
        (S("M128 232 L128 150", 24) + S("M128 160 C110 130 82 120 60 92", 14) + S("M128 156 C150 124 178 118 200 84", 14)
         + S("M128 150 C126 110 132 80 124 40", 12) + S("M60 92 L40 82", 8) + S("M60 92 L58 60", 8)
         + S("M200 84 L222 74", 8) + S("M200 84 L196 50", 8) + S("M124 40 L104 22", 7) + S("M124 40 L146 24", 7)
         + S("M86 118 L74 140", 7) + S("M170 116 L186 136", 7) + S("M96 232 Q128 214 160 232", 12)
         + R(40, 228, 176, 10, 5), ""),
    ]
    I["Reception"] = [  # a service bell on its desk
        (R(36, 196, 184, 22, 7) + P("M52 196 C52 142 86 108 128 108 C170 108 204 142 204 196 Z") + R(118, 82, 20, 30, 4)
         + R(104, 72, 48, 14, 6), S("M72 170 C78 146 96 130 116 124", 7)),
    ]
    I["LostFound"] = [  # a crate and a question
        (R(44, 140, 168, 96, 8), S("M44 172 L212 172", 6) + S("M100 176 L100 232", 6) + S("M156 176 L156 232", 6)),
        (S("M90 74 C90 30 166 26 166 72 C166 100 128 104 128 134", 20) + C(128, 26, 0), ""),
        (C(128, 152, 0), ""),
    ]
    I["Post"] = [  # a sealed letter
        (R(26, 62, 204, 140, 10), S("M30 68 L128 142 L226 68", 8) + S("M30 196 L100 132", 6) + S("M226 196 L156 132", 6)),
        (C(128, 146, 26), star5(128, 146, 13)),
    ]

    # --- restrooms
    I["Boys"] = boy()
    I["Girls"] = girl()
    gl, by = girl("translate(-22 36) scale(0.72)"), boy("translate(92 36) scale(0.72)")
    I["Restroom"] = [gl[0], gl[1], by[0], (R(124, 40, 8, 176, 4), "")]
    I["Accessible"] = [  # the access symbol
        (C(122, 38, 20) + S("M112 70 L112 146 L178 146 L196 206 L220 198", 22, "round")
         + S("M112 104 L168 104", 18), ""),
        (S("M84 112 A62 62 0 1 0 172 196", 18), ""),
    ]

    # --- wayfinding and rules
    I["Arrow"] = [  # a fletched arrow, pointing right (turn it with IconRotation)
        (R(54, 120, 136, 16, 3) + P("M180 92 L236 128 L180 164 L192 128 Z")
         + P("M20 98 L52 98 L80 120 L48 120 Z") + P("M20 158 L52 158 L80 136 L48 136 Z")
         + P("M44 98 L72 98 L100 120 L72 120 Z") + P("M44 158 L72 158 L100 136 L72 136 Z"), ""),
    ]
    I["Stairs"] = [  # a flight of steps going up
        (poly([(24, 228), (24, 190), (72, 190), (72, 150), (120, 150), (120, 110), (168, 110), (168, 70), (232, 70), (232, 228)]),
         ""),
        (S("M44 150 L116 78", 12) + P("M92 66 L130 64 L128 102 Z"), ""),
    ]
    I["Exit"] = [  # an arched way out and an arrow through it
        (P("M40 236 L40 110 C40 58 80 26 112 26 C144 26 184 58 184 110 L184 236 Z"),
         P("M60 236 L60 112 C60 70 90 46 112 46 C134 46 164 70 164 112 L164 236 Z")),
        (P("M88 236 L88 112 C88 92 100 80 112 76 L150 96 L150 236 Z"), C(136, 160, 6)),
        (R(120, 142, 80, 22, 4) + P("M190 116 L240 153 L190 190 Z"), ""),
    ]
    I["Quiet"] = [  # an owl (quiet in the halls)
        (R(36, 214, 184, 14, 6), ""),
        (P("M128 40 C150 40 160 30 176 18 C182 40 182 56 176 68 C196 90 204 124 198 160 C190 204 162 220 128 220 "
           "C94 220 66 204 58 160 C52 124 60 90 80 68 C74 56 74 40 80 18 C96 30 106 40 128 40 Z"),
         C(98, 98, 25) + C(158, 98, 25) + P("M120 120 L136 120 L128 140 Z") + S("M86 158 Q100 186 116 196", 6)
         + S("M170 158 Q156 186 140 196", 6) + S("M128 154 L128 156", 6) + S("M114 168 L114 170", 6)
         + S("M142 168 L142 170", 6)),
        (C(98, 98, 10) + C(158, 98, 10), ""),
    ]
    no_ring = RING(128, 128, 104, 18)
    no_bar = S("M54 202 L202 54", 18, "butt")
    I["NoRunning"] = [
        (C(146, 58, 18) + S("M132 86 L108 148", 18) + S("M108 148 L76 168 L66 204", 14) + S("M108 148 L146 176 L150 214", 14)
         + S("M128 98 L92 108 L72 132", 12) + S("M130 96 L156 124 L184 116", 12), ""),
        (no_ring + no_bar, ""),
    ]
    I["NoMagic"] = [
        (S("M70 186 L160 96", 14) + R(150, 74, 30, 30, 4, 'transform="rotate(45 165 89)"') + star4(196, 60, 22)
         + star4(150, 50, 11) + star4(206, 110, 11), ""),
        (no_ring + S("M54 54 L202 202", 18, "butt"), ""),
    ]
    I["NoEntry"] = [
        (C(128, 128, 104), R(56, 110, 144, 36, 6)),
    ]
    I["KeepOut"] = [  # a barred gate, chained and locked
        (P("M40 232 L40 100 C40 60 84 30 128 30 C172 30 216 60 216 100 L216 232 Z"),
         P("M56 232 L56 102 C56 70 92 46 128 46 C164 46 200 70 200 102 L200 232 Z")),
        ("".join(S(f"M{x} {54 + abs(x - 128) * 0.45:.0f} L{x} 232", 9) + P(f"M{x - 9} {50 + abs(x - 128) * 0.45:.0f} "
                                                                           f"L{x} {34 + abs(x - 128) * 0.45:.0f} L{x + 9} {50 + abs(x - 128) * 0.45:.0f} Z")
                 for x in (76, 102, 128, 154, 180)) + R(56, 120, 144, 9, 3), ""),
        (R(98, 140, 60, 50, 8) + S("M110 142 L110 124 C110 104 146 104 146 124 L146 142", 10), C(128, 160, 7)
         + R(124, 162, 8, 16, 2)),
    ]
    I["StaffOnly"] = [  # a skeleton key
        (G("rotate(-40 128 128)", RING(60, 128, 34, 14) + R(92, 120, 130, 16, 4) + R(186, 136, 14, 28, 2)
           + R(206, 136, 14, 38, 2) + R(160, 136, 10, 18, 2)),
         G("rotate(-40 128 128)", C(60, 128, 7))),
    ]
    I["Danger"] = [  # skull and crossed bones (no gore)
        (G("rotate(38 128 150)", R(40, 140, 176, 18, 9) + C(40, 141, 12) + C(40, 157, 12) + C(216, 141, 12) + C(216, 157, 12))
         + G("rotate(-38 128 150)", R(40, 140, 176, 18, 9) + C(40, 141, 12) + C(40, 157, 12) + C(216, 141, 12)
             + C(216, 157, 12)), ""),
        (P("M128 26 C170 26 196 54 196 92 C196 116 184 130 172 138 L172 160 L84 160 L84 138 C72 130 60 116 60 92 "
           "C60 54 86 26 128 26 Z"),
         E(102, 96, 17, 19) + E(154, 96, 17, 19) + P("M128 116 L138 136 L118 136 Z") + S("M106 146 L106 160", 5)
         + S("M128 146 L128 160", 5) + S("M150 146 L150 160", 5)),
    ]
    I["Information"] = [
        (C(128, 128, 104), C(128, 72, 15) + R(114, 102, 28, 96, 6) + R(100, 102, 28, 14, 3) + R(100, 186, 56, 14, 3)),
    ]
    I["Curfew"] = [  # a clock before the moon
        (C(182, 72, 58), C(154, 96, 52)),
        (C(108, 150, 80), RING(108, 150, 64, 6) + S("M108 150 L108 100", 10) + S("M108 150 L144 164", 10) + C(108, 150, 8)
         + "".join(C(round(108 + 52 * math.cos(math.radians(a)), 1), round(150 + 52 * math.sin(math.radians(a)), 1), 4)
                   for a in range(0, 360, 30))),
    ]
    I["WetFloor"] = [  # drops over a wet floor
        (P("M128 26 C150 66 174 92 174 126 C174 152 154 170 128 170 C102 170 82 152 82 126 C82 92 106 66 128 26 Z")
         + P("M58 92 C70 112 82 124 82 140 C82 154 72 162 58 162 C44 162 34 154 34 140 C34 124 46 112 58 92 Z")
         + P("M198 92 C210 112 222 124 222 140 C222 154 212 162 198 162 C184 162 174 154 174 140 C174 124 186 112 198 92 Z"),
         S("M104 124 C104 108 112 96 118 88", 6)),
        (S("M30 204 Q56 188 82 204 T134 204 T186 204 T238 204", 10) + S("M48 230 Q74 214 100 230 T152 230 T204 230", 9), ""),
    ]
    def pol(r, deg):
        return (128 + r * math.cos(math.radians(deg - 90)), 128 + r * math.sin(math.radians(deg - 90)))
    seams = ""
    for a in range(0, 360, 72):
        p0, p1 = pol(30, a), pol(60, a)
        seams += S(f"M{p0[0]:.1f} {p0[1]:.1f} L{p1[0]:.1f} {p1[1]:.1f}", 6)
        for b in (a - 36, a + 36):
            q = pol(68, b)
            seams += S(f"M{p1[0]:.1f} {p1[1]:.1f} L{q[0]:.1f} {q[1]:.1f}", 6)
    edge = ""
    for b in range(36, 396, 72):
        c = pol(92, b)
        pts = []
        for k in range(5):     # a pentagon on the rim, a vertex pointing at the centre
            ang = math.radians(b - 90 + 180 + k * 72)
            pts.append((c[0] + 24 * math.cos(ang), c[1] + 24 * math.sin(ang)))
        edge += poly(pts)
    I["Football"] = [  # a panelled match ball
        (C(128, 128, 100), poly([pol(30, a) for a in range(0, 360, 72)]) + edge + seams),
        (RING(128, 128, 106, 7), ""),
    ]
    I["Crest"] = [  # the school's shield, a key under three stars (a general room or house sign)
        (P("M40 34 L216 34 L216 120 C216 176 176 214 128 236 C80 214 40 176 40 120 Z"),
         P("M56 50 L200 50 L200 120 C200 166 168 198 128 218 C88 198 56 166 56 120 Z").replace("/>", ' fill="none" stroke-width="6"/>')
         + star5(88, 82, 13) + star5(128, 76, 13) + star5(168, 82, 13)
         + G("rotate(-90 128 150)", RING(98, 150, 17, 9) + R(113, 145, 64, 10, 3) + R(160, 153, 8, 16, 2)
             + R(146, 153, 6, 11, 2))),
    ]
    return I


ORDER = ("Homeroom Mathematics Chemistry English History Detention Herbology HomeEconomics Sewing Photography Woodshop "
         "Ceramics Drama Art Music Choir Gym Football Alchemy Astronomy Seance Library Archive RecordsOffice Infirmary "
         "Headmaster StaffRoom Lounge Cafeteria Chapel Dormitory CommonRoom LockerRoom BoilerRoom BellTower Crypt InkStudio "
         "Courtyard Reception LostFound Post Crest Boys Girls Restroom Accessible Arrow Stairs Exit Quiet NoRunning NoMagic "
         "NoEntry KeepOut StaffOnly Danger Information Curfew WetFloor").split()


def svg_of(layers, px=2048):
    defs, body = [], []
    n = len(layers)
    for i, (fill, cut) in enumerate(layers):
        knock = "".join(layers[j][0] for j in range(i + 1, n))
        knock = re.sub(r'stroke-width="([\d.]+)"', lambda m: f'stroke-width="{float(m.group(1)) + GAP * 2}"', knock)
        m = (f'<mask id="m{i}" maskUnits="userSpaceOnUse" x="-64" y="-64" width="384" height="384">'
             f'<rect x="-64" y="-64" width="384" height="384" fill="#fff"/>'
             f'<g fill="#000" stroke="#000">{cut}</g>'
             f'<g fill="#000" stroke="#000" stroke-width="{GAP * 2}" stroke-linejoin="round">{knock}</g></mask>')
        defs.append(m)
        body.append(f'<g mask="url(#m{i})" fill="#fff" stroke="#fff">{fill}</g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{px}" height="{px}" viewBox="0 0 256 256">'
            f'<defs>{"".join(defs)}</defs>{"".join(body)}</svg>')


def render(name, layers):
    os.makedirs(SVG, exist_ok=True)
    os.makedirs(os.path.join(OUT, "raw"), exist_ok=True)
    sv = os.path.join(SVG, f"{name}.svg")
    with open(sv, "w", encoding="utf-8") as f:
        f.write(svg_of(layers))
    html = os.path.join(SVG, f"{name}.html")
    with open(html, "w", encoding="utf-8") as f:
        f.write('<html><body style="margin:0;background:transparent">' + svg_of(layers) + "</body></html>")
    raw = os.path.join(OUT, "raw", f"{name}.png")
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                    "--default-background-color=00000000", "--window-size=2048,2048", f"--screenshot={raw}",
                    "file:///" + html.replace("\\", "/")], capture_output=True, timeout=60)
    return raw


def finish(name, raw, size=1024):
    """2048 white-on-clear -> 1024 icon: alpha from the render, RGB a soft emboss, the colour bled under clear pixels."""
    from PIL import Image, ImageChops, ImageFilter
    im = Image.open(raw).convert("RGBA")
    a = im.getchannel("A")
    # pad 3% so the knocked-out edge and the drop shadow in Roblox never touch the image border
    pad = int(2048 * 0.03)
    canvas = Image.new("L", (2048 + pad * 2, 2048 + pad * 2), 0)
    canvas.paste(a, (pad, pad))
    a = canvas.resize((size, size), Image.LANCZOS)
    # emboss: light from the top left over a blurred height field, kept light (tinting multiplies it)
    h = a.filter(ImageFilter.GaussianBlur(size / 256 * 2.2))
    sh = ImageChops.subtract(h, ImageChops.offset(h, 2, 2), 0.5, 128)   # 128 = flat
    lum = sh.point(lambda v: max(0, min(255, int(232 + (v - 128) * 1.1))))
    rgb = Image.merge("RGB", (lum, lum, lum))
    out = rgb.copy()
    out.putalpha(a)
    # bleed: under clear pixels the colour is the flat light grey, so filtering never pulls in black
    bg = Image.new("RGBA", out.size, (232, 232, 232, 0))
    bg.paste(rgb, (0, 0), a.point(lambda v: 255 if v > 0 else 0))
    bg.putalpha(a)
    path = os.path.join(OUT, f"NHSign_{name}.png")
    bg.save(path)
    return path


def sheet(names, path, cols=10, cell=200, tint=(255, 214, 128), back=(22, 18, 22)):
    from PIL import Image, ImageDraw, ImageFont
    rows = math.ceil(len(names) / cols)
    W, H = cols * cell, rows * (cell + 34) + 20
    sh = Image.new("RGB", (W, H), back)
    d = ImageDraw.Draw(sh)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", 17)
    except OSError:
        font = ImageFont.load_default()
    for k, n in enumerate(names):
        p = os.path.join(OUT, f"NHSign_{n}.png")
        if not os.path.exists(p):
            continue
        ic = Image.open(p).convert("RGBA").resize((cell - 30, cell - 30), Image.LANCZOS)
        r, g, b, a = ic.split()
        col = Image.merge("RGB", [ch.point(lambda v, t=t: v * t // 255) for ch, t in zip((r, g, b), tint)])
        x, y = (k % cols) * cell + 15, (k // cols) * (cell + 34) + 15
        shadow = Image.new("RGB", ic.size, (0, 0, 0))
        sh.paste(shadow, (x + 3, y + 4), a.point(lambda v: v * 0.55))
        sh.paste(col, (x, y), a)
        tw = d.textlength(n, font=font)
        d.text((x + (cell - 30 - tw) / 2, y + cell - 22), n, fill=(200, 190, 170), font=font)
    sh.save(path, quality=92)
    return path


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    I = icons()
    names = args or ORDER
    if "--refinish" in sys.argv:       # only redo the 1024 PNGs from the existing 2048 renders
        for n in names:
            finish(n, os.path.join(OUT, "raw", f"{n}.png"))
        if "--sheet" in sys.argv:
            sheet(ORDER, os.path.join(HERE, "icons", "IconSheet_gilt.jpg"))
            sheet(ORDER, os.path.join(HERE, "icons", "IconSheet_ink.jpg"), tint=(30, 24, 28), back=(196, 160, 96))
        sys.exit(0)
    missing = [n for n in ORDER if n not in I]
    assert not missing, missing
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(6) as ex:
        raws = list(ex.map(lambda n: (n, render(n, I[n])), names))
    for n, raw in raws:
        finish(n, raw)
    if "--sheet" in sys.argv:
        print(sheet(ORDER, os.path.join(HERE, "icons", "IconSheet_gilt.jpg")))
        print(sheet(ORDER, os.path.join(HERE, "icons", "IconSheet_ink.jpg"), tint=(30, 24, 28), back=(196, 160, 96)))
    print(len(names), "icons")
