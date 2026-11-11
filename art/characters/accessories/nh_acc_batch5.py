"""Accessories batch 5: magic (Kit A 21-24).

  RuneHalo        a thin ring of carved runes floating above the head, tipped back: blackened-iron rune segments with
                  the runes cut through onto a violet glowing core, silver rims, eight finialed clasps and a violet
                  gem at the front. Slot Halo, Head mount. Spins slowly in its own plane (extra.json orbit + bob)
  OrbitSigils     four glowing sigil plates (crescent, eye, key, mercury) in silver vesica frames, orbiting the head
                  at eye level, out past the shoulders. Slot Halo, Head mount (extra.json orbit + bob)
  CrowFamiliar    a crow perched on the left shoulder top, rigged for the idle controller (Root > H0 > Body; Head,
                  Tail, WingL, WingR; LidL / LidR on Head), violet familiar's eyes, a silver leg ring. Slot Familiar,
                  Torso mount (extra.json idle + bone ranges)
  CrystalPendant  a faceted amethyst in a silver cage on a fine chain round the neck, a faint violet core glow. Slot Neck
  PotionBelt      a high leather belt with five corked, faintly glowing vials in loops (front-right and back-right),
                  a stitched pouch with a crescent clasp and a silver buckle. Slot Belt

Space as nh_acc (studs, -Y front, +X the character's left). Head part centre (0, 0, 1.5).
Run: E:/Blender/blender.exe -b --factory-startup -P nh_acc.py -- RuneHalo,OrbitSigils,CrowFamiliar,CrystalPendant,PotionBelt
The game-side motion check (orbit at every angle and bob, the crow at its idle limits):
  E:/Blender/blender.exe -b --factory-startup -P nh_acc_batch5.py -- --motioncheck [--hats <root with batch 2 blends>]
"""
import math, random, os, json, sys
import bpy, bmesh
from mathutils import Vector, Matrix, Euler
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nh_acc as A
from nh_acc import item, piece, lerp, smooth
from nh_acc_batch1 import frame, offset_poly, ccw, bez, crescent, band_loop, project_out

VIOLET = (0.62, 0.30, 1.0)
HEAD_C = Vector((0, 0, 1.5))

# A toolkit gap this batch fills here (nh_acc is not edited): nh_acc.fit_table clamps a body's depth fit at 0.80, but
# the lean body's waist is only 0.355 deep (front and back at z -0.5), so a belt lying on the plain R6 waist would
# hover 0.045 off it. The game clamps NHFitBody at 0.75 (UI.AccessoryWear depthFor), so for the pieces named here the
# fit may go down to 0.75: the same measurement as fit_table, a lower floor.
LOW_FIT = {"PotionBelt"}
_fit_table_nh = A.fit_table


def _fit_table_b5(obj, mount):
    out = _fit_table_nh(obj, mount)
    if obj.name not in LOW_FIT or mount == "Head":
        return out
    c = A.MOUNT_CENTRE[mount]
    hw = 1.0 if mount == "Torso" else 0.5
    dg = bpy.context.evaluated_depsgraph_get()
    me = obj.evaluated_get(dg).to_mesh()
    pts = [obj.matrix_world @ v.co - c for v in me.vertices]
    obj.evaluated_get(dg).to_mesh_clear()
    contact = []
    for q in pts:
        if abs(q.x) > hw * 0.98 or abs(q.z) > 0.98 or abs(q.y) < 0.05:
            continue
        clear = abs(q.y) - 0.5
        if clear < 0.12:
            contact.append((q, -1 if q.y < 0 else 1, max(0.004, min(clear, 0.02))))
    random.seed(7)
    if len(contact) > 400:
        contact = random.sample(contact, 400)
    for bid, sv in list(out.items()):
        if sv > 0.8 + 1e-6:
            continue
        need = 0.0
        for q, side, cl in contact:
            d = A.body_depth(bid, mount, q.x, q.z, side)
            if d is not None:
                need = max(need, (d + cl) / abs(q.y))
        if need > 0:
            out[bid] = round(min(1.45, max(0.75, need)), 3)
    return out


A.fit_table = _fit_table_b5


def write_extra(key, data):
    with open(os.path.join(A.OUT, "layout", f"{key}.extra.json"), "w") as fh:
        json.dump(data, fh, indent=1)


def place_parts(n0, M):
    """move every part built since PARTS[n0] by M (they're built in a local frame)"""
    for ob in A.PARTS[n0:]:
        ob.matrix_world = M @ ob.matrix_world


def rot_x(a):
    return Matrix.Rotation(a, 4, "X")


# ================================================================== materials
def mat_feather(name, rgb=(0.016, 0.016, 0.022), sheen_tint=(0.32, 0.30, 0.75)):
    """crow plumage: overlapping feather scales (voronoi bump), fine barbs, a blue-violet sheen"""
    m, T, bs = A._base(name)
    vo = T.node("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 1.0
    T.L(T.coord((55.0, 38.0, 55.0)), vo.inputs["Vector"])
    wv = T.node("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X")
    wv.inputs["Scale"].default_value = 1.0; wv.inputs["Distortion"].default_value = 2.0
    T.L(T.coord(900.0), wv.inputs["Vector"])
    nz = T.node("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0; nz.inputs["Detail"].default_value = 6
    T.L(T.coord(30.0), nz.inputs["Vector"])
    edge = T.math("POWER", vo.outputs["Distance"], 0.7)
    h = T.math("ADD", edge, T.math("MULTIPLY", wv.outputs["Fac"], 0.25))
    col = T.mix(T.math("MULTIPLY", edge, 0.5), _rgb(T, rgb), tuple(c * 2.6 for c in rgb), "MIX")
    col = T.mix(0.06, col, nz.outputs["Color"], "OVERLAY")
    bp = T.node("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35; bp.inputs["Distance"].default_value = 0.004
    T.L(h, bp.inputs["Height"])
    bs.inputs["Sheen Weight"].default_value = 0.9
    bs.inputs["Sheen Roughness"].default_value = 0.35
    bs.inputs["Sheen Tint"].default_value = (*sheen_tint, 1)
    bs.inputs["Coat Weight"].default_value = 0.25
    r = T.math("ADD", 0.38, T.math("MULTIPLY", edge, 0.18))
    A._weather(T, bs, col, r, A._val(T, 0.0), bp.outputs["Normal"], 0.05, False, 0.5, 0.004)
    return m


def _rgb(T, c):
    return A._rgb(T, c)


def mat_glow_grad(name, centre, bright, dark, reach):
    """a glow material whose colour falls off from `centre` (bright) to `reach` studs away (dark): the emissive mask is
    white over the whole part, but the baked colour (what Roblox multiplies by EmissiveStrength) fades, so the core
    glows and the tips stay deep"""
    m, T, bs = A._base(name)
    tc = T.node("ShaderNodeTexCoord")
    vm = T.node("ShaderNodeVectorMath", operation="DISTANCE")
    T.L(tc.outputs["Object"], vm.inputs[0]); vm.inputs[1].default_value = tuple(centre)
    f = T.math("DIVIDE", vm.outputs["Value"], reach)
    f = T.math("POWER", T.math("MINIMUM", f, 1.0), 1.4)
    nz = T.node("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0; nz.inputs["Detail"].default_value = 4
    T.L(T.coord(60.0), nz.inputs["Vector"])
    col = T.mix(f, bright, dark, "MIX")
    col = T.mix(0.12, col, nz.outputs["Color"], "OVERLAY")
    T.L(col, bs.inputs["Base Color"]); T.L(col, bs.inputs["Emission Color"])
    bs.inputs["Emission Strength"].default_value = 4.0
    bs.inputs["Roughness"].default_value = 0.08
    bs.inputs["Coat Weight"].default_value = 1.0
    m["nh_glow"] = list(bright)
    return m


def fine_chain(name, points, pitch, mat, wire, major=6, minor=4, ratio=0.62):
    """a fine necklace chain: oval links along a poly line, each long along the chain and turned 90 degrees from the
    last, spaced by their inner length so they interlock"""
    pts = [Vector(p) for p in points]
    total = sum((b - a).length for a, b in zip(pts, pts[1:]))
    n = max(2, int(total / pitch) + 1)
    RL = pitch / 2 + 1.1 * wire          # wire-centre half length along the chain
    obs = []

    def at(d):
        for a, b in zip(pts, pts[1:]):
            L = (b - a).length
            if d <= L:
                return a + (b - a) * (d / max(L, 1e-9)), (b - a).normalized()
            d -= L
        return pts[-1], (pts[-1] - pts[-2]).normalized()
    s0 = None
    for k in range(n):
        p, t = at(k * total / (n - 1))
        side = t.cross(Vector((0, 0, 1)))
        if side.length < 1e-3:
            side = t.cross(Vector((1, 0, 0)))
        side.normalize()
        if s0 is not None and side.dot(s0) < 0:
            side = -side
        s0 = side.copy()
        S = side if k % 2 == 0 else t.cross(side).normalized()
        R = Matrix((S, t, S.cross(t))).transposed().to_4x4()
        bpy.ops.mesh.primitive_torus_add(major_radius=RL, minor_radius=wire, major_segments=major * 2, minor_segments=minor)
        ob = bpy.context.object
        ob.scale = (ratio, 1.0, 1.0)
        bpy.ops.object.transform_apply(scale=True)
        ob.matrix_world = Matrix.Translation(p) @ R
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        obs.append(ob)
    bpy.ops.object.select_all(action="DESELECT")
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.join()
    ob = bpy.context.object; ob.name = name
    for p in ob.data.polygons:
        p.use_smooth = True
    return A._finish(ob, mat)


def prisms(name, polys, z0, z1, mat, M=Matrix()):
    """many small flat outlines (x, y) raised from z0 to z1 in one mesh (rune strokes), placed by M"""
    verts, faces = [], []
    for poly in polys:
        n = len(poly)
        b = len(verts)
        verts += [M @ Vector((x, y, z0)) for x, y in poly] + [M @ Vector((x, y, z1)) for x, y in poly]
        faces.append(list(range(b + n - 1, b - 1, -1)))
        faces.append(list(range(b + n, b + 2 * n)))
        for i in range(n):
            j = (i + 1) % n
            faces.append([b + i, b + j, b + n + j, b + n + i])
    ob = A.mesh_from(name, verts, faces, mat, smooth_all=False)
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free()
    return ob


def loft(name, sections, mat, cap0=None, cap1=None, smooth_all=True):
    """a closed tube through rings of points (each ring the same count); cap0 / cap1 = an end point (or None: open)"""
    n = len(sections[0])
    verts, faces = [], []
    for ring in sections:
        verts += [Vector(p) for p in ring]
    for k in range(len(sections) - 1):
        for s in range(n):
            s2 = (s + 1) % n
            faces.append([k * n + s, k * n + s2, (k + 1) * n + s2, (k + 1) * n + s])
    if cap0 is not None:
        c = len(verts); verts.append(Vector(cap0))
        for s in range(n):
            faces.append([c, (s + 1) % n, s])
    if cap1 is not None:
        c = len(verts); verts.append(Vector(cap1))
        b = (len(sections) - 1) * n
        for s in range(n):
            faces.append([c, b + s, b + (s + 1) % n])
    ob = A.mesh_from(name, verts, faces, mat, smooth_all=smooth_all)
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data); bm.free()
    return ob


# ================================================================== 21a. the floating rune halo
HALO_R = 0.98
HALO_TILT = math.radians(15)          # tipped back: the front rises
HALO_Z = 2.55   # (coordinator review: 3.05 floated a stud and a half over most heads; the hair fit lifts it)
HALO_N = Vector((0, math.sin(HALO_TILT), math.cos(HALO_TILT)))
HALO_C = HEAD_C + HALO_N * ((HALO_Z - 1.5) / math.cos(HALO_TILT))   # on the spin axis through the head centre
HALO_M = Matrix.Translation(HALO_C) @ rot_x(-HALO_TILT)
FLAT = rot_x(math.radians(-90))       # extrude_poly's (x, z) outline -> the local ring plane (x, y), extruded up +Z

# rune designs in a unit cell (u along the ring, v outward), stencil strokes that never touch
RUNES = [
    [((-0.25, -0.45), (-0.25, 0.45)), ((-0.02, 0.05), (0.35, 0.42))],
    [((-0.32, -0.45), (-0.32, 0.45)), ((0.32, -0.45), (0.32, 0.45)), ((-0.10, 0.25), (0.10, -0.25))],
    [((-0.36, 0.45), (-0.02, -0.45)), ((0.14, -0.12), (0.36, 0.45))],
    [((0.0, -0.45), (0.0, 0.32)), ((-0.36, 0.45), (-0.16, 0.18)), ((0.16, 0.18), (0.36, 0.45))],
    [((-0.36, -0.45), (0.36, 0.45)), ((-0.36, 0.45), (-0.12, 0.15)), ((0.12, -0.15), (0.36, -0.45))],
    [((-0.30, -0.45), (-0.30, 0.45)), ((-0.08, 0.42), (0.32, 0.18)), ((-0.08, -0.02), (0.32, -0.26))],
    [((-0.12, 0.42), (-0.34, 0.08)), ((0.12, 0.42), (0.34, 0.08)), ((-0.34, -0.08), (-0.12, -0.42)), ((0.34, -0.08), (0.12, -0.42))],
    [((-0.22, -0.45), (-0.22, 0.45)), ((0.14, 0.12), (0.34, 0.12)), ((0.14, -0.12), (0.34, -0.12))],
    [((-0.34, -0.45), (-0.34, 0.20)), ((-0.12, 0.42), (0.34, 0.42)), ((0.34, 0.20), (0.34, -0.45))],
    [((0.0, -0.45), (0.0, 0.45)), ((-0.36, -0.10), (-0.16, 0.20)), ((0.16, 0.20), (0.36, -0.10))],
]


def rune_quads(theta, R, cw, ch, rune, sw):
    """the strokes of one rune centred at angle theta on radius R (cell cw along x ch radial, stroke width sw), as
    quads in the ring plane"""
    quads = []
    for (u0, v0), (u1, v1) in rune:
        p0 = Vector((u0 * cw, v0 * ch)); p1 = Vector((u1 * cw, v1 * ch))
        d = (p1 - p0).normalized(); nrm = Vector((-d.y, d.x)) * (sw / 2)
        q = []
        for c in (p0 - nrm - d * sw * 0.3, p1 - nrm + d * sw * 0.3, p1 + nrm + d * sw * 0.3, p0 + nrm - d * sw * 0.3):
            a = theta + c.x / R
            r = R + c.y
            q.append((r * math.cos(a), r * math.sin(a)))
        quads.append(ccw(q))
    return quads


@item("RuneHalo", "Floating rune halo", lens=40, focus=(0, 0, 1.0),
      close=((3.4, -6.4, 3.9), (0, 0.2, 2.6), 62))
def build_halo(M):
    A.MANNEQUIN_HAIR = {"male": "Males_Short", "female": "Females_Straight_Bob"}
    ink = A.mat_metal("HaloInkIron", (0.045, 0.040, 0.050), rough=0.45, scratch=0.6, wear=0.5, tarnish=(0.02, 0.018, 0.025))
    silver = M["silver"]
    glow = A.mat_glow("HaloRuneGlow", VIOLET)
    gem = A.mat_glow("HaloGem", (0.78, 0.42, 1.0))
    piece("RuneHalo", "Head")
    n0 = len(A.PARTS)
    R = HALO_R
    hw = 0.062          # half the band's width
    th = 0.024
    F = FLAT @ Matrix.Translation((0, th / 2, 0))
    rng = random.Random(21)
    nseg = 8
    front = math.radians(-90)
    glyphs = []
    for k in range(nseg):
        a0 = math.radians(22.5 + 45 * k) + 0.035
        a1 = math.radians(22.5 + 45 * (k + 1)) - 0.035
        ns = 14
        outer = [((R + hw) * math.cos(lerp(a0, a1, i / ns)), (R + hw) * math.sin(lerp(a0, a1, i / ns))) for i in range(ns + 1)]
        inner = [((R - hw) * math.cos(lerp(a1, a0, i / ns)), (R - hw) * math.sin(lerp(a1, a0, i / ns))) for i in range(ns + 1)]
        A.extrude_poly(f"HaloSeg{k}", ccw(outer + inner), th, ink, F, bevel=0.0)
        nr = 7
        for j in range(nr):
            a = lerp(a0 + 0.03, a1 - 0.03, (j + 0.5) / nr)
            if abs(math.atan2(math.sin(a - front), math.cos(a - front))) < 0.09:
                continue   # the gem sits here
            glyphs += rune_quads(a, R, 0.072, 0.080, RUNES[rng.randrange(len(RUNES))], 0.0135)
    prisms("HaloRunesTop", glyphs, th / 2 - 0.001, th / 2 + 0.0045, glow)
    prisms("HaloRunesBot", glyphs, -th / 2 - 0.0045, -th / 2 + 0.001, glow)
    for k, rr in enumerate((R + hw + 0.002, R - hw - 0.002)):
        A.torus(f"HaloRim{k}", rr, 0.0115, (0, 0, 0), silver, major=84, minor=6)
    # clasps between the segments: a silver block across the band, a pointed finial outward, a bead inward
    for k in range(nseg):
        a = math.radians(22.5 + 45 * k)
        ca, sa = math.cos(a), math.sin(a)
        blk = A.box(f"HaloClasp{k}", (0.16, 0.050, 0.040), (0, 0, 0), silver, bevel=0.010, segments=2)
        blk.matrix_world = Matrix.Translation((R * ca, R * sa, 0)) @ Matrix.Rotation(a, 4, "Z")
        A.sphere(f"HaloClaspBead{k}", 0.022, ((R + 0.088) * ca, (R + 0.088) * sa, 0), silver, seg=10, rings=6)
        A.cyl(f"HaloFinial{k}", 0.016, 0.075, (0, 0, 0), silver, verts=10, r2=0.0).matrix_world = \
            Matrix.Translation(((R + 0.139) * ca, (R + 0.139) * sa, 0)) @ Matrix.Rotation(a, 4, "Z") @ Matrix.Rotation(math.radians(90), 4, "Y")
        A.sphere(f"HaloInBead{k}", 0.016, ((R - 0.084) * ca, (R - 0.084) * sa, 0), silver, seg=10, rings=6)
    # the front gem: a violet cabochon in a silver quatrefoil setting
    fx, fy = R * math.cos(front), R * math.sin(front)
    A.sphere("HaloGemStone", 0.05, (fx, fy, 0), gem, scale=(1.0, 1.0, 0.62), seg=18, rings=10)
    A.torus("HaloGemBezel", 0.052, 0.010, (fx, fy, 0), silver, major=24, minor=6)
    for q in range(4):
        b = math.pi / 4 + q * math.pi / 2
        A.sphere(f"HaloGemLobe{q}", 0.026, (fx + 0.064 * math.cos(b), fy + 0.064 * math.sin(b), 0), silver,
                 scale=(1, 1, 0.75), seg=10, rings=6)
    place_parts(n0, HALO_M)
    write_extra("RuneHalo", {"RuneHalo": {"orbit": {"axis": [round(x, 4) for x in A.to_rbx(HALO_N)], "rpm": 2},
                                          "bob": 0.03}})
    return dict(notes="a ring of blackened iron segments carved with raised violet glowing runes on both faces; silver "
                      "rims, eight finialed clasps and a violet gem at the front; floats above the head tipped back and "
                      "spins slowly in its own plane (orbit axis = the ring's axis through the head centre)",
                glow=list(VIOLET))


# ================================================================== 21b. orbiting sigils
ORBIT_R = 1.75
ORBIT_Z = 1.5            # the head centre's height: the orbit plane passes through the mount centre
ORBIT_BOB = 0.05


def vesica(w, h, n=11):
    """a pointed oval (two arcs), width w, height h, centred"""
    # arcs through the top / bottom points and the side points
    a, b = w / 2, h / 2
    rr = (a * a + b * b) / (2 * a)       # radius of each side arc (centre on the x axis)
    cx = rr - a
    ang = math.atan2(b, rr - a) if rr - a != 0 else math.pi / 2
    pts = []
    for i in range(n + 1):                # right arc, centre (-cx, 0), from the bottom point to the top point
        t = lerp(-ang, ang, i / n)
        pts.append((-cx + rr * math.cos(t), rr * math.sin(t)))
    for i in range(1, n):                 # left arc, centre (cx, 0)
        t = lerp(math.pi - ang, math.pi + ang, i / n)
        pts.append((cx + rr * math.cos(t), rr * math.sin(t)))
    return ccw(pts)


def sigil_shapes(kind):
    """the glowing sigil: a list of (outline, holes) in the plate's (x, z) plane, about 0.13 across"""
    out = []
    if kind == "moon":
        out.append((crescent(0.0, 0.0, 0.062, 0.03, 0.016, 0.052), []))
        star = []
        for i in range(10):
            a = math.pi / 2 + 2 * math.pi * i / 10
            r = 0.026 if i % 2 == 0 else 0.010
            star.append((0.030 + r * math.cos(a), 0.012 + r * math.sin(a)))
        out.append((ccw(star), []))
    elif kind == "eye":
        eye = ccw(bez((-0.07, 0), (-0.035, 0.045), (0.035, 0.045), (0.07, 0), 10) +
                  bez((0.07, 0), (0.035, -0.045), (-0.035, -0.045), (-0.07, 0), 10))
        out.append((eye, [ccw(offset_poly(eye, 0.010))[::-1]]))
        out.append((A.circle_pts(0, 0, 0.021, 16), []))
        for k in range(5):   # lashes / rays above
            a = math.radians(50 + 20 * k)
            c, s = math.cos(a), math.sin(a)
            p0, p1 = Vector((0.050 * c, 0.040 + 0.030 * s)), Vector((0.075 * c, 0.040 + 0.055 * s))
            d = (p1 - p0).normalized(); nn = Vector((-d.y, d.x)) * 0.0045
            out.append((ccw([tuple(p0 - nn), tuple(p1 - nn), tuple(p1 + nn), tuple(p0 + nn)]), []))
    elif kind == "key":
        out.append((A.circle_pts(0, 0.052, 0.030, 18), [A.circle_pts(0, 0.052, 0.015, 14)[::-1]]))
        out.append((ccw([(-0.008, 0.023), (0.008, 0.023), (0.008, -0.072), (-0.008, -0.072)]), []))
        out.append((ccw([(0.008, -0.040), (0.036, -0.040), (0.036, -0.050), (0.008, -0.050)]), []))
        out.append((ccw([(0.008, -0.060), (0.030, -0.060), (0.030, -0.070), (0.008, -0.070)]), []))
    elif kind == "mercury":
        out.append((A.circle_pts(0, 0.006, 0.030, 20), [A.circle_pts(0, 0.006, 0.019, 16)[::-1]]))
        out.append((crescent(0, 0.050, 0.030, 0.0, 0.012, 0.024), []))
        out.append((ccw([(-0.0055, -0.026), (0.0055, -0.026), (0.0055, -0.075), (-0.0055, -0.075)]), []))
        out.append((ccw([(-0.026, -0.046), (0.026, -0.046), (0.026, -0.056), (-0.026, -0.056)]), []))
    return out


@item("OrbitSigils", "Orbiting sigils", lens=40, close=((5.2, -7.6, 2.4), (0.6, 0, 1.5), 52))
def build_sigils(M):
    A.MANNEQUIN_HAIR = {"male": "Males_Short", "female": "Females_Straight_Bob"}
    silver = M["silver"]
    ink = M["black_enamel"]
    glow = A.mat_glow("SigilGlow", VIOLET)
    piece("OrbitSigils", "Head")
    W, H = 0.30, 0.32   # (coordinator review: 0.21 x 0.28 read as specks at play distance; the height stays
    # capped: the orbit must stay over the swinging arms and under the hat brims)
    th = 0.026
    for k, kind in enumerate(("moon", "eye", "key", "mercury")):
        phi = math.radians(45 + 90 * k)
        # plate frame: local -Y (the extrude's front) faces out along phi; local x along the orbit, z up
        P = Matrix.Translation((ORBIT_R * math.cos(phi), ORBIT_R * math.sin(phi), ORBIT_Z)) @ \
            Matrix.Rotation(phi + math.pi / 2, 4, "Z")
        Fm = P @ Matrix.Translation((0, th / 2, 0))
        out = vesica(W, H)
        A.extrude_poly(f"SigilPlate{k}", out, th, ink, Fm, bevel=0.0)
        A.extrude_poly(f"SigilRim{k}", out, th + 0.014, silver, P @ Matrix.Translation((0, th / 2 + 0.007, 0)), bevel=0.004,
                       segments=1, holes=[ccw(offset_poly(out, 0.016))[::-1]])
        ring = offset_poly(out, 0.034)
        for yy in (-th / 2, th / 2):
            A.tube(f"SigilInner{k}_{yy > 0}", [tuple(P @ Vector((x, yy, z))) for x, z in ring], 0.0038, silver,
                   closed=True, res=3, poly=True)
        for side, Fs in (("o", P @ Matrix.Translation((0, -th / 2, 0))),
                         ("i", P @ Matrix.Rotation(math.pi, 4, "Z") @ Matrix.Translation((0, -th / 2, 0)))):
            for j, (sh, holes) in enumerate(sigil_shapes(kind)):
                A.extrude_poly(f"Sigil{k}{side}{j}", ccw(sh), 0.007, glow, Fs @ Matrix.Translation((0, 0.001, 0)) @ Matrix.Diagonal((1.3, 1.0, 1.3, 1.0)),
                               bevel=0.0, holes=holes)
        # finials: a bead and a spike above, a drop below
        top = P @ Vector((0, 0, H / 2 + 0.012)); bot = P @ Vector((0, 0, -H / 2 - 0.012))
        A.sphere(f"SigilTopBead{k}", 0.018, top, silver, seg=12, rings=8)
        A.cyl(f"SigilSpike{k}", 0.011, 0.05, top + Vector((0, 0, 0.038)), silver, verts=10, r2=0.0)
        A.sphere(f"SigilDrop{k}", 0.016, bot, silver, scale=(1, 1, 1.4), seg=12, rings=8)
        A.cyl(f"SigilDropTip{k}", 0.008, 0.03, bot - Vector((0, 0, 0.03)), silver, verts=8, r2=0.0, rot=(math.pi, 0, 0))
    write_extra("OrbitSigils", {"OrbitSigils": {"orbit": {"axis": [0, 1, 0], "rpm": 5}, "bob": ORBIT_BOB}})
    return dict(notes="four ink-black vesica plates in silver frames, each with its own violet sigil (crescent and star, "
                      "an eye, a key, mercury) on both faces; they orbit the head at eye level, 1.75 studs out (past "
                      "the shoulders, over the arms), every angle and the bob checked", glow=list(VIOLET))


# ================================================================== 22. the crow familiar
CROW_AT = Vector((0.85, -0.08, 1.0))   # between its feet, on the left shoulder top
EYE = {1: Vector((0.047, -0.188, 0.418)), -1: Vector((-0.047, -0.188, 0.418))}
# idle bones: (name, head, tail, parent) in crow-local coordinates; every animated bone turns about its OWN Y axis
# (the bone's length), so the axis is [0, 1, 0] in bone space whatever the importer does with roll
CROW_BONES = [
    ("Root", (0, 0, 0), (0, 0, 0.08), None),
    ("H0", (0, 0, 0), (0, 0, 0.05), "Root"),
    ("Body", (0, 0.0, 0.15), (0, 0.0, 0.26), "H0"),
    ("Head", (0, -0.135, 0.30), (0, -0.135, 0.45), "Body"),       # up: turning about it = looking round
    ("LidL", tuple(EYE[1]), tuple(EYE[1] + Vector((0, 0.03, 0))), "Head"),     # backward: + closes the left lid
    ("LidR", tuple(EYE[-1]), tuple(EYE[-1] + Vector((0, -0.03, 0))), "Head"),  # forward: + closes the right lid
    ("Tail", (0, 0.155, 0.142), (0.06, 0.155, 0.142), "Body"),    # sideways: + lifts the tail
    ("WingL", (0.07, -0.06, 0.32), (0.12, -0.06, 0.32), "Body"),  # sideways: + lifts the wingtips
    ("WingR", (-0.07, -0.06, 0.32), (-0.02, -0.06, 0.32), "Body"),
]
CROW_IDLE = {   # degrees about each bone's own Y (Roblox bone axes after import: [0, 1, 0])
    "Head": (-55, 75),     # + turns the beak outward (to the character's left), - toward the player's head
    "LidL": (0, 88), "LidR": (0, 88),     # open -> closed
    "Tail": (-8, 16),      # down .. up
    "WingL": (0, 12), "WingR": (0, 12),   # folded -> tips lifted (a ruffle / settle)
}


def vg(ob, fn):
    """vertex groups on a part from fn(local crow co) -> {bone: w} (joined parts keep their groups by name)"""
    groups = {}
    for v in ob.data.vertices:
        co = ob.matrix_world @ v.co - CROW_AT
        for b, w in fn(co).items():
            if w <= 1e-4:
                continue
            if b not in groups:
                groups[b] = ob.vertex_groups.get(b) or ob.vertex_groups.new(name=b)
            groups[b].add([v.index], w, "REPLACE")
    return ob


CROW_TAN = Vector((0, -0.29, 0.22)).normalized()
CROW_UP = CROW_TAN.cross(Vector((1, 0, 0))).normalized()


def body_axis(t):
    """the crow's body axis, tail base (t 0) to the neck (t 1), extrapolated past either end; an upright perch"""
    return Vector((0, lerp(0.17, -0.12, t), 0.135 + 0.22 * t + 0.015 * math.sin(math.pi * max(0.0, min(t, 1.0)))))


def body_wh(t):
    tc = max(0.0, min(1.0, t))
    w = 0.035 + 0.020 * tc + 0.058 * math.sin(math.pi * tc ** 0.8) - (0.025 * (t - 1.0) / 0.12 if t > 1.0 else 0)
    h = 0.032 + 0.012 * tc + 0.068 * math.sin(math.pi * tc ** 0.85) - (0.020 * (t - 1.0) / 0.12 if t > 1.0 else 0)
    return max(w, 0.02), max(h, 0.02)


def body_section(t, a):
    c = body_axis(t); w, h = body_wh(t)
    hh = h * (1.1 if math.sin(a) < 0 else 1.0)
    zc = -0.015 * math.sin(math.pi * max(0.0, min(t, 1.0)))
    return c + Vector((w * math.cos(a), 0, 0)) + CROW_UP * (hh * math.sin(a)) + Vector((0, 0, zc))


def body_half_x(y, z):
    """the body's half width at (y, z) (sections taken across the axis, approximated by the nearest one)"""
    t = ((y - 0.17) * -0.29 + (z - 0.135) * 0.22) / (0.29 ** 2 + 0.22 ** 2)
    for _ in range(3):   # refine against the small bow in the axis
        c = body_axis(t)
        zc = -0.015 * math.sin(math.pi * max(0.0, min(t, 1.0)))
        t += (Vector((0, y, z)) - (c + Vector((0, 0, zc)))).dot(CROW_TAN) / 0.3647
    t = max(0.0, min(1.12, t))
    c = body_axis(t); w, h = body_wh(t)
    zc = -0.015 * math.sin(math.pi * min(t, 1.0))
    d = Vector((0, y, z)) - (c + Vector((0, 0, zc)))
    k = d.dot(CROW_UP) / (h * (1.1 if d.dot(CROW_UP) < 0 else 1.0))
    return w * math.sqrt(max(0.0, 1 - k * k))


def feather_strip(name, root, tip, width, mat, up=Vector((0, 0, 1)), thick=0.005, bow=0.0, nu=3, nv=8):
    """one flight / tail feather: a tapered vane with a rounded tip, bowed along its length"""
    root, tip = Vector(root), Vector(tip)
    d = (tip - root); L = d.length; d.normalize()
    side = d.cross(up).normalized()
    nrm = side.cross(d).normalized()
    G = []
    for i in range(nu + 1):
        u = i / nu - 0.5
        col = []
        for j in range(nv + 1):
            t = j / nv
            wdt = width * (0.55 + 0.45 * math.sin(math.pi * min(1.0, 0.25 + t * 0.85))) * (1 - smooth(0.82, 1.0, t) * 0.75)
            p = root + d * (L * t) + side * (u * wdt) + nrm * (bow * math.sin(math.pi * t) + 0.004 * (abs(u) * 2) ** 2)
            col.append(p)
        G.append(col)
    return A.surface(name, G, thick, mat)


WING_TIP = Vector((0, 0.37, 0.135))


def wing_point(s, u, v, lift=0.0):
    """the folded wing's surface: u across (0 the back line .. 1 the lower edge), v along (0 the shoulder .. 1 the tip)"""
    y = lerp(-0.075, WING_TIP.y, v)
    yb = 0.17                     # the body's back end
    if y <= yb:
        t = max(0.0, min(1.0, (0.17 - y) / 0.29))
        k = lerp(0.80, -0.32, u)
        q = body_section(t, math.asin(max(-1.0, min(1.0, k))))
        x = max(0.02, body_half_x(q.y, q.z)) + 0.011 + 0.003 * math.sin(math.pi * u) + lift
        return Vector((s * x, q.y, q.z))
    f = (y - yb) / (WING_TIP.y - yb)
    e = wing_point(s, u, (yb + 0.075) / (WING_TIP.y + 0.075), lift)
    tip = Vector((s * (0.020 + 0.016 * (1 - u)), WING_TIP.y, WING_TIP.z + 0.035 * (0.5 - u) * (1 - f)))
    return e.lerp(tip, smooth(0.0, 1.0, f) * 0.92 + 0.08 * f)


def crow_parts(M):
    P0 = CROW_AT
    fe = mat_feather("CrowPlume")
    fe2 = mat_feather("CrowFlight", rgb=(0.012, 0.013, 0.020), sheen_tint=(0.25, 0.32, 0.8))
    beakm = A.mat_flat("CrowBeak", (0.020, 0.019, 0.023), rough=0.32, coat=0.4, noise=180, bump=0.05, vary=0.05, wear=0.15)
    legm = A.mat_flat("CrowLeg", (0.028, 0.026, 0.030), rough=0.5, noise=260, bump=0.25, vary=0.08, wear=0.15)
    eyem = A.mat_glow("CrowEye", (0.70, 0.36, 1.0))
    silver = M["silver"]
    gem = A.mat_glow("CrowRingGem", (0.75, 0.40, 1.0))
    T = Matrix.Translation(P0)
    n0 = len(A.PARTS)
    made = []

    def mk(ob, fn):
        made.append((ob, fn))
        return ob

    def head_w(co):   # the neck blends from the body into the head
        k = smooth(0.30, 0.36, co.z) * smooth(-0.08, -0.13, co.y)
        return {"Head": k, "Body": 1 - k}
    # ---- body: a loft along the tilted axis (an upright perch), the belly a little deeper, shaggy throat hackles
    secs = []
    N = 22
    for i in range(21):
        t = i / 20 * 1.12
        ring = []
        for s_ in range(N):
            a = 2 * math.pi * s_ / N
            ruff = 1 + 0.04 * math.sin(7 * a + 9 * t) * smooth(0.62, 0.95, t) * (1 if math.sin(a) < 0.3 else 0.3)
            p = body_section(t, a)
            c = body_axis(t)
            ring.append(c + (p - c) * ruff)
        secs.append(ring)
    mk(loft("CrowBody", secs, fe, cap0=body_axis(0) + Vector((0, 0.010, -0.004)), cap1=body_axis(1.12)), head_w)
    # ---- head: a flat-crowned ellipsoid, the forehead running steeply into the beak
    hd = A.sphere("CrowHead", 1.0, (0, -0.155, 0.405), fe, scale=(0.064, 0.080, 0.066), seg=22, rings=12)
    for v in hd.data.vertices:
        co = hd.matrix_world @ v.co
        if co.z > 0.44:
            v.co.z -= (co.z - 0.44) * 0.45
        if co.y < -0.20 and co.z > 0.40:
            v.co.z -= (co.z - 0.40) * 0.25 * smooth(-0.20, -0.235, co.y)
    hd.data.update()
    mk(hd, lambda co: {"Head": 1.0})
    # ---- beak: a deep, slightly hooked wedge
    bs = []
    for i in range(13):
        t = i / 12
        y = lerp(-0.212, -0.355, t)
        zc = 0.394 - 0.028 * t ** 1.6
        bw = 0.027 * (1 - t) ** 0.9 + 0.0015
        hu = 0.030 * (1 - t) ** 0.8 + 0.0015
        hl = 0.016 * (1 - t) + 0.0012
        ring = []
        for s_ in range(14):
            a = 2 * math.pi * s_ / 14
            sa = math.sin(a)
            z = zc + (hu if sa > 0 else hl) * sa + 0.004 * (1 - t) * max(0.0, sa) ** 8
            ring.append(Vector((bw * math.cos(a) * (1 - 0.25 * max(0.0, sa)), y, z)))
        bs.append(ring)
    mk(loft("CrowBeak", bs, beakm, cap0=Vector((0, -0.207, 0.394)), cap1=Vector((0, -0.358, 0.364))),
       lambda co: {"Head": 1.0})
    for sx in (-1, 1):   # nasal bristles over the beak base
        mk(A.sphere(f"CrowBristle{sx}", 1.0, (sx * 0.011, -0.232, 0.414), fe, scale=(0.015, 0.032, 0.009), seg=10, rings=6,
                    rot=(math.radians(-12), 0, sx * math.radians(8))), lambda co: {"Head": 1.0})
    # ---- eyes (a familiar's violet glow) and lids (shells round the eye: open = tucked up into the brow)
    for sx in (-1, 1):
        e = EYE[sx]
        mk(A.sphere(f"CrowEye{sx}", 0.0145, e, eyem, seg=12, rings=8), lambda co: {"Head": 1.0})
        G = []
        for i in range(13):
            ph = 2 * math.pi * i / 12
            col = []
            for j in range(5):
                th_ = math.radians(lerp(5, 72, j / 4))
                d = Vector((math.sin(th_) * math.cos(ph), math.sin(th_) * math.sin(ph), math.cos(th_)))
                col.append(e + d * 0.0178)
            G.append(col)
        mk(A.surface(f"CrowLid{sx}", G, 0.0025, fe), (lambda nm: (lambda co: {nm: 1.0}))("LidL" if sx > 0 else "LidR"))
    # ---- wings, folded along the sides, the primaries crossing over the tail; a scalloped covert layer
    for sx in (-1, 1):
        wn = "WingL" if sx > 0 else "WingR"
        root_w = (lambda wn_: (lambda co: {wn_: smooth(-0.085, -0.02, co.y), "Body": 1 - smooth(-0.085, -0.02, co.y)}))(wn)
        nu, nv = 6, 14
        G = [[wing_point(sx, i / nu, j / nv) for j in range(nv + 1)] for i in range(nu + 1)]
        mk(A.surface(f"CrowWing{sx}", G, 0.010, fe), root_w)
        cov = []
        for i in range(4):
            u = i / 3 * 0.62
            col = []
            for j in range(11):
                v = j / 10 * 0.5
                p = wing_point(sx, u, v, lift=0.006)
                if i == 3:   # the scalloped lower edge
                    p = p + Vector((0, 0, 0.012 * abs(math.sin(j / 10 * math.pi * 4))))
                col.append(p)
            cov.append(col)
        mk(A.surface(f"CrowCoverts{sx}", cov, 0.006, fe), root_w)
        for k in range(5):   # the primaries: five long flight feathers fanning back over the tail
            u = 0.28 + 0.15 * k
            root = wing_point(sx, u, 0.50, lift=0.004)
            tip = Vector((sx * (0.018 + 0.010 * k), WING_TIP.y + 0.012 * (4 - k), WING_TIP.z + 0.012 - 0.008 * k))
            mk(feather_strip(f"CrowPrimary{sx}_{k}", root, tip, 0.038, fe2, up=Vector((sx, 0, 0.35)), bow=0.005),
               (lambda wn_: (lambda co: {wn_: 1.0}))(wn))
    # ---- tail: seven rectrices fanned a little, the middle ones on top
    for k in range(7):
        dx = (k - 3) * 0.015
        lift = 0.004 * (3 - abs(k - 3))
        mk(feather_strip(f"CrowTail{k}", (dx * 0.25, 0.150, 0.146 + lift), (dx, 0.45, 0.090 + lift), 0.042, fe2, bow=0.004),
           lambda co: {"Tail": smooth(0.16, 0.21, co.y), "Body": 1 - smooth(0.16, 0.21, co.y)})
    # ---- legs, scutes, toes and claws (resting on the shoulder top)
    for sx in (-1, 1):
        ank = Vector((sx * 0.040, -0.012, 0.024))
        mk(A.tube(f"CrowTarsus{sx}", [(sx * 0.038, 0.0, 0.16), (sx * 0.039, -0.006, 0.09), tuple(ank)], 0.0105, legm, res=5,
                  taper=lambda t: lerp(1.0, 0.8, t)), lambda co: {"Root": 1.0})
        for q, z in enumerate((0.048, 0.072)):
            mk(A.torus(f"CrowScute{sx}_{q}", 0.0095, 0.0022, (sx * 0.0395, -0.008, z), legm, major=10, minor=4),
               lambda co: {"Root": 1.0})
        for q, ang in enumerate((-28, 0, 28, 180)):
            a = math.radians(ang * sx)
            L = 0.064 if ang != 180 else 0.042
            d = Vector((math.sin(a), -math.cos(a), 0))
            p1 = ank + d * (L * 0.45) + Vector((0, 0, -0.010))
            p2 = ank + d * L + Vector((0, 0, -0.013))
            mk(A.tube(f"CrowToe{sx}_{q}", [tuple(ank + Vector((0, 0, -0.004))), tuple(p1), tuple(p2)], 0.0068, legm, res=5,
                      taper=lambda t: lerp(1.0, 0.62, t)), lambda co: {"Root": 1.0})
            cl = A.cyl(f"CrowClaw{sx}_{q}", 0.0045, 0.018, (0, 0, 0), beakm, verts=6, r2=0.0, bevel=0.0)
            cl.matrix_world = Matrix.Translation(p2 + d * 0.008 + Vector((0, 0, -0.002))) @ \
                (d + Vector((0, 0, -0.55))).normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
            mk(cl, lambda co: {"Root": 1.0})
    # the familiar's silver ring on the left leg, a violet chip in it
    mk(A.torus("CrowLegRing", 0.0135, 0.0036, (0.0392, -0.008, 0.105), silver, major=14, minor=5), lambda co: {"Root": 1.0})
    mk(A.sphere("CrowLegGem", 0.0055, (0.0392, -0.023, 0.105), gem, seg=8, rings=6), lambda co: {"Root": 1.0})
    place_parts(n0, T)
    for ob, fn in made:
        vg(ob, fn)
        if not ob.vertex_groups:
            vg(ob, lambda co: {"Body": 1.0})
    return made


def _crow_rig(ob):
    """the idle rig from the parts' vertex groups (bones named for the controller, not a sway chain)"""
    bones = [(n, Vector(h) + CROW_AT, Vector(t) + CROW_AT, p) for n, h, t, p in CROW_BONES]
    arm_d = bpy.data.armatures.new(f"{ob.name}Rig")
    arm = A._new_obj(f"{ob.name}Rig", arm_d)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    eb = {}
    for name, head, tail, parent in bones:
        b = arm_d.edit_bones.new(name)
        b.head, b.tail, b.roll = head, tail, 0.0
        if parent:
            b.parent = eb[parent]
        eb[name] = b
    bpy.ops.object.mode_set(mode="OBJECT")
    names = [b[0] for b in bones]
    for name in names:
        if ob.vertex_groups.get(name) is None:
            ob.vertex_groups.new(name=name)
    # at most 4 weights a vertex, normalised; unweighted vertices ride the Body
    gi = {g.index: g.name for g in ob.vertex_groups}
    body = ob.vertex_groups["Body"]
    for v in ob.data.vertices:
        ws = sorted(((gi[g.group], g.weight) for g in v.groups if g.weight > 1e-4), key=lambda t: -t[1])
        if not ws:
            body.add([v.index], 1.0, "REPLACE"); continue
        keep = ws[:4]; tot = sum(w for _, w in keep)
        for nm, w in ws:
            g = ob.vertex_groups[nm]
            if (nm, w) in keep:
                g.add([v.index], w / tot, "REPLACE")
            else:
                g.remove([v.index])
    ob.parent = arm
    md = ob.modifiers.new("Armature", "ARMATURE"); md.object = arm
    return arm, bones


@item("CrowFamiliar", "Crow familiar", views=["front34", "front", "side", "back", "close"],
      close=((3.1, -4.4, 1.8), (0.85, -0.08, 1.24), 100))
def build_crow(M):
    A.MANNEQUIN_HAIR = {"male": "Males_Short", "female": "Females_Low_Ponytail"}
    piece("Crow", "Torso", rig=_crow_rig)
    crow_parts(M)
    write_extra("CrowFamiliar", {"Crow": {
        "idle": "Familiar",
        "bones": {n: {"axis": [0, 1, 0], "min": lo, "max": hi} for n, (lo, hi) in CROW_IDLE.items()}}})
    return dict(notes="a crow perched on the left shoulder top (Torso mount): iridescent black plumage, folded wings with "
                      "the primaries crossing over a fanned tail, a hooked beak, violet familiar's eyes with lids, a "
                      "silver leg ring; rigged Root > H0 > Body > Head (> LidL, LidR), Tail, WingL, WingR for the idle "
                      "controller (no sway profile)", glow=[0.70, 0.36, 1.0])


# ================================================================== 23. the crystal pendant
PEND_BAIL = Vector((0, -0.527, 0.900))
PEND_C = Vector((0, -0.562, 0.745))


def _pend_rig(ob):
    return A.pendulum_rig(ob, PEND_BAIL, [Vector((0, -0.562, 0.62))])


def neck_chain_path(r=0.62, lift=0.024):
    """the chain's centre line: round the neck on the shoulder tops (draped over the back edge behind the neck), then
    a V down the chest from each side of the throat to the bail"""
    from nh_acc_batch1 import drape_point
    xf = math.sqrt(max(0.0, r * r - (0.5 - 0.0) ** 2))   # where the circle leaves the front edge
    a_l = math.atan2(-0.5, xf)            # left front (x > 0)
    a_r = math.atan2(-0.5, -xf) + 2 * math.pi
    ring = []
    n = 120
    for i in range(n + 1):
        a = lerp(a_l, a_r, i / n)
        p = drape_point(r * math.cos(a), r * math.sin(a) * 1.0, base_z=1.0, lift=lift)
        ring.append(p)
    k = lift * 0.7071
    vl = [Vector((xf * 0.975, -0.5 - k, 1.0 + k)), Vector((xf * 0.93, -0.5 - lift, 0.99)), Vector((0.22, -0.5 - lift, 0.955)),
          Vector((0.095, -0.5 - lift, 0.926)), PEND_BAIL + Vector((0.012, 0, 0.012))]
    vr = [Vector((-p.x, p.y, p.z)) for p in vl]
    return list(reversed(vl)) + ring + vr


@item("CrystalPendant", "Crystal pendant", close=((1.7, -4.8, 1.05), (0, -0.5, 0.78), 118))
def build_pendant(M):
    A.MANNEQUIN_HAIR = {"male": "Males_Short", "female": "Females_Low_Ponytail"}
    silver = M["silver"]
    crystal = mat_glow_grad("AmethystCore", PEND_C, (0.62, 0.26, 1.0), (0.07, 0.015, 0.13), 0.13)
    piece("CrystalPendant", "Torso", rig=_pend_rig, sway="Loops", keepout=(0, 1, 0), lock="Z")
    fine_chain("PendChain", [tuple(p) for p in neck_chain_path()], 0.042, silver, wire=0.0068, major=4)
    A.torus("PendBail", 0.022, 0.0062, PEND_BAIL, silver, rot=(math.radians(90), 0, 0), major=16, minor=6)
    # the cage crown: a little silver cap with six prongs and a beaded collar
    cap = A.lathe("PendCap", [(0.0, 0.040), (0.010, 0.040), (0.016, 0.030), (0.030, 0.018), (0.046, 0.006), (0.050, 0.0),
                              (0.044, -0.006), (0.0, -0.004)], (0, 0, 0), silver, seg=24)
    cap.matrix_world = Matrix.Translation(PEND_C + Vector((0, 0, 0.098)))
    for q in range(10):
        a = 2 * math.pi * q / 10
        A.sphere(f"PendCapBead{q}", 0.0072, PEND_C + Vector((0.049 * math.cos(a), 0.049 * math.sin(a), 0.098)), silver,
                 seg=8, rings=6)
    # the crystal: a long hexagonal bipyramid, the facets a little irregular
    rng = random.Random(23)
    hexr = 0.042
    ztop, zp1, zp0, zbot = 0.105, 0.050, -0.045, -0.105
    verts = [PEND_C + Vector((0, 0, ztop))]
    for z in (zp1, zp0):
        for s in range(6):
            a = 2 * math.pi * s / 6 + math.pi / 6
            rr = hexr * (1 + rng.uniform(-0.06, 0.06))
            verts.append(PEND_C + Vector((rr * math.cos(a), rr * math.sin(a) * 0.92, z + rng.uniform(-0.006, 0.006))))
    verts.append(PEND_C + Vector((0.003, 0, zbot)))
    faces = []
    for s in range(6):
        s2 = (s + 1) % 6
        faces.append([0, 1 + s2, 1 + s])
        faces.append([1 + s, 1 + s2, 7 + s2, 7 + s])
        faces.append([13, 7 + s, 7 + s2])
    cr = A.mesh_from("PendCrystal", verts, faces, crystal, smooth_all=False)
    bm = bmesh.new(); bm.from_mesh(cr.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(cr.data); bm.free()
    # the cage: six wires down the crystal's edges, two bands, a finial below
    for s in range(6):
        a = 2 * math.pi * s / 6 + math.pi / 6
        dx, dy = math.cos(a), math.sin(a) * 0.92
        pts = [PEND_C + Vector((dx * 0.030, dy * 0.030, 0.100)), PEND_C + Vector((dx * 0.047, dy * 0.047, zp1)),
               PEND_C + Vector((dx * 0.047, dy * 0.047, zp0)), PEND_C + Vector((dx * 0.010, dy * 0.010, zbot - 0.004))]
        A.tube(f"PendWire{s}", [tuple(p) for p in pts], 0.0042, silver, res=4, poly=True)
    for k, z in enumerate((zp1 - 0.004, zp0 + 0.004)):
        A.torus(f"PendBand{k}", 0.0475, 0.0048, PEND_C + Vector((0, 0, z)), silver, major=24, minor=5, scale=(1, 0.92, 1))
    A.sphere("PendFinial", 0.010, PEND_C + Vector((0, 0, zbot - 0.010)), silver, seg=10, rings=6)
    A.cyl("PendFinialTip", 0.006, 0.022, PEND_C + Vector((0, 0, zbot - 0.027)), silver, verts=8, r2=0.0, rot=(math.pi, 0, 0))
    # a tiny crescent on the bail's front
    A.extrude_poly("PendMoon", crescent(0, 0, 0.016, 0.008, 0.004, 0.013), 0.004, silver,
                   frame(PEND_C + Vector((0, -0.048, 0.098)), (0, 0, 0)), bevel=0.0)
    return dict(notes="a faceted amethyst in a silver cage (six wires, two bands, a beaded crown and a finial) on a fine "
                      "silver chain round the neck; its core glows faint violet (a falling emissive gradient)",
                glow=[0.62, 0.26, 1.0])


# ================================================================== 24. the potion belt
BELT_Z = -0.548
BELT_W = 0.11
BELT_OFF = 0.011
BELT_T = 0.010
VIALS = [   # x, side (-1 front, +1 back), shape, liquid colour, level
    (-0.24, -1, "flask", (0.55, 0.22, 0.95), 0.70),
    (-0.47, -1, "tube", (0.22, 0.70, 0.34), 0.80),
    (-0.71, -1, "hex", (0.95, 0.56, 0.14), 0.62),
    (-0.38, 1, "tear", (0.18, 0.62, 0.85), 0.75),
    (-0.66, 1, "longneck", (0.78, 0.22, 0.62), 0.66),
]


def vial_profile(shape):
    """(r, z) from the base up to the lip, and the neck radius"""
    if shape == "flask":
        return [(0.0, 0.0), (0.024, 0.002), (0.040, 0.016), (0.047, 0.040), (0.045, 0.066), (0.034, 0.090), (0.019, 0.106),
                (0.015, 0.118), (0.015, 0.150), (0.019, 0.155), (0.019, 0.161), (0.014, 0.163)], 0.015
    if shape == "tube":
        return [(0.0, 0.0), (0.020, 0.004), (0.027, 0.018), (0.028, 0.050), (0.028, 0.140), (0.027, 0.152), (0.031, 0.158),
                (0.031, 0.165), (0.024, 0.167)], 0.024
    if shape == "hex":
        return [(0.0, 0.0), (0.040, 0.0), (0.046, 0.008), (0.046, 0.090), (0.036, 0.110), (0.016, 0.122), (0.016, 0.150),
                (0.020, 0.154), (0.020, 0.160), (0.014, 0.162)], 0.016
    if shape == "tear":
        return [(0.0, 0.0), (0.012, 0.004), (0.026, 0.020), (0.040, 0.050), (0.044, 0.076), (0.036, 0.100), (0.020, 0.116),
                (0.014, 0.124), (0.014, 0.152), (0.018, 0.156), (0.018, 0.162), (0.012, 0.164)], 0.014
    return [(0.0, 0.0), (0.030, 0.002), (0.042, 0.012), (0.044, 0.040), (0.036, 0.058), (0.016, 0.070), (0.011, 0.082),
            (0.011, 0.150), (0.016, 0.154), (0.016, 0.160), (0.011, 0.162)], 0.011


def split_profile(prof, zl):
    """the profile below the liquid line (closed at the axis there) and above it"""
    lo, hi = [], []
    for (r0, z0), (r1, z1) in zip(prof, prof[1:]):
        if z0 <= zl:
            lo.append((r0, z0))
        if z0 < zl <= z1 or z1 < zl <= z0:
            t = (zl - z0) / (z1 - z0)
            lo.append((lerp(r0, r1, t), zl)); hi.append((lerp(r0, r1, t), zl))
        if z1 > zl:
            hi.append((r1, z1))
    return lo + [(0.0, lo[-1][1])], [(0.0, hi[0][1])] + hi


def vial(k, x, side, shape, liquid, level, M, glass, cork, wax, leather):
    prof, rn = vial_profile(shape)
    rmax = max(r for r, _ in prof)
    base_z = -0.632
    ys = side * (0.5 + BELT_OFF + BELT_T / 2 + 0.011 + rmax + 0.002)
    seg = 6 if shape == "hex" else 20
    zl = max(z for _, z in prof) * level * 0.62
    lo, hi = split_profile(prof, zl)
    liq = A.mat_glow(f"Potion{k}", liquid)
    A.lathe(f"Vial{k}Liquid", [(r + (0.0012 if r > 0 else 0), z) for r, z in lo], (x, ys, base_z), liq, seg=seg,
            rot=(0, 0, math.radians(30) if shape == "hex" else 0))
    A.lathe(f"Vial{k}Glass", hi, (x, ys, base_z), glass, seg=seg, rot=(0, 0, math.radians(30) if shape == "hex" else 0))
    top = max(z for _, z in prof)
    ck = A.lathe(f"Vial{k}Cork", [(0.0, 0.0), (rn * 0.95, 0.0), (rn * 1.18, 0.028), (rn * 1.10, 0.044), (0.0, 0.046)],
                 (x, ys, base_z + top - 0.018), cork, seg=16)
    if k in (1, 4):   # wax-sealed corks: a cap with drips
        A.lathe(f"Vial{k}Wax", [(0.0, 0.050), (rn * 1.3, 0.044), (rn * 1.45, 0.030), (rn * 1.35, 0.016), (rn * 1.2, 0.010)],
                (x, ys, base_z + top - 0.018), wax, seg=16)
        for q in range(3):
            a = 2 * math.pi * q / 3 + 0.5
            A.sphere(f"Vial{k}Drip{q}", 0.0075, (x + rn * 1.25 * math.cos(a), ys + rn * 1.25 * math.sin(a), base_z + top - 0.012 - 0.008 * q),
                     wax, scale=(1, 1, 1.8), seg=8, rings=6)
    if k == 0:        # a little paper tag on a thread
        A.tube("Vial0Thread", [(x - 0.016, ys, base_z + top - 0.030), (x - 0.034, ys - 0.008, base_z + top - 0.07),
                               (x - 0.040, ys - 0.012, base_z + top - 0.10)], 0.0022, A.mat_flat("Thread", (0.55, 0.48, 0.36), rough=0.8), res=3)
        A.box("Vial0Tag", (0.034, 0.003, 0.046), (x - 0.042, ys - 0.026, base_z + top - 0.125), M["paper"], bevel=0.0015)
    if k == 2:        # a silver wire bail round the neck
        A.torus("Vial2Wire", rn + 0.003, 0.0028, (x, ys, base_z + 0.125), M["silver"], major=16, minor=4)
    # the leather loop that holds it on the belt, and its rivet
    A.lathe(f"Vial{k}Loop", [(rmax + 0.0015, -0.019), (rmax + 0.011, -0.017), (rmax + 0.012, 0.017), (rmax + 0.0015, 0.019)],
            (x, ys, BELT_Z - 0.012), leather, seg=seg if seg > 6 else 20, rot=(0, 0, math.radians(30) if shape == "hex" else 0),
            smooth_all=True)
    A.cyl(f"Vial{k}Rivet", 0.010, 0.008, (x, side * (0.5 + BELT_OFF + BELT_T / 2 + 0.004), BELT_Z + 0.040), M["brass"],
          rot=(math.radians(90), 0, 0), verts=12)


@item("PotionBelt", "Potion belt", views=["front34", "front", "side_r", "back", "close"],
      close=((-2.8, -5.4, -0.1), (-0.25, -0.4, -0.55), 78))
def build_belt(M):
    A.MANNEQUIN_HAIR = {"male": "Males_Short", "female": "Females_Straight_Bob"}
    leather = A.mat_leather("BeltLeather", (0.11, 0.055, 0.035), scale=2.4)
    dark = A.mat_leather("BeltDark", (0.05, 0.035, 0.03), scale=2.6)
    thread = A.mat_flat("BeltThread", (0.62, 0.55, 0.42), rough=0.8, noise=300, bump=0.1)
    glass = A.mat_flat("VialGlass", (0.05, 0.05, 0.065), rough=0.05, coat=1.0, noise=10, bump=0.0, vary=0.02, wear=0.0)
    cork = A.mat_flat("Cork", (0.40, 0.28, 0.16), rough=0.85, noise=160, bump=0.35, vary=0.15, wear=0.1, dirt=0.8)
    wax = A.mat_flat("SealWax", (0.10, 0.03, 0.14), rough=0.35, noise=40, bump=0.08, vary=0.05, wear=0.0)
    silver = M["silver"]
    piece("PotionBelt", "Torso")
    G = band_loop(Vector((0, 0, BELT_Z)), (0, 0, 1), BELT_W, BELT_OFF)
    A.surface("BeltBand", G, BELT_T, leather)
    for k in (0, 3):   # stitch lines just in from each edge (not over the left hip, where the katana's guard is close)
        row = [project_out(G[k][j] + (G[1 if k == 0 else 2][j] - G[k][j]).normalized() * 0.012, BELT_OFF + BELT_T / 2 + 0.001)
               for j in range(len(G[k]) - 1)]
        runs, cur = [], []
        for p in row:
            if p.x > 0.55 and p.y < -0.2:
                if len(cur) > 1:
                    runs.append(cur)
                cur = []
            else:
                cur.append(p)
        if len(cur) > 1:
            runs.append(cur)
        if len(runs) > 1 and (runs[0][0] - row[0]).length < 1e-9 and (runs[-1][-1] - row[-1]).length < 1e-9:
            runs = [runs[-1] + runs[0]] + runs[1:-1]
        for q, run in enumerate(runs):
            A.tube(f"BeltStitch{k}_{q}", [tuple(p) for p in run], 0.0028, thread, res=3, poly=True)
    yb = -(0.5 + BELT_OFF + BELT_T / 2)
    # the buckle: a pointed-oval silver frame with a crescent boss, the strap end through it
    out = vesica(0.15, 0.135, 10)
    Fb = frame((0.0, yb - 0.001, BELT_Z))
    A.extrude_poly("BeltBuckle", out, 0.018, silver, Fb, bevel=0.004, segments=2, holes=[ccw(offset_poly(out, 0.022))[::-1]])
    A.extrude_poly("BeltBuckleBar", ccw([(-0.006, -0.050), (0.006, -0.050), (0.006, 0.050), (-0.006, 0.050)]), 0.024, silver,
                   Fb, bevel=0.002, segments=1)
    A.extrude_poly("BeltBuckleMoon", crescent(0, 0.0, 0.026, 0.012, 0.006, 0.021), 0.010, M["brassold"],
                   frame((0.0, yb - 0.019, BELT_Z + 0.050)), bevel=0.0015, segments=1)
    tail = [[project_out(Vector((x, -0.6, BELT_Z + dz)), BELT_OFF + BELT_T + 0.004) for x in (0.02, 0.10, 0.18, 0.235)]
            for dz in (-0.042, 0.042)]
    A.surface("BeltTail", tail, 0.010, dark)
    A.box("BeltTailTip", (0.03, 0.012, 0.09), tuple(project_out(Vector((0.245, -0.6, BELT_Z)), BELT_OFF + BELT_T + 0.005)), silver, bevel=0.004)
    A.box("BeltKeeper", (0.024, 0.016, 0.125), tuple(project_out(Vector((0.115, -0.6, BELT_Z)), BELT_OFF + BELT_T + 0.004)), dark, bevel=0.004)
    # the vials
    for k, (x, side, shape, col, level) in enumerate(VIALS):
        vial(k, x, side, shape, col, level, M, glass, cork, wax, dark)
    # the pouch on the front left (clear of the katana's guard further out), a flap and a crescent clasp
    lo, hi = Vector((0.27, yb - 0.012 - 0.105, -0.655)), Vector((0.53, yb - 0.010, -0.470))
    A.box("PouchBody", hi - lo, (lo + hi) / 2, dark, bevel=0.03, segments=3)
    flap = []
    for i in range(9):
        u = i / 8
        col = []
        for j in range(7):
            t = j / 6
            col.append(Vector((lerp(lo.x - 0.008, hi.x + 0.008, u), lo.y - 0.010 - 0.006 * math.sin(math.pi * u) * t,
                               lerp(hi.z + 0.012, lo.z + 0.085 - 0.03 * math.sin(math.pi * u), t))))
        flap.append(col)
    A.surface("PouchFlap", flap, 0.012, leather)
    A.tube("PouchFlapStitch", [tuple(flap[i][-1] + Vector((0, -0.007, 0.012))) for i in range(9)], 0.0025, thread, res=3)
    A.extrude_poly("PouchClasp", crescent(0, 0, 0.030, 0.014, 0.007, 0.025), 0.010, silver,
                   frame(((lo.x + hi.x) / 2, lo.y - 0.022, lo.z + 0.075)), bevel=0.002, segments=1)
    A.sphere("PouchStud", 0.012, ((lo.x + hi.x) / 2, lo.y - 0.018, lo.z + 0.040), silver, seg=10, rings=6)
    for k, x in enumerate((lo.x + 0.03, hi.x - 0.03)):   # the loops that hang it on the belt
        A.box(f"PouchLoop{k}", (0.03, 0.010, 0.13), (x, yb - 0.003, BELT_Z + 0.01), leather, bevel=0.003)
    return dict(notes="a high dark leather belt, stitched, a pointed-oval silver buckle with a crescent; five corked vials "
                      "(violet, green, amber, teal, magenta, faintly glowing) in loops on the front right and back right, "
                      "two wax-sealed, one tagged; a pouch with a crescent clasp on the front left (clear of the katana's "
                      "guard). Above the striding legs' reach (z -0.50 .. -0.635)", glow=[0.55, 0.22, 0.95])


# ================================================================== the game-side motion check
def _in_body(p):
    if abs(p.x) <= 1.0 and abs(p.y) <= 0.5 and abs(p.z) <= 1.0:
        return True
    r = math.hypot(p.x, p.y)
    return 0.9 <= p.z <= 2.1 and r <= 0.6 - max(0.0, abs(p.z - 1.5) - 0.35)


def motion_check():
    """the orbiting pieces at every angle (5 degree steps) and the ends and middle of their bob, at the hair-fit scale
    (1.02 about the headband) and without, against every body (rest and both strides), the head, every hair, the hats
    (rest, and each hat at every hair's fit), the crow, the capes and the other pieces they can be worn with; and the
    crow at its idle limits (every bone at min / max, the head swept) against the same. Prints MOTION lines."""
    import acc_check as C
    from mathutils.bvhtree import BVHTree
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    hats_root = argv[argv.index("--hats") + 1] if "--hats" in argv else None
    root = argv[argv.index("--root") + 1] if "--root" in argv else "E:/NH-Work/acc"
    bpy.ops.wm.read_factory_settings(use_empty=True)
    C.load_slots(); C.load_conflicts()
    bodies = {"standard": C.standard_body()}; bodies.update(C.load_body_meshes())
    head = C.head_mesh()
    tb = lambda vt: BVHTree.FromPolygons(vt[0], vt[1], epsilon=0.0)
    body_trees = {}
    for bid, parts in bodies.items():
        for deg in (0, C.LIMB_DEG, -C.LIMB_DEG):
            posed = parts if deg == 0 else C.limb_pose(parts, deg)[0]
            body_trees[(bid, deg)] = [(k, tb(v)) for k, v in posed.items()] + [("Head", tb(head))]
    hairs = {}
    for h in sorted(A._hair_attach()):
        ob = A.real_hair(h)
        if ob is None:
            continue
        v, t = C.mesh_tris(ob); bpy.data.objects.remove(ob)
        t = [tri for tri in t if not _in_body(sum((v[i] for i in tri), Vector()) / 3)]
        hairs[h] = BVHTree.FromPolygons(v, t, epsilon=0.0)

    def load(rt, it, posable=False):
        lay = json.load(open(os.path.join(rt, "layout", f"{it}.json")))
        with bpy.data.libraries.load(os.path.join(rt, "blend", f"{it}.blend"), link=False) as (src, dst):
            dst.objects = [n for n in src.objects if n in lay["pieces"] or (n.endswith("Rig") and n[:-3] in lay["pieces"])]
        objs = {o.name: o for o in dst.objects if o is not None}
        for o in objs.values():
            bpy.context.scene.collection.objects.link(o)
        out = {}
        for n, o in objs.items():
            if n in lay["pieces"]:
                out[n] = dict(ob=o, arm=objs.get(n + "Rig"), lay=lay["pieces"][n], verts=C.mesh_tris(o))
        if not posable:
            for o in objs.values():
                bpy.data.objects.remove(o)
        return out
    others = {}
    b1 = ["CliquePins", "SchoolTie", "BowTie", "Sashes", "Satchel", "MessengerBag", "BookStrap", "Grimoire", "ChoirCollar", "Ruff"]
    for it in b1 + ["CrystalPendant", "PotionBelt", "RuneHalo", "CrowFamiliar"]:
        if os.path.exists(os.path.join(root, "blend", f"{it}.blend")):
            for n, P in load(root, it).items():
                others[(it, n)] = P["verts"]
    for key in ("WardenMantle", "ReaperShroud", "DuelistCape", "CaptainGreatcape", "MidnightCollar"):
        bp = f"E:/NH-Work/capes/{key}.blend"
        with bpy.data.libraries.load(bp, link=False) as (src, dst):
            dst.objects = [n for n in src.objects if n == "CapeBody"]
        ob = dst.objects[0]; bpy.context.scene.collection.objects.link(ob)
        for md in list(ob.modifiers):
            ob.modifiers.remove(md)
        ob.parent = None
        others[("Cape" + key, "CapeBody")] = C.mesh_tris(ob)
        C.SLOT_OF[("Cape" + key, "CapeBody")] = "Cape"
        bpy.data.objects.remove(ob)
    hats = {}
    if hats_root:
        for it in ("Hats", "WitchHat", "HunterHat", "MourningHats", "Masks", "TatteredHood"):
            if os.path.exists(os.path.join(hats_root, "blend", f"{it}.blend")):
                for n, P in load(hats_root, it).items():
                    hats[(it, n)] = (P["verts"], P["lay"].get("hair_fit", {}))
    print("MOTION loaded", len(hairs), "hairs,", len(others), "other pieces,", len(hats), "hat pieces")
    SEATP = Vector((0, 0, 1.93))

    def hat_fit(vt, f):
        k, dz = f
        return ([SEATP + (p - SEATP) * k + Vector((0, 0, dz)) for p in vt[0]], vt[1])
    other_trees = {key: BVHTree.FromPolygons(ov[0], ov[1], epsilon=0.0) for key, ov in others.items()}
    hat_trees = {}
    for key, (hv, fits) in hats.items():
        hat_trees[(key, None)] = BVHTree.FromPolygons(hv[0], hv[1], epsilon=0.0)
        for h, f in fits.items():
            if f:
                hat_trees[(key, h)] = BVHTree.FromPolygons(*hat_fit(hv, f), epsilon=0.0)

    def against(vt, mine, skip_hats=False, hair_fit=1.0):
        """{label: n} of everything this shape meets"""
        T = BVHTree.FromPolygons(vt[0], vt[1], epsilon=0.0)
        hits = {}
        for (bid, deg), trees in body_trees.items():
            for k, t in trees:
                if T.overlap(t):
                    hits[f"body {bid} limbs {deg:+d} {k}"] = 1
        for h, t in hairs.items():
            if T.overlap(t):
                hits[f"hair {h}"] = 1
        for key, t in other_trees.items():
            if key[0] == mine[0] or C.exclusive(mine, key) or C.slot_of(*mine) == C.slot_of(*key):
                continue
            if T.overlap(t):
                hits[f"piece {key[0]}/{key[1]}"] = 1
        if not skip_hats:
            for (key, h), t in hat_trees.items():
                if C.exclusive(mine, key) or not T.overlap(t):
                    continue
                if h is None:
                    hits[f"hat {key[1]} at rest"] = 1
                else:
                    hits.setdefault(f"hat {key[1]} under hair fits", set()).add(h)
        return hits
    # ---- the orbiting pieces
    for it in ("RuneHalo", "OrbitSigils"):
        ex = os.path.join(root, "layout", f"{it}.extra.json")
        if not os.path.exists(ex):
            continue
        spec = json.load(open(ex))
        for pn, P in load(root, it).items():
            o = spec.get(pn, {}).get("orbit")
            if not o:
                continue
            ax = Vector((-o["axis"][0], o["axis"][2], o["axis"][1])).normalized()   # Roblox mount axes -> Blender
            c = A.MOUNT_CENTRE[P["lay"]["mount"]]
            bob = spec[pn].get("bob", 0.0)
            v0, t0 = P["verts"]
            worst, n, hair_sets = {}, 0, {}
            for deg in range(0, 360, 5):
                R = Matrix.Rotation(math.radians(deg), 3, ax)
                for b in (-bob, 0.0, bob):
                    for k in (1.0, 1.02):
                        vv = [SEATP + ((R @ (p - c) + c + Vector((0, 0, b))) - SEATP) * k for p in v0]
                        hits = against((vv, t0), (it, pn), skip_hats=(deg % 15 != 0))
                        n += 1
                        for h, x in hits.items():
                            if isinstance(x, set):
                                hair_sets.setdefault(h, set()).update(x)
                            else:
                                worst.setdefault(h, []).append(deg)
            print(f"MOTION orbit {it}/{pn}: {n} poses (72 angles x bob -{bob}/0/+{bob} x hair-fit 1.00/1.02), axis "
                  f"{[round(x, 3) for x in ax]} about {tuple(c)}")
            if not worst:
                print(f"MOTION orbit {it}/{pn}: clear of every body, hair, piece and hat at every pose")
            for h, degs in sorted(worst.items()):
                print(f"MOTION orbit {it}/{pn} meets {h} at {len(degs)} poses (angles {sorted(set(degs))[:8]}...)")
            for h, x in sorted(hair_sets.items()):
                print(f"MOTION orbit {it}/{pn}: {h} for {len(x)} hairs: {sorted(x)}")
    # ---- the crow at its idle limits
    if os.path.exists(os.path.join(root, "blend", "CrowFamiliar.blend")):
        spec = json.load(open(os.path.join(root, "layout", "CrowFamiliar.extra.json")))["Crow"]["bones"]
        Pc = load(root, "CrowFamiliar", posable=True)["Crow"]
        ob, arm = Pc["ob"], Pc["arm"]
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode="POSE")

        def pose(vals):
            for pb in arm.pose.bones:
                pb.rotation_mode = "AXIS_ANGLE"
                a = vals.get(pb.name, 0.0)
                pb.rotation_axis_angle = (math.radians(a), 0, 1, 0)
            bpy.context.view_layer.update()
            return C.mesh_tris(ob)
        poses = []
        lim = {k: (v["min"], v["max"]) for k, v in spec.items()}
        import itertools
        for hd in [lerp(lim["Head"][0], lim["Head"][1], i / 8) for i in range(9)]:
            for tl, wg, ld in itertools.product(lim["Tail"], (0, 1), (0, 1)):
                poses.append({"Head": hd, "Tail": tl, "WingL": lim["WingL"][wg], "WingR": lim["WingR"][wg],
                              "LidL": lim["LidL"][ld], "LidR": lim["LidR"][ld]})
        fails, hair_bad, piece_bad = {}, {}, {}
        worst_clip = (0.0, "")
        for i, pv in enumerate(poses):
            vt = pose(pv)
            hits = against(vt, ("CrowFamiliar", "Crow"), skip_hats=True)
            for h in hits:
                if h.startswith("hair"):
                    hair_bad[h[5:]] = hair_bad.get(h[5:], 0) + 1
                elif h.startswith("piece"):
                    piece_bad[h] = piece_bad.get(h, 0) + 1
                else:
                    fails[h] = fails.get(h, 0) + 1
            if i % 9 == 0 or i == len(poses) - 1:   # the clip depth on every body (rest and strides) at the corner poses
                for bid in bodies:
                    for deg in (0, C.LIMB_DEG, -C.LIMB_DEG):
                        posed = bodies[bid] if deg == 0 else C.limb_pose(bodies[bid], deg)[0]
                        clip, gap, where = C.check_body(vt[0], "Torso", posed, head)
                        if clip > worst_clip[0]:
                            worst_clip = (clip, f"{bid} limbs {deg:+d} pose {i}: {where}")
        pose({})
        bpy.ops.object.mode_set(mode="OBJECT")
        rest_hair = [h for h, t in hairs.items() if BVHTree.FromPolygons(*Pc["verts"], epsilon=0.0).overlap(t)]
        print(f"MOTION idle Crow: {len(poses)} poses (head swept {lim['Head']}, tail {lim['Tail']}, wings, lids)")
        print(f"MOTION idle Crow: deepest clip into any body / the head {worst_clip[0]:.4f} ({worst_clip[1]})")
        for h, n in sorted(fails.items()):
            print(f"MOTION idle Crow meets {h} in {n} poses")
        if not fails:
            print("MOTION idle Crow: clear of every body (rest and both strides) and the head in every pose")
        for h, n in sorted(piece_bad.items()):
            print(f"MOTION idle Crow meets {h} in {n} poses")
        print(f"MOTION idle Crow hair: {len(hairs) - len(rest_hair)}/{len(hairs)} clear at rest; "
              f"{len(hairs) - len(set(rest_hair) | set(hair_bad))}/{len(hairs)} clear in every idle pose; "
              f"idle-only: {sorted(set(hair_bad) - set(rest_hair))}")
    print("MOTION done")


if __name__ == "__main__" and "--motioncheck" in sys.argv:
    motion_check()
