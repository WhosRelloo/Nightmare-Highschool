--[[
	Reputation (server). Owns PlayerData.Social: reputation categories, relationships with
	important NPCs, and earned titles. Factions keep their own block inside Social.Factions but
	save through Reputation.Sync so there is one writer for the Social data.

	API:
		Reputation.Get(Player) -> Social table (live)
		Reputation.Add(Player, Category, Amount, Reason?)
		Reputation.Value(Player, Category)
		Reputation.Relationship(Player, NpcId) -> Value, State, Met
		Reputation.ChangeRelationship(Player, NpcId, Amount, Reason?, Flag?)  -- (2.27) Flag: Fought | Helped | Pranked | Lied
		Reputation.Meet(Player, NpcId)          -- (2.27) a rostered student's introduction
		Reputation.Learn(Player, NpcId)         -- (2.29) met by hearing their name; the value doesn't move
		Reputation.Entry(Player, NpcId) -> { Value, Met, Last, Flags }  (2.27, a copy)
		Reputation.StateOf(Value) -> state name, ignoring Met (2.27)
	(2.27) Saved entries: the important NPCs, the named cast (Config.Npcs) and the roster (Config.Students), up to
	Config.SavedCap (64). Each is { Value, Met, Last = os.time(), Flags = { [flag] = count } }.
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
local Roster = require(ServerScriptService.Services.Social.Roster) -- (2.27)
local Cast = require(ReplicatedStorage.Config.Npcs) -- (2.27) the named cast keeps a saved relationship too

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

-- (2.27) who keeps a saved relationship: the important NPCs (Config.Reputation.Npcs), the named cast (Config.Npcs)
-- and the roster (Config.Students). Config.Reputation.Npcs alone still means "attacking them costs standing".
function Local.Saved(Id: string): boolean
	return Config.Npcs[Id] ~= nil or (typeof(Cast[Id]) == `table`) or Roster.IsRostered(Id)
end
function Local.NameOf(Id: string): string
	local E = Config.Npcs[Id] or (if typeof(Cast[Id]) == `table` then Cast[Id] else nil) or Roster.Get(Id)
	return E and E.Name or Id
end
function Shared.StateOf(Value: number): string return Local.StateFor(Value, true) end

-- (2.27) the cap (docs/expansion/13-Living-School.md §2.3): drop the oldest Acquaintance first, then the oldest of any
-- state but Trusted and Hostile. Important NPCs (Config.Reputation.Npcs) are never dropped.
function Local.Trim(Rels, Cap: number): { string }
	local Dropped = {}
	local Count = 0
	for _ in Rels do Count += 1 end
	while Count > Cap do
		local Pick, PickLast, PickPass = nil, math.huge, 3
		for Id, R in Rels do
			if not Config.Npcs[Id] and typeof(R) == `table` then
				local State = Local.StateFor(R.Value or 0, true)
				local Pass = if State == `Acquaintance` then 1 elseif State ~= `Trusted` and State ~= `Hostile` then 2 else 3
				local Last = R.Last or 0
				if Pass < PickPass or (Pass == PickPass and Last < PickLast) then Pick, PickLast, PickPass = Id, Last, Pass end
			end
		end
		if not Pick or PickPass == 3 then break end -- only Trusted, Hostile and important entries are left
		Rels[Pick] = nil
		Count -= 1
		table.insert(Dropped, Pick)
	end
	return Dropped
end
function Shared.TrimForTests(Rels, Cap: number, _Now: number?) return Local.Trim(Rels, Cap) end

function Local.Record(Player: Player, NpcId: string)
	local Social = Shared.Get(Player)
	if not Social or not Local.Saved(NpcId) then return nil end
	local Record = Social.Relationships[NpcId]
	if typeof(Record) ~= `table` then
		Record = { Value = 0; Met = false; Last = os.time(); Flags = {} }
		Social.Relationships[NpcId] = Record
		Local.Trim(Social.Relationships, Config.SavedCap or 64)
	end
	-- (2.27) older entries (Ezra, Vesper) gain the new fields
	Record.Last = Record.Last or os.time()
	if typeof(Record.Flags) ~= `table` then Record.Flags = {} end
	return Record
end

-- (2.27) a copy of the saved entry (an empty one if there's none yet); reading never creates an entry
function Shared.Entry(Player: Player, NpcId: string)
	local Social = Shared.Get(Player)
	local R = Social and Social.Relationships[NpcId]
	if typeof(R) ~= `table` then return { Value = 0; Met = false; Last = 0; Flags = {} } end
	return { Value = R.Value or 0; Met = R.Met == true; Last = R.Last or 0; Flags = if typeof(R.Flags) == `table` then table.clone(R.Flags) else {} }
end

function Shared.Relationship(Player: Player, NpcId: string): (number, string, boolean)
	if not Local.Saved(NpcId) then return 0, `Unknown`, false end
	local E = Shared.Entry(Player, NpcId)
	return E.Value, Local.StateFor(E.Value, E.Met), E.Met
end

-- for a rostered student this is their introduction (2.27)
function Shared.Meet(Player: Player, NpcId: string)
	local Record = Local.Record(Player, NpcId)
	if not Record or Record.Met then return end
	Record.Met = true
	Record.Value = math.max(Record.Value, 5)
	Record.Last = os.time()
	Shared.Sync(Player)
	Shared.RelationshipChanged:Fire(Player, NpcId, Local.StateFor(Record.Value, true), `Unknown`)
end

-- (2.29) a name heard in a rumour: you now know who they are, and how they feel about you doesn't change
function Shared.Learn(Player: Player, NpcId: string)
	local Record = Local.Record(Player, NpcId)
	if not Record or Record.Met then return end
	Record.Met = true
	Record.Last = os.time()
	Shared.Sync(Player)
	Shared.RelationshipChanged:Fire(Player, NpcId, Local.StateFor(Record.Value, true), `Unknown`)
end

local FLAGS = { Fought = true; Helped = true; Pranked = true; Lied = true } -- (2.27) counted per entry
function Shared.ChangeRelationship(Player: Player, NpcId: string, Amount: number, Reason: string?, Flag: string?)
	local Record = Local.Record(Player, NpcId)
	if not Record or (Amount == 0 and not Flag) then return end

	local OldState = Local.StateFor(Record.Value, Record.Met)
	if not Roster.IsRostered(NpcId) then Record.Met = true end -- (2.27) a rostered student is Met only by their introduction
	Record.Value = math.clamp(Record.Value + Amount, -100, 100)
	Record.Last = os.time()
	if Flag and FLAGS[Flag] then Record.Flags[Flag] = (Record.Flags[Flag] or 0) + 1 end
	local NewState = Local.StateFor(Record.Value, Record.Met)
	Shared.Sync(Player)

	if NewState ~= OldState then
		if Record.Met then -- (2.27) no name in a notification before you've learned it
			Notifications.Notify(Player, {
				Title = `{Local.NameOf(NpcId)}: {NewState}`;
				Text = Reason;
				Kind = if Amount > 0 then `Good` else `Bad`;
				Duration = 4;
			})
		end
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
