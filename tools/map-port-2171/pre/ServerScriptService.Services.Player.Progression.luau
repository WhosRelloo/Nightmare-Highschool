--[[
	Progression (server): EXP, levels, stats, and the effects of stats, clan perks and lineage traits.
	Config: ReplicatedStorage.Config.Progression. Saved in PlayerData.Progress via SetProgress:
		{ Level, Exp, Points, Stats = { Might, Grit, Wits }, FatedDay }

	EXP comes from existing game signals (no system had to change to send it):
		Attendance.Recorded (present / tardy), Activities.Finished (graded lessons), Quests.Completed,
		Duels.Won, Duels.ChampionDefeated, Downed.OnExecuted (grip executions), Factions.Joined /
		RankChanged, HallMonitor.Escaped, Strangers introductions.
	Every award is multiplied by SchoolClock.GetExpMultiplier() (1.2x in school hours, concept doc) and
	by your EXP bonuses for that kind of EXP (stats, clan perk, traits).
	Levelling gives stat points (Config.PointsPerLevel); spend them in the character sheet.

	Effects (see Config.Progression) are applied as character attributes that combat reads:
		NH_DamageDealt, NH_DamageTaken (Downed.ApplyDamage), NH_PostureGain (DamageLogic),
		NH_Stealth (Quests.Stealth), plus Humanoid.MaxHealth, low-health regeneration and the
		once-a-day revive (Fated). Public player attribute: Level.

	Remotes: ReplicatedStorage.NHProgress  Get (RF) -> sheet, Spend (RF) (statId, n) -> ok, sheet,
	         Updated (RE) server -> client: sheet
	Server API: Progression.Award(player, key | amount, category?, reason?), Progression.Sheet(player)
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local Config = require(ReplicatedStorage.Config.Progression)
local OUT_OF_COMBAT_REGEN = 0.02 -- fraction of max health healed per second once your combat tag runs out
local Lineage = require(ReplicatedStorage.Lineage)
local Data = require(ServerScriptService.Services.Player.Data)
local Identity = require(ServerScriptService.Services.Player.Identity)
local Notifications = require(ServerScriptService.Services.Features.Notifications)
local Fx = require(ServerScriptService.Services.Features.Fx)

local Local = {}
local Shared = {}
local Last = {} :: { [Player]: number }

local function try(Path: { string })
	local M = ServerScriptService
	for _, N in Path do
		M = M and M:FindFirstChild(N)
	end
	if not M then return nil end
	local Ok, Mod = pcall(require, M)
	return if Ok then Mod else nil
end

---| Data |---

function Shared.Sanitize(Raw: any)
	local Out = { Level = 1; Exp = 0; Points = 0; Stats = {}; FatedDay = -1 }
	for _, S in Config.Stats do Out.Stats[S.Id] = 0 end
	if typeof(Raw) ~= `table` then return Out end
	local function num(V, Min, Max) return if typeof(V) == `number` and V == V then math.clamp(math.floor(V), Min, Max) else nil end
	Out.Level = num(Raw.Level, 1, Config.MaxLevel) or 1
	Out.Exp = num(Raw.Exp, 0, 10 ^ 9) or 0
	Out.Points = num(Raw.Points, 0, Config.MaxLevel * Config.PointsPerLevel) or 0
	Out.FatedDay = num(Raw.FatedDay, -1, 10 ^ 7) or -1
	if typeof(Raw.Stats) == `table` then
		for _, S in Config.Stats do Out.Stats[S.Id] = num(Raw.Stats[S.Id], 0, Config.MaxStat) or 0 end
	end
	return Out
end

function Shared.Get(Player: Player)
	local Profile = Data.GetProfile(Player)
	return Profile and Shared.Sanitize(Profile.Progress)
end

function Local.Save(Player: Player, P)
	Data.UpdateState(Player, { type = `SetProgress`; progress = P })
end

---| Effects |---

function Local.Add(Into, Effects, Scale: number?)
	for K, V in Effects or {} do Into[K] = (Into[K] or 0) + V * (Scale or 1) end
end

-- Every effect from your stats, clan perk and traits, added together.
function Shared.Effects(Player: Player)
	local E, Sources = {}, {}
	local P = Shared.Get(Player)
	if P then
		for _, S in Config.Stats do Local.Add(E, S.Per, P.Stats[S.Id]) end
	end
	local I = Identity.Get(Player)
	local ClanFx = I and I.Clan and Config.ClanEffects[I.Clan]
	if ClanFx then Local.Add(E, ClanFx) Sources.Clan = ClanFx end
	local Profile = Data.GetProfile(Player)
	local L = Profile and Lineage.Sanitize(Profile.Lineage)
	Sources.Traits = {}
	for _, Id in L and L.Traits or {} do
		for _, T in Lineage.Traits or {} do
			if T.Id == Id then Local.Add(E, T.Effects) table.insert(Sources.Traits, T) end
		end
	end
	-- race passive: strengths by tier x sub-race boost, plus flat drawbacks (ReplicatedStorage.Lineage)
	if L and L.Race then
		Local.Add(E, Lineage.PassiveEffects(L.Race, L.SubRace, L.Tier))
		Sources.Race = { Race = L.Race; Sub = L.SubRace; Tier = L.Tier }
	end
	-- worn 3D gear (Services.Features.Gear, budgets in Config.Gear)
	pcall(function()
		local G = require(game:GetService(`ServerScriptService`).Services.Features.Gear).Effects(Player)
		if next(G) then Local.Add(E, G) Sources.Gear = G end
	end)
	-- (kit 1.79) the everyday kit: a borrowed book pinned to the hotbar (Services.Features.Kit)
	pcall(function()
		local K = require(game:GetService(`ServerScriptService`).Services.Features.Kit).Effects(Player)
		if next(K) then Local.Add(E, K) Sources.Kit = K end
	end)
	-- (training 1.81) the trained areas: Arms, Torso, Legs (Services.Features.Training, Config.Progression.Training)
	pcall(function()
		local Tr = require(game:GetService(`ServerScriptService`).Services.Features.Training).Effects(Player)
		if next(Tr) then Local.Add(E, Tr) Sources.Training = Tr end
	end)
	-- the active snack buff (Services.Features.Inventory, Config.Items)
	pcall(function()
		local B = require(game:GetService(`ServerScriptService`).Services.Features.Inventory).Effects(Player)
		if next(B) then Local.Add(E, B) Sources.Snack = B end
	end)
	return E, Sources
end

function Local.IsNight(): boolean
	local Clock = try({ `Services`, `School`, `SchoolClock` })
	local Ok, State = pcall(function() return Clock.GetState() end)
	local Hour = Ok and State and State.Hour
	return typeof(Hour) == `number` and (Hour >= 20 or Hour < 6)
end

function Local.IsFullMoon(): boolean
	local Clock = try({ `Services`, `School`, `SchoolClock` })
	local Ok, State = pcall(function() return Clock.GetState() end)
	return Ok and State and Lineage.IsFullMoon(State.Day, State.Hour) or false
end

-- (1.41) the new moon (the Wraiths' night)
function Local.IsNewMoon(): boolean
	local Clock = try({ `Services`, `School`, `SchoolClock` })
	local Ok, State = pcall(function() return Clock.GetState() end)
	return Ok and State and Lineage.IsNewMoon and Lineage.IsNewMoon(State.Day, State.Hour) or false
end

function Local.IsSchoolHours(): boolean
	local Clock = try({ `Services`, `School`, `SchoolClock` })
	local Ok, Mult = pcall(function() return Clock.GetExpMultiplier() end)
	return Ok and typeof(Mult) == `number` and Mult > 1
end

-- Puts the active effects on the character, where combat reads them.
function Shared.Apply(Player: Player)
	local Character = Player.Character
	local Humanoid = Character and Character:FindFirstChildOfClass(`Humanoid`)
	if not Humanoid then return end
	local E = Shared.Effects(Player)
	local Night = Local.IsNight()
	local FullMoon = Night and Local.IsFullMoon()
	local NewMoon = Night and Local.IsNewMoon()
	-- (1.41) a crimson or blue moon strengthens some races (Lineage.MoonEvents)
	local EventPower = 0
	if FullMoon then
		local Clock = try({ `Services`, `School`, `SchoolClock` })
		local Ok, St = pcall(function() return Clock.GetState() end)
		if Ok and St and Lineage.MoonEventPower then EventPower = Lineage.MoonEventPower(Player:GetAttribute(`Race`), St.Day, St.Hour) end
	end
	local Dealt = 1 + (E.DamageDealt or 0) + (if Night then (E.NightPower or 0) + (if FullMoon then E.FullMoonPower or 0 else 0)
		+ (if NewMoon then E.NewMoonPower or 0 else 0) + EventPower else (E.DamageByDay or 0))
	Character:SetAttribute(`NH_DamageDealt`, if math.abs(Dealt - 1) > 1e-4 then Dealt else nil)
	local Taken = math.max(0.5, 1 + (E.DamageTaken or 0))
	Character:SetAttribute(`NH_DamageTaken`, if math.abs(Taken - 1) > 1e-4 then Taken else nil)
	local Posture = math.max(0.4, 1 + (E.PostureGain or 0))
	Character:SetAttribute(`NH_PostureGain`, if math.abs(Posture - 1) > 1e-4 then Posture else nil)
	local Stealth = math.max(0.4, 1 + (E.Stealth or 0) + (if NewMoon then E.NewMoonStealth or 0 else 0))
	Character:SetAttribute(`NH_Stealth`, if math.abs(Stealth - 1) > 1e-4 then Stealth else nil)
	-- (training 1.81) Legs: sprint speed, applied by Features.CombatSpeed to sprint speeds only
	local Sprint = 1 + (E.SprintSpeed or 0)
	Character:SetAttribute(`NH_SprintMult`, if math.abs(Sprint - 1) > 1e-4 then Sprint else nil)
	-- race family bonuses, read by Lineage.DamageScale inside Downed.ApplyDamage
	local function opt(V) return if V and math.abs(V) > 1e-4 then V else nil end
	Character:SetAttribute(`NH_VsUndead`, opt(E.DamageVsUndead))
	Character:SetAttribute(`NH_VsMonster`, opt(E.DamageVsMonster))
	Character:SetAttribute(`NH_FromUndead`, opt(E.DamageTakenFromUndead))
	local Max = 100 + math.floor(E.MaxHealth or 0)
	if Humanoid.MaxHealth ~= Max and Humanoid.Health > 0 then
		local Ratio = Humanoid.Health / math.max(Humanoid.MaxHealth, 1)
		Humanoid.MaxHealth = Max
		Humanoid.Health = math.clamp(Ratio * Max, 1, Max)
	end
end

---| EXP |---

function Shared.Award(Player: Player, What: any, Category: string?, Reason: string?): number
	local P = Shared.Get(Player)
	if not P then return 0 end
	local Base, Cat = 0, Category
	if typeof(What) == `string` then
		local Def = Config.Exp[What]
		if not Def then return 0 end
		Base, Cat = Def.Amount, Cat or Def.Category
	elseif typeof(What) == `number` then
		Base = What
	end
	if Base <= 0 then return 0 end
	local E = Shared.Effects(Player)
	local Bonus = 1 + (E[`{Cat or ``}Exp`] or 0) + (E.AllExp or 0)
	if Local.IsSchoolHours() then Bonus += E.SchoolExp or 0 end
	if Local.IsNight() then Bonus += E.NightExp or 0 end
	-- study group: +10% while a member is near (Services.Features.Party)
	local Party = try({ `Services`, `Features`, `Party` })
	if Party then pcall(function() Bonus += Party.ExpBonus(Player) end) end
	local Clock = try({ `Services`, `School`, `SchoolClock` })
	local ClockMult = 1
	pcall(function() ClockMult = Clock.GetExpMultiplier() end)
	local Gain = math.max(1, math.floor(Base * Bonus * ClockMult + 0.5))

	P.Exp += Gain
	local Ups = 0
	while P.Level < Config.MaxLevel and P.Exp >= Config.ToNext(P.Level) do
		P.Exp -= Config.ToNext(P.Level)
		P.Level += 1
		P.Points += Config.PointsPerLevel
		Ups += 1
	end
	if P.Level >= Config.MaxLevel then P.Exp = 0 end
	Local.Save(Player, P)
	Player:SetAttribute(`Level`, P.Level)
	if Ups > 0 then
		Local.LevelUpEffect(Player, P.Level, Ups * Config.PointsPerLevel)
	end
	Shared.Notify(Player, { Gain = Gain; Reason = Reason; Ups = Ups })
	if Party and Cat == `Combat` then pcall(Party.Share, Player, Gain, Cat) end
	return Gain
end

-- VFX P1-6 "Bell Toll": drawn on clients (Controllers.Gui.Moments). The owner gets the banner (it replaces the
-- old "Level N!" toast); players within 80 studs see the ember column. One event per award, however many levels.
function Local.LevelUpEffect(Player: Player, Level: number, Points: number)
	local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	local Data = { UserId = Player.UserId; Level = Level; Points = Points }
	if Root then
		Fx.FireNear(Root.Position, 80, `LevelUp`, Data) -- includes the owner
	else
		Fx.Fire(Player, `LevelUp`, Data)
	end
end

---| Spending points |---

function Shared.Spend(Player: Player, StatId: any, Count: any): (boolean, any)
	local P = Shared.Get(Player)
	if not P then return false, `Your record is still loading` end
	if typeof(StatId) ~= `string` or not Config.StatById[StatId] then return false, `Unknown stat` end
	local N = if typeof(Count) == `number` and Count == Count then math.clamp(math.floor(Count), 1, 10) else 1
	N = math.min(N, P.Points, Config.MaxStat - P.Stats[StatId])
	if N <= 0 then return false, if P.Points <= 0 then `No points to spend` else `That stat is maxed` end
	P.Stats[StatId] += N
	P.Points -= N
	Local.Save(Player, P)
	Shared.Apply(Player)
	Shared.Notify(Player)
	return true, Shared.Sheet(Player)
end

---| Sheet (what the client shows) |---

-- what the Report Card shows beside the numbers (Controllers.Gui.StatsPanel)
function Local.RecordFor(Player: Player)
	local Prof = Data.GetProfile(Player) or {}
	local I = Identity.Get(Player)
	local A = Prof.Attendance or {}
	local D = Prof.Discipline or {}
	local Classes = {}
	for K, C in Prof.Classes or {} do if typeof(C) == `table` then Classes[K] = { Passes = C.Passes or 0 } end end
	local Ok, Name = pcall(function() return Identity.FullName(I) end)
	return {
		Name = if Ok and typeof(Name) == `string` then Name else ``;
		Attendance = { Totals = A.Totals or {}; Streak = A.Streak or 0; BestStreak = A.BestStreak or 0 };
		Discipline = { Level = D.Level or `Clear`; Points = D.Points or 0; DetentionsOwed = D.DetentionsOwed or 0 };
		Classes = Classes; NPCKills = Prof.NPCKills or 0;
	}
end

function Shared.Sheet(Player: Player)
	local P = Shared.Get(Player)
	if not P then return nil end
	local E, Sources = Shared.Effects(Player)
	local Traits = {}
	for _, T in Sources.Traits or {} do table.insert(Traits, { Name = T.Name; Text = Config.Describe(T.Effects) }) end
	local I = Identity.Get(Player)
	local RaceInfo = nil
	if Sources.Race then
		local R = Lineage.RaceById[Sources.Race.Race]
		local S = Lineage.SubById[Sources.Race.Sub]
		local Str, Dra = Lineage.Passives(Sources.Race.Race, Sources.Race.Sub, Sources.Race.Tier)
		RaceInfo = {
			Race = R and R.Name or Sources.Race.Race; Sub = S and S.Sub.Name or ``; Rarity = S and S.Sub.Rarity or ``;
			Tier = Sources.Race.Tier; TierName = Lineage.TierName(Sources.Race.Race, Sources.Race.Tier);
			Passive = R and R.Passive and R.Passive.Name or ``;
			Strengths = Config.Describe(Str); Drawbacks = if next(Dra) then Config.Describe(Dra) else (R and R.Passive and R.Passive.DrawbackText or ``);
		}
	end
	return {
		RaceInfo = RaceInfo;
		Level = P.Level; Exp = P.Exp; Next = if P.Level < Config.MaxLevel then Config.ToNext(P.Level) else 0;
		Points = P.Points; Stats = P.Stats; Effects = E; EffectsText = Config.Describe(E);
		Clan = I and I.Clan; ClanText = Sources.Clan and Config.Describe(Sources.Clan) or ``;
		Traits = Traits; Kills = (Data.GetProfile(Player) or {}).Kills or 0; NPCKills = (Data.GetProfile(Player) or {}).NPCKills or 0;
		GearText = Sources.Gear and Config.Describe(Sources.Gear) or ``; Record = Local.RecordFor(Player); SnackText = Sources.Snack and Config.Describe(Sources.Snack) or ``;
		Tier = Player:GetAttribute(`RaceTier`); Race = Player:GetAttribute(`SubRace`) or Player:GetAttribute(`Race`);
	}
end

function Shared.Notify(Player: Player, Extra)
	local Folder = ReplicatedStorage:FindFirstChild(`NHProgress`)
	local Sheet = Shared.Sheet(Player)
	if Folder and Sheet then
		Sheet.Last = Extra
		Folder.Updated:FireClient(Player, Sheet)
	end
end

---| Hooks |---

function Local.Hook()
	local function on(Path: { string }, Signal: string, Fn)
		local M = try(Path)
		local S = M and M[Signal]
		if S and S.Connect then S:Connect(function(...) pcall(Fn, ...) end) else warn(`[Progression] missing {table.concat(Path, ".")}.{Signal}`) end
	end
	on({ `Services`, `School`, `Attendance` }, `Recorded`, function(Player, Record)
		local Status = typeof(Record) == `table` and (Record.Status or Record.Result) or Record
		if Status == `Present` then Shared.Award(Player, `AttendPresent`, nil, `Attended class`)
		elseif Status == `Tardy` then Shared.Award(Player, `AttendTardy`, nil, `Late to class`) end
	end)
	on({ `Services`, `School`, `Activities` }, `Finished`, function(Player, Subject, Result)
		if typeof(Result) ~= `table` or Result.Practice or Result.Study or not Result.Passed then return end
		local Grade = Result.Grade
		local Bonus = Config.LessonGradeBonus[tostring(Grade)] or 0
		-- (kit 1.79) a borrowed book on the lesson's subject: +10%
		local Book = 0
		pcall(function() Book = require(game:GetService(`ServerScriptService`).Services.Features.Kit).LessonBonus(Player, Subject) end)
		Shared.Award(Player, math.floor((Config.Exp.Lesson.Amount + Bonus) * (1 + Book) + 0.5), `Class`, `{Subject} lesson`)
	end)
	on({ `Services`, `Quests`, `Quests` }, `Completed`, function(Player, Id)
		local Quests = require(ReplicatedStorage.Config.Quests)
		local Def = Quests.Quests and Quests.Quests[Id]
		local Explicit = Def and Def.Rewards and Def.Rewards.Exp
		local Main = Def and (Def.Category == `Main` or Def.Chapter ~= nil)
		if Explicit then Shared.Award(Player, Explicit, `Quest`, Def.Name)
		else Shared.Award(Player, if Main then `QuestMain` else `QuestSide`, nil, Def and Def.Name) end
	end)
	on({ `Services`, `Quests`, `Duels` }, `Won`, function(Player) Shared.Award(Player, `DuelWon`, nil, `Won a duel`) end)
	on({ `Services`, `Quests`, `Duels` }, `ChampionDefeated`, function(Player) Shared.Award(Player, `ChampionDefeated`, nil, `Beat the champion`) end)
	on({ `Services`, `Features`, `Downed` }, `OnExecuted`, function(Gripper, Target)
		local Player = Players:GetPlayerFromCharacter(Gripper)
		if not Player then return end
		local IsPlayer = Players:GetPlayerFromCharacter(Target) ~= nil
		Shared.Award(Player, if IsPlayer then `ExecutePlayer` else `ExecuteNPC`, nil, `Execution`)
	end)
	-- race passives: healing on a kill (Vampire) or an execution (Ghoul)
	local function heal(Character: Model?, Fraction: number)
		local H = Character and Character:FindFirstChildOfClass(`Humanoid`)
		if H and H.Health > 0 and Fraction > 0 and not Character:GetAttribute(`DownedUntil`) then
			H.Health = math.min(H.MaxHealth, H.Health + H.MaxHealth * Fraction)
		end
	end
	on({ `Services`, `Features`, `Downed` }, `OnExecuted`, function(Gripper)
		local Player = Players:GetPlayerFromCharacter(Gripper)
		if Player then heal(Gripper, Shared.Effects(Player).HealOnExecute or 0) end
	end)
	on({ `Services`, `Features`, `Downed` }, `OnDefeated`, function(Target, Killer)
		local Player = Killer and Players:GetPlayerFromCharacter(Killer)
		if Player and Killer ~= Target then heal(Killer, Shared.Effects(Player).HealOnKill or 0) end
	end)
	on({ `Services`, `Social`, `Factions` }, `Joined`, function(Player) Shared.Award(Player, `FactionJoined`, nil, `Joined a faction`) end)
	on({ `Services`, `Social`, `Factions` }, `RankChanged`, function(Player, _, New, Old)
		if New and Old and New ~= Old then Shared.Award(Player, `FactionRank`, nil, `New faction rank`) end
	end)
	on({ `Services`, `School`, `HallMonitor` }, `Escaped`, function(Player) Shared.Award(Player, `EscapedMonitor`, nil, `Slipped away`) end)
	-- Fated: once per in-game day, a downed student gets back up
	on({ `Services`, `Features`, `Downed` }, `OnDowned`, function(Target)
		local Player = Players:GetPlayerFromCharacter(Target)
		if not Player or Target:GetAttribute(`Dueling`) then return end
		local E = Shared.Effects(Player)
		if (E.DailyRevive or 0) < 1 then return end
		local P = Shared.Get(Player)
		local Clock = try({ `Services`, `School`, `SchoolClock` })
		local Ok, State = pcall(function() return Clock.GetState() end)
		local Day = Ok and State and State.Day or 0
		if not P or P.FatedDay == Day then return end
		P.FatedDay = Day
		Local.Save(Player, P)
		task.delay(2.5, function()
			local Downed = try({ `Services`, `Features`, `Downed` })
			if Downed and Downed.IsDowned(Target) then
				Target:SetAttribute(`NHFated`, true) -- VFX P2-8: the get-up plays the Fated sigil
				pcall(Downed.Recover, Target)
				pcall(Notifications.Notify, Player, { Title = `Fate refuses to let you fall`; Text = `Once a day, you get back up.`; Kind = `Good`; Duration = 4 })
			end
		end)
	end)
end

-- Strangers calls this the first time you introduce yourself to someone
function Shared.OnIntroduced(Player: Player)
	Shared.Award(Player, `Introduced`, nil, `Made an introduction`)
end

---| Start |---

function Shared.OnStart()
	local Folder = Instance.new(`Folder`)
	Folder.Name = `NHProgress`
	local Get = Instance.new(`RemoteFunction`) Get.Name = `Get` Get.Parent = Folder
	local Spend = Instance.new(`RemoteFunction`) Spend.Name = `Spend` Spend.Parent = Folder
	local Updated = Instance.new(`RemoteEvent`) Updated.Name = `Updated` Updated.Parent = Folder
	Folder.Parent = ReplicatedStorage
	Get.OnServerInvoke = function(Player) return Shared.Sheet(Player) end
	Spend.OnServerInvoke = function(Player, StatId, Count)
		local Now = os.clock()
		if Last[Player] and Now - Last[Player] < 0.15 then return false, `Slow down` end
		Last[Player] = Now
		return Shared.Spend(Player, StatId, Count)
	end

	Local.Hook()
	Data.ProfileLoaded:Connect(function(Player)
		local P = Shared.Get(Player)
		if P then Player:SetAttribute(`Level`, P.Level) end
		task.defer(Shared.Apply, Player)
		task.defer(Shared.Notify, Player)
	end)
	local function Watch(Player: Player)
		Player.CharacterAdded:Connect(function(Character)
			Character:WaitForChild(`Humanoid`, 10)
			task.wait(0.2)
			Shared.Apply(Player)
		end)
		-- a new clan or trait changes your effects
		Player.AttributeChanged:Connect(function(Name)
			if Name == `Traits` or Name == `Signed` or Name == `Race` or Name == `SubRace` or Name == `RaceTier` then Shared.Apply(Player) Shared.Notify(Player) end
		end)
	end
	for _, P in Players:GetPlayers() do Watch(P) end
	Players.PlayerAdded:Connect(Watch)
	Players.PlayerRemoving:Connect(function(P) Last[P] = nil end)

	-- night power switches on and off with the clock; low-health regeneration ticks once a second
	task.spawn(function()
		while true do
			task.wait(1)
			for _, Player in Players:GetPlayers() do
				local Humanoid = Player.Character and Player.Character:FindFirstChildOfClass(`Humanoid`)
				if Humanoid and Data.GetProfile(Player) then
					local E = Shared.Effects(Player)
					if (E.NightPower or 0) ~= 0 or (E.DamageByDay or 0) ~= 0 or (E.FullMoonPower or 0) ~= 0 or (E.NewMoonPower or 0) ~= 0 or (E.NewMoonStealth or 0) ~= 0
						or workspace:GetAttribute(`NHMoonEvent`) ~= nil or Player.Character:GetAttribute(`NHMoonEventOn`) then
						Shared.Apply(Player)
						Player.Character:SetAttribute(`NHMoonEventOn`, if workspace:GetAttribute(`NHMoonEvent`) ~= nil then true else nil)
					end
					local Regen = E.LowHealthRegen or 0
					if Regen > 0 and Humanoid.Health > 0 and Humanoid.Health < Humanoid.MaxHealth * 0.3 and not Player.Character:GetAttribute(`DownedUntil`) then
						Humanoid.Health = math.min(Humanoid.MaxHealth, Humanoid.Health + 1 + Regen * 5)
					end
					-- base regeneration out of combat (Known bug #3: nothing healed you outside getting up from downed):
					-- once your combat tag has run out (Features.CombatTag, 30 s after your last exchange), 2% of max health a second
					local Tagged = (Player:GetAttribute(`CombatTagUntil`) or 0) > workspace:GetServerTimeNow()
					-- (kit 1.79) the Night Chill pauses it (Services.Features.Kit sets NHChilled)
					if not Tagged and Humanoid.Health > 0 and Humanoid.Health < Humanoid.MaxHealth and not Player.Character:GetAttribute(`DownedUntil`) and Player:GetAttribute(`InMainMenu`) ~= true
						and Player.Character:GetAttribute(`NHChilled`) ~= true then
						Humanoid.Health = math.min(Humanoid.MaxHealth, Humanoid.Health + Humanoid.MaxHealth * OUT_OF_COMBAT_REGEN)
					end
				end
			end
		end
	end)
end

---| Testing |---

function Shared.AwardForTests(Player: Player, Amount: number, Category: string?) return Shared.Award(Player, Amount, Category, `Test`) end

return Shared
