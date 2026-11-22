
---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

---| Modules |---

local UnPackets = require(ReplicatedStorage.Remotes.UnPackets)

---| Type Annotation |---

type		InputState = 'Began' | 'Ended'
type 		InputData = {
	Input: { string } | string;
	Held: boolean;
	
	InputType: InputState;
	Connections: RBXScriptConnection;
	
	LastTimePressed: number;
}

---| Bind |---

return function (Character: Model, InputState: InputState, Action: string, Data: InputData)
	if not Character then
		return
	end
	
	local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	if not Humanoid then return end
	
	if InputState ~= `Began` then
		UnPackets.Sprint:Fire(`Release`)
		--return
	end
	
	-- Hold-to-sprint (Left Shift by default). Only a W binding keeps the old double-tap.
	local Key = if typeof(Data.Input) == `table` then Data.Input[1] else Data.Input
	if tostring(Key) ~= `W` then
		if InputState == `Began` then UnPackets.Sprint:Fire(`Activate`) end
		return
	end

	local CurrentTime = tick()
	local LastTimePressed = Data.LastTimePressed
	
	if LastTimePressed and CurrentTime - LastTimePressed <= 0.2 then
		if InputState ~= `Ended` then UnPackets.Sprint:Fire(`Activate`) end
			
		--until not Data.Held
		--UnPackets.Sprint:Fire(`Release`)
	end
	
	Data.LastTimePressed = CurrentTime
end
