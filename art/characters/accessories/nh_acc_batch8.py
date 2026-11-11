"""Accessories batch 8: Kit B, "The Headmaster's Circle" (the admin regalia, staff only; the greatcoat, Kit B 2, is built
with the Delinquents' long coat in the coat batch).

  CrowMantle      a feathered shoulder mantle (rows of black contour feathers over a leather hide, a bound neck edge, an
                  iron clasp of two crescent bosses at the throat) and two perched crows (one on each shoulder) with
                  ember eyes. Pieces CrowMantle (rigid) and MantleCrows (the crows, idle bones in groups A and B).
                  Slot Shoulders. extra.json: the crows' idle, a slow feather drop (emitter spec), the eyes' pulse
  ThornCrown      a circlet of brass thorns over a filigree band between two twisted rope rims, a crimson stone at the
                  front (glow, pulse 3 s). Slot Hat, Head mount, per-hair fits
  RavenPauldron   one pauldron on the LEFT arm (the right is the sword arm): a blackened-brass cop and four lames with
                  gilt rolled edges, filigree and rivets, a raven skull in bone on the crown with ember eyes (pulse).
                  Slot Shoulders (so it can't be worn with the mantle)
  IronKeys        three large ornate iron keys orbiting the shoulders slowly, above every arm swing, under every hat
                  brim, a faint ember glow in their bows. Slot Halo, Torso mount (extra.json orbit + bob)
  ShadowTrail     smoke and feathers at the feet while walking: a tiny hidden anchor below the feet (z -3.09: the
                  striding legs sweep down to z -3.06) and an emitter spec (extra.json trail). Slot Trail
  ChainedLedger   a heavy black ledger floating open beside the right shoulder, its pages turning by themselves
                  (Page1..Page6, idle Ledger, a slow bob), chained by a short iron chain to an iron cuff on the right
                  wrist. Pieces Ledger and LedgerChain, both riding the right arm. Slot Familiar
  SigilHalo       a crimson runic sigil ring floating behind the head, spinning slowly about the head's forward axis;
                  glow + flare. Slot Halo, Head mount
  SealOfOffice    a heavy chain of office: alternating gilt plaques and brass S-links over the shoulders and down the
                  chest to a large medallion (a crowned crescent moon, crossed keys and a crow on crimson enamel).
                  Slot Collar
  HeadSignet      the Headmaster's signet on the left hand: the crest in gilt on crimson enamel. Slot Ring
  OfficeStaff     a raven-headed staff of office held in the right hand like a walking staff (in front of the hand, the
                  foot 0.14 off the ground, the head at shoulder height), crimson glowing eyes (pulse). Slot Hand
  ObserverMask    "Observer": a porcelain half-mask, one eye open-carved with a gilt rayed rim, the other painted shut
                  (a gilt-lashed lid and a gilt tear), gilt kintsugi crackle. Slot Face, per-hair fits like the masks

Space as nh_acc (studs, -Y front, +X the character's left). Head part centre (0, 0, 1.5).
Run (geometry): E:/Blender/blender.exe -b --factory-startup -P nh_acc.py -- batch8 --nobake --norender
Bake: bash E:/NH-Work/acc/bake_batch.sh batch8
The game-side motion check (orbits at every angle and bob, the crows' and the ledger's idle limits, the staff in the
swinging arm against the hats at their hair fits, the keys against the arms at every swing angle):
  E:/Blender/blender.exe -b --factory-startup -P nh_acc_batch8.py -- --motioncheck
Hair fits (acc_hairfit, then the mask refitted as the game wears it: a uniform scale about the headband, no lift):
  E:/Blender/blender.exe -b --factory-startup -P nh_acc_batch8.py -- --hairfit --items <Items>
then (after the bake): the motion check with --writehair (refuses the hairs a moving piece meets in any pose, refits
the spinning halo), python acc_hairgroup.py, acc_hatcapes.py --items ThornCrown,SigilHalo,ObserverMask
"""
import math, random, os, json, sys
import bpy, bmesh
from mathutils import Vector, Matrix, Euler
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nh_acc as A
from nh_acc import item, piece, lerp, smooth
from nh_acc_batch1 import frame, offset_poly, ccw, bez, crescent, drape_point
import nh_acc_batch3 as B3
import nh_acc_batch4 as B4
import nh_acc_batch5 as B5
import nh_acc_batch2 as B2

EMBER = (1.0, 0.34, 0.07)
CRIM = (0.92, 0.06, 0.12)
HEAD_C = Vector((0, 0, 1.5))
SHORT_HAIR = {"male": "Males_Short", "female": "Females_Straight_Bob"}


def write_extra(key, data):
    with open(os.path.join(A.OUT, "layout", f"{key}.extra.json"), "w") as fh:
        json.dump(data, fh, indent=1)


def kmats(M):
    """the regalia palette: blackened brass, gilt, iron, bone, porcelain, crimson enamel, ember and crimson glows"""
    return dict(
        bbrass=A.mat_metal("BlackBrass", (0.15, 0.105, 0.052), rough=0.36, scratch=0.7, wear=0.8, dirt=0.85,
                           tarnish=(0.035, 0.026, 0.016)),
        gilt=M["gold"], brass=M["brass"], brassold=M["brassold"], iron=M["iron"], steel=M["steel"],
        bone=M["bone"], porcelain=M["porcelain"], enamel=M["crimson_enamel"], black=M["black_enamel"],
        leather=M["leather_black"], paper=M["paper"], velvet=M["crimson_velvet"],
        ember=A.mat_glow("KBEmber", EMBER), crim=A.mat_glow("KBCrimson", CRIM))


def to_mesh_space(v, mount):
    return [round(x, 4) for x in A.to_rbx(Vector(v) - A.MOUNT_CENTRE[mount])]


# ================================================================== shared shapes
def feathers(name, spines, mat, th=0.006):
    """many small contour feathers in one mesh: spines = [(points along the rachis, outward normal at each, width)];
    each a shallow V vane (the rachis up, the edges down toward what it lies on), widest a third along, a rounded tip,
    two shells and rims"""
    verts, faces = [], []
    for pts, nrms, W in spines:
        nv = len(pts) - 1
        top, bot = [], []
        for j, (c, n) in enumerate(zip(pts, nrms)):
            t = j / nv
            d = (pts[min(j + 1, nv)] - pts[max(j - 1, 0)]).normalized()
            s = d.cross(n).normalized()
            nn = s.cross(d).normalized()
            w = W * (0.62 + 0.38 * math.sin(math.pi * min(1.0, 0.25 + 0.85 * t))) * (1 - 0.78 * smooth(0.62, 1.0, t))
            tt = th * (1 - 0.55 * t)
            rt, rb = [], []
            for u in (-1.0, 0.0, 1.0):
                p = c + s * (u * w / 2) - nn * (0.16 * w * abs(u))
                k = 0.2 + 0.8 * (1 - abs(u))
                rt.append(len(verts)); verts.append(p + nn * (tt * k / 2))
                rb.append(len(verts)); verts.append(p - nn * (tt * k / 2))
            top.append(rt); bot.append(rb)
        for j in range(nv):
            for i in range(2):
                faces.append([top[j][i], top[j][i + 1], top[j + 1][i + 1], top[j + 1][i]])
                faces.append([bot[j][i], bot[j + 1][i], bot[j + 1][i + 1], bot[j][i + 1]])
            for i in (0, 2):
                faces.append([top[j][i], top[j + 1][i], bot[j + 1][i], bot[j][i]])
        for j in (0, nv):
            for i in range(2):
                faces.append([top[j][i], bot[j][i], bot[j][i + 1], top[j][i + 1]])
    ob = A.mesh_from(name, verts, faces, mat)
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data); bm.free()
    return ob


def crown_outline(w=1.0, h=1.0):
    """a five-pointed crown (x across, z up, base at z 0), ball-tipped points as small bumps"""
    pts = [(-0.50, 0.0), (0.50, 0.0), (0.50, 0.22), (0.64, 0.70), (0.30, 0.38), (0.15, 0.62), (0.0, 0.86),
           (-0.15, 0.62), (-0.30, 0.38), (-0.64, 0.70), (-0.50, 0.22)]
    return ccw([(x * w, z * h) for x, z in pts])


def crow_outline(s=1.0):
    """a crow perched, side on, facing +x (x along, z up), about 1.3 long at s = 1"""
    pts = [(-0.62, -0.10), (-0.60, -0.04), (-0.30, 0.06), (0.0, 0.20), (0.20, 0.30), (0.32, 0.36), (0.42, 0.33),
           (0.62, 0.25), (0.67, 0.21), (0.44, 0.18), (0.37, 0.12), (0.31, -0.06), (0.14, -0.20), (0.10, -0.30),
           (0.15, -0.37), (0.0, -0.37), (-0.02, -0.25), (-0.18, -0.17)]
    return ccw([(x * s, z * s) for x, z in pts])


def key_shapes(L, kind="quatre"):
    """a small flat key (x along from the bow at 0 to the bit at L, z up): [(outline, holes)]"""
    r = L * 0.17
    out = []
    if kind == "quatre":
        bow = B4.quatrefoil(r) if hasattr(B4, "quatrefoil") else A.circle_pts(0, 0, r, 20)
        bow = [(x, z) for x, z in bow]
        out.append((ccw(bow), [ccw([(x * 0.55, z * 0.55) for x, z in bow])[::-1]]))
    else:
        out.append((A.circle_pts(0, 0, r, 20), [A.circle_pts(0, 0, r * 0.55, 16)[::-1]]))
    w = L * 0.035
    out.append((ccw([(r * 0.9, -w), (L, -w), (L, w), (r * 0.9, w)]), []))
    out.append((ccw([(L * 0.72, -w), (L * 0.98, -w), (L * 0.98, -L * 0.17), (L * 0.88, -L * 0.17), (L * 0.88, -L * 0.10),
                     (L * 0.82, -L * 0.10), (L * 0.82, -L * 0.17), (L * 0.72, -L * 0.17)]), []))
    return out


def crest(name, F, size, gilt, silver, crow_mat, depth=0.010, keys=True, crow=True):
    """the school crest in relief, in the (x, z) plane of frame F (front toward -Y): crossed keys behind a crescent
    moon, a crown over it, a crow perched in the crescent's hollow"""
    s = size
    if keys:
        for k, a in enumerate((-38, 38)):
            R = F @ Matrix.Translation((0, 0.0005, -0.02 * s)) @ Matrix.Rotation(math.radians(a + 90), 4, "Y") @ \
                Matrix.Translation((-0.48 * s, 0, 0))
            for j, (o, holes) in enumerate(key_shapes(0.96 * s, "ring")):
                A.extrude_poly(f"{name}Key{k}_{j}", o, depth * 0.8, gilt, R, bevel=0.0, holes=holes)
    A.extrude_poly(f"{name}Moon", crescent(0.0, -0.04 * s, 0.30 * s, 0.11 * s, 0.07 * s, 0.25 * s), depth, silver,
                   F @ Matrix.Translation((0, -depth * 0.6, 0)), bevel=0.0)
    A.extrude_poly(f"{name}Crown", crown_outline(0.36 * s, 0.30 * s), depth, gilt,
                   F @ Matrix.Translation((0, -depth * 0.6, 0.29 * s)), bevel=0.0)
    if crow:
        A.extrude_poly(f"{name}Crow", crow_outline(0.18 * s), depth * 1.25, crow_mat,
                       F @ Matrix.Translation((0.04 * s, -depth * 0.9, -0.02 * s)), bevel=0.0)


# ================================================================== 1. the murder of crows mantle
MN_R = 0.78            # the mantle's inner edge (plan radius about the neck)
MN_PHI0 = 0.16         # the front opening: the edges at +-9 degrees
MN_HIDE = 0.014
MN_LIFT = 0.008 + MN_HIDE / 2
CROW_S = 0.88
CROWS = [("A", Vector((0.86, 0.03)), math.radians(12)), ("B", Vector((-0.86, -0.01)), math.radians(-16))]
CROW_LIST = []          # (letter, crow-local -> character matrix), filled by the builder for the rig


def mn_hem(phi):
    """plan radius of the hem at angle phi (0 = the front centre, +90 the left side): on the shoulder tops it stops at
    the arm's edge (|x| 0.94), down the front and the back it hangs a drop below the top edge"""
    s, c = abs(math.sin(phi)), math.cos(phi)
    D = (0.50 if c > 0 else 0.56) * (0.70 + 0.30 * abs(c))
    r1 = 0.94 / max(s, 1e-6)
    r2 = (0.5 + D) / max(abs(c), 1e-6)
    return min(r1, r2)


def mn_plan(phi, f):
    r = lerp(MN_R, mn_hem(phi), f)
    x, y = r * math.sin(phi), -r * math.cos(phi)
    if abs(x) > 0.972:
        k = 0.972 / abs(x); x *= k; y *= k
    return x, y


def mn_point(phi, f, lift):
    x, y = mn_plan(phi, f)
    return drape_point(x, y, 1.0, lift)


def _crows_rig(ob):
    bones = [("Root", Vector((0, 0, 1.0)), Vector((0, 0, 1.08)), None), ("H0", Vector((0, 0, 1.0)), Vector((0, 0, 1.05)), "Root")]
    for L, Mx in CROW_LIST:
        for n, h, t, p in B5.CROW_BONES[2:]:
            bones.append((n + L, Mx @ (Vector(h) + B5.CROW_AT), Mx @ (Vector(t) + B5.CROW_AT), "H0" if p == "H0" else p + L))
    return _idle_rig(ob, bones, "Root")


def _idle_rig(ob, bones, fallback):
    """an idle rig from the parts' vertex groups (bones named for the controller, not a sway chain), at most 4
    normalised weights a vertex; unweighted vertices ride `fallback`"""
    arm_d = bpy.data.armatures.new(f"{ob.name}Rig")
    arm = A._new_obj(f"{ob.name}Rig", arm_d)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    eb = {}
    for name, head, tail, parent in bones:
        b = arm_d.edit_bones.new(name)
        b.head, b.tail, b.roll = Vector(head), Vector(tail), 0.0
        if parent:
            b.parent = eb[parent]
        eb[name] = b
    bpy.ops.object.mode_set(mode="OBJECT")
    for name, *_ in bones:
        if ob.vertex_groups.get(name) is None:
            ob.vertex_groups.new(name=name)
    gi = {g.index: g.name for g in ob.vertex_groups}
    fb = ob.vertex_groups[fallback]
    for v in ob.data.vertices:
        ws = sorted(((gi[g.group], g.weight) for g in v.groups if g.weight > 1e-4), key=lambda t: -t[1])
        if not ws:
            fb.add([v.index], 1.0, "REPLACE"); continue
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


CROW_IDLE_B8 = {   # degrees about each bone's own Y; + turns the beak toward +X (the character's left)
    "HeadA": (-25, 70), "HeadB": (-70, 25),      # never toward the wearer's head (the hair)
    "LidLA": (0, 88), "LidRA": (0, 88), "LidLB": (0, 88), "LidRB": (0, 88),
    "TailA": (0, 16), "TailB": (0, 16),          # never down into the mantle's feathers
    "WingLA": (0, 12), "WingRA": (0, 12), "WingLB": (0, 12), "WingRB": (0, 12),
}


@item("CrowMantle", "Murder of Crows mantle", views=["front34", "front", "side", "back", "close"],
      close=((3.4, -4.6, 2.2), (0, -0.05, 1.08), 72))
def build_mantle(M):
    A.MANNEQUIN_HAIR = dict(SHORT_HAIR)
    K = kmats(M)
    plume = B5.mat_feather("MantlePlume", rgb=(0.015, 0.015, 0.020), sheen_tint=(0.30, 0.30, 0.72))
    quill = B5.mat_feather("MantleQuill", rgb=(0.011, 0.012, 0.017), sheen_tint=(0.24, 0.33, 0.80))
    hide = A.mat_leather("MantleHide", (0.045, 0.040, 0.045), scale=2.6)
    piece("CrowMantle", "Torso")
    NP, NF = 56, 5
    phis = [lerp(MN_PHI0, 2 * math.pi - MN_PHI0, j / NP) for j in range(NP + 1)]
    G = [[mn_point(ph, i / (NF - 1), MN_LIFT) for ph in phis] for i in range(NF)]
    A.surface("MantleHideBody", G, MN_HIDE, hide)
    # the neck edge bound in leather, and the front edges
    B4.wire("MantleNeckBind", [tuple(mn_point(ph, 0.0, MN_LIFT + 0.004)) for ph in phis], 0.011, K["leather"], sides=5)
    # rows of contour feathers, the rows nearer the neck lying over the ones below (shingled), the last row's tips
    # past the hem as a feathered fringe
    rows = [(0.00, 0.34, 0.029, 22), (0.19, 0.53, 0.023, 24), (0.38, 0.72, 0.017, 26), (0.57, 0.92, 0.011, 28), (0.76, 1.12, 0.005, 30)]
    rng = random.Random(8)
    spines = {0: [], 1: []}
    feet = [Vector((p.x, p.y)) for _, p, _ in CROWS]
    for r, (f0, f1, off, n) in enumerate(rows):
        for k in range(n):
            ph = lerp(MN_PHI0 + 0.03, 2 * math.pi - MN_PHI0 - 0.03, (k + 0.5 * (r % 2)) / (n - 0.5))
            ph += rng.uniform(-0.02, 0.02)
            a0 = f0 + rng.uniform(-0.03, 0.02)
            a1 = f1 + rng.uniform(-0.04, 0.05)
            root_plan = Vector(mn_plan(ph, a0))
            if any((root_plan - ft).length < 0.075 for ft in feet):
                continue   # the crows' feet grip the hide here
            pts, nrms = [], []
            for q in range(5):
                f = lerp(a0, a1, q / 4)
                lift = MN_LIFT + MN_HIDE / 2 + off - 0.004 * (q / 4) ** 2
                p = mn_point(ph, f, lift)
                pts.append(p); nrms.append(B3.outward(p))
            dphi = (2 * math.pi - 2 * MN_PHI0) / n
            wid = max(0.06, min(0.16, MN_R * dphi * 1.85 * (1 + 0.5 * (a0 + a1) / 2)))
            spines[rng.random() < 0.35].append((pts, nrms, wid * rng.uniform(0.9, 1.1)))
    feathers("MantleFeathers", spines[0], plume, th=0.006)
    feathers("MantleFeathersDark", spines[1], quill, th=0.006)
    # the iron clasp: two domed bosses on the front edges with a gilt crescent each, hooked together by an iron bar
    zc = None
    for sx in (-1, 1):
        p = mn_point(sx * MN_PHI0 if sx > 0 else 2 * math.pi - MN_PHI0, 0.10, MN_LIFT + MN_HIDE / 2)
        zc = p.z
        c = Vector((sx * 0.118, p.y - 0.004, p.z))
        A.lathe(f"ClaspBoss{sx}", [(0.0, 0.034), (0.026, 0.031), (0.044, 0.022), (0.054, 0.010), (0.056, 0.0), (0.0, 0.0)],
                (0, 0, 0), K["iron"], seg=28).matrix_world = Matrix.Translation(c) @ Matrix.Rotation(math.radians(90), 4, "X")
        A.torus(f"ClaspBossRim{sx}", 0.052, 0.006, c + Vector((0, -0.010, 0)), K["iron"], rot=(math.radians(90), 0, 0), major=28, minor=5)
        A.extrude_poly(f"ClaspMoon{sx}", crescent(0, 0, 0.030, sx * 0.011, 0.006, 0.025), 0.008, K["gilt"],
                       frame((c.x, c.y - 0.030, c.z)), bevel=0.0)
    for sx in (-1, 1):
        A.torus(f"ClaspLoop{sx}", 0.020, 0.0065, (sx * 0.052, -0.505 - MN_LIFT - 0.030, zc), K["iron"],
                rot=(math.radians(90), 0, 0), major=16, minor=5)
    A.tube("ClaspBar", [(-0.07, -0.555, zc), (0.0, -0.562, zc - 0.006), (0.07, -0.555, zc)], 0.0085, K["iron"], res=6)

    # ---- the two crows (the batch 5 familiar, ember-eyed, a little smaller), one perched on each shoulder
    piece("MantleCrows", "Torso", rig=_crows_rig)
    CROW_LIST.clear()
    ember = K["ember"]
    for L, at, yaw in CROWS:
        n0 = len(A.PARTS)
        made = B5.crow_parts(M)
        Mx = Matrix.Translation((at.x, at.y, 0)) @ Matrix.Rotation(yaw, 4, "Z") @ Matrix.Scale(CROW_S, 4) @ \
            Matrix.Translation(-B5.CROW_AT)
        for ob, _ in made:
            ob.matrix_world = Mx @ ob.matrix_world
            if len(ob.data.polygons) > 40:   # two crows on one piece: about half the familiar's density each
                dm = ob.modifiers.new("Dec", "DECIMATE"); dm.ratio = 0.5
        bpy.context.view_layer.update()
        zmin = min((ob.matrix_world @ v.co).z for ob, _ in made for v in ob.data.vertices)
        lift = Matrix.Translation((0, 0, 1.0 + MN_LIFT + MN_HIDE / 2 + 0.003 - zmin))
        for ob, _ in made:
            ob.matrix_world = lift @ ob.matrix_world
            for g in ob.vertex_groups:
                if g.name != "Root":
                    g.name = g.name + L
            for i, m in enumerate(ob.data.materials):
                if m.name.startswith("CrowEye") or m.name.startswith("CrowRingGem"):
                    ob.data.materials[i] = ember
                elif m.name.startswith("Silver"):
                    ob.data.materials[i] = K["bbrass"]
        CROW_LIST.append((L, lift @ Mx))
    write_extra("CrowMantle", {
        "MantleCrows": {"idle": "Familiar", "pulse": 4.0,
                        "bones": {n: {"axis": [0, 1, 0], "min": lo, "max": hi} for n, (lo, hi) in CROW_IDLE_B8.items()}},
        "CrowMantle": {"emitters": [{
            "name": "FeatherDrift", "always": True, "kind": "feather",
            "texture": "a single black crow feather (the crow VFX's feather sprite), slight blue-violet sheen",
            "at": [0, 1.05, 0.05], "spread": [1.7, 0.1, 1.0], "rate": 0.06,
            "lifetime": [4.0, 6.0], "speed": [0.15, 0.35], "direction": "down (-Y), drifting", "acceleration": [0, -0.6, 0],
            "drag": 1.5, "rotation": [0, 360], "rot_speed": [-90, 90], "size": [0.22, 0.20], "transparency": [0.0, 1.0],
            "light_emission": 0, "lock_to_part": False,
            "note": "Torso mount space: the odd feather drifting off the mantle's shoulders and down, about 3-4 a minute "
                    "(rate 0.06/s). Off with Reduce Motion"}]}})
    return dict(notes="a feathered shoulder mantle: four shingled rows of black contour feathers (blue-violet sheen) over "
                      "a leather hide, the last row a feathered fringe past the hem; a bound neck edge; an iron clasp of "
                      "two domed bosses with gilt crescents at the throat. Two crows perch on the shoulders (MantleCrows): "
                      "ember eyes and blackened-brass leg rings, idle bones in groups A (left) and B (right)",
                glow=list(EMBER))


# ================================================================== 3. the crown of thorned brass
CR_R = 0.632
CR_Z0, CR_Z1 = 1.815, 1.905


def _helix(R, z, amp, turns, phase, n):
    return [((R + amp * math.cos(turns * 2 * math.pi * i / n + phase)) * math.cos(2 * math.pi * i / n),
             (R + amp * math.cos(turns * 2 * math.pi * i / n + phase)) * math.sin(2 * math.pi * i / n),
             z + amp * math.sin(turns * 2 * math.pi * i / n + phase)) for i in range(n)]


@item("ThornCrown", "Crown of Thorned Brass", lens=40, focus=(0, 0, 1.0), close=((2.6, -4.4, 2.6), (0, 0, 1.95), 95))
def build_crown(M):
    A.MANNEQUIN_HAIR = dict(SHORT_HAIR)
    K = kmats(M)
    brass, old, gilt = K["brass"], K["brassold"], K["gilt"]
    piece("ThornCrown", "Head")
    # the band: a slightly flared brass ring, a gilt filigree scroll raised on it
    A.lathe("CrownBand", [(CR_R - 0.010, CR_Z0 + 0.004), (CR_R + 0.004, CR_Z0), (CR_R + 0.010, CR_Z0 + 0.012),
                          (CR_R + 0.008, CR_Z1 - 0.012), (CR_R + 0.012, CR_Z1), (CR_R - 0.008, CR_Z1 - 0.002),
                          (CR_R - 0.010, CR_Z0 + 0.004)], (0, 0, 0), old, seg=64)

    def band_map(u, v):
        a = math.pi * 2 * u
        return Vector(((CR_R + 0.0125) * math.cos(a), (CR_R + 0.0125) * math.sin(a), lerp(CR_Z0 + 0.016, CR_Z1 - 0.016, (v + 1) / 2)))
    lines = B4.filigree("band")
    for seg in range(5):
        for k, ln in enumerate(lines):
            pts = [tuple(band_map((seg + (u + 1) / 2) / 5, v * 0.9)) for u, v in ln]
            B4.wire(f"CrownFil{seg}_{k}", pts, 0.0036, gilt, sides=3)
    # a twisted rope rim (two strands) over the band's top edge, a plain roll under it
    for ph in (0.0, math.pi):
        B4.wire(f"CrownRope{ph:.1f}", _helix(CR_R + 0.010, CR_Z1 + 0.004, 0.0062, 30, ph, 100), 0.0062, brass, sides=4, closed=True)
    A.torus("CrownRoll", CR_R + 0.008, 0.0070, (0, 0, CR_Z0 - 0.001), brass, major=72, minor=5)
    # thorns: 16 long curved thorns (the front one tallest), each with two small side thorns; vine arches between
    rng = random.Random(3)
    nth = 16
    for k in range(nth):
        a = -math.pi / 2 + 2 * math.pi * k / nth
        ca, sa = math.cos(a), math.sin(a)
        out = Vector((ca, sa, 0))
        front = k == 0
        H = 0.26 if front else (0.18 if k % 2 == 0 else 0.11) * rng.uniform(0.92, 1.08)
        lean = 0.05 + 0.03 * (k % 2)
        base = Vector(((CR_R + 0.006) * ca, (CR_R + 0.006) * sa, CR_Z1 + 0.004))
        pts = [base + out * (lean * (t ** 1.6)) + Vector((0, 0, H * t)) - Vector((-sa, ca, 0)) * (0.012 * math.sin(math.pi * t) * (1 if k % 3 else -1))
               for t in (i / 6 for i in range(7))]
        r0 = 0.020 if front else 0.016
        tip = A.cyl(f"ThornTip{k}", r0 * 0.75, (pts[-1] - pts[-2]).length * 1.25, (0, 0, 0), brass, verts=6, r2=0.0, bevel=0.0)
        d = (pts[-1] - pts[-2]).normalized()
        tip.matrix_world = Matrix.Translation(pts[-2] + d * (pts[-1] - pts[-2]).length * 0.62) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
        # the thorn body: a taper from the base, sampled as stacked cones along the curve
        for q in range(5):
            p0, p1 = pts[q], pts[q + 1]
            rr = r0 * (1 - 0.13 * q)
            cn = A.cyl(f"ThornSeg{k}_{q}", rr * 1.12, (p1 - p0).length, (0, 0, 0), brass, verts=6, r2=rr * 0.95, bevel=0.0)
            dd = (p1 - p0).normalized()
            cn.matrix_world = Matrix.Translation((p0 + p1) / 2) @ dd.to_track_quat("Z", "Y").to_matrix().to_4x4()
        for s, tq in ((1, 0.35), (-1, 0.62)):
            p = pts[int(tq * 6)]
            side = Vector((-sa, ca, 0)) * s
            dirn = (side * 0.8 + out * 0.4 + Vector((0, 0, 0.35))).normalized()
            L = 0.045 if H > 0.15 else 0.032
            st = A.cyl(f"ThornSpur{k}_{s}", 0.0075, L, (0, 0, 0), brass, verts=5, r2=0.0, bevel=0.0)
            st.matrix_world = Matrix.Translation(p + dirn * (L / 2)) @ dirn.to_track_quat("Z", "Y").to_matrix().to_4x4()
        # the vine arch to the next thorn
        a2 = a + 2 * math.pi / nth
        arch = []
        for i in range(9):
            t = i / 8
            aa = lerp(a + 0.05, a2 - 0.05, t)
            arch.append(((CR_R + 0.010) * math.cos(aa), (CR_R + 0.010) * math.sin(aa), CR_Z1 + 0.010 + 0.040 * math.sin(math.pi * t)))
        B4.wire(f"CrownArch{k}", arch, 0.0048, old, sides=4)
        A.sphere(f"CrownArchBud{k}", 0.010, arch[4], gilt, seg=6, rings=4)
    # the crimson stone at the front in a gilt bezel with four claws and a small crescent under it
    sc = Vector((0, -(CR_R + 0.026), (CR_Z0 + CR_Z1) / 2 + 0.004))
    A.sphere("CrownStone", 0.040, sc + Vector((0, -0.004, 0)), K["crim"], scale=(0.82, 0.55, 1.0), seg=16, rings=10)
    A.torus("CrownBezel", 0.036, 0.0075, sc + Vector((0, 0.006, 0)), gilt, rot=(math.radians(90), 0, 0), major=24, minor=4,
            scale=(0.84, 1, 1.0))
    for q in range(4):
        b = math.pi / 4 + q * math.pi / 2
        A.sphere(f"CrownClaw{q}", 0.0085, sc + Vector((0.032 * math.cos(b), -0.012, 0.040 * math.sin(b))), gilt, seg=8, rings=5)
    A.extrude_poly("CrownMoon", crescent(0, 0, 0.022, 0.0, 0.010, 0.018), 0.006, gilt,
                   frame((0, sc.y + 0.006, CR_Z0 + 0.006)), bevel=0.0)
    write_extra("ThornCrown", {"ThornCrown": {"pulse": 3.0, "light": {
        "color": [255, 40, 60], "range": 4, "brightness": 0.5, "at": to_mesh_space(sc, "Head"), "flicker": False}}})
    return dict(notes="a circlet of sixteen curved brass thorns (each with side spurs, the front one tallest) over a "
                      "filigreed band between twisted rope rims, budded vine arches between the thorns, and a crimson "
                      "stone in a gilt four-claw bezel at the front (glow, pulse 3 s)", glow=list(CRIM))


# ================================================================== 4. the raven-skull pauldron
@item("RavenPauldron", "Raven-skull pauldron", views=["front34", "front", "side", "back", "close"],
      close=((4.8, -4.2, 2.3), (1.55, 0, 0.75), 88))
def build_pauldron(M):
    A.MANNEQUIN_HAIR = dict(SHORT_HAIR)
    K = kmats(M)
    bb, gilt, bone = K["bbrass"], K["gilt"], K["bone"]
    piece("RavenPauldron", "LeftArm")
    cp = B4.cop_point
    nu, nv = 18, 22
    G = [[cp(i / nu, lerp(-1, 1, j / nv)) for j in range(nv + 1)] for i in range(nu + 1)]
    A.surface("RPCop", G, 0.016, bb)
    rim = ([cp(0, lerp(-1, 1, j / nv)) for j in range(nv + 1)] + [cp(i / nu, 1) for i in range(1, nu + 1)] +
           [cp(1, lerp(1, -1, j / nv)) for j in range(1, nv + 1)] + [cp(i / nu, -1) for i in range(nu - 1, 0, -1)])
    B4.wire("RPCopRoll", [tuple(p) for p in rim], 0.0115, gilt, closed=True)
    # engraved gilt filigree on the outer flank, front and back, and a band of it along the crown
    def flank(uu, vv, side):
        s = lerp(0.93, 0.60, (vv + 1) / 2)
        v = side * 0.42 + uu * 0.20
        return cp(s, v) + B4.cop_normal(s, v) * 0.0095
    for side in (-1, 1):
        B4.tubes_on(f"RPFil{side}", B4.filigree("panel"), lambda u, v, side=side: flank(u, v, side), 0.0040, gilt)
    for k in range(9):
        v = lerp(-0.84, 0.84, k / 8)
        B4.rivet(f"RPRivI{k}", cp(0.05, v) + B4.cop_normal(0.05, v) * 0.008, B4.cop_normal(0.05, v), gilt, r=0.013, seg=6)
    for k, s in enumerate((0.30, 0.55, 0.80)):
        for sg in (-1, 1):
            B4.rivet(f"RPRivE{k}{sg}", cp(s, sg * 0.93) + B4.cop_normal(s, sg * 0.93) * 0.008, B4.cop_normal(s, sg * 0.93),
                     gilt, r=0.013, seg=6)
    # four lames below the cop, each tucked under the one above, gilt rolled hems and articulation rivets
    lames = ((0.610, 0.455, 0.094), (0.500, 0.345, 0.080), (0.390, 0.235, 0.066), (0.280, 0.130, 0.052))
    for k, (zt, zb, dd) in enumerate(lames):
        _, Lg = B4.wrap_surface(f"RPLame{k}", zt, zb, lambda t, dd=dd: dd + 0.014 * t, bb, thick=0.012, nz=3,
                                x_in=-0.30, a=min(0.16, (dd - 0.016) / 0.4142), n_arc=6, n_face=3, n_out=6)
        B4.edge_roll(f"RPLameRoll{k}", Lg, len(Lg[0]) - 1, 0.0085, gilt)
        for i in (0, len(Lg) // 2, len(Lg) - 1):
            p = Lg[i][1]
            nrm = (p - Vector((1.5, 0, p.z))); nrm.z = 0
            B4.rivet(f"RPLameRiv{k}_{i}", p + nrm.normalized() * 0.008, nrm, gilt, r=0.012, seg=6)
    # the arming strap round the upper arm
    _, S = B4.wrap_surface("RPStrap", 0.105, 0.035, lambda t: 0.020, K["leather"], thick=0.012, nz=1, x_in=-0.47)
    # ---- the raven skull on the crown of the cop, beak forward, on a gilt crescent saddle
    top = cp(0.244, 0.0)                     # the cop's crown (x 1.5, z ~1.10)
    nt = B4.cop_normal(0.244, 0.0)
    sk = top + nt * 0.014
    n_sk = len(A.PARTS)
    A.lathe("RPSaddle", [(0.0, 0.016), (0.070, 0.014), (0.082, 0.006), (0.080, 0.0), (0.0, 0.0)], (0, 0, 0), gilt, seg=24,
            scale=(1.0, 1.35, 1.0)).matrix_world = Matrix.Translation(top + nt * 0.004)
    cz = sk.z + 0.072
    cran = A.sphere("RavenCranium", 1.0, (sk.x, sk.y + 0.055, cz), bone, scale=(0.072, 0.092, 0.066), seg=20, rings=12)
    for v in cran.data.vertices:   # a flatter crown, the brow ridges over the sockets
        co = cran.matrix_world @ v.co
        if co.z > cz + 0.035:
            v.co.z -= (co.z - (cz + 0.035)) * 0.35 / 0.066
    cran.data.update()
    # the beak: a long, deep, slightly hooked bone wedge forward (-Y), upper and lower mandibles
    for jaw, (zt, hu, hl, L) in enumerate(((cz - 0.004, 0.024, 0.010, 0.30), (cz - 0.030, 0.008, 0.012, 0.25))):
        secs = []
        for i in range(11):
            t = i / 10
            y = sk.y + 0.005 - L * t
            zcen = zt - (0.030 if jaw == 0 else 0.010) * t ** 1.8
            bw = 0.030 * (1 - t) ** 0.85 + 0.002
            ring = []
            for q in range(12):
                a = 2 * math.pi * q / 12
                sa = math.sin(a)
                ring.append(Vector((sk.x + bw * math.cos(a), y, zcen + (hu if sa > 0 else hl) * (1 - t) ** 0.7 * sa)))
            secs.append(ring)
        B5.loft(f"RavenBeak{jaw}", secs, bone, cap0=Vector((sk.x, sk.y + 0.008, zt)), cap1=secs[-1][0].lerp(secs[-1][6], 0.5))
    # the sockets (dark rims) and the ember eyes deep in them
    for sx in (-1, 1):
        e = Vector((sk.x + sx * 0.054, sk.y + 0.030, cz + 0.008))
        A.torus(f"RavenSocket{sx}", 0.021, 0.0065, e, bone, rot=(0, math.radians(90), 0), major=16, minor=5)
        A.sphere(f"RavenEye{sx}", 0.017, e + Vector((-sx * 0.004, 0, 0)), K["ember"], seg=12, rings=8)
        # nostril slits on the beak's base
        A.sphere(f"RavenNare{sx}", 0.006, (sk.x + sx * 0.016, sk.y - 0.070, cz + 0.010), K["black"], scale=(0.6, 2.6, 0.7),
                 seg=8, rings=5)
    B5.place_parts(n_sk, Matrix.Translation(top) @ Matrix.Scale(1.3, 4) @ Matrix.Translation(-top))   # read at play distance
    # black feathers fanning back from under the skull over the cop's back
    spn = []
    for k in range(7):
        a = lerp(-0.55, 0.55, k / 6)
        pts, nrms = [], []
        for q in range(5):
            t = q / 4
            v = lerp(0.08, 0.80, t) / 0.63 * 0.63
            s = 0.244 + a * 0.30 * t
            p = cp(max(0.02, min(0.95, s)), min(0.97, v)) + B4.cop_normal(max(0.02, min(0.95, s)), min(0.97, v)) * (0.022 + 0.010 * (1 - t))
            pts.append(p); nrms.append(B4.cop_normal(max(0.02, min(0.95, s)), min(0.97, v)))
        spn.append((pts, nrms, 0.075 - 0.02 * abs(a)))
    plume = B5.mat_feather("PauldronPlume")
    feathers("RPFeathers", spn, plume, th=0.006)
    write_extra("RavenPauldron", {"RavenPauldron": {"pulse": 2.5}})
    return dict(notes="one pauldron on the left arm: a blackened-brass cop over four lames, gilt rolled edges, gilt "
                      "filigree on both flanks, gilt rivets, an arming strap; a raven skull in bone on a gilt saddle on "
                      "the crown, beak forward, ember eyes deep in the sockets (glow, pulse); black feathers fanning back "
                      "over the cop", glow=list(EMBER))


# ================================================================== 5. three ornate iron keys
KEY_R = 1.70
KEY_Z = 1.52
KEY_TILT = math.radians(65)   # the flat faces turned up and out (a low profile over the swinging pauldrons)
KEY_BOB = 0.02
KEY_S = 1.35        # large keys: about 0.86 studs long


def key_build(name, kind, F, K):
    """one large key in its local frame (x along from the bow centre at 0 to the bit, z up, the flat faces toward -Y),
    placed by F"""
    iron, gl = K["iron"], K["ember"]
    th = 0.034
    Fz = F @ Matrix.Translation((0, th / 2, 0))
    if kind == "quatre":
        outer = B4.quatrefoil(0.105, 40)
        inner = [(x * 0.66, z * 0.66) for x, z in outer]
    elif kind == "moon":
        outer = A.circle_pts(0, 0, 0.100, 40)
        inner = A.circle_pts(0, 0, 0.066, 32)
    else:   # a pointed lancet arch
        outer = B5.vesica(0.19, 0.24, 13)
        inner = B5.vesica(0.12, 0.16, 11)
    outer, inner = ccw([(x, z) for x, z in outer]), ccw([(x, z) for x, z in inner])
    A.extrude_poly(f"{name}Bow", outer, th, iron, Fz, bevel=0.004, segments=1, holes=[inner[::-1]])
    # the glowing ember pane in the bow, and its pierced iron tracery over both faces
    A.extrude_poly(f"{name}Glow", offset_poly(inner, -0.004), 0.008, gl, F @ Matrix.Translation((0, 0.004, 0)), bevel=0.0)
    if kind == "quatre":
        trac = [ccw(A.circle_pts(0, 0, 0.022, 14))]
        for q in range(4):
            a = q * math.pi / 2
            trac.append(ccw([(0.020 * math.cos(a + 0.3), 0.020 * math.sin(a + 0.3)), (0.062 * math.cos(a), 0.062 * math.sin(a)),
                             (0.020 * math.cos(a - 0.3), 0.020 * math.sin(a - 0.3))]))
    elif kind == "moon":
        trac = [crescent(0, 0, 0.052, 0.020, 0.010, 0.044)]
    else:
        trac = [ccw([(-0.008, -0.07), (0.008, -0.07), (0.008, 0.07), (-0.008, 0.07)]),
                ccw([(-0.05, -0.008), (0.05, -0.008), (0.05, 0.008), (-0.05, 0.008)])]
    for k, t in enumerate(trac):
        A.extrude_poly(f"{name}Trac{k}", t, 0.020, iron, F @ Matrix.Translation((0, 0.010, 0)), bevel=0.0)
    # a crown finial on top of the bow
    A.extrude_poly(f"{name}Finial", crown_outline(0.09, 0.075), 0.022, iron,
                   F @ Matrix.Translation((0, 0.011, (0.118 if kind != "lancet" else 0.12) - 0.004)), bevel=0.003, segments=1)
    # the shank: a round iron shaft with turned collars, a pipe end; then the bit with its wards
    L = 0.64
    Ax = Matrix.Rotation(math.radians(90), 4, "Y")
    A.lathe(f"{name}Shank", [(0.0, 0.10), (0.024, 0.10), (0.032, 0.118), (0.024, 0.136), (0.020, 0.15), (0.020, 0.40),
                             (0.030, 0.418), (0.030, 0.432), (0.021, 0.45), (0.019, L), (0.0, L)], (0, 0, 0), iron, seg=12,
            ).matrix_world = F @ Ax
    for k, x in enumerate((0.22, 0.27)):
        A.torus(f"{name}Ring{k}", 0.024, 0.0055, (0, 0, 0), iron, major=12, minor=4).matrix_world = \
            F @ Matrix.Translation((x, 0, 0)) @ Ax
    bit = ccw([(L - 0.16, -0.012), (L - 0.005, -0.012), (L - 0.005, -0.125), (L - 0.035, -0.125), (L - 0.035, -0.080),
               (L - 0.060, -0.080), (L - 0.060, -0.125), (L - 0.090, -0.125), (L - 0.090, -0.095), (L - 0.115, -0.095),
               (L - 0.115, -0.125), (L - 0.16, -0.125)])
    A.extrude_poly(f"{name}Bit", bit, 0.026, iron, F @ Matrix.Translation((0, 0.013, 0)), bevel=0.003, segments=1)


@item("IronKeys", "Three ornate iron keys", lens=40, focus=(0, 0, 0.6), close=((4.6, -6.6, 2.8), (0.6, 0, 1.35), 60))
def build_keys(M):
    A.MANNEQUIN_HAIR = dict(SHORT_HAIR)
    K = kmats(M)
    piece("IronKeys", "Torso")
    for k, kind in enumerate(("quatre", "moon", "lancet")):
        phi = math.radians(90 + 120 * k)
        # the key's centre on the orbit, its length along the orbit (tangent), lying tipped back so its flat faces
        # look up and out (the bow's top edge outward): low enough over the swinging pauldrons, under the hat brims
        t = Vector((-math.sin(phi), math.cos(phi), 0))
        o = Vector((math.cos(phi), math.sin(phi), 0))
        X = t
        Z = (Vector((0, 0, 1)) * math.cos(KEY_TILT) + o * math.sin(KEY_TILT)).normalized()
        Y = Z.cross(X).normalized()
        c = o * KEY_R + Vector((0, 0, KEY_Z)) - X * (0.31 * KEY_S)
        F = B4.basis_frame(c, X, Y, Z) @ Matrix.Scale(KEY_S, 4)
        key_build(f"Key{k}", kind, F, K)
    write_extra("IronKeys", {"IronKeys": {"orbit": {"axis": [0, 1, 0], "rpm": 3}, "bob": KEY_BOB, "pulse": 5.0}})
    return dict(notes="three large ornate iron keys (quatrefoil, full-moon and lancet bows with pierced tracery over an "
                      "ember-glowing pane, crown finials, turned collars, warded bits) orbiting the shoulders 1.70 studs "
                      "out at z 1.52, lying tipped back: above the swinging arms and pauldrons, under every hat brim at every hair fit", glow=list(EMBER))


# ================================================================== 6. the shadow trail
@item("ShadowTrail", "Shadow trail", lens=40, focus=(0, 0, -1.2), female=False, close=((2.4, -4.4, -2.2), (0, 0, -2.9), 80))
def build_trail(M):
    A.MANNEQUIN_HAIR = dict(SHORT_HAIR)
    glow = A.mat_glow("TrailAnchor", (0.05, 0.04, 0.06), strength=0.5)
    piece("ShadowTrail", "Torso", kind="Glow", glow=(0.05, 0.04, 0.06))
    A.cyl("TrailAnchorDisc", 0.06, 0.012, (0, 0, -3.09), glow, verts=8, bevel=0.0)
    write_extra("ShadowTrail", {"ShadowTrail": {"trail": True, "hidden": True, "emitters": [
        {"name": "ShadowSmoke", "kind": "smoke", "texture": "soft round smoke puff (the TP VFX smoke sprite)",
         "color": [[0.04, 0.035, 0.05], [0.10, 0.06, 0.09]], "at": [0, -1.0, 0.0], "spread": [1.2, 0.05, 0.9],
         "rate": 18, "lifetime": [0.9, 1.6], "speed": [0.2, 0.6], "direction": "up (+Y) and back (+Z), slow",
         "acceleration": [0, 0.5, 0], "drag": 2.5, "size": [[0.0, 0.5], [0.4, 1.3], [1.0, 1.9]],
         "transparency": [[0.0, 1.0], [0.15, 0.35], [1.0, 1.0]], "light_emission": 0, "lock_to_part": False,
         "rotation": [0, 360], "rot_speed": [-30, 30],
         "note": "dark smoke curling up round the feet while walking (Torso mount space: the anchor sits 0.09 under the "
                 "feet, at the ground)"},
        {"name": "ShadowFeathers", "kind": "feather", "texture": "a single black crow feather sprite",
         "color": [[0.02, 0.02, 0.03], [0.02, 0.02, 0.03]], "at": [0, -1.05, 0.0], "spread": [0.9, 0.05, 0.6],
         "rate": 2.5, "lifetime": [1.2, 2.0], "speed": [0.6, 1.2], "direction": "up and out, then falling",
         "acceleration": [0, -1.2, 0], "drag": 1.2, "size": [0.20, 0.16], "transparency": [0.0, 1.0],
         "rotation": [0, 360], "rot_speed": [-160, 160], "light_emission": 0, "lock_to_part": False,
         "note": "a few feathers kicked up from the smoke"},
        {"name": "ShadowEmbers", "kind": "spark", "optional": True, "color": [[1.0, 0.34, 0.07], [0.6, 0.06, 0.1]],
         "at": [0, -1.0, 0.0], "spread": [0.8, 0.05, 0.5], "rate": 3, "lifetime": [0.6, 1.0], "speed": [0.4, 0.9],
         "size": [0.05, 0.0], "light_emission": 1, "note": "a rare ember eye-glint in the smoke; skip if too busy"}]}})
    return dict(notes="smoke and feathers at the feet while walking: a tiny hidden anchor (a 0.12 disc, Transparency 1 in "
                      "the game) at z -3.09, under the feet (the striding legs sweep down to z -3.06); the emitters are "
                      "described in ShadowTrail.extra.json (trail: they run only while walking; Reduce Motion turns them off)")


# ================================================================== 7. the floating chained ledger
LG_SPINE = Vector((-2.53, 0.02, 0.80))       # the ledger's spine centre (right arm: x -1.5 is the arm's centre)
LG_YAW = math.radians(-32)                   # its open face toward the front and the right
LG_TILT = math.radians(14)                   # tipped back a little
LG_H, LG_W = 0.46, 0.30                      # page height, each half's width
LG_ALPHA = math.radians(11)                  # each half tipped back from the spine (a shallow V)
LG_PAGES = 6
LG_TURN = -142                               # a page turned over (degrees about the gutter, bone Y)
LG_HINGE = Vector((0, -0.047, 0))            # the gutter (book-local): where the two blocks' tops meet, the leaves' hinge
LG_BOB = 0.025
LG_RING = Vector((0, 0.036, -(LG_H + 0.04) / 2 - 0.042))   # the staple ring at the spine's foot (book-local)
LG_RING_R = 0.032


def lg_frame():
    """book-local -> character: local z along the spine (up), local +x the reader's right, local -y toward the reader"""
    return Matrix.Translation(LG_SPINE) @ Matrix.Rotation(LG_YAW, 4, "Z") @ Matrix.Rotation(-LG_TILT, 4, "X")


def _ledger_rig(ob):
    F = lg_frame()
    bot, top = F @ Vector((0, 0, -LG_H / 2)), F @ Vector((0, 0, LG_H / 2))
    hb, ht = F @ (LG_HINGE + Vector((0, 0, -LG_H / 2))), F @ (LG_HINGE + Vector((0, 0, LG_H / 2)))
    bones = [("Root", bot, bot + (top - bot) * 0.3, None)]
    for k in range(1, LG_PAGES + 1):
        bones.append((f"Page{k}", hb, ht, "Root"))
    return _idle_rig(ob, bones, "Root")


def _wrist_cuff(name, z0, z1, d, mat, x_in=-0.20):
    """a U band round the RIGHT arm's front, outer and back faces (the inner face is flush on the torso), from z0 to z1"""
    cols = []
    for j in range(3):
        z = lerp(z0, z1, j / 2)
        cols.append([Vector((-1.5 - X, Y, z)) for X, Y in B4.arm_wrap(d, x_in=x_in, a=0.0)])
    G = [[cols[j][i] for j in range(3)] for i in range(len(cols[0]))]
    return A.surface(name, G, 0.014, mat), G


@item("ChainedLedger", "Floating chained ledger", views=["front34", "front", "side_r", "back", "close"],
      close=((-5.4, -5.2, 1.6), (-2.2, 0, 0.4), 78))
def build_ledger(M):
    A.MANNEQUIN_HAIR = dict(SHORT_HAIR)
    K = kmats(M)
    F = lg_frame()
    cover = A.mat_leather("LedgerCover", (0.040, 0.034, 0.036), scale=3.2, wear=0.6)
    paper = A.mat_set("LedgerPaper", "NH_Paper", tint=(0.92, 0.85, 0.70), scale=3.0, wear=0.25, dirt=0.8)
    edge = A.mat_flat("LedgerEdge", (0.55, 0.06, 0.08), rough=0.4, noise=200, bump=0.08, vary=0.10, wear=0.2)
    piece("Ledger", "RightArm", rig=_ledger_rig)
    n0 = len(A.PARTS)
    ca, sa = math.cos(LG_ALPHA), math.sin(LG_ALPHA)
    halfdir = {1: Vector((ca, -sa, 0)), -1: Vector((-ca, -sa, 0))}
    Wc, Hc, tc = LG_W + 0.025, LG_H + 0.04, 0.026
    for s in (1, -1):
        d = halfdir[s]
        nrm = Vector((0, -1, 0)) - d * d.dot(Vector((0, -1, 0)))
        nrm.normalize()
        # the board
        G = [[Vector((0, 0, 0)) + d * (0.012 + Wc * i / 6) + Vector((0, 0, lerp(-Hc / 2, Hc / 2, j / 6))) + nrm * (-tc / 2 - 0.002)
              for j in range(7)] for i in range(7)]
        A.surface(f"LedgerBoard{s}", G, tc, cover)
        # the page block, its edge gilded crimson, the top page bowing up near the spine
        PB = [[d * (0.016 + (LG_W - 0.006) * i / 8) + Vector((0, 0, lerp(-LG_H / 2, LG_H / 2, j / 6))) +
               nrm * (0.024 - 0.004 * smooth(0.6, 1.0, i / 8)) for j in range(7)] for i in range(9)]
        A.surface(f"LedgerBlock{s}", PB, 0.044, paper)
        A.box(f"LedgerFore{s}", (0.006, 0.050, LG_H - 0.004), (0, 0, 0), edge, bevel=0.002).matrix_world = \
            Matrix.Translation(d * (LG_W + 0.010) + nrm * 0.026) @ Matrix.Rotation(math.atan2(d.y, d.x), 4, "Z")
        # brass corner caps
        for zz in (-1, 1):
            cc = d * (Wc - 0.02) + Vector((0, 0, zz * (Hc / 2 - 0.02))) + nrm * (-0.002)
            A.box(f"LedgerCorner{s}{zz}", (0.050, tc + 0.012, 0.050), (0, 0, 0), K["brassold"], bevel=0.006).matrix_world = \
                Matrix.Translation(cc) @ Matrix.Rotation(math.atan2(d.y, d.x), 4, "Z")
    # the spine: a rounded leather back with raised bands and gilt tooling
    A.lathe("LedgerSpine", [(0.0, -Hc / 2), (0.040, -Hc / 2), (0.046, -Hc / 2 + 0.01), (0.046, Hc / 2 - 0.01), (0.040, Hc / 2),
                            (0.0, Hc / 2)], (0, 0.036, 0), cover, seg=16, scale=(0.8, 1.0, 1.0))
    for k in range(4):
        z = lerp(-Hc / 2 + 0.07, Hc / 2 - 0.07, k / 3)
        A.torus(f"LedgerBand{k}", 0.044, 0.007, (0, 0.036, z), K["gilt"], major=14, minor=4, scale=(0.82, 1.0, 1.0))
    # the clasp strap hanging off the right board with its iron catch, and the iron ring at the spine's foot (the chain)
    d = halfdir[1]
    A.tube("LedgerStrap", [tuple(d * (Wc - 0.01) + Vector((0, 0, 0.0)) + Vector((0, -0.004, 0))),
                           tuple(d * (Wc + 0.05) + Vector((0, 0, -0.03))), tuple(d * (Wc + 0.07) + Vector((0, 0, -0.10)))],
           0.012, cover, res=4, poly=True)
    A.box("LedgerCatch", (0.05, 0.016, 0.06), tuple(d * (Wc + 0.07) + Vector((0, 0, -0.13))), K["iron"], bevel=0.006)
    A.torus("LedgerRing", LG_RING_R, 0.0095, tuple(LG_RING), K["iron"], rot=(0, math.radians(90), 0), major=24, minor=6)
    A.box("LedgerRingTab", (0.03, 0.05, 0.034), (0, 0.036, -Hc / 2 - 0.010), K["iron"], bevel=0.006)
    # the turning pages: six loose leaves lying on the right block, each on its own bone (Page1 on top)
    rightn = Vector((0, -1, 0)) - halfdir[1] * halfdir[1].dot(Vector((0, -1, 0)))
    rightn.normalize()
    page_objs = []
    for k in range(LG_PAGES):
        e = 0.0035 + 0.0042 * (LG_PAGES - 1 - k)      # Page1 on top
        PG = [[LG_HINGE + halfdir[1] * (0.006 + (LG_W - 0.016) * i / 8) + Vector((0, 0, lerp(-LG_H / 2 + 0.012, LG_H / 2 - 0.012, j / 6))) +
               rightn * (e * smooth(0.0, 0.30, i / 8) + 0.006 * math.sin(math.pi * i / 8))
               for j in range(7)] for i in range(9)]
        page_objs.append((A.surface(f"LedgerLeaf{k + 1}", PG, 0.0035, paper), f"Page{k + 1}"))
    B5.place_parts(n0, F)
    for ob, bn in page_objs:
        g = ob.vertex_groups.new(name=bn)
        g.add([v.index for v in ob.data.vertices], 1.0, "REPLACE")
    # ---- the chain rides with the ledger (it bobs with it): from the staple ring at the spine's foot down to the
    # wrist, where its end passes straight down through a flat iron ring on the cuff and is held by a toggle bar
    # under it (a toggle-and-ring fastening): the chain never touches the ring however the ledger bobs
    ring = F @ LG_RING
    TR = Vector((-2.105, 0.0, -0.33))          # the cuff's ring (lying flat, axis vertical)
    TRR, TRW = 0.060, 0.0095
    top = ring - (F.to_3x3() @ Vector((0, 0, 1))) * 0.045
    p3 = TR + Vector((0, 0, 0.16))
    mid1 = top.lerp(p3, 0.40) + Vector((-0.06, 0, 0))
    mid2 = top.lerp(p3, 0.75) + Vector((-0.03, 0, 0))
    A.chain("LedgerChainLinks", [tuple(top), tuple(mid1), tuple(mid2), tuple(p3), tuple(TR + Vector((0, 0, -0.035)))], 0.040, K["iron"])
    zb = TR.z - TRW - LG_BOB - 0.010 - 0.014
    A.cyl("LedgerToggle", 0.014, 0.15, (TR.x, TR.y, zb), K["iron"], rot=(math.radians(90), 0, 0), verts=10, bevel=0.003)
    for s_ in (-1, 1):
        A.sphere(f"LedgerToggleEnd{s_}", 0.019, (TR.x, s_ * 0.078, zb), K["iron"], seg=10, rings=6)
    A.torus("LedgerToggleEye", 0.020, 0.0065, (TR.x, TR.y, zb + 0.016), K["iron"], rot=(0, math.radians(90), 0), major=12, minor=4)
    # ---- the wrist cuff (a second piece: it stays on the wrist)
    piece("LedgerChain", "RightArm")
    _, CG = _wrist_cuff("LedgerCuff", -0.36, -0.50, 0.012, K["iron"])
    for zz in (-0.36, -0.50):
        B4.wire(f"LedgerCuffRoll{zz}", [tuple(Vector((-1.5 - X, Y, zz))) for X, Y in B4.arm_wrap(0.022, x_in=-0.20, a=0.0)], 0.007, K["iron"])
    for k in range(5):
        B4.rivet(f"LedgerCuffRiv{k}", Vector((-2.0 - 0.026, lerp(-0.36, 0.36, k / 4), -0.43)), Vector((-1, 0, 0)), K["iron"], r=0.011, seg=6)
    A.box("LedgerCuffLug", (0.034, 0.05, 0.05), (-2.0 - 0.034, 0.0, -0.43), K["iron"], bevel=0.008)
    A.box("LedgerCuffStalk", (0.016, 0.026, 0.085), (-2.040, 0.0, -0.37), K["iron"], bevel=0.004)
    A.torus("LedgerCuffRing", TRR, TRW, tuple(TR), K["iron"], major=24, minor=6)
    write_extra("ChainedLedger", {"Ledger": {
        "idle": "Ledger", "bob": LG_BOB,
        "bones": {f"Page{k}": {"axis": [0, 1, 0], "min": 0, "max": LG_TURN} for k in range(1, LG_PAGES + 1)},
        "note": "the pages turn over the front of the book (right to left, as the reader sees it) one after another, "
                "then settle back. The chain is part of the Ledger (it bobs with it): its end passes down through the flat ring on "
                "the cuff (LedgerChain) and a toggle bar under it holds it, with room for the bob"}})
    return dict(notes="a heavy black ledger floating open beside the right shoulder (it rides the right arm, outboard "
                      "of it): leather boards with brass corners, a banded gilt-tooled spine, crimson-edged page blocks, "
                      "six loose leaves that turn by themselves (Page1..Page6, idle Ledger), a clasp strap; a short iron "
                      "chain from a staple ring at its foot down through a flat ring on an iron cuff on the right wrist "
                      "(LedgerChain), held by a toggle bar (a toggle-and-ring fastening: it never touches the ring as the "
                      "ledger bobs)")


# ================================================================== 8. the crimson sigil halo
SH_C = Vector((0, 0.95, 1.5))     # on the head's forward axis through the head centre: it spins in its own plane
SH_R = 0.84


@item("SigilHalo", "Crimson sigil halo", lens=40, focus=(0, 0, 1.0), views=["front34", "front", "side", "back", "back34", "close"],
      close=((3.4, 5.8, 2.6), (0, 0.8, 1.55), 70))
def build_sigil_halo(M):
    A.MANNEQUIN_HAIR = dict(SHORT_HAIR)
    K = kmats(M)
    bb, gilt, glow = K["bbrass"], K["gilt"], K["crim"]
    piece("SigilHalo", "Head")
    n0 = len(A.PARTS)
    flat = Matrix.Rotation(math.radians(-90), 4, "X")   # extrude_poly's (x, z) outline -> the local ring plane (x, y), up +Z
    th = 0.026
    Fr = flat @ Matrix.Translation((0, th / 2, 0))
    R1, R0 = SH_R, SH_R - 0.11
    rng = random.Random(30)
    glyphs = []
    nseg = 12
    for k in range(nseg):
        a0 = 2 * math.pi * k / nseg + 0.025
        a1 = 2 * math.pi * (k + 1) / nseg - 0.025
        ns = 10
        outer = [(R1 * math.cos(lerp(a0, a1, i / ns)), R1 * math.sin(lerp(a0, a1, i / ns))) for i in range(ns + 1)]
        inner = [(R0 * math.cos(lerp(a1, a0, i / ns)), R0 * math.sin(lerp(a1, a0, i / ns))) for i in range(ns + 1)]
        A.extrude_poly(f"SHSeg{k}", ccw(outer + inner), th, bb, Fr, bevel=0.0)
        for j in range(4):
            a = lerp(a0 + 0.04, a1 - 0.04, (j + 0.5) / 4)
            glyphs += B5.rune_quads(a, (R0 + R1) / 2, 0.070, 0.074, B5.RUNES[rng.randrange(len(B5.RUNES))], 0.013)
        # a pointed gilt ray outward between the segments, long and short in turn
        a = 2 * math.pi * k / nseg
        L = 0.13 if k % 2 == 0 else 0.075
        A.extrude_poly(f"SHRay{k}", ccw([(-0.020, 0.0), (0.020, 0.0), (0.0, L)]), 0.016, gilt,
                       Matrix.Rotation(a - math.pi / 2, 4, "Z") @ Matrix.Translation((0, R1 - 0.01, 0)) @ flat @ Matrix.Translation((0, 0.008, 0)),
                       bevel=0.003, segments=1)
        A.sphere(f"SHStud{k}", 0.016, (R1 * math.cos(a), R1 * math.sin(a), 0), gilt, scale=(1, 1, 1.3), seg=10, rings=6)
    B5.prisms("SHRunesF", glyphs, th / 2 - 0.001, th / 2 + 0.0045, glow)
    B5.prisms("SHRunesB", glyphs, -th / 2 - 0.0045, -th / 2 + 0.001, glow)
    for k, rr in enumerate((R1 + 0.003, R0 - 0.003)):
        A.torus(f"SHRim{k}", rr, 0.0105, (0, 0, 0), gilt, major=80, minor=4)
    # the inner sigil web (seen round the head and from behind): an eight-pointed star of two squares inscribed in a
    # thin gilt ring, a crimson eye-in-crescent at its heart
    Ri = R0 - 0.08
    A.torus("SHInnerRing", Ri, 0.008, (0, 0, 0), gilt, major=64, minor=4)
    for q in range(2):
        sq = [(Ri * math.cos(q * math.pi / 4 + p * math.pi / 2), Ri * math.sin(q * math.pi / 4 + p * math.pi / 2), 0) for p in range(4)]
        B4.wire(f"SHStar{q}", sq, 0.0075, glow, sides=4, closed=True)
    for q in range(8):   # spokes from the inner ring to the band
        a = math.pi / 8 + q * math.pi / 4
        B4.wire(f"SHSpoke{q}", [(Ri * math.cos(a), Ri * math.sin(a), 0), (R0 * math.cos(a), R0 * math.sin(a), 0)], 0.007, bb, sides=4)
    eye_core = [ccw([(0.11 * math.cos(a), 0.06 * math.sin(a)) for a in (2 * math.pi * i / 24 for i in range(24))])]
    for side, Fs in (("f", Matrix.Translation((0, 0, 0.004)) @ flat), ("b", Matrix.Rotation(math.pi, 4, "Y") @ Matrix.Translation((0, 0, 0.004)) @ flat)):
        A.extrude_poly(f"SHEye{side}", eye_core[0], 0.006, glow, Fs, bevel=0.0, holes=[ccw(A.circle_pts(0, 0, 0.032, 16))[::-1]])
        A.extrude_poly(f"SHMoon{side}", crescent(0, 0, 0.17, 0.0, 0.05, 0.15), 0.008, gilt, Fs, bevel=0.0)
    A.sphere("SHPupil", 0.030, (0, 0, 0), K["black"], scale=(1, 1, 0.5), seg=12, rings=8)
    for q in range(4):   # four gilt stays hold the heart in the web
        a = q * math.pi / 2 + math.pi / 4
        B4.wire(f"SHStay{q}", [(0.16 * math.cos(a), 0.16 * math.sin(a), 0), (Ri * math.cos(a), Ri * math.sin(a), 0)], 0.006, gilt, sides=4)
    # into place: the ring plane faces forward (local +Z -> character -Y), behind the head
    B5.place_parts(n0, Matrix.Translation(SH_C) @ Matrix.Rotation(math.radians(90), 4, "X"))
    write_extra("SigilHalo", {"SigilHalo": {"orbit": {"axis": [0, 0, 1], "rpm": 1.5}, "flare": True,
                                            "light": {"color": [255, 30, 50], "range": 6, "brightness": 0.6,
                                                      "at": to_mesh_space(SH_C, "Head"), "flicker": False}}})
    return dict(notes="a ring of twelve blackened-brass segments carved with raised crimson glowing runes on both faces, "
                      "gilt rims, studs and long and short rays; inside it, round the head, a gilt ring with an eight-pointed "
                      "crimson star and a crimson eye in a gilt crescent at its heart. Floats behind the head and spins "
                      "slowly about the head's forward axis; flares when an admin tool is used", glow=list(CRIM))


# ================================================================== 9. the seal of office
def seal_path():
    """the chain's plan loop (x, y; |y| > 0.5 hangs down that face by the overhang): round the back of the neck
    (0.70 out at the sides, dipping onto the upper back behind the head), over the shoulder tops, then a U down the
    chest to the medallion's bail (z ~0.38)"""
    back = []
    for i in range(47):
        a = lerp(math.radians(-25), math.radians(205), i / 46)
        back.append(Vector((0.80 * math.cos(a), (0.66 if math.sin(a) > 0 else 0.70) * math.sin(a))))
    U = []
    for i in range(16):
        t = i / 15
        U.append(Vector((-0.62 * math.cos(t * math.pi / 2), -0.5 - 0.62 * math.sin(t * math.pi / 2) ** 0.9)))
    U2 = [Vector((-p.x, p.y)) for p in reversed(U[:-1])]
    return back + U + U2 + [back[0]]


@item("SealOfOffice", "Seal of Office", close=((2.4, -5.0, 1.4), (0, -0.4, 0.45), 95))
def build_seal(M):
    A.MANNEQUIN_HAIR = dict(SHORT_HAIR)
    K = kmats(M)
    gilt, brass, en, blk = K["gilt"], K["brass"], K["enamel"], K["black"]
    piece("SealOfOffice", "Torso")
    plan = seal_path()
    LIFT = 0.012
    path3 = [drape_point(p.x, p.y, 1.0, LIFT + 0.004 * smooth(-0.5, -0.62, p.y)) for p in plan]   # a little more off the chest
    path3 = B3.resample(path3, 0.01)
    total = sum((b - a).length for a, b in zip(path3, path3[1:]))
    cum = [0.0]
    for a, b in zip(path3, path3[1:]):
        cum.append(cum[-1] + (b - a).length)

    def at(d):
        for k in range(len(cum) - 1):
            if cum[k + 1] >= d:
                t = (d - cum[k]) / max(1e-9, cum[k + 1] - cum[k])
                p = path3[k].lerp(path3[k + 1], t)
                tg = (path3[k + 1] - path3[k]).normalized()
                return p, tg
        return path3[-1], (path3[-1] - path3[-2]).normalized()
    pitch = 0.15
    n = int(total / pitch)
    pitch = total / n
    plaque = ccw([(x, z) for x, z in A.circle_pts(0, 0, 1.0, 16, sx=1.0)])
    for k in range(n + 1):
        d = k * pitch
        p, tg = at(d)
        nrm = B3.outward(p)
        side = nrm.cross(tg).normalized()
        tg = side.cross(nrm).normalized()
        Fm = B4.basis_frame(p, tg, -nrm, side)     # local x along the chain, local -y out of the body, z across
        if k % 2 == 0:   # a gilt plaque: a rounded square with a raised rim and an enamel boss
            sq = ccw([(0.050 * math.copysign(abs(math.cos(a)) ** 0.5, math.cos(a)), 0.038 * math.copysign(abs(math.sin(a)) ** 0.5, math.sin(a)))
                      for a in (2 * math.pi * i / 16 for i in range(16))])
            A.extrude_poly(f"SealPlaque{k}", sq, 0.016, gilt, Fm @ Matrix.Translation((0, 0.0, 0)), bevel=0.004, segments=1)
            A.sphere(f"SealBoss{k}", 0.019, Fm @ Vector((0, -0.020, 0)), en if (k // 2) % 2 == 0 else blk, scale=(1, 0.55, 1), seg=10, rings=5)
        else:            # a brass S-link between the plaques
            S = [(lerp(-0.045, 0.045, i / 10), 0.0, 0.022 * math.sin(2 * math.pi * i / 10)) for i in range(11)]
            B4.wire(f"SealS{k}", [tuple(Fm @ Vector((x, -0.008, z))) for x, _, z in S], 0.0085, brass, sides=6)
    # the medallion: a gilt disc with a roped rim on a crimson enamel field: the crest in relief
    bottom = min(path3, key=lambda q: q.z)
    mc = Vector((0, -0.5 - LIFT - 0.004 - 0.030, bottom.z - 0.045 - 0.20))
    Fm = Matrix.Translation(mc)
    A.lathe("SealMedal", [(0.0, 0.0), (0.205, 0.0), (0.215, 0.010), (0.212, 0.026), (0.196, 0.032), (0.0, 0.032)], (0, 0, 0), gilt,
            seg=64).matrix_world = Fm @ Matrix.Translation((0, 0.016, 0)) @ Matrix.Rotation(math.radians(90), 4, "X")
    for ph in (0.0, math.pi):
        B4.wire(f"SealMedalRope{ph:.1f}", [tuple(Fm @ Vector((x, -0.018, z)))
                                           for x, _, z in [((0.200 + 0.005 * math.cos(30 * 2 * math.pi * i / 120 + ph)) * math.cos(2 * math.pi * i / 120), 0,
                                                            (0.200 + 0.005 * math.cos(30 * 2 * math.pi * i / 120 + ph)) * math.sin(2 * math.pi * i / 120)) for i in range(120)]],
                0.0055, gilt, sides=4, closed=True)
    A.extrude_poly("SealField", ccw(A.circle_pts(0, 0, 0.185, 48)), 0.006, en, Fm @ Matrix.Translation((0, -0.014, 0)), bevel=0.0)
    crest("SealCrest", Fm @ Matrix.Translation((0, -0.020, 0)), 0.36, gilt, K["brass"], blk, depth=0.010)
    # the bail: a gilt ring from the chain's lowest plaque to the medallion
    A.torus("SealBail", 0.032, 0.0085, (0, mc.y + 0.004, mc.z + 0.225), gilt, rot=(0, math.radians(90), 0), major=16, minor=6)
    A.sphere("SealBailKnot", 0.020, (0, mc.y - 0.002, mc.z + 0.198), gilt, scale=(1.2, 0.8, 1.0), seg=12, rings=8)
    return dict(notes="a heavy chain of office round the shoulders and down the chest: gilt plaques with crimson and black "
                      "enamel bosses alternating with brass S-links, to a large gilt medallion with a roped rim bearing "
                      "the school crest on crimson enamel (crossed gilt keys, a brass crescent moon under a gilt crown, "
                      "a black crow in the crescent's hollow). A torso layer above the sashes' (it lies on the chest top)")


# ================================================================== 10a. the Headmaster's signet ring
@item("HeadSignet", "Headmaster's signet ring", views=["front34", "front", "side", "back", "close"],
      close=((5.4, -3.0, -0.35), (2.0, -0.04, -0.80), 165))
def build_head_signet(M):
    A.MANNEQUIN_HAIR = dict(SHORT_HAIR)
    K = kmats(M)
    gilt, en, bb = K["gilt"], K["enamel"], K["bbrass"]
    piece("HeadSignet", "LeftArm")
    RZ = B3.RING_Z
    tk, hh, off = 0.026, 0.074, 0.005
    o = off + tk / 2
    xo = 2.0 + o
    XE = 1.37
    path = [Vector((XE, -0.5 - o, 0))]
    for k in range(9):
        a = lerp(-math.pi / 2, 0, k / 8)
        path.append(Vector((2.0 + o * math.cos(a), -0.5 + o * math.sin(a), 0)))
    for k in range(9):
        a = lerp(0, math.pi / 2, k / 8)
        path.append(Vector((2.0 + o * math.cos(a), 0.5 + o * math.sin(a), 0)))
    path.append(Vector((XE, 0.5 + o, 0)))
    path = B3.resample(path, 0.03)
    G = [[Vector((p.x, p.y, RZ + dz)) for p in path] for dz in (-hh / 2, -hh / 6, hh / 6, hh / 2)]
    A.surface("HSBand", G, tk, gilt)
    for dz in (-1, 1):
        B3.sweep(f"HSEdge{dz}", [Vector((p.x, p.y, RZ + dz * hh / 2)) for p in path], 0.0055, bb, nr=5)
    for s in (-1, 1):   # the open ends: a gilt cap and a crimson bead
        e = Vector((XE - 0.006, s * (0.5 + o), RZ))
        A.sphere(f"HSCap{s}", 0.026, e, gilt, scale=(1.0, 0.60, 1.0), seg=12, rings=8)
        A.sphere(f"HSBead{s}", 0.016, e + Vector((-0.014, s * 0.012, 0)), en, scale=(1.0, 0.8, 1.0), seg=10, rings=6)
    # the bezel: a gilt oval table on the outer face, a crimson enamel field, the crest in gilt relief, a beaded rim
    F = Matrix.Translation((xo + tk / 2, 0, RZ)) @ Matrix.Rotation(math.radians(90), 4, "Z")
    oval = [(0.132 * math.cos(a), 0.104 * math.sin(a)) for a in (2 * math.pi * k / 40 for k in range(40))]
    A.extrude_poly("HSTable", ccw(oval), 0.022, gilt, F, bevel=0.005, segments=1)
    A.extrude_poly("HSRim", ccw(oval), 0.030, gilt, F, bevel=0.003, segments=1,
                   holes=[ccw([(x * 0.86, z * 0.84) for x, z in oval])[::-1]])
    A.extrude_poly("HSField", ccw([(x * 0.86, z * 0.84) for x, z in oval]), 0.026, en, F, bevel=0.0)
    crest("HSCrest", F @ Matrix.Translation((0, -0.026, 0)), 0.19, gilt, gilt, K["black"], depth=0.008)
    for k in range(20):
        a = 2 * math.pi * k / 20
        A.sphere(f"HSBeadRim{k}", 0.0065, F @ Vector((0.120 * math.cos(a), -0.030, 0.093 * math.sin(a))), gilt, seg=6, rings=4)
    for s in (-1, 1):   # scrolled shoulders where the band meets the table
        y = s * 0.135
        A.sphere(f"HSKnot{s}", 0.017, (xo + tk / 2 + 0.006, y, RZ), gilt, scale=(0.9, 0.7, 1.25), seg=12, rings=8)
        for dz in (-1, 1):
            P = [(xo + tk / 2 + 0.004, s * (0.135 + 0.03 * t), RZ + dz * (0.020 + 0.012 * math.sin(math.pi * t))) for t in (i / 6 for i in range(7))]
            B3.sweep(f"HSScroll{s}_{dz}", P, lambda t: 0.005 * (1 - 0.5 * t), gilt, nr=6)
    return dict(notes="the Headmaster's gilt signet on the left hand: an oval table with a beaded rim, the school crest "
                      "(crossed keys, a crowned crescent, a black crow) in gilt on crimson enamel, scrolled shoulders, "
                      "blackened-brass edges; an open band round the hand's front, outer face and back, its ends "
                      "finished in crimson beads (the inner third, which swings past the katana, carries no metal)")


# ================================================================== 10b. the raven-headed staff of office
ST_X, ST_Y = -1.5, -0.625
ST_FOOT, ST_TOP = -2.86, 0.98


@item("OfficeStaff", "Raven-headed staff of office", views=["front34", "front", "side_r", "back", "close"],
      close=((-4.6, -4.8, 1.4), (ST_X, ST_Y, 0.95), 90))
def build_staff(M):
    A.MANNEQUIN_HAIR = dict(SHORT_HAIR)
    K = kmats(M)
    gilt, bb = K["gilt"], K["bbrass"]
    ebony = A.mat_flat("StaffEbony", (0.020, 0.015, 0.013), rough=0.22, noise=120, bump=0.025, vary=0.05, wear=0.25, coat=0.45)
    grip = A.mat_leather("StaffGrip", (0.26, 0.035, 0.045), scale=4.0, wear=0.5)
    piece("OfficeStaff", "RightArm")
    x, y = ST_X, ST_Y
    # the shaft: ebony, tapering to the foot, gilt collars, a gilt spiral wire round the upper third
    A.lathe("StaffShaft", [(0.0, ST_FOOT + 0.18), (0.030, ST_FOOT + 0.18), (0.036, -1.2), (0.038, 0.70), (0.0, 0.70)],
            (x, y, 0), ebony, seg=16)
    hel = [(x + 0.040 * math.cos(2 * math.pi * i / 14), y + 0.040 * math.sin(2 * math.pi * i / 14), lerp(-0.62, 0.66, i / 140))
           for i in range(141)]
    B4.wire("StaffSpiral", hel, 0.0042, gilt, sides=4)
    for k, (z, r, h) in enumerate(((0.70, 0.050, 0.05), (-0.62, 0.046, 0.03), (-1.08, 0.046, 0.03), (-2.40, 0.042, 0.035))):
        A.lathe(f"StaffCollar{k}", [(0.0, -h / 2), (r - 0.006, -h / 2), (r, -h / 4), (r - 0.004, 0.0), (r, h / 4), (r - 0.006, h / 2),
                                    (0.0, h / 2)], (x, y, z), gilt, seg=20)
    # the grip: crimson leather wound in ridges where the hand holds it
    prof = [(0.0, -1.06)] + [(0.044 + 0.004 * (i % 2), lerp(-1.06, -0.64, i / 16)) for i in range(17)] + [(0.0, -0.64)]
    A.lathe("StaffGrip", prof, (x, y, 0), grip, seg=16)
    # the iron ferrule at the foot
    A.lathe("StaffFerrule", [(0.0, ST_FOOT), (0.016, ST_FOOT), (0.030, ST_FOOT + 0.10), (0.034, ST_FOOT + 0.19), (0.0, ST_FOOT + 0.19)],
            (x, y, 0), K["iron"], seg=14)
    # the raven head: cast in blackened brass, a gilt beak, crimson glowing eyes, a ruff of feathers at the neck
    hc = Vector((x, y + 0.010, 0.86))
    A.lathe("StaffNeck", [(0.0, 0.70), (0.040, 0.70), (0.046, 0.76), (0.052, 0.80), (0.0, 0.80)], (x, y, 0), bb, seg=18)
    hd = A.sphere("RavenHead", 1.0, hc, bb, scale=(0.058, 0.074, 0.062), seg=22, rings=12)
    for v in hd.data.vertices:
        co = hd.matrix_world @ v.co
        if co.z > hc.z + 0.03:
            v.co.z -= (co.z - (hc.z + 0.03)) * 0.4 / 0.062
    hd.data.update()
    secs = []
    for i in range(12):
        t = i / 11
        yy = hc.y - 0.050 - 0.150 * t
        zc = hc.z - 0.004 - 0.026 * t ** 1.7
        bw = 0.024 * (1 - t) ** 0.85 + 0.0015
        hu, hl = 0.026 * (1 - t) ** 0.8 + 0.0015, 0.014 * (1 - t) + 0.001
        ring = []
        for q in range(12):
            a = 2 * math.pi * q / 12
            sa = math.sin(a)
            ring.append(Vector((x + bw * math.cos(a), yy, zc + (hu if sa > 0 else hl) * sa)))
        secs.append(ring)
    B5.loft("RavenBeak", secs, gilt, cap0=Vector((x, hc.y - 0.045, hc.z - 0.004)), cap1=Vector((x, hc.y - 0.203, hc.z - 0.034)))
    for sx in (-1, 1):
        e = Vector((x + sx * 0.047, hc.y - 0.030, hc.z + 0.012))
        A.sphere(f"RavenEyeS{sx}", 0.0125, e, K["crim"], seg=12, rings=8)
        A.torus(f"RavenBrow{sx}", 0.015, 0.004, e + Vector((-sx * 0.002, 0, 0)), gilt, rot=(0, math.radians(90), 0), major=14, minor=4)
    spn = []
    for k in range(14):
        a = 2 * math.pi * k / 14
        o = Vector((math.cos(a), math.sin(a), 0))
        pts = [Vector((x, y, 0)) + o * (0.048 + 0.035 * t) + Vector((0, 0, 0.83 - 0.11 * t)) for t in (q / 4 for q in range(5))]
        nr = [(o + Vector((0, 0, 0.6))).normalized() for _ in pts]
        spn.append((pts, nr, 0.040))
    feathers("StaffRuff", spn, B5.mat_feather("StaffPlume"), th=0.005)
    # a crimson silk tassel on a cord under the collar
    A.tube("StaffCord", [(x - 0.050, y, 0.69), (x - 0.058, y, 0.64), (x - 0.060, y, 0.58)], 0.0045, K["velvet"], res=4)
    A.sphere("StaffTasselHead", 0.016, (x - 0.060, y, 0.572), gilt, scale=(1, 1, 1.2), seg=12, rings=8)
    G = []
    for i in range(21):
        th_ = 2 * math.pi * i / 20
        G.append([Vector((x - 0.060 + (0.010 + 0.012 * t) * math.cos(th_), y + (0.010 + 0.012 * t) * math.sin(th_), lerp(0.560, 0.47, t)))
                  for t in (j / 4 for j in range(5))])
    A.surface("StaffTassel", G, 0.003, K["velvet"], caps=False)
    write_extra("OfficeStaff", {"OfficeStaff": {"pulse": 3.0}})
    return dict(notes="a raven-headed staff of office carried in the right hand like a walking staff (in front of the hand, "
                      "rigid with the arm): an ebony shaft with a gilt spiral wire and gilt collars, a crimson leather grip, "
                      "an iron ferrule 0.14 off the ground; a raven head cast in blackened brass with a gilt beak, crimson "
                      "glowing eyes (pulse) and a ruff of black feathers at the neck, at shoulder height; a crimson tassel",
                glow=list(CRIM))


# ================================================================== 11. the Observer half-mask
def _crackle(seed, n=9):
    """kintsugi crack lines over the mask (x, z): random walks from the edges, branching once or twice"""
    rng = random.Random(seed)
    lines = []
    for k in range(n):
        x = rng.uniform(-0.44, 0.44)
        z = rng.choice((1.47, 1.69)) if abs(x) < 0.3 else rng.uniform(1.50, 1.66)
        ang = math.atan2(1.58 - z, -x * 0.3) + rng.uniform(-0.6, 0.6)
        pts = [(x, z)]
        for s in range(rng.randint(7, 12)):
            ang += rng.uniform(-0.55, 0.55)
            x += 0.022 * math.cos(ang); z += 0.022 * math.sin(ang)
            pts.append((x, z))
            if s == 4 and rng.random() < 0.6:
                a2 = ang + rng.choice((-1, 1)) * rng.uniform(0.6, 1.1)
                bx, bz = x, z
                br = [(bx, bz)]
                for _ in range(rng.randint(3, 6)):
                    a2 += rng.uniform(-0.5, 0.5)
                    bx += 0.02 * math.cos(a2); bz += 0.02 * math.sin(a2)
                    br.append((bx, bz))
                lines.append(br)
        lines.append(pts)
    return lines


def orient_outward(ob, mid_r=None):
    """make a closed shell's faces point outward (recalculated, then flipped if its signed volume is negative): the
    wrapped mask shell came out inside-out, which baked its ambient occlusion and crevice dirt black"""
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.faces.ensure_lookup_table()
    if mid_r is not None:   # a thin shell round the head axis: the outer faces out, the inner faces in, face by face
        flip = []
        for f in bm.faces:
            c = f.calc_center_median()
            rad = Vector((c.x, c.y, 0)).normalized()
            d = f.normal.dot(rad)
            r = math.hypot(c.x, c.y)
            if (r > mid_r and d < -0.2) or (r < mid_r and d > 0.2):
                flip.append(f)
        if flip:
            bmesh.ops.reverse_faces(bm, faces=flip)
        bm.to_mesh(ob.data); bm.free(); ob.data.update()
        return len(flip)
    vol = 0.0
    for f in bm.faces:
        vs = [v.co for v in f.verts]
        for i in range(1, len(vs) - 1):
            vol += vs[0].dot(vs[i].cross(vs[i + 1])) / 6.0
    if vol < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(ob.data); bm.free()
    ob.data.update()
    return vol


def _on_mask(x, z, r=0.636):
    return (r * math.sin(x / 0.64), -r * math.cos(x / 0.64), z)


@item("ObserverMask", "Observer half-mask", close=((2.4, -4.6, 1.95), (0, 0, 1.62), 115))
def build_observer(M):
    A.MANNEQUIN_HAIR = dict(SHORT_HAIR)
    K = kmats(M)
    gilt, porc = K["gilt"], K["porcelain"]
    piece("ObserverMask", "Head")
    pts, eyes = B2.mask_outline("gilt")
    open_eye = eyes[1]          # the character's left eye (+X) is carved open
    ob = A.extrude_poly("ObsShell", ccw(pts), 0.020, porc, frame((0, 0, 0)), bevel=0.004, segments=2, holes=[ccw(open_eye)[::-1]])
    bpy.context.view_layer.objects.active = ob
    for md in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=md.name)
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if e.calc_length() > 0.05], cuts=2, use_grid_fill=True)
    bm.to_mesh(ob.data); bm.free()
    for v in ob.data.vertices:   # a sculpted brow over each eye and a ridge down the nose (before the wrap)
        xx, zz = v.co.x, v.co.z
        ex = min(abs(xx - 0.205), abs(xx + 0.205))
        v.co.y -= 0.010 * math.exp(-(ex / 0.12) ** 2) * math.exp(-((zz - 1.675) / 0.03) ** 2) * (1 if v.co.y < -0.01 else 0)
    ob.data.update()
    B2.wrap_mask(ob, 0.612)
    orient_outward(ob, mid_r=0.622)
    # the gilt edge round the outline and the open eye
    edge = [_on_mask(x, z, 0.623) for x, z in pts]
    B4.wire("ObsEdge", edge, 0.0075, gilt, sides=6, closed=True)
    B4.wire("ObsEyeRim", [_on_mask(x, z, 0.632) for x, z in open_eye], 0.0075, gilt, sides=6, closed=True)
    # the open eye's rayed surround: short gilt rays round the carved eye
    for k in range(12):
        a = 2 * math.pi * k / 12
        if math.sin(a) < -0.6:
            continue
        p0 = (0.205 + 0.125 * math.cos(a), 1.605 + 0.075 * math.sin(a))
        p1 = (0.205 + (0.150 + 0.018 * (k % 2)) * math.cos(a), 1.605 + (0.092 + 0.012 * (k % 2)) * math.sin(a))
        for r_, run in enumerate(B2.mask_runs([p0, ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2), p1], "gilt", 0.008)):
            B4.wire(f"ObsRay{k}_{r_}", [_on_mask(x, z, 0.634) for x, z in run], 0.0036, gilt, sides=4)
    # the painted-shut eye: a raised closed lid (porcelain) with a gilt lid line, gilt lashes, a gilt tear below
    lid = [(-0.205 + 0.10 * math.cos(a), 1.600 - 0.022 * math.sin(a)) for a in (math.pi * i / 16 for i in range(17))]
    B4.wire("ObsLid", [_on_mask(x, z, 0.636) for x, z in lid], 0.0085, porc, sides=6)
    B4.wire("ObsLidLine", [_on_mask(x, z, 0.643) for x, z in lid], 0.0035, gilt, sides=4)
    for k in range(9):
        a = math.pi * (k + 1) / 10
        x0, z0 = -0.205 + 0.10 * math.cos(a), 1.600 - 0.022 * math.sin(a)
        dx, dz = 0.012 * math.cos(a), -0.028
        B4.wire(f"ObsLash{k}", [_on_mask(x0, z0, 0.641), _on_mask(x0 + dx, z0 + dz, 0.639)], 0.0028, gilt, sides=4)
    tear = ccw([(0.0, 0.018), (0.008, 0.002), (0.009, -0.010), (0.0, -0.017), (-0.009, -0.010), (-0.008, 0.002)])
    tp = Vector(_on_mask(-0.215, 1.525, 0.633))
    A.extrude_poly("ObsTear", tear, 0.006, gilt, Matrix.Translation(tp) @ Matrix.Rotation(-0.215 / 0.64, 4, "Z"), bevel=0.0015, segments=1)
    # kintsugi crackle: thin gilt seams over the porcelain, never across the eyes or past the outline
    for k, ln in enumerate(_crackle(11)):
        for r_, run in enumerate(B2.mask_runs(ln, "gilt", 0.016)):
            B4.wire(f"ObsCrack{k}_{r_}", [_on_mask(x, z, 0.6345) for x, z in run], 0.0032, gilt, sides=4)
    return dict(notes="'Observer': a porcelain half-mask with a sculpted brow, a gilt edge; the left eye carved open in a "
                      "gilt rim with short rays, the right painted shut (a raised lid with a gilt lid line and lashes, a "
                      "gilt tear below it); gilt kintsugi crackle over the porcelain")


# ================================================================== the game-side motion check
MINE = ["CrowMantle", "ThornCrown", "RavenPauldron", "IronKeys", "ShadowTrail", "ChainedLedger", "SigilHalo",
        "SealOfOffice", "HeadSignet", "OfficeStaff", "ObserverMask"]
HEADWEAR = ["Hats", "WitchHat", "HunterHat", "MourningHats", "TatteredHood", "Masks", "ThornCrown", "ObserverMask"]
MASK_PIECES = {"LaceMask", "LaceMaskTrim", "BoneMask", "GiltMask", "ObserverMask"}
ARM_DEGS = list(range(-55, 56, 5))


def _in_body(p):
    if abs(p.x) <= 1.0 and abs(p.y) <= 0.5 and abs(p.z) <= 1.0:
        return True
    r = math.hypot(p.x, p.y)
    return 0.9 <= p.z <= 2.1 and r <= 0.6 - max(0.0, abs(p.z - 1.5) - 0.35)


def motion_check():
    """every moving regalia piece in steps against everything it can meet. Bodies: all 12, the arms and legs at every
    5 degrees of the stride (-55..55; acc_check tests only the ends). Prints MOTION lines.
      IronKeys      the orbit at every 5 degrees x bob -b/0/+b, against the arms at every stride angle, the head, every
                    hair, every other piece (arm pieces moved with their arm at every angle), the capes and every
                    head piece at every hair's fit
      SigilHalo     the spin at every 5 degrees, at each hair's own fit against that hair and the hats at that fit
      MantleCrows   both crows at their idle limits (heads swept, tails, wings, lids)
      Ledger        the bob and the pages turning one after another, the arm at every angle
      OfficeStaff, RavenPauldron, the arm pieces, ShadowTrail   at every arm / leg angle"""
    import acc_check as C
    import itertools
    from mathutils.bvhtree import BVHTree
    root = "E:/NH-Work/acc"
    bpy.ops.wm.read_factory_settings(use_empty=True)
    C.load_slots(); C.load_conflicts()
    bodies = {"standard": C.standard_body()}; bodies.update(C.load_body_meshes())
    head = C.head_mesh()
    tb = lambda vt: BVHTree.FromPolygons(vt[0], vt[1], epsilon=0.0)
    posed_trees = {}   # (bid, deg) -> {part: tree}
    for bid, parts in bodies.items():
        for deg in ARM_DEGS:
            posed = parts if deg == 0 else C.limb_pose(parts, deg)[0]
            posed_trees[(bid, deg)] = {k: tb(v) for k, v in posed.items()}
    head_tree = tb(head)
    hairs = {}
    for h in sorted(A._hair_attach()):
        ob = A.real_hair(h)
        if ob is None:
            continue
        v, t = C.mesh_tris(ob); bpy.data.objects.remove(ob)
        t = [tri for tri in t if not _in_body(sum((v[i] for i in tri), Vector()) / 3)]
        hairs[h] = tb((v, t))

    def load(it, posable=False):
        lay = json.load(open(os.path.join(root, "layout", f"{it}.json")))
        with bpy.data.libraries.load(os.path.join(root, "blend", f"{it}.blend"), link=False) as (src, dst):
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

    def arm_move(verts, mount, deg):
        if mount == "LeftArm":
            a = deg
        elif mount == "RightArm":
            a = -deg
        else:
            return verts
        R = Matrix.Rotation(math.radians(a), 3, "X"); piv = Vector((0, 0, 0.5))
        return [R @ (p - piv) + piv for p in verts]
    items = sorted(f[:-6] for f in os.listdir(os.path.join(root, "blend")) if f.endswith(".blend"))
    others = {}        # (item, piece) -> (mount, verts, tris, hair fits)
    for it in items:
        for n, P in load(it).items():
            others[(it, n)] = (P["lay"]["mount"], P["verts"][0], P["verts"][1], P["lay"].get("hair_fit") or {})
    for key in ("WardenMantle", "ReaperShroud", "DuelistCape", "CaptainGreatcape", "MidnightCollar"):
        with bpy.data.libraries.load(f"E:/NH-Work/capes/{key}.blend", link=False) as (src, dst):
            dst.objects = [n for n in src.objects if n == "CapeBody"]
        ob = dst.objects[0]; bpy.context.scene.collection.objects.link(ob)
        for md in list(ob.modifiers):
            ob.modifiers.remove(md)
        ob.parent = None
        v, t = C.mesh_tris(ob)
        others[("Cape" + key, "CapeBody")] = ("Torso", v, t, {})
        C.SLOT_OF[("Cape" + key, "CapeBody")] = "Cape"
        bpy.data.objects.remove(ob)
    SEATP = Vector((0, 0, 1.93))

    def fitted(verts, f, pn):
        if not f:
            return verts
        k, dz = f
        if pn in MASK_PIECES:
            return [Vector((p.x * k, p.y * k, p.z)) for p in verts]
        return [SEATP + (p - SEATP) * k + Vector((0, 0, dz)) for p in verts]
    # trees of the other pieces: rest; arm pieces at every angle; head pieces at every hair's fit
    o_rest, o_arm, o_fit = {}, {}, {}
    for key, (mount, v, t, fits) in others.items():
        o_rest[key] = tb((v, t))
        if mount.endswith("Arm"):
            o_arm[key] = {deg: tb((arm_move(v, mount, deg), t)) for deg in ARM_DEGS}
        if mount == "Head" and key[0] in HEADWEAR:
            o_fit[key] = {h: tb((fitted(v, f, key[1]), t)) for h, f in fits.items() if f}
    print("MOTION loaded", len(hairs), "hairs,", len(others), "pieces and capes,", len(o_fit), "head pieces with hair fits")

    def can_meet(mine, key):
        return key[0] != mine[0] and not C.exclusive(mine, key) and C.slot_of(*mine) != C.slot_of(*key)

    def against(vt, mine, degs=(0,), hair=True, pieces=True, hats=True, own_mount=None, hair_fit=None):
        """{label: set(of where)} of everything this shape meets"""
        T = tb(vt)
        hits = {}
        for (bid, deg), trees in posed_trees.items():
            if deg not in degs:
                continue
            for k, t in trees.items():
                if k == own_mount:
                    continue
                if T.overlap(t):
                    hits.setdefault(f"body {k}", set()).add(f"{bid}@{deg:+d}")
        if own_mount != "Head" and T.overlap(head_tree):
            hits.setdefault("body Head", set()).add("head")
        if hair:
            for h, t in hairs.items():
                if T.overlap(t):
                    hits.setdefault("hair", set()).add(h)
        if pieces:
            for key, t in o_rest.items():
                if not can_meet(mine, key):
                    continue
                if key in o_arm:
                    hit = [d for d in degs if d in o_arm[key] and T.overlap(o_arm[key][d])]
                    if hit:
                        hits.setdefault(f"piece {key[0]}/{key[1]}", set()).update(f"{d:+d}" for d in hit)
                elif key not in o_fit and not (key[0].startswith("Cape") and 0 not in degs) and T.overlap(t):
                    # (the capes are measured at rest: a swinging arm passes through a cape's drape whatever it carries)
                    hits.setdefault(f"piece {key[0]}/{key[1]}", set()).add("rest")
        if hats:
            for key, fits in o_fit.items():
                if not can_meet(mine, key):
                    continue
                hs = [h for h, t in fits.items() if (hair_fit is None or h == hair_fit) and T.overlap(t)]
                if hs:
                    hits.setdefault(f"hat {key[0]}/{key[1]} at hair fits", set()).update(hs)
        return hits

    hair_bad = {}

    def report(label, n, agg, key=None):
        if key is not None:
            hair_bad.setdefault(key, set()).update(agg.get("hair", set()) | agg.get("its hair at the fit", set()))
        print(f"MOTION {label}: {n} poses")
        if not agg:
            print(f"MOTION {label}: clear of every body, hair, piece, cape and hat in every pose")
        for h, x in sorted(agg.items()):
            print(f"MOTION {label} meets {h}: {len(x)} ({', '.join(sorted(x)[:8])}{'...' if len(x) > 8 else ''})")

    def merge(agg, hits):
        for h, x in hits.items():
            agg.setdefault(h, set()).update(x)

    def pose_arm(arm, vals):
        for pb in arm.pose.bones:
            pb.rotation_mode = "AXIS_ANGLE"
            pb.rotation_axis_angle = (math.radians(vals.get(pb.name, 0.0)), 0, 1, 0)
        bpy.context.view_layer.update()
    mine = [it for it in MINE if os.path.exists(os.path.join(root, "blend", f"{it}.blend"))]
    # ---- the keys' orbit
    if "IronKeys" in mine:
        spec = json.load(open(os.path.join(root, "layout", "IronKeys.extra.json")))["IronKeys"]
        P = load("IronKeys")["IronKeys"]
        v0, t0 = P["verts"]
        bob = spec.get("bob", 0.0)
        agg, n = {}, 0
        for deg in range(0, 360, 5):
            R = Matrix.Rotation(math.radians(deg), 3, "Z")
            for b in (-bob, 0.0, bob):
                vv = [R @ p + Vector((0, 0, b)) for p in v0]
                merge(agg, against((vv, t0), ("IronKeys", "IronKeys"), degs=ARM_DEGS, hats=(deg % 15 == 0)))
                n += 1
        zs = [p.z for p in v0]
        rs = [math.hypot(p.x, p.y) for p in v0]
        print(f"MOTION orbit IronKeys: z {min(zs):.3f}..{max(zs):.3f}, radius {min(rs):.3f}..{max(rs):.3f}, bob {bob}")
        report("orbit IronKeys (72 angles x 3 bob, arms and legs at every 5 deg of the stride, 12 bodies)", n, agg, ("IronKeys", "IronKeys"))
    # ---- the sigil halo's spin, at each hair's own fit
    if "SigilHalo" in mine:
        P = load("SigilHalo")["SigilHalo"]
        v0, t0 = P["verts"]
        fits = P["lay"].get("hair_fit") or {}
        agg, agg_h, n = {}, {}, 0
        for deg in range(0, 360, 5):
            R = Matrix.Rotation(math.radians(deg), 3, "Y")
            vr = [R @ (p - HEAD_C) + HEAD_C for p in v0]
            merge(agg, against((vr, t0), ("SigilHalo", "SigilHalo"), degs=(0, 55, -55), hair=not fits, hats=False,
                               own_mount="Head"))
            n += 1
            for h, f in fits.items():
                if not f:
                    continue
                vv = fitted(vr, f, "SigilHalo")
                T = tb((vv, t0))
                if T.overlap(hairs[h]):
                    agg_h.setdefault("its hair at the fit", set()).add(h)
                for key, fl in o_fit.items():
                    if h in fl and can_meet(("SigilHalo", "SigilHalo"), key) and T.overlap(fl[h]):
                        agg_h.setdefault(f"hat {key[0]}/{key[1]} at the same hair's fit", set()).add(h)
        merge(agg, agg_h)
        report(f"orbit SigilHalo (72 angles; {sum(1 for f in fits.values() if f)} hair fits)", n, agg, ("SigilHalo", "SigilHalo"))
        if "--writehair" in sys.argv:   # a fit for each such hair that clears the spin at every angle (or none)
            cands = sorted(((round(min(1.0 + 0.02 * i + 0.02, 1.42), 3), round(0.02 * j, 3)) for i in range(21) for j in range(16)),
                           key=lambda c: (c[0] - 1) + 1.5 * c[1])
            new = dict(fits)
            crown_fit = o_fit.get(("ThornCrown", "ThornCrown"), {})
            redo = agg_h.get("its hair at the fit", set()) | agg_h.get("hat ThornCrown/ThornCrown at the same hair's fit", set())
            for h in sorted(redo):
                f0 = fits.get(h)
                if not f0:
                    continue
                found = None
                for c in cands:
                    if c[0] < f0[0] or c[1] < f0[1]:
                        continue
                    ok = True
                    for deg in range(0, 360, 5):
                        R = Matrix.Rotation(math.radians(deg), 3, "Y")
                        vv = fitted([R @ (p - HEAD_C) + HEAD_C for p in v0], c, "SigilHalo")
                        T_ = tb((vv, t0))
                        if T_.overlap(hairs[h]) or (h in crown_fit and T_.overlap(crown_fit[h])):
                            ok = False; break
                    if ok:
                        found = list(c); break
                new[h] = found
                print(f"MOTION hairfit SigilHalo {h}: {f0} -> {found} (clear of the hair, and of the crown at the same hair's fit, at every angle of the spin)")
            hair_bad[("SigilHalo", "SigilHalo")] = set()
            lp = os.path.join(root, "layout", "SigilHalo.json")
            lay = json.load(open(lp)); lay["pieces"]["SigilHalo"]["hair_fit"] = new
            json.dump(lay, open(lp, "w"), indent=1)
    # ---- the two crows at their idle limits
    if "CrowMantle" in mine:
        spec = json.load(open(os.path.join(root, "layout", "CrowMantle.extra.json")))["MantleCrows"]["bones"]
        Ps = load("CrowMantle", posable=True)
        Pc, mantle_v = Ps["MantleCrows"], Ps["CrowMantle"]["verts"]
        mantle_t = tb(mantle_v)
        ob, arm = Pc["ob"], Pc["arm"]
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode="POSE")
        lim = {k: (v["min"], v["max"]) for k, v in spec.items()}
        agg, self_hit, n = {}, set(), 0
        for i in range(9):
            for tl, wg, ld in itertools.product((0, 1), (0, 1), (0, 1)):
                vals = {}
                for L in "AB":
                    vals["Head" + L] = lerp(lim["Head" + L][0], lim["Head" + L][1], i / 8)
                    vals["Tail" + L] = lim["Tail" + L][tl]
                    for w in ("WingL", "WingR"):
                        vals[w + L] = lim[w + L][wg]
                    for d in ("LidL", "LidR"):
                        vals[d + L] = lim[d + L][ld]
                pose_arm(arm, vals)
                vt = C.mesh_tris(ob)
                merge(agg, against(vt, ("CrowMantle", "MantleCrows"), degs=ARM_DEGS))
                if tb(vt).overlap(mantle_t):
                    self_hit.add(f"pose {i}/{tl}{wg}{ld}")
                n += 1
        pose_arm(arm, {})
        bpy.ops.object.mode_set(mode="OBJECT")
        for P_ in Ps.values():
            for o_ in (P_["ob"], P_["arm"]):
                if o_ is not None:
                    bpy.data.objects.remove(o_)
        report("idle MantleCrows (heads swept in 9 steps x tails x wings x lids, every stride angle)", n, agg, ("CrowMantle", "MantleCrows"))
        print(f"MOTION idle MantleCrows vs its own mantle: {len(self_hit)} poses touch the feathers {sorted(self_hit)[:6]}")
    # ---- the ledger: the bob and the pages, on the swinging arm
    if "ChainedLedger" in mine:
        spec = json.load(open(os.path.join(root, "layout", "ChainedLedger.extra.json")))["Ledger"]
        Ps = load("ChainedLedger", posable=True)
        PL = Ps["Ledger"]
        ob, arm = PL["ob"], PL["arm"]
        bob = spec.get("bob", 0.0)
        pages = sorted(spec["bones"])
        turn = spec["bones"][pages[0]]["max"]
        chain_t = tb(Ps["LedgerChain"]["verts"])
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode="POSE")
        poses = [{}]
        for k, pg in enumerate(pages):
            for a in [turn * q / 6 for q in range(1, 7)]:
                vals = {p2: turn for p2 in pages[:k]}
                vals[pg] = a
                poses.append(vals)
        agg, n, chain_hit = {}, 0, set()
        for vals in poses:
            pose_arm(arm, vals)
            v, t = C.mesh_tris(ob)
            for b in (-bob, 0.0, bob):
                vb = [p + Vector((0, 0, b)) for p in v]
                for deg in ARM_DEGS[::2]:
                    vm = arm_move(vb, "RightArm", deg)
                    merge(agg, against((vm, t), ("ChainedLedger", "Ledger"), degs=(deg,), own_mount="RightArm", hats=False,
                                       hair=(deg == 0)))
                    n += 1
                if tb((vb, t)).overlap(chain_t):
                    chain_hit.add(f"{len(vals)} turned, bob {b:+.3f}")
        pose_arm(arm, {})
        bpy.ops.object.mode_set(mode="OBJECT")
        for P_ in Ps.values():
            for o_ in (P_["ob"], P_["arm"]):
                if o_ is not None:
                    bpy.data.objects.remove(o_)
        report("idle Ledger (pages turning one after another x bob x the arm swinging)", n, agg, ("ChainedLedger", "Ledger"))
        print(f"MOTION idle Ledger (with its chain) vs the cuff and its ring: {len(chain_hit)} poses meet {sorted(chain_hit)[:4]}")
    # ---- rigid arm pieces and the trail anchor at every stride angle
    for it, pn in (("OfficeStaff", "OfficeStaff"), ("RavenPauldron", "RavenPauldron"), ("HeadSignet", "HeadSignet"),
                   ("ChainedLedger", "LedgerChain"), ("ShadowTrail", "ShadowTrail")):
        if it not in mine:
            continue
        P = load(it)[pn]
        v0, t0 = P["verts"]
        mount = P["lay"]["mount"]
        agg, n = {}, 0
        for deg in ARM_DEGS:
            vm = arm_move(v0, mount, deg)
            merge(agg, against((vm, t0), (it, pn), degs=(deg,), own_mount=mount, hats=True))
            n += 1
        report(f"stride {it}/{pn} (arms and legs at every 5 deg, 12 bodies, hats at every hair fit)", n, agg, (it, pn))
    # the hairs a moving piece meets in any pose can't wear it: their fit becomes null (the Wardrobe and the server
    # refuse that hair with that piece). Static pieces keep acc_hairfit's answer.
    for (it, pn), bad in sorted(hair_bad.items()):
        lp = os.path.join(root, "layout", f"{it}.json")
        lay = json.load(open(lp))
        fits = lay["pieces"][pn].get("hair_fit") or {}
        newly = sorted(h for h in bad if fits.get(h))
        ok = sum(1 for h, f in fits.items() if f and h not in bad)
        print(f"MOTION hair {it}/{pn}: {ok}/{len(fits)} hairs clear in every pose; newly refused in motion: {newly or '-'}")
        if "--writehair" in sys.argv and newly:
            for h in newly:
                fits[h] = None
            lay["pieces"][pn]["hair_fit"] = fits
            json.dump(lay, open(lp, "w"), indent=1)
    print("MOTION done")


if __name__ == "__main__" and "--motioncheck" in sys.argv:
    motion_check()


# ================================================================== hair fits (the mask as a mask)
def hairfit():
    """acc_hairfit for the batch; then the mask is refitted the way the game wears every head piece
    (UI.AccessoryWear: a uniform scale k about the headband centre, then a lift) and acc_check tests it: k 1.00..1.12,
    no lift (the eye hole stays on the eye). acc_hairfit's mask branch scales masks radially about the head's axis,
    which isn't what the game does (2 hairs crossed this mask at its radial fit when worn the game's way)."""
    import acc_hairfit as H
    H.main()
    if H.ONLY and "ObserverMask" not in H.ONLY:
        return
    import acc_check as C
    from mathutils.bvhtree import BVHTree
    bpy.ops.wm.read_factory_settings(use_empty=True)
    lp = os.path.join(H.ROOT, "layout", "ObserverMask.json")
    lay = json.load(open(lp))
    with bpy.data.libraries.load(os.path.join(H.ROOT, "blend", "ObserverMask.blend"), link=False) as (src, dst):
        dst.objects = ["ObserverMask"]
    ob = dst.objects[0]; bpy.context.scene.collection.objects.link(ob)
    for md in list(ob.modifiers):
        ob.modifiers.remove(md)
    ob.parent = None
    v0, t0 = C.mesh_tris(ob)
    piv = Vector((0, 0, H.SEAT))
    fits = {}
    for h in sorted(A._hair_attach()):
        hb = A.real_hair(h)
        if hb is None:
            continue
        v, t = C.mesh_tris(hb); bpy.data.objects.remove(hb)
        free = [not _in_body(sum((v[i] for i in tri), Vector()) / 3) for tri in t]
        HT = BVHTree.FromPolygons(v, t, epsilon=0.0)
        found = None
        for i in range(13):
            k = 1.0 + 0.01 * i
            kk = round(min(k + 0.02, 1.14), 3)
            vv = [piv + (p - piv) * kk for p in v0]   # tested at the stored (worn) value, margin included
            ov = BVHTree.FromPolygons(vv, t0, epsilon=0.0).overlap(HT)
            if not any(free[j] for _, j in ov):
                found = [kk, 0.0]
                break
        fits[h] = found
    lay["pieces"]["ObserverMask"]["hair_fit"] = fits
    json.dump(lay, open(lp, "w"), indent=1)
    ok = [f for f in fits.values() if f]
    print(f"HAIRFIT ObserverMask/ObserverMask (uniform, as worn): {len(ok)}/{len(fits)} hairs fit; k up to "
          f"{max((f[0] for f in ok), default=0):.2f}; no fit: {', '.join(h for h, f in fits.items() if not f) or '-'}")


if __name__ == "__main__" and "--hairfit" in sys.argv:
    hairfit()
