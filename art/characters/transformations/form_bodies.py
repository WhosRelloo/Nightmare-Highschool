"""NH race transformations, Task 2 batch 2: the body pieces, fitted to each of the 12 bodies (Blender 5.2, headless).

E:/Blender/blender.exe -b --factory-startup -P form_bodies.py -- --dest E:/NH-Work/forms [--only lean,plus] [--sheet]

One FBX per body, NHFormBody_<body>.fbx (import with rig OFF), holding every direction's body pieces for that body,
plus NHFormHead.fbx (the Head is the same on every body). Pieces are named <Dir><Piece>, e.g. W1Mantle, G2WrapL:
  V2  Spines (Torso)                                           obsidian spines down the back
  W1  Mantle (Torso), CuffL/CuffR (arms), ShinL/ShinR (legs)   fur locks, tinted by the Fur Look (no head fur)
  W2  Mantle, Back (Torso), ArmL/ArmR (arms), Moon (Torso)     fur down the arms and back; glowing moon-marks
  G1  Ribs (Torso: ribs + sternum), Spine (Torso), SpurL/SpurR (arms)                     bone, the Bone finish
  G2  WrapL/WrapR (arms, with hanging tatters), Chest (Torso), Moss (Torso), Nails (Torso)   grave linen, moss, iron
  R1  Capelet (Torso)                                          a mist capelet open at the front (head clear)
  R2  SpikeL/SpikeR (arms), Chains (Torso), Hang (Left Arm), RimeL/RimeR (legs)           ice, spectral chain
  Head: G1Jaw (the jaw guard)
V1 has no body piece: its long swept ears are the Vampire Ears Look (race cosmetics). Werewolf ears and tail are the
race Looks too. No claws anywhere (owner 2026-11-23).

Fitting: every piece is raycast onto that body's own meshes (art/characters/bodies: NHBodyTypes.blend; Female v2 rebuilt
from nh_female_body; Standard = the R6 boxes). Same seed per body, so the pieces match across bodies.
Low poly by design (no subdivision): fur locks are single-sided blades (the MeshParts are DoubleSided in Studio).
UVs are world-scaled (TILE studs per UV unit) for the tileable NHForm_* maps; fur locks run their V down the lock.
Writes <dest>/forms_body_fit.json: per file, per piece: its R6 part, bounding-box centre from that part's centre in
Roblox axes (x right, y up, z back), tris, map set, tint kind.
"""
import bpy, bmesh, json, math, os, random, sys
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
DEST = argv[argv.index("--dest") + 1] if "--dest" in argv else "E:/NH-Work/forms"
ONLY = argv[argv.index("--only") + 1].split(",") if "--only" in argv else None
SHEET = "--sheet" in argv          # also render a check sheet per body (every direction, front and back) to <dest>/check
os.makedirs(os.path.join(DEST, "fbx"), exist_ok=True)

BODIES_BLEND = "E:/NH-Work/bodytypes/NHBodyTypes.blend"
RIG = "E:/Blender Shit/CHARACTER SHIT/PaintRigV3.blend"
BODY_IDS = ["standard", "female", "lean", "athletic", "muscular", "stocky", "heavy", "petite", "toned", "curvy", "strong", "plus"]
PARTS = {"Torso": "Torso", "RArm": "RightArm", "LArm": "LeftArm", "RLeg": "RightLeg", "LLeg": "LeftLeg"}
RBX_PART = {"Torso": "Torso", "RArm": "Right Arm", "LArm": "Left Arm", "RLeg": "Right Leg", "LLeg": "Left Leg", "Head": "Head"}
CENTRE = {"Torso": Vector((0, 0, 3)), "RArm": Vector((1.5, 0, 3)), "LArm": Vector((-1.5, 0, 3)),
          "RLeg": Vector((0.5, 0, 1)), "LLeg": Vector((-0.5, 0, 1)), "Head": Vector((0, 0, 4.5))}
SIZE = {"Torso": (2, 1, 2), "RArm": (1, 1, 2), "LArm": (1, 1, 2), "RLeg": (1, 1, 2), "LLeg": (1, 1, 2)}
TILE = {"fur": 0.5, "bone": 0.6, "cloth": 0.8, "mist": 2.0, "ice": 1.0, "horn": 0.5, "glow": 1.0}
UP, DN, FW, BK = Vector((0, 0, 1)), Vector((0, 0, -1)), Vector((0, 1, 0)), Vector((0, -1, 0))
TRI_CAP = 20000
DANG = {}           # the last build_body's dangles (FormDangles): tatters, chain swags, the wrist chain
DANGLES = "--dangles" in argv   # write NHFormDangles.fbx + forms_dangles.json only (see dangles())


# ---------------------------------------------------------------- geometry (verts, faces, uvs) builders
class Geo:
    """one piece: accumulated verts / faces / per-vertex UVs"""
    def __init__(self):
        self.v, self.f, self.uv = [], [], []

    def grid(self, rows, uvs, closed=False):
        """rows: list of rows of points (same length); uvs alike. closed: wrap across (tubes)."""
        b = len(self.v)
        n = len(rows[0])
        for r, ur in zip(rows, uvs):
            self.v += r; self.uv += ur
        m = n if closed else n - 1
        for i in range(len(rows) - 1):
            for j in range(m):
                a = b + i * n + j
                c = b + i * n + (j + 1) % n
                self.f.append((a, c, c + n, a + n))

    def tris(self):
        return sum(len(f) - 2 for f in self.f)


def frame(d):
    d = d.normalized()
    a = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
    u = d.cross(a).normalized()
    return u, d.cross(u).normalized()


def tube(G, pts, radii, sides=6, tile=0.6, flat=1.0):
    """a tapered tube along pts (parallel-transported frame); flat < 1 squashes it along the second axis"""
    rows, uvs = [], []
    u, w = frame(pts[1] - pts[0])
    acc = 0.0
    for i, p in enumerate(pts):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        u = (u - d * u.dot(d)).normalized(); w = d.cross(u).normalized()
        if i:
            acc += (p - pts[i - 1]).length
        r = radii[i]
        row, ur = [], []
        for k in range(sides + 1):
            a = 2 * math.pi * k / sides
            row.append(p + u * (math.cos(a) * r) + w * (math.sin(a) * r * flat))
            ur.append((k / sides * 2 * math.pi * radii[0] / tile, acc / tile))
        rows.append(row); uvs.append(ur)
    G.grid(rows, uvs)


def cone(G, base, d, length, r0, sides=6, tile=0.6, bend=None, n=4):
    pts = [base + d.normalized() * (length * t) + (bend or Vector()) * (length * t * t) for t in [i / n for i in range(n + 1)]]
    tube(G, pts, [r0 * (1 - i / n) + 0.002 for i in range(n + 1)], sides, tile)


def blade(G, root, along, across, nrm, L, W, curve, nu=5, nv=2, tile=0.5):
    """a fur lock / tatter: a pointed single-sided blade, widest a third of the way, curling out along nrm"""
    along, across, nrm = along.normalized(), across.normalized(), nrm.normalized()
    rows, uvs = [], []
    for i in range(nu + 1):
        t = i / nu
        w = W * (0.75 + 0.25 * math.sin(math.pi * min(1.0, t * 2.5))) * (1 - t) ** 0.85
        row, ur = [], []
        for j in range(nv + 1):
            s = j / nv * 2 - 1
            row.append(root + along * (L * t) + across * (w * s) + nrm * (curve * L * t * t + 0.012 * (1 - abs(s))))
            ur.append(((s * W) / tile + 0.5, (L * t) / tile))
        rows.append(row); uvs.append(ur)
    G.grid(rows, uvs)


def torus(G, c, axis, turn, R, r, stretch=1.5, seg=8, ring=4, tile=0.5):
    """a chain link: axis = the chain's direction (long axis), turn = the link's plane normal"""
    ax = axis.normalized(); nn = turn - ax * turn.dot(ax)
    if nn.length < 1e-4:
        nn = UP - ax * ax.z if abs(ax.z) < 0.95 else Vector((1, 0, 0))
    nn = nn.normalized(); bx = ax.cross(nn)
    rows, uvs = [], []
    for i in range(seg + 1):
        a = 2 * math.pi * i / seg
        cen = c + ax * (math.cos(a) * R * stretch) + bx * (math.sin(a) * R)
        rad = (ax * math.cos(a) * stretch + bx * math.sin(a)).normalized()
        row, ur = [], []
        for k in range(ring + 1):
            b = 2 * math.pi * k / ring
            row.append(cen + rad * (math.cos(b) * r) + nn * (math.sin(b) * r))
            ur.append((i / seg * 2 * math.pi * R / tile, k / ring * 2 * math.pi * r / tile))
        rows.append(row); uvs.append(ur)
    G.grid(rows, uvs)


def ellipsoid(G, c, rx, ry, rz, seg=10, ring=6, tile=0.6):
    rows, uvs = [], []
    for i in range(ring + 1):
        th = math.pi * i / ring
        row, ur = [], []
        for k in range(seg + 1):
            ph = 2 * math.pi * k / seg
            row.append(c + Vector((rx * math.sin(th) * math.cos(ph), ry * math.sin(th) * math.sin(ph), rz * math.cos(th))))
            ur.append((k / seg * 2 * math.pi * rx / tile, i / ring * math.pi * rz / tile))
        rows.append(row); uvs.append(ur)
    G.grid(rows, uvs)


# ---------------------------------------------------------------- body surfaces
def bvh_of(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    oe = ob.evaluated_get(dg)
    me = oe.to_mesh()
    mw = ob.matrix_world
    verts = [mw @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    oe.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys)


def box_bvh(key):
    c, (sx, sy, sz) = CENTRE[key], SIZE[key]
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    vs = [c + Vector((x * hx, y * hy, z * hz)) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    fs = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return BVHTree.FromPolygons(vs, fs)


BODY_OBJS = {}                         # {body: [objects]} for the check sheets


def box_obj(key, name):
    c, (sx, sy, sz) = CENTRE[key], SIZE[key]
    bpy.ops.mesh.primitive_cube_add(size=1, location=c)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (sx, sy, sz)
    bpy.context.view_layer.update()
    return ob


def load_bodies():
    """{body: {part: BVHTree}} in the build space (front +Y, the R6 layout at height 1)"""
    out = {}
    with bpy.data.libraries.load(BODIES_BLEND, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n.startswith("NHBody_")]
    for ob in dst.objects:
        bpy.context.scene.collection.objects.link(ob)
    sys.path.insert(0, os.path.join(HERE, "..", "bodies"))
    sys.path.insert(0, os.path.join(HERE, "..", "female"))
    import nh_body_types as nbt                # (its argv parsing ignores --dest)
    fem = nbt.current_bodies()
    for b in BODY_IDS:
        if b == "standard":
            out[b] = {k: box_bvh(k) for k in PARTS}
            BODY_OBJS[b] = [box_obj(k, f"std_{k}") for k in PARTS]
            continue
        out[b] = {}
        for key, p in PARTS.items():
            ob = fem[p] if b == "female" else next(o for o in dst.objects if o.name.startswith(f"NHBody_{b}_{p}"))
            ob.rotation_euler = (0, 0, math.pi)       # built facing -Y; the build space faces +Y
            ob.location = CENTRE[key]
            ob.scale = (1, 1, 1)
            bpy.context.view_layer.update()
            out[b][key] = bvh_of(ob)
            BODY_OBJS.setdefault(b, []).append(ob)
            ws = [ob.matrix_world @ v.co for v in ob.data.vertices]
            print(f"  {b} {key}: x {min(v.x for v in ws):.2f}..{max(v.x for v in ws):.2f} y {min(v.y for v in ws):.2f}.."
                  f"{max(v.y for v in ws):.2f} z {min(v.z for v in ws):.2f}..{max(v.z for v in ws):.2f}")
    return out


HEAD_OBJ = []


def head_bvh():
    with bpy.data.libraries.load(RIG, link=False) as (src, dst):
        dst.objects = ["Idarkgames9"]
    ob = dst.objects[0]
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.update()
    HEAD_OBJ.append(ob)
    ws = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    lo = Vector((min(v.x for v in ws), min(v.y for v in ws), min(v.z for v in ws)))
    hi = Vector((max(v.x for v in ws), max(v.y for v in ws), max(v.z for v in ws)))
    print(f"head bbox {tuple(round(x, 3) for x in lo)} .. {tuple(round(x, 3) for x in hi)}")
    return bvh_of(ob)


def hit(bvh, origin, d):
    loc, nrm, _, _ = bvh.ray_cast(origin, d.normalized(), 20)
    return loc, nrm


def project(bvh, p, d, off):
    """p moved onto the surface along d (cast from 2 studs before p), then lifted off by `off`"""
    loc, nrm = hit(bvh, p - d.normalized() * 2.0, d)
    if loc is None:
        return p
    return loc - d.normalized() * off


def ring_point(bvh, cx, cy, z, d, off):
    o = Vector((cx, cy, z)) + d * 4
    loc, _ = hit(bvh, o, -d)
    if loc is None:
        loc = Vector((cx, cy, z)) + d * 0.5
    return loc + d * off


LINK_STEP = 0.17   # chain node spacing (a link is 0.23 long: neighbours interlock)


def project_n(bvh, p, d, off):
    """project(), also returning the surface normal (facing back along d)"""
    loc, nrm = hit(bvh, p - d.normalized() * 2.0, d)
    if loc is None:
        return None, None
    n = nrm.normalized()
    if n.dot(d) > 0:
        n = -n
    return loc - d.normalized() * off, n


def resample(path, nrm, step):
    """even nodes along a polyline (ends kept), normals blended along each segment"""
    L = [0.0]
    for a, b in zip(path, path[1:]):
        L.append(L[-1] + (b - a).length)
    n = max(2, round(L[-1] / step))
    out, on = [], []
    k = 0
    for i in range(n + 1):
        s = L[-1] * i / n
        while k < len(path) - 2 and L[k + 1] < s:
            k += 1
        t = 0.0 if L[k + 1] == L[k] else (s - L[k]) / (L[k + 1] - L[k])
        out.append(path[k].lerp(path[k + 1], t))
        on.append(nrm[k].lerp(nrm[k + 1], t).normalized())
    return out, on


def leg_outer(bvh, sx):
    """how far the leg reaches out to its side (|x|, build space), over the thigh and shin"""
    best = 0.0
    for z in (0.3, 0.7, 1.1, 1.5, 1.9):
        loc, _ = hit(bvh, Vector((3 * sx, 0, z)), Vector((-sx, 0, 0)))
        if loc is not None:
            best = max(best, abs(loc.x))
    return best or 1.0


# ---------------------------------------------------------------- pieces
def fur(G, bvh, centre, spread, n, length, r0, bias, keep=None, curve=(0.03, 0.09), nu=5, nv=2, tile=0.5):
    """shingled fur locks rooted on the surface, lying along gravity (bias) and curling out at the tip"""
    made = 0
    tries = 0
    while made < n and tries < n * 12:
        tries += 1
        p = centre + Vector((random.uniform(-spread.x, spread.x), random.uniform(-spread.y, spread.y), random.uniform(-spread.z, spread.z)))
        dirn = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-0.2, 0.6))).normalized()
        loc, nn = hit(bvh, p + dirn * 3, -dirn)
        if loc is None or (keep and not keep(loc, nn)):
            continue
        down = bias - nn * bias.dot(nn)
        if down.length < 1e-3:
            down = DN - nn * nn.z
        along = (down.normalized() * 0.97 + nn * 0.1).normalized()
        across = nn.cross(along).normalized()
        blade(G, loc - nn * 0.02, along, across, nn, length * random.uniform(0.9, 1.4), r0 * random.uniform(0.8, 1.2),
              random.uniform(*curve), nu, nv, tile)
        made += 1


def gauze(G, bvh, cx, cy, z0, z1, turns, width, off, layer, phase=0.0, spt=24, tile=0.8):
    steps = int(turns * spt)
    rows, uvs = [], []
    for k in range(steps + 1):
        t = k / steps
        ang = phase + 2 * math.pi * turns * t
        d = Vector((math.cos(ang), math.sin(ang), 0))
        zc = z0 + (z1 - z0) * t
        o = off + layer * turns * t
        w = width * min(1.0, t * steps / 4, (1 - t) * steps / 6 + 0.35)
        row = [ring_point(bvh, cx, cy, zc + dz * w, d, o + bulge) for dz, bulge in ((-0.5, 0.0), (0.0, 0.006), (0.5, 0.0))]
        rows.append(row)
        uvs.append([(t * turns * 2 * math.pi * 0.6 / tile, j * 0.5 * w / tile) for j in range(3)])
    # rows run along the ribbon; grid wants rows of equal length -> transpose (3 strands x steps)
    G.grid([list(r) for r in zip(*rows)], [list(u) for u in zip(*uvs)])


def patch(G, bvh, centre, nrm, up, size, res, off, height, tile, seed_rng):
    """frost / rime: a grid laid over the surface from outside; points whose ray misses the body are dropped (with their
    faces), so narrow limbs get a narrower patch instead of a flat card in the air"""
    n = nrm.normalized()
    u = up.cross(n).normalized(); v = n.cross(u).normalized()
    idx = {}
    for i in range(res + 1):
        for j in range(res + 1):
            a, b = (i / res - 0.5) * size, (j / res - 0.5) * size * 1.3
            fall = max(0.0, 1 - (2 * abs(i / res - 0.5)) ** 4) * max(0.0, 1 - (2 * abs(j / res - 0.5)) ** 4)
            loc, nn = hit(bvh, centre + u * a + v * b + n * 2.0, -n)
            if loc is None or nn.dot(n) < 0.3:
                continue
            idx[i, j] = len(G.v)
            G.v.append(loc + nn * (off + height * fall * seed_rng.uniform(0.2, 1.0)))
            G.uv.append((a / tile, b / tile))
    for i in range(res):
        for j in range(res):
            q = [idx.get(k) for k in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))]
            if None not in q:
                G.f.append(tuple(q))


def half_width(bvh, z, y=0.0):
    loc, _ = hit(bvh, Vector((3, y, z)), Vector((-1, 0, 0)))
    return loc.x if loc else 1.0


def build_body(B, H):
    """every piece for one body: {name: (part key, Geo, map set, tint kind)}"""
    random.seed(11)
    rng2 = random.Random(5)
    T = B["Torso"]
    P = {}
    DANG.clear()
    DANG.update({"tatters": [], "swags": [], "hang": None,
                 "legOuter": [round(leg_outer(B["RLeg"], 1), 4), round(leg_outer(B["LLeg"], -1), 4)]})

    def piece(name, part, mset, tint):
        G = Geo(); P[name] = (part, G, mset, tint); return G

    # ---- V2 Night Sovereign: obsidian spines down the back
    G = piece("V2Spines", "Torso", "horn", "HornFinish")
    for k in range(6):
        z = 3.85 - k * 0.3
        p = project(T, Vector((0, -0.6, z)), FW, 0.0)
        cone(G, p + FW * 0.03, Vector((0, -1, 0.5)), 0.32 - k * 0.03, 0.065, sides=6, tile=TILE["horn"], bend=UP * 0.6)

    # ---- W1 Moonbound / W2 Feral Lord: fur
    arm_gap = lambda loc, nn: not (abs(loc.x) > 0.9 and abs(nn.x) > 0.6)      # no locks on the torso sides (the arms)
    G = piece("W1Mantle", "Torso", "fur", "Fur")
    fur(G, T, Vector((0, -0.1, 3.82)), Vector((1.0, 0.6, 0.22)), 420, 0.5, 0.075, Vector((0, -0.3, -0.6)), keep=arm_gap)
    G = piece("W2Mantle", "Torso", "fur", "Fur")
    fur(G, T, Vector((0, -0.1, 3.8)), Vector((1.0, 0.6, 0.26)), 450, 0.6, 0.08, Vector((0, -0.3, -0.6)), keep=arm_gap)
    G = piece("W2Back", "Torso", "fur", "Fur")
    fur(G, T, Vector((0, -0.5, 3.0)), Vector((0.9, 0.12, 0.85)), 380, 0.45, 0.07, Vector((0, -0.2, -0.8)),
        keep=lambda loc, nn: arm_gap(loc, nn) and nn.y < -0.3)
    for sx, key, sd in ((1, "RArm", "R"), (-1, "LArm", "L")):
        A = B[key]
        G = piece(f"W1Cuff{sd}", key, "fur", "Fur")
        fur(G, A, Vector((1.5 * sx, 0, 2.45)), Vector((0.55, 0.55, 0.2)), 130, 0.32, 0.06, Vector((0, 0, -0.5)),
            keep=lambda loc, nn: loc.z > 2.05)
        G = piece(f"W2Arm{sd}", key, "fur", "Fur")
        fur(G, A, Vector((1.5 * sx, 0, 3.3)), Vector((0.55, 0.55, 0.65)), 270, 0.38, 0.065, Vector((0, 0, -0.5)),
            keep=lambda loc, nn, sx=sx: loc.z > 2.3 and not (abs(loc.x) < 1.08 and abs(nn.x) > 0.6))
        lk = "RLeg" if sx > 0 else "LLeg"
        G = piece(f"W1Shin{sd}", lk, "fur", "Fur")
        fur(G, B[lk], Vector((0.5 * sx, 0, 0.62)), Vector((0.55, 0.55, 0.16)), 85, 0.28, 0.06, Vector((0, 0, -0.5)),
            keep=lambda loc, nn, sx=sx: loc.z > 0.25 and not (abs(loc.x) < 0.08 and abs(nn.x) > 0.6))
    G = piece("W2Moon", "Torso", "glow", "Glow")
    ctr = Vector((0, 0.62, 3.2))
    for c0, rr in ((ctr, 0.28), (ctr + Vector((0.42, 0, 0.18)), 0.12), (ctr + Vector((-0.44, 0, -0.1)), 0.1)):
        pts = [project(T, c0 + Vector((rr * math.cos(a), 0, rr * math.sin(a))), BK, 0.03) for a in [math.pi * (0.25 + 1.2 * k / 10) for k in range(11)]]
        tube(G, pts, [0.03 * math.sin(math.pi * (0.1 + 0.8 * i / 10)) + 0.006 for i in range(11)], sides=5, tile=TILE["glow"])

    # ---- G1 Ossuary: ribs + sternum, the vertebral ridge, arm spurs
    G = piece("G1Ribs", "Torso", "bone", "WingFinish")
    for sx in (-1, 1):
        for k in range(4):
            z = 3.55 - k * 0.3
            hw = min(half_width(T, z - 0.1, 0.2), half_width(T, z - 0.18, 0.2)) - 0.12     # this body's chest width there
            pts = [project(T, Vector((sx * (0.08 + (hw - 0.08) * t), 1, z - 0.18 * t * t)), BK, 0.035) for t in [i / 8 for i in range(9)]]
            tube(G, pts, [0.055 - 0.025 * i / 8 for i in range(9)], sides=6, tile=TILE["bone"])
    st = [project(T, Vector((0, 1, 3.85 - 0.13 * i)), BK, 0.05) for i in range(10)]
    tube(G, st, [0.07 - 0.03 * i / 9 for i in range(10)], sides=8, tile=TILE["bone"])
    G = piece("G1Spine", "Torso", "bone", "WingFinish")
    for k in range(7):
        p = project(T, Vector((0, -1, 3.9 - k * 0.27)), FW, 0.0)
        ellipsoid(G, p + Vector((0, -0.04, 0)), 0.13, 0.1, 0.07, tile=TILE["bone"])
    for sx, key, sd in ((1, "RArm", "R"), (-1, "LArm", "L")):
        G = piece(f"G1Spur{sd}", key, "bone", "WingFinish")
        for k in range(3):
            p = project(B[key], Vector((2.0 * sx, 0, 3.7 - k * 0.22)), Vector((-sx, 0, 0)), 0.0)
            cone(G, p, Vector((sx, -0.3, 0.6)), 0.3, 0.06, sides=6, tile=TILE["bone"], bend=UP * 0.5)

    # ---- G2 Gravecloth: linen wraps (tatters hang from the arm wraps), chest wrap, grave-moss, iron coffin nails
    for sx, key, sd in ((1, "RArm", "R"), (-1, "LArm", "L")):
        A = B[key]
        G = piece(f"G2Wrap{sd}", key, "cloth", "None")
        gauze(G, A, 1.5 * sx, 0, 2.15, 3.85, 5.5, 0.36, 0.03, 0.006)
        for k in range(4):
            a = random.uniform(0, 2 * math.pi)
            d = Vector((math.cos(a), math.sin(a), 0))
            p = ring_point(A, 1.5 * sx, 0, 2.2, d, 0.05)
            across = Vector((-math.sin(a), math.cos(a), 0))
            along = Vector((0.06 * math.cos(a), 0.06 * math.sin(a), -1)).normalized()
            L = random.uniform(0.5, 0.8)              # (same draw order as the baked tatters: every other piece unchanged)
            DANG["tatters"].append({"part": RBX_PART[key], "w": 0.07, "across": rbx(across), "out": rbx(d),
                                    "pts": [rbx(p + along * (L * i / 3) - CENTRE[key]) for i in range(4)]})
    G = piece("G2Chest", "Torso", "cloth", "None")
    gauze(G, T, 0, 0, 2.55, 3.8, 3.0, 0.46, 0.03, 0.008, phase=1.0)
    G = piece("G2Moss", "Torso", "fur", "Moss")
    fur(G, T, Vector((0, 0, 3.95)), Vector((1.0, 0.55, 0.08)), 420, 0.14, 0.045, Vector((0, 0, -0.2)), keep=arm_gap,
        curve=(0.1, 0.3), nu=3, nv=1)
    G = piece("G2Nails", "Torso", "horn", "Iron")
    for x, z in ((-0.6, 3.5), (0.5, 3.1), (-0.2, 2.8)):
        p = project(T, Vector((x, 1, z)), BK, 0.06)
        tube(G, [p + Vector((0, -0.08, 0)), p + Vector((0, 0.12, 0.03))], [0.022, 0.02], sides=5, tile=TILE["horn"])
        tube(G, [p + Vector((0, 0.12, 0.03)), p + Vector((0, 0.15, 0.035))], [0.06, 0.06], sides=8, tile=TILE["horn"])

    # ---- R1 Hollow Shroud: a mist capelet over the shoulders, open at the front (head clear, uniform shows)
    G = piece("R1Capelet", "Torso", "mist", "WingPalette")
    depth = max(0.5, max(abs(hit(T, Vector((x, 2, 3.7)), BK)[0].y if hit(T, Vector((x, 2, 3.7)), BK)[0] else 0.5)
                         for x in (-0.5, 0, 0.5)))
    N, S = 40, 6
    rows, uvs = [], []
    for i in range(S + 1):
        t = i / S
        row, ur = [], []
        for k in range(N + 1):
            a = 2 * math.pi * k / N
            side = abs(math.cos(a))                      # 1 at the sides (over the arms), 0 front / back
            rx = 0.95 + (1.1 * side + 0.25) * t ** 0.6
            ry = depth + 0.08 + 0.25 * t
            drop = (1.0 - 0.35 * side) * t ** 1.1 + 0.25 * side * t ** 0.5
            hem = 0.16 * t ** 2 * (math.sin(a * 7) + 0.6 * math.sin(a * 13 + 1))
            row.append(Vector((rx * math.cos(a), ry * math.sin(a), 4.08 - drop - max(0.0, hem))))
            ur.append((a * 1.2 / TILE["mist"], t * 1.1 / TILE["mist"]))
        rows.append(row); uvs.append(ur)
    b0 = len(G.v)
    for r, u in zip(rows, uvs):
        G.v += r; G.uv += u
    for i in range(S):
        for k in range(N):
            a = 2 * math.pi * (k + 0.5) / N
            if math.sin(a) > 0.55:                        # open at the front
                continue
            q = b0 + i * (N + 1) + k
            G.f.append((q, q + 1, q + N + 2, q + N + 1))

    # ---- R2 Frost Revenant: ice spikes on the shoulders, spectral chains, rime on the shins
    for sx, key, sd in ((1, "RArm", "R"), (-1, "LArm", "L")):
        G = piece(f"R2Spike{sd}", key, "ice", "None")
        for k in range(9):
            d = Vector((sx * random.uniform(0.4, 1), random.uniform(-0.6, 0.6), random.uniform(0.3, 1))).normalized()
            p = project(B[key], Vector((1.5 * sx, 0, 3.75)) + d * 0.6, -d, 0.0)
            L = random.uniform(0.25, 0.6)
            cone(G, p - d * 0.03, d, L, L * 0.2, sides=6, tile=TILE["ice"])
        lk = "RLeg" if sx > 0 else "LLeg"
        G = piece(f"R2Rime{sd}", lk, "ice", "None")
        patch(G, B[lk], Vector((0.5 * sx, 0.6, 0.6)), FW, UP, 0.8, 10, 0.01, 0.05, TILE["ice"], rng2)
    # spectral chains (dangles: rigid links on a rope, FormDangles): a swag across the chest and one across the back,
    # pinned over the shoulders; and a short chain hanging from the left wrist
    for fy in (1, -1):
        pts, nrs = [], []
        for k in range(15):
            t = k / 14
            x = -0.72 + 1.44 * t
            z = 4.0 - 0.95 * math.sin(math.pi * t) ** 1.3
            q, n = project_n(T, Vector((x, fy * 1.5, min(z, 3.96))), Vector((0, -fy, 0)), 0.06)
            if q is not None:                   # (the top edge can graze: a missed ray would leave the point in the air)
                pts.append(q); nrs.append(n)
        tops = [project_n(T, Vector((x, 0, 4.6)), DN, 0.06) for x in (-0.72, 0.72)]
        path = [tops[0][0]] + pts + [tops[1][0]]
        nrm = [tops[0][1]] + nrs + [tops[1][1]]
        nodes, nn = resample(path, nrm, LINK_STEP)
        DANG["swags"].append({"part": "Torso", "pts": [rbx(v + n * 0.02 - CENTRE["Torso"]) for v, n in zip(nodes, nn)],
                              "nrm": [rbx(n) for n in nn]})
    top = Vector((-1.5, 0.12, 2.115))
    DANG["hang"] = {"part": "Left Arm", "pts": [rbx(top + DN * (0.15 * k) - CENTRE["LArm"]) for k in range(9)]}
    return P


def head_pieces(H):
    random.seed(3)
    G = Geo()
    hc = CENTRE["Head"]
    jaw = [project(H, hc + Vector((0.45 * math.cos(a), 1, -0.32 + 0.08 * math.sin(a) ** 2)), BK, 0.04) for a in [math.pi * k / 12 for k in range(13)]]
    tube(G, jaw, [0.05] * 13, sides=6, tile=TILE["bone"])
    for k in (2, 5, 7, 10):           # teeth-like studs along the guard
        cone(G, jaw[k], BK * -1 + DN * 0.6, 0.09, 0.03, sides=5, tile=TILE["bone"])
    return {"G1Jaw": ("Head", G, "bone", "WingFinish")}


# ---------------------------------------------------------------- objects, export, fit
def to_object(name, G):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in G.v], [], G.f)
    me.update()
    uvl = me.uv_layers.new()
    for poly in me.polygons:
        for li, vi in zip(poly.loop_indices, poly.vertices):
            uvl.data[li].uv = G.uv[vi]
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def rbx(v):
    return [round(v.x, 4), round(v.z, 4), round(-v.y, 4)]


def bbox_centre(ob):
    ws = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return sum(ws, Vector()) / 8


def export(path, objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH"}, apply_unit_scale=True,
                             global_scale=0.01, axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE",
                             path_mode="STRIP", embed_textures=False, add_leaf_bones=False, bake_anim=False)


def write(fname, pieces, fit):
    objs, rec = [], {}
    for name, (part, G, mset, tint) in pieces.items():
        if not G.f:
            print(f"!! {fname} {name}: empty")
            continue
        ob = to_object(name, G)
        objs.append(ob)
        n = G.tris()
        if n > TRI_CAP:
            print(f"!! {fname} {name}: {n} tris (cap {TRI_CAP})")
        rec[name] = {"part": RBX_PART[part], "centre": rbx(bbox_centre(ob) - CENTRE[part]), "tris": n, "maps": mset, "tint": tint}
    export(os.path.join(DEST, "fbx", fname), objs)
    fit[fname] = rec
    print(f"{fname}: {len(objs)} pieces, {sum(r['tris'] for r in rec.values())} tris; "
          + ", ".join(f"{k} {v['tris']}" for k, v in rec.items()))
    return objs


# ---------------------------------------------------------------- check sheets (Cycles CPU: the GPU crashes headless)
COL = {"fur": (0.42, 0.3, 0.2, 1), "bone": (0.85, 0.8, 0.68, 1), "cloth": (0.8, 0.77, 0.66, 1), "mist": (0.45, 0.52, 0.85, 0.55),
       "ice": (0.7, 0.85, 0.95, 0.8), "horn": (0.12, 0.11, 0.13, 1), "glow": (0.85, 0.9, 1.0, 1)}
_mats = {}


def cmat(key):
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    c = COL.get(key, (0.55, 0.58, 0.66, 1))
    b.inputs["Base Color"].default_value = c
    b.inputs["Roughness"].default_value = 0.55
    if c[3] < 1:
        b.inputs["Alpha"].default_value = c[3]
    if key == "glow":
        b.inputs["Emission Color"].default_value = c
        b.inputs["Emission Strength"].default_value = 4.0
    _mats[key] = m
    return m


def sheet(body, objs, fit_rec, head_obj):
    import numpy as np
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 12
    sc.render.resolution_x, sc.render.resolution_y = 300, 420
    sc.render.film_transparent = False
    if not sc.world:
        sc.world = bpy.data.worlds.new("w")
    sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.16, 0.16, 0.18, 1)
    if "SunK" not in bpy.data.objects:
        for nm, rot, e in (("SunK", (0.9, 0.2, 0.6), 3.0), ("SunB", (1.1, 0.0, 3.6), 2.0)):
            ld = bpy.data.lights.new(nm, "SUN"); ld.energy = e
            lo = bpy.data.objects.new(nm, ld); lo.rotation_euler = rot; sc.collection.objects.link(lo)
        cd = bpy.data.cameras.new("cam"); cd.lens = 50
        co = bpy.data.objects.new("cam", cd); sc.collection.objects.link(co); sc.camera = co
    cam = bpy.data.objects["cam"]
    for b, bo in BODY_OBJS.items():
        for o in bo:
            o.hide_render = b != body
            if b == body:
                o.data.materials.clear(); o.data.materials.append(cmat("body"))
    head_obj.data.materials.clear(); head_obj.data.materials.append(cmat("body"))
    for o in objs:
        o.data.materials.clear(); o.data.materials.append(cmat(fit_rec[o.name]["maps"]))
    dirs = ["V2", "W1", "W2", "G1", "G2", "R1", "R2"]
    tiles = []
    for d in dirs:
        for o in objs:
            o.hide_render = not o.name.startswith(d)
        row = []
        for ang in (25, 180 + 25):
            a = math.radians(ang)
            cam.location = Vector((7.5 * math.sin(a), 7.5 * math.cos(a), 3.6))
            cam.rotation_euler = (Vector((0, 0, 2.6)) - cam.location).to_track_quat("-Z", "Y").to_euler()
            path = os.path.join(DEST, "check", f"_tmp.png")
            sc.render.filepath = path
            bpy.ops.render.render(write_still=True)
            im = bpy.data.images.load(path, check_existing=False)
            px = np.array(im.pixels[:]).reshape(420, 300, 4)
            bpy.data.images.remove(im)
            row.append(px)
        tiles.append(np.concatenate(row, 1))
    fronts = np.concatenate([t[:, :300] for t in tiles], 1)
    backs = np.concatenate([t[:, 300:] for t in tiles], 1)
    grid = np.concatenate([backs, fronts], 0)         # Blender rows run bottom-up: fronts on top
    h, w = grid.shape[:2]
    img = bpy.data.images.new(f"sheet_{body}", w, h)
    img.pixels.foreach_set(grid.astype(np.float32).ravel())
    img.filepath_raw = os.path.join(DEST, "check", f"body_{body}.png"); img.file_format = "PNG"; img.save()
    print("sheet", img.filepath_raw)
    for o in objs:
        o.hide_render = False


def card(taper):
    """a tatter segment, 1 x 1 (X across, Z along: top +0.5 to bottom -0.5), cupped a little along Y; taper: to a point"""
    G = Geo()
    rows, uvs = [], []
    for i in range(4):
        t = i / 3
        w = 0.5 * ((1 - t) ** 0.9 if taper else 1.0) + (0.02 if taper and i == 3 else 0.0)
        rows.append([Vector((w * s, 0.06 * (1 - s * s), 0.5 - t)) for s in (-1, 0, 1)])
        uvs.append([(0.045 * (s + 1), 0.3 * t) for s in (-1, 0, 1)])
    G.grid(rows, uvs)
    return G


def dangles():
    """NHFormDangles.fbx (import with rig OFF): Link (one chain link: long axis X, ring in X-Z), TatterSeg / TatterTip
    (cards), and every body's tatter-free arm wraps G2WrapL_<body> / G2WrapR_<body>. forms_dangles.json: per body, the
    wraps' fit, the leg reach, and every dangle's rest nodes (part-local, Roblox axes, height 1)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bodies = load_bodies()
    H = head_bvh()
    objs, out = [], {"bodies": {}}
    G = Geo()
    torus(G, Vector(), Vector((1, 0, 0)), Vector((0, 1, 0)), 0.065, 0.017, tile=TILE["horn"])
    objs.append(to_object("Link", G))
    objs.append(to_object("TatterSeg", card(False)))
    objs.append(to_object("TatterTip", card(True)))
    for b in BODY_IDS:
        P = build_body(bodies[b], H)
        rec = {"legOuter": DANG["legOuter"], "tatters": DANG["tatters"], "swags": DANG["swags"], "hang": DANG["hang"], "wraps": {}}
        for nm in ("G2WrapL", "G2WrapR"):
            part, Gw, mset, tint = P[nm]
            ob = to_object(f"{nm}_{b}", Gw)
            objs.append(ob)
            rec["wraps"][nm] = {"part": RBX_PART[part], "centre": rbx(bbox_centre(ob) - CENTRE[part]), "tris": Gw.tris()}
        out["bodies"][b] = rec
        print(b, "swag nodes", [len(w["pts"]) for w in rec["swags"]], "tatters", len(rec["tatters"]), "legOuter", rec["legOuter"],
              "wraps", {k: v["tris"] for k, v in rec["wraps"].items()})
    sizes = {o.name: [round(x, 4) for x in o.dimensions] for o in objs[:3]}
    out["meshes"] = sizes
    export(os.path.join(DEST, "fbx", "NHFormDangles.fbx"), objs)
    path = os.path.join(DEST, "forms_dangles.json")
    json.dump(out, open(path, "w"), indent=1)
    print("wrote", path, "meshes", sizes, "objects", len(objs))


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bodies = load_bodies()
    H = head_bvh()
    fit_path = os.path.join(DEST, "forms_body_fit.json")
    fit = json.load(open(fit_path)) if os.path.exists(fit_path) else {}
    for b in BODY_IDS:
        if ONLY and b not in ONLY:
            continue
        objs = write(f"NHFormBody_{b}.fbx", build_body(bodies[b], H), fit)
        if SHEET:
            sheet(b, objs, fit[f"NHFormBody_{b}.fbx"], HEAD_OBJ[0])
        for ob in objs:
            bpy.data.objects.remove(ob, do_unlink=True)
    if not ONLY or "head" in ONLY:
        for ob in write("NHFormHead.fbx", head_pieces(H), fit):
            bpy.data.objects.remove(ob, do_unlink=True)
    json.dump(fit, open(fit_path, "w"), indent=1)
    print("wrote", fit_path)


dangles() if DANGLES else main()
