"""Read-only peek into a binary .rbxm: classes, instance names, string props, tree. Pure Python (LZ4 block + zstd-free)."""
import struct, sys, collections, json


def lz4_block(src, out_len):
    dst = bytearray()
    i = 0
    n = len(src)
    while i < n:
        tok = src[i]; i += 1
        lit = tok >> 4
        if lit == 15:
            while True:
                b = src[i]; i += 1; lit += b
                if b != 255: break
        dst += src[i:i + lit]; i += lit
        if i >= n: break
        off = src[i] | (src[i + 1] << 8); i += 2
        ml = tok & 15
        if ml == 15:
            while True:
                b = src[i]; i += 1; ml += b
                if b != 255: break
        ml += 4
        st = len(dst) - off
        for k in range(ml):
            dst.append(dst[st + k])
    return bytes(dst)


def chunks(data):
    p = 32
    while p < len(data):
        name = data[p:p + 4].rstrip(b"\0").decode(); clen, ulen = struct.unpack_from("<II", data, p + 4); p += 16
        if clen == 0:
            body = data[p:p + ulen]; p += ulen
        else:
            raw = data[p:p + clen]; p += clen
            if raw[:4] == b"\x28\xb5\x2f\xfd":
                raise SystemExit("zstd chunk; need zstandard")
            body = lz4_block(raw, ulen)
        yield name, body
        if name == "END": break


def deint(b, n, w):
    out = bytearray(n * w)
    for i in range(n):
        for j in range(w):
            out[i * w + j] = b[j * n + i]
    return bytes(out)


def ints(b, n):
    raw = deint(b, n, 4)
    vals = []
    for i in range(n):
        u = struct.unpack_from(">I", raw, i * 4)[0]
        vals.append((u >> 1) ^ -(u & 1))
    return vals


def refs(b, n):
    v = ints(b, n); out = []; acc = 0
    for x in v:
        acc += x; out.append(acc)
    return out


def main(path):
    data = open(path, "rb").read()
    classes = {}; inst_class = {}; names = {}; strprops = collections.defaultdict(dict); parent = {}
    for name, body in chunks(data):
        if name == "INST":
            cid, = struct.unpack_from("<I", body, 0)
            ln, = struct.unpack_from("<I", body, 4)
            cname = body[8:8 + ln].decode(); q = 8 + ln + 1
            cnt, = struct.unpack_from("<I", body, q); q += 4
            ids = refs(body[q:q + 4 * cnt], cnt)
            classes[cid] = (cname, ids)
            for r in ids: inst_class[r] = cname
        elif name == "PROP":
            cid, = struct.unpack_from("<I", body, 0)
            ln, = struct.unpack_from("<I", body, 4)
            pname = body[8:8 + ln].decode(); q = 8 + ln
            t = body[q]; q += 1
            ids = classes[cid][1]
            if t == 0x01:
                for r in ids:
                    sl, = struct.unpack_from("<I", body, q); q += 4
                    s = body[q:q + sl]; q += sl
                    if pname == "Name":
                        names[r] = s.decode("utf-8", "replace")
                    elif pname in ("Source", "AnimationId", "Value", "Text", "Tags", "AttributesSerialize"):
                        strprops[r][pname] = s
        elif name == "PRNT":
            cnt, = struct.unpack_from("<I", body, 1)
            ch = refs(body[5:5 + 4 * cnt], cnt)
            pa = refs(body[5 + 4 * cnt:5 + 8 * cnt], cnt)
            parent.update(zip(ch, pa))
    return classes, inst_class, names, strprops, parent


if __name__ == "__main__":
    path = sys.argv[1]
    classes, ic, names, sp, parent = main(path)
    cc = collections.Counter(ic.values())
    print("classes:", dict(cc.most_common()))
    kids = collections.defaultdict(list)
    for c, p in parent.items(): kids[p].append(c)

    def full(r):
        parts = []
        while r in names:
            parts.append(names[r]); r = parent.get(r, -1)
        return ".".join(reversed(parts))
    mode = sys.argv[2] if len(sys.argv) > 2 else "tree"
    if mode == "tree":
        def walk(r, d):
            if d > int(sys.argv[3] if len(sys.argv) > 3 else 3): return
            ks = kids.get(r, [])
            print("  " * d + f"{ic.get(r)} {names.get(r)!r} ({len(ks)})")
            byc = collections.Counter(ic[k] for k in ks)
            if len(ks) > 25:
                print("  " * (d + 1) + f"... {dict(byc)}; first: " + ", ".join(names.get(k, '?') for k in ks[:25]))
                return
            for k in ks: walk(k, d + 1)
        for r in kids.get(-1, []): walk(r, 0)
    elif mode == "scripts":
        for r, props in sp.items():
            if "Source" in props:
                print(f"== {ic[r]} {full(r)} ({len(props['Source'])} bytes)")
    elif mode == "src":
        for r, props in sp.items():
            if "Source" in props and full(r) == sys.argv[3]:
                sys.stdout.write(props["Source"].decode("utf-8", "replace"))
    elif mode == "class":
        for r, c in ic.items():
            if c == sys.argv[3]:
                print(full(r), {k: v[:200] for k, v in sp.get(r, {}).items()})
