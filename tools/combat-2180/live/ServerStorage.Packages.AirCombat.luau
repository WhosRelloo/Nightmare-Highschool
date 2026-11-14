
---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)

---| Modules |---

local TagService = require(ReplicatedStorage.Packages.Core.TagService)
local BodyPositionModule = require(ReplicatedStorage.Functions.BP)
local LinearVelocity = require(ReplicatedStorage.Functions.LinearVelocity)
local bLua = require(ReplicatedStorage.Packages.bLua)
local Packets = require(ReplicatedStorage.Remotes.Packets)

local AirCombat = {}

local function getCeilingHeight(Root: BasePart)
	local Params = bLua.Paramaters('Map')
	local Result = workspace:Raycast(Root.Position, Root.CFrame.upVector * 200, Params)

	local Height = 12
	if Result and Result.Position then
		local Distance = (Result.Position - Root.Position).Magnitude
		if Distance < 25 then
			Height = math.min(Height, Distance - 5)
		end
	end

	return Height
end

local function createAerialPosition(Character: Model, Position: Vector3)
	local BodyPos = BodyPositionModule.new(Character, `AerialPosition`)
	BodyPos.Position = Position
	BodyPos.MaxForce = Vector3.new(1, 1, 1)
	BodyPos.P = 2e4
	BodyPos.Timeout = 3
	BodyPos.LastChanged = os.clock()
	BodyPos:SendToClients({ Remove = 30 })

	return BodyPos
end

function AirCombat.Launch(User: Model, Target: Model)
	local UserRoot = User:FindFirstChild("HumanoidRootPart")
	local TargetRoot = Target:FindFirstChild("HumanoidRootPart")

	if not UserRoot then return end
	if not TargetRoot then return end

	AirCombat.Stop(User, Target)

	BodyPositionModule.Register(User)
	BodyPositionModule.Register(Target)

	TagService:AddTag(User, `InAir`, 3)
	TagService:AddTag(Target, `InAir`, 3)

	AirCombat.ResetHits(Target)

	local AirHeight = getCeilingHeight(UserRoot)
	local UserCFrame = UserRoot.CFrame * CFrame.new(0, AirHeight, 0)
	local UserPosition = UserCFrame.Position
	local TargetPosition = (UserCFrame * CFrame.new(0, 0, -5.5)).Position

	createAerialPosition(User, UserPosition)
	createAerialPosition(Target, TargetPosition)

	TargetRoot.CFrame = CFrame.lookAt(
		TargetRoot.Position,
		Vector3.new(UserRoot.Position.X, TargetRoot.Position.Y, UserRoot.Position.Z)
	)

	task.wait()

	bLua.spawn(AirCombat.StartTracking, User, false)
	bLua.spawn(AirCombat.StartTracking, Target, false)
end

function AirCombat.IsActive(User: Model, Target: Model): boolean
	return TagService:HasTag(User, `InAir`) and TagService:HasTag(Target, `InAir`)
end

function AirCombat.GetHits(Target: Model): number
	return Target:GetAttribute(`AirHitCount`) or 0
end

function AirCombat.AddHit(Target: Model): number
	local Current = AirCombat.GetHits(Target)
	local New = Current + 1
	Target:SetAttribute(`AirHitCount`, New)
	return New
end

function AirCombat.ResetHits(Target: Model)
	Target:SetAttribute(`AirHitCount`, 0)
end

function AirCombat.CheckFinisher(Target: Model): boolean
	return AirCombat.GetHits(Target) >= 3
end

function AirCombat.Stop(User: Model, Target: Model)
	TagService.RemoveAllTagsFromInstance(User, `InAir`)
	TagService.RemoveAllTagsFromInstance(Target, `InAir`)
	AirCombat.ResetHits(Target)

	BodyPositionModule.StopTaggedBodyMovers(User, `AerialPosition`)
	BodyPositionModule.StopTaggedBodyMovers(Target, `AerialPosition`)
end

function AirCombat.StopCharacter(Character: Model)
	if not Character then return end

	TagService.RemoveAllTagsFromInstance(Character, `InAir`)
	AirCombat.ResetHits(Character)
	BodyPositionModule.StopTaggedBodyMovers(Character, `AerialPosition`)
end

function AirCombat.StartTracking(Character: Model, IgnoreRagdollCheck: boolean?)
	local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`)
	if not Humanoid then return end

	local RootPart = Humanoid.RootPart
	if not RootPart then return end

	local Player = RootPart:GetNetworkOwner()

	task.wait(0.3)

	if not Player then
		local ClosestPlayer = { Player = nil; Distance = math.huge }

		for _, PotentialPlayer in Players:GetPlayers() do
			local PotentialCharacter = PotentialPlayer.Character
			if not PotentialCharacter then continue end

			local PotentialRoot = PotentialCharacter:FindFirstChild(`HumanoidRootPart`)
			if not PotentialRoot then continue end

			local Distance = (PotentialRoot.Position - RootPart.Position).Magnitude

			if Distance < ClosestPlayer.Distance then
				ClosestPlayer.Player = PotentialPlayer
				ClosestPlayer.Distance = Distance
			end
		end

		Player = ClosestPlayer.Player
	end

	if not Player then return end


	pcall(function()
		Packets.AirCombat:FireClient(Player, {
			Character = Character;
			IgnoreRagdoll = IgnoreRagdollCheck or false;
		})
	end)


end

-- (2.18.0) After an air hit, push the target a little further along the line of the attack and bring the attacker
-- in behind it, inside fist reach, both facing each other. It used to push the target back along ITS OWN facing and
-- move the attacker 5.5 studs toward where the target had been: after the first air hit the target ended up about 5
-- studs to the side, air hits 2-4 whiffed, and the 3-hit downslam finisher (the air crit) never came.
local AIR_PUSH = 2.5 -- studs the target is knocked along the attack each air hit
local AIR_GAP = 3.6  -- studs between the two after it (M1 reach is about 5.8: Offset 2.8 + half the 6-stud box)

function AirCombat.Reposition(User: Model, Target: Model, TargetOffset: number?, UserOffset: number?)
	local TargetRoot = Target:FindFirstChild(`HumanoidRootPart`)
	local UserRoot = User:FindFirstChild(`HumanoidRootPart`)

	if not TargetRoot or not UserRoot then return end

	if not TagService:HasTag(User, `InAir`) or not TagService:HasTag(Target, `InAir`) then
		return
	end

	local TargetAerial = BodyPositionModule.GetByTag(Target, `AerialPosition`)
	local UserAerial = BodyPositionModule.GetByTag(User, `AerialPosition`)

	if not TargetAerial or not UserAerial then
		return
	end

	TargetAerial.LastChanged = os.clock()
	TargetAerial.Timeout = 2.5

	UserAerial.LastChanged = os.clock()
	UserAerial.Timeout = 2.5

	TagService:AddTag(User, `InAir`, 3)
	TagService:AddTag(Target, `InAir`, 3)

	-- the line of the attack, flat
	local Dir = (TargetRoot.Position - UserRoot.Position) * Vector3.new(1, 0, 1)
	if Dir.Magnitude < 0.5 then Dir = UserRoot.CFrame.LookVector * Vector3.new(1, 0, 1) end
	if Dir.Magnitude < 1e-3 then return end
	Dir = Dir.Unit

	-- a wall behind the target shortens the push (never through it)
	local Push = TargetOffset or AIR_PUSH
	local Params = bLua.Paramaters('Map')
	local Wall = workspace:Raycast(TargetRoot.Position, Dir * (Push + 2), Params)
	if Wall then Push = math.max(0, (Wall.Position - TargetRoot.Position).Magnitude - 2) end

	local Y = TargetAerial.Position.Y
	local T = TargetRoot.Position + Dir * Push
	local U = T - Dir * (UserOffset or AIR_GAP)
	TargetAerial.Position = Vector3.new(T.X, Y, T.Z)
	UserAerial.Position = Vector3.new(U.X, Y, U.Z)

	-- face each other, so the next swing (and the target's reaction) points the right way
	TargetRoot.CFrame = CFrame.lookAt(TargetRoot.Position, TargetRoot.Position - Dir)
	UserRoot.CFrame = CFrame.lookAt(UserRoot.Position, UserRoot.Position + Dir)
end

return AirCombat
