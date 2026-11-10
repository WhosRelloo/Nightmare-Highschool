"""R6 CharacterMesh clothing atlas (1024 x 512) used by Roblox for meshed R6 body parts.

Measured on 2026-11-10 from Roblox's own package meshes (Girl torso 48112070, Woman, Robloxian 2.0, ROBLOX Boy/Girl).
Roblox composites the Shirt / Pants templates into this atlas; a CharacterMesh's UVs must index it.

Layout (pixels, x = U * 1024, y = V * 512, V measured downward as stored in Roblox meshes):
- each part's four sides are one strip; height runs along +x (bottom of the part at the low x), sides stack along y
- caps (top "U" / bottom "D") sit in a row at y 328..392 (and one at y 400..464), 8 px apart

Run with plain Python 3 + Pillow to write atlas_check.png (labelled regions) next to this file.
"""
import os

STRIP_H = 128          # 2 studs of height
FACE_1 = 64            # 1 stud
U_PER_STUD = 64 / 1024
V_PER_STUD = 64 / 512

# x range of each strip (bottom..top of the part) and the side order down the strip (y in studs from 0)
STRIPS = {
    "Torso":    {"x": (32, 160),  "faces": [("R", 0, 1), ("F", 1, 3), ("L", 3, 4), ("B", 4, 6)]},
    "RightArm": {"x": (232, 360), "faces": [("B", 1, 2), ("R", 2, 3), ("F", 3, 4), ("L", 4, 5)]},
    "LeftArm":  {"x": (432, 560), "faces": [("R", 0, 1), ("F", 1, 2), ("L", 2, 3), ("B", 3, 4)]},
    "RightLeg": {"x": (632, 760), "faces": [("B", 1, 2), ("R", 2, 3), ("F", 3, 4), ("L", 4, 5)]},
    "LeftLeg":  {"x": (832, 960), "faces": [("R", 0, 1), ("F", 1, 2), ("L", 2, 3), ("B", 3, 4)]},
}
# caps: (x0, x1, y0, y1)
CAPS = {
    ("Torso", "U"): (200, 328, 328, 392), ("Torso", "D"): (336, 464, 328, 392),
    ("RightLeg", "U"): (472, 536, 328, 392), ("LeftLeg", "U"): (544, 608, 328, 392),
    ("RightLeg", "D"): (616, 680, 328, 392), ("LeftLeg", "D"): (688, 752, 328, 392),
    ("RightArm", "D"): (760, 824, 328, 392), ("LeftArm", "D"): (832, 896, 328, 392),
    ("RightArm", "U"): (904, 968, 328, 392), ("LeftArm", "U"): (200, 264, 400, 464),
}


def strip_uv(part):
    """(u_centre, u_half) of the part's side strip, plus {face: (v0, v1)} in traversal order
    +x(R) -> front(F) -> -x(L) -> back(B), which is how nh_female_body.py walks each ring."""
    s = STRIPS[part]
    x0, x1 = s["x"]
    faces = {f: (a * V_PER_STUD, b * V_PER_STUD) for f, a, b in s["faces"]}
    return (x0 + x1) / 2 / 1024, (x1 - x0) / 2 / 1024, faces


def cap_uv(part, which):
    x0, x1, y0, y1 = CAPS[(part, which)]
    return (x0 + x1) / 2 / 1024, (y0 + y1) / 2 / 512, (x1 - x0) / 2 / 1024, (y1 - y0) / 2 / 512


if __name__ == "__main__":
    from PIL import Image, ImageDraw, ImageFont

    W, H = 2048, 1024        # drawn at 2x for sharp labels
    k = 2
    img = Image.new("RGB", (W, H), (40, 40, 46))
    d = ImageDraw.Draw(img)
    cols = {"F": (205, 60, 60), "B": (60, 90, 200), "R": (60, 170, 80), "L": (210, 170, 40),
            "U": (180, 90, 200), "D": (90, 190, 200)}
    short = {"Torso": "T", "RightArm": "RA", "LeftArm": "LA", "RightLeg": "RL", "LeftLeg": "LL"}
    try:
        font = ImageFont.truetype("arialbd.ttf", 34)
    except OSError:
        font = ImageFont.load_default()

    def label(box, text, rotate):
        x0, y0, x1, y1 = box
        t = Image.new("RGBA", (220, 60), (0, 0, 0, 0))
        ImageDraw.Draw(t).text((110, 30), text, fill=(255, 255, 255), font=font, anchor="mm")
        if rotate:
            t = t.rotate(-90, expand=True)   # text top points to +x = up the body
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
        img.paste(t, (cx - t.width // 2, cy - t.height // 2), t)

    for part, s in STRIPS.items():
        x0, x1 = s["x"]
        for f, a, b in s["faces"]:
            box = (x0 * k, a * 64 * k, x1 * k, b * 64 * k)
            d.rectangle(box, fill=cols[f], outline=(20, 20, 20), width=3)
            # an arrow along +x (towards the top of the part)
            my = (box[1] + box[3]) // 2
            d.line((box[0] + 20, my + 40, box[2] - 30, my + 40), fill=(255, 255, 255), width=4)
            d.polygon([(box[2] - 30, my + 30), (box[2] - 10, my + 40), (box[2] - 30, my + 50)], fill=(255, 255, 255))
            label(box, f"{short[part]}-{f}", True)
    for (part, f), (x0, x1, y0, y1) in CAPS.items():
        box = (x0 * k, y0 * k, x1 * k, y1 * k)
        d.rectangle(box, fill=cols[f], outline=(20, 20, 20), width=3)
        label(box, f"{short[part]}{f}", False)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "atlas_check.png")
    img.save(out)
    print("wrote", out)
