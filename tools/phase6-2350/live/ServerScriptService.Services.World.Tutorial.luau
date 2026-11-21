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
local Late: { [Player]: RBXScriptConnection } = {} -- (final fix round) parts added to the character after Enter (tools, accessories)

local Config = require(game:GetService(`ReplicatedStorage`).Config.Cine)
local function progression() return require(ServerScriptService.Services.Player.Progression) end

local function setGroup(Character: Model?, Group: string)
	if not Character then return end
	for _, D in Character:GetDescendants() do
		if D:IsA(`BasePart`) then D.CollisionGroup = Group end
	end
end

-- (final fix round) a part that joins the character later (a Tool's handle, an accessory) is put in the tutorial group too; dropped on
-- Leave and whenever the character changes
local function watchLate(Player: Player, Character: Model?)
	if Late[Player] then Late[Player]:Disconnect() Late[Player] = nil end
	if not Character then return end
	Late[Player] = Character.DescendantAdded:Connect(function(D)
		if D:IsA(`BasePart`) then D.CollisionGroup = GROUP end
	end)
end

function Shared.Checkpoint(Player: Player, CutId: string, Segment: string)
	progression().SetCheckpoint(Player, `{CutId}:{Segment}`)
end

function Shared.CheckpointOf(Player: Player): string?
	local P = progression().Get(Player)
	return P and P.Origin and P.Origin.Checkpoint or nil
end

-- (task 12, fix round 1) resume: a player who enters Wickfield or respawns in it with a checkpoint ("<Cut>:<Segment>") is put on a mark
-- of the cut's set, 3 studs up like Cine's own placements. The cut declares the map (Config.Cine Cuts[Id].Resume = { Marks = segment ->
-- mark, End = mark }): a Seen (finished) cut resumes at End (the sneak's FenceLand, the bus's Stand), never at a mid-cut mark that
-- strands the player behind what they already did; otherwise Marks[Segment]. An unmapped segment or a missing mark warns and
-- leaves the player where the game put them. Returns the mark's name when it placed the player.
function Shared.Resume(Player: Player): string?
	local Cp = Shared.CheckpointOf(Player)
	if not Cp then return nil end
	local CutId, Segment = Cp:match(`^([%w_]+):([%w_]+)$`)
	local Cut = CutId and Config.Cuts[CutId]
	local Map = Cut and Cut.Resume
	if not (Cut and Map) then warn(`[Tutorial] resume: checkpoint {Cp} names a cut with no Resume map`) return nil end
	local Done = false
	pcall(function() Done = require(script.Parent.Cine).Seen(Player, CutId) == true end)
	local Name = if Done then Map.End else Map.Marks[Segment]
	local Sets = workspace:FindFirstChild(`NHCineSets`)
	local Set = Cut.Set and Sets and Sets:FindFirstChild(Cut.Set)
	local Mark = Set and Name and Set:FindFirstChild(Name)
	if not (Mark and Mark:IsA(`BasePart`)) then
		warn(`[Tutorial] resume: checkpoint {Cp} (seen {tostring(Done)}) maps to mark {tostring(Name)}, not found in set {tostring(Cut.Set)}`)
		return nil
	end
	local Char = Player.Character
	if not (Char and Char:FindFirstChild(`HumanoidRootPart`)) then return nil end
	Char:PivotTo(Mark.CFrame * CFrame.new(0, 3, 0))
	return Mark.Name
end

function Shared.Enter(Player: Player): boolean
	if Inside[Player] then return true end
	Player:SetAttribute(`NHTutorial`, true)
	setGroup(Player.Character, GROUP)
	watchLate(Player, Player.Character)
	Shared.Resume(Player)
	Inside[Player] = Player.CharacterAdded:Connect(function(C)
		C:WaitForChild(`HumanoidRootPart`, 5)
		setGroup(C, GROUP)
		watchLate(Player, C)
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
	watchLate(Player, nil)
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
	-- (final fix round) a failure here must not stop the service's own start: players would then not even get the PlayerRemoving hook
	local Ok, Err = pcall(function() PhysicsService:CollisionGroupSetCollidable(GROUP, GROUP, false) end)
	if not Ok then warn(`[Tutorial] collision group: {Err}`) end
	Players.PlayerRemoving:Connect(function(P) Shared.Leave(P, `Left`) end)
end

return Shared
