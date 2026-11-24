"""Run a check inside the running game's own VM. usage: python -X utf8 -I run_live.py <check.lua> [timeout_s] [Server|Client]
The MCP's execute_luau gets a fresh module graph on both sides (on the server, its require of Features.Admin never ran
OnStart and sees no loaded profiles; on the client, its require of the StaffConsole controller is not the one the
game runs). So the check goes in a Script under ServerScriptService (Server, the default) or a LocalScript under
PlayerGui (Client), as restore.py does, and the result comes back through an attribute. Prints the result; exit 1
unless it starts with PASS.
On a timeout the check is not destroyed mid-run: it gets the attribute Stop (checks poll it and clean up) and up to
90 s more to answer; console_play_run.lua then puts slot 2 back and clears NHTestLevel before it returns."""
import os, subprocess, sys
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
src = open(sys.argv[1], encoding="utf-8").read()
timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 240
side = sys.argv[3] if len(sys.argv) > 3 else "Server"
assert side in ("Server", "Client")
assert "]==]" not in src
cls, parent = ("Script", "game.ServerScriptService") if side == "Server" else ("LocalScript", "game.Players.LocalPlayer:WaitForChild(\"PlayerGui\")")
lua = '''local S = Instance.new("%s")
S.Name = "NHConsoleCheck"
S.Source = [==[
local function main()
%s
end
local ok, r = pcall(main)
script:SetAttribute("Out", if ok then tostring(r) else "FAIL error: " .. tostring(r))
]==]
S.Parent = %s
local t0 = os.clock()
while S:GetAttribute("Out") == nil and os.clock() - t0 < %d do task.wait(0.5) end
-- timed out: never destroy a check mid-run (it would skip its put-back); ask it to stop and give it time to clean up
if S:GetAttribute("Out") == nil then
	S:SetAttribute("Stop", true)
	local t1 = os.clock()
	while S:GetAttribute("Out") == nil and os.clock() - t1 < 90 do task.wait(0.5) end
end
local r = S:GetAttribute("Out")
S:Destroy()
return tostring(r or "FAIL timeout")''' % (cls, src, parent, timeout)
tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_live.lua")
open(tmp, "w", encoding="utf-8").write(lua)
r = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", "placeId: 98950102230473", side, "@" + tmp],
                   capture_output=True, text=True, encoding="utf-8")
out = (r.stdout or "").strip()
print(out or r.stderr[-2000:])
sys.exit(0 if out.startswith("PASS") else 1)
