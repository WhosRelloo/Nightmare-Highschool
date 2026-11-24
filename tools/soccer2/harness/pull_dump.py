"""Pull _G.NHSoccerDump (written by checks/soccer_demo.lua) from the Play client in 20,000-character chunks.
usage: python -X utf8 -I tools/soccer2/harness/pull_dump.py <out.json>"""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.join(os.path.dirname(os.path.dirname(HERE)), "admin-console", "run_live.py")
TMP = os.path.join(HERE, "_pull.lua")
out, i = [], 0
while True:
    open(TMP, "w", encoding="utf-8").write('local S = _G.NHSoccerDump\nif not S then return "FAIL no dump" end\n'
        'local a = %d * 20000 + 1\nif a > #S then return "PASS <<EOF>>" end\nreturn "PASS " .. S:sub(a, a + 19999)' % i)
    r = subprocess.run([sys.executable, "-X", "utf8", "-I", RUN, TMP, "30", "Client"], capture_output=True, text=True, encoding="utf-8")
    s = r.stdout.rstrip("\r\n")
    if not s.startswith("PASS "): sys.exit("pull failed: " + s[:300])
    s = s[5:]
    if s == "<<EOF>>": break
    out.append(s)
    i += 1
open(sys.argv[1], "w", encoding="utf-8").write("".join(out))
print("pulled", i, "chunks,", sum(len(x) for x in out), "chars")
