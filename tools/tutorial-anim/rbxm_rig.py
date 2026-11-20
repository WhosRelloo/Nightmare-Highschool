"""Pull the R6Block / R15Block template rigs out of RoMixamo.rbxm: part CFrames, Motor6D C0/C1/Part0/Part1 -> rigs.json"""
import struct, sys, json, collections
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import rbxm_peek as R

NORM = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (-1, 0, 0), (0, -1, 0), (0, 0, -1)]


def rbxfloat(u):
    u = ((u >> 1) | ((u & 1) << 31)) & 0xFFFFFFFF
    return struct.unpack(">f", struct.pack(">I", u))[0]


def floats(b, n):
    raw = R.deint(b, n, 4)
    return [rbxfloat(struct.unpack_from(">I", raw, i * 4)[0]) for i in range(n)]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def main(path):
    data = open(path, "rb").read()
    classes = {}; names = {}; parent = {}; cf = collections.defaultdict(dict); refp = collections.defaultdict(dict); ic = {}
    for name, body in R.chunks(data):
        if name == "INST":
            cid, = struct.unpack_from("<I", body, 0); ln, = struct.unpack_from("<I", body, 4)
            cname = body[8:8 + ln].decode(); q = 8 + ln + 1
            cnt, = struct.unpack_from("<I", body, q); q += 4
            ids = R.refs(body[q:q + 4 * cnt], cnt)
            classes[cid] = (cname, ids)
            for r in ids: ic[r] = cname
        elif name == "PROP":
            cid, = struct.unpack_from("<I", body, 0); ln, = struct.unpack_from("<I", body, 4)
            pname = body[8:8 + ln].decode(); q = 8 + ln
            t = body[q]; q += 1
            ids = classes[cid][1]; n = len(ids)
            if t == 0x01 and pname == "Name":
                for r in ids:
                    sl, = struct.unpack_from("<I", body, q); q += 4
                    names[r] = body[q:q + sl].decode("utf-8", "replace"); q += sl
            elif t == 0x10:
                rots = []
                for _ in range(n):
                    i = body[q]; q += 1
                    if i == 0:
                        m = struct.unpack_from("<9f", body, q); q += 36
                        rots.append(list(m))
                    else:
                        x = NORM[(i - 1) // 6]; y = NORM[(i - 1) % 6]; z = cross(x, y)
                        rots.append([x[0], y[0], z[0], x[1], y[1], z[1], x[2], y[2], z[2]])
                xs = floats(body[q:q + 4 * n], n); q += 4 * n
                ys = floats(body[q:q + 4 * n], n); q += 4 * n
                zs = floats(body[q:q + 4 * n], n); q += 4 * n
                for k, r in enumerate(ids):
                    cf[r][pname] = [xs[k], ys[k], zs[k]] + rots[k]
            elif t == 0x13:
                vals = R.refs(body[q:q + 4 * n], n)
                for k, r in enumerate(ids):
                    refp[r][pname] = vals[k]
        elif name == "PRNT":
            cnt, = struct.unpack_from("<I", body, 1)
            ch = R.refs(body[5:5 + 4 * cnt], cnt); pa = R.refs(body[5 + 4 * cnt:5 + 8 * cnt], cnt)
            parent.update(zip(ch, pa))

    def full(r):
        parts = []
        while r in names:
            parts.append(names[r]); r = parent.get(r, -1)
        return ".".join(reversed(parts))
    out = {}
    for r, nm in names.items():
        f = full(r)
        for rig in ("R6Block", "R15Block"):
            pre = f"RoMixamo.AvatarTemplate.{rig}."
            if f.startswith(pre):
                d = out.setdefault(rig, {"parts": {}, "motors": {}})
                if ic[r] in ("Part", "MeshPart") and names.get(parent.get(r)) == rig:
                    d["parts"][nm] = cf[r].get("CFrame")
                if ic[r] == "Motor6D":
                    d["motors"][nm] = {"C0": cf[r].get("C0"), "C1": cf[r].get("C1"), "Part0": names.get(refp[r].get("Part0")),
                                       "Part1": names.get(refp[r].get("Part1")), "parent": names.get(parent.get(r))}
    return out


if __name__ == "__main__":
    o = main(sys.argv[1])
    json.dump(o, open("rigs.json", "w"), indent=1)
    for rig, d in o.items():
        print(rig, list(d["parts"]))
        for m, v in d["motors"].items():
            print("  ", m, v["Part0"], "->", v["Part1"], [round(x, 3) for x in v["C0"][:3]], [round(x, 3) for x in v["C1"][:3]])
