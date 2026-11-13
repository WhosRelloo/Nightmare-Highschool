"""Print a small Luau payload with full poses of a baked pair at chosen times (for Studio previews/screenshots).
usage: python snap.py out/GripVampire t1 t2 ...   (reads <base>.lua and <base>Victim.lua)"""
import re
import sys

import numpy as np


def tracks_of(lua_path):
    src = open(lua_path).read()
    data = re.search(r"local DATA = \[==\[\n(.*?)\]==\]", src, re.S).group(1)
    tr = {}
    for line in data.strip().splitlines():
        t, _, rest = line.partition(";")
        t = float(t)
        for part, vals in re.findall(r"([^=;]+)=([^;]+)", rest):
            n = [float(v) for v in vals.split(",")]
            n += [0.0] * (7 - len(n))
            tr.setdefault(part, []).append((t, np.array(n)))
    return tr


def sample(l, t):
    if t <= l[0][0]:
        return l[0][1]
    for (t0, a), (t1, b) in zip(l, l[1:]):
        if t <= t1:
            k = (t - t0) / max(1e-6, t1 - t0)
            if np.dot(a[:4], b[:4]) < 0:
                b = b.copy()
                b[:4] *= -1
            v = a + (b - a) * k
            v[:4] /= np.linalg.norm(v[:4])
            return v
    return l[-1][1]


def payload(base, times):
    out = []
    for suffix, tag in (("", "A"), ("Victim", "V")):
        tr = tracks_of(base + suffix + ".lua")
        lines = []
        for t in times:
            parts = ";".join(f"{p}=" + ",".join(f"{x:.4f}" for x in sample(l, t)) for p, l in tr.items())
            lines.append(f"{t};{parts}")
        out.append(f'_G.NHGrip.Load("{tag}", [==[\n' + "\n".join(lines) + "\n]==])")
    return "\n".join(out)


if __name__ == "__main__":
    print(payload(sys.argv[1], [float(x) for x in sys.argv[2:]]))
