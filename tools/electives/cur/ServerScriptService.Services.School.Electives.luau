--[[
	Electives (server): one elective per term, picked at the Registrar desk (CollectionService tag NHRegistrarDesk,
	next to the Enrollment desk). Saved as Profile.Classes.Electives = { Term, Pick }; mirrored to the Player attribute
	ElectivePick, which Config.Classes.For reads on both sides. A pick holds for the term it was made in; when a new term
	begins it can change (the old pick stays until then).
	API: PickFor(Player) -> id?, Enrol(Player, Id) -> (ok, reason?), IsLocked(Player), ForceForTests(Player, Id?)
	Remotes: ElectiveEvent (Open / Result), ElectiveEnrol ({ Id }).
]]
local CollectionService = game:GetService(`CollectionService`)
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

local Packets = require(ReplicatedStorage.Remotes.Packets)
local Config = require(ReplicatedStorage.Config.Electives)
local Interaction = require(ReplicatedStorage.Config.Interaction)
local SchoolClock = require(ServerScriptService.Services.School.SchoolClock)
local Data = require(ServerScriptService.Services.Player.Data)

local Shared = {}
local Local = {}
local TAG = `NHRegistrarDesk`
local NEAR = 14

function Local.Notify(P: Player, Title: string, Text: string?, Kind: string?)
	pcall(function()
		require(ServerScriptService.Services.Features.Notifications).Notify(P, { Title = Title; Text = Text; Kind = Kind or `Info`; Duration = 4 })
	end)
end

function Local.Record(Player: Player)
	local Profile = Data.GetProfile(Player)
	if not Profile then return nil end
	if typeof(Profile.Classes) ~= `table` then Profile.Classes = {} end
	local R = Profile.Classes.Electives
	if typeof(R) ~= `table` then
		R = { Term = 0; Pick = `` }
		Profile.Classes.Electives = R
	end
	return R
end

function Local.Term(): number
	local Ok, Cal = pcall(SchoolClock.Calendar)
	return if Ok and Cal and Cal.Term then Cal.Term else 0
end

function Shared.PickFor(Player: Player): string?
	local R = Local.Record(Player)
	local Def = R and Config.Get(R.Pick)
	return if Def and Def.Open then Def.Id else nil
end

function Shared.IsLocked(Player: Player): boolean
	local R = Local.Record(Player)
	return R ~= nil and R.Pick ~= `` and R.Term == Local.Term()
end

function Shared.Enrol(Player: Player, Id: string): (boolean, string?)
	local Def = Config.Get(Id)
	if not Def then return false, `Unknown` end
	if not Def.Open then return false, `Closed` end
	local R = Local.Record(Player)
	if not R then return false, `NoData` end
	if Shared.IsLocked(Player) then return false, `Locked` end
	R.Term, R.Pick = Local.Term(), Def.Id
	Player:SetAttribute(`ElectivePick`, Def.Id)
	Local.Notify(Player, `Enrolled: {Def.Name}`, `Tuesdays and Thursdays, periods 3 and 4. Room {Def.Room:sub(2)}.`, `Success`)
	return true, nil
end

function Shared.ForceForTests(Player: Player, Id: string?)
	local R = Local.Record(Player)
	if R then R.Term, R.Pick = 0, Id or `` end
	Player:SetAttribute(`ElectivePick`, if Config.Get(Id) then Id else nil)
end

function Local.Near(Player: Player): boolean
	local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	if not Root then return false end
	for _, D in CollectionService:GetTagged(TAG) do
		local Pos = if D:IsA(`Model`) then D:GetPivot().Position elseif D:IsA(`BasePart`) then D.Position else nil
		if Pos and (Pos - Root.Position).Magnitude <= NEAR then return true end
	end
	return false
end

function Local.OnJoin(Player: Player)
	for _ = 1, 60 do
		if not Player.Parent or Data.GetProfile(Player) then break end
		task.wait(0.25)
	end
	if Player.Parent then Player:SetAttribute(`ElectivePick`, Shared.PickFor(Player)) end
end

function Local.Prompt(Inst: Instance)
	local Host = if Inst:IsA(`Model`) then (Inst.PrimaryPart or Inst:FindFirstChildWhichIsA(`BasePart`, true)) else Inst
	if not (Host and Host:IsA(`BasePart`)) or Host:FindFirstChild(`NHRegistrarPrompt`) then return end
	local Pr = Instance.new(`ProximityPrompt`)
	Pr.Name = `NHRegistrarPrompt`
	Pr.ActionText = `Choose an elective`
	Pr.ObjectText = `The Registrar`
	Pr.KeyboardKeyCode = Interaction.PromptKey
	Pr.GamepadKeyCode = Interaction.GamepadKey
	Pr.HoldDuration = 0
	Pr.MaxActivationDistance = 8
	Pr.RequiresLineOfSight = false
	Pr.Triggered:Connect(function(Player)
		Packets.ElectiveEvent:FireClient(Player, { Type = `Open`; Pick = Shared.PickFor(Player); Locked = Shared.IsLocked(Player); Term = Local.Term() })
	end)
	Pr.Parent = Host
end

-- (Task 12) Anatomy mastery: every species in Config.Anatomy.Mastery at MinGrade or better grants the title
-- (Social.Reputation.AwardTitle) and the accessory (Features.Accessories.Grant). Both calls are idempotent, so this runs
-- after every Journal write: the title lands once, and the accessory backfills on the next lesson once it is in
-- Config.Accessories (BrassLoupeMonocle is not modelled yet). Returns { Title = bool, Accessory = bool } (newly granted).
local GRADE_RANK = { [`A+`] = 6; A = 5; B = 4; C = 3; D = 2; F = 1 }
function Shared.CheckMastery(Player: Player, Subject: string, ClassData): { Title: boolean, Accessory: boolean }?
	if Subject ~= `Anatomy` or typeof(ClassData) ~= `table` or typeof(ClassData.Journal) ~= `table` then return nil end
	local M = require(ReplicatedStorage.Config.Anatomy).Mastery
	for _, Id in M.Species do
		if (GRADE_RANK[ClassData.Journal[Id]] or 0) < GRADE_RANK[M.MinGrade] then return nil end
	end
	local Got = { Title = false; Accessory = false }
	local Svc = ServerScriptService.Services
	pcall(function() Got.Title = require(Svc.Social.Reputation).AwardTitle(Player, M.Title) == true end)
	pcall(function() Got.Accessory = require(Svc.Features.Accessories).Grant(Player, M.Accessory) == true end)
	if not ClassData.Mastered then
		ClassData.Mastered = true
		Local.Notify(Player, `Specimen Journal complete`, `Every specimen at {M.MinGrade} or better. You are an {M.Title}.`, `Good`)
	end
	if Got.Accessory then Local.Notify(Player, `New in your wardrobe`, `The Brass Loupe Monocle: wear it at a wardrobe station.`, `Info`) end
	return Got
end

function Shared.OnStart()
	pcall(function()
		require(ServerScriptService.Services.School.Activities).JournalHandler = Shared.CheckMastery
	end)
	Players.PlayerAdded:Connect(Local.OnJoin)
	for _, P in Players:GetPlayers() do task.spawn(Local.OnJoin, P) end
	Packets.ElectiveEnrol.OnServerEvent:Connect(function(Player, Msg)
		if typeof(Msg) ~= `table` or typeof(Msg.Id) ~= `string` then return end
		local Ok, Why
		if not Local.Near(Player) then Ok, Why = false, `Far` else Ok, Why = Shared.Enrol(Player, Msg.Id) end
		Packets.ElectiveEvent:FireClient(Player, { Type = `Result`; Ok = Ok; Why = Why; Pick = Shared.PickFor(Player); Locked = Shared.IsLocked(Player); Term = Local.Term() })
	end)
	for _, I in CollectionService:GetTagged(TAG) do Local.Prompt(I) end
	CollectionService:GetInstanceAddedSignal(TAG):Connect(Local.Prompt)
end

return Shared
