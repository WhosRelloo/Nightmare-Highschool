"""Replay the combat releases' edit lists (in order) onto the Map's sources. usage: python mapport/chain.py SRC OUT"""
import importlib, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHAIN = ["q8_patches","q8b_patches","q8c_patches","q9_patches","q9b_patches","q10_patches","q10b_patches","q10c_patches",
         "q11_patches","q11b_patches","q12_patches","q13_patches","q13b_patches","q13c_patches","q13d_patches","q13e_patches",
         "q14_config","q14_server","q14_armory","q14_ui","q14b","q14c","q14d"]
src, out = sys.argv[1], sys.argv[2]
if os.path.exists(out): shutil.rmtree(out)
shutil.copytree(src, out)
fails, applied = [], 0
for m in CHAIN:
    for path, old, new in importlib.import_module(m).EDITS:
        f = os.path.join(out, path + ".luau")
        if not os.path.exists(f): continue  # a file the Map doesn't have here (new, or missing on the Map)
        s = open(f, encoding="utf-8", newline="").read()
        n = s.count(old)
        if n != 1:
            fails.append((m, path, n, old[:90].replace("\n", " | ")))
            continue
        open(f, "w", encoding="utf-8", newline="").write(s.replace(old, new))
        applied += 1
print("applied", applied)
for x in fails: print("FAIL", x)
