--[[
	CliqueShowdowns (server). Services.Social.CliqueShowdowns   (Cliques Phase 5, 1.34; Config.Cliques.Showdown)
	Bully's chapter bosses, our way: beat a clique's leader one on one and the clique respects you.

	  Who can      As a friend: Friendly with the clique and its leader's quest 2 done. Ask the leader ("I want to test
	               myself."): the Showdown<Clique> quest starts. As a foe: Hostile with the clique. Once a day the leader texts
	               you a challenge (Challenge line) and the quest starts by itself; answer it After School or in the Evening.
	               Not again the same event day after a loss or a forfeit. A won showdown is done for good.
	  The fight    Walk into the clique's hangout (outside class; a challenge only After School / Evening): the real leader
	               steps aside and a fighter in their look (NpcLooks) takes their place at their LeaderTier, with
	               LeaderHealth. RingSize (5) members stand round you, shouting. At half health the leader calls Backup (2)
	               of them in (Call line). Down the leader: you win. Go down: you lose. Get ForfeitDistance (30) studs past
	               the hangout: a forfeit. The hangout is CombatAllowed while it lasts (the hall monitor leaves it alone).
	  Win          The clique goes to Respected (60) if it was lower, the leader says their Beaten line, the quest is done
	               (+50 Yen). PlayerData.Social.Showdowns.Won[<clique>] = event day.
	  Lose         Their Gloat line; try again on a later day. A Hostile leader's win costs FoeLoss (-5) more.
	  No-show      A challenge not answered by the end of the Evening fails, and that clique's crews confront you twice as
	               often the next day (Player attribute NHGrudge_<clique>, read by CliqueFights).
	  King         All eight beaten: King (or Queen) of the School: the title, the Player attribute NHKing (10% off at every
	               shop: Config.Cliques.PriceFactor; backup at every hangout: CliqueFights), a text from every leader (Crown),
	               and the Midnight Bell's front page (Features.Phone Gazette).
	API: CanChallenge(Player, Clique), StartFight(Player, Clique, Path?), State(), Summary(Player), WinForTests(Player, Clique).
]]

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local CollectionService = game:GetService(`CollectionService`)

local Config = require(ReplicatedStorage.Config.Cliques)
local QConfig = require(ReplicatedStorage.Config.Quests)
local NPCConfig = require(ReplicatedStorage.Config.NPC)

local S = Config.Showdown
local Shared = {}
local Local = {}
local Rng = Random.new()

local function svc(Path: string)
	local Node = ServerScriptService.Services
	for Part in Path:gmatch(`[^%.]+`) do Node = Node:FindFirstChild(Part) if not Node then return nil end end
	local Ok, Mod = pcall(require, Node)
	return Ok and Mod or nil
end

-- clique -> leader NpcId and quest id
local LeaderNpc, QuestFor = {}, {}
for Id, Def in QConfig.Quests do
	if Def.Showdown and Def.Giver then LeaderNpc[Def.Showdown] = Def.Giver QuestFor[Def.Showdown] = Id end
end

local Fights = {} :: { [string]: any } -- clique -> the fight going on
local Pending = {} :: { [Player]: { [string]: string } } -- clique -> "Friend" | "Foe" (quest started, fight not yet)

---| data (PlayerData.Social.Showdowns, through Social.Reputation like the clique standing) |---

function Local.Data(P: Player)
	local Rep = svc(`Social.Reputation`)
	local Social = Rep and Rep.Get(P)
	if not Social then return nil end
	local D = Social.Showdowns
	if typeof(D) ~= `table` then D = {} Social.Showdowns = D end
	for _, K in { `Won`, `Tried`, `Challenged`, `NoShow`, `FoeQuest` } do -- (audit) FoeQuest: the day of the Foe challenge the active quest came from
		if typeof(D[K]) ~= `table` then D[K] = {} end
	end
	return D
end

function Local.Save(P: Player)
	local Rep = svc(`Social.Reputation`)
	if Rep and Rep.Sync then pcall(Rep.Sync, P) end
end

function Local.Day(): number?
	local Clock = svc(`School.SchoolClock`)
	local Ok, State = pcall(function() return Clock.GetState() end)
	return if Ok then Config.EventDay(State) else nil
end

function Local.Segment(): string?
	local Clock = svc(`School.SchoolClock`)
	local Ok, State = pcall(function() return Clock.GetState() end)
	return Ok and State and State.Segment and State.Segment.Kind or nil
end

function Local.Standing(P: Player, Id: string): number
	local Cl = svc(`Social.Cliques`)
	local C = Cl and Cl.Get(P)
	return C and C[Id] or 0
end

---| who can |---

-- "Friend" | "Foe" | nil, and why not
function Shared.CanChallenge(P: Player, Id: string): (boolean, string?, string?)
	local D = Local.Data(P)
	local Day = Local.Day()
	if not (D and Day and Config.Defs[Id]) then return false, `Locked` end
	if D.Won[Id] then return false, `Done` end
	if D.Tried[Id] == Day then return false, `DoneToday` end
	local Value = Local.Standing(P, Id)
	local Tier = Config.Tier(Value)
	if Tier == `Hostile` then
		if D.Challenged[Id] == Day then return true, `Ok`, `Foe` end
		return false, `Locked`
	end
	local Data = svc(`Player.Data`)
	local Profile = Data and Data.GetProfile(P)
	local Done = Profile and Profile.Quests and Profile.Quests.Done
	local Q2 = Config.Defs[Id].Quests and Config.Defs[Id].Quests[2]
	if Value >= 20 and Done and Q2 and Done[Q2] ~= nil then return true, `Ok`, `Friend` end
	return false, `Locked`
end

---| the fight |---

function Local.Center(Id: string): Vector3?
	local F = svc(`Social.CliqueFights`)
	local List = F and F.Spots(Id) or {}
	if #List == 0 then
		local Box = F and F.Box(Id)
		return Box and Box.Position or nil
	end
	local C = Vector3.zero
	for _, P in List do C += P end
	return C / #List
end

function Local.Say(Model: Model?, Text: string?)
	local Cl = svc(`Social.Cliques`)
	if Cl and Model and Text then pcall(Cl.Say, Model, Text) end
end

function Local.Pick(List: { string }?): string?
	return if List and #List > 0 then List[Rng:NextInteger(1, #List)] else nil
end

-- the real leader steps aside while the fight is on (the dialogue NPC from Social.Npcs)
function Local.HideLeader(Ev)
	local Npcs = svc(`Social.Npcs`)
	local M = Npcs and Npcs.Get(LeaderNpc[Ev.Clique])
	if M and M.Parent then
		Ev.RealLeader = M
		Ev.RealPivot = M:GetPivot()
		Ev.RealParent = M.Parent
		M.Parent = nil
	end
end
function Local.ShowLeader(Ev)
	local M = Ev.RealLeader
	if M and not M.Parent then
		pcall(function()
			M.Parent = Ev.RealParent or workspace:FindFirstChild(`Live`) or workspace
			M:PivotTo(Ev.RealPivot)
		end)
	end
end

function Local.SpawnLeader(Ev, At: Vector3)
	local AI = svc(`AI.AI`)
	local Def = Config.Defs[Ev.Clique]
	if not AI then return nil end
	local Set = table.clone(NPCConfig.Default)
	Set.Tier = Def.LeaderTier or `Hard`
	Set.Weapon = `Fist`
	Set.AggroRange = 60
	Set.ChaseRange = 90
	Set.AttackRange = 10
	Set.CorpseTime = 3
	Set.RespawnTime = nil
	local P = Ev.Player
	Set.FixedTarget = function() return if P.Parent then P.Character else nil end
	local Npc = AI.Spawn(workspace:FindFirstChild(`Live`) or workspace, nil, nil, Set)
	local Char = Npc and Npc.Character
	if not Char then return nil end
	Char.Name = Def.Leader
	Char:SetAttribute(`Clique`, Ev.Clique)
	Char:SetAttribute(`QuestTarget`, `Showdown{Ev.Clique}`)
	Char:SetAttribute(`NHShowdownLeader`, Ev.Clique)
	Char:PivotTo(CFrame.lookAt(At + Vector3.new(0, 3, 0), (P.Character and P.Character:GetPivot().Position or At) * Vector3.new(1, 0, 1) + Vector3.new(0, At.Y + 3, 0)))
	local Hum = Char:FindFirstChildWhichIsA(`Humanoid`)
	if Hum then
		Hum.DisplayName = Def.Leader
		local HP = S.LeaderHealth[Set.Tier] or 150
		Hum.MaxHealth = HP
		Hum.Health = HP
	end
	local Looks = svc(`Features.NpcLooks`)
	local Spec = Looks and Looks.Specs and Looks.Specs[LeaderNpc[Ev.Clique]]
	if Spec then task.spawn(Looks.Apply, Char, Spec) end
	return Char, Npc
end

-- the hangout is a fight zone while it's on (School.HallMonitor skips CombatAllowed places)
function Local.Zone(Ev, Center: Vector3)
	local F = svc(`Social.CliqueFights`)
	local Box = F and F.Box(Ev.Clique)
	local Z = Instance.new(`Part`)
	Z.Name = `NHShowdownZone`
	Z.Anchored = true
	Z.CanCollide = false
	Z.CanQuery = false
	Z.CanTouch = false
	Z.Transparency = 1
	if Box then
		Z.CFrame = Box.CFrame
		Z.Size = Box.Size + Vector3.new(2 * S.ForfeitDistance, 20, 2 * S.ForfeitDistance)
	else
		Z.CFrame = CFrame.new(Center)
		Z.Size = Vector3.new(90, 30, 90)
	end
	CollectionService:AddTag(Z, `CombatAllowed`)
	Z.Parent = workspace
	Ev.Zone = Z
end

function Shared.StartFight(P: Player, Id: string, Path: string?): boolean
	if Fights[Id] then return false end
	local F = svc(`Social.CliqueFights`)
	local Def = Config.Defs[Id]
	local Char = P.Character
	if not (F and Def and Char) or F.Out(Char) then return false end
	local Center = Local.Center(Id)
	if not Center then return false end
	local Ev = { Player = P; Clique = Id; Path = Path or `Friend`; Ring = {}; Joined = {}; Started = os.clock(); Kind = `Showdown` }
	Fights[Id] = Ev
	-- (audit) marks the player for the fight, so clique backup, their crew and turf confrontations stay out of a 1-on-1
	Ev.Char = Char
	if Char then Char:SetAttribute(`NHShowdown`, Id) end
	if Pending[P] then Pending[P][Id] = nil end
	Local.HideLeader(Ev)
	Local.Zone(Ev, Center)
	-- the leader, a few studs from you, facing you
	local PR = Char:GetPivot().Position
	local Dir = (Center - PR) * Vector3.new(1, 0, 1)
	Dir = if Dir.Magnitude > 1 then Dir.Unit else Vector3.new(1, 0, 0)
	local At = F.Floor(PR + Dir * 10) or F.Floor(Center) or Center
	local Leader, Npc = Local.SpawnLeader(Ev, At)
	if not Leader then Local.End(Ev, `Error`) return false end
	Ev.Leader, Ev.Npc = Leader, Npc
	-- the ring
	local Mid = (PR + At) / 2
	for I = 1, S.RingSize do
		local A = (I / S.RingSize) * math.pi * 2
		local Pos = F.Floor(Mid + Vector3.new(math.cos(A), 0, math.sin(A)) * S.RingRadius) or F.Floor(Mid) or Mid
		local M = F.SpawnFighter(Id, Pos, Ev, nil)
		if M then
			M:PivotTo(CFrame.lookAt(Pos + Vector3.new(0, 3, 0), Mid + Vector3.new(0, 3, 0)))
			table.insert(Ev.Ring, M)
		end
	end
	Local.Say(Leader, Local.Pick(Def.Taunt) or `Let's go.`)
	local N = svc(`Features.Notifications`)
	if N then pcall(N.Notify, P, { Title = `Showdown: {Def.Leader}`; Text = `Down them. At half health their crew joins in. Run and you forfeit.`; Kind = `Warning`; Duration = 5 }) end
	task.spawn(function() Local.Run(Ev) end)
	return true
end

function Local.Run(Ev)
	local F = svc(`Social.CliqueFights`)
	local Def = Config.Defs[Ev.Clique]
	local P = Ev.Player
	local Box = F and F.Box(Ev.Clique)
	local LastShout = os.clock()
	while Fights[Ev.Clique] == Ev do
		task.wait(0.25)
		local Char = P.Parent and P.Character
		if not Char or F.Out(Char) then Local.End(Ev, `Lost`) return end
		if F.Out(Ev.Leader) then Local.End(Ev, `Won`) return end
		local R = Char:FindFirstChild(`HumanoidRootPart`)
		if R and Box and not F.Inside(R, Box, S.ForfeitDistance) then Local.End(Ev, `Forfeit`) return end
		-- half health: the crew comes in
		local Hum = Ev.Leader:FindFirstChildWhichIsA(`Humanoid`)
		if Hum and not Ev.Called and Hum.Health <= Hum.MaxHealth / 2 then
			Ev.Called = true
			Local.Say(Ev.Leader, Local.Pick(Def.Call) or `Get in here!`)
			for I = 1, math.min(S.Backup, #Ev.Ring) do
				local M = table.remove(Ev.Ring, Rng:NextInteger(1, #Ev.Ring))
				table.insert(Ev.Joined, M)
				F.Aim(M, Char, 5000)
			end
		end
		-- the ring shouts
		if os.clock() - LastShout >= S.ShoutEvery and #Ev.Ring > 0 then
			LastShout = os.clock()
			Local.Say(Ev.Ring[Rng:NextInteger(1, #Ev.Ring)], Local.Pick(Def.Rally) or Local.Pick(Def.Taunt))
		end
		if os.clock() - Ev.Started > 300 then Local.End(Ev, `Time`) return end
	end
end

function Local.End(Ev, Why: string)
	if Fights[Ev.Clique] ~= Ev then return end
	Fights[Ev.Clique] = nil
	if Ev.Char and Ev.Char:GetAttribute(`NHShowdown`) == Ev.Clique then Ev.Char:SetAttribute(`NHShowdown`, nil) end -- (audit)
	Ev.Result = Why
	local P = Ev.Player
	local Id = Ev.Clique
	local Def = Config.Defs[Id]
	local F = svc(`Social.CliqueFights`)
	local Cl = svc(`Social.Cliques`)
	local Quests = svc(`Quests.Quests`)
	local N = svc(`Features.Notifications`)
	local Day = Local.Day()
	local D = Local.Data(P)
	Local.LastResult = `{P.Name} vs {Def.Leader}: {Why} after {math.floor(os.clock() - Ev.Started)} s ({Ev.Path})`
	if Why == `Won` then
		Local.Say(Ev.Leader, Def.Beaten)
		if D then D.Won[Id] = Day or 0 Local.Save(P) end
		local Cur = Local.Standing(P, Id)
		if Cl and Cur < 60 then pcall(Cl.Add, P, Id, 60 - Cur, `You beat {Def.Leader} in a showdown`) end
		if Quests and Quests.Progress then pcall(Quests.Progress, P, `Defeat`, `Showdown{Id}`) end
		if N then pcall(N.Notify, P, { Title = `You beat {Def.Leader}`; Text = `{Def.Name} respect you now.`; Kind = `Good`; Duration = 6 }) end
		task.defer(Local.CheckKing, P)
	else
		local Speaker = if Ev.Leader and not F.Out(Ev.Leader) then Ev.Leader else Ev.Ring[1]
		if Why == `Lost` then Local.Say(Speaker, Local.Pick(Def.Gloat) or Local.Pick(Def.Jeer))
		elseif Why == `Forfeit` then Local.Say(Speaker, Local.Pick(Def.Leave) or `Run, then!`) end
		-- (audit) a showdown that failed to start (Error) is not the player's loss
		if D and Day and Why ~= `Error` then D.Tried[Id] = Day Local.Save(P) end
		if Why ~= `Error` and Quests and Quests.Fail and QuestFor[Id] then
			pcall(Quests.Fail, P, QuestFor[Id], if Why == `Forfeit` then `You ran from the showdown. Try again tomorrow.` else `You lost the showdown. Try again tomorrow.`)
		end
		if Ev.Path == `Foe` and Why ~= `Error` and Cl then pcall(Cl.Add, P, Id, S.FoeLoss, `{Def.Leader} beat you`) end
		if N and Why ~= `Error` then pcall(N.Notify, P, { Title = if Why == `Forfeit` then `You ran` else `{Def.Leader} won`; Text = `Try again tomorrow.`; Kind = `Bad`; Duration = 5 }) end
	end
	if Ev.Zone then Ev.Zone:Destroy() end
	task.delay(2.5, function()
		for _, M in Ev.Ring do if M.Parent then F.Leave(M) end end
		for _, M in Ev.Joined do if M.Parent then F.Leave(M) end end
		if Ev.Leader and Ev.Leader.Parent then
			if F.Out(Ev.Leader) then task.wait(2) end
			if Ev.Leader.Parent then Ev.Leader:Destroy() end
		end
		Local.ShowLeader(Ev)
	end)
end

---| King / Queen of the School |---

function Local.CheckKing(P: Player)
	local D = Local.Data(P)
	if not D or D.King then return end
	for _, Id in Config.Order do if not D.Won[Id] then return end end
	D.King = true
	Local.Save(P)
	P:SetAttribute(`NHKing`, true)
	local Queen = false
	pcall(function()
		-- (audit) the look lives in PlayerData.Appearance; Identity has no Look field, so this was always King
		local Data = svc(`Player.Data`)
		local Profile = Data and Data.GetProfile(P)
		local Look = Profile and require(game:GetService(`ReplicatedStorage`).UI.Appearance).Sanitize(Profile.Appearance)
		Queen = Look ~= nil and require(game:GetService(`ReplicatedStorage`).UI.Appearance).IsFemale(Look)
	end)
	local Title = S.KingTitle[if Queen then 2 else 1]
	local Rep = svc(`Social.Reputation`)
	if Rep then pcall(Rep.AwardTitle, P, Title) end
	local Phone = svc(`Features.Phone`)
	for _, Id in Config.Order do
		if Phone then pcall(Phone.AddText, P, { From = Config.Defs[Id].Leader; Body = Config.Defs[Id].Crown }, true) end
	end
	local N = svc(`Features.Notifications`)
	if N then pcall(N.Notify, P, { Title = Title; Text = `Every leader in the school has bowed. 10% off at every shop, and backup at every hangout.`; Kind = `Milestone`; Duration = 8 }) end
end

function Shared.WinForTests(P: Player, Id: string): boolean
	local D = Local.Data(P)
	if not D then return false end
	D.Won[Id] = Local.Day() or 0
	Local.Save(P)
	Local.CheckKing(P)
	return true
end

---| challenges, pending fights, no-shows |---

function Local.Ready(P: Player): boolean
	if not P.Parent or P:GetAttribute(`InMainMenu`) == true or P:GetAttribute(`Slot`) == nil then return false end
	return Local.Data(P) ~= nil
end

function Local.Tick()
	local Day = Local.Day()
	local Seg = Local.Segment()
	local F = svc(`Social.CliqueFights`)
	local Quests = svc(`Quests.Quests`)
	local Phone = svc(`Features.Phone`)
	if not (Day and F and Quests) then return end
	for _, P in Players:GetPlayers() do
		if not Local.Ready(P) then continue end
		local D = Local.Data(P)
		-- attributes: King, and the grudges from yesterday's no-shows
		if D.King and P:GetAttribute(`NHKing`) ~= true then P:SetAttribute(`NHKing`, true) end
		for _, Id in Config.Order do
			local Grudge = D.NoShow[Id] == Day - 1 or D.NoShow[Id] == Day
			if (P:GetAttribute(`NHGrudge_{Id}`) == true) ~= Grudge then P:SetAttribute(`NHGrudge_{Id}`, if Grudge then true else nil) end
		end
		for _, Id in Config.Order do
			local Q = QuestFor[Id]
			local Active = Q and Quests.IsActive and Quests.IsActive(P, Q)
			-- a Hostile leader's challenge, once a day
			if not D.Won[Id] and D.Challenged[Id] ~= Day and D.Tried[Id] ~= Day and Config.Tier(Local.Standing(P, Id)) == `Hostile` and not Active then
				D.Challenged[Id] = Day
				D.FoeQuest[Id] = Day -- (audit) the path is stored with the challenge
				Local.Save(P)
				if Phone then pcall(Phone.AddText, P, { From = Config.Defs[Id].Leader; Body = Config.Defs[Id].Challenge }) end
				if Q then pcall(Quests.Start, P, Q, true) end
				Active = Quests.IsActive and Quests.IsActive(P, Q)
			end
			-- (audit) the path comes from the stored challenge (it was worked out each tick, so a Foe challenge carried over to a
			-- later day, or a standing change, turned into a Friend one)
			if not Active and D.FoeQuest[Id] then D.FoeQuest[Id] = nil Local.Save(P) end
			if not Active or Fights[Id] then continue end
			local FoeDay = D.FoeQuest[Id] or (if D.Challenged[Id] == Day and Config.Tier(Local.Standing(P, Id)) == `Hostile` then Day else nil)
			local Path = if FoeDay then `Foe` else `Friend`
			-- a challenge nobody answered: gone at night (or once its day has passed), and their crews hold a grudge tomorrow
			if Path == `Foe` and (FoeDay ~= Day or Seg == `Night` or Seg == `Morning`) then
				D.NoShow[Id] = FoeDay
				D.Tried[Id] = FoeDay
				D.FoeQuest[Id] = nil
				Local.Save(P)
				pcall(Quests.Fail, P, Q, `You didn't show up. {Config.Defs[Id].Name} won't forget it.`)
				continue
			end
			-- in their hangout at the right time: it starts
			local Ok = Seg ~= nil and Seg ~= `Class` and (Path == `Friend` or S.FoeKinds[Seg] == true)
			local R = P.Character and P.Character:FindFirstChild(`HumanoidRootPart`)
			local Box = F.Box(Id)
			if Ok and R and Box and F.Inside(R, Box, 0) and not F.Out(P.Character) and not P.Character:GetAttribute(`Dueling`) then
				Shared.StartFight(P, Id, Path)
			end
		end
	end
end

---| bulletin / tests |---

function Shared.Summary(P: Player)
	local D = Local.Data(P)
	local Out = { Beaten = 0; Of = #Config.Order; King = false; Open = {} }
	if not D then return Out end
	for _, Id in Config.Order do if D.Won[Id] then Out.Beaten += 1 end end
	Out.King = D.King == true
	local Quests = svc(`Quests.Quests`)
	for _, Id in Config.Order do
		if QuestFor[Id] and Quests and Quests.IsActive and Quests.IsActive(P, QuestFor[Id]) then
			table.insert(Out.Open, { Leader = Config.Defs[Id].Leader; Hangout = Config.Defs[Id].HangoutName; Foe = D.Challenged[Id] == Local.Day() })
		end
	end
	return Out
end

function Shared.State()
	local Out = { Fights = {}; LastResult = Local.LastResult }
	for Id, Ev in Fights do
		local Hum = Ev.Leader and Ev.Leader:FindFirstChildWhichIsA(`Humanoid`)
		table.insert(Out.Fights, { Clique = Id; Player = Ev.Player.Name; Path = Ev.Path; Age = math.floor(os.clock() - Ev.Started);
			LeaderHealth = Hum and math.floor(Hum.Health) or 0; LeaderMax = Hum and Hum.MaxHealth or 0; Called = Ev.Called == true;
			Ring = #Ev.Ring; Joined = #Ev.Joined; LeaderHidden = Ev.RealLeader ~= nil and Ev.RealLeader.Parent == nil })
	end
	return Out
end

-- tests: hurt the leader (as if hit) to check the half-health call and the win
function Shared.HurtForTests(Id: string, Amount: number): boolean
	local Ev = Fights[Id]
	local Hum = Ev and Ev.Leader and Ev.Leader:FindFirstChildWhichIsA(`Humanoid`)
	if not Hum then return false end
	Hum:TakeDamage(Amount)
	return true
end

function Shared.OnStart()
	local Quests = svc(`Quests.Quests`)
	Players.PlayerRemoving:Connect(function(P)
		Pending[P] = nil
		for _, Ev in Fights do if Ev.Player == P then Local.End(Ev, `Forfeit`) end end
	end)
	task.spawn(function()
		while true do
			task.wait(1)
			local Ok, Err = pcall(Local.Tick)
			if not Ok then warn(`[CliqueShowdowns] {Err}`) end
		end
	end)
	_ = Quests
end

return Shared
