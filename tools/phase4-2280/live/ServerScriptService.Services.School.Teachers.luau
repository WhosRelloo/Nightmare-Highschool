--[[ (2.28) Teachers (server). Services.School.Teachers: a subject teacher at their desk is a witness in their room.
	- A combat hit by a student inside a classroom, while that room's teacher stands at the desk and can see the
	  attacker (a raycast from the head that ignores characters), books Fighting through Discipline.ReportIncident,
	  once per player per period, with the teacher's name as the witness.
	- A late or absent mark names the teacher of that room (Discipline asks NameFor).
	docs/expansion/13-Living-School.md §3.2.
	API: AtDesk(RoomId) -> (NpcId?, Model?), Sees(Model, Position) -> bool, NameFor(RoomId?) -> name, WitnessForTests ]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

local Cast = require(ReplicatedStorage.Config.Npcs)

local Shared = {}
local Local = {}
local Reported = {} :: { [Player]: string } -- the period key each player was last booked in
local DESK_RANGE = 4

local function Npcs() return require(ServerScriptService.Services.Social.Npcs) end
local function Places() return require(ServerScriptService.Services.Quests.Places) end
local function Clock() return require(ServerScriptService.Services.School.SchoolClock).GetState() end

-- the room each desk post belongs to (marks_staff.luau's posts; Hale's 2.24 post is the Room 102 desk)
local DESK_ROOM = { Sallow = `R102`; [`Hale@R103`] = `R103`; Pryce = `R104`; Whitlock = `R105`; Hale = `R102` }

function Shared.AtDesk(RoomId: string): (string?, Model?)
	local Seg = Clock().Segment
	if not (Seg and Seg.Kind == `Class`) then return nil, nil end
	for Id, Npc in Cast do
		if not Npc.Posts then continue end
		local Key = Npcs().PostKey(Id, Seg.Kind, Seg.Name)
		if Key and DESK_ROOM[Key] == RoomId then
			local M = Npcs().Get(Id)
			local Post = Places().Find(`NpcPost`, Key)
			local Root = M and M:FindFirstChild(`HumanoidRootPart`)
			if Root and Post and ((Root.Position - Post.Position) * Vector3.new(1, 0, 1)).Magnitude <= DESK_RANGE then
				return Id, M
			end
		end
	end
	return nil, nil
end

function Shared.Sees(M: Model, Position: Vector3): boolean
	local Head = M:FindFirstChild(`Head`)
	if not Head then return false end
	local Params = RaycastParams.new()
	Params.FilterType = Enum.RaycastFilterType.Exclude
	local Ignore = { M }
	for _, P in Players:GetPlayers() do if P.Character then table.insert(Ignore, P.Character) end end
	for _, Name in { `Live`, `NHSchedule`, `Regions` } do
		local F = workspace:FindFirstChild(Name)
		if F then table.insert(Ignore, F) end
	end
	Params.FilterDescendantsInstances = Ignore
	local Hit = workspace:Raycast(Head.Position, Position - Head.Position, Params)
	return Hit == nil or (Hit.Position - Position).Magnitude < 2
end

-- the teacher a room's period belongs to (by the timetable, not by who is standing there: attendance is recorded as
-- the period ends, often after the teacher has left); "Teacher" for a room with nobody's desk in it
function Shared.NameFor(RoomId: string?, PeriodName: string?): string
	if not RoomId then return `Teacher` end
	local Name = PeriodName or (Clock().Segment and Clock().Segment.Name) or ``
	for Id, Npc in Cast do
		if Npc.Posts then
			local Key = Npcs().PostKey(Id, `Class`, Name)
			if Key and DESK_ROOM[Key] == RoomId then return Npc.Name end
		end
	end
	return `Teacher`
end

-- the classroom by its own folder's bounds (workspace.School.R10x: the same box the desks and chairs belong to).
-- Not Features.Regions: its R10x boxes sit about one room east of these rooms (found in 2.28; logged, not changed here).
function Local.RoomOf(Player: Player): string?
	local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`)
	if not Root then return nil end
	for _, Room in { `R101`, `R102`, `R103`, `R104`, `R105` } do
		local F = workspace.School:FindFirstChild(Room)
		if F then
			local Ok, CF, Size = pcall(function() return F:GetBoundingBox() end)
			if Ok then
				local L = CF:PointToObjectSpace(Root.Position)
				if math.abs(L.X) <= Size.X / 2 and math.abs(L.Z) <= Size.Z / 2 and math.abs(L.Y) <= Size.Y / 2 + 4 then return Room end
			end
		end
	end
	return nil
end

function Local.PeriodKey(): string
	local S = Clock()
	return `{S.Day}:{S.SegmentIndex}`
end

-- returns what happened (for tests)
function Local.Witness(Player: Player): { [string]: any }
	local Room = Local.RoomOf(Player)
	if not Room then return { Room = false } end
	local Id, M = Shared.AtDesk(Room)
	if not (Id and M) then return { Room = Room; Teacher = false } end
	local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`)
	local Sees = Root ~= nil and Shared.Sees(M, Root.Position)
	if not Sees then return { Room = Room; Teacher = Id; Sees = false } end
	local Key = Local.PeriodKey()
	if Reported[Player] == Key then return { Room = Room; Teacher = Id; Sees = true; Reported = false; Already = true } end
	Reported[Player] = Key
	local Booked = require(ServerScriptService.Services.School.Discipline).ReportIncident({
		Type = `Fighting`; Suspect = Player; Witness = Cast[Id].Name; Position = Root.Position; Recognized = true;
	})
	return { Room = Room; Teacher = Id; Sees = true; Reported = Booked }
end

-- clears this player's period key first, so a test can book once more
function Shared.WitnessForTests(Player: Player, RoomId: string)
	local Out = { AtDesk = (Shared.AtDesk(RoomId)) or false }
	local W = Local.Witness(Player)
	for K, V in W do Out[K] = V end
	return Out
end
function Shared.ClearForTests(Player: Player) Reported[Player] = nil end

function Shared.OnStart()
	local Downed = require(ServerScriptService.Services.Features.Downed)
	Downed.OnDamage:Connect(function(_Target, _Damage, Attacker)
		local Player = Attacker and Players:GetPlayerFromCharacter(Attacker)
		if not Player then return end
		local Ok, Err = pcall(Local.Witness, Player)
		if not Ok then warn(`[Teachers] {Err}`) end
	end)
	Players.PlayerRemoving:Connect(function(P) Reported[P] = nil end)
end

return Shared
