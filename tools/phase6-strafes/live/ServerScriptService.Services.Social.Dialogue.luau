--[[
	Dialogue (server authoritative, reusable)

	Trees live in ServerStorage.Dialogue.<NpcId> and are plain data:
		{
			Start = function(ctx) -> node id,
			Nodes = {
				[Id] = {
					Text = "..." or function(ctx) -> string,
					Choices = { { Text = "..." or fn, If = fn(ctx)?, Do = fn(ctx) -> next id?, Next = id? } },
					-- or Choices = function(ctx) -> list (for shared menus)
				},
			},
		}
	The client only ever receives the current line and the choices that passed their If check.
	Every choice is re-validated here (session, index, distance to the NPC) before its Do runs,
	so outcomes (joining, relationship, reputation) can't be forged.

	ctx helpers: Player, NpcId, Npc, FactionId, Met(), Meet(), Value(), State(), Rel(n, reason),
	Rep(category), AddRep(category, n), Standing(), Rank(), Member(), RivalMember(), CanJoin(),
	Join(), Leave(), Once(key) (true once per in-game day), Mission(), MissionDef, Faction.
	Quests: Offers(), QuestDef(id), StartQuest(id), QuestStatus(id), JustCompleted (quests this
	conversation finished, e.g. a delivery), Has(item), StartChampion(), Decide(id, choice) / Decided(id) (2.24.0).
]]

---| Services |---

local Players = game:GetService(`Players`)
local HttpService = game:GetService(`HttpService`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerStorage = game:GetService(`ServerStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local Packets = require(ReplicatedStorage.Remotes.Packets)
local RepConfig = require(ReplicatedStorage.Config.Reputation)
local FactionConfig = require(ReplicatedStorage.Config.Factions)
local Cast = require(ReplicatedStorage.Config.Npcs)
local QuestConfig = require(ReplicatedStorage.Config.Quests)

local Reputation = require(ServerScriptService.Services.Social.Reputation)
local Factions = require(ServerScriptService.Services.Social.Factions)
local SchoolClock = require(ServerScriptService.Services.School.SchoolClock)
local Quests = require(ServerScriptService.Services.Quests.Quests)
local Duels = require(ServerScriptService.Services.Quests.Duels)

local MAX_DISTANCE = 16
local Sessions = {} :: { [Player]: any }

local Local = {}
local Shared = {}

function Local.Tree(NpcId: string)
	local Name = Cast[NpcId] and Cast[NpcId].Dialogue or NpcId
	local Module = ServerStorage:FindFirstChild(`Dialogue`) and ServerStorage.Dialogue:FindFirstChild(Name)
	return Module and require(Module)
end

function Local.Context(Player: Player, NpcId: string, JustCompleted: { string }?)
	local Npc = Cast[NpcId] or RepConfig.Npcs[NpcId]
	local FactionId = Npc and Npc.Faction
	local Faction = FactionId and FactionConfig.Factions[FactionId]
	local ctx = { Player = Player; NpcId = NpcId; Npc = Npc; FactionId = FactionId; Faction = Faction; MissionDef = Faction and Faction.Mission }

	function ctx.Met() local _, _, Met = Reputation.Relationship(Player, NpcId) return Met end
	function ctx.Meet() Reputation.Meet(Player, NpcId) end
	function ctx.Value() return (Reputation.Relationship(Player, NpcId)) end
	function ctx.State() local _, State = Reputation.Relationship(Player, NpcId) return State end
	function ctx.Rel(Amount: number, Reason: string?) Reputation.ChangeRelationship(Player, NpcId, Amount, Reason) end
	function ctx.Rep(Category: string) return Reputation.Value(Player, Category) end
	function ctx.PathTier(Path: string) -- (2.31) Standing Paths (Services.Player.Paths)
		local Ok, T = pcall(function() return require(ServerScriptService.Services.Player.Paths).Tier(Player, Path) end)
		return if Ok and typeof(T) == `number` then T else 1
	end
	function ctx.AddRep(Category: string, Amount: number) Reputation.Add(Player, Category, Amount) end
	function ctx.Standing() local F = Factions.Get(Player, FactionId) return F and F.Standing or 0 end
	function ctx.Rank() local F = Factions.Get(Player, FactionId) return F and F.Rank or `Outsider` end
	function ctx.Member() local F = Factions.Get(Player, FactionId) return F ~= nil and F.Member end
	function ctx.RivalMember()
		for _, RivalId in Faction and Faction.Rivals or {} do
			local R = Factions.Get(Player, RivalId)
			if R and R.Member then return true end
		end
		return false
	end
	function ctx.CanJoin() return Factions.CanJoin(Player, FactionId) end
	function ctx.Join() return Factions.Join(Player, FactionId) end
	function ctx.Leave() return Factions.Leave(Player, FactionId) end
	function ctx.Mission() return Factions.GetMissionProgress(Player, FactionId) end
	function ctx.MissionStatus() return Factions.MissionStatus(Player, FactionId) end
	function ctx.Once(Key: string): boolean
		local Social = Reputation.Get(Player)
		if not Social then return false end
		Social.DialogueDaily = if typeof(Social.DialogueDaily) == `table` then Social.DialogueDaily else {}
		local Day = SchoolClock.GetState().Day
		local Id = `{NpcId}:{Key}`
		return Social.DialogueDaily[Id] ~= Day
	end
	ctx.JustCompleted = JustCompleted or (Sessions[Player] and Sessions[Player].JustCompleted) or {}
	function ctx.Offers() return Quests.Offers(Player, NpcId, true) end
	function ctx.DressLine(Clique: string): string? -- (line matrix) a clique giver turns you away for your clothes
		local Ok, Line = pcall(function()
			return require(game:GetService(`ServerScriptService`).Services.AI.StudentBrain.Talk).Line(Clique, `DressCode`, Player)
		end)
		return if Ok then Line else nil
	end
	function ctx.QuestDef(Id: string) return QuestConfig.Quests[Id] end
	function ctx.StartQuest(Id: string) return Quests.Start(Player, Id) end
	function ctx.QuestStatus(Id: string) return Quests.Status(Player, Id) end
	function ctx.QuestActive(Id: string) return Quests.IsActive(Player, Id) end
	function ctx.Objective(Id: string) return Quests.CurrentObjective(Player, Id) end
	function ctx.Has(Item: string) return Quests.HasItem(Player, Item) end
	-- (2.24.0) Decision objectives: an answer chosen here is saved (Quests.Decisions[Id]) and completes the stage
	function ctx.Decide(Id: string, Choice: string) return Quests.Decide(Player, Id, Choice) end
	function ctx.Decided(Id: string) return Quests.Decided(Player, Id) end
	function ctx.StartChampion() return Duels.StartChampion(Player) end
	-- (1.35) clique membership (Social.CliqueMembership): this NPC's clique, if they lead one of the joinable six
	ctx.CliqueId = (Npc and Npc.Clique) or (function() for _, D in QuestConfig.Quests do if D.Dare and D.Giver == NpcId then return D.Clique end end return nil end)()
	local function Membership() local Ok, M = pcall(require, game:GetService(`ServerScriptService`).Services.Social.CliqueMembership) return Ok and M or nil end
	function ctx.CliqueMember() local M = Membership() return M ~= nil and ctx.CliqueId ~= nil and M.IsMember(Player, ctx.CliqueId) end
	function ctx.CliqueCanJoin() local M = Membership() if not (M and ctx.CliqueId) then return false, `NotJoinable` end return M.CanJoin(Player, ctx.CliqueId) end
	function ctx.CliqueJoin() local M = Membership() return M ~= nil and ctx.CliqueId ~= nil and (M.Join(Player, ctx.CliqueId)) == true end
	function ctx.CliqueLeave() local M = Membership() return M ~= nil and (M.Leave(Player)) == true end
	function ctx.CliqueLine(Key: string) local C = require(ReplicatedStorage.Config.Cliques).Defs[ctx.CliqueId or ``] return C and C[Key] end
	function ctx.Joinable() local C = require(ReplicatedStorage.Config.Cliques) return ctx.CliqueId ~= nil and table.find(C.Membership.Joinable, ctx.CliqueId) ~= nil end
	function ctx.QuestData(Id: string) return Quests.DataFor(Player, Id) end
	ctx.Vars = Sessions[Player] and Sessions[Player].Vars or {} -- per-conversation scratch (e.g. which quest)
	function ctx.UseOnce(Key: string)
		local Social = Reputation.Get(Player)
		if not Social then return end
		Social.DialogueDaily = if typeof(Social.DialogueDaily) == `table` then Social.DialogueDaily else {}
		Social.DialogueDaily[`{NpcId}:{Key}`] = SchoolClock.GetState().Day
	end
	return ctx
end

function Local.Resolve(Value: any, ctx): any
	if typeof(Value) == `function` then return Value(ctx) end
	return Value
end

function Local.Close(Player: Player, Silent: boolean?)
	local S = Sessions[Player]
	if not S then return end
	Sessions[Player] = nil
	if not Silent and Player.Parent then
		Packets.DialogueEvent:FireClient(Player, { Type = `Close`; Id = S.Id })
	end
end

function Local.Show(Player: Player, S, NodeId: string?)
	local Node = NodeId and S.Tree.Nodes[NodeId]
	if not Node then
		Local.Close(Player)
		return
	end

	local ctx = Local.Context(Player, S.NpcId)
	-- (audit) a node whose Text / Choices / If errored left the client stuck on Waiting: close the talk instead
	local Ok, Text, Offered, Labels = pcall(function()
		local T = Local.Resolve(Node.Text, ctx)
		local AllChoices = Local.Resolve(Node.Choices, ctx) or {}
		local O, L = {}, {}
		for _, Choice in AllChoices do
			if not Choice.If or Choice.If(ctx) then
				table.insert(O, Choice)
				table.insert(L, Local.Resolve(Choice.Text, ctx))
			end
		end
		return T, O, L
	end)
	if not Ok then
		warn(`[Dialogue] {S.NpcId}.{NodeId}: {Text}`)
		Local.Close(Player)
		return
	end
	if #Offered == 0 then
		table.insert(Offered, { Text = `Goodbye.` })
		table.insert(Labels, `Goodbye.`)
	end

	S.NodeId = NodeId
	S.Offered = Offered

	local Npc = S.Npc
	local Faction = Npc.Faction and FactionConfig.Factions[Npc.Faction]
	local State = nil
	if RepConfig.Npcs[S.NpcId] then
		State = select(2, Reputation.Relationship(Player, S.NpcId))
	end
	Packets.DialogueEvent:FireClient(Player, {
		Type = `Node`;
		Id = S.Id;
		Speaker = Npc.Name;
		Role = Npc.Role;
		Relationship = State;
		Color = Faction and Faction.Color or Npc.Color or Color3.fromRGB(240, 240, 240);
		Text = Text;
		Choices = Labels;
		Model = S.Model; -- (1.35.1) who's talking: the client frames them (Gui.Dialogue talk cinematic)
	})
end

function Local.InRange(Player: Player, S): boolean
	local Character = Player.Character
	local Root = Character and Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	local NpcRoot = S.Model and S.Model.Parent and S.Model:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	if not Root or not NpcRoot then return false end
	local NpcHumanoid = S.Model:FindFirstChildWhichIsA(`Humanoid`)
	if not NpcHumanoid or NpcHumanoid.Health <= 0 or NpcHumanoid:GetAttribute(`Downed`) then return false end
	return (Root.Position - NpcRoot.Position).Magnitude <= MAX_DISTANCE
end

---| API |---

function Shared.Start(Player: Player, NpcId: string, Model: Model): boolean
	local Tree = Local.Tree(NpcId)
	local Npc = Cast[NpcId] or RepConfig.Npcs[NpcId]
	if not Tree or not Npc then return false end

	Local.Close(Player)
	local S = { Id = HttpService:GenerateGUID(false); NpcId = NpcId; Npc = Npc; Tree = Tree; Model = Model; Vars = {} }
	if not Local.InRange(Player, S) then return false end
	Sessions[Player] = S

	-- Quests first: talking can finish objectives (meet someone, deliver something).
	local Ok, Completed = pcall(Quests.OnTalk, Player, NpcId)
	if not Ok then
		warn(`[Dialogue] quests: {Completed}`)
		Completed = {}
	end
	S.JustCompleted = Completed

	local ctx = Local.Context(Player, NpcId, Completed)
	Local.Show(Player, S, Tree.Start(ctx))
	return true
end

function Shared.IsTalking(Player: Player): boolean
	return Sessions[Player] ~= nil
end

function Shared.Close(Player: Player)
	Local.Close(Player)
end

-- Testing (TestBridge): current node + offered choice labels, and choosing by index.
function Shared.PeekForTests(Player: Player)
	local S = Sessions[Player]
	if not S then return nil end
	local Labels = {}
	local ctx = Local.Context(Player, S.NpcId)
	for _, Choice in S.Offered do table.insert(Labels, Local.Resolve(Choice.Text, ctx)) end
	return { Node = S.NodeId; Choices = Labels; Id = S.Id }
end

function Local.OnAction(Player: Player, Message)
	local S = Sessions[Player]
	if not S or typeof(Message) ~= `table` or Message.Id ~= S.Id then return end

	if Message.Close then
		Local.Close(Player, true)
		return
	end

	local Index = Message.Choice
	local Choice = typeof(Index) == `number` and S.Offered and S.Offered[Index]
	if not Choice then return end
	if not Local.InRange(Player, S) then
		Local.Close(Player)
		return
	end

	local ctx = Local.Context(Player, S.NpcId)
	-- Re-check the condition: state may have changed since the menu was shown.
	if Choice.If and not Choice.If(ctx) then
		Local.Show(Player, S, S.NodeId)
		return
	end

	local NextId = Choice.Next
	if Choice.Do then
		local Ok, Result = pcall(Choice.Do, ctx)
		if not Ok then
			warn(`[Dialogue] {S.NpcId}.{S.NodeId}: {Result}`)
		elseif typeof(Result) == `string` then
			NextId = Result
		end
	end

	if Sessions[Player] ~= S then return end -- closed meanwhile
	if NextId then
		Local.Show(Player, S, NextId)
	else
		Local.Close(Player)
	end
end

function Shared.ChooseForTests(Player: Player, Index: number)
	local S = Sessions[Player]
	if not S then return false end
	Local.OnAction(Player, { Id = S.Id; Choice = Index })
	return true
end

function Shared.OnStart()
	Packets.DialogueAction.OnServerEvent:Connect(function(Player, Message)
		local Ok, Err = pcall(Local.OnAction, Player, Message)
		if not Ok then warn(`[Dialogue] {Err}`) end
	end)
	Players.PlayerRemoving:Connect(function(Player) Sessions[Player] = nil end)

	task.spawn(function()
		while true do
			task.wait(1)
			for Player, S in Sessions do
				if not Player.Parent or not Local.InRange(Player, S) then
					Local.Close(Player)
				end
			end
		end
	end)
end

return Shared
