"""Pack an animpro DATA block compactly for Studio: 'tms|T:qx,qy,qz,qw[,x,y,z];H:...' with ints (x1000).
usage: python pack.py out/GripVampire  -> prints the Luau call for ServerStorage.NH_GripAnims.Builder"""
import re
import sys

CODE = {"Torso": "T", "Head": "H", "Left Arm": "LA", "Right Arm": "RA", "Left Leg": "LL", "Right Leg": "RL"}


def pack(base):
    src = open(base + ".lua").read()
    data = re.search(r"local DATA = \[==\[\n(.*?)\]==\]", src, re.S).group(1)
    markers = re.search(r"local MARKERS = (\{.*?\})\n", src).group(1)
    name = re.search(r'seq.Name = "([^"]+)"', src).group(1)
    out = []
    for line in data.strip().splitlines():
        t, _, rest = line.partition(";")
        parts = []
        for part, vals in re.findall(r"([^=;]+)=([^;]+)", rest):
            n = [int(round(float(v) * 1000)) for v in vals.split(",")]
            while len(n) > 4 and n[-1] == 0:
                n.pop()
            parts.append(CODE[part] + ":" + ",".join(str(x) for x in n))
        out.append(str(int(round(float(t) * 1000))) + "|" + ";".join(parts))
    return f'return require(game.ServerStorage.NH_GripAnims.Builder).BuildPacked("{name}", [==[\n' + "\n".join(out) + f"\n]==], {markers})"


if __name__ == "__main__":
    print(pack(sys.argv[1]))
