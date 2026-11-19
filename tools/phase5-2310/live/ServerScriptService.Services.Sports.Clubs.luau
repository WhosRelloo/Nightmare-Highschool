--[[
	Clubs (server): sports club membership, club EXP and ranks, match records, drill bests.
	Saved in PlayerData.Sports via action SetSports (Config.Sports.Sanitize); only this module writes it.
	Mirrors read-only Player attributes Club (club id), ClubRank (rank name) for the HUD, Students list, nameplates.

	API: Get(p), Join(p, clubId), Leave(p), AddExp(p, amount, reason), Record(p, sport, won), DrillBest(p, drill, score, lowerIsBetter)
	Remotes: ReplicatedStorage.NHSports.Get (RemoteFunction) -> sheet, NHSports.Updated (RemoteEvent) -> sheet
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local Config = require(ReplicatedStorage.Config.Sports)
local Data = require(ServerScriptService.Services.Player.Data)

local Local = {}
local Shared = {}
local Folder = nil

local function try(Path: { string })
	local M = ServerScriptService
	for _, N in Path do M = M and M:FindFirstChild(N) end
	if not M then return nil end
	local Ok, Mod = pcall(require, M)
	return if Ok then Mod else nil
end

function Shared.Get(Player: Player)
	local Profile = Data.GetProfile(Player)
	return Profile and Config.Sanitize(Profile.Sports)
end

function Local.Save(Player: Player, S)
	Data.UpdateState(Player, { type = `SetSports`; sports = S })
	Local.Mirror(Player, S)
	Shared.Notify(Player)
end

function Local.Mirror(Player: Player, S)
	Player:SetAttribute(`Club`, S.Club)
	Player:SetAttribute(`ClubRank`, if S.Club then (Config.RankFor(S.ClubExp)) else nil)
end

function Local.Notify(Player: Player, Data_)
	local N = try({ `Services`, `Features`, `Notifications` })
	if N then pcall(N.Notify, Player, Data_) end
end

function Shared.Sheet(Player: Player)
	local S = Shared.Get(Player)
	if not S then return nil end
	local Rank, Index = Config.RankFor(S.ClubExp)
	local Next = Config.NextRank(S.ClubExp)
	return { Club = S.Club; ClubExp = S.ClubExp; Rank = if S.Club then Rank else nil; RankIndex = Index; Next = Next and { Name = Next.Name; Min = Next.Min } or nil;
		Record = S.Record; Drills = S.Drills }
end

function Shared.Notify(Player: Player)
	if Folder then
		local Sheet = Shared.Sheet(Player)
		if Sheet then Folder.Updated:FireClient(Player, Sheet) end
	end
end

-- Join a club (one at a time; switching resets club EXP)
function Shared.Join(Player: Player, ClubId: string): (boolean, string?)
	local Club = Config.Clubs[ClubId]
	local S = Shared.Get(Player)
	if not (Club and S) then return false, `Unknown club` end
	if S.Club == ClubId then return false, `You're already on the {Club.Name}` end
	local Switched = S.Club ~= nil
	S.Club = ClubId
	S.ClubExp = 0
	Local.Save(Player, S)
	Local.Notify(Player, { Title = `Welcome to the {Club.Name}`; Text = if Switched then `You switched clubs: your club rank starts again at Rookie.` else `Rookie for now. Drills and matches build your rank.`; Kind = `Good`; Duration = 6 })
	return true
end

function Shared.Leave(Player: Player): boolean
	local S = Shared.Get(Player)
	if not (S and S.Club) then return false end
	local Old = Config.Clubs[S.Club]
	S.Club = nil
	S.ClubExp = 0
	Local.Save(Player, S)
	Local.Notify(Player, { Title = `You left the {Old.Name}`; Text = `You can still play pickup games anytime.`; Kind = `Info`; Duration = 5 })
	return true
end

-- Club EXP (members only, for their own club's sport)
function Shared.AddExp(Player: Player, Sport: string, Amount: number, Reason: string?)
	local S = Shared.Get(Player)
	if not (S and S.Club) or Config.Clubs[S.Club].Sport ~= Sport or Amount <= 0 then return end
	local OldRank = Config.RankFor(S.ClubExp)
	S.ClubExp += math.floor(Amount)
	local NewRank, Index = Config.RankFor(S.ClubExp)
	Local.Save(Player, S)
	if NewRank ~= OldRank then
		local Club = Config.Clubs[S.Club]
		Local.Notify(Player, { Title = `{Club.Name}: {NewRank}`; Text = `You've been promoted to {NewRank}.`; Kind = `Good`; Duration = 6 })
		if Index == #Config.Ranks then
			local Rep = try({ `Services`, `Social`, `Reputation` })
			if Rep then pcall(Rep.AwardTitle, Player, `{Club.Short} Captain`) end
		end
	end
end

function Shared.Record(Player: Player, Sport: string, Won: boolean)
	local S = Shared.Get(Player)
	if not S then return end
	S.Record[Sport] = S.Record[Sport] or { W = 0; L = 0 }
	if Won then S.Record[Sport].W += 1 else S.Record[Sport].L += 1 end
	Local.Save(Player, S)
end

-- Saves a drill score when it beats the best; returns true when it's a new best
function Shared.DrillBest(Player: Player, Drill: string, Score: number, LowerIsBetter: boolean?): boolean
	local S = Shared.Get(Player)
	if not S or not Config.Drills[Drill] or typeof(Score) ~= `number` or Score ~= Score or Score <= 0 then return false end
	local Old = S.Drills[Drill]
	local Better = Old == nil or (if LowerIsBetter then Score < Old else Score > Old)
	if Better then
		S.Drills[Drill] = Score
		Local.Save(Player, S)
	end
	return Better
end

function Shared.OnStart()
	Folder = ReplicatedStorage:FindFirstChild(`NHSports`) or Instance.new(`Folder`)
	Folder.Name = `NHSports`
	local Get = Folder:FindFirstChild(`Get`) or Instance.new(`RemoteFunction`); Get.Name = `Get`; Get.Parent = Folder
	local Updated = Folder:FindFirstChild(`Updated`) or Instance.new(`RemoteEvent`); Updated.Name = `Updated`; Updated.Parent = Folder
	Folder.Parent = ReplicatedStorage
	Get.OnServerInvoke = function(Player) return Shared.Sheet(Player) end
	local function mirror(Player)
		local S = Shared.Get(Player)
		if S then Local.Mirror(Player, S) end
	end
	Data.ProfileLoaded:Connect(mirror)
	for _, Player in Players:GetPlayers() do mirror(Player) end   -- profiles that loaded before this started
end

return Shared
