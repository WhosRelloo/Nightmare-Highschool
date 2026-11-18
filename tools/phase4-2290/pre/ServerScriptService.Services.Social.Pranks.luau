--[[
	Pranks: marking walls with crimson sigils (server). The Crimson Court's repeatable activity.

	Mark walls live in workspace.School.MarkWalls (parts named "MarkWall" with WallId, Label and
	Bonus attributes) and always show a faint "mark here" outline, so nothing is invisible.
	Hold E to mark. Every on-duty hall monitor that can see you is checked (HallMonitor.CheckWitness):
		Recognized  close and in view: Vandalism violation now, reduced standing
		Spotted     seen from afar: the monitor comes to investigate (a catch = Vandalism)
		clean       nobody saw: full standing (+ the wall's Bonus for riskier walls)
	Each player can mark each wall once per in-game day. A marked wall stays painted for
	MarkedSeconds, then the janitor scrubs it.

	Signal: Pranks.Marked(Player, WallId, { Recognized, Spotted, Bonus, PeriodKey? })
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local SignalPlus = require(ReplicatedStorage.Packages.SignalPlus)
local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local Interaction = require(ReplicatedStorage.Config.Interaction)
local DisciplineConfig = require(ReplicatedStorage.Config.Discipline)

local SchoolClock = require(ServerScriptService.Services.School.SchoolClock)
local HallMonitor = require(ServerScriptService.Services.School.HallMonitor)
local Reputation = require(ServerScriptService.Services.Social.Reputation)
local Notifications = require(ServerScriptService.Services.Features.Notifications)

local MARKED_SECONDS = 600     -- 2 in-game hours at the default clock speed
local MAX_RANGE = 10
local BUSY = { `Downed`, `Carried`, `Gripped`, `Gripping`, `InActivity`, `Stun`, `ParryStun`, `Paralyzed` }

local SIGILS = { `THE NIGHT IS OURS`, `CC`, `FANGS OUT`, `WE SEE YOU`, `CRIMSON`, `LIGHTS OUT` }

local MarkedUntil = {} :: { [BasePart]: number }

local Local = {}
local Shared = {}

Shared.Marked = SignalPlus()

function Local.Paint(Wall: BasePart, Painted: boolean)
	local Gui = Wall:FindFirstChild(`Mark`)
	if not Gui then return end
	Gui.Outline.Visible = not Painted
	Gui.Sigil.Visible = Painted
	if Painted then Gui.Sigil.Text = SIGILS[math.random(1, #SIGILS)] end
	local Prompt = Wall:FindFirstChildOfClass(`ProximityPrompt`)
	if Prompt then Prompt.Enabled = not Painted end
end

function Local.PeriodKey(): string?
	local State = SchoolClock.GetState()
	if State.Segment.Kind ~= `Class` then return nil end
	return `D{State.Day}-S{State.SegmentIndex}`
end

function Local.OnMark(Player: Player, Wall: BasePart)
	local Character = Player.Character
	local Root = Character and Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	local Humanoid = Character and Character:FindFirstChildWhichIsA(`Humanoid`)
	if not Root or not Humanoid or Humanoid.Health <= 0 or Humanoid:GetAttribute(`Downed`) then return end
	if StateManager.HasState(Character, BUSY) then return end
	if (Root.Position - Wall.Position).Magnitude > MAX_RANGE then return end
	if MarkedUntil[Wall] and os.clock() < MarkedUntil[Wall] then return end

	local WallId = Wall:GetAttribute(`WallId`)
	local Social = Reputation.Get(Player)
	if not Social or not WallId then return end
	Social.Marks = if typeof(Social.Marks) == `table` then Social.Marks else {}

	local Day = SchoolClock.GetState().Day
	if Social.Marks[WallId] == Day then
		Notifications.Notify(Player, { Title = `You already marked this wall today`; Kind = `Info`; Duration = 3 })
		return
	end
	Social.Marks[WallId] = Day
	Reputation.Sync(Player)

	-- Inner Circle "Unseen": witnesses must be twice as close to recognise you.
	local Range = DisciplineConfig.Witness.RecognizeRange * (if Player:GetAttribute(`Perk_Unseen`) then 0.5 else 1)
	local Witness = HallMonitor.CheckWitness(Player, `Vandalism`, Range)

	MarkedUntil[Wall] = os.clock() + MARKED_SECONDS
	Local.Paint(Wall, true)
	task.delay(MARKED_SECONDS, function()
		if MarkedUntil[Wall] and os.clock() >= MarkedUntil[Wall] - 0.5 then
			MarkedUntil[Wall] = nil
			Local.Paint(Wall, false)
		end
	end)

	if Witness == `Recognized` then
		Notifications.Notify(Player, { Title = `Caught red-handed`; Text = `A hall monitor saw you mark the wall.`; Kind = `Bad`; Duration = 4 })
	elseif Witness == `Spotted` then
		Notifications.Notify(Player, { Title = `A hall monitor spotted you`; Text = `Get out of sight before they reach you!`; Kind = `Warning`; Duration = 4 })
	else
		Notifications.Notify(Player, { Title = `Wall marked`; Text = `Nobody saw a thing.`; Kind = `Good`; Duration = 3 })
	end

	Shared.Marked:Fire(Player, WallId, {
		Recognized = Witness == `Recognized`;
		Spotted = Witness == `Spotted`;
		Bonus = Wall:GetAttribute(`Bonus`) or 0;
		PeriodKey = Local.PeriodKey();
	})
end

function Shared.ResetForTests(Player: Player)
	local Social = Reputation.Get(Player)
	if Social then Social.Marks = {} end
	for Wall in MarkedUntil do
		MarkedUntil[Wall] = nil
		Local.Paint(Wall, false)
	end
end

function Shared.MarkForTests(Player: Player, WallId: string)
	local School = workspace:FindFirstChild(`School`)
	local Folder = School and School:FindFirstChild(`MarkWalls`)
	for _, Wall in Folder and Folder:GetChildren() or {} do
		if Wall:GetAttribute(`WallId`) == WallId then
			Local.OnMark(Player, Wall)
			return true
		end
	end
	return false
end

function Shared.OnStart()
	local School = workspace:FindFirstChild(`School`)
	local Folder = School and School:FindFirstChild(`MarkWalls`)
	if not Folder then
		warn(`[Pranks] workspace.School.MarkWalls missing`)
		return
	end

	for _, Wall in Folder:GetChildren() do
		if not Wall:IsA(`BasePart`) then continue end
		local Prompt = Instance.new(`ProximityPrompt`)
		Prompt.ActionText = `Mark the wall`
		Prompt.ObjectText = Wall:GetAttribute(`Label`) or `Wall`
		Prompt.KeyboardKeyCode = Interaction.PromptKey
		Prompt.GamepadKeyCode = Interaction.GamepadKey
		Prompt.HoldDuration = 1.5
		Prompt.MaxActivationDistance = 7
		Prompt.RequiresLineOfSight = false
		Prompt.Triggered:Connect(function(Player)
			local Ok, Err = pcall(Local.OnMark, Player, Wall)
			if not Ok then warn(`[Pranks] {Err}`) end
		end)
		Prompt.Parent = Wall
	end
end

return Shared
