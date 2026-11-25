# Chat and Factions panel: iron and candle, quiet. Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the top-left chat window and the Factions panel in the UI kit's iron and candle look, quiet when idle, with subtle shared animations.

**Architecture:**
- **`ReplicatedStorage.UI.Motion` (new):** a ModuleScript that holds every animation (smoke-in text, wake and quiet fades, candle flicker, edge glint, staggered rise, bar fill, rank pips, panel open and close). Candles and glints share one Heartbeat connection.
- **`Controllers.Gui.Chat` and `Controllers.Gui.FactionsPanel`:** edited in place to use Motion and the new look. Their behaviour and public API are unchanged.
- **Mirrors:** everything is mirrored in `tools/chat-factions-ui/live/` and installed in Edit with `install_inplace.py`.

**Tech Stack:** Luau (Roblox), TweenService, RunService.Heartbeat, the NH UI kit (`ReplicatedStorage.UI.Components`, `UI.Theme`). Python tools in `tools/admin-console/` (`fetch.py`, `install_inplace.py`, `run_check.py`, `run_live.py`).

**Spec:** `docs/superpowers/specs/2026-11-25-chat-factions-ui-design.md`

## Global Constraints

**Place**
- NH Combat Test, studio_id `b9e911b4-f488-4744-a550-024551f9f30a`.
- Installs in **Edit only**. Before any install, call `get_studio_state`: other sessions share this Studio, so if it's in Play, wait.
- Never save the place.

**Install and backup**
- The backup name for every install is `ChatFactionsUI_pre_20261125`.
- Install with `install_inplace.py`. Its orig is a fresh `fetch.py` of the same paths into `tools/chat-factions-ui/_orig/` (gitignored).

**Behaviour that must not change**
- The chat's public API: `Shared.Build`, `SetShown`, `IsShown`, `Focus`, `OnStart` and `Preview`, with their signatures.
- TextChatService sending and receiving, the `NHCanChat` gate, / to talk, Enter, Esc keeps the draft, Up / Down history, `Packages.Bind.Typing`.
- `MAX_LINES` 120, `MAX_CHARS` 200, `SEND_GAP` 0.6, `IDLE_AFTER` 10, and the name inks.

**Factions panel**
- `TOGGLE_KEY` stays `Enum.KeyCode.L`.
- `Shared.Toggle(Open?)` and `Shared.OnStart` keep their signatures.
- It still reads `PlayerData.Social` and re-renders on `SetSocial`.
- Equip still fires `Packets.SocialAction` `{ Action = "EquipTitle"; Title = ... }`.

**Look and motion**
- Faction colours come from `Config.Factions.Factions[Id].Color`.
- Reduced motion (`NHReducedMotion`) means end states at once, and no flicker or glint.

**Who does what**
- Play rounds are run by the controller, not the implementer.
- Play round recipe:
  1. `start_stop_play` true.
  2. `bash tools/forms/harness/round_start.sh`.
  3. Cine: `python -X utf8 -I tools/admin-console/run_check.py Server tools/soccer2/checks/cine.lua`.
  4. The checks.
  5. `python -X utf8 -I tools/forms/harness/restore.py`.
  6. Cine again.
  7. `start_stop_play` false.
- The run commands differ by side:
  - Client checks run with `python -X utf8 -I tools/admin-console/run_live.py <file> <timeout> Client`. A check file must not contain `]==]`.
  - Edit checks run with `python -X utf8 -I tools/admin-console/run_check.py Edit <file>`.

**Commits**
- Each commit message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- After code changes, run `graphify update .` if `graphify` is on PATH. Skip it if not.

## Rulings (plan-time, against the current code)

- **Chat edits, not rewrites.** `Gui.Chat` already fades, has `Local.Reduced()`, and owns all the behaviour. The rebuild
  replaces its header mark, adds the vignette and the candle, swaps `SetFaded` for a full quiet state through
  `Motion.Wake`, and swaps the line fade for `Motion.SmokeIn`. What it costs if wrong: a later full rewrite. That would
  be safe, because the check covers the behaviour.
- **Factions panel:**
  - `Render` gains an `Animate` flag. It's true only on open, never on the `SetSocial` re-render, so updates don't
    replay the animation.
  - `Render` now returns early on `Ui.Open`, not `Panel.Visible`, because the panel stays visible while its close
    animation plays.
- **Test hooks:** both modules gain a `Shared.ForTests` table. It's read only by checks.

## Files

| File | Responsibility |
|---|---|
| `tools/chat-factions-ui/live/ReplicatedStorage.UI.Motion.luau` (create) | the shared animations |
| `tools/chat-factions-ui/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.Chat.luau` (create from `pre/`, then modify) | the chat window |
| `tools/chat-factions-ui/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.FactionsPanel.luau` (create from `pre/`, then modify) | the Factions panel |
| `tools/chat-factions-ui/checks/motion_edit.lua`, `motion_play.lua`, `chat_play.lua`, `factions_play.lua` (create) | checks |
| `tools/chat-factions-ui/harness/make_motion.lua` (create) | creates the empty `UI.Motion` ModuleScript once |
| `tools/chat-factions-ui/.gitignore` (create) | `_orig/` |
| `tools/chat-factions-ui/REPORT.md`, `docs/UI-Kit.md`, `CHANGELOG.md` (modify) | the record |

---

### Task 1: `UI.Motion`

**Files:**
- Create: `tools/chat-factions-ui/.gitignore`
- Create: `tools/chat-factions-ui/harness/make_motion.lua`
- Create: `tools/chat-factions-ui/live/ReplicatedStorage.UI.Motion.luau`
- Create: `tools/chat-factions-ui/checks/motion_edit.lua`
- Create: `tools/chat-factions-ui/checks/motion_play.lua`

**Interfaces:**
- Consumes: `ReplicatedStorage.UI.Components` (`Kit.FadeIn(root, duration)`, `Kit.FadeOut(root, duration)`). `FadeOut`
  remembers each descendant's built transparency in `NHBase*` attributes, and `FadeIn` returns to it.
- Produces (`require(ReplicatedStorage.UI.Motion)`):
  - `Motion.ForceReduced: boolean?`: checks set it; nil follows the player's setting.
  - `Motion.Reduced(): boolean`
  - `Motion.Play(Inst, Time, Goal, Style?): Tween`: one tween per instance; a new one cancels the old.
  - `Motion.SmokeIn(Label: TextLabel, Delay: number?)`
  - `Motion.Wake(Items: { { Instance, {[string]: any}, {[string]: any} } }, On: boolean, Instant: boolean?)`
  - `Motion.Candle(Flame: ImageLabel, Holder: GuiObject?)`
  - `Motion.Glint(Target: Instance, Prop: string, A: Color3, B: Color3, Holder: GuiObject?)`
  - `Motion.Stop(Inst: Instance)`
  - `Motion.ActiveCount(): number`
  - `Motion.Rise(Items: { GuiObject }, Step: number?)`
  - `Motion.Fill(Bar: GuiObject, Delay: number?)`: `Bar` is a `Kit.Bar` root with a `Fill` child.
  - `Motion.Pips(Pips: { GuiObject }, Count: number, On: Color3, Off: Color3, Delay: number?)`
  - `Motion.Open(Panel: GuiObject)`, `Motion.Close(Panel: GuiObject)`

- [ ] **Step 1: The ignore file and the stub maker**

`tools/chat-factions-ui/.gitignore`:
```
_orig/
```

`tools/chat-factions-ui/harness/make_motion.lua`:
```lua
-- make_motion (chat-factions-ui, Edit): creates ReplicatedStorage.UI.Motion as an empty ModuleScript, once, so
-- install_inplace.py (which only sets Source on existing scripts) can install it.
local UI = game.ReplicatedStorage:FindFirstChild("UI")
if not UI then return "FAIL no ReplicatedStorage.UI" end
local M = UI:FindFirstChild("Motion")
if M then return "PASS already there (" .. M.ClassName .. ")" end
M = Instance.new("ModuleScript")
M.Name = "Motion"
M.Source = "return {}\n"
M.Parent = UI
return "PASS made ReplicatedStorage.UI.Motion"
```

- [ ] **Step 2: Write the failing Edit check**

`tools/chat-factions-ui/checks/motion_edit.lua`:
```lua
-- motion_edit (chat-factions-ui, Edit): UI.Motion has every helper, and with reduced motion every helper leaves the end
-- state at once (no tween, no loop). The animated paths are checked in Play (motion_play.lua).
local M = game.ReplicatedStorage.UI:FindFirstChild("Motion")
if not M then return "FAIL no UI.Motion" end
local C = M:Clone()
C.Parent = M.Parent -- it requires script.Parent.Components
local Okr, Motion = pcall(require, C)
C:Destroy()
if not Okr then return "FAIL require: " .. tostring(Motion) end
if type(Motion) ~= "table" then return "FAIL UI.Motion returns " .. typeof(Motion) end
local Fails = {}
local function Ok(Cond, What) if not Cond then table.insert(Fails, What) end end
for _, Name in { "Reduced", "Play", "SmokeIn", "Wake", "Candle", "Glint", "Stop", "ActiveCount", "Rise", "Fill", "Pips", "Open", "Close" } do
	Ok(type(Motion[Name]) == "function", "missing " .. Name)
end
if #Fails > 0 then return "FAIL " .. table.concat(Fails, "; ") end
Motion.ForceReduced = true
Ok(Motion.Reduced() == true, "ForceReduced ignored")
local G = Instance.new("ScreenGui")
local L = Instance.new("TextLabel")
L.TextTransparency = 0.1
L.Position = UDim2.fromOffset(15, 0)
L.Parent = G
Motion.SmokeIn(L)
Ok(L.TextTransparency == 0.1 and L.Position == UDim2.fromOffset(15, 0), "SmokeIn (reduced) changed the label")
local F = Instance.new("Frame")
F.BackgroundTransparency = 0.5
F.Parent = G
local Items = { { F, { BackgroundTransparency = 0 }, { BackgroundTransparency = 1 } } }
Motion.Wake(Items, false)
Ok(F.BackgroundTransparency == 1, "Wake quiet (reduced) " .. F.BackgroundTransparency)
Motion.Wake(Items, true)
Ok(F.BackgroundTransparency == 0, "Wake awake (reduced) " .. F.BackgroundTransparency)
local Base = Motion.ActiveCount()
local Flame = Instance.new("ImageLabel")
Flame.Parent = G
Motion.Candle(Flame, nil)
local S = Instance.new("UIStroke")
S.Parent = F
Motion.Glint(S, "Color", Color3.new(1, 0, 0), Color3.new(0, 0, 1), nil)
Ok(S.Color == Color3.new(1, 0, 0), "Glint (reduced) didn't set A")
Ok(Motion.ActiveCount() == Base, "Candle or Glint joined the loop under reduced motion")
local Bar = Instance.new("Frame")
local Fill = Instance.new("Frame")
Fill.Name = "Fill"
Fill.Size = UDim2.new(0.4, -4, 1, -4)
Fill.Parent = Bar
Bar.Parent = G
Motion.Fill(Bar, 0)
Ok(Fill.Size == UDim2.new(0.4, -4, 1, -4), "Fill (reduced) changed the size")
local Pips = {}
for I = 1, 5 do
	local P = Instance.new("Frame")
	P.Parent = G
	Pips[I] = P
end
Motion.Pips(Pips, 3, Color3.new(1, 1, 0), Color3.new(0, 0, 0), 0)
Ok(Pips[3].BackgroundColor3 == Color3.new(1, 1, 0) and Pips[4].BackgroundColor3 == Color3.new(0, 0, 0), "Pips (reduced)")
local Panel = Instance.new("Frame")
Panel.Visible = false
Panel.Parent = G
Motion.Open(Panel)
Ok(Panel.Visible, "Open (reduced) left it hidden")
Motion.Close(Panel)
Ok(not Panel.Visible, "Close (reduced) left it shown")
Motion.ForceReduced = nil
G:Destroy()
return if #Fails == 0 then "PASS motion_edit" else "FAIL " .. table.concat(Fails, "; ")
```

- [ ] **Step 3: Create the stub in Studio and run the check (RED)**

Run `get_studio_state` (it must be Edit), then:
```
cd E:/NH-chatui
python -X utf8 -I tools/admin-console/run_check.py Edit tools/chat-factions-ui/harness/make_motion.lua
python -X utf8 -I tools/admin-console/run_check.py Edit tools/chat-factions-ui/checks/motion_edit.lua
```
Expected: `PASS made ReplicatedStorage.UI.Motion`, then `FAIL missing Reduced; missing Play; ...`.

- [ ] **Step 4: Write `UI.Motion`**

`tools/chat-factions-ui/live/ReplicatedStorage.UI.Motion.luau`:
```lua
--[[
	UI.Motion (chat-factions-ui, 2026-11-25): the small shared animations of the iron-and-candle screens
	(Controllers.Gui.Chat, Controllers.Gui.FactionsPanel). Spec: docs/superpowers/specs/2026-11-25-chat-factions-ui-design.md.

	- Every helper honours Settings > Reduce Motion (player attribute NHReducedMotion): the end state at once, and no
	  flicker or glint. Motion.ForceReduced (true / false) overrides the setting for checks; nil follows it.
	- One tween per instance at a time: a new one cancels the old (never stacked).
	- Candles and glints share one Heartbeat connection, connected only while something is registered. An entry leaves
	  when its instance leaves the DataModel; it pauses while its Holder is hidden.
]]

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local Kit = require(script.Parent:WaitForChild("Components"))

local Motion = {}
Motion.ForceReduced = nil :: boolean?

local Running = setmetatable({}, { __mode = "k" }) :: { [Instance]: Tween }
local Candles = {} :: { [ImageLabel]: { Size: UDim2, T: number, Phase: number, Holder: GuiObject? } }
local Glints = {} :: { [Instance]: { Prop: string, A: Color3, B: Color3, Phase: number, Holder: GuiObject? } }
local Opening = setmetatable({}, { __mode = "k" }) :: { [GuiObject]: number }
local Beat: RBXScriptConnection? = nil

function Motion.Reduced(): boolean
	if Motion.ForceReduced ~= nil then
		return Motion.ForceReduced
	end
	local P = Players.LocalPlayer
	return P ~= nil and P:GetAttribute("NHReducedMotion") == true
end

function Motion.Play(Inst: Instance, Time: number, Goal: { [string]: any }, Style: Enum.EasingStyle?): Tween
	local Old = Running[Inst]
	if Old then
		Old:Cancel()
	end
	local T = TweenService:Create(Inst, TweenInfo.new(Time, Style or Enum.EasingStyle.Quad, Enum.EasingDirection.Out), Goal)
	Running[Inst] = T
	T.Completed:Once(function()
		if Running[Inst] == T then
			Running[Inst] = nil
		end
	end)
	T:Play()
	return T
end

local function settle(Inst: Instance, Goal: { [string]: any })
	local Old = Running[Inst]
	if Old then
		Old:Cancel()
		Running[Inst] = nil
	end
	local Any: any = Inst
	for K, V in Goal do
		Any[K] = V
	end
end

---| Text |---

-- A new line drifts in: from transparent and 8 px left to how it was built, over 0.35 s.
function Motion.SmokeIn(Label: TextLabel, Delay: number?)
	if Motion.Reduced() then
		return
	end
	local T0, S0, P0 = Label.TextTransparency, Label.TextStrokeTransparency, Label.Position
	Label.TextTransparency, Label.TextStrokeTransparency = 1, 1
	Label.Position = P0 + UDim2.fromOffset(-8, 0)
	local function go()
		if Label.Parent then
			Motion.Play(Label, 0.35, { TextTransparency = T0, TextStrokeTransparency = S0, Position = P0 })
		end
	end
	if Delay and Delay > 0 then
		task.delay(Delay, go)
	else
		go()
	end
end

---| Wake / quiet |---

-- Items: { { Inst, AwakeGoal, QuietGoal } }. On = true tweens each to AwakeGoal over 0.25 s; false to QuietGoal over 0.6 s.
function Motion.Wake(Items: { { any } }, On: boolean, Instant: boolean?)
	local Time = if On then 0.25 else 0.6
	for _, It in Items do
		local Inst, Goal = It[1], if On then It[2] else It[3]
		if Inst then
			if Instant or Motion.Reduced() then
				settle(Inst, Goal)
			else
				Motion.Play(Inst, Time, Goal)
			end
		end
	end
end

---| The shared loop: candles and glints |---

local function shown(Holder: GuiObject?): boolean
	return Holder == nil or Holder.Visible
end

local function step()
	local Now = os.clock()
	for Flame, E in Candles do
		if not Flame:IsDescendantOf(game) then
			Candles[Flame] = nil
		elseif shown(E.Holder) then
			local W = 1 + 0.06 * math.sin(Now * 3.7 + E.Phase) + 0.03 * math.sin(Now * 11.3 + E.Phase * 2)
			local H = 1 + 0.09 * math.sin(Now * 3.7 + E.Phase + 0.6) + 0.04 * math.sin(Now * 9.1 + E.Phase)
			Flame.Size = UDim2.new(E.Size.X.Scale * W, E.Size.X.Offset * W, E.Size.Y.Scale * H, E.Size.Y.Offset * H)
			Flame.ImageTransparency = math.clamp(E.T + 0.12 * (0.5 + 0.5 * math.sin(Now * 5.3 + E.Phase)), 0, 1)
		end
	end
	for Inst, E in Glints do
		if not Inst:IsDescendantOf(game) then
			Glints[Inst] = nil
		elseif shown(E.Holder) then
			local K = 0.5 + 0.5 * math.sin(Now * (2 * math.pi / 5) + E.Phase)
			local Any: any = Inst
			Any[E.Prop] = E.A:Lerp(E.B, K)
		end
	end
	if next(Candles) == nil and next(Glints) == nil and Beat then
		Beat:Disconnect()
		Beat = nil
	end
end

local function ensureBeat()
	if not Beat then
		Beat = RunService.Heartbeat:Connect(step)
	end
end

-- A candle flame flickers (size and transparency, about 1.7 s a cycle) around how it was built.
function Motion.Candle(Flame: ImageLabel, Holder: GuiObject?)
	if Motion.Reduced() then
		return
	end
	Candles[Flame] = { Size = Flame.Size, T = Flame.ImageTransparency, Phase = math.random() * 6.28, Holder = Holder }
	ensureBeat()
end

-- An edge breathes between A and B (about 5 s a cycle). Prop is the colour property ("ImageColor3", "Color").
function Motion.Glint(Target: Instance, Prop: string, A: Color3, B: Color3, Holder: GuiObject?)
	local Any: any = Target
	Any[Prop] = A
	if Motion.Reduced() then
		return
	end
	Glints[Target] = { Prop = Prop, A = A, B = B, Phase = math.random() * 6.28, Holder = Holder }
	ensureBeat()
end

-- Leaves the loop; a candle goes back to its built size.
function Motion.Stop(Inst: Instance)
	local E = Candles[Inst :: any]
	if E then
		local F = Inst :: ImageLabel
		F.Size = E.Size
		F.ImageTransparency = E.T
	end
	Candles[Inst :: any] = nil
	Glints[Inst] = nil
end

function Motion.ActiveCount(): number
	local N = 0
	for _ in Candles do
		N += 1
	end
	for _ in Glints do
		N += 1
	end
	return N
end

---| Panels |---

-- Sections fade up one after another (Step apart). They sit in list layouts, so they don't move.
function Motion.Rise(Items: { GuiObject }, Step: number?)
	if Motion.Reduced() then
		return
	end
	for I, Item in Items do
		Kit.FadeOut(Item, 0.01)
		task.delay(0.05 + (I - 1) * (Step or 0.15), function()
			if Item.Parent then
				Kit.FadeIn(Item, 0.4)
			end
		end)
	end
end

-- A Kit.Bar fills from 0 to its built size over 1.1 s.
function Motion.Fill(Bar: GuiObject, Delay: number?)
	local Fill = Bar:FindFirstChild("Fill") :: GuiObject?
	if not Fill or Motion.Reduced() then
		return
	end
	local Target = Fill.Size
	Fill.Size = UDim2.new(0, 0, Target.Y.Scale, Target.Y.Offset)
	task.delay(Delay or 0, function()
		if Fill.Parent then
			Motion.Play(Fill, 1.1, { Size = Target }, Enum.EasingStyle.Quart)
		end
	end)
end

-- Rank pips: the first Count light one at a time in On (0.15 s apart); the rest stay Off.
function Motion.Pips(Pips: { GuiObject }, Count: number, On: Color3, Off: Color3, Delay: number?)
	local Reduced = Motion.Reduced()
	for I, P in Pips do
		P.BackgroundColor3 = if Reduced and I <= Count then On else Off
	end
	if Reduced then
		return
	end
	for I = 1, math.min(Count, #Pips) do
		task.delay((Delay or 0) + (I - 1) * 0.15, function()
			if Pips[I].Parent then
				Motion.Play(Pips[I], 0.3, { BackgroundColor3 = On })
			end
		end)
	end
end

local function scaler(Panel: GuiObject): UIScale
	local S = Panel:FindFirstChild("NHOpenScale") :: UIScale?
	if not S then
		local New = Instance.new("UIScale")
		New.Name = "NHOpenScale"
		New.Parent = Panel
		S = New
	end
	return S :: UIScale
end

-- Shows a panel: it scales up from 0.985 and rises 10 px while it fades in (0.3 s).
function Motion.Open(Panel: GuiObject)
	Opening[Panel] = (Opening[Panel] or 0) + 1
	Panel.Visible = true
	local S = scaler(Panel)
	if Panel:GetAttribute("NHOpenPos") == nil then
		Panel:SetAttribute("NHOpenPos", Panel.Position)
	end
	local Base = Panel:GetAttribute("NHOpenPos") :: UDim2
	if Motion.Reduced() then
		settle(S, { Scale = 1 })
		settle(Panel, { Position = Base })
		if Panel:GetAttribute("NHBaseT") ~= nil then
			Kit.FadeIn(Panel, 0.01) -- back from an animated close
		end
		return
	end
	S.Scale = 0.985
	Panel.Position = Base + UDim2.fromOffset(0, 10)
	Motion.Play(S, 0.3, { Scale = 1 })
	Motion.Play(Panel, 0.3, { Position = Base })
	Kit.FadeIn(Panel, 0.3)
end

-- Hides a panel: the reverse over 0.2 s. Opening it again before that keeps it open.
function Motion.Close(Panel: GuiObject)
	Opening[Panel] = (Opening[Panel] or 0) + 1
	local Mine = Opening[Panel]
	if Motion.Reduced() or not Panel.Visible then
		Panel.Visible = false
		return
	end
	Motion.Play(scaler(Panel), 0.2, { Scale = 0.985 })
	Kit.FadeOut(Panel, 0.2)
	task.delay(0.22, function()
		if Opening[Panel] == Mine then
			Panel.Visible = false
		end
	end)
end

return Motion
```

- [ ] **Step 5: Install it**

Run `get_studio_state` (it must be Edit), then:
```
cd E:/NH-chatui
python -X utf8 -I tools/admin-console/fetch.py tools/chat-factions-ui/_orig ReplicatedStorage.UI.Motion
python -X utf8 -I tools/admin-console/install_inplace.py tools/chat-factions-ui/_orig tools/chat-factions-ui/live ChatFactionsUI_pre_20261125 ReplicatedStorage.UI.Motion
```
Expected: `ok ReplicatedStorage.UI.Motion ...`, then a line naming `ReplicatedStorage.UI.Motion ModuleScript <bytes>`, with
no `PARSE FAIL`, `MISSING` or `CHANGED SINCE`.

- [ ] **Step 6: Run the Edit check (GREEN)**

```
python -X utf8 -I tools/admin-console/run_check.py Edit tools/chat-factions-ui/checks/motion_edit.lua
```
Expected: `PASS motion_edit`.

- [ ] **Step 7: Write the Play check (the controller runs it)**

`tools/chat-factions-ui/checks/motion_play.lua`:
```lua
-- motion_play (chat-factions-ui, Client, Play): UI.Motion's animated paths reach their end states, an interrupted fade
-- is replaced, a panel reopened mid-close stays open, and the shared loop flickers a candle and lets it go on destroy.
local Motion = require(game.ReplicatedStorage.UI.Motion)
local P = game.Players.LocalPlayer
local Fails = {}
local function Ok(Cond, What) if not Cond then table.insert(Fails, What) end end
Motion.ForceReduced = false
local Base = Motion.ActiveCount() -- the live chat's and panel's candles may already be in the loop
local G = Instance.new("ScreenGui")
G.Name = "MotionCheck"
G.Parent = P.PlayerGui

local L = Instance.new("TextLabel")
L.TextTransparency = 0.1
L.Position = UDim2.fromOffset(15, 0)
L.Parent = G
Motion.SmokeIn(L)
Ok(L.TextTransparency == 1, "SmokeIn doesn't start hidden")
task.wait(0.6)
Ok(math.abs(L.TextTransparency - 0.1) < 0.01 and L.Position == UDim2.fromOffset(15, 0), "SmokeIn end " .. L.TextTransparency)

local F = Instance.new("Frame")
F.BackgroundTransparency = 0
F.Parent = G
local Items = { { F, { BackgroundTransparency = 0 }, { BackgroundTransparency = 1 } } }
Motion.Wake(Items, false)
task.wait(0.15)
Motion.Wake(Items, true) -- replaces the fade-out half way
task.wait(0.45)
Ok(F.BackgroundTransparency < 0.01, "Wake: the interrupted fade didn't end awake " .. F.BackgroundTransparency)

local Flame = Instance.new("ImageLabel")
Flame.Size = UDim2.fromOffset(12, 14)
Flame.Parent = G
Motion.Candle(Flame, nil)
local S = Instance.new("UIStroke")
S.Parent = F
Motion.Glint(S, "Color", Color3.new(1, 0, 0), Color3.new(0, 0, 1), nil)
Ok(Motion.ActiveCount() == Base + 2, ("loop entries %d, want %d"):format(Motion.ActiveCount(), Base + 2))
local Seen = {}
for _ = 1, 12 do
	task.wait(0.05)
	Seen[math.floor(Flame.Size.X.Offset * 100)] = true
end
local N = 0
for _ in Seen do N += 1 end
Ok(N >= 3, "the candle doesn't flicker (" .. N .. " sizes)")

local Bar = Instance.new("Frame")
local Fill = Instance.new("Frame")
Fill.Name = "Fill"
Fill.Size = UDim2.new(0.4, -4, 1, -4)
Fill.Parent = Bar
Bar.Parent = G
Motion.Fill(Bar, 0)
Ok(Fill.Size.X.Scale == 0, "Fill doesn't start empty")
task.wait(1.3)
Ok(Fill.Size == UDim2.new(0.4, -4, 1, -4), "Fill end " .. tostring(Fill.Size))

local Pips = {}
for I = 1, 5 do
	local Q = Instance.new("Frame")
	Q.Parent = G
	Pips[I] = Q
end
Motion.Pips(Pips, 3, Color3.new(1, 1, 0), Color3.new(0, 0, 0), 0)
Ok(Pips[1].BackgroundColor3 == Color3.new(0, 0, 0), "Pips don't start off")
task.wait(0.9)
Ok(Pips[3].BackgroundColor3 == Color3.new(1, 1, 0) and Pips[4].BackgroundColor3 == Color3.new(0, 0, 0), "Pips end")

local Panel = Instance.new("Frame")
Panel.Visible = false
Panel.Parent = G
local T = Instance.new("TextLabel")
T.Parent = Panel
Motion.Open(Panel)
task.wait(0.5)
Ok(Panel.Visible and T.TextTransparency == 0 and Panel.NHOpenScale.Scale == 1, "Open end")
Motion.Close(Panel)
task.wait(0.1)
Motion.Open(Panel) -- reopened mid-close
task.wait(0.5)
Ok(Panel.Visible and T.TextTransparency == 0, "reopened mid-close but hidden or faded")
Motion.Close(Panel)
task.wait(0.5)
Ok(not Panel.Visible, "Close end")

G:Destroy()
task.wait(0.2)
Ok(Motion.ActiveCount() == Base, ("loop entries after destroy %d, want %d"):format(Motion.ActiveCount(), Base))
Motion.ForceReduced = nil
return if #Fails == 0 then "PASS motion_play" else "FAIL " .. table.concat(Fails, "; ")
```

- [ ] **Step 8: Commit**

```
git add tools/chat-factions-ui/.gitignore tools/chat-factions-ui/harness tools/chat-factions-ui/live/ReplicatedStorage.UI.Motion.luau tools/chat-factions-ui/checks/motion_edit.lua tools/chat-factions-ui/checks/motion_play.lua
git commit -m "Chat and Factions UI, Task 1: UI.Motion (smoke-in, wake, candle, glint, rise, fill, pips, open/close), installed in Edit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 9 (controller): Play round**

`motion_play.lua` through `run_live.py ... 60 Client`. Expected: `PASS motion_play`.

---

### Task 2: The chat, quiet and lit

**Files:**
- Create: `tools/chat-factions-ui/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.Chat.luau`, copied from `tools/chat-factions-ui/pre/` and then modified as below
- Create: `tools/chat-factions-ui/checks/chat_play.lua`

**Interfaces:**
- Consumes: `Motion.SmokeIn`, `Motion.Wake`, `Motion.Candle`, `Motion.Glint` (Task 1). Theme image keys
  `CandleBody`, `CandleFlame` and `Glow`. `Kit.Image(key, props)` makes an ImageLabel named `key` unless `Name` is given.
- Produces:
  - `Shared.ForTests = { Ui: () -> table?, State: table, Send: (Text: string) -> () }`.
  - The `Ui` table also gains `Flame`, `Candle` and `Vignette`.

- [ ] **Step 1: Copy the module**

```
cp tools/chat-factions-ui/pre/StarterPlayer.StarterPlayerScripts.Controllers.Gui.Chat.luau tools/chat-factions-ui/live/
```

- [ ] **Step 2: Write the failing Play check**

`tools/chat-factions-ui/checks/chat_play.lua`:
```lua
-- chat_play (chat-factions-ui, Client, Play): the rebuilt chat. A sent note arrives as a line and joins the history,
-- the frame sinks to text only when quiet and wakes on Focus, the draft holds, SetShown and NHCanChat hide it.
local P = game.Players.LocalPlayer
local Chat = require(P.PlayerScripts.Controllers.Gui.Chat)
local T = Chat.ForTests
if not T then return "FAIL no Chat.ForTests" end
local U = T.Ui()
if not U then return "FAIL the chat isn't built" end
if not U.Vignette or not U.Flame then return "FAIL no vignette or candle" end
local S = T.State
local Fails = {}
local function Ok(Cond, What) if not Cond then table.insert(Fails, What) end end
local function lineWith(Text: string): TextLabel?
	for _, R in U.Log:GetChildren() do
		local L = R:FindFirstChild("Text")
		if L and string.find(L.Text, Text, 1, true) then return L end
	end
	return nil
end

-- 1. a sent note arrives and joins the history
local Tag = "chat check " .. math.random(1000, 9999)
S.LastSent = 0
T.Send(Tag)
local Got = nil
for _ = 1, 60 do
	Got = lineWith(Tag)
	if Got then break end
	task.wait(0.1)
end
Ok(Got ~= nil, "the sent note never arrived")
Ok(S.History[#S.History] == Tag, "history: " .. tostring(S.History[#S.History]))

-- 2. quiet: the frame sinks, the lines stay
if U.Box:IsFocused() then U.Box:ReleaseFocus(false) end
S.Hover = false
S.LastActive = os.clock() - 60
task.wait(1.3)
Ok(S.Faded == true, "never went quiet")
Ok(U.Header.GroupTransparency > 0.99, "header shows when quiet: " .. U.Header.GroupTransparency)
Ok(U.Background == nil or U.Background.ImageTransparency > 0.99, "panel shows when quiet")
Ok(U.Border == nil or not U.Border:IsA("ImageLabel") or U.Border.ImageTransparency > 0.99, "iron edge shows when quiet")
Ok(U.Bar.GroupTransparency > (if S.Touch then 0.55 else 0.99), "bar when quiet: " .. U.Bar.GroupTransparency)
Ok(Got == nil or Got.TextTransparency < 0.05, "the line is hidden when quiet")
Ok(U.Vignette.ImageTransparency < 0.5, "no vignette when quiet: " .. U.Vignette.ImageTransparency)

-- 3. Focus (what / does) wakes it and focuses the bar; leaving keeps the draft
Chat.Focus()
task.wait(0.5)
Ok(U.Box:IsFocused(), "Focus didn't focus the bar")
Ok(S.Faded == false and U.Header.GroupTransparency < 0.01, "Focus didn't wake it: " .. U.Header.GroupTransparency)
Ok(U.Vignette.ImageTransparency > 0.99, "vignette shows when awake")
U.Box.Text = "a draft"
U.Box:ReleaseFocus(false)
task.wait(0.1)
Ok(U.Box.Text == "a draft", "the draft was lost: " .. U.Box.Text)
U.Box.Text = ""

-- 4. SetShown and NHCanChat
Chat.SetShown(false)
Ok(U.Window.Visible == false, "SetShown(false) left it showing")
Chat.SetShown(true)
Ok(U.Window.Visible == true, "SetShown(true) left it hidden")
local Was = P:GetAttribute("NHCanChat")
P:SetAttribute("NHCanChat", false)
task.wait(0.1)
Ok(U.Window.Visible == false, "NHCanChat=false still shows it")
P:SetAttribute("NHCanChat", Was)
task.wait(0.1)
Ok(U.Window.Visible == true, "NHCanChat put back but still hidden")
return if #Fails == 0 then "PASS chat_play" else "FAIL " .. table.concat(Fails, "; ")
```

- [ ] **Step 3: The Motion require**

In the live copy, below `local Kit = require(ReplicatedStorage.UI:WaitForChild("Components"))`, add:
```lua
local Motion = require(ReplicatedStorage.UI:WaitForChild("Motion")) -- (chat-factions-ui) smoke-in, wake, candle, glint
```
In the header comment, after the line `- It fades back to a faint log after a few quiet seconds and comes back on a new message, the mouse, or /.`, add:
```lua
	- (chat-factions-ui, 2026-11-25) Quiet means text only: the panel, iron edge, header and bar fade out (the bar stays
	  faint on touch), and a soft dark vignette sits behind the lines. New lines smoke in; the header candle flickers and
	  the iron edge glints (UI.Motion). Spec: docs/superpowers/specs/2026-11-25-chat-factions-ui-design.md.
```

- [ ] **Step 4: The candle in the header, and the vignette**

Replace the header mark (the `Kit.Image("Knob", { Name = "Mark", ... })` call in `Shared.Build`) with:
```lua
	local Candle = new("Frame", {
		Name = "Candle",
		BackgroundTransparency = 1,
		AnchorPoint = Vector2.new(0, 0.5),
		Position = UDim2.new(0, 2, 0.5, -1),
		Size = UDim2.fromOffset(16, 24),
		ZIndex = 9,
		Parent = Header,
	})
	Kit.Image("CandleBody", {
		Name = "Wax",
		AnchorPoint = Vector2.new(0.5, 1),
		Position = UDim2.new(0.5, 0, 1, 0),
		Size = UDim2.fromOffset(8, 12),
		ZIndex = 9,
		Parent = Candle,
	})
	local Flame = Kit.Image("CandleFlame", {
		Name = "Flame",
		AnchorPoint = Vector2.new(0.5, 1),
		Position = UDim2.new(0.5, 0, 1, -11),
		Size = UDim2.fromOffset(12, 14),
		ZIndex = 10,
		Parent = Candle,
	})
```
Directly after the `local Content = Api.Content` line, add the vignette:
```lua
	-- (chat-factions-ui) the soft dark patch behind the lines while quiet (hidden while awake: the panel is there)
	local Vignette = Kit.Image("Glow", {
		Name = "Vignette",
		ImageColor3 = Color3.new(0, 0, 0),
		ImageTransparency = 1,
		ScaleType = Enum.ScaleType.Stretch,
		Position = UDim2.fromOffset(-40, -10),
		Size = UDim2.new(1, 60, 1, -BAR + 20),
		ZIndex = 1,
		Parent = Window,
	})
```
In the `local U = { ... }` table, add these three entries after `Title = Title,`:
```lua
		Candle = Candle,
		Flame = Flame,
		Vignette = Vignette,
```

- [ ] **Step 5: Lines smoke in, with a darker stroke**

In `Local.AddLine`, change `TextStrokeTransparency = 0.45,` to `TextStrokeTransparency = 0.3,`. Then replace:
```lua
	Row.Parent = Log
	if not Local.Reduced() then
		Label.TextTransparency = 1
		Pip.ImageTransparency = 1
		tween(Label, 0.18, { TextTransparency = 0 })
		tween(Pip, 0.18, { ImageTransparency = 0 })
	end
```
with:
```lua
	Row.Parent = Log
	Motion.SmokeIn(Label)
	if not Local.Reduced() then
		Pip.ImageTransparency = 1
		tween(Pip, 0.35, { ImageTransparency = 0 })
	end
```

- [ ] **Step 6: Quiet means text only**

Replace the whole `function Local.SetFaded(U, Faded: boolean, Instant: boolean?) ... end` with:
```lua
-- (chat-factions-ui) what wakes and what goes quiet: { Inst, AwakeGoal, QuietGoal } for Motion.Wake
function Local.WakeItems(U)
	local Items = {}
	if U.Background then
		table.insert(Items, { U.Background, { ImageTransparency = 0.18, BackgroundTransparency = 0.18 }, { ImageTransparency = 1, BackgroundTransparency = 1 } })
	end
	if U.Border then
		for _, B in (if U.Border:IsA("ImageLabel") then { U.Border } else U.Border:GetChildren()) do
			if B:IsA("ImageLabel") then
				table.insert(Items, { B, { ImageTransparency = 0 }, { ImageTransparency = 1 } })
			end
		end
	end
	if U.Shadow then
		table.insert(Items, { U.Shadow, { ImageTransparency = 0.15 }, { ImageTransparency = 1 } })
	end
	table.insert(Items, { U.Header, { GroupTransparency = 0 }, { GroupTransparency = 1 } })
	-- touch: the bar stays faint when quiet, so there is still something to tap
	table.insert(Items, { U.Bar, { GroupTransparency = 0 }, { GroupTransparency = if State.Touch then 0.6 else 1 } })
	table.insert(Items, { U.Vignette, { ImageTransparency = 1 }, { ImageTransparency = 0.35 } })
	return Items
end

function Local.SetFaded(U, Faded: boolean, Instant: boolean?)
	if State.Faded == Faded and not Instant then return end
	State.Faded = Faded
	Motion.Wake(Local.WakeItems(U), not Faded, Instant)
	U.Log.ScrollBarImageTransparency = if Faded then 1 else 0.2
end
```

- [ ] **Step 7: The candle and the glint go live; the test hook**

In `Shared.OnStart`, directly after the `if State.Touch then U.Box.PlaceholderText = "Tap to talk..." end` line, add:
```lua
	-- (chat-factions-ui) the header candle flickers and the iron edge breathes while the window is shown
	Motion.Candle(U.Flame, U.Window)
	if U.Border and U.Border:IsA("ImageLabel") then
		Motion.Glint(U.Border, "ImageColor3", C.Iron, C.Iron:Lerp(C.Gold, 0.55), U.Window)
	end
```
Directly above `return Shared` at the end of the file, add:
```lua
-- checks only (tools/chat-factions-ui/checks/chat_play.lua)
Shared.ForTests = {
	Ui = function() return Ui end,
	State = State,
	Send = function(Text: string)
		if Ui then
			Ui.Box.Text = Text
			Local.Send()
		end
	end,
}
```

- [ ] **Step 8: Install in Edit and check the preview**

Run `get_studio_state` (it must be Edit), then:
```
python -X utf8 -I tools/admin-console/fetch.py tools/chat-factions-ui/_orig StarterPlayer.StarterPlayerScripts.Controllers.Gui.Chat
python -X utf8 -I tools/admin-console/install_inplace.py tools/chat-factions-ui/_orig tools/chat-factions-ui/live ChatFactionsUI_pre_20261125 StarterPlayer.StarterPlayerScripts.Controllers.Gui.Chat
```
Expected: the installer's line for `...Gui.Chat ModuleScript <bytes>`, with no failure word.

Then build the preview in Edit with `execute_luau` (Edit):
```lua
local G = Instance.new("ScreenGui") G.Name = "ChatPreviewCheck" G.Parent = game.StarterGui
local Ok, E = pcall(function()
	local M = require(game.StarterPlayer.StarterPlayerScripts.Controllers.Gui.Chat:Clone())
	M.Preview(G)
	local Q = Instance.new("ScreenGui") Q.Name = "ChatPreviewQuiet" Q.Parent = game.StarterGui
	M.Preview(Q, true)
end)
return tostring(Ok) .. " " .. tostring(E)
```
Expected: `true nil`. Take a `screen_capture`: the awake window is at the top left, and below it the quiet one shows only
lines, with the dark patch behind them. Then destroy both ScreenGuis (`game.StarterGui.ChatPreviewCheck:Destroy()`
and `game.StarterGui.ChatPreviewQuiet:Destroy()`).

- [ ] **Step 9: Commit**

```
git add tools/chat-factions-ui/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.Chat.luau tools/chat-factions-ui/checks/chat_play.lua
git commit -m "Chat and Factions UI, Task 2: the chat goes quiet to text only (vignette), lines smoke in, a candle in the header, the iron edge glints

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 10 (controller): Play round**

`chat_play.lua` and `motion_play.lua` through `run_live.py ... 60 Client`. Expected: `PASS chat_play`, `PASS motion_play`.

---

### Task 3: The Factions panel

**Files:**
- Create: `tools/chat-factions-ui/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.FactionsPanel.luau`, copied from `pre/` and then modified as below
- Create: `tools/chat-factions-ui/checks/factions_play.lua`

**Interfaces:**
- Consumes: `Motion.Open`, `Close`, `Rise`, `Fill`, `Pips`, `SmokeIn`, `Candle`, `Glint` (Task 1). `Kit.Bar` roots
  carry a `Value` attribute (the fraction) and a `Fill` child. `Kit.Decorate` puts the card border in
  `NHDecor.Ornament`.
- Produces:
  - `Shared.ForTests = { Ui: () -> table?, PipOff: Color3, Equip: (Title: string, Equipped: boolean) -> () }`.
  - Each faction card (the inner frame, named by its faction id) holds a `Pips` frame with `Pip1` to `PipN`,
    where N = `#FactionConfig.Ranks`.

- [ ] **Step 1: Copy the module**

```
cp tools/chat-factions-ui/pre/StarterPlayer.StarterPlayerScripts.Controllers.Gui.FactionsPanel.luau tools/chat-factions-ui/live/
```

- [ ] **Step 2: Write the failing Play check**

`tools/chat-factions-ui/checks/factions_play.lua`:
```lua
-- factions_play (chat-factions-ui, Client, Play): the rebuilt Factions panel. Toggle(true) opens it with every section,
-- the bars end at their values, the pips match each rank, Equip sends SocialAction, Toggle(false) hides it, and with
-- reduced motion everything is at its end state at once.
local P = game.Players.LocalPlayer
local F = require(P.PlayerScripts.Controllers.Gui.FactionsPanel)
local SC = require(P.PlayerScripts.Controllers.StateController)
local Cfg = require(game.ReplicatedStorage.Config.Factions)
local T = F.ForTests
if not T then return "FAIL no FactionsPanel.ForTests" end
local Fails, Notes = {}, {}
local function Ok(Cond, What) if not Cond then table.insert(Fails, What) end end

local function checkBody(Body: Instance, Label: string)
	local Profile = SC.GetProfile(false)
	local Social = Profile and Profile.Social or {}
	for _, N in { "Reputation", "Vigil", "CrimsonCourt", "Titles", "Rumours" } do
		Ok(Body:FindFirstChild(N, true) ~= nil, Label .. ": missing " .. N)
	end
	for _, D in Body:GetDescendants() do
		if D.Name == "Bar" and D:GetAttribute("Value") ~= nil and D:FindFirstChild("Fill") then
			local Want = math.clamp(D:GetAttribute("Value"), 0, 1)
			Ok(math.abs(D.Fill.Size.X.Scale - Want) < 0.002, ("%s: a bar at %.3f, want %.3f"):format(Label, D.Fill.Size.X.Scale, Want))
		end
	end
	for _, Id in { "Vigil", "CrimsonCourt" } do
		local Card = Body:FindFirstChild(Id, true)
		local Pips = Card and Card:FindFirstChild("Pips")
		local Rank = Social.Factions and Social.Factions[Id] and Social.Factions[Id].Rank or "Outsider"
		local Want = 1
		for I, R in Cfg.Ranks do if R.Name == Rank then Want = I end end
		local Lit, All = 0, 0
		if Pips then
			for _, Q in Pips:GetChildren() do
				if Q:IsA("Frame") then
					All += 1
					if Q.BackgroundColor3 == Cfg.Factions[Id].Color then Lit += 1 end
				end
			end
		end
		Ok(All == #Cfg.Ranks, ("%s: %s has %d pips, want %d"):format(Label, Id, All, #Cfg.Ranks))
		Ok(Lit == Want, ("%s: %s pips lit %d, rank %s wants %d"):format(Label, Id, Lit, Rank, Want))
	end
end

-- 1. animated open: once it has settled, everything is at its end state
F.Toggle(true)
task.wait(3)
local U = T.Ui()
if not U then return "FAIL the panel isn't built" end
Ok(U.Panel.Visible, "Toggle(true) left it hidden")
checkBody(U.Body, "animated")

-- 2. Equip sends SocialAction (the send is caught, not passed on)
local Packets = require(game.ReplicatedStorage.Remotes.Packets)
local Got = nil
local Hooked, Old = pcall(function() return Packets.SocialAction.Fire end)
if Hooked and pcall(function() Packets.SocialAction.Fire = function(_, D) Got = D end end) then
	T.Equip("Night Owl", false)
	Packets.SocialAction.Fire = Old
	Ok(Got and Got.Action == "EquipTitle" and Got.Title == "Night Owl", "Equip didn't send EquipTitle")
	T.Equip("Night Owl", true)
else
	table.insert(Notes, "Equip not checked: Packets.SocialAction can't be hooked")
end

-- 3. close
F.Toggle(false)
task.wait(0.5)
Ok(not U.Panel.Visible, "Toggle(false) left it showing")

-- 4. reduced motion: open again, everything at its end state at once
local WasReduced = P:GetAttribute("NHReducedMotion")
P:SetAttribute("NHReducedMotion", true)
F.Toggle(true)
checkBody(U.Body, "reduced")
F.Toggle(false)
P:SetAttribute("NHReducedMotion", WasReduced)
Ok(not U.Panel.Visible, "reduced Toggle(false) left it showing")
return (if #Fails == 0 then "PASS factions_play" else "FAIL " .. table.concat(Fails, "; ")) .. (if #Notes > 0 then " | " .. table.concat(Notes, "; ") else "")
```
In step 2, the second `T.Equip("Night Owl", true)` call runs after the hook is removed. It fires the real unequip,
`Title = ""`, so the player's title is cleared. Delete that line if the player's title must stay. The controller
records the title before the round and puts it back with the console if it changed.

- [ ] **Step 3: Requires, constants, the header note**

In the live copy, below the `local Kit = require(...)` line, add:
```lua
local Motion = require(ReplicatedStorage.UI:WaitForChild(`Motion`)) -- (chat-factions-ui) open/close, rise, fill, pips, candle, glint
```
Below `local ORDER = { `Vigil`, `CrimsonCourt` }`, add:
```lua
local PIP_OFF = Color3.fromRGB(42, 36, 28) -- an unlit rank pip
```
At the end of the header comment (before `]]`), add:
```lua
	(chat-factions-ui, 2026-11-25) Iron and candle: a candle by the title, faction cards washed in their colour with a
	breathing edge, rank pips, and on open the panel rises in, the sections fade up in turn, the bars fill and the pips
	light (UI.Motion). A SetSocial re-render doesn't replay it. Spec: docs/superpowers/specs/2026-11-25-chat-factions-ui-design.md.
```

- [ ] **Step 4: The candle and the close button**

In `Local.Build`, replace the `Close` button block:
```lua
	local Close = Kit.Button({
		Name = `Close`; text = `X`; textSize = 18;
```
with:
```lua
	local Close = Kit.Button({
		Name = `Close`; text = `×`; textSize = 22;
```
Directly after the `Close.ZIndex = 3` line, add:
```lua
	-- (chat-factions-ui) the candle by the title
	local Candle = Instance.new(`Frame`)
	Candle.Name = `Candle`
	Candle.BackgroundTransparency = 1
	Candle.Position = UDim2.new(0, 34, 0, 26)
	Candle.Size = UDim2.fromOffset(18, 28)
	Candle.ZIndex = 8
	Candle.Parent = Panel
	Kit.Image(`CandleBody`, { Name = `Wax`; AnchorPoint = Vector2.new(0.5, 1); Position = UDim2.new(0.5, 0, 1, 0); Size = UDim2.fromOffset(9, 14); ZIndex = 8; Parent = Candle })
	local Flame = Kit.Image(`CandleFlame`, { Name = `Flame`; AnchorPoint = Vector2.new(0.5, 1); Position = UDim2.new(0.5, 0, 1, -13); Size = UDim2.fromOffset(14, 16); ZIndex = 9; Parent = Candle })
	Motion.Candle(Flame, Panel)
```
Change the `Local.Build` return line to:
```lua
	return { Gui = Gui; Panel = Panel; Body = Scroll; Open = false }
```

- [ ] **Step 5: Cards washed in their colour**

In `Local.Card`, change the `Kit.Decorate(Outer, { ... })` call's `bgColor = CARD_BG;` to:
```lua
		ornament = `slot`; shadow = false; bgColor = if Accent then Accent:Lerp(CARD_BG, 0.85) else CARD_BG;
```
That is, replace the `ornament = ...; shadow = false; bgColor = CARD_BG;` line with this one. The `frameColor` line
stays.

- [ ] **Step 6: The faction card with pips**

Replace the whole `function Local.FactionCard(Parent: Instance, Order: number, Id: string, Social) ... end` with:
```lua
-- One faction's card. Returns what the open animation needs: { Outer, Bar, Pips, Count, Color }.
function Local.FactionCard(Parent: Instance, Order: number, Id: string, Social, Animate: boolean?)
	local Def = FactionConfig.Factions[Id]
	local F = Social.Factions and Social.Factions[Id] or {}
	local Standing = F.Standing or 0
	local Rank = F.Rank or `Outsider`
	local Member = F.Member == true
	local Card = Local.Card(Parent, Order, Def.Color)
	Card.Name = Id

	Kit.Emboss(Local.Label(Card, { Order = 1; Text = Def.Name; Font = Enum.Font.Fantasy; TextSize = 23; Color = Def.Color }), Def.Color:Lerp(Color3.new(0, 0, 0), 0.45), 1.4)
	Local.Label(Card, { Order = 2; Text = `<i>{Def.Tagline}</i>`; TextSize = 13; Color = DIM })

	-- Rank, its pips, and the bar to the next rank
	local Index = Local.RankIndex(Rank)
	local Next = FactionConfig.Ranks[Index + 1]
	local Min = FactionConfig.Ranks[Index].Min
	local Status = if Member then `Member` else `Not a member`
	Local.Label(Card, { Order = 3; Name = `Rank`; Text = `<b>{Rank}</b>  ·  {Status}  ·  {math.floor(Standing)} standing`; TextSize = 15 })
	local PipRow = Instance.new(`Frame`)
	PipRow.Name = `Pips`
	PipRow.BackgroundTransparency = 1
	PipRow.LayoutOrder = 4
	PipRow.Size = UDim2.new(1, 0, 0, 8)
	PipRow.Parent = Card
	local PipLayout = Instance.new(`UIListLayout`)
	PipLayout.FillDirection = Enum.FillDirection.Horizontal
	PipLayout.SortOrder = Enum.SortOrder.LayoutOrder
	PipLayout.Padding = UDim.new(0, 6)
	PipLayout.Parent = PipRow
	local Pips = {}
	for I = 1, #FactionConfig.Ranks do
		local Pip = Instance.new(`Frame`)
		Pip.Name = `Pip{I}`
		Pip.LayoutOrder = I
		Pip.BorderSizePixel = 0
		Pip.Size = UDim2.fromOffset(22, 8)
		Pip.BackgroundColor3 = if I <= Index and not Animate then Def.Color else PIP_OFF
		Pip.Parent = PipRow
		Pips[I] = Pip
	end
	local Bar
	if Next then
		local Fraction = (Standing - Min) / math.max(1, Next.Min - Min)
		local Caption = `{math.floor(Standing)} / {Next.Min} to {Next.Name}`
		if Next.RequiresMember and not Member then Caption = `Join to reach {Next.Name}` end
		Bar = Local.Bar(Card, 5, Fraction, Def.Color, Caption)
	else
		Bar = Local.Bar(Card, 5, 1, Def.Color, `Highest rank`)
	end

	-- Joining
	if not Member then
		local Flags = F.Flags or {}
		local Noticed = Standing >= FactionConfig.Ranks[2].Min
		local Done = Def.Initiation and Flags[Def.Initiation.Flag]
		local Tick = function(Ok) return if Ok then `<font color="#7fd28c">✓</font>` else `<font color="#8a8596">○</font>` end
		Local.Label(Card, { Order = 6; TextSize = 13; Text =
			`<b>To join</b>   {Tick(Noticed)} Reach Prospect ({FactionConfig.Ranks[2].Min} standing)   {Tick(Done)} {Def.Initiation.Text}   then talk to {RepConfig.Npcs[Def.Leader].Name}` })
	end

	-- Leader + hangout
	local Record = Social.Relationships and Social.Relationships[Def.Leader]
	local Npc = RepConfig.Npcs[Def.Leader]
	Local.Label(Card, { Order = 7; TextSize = 13; Color = DIM; Text =
		`Leader: <b>{Npc.Name}</b> ({Local.RelationState(Record)})  ·  Hangout: {Def.Hangout}` })
	Local.Label(Card, { Order = 8; TextSize = 13; Text = `<b>Activity:</b> {Def.Activity.Name}. {Def.Activity.Text}` })

	-- Mission
	if Def.Mission then
		local M = F.Missions and F.Missions[Def.Mission.Id]
		local Done = typeof(M) == `table` and M.Done
		local Progress = if Done then `<font color="#7fd28c">Complete</font>`
			elseif Member then `{Local.MissionCount(Id, M)}/3`
			else `<font color="#8a8596">members only</font>`
		Local.Label(Card, { Order = 9; TextSize = 13; Text =
			`<b>Mission: {Def.Mission.Name}</b> ({Progress}). {Def.Mission.Text} Reward: title "{Def.Mission.Reward.Title}".` })
	end

	-- Perks
	local PerkOrder = 10
	for _, RankDef in FactionConfig.Ranks do
		local Perk = Def.Perks and Def.Perks[RankDef.Name]
		if Perk then
			local Has = Member and Index >= Local.RankIndex(RankDef.Name)
			local Need = if RankDef.Name == `Inner Circle` and Def.InnerCircleRequires
				then ` (also needs {Def.InnerCircleRequires.Min} {Def.InnerCircleRequires.Reputation})` else ``
			local Star = if Has then `<font color="` .. Local.Hex(Def.Color) .. `">★</font>` else `☆`
			Local.Label(Card, { Order = PerkOrder; TextSize = 13; Color = if Has then TEXT else DIM; Text =
				`{Star} <b>{Perk.Name}</b> · {RankDef.Name}{Need}: {Perk.Text}` })
			PerkOrder += 1
		end
	end

	-- the card's edge breathes in its colour while the panel is open
	local Outer = Card.Parent :: GuiObject
	local Decor = Outer:FindFirstChild(`NHDecor`)
	local Edge = Decor and Decor:FindFirstChild(`Ornament`)
	if Edge and Edge:IsA(`ImageLabel`) then
		Motion.Glint(Edge, `ImageColor3`, Def.Color:Lerp(KitTheme.Colors.RowFrame, 0.35), Def.Color, Ui and Ui.Panel)
	end
	return { Outer = Outer; Bar = Bar; Pips = Pips; Count = Index; Color = Def.Color }
end
```

- [ ] **Step 7: Render with the open animation**

Replace the whole `function Local.Render() ... end` with:
```lua
-- Animate = true only when the panel opens (the sections fade up in turn, bars fill, pips light, rumours smoke in).
function Local.Render(Animate: boolean?)
	if not Ui or not Ui.Open then return end
	local Profile = StateController.GetProfile(false)
	local Social = Profile and Profile.Social
	for _, Child in Ui.Body:GetChildren() do
		if Child:IsA(`GuiObject`) then Child:Destroy() end
	end
	if typeof(Social) ~= `table` then
		Local.Label(Ui.Body, { Text = `Loading...`; Color = DIM })
		return
	end
	local Rise, Bars, PipSets, Smokes = {}, {}, {}, {}

	-- Reputation
	local Rep = Local.Card(Ui.Body, 1)
	Rep.Name = `Reputation`
	table.insert(Rise, Rep.Parent)
	local TitleText = if Social.Title and Social.Title ~= `` then `  ·  Title: <b>{Social.Title}</b>` else ``
	Local.Label(Rep, { Order = 0; Text = `<b>Reputation</b>{TitleText}`; TextSize = 16 })
	for I, Category in REP_ORDER do
		local Rule = RepConfig.Categories[Category]
		local Value = Social.Reputation and Social.Reputation[Category] or 0
		table.insert(Bars, Local.Bar(Rep, I * 2 - 1, Value / Rule.Max, Color3.fromRGB(120, 110, 160), `{Category}  {math.floor(Value)} / {Rule.Max}`))
		Local.Label(Rep, { Order = I * 2; Text = Rule.Text; TextSize = 12; Color = DIM })
	end

	-- Factions
	for I, Id in ORDER do
		local Info = Local.FactionCard(Ui.Body, 1 + I, Id, Social, Animate)
		table.insert(Rise, Info.Outer)
		table.insert(Bars, Info.Bar)
		table.insert(PipSets, Info)
	end

	-- Titles
	local Titles = Local.Card(Ui.Body, 10)
	Titles.Name = `Titles`
	table.insert(Rise, Titles.Parent)
	Local.Label(Titles, { Order = 0; Text = `<b>Titles</b>`; TextSize = 16 })
	local Owned = if typeof(Social.Titles) == `table` then Social.Titles else {}
	if #Owned == 0 then
		Local.Label(Titles, { Order = 1; Text = `None yet. Faction missions award titles.`; TextSize = 13; Color = DIM })
	end
	for I, Title in Owned do
		local Equipped = Social.Title == Title
		local Button = Kit.Button({
			Name = `Title{I}`; LayoutOrder = I; Size = UDim2.new(0, 260, 0, 44); textSize = 18;
			style = if Equipped then `gold` else `default`;
			text = if Equipped then `{Title}  (equipped)` else `Equip "{Title}"`;
			Parent = Titles;
		})
		Button.Activated:Connect(function()
			Local.Equip(Title, Equipped)
		end)
	end

	-- Rumours (they smoke in; the card itself doesn't rise)
	local Rumours = Local.Card(Ui.Body, 11)
	Rumours.Name = `Rumours`
	Local.Label(Rumours, { Order = 0; Text = `<b>Rumours</b>`; TextSize = 16 })
	for I, Planned in FactionConfig.Planned or {} do
		table.insert(Smokes, Local.Label(Rumours, { Order = I; TextSize = 13; Color = DIM; Text = `<b>{Planned.Name}</b>: {Planned.Text}` }))
	end

	if Animate then
		Motion.Rise(Rise, 0.15)
		for I, B in Bars do
			Motion.Fill(B, 0.5 + 0.05 * I)
		end
		for _, Set in PipSets do
			Motion.Pips(Set.Pips, Set.Count, Set.Color, PIP_OFF, 0.7)
		end
		for I, L in Smokes do
			Motion.SmokeIn(L, 0.9 + 0.2 * I)
		end
	end
end

function Local.Equip(Title: string, Equipped: boolean)
	Packets.SocialAction:Fire({ Action = `EquipTitle`; Title = if Equipped then `` else Title })
end
```

- [ ] **Step 8: Toggle opens and closes with Motion; the hook**

Replace the whole `function Shared.Toggle(Open: boolean?) ... end` with:
```lua
function Shared.Toggle(Open: boolean?)
	Ui = Ui or Local.Build()
	if Open == nil then Open = not Ui.Open end
	Ui.Open = Open
	if Open then
		Motion.Open(Ui.Panel) -- first: its fade covers the old body, then Render's rise hides and staggers the new one
		Local.Render(true)
	else
		Motion.Close(Ui.Panel)
	end
end
```
Directly above `return Shared`, add:
```lua
-- checks only (tools/chat-factions-ui/checks/factions_play.lua)
Shared.ForTests = {
	Ui = function() return Ui end,
	PipOff = PIP_OFF,
	Equip = function(Title: string, Equipped: boolean) Local.Equip(Title, Equipped) end,
}
```
`StateController.ProfileUpdated` still calls `Local.Render()` with no argument, so a re-render doesn't animate. Leave
it as it is.

- [ ] **Step 9: Install in Edit**

Run `get_studio_state` (it must be Edit), then:
```
python -X utf8 -I tools/admin-console/fetch.py tools/chat-factions-ui/_orig StarterPlayer.StarterPlayerScripts.Controllers.Gui.FactionsPanel
python -X utf8 -I tools/admin-console/install_inplace.py tools/chat-factions-ui/_orig tools/chat-factions-ui/live ChatFactionsUI_pre_20261125 StarterPlayer.StarterPlayerScripts.Controllers.Gui.FactionsPanel
```
Expected: the installer's line for `...Gui.FactionsPanel ModuleScript <bytes>`, with no failure word.

- [ ] **Step 10: Commit**

```
git add tools/chat-factions-ui/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.FactionsPanel.luau tools/chat-factions-ui/checks/factions_play.lua
git commit -m "Chat and Factions UI, Task 3: the Factions panel in iron and candle (candle, washed cards with breathing edges, rank pips; opens with rise, fill, pips and smoke-in)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 11 (controller): Play round**

Run `factions_play.lua` through `run_live.py ... 60 Client`. Before it, read the player's `Social.Title` from the Server; after it, put the title back if it changed. Expected: `PASS factions_play`.

---

### Task 4: The final round, shots and the record

**Files:**
- Create: `tools/chat-factions-ui/REPORT.md`
- Create: `docs/superpowers/mockups/2026-11-25-chat-factions-ui/` (screenshots)
- Modify: `docs/UI-Kit.md` (a `UI.Motion` section)
- Modify: `CHANGELOG.md` (an Unreleased entry)

- [ ] **Step 1 (controller): The final Play round**

The checks run in this order:
1. Cine.
2. `motion_play`, `chat_play`, `factions_play`.
3. The screenshots, with `screen_capture`, copied from the tool's saved file into the mockups folder:
   - `chat-quiet.jpg`: idle for 12 s.
   - `chat-awake.jpg`: after `Chat.Focus()` through a `run_live` Client one-liner.
   - `factions-open.jpg`: about 3 s after `FactionsPanel.Toggle(true)`.
4. `FactionsPanel.Toggle(false)`.
5. Restore, then cine again.

Edit, after Play stops: `motion_edit`. Every check must PASS.

- [ ] **Step 2: Write the report**

`tools/chat-factions-ui/REPORT.md` gets:
- the branch, the spec, and the plan;
- the install lines and the backup name;
- each check's exact output from the final round;
- the screenshots;
- the line "**Place not saved.**";
- **For the owner:** the look in motion, the candle's speed, and whether the quiet chat reads over bright scenes.

- [ ] **Step 3: The UI kit doc**

Add this section at the end of `docs/UI-Kit.md`:
```markdown
## Motion (`ReplicatedStorage.UI.Motion`, 2026-11-25)

Shared animations for the iron-and-candle screens (the chat window and the Factions panel). Every helper honours
Settings > Reduce Motion (`NHReducedMotion`): the end state at once, and no flicker or glint.

| Helper | Does |
|---|---|
| `SmokeIn(Label, Delay?)` | fades a line in from 8 px left (0.35 s) |
| `Wake(Items, On, Instant?)` | each `{ Inst, AwakeGoal, QuietGoal }` tweens up (0.25 s) or down (0.6 s) |
| `Candle(Flame, Holder?)` | a flame flickers (shared Heartbeat loop; pauses while `Holder` is hidden) |
| `Glint(Target, Prop, A, B, Holder?)` | a colour breathes between A and B (5 s) |
| `Rise(Items, Step?)` | sections fade up in turn (`Kit.FadeIn`) |
| `Fill(Bar, Delay?)` | a `Kit.Bar` fills from 0 (1.1 s) |
| `Pips(Pips, Count, On, Off, Delay?)` | rank pips light one at a time |
| `Open(Panel)` / `Close(Panel)` | a panel scales, rises and fades in (0.3 s) / out (0.2 s) |

One tween per instance at a time (a new one replaces the old). `ActiveCount()` and `Stop(Inst)` are for checks and
clean-up.
```

- [ ] **Step 4: The changelog**

Under `## [Unreleased]` in `CHANGELOG.md`, replace the line `Nothing yet.` with:
```markdown
### `chat-factions-ui`: the chat and the Factions panel in iron and candle, quiet (not merged; installed in NH Combat Test, place not saved)
Spec: `docs/superpowers/specs/2026-11-25-chat-factions-ui-design.md`. Plan: `docs/superpowers/plans/2026-11-25-chat-factions-ui.md`.
Record: `tools/chat-factions-ui/REPORT.md`. Backup: `ServerStorage.NH_Backup.ChatFactionsUI_pre_20261125`.
- **The chat goes quiet to text only:** the panel, iron edge, header and bar fade out after 10 quiet seconds (the bar
  stays faint on touch), and a soft dark patch sits behind the lines. /, the mouse or a new message brings the frame
  back. New lines smoke in, the header has a flickering candle, and the iron edge glints.
- **The Factions panel** has a candle by its title, faction cards washed in their colour with a breathing edge, and
  rank pips. On open it rises in, the sections fade up in turn, the bars fill, the pips light and the rumours smoke in.
  Profile updates redraw it without replaying the animation.
- **`UI.Motion`:** the shared animations. Everything honours Reduce Motion.
- Behaviour is unchanged: TextChatService, filtering, commands, `NHCanChat`, / and history, L for the panel, and
  equipping titles.
```

- [ ] **Step 5: Commit**

```
git add tools/chat-factions-ui/REPORT.md docs/superpowers/mockups/2026-11-25-chat-factions-ui docs/UI-Kit.md CHANGELOG.md
git commit -m "Chat and Factions UI, Task 4: final round, screenshots, report, UI kit Motion section, changelog

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
