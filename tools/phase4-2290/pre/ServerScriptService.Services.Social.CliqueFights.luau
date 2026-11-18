--[[
	CliqueFights (server). Services.Social.CliqueFights   (Cliques Phase 2, 1.27; Config.Cliques.Fights)
	The cliques fight now, Bully style (owner, 2026-11-04: "full Bully-style rivalry").

	  Turf confrontations  Stay TurfLinger (8) seconds in the hangout of a clique that's Hostile to you and 2 of its
	                       members (3 at -70 or lower) come out of the group at you. One taunts you, then they attack.
	                       They fight only you, at their clique's tier (Config.Cliques Defs Tier). It ends when you get
	                       LetGoDistance (30) studs past the hangout ("And stay out!"), go down (they jeer), put them
	                       all down, or after 90 s. The same clique waits 2 minutes before doing it again.
	  Rival scuffles       At Break, Lunch, After School and in the Evening, at most every ScuffleEvery (240) s and only
	                       with a student within 120 studs to see it, one rival pair (Config.Cliques.RivalPairs) fights
	                       2v2 or 3v3 at one side's hangout: the defenders come out of their group, the rivals walk in.
	                       They're the regular combat AI and fight only each other. Hit one side and those fighters turn
	                       on you; each rival you put down is +6 with the side you're helping (the -8 for downing a
	                       member, and its rival's share, come from Social.Cliques), and +10 more if your side wins.
	                       It ends when a side is all down, after 60 s, or when a hall monitor arrives (school grounds
	                       only: School.HallMonitor.Respond). Students of those cliques nearby turn to watch
	                       (workspace attribute NHScuffleAt, read by Features.Schedules).
	The fighters are spawned for the event (AI.Spawn, dressed in the clique's clothes, named Config.Cliques Fighter)
	and walk off and despawn afterwards; the scheduled students keep their routine. Fighting where a monitor can see
	you is booked as usual (School.HallMonitor: Fighting).
	Phase 3 (1.28):
	  Turf wars            Win TurfWins (2) scuffles at a rival's hangout in one in-game day (6 AM to 6 AM) and your
	                       side holds it until the next 6 AM: the owners' students go elsewhere (Features.Schedules reads
	                       workspace NHTurfHolder_<Clique>), the holders hang out and defend there, and the region card
	                       says who holds it (workspace NHTurf_<RegionId>). The owners take it back by winning there once.
	                       Students who helped win the deciding scuffle get TurfBonus (+15) with the winners.
	  Backup               A student whose clique reward is unlocked (attribute CliqueReward_<Id>, Social.Cliques) and who
	                       is hit by an NPC near that clique's hangout or its students gets two of its members to fight the
	                       attacker, once every BackupCooldown (90) s; not in duels.
	Phase 5 (1.34): a student with NHGrudge_<Clique> (Social.CliqueShowdowns: a challenge they didn't answer) is confronted
	twice as often by that clique; a King / Queen of the School (NHKing) gets backup at every hangout.
	Phase 4 (1.33, Config.Cliques.Events):
	  Rumble days          About every RumbleEveryDays (3) in-game days, at 6 AM, a rival pair is picked (the most heated
	                       one yesterday, else at random) and announced for the next day's After School at the Commons
	                       (Social.CliqueEvents texts everyone). It starts when a student is within RumbleStartRange (160)
	                       studs of the venue, or 10 in-game minutes into After School: RumbleWaves (3) waves of RumbleSize
	                       (3) a side; a side's next wave walks in when its wave is all down. The hall monitor comes at
	                       RumbleMonitor (60) s ("Break it up!": they keep going); at RumbleStaff (120) s a coach walks over
	                       and ends it. The side that lost fewer fighters wins (or the side still standing). Joining in works
	                       as in a scuffle, with RumbleWin (+15) for the winners' helpers; the winners hold the losers'
	                       hangout until 6 AM the day after (Turf Until).
	  Feuds                Scuffles and rumbles per rival pair per event day (Feuds(), for the bulletin).
	  Pranks               Social.CliquePranks spawns its pranksters here (SpawnFighter with Event.Kind = "Prank" and
	                       Event.OnHit / Event.OnDowned callbacks).
	API: StartScuffle(Owner, Rival), Confront(Player, Clique), RecordWin(Owner, Rival, Winner), Turf(), State(),
	     StartRumble(A, B), PlanRumble(A, B, Day?), Rumble(), Feuds(); helpers SpawnFighter, Leave, Aim, Spots, Box, Floor,
	     Out, PlayerNear, OnSchoolGrounds, TurfDay, Announce.
]]

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local CollectionService = game:GetService(`CollectionService`)

local Config = require(ReplicatedStorage.Config.Cliques)
local NPCConfig = require(ReplicatedStorage.Config.NPC)
local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local TagService = require(ReplicatedStorage.Packages.Core.TagService)

local F = Config.Fights
local Shared = {}
local Local = {}
local Rng = Random.new()

local function svc(Path: string)
	local Node = ServerScriptService.Services
	for Part in Path:gmatch(`[^%.]+`) do Node = Node:FindFirstChild(Part) if not Node then return nil end end
	local Ok, Mod = pcall(require, Node)
	return Ok and Mod or nil
end

local Fighters = {} :: { [Model]: any } -- fighter -> { Npc, Clique, Event }
local Confronts = {} :: { [Player]: any }
local Cooldown = {} :: { [Player]: { [string]: number } }
local Linger = {} :: { [Player]: { [string]: number } }
local Scuffle = nil :: any
local LastScuffle = -math.huge
local Turf = {} :: { [string]: { Holder: string, Day: number } } -- owner clique -> who holds its hangout
local Wins = {} :: { [string]: any } -- owner clique -> { Day, [rival] = scuffles won there today }
local Backups = {} :: { [Player]: number } -- last backup per student
local E = Config.Events or {}
local Rumble = nil :: any            -- the rumble going on
local RumblePlan = nil :: any        -- { A, B, Day, Announced, Started? }: the next one
local LastRumbleDay = nil :: number? -- event day the last rumble was planned
local Feuds = {} :: { [number]: { [string]: any } } -- event day -> "A|B" -> { A, B, Count, Wins = { [clique] = n } }

---| places |---

function Local.Floor(At: Vector3): Vector3?
	local RP = RaycastParams.new()
	RP.FilterType = Enum.RaycastFilterType.Exclude
	local Ex = {}
	for _, N in { `Live`, `NHSchedule`, `NHAmbient`, `NHFx`, `Regions` } do local Fo = workspace:FindFirstChild(N) if Fo then table.insert(Ex, Fo) end end
	RP.FilterDescendantsInstances = Ex
	RP.RespectCanCollide = true
	local Hit = workspace:Raycast(At + Vector3.new(0, 6, 0), Vector3.new(0, -40, 0), RP)
	return if Hit and Hit.Normal.Y > 0.6 then Hit.Position else nil
end

function Local.Spots(Id: string): { Vector3 }
	local Out = {}
	for _, P in CollectionService:GetTagged(`NHCliqueSpot`) do
		if P:IsA(`BasePart`) and P:GetAttribute(`NHCliqueSpot`) == Id and P:IsDescendantOf(workspace) then
			table.insert(Out, Local.Floor(P.Position) or P.Position)
		end
	end
	return Out
end

function Local.Box(Id: string): BasePart?
	local Def = Config.Defs[Id]
	local Folder = workspace:FindFirstChild(`Regions`)
	local B = Def and Folder and Folder:FindFirstChild(Def.Hangout)
	return if B and B:IsA(`BasePart`) then B else nil
end

function Local.Inside(Root: BasePart, Box: BasePart, Extra: number): boolean
	local L = Box.CFrame:PointToObjectSpace(Root.Position)
	local H = Box.Size / 2 + Vector3.new(Extra, 6, Extra)
	return math.abs(L.X) <= H.X and math.abs(L.Y) <= H.Y and math.abs(L.Z) <= H.Z
end

function Local.OnSchoolGrounds(Id: string): boolean
	local Ok, Regions = pcall(require, ReplicatedStorage.Config.Regions)
	local Def = Config.Defs[Id]
	local R = Ok and Def and Regions.Defs and Regions.Defs[Def.Hangout]
	return R ~= nil and R.Kind ~= `Turf`
end

function Local.Root(Char: Model?): BasePart?
	return Char and Char:FindFirstChild(`HumanoidRootPart`) :: BasePart?
end

function Local.Out(Char: Model?): boolean -- down, dead or gone
	if not (Char and Char.Parent) then return true end
	local H = Char:FindFirstChildWhichIsA(`Humanoid`)
	if not H or H.Health <= 0 or H:GetAttribute(`Downed`) then return true end
	return StateManager.HasState(Char, { `Downed`, `Carried`, `Gripped` })
end

function Local.PlayerNear(Pos: Vector3, Range: number): Player?
	for _, P in Players:GetPlayers() do
		local R = Local.Root(P.Character)
		if R and P:GetAttribute(`InMainMenu`) ~= true and (R.Position - Pos).Magnitude <= Range then return P end
	end
	return nil
end

---| fighters |---

local TOP_EXTRA = {} -- (school tops come from the clique's Look; the client's dress code swaps them on turf)
function Local.Dress(Char: Model, Id: string)
	local App = require(ReplicatedStorage.UI.Appearance)
	local L = Config.Defs[Id].Look or {}
	local Look = App.Sanitize({})
	local Female = Rng:NextNumber() < 0.35
	Look.Body = if Female then 2 else 1
	Look.Skin = Rng:NextInteger(1, math.max(1, #App.Skins))
	local Tops = table.clone(L.Tops or {})
	if Female then for _, T in L.FemaleTops or {} do table.insert(Tops, T) end end
	for _, T in TOP_EXTRA do table.insert(Tops, T) end
	local Bottoms = if Female and L.FemaleBottoms then L.FemaleBottoms else L.Bottoms
	if #Tops > 0 then Look.Uniform = App.IndexOf(App.Uniforms, Tops[Rng:NextInteger(1, #Tops)]) or Look.Uniform end
	if Bottoms and #Bottoms > 0 then Look.Bottoms = App.IndexOf(App.BottomsList, Bottoms[Rng:NextInteger(1, #Bottoms)]) or Look.Bottoms end
	Look.Eyes = Rng:NextInteger(2, math.max(2, #App.Eyes))
	Look.EyeSet = if Female then 2 else 1
	if #App.Brows > 1 then Look.Brows = Rng:NextInteger(2, #App.Brows) end
	if #App.Mouths > 1 then Look.Mouth = Rng:NextInteger(2, #App.Mouths) end
	local Cat = ReplicatedStorage:FindFirstChild(`NHHairCatalog`)
	if Cat then
		local Pool = {}
		for _, H in Cat:GetChildren() do
			if H:GetAttribute(`Group`) == (if Female then `Female` else `Male`) then table.insert(Pool, H:GetAttribute(`AssetId`)) end
		end
		if #Pool > 0 then Look.HairId = Pool[Rng:NextInteger(1, #Pool)] end
	end
	Look.HairColor = Rng:NextInteger(1, math.max(1, #App.HairColors))
	Look._Idx = true
	pcall(App.ApplyTo, Char, Look)
end

local FIGHTER_HEALTH = { Easy = 60; Normal = 75; Hard = 90; Nightmare = 110 }

-- a clique member that fights: the regular combat AI at the clique's tier, picking no targets of its own
function Local.SpawnFighter(Id: string, At: Vector3, Event, FixedTarget)
	local AI = svc(`AI.AI`)
	local Def = Config.Defs[Id]
	if not (AI and Def) then return nil end
	local S = table.clone(NPCConfig.Default)
	S.Tier = Def.Tier or `Normal`
	S.Weapon = `Fist`
	S.AggroRange = 0.5 -- never picks up bystanders: targets come from threat (scuffles) or FixedTarget (confrontations)
	S.AttackRange = 10
	S.ChaseRange = 120
	S.PatrolSpeed = 10
	S.IdleWaitTime = 1e6
	S.CorpseTime = 3
	S.RespawnTime = nil
	S.FixedTarget = FixedTarget
	local Npc = AI.Spawn(workspace:FindFirstChild(`Live`) or workspace, nil, nil, S)
	local Char = Npc and Npc.Character
	if not Char then return nil end
	Char.Name = Def.Fighter or `{Def.Name} member`
	Char:SetAttribute(`Clique`, Id)
	Char:SetAttribute(`NHCliqueFighter`, Event.Kind)
	Char:PivotTo(CFrame.new(At + Vector3.new(0, 3, 0)) * CFrame.Angles(0, Rng:NextNumber(0, math.pi * 2), 0))
	Npc.HomeCFrame = Char:GetPivot()
	local Hum = Char:FindFirstChildWhichIsA(`Humanoid`)
	if Hum then
		Hum.DisplayName = Char.Name
		-- street fighters, not bosses: a scuffle should end with someone on the floor
		local HP = FIGHTER_HEALTH[S.Tier] or 75
		Hum.MaxHealth = HP
		Hum.Health = HP
	end
	Fighters[Char] = { Npc = Npc; Clique = Id; Event = Event }
	Char.AncestryChanged:Connect(function(_, Parent) if not Parent then Fighters[Char] = nil end end)
	task.spawn(Local.Dress, Char, Id)
	return Char, Npc
end

-- point a fighter at someone (a rival fighter or a player who hit it)
function Local.Aim(Char: Model, Target: Model, Amount: number?)
	local Info = Fighters[Char]
	if not Info or not Info.Npc then return end
	Info.Npc.ThreatTable = {}
	local AI = svc(`AI.AI`)
	if AI then AI.AddThreat(Char, Target, Amount or 1000) end
end

-- stop fighting and walk off; gone once nobody's near (or after 15 s), never while a student carries or grips it
function Local.Leave(Char: Model)
	local Info = Fighters[Char]
	if not Info or Info.Leaving then return end
	Info.Leaving = true
	local Npc = Info.Npc
	if Npc then
		if Npc.Target and TagService:HasTag(Npc.Target, `Agro`) == Char then pcall(function() TagService:RemoveTag(Npc.Target, `Agro`) end) end
		Npc.Target = nil
		Npc.TargetActionManager = nil
		Npc.ThreatTable = {}
		Npc.Plan = nil
		if Npc.Config then Npc.Config.FixedTarget = function() return nil end end
		local Ctrl = svc(`AI.AI.NPCController`)
		if Ctrl and Ctrl.SetState then pcall(Ctrl.SetState, Npc, `Idle`) end
		-- "home" is now somewhere away from the nearest student
		local R = Local.Root(Char)
		if R then
			local Away = R.Position + Vector3.new(Rng:NextNumber(-1, 1), 0, Rng:NextNumber(-1, 1)).Unit * 40
			local Near = Local.PlayerNear(R.Position, 60)
			local PR = Near and Local.Root(Near.Character)
			if PR then
				local D = (R.Position - PR.Position) * Vector3.new(1, 0, 1)
				if D.Magnitude > 0.5 then Away = R.Position + D.Unit * 40 end
			end
			Npc.HomeCFrame = CFrame.new(Local.Floor(Away) or Away)
		end
	end
	task.spawn(function()
		local T0 = os.clock()
		while Char.Parent do
			task.wait(1)
			local Held = StateManager.HasState(Char, { `Carried`, `Gripped` })
			local R = Local.Root(Char)
			local Alone = not (R and Local.PlayerNear(R.Position, 40))
			if not Held and (Alone or os.clock() - T0 > 15) then break end
			if os.clock() - T0 > 45 then break end
		end
		if Char.Parent then Char:Destroy() end
	end)
end

---| turf confrontations |---

function Shared.Confront(P: Player, Id: string, Standing: number?)
	if Confronts[P] then return false end
	local Def = Config.Defs[Id]
	local Box = Local.Box(Id)
	if not (Def and Box) then return false end
	local R = Local.Root(P.Character)
	if not R then return false end
	local Count = if (Standing or 0) <= -70 then F.ConfrontCrew[2] else F.ConfrontCrew[1]
	local Spots = Local.Spots(Id)
	table.sort(Spots, function(a, b) return (a - R.Position).Magnitude > (b - R.Position).Magnitude end)
	local Ev = { Kind = `Confront`; Player = P; Clique = Id; Fighters = {}; Started = os.clock() }
	Confronts[P] = Ev
	Cooldown[P] = Cooldown[P] or {}
	Cooldown[P][Id] = os.clock()
	local function Target() return if P.Parent then P.Character else nil end
	for I = 1, Count do
		local At = Spots[I] or Local.Floor(Box.Position + Vector3.new(Rng:NextNumber(-6, 6), 0, Rng:NextNumber(-6, 6))) or Box.Position
		local Char = Local.SpawnFighter(Id, At, Ev, Target)
		if Char then table.insert(Ev.Fighters, Char) end
	end
	if #Ev.Fighters == 0 then Confronts[P] = nil return false end
	local Cl = svc(`Social.Cliques`)
	task.delay(0.8, function() if Cl and Ev.Fighters[1] then Cl.Say(Ev.Fighters[1], Cl.Line(Id, `Taunt`)) end end)
	task.spawn(function()
		local Why = `Time`
		while os.clock() - Ev.Started < F.ConfrontTime do
			task.wait(1)
			local Char = P.Parent and P.Character
			local PR = Local.Root(Char)
			if not PR then Why = `Gone` break end
			local Down = Local.Out(Char)
			if Down then Why = `Down` break end
			local Standing = 0
			for _, Fi in Ev.Fighters do if not Local.Out(Fi) then Standing += 1 end end
			if Standing == 0 then Why = `Beaten` break end
			if not Local.Inside(PR, Box, F.LetGoDistance) then Why = `Away` break end
		end
		local Speaker = nil
		for _, Fi in Ev.Fighters do if not Local.Out(Fi) then Speaker = Fi break end end
		if Cl and Speaker then
			if Why == `Down` then Cl.Say(Speaker, Cl.Line(Id, `Jeer`)) elseif Why == `Away` then Cl.Say(Speaker, Cl.Line(Id, `Leave`)) end
		end
		task.wait(1.2)
		for _, Fi in Ev.Fighters do if Fi.Parent then Local.Leave(Fi) end end
		Ev.Result = Why
		Local.LastResult = `{Id} confronted {P.Name}: {Why} after {math.floor(os.clock() - Ev.Started)} s`
		Confronts[P] = nil
	end)
	return true
end

function Local.TurfStep(Dt: number)
	local Cl = svc(`Social.Cliques`)
	if not Cl then return end
	for _, P in Players:GetPlayers() do
		local R = Local.Root(P.Character)
		local Ok = R and P:GetAttribute(`InMainMenu`) ~= true and P:GetAttribute(`Slot`) ~= nil and not Local.Out(P.Character)
			and not P.Character:GetAttribute(`Dueling`) and not P.Character:GetAttribute(`Protected`)
			and not P.Character:GetAttribute(`NHShowdown`) -- (audit) no turf confrontation on top of a showdown
		local C = Ok and Cl.Get(P)
		Linger[P] = Linger[P] or {}
		for _, Id in Config.Order do
			local Box = C and Local.Box(Id)
			local Hostile = C and Config.Tier(C[Id] or 0) == `Hostile`
			-- (1.35) a member of their rival (Social.CliqueMembership: NHClique) gets the same treatment on their turf
			local Mine = P:GetAttribute(`NHClique`)
			if Mine and Config.Defs[Id].Rival == Mine then Hostile = true end
			if Box and Hostile and Local.Inside(R, Box, 0) then
				Linger[P][Id] = (Linger[P][Id] or 0) + Dt
				local Last = Cooldown[P] and Cooldown[P][Id] or -math.huge
				-- (1.34) a grudge (you didn't answer their leader's challenge): they come twice as often
				local Wait = F.ConfrontCooldown * (if P:GetAttribute(`NHGrudge_{Id}`) == true then 0.5 else 1)
				if Linger[P][Id] >= F.TurfLinger and os.clock() - Last >= Wait and not Confronts[P] then
					Linger[P][Id] = 0
					Shared.Confront(P, Id, C[Id])
				end
			else
				Linger[P][Id] = 0
			end
		end
	end
end

---| rival scuffles |---

function Local.Other(Ev, Id: string): string
	return if Id == Ev.A then Ev.B else Ev.A
end

-- a scuffle at Owner's hangout against Rival. If Rival holds that hangout, Rival defends it and the owners walk in.
function Shared.StartScuffle(Owner: string, Rival: string): boolean
	if Scuffle or Rumble then return false end
	local Held = Turf[Owner]
	local Defender, Attacker = Owner, Rival
	if Held and Held.Holder == Rival then Defender, Attacker = Rival, Owner end
	local Spots = Local.Spots(Owner)
	if #Spots < 2 then return false end
	local Venue = Vector3.zero
	for _, S in Spots do Venue += S end
	Venue /= #Spots
	local Size = Rng:NextInteger(F.ScuffleSize[1], F.ScuffleSize[2])
	local Ev = { Kind = `Scuffle`; A = Defender; B = Attacker; Owner = Owner; Venue = Venue; Sides = { [Defender] = {}; [Attacker] = {} };
		Help = {}; Started = os.clock() }
	Scuffle = Ev
	LastScuffle = os.clock()
	for I = 1, Size do
		local At = Spots[(I - 1) % #Spots + 1]
		local Char = Local.SpawnFighter(Defender, At, Ev, nil)
		if Char then table.insert(Ev.Sides[Defender], Char) end
	end
	-- the rivals walk in from one side
	local Ang = Rng:NextNumber(0, math.pi * 2)
	for I = 1, Size do
		local A = Ang + (I - (Size + 1) / 2) * 0.35
		local At = Local.Floor(Venue + Vector3.new(math.cos(A), 0, math.sin(A)) * 22) or Local.Floor(Venue + Vector3.new(math.cos(A), 0, math.sin(A)) * 12) or Venue
		local Char = Local.SpawnFighter(Attacker, At, Ev, nil)
		if Char then table.insert(Ev.Sides[Attacker], Char) end
	end
	workspace:SetAttribute(`NHScuffleAt`, Venue)
	local Cl = svc(`Social.Cliques`)
	task.delay(0.6, function()
		if Cl then
			if Ev.Sides[Attacker][1] then Cl.Say(Ev.Sides[Attacker][1], Cl.Line(Attacker, `Rally`)) end
			task.wait(0.9)
			if Ev.Sides[Defender][1] then Cl.Say(Ev.Sides[Defender][1], Cl.Line(Defender, `Rally`)) end
		end
	end)
	-- a hall monitor comes to break it up (school grounds only)
	if Local.OnSchoolGrounds(Owner) then
		task.delay(4, function()
			if Scuffle ~= Ev then return end
			local HM = svc(`School.HallMonitor`)
			if HM and HM.Respond then
				Ev.MonitorComing = HM.Respond(Venue, function() if Scuffle == Ev then Local.EndScuffle(Ev, `Monitor`) end end)
			end
		end)
	end
	task.spawn(function()
		while Scuffle == Ev do
			task.wait(0.5)
			Local.ScuffleStep(Ev)
		end
	end)
	return true
end

function Local.ScuffleStep(Ev)
	if os.clock() - Ev.Started > F.ScuffleTime then Local.EndScuffle(Ev, `Time`) return end
	local Up = {}
	for Id, List in Ev.Sides do
		Up[Id] = {}
		for _, Ch in List do if not Local.Out(Ch) then table.insert(Up[Id], Ch) end end
	end
	if #Up[Ev.A] == 0 or #Up[Ev.B] == 0 then
		Local.EndScuffle(Ev, `Won`, if #Up[Ev.A] > 0 then Ev.A elseif #Up[Ev.B] > 0 then Ev.B else nil)
		return
	end
	-- anyone without a live opponent picks the nearest standing rival (or keeps the student who hit it)
	for Id, List in Up do
		local Foes = Up[Local.Other(Ev, Id)]
		for _, Ch in List do
			local Info = Fighters[Ch]
			local T = Info and Info.Npc and Info.Npc.Target
			local Keep = T and not Local.Out(T) and (Players:GetPlayerFromCharacter(T) or table.find(Foes, T))
			if Info and not Keep then
				local R = Local.Root(Ch)
				local Best, BD = nil, math.huge
				for _, Fo in Foes do
					local FR = Local.Root(Fo)
					if R and FR and (FR.Position - R.Position).Magnitude < BD then Best, BD = Fo, (FR.Position - R.Position).Magnitude end
				end
				if Best then Local.Aim(Ch, Best) end
			end
		end
	end
end

function Local.EndScuffle(Ev, Why: string, Winner: string?)
	if Scuffle ~= Ev then return end
	Scuffle = nil
	Ev.Result = Why
	Ev.Winner = Winner
	Local.LastResult = `{Ev.A} vs {Ev.B}: {Why}{if Winner then ` ({Winner} won)` else ``} after {math.floor(os.clock() - Ev.Started)} s`
	workspace:SetAttribute(`NHScuffleAt`, nil)
	local Cl = svc(`Social.Cliques`)
	if Cl and Why == `Monitor` then
		for Id, List in Ev.Sides do
			for _, Ch in List do if not Local.Out(Ch) then Cl.Say(Ch, Cl.Line(Id, `Scatter`)) break end end
		end
	end
	if Winner then pcall(Shared.RecordWin, Ev.Owner or Ev.A, Local.Other(Ev, Ev.Owner or Ev.A), Winner, Ev) end
	Local.CountFeud(Ev.A, Ev.B, Winner)
	-- the winning side thanks the students who fought for it (and their leader's quest hears about it)
	if Cl and Winner then
		local Quests = svc(`Quests.Quests`)
		for P, H in Ev.Help do
			if P.Parent and H.Side == Winner and (H.Downs or 0) > 0 then
				pcall(Cl.Add, P, Winner, F.HelpWin, `Your side won the scuffle`)
				if Quests and Quests.Progress then pcall(Quests.Progress, P, `Scuffle`, Winner) end
			end
		end
	end
	task.delay(if Why == `Monitor` then 0.4 else 1.5, function()
		for _, List in Ev.Sides do for _, Ch in List do if Ch.Parent then Local.Leave(Ch) end end end
	end)
end

-- a student hit a fighter: it turns on them, and they're on the other side's team
function Local.OnHit(Target: Model, Damage: number, Attacker: Model?)
	local Victim = Players:GetPlayerFromCharacter(Target)
	if Victim then Local.Backup(Victim, Attacker) return end
	local Info = Fighters[Target]
	local P = Attacker and Players:GetPlayerFromCharacter(Attacker)
	if not (Info and P) or Info.Leaving then return end
	local Ev = Info.Event
	if Ev and Ev.Kind == `Prank` and Ev.OnHit then pcall(Ev.OnHit, P, Target) return end
	if Ev and ((Ev.Kind == `Scuffle` and Scuffle == Ev) or (Ev.Kind == `Rumble` and Rumble == Ev)) then
		local H = Ev.Help[P] or { Hits = {} }
		Ev.Help[P] = H
		H.Hits[Info.Clique] = (H.Hits[Info.Clique] or 0) + 1
		-- you're with whichever side you've hit less
		local Other = Local.Other(Ev, Info.Clique)
		H.Side = if (H.Hits[Other] or 0) < H.Hits[Info.Clique] then Other else Info.Clique
		if not (Info.Npc and Info.Npc.Target == Attacker) then Local.Aim(Target, Attacker, 5000) end
	end
end

function Local.OnDowned(Target: Model, Attacker: Model?)
	local Info = Fighters[Target]
	local P = Attacker and Players:GetPlayerFromCharacter(Attacker)
	if not (Info and P) or Info.Leaving then return end -- (audit) a fighter walking off can't fight back: no standing for it
	local Ev = Info.Event
	if Ev and Ev.Kind == `Prank` and Ev.OnDowned then pcall(Ev.OnDowned, P, Target) return end
	-- (2.7.3) only while that scuffle / rumble is still on, as OnHit checks (the 0.4-1.5 s before fighters walk off paid +6)
	if Ev and ((Ev.Kind == `Scuffle` and Scuffle == Ev) or (Ev.Kind == `Rumble` and Rumble == Ev)) then
		local H = Ev.Help[P] or { Hits = {} }
		Ev.Help[P] = H
		H.Downs = (H.Downs or 0) + 1
		local Cl = svc(`Social.Cliques`)
		local Side = Local.Other(Ev, Info.Clique)
		if Cl then pcall(Cl.Add, P, Side, F.HelpDown, `You fought for them`) end
	end
end

---| turf wars |---

function Local.TurfDay(): number?
	local Clock = svc(`School.SchoolClock`)
	local Ok, State = pcall(function() return Clock.GetState() end)
	if not (Ok and State and State.Day) then return nil end
	return if (State.Hour or 12) >= 6 then State.Day else State.Day - 1
end

function Local.Announce(Pos: Vector3?, Title: string, Text: string)
	local N = svc(`Features.Notifications`)
	if not N then return end
	for _, P in Players:GetPlayers() do
		local R = Local.Root(P.Character)
		if R and (not Pos or (R.Position - Pos).Magnitude <= 220) then
			pcall(N.Notify, P, { Title = Title; Text = Text; Kind = `Info`; Duration = 5 })
		end
	end
end

function Local.SetTurf(Owner: string, Holder: string?, Until: number?)
	local Def = Config.Defs[Owner]
	Turf[Owner] = if Holder then { Holder = Holder; Day = Local.TurfDay() or 0; Until = Until } else nil
	workspace:SetAttribute(`NHTurfHolder_{Owner}`, Holder)
	if Def then workspace:SetAttribute(`NHTurf_{Def.Hangout}`, if Holder then Config.Defs[Holder].Name else nil) end
end

-- a scuffle at Owner's hangout ended with Winner on top: count it toward the turf
function Shared.RecordWin(Owner: string, Rival: string, Winner: string, Ev)
	local Day = Local.TurfDay() or 0
	local Held = Turf[Owner]
	local Cl = svc(`Social.Cliques`)
	local OwnDef, RivDef = Config.Defs[Owner], Config.Defs[Rival]
	if not (OwnDef and RivDef) then return end
	local function thank(Side: string, Amount: number, Why: string)
		if not (Cl and Ev) then return end
		for P, H in Ev.Help do
			if P.Parent and H.Side == Side and (H.Downs or 0) > 0 then pcall(Cl.Add, P, Side, Amount, Why) end
		end
	end
	if Held and Held.Holder == Rival then
		if Winner == Owner then
			Local.SetTurf(Owner, nil)
			Local.Announce(Ev and Ev.Venue, `{OwnDef.HangoutName} is back`, `{OwnDef.Name} took back {OwnDef.HangoutName} from {RivDef.Name}.`)
			thank(Owner, F.TurfBonus, `You helped take back {OwnDef.HangoutName}`)
		end
		return
	end
	local W = Wins[Owner]
	if not W or W.Day ~= Day then W = { Day = Day } Wins[Owner] = W end
	if Winner == Rival then
		W[Rival] = (W[Rival] or 0) + 1
		if W[Rival] >= F.TurfWins then
			W[Rival] = 0
			Local.SetTurf(Owner, Rival)
			Local.Announce(Ev and Ev.Venue, `Turf taken`, `{RivDef.Name} took {OwnDef.HangoutName}. It's theirs until morning.`)
			thank(Rival, F.TurfBonus, `You helped take {OwnDef.HangoutName}`)
		end
	elseif Winner == Owner then
		W[Rival] = 0
	end
end

function Shared.Turf()
	local Out = {}
	for Owner, T in Turf do Out[Owner] = T.Holder end
	return Out
end

function Local.TurfTick()
	local Day = Local.TurfDay()
	if not Day then return end
	for Owner, T in Turf do
		if Day > (T.Until or T.Day) or Day < T.Day then
			local OwnDef = Config.Defs[Owner]
			Local.SetTurf(Owner, nil)
			if OwnDef then Local.Announce(nil, `{OwnDef.HangoutName} is back`, `Morning: {OwnDef.Name} have {OwnDef.HangoutName} again.`) end
		end
	end
end

---| backup |---

function Local.Backup(P: Player, Attacker: Model?)
	local Char = P.Character
	local R = Local.Root(Char)
	if not (R and Attacker and Attacker.Parent) or Players:GetPlayerFromCharacter(Attacker) then return end
	if Char:GetAttribute(`Dueling`) or Char:GetAttribute(`NHShowdown`) or Local.Out(Attacker) then return end -- (audit) showdowns are 1-on-1
	if os.clock() - (Backups[P] or -math.huge) < F.BackupCooldown then return end
	local Mine = Fighters[Attacker]
	-- (2.7.3) the attacker's clique: an event fighter's, else any tagged NPC's (the street crews are Delinquents), so a
	-- clique never sends backup against its own (the street crews carry no attribute: Config.Npcs maps them by name)
	local AttackerClique = (Mine and Mine.Clique) or Attacker:GetAttribute(`Clique`) or Config.Npcs[Attacker.Name]
	for _, Id in Config.Order do
		-- (1.34) King / Queen of the School: backup at every clique's hangout
		if (P:GetAttribute(`CliqueReward_{Id}`) == true or P:GetAttribute(`NHKing`) == true or P:GetAttribute(`NHClique`) == Id) and AttackerClique ~= Id then
			local Box = Local.Box(Id)
			local Near = Box and Local.Inside(R, Box, 20)
			if P:GetAttribute(`NHClique`) == Id then Near = true end -- (1.35) members: backup anywhere
			if not Near then
				local Sched = workspace:FindFirstChild(`NHSchedule`)
				for _, M in (Sched and Sched:GetChildren() or {}) do
					local MR = M:GetAttribute(`Clique`) == Id and Local.Root(M)
					if MR and (MR.Position - R.Position).Magnitude <= 30 then Near = true break end
				end
			end
			if Near then
				Backups[P] = os.clock()
				local Ev = { Kind = `Backup`; Player = P; Clique = Id; Fighters = {}; Started = os.clock() }
				for I = 1, 2 do
					local A = Rng:NextNumber(0, math.pi * 2)
					local At = Local.Floor(R.Position + Vector3.new(math.cos(A), 0, math.sin(A)) * 12) or Local.Floor(R.Position) or R.Position
					local F2 = Local.SpawnFighter(Id, At, Ev, nil)
					if F2 then table.insert(Ev.Fighters, F2) Local.Aim(F2, Attacker, 5000) end
				end
				local Cl = svc(`Social.Cliques`)
				if Cl and Ev.Fighters[1] then Cl.Say(Ev.Fighters[1], Cl.Line(Id, `Backup`) or Cl.Line(Id, `Rally`)) end
				task.spawn(function()
					while os.clock() - Ev.Started < 40 do
						task.wait(1)
						if Local.Out(Attacker) then break end
						local AR, PR = Local.Root(Attacker), Local.Root(P.Character)
						if not (AR and PR) or (AR.Position - PR.Position).Magnitude > 80 then break end
					end
					task.wait(1)
					for _, Fi in Ev.Fighters do if Fi.Parent then Local.Leave(Fi) end end
				end)
				return
			end
		end
	end
end

-- (1.28) cliques a nearby student has a leader's scuffle quest for: those scuffles come sooner, near them
function Local.Wanted(): { [string]: Player }
	local Out = {}
	local Data = svc(`Player.Data`)
	local QCfg = require(ReplicatedStorage.Config.Quests)
	for _, P in Players:GetPlayers() do
		local Profile = Data and Data.GetProfile(P)
		local Active = Profile and Profile.Quests and Profile.Quests.Active
		for Id, D in Config.Defs do
			local Q = D.Quests and D.Quests[2]
			local Def = Q and QCfg.Quests[Q]
			if Active and Active[Q] and Def and Def.Objectives[1] and Def.Objectives[1].Type == `Scuffle` then Out[Id] = P end
		end
	end
	return Out
end

function Local.ScuffleTick()
	if Scuffle or Rumble then return end
	local Wanted = Local.Wanted()
	local Every = if next(Wanted) then math.min(F.ScuffleEvery, 60) else F.ScuffleEvery
	if os.clock() - LastScuffle < Every then return end
	local Clock = svc(`School.SchoolClock`)
	local Ok, State = pcall(function() return Clock.GetState() end)
	if not (Ok and State and State.Segment and F.ScuffleKinds[State.Segment.Kind]) then return end
	local Options = {}
	for _, Pair in Config.RivalPairs do
		for _, Order in { { Pair[1], Pair[2] }, { Pair[2], Pair[1] } } do
			local Spots = Local.Spots(Order[1])
			if #Spots >= 2 then
				local C = Vector3.zero
				for _, S in Spots do C += S end
				C /= #Spots
				if Local.PlayerNear(C, F.ScuffleSeeRange) then table.insert(Options, Order) end
			end
		end
	end
	if #Options == 0 then return end
	local Preferred = {}
	for _, O in Options do if Wanted[O[1]] or Wanted[O[2]] then table.insert(Preferred, O) end end
	if #Preferred > 0 then Options = Preferred end
	local Pick = Options[Rng:NextInteger(1, #Options)]
	Shared.StartScuffle(Pick[1], Pick[2])
end

function Shared.State()
	local Out = { Confronts = {}; Scuffle = nil; Fighters = 0 }
	for P, Ev in Confronts do
		table.insert(Out.Confronts, { Player = P.Name; Clique = Ev.Clique; Fighters = #Ev.Fighters; Age = math.floor(os.clock() - Ev.Started) })
	end
	if Scuffle then
		local Up = {}
		for Id, List in Scuffle.Sides do
			local N = 0
			for _, Ch in List do if not Local.Out(Ch) then N += 1 end end
			Up[Id] = N
		end
		Out.Scuffle = { A = Scuffle.A; B = Scuffle.B; Up = Up; Age = math.floor(os.clock() - Scuffle.Started); Monitor = Scuffle.MonitorComing }
	end
	for _ in Fighters do Out.Fighters += 1 end
	Out.LastResult = Local.LastResult
	Out.Turf = Shared.Turf()
	Out.Rumble = Shared.Rumble()
	return Out
end

---| feuds (1.33) |---

function Local.CountFeud(A: string, B: string, Winner: string?)
	local Day = Local.TurfDay() or 0
	local Key = if A < B then `{A}|{B}` else `{B}|{A}`
	Feuds[Day] = Feuds[Day] or {}
	local F2 = Feuds[Day][Key] or { A = if A < B then A else B; B = if A < B then B else A; Count = 0; Wins = {} }
	Feuds[Day][Key] = F2
	F2.Count += 1
	if Winner then F2.Wins[Winner] = (F2.Wins[Winner] or 0) + 1 end
	for D in Feuds do if D < Day - 2 then Feuds[D] = nil end end
end

-- today's feuds (or another event day's): { { A, B, Count, Wins } }, most heated first
function Shared.Feuds(Day: number?)
	local Out = {}
	for _, F2 in Feuds[Day or Local.TurfDay() or 0] or {} do table.insert(Out, F2) end
	table.sort(Out, function(X, Y) return X.Count > Y.Count end)
	return Out
end

---| rumble days (1.33) |---

-- where a rumble happens: the venue clique's gathering spots (the Commons), and its centre
function Local.RumbleVenue(): ({ Vector3 }, Vector3?)
	local Spots = Local.Spots(E.RumbleVenue or `Ordinary`)
	if #Spots == 0 then Spots = Local.Spots(`Ordinary`) end
	if #Spots == 0 then return Spots, nil end
	local C = Vector3.zero
	for _, S in Spots do C += S end
	return Spots, C / #Spots
end

function Local.RumbleWave(Ev, Id: string)
	Ev.Waves[Id] += 1
	local Side = if Id == Ev.A then -1 else 1
	local Dir = Ev.Axis * Side
	local Perp = Vector3.new(-Dir.Z, 0, Dir.X)
	for I = 1, (E.RumbleSize or 3) do
		local Off = Dir * 24 + Perp * ((I - ((E.RumbleSize or 3) + 1) / 2) * 4)
		local At = Local.Floor(Ev.Venue + Off) or Local.Floor(Ev.Venue + Dir * 12) or Ev.Venue
		local Char = Local.SpawnFighter(Id, At, Ev, nil)
		if Char then table.insert(Ev.Sides[Id], Char) end
	end
	local Cl = svc(`Social.Cliques`)
	local First = Ev.Sides[Id][#Ev.Sides[Id]]
	if Cl and First then task.delay(0.5, function() Cl.Say(First, Cl.Line(Id, `Rally`)) end) end
end

function Shared.StartRumble(A: string, B: string): boolean
	if Rumble or Scuffle then return false end
	if not (Config.Defs[A] and Config.Defs[B]) then return false end
	local Spots, Venue = Local.RumbleVenue()
	if not Venue then return false end
	local Ang = Rng:NextNumber(0, math.pi * 2)
	local Ev = { Kind = `Rumble`; A = A; B = B; Venue = Venue; Axis = Vector3.new(math.cos(Ang), 0, math.sin(Ang));
		Sides = { [A] = {}; [B] = {} }; Waves = { [A] = 0; [B] = 0 }; Fallen = {}; Lost = { [A] = 0; [B] = 0 }; Help = {}; Started = os.clock() }
	Rumble = Ev
	if RumblePlan then RumblePlan.Started = true end
	Local.RumbleWave(Ev, A)
	Local.RumbleWave(Ev, B)
	workspace:SetAttribute(`NHScuffleAt`, Venue)
	workspace:SetAttribute(`NHRumble`, `{A}|{B}`)
	Local.Announce(Venue, `Rumble!`, `{Config.Defs[A].Name} and {Config.Defs[B].Name} are fighting at {Config.Defs[E.RumbleVenue or `Ordinary`].HangoutName}.`)
	-- the hall monitor comes first (they don't stop for one monitor), then a coach ends it
	task.delay(E.RumbleMonitor or 60, function()
		if Rumble ~= Ev then return end
		local HM = svc(`School.HallMonitor`)
		if HM and HM.Respond then Ev.MonitorComing = HM.Respond(Venue, function()
			if Rumble ~= Ev then return end
			local Cl = svc(`Social.Cliques`)
			for Id, List in Ev.Sides do
				for _, Ch in List do if not Local.Out(Ch) then if Cl then Cl.Say(Ch, `There's only one of them! Keep going!`) end break end end
				break
			end
		end) end
	end)
	task.delay(E.RumbleStaff or 120, function() if Rumble == Ev then Local.SendCoach(Ev) end end)
	task.spawn(function()
		while Rumble == Ev do
			task.wait(0.5)
			Local.RumbleStep(Ev)
		end
	end)
	return true
end

function Local.RumbleStep(Ev)
	if os.clock() - Ev.Started > (E.RumbleTime or 240) then Local.EndRumble(Ev, `Time`) return end
	-- a fighter who goes down is out of the rumble for good (downed fighters get up again later): they leave
	local Up = {}
	for Id, List in Ev.Sides do
		Up[Id] = {}
		for _, Ch in List do
			if Ev.Fallen[Ch] then continue end
			if Local.Out(Ch) then
				Ev.Fallen[Ch] = true
				Ev.Lost[Id] += 1
				task.delay(4, function() if Ch.Parent then Local.Leave(Ch) end end)
			else
				table.insert(Up[Id], Ch)
			end
		end
	end
	for _, Id in { Ev.A, Ev.B } do
		if #Up[Id] == 0 then
			if Ev.Waves[Id] < (E.RumbleWaves or 3) then
				Local.RumbleWave(Ev, Id)
			else
				Local.EndRumble(Ev, `Won`, Local.Other(Ev, Id))
				return
			end
		end
	end
	-- same targeting as a scuffle
	for Id, List in Up do
		local Foes = Up[Local.Other(Ev, Id)]
		for _, Ch in List do
			local Info = Fighters[Ch]
			local T = Info and Info.Npc and Info.Npc.Target
			local Keep = T and not Local.Out(T) and (Players:GetPlayerFromCharacter(T) or table.find(Foes, T))
			if Info and not Keep then
				local R = Local.Root(Ch)
				local Best, BD = nil, math.huge
				for _, Fo in Foes do
					local FR = Local.Root(Fo)
					if R and FR and (FR.Position - R.Position).Magnitude < BD then Best, BD = Fo, (FR.Position - R.Position).Magnitude end
				end
				if Best then Local.Aim(Ch, Best) end
			end
		end
	end
end

-- a coach walks over and ends it (the school has no teachers on the grounds; the coaches are close by)
function Local.SendCoach(Ev)
	local Live = workspace:FindFirstChild(`Live`)
	local Best, BD = nil, math.huge
	for _, M in (Live and Live:GetChildren() or {}) do
		local R = M:IsA(`Model`) and Local.Root(M)
		if R and string.find(M.Name, `^Coach `) and not Local.Out(M) then
			local D = (R.Position - Ev.Venue).Magnitude
			if D < BD then Best, BD = M, D end
		end
	end
	local Cl = svc(`Social.Cliques`)
	local function finish(Speaker)
		if Rumble ~= Ev then return end
		if Cl and Speaker then Cl.Say(Speaker, `That's ENOUGH! Everyone, out! Now!`) end
		Local.EndRumble(Ev, `Staff`)
	end
	if not Best then finish(nil) return end
	local Hum = Best:FindFirstChildWhichIsA(`Humanoid`)
	local R = Local.Root(Best)
	if not (Hum and R) or R.Anchored then finish(Best) return end
	local Home = R.CFrame
	Ev.Coach = Best.Name
	task.spawn(function()
		local T0 = os.clock()
		while Rumble == Ev and os.clock() - T0 < 25 do
			Hum:MoveTo(Ev.Venue)
			if (R.Position - Ev.Venue).Magnitude <= 18 then break end
			task.wait(0.5)
		end
		finish(Best)
		task.wait(2)
		local T1 = os.clock()
		while Best.Parent and os.clock() - T1 < 30 and (R.Position - Home.Position).Magnitude > 3 do
			Hum:MoveTo(Home.Position)
			task.wait(0.5)
		end
		if Best.Parent then pcall(function() Best:PivotTo(Home) end) end
	end)
end

function Local.EndRumble(Ev, Why: string, Winner: string?)
	if Rumble ~= Ev then return end
	Rumble = nil
	workspace:SetAttribute(`NHScuffleAt`, nil)
	workspace:SetAttribute(`NHRumble`, nil)
	if not Winner then
		-- the side that lost fewer fighters (counting every wave)
		local Lost = Ev.Lost
		if Lost[Ev.A] < Lost[Ev.B] then Winner = Ev.A elseif Lost[Ev.B] < Lost[Ev.A] then Winner = Ev.B end
	end
	Ev.Result = Why
	Ev.Winner = Winner
	Local.LastResult = `Rumble {Ev.A} vs {Ev.B}: {Why}{if Winner then ` ({Winner} won)` else ``} after {math.floor(os.clock() - Ev.Started)} s`
	Local.LastRumble = { A = Ev.A; B = Ev.B; Winner = Winner; Why = Why }
	Local.CountFeud(Ev.A, Ev.B, Winner)
	local Cl = svc(`Social.Cliques`)
	if Cl then
		for Id, List in Ev.Sides do
			for _, Ch in List do if not Local.Out(Ch) then Cl.Say(Ch, Cl.Line(Id, if Id == Winner then `Rally` else `Scatter`)) break end end
		end
	end
	if Winner then
		local Loser = Local.Other(Ev, Winner)
		local LDef, WDef = Config.Defs[Loser], Config.Defs[Winner]
		local Day = Local.TurfDay() or 0
		Local.SetTurf(Loser, Winner, Day + 1)
		Local.Announce(nil, `Rumble over`, `{WDef.Name} won. They hold {LDef.HangoutName} until tomorrow night.`)
		local Quests = svc(`Quests.Quests`)
		for P, H in Ev.Help do
			if P.Parent and H.Side == Winner and (H.Downs or 0) > 0 then
				if Cl then pcall(Cl.Add, P, Winner, E.RumbleWin or 15, `Your side won the rumble`) end
				if Quests and Quests.Progress then pcall(Quests.Progress, P, `Scuffle`, Winner) end
			end
		end
	else
		Local.Announce(nil, `Rumble over`, `Nobody won. {Config.Defs[Ev.A].Name} and {Config.Defs[Ev.B].Name} will be back.`)
	end
	task.delay(1.2, function()
		for _, List in Ev.Sides do for _, Ch in List do if Ch.Parent then Local.Leave(Ch) end end end
	end)
end

function Shared.Rumble()
	local Out = { Plan = nil; Live = nil; Last = Local.LastRumble }
	if RumblePlan then Out.Plan = { A = RumblePlan.A; B = RumblePlan.B; Day = RumblePlan.Day; Today = RumblePlan.Day == Local.TurfDay() } end
	if Rumble then
		local Up, Waves = {}, {}
		for Id, List in Rumble.Sides do
			local N = 0
			for _, Ch in List do if not Local.Out(Ch) and not Rumble.Fallen[Ch] then N += 1 end end
			Up[Id] = N
			Waves[Id] = (E.RumbleWaves or 3) - Rumble.Waves[Id]
		end
		Out.Live = { A = Rumble.A; B = Rumble.B; Up = Up; WavesLeft = Waves; Lost = table.clone(Rumble.Lost); Age = math.floor(os.clock() - Rumble.Started);
			Coach = Rumble.Coach; Monitor = Rumble.MonitorComing }
	end
	return Out
end

-- plan the next rumble for Day (default: tomorrow) and tell everyone (Social.CliqueEvents)
function Shared.PlanRumble(A: string?, B: string?, Day: number?)
	local Today = Local.TurfDay() or 0
	if not (A and B) then
		local Yesterday = Shared.Feuds(Today - 1)[1] or Shared.Feuds(Today)[1]
		if Yesterday then
			A, B = Yesterday.A, Yesterday.B
		else
			local Pair = Config.RivalPairs[Rng:NextInteger(1, #Config.RivalPairs)]
			A, B = Pair[1], Pair[2]
		end
	end
	RumblePlan = { A = A; B = B; Day = Day or (Today + 1) }
	LastRumbleDay = Today
	local Ev = svc(`Social.CliqueEvents`)
	if Ev and Ev.RumblePlanned then pcall(Ev.RumblePlanned, RumblePlan) end
	return RumblePlan
end

function Local.RumbleTick()
	local Today = Local.TurfDay()
	if not Today then return end
	if RumblePlan and RumblePlan.Day < Today then RumblePlan = nil end
	if not RumblePlan and (LastRumbleDay == nil or Today - LastRumbleDay >= (E.RumbleEveryDays or 3)) then
		Shared.PlanRumble(nil, nil, Today + 1)
		return
	end
	if not RumblePlan or RumblePlan.Started or RumblePlan.Day ~= Today or Rumble then return end
	local Clock = svc(`School.SchoolClock`)
	local Ok, State = pcall(function() return Clock.GetState() end)
	if not (Ok and State and State.Segment and State.Segment.Kind == `AfterSchool`) then RumblePlan.Seen = nil return end
	RumblePlan.Seen = RumblePlan.Seen or os.clock()
	local _, Venue = Local.RumbleVenue()
	local Wait = 10 * require(ReplicatedStorage.Functions.SchoolTime).SecondsPerGameMinute()
	if Venue and (Local.PlayerNear(Venue, E.RumbleStartRange or 160) or os.clock() - RumblePlan.Seen >= Wait) then
		if Scuffle then return end
		Shared.StartRumble(RumblePlan.A, RumblePlan.B)
	end
end

---| helpers for Social.CliquePranks |---
Shared.SpawnFighter = function(...) return Local.SpawnFighter(...) end
Shared.Leave = function(...) return Local.Leave(...) end
Shared.Aim = function(...) return Local.Aim(...) end
Shared.Spots = function(...) return Local.Spots(...) end
Shared.Box = function(...) return Local.Box(...) end
Shared.Floor = function(...) return Local.Floor(...) end
Shared.Out = function(...) return Local.Out(...) end
Shared.PlayerNear = function(...) return Local.PlayerNear(...) end
Shared.OnSchoolGrounds = function(...) return Local.OnSchoolGrounds(...) end
Shared.TurfDay = function() return Local.TurfDay() end
Shared.Announce = function(...) return Local.Announce(...) end
Shared.Inside = function(...) return Local.Inside(...) end
Shared.NpcOf = function(Char) local I = Fighters[Char] return I and I.Npc end -- (1.35) the crew follows you

function Shared.OnStart()
	local Downed = svc(`Features.Downed`)
	if Downed then
		if Downed.OnDamage then Downed.OnDamage:Connect(function(T, D, A) pcall(Local.OnHit, T, D, A) end) end
		if Downed.OnDowned then Downed.OnDowned:Connect(function(T, A) pcall(Local.OnDowned, T, A) end) end
	end
	Players.PlayerRemoving:Connect(function(P) Cooldown[P] = nil Linger[P] = nil Backups[P] = nil end)
	task.spawn(function()
		local Acc = 0
		while true do
			local Dt = task.wait(1)
			pcall(Local.TurfStep, Dt)
			Acc += Dt
			if Acc >= 5 then Acc = 0 pcall(Local.ScuffleTick) pcall(Local.TurfTick) pcall(Local.RumbleTick) end
		end
	end)
end

return Shared
