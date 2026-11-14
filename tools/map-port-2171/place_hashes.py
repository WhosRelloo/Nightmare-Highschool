"""Checksum every script in a place, one root at a time (avoids the output cap). usage: hashes2.py <studio> <out.json>"""
import json, subprocess, sys
CLI = "C:/Users/Owner/AppData/Roaming/npm/node_modules/rbx-studio-cli/bin/rbxstudio"
ROOTS = ["ServerScriptService", "ServerStorage", "ReplicatedStorage", "StarterPlayer", "StarterGui", "ReplicatedFirst", "Workspace"]
def run(sid, code):
    r = subprocess.run(["node", CLI, "raw", "execute_luau", json.dumps({"studio_id": sid, "datamodel_type": "Edit", "code": code})], capture_output=True, text=True, encoding="utf-8")
    t = r.stdout.strip()
    try: t = json.loads(t)
    except Exception: pass
    return t, r.stderr
sid, dest = sys.argv[1], sys.argv[2]
rows = {}
for root in ROOTS:
    off = 0
    while True:
        code = r'''
local R = game:GetService("%s")
local list = {}
for _, s in R:GetDescendants() do if s:IsA("LuaSourceContainer") and not s:GetFullName():find("NHHungerInstallBuf", 1, true) then list[#list + 1] = s end end
local out = {}
for i = %d + 1, math.min(#list, %d + 150) do
	local s = list[i]
	local src = s.Source
	local h = 0
	for q = 1, #src do h = (h * 31 + string.byte(src, q)) %% 2147483647 end
	out[#out + 1] = s:GetFullName() .. "\t" .. s.ClassName .. "\t" .. #src .. "\t" .. h
end
return #list .. "\n" .. table.concat(out, "\n")''' % (root, off, off)
        t, err = run(sid, code)
        lines = str(t).split("\n")
        total = int(lines[0])
        for line in lines[1:]:
            p = line.split("\t")
            if len(p) == 4: rows[p[0]] = {"class": p[1], "len": int(p[2]), "hash": p[3]}
        off += 150
        if off >= total: break
    print(root, total)
json.dump(rows, open(dest, "w"))
print(sid, len(rows))
