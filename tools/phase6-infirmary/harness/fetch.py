"""usage: python -X utf8 -I fetch.py <out_dir> <Edit|Server> <Dotted.Path>...  (reads script Sources from NH Combat Test)"""
import os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
out, dm = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
import time
def run(code):
    for _ in range(5):
        o = run1(code)
        if "#" in o or ">>" in o: return o
        time.sleep(3)
    raise SystemExit("fetch failed: " + o[:300])
def run1(code):
    f = os.path.join(HERE, "_f.lua"); open(f, "w", encoding="utf-8").write(code)
    return subprocess.run([sys.executable, "-X", "utf8", "-I", "E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py", "luau", "placeId: 98950102230473", dm, "@" + f], capture_output=True, text=True, encoding="utf-8").stdout
for p in sys.argv[3:]:
    segs = p.split(".")
    find = 'local n=game:GetService("%s") ' % segs[0] + ''.join('n=n:FindFirstChild("%s") ' % s for s in segs[1:])
    total = int(re.search(r"#(\d+)", run(find + 'return "#"..#n.Source')).group(1))
    buf, off = "", 1
    while off <= total:
        o = run(find + 'local s=n.Source:sub(%d,%d) return "<<"..(string.gsub(s,"[^%%w%%s]",function(c) return string.format("~%%02X",string.byte(c)) end))..">>"' % (off, off + 7999))
        buf += re.sub(r"~([0-9A-F]{2})", lambda m: chr(int(m.group(1), 16)), o[o.index("<<") + 2:o.rindex(">>")])
        off += 8000
    raw = buf.encode("latin-1").decode("utf-8")
    open(os.path.join(out, p + ".luau"), "w", encoding="utf-8", newline="").write(raw)
    print(p, total, len(raw.encode()))
