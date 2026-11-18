--[[ (2.27) Roster (server). Services.Social.Roster: who the rostered students are (Config.Students), each one's
	seeded randomness (the same look every server), and the body Schedules made for them.
	Spec: docs/expansion/13-Living-School.md §2.2, §3.3 (2.28: Plan, WhereNow). Near(Pos, Radius) came in 2.29.
	API: All(), Get(Id), IsRostered(Id), Rng(Id), Bind(Id, S), Body(Id), SelfTestForTests()
	     Plan(SegName, Id, Day) -> { Room?, Skip }  (2.28) the room a student's set uses in a class segment
	     WhereNow(Id) -> { Embodied, At?, Activity? } (2.28) their body, or the spot they're at with no body ]]
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local Config = require(ReplicatedStorage.Config.Students)
local NpcBuilds = require(ReplicatedStorage.Config.NpcBuilds)
local Cliques = require(ReplicatedStorage.Config.Cliques)

local Shared = {}
local Bodies = {} :: { [string]: any }

function Shared.All() return Config.List end
function Shared.Get(Id: string) return Config.ById[Id] end
function Shared.IsRostered(Id: string?): boolean return Id ~= nil and Config.ById[Id] ~= nil end
function Shared.Rng(Id: string): Random return Random.new(NpcBuilds.Seed(`Roster|{Id}`)) end
function Shared.Bind(Id: string, S) Bodies[Id] = S end
function Shared.Body(Id: string) return Bodies[Id] end

-- (2.28) doc 13 §3.3: in each class period every subject room hosts one set; the sets rotate
Shared.ROTATION = {
	[`Period 1`] = { A = `R102`; B = `R103`; C = `R104`; D = `R105` };
	[`Period 2`] = { D = `R102`; A = `R103`; B = `R104`; C = `R105` };
	[`Period 3`] = { C = `R102`; D = `R103`; A = `R104`; B = `R105` };
	[`Period 4`] = { B = `R102`; C = `R103`; D = `R104`; A = `R105` };
}
-- homeroom: sets A and B in Room 101; C and D in Room 102 for Mr. Hale's register
Shared.HOMEROOM = { A = `R101`; B = `R101`; C = `R102`; D = `R102` }

function Shared.Plan(SegName: string, Id: string, Day: number)
	local E = Config.ById[Id]
	if not E then return { Room = nil; Skip = false } end
	if SegName == `Homeroom` then return { Room = Shared.HOMEROOM[E.Set]; Skip = false } end
	local Rot = Shared.ROTATION[SegName]
	if not Rot then return { Room = nil; Skip = false } end
	-- a Delinquent may skip; the same answer every time for this student, day and period
	local Skip = false
	if E.SkipChance then
		local R = Random.new(NpcBuilds.Seed(`Skip|{Id}|{Day}|{SegName}`))
		Skip = R:NextNumber() < E.SkipChance
	end
	return { Room = if Skip then nil else Rot[E.Set]; Skip = Skip }
end

-- (2.28) where a rostered student is: their body, or the spot they're at with no body (Schedules' sleepers)
function Shared.WhereNow(Id: string)
	local S = Bodies[Id]
	if not S then return { Embodied = false } end
	if S.Model and S.Root then return { Embodied = true; At = S.Root.Position; Activity = S.Activity } end
	return { Embodied = false; At = S.Asleep and S.Asleep.At; Activity = S.Activity }
end

-- (2.29) rostered students within Radius of Pos (their body, or where they are with no body)
function Shared.Near(Pos: Vector3?, Radius: number): { string }
	local Out = {}
	if not Pos then return Out end
	for _, E in Config.List do
		local W = Shared.WhereNow(E.Id)
		if W.At and (W.At - Pos).Magnitude <= Radius then table.insert(Out, E.Id) end
	end
	return Out
end

function Shared.SelfTestForTests()
	local Out = { Count = #Config.List; Bad = {} }
	local PerClique, PerSet, Seen = {}, {}, {}
	for _, E in Config.List do
		if Seen[E.Id] then table.insert(Out.Bad, `dup {E.Id}`) end
		Seen[E.Id] = true
		if not Cliques.Defs[E.Clique] then table.insert(Out.Bad, `clique {E.Id}`) end
		if not table.find(Config.Tempers, E.Temper) then table.insert(Out.Bad, `temper {E.Id}`) end
		if not table.find(Config.Sets, E.Set) then table.insert(Out.Bad, `set {E.Id}`) end
		if typeof(E.Bravery) ~= `number` or E.Bravery < 0 or E.Bravery > 1 then table.insert(Out.Bad, `bravery {E.Id}`) end
		if (E.SkipChance ~= nil) ~= (E.Clique == `Delinquents`) then table.insert(Out.Bad, `skip {E.Id}`) end
		if typeof(E.First) ~= `string` or typeof(E.Bio) ~= `string` then table.insert(Out.Bad, `text {E.Id}`) end
		PerClique[E.Clique] = (PerClique[E.Clique] or 0) + 1
		PerSet[E.Set] = (PerSet[E.Set] or 0) + 1
	end
	Out.CliquesOf3 = true
	for Id in Cliques.Defs do if PerClique[Id] ~= 3 then Out.CliquesOf3 = false end end
	Out.SetsOf6 = PerSet.A == 6 and PerSet.B == 6 and PerSet.C == 6 and PerSet.D == 6
	local A, B = Shared.Rng(`OdetteMarsh`), Shared.Rng(`OdetteMarsh`)
	Out.SeedStable = A:NextInteger(1, 1e6) == B:NextInteger(1, 1e6)
	Out.SeedDiffers = Shared.Rng(`OdetteMarsh`):NextInteger(1, 1e6) ~= Shared.Rng(`SilasPenwright`):NextInteger(1, 1e6)
	return Out
end

return Shared
