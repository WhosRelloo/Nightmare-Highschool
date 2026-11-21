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

local Config = require(game:GetService(`ReplicatedStorage`).Config.Cine)
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

-- (task 12) resume: a player who enters Wickfield or respawns in it with a checkpoint ("<Cut>:<Segment>") is put on that segment's
-- mark in the cut's set (a mark named like the segment, else <Segment>Zone, else Start), 3 studs up like Cine's own placements.
-- Returns the mark's name when it placed the player. The two-line version the plan sketched, plus the segment-to-mark lookup.
function Shared.Resume(Player: Player): string?
	local Cp = Shared.CheckpointOf(Player)
	local CutId, Segment
	if Cp then CutId, Segment = Cp:match(`^([%w_]+):([%w_]+)$`) end
	local Cut = CutId and Config.Cuts[CutId]
	local Sets = workspace:FindFirstChild(`NHCineSets`)
	local Set = Cut and Cut.Set and Sets and Sets:FindFirstChild(Cut.Set)
	if not (Set and Segment) then return nil end
	local Mark = Set:FindFirstChild(Segment) or Set:FindFirstChild(Segment .. `Zone`) or Set:FindFirstChild(`Start`)
	local Char = Player.Character
	if not (Mark and Mark:IsA(`BasePart`) and Char and Char:FindFirstChild(`HumanoidRootPart`)) then return nil end
	Char:PivotTo(Mark.CFrame * CFrame.new(0, 3, 0))
	return Mark.Name
end

function Shared.Enter(Player: Player): boolean
	if Inside[Player] then return true end
	Player:SetAttribute(`NHTutorial`, true)
	setGroup(Player.Character, GROUP)
	Shared.Resume(Player)
	Inside[Player] = Player.CharacterAdded:Connect(function(C)
		C:WaitForChild(`HumanoidRootPart`, 5)
		setGroup(C, GROUP)
		Shared.Resume(Player)
	end)
	return true
end

-- Why: nil for a deliberate leave (a running cut ends "Aborted"), "Left" when the player is disconnecting (the cut ends
-- "Left": not marked Seen, nothing sent to a client that is gone)
function Shared.Leave(Player: Player, Why: string?)
	local Cn = Inside[Player]
	if Cn then Cn:Disconnect() end
	Inside[Player] = nil
	-- (task 9, spec §4.3) leaving Wickfield is the safety net for an open-ended beat: end any running cine session first,
	-- while the player is still marked as in Wickfield
	pcall(function() require(script.Parent.Cine).EndFor(Player, if Why == `Left` then `Left` else `Aborted`) end)
	Player:SetAttribute(`NHTutorial`, nil)
	-- (task 8 fix round 1) a walk-and-talk beat's crouch doesn't outlive Wickfield
	pcall(function() require(script.Parent.Cine).EndBeatCrouch(Player) end)
	setGroup(Player.Character, `Default`)
end

function Shared.OnStart()
	pcall(function() PhysicsService:RegisterCollisionGroup(GROUP) end)
	PhysicsService:CollisionGroupSetCollidable(GROUP, GROUP, false)
	Players.PlayerRemoving:Connect(function(P) Shared.Leave(P, `Left`) end)
end

return Shared
