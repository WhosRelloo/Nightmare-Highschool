# Run Luau in Studio through the rbxstudio CLI. Set STUDIO to the current id from list_roblox_studios (it changes when Studio reopens).
import json, subprocess, sys, os

CLI = "C:/Users/Owner/AppData/Roaming/npm/node_modules/rbx-studio-cli/bin/rbxstudio"
STUDIO = "d4d1c2a6-c32d-4379-8b51-80a3e5e9bb70"

def run(dm, code):
    args = json.dumps({"studio_id": STUDIO, "datamodel_type": dm, "code": code})
    r = subprocess.run(["node", CLI, "raw", "execute_luau", args], capture_output=True, text=True, encoding="utf-8")
    return r.stdout, r.stderr

if __name__ == "__main__":
    dm, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    for path in sys.argv[3:]:
        code = ("local i = game\nfor seg in string.gmatch(%s, '[^%%.]+') do if seg ~= 'game' then "
                "i = i:FindFirstChild(seg) or game:GetService(seg) end end\nreturn i.Source") % json.dumps(path)
        out, err = run(dm, code)
        fn = os.path.join(outdir, path.replace("game.", "") + ".luau")
        try:
            out = json.loads(out)
        except Exception:
            pass
        open(fn, "w", encoding="utf-8", newline="").write(out)
        print(os.path.basename(fn), len(out.splitlines()), err[:150])
