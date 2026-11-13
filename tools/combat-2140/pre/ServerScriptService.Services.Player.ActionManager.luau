
---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

---| Modules |---

local UnPackets = require(ReplicatedStorage.Remotes.UnPackets)
local Packets = require(ReplicatedStorage.Remotes.Packets)
local CombatLog = require(game:GetService(`ServerStorage`).Packages.CombatLog) -- (2.13.0) Studio combat log

local Trove = require(ReplicatedStorage.Packages.Trove)
local TagService = require(ReplicatedStorage.Packages.Core.TagService)
local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local _AirWeldCache = require(ReplicatedStorage.Packages.Core._Local).new(`AirWeld`)

---| Type Annotation |---

type		Class = 'Attack' | 'Movement' | 'General'
type		Priority = 'Low' | 'Default' | 'High'

export type ActionManager = {

	--| Properties |--

	Character: Model | Instance;
	Action: string ?;

	Trove: Trove.Trove;
	Thread: thread;

	Activate: (self: ActionManager, Action: string, ...any) -> (boolean ?);
	Cancel: (self: ActionManager,  Action: string) -> (boolean ?);

	CanActivate: (self: ActionManager, Action: string) -> (boolean ?);
	Cooldown: (self: ActionManager, Action: string, Duration: number) -> (ActionManager);

	Release: (self: ActionManager, Action: string, ...any) -> (ActionManager);
	Destroy: (self: ActionManager) -> ();

	--| Threads |--

	Cooldowns: { [string]: {boolean} ? };
	Tasks: { typeof(task.spawn( function() end) ) };
}

local EntityManager = {} :: { [Model]: ActionManager }
local PriorityList = { `Low`; `Default`; `High` }

-- Downed / Carry / Grip lock out actions (see Services.Features.Downed).
local LOCKED_STATES = { `Downed`, `Carried`, `Gripped`, `Gripping`, `InActivity` }
local CARRY_ALLOWED_ACTIONS = { Sprint = true }

-- Actions a client may start by name through the generic UnPackets.Action remote.
-- Empty on purpose: nothing uses it yet, and an open remote let clients start any
-- action (e.g. Dodge without a direction = free i-frames, the Template skill with no cooldown).
-- Add skill names here when the skill system needs it.
local REMOTE_ACTION_ALLOWLIST = { BodySlam = true; BearHug = true; QuestionMarkKick = true; RaceAction = true; SlashBarrage = true; RippersWaltz = true; Transform = true; WolfBite = true; WolfLeap = true } :: { [string]: boolean } -- Fist skills (Skills/*, they check the Fist weapon themselves)

local TOGGLE_STATES = { Activate = true, Release = true }
local ENDER_WINDOW = 0.8 -- (fist moveset) M2 this soon after hit 2 or 3 lands is a string ender
local M1_BUFFER = 0.5 -- (combat audit) a click this close to the end of a swing plays next instead of being dropped (0.35 lost clicks to the server's wait overshooting by a frame)
local WOLF_ALLOWED = { Sprint = true; Dodge = true; Slide = true; Transform = true; WolfBite = true; WolfLeap = true; RaceAction = true }

local Manager = {}
Manager.__index = Manager

local Local = {}
local Shared = {}

function Shared.OnStart()

	UnPackets.Feint.OnServerEvent:Connect(function(Player: Player)
		local Character = Player.Character
		if not Character then return end

		Shared.Feint(Character)
	end)

	UnPackets.Slide.OnServerEvent:Connect(function(Player: Player)
		local Character = Player.Character
		if not Character then return end
		-- (audit) the slide key only slides while sprinting (otherwise it crouches), but any Slide packet used to slide.
		-- A sprint being carried out of a slide (SprintCarry) and a chained slide (ChainSlide) still count.
		local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`)
		local Chain = Character:GetAttribute(`ChainSlide`) == true
		if not Humanoid or not (Humanoid:GetAttribute(`Sprint`) or Character:GetAttribute(`SprintCarry`) or Chain) then return end

		local ActionManager = Manager.new(Character)
		-- (audit) the chain-slide window (0.5 s after a slide-jump) is shorter than the 2 s slide cooldown, so its +10 was
		-- unreachable: a slide inside the window skips the running cooldown (put back if the slide doesn't start)
		local Held = if Chain then ActionManager.Cooldowns[`Slide`] else nil
		if Held then ActionManager.Cooldowns[`Slide`] = nil end
		local Started = ActionManager:Activate(`Slide`)
		if Held and not Started and ActionManager.Cooldowns and not ActionManager.Cooldowns[`Slide`] and next(Held) then ActionManager.Cooldowns[`Slide`] = Held end
		if Started and Chain then Character:SetAttribute(`ChainSlide`, nil) end -- one chained slide per slide-jump
	end)





	UnPackets.M1.OnServerEvent:Connect(function(Player: Player, Flags: number) -- (combat audit) 1 = aerial, 2 = a new press
		if typeof(Flags) ~= `number` then return end
		local Aerial = Flags % 2 == 1
		local Press = (Flags // 2) % 2 == 1
		local Predicted = (Flags // 8) % 8 -- (2.13.0, combat concept 12) the hit the client already started, 0 = none
		local Character = Player.Character
		if not Character then return end
		if CombatLog.On() and Press then CombatLog.Log(Character, `in M1`, string.format(`press%s%s, ping %d ms`, if Aerial then ` (air)` else ``, if Predicted > 0 then `, client started hit ` .. Predicted else ``, math.floor(Player:GetNetworkPing() * 1000))) end

		local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		if not Humanoid then return end

		local Paramaters = { 
			Aerial = Local.ServerAerial(Character, Humanoid, Aerial);
			Running = Humanoid:GetAttribute(`Sprint`) :: boolean;
			Predicted = if Press and Predicted > 0 then Predicted else nil; -- (2.13.0) Combat.M1
		}

		local ActionManager = Manager.new(Character)
		-- (2.13.0, combat concept 12) the client started a swing this press won't play (refused, buffered for later, the
		-- clinch): bumping NHPredictRefused makes it drop its copy at once (InputController.Combat.M1.Predict)
		local function Refuse()
			if Paramaters.Predicted then Character:SetAttribute(`NHPredictRefused`, (Character:GetAttribute(`NHPredictRefused`) or 0) + 1) end
		end
		-- (fist moveset) M1 while holding block is the clinch (Combat.Clinch): a grab that goes through a guard
		if ActionManager.Action == `Block` and not Paramaters.Aerial and Local.IsFist(Character) then
			Refuse()
			ActionManager:Activate(`Clinch`)
			return
		end
		-- (combat audit) a click during a swing used to be dropped (tapping in rhythm lost hits); now it's remembered and the
		-- next swing starts the moment this one ends (Manager.Activate), if the click was within M1_BUFFER of it.
		-- Only a fresh press counts: the client re-sends M1 every 0.05 s while the button is held, and buffering those
		-- repeats turned one click into two swings.
		-- Only a new press counts (the client flags it): the client re-sends M1 every 0.05 s while the button is held, and
		-- buffering those repeats turned one click into two swings. (A timing guess, gap > 0.09 s, wasn't enough: the
		-- network batches the repeats ~0.1 s apart.)
		if not ActionManager:Activate(`M1`, Paramaters) then
			Refuse()
			if ActionManager.Action == `M1` and not Paramaters.Aerial and Press then
				ActionManager.BufferedM1 = os.clock()
			end
		end
	end)


	UnPackets.M2.OnServerEvent:Connect(function(Player: Player, Flags: number) -- (combat B10) 1 = aerial, 2 = a new press, 4 = let go
		if typeof(Flags) ~= `number` then return end
		local Aerial = Flags % 2 == 1
		if CombatLog.On() and Player.Character and Flags >= 2 then CombatLog.Log(Player.Character, `in M2`, if (Flags // 4) % 2 == 1 then `let go` else `press`) end
		local HeldBy = Player.Character and Manager.new(Player.Character)
		if HeldBy then
			if (Flags // 4) % 2 == 1 then HeldBy.M2Held = false return end -- let go (Assets.M2.Fist charges while held)
			if (Flags // 2) % 2 == 1 then HeldBy.M2Held = true end
			HeldBy.M2LastPacket = os.clock() -- the hold-repeats keep a charge alive even if the let-go packet is lost
		end
		local Character = Player.Character
		if not Character then return end

		local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		if not Humanoid then return end

		local Paramaters = { 
			Aerial = Local.ServerAerial(Character, Humanoid, Aerial);
			Running = Humanoid:GetAttribute(`Sprint`) :: boolean
		}

		local ActionManager = Manager.new(Character)
		-- (fist moveset) right after hit 2 or 3 of the string, M2 is a string ender instead of the plain heavy
		if not Paramaters.Aerial and Local.TryEnder(ActionManager, Character, Humanoid) then return end
		ActionManager:Activate(`M2`, Paramaters)
	end)

	UnPackets.Uppercut.OnServerEvent:Connect(function(Player: Player)
		local Character = Player.Character
		if not Character then return end

		local ActionManager = Manager.new(Character)
		ActionManager:Activate(`Uppercut`)
	end)

	UnPackets.Dodge.OnServerEvent:Connect(function(Player: Player, MoveVector: string) 
		if not MoveVector then return end

		local Character = Player.Character
		if not Character then return end

		local ActionManager = Manager.new(Character)
		ActionManager:Activate(`Dodge`, MoveVector)
	end)

	UnPackets.Sprint.OnServerEvent:Connect(function(Player: Player, State: string)
		if not TOGGLE_STATES[State] then return end

		local Character = Player.Character
		if not Character then return end

		Character:SetAttribute(`SprintHeld`, State == `Activate`) -- a slide hands back to the sprint while it's held
		local ActionManager = Manager.new(Character)
		ActionManager[State](ActionManager, `Sprint`)
	end)

	UnPackets.Block.OnServerEvent:Connect(function(Player: Player, State: string)
		if not TOGGLE_STATES[State] then return end

		local Character = Player.Character
		if not Character then return end

		local ActionManager = Manager.new(Character)
		ActionManager[State](ActionManager, `Block`)
	end)

	UnPackets.Equip.OnServerEvent:Connect(function(Player: Player)
		local Character = Player.Character
		if not Character then return end

		local ActionManager = Manager.new(Character)
		ActionManager.Activate(ActionManager, `Equip`)
	end)

	UnPackets.Action.OnServerEvent:Connect(function(Player: Player, ActionName: string)
		if typeof(ActionName) ~= `string` or not REMOTE_ACTION_ALLOWLIST[ActionName] then return end

		local Character = Player.Character
		if not Character then return end

		local ActionManager = Manager.new(Character)
		ActionManager.Activate(ActionManager, ActionName)
	end)

end

function Shared.CancelAction(Character: Model, Action: string)
	if not Character then
		return
	end

	local ActionManager = Manager.new(Character)
	ActionManager:Cancel(Action)
end

function Shared.CancelCurrentAction(Character: Model)
	if not Character then
		return
	end

	local ActionManager = Manager.new(Character)
	if not ActionManager.Action then return end

	ActionManager:Cancel(ActionManager.Action)
end

function Shared.CancelClass(Character: Model, Class: Class)
	if not Character then
		return
	end

	local ActionManager = Manager.new(Character)
	local Module = ActionManager.Action and Local.FetchModule(ActionManager.Action) :: ModuleScript

	if not Module then
		return
	end

	local ActionClass = Module.Class
	if ActionClass ~= Class then return end

	return ActionManager:Cancel(ActionManager.Action)
end

function Shared.CancelCooldown(Character: Model, Name: string)
	if not Character then
		return
	end

	local ActionManager = Manager.new(Character)
	if not ActionManager.Cooldowns[Name] then return end

	local Cooldowns = ActionManager.Cooldowns[Name]
	table.clear(ActionManager.Cooldowns[Name])
end

function Shared.isActionPlaying(Character: Model, Action: string): boolean
	if not Character then
		return
	end

	local ActionManager = Manager.new(Character)
	return ActionManager.Action == Action
end

function Shared.M1(Character: Model)
	if not Character then
		return
	end

	local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	if not Humanoid then return end

	local Paramaters = { 
		Aerial = false;
		Running = Humanoid:GetAttribute(`Sprint`) :: boolean
	}

	local ActionManager = Manager.new(Character)
	ActionManager:Activate(`M1`, Paramaters)
end

function Shared.Equip(Character: Model)
	if not Character then
		return
	end

	local ActionManager = Manager.new(Character)
	ActionManager:Activate(`Equip`)
end

function Shared.Block(Character: Model, State: string)
	if not Character then
		return
	end

	local ActionManager = Manager.new(Character)
	if State == `Activate` then
		ActionManager:Activate(`Block`)
	elseif State == `Cancel` then
		ActionManager:Cancel(`Block`)
	end
end

function Shared.Feint(Character: Model)
	if not Character then
		return
	end

	local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	if not Humanoid then return end

	local Feintables = { `M1` }
	local ActionManager = Manager.new(Character)

	if ActionManager.Cooldowns[`Feint`] then
		return
	end

	if not table.find(Feintables, ActionManager.Action) then
		return
	end

	Shared.CancelCurrentAction(Character)
	Shared.CancelClass(Character, `Attack`)

	ActionManager:Cooldown(`Feint`, 3)
	ActionManager:Cooldown(`Aerial M1`, 2)

	Packets.Replicate:Fire(`Misc`, `Feint`, {
		User = Character;
	})

	local Player = Players:GetPlayerFromCharacter(Character)
	if Player then 
		Packets.Replicate:FireClient(Player, `Shared`, `Feint M2`, {})
	end
end

-- (fist moveset) the string enders and the clinch are the fist class's (equipped)
function Local.IsFist(Character: Model): boolean
	local Ok, Fist = pcall(function() return require(script.Skills.GrabCore).IsFist(Character) end)
	return Ok and Fist == true
end

-- (fist moveset) concept 6: M2 within ENDER_WINDOW of hit 2 or 3 landing ends the string with a special:
--   after hit 1, the shove; after hit 2, the launcher (the Uppercut); after hit 3, the body blow (Combat.Ender).
--   (Holding back for the shove was tried first: the character turns to walk away, so it swung at nothing.)
-- It cancels the swing's recovery once that swing's hit frame has passed. Returns true if an ender started.
function Local.TryEnder(AM, Character: Model, Humanoid: Humanoid): boolean
	if not Local.IsFist(Character) then return false end
	if next(AM.Cooldowns[`M2`] or {}) then return false end
	local Combo = Character:GetAttribute(`Combo`) or 0
	local LastHit = Character:GetAttribute(`Tick`) or 0 -- tick() of the last swing's hit frame (Combat.M1)
	if Combo < 1 or tick() - LastHit > ENDER_WINDOW then return false end
	local Kind = if Combo == 1 then `Shove` elseif Combo == 2 then `Launcher` elseif Combo == 3 then `BodyBlow` else nil
	if not Kind then return false end
	if Kind == `Launcher` and next(AM.Cooldowns[`Uppercut`] or {}) then return false end
	if AM.Action == `M1` then
		local Wu = Character:GetAttribute(`NHWindupUntil`)
		if typeof(Wu) == `number` and workspace:GetServerTimeNow() < Wu then return false end -- the next swing is winding up
		AM:Cancel(`M1`)
	elseif AM.Action then
		return false
	end
	Character:SetAttribute(`Combo`, 0) -- the string is over; the next M1 starts a new one
	if Kind == `Launcher` then
		if AM:Activate(`Uppercut`) then AM:Cooldown(`M2`, 2.5) return true end
		return false
	end
	return AM:Activate(`Ender`, Kind) == true
end

function Local.CleanupAirWeld(Character: Model)
	TagService.RemoveAllTagsFromInstance(Character, `AirWeld`)
end

function Local.FetchModule(Name: string)
	local Module = script:FindFirstChild(Name, true) :: ModuleScript
	if not Module or not Module:IsA(`ModuleScript`) then return end

	local Success, Result = pcall(function()
		return require(Module) or nil
	end)

	if not Success then return end

	if typeof(Result) ~= `function` and Result ~= nil then
		return Result
	end
end

-- (audit) the client says whether an M1/M2 is aerial; the server used to take its word, so an exploiter could use the
-- stronger aerial attacks on the ground. Now the server must also see the character airborne (or in an air combo).
-- A real aerial clicked right at the start of a jump can reach the server before the jump does, so it waits a moment.
function Local.ServerAerial(Character: Model, Humanoid: Humanoid, Claimed: any): boolean
	if Claimed ~= true then return false end
	local function Air(): boolean
		if Humanoid.FloorMaterial == Enum.Material.Air then return true end
		local State = Humanoid:GetState()
		if State == Enum.HumanoidStateType.Freefall or State == Enum.HumanoidStateType.Jumping then return true end
		local Ok, Tagged = pcall(function() return TagService:HasTag(Character, `InAir`) end)
		return Ok and Tagged == true
	end
	if Air() then return true end
	local Start = os.clock()
	while os.clock() - Start < 0.2 do
		task.wait()
		if Air() then return true end
	end
	return false
end

function Manager.new(Character: Model): ActionManager
	if EntityManager[Character] then
		return EntityManager[Character]
	end

	local self = setmetatable({}, Manager) :: ActionManager

	self.Character = Character
	self.Action = false

	self.Cooldowns = { }
	self.Tasks = { }

	self.Trove = Trove.new()
	self.Trove:Connect(
		Character.AncestryChanged,
		function(Child: Instance, Parent: Instance)
			if Parent then
				return
			end

			self:Destroy()
		end)

	EntityManager[Character] = self
	return self
end

function Manager.Activate(self: ActionManager, Action: string, ...): boolean?
	local Module = Local.FetchModule(Action)
	if not Module then return end

	if not self:CanActivate(Action, ...) then
		if CombatLog.On() and (Module.Class == `Attack` or Action == `Block` or Action == `Dodge`) then
			CombatLog.Log(self.Character, `refused`, Action .. (if self.Action then ` (busy: ` .. tostring(self.Action) .. `)` else ``))
		end
		return
	end

	local Activate = Module.Activate :: (self: ActionManager, ...any) -> ()
	if not Activate then return end
	if CombatLog.On() and (Module.Class == `Attack` or Action == `Block` or Action == `Dodge`) then
		CombatLog.Log(self.Character, `start`, Action .. (if self.Action and self.Action ~= Action then ` (cancels ` .. tostring(self.Action) .. `)` else ``))
	end

	if self.Thread then
		local threadStatus = coroutine.status(self.Thread)
		if threadStatus == "suspended" or threadStatus == "running" then
			pcall(coroutine.close, self.Thread)
		end
	end

	local Paramaters = {...}
	self.Thread = coroutine.create(function()
		self.Action = Action
		local Me = coroutine.running()
		-- (audit) a Sprint/Block/Equip thread that outlives its Release used to clear the NEXT action's state when it
		-- woke up (an M1 started right after letting go of sprint became invisible to the manager). Only clear it
		-- while this thread still owns the manager, or nothing else has started since.
		-- (Equip swaps in its own thread, so "still this action" counts as owning it too)
		local function Owns() return self.Thread == Me or self.Action == false or self.Action == Action end

		local Success, Result = pcall(
			Activate,
			self,
			unpack(Paramaters)

		)

		if not Success then 
			if Owns() then self.Action = false end
			return warn(Result, Action) 
		end

		if Module.Cooldown then
			self:Cooldown(Action, Module.Cooldown)
		end

		if Owns() then
			self.Action = false
			Local.CleanupAirWeld(self.Character)
			-- (combat audit) play the buffered click
			local Buffered = Action == `M1` and self.BufferedM1
			self.BufferedM1 = nil
			if Buffered and os.clock() - Buffered <= M1_BUFFER then
				local Char = self.Character
				task.defer(function() if Char and Char.Parent and self.Action == false then Shared.M1(Char) end end)
			end
		end
	end)

	coroutine.resume(self.Thread)
	return true
end

function Manager.CanActivate(self: ActionManager, Action: string, ...): boolean?
	local Module = Local.FetchModule(Action)
	if not Module then return end

	-- Main menu: your student stands on the stage while you edit them; no combat.
	local MenuPlayer = game:GetService(`Players`):GetPlayerFromCharacter(self.Character)
	if MenuPlayer and MenuPlayer:GetAttribute(`InMainMenu`) == true then return end

	if StateManager.HasState(self.Character, LOCKED_STATES) then
		return
	end

	-- wolf form (Features.Transformation): only movement, the wolf's own attacks and turning back
	if self.Character:GetAttribute(`WolfForm`) and not WOLF_ALLOWED[Action] then
		return
	end

	if StateManager.HasState(self.Character, `Carrying`) and not CARRY_ALLOWED_ACTIONS[Action] then
		return
	end

	local Priority = Module.Priority :: Priority or `Default` :: Priority
	local Conditions = Module.Conditions :: (self: ActionManager) -> ()

	-- on cooldown: refuse BEFORE cancelling what you're doing (a dash pressed on cooldown used to kill your sprint)
	if next(self.Cooldowns[Action] or {}) then
		return
	end

	if self.Action then
		local LastActionModule = Local.FetchModule(self.Action)
		local LastPriority = LastActionModule.Priority :: Priority or `Default` :: Priority

		Priority = table.find(PriorityList, Priority) :: Priority
		LastPriority = table.find(PriorityList, LastPriority) :: Priority

		if LastPriority >= Priority then
			return
		end

		self:Cancel(self.Action)
	end

	if self.Action or Conditions and not Conditions(self, ...) then
		return
	end

	if next(self.Cooldowns[Action] or {}) then
		return
	end

	return true
end

function Manager.Release(self: ActionManager, Action: string, ...): ActionManager
	local Module = Local.FetchModule(Action)
	if not Module or self.Action ~= Action then return end

	local Release = Module.Release :: (self: ActionManager, Action: string, ...any) -> ()
	if not Release then return end

	local Paramaters = {...}
	self.Thread = coroutine.create(function()
		local Success, Result = pcall(
			Release,
			self,
			unpack(Paramaters)

		)

		self.Action = false
		if not Success then return warn(Result, Action) end
	end)

	coroutine.resume(self.Thread)
	return self
end

function Manager.Cancel(self: ActionManager, Action: string): boolean?
	local Module = Local.FetchModule(Action)
	if not Module or self.Action ~= Action then return end

	local OnCancel = Module.OnCancel :: (self: ActionManager) -> ()

	if self.Thread then
		coroutine.close(self.Thread)
	end

	if OnCancel then
		local Success, Result = pcall(OnCancel, self)

		if not Success then
			warn(Result)

		end

	end

	self.Action = false
	Local.CleanupAirWeld(self.Character)
	return true
end

function Manager.Cooldown(self: ActionManager, Action: string, Duration: number): ActionManager
	if not self or not self.Cooldowns then
		return self
	end

	if not self.Cooldowns[Action] then
		self.Cooldowns[Action] = {}

	end

	local Cooldown = self.Cooldowns[Action]
	table.insert(Cooldown, true)
	-- skills show their cooldown on the client hotbar (Controllers.SkillController)
	if REMOTE_ACTION_ALLOWLIST[Action] and self.Character then
		self.Character:SetAttribute(`SkillCD_{Action}`, workspace:GetServerTimeNow() + Duration)
	end

	local Task
	Task = task.delay(Duration, function()
		-- (audit) a finished cooldown task leaves self.Tasks (it grew by one entry per cooldown for the whole life)
		if self and self.Tasks then
			local At = table.find(self.Tasks, Task)
			if At then table.remove(self.Tasks, At) end
		end
		if not self or not self.Cooldowns then return end

		table.remove(Cooldown, table.find(Cooldown, true))

		if not next(Cooldown) then
			-- (audit) only while the slot still holds this table (the chain slide swaps a fresh one in)
			if self.Cooldowns[Action] == Cooldown then self.Cooldowns[Action] = nil end

		end
	end)

	table.insert(self.Tasks, Task)
	return self
end

function Manager.Destroy(self: ActionManager)
	if self.Thread then
		local threadStatus = coroutine.status(self.Thread)
		if threadStatus == "suspended" or threadStatus == "running" then
			pcall(coroutine.close, self.Thread)
		end
		self.Thread = nil
	end
	-- (audit) let the running action clean up after itself (a grab anchors its victim and only OnCancel lets go;
	-- when the grabber left mid-grab the victim stayed anchored)
	if self.Action then
		local Module = Local.FetchModule(self.Action)
		if Module and Module.OnCancel then pcall(Module.OnCancel, self) end
	end

	self.Trove:Destroy()
	self.Trove = nil

	self.Action = nil

	if self.Cooldowns then
		table.clear(self.Cooldowns)
		self.Cooldowns = nil
	end

	if self.Tasks then
		for _, Task in self.Tasks do
			task.cancel(Task)
		end
		table.clear(self.Tasks)
		self.Tasks = nil
	end

	if EntityManager[self.Character] then
		EntityManager[self.Character] = nil
	end
end

Shared.new = Manager.new

return Shared
