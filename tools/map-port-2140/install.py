"""Install sources into a place by path, uploading in chunks (big scripts). usage: python mapport/install.py STUDIO_ID DIR [--create]
DIR holds <path>.luau files; existing scripts get their Source replaced; with --create, missing ones are made
(class from ct_hashes.json) under their parent path."""
import json, os, subprocess, sys
CLI = "C:/Users/Owner/AppData/Roaming/npm/node_modules/rbx-studio-cli/bin/rbxstudio"
sid, d = sys.argv[1], sys.argv[2]
create = "--create" in sys.argv
ct = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ct_hashes.json")))
def run(code):
    r = subprocess.run(["node", CLI, "raw", "execute_luau", json.dumps({"studio_id": sid, "datamodel_type": "Edit", "code": code})], capture_output=True, text=True, encoding="utf-8")
    return r.stdout.strip(), r.stderr.strip()
RESOLVE = '''local function at(p, make, class)
	local segs = {}
	for seg in string.gmatch(p, "[^%.]+") do table.insert(segs, seg) end
	local i = game:GetService(segs[1])
	for k = 2, #segs do
		local nx = i:FindFirstChild(segs[k])
		if not nx then
			if not (make and k == #segs) then return nil, "no " .. segs[k] end
			nx = Instance.new(class) nx.Name = segs[k] nx.Parent = i
		end
		i = nx
	end
	return i
end
'''
for f in sorted(os.listdir(d), key=lambda x: (x.count("."), x)):
    if not f.endswith(".luau"): continue
    path = f[:-5]
    src = open(os.path.join(d, f), encoding="utf-8").read()
    cls = ct.get(path, {}).get("class", "ModuleScript")
    o, e = run("local v = game.ServerStorage:FindFirstChild('_NHSrc') or Instance.new('StringValue', game.ServerStorage) v.Name = '_NHSrc' v.Value = '' return 'ok'")
    for i in range(0, len(src), 9000):
        o, e = run("local v = game.ServerStorage._NHSrc v.Value = v.Value .. %s return #v.Value" % json.dumps(src[i:i+9000]))
        if e: print("chunk err", path, e[:200]); break
    code = RESOLVE + '''local v = game.ServerStorage._NHSrc
local s = v.Value v:Destroy()
if not loadstring(s) then return "PARSE FAIL" end
local inst, why = at(%s, %s, %s)
if not inst then return "NO PATH " .. tostring(why) end
inst.Source = s
return "ok " .. inst.ClassName .. " " .. #inst.Source''' % (json.dumps(path), "true" if create else "false", json.dumps(cls))
    o, e = run(code)
    print(path, o, e[:200])
