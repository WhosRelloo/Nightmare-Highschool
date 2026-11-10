"""Lineup renders for the body types: the current body first, then each variant, front / side / back.
Called from nh_body_types.py with --render. Writes renders/<id>_<view>.png and renders/lineup_<gender>.png."""
import bpy, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "female"))
import render_compare as rc   # noqa: E402  (materials, head, boxes, lights, camera)

LIMB_AT = {"Torso": (0, 0), "RightArm": (1.5, 0), "LeftArm": (-1.5, 0), "RightLeg": (0.5, -2), "LeftLeg": (-0.5, -2)}


def figure(parts, ox, skin, label):
    objs = []
    h = rc.head(f"{label}_Head"); rc.place(h, 0, 1.5, ox); objs.append(h)
    for part, (x, y) in LIMB_AT.items():
        if parts is None:   # the standard R6 body: plain blocks
            o = rc.box(f"{label}_{part}", 2 if part == "Torso" else 1, 2, 1)
        else:
            src = parts[part]
            o = src.copy(); o.data = src.data.copy(); bpy.context.scene.collection.objects.link(o)
            o.hide_render = False
        o.name = f"{label}_{part}"
        rc.place(o, x, y, ox); objs.append(o)
    for o in objs:
        o.data.materials.clear(); o.data.materials.append(skin)
    return objs


def run(built, female_now, bodies, out):
    sc, cam = rc.setup_scene()
    skin = rc.mat("Skin", (234, 190, 160))
    for objs in list(built.values()) + [female_now]:
        for o in objs.values():
            o.hide_render = True
    figs = {}
    keys = [("male_now", None), ("female_now", female_now)] + [(b["id"], built[b["id"]]) for b in bodies if b["id"] in built]
    for i, (key, parts) in enumerate(keys):
        figs[key] = (i * 12, figure(parts, i * 12, skin, key))
    for key, (ox, objs) in figs.items():
        for k2, (_, lst) in figs.items():
            for o in lst:
                o.hide_render = k2 != key
        for view in ("front", "side", "back"):
            objs[2].hide_render = view == "side"      # the near (right) arm would hide the torso profile
            rc.shoot(sc, cam, ox, view, os.path.join(out, "renders", f"{key}_{view}.png"))
        objs[2].hide_render = False
    cols = {"male": [["male_now", "Standard", "current"]] + [[b["id"], b["name"], "new"] for b in bodies if b["gender"] == "Male" and b["id"] in built],
            "female": [["female_now", "Female", "current (v2)"]] + [[b["id"], b["name"], "new"] for b in bodies if b["gender"] == "Female" and b["id"] in built]}
    import json
    with open(os.path.join(out, "renders", "lineup_cols.json"), "w") as fh:
        json.dump(cols, fh)
    print("RENDERED", len(figs))
