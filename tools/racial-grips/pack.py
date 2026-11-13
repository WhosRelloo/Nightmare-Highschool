"""Pack an animpro DATA block compactly for Studio: 'tms|T:qx,qy,qz,qw[,x,y,z];H:...' with ints (x1000).
usage: python pack.py out/GripVampire  -> prints the Luau call for ServerStorage.NH_GripAnims.Builder"""
import json
import os
import re
import sys

FPS = 30

CODE = {"Torso": "T", "Head": "H", "Left Arm": "LA", "Right Arm": "RA", "Left Leg": "LL", "Right Leg": "RL"}


def pack(base):
    src = open(base + ".lua").read()
    data = re.search(r"local DATA = \[==\[\n(.*?)\]==\]", src, re.S).group(1)
    markers = re.search(r"local MARKERS = (\{.*?\})\n", src).group(1)
    name = re.search(r'seq.Name = "([^"]+)"', src).group(1)
    # tucked kneel legs (pair.py writes <name>.tuck.json): animpro only rotates limbs, so the leg's slide into the
    # torso is added here as the Pose position. A leg whose offset changes is always written (its last rotation).
    tpath = base + ".tuck.json"
    tuck = json.load(open(tpath)) if os.path.exists(tpath) else {}
    out, lastq, lastoff = [], {}, {}
    for line in data.strip().splitlines():
        t, _, rest = line.partition(";")
        f = str(int(round(float(t) * FPS)))
        vals_by = {}
        for part, vals in re.findall(r"([^=;]+)=([^;]+)", rest):
            vals_by[part] = [float(v) for v in vals.split(",")]
            lastq[part] = vals_by[part][:4]
        for part in ("Right Leg", "Left Leg"):
            off = (tuck.get(f) or {}).get(part, [0.0, 0.0, 0.0])
            if part in vals_by or off != lastoff.get(part, [0.0, 0.0, 0.0]):
                q = vals_by[part][:4] if part in vals_by else lastq.get(part, [0.0, 0.0, 0.0, 1.0])
                vals_by[part] = q + list(off)
                lastoff[part] = off
        parts = []
        for part, v in vals_by.items():
            n = [int(round(x * 1000)) for x in v]
            while len(n) > 4 and n[-1] == 0:
                n.pop()
            parts.append(CODE[part] + ":" + ",".join(str(x) for x in n))
        out.append(str(int(round(float(t) * 1000))) + "|" + ";".join(parts))
    return f'return require(game.ServerStorage.NH_GripAnims.Builder).BuildPacked("{name}", [==[\n' + "\n".join(out) + f"\n]==], {markers})"


if __name__ == "__main__":
    print(pack(sys.argv[1]))
