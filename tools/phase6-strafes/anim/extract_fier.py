"""Read-only extract of the FIER ANIMATIONS source clips (S2). NEVER writes to FIER: the Luau only reads properties and
returns text. usage: python -X utf8 -I extract_fier.py [names...]   (default: every source in recipes.json)
Writes src/<Folder>__<Clip>.json (bake.py's clip format). Clips over 20 s keep every 2nd keyframe (they're decimated
to 15 fps by the bake anyway)."""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
PLACE = "placeId: 107424155290133"
TMP = os.path.join(HERE, "..", "harness", "_extract.lua")
FOLDERS = ["Cinematic / NPC Gestures", "Idle Anims", "Injured Anims", "Interaction Anims", "Walk / Stand Anims",
           "Movement Anims", "Quick Movement Anims", "Soccer Anims", "Zombie Anims"]
CHUNK = 60  # keyframes per call (the result cap is 30,000 chars)


def sanitize(folder, clip):
    f = re.sub(r"[^A-Za-z0-9]+", "_", folder).strip("_")
    c = re.sub(r"[^A-Za-z0-9]+", "_", clip).strip("_")
    return f + "__" + c


def unsanitize(name):
    for f in FOLDERS:
        pre = re.sub(r"[^A-Za-z0-9]+", "_", f).strip("_") + "__"
        if name.startswith(pre):
            return f, name[len(pre):]
    raise SystemExit("unknown folder in " + name)


LUA = r'''local F = workspace:FindFirstChild(%s)
local S = F and F:FindFirstChild("AnimSaves")
if not S then return "ERR no folder" end
local Want = %s
local KS
for _, k in S:GetChildren() do
	if k:IsA("KeyframeSequence") and (k.Name:gsub("[^%%w]+", "_"):gsub("^_+", ""):gsub("_+$", "")) == Want then KS = k break end
end
if not KS then return "ERR no clip " .. Want end
local kfs = {}
for _, k in KS:GetChildren() do if k:IsA("Keyframe") then table.insert(kfs, k) end end
table.sort(kfs, function(a, b) return a.Time < b.Time end)
local Step = (kfs[#kfs].Time > 20) and 2 or 1
local Pick = {}
for i = 1, #kfs, Step do table.insert(Pick, kfs[i]) end
if Pick[#Pick] ~= kfs[#kfs] then table.insert(Pick, kfs[#kfs]) end
local From, Count = %d, %d
local out = { string.format("H;%%s;%%s;%%s;%%d;%%d", KS.Name, tostring(KS.Loop), KS.Priority.Name, #Pick, #kfs) }
local function r(v) return string.format("%%.4f", v) end
for i = From, math.min(#Pick, From + Count - 1) do
	local k = Pick[i]
	local line = { r(k.Time) }
	for _, p in k:GetDescendants() do
		if p:IsA("Pose") and p.Name ~= "HumanoidRootPart" then
			local c = p.CFrame
			local ax, an = c:ToAxisAngle()
			local s = math.sin(an / 2)
			table.insert(line, p.Name .. "=" .. table.concat({ r(ax.X * s), r(ax.Y * s), r(ax.Z * s), r(math.cos(an / 2)), r(c.X), r(c.Y), r(c.Z), r(p.Weight) }, ","))
		end
	end
	table.insert(out, table.concat(line, ";"))
end
table.insert(out, "END")
return table.concat(out, "\n")'''


def q_to_rows(qx, qy, qz, qw):
    return [1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw), 2 * (qx * qz + qy * qw),
            2 * (qx * qy + qz * qw), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw),
            2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw), 1 - 2 * (qx * qx + qy * qy)]


def run(lua):
    open(TMP, "w", encoding="utf-8").write(lua)
    r = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", PLACE, "Edit", "@" + TMP],
                       capture_output=True, text=True, encoding="utf-8")
    return r.stdout.replace("\r", "").strip()


def extract(name):
    folder, clip = unsanitize(name)
    frames, head, start = [], None, 1
    while True:
        out = run(LUA % (json.dumps(folder), json.dumps(clip), start, CHUNK))
        if out.startswith("ERR") or not out.startswith("H;"):
            raise SystemExit(f"{name}: {out[:300]}")
        lines = out.split("\n")
        if lines[-1] != "END":
            open(TMP + ".bad.txt", "w", encoding="utf-8").write(out)
            raise SystemExit(f"{name}: truncated result at keyframe {start} ({len(out)} chars)")
        lines = lines[:-1]
        h = lines[0].split(";")
        head = {"name": h[1], "loop": h[2] == "true", "priority": h[3], "picked": int(h[4]), "keyframes": int(h[5])}
        for ln in lines[1:]:
            parts = ln.split(";")
            poses = {}
            for p in parts[1:]:
                j, vals = p.split("=")
                v = [float(x) for x in vals.split(",")]
                poses[j] = {"cf": v[4:7] + q_to_rows(*v[0:4]), "w": v[7]}
            frames.append({"t": float(parts[0]), "poses": poses})
        start += CHUNK
        if start > head["picked"]:
            break
    d = {"name": head["name"], "loop": head["loop"], "priority": head["priority"], "source": f"{folder}/{head['name']}",
         "keyframes": head["keyframes"], "frames": frames}
    os.makedirs(os.path.join(HERE, "src"), exist_ok=True)
    json.dump(d, open(os.path.join(HERE, "src", name + ".json"), "w", encoding="utf-8"), separators=(",", ":"))
    print(name, len(frames), "frames of", head["keyframes"])


def count():
    return run('local n = 0 for _, d in game:GetDescendants() do if d:IsA("KeyframeSequence") then n += 1 end end return tostring(n)')


if __name__ == "__main__":
    names = sys.argv[1:] or sorted({r["src"] for r in json.load(open(os.path.join(HERE, "recipes.json"), encoding="utf-8"))})
    before = count()
    print("FIER KeyframeSequences before:", before)
    for n in names:
        extract(n)
    after = count()
    print("FIER KeyframeSequences after:", after, "(unchanged)" if after == before else "CHANGED!")
