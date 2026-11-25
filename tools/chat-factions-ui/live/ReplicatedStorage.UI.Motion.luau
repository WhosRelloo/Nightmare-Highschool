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
