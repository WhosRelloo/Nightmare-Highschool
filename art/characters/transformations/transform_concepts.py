"""Nightmare Highschool: race transformation concept renders (2026-11-23), for the owner's pick before any mass modelling.

Headless (Blender 5.2): E:/Blender/blender.exe -b --factory-startup -P transform_concepts.py -- --race Vampire --out <dir> [--quick]

Two directions per transforming race, each shown on two contrasting bodies (one male at the race's tallest height, one female at
its shortest), so every race sheet covers different builds and both genders:
  Vampire  V1 Nocturne (folded wings, high membrane collar, ears, claws)   V2 Night Sovereign (spread wings, swept horns, spine)
  Werewolf W1 Moonbound (mane, fur cuffs, ears, tail, claws)               W2 Feral Lord (muzzle, full fur mantle, moon-marks)
  Ghoul    G1 Ossuary (ossified rib plates, bone claws, jaw guard, spine)  G2 Gravecloth (grave-linen wraps, tatters, moss, nails)
  Wraith   R1 Hollow Shroud (void cowl, mist body, trailing tatters)       R2 Frost Revenant (ice crown and spikes, spectral chains)
Every piece is sculpted geometry fitted to its body by raycasting (nhfig), with the body's skin weights copied so it bends with
the pose. PaintRigV3 is opened through libraries.load only (read-only). No gore: no exposed flesh, no blood.
"""
import bpy, math, os, sys, random
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nhfig import *          # noqa: F401,F403  (scene reset, materials, fitting helpers)
import nhfig
import hqwing

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
RACE = argv[argv.index("--race") + 1] if "--race" in argv else "Vampire"
OUT = argv[argv.index("--out") + 1] if "--out" in argv else "E:/ClaudeTemp/nhart/out/tf"
QUICK = "--quick" in argv
os.makedirs(OUT, exist_ok=True)
random.seed(11)
sc = bpy.context.scene


# ---------------------------------------------------------------- materials for the forms
def mat(name, base, rough=0.5, metal=0.0, sss=0.0, emit=None, emit_str=0.0, bump=None, sheen=0.0, trans=0.0, alpha=None):
    m, nt, b = node_mat(name, base, rough=rough, metal=metal, sss=sss, emit=emit, emit_str=emit_str)
    if bump:
        add_bump(nt, b, *bump)
    if sheen:
        b.inputs["Sheen Weight"].default_value = sheen
        b.inputs["Sheen Tint"].default_value = (*[min(1, c * 1.6) for c in base], 1)
    if trans:
        b.inputs["Transmission Weight"].default_value = trans
    if alpha is not None:
        b.inputs["Alpha"].default_value = alpha
    return m


F = {
    "membrane": mat("Membrane", (0.045, 0.012, 0.02), rough=0.5, sss=0.12, bump=(30, 0.3)),
    "wingbone": mat("WingBone", (0.05, 0.04, 0.05), rough=0.35, bump=(60, 0.2)),
    "obsidian": mat("ObsidianHorn", (0.03, 0.025, 0.03), rough=0.25, bump=(9, 0.5, "wave")),
    "claw": mat("Claw", (0.035, 0.03, 0.035), rough=0.22),
    "ivory": mat("Ivory", (0.83, 0.78, 0.66), rough=0.55, sss=0.08, bump=(24, 0.35)),
    "boneclaw": mat("BoneClaw", (0.78, 0.72, 0.6), rough=0.45),
    "furA": mat("FurUmber", (0.2, 0.12, 0.07), rough=0.75, sheen=0.7, bump=(80, 0.3)),
    "furB": mat("FurCharcoal", (0.07, 0.065, 0.07), rough=0.75, sheen=0.7, bump=(80, 0.3)),
    "furTip": mat("FurAsh", (0.3, 0.24, 0.19), rough=0.8, sheen=0.6),
    "nose": mat("Nose", (0.02, 0.018, 0.02), rough=0.3, bump=(70, 0.2)),
    "fang": mat("Fang", (0.92, 0.9, 0.84), rough=0.3),
    "moon": mat("MoonMark", (0.85, 0.88, 0.95), rough=0.3, emit=(0.7, 0.8, 1.0), emit_str=3.0),
    "linen": gauze_mat("GraveLinen", (0.36, 0.37, 0.31)),
    "moss": mat("GraveMoss", (0.12, 0.2, 0.08), rough=0.9, sheen=0.4),
    "iron": mat("CoffinIron", (0.16, 0.14, 0.13), rough=0.6, metal=1.0, bump=(40, 0.4)),
    "void": mat("Void", (0.0, 0.0, 0.0), rough=1.0),
    "mist": mat("Mist", (0.1, 0.3, 0.4), rough=0.3, emit=(0.25, 0.7, 0.9), emit_str=0.9, trans=0.6, alpha=0.4),
    "shroud": mat("Shroud", (0.05, 0.06, 0.08), rough=0.85, sss=0.1, bump=(18, 0.4), emit=(0.15, 0.4, 0.5), emit_str=0.15),
    "chain": mat("SpectralChain", (0.6, 0.85, 0.95), rough=0.2, metal=0.6, emit=(0.4, 0.8, 1.0), emit_str=1.2),
    "blazer": mat("Blazer", (0.07, 0.06, 0.09), rough=0.7, bump=(200, 0.15, "wave")),
}
EYES = {
    "Vampire": decal_mat("EyeVamp", (1.0, 0.05, 0.08), (0.6, 0.0, 0.02), softness=0.1, rough=0.2, noise_scale=1, emit=(1, 0.05, 0.08), emit_str=8),
    "Werewolf": decal_mat("EyeWolf", (1.0, 0.62, 0.08), (0.7, 0.3, 0.0), softness=0.1, rough=0.2, noise_scale=1, emit=(1, 0.6, 0.08), emit_str=8),
    "Ghoul": decal_mat("EyeGhoul", (0.55, 1.0, 0.15), (0.3, 0.6, 0.0), softness=0.1, rough=0.2, noise_scale=1, emit=(0.55, 1, 0.15), emit_str=8),
    "Wraith": decal_mat("EyeWraith", (0.6, 0.9, 1.0), (0.3, 0.6, 1.0), softness=0.1, rough=0.2, noise_scale=1, emit=(0.6, 0.9, 1.0), emit_str=10),
}
SKINC = {"Vampire": (0.86, 0.78, 0.77), "Werewolf": (0.62, 0.44, 0.32), "Ghoul": (0.48, 0.53, 0.44), "Wraith": (0.6, 0.64, 0.7),
         "Werewolf2": (0.36, 0.24, 0.17), "Vampire2": (0.5, 0.36, 0.3), "Ghoul2": (0.4, 0.45, 0.4), "Wraith2": (0.42, 0.45, 0.52)}
for k, c in SKINC.items():
    nhfig.SKIN[k] = node_mat("Skin" + k, c, rough=0.5, sss=0.25)[0]
M["blazer"] = F["blazer"]


# ---------------------------------------------------------------- shape helpers (all smooth, subdivided)
def arc(p0, d, up, length, curl, n=9):
    d = d.normalized(); up = up.normalized()
    return [p0 + d * (length * t) + up * (curl * (length * t) ** 2) for t in [i / (n - 1) for i in range(n)]]


def taper(name, pts, r0, r1, m, subd=1, flat=None):
    rs = [(p, float((r0 + (r1 - r0) * (i / (len(pts) - 1))) / r0)) for i, p in enumerate(pts)]
    o = tube(name, rs, r0, m, subd=subd)
    if flat:
        o.scale = flat
    return o


def leaf(name, base, along, across, normal, length, width, cup, m, res=(14, 8), thick=0.03, tip_curl=0.0):
    """A sculpted ear or fin: a leaf outline (widest a third of the way up) cupped along its normal, curled at the tip."""
    along, across, normal = along.normalized(), across.normalized(), normal.normalized()
    verts, faces, uvs = [], [], []
    nu, nv = res
    for i in range(nu + 1):
        t = i / nu
        w = width * (math.sin(math.pi * min(1, t * 1.25)) ** 0.7) * (1 - 0.85 * t)
        for j in range(nv + 1):
            s = j / nv * 2 - 1
            p = base + along * (length * t) + across * (w * s) + normal * (cup * (1 - s * s) * math.sin(math.pi * t) + tip_curl * t ** 3)
            verts.append(p)
            uvs.append((t, j / nv))
    for i in range(nu):
        for j in range(nv):
            a = i * (nv + 1) + j
            faces.append((a, a + nv + 1, a + nv + 2, a + 1))
    return add_mods(mesh_obj(name, verts, faces, m, uvs=uvs), thick=thick, subd=1)


def tuft(name, root, nrm, length, r0, m, bias=Vector((0, 0, -0.4)), curl=0.5):
    d = (nrm + bias * 0.6).normalized()
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 1e-3:
        side = Vector((1, 0, 0))
    up = (d.cross(side)).normalized() * curl + bias * 0.5
    pts = arc(root - nrm * r0 * 0.6, d, up, length, 0.9 / max(length, 0.05), n=6)
    return taper(name, pts, r0, r0 * 0.08, m, subd=1)


def fur_region(prefix, bvh, centre, spread, count, length, r0, mats, nrm_bias=Vector((0, 0, -0.5)), axis_pts=None):
    """Fur as clumped locks: each lock is a curved, pointed blade (hqwing.blade_mesh) rooted on the surface, lying down along
    gravity and curling out at the tip, shingled so the coat reads as layered fur. Every region is ONE mesh per shade."""
    parts = [hqwing.Part(), hqwing.Part()]
    n = int(count * 4.5)
    for i in range(n):
        p = centre + Vector((random.uniform(-spread.x, spread.x), random.uniform(-spread.y, spread.y), random.uniform(-spread.z, spread.z)))
        dirn = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-0.2, 0.6))).normalized()
        loc, nn = surf(bvh, p + dirn * 3, -dirn)
        if loc is None:
            continue
        down = nrm_bias - nn * nrm_bias.dot(nn)
        if down.length < 1e-3:
            down = Vector((0, 0, -1)) - nn * nn.z
        along = (down.normalized() * 0.93 + nn * 0.2).normalized()
        across = nn.cross(along).normalized()
        L = length * random.uniform(0.85, 1.45)
        W = r0 * random.uniform(1.0, 1.55)
        k = 0 if random.random() < 0.85 else 1
        P = parts[k]
        P.add(hqwing.blade_mesh(loc - nn * 0.01, along, across, nn, L, W, base=P.base(), nu=6, nv=3,
                                vane_curve=random.uniform(0.05, 0.14), tip=random.uniform(0.03, 0.1), asym=random.uniform(-0.3, 0.3)))
    out = []
    for k, P in enumerate(parts):
        if P.v:
            ob = mesh_obj(f"{prefix}_{k}", P.v, P.f, mats[0] if k == 0 else mats[-1])
            add_mods(ob, thick=0.012, subd=1)
            out.append(ob)
    return out


def _old_fur_region(prefix, bvh, centre, spread, count, length, r0, mats, nrm_bias=Vector((0, 0, -0.5)), axis_pts=None):
    """Raycast `count` tufts onto a body region: random directions around `centre` within `spread` (a box), each tuft growing
    out of the surface along its normal, swept by gravity. Tufts are tapered tubes, so the mane has real volume."""
    made = []
    for i in range(count):
        p = centre + Vector((random.uniform(-spread.x, spread.x), random.uniform(-spread.y, spread.y), random.uniform(-spread.z, spread.z)))
        dirn = (p - (axis_pts or centre)).normalized() if axis_pts else Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-0.2, 0.6))).normalized()
        loc, n = surf(bvh, p + dirn * 3, -dirn)
        if loc is None:
            continue
        L = length * random.uniform(0.6, 1.25)
        made.append(tuft(f"{prefix}{i}", loc, n, L, r0 * random.uniform(0.8, 1.3), random.choice(mats), bias=nrm_bias, curl=random.uniform(0.2, 0.8)))
    return made


def wing(name, root, out, down, back, span, spread, spokes=4, m_mem=None, m_bone=None):
    """A membrane wing: an arm bone from the shoulder blade to the wrist, finger bones fanning from the wrist, a scalloped
    membrane between them and the body; the bones are tapered tubes standing proud of the membrane."""
    out, down, back = out.normalized(), down.normalized(), back.normalized()
    wrist = root + out * span * 0.45 + back * span * 0.18 + down * (-span * 0.25 * spread)
    tips = []
    for k in range(spokes):
        a = (k / (spokes - 1))
        dirn = (out * math.cos(a * 1.25 * spread + 0.15) + down * math.sin(a * 1.25 * spread + 0.15) * (0.6 + 0.4 * spread)).normalized()
        tips.append(wrist + dirn * span * (0.62 - 0.15 * a) + back * span * 0.12)
    body_end = root + down * span * 0.55 + back * span * 0.05
    rails = [[root + (wrist - root) * t for t in (0, 0.5, 1)] + [wrist + (tips[0] - wrist) * t for t in (0.5, 1)]]
    for k in range(1, spokes):
        rails.append([root + (wrist - root) * t for t in (0, 0.5, 1)] + [wrist + (tips[k] - wrist) * t for t in (0.5, 1)])
    rails.append([root + (body_end - root) * t for t in (0, 0.25, 0.5, 0.75, 1)])
    verts, faces, uvs = [], [], []
    NU, NV = 12, 6
    for r in range(len(rails) - 1):
        A, B = rails[r], rails[r + 1]
        base = len(verts)
        for i in range(NU + 1):
            u = i / NU
            def at(R):
                f = u * (len(R) - 1); k = min(int(f), len(R) - 2); t = f - k
                return R[k] * (1 - t) + R[k + 1] * t
            pa, pb = at(A), at(B)
            for j in range(NV + 1):
                v = j / NV
                p = pa * (1 - v) + pb * v
                sag = 0.22 * span * u ** 2 * math.sin(math.pi * v)
                p = p + ((root - p) * 0.0) + (-(out + down).normalized()) * sag * 0.35 + back * (0.05 * span * math.sin(math.pi * v) * u)
                verts.append(p)
                uvs.append((u, (r + v) / len(rails)))
        for i in range(NU):
            for j in range(NV):
                a = base + i * (NV + 1) + j
                faces.append((a, a + NV + 1, a + NV + 2, a + 1))
    mem = add_mods(mesh_obj(name + "Mem", verts, faces, m_mem or F["membrane"], uvs=uvs), thick=0.018, subd=1)
    parts = [mem]
    parts.append(taper(name + "Arm", [root, root + (wrist - root) * 0.5 + back * 0.04, wrist], 0.075, 0.045, m_bone or F["wingbone"]))
    for k, tp in enumerate(tips):
        parts.append(taper(f"{name}Fin{k}", [wrist, wrist + (tp - wrist) * 0.5 + back * 0.03, tp], 0.04, 0.008, m_bone or F["wingbone"]))
    parts.append(taper(name + "Thumb", arc(wrist, out + Vector((0, 0, 0.6)), -down, 0.28 * span / 2.2, 0.3, n=5), 0.035, 0.004, F["claw"]))
    return parts


def claws(prefix, cx, curl_dir, m, length=0.32, r0=0.045, n=4):
    """Claws from the bottom front edge of an R6 hand (rest pose: arm box bottom at z 2): curved, tapered, glossy."""
    made = []
    for i in range(n):
        xo = -0.3 + 0.6 * i / (n - 1)
        base = Vector((cx + xo, 0.32, 2.06))
        pts = arc(base, Vector((0, 0.45, -1)), curl_dir, length, 1.3 / length, n=7)
        made.append(taper(f"{prefix}{i}", pts, r0, r0 * 0.06, m))
    return made


def horn(name, base, out, up, back, length, r0, m, curl=1.0):
    pts = []
    for i in range(12):
        t = i / 11
        a = t * math.pi * 0.9 * curl
        pts.append(base + out * (length * 0.35 * t) + up * (length * 0.55 * math.sin(a)) + back * (length * 0.6 * (1 - math.cos(a)) + length * 0.25 * t))
    return taper(name, pts, r0, r0 * 0.07, m)


def ring_on_torso(bvh, z, off, n=48, centre=(0, 0)):
    return [ring_point(bvh, centre, Vector((math.cos(2 * math.pi * k / n), math.sin(2 * math.pi * k / n), 0)), z, off) for k in range(n + 1)]


def hq_wings(tag, style, pal, fin, size):
    mats = hqwing.wing_mats(pal, fin, tag, style)
    objs = []
    for sx in (-1, 1):
        w = hqwing.Wing(sx, (0.42 * sx, -0.5, 3.72), size=size, style=style, seed=7 + sx)
        objs += w.build(f"{tag}W{sx}", mats, mesh_obj, add_mods, pose=(0.08, 16, 0, 0))
    return objs


def hq_horns(tag, kind, fin, tip):
    hm = hqwing.horn_mats(fin, tip, tag)
    objs = []
    for part, (v, f) in hqwing.horns(kind, Vector((0, 0, 4.5))).items():
        ob = mesh_obj(f"{tag}Horn_{part}", v, f, hm[part])
        add_mods(ob, subd=1)
        objs.append(ob)
    return objs


# ---------------------------------------------------------------- one figure
def build(tag, race, direction, body, gender, skin_key):
    coll, o = load_rig(tag)
    arm = o["arm"]
    if body != "standard":
        swap_body(o, body, coll)
    skin(o, skin_key, top="blazer", legs="skirt" if gender == "F" else "trousers")
    bpy.context.view_layer.update()
    face(tag, o, "grim")
    for ob in sc.objects:
        if ob.name.startswith(f"{tag}Eye"):
            ob.data.materials.clear(); ob.data.materials.append(EYES[race])
    bv = {k: eval_bvh(o[k]) for k in ("Torso", "RArm", "LArm", "RLeg", "LLeg", "Head")}
    made = []                                  # (object, part key)
    def add(objs, part):
        for x in (objs if isinstance(objs, list) else [objs]):
            made.append((x, part))
    B = Vector((0, -1, 0)); FW = Vector((0, 1, 0)); UP = Vector((0, 0, 1)); DN = Vector((0, 0, -1))
    hc = Vector((0, 0, 4.5))

    if race == "Vampire":
        # ears: long, swept, cupped (both directions)
        for sx in (-1, 1):
            add(leaf(f"{tag}Ear{sx}", hc + Vector((0.58 * sx, -0.02, 0.05)), Vector((0.75 * sx, -0.35, 0.6)), Vector((0, 0.3, 1)),
                     Vector((0, 1, 0)), 0.62 if direction == 1 else 0.5, 0.2, 0.05, nhfig.SKIN[skin_key], tip_curl=0.04), "Head")
            add(claws(f"{tag}Claw{sx}", 1.5 * sx, Vector((0, 1, 0)), F["claw"], length=0.36, r0=0.035), "RArm" if sx > 0 else "LArm")
        root_l, root_r = Vector((-0.45, -0.52, 3.75)), Vector((0.45, -0.52, 3.75))
        if direction == 1:
            # Nocturne: wings folded like a cloak, a high membrane collar behind the head
            add(hq_wings(tag, "nocturne", "Wine", "Obsidian", 1.1), "Torso")
            for k in range(5):
                a = -0.9 + 1.8 * k / 4
                base = Vector((0.55 * math.sin(a), -0.35 - 0.1 * math.cos(a), 3.98))
                add(leaf(f"{tag}Collar{k}", base, Vector((math.sin(a) * 0.5, -0.4, 1)), Vector((math.cos(a), 0.2 * math.sin(a), 0)),
                         Vector((math.sin(a) * 0.3, 1, 0)), 1.0, 0.24, 0.06, F["membrane"], thick=0.02), "Torso")
        else:
            # Night Sovereign: wings spread wide, horns swept back, a ridge of spines down the back
            add(hq_wings(tag, "wyrm", "Wine", "Bloodstone", 1.15), "Torso")
            add(hq_horns(tag, "demon", "Obsidian", "Bloodstone"), "Head")
            for k in range(6):
                z = 3.85 - k * 0.3
                p = project(bv["Torso"], Vector((0, -0.4, z)), Vector((0, 1, 0)), 0.0)
                add(taper(f"{tag}Spine{k}", arc(p, Vector((0, -1, 0.5)), UP, 0.3 - k * 0.03, 0.6, n=5), 0.06, 0.006, F["obsidian"]), "Torso")

    elif race == "Werewolf":
        fur = [F["furA"], F["furA"], F["furTip"]] if direction == 1 else [F["furB"], F["furB"], F["furTip"]]
        for sx in (-1, 1):
            add(leaf(f"{tag}Ear{sx}", hc + Vector((0.36 * sx, -0.05, 0.55)), Vector((0.35 * sx, -0.1, 1)), Vector((1, 0, 0)), Vector((0, 1, 0)),
                     0.55, 0.24, 0.07, fur[0], tip_curl=-0.03), "Head")
            key = "RArm" if sx > 0 else "LArm"           # (owner 2026-11-23: no claws on the wolves)
            add(fur_region(f"{tag}Cuff{sx}_", bv[key], Vector((1.5 * sx, 0, 2.45)), Vector((0.55, 0.55, 0.2)), 46, 0.28, 0.06, fur), key)
            lk = "RLeg" if sx > 0 else "LLeg"
            add(fur_region(f"{tag}Shin{sx}_", bv[lk], Vector((0.5 * sx, 0, 0.3)), Vector((0.55, 0.55, 0.1)), 14, 0.22, 0.06, fur), lk)
        # (owner 2026-11-23: no fur on the head; the ears stay)
        # the mane over the shoulders and upper back (W2: the whole upper body and down the arms)
        mane_n = 170 if direction == 1 else 300
        add(fur_region(f"{tag}Mane", bv["Torso"], Vector((0, -0.1, 3.85)), Vector((1.0, 0.6, 0.18)), mane_n, 0.4 if direction == 1 else 0.5, 0.075, fur,
                       nrm_bias=Vector((0, -0.3, -0.6))), "Torso")
        if direction == 2:
            for sx in (-1, 1):
                key = "RArm" if sx > 0 else "LArm"
                add(fur_region(f"{tag}Arm{sx}_", bv[key], Vector((1.5 * sx, 0, 3.4)), Vector((0.55, 0.55, 0.55)), 110, 0.32, 0.065, fur), key)
            add(fur_region(f"{tag}Back", bv["Torso"], Vector((0, -0.5, 3.0)), Vector((0.9, 0.1, 0.8)), 160, 0.38, 0.07, fur, nrm_bias=Vector((0, -0.2, -0.8))), "Torso")
            # moon-marks: pale crescents glowing through the chest fur gap
            ctr = Vector((0, 0.62, 3.2))
            pts = [project(bv["Torso"], ctr + Vector((0.28 * math.cos(a), 0, 0.28 * math.sin(a))), Vector((0, -1, 0)), 0.03) for a in [math.pi * (0.25 + 1.2 * k / 14) for k in range(15)]]
            add(taper(f"{tag}Moon", pts, 0.035, 0.012, F["moon"]), "Torso")
        # tail
        tp = [Vector((0, -0.55, 2.2)), Vector((0, -1.05, 1.9)), Vector((0, -1.55, 1.75)), Vector((0, -1.95, 1.95)), Vector((0, -2.15, 2.35))]
        add(taper(f"{tag}Tail", tp, 0.22, 0.06, fur[0], subd=2), "Torso")
        for i in range(70):
            t = random.uniform(0.05, 1.0)
            k = min(int(t * 4), 3); f = t * 4 - k
            c = tp[k] * (1 - f) + tp[k + 1] * f
            d = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))).normalized()
            add(tuft(f"{tag}TailF{i}", c + d * 0.18 * (1 - 0.6 * t), d, 0.25, 0.05, random.choice(fur), bias=Vector((0, -1, 0)), curl=0.3), "Torso")

    elif race == "Ghoul":
        if direction == 1:
            # Ossuary: ossified rib plates grown over the chest, a jaw guard, bone claws, a vertebral ridge
            for sx in (-1, 1):
                for k in range(4):
                    z = 3.55 - k * 0.3
                    pts = [project(bv["Torso"], Vector((sx * (0.08 + 0.85 * t), 1, z - 0.18 * t * t)), Vector((0, -1, 0)), 0.035) for t in [i / 8 for i in range(9)]]
                    add(taper(f"{tag}Rib{sx}_{k}", pts, 0.055, 0.03, F["ivory"]), "Torso")
                add(claws(f"{tag}BClaw{sx}", 1.5 * sx, Vector((0, 1, 0)), F["boneclaw"], length=0.4, r0=0.05, n=3), "RArm" if sx > 0 else "LArm")
            add(hq_wings(tag, "ossuary", "Wine", "Ivory", 1.0), "Torso")
            add(hq_horns(tag, "wendigo", "Bone", "Bone"), "Head")
            st = [project(bv["Torso"], Vector((0, 1, 3.85 - 0.12 * i)), Vector((0, -1, 0)), 0.05) for i in range(10)]
            add(taper(f"{tag}Sternum", st, 0.07, 0.04, F["ivory"]), "Torso")
            jaw = [project(bv["Head"], hc + Vector((0.45 * math.cos(a), 1, -0.3 + 0.08 * math.sin(a) ** 2)), Vector((0, -1, 0)), 0.04) for a in [math.pi * k / 12 for k in range(13)]]
            add(taper(f"{tag}Jaw", jaw, 0.05, 0.05, F["ivory"]), "Head")
            for k in range(7):
                z = 3.9 - k * 0.27
                p = project(bv["Torso"], Vector((0, -1, z)), Vector((0, 1, 0)), 0.0)
                bpy.ops.mesh.primitive_uv_sphere_add(radius=0.11, location=p + Vector((0, -0.05, 0)), segments=16, ring_count=10)
                v = bpy.context.active_object; v.name = f"{tag}Vert{k}"; v.scale = (1.2, 0.9, 0.6); v.data.materials.append(F["ivory"]); add(v, "Torso")
            for sx in (-1, 1):
                key = "RArm" if sx > 0 else "LArm"
                for k in range(3):
                    p = project(bv[key], Vector((1.5 * sx + 0.5 * sx, 0, 3.7 - k * 0.22)), Vector((-sx, 0, 0)), 0.0)
                    add(taper(f"{tag}Spur{sx}_{k}", arc(p, Vector((sx, -0.3, 0.6)), UP, 0.3, 0.5, n=5), 0.06, 0.005, F["ivory"]), key)
        else:
            # Gravecloth: grave-linen wound round the arms and chest, tatters hanging, grave-moss, iron coffin nails
            for sx in (-1, 1):
                key = "RArm" if sx > 0 else "LArm"
                add(gauze_wrap(f"{tag}Wrap{sx}", bv[key], (1.5 * sx, 0), 2.15, 3.85, 4.5, 0.26, off=0.03, layer=0.008, mat=F["linen"]), key)
                for k in range(4):
                    a = random.uniform(0, 2 * math.pi)
                    p = ring_point(bv[key], (1.5 * sx, 0), Vector((math.cos(a), math.sin(a), 0)), 2.15, 0.06)
                    pts = [p + Vector((0.05 * math.cos(a) * t, 0.05 * math.sin(a) * t, -0.75 * t)) for t in [i / 5 for i in range(6)]]
                    verts, faces = [], []
                    sd = Vector((-math.sin(a), math.cos(a), 0)) * 0.07
                    for i, q in enumerate(pts):
                        w = 1 - 0.6 * i / 5
                        verts += [fray(q - sd * w, 0.01), fray(q + sd * w, 0.01)]
                    faces = [(i * 2, i * 2 + 2, i * 2 + 3, i * 2 + 1) for i in range(5)]
                    add(add_mods(mesh_obj(f"{tag}Tatter{sx}_{k}", verts, faces, F["linen"]), thick=0.01), key)
                add(claws(f"{tag}BClaw{sx}", 1.5 * sx, Vector((0, 1, 0)), F["boneclaw"], length=0.3, r0=0.045, n=4), key)
            add(gauze_wrap(f"{tag}Chest", bv["Torso"], (0, 0), 2.6, 3.75, 2.2, 0.38, off=0.03, layer=0.01, mat=F["linen"], phase=1.0), "Torso")
            add(hq_horns(tag, "thorn", "Obsidian", "Obsidian"), "Head")
            add(fur_region(f"{tag}Moss", bv["Torso"], Vector((0, 0, 3.95)), Vector((1.0, 0.55, 0.06)), 120, 0.09, 0.035, [F["moss"]],
                           nrm_bias=Vector((0, 0, -0.2))), "Torso")
            for k, (x, z) in enumerate(((-0.6, 3.5), (0.5, 3.1), (-0.2, 2.8))):
                p = project(bv["Torso"], Vector((x, 1, z)), Vector((0, -1, 0)), 0.06)
                add(taper(f"{tag}Nail{k}", [p + Vector((0, 0.12, 0.03)), p + Vector((0, -0.05, 0))], 0.025, 0.02, F["iron"], subd=0), "Torso")
                bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=0.025, location=p + Vector((0, 0.13, 0.03)), rotation=(math.pi / 2, 0, 0))
                h = bpy.context.active_object; h.name = f"{tag}NailHead{k}"; h.data.materials.append(F["iron"]); add(h, "Torso")

    elif race == "Wraith":
        if direction == 1:
            # Hollow Shroud (student look kept, owner 2026-11-23): head clear, a tattered capelet, veil wings
            rings = []
            for i in range(14):
                t = i / 13
                z = 4.0 + 1.35 * t
                rx, ry = 0.78 * (1 - 0.35 * t ** 2), 0.8 * (1 - 0.3 * t ** 2)
                yo = -0.05 - 0.1 * t
                pts = []
                for k in range(28):
                    a = 2 * math.pi * k / 28
                    front = max(0.0, math.sin(a))
                    pts.append(Vector((rx * math.cos(a), yo + ry * math.sin(a) + 0.18 * front * (1 - t), z - 0.25 * front ** 3 * t)))
                rings.append(pts)
            verts = [p for r in rings for p in r]
            faces = []
            for i in range(13):
                for k in range(28):
                    a = 2 * math.pi * k / 28
                    if math.sin(a) > 0.82 and i < 9:     # the cowl's opening
                        continue
                    faces.append((i * 28 + k, i * 28 + (k + 1) % 28, (i + 1) * 28 + (k + 1) % 28, (i + 1) * 28 + k))
            # (owner 2026-11-23: wraith heads stay clear: the cowl is not worn)
            # a tattered spectral capelet from the hood over the shoulders, open at the front so the uniform still shows
            cap = hqwing.Part()
            N, S = 40, 6
            for i in range(S + 1):
                t = i / S
                z = 4.02 - 0.9 * t
                for k in range(N):
                    a = 2 * math.pi * k / N
                    rx, ry = 1.16 + 0.12 * t, 0.68 + 0.1 * t
                    hem = 0.18 * t ** 2 * (math.sin(a * 7) + 0.6 * math.sin(a * 13 + 1))
                    cap.v.append(Vector((rx * math.cos(a), ry * math.sin(a), z - max(0.0, hem))))
            for i in range(S):
                for k in range(N):
                    a = 2 * math.pi * (k + 0.5) / N
                    if math.sin(a) > 0.55:        # open at the front
                        continue
                    cap.f.append((i * N + k, i * N + (k + 1) % N, (i + 1) * N + (k + 1) % N, (i + 1) * N + k))
            add(add_mods(mesh_obj(f"{tag}Capelet", cap.v, cap.f, F["shroud"]), thick=0.025, subd=2), "Torso")
            add(hq_wings(tag, "wraithveil", "Midnight", "Ivory", 0.95), "Torso")
        else:
            # Frost Revenant: a crown of ice, ice spikes at the shoulders, spectral chains, frost-tipped fingers
            # (owner 2026-11-23: wraith heads stay clear: no ice crown)
            for sx in (-1, 1):
                key = "RArm" if sx > 0 else "LArm"
                for k in range(9):
                    d = Vector((sx * random.uniform(0.4, 1), random.uniform(-0.6, 0.6), random.uniform(0.3, 1))).normalized()
                    p = project(bv[key], Vector((1.5 * sx, 0, 3.75)) + d * 0.6, -d, 0.0)
                    L = random.uniform(0.25, 0.6)
                    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=L * 0.2, radius2=0.0, depth=L, location=p + d * L * 0.45)
                    c = bpy.context.active_object; c.name = f"{tag}Spike{sx}_{k}"; c.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
                    c.data.materials.append(M["ice"]); add(c, key)
            # chains: links along a loop round the chest and one hanging from the left wrist
            loop = ring_on_torso(bv["Torso"], 3.0, 0.07, n=26)
            for k in range(26):
                p, q = loop[k], loop[k + 1]
                bpy.ops.mesh.primitive_torus_add(major_radius=0.07, minor_radius=0.018, location=(p + q) / 2)
                lk = bpy.context.active_object; lk.name = f"{tag}Link{k}"
                lk.rotation_euler = (q - p).to_track_quat("X", "Z").to_euler(); lk.rotation_euler.rotate_axis("X", (math.pi / 2) * (k % 2))
                lk.scale = (1.5, 1, 1); lk.data.materials.append(F["chain"]); add(lk, "Torso")
            for k in range(9):
                p = Vector((-1.5, 0.1, 2.05 - 0.13 * k))
                bpy.ops.mesh.primitive_torus_add(major_radius=0.06, minor_radius=0.016, location=p)
                lk = bpy.context.active_object; lk.name = f"{tag}Hang{k}"; lk.rotation_euler = (0, math.pi / 2 * (k % 2), math.pi / 2)
                lk.scale = (1, 1, 1.5); lk.data.materials.append(F["chain"]); add(lk, "LArm")
            add(hq_wings(tag, "rime", "Midnight", "Ivory", 0.85), "Torso")
            add(surface_patch(f"{tag}FrostL", bv["LLeg"], Vector((-0.5, 0.6, 0.5)), FW, UP, 0.8, M["frost"], res=36, height=0.04, rough=1.2, rough_scale=24), "LLeg")
            add(surface_patch(f"{tag}FrostR", bv["RLeg"], Vector((0.5, 0.6, 0.5)), FW, UP, 0.8, M["frost"], res=36, height=0.04, rough=1.2, rough_scale=24), "RLeg")

    for ob, part in made:
        if ob.vertex_groups:
            continue
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        coll.objects.link(ob)
        copy_weights(ob, o[part], arm)
    # a menacing stance: arms forward and down, claws ready; the head lowered a little
    pose(arm, "R A", "X", 30); pose(arm, "R E", "X", 35); pose(arm, "R A", "Y", -10)
    pose(arm, "L A", "X", 20); pose(arm, "L E", "X", 45); pose(arm, "L A", "Y", 12)
    pose(arm, "Head", "X", 8)
    pose(arm, "R L", "X", 8); pose(arm, "L L", "X", -6)
    return coll, arm


# ---------------------------------------------------------------- the race sheet: 2 directions x (tall male, short female)
CAST = {
    "Vampire": [(1, "muscular", "M", 1.22, "Vampire"), (1, "petite", "F", 0.90, "Vampire2"), (2, "athletic", "M", 1.22, "Vampire"), (2, "curvy", "F", 0.90, "Vampire2")],
    "Werewolf": [(1, "heavy", "M", 1.22, "Werewolf"), (1, "toned", "F", 0.95, "Werewolf2"), (2, "muscular", "M", 1.22, "Werewolf2"), (2, "plus", "F", 0.95, "Werewolf")],
    "Ghoul": [(1, "lean", "M", 1.14, "Ghoul"), (1, "curvy", "F", 0.82, "Ghoul2"), (2, "stocky", "M", 1.14, "Ghoul2"), (2, "petite", "F", 0.82, "Ghoul")],
    "Wraith": [(1, "standard", "M", 1.22, "Wraith"), (1, "strong", "F", 0.90, "Wraith2"), (2, "heavy", "M", 1.22, "Wraith2"), (2, "toned", "F", 0.90, "Wraith")],
}
arms, REST = {}, {}
xs = [12.5, 4.2, -4.2, -12.5]
for i, (direction, body, gender, scale, skin_key) in enumerate(CAST[RACE]):
    tag = "ABCD"[i]
    coll, arm = build(tag, RACE, direction, body, gender, skin_key)
    REST[tag] = arm.matrix_world.copy()
    base = arm.location.copy()
    arm.scale = (scale, scale, scale)
    arm.location = (base.x * scale + xs[i], base.y * scale, base.z * scale)
    arm.rotation_euler = (0, 0, math.radians(-12 if i % 2 == 0 else 12))
    arms[tag] = arm
bpy.context.view_layer.update()

bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0))
m, nt, b = node_mat("Floor", (0.05, 0.045, 0.05), rough=0.6); add_bump(nt, b, 2.5, 0.2)
bpy.context.active_object.data.materials.append(m)
bpy.ops.mesh.primitive_plane_add(size=80, location=(0, -16, 18), rotation=(math.pi / 2, 0, 0))
bpy.context.active_object.data.materials.append(node_mat("Back", (0.025, 0.02, 0.03), rough=0.9)[0])
world = bpy.data.worlds.new("W"); sc.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.012, 0.011, 0.016, 1)


def light(name, loc, energy, color, size, aim=(0, 0, 3)):
    L = bpy.data.lights.new(name, "AREA"); L.energy = energy; L.color = color; L.size = size
    ob = link(bpy.data.objects.new(name, L)); ob.location = loc
    ob.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


light("Key", (8, 14, 11), 3600, (1.0, 0.9, 0.8), 7)
light("Fill", (-11, 11, 6), 1100, (0.6, 0.7, 1.0), 9)
light("Rim", (0, -12, 10), 3200, (0.9, 0.75, 1.0), 7)
light("Moon", (-6, -6, 14), 1500, (0.7, 0.8, 1.0), 4)
sc.render.engine = "CYCLES"
sc.cycles.samples = 24 if QUICK else 160
sc.cycles.use_denoising = True
try:
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
except Exception:
    pass
cam_d = bpy.data.cameras.new("Cam"); cam = link(bpy.data.objects.new("Cam", cam_d)); sc.camera = cam


def shoot(name, loc, aim, lens, w, h):
    cam.location = loc
    cam.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    cam_d.lens = lens
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.filepath = os.path.join(OUT, f"{RACE.lower()}_{name}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", sc.render.filepath)


def fig_pt(tag, p):
    return arms[tag].matrix_world @ REST[tag].inverted() @ Vector(p)


W, H = (960, 540) if QUICK else (1920, 1080)
shoot("lineup", (0, 38, 7.5), (0, 0, 3.4), 42, W, H)
cw = 540 if QUICK else 1080
for tag, label in (("A", "d1"), ("C", "d2")):
    shoot(f"{label}_front", fig_pt(tag, (2.6, 8.5, 5.2)), fig_pt(tag, (0, 0, 3.3)), 50, cw, cw)
    shoot(f"{label}_back", fig_pt(tag, (-3.2, -8.5, 5.4)), fig_pt(tag, (0, 0, 3.3)), 50, cw, cw)
print("DONE")
