--[[
	Tag Assist (client effect): a study-group member answering the call (combat concept 21, 2.15.0; server:
	ServerStorage.Packages.TagAssist). A gold streak from where they were to where they land beside the target, a
	burst where they arrive, and a short warm flash.
]]
local Debris = game:GetService(`Debris`)
local TweenService = game:GetService(`TweenService`)

local GOLD = Color3.fromRGB(232, 172, 74)
local PALE = Color3.fromRGB(255, 236, 200)

return function(_Character: Model, Paramaters: { User: Model; From: Vector3?; To: Vector3? })
	local From, To = Paramaters.From, Paramaters.To
	if typeof(From) ~= `Vector3` or typeof(To) ~= `Vector3` then return end
	local Holder = Instance.new(`Part`)
	Holder.Name = `NHTagAssist`
	Holder.Anchored = true
	Holder.CanCollide, Holder.CanQuery, Holder.CanTouch = false, false, false
	Holder.Transparency = 1
	Holder.Size = Vector3.new(0.2, 0.2, 0.2)
	Holder.CFrame = CFrame.new(To)
	Holder.Parent = workspace:FindFirstChild(`Visuals`) or workspace
	local A0, A1 = Instance.new(`Attachment`), Instance.new(`Attachment`)
	A0.WorldPosition = From + Vector3.new(0, 0.5, 0)
	A1.WorldPosition = To + Vector3.new(0, 0.5, 0)
	A0.Parent, A1.Parent = Holder, Holder
	-- attachments keep their world position only once parented: set again
	A0.WorldPosition = From + Vector3.new(0, 0.5, 0)
	A1.WorldPosition = To + Vector3.new(0, 0.5, 0)
	local Beam = Instance.new(`Beam`)
	Beam.Attachment0, Beam.Attachment1 = A0, A1
	Beam.Color = ColorSequence.new(PALE, GOLD)
	Beam.LightEmission = 1
	Beam.FaceCamera = true
	Beam.Width0, Beam.Width1 = 0.2, 1.4
	Beam.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.9), NumberSequenceKeypoint.new(1, 0.1) })
	Beam.Parent = Holder
	local Sparks = Instance.new(`ParticleEmitter`)
	Sparks.Texture = `rbxasset://textures/particles/sparkles_main.dds`
	Sparks.Color = ColorSequence.new(PALE, GOLD)
	Sparks.LightEmission = 1
	Sparks.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.45), NumberSequenceKeypoint.new(1, 0) })
	Sparks.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(1, 1) })
	Sparks.Lifetime = NumberRange.new(0.3, 0.5)
	Sparks.Speed = NumberRange.new(8, 14)
	Sparks.SpreadAngle = Vector2.new(180, 180)
	Sparks.Rate = 0
	Sparks.Parent = A1
	Sparks:Emit(22)
	local Light = Instance.new(`PointLight`)
	Light.Color = GOLD
	Light.Range = 12
	Light.Brightness = 4
	Light.Parent = A1
	TweenService:Create(Light, TweenInfo.new(0.4, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Brightness = 0 }):Play()
	-- the streak thins out and fades
	local Fade = 0
	task.spawn(function()
		while Fade < 1 and Beam.Parent do
			Fade = math.min(1, Fade + 0.08)
			Beam.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.9 + 0.1 * Fade), NumberSequenceKeypoint.new(1, 0.1 + 0.9 * Fade) })
			Beam.Width1 = 1.4 * (1 - Fade)
			task.wait(0.03)
		end
	end)
	Debris:AddItem(Holder, 1)
end
