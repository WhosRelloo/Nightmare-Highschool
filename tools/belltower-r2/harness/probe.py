"""usage: python -X utf8 -I probe.py <Command> [lua literal args...]   e.g. probe.py Get   probe.py Witness '"Truancy"'
Invokes ServerStorage.NHNotorietyProbe (Studio only, made by Services.School.Notoriety) for the first player."""
import os, subprocess, sys
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
PLACE = "placeId: 98950102230473"
TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_probe.lua")
cmd, args = sys.argv[1], sys.argv[2:]
lua_args = ", ".join(args)
open(TMP, "w", encoding="utf-8").write(f'''local H = game:GetService("HttpService")
local P = game.Players:GetPlayers()[1]
local B = game.ServerStorage:FindFirstChild("NHNotorietyProbe")
if not B then return "NO PROBE" end
local r = B:Invoke("{cmd}", P and P.Name{", " + lua_args if lua_args else ""})
local okj, j = pcall(H.JSONEncode, H, r)
return okj and j or tostring(r)''')
r = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", PLACE, "Server", "@" + TMP], capture_output=True, text=True, encoding="utf-8")
print(r.stdout.replace("\r", ""))
