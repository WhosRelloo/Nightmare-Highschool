"""usage: python -X utf8 -I server.py <file.lua>   runs the file INSIDE the game VM (a runtime Script in
ServerScriptService), so it reaches the real services. The file must end with `return <string>`. Play mode only."""
import os, subprocess, sys
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
HERE = os.path.dirname(os.path.abspath(__file__))
body = open(sys.argv[1], encoding="utf-8").read()
n = 2
while ("]" + "=" * n + "]") in body:
    n += 1
o, c = "[" + "=" * n + "[", "]" + "=" * n + "]"
lua = ('local S = Instance.new("Script")\n'
       f'S.Source = "local ok, r = pcall(function()\n" .. {o}{body}{c} .. "\nend) script:SetAttribute(\'Out\', ok and tostring(r) or (\'ERR \' .. tostring(r)))"\n'
       'S.Parent = game.ServerScriptService\n'
       'local t0 = os.clock()\n'
       'while S:GetAttribute("Out") == nil and os.clock() - t0 < 60 do task.wait(0.25) end\n'
       'local r = S:GetAttribute("Out")\nS:Destroy()\nreturn tostring(r)')
tmp = os.path.join(HERE, "_server.lua")
open(tmp, "w", encoding="utf-8").write(lua)
r = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", "placeId: 98950102230473", "Server", "@" + tmp],
                   capture_output=True, text=True, encoding="utf-8")
print(r.stdout.replace("\r", ""))
