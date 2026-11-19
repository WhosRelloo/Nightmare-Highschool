--[[
	The Ring (server authoritative). Opt-in PvP and the ring champion.

	Player duels: two students stand on the two DuelPad parts for 3 seconds -> duel starts. First one
	downed loses; leaving the ring area (QuestArea = DuelRing) forfeits; 2 minutes = draw. Both
	fighters are Protected (nobody can carry or grip them) and the loser is picked back up straight
	away. The ring area is tagged CombatAllowed so hall monitors don't treat it as fighting.
	A winner only gets credit against the same opponent once per in-game hour (no win-trading).

	Champion: Bruno's dialogue calls StartChampion(Player); an AI fighter that only targets that
	player spawns on pad 2.

	Signals: Won(WinnerPlayer, LoserModel), ChampionDefeated(Player), ChampionWon(Player)
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local SignalPlus = require(ReplicatedStorage.Packages.SignalPlus)
local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local NPCConfig = require(ReplicatedStorage.Config.NPC)

local Places = require(script.Parent.Places)
local SchoolClock = require(ServerScriptService.Services.School.SchoolClock)
local Downed = require(ServerScriptService.Services.Features.Downed)
local Notifications = require(ServerScriptService.Services.Features.Notifications)

local COUNTDOWN = 3
local DUEL_SECONDS = 120
local BUSY = { `Downed`, `Carried`, `Gripped`, `Gripping`, `Carrying`, `InActivity` }

local Duel = nil :: any
local Countdown = nil :: any
-- after a duel both fighters must step off the pads before another countdown can start
local Resting = {} :: { [Player]: boolean }
local PairCredit = {} :: { [string]: string } -- "winnerId:loserId" -> hour key

local Local = {}
local Shared = {}

Shared.Won = SignalPlus()
Shared.ChampionDefeated = SignalPlus()
Shared.ChampionWon = SignalPlus()

function Local.Alive(Model: Model?): boolean
	local Humanoid = Model and Model.Parent and Model:FindFirstChildWhichIsA(`Humanoid`)
	return Humanoid ~= nil and Humanoid.Health > 0
end

function Local.Root(Model: Model?): BasePart?
	return Model and Model:FindFirstChild(`HumanoidRootPart`) :: BasePart?
end

function Local.Pads(): (BasePart?, BasePart?)
	return Places.Find(`DuelPad`, 1), Places.Find(`DuelPad`, 2)
end

function Local.OnPad(Pad: BasePart?): Player?
	if not Pad then return nil end
	for _, Player in Players:GetPlayers() do
		local Character = Player.Character
		local Root = Local.Root(Character)
		local Humanoid = Character and Character:FindFirstChildWhichIsA(`Humanoid`)
		if Root and Humanoid and Humanoid.Health > 0 and not Humanoid:GetAttribute(`Downed`)
			and not StateManager.HasState(Character, BUSY) and Places.Inside(Pad, Root.Position, 6) then
			return Player
		end
	end
	return nil
end

function Local.Tell(Model: Model?, Data)
	local Player = Model and Players:GetPlayerFromCharacter(Model)
	if Player then Notifications.Notify(Player, Data) end
end

function Local.SetPads(Color: Color3?)
	local A, B = Local.Pads()
	for _, Pad in { A, B } do
		if Pad then Pad.Color = Color or Pad:GetAttribute(`IdleColor`) or Pad.Color end
	end
end

function Shared.IsBusy(): boolean
	return Duel ~= nil or Countdown ~= nil
end

function Shared.Start(A: Model, B: Model, Kind: string, Player: Player?)
	Duel = { A = A; B = B; Kind = Kind; Player = Player; Ends = os.clock() + DUEL_SECONDS }
	for _, Model in { A, B } do
		Model:SetAttribute(`Protected`, true)
		Model:SetAttribute(`Dueling`, true)
	end
	-- (audit) link the two fighters: DamageLogic and grabs only let a duelist's own opponent hit them
	for _, Pair in { { A, B }, { B, A } } do
		local Old = Pair[1]:FindFirstChild(`DuelOpponent`)
		if Old then Old:Destroy() end
		local Link = Instance.new(`ObjectValue`)
		Link.Name = `DuelOpponent`
		Link.Value = Pair[2]
		Link.Parent = Pair[1]
	end
	Local.SetPads(Color3.fromRGB(200, 60, 60))
	local Text = if Kind == `Champion` then `Down the champion. Stay inside the ring.` else `First one down loses. Leave the ring and you forfeit.`
	Local.Tell(A, { Title = `FIGHT!`; Text = Text; Kind = `Warning`; Duration = 4 })
	Local.Tell(B, { Title = `FIGHT!`; Text = Text; Kind = `Warning`; Duration = 4 })
end

function Local.Finish(Winner: Model?, Loser: Model?, Reason: string, LoserReason: string?)
	local D = Duel
	if not D then return end
	Duel = nil
	Local.SetPads(nil)
	LoserReason = LoserReason or Reason
	for _, Model in { D.A, D.B } do
		local P = Model and Players:GetPlayerFromCharacter(Model)
		if P then Resting[P] = true end
	end

	local function Release(Model: Model?)
		if not Model then return end
		Model:SetAttribute(`Dueling`, nil)
		local Link = Model:FindFirstChild(`DuelOpponent`) -- (audit) unlink (set in Shared.Start)
		if Link then Link:Destroy() end
		if Downed.IsDowned(Model) then pcall(Downed.Recover, Model) end
		Model:SetAttribute(`Protected`, nil)
	end

	if D.Kind == `Champion` then
		local Champion = D.B
		local Player = D.Player
		if Winner == D.A and Player then
			Notifications.Notify(Player, { Title = `The champion is down!`; Text = `Bruno looks impressed.`; Kind = `Good`; Duration = 5 })
			Shared.ChampionDefeated:Fire(Player)
		elseif Player then
			Notifications.Notify(Player, { Title = `The champion wins`; Text = `{LoserReason} Talk to Bruno for a rematch.`; Kind = `Bad`; Duration = 5 })
			Shared.ChampionWon:Fire(Player)
		end
		task.delay(1.5, function()
			Release(D.A)
			if Champion and Champion.Parent then Champion:Destroy() end
		end)
		return
	end

	task.delay(1.5, function()
		Release(D.A)
		Release(D.B)
	end)

	if not Winner then
		Local.Tell(D.A, { Title = `Draw`; Text = Reason; Kind = `Info`; Duration = 4 })
		Local.Tell(D.B, { Title = `Draw`; Text = Reason; Kind = `Info`; Duration = 4 })
		return
	end

	Local.Tell(Loser, { Title = `You lost the duel`; Text = LoserReason; Kind = `Bad`; Duration = 4 })
	local WinnerPlayer = Players:GetPlayerFromCharacter(Winner)
	if not WinnerPlayer then return end

	local LoserPlayer = Loser and Players:GetPlayerFromCharacter(Loser)
	local State = SchoolClock.GetState()
	local HourKey = `{State.Day}-{math.floor(State.Hour)}`
	local PairKey = `{WinnerPlayer.UserId}:{if LoserPlayer then LoserPlayer.UserId else (Loser and Loser.Name or `?`)}`
	if PairCredit[PairKey] == HourKey then
		Notifications.Notify(WinnerPlayer, { Title = `You won the duel`; Text = `No credit: you already beat them this hour.`; Kind = `Info`; Duration = 4 })
		return
	end
	PairCredit[PairKey] = HourKey
	Notifications.Notify(WinnerPlayer, { Title = `You won the duel!`; Text = Reason; Kind = `Good`; Duration = 4 })
	Shared.Won:Fire(WinnerPlayer, Loser)
end

function Local.Tick()
	local Ring = Places.Find(`QuestArea`, `DuelRing`)
	if Duel then
		local D = Duel
		for _, Pair in { { D.A, D.B }, { D.B, D.A } } do
			local Me, Other = Pair[1], Pair[2]
			if not Local.Alive(Me) then
				Local.Finish(Other, Me, `Your opponent is gone.`)
				return
			end
			local Root = Local.Root(Me)
			if Ring and Root and not Places.Inside(Ring, Root.Position, 10) and not Downed.IsDowned(Me) then
				Local.Finish(Other, Me, `Your opponent left the ring.`, `You left the ring.`)
				return
			end
		end
		if os.clock() > D.Ends then Local.Finish(nil, nil, `Time's up.`) end
		return
	end

	-- Pads: both occupied by two different students for COUNTDOWN seconds.
	local PadA, PadB = Local.Pads()
	local A, B = Local.OnPad(PadA), Local.OnPad(PadB)
	-- a fighter who just finished a duel has to step off before the pads count them again
	for P in Resting do
		if P ~= A and P ~= B then Resting[P] = nil end
	end
	if A and Resting[A] then A = nil end
	if B and Resting[B] then B = nil end
	if A and B and A ~= B then
		if not Countdown or Countdown.A ~= A or Countdown.B ~= B then
			Countdown = { A = A; B = B; At = os.clock() }
			Local.SetPads(Color3.fromRGB(230, 180, 60))
			for _, P in { A, B } do
				Notifications.Notify(P, { Title = `Duel in {COUNTDOWN}...`; Text = `Step off the pad to back out.`; Kind = `Warning`; Duration = COUNTDOWN })
			end
		elseif os.clock() - Countdown.At >= COUNTDOWN then
			Countdown = nil
			Shared.Start(A.Character, B.Character, `Duel`)
		end
	elseif Countdown then
		Countdown = nil
		Local.SetPads(nil)
	end
end

---| Champion |---

function Shared.StartChampion(Player: Player): (boolean, string?)
	if Shared.IsBusy() then return false, `The ring is busy.` end
	local Character = Player.Character
	if not Local.Alive(Character) or Downed.IsDowned(Character) then return false, `You can't fight like that.` end
	local PadA, PadB = Local.Pads()
	if not PadA or not PadB then return false, `There's no ring here.` end

	local AI = require(ServerScriptService.Services.AI.AI)
	local Settings = table.clone(NPCConfig.Default)
	Settings.Tier = `Nightmare` -- the hardest fighter in the game (Config.NPC.Tiers, 1.23)
	Settings.AggroRange = 60
	Settings.ChaseRange = 70
	Settings.CorpseTime = 1
	Settings.RespawnTime = nil
	Settings.FixedTarget = function() return Player.Character end

	local Npc = AI.Spawn(workspace.Live, nil, nil, Settings)
	local Champion = Npc and Npc.Character
	if not Champion then return false, `The champion didn't show up.` end
	Champion.Name = `Ring Champion`
	Champion:SetAttribute(`QuestTarget`, `RingChampion`)
	Champion:PivotTo(PadB.CFrame + Vector3.new(0, 3, 0))
	-- into the ring under the teleport veil (VFX P2-7)
	require(ServerScriptService.Services.Features.Fx).VeilMove(Player, CFrame.lookAt(PadA.Position + Vector3.new(0, 3, 0), PadB.Position + Vector3.new(0, 3, 0)))

	Shared.Start(Character, Champion, `Champion`, Player)
	return true
end

---| Testing |---

-- Start a player duel against any character (e.g. a test dummy standing in for a second player).
function Shared.DuelForTests(Player: Player, Opponent: Model): boolean
	if Shared.IsBusy() or not Player.Character then return false end
	Shared.Start(Player.Character, Opponent, `Duel`)
	return true
end

function Shared.StateForTests()
	return Duel and { Kind = Duel.Kind; A = Duel.A.Name; B = Duel.B.Name } or (Countdown and { Countdown = true }) or nil
end

function Shared.OnStart()
	Downed.OnDowned:Connect(function(Target)
		local D = Duel
		if not D then return end
		if Target == D.A then
			Local.Finish(D.B, D.A, `Your opponent went down.`, `You went down.`)
		elseif Target == D.B then
			Local.Finish(D.A, D.B, `Your opponent went down.`, `You went down.`)
		end
	end)

	local PadA, PadB = Local.Pads()
	for _, Pad in { PadA, PadB } do
		if Pad and Pad:GetAttribute(`IdleColor`) == nil then Pad:SetAttribute(`IdleColor`, Pad.Color) end
	end

	task.spawn(function()
		while true do
			task.wait(0.25)
			local Ok, Err = pcall(Local.Tick)
			if not Ok then warn(`[Duels] {Err}`) end
		end
	end)
end

return Shared
