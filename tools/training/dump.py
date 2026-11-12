"""Dump a Studio script's current source to a local file (via the MCP script_read), for diffing before a patch."""
import json, re, subprocess, sys
cli = "C:/Users/Owner/AppData/Roaming/npm/node_modules/rbx-studio-cli/bin/rbxstudio"
STUDIO = "3975893b-27d9-494f-aa48-c79a0349d872"
path, out = sys.argv[1], sys.argv[2]
r = subprocess.run(["node", cli, "raw", "script_read", json.dumps({"studio_id": STUDIO, "target_file": path})],
                   capture_output=True, text=True, encoding="utf-8")
txt = json.loads(r.stdout)
lines = []
for ln in txt.split("\n"):
    m = re.match(r"^\s*(\d+)\u2192(.*)$", ln)
    if m:
        lines.append(m.group(2))
    elif lines:
        lines[-1] += "\n" + ln   # never expected
open(out, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
print(path, len(lines), "lines")
