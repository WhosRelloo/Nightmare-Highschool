"""Pull scripts' current Source from NH Combat Test (Edit). usage: python -X utf8 -I fetch.py <out_dir> <Dotted.Path> [...]
Writes <out_dir>/<Dotted.Path>.luau byte for byte. Exit 1 if any path is missing.
rbxc caps one call's output (~30000 chars), so a script is read in CHUNK-byte pieces cut on UTF-8 boundaries."""
import json, os, subprocess, sys
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
PLACE = "placeId: 98950102230473"
HERE = os.path.dirname(os.path.abspath(__file__))
CHUNK = 8000
out, paths = sys.argv[1], sys.argv[2:]
os.makedirs(out, exist_ok=True)
bad = 0


def run(lua):
    f = os.path.join(HERE, "_fetch.lua")
    open(f, "w", encoding="utf-8").write(lua)
    r = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", PLACE, "Edit", "@" + f],
                       capture_output=True, text=True, encoding="utf-8")
    return (r.stdout or "").strip()


for p in paths:
    segs = ", ".join('"%s"' % s for s in p.split("."))
    head = ('local N = game for _, S in {%s} do N = N and N:FindFirstChild(S) end\n'
            'if not N then return "MISSING" end\n' % segs)
    txt = run(head + 'return tostring(#N.Source)')
    if not txt.isdigit():
        print("MISSING", p, txt[:200]); bad += 1; continue
    total, pos, parts = int(txt), 1, []
    while pos <= total:
        body = ('local S = N.Source local a = %d local b = math.min(a + %d, #S + 1)\n'
                'while b <= #S and (S:byte(b) >= 128 and S:byte(b) < 192) do b += 1 end\n'
                'return game:GetService("HttpService"):JSONEncode({ S = S:sub(a, b - 1), B = b })' % (pos, CHUNK))
        chunk = run(head + body)
        if not chunk.startswith("{"):
            print("MISSING", p, chunk[:200]); bad += 1; parts = None; break
        d = json.loads(chunk)
        parts.append(d["S"]); pos = d["B"]
    if parts is None:
        continue
    src = "".join(parts)
    open(os.path.join(out, p + ".luau"), "w", encoding="utf-8", newline="").write(src)
    print("ok", p, len(src), "(%d bytes)" % total)
sys.exit(1 if bad else 0)
