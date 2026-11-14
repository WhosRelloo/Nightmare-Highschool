
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

	local TargetPos = Vector3.new(TargetRoot.Position.X, 0, TargetRoot.Position.Z)
	local UserPos = Vector3.new(UserRoot.Position.X, 0, UserRoot.Position.Z)

	local Params = bLua.Paramaters('Map')
	local WallCheck = workspace:Raycast(TargetRoot.Position, -TargetRoot.CFrame.LookVector * 4, Params)

	if WallCheck then return end

	local FlatLookVector = Vector3.new(TargetRoot.CFrame.LookVector.X, 0, TargetRoot.CFrame.LookVector.Z).Unit
	local DirectionToTarget = (TargetPos - UserPos).Unit

	local TargetBackOffset = TargetOffset or -5.5
	local UserForwardOffset = UserOffset or 5.5

	TargetAerial.Position = TargetRoot.Position + FlatLookVector * TargetBackOffset

	local FlatUserOffset = Vector3.new(DirectionToTarget.X, 0, DirectionToTarget.Z).Unit * UserForwardOffset
	UserAerial.Position = Vector3.new(UserRoot.Position.X, TargetAerial.Position.Y, UserRoot.Position.Z) + FlatUserOffset
end

return AirCombat
