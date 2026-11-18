--[[ (2.27) Roster (server). Services.Social.Roster: who the rostered students are (Config.Students), each one's
	seeded randomness (the same look every server), and the body Schedules made for them.
	Spec: docs/expansion/13-Living-School.md §2.2. Timetable plans (Plan, WhereNow) come in 2.28; Near in 2.29.
	API: All(), Get(Id), IsRostered(Id), Rng(Id), Bind(Id, S), Body(Id), SelfTestForTests() ]]
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
