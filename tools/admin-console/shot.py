"""Save a Studio screen_capture as a PNG. usage: python -X utf8 -I shot.py <out.png>
Uses rbxc.py's MCP client (E:/Rensei/Rensei-Game-Design/Art/Tools) against NH Combat Test."""
import base64, importlib.util, json, sys
spec = importlib.util.spec_from_file_location("rbxc", r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py")
rbxc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rbxc)
out = sys.argv[1]
c = rbxc.Client()
try:
    r = c.req("tools/call", {"name": "list_roblox_studios", "arguments": {}})
    data = json.loads(r["result"]["content"][0]["text"])
    items = data if isinstance(data, list) else data.get("studios") or data.get("instances") or []
    hits = [i for i in items if "98950102230473" in (i.get("name") or "")]
    sid = hits[0]["id"]
    r = c.req("tools/call", {"name": "screen_capture", "arguments": {"capture_id": "ConsoleShot", "studio_id": sid}}, timeout=120)
    res = r.get("result") or r.get("error")
    saved = False
    for part in res.get("content") or []:
        if part.get("type") == "image":
            open(out, "wb").write(base64.b64decode(part["data"]))
            saved = True
            break
    print(("saved " + out) if saved else ("no image: " + json.dumps(res)[:500]))
finally:
    c.close()
