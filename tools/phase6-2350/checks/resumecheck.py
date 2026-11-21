"""resumecheck (task 12 fix round 1): Tutorial.Resume rows, Play on slot 2, run from the harness dir:
   python -X utf8 -I ../checks/resumecheck.py
Sets a checkpoint, kills the character, reads where the respawn lands (3 studs above the mark). Clears marks and the checkpoint after."""
import os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
HARN = os.path.join(HERE, "..", "harness")
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
PLACE = "placeId: 98950102230473"
TMP = os.path.join(HARN, "_resume.lua")

def server(lua):
    open(TMP, "w", encoding="utf-8").write(lua)
    r = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", PLACE, "Server", "@" + TMP], capture_output=True, text=True, encoding="utf-8")
    return r.stdout.strip()

def bridge(cmd, *args):
    subprocess.run([sys.executable, "-X", "utf8", "-I", os.path.join(HARN, "bridge.py"), cmd, *args], capture_output=True, text=True, encoding="utf-8")

def setcp(v):
    arg = "nil" if v is None else '"%s"' % v
    server('local S = Instance.new("Script") S.Source = [[ require(game.ServerScriptService.Services.Player.Progression).SetCheckpoint(game.Players:GetPlayers()[1], %s) ]] S.Parent = game.ServerScriptService task.wait(1) S:Destroy() return "ok"' % arg)

def respawn_pos():
    server('game.Players:GetPlayers()[1].Character.Humanoid.Health = 0 return "k"')
    time.sleep(6)
    return server('local r = game.Players:GetPlayers()[1].Character.HumanoidRootPart return r.Position.X .. "," .. r.Position.Y .. "," .. r.Position.Z')

ROWS = [  # (label, seen cut, checkpoint, expected x, z)
    ("sneak Seen, checkpoint TutorialSneak:Fence -> FenceLand", "TutorialSneak", "TutorialSneak:Fence", 4012, 4077.5),
    ("sneak not Seen, checkpoint TutorialSneak:Fence -> FenceZone", None, "TutorialSneak:Fence", 4012, 4082),
    ("sneak not Seen, checkpoint TutorialSneak:Garden -> Start", None, "TutorialSneak:Garden", 3994, 4104),
    ("bus Seen (under the hold), checkpoint TutorialBus:Main -> Stand", "TutorialBus", "TutorialBus:Main", 4001.5, 3998.3),
    ("bus not Seen (died mid-cut), checkpoint TutorialBus:Start -> Stand", None, "TutorialBus:Start", 4001.5, 3998.3),
]
bridge("TutorialEnter", "$P")
ok_all = True
for label, seen, cp, ex, ez in ROWS:
    for c in ("TutorialSneak", "TutorialBus"): bridge("CineMark", "$P", '"%s"' % c, "nil")
    if seen: bridge("CineMark", "$P", '"%s"' % seen, '"Seen"')
    setcp(cp)
    p = respawn_pos()
    x, _, z = [float(v) for v in p.split(",")]
    ok = abs(x - ex) < 0.6 and abs(z - ez) < 0.6
    ok_all = ok_all and ok
    print(("ok   " if ok else "FAIL ") + label + " (landed %.1f, %.1f; want %.1f, %.1f)" % (x, z, ex, ez))
for c in ("TutorialSneak", "TutorialBus"): bridge("CineMark", "$P", '"%s"' % c, "nil")
setcp(None)
bridge("TutorialLeave", "$P")
print("RESUME OK" if ok_all else "RESUME FAIL")
