--[[
	Charge (client effect): a heavy charging, one call per step (Assets.M2.Fist, combat concept 10, 2.11.0).
	Each step: a gold rim on the charger that brightens with the step (skipped under Reduce Flashing) and a rising chime.
	The full charge flares like the heavy's critical tell.
]]
local Debris = game:GetService(`Debris`)
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local TweenService = game:GetService(`TweenService`)

local EmitManager = require(ReplicatedStorage.Functions.EmitManager)

return function(Character: Model, Paramaters: { User: Model; Level: number })
	local User = Paramaters.User
	local Level = math.clamp(tonumber(Paramaters.Level) or 1, 1, 3)
	local Root = User and User:FindFirstChild(`HumanoidRootPart`)
	if not Root then return end

	local S = ReplicatedStorage.Assets.Sounds.Default:FindFirstChild(`Critical`)
	if S then
		local Ok, C = pcall(EmitManager.CloneSound, S, Root)
		if Ok and typeof(C) == `Instance` and C:IsA(`Sound`) then
			C.PlaybackSpeed = 0.8 + 0.2 * Level
			C.Volume *= 0.35 + 0.2 * Level
		end
	end

	if Level >= 3 then
		local Heavy = ReplicatedStorage.Assets.Effects.CombatFX:FindFirstChild(`Heavy`)
		if Heavy and Heavy:FindFirstChild(`Weld`) then
			local FX = Heavy:Clone()
			FX.Weld.Part1 = Root
			FX.Parent = workspace:FindFirstChild(`Visuals`) or workspace
			EmitManager.Emit(FX:GetDescendants(), true)
			Debris:AddItem(FX, 1)
		end
	end

	if Players.LocalPlayer:GetAttribute(`NHReducedFlash`) == true then return end
	local Hl = Instance.new(`Highlight`)
	Hl.FillColor = Color3.fromRGB(214, 176, 92) Hl.OutlineColor = Color3.fromRGB(236, 206, 128)
	Hl.FillTransparency = 1 - 0.12 * Level Hl.OutlineTransparency = 0.55 - 0.15 * Level
	Hl.DepthMode = Enum.HighlightDepthMode.Occluded
	Hl.Adornee = User Hl.Parent = workspace:FindFirstChild(`Visuals`) or workspace
	TweenService:Create(Hl, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { FillTransparency = 1; OutlineTransparency = 1 }):Play()
	Debris:AddItem(Hl, 0.4)
end
