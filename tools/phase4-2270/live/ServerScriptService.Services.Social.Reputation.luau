--[[
	Reputation (server). Owns PlayerData.Social: reputation categories, relationships with
	important NPCs, and earned titles. Factions keep their own block inside Social.Factions but
	save through Reputation.Sync so there is one writer for the Social data.

	API:
		Reputation.Get(Player) -> Social table (live)
		Reputation.Add(Player, Category, Amount, Reason?)
		Reputation.Value(Player, Category)
		Reputation.Relationship(Player, NpcId) -> Value, State, Met
		Reputation.ChangeRelationship(Player, NpcId, Amount, Reason?)
		Reputation.Meet(Player, NpcId)
		Reputation.AwardTitle(Player, Title)
		Reputation.Sync(Player)  -- push the Social block to the client (batched)
		Signals: Changed(Player, Category, New, Old), RelationshipChanged(Player, NpcId, State, OldState)
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local SignalPlus = require(ReplicatedStorage.Packages.SignalPlus)
local Config = require(ReplicatedStorage.Config.Reputation)

local Packets = require(ReplicatedStorage.Remotes.Packets)
local Data = require(ServerScriptService.Services.Player.Data)
local Notifications = require(ServerScriptService.Services.Features.Notifications)

local Local = {}
local Shared = {}

Shared.Changed = SignalPlus()
Shared.RelationshipChanged = SignalPlus()

local PendingSync = {} :: { [Player]: boolean }

function Shared.Get(Player: Player): any?
	local Profile = Data.GetProfile(Player)
	if not Profile then return nil end

	local Social = Profile.Social
	if typeof(Social) ~= `table` then
		Social = {}
		Profile.Social = Social
	end
	Social.Factions = if typeof(Social.Factions) == `table` then Social.Factions else {}
	Social.Reputation = if typeof(Social.Reputation) == `table` then Social.Reputation else {}
	Social.Relationships = if typeof(Social.Relationships) == `table` then Social.Relationships else {}
	Social.Titles = if typeof(Social.Titles) == `table` then Social.Titles else {}
	Social.Title = if typeof(Social.Title) == `string` then Social.Title else ``
	for Category in Config.Categories do
		Social.Reputation[Category] = Social.Reputation[Category] or 0
	end
	return Social
end

-- Batched: many changes in one frame send one update.
function Shared.Sync(Player: Player)
	if PendingSync[Player] then return end
	PendingSync[Player] = true
	task.defer(function()
		PendingSync[Player] = nil
		local Social = Player.Parent and Shared.Get(Player)
		if Social then
			Data.UpdateState(Player, { type = `SetSocial`; social = Social })
			Player:SetAttribute(`Title`, if Social.Title ~= `` then Social.Title else nil)
		end
	end)
end

---| Reputation |---

function Shared.Value(Player: Player, Category: string): number
	local Social = Shared.Get(Player)
	return Social and Social.Reputation[Category] or 0
end

function Shared.Add(Player: Player, Category: string, Amount: number, Reason: string?)
	local Rule = Config.Categories[Category]
	local Social = Shared.Get(Player)
	if not Rule or not Social or Amount == 0 then return end

	local Old = Social.Reputation[Category] or 0
	local New = math.clamp(Old + Amount, Rule.Min, Rule.Max)
	if New == Old then return end

	Social.Reputation[Category] = New
	Shared.Sync(Player)
	Shared.Changed:Fire(Player, Category, New, Old)
end

---| Relationships |---

function Local.StateFor(Value: number, Met: boolean): string
	if not Met then return `Unknown` end
	for _, State in Config.RelationshipStates do
		if Value <= State.Max then return State.Name end
	end
	return `Trusted`
end

function Local.Record(Player: Player, NpcId: string)
	local Social = Shared.Get(Player)
	if not Social or not Config.Npcs[NpcId] then return nil end
	local Record = Social.Relationships[NpcId]
	if typeof(Record) ~= `table` then
		Record = { Value = 0; Met = false }
		Social.Relationships[NpcId] = Record
	end
	return Record
end

function Shared.Relationship(Player: Player, NpcId: string): (number, string, boolean)
	local Record = Local.Record(Player, NpcId)
	if not Record then return 0, `Unknown`, false end
	return Record.Value, Local.StateFor(Record.Value, Record.Met), Record.Met
end

function Shared.Meet(Player: Player, NpcId: string)
	local Record = Local.Record(Player, NpcId)
	if not Record or Record.Met then return end
	Record.Met = true
	Record.Value = math.max(Record.Value, 5)
	Shared.Sync(Player)
	Shared.RelationshipChanged:Fire(Player, NpcId, Local.StateFor(Record.Value, true), `Unknown`)
end

function Shared.ChangeRelationship(Player: Player, NpcId: string, Amount: number, Reason: string?)
	local Record = Local.Record(Player, NpcId)
	if not Record or Amount == 0 then return end

	local OldState = Local.StateFor(Record.Value, Record.Met)
	Record.Met = true
	Record.Value = math.clamp(Record.Value + Amount, -100, 100)
	local NewState = Local.StateFor(Record.Value, true)
	Shared.Sync(Player)

	if NewState ~= OldState then
		local Npc = Config.Npcs[NpcId]
		Notifications.Notify(Player, {
			Title = `{Npc.Name}: {NewState}`;
			Text = Reason;
			Kind = if Amount > 0 then `Good` else `Bad`;
			Duration = 4;
		})
		Shared.RelationshipChanged:Fire(Player, NpcId, NewState, OldState)
	end
end

---| Titles |---

function Shared.AwardTitle(Player: Player, Title: string): boolean
	local Social = Shared.Get(Player)
	if not Social or table.find(Social.Titles, Title) then return false end

	table.insert(Social.Titles, Title)
	if Social.Title == `` then Social.Title = Title end
	Shared.Add(Player, `Popularity`, 5, `Earned a title`)
	Shared.Sync(Player)
	Notifications.Notify(Player, { Title = `Title earned: {Title}`; Kind = `Good`; Duration = 6 })
	return true
end

function Shared.EquipTitle(Player: Player, Title: string): boolean
	local Social = Shared.Get(Player)
	if not Social then return false end
	if Title ~= `` and not table.find(Social.Titles, Title) then return false end
	Social.Title = Title
	Shared.Sync(Player)
	return true
end

function Shared.OnStart()
	Data.ProfileLoaded:Connect(function(Player)
		if Shared.Get(Player) then Shared.Sync(Player) end
	end)
	for _, Player in Players:GetPlayers() do
		if Shared.Get(Player) then Shared.Sync(Player) end
	end
	Players.PlayerRemoving:Connect(function(Player) PendingSync[Player] = nil end)

	-- Client requests (only equipping an owned title for now; everything else is server-driven).
	local LastAction = {} :: { [Player]: number }
	Packets.SocialAction.OnServerEvent:Connect(function(Player, Message)
		if typeof(Message) ~= `table` then return end
		local Now = os.clock()
		if LastAction[Player] and Now - LastAction[Player] < 0.5 then return end
		LastAction[Player] = Now
		if Message.Action == `EquipTitle` and typeof(Message.Title) == `string` and #Message.Title <= 40 then
			Shared.EquipTitle(Player, Message.Title)
		end
	end)
	Players.PlayerRemoving:Connect(function(Player) LastAction[Player] = nil end)
end

return Shared
