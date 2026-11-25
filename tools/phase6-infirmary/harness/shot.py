"""Save a Studio screen_capture of NH Combat Test as an image.
usage: python -X utf8 -I shot.py <out.png> [cx cy cz lx ly lz]   (camera position, look-at; Edit only)
Uses rbxc.py's MCP client (E:/Rensei/Rensei-Game-Design/Art/Tools)."""
import base64, importlib.util, json, sys
spec = importlib.util.spec_from_file_location("rbxc", r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py")
rbxc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rbxc)
out = sys.argv[1]
args = {"capture_id": "InfirmaryShot"}
if len(sys.argv) >= 8:
    v = [float(x) for x in sys.argv[2:8]]
    args["camera_position"], args["look_at_position"] = v[:3], v[3:]
c = rbxc.Client()
try:
    r = c.req("tools/call", {"name": "list_roblox_studios", "arguments": {}})
    data = json.loads(r["result"]["content"][0]["text"])
    items = data if isinstance(data, list) else data.get("studios") or []
    args["studio_id"] = [i for i in items if "98950102230473" in (i.get("name") or "")][0]["id"]
    r = c.req("tools/call", {"name": "screen_capture", "arguments": args}, timeout=120)
    res = r.get("result") or r.get("error")
    for part in res.get("content") or []:
        if part.get("type") == "image":
            open(out, "wb").write(base64.b64decode(part["data"]))
            print("saved " + out)
            break
    else:
        print("no image: " + json.dumps(res)[:500])
finally:
    c.close()
