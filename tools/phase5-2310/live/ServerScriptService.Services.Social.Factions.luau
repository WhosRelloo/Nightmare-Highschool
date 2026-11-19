--[[
	Factions (server authoritative). Rules in Config.Factions.

	Per player and faction (saved in PlayerData.Social.Factions[Id]):
		Standing, Member, Rank, JoinedDay, LeftDay, Flags (initiation), Missions, Daily (limits), PassDay.

	Where standing comes from (all server events, never the client):
		Vigil         lesson grades (Activities.Finished), Night Study, minus for truancy catches
		CrimsonCourt  marking walls (Pranks.Marked), escaping hall monitors, downing people
	Rivals lose a share of what you gain. Rivals are exclusive for membership.

	Perks are exposed as player attributes (Perk_<Id> = true) so other systems read them
	without requiring this module: HallMonitor (VigilPass via CatchFilter, Shadowstep),
	Pranks (Unseen), Activities (LessonYenBonus).

	API: AddStanding, SetFlag, CanJoin, Join, Leave, Get(Player, Id), RankFor, RankIndex,
	     GetMissionProgress. Signals: RankChanged, Joined, Left.
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local SignalPlus = require(ReplicatedStorage.Packages.SignalPlus)
local Config = require(ReplicatedStorage.Config.Factions)
local Classes = require(ReplicatedStorage.Config.Classes)

local Reputation = require(ServerScriptService.Services.Social.Reputation)
local SchoolClock = require(ServerScriptService.Services.School.SchoolClock)
local Activities = require(ServerScriptService.Services.School.Activities)
local HallMonitor = require(ServerScriptService.Services.School.HallMonitor)
local Pranks = require(ServerScriptService.Services.Social.Pranks)
local Downed = require(ServerScriptService.Services.Features.Downed)
local Data = require(ServerScriptService.Services.Player.Data)
local Notifications = require(ServerScriptService.Services.Features.Notifications)

local Local = {}
local Shared = {}

Shared.RankChanged = SignalPlus() -- (Player, FactionId, NewRank, OldRank)
Shared.Joined = SignalPlus()
Shared.Left = SignalPlus()

local RANK_INDEX = {} :: { [string]: number }
for Index, Rank in Config.Ranks do RANK_INDEX[Rank.Name] = Index end
local PROSPECT_MIN = Config.Ranks[2].Min

---| Data |---

function Local.Day(): number
	return SchoolClock.GetState().Day
end

function Shared.Get(Player: Player, Id: string): any?
	if not Config.Factions[Id] then return nil end
	local Social = Reputation.Get(Player)
	if not Social then return nil end

	local F = Social.Factions[Id]
	if typeof(F) ~= `table` then
		F = {}
		Social.Factions[Id] = F
	end
	F.Standing = F.Standing or 0
	F.Member = F.Member == true
	F.Rank = F.Rank or `Outsider`
	F.JoinedDay = F.JoinedDay or -1
	F.LeftDay = F.LeftDay or -1
	F.PassDay = F.PassDay or -1
	F.Flags = if typeof(F.Flags) == `table` then F.Flags else {}
	F.Missions = if typeof(F.Missions) == `table` then F.Missions else {}
	F.Daily = if typeof(F.Daily) == `table` then F.Daily else { Day = -1; Counts = {} }
	return F
end

function Shared.RankIndex(Name: string): number
	return RANK_INDEX[Name] or 1
end

function Shared.RankFor(Player: Player, Id: string): string
	local F = Shared.Get(Player, Id)
	local Def = Config.Factions[Id]
	if not F or not Def then return `Outsider` end

	local Result = Config.Ranks[1].Name
	for _, Rank in Config.Ranks do
		if F.Standing < Rank.Min then break end
		if Rank.RequiresMember and not F.Member then break end
		if Rank.Name == `Inner Circle` and Def.InnerCircleRequires then
			local Need = Def.InnerCircleRequires
			if Reputation.Value(Player, Need.Reputation) < Need.Min then break end
		end
		Result = Rank.Name
	end
	return Result
end

-- Perks as attributes so other services can read them without requiring this module.
function Local.ApplyPerks(Player: Player)
	local LessonBonus = 1
	for Id, Def in Config.Factions do
		local F = Shared.Get(Player, Id)
		for RankName, Perk in Def.Perks or {} do
			local Has = F and F.Member and Shared.RankIndex(F.Rank) >= Shared.RankIndex(RankName)
			Player:SetAttribute(`Perk_{Perk.Id}`, if Has then true else nil)
			if Has and Perk.Id == `BlessedScholar` then LessonBonus = 1.5 end
		end
		Player:SetAttribute(`Faction_{Id}`, if F and F.Member then F.Rank else nil)
	end
	Player:SetAttribute(`LessonYenBonus`, if LessonBonus ~= 1 then LessonBonus else nil)
end

function Local.Recompute(Player: Player, Id: string, Quiet: boolean?)
	local F = Shared.Get(Player, Id)
	if not F then return end
	local Old = F.Rank
	local New = Shared.RankFor(Player, Id)
	F.Rank = New
	Local.ApplyPerks(Player)
	Reputation.Sync(Player)

	if New ~= Old then
		local Def = Config.Factions[Id]
		local Up = Shared.RankIndex(New) > Shared.RankIndex(Old)
		-- Popularity only for ranks never reached before (no farming by leaving and rejoining).
		if Up and Shared.RankIndex(New) > Shared.RankIndex(F.BestRank or `Outsider`) then
			F.BestRank = New
			Reputation.Add(Player, `Popularity`, 3, `Rank up`)
		end
		if not Quiet then
			local Perk = Def.Perks and Def.Perks[New]
			Notifications.Notify(Player, {
				Title = `{Def.Name}: {New}`;
				Text = if Up and Perk then `Perk unlocked: {Perk.Name}` elseif Up then `Rank up!` else `Your rank dropped.`;
				Kind = if Up then `Good` else `Bad`;
				Duration = 6;
			})
		end
		Shared.RankChanged:Fire(Player, Id, New, Old)
	end
end

---| Standing |---

function Shared.AddStanding(Player: Player, Id: string, Amount: number, Reason: string?, FromRival: boolean?)
	local F = Shared.Get(Player, Id)
	local Def = Config.Factions[Id]
	if not F or not Def or Amount == 0 then return end

	local Cap = if F.Member then Config.MaxStanding else Config.NonMemberCap
	local Old = F.Standing
	F.Standing = math.clamp(F.Standing + Amount, 0, math.max(Cap, if Amount < 0 then F.Standing else 0))
	local Delta = F.Standing - Old

	if Amount > 0 and not FromRival then
		for _, RivalId in Def.Rivals or {} do
			Shared.AddStanding(Player, RivalId, -Amount * Config.RivalShare, nil, true)
		end
	end

	if not FromRival and math.abs(Delta) >= 0.5 then
		Notifications.Notify(Player, {
			Title = `{if Delta > 0 then `+` else ``}{math.floor(Delta + 0.5)} {Def.Name}`;
			Text = Reason;
			Kind = if Delta > 0 then `Info` else `Warning`;
			Duration = 3;
		})
	elseif not FromRival and Amount > 0 and Delta == 0 and not F.Member and Old >= Config.NonMemberCap then
		Notifications.Notify(Player, { Title = `{Def.Name} has noticed you`; Text = `Join them to keep rising (talk to {Def.Leader}).`; Kind = `Info`; Duration = 4 })
	end

	Local.Recompute(Player, Id)
end

-- Daily limit for farmable sources. Returns true if this one still counts.
function Local.DailyAllow(Player: Player, Id: string, Key: string): boolean
	local F = Shared.Get(Player, Id)
	if not F then return false end
	local Day = Local.Day()
	if F.Daily.Day ~= Day then F.Daily = { Day = Day; Counts = {} } end
	local Limit = Config.Standing.DailyLimits[Key]
	local Count = (F.Daily.Counts[Key] or 0) + 1
	if Limit and Count > Limit then return false end
	F.Daily.Counts[Key] = Count
	return true
end

function Shared.SetFlag(Player: Player, Id: string, Flag: string)
	local F = Shared.Get(Player, Id)
	local Def = Config.Factions[Id]
	if not F or F.Flags[Flag] then return end
	F.Flags[Flag] = true
	Reputation.Sync(Player)
	if Def.Initiation and Def.Initiation.Flag == Flag and not F.Member then
		Notifications.Notify(Player, { Title = `{Def.Name}: initiation complete`; Text = `Talk to {Def.Leader} to join.`; Kind = `Good`; Duration = 6 })
	end
end

---| Membership |---

function Shared.MemberOf(Player: Player): { string }
	local Result = {}
	for Id in Config.Factions do
		local F = Shared.Get(Player, Id)
		if F and F.Member then table.insert(Result, Id) end
	end
	return Result
end

-- Returns ok, reason (a short code for dialogue) .
function Shared.CanJoin(Player: Player, Id: string): (boolean, string)
	local F = Shared.Get(Player, Id)
	local Def = Config.Factions[Id]
	if not F or not Def then return false, `Unknown` end
	if F.Member then return false, `AlreadyMember` end
	-- (1.35) one crowd at a time: not while you're in one of the six cliques (Social.CliqueMembership)
	do
		local Ok, M = pcall(require, game:GetService(`ServerScriptService`).Services.Social.CliqueMembership)
		if Ok and M and M.Joined and M.Joined(Player) then return false, `CliqueMember` end
	end
	for _, RivalId in Def.Rivals or {} do
		local R = Shared.Get(Player, RivalId)
		if R and R.Member then return false, `RivalMember` end
	end
	if F.LeftDay >= 0 and Local.Day() < F.LeftDay + Config.RejoinCooldownDays then return false, `Cooldown` end
	if F.Standing < PROSPECT_MIN then return false, `NotNoticed` end
	if Def.Initiation and not F.Flags[Def.Initiation.Flag] then return false, `Initiation` end
	return true, `Ok`
end

function Shared.Join(Player: Player, Id: string): boolean
	local Ok = Shared.CanJoin(Player, Id)
	if not Ok then return false end

	local F = Shared.Get(Player, Id)
	local Def = Config.Factions[Id]
	local FirstTime = F.JoinedDay < 0
	F.Member = true
	F.JoinedDay = Local.Day()
	F.Standing = math.max(F.Standing, Config.Ranks[3].Min) -- joining makes you a Member
	Reputation.ChangeRelationship(Player, Def.Leader, 10)
	if FirstTime then Reputation.Add(Player, `Popularity`, 3, `Joined a faction`) end

	Notifications.Notify(Player, { Title = `You joined {Def.Name}`; Text = Def.Tagline; Kind = `Good`; Duration = 6 })
	Local.Recompute(Player, Id, true)
	Shared.Joined:Fire(Player, Id)
	return true
end

function Shared.Leave(Player: Player, Id: string): boolean
	local F = Shared.Get(Player, Id)
	local Def = Config.Factions[Id]
	if not F or not F.Member then return false end

	F.Member = false
	F.LeftDay = Local.Day()
	F.Standing = math.min(F.Standing * Config.LeaveKeepFraction, Config.NonMemberCap)
	Reputation.ChangeRelationship(Player, Def.Leader, -15, `You walked away from them.`)
	Reputation.Add(Player, `Trust`, -5, `Left a faction`)

	Notifications.Notify(Player, { Title = `You left {Def.Name}`; Kind = `Warning`; Duration = 5 })
	Local.Recompute(Player, Id, true)
	Shared.Left:Fire(Player, Id)
	return true
end

---| Missions |---

function Shared.GetMissionProgress(Player: Player, Id: string): any
	local F = Shared.Get(Player, Id)
	local Def = Config.Factions[Id]
	if not F or not Def.Mission then return nil end
	local M = F.Missions[Def.Mission.Id]
	if typeof(M) ~= `table` then
		M = { Done = false; Key = ``; Items = {} }
		F.Missions[Def.Mission.Id] = M
	end
	return M
end

-- Done, count for the current window (Vigil: today; Court: this class period). Old progress shows as 0.
function Shared.MissionStatus(Player: Player, Id: string): (boolean, number)
	local M = Shared.GetMissionProgress(Player, Id)
	if not M then return false, 0 end
	if M.Done then return true, 3 end
	local State = SchoolClock.GetState()
	local Current = if Id == `Vigil`
		then `Day{State.Day}`
		elseif State.Segment.Kind == `Class` then `D{State.Day}-S{State.SegmentIndex}` else nil
	return false, if Current and M.Key == Current then #M.Items else 0
end

function Local.MissionStep(Player: Player, Id: string, Key: string, Item: string)
	local F = Shared.Get(Player, Id)
	local Def = Config.Factions[Id]
	if not F or not F.Member or not Def.Mission then return end

	local M = Shared.GetMissionProgress(Player, Id)
	if M.Done then return end
	if M.Key ~= Key then
		M.Key = Key
		M.Items = {}
	end
	if table.find(M.Items, Item) then return end
	table.insert(M.Items, Item)
	Reputation.Sync(Player)

	if #M.Items >= 3 then
		M.Done = true
		local Reward = Def.Mission.Reward
		Notifications.Notify(Player, { Title = `Mission complete: {Def.Mission.Name}`; Text = `+{Reward.Standing} standing, +{Reward.Yen} Yen`; Kind = `Good`; Duration = 7 })
		if Reward.Yen and Reward.Yen > 0 then
			Data.UpdateState(Player, { type = `UpdateYen`; amount = Reward.Yen })
		end
		if Reward.Title then Reputation.AwardTitle(Player, Reward.Title) end
		Shared.AddStanding(Player, Id, Reward.Standing, Def.Mission.Name)
	else
		Notifications.Notify(Player, { Title = `{Def.Mission.Name}: {#M.Items}/3`; Kind = `Info`; Duration = 3 })
	end
end

---| Event hooks |---

function Local.OnLesson(Player: Player, Subject: string, Result)
	if Result.Practice or Result.Cancelled then return end
	local Grade = Result.Grade

	local Amount = Config.Standing.LessonGrade[Grade] or 0
	if Amount ~= 0 then
		Shared.AddStanding(Player, `Vigil`, Amount, `{Subject} grade {Grade}`)
	end

	local Academic = ({ [`A+`] = 3; A = 2; B = 1; C = 0; D = 0; F = -1 })[Grade] or 0
	if Academic ~= 0 then Reputation.Add(Player, `Academics`, Academic, `Lesson grade`) end

	if Grade == `A+` or Grade == `A` or Grade == `B` then
		Shared.SetFlag(Player, `Vigil`, `GradeB`)
	end
	if Result.Passed then
		Local.MissionStep(Player, `Vigil`, `Day{Local.Day()}`, Subject)
	end
end

function Local.OnStudy(Player: Player, Subject: string, Result)
	local Amount = Config.Standing.Study[Result.Grade] or 0
	if Amount > 0 then
		Shared.AddStanding(Player, `Vigil`, Amount, `Night Study ({Subject})`)
	end
	if Result.Passed then Reputation.Add(Player, `Academics`, 1, `Night Study`) end
	return if Amount > 0 then `+{Amount} The Vigil standing` else nil
end

-- Spotted from afar: it only counts as clean once you actually lose the monitor.
local PendingMarks = {} :: { [Player]: { { Wall: string, Info: any, At: number } } }

-- (audit) is a hall monitor chasing this player right now?
function Local.ChasedBy(Player: Player): boolean
	local Ok, List = pcall(HallMonitor.GetMonitors)
	for _, M in (Ok and List) or {} do
		if M.State == `Chase` and M.Target == Player.Name then return true end
	end
	return false
end

function Local.OnMarked(Player: Player, Wall: string, Info)
	if Info.Recognized then
		Shared.AddStanding(Player, `CrimsonCourt`, Config.Standing.MarkCaught, `Marked a wall (but you were seen)`)
		return
	end
	-- (audit) only wait on a chase that really started on this player (a monitor already chasing someone else just keeps
	-- going and nothing settles the mark); stamped so an unsettled one expires
	if Info.Spotted and Local.ChasedBy(Player) then
		PendingMarks[Player] = PendingMarks[Player] or {}
		table.insert(PendingMarks[Player], { Wall = Wall; Info = Info; At = os.clock() })
		return
	end
	Local.CleanMark(Player, Wall, Info)
end

function Local.SettleMarks(Player: Player, Escaped: boolean)
	local List = PendingMarks[Player]
	PendingMarks[Player] = nil
	for _, Pending in List or {} do
		if os.clock() - (Pending.At or 0) > 120 then continue end -- (audit) expired: that chase ended some other way
		if Escaped then
			Local.CleanMark(Player, Pending.Wall, Pending.Info)
		else
			Shared.AddStanding(Player, `CrimsonCourt`, Config.Standing.MarkCaught, `Marked a wall (but got caught)`)
		end
	end
end

function Local.CleanMark(Player: Player, Wall: string, Info)
	Shared.AddStanding(Player, `CrimsonCourt`, Config.Standing.MarkClean + (Info.Bonus or 0), `Marked a wall unseen`)
	Shared.SetFlag(Player, `CrimsonCourt`, `CleanMark`)
	if Info.PeriodKey then
		Local.MissionStep(Player, `CrimsonCourt`, Info.PeriodKey, Wall)
	end
end

function Shared.OnStart()
	-- Lessons -> Vigil standing / Academics
	Activities.Finished:Connect(function(Player, Subject, Result)
		local Ok, Err = pcall(Local.OnLesson, Player, Subject, Result)
		if not Ok then warn(`[Factions] {Err}`) end
	end)
	Activities.StudyHandler = function(Player, Subject, Result)
		local Ok, Line = pcall(Local.OnStudy, Player, Subject, Result)
		return if Ok then Line else nil
	end

	-- Walls -> Court standing, initiation, mission
	Pranks.Marked:Connect(function(Player, Wall, Info)
		local Ok, Err = pcall(Local.OnMarked, Player, Wall, Info)
		if not Ok then warn(`[Factions] {Err}`) end
	end)

	-- Hall monitors
	HallMonitor.Escaped:Connect(function(Player, Reason)
		Local.SettleMarks(Player, true) -- any chase you escape clears pending marks
		if Local.DailyAllow(Player, `CrimsonCourt`, `EscapedMonitor`) then
			Shared.AddStanding(Player, `CrimsonCourt`, Config.Standing.EscapedMonitor, `Gave a hall monitor the slip`)
		end
	end)
	HallMonitor.Caught:Connect(function(Player, Reason, Excused)
		Local.SettleMarks(Player, false)
		if Reason == `Truancy` and not Excused then
			Shared.AddStanding(Player, `Vigil`, Config.Standing.CaughtTruancy, `Caught skipping class`)
		end
	end)
	-- Vigil Pass: once per in-game day a catch becomes a warning.
	HallMonitor.CatchFilter = function(Player, Reason): (boolean, string?)
		if Player:GetAttribute(`Perk_VigilPass`) ~= true then return true, nil end
		local F = Shared.Get(Player, `Vigil`)
		local Day = Local.Day()
		if not F or F.PassDay == Day then return true, nil end
		F.PassDay = Day
		Reputation.Sync(Player)
		Notifications.Notify(Player, { Title = `Vigil Pass used`; Text = `The monitor let you off with a warning (once per day).`; Kind = `Info`; Duration = 5 })
		return false, `Vigil, huh? ...Fine. Don't make me regret it.`
	end

	-- Downing people -> Intimidation + Court standing
	Downed.OnDowned:Connect(function(Target, Attacker)
		local Player = Attacker and Players:GetPlayerFromCharacter(Attacker)
		if not Player or Target == Attacker then return end
		Reputation.Add(Player, `Intimidation`, 2, `Downed someone`)
		if Local.DailyAllow(Player, `CrimsonCourt`, `DownedSomeone`) then
			Shared.AddStanding(Player, `CrimsonCourt`, Config.Standing.DownedSomeone, `Put someone on the floor`)
		end
	end)
	Downed.OnExecuted:Connect(function(Gripper)
		local Player = Players:GetPlayerFromCharacter(Gripper)
		if Player then Reputation.Add(Player, `Intimidation`, 3, `Gripped someone`) end
	end)

	-- Inner Circle also needs a reputation score: re-rank when that score changes.
	Reputation.Changed:Connect(function(Player, Category)
		for Id, Def in Config.Factions do
			local Need = Def.InnerCircleRequires
			if Need and Need.Reputation == Category then Local.Recompute(Player, Id) end
		end
	end)

	-- Perk attributes for players already loaded / joining
	local function Init(Player)
		if not Reputation.Get(Player) then return end
		for Id in Config.Factions do Local.Recompute(Player, Id, true) end
	end
	Data.ProfileLoaded:Connect(Init)
	Players.PlayerRemoving:Connect(function(Player) PendingMarks[Player] = nil end)
	for _, Player in Players:GetPlayers() do task.spawn(Init, Player) end
end

return Shared
