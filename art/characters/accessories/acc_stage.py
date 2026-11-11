"""Stage a batch of accessories for the owner's Studio import (group 15981569).

python acc_stage.py <folder> <Item>[,<Item>...] [--suffix v2] [--root E:/NH-Work/acc]

Copies each item's FBX (fbx/NHAcc_<Item>.fbx) and its maps into art/group-upload-accessories/<folder>/: colour, normal,
roughness, metalness (skipped when the item has no metal at all) and the emissive mask, downsized to 1024 (Roblox
shows SurfaceAppearance maps at 1024 at most). Alpha pieces' own textures (layout "alpha_tex") come too.
--suffix renames the images NHAcc_<Item>_<suffix>_<kind>.png so a re-upload gets new names (the ids are then read by
the new names and mapped back to the logical NHAcc_<Item>_<kind> keys in ids.json). The FBX keeps its name, because
the assembly script finds the import by model name.
"""
import json, os, shutil, sys
from PIL import Image

args = sys.argv[1:]
folder, items = args[0], args[1].split(",")
SUF = args[args.index("--suffix") + 1] if "--suffix" in args else ""
ROOT = args[args.index("--root") + 1] if "--root" in args else "E:/NH-Work/acc"
OUT = os.path.join("E:/Nightmare-Highschool/art/group-upload-accessories", folder)
os.makedirs(OUT, exist_ok=True)
n = 0
for it in items:
    shutil.copy2(os.path.join(ROOT, "fbx", f"NHAcc_{it}.fbx"), OUT)
    n += 1
    for kind in ("color", "normal", "roughness", "metalness", "emissive"):
        src = os.path.join(ROOT, "maps", f"NHAcc_{it}_{kind}.png")
        if not os.path.exists(src):
            continue
        im = Image.open(src)
        if kind == "metalness" and im.convert("L").getextrema()[1] == 0:
            continue
        if kind == "emissive" and im.convert("L").getextrema()[1] == 0:
            continue
        if im.size[0] > 1024:
            im = im.resize((1024, 1024), Image.LANCZOS)
        name = f"NHAcc_{it}_{SUF}_{kind}.png" if SUF else f"NHAcc_{it}_{kind}.png"
        im.save(os.path.join(OUT, name), optimize=True)
        n += 1
    lp = os.path.join(ROOT, "layout", f"{it}.json")
    if os.path.exists(lp):
        for pn, e in json.load(open(lp))["pieces"].items():
            if e.get("alpha_tex"):
                s = os.path.join(ROOT, "maps", e["alpha_tex"])
                if os.path.exists(s):
                    shutil.copy2(s, OUT)
                    n += 1
print("staged", n, "files in", OUT)
