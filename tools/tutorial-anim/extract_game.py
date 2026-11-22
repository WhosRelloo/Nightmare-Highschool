"""Extract a game animation to game/<leaf>.json through extract_game.luau.

  python -I -X utf8 extract_game.py Default.Movement.CrouchWalk

The path is under ReplicatedStorage.Assets.Animations in NH Combat Test (Edit). The Luau samples the clip at 30 fps on an
R6 dummy (Motor6D.Transform per joint per frame). It runs in 30-frame chunks because rbxc.py truncates a result at
30000 chars (a whole clip is more), and the Luau rounds every number to 6 decimals to keep a chunk inside that limit.
The chunks are merged by time and written as compact JSON {path, length, frames}, which build.py's load_game reads.
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
RBXC = "E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
CHUNK = 30


def extract(path):
    src = open(os.path.join(HERE, "extract_game.luau"), encoding="utf-8").read()
    frames, f, n, length = [], 0, None, None
    with tempfile.TemporaryDirectory() as tmp:
        lua = os.path.join(tmp, "x.luau")
        while n is None or f <= n:
            open(lua, "w", encoding="utf-8").write(
                src.replace("__PATH__", path).replace("__FROM__", str(f)).replace("__TO__", str(f + CHUNK - 1)))
            out = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", "placeId: 98950102230473", "Edit", "@" + lua],
                                 capture_output=True, text=True, encoding="utf-8", check=True).stdout
            d = json.loads(out)
            n, length = d["n"], d["length"]
            frames += d["frames"]
            f += CHUNK
    frames.sort(key=lambda r: r["t"])
    return {"path": path, "length": length, "frames": frames}


if __name__ == "__main__":
    p = sys.argv[1]
    os.makedirs(os.path.join(HERE, "game"), exist_ok=True)
    out = os.path.join(HERE, "game", p.split(".")[-1] + ".json")
    d = extract(p)
    json.dump(d, open(out, "w", encoding="utf-8"), separators=(",", ":"))
    print(p, len(d["frames"]), d["length"], "->", out)
