"""usage: python -X utf8 -I probe.py <Command> [lua literal args...]   e.g. probe.py Get   probe.py Slip '{Title="Hi", Text="x"}'
Invokes PlayerGui.NHQuietProbe (Studio only, made by Controllers.Gui.HudState) in the Client VM; prints JSON."""
import os, subprocess, sys
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_probe.lua")
cmd, args = sys.argv[1], sys.argv[2:]
open(TMP, "w", encoding="utf-8").write(f'''local H = game:GetService("HttpService")
local B = game.Players.LocalPlayer.PlayerGui:FindFirstChild("NHQuietProbe")
if not B then return "NO PROBE" end
local r = B:Invoke("{cmd}"{", " + ", ".join(args) if args else ""})
local okj, j = pcall(H.JSONEncode, H, r)
return okj and j or tostring(r)''')
r = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", "placeId: 98950102230473", "Client", "@" + TMP],
                   capture_output=True, text=True, encoding="utf-8")
print(r.stdout.replace("\r", ""))
