
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

	local InAir = Humanoid.FloorMaterial == Enum.Material.Air
	local InAirCombat = TagService:HasTag(Character, `InAir`)
	local CtrlHeld = UserInputService:IsKeyDown(Enum.KeyCode.LeftControl) or Keybinds.VirtualDown(`LeftControl`) -- touch Crouch button
		or Players.LocalPlayer:GetAttribute(`NHPadUppercut`) == true -- (1.33.1) a controller holding RS (Gui.GamepadControls)

	if CtrlHeld and not InAir and not StateManager.HasState(Character, {`Attacking`}) and not InAirCombat then
		UnPackets.Uppercut:Fire()
		return
	end

	-- (combat audit) the packet is a flags byte: 1 = aerial, 2 = a new press (the server buffers only presses;
	-- the hold-repeats below send 0)
	local Pressed = false
	-- Only allow aerial M1 if in air but NOT in air combat
	if InAir and not InAirCombat then 
		UnPackets.M1:Fire(3)
		Pressed = true
	end

	Humanoid:SetStateEnabled(Enum.HumanoidStateType.Jumping, false)

	while Data.Held do
		if StateManager.HasState(Character, {`Stun`, `ParryStun`, `Ragdoll`, `Paralyzed`}) then
			break
		end

		if not Humanoid:GetAttribute(`Equip`) then
			break
		end

		UnPackets.M1:Fire(if Pressed then 0 else 2)
		Pressed = true
		task.wait(.05)

	end

	Humanoid:SetStateEnabled(Enum.HumanoidStateType.Jumping, true)
end
