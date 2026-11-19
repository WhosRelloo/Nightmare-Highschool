"""Dump Studio scripts into the mirror. usage: python -X utf8 -I dump.py <dotted path> [...]"""
import os, subprocess, sys
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
PLACE = "placeId: 98950102230473"
ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "phase5-2310")
TMP = os.path.join(ROOT, "harness", "_dump.lua")
for path in sys.argv[1:]:
    text, c = "", 0
    while True:
        open(TMP, "w", encoding="utf-8").write(f'''local inst = game
for part in string.gmatch("{path}", "[^%.]+") do inst = inst:FindFirstChild(part) end
local s = inst.Source
local a = {c} * 25000 + 1
if a > #s then return "<<EOF>>" end
return s:sub(a, a + 24999) .. "<<CHUNK>>"''')
        out = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", PLACE, "Edit", "@" + TMP], capture_output=True, text=True, encoding="utf-8").stdout.replace("\r", "")
        if out.startswith("<<EOF>>"): break
        text += out[:out.rfind("<<CHUNK>>")]
        c += 1
    for sub in ("pre", "live"):
        os.makedirs(os.path.join(ROOT, sub), exist_ok=True)
        dest = os.path.join(ROOT, sub, path + ".luau")
        if sub == "pre" and os.path.exists(dest): continue  # pre/ is the first snapshot only
        open(dest, "w", encoding="utf-8", newline="").write(text)
    print(path, len(text.encode("utf-8")), "bytes")
