--[[
	Player.Data: the Map place's NO-SAVE stand-in (NH core add-on, 2026-11-05).

	The Map place is for walking the builder's map with the game's feel. It never touches the real saves:
	there is no ProfileService and no DataStore here. Every player gets a fresh in-memory copy of
	PlayerData.DEFAULT_PLAYER_DATA when they join, and it is thrown away when they leave.

	Same API as NH Combat Test's Services.Player.Data (GetProfile, UpdateState, ProfileLoaded, LoadSlot,
	GetSlot, ViewSlot, SlotKey), so the copied systems work unchanged.
]]

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)

local SignalPlus = require(ReplicatedStorage.Packages.SignalPlus)
local UpdateState = require(ReplicatedStorage.Functions.UpdateState)
local PlayerData = require(ReplicatedStorage.PlayerData)
local Packets = require(ReplicatedStorage.Remotes.Packets)

export type StateAction = UpdateState.StateAction
export type PlayerData = UpdateState.PlayerData

local Shared = {}
local Profiles = {} :: { [Player]: any }

Shared.ProfileLoaded = SignalPlus()
Shared.NoSave = true

local function deepCopy(T)
	if typeof(T) ~= `table` then return T end
	local C = {}
	for K, V in T do C[K] = deepCopy(V) end
	return C
end

function Shared.SlotKey(UserId: number, Slot: number): string return `MapPreview_{UserId}_{Slot}` end
function Shared.ViewSlot(_UserId: number, _Slot: number) return nil end
function Shared.GetSlot(Player: Player): number? return if Profiles[Player] then 1 else nil end

function Shared.LoadSlot(Player: Player, _Slot: number?): boolean
	if Profiles[Player] then return true end
	if not Player.Parent then return false end
	local Data = deepCopy(PlayerData.DEFAULT_PLAYER_DATA)
	-- (Map preview, owner: unlock everything) every school top, cape and accessory is owned, and the student is
	-- enrolled, so the whole wardrobe can be tried on the map. Nothing is saved.
	pcall(function()
		local Appearance = require(ReplicatedStorage.UI.Appearance)
		local Gear = require(ReplicatedStorage.Config.Gear)
		local I = if typeof(Data.Identity) == `table` then Data.Identity else {}
		I.Uniforms, I.Capes, I.Gear = {}, {}, {}
		for _, U in Appearance.Uniforms or {} do if U.Id then table.insert(I.Uniforms, U.Id) end end
		for _, C in Appearance.Capes or {} do if C.Id then table.insert(I.Capes, C.Id) end end
		for K, It in Gear.Items or {} do
			local Id = if typeof(It) == `table` and It.Id then It.Id elseif typeof(K) == `string` then K else nil
			if Id then table.insert(I.Gear, Id) end
		end
		-- (1.86 port) every 3D accessory except the staff regalia (Admin pieces stay staff only)
		I.Accessories = {}
		pcall(function()
			for _, It in require(ReplicatedStorage.Config.Accessories).Items or {} do
				if It.Id and not It.Admin then table.insert(I.Accessories, It.Id) end
			end
		end)
		I.Enrolled = true
		Data.Identity = I
	end)
	Profiles[Player] = Data
	Player:SetAttribute(`Slot`, 1)
	Shared.ProfileLoaded:Fire(Player, Data)
	Packets.SetState:FireClient(Player, Data)
	return true
end

function Shared.GetProfile(Player: Player): PlayerData
	return Profiles[Player]
end

function Shared.UpdateState(Player: Player, Action: StateAction)
	local Data = Profiles[Player]
	if not Data then return end
	UpdateState(Data, Action)
	Packets.UpdateState:FireClient(Player, Action)
end

function Shared.OnStart()
	Packets.Start.OnServerEvent:Connect(function(Player: Player)
		local Data = Profiles[Player]
		if Data then Packets.SetState:FireClient(Player, Data) end
	end)
	if RunService:IsStudio() then
		Packets.Replicate.OnServerEvent:Connect(function(_Player: Player, Category: string, Effect: string, Parameters: any)
			Packets.Replicate:Fire(Category, Effect, Parameters)
		end)
	end
	for _, Player in Players:GetPlayers() do task.spawn(Shared.LoadSlot, Player) end
	Players.PlayerAdded:Connect(function(Player) Shared.LoadSlot(Player) end)
	Players.PlayerRemoving:Connect(function(Player) Profiles[Player] = nil end)
end

return Shared
