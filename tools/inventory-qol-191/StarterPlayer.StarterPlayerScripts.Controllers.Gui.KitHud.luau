--[[
	KitHud (client): the in-play Nightmare Highschool HUD, built from ReplicatedStorage.UI.Components.
	  * health bar with % orb  <- Humanoid.Health / MaxHealth
	  * hotbar                 <- your Backpack tools (click, tap or 1-9 to equip / unequip)
	  * Yen plate              <- profile Yen (StateController); beside the bar's right end. A real Yen
	                              change counts up, pulses the coin and floats a +/- chip; profile loads
	                              and save-slot swaps are silent. Reduce Motion drops the rise and pulse.
	  * posture rail           <- "Posture" attribute on the character or Humanoid (0..Config.Combat.PostureMax);
	                              hangs under the health bar (the orb rests in its saddle). Visual only.
	  * DOWNED alert           <- Humanoid "Downed" + character "DownedUntil" (get-up countdown)
	Replaces Roblox's core Health bar and Backpack hotbar. The bottom HUD hides while you are in
	dialogue (InDialogue attribute) or a lesson, and number keys are ignored then too.
	Tools may set attributes Rarity ("Common" .. "Cursed") and Count to style their slot.
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local StarterGui = game:GetService(`StarterGui`)
local TweenService = game:GetService(`TweenService`)
local UserInputService = game:GetService(`UserInputService`)

---| Modules |---

local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))
local CombatConfig = require(ReplicatedStorage.Config.Combat)
local StateController = require(script.Parent.Parent.StateController)

local Player = Players.LocalPlayer
local Colors = Kit.Theme.Colors

local BASE_SLOTS, MAX_SLOTS = 6, 9
local DIGITS = {
	[Enum.KeyCode.One] = 1, [Enum.KeyCode.Two] = 2, [Enum.KeyCode.Three] = 3,
	[Enum.KeyCode.Four] = 4, [Enum.KeyCode.Five] = 5, [Enum.KeyCode.Six] = 6,
	[Enum.KeyCode.Seven] = 7, [Enum.KeyCode.Eight] = 8, [Enum.KeyCode.Nine] = 9,
}

local Local = {}
local Shared = {}

local Ui = nil
local Order = {} :: { Tool } -- hotbar order, stable like the core backpack
local CharConns = {} :: { RBXScriptConnection }
local Pending = false

---| Build |---

-- The kit's title font, whether the theme holds an Enum.Font or a Font object.
function Local.TitleFont(Label: TextLabel)
	local F = Kit.Theme.Fonts and Kit.Theme.Fonts.Title
	if typeof(F) == `EnumItem` then
		Label.Font = F
	elseif typeof(F) == `Font` then
		Label.FontFace = F
	else
		Label.Font = Enum.Font.Garamond
	end
end

-- Health bar (2026-11-03): smaller (600x50, was 820x64) and dressed in baked-PBR art from
-- art/ui/hud/make_health_pbr.py: hammered iron bands with scratched-brass beads and rivets, pointed gothic
-- end pieces with a brass spike and a crimson gem, brass collars at the orb, a blood-glass fill (greyscale,
-- so the bar's colour still tints it) and a brass-ringed glass orb. The kit's rails and caps stay (hidden).
local BAR_W, BAR_H, BAR_Y = 600, 50, 2 -- (1.74.0) higher than before so the EXP strip fits between the posture rail and the hotbar; (1.77.0) 2 px more so Thornrose's lowest thorns clear the rail
local HEALTH_ART = {
	Frame = `rbxassetid://77819721427160`;
	Fill = `rbxassetid://106379745673810`;
	OrbRing = `rbxassetid://112070089185906`;
	OrbGlass = `rbxassetid://111801438280193`;
}

-- Posture rail (1.74.0, "Twin Rail"): a slim forged rail hung under the health bar, baked-PBR art from
-- art/ui/hud/make_posture_pbr.py. The health orb rests in its brass saddle. Posture spreads out from the orb in
-- candle gold that warms to ember, cracks spread through it at 40 / 65 / 85%, the end gems pulse from 80%, and a
-- guard break shatters the fill off and engraves GUARD | BROKEN until you can move again (the Daze effect ends).
-- Reduce Motion: no shards, no pulse (a steady glow), no punch. Reduce Flashing: no flashes.
-- Visual only: the value still comes from the server's Posture attribute and nothing here writes it.
local RAIL_W, RAIL_H, RAIL_Y = BAR_W, 24, BAR_Y + BAR_H - 3 -- 49 in Bottom: the rail stays put; Thornrose's bottom thorns end just above its art
local RAIL_X0, RAIL_Y0, RAIL_TW, RAIL_TH = 37.5, 7, 525, 10 -- the art's window (where the fill shows)
local RAIL_SADDLE = 44 -- the saddle under the orb hides the middle +-44 px
local CRACK_AT = { 0.4, 0.65, 0.85 }
local WARN_AT = 0.8
local BRASS = Color3.fromRGB(226, 168, 72) -- molten candle-brass (the kit's Gold reads as bone on this bright fill)
local EMBER = Color3.fromRGB(255, 122, 46)
local HOT = Color3.fromRGB(255, 196, 130)
local CRACK_ROW = 40 -- PostureCracks2: 1024 x 40 rows, right half 1-3 then the same turned 180 for the left half
local BROKEN_TEXT = Color3.fromRGB(255, 104, 112)
local POSTURE_ART = { -- group 15981569 uploads (art/group-upload-posture)
	Frame = `rbxassetid://84993448249120`;
	Fill = `rbxassetid://112325315351154`;
	Cracks = `rbxassetid://120358598105240`; -- PostureCracks2
	Shards = `rbxassetid://122486978293271`;
	Briar = `rbxassetid://90765816898791`; -- (1.77.0) the rail in Thornrose's iron briar, rosebud ends
}
local RAIL_GEM_X = 22 -- where the end glows sit (the Twin Rail's gems; the briar's rosebuds are at 29)

function Local.Calm(): boolean
	return Player:GetAttribute(`NHReducedMotion`) == true
end

function Local.NoFlash(): boolean
	return Player:GetAttribute(`NHReducedFlash`) == true
end

function Local.BuildPosture(Bottom: Frame)
	local function new(Class: string, Props: { [string]: any }, Parent: Instance?)
		local I = Instance.new(Class)
		if I:IsA(`GuiObject`) then I.BorderSizePixel = 0 end
		for K, V in Props do (I :: any)[K] = V end
		I.Parent = Parent
		return I
	end
	local Images = Kit.Theme.Images
	local Root = new(`Frame`, {
		Name = `PostureRail`; BackgroundTransparency = 1; ZIndex = 1;
		AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, 0, 0, RAIL_Y); Size = UDim2.fromOffset(RAIL_W, RAIL_H);
	}, Bottom)
	local Track = new(`Frame`, {
		Name = `Track`; BackgroundColor3 = Color3.fromRGB(12, 8, 8); ZIndex = 1;
		Position = UDim2.fromOffset(RAIL_X0, RAIL_Y0); Size = UDim2.fromOffset(RAIL_TW, RAIL_TH);
	}, Root)
	local Half = RAIL_TW / 2
	local Sides = {}
	for _, Side in { -1, 1 } do
		local AX = if Side < 0 then 1 else 0
		local Clip = new(`Frame`, {
			Name = if Side < 0 then `Left` else `Right`; BackgroundTransparency = 1; ClipsDescendants = true; ZIndex = 2;
			AnchorPoint = Vector2.new(AX, 0); Position = UDim2.fromScale(0.5, 0); Size = UDim2.fromScale(0, 1);
		}, Track)
		local Tex = new(`ImageLabel`, {
			Name = `Fill`; Image = POSTURE_ART.Fill; ScaleType = Enum.ScaleType.Tile; TileSize = UDim2.fromOffset(80, RAIL_TH);
			ImageColor3 = BRASS; BackgroundColor3 = BRASS:Lerp(Colors.Ink, 0.5); ZIndex = 2;
			AnchorPoint = Vector2.new(AX, 0); Position = UDim2.fromScale(AX, 0); Size = UDim2.fromOffset(Half, RAIL_TH);
		}, Clip)
		local Cracks = {}
		for K = 1, 3 do
			Cracks[K] = new(`ImageLabel`, {
				Name = `Cracks{K}`; Image = POSTURE_ART.Cracks; BackgroundTransparency = 1; ImageTransparency = 1; ZIndex = 3;
				ImageRectOffset = Vector2.new(0, (K - 1 + (if Side < 0 then 3 else 0)) * CRACK_ROW); ImageRectSize = Vector2.new(1024, CRACK_ROW);
				AnchorPoint = Vector2.new(AX, 0); Position = UDim2.fromScale(AX, 0); Size = UDim2.fromOffset(Half, RAIL_TH);
			}, Clip)
		end
		-- the molten meniscus at the leading (outer) edge
		local Lip = new(`Frame`, {
			Name = `Lip`; BackgroundColor3 = Color3.fromRGB(255, 240, 206); ZIndex = 4;
			AnchorPoint = Vector2.new(1 - AX, 0); Position = UDim2.fromScale(1 - AX, 0); Size = UDim2.new(0, 2, 1, 0);
		}, Clip)
		new(`UIGradient`, { Rotation = 90; Transparency = NumberSequence.new(0.1, 0.75) }, Lip)
		local Flash = new(`Frame`, { Name = `Flash`; BackgroundColor3 = Color3.fromRGB(255, 240, 214); BackgroundTransparency = 1; ZIndex = 4; Size = UDim2.fromScale(1, 1) }, Clip)
		Sides[Side] = { Clip = Clip; Tex = Tex; Cracks = Cracks; Lip = Lip; Flash = Flash }
	end
	local Briar = not string.match(POSTURE_ART.Briar, `://0$`)
	if Briar then RAIL_GEM_X = 29 end
	new(`ImageLabel`, { Name = `FramePBR`; Image = if Briar then POSTURE_ART.Briar else POSTURE_ART.Frame; BackgroundTransparency = 1; ZIndex = 5; Size = UDim2.fromScale(1, 1) }, Root)
	local Gems = {}
	for I, X in { RAIL_GEM_X, RAIL_W - RAIL_GEM_X } do
		-- a wide ember halo, and a small hot core sitting on the smoked gem
		Gems[I * 2 - 1] = new(`ImageLabel`, {
			Name = `GemGlow`; Image = Images.Glow; ImageColor3 = Color3.fromRGB(255, 140, 52); ImageTransparency = 1; BackgroundTransparency = 1; ZIndex = 6;
			AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromOffset(X, RAIL_H / 2); Size = UDim2.fromOffset(48, 48);
		}, Root)
		Gems[I * 2] = new(`ImageLabel`, {
			Name = `GemCore`; Image = Images.Glow; ImageColor3 = Color3.fromRGB(255, 224, 160); ImageTransparency = 1; BackgroundTransparency = 1; ZIndex = 6;
			AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromOffset(X, RAIL_H / 2); Size = UDim2.fromOffset(16, 16);
		}, Root)
	end
	local Burst = new(`ImageLabel`, {
		Name = `BreakFlash`; Image = Images.Glow; ImageColor3 = Color3.fromRGB(255, 200, 140); ImageTransparency = 1; BackgroundTransparency = 1; ZIndex = 6;
		AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromOffset(RAIL_W / 2, RAIL_H / 2); Size = UDim2.fromOffset(RAIL_W + 60, 70);
	}, Root)
	local Words = new(`Frame`, { Name = `Words`; BackgroundTransparency = 1; ZIndex = 7; Size = UDim2.fromScale(1, 1) }, Root)
	local WordScale = new(`UIScale`, {}, Words)
	local function Word(Name: string, Text: string, Right: boolean)
		local L = new(`TextLabel`, {
			Name = Name; Text = Text; BackgroundTransparency = 1; TextSize = 17; TextColor3 = BROKEN_TEXT;
			TextStrokeColor3 = Color3.new(0, 0, 0); TextStrokeTransparency = 1; TextTransparency = 1; ZIndex = 7;
			TextXAlignment = if Right then Enum.TextXAlignment.Right else Enum.TextXAlignment.Left;
			AnchorPoint = Vector2.new(if Right then 1 else 0, 0.5);
			Position = UDim2.fromOffset(RAIL_W / 2 + (if Right then -48 else 48), RAIL_H / 2); Size = UDim2.fromOffset(190, 22);
		}, Words)
		Local.TitleFont(L)
		return L
	end
	local WordL, WordR = Word(`Guard`, `GUARD`, true), Word(`Broken`, `BROKEN`, false)

	local Api = { Root = Root }
	local Value, Peak = 0, 0
	local Stage = 0
	local PulseConn: RBXScriptConnection? = nil
	local BreakToken = 0
	local BrokenAt = -math.huge
	local Breaking = false

	local function ReachOf(F: number): UDim2
		if F <= 0.001 then return UDim2.fromScale(0, 1) end
		local S = RAIL_SADDLE / RAIL_TW
		return UDim2.fromScale(S + (0.5 - S) * F, 1)
	end
	local function ColorOf(F: number): Color3
		local C = BRASS:Lerp(EMBER, math.clamp((F - 0.3) / 0.55, 0, 1))
		if F >= 0.85 then C = C:Lerp(HOT, math.clamp((F - 0.85) / 0.15, 0, 1) * 0.6) end
		return C
	end
	local function SetCracks(N: number, Instant: boolean)
		if N == Stage and not Instant then return end
		Stage = N
		for _, Sd in Sides do
			for K, C in Sd.Cracks do
				local Goal = if K <= N then 0 else 1
				if Instant then C.ImageTransparency = Goal
				else TweenService:Create(C, TweenInfo.new(if Goal == 0 then 0.25 else 0.5), { ImageTransparency = Goal }):Play() end
			end
		end
	end
	local function SetWarn(On: boolean)
		if On and not PulseConn then
			local T0 = os.clock()
			PulseConn = game:GetService(`RunService`).Heartbeat:Connect(function()
				local T = if Local.Calm() then 0.25 else 0.45 - 0.4 * math.sin((os.clock() - T0) * math.pi * 2 / 0.9)
				for _, G in Gems do G.ImageTransparency = T end
			end)
		elseif not On and PulseConn then
			PulseConn:Disconnect()
			PulseConn = nil
			for _, G in Gems do TweenService:Create(G, TweenInfo.new(0.4), { ImageTransparency = 1 }):Play() end
		end
	end

	function Api:Set(F: number, Instant: boolean?)
		F = math.clamp(F, 0, 1)
		local Up = F > Value + 0.001
		Value = F
		if F > 0 then Peak = F end
		if Breaking and F <= 0 then return end -- the break owns the rail until it has played
		local Goal = ReachOf(F)
		local Info = if Up then TweenInfo.new(0.16, Enum.EasingStyle.Quart, Enum.EasingDirection.Out) else TweenInfo.new(0.24, Enum.EasingStyle.Linear)
		for _, Sd in Sides do
			if Instant then Sd.Clip.Size = Goal else TweenService:Create(Sd.Clip, Info, { Size = Goal }):Play() end
			Sd.Tex.ImageColor3 = ColorOf(F)
			Sd.Tex.BackgroundColor3 = ColorOf(F):Lerp(Colors.Ink, 0.5)
			Sd.Lip.Visible = F > 0.001 and F < 0.999
			if Up and not Instant and not Local.NoFlash() then
				Sd.Flash.BackgroundTransparency = 0.45
				TweenService:Create(Sd.Flash, TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { BackgroundTransparency = 1 }):Play()
			end
		end
		local N = 0
		for K, At in CRACK_AT do if F >= At then N = K end end
		SetCracks(N, Instant == true)
		SetWarn(F >= WARN_AT)
		Root:SetAttribute(`Value`, F)
	end

	function Api:Get()
		return Value
	end

	-- the guard break: the fill shatters off the rail and the rail reads GUARD | BROKEN until Daze ends
	function Api:Break(Daze: Instance?)
		local Now = os.clock()
		if Now - BrokenAt < 0.6 then
			if Daze then Api.Daze = Daze end
			return
		end
		BrokenAt = Now
		BreakToken += 1
		local My = BreakToken
		Breaking = true
		local From = math.max(Peak, 0.25)
		Peak = 0
		for _, Sd in Sides do Sd.Clip.Size = UDim2.fromScale(0, 1) end
		SetCracks(0, true)
		SetWarn(false)
		Root:SetAttribute(`Broken`, true)
		if not Local.NoFlash() then
			Burst.ImageTransparency = 0.15
			TweenService:Create(Burst, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { ImageTransparency = 1 }):Play()
		end
		if not Local.Calm() then
			local Rng = Random.new()
			local Reach = RAIL_SADDLE + (Half - RAIL_SADDLE) * From
			for I = 1, 14 do
				local Side = if I % 2 == 0 then 1 else -1
				local X = RAIL_W / 2 + Side * Rng:NextNumber(RAIL_SADDLE, Reach)
				local S = Rng:NextNumber(10, 18)
				local Shard = new(`ImageLabel`, {
					Name = `Shard`; Image = POSTURE_ART.Shards; ImageRectOffset = Vector2.new((I % 4) * 128, 0); ImageRectSize = Vector2.new(128, 128);
					ImageColor3 = Color3.fromRGB(255, 226, 170); BackgroundTransparency = 1; ZIndex = 6; Rotation = Rng:NextNumber(0, 360);
					AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromOffset(X, RAIL_H / 2 + Rng:NextNumber(-3, 3)); Size = UDim2.fromOffset(S, S);
				}, Root)
				local T = Rng:NextNumber(0.55, 0.9)
				TweenService:Create(Shard, TweenInfo.new(T, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
					Position = UDim2.fromOffset(X + Side * Rng:NextNumber(8, 46), RAIL_H / 2 + Rng:NextNumber(-34, 30));
					Rotation = Shard.Rotation + Rng:NextNumber(-200, 200); ImageTransparency = 1;
				}):Play()
				task.delay(T + 0.05, function() Shard:Destroy() end)
			end
		end
		Track.BackgroundColor3 = Color3.fromRGB(70, 12, 20)
		TweenService:Create(Track, TweenInfo.new(1.2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { BackgroundColor3 = Color3.fromRGB(34, 8, 12) }):Play()
		for _, L in { WordL, WordR } do
			L.TextTransparency, L.TextStrokeTransparency = 0, 0.15
		end
		if not Local.Calm() then
			WordScale.Scale = 1.3
			TweenService:Create(WordScale, TweenInfo.new(0.28, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 }):Play()
		else
			WordScale.Scale = 1
		end
		Api.Daze = Daze
		-- hold while the Daze lasts (it is removed when you can move again), 1.5 s if there is none, 4 s at most
		task.spawn(function()
			local Start = os.clock()
			while BreakToken == My and os.clock() - Start < 4 do
				local D = Api.Daze
				if D then
					if not D.Parent then break end
				elseif os.clock() - Start >= 1.5 then
					break
				end
				task.wait(0.05)
			end
			if BreakToken ~= My then return end
			Breaking = false
			Api.Daze = nil
			Root:SetAttribute(`Broken`, nil)
			local Out = TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
			for _, L in { WordL, WordR } do TweenService:Create(L, Out, { TextTransparency = 1; TextStrokeTransparency = 1 }):Play() end
			TweenService:Create(Track, TweenInfo.new(0.6), { BackgroundColor3 = Color3.fromRGB(12, 8, 8) }):Play()
			Api:Set(Value, false) -- whatever the server says now
		end)
	end

	Api:Set(0, true)
	return Root, Api
end

-- Health bar "Thornrose" (1.77.0, the owner's pick of three all-new designs): a briar of black iron. Two twisted
-- vines with brass-tipped thorns run along the bar, closed rosebuds cap the ends, crimson velvet is the fill and an
-- iron rose holds the % in a glass heart. Art: art/ui/hud/make_health_thornrose.py (group 15981569).
-- Animated: the fill eases (the kit's ghost lags behind it), a hit flashes a nick at the cut, flares the thorns and
-- shudders the rose; healing runs a gold sheen; the velvet catches a drifting sheen now and then; under 25% the glass
-- heart beats (faster under 10%); a transformation crossfades the colours (the form's own fill and glass) and turns
-- the rose a petal; downed goes to ash. Reduce Motion: no shudder, turn, sheen or beat scale (colours still change).
-- Reduce Flashing: no nick or flare, a softer beat. Visual only: it draws Humanoid.Health and the Transformation /
-- Downed attributes and writes nothing.
local THORN_ART = { -- group 15981569 uploads (art/group-upload-thornrose)
	Frame = `rbxassetid://70708896284357`;
	Velvet = `rbxassetid://137656357969028`;
	Rose = `rbxassetid://123909178669597`;
	Glass = `rbxassetid://88578355333318`;
}
local THORN_FORMS = { -- [form] = { fill, glass }; forms come from the character's Transformation attribute
	Human = { Color3.fromRGB(150, 22, 34), Color3.fromRGB(200, 40, 60) };
	Vampire = { Color3.fromRGB(84, 6, 30), Color3.fromRGB(255, 36, 72) }; -- near-black wine, a hot crimson heart (reads apart from Human)
	Wolf = { Color3.fromRGB(150, 72, 20), Color3.fromRGB(236, 158, 40) };
	Ghoul = { Color3.fromRGB(92, 104, 74), Color3.fromRGB(176, 206, 156) };
	Wraith = { Color3.fromRGB(70, 112, 152), Color3.fromRGB(158, 220, 255) };
	Downed = { Color3.fromRGB(70, 60, 62), Color3.fromRGB(96, 64, 66) };
}
local LOW_AT = 0.25
local Thorn = nil -- the skin's parts and animation state (nil until the art is in)

function Local.SkinThorn(Root: Frame)
	if string.match(THORN_ART.Frame, `://0$`) then Local.SkinHealth(Root) return end -- art not uploaded: the 1.13.0 skin
	local function new(Class: string, Props: { [string]: any }, Parent: Instance?)
		local I = Instance.new(Class)
		if I:IsA(`GuiObject`) then I.BorderSizePixel = 0 end
		for K, V in Props do (I :: any)[K] = V end
		I.Parent = Parent
		return I
	end
	for _, Name in { `RailTop`, `RailBottom`, `CapLeft`, `CapRight` } do
		local P = Root:FindFirstChild(Name)
		if P then P.Visible = false end
	end
	local Track = Root:FindFirstChild(`Track`) :: Frame
	local Fill = Track:FindFirstChild(`Fill`) :: Frame
	local Tex = Fill:FindFirstChild(`Texture`) :: ImageLabel
	local Orb = Root:FindFirstChild(`Orb`) :: Frame
	local Ring, Glass = Orb:FindFirstChild(`Ring`) :: ImageLabel, Orb:FindFirstChild(`Glass`) :: ImageLabel
	-- the art's window: x 37.5..562.5, y 15..35 of the 600 x 50 bar (the kit lays the track out again on a resize)
	local function Place()
		Track.Position = UDim2.fromOffset(37.5, 15)
		Track.Size = UDim2.fromOffset(525, 20)
		Tex.TileSize = UDim2.fromOffset(107, 20)
	end
	Place()
	Root:GetPropertyChangedSignal(`Size`):Connect(Place)
	Tex.Image = THORN_ART.Velvet
	-- the briar is 600 x 75: thorns rise 15 px above the bar's box and the bottom vine dips under it
	new(`ImageLabel`, { Name = `FramePBR`; Image = THORN_ART.Frame; BackgroundTransparency = 1; ZIndex = 6; Position = UDim2.new(0, 0, 0, -15); Size = UDim2.new(1, 0, 1.5, 0) }, Root)
	local Flare = new(`ImageLabel`, {
		Name = `ThornFlare`; Image = THORN_ART.Frame; ImageColor3 = Color3.fromRGB(255, 70, 60); ImageTransparency = 1; BackgroundTransparency = 1;
		ZIndex = 7; Position = UDim2.new(0, 0, 0, -15); Size = UDim2.new(1, 0, 1.5, 0);
	}, Root)
	Ring.Image = THORN_ART.Rose
	Ring.ImageColor3 = Color3.new(1, 1, 1)
	Glass.Image = THORN_ART.Glass
	Glass.Size = UDim2.fromScale(0.6, 0.6)
	local GlassGlow = new(`ImageLabel`, {
		Name = `HeartGlow`; Image = Kit.Theme.Images.Glow; ImageTransparency = 1; BackgroundTransparency = 1; ZIndex = 8;
		AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromScale(0.95, 0.95);
	}, Orb)
	local OrbScale = new(`UIScale`, {}, Orb)
	local Sheen = new(`Frame`, {
		Name = `Sheen`; BackgroundColor3 = Color3.new(1, 1, 1); ZIndex = 4; AnchorPoint = Vector2.new(0.5, 0);
		Position = UDim2.fromScale(-0.3, 0); Size = UDim2.new(0, 70, 1, 0); Visible = false;
	}, Fill)
	new(`UIGradient`, { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.5, 0.72), NumberSequenceKeypoint.new(1, 1) }) }, Sheen)
	local Nick = new(`ImageLabel`, {
		Name = `HitNick`; Image = Kit.Theme.Images.Glow; ImageColor3 = Color3.fromRGB(255, 226, 210); ImageTransparency = 1; BackgroundTransparency = 1;
		ZIndex = 5; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromOffset(300, 25); Size = UDim2.fromOffset(36, 46);
	}, Root)
	Thorn = {
		Root = Root; Track = Track; Fill = Fill; Ring = Ring; Glass = Glass; GlassGlow = GlassGlow; OrbScale = OrbScale;
		Flare = Flare; Sheen = Sheen; Nick = Nick; Value = nil; Form = nil; RingAngle = 0; SheenBusy = false;
		FillColor = THORN_FORMS.Human[1]; GlassColor = THORN_FORMS.Human[2];
	}
	Glass.ImageColor3 = Thorn.GlassColor
	GlassGlow.ImageColor3 = Thorn.GlassColor:Lerp(Color3.new(1, 1, 1), 0.35)

	-- the glass heart: a slow breath, or a lub-dub beat under 25% health
	game:GetService(`RunService`).Heartbeat:Connect(function()
		if not (Thorn and Root.Parent) then return end
		local V, Now = Thorn.Value or 1, os.clock()
		local Scale, Glow = 1, 1
		if Thorn.Form ~= `Downed` and V > 0 and V < LOW_AT then
			local Period = if V < 0.1 then 0.7 else 1.0
			local T = (Now % Period) / Period
			local Beat = math.exp(-((T - 0.08) / 0.05) ^ 2) + 0.6 * math.exp(-((T - 0.3) / 0.06) ^ 2)
			Glow = 1 - (if Local.NoFlash() then 0.3 else 0.75) * Beat
			if not Local.Calm() then Scale = 1 + 0.07 * Beat end
		elseif Thorn.Form ~= `Downed` then
			Glow = 0.88 - (if Local.Calm() then 0 else 0.1 * (0.5 + 0.5 * math.sin(Now * math.pi * 2 / 4)))
		end
		GlassGlow.ImageTransparency = Glow
		if OrbScale.Scale ~= Scale then OrbScale.Scale = Scale end
	end)
	-- the velvet catches a drifting sheen every 6-9 s
	task.spawn(function()
		local Rng = Random.new()
		while Root.Parent do
			task.wait(Rng:NextNumber(6, 9))
			if Thorn and not Local.Calm() and (Thorn.Value or 0) > 0.05 and Thorn.Form ~= `Downed` then
				Local.ThornSheen(Color3.new(1, 1, 1), 1.6, 0.72)
			end
		end
	end)
end

function Local.ThornSheen(Color: Color3, Time: number, Peak: number)
	if not Thorn or Thorn.SheenBusy then return end
	Thorn.SheenBusy = true
	local S = Thorn.Sheen
	S.BackgroundColor3 = Color
	local G = S:FindFirstChildOfClass(`UIGradient`)
	if G then G.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.5, Peak), NumberSequenceKeypoint.new(1, 1) }) end
	S.Position = UDim2.fromScale(-0.2, 0)
	S.Visible = true
	local Tw = TweenService:Create(S, TweenInfo.new(Time, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut), { Position = UDim2.fromScale(1.2, 0) })
	Tw.Completed:Once(function()
		S.Visible = false
		if Thorn then Thorn.SheenBusy = false end
	end)
	Tw:Play()
end

-- Health from the Humanoid: the kit bar snaps its fill and lags its ghost; Thornrose eases the fill and reacts
function Local.OnHealth(Frac: number, Instant: boolean?)
	local Prev = Thorn and Thorn.Value
	Ui.Health:Set(Frac, Instant)
	if not Thorn then return end
	Thorn.Value = Frac
	if Instant or Prev == nil then return end
	local Delta = Frac - Prev
	if math.abs(Delta) < 0.004 then return end
	local Fill = Thorn.Fill
	Fill.Size = UDim2.fromScale(Prev, 1)
	local Info = if Delta < 0 then TweenInfo.new(0.18, Enum.EasingStyle.Quad, Enum.EasingDirection.Out) else TweenInfo.new(0.45, Enum.EasingStyle.Sine, Enum.EasingDirection.Out)
	TweenService:Create(Fill, Info, { Size = UDim2.fromScale(Frac, 1) }):Play()
	if Thorn.Form == `Downed` then return end
	if Delta < 0 then
		if not Local.NoFlash() then
			local N = Thorn.Nick
			N.Position = UDim2.fromOffset(37.5 + 525 * Frac, 25)
			N.ImageTransparency = 0.05
			TweenService:Create(N, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { ImageTransparency = 1 }):Play()
			Thorn.Flare.ImageTransparency = if Delta < -0.08 then 0.5 else 0.72
			TweenService:Create(Thorn.Flare, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { ImageTransparency = 1 }):Play()
		end
		if not Local.Calm() then
			local Kick = math.clamp(-Delta * 60, 3, 9) * (if math.random() < 0.5 then -1 else 1)
			Thorn.Ring.Rotation = Thorn.RingAngle + Kick
			TweenService:Create(Thorn.Ring, TweenInfo.new(0.4, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Rotation = Thorn.RingAngle }):Play()
		end
	else
		if not Local.Calm() then Local.ThornSheen(Color3.fromRGB(255, 214, 140), 0.7, 0.55) end
	end
end

-- The form's colours: Downed (ash) over the Transformation attribute, else Human
function Local.ApplyForm(Character: Model, Humanoid: Humanoid, Instant: boolean?)
	if not Thorn then return end
	local Form = `Human`
	if Humanoid:GetAttribute(`Downed`) and Humanoid.Health > 0 then
		Form = `Downed`
	else
		local T = Character:GetAttribute(`Transformation`)
		if typeof(T) == `string` and THORN_FORMS[T] then Form = T end
	end
	if Form == Thorn.Form then return end
	local Was = Thorn.Form
	Thorn.Form = Form
	local FromF, FromG = Thorn.FillColor, Thorn.GlassColor
	local ToF, ToG = THORN_FORMS[Form][1], THORN_FORMS[Form][2]
	Thorn.FillColor, Thorn.GlassColor = ToF, ToG
	local function Paint(A: number)
		local F, G = FromF:Lerp(ToF, A), FromG:Lerp(ToG, A)
		Ui.Health:SetColor(F)
		Thorn.Glass.ImageColor3 = G
		Thorn.GlassGlow.ImageColor3 = G:Lerp(Color3.new(1, 1, 1), 0.35)
	end
	if Instant or Was == nil then Paint(1) return end
	local Mix = Instance.new(`NumberValue`)
	Mix.Changed:Connect(Paint)
	local Tw = TweenService:Create(Mix, TweenInfo.new(0.5, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut), { Value = 1 })
	Tw.Completed:Once(function() Paint(1) Mix:Destroy() end)
	Tw:Play()
	-- a transformation turns the rose by a petal (it blooms into the new form)
	if Form ~= `Downed` and Was ~= `Downed` and not Local.Calm() then
		Thorn.RingAngle += 360 / 7
		TweenService:Create(Thorn.Ring, TweenInfo.new(0.7, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Rotation = Thorn.RingAngle }):Play()
	end
end

function Local.SkinHealth(Root: Frame)
	for _, Name in { `RailTop`, `RailBottom`, `CapLeft`, `CapRight` } do
		local P = Root:FindFirstChild(Name)
		if P then P.Visible = false end
	end
	local Frame = Instance.new(`ImageLabel`)
	Frame.Name = `FramePBR`
	Frame.BackgroundTransparency = 1
	Frame.Image = HEALTH_ART.Frame
	Frame.ScaleType = Enum.ScaleType.Stretch
	Frame.Size = UDim2.fromScale(1, 1)
	Frame.ZIndex = 6
	Frame.Parent = Root
	local Tex = Root:FindFirstChild(`Texture`, true)
	if Tex and Tex:IsA(`ImageLabel`) then Tex.Image = HEALTH_ART.Fill end
	local Orb = Root:FindFirstChild(`Orb`)
	if Orb then
		local Ring, Glass = Orb:FindFirstChild(`Ring`), Orb:FindFirstChild(`Glass`)
		if Ring then Ring.Image = HEALTH_ART.OrbRing Ring.ImageColor3 = Color3.new(1, 1, 1) end
		if Glass then Glass.Image = HEALTH_ART.OrbGlass Glass.ImageColor3 = Color3.fromRGB(150, 34, 52) end
	end
end

-- The Yen purse: a framed plate just past the health bar's right end, centred on the bar
-- (the mirror of the posture meter on the left), with a gold coin made from the HUD orb art.
function Local.BuildYen(Bottom: Frame)
	local Root = Kit.Plate({
		Name = `Yen`; frameColor = Colors.Gold:Lerp(Colors.Iron or Color3.fromRGB(70, 66, 62), 0.45);
		AnchorPoint = Vector2.new(0, 0.5); Position = UDim2.new(0.5, BAR_W / 2 + 42, 0, BAR_Y + BAR_H / 2); Size = UDim2.fromOffset(0, 46);
		Parent = Bottom;
	})
	Root.AutomaticSize = Enum.AutomaticSize.X
	-- the row lives in its own frame, so the plate's frame / backdrop images stay out of the layout
	local Content = Instance.new(`Frame`)
	Content.Name = `Content`
	Content.BackgroundTransparency = 1
	Content.AutomaticSize = Enum.AutomaticSize.X
	Content.Size = UDim2.new(0, 0, 1, 0)
	Content.ZIndex = 11
	Content.Parent = Root
	local Pad = Instance.new(`UIPadding`)
	Pad.PaddingLeft, Pad.PaddingRight = UDim.new(0, 8), UDim.new(0, 18)
	Pad.Parent = Content
	local Row = Instance.new(`UIListLayout`)
	Row.FillDirection = Enum.FillDirection.Horizontal
	Row.VerticalAlignment = Enum.VerticalAlignment.Center
	Row.SortOrder = Enum.SortOrder.LayoutOrder
	Row.Padding = UDim.new(0, 10)
	Row.Parent = Content

	-- coin: the orb's fill + ring in gold, a yen mark stamped in the middle
	local Coin = Instance.new(`Frame`)
	Coin.Name = `Coin`
	Coin.BackgroundTransparency = 1
	Coin.Size = UDim2.fromOffset(34, 34)
	Coin.LayoutOrder = 1
	Coin.ZIndex = 11
	Coin.Parent = Content
	local CoinScale = Instance.new(`UIScale`)
	CoinScale.Parent = Coin
	local Images = Kit.Theme.Images
	local function Img(Name: string, Id: any, Color: Color3, Inset: number)
		local I = Instance.new(`ImageLabel`)
		I.Name = Name
		I.BackgroundTransparency = 1
		I.Image = if typeof(Id) == `number` then `rbxassetid://{Id}` else tostring(Id or ``)
		I.ImageColor3 = Color
		I.AnchorPoint = Vector2.new(0.5, 0.5)
		I.Position = UDim2.fromScale(0.5, 0.5)
		I.Size = UDim2.new(1, -Inset, 1, -Inset)
		I.ZIndex = 11
		I.Parent = Coin
		return I
	end
	Img(`Fill`, Images.OrbFill, Colors.Gold:Lerp(Color3.new(0, 0, 0), 0.35), 6)
	Img(`Ring`, Images.OrbRing, Colors.Gold, 0)
	local Mark = Instance.new(`TextLabel`)
	Mark.Name = `Mark`
	Mark.BackgroundTransparency = 1
	Mark.Size = UDim2.fromScale(1, 1)
	Mark.Text = `\u{00A5}`
	Local.TitleFont(Mark)
	Mark.TextSize = 20
	Mark.TextColor3 = Color3.fromRGB(255, 236, 190)
	Mark.TextStrokeTransparency = 0.55
	Mark.ZIndex = 12
	Mark.Parent = Coin

	local Amount = Instance.new(`TextLabel`)
	Amount.Name = `Label`
	Amount.BackgroundTransparency = 1
	Amount.AutomaticSize = Enum.AutomaticSize.X
	Amount.Size = UDim2.fromOffset(0, 34)
	Amount.Text = `0`
	Local.TitleFont(Amount)
	Amount.TextSize = 24
	Amount.TextColor3 = Colors.Gold
	Amount.TextXAlignment = Enum.TextXAlignment.Left
	Amount.TextStrokeTransparency = 0.6
	Amount.LayoutOrder = 2
	Amount.ZIndex = 11
	Amount.Parent = Content

	return { Root = Root; Label = Amount; Coin = Coin; CoinScale = CoinScale }
end

-- Touch-only screens (phones, tablets; Studio: ReplicatedStorage attribute NHTouchTest). The touch buttons
-- (Controllers.Gui.TouchControls) take the bottom-right corner and say how wide it is in the Player attribute
-- NHTouchReserveRight (px), so the bar scales to fit the space left of them and slides left to sit in it.
local TOUCH_L, TOUCH_R = 316, 500 -- how far the HUD reaches left and right of its centre, design px (the bars' left tip .. Yen)
local PHONE_R = 330 -- on phones the Yen plate sits above the bar, so the HUD ends at the bar's right cap
function Local.TouchOnly(): boolean
	if UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled then return true end
	return game:GetService(`RunService`):IsStudio() and ReplicatedStorage:GetAttribute(`NHTouchTest`) == true
end

function Local.TouchFit()
	if not (Ui and Ui.ScaleOpts) then return end
	local Cam = workspace.CurrentCamera
	if not Cam then return end
	local Vp = if Kit.Viewport then Kit.Viewport() else Cam.ViewportSize
	local Reserve = Player:GetAttribute(`NHTouchReserveRight`) or 0
	local Avail = math.max(240, Vp.X - Reserve - 16)
	local Phone = Kit.Phone ~= nil and Kit.Phone()
	Ui.ScaleOpts.fitWidth = TOUCH_L + (if Phone then PHONE_R else TOUCH_R)
	if Ui.Yen and Ui.Yen.Root then
		local Y = Ui.Yen.Root
		if Phone then
			Y.AnchorPoint = Vector2.new(1, 1)
			Y.Position = UDim2.new(0.5, BAR_W / 2, 0, BAR_Y - 16) -- (1.77.0) clear of the Thornrose thorns, which rise 15 px above the bar
		else
			Y.AnchorPoint = Vector2.new(0, 0.5)
			Y.Position = UDim2.new(0.5, BAR_W / 2 + 42, 0, BAR_Y + BAR_H / 2)
		end
	end
	Ui.ScaleOpts.fitMargin = Vp.X - Avail
	Kit.SetUserScale(Kit.UserScale) -- re-runs every AutoScale, this one with the new margin
	local Scale = Ui.Gui:FindFirstChild(`NHAutoScale`)
	local S = if Scale then Scale.Scale else 1
	local Cx = if Reserve > 0 then 8 + TOUCH_L * S else Vp.X / 2
	-- sitting left, the hotbar would cover the Study Group dock in the bottom-left corner: stand on it instead
	local Lift = 0
	local PG = Player:FindFirstChild(`PlayerGui`)
	local SG = PG and PG:FindFirstChild(`NHStudyGroup`)
	local Dock = SG and SG:FindFirstChild(`Dock`)
	if Reserve > 0 and Dock and Dock:IsA(`GuiObject`) and Dock.Visible and SG.Enabled then
		-- from the dock's own layout (bottom-anchored), so it doesn't depend on where the screen really is
		local DS = SG:FindFirstChild(`NHAutoScale`)
		local Dsc = if DS then DS.Scale else 1
		local Top = -Dock.Position.Y.Offset * Dsc + Dock.AnchorPoint.Y * Dock.AbsoluteSize.Y + (1 - Dock.Position.Y.Scale) * Vp.Y
		Lift = math.max(0, Top + 4)
	end
	Ui.Bottom.Position = UDim2.new(Cx / Vp.X, 0, 1, -8 - Lift / S) -- the posture rail lives in Bottom and moves with it
end

function Local.Build()
	local Gui = Instance.new(`ScreenGui`)
	Gui.Name = `KitHud`
	Gui.ResetOnSpawn = false
	Gui.IgnoreGuiInset = true
	Gui.DisplayOrder = 3
	Gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	local ScaleOpts = if Local.TouchOnly() then { fitWidth = TOUCH_L + TOUCH_R; fitMargin = 24 } else nil
	Kit.AutoScale(Gui, ScaleOpts)

	local Bottom = Instance.new(`Frame`)
	Bottom.Name = `Bottom`
	Bottom.BackgroundTransparency = 1
	Bottom.AnchorPoint = Vector2.new(0.5, 1)
	Bottom.Position = UDim2.new(0.5, 0, 1, -8)
	Bottom.Size = UDim2.fromOffset(900, 176)
	Bottom.Parent = Gui

	local HealthRoot, Health = Kit.HealthBar({
		Name = `Health`; value = 1;
		AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, 0, 0, BAR_Y); Size = UDim2.fromOffset(BAR_W, BAR_H);
		Parent = Bottom;
	})
	Local.SkinThorn(HealthRoot)
	HealthRoot.ZIndex = 2 -- the orb draws over the posture rail's saddle

	local Yen = Local.BuildYen(Bottom)

	local PostureRoot, Posture = Local.BuildPosture(Bottom)

	local DownedRoot, Downed = Kit.DangerAlert({
		Name = `Downed`; title = `DOWNED`; subtitle = `You can still crawl`;
		AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, 0, 0, 70); Visible = false;
		Parent = Gui;
	})

	Gui.Parent = Player:WaitForChild(`PlayerGui`)
	return {
		Gui = Gui; ScaleOpts = ScaleOpts; Bottom = Bottom; Health = Health; Yen = Yen; Posture = Posture; PostureRoot = PostureRoot;
		Downed = Downed; DownedRoot = DownedRoot; Hotbar = nil; HotbarRoot = nil; Slots = 0;
	}
end

function Local.BuildHotbar(Count: number)
	if Ui.HotbarRoot then Ui.HotbarRoot:Destroy() end
	local Root, Api = Kit.Hotbar({
		Name = `Hotbar`; slots = Count; slotSize = 70; gap = 10;
		AnchorPoint = Vector2.new(0.5, 1); Position = UDim2.new(0.5, 0, 1, 0);
		onSelect = function(Index) Local.OnSlot(Index) end;
		Parent = Ui.Bottom;
	})
	Ui.HotbarRoot, Ui.Hotbar, Ui.Slots = Root, Api, Count
end

---| Hotbar |---

function Local.ToolItem(Tool: Tool)
	return {
		name = Tool.Name;
		icon = if Tool.TextureId ~= `` then Tool.TextureId else nil;
		rarity = Tool:GetAttribute(`Rarity`) or `Common`;
		count = Tool:GetAttribute(`Count`);
		id = Tool:GetFullName();
	}
end

local CountWatch = setmetatable({}, { __mode = `k` }) -- (audit) eating a snack only changes the tool's Count
function Local.CollectTools()
	local Present = {}
	local Fresh = {}
	local function Add(Item)
		if Item:IsA(`Tool`) and not Present[Item] then
			Present[Item] = true
			-- (inventory QOL 1.91) an empty pin or a new cooldown also restyles the slot
			if not CountWatch[Item] then CountWatch[Item] = Item.AttributeChanged:Connect(function(A)
				if A == `Count` or A == `NHEmpty` or A == `NHReadyAt` then Local.Schedule() end
			end) end
			table.insert(Fresh, Item)
		end
	end
	local Backpack = Player:FindFirstChildOfClass(`Backpack`)
	if Backpack then for _, Item in Backpack:GetChildren() do Add(Item) end end
	if Player.Character then for _, Item in Player.Character:GetChildren() do Add(Item) end end

	local NewOrder = {}
	local Kept = {}
	for _, Tool in Order do
		if Present[Tool] then
			table.insert(NewOrder, Tool)
			Kept[Tool] = true
		end
	end
	for _, Tool in Fresh do
		if not Kept[Tool] then table.insert(NewOrder, Tool) end
	end
	Order = NewOrder
end

function Local.Render()
	Pending = false
	if not Ui then return end
	Local.CollectTools()
	local Need = math.clamp(#Order, BASE_SLOTS, MAX_SLOTS)
	if Ui.Slots ~= Need then Local.BuildHotbar(Need) end
	local Equipped = nil
	for Index = 1, Ui.Slots do
		local Tool = Order[Index]
		Ui.Hotbar:SetItem(Index, if Tool then Local.ToolItem(Tool) else nil)
		Local.SlotState(Index, Tool)
		if Tool and Player.Character and Tool.Parent == Player.Character then Equipped = Index end
	end
	Ui.Hotbar:Select(Equipped, true)
end

-- (inventory QOL 1.91) a snack slot greys out when the pin is empty ("Restock") and drains a dark shade with the seconds
-- left while it's cooling down (the shared "full" wait for food, the one-sip wait for drinks)
local Shades = {} :: { [number]: Tool }
function Local.SlotState(Index: number, Tool: Tool?)
	local Slot = Ui.HotbarRoot and Ui.HotbarRoot:FindFirstChild(`Slot{Index}`, true)
	if not Slot then return end
	local Shade = Slot:FindFirstChild(`NHShade`)
	if not (Tool and Tool:GetAttribute(`NHItem`)) then
		if Shade then Shade.Visible = false end
		Shades[Index] = nil
		return
	end
	if not Shade then
		Shade = Instance.new(`Frame`)
		Shade.Name = `NHShade`
		Shade.BackgroundColor3 = Color3.new(0, 0, 0)
		Shade.BorderSizePixel = 0
		Shade.AnchorPoint = Vector2.new(0.5, 1)
		Shade.Position = UDim2.new(0.5, 0, 1, -4)
		Shade.ZIndex = 6
		Shade.Visible = false
		Shade.Parent = Slot
		local L = Instance.new(`TextLabel`)
		L.Name = `Text`
		L.BackgroundTransparency = 1
		L.AnchorPoint = Vector2.new(0.5, 1)
		L.Position = UDim2.fromScale(0.5, 1)
		L.Size = UDim2.new(1, 0, 0, 24)
		L.Font = Enum.Font.GothamBold
		L.TextSize = 15
		L.TextColor3 = Colors.Text or Color3.fromRGB(232, 222, 196)
		L.TextStrokeTransparency = 0.4
		L.ZIndex = 7
		L.Parent = Shade
	end
	Shades[Index] = Tool
	Local.StepShade(Index)
end

function Local.StepShade(Index: number)
	local Tool = Shades[Index]
	local Slot = Tool and Ui and Ui.HotbarRoot and Ui.HotbarRoot:FindFirstChild(`Slot{Index}`, true)
	local Shade = Slot and Slot:FindFirstChild(`NHShade`)
	if not Shade then return end
	local Label = Shade:FindFirstChild(`Text`) :: TextLabel
	if Tool:GetAttribute(`NHEmpty`) then
		Shade.Visible = true
		Shade.BackgroundTransparency = 0.45
		Shade.Size = UDim2.new(1, -8, 1, -8)
		Label.Text = `Restock`
		return
	end
	local Left = (Tool:GetAttribute(`NHReadyAt`) or 0) - workspace:GetServerTimeNow()
	if Left <= 0 then Shade.Visible = false return end
	local Full = math.max(Tool:GetAttribute(`NHCooldown`) or Left, 0.1)
	Shade.Visible = true
	Shade.BackgroundTransparency = 0.35
	Shade.Size = UDim2.new(1, -8, math.clamp(Left / Full, 0, 1), -8 * math.clamp(Left / Full, 0, 1))
	Label.Text = tostring(math.ceil(Left))
end

function Local.Schedule()
	if Pending then return end
	Pending = true
	task.defer(Local.Render)
end

-- From a click / tap on a slot (the Hotbar toggles its own selection) or a number key.
function Local.OnSlot(Index: number?)
	local Humanoid = Player.Character and Player.Character:FindFirstChildOfClass(`Humanoid`)
	if not Humanoid or Local.Busy() then
		Local.Schedule()
		return
	end
	local Tool = Index and Order[Index]
	if Tool and Tool.Parent ~= Player.Character then
		Humanoid:EquipTool(Tool)
	else
		Humanoid:UnequipTools()
	end
	Local.Schedule()
end

---| State |---

function Local.Busy(): boolean
	local Gui = Player:FindFirstChild(`PlayerGui`)
	return Player:GetAttribute(`InDialogue`) == true or (Gui ~= nil and Gui:FindFirstChild(`Lesson`) ~= nil)
end

function Local.UpdateVisibility()
	if Ui then Ui.Bottom.Visible = not Local.Busy() end
end

function Local.Commas(N: number): string
	local Text = tostring(math.floor(N))
	local Count
	repeat
		Text, Count = string.gsub(Text, `^(-?%d+)(%d%d%d)`, `%1,%2`)
	until Count == 0
	return Text
end

-- Yen: on a real Yen change (an UpdateYen action) it counts to the new total, the coin pulses and a
-- "+N" / "-N" chip floats off the plate. Loading a profile or swapping save slots just sets the number.
-- Reduce Motion: no rise or pulse.
local Shown = nil :: number? -- the number on the plate
local Target = nil :: number?
local CountTween = nil :: Tween?

function Local.ShowAmount(N: number)
	Shown = N
	Ui.Yen.Label.Text = Local.Commas(N)
end

function Local.YenChip(Delta: number)
	local Calm = Player:GetAttribute(`NHReducedMotion`) == true
	local Up = Delta > 0
	local Chip = Instance.new(`TextLabel`)
	Chip.Name = `YenChip`
	Chip.BackgroundTransparency = 1
	-- on the HUD frame (not inside the plate's row layout), just above the amount
	Chip.AnchorPoint = Vector2.new(0, 1)
	Chip.Position = UDim2.new(0.5, 452 + 48, 0, 8)
	if Kit.Phone and Kit.Phone() then -- the Yen plate sits above the bar on phones: float the chip above it
		Chip.AnchorPoint = Vector2.new(1, 1)
		Chip.Position = UDim2.new(0.5, BAR_W / 2, 0, BAR_Y - 66)
	end
	Chip.Size = UDim2.fromOffset(0, 24)
	Chip.AutomaticSize = Enum.AutomaticSize.X
	Chip.Text = `{if Up then `+` else `\u{2212}`}\u{00A5}{Local.Commas(math.abs(Delta))}`
	Local.TitleFont(Chip)
	Chip.TextSize = 20
	Chip.TextColor3 = if Up then Color3.fromRGB(150, 222, 140) else Color3.fromRGB(232, 92, 84)
	Chip.TextStrokeTransparency = 0.35
	Chip.TextStrokeColor3 = Color3.new(0, 0, 0)
	Chip.ZIndex = 13
	Chip.Parent = Ui.Bottom
	local Info = TweenInfo.new(1.3, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
	local Goal = { TextTransparency = 1; TextStrokeTransparency = 1 }
	if not Calm then Goal.Position = Chip.Position - UDim2.fromOffset(0, 26) end
	task.delay(0.35, function()
		if Chip.Parent then TweenService:Create(Chip, Info, Goal):Play() end
	end)
	task.delay(1.8, function() Chip:Destroy() end)
	if not Calm then
		local Scale = Ui.Yen.CoinScale
		Scale.Scale = 1.22
		TweenService:Create(Scale, TweenInfo.new(0.35, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 }):Play()
	end
end

function Local.SetYen(Profile, Animate: boolean?)
	if not (Ui and typeof(Profile) == `table` and typeof(Profile.Yen) == `number`) then return end
	local New = math.floor(Profile.Yen)
	local Silent = Target == nil or Animate ~= true
	if New == Target then return end
	local Old = Target
	Target = New
	if CountTween then CountTween:Cancel(); CountTween = nil end
	if Silent or Old == nil then
		Local.ShowAmount(New)
		return
	end
	Local.YenChip(New - Old)
	-- count from what's on the plate to the new total
	local Counter = Instance.new(`NumberValue`)
	Counter.Value = Shown or Old
	local This = TweenService:Create(Counter, TweenInfo.new(math.clamp(math.abs(New - Old) / 400, 0.35, 0.9), Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Value = New })
	CountTween = This
	Counter.Changed:Connect(function(V)
		if CountTween == This then Local.ShowAmount(math.round(V)) end
	end)
	-- Completed also fires on Cancel (even after it finished): only the live, finished count may write
	This.Completed:Connect(function(State)
		if CountTween == This and State == Enum.PlaybackState.Completed then
			CountTween = nil
			Local.ShowAmount(New)
		end
		Counter:Destroy()
	end)
	This:Play()
end

function Local.PostureBroken(Daze: Instance?)
	if Ui and Ui.Posture then Ui.Posture:Break(Daze) end
end

function Local.BindCharacter(Character: Model)
	for _, Connection in CharConns do Connection:Disconnect() end
	table.clear(CharConns)
	local Humanoid = Character:WaitForChild(`Humanoid`, 10) :: Humanoid?
	if not Humanoid or Player.Character ~= Character then return end

	local function Health(Instant: boolean?)
		Local.OnHealth(if Humanoid.MaxHealth > 0 then Humanoid.Health / Humanoid.MaxHealth else 0, Instant)
	end
	if Thorn then Thorn.Value = nil end -- a new body: no hit effects for its first reading
	-- Posture is the server's Humanoid attribute (DamageLogic fills it on blocked hits, it breaks
	-- at PostureMax and resets to 0; Features.Posture drains it). The rail only draws it.
	local LastPosture = 0
	local function Posture()
		local Max = CombatConfig.PostureMax or 100
		local Value = tonumber(Character:GetAttribute(`Posture`) or Humanoid:GetAttribute(`Posture`)) or 0
		local Fraction = math.clamp(Value / Max, 0, 1)
		-- A break jumps straight from high to 0 (a normal drain steps down slowly).
		if Value <= 0 and LastPosture >= Max * 0.6 then Local.PostureBroken() end
		Ui.Posture:Set(Fraction)
		LastPosture = Value
	end
	local function Downed()
		if Humanoid:GetAttribute(`Downed`) and Humanoid.Health > 0 then
			local Until = Character:GetAttribute(`DownedUntil`)
			Ui.Downed:Start(if Until then math.max(0, Until - workspace:GetServerTimeNow()) else 0)
		else
			Ui.Downed:Stop(true)
		end
	end

	Health(true)
	Posture()
	Downed()
	Local.ApplyForm(Character, Humanoid, true)
	table.insert(CharConns, Humanoid.HealthChanged:Connect(function() Health(false) end))
	table.insert(CharConns, Humanoid:GetPropertyChangedSignal(`MaxHealth`):Connect(function() Health(false) end))
	table.insert(CharConns, Character.AttributeChanged:Connect(function(Name)
		if Name == `Posture` then Posture() elseif Name == `DownedUntil` then Downed()
		elseif Name == `Transformation` then Local.ApplyForm(Character, Humanoid) end
	end))
	table.insert(CharConns, Humanoid.AttributeChanged:Connect(function(Name)
		if Name == `Posture` then Posture() elseif Name == `Downed` then Downed() Local.ApplyForm(Character, Humanoid) end
	end))
	table.insert(CharConns, Character.ChildAdded:Connect(Local.Schedule))
	-- the combat's guard-break effect (StateController Misc "Posture Break") puts a Daze on the broken character
	-- for as long as they're paralyzed: it also catches instant breaks from low posture
	table.insert(CharConns, Character.ChildAdded:Connect(function(Child)
		if Child.Name == `Daze` then Local.PostureBroken(Child) end
	end))
	table.insert(CharConns, Character.ChildRemoved:Connect(Local.Schedule))

	local Backpack = Player:WaitForChild(`Backpack`, 10)
	if Backpack then
		table.insert(CharConns, Backpack.ChildAdded:Connect(Local.Schedule))
		table.insert(CharConns, Backpack.ChildRemoved:Connect(Local.Schedule))
	end
	Local.Schedule()
end

---| API |---

function Shared.GetUi()
	return Ui
end

function Shared.OnStart()
	Ui = Local.Build()
	Local.BuildHotbar(BASE_SLOTS)
	if Ui.ScaleOpts then
		local function Refit() task.defer(Local.TouchFit) end
		Player:GetAttributeChangedSignal(`NHTouchReserveRight`):Connect(Refit)
		local function HookCam()
			local Cam = workspace.CurrentCamera
			if Cam then Cam:GetPropertyChangedSignal(`ViewportSize`):Connect(Refit) end
			Refit()
		end
		workspace:GetPropertyChangedSignal(`CurrentCamera`):Connect(HookCam)
		if Kit.PreviewChanged then Kit.PreviewChanged:Connect(Refit) end -- Studio phone previews
		-- the Study Group dock (which the bar stands on) is built after the HUD
		-- (the dock is hidden in the main menu, and the touch buttons can change size): refit when either changes
		task.spawn(function()
			local Seen = ``
			while Ui and Ui.Gui.Parent do
				task.wait(1)
				local PG = Player:FindFirstChild(`PlayerGui`)
				local SG = PG and PG:FindFirstChild(`NHStudyGroup`)
				local Dock = SG and SG:FindFirstChild(`Dock`)
				local Key = `{Player:GetAttribute(`NHTouchReserveRight`)}|{SG and SG.Enabled}|{Dock and Dock.Visible}|{Dock and Dock.AbsoluteSize.Y}`
				if Key ~= Seen then Seen = Key Local.TouchFit() end
			end
		end)
		HookCam()
	end
	pcall(function() StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.Health, false) end)
	pcall(function() StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.Backpack, false) end)

	Player.CharacterAdded:Connect(function(Character) task.spawn(Local.BindCharacter, Character) end)
	if Player.Character then task.spawn(Local.BindCharacter, Player.Character) end
	-- (inventory QOL 1.91) drain the cooldown shades
	game:GetService(`RunService`).Heartbeat:Connect(function()
		for Index in Shades do Local.StepShade(Index) end
	end)

	UserInputService.InputBegan:Connect(function(Input, Processed)
		if Processed or not Ui then return end
		local Index = DIGITS[Input.KeyCode]
		if not Index or Index > Ui.Slots or Local.Busy() or UserInputService:GetFocusedTextBox() then return end
		local Current = Ui.Hotbar:GetSelected()
		Ui.Hotbar:Select(if Current == Index then nil else Index) -- fires OnSlot
	end)

	Player:GetAttributeChangedSignal(`InDialogue`):Connect(Local.UpdateVisibility)
	local Gui = Player:WaitForChild(`PlayerGui`)
	Gui.ChildAdded:Connect(function(Child) if Child.Name == `Lesson` then Local.UpdateVisibility() end end)
	Gui.ChildRemoved:Connect(function(Child) if Child.Name == `Lesson` then Local.UpdateVisibility() end end)
	Local.UpdateVisibility()

	StateController.ProfileUpdated:Connect(function(State, Action)
		Local.SetYen(State, typeof(Action) == `table` and Action.type == `UpdateYen`)
	end)

	task.spawn(function()
		local Seen = StateController.GetProfile(true)
		Local.SetYen(Seen)
		-- a whole profile arriving (save-slot swap) doesn't fire ProfileUpdated: show its Yen, silently
		while true do
			task.wait(1)
			local Now = StateController.GetProfile(false)
			if Now and Now ~= Seen then
				Seen = Now
				Local.SetYen(Now)
			end
		end
	end)
end

return Shared
