"""Load an exported clip (ghoul_eatbody.txt format) as generator keys."""
import os


def load(name):
    keys = []
    for line in open(os.path.join(os.path.dirname(__file__), name)):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        t, *parts = line.split(";")
        k = {"t": round(float(t), 4)}
        for p in parts:
            j, v = p.split("=")
            if j == "Root":
                pos, rot = v.split("|")
                k["Root"] = {"p": [float(x) for x in pos.split(",")], "r": [float(x) for x in rot.split(",")]}
            else:
                k[j] = [float(x) for x in v.split(",")]
        keys.append(k)
    return keys
