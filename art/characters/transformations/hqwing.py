"""High-quality, animatable, customizable wings and horns for NH transformation concepts.

WINGS: one jointed skeleton (humerus, forearm, digits with knuckles, no thumb or tip hooks) drives every style. Each style is a set of parts
generated from the skeleton for a pose (fold, flap angle, digit lag, cycle time), always with the same topology, so an animation
is one shape key per frame: flaps, folds, ripples and the digits' follow-through are real geometry.
  nocturne   bat: 4 digits, scalloped membrane, raised veins, rim, a healed notch
  wyrm       drake: 3 long digits, thick bones, spikes on the leading edge
  tattered   bat torn deep in every panel
  fallen     raven feathers: primaries, secondaries and two rows of coverts, iridescent
  ossuary    bones only, with grave-cloth tatters hanging between the digits
  wraithveil spectral: a rippling mist membrane, wisps trailing from every tip
  rime       ice: an ice membrane and shards growing along the bones
HORNS (horns()): ram, demon, wendigo, thorn, broken, sovereign, bull; ridged (annulated) and twisted, with a tip finish.
Customization: PALETTES (membrane / feather colour), FINISHES (bone, horn, tip), size, style. Each is one Look option.
"""
import bpy, math, random
from mathutils import Vector, Matrix


# ---------------------------------------------------------------- geometry primitives (fixed topology)
def _frames(pts):
    T = []
    for i in range(len(pts)):
        a = pts[max(i - 1, 0)]; b = pts[min(i + 1, len(pts) - 1)]
        T.append((b - a).normalized() if (b - a).length > 1e-9 else Vector((0, 0, 1)))
    n = T[0].orthogonal().normalized()
    N = [n]
    for i in range(1, len(T)):
        axis = T[i - 1].cross(T[i])
        if axis.length > 1e-6:
            ang = math.acos(max(-1, min(1, T[i - 1].dot(T[i]))))
            n = (Matrix.Rotation(ang, 3, axis.normalized()) @ n).normalized()
        N.append(n)
    return T, N


def tube_mesh(pts, radii, seg=10, flat=1.0, base=0, twist=0.0):
    T, N = _frames(pts)
    verts, faces = [], []
    for i, p in enumerate(pts):
        b = T[i].cross(N[i]).normalized()
        tw = twist * i / max(len(pts) - 1, 1)
        for k in range(seg):
            a = 2 * math.pi * k / seg + tw
            verts.append(p + N[i] * (math.cos(a) * radii[i]) + b * (math.sin(a) * radii[i] * flat))
    for i in range(len(pts) - 1):
        for k in range(seg):
            a = base + i * seg + k; b2 = base + i * seg + (k + 1) % seg
            faces.append((a, b2, b2 + seg, a + seg))
    c0 = base + len(verts); verts.append(pts[0] - T[0] * radii[0] * 0.3)
    c1 = base + len(verts); verts.append(pts[-1] + T[-1] * max(radii[-1], 1e-4) * 0.3)
    L = base + (len(pts) - 1) * seg
    for k in range(seg):
        faces.append((c0, base + (k + 1) % seg, base + k))
        faces.append((c1, L + k, L + (k + 1) % seg))
    return verts, faces


def blade_mesh(base_p, along, across, normal, length, width, base=0, nu=8, nv=4, vane_curve=0.04, tip=0.0, asym=0.3):
    """A feather (or shard) blade: a pointed vane with a raised rachis down the middle, curved along its length."""
    along, across, normal = along.normalized(), across.normalized(), normal.normalized()
    verts, faces = [], []
    for i in range(nu + 1):
        t = i / nu
        w = width * (math.sin(math.pi * min(1.0, t * 1.05)) ** 0.6) * (1 - 0.55 * t ** 2)
        for j in range(nv + 1):
            s = j / nv * 2 - 1
            ww = w * (1 + asym * 0.5) if s > 0 else w * (1 - asym * 0.5)
            ridge = 0.018 * width / 0.12 * (1 - abs(s)) ** 3
            p = base_p + along * (length * t) + across * (ww * s) + normal * (vane_curve * length * t * t + ridge + tip * t ** 4)
            verts.append(p)
    for i in range(nu):
        for j in range(nv):
            a = base + i * (nv + 1) + j
            faces.append((a, a + nv + 1, a + nv + 2, a + 1))
    return verts, faces


def cone_mesh(base_p, dirn, length, r, base=0, seg=6, twist=0.0):
    d = dirn.normalized(); n = d.orthogonal().normalized(); b = d.cross(n)
    verts = []
    for k in range(seg):
        a = 2 * math.pi * k / seg + twist
        verts.append(base_p + (n * math.cos(a) + b * math.sin(a)) * r)
    verts.append(base_p + d * length)
    verts.append(base_p - d * r * 0.2)
    faces = [(base + k, base + (k + 1) % seg, base + seg) for k in range(seg)]
    faces += [(base + (k + 1) % seg, base + k, base + seg + 1) for k in range(seg)]
    return verts, faces


def bezier(p0, p1, p2, n):
    return [p0 * (1 - t) ** 2 + p1 * 2 * t * (1 - t) + p2 * t * t for t in [i / (n - 1) for i in range(n)]]


def resample(poly, n):
    L = [0.0]
    for i in range(1, len(poly)):
        L.append(L[-1] + (poly[i] - poly[i - 1]).length)
    out = []
    for j in range(n):
        s = L[-1] * j / (n - 1)
        k = 0
        while k < len(L) - 2 and L[k + 1] < s:
            k += 1
        seg = max(L[k + 1] - L[k], 1e-9)
        t = (s - L[k]) / seg
        out.append(poly[k] * (1 - t) + poly[k + 1] * t)
    return out


def lerp(a, b, t):
    return a + (b - a) * t


class Part:
    def __init__(self):
        self.v, self.f = [], []

    def add(self, vf):
        v, f = vf
        self.v += v; self.f += f

    def base(self):
        return len(self.v)


# ---------------------------------------------------------------- wings
STYLES = {
    "nocturne":   {"digits": 4, "membrane": True, "veins": True, "notches": [(1, 0.62, 0.08)]},
    "wyrm":       {"digits": 3, "membrane": True, "veins": True, "spikes": True, "notches": [], "thick": 1.45, "forearm": 1.55},
    "tattered":   {"digits": 4, "membrane": True, "veins": True, "notches": [(k, v, d) for k in range(4) for v, d in ((0.3, 0.24), (0.7, 0.34))]},
    "fallen":     {"digits": 3, "membrane": False, "feathers": True, "notches": []},
    "ossuary":    {"digits": 4, "membrane": False, "tatters": True, "notches": [], "thick": 1.2},
    "wraithveil": {"digits": 4, "membrane": True, "wisps": True, "notches": [(k, 0.5, 0.18) for k in range(4)]},
    "rime":       {"digits": 3, "membrane": True, "shards": True, "notches": [], "forearm": 1.45},
}


class Wing:
    NU, NV = 14, 7

    def __init__(self, sx, root, size=1.0, style="nocturne", body_drop=1.7, seed=3):
        self.sx, self.root, self.s, self.style, self.drop = sx, Vector(root), size, style, body_drop
        self.cfg = STYLES[style]
        self.digits = self.cfg["digits"]
        self.notches = self.cfg.get("notches", [])
        self.seed = seed

    def skeleton(self, fold, flap, lag):
        sx, s = self.sx, self.s
        out, up, back = Vector((sx, 0, 0)), Vector((0, 0, 1)), Vector((0, -1, 0))

        def d(elev, bk):
            a = math.radians(elev)
            return (out * math.cos(a) + up * math.sin(a) + back * bk).normalized()
        R = self.root
        hum = d(lerp(42, 72, fold), lerp(0.35, 0.75, fold))
        E = R + hum * 0.85 * s
        fore = d(lerp(14, -105, fold), lerp(0.25, 0.45, fold))
        W = E + fore * self.cfg.get("forearm", 1.3) * s
        if self.digits == 4:
            el = [52, 18, -18, -52]; ln = [1.75, 2.1, 1.85, 1.45]; bk = [0.12, 0.18, 0.24, 0.3]
        else:
            el = [44, -6, -48]; ln = [2.15, 2.35, 1.75]; bk = [0.14, 0.22, 0.3]
        digits = []
        for k in range(self.digits):
            e = lerp(el[k], -98 - 4 * k, fold)
            lagk = lag * (0.5 + 0.5 * k / max(self.digits - 1, 1))
            dir1 = d(e + lagk * 0.6, lerp(bk[k], 0.5, fold))
            dir2 = d(e - 9 - k * 3 + lagk, lerp(bk[k] + 0.08, 0.55, fold))
            K = W + dir1 * ln[k] * 0.48 * s
            Tp = K + dir2 * ln[k] * 0.52 * s
            digits.append((K, Tp))
        thumb = W + d(lerp(70, 10, fold), 0.1) * 0.22 * s
        rot = Matrix.Rotation(math.radians(flap) * sx, 3, Vector((0, 1, 0)))
        def F(p): return R + rot @ (p - R)
        body = [R + Vector((sx * 0.06 * t, -0.04, -self.drop * t)) for t in (0, 0.25, 0.5, 0.75, 1.0)]
        return {"R": R, "E": F(E), "W": F(W), "digits": [(F(K), F(T)) for K, T in digits], "thumb": F(thumb), "body": body,
                "out": rot @ out, "up": rot @ up, "back": back}

    def geom(self, fold=0.0, flap=0.0, lag=0.0, t=0.0):
        rnd = random.Random(self.seed)
        S = self.skeleton(fold, flap, lag)
        R, E, W, Dg, body = S["R"], S["E"], S["W"], S["digits"], S["body"]
        s, sx, cfg = self.s, self.sx, self.cfg
        th = cfg.get("thick", 1.0)
        P = {}
        bones = Part()
        bones.add(tube_mesh(bezier(R, lerp(R, E, 0.5) + Vector((0, -0.05, 0.03)), E, 7),
                            [x * th * s for x in (0.11, 0.1, 0.085, 0.08, 0.085, 0.095, 0.1)], seg=12, base=bones.base()))
        bones.add(tube_mesh(bezier(E, lerp(E, W, 0.5) + Vector((0, -0.04, 0)), W, 8),
                            [x * th * s for x in (0.1, 0.08, 0.065, 0.06, 0.058, 0.06, 0.068, 0.075)], seg=12, base=bones.base()))
        for K, T in Dg:
            r = [0.06, 0.05, 0.042, 0.038, 0.048, 0.034, 0.026, 0.018, 0.008]
            bones.add(tube_mesh(bezier(W, K, T, 9), [x * th * s for x in r], seg=12, base=bones.base()))
        # (owner 2026-11-23: no thumb or fingertip hooks on any wing)
        P["bones"] = bones
        rails = [resample([W, K, T], self.NU + 1) for K, T in Dg]
        main_a = resample([R, E, W, Dg[-1][0], Dg[-1][1]], self.NU + 1)
        main_b = resample(body, self.NU + 1)
        panels = [(rails[k], rails[k + 1], W) for k in range(len(rails) - 1)] + [(main_a, main_b, E)]
        if cfg.get("membrane"):
            mem, veins, rim = Part(), Part(), Part()
            for pi_, (A, B, pull) in enumerate(panels):
                base = len(mem.v)
                tipA, tipB = A[-1], B[-1]
                depth = 0.36 * (tipA - tipB).length
                for i in range(self.NU + 1):
                    u = i / self.NU
                    for j in range(self.NV + 1):
                        v = j / self.NV
                        p = lerp(A[i], B[i], v)
                        mid = lerp(tipA, tipB, 0.5)
                        sag = depth * math.sin(math.pi * v) * u ** 3
                        notch = 0.0
                        for (np_, nv_, nd_) in self.notches:
                            if np_ == pi_ and abs(v - nv_) < 0.09 and u > 0.7:
                                notch = max(notch, nd_ * s * (1 - abs(v - nv_) / 0.09) * ((u - 0.7) / 0.3) ** 1.5)
                        p = p + (pull - mid).normalized() * (sag + notch)
                        bil = 0.05 * s * math.sin(math.pi * v) * math.sin(math.pi * u)
                        if self.style == "wraithveil":
                            bil += 0.07 * s * math.sin(math.pi * v) * math.sin(6 * u + 2 * math.pi * t + pi_)
                        p = p + S["back"] * bil
                        mem.v.append(p)
                for i in range(self.NU):
                    for j in range(self.NV):
                        a = base + i * (self.NV + 1) + j
                        mem.f.append((a, a + self.NV + 1, a + self.NV + 2, a + 1))
                if cfg.get("veins"):
                    for vv in (0.33, 0.66):
                        line = [mem.v[base + i * (self.NV + 1) + int(vv * self.NV)] + Vector((0, -0.006, 0)) for i in range(2, self.NU + 1)]
                        veins.add(tube_mesh(line, [0.009 * s] * len(line), seg=6, base=veins.base()))
                edge = [mem.v[base + self.NU * (self.NV + 1) + j] for j in range(self.NV + 1)]
                rim.add(tube_mesh(edge, [0.012 * s] * len(edge), seg=6, base=rim.base()))
            P["membrane"] = mem
            if cfg.get("veins"):
                P["veins"] = veins
            P["rim"] = rim
        if cfg.get("spikes"):
            sp = Part()
            lead = resample([R, E, W, Dg[0][0]], 9)
            for i, p in enumerate(lead[1:-1]):
                L = (0.24 + 0.12 * math.sin(i * 1.3)) * s
                sp.add(cone_mesh(p, S["up"] * 0.8 + S["back"] * 0.6, L, 0.065 * s, base=sp.base()))
            P["spikes"] = sp
        if cfg.get("shards"):
            sh = Part()
            for K, T in Dg:
                for i, p in enumerate(resample([W, K, T], 7)[1:-1]):
                    for kk in range(2):
                        dv = (S["up"] * rnd.uniform(0.3, 1) + S["back"] * rnd.uniform(-0.6, 0.9) + S["out"] * rnd.uniform(-0.3, 0.5)).normalized()
                        sh.add(cone_mesh(p, dv, rnd.uniform(0.15, 0.42) * s, rnd.uniform(0.03, 0.06) * s, base=sh.base(), twist=rnd.uniform(0, 1)))
            for i, p in enumerate(resample([R, E, W], 7)[1:]):
                dv = (S["up"] + S["back"] * 0.5).normalized()
                sh.add(cone_mesh(p, dv, rnd.uniform(0.3, 0.55) * s, 0.06 * s, base=sh.base()))
            P["shards"] = sh
        if cfg.get("feathers"):
            fp = Part(); cv = Part()
            down = -S["up"]
            hand = resample([W, Dg[0][0], Dg[0][1]], 15)
            arm_line = resample([R, E, W], 17)
            bk = S["back"]
            def acr(al):
                return bk.cross(al).normalized()
            for i, p in enumerate(hand[:-1]):          # primaries: long, fanning from along the hand to down-and-out
                f = i / 13
                along = (S["out"] * (0.3 + 0.7 * f) + down * (1 - f) * 1.0).normalized()
                L = (1.35 + 0.85 * f) * s
                fp.add(blade_mesh(p + bk * (0.012 * i), along, acr(along), bk, L, 0.2 * s, base=fp.base(),
                                  vane_curve=0.05 + 0.025 * math.sin(2 * math.pi * t + f * 2), asym=0.5))
            for i, p in enumerate(arm_line[1:]):        # secondaries and tertials
                f = i / 15
                along = (down * 1.0 + S["out"] * (0.05 + 0.3 * f)).normalized()
                L = (1.05 + 0.4 * f) * s
                fp.add(blade_mesh(p + bk * (0.02 + 0.008 * i), along, acr(along), bk, L, 0.19 * s, base=fp.base(), vane_curve=0.06, asym=0.4))
            for row, (ln, off) in enumerate(((0.7, 0.06), (0.45, 0.1), (0.26, 0.13))):   # three rows of coverts
                for i, p in enumerate(resample([R, E, W, Dg[0][0]], 20)[1:]):
                    f = i / 18
                    along = (down * 0.9 + S["out"] * (0.15 + 0.55 * f)).normalized()
                    cv.add(blade_mesh(p + bk * (off + 0.004 * i), along, acr(along), bk, ln * s * (0.85 + 0.35 * f), 0.15 * s, base=cv.base(), vane_curve=0.09))
            P["feathers"] = fp
            P["coverts"] = cv
        if cfg.get("tatters"):
            ta = Part()
            for pi_, (A, B, pull) in enumerate(panels):
                for q in range(3):
                    u = 0.35 + 0.22 * q
                    a = A[int(u * self.NU)]; b = B[int(u * self.NU)]
                    top = lerp(a, b, 0.3 + 0.2 * q)
                    strip = []
                    for k in range(6):
                        sway = 0.12 * s * math.sin(2 * math.pi * t + q + pi_ + k * 0.5) * k / 5
                        strip.append(top + Vector((0, 0, -0.22 * s * k)) + S["back"] * sway)
                    w = (b - a).normalized() * 0.08 * s
                    base = ta.base()
                    for k, p in enumerate(strip):
                        ww = 1 - 0.5 * k / 5
                        ta.v += [p - w * ww, p + w * ww]
                    ta.f += [(base + k * 2, base + k * 2 + 2, base + k * 2 + 3, base + k * 2 + 1) for k in range(5)]
            P["tatters"] = ta
        if cfg.get("wisps"):
            wi = Part()
            for K, T in Dg:
                pts = [T + (T - K).normalized() * 0.15 * s * k + Vector((0, -0.12 * s * k, -0.05 * s * k)) + S["back"] * 0.08 * s * math.sin(2 * math.pi * t + k) for k in range(8)]
                wi.add(tube_mesh(pts, [0.035 * s * (1 - k / 8) + 0.003 for k in range(8)], seg=8, base=wi.base(), flat=0.35))
            P["wisps"] = wi
        return P

    def build(self, name, mats, mesh_obj, add_mods, pose=(0.0, 0.0, 0.0, 0.0)):
        P = self.geom(*pose)
        self.objs = {}
        thick = {"membrane": 0.014, "feathers": 0.008, "coverts": 0.008, "tatters": 0.01}
        for key, part in P.items():
            m = mats.get(key) or mats["bone"]
            ob = mesh_obj(f"{name}_{key}", part.v, part.f, m)
            add_mods(ob, thick=thick.get(key, 0.0), subd=1)
            self.objs[key] = ob
        return list(self.objs.values())

    def frame_verts(self, pose):
        return {k: p.v for k, p in self.geom(*pose).items()}


def animate_shapes(obj_frames, n_frames, start=1):
    for ob, frames in obj_frames.items():
        if not ob.data.shape_keys:
            ob.shape_key_add(name="Basis", from_mix=False)
        mw_inv = ob.matrix_world.inverted()
        keys = []
        for i, vs in enumerate(frames):
            k = ob.shape_key_add(name=f"F{i}", from_mix=False)
            for vi, p in enumerate(vs):
                k.data[vi].co = mw_inv @ p
            keys.append(k)
        for i, k in enumerate(keys):
            f = start + i
            for ff, val in ((f - 1, 0.0), (f, 1.0), (f + 1, 0.0)):
                k.value = val
                k.keyframe_insert("value", frame=ff)
            k.value = 0.0


# ---------------------------------------------------------------- horns
def _horn_path(base, out, up, fwd, kind, length):
    pts = []
    n = 16
    for i in range(n):
        t = i / (n - 1)
        if kind == "ram":
            a = t * math.pi * 2.1
            r = length * 0.36 * (1 - 0.42 * t)
            p = base + up * (r * math.sin(a)) + (-fwd) * (r * (1 - math.cos(a)) * 0.9) + out * (length * 0.3 * t ** 0.8)
        elif kind == "demon":
            p = base + up * (length * (0.35 * t + 0.12 * t * t)) + (-fwd) * (length * 0.85 * t ** 1.3) + out * (length * 0.18 * t)
        elif kind == "bull":
            p = base + out * (length * 0.55 * t) + fwd * (length * 0.45 * t ** 2) + up * (length * 0.35 * t ** 2.2)
        elif kind == "sovereign":
            p = base + up * (length * 0.95 * t) + (-fwd) * (length * 0.22 * math.sin(math.pi * t)) + out * (length * 0.2 * t - 0.05 * math.sin(2 * math.pi * t))
        elif kind == "broken":
            tt = t * 0.55
            p = base + up * (length * (0.35 * tt + 0.12 * tt * tt)) + (-fwd) * (length * 0.85 * tt ** 1.3) + out * (length * 0.18 * tt)
        else:
            p = base + up * (length * t)
        pts.append(p)
    return pts


def horns(kind, centre, s=1.0, rings=9, twist=1.4, seed=5):
    """{part: (verts, faces)}: 'horn' (ridged, twisted, tapered), 'tip' (the tip finish) and, for sovereign, 'halo'.
    centre: the R6 head centre (rest pose; the rig faces +Y). Fitted to the R6 head (1.2 studs at scale 1)."""
    rnd = random.Random(seed)
    parts = {"horn": Part(), "tip": Part()}
    up, fwd = Vector((0, 0, 1)), Vector((0, 1, 0))
    H = parts["horn"]
    if kind == "thorn":
        for k in range(13):
            a = math.pi * (0.1 + 0.8 * k / 12)
            p = centre + Vector((0.62 * math.cos(a), 0.25 - 0.55 * math.sin(a), 0.5))
            L = (0.35 + 0.35 * (1 - abs(k - 6) / 6)) * s
            dv = (up + Vector((math.cos(a) * 0.35, -0.2, 0))).normalized()
            pts = [p + dv * L * t + Vector((0, 0, 0.04 * math.sin(math.pi * t))) for t in [i / 6 for i in range(7)]]
            H.add(tube_mesh(pts, [0.06 * s * (1 - t * 0.95) for t in [i / 6 for i in range(7)]], seg=8, base=H.base(), twist=0.6))
        ring = [centre + Vector((0.66 * math.cos(a), 0.1 - 0.59 * math.sin(a), 0.46)) for a in [math.pi * k / 20 for k in range(21)]]
        H.add(tube_mesh(ring, [0.05 * s] * len(ring), seg=8, base=H.base(), twist=8))
    elif kind == "wendigo":
        for sx in (-1, 1):
            out = Vector((sx, 0, 0))
            b = centre + Vector((0.36 * sx, -0.05, 0.52))
            beam = [b + up * (1.3 * s * t) + out * (0.55 * s * t) + (-fwd) * (0.35 * s * t * t) for t in [i / 11 for i in range(12)]]
            H.add(tube_mesh(beam, [0.075 * s * (1 - 0.8 * t) for t in [i / 11 for i in range(12)]], seg=10, base=H.base(), twist=0.8))
            for at, ln, dv in ((0.25, 0.55, fwd * 0.6 + up * 0.8), (0.5, 0.6, out + up * 0.6), (0.72, 0.45, -fwd + up), (0.88, 0.35, out * 0.4 + fwd * 0.6 + up)):
                p0 = beam[int(at * 11)]
                dvn = dv.normalized()
                tine = [p0 + dvn * (ln * s * t) + up * (0.08 * s * t * t) for t in [i / 6 for i in range(7)]]
                H.add(tube_mesh(tine, [0.045 * s * (1 - 0.92 * t) for t in [i / 6 for i in range(7)]], seg=8, base=H.base()))
    else:
        for sx in (-1, 1):
            out = Vector((sx, 0, 0))
            base = centre + Vector((0.34 * sx, 0.2 if kind == "bull" else 0.05, 0.35 if kind == "bull" else 0.5))
            L = {"ram": 1.5, "demon": 1.75, "bull": 1.4, "sovereign": 1.55, "broken": 1.75}[kind] * s
            broken_here = kind == "broken" and sx < 0
            path = _horn_path(base, out, up, fwd, "broken" if broken_here else ("demon" if kind == "broken" else kind), L)
            r0 = {"ram": 0.24, "demon": 0.17, "bull": 0.19, "sovereign": 0.12, "broken": 0.17}[kind] * s
            n = len(path)
            radii = []
            for i in range(n):
                t = i / (n - 1)
                taper = 1 - (0.5 if broken_here else 0.94) * t ** (0.7 if kind == "ram" else 0.9)
                ridge = 1 + 0.09 * max(0.0, math.sin(t * rings * 2 * math.pi)) ** 2
                radii.append(r0 * taper * ridge)
            H.add(tube_mesh(path, radii, seg=14, base=H.base(), twist=twist * sx, flat=0.85))
            if broken_here:
                tip_c = path[-1]
                dirn = (path[-1] - path[-2]).normalized()
                for k in range(7):
                    a = 2 * math.pi * k / 7
                    d = dirn.orthogonal().normalized()
                    d = Matrix.Rotation(a, 3, dirn) @ d
                    H.add(cone_mesh(tip_c + d * radii[-1] * 0.6, dirn + d * 0.2, rnd.uniform(0.05, 0.13) * s, radii[-1] * 0.35, base=H.base(), seg=4))
            else:
                tp = path[-4:]
                parts["tip"].add(tube_mesh(tp, [radii[-4] * 1.04, radii[-3] * 1.04, radii[-2] * 1.04, 0.002], seg=14, base=parts["tip"].base(), twist=twist * sx, flat=0.85))
        if kind == "sovereign":
            halo = Part()
            ring = [centre + Vector((0.78 * math.cos(a), -0.75, 0.75 + 0.78 * math.sin(a))) for a in [2 * math.pi * k / 40 for k in range(41)]]
            halo.add(tube_mesh(ring, [0.035 * s] * len(ring), seg=8, base=0))
            for k in range(12):
                a = 2 * math.pi * k / 12
                p = centre + Vector((0.78 * math.cos(a), -0.75, 0.75 + 0.78 * math.sin(a)))
                halo.add(cone_mesh(p, Vector((math.cos(a), 0, math.sin(a))), 0.22 * s, 0.035 * s, base=halo.base()))
            parts["halo"] = halo
    return {k: (p.v, p.f) for k, p in parts.items() if p.v}


# ---------------------------------------------------------------- customization: palettes and finishes
PALETTES = {
    "Wine":     {"base": (0.03, 0.006, 0.012), "glow": (0.55, 0.03, 0.05), "vein": (0.25, 0.02, 0.04), "vein_emit": 0.0},
    "Midnight": {"base": (0.012, 0.012, 0.03), "glow": (0.3, 0.12, 0.75), "vein": (0.08, 0.05, 0.2), "vein_emit": 0.0},
    "Ashen":    {"base": (0.42, 0.39, 0.36), "glow": (0.9, 0.6, 0.45), "vein": (0.3, 0.22, 0.2), "vein_emit": 0.0},
    "Ember":    {"base": (0.02, 0.015, 0.015), "glow": (0.9, 0.3, 0.05), "vein": (1.0, 0.35, 0.05), "vein_emit": 6.0},
    "Raven":    {"base": (0.012, 0.012, 0.016), "glow": (0.1, 0.2, 0.5), "vein": (0.05, 0.05, 0.08), "vein_emit": 0.0},
    "Dove":     {"base": (0.8, 0.78, 0.74), "glow": (0.9, 0.85, 0.7), "vein": (0.6, 0.55, 0.5), "vein_emit": 0.0},
}
FINISHES = {
    "Obsidian": {"base": (0.02, 0.018, 0.022), "metal": 0.0, "rough": 0.18, "coat": 0.8},
    "Bone":     {"base": (0.72, 0.66, 0.55), "metal": 0.0, "rough": 0.5, "coat": 0.1},
    "Gilded":   {"base": (0.85, 0.62, 0.25), "metal": 1.0, "rough": 0.25, "coat": 0.3},
    "Ivory":    {"base": (0.88, 0.84, 0.74), "metal": 0.0, "rough": 0.35, "coat": 0.4},
    "Bloodstone": {"base": (0.12, 0.02, 0.025), "metal": 0.0, "rough": 0.2, "coat": 0.9},
}


def _principled(name, base, rough=0.4, metal=0.0, coat=0.0, emit=None, emit_str=0.0, trans=0.0, alpha=1.0, sheen=0.0, thin_film=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = emit_str
    if trans:
        b.inputs["Transmission Weight"].default_value = trans
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
    if sheen:
        b.inputs["Sheen Weight"].default_value = sheen
    if thin_film and "Thin Film Thickness" in b.inputs:
        b.inputs["Thin Film Thickness"].default_value = thin_film
    return m, b


def wing_mats(palette="Wine", finish="Obsidian", tag="", style="nocturne"):
    P, Fz = PALETTES[palette], FINISHES[finish]
    m = bpy.data.materials.new(f"WingMembrane{palette}{tag}"); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*P["base"], 1)
    b.inputs["Roughness"].default_value = 0.42
    b.inputs["Subsurface Weight"].default_value = 0.2
    b.inputs["Subsurface Radius"].default_value = P["glow"]
    b.inputs["Subsurface Scale"].default_value = 0.08
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent"); tr.inputs["Color"].default_value = (*P["glow"], 1)
    mix = nt.nodes.new("ShaderNodeMixShader"); mix.inputs["Fac"].default_value = 0.16
    out = nt.nodes["Material Output"]
    nt.links.new(b.outputs[0], mix.inputs[1]); nt.links.new(tr.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.inputs["Scale"].default_value = 3; wv.inputs["Distortion"].default_value = 8; wv.inputs["Detail"].default_value = 6
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 30; nz.inputs["Detail"].default_value = 10
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"]); nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MULTIPLY_ADD"; mx.inputs[1].default_value = 0.35
    nt.links.new(nz.outputs["Fac"], mx.inputs[0]); nt.links.new(wv.outputs["Fac"], mx.inputs[2])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.18; bp.inputs["Distance"].default_value = 0.01
    nt.links.new(mx.outputs[0], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    bone, _ = _principled(f"WingBone{finish}{tag}", Fz["base"], Fz["rough"], Fz["metal"], Fz["coat"])
    vein, _ = _principled(f"WingVein{palette}{tag}", P["vein"], 0.35, emit=P["vein"], emit_str=P["vein_emit"])
    mats = {"membrane": m, "bone": bone, "veins": vein, "rim": bone, "spikes": bone}
    if style == "fallen":
        fe, _ = _principled(f"Feather{palette}{tag}", P["base"], 0.38, coat=0.25, sheen=0.12, thin_film=420)
        mats["feathers"] = fe; mats["coverts"] = fe
    if style == "ossuary":
        mats["tatters"] = _principled(f"Gravecloth{tag}", (0.3, 0.3, 0.26), 0.85)[0]
    if style == "wraithveil":
        mist, _ = _principled(f"Veil{tag}", (0.08, 0.22, 0.3), 0.2, emit=(0.15, 0.6, 0.85), emit_str=0.7, trans=0.5, alpha=0.45)
        mats["membrane"] = mist; mats["wisps"] = mist
        mats["bone"] = _principled(f"VeilBone{tag}", (0.25, 0.4, 0.5), 0.2, emit=(0.3, 0.75, 1.0), emit_str=0.9)[0]
        mats["rim"] = mats["bone"]
    if style == "rime":
        ice, _ = _principled(f"IceWing{tag}", (0.75, 0.9, 1.0), 0.06, emit=(0.5, 0.8, 1.0), emit_str=0.5, trans=0.9)
        mats["membrane"] = ice; mats["shards"] = ice; mats["rim"] = ice
    return mats


def horn_mats(finish="Obsidian", tip="Gilded", tag=""):
    Fz = FINISHES[finish]
    h, hb = _principled(f"Horn{finish}{tag}", Fz["base"], Fz["rough"] + 0.1, Fz["metal"], Fz["coat"])
    nt = h.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord"); wv = nt.nodes.new("ShaderNodeTexWave")
    wv.inputs["Scale"].default_value = 22; wv.inputs["Distortion"].default_value = 4; wv.inputs["Detail"].default_value = 8
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.4
    nt.links.new(wv.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], hb.inputs["Normal"])
    T = FINISHES.get(tip, Fz)
    t, _ = _principled(f"HornTip{tip}{tag}", T["base"], T["rough"], T["metal"], T["coat"])
    halo, _ = _principled(f"Halo{tag}", (1.0, 0.8, 0.4), 0.2, metal=1.0, emit=(1.0, 0.7, 0.3), emit_str=4.0)
    return {"horn": h, "tip": t, "halo": halo}
