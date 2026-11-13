--[[
	Race Fist (client effect): the last hit of a fist string carrying the attacker's race (combat concept 17, 2.14.0;
	server: ServerStorage.Packages.RaceFists). A short burst in the race's colour where the hit landed: sparks, a ring,
	a flash of light. A Crimson or Blue moon event recolours it. No blood or gore (the vampire's is a crimson shimmer,
	the ghoul's a sickly mist).
]]
local Debris = game:GetService(`Debris`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local TweenService = game:GetService(`TweenService`)

local COLORS = {
	Vampire = Color3.fromRGB(196, 30, 58);
	Priest = Color3.fromRGB(255, 236, 170);
	Werewolf = Color3.fromRGB(232, 162, 58);
	Wraith = Color3.fromRGB(150, 214, 255);
	Ghoul = Color3.fromRGB(150, 196, 96);
	Human = Color3.fromRGB(226, 226, 232);
}
local MOON = { Crimson = Color3.fromRGB(200, 24, 40); Blue = Color3.fromRGB(70, 120, 255) }
local SPARK = `rbxasset://textures/particles/sparkles_main.dds`
local RING = `rbxasset://textures/particles/explosion01_shockwave_color.dds`

local function MoonTint(Moon: any): Color3?
	if typeof(Moon) ~= `string` then return nil end
	for Key, C in MOON do if string.find(Moon, Key) then return C end end
	return nil
end

return function(_Character: Model, Paramaters: { User: Model; Attacker: Model?; Race: string?; Moon: any })
	local User = Paramaters.User
	local Root = User and (User:FindFirstChild(`Torso`) or User:FindFirstChild(`HumanoidRootPart`))
	if not (Root and Root:IsA(`BasePart`)) then return end
	local Base = COLORS[Paramaters.Race or ``] or COLORS.Human
	local Tint = MoonTint(Paramaters.Moon)
	local Color = if Tint then Base:Lerp(Tint, 0.55) else Base

	local A = Instance.new(`Attachment`)
	A.Name = `NHRaceFist`
	A.Parent = Root

	local Sparks = Instance.new(`ParticleEmitter`)
	Sparks.Texture = SPARK
	Sparks.Color = ColorSequence.new(Color:Lerp(Color3.new(1, 1, 1), 0.35), Color)
	Sparks.LightEmission = 1
	Sparks.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5), NumberSequenceKeypoint.new(1, 0) })
	Sparks.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(1, 1) })
	Sparks.Lifetime = NumberRange.new(0.25, 0.45)
	Sparks.Speed = NumberRange.new(10, 18)
	Sparks.SpreadAngle = Vector2.new(180, 180)
	Sparks.Drag = 6
	Sparks.Rate = 0
	Sparks.Parent = A
	Sparks:Emit(if Paramaters.Race == `Wraith` or Paramaters.Race == `Ghoul` then 14 else 22)

	local Ring = Instance.new(`ParticleEmitter`)
	Ring.Texture = RING
	Ring.Color = ColorSequence.new(Color)
	Ring.LightEmission = 0.8
	Ring.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.6), NumberSequenceKeypoint.new(1, 5) })
	Ring.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2), NumberSequenceKeypoint.new(1, 1) })
	Ring.Lifetime = NumberRange.new(0.3)
	Ring.Speed = NumberRange.new(0)
	Ring.Orientation = Enum.ParticleOrientation.VelocityPerpendicular
	Ring.Rate = 0
	Ring.Parent = A
	Ring:Emit(1)

	local Light = Instance.new(`PointLight`)
	Light.Color = Color
	Light.Range = 12
	Light.Brightness = 4
	Light.Parent = A
	TweenService:Create(Light, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Brightness = 0 }):Play()

	Debris:AddItem(A, 1)
end
