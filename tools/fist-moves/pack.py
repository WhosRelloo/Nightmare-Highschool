"""Pack a baked fist clip for Studio (ServerStorage.NH_FistAnims.Builder.BuildPacked).
Same compact format as racial-grips/pack.py ('tms|T:qx,qy,qz,qw[,x,y,z];H:...', ints x1000). Differences:
  * markers named Hit / EndLag also name their keyframe: the game reads them with GetTimeOfKeyframe / KeyframeReached
    (ServerStorage.Packages.AnimMarkers), not as KeyframeMarkers;
  * --to E cuts it at E seconds (a pair's attacker can end before the victim);
  * --from S trims the clip to start at S seconds (the clinch victim starts when they're caught), with every part keyed
    on the new first frame.
usage: python pack.py out/FistShove [--from 0.14] [--name FistClinchVictim]  -> prints the Luau call"""
import json
import os
import re
import sys

FPS = 30
CODE = {"Torso": "T", "Head": "H", "Left Arm": "LA", "Right Arm": "RA", "Left Leg": "LL", "Right Leg": "RL"}


def pack(base, start=0.0, name=None, stop=None):
    src = open(base + ".lua").read()
    data = re.search(r"local DATA = \[==\[\n(.*?)\]==\]", src, re.S).group(1)
    markers = re.search(r"local MARKERS = (\{.*?\})\n", src).group(1)
    name = name or re.search(r'seq.Name = "([^"]+)"', src).group(1)
    # limb slides (fist_poses.bake_offs): every limb gets its Pose position on every frame
    opath = base + ".offs.json"
    offs = json.load(open(opath)) if os.path.exists(opath) else {}
    rows, last = [], {}
    for line in data.strip().splitlines():
        t, _, rest = line.partition(";")
        vals = {part: [float(v) for v in vs.split(",")] for part, vs in re.findall(r"([^=;]+)=([^;]+)", rest)}
        rows.append((float(t), vals))
    out, first = [], True
    for i, (t, vals) in enumerate(rows):
        for p, v in vals.items():
            prev = last.get(p)
            last[p] = v
        if t < start - 1e-6 or (stop is not None and t > stop + 1e-6):
            continue
        use = dict(last) if first else dict(vals)  # the first kept frame carries every part
        first = False
        slide = offs.get(str(int(round(t * FPS))))
        if slide:
            for part, xyz in slide.items():
                use[part] = list(last[part][:4]) + list(xyz)  # the part's current rotation + its slide
        parts = []
        for part, v in use.items():
            n = [int(round(x * 1000)) for x in v]
            while len(n) > 4 and n[-1] == 0:
                n.pop()
            parts.append(CODE[part] + ":" + ",".join(str(x) for x in n))
        out.append(str(int(round((t - start) * 1000))) + "|" + ";".join(parts))
    if start > 0:
        markers = "{}"  # the trimmed victim clip carries no gameplay markers
    return f'return require(game.ServerStorage.NH_FistAnims.Builder).BuildPacked("{name}", [==[\n' + "\n".join(out) + f"\n]==], {markers})"


if __name__ == "__main__":
    args = sys.argv[1:]
    start = float(args[args.index("--from") + 1]) if "--from" in args else 0.0
    name = args[args.index("--name") + 1] if "--name" in args else None
    stop = float(args[args.index("--to") + 1]) if "--to" in args else None
    print(pack(args[0], start, name, stop))
