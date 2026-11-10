"""Nightmare Highschool: the feminine R6 body (torso, arms, legs) as R6 CharacterMeshes.

Headless:  E:/Blender/blender.exe -b -P nh_female_body.py -- [--render] [--out E:/NH-Work/femalebody]

Geometry is in studs, in each R6 part's own space (Roblox: +x right, +y up, -z front). Blender: (x, -z, y).
- Torso fits the 2 x 2 x 1 Torso; arms and legs fit 1 x 2 x 1. Every part's bounding box is centred on
  the part (symmetric in x, y and z), so Roblox's importer can't shift the shape if it recentres meshes.
- Arms and legs keep a flat inner side flush with the body and taper only on the outside.
- UVs index Roblox's R6 CharacterMesh clothing atlas (see atlas.py), so Shirts and Pants keep working.
"""
import bpy, bmesh, math, os, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import atlas  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[argv.index("--out") + 1] if "--out" in argv else "E:/NH-Work/femalebody"
DO_RENDER = "--render" in argv
# --parts Torso,RightLeg,LeftLeg exports only those parts, to <name>.fbx (--name, default NHFemaleBody)
ONLY = argv[argv.index("--parts") + 1].split(",") if "--parts" in argv else None
FBX_NAME = argv[argv.index("--name") + 1] if "--name" in argv else "NHFemaleBody"
os.makedirs(os.path.join(OUT, "fbx"), exist_ok=True)
os.makedirs(os.path.join(OUT, "renders"), exist_ok=True)


# ---------- curves ----------
def pchip(keys):
    """monotone cubic through (x, y) keys: no overshoot, so profiles stay smooth and in bounds"""
    xs = [k[0] for k in keys]; ys = [k[1] for k in keys]
    n = len(xs)
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    dl = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    m[0], m[-1] = dl[0], dl[-1]
    for i in range(1, n - 1):
        if dl[i - 1] * dl[i] <= 0:
            m[i] = 0.0
        else:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / dl[i - 1] + w2 / dl[i])

    def f(x):
        if x <= xs[0]: return ys[0]
        if x >= xs[-1]: return ys[-1]
        i = max(j for j in range(n - 1) if xs[j] <= x)
        t = (x - xs[i]) / h[i]
        h00 = 2 * t**3 - 3 * t**2 + 1; h10 = t**3 - 2 * t**2 + t
        h01 = -2 * t**3 + 3 * t**2; h11 = t**3 - t**2
        return h00 * ys[i] + h10 * h[i] * m[i] + h01 * ys[i + 1] + h11 * h[i] * m[i + 1]
    return f


def smooth(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


# ---------- ring: rounded rectangle, walked +x -> front(-z) -> -x -> back(+z) ----------
DEPTH_CAP = 0.54  # torso half-depth limit (bust / seat peak); 0.5 is the R6 box, v2 lets the bust read a little past it
NC = 3          # segments per half corner (6 per 90 deg corner)
NX = 4          # straight segments on the x faces (sides)
NZ_T = 12       # straight segments on front/back of the torso
NZ_L = 5        # ... of a limb


def ring(hw, hd, rc, cx, nz, inner=0, rin=None):
    """inner: -1 / +1 = the side (-x / +x) that touches the body; its two corners get radius rin (near-square, like R6)"""
    def rad(sx):
        r = rin if (inner != 0 and sx == inner and rin is not None) else rc
        return min(r, hw - 1e-3, hd - 1e-3)
    rp, rm = rad(1), rad(-1)          # radius of the +x corners / -x corners
    faces = [
        [("arc", (cx + hw - rp, hd - rp), 45, 0, rp), ("line", (cx + hw, hd - rp), (cx + hw, -(hd - rp)), NX),
         ("arc", (cx + hw - rp, -(hd - rp)), 0, -45, rp)],
        [("arc", (cx + hw - rp, -(hd - rp)), -45, -90, rp), ("line", (cx + hw - rp, -hd), (cx - hw + rm, -hd), nz),
         ("arc", (cx - hw + rm, -(hd - rm)), -90, -135, rm)],
        [("arc", (cx - hw + rm, -(hd - rm)), -135, -180, rm), ("line", (cx - hw, -(hd - rm)), (cx - hw, hd - rm), NX),
         ("arc", (cx - hw + rm, hd - rm), 180, 135, rm)],
        [("arc", (cx - hw + rm, hd - rm), 135, 90, rm), ("line", (cx - hw + rm, hd), (cx + hw - rp, hd), nz),
         ("arc", (cx + hw - rp, hd - rp), 90, 45, rp)],
    ]
    pts = []
    for fi, path in enumerate(faces):
        fp = []  # (x, z, nx, nz)
        for seg in path:
            if seg[0] == "arc":
                (ccx, ccz), a0, a1, r = seg[1], seg[2], seg[3], seg[4]
                for k in range(NC + 1):
                    a = math.radians(a0 + (a1 - a0) * k / NC)
                    p = (ccx + r * math.cos(a), ccz + r * math.sin(a), math.cos(a), math.sin(a))
                    if not fp or (abs(fp[-1][0] - p[0]) > 1e-9 or abs(fp[-1][1] - p[1]) > 1e-9):
                        fp.append(p)
            else:
                (x0, z0), (x1, z1), n = seg[1], seg[2], seg[3]
                nrm = (fp[-1][2], fp[-1][3])
                for k in range(1, n):
                    t = k / n
                    fp.append((x0 + (x1 - x0) * t, z0 + (z1 - z0) * t, nrm[0], nrm[1]))
        # arc length parameter
        L = [0.0]
        for i in range(1, len(fp)):
            L.append(L[-1] + math.hypot(fp[i][0] - fp[i - 1][0], fp[i][1] - fp[i - 1][1]))
        for i, p in enumerate(fp[:-1]):           # the end point is the next face's start
            pts.append({"x": p[0], "z": p[1], "nx": p[2], "nz": p[3], "face": fi, "s": L[i] / L[-1]})
    return pts


# ---------- part definitions ----------
def torso_rings():
    hwf = pchip([(-1.0, 1.0), (-0.80, 1.0), (-0.62, 0.975), (-0.42, 0.885), (-0.20, 0.79), (0.02, 0.805),
                 (0.25, 0.90), (0.50, 0.975), (0.70, 1.0), (1.0, 1.0)])
    hdf = pchip([(-1.0, 0.475), (-0.80, 0.475), (-0.55, 0.46), (-0.20, 0.405), (0.05, 0.415), (0.30, 0.455),
                 (0.55, 0.47), (1.0, 0.47)])
    BUST, SEAT = 0.105, 0.07     # extra depth front / back (balanced below so the z extents match)
    # 2026-11-10 v2 (owner: "make the bust a little more noticeable"): 0.06 -> 0.105, clearer underside and lobes

    def bust(y, x):
        g = math.exp(-((y - 0.33) / (0.21 if y > 0.33 else 0.13)) ** 2)
        lobe = 0.50 + 0.50 * math.exp(-((abs(x) - 0.40) / 0.24) ** 2)
        return BUST * g * lobe * (1 - smooth(0.62, 0.95, abs(x)))

    def seat(y, x):
        g = math.exp(-((y + 0.70) / (0.20 if y > -0.70 else 0.15)) ** 2)
        lobe = 0.72 + 0.28 * math.exp(-((abs(x) - 0.45) / 0.30) ** 2)
        return SEAT * g * lobe * (1 - smooth(0.70, 0.98, abs(x)))

    ys = []
    # bottom bevel (r 0.05), body, soft shoulder roll (x 0.15, y 0.11, z 0.06)
    RB, RSX, RSY, RSZ = 0.05, 0.15, 0.11, 0.06
    spec = []
    for k in range(0, 4):
        th = math.radians(90 * (4 - k) / 4)      # 90 deg = the bottom ring (fully inset, y = -1)
        spec.append((-1 + RB * (1 - math.sin(th)), RB * (1 - math.cos(th)), RB * (1 - math.cos(th)), 0))
    body = [-0.95 + i * (0.95 + 0.89) / 30 for i in range(31)]
    for y in body:
        spec.append((y, 0, 0, 1))
    for k in range(1, 7):
        th = math.radians(90 * k / 6)
        spec.append((1 - RSY + RSY * math.sin(th), RSX * (1 - math.cos(th)), RSZ * (1 - math.cos(th)), 1))
    rings = []
    for y, insx, insz, _ in spec:
        hw, hd = hwf(y) - insx, hdf(y) - insz
        pts = ring(hw, hd, 0.10 if hd > 0.2 else hd * 0.5, 0.0, NZ_T)
        for p in pts:
            wf = max(0.0, -p["nz"]) ** 1.5
            wb = max(0.0, p["nz"]) ** 1.5
            p["z"] += -bust(y, p["x"]) * wf + seat(y, p["x"]) * wb
        rings.append({"y": y, "hw": hw, "hd": hd, "cx": 0.0, "pts": pts})
    return rings


def limb_rings(kind, side):
    """kind 'arm' | 'leg'; side +1 = Right (inner side is -x), -1 = Left (inner side is +x)"""
    if kind == "arm":
        hwf = pchip([(-1.0, 0.425), (-0.45, 0.445), (0.10, 0.468), (0.60, 0.492), (0.78, 0.50), (1.0, 0.50)])
        hdf = pchip([(-1.0, 0.415), (-0.30, 0.435), (0.40, 0.46), (1.0, 0.465)])
        RT, RB, RC = 0.13, 0.08, 0.10
    else:
        hwf = pchip([(-1.0, 0.44), (-0.40, 0.452), (0.30, 0.478), (0.75, 0.50), (1.0, 0.50)])
        hdf = pchip([(-1.0, 0.44), (-0.40, 0.448), (0.40, 0.468), (1.0, 0.47)])
        RT, RB, RC = 0.04, 0.05, 0.09
    # legs meet in the middle like standard R6 (owner, 2026-11-10: "I don't like how much of a gap there is"):
    # the inner corners are near-square, so the two legs touch with only a fine seam
    RIN = 0.02 if kind == "leg" else None
    spec = []
    for k in range(0, 4):
        th = math.radians(90 * (4 - k) / 4)      # bottom ring first
        spec.append((-1 + RB * (1 - math.sin(th)), RB * (1 - math.cos(th))))
    lo, hi = -1 + RB, 1 - RT
    for i in range(1, 22):
        spec.append((lo + (hi - lo) * i / 22, 0.0))
    for k in range(0, 5):
        th = math.radians(90 * k / 4)
        spec.append((1 - RT + RT * math.sin(th), RT * (1 - math.cos(th))))
    rings = []
    for y, ins in spec:
        hw_full = hwf(y)
        cx = -side * (0.5 - hw_full)       # inner face stays at -0.5 (right) / +0.5 (left)
        hw, hd = hw_full - ins, hdf(y) - ins
        rings.append({"y": y, "hw": hw, "hd": hd, "cx": cx, "pts": ring(hw, hd, RC, cx, NZ_L, -side, RIN)})
    return rings


# ---------- mesh build ----------
def build(name, rings, part):
    cu, hu, faces_v = atlas.strip_uv(part)
    hu_cap = 0.0625 if part == "Torso" else 0.03125
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    N = len(rings[0]["pts"])
    V = []
    for r in rings:
        V.append([bm.verts.new((p["x"], -p["z"], r["y"])) for p in r["pts"]])
    y0, y1 = rings[0]["y"], rings[-1]["y"]

    def side_uv(ri, j, face, s):
        yn = 2 * (rings[ri]["y"] - y0) / (y1 - y0) - 1
        v0, v1 = faces_v["RFLB"[face]]
        return (cu + hu * yn, v0 + (v1 - v0) * s)

    for i in range(len(rings) - 1):
        for j in range(N):
            jn = (j + 1) % N
            pj, pn = rings[i]["pts"][j], rings[i]["pts"][jn]
            face = pj["face"]
            s0, s1 = pj["s"], (pn["s"] if pn["face"] == face else 1.0)
            f = bm.faces.new((V[i][j], V[i][jn], V[i + 1][jn], V[i + 1][j]))
            uvs = [side_uv(i, j, face, s0), side_uv(i, jn, face, s1), side_uv(i + 1, jn, face, s1), side_uv(i + 1, j, face, s0)]
            for lp, (u, v) in zip(f.loops, uvs):
                lp[uvl].uv = (u, 1 - v)

    def cap(r, verts, which):
        ccu, ccv, _, hv = atlas.cap_uv(part, which)
        sgn = -1 if which == "U" else 1
        cx, hw, hd, y = r["cx"], r["hw"], r["hd"], r["y"]

        def uv(x, z):
            return (ccu - hu_cap * (x - cx) / hw, ccv + sgn * hv * (z / hd))
        layers = [verts]
        for fct in (0.68, 0.36):
            layers.append([bm.verts.new((cx + (p["x"] - cx) * fct, -(p["z"] * fct), y)) for p in r["pts"]])
        centre = bm.verts.new((cx, 0.0, y))

        def xz(v):
            return v.co.x, -v.co.y
        for a, b in zip(layers[:-1], layers[1:]):
            for j in range(N):
                jn = (j + 1) % N
                q = (a[j], a[jn], b[jn], b[j]) if which == "U" else (a[jn], a[j], b[j], b[jn])
                f = bm.faces.new(q)
                for lp in f.loops:
                    lp[uvl].uv = (lambda t: (t[0], 1 - t[1]))(uv(*xz(lp.vert)))
        last = layers[-1]
        for j in range(N):
            jn = (j + 1) % N
            tri = (last[j], last[jn], centre) if which == "U" else (last[jn], last[j], centre)
            f = bm.faces.new(tri)
            for lp in f.loops:
                lp[uvl].uv = (lambda t: (t[0], 1 - t[1]))(uv(*xz(lp.vert)))

    cap(rings[-1], V[-1], "U")
    cap(rings[0], V[0], "D")
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def centre_check(ob, label):
    xs = [v.co.x for v in ob.data.vertices]; ys = [v.co.y for v in ob.data.vertices]; zs = [v.co.z for v in ob.data.vertices]
    return {"part": label, "x": [round(min(xs), 4), round(max(xs), 4)], "z_front_back": [round(min(ys), 4), round(max(ys), 4)],
            "y": [round(min(zs), 4), round(max(zs), 4)], "verts": len(ob.data.vertices), "tris": sum(len(p.vertices) - 2 for p in ob.data.polygons)}


def balance_torso_depth(ob):
    """make the front and back extents equal (bbox centred in z) by nudging only the bust/seat region"""
    ys = [v.co.y for v in ob.data.vertices]
    front, back = max(ys), -min(ys)        # Blender +y is the front
    if abs(front - back) < 1e-4:
        return
    target = max(front, back)
    if front < target:   # stretch the front bulge outward
        k = (target - 0.47) / (front - 0.47)
        for v in ob.data.vertices:
            if v.co.y > 0.47:
                v.co.y = 0.47 + (v.co.y - 0.47) * k
    else:
        k = (target - 0.475) / (back - 0.475)
        for v in ob.data.vertices:
            if -v.co.y > 0.475:
                v.co.y = -(0.475 + (-v.co.y - 0.475) * k)


def main():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "NONE"
    parts = {
        "NHFem_Torso": build("NHFem_Torso", torso_rings(), "Torso"),
        "NHFem_RightArm": build("NHFem_RightArm", limb_rings("arm", 1), "RightArm"),
        "NHFem_LeftArm": build("NHFem_LeftArm", limb_rings("arm", -1), "LeftArm"),
        "NHFem_RightLeg": build("NHFem_RightLeg", limb_rings("leg", 1), "RightLeg"),
        "NHFem_LeftLeg": build("NHFem_LeftLeg", limb_rings("leg", -1), "LeftLeg"),
    }
    balance_torso_depth(parts["NHFem_Torso"])
    # keep the torso near the R6 Torso box: scale depth so the bust/seat peak is DEPTH_CAP
    tv = parts["NHFem_Torso"].data.vertices
    k = DEPTH_CAP / max(abs(v.co.y) for v in tv)
    for v in tv:
        v.co.y *= k
    report = [centre_check(ob, n) for n, ob in parts.items()]
    with open(os.path.join(OUT, "body_report.json"), "w") as fh:
        json.dump(report, fh, indent=1)
    print(json.dumps(report))
    # FBX: every part at the origin, in its own R6 part space
    bpy.ops.object.select_all(action="DESELECT")
    chosen = [ob for n, ob in parts.items() if ONLY is None or n[len("NHFem_"):] in ONLY]
    for ob in chosen:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = chosen[0]
    # Roblox's 3D importer (measured on two imports, 2026-11-10): it reads this FBX as centimetres (export at 0.01),
    # and it maps Blender -Y to the Roblox front, so turn the geometry 180 deg about Z for the export (then back).
    def turn(obs):
        for ob in obs:
            for v in ob.data.vertices:
                v.co.x, v.co.y = -v.co.x, -v.co.y
    turn(parts.values())
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, "fbx", FBX_NAME + ".fbx"), use_selection=True,
                             object_types={"MESH"}, apply_unit_scale=True, global_scale=0.01, axis_forward="-Z",
                             axis_up="Y", mesh_smooth_type="FACE", path_mode="STRIP", embed_textures=False,
                             add_leaf_bones=False, bake_anim=False)
    turn(parts.values())
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "NHFemaleBody.blend"))
    if DO_RENDER:
        import render_compare
        render_compare.run(parts, OUT)


if __name__ == "__main__":
    main()
