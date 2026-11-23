--[[
	Evolution (server): race hunger, rites and tier-ups (Races Phase 3).

	Hunger (Lineage.HungerName) fills from kills and grip finishes, weighted by race:
	  Vampire: night kills x2, finishes +2      Werewolf: night kills x2, full moon x4, finishes +1
	  Ghoul: finishes +3 (kills +0.5)           Wraith: kills +1, finishes +1
	  Human: kills +1, monster players x2       Priest: kills +1, undead players x2, attending class +1
	At Lineage.HungerNeed[tier] the rite for that tier (Config.Quests "Rite<Race><Tier>") starts on its own.
	Finishing the rite evolves you: when you're safe (not downed, duelling, busy or hit in the last 6 s) the
	tier rises, you're frozen and can't be hurt (character attribute NH_Evolving), and every client plays the
	tier-up cutscene (Controllers.Gui.Evolution): your camera, everyone's view of the pose and effects.

	Remotes: ReplicatedStorage.NHEvolve.Play (server -> all: player, race, tier, tierName, skippable)
	         ReplicatedStorage.NHEvolve.Done (client -> server: my cutscene finished or was skipped)
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local Lineage = require(ReplicatedStorage:WaitForChild(`Lineage`))
local SchoolTime = require(game:GetService("ReplicatedStorage"):WaitForChild("Functions"):WaitForChild("SchoolTime")) -- (2.22.0) shared night windows

local SAFE_AFTER_HIT = 6
local CUTSCENE_TIMEOUT = 16

local Local = {}
local Shared = {}
local LastHit = setmetatable({}, { __mode = `k` }) :: { [Model]: number }
local Pending = {} :: { [Player]: number }     -- tier waiting to be played
local Playing = {} :: { [Player]: { Restore: () -> () } }
local Remotes = nil

local function try(Path: { string })
	local M = ServerScriptService
	for _, N in Path do M = M and M:FindFirstChild(N) end
	if not M then return nil end
	local Ok, Mod = pcall(require, M)
	return if Ok then Mod else nil
end

function Local.Clock()
	local Clock = try({ `Services`, `School`, `SchoolClock` })
	local Ok, State = pcall(function() return Clock.GetState() end)
	if not (Ok and State) then return false, false end
	local Night = SchoolTime.IsNight(State.Hour)
	return Night, Lineage.IsFullMoon(State.Day, State.Hour)
end

function Local.Notify(Player: Player, Data)
	local N = try({ `Services`, `Features`, `Notifications` })
	if N then pcall(N.Notify, Player, Data) end
end

---| Hunger |---

-- how much hunger a kill / finish is worth for this player's race
function Local.Worth(Player: Player, Kind: string, Victim: Model?): number
	local Race = Player:GetAttribute(`Race`)
	local Night, FullMoon = Local.Clock()
	local VictimPlayer = Victim and Players:GetPlayerFromCharacter(Victim)
	local VictimRace = VictimPlayer and VictimPlayer:GetAttribute(`Race`)
	if Kind == `Kill` then
		if Race == `Vampire` then return if Night then 2 else 1
		elseif Race == `Werewolf` then return if FullMoon then 4 elseif Night then 2 else 1
		elseif Race == `Ghoul` then return 0.5
		elseif Race == `Human` then return if Lineage.IsMonster(VictimRace) then 2 else 1
		elseif Race == `Priest` then return if Lineage.IsUndead(VictimRace) then 2 else 1
		end
		return 1
	elseif Kind == `Finish` then
		return ({ Vampire = 2; Werewolf = 1; Ghoul = 3; Wraith = 1 })[Race] or 0
	elseif Kind == `Attend` then
		return if Race == `Priest` then 1 else 0
	end
	return 0
end

function Shared.Feed(Player: Player, Amount: number, Reason: string?)
	if Amount <= 0 then return end
	local L = Lineage.AddHunger(Player, Amount)
	if L then Local.CheckRite(Player, L) end
end

-- hunger full -> start that tier's rite (once)
function Local.CheckRite(Player: Player, L)
	L = L or (Lineage.Current and Lineage.Current(Player))
	if not (L and L.Race) or (L.Tier or 1) >= 3 then return end
	local Tier = L.Tier + 1
	if (L.Hunger or 0) < (Lineage.HungerNeed[Tier] or math.huge) then return end
	local Quests = try({ `Services`, `Quests`, `Quests` })
	local Id = Lineage.RiteFor(L.Race, Tier)
	if not Quests or Quests.IsActive(Player, Id) or Quests.IsDone(Player, Id) then return end
	if Quests.Start(Player, Id) then
		local Name = Lineage.HungerName[L.Race] or `Hunger`
		Local.Notify(Player, { Title = `Your blood stirs`; Text = `{Name} is full. A rite is open in your journal: become {Lineage.TierName(L.Race, Tier)}.`; Kind = `Good`; Duration = 8 })
	end
end

---| Tier-up |---

function Local.Safe(Player: Player): boolean
	local C = Player.Character
	local H = C and C:FindFirstChildOfClass(`Humanoid`)
	if not (H and H.Health > 0) or Player:GetAttribute(`InMainMenu`) then return false end
	if H:GetAttribute(`Downed`) or C:GetAttribute(`Dueling`) or C:GetAttribute(`Protected`) or C:GetAttribute(`GrippedBy`) then return false end
	local Downed = try({ `Services`, `Features`, `Downed` })
	if Downed and (Downed.IsDowned(C) or Downed.IsBusy(C)) then return false end
	if LastHit[C] and os.clock() - LastHit[C] < SAFE_AFTER_HIT then return false end
	return true
end

function Local.Freeze(Character: Model): () -> ()
	local H = Character:FindFirstChildOfClass(`Humanoid`)
	local Root = Character:FindFirstChild(`HumanoidRootPart`)
	local Speed, Jump, JumpH = H.WalkSpeed, H.JumpPower, H.JumpHeight
	-- (audit) save the base speed, not CombatSpeed's slowed one (restoring that made it slow again)
	local Mult = H:GetAttribute(`NH_SpeedMult`)
	if typeof(Mult) == `number` and Mult > 0 then Speed = Speed / Mult end
	H.WalkSpeed = 0; H.JumpPower = 0; H.JumpHeight = 0
	if Root then Root.Anchored = true end
	Character:SetAttribute(`NH_Evolving`, true)
	return function()
		if Character.Parent then
			Character:SetAttribute(`NH_Evolving`, nil)
			if Root and Root.Parent then Root.Anchored = false end
			if H.Parent then
				if H.WalkSpeed == 0 then H.WalkSpeed = if Speed > 0 then Speed else 14.4 end
				H.JumpPower = Jump; H.JumpHeight = JumpH
			end
		end
	end
end

-- evolve now (the server has already decided it's allowed) and play the cutscene everywhere
function Shared.Evolve(Player: Player, Tier: number): boolean
	local Ok, L = Lineage.Evolve(Player, Tier)
	if not Ok then return false end
	local Character = Player.Character
	local Key = `{L.Race}:{Tier}`
	local Skippable = Lineage.HasSeen(Player, Key)
	if Character and Character:FindFirstChildOfClass(`Humanoid`) then
		Playing[Player] = { Restore = Local.Freeze(Character) }
		Remotes.Play:FireAllClients(Player, L.Race, Tier, Lineage.TierName(L.Race, Tier), Skippable)
		local Token = Playing[Player]
		task.delay(CUTSCENE_TIMEOUT, function()
			if Playing[Player] == Token then Local.Finish(Player) end
		end)
	end
	Lineage.MarkSeen(Player, Key)
	-- VFX P1-17: a Moment banner instead of a toast (the toast used to expire behind the cutscene; the banner waits for it)
	local Fx = try({ `Services`, `Features`, `Fx` })
	if Fx then
		Fx.Fire(Player, `Evolved`, { Race = L.Race; Tier = Tier; Name = Lineage.TierName(L.Race, Tier) })
	else
		Local.Notify(Player, { Title = `Evolved`; Text = `You are now {Lineage.TierName(L.Race, Tier)} (Tier {Tier}).`; Kind = `Good`; Duration = 6 })
	end
	task.defer(Local.CheckRite, Player)
	return true
end

function Local.Finish(Player: Player)
	local P = Playing[Player]
	Playing[Player] = nil
	if P then pcall(P.Restore) end
end

-- rite finished: wait until it's safe, then evolve
function Local.Queue(Player: Player, Tier: number)
	Pending[Player] = Tier
	task.spawn(function()
		local Waited = 0
		while Pending[Player] == Tier and Player.Parent do
			if Local.Safe(Player) then
				Pending[Player] = nil
				Shared.Evolve(Player, Tier)
				return
			end
			if Waited == 0 then
				Local.Notify(Player, { Title = `Rite complete`; Text = `Get somewhere safe. Your blood will turn when nothing is hunting you.`; Kind = `Info`; Duration = 6 })
			end
			Waited += 1
			task.wait(1)
		end
	end)
end

---| Start |---

function Shared.OnStart()
	local Folder = ReplicatedStorage:FindFirstChild(`NHEvolve`) or Instance.new(`Folder`)
	Folder.Name = `NHEvolve`
	local Play = Folder:FindFirstChild(`Play`) or Instance.new(`RemoteEvent`); Play.Name = `Play`; Play.Parent = Folder
	local Done = Folder:FindFirstChild(`Done`) or Instance.new(`RemoteEvent`); Done.Name = `Done`; Done.Parent = Folder
	Folder.Parent = ReplicatedStorage
	Remotes = { Play = Play; Done = Done }
	Done.OnServerEvent:Connect(function(Player) Local.Finish(Player) end)

	local Downed = try({ `Services`, `Features`, `Downed` })
	if Downed then
		Downed.OnDamage:Connect(function(Target) LastHit[Target] = os.clock() end)
		Downed.OnDefeated:Connect(function(Target, Killer)
			local Player = Killer and Players:GetPlayerFromCharacter(Killer)
			if Player and Killer ~= Target then Shared.Feed(Player, Local.Worth(Player, `Kill`, Target), `Kill`) end
		end)
		Downed.OnExecuted:Connect(function(Gripper, Target)
			local Player = Players:GetPlayerFromCharacter(Gripper)
			if Player then Shared.Feed(Player, Local.Worth(Player, `Finish`, Target), `Finish`) end
		end)
	end
	local Attendance = try({ `Services`, `School`, `Attendance` })
	if Attendance and Attendance.Recorded then
		Attendance.Recorded:Connect(function(Player, Record)
			local Status = typeof(Record) == `table` and (Record.Status or Record.Result) or Record
			if Status == `Present` then Shared.Feed(Player, Local.Worth(Player, `Attend`), `Class`) end
		end)
	end
	local Quests = try({ `Services`, `Quests`, `Quests` })
	if Quests and Quests.Completed then
		Quests.Completed:Connect(function(Player, Id)
			local Race, Tier = Player:GetAttribute(`Race`), (Player:GetAttribute(`RaceTier`) or 1) + 1
			if Race and Id == Lineage.RiteFor(Race, Tier) then Local.Queue(Player, Tier) end
		end)
	end
	-- a save that already has full hunger gets its rite on load
	local Data = try({ `Services`, `Player`, `Data` })
	if Data and Data.ProfileLoaded then
		Data.ProfileLoaded:Connect(function(Player)
			task.delay(3, Local.CheckRite, Player)
		end)
	end
	Players.PlayerRemoving:Connect(function(Player)
		Pending[Player] = nil
		Local.Finish(Player)
	end)
end

---| Testing |---

function Shared.CheckRiteForTests(Player: Player) Local.CheckRite(Player) end

return Shared
