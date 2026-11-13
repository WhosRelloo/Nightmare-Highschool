
---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

---| Modules |---

local UnPackets = require(ReplicatedStorage.Remotes.UnPackets)
local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)

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
	if Character and (Character:GetAttribute(`HasSportBall`) or Character:GetAttribute(`SportKeys`)) then return end -- sports: the ball's controls own this key
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
	-- (combat B10) flags: 1 = aerial, 2 = a new press, 4 = let go (0 = a hold-repeat). Holding charges the Fist heavy.
	pcall(function() require(script.Parent.LockOn.Core).Assist(Character) end) -- (combat A5)
	local Pressed = false
	if InAir then UnPackets.M2:Fire(3) Pressed = true end

	while Data.Held do
		if StateManager.HasState(Character, {`Stun`, `ParryStun`, `Ragdoll`, `Paralyzed`}) then
			break
		end

		if not Humanoid:GetAttribute(`Equip`) then
			break
		end

		UnPackets.M2:Fire(if Pressed then 0 else 2)
		Pressed = true
		task.wait(.05)

	end
	UnPackets.M2:Fire(4) -- (combat B10) let go: a charging heavy swings
end
