# Interactive Cutscenes (framework) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Story cutscenes can stop for timed prompts (Press, Mash, Direction, Hold, Choice) and branch on the result. The server judges the prompts. A solo viewer branches on their own client the instant they press, and a group branches on the team result. A grade is kept per cut, and the prologue gets its first prompt ("Here.").

**Architecture:**
- **Shared judge:** a pure module, `ReplicatedStorage.Functions.CineJudge`. It scores a prompt from timestamped input and validates a cut's segment graph. The client and the server both use it.
- **Static graph:** a cut module gains a static `Def.Graph` (segment names, lengths, prompts, branches), which the server can read. `Def.Build(Ctx)` returns the shots and events per segment.
- **Director:** `Controllers.Cine` plays one segment at a time. A new `Controllers.CinePrompt` opens prompts and captures input, and `Gui.CineUI` draws them.
- **Server:** `Services.World.Cine` scores every viewer and decides group branches. It saves grades in `Quests.CineGrades`.

**Tech Stack:** Roblox Luau in the NH Combat Test place (placeId 98950102230473). It's installed from a repo mirror through the Studio MCP bridge (`rbxc.py`). Tests run in the game VM through `ServerStorage.NHTestBridge` and in the client VM through Studio's execute_luau.

**Spec:** `docs/expansion/12-Interactive-Cutscenes.md` (approved 2026-11-17). It builds on Phase 1 (`docs/expansion/11-Phase1-Plan.md`, 2.24.0).

**Scope:** this plan is part **A**, the framework plus the prologue prompt, shipping as **2.25.0**. Part **B**, the Chapter One finale "The Strikethrough" (§6 of the spec), gets its own plan once A has landed. B needs the animation-sourcing analysis (§8), the enemy actor, VFX, the After Hours stage and the `FileKept` torn page.

## Global Constraints

- Build only in **NH Combat Test**. The Map place (111107083446202) is **read-only**: no edits, no new instances.
- **Back up** every script before its first edit to `ServerStorage.NH_Backup.Phase2_pre_<YYYYMMDD>` (a copy of the instance, named `<Service>_<path_with_underscores>`).
- **Mirror:** `tools/phase2-2250/pre/` (before) and `tools/phase2-2250/live/` (after), one `.luau` per script, named by its dotted path. Studio is changed only by installing from `live/` with fresh instances (`tools/phase2-2250/harness/install.py`). Never edit `.Source` in place.
- **Studio must be in Edit mode** to install. Install changes made in Play don't persist.
- **UI** is built only from the UI kit's existing art and styles (`Kit.Slice`, `Theme.Images`: `Seal`, `PanelBg`, `Divider`, `Pip`, `Crest`, `Bell`; `Theme.Colors`; `Kit.Button`; `Kit.PlaySound`). No plain grey frames, no default prompts.
- **Text** is never below 20 px (CineUI's `textSize`).
- **Windows** (spec §2):
  - Press: Perfect ±0.12 s, Good ±0.25 s.
  - Mash: default 7 taps/s, 5 on touch, 1.6 to 2.5 s.
  - Direction: 0.9 s.
  - Hold: zone ±0.15 s.
  - Choice: 4 to 6 s, no answer means the default.
  - Reduce Motion widens Press, Direction and Hold windows ×1.3.
- **Points:** Perfect 3, Good 2, Win 2, Hit 2, Right 1, an answered Choice 1, everything else 0.
- **Grades:** S ≥ 90%, A ≥ 75%, B ≥ 55%, C ≥ 35%, otherwise D, of the most points possible on the path taken.
- **Test slot:** slot 2 only (slot 1 is the owner's). Snapshot it before a state-changing test and restore it exactly after (harness `snapshot.lua` / `restore.py`). Set the school clock to `21:30` before entering school, or classes log absences.
- **Studio test-tool quirk:** execute_luau resets the camera type at the end of every call. Start a cut and observe it in the **same** client call.
- **Commits:** `git -c user.name=Rello commit`, ending with the Co-Authored-By and Claude-Session lines. Commit only this plan's files (the working tree has other sessions' unrelated changes, e.g. CHANGELOG's 2.16.0 hunk).

## Spec deltas (implementation choices; recorded in doc 12 by Task 8)

1. **Judge location:** `ReplicatedStorage.Functions.CineJudge`, not `ReplicatedStorage.Cine.Judge`. The toolkit installer recreates `ReplicatedStorage.Cine` and would drop a child module.
2. **Branch table:** a prompt's branches are one table, `on = { <Outcome> = "<Segment>", Else = "<Segment>"? }`, instead of `onPerfect` / `onMiss` fields.
3. **Time base:** input times are seconds after the prompt **opens** on that client. Every window is measured from the open: `beat`, `dur`, `zoneAt`.
4. **Grades and skips:** a grade is recorded only when an interactive cut plays to its end. A skip ends the cut as it does today, records no grade and keeps the old best.
5. **Story beats:** a cut can turn the grade card off (`ShowGrade = false` in `Config.Cine`). The prologue does, because one prompt doesn't merit a report card.

---

## File structure

| File (dotted Studio path → mirror `tools/phase2-2250/live/<path>.luau`) | Responsibility | New / changed |
|---|---|---|
| `ReplicatedStorage.Functions.CineJudge` | Pure scoring, branching, team result, grade, graph validation, longest path | new |
| `ServerScriptService.Services.World.Cine` | Sessions: interactive messages (`Seg`, `Input`, `Where`, `Grade`), per-viewer scores, group decide, flags, grade save, rewards | changed |
| `ServerScriptService.Services.Quests.Quests` | `CineGrades` save block and accessor | changed |
| `StarterPlayer.StarterPlayerScripts.Controllers.CinePrompt` | One open prompt: input capture (ContextActionService, touch, test hook), close, and Input | new |
| `StarterPlayer.StarterPlayerScripts.Controllers.Cine` | Plays segments, opens prompts, solo branch, group `Branch` / `Segment`, grade card, `FlattenForTests` | changed |
| `StarterPlayer.StarterPlayerScripts.Controllers.Gui.CineUI` | Prompt visuals (Press, Mash, Direction, Hold, Choice), verdict, grade card | changed |
| `ReplicatedStorage.Config.Cine` | `Interactive`, `ShowGrade`, `Rewards`; the prologue's new length | changed |
| `ReplicatedStorage.Cinematics.Prologue` | `Def.Graph` + segmented `Build` with the "Here." Press | changed |
| `StarterPlayer.StarterPlayerScripts.Controllers.Gui.QuestJournal` | Best grade beside "Watch again" | changed |
| `ServerScriptService.Services.Studio.TestBridge` | `CineJudgeTest`, `CineGraphTest`, `CineQteTest` | changed |
| `tools/phase2-2250/harness/*` | `install.py`, `dump.py`, `bridge.py`, `client.py`, `start_play.lua`, `snapshot.lua`, `restore.py`, `analyze_paths.lua` | new |

---

### Task 1: Harness, mirror and the pure judge

**Files:**
- Create: `tools/phase2-2250/harness/install.py`, `dump.py`, `bridge.py`, `client.py`, `start_play.lua`, `snapshot.lua`, `restore.py`
- Create: `tools/phase2-2250/live/ReplicatedStorage.Functions.CineJudge.luau`
- Modify: `tools/phase2-2250/live/ServerScriptService.Services.Studio.TestBridge.luau` (add `CineJudgeTest`, `CineGraphTest`)

**Interfaces:**
- Produces (`CineJudge`, required as `require(ReplicatedStorage.Functions.CineJudge)`):
  - `Judge.Window(P, Opts?) -> number`: real seconds the prompt stays open. `Opts.Reduced` widens.
  - `Judge.Evaluate(P, Input) -> (Outcome: string, Points: number)`. Input is `{ Times = {number}, Pick = string?, PickAt = number?, Release = number?, Touch = boolean?, Reduced = boolean? }`, times in seconds after the open.
  - `Judge.Branch(P, Outcome) -> string?`
  - `Judge.Team(P, Outcomes: {string}) -> string`
  - `Judge.Grade(Points, Max) -> string?`
  - `Judge.Outcomes(P) -> {string}`
  - `Judge.Successors(Graph, Name) -> {string}`
  - `Judge.Follows(Graph, From, To) -> boolean`
  - `Judge.Validate(Graph) -> {string}` (errors)
  - `Judge.LongestPath(Graph) -> number`
  - Tables: `Judge.MAX[kind]`, `Judge.POINTS`, `Judge.RANK`, `Judge.GRADE_RANK`, `Judge.GRACE` (0.35).
- Graph shape: `{ start = "Name", segments = { [Name] = { len = number, next = "Name"?, prompt = P? } } }`.
- Prompt `P`, by kind:
  - Common: `kind`, `at` (segment seconds), `slow` (0 to 1, the world speed while it's open), `on = { [Outcome] = Segment, Else = Segment? }`, `flag` (optional; saves the outcome under that Decisions key).
  - Press: `beat`, `perfect`, `good`.
  - Mash: `dur`, `rate`, `touchRate`.
  - Direction: `dur`, `options = {"Left","Right",...}`, `answer`.
  - Hold: `zoneAt`, `zone`.
  - Choice: `dur`, `options = {{id, text}}`, `default`.

- [ ] **Step 1: Create the harness**

`tools/phase2-2250/harness/install.py` (installs mirror files as fresh ModuleScripts, keeping children; refuses on a parse error):

```python
"""Install mirror files into NH Combat Test (Edit mode) as fresh ModuleScripts.
usage: python -X utf8 -I install.py <file.luau> [...]   (paths to tools/phase2-2250/live/<dotted path>.luau)"""
import os, subprocess, sys
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
PLACE = "placeId: 98950102230473"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "_install.lua")

def bracket(src):
    n = 2
    while ("]" + "=" * n + "]") in src: n += 1
    return "[" + "=" * n + "[", "]" + "=" * n + "]"

parts = ["local Report = {}", "local Items = {}"]
for f in sys.argv[1:]:
    segs = os.path.basename(f)[:-len(".luau")].split(".")
    src = open(f, encoding="utf-8").read()
    o, c = bracket(src)
    parts.append("table.insert(Items, { Path = {%s}; Source = %s\n%s%s })" % (", ".join('"%s"' % s for s in segs), o, src, c))
parts.append(r'''
for _, It in Items do
	local Fn, Err = loadstring(It.Source)
	if not Fn then return "PARSE FAIL " .. table.concat(It.Path, ".") .. ": " .. tostring(Err) end
end
for _, It in Items do
	local Node = game:GetService(It.Path[1])
	for I = 2, #It.Path - 1 do
		local Next = Node:FindFirstChild(It.Path[I])
		if not Next then Next = Instance.new("Folder") Next.Name = It.Path[I] Next.Parent = Node end
		Node = Next
	end
	local Name = It.Path[#It.Path]
	local Old = Node:FindFirstChild(Name)
	local New = Instance.new("ModuleScript")
	New.Name = Name
	New.Source = It.Source
	New.Parent = Node
	if Old then for _, K in Old:GetChildren() do K.Parent = New end Old:Destroy() end
	table.insert(Report, New:GetFullName() .. " " .. #New.Source)
end
return table.concat(Report, "\n")''')
open(OUT, "w", encoding="utf-8").write("\n".join(parts))
r = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", PLACE, "Edit", "@" + OUT], capture_output=True, text=True, encoding="utf-8")
print(r.stdout.replace("\r", ""), r.stderr[-2000:] if r.returncode else "")
sys.exit(1 if "PARSE FAIL" in r.stdout or r.returncode else 0)
```

`tools/phase2-2250/harness/dump.py` (copies a live script's exact source into `pre/` and `live/`, in 25 KB chunks):

```python
"""Dump Studio scripts into the mirror. usage: python -X utf8 -I dump.py <dotted path> [...]"""
import os, subprocess, sys
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
PLACE = "placeId: 98950102230473"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = os.path.join(ROOT, "harness", "_dump.lua")
for path in sys.argv[1:]:
    text, c = "", 0
    while True:
        open(TMP, "w", encoding="utf-8").write(f'''local inst = game
for part in string.gmatch("{path}", "[^%.]+") do inst = inst:FindFirstChild(part) end
local s = inst.Source
local a = {c} * 25000 + 1
if a > #s then return "<<EOF>>" end
return s:sub(a, a + 24999) .. "<<CHUNK>>"''')
        out = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", PLACE, "Edit", "@" + TMP], capture_output=True, text=True, encoding="utf-8").stdout.replace("\r", "")
        if out.startswith("<<EOF>>"): break
        text += out[:out.rfind("<<CHUNK>>")]
        c += 1
    for sub in ("pre", "live"):
        os.makedirs(os.path.join(ROOT, sub), exist_ok=True)
        dest = os.path.join(ROOT, sub, path + ".luau")
        if sub == "pre" and os.path.exists(dest): continue  # pre/ is the first snapshot only
        open(dest, "w", encoding="utf-8", newline="").write(text)
    print(path, len(text.encode("utf-8")), "bytes")
```

`tools/phase2-2250/harness/bridge.py` (calls a TestBridge command in the game VM; `$P` becomes the first player's name):

```python
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
```

`tools/phase2-2250/harness/client.py` (runs a Luau file on the Client VM):

```python
"""usage: python -X utf8 -I client.py <file.lua>"""
import subprocess, sys
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
r = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", "placeId: 98950102230473", "Client", "@" + sys.argv[1]], capture_output=True, text=True, encoding="utf-8")
print(r.stdout.replace("\r", ""))
```

`tools/phase2-2250/harness/start_play.lua` (run on Server after starting Play: slot 2, 21:30, into school):

```lua
local B = game.ServerStorage.NHTestBridge
local P
local t0 = os.clock()
repeat task.wait(0.5) P = game.Players:GetPlayers()[1] until (P and P:GetAttribute("InMainMenu") ~= nil) or os.clock() - t0 > 30
task.wait(3)
B:Invoke("ChooseSlot", P.Name, 2)
B:Invoke("SetTime", "21:30")
B:Invoke("EnterSchool", P.Name)
local t1 = os.clock()
while P:GetAttribute("InMainMenu") and os.clock() - t1 < 15 do task.wait(0.25) end
task.wait(2)
return "inMenu " .. tostring(P:GetAttribute("InMainMenu"))
```

`tools/phase2-2250/harness/snapshot.lua` (Server: slot 2's quests, Yen and discipline as JSON; the output is saved to `tools/phase2-2250/harness/_slot2.json`):

```lua
local S = Instance.new("Script")
S.Source = [[
local P = game.Players:GetPlayers()[1]
local H = game:GetService("HttpService")
local SSS = game.ServerScriptService.Services
local Prof = require(SSS.Player.Data).GetProfile(P)
local Disc = require(SSS.School.Discipline).GetData(P)
script:SetAttribute("Json", H:JSONEncode({ Quests = Prof.Quests; Yen = Prof.Yen; Discipline = Disc }))
]]
S.Parent = game.ServerScriptService
task.wait(1)
local J = S:GetAttribute("Json")
S:Destroy()
return J
```

`tools/phase2-2250/harness/restore.py` (writes the snapshot back through a game-VM Script; same method as the Phase 1 restore):

```python
"""usage: python -X utf8 -I restore.py   (reads _slot2.json next to this file)"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
j = json.dumps(json.load(open(os.path.join(HERE, "_slot2.json"), encoding="utf-8")))
assert "]==]" not in j
lua = '''local J = [==[%s]==]
local S = Instance.new("Script")
S:SetAttribute("Json", J)
S.Source = [[
local H = game:GetService("HttpService")
local P = game.Players:GetPlayers()[1]
local ok, err = pcall(function()
	local SSS = game.ServerScriptService.Services
	local Data = require(SSS.Player.Data)
	local Disc = require(SSS.School.Discipline)
	local Snap = H:JSONDecode(script:GetAttribute("Json"))
	local Prof = Data.GetProfile(P)
	Prof.Quests = Snap.Quests
	require(SSS.Quests.Quests).SyncForCine(P)
	Data.UpdateState(P, { type = "UpdateYen"; amount = Snap.Yen - Prof.Yen })
	local ls = P:FindFirstChild("leaderstats") if ls and ls:FindFirstChild("Yen") then ls.Yen.Value = Prof.Yen end
	local D = Disc.GetData(P) for K, V in Snap.Discipline do D[K] = V end
	P:SetAttribute("DisciplineLevel", D.Level) P:SetAttribute("DisciplinePoints", D.Points) P:SetAttribute("DetentionsOwed", D.DetentionsOwed)
end)
script:SetAttribute("Out", ok and "restored" or ("ERR " .. tostring(err)))
]]
S.Parent = game.ServerScriptService
task.wait(1.5)
local r = S:GetAttribute("Out")
S:Destroy()
return tostring(r)''' % j
tmp = os.path.join(HERE, "_restore.lua")
open(tmp, "w", encoding="utf-8").write(lua)
print(subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", "placeId: 98950102230473", "Server", "@" + tmp], capture_output=True, text=True, encoding="utf-8").stdout)
```

- [ ] **Step 2: Snapshot the scripts this plan edits into `pre/` and `live/`, and back them up in Studio**

Run (Studio in Edit):

```bash
cd /e/Nightmare-Highschool/tools/phase2-2250/harness
python -X utf8 -I dump.py ServerScriptService.Services.World.Cine ServerScriptService.Services.Quests.Quests StarterPlayer.StarterPlayerScripts.Controllers.Cine StarterPlayer.StarterPlayerScripts.Controllers.Gui.CineUI ReplicatedStorage.Config.Cine ReplicatedStorage.Cinematics.Prologue StarterPlayer.StarterPlayerScripts.Controllers.Gui.QuestJournal ServerScriptService.Services.Studio.TestBridge
```

Expected: eight lines `<path> <bytes> bytes`, with sizes matching `#inst.Source` in Studio.

Then back them up in Studio (execute_luau, Edit):

```lua
local Root = game.ServerStorage:FindFirstChild("NH_Backup") or Instance.new("Folder", game.ServerStorage)
Root.Name = "NH_Backup"
local F = Root:FindFirstChild("Phase2_pre_20261118") or Instance.new("Folder", Root)
F.Name = "Phase2_pre_20261118"
local Paths = { "ServerScriptService.Services.World.Cine", "ServerScriptService.Services.Quests.Quests", "StarterPlayer.StarterPlayerScripts.Controllers.Cine",
	"StarterPlayer.StarterPlayerScripts.Controllers.Gui.CineUI", "ReplicatedStorage.Config.Cine", "ReplicatedStorage.Cinematics.Prologue",
	"StarterPlayer.StarterPlayerScripts.Controllers.Gui.QuestJournal", "ServerScriptService.Services.Studio.TestBridge" }
local Out = {}
for _, Path in Paths do
	local I = game
	for Part in Path:gmatch("[^%.]+") do I = I:FindFirstChild(Part) end
	local Name = Path:gsub("%.", "_")
	if not F:FindFirstChild(Name) then local C = I:Clone() C.Name = Name C.Parent = F end
	table.insert(Out, Name)
end
return table.concat(Out, "\n")
```

Expected: eight backup names. (Use today's date in the folder name if it isn't 2026-11-18.)

- [ ] **Step 3: Write the failing judge tests (TestBridge)**

In `tools/phase2-2250/live/ServerScriptService.Services.Studio.TestBridge.luau`, add before the line `-- Move the player next to a map part found by attribute`:

```lua
---| (2.25.0) interactive cuts: the judge and the graph |---

local function CineJudge() return require(game:GetService(`ReplicatedStorage`).Functions.CineJudge) end

-- every scoring rule on fixed inputs; returns { Passed, Failed = { "name: got X, want Y" } }
function Commands.CineJudgeTest()
	local J = CineJudge()
	local Press = { kind = `Press`; at = 1; beat = 0.6; slow = 0.3; on = { Perfect = `A`; Good = `A`; Miss = `B` } }
	local Mash = { kind = `Mash`; at = 0; dur = 2; rate = 7; touchRate = 5; on = { Win = `A`; Lose = `B` } }
	local Dir = { kind = `Direction`; at = 0; dur = 0.9; options = { `Left`, `Right` }; answer = `Left`; on = { Right = `A`; Wrong = `B` } }
	local Hold = { kind = `Hold`; at = 0; zoneAt = 1.2; zone = 0.15; on = { Hit = `A`; Miss = `B` } }
	local Choice = { kind = `Choice`; at = 0; dur = 5; options = { { id = `Ask`; text = `Who?` }, { id = `Nod`; text = `...` } }; default = `Nod`;
		on = { Ask = `A`; Nod = `B` } }
	local function taps(N, Dur) local T = {} for I = 1, N do T[I] = (I - 0.5) * Dur / N end return T end
	local Cases = {
		{ `press exact`, Press, { Times = { 0.6 } }, `Perfect`, 3 },
		{ `press +0.12 edge`, Press, { Times = { 0.72 } }, `Perfect`, 3 },
		{ `press +0.2`, Press, { Times = { 0.8 } }, `Good`, 2 },
		{ `press -0.25 edge`, Press, { Times = { 0.35 } }, `Good`, 2 },
		{ `press -0.3`, Press, { Times = { 0.3 } }, `Miss`, 0 },
		{ `press none`, Press, { Times = {} }, `Miss`, 0 },
		{ `press earliest counts`, Press, { Times = { 0.9, 0.6 } }, `Perfect`, 3 }, -- times are sorted: 0.6 is judged
		{ `press reduced widens`, Press, { Times = { 0.9 }; Reduced = true }, `Good`, 2 },
		{ `mash 14 of 14`, Mash, { Times = taps(14, 2) }, `Win`, 2 },
		{ `mash 13`, Mash, { Times = taps(13, 2) }, `Lose`, 0 },
		{ `mash touch 10`, Mash, { Times = taps(10, 2); Touch = true }, `Win`, 2 },
		{ `mash late taps ignored`, Mash, { Times = { 2.5, 2.6, 2.7 } }, `Lose`, 0 },
		{ `dir right`, Dir, { Pick = `Left`; PickAt = 0.5 }, `Right`, 1 },
		{ `dir wrong`, Dir, { Pick = `Right`; PickAt = 0.5 }, `Wrong`, 0 },
		{ `dir late`, Dir, { Pick = `Left`; PickAt = 1.2 }, `Wrong`, 0 },
		{ `dir none`, Dir, {}, `Wrong`, 0 },
		{ `hold hit`, Hold, { Times = { 0.1 }; Release = 1.3 }, `Hit`, 2 },
		{ `hold early`, Hold, { Times = { 0.1 }; Release = 0.9 }, `Miss`, 0 },
		{ `hold never down`, Hold, { Release = 1.2 }, `Miss`, 0 },
		{ `choice picked`, Choice, { Pick = `Ask`; PickAt = 2 }, `Ask`, 1 },
		{ `choice timeout`, Choice, {}, `Nod`, 0 },
		{ `choice bogus id`, Choice, { Pick = `Hack`; PickAt = 1 }, `Nod`, 0 },
	}
	local Out = { Passed = 0; Failed = {} }
	for _, C in Cases do
		local Ok, O, Pts = pcall(J.Evaluate, C[2], C[3])
		if Ok and O == C[4] and Pts == C[5] then Out.Passed += 1
		else table.insert(Out.Failed, `{C[1]}: got {tostring(O)}/{tostring(Pts)}, want {C[4]}/{C[5]}`) end
	end
	-- branch, team, grade
	local function check(Name, Got, Want) if Got == Want then Out.Passed += 1 else table.insert(Out.Failed, `{Name}: got {tostring(Got)}, want {tostring(Want)}`) end end
	check(`branch perfect`, J.Branch(Press, `Perfect`), `A`)
	check(`branch miss`, J.Branch(Press, `Miss`), `B`)
	check(`branch else`, J.Branch({ on = { Else = `Z` } }, `Whatever`), `Z`)
	check(`team majority`, J.Team(Press, { `Miss`, `Miss`, `Good` }), `Miss`)
	check(`team tie -> better`, J.Team(Press, { `Perfect`, `Miss` }), `Perfect`)
	check(`team empty -> miss`, J.Team(Press, {}), `Miss`)
	check(`team choice tie -> earlier option`, J.Team(Choice, { `Nod`, `Ask` }), `Ask`)
	check(`grade S`, J.Grade(9, 10), `S`)
	check(`grade A`, J.Grade(3, 4), `A`)
	check(`grade B`, J.Grade(11, 20), `B`)
	check(`grade C`, J.Grade(7, 20), `C`)
	check(`grade D`, J.Grade(1, 10), `D`)
	check(`grade none`, J.Grade(0, 0), nil)
	check(`max press`, J.MAX.Press, 3)
	return Out
end

-- graph validation on a good graph and on broken ones; returns { Passed, Failed }
function Commands.CineGraphTest()
	local J = CineJudge()
	local Out = { Passed = 0; Failed = {} }
	local function expect(Name, Graph, WantErrs: boolean, Needle: string?)
		local Errs = J.Validate(Graph)
		local Text = table.concat(Errs, " | ")
		local Ok = (#Errs > 0) == WantErrs and (Needle == nil or Text:find(Needle, 1, true) ~= nil)
		if Ok then Out.Passed += 1 else table.insert(Out.Failed, `{Name}: errors [{Text}]`) end
	end
	local function good()
		return { start = `A`; segments = {
			A = { len = 3; prompt = { kind = `Press`; at = 1; beat = 0.6; slow = 0.3; on = { Perfect = `B`; Good = `B`; Miss = `C` } } };
			B = { len = 2; next = `D` }; C = { len = 2; next = `D` };
			D = { len = 3; prompt = { kind = `Mash`; at = 0.5; dur = 1.6; rate = 7; slow = 0.5; on = { Win = `E`; Lose = `E` } } };
			E = { len = 1 } } }
	end
	expect(`good graph`, good(), false)
	local G1 = good() G1.start = `Nope`
	expect(`bad start`, G1, true, `start`)
	local G2 = good() G2.segments.B.next = `Ghost`
	expect(`unknown next`, G2, true, `Ghost`)
	local G3 = good() G3.segments.E.next = `A`
	expect(`loop`, G3, true, `loop`)
	local G4 = good() G4.segments.A.prompt.on.Miss = nil
	expect(`missing branch`, G4, true, `no branch for Miss`)
	local G5 = good() G5.segments.A.len = 1.2
	expect(`tail too short`, G5, true, `tail`)
	local G6 = good() G6.segments.A.next = `B`
	expect(`prompt with next`, G6, true, `no next`)
	-- the longest path: A (1 + 2/0.3) + C 2 + D (0.5 + 2.5/0.5) + E 1 = 7.67 + 2 + 5.5 + 1
	local L = J.LongestPath(good())
	if math.abs(L - (1 + 2 / 0.3 + 2 + 0.5 + 2.5 / 0.5 + 1)) < 0.01 then Out.Passed += 1 else table.insert(Out.Failed, `longest path {L}`) end
	if J.Follows(good(), `B`, `D`) and not J.Follows(good(), `A`, `D`) then Out.Passed += 1 else table.insert(Out.Failed, `follows`) end
	return Out
end
```

- [ ] **Step 4: Install TestBridge and run the tests to see them fail**

```bash
cd /e/Nightmare-Highschool/tools/phase2-2250/harness
python -X utf8 -I install.py ../live/ServerScriptService.Services.Studio.TestBridge.luau
```

Start Play (MCP `start_stop_play` true), then:

```bash
python -X utf8 -I bridge.py CineJudgeTest
```

Expected: `{"ok":false,"result":"...Functions is not a valid member...CineJudge..."}` or similar. The module doesn't exist yet. Stop Play.

- [ ] **Step 5: Write `CineJudge`**

`tools/phase2-2250/live/ReplicatedStorage.Functions.CineJudge.luau`:

```lua
--[[
	CineJudge (shared, 2.25.0). ReplicatedStorage.Functions.CineJudge. Pure functions, no state: the client uses them to
	branch a solo cut the instant you press, the server to score every viewer and pick a group's branch. Spec:
	docs/expansion/12-Interactive-Cutscenes.md.

	A prompt P (in a cut's Def.Graph segment): kind = "Press" | "Mash" | "Direction" | "Hold" | "Choice"; at (segment
	seconds when it opens); slow (world speed while open); on = { [Outcome] = Segment; Else = Segment? }; flag?
	  Press      beat (s after open), perfect = 0.12, good = 0.25        -> Perfect | Good | Miss
	  Mash       dur = 2, rate = 7 (taps/s), touchRate = 5               -> Win | Lose
	  Direction  dur = 0.9, options = {"Left","Right",...}, answer       -> Right | Wrong
	  Hold       zoneAt (s after open), zone = 0.15                      -> Hit | Miss
	  Choice     dur = 5, options = {{ id, text }}, default              -> the chosen id (or default)
	Input: { Times = {s after open}, Pick?, PickAt?, Release?, Touch?, Reduced? } (Reduce Motion widens Press, Direction,
	Hold by 1.3).
]]

local Judge = {}

Judge.POINTS = { Perfect = 3; Good = 2; Win = 2; Hit = 2; Right = 1 }
Judge.MAX = { Press = 3; Mash = 2; Direction = 1; Hold = 2; Choice = 1 }
Judge.RANK = { Perfect = 6; Good = 5; Win = 5; Hit = 5; Right = 4; Miss = 1; Lose = 1; Wrong = 1 }
Judge.MISS = { Press = `Miss`; Mash = `Lose`; Direction = `Wrong`; Hold = `Miss` }
Judge.GRADE_RANK = { S = 5; A = 4; B = 3; C = 2; D = 1 }
Judge.WIDEN = 1.3
Judge.GRACE = 0.35

local function widen(Opts): number
	return if Opts and Opts.Reduced then Judge.WIDEN else 1
end

function Judge.Window(P, Opts): number
	local W = widen(Opts)
	if P.kind == `Press` then return (P.beat or 0.6) + (P.good or 0.25) * W + 0.1
	elseif P.kind == `Mash` then return P.dur or 2
	elseif P.kind == `Direction` then return (P.dur or 0.9) * W
	elseif P.kind == `Hold` then return (P.zoneAt or 1) + (P.zone or 0.15) * W + 0.3
	elseif P.kind == `Choice` then return P.dur or 5 end
	return 0
end

function Judge.Evaluate(P, Input): (string, number)
	Input = Input or {}
	local W = widen(Input)
	local Window = Judge.Window(P, Input)
	local Times = table.clone(Input.Times or {})
	table.sort(Times)
	local Kind = P.kind
	local Outcome
	if Kind == `Press` then
		local First = nil
		for _, T in Times do if T >= -0.05 and T <= Window then First = T break end end
		if not First then Outcome = `Miss` else
			local D = math.abs(First - (P.beat or 0.6))
			Outcome = if D <= (P.perfect or 0.12) * W + 1e-6 then `Perfect` elseif D <= (P.good or 0.25) * W + 1e-6 then `Good` else `Miss`
		end
	elseif Kind == `Mash` then
		local Dur = P.dur or 2
		local N = 0
		for _, T in Times do if T >= 0 and T <= Dur then N += 1 end end
		local Rate = if Input.Touch then (P.touchRate or 5) else (P.rate or 7)
		Outcome = if N >= Rate * Dur - 1e-6 then `Win` else `Lose`
	elseif Kind == `Direction` then
		local InTime = Input.Pick ~= nil and (Input.PickAt or 0) <= Window
		local Valid = InTime and table.find(P.options or {}, Input.Pick) ~= nil
		Outcome = if Valid and Input.Pick == P.answer then `Right` else `Wrong`
	elseif Kind == `Hold` then
		local Down, Up = Times[1], Input.Release
		if Down == nil or Up == nil or Up < Down then Outcome = `Miss`
		else Outcome = if math.abs(Up - (P.zoneAt or 1)) <= (P.zone or 0.15) * W + 1e-6 then `Hit` else `Miss` end
	elseif Kind == `Choice` then
		if Input.Pick ~= nil and (Input.PickAt or 0) <= Window then
			for _, O in P.options or {} do
				if O.id == Input.Pick then return Input.Pick, 1 end
			end
		end
		return P.default, 0
	else
		return `Miss`, 0
	end
	return Outcome, Judge.POINTS[Outcome] or 0
end

function Judge.Branch(P, Outcome: string): string?
	local On = P.on or {}
	return On[Outcome] or On.Else
end

function Judge.Outcomes(P): { string }
	local K = P.kind
	if K == `Press` then return { `Perfect`, `Good`, `Miss` }
	elseif K == `Mash` then return { `Win`, `Lose` }
	elseif K == `Direction` then return { `Right`, `Wrong` }
	elseif K == `Hold` then return { `Hit`, `Miss` }
	elseif K == `Choice` then
		local L = {}
		for _, O in P.options or {} do table.insert(L, O.id) end
		return L
	end
	return {}
end

-- a Choice tie goes to the earlier option; other ties to the better outcome
local function rank(P, Outcome: string): number
	if P.kind == `Choice` then
		for I, O in P.options or {} do if O.id == Outcome then return 100 - I end end
		return 0
	end
	return Judge.RANK[Outcome] or 0
end

function Judge.Team(P, Outcomes: { string }): string
	if #Outcomes == 0 then return if P.kind == `Choice` then P.default else Judge.MISS[P.kind] or `Miss` end
	local Count = {}
	for _, O in Outcomes do Count[O] = (Count[O] or 0) + 1 end
	local Best, BestN, BestRank = nil, -1, -1
	for O, N in Count do
		local R = rank(P, O)
		if N > BestN or (N == BestN and R > BestRank) then Best, BestN, BestRank = O, N, R end
	end
	return Best
end

function Judge.Grade(Points: number, Max: number): string?
	if Max <= 0 then return nil end
	local S = Points / Max
	return if S >= 0.9 then `S` elseif S >= 0.75 then `A` elseif S >= 0.55 then `B` elseif S >= 0.35 then `C` else `D`
end

---| the graph |---

function Judge.Successors(Graph, Name: string): { string }
	local Node = Graph.segments[Name]
	if not Node then return {} end
	if Node.prompt then
		local L, Seen = {}, {}
		for _, O in Judge.Outcomes(Node.prompt) do
			local T = Judge.Branch(Node.prompt, O)
			if T and not Seen[T] then Seen[T] = true table.insert(L, T) end
		end
		return L
	end
	return if Node.next then { Node.next } else {}
end

-- To is From, or reached from it through next links only (no prompt in between)
function Judge.Follows(Graph, From: string?, To: string): boolean
	local Seen = {}
	local N = From
	while N and not Seen[N] do
		if N == To then return true end
		Seen[N] = true
		local Node = Graph.segments[N]
		N = Node and not Node.prompt and Node.next or nil
	end
	return false
end

-- real seconds of a segment: at normal speed until its prompt opens, the tail at the prompt's slow speed
local function realLen(Node): number
	local P = Node.prompt
	if not P then return Node.len end
	return P.at + (Node.len - P.at) / (P.slow or 1)
end

function Judge.LongestPath(Graph): number
	local Memo = {}
	local function cost(N, Depth)
		if Depth > 64 then return 0 end
		if Memo[N] then return Memo[N] end
		local Node = Graph.segments[N]
		if not Node then return 0 end
		local Best = 0
		for _, S in Judge.Successors(Graph, N) do Best = math.max(Best, cost(S, Depth + 1)) end
		Memo[N] = realLen(Node) + Best
		return Memo[N]
	end
	return cost(Graph.start, 0)
end

function Judge.Validate(Graph): { string }
	local Errs = {}
	local Segs = Graph and Graph.segments
	if typeof(Segs) ~= `table` then return { `no segments` } end
	if not Segs[Graph.start or ``] then table.insert(Errs, `start "{tostring(Graph.start)}" is not a segment`) end
	for Name, Node in Segs do
		if typeof(Node.len) ~= `number` or Node.len <= 0 then table.insert(Errs, `{Name}: len must be > 0`) end
		local P = Node.prompt
		if P then
			if Node.next then table.insert(Errs, `{Name}: a segment with a prompt branches, so it has no next`) end
			if not Judge.MAX[P.kind] then
				table.insert(Errs, `{Name}: unknown prompt kind {tostring(P.kind)}`)
			else
				if typeof(P.at) ~= `number` or P.at < 0 or P.at >= (Node.len or 0) then table.insert(Errs, `{Name}: prompt.at must be inside the segment`) end
				local Tail = ((Node.len or 0) - (P.at or 0)) / (P.slow or 1)
				local Need = Judge.Window(P, { Reduced = true }) + 0.6
				if Tail < Need then table.insert(Errs, string.format(`%s: the prompt's tail lasts %.2f s real time; it needs %.2f (window + hold)`, Name, Tail, Need)) end
				if P.kind == `Choice` then
					local Has = false
					for _, O in P.options or {} do if O.id == P.default then Has = true end end
					if not Has then table.insert(Errs, `{Name}: Choice default must be one of its options`) end
				end
				if P.kind == `Direction` and not table.find(P.options or {}, P.answer) then table.insert(Errs, `{Name}: Direction answer must be one of its options`) end
				for _, O in Judge.Outcomes(P) do
					local T = Judge.Branch(P, O)
					if not T then table.insert(Errs, `{Name}: no branch for {O}`)
					elseif not Segs[T] then table.insert(Errs, `{Name}: branch {O} -> unknown segment {T}`) end
				end
			end
		elseif Node.next and not Segs[Node.next] then
			table.insert(Errs, `{Name}: next -> unknown segment {Node.next}`)
		end
	end
	local State = {}
	local function walk(N, Depth)
		if Depth > 64 then table.insert(Errs, `path deeper than 64 segments`) return end
		if State[N] == 1 then table.insert(Errs, `loop through {N}`) return end
		if State[N] == 2 then return end
		State[N] = 1
		for _, S in Judge.Successors(Graph, N) do if Segs[S] then walk(S, Depth + 1) end end
		State[N] = 2
	end
	if Segs[Graph.start or ``] then walk(Graph.start, 0) end
	return Errs
end

return Judge
```

- [ ] **Step 6: Install and run the tests to see them pass**

Studio in Edit:

```bash
python -X utf8 -I install.py ../live/ReplicatedStorage.Functions.CineJudge.luau
```

Start Play, then:

```bash
python -X utf8 -I bridge.py CineJudgeTest
python -X utf8 -I bridge.py CineGraphTest
```

Expected: `"Failed":[]` in both, with `Passed` 36 and 9. Stop Play.

- [ ] **Step 7: Commit**

```bash
cd /e/Nightmare-Highschool
git add tools/phase2-2250/harness/*.py tools/phase2-2250/harness/*.lua tools/phase2-2250/pre tools/phase2-2250/live
git -c user.name=Rello commit -m "2.25.0 (1/8): CineJudge, the interactive-cut judge, with TestBridge tests and the phase 2 harness"
```

(The harness's `_*.lua` / `_slot2.json` scratch files are rewritten on every run; add `tools/phase2-2250/harness/_*` to `.gitignore` in this commit.)

---

### Task 2: Save block `CineGrades` (Quests)

**Files:**
- Modify: `tools/phase2-2250/live/ServerScriptService.Services.Quests.Quests.luau` (the block normaliser near `Q.Decisions = ...`, and the accessors after `Shared.SyncForCine`)
- Modify: `tools/phase2-2250/live/ServerScriptService.Services.Studio.TestBridge.luau` (`CineGrades` command)

**Interfaces:**
- Produces: `Quests.CineGrades(Player) -> { [CutId]: { Best: string, Points: number, Max: number } }?`. It's the live table, so the writer then calls `Quests.SyncForCine(Player)`.

- [ ] **Step 1: Failing test.** Add to TestBridge:

```lua
function Commands.CineGrades(PlayerName: string)
	return DeepCopy(QuestsService().CineGrades(Players:FindFirstChild(PlayerName)))
end
```

Install TestBridge, Play, then run `python -X utf8 -I bridge.py CineGrades $P`. Expected: `ok:false`, "attempt to call a nil value". Stop Play.

- [ ] **Step 2: Implement.** In Quests, right after the line `Q.Decisions = if typeof(Q.Decisions) == \`table\` then Q.Decisions else {} -- (2.24.0) Decision objectives`, add:

```lua
	Q.CineGrades = if typeof(Q.CineGrades) == `table` then Q.CineGrades else {} -- (2.25.0) best grade per interactive cut
```

After `function Shared.SyncForCine(Player: Player) Local.Sync(Player) end`, add:

```lua
-- (2.25.0) the best grade per interactive cut ({ [CutId] = { Best, Points, Max } }); Services.World.Cine is the only writer
function Shared.CineGrades(Player: Player): { [string]: any }?
	local Q = Local.Get(Player)
	return Q and Q.CineGrades
end
```

- [ ] **Step 3: Verify.** Install Quests and TestBridge in Edit, Play, run `harness/start_play.lua` on the Server VM, then `bridge.py CineGrades $P`. Expected: `{"ok":true,"result":[]}`. Stop Play.

- [ ] **Step 4: Commit** (`2.25.0 (2/8): Quests.CineGrades save block`).

---

### Task 3: Server sessions run interactive cuts

**Files:**
- Modify: `tools/phase2-2250/live/ServerScriptService.Services.World.Cine.luau`
- Modify: `tools/phase2-2250/live/ServerScriptService.Services.Studio.TestBridge.luau` (`CineQteTest`)
- Modify: `tools/phase2-2250/live/ReplicatedStorage.Config.Cine.luau` (document `Interactive`, `ShowGrade`, `Rewards`, `GradeCard`)

**Interfaces:**
- Consumes: `CineJudge` (Task 1) and `Quests.CineGrades` / `Quests.Decide` / `Quests.SyncForCine`.
- Produces (messages on `ReplicatedStorage.NHCine`):
  - Server → client:
    - `Play` gains `Interactive: boolean` and `Solo: boolean`.
    - `{ Kind="Branch", Session, Seg, Next, StartAt, Outcome, Team }` (group).
    - `{ Kind="Segment", Session, Name, StartAt }` (the reply to `Where`).
    - `{ Kind="Grade", Session, Grade, Points, Max, Perfects, Show }`.
  - Client → server:
    - `{ Kind="Seg", Session, Name, At }`: the segment it now plays (server time).
    - `{ Kind="Input", Session, Seg, Opened, Times, Pick, PickAt, Release, Touch, Reduced }`.
    - `{ Kind="Where", Session }`.
    - `{ Kind="Grade", Session }`: asked at the end of the final segment.
  - Test hook: `Cine.QteSelfTestForTests(Player) -> table`.

- [ ] **Step 1: Failing test.** Add to TestBridge:

```lua
-- the group decide, the solo path check, Where and the grade on the real session code, with stand-in viewers
function Commands.CineQteTest(PlayerName: string)
	return DeepCopy(CineService().QteSelfTestForTests(Players:FindFirstChild(PlayerName)))
end
```

Install, Play, run `start_play.lua`, then `bridge.py CineQteTest $P`. Expected: an "attempt to call a nil value" error. Stop Play.

- [ ] **Step 2: Config.** In `Config.Cine`, extend the header comment and the table:

```lua
--   Interactive  true: the cut's module has a Def.Graph (segments and prompts); Length is its longest path
--                (CineJudge.LongestPath) plus the grade card
--   ShowGrade    false: no grade card at the end (a story beat with one prompt); the grade is still kept
--   Rewards      { S = yen, A = yen, B = yen }: a bonus by grade, on the first viewing only
```

and add `GradeCard = 2.5;` (seconds the grade card holds) after `SkipGrace`.

- [ ] **Step 3: Server code.** In `World.Cine`:

(a) Below `local Config = require(ReplicatedStorage.Config.Cine)`:

```lua
local Judge = require(ReplicatedStorage.Functions.CineJudge)
```

(b) Add after `Local.SetMark`:

```lua
---| interactive cuts (2.25.0): the graph lives in the cut module (ReplicatedStorage.Cinematics.<Id>.Graph) |---

function Local.GraphOf(CutId: string)
	local Ok, Def = pcall(function() return require(ReplicatedStorage.Cinematics[CutId]) end)
	return if Ok and typeof(Def) == `table` and typeof(Def.Graph) == `table` then Def.Graph else nil
end

function Local.Flag(Player: Player, Flag: string, Outcome: string)
	pcall(function() Quests().Decide(Player, Flag, Outcome) end)
end

function Local.Score(V, Seg: string, P, Outcome: string, Points: number)
	V.Judged[Seg] = { Outcome = Outcome }
	V.Points += Points
	V.Max += Judge.MAX[P.kind] or 0
	if Outcome == `Perfect` then V.Perfects += 1 end
end

function Local.CleanInput(M, P)
	local Window = Judge.Window(P, { Reduced = M.Reduced == true })
	local Times = {}
	if typeof(M.Times) == `table` then
		for I, T in M.Times do
			if I > 64 then break end
			if typeof(T) == `number` and T == T and T >= -0.5 and T <= Window + 0.5 then table.insert(Times, T) end
		end
	end
	return { Times = Times; Pick = if typeof(M.Pick) == `string` then M.Pick else nil; PickAt = tonumber(M.PickAt);
		Release = tonumber(M.Release); Touch = M.Touch == true; Reduced = M.Reduced == true }
end

-- a group's prompt is decided when everyone still watching has answered, or at its deadline (missing = a miss)
function Local.Decide(S, Seg: string)
	S.Decided = S.Decided or {}
	if S.Decided[Seg] then return end
	local P = S.Graph.segments[Seg].prompt
	local Outs = {}
	for Player, V in S.Viewers do
		if not V.Ended then
			if not V.Judged[Seg] then
				local O, Pts = Judge.Evaluate(P, {})
				Local.Score(V, Seg, P, O, Pts)
			end
			table.insert(Outs, V.Judged[Seg].Outcome)
		end
	end
	if #Outs == 0 then return end
	S.Decided[Seg] = true
	local Team = Judge.Team(P, Outs)
	local Next = Judge.Branch(P, Team)
	local StartAt = workspace:GetServerTimeNow() + 0.25
	S.Seg, S.SegStartAt = Next, StartAt
	for Player, V in S.Viewers do
		if not V.Ended then
			if P.flag then Local.Flag(Player, P.flag, Team) end
			Local.Send(Player, { Kind = `Branch`; Session = S.Id; Seg = Seg; Next = Next; StartAt = StartAt;
				Outcome = V.Judged[Seg].Outcome; Team = Team })
		end
	end
	Local.ArmPrompt(S)
end

function Local.TryDecide(S, Seg: string)
	for _, V in S.Viewers do
		if not V.Ended and not V.Judged[Seg] then return end
	end
	Local.Decide(S, Seg)
end

-- group: from the current segment, follow next links to the next prompt and set its deadline on the shared clock
function Local.ArmPrompt(S)
	if not (S.Graph and S.Group) then return end
	local N, At = S.Seg, S.SegStartAt
	local Seen = {}
	while N and not Seen[N] do
		Seen[N] = true
		local Node = S.Graph.segments[N]
		if not Node then return end
		if Node.prompt then
			local P, Seg = Node.prompt, N
			local Deadline = At + P.at + Judge.Window(P, { Reduced = true }) + Judge.GRACE
			task.delay(math.max(0, Deadline - workspace:GetServerTimeNow()), function()
				if Sessions[S.Id] then Local.Decide(S, Seg) end
			end)
			return
		end
		At += Node.len
		N = Node.next
	end
end

function Local.OnInput(S, Player: Player, V, M)
	if not S.Graph or typeof(M.Seg) ~= `string` then return end
	local Node = S.Graph.segments[M.Seg]
	local P = Node and Node.prompt
	if not P or V.Judged[M.Seg] then return end
	if not Judge.Follows(S.Graph, S.Seg, M.Seg) then return end
	local Outcome, Points = Judge.Evaluate(P, Local.CleanInput(M, P))
	Local.Score(V, M.Seg, P, Outcome, Points)
	if S.Group then
		Local.TryDecide(S, M.Seg)
	else
		V.Judged[M.Seg].Next = Judge.Branch(P, Outcome)
		if P.flag then Local.Flag(Player, P.flag, Outcome) end
	end
end

-- solo: the client says where it is now (it branches on its own); only real moves along the graph are accepted
function Local.OnSeg(S, Player: Player, V, M)
	if not S.Graph or S.Group or typeof(M.Name) ~= `string` or not S.Graph.segments[M.Name] then return end
	local Cur = S.Seg
	local Ok = Judge.Follows(S.Graph, Cur, M.Name)
	if not Ok then
		-- through a prompt: only after it was judged (the server's own verdict says which way)
		local J = V.Judged[Cur]
		if J then
			for _, T in Judge.Successors(S.Graph, Cur) do
				if Judge.Follows(S.Graph, T, M.Name) then Ok = true end
			end
			if Ok and J.Next and not Judge.Follows(S.Graph, J.Next, M.Name) then
				warn(`[Cine] {Player.Name}: solo branch {Cur} -> {M.Name}, but the server judged {J.Next}`)
			end
		end
	end
	if not Ok then return end
	S.Seg = M.Name
	S.SegStartAt = tonumber(M.At) or workspace:GetServerTimeNow()
end

-- the grade, once, when the client reaches the end of the cut; saved as the best, and the first viewing pays a bonus
function Local.SendGrade(S, Player: Player, V)
	if V.Graded then return end
	V.Graded = true
	local Cut = Config.Cuts[S.CutId]
	local Grade = Judge.Grade(V.Points, V.Max)
	if Grade then
		pcall(function()
			local G = Quests().CineGrades(Player)
			if not G then return end
			local Old = G[S.CutId]
			if not Old or (Judge.GRADE_RANK[Grade] or 0) > (Judge.GRADE_RANK[Old.Best] or 0) then
				G[S.CutId] = { Best = Grade; Points = V.Points; Max = V.Max }
				Quests().SyncForCine(Player)
			end
		end)
		local First = not V.SeenBefore and not S.Skippable
		local Bonus = First and Cut.Rewards and Cut.Rewards[Grade]
		if typeof(Bonus) == `number` and Bonus > 0 then
			pcall(function()
				require(ServerScriptService.Services.Player.Data).UpdateState(Player, { type = `UpdateYen`; amount = Bonus })
			end)
		end
	end
	Local.Send(Player, { Kind = `Grade`; Session = S.Id; Grade = Grade; Points = V.Points; Max = V.Max; Perfects = V.Perfects;
		Show = Cut.ShowGrade ~= false })
end
```

(c) In `Shared.Play`, give each viewer score fields. Change `S.Viewers[Player] = { SeenBefore = SeenBefore; StartedBefore = StartedBefore; Release = Release }` to:

```lua
		S.Viewers[Player] = { SeenBefore = SeenBefore; StartedBefore = StartedBefore; Release = Release;
			Points = 0; Max = 0; Perfects = 0; Judged = {} }
```

After `Sessions[S.Id] = S` add:

```lua
	S.Graph = Local.GraphOf(CutId)
	if S.Graph then S.Seg = S.Graph.start end
```

After `local StartAt = ...` add `S.SegStartAt = StartAt`. In the Play message table add `Interactive = S.Graph ~= nil; Solo = not S.Group;`. After the loop that sends Play, before `if S.Group then Local.BroadcastVotes(S) end`, add `Local.ArmPrompt(S)`.

(d) In `Local.OnMessage`, inside the `if Message.Kind == \`Began\` ... end` chain, add these branches before the final `end`:

```lua
	elseif Message.Kind == `Input` then
		Local.OnInput(S, Player, V, Message)
	elseif Message.Kind == `Seg` then
		Local.OnSeg(S, Player, V, Message)
	elseif Message.Kind == `Where` then
		if S.Graph then Local.Send(Player, { Kind = `Segment`; Session = S.Id; Name = S.Seg; StartAt = S.SegStartAt }) end
	elseif Message.Kind == `Grade` then
		if S.Graph then Local.SendGrade(S, Player, V) end
```

Raise `RATE` from 12 to 40 (mash prompts send presses in one `Input`, but `Seg` and `Where` add messages; 40 a second still blocks floods).

(e) Test hook, after `Shared.SessionsForTests`:

```lua
-- (2.25.0) the group decide, the solo path check, Where and the grade on the real code, with stand-in viewers (the MCP
-- starts one-player Plays). Nothing is saved: messages to stand-ins are recorded, the real player's grades and
-- decisions are put back.
function Shared.QteSelfTestForTests(Player: Player)
	local Out = {}
	local function fake(Name: string) return setmetatable({ Name = Name; Parent = game; UserId = -1 }, { __tostring = function() return Name end }) end
	local A, B, C = Player, fake(`StandInB`), fake(`StandInC`)
	local Graph = { start = `A`; segments = {
		A = { len = 3; prompt = { kind = `Press`; at = 1; beat = 0.6; slow = 0.3; on = { Perfect = `B`; Good = `B`; Miss = `C` } } };
		B = { len = 2; next = `D` }; C = { len = 2; next = `D` };
		D = { len = 3; prompt = { kind = `Mash`; at = 0.5; dur = 1.6; rate = 7; slow = 0.5; on = { Win = `E`; Lose = `E` } } };
		E = { len = 1 } } }
	local Sent = {}
	local RealSend = Local.Send
	Local.Send = function(P, M) table.insert(Sent, { To = tostring(P); M = M }) end
	local SavedGrades = table.clone((Quests().CineGrades(Player)) or {})
	local function viewer() return { SeenBefore = false; Points = 0; Max = 0; Perfects = 0; Judged = {} } end
	local function msg(Kind, To) for I = #Sent, 1, -1 do if Sent[I].M.Kind == Kind and (To == nil or Sent[I].To == To) then return Sent[I].M end end return nil end
	local Ok, Err = pcall(function()
		-- 1. two viewers: a Perfect and a Miss tie -> the better outcome (Perfect) -> B; each keeps their own points
		local S = { Id = `qte1`; CutId = `Prologue`; Group = true; Graph = Graph; Seg = `A`; SegStartAt = 0; Viewers = { [A] = viewer(); [B] = viewer() } }
		Sessions[S.Id] = S
		Local.OnInput(S, A, S.Viewers[A], { Seg = `A`; Times = { 0.6 } })
		Out.WaitsForEveryone = msg(`Branch`) == nil
		Local.OnInput(S, B, S.Viewers[B], { Seg = `A`; Times = {} })
		local Br = msg(`Branch`, tostring(A))
		Out.TieBranch = Br and Br.Next
		Out.PointsA, Out.PointsB = S.Viewers[A].Points, S.Viewers[B].Points
		Out.SegAfter = S.Seg
		-- 2. Where tells a lost client the current segment
		Sent = {}
		Local.OnMessage(A, { Kind = `Where`; Session = `qte1` })
		local W = msg(`Segment`)
		Out.Where = W and W.Name
		-- 3. three viewers, two miss: majority -> C; a missing answer at the deadline counts as a miss
		Sent = {}
		local S3 = { Id = `qte3`; CutId = `Prologue`; Group = true; Graph = Graph; Seg = `A`; SegStartAt = 0;
			Viewers = { [A] = viewer(); [B] = viewer(); [C] = viewer() } }
		Sessions[S3.Id] = S3
		Local.OnInput(S3, A, S3.Viewers[A], { Seg = `A`; Times = { 0.8 } })
		Local.OnInput(S3, B, S3.Viewers[B], { Seg = `A`; Times = { 0.1 } })
		Local.Decide(S3, `A`) -- C never answered: the deadline
		local B3 = msg(`Branch`, tostring(A))
		Out.MajorityBranch = B3 and B3.Next
		-- 4. solo: input then a path report the server agrees with; a skip past an unjudged prompt is refused
		Sent = {}
		local S4 = { Id = `qte4`; CutId = `Prologue`; Group = false; Graph = Graph; Seg = `A`; SegStartAt = 0; Viewers = { [A] = viewer() } }
		Sessions[S4.Id] = S4
		Local.OnSeg(S4, A, S4.Viewers[A], { Name = `D`; At = 1 })
		Out.SoloSkipRefused = S4.Seg == `A`
		Local.OnInput(S4, A, S4.Viewers[A], { Seg = `A`; Times = { 0.62 } })
		Local.OnSeg(S4, A, S4.Viewers[A], { Name = `B`; At = 2 })
		Out.SoloMovedToB = S4.Seg == `B`
		Local.OnSeg(S4, A, S4.Viewers[A], { Name = `D`; At = 4 })
		Out.SoloNextChain = S4.Seg == `D`
		local Taps = {}
		for I = 1, 12 do Taps[I] = I * 0.13 end
		Local.OnInput(S4, A, S4.Viewers[A], { Seg = `D`; Times = Taps })
		Out.MashOutcome = S4.Viewers[A].Judged.D.Outcome
		-- 5. the grade: Perfect (3/3) + Mash Win (2/2) = 5/5 -> S
		Sent = {}
		Local.SendGrade(S4, A, S4.Viewers[A])
		local G = msg(`Grade`)
		Out.Grade = G and G.Grade
		Out.GradeSaved = ((Quests().CineGrades(Player)) or {}).Prologue ~= nil
	end)
	Local.Send = RealSend
	for _, Id in { `qte1`, `qte3`, `qte4` } do Sessions[Id] = nil end
	local G = Quests().CineGrades(Player)
	if G then table.clear(G) for K, V in SavedGrades do G[K] = V end pcall(function() Quests().SyncForCine(Player) end) end
	if not Ok then Out.Error = tostring(Err) end
	return Out
end
```

Note: `Local.OnMessage` checks the rate and the session table. The stand-in test calls it only for `Where` with the real player.

- [ ] **Step 4: Run the test to see it pass.** Install `World.Cine`, `Config.Cine` and TestBridge in Edit. Then Play, `start_play.lua`, and `bridge.py CineQteTest $P`.

Expected: `WaitsForEveryone:true, TieBranch:"B", PointsA:3, PointsB:0, SegAfter:"B", Where:"B", MajorityBranch:"C", SoloSkipRefused:true, SoloMovedToB:true, SoloNextChain:true, MashOutcome:"Win", Grade:"S", GradeSaved:true`, and no `Error`.

The 12 taps over the 1.6 s mash: 7 × 1.6 = 11.2 needed, so 12 is a Win. The Mash `D` got 2 points, so the total is 5/5.

Also re-run `bridge.py CineVoteTest $P`; it must still pass as in 2.24.0. Stop Play.

- [ ] **Step 5: Commit** (`2.25.0 (3/8): Cine server judges interactive cuts`).

---

### Task 4: `CinePrompt`, opening a prompt and capturing input

**Files:**
- Create: `tools/phase2-2250/live/StarterPlayer.StarterPlayerScripts.Controllers.CinePrompt.luau`

**Interfaces:**
- Consumes: `CineJudge.Window`, `CineJudge.Evaluate`, and the CineUI prompt API from Task 5 (`PromptShow`, `PromptHit`, `PromptMeter`, `PromptHold`, `PromptHide`). All are called in `pcall`, so this task works before Task 5 lands.
- Produces:
  - `CinePrompt.Open(P, Opts: { Reduced: boolean, Touch: boolean }, OnClose: (Input) -> ())`: the window closes on its own, and Press, Direction, Choice and Hold close early once answered.
  - `CinePrompt.Cancel()` and `CinePrompt.IsOpen() -> boolean`.
- Studio test hook: when `RunService:IsStudio()`, a `BindableEvent` named `NHCineTestInput` in ReplicatedStorage feeds `{ Kind = "Down" | "Up" | "Pick", Id? }` into the open prompt.

- [ ] **Step 1: Failing test.** Save this client test as `tools/phase2-2250/harness/t_prompt.lua`. It opens a Press prompt on the real module, feeds a press 0.6 s in through the hook, and reads the Input:

```lua
local RS = game:GetService("ReplicatedStorage")
local Prompt = require(game.Players.LocalPlayer.PlayerScripts.Controllers.CinePrompt)
local Judge = require(RS.Functions.CineJudge)
local B = RS:FindFirstChild("NHCineTestInput") or Instance.new("BindableEvent")
B.Name = "NHCineTestInput"
B.Parent = RS
local Results = {}
local function run(P, Feed)
	local Got = nil
	Prompt.Open(P, { Reduced = false; Touch = false }, function(Input) Got = Input end)
	Feed()
	local T0 = os.clock()
	while not Got and os.clock() - T0 < 6 do task.wait(0.03) end
	return Got and table.pack(Judge.Evaluate(P, Got)) or { "no close" }
end
local r1 = run({ kind = "Press"; at = 0; beat = 0.6; on = {} }, function() task.wait(0.6) B:Fire({ Kind = "Down" }) end)
local r2 = run({ kind = "Direction"; at = 0; dur = 0.9; options = { "Left", "Right" }; answer = "Right"; on = {} }, function() task.wait(0.3) B:Fire({ Kind = "Pick"; Id = "Right" }) end)
local r3 = run({ kind = "Mash"; at = 0; dur = 1.0; rate = 7; on = {} }, function() for i = 1, 9 do task.wait(0.1) B:Fire({ Kind = "Down" }) end end)
local r4 = run({ kind = "Hold"; at = 0; zoneAt = 0.8; zone = 0.15; on = {} }, function() task.wait(0.1) B:Fire({ Kind = "Down" }) task.wait(0.7) B:Fire({ Kind = "Up" }) end)
local r5 = run({ kind = "Press"; at = 0; beat = 0.6; on = {} }, function() end)
B:Destroy()
return string.format("press %s | dir %s | mash %s | hold %s | press-none %s", tostring(r1[1]), tostring(r2[1]), tostring(r3[1]), tostring(r4[1]), tostring(r5[1]))
```

Play, `start_play.lua`, then `python -X utf8 -I client.py t_prompt.lua`. Expected: a "CinePrompt is not a valid member" error. Stop Play.

- [ ] **Step 2: Implement** `Controllers.CinePrompt`:

```lua
--[[
	CinePrompt (client, 2.25.0). Controllers.CinePrompt: one open prompt at a time during an interactive cut
	(Controllers.Cine opens it, Gui.CineUI draws it). Input is captured above combat (ContextActionService, sunk) so a
	prompt's key never swings a fist. Times are seconds after the prompt opened (CineJudge's time base).
	  Press / Mash / Hold: E, Space, gamepad A, or the big seal on screen (tap / click)
	  Direction: A D W S, the arrow keys, the D-pad, or the seals on screen
	  Choice: 1 2 3, the D-pad (left / up / right), or the buttons on screen
]]

local ContextActionService = game:GetService(`ContextActionService`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)

local Judge = require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`CineJudge`))

local Shared = {}
local Local = {}
local ACTION = `NHCinePrompt`
local Open = nil

local PRIMARY = { Enum.KeyCode.E, Enum.KeyCode.Space, Enum.KeyCode.ButtonA }
local DIRS = {
	[Enum.KeyCode.A] = `Left`; [Enum.KeyCode.Left] = `Left`; [Enum.KeyCode.DPadLeft] = `Left`;
	[Enum.KeyCode.D] = `Right`; [Enum.KeyCode.Right] = `Right`; [Enum.KeyCode.DPadRight] = `Right`;
	[Enum.KeyCode.W] = `Up`; [Enum.KeyCode.Up] = `Up`; [Enum.KeyCode.DPadUp] = `Up`;
	[Enum.KeyCode.S] = `Down`; [Enum.KeyCode.Down] = `Down`; [Enum.KeyCode.DPadDown] = `Down`;
}
local CHOICE_KEYS = { [Enum.KeyCode.One] = 1; [Enum.KeyCode.Two] = 2; [Enum.KeyCode.Three] = 3;
	[Enum.KeyCode.DPadLeft] = 1; [Enum.KeyCode.DPadUp] = 2; [Enum.KeyCode.DPadRight] = 3 }

local function UI() return require(script.Parent:WaitForChild(`Gui`):WaitForChild(`CineUI`)) end

function Local.Now(): number return os.clock() - Open.T0 end

function Local.Close()
	local O = Open
	if not O then return end
	Open = nil
	ContextActionService:UnbindAction(ACTION)
	for _, Cn in O.Conns do Cn:Disconnect() end
	local Outcome = Judge.Evaluate(O.P, O.Input)
	pcall(function() UI().PromptHide(Outcome) end)
	task.spawn(O.OnClose, O.Input)
end

function Local.Press(Down: boolean)
	local O = Open
	if not O then return end
	local T = Local.Now()
	local K = O.P.kind
	if K == `Press` then
		if Down then
			table.insert(O.Input.Times, T)
			pcall(function() UI().PromptHit() end)
			Local.Close()
		end
	elseif K == `Mash` then
		if Down then
			table.insert(O.Input.Times, T)
			O.Count += 1
			pcall(function() UI().PromptHit() UI().PromptMeter(math.min(1, O.Count / O.Need)) end)
		end
	elseif K == `Hold` then
		if Down and #O.Input.Times == 0 then
			table.insert(O.Input.Times, T)
			pcall(function() UI().PromptHold(true) end)
		elseif not Down and #O.Input.Times > 0 and not O.Input.Release then
			O.Input.Release = T
			Local.Close()
		end
	end
end

function Local.Pick(Id: string)
	local O = Open
	if not O or O.Input.Pick then return end
	O.Input.Pick = Id
	O.Input.PickAt = Local.Now()
	pcall(function() UI().PromptHit() end)
	Local.Close()
end

function Local.OnAction(_, State: Enum.UserInputState, Obj: InputObject)
	local O = Open
	if not O then return Enum.ContextActionResult.Pass end
	local Down = State == Enum.UserInputState.Begin
	local Up = State == Enum.UserInputState.End
	local K = O.P.kind
	if K == `Direction` then
		local Dir = DIRS[Obj.KeyCode]
		if Down and Dir and table.find(O.P.options or {}, Dir) then Local.Pick(Dir) end
	elseif K == `Choice` then
		local I = CHOICE_KEYS[Obj.KeyCode]
		local Opt = I and O.P.options and O.P.options[I]
		if Down and Opt then Local.Pick(Opt.id) end
	elseif table.find(PRIMARY, Obj.KeyCode) then
		if Down then Local.Press(true) elseif Up then Local.Press(false) end
	end
	return Enum.ContextActionResult.Sink
end

function Shared.Open(P, Opts, OnClose: (any) -> ())
	Shared.Cancel()
	local Touch = Opts.Touch == true
	local Rate = if Touch then (P.touchRate or 5) else (P.rate or 7)
	Open = { P = P; T0 = os.clock(); OnClose = OnClose; Conns = {}; Count = 0; Need = math.max(1, math.ceil(Rate * (P.dur or 2)));
		Input = { Times = {}; Touch = Touch; Reduced = Opts.Reduced == true } }
	local Keys = {}
	if P.kind == `Direction` then for K in DIRS do table.insert(Keys, K) end
	elseif P.kind == `Choice` then for K in CHOICE_KEYS do table.insert(Keys, K) end
	else Keys = table.clone(PRIMARY) end
	ContextActionService:BindActionAtPriority(ACTION, Local.OnAction, false, Enum.ContextActionPriority.High.Value + 50, table.unpack(Keys))
	pcall(function()
		UI().PromptShow(P, { Reduced = Opts.Reduced == true; Touch = Touch; OnTap = Local.Press; OnPick = Local.Pick })
	end)
	local Mine = Open
	task.delay(Judge.Window(P, Open.Input), function() if Open == Mine then Local.Close() end end)
	if RunService:IsStudio() then
		local Hook = ReplicatedStorage:FindFirstChild(`NHCineTestInput`)
		if Hook and Hook:IsA(`BindableEvent`) then
			table.insert(Open.Conns, Hook.Event:Connect(function(M)
				if typeof(M) ~= `table` then return end
				if M.Kind == `Down` then Local.Press(true) elseif M.Kind == `Up` then Local.Press(false)
				elseif M.Kind == `Pick` and typeof(M.Id) == `string` then Local.Pick(M.Id) end
			end))
		end
	end
end

function Shared.Cancel()
	local O = Open
	if not O then return end
	Open = nil
	ContextActionService:UnbindAction(ACTION)
	for _, Cn in O.Conns do Cn:Disconnect() end
	pcall(function() UI().PromptHide(nil) end)
end

function Shared.IsOpen(): boolean return Open ~= nil end

return Shared
```

- [ ] **Step 3: Verify.** Install `Controllers.CinePrompt` in Edit, then Play, `start_play.lua`, and `client.py t_prompt.lua`.

Expected: `press Perfect | dir Right | mash Win | hold Hit | press-none Miss` (9 taps in 1.0 s ≥ 7). On a slow machine one of the timing cases can land a Good; re-run once. Two different results in a row is a failure. Stop Play.

- [ ] **Step 4: Commit** (`2.25.0 (4/8): CinePrompt captures prompt input`).

---

### Task 5: CineUI draws prompts and the grade card

**Files:**
- Modify: `tools/phase2-2250/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.CineUI.luau` (add after `Shared.Ring`; extend the API header)

**Interfaces:**
- Produces:
  - `CineUI.PromptShow(P, Opts: { Reduced, Touch, OnTap: (Down: boolean) -> (), OnPick: (Id: string) -> () })`
  - `CineUI.PromptHit()`
  - `CineUI.PromptMeter(Fraction: number)`
  - `CineUI.PromptHold(Down: boolean)`
  - `CineUI.PromptHide(Outcome: string?)`
  - `CineUI.GradeCard(Grade: string, Perfects: number, Prompts: number, Seconds: number)`

- [ ] **Step 1: Failing check.** `tools/phase2-2250/harness/t_ui.lua` (client):

```lua
local UI = require(game.Players.LocalPlayer.PlayerScripts.Controllers.Gui.CineUI)
UI.Show({ Skippable = false })
UI.PromptShow({ kind = "Press"; beat = 0.6; on = {} }, { Reduced = false; Touch = false; OnTap = function() end; OnPick = function() end })
task.wait(0.4)
local G = game.Players.LocalPlayer.PlayerGui.NHCineUI
local P = G:FindFirstChild("Prompt")
return "prompt layer " .. tostring(P ~= nil) .. " key " .. tostring(P and P:FindFirstChild("Key") ~= nil)
```

Note: requiring the controller from execute_luau makes a **copy**, but this copy builds into the same PlayerGui, so the check works. Play → `client.py t_ui.lua`. Expected: an error, `PromptShow` is nil. Stop Play.

- [ ] **Step 2: Implement.** Append to CineUI, after `Shared.Ring`:

```lua
---| prompts (2.25.0): drawn from the kit's seal, panel and frame art |---

local VERDICT = { Perfect = `PERFECT`; Good = `GOOD`; Miss = `MISS`; Win = `BROKE FREE`; Lose = `TOO SLOW`; Hit = `PERFECT`; Right = `DODGED`; Wrong = `MISSED` }
local GOOD_OUTCOME = { Perfect = true; Good = true; Win = true; Hit = true; Right = true }
local CRIMSON = Color3.fromRGB(200, 40, 60)

local function keyGlyph(Touch: boolean): string
	if Touch then return `TAP` end
	if UserInputService.GamepadEnabled and not UserInputService.KeyboardEnabled then return `A` end
	return `E`
end

local function sealButton(Name: string, Parent: Instance, Pos: UDim2, Size: number, Text: string, TextBase: number)
	local S = new(`ImageButton`, { Name = Name; BackgroundTransparency = 1; Image = Img.Seal; ImageColor3 = C.Wax; AutoButtonColor = false;
		AnchorPoint = Vector2.new(0.5, 0.5); Position = Pos; Size = UDim2.fromOffset(Size, Size); ZIndex = 52 }, Parent)
	new(`TextLabel`, { Name = `Glyph`; BackgroundTransparency = 1; Font = Theme.Fonts.Title; Text = Text; TextColor3 = C.Gold;
		TextSize = textSize(TextBase); Size = UDim2.fromScale(1, 1); ZIndex = 53 }, S)
	return S
end

local function tapWired(B: GuiButton, OnTap: (boolean) -> ())
	B.InputBegan:Connect(function(I)
		if I.UserInputType == Enum.UserInputType.Touch or I.UserInputType == Enum.UserInputType.MouseButton1 then OnTap(true) end
	end)
	B.InputEnded:Connect(function(I)
		if I.UserInputType == Enum.UserInputType.Touch or I.UserInputType == Enum.UserInputType.MouseButton1 then OnTap(false) end
	end)
end

function Shared.PromptShow(P, Opts)
	if not Ui then Local.Build() end
	Ui.Gui.Enabled = true
	if Ui.Prompt then Ui.Prompt:Destroy() end
	local L = new(`CanvasGroup`, { Name = `Prompt`; BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0.5);
		Position = UDim2.fromScale(0.5, 0.6); Size = UDim2.fromOffset(560, 300); GroupTransparency = 1; ZIndex = 50 }, Ui.Gui)
	Ui.Prompt = L
	local Parts = {}
	Ui.PromptParts = Parts
	local Kind = P.kind
	local Label = new(`TextLabel`, { Name = `Label`; BackgroundTransparency = 1; Font = Theme.Fonts.Title; TextColor3 = C.Chalk; Text = ``;
		TextSize = textSize(22); AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.fromScale(0.5, 0.8); Size = UDim2.new(1, 0, 0, 34); ZIndex = 52 }, L)
	Parts.Label = Label
	if Kind == `Press` or Kind == `Mash` or Kind == `Hold` then
		local Key = sealButton(`Key`, L, UDim2.fromScale(0.5, 0.4), 108, keyGlyph(Opts.Touch), 30)
		Parts.Key = Key
		tapWired(Key, Opts.OnTap)
		Label.Text = if Kind == `Mash` then `MASH` elseif Kind == `Hold` then `HOLD, RELEASE ON THE SEAL` else (P.label or `NOW`)
		if Kind == `Press` or Kind == `Hold` then
			-- a faint seal where the closing seal lands; the closing seal shrinks onto it on the beat (Press) or, once the
			-- key is held, at the release mark (Hold)
			new(`ImageLabel`, { Name = `Zone`; BackgroundTransparency = 1; Image = Img.Seal; ImageColor3 = C.Gold; ImageTransparency = 0.8;
				AnchorPoint = Vector2.new(0.5, 0.5); Position = Key.Position; Size = UDim2.fromOffset(124, 124); ZIndex = 51 }, L)
			local Ring = new(`ImageLabel`, { Name = `Ring`; BackgroundTransparency = 1; Image = Img.Seal; ImageColor3 = C.Gold; ImageTransparency = 0.5;
				AnchorPoint = Vector2.new(0.5, 0.5); Position = Key.Position; Size = UDim2.fromOffset(264, 264); ZIndex = 51 }, L)
			Parts.Ring = Ring
			Parts.RingAt = if Kind == `Press` then (P.beat or 0.6) else (P.zoneAt or 1)
			if Kind == `Press` then tween(Ring, Parts.RingAt, { Size = UDim2.fromOffset(124, 124) }, Enum.EasingStyle.Linear) end
		else
			local Bar = new(`ImageLabel`, { Name = `Meter`; Image = Img.PanelBg; ImageColor3 = C.PanelTint; BackgroundColor3 = C.Ink; BackgroundTransparency = 0.2;
				BorderSizePixel = 0; ScaleType = Enum.ScaleType.Stretch; AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.fromScale(0.5, 0.93);
				Size = UDim2.fromOffset(340, 20); ZIndex = 52 }, L)
			Parts.Fill = new(`ImageLabel`, { Name = `Fill`; Image = Img.PanelBg; ImageColor3 = C.Gold; BackgroundTransparency = 1;
				ScaleType = Enum.ScaleType.Stretch; Size = UDim2.fromScale(0, 1); ZIndex = 53 }, Bar)
			Kit.Slice(`FrameThin`, C.GoldDeep, { Name = `Rim`; SliceScale = 0.2; ZIndex = 54; Parent = Bar })
		end
	elseif Kind == `Direction` then
		local Options = P.options or {}
		local KEY = { Left = `A`; Right = `D`; Up = `W`; Down = `S` }
		for I, Dir in Options do
			local X = (I - 0.5) / #Options
			local Glyph = if Opts.Touch then string.upper(Dir) else KEY[Dir] or Dir
			local S = sealButton(`Dir_{Dir}`, L, UDim2.fromScale(X, 0.4), 96, Glyph, if Opts.Touch then 20 else 30)
			S.Activated:Connect(function() Opts.OnPick(Dir) end)
			new(`TextLabel`, { Name = `Word`; BackgroundTransparency = 1; Font = Theme.Fonts.Body; Text = string.upper(Dir); TextColor3 = C.Chalk;
				TextSize = textSize(20); AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, 0, 1, 4); Size = UDim2.fromOffset(120, 24); ZIndex = 53 }, S)
		end
		Label.Text = P.label or `DODGE`
	elseif Kind == `Choice` then
		local Options = P.options or {}
		for I, O in Options do
			local B = Kit.Button({ text = `{I}   {O.text}`; style = `default`; onClick = function() Opts.OnPick(O.id) end;
				Size = UDim2.fromOffset(500, 50); Parent = L })
			B.AnchorPoint = Vector2.new(0.5, 0)
			B.Position = UDim2.new(0.5, 0, 0, 10 + (I - 1) * 58)
			B.ZIndex = 52
		end
		Label.Position = UDim2.fromScale(0.5, 0.86)
		Label.Text = ``
		local Bar = new(`ImageLabel`, { Name = `Timer`; Image = Img.PanelBg; ImageColor3 = C.Gold; BackgroundTransparency = 1; ScaleType = Enum.ScaleType.Stretch;
			AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.fromScale(0.5, 0.95); Size = UDim2.fromOffset(500, 6); ZIndex = 52 }, L)
		tween(Bar, P.dur or 5, { Size = UDim2.fromOffset(0, 6) }, Enum.EasingStyle.Linear)
	end
	local Reduced = Opts.Reduced or reduced()
	if Reduced then L.GroupTransparency = 0 else
		local Sc = new(`UIScale`, { Scale = 0.9 }, L)
		tween(Sc, 0.14, { Scale = 1 }, Enum.EasingStyle.Back)
		tween(L, 0.12, { GroupTransparency = 0 })
	end
end

function Shared.PromptHit()
	local Parts = Ui and Ui.PromptParts
	pcall(Kit.PlaySound, `Stamp`, 0.4)
	local Key = Parts and Parts.Key
	if Key and not reduced() then
		Key.Size = UDim2.fromOffset(124, 124)
		tween(Key, 0.18, { Size = UDim2.fromOffset(108, 108) }, Enum.EasingStyle.Back)
	end
end

function Shared.PromptMeter(Fraction: number)
	local Fill = Ui and Ui.PromptParts and Ui.PromptParts.Fill
	if Fill then Fill.Size = UDim2.fromScale(math.clamp(Fraction, 0, 1), 1) end
end

function Shared.PromptHold(Down: boolean)
	local Parts = Ui and Ui.PromptParts
	if Down and Parts and Parts.Ring then
		tween(Parts.Ring, Parts.RingAt, { Size = UDim2.fromOffset(124, 124) }, Enum.EasingStyle.Linear)
	end
end

function Shared.PromptHide(Outcome: string?)
	if not (Ui and Ui.Prompt) then return end
	local L = Ui.Prompt
	Ui.Prompt = nil
	local Label = Ui.PromptParts and Ui.PromptParts.Label
	if Outcome and Label and VERDICT[Outcome] then
		Label.Text = VERDICT[Outcome]
		Label.TextColor3 = if GOOD_OUTCOME[Outcome] then C.Gold else CRIMSON
		task.delay(0.35, function() tween(L, 0.3, { GroupTransparency = 1 }) end)
		task.delay(0.8, function() L:Destroy() end)
	else
		L:Destroy()
	end
end

function Shared.GradeCard(Grade: string, Perfects: number, Prompts: number, Seconds: number)
	local Sub = if Prompts > 0 then `{Perfects} of {Prompts} perfect` else nil
	Shared.Card(`GRADE {Grade}`, Sub, Seconds)
end
```

Also add `PromptShow, PromptHit, PromptMeter, PromptHold, PromptHide, GradeCard` to the API line in the header comment. In `Shared.Hide`, add at the top: `if Ui and Ui.Prompt then Ui.Prompt:Destroy() Ui.Prompt = nil end`.

- [ ] **Step 3: Verify.** Install CineUI in Edit. Then Play, `start_play.lua`, and `client.py t_ui.lua`. Expected: `prompt layer true key true`.

Take a screenshot with MCP `screen_capture`. The Press seal and the closing gold seal must use the kit's seal art, the label must be legible, and nothing may overlap the letterbox. Repeat `t_ui.lua` with `kind = "Choice"` (options `{ {id="a", text="Nobody answered."}, {id="b", text="Who's Mira Holt?"} }`, default `"a"`, dur 5) and take a screenshot: kit buttons, numbered, with the timer bar under them. Then run `UI.Hide()` from a client call. Stop Play.

- [ ] **Step 4: Commit** (`2.25.0 (5/8): CineUI draws prompts and the grade card`).

---

### Task 6: The director plays segments, prompts and branches

**Files:**
- Modify: `tools/phase2-2250/live/StarterPlayer.StarterPlayerScripts.Controllers.Cine.luau`

**Interfaces:**
- Consumes: `CineJudge` (Task 1), `CinePrompt` (Task 4), CineUI `GradeCard` (Task 5), and the server messages (Task 3).
- Produces:
  - A cut module may export `Def.Graph`. `Def.Build(Ctx)` then returns `{ segments = { [Name] = { shots, events } }, grade? }`, and events are timed from their segment's start.
  - A cut without `Graph` plays as before (one segment, `Main`).
  - `Shared.FlattenForTests(Built, Graph, Path: {string}) -> { shots, events }` (Task 7's analysis).
  - The player attribute `NHCinePrompt = <kind>` while a prompt is open (tests watch it).

- [ ] **Step 1: Failing test.** `tools/phase2-2250/harness/t_director.lua` (client) plays the test cut `ReplicatedStorage.Cinematics.__QteTest` (installed in step 3). It feeds a Perfect press through the hook and checks the path and the grade, all in one call (the camera-reset quirk):

```lua
local RS = game:GetService("ReplicatedStorage")
local P = game.Players.LocalPlayer
local R = RS.NHCine
local Hook = RS:FindFirstChild("NHCineTestInput") or Instance.new("BindableEvent")
Hook.Name = "NHCineTestInput"
Hook.Parent = RS
local Log, Grade, Sess = {}, nil, nil
local c = R.OnClientEvent:Connect(function(m)
	if m.Kind == "Play" then Sess = m.Session table.insert(Log, "Play interactive=" .. tostring(m.Interactive)) end
	if m.Kind == "Grade" then Grade = m.Grade end
end)
local OutSeg = {}
local c2 = P:GetAttributeChangedSignal("NHCinePrompt"):Connect(function()
	local K = P:GetAttribute("NHCinePrompt")
	if K == "Press" then task.wait(0.6) Hook:Fire({ Kind = "Down" }) end
	if K == "Mash" then for i = 1, 14 do task.wait(0.1) Hook:Fire({ Kind = "Down" }) end end
	table.insert(Log, "prompt " .. tostring(K))
end)
R:FireServer({ Kind = "Replay"; Id = "__QteTest" })
local t0 = os.clock()
while os.clock() - t0 < 25 and workspace.CurrentCamera.CameraType ~= Enum.CameraType.Custom or os.clock() - t0 < 2 do task.wait(0.1) end
c:Disconnect() c2:Disconnect() Hook:Destroy()
return table.concat(Log, " | ") .. " | grade " .. tostring(Grade) .. " | path " .. tostring(P:GetAttribute("NHCinePath"))
```

The test cut `tools/phase2-2250/live/ReplicatedStorage.Cinematics.__QteTest.luau` (Studio-only; it stays installed for regression runs). Its graph is the Task 3 graph; the shots are holds on the Hall set's `HallCam` marks:

```lua
-- A test cut for the interactive director (TestBridge / harness only; never in a quest). The Task 3 graph.
local Def = { Set = `Hall` }
Def.Graph = { start = `A`; segments = {
	A = { len = 3; prompt = { kind = `Press`; at = 1; beat = 0.6; slow = 0.3; on = { Perfect = `B`; Good = `B`; Miss = `C` } } };
	B = { len = 2; next = `D` }; C = { len = 2; next = `D` };
	D = { len = 3; prompt = { kind = `Mash`; at = 0.5; dur = 1.6; rate = 7; slow = 0.5; on = { Win = `E`; Lose = `E` } } };
	E = { len = 1 } } }
function Def.Build(Ctx)
	local function hold(Name, Dur, Dist)
		return { name = Name; dur = Dur; subject = Ctx.Mark(`HallLook`);
			camera = { keys = { { t = 0; pos = Ctx.Pos(`HallCam`); look = Ctx.Pos(`HallLook`); lens = 35 },
				{ t = Dur; pos = Ctx.Pos(`HallCam`) + Ctx.CF(`HallCam`).LookVector * Dist; look = Ctx.Pos(`HallLook`); lens = 35 } } }; noise = false }
	end
	return { segments = {
		A = { shots = { hold(`A`, 3, 1) } }; B = { shots = { hold(`B`, 2, 2) } }; C = { shots = { hold(`C`, 2, 2) } };
		D = { shots = { hold(`D`, 3, 1) } }; E = { shots = { hold(`E`, 1, 0.5) } } } }
end
return Def
```

with `Config.Cine.Cuts.__QteTest = { Name = \`QTE test\`; Length = 30; Set = \`Hall\`; Replay = true; Interactive = true }`.

Before a replay works, slot 2 needs `Seen`: `bridge.py CineMark $P '"__QteTest"' '"Seen"'`. Clear it afterwards with `CineMark $P '"__QteTest"' nil`.

Install `__QteTest` and `Config.Cine`, then Play, `start_play.lua`, `snapshot.lua` (save the output to `_slot2.json`), the `CineMark` command, and `client.py t_director.lua`. Expected: the cut plays as one segment, never shows a prompt, and the grade is `nil` (the director doesn't know graphs yet). Stop Play.

- [ ] **Step 2: Implement.** Changes to `Controllers.Cine`:

(a) Modules, after `local Kit = ...`:

```lua
local Judge = require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`CineJudge`))
local function Prompt() return require(script.Parent:WaitForChild(`CinePrompt`)) end
local function touch(): boolean
	local UIS = game:GetService(`UserInputService`)
	return UIS.TouchEnabled and not UIS.KeyboardEnabled
end
```

(b) Replace everything in `Local.Play` from `Cut.Events = Built.events or {}` down to (and including) the final `send({ Kind = \`Began\` ...})` with:

```lua
	-- (2.25.0) every cut is a graph of segments; a plain cut is one segment, Main
	Cut.Built = Built
	Cut.Interactive = typeof(Def.Graph) == `table`
	Cut.Graph = if Cut.Interactive then Def.Graph else { start = `Main`; segments = { Main = { len = Local.ShotsLength(Built.shots or {}) } } }
	Built.segments = Built.segments or { Main = { shots = Built.shots; events = Built.events } }
	Cut.Solo = not Cut.Group
	Cut.Scale = 1
	Cut.PromptCount = 0
	Local.HideLive(Cut)
	if not CameraLease.Take(LEASE, function()
		if Cut.Live and Current == Cut then return true end
		return Cut.EndingAt ~= nil and os.clock() - Cut.EndingAt < 3
	end) then
		Local.Finish(Cut, `NoCamera`)
		return
	end
	Gui.Show({ Skippable = Message.Skippable; Group = Cut.Group; Votes = Message.Votes; Need = Message.Need })
	Gui.Veil(1, 0)
	-- a group cut runs on the server's clock (late joiners start mid-way through the first segment)
	local Start = if Cut.Group then math.max(0, workspace:GetServerTimeNow() - (Message.StartAt or 0)) else 0
	Local.PlaySegment(Cut, Cut.Graph.start, Start)
	if not Built.keepBlack then Gui.Veil(0, if Start > 0 then 0.2 else 0.8) end
	send({ Kind = `Began`; Session = Cut.Session; At = Message.StartAt })
end

function Local.ShotsLength(Shots): number
	local T = 0
	for _, S in Shots do T += S.dur or 0 end
	return T
end

-- one segment: its shots on the toolkit's player, its events on the segment's clock, its prompt when its time comes
function Local.PlaySegment(Cut, Name: string, Start: number?)
	if not Cut.Live then return end
	local Seg = Cut.Built.segments[Name]
	local Node = Cut.Graph.segments[Name]
	if not (Seg and Node) then warn(`[Cine] no segment {Name}`) Local.Finish(Cut, `Error`) return end
	if Cut.Handle then pcall(function() Cut.Handle:stop() end) end -- (no camera type restore: the next shot cuts in this frame)
	pcall(function() Prompt().Cancel() end)
	Player:SetAttribute(`NHCinePrompt`, nil)
	Cut.Seg = Name
	Cut.Prompt = nil
	Cut.Scale = 1
	Cut.Path = (Cut.Path or ``) .. (if Cut.Path then `>` else ``) .. Name
	Player:SetAttribute(`NHCinePath`, Cut.Path) -- tests read the path taken
	Start = Start or 0
	Cut.Events = table.clone(Seg.events or {})
	table.sort(Cut.Events, function(A, B) return (A.t or 0) < (B.t or 0) end)
	Cut.Fired = 1
	while Cut.Fired <= #Cut.Events and (Cut.Events[Cut.Fired].t or 0) < Start - 0.05 do
		local E = Cut.Events[Cut.Fired]
		Cut.Fired += 1
		if E.pose or E.look or E.walk or E.place then pcall(Local.Fire, Cut, E) end -- catch the actors up, no stale lines
	end
	local Def = Cut.Def
	local Lib = CineLib()
	local Last = os.clock()
	Cut.Handle = Lib.play({ name = `{Cut.Id}.{Name}`; letterbox = LETTERBOX; grade = Cut.Built.grade; shots = Local.Strip(Cut, Seg.shots) }, {
		start = Start; overlay = false; autoStop = false;
		onFrame = function(H)
			if not Cut.Live or Cut.Seg ~= Name then return end
			local Now = os.clock()
			local Dt = math.min(Now - Last, 0.1) * Cut.Scale
			Last = Now
			Cut.Clock = H.time
			if Cut.ClockWas then game:GetService(`Lighting`).ClockTime = Def.Clock end
			while Cut.Fired <= #Cut.Events and (Cut.Events[Cut.Fired].t or 0) <= H.time do
				local E = Cut.Events[Cut.Fired]
				Cut.Fired += 1
				local Ok2, Err = pcall(Local.Fire, Cut, E)
				if not Ok2 then warn(`[Cine] event: {Err}`) end
			end
			local Cam = workspace.CurrentCamera
			for _, A in Cut.Actors do pcall(Local.StepActor, A, Dt, H.time, Cam) end
			if Node.prompt and not Cut.Prompt and H.time >= Node.prompt.at then Local.OpenPrompt(Cut, Name, Node.prompt) end
		end;
		onDone = function() if Cut.Live and Cut.Seg == Name then Local.SegmentDone(Cut, Name) end end;
	})
	Cut.Handle._restoreCameraType = nil
	if Cut.Interactive then send({ Kind = `Seg`; Session = Cut.Session; Name = Name; At = workspace:GetServerTimeNow() - Start }) end
end

function Local.SegmentDone(Cut, Name: string)
	local Node = Cut.Graph.segments[Name]
	if Node.prompt then
		-- the tail ran out before the branch was known (a slow server in a group cut): ask where the cut is
		if not Cut.Solo then send({ Kind = `Where`; Session = Cut.Session }) end
		return
	end
	if Node.next then Local.PlaySegment(Cut, Node.next) return end
	task.spawn(Local.EndGraph, Cut)
end

function Local.OpenPrompt(Cut, SegName: string, P)
	Cut.Prompt = { Seg = SegName }
	Cut.PromptCount += 1
	Cut.Scale = P.slow or 1
	pcall(function() Cut.Handle:setTimeScale(Cut.Scale) end)
	Player:SetAttribute(`NHCinePrompt`, P.kind)
	local Reduced = Cut.Ctx and Cut.Ctx.Reduced or false
	local Opened = workspace:GetServerTimeNow()
	Prompt().Open(P, { Reduced = Reduced; Touch = touch() }, function(Input)
		Player:SetAttribute(`NHCinePrompt`, nil)
		if not Cut.Live or Cut.Seg ~= SegName then return end
		send({ Kind = `Input`; Session = Cut.Session; Seg = SegName; Opened = Opened; Times = Input.Times; Pick = Input.Pick;
			PickAt = Input.PickAt; Release = Input.Release; Touch = Input.Touch; Reduced = Input.Reduced })
		if Cut.Solo then
			local Outcome = Judge.Evaluate(P, Input)
			local Next = Judge.Branch(P, Outcome)
			if Next then Local.Branch(Cut, SegName, Next, nil) end
		else
			task.delay(1.5, function()
				if Cut.Live and Cut.Seg == SegName then send({ Kind = `Where`; Session = Cut.Session }) end
			end)
		end
	end)
end

-- cut to the next segment on the branch (solo: now; group: at the server's StartAt, inside the slow-motion hold)
function Local.Branch(Cut, From: string, Next: string, StartAt: number?)
	if not Cut.Live or Cut.Seg ~= From then return end
	local Delay = if StartAt then math.max(0, StartAt - workspace:GetServerTimeNow()) else 0
	local function go() if Cut.Live and Cut.Seg == From then Local.PlaySegment(Cut, Next) end end
	if Delay > 0 then task.delay(Delay, go) else go() end
end

-- the end of the last segment: an interactive cut asks for its grade (server-judged) and shows the card first
function Local.EndGraph(Cut)
	if not Cut.Interactive then Local.Finish(Cut, `Done`) return end
	Cut.GradeMsg = nil
	send({ Kind = `Grade`; Session = Cut.Session })
	local T0 = os.clock()
	while Cut.Live and not Cut.GradeMsg and os.clock() - T0 < 2 do task.wait(0.05) end
	if not Cut.Live then return end
	local G = Cut.GradeMsg
	if G and G.Grade and G.Show ~= false then
		local Seconds = Config.GradeCard or 2.5
		pcall(function() UI().GradeCard(G.Grade, G.Perfects or 0, Cut.PromptCount or 0, Seconds) end)
		task.wait(Seconds)
	end
	if Cut.Live then Local.Finish(Cut, `Done`) end
end
```

(c) In `Local.Finish`, after `Cut.Live = false`, add:

```lua
	pcall(function() Prompt().Cancel() end)
	Player:SetAttribute(`NHCinePrompt`, nil)
```

(d) In `Shared.OnStart`'s `Remote.OnClientEvent` handler, add before `elseif Message.Kind == \`End\``:

```lua
		elseif Message.Kind == `Branch` then
			if Current and Current.Session == Message.Session then Local.Branch(Current, Message.Seg, Message.Next, Message.StartAt) end
		elseif Message.Kind == `Segment` then
			local Cut = Current
			if Cut and Cut.Session == Message.Session and typeof(Message.Name) == `string` and Cut.Seg ~= Message.Name then
				Local.PlaySegment(Cut, Message.Name, math.max(0, workspace:GetServerTimeNow() - (Message.StartAt or 0)))
			end
		elseif Message.Kind == `Grade` then
			if Current and Current.Session == Message.Session then Current.GradeMsg = Message end
```

(e) Replace `Shared.BuildForTests` with the version below, and add `FlattenForTests`. The capture and analysis helpers build every segment, then flatten one path.

```lua
function Shared.BuildForTests(Id: string)
	local Def = require(ReplicatedStorage.Cinematics[Id])
	local Cut = { Id = Id; Def = Def; Actors = {}; Restore = {}; Conns = {}; Sounds = {}; Used = {} }
	Cut.Folder = Instance.new(`Folder`)
	Cut.Folder.Name = `NHCineActors`
	Cut.Folder.Parent = workspace
	local Ctx = Local.Context(Cut, { Name = Player.DisplayName })
	for _, Spec in Def.Actors or {} do
		local A = Local.MakeActor(Cut, Spec)
		if A then Cut.Actors[Spec.Name] = A end
	end
	return Cut, Def.Build(Ctx), Local
end

-- one path through a built cut as a single shot list and event list (segment times shifted to the path's clock)
function Shared.FlattenForTests(Built, Graph, Path: { string })
	if not Graph then return { shots = Built.shots; events = Built.events } end
	local Shots, Events, At = {}, {}, 0
	for _, Name in Path do
		local Seg = Built.segments[Name]
		for _, S in Seg.shots do table.insert(Shots, S) end
		for _, E in Seg.events or {} do local C = table.clone(E) C.t = (E.t or 0) + At table.insert(Events, C) end
		At += Graph.segments[Name].len
	end
	return { shots = Shots; events = Events }
end
```

(f) Header comment: describe `Graph` and segments, and the events' segment clock.

- [ ] **Step 3: Verify.** Install `Controllers.Cine` in Edit. Play, `start_play.lua`, `snapshot.lua` (→ `_slot2.json`), `bridge.py CineMark $P '"__QteTest"' '"Seen"'`, `client.py t_director.lua`.

Expected:
- `Play interactive=true | prompt Press | prompt nil | prompt Mash | prompt nil | grade S | path A>B>D>E`

Change `t_director.lua` to feed **no** press for the Press prompt and run it again. Expected: path `A>C>D>E`, grade `C` (the Press is a Miss, 0 of 3; the Mash is a Win, 2 of 2; 2/5 = 40%).

Then:
- `bridge.py CineGrades $P` shows `__QteTest = { Best = "S" ... }`.
- The console has no `[Cine]` errors (`get_console_output`).
- `CineMark $P '"__QteTest"' nil`, then `restore.py`.
- Stop Play.

- [ ] **Step 4: Re-check Phase 1 behaviour (no regressions).** Play, `start_play.lua`, `CineMark $P '"Prologue"' '"Seen"'`, then the 2.24.0 replay-and-skip check, as a client call:

```lua
local R = game.ReplicatedStorage.NHCine
local sess
local c = R.OnClientEvent:Connect(function(m) if m.Kind == "Play" then sess = m.Session end end)
R:FireServer({ Kind = "Replay", Id = "Collected" })
task.wait(4)
local mid = tostring(workspace.CurrentCamera.CameraType)
R:FireServer({ Kind = "Skip", Session = sess })
task.wait(1.2)
c:Disconnect()
return mid .. " -> " .. tostring(workspace.CurrentCamera.CameraType)
```

Use `CineMark $P '"Collected"' '"Seen"'` first. Expected: `Enum.CameraType.Scriptable -> Enum.CameraType.Custom`. Then clear both marks and `restore.py`. Stop Play.

- [ ] **Step 5: Commit** (`2.25.0 (6/8): the director plays segments, prompts and branches`).

---

### Task 7: The prologue's "Here." prompt

**Files:**
- Modify: `tools/phase2-2250/live/ReplicatedStorage.Cinematics.Prologue.luau`
- Modify: `tools/phase2-2250/live/ReplicatedStorage.Config.Cine.luau` (Prologue: `Interactive`, `ShowGrade = false`, `Length`)
- Create: `tools/phase2-2250/harness/analyze_paths.lua`

**Interfaces:**
- Consumes: the Task 6 director contract (`Def.Graph`, `Build` → `segments`).
- Produces: the Prologue graph `RollCall → (Perfect | Good) Answer / Miss Late → Holt`. No flag, and no grade card.

- [ ] **Step 1: Failing test, the path analysis.** `tools/phase2-2250/harness/analyze_paths.lua` (client) enumerates every path of a cut and runs the Phase 1 per-shot analysis on each. Substitute `__CUT__` before running.

```lua
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local Director = require(Players.LocalPlayer.PlayerScripts.Controllers.Cine)
local Judge = require(RS.Functions.CineJudge)
local Lib = require(RS.Cine)
local Def = require(RS.Cinematics["__CUT__"])
local Graph = Def.Graph
local Paths = {}
local function walk(N, Path)
	table.insert(Path, N)
	local S = Judge.Successors(Graph, N)
	if #S == 0 then table.insert(Paths, table.clone(Path)) else for _, Next in S do walk(Next, Path) end end
	table.remove(Path)
end
if not Graph then return "no graph" end
local Errs = Judge.Validate(Graph)
if #Errs > 0 then return "INVALID: " .. table.concat(Errs, " | ") end
walk(Graph.start, {})
local Out, Fixes = {}, 0
for _, Path in Paths do
	local Cut, Built, L = Director.BuildForTests("__CUT__")
	local Flat = Director.FlattenForTests(Built, Graph, Path)
	local events = Flat.events
	table.sort(events, function(a, b) return (a.t or 0) < (b.t or 0) end)
	local line = (Cut.Actors.Hale and Cut.Actors.Self) and { Cut.Actors.Hale.Model, Cut.Actors.Self.Model } or nil
	local At, Fired = 0, 1
	for _, shot in Flat.shots do
		local Mid = At + shot.dur / 2
		while Fired <= #events and (events[Fired].t or 0) <= Mid do
			local E = events[Fired]
			Fired += 1
			if E.walk then
				local A, To = Cut.Actors[E.walk.who], Cut.Ctx.Mark(E.walk.to)
				if A and To then if E.walk.pose then L.SetPose(A, E.walk.pose, 100) end A.Walk = { From = A.Base; To = To.CFrame; T0 = E.t; Dur = E.walk.dur or 2 } end
			elseif E.pose or E.look or E.place then pcall(L.Fire, Cut, E) end
		end
		for _, A in Cut.Actors do for K, V in A.Target do A.Cur[K] = V end pcall(L.StepActor, A, 1 / 60, Mid, workspace.CurrentCamera) end
		local ok, report = pcall(Lib.analyze, { name = shot.name; letterbox = 2.28; line = line; shots = { shot } })
		for l in tostring(report):gmatch("[^\n]+") do
			if l:find("^%[fix%]") then Fixes += 1 table.insert(Out, table.concat(Path, ">") .. " " .. l) end
		end
		At += shot.dur
	end
	if Cut.Folder then Cut.Folder:Destroy() end
end
return string.format("%d paths, %d fixes, longest %.1f s\n", #Paths, Fixes, Judge.LongestPath(Graph)) .. table.concat(Out, "\n")
```

Run it against the current Prologue: `sed 's/__CUT__/Prologue/g' analyze_paths.lua > _ap.lua && client.py _ap.lua` (in Play). Expected: `no graph`.

- [ ] **Step 2: Implement the graph.** In the Prologue module, set `Def.Graph` after `Def` is defined. The segment lengths come from the 2.24.0 shot list:
  - RollCall: shots 1 to 4 = 14.0, plus "Your name" 1.0 = 15.0.
  - Answer: 1.6.
  - Late: 1.2 + 1.6 = 2.8.
  - Holt: 3.2 + 4.8 + 3.0 + 3.6 = 14.6.

```lua
-- (2.25.0) the roll call stops for one prompt: answer to your name on the beat. Late (a miss) changes one line, nothing else.
Def.Graph = { start = `RollCall`; segments = {
	RollCall = { len = 15.0; prompt = { kind = `Press`; at = 14.3; beat = 0.55; slow = 0.35; label = `ANSWER`;
		on = { Perfect = `Answer`; Good = `Answer`; Miss = `Late` } } };
	Answer = { len = 1.6; next = `Holt` };
	Late = { len = 2.8; next = `Holt` };
	Holt = { len = 14.6 };
} }
```

Restructure `Def.Build` to return `segments`:
- `RollCall` holds shots 1 to 4 unchanged, plus the new shot "Your name" (`dur = 1.0`; subject Self; `camera = { frame = { size = \`MCU\`; yaw = -28; pitch = 2; lens = 50 } }; noise = \`auto\`; dof = true`).
  - Events: all of the old events with `t < 14.0`, unchanged, **except** the Hale line with your name moves to `t = 13.3` (it was `T[4] + 1.9` = 13.3 already).
  - Remove the old `T[5]` "Here." line and its pose from RollCall.
- `Answer`: one shot "You answer" (`dur = 1.6`; subject Self; `camera = { frame = { size = \`MS\`; yaw = -20; pitch = 3; lens = 45 } }; noise = \`auto\`; dof = true`). This is a different size from "Your name", so the cut isn't a jump cut. Events:
  - `{ t = 0.05; say = { who = \`Self\`; name = First; text = \`Here.\`; dur = 1.2 } }`
  - `{ t = 0.0; pose = { who = \`Self\`; name = { RS = 1.0; LS = 0.9; Lean = 0.1; Pitch = -0.04 }; speed = 5 } }`
- `Late`: two shots.
  - "Late answer": `dur = 1.2`; subject Self; `camera = { frame = { size = \`MCU\`; yaw = -28; pitch = 2; lens = 50 } }`. That's the same framing as "Your name", deliberately, to hold on the awkward beat. Mark it `jumpCut = true`.
  - "Hale glance": `dur = 1.6`; subject Hale; `camera = { frame = { size = \`MCU\`; yaw = 22; pitch = 1; lens = 50 } }`; `noise = \`auto\``; `dof = true`.
  - Events: `{ t = 0.15; say = { who = \`Self\`; name = First; text = \`...Here.\`; dur = 1.0 } }`, `{ t = 1.2; look = { who = \`Hale\`; at = \`Self\` } }`, `{ t = 1.35; say = { who = \`Hale\`; text = \`...Here, apparently.\`; dur = 1.3 } }`, `{ t = 2.7; look = { who = \`Hale\`; at = false } }`.
- `Holt`: shots 6 to 9 unchanged ("Holt", "The empty desk", "Moving on", "Behind you"). Events: every old event with `t >= T[6]`, with `t` reduced by `T[6]` (= 16.4 in 2.24.0). The old `T[k]` arithmetic becomes per-segment offsets: compute `local H = {}` with the Holt shot starts 0, 3.2, 8.0, 11.0, the same way `T` was computed.

Return `{ segments = { RollCall = {...}; Answer = {...}; Late = {...}; Holt = {...} }; grade = <the same grade table as 2.24.0> }`.

In `Config.Cine`, change Prologue to:

```lua
		Prologue = { Name = `Roll Call`; Length = 35; Set = `RollCall`; Replay = true; Arrive = `Arrive`; Interactive = true; ShowGrade = false };
```

`Length` = the longest path, 33.7 s by `CineJudge.LongestPath` (RollCall 14.3 + 0.7/0.35 = 16.3; Late 2.8; Holt 14.6), rounded up. `ShowGrade = false` means no card.

- [ ] **Step 3: Verify.** Install Prologue and Config.Cine in Edit, then Play, `start_play.lua`, and run `analyze_paths.lua` for Prologue. Expected: `2 paths, 0 fixes, longest 33.7 s`.

Then a live run, as a client call:
1. `snapshot.lua` → `_slot2.json`, then `CineMark $P '"Prologue"' '"Seen"'`.
2. Replay `Prologue`. When `NHCinePrompt` becomes `Press`, wait 0.55 s, fire the hook `Down`, and record `NHCinePath`. Expected: `RollCall>Answer>Holt`.
3. Replay again with no press. Expected: `RollCall>Late>Holt`.
4. Skip each run after the path is recorded.

Take one `screen_capture` during an open prompt (fire nothing, then capture). Then `CineMark ... nil` and `restore.py`. Stop Play.

- [ ] **Step 4: Commit** (`2.25.0 (7/8): the prologue's Here. prompt`).

---

### Task 8: Journal grade, docs and release

**Files:**
- Modify: `tools/phase2-2250/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.QuestJournal.luau` (the "Cutscenes" section)
- Modify: `docs/expansion/12-Interactive-Cutscenes.md` (add a "Spec deltas" section, the five items above), `CHANGELOG.md` (2.25.0), `README.md` (Latest update), `docs/Implementation-Status.md` (row), `updates/discord/game-updates/2026-11-18-interactive-cutscenes.md`, `updates/discord/README.md`
- Vault: copy the CHANGELOG, the post (named `Discord 2026-11-18 Interactive Cutscenes.md`) and doc 12 into `E:/Download/Obsidian (VAULT)/Rello Memory/Nightmare Highschool/`, and add the home-note line.

- [ ] **Step 1: Journal.** In the Cutscenes block of `Local.RenderQuests`, replace the label's text `Cut.Name` with a name and best grade. Collect `Grades = if typeof(Q.CineGrades) == \`table\` then Q.CineGrades else {}` beside `Seen`, and set:

```lua
				Text = if Grades[Cut.Id] and (CineConfig.Cuts[Cut.Id].ShowGrade ~= false) then `{Cut.Name}   <font color="#{C.Gold:ToHex()}">{Grades[Cut.Id].Best}</font>` else Cut.Name;
				RichText = true;
```

Verify:
1. Install the journal in Edit, then Play, `start_play.lua` and `snapshot.lua`.
2. `CineMark $P '"__QteTest"' '"Seen"'`, then run `t_director.lua` (a grade S).
3. Open the journal by clicking `LocalPlayer.PlayerGui`'s Journal button at its `AbsolutePosition` (MCP `user_mouse_input`), then `screen_capture`.
4. Expected: "QTE test   S" in gold under Cutscenes. The prologue shows no grade.
5. Clear the marks, `restore.py`, and stop Play.

- [ ] **Step 2: Remove the test cut from the journal.** Give `Config.Cine.Cuts.__QteTest` the field `Hidden = true`, and in the Cutscenes loop skip cuts with `Cut.Hidden`. Re-check the journal screenshot after `CineMark ... "Seen"`: "QTE test" is gone.

- [ ] **Step 3: Final checks.** In one Play session (`start_play.lua`, `snapshot.lua`), run:
  - `bridge.py CineJudgeTest`, `CineGraphTest` and `CineQteTest $P`: no failures.
  - `CineVoteTest $P` and `Phase1SelfTest $P`: as in 2.24.0.
  - The Task 7 live prologue run (both paths).
  - A console check: no errors from `Cine`, `CinePrompt`, `CineUI`, `CineJudge` or `QuestJournal` (the 2.24.0 `errs.lua` filter plus `CinePrompt` and `CineJudge`).

  Then `restore.py` and stop Play. Save the place (MCP `save_place`) and note the version.

- [ ] **Step 4: Docs.**
  - **CHANGELOG `[2.25.0] - <date>: Interactive cutscenes, the framework`:**
    - the backup folder, the mirror and the Map read-only line
    - Added: CineJudge, the prompt kinds and windows, solo branching and group team results, grades and `CineGrades`, the prologue prompt, the Journal grade
    - Checked: every test above with its numbers, and the paths' analysis
    - Not checked: a real two-player run, phone screens, the owner at full speed
    - The place version
  - **README:** a Latest-update paragraph.
  - **Implementation-Status:** a row.
  - **Discord post (player words):**
    - "Cutscenes can now ask you to act: when Mr. Hale reads your name, answer on the beat."
    - "Miss it and he notices."
    - "Interactive cutscenes keep your best grade in the Journal."
    - "Watching with your study group, everyone plays and the scene follows the group."
  - **Doc 12:** the Spec deltas section.
  - **Vault:** copy and link.

- [ ] **Step 5: Commit** (`2.25.0: interactive cutscenes, the framework (Judge, prompts, segments, grades, the prologue's Here.)`). Stage only this plan's files, and use the hunk-staging method from 2.24.0 if CHANGELOG still carries another session's hunk: `git diff CHANGELOG.md` → keep only the 2.25.0 hunk → `git apply --cached`.

---

## Self-review

- **Spec coverage:**
  - §2 prompt kinds and windows: Tasks 1, 4, 5.
  - §3 the segment graph and validation: Tasks 1, 6, 7.
  - §4 network, solo and group, Where, skip: Tasks 3, 6. Skip follows delta 4.
  - §5 grades, rewards, flags and the Journal: Tasks 2, 3, 8.
  - §7 director changes: Task 6. Actors playing clips per joint is part B's need (the finale) and moves to plan B.
  - §9 tests: Tasks 1, 3, 4, 6, 7, 8.
  - §6 and §8 (the finale and animation sourcing): plan B.
- **Placeholders:** none. Every code step has the code. Task 7's Prologue restructure names every shot, its framing, every moved event and the offsets.
- **Types:** `Judge.Evaluate(P, Input) -> (string, number)` is used the same way in Tasks 1, 3, 4 and 6. Message fields match between Task 3 (server) and Task 6 (client): `Seg`, `Input`, `Where`, `Grade`, `Branch`, `Segment`. `CineUI` API names match between Tasks 4, 5 and 6. `Quests.CineGrades` comes from Task 2 and is used in Task 3.
- **Numbers checked:**
  - `CineJudgeTest` has 22 cases plus 14 checks (36), and `CineGraphTest` has 9.
  - The test graph's longest path is 16.17 s.
  - The Prologue's longest path is 33.7 s; its prompt tail lasts 2.0 s against the 1.575 s needed.
  - Task 6's two runs grade S (5/5) and C (2/5).
