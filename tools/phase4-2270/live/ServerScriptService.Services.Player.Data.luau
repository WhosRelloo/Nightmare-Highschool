local RunService = game:GetService("RunService")

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local RunService = game:GetService(`RunService`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local ProfileService = require(ServerScriptService.Packages.ProfileService)
local SignalPlus = require(ReplicatedStorage.Packages.SignalPlus)

local UpdateState = require(ReplicatedStorage.Functions.UpdateState)
local PlayerData = require(ReplicatedStorage.PlayerData)

local Trove = require(ReplicatedStorage.Packages.Trove).new()
local Packets = require(ReplicatedStorage.Remotes.Packets)

---| Type Annotation |---

export type StateAction = UpdateState.StateAction
export type PlayerData = UpdateState.PlayerData

---| Data Store |---

local DATASTORE_NAME = if RunService:IsStudio() then `[Test] Studio's Data |1S|` else `Production's DatSa`
local ProfileStore = ProfileService.GetProfileStore(DATASTORE_NAME, PlayerData.DEFAULT_PLAYER_DATA)

local Profiles : { [Player]: ProfileService.Profile < PlayerData.PlayerData > } = {}
local LoadedSlot : { [Player]: number } = {}
local Loading : { [Player]: boolean } = {}

-- Save slots (Main Menu): the profile only loads once the player picks a slot.
-- Slot 1 keeps the original key, so saves from before slots existed are slot 1.
local MenuConfig = require(ReplicatedStorage.Config.MainMenu)
local PlayerTroves : { [Player]: typeof(Trove.new()) } = {}

---| Data Services |---

local Local = {}
local Shared = {}

Shared.ProfileLoaded = SignalPlus() :: SignalPlus.Signal < Player, PlayerData.PlayerData >

function Shared.OnStart()

	---| FrameWork |---

	Packets.Start.OnServerEvent:Connect(function(Player: Player) 
		local Profile = Shared.GetProfile(Player)

		if Profile then
			Packets.SetState:FireClient(Player, Local.ClientCopy(Profile))

		end
	end)

	if RunService:IsStudio() then
		Packets.Replicate.OnServerEvent:Connect(function(Player: Player, Category: string, Effect: string, Parameters: any)

			Packets.Replicate:Fire(Category, Effect, Parameters)
		end)
	end

	---| Player Connnection |---

	-- With the main menu on, Services.Player.Slots calls Shared.LoadSlot when a slot is picked.
	if not MenuConfig.Enabled then
		for _, Player: Player in Players:GetPlayers() do
			task.spawn(Shared.LoadSlot, Player, 1)
		end
		Trove:Add( Players.PlayerAdded:Connect(function(Player) Shared.LoadSlot(Player, 1) end) )
	end
	Trove:Add( Players.PlayerRemoving:Connect( Local.RemoveProfile ) )

	---| Clean Up |---

	game:BindToClose(function() 
		Trove:Destroy()
		for _, playerTrove in PlayerTroves do
			playerTrove:Destroy()
		end
		table.clear(PlayerTroves)
	end)
end

function Shared.SlotKey(UserId: number, Slot: number): string
	if Slot == 1 then return `{UserId}'s Data` end
	return `{UserId}'s Data|Slot{Slot}`
end

-- Read-only look at a slot's save (no session lock), for the slot picker. nil = empty slot.
function Shared.ViewSlot(UserId: number, Slot: number): PlayerData?
	local Ok, Profile = pcall(function()
		return ProfileStore:ViewProfileAsync(Shared.SlotKey(UserId, Slot))
	end)
	if not Ok then
		warn(`[Data] ViewSlot {Slot}: {Profile}`)
		return nil
	end
	return Profile and Profile.Data or nil
end

function Shared.GetSlot(Player: Player): number?
	return LoadedSlot[Player]
end

-- Loads (session-locks) the chosen slot's profile. Returns true when loaded.
function Shared.LoadSlot(Player: Player, Slot: number): boolean
	if Profiles[Player] or Loading[Player] then return Profiles[Player] ~= nil end
	if typeof(Slot) ~= `number` or Slot % 1 ~= 0 or Slot < 1 or Slot > MenuConfig.SlotCount then return false end
	Loading[Player] = true
	local Ok = Local.CreateProfile(Player, Slot)
	Loading[Player] = nil
	return Ok == true
end

function Local.CreateProfile(Player: Player, Slot: number)
	local UserId = Player.UserId
	local ProfileKey = Shared.SlotKey(UserId, Slot)

	local Date = os.date(`%Y-%m-%d`)
	local Profile = ProfileStore:LoadProfileAsync(ProfileKey)

	if not Profile then
		Player:Kick(`Unable to load your Data! This Happened on {Date}.`) 
		return false
	end
	if not Player.Parent then
		Profile:Release()
		return false
	end

	Profile:ListenToRelease(function()
		Profiles[Player] = nil
		Player:Kick()

	end)

	Profile:AddUserId(UserId)
	Profile:Reconcile()
	-- (armory) Fist by default; a class you don't own goes back to Fist (Config.Armory.Migrate)
	local ArmOk, ArmErr = pcall(function() require(ReplicatedStorage.Config.Armory).Migrate(Profile.Data) end)
	if not ArmOk then warn(`[Data] armory migrate: {ArmErr}`) end

	Profiles[Player] = Profile
	LoadedSlot[Player] = Slot
	Player:SetAttribute(`Slot`, Slot)

	-- Create individual Trove for this player
	PlayerTroves[Player] = Trove.new()

	Local.CreateLeaderStats(Player)

	Shared.ProfileLoaded:Fire(Player, Profile.Data)
	Packets.SetState:FireClient(Player, Local.ClientCopy(Profile.Data))
	return true
end

-- (audit) the client's copy of the save leaves out each active quest's Secret (where a hidden item really is);
-- Quests' own sync already strips it, but these two full-profile sends didn't
function Local.ClientCopy(Data: any): any
	if typeof(Data) ~= `table` or typeof(Data.Quests) ~= `table` or typeof(Data.Quests.Active) ~= `table` then return Data end
	local Copy = table.clone(Data)
	Copy.Quests = table.clone(Data.Quests)
	Copy.Quests.Active = {}
	for Id, S in Data.Quests.Active do
		if typeof(S) == `table` and S.Secret ~= nil then
			local C = table.clone(S)
			C.Secret = nil
			Copy.Quests.Active[Id] = C
		else
			Copy.Quests.Active[Id] = S
		end
	end
	return Copy
end

function Local.RemoveProfile(Player: Player)
	local Profile = Profiles[Player]

	if Profile then
		Profile:Release()
	end
	LoadedSlot[Player] = nil
	Loading[Player] = nil

	-- Clean up player-specific Trove
	if PlayerTroves[Player] then
		PlayerTroves[Player]:Destroy()
		PlayerTroves[Player] = nil
	end

end

function Local.CreateLeaderStats(Player: Player)
	local Profile = Profiles[Player]

	if not Profile then 
		return 
	end

	local Data = Profile.Data

	if not Data then 
		return 
	end

	local LeaderStats = Instance.new(`Folder`, Player)
	LeaderStats.Name = `leaderstats`

	local Yen = Instance.new(`NumberValue`, LeaderStats)
	Yen.Name = `Yen`
	Yen.Value = Data.Yen

	local Kills = Instance.new(`IntValue`, LeaderStats)
	Kills.Name = `Kills`
	Kills.Value = Data.Kills or 0
end

function Shared.UpdateState(Player: Player, Action: StateAction)
	local Profile = Profiles[Player]

	if not Profile then 
		return 
	end

	UpdateState(Profile.Data, Action)
	Packets.UpdateState:FireClient(Player, Action)

	local LeaderStats = Player:FindFirstChild(`leaderstats`)
	if LeaderStats and Action.type == `UpdateYen` and LeaderStats:FindFirstChild(`Yen`) then
		LeaderStats.Yen.Value = Profile.Data.Yen
	end
	if LeaderStats and Action.type == `AddKill` and LeaderStats:FindFirstChild(`Kills`) then
		LeaderStats.Kills.Value = Profile.Data.Kills or 0
	end
end

function Shared.GetProfile(Player: Player): PlayerData
	local Profile = Profiles[Player]

	if Profile then 
		return Profile.Data :: PlayerData
	end
end

-- (audit) the live ProfileService profile (or nil), so Purchases can wait until a receipt is really saved
function Shared.GetProfileObject(Player: Player)
	return Profiles[Player]
end

return Shared
