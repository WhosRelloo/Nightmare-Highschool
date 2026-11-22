"""usage: python -X utf8 -I client.py <file.lua>"""
import subprocess, sys
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
r = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", "placeId: 98950102230473", "Edit", "@" + sys.argv[1]], capture_output=True, text=True, encoding="utf-8")
print(r.stdout.replace("\r", ""))
