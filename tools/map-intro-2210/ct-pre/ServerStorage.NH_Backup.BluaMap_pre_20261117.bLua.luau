
local bLua = {}

bLua.spawn = function(callback, ...)
	if not callback then return end
	coroutine.resume(coroutine.create(callback), ...)
end

bLua.delay = function(duration, callback, ...)
	if not duration or typeof(duration) ~= 'number' then return end
	coroutine.resume(coroutine.create(function(...)
		task.wait(duration)
		callback(...)
	end), ...)
	return duration
end

bLua.lerp = function(original, target, delta) -- Original, Change
	return original + (target - original) * delta
end

bLua.CFrame = {
	Build = function(position, lookVector)
		return CFrame.new(position, position+lookVector)
	end,

	UpVector = function(position, upVector, relativeLookVector)
		upVector = upVector.unit

		local rightVector = CFrame.new(position, position+upVector).RightVector
		local defaultCFrame = CFrame.lookAt(position, position+rightVector, upVector)
		
		local dotForward = relativeLookVector:Dot(defaultCFrame.LookVector)
		local dotRight = relativeLookVector:Dot(defaultCFrame.RightVector)
		
		local LookVector = defaultCFrame.LookVector
		if dotForward > 0.5 then
			LookVector = defaultCFrame.LookVector
		elseif dotForward < -0.5 then
			LookVector = -defaultCFrame.LookVector
		elseif dotRight > 0.5 then
			LookVector = defaultCFrame.RightVector
		elseif dotRight < -0.5 then
			LookVector = -defaultCFrame.RightVector
		end
		
		return CFrame.lookAt(position, position+LookVector, upVector)
	end
}

bLua.Vector3 = {
	AngledLookVector = function(lookVector, angles)
		return (CFrame.new(Vector3.zero, Vector3.zero+lookVector)*angles).LookVector
	end,

	Clamp = function(vector3, min, max)
		return Vector3.new(math.clamp(vector3.X,min.X,max.X),math.clamp(vector3.Y,min.Y,max.Y),math.clamp(vector3.Z,min.Z,max.Z))
	end,

	Replace = function(vector3, x,y,z)
		return Vector3.new(x or vector3.X, y or vector3.Y, z or vector3.Z)
	end,
}

bLua.MergeTable = function(a, b)
	local new = {}
	for _,v in a do
		table.insert(new, v)
	end
	for _,v in b do
		table.insert(new, v)
	end
	return new
end

bLua.Unit = function(cframe: CFrame, faceDirection, character)
	if faceDirection == 'LeftVector' then
		return -cframe.RightVector
	elseif faceDirection == 'BackVector' then
		return -cframe.LookVector
	elseif faceDirection == 'MoveVector' and character and character:FindFirstChildOfClass('Humanoid') then
		local hum = character:FindFirstChildOfClass('Humanoid')
		return hum.MoveDirection
	elseif faceDirection == 'CameraVector' then
		return workspace.CurrentCamera.CFrame.LookVector
	else
		return cframe[faceDirection]
	end
end

bLua.ComboCounter = function(Combo, Tick, MaxCombo, timeTillReset)
	if not Tick or not Combo then
		Tick = tick()
		Combo = 0
	end
	local timeDifference = tick() - Tick
	local newCombo = Combo + 1

	if timeDifference > (timeTillReset or 1.5) and Tick ~= 0 then
		newCombo = 1 
	end
	
	if newCombo > (MaxCombo or 5) then
		newCombo = 1

	end

	return newCombo
end

bLua.Paramaters = function(preset)
	local params = RaycastParams.new()
	preset = string.lower(preset)

	if preset == 'map' then
		params.FilterType = Enum.RaycastFilterType.Include
		params.IgnoreWater = true
		params.RespectCanCollide = true
		params.FilterDescendantsInstances = {workspace.Map}
	elseif preset == 'live' then
		params.FilterType = Enum.RaycastFilterType.Include
		params.RespectCanCollide = false
		params.FilterDescendantsInstances = {workspace.Live}
	end

	return params
end



function bLua:GetPlayer(Character: Model)
	local player = Character
	if Character and Character:IsA('Model') then
		player = game:GetService('Players'):GetPlayerFromCharacter(player)
	end
	return player
end

bLua.Math = {
	Scale = function(input, inputMax, outputMax)
		local preCalc = math.max(inputMax.X, math.min(inputMax.Y, input))
		return outputMax.X + ((outputMax.Y - outputMax.X) * ((preCalc - inputMax.X) / (inputMax.Y - inputMax.X)))
	end,
}

return bLua
