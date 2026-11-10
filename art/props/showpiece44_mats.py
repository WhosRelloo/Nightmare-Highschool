"""Props batch 44 (the showpiece kit): procedural PBR materials, one look per real material, so the 2048 bake keeps
fabric reading as fabric and metal as metal: every material drives its own colour, roughness, metalness and normal
(weave, pile, grain, brushing, hammering, patina, veining, facets), then nh_props._weather adds edge wear and crevice
dirt. Pattern scales are in studs (object space), tuned for a 2048 statue atlas (about 130 px a stud).

  K = kit(mode)   mode "statue" (stone and bronze bodies, real cloth and metal) or "paint" (full colour, for the
                  painting renders); kit() returns a dict of every material by key.
"""
import bpy

import nh_props as P

_cache = {}


class G:
    """A tiny node-graph builder on one material."""

    def __init__(self, name):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        self.mat = mat
        self.nt = mat.node_tree
        for n in list(self.nt.nodes):
            self.nt.nodes.remove(n)
        self.out = self.nt.nodes.new("ShaderNodeOutputMaterial")
        self.bs = self.nt.nodes.new("ShaderNodeBsdfPrincipled")
        self.nt.links.new(self.bs.outputs["BSDF"], self.out.inputs["Surface"])
        self._tc = self.nt.nodes.new("ShaderNodeTexCoord")

    def L(self, a, b):
        self.nt.links.new(a, b)

    def _in(self, sock, v):
        if isinstance(v, (int, float)):
            sock.default_value = v
        elif isinstance(v, tuple):
            sock.default_value = v if len(v) == len(sock.default_value) else (*v, 1.0)
        else:
            self.L(v, sock)

    def coord(self, scale=1.0, stretch=(1, 1, 1), offset=(0, 0, 0), rot=(0, 0, 0)):
        mp = self.nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (scale * stretch[0], scale * stretch[1], scale * stretch[2])
        mp.inputs["Location"].default_value = offset
        mp.inputs["Rotation"].default_value = rot
        self.L(self._tc.outputs["Object"], mp.inputs["Vector"])
        return mp.outputs["Vector"]

    def noise(self, vec, scale, detail=2.0, rough=0.5, dist=0.0, color=False):
        n = self.nt.nodes.new("ShaderNodeTexNoise")
        self.L(vec, n.inputs["Vector"])
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = detail
        n.inputs["Roughness"].default_value = rough
        n.inputs["Distortion"].default_value = dist
        return n.outputs["Color" if color else "Fac"]

    def voronoi(self, vec, scale, feature="F1", rnd=1.0, out="Distance"):
        n = self.nt.nodes.new("ShaderNodeTexVoronoi")
        n.feature = feature
        self.L(vec, n.inputs["Vector"])
        n.inputs["Scale"].default_value = scale
        n.inputs["Randomness"].default_value = rnd
        return n.outputs[out]

    def wave(self, vec, scale, direction="X", dist=0.0, detail=0.0, profile="SIN", phase=0.0):
        n = self.nt.nodes.new("ShaderNodeTexWave")
        n.wave_type = "BANDS"
        n.bands_direction = direction
        n.wave_profile = profile
        self.L(vec, n.inputs["Vector"])
        n.inputs["Scale"].default_value = scale
        n.inputs["Distortion"].default_value = dist
        n.inputs["Detail"].default_value = detail
        n.inputs["Phase Offset"].default_value = phase
        return n.outputs["Fac"]

    def m(self, op, a, b=None, c=None, clamp=False):
        n = self.nt.nodes.new("ShaderNodeMath")
        n.operation = op
        n.use_clamp = clamp
        for i, v in enumerate((a, b, c)):
            if v is not None:
                self._in(n.inputs[i], v)
        return n.outputs[0]

    def lerp(self, a, b, t):
        """a + (b - a) * t for floats (a, b numbers or sockets)."""
        return self.m("MULTIPLY_ADD", t, self.m("SUBTRACT", b, a), a)

    def ramp(self, fac, lo, hi):
        """Smoothstep-like remap of fac from [lo, hi] to [0, 1]."""
        n = self.nt.nodes.new("ShaderNodeMapRange")
        n.interpolation_type = "SMOOTHSTEP"
        self._in(n.inputs["Value"], fac)
        n.inputs["From Min"].default_value = lo
        n.inputs["From Max"].default_value = hi
        return n.outputs["Result"]

    def rgb(self, c):
        n = self.nt.nodes.new("ShaderNodeRGB")
        n.outputs[0].default_value = (*c, 1)
        return n.outputs[0]

    def mixc(self, a, b, t):
        n = self.nt.nodes.new("ShaderNodeMix")
        n.data_type = "RGBA"
        self._in(n.inputs[0], t)
        self._in(n.inputs[6], a if not isinstance(a, tuple) else (*a, 1))
        self._in(n.inputs[7], b if not isinstance(b, tuple) else (*b, 1))
        return n.outputs[2]

    def scale(self, col, k):
        n = self.nt.nodes.new("ShaderNodeVectorMath")
        n.operation = "SCALE"
        self._in(n.inputs[0], col if not isinstance(col, tuple) else col)
        self._in(n.inputs["Scale"], k)
        return n.outputs[0]

    def val(self, v):
        n = self.nt.nodes.new("ShaderNodeValue")
        n.outputs[0].default_value = v
        return n.outputs[0]

    def bump(self, height, strength, dist=0.02, normal=None):
        n = self.nt.nodes.new("ShaderNodeBump")
        n.inputs["Strength"].default_value = strength
        n.inputs["Distance"].default_value = dist
        self.L(height, n.inputs["Height"])
        if normal is not None:
            self.L(normal, n.inputs["Normal"])
        return n.outputs["Normal"]

    def finish(self, col, rough, metal, normal, wear=0.2, wear_metal=False, dirt=0.6):
        if isinstance(rough, (int, float)):
            rough = self.val(rough)
        if isinstance(metal, (int, float)):
            metal = self.val(metal)
        P._weather(self.nt, self.bs, col, rough, metal, normal, wear, wear_metal, dirt)
        self.mat["nh_kind"] = "pbr"
        return self.mat


def _key(*a):
    return "|".join(str(x) for x in a)


def cached(fn):
    def w(*a, **k):
        key = _key(fn.__name__, *a, *sorted(k.items()))
        m = _cache.get(key)
        if m is None or m.name not in bpy.data.materials:
            m = fn(*a, **k)
            _cache[key] = m
        return m
    return w


def clear():
    _cache.clear()


# ================================================================== fabrics

@cached
def wool(name, rgb, threads=7.0, twill=True, fuzz=0.25, mottle=0.18, rough=0.86):
    """Woven wool (blazers, coats, cloaks): a 2/2 twill (diagonal ribs over a fine cross weave), fibre fuzz, dye mottling."""
    g = G(name)
    v = g.coord(threads)
    d = g.wave(v, 1.0, "DIAGONAL" if twill else "X", profile="SIN")
    w = g.wave(v, 1.0, "Z", profile="SIN", phase=1.3)
    xw = g.wave(v, 1.0, "X", profile="SIN", phase=0.4)
    fz = g.noise(g.coord(threads * 6), 1.0, 4.0, 0.6)
    weave = g.m("ADD", g.m("MULTIPLY", d, 0.55), g.m("MULTIPLY", g.m("MAXIMUM", w, xw), 0.35))
    h = g.m("ADD", weave, g.m("MULTIPLY", fz, fuzz))
    mot = g.noise(g.coord(1.1), 1.0, 3.0, 0.55)
    k = g.m("ADD", g.m("MULTIPLY", h, 0.32), g.m("MULTIPLY_ADD", mot, mottle * 2, 0.62 - mottle))
    col = g.scale(rgb, k)
    r = g.m("ADD", rough - 0.06, g.m("MULTIPLY", fz, 0.12))
    nrm = g.bump(h, 0.38, 0.015)
    return g.finish(col, r, 0.0, nrm, wear=0.12, dirt=0.55)


@cached
def velvet(name, rgb, crush=0.4):
    """Crushed velvet (capes, gowns, throne seats): a dense pile with soft crushed patches that catch the light,
    deep shadow in the folds, a very fine pile normal."""
    g = G(name)
    cr = g.noise(g.coord(1.6, (1, 1, 2.5)), 1.0, 4.0, 0.6, dist=1.4)
    cr2 = g.ramp(cr, 0.35, 0.7)
    pile = g.noise(g.coord(90.0), 1.0, 2.0, 0.5)
    k = g.m("ADD", g.m("MULTIPLY", cr2, crush * 1.6), 0.55 - crush * 0.4)
    col = g.scale(rgb, g.m("ADD", k, g.m("MULTIPLY", pile, 0.12)))
    r = g.m("SUBTRACT", 0.92, g.m("MULTIPLY", cr2, 0.25))
    nrm = g.bump(g.m("ADD", pile, g.m("MULTIPLY", cr, 0.6)), 0.18, 0.01)
    return g.finish(col, r, 0.0, nrm, wear=0.05, dirt=0.75)


@cached
def silk(name, rgb, sheen=0.35, lines=30.0):
    """Silk and satin (linings, sashes, ties, ribbons): smooth, with soft irregular sheen pools and a fine weft."""
    g = G(name)
    band = g.ramp(g.noise(g.coord(0.9, (1, 1, 0.35)), 1.0, 3.0, 0.55, dist=0.6), 0.35, 0.75)
    fine = g.wave(g.coord(lines), 1.0, "Z")
    k = g.m("ADD", 0.72 - sheen * 0.2, g.m("MULTIPLY", band, sheen))
    col = g.scale(rgb, g.m("ADD", k, g.m("MULTIPLY", fine, 0.04)))
    r = g.m("ADD", 0.24, g.m("MULTIPLY", band, 0.12))
    nrm = g.bump(fine, 0.06, 0.01)
    return g.finish(col, r, 0.0, nrm, wear=0.04, dirt=0.4)


@cached
def denim(name, rgb=(0.07, 0.11, 0.22)):
    """Denim: a steep blue twill with white weft flecks and faded high points."""
    g = G(name)
    v = g.coord(11.0)
    d = g.wave(v, 1.0, "DIAGONAL", profile="SAW")
    fleck = g.ramp(g.noise(g.coord(60.0, (1, 1, 4)), 1.0, 1.0), 0.55, 0.75)
    fade = g.noise(g.coord(1.4), 1.0, 3.0)
    base = g.scale(rgb, g.m("ADD", 0.7, g.m("MULTIPLY", d, 0.5)))
    col = g.mixc(base, (0.55, 0.58, 0.66), g.m("MULTIPLY", fleck, 0.4))
    col = g.mixc(col, (0.3, 0.38, 0.55), g.m("MULTIPLY", g.ramp(fade, 0.5, 0.8), 0.35))
    nrm = g.bump(d, 0.3, 0.012)
    return g.finish(col, 0.88, 0.0, nrm, wear=0.35, dirt=0.6)


@cached
def knit(name, rgb, ribs=9.0, stripe=None):
    """Jersey and rib knit (sports kit, jumpers, scarves): vertical knit columns of little V loops, optional stripe colour."""
    g = G(name)
    v = g.coord(ribs)
    col_ = g.wave(v, 1.0, "X", profile="SIN")
    loop = g.wave(g.coord(ribs * 1.8), 1.0, "Z", profile="TRI")
    h = g.m("MULTIPLY", col_, g.m("ADD", 0.6, g.m("MULTIPLY", loop, 0.4)))
    base = g.scale(rgb, g.m("ADD", 0.72, g.m("MULTIPLY", h, 0.35)))
    if stripe:
        st = g.ramp(g.wave(g.coord(0.55), 1.0, "Z", profile="SIN"), 0.78, 0.82)
        base = g.mixc(base, g.scale(stripe, g.m("ADD", 0.72, g.m("MULTIPLY", h, 0.35))), st)
    nrm = g.bump(h, 0.32, 0.012)
    return g.finish(base, 0.9, 0.0, nrm, wear=0.06, dirt=0.55)


@cached
def linen(name, rgb, threads=16.0):
    """Linen and cotton shirting (shirts, surplices, bandages): a plain over-under weave with slubs."""
    g = G(name)
    v = g.coord(threads)
    a = g.wave(v, 1.0, "X")
    b = g.wave(v, 1.0, "Z", phase=1.57)
    slub = g.noise(g.coord(threads * 0.6, (1, 1, 8)), 1.0, 2.0)
    h = g.m("ADD", g.m("MULTIPLY", a, b), g.m("MULTIPLY", slub, 0.3))
    col = g.scale(rgb, g.m("ADD", 0.82, g.m("MULTIPLY", h, 0.22)))
    return g.finish(col, 0.8, 0.0, g.bump(h, 0.22, 0.01), wear=0.05, dirt=0.5)


@cached
def fur(name, rgb, tip=None, scale=1.0):
    """Fur and hair (ruffs, wolf pelts, hair locks): long stretched strands in clumps, light tips, matted roots."""
    g = G(name)
    strand = g.noise(g.coord(26.0 * scale, (1, 1, 0.12)), 1.0, 6.0, 0.65)
    clump = g.noise(g.coord(3.0 * scale, (1, 1, 0.4)), 1.0, 2.0)
    h = g.m("ADD", strand, g.m("MULTIPLY", clump, 0.6))
    col = g.scale(rgb, g.m("ADD", 0.45, g.m("MULTIPLY", h, 0.7)))
    if tip:
        col = g.mixc(col, tip, g.m("MULTIPLY", g.ramp(strand, 0.55, 0.8), 0.6))
    return g.finish(col, g.m("ADD", 0.7, g.m("MULTIPLY", strand, 0.25)), 0.0, g.bump(h, 0.55, 0.02), wear=0.0, dirt=0.8)


@cached
def leather(name, rgb, grain=34.0, gloss=0.42, crease=0.22):
    """Leather (jackets, boots, belts, gauntlet cuffs, book covers): pebbled grain cells, creases, rubbed shine."""
    g = G(name)
    cell = g.voronoi(g.coord(grain), 1.0, "SMOOTH_F1")
    cr = g.wave(g.coord(3.5), 1.0, "Z", dist=6.0, detail=3.0)
    crl = g.ramp(cr, 0.0, 0.08)
    h = g.m("ADD", g.m("MULTIPLY", cell, 0.5), g.m("MULTIPLY", crl, crease))
    rub = g.noise(g.coord(1.2), 1.0, 3.0)
    col = g.scale(rgb, g.m("ADD", 0.62, g.m("MULTIPLY", h, 0.32)))
    col = g.mixc(col, g.scale(rgb, 1.6), g.m("MULTIPLY", g.ramp(rub, 0.55, 0.8), 0.35))
    r = g.m("SUBTRACT", g.m("ADD", gloss, g.m("MULTIPLY", h, 0.22)), g.m("MULTIPLY", g.ramp(rub, 0.55, 0.8), 0.15))
    return g.finish(col, r, 0.0, g.bump(h, 0.42, 0.012), wear=0.3, dirt=0.75)


# ================================================================== metals

@cached
def gold(name="Gold44", rgb=(1.0, 0.72, 0.3), rough=0.2, hammer=True, tarnish=0.25):
    """Polished gold and gilt brass (crowns, buckles, frame gilding): faint hammer dents, darker tarnish in patches."""
    g = G(name)
    h = g.voronoi(g.coord(9.0), 1.0, "SMOOTH_F1") if hammer else g.val(0.0)
    tn = g.ramp(g.noise(g.coord(2.2), 1.0, 5.0, 0.6), 0.55, 0.85)
    col = g.mixc(rgb, (rgb[0] * 0.42, rgb[1] * 0.3, rgb[2] * 0.16), g.m("MULTIPLY", tn, tarnish * 2))
    r = g.m("ADD", rough, g.m("MULTIPLY", tn, 0.3))
    return g.finish(col, r, 1.0, g.bump(h, 0.12, 0.01), wear=0.25, dirt=0.9)


@cached
def silver(name="Silver44", rgb=(0.8, 0.8, 0.82), rough=0.22, brushed=True, axis=(1, 1, 0.04)):
    """Polished steel and silver (blades, armour, buckles): fine brushing streaks along one axis, grey tarnish in crevices."""
    g = G(name)
    st = g.noise(g.coord(14.0, axis), 1.0, 6.0, 0.6) if brushed else g.val(0.5)
    scr = g.ramp(g.noise(g.coord(40.0, (1, 0.1, 1)), 1.0, 1.0), 0.72, 0.78)
    col = g.scale(rgb, g.m("ADD", 0.88, g.m("MULTIPLY", st, 0.18)))
    r = g.m("ADD", rough - 0.06, g.m("ADD", g.m("MULTIPLY", st, 0.12), g.m("MULTIPLY", scr, 0.2)))
    return g.finish(col, r, 1.0, g.bump(g.m("ADD", st, scr), 0.06, 0.01), wear=0.2, dirt=0.85)


@cached
def iron(name="Iron44", rgb=(0.085, 0.082, 0.09)):
    """Blackened wrought iron (chains, bands, lantern cages, frame brackets): pitted, a little rust in the pits, worn
    bright on the edges."""
    g = G(name)
    pit = g.voronoi(g.coord(18.0), 1.0, "F1")
    pitm = g.ramp(pit, 0.12, 0.0)
    rust = g.ramp(g.noise(g.coord(3.0), 1.0, 5.0, 0.6), 0.6, 0.78)
    col = g.mixc(rgb, (0.2, 0.08, 0.03), g.m("MULTIPLY", g.m("MAXIMUM", rust, pitm), 0.7))
    r = g.m("ADD", 0.5, g.m("MULTIPLY", g.m("MAXIMUM", rust, pitm), 0.4))
    mt = g.m("SUBTRACT", 0.85, g.m("MULTIPLY", rust, 0.8), clamp=True)
    return g.finish(col, r, mt, g.bump(g.m("ADD", pit, g.m("MULTIPLY", rust, 0.5)), 0.3, 0.01), wear=0.5, wear_metal=True, dirt=0.8)


@cached
def bronze(name="Bronze44", rgb=(0.42, 0.26, 0.13), patina=(0.16, 0.34, 0.29), amount=0.18, dark=1.0):
    """Statuary bronze with verdigris: polished brown bronze on the high points, chalky green-blue patina pooled in
    streaks and recesses (rough, not metal)."""
    g = G(name)
    n = g.noise(g.coord(1.7, (1, 1, 0.45)), 1.0, 6.0, 0.62, dist=0.6)
    msk = g.ramp(n, 0.62 - amount * 0.35, 0.72 - amount * 0.3)
    fine = g.noise(g.coord(22.0), 1.0, 3.0)
    bz = g.scale(tuple(c * dark for c in rgb), g.m("ADD", 0.8, g.m("MULTIPLY", fine, 0.35)))
    pt = g.scale(patina, g.m("ADD", 0.7, g.m("MULTIPLY", fine, 0.5)))
    col = g.mixc(bz, pt, msk)
    r = g.lerp(0.32, 0.82, msk)
    mt = g.lerp(1.0, 0.0, msk)
    return g.finish(col, r, mt, g.bump(g.m("ADD", g.m("MULTIPLY", msk, 0.6), g.m("MULTIPLY", fine, 0.3)), 0.25, 0.012),
                    wear=0.55, dirt=1.0)


# ================================================================== stone and the rest

@cached
def marble(name, base=(0.86, 0.84, 0.8), vein=(0.32, 0.31, 0.33), scale=1.1, width=0.035, rough=0.16, gold_vein=False):
    """Polished marble: soft clouding and a few thin meandering veins (isolines of a warped noise, so they branch and
    wander rather than stripe); gold_vein gives black marble gilt veins."""
    g = G(name)
    n = g.noise(g.coord(scale * 0.45), 1.0, 5.0, 0.62, dist=1.2)
    d = g.m("ABSOLUTE", g.m("SUBTRACT", n, 0.5))
    vm = g.ramp(d, width * 0.5, 0.0)
    n2 = g.noise(g.coord(scale * 1.3), 1.0, 4.0, 0.6, dist=0.8)
    vm2 = g.m("MULTIPLY", g.ramp(g.m("ABSOLUTE", g.m("SUBTRACT", n2, 0.5)), width * 0.25, 0.0), 0.55)
    vmask = g.m("MAXIMUM", vm, vm2)
    cl = g.noise(g.coord(scale * 2.8), 1.0, 4.0)
    b = g.scale(base, g.m("ADD", 0.88, g.m("MULTIPLY", cl, 0.18)))
    col = g.mixc(b, vein, vmask)
    mt = g.m("MULTIPLY", vmask, 0.9 if gold_vein else 0.0)
    return g.finish(col, g.m("ADD", rough, g.m("MULTIPLY", vmask, 0.15)), mt, g.bump(g.m("MULTIPLY", vmask, -1.0), 0.04, 0.01),
                    wear=0.08, dirt=0.75)


def stone(name, tint=(0.95, 0.93, 0.88), set_name="NH_Limestone", scale=0.28, dirt=0.95):
    """The game's own seamless stone sets (weathered limestone, slate, castle stone) so bases match the school."""
    key = _key("stone", name, tint, set_name, scale)
    if key not in _cache:
        _cache[key] = P.material(name, set_name, tint=tint, scale=scale, wear=0.35, dirt=dirt)
    return _cache[key]


@cached
def rough_stone(name, rgb=(0.32, 0.31, 0.3), scale=1.5, moss=0.0):
    """Broken rock and rubble (cracked plinth tops, boulders): chunky noise relief, lichen and optional moss."""
    g = G(name)
    n = g.noise(g.coord(scale), 1.0, 8.0, 0.62, dist=0.4)
    cr = g.ramp(g.voronoi(g.coord(scale * 1.4), 1.0, "DISTANCE_TO_EDGE"), 0.04, 0.0)
    col = g.scale(rgb, g.m("SUBTRACT", g.m("ADD", 0.6, g.m("MULTIPLY", n, 0.65)), g.m("MULTIPLY", cr, 0.5)))
    if moss:
        mm = g.ramp(g.noise(g.coord(2.2), 1.0, 5.0), 0.62 - moss * 0.2, 0.7 - moss * 0.2)
        col = g.mixc(col, (0.06, 0.09, 0.03), mm)
    return g.finish(col, g.m("ADD", 0.78, g.m("MULTIPLY", n, 0.18)), 0.0,
                    g.bump(g.m("SUBTRACT", n, g.m("MULTIPLY", cr, 0.8)), 0.7, 0.03), wear=0.4, dirt=1.0)


@cached
def wood(name, rgb=(0.2, 0.11, 0.06), scale=1.0, gloss=0.45, axis="Z"):
    """Oiled and lacquered oak and ebony (coffins, staffs, thrones, frames): ring figure, open pores, a waxed sheen."""
    g = G(name)
    st = {"Z": (1, 1, 0.08), "X": (0.08, 1, 1), "Y": (1, 0.08, 1)}[axis]
    rings = g.wave(g.coord(scale * 3.0, st), 1.0, "X" if axis != "X" else "Y", dist=4.0, detail=3.0)
    pore = g.noise(g.coord(scale * 60.0, st), 1.0, 2.0)
    col = g.scale(rgb, g.m("ADD", 0.7, g.m("MULTIPLY", rings, 0.5)))
    r = g.m("ADD", gloss, g.m("MULTIPLY", pore, 0.25))
    return g.finish(col, r, 0.0, g.bump(g.m("ADD", g.m("MULTIPLY", rings, 0.4), pore), 0.18, 0.01), wear=0.35, dirt=0.8)


@cached
def gem(name, rgb, rough=0.05):
    """Cut gemstones (rubies, amethysts, emeralds, moonstones): saturated, glassy, a brighter inner fire."""
    g = G(name)
    n = g.noise(g.coord(7.0), 1.0, 2.0)
    col = g.scale(rgb, g.m("ADD", 0.7, g.m("MULTIPLY", n, 0.8)))
    return g.finish(col, rough, 0.0, None, wear=0.0, dirt=0.0)


@cached
def plain(name, rgb, rough=0.5, metal=0.0, noise=0.08, bump=0.05, wear=0.15, dirt=0.6):
    """Smooth painted or enamelled surfaces (masks, spray cans, porcelain, enamel)."""
    g = G(name)
    n = g.noise(g.coord(6.0), 1.0, 3.0)
    col = g.scale(rgb, g.m("ADD", 1.0 - noise, g.m("MULTIPLY", n, noise * 2)))
    return g.finish(col, g.m("ADD", rough - 0.03, g.m("MULTIPLY", n, 0.06)), metal, g.bump(n, bump, 0.01), wear=wear, dirt=dirt)


@cached
def skin(name, rgb, rough=0.48):
    """Painted skin for the colour renders (a soft mottle and pore bump; R6 faces stay graphic)."""
    g = G(name)
    n = g.noise(g.coord(4.0), 1.0, 3.0)
    p = g.noise(g.coord(80.0), 1.0, 1.0)
    col = g.scale(rgb, g.m("ADD", 0.92, g.m("MULTIPLY", n, 0.12)))
    return g.finish(col, g.m("ADD", rough, g.m("MULTIPLY", p, 0.1)), 0.0, g.bump(p, 0.04, 0.005), wear=0.0, dirt=0.3)


@cached
def parchment(name="Parchment44", rgb=(0.78, 0.7, 0.52)):
    g = G(name)
    n = g.noise(g.coord(3.0), 1.0, 6.0, 0.6)
    fib = g.noise(g.coord(50.0, (1, 1, 0.3)), 1.0, 2.0)
    col = g.scale(rgb, g.m("ADD", 0.72, g.m("MULTIPLY", n, 0.4)))
    return g.finish(col, 0.85, 0.0, g.bump(fib, 0.1, 0.01), wear=0.2, dirt=0.8)


@cached
def ink(name="InkGloss44", rgb=(0.006, 0.006, 0.012), sheen=(0.12, 0.03, 0.2)):
    """Glossy living ink: near-black with an oily violet sheen swirling in it."""
    g = G(name)
    sw = g.wave(g.coord(1.2), 1.0, "DIAGONAL", dist=12.0, detail=4.0)
    col = g.mixc(rgb, sheen, g.m("MULTIPLY", g.ramp(sw, 0.6, 0.95), 0.8))
    return g.finish(col, 0.06, 0.0, g.bump(sw, 0.05, 0.01), wear=0.0, dirt=0.1)


@cached
def wax(name="Wax44", rgb=(0.86, 0.8, 0.66)):
    return plain(name + "p", rgb, rough=0.42, noise=0.06, bump=0.03, wear=0.0, dirt=0.5)


@cached
def bone(name="Bone44", rgb=(0.8, 0.76, 0.64)):
    g = G(name)
    n = g.noise(g.coord(5.0), 1.0, 6.0, 0.6)
    col = g.scale(rgb, g.m("ADD", 0.7, g.m("MULTIPLY", n, 0.4)))
    return g.finish(col, 0.62, 0.0, g.bump(n, 0.15, 0.01), wear=0.2, dirt=1.0)


def glow_mat(rgb):
    """What a _Glow piece bakes to (its own colour, flat): in Roblox it is Neon in this colour."""
    return plain(f"Glow44_{rgb}", rgb, rough=0.4, noise=0.02, bump=0.0, wear=0.0, dirt=0.0)


def glass_mat(rgb):
    return plain(f"Glass44_{rgb}", rgb, rough=0.05, noise=0.02, bump=0.0, wear=0.0, dirt=0.0)


# ================================================================== the kit

def kit():
    """Every material of the batch by key. The figures pick theirs by key (see showpiece44_chars.py)."""
    K = {
        # stone and statuary bodies
        "marble": marble("Marble44", (0.86, 0.84, 0.8), (0.34, 0.33, 0.35)),
        "marblewarm": marble("MarbleWarm44", (0.84, 0.79, 0.7), (0.45, 0.36, 0.28), scale=0.9),
        "blackmarble": marble("BlackMarble44", (0.025, 0.024, 0.03), (0.75, 0.6, 0.3), scale=1.3, width=0.03, rough=0.12, gold_vein=True),
        "bronze": bronze("Bronze44"),
        "bronzedk": bronze("BronzeDark44", rgb=(0.24, 0.15, 0.08), amount=0.12),
        "bronzegreen": bronze("BronzeVerdigris44", patina=(0.24, 0.5, 0.42), amount=0.6),
        "limestone": stone("Limestone44"),
        "limestonedk": stone("LimestoneDark44", tint=(0.55, 0.53, 0.5)),
        "slate": stone("Slate44", tint=(0.32, 0.36, 0.34), set_name="NH_Slate", scale=0.18),
        "rock": rough_stone("Rock44"),
        "rockmoss": rough_stone("RockMoss44", (0.3, 0.3, 0.28), moss=0.6),
        "granite": rough_stone("Granite44", (0.22, 0.21, 0.22), scale=3.0),
        # metals
        "gold": gold("Gold44"),
        "gilt": gold("Gilt44", (0.95, 0.68, 0.3), rough=0.3, tarnish=0.45),
        "silver": silver("Silver44"),
        "steel": silver("Steel44", (0.62, 0.63, 0.66), rough=0.18),
        "blade": silver("Blade44", (0.78, 0.8, 0.84), rough=0.12, axis=(0.04, 1, 1)),
        "iron": iron("Iron44"),
        "brass": gold("Brass44", (0.82, 0.6, 0.28), rough=0.34, hammer=False, tarnish=0.5),
        # fabrics
        "wool_black": wool("WoolBlack44", (0.035, 0.034, 0.04)),
        "wool_navy": wool("WoolNavy44", (0.03, 0.045, 0.1)),
        "wool_crimson": wool("WoolCrimson44", (0.2, 0.02, 0.03)),
        "wool_grey": wool("WoolGrey44", (0.16, 0.16, 0.17), threads=6.0),
        "wool_green": wool("WoolGreen44", (0.04, 0.09, 0.06)),
        "wool_plum": wool("WoolPlum44", (0.09, 0.03, 0.1)),
        "tweed": wool("Tweed44", (0.22, 0.17, 0.11), threads=5.0, fuzz=0.45, mottle=0.3),
        "velvet_crimson": velvet("VelvetCrimson44", (0.22, 0.012, 0.03)),
        "velvet_black": velvet("VelvetBlack44", (0.03, 0.025, 0.035)),
        "velvet_violet": velvet("VelvetViolet44", (0.12, 0.03, 0.2)),
        "velvet_blue": velvet("VelvetBlue44", (0.02, 0.04, 0.16)),
        "silk_crimson": silk("SilkCrimson44", (0.45, 0.02, 0.05)),
        "silk_black": silk("SilkBlack44", (0.03, 0.03, 0.035)),
        "silk_gold": silk("SilkGold44", (0.7, 0.5, 0.18)),
        "silk_ivory": silk("SilkIvory44", (0.85, 0.82, 0.74)),
        "silk_violet": silk("SilkViolet44", (0.25, 0.06, 0.4)),
        "linen": linen("Linen44", (0.86, 0.84, 0.78)),
        "linen_grey": linen("LinenGrey44", (0.45, 0.44, 0.42)),
        "denim": denim("Denim44"),
        "denim_black": denim("DenimBlack44", (0.04, 0.04, 0.05)),
        "knit_gold": knit("KnitGold44", (0.7, 0.48, 0.1), stripe=(0.3, 0.02, 0.03)),
        "knit_crimson": knit("KnitCrimson44", (0.4, 0.03, 0.05), stripe=(0.75, 0.6, 0.25)),
        "knit_grey": knit("KnitGrey44", (0.28, 0.28, 0.3)),
        "knit_white": knit("KnitWhite44", (0.85, 0.85, 0.82)),
        "leather_black": leather("LeatherBlack44", (0.035, 0.032, 0.035), gloss=0.32),
        "leather_brown": leather("LeatherBrown44", (0.22, 0.11, 0.05)),
        "leather_oxblood": leather("LeatherOxblood44", (0.18, 0.025, 0.03), gloss=0.35),
        "fur_grey": fur("FurGrey44", (0.25, 0.24, 0.24), tip=(0.6, 0.58, 0.55)),
        "fur_brown": fur("FurBrown44", (0.18, 0.11, 0.06), tip=(0.42, 0.3, 0.18)),
        "fur_white": fur("FurWhite44", (0.75, 0.74, 0.72), tip=(0.95, 0.95, 0.94)),
        "fur_black": fur("FurBlack44", (0.035, 0.03, 0.03), tip=(0.18, 0.16, 0.16)),
        # wood, gems, misc
        "oak": wood("Oak44", (0.3, 0.17, 0.08)),
        "ebony": wood("Ebony44", (0.035, 0.025, 0.02), gloss=0.25),
        "coffin": wood("CoffinWood44", (0.09, 0.03, 0.025), gloss=0.3),
        "ruby": gem("Ruby44", (0.6, 0.01, 0.04)),
        "amethyst": gem("Amethyst44", (0.32, 0.06, 0.55)),
        "emerald": gem("Emerald44", (0.02, 0.4, 0.15)),
        "sapphire": gem("Sapphire44", (0.03, 0.1, 0.55)),
        "moonstone": gem("Moonstone44", (0.7, 0.78, 0.92), rough=0.15),
        "parchment": parchment(),
        "ink": ink(),
        "wax": wax(),
        "bone": bone(),
        "porcelain": plain("Porcelain44", (0.9, 0.89, 0.86), rough=0.15, noise=0.03),
        "enamel_black": plain("EnamelBlack44", (0.02, 0.02, 0.025), rough=0.2),
        "rubber": plain("Rubber44", (0.03, 0.03, 0.03), rough=0.85),
        "spraycan": plain("SprayCan44", (0.6, 0.05, 0.4), rough=0.3, metal=0.6),
        "feather": fur("Feather44", (0.02, 0.02, 0.03), tip=(0.06, 0.07, 0.12), scale=0.6),
        "brick": stone("Brick44", (0.55, 0.35, 0.3), "NH_Limestone", 0.5),
        # skins (painting renders; statues use their body stone)
        "skin_pale": skin("SkinPale44", (0.8, 0.66, 0.56)),
        "skin_warm": skin("SkinWarm44", (0.6, 0.42, 0.3)),
        "skin_dark": skin("SkinDark44", (0.28, 0.17, 0.11)),
        "skin_vamp": skin("SkinVamp44", (0.78, 0.76, 0.8)),
        "skin_ghoul": skin("SkinGhoul44", (0.42, 0.46, 0.4)),
        "hair_black": fur("HairBlack44", (0.02, 0.018, 0.02), tip=(0.08, 0.07, 0.09), scale=1.6),
        "hair_brown": fur("HairBrown44", (0.12, 0.06, 0.03), tip=(0.25, 0.14, 0.07), scale=1.6),
        "hair_blond": fur("HairBlond44", (0.55, 0.4, 0.18), tip=(0.8, 0.66, 0.4), scale=1.6),
        "hair_white": fur("HairWhite44", (0.7, 0.7, 0.72), tip=(0.95, 0.95, 0.96), scale=1.6),
        "hair_red": fur("HairRed44", (0.3, 0.06, 0.02), tip=(0.55, 0.16, 0.05), scale=1.6),
        "turf": fur("Turf44", (0.04, 0.12, 0.03), tip=(0.12, 0.26, 0.06), scale=3.0),
        "dark": plain("FaceDark44", (0.02, 0.015, 0.02), rough=0.5, noise=0.0, bump=0.0, wear=0.0),
    }
    return K
