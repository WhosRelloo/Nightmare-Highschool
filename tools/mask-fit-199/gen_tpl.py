# python port5/gen_tpl.py <root> <backup folder path, e.g. ServerStorage.NH_Backup> <out.luau>
# The face masks' templates (ReplicatedStorage.NHAccessories): NHFit, NHHairFit, NHHairTuck, NHHairScale from <root>'s
# layouts and tucks, written the way acc_assemble.py writes them. Backs each model up first (<Model>_pre199).
import io, json, os, re, sys

ROOT, BK, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
A = "E:/Nightmare-Highschool/art/characters/accessories/acc_assemble.py"
src = open(A, encoding="utf-8").read()
# the two string builders, as acc_assemble has them
ns = {"os": os, "json": json, "ROOT": ROOT}
for name in ("tuck_string", "hair_fit_string"):
    m = re.search(r"\ndef " + name + r"\(.*?(?=\n\n\n)", src, re.S)
    exec(m.group(0), ns)
hf_src = open("E:/Nightmare-Highschool/art/characters/accessories/acc_hairfit.py", encoding="utf-8").read()
MASKS = set(re.findall(r'"(\w+)"', re.search(r"MASKS = \{(.*?)\}", hf_src, re.S).group(1)))

ITEMS = ["DominoMask", "FoxMask", "GrilleMask", "KintsugiMask", "Masks", "MothMask", "WatchMask", "WaxMask", "WolfMask"]


def lstr(s):
    return "nil" if s is None else '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


L = ["local R = game.ReplicatedStorage.NHAccessories",
     "local BK = game"]
for seg in BK.split("."):
    L.append(f'BK = BK:FindFirstChild("{seg}") or (function(p) local f = Instance.new("Folder") f.Name = "{seg}" f.Parent = p return f end)(BK)')
L.append("local out = {}")
for it in ITEMS:
    lay = json.load(open(os.path.join(ROOT, "layout", it + ".json")))
    L.append(f'do local M = R:FindFirstChild("{it}") assert(M, "no template {it}")')
    L.append(f'  if not BK:FindFirstChild("{it}_pre199") then local c = M:Clone() c.Name = "{it}_pre199" c.Parent = BK end')
    for pn, e in lay["pieces"].items():
        if e.get("mount") != "Head":
            continue
        f = e["fit"]
        hf = ns["hair_fit_string"](e.get("hair_fit"))
        tk = ns["tuck_string"](it, pn)
        L.append(f'  local P = M:FindFirstChild("{pn}", true) assert(P, "no piece {it}.{pn}")')
        L.append(f'  P:SetAttribute("NHFit", CFrame.new({f[0]:.4f}, {f[1]:.4f}, {f[2]:.4f}))')
        L.append(f'  P:SetAttribute("NHHairFit", {lstr(hf)})')
        L.append(f'  P:SetAttribute("NHHairTuck", {lstr(tk)})')
        L.append(f'  P:SetAttribute("NHHairScale", {lstr("Radial" if pn in MASKS else None)})')
        L.append(f'  P:SetAttribute("NHPreviewShifted", nil)')
        L.append(f'  table.insert(out, "{it}.{pn} fit " .. tostring(P:GetAttribute("NHFit").Position) .. " tuck " .. tostring(P:GetAttribute("NHHairTuck") ~= nil))')
    L.append("end")
L.append('return table.concat(out, "\\n")')
io.open(OUT, "w", encoding="utf-8", newline="").write("\n".join(L) + "\n")
print("ok", OUT, len(L))
