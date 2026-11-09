"""Props batch 39, the dorm house kit, for nh_props.py: the dorm building beyond the private room (batch 34's kit), and personal
things for the girls' and boys' rooms. Batch 34's look: cast iron, black marble, crimson enamel, brass and gilt, ebonised wood.

Shared building  BunkBed (two cast-iron tiers; mattress tops 1.84 and 5.5; Bedding is its own piece), Nightstand, FloorMirror
                 (Mirror: the glass), LaundryHamper, WashingMachine (Glass: the porthole), ShowerStall, MiniFridge, BeanBag,
                 PingPongTable, RADesk (the resident adviser's lobby desk: sign-in book, key board, bell)
Girls' rooms     VanityTable (Mirror: the glass; Glow: the bulbs round it), MakeupSet, JewelryBox, PerfumeTray (Glass: the bottles),
                 ShoeRack, FairyLights (Glow: the bulbs)
Boys' rooms      WeightBench, Dumbbells, GuitarStand, TVConsole, SneakerPile, DoorHoop
Boys' bathroom   Urinal, UrinalDivider, UrinalTrough (batch 5's porcelain, marble and brass)

Front faces -Y, Z is up, the origin is at the bottom centre (wall pieces: on the wall plane, y = 0). Prints from kits3739_atlas.py
(DormHousePrint). Registered into nh_props.BUILD on import.
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, material, _finish, _gable
from nh_props_batch3 import sphere, cone
from nh_props_batch4 import lathe, hoop, strip, _mark, _xform, _dims, flat, _solid
from nh_props_batch5 import marble
from nh_props_batch9 import foil
from nh_props_batch24 import _text, _fine, rbox
import nh_props_batch20 as B20
import nh_props_batch24 as B24
import nh_props_batch29 as B29
import nh_props_batch30 as B30
import nh_props_batch34_dorm as B34
import nh_props_batch37 as B37
import window_shapes as WS

DEG = math.pi / 180
RX, RY, RZ, T = B30.RX, B30.RY, B30.RZ, B30.T
FONT = B37.FONT
kit = B37.kit


def porcelain():
    return flat("Porcelain", (0.82, 0.8, 0.74), 0.08, wear=0.02, dirt=0.6)


def silvered():
    return flat("Silvered", (0.72, 0.74, 0.77), 0.04, metal=1.0, dirt=0.3)


def plain(name, rgb, rough=0.5, metal=0.0):
    return flat(name, rgb, rough, metal=metal)


def ebony_case(prefix, w, d, h, z0, K, bevel=0.02):
    box(prefix, (w, d, h), (0, 0, z0 + h / 2), K["ebony"], bevel=bevel)


# ================================================================== shared building

def bunk_bed(M):
    """Two cast-iron tiers (4 x 8, posts to 7.4), a ladder on the right side, a guard rail round the top; mattress tops 1.84 and 5.5.
    The mattresses, blankets and pillows are the Bedding piece."""
    K = kit(M)
    ir, br = K["iron"], K["brass"]
    W, L = 4.0, 8.0
    hx, hy = W / 2 - 0.1, L / 2 - 0.1
    top = 7.4
    tiers = (1.0, 4.66)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * hx, sy * hy
            cyl(f"Post{sx}{sy}", 0.08, top, (x, y, top / 2), ir, verts=14, bevel=0.01)
            cyl(f"Foot{sx}{sy}", 0.11, 0.1, (x, y, 0.05), ir, verts=14, bevel=0.02)
            for z in (tiers[0] + 0.12, tiers[1] + 0.12, top - 0.6):
                cyl(f"Collar{sx}{sy}{z:.1f}", 0.1, 0.08, (x, y, z), br, verts=14, bevel=0.015)
            sphere(f"Knob{sx}{sy}", 0.14, (x, y, top + 0.12), br, seg=14, rings=7)
    for sy in (-1, 1):
        y = sy * hy
        for k, (zl, zh) in enumerate(((0.5, 3.0), (tiers[1] - 0.3, top - 0.25))):
            tube(f"EndTop{sy}{k}", [(x, y, z) for x, z in B34.seg_arc(hx, zh - 0.4, 0.4, 14)], 0.04, ir, poly=True)
            tube(f"EndLow{sy}{k}", [(-hx, y, zl), (hx, y, zl)], 0.035, ir, poly=True)
            for i in range(7):
                x = -hx + (i + 1) * 2 * hx / 8
                if abs(x) < 0.4:
                    continue
                zt = zh - 0.4 + 0.4 * math.cos(x / hx * math.pi / 2) ** 0.5
                tube(f"Spin{sy}{k}{i}", [(x, y, zl), (x, y, zt - 0.02)], 0.02, ir, poly=True)
            zc = (zl + zh) / 2
            hoop(f"Roundel{sy}{k}", (0, y, zc), 0.36, "Y", ir, thick=0.03)
            foil(f"Foil{sy}{k}", 0, y, zc, 0.3, br, lobes=4, thick=0.02)
    for k, z in enumerate(tiers):
        for sx in (-1, 1):
            box(f"SideRail{k}{sx}", (0.07, 2 * hy, 0.24), (sx * hx, 0, z), ir, bevel=0.015)
        for i in range(6):
            box(f"Slat{k}{i}", (2 * hx - 0.1, 0.18, 0.04), (0, -hy + (i + 0.5) * 2 * hy / 6, z + 0.1), ir, bevel=0.008)
    # the upper guard rail on the left and the ladder on the right
    for z in (tiers[1] + 0.9, tiers[1] + 1.5):
        tube(f"Guard{z:.1f}", [(-hx, -hy, z), (-hx, hy, z)], 0.035, ir, poly=True)
        tube(f"GuardR{z:.1f}", [(hx, 0.6, z), (hx, hy, z)], 0.035, ir, poly=True)
    for i in range(9):
        y = -hy + 0.3 + i * (2 * hy - 0.6) / 8
        tube(f"GuardBar{i}", [(-hx, y, tiers[1] + 0.12), (-hx, y, tiers[1] + 1.5)], 0.018, ir, poly=True)
    lx = hx + 0.3
    for y in (-1.0, 0.4):
        tube(f"LadderSide{y}", [(lx, y, 0.0), (lx, y, tiers[1] + 1.5)], 0.04, ir, poly=True)
        tube(f"LadderHook{y}", [(lx, y, tiers[1] + 1.5), (hx, y, tiers[1] + 1.55)], 0.035, ir, poly=True)
    for i in range(1, 7):
        z = i * (tiers[1] + 0.2) / 6
        tube(f"Rung{i}", [(lx, -1.0, z), (lx, 0.4, z)], 0.032, br, poly=True)
    # the bedding
    set_group("Bedding")
    blank = B34.uv_fabric("BunkBlanket", "NH_Damask", (0.15, 0.01, 0.018), 0.95, band=(0.55, 0.47, 0.34))
    blank2 = B34.uv_fabric("BunkBlanket2", "NH_Stripe", (0.6, 0.55, 0.48), 0.8, band=(0.15, 0.01, 0.018))
    out = []
    for k, (z, bm_) in enumerate(((tiers[0] + 0.48, blank), (tiers[1] + 0.48, blank2))):
        mat_top = z + 0.36
        m = B29.cushion(f"Mattress{k}", (W - 0.32, L - 0.36, 0.72), (0, 0, z), K["linen"], e=(0.25, 0.12), cuts=5, piping=K["linen"], pipe_r=0.03)
        B29.cushion(f"Pillow{k}", (2.6, 1.1, 0.42), (0, L / 2 - 0.95, mat_top + 0.18), K["linen"], e=(0.55, 0.35), cuts=5, puff=0.25)
        cols = B34.collider_copies([m])
        bw, bl = 4.6, 5.8
        bk = B34.grid_cloth(f"Blanket{k}", [(-bw / 2, -bl / 2), (bw / 2, -bl / 2), (bw / 2, bl / 2), (-bw / 2, bl / 2)], 0.16, bm_,
                            T(0, -L / 2 + 0.25 + bl / 2, mat_top + 0.25), band=B34.blanket_band(bl, bw))
        B34.simulate([bk], cols + [B34.floor_collider(z=mat_top - 1.2)], frames=55, mass=0.4, stiff=6.0, bend=0.2, friction=10.0)
        B34.finish_cloth([bk], 0.03)
    set_group("Main")
    return _dims()


def nightstand(M):
    """An ebonised nightstand (1.7 wide, black marble top 2.3): a drawer and a door with crimson enamel insets, brass pulls; a brass
    alarm clock and a book on top."""
    K = kit(M)
    W, D, H = 1.7, 1.4, 2.2
    box("Body", (W, D, H - 0.3), (0, 0, 0.3 + (H - 0.3) / 2), K["ebony"], bevel=0.02)
    for sx in (-1, 1):
        for sy in (-1, 1):
            lathe(f"Leg{sx}{sy}", [(0, 0), (0.07, 0), (0.09, 0.1), (0.06, 0.2), (0.08, 0.3), (0, 0.3)], K["iron"], seg=12, loc=(sx * (W / 2 - 0.12), sy * (D / 2 - 0.12), 0))
    box("Top", (W + 0.1, D + 0.1, 0.1), (0, 0, H + 0.05), K["marble"], bevel=0.02)
    yf = -D / 2
    box("Drawer", (W - 0.2, 0.05, 0.4), (0, yf - 0.02, H - 0.3), K["ebony"], bevel=0.015)
    box("DrawerInset", (W - 0.5, 0.012, 0.2), (0, yf - 0.045, H - 0.3), K["enamel"], bevel=0.0)
    box("Door", (W - 0.2, 0.05, 1.1), (0, yf - 0.02, 0.95), K["ebony"], bevel=0.015)
    pts = WS.arch(0.45, 0.55, 1.05, 1.35, 8)
    B20.tprism("DoorInset", pts, yf - 0.05, 0.012, K["enamel"])
    tube("DoorEdge", [(x, yf - 0.058, z) for x, z in pts] + [(pts[0][0], yf - 0.058, pts[0][1])], 0.018, K["iron"], square=True, poly=True)
    for z in (H - 0.3,):
        tube("Pull", [(-0.2, yf - 0.04, z + 0.05), (-0.16, yf - 0.1, z - 0.02), (0.16, yf - 0.1, z - 0.02), (0.2, yf - 0.04, z + 0.05)], 0.012, K["brassf"])
    sphere("Knob", 0.05, (0.62, yf - 0.08, 0.95), K["brassf"], seg=10, rings=5)
    # an alarm clock with twin bells
    s = _mark()
    cyl("ClockBody", 0.22, 0.12, (0, 0, 0.3), K["brassf"], rot=(math.pi / 2, 0, 0), verts=28, bevel=0.015)
    cyl("ClockFace", 0.19, 0.01, (0, -0.065, 0.3), K["bone"], rot=(math.pi / 2, 0, 0), verts=28, bevel=0.0)
    for a in range(12):
        t = a / 12 * 6.283
        box(f"Tick{a}", (0.01, 0.005, 0.03), (math.sin(t) * 0.16, -0.072, 0.3 + math.cos(t) * 0.16), K["ink"], bevel=0.0, rot=(0, t, 0))
    tube("HandH", [(0, -0.075, 0.3), (0.06, -0.075, 0.35)], 0.008, K["ink"], poly=True)
    tube("HandM", [(0, -0.075, 0.3), (-0.02, -0.075, 0.44)], 0.006, K["ink"], poly=True)
    for sx in (-1, 1):
        lathe(f"Bell{sx}", [(0, 0.1), (0.08, 0.09), (0.1, 0.04), (0.105, 0.0), (0, 0.0)], K["brassf"], seg=18)
        P.PARTS[-1].matrix_world = T(sx * 0.14, 0, 0.5) @ RY(sx * 30 * DEG)
        tube(f"ClockLeg{sx}", [(sx * 0.1, 0, 0.12), (sx * 0.16, 0, 0.0)], 0.015, K["brassf"], poly=True)
    tube("Hammer", [(0, 0, 0.52), (0, 0, 0.62)], 0.01, K["brassf"], poly=True)
    _xform(s, T(-0.35, 0.1, H + 0.1) @ RZ(15 * DEG))
    book = material("NightBook", "NH_Leather", tint=(0.05, 0.08, 0.06), scale=3.0, normal=0.4, wear=0.4)
    box("Book", (0.6, 0.85, 0.12), (0.35, 0.05, H + 0.16), book, bevel=0.015, rot=(0, 0, -0.2))
    box("BookPages", (0.56, 0.8, 0.1), (0.37, 0.05, H + 0.16), B24.pages("NightPages", (0.8, 0.76, 0.66)), bevel=0.004, rot=(0, 0, -0.2))
    _fine(0.6)
    return _dims()


def floor_mirror(M):
    """A cheval mirror (6.7 tall): a pointed-arch glass (the Mirror piece) swung on brass pivots between cast-iron uprights on splayed
    feet."""
    K = kit(M)
    ir = K["iron"]
    hw, z0, zs, za = 0.95, 1.0, 5.1, 6.1
    for sx in (-1, 1):
        x = sx * (hw + 0.35)
        tube(f"Upright{sx}", [(x, 0, 0.15), (x, 0, 3.6)], 0.06, ir, square=True, poly=True)
        tube(f"Foot{sx}", [(x, -0.9, 0.06), (x, 0, 0.18), (x, 0.9, 0.06)], 0.06, ir, square=True)
        for sy in (-1, 1):
            sphere(f"Toe{sx}{sy}", 0.07, (x, sy * 0.9, 0.06), K["brass"], seg=8, rings=4)
        sphere(f"Finial{sx}", 0.09, (x, 0, 3.7), K["brass"], seg=10, rings=5)
        cyl(f"Pivot{sx}", 0.09, 0.3, (sx * (hw + 0.2), 0, 3.3), K["brassf"], rot=(0, math.pi / 2, 0), verts=14, bevel=0.01)
        tube(f"Scroll{sx}", [(x, 0, 0.6), (sx * (hw + 0.1), 0, 0.9), (sx * (hw - 0.1), 0, 0.7)], 0.025, ir)
    tube("Stretcher", [(-(hw + 0.35), 0, 0.5), (hw + 0.35, 0, 0.5)], 0.04, ir, poly=True)
    tilt = -5 * DEG
    s = _mark()
    from nh_props import _arch_loop
    B20.tprism("Back", [(x, z) for x, _, z in _arch_loop(0, 0, hw + 0.12, z0 - 0.12, zs, za + 0.14)], 0.06, 0.06, K["ebony"])
    tube("Frame", _arch_loop(0, -0.0, hw + 0.06, z0 - 0.04, zs, za + 0.06), 0.07, ir, square=True, closed=True, poly=True)
    tube("Bead", _arch_loop(0, -0.07, hw, z0, zs, za), 0.022, K["brass"], closed=True, poly=True)
    sphere("TopFinial", 0.07, (0, 0.0, za + 0.22), K["brass"], seg=10, rings=5)
    set_group("Mirror")
    B20.tprism("Glass", [(x, z) for x, _, z in _arch_loop(0, 0, hw, z0, zs, za)], 0.02, 0.015, silvered())
    set_group("Main")
    _xform(s, T(0, 0, 3.3) @ RX(tilt) @ T(0, 0, -3.3))
    return _dims()


def laundry_hamper(M):
    """A lidded hamper (1.6 across, 2.4 tall): woven wicker on an iron hoop frame, the lid propped on its side, a shirt half out over
    the rim."""
    K = kit(M)
    wick = material("Wicker", "NH_DeskWood", tint=(0.12, 0.07, 0.04), scale=1.5, rough_add=0.15, wear=0.3)
    r0, r1, H = 0.7, 0.8, 2.3
    lathe("Basket", [(0, 0.05), (r0, 0.05), (r0 + 0.01, 0.1), (r1, H), (r1 - 0.05, H), (r0 - 0.05, 0.12), (0, 0.12)], wick, seg=40, flute=(40, 0.04))
    for z in (0.1, 0.9, 1.6, H):
        rr = r0 + (r1 - r0) * z / H + 0.01
        hoop(f"Band{z}", (0, 0, z), rr, "Z", K["iron"], thick=0.025)
    for k in range(4):
        a = k / 4 * 6.283 + 0.4
        tube(f"Rib{k}", [(math.cos(a) * (r0 + 0.02), math.sin(a) * (r0 + 0.02), 0.0), (math.cos(a) * (r1 + 0.02), math.sin(a) * (r1 + 0.02), H)], 0.025, K["iron"],
             poly=True)
        sphere(f"Foot{k}", 0.06, (math.cos(a) * r0, math.sin(a) * r0, 0.04), K["brass"], seg=8, rings=4)
    for sx in (-1, 1):
        hoop(f"Handle{sx}", (sx * (r1 + 0.04), 0, H - 0.3), 0.12, "X", K["brass"], thick=0.02)
    # the lid leaning against the side
    s = _mark()
    lathe("Lid", [(0, 0.12), (0.5, 0.1), (0.82, 0.03), (0.84, 0.0), (0, 0.0)], wick, seg=40, flute=(40, 0.03))
    hoop("LidBand", (0, 0, 0.01), 0.84, "Z", K["iron"], thick=0.025)
    sphere("LidKnob", 0.07, (0, 0, 0.15), K["brass"], seg=10, rings=5)
    _xform(s, T(1.25, 0.2, 0.86) @ RY(-78 * DEG) @ RZ(0.3))
    # the laundry heaped above the rim, a tee dropped on the floor beside it
    lm = material("Laundry", "NH_Leather", tint=(0.4, 0.36, 0.3), scale=3.0, normal=0.6, rough_add=0.3, wear=0.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r1 - 0.04, segments=24, ring_count=12, location=(0, 0, H - 0.08))
    heap = bpy.context.active_object
    heap.name = "Heap"
    heap.scale = (1.0, 1.0, 0.4)
    bpy.ops.object.transform_apply(scale=True)
    g = random.Random(3904)
    for v in heap.data.vertices:
        v.co.z += 0.06 * math.sin(v.co.x * 9 + 1) * math.sin(v.co.y * 7) + g.uniform(-0.015, 0.015)
    _finish(heap, lm, 0)
    sleeve = material("SleeveCloth", "NH_Leather", tint=(0.16, 0.012, 0.02), scale=4.0, normal=0.5, rough_add=0.3, wear=0.0)
    strip("Sleeve", [(0.3, -0.5, H + 0.05), (0.55, -0.72, H - 0.02), (0.62, -0.84, H - 0.4), (0.6, -0.88, H - 0.9)], 0.22, (1, 0, 0), sleeve, thick=0.02)
    sh = B34.garment("Shirt", "Tee", T(1.2, -1.0, 0.35) @ RZ(80 * DEG), K, h=0.09, crumple=0.12, seed=5)
    B34.simulate([sh], [B34.floor_collider()], frames=50, mass=0.3, stiff=8.0, bend=0.4, friction=10.0)
    B34.finish_cloth([sh], 0.02)
    return _dims()


def washing_machine(M):
    """A front-loading washer (2.4 x 2.3 x 3.2) dressed gothic: a crimson enamel cabinet on an iron plinth, an ebonised top, a brass
    porthole (Glass: its window) with clothes in the drum, the RAVENWASH panel with brass dials."""
    K = kit(M)
    W, D, H = 2.4, 2.3, 3.0
    box("Plinth", (W, D - 0.1, 0.25), (0, 0.05, 0.125), K["iron"], bevel=0.02)
    for sx in (-1, 1):
        for sy in (-1, 1):
            lathe(f"Foot{sx}{sy}", [(0, 0), (0.1, 0), (0.08, 0.06), (0, 0.06)], K["iron"], seg=10, loc=(sx * (W / 2 - 0.15), sy * (D / 2 - 0.15), -0.0))
    rbox("Cabinet", W / 2, D / 2, 0.12, 0.25, H, K["enamel"], step=0.05, rows=4)
    box("Top", (W + 0.06, D + 0.04, 0.12), (0, 0, H + 0.06), K["ebony"], bevel=0.03)
    yf = -D / 2
    B30.plate("Panel", "K9_Washer_Panel", W - 0.2, (W - 0.2) * 220 / 900, 0.04, T(0, yf - 0.02, H - 0.35), K["p9"], edge="K9_black", k=2.5)
    for k, (x, r) in enumerate(((0.29 * (W - 0.2) - 0.55 * 0, 0.16), (0.65, 0.12))):
        xx = -((W - 0.2) / 2) + (W - 0.2) * (520 / 900 if k == 0 else 770 / 900)
        cyl(f"Dial{k}", r, 0.08, (xx, yf - 0.08, H - 0.35 + 0.0), K["brassf"], rot=(math.pi / 2, 0, 0), verts=24, bevel=0.015)
        box(f"DialMark{k}", (0.02, 0.01, r * 0.7), (xx, yf - 0.125, H - 0.35 + r * 0.3), K["ink"], bevel=0.0)
    # the porthole
    zc = 1.35
    s = _mark()
    lathe("PortRing", [(0.58, 0.0), (0.72, 0.0), (0.74, 0.05), (0.7, 0.12), (0.6, 0.14), (0.56, 0.1), (0.56, 0.0)], K["brassf"], seg=48)
    lathe("Drum", [(0.56, 0.0), (0.56, -0.5), (0, -0.55)], plain("Drum", (0.06, 0.06, 0.065), 0.3, metal=0.8), seg=32)
    _xform(s, T(0, yf - 0.01, zc) @ RX(math.pi / 2))
    clothes = material("DrumLaundry", "NH_Leather", tint=(0.3, 0.05, 0.06), scale=3.0, normal=0.7, rough_add=0.3, wear=0.0)
    sphere("Laundry", 0.45, (0.05, yf + 0.35, zc - 0.25), clothes, seg=14, rings=7, scale=(1.1, 0.7, 0.6))
    box("Latch", (0.12, 0.08, 0.3), (0.76, yf - 0.06, zc), K["brassf"], bevel=0.02)
    box("Hinge", (0.12, 0.08, 0.4), (-0.76, yf - 0.05, zc), K["brassf"], bevel=0.02)
    foil("Crest", 0, yf - 0.012, H - 0.95, 0.12, K["gilt"], lobes=4, thick=0.012)
    set_group("Glass")
    lathe("Window", [(0, 0.11), (0.3, 0.1), (0.58, 0.06), (0.58, 0.04), (0, 0.06)], K["glass"], seg=40)
    P.PARTS[-1].matrix_world = T(0, yf - 0.01, zc) @ RX(math.pi / 2)
    set_group("Main")
    return _dims()


def shower_stall(M):
    """A tiled shower stall (3.8 x 3.8, walls 7.6): three tiled walls on a marble curb, a checked floor tray, a brass rose and valve
    wheel, a soap shelf, a curtain on rings along a brass rail across the open front."""
    K = kit(M)
    W, D, H = 3.8, 3.8, 7.6
    t = 0.15
    yb = D / 2
    box("Curb", (W + 0.3, D + 0.15, 0.35), (0, 0.075, 0.175), marble("ShowerMarble", base=(0.03, 0.028, 0.034), vein=(0.4, 0.38, 0.33), scale=0.9, width=0.03,
                                                                       distortion=6.0, detail=2.5), bevel=0.03)
    B34.pbox("Floor", (W - 0.1, D - 0.1, 0.02), (0, 0.05, 0.36), K["p9"], {"top": "K9_Tiles_Floor", "else": "sw:K9_grout"}, k=1.5)
    cyl("Drain", 0.15, 0.01, (0, 0.2, 0.375), K["brassf"], verts=20, bevel=0.0)
    for k in range(5):
        box(f"DrainSlot{k}", (0.2, 0.02, 0.005), (0, 0.12 + k * 0.04, 0.381), K["ink"], bevel=0.0)
    tiles = {"else": "sw:K9_grout"}
    B34.pbox("Back", (W + 0.3, t, H), (0, yb, H / 2), K["p9"], dict(tiles, front="K9_Tiles_Wall"), k=2.2)
    for sx in (-1, 1):
        f = dict(tiles)
        f["right" if sx < 0 else "left"] = "K9_Tiles_Wall"
        B34.pbox(f"Side{sx}", (t, D, H), (sx * (W / 2 + 0.075), 0.05, H / 2), K["p9"], f, k=2.2)
        box(f"Cap{sx}", (t + 0.06, D + 0.04, 0.12), (sx * (W / 2 + 0.075), 0.05, H + 0.06), K["marble"], bevel=0.02)
        box(f"Edge{sx}", (t + 0.06, 0.1, H), (sx * (W / 2 + 0.075), -D / 2 + 0.0, H / 2), K["marble"], bevel=0.02)
    box("BackCap", (W + 0.42, t + 0.06, 0.12), (0, yb, H + 0.06), K["marble"], bevel=0.02)
    # the plumbing
    y = yb - t / 2 - 0.05
    tube("Riser", [(0.8, y, 3.0), (0.8, y, 6.3), (0.8, y - 0.5, 6.5)], 0.045, K["brassf"])
    lathe("Rose", [(0, 0.15), (0.06, 0.15), (0.08, 0.08), (0.3, 0.02), (0.32, 0.0), (0, 0.0)], K["brassf"], seg=28)
    P.PARTS[-1].matrix_world = T(0.8, y - 0.6, 6.42) @ RX(-25 * DEG)
    cyl("Valve", 0.1, 0.12, (0.8, y - 0.02, 3.6), K["brassf"], rot=(math.pi / 2, 0, 0), verts=16, bevel=0.01)
    hoop("ValveWheel", (0.8, y - 0.15, 3.6), 0.2, "Y", K["brassf"], thick=0.02)
    for k in range(3):
        a = k / 3 * math.pi
        tube(f"ValveSpoke{k}", [(0.8 - math.cos(a) * 0.2, y - 0.15, 3.6 - math.sin(a) * 0.2), (0.8 + math.cos(a) * 0.2, y - 0.15, 3.6 + math.sin(a) * 0.2)], 0.012,
             K["brassf"], poly=True)
    box("SoapShelf", (0.8, 0.35, 0.05), (-1.1, y - 0.15, 3.4), K["brassf"], bevel=0.01)
    box("Soap", (0.3, 0.18, 0.1), (-1.1, y - 0.15, 3.48), porcelain(), bevel=0.04)
    # curtain rail, rings and the curtain (pleated, pulled mostly to the left)
    zr = H - 0.6
    tube("Rail", [(-W / 2, -D / 2 + 0.15, zr), (W / 2, -D / 2 + 0.15, zr)], 0.03, K["brassf"], poly=True)
    curtain = B34.uv_fabric("CurtainStripe", "NH_Stripe", (0.16, 0.012, 0.02), 1.0)
    n, cw = 70, 1.9
    bm = bmesh.new()
    rows = []
    for j in range(25):
        z = 0.6 + j * (zr - 0.75) / 24
        row = []
        for i in range(n + 1):
            u = i / n
            x = -W / 2 + 0.05 + u * cw * (1 + 0.1 * (1 - z / zr))
            yy = -D / 2 + 0.15 + 0.1 * math.sin(u * 40) * (0.7 + 0.3 * z / zr)
            row.append(bm.verts.new((x, yy, z)))
        rows.append(row)
    uvf = bm.loops.layers.uv.new("Flat")
    for j in range(24):
        for i in range(n):
            f = bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
            f.smooth = True
            for lp in f.loops:
                lp[uvf].uv = (lp.vert.co.x, lp.vert.co.z)
    ob = B34.mesh_obj("Curtain", bm, curtain)
    _solid(ob, 0.015)
    for i in range(12):
        x = -W / 2 + 0.08 + i * cw * 1.0 / 11
        hoop(f"Ring{i}", (x, -D / 2 + 0.15, zr - 0.06), 0.06, "X", K["brassf"], thick=0.01)
    return _dims()


def mini_fridge(M):
    """A small crimson enamel fridge (1.6 x 1.6 x 2.6) with rounded corners, a brass handle and hinges, stickers and a note, a can on top."""
    K = kit(M)
    W, D, H = 1.6, 1.5, 2.5
    rbox("Body", W / 2, D / 2, 0.2, 0.12, H, K["enamel"], step=0.05, rows=6)
    box("Base", (W - 0.1, D - 0.1, 0.12), (0, 0, 0.06), K["iron"], bevel=0.02)
    yf = -D / 2
    box("DoorSeam", (W - 0.1, 0.01, 0.012), (0, yf - 0.002, 1.75), K["ink"], bevel=0.0)
    box("Handle", (0.06, 0.1, 0.8), (W / 2 - 0.2, yf - 0.06, 1.25), K["brassf"], bevel=0.02)
    for z in (0.5, 2.1):
        box(f"Hinge{z}", (0.06, 0.06, 0.18), (-W / 2 + 0.05, yf - 0.02, z), K["brassf"], bevel=0.01)
    box("Grille", (W - 0.3, 0.02, 0.15), (0, yf - 0.005, 0.24), K["iron"], bevel=0.005)
    for k, (key, x, z, a, s) in enumerate((("K9_Sticker_Bat", -0.35, 1.9, 8, 0.38), ("K9_Sticker_Moon", 0.25, 1.35, -6, 0.34), ("K9_Sticker_Skull", -0.3, 0.9, 12, 0.3),
                                          ("K9_Sticker_Note", 0.2, 2.15, -4, 0.36))):
        B30.plate(f"Sticker{k}", key, s, s, 0.004, T(x, yf - 0.004, z) @ RY(a * DEG), K["p9"], edge="K9_paper", k=2.0)
    sphere("Magnet", 0.04, (0.2, yf - 0.02, 2.3), plain("MagnetRed", (0.4, 0.02, 0.03), 0.3), seg=8, rings=4, scale=(1, 0.5, 1))
    B34.can("Can", "DP_Can_Moon", K, T(0.3, 0.1, H))
    _fine(0.7)
    return _dims()


def bean_bag(M):
    """A slumped crimson leather bean bag (2.8 across), dented where someone sat, creased round its middle."""
    K = kit(M)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
    g = random.Random(3907)
    ph = [g.uniform(0, 6.28) for _ in range(6)]
    for v in bm.verts:
        p = v.co.copy()
        r = 1.35 * (1 + 0.04 * math.sin(p.x * 7 + ph[0]) * math.sin(p.y * 6 + ph[1]) + 0.03 * math.sin(p.z * 9 + ph[2]))
        x, y, z = p.x * r, p.y * r, p.z * 0.75
        # sag: wider at the bottom, flat on the floor
        if z < 0:
            k = 1 + 0.25 * (-z)
            x, y = x * k, y * k
        # the sitting dent, toward the back, and a raised back
        d = math.exp(-((x - 0.0) ** 2 + (y - 0.15) ** 2) / 0.45)
        if z > 0:
            z -= 0.55 * d * z
            z += 0.25 * max(0.0, y) * (z > 0.2)
        z += 0.75
        v.co = Vector((x, y, max(0.0, z)))
    for f in bm.faces:
        f.smooth = True
    ob = B34.mesh_obj("Bag", bm, K["leather"])
    bpy.ops.object.select_all(action="DESELECT")
    tube("Seam", [(math.cos(t) * 1.4, math.sin(t) * 1.4, 0.6 + 0.05 * math.sin(t * 3)) for t in [i / 32 * 6.283 for i in range(32)]], 0.025, K["leather"],
         closed=True, poly=True)
    sphere("Zip", 0.05, (0, 1.42, 0.58), K["brassf"], seg=8, rings=4)
    return _dims()


def ping_pong_table(M):
    """A table-tennis table (9 x 5, top 2.5): a crimson top with bone lines on cast-iron trestles, the net (a printed plate) on brass
    clamps, two paddles and a ball."""
    K = kit(M)
    W, D, top = 9.0, 5.0, 2.5
    box("Top", (W, D, 0.12), (0, 0, top - 0.06), K["enamel"], bevel=0.02)
    box("Apron", (W - 0.6, D - 0.6, 0.2), (0, 0, top - 0.22), K["ebony"], bevel=0.015)
    bone = flat("LineBone", (0.66, 0.62, 0.52), 0.4)
    for nm, sz, loc in (("LineE1", (W - 0.02, 0.06, 0.004), (0, -D / 2 + 0.03, top + 0.002)), ("LineE2", (W - 0.02, 0.06, 0.004), (0, D / 2 - 0.03, top + 0.002)),
                        ("LineE3", (0.06, D - 0.02, 0.004), (-W / 2 + 0.03, 0, top + 0.002)), ("LineE4", (0.06, D - 0.02, 0.004), (W / 2 - 0.03, 0, top + 0.002)),
                        ("LineC", (W - 0.02, 0.03, 0.004), (0, 0, top + 0.002))):
        box(nm, sz, loc, bone, bevel=0.0)
    for sx in (-1, 1):
        x = sx * (W / 2 - 1.0)
        for sy in (-1, 1):
            tube(f"Leg{sx}{sy}", [(x, sy * (D / 2 - 0.5), 0.05), (x, sy * (D / 2 - 0.6), top - 0.3)], 0.06, K["iron"], square=True, poly=True)
            sphere(f"Foot{sx}{sy}", 0.09, (x, sy * (D / 2 - 0.5), 0.07), K["brass"], seg=8, rings=4)
        tube(f"Arch{sx}", [(x, y, z) for y, z in B34.seg_arc(D / 2 - 0.6, top - 0.9, 0.55, 14)], 0.045, K["iron"], poly=True)
        hoop(f"Ring{sx}", (x, 0, 1.0), 0.35, "X", K["iron"], thick=0.035)
    tube("Stretcher", [(-(W / 2 - 1.0), 0, 0.6), (W / 2 - 1.0, 0, 0.6)], 0.045, K["iron"], poly=True)
    # the net across the middle (along Y), on posts
    nh = 0.45
    B30.plate("Net", "K9_PP_Net", D + 0.4, nh, 0.012, T(0, 0, top + nh / 2) @ RZ(math.pi / 2), K["p9"], edge="K9_black", k=2.0)
    for sy in (-1, 1):
        cyl(f"NetPost{sy}", 0.035, nh + 0.05, (0, sy * (D / 2 + 0.2), top + nh / 2), K["brassf"], verts=10, bevel=0.005)
        box(f"Clamp{sy}", (0.12, 0.25, 0.14), (0, sy * (D / 2 + 0.08), top - 0.02), K["brassf"], bevel=0.01)
    # paddles and a ball
    for k, (x, y, a) in enumerate(((-2.6, -1.0, 30), (2.9, 1.2, -140))):
        s = _mark()
        cyl(f"Blade{k}", 0.38, 0.03, (0, 0, 0.015), K["ebony"], verts=28, bevel=0.005)
        P.PARTS[-1].scale = (1.0, 1.08, 1)
        cyl(f"Rubber{k}", 0.37, 0.012, (0, 0, 0.036), plain("PaddleRubber", (0.2, 0.015, 0.02), 0.7), verts=28, bevel=0.0)
        P.PARTS[-1].scale = (1.0, 1.08, 1)
        box(f"Handle{k}", (0.13, 0.5, 0.09), (0, -0.6, 0.045), K["oak"], bevel=0.03)
        _xform(s, T(x, y, top) @ RZ(a * DEG))
    sphere("Ball", 0.07, (0.8, -0.6, top + 0.07), plain("Ball", (0.82, 0.8, 0.72), 0.4), seg=14, rings=8)
    return _dims()


def ra_desk(M):
    """The resident adviser's lobby desk (6.0 wide, counter top 3.0): ebonised, black marble counter, crimson enamel panels, a brass
    RESIDENT ADVISER plate; the sign-in book open with a pen, a key board of numbered hooks behind, a service bell."""
    K = kit(M)
    W, D, top = 6.0, 2.4, 3.0
    wd = K["ebony"]
    box("Body", (W, D - 0.4, top - 0.35), (0, 0.2, 0.2 + (top - 0.35) / 2), wd, bevel=0.03)
    box("Plinth", (W + 0.1, D - 0.3, 0.2), (0, 0.2, 0.1), K["marble"], bevel=0.02)
    box("Counter", (W + 0.2, D, 0.15), (0, 0, top - 0.075), K["marble"], bevel=0.03)
    box("Bead", (W + 0.22, 0.03, 0.05), (0, -D / 2 - 0.005, top - 0.12), K["brass"], bevel=0.01)
    yf = 0.2 - (D - 0.4) / 2
    for k in range(3):
        cx = -W / 2 + 1.0 + k * (W - 2.0) / 2
        pts = WS.arch(0.7, 0.55, 1.75, 2.35, 8, cx=cx)
        B20.tprism(f"Field{k}", pts, yf - 0.01, 0.02, K["enamel"])
        tube(f"FieldEdge{k}", [(x, yf - 0.025, z) for x, z in pts] + [(pts[0][0], yf - 0.025, pts[0][1])], 0.03, K["iron"], square=True, poly=True)
    box("Plate", (2.4, 0.04, 0.32), (0, yf - 0.04, top - 0.42), K["brassf"], bevel=0.01)
    _text("PlateWord", "RESIDENT ADVISER", FONT, K["gilt"], lambda x, y, h: (x, yf - 0.06 - h, top - 0.42 + y), fit=(2.1, 0.18), depth=0.012, res=3)
    # the sign-in book, open, a pen on a chain
    s = _mark()
    cover = material("SignCloth", "NH_Leather", tint=(0.04, 0.05, 0.12), scale=2.5, normal=0.4, wear=0.3)
    pw, ph = 0.8, 1.05
    for sx in (-1, 1):
        box(f"Board{sx}", (pw + 0.04, ph + 0.06, 0.03), (sx * (pw / 2 + 0.01), 0, 0.015), cover, bevel=0.01)
        box(f"Block{sx}", (pw - 0.06, ph - 0.04, 0.05), (sx * (pw / 2 + 0.01), 0, 0.05), B24.pages("SignPages", (0.82, 0.78, 0.66)), bevel=0.01)

        def fn(sv, tv, sx=sx):
            x = sx * (0.02 + sv * (pw - 0.06))
            z = 0.08 + 0.05 * math.sin(min(1.0, sv * 1.3) * math.pi / 2) ** 0.6 - 0.025 * sv ** 3
            return (x, -ph / 2 + 0.03 + tv * (ph - 0.06), z)
        B30.leaf_sheet(f"Page{sx}", "K9_SignIn_L" if sx < 0 else "K9_SignIn_R", fn, 10, 1, (1, 0, 0, 1) if sx < 0 else (0, 0, 1, 1), K["p9"], thick=0.008, k=3.0)
    _xform(s, T(-0.9, -0.5, top) @ RZ(8 * DEG))
    cyl("Pen", 0.02, 0.45, (0.0, -0.75, top + 0.03), plain("PenBlack", (0.02, 0.02, 0.025), 0.25), rot=(0, math.pi / 2, 0.3), verts=10, bevel=0.003)
    B30.chain("PenChain", [(-0.2, -0.82, top + 0.02), (0.3, -0.95, top + 0.01), (0.5, -0.9, top + 0.02)], K["brass"], r=0.022, thick=0.005)
    B37.service_bell("Bell", K, (1.3, -0.6, top))
    # the key board behind: a gothic board on a back post with numbered brass tags on hooks
    zb = top + 0.4
    box("KeyPost", (0.2, 0.2, 2.6), (2.0, D / 2 - 0.2, top + 1.3), wd, bevel=0.02)
    s = _mark()
    pts = WS.arch(0.9, 0.0, 1.3, 1.8, 10)
    B20.tprism("KeyBoard", pts, 0.0, 0.08, wd)
    tube("KeyBoardEdge", [(x, -0.045, z) for x, z in pts] + [(pts[0][0], -0.045, pts[0][1])], 0.025, K["brass"], square=True, poly=True)
    for r in range(3):
        for c in range(4):
            x, z = -0.6 + c * 0.4, 0.35 + r * 0.38
            tube(f"Hook{r}{c}", [(x, -0.04, z), (x, -0.12, z), (x, -0.12, z + 0.04)], 0.01, K["brassf"], poly=True)
            if (r * 4 + c) % 5 == 3:
                continue
            if (r + c) % 2:
                box(f"TagOnly{r}{c}", (0.14, 0.012, 0.1), (x, -0.13, z - 0.1), K["brassf"], bevel=0.004)
                continue
            box(f"Tag{r}{c}", (0.14, 0.012, 0.1), (x, -0.13, z - 0.1), K["brassf"], bevel=0.004)
            B37.key_shape(f"Key{r}{c}", K, T(x, -0.12, z - 0.03) @ Matrix.Diagonal((0.45, 0.45, 0.45, 1)), L=0.35, bits=1 + c % 2, seed=r * 4 + c)
    _xform(s, T(2.0, D / 2 - 0.32, zb + 0.4))
    _text("KeysWord", "KEYS", FONT, K["gilt"], lambda x, y, h: (2.0 + x, D / 2 - 0.37 - h, zb + 0.4 + 1.55 + y), fit=(0.5, 0.14), depth=0.01, res=3)
    _fine(0.6)
    return _dims()


# ================================================================== girls' rooms

def vanity_table(M):
    """An ebonised dressing table (4.2 wide, top 2.6) with a black marble top, drawers, and an arched mirror (the Mirror piece) ringed
    with ten round bulbs (Glow); a brush and a bottle on top."""
    K = kit(M)
    W, D, top = 4.2, 1.8, 2.6
    wd = K["ebony"]
    box("Top", (W, D, 0.1), (0, 0, top - 0.05), K["marble"], bevel=0.02)
    for sx in (-1, 1):
        box(f"Ped{sx}", (1.1, D - 0.2, top - 0.4), (sx * (W / 2 - 0.6), 0, 0.3 + (top - 0.4) / 2 - 0.05), wd, bevel=0.02)
        for k in range(3):
            z = 0.55 + k * 0.62
            box(f"Drawer{sx}{k}", (0.95, 0.05, 0.52), (sx * (W / 2 - 0.6), -D / 2 + 0.08, z), wd, bevel=0.015)
            box(f"DrawerInset{sx}{k}", (0.7, 0.012, 0.3), (sx * (W / 2 - 0.6), -D / 2 + 0.05, z), K["enamel"], bevel=0.0)
            sphere(f"Knob{sx}{k}", 0.045, (sx * (W / 2 - 0.6), -D / 2 + 0.01, z), K["brassf"], seg=10, rings=5)
        for sy in (-1, 1):
            lathe(f"Leg{sx}{sy}", [(0, 0), (0.07, 0), (0.09, 0.1), (0.06, 0.25), (0, 0.25)], K["iron"], seg=12, loc=(sx * (W / 2 - 0.15), sy * (D / 2 - 0.2), 0))
    box("Apron", (W - 2.4, 0.08, 0.3), (0, -D / 2 + 0.12, top - 0.25), wd, bevel=0.015)
    # the mirror: an arched ebonised surround, bulbs round it
    from nh_props import _arch_loop
    hw, z0, zs, za = 1.2, top + 0.25, top + 2.2, top + 3.0
    y = D / 2 - 0.15
    B20.tprism("MirrorBack", [(x, z) for x, _, z in _arch_loop(0, 0, hw + 0.35, z0 - 0.15, zs, za + 0.35)], y, 0.1, wd)
    tube("MirrorFrame", _arch_loop(0, y - 0.06, hw + 0.05, z0, zs, za + 0.05), 0.04, K["brass"], square=True, closed=True, poly=True)
    set_group("Mirror")
    B20.tprism("Glass", [(x, z) for x, _, z in _arch_loop(0, 0, hw, z0, zs, za)], y - 0.06, 0.012, silvered())
    set_group("Main")
    ring = _arch_loop(0, y - 0.07, hw + 0.2, z0 + 0.1, zs, za + 0.22)
    pts = WS.resample([(p[0], p[2]) for p in ring], 0.1, closed=False)
    tot = len(pts)
    bulbs = [pts[int(i * (tot - 1) / 11)] for i in range(12)]
    for i, (x, z) in enumerate(bulbs):
        cyl(f"Socket{i}", 0.06, 0.08, (x, y - 0.09, z), K["brassf"], rot=(math.pi / 2, 0, 0), verts=12, bevel=0.01)
    set_group("Glow")
    for i, (x, z) in enumerate(bulbs):
        sphere(f"Bulb{i}", 0.085, (x, y - 0.19, z), K["paper"], seg=12, rings=6)
    set_group("Main")
    # a hairbrush and a bottle
    s = _mark()
    box("BrushBack", (0.22, 0.4, 0.06), (0, 0, 0.03), K["brassf"], bevel=0.025)
    box("BrushHandle", (0.08, 0.35, 0.04), (0, -0.36, 0.02), K["brassf"], bevel=0.015)
    box("Bristles", (0.18, 0.35, 0.05), (0, 0, -0.02), plain("Bristle", (0.1, 0.08, 0.07), 0.9), bevel=0.01)
    _xform(s, T(-1.3, -0.3, top + 0.045) @ RZ(30 * DEG))
    lathe("Bottle", [(0, 0), (0.12, 0), (0.14, 0.05), (0.14, 0.25), (0.06, 0.3), (0.04, 0.36), (0, 0.36)], plain("BottleViolet", (0.14, 0.05, 0.16), 0.08), seg=18,
          loc=(1.3, 0.1, top))
    sphere("BottleStopper", 0.06, (1.3, 0.1, top + 0.42), K["brassf"], seg=10, rings=5)
    return _dims()


def makeup_set(M):
    K = kit(M)
    # the palette, open: a mirror in the lid, a dozen colours in brass pans
    s = _mark()
    B34.pbox("PalBase", (0.9, 0.6, 0.06), (0, 0, 0.03), K["p9"], {"else": "sw:K9_black"}, k=1.0)
    cols = [(0.35, 0.05, 0.08), (0.12, 0.01, 0.03), (0.4, 0.25, 0.2), (0.25, 0.12, 0.25), (0.05, 0.05, 0.06), (0.5, 0.4, 0.3), (0.16, 0.1, 0.25), (0.45, 0.3, 0.12),
            (0.6, 0.35, 0.32), (0.08, 0.12, 0.2), (0.3, 0.18, 0.1), (0.55, 0.5, 0.45)]
    for k, c in enumerate(cols):
        x, y = -0.32 + (k % 4) * 0.21, -0.17 + (k // 4) * 0.17
        cyl(f"Pan{k}", 0.075, 0.025, (x, y, 0.065), K["brassf"], verts=16, bevel=0.003)
        cyl(f"Shade{k}", 0.068, 0.005, (x, y, 0.079), plain(f"Shade{k}", c, 0.7), verts=16, bevel=0.0)
    s2 = _mark()
    B34.pbox("PalLid", (0.9, 0.6, 0.04), (0, -0.3, 0.02), K["p9"], {"top": "K9_Makeup_Lid", "else": "sw:K9_black"}, k=1.6)
    box("PalMirror", (0.8, 0.5, 0.005), (0, -0.3, -0.003), silvered(), bevel=0.0)
    _xform(s2, T(0, 0.3, 0.06) @ RX(-100 * DEG))
    _xform(s, T(-0.35, -0.1, 0) @ RZ(-10 * DEG))
    # brushes in a cup
    lathe("Cup", [(0, 0), (0.17, 0), (0.18, 0.02), (0.18, 0.45), (0.16, 0.45), (0.16, 0.04), (0, 0.04)], K["enamel"], seg=24, loc=(0.7, 0.35, 0))
    hoop("CupRim", (0.7, 0.35, 0.45), 0.17, "Z", K["gilt"], thick=0.012)
    g = random.Random(3912)
    for k in range(6):
        a = k / 6 * 6.283
        bx, by = 0.7 + math.cos(a) * 0.08, 0.35 + math.sin(a) * 0.08
        tip = (bx + math.cos(a) * 0.16, by + math.sin(a) * 0.16, 0.85 + g.uniform(-0.05, 0.08))
        tube(f"BrushH{k}", [(bx, by, 0.05), tip], 0.015, K["ebony"], poly=True)
        d = Vector(tip) - Vector((bx, by, 0.05))
        d.normalize()
        p = Vector(tip)
        cyl(f"Ferrule{k}", 0.02, 0.06, tuple(p + d * 0.03), K["brassf"], verts=10, bevel=0.002)
        P.PARTS[-1].rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        sphere(f"Bristle{k}", 0.04 if k % 2 else 0.028, tuple(p + d * 0.1), plain("BrushHair", (0.25, 0.18, 0.12), 0.9), seg=10, rings=6, scale=(1, 1, 1.8))
        P.PARTS[-1].rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    # lipsticks: two standing, one lying open
    for k, (x, y, c, up) in enumerate(((0.25, 0.45, (0.3, 0.01, 0.03), True), (0.4, 0.5, (0.1, 0.01, 0.02), True), (0.3, -0.5, (0.45, 0.06, 0.1), False))):
        s = _mark()
        cyl(f"LipCase{k}", 0.05, 0.22, (0, 0, 0.11), K["brassf"], verts=16, bevel=0.005)
        cyl(f"LipBand{k}", 0.052, 0.04, (0, 0, 0.06), K["ebony"], verts=16, bevel=0.003)
        lathe(f"Lip{k}", [(0, 0.22), (0.035, 0.22), (0.035, 0.29), (0.0, 0.32)], plain(f"Lipstick{k}", c, 0.3), seg=14)
        _xform(s, T(x, y, 0) if up else T(x, y, 0.05) @ RZ(0.5) @ RY(90 * DEG))
    lathe("Compact", [(0, 0), (0.18, 0), (0.19, 0.02), (0.18, 0.06), (0, 0.06)], K["gilt"], seg=28, loc=(-0.6, 0.5, 0))
    _fine(0.35)
    return _dims()


def jewelry_box(M):
    """An open jewellery box (1.2 x 0.8): ebonised with brass corners, crimson velvet inside, a mirror in the lid; necklaces spill over
    the front, rings in their slots."""
    K = kit(M)
    W, D, H = 1.2, 0.8, 0.45
    t = 0.04
    for nm, sz, loc in (("Floor", (W, D, t), (0, 0, t / 2)), ("Front", (W, t, H), (0, -D / 2 + t / 2, H / 2)), ("Back", (W, t, H), (0, D / 2 - t / 2, H / 2)),
                        ("Left", (t, D, H), (-W / 2 + t / 2, 0, H / 2)), ("Right", (t, D, H), (W / 2 - t / 2, 0, H / 2))):
        box(nm, sz, loc, K["ebony"], bevel=0.008)
    box("Velvet", (W - 2 * t, D - 2 * t, 0.2), (0, 0, t + 0.1), K["velvet"], bevel=0.01)
    for k in range(4):
        box(f"RingSlot{k}", (W - 0.2, 0.03, 0.03), (0, -0.15 + k * 0.08, t + 0.2), K["groove"], bevel=0.0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f"Corner{sx}{sy}", (0.08, 0.08, H + 0.01), (sx * (W / 2 - 0.02), sy * (D / 2 - 0.02), H / 2), K["brassf"], bevel=0.01)
    # the lid, open, mirror inside
    s = _mark()
    box("Lid", (W, D, 0.08), (0, 0, 0.04), K["ebony"], bevel=0.012)
    box("LidVelvet", (W - 0.1, D - 0.1, 0.01), (0, 0, -0.005), K["velvet"], bevel=0.0)
    box("LidMirror", (W - 0.3, D - 0.3, 0.006), (0, 0, -0.012), silvered(), bevel=0.0)
    _xform(s, T(0, D / 2, H) @ RX(-100 * DEG) @ T(0, -D / 2, 0))
    # rings
    for k in range(5):
        hoop(f"Ring{k}", (-0.4 + k * 0.2, -0.15 + (k % 4) * 0.08, t + 0.24), 0.05, "X", K["gilt"] if k % 2 else K["steel"], thick=0.01)
        if k % 2 == 0:
            sphere(f"Gem{k}", 0.025, (-0.4 + k * 0.2, -0.15 + (k % 4) * 0.08, t + 0.3), plain(f"Gem{k}", ((0.4, 0.01, 0.03), (0.02, 0.05, 0.3), (0.02, 0.2, 0.06))[k // 2 % 3], 0.05),
                   seg=8, rings=4)
    # necklaces draped over the front edge
    for k, (x0, col) in enumerate(((-0.3, K["gilt"]), (0.15, K["steel"]))):
        pts = [(x0, 0.05, t + 0.22), (x0 + 0.05, -D / 2 + 0.02, H + 0.01), (x0 + 0.08, -D / 2 - 0.05, H - 0.15), (x0 + 0.1, -D / 2 - 0.06, H - 0.35 + k * 0.08)]
        B30.chain(f"Chain{k}", pts, col, r=0.012, thick=0.003)
        sphere(f"Pendant{k}", 0.04, (x0 + 0.1, -D / 2 - 0.07, H - 0.39 + k * 0.08), plain("Garnet", (0.25, 0.01, 0.02), 0.05) if k == 0 else K["gilt"], seg=10,
               rings=6, scale=(1, 0.5, 1.3))
    B30.chain("ChainLoose", [(0.3, -0.25, 0.0), (0.55, -0.45, 0.0), (0.75, -0.3, 0.0), (0.6, -0.15, 0.0)], K["gilt"], r=0.012, thick=0.003)
    _fine(0.3)
    return _dims()


def perfume_tray(M):
    """A mirrored silver tray (1.4 x 0.9) of perfume bottles (Glass: the bottles), coloured scent in each, brass and crystal stoppers, an
    atomiser with a tasselled bulb, printed labels."""
    K = kit(M)
    silver = material("TraySilver", base=(0.62, 0.62, 0.64), rough=0.18, metal=1.0, wear=0.25, dirt=0.8)
    lathe("Tray", [(0, 0), (0.6, 0), (0.66, 0.03), (0.7, 0.08), (0.67, 0.09), (0.62, 0.04), (0, 0.04)], silver, seg=40, scale=(1.0, 0.65))
    lathe("TrayMirror", [(0, 0.041), (0.6, 0.041), (0.6, 0.045), (0, 0.045)], silvered(), seg=40, scale=(1.0, 0.65))
    for k in range(3):
        sphere(f"Foot{k}", 0.03, (math.cos(k * 2.09) * 0.5, math.sin(k * 2.09) * 0.32, 0.01), silver, seg=8, rings=4)
    z0 = 0.045
    bottles = [((-0.32, 0.05), [(0, 0), (0.13, 0), (0.15, 0.03), (0.15, 0.3), (0.08, 0.36), (0.05, 0.38), (0, 0.38)], (0.08, 0.02, 0.1), "K9_Perfume_Nocturne"),
               ((0.0, 0.12), [(0, 0), (0.1, 0), (0.16, 0.12), (0.16, 0.2), (0.09, 0.3), (0.04, 0.32), (0, 0.32)], (0.3, 0.02, 0.04), "K9_Perfume_Velvet"),
               ((0.3, 0.0), [(0, 0), (0.09, 0), (0.1, 0.02), (0.1, 0.42), (0.04, 0.46), (0, 0.46)], (0.5, 0.45, 0.35), "K9_Perfume_Moonmilk")]
    for k, ((x, y), prof, col, lab) in enumerate(bottles):
        inner = [(r * 0.85, z * 0.85 + 0.01) for r, z in prof]
        lathe(f"Scent{k}", inner[:4] + [(0, inner[3][1])], plain(f"Scent{k}", col, 0.05), seg=20, loc=(x, y, z0))
        top = prof[-1][1]
        lathe(f"Stopper{k}", [(0, 0), (0.05, 0), (0.06, 0.04), (0.04, 0.08), (0.07, 0.14), (0, 0.18)], K["brassf"] if k != 1 else K["gilt"], seg=16, loc=(x, y, z0 + top))
        B30.plate(f"Label{k}", lab, 0.16, 0.12, 0.004, T(x, y - 0.155 if k != 2 else y - 0.105, z0 + 0.15), K["p9"], edge="K9_paper", k=1.8)
    # the atomiser
    ax, ay = 0.15, -0.2
    tube("AtomTube", [(ax, ay, z0 + 0.28), (ax + 0.12, ay - 0.05, z0 + 0.3), (ax + 0.25, ay - 0.1, z0 + 0.2)], 0.008, K["brassf"])
    sphere("AtomBulb", 0.06, (ax + 0.28, ay - 0.12, z0 + 0.14), plain("AtomBulb", (0.3, 0.02, 0.05), 0.6), seg=12, rings=6, scale=(1, 1, 1.3))
    tube("Tassel", [(ax + 0.3, ay - 0.13, z0 + 0.07), (ax + 0.32, ay - 0.15, z0 + 0.0)], 0.02, K["gilt"], poly=True)
    set_group("Glass")
    for k, ((x, y), prof, col, lab) in enumerate(bottles):
        lathe(f"Bottle{k}", prof, K["glass"], seg=24, loc=(x, y, z0))
    lathe("Atomiser", [(0, 0), (0.1, 0), (0.12, 0.1), (0.1, 0.22), (0.04, 0.26), (0, 0.27)], K["glass"], seg=20, loc=(ax, ay, z0))
    set_group("Main")
    _fine(0.35)
    return _dims()


def shoe_heel(prefix, mat, mtx, sole):
    """A court shoe, toe to -Y, sole on z = 0."""
    s = _mark()
    prof = [(-0.42, 0.0), (-0.15, 0.0), (0.05, 0.08), (0.22, 0.24), (0.32, 0.27), (0.32, 0.3), (0.2, 0.28), (0.05, 0.12), (-0.15, 0.025), (-0.42, 0.025)]
    B20.tprism(f"{prefix}Sole", prof, 0.0, 0.17, sole, plane="YZ")
    cone(f"{prefix}Heel", 0.035, 0.012, 0.27, (0, 0.29, 0.135), sole, verts=10)
    sphere(f"{prefix}Vamp", 0.1, (0, -0.28, 0.03), mat, seg=14, rings=7, scale=(0.95, 1.5, 0.75))
    strip(f"{prefix}Counter", [(-0.085, 0.05, 0.13), (-0.085, 0.2, 0.3), (0.0, 0.33, 0.4), (0.085, 0.2, 0.3), (0.085, 0.05, 0.13)], 0.12, (0, 0, 1), mat,
          thick=0.012)
    _xform(s, mtx)


def boot(prefix, mat, mtx, buckle):
    s = _mark()
    rbox(f"{prefix}Sole", 0.1, 0.24, 0.08, 0.0, 0.05, flat("BootSole", (0.03, 0.03, 0.03), 0.8))
    box(f"{prefix}Heel", (0.16, 0.14, 0.15), (0, 0.16, 0.075), flat("BootSole", (0.03, 0.03, 0.03), 0.8), bevel=0.02)
    sphere(f"{prefix}Foot", 0.12, (0, -0.08, 0.1), mat, seg=14, rings=7, scale=(0.85, 1.6, 0.7))
    lathe(f"{prefix}Shaft", [(0, 0.05), (0.1, 0.05), (0.11, 0.3), (0.11, 0.85), (0.12, 0.9), (0, 0.88)], mat, seg=18, loc=(0, 0.12, 0.05), scale=(1.0, 1.15))
    for z in (0.3, 0.55):
        box(f"{prefix}Strap{z}", (0.25, 0.27, 0.035), (0, 0.12, z), mat, bevel=0.01)
        box(f"{prefix}Buckle{z}", (0.06, 0.02, 0.05), (0.12, 0.12, z), buckle, bevel=0.005)
    _xform(s, mtx)


def shoe_rack(M):
    """A three-tier cast-iron shoe rack (3.0 wide, 2.2 tall) with heels on the top tiers and boots on the floor tier."""
    K = kit(M)
    ir = K["iron"]
    W, D = 3.0, 1.0
    tiers = (0.25, 0.95, 1.65)
    for sx in (-1, 1):
        tube(f"Side{sx}", [(sx * W / 2, -D / 2, 0.0), (sx * W / 2, -D / 2, 2.1), (sx * W / 2, D / 2, 2.1), (sx * W / 2, D / 2, 0.0)], 0.035, ir, square=True, poly=True)
        sphere(f"Finial{sx}", 0.06, (sx * W / 2, -D / 2, 2.17), K["brass"], seg=8, rings=4)
        hoop(f"SideRing{sx}", (sx * W / 2, 0, 1.3), 0.2, "X", ir, thick=0.02)
    for k, z in enumerate(tiers):
        for sy in (-1, 1):
            tube(f"Bar{k}{sy}", [(-W / 2, sy * 0.3, z + sy * 0.05), (W / 2, sy * 0.3, z + sy * 0.05)], 0.025, ir, poly=True)
    tube("TopRail", [(-W / 2, 0, 2.1), (W / 2, 0, 2.1)], 0.03, ir, poly=True)
    patent = material("Patent", base=(0.13, 0.008, 0.02), rough=0.12, wear=0.1)
    black = material("PatentBlack", base=(0.012, 0.012, 0.014), rough=0.12, wear=0.1)
    sole = flat("HeelSole", (0.03, 0.025, 0.025), 0.4)
    leather = material("BootLeather", "NH_Leather", tint=(0.03, 0.025, 0.025), scale=3.0, normal=0.5, wear=0.4)
    for k, x in enumerate((-1.1, -0.75, 0.2, 0.55)):
        z = tiers[2] + 0.08
        shoe_heel(f"HA{k}", patent if k < 2 else black, T(x, 0.0, z) @ RX(4 * DEG), sole)
    for k, x in enumerate((-0.9, -0.55, 0.6, 0.95)):
        shoe_heel(f"HB{k}", black if k < 2 else patent, T(x, 0.0, tiers[1] + 0.08) @ RX(4 * DEG), sole)
    for k, x in enumerate((-1.0, -0.55, 0.5)):
        boot(f"Boot{k}", leather, T(x, 0.0, 0.0) @ RZ((-8 + k * 6) * DEG), K["brassf"])
    boot("BootFallen", leather, T(1.15, -0.3, 0.12) @ RZ(-40 * DEG) @ RY(80 * DEG), K["brassf"])
    return _dims()


def fairy_lights(M):
    """A string of little bulbs (Glow) hung from a brass wall hook (back on the wall at y = 0, the hook at 3.0), sagging in loops along the
    wall and trailing down."""
    K = kit(M)
    cyl("HookPlate", 0.08, 0.03, (0, -0.015, 3.0), K["brassf"], rot=(math.pi / 2, 0, 0), verts=14, bevel=0.008)
    tube("Hook", [(0, -0.03, 3.0), (0, -0.14, 3.0), (0, -0.16, 3.08)], 0.015, K["brassf"])
    wire = flat("LightWire", (0.03, 0.04, 0.03), 0.5)
    pts = []
    # three swags off the hook (to the left), then a tail down to the floor on the right
    segs = [((0, 3.0), (-1.4, 2.95), 0.5), ((-1.4, 2.95), (-2.6, 3.0), 0.45), ((0, 3.0), (1.1, 3.0), 0.35)]
    curves = []
    for (a, b, sag) in segs:
        c = []
        for i in range(25):
            t = i / 24
            x = a[0] + (b[0] - a[0]) * t
            z = a[1] + (b[1] - a[1]) * t - sag * math.sin(t * math.pi)
            c.append((x, -0.12, z))
        curves.append(c)
    tail = [(1.1, -0.1, 3.0), (1.2, -0.12, 2.4), (1.15, -0.13, 1.6), (1.25, -0.12, 0.9), (1.4, -0.2, 0.2), (1.8, -0.4, 0.02)]
    for k in range(2):
        hoop(f"Tack{k}", ((-1.4, -2.6)[k], -0.03, (2.95, 3.0)[k]), 0.04, "Y", K["brassf"], thick=0.01)
    hoop("Tack2", (1.1, -0.03, 3.0), 0.04, "Y", K["brassf"], thick=0.01)
    bulbs = []
    for k, c in enumerate(curves):
        tube(f"Wire{k}", c, 0.008, wire, poly=True)
        bulbs += c[2::3]
    tube("Tail", tail, 0.008, wire)
    for i in range(10):
        t = i / 9
        k = min(len(tail) - 2, int(t * (len(tail) - 1)))
        f = t * (len(tail) - 1) - k
        p = Vector(tail[k]).lerp(Vector(tail[k + 1]), f)
        bulbs.append(tuple(p))
    box("Plug", (0.12, 0.06, 0.18), (1.85, -0.42, 0.06), plain("Plug", (0.7, 0.68, 0.62), 0.4), bevel=0.02)
    for i, p in enumerate(bulbs):
        cyl(f"Cap{i}", 0.022, 0.04, (p[0], p[1], p[2] - 0.03), K["brassf"], verts=8, bevel=0.003)
    set_group("Glow")
    for i, p in enumerate(bulbs):
        sphere(f"Bulb{i}", 0.04, (p[0], p[1], p[2] - 0.08), K["paper"], seg=10, rings=6, scale=(1, 1, 1.3))
    set_group("Main")
    _fine(0.5)
    return _dims()


# ================================================================== boys' rooms

def plate_weight(prefix, x, r, K, axis_len=0.08):
    cyl(f"{prefix}", r, axis_len, (x, 0, 0), K["iron"], rot=(0, math.pi / 2, 0), verts=28, bevel=0.012)
    cyl(f"{prefix}Hub", 0.06, axis_len + 0.02, (x, 0, 0), K["enamel"], rot=(0, math.pi / 2, 0), verts=14, bevel=0.005)


def weight_bench(M):
    """A flat weight bench (pad top 1.6) with an iron upright rack holding a loaded barbell (bar at 3.4), crimson leather pad."""
    K = kit(M)
    ir = K["iron"]
    L = 4.6
    box("Pad", (1.0, L, 0.25), (0, 0.2, 1.48), K["leather"], bevel=0.08, segments=3)
    box("PadBoard", (0.9, L - 0.1, 0.06), (0, 0.2, 1.33), K["ebony"], bevel=0.01)
    tube("Spine", [(0, -1.8, 1.25), (0, 2.3, 1.25)], 0.07, ir, square=True, poly=True)
    for y in (-1.8, 2.3):
        tube(f"Leg{y}", [(0, y, 1.25), (0, y, 0.1)], 0.07, ir, square=True, poly=True)
        tube(f"Foot{y}", [(-0.8, y, 0.06), (0.8, y, 0.06)], 0.07, ir, square=True, poly=True)
        for sx in (-1, 1):
            sphere(f"FootCap{y}{sx}", 0.08, (sx * 0.8, y, 0.06), K["rubber"], seg=8, rings=4)
    # uprights at the head (-Y end)
    for sx in (-1, 1):
        x = sx * 1.4
        tube(f"Upright{sx}", [(x, -1.8, 0.1), (x, -1.8, 3.6)], 0.07, ir, square=True, poly=True)
        tube(f"Brace{sx}", [(x, -1.8, 1.0), (sx * 0.1, -1.2, 1.25)], 0.05, ir, square=True, poly=True)
        tube(f"Cradle{sx}", [(x, -1.8, 3.3), (x, -1.95, 3.3), (x, -2.0, 3.45)], 0.04, ir, poly=True)
        tube(f"Base{sx}", [(x, -2.4, 0.06), (x, -1.2, 0.06)], 0.07, ir, square=True, poly=True)
    tube("RackTop", [(-1.4, -1.8, 3.6), (1.4, -1.8, 3.6)], 0.05, ir, square=True, poly=True)
    s = _mark()
    cyl("Bar", 0.04, 5.6, (0, 0, 0), K["steel"], rot=(0, math.pi / 2, 0), verts=12, bevel=0.003)
    for sx in (-1, 1):
        cyl(f"Collar{sx}", 0.07, 0.1, (sx * 1.6, 0, 0), K["steel"], rot=(0, math.pi / 2, 0), verts=14, bevel=0.01)
        for k, r in enumerate((0.75, 0.6, 0.45)):
            plate_weight(f"Plate{sx}{k}", sx * (1.75 + k * 0.11), r, K)
    _xform(s, T(0, -1.92, 3.4))
    return _dims()


def dumbbell(prefix, K, mtx, r=0.17, L=0.9):
    s = _mark()
    cyl(f"{prefix}Grip", 0.05, L * 0.5, (0, 0, 0), K["steel"], rot=(0, math.pi / 2, 0), verts=12, bevel=0.004)
    for sx in (-1, 1):
        cyl(f"{prefix}Head{sx}", r, L * 0.22, (sx * L * 0.36, 0, 0), K["iron"], rot=(0, math.pi / 2, 0), verts=6, bevel=0.02)
        cyl(f"{prefix}Band{sx}", r * 0.6, L * 0.24, (sx * L * 0.36, 0, 0), K["enamel"], rot=(0, math.pi / 2, 0), verts=12, bevel=0.005)
    _xform(s, mtx)


def dumbbells(M):
    """A small two-tier iron rack (2.6 wide, 2.0 tall) of six hex dumbbells, smallest at the top, one pair on the floor."""
    K = kit(M)
    ir = K["iron"]
    W = 2.6
    for sx in (-1, 1):
        tube(f"Frame{sx}", [(sx * W / 2, 0.5, 0.0), (sx * W / 2, 0.0, 2.0), (sx * W / 2, -0.5, 0.0)], 0.05, ir, square=True, poly=True)
        tube(f"FrameBar{sx}", [(sx * W / 2, -0.4, 0.4), (sx * W / 2, 0.4, 0.4)], 0.04, ir, square=True, poly=True)
    for k, (y, z) in enumerate(((-0.25, 1.3), (0.15, 0.75))):
        for sy in (-1, 1):
            tube(f"Shelf{k}{sy}", [(-W / 2, y + sy * 0.12, z), (W / 2, y + sy * 0.12, z)], 0.03, ir, poly=True)
    for k in range(3):
        dumbbell(f"DA{k}", K, T(-0.8 + k * 0.8, -0.25, 1.3 + 0.13), r=0.12 + k * 0.01, L=0.7)
    for k in range(3):
        dumbbell(f"DB{k}", K, T(-0.8 + k * 0.8, 0.15, 0.75 + 0.19), r=0.18 + k * 0.01, L=0.9)
    dumbbell("DF0", K, T(-0.4, -1.0, 0.2) @ RZ(0.3), r=0.2, L=0.95)
    dumbbell("DF1", K, T(0.5, -1.1, 0.2) @ RZ(-0.2), r=0.2, L=0.95)
    return _dims()


def guitar_outline(n=48):
    """An acoustic guitar body (lower bout, waist, upper bout) as (x, y) in studs, its neck end at +y."""
    pts = []
    for i in range(n):
        t = i / n * 2 * math.pi
        y = math.sin(t) * 0.95
        w = 0.62 - 0.12 * math.exp(-((y - 0.15) / 0.18) ** 2) - 0.13 * max(0.0, y) ** 1.5
        pts.append((math.cos(t) * w, y))
    return pts


def guitar_stand(M):
    """An acoustic guitar (RAVENSWORTH, an invented maker) on an iron tripod stand; the guitar leans back, its headstock at 4.4."""
    K = kit(M)
    ir = K["iron"]
    for k in range(3):
        a = k / 3 * 2 * math.pi + math.pi / 2
        tube(f"Leg{k}", [(0, 0.1, 1.2), (math.cos(a) * 0.7, 0.1 + math.sin(a) * 0.6, 0.02)], 0.03, ir, poly=True)
        sphere(f"Toe{k}", 0.04, (math.cos(a) * 0.7, 0.1 + math.sin(a) * 0.6, 0.03), K["rubber"], seg=8, rings=4)
    tube("Mast", [(0, 0.1, 1.2), (0, 0.4, 3.3)], 0.03, ir, poly=True)
    tube("Yoke", [(-0.18, 0.36, 3.35), (0, 0.4, 3.25), (0.18, 0.36, 3.35)], 0.025, ir)
    for sx in (-1, 1):
        tube(f"Cradle{sx}", [(0, 0.1, 1.2), (sx * 0.4, -0.15, 0.6)], 0.03, ir, poly=True)
        sphere(f"CradleCap{sx}", 0.05, (sx * 0.4, -0.15, 0.6), K["rubber"], seg=8, rings=4)
    # the guitar, built lying on its back (top at +z, neck toward +y), then stood up and leaned back
    s = _mark()
    body_w = material("GuitarBody", "NH_DeskWood", tint=(0.2, 0.06, 0.03), scale=0.5, rough_add=-0.2, wear=0.2)
    top_w = material("GuitarTop", "NH_DeskWood", tint=(0.25, 0.11, 0.05), scale=0.8, rough_add=-0.25, wear=0.15)
    ebony_w = K["ebony"]
    outl = guitar_outline()
    B20.tprism("Sides", outl, 0.0, 0.4, body_w, plane="XY")
    B20.tprism("TopPlate", outl, 0.4, 0.01, top_w, plane="XY")
    tube("Binding", [(x, y, 0.405) for x, y in outl], 0.012, K["bone"], closed=True, poly=True)
    cyl("Hole", 0.17, 0.005, (0, 0.3, 0.413), K["ink"], verts=28, bevel=0.0)
    hoop("Rosette", (0, 0.3, 0.413), 0.2, "Z", K["bone"], thick=0.012)
    hoop("Rosette2", (0, 0.3, 0.413), 0.23, "Z", K["gilt"], thick=0.006)
    box("Bridge", (0.4, 0.1, 0.03), (0, -0.45, 0.425), ebony_w, bevel=0.01)
    box("Saddle", (0.3, 0.015, 0.02), (0, -0.43, 0.445), K["bone"], bevel=0.0)
    B20.tprism("Guard", [(0.12, 0.05), (0.32, 0.12), (0.36, 0.35), (0.2, 0.5), (0.18, 0.3)], 0.411, 0.004, K["ink"], plane="XY")
    box("Neck", (0.18, 1.7, 0.12), (0, 1.75, 0.34), body_w, bevel=0.03)
    box("Board", (0.17, 1.75, 0.03), (0, 1.73, 0.415), ebony_w, bevel=0.005)
    for k in range(14):
        y = 0.9 + 1.7 * (1 - 0.94 ** (k + 1)) / (1 - 0.94 ** 15)
        box(f"Fret{k}", (0.17, 0.008, 0.01), (0, 2.6 - (y - 0.9), 0.433), K["steel"], bevel=0.0)
    box("Head", (0.28, 0.55, 0.06), (0, 2.85, 0.36), ebony_w, bevel=0.02)
    _text("Brand", "RAVENSWORTH", FONT, K["gilt"], lambda x, y, h: (y, 2.86 + x, 0.39 + h), fit=(0.42, 0.07), depth=0.004, res=2)
    for sx in (-1, 1):
        for k in range(3):
            cyl(f"Peg{sx}{k}", 0.025, 0.12, (sx * 0.17, 2.7 + k * 0.14, 0.36), K["brassf"], rot=(0, math.pi / 2, 0), verts=8, bevel=0.003)
    for k in range(6):
        x = -0.06 + k * 0.024
        tube(f"String{k}", [(x * 1.3, -0.43, 0.45), (x, 2.6, 0.44)], 0.003, K["steel"], poly=True)
    _xform(s, T(0, -0.15, 0.6 + 0.95 * math.cos(14 * DEG)) @ RX(-14 * DEG) @ RX(math.pi / 2) @ T(0, 0, -0.2))
    return _dims()


def tv_console(M):
    """A modern flat screen dressed gothic, on a low ebonised media console (black marble top 1.5): a slim black panel (3.6 wide) in a
    carved dark-oak frame with brass inlay, pointed spandrels in its top corners and a crest with a brass quatrefoil, on blackened-iron
    feet; the screen (Glow) shows the invented game CRYPT CRAWLER. On the shelf a slim invented console with a crimson light (Glow),
    a sleek black-and-crimson controller in front."""
    K = kit(M)
    W, D, top = 4.4, 1.8, 1.5
    wd = K["ebony"]
    oak = K["darkoak"]
    # the console cabinet: an open shelf between ebonised ends, a black marble top
    box("CabBase", (W, D, 0.2), (0, 0, 0.35), wd, bevel=0.02)
    box("CabBack", (W, 0.08, top - 0.55), (0, D / 2 - 0.04, 0.45 + (top - 0.55) / 2), wd, bevel=0.01)
    for sx in (-1, 1):
        box(f"CabEnd{sx}", (0.14, D, top - 0.35), (sx * (W / 2 - 0.07), 0, 0.25 + (top - 0.35) / 2), wd, bevel=0.02)
        tube(f"EndArch{sx}", [(sx * (W / 2 + 0.002), y, z) for y, z in WS.arch(0.55, 0.5, 0.95, 1.25, 8)], 0.015, K["brass"], poly=True)
    box("CabMid", (0.1, D - 0.1, top - 0.55), (0.55, 0, 0.45 + (top - 0.55) / 2), wd, bevel=0.01)
    box("CabTopBoard", (W, D, 0.08), (0, 0, top - 0.14), wd, bevel=0.01)
    box("CabTop", (W + 0.08, D + 0.06, 0.1), (0, 0, top - 0.05), K["marble"], bevel=0.02)
    box("BrassEdge", (W, 0.03, 0.04), (0, -D / 2 - 0.01, 0.45), K["brass"], bevel=0.005)
    for sx in (-1, 1):
        for sy in (-1, 1):
            lathe(f"Leg{sx}{sy}", [(0, 0), (0.06, 0), (0.08, 0.15), (0.05, 0.25), (0, 0.25)], K["iron"], seg=12, loc=(sx * (W / 2 - 0.15), sy * (D / 2 - 0.15), 0))
    # games on the right of the divider
    for k in range(4):
        box(f"Game{k}", (0.07, 0.6, 0.45), (0.9 + k * 0.09, 0.0, 0.45 + 0.225), plain(f"GameCase{k}", ((0.12, 0.01, 0.02), (0.02, 0.02, 0.03), (0.1, 0.05, 0.14),
                                                                                                   (0.02, 0.02, 0.03))[k], 0.3), bevel=0.01)
    # the panel and its frame
    pw, ph, pt = 3.6, 3.6 * 9 / 16, 0.1
    zc = top + 0.45 + ph / 2
    yb = 0.15
    box("Panel", (pw, pt, ph), (0, yb, zc), plain("PanelBlack", (0.012, 0.012, 0.014), 0.25), bevel=0.02)
    box("PanelBack", (pw * 0.6, 0.12, ph * 0.6), (0, yb + 0.1, zc), plain("PanelBlack", (0.012, 0.012, 0.014), 0.25), bevel=0.03)
    fw, fd = 0.16, 0.16
    yf = yb - pt / 2 - fd / 2 + 0.04
    hw, hh = pw / 2 + fw / 2 - 0.04, ph / 2 + fw / 2 - 0.04
    for nm, sz, loc in (("FrameT", (pw + 2 * fw - 0.08, fd, fw), (0, yf, zc + hh)), ("FrameB", (pw + 2 * fw - 0.08, fd, fw), (0, yf, zc - hh)),
                        ("FrameL", (fw, fd, ph - 0.08), (-hw, yf, zc)), ("FrameR", (fw, fd, ph - 0.08), (hw, yf, zc))):
        box(nm, sz, loc, oak, bevel=0.03, segments=3)
    yi = yf - fd / 2 - 0.004
    tube("Inlay", [(-hw, yi, zc - hh), (hw, yi, zc - hh), (hw, yi, zc + hh), (-hw, yi, zc + hh)], 0.01, K["brassf"], square=True, closed=True, poly=True)
    tube("InlayIn", [(-pw / 2 + 0.02, yi + 0.03, zc - ph / 2 + 0.02), (pw / 2 - 0.02, yi + 0.03, zc - ph / 2 + 0.02), (pw / 2 - 0.02, yi + 0.03, zc + ph / 2 - 0.02),
                     (-pw / 2 + 0.02, yi + 0.03, zc + ph / 2 - 0.02)], 0.008, K["brassf"], square=True, closed=True, poly=True)
    # pointed spandrels in the top corners (the screen's top corners framed as a flattened pointed arch)
    zt = zc + ph / 2
    for sx in (-1, 1):
        x0 = sx * pw / 2
        pts = [(x0, zt), (x0, zt - 0.42)] + [(x0 - sx * 0.42 * (1 - math.cos(t * math.pi / 2)), zt - 0.42 * (1 - math.sin(t * math.pi / 2))) for t in
                                             [i / 6 for i in range(1, 7)]]
        B20.tprism(f"Spandrel{sx}", pts, yi + 0.02, 0.05, oak)
        tube(f"SpandrelLine{sx}", [(x, yi - 0.005, z) for x, z in pts[1:]], 0.008, K["brassf"], poly=True)
    _gable("Crest", 0, yf, 0.55, zc + hh + fw / 2 - 0.02, zc + hh + 0.55, fd, oak, K["brassf"], edge=0.02)
    foil("CrestFoil", 0, yf - fd / 2 - 0.01, zc + hh + 0.24, 0.11, K["brassf"], lobes=4, thick=0.012)
    for sx in (-1, 1):
        sphere(f"Finial{sx}", 0.06, (sx * hw, yf, zc + hh + fw / 2 + 0.05), K["brassf"], seg=10, rings=5)
    # blackened-iron feet: pointed arches standing on the marble
    for sx in (-1, 1):
        x = sx * 1.1
        tube(f"Foot{sx}", [(x - 0.25, yb - 0.25, top), (x - 0.25, yb, top + 0.25), (x, yb, top + 0.5), (x + 0.25, yb, top + 0.25), (x + 0.25, yb - 0.25, top)], 0.03,
             K["iron"], square=True)
        tube(f"FootBack{sx}", [(x, yb, top + 0.5), (x, yb + 0.3, top)], 0.025, K["iron"], square=True, poly=True)
        box(f"FootPlate{sx}", (0.65, 0.5, 0.03), (x, yb - 0.05, top + 0.015), K["iron"], bevel=0.008)
    # the screen
    set_group("Glow")
    B30.plate("Screen", "K9_TV_Screen", pw - 0.08, ph - 0.08, 0.01, T(0, yb - pt / 2 - 0.006, zc), K["p9"], edge="K9_screen", k=3.0)
    set_group("Main")
    # the console: a slim black slab with a chamfered front, a crimson light along it
    s = _mark()
    B20.tprism("Console", [(-0.62, 0.0), (0.62, 0.0), (0.62, 0.1), (0.55, 0.14), (-0.55, 0.14), (-0.62, 0.1)], 0.0, 0.9, plain("ConsoleBlack", (0.015, 0.015, 0.018), 0.3),
               plane="XZ")
    box("ConsoleTopInlay", (1.0, 0.7, 0.006), (0, 0.0, 0.142), plain("ConsoleGloss", (0.03, 0.03, 0.035), 0.08), bevel=0.0)
    for k in range(5):
        box(f"Vent{k}", (0.03, 0.5, 0.004), (0.3 + k * 0.05, 0.0, 0.146), K["ink"], bevel=0.0)
    set_group("Glow")
    box("ConsoleLight", (0.9, 0.015, 0.012), (0, -0.452, 0.07), plain("CrimsonLight", (0.5, 0.02, 0.04), 0.3), bevel=0.0)
    set_group("Main")
    _xform(s, T(-0.8, 0.0, 0.45))
    # the controller: black, crimson accents
    s = _mark()
    body = plain("PadBlack", (0.018, 0.018, 0.02), 0.35)
    accent = K["enamel"]
    rbox("Pad", 0.26, 0.11, 0.1, 0.02, 0.09, body)
    for sx in (-1, 1):
        sphere(f"Grip{sx}", 0.11, (sx * 0.24, 0.1, 0.06), body, seg=16, rings=8, scale=(0.9, 1.6, 0.6))
        cyl(f"Stick{sx}", 0.045, 0.04, (sx * 0.1, 0.06, 0.1), body, verts=16, bevel=0.01)
        hoop(f"StickRing{sx}", (sx * 0.1, 0.06, 0.1), 0.05, "Z", accent, thick=0.006)
        box(f"Shoulder{sx}", (0.14, 0.05, 0.03), (sx * 0.2, -0.11, 0.08), accent, bevel=0.01)
    box("CrossA", (0.1, 0.03, 0.02), (-0.17, -0.03, 0.095), K["ink"], bevel=0.005)
    box("CrossB", (0.03, 0.1, 0.02), (-0.17, -0.03, 0.095), K["ink"], bevel=0.005)
    for k, (x, y) in enumerate(((0.17, 0.0), (0.21, -0.04), (0.17, -0.08), (0.13, -0.04))):
        cyl(f"PadButton{k}", 0.018, 0.025, (x, y, 0.095), accent, verts=10, bevel=0.004)
    _xform(s, T(0.7, -1.35, 0.0) @ RZ(-18 * DEG))
    return _dims()


_base_preview_39 = P.preview


def _preview_39(objs, name, dims, suffix=""):
    """TVConsole's Glow piece is a printed screen: preview it lit with its own colour (the shared preview paints every Glow piece
    candle orange)."""
    if name != "TVConsole":
        return _base_preview_39(objs, name, dims, suffix)
    for ob in objs:
        if ob.name.endswith("_Glow"):
            ob.name = ob.name[:-5] + "_Screen"
            for m in ob.data.materials:
                nt = m.node_tree
                bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
                src = bs.inputs["Base Color"].links[0].from_socket if bs.inputs["Base Color"].links else None
                if src is not None:
                    nt.links.new(src, bs.inputs["Emission Color"])
                    bs.inputs["Emission Strength"].default_value = 2.5
    _base_preview_39(objs, name, dims, suffix)
    for ob in objs:
        if ob.name.endswith("_Screen"):
            ob.name = ob.name[:-7] + "_Glow"


P.preview = _preview_39


def sneaker(prefix, upper, accent, mtx, K):
    """A sneaker (invented: a quatrefoil on its side), toe toward -Y, sole on z = 0."""
    s = _mark()
    sole = flat("SneakerSole", (0.72, 0.69, 0.62), 0.6)
    rbox(f"{prefix}Sole", 0.17, 0.46, 0.15, 0.0, 0.08, sole)
    sphere(f"{prefix}Upper", 0.2, (0, 0.05, 0.13), upper, seg=16, rings=8, scale=(0.82, 2.1, 0.75))
    sphere(f"{prefix}Toe", 0.14, (0, -0.3, 0.09), upper, seg=14, rings=7, scale=(1.1, 1.1, 0.55))
    cyl(f"{prefix}Collar", 0.11, 0.04, (0, 0.22, 0.27), K["ink"], verts=16, bevel=0.01)
    P.PARTS[-1].scale = (1, 1.3, 1)
    box(f"{prefix}Tongue", (0.12, 0.2, 0.03), (0, 0.05, 0.28), upper, bevel=0.012, rot=(0.5, 0, 0))
    for k in range(4):
        tube(f"{prefix}Lace{k}", [(-0.08, -0.12 + k * 0.07, 0.24 + k * 0.015), (0.08, -0.12 + k * 0.07, 0.24 + k * 0.015)], 0.008, accent if k % 2 else sole, poly=True)
    for sx in (-1, 1):
        B20.tprism(f"{prefix}Foil{sx}", WS.foil_outline(0.08, 0.15, 0.06, lobes=4, n=32), sx * 0.165, 0.01, accent, plane="YZ")
    box(f"{prefix}Tab", (0.06, 0.03, 0.1), (0, 0.45, 0.2), accent, bevel=0.01)
    _xform(s, mtx)


def sneaker_pile(M):
    """A heap of five sneakers, invented designs (crimson, black, bone, ink blue, moss), kicked off in a pile."""
    K = kit(M)
    ups = [plain("UpCrimson", (0.17, 0.012, 0.022), 0.6), plain("UpBlack", (0.02, 0.02, 0.022), 0.6), plain("UpBone", (0.55, 0.52, 0.44), 0.6),
           plain("UpInk", (0.03, 0.05, 0.14), 0.6), plain("UpMoss", (0.08, 0.12, 0.05), 0.6)]
    acc = [K["gilt"], K["enamel"], plain("AccInk", (0.02, 0.02, 0.03), 0.4), plain("AccBone", (0.6, 0.56, 0.48), 0.5), K["enamel"]]
    poses = [T(-0.3, 0.1, 0.0) @ RZ(20 * DEG), T(0.35, -0.15, 0.0) @ RZ(-60 * DEG), T(0.0, 0.0, 0.33) @ RZ(80 * DEG) @ RY(12 * DEG),
             T(-0.6, -0.5, 0.17) @ RZ(140 * DEG) @ RY(90 * DEG), T(0.5, 0.5, 0.15) @ RZ(-150 * DEG) @ RY(-80 * DEG) @ RX(10 * DEG)]
    for k, m in enumerate(poses):
        sneaker(f"S{k}", ups[k], acc[k], m, K)
    _fine(0.5)
    return _dims()


def door_hoop(M):
    """A mini basketball hoop that hooks over a door (the backboard's back on the door face at y = 0, the hooks' bend at 5.6 for a door 8
    tall, set it so the hooks sit on the door top): a printed backboard, a crimson rim, a net, a small ball on the floor."""
    K = kit(M)
    bw, bh = 1.8, 1.2
    zc = 4.6
    B30.plate("Board", "K9_Backboard", bw, bh, 0.06, T(0, -0.04, zc), K["p9"], edge="K9_bone", k=2.5)
    for sx in (-1, 1):
        x = sx * 0.55
        tube(f"Hook{sx}", [(x, -0.02, zc - 0.3), (x, -0.02, zc + bh / 2 + 0.4), (x, 0.08, zc + bh / 2 + 0.5), (x, 0.32, zc + bh / 2 + 0.5), (x, 0.34, zc + bh / 2 + 0.2)],
             0.025, K["iron"], square=True, poly=True)
        cyl(f"Pad{sx}", 0.06, 0.04, (x, -0.0, zc - 0.5), K["rubber"], rot=(math.pi / 2, 0, 0), verts=12, bevel=0.01)
    box("Bracket", (0.4, 0.3, 0.06), (0, -0.2, zc - 0.32), K["iron"], bevel=0.01)
    rim_c = (0, -0.6, zc - 0.32)
    hoop("Rim", rim_c, 0.32, "Z", K["enamel"], thick=0.025)
    net = flat("Net", (0.75, 0.72, 0.66), 0.8)
    n = 12
    for k in range(n):
        a0, a1 = k / n * 6.283, (k + 0.5) / n * 6.283
        a2 = (k + 1) / n * 6.283
        p0 = (rim_c[0] + math.cos(a0) * 0.32, rim_c[1] + math.sin(a0) * 0.32, rim_c[2])
        p1 = (rim_c[0] + math.cos(a1) * 0.25, rim_c[1] + math.sin(a1) * 0.25, rim_c[2] - 0.25)
        p2 = (rim_c[0] + math.cos(a2) * 0.32, rim_c[1] + math.sin(a2) * 0.32, rim_c[2])
        p3 = (rim_c[0] + math.cos(a0) * 0.2, rim_c[1] + math.sin(a0) * 0.2, rim_c[2] - 0.5)
        tube(f"NetA{k}", [p0, p1, p3], 0.006, net, poly=True)
        tube(f"NetB{k}", [p2, p1], 0.006, net, poly=True)
    hoop("NetLow", (rim_c[0], rim_c[1], rim_c[2] - 0.5), 0.2, "Z", net, thick=0.006)
    # the ball, on the floor
    ball = material("MiniBall", "NH_Leather", tint=(0.36, 0.1, 0.03), scale=8.0, normal=0.6, wear=0.1)
    sphere("Ball", 0.22, (0.35, -0.75, 0.22), ball, seg=20, rings=12)
    seam = flat("Seam", (0.02, 0.015, 0.012), 0.6)
    hoop("SeamA", (0.35, -0.75, 0.22), 0.222, "X", seam, thick=0.006)
    hoop("SeamB", (0.35, -0.75, 0.22), 0.222, "Z", seam, thick=0.006)
    hoop("SeamC", (0.35, -0.75, 0.22), 0.222, "Y", seam, thick=0.006)
    return _dims()


# ================================================================== boys' bathroom

def urinal_shell(name, mat, z0, z1, lip, rx=0.75, ry=0.85, open_top=None):
    """A wall-hung urinal bowl: a half-round shell (back at y = 0) from z0 to z1, its front cut open from the lip up (a smooth-edged
    opening: every row's vertices are spread so two of them sit on the opening's edges); given thickness inward."""
    open_top = open_top or z1 - 0.45
    zs = sorted(set([round(z0 + (z1 - z0) * j / 20, 4) for j in range(21)] + [lip, open_top]))
    k1, k2 = 9, 10            # segments either side of the opening, segments across it

    def half(z):
        t = min(1.0, max(0.0, (z - lip) / (open_top - lip)))
        return math.radians(62 - 30 * t * t)

    bm = bmesh.new()
    rows = []
    for z in zs:
        t = (z - z0) / (z1 - z0)
        sx = rx * (0.75 + 0.25 * math.sin(min(1.0, t * 1.6) * math.pi / 2)) * (1 - 0.15 * t)
        sy = ry * (0.55 + 0.45 * math.sin(min(1.0, t * 2.0) * math.pi / 2)) * (1 - 0.35 * t ** 2)
        h = half(z)
        a0, a1 = math.pi / 2 - h, math.pi / 2 + h
        angs = [a0 * i / k1 for i in range(k1)] + [a0 + (a1 - a0) * i / k2 for i in range(k2)] + [a1 + (math.pi - a1) * i / k1 for i in range(k1 + 1)]
        rows.append([bm.verts.new((math.cos(a) * sx, -math.sin(a) * sy, z)) for a in angs])
    na = len(rows[0]) - 1
    for j in range(len(zs) - 1):
        zc = (zs[j] + zs[j + 1]) / 2
        for i in range(na):
            if lip < zc < open_top and k1 <= i < k1 + k2:
                continue
            f = bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
            f.smooth = True
    c0 = bm.verts.new((0, 0, z0))
    for i in range(na):
        bm.faces.new((rows[0][i + 1], rows[0][i], c0))
    c1 = bm.verts.new((0, 0, z1))
    for i in range(na):
        bm.faces.new((rows[-1][i], rows[-1][i + 1], c1))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        c = f.calc_center_median()
        out = Vector((c.x, c.y, 0))
        if out.length > 1e-4 and f.normal.dot(out) < 0 and abs(f.normal.z) < 0.9:
            f.normal_flip()
    ob = B34.mesh_obj(name, bm, mat)
    _solid(ob, 0.05)
    ob.modifiers["Solid"].offset = -1
    return ob


def urinal(M):
    """A wall-hung porcelain urinal (pivot on the wall plane at floor level; the lip at 2.0, the bowl's top 3.4) on a black marble back
    panel: a grated drain with its trap going back into the wall, a brass flush pipe up to a push valve (4.3) that runs into the wall."""
    K = kit(M)
    por = porcelain()
    br = K["brassf"]
    slab = marble("MarbleBlack", base=(0.03, 0.028, 0.034), vein=(0.4, 0.38, 0.33), scale=0.9, width=0.03, distortion=6.0, detail=2.5)
    box("Panel", (1.7, 0.06, 3.9), (0, -0.03, 1.0 + 1.95), slab, bevel=0.02)
    box("PanelCap", (1.8, 0.1, 0.08), (0, -0.05, 4.94), br, bevel=0.015)
    urinal_shell("Bowl", por, 1.3, 3.4, 2.0)
    box("BackPlate", (1.4, 0.04, 2.0), (0, -0.08, 2.35), por, bevel=0.015)
    cyl("Drain", 0.12, 0.012, (0, -0.35, 1.52), br, verts=18, bevel=0.0)
    for k in range(4):
        box(f"DrainSlot{k}", (0.16, 0.015, 0.004), (0, -0.4 + k * 0.035, 1.528), K["ink"], bevel=0.0)
    # the trap under the bowl, turning back into the wall
    tube("Trap", [(0, -0.35, 1.3), (0, -0.35, 1.05), (0, -0.25, 0.9), (0, -0.12, 0.92), (0, -0.0, 0.95)], 0.06, br)
    cyl("TrapRose", 0.12, 0.03, (0, -0.015, 0.95), br, rot=(math.pi / 2, 0, 0), verts=16, bevel=0.008)
    # the flush pipe and push valve, the supply going into the wall
    tube("Spud", [(0, -0.3, 3.38), (0, -0.3, 3.7), (0, -0.14, 3.85), (0, -0.14, 4.1)], 0.04, br)
    cyl("ValveBody", 0.12, 0.4, (0, -0.14, 4.3), br, verts=18, bevel=0.02)
    cyl("Button", 0.07, 0.08, (0, -0.28, 4.35), br, rot=(math.pi / 2, 0, 0), verts=16, bevel=0.015)
    cyl("ButtonCap", 0.05, 0.02, (0, -0.33, 4.35), por, rot=(math.pi / 2, 0, 0), verts=14, bevel=0.005)
    tube("Supply", [(0, -0.14, 4.5), (0, -0.14, 4.6), (0, -0.04, 4.65)], 0.035, br)
    cyl("WallRose", 0.1, 0.03, (0, -0.075, 4.65), br, rot=(math.pi / 2, 0, 0), verts=16, bevel=0.008)
    for sx in (-1, 1):
        sphere(f"Bolt{sx}", 0.04, (sx * 0.6, -0.1, 3.2), br, seg=8, rings=4, scale=(1, 0.6, 1))
        for z in (1.15, 4.75):
            sphere(f"PanelBolt{sx}{z}", 0.035, (sx * 0.72, -0.065, z), br, seg=8, rings=4, scale=(1, 0.5, 1))
    return _dims()


def urinal_divider(M):
    """A black marble privacy screen between urinals (0.1 thick, 2.2 out from the wall, from 1.2 to 4.4), held by brass brackets; origin on
    the wall plane at floor level."""
    K = kit(M)
    slab = marble("MarbleBlack", base=(0.03, 0.028, 0.034), vein=(0.4, 0.38, 0.33), scale=0.9, width=0.03, distortion=6.0, detail=2.5)
    br = K["brassf"]
    d, z0, z1 = 2.2, 1.2, 4.4
    prof = [(0.0, z0), (-d + 0.3, z0), (-d + 0.1, z0 + 0.1), (-d, z0 + 0.35), (-d, z1 - 0.6), (-d + 0.2, z1 - 0.25), (-d + 0.6, z1), (0.0, z1)]
    B20.tprism("Screen", prof, 0.0, 0.1, slab, plane="YZ")
    tube("EdgeBead", [(0.06, y, z) for y, z in prof[1:-1]], 0.015, br, poly=True)
    tube("EdgeBead2", [(-0.06, y, z) for y, z in prof[1:-1]], 0.015, br, poly=True)
    for z in (z0 + 0.4, z1 - 0.4):
        for sx in (-1, 1):
            box(f"Bracket{z}{sx}", (0.04, 0.3, 0.25), (sx * 0.07, -0.15, z), br, bevel=0.01)
            sphere(f"Bolt{z}{sx}", 0.025, (sx * 0.095, -0.2, z), br, seg=8, rings=4)
        box(f"WallPlate{z}", (0.3, 0.03, 0.3), (0, -0.015, z), br, bevel=0.01)
    tube("Post", [(0, -d + 0.15, 0.0), (0, -d + 0.15, z0)], 0.035, br, poly=True)
    cyl("PostFoot", 0.08, 0.04, (0, -d + 0.15, 0.02), br, verts=14, bevel=0.01)
    return _dims()


def urinal_trough(M):
    """An old-school floor-standing trough urinal (6.0 wide; the lip at 2.0) on a marble step, a tiled splash-back 5.6 tall, a perforated
    brass flush pipe along its top, a grated drain at one end; origin at the back, on the wall plane, floor level."""
    K = kit(M)
    por = porcelain()
    br = K["brassf"]
    W, D = 6.0, 1.3
    step = marble("TroughMarble", base=(0.03, 0.028, 0.034), vein=(0.4, 0.38, 0.33), scale=0.9, width=0.03, distortion=6.0, detail=2.5)
    box("Step", (W + 0.4, 2.6, 0.3), (0, -1.3, 0.15), step, bevel=0.03)
    # the trough: a porcelain body, its basin sunk into the top, sloping to the drain at the right
    yb = -0.15
    box("Body", (W, D, 1.4), (0, yb - D / 2, 0.3 + 0.7), por, bevel=0.06)
    box("Front", (W, 0.2, 0.3), (0, yb - D + 0.1, 1.85), por, bevel=0.08)
    box("BackWall", (W, 0.2, 0.3), (0, yb - 0.1, 1.85), por, bevel=0.05)
    for sx in (-1, 1):
        box(f"End{sx}", (0.2, D, 0.3), (sx * (W / 2 - 0.1), yb - D / 2, 1.85), por, bevel=0.06)
    box("Basin", (W - 0.4, D - 0.4, 0.04), (0, yb - D / 2, 1.72), flat("PorcelainIn", (0.74, 0.72, 0.66), 0.08, dirt=0.6), bevel=0.0, rot=(0, 0.015, 0))
    cyl("Drain", 0.12, 0.012, (W / 2 - 0.45, yb - D / 2, 1.69), br, verts=18, bevel=0.0)
    for k in range(4):
        box(f"DrainSlot{k}", (0.16, 0.015, 0.004), (W / 2 - 0.45, yb - D / 2 - 0.05 + k * 0.035, 1.697), K["ink"], bevel=0.0)
    # the splash-back, tiled, capped with marble
    B34.pbox("Splash", (W, 0.15, 3.6), (0, -0.075, 2.0 + 1.8), K["p9"], {"front": "K9_Tiles_Wall", "else": "sw:K9_grout"}, k=2.2)
    box("SplashCap", (W + 0.1, 0.2, 0.1), (0, -0.1, 5.65), step, bevel=0.02)
    for sx in (-1, 1):
        box(f"SplashSide{sx}", (0.1, 0.2, 3.6), (sx * (W / 2 + 0.05), -0.1, 3.8), step, bevel=0.02)
    # the flush pipe: from a cistern valve down to a perforated spreader along the top of the trough's back
    tube("Spreader", [(-W / 2 + 0.3, -0.3, 2.3), (W / 2 - 0.3, -0.3, 2.3)], 0.04, br, poly=True)
    for k in range(18):
        x = -W / 2 + 0.45 + k * (W - 0.9) / 17
        cyl(f"Hole{k}", 0.012, 0.01, (x, -0.34, 2.28), K["ink"], rot=(math.pi / 2, 0, 0), verts=6, bevel=0.0)
    for sx in (-1, 1):
        box(f"PipeClip{sx}", (0.1, 0.2, 0.08), (sx * 2.0, -0.2, 2.3), br, bevel=0.01)
    tube("Downpipe", [(0, -0.3, 2.3), (0, -0.3, 4.9), (0, -0.2, 5.1)], 0.04, br)
    cyl("Valve", 0.13, 0.4, (0, -0.3, 4.4), br, verts=18, bevel=0.02)
    cyl("Push", 0.07, 0.08, (0, -0.45, 4.45), br, rot=(math.pi / 2, 0, 0), verts=16, bevel=0.015)
    cyl("PushCap", 0.05, 0.02, (0, -0.5, 4.45), por, rot=(math.pi / 2, 0, 0), verts=14, bevel=0.005)
    return _dims()


# ------------------------------------------------------------------ registration

BUILDERS = {
    "BunkBed": bunk_bed,
    "Nightstand": nightstand,
    "FloorMirror": floor_mirror,
    "LaundryHamper": laundry_hamper,
    "WashingMachine": washing_machine,
    "ShowerStall": shower_stall,
    "MiniFridge": mini_fridge,
    "BeanBag": bean_bag,
    "PingPongTable": ping_pong_table,
    "RADesk": ra_desk,
    "VanityTable": vanity_table,
    "MakeupSet": makeup_set,
    "JewelryBox": jewelry_box,
    "PerfumeTray": perfume_tray,
    "ShoeRack": shoe_rack,
    "FairyLights": fairy_lights,
    "WeightBench": weight_bench,
    "Dumbbells": dumbbells,
    "GuitarStand": guitar_stand,
    "TVConsole": tv_console,
    "SneakerPile": sneaker_pile,
    "DoorHoop": door_hoop,
    "Urinal": urinal,
    "UrinalDivider": urinal_divider,
    "UrinalTrough": urinal_trough,
}
P.BUILD.update(BUILDERS)
P.PREVIEW_PAD.update({n: 1.08 for n in BUILDERS})
P.PREVIEW_PAD.update({"FairyLights": 1.2, "DoorHoop": 1.15})
B24.SMALL.update({"MakeupSet": 1.4, "JewelryBox": 1.5, "PerfumeTray": 1.5, "SneakerPile": 1.3})
