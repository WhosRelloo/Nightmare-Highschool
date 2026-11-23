--[[
	Players sit in the classroom chairs (server). Services.Features.PlayerSeats   (1.47, owner: "make it so players can
	sit in the classroom seats as well")

	Every StudentChair prop in the school gets an invisible Seat on its cushion (Features.Seats: the seat-top height,
	facing the chair's front) and a "Sit" prompt (hold E, close by). Touching the seat does nothing (CanTouch off), so
	nobody sits by walking into a chair; jump to stand up. A chair a student is sitting in, or heading for, refuses
	(Features.Schedules marks its chairs: ChairTaken), and a chair a player sits in is skipped by the students
	(IsOccupied).

	The sitter's client plays the students' Sitting pose (Controllers.World.PlayerSeat) and, once it's on, says how far
	the hips are from the cushion (ReplicatedStorage.NHPlayerSeats.Settle(Up, Back)); the server moves the seat weld by
	that much (clamped), so the hips rest on the cushion a little toward the backrest, like the students'.

	API: IsOccupied(Chair) -> boolean, SeatOf(Chair) -> Seat?
]]
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

local Shared = {}
local Local = {}

local KINDS = { StudentChair = true; BleacherSeat = true } -- (phase6-strafes) players sit on the bleachers too (owner)
-- (audit) can't sit while busy: the Npcs / Hangouts BUSY list, plus Carrying
local BUSY = { `Downed`, `Carried`, `Carrying`, `Gripped`, `Gripping`, `InActivity`, `Stun`, `ParryStun`, `Paralyzed` }
local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)

local function svc(Path: string)
	local Node = ServerScriptService.Services
	for Part in Path:gmatch(`[^%.]+`) do Node = Node:FindFirstChild(Part) if not Node then return nil end end
	local Ok, Mod = pcall(require, Node)
	return Ok and Mod or nil
end

function Shared.SeatOf(Chair: Model): Seat?
	local S = Chair and Chair:FindFirstChild(`NHPlayerSeat`)
	return if S and S:IsA(`Seat`) then S else nil
end

function Shared.IsOccupied(Chair: Model): boolean
	local S = Shared.SeatOf(Chair)
	return S ~= nil and S.Occupant ~= nil
end

function Local.Notify(P: Player, Title: string)
	local N = svc(`Features.Notifications`)
	if N then pcall(N.Notify, P, { Title = Title; Kind = `Info`; Duration = 3 }) end
end

function Local.Setup(Chair: Model)
	if Shared.SeatOf(Chair) then return end
	local Seats = svc(`Features.Seats`)
	if not Seats then return end
	local Top = Seats.Top(Chair)
	local Look = Chair:GetPivot().LookVector * Vector3.new(1, 0, 1)
	Look = if Look.Magnitude > 0 then Look.Unit else Vector3.new(0, 0, -1)
	local Seat = Instance.new(`Seat`)
	Seat.Name = `NHPlayerSeat`
	Seat.Size = Vector3.new(1.4, 0.2, 1.4)
	-- the seat's top on the cushion, facing the chair's front (a sitter faces the Seat's LookVector)
	Seat.CFrame = CFrame.lookAt(Top - Vector3.new(0, 0.1, 0), Top - Vector3.new(0, 0.1, 0) + Look)
	Seat.Anchored = true
	Seat.CanCollide = false
	Seat.CanTouch = false
	Seat.CanQuery = false
	Seat.Transparency = 1
	Seat.Parent = Chair
	local Interaction = require(ReplicatedStorage.Config.Interaction)
	local Prompt = Instance.new(`ProximityPrompt`)
	Prompt.Name = `SitPrompt`
	Prompt.ActionText = `Sit`
	Prompt.ObjectText = `Chair`
	Prompt.KeyboardKeyCode = Interaction.PromptKey
	Prompt.GamepadKeyCode = Interaction.GamepadKey
	Prompt.HoldDuration = 0.2
	Prompt.MaxActivationDistance = 4.5
	Prompt.RequiresLineOfSight = false
	Prompt.Parent = Seat
	Prompt.Triggered:Connect(function(P)
		local Ok, Err = pcall(Local.Sit, P, Chair, Seat)
		if not Ok then warn(`[PlayerSeats] {Err}`) end
	end)
	Seat:GetPropertyChangedSignal(`Occupant`):Connect(function()
		Prompt.Enabled = Seat.Occupant == nil
	end)
end

function Local.Sit(P: Player, Chair: Model, Seat: Seat)
	local C = P.Character
	local Hum = C and C:FindFirstChildWhichIsA(`Humanoid`)
	if not Hum or Hum.Health <= 0 or Hum:GetAttribute(`Downed`) or Hum.Sit then return end
	if StateManager.HasState(C, BUSY) then return end -- (audit) carrying / gripping / stunned
	if Seat.Occupant then return end
	local Sched = svc(`Features.Schedules`)
	if Sched and Sched.ChairTaken and Sched.ChairTaken(Chair) then
		Local.Notify(P, `Someone's sitting there`)
		return
	end
	local Act = svc(`School.Activities`)
	if Act and Act.IsInActivity(P) then return end
	Seat:Sit(Hum)
end

-- the sitter's client measured its posed hips against the cushion: move the seat weld (seat space: +Y up, +Z back)
function Local.Settle(P: Player, Up: any, Back: any)
	if typeof(Up) ~= `number` or typeof(Back) ~= `number` or Up ~= Up or Back ~= Back then return end
	local Hum = P.Character and P.Character:FindFirstChildWhichIsA(`Humanoid`)
	local Seat = Hum and Hum.SeatPart
	if not (Seat and Seat.Name == `NHPlayerSeat` and Seat.Occupant == Hum) then return end
	local W = Seat:FindFirstChild(`SeatWeld`)
	if not (W and W:IsA(`Weld`)) then return end
	local Base = W:GetAttribute(`NHBaseC0`)
	if not Base then Base = W.C0 W:SetAttribute(`NHBaseC0`, Base) end
	-- the corrections add up (the client may measure again once the first one has landed)
	local U = math.clamp((W:GetAttribute(`NHUp`) or 0) + Up, -1.5, 1.5)
	local B = math.clamp((W:GetAttribute(`NHBack`) or 0) + Back, -0.2, 0.8)
	W:SetAttribute(`NHUp`, U)
	W:SetAttribute(`NHBack`, B)
	W.C0 = CFrame.new(0, U, B) * Base
end

function Shared.OnStart()
	local F = Instance.new(`Folder`)
	F.Name = `NHPlayerSeats`
	local R = Instance.new(`RemoteEvent`)
	R.Name = `Settle`
	R.Parent = F
	F.Parent = ReplicatedStorage
	R.OnServerEvent:Connect(function(P, Up, Back) pcall(Local.Settle, P, Up, Back) end)
	task.spawn(function()
		local School = workspace:WaitForChild(`School`, 30)
		local Props = School and School:WaitForChild(`NHProps`, 30)
		if not Props then return end
		for _, P in Props:GetChildren() do
			if P:IsA(`Model`) and KINDS[P.Name] then pcall(Local.Setup, P) end
		end
		Props.ChildAdded:Connect(function(P)
			if P:IsA(`Model`) and KINDS[P.Name] then task.defer(function() pcall(Local.Setup, P) end) end
		end)
		-- (phase6-strafes) the bleacher seats (tagged models, workspace.Sports.<Venue>.NHBleacherSeats)
		local CS = game:GetService(`CollectionService`)
		for _, P in CS:GetTagged(`NHBleacherSeat`) do if P:IsA(`Model`) then pcall(Local.Setup, P) end end
		CS:GetInstanceAddedSignal(`NHBleacherSeat`):Connect(function(P)
			if P:IsA(`Model`) then task.defer(function() pcall(Local.Setup, P) end) end
		end)
	end)
end

return Shared
