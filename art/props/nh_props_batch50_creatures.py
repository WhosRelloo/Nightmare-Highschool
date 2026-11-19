"""Props batch 50 (2026-11-19): the tutorial's two animals (docs/expansion/15-Tutorial-The-Last-Normal-Night.md §4),
sculpt-quality, rigged and animated. Both are a branching skeleton skinned into one smooth body (batch 33/34's method)
with soft parts as their own pieces, a fur or feather shader with real markings (object-space masks + a directional fur
or feather relief), and clips in the house style (anticipation, overshoot, a long settle, offsets between parts).

  "E:/Blender/blender.exe" --background --factory-startup --python art/props/nh_props_batch50_creatures.py -- <Biscuit|Goose|all> [--size 2048] [--samples 64] [--gpu]

Biscuit  the family's basset hound: long and low (4.6 long, 1.7 at the shoulder), crooked short legs with turned-out
         front paws, a deep keel of a chest, loose skin (a dewlap, jowls), a long sad face with a wrinkled brow, red-rimmed
         droopy eyes, huge ears that nearly touch the ground (their own piece, two bones each, they swing), a white-tipped
         tail; tricolour coat (tan, a black saddle, white chest, legs, muzzle, blaze and tail tip); a red collar with a
         brass tag. Clips: Sleep (breathing, an ear twitch; loops), WakeStare (one eye opens, the head lifts, a long
         stare), Sigh (a big inhale, the slow collapse back down), Wuff (one bored bark), Trot (loops).
Goose    a Canada goose with opinions, comically big (4.4 tall to the crown): a long black S-neck, the white chinstrap,
         a beige breast, a brown back with pale barring, a black tail over a white rump, black bill and webbed feet,
         folded wings (their own pieces, three bones each). Clips: Idle (neck sway, head turns; loops), Alert (stretches
         up tall), Hiss (neck coils low, wings half open, the bill gapes), Charge (the run, wings flapping; loops),
         Honk, Strut (the smug victory waddle; loops).

Front faces -Y, Z is up, the origin is at the bottom centre (feet on the ground). Each prop's clips: art/props/anim/<Prop>.json,
the actions in the FBX, the review sheet art/props/previews/<Prop>_clips.png (art/hometown/clip_sheet.py).
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nh_props as P  # noqa: E402
from nh_props import set_group, _finish, material  # noqa: E402
from nh_props_batch3 import sphere, cone  # noqa: E402
from nh_props_batch4 import _dims, lathe, hoop  # noqa: E402
from nh_props_batch33 import Skel  # noqa: E402
from nh_props_batch34 import chain  # noqa: E402
import nh_props_batch49_hometown as B49  # noqa: E402
from nh_props_batch49_hometown import RIG, CLIPS, ease, back_out, rig_pieces, clip_strips  # noqa: E402

BUILDERS = {}


# ------------------------------------------------------------------ shader helpers (object-space masks)

class NT:
    """a tiny node-graph helper: math on object coordinates for coat markings"""

    def __init__(self, m):
        self.nt = m.node_tree
        self.N, self.L = self.nt.nodes, self.nt.links.new
        tc = self.N.new("ShaderNodeTexCoord")
        sep = self.N.new("ShaderNodeSeparateXYZ")
        self.L(tc.outputs["Object"], sep.inputs[0])
        self.obj = tc.outputs["Object"]
        self.x, self.y, self.z = sep.outputs[0], sep.outputs[1], sep.outputs[2]

    def math(self, op, a, b=None, clamp=False):
        n = self.N.new("ShaderNodeMath")
        n.operation = op
        n.use_clamp = clamp
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                self.L(v, n.inputs[i])
        return n.outputs[0]

    def step(self, v, e0, e1):
        """smoothstep(e0, e1, v) via map range"""
        n = self.N.new("ShaderNodeMapRange")
        n.interpolation_type = "SMOOTHSTEP"
        n.inputs["From Min"].default_value = e0
        n.inputs["From Max"].default_value = e1
        self.L(v, n.inputs["Value"])
        return n.outputs["Result"]

    def noise(self, scale, detail=4, stretch=(1, 1, 1), out="Fac"):
        mp = self.N.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = stretch
        self.L(self.obj, mp.inputs["Vector"])
        n = self.N.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = detail
        self.L(mp.outputs["Vector"], n.inputs["Vector"])
        return n.outputs[out]

    def mix(self, fac, a, b):
        n = self.N.new("ShaderNodeMix")
        n.data_type = "RGBA"
        self.L(fac, n.inputs["Factor"])
        for slot, v in (("A", a), ("B", b)):
            if isinstance(v, tuple):
                n.inputs[slot].default_value = (*v, 1.0)
            else:
                self.L(v, n.inputs[slot])
        return n.outputs["Result"]

    def bump(self, height, strength, dist=0.02):
        b = self.N.new("ShaderNodeBump")
        b.inputs["Strength"].default_value = strength
        b.inputs["Distance"].default_value = dist
        self.L(height, b.inputs["Height"])
        return b.outputs["Normal"]


def _new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bs = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    return m, bs


def basset_coat():
    """tan, a black saddle over the back, white legs/chest/muzzle/blaze/tail tip; a short, dense coat lying back"""
    m, bs = _new_mat("BassetCoat")
    g = NT(m)
    wob = g.math("MULTIPLY", g.math("SUBTRACT", g.noise(3.0, 3), 0.5), 0.35)
    z = g.math("ADD", g.z, wob)
    y = g.math("ADD", g.y, wob)
    ax = g.math("ABSOLUTE", g.x)
    # white: low legs and paws, the chest and throat front, the muzzle, a blaze up the face, the belly, the tail tip
    legs = g.math("SUBTRACT", 1.0, g.step(z, 0.42, 0.62))
    chest = g.math("MULTIPLY", g.math("SUBTRACT", 1.0, g.step(y, -1.45, -1.15)), g.math("SUBTRACT", 1.0, g.step(z, 1.05, 1.3)))
    muzzle = g.math("MULTIPLY", g.math("SUBTRACT", 1.0, g.step(y, -3.1, -2.95)), g.math("SUBTRACT", 1.0, g.step(z, 1.5, 1.62)))
    blaze = g.math("MULTIPLY", g.math("SUBTRACT", 1.0, g.step(ax, 0.05, 0.09)), g.math("MULTIPLY", g.math("SUBTRACT", 1.0, g.step(y, -2.2, -2.05)), g.step(z, 1.6, 1.7)))
    tip = g.step(y, 2.3, 2.4)
    white = g.math("MAXIMUM", g.math("MAXIMUM", g.math("MAXIMUM", legs, chest), g.math("MAXIMUM", muzzle, blaze)), tip)
    # the black saddle: the top of the back between the shoulders and the hips
    sad = g.math("MULTIPLY", g.step(z, 1.28, 1.45), g.math("MULTIPLY", g.step(y, -1.15, -0.9), g.math("SUBTRACT", 1.0, g.step(y, 1.5, 1.75))))
    sad = g.math("MULTIPLY", sad, g.math("SUBTRACT", 1.0, white))
    fur = g.noise(60.0, 6, stretch=(1.0, 0.18, 1.0))               # hairs lying back along the body
    tan = g.mix(fur, (0.42, 0.2, 0.07), (0.58, 0.3, 0.11))
    blk = g.mix(fur, (0.02, 0.017, 0.015), (0.06, 0.05, 0.045))
    wht = g.mix(fur, (0.82, 0.78, 0.7), (0.95, 0.92, 0.85))
    col = g.mix(sad, tan, blk)
    col = g.mix(white, col, wht)
    g.L(col, bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.7
    bs.inputs["Sheen Weight"].default_value = 0.35
    g.L(g.bump(g.noise(90.0, 4, stretch=(1.0, 0.15, 1.0)), 0.25, 0.01), bs.inputs["Normal"])
    return m


def goose_plumage():
    """Canada goose: a black neck and head, the white chinstrap, a beige breast, a brown back barred pale, a black tail, a
    white rump; feather relief (overlapping scales)"""
    m, bs = _new_mat("GoosePlumage")
    g = NT(m)
    ax = g.math("ABSOLUTE", g.x)
    neck = g.step(g.z, 1.95, 2.15)
    chin = g.math("MULTIPLY", g.math("MULTIPLY", g.step(g.z, 3.62, 3.68), g.math("SUBTRACT", 1.0, g.step(g.z, 3.98, 4.04))),
                  g.math("MULTIPLY", g.step(g.y, -1.82, -1.74), g.math("SUBTRACT", 1.0, g.step(g.y, -1.42, -1.34))))
    chin = g.math("MULTIPLY", chin, g.step(ax, 0.06, 0.12))
    back = g.step(g.z, 1.65, 1.95)                                   # the top of the body (wings and back)
    tail = g.step(g.y, 1.25, 1.4)
    rump = g.math("MULTIPLY", g.step(g.y, 0.85, 1.05), g.math("SUBTRACT", 1.0, g.step(g.z, 1.25, 1.45)))
    bars_n = g.N.new("ShaderNodeTexWave")
    bars_n.wave_type = "BANDS"
    bars_n.bands_direction = "Y"
    bars_n.inputs["Scale"].default_value = 4.0
    bars_n.inputs["Distortion"].default_value = 2.0
    g.L(g.obj, bars_n.inputs["Vector"])
    bars = g.step(bars_n.outputs["Fac"], 0.7, 0.85)
    vor = g.N.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = 9.0
    mp = g.N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.4, 0.7, 1.0)
    g.L(g.obj, mp.inputs["Vector"])
    g.L(mp.outputs["Vector"], vor.inputs["Vector"])
    feath = g.step(vor.outputs["Distance"], 0.0, 0.12)
    breast = g.mix(feath, (0.42, 0.36, 0.28), (0.62, 0.55, 0.44))
    brown = g.mix(bars, g.mix(feath, (0.2, 0.15, 0.1), (0.32, 0.25, 0.17)), (0.62, 0.55, 0.45))
    col = g.mix(back, breast, brown)
    col = g.mix(rump, col, (0.9, 0.88, 0.84))
    col = g.mix(tail, col, (0.03, 0.03, 0.03))
    col = g.mix(neck, col, (0.025, 0.025, 0.028))
    col = g.mix(chin, col, (0.93, 0.92, 0.9))
    g.L(col, bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.6
    bs.inputs["Sheen Weight"].default_value = 0.2
    g.L(g.bump(feath, 0.35, 0.02), bs.inputs["Normal"])
    return m


def goose_wing():
    """the folded wing: brown feathers edged pale, barred across, the primaries near black toward the tip"""
    m = bpy.data.materials.get("GooseWing")
    if m:
        return m
    m, bs = _new_mat("GooseWing")
    g = NT(m)
    vor = g.N.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = 6.0
    mp = g.N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 0.45, 1.6)
    g.L(g.obj, mp.inputs["Vector"])
    g.L(mp.outputs["Vector"], vor.inputs["Vector"])
    edge = g.math("SUBTRACT", 1.0, g.step(vor.outputs["Distance"], 0.0, 0.07))
    base = g.mix(g.noise(20.0, 3), (0.2, 0.15, 0.1), (0.3, 0.23, 0.15))
    col = g.mix(edge, base, (0.66, 0.58, 0.47))
    tip = g.step(g.y, 0.9, 1.4)
    col = g.mix(tip, col, (0.06, 0.05, 0.045))
    g.L(col, bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.55
    bs.inputs["Sheen Weight"].default_value = 0.2
    g.L(g.bump(g.step(vor.outputs["Distance"], 0.0, 0.1), 0.4, 0.02), bs.inputs["Normal"])
    return m


def eye_mat(iris=(0.08, 0.05, 0.03)):
    return material("EyeGloss" + str(iris), base=iris, rough=0.05, wear=0.0, dirt=0.0)


# ------------------------------------------------------------------ soft sheets (the ears, the wings)

def sheet(name, pts_fn, nu, nv, thick, mat):
    """a sheet from a function (u, v) -> point, thickened, smooth"""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vs = [[bm.verts.new(tuple(pts_fn(i / nu, j / nv))) for j in range(nv + 1)] for i in range(nu + 1)]
    for i in range(nu):
        for j in range(nv):
            f = bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
            f.smooth = True
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    so = ob.modifiers.new("Thick", "SOLIDIFY")
    so.thickness = thick
    so.offset = 0.0
    sd = ob.modifiers.new("Sub", "SUBSURF")
    sd.levels = 1
    sd.render_levels = 1
    return _finish(ob, mat, 0)


# ================================================================== Biscuit

def biscuit(M):
    coat = basset_coat()
    set_group("Main")
    S = Skel()
    V = Vector
    pelvis = V((0, 1.4, 1.25))
    root = S.add(pelvis, 0.55)
    spine = chain(S, [V((0, 0.6, 1.22)), V((0, -0.3, 1.2)), V((0, -1.1, 1.18))], [0.6, 0.66, 0.7], root)
    keel = chain(S, [V((0, -1.0, 0.72)), V((0, -0.55, 0.58)), V((0, 0.1, 0.66))], [0.58, 0.5, 0.42], spine[2])
    neck = chain(S, [V((0, -1.62, 1.36)), V((0, -1.95, 1.56))], [0.5, 0.43], spine[2])
    head = chain(S, [V((0, -2.22, 1.74)), V((0, -2.6, 1.68)), V((0, -3.0, 1.54)), V((0, -3.38, 1.46)), V((0, -3.62, 1.42))], [0.44, 0.38, 0.33, 0.3, 0.26], neck[1])
    chain(S, [V((0, -2.08, 1.14)), V((0, -1.75, 1.0))], [0.3, 0.22], neck[1])                        # the dewlap
    for sx in (-1, 1):
        chain(S, [V((sx * 0.21, -2.95, 1.26)), V((sx * 0.2, -3.25, 1.18)), V((sx * 0.17, -3.48, 1.2))], [0.22, 0.2, 0.15], head[2])   # the flews (jowls)
        chain(S, [V((sx * 0.3, -2.3, 1.55))], [0.22], head[0])                                          # loose cheek skin
        chain(S, [V((sx * 0.15, -2.42, 1.95))], [0.15], head[0])                                        # wrinkled brow
        chain(S, [V((sx * 0.5, -1.2, 1.2)), V((sx * 0.55, -0.9, 0.95))], [0.36, 0.32], spine[2])        # shoulder
        chain(S, [V((sx * 0.45, 1.5, 1.15)), V((sx * 0.55, 1.25, 0.82))], [0.42, 0.36], root)           # haunch
    legs = {}
    for side, sx in (("L", 1), ("R", -1)):
        f = [V((sx * 0.5, -1.15, 0.85)), V((sx * 0.52, -1.2, 0.52)), V((sx * 0.44, -1.33, 0.26)), V((sx * 0.58, -1.58, 0.13))]
        legs[f"F{side}"] = (f, chain(S, f, [0.3, 0.22, 0.17, 0.2], spine[2]))
        h = [V((sx * 0.5, 1.35, 0.9)), V((sx * 0.52, 1.12, 0.55)), V((sx * 0.46, 1.55, 0.28)), V((sx * 0.46, 1.4, 0.13))]
        legs[f"H{side}"] = (h, chain(S, h, [0.36, 0.24, 0.15, 0.19], root))
    tail = [V((0, 1.9, 1.48)), V((0, 2.22, 1.82)), V((0, 2.42, 2.16)), V((0, 2.52, 2.42))]
    chain(S, tail, [0.14, 0.11, 0.08, 0.05], root)
    S.build("Body", coat, subdiv=2, knobs=0.015)
    # the nose, the eyes (dark, glossy, red haw below), the paws' black pads
    sphere("Nose", 0.16, (0, -3.76, 1.55), material("NoseBlack", base=(0.02, 0.02, 0.02), rough=0.25, wear=0.0), seg=16, rings=10, scale=(1.3, 0.8, 0.85))
    for sx in (-1, 1):
        sphere(f"Eye{sx}", 0.085, (sx * 0.27, -2.66, 1.74), eye_mat(), seg=14, rings=10)
        sphere(f"Haw{sx}", 0.08, (sx * 0.27, -2.66, 1.67), material("Haw", base=(0.55, 0.12, 0.1), rough=0.3, wear=0.0), seg=12, rings=8, scale=(1.1, 0.8, 0.45))
    # the collar and its tag
    na, nb = V((0, -1.62, 1.36)), V((0, -1.95, 1.56))
    ax = (nb - na).normalized()
    u_ = ax.cross(V((1, 0, 0))).normalized()
    v_ = ax.cross(u_).normalized()
    cc = na.lerp(nb, 0.45)
    ring = [cc + (u_ * math.cos(a) + v_ * math.sin(a)) * 0.5 for a in (2 * math.pi * i / 32 for i in range(33))]
    from nh_props import tube
    tube("Collar", ring, 0.06, material("CollarRed", base=(0.55, 0.05, 0.04), rough=0.45, wear=0.3), square=True)
    low = min(ring, key=lambda p: p.z)
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.11, depth=0.03, location=(low.x, low.y - 0.05, low.z - 0.12), rotation=(math.pi / 2, 0, 0))
    _finish(bpy.context.active_object, M["brass"], 0)
    # the ears: big soft sheets from the top of the skull, hanging nearly to the ground (their own piece)
    set_group("Ears")
    for sx in (-1, 1):
        def ear(u, v, sx=sx):
            w = 0.18 + 0.42 * math.sin(math.pi * min(1.0, 0.12 + 0.95 * v)) ** 0.8     # narrow at the root, broad, round at the tip
            y = -2.28 + (u - 0.5) * w - 0.1 * v
            out = 0.42 + 0.1 * math.sin(math.pi * v * 0.8)
            x = sx * out
            z = 1.98 - 1.32 * v - 0.12 * (1 - math.sin(math.pi * u)) * v ** 2           # the rounded bottom edge
            curl = 0.09 * math.sin(math.pi * u) * math.sin(math.pi * min(1.0, v * 1.2))  # the ear cups round the cheek
            return Vector((x - sx * curl, y, z))
        sheet(f"Ear{sx}", ear, 8, 14, 0.05, coat)
    # eyelids (closed when asleep: the rig opens them)
    set_group("Lids")
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=18, ring_count=10, radius=0.1, location=(0, 0, 0))
        lid = bpy.context.active_object
        lid.name = f"Lid{sx}"
        bm = bmesh.new()
        bm.from_mesh(lid.data)
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(0, 0, -1), clear_outer=True)
        bm.to_mesh(lid.data)
        bm.free()
        from mathutils import Matrix as _M
        lid.matrix_world = _M.Translation((sx * 0.27, -2.66, 1.74)) @ _M.Rotation(math.radians(95), 4, "X")
        so = lid.modifiers.new("Thick", "SOLIDIFY")
        so.thickness = 0.015
        _finish(lid, coat, 0)
    set_group("Main")
    # the joints
    J = {}
    J["Pelvis"] = (tuple(pelvis), (0, 0.6, 1.22), None)
    J["Spine"] = ((0, 0.6, 1.22), (0, -0.3, 1.2), "Pelvis")
    J["Chest"] = ((0, -0.3, 1.2), (0, -1.1, 1.18), "Spine")
    J["Neck"] = ((0, -1.1, 1.18), (0, -1.95, 1.56), "Chest")
    J["Head"] = ((0, -1.95, 1.56), (0, -3.0, 1.54), "Neck")
    J["Muzzle"] = ((0, -2.8, 1.55), (0, -3.7, 1.42), "Head")
    for side in "LR":
        f, _ = legs[f"F{side}"]
        J[f"F{side}Upper"] = (tuple(f[0]), tuple(f[1]), "Chest")
        J[f"F{side}Lower"] = (tuple(f[1]), tuple(f[2]), f"F{side}Upper")
        J[f"F{side}Paw"] = (tuple(f[2]), tuple(f[3]), f"F{side}Lower")
        h, _ = legs[f"H{side}"]
        J[f"H{side}Upper"] = (tuple(h[0]), tuple(h[1]), "Pelvis")
        J[f"H{side}Lower"] = (tuple(h[1]), tuple(h[2]), f"H{side}Upper")
        J[f"H{side}Paw"] = (tuple(h[2]), tuple(h[3]), f"H{side}Lower")
    J["Tail1"] = (tuple(tail[0]), tuple(tail[1]), "Pelvis")
    J["Tail2"] = (tuple(tail[1]), tuple(tail[3]), "Tail1")
    for side, sx in (("L", 1), ("R", -1)):
        J[f"Ear{side}1"] = ((sx * 0.4, -2.28, 1.98), (sx * 0.5, -2.33, 1.3), "Head")
        J[f"Ear{side}2"] = ((sx * 0.5, -2.33, 1.3), (sx * 0.44, -2.4, 0.62), f"Ear{side}1")
        J[f"Lid{side}"] = ((sx * 0.27, -2.61, 1.74), (sx * 0.27, -2.81, 1.74), "Head")
    body_bones = ["Pelvis", "Spine", "Chest", "Neck", "Head", "Muzzle", "Tail1", "Tail2"] + [f"{a}{s}{b}" for a in "FH" for s in "LR" for b in ("Upper", "Lower", "Paw")]
    RIG["Biscuit"] = dict(bones=J, own={"Main": body_bones, "Ears": ["EarL1", "EarL2", "EarR1", "EarR2"], "Lids": ["LidL", "LidR"]})
    return _dims()


# ---- Biscuit's clips (world terms: rotations about each bone's head; x = pitch (+ nose down), z = turn)
def _s(t, period, phase=0.0):
    return math.sin(2 * math.pi * t / period - phase)


def _b_breath(t, period=3.2, amp=1.0):
    return amp * (0.5 + 0.5 * _s(t, period))


def _lid(t, opened):
    """lids: 0 closed (rest), rotate up to open"""
    return ("x", -70 * opened, (0, 0, 0))


BISCUIT_CLIPS = {
    # asleep, chin on paws: the ribs rise and fall, an ear twitches once, the tail tip flicks
    "Sleep": dict(length=6.4, loop=True, keys={
        "Pelvis": lambda t: ("x", 0, (0, 0, -0.02 * _b_breath(t))),
        "Chest": lambda t: ("x", -1.2 * _b_breath(t), (0, 0, 0.03 * _b_breath(t))),
        "Neck": lambda t: ("x", 16, (0, 0, -0.22)),
        "Head": lambda t: ("x", 14 + 1.0 * _b_breath(t), (0, 0, 0)),
        "EarL1": lambda t: ("y", 12 * math.exp(-((t - 3.1) / 0.12) ** 2), (0, 0, 0)),
        "Tail2": lambda t: ("z", 10 * math.exp(-((t - 4.8) / 0.15) ** 2), (0, 0, 0))}),
    # one eye opens, the head lifts off the paws, a long dead-eyed stare at you
    "WakeStare": dict(length=3.6, keys={
        "Neck": lambda t: ("x", 16 * (1 - ease((t - 0.8) / 0.9)) - 3 * ease((t - 1.7) / 0.4), (0, 0, -0.22 * (1 - ease((t - 0.8) / 0.9)))),
        "Head": lambda t: ("x", 14 * (1 - back_out((t - 0.9) / 0.8, 0.8)), (0, 0, 0)),
        "LidR": lambda t: _lid(t, ease((t - 0.2) / 0.4) * 0.55),
        "LidL": lambda t: _lid(t, ease((t - 1.4) / 0.6) * 0.45),
        "EarL1": lambda t: ("y", -6 * back_out((t - 0.9) / 0.6), (0, 0, 0)),
        "EarR1": lambda t: ("y", 6 * back_out((t - 0.95) / 0.6), (0, 0, 0))}),
    # the sigh: a big inhale (chest up, head up), then everything collapses slowly back down
    "Sigh": dict(length=3.2, keys={
        "Chest": lambda t: ("x", -5 * math.sin(math.pi * min(1, t / 1.4)) * (1 if t < 1.4 else 0) - 5 * (1 - ease((t - 1.4) / 1.2)) * (t >= 1.4), (0, 0, 0.12 * math.sin(math.pi * min(1, t / 1.4)))),
        "Neck": lambda t: ("x", -6 * math.sin(math.pi * min(1, t / 1.4)) + 16 * ease((t - 1.5) / 1.5), (0, 0, -0.22 * ease((t - 1.5) / 1.5))),
        "Head": lambda t: ("x", 14 * back_out((t - 1.7) / 1.3, 0.4), (0, 0, 0)),
        "LidL": lambda t: _lid(t, 0.45 * (1 - ease((t - 1.8) / 0.8))),
        "LidR": lambda t: _lid(t, 0.55 * (1 - ease((t - 1.9) / 0.8))),
        "EarL1": lambda t: ("y", 4 * math.sin(math.pi * min(1, t / 1.4)), (0, 0, 0)),
        "EarR1": lambda t: ("y", -4 * math.sin(math.pi * min(1, t / 1.4)), (0, 0, 0))}),
    # one bored "wuff": a little wind-up, the head pops, the ears flap after it, settle
    "Wuff": dict(length=1.4, keys={
        "Chest": lambda t: ("x", 3 * math.exp(-((t - 0.25) / 0.12) ** 2) - 4 * math.exp(-((t - 0.45) / 0.08) ** 2), (0, 0, 0)),
        "Neck": lambda t: ("x", 6 * math.exp(-((t - 0.25) / 0.12) ** 2) - 12 * math.exp(-((t - 0.45) / 0.07) ** 2), (0, 0, 0)),
        "Head": lambda t: ("x", -10 * math.exp(-((t - 0.47) / 0.07) ** 2), (0, 0, 0)),
        "Muzzle": lambda t: ("x", 12 * math.exp(-((t - 0.47) / 0.06) ** 2), (0, 0, 0)),
        "EarL1": lambda t: ("y", 14 * math.exp(-((t - 0.55) / 0.1) ** 2) * math.cos((t - 0.55) * 18), (0, 0, 0)),
        "EarR1": lambda t: ("y", -14 * math.exp(-((t - 0.57) / 0.1) ** 2) * math.cos((t - 0.57) * 18), (0, 0, 0)),
        "LidL": lambda t: _lid(t, 0.5), "LidR": lambda t: _lid(t, 0.5)}),
    # the trot: short legs paddling, the long body rolling, the ears swinging a beat late; loops
    "Trot": dict(length=0.8, loop=True, keys={
        **{f"F{s}Upper": (lambda t, ph=(0 if s == "L" else math.pi): ("x", 28 * math.sin(2 * math.pi * t / 0.8 + ph), (0, 0, 0))) for s in "LR"},
        **{f"F{s}Lower": (lambda t, ph=(0 if s == "L" else math.pi): ("x", 18 * max(0.0, math.sin(2 * math.pi * t / 0.8 + ph + 0.8)), (0, 0, 0))) for s in "LR"},
        **{f"H{s}Upper": (lambda t, ph=(math.pi if s == "L" else 0): ("x", -26 * math.sin(2 * math.pi * t / 0.8 + ph), (0, 0, 0))) for s in "LR"},
        **{f"H{s}Lower": (lambda t, ph=(math.pi if s == "L" else 0): ("x", -20 * max(0.0, math.sin(2 * math.pi * t / 0.8 + ph + 0.8)), (0, 0, 0))) for s in "LR"},
        "Pelvis": lambda t: ([("y", 4 * _s(t, 0.8)), ("z", 3 * _s(t, 0.8, 0.5))], (0, 0, 0.05 * abs(_s(t, 0.4)))),
        "Head": lambda t: ("x", 3 * _s(t, 0.4, 0.6), (0, 0, 0)),
        "EarL1": lambda t: ("y", 14 * _s(t, 0.8, 1.4), (0, 0, 0)), "EarR1": lambda t: ("y", 14 * _s(t, 0.8, 1.4), (0, 0, 0)),
        "EarL2": lambda t: ("y", 10 * _s(t, 0.8, 2.2), (0, 0, 0)), "EarR2": lambda t: ("y", 10 * _s(t, 0.8, 2.2), (0, 0, 0)),
        "Tail2": lambda t: ("z", 18 * _s(t, 0.4), (0, 0, 0)),
        "LidL": lambda t: _lid(t, 0.6), "LidR": lambda t: _lid(t, 0.6)}),
}


# ================================================================== the Goose

def goose(M):
    plume = goose_plumage()
    black = material("GooseBlack", base=(0.025, 0.025, 0.028), rough=0.35, wear=0.1)
    start_ = len(P.PARTS)
    set_group("Main")
    S = Skel()
    V = Vector
    pelvis = V((0, 0.75, 1.6))
    root = S.add(pelvis, 0.68)
    body = chain(S, [V((0, 0.1, 1.72)), V((0, -0.55, 1.78)), V((0, -0.98, 1.98))], [0.9, 0.84, 0.58], root)
    neck = chain(S, [V((0, -1.18, 2.45)), V((0, -1.2, 3.0)), V((0, -1.14, 3.55)), V((0, -1.3, 4.02))], [0.32, 0.23, 0.2, 0.19], body[2])
    head = chain(S, [V((0, -1.55, 4.18)), V((0, -1.82, 4.14))], [0.22, 0.16], neck[3])
    tail = chain(S, [V((0, 1.35, 1.85)), V((0, 1.8, 2.12))], [0.32, 0.16], root)
    chain(S, [V((0, 0.95, 1.3))], [0.42], root)                    # the undertail
    S.build("Body", plume, subdiv=2, knobs=0.012)
    # the bill: upper fixed with the head, the lower its own piece (it gapes)
    B = Skel()
    b0 = B.add(V((0, -1.92, 4.18)), 0.1)
    chain(B, [V((0, -2.12, 4.14)), V((0, -2.32, 4.1))], [0.08, 0.05], b0)
    B.build("BillUpper", black, subdiv=2, knobs=0.0)
    set_group("Jaw")
    Bl = Skel()
    l0 = Bl.add(V((0, -1.9, 4.08)), 0.07)
    chain(Bl, [V((0, -2.1, 4.04)), V((0, -2.28, 4.02))], [0.055, 0.035], l0)
    Bl.build("BillLower", black, subdiv=2, knobs=0.0)
    set_group("Main")
    for sx in (-1, 1):
        sphere(f"Eye{sx}", 0.05, (sx * 0.15, -1.68, 4.27), eye_mat((0.03, 0.02, 0.02)), seg=12, rings=8)
    # legs and webbed feet (black)
    legs = {}
    for side, sx in (("L", 1), ("R", -1)):
        L_ = Skel()
        k0 = L_.add(V((sx * 0.32, 0.25, 1.15)), 0.12)
        pts = [V((sx * 0.33, 0.12, 0.62)), V((sx * 0.33, 0.05, 0.14))]
        chain(L_, pts, [0.075, 0.06], k0)
        L_.build(f"Leg{side}", black, subdiv=2, knobs=0.0)
        web = [(sx * 0.33 + 0.0, 0.12), (sx * 0.33 + 0.28, -0.36), (sx * 0.33 + 0.08, -0.5), (sx * 0.33, -0.56), (sx * 0.33 - 0.08, -0.5), (sx * 0.33 - 0.28, -0.36)]
        me = bpy.data.meshes.new(f"Web{side}")
        bm = bmesh.new()
        vs = [bm.verts.new((x, y, 0.06)) for x, y in web] + [bm.verts.new((x, y, 0.0)) for x, y in web]
        n = len(web)
        bm.faces.new(vs[:n])
        bm.faces.new(list(reversed(vs[n:])))
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((vs[i], vs[j], vs[n + j], vs[n + i]))
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(f"Web{side}", me)
        bpy.context.collection.objects.link(ob)
        _finish(ob, black, 0)
        legs[side] = (V((sx * 0.32, 0.25, 1.15)), pts)
    # the folded wings: long feathered sheets along the body's sides, primaries crossing over the tail (their own pieces)
    set_group("Wings")
    for sx in (-1, 1):
        def wing(u, v, sx=sx):
            y = -0.85 + 2.6 * u
            z = 2.25 - 0.4 * u - 0.55 * v + 0.15 * math.sin(math.pi * u)
            x = sx * (0.78 - 0.25 * u * u + 0.12 * math.sin(math.pi * v)) * (1 - 0.15 * v)
            return Vector((x, y, z))
        sheet(f"Wing{sx}", wing, 14, 5, 0.07, goose_wing())
    set_group("Main")
    J = {}
    J["Pelvis"] = (tuple(pelvis), (0, 0.1, 1.72), None)
    J["Body"] = ((0, 0.1, 1.72), (0, -0.98, 1.98), "Pelvis")
    J["Neck1"] = ((0, -0.98, 1.98), (0, -1.2, 3.0), "Body")
    J["Neck2"] = ((0, -1.2, 3.0), (0, -1.14, 3.55), "Neck1")
    J["Neck3"] = ((0, -1.14, 3.55), (0, -1.3, 4.02), "Neck2")
    J["Head"] = ((0, -1.3, 4.02), (0, -2.3, 4.1), "Neck3")
    J["Jaw"] = ((0, -1.9, 4.08), (0, -2.28, 4.02), "Head")
    J["Tail"] = ((0, 1.35, 1.85), (0, 1.8, 2.12), "Pelvis")
    for side, sx in (("L", 1), ("R", -1)):
        hip, (knee, foot) = legs[side]
        J[f"Leg{side}"] = (tuple(hip), tuple(knee), "Pelvis")
        J[f"Shin{side}"] = (tuple(knee), tuple(foot), f"Leg{side}")
        J[f"Foot{side}"] = (tuple(foot), (sx * 0.33, -0.45, 0.04), f"Shin{side}")
        J[f"Wing{side}1"] = ((sx * 0.72, -0.85, 2.25), (sx * 0.72, -0.05, 2.05), "Body")
        J[f"Wing{side}2"] = ((sx * 0.72, -0.05, 2.05), (sx * 0.62, 0.85, 1.92), f"Wing{side}1")
        J[f"Wing{side}3"] = ((sx * 0.62, 0.85, 1.92), (sx * 0.5, 1.75, 1.85), f"Wing{side}2")
    def low(z, leg=False):
        if leg:
            return 0.14 + (z - 0.14) * 0.70 if z < 1.2 else z - 0.3
        return z - 0.3 if z > 0.7 else z
    for ob in P.PARTS[start_:]:
        if ob.name.startswith("Web"):
            continue
        if ob.name.startswith("Leg"):
            for v in ob.data.vertices:
                v.co.z = low(v.co.z, leg=True)
        else:
            ob.location.z -= 0.3
    for k_, (h_, t_, par_) in list(J.items()):
        leg = k_.startswith(("Leg", "Shin", "Foot"))
        J[k_] = ((h_[0], h_[1], low(h_[2], leg)), (t_[0], t_[1], low(t_[2], leg)), par_)
    body_b = ["Pelvis", "Body", "Neck1", "Neck2", "Neck3", "Head", "Tail", "LegL", "ShinL", "FootL", "LegR", "ShinR", "FootR"]
    RIG["Goose"] = dict(bones=J, own={"Main": body_b, "Jaw": "Jaw", "Wings": [f"Wing{s}{k}" for s in "LR" for k in (1, 2, 3)]})
    return _dims()


def _wing(side_sign, spread, flap=0.0):
    """wing bones: spread 0 folded .. 1 fully open (out and up), flap adds a downstroke"""
    a = spread * 100 + flap
    return [("y", side_sign * -a), ("x", -spread * 20)]


GOOSE_CLIPS = {
    "Idle": dict(length=4.0, loop=True, keys={
        "Neck1": lambda t: ("x", 2 * _s(t, 4.0), (0, 0, 0)),
        "Neck3": lambda t: ([("z", 18 * _s(t, 4.0, 0.8))], (0, 0, 0)),
        "Head": lambda t: ([("z", 25 * math.tanh(3 * _s(t, 2.0, 1.3)))], (0, 0, 0)),
        "Tail": lambda t: ("z", 10 * math.exp(-((t - 2.6) / 0.08) ** 2) * math.cos((t - 2.6) * 40), (0, 0, 0))}),
    # sees you: the neck snaps up tall and straight, the head cocks
    "Alert": dict(length=1.0, keys={
        "Neck1": lambda t: ("x", -14 * back_out(t / 0.35, 1.6), (0, 0, 0)),
        "Neck2": lambda t: ("x", -6 * back_out((t - 0.04) / 0.35, 1.6), (0, 0, 0)),
        "Head": lambda t: ([("x", 8 * back_out((t - 0.1) / 0.3)), ("y", 18 * ease((t - 0.45) / 0.2))], (0, 0, 0))}),
    # the threat: the neck coils low and forward, the wings half open, the bill gapes; a hiss you can see
    "Hiss": dict(length=1.6, keys={
        "Body": lambda t: ("x", 10 * ease(t / 0.4), (0, 0, 0)),
        "Neck1": lambda t: ("x", 48 * back_out(t / 0.45, 1.0), (0, 0, 0)),
        "Neck2": lambda t: ("x", -30 * back_out((t - 0.05) / 0.45, 1.0) + 2 * _s(t, 0.12) * (t > 0.5), (0, 0, 0)),
        "Neck3": lambda t: ("x", -12 * back_out((t - 0.1) / 0.45, 1.0), (0, 0, 0)),
        "Jaw": lambda t: ("x", 28 * ease((t - 0.35) / 0.15) + 3 * _s(t, 0.08) * (t > 0.5), (0, 0, 0)),
        "WingL1": lambda t: (_wing(1, 0.5 * back_out((t - 0.2) / 0.4)), (0, 0, 0)),
        "WingR1": lambda t: (_wing(-1, 0.5 * back_out((t - 0.2) / 0.4)), (0, 0, 0)),
        "Tail": lambda t: ("z", 12 * _s(t, 0.1) * (t > 0.5), (0, 0, 0))}),
    # the charge: head low and out, legs paddling fast, wings beating; loops
    "Charge": dict(length=0.5, loop=True, keys={
        "Body": lambda t: ([("x", 14), ("y", 6 * _s(t, 0.5))], (0, 0, 0.08 * abs(_s(t, 0.25)))),
        "Neck1": lambda t: ("x", 52, (0, 0, 0)), "Neck2": lambda t: ("x", -34, (0, 0, 0)), "Neck3": lambda t: ("x", -14 + 4 * _s(t, 0.25), (0, 0, 0)),
        "Jaw": lambda t: ("x", 20 + 6 * _s(t, 0.125), (0, 0, 0)),
        "LegL": lambda t: ("x", 32 * _s(t, 0.5), (0, 0, 0)), "LegR": lambda t: ("x", -32 * _s(t, 0.5), (0, 0, 0)),
        "ShinL": lambda t: ("x", -20 * max(0, _s(t, 0.5, 1.0)), (0, 0, 0)), "ShinR": lambda t: ("x", -20 * max(0, _s(t, 0.5, 1.0 + math.pi)), (0, 0, 0)),
        "WingL1": lambda t: (_wing(1, 0.85, 35 * _s(t, 0.25)), (0, 0, 0)), "WingR1": lambda t: (_wing(-1, 0.85, 35 * _s(t, 0.25)), (0, 0, 0)),
        "WingL2": lambda t: ("y", -20 * _s(t, 0.25, 0.7), (0, 0, 0)), "WingR2": lambda t: ("y", 20 * _s(t, 0.25, 0.7), (0, 0, 0))}),
    # HONK: crouch, the neck pumps forward, the bill snaps open, the head recoils
    "Honk": dict(length=1.0, keys={
        "Body": lambda t: ("x", 6 * math.exp(-((t - 0.2) / 0.1) ** 2) - 4 * math.exp(-((t - 0.4) / 0.08) ** 2), (0, 0, -0.06 * math.exp(-((t - 0.2) / 0.1) ** 2))),
        "Neck1": lambda t: ("x", 8 * math.exp(-((t - 0.2) / 0.1) ** 2) + 22 * math.exp(-((t - 0.42) / 0.09) ** 2), (0, 0, 0)),
        "Neck3": lambda t: ("x", -16 * math.exp(-((t - 0.44) / 0.09) ** 2), (0, 0, 0)),
        "Jaw": lambda t: ("x", 34 * math.exp(-((t - 0.44) / 0.07) ** 2), (0, 0, 0)),
        "Head": lambda t: ("x", -8 * math.exp(-((t - 0.5) / 0.1) ** 2), (0, 0, 0)),
        "Tail": lambda t: ("z", 15 * math.exp(-((t - 0.5) / 0.1) ** 2) * math.cos((t - 0.5) * 30), (0, 0, 0))}),
    # the victory waddle: a big side-to-side roll, chest out, head high and smug; loops
    "Strut": dict(length=1.0, loop=True, keys={
        "Pelvis": lambda t: ([("y", 10 * _s(t, 1.0)), ("z", 6 * _s(t, 1.0, 0.4))], (0, 0, 0.04 * abs(_s(t, 0.5)))),
        "Body": lambda t: ("x", -6, (0, 0, 0)),
        "Neck1": lambda t: ("x", -10, (0, 0, 0)),
        "Head": lambda t: ([("x", 6), ("z", 12 * _s(t, 1.0, 1.2))], (0, 0, 0)),
        "LegL": lambda t: ("x", 22 * _s(t, 1.0), (0, 0, 0)), "LegR": lambda t: ("x", -22 * _s(t, 1.0), (0, 0, 0)),
        "Tail": lambda t: ("z", 14 * _s(t, 0.5), (0, 0, 0)),
        "WingL1": lambda t: (_wing(1, 0.08 + 0.05 * _s(t, 0.5)), (0, 0, 0)), "WingR1": lambda t: (_wing(-1, 0.08 + 0.05 * _s(t, 0.5)), (0, 0, 0))}),
}

CLIPS["Biscuit"] = BISCUIT_CLIPS
CLIPS["Goose"] = GOOSE_CLIPS
BUILDERS.update({"Biscuit": biscuit, "Goose": goose})
P.BUILD.update(BUILDERS)
P.PREVIEW_PAD.update({"Biscuit": 1.2, "Goose": 1.2})
for _p in BUILDERS:
    P.RIGS[_p] = (lambda p: (lambda objs: rig_pieces(p, objs)))(_p)
B49.CLIP_CAM.update({
    "Biscuit": {c: ((2.4, -5.6, 2.1), (0, -2.2, 1.3)) for c in BISCUIT_CLIPS},
    "Goose": {c: ((4.4, -5.0, 3.0), (0, -0.6, 1.8)) for c in GOOSE_CLIPS},
})

if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = list(BUILDERS) if (not argv or argv[0] == "all") else [argv[0]]
    for n in names:
        P.run(n)
        clip_strips(n)
