
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
	if Character and Character:GetAttribute(`HasSportBall`) then return end -- sports: the ball's controls own this key
	if not Character then
		return
	end

	local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	if not Humanoid then return end

	if StateManager.HasState(Character, {`Ragdoll`, `Paralyzed`}) then
		return
	end

	if not Humanoid:GetAttribute(`Equip`) then
		return
	end

	-- (2.13.0) the local player's own "block is held" flag (client-set, never replicated): a click while it's held is
	-- the clinch, so InputController.Combat.M1.Predict doesn't start a punch for it
	Players.LocalPlayer:SetAttribute(`NHBlockHeld`, InputState == `Began`)
	if InputState == `Began` then
		UnPackets.Block:Fire(`Activate`)

	else
		UnPackets.Block:Fire(`Release`)

	end
end
