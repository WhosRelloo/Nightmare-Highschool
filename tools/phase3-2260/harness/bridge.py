"""usage: python -X utf8 -I bridge.py <Command> [lua literal args...]   e.g. bridge.py CineJudgeTest   bridge.py PlayCut $P '"Prologue"' true"""
import os, subprocess, sys
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
PLACE = "placeId: 98950102230473"
TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_bridge.lua")
cmd, args = sys.argv[1], sys.argv[2:]
lua_args = ", ".join("P.Name" if a == "$P" else a for a in args)
open(TMP, "w", encoding="utf-8").write(f'''local H = game:GetService("HttpService")
local P = game.Players:GetPlayers()[1]
local ok, r = game.ServerStorage.NHTestBridge:Invoke("{cmd}"{", " + lua_args if lua_args else ""})
local okj, j = pcall(H.JSONEncode, H, {{ ok = ok; result = r }})
return okj and j or tostring(r)''')
r = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", PLACE, "Server", "@" + TMP], capture_output=True, text=True, encoding="utf-8")
print(r.stdout.replace("\r", ""))
