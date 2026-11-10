"""Nightmare Highschool: extra R6 body types (male and female variants), built as R6 CharacterMeshes.

Headless:  E:/Blender/blender.exe -b --factory-startup -P nh_body_types.py -- [--render] [--only id,id] [--fbx]

Every body is a variant of its gender's current body: male variants of the standard R6 block body, female variants
of the Female body v2 (art/characters/female/nh_female_body.py, reused here for the rings, UVs and caps).
Rules (owner: "MAKE THEM STILL RESEMBLE NORMAL R6 CHARACTER PROPORTIONS THOUGH"):
- same head, part sizes, joints and animations; widths stay inside the R6 boxes (torso 2, limbs 1);
  depth may go a little past 1 stud for chests, busts and bellies (listed per body in body_report.json)
- limbs keep a flat inner side flush with the body and reach the full box width at the top, so the mesh's bounding box
  is centred: Roblox's 3D importer re-centres every mesh on its bounding box (measured 2026-11-10 on imported props)
- UVs index Roblox's R6 CharacterMesh clothing atlas (art/characters/female/atlas.py)
"""
import bpy, math, os, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
FEM = os.path.join(HERE, "..", "female")
sys.path.insert(0, FEM)
import nh_female_body as fb   # noqa: E402  (its main() only runs when it is the script)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[argv.index("--out") + 1] if "--out" in argv else "E:/NH-Work/bodytypes"
ONLY = argv[argv.index("--only") + 1].split(",") if "--only" in argv else None
for sub in ("fbx", "renders", "upload"):
    os.makedirs(os.path.join(OUT, sub), exist_ok=True)

pchip, smooth = fb.pchip, fb.smooth


# ---------- features: bumps and grooves displaced along the ring normal ----------
def side_weight(p, side, outer_sign=1):
    nx, nz = p["nx"], p["nz"]
    if side == "front":
        return max(0.0, -nz) ** 1.5
    if side == "back":
        return max(0.0, nz) ** 1.5
    if side == "sides":
        return abs(nx) ** 1.5
    if side == "outer":
        return max(0.0, nx * outer_sign) ** 1.5
    return 1.0


def bump_amount(f, y, x):
    if y >= f["y"]:
        g = math.exp(-((y - f["y"]) / f["up"]) ** 2)
    else:
        g = math.exp(-((y - f["y"]) / f["dn"]) ** 2)
    lobes = f.get("lobes")
    if lobes:
        lw = max(math.exp(-((abs(x) - xc) / sx) ** 2) for xc, sx in lobes)
        base = f.get("base", 0.0)
        g *= base + (1 - base) * lw
    if f.get("xfade"):
        a, b = f["xfade"]
        g *= 1 - smooth(a, b, abs(x))
    return f["amp"] * g


def groove_amount(f, y, x):
    if f["groove"] == "v":        # a vertical line (the abs' centre line)
        win = smooth(f["y0"] - 0.05, f["y0"] + 0.05, y) * (1 - smooth(f["y1"] - 0.05, f["y1"] + 0.05, y))
        return f["amp"] * math.exp(-((x - f.get("x", 0.0)) / f["w"]) ** 2) * win
    if f["groove"] == "d":        # a diagonal line, mirrored left / right (collarbones, the obliques' V-lines)
        (x0, y0), (x1, y1) = f["a"], f["b"]
        ax, ay = abs(x) - x0, y - y0
        bx, by = x1 - x0, y1 - y0
        t = max(0.0, min(1.0, (ax * bx + ay * by) / (bx * bx + by * by)))
        d = math.hypot(ax - bx * t, ay - by * t)
        return f["amp"] * math.exp(-(d / f["w"]) ** 2)
    # horizontal lines (the abs' rows)
    win = 1 - smooth(f["xmax"] - 0.06, f["xmax"] + 0.02, abs(x))
    return f["amp"] * max(math.exp(-((y - yy) / f["w"]) ** 2) for yy in f["ys"]) * win


def displace(rings, feats, outer_sign=1, lx=None, xlim=None):
    """adds each feature along the point's ring normal; records front / back parts for balancing"""
    for r in rings:
        y = r["y"]
        for p in r["pts"]:
            p["z0"], p["x0"] = p["z"], p["x"]
            p["df"] = p["db"] = 0.0
            xr = (p["x"] - r["cx"]) if lx else p["x"]     # limb: x across the limb; torso: across the body
            for f in feats:
                if "groove" in f:
                    d = groove_amount(f, y, xr) * side_weight(p, f.get("side", "front"))
                else:
                    d = bump_amount(f, y, xr) * side_weight(p, f["side"], outer_sign)
                if p["nz"] < 0:
                    p["df"] += d
                else:
                    p["db"] += d
    apply_disp(rings, 1.0, 1.0, xlim)


def apply_disp(rings, kf, kb, xlim=None):
    for r in rings:
        for p in r["pts"]:
            d = p["df"] * kf + p["db"] * kb
            p["x"] = p["x0"] + p["nx"] * d
            p["z"] = p["z0"] + p["nz"] * d
            if xlim is not None:
                p["x"] = max(-xlim, min(xlim, p["x"]))


def z_extents(rings):
    zs = [p["z"] for r in rings for p in r["pts"]]
    return -min(zs), max(zs)      # front depth, back depth


def balance(rings, mode, xlim=None):
    """make the z extents equal so the importer's re-centring can't move the shape.
    stretch: grow the smaller side's features (bust vs seat); shift: move the whole part (bellies, muscles)"""
    front, back = z_extents(rings)
    if abs(front - back) < 1e-4:
        return 0.0
    if mode == "stretch":
        lo, hi = 1.0, 6.0
        for _ in range(40):
            k = (lo + hi) / 2
            apply_disp(rings, k if front < back else 1.0, k if back < front else 1.0, xlim)
            f2, b2 = z_extents(rings)
            small = f2 if front < back else b2
            big = b2 if front < back else f2
            if small < big:
                lo = k
            else:
                hi = k
        front, back = z_extents(rings)
        if abs(front - back) < 2e-3:
            return 0.0
    dz = (back - front) / 2         # move toward the shallow side: + = backwards (Roblox +z)
    for r in rings:
        for p in r["pts"]:
            p["z"] -= dz
    return dz


def depth_cap(rings, cap):
    if not cap:
        return
    front, back = z_extents(rings)
    m = max(front, back)
    if m > cap:
        k = cap / m
        for r in rings:
            for p in r["pts"]:
                p["z"] *= k


# ---------- torso / limb rings from a spec ----------
def torso_rings(t):
    hwf, hdf = pchip(t["hw"]), pchip(t["hd"])
    RB = min(t.get("rb", 0.05), 0.02)       # v3: a near-square bottom edge where the legs meet it (no leg lip showing)
    RSX, RSY, RSZ = t.get("top", (0.15, 0.11, 0.06))
    n = t.get("rings", 31)
    spec = []
    for k in range(0, 4):
        th = math.radians(90 * (4 - k) / 4)
        spec.append((-1 + RB * (1 - math.sin(th)), RB * (1 - math.cos(th)), RB * (1 - math.cos(th))))
    lo, hi = -1 + RB, 1 - RSY
    for i in range(n):
        spec.append((lo + (hi - lo) * i / (n - 1), 0.0, 0.0))
    for k in range(1, 7):
        th = math.radians(90 * k / 6)
        spec.append((1 - RSY + RSY * math.sin(th), RSX * (1 - math.cos(th)), RSZ * (1 - math.cos(th))))
    rings = []
    # v3 (owner: "I don't like that overlap in the legs from the torso"): the hips ease out to cover the tops of the legs
    # (full width, at least the legs' depth, near-square corners) over the bottom 0.28 studs, like a standard R6 torso
    leg_hd = t.get("_leg_top_hd", 0.5)
    hd_target = max(hdf(-1.0), leg_hd + 0.004)
    rc0 = t.get("rc", 0.10)

    def hips(y):
        return smooth(-0.72, -1.0, y)
    for y, ix, iz in spec:
        s = hips(y)
        hw = hwf(y) + (1.0 - hwf(y)) * s - ix
        hd = hdf(y) + max(0.0, hd_target - hdf(y)) * s - iz
        rc = rc0 + (min(rc0, 0.05) - rc0) * s
        rings.append({"y": y, "hw": hw, "hd": hd, "cx": 0.0, "pts": fb.ring(hw, hd, rc if hd > 0.2 else hd * 0.5, 0.0, t.get("nz", fb.NZ_T))})
    displace(rings, t.get("feats", []), xlim=1.0)
    dz = balance(rings, t.get("balance", "stretch"), xlim=1.0)
    depth_cap(rings, t.get("cap"))
    return rings, dz


def limb_rings(l, side):
    """side +1 = Right (inner side -x), -1 = Left. hw keys are the full width/2; the top must reach 0.5"""
    hwf, hdf = pchip(l["hw"]), pchip(l["hd"])
    RT, RB, RC, RIN = l.get("rt", 0.10), l.get("rb", 0.06), l.get("rc", 0.10), l.get("rin")
    spec = []
    for k in range(0, 4):
        th = math.radians(90 * (4 - k) / 4)
        spec.append((-1 + RB * (1 - math.sin(th)), RB * (1 - math.cos(th))))
    lo, hi = -1 + RB, 1 - RT
    n = l.get("rings", 22)
    for i in range(1, n):
        spec.append((lo + (hi - lo) * i / n, 0.0))
    for k in range(0, 5):
        th = math.radians(90 * k / 4)
        spec.append((1 - RT + RT * math.sin(th), RT * (1 - math.cos(th))))
    rings = []
    for y, ins in spec:
        hw_full = hwf(y)
        cx = -side * (0.5 - hw_full)
        hw, hd = hw_full - ins, hdf(y) - ins
        rings.append({"y": y, "hw": hw, "hd": hd, "cx": cx, "pts": fb.ring(hw, hd, RC, cx, l.get("nz", fb.NZ_L), -side, RIN)})
    displace(rings, l.get("feats", []), outer_sign=side, lx=True, xlim=0.5)
    dz = balance(rings, "shift", xlim=0.5)
    # the importer re-centres on the bounding box: the outer side must reach the box edge too (thin limbs taper away
    # from it), so widen the limb about its flat inner side until it does
    inner = -0.5 * side
    outer = max((p["x"] * side for r in rings for p in r["pts"])) * side
    if abs(outer - inner) > 1e-6 and abs(abs(outer) - 0.5) > 1e-4:
        k = (0.5 * side - inner) / (outer - inner)
        for r in rings:
            for p in r["pts"]:
                p["x"] = inner + (p["x"] - inner) * k
            r["cx"] = inner + (r["cx"] - inner) * k
            r["hw"] *= k
    return rings, dz


# ---------- the roster ----------
def F(side, y, up, dn, amp, lobes=None, base=0.0, xfade=None):
    return {"side": side, "y": y, "up": up, "dn": dn, "amp": amp, "lobes": lobes, "base": base, "xfade": xfade}


def ABS(depth, rows=(-0.02, -0.27, -0.52), w=0.035, xmax=0.30, vw=0.035, y0=-0.62, y1=0.12):
    return [{"groove": "v", "x": 0.0, "w": vw, "y0": y0, "y1": y1, "amp": -depth},
            {"groove": "h", "ys": list(rows), "w": w, "xmax": xmax, "amp": -depth * 0.85}]


def PECS(amp, y=0.46, lobe=0.42):
    return F("front", y, 0.20, 0.075, amp, [(lobe, 0.30)], 0.35, (0.80, 1.0))


def BUST(amp, y=0.33, up=0.21, dn=0.13, base=0.5):
    return F("front", y, up, dn, amp, [(0.40, 0.24)], base, (0.62, 0.95))


def SEAT(amp, y=-0.70, up=0.20, dn=0.15):
    return F("back", y, up, dn, amp, [(0.45, 0.30)], 0.72, (0.70, 0.98))


# detail helpers (2026-11-10 v2, owner: "Make the body types more detailed & exaggerated")
def STERNUM(depth, y0=0.2, y1=0.75):
    return {"groove": "v", "x": 0.0, "w": 0.03, "y0": y0, "y1": y1, "amp": -depth}


def SPINE(depth, y0=-0.85, y1=0.85):
    return {"groove": "v", "side": "back", "x": 0.0, "w": 0.035, "y0": y0, "y1": y1, "amp": -depth}


def VLINES(depth, a=(0.40, -0.42), b=(0.12, -0.96), w=0.03):
    return {"groove": "d", "a": a, "b": b, "w": w, "amp": -depth}


def COLLAR(depth, a=(0.10, 0.86), b=(0.66, 0.79), w=0.028):
    return {"groove": "d", "a": a, "b": b, "w": w, "amp": -depth}


def BLADES(amp, y=0.45):
    return F("back", y, 0.22, 0.18, amp, [(0.45, 0.24)], 0.15, (0.85, 1.0))


T_HI = {"nz": 28, "rings": 64}
L_HI = {"rings": 32}

BODIES = [
    # ---------------- male: variants of the standard R6 block body ----------------
    {"id": "lean", "name": "Lean", "gender": "Male", "build": ("Skinny", 1),
     "blurb": "skinny and wiry: a narrow waist, a sunken stomach, collarbones, thin limbs with knobby elbows and knees",
     "torso": {**T_HI, "hw": [(-1, 0.88), (-0.75, 0.87), (-0.25, 0.79), (0.15, 0.88), (0.45, 0.96), (0.7, 1.0), (1, 1.0)],
               "hd": [(-1, 0.40), (-0.3, 0.35), (0.35, 0.41), (1, 0.42)], "rc": 0.07, "top": (0.10, 0.08, 0.04), "rb": 0.04,
               "feats": [PECS(0.012), COLLAR(0.014), STERNUM(0.008), F("front", -0.22, 0.25, 0.25, -0.03, [(0.0, 0.5)], 0.4, (0.7, 0.95)),
                         SPINE(0.01), BLADES(0.018)], "balance": "shift"},
     "arm": {**L_HI, "hw": [(-1, 0.37), (-0.5, 0.385), (-0.08, 0.40), (0.25, 0.42), (0.7, 0.47), (1, 0.5)], "hd": [(-1, 0.35), (0.2, 0.39), (1, 0.42)],
             "rc": 0.08, "rt": 0.14, "rb": 0.06, "feats": [F("back", -0.06, 0.07, 0.07, 0.022)]},
     "leg": {**L_HI, "hw": [(-1, 0.38), (-0.5, 0.395), (-0.08, 0.41), (0.25, 0.43), (0.7, 0.475), (1, 0.5)], "hd": [(-1, 0.38), (1, 0.43)],
             "rc": 0.08, "rin": 0.02, "rt": 0.04, "rb": 0.05, "feats": [F("front", -0.06, 0.07, 0.08, 0.026)]}},
    {"id": "athletic", "name": "Athletic", "gender": "Male", "build": ("Conditioned", 1),
     "blurb": "a V-taper: full shoulders, a trim waist, firm pecs, a visible six-pack and V-lines, toned arms and legs",
     "torso": {**T_HI, "hw": [(-1, 0.92), (-0.7, 0.91), (-0.38, 0.86), (0.05, 0.94), (0.4, 1.0), (1, 1.0)],
               "hd": [(-1, 0.46), (-0.3, 0.43), (0.45, 0.49), (1, 0.49)], "rc": 0.07, "top": (0.10, 0.08, 0.05), "rb": 0.04,
               "feats": [PECS(0.06), STERNUM(0.012)] + ABS(0.016) + [VLINES(0.013), COLLAR(0.008), SPINE(0.012), BLADES(0.035)],
               "balance": "shift"},
     "arm": {**L_HI, "hw": [(-1, 0.42), (-0.4, 0.45), (-0.05, 0.445), (0.3, 0.48), (0.6, 0.47), (0.85, 0.5), (1, 0.5)], "hd": [(-1, 0.41), (0.3, 0.47), (1, 0.48)],
             "rc": 0.08, "rt": 0.14, "rb": 0.06,
             "feats": [F("front", 0.25, 0.2, 0.16, 0.045), F("back", 0.35, 0.22, 0.18, 0.035), F("front", -0.42, 0.16, 0.2, 0.025)]},
     "leg": {**L_HI, "hw": [(-1, 0.43), (-0.45, 0.47), (-0.1, 0.455), (0.4, 0.485), (1, 0.5)], "hd": [(-1, 0.43), (1, 0.48)],
             "rc": 0.07, "rin": 0.02, "rt": 0.03, "rb": 0.05,
             "feats": [F("front", 0.38, 0.28, 0.24, 0.04), F("back", -0.4, 0.18, 0.24, 0.05), F("front", -0.08, 0.06, 0.07, 0.012)]}},
    {"id": "muscular", "name": "Muscular", "gender": "Male", "build": ("Conditioned", 2),
     "blurb": "bodybuilder: big pecs with a deep sternum line, a deep six-pack and V-lines, broad shoulder blades, huge arms and legs",
     "torso": {**T_HI, "hw": [(-1, 0.90), (-0.7, 0.88), (-0.45, 0.83), (0.0, 0.94), (0.35, 1.0), (1, 1.0)],
               "hd": [(-1, 0.47), (-0.35, 0.44), (0.45, 0.5), (1, 0.5)], "rc": 0.07, "top": (0.10, 0.08, 0.05), "rb": 0.04,
               "feats": [F("front", 0.46, 0.21, 0.06, 0.12, [(0.42, 0.30)], 0.3, (0.82, 1.0)), STERNUM(0.024)] + ABS(0.03, w=0.04)
               + [VLINES(0.024), SPINE(0.024), BLADES(0.07), F("back", -0.25, 0.3, 0.3, 0.025, [(0.55, 0.25)], 0.0, (0.85, 1.0))],
               "balance": "shift"},
     "arm": {**L_HI, "hw": [(-1, 0.42), (-0.4, 0.47), (-0.08, 0.445), (0.28, 0.5), (0.58, 0.465), (0.82, 0.5), (1, 0.5)],
             "hd": [(-1, 0.42), (0.2, 0.5), (1, 0.5)], "rc": 0.08, "rt": 0.15, "rb": 0.06,
             "feats": [F("front", 0.26, 0.18, 0.13, 0.095), F("back", 0.36, 0.22, 0.16, 0.075), F("front", -0.4, 0.15, 0.2, 0.05),
                       F("back", -0.45, 0.15, 0.2, 0.03)]},
     "leg": {**L_HI, "hw": [(-1, 0.43), (-0.42, 0.49), (-0.1, 0.455), (0.35, 0.5), (1, 0.5)], "hd": [(-1, 0.43), (0.3, 0.5), (1, 0.5)],
             "rc": 0.07, "rin": 0.02, "rt": 0.03, "rb": 0.05,
             "feats": [F("front", 0.36, 0.26, 0.2, 0.085), F("back", -0.36, 0.16, 0.22, 0.095), F("back", 0.6, 0.25, 0.25, 0.03),
                       F("front", -0.08, 0.06, 0.07, 0.018)]}},
    {"id": "stocky", "name": "Stocky", "gender": "Male", "build": ("Heavy", 1),
     "blurb": "broad and solid: a deep barrel chest, a hunched upper back, a firm gut, thick rounded limbs and big forearms",
     "torso": {**T_HI, "hw": [(-1, 1.0), (1, 1.0)], "hd": [(-1, 0.52), (0.2, 0.55), (1, 0.53)], "rc": 0.18, "top": (0.12, 0.10, 0.07), "rb": 0.06,
               "feats": [F("front", 0.38, 0.3, 0.26, 0.07, [(0.0, 0.9)], 0.6, (0.75, 1.0)), F("front", -0.5, 0.3, 0.26, 0.09, [(0.0, 0.7)], 0.3, (0.78, 1.0)),
                         F("back", 0.5, 0.32, 0.4, 0.06, None, 0, (0.85, 1.0)), SPINE(0.008)], "balance": "shift"},
     "arm": {**L_HI, "hw": [(-1, 0.47), (-0.4, 0.5), (1, 0.5)], "hd": [(-1, 0.46), (-0.4, 0.5), (1, 0.5)], "rc": 0.16, "rt": 0.14, "rb": 0.08,
             "feats": [F("all", 0.3, 0.35, 0.3, 0.03), F("all", -0.4, 0.18, 0.22, 0.045)]},
     "leg": {**L_HI, "hw": [(-1, 0.48), (1, 0.5)], "hd": [(-1, 0.47), (1, 0.5)], "rc": 0.14, "rin": 0.02, "rt": 0.03, "rb": 0.06,
             "feats": [F("all", 0.45, 0.35, 0.3, 0.035), F("back", -0.4, 0.2, 0.25, 0.045)]}},
    {"id": "heavy", "name": "Heavy", "gender": "Male", "build": ("Heavy", 2),
     "blurb": "big and soft: a large round belly that hangs over the belt, a soft chest, back rolls, love handles, thick soft limbs",
     "torso": {**T_HI, "hw": [(-1, 0.97), (-0.6, 0.96), (-0.35, 1.0), (0.1, 0.98), (0.5, 1.0), (1, 1.0)], "hd": [(-1, 0.5), (1, 0.5)],
               "rc": 0.26, "top": (0.14, 0.11, 0.09), "rb": 0.09,
               "feats": [F("front", -0.42, 0.36, 0.2, 0.25, [(0.0, 0.75)], 0.35, (0.82, 1.0)), F("front", 0.42, 0.16, 0.1, 0.075, [(0.42, 0.28)], 0.45, (0.82, 1.0)),
                         F("back", -0.2, 0.1, 0.12, 0.045, None, 0, (0.85, 1.0)), F("back", -0.58, 0.1, 0.12, 0.05, None, 0, (0.85, 1.0)),
                         F("sides", -0.62, 0.14, 0.14, 0.04), F("back", 0.35, 0.35, 0.35, 0.03, None, 0, (0.85, 1.0))], "balance": "shift"},
     "arm": {**L_HI, "hw": [(-1, 0.46), (-0.3, 0.5), (1, 0.5)], "hd": [(-1, 0.45), (1, 0.5)], "rc": 0.24, "rt": 0.18, "rb": 0.12,
             "feats": [F("front", 0.32, 0.32, 0.3, 0.06), F("back", 0.3, 0.32, 0.3, 0.065)]},
     "leg": {**L_HI, "hw": [(-1, 0.46), (-0.3, 0.5), (1, 0.5)], "hd": [(-1, 0.46), (1, 0.5)], "rc": 0.2, "rin": 0.03, "rt": 0.03, "rb": 0.1,
             "feats": [F("front", 0.5, 0.42, 0.36, 0.06), F("back", 0.55, 0.4, 0.3, 0.055), F("all", -0.12, 0.1, 0.1, 0.02)]}},
    # ---------------- female: variants of the Female body v2 ----------------
    {"id": "petite", "name": "Petite", "gender": "Female", "build": ("Skinny", 1),
     "blurb": "slim and delicate: a tiny waist, collarbones, a small bust, very slender arms and legs",
     "torso": {**T_HI, "hw": [(-1, 0.93), (-0.8, 0.93), (-0.6, 0.90), (-0.4, 0.80), (-0.2, 0.70), (0.02, 0.72), (0.25, 0.84), (0.5, 0.95), (0.7, 0.99), (1, 0.99)],
               "hd": [(-1, 0.43), (-0.8, 0.43), (-0.55, 0.42), (-0.2, 0.35), (0.05, 0.36), (0.3, 0.41), (0.55, 0.43), (1, 0.43)],
               "rc": 0.10, "top": (0.18, 0.12, 0.06), "feats": [BUST(0.075), SEAT(0.055), COLLAR(0.012), SPINE(0.008)], "balance": "stretch", "cap": 0.5},
     "arm": {**L_HI, "hw": [(-1, 0.36), (-0.45, 0.375), (0.1, 0.40), (0.55, 0.45), (1, 0.5)], "hd": [(-1, 0.35), (1, 0.42)], "rc": 0.10, "rt": 0.15, "rb": 0.08},
     "leg": {**L_HI, "hw": [(-1, 0.38), (-0.45, 0.40), (0.1, 0.425), (0.6, 0.47), (1, 0.5)], "hd": [(-1, 0.38), (1, 0.44)], "rc": 0.09, "rin": 0.02, "rt": 0.04, "rb": 0.05,
             "feats": [F("front", -0.06, 0.06, 0.07, 0.012)]}},
    {"id": "toned", "name": "Toned", "gender": "Female", "build": ("Conditioned", 1),
     "blurb": "athletic: a firm waist with visible abs and V-lines, shoulder blades, toned shoulders, arms, quads and calves",
     "torso": {**T_HI, "hw": [(-1, 1.0), (-0.8, 1.0), (-0.6, 0.97), (-0.4, 0.89), (-0.2, 0.82), (0.02, 0.83), (0.25, 0.91), (0.5, 0.98), (0.7, 1.0), (1, 1.0)],
               "hd": [(-1, 0.47), (-0.8, 0.47), (-0.55, 0.45), (-0.2, 0.40), (0.05, 0.41), (0.3, 0.45), (0.55, 0.47), (1, 0.47)],
               "rc": 0.10, "top": (0.13, 0.10, 0.06),
               "feats": [BUST(0.10)] + ABS(0.013, rows=(-0.06, -0.3), y0=-0.52, y1=0.04) + [VLINES(0.011), SEAT(0.085), SPINE(0.01), BLADES(0.022)],
               "balance": "stretch", "cap": 0.56},
     "arm": {**L_HI, "hw": [(-1, 0.41), (-0.45, 0.44), (-0.05, 0.435), (0.3, 0.47), (0.6, 0.46), (0.85, 0.5), (1, 0.5)], "hd": [(-1, 0.40), (0.3, 0.46), (1, 0.47)],
             "rc": 0.10, "rt": 0.14, "rb": 0.08, "feats": [F("front", 0.26, 0.2, 0.15, 0.035), F("back", 0.36, 0.22, 0.17, 0.028)]},
     "leg": {**L_HI, "hw": [(-1, 0.42), (-0.42, 0.46), (-0.1, 0.45), (0.35, 0.48), (0.75, 0.5), (1, 0.5)], "hd": [(-1, 0.42), (1, 0.47)],
             "rc": 0.09, "rin": 0.02, "rt": 0.04, "rb": 0.05,
             "feats": [F("back", -0.4, 0.18, 0.24, 0.045), F("front", 0.38, 0.28, 0.22, 0.03), F("front", -0.08, 0.06, 0.07, 0.01)]}},
    {"id": "curvy", "name": "Curvy", "gender": "Female", "build": ("Heavy", 1),
     "blurb": "an exaggerated hourglass: a big bust, a tiny waist, wide full hips and seat, thick thighs",
     "torso": {**T_HI, "hw": [(-1, 1.0), (-0.5, 1.0), (-0.36, 0.9), (-0.2, 0.72), (0.02, 0.75), (0.25, 0.89), (0.5, 0.975), (0.7, 1.0), (1, 1.0)],
               "hd": [(-1, 0.5), (-0.8, 0.5), (-0.55, 0.48), (-0.2, 0.39), (0.05, 0.40), (0.3, 0.45), (0.55, 0.47), (1, 0.47)],
               "rc": 0.12, "top": (0.15, 0.11, 0.06), "feats": [BUST(0.20, dn=0.15, base=0.45), SEAT(0.17, y=-0.68, up=0.22, dn=0.16), SPINE(0.008)],
               "balance": "stretch", "cap": 0.66},
     "arm": {**L_HI, "hw": [(-1, 0.425), (-0.45, 0.445), (0.1, 0.47), (0.6, 0.492), (0.78, 0.5), (1, 0.5)], "hd": [(-1, 0.415), (-0.3, 0.435), (0.4, 0.465), (1, 0.47)],
             "rc": 0.11, "rt": 0.14, "rb": 0.08, "feats": [F("all", 0.35, 0.3, 0.3, 0.015)]},
     "leg": {**L_HI, "hw": [(-1, 0.42), (-0.5, 0.44), (-0.1, 0.49), (0.2, 0.5), (1, 0.5)], "hd": [(-1, 0.43), (-0.1, 0.48), (1, 0.5)],
             "rc": 0.11, "rin": 0.02, "rt": 0.04, "rb": 0.05,
             "feats": [F("front", 0.5, 0.36, 0.34, 0.05), F("back", 0.55, 0.32, 0.3, 0.05), F("back", -0.45, 0.2, 0.25, 0.025)]}},
    {"id": "strong", "name": "Strong", "gender": "Female", "build": ("Conditioned", 2),
     "blurb": "powerful: pecs under the bust, a deep six-pack and V-lines, broad shoulder blades, big arms, quads and calves",
     "torso": {**T_HI, "hw": [(-1, 1.0), (-0.8, 1.0), (-0.6, 0.96), (-0.4, 0.90), (-0.2, 0.86), (0.02, 0.88), (0.25, 0.95), (0.5, 1.0), (1, 1.0)],
               "hd": [(-1, 0.48), (-0.55, 0.46), (-0.2, 0.43), (0.05, 0.435), (0.3, 0.47), (0.55, 0.48), (1, 0.48)],
               "rc": 0.09, "top": (0.12, 0.09, 0.05),
               "feats": [BUST(0.085), F("front", 0.52, 0.14, 0.08, 0.04, [(0.42, 0.3)], 0.3, (0.8, 1.0)), STERNUM(0.01, y0=0.55)]
               + ABS(0.024, rows=(-0.05, -0.3, -0.53), y0=-0.63, y1=0.1, w=0.038) + [VLINES(0.02), BLADES(0.05), SPINE(0.018), SEAT(0.08)],
               "balance": "shift"},
     "arm": {**L_HI, "hw": [(-1, 0.42), (-0.4, 0.465), (-0.08, 0.44), (0.28, 0.49), (0.58, 0.465), (0.82, 0.5), (1, 0.5)], "hd": [(-1, 0.42), (0.2, 0.49), (1, 0.5)],
             "rc": 0.09, "rt": 0.15, "rb": 0.07,
             "feats": [F("front", 0.26, 0.18, 0.14, 0.07), F("back", 0.36, 0.22, 0.16, 0.055), F("front", -0.4, 0.15, 0.2, 0.035)]},
     "leg": {**L_HI, "hw": [(-1, 0.43), (-0.42, 0.48), (-0.1, 0.455), (0.35, 0.5), (1, 0.5)], "hd": [(-1, 0.43), (0.3, 0.49), (1, 0.5)],
             "rc": 0.08, "rin": 0.02, "rt": 0.04, "rb": 0.05,
             "feats": [F("front", 0.36, 0.26, 0.2, 0.065), F("back", -0.36, 0.16, 0.22, 0.075), F("front", -0.08, 0.06, 0.07, 0.014)]}},
    {"id": "plus", "name": "Plus", "gender": "Female", "build": ("Heavy", 2),
     "blurb": "full-figured: a big soft belly, a large bust and seat, back rolls, wide soft arms and thick thighs",
     "torso": {**T_HI, "hw": [(-1, 1.0), (-0.6, 0.97), (-0.35, 1.0), (0.1, 0.98), (0.4, 1.0), (1, 1.0)],
               "hd": [(-1, 0.48), (-0.5, 0.47), (0.0, 0.46), (0.3, 0.47), (1, 0.47)], "rc": 0.22, "top": (0.15, 0.11, 0.08), "rb": 0.08,
               "feats": [BUST(0.19, dn=0.15, base=0.6), F("front", -0.45, 0.3, 0.2, 0.17, [(0.0, 0.7)], 0.35, (0.82, 1.0)), SEAT(0.15),
                         F("back", -0.15, 0.1, 0.12, 0.035, None, 0, (0.85, 1.0)), F("sides", -0.55, 0.14, 0.14, 0.03)],
               "balance": "shift"},
     "arm": {**L_HI, "hw": [(-1, 0.45), (-0.4, 0.475), (0.3, 0.5), (1, 0.5)], "hd": [(-1, 0.44), (1, 0.5)], "rc": 0.2, "rt": 0.16, "rb": 0.1,
             "feats": [F("front", 0.32, 0.32, 0.3, 0.05), F("back", 0.3, 0.32, 0.3, 0.06)]},
     "leg": {**L_HI, "hw": [(-1, 0.45), (-0.4, 0.48), (0.1, 0.5), (1, 0.5)], "hd": [(-1, 0.45), (1, 0.5)], "rc": 0.18, "rin": 0.03, "rt": 0.04, "rb": 0.08,
             "feats": [F("front", 0.5, 0.42, 0.36, 0.06), F("back", 0.55, 0.4, 0.3, 0.06), F("all", -0.12, 0.1, 0.1, 0.018)]}},
]


PARTS = (("Torso", None), ("RightArm", 1), ("LeftArm", -1), ("RightLeg", 1), ("LeftLeg", -1))


# v3 (owner: "fix the shoulder areas looking like shoulderpads", "make it look less cartoony"): arms and legs taper
# smoothly from the top (no full-width cap that steps in), muscle comes from front / back mass instead of width dips
LIMBS_V3 = {
    "lean":     {"arm": [(1, 0.5), (0.5, 0.45), (-0.2, 0.41), (-1, 0.37)], "leg": [(1, 0.5), (0.75, 0.49), (0.2, 0.44), (-0.4, 0.41), (-1, 0.39)]},
    "athletic": {"arm": [(1, 0.5), (0.4, 0.48), (-0.2, 0.455), (-1, 0.42)], "leg": [(1, 0.5), (0.6, 0.49), (-0.1, 0.465), (-0.45, 0.47), (-1, 0.44)]},
    "muscular": {"arm": [(1, 0.5), (0.3, 0.495), (-0.2, 0.475), (-1, 0.44)], "leg": [(1, 0.5), (0.5, 0.5), (-0.1, 0.47), (-0.42, 0.485), (-1, 0.45)]},
    "stocky":   {"arm": [(1, 0.5), (-1, 0.48)], "leg": [(1, 0.5), (-1, 0.48)]},
    "heavy":    {"arm": [(1, 0.5), (-1, 0.47)], "leg": [(1, 0.5), (-1, 0.47)]},
    "petite":   {"arm": [(1, 0.5), (0.5, 0.445), (-0.2, 0.40), (-1, 0.36)], "leg": [(1, 0.5), (0.75, 0.49), (0.1, 0.44), (-1, 0.395)]},
    "toned":    {"arm": [(1, 0.5), (0.4, 0.475), (-0.2, 0.445), (-1, 0.41)], "leg": [(1, 0.5), (0.6, 0.49), (-0.1, 0.46), (-0.42, 0.465), (-1, 0.43)]},
    "curvy":    {"arm": [(1, 0.5), (0.78, 0.5), (0.6, 0.492), (0.1, 0.468), (-0.45, 0.445), (-1, 0.425)],
                 "leg": [(1, 0.5), (0.2, 0.5), (-0.1, 0.49), (-0.5, 0.45), (-1, 0.43)]},
    "strong":   {"arm": [(1, 0.5), (0.3, 0.49), (-0.2, 0.465), (-1, 0.43)], "leg": [(1, 0.5), (0.5, 0.5), (-0.1, 0.465), (-0.42, 0.48), (-1, 0.44)]},
    "plus":     {"arm": [(1, 0.5), (-1, 0.46)], "leg": [(1, 0.5), (0.1, 0.5), (-0.4, 0.48), (-1, 0.46)]},
}


def tone(feats, k_bump=0.72, k_groove=0.6, w_scale=1.3, min_edge=0.13):
    """v3 realism pass: shallower, softer features; no hard shelf under a bust, belly or seat"""
    out = []
    for f in feats:
        g = dict(f)
        if "groove" in g:
            g["amp"] *= k_groove
            g["w"] *= w_scale
        else:
            g["amp"] *= k_bump
            if g["side"] in ("front", "back") and abs(g["amp"]) > 0.02:
                g["dn"], g["up"] = max(g["dn"], min_edge), max(g["up"], min_edge)
            if g["side"] == "back" and g["y"] < -0.5 and g["amp"] > 0.04:
                # a seat that is still full at the torso's bottom edge reads as a shelf (the legs are separate parts):
                # sit it higher and let it fade out before the hip joint
                g["y"], g["dn"] = g["y"] + 0.1, max(g["dn"], 0.2)
        out.append(g)
    return out


def v3(b):
    import copy
    b = copy.deepcopy(b)
    lim = LIMBS_V3.get(b["id"])
    for k in ("arm", "leg"):
        if lim:
            b[k]["hw"] = sorted(lim[k])        # pchip needs the keys in ascending y
        b[k]["rt"] = 0.10 if k == "arm" else 0.02     # a soft deltoid, a square hip joint
        b[k]["feats"] = tone(b[k].get("feats", []))
    b["torso"]["feats"] = tone(b["torso"].get("feats", []))
    b["torso"]["_leg_top_hd"] = pchip(b["leg"]["hd"])(1.0)
    return b


def build_body(b):
    b = v3(b)
    objs, report = {}, {"id": b["id"], "name": b["name"], "gender": b["gender"]}
    for part, side in PARTS:
        if part == "Torso":
            rings, dz = torso_rings(b["torso"])
        else:
            rings, dz = limb_rings(b["arm" if "Arm" in part else "leg"], side)
        name = f"NHBody_{b['id']}_{part}"
        ob = fb.build(name, rings, part)
        objs[part] = ob
        c = fb.centre_check(ob, part)
        c["shift_z"] = round(dz, 4)
        report[part] = c
    return objs, report


def current_bodies():
    """the current male (standard R6, boxes in the renders) and the Female body v2 (rebuilt from its own script)"""
    fem = {}
    tr = fb.torso_rings()
    fem["Torso"] = fb.build("NHBody_female_Torso", tr, "Torso")
    fb.balance_torso_depth(fem["Torso"])
    tv = fem["Torso"].data.vertices
    k = fb.DEPTH_CAP / max(abs(v.co.y) for v in tv)
    for v in tv:
        v.co.y *= k
    for part, side in PARTS[1:]:
        fem[part] = fb.build(f"NHBody_female_{part}", fb.limb_rings("arm" if "Arm" in part else "leg", side), part)
    return fem


def export(objs, name):
    """FBX for the owner's Studio import: 0.01 scale (the importer reads cm) and the geometry turned so Blender -Y is front"""
    obs = list(objs.values())
    for ob in obs:
        for v in ob.data.vertices:
            v.co.x, v.co.y = -v.co.x, -v.co.y
    bpy.ops.object.select_all(action="DESELECT")
    for ob in obs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, "fbx", name + ".fbx"), use_selection=True, object_types={"MESH"},
                             apply_unit_scale=True, global_scale=0.01, axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE",
                             path_mode="STRIP", embed_textures=False, add_leaf_bones=False, bake_anim=False)
    for ob in obs:
        for v in ob.data.vertices:
            v.co.x, v.co.y = -v.co.x, -v.co.y


def main():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.context.scene.unit_settings.system = "NONE"
    built, reports = {}, []
    for b in BODIES:
        if ONLY and b["id"] not in ONLY:
            continue
        objs, rep = build_body(b)
        built[b["id"]] = objs
        reports.append(rep)
    with open(os.path.join(OUT, "body_report.json"), "w") as fh:
        json.dump(reports, fh, indent=1)
    print("REPORT " + json.dumps([{"id": r["id"], **{p: [r[p]["x"], r[p]["z_front_back"], r[p]["y"], r[p]["shift_z"]] for p, _ in PARTS}} for r in reports]))
    if "--fbx" in argv:
        allobjs = {f"{i}_{p}": ob for i, objs in built.items() for p, ob in objs.items()}
        export(allobjs, "NHBodyTypes")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "NHBodyTypes.blend"))
    if "--render" in argv:
        sys.path.insert(0, HERE)
        import render_lineup
        render_lineup.run(built, current_bodies(), BODIES, OUT)


if __name__ == "__main__":
    main()
