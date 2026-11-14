--[[
	NPCActions. The moves a combat NPC makes (Services.AI.AI). 1.23: nothing here waits inside the AI update any more
	(a parry or guard that had to cancel a swing first used to pause every NPC's update for 50 ms, and two overlapping
	parries cancelled each other); the follow-up runs a moment later instead. Sprint speed comes from the tier.
]]
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local TrackService = require(ReplicatedStorage.Packages.TrackService)
local ActionManager = require(ServerScriptService.Services.Player.ActionManager)

export type NPC = {
	Character: Model;
	ActionManager: any;
	LastBlock: number;
	LastDodge: number;
	LastFeint: number;
	LastUppercut: number;
	LastAttack: number;
	LastM2: number;
	IsBlocking: boolean;
}

local Actions = {}
local function NPCBehaviors() return require(script.Parent.NPCBehaviors) end

function Actions.EquipWeapon(Character: Model, WeaponName: string)
	task.spawn(Actions.EquipNow, Character, WeaponName) -- it waits for the rig's accessory; never inside the AI update
end

function Actions.EquipNow(Character: Model, WeaponName: string)
	local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	if not Humanoid then
		return
	end

	local WeaponsConfig = require(ReplicatedStorage.Config.Weapons)
	local Config = WeaponsConfig[WeaponName]

	if not Config then
		return
	end

	Humanoid:SetAttribute(`Equip`, true)

	if WeaponName == `Fist` then
		return
	end

	if not Config.Model or not Config.Model.Handle then
		return
	end

	local Accessory = Character:WaitForChild(`Accessory`, 2)
	if not Accessory then
		return
	end

	local Weapons = Accessory:WaitForChild(`Weapons`, 2)
	if not Weapons then
		return
	end

	for _, Weapon: BasePart in Weapons:GetChildren() do
		Weapon:Destroy()
	end

	local WeaponModel = Config.Model.Handle:Clone()
	WeaponModel.Parent = Weapons

	if Config.Model.Grip then
		local GripLocation = Character:FindFirstChild(Config.Model.Grip) :: BasePart
		if GripLocation then
			local Handle = WeaponModel:FindFirstChild(`Handle`)
			if Handle and Handle:IsA(`Motor6D`) then
				Handle.Part1 = GripLocation
			end
		end
	end
end

function Actions.TapParry(npc: NPC): boolean
	if StateManager.HasState(npc.Character, {`Ragdoll`, `Paralyzed`}) then
		return false
	end

	local CurrentTime = tick()
	if CurrentTime - npc.LastBlock < 0.1 then
		return false
	end
	npc.LastBlock = CurrentTime

	local function press()
		local AM = npc.ActionManager
		if not AM or not npc.Character then return end
		if AM:Activate(`Block`) then
			npc.ParriedAt = os.clock() -- for the punish check (NPCController)
			npc.ParryCounted = false
			NPCBehaviors().Stat(npc, `Parry`)
			task.delay(0.25, function()
				if npc.ActionManager and npc.ActionManager.Action == `Block` then
					npc.ActionManager:Release(`Block`)
				end
			end)
		end
	end
	if npc.ActionManager.Action then
		TrackService.StopTaggedTracks(npc.Character, `Attack`)
		npc.ActionManager:Cancel(npc.ActionManager.Action)
		task.delay(0.05, press)
	else
		press()
	end
	return true
end

function Actions.HoldBlock(npc: NPC): boolean
	if npc.IsBlocking then return true end
	if npc.ActionManager.Action == `Block` then return true end

	if StateManager.HasState(npc.Character, {`Ragdoll`, `Paralyzed`}) then
		return false
	end

	local CurrentTime = tick()
	if CurrentTime - npc.LastBlock < 0.5 then
		return false
	end
	npc.LastBlock = CurrentTime

	local function raise()
		local AM = npc.ActionManager
		if not AM or not npc.Character then return end
		if AM:Activate(`Block`) then
			npc.IsBlocking = true
			NPCBehaviors().Stat(npc, `Guard`)
			task.delay(1.2, function()
				if npc.IsBlocking and npc.ActionManager and npc.ActionManager.Action == `Block` then
					Actions.StopBlock(npc)
				end
			end)
		end
	end
	if npc.ActionManager.Action then
		TrackService.StopTaggedTracks(npc.Character, `Attack`)
		npc.ActionManager:Cancel(npc.ActionManager.Action)
		task.delay(0.05, raise)
	else
		raise()
	end
	return true
end

function Actions.StopBlock(npc: NPC)
	if npc.ActionManager and npc.ActionManager.Action == `Block` then
		npc.ActionManager:Release(`Block`)
	end
	npc.IsBlocking = false
end

function Actions.Dodge(npc: NPC): boolean
	local CurrentTime = tick()
	if CurrentTime - npc.LastDodge < 1.8 then
		return false
	end

	if StateManager.HasState(npc.Character, {`Stun`, `ParryStun`, `Ragdoll`, `Paralyzed`}) then
		return false
	end

	if npc.ActionManager.Action then
		TrackService.StopTaggedTracks(npc.Character, `Attack`)
		npc.ActionManager:Cancel(npc.ActionManager.Action)
	end

	local DodgeDirections = {`BackVector`, `LeftVector`, `RightVector`}
	local Direction = DodgeDirections[math.random(1, #DodgeDirections)]

	local Success = npc.ActionManager:Activate(`Dodge`, Direction)

	if Success then
		npc.LastDodge = CurrentTime
		NPCBehaviors().Stat(npc, `Dodge`)
		return true
	end

	return false
end

function Actions.Evasive(npc: NPC): boolean
	local CurrentTime = tick()
	if CurrentTime - npc.LastDodge < 3.0 then
		return false
	end

	if npc.ActionManager.Action then
		TrackService.StopTaggedTracks(npc.Character, `Attack`)
		npc.ActionManager:Cancel(npc.ActionManager.Action)
	end

	local EvasiveDirections = {`BackVector`, `LeftVector`, `RightVector`}
	local Direction = EvasiveDirections[math.random(1, #EvasiveDirections)]

	local Success = npc.ActionManager:Activate(`Evasive`, Direction)

	if Success then
		npc.LastDodge = CurrentTime
		NPCBehaviors().Stat(npc, `Evasive`)
		return true
	end

	return false
end

function Actions.Feint(npc: NPC): boolean
	local CurrentTime = tick()

	if npc.ActionManager.Cooldowns[`Feint`] then
		return false
	end

	if npc.ActionManager.Action ~= `M1` then
		return false
	end

	ActionManager.Feint(npc.Character)
	npc.LastFeint = CurrentTime

	return true
end

function Actions.TrySlide(npc: NPC): boolean
	if not npc.Target then return false end

	if StateManager.HasState(npc.Character, {`Stun`, `ParryStun`, `Ragdoll`, `Paralyzed`}) then
		return false
	end

	local RootPart = npc.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart
	if not RootPart then return false end

	local TargetRoot = npc.Target:FindFirstChild(`HumanoidRootPart`) :: BasePart
	if not TargetRoot then return false end

	local Distance = (RootPart.Position - TargetRoot.Position).Magnitude

	local CurrentTime = tick()
	if CurrentTime - npc.LastSlide < 1.8 then
		return false
	end

	if Distance > 10 and Distance < 22 and NPCBehaviors().EverySecond(npc, `Slide`) then
		if npc.ActionManager.Action then
			TrackService.StopTaggedTracks(npc.Character, `Attack`)
			npc.ActionManager:Cancel(npc.ActionManager.Action)
		end

		local Success = npc.ActionManager:Activate(`Slide`)
		if Success then
			npc.LastSlide = CurrentTime
			return true
		end
	end

	return false
end

function Actions.Uppercut(npc: NPC): boolean
	local CurrentTime = tick()

	if StateManager.HasState(npc.Character, {`Stun`, `ParryStun`, `Ragdoll`, `Paralyzed`, `Attacking`, `Uppercutting`}) then
		return false
	end

	if npc.ActionManager.Action then return false end -- only from neutral (it used to cancel and wait inside the update)

	local Success = npc.ActionManager:Activate(`Uppercut`)

	if Success then
		npc.LastUppercut = CurrentTime
		npc.LastAttack = CurrentTime
		return true
	end

	return false
end

function Actions.ActivateSprint(npc: NPC): boolean
	local Humanoid = npc.Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	if not Humanoid then return false end

	if Humanoid:GetAttribute(`Sprint`) then
		return true
	end

	npc._sprintStartTime = tick()

	Humanoid.WalkSpeed = (npc.Config and npc.Config.SprintSpeed) or 22
	Humanoid:SetAttribute(`Sprint`, true)

	return true
end

function Actions.DeactivateSprint(npc: NPC)
	local Humanoid = npc.Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	if not Humanoid then return end

	if not Humanoid:GetAttribute(`Sprint`) then
		return
	end

	local BaseSpeed = npc.Config.PatrolSpeed or 12
	if npc.State == `Chasing` or npc.State == `Attacking` then
		BaseSpeed = npc.Config.ChaseSpeed or 16
	end

	Humanoid.WalkSpeed = BaseSpeed
	Humanoid:SetAttribute(`Sprint`, false)

	npc._sprintStartTime = 0

end

function Actions.UpdateSprint(npc: NPC)
	local Humanoid = npc.Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	if not Humanoid or not Humanoid:GetAttribute(`Sprint`) then return end


end

return Actions

