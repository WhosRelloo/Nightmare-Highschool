--[[
	Beast Stagger (client effect): a beast's footing broken by fists (combat concept 22, 2.15.0; server:
	ServerStorage.Packages.BeastStagger). A pale-gold crack of light on the beast: a shock ring on the ground, a burst
	of sparks off its body, a short bright flash, and the camera gives a small kick for the one who did it (Camera
	Shake setting). No blood or gore.
]]
local Debris = game:GetService(`Debris`)
local Players = game:GetService(`Players`)
local TweenService = game:GetService(`TweenService`)

local PALE = Color3.fromRGB(255, 240, 200)
local GOLD = Color3.fromRGB(232, 172, 74)
local SPARK = `rbxasset://textures/particles/sparkles_main.dds`
local RING = `rbxasset://textures/particles/explosion01_shockwave_color.dds`

return function(_Character: Model, Paramaters: { User: Model; Attacker: Model? })
	local User = Paramaters.User
	local Root = User and (User:FindFirstChild(`HumanoidRootPart`) or User.PrimaryPart)
	if not (Root and Root:IsA(`BasePart`)) then return end

	local A = Instance.new(`Attachment`)
	A.Name = `NHBeastStagger`
	A.Parent = Root

	local Ring = Instance.new(`ParticleEmitter`)
	Ring.Texture = RING
	Ring.Color = ColorSequence.new(PALE, GOLD)
	Ring.LightEmission = 0.9
	Ring.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(1, 9) })
	Ring.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1), NumberSequenceKeypoint.new(1, 1) })
	Ring.Lifetime = NumberRange.new(0.45)
	Ring.Speed = NumberRange.new(0)
	Ring.Orientation = Enum.ParticleOrientation.VelocityPerpendicular
	Ring.EmissionDirection = Enum.NormalId.Top
	Ring.Rate = 0
	Ring.Parent = A
	Ring:Emit(2)

	local Sparks = Instance.new(`ParticleEmitter`)
	Sparks.Texture = SPARK
	Sparks.Color = ColorSequence.new(PALE, GOLD)
	Sparks.LightEmission = 1
	Sparks.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.6), NumberSequenceKeypoint.new(1, 0) })
	Sparks.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(1, 1) })
	Sparks.Lifetime = NumberRange.new(0.35, 0.6)
	Sparks.Speed = NumberRange.new(14, 24)
	Sparks.SpreadAngle = Vector2.new(180, 180)
	Sparks.Drag = 5
	Sparks.Rate = 0
	Sparks.Parent = A
	Sparks:Emit(34)

	local Light = Instance.new(`PointLight`)
	Light.Color = PALE
	Light.Range = 18
	Light.Brightness = 6
	Light.Parent = A
	TweenService:Create(Light, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Brightness = 0 }):Play()

	-- a small camera kick for the one who broke it (the Camera Shake setting scales it; 0 turns it off)
	if Paramaters.Attacker and Paramaters.Attacker == Players.LocalPlayer.Character then
		local Scale = tonumber(Players.LocalPlayer:GetAttribute(`NHShakeScale`)) or 1
		local Cam = workspace.CurrentCamera
		if Cam and Scale > 0 then
			task.spawn(function()
				for I = 1, 6 do
					local K = (1 - I / 6) * 0.35 * Scale
					Cam.CFrame *= CFrame.Angles(math.rad((math.random() - 0.5) * K), math.rad((math.random() - 0.5) * K), 0)
					task.wait()
				end
			end)
		end
	end

	Debris:AddItem(A, 1.5)
end
