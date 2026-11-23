--[[
	Crouch (server authoritative). Hold Left Ctrl; while sprinting the same key slides instead
	(client: Controllers.Character.InputController.Movement.Slide).

	Crouching sets the Humanoid attribute Crouch = true and walk speed CROUCH_SPEED. Anything fast or busy
	stands you up: sprinting, jumping or falling, an action (attack, dodge, block, slide...), stun states,
	being downed / carried / gripped, and the main menu.

	Read by: Controllers.Character.AnimationController (Crouch / CrouchWalk tracks, camera dip) and
	Services.Quests.Stealth (Config.Stealth.Detection.CrouchMultiplier).
	Remote: UnPackets.Crouch ("Activate" | "Release").
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local UnPackets = require(ReplicatedStorage.Remotes.UnPackets)
local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local TagService = require(ReplicatedStorage.Packages.Core.TagService)

local CROUCH_SPEED = 7
local WALK_SPEED = require(ReplicatedStorage.Config.Locomotion).Speeds.Walk -- (locomotion-pace, was 12) fallback only: standing up restores the speed you had before crouching
local BUSY_STATES = { `Stun`, `ParryStun`, `Ragdoll`, `Paralyzed`, `SkillInUse`, `Downed`, `Carried`, `Gripped`, `Gripping`, `Carrying`, `InActivity` }
local BUSY_ACTIONS = { `M1`, `M2`, `Uppercut`, `Dodge`, `Slide`, `Block`, `Feint` }

local Local = {}
local Shared = {}

local Crouched = setmetatable({}, { __mode = `k` }) :: { [Humanoid]: boolean }
local Before = setmetatable({}, { __mode = `k` }) :: { [Humanoid]: number } -- walk speed before crouching
local LastPress = {} :: { [Player]: number }
local ActionManager = nil

function Local.Actions()
	if not ActionManager then
		local Ok, M = pcall(require, ServerScriptService.Services.Player.ActionManager)
		ActionManager = Ok and M or false
	end
	return ActionManager or nil
end

-- why this character can't stay crouched right now (nil = it can)
function Local.Busy(Character: Model, Humanoid: Humanoid): string?
	local Player = Players:GetPlayerFromCharacter(Character)
	if Player and Player:GetAttribute(`InMainMenu`) then return `menu` end
	if Humanoid.Health <= 0 then return `dead` end
	if Humanoid:GetAttribute(`Sprint`) then return `sprint` end
	if TagService:HasTag(Character, `InAir`) then return `air` end
	local State = Humanoid:GetState()
	if State == Enum.HumanoidStateType.Jumping or State == Enum.HumanoidStateType.Freefall then return `air` end
	if StateManager.HasState(Character, BUSY_STATES) then return `state` end
	local Actions = Local.Actions()
	if Actions then
		for _, Name in BUSY_ACTIONS do
			if Actions.isActionPlaying(Character, Name) then return Name end
		end
	end
	return nil
end

function Shared.IsCrouched(Humanoid: Humanoid): boolean
	return Crouched[Humanoid] == true
end

function Shared.Stand(Humanoid: Humanoid)
	if not Crouched[Humanoid] then return end
	Crouched[Humanoid] = nil
	Humanoid:SetAttribute(`Crouch`, nil)
	-- only undo our own speed (sprint, slide or a stun may have set theirs)
	if Humanoid.WalkSpeed == CROUCH_SPEED then Humanoid.WalkSpeed = Before[Humanoid] or WALK_SPEED end
	Before[Humanoid] = nil
end

function Shared.Crouch(Character: Model): boolean
	if Character:GetAttribute(`InSport`) or Character:GetAttribute(`HasSportBall`) then return false end -- no crouching in sports
	local Humanoid = Character and Character:FindFirstChildWhichIsA(`Humanoid`)
	if not Humanoid or Crouched[Humanoid] or Local.Busy(Character, Humanoid) then return false end
	Crouched[Humanoid] = true
	-- (audit) remember the BASE speed: while combat-tagged WalkSpeed carries CombatSpeed's multiplier, and restoring that
	-- slowed value made CombatSpeed slow it again (every crouch shaved more off)
	local Mult = Humanoid:GetAttribute(`NH_SpeedMult`)
	local Base = Humanoid.WalkSpeed / (if typeof(Mult) == `number` and Mult > 0 then Mult else 1)
	Before[Humanoid] = if Base > CROUCH_SPEED then Base else WALK_SPEED
	Humanoid:SetAttribute(`Crouch`, true)
	Humanoid.WalkSpeed = CROUCH_SPEED
	task.spawn(function()
		while Crouched[Humanoid] and Humanoid.Parent do
			if Local.Busy(Character, Humanoid) then
				Shared.Stand(Humanoid)
				break
			end
			-- something else raised the speed (e.g. a menu or a status ending): stay at crouch speed
			if Humanoid.WalkSpeed > CROUCH_SPEED then Humanoid.WalkSpeed = CROUCH_SPEED end
			task.wait(0.1)
		end
	end)
	return true
end

function Shared.OnStart()
	UnPackets.Crouch.OnServerEvent:Connect(function(Player: Player, State: string)
		local Character = Player.Character
		local Humanoid = Character and Character:FindFirstChildWhichIsA(`Humanoid`)
		if not Humanoid then return end
		if State == `Activate` then
			local Now = os.clock()
			if LastPress[Player] and Now - LastPress[Player] < 0.15 then return end -- rate limit presses (releases always count)
			LastPress[Player] = Now
			Shared.Crouch(Character)
		elseif State == `Release` then
			Shared.Stand(Humanoid)
		end
	end)
	Players.PlayerRemoving:Connect(function(Player) LastPress[Player] = nil end)
end

return Shared
