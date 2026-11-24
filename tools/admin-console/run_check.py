"""Run a check file in NH Combat Test. usage: python -X utf8 -I run_check.py <Edit|Server|Client> <check.lua>
Prints the check's result. Exit 1 unless it starts with PASS."""
import subprocess, sys
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
dm, f = sys.argv[1], sys.argv[2]
r = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", "placeId: 98950102230473", dm, "@" + f],
                   capture_output=True, text=True, encoding="utf-8")
out = (r.stdout or "").strip()
print(out or r.stderr[-2000:])
sys.exit(0 if out.startswith("PASS") else 1)
