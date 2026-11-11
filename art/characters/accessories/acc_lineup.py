"""Body-type lineups: one baked accessory on all 12 R6 bodies (each with its depth fit), for the owner's review.

E:/Blender/blender.exe -b --factory-startup -P acc_lineup.py -- <Item>[:<Piece>,...] [--root E:/NH-Work/acc] [--view front34]
Opens <root>/blend/<Item>.blend (the baked build), puts the mannequin of each body type under it, scales the piece's
depth by that body's fit (layout fit_body, as UI.AccessoryWear does) and renders <root>/renders/lineup_<Item>[_<Piece>].png
(12 tiles, labelled).
"""
import bpy, json, os, sys
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ROOT = argv[argv.index("--root") + 1] if "--root" in argv else "E:/NH-Work/acc"
VIEW = argv[argv.index("--view") + 1] if "--view" in argv else "front34"
spec = argv[0]
item, _, only = spec.partition(":")
only = only.split(",") if only else None
sys.argv = [sys.argv[0], "--", "--out", ROOT]
import nh_acc as A   # noqa: E402

bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "blend", f"{item}.blend"))
lay = json.load(open(os.path.join(ROOT, "layout", f"{item}.json")))
pieces = {n: bpy.data.objects[n] for n in lay["pieces"] if n in bpy.data.objects}
for n, ob in pieces.items():
    show = only is None or n in only
    ob.hide_render = not show
    if ob.parent is not None:
        ob.parent.hide_render = not show
A._bodies.clear()
cam = A.stage()
sc = bpy.context.scene
sc.cycles.samples = 48
tiles = []
tag = f"_{'_'.join(only)}" if only else ""
for bid in A.BODY_IDS:
    saved = []
    for n, ob in pieces.items():
        e = lay["pieces"][n]
        s = e.get("fit_body", {}).get(bid, 1.0) if bid != "standard" else 1.0
        tgt = ob.parent if ob.parent is not None else ob
        saved.append((tgt, tgt.matrix_world.copy()))
        c = A.MOUNT_CENTRE[e["mount"]]
        tgt.matrix_world = Matrix.Translation(c) @ Matrix.Diagonal((1, s, 1, 1)) @ Matrix.Translation(-c) @ tgt.matrix_world
    man = A.mannequin(bid)
    path = os.path.join(ROOT, "tmp", f"lu_{item}{tag}_{bid}.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    A.shoot(cam, path, VIEW, target=(0, 0, -0.3), lens=55, res=340, aspect=1.25)
    tiles.append((bid, path))
    for o in man:
        bpy.data.objects.remove(o)
    for t, mw in saved:
        t.matrix_world = mw
json.dump(tiles, open(os.path.join(ROOT, "tmp", f"lu_{item}{tag}.json"), "w"))
print("LINEUP", item, tag, len(tiles))
