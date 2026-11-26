"""Run a check in NH Combat Test's Edit VM. usage: python -X utf8 -I edit.py <check.lua>. Exit 1 unless it prints PASS."""
import subprocess, sys
r = subprocess.run([sys.executable, "-X", "utf8", "-I", r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py", "luau", "placeId: 98950102230473", "Edit", "@" + sys.argv[1]], capture_output=True, text=True, encoding="utf-8")
out = (r.stdout or r.stderr).strip()
print(out)
sys.exit(0 if out.startswith("PASS") else 1)
