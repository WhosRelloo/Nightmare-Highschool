"""Shared sizes for props batch 41 (the art kit): the painted canvases' sizes in studs, and the panel layouts of the pieces
whose one canvas image spans several panels. Read by nh_props_batch41.py (the frames and boards) and art41_canvases.py
(the paintings), so an image always matches the shape it is projected onto. Pure data, no Blender."""
import math

# painting -> (shape, width, height) in studs; the image has the same aspect (long side 2048)
CANVAS = {
    "PortraitHeadmasterGallery": ("rect", 4.5, 8.0),
    "PortraitHeadmistress": ("rect", 3.0, 4.0),
    "PortraitCursedStudent": ("rect", 3.0, 4.0),
    "PortraitCountessOval": ("oval", 2.7, 3.6),
    "PaintingVampireBall": ("rect", 7.0, 3.94),
    "PaintingWolfHuntSnow": ("rect", 6.0, 3.375),
    "TondoMoonCloister": ("circle", 3.6, 3.6),
    "PaintingAcademyPanorama": ("rect", 9.0, 2.6),
    "PaintingClassOf1887": ("rect", 5.0, 3.5),
    "CliqueHeraldry": ("rect", 6.4, 3.6),
    "StainedGlassRoundel": ("circle", 3.0, 3.0),
    "MosaicRaven": ("arch", 3.2, 4.4),
    "IconTriptych": ("arch", 1.3, 1.9),
    "IconTriptychL": ("arch", 0.65, 1.55),
    "IconTriptychR": ("arch", 0.65, 1.55),
}

# PortraitMiniatures: five little portraits on a velvet board (board coords: x across, z up from the board's foot)
MINI_BOARD = (3.9, 4.6)
MINIS = [  # (render scene, shape, cx, cz, w, h)
    ("MiniCourtGirl", "oval", 0.0, 2.7, 1.25, 1.65),
    ("MiniVampire", "circle", -1.27, 3.62, 1.0, 1.0),
    ("MiniWolfGirl", "circle", 1.27, 3.62, 1.0, 1.0),
    ("MiniProfessor", "rect", -1.27, 1.55, 0.95, 1.2),
    ("MiniChoirBoy", "octagon", 1.27, 1.55, 0.95, 1.2),
]


def minis_bounds():
    x0 = min(cx - w / 2 for _, _, cx, cz, w, h in MINIS)
    x1 = max(cx + w / 2 for _, _, cx, cz, w, h in MINIS)
    z0 = min(cz - h / 2 for _, _, cx, cz, w, h in MINIS)
    z1 = max(cz + h / 2 for _, _, cx, cz, w, h in MINIS)
    return x0, x1, z0, z1


def px(name, long=2048):
    _, w, h = CANVAS[name]
    return (long, int(round(long * h / w))) if w >= h else (int(round(long * w / h)), long)


# the tapestries: (map name, width, height of the woven field incl. any dagged hem, in studs)
TAPESTRY = {"TapestryCliques": ("TapestryCliquesWeave", 6.0, 7.875), "TapestryProcession": ("TapestryProcessionWeave", 12.0, 6.75)}


# the cliques' emblems, as ReplicatedStorage.Config.Cliques draws them (nh_props_batch37): unit space, y up
EMBLEM = {
    "candle": dict(fills=[[(-0.12, -0.45), (0.12, -0.45), (0.12, 0.1), (-0.12, 0.1)], [(0, 0.42), (0.07, 0.3), (0.08, 0.2), (0.0, 0.13), (-0.08, 0.2), (-0.07, 0.3)]],
                   strokes=[[(-0.3, -0.48), (0.3, -0.48)]] + [[(math.cos(math.radians(a)) * 0.2, 0.25 + math.sin(math.radians(a)) * 0.2),
                                                               (math.cos(math.radians(a)) * 0.34, 0.25 + math.sin(math.radians(a)) * 0.34)] for a in (20, 55, 125, 160)]),
    "crown": dict(fills=[[(-0.4, -0.05), (-0.42, 0.35), (-0.22, 0.12), (0.0, 0.42), (0.22, 0.12), (0.42, 0.35), (0.4, -0.05)],
                         [(-0.22, -0.05), (-0.12, -0.05), (-0.17, -0.3)], [(0.12, -0.05), (0.22, -0.05), (0.17, -0.3)]], strokes=[]),
    "pennant": dict(fills=[[(-0.4, 0.4), (0.45, 0.2), (-0.4, 0.0)]], strokes=[[(-0.42, 0.45), (-0.42, -0.5)]]),
    "flames": dict(fills=[[(-0.45, -0.3)] + [p for i in range(6) for p in ((-0.45 + i * 0.16 + 0.08, 0.1 + 0.18 * (i % 2)), (-0.45 + i * 0.16 + 0.16, -0.12))] +
                          [(0.5, -0.3)], [(-0.35, -0.38), (0.35, -0.38), (0.35, -0.46), (-0.35, -0.46)]], strokes=[]),
    "paw": dict(fills=[[(math.cos(t) * 0.2, -0.15 + math.sin(t) * 0.16) for t in [k / 16 * 6.283 for k in range(16)]]] +
                [[(tx + math.cos(t) * 0.07, ty + math.sin(t) * 0.09) for t in [k / 12 * 6.283 for k in range(12)]] for tx, ty in
                 ((-0.24, 0.12), (-0.09, 0.26), (0.09, 0.26), (0.24, 0.12))], strokes=[]),
    "smiley": dict(fills=[[(-0.14 + math.cos(t) * 0.06, 0.12 + math.sin(t) * 0.06) for t in [k / 10 * 6.283 for k in range(10)]],
                          [(0.14 + math.cos(t) * 0.06, 0.12 + math.sin(t) * 0.06) for t in [k / 10 * 6.283 for k in range(10)]]],
                   strokes=[[(math.cos(t) * 0.42, math.sin(t) * 0.42) for t in [k / 28 * 6.283 for k in range(29)]],
                            [(math.cos(t) * 0.25, 0.02 + math.sin(t) * 0.25) for t in [math.radians(200 + k * 10) for k in range(15)]]]),
    "halo": dict(fills=[[(-0.05, 0.2), (0.05, 0.2), (0.05, 0.02), (0.2, 0.02), (0.2, -0.07), (0.05, -0.07), (0.05, -0.5), (-0.05, -0.5), (-0.05, -0.07),
                         (-0.2, -0.07), (-0.2, 0.02), (-0.05, 0.02)]],
                 strokes=[[(math.cos(t) * 0.22, 0.38 + math.sin(t) * 0.077) for t in [k / 24 * 6.283 for k in range(25)]]]),
    "quill": dict(fills=[[(0.38, 0.45), (0.25, 0.42), (0.05, 0.25), (-0.12, 0.0), (-0.2, -0.18), (-0.1, -0.08), (0.1, 0.08), (0.3, 0.3)]],
                  strokes=[[(0.38, 0.45), (-0.28, -0.32)], [(-0.28, -0.32), (-0.29, -0.45)]]),
}
