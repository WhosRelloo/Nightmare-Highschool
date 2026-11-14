
---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local UserInputService = game:GetService(`UserInputService`)

---| Modules |---

local UnPackets = require(ReplicatedStorage.Remotes.UnPackets)
local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local TagService = require(ReplicatedStorage.Packages.Core.TagService)
local Keybinds = require(ReplicatedStorage.Packages.Bind.Keybinds)

---| Type Annotation |---

type		InputState = 'Began' | 'Ended'
type 		InputData = {
	Input: { string } | string;
	Held: boolean;

	InputType: InputState;
	Connections: RBXScriptConnection;
}

---| Bind |---

return function (Character: Model, InputState: InputState, Action: string, Data: InputData)
	if Character and (Character:GetAttribute(`HasSportBall`) or Character:GetAttribute(`InSport`)) then return end -- sports: click shoots or steals in a game
	if not Character then
		return
	end

	local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	if not Humanoid then return end

	if StateManager.HasState(Character, {`Stun`, `ParryStun`, `Ragdoll`, `Paralyzed`}) then
		return
	end

	if not Humanoid:GetAttribute(`Equip`) then
		return
	end

	pcall(function() require(script.Parent.LockOn.Core).Assist(Character) end) -- (combat A5) face the target / aim assist
	local InAir = Humanoid.FloorMaterial == Enum.Material.Air
	local InAirCombat = TagService:HasTag(Character, `InAir`)
	local CtrlHeld = UserInputService:IsKeyDown(Enum.KeyCode.LeftControl) or Keybinds.VirtualDown(`LeftControl`) -- touch Crouch button
		or Players.LocalPlayer:GetAttribute(`NHPadUppercut`) == true -- (1.33.1) a controller holding RS (Gui.GamepadControls)

	if CtrlHeld and not InAir and not StateManager.HasState(Character, {`Attacking`}) and not InAirCombat then
		UnPackets.Uppercut:Fire()
		return
	end

	-- (combat audit) the packet is a flags byte: 1 = aerial, 2 = a new press (the server buffers only presses;
	-- the hold-repeats below send 0). (2.13.0, combat concept 12) + index * 8: the hit of the string this client
	-- already started playing (script.Predict); 0 = not predicted.
	local Pressed = false
	-- Only allow aerial M1 if in air but NOT in air combat
	if InAir and not InAirCombat then 
		UnPackets.M1:Fire(3)
		Pressed = true
	end

	-- (2.18.0) in air combat, turn to face the one you launched before each swing: a mouse player has no aim assist up
	-- there (LockOn.Core.Assist only turns to a locked target), so air hits 2-4 used to swing at empty air
	local function FaceAirTarget()
		if not TagService:HasTag(Character, `InAir`) then return end
		local Root = Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
		local Live = workspace:FindFirstChild(`Live`)
		if not (Root and Live) then return end
		local Best, BestD = nil, 14
		for _, M in Live:GetChildren() do
			local R = M ~= Character and M:FindFirstChild(`HumanoidRootPart`) :: BasePart?
			if R and TagService:HasTag(M, `InAir`) then
				local D = (R.Position - Root.Position).Magnitude
				if D < BestD then Best, BestD = R, D end
			end
		end
		if Best then
			Root.CFrame = CFrame.lookAt(Root.Position, Vector3.new(Best.Position.X, Root.Position.Y, Best.Position.Z))
		end
	end

	Humanoid:SetStateEnabled(Enum.HumanoidStateType.Jumping, false)

	while Data.Held do
		if StateManager.HasState(Character, {`Stun`, `ParryStun`, `Ragdoll`, `Paralyzed`}) then
			break
		end

		if not Humanoid:GetAttribute(`Equip`) then
			break
		end

		pcall(FaceAirTarget) -- (2.18.0)
		local Flags = if Pressed then 0 else 2
		if not Pressed and not InAir then
			local Ok, Index = pcall(require(script.Predict).Try, Character, Humanoid)
			if Ok and Index then Flags += Index * 8 end
		end
		UnPackets.M1:Fire(Flags)
		Pressed = true
		task.wait(.05)

	end

	Humanoid:SetStateEnabled(Enum.HumanoidStateType.Jumping, true)
end
