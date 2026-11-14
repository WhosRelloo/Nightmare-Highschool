--[[
	Body (server). Services.Features.Body   (Hunger 1.0: docs/Hunger-and-Body-Concept.md, phases 1 and 2)
	Every race's hunger: a need from 0 to 100 that falls while you play and rises when you eat your race's food
	(Config.Body). The server decides everything: the client never sends a hunger value.

	  * Decay: Config.Body.DecayRate (the race, sub-race, day or night, full / new / crimson moon), worked out from the
	    server clock every few seconds. It pauses in the main menu and while evolving.
	  * Offline: on load, the time away (os.time() since LastTick) takes hunger down at Config.Body.OfflineRate, never
	    below OfflineFloor (35). A save already under the floor stays where it was.
	  * Eating: Inventory.Use / KitEat call Shared.Ate / Shared.AteHeal after the item is used (the 12 s "full"
	    cooldown is the rate limit). Racial grips: RaceAction calls Shared.Fed with the grip's Kind.
	  * Wraiths (until phase 4's warmth): +2 a minute with 3+ others within 12 studs.
	  * A race change (the bite, a race spin) puts hunger at Config.Body.TurnedTo (60) if it was lower.
	  * Effects: the band's (Config.Body.BandEffects) and the Stuffed food coma, added by Progression as "Hunger".

	Saved in PlayerData.Body through ProfileService only: the profile table is updated in place every tick (autosaved
	by ProfileService, like the kit's fuel), and through Data.UpdateState SetBody on each band change and meal.
	Player attributes: Hunger (one decimal), HungerBand.
	Remotes ReplicatedStorage.NHBody (Ready): Get (RF) -> state, Event (RE, server -> client) "Ate" | "Fed" | "Band".
	Test: Shared.TestSet(P, Hunger), Shared.TestTick(P, Seconds), Shared.State(P).
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

local Data = require(ServerScriptService.Services.Player.Data)
local Config = require(ReplicatedStorage.Config.Body)
local Lineage = require(ReplicatedStorage.Lineage)

local Shared = {}
local Local = {}

local TICK = 5            -- seconds between decay steps
local SAVE_EVERY = 60     -- seconds between quiet SetBody saves (the profile table itself is updated every tick)

local St = {} :: { [Player]: { Hunger: number, Band: string, Coma: number, LastSave: number, Clock: number } }
local LastCall = {} :: { [Player]: number }
local EventRE: RemoteEvent? = nil

local function try(Path: { string })
	local Ok, M = pcall(function()
		local X: Instance = ServerScriptService
		for _, N in Path do X = X:FindFirstChild(N) :: Instance end
		return require(X :: ModuleScript)
	end)
	return if Ok then M else nil
end

---| the world: night and moons |---

function Local.Ctx()
	local Clock = try({ `Services`, `School`, `SchoolClock` })
	local Ok, S = pcall(function() return Clock.GetState() end)
	local Hour = Ok and S and S.Hour
	local Day = Ok and S and S.Day
	local Night = typeof(Hour) == `number` and (Hour >= 20 or Hour < 6)
	local Ctx = { Night = Night; FullMoon = false; NewMoon = false; Crimson = false }
	if Night and Day then
		pcall(function() Ctx.FullMoon = Lineage.IsFullMoon(Day, Hour) == true end)
		pcall(function() Ctx.NewMoon = Lineage.IsNewMoon and Lineage.IsNewMoon(Day, Hour) == true end)
		-- (1.41) a crimson moon: the vampires' night (Features.MoonPhases publishes tonight's event)
		local Ev = workspace:GetAttribute(`NHMoonEvent`)
		Ctx.Crimson = typeof(Ev) == `string` and Ev:lower():find(`crimson`) ~= nil
	end
	return Ctx
end

local function raceOf(P: Player): (string, string?)
	return P:GetAttribute(`Race`) or `Human`, P:GetAttribute(`SubRace`)
end

---| data |---

function Local.Profile(P: Player)
	return Data.GetProfile(P)
end

-- the race on this save (PlayerData.Lineage.Race, the server's own roll)
function Local.SaveRace(P: Player): string?
	local Profile = Local.Profile(P)
	local L = Profile and Profile.Lineage
	return typeof(L) == `table` and typeof(L.Race) == `string` and L.Race or nil
end

-- the save as it should be now (from the live state when there is one)
function Local.Record(P: Player)
	local S = St[P]
	local Profile = Local.Profile(P)
	local Saved = Config.Sanitize(Profile and Profile.Body)
	Saved.Hunger = if S then math.floor(S.Hunger * 100 + 0.5) / 100 else Saved.Hunger
	Saved.LastTick = os.time()
	Saved.Race = Local.SaveRace(P) or Saved.Race
	return Saved
end

-- Quiet: update the profile table in place (ProfileService autosaves it) without telling the client
function Local.Save(P: Player, Quiet: boolean?)
	local Profile = Local.Profile(P)
	if not Profile then return end
	local Rec = Local.Record(P)
	if Quiet then
		Profile.Body = Rec
	else
		Data.UpdateState(P, { type = `SetBody`; body = Rec })
		if St[P] then St[P].LastSave = os.clock() end
	end
end

-- first look at a save this session: migrate, then the time away
function Local.Load(P: Player)
	local Profile = Local.Profile(P)
	if not Profile then return end
	local Raw = Profile.Body
	local B = Config.Sanitize(Raw)
	if typeof(Raw) ~= `table` or Raw.V == nil then
		-- a save from before hunger: start Full. Training's reserved Fed (0-100, never written before) is folded in
		-- if it ever held a value.
		local Fed = typeof(Profile.Training) == `table` and Profile.Training.Fed
		B.Hunger = if typeof(Fed) == `number` and Fed > 0 then math.clamp(Fed, Config.OfflineFloor, Config.Max) else Config.Start
		B.LastTick = os.time()
	elseif B.LastTick > 0 then
		local Away = math.clamp(os.time() - B.LastTick, 0, 30 * 86400)
		if B.Hunger > Config.OfflineFloor then
			local RaceId, SubId = raceOf(P)
			B.Hunger = math.max(Config.OfflineFloor, B.Hunger - Away * Config.OfflineDecay(RaceId, SubId))
		end
	end
	St[P] = { Hunger = B.Hunger; Band = Config.Band(B.Hunger); Coma = 0; LastSave = os.clock(); Clock = os.clock() }
	Local.Publish(P)
	Local.Save(P, false)
	Local.Reapply(P)
end

---| state |---

function Local.Publish(P: Player)
	local S = St[P]
	if not S then return end
	P:SetAttribute(`Hunger`, math.floor(S.Hunger * 10 + 0.5) / 10)
	P:SetAttribute(`HungerBand`, S.Band)
end

function Local.Reapply(P: Player)
	pcall(function()
		local Progression = require(ServerScriptService.Services.Player.Progression)
		Progression.Apply(P)
		Progression.Notify(P)
	end)
end

function Local.Fire(P: Player, Kind: string, D: any?)
	if EventRE and P.Parent then EventRE:FireClient(P, Kind, D) end
end

-- set hunger; handles the band change, the food coma, the attributes and saving
function Local.Set(P: Player, Value: number, Why: string?, Quiet: boolean?)
	local S = St[P]
	if not S then return end
	local Old = S.Band
	S.Hunger = math.clamp(Value, 0, Config.Max)
	local New = Config.Band(S.Hunger)
	S.Band = New
	Local.Publish(P)
	if New ~= Old then
		if New == `Stuffed` then S.Coma = workspace:GetServerTimeNow() + Config.ComaSeconds end
		Local.Fire(P, `Band`, { Band = New; From = Old; Why = Why })
		Local.Save(P, false)
		Local.Reapply(P)
	elseif not Quiet then
		Local.Save(P, false)
	else
		Local.Save(P, true)
	end
end

function Shared.Get(P: Player): number?
	local S = St[P]
	return S and S.Hunger
end

function Shared.State(P: Player)
	local S = St[P]
	if not S then return nil end
	local RaceId, SubId = raceOf(P)
	return {
		Hunger = S.Hunger; Band = S.Band; Race = RaceId; Sub = SubId;
		Word = Config.Word(RaceId, S.Band);
		Rate = Config.DecayRate(RaceId, SubId, Local.Ctx()) * 3600; -- per hour, for the tooltip
		Coma = if S.Coma > workspace:GetServerTimeNow() then S.Coma else nil;
		EatsFood = Config.EatsFood(RaceId);
	}
end

-- the band's effects for Progression (source "Hunger")
function Shared.Effects(P: Player)
	local S = St[P]
	if not S then return {} end
	local E = {}
	for K, V in Config.BandEffects[S.Band] or {} do E[K] = (E[K] or 0) + V end
	if S.Coma > workspace:GetServerTimeNow() then
		for K, V in Config.ComaEffects do E[K] = (E[K] or 0) + V end
	end
	return E
end

---| eating and feeding |---

-- after Inventory.Use has used up the item (It is the Config.Items entry)
function Shared.Ate(P: Player, It): number
	if not (St[P] and typeof(It) == `table`) then return 0 end
	local RaceId, SubId = raceOf(P)
	local Gain = Config.Gain(RaceId, SubId, It)
	Local.Fire(P, `Ate`, { Id = It.Id; Amount = Gain; Duration = It.Duration or 1 })
	if Gain > 0 then Local.Set(P, St[P].Hunger + Gain, `Ate`) end
	return Gain
end

-- a snack-tin bite (Inventory.KitEat): plain food of that heal
function Shared.AteHeal(P: Player, Heal: number): number
	if not St[P] or typeof(Heal) ~= `number` then return 0 end
	local RaceId, SubId = raceOf(P)
	local Gain = Config.Gain(RaceId, SubId, { Id = `Tin`; Kind = `Heal`; Heal = Heal })
	Local.Fire(P, `Ate`, { Id = `Tin`; Amount = Gain; Duration = 3 })
	if Gain > 0 then Local.Set(P, St[P].Hunger + Gain, `Ate`) end
	return Gain
end

-- a racial grip finished (Features.RaceAction, Kind = BloodDrain | EatBody | Maul | SoulSiphon | ...)
function Shared.Fed(P: Player, Kind: string): number
	if not St[P] then return 0 end
	local RaceId = raceOf(P)
	local Gain = Config.FeedGain(RaceId, Kind)
	if Gain <= 0 then return 0 end
	Local.Fire(P, `Fed`, { Kind = Kind; Amount = Gain })
	Local.Set(P, St[P].Hunger + Gain, `Fed`)
	return Gain
end

---| the clock |---

function Local.Live(P: Player): boolean
	if P:GetAttribute(`InMainMenu`) == true then return false end
	local Char = P.Character
	local Hum = Char and Char:FindFirstChildOfClass(`Humanoid`)
	if not (Hum and Hum.Health > 0) then return false end
	if Char:GetAttribute(`NH_Evolving`) then return false end
	return true
end

-- how many other living characters are near (the Wraith's crowd)
function Local.Crowd(P: Player, Radius: number): number
	local Root = P.Character and P.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	if not Root then return 0 end
	local Live = workspace:FindFirstChild(`Live`)
	local N = 0
	for _, M in (Live and Live:GetChildren() or {}) do
		if M ~= P.Character and M:IsA(`Model`) then
			local Hum = M:FindFirstChildOfClass(`Humanoid`)
			local R = M:FindFirstChild(`HumanoidRootPart`) :: BasePart?
			if Hum and Hum.Health > 0 and R and (R.Position - Root.Position).Magnitude <= Radius then N += 1 end
		end
	end
	return N
end

function Local.Step(P: Player, Dt: number, Ctx)
	local S = St[P]
	if not S then return end
	local RaceId, SubId = raceOf(P)
	local Delta = -Config.DecayRate(RaceId, SubId, Ctx) * Dt
	local Crowd = Config.Crowd(RaceId, SubId)
	if Crowd and Local.Crowd(P, Crowd.Radius) >= Crowd.Count then Delta += Crowd.PerMinute * Dt / 60 end
	Local.Set(P, S.Hunger + Delta, `Tick`, os.clock() - S.LastSave < SAVE_EVERY)
	-- the food coma ends quietly: put the sprint back
	if S.Coma > 0 and S.Coma <= workspace:GetServerTimeNow() then
		S.Coma = 0
		Local.Reapply(P)
	end
end

function Local.Loop()
	while true do
		task.wait(TICK)
		local Ctx = Local.Ctx()
		for P, S in St do
			local Now = os.clock()
			local Dt = math.min(Now - S.Clock, TICK * 3)
			S.Clock = Now
			if P.Parent and Local.Live(P) then
				local Ok, Err = pcall(Local.Step, P, Dt, Ctx)
				if not Ok then warn(`[Body] step {P.Name}: {Err}`) end
			end
		end
	end
end

---| tests (Studio and the test bridge) |---

function Shared.TestSet(P: Player, Hunger: number): boolean
	if not St[P] or typeof(Hunger) ~= `number` then return false end
	Local.Set(P, Hunger, `Test`)
	return true
end

-- run the decay forward by Seconds of play (the real step, with the current time of day)
function Shared.TestTick(P: Player, Seconds: number): number?
	if not St[P] or typeof(Seconds) ~= `number` then return nil end
	Local.Step(P, math.clamp(Seconds, 0, 86400), Local.Ctx())
	return St[P].Hunger
end

-- (admin desk) set a student's hunger; logged by the desk
function Shared.AdminSet(P: Player, Hunger: number): boolean
	return Shared.TestSet(P, Hunger)
end

---| start |---

function Shared.OnStart()
	local F = Instance.new(`Folder`)
	F.Name = `NHBody`
	local Get = Instance.new(`RemoteFunction`)
	Get.Name = `Get`
	Get.Parent = F
	EventRE = Instance.new(`RemoteEvent`)
	EventRE.Name = `Event`
	EventRE.Parent = F
	Get.OnServerInvoke = function(P)
		local Now = os.clock()
		if LastCall[P] and Now - LastCall[P] < 0.3 then return nil end
		LastCall[P] = Now
		return Shared.State(P)
	end
	F:SetAttribute(`Ready`, true)
	F.Parent = ReplicatedStorage

	Data.ProfileLoaded:Connect(function(P) task.defer(Local.Load, P) end)
	for _, P in Players:GetPlayers() do
		if Data.GetProfile(P) then task.spawn(Local.Load, P) end
	end
	local function watch(P: Player)
		-- a new race (the bite, a race spin, the admin desk) never starts starving
		-- the Race attribute also changes when a slot loads, so this compares the save's own race with the one the
		-- hunger was last saved under
		P:GetAttributeChangedSignal(`Race`):Connect(function()
			task.defer(function()
				local S = St[P]
				local Profile = Local.Profile(P)
				if not (S and Profile) then return end
				local Now, Was = Local.SaveRace(P), Config.Sanitize(Profile.Body).Race
				if Now and Was and Now ~= Was and S.Hunger < Config.TurnedTo then
					Local.Set(P, Config.TurnedTo, `Turned`)
				else
					Local.Save(P, true)
				end
				Local.Fire(P, `Race`, nil)
			end)
		end)
	end
	Players.PlayerAdded:Connect(watch)
	for _, P in Players:GetPlayers() do watch(P) end
	Players.PlayerRemoving:Connect(function(P)
		if St[P] then Local.Save(P, true) end
		St[P], LastCall[P] = nil, nil
	end)
	game:BindToClose(function()
		for P in St do pcall(Local.Save, P, true) end
	end)
	task.spawn(Local.Loop)
end

return Shared
