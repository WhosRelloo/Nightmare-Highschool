--!strict
--[[
	Tutorial (server). ServerScriptService.Services.World.Tutorial   (2.35.0, spec 2026-11-20 §4.2-§4.3)
	Who's in Wickfield, privately: the NHTutorial attribute (the client hides other tutorial players), a collision group
	that doesn't collide with itself, and the resume checkpoint saved in Progress.Origin.Checkpoint. This slice only
	enters and leaves; the run's beat order (doc 15 §5) comes with the full tutorial.
]]
local Players = game:GetService(`Players`)
local PhysicsService = game:GetService(`PhysicsService`)
local ServerScriptService = game:GetService(`ServerScriptService`)

local GROUP = `TutorialPlayers`
local Shared = {}
local Inside: { [Player]: RBXScriptConnection } = {}

local function progression() return require(ServerScriptService.Services.Player.Progression) end

local function setGroup(Character: Model?, Group: string)
	if not Character then return end
	for _, D in Character:GetDescendants() do
		if D:IsA(`BasePart`) then D.CollisionGroup = Group end
	end
end

function Shared.Checkpoint(Player: Player, CutId: string, Segment: string)
	progression().SetCheckpoint(Player, `{CutId}:{Segment}`)
end

function Shared.CheckpointOf(Player: Player): string?
	local P = progression().Get(Player)
	return P and P.Origin and P.Origin.Checkpoint or nil
end

function Shared.Enter(Player: Player): boolean
	if Inside[Player] then return true end
	Player:SetAttribute(`NHTutorial`, true)
	setGroup(Player.Character, GROUP)
	Inside[Player] = Player.CharacterAdded:Connect(function(C)
		C:WaitForChild(`HumanoidRootPart`, 5)
		setGroup(C, GROUP)
	end)
	return true
end

function Shared.Leave(Player: Player)
	local Cn = Inside[Player]
	if Cn then Cn:Disconnect() end
	Inside[Player] = nil
	Player:SetAttribute(`NHTutorial`, nil)
	-- (task 8 fix round 1) a walk-and-talk beat's crouch doesn't outlive Wickfield
	pcall(function() require(script.Parent.Cine).EndBeatCrouch(Player) end)
	setGroup(Player.Character, `Default`)
end

function Shared.OnStart()
	pcall(function() PhysicsService:RegisterCollisionGroup(GROUP) end)
	PhysicsService:CollisionGroupSetCollidable(GROUP, GROUP, false)
	Players.PlayerRemoving:Connect(function(P) Shared.Leave(P) end)
end

return Shared
