"""Install a Luau source file into NH Combat Test through a PRIVATE buffer (never NHInstallBuffer / _G.NHCompileBuf),
then checksum it (h = h * 31 + byte mod 2^31 - 1 over the UTF-8 bytes, LF line ends).

    python install.py <file.luau> <dot.path.in.game> <ClassName> [studio_id]
"""
import subprocess
import sys
from pathlib import Path

STUDIO = sys.argv[4] if len(sys.argv) > 4 else "ae020719-8a6e-4795-bbba-a2da99d033c0"   # NH Combat Test (ids change: `rbxstudio list`)


def checksum(b: bytes) -> int:
    h = 0
    for x in b:
        h = (h * 31 + x) % 2147483647
    return h


def main():
    src, path, cls = sys.argv[1], sys.argv[2], sys.argv[3]
    b = Path(src).read_bytes().replace(b"\r\n", b"\n")
    text = b.decode("utf-8")
    want = checksum(b)
    # a long-bracket literal that can't be closed by the source itself
    eq = "=" * 8
    while f"]{eq}]" in text:
        eq += "="
    parts = path.split(".")
    if parts[0] == "game":
        parts = parts[1:]
    luau = f"""
local SRC = [{eq}[
{text}]{eq}]
local buf = game:GetService("ServerStorage"):FindFirstChild("NHHungerInstallBuf_5c41e9") or Instance.new("StringValue")
buf.Name = "NHHungerInstallBuf_5c41e9"
buf.Value = SRC
buf.Parent = game:GetService("ServerStorage")
local parent = game
local names = {{ {", ".join(repr(p).replace("'", '"') for p in parts)} }}
for i = 1, #names - 1 do
	local nxt = parent:FindFirstChild(names[i]) or (i == 1 and game:GetService(names[i])) or nil
	if not nxt then return "missing parent " .. names[i] end
	parent = nxt
end
local s = parent:FindFirstChild(names[#names])
if s and s.ClassName ~= "{cls}" then return "class mismatch " .. s.ClassName end
if not s then s = Instance.new("{cls}") s.Name = names[#names] end
s.Source = buf.Value
s.Parent = parent
local h = 0
local v = s.Source
for i = 1, #v do h = (h * 31 + string.byte(v, i)) % 2147483647 end
buf:Destroy()
return "installed " .. s:GetFullName() .. " len " .. #v .. " sum " .. h
"""
    import json, shutil
    exe = shutil.which("rbxstudio") or shutil.which("rbxstudio.cmd")

    def run(code):
        args = json.dumps({"code": code, "studio_id": STUDIO, "datamodel_type": "Edit"})
        cli = "C:/Users/Owner/AppData/Roaming/npm/node_modules/rbx-studio-cli/bin/rbxstudio"
        r = subprocess.run(["node", cli, "raw", "execute_luau", args], capture_output=True, text=True, encoding="utf-8")
        return (r.stdout or "") + (r.stderr or "")
    BUF = 'game:GetService("ServerStorage"):FindFirstChild("NHHungerInstallBuf_5c41e9")'
    print(run('local b = Instance.new("StringValue") b.Name = "NHHungerInstallBuf_5c41e9" b.Parent = game:GetService("ServerStorage") return "buf"').strip()[-80:])
    CH = 7000
    for i in range(0, len(text), CH):
        chunk = text[i:i + CH]
        e = "=" * 8
        while f"]{e}]" in chunk or chunk.endswith("]" + e[:-1]):
            e += "="
        o = run(f"local b = {BUF} b.Value = b.Value .. [{e}[" + "\n" + chunk + f"]{e}] return #b.Value")
        print("  chunk", i, o.strip()[-60:])
        if "error" in o.lower() and "Error" in o:
            print("chunk failed", o[-300:])
            return
    final = luau[luau.index("local parent = game"):]
    out = run(f"local buf = {BUF}" + "\n" + final)
    ok = f"sum {want}" in out and f"len {len(b)}" in out
    print(out.strip()[-400:])
    print("CHECKSUM", "OK" if ok else f"MISMATCH (want len {len(b)} sum {want})")


if __name__ == "__main__":
    main()
