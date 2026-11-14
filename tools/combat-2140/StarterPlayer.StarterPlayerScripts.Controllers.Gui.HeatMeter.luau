--[[
	HeatMeter (client). Controllers.Gui.HeatMeter   (combat concept 18, 2.14.0; server: ServerStorage.Packages.Heat)
	The Heat meter: a small ember brazier on the right cap of the Thornrose health bar (KitHud.Bottom), mirroring the
	hunger reliquary on the left cap. Kept small (44 px) and quiet so the bar stays uncluttered.
	Reads the character attribute NHHeat (0-100); a full bar makes the next Z / X / C skill an EX.
	Layers (bottom to top): Glow (the full-bar halo), Frame (the iron brazier), Fill (the coals, rising with the level),
	Sparks. Art: Config.HeatArt (group uploads); while an id is empty a plain stand-in draws instead.
	Motion (one RenderStepped loop):
	  level  eases toward the value (a critically damped spring), never jumps;
	  idle   the coals flicker (brightness +-6% on two out-of-phase sines); empty, the brazier dims to 55%;
	  fill   a spark drifts up from the coals every ~0.5 s while there's heat, faster as it rises;
	  full   the halo breathes (1.1 Hz) and the brazier swells 4%;
	  spend  the level drops to 0 with a 0.35 s flare ring (the EX itself flares in the world: StateController "Heat EX").
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local TweenService = game:GetService(`TweenService`)

local Player = Players.LocalPlayer

local Art = {}
pcall(function() Art = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`HeatArt`)) end)
local function Has(Key: string): boolean return typeof(Art[Key]) == `string` and Art[Key] ~= `` end

local BAR_W, BAR_H, BAR_Y = 600, 50, 2 -- Controllers.Gui.KitHud's Thornrose bar, in KitHud.Bottom
local SIZE = 44
local CAP_IN = 30 -- the brazier's centre, this far in from the bar's right end (on the cap's boss)
local EMBER = Color3.fromRGB(232, 162, 58)
local CRIMSON = Color3.fromRGB(139, 26, 26)
local HOT = Color3.fromRGB(255, 236, 190)
local IRON = Color3.fromRGB(24, 20, 20)

local Shared = {}
local Local = {}
local Ui = nil
local Shown, Target, Vel = 0, 0, 0
local SparkClock = 0

local function new(Class: string, Props: { [string]: any }, Parent: Instance?)
	local I = Instance.new(Class)
	if I:IsA(`GuiObject`) then I.BorderSizePixel = 0 end
	for K, V in Props do (I :: any)[K] = V end
	I.Parent = Parent
	return I
end

function Local.Build(Bottom: Frame)
	local Root = new(`Frame`, {
		Name = `NHHeat`; BackgroundTransparency = 1; ZIndex = 20; AnchorPoint = Vector2.new(0.5, 0.5);
		Position = UDim2.new(0.5, BAR_W / 2 - CAP_IN, 0, BAR_Y + BAR_H / 2); Size = UDim2.fromOffset(SIZE, SIZE);
	}, Bottom)
	local Scale = new(`UIScale`, { Scale = 1 }, Root)
	local Glow = new(`ImageLabel`, {
		Name = `Glow`; BackgroundTransparency = 1; ZIndex = 20; Image = if Has(`Glow`) then Art.Glow else `rbxassetid://117234203443052`;
		ImageColor3 = EMBER; ImageTransparency = 1; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5);
		Size = UDim2.fromScale(1.5, 1.5); -- the art's glow is 1.5x the frame, same centre
	}, Root)
	-- the brazier: the art, or an iron disc with a brass rim
	local Frame
	if Has(`Frame`) then
		Frame = new(`ImageLabel`, { Name = `Frame`; BackgroundTransparency = 1; ZIndex = 21; Image = Art.Frame; Size = UDim2.fromScale(1, 1) }, Root)
	else
		Frame = new(`Frame`, { Name = `Frame`; BackgroundColor3 = IRON; ZIndex = 21; Size = UDim2.fromScale(1, 1) }, Root)
		new(`UICorner`, { CornerRadius = UDim.new(0.5, 0) }, Frame)
		new(`UIStroke`, { Color = Color3.fromRGB(150, 112, 60); Thickness = 1.5; Transparency = 0.15 }, Frame)
	end
	-- the coals: a clip that rises from FillBottom to FillTop, the fill art inside it pinned to the brazier
	local Top, Bot = Art.FillTop or 0.3, Art.FillBottom or 0.78
	if not Has(`Fill`) then Top, Bot = 0.12, 0.88 end
	local Clip = new(`Frame`, {
		Name = `FillClip`; BackgroundTransparency = 1; ClipsDescendants = true; ZIndex = 22; AnchorPoint = Vector2.new(0, 1);
		Position = UDim2.fromScale(0, Bot); Size = UDim2.fromScale(1, 0);
	}, Root)
	local Fill
	if Has(`Fill`) then
		-- pinned to the brazier, not the clip: the clip's bottom is the coal line (Bot), the image's bottom is the brazier's
		Fill = new(`ImageLabel`, { Name = `Fill`; BackgroundTransparency = 1; ZIndex = 22; Image = Art.Fill; AnchorPoint = Vector2.new(0, 1);
			Position = UDim2.new(0, 0, 1, math.floor((1 - Bot) * SIZE + 0.5)); Size = UDim2.fromOffset(SIZE, SIZE) }, Clip)
	else
		Fill = new(`Frame`, { Name = `Fill`; BackgroundColor3 = Color3.new(1, 1, 1); ZIndex = 22; AnchorPoint = Vector2.new(0.5, 1);
			Position = UDim2.new(0.5, 0, 1, 0); Size = UDim2.fromOffset(SIZE * 0.76, SIZE * 0.76) }, Clip)
		new(`UICorner`, { CornerRadius = UDim.new(0.5, 0) }, Fill)
		new(`UIGradient`, { Rotation = -90; Color = ColorSequence.new({
			ColorSequenceKeypoint.new(0, CRIMSON), ColorSequenceKeypoint.new(0.55, EMBER), ColorSequenceKeypoint.new(1, HOT) }) }, Fill)
	end
	local Sparks = new(`Frame`, { Name = `Sparks`; BackgroundTransparency = 1; ZIndex = 23; Size = UDim2.fromScale(1, 1) }, Root)
	Ui = { Root = Root; Scale = Scale; Glow = Glow; Frame = Frame; Clip = Clip; Fill = Fill; Sparks = Sparks; Top = Top; Bot = Bot }
end

function Local.Spark()
	if not Ui then return end
	local Level = Ui.Bot - (Ui.Bot - Ui.Top) * Shown
	local S = new(`ImageLabel`, {
		Name = `Spark`; BackgroundTransparency = 1; ZIndex = 23; Image = if Has(`Spark`) then Art.Spark else `rbxasset://textures/particles/sparkles_main.dds`;
		ImageColor3 = HOT; ImageTransparency = 0.1; AnchorPoint = Vector2.new(0.5, 0.5);
		Position = UDim2.fromScale(0.35 + math.random() * 0.3, Level); Size = UDim2.fromOffset(6, 6);
	}, Ui.Sparks)
	local T = TweenService:Create(S, TweenInfo.new(0.7 + math.random() * 0.3, Enum.EasingStyle.Sine, Enum.EasingDirection.Out), {
		Position = UDim2.fromScale(S.Position.X.Scale + (math.random() - 0.5) * 0.3, Level - 0.55); ImageTransparency = 1; Size = UDim2.fromOffset(2, 2) })
	T.Completed:Once(function() S:Destroy() end)
	T:Play()
end

-- the EX flare ring on the brazier when the bar is spent
function Local.Spend()
	if not Ui then return end
	local Ring = new(`ImageLabel`, {
		Name = `Spend`; BackgroundTransparency = 1; ZIndex = 24; Image = if Has(`Flare`) then Art.Flare else `rbxassetid://117234203443052`;
		ImageColor3 = HOT; ImageTransparency = 0; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromScale(1, 1);
	}, Ui.Root)
	local T = TweenService:Create(Ring, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = UDim2.fromScale(2.6, 2.6); ImageTransparency = 1 })
	T.Completed:Once(function() Ring:Destroy() end)
	T:Play()
end

function Local.Step(Dt: number)
	if not (Ui and Ui.Root.Parent) then return end
	-- the level: a critically damped spring toward the value
	local K = 60
	local A = K * (Target - Shown) - 2 * math.sqrt(K) * Vel
	Vel += A * Dt
	Shown = math.clamp(Shown + Vel * Dt, 0, 1)
	Ui.Clip.Size = UDim2.fromScale(1, (Ui.Bot - Ui.Top) * Shown + (if Shown > 0 then 0.02 else 0))
	local T = os.clock()
	local Flicker = 1 + 0.06 * math.sin(T * 7.3) + 0.04 * math.sin(T * 11.9 + 1.7)
	local Full = Target >= 0.999
	local Bright = math.clamp(0.75 + 0.25 * Shown, 0, 1) * Flicker
	if Ui.Fill:IsA(`ImageLabel`) then
		Ui.Fill.ImageColor3 = Color3.new(Bright, Bright, Bright)
	else
		Ui.Fill.BackgroundColor3 = Color3.new(Bright, Bright, Bright)
	end
	-- empty: the brazier dims; full: the halo breathes and it swells a little
	local Dim = if Shown < 0.02 then 0.45 else 0
	if Ui.Frame:IsA(`ImageLabel`) then Ui.Frame.ImageTransparency = Dim else Ui.Frame.BackgroundTransparency = Dim end
	Ui.Glow.ImageTransparency = if Full then 0.35 + 0.3 * (0.5 + 0.5 * math.sin(T * 1.1 * 2 * math.pi)) else 1 - 0.35 * math.max(0, Shown - 0.6)
	Ui.Scale.Scale = if Full then 1.04 + 0.01 * math.sin(T * 1.1 * 2 * math.pi) else 1
	-- sparks: one about every 0.5 s with heat, faster as it rises
	if Shown > 0.04 then
		SparkClock += Dt * (0.8 + 2.4 * Shown)
		if SparkClock >= 1 then SparkClock = 0 Local.Spark() end
	end
end

function Local.Mount()
	local PG = Player:WaitForChild(`PlayerGui`)
	local Hud = PG:WaitForChild(`KitHud`, 120)
	local Bottom = Hud and Hud:WaitForChild(`Bottom`, 30)
	if not Bottom then return end
	if Ui and Ui.Root then Ui.Root:Destroy() end
	Local.Build(Bottom)
end

function Local.Watch(Character: Model)
	Target = (tonumber(Character:GetAttribute(`NHHeat`)) or 0) / 100
	Shown = Target
	Character:GetAttributeChangedSignal(`NHHeat`):Connect(function()
		local Was = Target
		Target = math.clamp((tonumber(Character:GetAttribute(`NHHeat`)) or 0) / 100, 0, 1)
		if Was >= 0.999 and Target <= 0.001 then Local.Spend() end
	end)
end

function Shared.OnStart()
	task.spawn(function()
		Local.Mount()
		if Player.Character then Local.Watch(Player.Character) end
		Player.CharacterAdded:Connect(function(C)
			Local.Watch(C)
			task.defer(function() if not (Ui and Ui.Root.Parent) then Local.Mount() end end)
		end)
		RunService.RenderStepped:Connect(Local.Step)
	end)
end

return Shared
