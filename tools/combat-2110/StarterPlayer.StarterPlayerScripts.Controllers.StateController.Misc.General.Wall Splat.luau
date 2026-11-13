--[[
	Wall Splat (client effect): someone knocked into a wall and pinned there (DamageLogic, combat concept 11, 2.11.0).
	Dust off the wall where they hit, a heavy thud, a camera jolt for the two people in the exchange (Camera Shake
	setting), and "WALL SPLAT" on the attacker's combo readout. No blood or gore.
]]
local Debris = game:GetService(`Debris`)
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local EmitManager = require(ReplicatedStorage.Functions.EmitManager)

local Shown = 0

return function(Character: Model, Paramaters: { User: Model; Attacker: Model?; Point: Vector3?; Normal: Vector3? })
	local User = Paramaters.User
	local Root = User and User:FindFirstChild(`HumanoidRootPart`)
	if not Root then return end

	local Smoke = ReplicatedStorage.Assets.Effects.CombatFX:FindFirstChild(`DownSmoke`)
	if Smoke and typeof(Paramaters.Point) == `Vector3` then
		local FX = Smoke:Clone()
		for _, J in FX:GetDescendants() do if J:IsA(`JointInstance`) or J:IsA(`WeldConstraint`) then J:Destroy() end end
		FX.Anchored = true FX.CanCollide = false FX.CanQuery = false
		local N = if typeof(Paramaters.Normal) == `Vector3` then Paramaters.Normal else Vector3.zAxis
		FX.CFrame = CFrame.lookAt(Paramaters.Point + N * 0.3, Paramaters.Point + N * 2)
		FX.Parent = workspace:FindFirstChild(`Visuals`) or workspace
		EmitManager.Emit(FX:GetDescendants(), true)
		Debris:AddItem(FX, 2)
	end

	local Blunt = ReplicatedStorage.Assets.Sounds.Hit:FindFirstChild(`Blunt`)
	local List = Blunt and Blunt:GetChildren() or {}
	if #List > 0 then
		local Ok, C = pcall(EmitManager.CloneSound, List[math.random(#List)], Root)
		if Ok and typeof(C) == `Instance` and C:IsA(`Sound`) then C.PlaybackSpeed = 0.8 end
	end

	local Me = Players.LocalPlayer.Character
	if Me and (Me == User or Me == Paramaters.Attacker) then EmitManager.ShakeCamera(4, 12, 0, 0.35) end

	-- the readout (made by StateController Damage Type on your first combo; nothing to do if you haven't had one)
	if Me and Me == Paramaters.Attacker then
		local G = Players.LocalPlayer.PlayerGui:FindFirstChild(`NHComboCounter`)
		local Tag = G and G:FindFirstChild(`Counter`, true)
		if Tag and Tag:IsA(`TextLabel`) then
			Shown += 1
			local Mine = Shown
			Tag.Text = `WALL SPLAT`
			Tag.TextColor3 = require(ReplicatedStorage.UI.Components).Theme.Colors.Gold
			Tag.Visible = true
			Tag.TextTransparency = 0
			task.delay(1, function() if Shown == Mine then Tag.TextTransparency = 1 end end)
		end
	end
end
