--[[
	UI.Motion (chat-factions-ui, 2026-11-25): the small shared animations of the iron-and-candle screens
	(Controllers.Gui.Chat, Controllers.Gui.FactionsPanel). Spec: docs/superpowers/specs/2026-11-25-chat-factions-ui-design.md.

	- Every helper honours Settings > Reduce Motion (player attribute NHReducedMotion): the end state at once, and no
	  flicker or glint. Motion.ForceReduced (true / false) overrides the setting for checks; nil follows it. The loop
	  reads it every step (the saved setting lands after OnStart): a registered candle rests at how it was built and a
	  glint at A while it is on, and they carry on when it is turned off.
	- Delayed fade-ins (Rise, SmokeIn) inside a panel shown by Motion.Open are dropped if the panel is closed first.
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
local Candles = {} :: { [ImageLabel]: { Size: UDim2, Color: Color3, Phase: number, Holder: GuiObject? } }
local Glints = {} :: { [Instance]: { Prop: string, A: Color3, B: Color3, Phase: number, Holder: GuiObject? } }
local Opening = setmetatable({}, { __mode = "k" }) :: { [GuiObject]: number }
local Shut = setmetatable({}, { __mode = "k" }) :: { [GuiObject]: boolean } -- panels Close has run on since their last Open
local Tokens = setmetatable({}, { __mode = "k" }) :: { [Instance]: number } -- newest delayed call per Fill / SmokeIn
local Rising = setmetatable({}, { __mode = "k" }) :: { [GuiObject]: number } -- Rise items whose fade-in is pending
local Serial = 0
local Beat: RBXScriptConnection? = nil

function Motion.Reduced(): boolean
	if Motion.ForceReduced ~= nil then
		return Motion.ForceReduced
	end
	local P = Players.LocalPlayer
	return P ~= nil and P:GetAttribute("NHReducedMotion") == true
end

-- The panel (one Motion.Open / Close has run on) an instance sits in. A delayed fade-in inside it goes ahead only if
-- the panel is open when it is due: after a Close (and no Open since) it is dropped, so nothing fades back in.
local function gate(Inst: Instance): GuiObject?
	local A: Instance? = Inst
	while A do
		if Opening[A :: any] ~= nil then
			return A :: any
		end
		A = A.Parent
	end
	return nil
end

local function stillOpen(Panel: GuiObject?): boolean
	return Panel == nil or not Shut[Panel]
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
	-- How it was built is read once: a second call mid-drift must not take a half-faded state as the target.
	if Label:GetAttribute("NHSmokePos") == nil then
		Label:SetAttribute("NHSmokeT", Label.TextTransparency)
		Label:SetAttribute("NHSmokeS", Label.TextStrokeTransparency)
		Label:SetAttribute("NHSmokePos", Label.Position)
	end
	local T0, S0, P0 = Label:GetAttribute("NHSmokeT") :: number, Label:GetAttribute("NHSmokeS") :: number, Label:GetAttribute("NHSmokePos") :: UDim2
	local Mine = (Tokens[Label] or 0) + 1
	Tokens[Label] = Mine
	local Panel = gate(Label)
	settle(Label, { TextTransparency = 1, TextStrokeTransparency = 1, Position = P0 + UDim2.fromOffset(-8, 0) })
	local function go()
		if Label.Parent and Tokens[Label] == Mine and stillOpen(Panel) then
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
	local Reduced = Motion.Reduced() -- read every step: the saved setting lands after the screens register
	for Flame, E in Candles do
		if not Flame:IsDescendantOf(game) then
			Candles[Flame] = nil
		elseif Reduced then
			Flame.Size = E.Size -- still, at how it was built; the entry stays so it resumes when the setting is off
			Flame.ImageColor3 = E.Color
		elseif shown(E.Holder) then
			local W = 1 + 0.06 * math.sin(Now * 3.7 + E.Phase) + 0.03 * math.sin(Now * 11.3 + E.Phase * 2)
			local H = 1 + 0.09 * math.sin(Now * 3.7 + E.Phase + 0.6) + 0.04 * math.sin(Now * 9.1 + E.Phase)
			Flame.Size = UDim2.new(E.Size.X.Scale * W, E.Size.X.Offset * W, E.Size.Y.Scale * H, E.Size.Y.Offset * H)
			-- brightness flickers through the colour, never ImageTransparency: the panel's fades own that
			Flame.ImageColor3 = E.Color:Lerp(Color3.new(0, 0, 0), 0.18 * (0.5 + 0.5 * math.sin(Now * 5.3 + E.Phase)))
		end
	end
	for Inst, E in Glints do
		if not Inst:IsDescendantOf(game) then
			Glints[Inst] = nil
		elseif Reduced then
			local Any: any = Inst
			Any[E.Prop] = E.A
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

-- A candle flame flickers (size and brightness through its colour, about 1.7 s a cycle) around how it was built.
-- Under Reduce Motion it stays registered but still (see step).
function Motion.Candle(Flame: ImageLabel, Holder: GuiObject?)
	Candles[Flame] = { Size = Flame.Size, Color = Flame.ImageColor3, Phase = math.random() * 6.28, Holder = Holder }
	ensureBeat()
end

-- An edge breathes between A and B (about 5 s a cycle). Prop is the colour property ("ImageColor3", "Color").
function Motion.Glint(Target: Instance, Prop: string, A: Color3, B: Color3, Holder: GuiObject?)
	local Any: any = Target
	Any[Prop] = A -- rests at A on register, then breathes from a random phase (still at A under Reduce Motion)
	Glints[Target] = { Prop = Prop, A = A, B = B, Phase = math.random() * 6.28, Holder = Holder }
	ensureBeat()
end

-- Leaves the loop; a candle goes back to its built size.
function Motion.Stop(Inst: Instance)
	local E = Candles[Inst :: any]
	if E then
		local F = Inst :: ImageLabel
		F.Size = E.Size
		F.ImageColor3 = E.Color
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

-- Kit.FadeOut records a subtree's current transparency as its base once, and Kit.FadeIn returns to that base. So the
-- bases are recorded first, while the subtree is at how it was built, before any helper here changes a transparency.
local function remember(Root: GuiObject)
	local Rem = (Kit :: any)._rememberBase
	if not Rem then
		return
	end
	Rem(Root)
	for _, D in Root:GetDescendants() do
		Rem(D)
	end
end

-- Drives every remembered transparency to 1 at once. A zero-length tween replaces any tween running on the property
-- (a plain assignment would be undone by it), so this also cancels an unfinished Kit.FadeIn; the direct set shows it now.
local function hide(Root: GuiObject)
	remember(Root)
	local Zero = TweenInfo.new(0)
	local function one(D: Instance)
		if D:GetAttribute("NHBaseT") == nil then
			return
		end
		local Goal: { [string]: any } = {}
		if D:IsA("TextLabel") or D:IsA("TextButton") then
			Goal.TextTransparency, Goal.TextStrokeTransparency = 1, 1
		elseif D:IsA("ImageLabel") then
			Goal.ImageTransparency = 1
		elseif D:IsA("UIStroke") then
			Goal.Transparency = 1
		end
		if D:IsA("GuiObject") then
			Goal.BackgroundTransparency = 1
		end
		if next(Goal) then
			TweenService:Create(D, Zero, Goal):Play()
			local Any: any = D
			for K, V in Goal do
				Any[K] = V -- at once too: the tween only lands next step
			end
		end
	end
	one(Root)
	for _, D in Root:GetDescendants() do
		one(D)
	end
end

-- Sections fade up one after another (Step apart). They sit in list layouts, so they don't move. While an item waits,
-- it is in Rising: Open's fade (one Heartbeat after Open) hides it again, so the stagger isn't lost; a Close drops it.
function Motion.Rise(Items: { GuiObject }, Step: number?)
	if Motion.Reduced() then
		return
	end
	for I, Item in Items do
		hide(Item)
		Serial += 1
		local Mine = Serial
		Rising[Item] = Mine
		local Panel = gate(Item)
		task.delay(0.05 + (I - 1) * (Step or 0.15), function()
			if Rising[Item] ~= Mine then
				return -- a newer Rise owns it
			end
			Rising[Item] = nil
			if Item.Parent and stillOpen(Panel) then
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
	if Fill:GetAttribute("NHFillTarget") == nil then
		Fill:SetAttribute("NHFillTarget", Fill.Size) -- read once: a second call mid-fill must not take a part-filled size
	end
	local Target = Fill:GetAttribute("NHFillTarget") :: UDim2
	local Mine = (Tokens[Fill] or 0) + 1
	Tokens[Fill] = Mine
	settle(Fill, { Size = UDim2.new(0, 0, Target.Y.Scale, Target.Y.Offset) })
	task.delay(Delay or 0, function()
		if Fill.Parent and Tokens[Fill] == Mine then
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
			local Pip = Pips[I]
			if Pip.Parent then
				local T = Motion.Play(Pip, 0.3, { BackgroundColor3 = On })
				T.Completed:Once(function(State)
					-- a tween ends a hair off its goal; land exactly (unless it was cancelled or the pip is gone)
					if State == Enum.PlaybackState.Completed and Pip.Parent then
						Pip.BackgroundColor3 = On
					end
				end)
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
	Shut[Panel] = nil
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
	hide(Panel)
	S.Scale = 0.985
	Panel.Position = Base + UDim2.fromOffset(0, 10)
	Motion.Play(S, 0.3, { Scale = 1 })
	Motion.Play(Panel, 0.3, { Position = Base })
	-- One Heartbeat later, so the zero-length tweens of hide() have landed and FadeIn starts from invisible.
	local Mine = Opening[Panel]
	RunService.Heartbeat:Once(function()
		if Opening[Panel] == Mine and Panel.Parent then
			Kit.FadeIn(Panel, 0.3)
			-- that fade covers every descendant; Rise items still waiting go back to hidden for their own turn
			for Item in Rising do
				if Item:IsDescendantOf(Panel) then
					hide(Item)
				end
			end
		end
	end)
end

-- Hides a panel: the reverse over 0.2 s (scales to 0.985 and drops 10 px while it fades), then hides it. Opening it
-- again before that keeps it open. Pending Rise / SmokeIn fade-ins inside it are dropped (see gate).
function Motion.Close(Panel: GuiObject)
	Opening[Panel] = (Opening[Panel] or 0) + 1
	Shut[Panel] = true
	local Mine = Opening[Panel]
	if Motion.Reduced() or not Panel.Visible then
		Panel.Visible = false
		return
	end
	if Panel:GetAttribute("NHOpenPos") == nil then
		Panel:SetAttribute("NHOpenPos", Panel.Position)
	end
	local Base = Panel:GetAttribute("NHOpenPos") :: UDim2
	remember(Panel)
	Motion.Play(scaler(Panel), 0.2, { Scale = 0.985 })
	Motion.Play(Panel, 0.2, { Position = Base + UDim2.fromOffset(0, 10) })
	Kit.FadeOut(Panel, 0.2)
	task.delay(0.22, function()
		if Opening[Panel] == Mine then
			Panel.Visible = false
			settle(Panel, { Position = Base })
			settle(scaler(Panel), { Scale = 1 })
		end
	end)
end

return Motion
