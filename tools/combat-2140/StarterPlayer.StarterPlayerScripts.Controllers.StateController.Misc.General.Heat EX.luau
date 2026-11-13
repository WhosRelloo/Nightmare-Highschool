--[[
	Heat EX (client effect): a skill started on a full Heat bar (combat concept 18, 2.14.0; server:
	ServerStorage.Packages.Heat). A gold-ember flare on the fighter: a burst of embers, a rising ring and a warm flash,
	and the "EX" call on their combo readout if it's you. The flare art is a group upload (Config.HeatArt.Flare); until
	it's set the stock spark texture stands in.
]]
local Debris = game:GetService(`Debris`)
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local TweenService = game:GetService(`TweenService`)

local GOLD = Color3.fromRGB(232, 162, 58)
local HOT = Color3.fromRGB(255, 236, 190)

return function(_Character: Model, Paramaters: { User: Model; Skill: string? })
	local User = Paramaters.User
	local Root = User and (User:FindFirstChild(`Torso`) or User:FindFirstChild(`HumanoidRootPart`))
	if not (Root and Root:IsA(`BasePart`)) then return end
	local Art = {}
	pcall(function() Art = require(ReplicatedStorage.Config.HeatArt) end)
	local Flare = if typeof(Art.Flare) == `string` and Art.Flare ~= `` then Art.Flare else `rbxasset://textures/particles/sparkles_main.dds`
	local Spark = if typeof(Art.Spark) == `string` and Art.Spark ~= `` then Art.Spark else `rbxasset://textures/particles/fire_main.dds`

	local A = Instance.new(`Attachment`)
	A.Name = `NHHeatEX`
	A.Parent = Root

	local Burst = Instance.new(`ParticleEmitter`)
	Burst.Texture = Flare
	Burst.Color = ColorSequence.new(HOT, GOLD)
	Burst.LightEmission = 1
	Burst.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1.5), NumberSequenceKeypoint.new(0.3, 6), NumberSequenceKeypoint.new(1, 7) })
	Burst.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1), NumberSequenceKeypoint.new(1, 1) })
	Burst.Lifetime = NumberRange.new(0.4)
	Burst.Speed = NumberRange.new(0)
	Burst.Rotation = NumberRange.new(0, 360)
	Burst.Rate = 0
	Burst.Parent = A
	Burst:Emit(1)

	local Embers = Instance.new(`ParticleEmitter`)
	Embers.Texture = Spark
	Embers.Color = ColorSequence.new(HOT, GOLD)
	Embers.LightEmission = 1
	Embers.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(1, 0) })
	Embers.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(1, 1) })
	Embers.Lifetime = NumberRange.new(0.5, 0.9)
	Embers.Speed = NumberRange.new(6, 14)
	Embers.Acceleration = Vector3.new(0, 10, 0)
	Embers.SpreadAngle = Vector2.new(180, 180)
	Embers.Drag = 3
	Embers.Rate = 0
	Embers.Parent = A
	Embers:Emit(30)

	local Light = Instance.new(`PointLight`)
	Light.Color = GOLD
	Light.Range = 16
	Light.Brightness = 5
	Light.Parent = A
	TweenService:Create(Light, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Brightness = 0 }):Play()

	Debris:AddItem(A, 1.5)
end
