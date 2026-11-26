"""Compile the nine seated R6 Anatomy clips (<Clip>.json -> lua/<Clip>.lua with animpro.mjs) and build them in
NH Combat Test (Edit) under ReplicatedStorage.AnatomyClips.Animations, then the Clips map module.
usage (from tools/electives/anim): python -X utf8 -I make_clips.py [--no-studio]"""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ANIMPRO = os.path.expanduser("~/.claude/skills/roblox-cinematic-animation/scripts/animpro.mjs")
RBXC = "E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
CLIPS = ["BenchIdle", "Unwind", "Trace", "Pry", "Lift", "Recoil", "Loupe", "Write", "Done"]
os.makedirs(os.path.join(HERE, "lua"), exist_ok=True)
os.makedirs(os.path.join(HERE, "sheets"), exist_ok=True)
bad = 0
for n in CLIPS:
    r = subprocess.run(["node", ANIMPRO, f"{n}.json", "--sheet", f"sheets/{n}.png", "--trails", f"sheets/{n}_t.png",
                        "--out", f"lua/{n}.lua", "--parent", "game.ReplicatedStorage.AnatomyClips", "--life", "0.6"],
                       cwd=HERE, capture_output=True, text=True)
    print(n, "animpro exit", r.returncode)
    bad += r.returncode not in (0,)
if "--no-studio" not in sys.argv:
    subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", "placeId: 98950102230473", "Edit",
                    "@" + os.path.join(HERE, "..", "harness", "mkfolder.lua")], check=False)
    for n in CLIPS:
        subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", "placeId: 98950102230473", "Edit", "@" + os.path.join(HERE, "lua", f"{n}.lua")])
    subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", "placeId: 98950102230473", "Edit", "@" + os.path.join(HERE, "clips_map.lua")])
sys.exit(1 if bad else 0)
