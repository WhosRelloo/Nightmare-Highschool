# The Strikethrough (Chapter One finale) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After Hours ends in a playable fight in Room 102 at night. You lay Mira's file on her desk, an Unwritten rises out of it, and you dodge, shove, fight a tug of war over the file, and finish it with a hold. COLLECTED then plays, with a torn page if you lost the tug of war.

**Architecture:**
- **Built on 2.25.0:** CineJudge prompts, segment graphs, solo and group branching, grades.
- **The director gains four things:**
  - actors play clips through the toolkit's `anim` event, so slow-motion and hitstop apply to them
  - a cast template source (`Template:<Name>`)
  - effect and move events
  - story flags passed in the Play message
- **Animation sourcing:** the R6 clips are converted from measurements of existing clips by a forward-kinematics extractor and a retiming converter, then checked with the animation tool's audits. That's the owner's rule: reuse, else derive from related clips.
- **The Strikethrough** is an R6 cast template built from the AI rig, existing clothing and existing effects.

**Tech Stack:** Roblox Luau (NH Combat Test, placeId 98950102230473). The Studio MCP and the `tools/phase2-2250/harness` scripts (install, dump, bridge, client, snapshot, restore, `analyze_paths.lua`). Node: the `roblox-cinematic-animation` skill's `scripts/animpro.mjs`. Python: the `r6-animation-cinematics` skill's `scripts/physics_audit.py` and `jitter_audit.py`.

**Spec:** `docs/expansion/12-Interactive-Cutscenes.md` §6 (the finale) and §8 (animation sourcing), plus the 2.25.0 deltas in §11. The house style is in the `r6-animation-cinematics` skill. Load it, and `roblox-cinematic-animation`, before Tasks 3 and 6.

## Global Constraints

- Build only in **NH Combat Test**. The Map place is **read-only**. Its marks go into doc 11's port table, not into the Map.
- **Backup** before the first edit of each script: `ServerStorage.NH_Backup.Phase3_pre_<YYYYMMDD>`.
- **Mirror:** `tools/phase3-2260/{pre,live}`. Install with `tools/phase2-2250/harness/install.py <file>`, and dump with `tools/phase2-2250/harness/dump.py`. Before the first dump, change `dump.py`'s `ROOT` to target `phase3-2260`.
- **Animation:**
  - Reuse an existing clip when one fits.
  - Otherwise derive from measured related clips (Task 2), on the regular non-bending **R6** rig, with true proportions.
  - **Legs must be realistic:** planted feet slide < 0.6 studs/s, there's no floor penetration, weight goes over the supporting leg, contacts compress the root 0.2 to 0.5 studs, and steps land with contact.
  - **House style:** creeping anticipation of 0.25 to 0.45 s, a strike of 4 to 7 frames at 60 fps, a follow-through and settle of 0.5 to 1.0 s, moving holds (< 3% frozen frames), hitstop on contacts (heavy 6 to 10 frames), and offsets between joints (root first, arms 1 to 4 frames later).
- **UI and VFX:** only existing assets: kit art, `ReplicatedStorage.Assets.Effects.*` and existing particle textures such as the dark smoke `rbxassetid://8527116276`. No blocky organic shapes. The R6 body is excepted from that rule.
- **Test slot 2** only: snapshot before, restore after. Set `SetTime "21:30"` first, so the fight is at night and no classes run.
- **Studio quirk:** start and observe a cut in the same client call.
- **Commits:** `git -c user.name=Rello`, Co-Authored-By and Claude-Session lines, on branch `phase3-2260`. Only this plan's files.

---

## File structure

| File (dotted path → `tools/phase3-2260/live/<path>.luau`, unless noted) | Responsibility | New / changed |
|---|---|---|
| `StarterPlayer.StarterPlayerScripts.Controllers.Cine` | Actors yield their limbs to playing clips; `Template:` source; `fx` / `move` events; `Ctx.Flags`, `Ctx.Clip` | changed |
| `ServerScriptService.Services.World.Cine` | Play message carries `Flags` (`Config.Cine.Cuts[Id].Flags`) | changed |
| `ReplicatedStorage.Config.CineClips` | Clip name → published id, with fallback to a KeyframeSequence in `ReplicatedStorage.NHCineClips` | new |
| `ReplicatedStorage.NHCineClips.*` (KeyframeSequences, built by the animation tool's `--out` Luau) | The derived R6 clips | new (instances) |
| `ReplicatedStorage.NHCineCast.Strikethrough` (Model) | The Unwritten: an R6 rig with clothing, ink and page effects, faceless | new (instance, built by `tools/phase3-2260/build_strikethrough.luau`) |
| `workspace.NHCineSets.Strike` (marks) | The fight's marks in Room 102 | new (instances, built by `tools/phase3-2260/marks_strike.luau`) |
| `ReplicatedStorage.Cinematics.Strikethrough` | The fight graph and segments | new |
| `ReplicatedStorage.Cinematics.Collected` | The torn page when `Flags.FileKept == "Lose"` | changed |
| `ReplicatedStorage.Config.Cine` | `Strikethrough` entry; `Collected.Flags` | changed |
| `ReplicatedStorage.Config.Quests` | After Hours: `Return` and `Fight` stages before `Collected`; `Version = 2`, `StageShiftFrom = 3`, `StageShift = 2` | changed |
| `ServerScriptService.Services.Quests.Quests` | `MigrateVersion` honours `StageShiftFrom` | changed |
| `ServerScriptService.Services.Studio.TestBridge` | `AfterHoursMigrateTest` | changed |
| `tools/phase3-2260/anim/extract.luau`, `convert.py`, `clips.json`, `source/*.json`, `pose/*.json`, `out/*.lua`, `REPORT.md` | Animation measurement, conversion, built clips, report | new |

---

### Task 1: Director, actors play clips, cast templates, effects, flags

**Files:**
- Modify: `…Controllers.Cine.luau`, `…World.Cine.luau`
- Create: `…ReplicatedStorage.Config.CineClips.luau`
- Test: `tools/phase3-2260/harness/t_clip.lua`; `ReplicatedStorage.Cinematics.__QteTest` gains an `anim` and an `fx` event in segment A

**Interfaces:**
- Produces, for cut modules:
  - **Actor source** `From = "Template:<Name>"` clones `ReplicatedStorage.NHCineCast.<Name>`.
  - **`Ctx.Clip(Name) -> string?`:** an AnimationId from `Config.CineClips[Name]`. That's the published id, or a preview id for the KeyframeSequence `ReplicatedStorage.NHCineClips[Name]`.
  - **`Ctx.GameClip(Path) -> string?`:** the AnimationId of `ReplicatedStorage.Assets.Animations.<Path>` (dotted).
  - **`Ctx.Flags`:** a `{ [Flag] = Outcome }` table from the Play message.
  - **Shot events:**
    - `{ t, anim = { rig = Ctx.Actor(Name), id = Ctx.Clip(...), speed?, fade?, looped? } }` (the toolkit's own event). It goes in a **shot's** `events` table, not the segment's, so the shot player times it and applies slow-motion and hitstop. The director's segment events handle `fx`, `move`, `walk`, `place`, `pose`, `look`, `say`, `bell`, `card`, `sound` and `call`.
    - `{ t, fx = { template = "CombatFX.Flashstep", at = <Instance|CFrame>, part? = "Torso", count = 20, color? = Color3 } }`
    - `{ t, move = { part = <BasePart>, to = <CFrame>, dur = 0.3 } }`: a client-side move, put back when the cut ends.
- **Server:** the Play message gains `Flags = { [Flag] = Quests.Decided(Player, Flag) }` for each name in `Config.Cine.Cuts[Id].Flags`.

- [ ] **Step 1: Failing test.** Add these events to segment A of `__QteTest`:
  - `{ t = 0.2; anim = { rig = Ctx.Actor("Self"); id = Ctx.GameClip("Weapons.Fist.Moves.Shove") } }`
  - `{ t = 0.4; fx = { template = "CombatFX.Flashstep"; at = Ctx.Actor("Self"); part = "Torso"; count = 12 } }`

  Give `__QteTest` an actor: `Actors = { { Name = "Self"; From = "Self"; Mark = "HallLook"; Pose = "Stand" } }`.

  Then the client test `tools/phase3-2260/harness/t_clip.lua`:

```lua
local RS = game:GetService("ReplicatedStorage")
local R = RS.NHCine
local found, fxSeen = nil, false
local sess
local c = R.OnClientEvent:Connect(function(m) if m.Kind == "Play" then sess = m.Session end end)
R:FireServer({ Kind = "Replay"; Id = "__QteTest" })
local t0 = os.clock()
while os.clock() - t0 < 2.5 do
	task.wait(0.05)
	local A = workspace:FindFirstChild("NHCineActors") and workspace.NHCineActors:FindFirstChild("CineActor_Self")
	local An = A and A:FindFirstChildOfClass("Humanoid") and A.Humanoid:FindFirstChildOfClass("Animator")
	if An then for _, T in An:GetPlayingAnimationTracks() do if T.Animation.AnimationId:find("99575689929104") then found = T.Animation.AnimationId end end end
	if workspace:FindFirstChild("NHCineActors") and workspace.NHCineActors:FindFirstChild("CineFx", true) then fxSeen = true end
end
R:FireServer({ Kind = "Skip"; Session = sess })
c:Disconnect()
return "clip " .. tostring(found) .. " | fx " .. tostring(fxSeen)
```

  Run it as in 2.25.0 (`CineMark $P '"__QteTest"' '"Seen"'` first). Expected: `clip nil | fx false`, because `GameClip` doesn't exist yet and Build errors.

- [ ] **Step 2: Implement (director).**

(a) In `Local.StepActor`, replace `local Clip = A.WalkTrack ~= nil and A.WalkTrack.IsPlaying` with:

```lua
	local Clip = (A.WalkTrack ~= nil and A.WalkTrack.IsPlaying) or Local.HasClip(A)
```

Add above `Local.StepActor`:

```lua
-- (2.26.0) any clip playing on an actor (the toolkit's anim event, the walk) owns the limbs: the pose layer keeps only the
-- head's look, so a clip is never overwritten by the procedural breathing
function Local.HasClip(A): boolean
	local Hum = A.Model:FindFirstChildOfClass(`Humanoid`)
	local An = Hum and Hum:FindFirstChildOfClass(`Animator`)
	if not An then return false end
	for _, T in An:GetPlayingAnimationTracks() do
		if T.WeightCurrent > 0.05 then return true end
	end
	return false
end
```

(b) In `Local.SourceFor`, before the final `return nil`:

```lua
	local Template = From:match(`^Template:(.+)$`)
	if Template then
		local Cast = ReplicatedStorage:FindFirstChild(`NHCineCast`)
		local M = Cast and Cast:FindFirstChild(Template)
		return if M and M:IsA(`Model`) then M else nil
	end
```

(c) In `Local.Context`, after `local Ctx = { ... }`, add:

```lua
	Ctx.Flags = if typeof(Message.Flags) == `table` then Message.Flags else {}
	function Ctx.GameClip(Path: string): string?
		local I = ReplicatedStorage:FindFirstChild(`Assets`) and ReplicatedStorage.Assets:FindFirstChild(`Animations`)
		for Part in Path:gmatch(`[^%.]+`) do I = I and I:FindFirstChild(Part) end
		return if I and I:IsA(`Animation`) then I.AnimationId else nil
	end
	function Ctx.Clip(Name: string): string?
		local Ok, Clips = pcall(function() return require(ReplicatedStorage.Config.CineClips) end)
		local Id = Ok and Clips[Name]
		if typeof(Id) == `string` and Id ~= `` then return Id end
		local Folder = ReplicatedStorage:FindFirstChild(`NHCineClips`)
		local Seq = Folder and Folder:FindFirstChild(Name)
		if Seq and Seq:IsA(`KeyframeSequence`) then
			local Pid = Seq:GetAttribute(`PreviewId`)
			if not Pid then
				local Ok2, Got = pcall(function() return game:GetService(`AnimationClipProvider`):RegisterAnimationClip(Seq) end)
				if Ok2 then Pid = tostring(Got) Seq:SetAttribute(`PreviewId`, Pid) end
			end
			return Pid
		end
		return nil
	end
```

(d) In `Local.Fire`, before `if E.call then`:

```lua
	if E.fx then Local.Fx(Cut, E.fx) end
	if E.move then Local.Move(Cut, E.move) end
```

and add after `Local.Sound`:

```lua
-- an existing effect from ReplicatedStorage.Assets.Effects (dotted path), emitted at an actor's part, a mark or a CFrame
function Local.Fx(Cut, F)
	local Src = ReplicatedStorage:FindFirstChild(`Assets`) and ReplicatedStorage.Assets:FindFirstChild(`Effects`)
	for Part in tostring(F.template):gmatch(`[^%.]+`) do Src = Src and Src:FindFirstChild(Part) end
	if not Src then warn(`[Cine] no effect {tostring(F.template)}`) return end
	local At = F.at
	local CF = if typeof(At) == `CFrame` then At
		elseif typeof(At) == `Instance` and At:IsA(`Model`) then ((At:FindFirstChild(F.part or `Torso`) or At.PrimaryPart) :: BasePart).CFrame
		elseif typeof(At) == `Instance` and At:IsA(`BasePart`) then At.CFrame else nil
	if not CF then return end
	local Holder = Instance.new(`Part`)
	Holder.Name = `CineFx`
	Holder.Anchored, Holder.CanCollide, Holder.CanQuery, Holder.CanTouch = true, false, false, false
	Holder.Transparency = 1
	Holder.Size = Vector3.one * 0.2
	Holder.CFrame = CF
	Holder.Parent = Cut.Folder
	local C = Src:Clone()
	C.Parent = Holder
	if C:IsA(`Attachment`) then C.CFrame = CFrame.identity end
	for _, D in Holder:GetDescendants() do
		if D:IsA(`ParticleEmitter`) then
			if F.color then D.Color = ColorSequence.new(F.color) end
			D.Enabled = false
			D:Emit(F.count or 10)
		end
	end
	task.delay(F.life or 3, function() if Holder.Parent then Holder:Destroy() end end)
end

-- a scene part moved on this screen only (a desk shoved), put back exactly when the cut ends
function Local.Move(Cut, M)
	local P = M.part
	if typeof(P) ~= `Instance` or not P:IsA(`BasePart`) or typeof(M.to) ~= `CFrame` then return end
	Cut.Restore[P] = Cut.Restore[P] or P.CFrame
	TweenService:Create(P, TweenInfo.new(M.dur or 0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CFrame = M.to }):Play()
end
```

`Local.Finish` already restores `Cut.Restore`. The toolkit's own `anim` event drives the clips (shots' `events`), so the director needs nothing more for clips.

- [ ] **Step 3: Implement (server and config).** In `World.Cine`'s `Shared.Play`, add `Flags = Local.FlagsFor(Player, Cut)` to the Play message table, with:

```lua
function Local.FlagsFor(Player: Player, Cut): { [string]: string }
	local Out = {}
	for _, F in Cut.Flags or {} do
		local Ok, V = pcall(function() return Quests().Decided(Player, F) end)
		if Ok and typeof(V) == `string` then Out[F] = V end
	end
	return Out
end
```

Create `ReplicatedStorage.Config.CineClips`:

```lua
--[[ (2.26.0) Cutscene clips by name. A published AnimationId wins; an empty string plays the KeyframeSequence of the same
	name in ReplicatedStorage.NHCineClips through a preview id (Studio only). After the owner publishes a clip, paste its
	id here. ]]
return {
	StrikeRise = ``; StrikeLunge = ``; StrikeRecoil = ``; StrikeGrab = ``; StrikeStagger = ``; StrikeTug = ``; StrikeShatter = ``;
	YouTugPull = ``; YouFinisher = ``;
}
```

- [ ] **Step 4: Verify.** Install the director, `World.Cine`, `Config.CineClips` and `__QteTest` in Edit, then run `t_clip.lua` in Play.
  - Expected: `clip rbxassetid://99575689929104 | fx true`.
  - Re-run the 2.25.0 `t_director.lua`: still `grade S | path A>B>D>E`.
  - Restore slot 2.
- [ ] **Step 5: Commit** (`2.26.0 (1/8): cutscene actors play clips; templates, effects, flags`).

---

### Task 2: Measure the related clips (forward kinematics) and convert them to R6

**Files:**
- Create: `tools/phase3-2260/anim/extract.luau`, `convert.py`, `clips.json`, `REPORT.md`
- Output: `tools/phase3-2260/anim/source/<Name>.json`, `tools/phase3-2260/anim/pose/<Target>.json`

**Interfaces:**
- **`extract.luau`** (Edit). Set `SOURCES` at the top. It returns JSON: `{ [Name] = { rig = "R15" | "R6", length, keys = [{ t, root = {x,y,z}, torso = {pitch,yaw,roll}, neck = {pitch,yaw,roll}, aims = { LeftShoulder = {x,y,z}, RightShoulder, LeftHip, RightHip } }] } }`.
  - Aims are unit vectors in the torso's body frame: x right, y up, z forward (the animation tool's axes).
  - R15 arms aim from the shoulder to the wrist and legs from the hip to the ankle, so an elbow or knee bend folds into the aim (the R6 rule).
- **`convert.py <target>`** reads `clips.json` and the source JSON and writes the R6 pose JSON:
  - it retimes the source keys to the target's phase times
  - it adds the root drop on contacts
  - it keeps planted feet on the floor (`grounded`).

- [ ] **Step 1: Write `extract.luau`.**

```lua
-- Measure cutscene source clips by forward kinematics on their own rigs. Edit mode, read only.
local SOURCES = {
	{ Name = "GhoulEmerge"; Rig = "R15"; Seq = function() return game.ServerStorage.NHBeasts.Clips.GraveGhoul.Emerge end };
	{ Name = "GhoulGrab"; Rig = "R15"; Seq = function() return game.ServerStorage.NHBeasts.Clips.GraveGhoul.Grab end };
	{ Name = "GhoulAttack1"; Rig = "R15"; Seq = function() return game.ServerStorage.NHBeasts.Clips.GraveGhoul.Attack1 end };
	{ Name = "GhoulStun1"; Rig = "R15"; Seq = function() return game.ServerStorage.NHBeasts.Clips.GraveGhoul.Stun1 end };
	{ Name = "GhoulDeath"; Rig = "R15"; Seq = function() return game.ServerStorage.NHBeasts.Clips.GraveGhoul.Death end };
	{ Name = "StalkerReach"; Rig = "R15S"; Seq = function() return game.ServerStorage.NHBeasts.Clips.NightStalker.Reach end };
	{ Name = "FistClinch"; Rig = "R6"; Id = "rbxassetid://105787080820844" };
	{ Name = "FistClinchVictim"; Rig = "R6"; Id = "rbxassetid://127085112840973" };
	{ Name = "FistM2"; Rig = "R6"; Id = "rbxassetid://80262616372750" };
	{ Name = "FistBodyBlow"; Rig = "R6"; Id = "rbxassetid://115837677569118" };
	{ Name = "Uptilt"; Rig = "R6"; Id = "rbxassetid://102341195576821" };
	{ Name = "Knockback"; Rig = "R6"; Id = "rbxassetid://138802633910747" };
}
local H = game:GetService("HttpService")
local KSP = game:GetService("KeyframeSequenceProvider")
local RIGS = { R15 = game.ServerStorage.NHBeasts.GraveGhoul; R15S = game.ServerStorage.NHBeasts.NightStalker; R6 = game.ServerScriptService.Services.AI.AI.Rig }

local function motors(rig)
	local L = {}
	for _, D in rig:GetDescendants() do if D:IsA("Motor6D") and D.Part0 and D.Part1 then L[D.Part1.Name] = D end end
	return L
end

-- every Pose in a keyframe, by part name (the Pose's Name is its Part1); missing poses keep the previous key's
local function posesOf(kf, last)
	local P = table.clone(last or {})
	for _, D in kf:GetDescendants() do if D:IsA("Pose") then P[D.Name] = D.CFrame end end
	return P
end

local function fk(rig, M, Poses)
	local Root = rig:FindFirstChild("HumanoidRootPart")
	local W = { [Root.Name] = CFrame.identity }
	local function world(Part)
		if W[Part.Name] then return W[Part.Name] end
		local Mo = M[Part.Name]
		if not Mo then W[Part.Name] = Root.CFrame:ToObjectSpace(Part.CFrame) return W[Part.Name] end
		local P0 = world(Mo.Part0)
		W[Part.Name] = P0 * Mo.C0 * (Poses[Part.Name] or CFrame.identity) * Mo.C1:Inverse()
		return W[Part.Name]
	end
	for Name in M do world(rig:FindFirstChild(Name, true)) end
	return W
end

local function euler(cf)
	local x, y, z = cf:ToOrientation()
	return { pitch = math.deg(x); yaw = math.deg(y); roll = math.deg(z) }
end

local function aim(TorsoCF, A, B)
	local d = TorsoCF:VectorToObjectSpace((B - A).Unit)
	return { x = d.X; y = d.Y; z = -d.Z } -- the tool's forward is the torso's look (-Z)
end

local function measure(rigKind, seq)
	local rig = RIGS[rigKind]
	local M = motors(rig)
	local R6 = rigKind == "R6"
	local kfs = seq:GetKeyframes()
	table.sort(kfs, function(a, b) return a.Time < b.Time end)
	local keys, last = {}, nil
	for _, kf in kfs do
		last = posesOf(kf, last)
		local W = fk(rig, M, last)
		local Torso = W[if R6 then "Torso" else "UpperTorso"]
		local Head = W.Head
		local function at(part, off) return (W[part] * CFrame.new(off)).Position end
		local aims
		if R6 then
			aims = {
				LeftShoulder = aim(Torso, at("Left Arm", Vector3.new(0, 1, 0)), at("Left Arm", Vector3.new(0, -1, 0)));
				RightShoulder = aim(Torso, at("Right Arm", Vector3.new(0, 1, 0)), at("Right Arm", Vector3.new(0, -1, 0)));
				LeftHip = aim(Torso, at("Left Leg", Vector3.new(0, 1, 0)), at("Left Leg", Vector3.new(0, -1, 0)));
				RightHip = aim(Torso, at("Right Leg", Vector3.new(0, 1, 0)), at("Right Leg", Vector3.new(0, -1, 0)));
			}
		else
			aims = {
				LeftShoulder = aim(Torso, W.LeftUpperArm.Position, W.LeftHand.Position);
				RightShoulder = aim(Torso, W.RightUpperArm.Position, W.RightHand.Position);
				LeftHip = aim(Torso, W.LeftUpperLeg.Position, W.LeftFoot.Position);
				RightHip = aim(Torso, W.RightUpperLeg.Position, W.RightFoot.Position);
			}
		end
		local lowest = math.huge
		for _, part in (if R6 then { "Left Leg", "Right Leg" } else { "LeftFoot", "RightFoot" }) do
			lowest = math.min(lowest, (W[part] * CFrame.new(0, if R6 then -1 else -0.2, 0)).Position.Y)
		end
		table.insert(keys, { t = kf.Time; root = { x = Torso.Position.X; y = Torso.Position.Y; z = Torso.Position.Z };
			torso = euler(Torso - Torso.Position); neck = euler((Torso:ToObjectSpace(Head)) - (Torso:ToObjectSpace(Head)).Position);
			aims = aims; footY = lowest })
	end
	return { rig = rigKind; length = kfs[#kfs].Time; keys = keys }
end

local Out = {}
for _, S in SOURCES do
	local ok, seq = pcall(function() return if S.Seq then S.Seq() else KSP:GetKeyframeSequenceAsync(S.Id) end)
	if ok and seq then
		local ok2, m = pcall(measure, S.Rig, seq)
		Out[S.Name] = if ok2 then m else { error = tostring(m) }
	else
		Out[S.Name] = { error = "could not load " .. tostring(S.Id or "seq") }
	end
end
return H:JSONEncode(Out)
```

- [ ] **Step 2: Run it and save the measurements.** Studio in Edit, from the repo root:

```bash
mkdir -p tools/phase3-2260/anim/source
python -X utf8 -I /e/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py luau "placeId: 98950102230473" Edit @E:/Nightmare-Highschool/tools/phase3-2260/anim/extract.luau | tr -d '\r' > tools/phase3-2260/anim/source/_all.json
python -I -c "import json;d=json.load(open('tools/phase3-2260/anim/source/_all.json'));[print(k, v.get('error') or (v['rig'], round(v['length'],2), len(v['keys']))) for k,v in d.items()]"
```

  Expected: 12 lines, no `error`, and key counts: GhoulEmerge 6, GhoulGrab 7, GhoulAttack1 5, GhoulStun1 4, GhoulDeath 5.

  If rbxc's 30k output cap truncates, run with `SOURCES` split into two halves.

  An R6 asset that fails to load (a permissions error) is noted in `REPORT.md`, and that target uses its next listed source in `clips.json`.

- [ ] **Step 3: Sign check (the axes are right).** Convert `Knockback` unchanged:
  - Run `python -I tools/phase3-2260/anim/convert.py --raw Knockback`, which writes `pose/_raw_Knockback.json` (Step 4 has the code).
  - Compile it: `node <roblox-cinematic-animation>/scripts/animpro.mjs tools/phase3-2260/anim/pose/_raw_Knockback.json --grounded --sheet tools/phase3-2260/anim/_check_knockback.png`.
  - Look at the sheet next to the game's Knockback played on a dummy (MCP `screen_capture`). The body must fall the same way, backwards, with the arms thrown forward.
  - If it's mirrored or reversed, flip the sign of `x` or `z` in `aim()` in `extract.luau`, re-run Step 2, and record the fix in `REPORT.md`.

- [ ] **Step 4: Write `clips.json` and `convert.py`.** `clips.json` holds the targets: each target's source, phase timings (house style) and contacts.

```json
{
  "StrikeRise":    { "source": "GhoulEmerge",  "length": 1.6,  "phases": { "anticipation": [0, 0.7], "strike": [0.7, 0.82], "settle": [0.82, 1.6] }, "contacts": [0.82], "drop": 0.35 },
  "StrikeLunge":   { "source": "StalkerReach", "alt": "GhoulAttack1", "length": 1.05, "phases": { "anticipation": [0, 0.38], "strike": [0.38, 0.47], "settle": [0.47, 1.05] }, "contacts": [0.47], "drop": 0.3 },
  "StrikeRecoil":  { "source": "GhoulStun1",   "length": 0.8,  "phases": { "anticipation": [0, 0.05], "strike": [0.05, 0.14], "settle": [0.14, 0.8] }, "contacts": [0.14], "drop": 0.2 },
  "StrikeGrab":    { "source": "GhoulGrab",    "length": 1.2,  "phases": { "anticipation": [0, 0.36], "strike": [0.36, 0.45], "settle": [0.45, 1.2] }, "contacts": [0.45], "drop": 0.25 },
  "StrikeStagger": { "source": "GhoulStun1",   "length": 1.0,  "phases": { "anticipation": [0, 0.04], "strike": [0.04, 0.15], "settle": [0.15, 1.0] }, "contacts": [0.15, 0.6], "drop": 0.4 },
  "StrikeTug":     { "source": "FistClinchVictim", "length": 1.0, "loop": true, "phases": { "anticipation": [0, 0.3], "strike": [0.3, 0.5], "settle": [0.5, 1.0] }, "contacts": [], "drop": 0.1 },
  "StrikeShatter": { "source": "GhoulDeath",   "length": 1.4,  "phases": { "anticipation": [0, 0.1], "strike": [0.1, 0.2], "settle": [0.2, 1.4] }, "contacts": [], "drop": 0.5 },
  "YouTugPull":    { "source": "FistClinch",   "length": 1.0,  "loop": true, "phases": { "anticipation": [0, 0.3], "strike": [0.3, 0.5], "settle": [0.5, 1.0] }, "contacts": [], "drop": 0.15 },
  "YouFinisher":   { "source": "FistM2", "blend": ["FistBodyBlow", "Uptilt"], "length": 1.25, "phases": { "anticipation": [0, 0.4], "strike": [0.4, 0.48], "settle": [0.48, 1.25] }, "contacts": [0.48], "drop": 0.4 }
}
```

`tools/phase3-2260/anim/convert.py`:

```python
"""Measured source clip -> R6 pose JSON for animpro.
usage: python -I convert.py <Target> | --raw <SourceName>
Retimes the source's keys onto the target's phases: the source's fastest segment (largest summed aim change per second)
becomes the strike; keys before it spread over the anticipation, keys after it over the settle. Aims are kept as
measured (R15 elbows and knees already folded in). The root drops by `drop` studs at each contact and recovers with a
small overshoot. Legs whose foot was at the floor in the source are marked `grounded` through animpro's flag."""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = json.load(open(os.path.join(HERE, "source", "_all.json"), encoding="utf-8"))
SPEC = json.load(open(os.path.join(HERE, "clips.json"), encoding="utf-8"))
JOINTS = ["LeftShoulder", "RightShoulder", "LeftHip", "RightHip"]

def vec(a): return [round(a["x"], 3), round(a["y"], 3), round(a["z"], 3)]
def change(k0, k1):
    return sum(math.dist(vec(k0["aims"][j]), vec(k1["aims"][j])) for j in JOINTS)

def strike_index(keys):
    best, bi = -1, 1
    for i in range(1, len(keys)):
        dt = max(keys[i]["t"] - keys[i - 1]["t"], 1e-3)
        v = change(keys[i - 1], keys[i]) / dt
        if v > best: best, bi = v, i
    return bi  # the key that ends the fastest segment = contact pose

def pose_key(k, t, base_y, extra_drop=0.0):
    return {"time": round(t, 3), "joints": {
        "Root": {"position": [0, round(k["root"]["y"] - base_y - extra_drop, 3), 0],
                 "rotation": [round(k["torso"]["pitch"], 1), round(k["torso"]["yaw"], 1), round(k["torso"]["roll"], 1)]},
        "Neck": {"rotation": [round(k["neck"]["pitch"], 1), round(k["neck"]["yaw"], 1), round(k["neck"]["roll"], 1)]},
        **{j: {"aim": vec(k["aims"][j])} for j in JOINTS}}}

def convert(name):
    spec = SPEC[name]
    src = SRC.get(spec["source"])
    if not src or "error" in src: src = SRC[spec["alt"]]
    keys = src["keys"]
    base_y = keys[0]["root"]["y"]
    si = strike_index(keys)
    a0, a1 = spec["phases"]["anticipation"]; s0, s1 = spec["phases"]["strike"]; e0, e1 = spec["phases"]["settle"]
    out = []
    pre = keys[:si]; post = keys[si:]
    for i, k in enumerate(pre):  # spread over the anticipation; the last pre key sits at the strike's start
        t = a0 + (s0 - a0) * (i / max(len(pre) - 1, 1))
        out.append(pose_key(k, t, base_y))
    for i, k in enumerate(post):  # the contact key at the strike's end, then the settle
        t = s1 + (e1 - s1) * (i / max(len(post) - 1, 1)) if i else s1
        drop = spec["drop"] if i == 0 and spec["contacts"] else (spec["drop"] * -0.15 if i == 1 and spec["contacts"] else 0.0)
        out.append(pose_key(k, t, base_y, drop))
    if spec.get("loop"):
        first = json.loads(json.dumps(out[0])); first["time"] = spec["length"]; out[-1:] = [out[-1], first] if out[-1]["time"] < spec["length"] else [first]
    else:
        out[-1]["time"] = spec["length"]
    markers = [{"name": "Hit", "value": "contact"}]
    for c in spec["contacts"]:
        for k in out:
            if abs(k["time"] - c) < 1e-3: k["markers"] = markers
    return {"name": name, "rig": "R6", "loop": bool(spec.get("loop")), "priority": "Action",
            "easing": {"style": "CubicV2", "direction": "InOut"}, "keyframes": out}

def raw(source):
    keys = SRC[source]["keys"]; base_y = keys[0]["root"]["y"]
    return {"name": "_raw_" + source, "rig": "R6", "keyframes": [pose_key(k, k["t"], base_y) for k in keys]}

os.makedirs(os.path.join(HERE, "pose"), exist_ok=True)
if sys.argv[1] == "--raw":
    doc = raw(sys.argv[2]); path = os.path.join(HERE, "pose", "_raw_" + sys.argv[2] + ".json")
else:
    doc = convert(sys.argv[1]); path = os.path.join(HERE, "pose", sys.argv[1] + ".json")
json.dump(doc, open(path, "w", encoding="utf-8"), indent=1)
print("wrote", path, len(doc["keyframes"]), "keys")
```

- [ ] **Step 5: Run the conversion for all nine targets and write `REPORT.md`.**

```bash
cd tools/phase3-2260/anim && for T in StrikeRise StrikeLunge StrikeRecoil StrikeGrab StrikeStagger StrikeTug StrikeShatter YouTugPull YouFinisher; do python -I convert.py $T; done
```

  Expected: nine `wrote ... N keys` lines.

  `REPORT.md` lists, per target:
  - its source clip or clips, with the asset id or path
  - the source's key times and the detected strike index
  - the retimed times
  - the measured peak angles: torso pitch range, the arms' and legs' forward swing in degrees from the aims, and the root drop

  Those are the numbers the clip copies, written in the clip's header in Task 3.

- [ ] **Step 6: Commit** (`2.26.0 (2/8): measured source clips and their R6 conversions`).

---

### Task 3: Author, check and install the R6 clips

> **Outcome (2026-11-17), the owner's direction:** use the game's own animations first (a strike can be an M1); if the game has none, use the group's.
> - **From the game:** six clips, mapped in `Config.CineClips` as `Assets:<path>`:
>   - Rise = `Default.Uptilt`.
>   - Lunge = `Weapons.Fist.RunningM1`.
>   - Recoil = `Default.Parried.1`.
>   - Grab = `Weapons.Fist.Moves.Clinch`.
>   - Stagger = `Default.Posture Break`.
>   - Finisher = `Weapons.Fist.M2`.
> - **The owner's group uploads,** from this task's baked clips:
>   - StrikeTug 98518994869117.
>   - StrikeShatter 104606462612953.
>   - YouTugPull 116365221175140.
> - **Changed:** `Ctx.Clip` resolves `Assets:` paths through `Ctx.GameClip`. Task 6's hit times follow the game clips, as listed in `Config.CineClips`.


**Files:**
- Modify: `tools/phase3-2260/anim/pose/<Target>.json` (polish passes)
- Create: `tools/phase3-2260/anim/out/<Target>.lua`, plus sheet, graph and trail PNGs under `tools/phase3-2260/anim/review/`
- Studio: `ReplicatedStorage.NHCineClips.<Target>` KeyframeSequences

**Interfaces:**
- Produces nine KeyframeSequences named exactly like the `Config.CineClips` keys. Each has a `Hit` marker on its contact key (the cut times hitstop and effects to it).

- [ ] **Step 1: Load the skills.** Invoke `r6-animation-cinematics` and `roblox-cinematic-animation`, and read `references/animation-craft.md` §2 to §9 and the R6 section of `character-animation.md`.

- [ ] **Step 2: Compile and check each clip.** For each target T:

```bash
SK="C:/Users/Owner/.claude/skills/roblox-cinematic-animation"
node $SK/scripts/animpro.mjs tools/phase3-2260/anim/pose/T.json --grounded --settle light \
  --sheet tools/phase3-2260/anim/review/T_sheet.png --graph tools/phase3-2260/anim/review/T_graph.png \
  --trails tools/phase3-2260/anim/review/T_trails.png --json tools/phase3-2260/anim/review/T.json --out tools/phase3-2260/anim/out/T.lua --parent game.ReplicatedStorage.NHCineClips
```

  Expected: exit 0, meaning no failing check and no lint `fix`. Look at all three images every time.

  **Fix loop.** For each failing check or `fix` lint, edit `pose/T.json` and re-run:
  - **A foot below the floor:** raise `Root.position` y at that key, or bring that leg's aim nearer `[0,-1,0]`.
  - **A frozen hold:** let `--life` stay at its default, or add a 1 to 3° drift key.
  - **Joints changing on the same frame:** shift the arm keys 0.03 to 0.07 s after the torso key (the offset rule).
  - **A strike that's too slow:** the contact key must be 0.07 to 0.12 s after the previous key.

  The measured aims stay as the base; only timing, offsets and floor contact change. Note every change in the clip's `name`-level comment in `REPORT.md`.

- [ ] **Step 3: The physics and jitter gates.**
  1. Preview each clip on a passive R6 dummy, a clone of a `Cape stuff` rig set to the `Characters` collision group.
  2. Dump per-frame part positions over the clip with the `r6-animation-cinematics` dump method, to `review/T_dump.json`.
  3. Run `python -I <r6-animation-cinematics>/scripts/physics_audit.py review/T_dump.json` and `jitter_audit.py` on the same file.

  Expected:
  - Physics: no floor penetration, planted feet slide < 0.6 st/s, falls accelerate.
  - Jitter: no one-frame pops except on the `Hit` frame.

  Fix in the pose JSON and re-run Steps 2 and 3.

- [ ] **Step 4: Install.**
  - Create `ReplicatedStorage.NHCineClips` (a Folder) in Edit.
  - Run each `out/T.lua` with execute_luau (they build `ReplicatedStorage.NHCineClips.T`).
  - Check that `#NHCineClips:GetChildren() == 9`, and that each KeyframeSequence has its `Hit` marker (`KeyframeMarker` children).

- [ ] **Step 5: The owner's publish list.** `tools/phase3-2260/anim/PUBLISH.md` lists the nine clips, each with one line: "Right-click `ReplicatedStorage.NHCineClips.<T>` → Save to Roblox (group 15981569), and paste the id into `Config.CineClips.<T>`".

  Until that's done, the clips play in Studio through preview ids (`Ctx.Clip`), and the live game shows actors in their pose layer. Say so in the release notes.

- [ ] **Step 6: Commit** (`2.26.0 (3/8): the finale's R6 clips, derived and checked`).

---

### Task 4: The Strikethrough cast template

**Files:**
- Create: `tools/phase3-2260/build_strikethrough.luau` (Edit script); Studio: `ReplicatedStorage.NHCineCast.Strikethrough`

**Interfaces:**
- Produces an R6 Model with a Humanoid, an Animator and the six standard parts, carrying the attributes `NHFaceless = true` and `NpcId = "Strikethrough"`. The director clones it for `From = "Template:Strikethrough"`.

- [ ] **Step 1: Write the build script.**

```lua
-- The Unwritten for the Chapter One finale: a faded student from the 1893 roll. Built from the AI rig (R6) with existing
-- clothing and existing effects only. Re-run safe.
local RS = game:GetService("ReplicatedStorage")
local Cast = RS:FindFirstChild("NHCineCast") or Instance.new("Folder", RS)
Cast.Name = "NHCineCast"
local Old = Cast:FindFirstChild("Strikethrough") if Old then Old:Destroy() end
local M = game.ServerScriptService.Services.AI.AI.Rig:Clone()
M.Name = "Strikethrough"
for _, D in M:GetDescendants() do if D:IsA("Script") or D:IsA("LocalScript") or D:IsA("BillboardGui") then D:Destroy() end end
-- 1893 clothes: the Victorian waistcoat uniform's shirt and pants templates (Appearance), washed out
local Appearance = require(RS:FindFirstChild("UI"):FindFirstChild("Appearance"))
local Uni
for _, U in Appearance.Uniforms or {} do if U.Id == "victorian-waistcoat" then Uni = U end end
local Shirt = M:FindFirstChildOfClass("Shirt") or Instance.new("Shirt", M)
local Pants = M:FindFirstChildOfClass("Pants") or Instance.new("Pants", M)
if Uni then Shirt.ShirtTemplate = Uni.Shirt or Shirt.ShirtTemplate Pants.PantsTemplate = Uni.Pants or Pants.PantsTemplate end
Shirt.Color3 = Color3.fromRGB(150, 150, 165)
Pants.Color3 = Color3.fromRGB(120, 120, 135)
-- faded: ash-grey skin, slightly see-through limbs, the head an ink smudge (no face)
local INK = Color3.fromRGB(18, 14, 22)
for _, P in M:GetChildren() do
	if P:IsA("BasePart") and P.Name ~= "HumanoidRootPart" then
		P.Color = Color3.fromRGB(150, 148, 156)
		P.Transparency = if P.Name == "Torso" or P.Name == "Head" then 0.05 else 0.25
		P.Material = Enum.Material.SmoothPlastic
	end
end
local Head = M.Head
for _, D in Head:GetDescendants() do if D:IsA("Decal") then D.Transparency = 1 elseif D:IsA("SurfaceGui") then D.Enabled = false end end
Head.Color = INK
M:SetAttribute("NHFaceless", true)
M:SetAttribute("NpcId", "Strikethrough")
-- ink bleeding off the edges (the game's dark smoke, tinted ink) and torn pages circling it (the kit's paper colour)
local function emitter(Part, Name, Props)
	local A = Instance.new("Attachment") A.Name = Name .. "Att" A.Parent = Part
	local E = Instance.new("ParticleEmitter") E.Name = Name
	for K, V in Props do E[K] = V end
	E.Parent = A
	return E
end
for _, P in { M.Torso, M["Left Arm"], M["Right Arm"], M["Left Leg"], M["Right Leg"] } do
	emitter(P, "Ink", { Texture = "rbxassetid://8527116276"; Color = ColorSequence.new(INK); LightEmission = 0; Rate = 14;
		Lifetime = NumberRange.new(0.6, 1.2); Speed = NumberRange.new(0.3, 0.9); Acceleration = Vector3.new(0, -2.5, 0);
		Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5), NumberSequenceKeypoint.new(1, 1.4) });
		Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(1, 1) }); SpreadAngle = Vector2.new(25, 25) })
end
emitter(Head, "InkHead", { Texture = "rbxassetid://8527116276"; Color = ColorSequence.new(INK); Rate = 10; Lifetime = NumberRange.new(0.5, 0.9);
	Speed = NumberRange.new(0.1, 0.4); Size = NumberSequence.new(0.9, 1.6); Transparency = NumberSequence.new(0.2, 1) })
emitter(M.Torso, "Pages", { Texture = "rbxassetid://8527116276"; Color = ColorSequence.new(Color3.fromRGB(214, 200, 168)); Rate = 3;
	Lifetime = NumberRange.new(1.8, 2.6); Speed = NumberRange.new(1.5, 2.5); RotSpeed = NumberRange.new(-120, 120);
	Size = NumberSequence.new(0.35); Shape = Enum.ParticleEmitterShape.Cylinder; ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface;
	Orientation = Enum.ParticleOrientation.VelocityPerpendicular; Transparency = NumberSequence.new(0.1, 1) })
M.Parent = Cast
return "built " .. M:GetFullName() .. " parts " .. #M:GetChildren()
```

  If `UI.Appearance` keeps uniforms under another key, read the module's export first (`script_read`). Use the uniform whose Id is `victorian-waistcoat`, as in 2.24.0's NpcLooks specs.

- [ ] **Step 2: Build and review.** Run the script in Edit. Pivot a temporary clone to (98, 4.1, 69) in Room 102 and take `screen_capture` from (94, 6, 62) looking at it.

  Check:
  - It reads as a faded student, a person rather than a blocky creature.
  - The head is an ink smudge, with no face.
  - Ink bleeds downward.
  - Pages drift.

  Destroy the clone. Adjust the colours or rates once if it reads as a plain grey dummy (the owner's rule against blocky organics). Save the screenshot under `tools/phase3-2260/review/strikethrough.jpg`.

- [ ] **Step 3: Commit** (`2.26.0 (4/8): the Strikethrough cast template`).

---

### Task 5: The fight's set marks (Room 102, night)

**Files:**
- Create: `tools/phase3-2260/marks_strike.luau`; Studio: `workspace.NHCineSets.Strike`
- Modify: `docs/expansion/11-Phase1-Plan.md` (port table rows)

**Interfaces:**
- The marks, in a floor-level mark convention (feet), facing given:
  - `You` (98, 1.1, 63.4) facing +Z: you at Mira's desk, the chair side.
  - `Rise` (98, 1.1, 68.8) facing -Z: it stands up out of the desk, on the board side.
  - `DodgeTo` (101.4, 1.1, 63.0) facing +Z: the dodge goes to your left (+X).
  - `ThrownTo` (95.6, 1.1, 60.4) facing +Z: thrown back into the back-row desks.
  - `TugYou` (98, 1.1, 64.6) and `TugIt` (98, 1.1, 67.2), facing each other across the desk.
  - `File` = the Hall set's `File` mark's CFrame.
  - `Desk` (98, 2.37, 66.5), the size of Mira's desk: the shove's target.
  - `Wide` (88, 7.5, 60.6) looking at (98, 4, 67): the establishing camera.
  - `Bell` (BellPart = `…SchoolBell_R104.SchoolBell_Bell`, at the bell).

- [ ] **Step 1: Write and run the marks script.** It's in the same style as `marks` from 2.24.0: transparent, non-colliding, non-querying, anchored 0.6-stud parts, made with `CFrame.lookAt`.

```lua
local V = Vector3.new
local Sets = workspace:FindFirstChild("NHCineSets")
local Old = Sets:FindFirstChild("Strike") if Old then Old:Destroy() end
local S = Instance.new("Folder") S.Name = "Strike"
local function mark(name, pos, look, size, attrs)
	local p = Instance.new("Part") p.Name = name p.Size = size or V(0.6, 0.2, 0.6)
	p.CFrame = CFrame.lookAt(pos, look) p.Transparency = 1 p.Anchored = true p.CanCollide = false p.CanQuery = false p.CanTouch = false
	for k, v in pairs(attrs or {}) do p:SetAttribute(k, v) end
	p.Parent = S
end
local N, Z = V(0, 0, 1), V(0, 0, -1)
mark("You", V(98, 1.1, 63.4), V(98, 1.1, 64.4))
mark("Rise", V(98, 1.1, 68.8), V(98, 1.1, 67.8))
mark("DodgeTo", V(101.4, 1.1, 63.0), V(101.4, 1.1, 64.0))
mark("ThrownTo", V(95.6, 1.1, 60.4), V(95.6, 1.1, 61.4))
mark("TugYou", V(98, 1.1, 64.6), V(98, 1.1, 65.6))
mark("TugIt", V(98, 1.1, 67.2), V(98, 1.1, 66.2))
local F = Sets.Hall.File:Clone() F.Parent = S
mark("Desk", V(98, 2.37, 66.5), V(98, 2.37, 67.5), V(3, 2.54, 1.96))
mark("Wide", V(88, 7.5, 60.6), V(98, 4, 67))
mark("Bell", V(146.1, 11.4, 57.7), V(146.1, 11.4, 56.7), nil, { BellPart = "Workspace.School.NHProps.SchoolBell_R104.SchoolBell_Bell" })
S.Parent = Sets
return #S:GetChildren() .. " marks"
```

  Expected: `11 marks`.

- [ ] **Step 2: Port table.** Add rows to doc 11's table for `Strike.*`, converted to the Map's Room 102 the same way as the RollCall rows. In the Map, students face +X and Mira's desk is at (−1007.4, 78.1); the NH Combat Test → Map mapping is in doc 11's Results. Example: `Strike.You` → (−1009.6, 0, 78.1) facing +X.
- [ ] **Step 3: Commit** (`2.26.0 (5/8): the fight's marks`).

---

### Task 6: The Strikethrough cut

> **Outcome (2026-11-17):** 16 paths, 0 fixes. The live runs:
> - **All right:** `Arrive>Lunge>Dodge>Again>Shove>Tug>Kept>Finisher>Shatter>Still`, grade S, FileKept `Win`.
> - **All missed:** `Arrive>Lunge>Thrown>Again>Grabbed>Tug>Torn>Finisher>Fade>Still`, grade D, FileKept `Lose`.
>
> **Changes from the table:**
> - **Length:** 56. `CineJudge.LongestPath` is 52.0 s with the slow-motion prompts.
> - **Marks:** two added, `RiseLow` (it rises from it) and `LungeTo` (the lunge lands an arm's length from you). Mira's chair is pushed aside on screen.
> - **Profile shots:** they are a keyed two-shot (`Profile`) from inside the east wall. A full shot cropped the eyes under the letterbox.
> - **Hit times:** they follow the game's clips.
> - **Cameras:**
>   - It rises: in the aisle, over the desk top.
>   - Tug: high, behind your shoulder.
>   - Pages: low and side on.
>   - Still: the back corner.
>   - Several framed versions put the camera through the east or south wall, or behind Mira's desk.
> - **Lighting:** a moonlight SpotLight over the desk and a backlight on the board wall. The template is pale as old paper, with a rim light, so it reads after hours.
> - **Captures:** `review/cut_*.jpg`, taken with `harness/cap.lua`.


**Files:**
- Create: `tools/phase3-2260/live/ReplicatedStorage.Cinematics.Strikethrough.luau`
- Modify: `…ReplicatedStorage.Config.Cine.luau` (entry)
- Test: `analyze_paths.lua` (Strikethrough), `tools/phase3-2260/harness/t_fight.lua`

**Interfaces:**
- Graph (spec §6). The Direction answer is `Left`: it lunges from its right, so you dodge left. The flag is `FileKept` (`Win` or `Lose`).

```lua
Def.Graph = { start = `Arrive`; segments = {
	Arrive  = { len = 7.0; next = `Lunge` };
	Lunge   = { len = 3.2; prompt = { kind = `Direction`; at = 2.1; dur = 0.9; slow = 0.12; options = { `Left`, `Right` }; answer = `Left`; label = `DODGE`;
		on = { Right = `Dodge`; Wrong = `Thrown` } } };
	Dodge   = { len = 1.6; next = `Again` };
	Thrown  = { len = 2.2; next = `Again` };
	Again   = { len = 2.8; prompt = { kind = `Press`; at = 1.6; beat = 0.5; slow = 0.2; label = `SHOVE`; on = { Perfect = `Shove`; Good = `Shove`; Miss = `Grabbed` } } };
	Shove   = { len = 1.8; next = `Tug` };
	Grabbed = { len = 2.0; next = `Tug` };
	Tug     = { len = 3.0; prompt = { kind = `Mash`; at = 0.6; dur = 2.2; rate = 7; touchRate = 5; slow = 0.5; flag = `FileKept`;
		on = { Win = `Kept`; Lose = `Torn` } } };
	Kept    = { len = 1.6; next = `Finisher` };
	Torn    = { len = 1.8; next = `Finisher` };
	Finisher = { len = 3.0; prompt = { kind = `Hold`; at = 0.8; zoneAt = 1.1; zone = 0.15; slow = 0.3; label = `HOLD, RELEASE ON THE SEAL`;
		on = { Hit = `Shatter`; Miss = `Fade` } } };
	Shatter = { len = 3.2; next = `Still` };
	Fade    = { len = 3.6; next = `Still` };
	Still   = { len = 3.0 };
} }
```

- [ ] **Step 1: Failing test.** Run `analyze_paths.lua` with `Strikethrough`. Expected: an error, since the module doesn't exist.

- [ ] **Step 2: Write the cut module.**

  **Header:**
  - `Set = "Strike"`, `Clock = 0.3`.
  - `Actors = { { Name="You"; From="Self"; Mark="You"; Pose="Stand" }, { Name="It"; From="Template:Strikethrough"; Mark="Rise"; Pose="Stand"; Display="???"; Faceless=true } }`.
  - The graph above.

  **`Build(Ctx)`** returns `segments` with these shots and events. Times are segment-relative. Clips are named with `Ctx.Clip` (looked up in `Config.CineClips`: the game's own clips as `Assets:<path>`, the group's uploads as ids) or `Ctx.GameClip` (a path under `Assets.Animations`). Every contact has a hitstop, a shake and an effect on its `Hit` time, and a `flash = { t, dur = 0.05 }` impact frame on heavy hits. The camera stays on the open side of the action line (You ↔ It along z), on the +X side.

  | Segment | Shots (name, dur, framing) | Events |
  |---|---|---|
  | Arrive | "Night room" 3.0 s, keys from `Wide` (28 mm, slow 1-stud push). "The file" 2.2 s: the `File` mark top-down, 50 mm (Collected's keys). "Seep" 1.8 s: CU on `Desk` at 65 mm, low (pitch −6) | t 0.2 `walk` You → `You` (dur 1.6) while the clip plays `Ctx.GameClip("Default.Movement.Walk")` (Task 1 handles the walk). t 3.1: the file prop appears on the desk (as in Collected's Build: folder and page). t 3.5: `bell = { volume = 0.5; speed = 0.5 }` (the wrong hour). t 5.4: `fx` `CombatFX.DownSmoke` at `Desk`, colour ink (seeping ink), and the actor `It` starts below the floor at `Rise` (y −3) |
  | Lunge | "It rises" 2.1 s: MWS low angle (pitch −10, yaw 30, 24 mm, dutch roll −8) on `It`; `anim` It `StrikeRise` at 0. "The lunge" 1.1 s: FS profile (yaw 85) on You; `anim` It `StrikeLunge` at 0.0 | t 0.0 `move`: It rises from y −3 to the mark over 0.7 s. At `StrikeRise`'s `Hit` (Uptilt's, 0.50): `shake 0.4` and `fx CombatFX.Guardbreak` (shards). Lunge t 0.05: `fx CombatFX.Flashstep` black rings at It. The prompt opens at 2.1, the lunge's anticipation creeping in slow-mo (0.12) |
  | Dodge | "Slip" 1.6 s: MS from your left-front (yaw −40) on You | t 0 `anim` You `GameClip("Movement.Dash.LeftVector")`; t 0 `walk` You → `DodgeTo` (dur 0.35); t 0.1 `anim` It `StrikeRecoil` (it overshoots); `fx MovementFX.DashFX` at You |
  | Thrown | "Thrown" 1.2 s: FS profile on You (yaw 85), `flash` at 0.12. "Into the desks" 1.0 s: low wide | t 0.12 `hitstop 0.12`, `shake 0.7`; t 0.12 `anim` You `GameClip("Default.Knockback")`; t 0.12 `walk` You → `ThrownTo` (dur 0.45); t 0.6 `anim` You `GameClip("Weapons.Fist.Movement.Land")`; `fx HitType.Blunt` at You's Torso |
  | Again | "It comes again" 2.8 s: OTS from behind You (yaw 160) toward It, 35 mm, slow push | t 0.4 `anim` It `StrikeLunge` (speed 0.8). Prompt at 1.6 (slow 0.2) |
  | Shove | "Shove" 1.8 s: FS profile (yaw 85) | t 0 `anim` You `GameClip("Weapons.Fist.Moves.Shove")`; t 0.18 `move` part `Desk` to `Desk.CFrame * CFrame.new(0, 0, -1.6)` (dur 0.18); t 0.2 `hitstop 0.1`, `shake 0.5`, `flash`; t 0.2 `anim` It `StrikeStagger`; `fx HitType.Blunt` at It |
  | Grabbed | "Grabbed" 2.0 s: MCU on your arm and face (yaw 30) | t 0.3 `anim` It `StrikeGrab`; at its `Hit` (Clinch's, 0.37): `shake 0.5`, `anim` You `GameClip("Default.Hit.2")` |
  | Tug | "Tug of war" 3.0 s: a steady 3/4 high wide (pitch 18, yaw 50, 35 mm) keeping both bodies and the file between them | t 0 `place` You → `TugYou`, It → `TugIt`; `anim` You `YouTugPull` looped, It `StrikeTug` looped. The prompt opens at 0.6 (slow 0.5); the meter shakes the camera through CineUI's meter |
  | Kept | "The file holds" 1.6 s: CU on the file | t 0.1 `fx CombatFX.Flashstep` at It (it's thrown off); `anim` It `StrikeRecoil` |
  | Torn | "Torn" 1.8 s: CU on the file | t 0.2 the page prop splits: a half-page Part flies off with `move`; `fx` paper colour (`HitType.Slash` tinted paper) |
  | Finisher | "Charge" 3.0 s: MCU on You, slow push (85 → 65 mm). The prompt opens at 0.8 | `anim` You `YouFinisher` at 0.8, played at speed 0 until the release (the cut's events: `{ t = 0.8; anim = { rig = You; id = Ctx.Clip("YouFinisher"); speed = 0.05 } }`); the strike lands in the next segment |
  | Shatter | "Release" 0.6 s: FS profile, `flash` on the `Hit` (0.07). "Pages" 2.6 s: VWS low wide, slow-mo `timescale { scale = 0.35; dur = 1.6 }` | t 0 `anim` You `YouFinisher` (Fist M2, from 0.36; it strikes at 0.43); t 0.07 `hitstop 0.18`, `shake 1.0`; `anim` It `StrikeShatter`; `fx CombatFX.Guardbreak` tinted ink, and again tinted paper; t 0.6 a `call` event tweens every BasePart of `Ctx.Actor("It")` from `LocalTransparencyModifier` 0 to 1 over 1.2 s (TweenService), and disables its ParticleEmitters at 1.4 s |
  | Fade | "It fades" 3.6 s: MS on It; the bell stops | `anim` It `StrikeShatter` (speed 0.6); the `call` fade over 2.5 s; `sound` the bell at volume 0.2, cut off |
  | Still | "Silence" 3.0 s: a wide of the empty room, your back to camera at the desk | t 0.5 `look` You at `File`. The cut ends; After Hours goes to Collected |

  Write every shot as a full table with `name`, `dur`, `subject`, `camera` (frame or keys), `noise`, `dof`. Use the framings above and the 2.24.0 Prologue as the pattern: subjects through `subj()`, keys from marks with `Ctx.Pos` / `Ctx.CF`. A missing `It` (no template) falls back to the `Rise` mark, so the framing holds.

  In `Config.Cine`: `Strikethrough = { Name = "The Strikethrough"; Length = <ceil(CineJudge.LongestPath)+GradeCard+1>; Set = "Strike"; Replay = true; Interactive = true; Rewards = { S = 15; A = 10; B = 5 } }`. Compute the length with `analyze_paths.lua` (it prints "longest"). Change `Collected` to add `Flags = { "FileKept" }`.

- [ ] **Step 3: Analyze every path.** `analyze_paths.lua` with `Strikethrough`. Expected: `16 paths, 0 fixes`:
  - 2 dodge outcomes × 2 shove outcomes × 2 tug outcomes × 2 finisher outcomes = 16.
  - Fix any `[fix]` (blocked subject, eyes out of frame) by re-aiming that shot, as in 2.24.0.

- [ ] **Step 4: Captures.** With the 2.24.0 capture helper (`cap.lua`, adapted for segments through `FlattenForTests`), hold and screenshot:
  - It rising (Lunge 1.0)
  - the lunge's slow-mo at the prompt
  - the Thrown impact frame
  - the Shove contact
  - the Tug wide
  - the Shatter `Hit`
  - the Still wide

  Each must read clearly: silhouettes apart, the line respected, no wall or prop blocking, the ink and pages visible at night.

- [ ] **Step 5: Live paths.** `t_fight.lua` is the 2.25.0 `t_director.lua` pattern, which feeds prompts through `NHCineTestInput`:
  - Direction `Pick Left`, then Press at the beat, a 16-tap Mash, and Hold down at 0.1 / up at 1.1. Expected path: `Arrive>Lunge>Dodge>Again>Shove>Tug>Kept>Finisher>Shatter>Still`, grade S, and `Quests.Decisions.FileKept = "Win"`.
  - A second run with every prompt missed. Expected: `Arrive>Lunge>Thrown>Again>Grabbed>Tug>Torn>Finisher>Fade>Still`, grade D, `FileKept = "Lose"`.
  - Snapshot and restore slot 2 around both runs.
- [ ] **Step 6: Commit** (`2.26.0 (6/8): the Strikethrough cut`).

---

### Task 7: After Hours gets the fight; COLLECTED shows the torn page

> **Outcome (2026-11-18):**
> - **Migration:** `AfterHoursMigrateTest` gave From1 1, From2 2, From3 3 before the fix, then 1, 2, 5 after.
> - **Torn page:** COLLECTED with FileKept `Lose` shows the half page, "STATUS: COLLECTED" on what's left (`review/collected_torn.jpg`).
> - **Quest flow, live:**
>   - **Getting to stage 3:** UseObject MiraFile → stage 2; RecordsExit → stage 3.
>   - **Mira's desk:** the `GoTo` must use offset `Vector3.new(0, 0, 0)`. The default +3 z puts you outside `Area_MiraDesk`.
>   - **The fight:** the Strikethrough plays: grade S.
>   - **After:** stage 5, and COLLECTED plays.
> - **Slot 2:** restored after each run.


**Files:**
- Modify: `…Config.Quests.luau`, `…Quests.Quests.luau` (`MigrateVersion`), `…Cinematics.Collected.luau`, `…Studio.TestBridge.luau`

**Interfaces:**
- **After Hours objectives:** `File`, `Out`, then
  - `Return` = `{ Id = "Return"; Type = "Reach"; Area = "MiraDesk"; Item = "MiraFile"; Text = "Take Mira's file back to her desk in Room 102" }`
  - `Fight` = `{ Id = "Fight"; Type = "Cinematic"; Cut = "Strikethrough"; Text = "Something is waiting at the empty desk" }`

  and then `Collected`.
- **Migration:** `Version = 2; StageShift = 2; StageShiftFrom = 3`. A save at stage 3 (Collected) moves to stage 5; saves at stages 1 and 2 stay.

- [ ] **Step 1: Failing test.** Add to TestBridge:

```lua
-- After Hours v1 saves: a save on Collected (stage 3) moves past the two new stages; earlier stages stay
function Commands.AfterHoursMigrateTest()
	local Q = QuestsService()
	local Def = require(game:GetService(`ReplicatedStorage`).Config.Quests).Quests.AfterHours
	local Out = {}
	for _, Stage in { 1, 2, 3 } do
		local State = { Stage = Stage; V = 1 }
		Q.MigrateForTests(Def, State)
		Out[`From{Stage}`] = State.Stage
	end
	return Out
end
```

  and a Decide command (Decisions are saved by `Quests.Decide`, not by `Progress`):

```lua
function Commands.Decide(PlayerName: string, Id: string, Choice: string)
	return QuestsService().Decide(Players:FindFirstChild(PlayerName), Id, Choice)
end
```

  and to Quests: `function Shared.MigrateForTests(Def, State) Local.MigrateVersion(Def, State) end`.

  Install, Play, then `bridge.py AfterHoursMigrateTest`. Expected: `From1 1, From2 2, From3 3` (no migration yet).

- [ ] **Step 2: Implement.** Replace `Local.MigrateVersion`'s body line:

```lua
		State.Stage = math.clamp((tonumber(State.Stage) or 1) + (Def.StageShift or 0), 1, #Def.Objectives)
```

with:

```lua
		local Stage = tonumber(State.Stage) or 1
		-- (2.26.0) StageShiftFrom: objectives were inserted in the middle, so only saves at or past that stage move
		if Stage >= (Def.StageShiftFrom or 1) then Stage += (Def.StageShift or 0) end
		State.Stage = math.clamp(Stage, 1, #Def.Objectives)
```

  Change After Hours in `Config.Quests` to the objective list above, with `Version = 2; StageShift = 2; StageShiftFrom = 3;`.

- [ ] **Step 3: COLLECTED's torn page.** In `Collected.Build`, after the page is made:

```lua
	-- (2.26.0) lost the tug of war in the finale: half the record tore away (Flags from the server)
	if Ctx.Flags.FileKept == `Lose` then
		Page.Size = Vector3.new(2.7, 0.02, 1.15)
		Page.CFrame = Page.CFrame * CFrame.new(0, 0, -0.42)
		Gui.CanvasSize = Vector2.new(400, 300)
		for _, L in Gui:GetChildren() do
			if L:IsA(`TextLabel`) and L.Position.Y.Offset > 260 then L.Position = L.Position - UDim2.fromOffset(0, 230) end
			if L:IsA(`TextLabel`) and L.Position.Y.Offset > 100 and L.Position.Y.Offset < 260 then L:Destroy() end
		end
	end
```

  The status line moves up onto the surviving half. Name, homeroom and seat are torn away; the header and STATUS stay.

- [ ] **Step 4: Verify.**
  - Install, Play, `start_play.lua`, then `bridge.py AfterHoursMigrateTest`. Expected: `From1 1, From2 2, From3 5`.
  - Snapshot slot 2. Set `Decisions.FileKept = "Lose"` with `bridge.py Decide $P '"FileKept"' '"Lose"'`. Mark Collected Seen and replay it.
  - Capture the file at 3.4 s. Expected: the half page with the header and "STATUS: COLLECTED".
  - Restore slot 2.
- [ ] **Step 5: The quest flow.**
  1. Snapshot. Then `ResetQuests $P`, and give the slot After Hours at stage 2 with the file: `StartQuest $P '"AfterHours"'`, then `QuestProgress $P '"Collect"' '"MiraFile"'`.
  2. `GoTo $P '"QuestArea"' '"RecordsExit"'`. Expected: stage 3 (`Return`).
  3. `GoTo $P '"QuestArea"' '"MiraDesk"'`. Expected: stage 4, and the Strikethrough plays (`CineState` shows a session).
  4. Skip-safe check: the cut can't be skipped the first time. Feed the prompts as in Task 6 Step 5. Expected after it ends: stage 5, and COLLECTED plays.
  5. Restore.
- [ ] **Step 6: Commit** (`2.26.0 (7/8): After Hours ends in the fight; COLLECTED's torn page`).

---

### Task 8: Final checks, docs, release 2.26.0

> **Outcome (2026-11-18):**
> - **Self-tests:** CineJudgeTest 36/36, CineGraphTest 9/9, CineQteTest, CineVoteTest, Phase1SelfTest and AfterHoursMigrateTest (1, 2, 5) pass. `AfterLeaveEnded`, `OldSlotCanStart` and `NewKidBeforeOrientation` are false by design.
> - **The prologue:** slot 2 hasn't seen it, so `Replay` is refused. Start it with `bridge.py PlayCut $P '"Prologue"' true` instead, and clear `NHCinePath` on the client before each run. Answer>Holt and Late>Holt.
> - **The fight:** S on the Dodge/Shove/Kept/Shatter path, D on the Thrown/Grabbed/Torn/Fade path, FileKept Lose.
> - **Console:** 0 errors from Cine, CinePrompt, CineUI, CineJudge or Quests. Slot 2 restored and matched its snapshot.

- [x] **Step 1: Regression in one session.**
  - `CineJudgeTest`, `CineGraphTest`, `CineQteTest`, `CineVoteTest`, `Phase1SelfTest` and `AfterHoursMigrateTest`.
  - The prologue's two live paths (2.25.0 `t_prologue.lua`).
  - `t_fight.lua`'s two paths.
  - A console check (no errors from Cine, CinePrompt, CineUI, CineJudge, Quests).
  - Restore slot 2, then `save_place`.
- [x] **Step 2: Docs.**
  - **CHANGELOG `[2.26.0]`:**
    - the finale, the clips (sources and measured numbers, from `REPORT.md`), the template and the quest change
    - "Checked" with every number, and "Not checked": a two-player run, phone screens, the published clip ids (Studio previews until the owner publishes, per `PUBLISH.md`)
  - **README:** a Latest-update line.
  - **Implementation-Status:** a row.
  - **Discord:**
    - a game-update post, `2026-11-xx-the-strikethrough.md`
    - an **announcement** in `updates/discord/announcements/`: this completes the Chapter One wave (2.22 to 2.26: foundations, the roll call, cutscenes you play, the finale), written as a launch post with emoji headers and a "full notes in #game-updates" footer
    - both indexes updated
  - **Doc 12:** part B marked shipped.
  - **Doc 11:** the port table rows.
  - **Vault:** copies, the home note's game-update line and its announcement line.
- [x] **Step 3: Commit and merge** (`2.26.0: the Strikethrough, Chapter One's finale`). Stage only this plan's files, and use the hunk-staging method for CHANGELOG if another session's hunk is still there. Then merge `phase3-2260` into `main`, stashing other sessions' working-tree changes around the checkout and popping them after.

---

## Self-review

- **Spec coverage:**
  - §6: segments 1 to 6 in Task 6, the After Hours stage in Task 7, the torn page in Task 7, the R6 body, ink and pages in Task 4.
  - §8: reuse in Task 6's shot table (Dash, Knockback, Shove, Hit, Land, Walk). The derivation from measured related clips is Tasks 2 and 3, with sources named in `clips.json` and `REPORT.md`. Realistic legs and the house style are gated in Task 3 Steps 2 and 3.
  - §5 flags and rewards: Tasks 1, 6, 7.
- **Placeholders:** the clip angles are not invented in this plan. They are produced by `extract.luau` → `convert.py` from named source clips, which is the owner's rule; Task 3 changes only timing, offsets and contact. Task 6 gives every shot its framing, subject and events. The implementer writes them as Lua tables in the Prologue's pattern.
- **Types:**
  - `Ctx.Clip`, `Ctx.GameClip`, `Ctx.Flags` and the `fx` / `move` events (Task 1) are used in Tasks 6 and 7.
  - The `Config.CineClips` keys match the nine `clips.json` targets.
  - The flag `FileKept` is the same in Tasks 6 and 7.
  - `StageShiftFrom` is defined in Task 7 Step 2 and used in its config.
- **Known risk:** R6 group animations may not load in `KeyframeSequenceProvider` if Studio lacks group permissions. Task 2 Step 2 handles that with each target's alternate source; the Knockback sign check needs one loadable R6 clip. If none loads, stop and ask the owner to grant access.
