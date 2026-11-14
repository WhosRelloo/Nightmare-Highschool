
---| Services |---

local Debris = game:GetService(`Debris`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

---| Modules |---
local Blood = require(game:GetService("ReplicatedStorage"):WaitForChild("Packages"):WaitForChild("Visuals"):WaitForChild("Blood"))

local EmitManager = require(ReplicatedStorage.Functions.EmitManager)
local WeaponsConfig = require(ReplicatedStorage.Config.Weapons)

local Players = game:GetService(`Players`)

-- (combat audit) hit-stop: the attack and hit-react tracks hold for a few frames on contact (the house style: light 3,
-- heavy 6 at 60 fps). Only Action3/Action4 tracks (swings, hit reacts) pause; walking and idle carry on.
local HOLD = { [Enum.AnimationPriority.Action3] = true; [Enum.AnimationPriority.Action4] = true }
-- (feel set) the readouts: a counter-hit flash and sound, your combo count, and optional damage numbers. Text only, in
-- the UI kit's fonts and colours; small, at the edge, and gone a moment after the string ends.
local TweenService = game:GetService(`TweenService`)
local CRIMSON = Color3.fromRGB(205, 58, 58)
local Readout = { N = 0; Last = 0; Gui = nil }
local function Setting(Key: string, Default: any): any
	local Ok, V = pcall(function() return require(ReplicatedStorage.UI.Settings).Get(Key) end)
	if Ok and V ~= nil then return V end
	return Default
end
local function Calm(): boolean return Players.LocalPlayer:GetAttribute(`NHReducedMotion`) == true end
local function Stroke(T: Instance) local S = Instance.new(`UIStroke`) S.Color = Color3.fromRGB(14, 10, 12) S.Thickness = 1.5 S.Transparency = 0.15 S.Parent = T end
local function ComboGui()
	if Readout.Gui and Readout.Gui.Parent then return Readout.Gui end
	local Kit = require(ReplicatedStorage.UI.Components)
	local Fonts, C = Kit.Theme.Fonts, Kit.Theme.Colors
	local G = Instance.new(`ScreenGui`)
	G.Name = `NHComboCounter` G.ResetOnSpawn = false G.DisplayOrder = 6 G.IgnoreGuiInset = true
	local Root = Instance.new(`Frame`)
	Root.Name = `Root` Root.BackgroundTransparency = 1 Root.AnchorPoint = Vector2.new(1, 0.5)
	Root.Position = UDim2.new(1, -40, 0.6, 0) Root.Size = UDim2.fromOffset(160, 92) Root.Parent = G -- clear of the quest tracker (40% sat behind it)
	Instance.new(`UIScale`, Root).Name = `Pop`
	local Tag = Kit.Text({ Name = `Counter`; Text = `COUNTER`; Font = Fonts.Title; TextSize = 17; TextColor3 = CRIMSON; TextXAlignment = Enum.TextXAlignment.Right;
		Position = UDim2.fromOffset(0, 0); Size = UDim2.new(1, 0, 0, 20); Visible = false; Parent = Root })
	local Num = Kit.Text({ Name = `Count`; Text = `2`; Font = Fonts.Title; TextSize = 46; TextColor3 = C.Gold; TextXAlignment = Enum.TextXAlignment.Right;
		Position = UDim2.fromOffset(0, 18); Size = UDim2.new(1, 0, 0, 48); Parent = Root })
	local Word = Kit.Text({ Name = `Hits`; Text = `H I T S`; Font = Fonts.Title; TextSize = 13; TextColor3 = C.TextDim; TextXAlignment = Enum.TextXAlignment.Right;
		Position = UDim2.fromOffset(0, 66); Size = UDim2.new(1, 0, 0, 16); Parent = Root })
	for _, T in { Tag, Num, Word } do Stroke(T) end
	G.Parent = Players.LocalPlayer:WaitForChild(`PlayerGui`)
	Readout.Gui = G
	return G
end
local function Fade(G: ScreenGui, To: number, Time: number)
	for _, T in G.Root:GetChildren() do
		if T:IsA(`TextLabel`) then
			TweenService:Create(T, TweenInfo.new(Time), { TextTransparency = To }):Play()
			local S = T:FindFirstChildOfClass(`UIStroke`)
			if S then TweenService:Create(S, TweenInfo.new(Time), { Transparency = math.max(To, 0.15) }):Play() end
		end
	end
end
local function ShowCombo(Tag: string?) -- (fist moveset) COUNTER, RIPOSTE or a move's name over the count
	local Now = os.clock()
	Readout.N = if Now - Readout.Last <= 1.6 then Readout.N + 1 else 1
	Readout.Last = Now
	if Readout.N < 2 and not Tag then return end -- one hit isn't a combo: nothing on screen
	local G = ComboGui()
	G.Root.Count.Text = tostring(Readout.N)
	G.Root.Count.Visible = Readout.N >= 2
	G.Root.Hits.Visible = Readout.N >= 2
	if Tag then
		G.Root.Counter.Text = Tag
		G.Root.Counter.TextColor3 = if Tag == `COUNTER` or Tag == `RIPOSTE` then CRIMSON else require(ReplicatedStorage.UI.Components).Theme.Colors.Gold
	end
	G.Root.Counter.Visible = Tag ~= nil or (G.Root.Counter.Visible and Now - (Readout.CounterAt or 0) < 0.8)
	if Tag then Readout.CounterAt = Now end
	Fade(G, 0, 0.06)
	if not Calm() then
		G.Root.Pop.Scale = 1.22
		TweenService:Create(G.Root.Pop, TweenInfo.new(0.14, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 }):Play()
	end
	task.delay(1.6, function() if Readout.Last == Now and Readout.Gui then Fade(Readout.Gui, 1, 0.35) end end)
end
local function DamageNumber(Target: Model, Damage: number, Heavy: boolean, Counter: boolean)
	local Head = Target:FindFirstChild(`Head`) or Target:FindFirstChild(`HumanoidRootPart`)
	if not Head then return end
	local Kit = require(ReplicatedStorage.UI.Components)
	local B = Instance.new(`BillboardGui`)
	B.Name = `NHDamageNumber` B.Size = UDim2.fromOffset(90, 34) B.AlwaysOnTop = true B.LightInfluence = 0 B.MaxDistance = 90
	B.StudsOffsetWorldSpace = Vector3.new(math.random(-8, 8) / 10, 2.1, 0) B.Adornee = Head
	local V = math.floor(Damage * 10 + 0.5) / 10
	local T = Kit.Text({ Text = if V == math.floor(V) then tostring(math.floor(V)) else string.format(`%.1f`, V); Font = Kit.Theme.Fonts.Title;
		TextSize = if Heavy or Counter then 24 else 18; TextColor3 = if Counter then CRIMSON elseif Heavy then Kit.Theme.Colors.Gold else Color3.fromRGB(236, 228, 214);
		TextXAlignment = Enum.TextXAlignment.Center; Size = UDim2.fromScale(1, 1); Parent = B })
	Stroke(T)
	B.Parent = Players.LocalPlayer:WaitForChild(`PlayerGui`)
	local Rise = if Calm() then 0.4 else 1.3
	TweenService:Create(B, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { StudsOffsetWorldSpace = B.StudsOffsetWorldSpace + Vector3.new(0, Rise, 0) }):Play()
	TweenService:Create(T, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, 0.35), { TextTransparency = 1 }):Play()
	Debris:AddItem(B, 0.8)
end
local function CounterFlash(Target: Model)
	local Root = Target:FindFirstChild(`HumanoidRootPart`)
	local S = ReplicatedStorage.Assets.Sounds.Default:FindFirstChild(`Critical`)
	if S and Root then
		local Ok, C = pcall(EmitManager.CloneSound, S, Root)
		if Ok and typeof(C) == `Instance` and C:IsA(`Sound`) then C.PlaybackSpeed = 1.35 end
	end
	if Players.LocalPlayer:GetAttribute(`NHReducedFlash`) == true then return end
	local Hl = Instance.new(`Highlight`)
	Hl.FillColor = Color3.new(1, 1, 1) Hl.OutlineColor = Color3.new(1, 1, 1)
	Hl.FillTransparency = 0.45 Hl.OutlineTransparency = 0.1 Hl.DepthMode = Enum.HighlightDepthMode.Occluded
	Hl.Adornee = Target Hl.Parent = workspace:FindFirstChild(`Visuals`) or workspace
	TweenService:Create(Hl, TweenInfo.new(0.22, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { FillTransparency = 1; OutlineTransparency = 1 }):Play()
	Debris:AddItem(Hl, 0.3)
end
local function Readouts(Paramaters, Me: Model?, Heavy: boolean, Counter: boolean)
	if Counter then CounterFlash(Paramaters.User) end
	if not (Me and Paramaters.Attacker == Me) then return end
	local Tag = if Counter then `COUNTER` elseif typeof(Paramaters.Tag) == `string` then Paramaters.Tag else nil
	if Setting(`ComboCounter`, true) then ShowCombo(Tag) end
	if Setting(`DamageNumbers`, false) and typeof(Paramaters.Damage) == `number` then DamageNumber(Paramaters.User, Paramaters.Damage, Heavy, Counter or Tag == `RIPOSTE`) end
end

local function HitStop(Model: Model?, Duration: number)
	local Hum = Model and Model:FindFirstChildWhichIsA(`Humanoid`)
	local Animator = Hum and Hum:FindFirstChildOfClass(`Animator`)
	if not Animator then return end
	local Held = {}
	for _, T in Animator:GetPlayingAnimationTracks() do
		if HOLD[T.Priority] and T.Speed > 0 then
			table.insert(Held, { T, T.Speed })
			T:AdjustSpeed(0)
		end
	end
	if #Held == 0 then return end
	task.delay(Duration, function()
		for _, H in Held do
			if H[1].IsPlaying and H[1].Speed == 0 then H[1]:AdjustSpeed(H[2]) end
		end
	end)
end

---| Effect |---

return function (Character: Model, Paramaters: { User: Model; Weapon: string } )
	local Config = WeaponsConfig[Paramaters.Weapon]
	if not Config then return end

	local Humanoid = Paramaters.User:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	if not Humanoid then return end

	-- (combat audit) contact weight: both bodies hold, and the attacker's and the victim's cameras jolt (Camera Shake setting)
	local Heavy = Paramaters.Heavy == true
	local Counter = Paramaters.Counter == true -- (feel set)
	local Hold = if Heavy or Counter then 0.1 else 0.05
	HitStop(Paramaters.User, Hold)
	if typeof(Paramaters.Attacker) == `Instance` then HitStop(Paramaters.Attacker, Hold) end
	local Me = Players.LocalPlayer and Players.LocalPlayer.Character
	if Me and (Me == Paramaters.Attacker or Me == Paramaters.User) then
		EmitManager.ShakeCamera(if Heavy or Counter then 3 else 1.4, 10, 0, if Heavy or Counter then 0.3 else 0.16)
	end
	pcall(Readouts, Paramaters, Me, Heavy, Counter) -- (feel set) a readout must never stop the hit's own effects

	local DamageType = Config.DamageType 
	-- (audit) a DamageType without its own HitType effect or hit sounds (Slash) falls back to Blunt instead of erroring
	local HitTypes = ReplicatedStorage.Assets.Effects.HitType
	local HitSounds = ReplicatedStorage.Assets.Sounds.Hit
	if not (DamageType and HitTypes:FindFirstChild(DamageType) and HitSounds:FindFirstChild(DamageType)) then DamageType = `Blunt` end
	local RootPart = Humanoid.RootPart
	local HitPosition = RootPart.CFrame

	local HitEffect = EmitManager.SpawnGroup(ReplicatedStorage.Assets.Effects.HitType[DamageType], HitPosition, 5)

	local sound = ReplicatedStorage.Assets.Sounds.Hit[DamageType]:GetChildren() :: Sound
	if #sound > 0 then -- (audit) HitCounter runs past the sound count: wrap it
		EmitManager.CloneSound(sound[((tonumber(Humanoid:GetAttribute("HitCounter")) or 1) - 1) % #sound + 1], HitEffect)
	end
	EmitManager.Emit(HitEffect:GetDescendants())



	if DamageType == "Blood" then
		local Torso = Paramaters.User:FindFirstChild("Torso")

		if Torso then


			if math.random(1, 3) == 1 then
				Blood.createBloodSplatter(Paramaters.User, { Amount = math.random(1, 3) })
			else
				Blood.createBloodSplatter(Paramaters.User, { Amount = math.random(1, 3) })
			end

		end
	end
end
