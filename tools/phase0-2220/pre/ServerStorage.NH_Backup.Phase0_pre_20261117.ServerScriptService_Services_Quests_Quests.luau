--[[
	Quests (server authoritative). Definitions: ReplicatedStorage.Config.Quests (data only).

	Saved in PlayerData.Quests:
		Active[Id] = { Stage, Counts = {ObjectiveId = n}, Items = {Item = "Held" | "Dropped"}, Data, Deadline? }
		Done[Id] = in-game day, Failed[Id] = reason, Cases (see Investigation), Tracked

	Progress comes only from server events: Attendance.Recorded, Activities.Finished, dialogue
	(OnTalk), quest-object prompts, quest areas (checked every 0.5 s), Investigation, Stealth.Caught,
	Duels. Nothing the client sends can complete an objective except Link / Deduce, which the
	Investigation module checks against server-only answers.

	Failure is recoverable by design:
		- timed quests fail on timeout and can be restarted from the giver
		- getting caught in a stealth zone rewinds to the quest's checkpoint (items taken back)
		- getting downed drops droppable quest items on the floor; only you can pick them up
		- disconnecting keeps everything; dropped items come back to you on rejoin

	Dares (1.33, Dare = true): each clique leader has three; DareFor(Leader) is today's (by the event day, which runs
	6 AM to 6 AM). Only that one can start, Done holds its event day, and an unfinished dare goes away at 6 AM.

	API: CanStart, Start, Abandon, Progress, OnTalk, OnInteract, HasItem, Offers, Status,
	     IsActive, IsDone, CurrentObjective, DareFor, DareDay. Signals: Started, Completed, Failed.
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local SignalPlus = require(ReplicatedStorage.Packages.SignalPlus)
local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local Packets = require(ReplicatedStorage.Remotes.Packets)
local Config = require(ReplicatedStorage.Config.Quests)
local Cases = require(ReplicatedStorage.Config.Cases)
local Interaction = require(ReplicatedStorage.Config.Interaction)
local SchoolTime = require(ReplicatedStorage.Functions.SchoolTime)

local Places = require(script.Parent.Places)
local Investigation = require(script.Parent.Investigation)
local Stealth = require(script.Parent.Stealth)
local Duels = require(script.Parent.Duels)

local Data = require(ServerScriptService.Services.Player.Data)
local Notifications = require(ServerScriptService.Services.Features.Notifications)
local Fx = require(ServerScriptService.Services.Features.Fx) -- quest beats are drawn by the client (Controllers.Gui.Moments)
local Downed = require(ServerScriptService.Services.Features.Downed)
local SchoolClock = require(ServerScriptService.Services.School.SchoolClock)
local Attendance = require(ServerScriptService.Services.School.Attendance)
local Activities = require(ServerScriptService.Services.School.Activities)
local Reputation = require(ServerScriptService.Services.Social.Reputation)
local Factions = require(ServerScriptService.Services.Social.Factions)
local Lineage = require(ReplicatedStorage.Lineage)
-- (1.28) clique standing: requirements, rewards and the Scuffle objective (lazy: Social.Cliques loads after us)
local function Cliques() return require(ServerScriptService.Services.Social.Cliques) end

local BUSY = { `Downed`, `Carried`, `Gripped`, `Gripping`, `InActivity`, `Stun`, `ParryStun`, `Paralyzed` }
local INTERACT_RANGE = 12
local GRADE_ORDER = { F = 0; D = 1; C = 2; B = 3; A = 4; [`A+`] = 5 }
local TIME_TEXT = `That has to wait until after hours (from 5 PM).`

local PendingSync = {} :: { [Player]: boolean }
local Drops = {} :: { [Player]: { [string]: BasePart } }
local LastInteract = {} :: { [Player]: number }
local Collecting = {} :: { [Player]: { string } } -- quests completed during OnTalk (signals fire late)

local Local = {}
local Shared = {}

Shared.Started = SignalPlus()   -- (Player, QuestId)
Shared.Completed = SignalPlus() -- (Player, QuestId)
Shared.Failed = SignalPlus()    -- (Player, QuestId, Reason)

---| Data |---

function Local.Get(Player: Player): any?
	local Profile = Data.GetProfile(Player)
	if not Profile then return nil end
	local Q = Profile.Quests
	if typeof(Q) ~= `table` then
		Q = {}
		Profile.Quests = Q
	end
	Q.Active = if typeof(Q.Active) == `table` then Q.Active else {}
	Q.Done = if typeof(Q.Done) == `table` then Q.Done else {}
	Q.Failed = if typeof(Q.Failed) == `table` then Q.Failed else {}
	Q.Cases = if typeof(Q.Cases) == `table` then Q.Cases else {}
	Q.Tracked = if typeof(Q.Tracked) == `string` then Q.Tracked else ``
	return Q
end

function Local.Sync(Player: Player)
	if PendingSync[Player] then return end
	PendingSync[Player] = true
	task.defer(function()
		PendingSync[Player] = nil
		local Q = Player.Parent and Local.Get(Player)
		if not Q then return end
		-- The client copy leaves out each quest's Secret (e.g. where the lost item really is).
		local Copy = table.clone(Q)
		Copy.Active = {}
		for Id, State in Q.Active do
			local S = table.clone(State)
			S.Secret = nil
			Copy.Active[Id] = S
		end
		-- Straight to the client: Data.UpdateState would also write this trimmed copy back into
		-- the server's save and lose the secrets.
		Packets.UpdateState:FireClient(Player, { type = `SetQuests`; quests = Copy })
		Local.SendSeals(Player)
	end)
end

-- VFX P1-14: which NPCs have something for this player (client Controllers.World.QuestSeals draws the seals).
-- TurnIn > Offer > Retry > Active. Sent only when it changes.
local LastSeals = {} :: { [Player]: string }
local SEAL_RANK = { Active = 0; Retry = 1; Offer = 2; TurnIn = 3 }

function Local.Seals(Player: Player): { [string]: string }
	local Q = Local.Get(Player)
	local Map = {}
	if not Q then return Map end
	local function put(NpcId: string?, State: string)
		if typeof(NpcId) ~= `string` then return end
		if not Map[NpcId] or SEAL_RANK[State] > SEAL_RANK[Map[NpcId] ] then Map[NpcId] = State end
	end
	for Id, Def in Config.Quests do
		local State = Q.Active[Id]
		if State then
			if Def.Giver then put(Def.Giver, `Active`) end
			for _, Index in Local.Live(State, Def) do
				local Obj = Def.Objectives[Index]
				if Obj and Obj.Type == `Talk` and not Obj.Optional then
					put(Obj.Npc, `TurnIn`)
					for _, N in Obj.Npcs or {} do put(N, `TurnIn`) end
				end
			end
		elseif Def.Giver then
			local Can, Why = Shared.CanStart(Player, Id)
			if Can or Why == `DressCode` then -- (line matrix) the marker stays for the undressed: the giver turns them away with a line
				put(Def.Giver, if Q.Failed[Id] then `Retry` else `Offer`)
			end
		end
	end
	return Map
end

function Local.SendSeals(Player: Player)
	if not Player.Parent then return end
	local Ok, Map = pcall(Local.Seals, Player)
	if not Ok then return end
	local Keys = {}
	for K, V in Map do table.insert(Keys, `{K}={V}`) end
	table.sort(Keys)
	local Sig = table.concat(Keys, `,`)
	if LastSeals[Player] == Sig then return end
	LastSeals[Player] = Sig
	Fx.Fire(Player, `Seals`, Map)
end

function Local.Day(): number
	return SchoolClock.GetState().Day
end

function Local.Now(): number
	return workspace:GetServerTimeNow()
end

-- (1.33) dares: the event day (6 AM to 6 AM), and each leader's dare of the day
function Shared.DareDay(): number
	local State = SchoolClock.GetState()
	return require(ReplicatedStorage.Config.Cliques).EventDay(State) or State.Day
end

local Pools = {} :: { [string]: { [string]: { string } } } -- "Dare" | "Job" -> leader -> quest ids
local function DailyFor(Kind: string, Leader: string, Day: number?): string?
	if not Pools[Kind] then
		local P = {}
		for Id, Def in Config.Quests do
			if Def[Kind] and Def.Giver then
				P[Def.Giver] = P[Def.Giver] or {}
				table.insert(P[Def.Giver], Id)
			end
		end
		for _, L in P do table.sort(L) end
		Pools[Kind] = P
	end
	local List = Pools[Kind][Leader]
	if not List or #List == 0 then return nil end
	local D = Day or Shared.DareDay()
	return List[(D + #Leader + (if Kind == `Job` then 1 else 0)) % #List + 1]
end
function Shared.DareFor(Leader: string, Day: number?): string? return DailyFor(`Dare`, Leader, Day) end
-- (1.35) a member's job of the day from their leader
function Shared.JobFor(Leader: string, Day: number?): string? return DailyFor(`Job`, Leader, Day) end

function Local.Notify(Player: Player, Data)
	Notifications.Notify(Player, Data)
end

-- A quest beat (start / new objective / complete / fail): a Moment banner instead of a toast (VFX P1-4).
function Local.Beat(Player: Player, Data)
	Fx.Fire(Player, `QuestBeat`, Data)
end

function Local.FirstRequired(Def, From: number): number?
	for Index = From, #Def.Objectives do
		if not Def.Objectives[Index].Optional then return Index end
	end
	return nil
end

function Local.ObjectiveIndex(Def, Id: string): number?
	for Index, Obj in Def.Objectives do
		if Obj.Id == Id then return Index end
	end
	return nil
end

function Local.TimeOk(Obj): boolean
	local State = SchoolClock.GetState()
	if Obj.Time and Obj.Time[State.Segment.Kind] ~= true then return false end
	if Obj.FullMoon and not Lineage.IsFullMoon(State.Day, State.Hour) then return false end
	return true
end

-- what to say when an objective is waiting on the clock
function Local.TimeText(Obj): string
	if Obj.FullMoon then return `That has to wait for a full-moon night (every 4th night).` end
	if Obj.Time and Obj.Time.Morning and not Obj.Time.Night then return `That has to wait until dawn (6 to 7:30 AM).` end
	if Obj.Time and Obj.Time.Night and not Obj.Time.Evening then return `That has to wait until night (from 9 PM).` end
	return TIME_TEXT
end

function Local.Busy(Player: Player): boolean
	local Character = Player.Character
	local Humanoid = Character and Character:FindFirstChildWhichIsA(`Humanoid`)
	if not Humanoid or Humanoid.Health <= 0 or Humanoid:GetAttribute(`Downed`) then return true end
	return StateManager.HasState(Character, BUSY) == true
end

---| Queries |---

function Shared.IsActive(Player: Player, Id: string): boolean
	local Q = Local.Get(Player)
	return Q ~= nil and Q.Active[Id] ~= nil
end

function Shared.IsDone(Player: Player, Id: string): boolean
	local Q = Local.Get(Player)
	return Q ~= nil and Q.Done[Id] ~= nil
end

function Shared.CurrentObjective(Player: Player, Id: string): any?
	local Q = Local.Get(Player)
	local State = Q and Q.Active[Id]
	local Def = Config.Quests[Id]
	return State and Def and Def.Objectives[State.Stage]
end

-- Read-only view of a quest's private data (e.g. which spot hides the lost charm).
function Shared.DataFor(Player: Player, Id: string): any?
	local Q = Local.Get(Player)
	local State = Q and Q.Active[Id]
	if not State then return nil end
	local View = table.clone(State.Data or {})
	for K, V in State.Secret or {} do View[K] = V end
	return View
end

function Shared.HasItem(Player: Player, Item: string): boolean
	local Q = Local.Get(Player)
	if not Q then return false end
	for _, State in Q.Active do
		if State.Items and State.Items[Item] == `Held` then return true end
	end
	return false
end

function Shared.CanStart(Player: Player, Id: string): (boolean, string)
	local Def = Config.Quests[Id]
	local Q = Local.Get(Player)
	if not Def or not Q then return false, `Unknown` end
	if Q.Active[Id] then return false, `Active` end
	if Def.Showdown then -- (1.34) friend or foe: Social.CliqueShowdowns
		-- (audit) no Q.Done check here: CanChallenge refuses a showdown you've won, and leaving the clique wipes that
		-- win so the leader can challenge you again (the old Done check made rejoining impossible)
		local Ok, Sd = pcall(require, ServerScriptService.Services.Social.CliqueShowdowns)
		local Can, Why = false, `Locked`
		if Ok and Sd and Sd.CanChallenge then Can, Why = Sd.CanChallenge(Player, Def.Showdown) end
		if not Can then return false, Why or `Locked` end
		return true, `Ok`
	end
	if Def.Job then -- (1.35) members only
		local Ok, M = pcall(require, ServerScriptService.Services.Social.CliqueMembership)
		if not (Ok and M and M.IsMember and M.IsMember(Player, Def.Clique)) then return false, `NotMember` end
		if Shared.JobFor(Def.Giver) ~= Id then return false, `NotToday` end
		if Q.Done[Id] == Shared.DareDay() then return false, `DoneToday` end
	elseif Def.Dare then
		if Shared.DareFor(Def.Giver) ~= Id then return false, `NotToday` end
		if Q.Done[Id] == Shared.DareDay() then return false, `DoneToday` end
	elseif Q.Done[Id] ~= nil then
		if Def.Repeatable ~= `Daily` then return false, `Done` end
		if Q.Done[Id] == Local.Day() then return false, `DoneToday` end
	end
	local Req = Def.Requires
	if Req then
		for _, Need in Req.Quests or {} do
			if Q.Done[Need] == nil then return false, `Locked` end
		end
		if Req.Rite and not Lineage.RiteReady(Player, Req.Rite.Race, Req.Rite.Tier) then return false, `Locked` end
		if Req.NotMember then
			local F = Factions.Get(Player, Req.NotMember)
			if F and F.Member then return false, `Member` end
		end
		if Req.Suspended and Player:GetAttribute(`Suspended`) ~= true then return false, `Locked` end -- (2.8.1) Bruno's suspension jobs
		if Req.Clique then
			local Ok, C = pcall(function() return Cliques().Get(Player) end)
			if not (Ok and C) or (C[Req.Clique.Id] or 0) < (Req.Clique.Min or 0) then return false, `Locked` end
		end
	end
	-- (line matrix) a clique's in-person quests wait until you're dressed the part, liked, or a member
	local DressFor = Def.Clique or (Req and Req.Clique and Req.Clique.Id)
	if DressFor and not (Def.Dare or Def.Job or Def.Showdown or (Req and Req.Suspended)) then -- (2.8.1) Bruno takes any suspended kid
		local Ok, Dressed = pcall(function() return Cliques().Dressed(Player, DressFor) end)
		if Ok and Dressed == false then return false, `DressCode` end
	end
	return true, `Ok`
end

-- Quests a giver can talk about: offers (startable), active ones, failed ones (retry).
function Shared.Offers(Player: Player, NpcId: string, WithDressCode: boolean?): { { Id: string, Kind: string } }
	local Q = Local.Get(Player)
	local List = {}
	if not Q then return List end
	for Id, Def in Config.Quests do
		if Def.Giver ~= NpcId then continue end
		if Q.Active[Id] then
			table.insert(List, { Id = Id; Kind = `Active` })
		else
			local Ok, Why = Shared.CanStart(Player, Id)
			if Ok then
				table.insert(List, { Id = Id; Kind = if Q.Failed[Id] then `Retry` else `Offer` })
			elseif WithDressCode and Why == `DressCode` then -- (line matrix) the dialogue turns you away with a line
				table.insert(List, { Id = Id; Kind = `DressCode` })
			end
		end
	end
	table.sort(List, function(A, B) return A.Id < B.Id end)
	return List
end

-- Short status line for dialogue / tests.
function Shared.Status(Player: Player, Id: string): string
	local Obj = Shared.CurrentObjective(Player, Id)
	if not Obj then return `` end
	local Q = Local.Get(Player)
	local Count = Q.Active[Id].Counts[Obj.Id] or 0
	local Need = Obj.Count or 1
	return if Need > 1 then `{Obj.Text} ({Count}/{Need})` else Obj.Text
end

---| Lifecycle |---

function Local.RewardText(Rewards): string
	local Parts = {}
	if Rewards.Yen then table.insert(Parts, `+{Rewards.Yen} Yen`) end
	for Category, Amount in Rewards.Rep or {} do table.insert(Parts, `{if Amount > 0 then `+` else ``}{Amount} {Category}`) end
	for Faction, Amount in Rewards.Standing or {} do
		local Def = require(ReplicatedStorage.Config.Factions).Factions[Faction]
		table.insert(Parts, `{if Amount > 0 then `+` else ``}{Amount} {Def and Def.Name or Faction}`)
	end
	for Clique, Amount in Rewards.Cliques or {} do
		local Def = require(ReplicatedStorage.Config.Cliques).Defs[Clique]
		table.insert(Parts, `{if Amount > 0 then `+` else ``}{Amount} {Def and Def.Name or Clique}`)
	end
	if Rewards.Title then table.insert(Parts, `title "{Rewards.Title}"`) end
	return table.concat(Parts, `  ·  `)
end

function Local.GiveRewards(Player: Player, Def)
	local R = Def.Rewards
	if not R then return end
	if R.Yen and R.Yen ~= 0 then Data.UpdateState(Player, { type = `UpdateYen`; amount = R.Yen }) end
	for Category, Amount in R.Rep or {} do Reputation.Add(Player, Category, Amount, Def.Name) end
	for Npc, Amount in R.Relationship or {} do Reputation.ChangeRelationship(Player, Npc, Amount, Def.Name) end
	for Faction, Amount in R.Standing or {} do Factions.AddStanding(Player, Faction, Amount, Def.Name) end
	for Clique, Amount in R.Cliques or {} do pcall(function() Cliques().Add(Player, Clique, Amount, Def.Name) end) end
	if R.Title then Reputation.AwardTitle(Player, R.Title) end
end

function Local.ClearDrops(Player: Player, QuestId: string?)
	for Key, Part in Drops[Player] or {} do
		if not QuestId or Key:sub(1, #QuestId + 1) == `{QuestId}:` then
			if Part.Parent then Part:Destroy() end
			Drops[Player][Key] = nil
		end
	end
end

function Shared.Start(Player: Player, Id: string, Silent: boolean?): boolean
	local Ok = Shared.CanStart(Player, Id)
	if not Ok then return false end
	local Q = Local.Get(Player)
	local Def = Config.Quests[Id]

	local State = { Stage = Local.FirstRequired(Def, 1) or 1; Counts = {}; Items = {}; Data = {}; Secret = {}; Started = Local.Now() }
	if Def.Dare or Def.Job then State.DareDay = Shared.DareDay() end
	if Def.TimeLimit then
		State.Deadline = Local.Now() + Def.TimeLimit * SchoolTime.SecondsPerGameMinute()
	end
	for _, Item in Def.StartItems or {} do State.Items[Item] = `Held` end
	for _, Obj in Def.Objectives do
		if Obj.Type == `Collect` and Obj.Hidden then
			State.Secret[Obj.Id] = Obj.Objects[math.random(1, #Obj.Objects)]
		end
	end

	Q.Failed[Id] = nil
	Q.Active[Id] = State
	if Q.Tracked == `` or not Q.Active[Q.Tracked] or Def.Category == `Main` then Q.Tracked = Id end

	if not Silent then
		Local.Beat(Player, { Type = `Start`; Title = Def.Name; Text = Def.Objectives[State.Stage].Text; Category = Def.Category })
	end
	Local.Sync(Player)
	Shared.Started:Fire(Player, Id)
	Local.Refresh(Player, Id)
	return true
end

local function Sup(P, Id, N) -- (1.39) the Midnight Bell's weekly superlatives (Services.Social.Superlatives)
	pcall(function() require(game:GetService(`ServerScriptService`).Services.Social.Superlatives).Count(P, Id, N) end)
end

function Local.Complete(Player: Player, Id: string)
	local Q = Local.Get(Player)
	local Def = Config.Quests[Id]
	if not Q or not Q.Active[Id] then return end

	local Was = Q.Active[Id]
	Q.Active[Id] = nil
	if Def and (Def.Dare or Def.Job) then Sup(Player, `Power`) end -- (1.39)
	Q.Done[Id] = if Def.Dare or Def.Job then (Was and Was.DareDay or Shared.DareDay()) else Local.Day()
	if Collecting[Player] then table.insert(Collecting[Player], Id) end
	Local.ClearDrops(Player, Id)
	if Q.Tracked == Id then
		Q.Tracked = ``
		for Other in Q.Active do Q.Tracked = Other break end
	end

	-- the beat goes first so its banner plays before any level-up the rewards cause
	Local.Beat(Player, { Type = `Complete`; Title = Def.Name; Text = if Def.Rewards then Local.RewardText(Def.Rewards) else nil; Category = Def.Category; Story = Def.Ending })
	Local.GiveRewards(Player, Def)
	Local.Sync(Player)
	Shared.Completed:Fire(Player, Id)

	if Def.Next then Shared.Start(Player, Def.Next) end
	Local.AutoStart(Player)
end

function Shared.Fail(Player: Player, Id: string, Reason: string)
	local Q = Local.Get(Player)
	local Def = Config.Quests[Id]
	if not Q or not Q.Active[Id] then return end
	Q.Active[Id] = nil
	Q.Failed[Id] = Reason
	Local.ClearDrops(Player, Id)
	if Q.Tracked == Id then
		Q.Tracked = ``
		for Other in Q.Active do Q.Tracked = Other break end
	end
	local Giver = Def.Giver and require(ReplicatedStorage.Config.Npcs)[Def.Giver]
	Local.Beat(Player, {
		Type = `Fail`; Title = Def.Name; Category = Def.Category;
		Text = if Giver then `{Reason} Talk to {Giver.Name} to try again.` else Reason;
	})
	Local.Sync(Player)
	Shared.Failed:Fire(Player, Id, Reason)
end

function Shared.Abandon(Player: Player, Id: string): boolean
	local Def = Config.Quests[Id]
	local Q = Local.Get(Player)
	if not Def or not Q or not Q.Active[Id] or Def.Category == `Main` then return false end
	Q.Active[Id] = nil
	Local.ClearDrops(Player, Id)
	if Q.Tracked == Id then
		Q.Tracked = ``
		for Other in Q.Active do Q.Tracked = Other break end
	end
	Local.Notify(Player, { Title = `Quest abandoned: {Def.Name}`; Kind = `Info`; Duration = 3 })
	Local.Sync(Player)
	return true
end

function Local.AutoStart(Player: Player)
	for Id, Def in Config.Quests do
		if Def.Auto and Shared.CanStart(Player, Id) then Shared.Start(Player, Id) end
	end
end

---| Progress |---

function Local.Advance(Player: Player, Id: string, Def, State, Index: number, Obj)
	if Obj.Grants then Investigation.Grant(Player, Obj.Grants.Case, Obj.Grants.Clue) end
	if Obj.Optional then
		Local.Notify(Player, { Title = `Optional done`; Text = Obj.Text; Kind = `Good`; Duration = 3 })
		Local.Sync(Player)
		return
	end
	local Next = Local.FirstRequired(Def, Index + 1)
	if not Next then
		Local.Complete(Player, Id)
		return
	end
	State.Stage = Next
	Local.Beat(Player, { Type = `Stage`; Title = Def.Name; Text = Def.Objectives[Next].Text; Category = Def.Category })
	Local.Sync(Player)
	Local.Refresh(Player, Id)
end

-- Set (Absolute) or add to an objective's count; advances when it reaches Count.
function Local.Bump(Player: Player, Id: string, Index: number, Amount: number, Absolute: boolean?)
	local Q = Local.Get(Player)
	local State = Q and Q.Active[Id]
	local Def = Config.Quests[Id]
	local Obj = Def and Def.Objectives[Index]
	if not State or not Obj then return end

	local Need = Obj.Count or 1
	local Old = State.Counts[Obj.Id] or 0
	if Old >= Need then return end
	local New = math.min(Need, if Absolute then Amount else Old + Amount)
	if New <= Old then return end
	State.Counts[Obj.Id] = New

	if New >= Need then
		Local.Advance(Player, Id, Def, State, Index, Obj)
	else
		Local.Notify(Player, { Title = Def.Name; Text = `{Obj.Text} ({New}/{Need})`; Kind = `Info`; Duration = 3 })
		Local.Sync(Player)
	end
end

-- Objectives that can be in progress right now: the current one plus unfinished optional ones.
function Local.Live(State, Def): { number }
	local List = { State.Stage }
	for Index, Obj in Def.Objectives do
		if Obj.Optional and Index ~= State.Stage and (State.Counts[Obj.Id] or 0) < (Obj.Count or 1) then
			table.insert(List, Index)
		end
	end
	return List
end

function Local.Matches(Obj, Type: string, Key: any, Extra: any): boolean
	if Obj.Type ~= Type then return false end
	if Type == `Attend` then
		return (Key == `Present` or Key == `Tardy`) and (not Obj.Subject or Obj.Subject == Extra)
	elseif Type == `Talk` then
		return Obj.Npc == Key or (Obj.Npcs ~= nil and table.find(Obj.Npcs, Key) ~= nil)
	elseif Type == `Interact` then
		return Obj.Object == Key
	elseif Type == `Defeat` then
		return Obj.Target == Key
	elseif Type == `Duel` then
		return true
	elseif Type == `Execute` then
		return true
	elseif Type == `Drill` then
		return Obj.Drill == nil or Obj.Drill == Key
	elseif Type == `SportMatch` then
		return Obj.Sport == nil or Obj.Sport == Key
	elseif Type == `Lesson` then
		if Obj.Subject and Obj.Subject ~= Key then return false end
		return not Obj.MinGrade or (GRADE_ORDER[Extra] or 0) >= (GRADE_ORDER[Obj.MinGrade] or 0)
	elseif Type == `Clues` or Type == `Link` or Type == `Deduce` then
		return Obj.Case == Key
	elseif Type == `Scuffle` then -- (1.28) won a scuffle for a clique (Social.CliqueFights)
		return Obj.Clique == nil or Obj.Clique == Key
	elseif Type == `Prank` then -- (1.33) pranked a clique's hangout (Social.CliquePranks)
		return Obj.Victim == nil or Obj.Victim == Key
	elseif Type == `StopPrank` then -- (1.35) put down a prankster at Victim's hangout (Social.CliquePranks)
		return Obj.Victim == nil or Obj.Victim == Key
	end
	return false
end

-- Generic progress entry point for server events.
function Shared.Progress(Player: Player, Type: string, Key: any, Extra: any?, Absolute: number?)
	-- (1.39) the week's superlatives hear about pranks, fights won and showdowns won, quest or not
	if Type == `Prank` then Sup(Player, `Pranks`)
	elseif Type == `Scuffle` then Sup(Player, `Riots`)
	elseif Type == `Defeat` and typeof(Key) == `string` and Key:find(`^Showdown`) then Sup(Player, `Power`) end
	local Q = Local.Get(Player)
	if not Q then return end
	for Id, State in table.clone(Q.Active) do
		local Def = Config.Quests[Id]
		if not Def then continue end
		for _, Index in Local.Live(State, Def) do
			local Obj = Def.Objectives[Index]
			if Obj and Local.Matches(Obj, Type, Key, Extra) and Local.TimeOk(Obj) then
				if Absolute then Local.Bump(Player, Id, Index, Absolute, true) else Local.Bump(Player, Id, Index, 1) end
			end
		end
	end
end

-- Re-check objectives whose state may already be satisfied (investigation counts).
function Local.Refresh(Player: Player, Id: string)
	local Q = Local.Get(Player)
	local State = Q and Q.Active[Id]
	local Def = Config.Quests[Id]
	if not State or not Def then return end
	local Obj = Def.Objectives[State.Stage]
	if Obj and (Obj.Type == `Clues` or Obj.Type == `Link` or Obj.Type == `Deduce`) then
		local Count = Investigation.Count(Player, Obj.Case, Obj.Type)
		if Count > 0 then Local.Bump(Player, Id, State.Stage, Count, true) end
	end
end

---| Talking (called by Dialogue before the first line) |---

-- Returns the quests this conversation just completed (so the NPC can say thanks).
function Shared.OnTalk(Player: Player, NpcId: string): { string }
	Collecting[Player] = {}
	Shared.Progress(Player, `Talk`, NpcId)

	local Q = Local.Get(Player)
	for Id, State in table.clone(Q and Q.Active or {}) do
		local Def = Config.Quests[Id]
		local Obj = Def and Def.Objectives[State.Stage]
		if Obj and Obj.Type == `Deliver` and Obj.Npc == NpcId then
			local Held = State.Items[Obj.Item]
			if Held == `Held` then
				State.Items[Obj.Item] = nil
				Local.Bump(Player, Id, State.Stage, 1)
			elseif Held == `Dropped` then
				local Item = Config.Items[Obj.Item]
				Local.Notify(Player, { Title = `You dropped the {Item and Item.Name or Obj.Item}!`; Text = `Go back and pick it up.`; Kind = `Warning`; Duration = 4 })
			end
		end
	end

	local Completed = Collecting[Player] or {}
	Collecting[Player] = nil
	return Completed
end

---| Quest objects |---

function Shared.OnInteract(Player: Player, ObjectId: string, Part: BasePart?)
	local Root = Places.Root(Player)
	Part = Part or Places.Find(`QuestObject`, ObjectId)
	if not Root or not Part or (Root.Position - Part.Position).Magnitude > INTERACT_RANGE then return end
	if Local.Busy(Player) then return end
	local Now = os.clock()
	if LastInteract[Player] and Now - LastInteract[Player] < 0.4 then return end
	LastInteract[Player] = Now

	local Q = Local.Get(Player)
	if not Q then return end
	local ObjDef = Config.Objects[ObjectId]
	local Useful = false

	-- Clues
	if ObjDef and ObjDef.Clue then
		if Investigation.HasClue(Player, ObjDef.Clue.Case, ObjDef.Clue.Id) then
			Useful = true
			local Clue = Cases[ObjDef.Clue.Case].Clues[ObjDef.Clue.Id]
			Local.Notify(Player, { Title = Clue.Name; Text = `Already in your case file.`; Kind = `Info`; Duration = 3 })
		elseif Investigation.Find(Player, ObjDef.Clue.Case, ObjDef.Clue.Id, Part.Position) then
			Useful = true
		end
	end

	-- Collect / search
	for Id, State in table.clone(Q.Active) do
		local Def = Config.Quests[Id]
		local Obj = Def and Def.Objectives[State.Stage]
		if not Obj or Obj.Type ~= `Collect` or not table.find(Obj.Objects, ObjectId) then continue end
		Useful = true
		if not Local.TimeOk(Obj) then
			Local.Notify(Player, { Title = `Not yet`; Text = TIME_TEXT; Kind = `Info`; Duration = 4 })
			continue
		end
		if Obj.Hidden and (State.Secret or {})[Obj.Id] ~= ObjectId then
			State.Data.Searched = State.Data.Searched or {}
			if not table.find(State.Data.Searched, ObjectId) then table.insert(State.Data.Searched, ObjectId) end
			Local.Notify(Player, { Title = `Nothing here`; Text = `Not this spot. Keep looking.`; Kind = `Info`; Duration = 3 })
			Local.Sync(Player)
			continue
		end
		State.Items[Obj.Item] = `Held`
		local Item = Config.Items[Obj.Item]
		Local.Notify(Player, { Title = `Got: {Item and Item.Name or Obj.Item}`; Kind = `Good`; Duration = 3 })
		Local.Bump(Player, Id, State.Stage, 1)
	end

	-- Plain interactions
	for Id, State in table.clone(Q.Active) do
		local Def = Config.Quests[Id]
		if not Def then continue end -- an id no longer in the config (it used to error here and break every object)
		for _, Index in Local.Live(State, Def) do
			local Obj = Def.Objectives[Index]
			if Obj.Type == `Interact` and Obj.Object == ObjectId then
				Useful = true
				if Local.TimeOk(Obj) then
					-- VFX P1-12: the prop answers (rite effects, votives; client Controllers.World.ObjectFx)
					if (State.Counts[Obj.Id] or 0) < (Obj.Count or 1) then Fx.Fire(Player, `ObjectFx`, { Object = ObjectId }) end
					Local.Bump(Player, Id, Index, 1)
					-- (1.28) some objects are mischief: a hall monitor who sees it books it (Objects.<id>.Witness)
					if ObjDef and ObjDef.Witness then
						pcall(function() require(ServerScriptService.Services.School.HallMonitor).CheckWitness(Player, ObjDef.Witness) end)
					end
				else
					Local.Notify(Player, { Title = `Not yet`; Text = Local.TimeText(Obj); Kind = `Info`; Duration = 4 })
				end
			end
		end
	end

	if not Useful then
		Local.Notify(Player, { Title = ObjDef and ObjDef.Name or `Nothing here`; Text = `Nothing useful here right now.`; Kind = `Info`; Duration = 2 })
	end
end

function Local.SetupObject(Part: BasePart)
	local Id = Part:GetAttribute(`QuestObject`)
	local Def = Config.Objects[Id]
	if not Def or Part:FindFirstChild(`QuestPrompt`) then return end
	local Prompt = Instance.new(`ProximityPrompt`)
	Prompt.Name = `QuestPrompt`
	Prompt.ActionText = Def.Action
	Prompt.ObjectText = Def.Name
	Prompt.KeyboardKeyCode = Interaction.PromptKey
	Prompt.GamepadKeyCode = Interaction.GamepadKey
	Prompt.HoldDuration = Def.Hold or 0.4
	Prompt.MaxActivationDistance = 8
	Prompt.RequiresLineOfSight = false
	Prompt:SetAttribute(`QuestObject`, Id) -- the client hides prompts you have no use for
	Prompt.Parent = Part
	Prompt.Triggered:Connect(function(Player)
		local Ok, Err = pcall(Shared.OnInteract, Player, Id, Part)
		if not Ok then warn(`[Quests] {Err}`) end
	end)
end

---| Dropped items |---

function Local.DropItems(Player: Player)
	local Q = Local.Get(Player)
	local Root = Places.Root(Player)
	if not Q or not Root then return end
	for Id, State in Q.Active do
		for Item, Status in State.Items do
			local ItemDef = Config.Items[Item]
			if Status ~= `Held` or not ItemDef or not ItemDef.Droppable then continue end
			State.Items[Item] = `Dropped`

			local Part = Instance.new(`Part`)
			Part.Name = `Dropped {ItemDef.Name}`
			Part.Size = Vector3.new(1.4, 1, 1.4)
			Part.Color = Color3.fromRGB(190, 150, 90)
			Part.Material = Enum.Material.Cardboard
			Part.CanCollide = false
			Part.Anchored = true
			Part.CFrame = CFrame.new(Root.Position + Root.CFrame.RightVector * 2 - Vector3.new(0, 2.4, 0))
			Part:SetAttribute(`DropOwner`, Player.UserId)
			Part:SetAttribute(`DropItem`, Item)
			-- only the owner sees it: other clients hide tagged objects (Controllers.World.OwnedObjects)
			Part:SetAttribute(`OwnerUserId`, Player.UserId)
			game:GetService(`CollectionService`):AddTag(Part, `NHOwnedObject`)
			local Prompt = Instance.new(`ProximityPrompt`)
			Prompt.ActionText = `Pick up`
			Prompt.ObjectText = ItemDef.Name
			Prompt.KeyboardKeyCode = Interaction.PromptKey
			Prompt.GamepadKeyCode = Interaction.GamepadKey
			Prompt.HoldDuration = 0.3
			Prompt.MaxActivationDistance = 8
			Prompt.RequiresLineOfSight = false
			Prompt:SetAttribute(`DropOwner`, Player.UserId) -- only the owner sees it
			Prompt.Parent = Part
			local Light = Instance.new(`PointLight`)
			Light.Color = Color3.fromRGB(255, 220, 120)
			Light.Range = 8
			Light.Parent = Part

			local Folder = workspace:FindFirstChild(`QuestDrops`) or Instance.new(`Folder`)
			Folder.Name = `QuestDrops`
			Folder.Parent = workspace
			Part.Parent = Folder

			local Key = `{Id}:{Item}`
			Drops[Player] = Drops[Player] or {}
			Drops[Player][Key] = Part
			Prompt.Triggered:Connect(function(Who)
				if Who ~= Player then return end
				local R = Places.Root(Player)
				if not R or (R.Position - Part.Position).Magnitude > INTERACT_RANGE or Local.Busy(Player) then return end
				local Now = Local.Get(Player)
				local S = Now and Now.Active[Id]
				if S and S.Items[Item] == `Dropped` then
					S.Items[Item] = `Held`
					Local.Notify(Player, { Title = `Picked up: {ItemDef.Name}`; Kind = `Good`; Duration = 3 })
					Local.Sync(Player)
				end
				Part:Destroy()
				if Drops[Player] then Drops[Player][Key] = nil end
			end)

			Local.Notify(Player, { Title = `You dropped the {ItemDef.Name}!`; Text = `Pick it back up when you're on your feet.`; Kind = `Warning`; Duration = 5 })
			Local.Sync(Player)
		end
	end
end

---| Stealth checkpoints |---

function Local.OnCaught(Player: Player, ZoneId: string)
	local Q = Local.Get(Player)
	if not Q then return end
	for Id, State in Q.Active do
		local Def = Config.Quests[Id]
		if not Def or not Def.Stealth or Def.Stealth.Zone ~= ZoneId then continue end -- (audit) stale quest id
		local Checkpoint = Local.ObjectiveIndex(Def, Def.Stealth.Checkpoint)
		if not Checkpoint or State.Stage < Checkpoint then continue end

		local Lost = {}
		for Index = Checkpoint, #Def.Objectives do
			local Obj = Def.Objectives[Index]
			State.Counts[Obj.Id] = nil
			if Obj.Type == `Collect` and Obj.Item and State.Items[Obj.Item] then
				State.Items[Obj.Item] = nil
				local Item = Config.Items[Obj.Item]
				table.insert(Lost, Item and Item.Name or Obj.Item)
			end
		end
		State.Stage = Checkpoint
		Local.ClearDrops(Player, Id)
		Local.Notify(Player, {
			Title = `{Def.Name}: try again`;
			Text = if #Lost > 0 then `They took back the {table.concat(Lost, `, `)}. Stay out of sight this time.` else `Stay out of sight this time.`;
			Kind = `Warning`; Duration = 6;
		})
		Local.Sync(Player)
	end
end

---| Loop: areas + deadlines |---

function Local.ExpireDare(Player: Player, Id: string)
	local Q = Local.Get(Player)
	local Def = Config.Quests[Id]
	if not (Q and Q.Active[Id] and Def) then return end
	Q.Active[Id] = nil
	Local.ClearDrops(Player, Id)
	if Q.Tracked == Id then
		Q.Tracked = ``
		for Other in Q.Active do Q.Tracked = Other break end
	end
	Local.Sync(Player)
	pcall(Notifications.Notify, Player, { Title = `Dare expired`; Text = `"{Def.Name}" ran out at dawn.`; Kind = `Info`; Duration = 4 })
end

function Local.Tick()
	local Now = Local.Now()
	for _, Player in Players:GetPlayers() do
		local Q = Local.Get(Player)
		if not Q then continue end
		local Root = Places.Root(Player)
		for Id, State in table.clone(Q.Active) do
			local Def = Config.Quests[Id]
			if not Def then continue end
			if State.Deadline and Now > State.Deadline then
				Shared.Fail(Player, Id, `You ran out of time.`)
				continue
			end
			-- (1.33) a dare lasts until 6 AM: then it's simply gone (no "failed" entry)
			if (Def.Dare or Def.Job) and State.DareDay and State.DareDay ~= Shared.DareDay() then
				Local.ExpireDare(Player, Id)
				continue
			end
			local Obj = Def.Objectives[State.Stage]
			if Obj and Obj.Type == `Reach` and Root and Local.TimeOk(Obj) and Places.InArea(Obj.Area, Root.Position) then
				if not Obj.Item or State.Items[Obj.Item] == `Held` then
					Local.Bump(Player, Id, State.Stage, 1)
				end
			end
		end
	end
end

---| Client requests |---

function Local.OnAction(Player: Player, Message)
	if typeof(Message) ~= `table` then return end
	local Q = Local.Get(Player)
	if not Q then return end
	local Action = Message.Action
	if Action == `Track` and typeof(Message.Quest) == `string` and Q.Active[Message.Quest] then
		Q.Tracked = Message.Quest
		Local.Sync(Player)
	elseif Action == `Abandon` and typeof(Message.Quest) == `string` then
		-- (audit) owner: players can't abandon rite or showdown quests (Admin QuestAbandon still can)
		local Def = Config.Quests[Message.Quest]
		if not (Def and (Def.Category == `Rite` or Def.Showdown)) then
			Shared.Abandon(Player, Message.Quest)
		end
	elseif Action == `Link` and typeof(Message.Case) == `string` then
		Investigation.Link(Player, Message.Case, Message.A, Message.B)
	elseif Action == `Deduce` and typeof(Message.Case) == `string` then
		Investigation.Deduce(Player, Message.Case, Message.Option)
	end
end

---| Testing |---

function Shared.ResetForTests(Player: Player)
	local Profile = Data.GetProfile(Player)
	if not Profile then return end
	Local.ClearDrops(Player)
	Profile.Quests = nil
	Local.Get(Player)
	Local.Sync(Player)
end

function Shared.StateForTests(Player: Player)
	return Local.Get(Player)
end

function Shared.SetDeadlineForTests(Player: Player, Id: string, SecondsFromNow: number)
	local Q = Local.Get(Player)
	if Q and Q.Active[Id] then Q.Active[Id].Deadline = Local.Now() + SecondsFromNow end
end

function Shared.AutoStartForTests(Player: Player)
	Local.AutoStart(Player)
end

---| Start |---

function Shared.OnStart()
	-- quest-giver seals also change with the clock and other systems (rites, factions): re-check now and then
	task.spawn(function()
		while true do
			task.wait(15)
			for _, P in Players:GetPlayers() do task.spawn(Local.SendSeals, P) end
		end
	end)
	Investigation.Init({
		Get = Local.Get;
		Sync = Local.Sync;
		Notify = Local.Notify;
		-- A case opens once a quest that uses it is active or done.
		IsOpen = function(Player: Player, CaseId: string): boolean
			local Q = Local.Get(Player)
			if not Q then return false end
			for Id, Def in Config.Quests do
				if Q.Active[Id] or Q.Done[Id] then
					for _, Obj in Def.Objectives do
						if Obj.Case == CaseId then return true end
					end
				end
			end
			return false
		end;
		Changed = function(Player: Player, CaseId: string, Kind: string)
			Shared.Progress(Player, Kind, CaseId, nil, Investigation.Count(Player, CaseId, Kind))
		end;
	})

	for _, Part in Places.FindAll(`QuestObject`) do Local.SetupObject(Part) end
	workspace.DescendantAdded:Connect(function(Part)
		if Part:IsA(`BasePart`) and Part:GetAttribute(`QuestObject`) then Local.SetupObject(Part) end
	end)

	Attendance.Recorded:Connect(function(Player, Record)
		Shared.Progress(Player, `Attend`, Record.Status, Record.Subject)
	end)
	Activities.Finished:Connect(function(Player, Subject, Result)
		if Result.Passed and not Result.Practice then Shared.Progress(Player, `Lesson`, Subject, Result.Grade) end
	end)
	Stealth.Caught:Connect(function(Player, ZoneId)
		local Ok, Err = pcall(Local.OnCaught, Player, ZoneId)
		if not Ok then warn(`[Quests] {Err}`) end
	end)
	Duels.Won:Connect(function(Player) Shared.Progress(Player, `Duel`, true) end)
	Duels.ChampionDefeated:Connect(function(Player) Shared.Progress(Player, `Defeat`, `RingChampion`) end)
	-- grip finishes (rites: feed / hunt)
	Downed.OnExecuted:Connect(function(Gripper)
		local Player = Players:GetPlayerFromCharacter(Gripper)
		if Player then Shared.Progress(Player, `Execute`, true) end
	end)
	Downed.OnDowned:Connect(function(Target)
		local Player = Players:GetPlayerFromCharacter(Target)
		if Player then
			local Ok, Err = pcall(Local.DropItems, Player)
			if not Ok then warn(`[Quests] {Err}`) end
		end
	end)

	Packets.QuestAction.OnServerEvent:Connect(function(Player, Message)
		local Ok, Err = pcall(Local.OnAction, Player, Message)
		if not Ok then warn(`[Quests] {Err}`) end
	end)

	-- Joining: dropped items come back (the drop is gone), then auto quests start.
	local function Init(Player: Player)
		local Q = Local.Get(Player)
		if not Q then return end
		for Id, State in Q.Active do
			State.Items = if typeof(State.Items) == `table` then State.Items else {}
			State.Counts = if typeof(State.Counts) == `table` then State.Counts else {}
			State.Data = if typeof(State.Data) == `table` then State.Data else {}
			State.Secret = if typeof(State.Secret) == `table` then State.Secret else {}
			for Item, Status in State.Items do
				if Status == `Dropped` then State.Items[Item] = `Held` end
			end
			-- Repair: a hidden search with no secret spot gets a new one (never strands the quest).
			local Def = Config.Quests[Id]
			for _, Obj in Def and Def.Objectives or {} do
				if Obj.Type == `Collect` and Obj.Hidden and not State.Secret[Obj.Id] then
					local Searched = State.Data.Searched or {}
					local Options = {}
					for _, Object in Obj.Objects do
						if not table.find(Searched, Object) then table.insert(Options, Object) end
					end
					if #Options == 0 then
						Options = Obj.Objects
						State.Data.Searched = {}
					end
					State.Secret[Obj.Id] = Options[math.random(1, #Options)]
				end
			end
		end
		Local.AutoStart(Player)
		Local.Sync(Player)
	end
	Data.ProfileLoaded:Connect(Init)
	for _, Player in Players:GetPlayers() do task.spawn(Init, Player) end

	Players.PlayerRemoving:Connect(function(Player)
		LastSeals[Player] = nil
		Local.ClearDrops(Player)
		Drops[Player] = nil
		PendingSync[Player] = nil
		LastInteract[Player] = nil
		Collecting[Player] = nil
		Investigation.Forget(Player)
	end)

	task.spawn(function()
		while true do
			task.wait(0.5)
			local Ok, Err = pcall(Local.Tick)
			if not Ok then warn(`[Quests] {Err}`) end
		end
	end)
end

return Shared

