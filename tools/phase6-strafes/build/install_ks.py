"""T2: build every anim/out/NHG_*.lua in NH Combat Test (Edit) -> ServerStorage.NHGestures + NHPublish.Gestures (and
ReplicatedStorage.NHLocoClips for the strafes). Each builder refuses to run outside NH Combat Test.
usage: python -X utf8 -I install_ks.py [names...]"""
import glob, os, subprocess, sys
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "anim", "out")
files = [os.path.join(OUT, n + ".lua") for n in sys.argv[1:]] or sorted(glob.glob(os.path.join(OUT, "NHG_*.lua")))
bad = 0
for f in files:
    r = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", "placeId: 98950102230473", "Edit", "@" + f], capture_output=True, text=True, encoding="utf-8")
    out = (r.stdout or r.stderr).strip().replace("\r", "")
    ok = out.startswith("built")
    bad += 0 if ok else 1
    print(("ok   " if ok else "FAIL ") + out[:200])
print(f"{len(files) - bad}/{len(files)} built")
