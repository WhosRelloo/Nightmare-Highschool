"""Checksum every script in a place (outside NH_Backup and Players). usage: python place_hashes.py <studio_id> <out.json>"""
import json, subprocess, sys
CLI = "C:/Users/Owner/AppData/Roaming/npm/node_modules/rbx-studio-cli/bin/rbxstudio"
code = r'''
local out = {}
local roots = { game.ServerScriptService, game.ServerStorage, game.ReplicatedStorage, game.StarterPlayer, game.StarterGui, game.ReplicatedFirst, workspace }
for _, R in roots do
	for _, s in R:GetDescendants() do
		if s:IsA("LuaSourceContainer") then
			local p = s:GetFullName()
			if not p:find("NH_Backup", 1, true) and not p:find("NHHungerInstallBuf", 1, true) then
				local src = s.Source
				local h = 0
				for i = 1, #src, 1 do h = (h * 31 + string.byte(src, i)) % 2147483647 end
				out[#out + 1] = p .. "\t" .. s.ClassName .. "\t" .. #src .. "\t" .. h
			end
		end
	end
	task.wait()
end
return table.concat(out, "\n")'''
sid, dest = sys.argv[1], sys.argv[2]
r = subprocess.run(["node", CLI, "raw", "execute_luau", json.dumps({"studio_id": sid, "datamodel_type": "Edit", "code": code})], capture_output=True, text=True, encoding="utf-8")
txt = r.stdout.strip()
try: txt = json.loads(txt)
except Exception: pass
rows = {}
for line in txt.split("\n"):
    parts = line.split("\t")
    if len(parts) == 4: rows[parts[0]] = {"class": parts[1], "len": int(parts[2]), "hash": parts[3]}
json.dump(rows, open(dest, "w"))
print(sid, len(rows), r.stderr[:200])
