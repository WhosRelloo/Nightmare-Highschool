"""Stage the Quiet Corners, Evidence Wall and dialogue art for the group upload (group 15981569).
Roblox caps images at 1024 px: Book and Wall split into quadrants, anything else over 1024 is downscaled.
usage: cd art/ui/hud && python export_quietcorners_upload.py
Writes art/group-upload-quietcorners/{A,B,C}/<Prefix><Name>.png and upload-manifest.json.
Tiers: A = Human + shared (drawn today), B = the other five races, C = not drawn today (PlateTrim, Cork)."""
import json
from collections import Counter
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
DEST = HERE.parents[1] / "group-upload-quietcorners"
RACES = ["Human", "Priest", "Vampire", "Werewolf", "Ghoul", "Wraith"]
SETS = {"quietcorners": "Qc", "evidence": "Ev", "dialogue": "Dl"}
QUADS = {"Book", "Wall"}
LATER = {"Cork"} | {f"PlateTrim{r}" for r in RACES}
CAP = 1024


def tier(name):
    if name in LATER:
        return "C"
    race = next((r for r in RACES if name.endswith(r)), None)
    return "B" if race and race != "Human" else "A"


def main():
    done = set(json.loads((OUT / "dialogue" / "ids.json").read_text()))
    manifest = []
    for sub, prefix in SETS.items():
        for src in sorted((OUT / sub).glob("*.png")):
            name = src.stem
            if name.startswith("_") or name in done:
                continue
            im = Image.open(src).convert("RGBA")
            if name in QUADS:
                w, h = im.size
                hw, hh = w // 2, h // 2
                pieces = [(name + k, im.crop(b)) for k, b in (("TL", (0, 0, hw, hh)), ("TR", (hw, 0, w, hh)),
                                                              ("BL", (0, hh, hw, h)), ("BR", (hw, hh, w, h)))]
            else:
                pieces = [(name, im)]
            for key, piece in pieces:
                if max(piece.size) > CAP:
                    k = CAP / max(piece.size)
                    piece = piece.resize((round(piece.width * k), round(piece.height * k)), Image.LANCZOS)
                t = tier(name)
                (DEST / t).mkdir(parents=True, exist_ok=True)
                file = f"{prefix}{key}.png"
                piece.save(DEST / t / file, optimize=True)
                manifest.append({"file": file, "tier": t, "key": key, "set": sub, "size": list(piece.size), "source": src.name})
    (DEST / "upload-manifest.json").write_text(json.dumps(manifest, indent=1))
    assert all(max(m["size"]) <= CAP for m in manifest)
    print("staged", len(manifest), dict(sorted(Counter(m["tier"] for m in manifest).items())))


if __name__ == "__main__":
    main()
