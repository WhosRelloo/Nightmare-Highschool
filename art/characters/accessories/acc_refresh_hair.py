"""Write a Studio script that refreshes the hair attributes (NHHairFit, NHHairTuck) on templates already in
ReplicatedStorage.NHAccessories, from the layouts and tucks (no re-import needed).

python acc_refresh_hair.py <name> <Model>[,<Model>...]  ->  tools/accessories/refresh_hair_<name>.luau
"""
import json, os, sys
sys.argv += [] 
import importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
name, models = sys.argv[1], sys.argv[2].split(",")
ROOT = "E:/NH-Work/acc"
spec = importlib.util.spec_from_file_location("asm_helpers", os.path.join(HERE, "acc_assemble.py"))
# reuse acc_assemble's string builders without running it: read the two functions' source
src = open(os.path.join(HERE, "acc_assemble.py"), encoding="utf-8").read()
ns = {"os": os, "json": json, "ROOT": ROOT}
for fn in ("def hair_fit_string", "def tuck_string"):
    i = src.index(fn)
    j = src.index("\n\n\n", i)
    exec(src[i:j], ns)
lines = [f"-- Refresh the hair attributes of templates already in the game ({name}): NHHairFit and NHHairTuck from",
         "-- art/characters/accessories/layout + tuck (acc_refresh_hair.py). NH Combat Test, Edit. Re-runnable.",
         "local store = game.ReplicatedStorage:FindFirstChild(\"NHAccessories\")",
         "local report = {}",
         "local DATA = {"]
for m in models:
    lay = json.load(open(f"{ROOT}/layout/{m}.json"))
    for pn, e in lay["pieces"].items():
        hf = ns["hair_fit_string"](e.get("hair_fit"))
        tk = ns["tuck_string"](m, pn)
        lines.append("\t{ %s, %s, %s, %s };" % (json.dumps(m), json.dumps(pn), json.dumps(hf) if hf else "nil", json.dumps(tk) if tk else "nil"))
lines += ["}",
          "for _, d in ipairs(DATA) do",
          "\tlocal model, piece, fit, tuck = d[1], d[2], d[3], d[4]",
          "\tlocal M = store and store:FindFirstChild(model)",
          "\tlocal P = M and M:FindFirstChild(piece)",
          "\tif not P then table.insert(report, model .. \".\" .. piece .. \": no template\") continue end",
          "\tP:SetAttribute(\"NHHairFit\", fit)",
          "\tP:SetAttribute(\"NHHairTuck\", tuck)",
          "\ttable.insert(report, model .. \".\" .. piece .. \": fit\" .. (tuck and (\", tuck for \" .. select(2, tuck:gsub(\";\", \"\")) + 1 .. \" hairs\") or \"\"))",
          "end",
          'return table.concat(report, "\\n")']
out = os.path.join("E:/Nightmare-Highschool/tools/accessories", f"refresh_hair_{name}.luau")
open(out, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
print(out, os.path.getsize(out))
