--[[
	Admin (server): the Headmaster's Desk, the admin panel's back end.

	Levels (spec §6): 0 none; 1 moderator (group rank 254); 2 admin (Config.Cmdr.Admin / Testers); 3 owner (rank 255+ or
	Config.Cmdr.Owner). In Studio: 3, unless the server set NHTestLevel (0-3) or NHTestNotAdmin (= 0). Owner-only: permanent
	bans, Shutdown, Yen over 100,000, race rites. Moderators' bans are 30 days at most.
	Every request is checked here, never trusted from the client, rate-limited, and written to the action log.

	Remotes (ReplicatedStorage.NHAdmin): Info() -> { Level, Players, Server, Log, Gear, Lists, Locked, Registry, Sections }
	                                      Status() -> { Server, Players, Locked } (nil for level 0)
	                                      Run(Command, TargetUserId?, Args) -> ok, message  (= Shared.Dispatch)
	                                      Inspect(UserId) -> a read-only summary of that student's loaded slot
	                                      History(UserId) -> { Ok, UserId, Name, Record } | { Ok = false, Error }
	                                      LogDay(Offset, Filter) -> { Ok, Day, Rows, Total, Page, Pages } | { Ok = false, Error }
	                                      Prefs() -> { Ok, Favs, Side };  SavePrefs(Favs, Side) -> boolean
	1b (2026-11-23): saved records (Warn, Note, Mute, Unmute, Ban, Unban write them; Remove history entry is owner-only
	and logged), mute lengths re-applied on join, the saved staff log (every Dispatch call except "Not staff" and
	"Slow down"), and the History, LogDay, Prefs and SavePrefs remotes. Stores: Features.StaffRecords.
	                                      Client (RemoteEvent): server -> admin client effects (spectate, notices)

	1.18 added (the systems since 1.8): school & discipline (set points, lift suspension, excuse today, detention
	owed, start a lesson, skip to a period, ring the bell), progression (level, stat points, titles, places found),
	activities (force or end a match, set a club, start / drop / reset quests, tonight's full moon, go to a place),
	and QOL (bring all, freeze all, server lock, staff notes, the inspector).

	1a (2026-11-23): the console's registry (Admin.Meta), levels 0-3, argument checks.
]]
local Players = game:GetService(`Players`)
local RunService = game:GetService(`RunService`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local TextChatService = game:GetService(`TextChatService`)
local TextService = game:GetService(`TextService`)
local Stats = game:GetService(`Stats`)
local GroupService = game:GetService(`GroupService`)

local StaffConsole = require(ReplicatedStorage.Functions.StaffConsole)
local Meta = require(script:WaitForChild(`Meta`))
local Records = require(ReplicatedStorage.Functions.StaffRecords)
local StaffRecords = require(ServerScriptService.Services.Features.StaffRecords)

local ADMIN_RANK = 254
local OWNER_RANK = 255
local LOG_MAX = 200

local Shared = {}
local Log = {} :: { any }
local Muted = {} :: { [number]: number } -- UserId -> Until (os.time(); 0 = until unmuted); filled from the saved record on join
local God = {} :: { [Player]: boolean }
local Frozen = {} :: { [Player]: boolean }
local RankCache = {} :: { [Player]: number }
local LastRun = {} :: { [Player]: number }
local StartedAt = os.time()
local Folder, ClientEvent
-- Studio only: the Play checks set it so Ban and Unban write the record without the Roblox Ban API (or a kick)
Shared.TestSkipBanApi = false
-- (phase 2, Studio only) the Play check sets this to try the live-server rule for Season, Moon and Sky
Shared.TestLiveMode = false
local OfflineRank = {} :: { [number]: { R: number, At: number } }

local function svc(path: string)
	local node = ServerScriptService.Services
	for part in path:gmatch(`[^%.]+`) do node = node:FindFirstChild(part) if not node then return nil end end
	local ok, mod = pcall(require, node)
	return ok and mod or nil
end

local function cmdrCfg()
	local ok, c = pcall(require, ReplicatedStorage.Config.Cmdr)
	return ok and c or { Admin = {}, Owner = {}, Testers = {} }
end

local function rankOf(P: Player): number
	if RankCache[P] then return RankCache[P] end
	local r = 0
	if game.CreatorType == Enum.CreatorType.Group then
		local ok, v = pcall(P.GetRankInGroup, P, game.CreatorId)
		r = ok and v or 0
	elseif P.UserId == game.CreatorId then
		r = 255
	end
	RankCache[P] = r
	return r
end

-- 0 none, 1 moderator, 2 admin, 3 owner (spec §6). Studio: 3, or the server-set NHTestLevel (0-3); NHTestNotAdmin = 0.
function Shared.Level(P: Player): number
	local c = cmdrCfg()
	local Studio = RunService:IsStudio()
	return StaffConsole.LevelFrom({
		Studio = Studio;
		TestLevel = if Studio then P:GetAttribute(`NHTestLevel`) else nil;
		NotAdmin = Studio and P:GetAttribute(`NHTestNotAdmin`) == true;
		Owner = table.find(c.Owner or {}, P.UserId) ~= nil;
		Admin = table.find(c.Admin or {}, P.UserId) ~= nil;
		Tester = table.find(c.Testers or {}, P.UserId) ~= nil;
		Rank = if Studio then 0 else rankOf(P);
	})
end

-- a UserId's group rank without a Player (cached 10 min); nil when the lookup fails
local function rankOfId(UserId: number): number?
	if game.CreatorType ~= Enum.CreatorType.Group then return if UserId == game.CreatorId then 255 else 0 end
	local C = OfflineRank[UserId]
	if C and os.clock() - C.At < 600 then return C.R end
	local Ok, Groups = pcall(GroupService.GetGroupsAsync, GroupService, UserId)
	if not Ok then return nil end
	local R = 0
	for _, G in Groups do if G.Id == game.CreatorId then R = G.Rank end end
	OfflineRank[UserId] = { R = R; At = os.clock() }
	return R
end

-- the staff level of any UserId: their own level when they're here; else the lists and the group rank. A failed
-- lookup counts as the owner, so "no targeting up" fails closed.
function Shared.LevelOf(UserId: number): number
	local P = Players:GetPlayerByUserId(UserId)
	if P then return Shared.Level(P) end
	local Rank = rankOfId(UserId)
	if Rank == nil then return 3 end
	local c = cmdrCfg()
	return StaffConsole.LevelFrom({
		Studio = false;
		Owner = table.find(c.Owner or {}, UserId) ~= nil;
		Admin = table.find(c.Admin or {}, UserId) ~= nil;
		Tester = table.find(c.Testers or {}, UserId) ~= nil;
		Rank = Rank;
	})
end

function Shared.MutedUntil(UserId: number): number? return Muted[UserId] end

local function saved(Msg: string, Ok: boolean): string return `{Msg} · {StaffRecords.Status(Ok)}` end

local function log(Admin: Player, Command: string, Target: string?, Detail: string?)
	table.insert(Log, 1, { T = os.time(); Admin = Admin.Name; Command = Command; Target = Target or ``; Detail = Detail or `` })
	if #Log > LOG_MAX then table.remove(Log) end
	print(`[Admin] {Admin.Name}: {Command} {Target or ``} {Detail or ``}`)
end

local function notify(P: Player, Title: string, Text: string?, Kind: string?)
	local N = svc(`Features.Notifications`)
	if N then pcall(N.Notify, P, { Title = Title; Text = Text; Kind = Kind or `Info` }) end
end

local function char(P: Player)
	local C = P.Character
	local H = C and C:FindFirstChildWhichIsA(`Humanoid`)
	local R = C and C:FindFirstChild(`HumanoidRootPart`)
	return C, H, R
end

local function num(v, lo, hi, default)
	v = tonumber(v)
	if not v or v ~= v then return default end
	return math.clamp(v, lo, hi)
end

local function str(v, max)
	if typeof(v) ~= `string` then return `` end
	return v:sub(1, max or 200)
end

---------------------------------------------------------------- commands
-- each: { Target = true if it needs a player (Dispatch hands it in), Run = function(Admin, Target, Args) -> ok, msg }.
-- Level, Target mode (required / optional / none), Args and the rest of the card live in Admin.Meta; Dispatch checks the
-- level and Args (StaffConsole.CheckArgs) before it calls Run, and Run keeps the owner-only rules (rites, big Yen, bans).
local C = {}

-- moderation
C.Kick = { Target = true; Run = function(A, T, a)
	local reason = str(a.Reason, 120)
	T:Kick(`Removed by staff{if reason ~= `` then `: ` .. reason else ``}`)
	return true, `Kicked {T.Name}`
end }
C.Ban = { Target = true; Run = function(A, T, a)
	local days = num(a.Days, 0, 3650, 1)
	local lvl = Shared.Level(A)
	if days == 0 and lvl < 3 then return false, `Permanent bans are owner-only` end
	if days > 30 and lvl < 2 then return false, `Moderators can ban for up to 30 days` end
	local reason = str(a.Reason, 200)
	-- the record first: a kick ends T, the record only needs the UserId
	local Entry = { By = A.UserId; At = os.time(); Days = days; Reason = reason }
	local _, Saved = StaffRecords.Write(T.UserId, function(R) Records.Push(R, `Bans`, Entry) end)
	local Length = if days == 0 then `ever` else days .. ` day(s)`
	if Shared.TestSkipBanApi and RunService:IsStudio() then return true, saved(`Banned {T.Name} for {Length} (test: Ban API skipped)`, Saved) end
	local ok, err = pcall(Players.BanAsync, Players, {
		UserIds = { T.UserId }; ApplyToUniverse = true;
		Duration = if days == 0 then -1 else math.floor(days * 86400);
		DisplayReason = if reason ~= `` then reason else `Banned by staff`; PrivateReason = `By {A.Name} ({A.UserId})`;
	})
	if not ok then T:Kick(`Banned by staff: {reason}`) return true, saved(`Ban API unavailable here ({err}); kicked instead`, Saved) end
	return true, saved(`Banned {T.Name} for {Length}`, Saved)
end }
-- (1b) the latest ban not lifted decides who may lift it: permanent (or none on record, set before 1b) the owner;
-- over 30 days an admin; else a moderator
C.Unban = { Run = function(A, _, a)
	local id = tonumber(a.UserId)
	if not id then return false, `Enter a UserId` end
	local lvl = Shared.Level(A)
	if not StaffConsole.CanTarget(lvl, Shared.LevelOf(id), id == A.UserId) then return false, `Can't use that on a higher rank` end
	local Rec, Err = StaffRecords.Get(id, true)
	if not Rec then return false, `{Err}: try again` end
	local Ban = Records.OpenBan(Rec)
	local Need = Records.UnbanLevel(Ban)
	if lvl < Need then
		return false, if Need == 3 then `Permanent bans can only be lifted by the owner` else `A ban over 30 days needs an admin to lift`
	end
	if not (Shared.TestSkipBanApi and RunService:IsStudio()) then
		local ok, err = pcall(Players.UnbanAsync, Players, { UserIds = { id }; ApplyToUniverse = true })
		if not ok then return false, tostring(err) end
	end
	if not Ban then return true, `Unbanned {id} (no ban on record)` end
	local At, By, Now = Ban.At, Ban.By, os.time()
	local _, Saved = StaffRecords.Write(id, function(R)
		local I = Records.Find(R, `Bans`, At, By)
		if I then R.Bans[I].Lifted = { By = A.UserId; At = Now } end
	end)
	return true, saved(`Unbanned {id}`, Saved)
end }
C.Mute = { Target = true; Run = function(A, T, a)
	local Now = os.time()
	local Until = Records.MuteUntil(tonumber(a.Minutes) or 0, Now)
	Muted[T.UserId] = Until
	local reason = str(a.Reason, 120)
	local Entry = { By = A.UserId; At = Now; Until = Until; Reason = if reason ~= `` then reason else nil }
	local _, Saved = StaffRecords.Write(T.UserId, function(R) Records.Push(R, `Mutes`, Entry) end)
	local Label = Records.MuteLabel(Entry)
	notify(T, `You've been muted`, if Until == 0 then `Staff muted your chat` else `Staff muted your chat for {Label}`, `Warning`)
	return true, saved(`Muted {T.Name} ({Label})`, Saved)
end }
C.Unmute = { Target = true; Run = function(A, T)
	Muted[T.UserId] = nil
	local Now = os.time()
	local _, Saved = StaffRecords.Write(T.UserId, function(R)
		for _, M in R.Mutes do if Records.MuteOn(M, Now) then M.Lifted = { By = A.UserId; At = Now } end end
	end)
	notify(T, `Chat restored`, nil, `Good`)
	return true, saved(`Unmuted {T.Name}`, Saved)
end }
C.Warn = { Target = true; Run = function(A, T, a)
	local reason = str(a.Reason, 160)
	notify(T, `Warning from staff`, if reason ~= `` then reason else `Please follow the school rules`, `Bad`)
	local Entry = { By = A.UserId; At = os.time(); Reason = reason }
	local _, Saved = StaffRecords.Write(T.UserId, function(R) Records.Push(R, `Warnings`, Entry) end)
	return true, saved(`Warned {T.Name}`, Saved)
end }
C.Freeze = { Target = true; Run = function(A, T)
	local _, H, R = char(T)
	if not R then return false, `No character` end
	Frozen[T] = not Frozen[T]
	R.Anchored = Frozen[T] == true
	return true, (Frozen[T] and `Froze ` or `Unfroze `) .. T.Name
end }
C.Jail = { Target = true; Run = function(A, T)
	local D = svc(`School.Detention`)
	local Room = D and D.GetRoom and D.GetRoom()
	local Zone = Room and (Room:FindFirstChild(`Zone`) or Room:FindFirstChildWhichIsA(`BasePart`, true))
	local C0 = T.Character
	if not (Zone and C0) then return false, `No detention room found` end
	C0:PivotTo(Zone.CFrame + Vector3.new(0, 3, 0))
	notify(T, `Sent to detention`, `By staff`, `Warning`)
	return true, `Sent {T.Name} to detention`
end }

-- player
C.Heal = { Target = true; Run = function(A, T)
	local C0, H = char(T)
	if not H then return false, `No character` end
	H.Health = H.MaxHealth
	H:SetAttribute(`Posture`, 0)
	return true, `Healed {T.Name}`
end }
C.Revive = { Target = true; Run = function(A, T)
	local D = svc(`Features.Downed`)
	local C0, H = char(T)
	if not (D and C0) then return false, `No character` end
	pcall(D.Recover, C0)
	if H then H.Health = math.max(H.Health, H.MaxHealth * 0.5) end
	return true, `Revived {T.Name}`
end }
C.Kill = { Target = true; Run = function(A, T) local _, H = char(T) if not H then return false, `No character` end H.Health = 0 return true, `Killed {T.Name}` end }
C.God = { Target = true; Run = function(A, T)
	God[T] = not God[T] or nil
	local C0 = T.Character
	if C0 then C0:SetAttribute(`NoDowned`, God[T] and true or nil) C0:SetAttribute(`NHGod`, God[T] and true or nil) end
	return true, (God[T] and `God mode on for ` or `God mode off for `) .. T.Name
end }
-- (height, 1.63) a free re-roll of a student's height, or a place in their range (Config.Heights.Pick); the full game
-- saves it, the Map place keeps it for the session (each has its own Services.Player.Height)
C.SpinHeight = { Target = true; Run = function(A, T)
	local Hm = svc(`Player.Height`)
	if not (Hm and Hm.Spin) then return false, `No height system here` end
	local ok, r = Hm.Spin(T)
	if not ok then return false, tostring(r) end
	return true, `{T.Name} now stands {r}`
end }
-- (body types, 2026-11-10) set a student's build and step through Appearance.SetBuild (saved, keeps their gender)
C.SetBuild = { Target = true; Run = function(A, T, a)
	local App = require(ReplicatedStorage.UI.Appearance)
	if not App.SetBuild then return false, `No body types here` end
	local ok, r = App.SetBuild(T, a.Build, tonumber(a.Step) or 0)
	if not ok then return false, tostring(r) end
	return true, `{T.Name} is now {r}`
end }
C.SetHeight = { Target = true; Run = function(A, T, a)
	local Hm = svc(`Player.Height`)
	if not (Hm and Hm.Set) then return false, `No height system here` end
	local P = require(ReplicatedStorage.Config.Heights).Pick(a.Pick)
	if not P then return false, `Pick Shortest, Average or Tallest` end
	local ok, r = Hm.Set(T, P)
	if not ok then return false, tostring(r) end
	return true, `{T.Name} now stands {r}`
end }
-- (race, 1.65) set a student's race and variant, or force their tier (ReplicatedStorage.Lineage). The full game saves
-- it; the Map place keeps it for the session.
C.SetRace = { Target = true; Run = function(A, T, a)
	local L = require(ReplicatedStorage.Lineage)
	if not L.AdminSetRace then return false, `No race system here` end
	local ok, r = L.AdminSetRace(T, str(a.Sub, 24))
	if not ok then return false, tostring(r) end
	local S = L.SubById[r.SubRace]
	return true, `{T.Name} is now {S and S.Sub.Name or r.Race} ({r.Race}), Tier {({ `I`, `II`, `III` })[r.Tier] or r.Tier}`
end }
C.SetTier = { Target = true; Run = function(A, T, a)
	local L = require(ReplicatedStorage.Lineage)
	if not L.AdminSetTier then return false, `No race system here` end
	local ok, r = L.AdminSetTier(T, a.Tier)
	if not ok then return false, tostring(r) end
	return true, `{T.Name} is now Tier {({ `I`, `II`, `III` })[r.Tier]}, {L.TierName(r.Race, r.Tier)}`
end }
C.Speed = { Target = true; Run = function(A, T, a)
	local _, H = char(T)
	if not H then return false, `No character` end
	H.WalkSpeed = num(a.Value, 0, 120, 16)
	return true, `{T.Name} walk speed {H.WalkSpeed}`
end }
C.GiveYen = { Target = true; Run = function(A, T, a)
	local n = math.floor(num(a.Amount, -1e7, 1e7, 0))
	if math.abs(n) > 100000 and Shared.Level(A) < 3 then return false, `Over ¥100,000 needs an owner` end
	local Data = svc(`Player.Data`)
	if not Data then return false, `Data service missing` end
	-- (audit) taking more than they have used to save a negative balance
	local Profile = Data.GetProfile and Data.GetProfile(T)
	if Profile and n < 0 then n = math.max(n, -(Profile.Yen or 0)) end
	Data.UpdateState(T, { type = `UpdateYen`; amount = n })
	return true, `Gave ¥{n} to {T.Name}`
end }
C.GiveExp = { Target = true; Run = function(A, T, a)
	local n = math.floor(num(a.Amount, 0, 1e6, 0))
	local cat = str(a.Category, 20) ~= `` and str(a.Category, 20) or `Combat`
	local P = svc(`Player.Progression`)
	if not P then return false, `Progression missing` end
	local got = P.Award(T, n, cat, `Admin`)
	return true, `Gave {got or n} {cat} EXP to {T.Name}`
end }
C.GiveGear = { Target = true; Run = function(A, T, a)
	local G = svc(`Features.Gear`)
	local id = str(a.Id, 60)
	if not G or id == `` then return false, `Pick a gear id` end
	local new = G.Grant(T, id)
	return true, if new then `Gave {id} to {T.Name}` else `{T.Name} already owns {id}`
end }
C.GiveSpins = { Target = true; Run = function(A, T, a)
	local I = svc(`Player.Identity`)
	local n = math.floor(num(a.Amount, 1, 50, 1))
	if not I then return false, `Identity missing` end
	I.AddSpins(T, n)
	return true, `Gave {n} lineage spin(s) to {T.Name}`
end }
C.GiveNameChange = { Target = true; Run = function(A, T)
	local I = svc(`Player.Identity`)
	if not I then return false, `Identity missing` end
	I.AddNameChanges(T, 1)
	return true, `Gave a name change to {T.Name}`
end }
C.ClearDiscipline = { Target = true; Run = function(A, T)
	local D = svc(`School.Discipline`)
	if not D then return false, `Discipline missing` end
	D.Reduce(T, 1e6, `Cleared by staff`)
	return true, `Cleared {T.Name}'s record`
end }
C.Transform = { Target = true; Run = function(A, T)
	local Tr = svc(`Features.Transformation`)
	if not (Tr and T.Character) then return false, `No character` end
	Tr.Toggle(T.Character)
	return true, `Toggled {T.Name}'s transformation`
end }
-- (console 2) the form's direction: the game's own Look path (Lineage.SetLook saves it, sets RaceLooks, RaceCosmetics re-dresses)
C.FormDirection = { Target = true; Run = function(A, T, a)
	local Data = svc(`Player.Data`) -- (profile() is defined further down, so it isn't in scope here)
	if not (Data and Data.GetProfile(T)) then return false, `Their profile isn't loaded` end
	local Race = T:GetAttribute(`Race`)
	local Forms = require(ReplicatedStorage.Config.Forms)
	local R = Race and Forms.Races and Forms.Races[Race]
	if not (R and R.Directions) then return false, `{T.Name} has no form (no race form at Tier I)` end
	local Dir
	for _, D in R.Directions do if D.Id == a.Direction then Dir = D end end
	if not Dir then return false, `Their race has no direction {a.Direction}` end
	local Lin = require(ReplicatedStorage.Lineage)
	if not Lin.SetLook then return false, `Couldn't set their form direction` end
	local Ok, Why = Lin.SetLook(T, `FormDirection`, Dir.Id)
	if not Ok then return false, if typeof(Why) == `string` and Why ~= `` then Why else `Couldn't set their form direction` end
	return true, `Set {T.Name}'s form to {Dir.Name} (direction {Dir.Id})`
end }
C.Bring = { Target = true; Run = function(A, T)
	local _, _, R = char(A)
	if not (R and T.Character) then return false, `No character` end
	-- teleport veil (VFX P2-7); the student lands in the staff member's swirl of birds (Config.AdminTp)
	require(ServerScriptService.Services.Features.Fx).VeilMove(T, R.CFrame * CFrame.new(0, 0, -4), { By = A })
	return true, `Brought {T.Name}`
end }
C.Goto = { Target = true; Run = function(A, T)
	local _, _, R = char(T)
	if not (R and A.Character) then return false, `No character` end
	-- staff travel as their flock: crows, or the owner's bats (Features.Fx.TpStyle, Config.AdminTp)
	require(ServerScriptService.Services.Features.Fx).VeilMove(A, R.CFrame * CFrame.new(0, 0, 4), { Admin = true })
	return true, `Went to {T.Name}`
end }
C.Spectate = { Target = true; Run = function(A, T)
	ClientEvent:FireClient(A, `Spectate`, T)
	return true, `Spectating {T.Name}`
end }

-- world
C.SetTime = { Run = function(A, _, a)
	local SC = svc(`School.SchoolClock`)
	local t = str(a.Time, 5)
	if not (SC and t:match(`^%d%d?:%d%d$`)) then return false, `Use HH:MM` end
	SC.SetTime(t)
	return true, `Clock set to {t}`
end }
C.ClockSpeed = { Run = function(A, _, a)
	local SC = svc(`School.SchoolClock`)
	if not SC then return false, `Clock missing` end
	local v = num(a.Value, 2, 600, 60)
	SC.SetSpeed(v)
	return true, `One game hour = {v}s`
end }
C.Announce = { Run = function(A, _, a)
	local N = svc(`Features.Notifications`)
	local msg = str(a.Text, 200)
	if not N or msg == `` then return false, `Write a message` end
	N.NotifyAll({ Title = `Announcement`; Text = msg; Kind = `Warning`; Duration = 8 })
	return true, `Announced`
end }
-- (2.19.0) enemies come in front of you, on the floor there: the Map has no hangout or wolf spots, and a test
-- wants them close. They stay until killed or cleared ("Clear all enemies").
local function aheadFloor(R: BasePart, Dist: number): Vector3?
	local P = RaycastParams.new()
	P.FilterType = Enum.RaycastFilterType.Exclude
	P.FilterDescendantsInstances = { workspace:FindFirstChild(`Live`) or R.Parent }
	local From = (R.CFrame * CFrame.new(0, 0, -Dist)).Position
	local Hit = workspace:Raycast(From + Vector3.new(0, 8, 0), Vector3.new(0, -40, 0), P)
	return Hit and Hit.Position or nil
end
local ROLE_NAMES = { Grunt = `delinquent`; Brute = `delinquent brute`; Leader = `gang leader` }
C.SpawnDelinquents = { Run = function(A)
	local D = svc(`Features.Delinquents`)
	local _, _, R = char(A)
	if not (D and R) then return false, `Delinquents missing` end
	local At = D.CrewAt and aheadFloor(R, 16)
	if not At then D.Fill() return true, `A delinquent crew is on its way (out of sight)` end
	local n = D.CrewAt(At)
	return n > 0, `{n} delinquents ahead of you`
end }
C.SpawnDelinquent = { Run = function(A, _, a)
	local D = svc(`Features.Delinquents`)
	local _, _, R = char(A)
	if not (D and R and D.SpawnAt) then return false, `Delinquents missing` end
	local Role = typeof(a) == `table` and ROLE_NAMES[a.Role] and a.Role or `Grunt`
	local At = aheadFloor(R, 12)
	if not At then return false, `No floor ahead of you` end
	if not D.SpawnAt(Role, At) then return false, `Couldn't spawn a {ROLE_NAMES[Role]}` end
	return true, `A {ROLE_NAMES[Role]} is ahead of you`
end }
C.SpawnWolves = { Run = function(A)
	local W = svc(`Features.WildWolves`)
	local _, _, R = char(A)
	if not (W and R) then return false, `Wolves missing` end
	if not W.SpawnPack then W.Fill() return true, `Wolves called (night only)` end
	local At = aheadFloor(R, 18)
	if not At then return false, `No floor ahead of you` end
	local n = W.SpawnPack(At, 3)
	if n == 0 then return false, `No wolves came: the wolf model (ServerStorage.NHWolf) isn't in this place` end
	return true, `{n} wolves ahead of you (they stay until killed or cleared)`
end }
-- (beasts) one beast (Config.Beasts) 22 studs in front of you, facing you, any time of day; it stays until killed or cleared
C.SpawnBeast = { Run = function(A, _, a)
	local B = svc(`Features.Beasts`)
	local _, _, R = char(A)
	if not (B and R) then return false, `No character` end
	local name = str(a.Beast, 30)
	local M = B.SpawnAt(name, R.CFrame * CFrame.new(0, 0, -22) * CFrame.Angles(0, math.pi, 0))
	if not M then -- (2.19.0) say why: the beast rigs live in ServerStorage.NHBeasts
		if not game:GetService(`ServerStorage`):FindFirstChild(`NHBeasts`) then return false, `The beast rigs (ServerStorage.NHBeasts) aren't in this place` end
		return false, `No beast called {name}`
	end
	M:SetAttribute(`NHAdminSpawn`, true)
	return true, `A {M.Name} appeared ahead of you (it stays until killed or cleared)`
end }
C.SpawnSparring = { Run = function(A, _, a)
	local AI = svc(`AI.AI`)
	local _, _, R = char(A)
	if not (AI and R) then return false, `No character` end
	local NPCConfig = require(game:GetService(`ReplicatedStorage`).Config.NPC)
	local Tier = typeof(a) == `table` and NPCConfig.Tiers[a.Tier] and a.Tier or `Normal`
	local Settings = table.clone(NPCConfig.Default)
	Settings.Tier = Tier
	local npc = AI.Spawn(workspace:FindFirstChild(`Live`) or workspace, nil, nil, Settings)
	if npc and npc.Character then npc.Character:PivotTo(R.CFrame * CFrame.new(0, 0, -10)) end
	return true, `Spawned a {Tier} sparring partner`
end }
C.ClearEnemies = { Run = function(A)
	local n = 0
	for _, m in (workspace:FindFirstChild(`Live`) or workspace):GetChildren() do
		if m:IsA(`Model`) and not Players:GetPlayerFromCharacter(m) and (m:GetAttribute(`NHDelinquent`) or m.Name:match(`^NPC_`)) then m:Destroy() n += 1 end
	end
	local wolves = workspace:FindFirstChild(`Live`) and workspace.Live:FindFirstChild(`NHWolves`)
	if wolves then for _, w in wolves:GetChildren() do w:Destroy() n += 1 end end
	local B = svc(`Features.Beasts`) -- (beasts)
	if B then n += B.Clear() end
	return true, `Removed {n} enemies`
end }
C.Shutdown = { Run = function(A, _, a)
	local reason = str(a.Reason, 120)
	for _, P in Players:GetPlayers() do P:Kick(`Server closed by staff{if reason ~= `` then `: ` .. reason else ``}`) end
	return true, `Shutting down`
end }

-- self (quality of life). Flight, noclip, invisibility, ESP and click-teleport run on the admin's client;
-- these server parts keep the character state honest.
C.Invisible = { Run = function(A)
	local C0 = A.Character
	if not C0 then return false, `No character` end
	local on = not C0:GetAttribute(`NHInvisible`)
	C0:SetAttribute(`NHInvisible`, on or nil)
	for _, d in C0:GetDescendants() do
		-- (audit) each part's / decal's own Transparency is saved in NHAdminT when going invisible and put back from it
		if (d:IsA(`BasePart`) and d.Name ~= `HumanoidRootPart`) or d:IsA(`Decal`) then
			if d:IsA(`BasePart`) then d.LocalTransparencyModifier = 0 end
			if on then
				if d:GetAttribute(`NHAdminT`) == nil then d:SetAttribute(`NHAdminT`, d.Transparency) end
				d.Transparency = 1
			elseif d:GetAttribute(`NHAdminT`) ~= nil then
				d.Transparency = d:GetAttribute(`NHAdminT`)
				d:SetAttribute(`NHAdminT`, nil)
			end
		end
		-- (audit) face strips and name tags (SurfaceGuis / BillboardGuis) are switched off too, and back as they were
		if d:IsA(`SurfaceGui`) or d:IsA(`BillboardGui`) then
			if on then
				if d:GetAttribute(`NHAdminE`) == nil then d:SetAttribute(`NHAdminE`, d.Enabled) end
				d.Enabled = false
			elseif d:GetAttribute(`NHAdminE`) ~= nil then
				d.Enabled = d:GetAttribute(`NHAdminE`)
				d:SetAttribute(`NHAdminE`, nil)
			end
		end
	end
	return true, on and `You're invisible` or `You're visible`
end }
C.TeleportTo = { Run = function(A, _, a)
	local p = a.Position
	if typeof(p) ~= `Vector3` then return false, `No position` end
	-- (staff flocks) the full flock, or a quick puff when clicked again within Config.AdminTp.QuickWindow
	if A.Character then require(ServerScriptService.Services.Features.Fx).VeilMove(A, CFrame.new(p + Vector3.new(0, 3, 0)), { Admin = true; Quick = true }) end
	return true, `Teleported`
end }


---------------------------------------------------------------- 1.18: school, progression, activities, world, QOL
-- (the systems added since the desk shipped in 1.8)

local Locked = false                                   -- server lock: new non-staff joiners are turned away
local BELL = `rbxassetid://9113584435`

local function profile(T: Player)
	local Data = svc(`Player.Data`)
	return Data and Data.GetProfile(T), Data
end

local function today(): number
	local SC = svc(`School.SchoolClock`)
	local ok, s = pcall(function() return SC.GetState() end)
	return ok and s and s.Day or 0
end

-- set discipline points and let the ladder recompute (Discipline has no setter: put the points one above, then
-- Reduce by one, which runs its own Recompute: level, probation, suspension, attributes)
local function setPoints(T: Player, n: number)
	local D = svc(`School.Discipline`)
	local d = D and D.GetData(T)
	if not d then return nil end
	d.Points = math.max(0, math.floor(n)) + 1
	D.Reduce(T, 1, `Set by staff`)
	return d
end

local function segments()
	local ok, cfg = pcall(require, ReplicatedStorage.Config.SchoolSchedule)
	return ok and cfg.Segments or {}
end

-- the rooms that can hold a lesson: a timetable room whose subject has a minigame (Config.Activities.Subjects). R101 is
-- Homeroom, which has none. Activities.SubjectForRoom reads the same two tables.
local function lessonRooms(): { string }
	local Out = {}
	local ok = pcall(function()
		local Subjects = require(ReplicatedStorage.Config.Activities).Subjects
		for _, Class in require(ReplicatedStorage.Config.Classes).Periods do -- base (R103 also hosts Anatomy)
			if Subjects[Class.Subject] and not table.find(Out, Class.Room) then table.insert(Out, Class.Room) end
		end
		table.sort(Out)
	end)
	return if ok then Out else {}
end

local function regionBox(Id: string): BasePart?
	local F = workspace:FindFirstChild(`Regions`)
	-- (audit) boxes are found by their RegionId attribute (the Name as a fallback), like the client; with several
	-- boxes for one place, the biggest
	local Best, BestV = nil, -1
	for _, B in (F and F:GetChildren()) or {} do
		if B:IsA(`BasePart`) and (B:GetAttribute(`RegionId`) or B.Name) == Id then
			local V = B.Size.X * B.Size.Y * B.Size.Z
			if V > BestV then Best, BestV = B, V end
		end
	end
	return Best
end

-- school & discipline
C.SetDisciplinePoints = { Target = true; Run = function(A, T, a)
	local d = setPoints(T, num(a.Value, 0, 100, 0))
	if not d then return false, `No record loaded` end
	return true, `{T.Name}: {d.Points} points ({d.Level})`
end }
C.LiftSuspension = { Target = true; Run = function(A, T)
	local D = svc(`School.Discipline`)
	local d = D and D.GetData(T)
	if not d then return false, `No record loaded` end
	d.SuspendedUntilDay, d.ProbationUntilDay = -1, -1
	setPoints(T, math.min(d.Points, 9)) -- under Probation (10), so it doesn't come straight back
	return true, `Lifted {T.Name}'s suspension and probation ({d.Points} points, {d.Level})`
end }
C.ExcuseToday = { Target = true; Run = function(A, T)
	local Prof, Data = profile(T)
	local D = svc(`School.Discipline`)
	local d = D and D.GetData(T)
	if not (Prof and d) then return false, `No record loaded` end
	local Day, n, pts = today(), 0, 0
	local Att = Prof.Attendance
	if typeof(Att) == `table` and typeof(Att.Recent) == `table` then
		Att.Totals = Att.Totals or {}
		for _, r in Att.Recent do
			if r.Day == Day and (r.Status == `Absent` or r.Status == `Tardy` or r.Status == `LeftEarly`) then
				Att.Totals[r.Status] = math.max(0, (Att.Totals[r.Status] or 0) - 1)
				Att.Totals.Excused = (Att.Totals.Excused or 0) + 1
				r.Status = `Excused`
				n += 1
			end
		end
		Data.UpdateState(T, { type = `SetAttendance`; attendance = Att })
	end
	local keep = {}
	for _, r in d.Recent or {} do
		if r.Day == Day and (r.Type == `Absent` or r.Type == `Tardy` or r.Type == `LeftEarly`) then pts += r.Points or 0 else table.insert(keep, r) end
	end
	d.Recent = keep
	setPoints(T, d.Points - pts)
	return true, `Excused {n} class(es) today for {T.Name} (-{pts} points)`
end }
C.ClearDetention = { Target = true; Run = function(A, T)
	local D = svc(`School.Discipline`)
	local d = D and D.GetData(T)
	if not d then return false, `No record loaded` end
	d.DetentionsOwed = 0
	setPoints(T, d.Points)
	return true, `{T.Name} owes no detention`
end }
C.OweDetention = { Target = true; Run = function(A, T)
	local D = svc(`School.Discipline`)
	local d = D and D.GetData(T)
	if not d then return false, `No record loaded` end
	d.DetentionsOwed += 1
	setPoints(T, d.Points)
	notify(T, `Detention`, `Report to Room 106 outside class`, `Warning`)
	return true, `{T.Name} owes {d.DetentionsOwed} detention(s)`
end }
C.StartLesson = { Target = true; Run = function(A, T, a)
	local Room = str(a.Room, 8)
	local Act = svc(`School.Activities`)
	if not (Act and table.find(lessonRooms(), Room)) then return false, `Pick a classroom that has a lesson` end
	if Act.IsInActivity(T) then return false, `{T.Name} is in a lesson already` end
	local ok = Act.StartForTests(T, Room)
	if ok == true then return true, `Started a {Room} lesson for {T.Name}` end
	-- Activities only tells the player why (a notification), so the same checks, in the same order, give the reason here
	if T:GetAttribute(`Enrolled`) == false then return false, `{T.Name} isn't enrolled yet` end
	local SC = svc(`School.SchoolClock`)
	local Seg = SC and SC.GetState().Segment
	local Cls = Seg and Seg.Kind == `Class` and require(ReplicatedStorage.Config.Classes).For(Seg.Name, SC.GetState().Day, T) -- (Electives) their own class
	if not Cls or Cls.Room ~= Room then return false, `No class in {Room} right now{if Seg then ` (it's {Seg.Name})` else ``}: skip to its period first` end
	if T:GetAttribute(`ClassInRoom`) ~= true then return false, `{T.Name} isn't in {Room}: take them there first` end
	return false, `Couldn't start it ({T.Name} is downed, or a substitute's errand is on)`
end }
C.SkipToPeriod = { Run = function(A, _, a)
	local SC = svc(`School.SchoolClock`)
	local want = str(a.Segment, 30)
	local start
	for _, s in segments() do if s.Name == want then start = s.Start end end -- the last one wins (Night = 21:00, not 00:00)
	if not start then return false, `Unknown period` end
	-- always forward: today if it's still ahead, otherwise tomorrow
	local st = SC.GetState()
	local h, m = start:match(`^(%d+):(%d+)$`)
	local at = tonumber(h) * 60 + tonumber(m)
	local day = if at > (st.MinuteOfDay or 0) then st.Day else st.Day + 1
	SC.SetTime(start, day)
	return true, `Clock moved forward to {want} ({start}{if day ~= st.Day then `, tomorrow` else ``}). Students in school may be marked for skipped classes; Excuse today clears that.`
end }
C.RingBell = { Run = function(A)
	local S = Instance.new(`Sound`)
	S.SoundId = BELL
	S.Volume = 0.6
	S.Parent = workspace
	S:Play()
	task.delay(6, function() S:Destroy() end)
	return true, `The bell rings across the school`
end }

-- progression & data
C.SetLevel = { Target = true; Run = function(A, T, a)
	local Prog, Cfg = svc(`Player.Progression`), require(ReplicatedStorage.Config.Progression)
	local P = Prog and Prog.Get(T)
	local _, Data = profile(T)
	if not (P and Data) then return false, `No record loaded` end
	local lv = math.floor(num(a.Value, 1, Cfg.MaxLevel or 100, P.Level))
	P.Level = lv
	if not (Cfg.ToNext and P.Exp < Cfg.ToNext(lv)) then P.Exp = 0 end
	Data.UpdateState(T, { type = `SetProgress`; progress = P })
	T:SetAttribute(`Level`, lv)
	pcall(Prog.Apply, T)
	pcall(Prog.Notify, T)
	return true, `{T.Name} is now level {lv}`
end }
C.SetStatPoints = { Target = true; Run = function(A, T, a)
	local Prog = svc(`Player.Progression`)
	local P = Prog and Prog.Get(T)
	local _, Data = profile(T)
	if not (P and Data) then return false, `No record loaded` end
	P.Points = math.floor(num(a.Value, 0, 999, P.Points))
	Data.UpdateState(T, { type = `SetProgress`; progress = P })
	pcall(Prog.Notify, T)
	return true, `{T.Name} has {P.Points} stat point(s) to spend`
end }
C.GrantTitle = { Target = true; Run = function(A, T, a)
	local R = svc(`Social.Reputation`)
	local title = str(a.Title, 40)
	if not R or title == `` then return false, `Write a title` end
	local new = R.AwardTitle(T, title)
	return true, if new then `Gave {T.Name} the title {title}` else `{T.Name} already has {title}`
end }
C.RemoveTitle = { Target = true; Run = function(A, T, a)
	local R = svc(`Social.Reputation`)
	local s = R and R.Get(T)
	local title = str(a.Title, 40)
	if not s then return false, `No record loaded` end
	-- GrantTitle stores the filtered text, so match what was granted: the text as typed, or as the filter returns it
	local i = table.find(s.Titles, title)
	if not i then
		local okF, Out = pcall(function()
			return TextService:FilterStringAsync(title, A.UserId, Enum.TextFilterContext.PublicChat):GetNonChatStringForBroadcastAsync()
		end)
		if okF and typeof(Out) == `string` then
			i = table.find(s.Titles, Out)
			if i then title = Out end
		end
	end
	if not i then return false, `{T.Name} doesn't have {title}` end
	table.remove(s.Titles, i)
	if s.Title == title then s.Title = `` end
	R.Sync(T)
	return true, `Removed {title} from {T.Name}`
end }
C.RegionsAll = { Target = true; Run = function(A, T)
	local Rg = svc(`Features.Regions`)
	if not Rg then return false, `Regions missing` end
	local s = Rg.GrantAll(T)
	return true, `{T.Name} has found all {s.Total} places`
end }
C.RegionsReset = { Target = true; Run = function(A, T)
	local Rg = svc(`Features.Regions`)
	if not Rg then return false, `Regions missing` end
	Rg.Reset(T)
	return true, `{T.Name}'s places found were reset`
end }

-- sports, quests & world
C.MatchStart = { Target = true; Run = function(A, T, a)
	local M = svc(`Sports.Matches`)
	local v = str(a.Venue, 30)
	if not (M and M.Get(v)) then return false, `Unknown venue` end
	local ok, err = M.ForceStart(v, { T }, {}, true)
	return ok ~= false, if ok ~= false then `Started a match at the {v} for {T.Name} (solo test)` else tostring(err or `Couldn't start`)
end }
C.MatchEnd = { Run = function(A, _, a)
	local M = svc(`Sports.Matches`)
	local m = M and M.Get(str(a.Venue, 30))
	if not m then return false, `Unknown venue` end
	if m.Phase == `Waiting` or m.Phase == `Ended` then return false, `No match running there` end
	m:End(nil, `Ended by staff`)
	return true, `Ended the match at the {a.Venue}`
end }
C.SetClub = { Target = true; Run = function(A, T, a)
	local Cl = svc(`Sports.Clubs`)
	local id = str(a.Club, 20)
	if not Cl then return false, `Clubs missing` end
	-- "None" (the first choice in Lists.Clubs) takes them out of their club; CheckArgs never lets an empty value through
	if id == `None` or id == `` then Cl.Leave(T) return true, `{T.Name} left their club` end
	local ok, err = Cl.Join(T, id)
	return ok, if ok then `{T.Name} joined {id}` else tostring(err)
end }
C.QuestStart = { Target = true; Run = function(A, T, a)
	local Q = svc(`Quests.Quests`)
	local id = str(a.Id, 40)
	if not Q then return false, `Quests missing` end
	if id:match(`^Rite`) and Shared.Level(A) < 3 then return false, `Race rites are owner-only` end
	local ok = Q.Start(T, id)
	local why = Q.Status(T, id)
	return ok == true, if ok then `Started {id} for {T.Name}` else `Couldn't start {id}: {if why ~= `` then why else `done already, or not open to them yet`}`
end }
C.QuestAbandon = { Target = true; Run = function(A, T, a)
	local Q = svc(`Quests.Quests`)
	local id = str(a.Id, 40)
	if not Q then return false, `Quests missing` end
	local ok = Q.Abandon(T, id)
	return ok == true, if ok then `Dropped {id} for {T.Name}` else `{id} isn't active`
end }
C.QuestReset = { Target = true; Run = function(A, T)
	local Q = svc(`Quests.Quests`)
	if not Q then return false, `Quests missing` end
	Q.ResetForTests(T)
	return true, `Reset every quest for {T.Name}`
end }
C.FullMoon = { Run = function(A)
	local SC = svc(`School.SchoolClock`)
	local Lin = require(ReplicatedStorage.Lineage)
	local d = today()
	while d % (Lin.FullMoonEvery or 4) ~= 0 do d += 1 end
	SC.SetTime(`22:00`, d)
	return true, `Tonight is a full moon (day {d}, 22:00). Students in school may be marked for skipped classes.`
end }
-- Target "optional": Dispatch hands in the selected student (already through the no-targeting-up check); Send moves them
C.GotoRegion = { Run = function(A, T, a)
	local B = regionBox(str(a.Id, 30))
	if not B then return false, `Unknown place` end
	local Who = A
	if a.Send == true then
		Who = T
		if not Who then return false, `Pick a student first` end
	end
	-- the floor of the box (its bottom plus a little), at its centre
	local Pos = B.Position - Vector3.new(0, B.Size.Y / 2 - 3.5, 0)
	require(ServerScriptService.Services.Features.Fx).VeilMove(Who, CFrame.new(Pos), if Who == A then { Admin = true } else { By = A })
	return true, `{if Who == A then `You went` else Who.Name .. ` went`} to {B.Name}`
end }

-- QOL
C.BringAll = { Run = function(A)
	local _, _, R = char(A)
	if not R then return false, `No character` end
	local n = 0
	for i, P in Players:GetPlayers() do
		if P ~= A and Shared.Level(P) == 0 and P.Character and P:GetAttribute(`InMainMenu`) ~= true then
			local ang = i * 0.9
			require(ServerScriptService.Services.Features.Fx).VeilMove(P, R.CFrame * CFrame.new(math.cos(ang) * 6, 0, math.sin(ang) * 6 - 4), { By = A })
			n += 1
		end
	end
	return true, `Brought {n} student(s)`
end }
C.FreezeAll = { Run = function(A, _, a)
	local on = a.On ~= false
	local n = 0
	for _, P in Players:GetPlayers() do
		if Shared.Level(P) == 0 then
			local _, _, R = char(P)
			if R then Frozen[P] = on or nil R.Anchored = on n += 1 end
		end
	end
	return true, `{if on then `Froze` else `Thawed`} {n} student(s)`
end }
C.ServerLock = { Run = function(A)
	Locked = not Locked
	return true, if Locked then `Server locked: only staff can join` else `Server unlocked`
end }
C.Note = { Target = true; Run = function(A, T, a)
	local text = str(a.Text, 300)
	if text == `` then return false, `Note is needed` end
	local Entry = { By = A.UserId; At = os.time(); Text = text }
	local _, Saved = StaffRecords.Write(T.UserId, function(R) Records.Push(R, `Notes`, Entry) end)
	return true, saved(`Noted on {T.Name}`, Saved)
end }
-- (1b) owner-only (Meta Level 3), Danger; TargetId is the picked UserId, who may be offline. Removing a ban entry
-- doesn't unban: Unban stays the only way (it calls the Roblox ban API). Removing a mute entry that is still on does
-- lift the live mute, like Unmute: Muted is cleared, or set to the Until of another mute still on in their record (what
-- loadRecord would give on a rejoin). A mute that had already ended or been lifted changes nothing else. The result
-- message (the log's Detail) has the entry's text and the outcome.
C.RemoveRecordEntry = { Target = true; Run = function(A, T, a, TargetId)
	local Entry, Saved, Err = StaffRecords.RemoveEntry(TargetId, a.List, a.At, a.By)
	if not Entry then return false, Err end
	local Who = if T then T.Name else StaffRecords.NameOf(TargetId)
	local Text = `Removed from {Who}'s {string.lower(a.List)}: {Records.EntryText(a.List, Entry)}`
	local Now = os.time()
	if a.List == `Mutes` and Records.MuteOn(Entry, Now) then
		local Rec = StaffRecords.Cached(TargetId)
		local Other = Rec and Records.OpenMute(Rec, Now)
		if Other then
			if T then Muted[TargetId] = Other.Until end -- offline: nothing to set here; a rejoin's loadRecord applies it
			Text ..=`; still muted by another entry`
		else
			Muted[TargetId] = nil
			if T then notify(T, `Chat restored`, nil, `Good`) end
			Text ..= `; mute lifted`
		end
	end
	return true, saved(Text, Saved)
end }

-- the Inspect remote: admins and up only (the console offers Inspect at level 2, Tools.luau), and no targeting up
function Shared.InspectFor(P: Player, UserId: any)
	local lvl = Shared.Level(P)
	if lvl < 2 then return nil end
	local T = Players:GetPlayerByUserId(tonumber(UserId) or 0)
	if not T or not StaffConsole.CanTarget(lvl, Shared.Level(T), T == P) then return nil end
	local ok, r = pcall(Shared.Inspect, P, T)
	return ok and r or nil
end

-- read-only look at a student's loaded slot (Info's Inspect)
-- the newest saved note, for the inspector
local function latestNote(UserId: number)
	local R = StaffRecords.Cached(UserId)
	local N = R and R.Notes[#R.Notes]
	return if N then { Text = N.Text; By = StaffRecords.NameOf(N.By); T = N.At } else nil
end

function Shared.Inspect(Admin: Player, T: Player)
	local Prof = profile(T)
	if not Prof then return nil end
	local Prog = svc(`Player.Progression`)
	local P = Prog and Prog.Get(T) or {}
	local D = svc(`School.Discipline`)
	local d = D and D.GetData(T) or {}
	local Att = typeof(Prof.Attendance) == `table` and Prof.Attendance.Totals or {}
	local R = svc(`Social.Reputation`)
	local s = R and R.Get(T) or {}
	local Rg = svc(`Features.Regions`)
	local rs = Rg and Rg.State(T) or { Found = {}, Total = 0 }
	local Q = svc(`Quests.Quests`)
	local active = {}
	pcall(function()
		for _, id in require(ReplicatedStorage.Config.Quests).Order or {} do if Q.IsActive(T, id) then table.insert(active, id) end end
	end)
	if #active == 0 then
		pcall(function() for id in require(ReplicatedStorage.Config.Quests).Quests do if Q.IsActive(T, id) then table.insert(active, id) end end end)
	end
	local sports = typeof(Prof.Sports) == `table` and Prof.Sports or {}
	local arcade = typeof(Prof.Arcade) == `table` and Prof.Arcade.Best or {}
	local Nt = svc(`School.Notoriety`)
	local nt = {}
	if Nt then local Ok, R = pcall(Nt.Get, T) if Ok and typeof(R) == `table` then nt = R end end
	local Tu = svc(`World.Tutorial`)
	local Lin = typeof(Prof.Lineage) == `table` and Prof.Lineage or {}
	local Checkpoint = nil
	if Tu then local Ok, R = pcall(Tu.CheckpointOf, T) if Ok then Checkpoint = R end end
	return {
		Name = T.Name; UserId = T.UserId; Slot = T:GetAttribute(`Slot`); Race = T:GetAttribute(`SubRace`) or T:GetAttribute(`Race`);
		Yen = Prof.Yen or 0; Level = P.Level; Exp = P.Exp; Points = P.Points; Stats = P.Stats;
		Discipline = { Points = d.Points; Level = d.Level; Owed = d.DetentionsOwed; Suspended = d.SuspendedUntilDay; Probation = d.ProbationUntilDay };
		Attendance = Att; Titles = s.Titles or {}; Title = s.Title or ``;
		Regions = #rs.Found; RegionsTotal = rs.Total; Club = sports.Club or ``; Quests = active;
		Arcade = arcade; Kills = Prof.Kills or 0; Note = latestNote(T.UserId);
		Heat = nt.Heat; Bells = nt.Tier; BellState = nt.State; Summons = nt.Summons;
		FormDirection = typeof(Lin.Looks) == `table` and Lin.Looks.FormDirection or nil;
		Checkpoint = Checkpoint;
	}
end

---------------------------------------------------------------- (phase 2) group modules

-- Season, Moon tonight and Sky: Studio always (unless the Play check asks for the live rule); live, the owner only
function Shared.ServerWide(A: Player): (boolean, string?)
	local Studio = RunService:IsStudio() and not Shared.TestLiveMode
	return StaffConsole.ServerWideOk(Shared.Level(A), Studio)
end

local H = {
	svc = svc; str = str; profile = profile; today = today; Level = function(P) return Shared.Level(P) end;
	ServerWide = function(A) return Shared.ServerWide(A) end; notify = notify;
	Meta = function(Name: string, Kind: string, Extra: any?) local T = Extra or {} T.Name = Name T.Kind = Kind return T end;
}
Shared.GROUPS = { `World`, `Story`, `BellTower` }
for _, Name in Shared.GROUPS do
	local Mod = script:FindFirstChild(Name)
	if not Mod then warn(`[Admin] Admin.{Name} missing: its cards are not in the console`) continue end
	for Id, E in require(Mod)(H) do
		if C[Id] or Meta[Id] then error(`[Admin] Admin.{Name}: the id {Id} is already taken`) end
		C[Id] = { Run = E.Run }
		Meta[Id] = E.Meta
	end
end

-- the desk's pick lists (sent with Info)
local function buildLists()
	local L = { Quests = {}; Regions = {}; Clubs = {}; Venues = {}; Segments = {}; Beasts = {}; Races = {}; Gear = {}; Rooms = lessonRooms();
		Cutscenes = {}; Cases = {}; Clues = {}; Misdeeds = {} }
	pcall(function() -- (beasts) the Spawns tab's beast buttons
		for id, d in require(ReplicatedStorage.Config.Beasts).Defs do table.insert(L.Beasts, { Id = id; Name = d.Name or id }) end
		table.sort(L.Beasts, function(x, y) return x.Name < y.Name end)
	end)
	pcall(function()
		for id, q in require(ReplicatedStorage.Config.Quests).Quests do
			-- race rites are listed so the owner can pick one; QuestStart still refuses them below owner
			table.insert(L.Quests, { Id = id; Name = (if id:match(`^Rite`) then `Race rite: ` else ``) .. (q.Title or q.Name or id) })
		end
		table.sort(L.Quests, function(x, y) return x.Name < y.Name end)
	end)
	pcall(function()
		local R = require(ReplicatedStorage.Config.Regions)
		for _, id in R.Countable() do table.insert(L.Regions, { Id = id; Name = R.Defs[id].Name }) end
		table.sort(L.Regions, function(x, y) return x.Name < y.Name end)
	end)
	pcall(function()
		for id, c in require(ReplicatedStorage.Config.Sports).Clubs do table.insert(L.Clubs, { Id = id; Name = c.Name }) end
		table.sort(L.Clubs, function(x, y) return x.Name < y.Name end)
		table.insert(L.Clubs, 1, { Id = `None`; Name = `None (leave their club)` }) -- SetClub: take them out
	end)
	pcall(function()
		local M = svc(`Sports.Matches`)
		for name in M.All() do table.insert(L.Venues, name) end
		table.sort(L.Venues)
	end)
	for _, s in segments() do
		if not table.find(L.Segments, s.Name) then table.insert(L.Segments, s.Name) end
	end
	pcall(function() -- (console 1a) the Race card's choices: every sub-race
		for _, R in require(ReplicatedStorage.Lineage).Races do
			for _, S in R.Subs do table.insert(L.Races, { Id = S.Id; Name = S.Name }) end
		end
	end)
	pcall(function() -- (console 1a) the Give gear card's choices
		for _, it in require(ReplicatedStorage.Config.Gear).Items do table.insert(L.Gear, { Id = it.Id; Name = it.Name }) end
		table.sort(L.Gear, function(x, y) return x.Name < y.Name end)
	end)
	pcall(function() -- (console 2) Play a cutscene / Cutscene seen
		for id, c in require(ReplicatedStorage.Config.Cine).Cuts do
			if not c.Hidden then table.insert(L.Cutscenes, { Id = id; Name = c.Name or id }) end
		end
		table.sort(L.Cutscenes, function(x, y) return x.Name < y.Name end)
	end)
	pcall(function() -- (console 2) Give a clue / Reset a case
		for caseId, c in require(ReplicatedStorage.Config.Cases) do
			if typeof(c) == `table` then
				table.insert(L.Cases, { Id = caseId; Name = c.Name or caseId })
				for clueId, k in c.Clues or {} do
					table.insert(L.Clues, { Id = `{caseId}/{clueId}`; Name = `{c.Name or caseId}: {k.Name or clueId}`; Order = (c.Number or 0) * 100 + (k.Order or 0) })
				end
			end
		end
		table.sort(L.Cases, function(x, y) return x.Name < y.Name end)
		table.sort(L.Clues, function(x, y) return x.Order < y.Order end)
	end)
	pcall(function() -- (console 2) Give a summons: the misdeeds Admin.BellTower lists (Config.Notoriety.Heat keys)
		for id in require(ReplicatedStorage.Config.Notoriety).Heat do table.insert(L.Misdeeds, { Id = id; Name = id }) end
		table.sort(L.Misdeeds, function(x, y) return x.Name < y.Name end)
	end)
	return L
end

local ListsAt, ListsCache = -math.huge, nil
function Shared.Lists()
	if os.clock() - ListsAt > 10 or not ListsCache then ListsCache = buildLists() ListsAt = os.clock() end
	return ListsCache
end

function Shared.Locked(): boolean return Locked end

---------------------------------------------------------------- remotes

function Shared.Registry(Level: number)
	local Out = {}
	for Id, D in Meta do
		if D.Level <= Level then table.insert(Out, StaffConsole.Public(Id, D)) end
	end
	table.sort(Out, function(a, b) return a.Title < b.Title end)
	return Out
end

local function hasNote(UserId: number): boolean
	local R = StaffRecords.Cached(UserId)
	return R ~= nil and #R.Notes > 0
end

local function playerList()
	local list = {}
	local Q = svc(`Quests.Quests`)
	local Cn = svc(`World.Cine`)
	for _, P in Players:GetPlayers() do
		local C0, H = char(P)
		table.insert(list, {
			UserId = P.UserId; Name = P.Name; Display = P.DisplayName;
			Health = H and math.floor(H.Health) or 0; MaxHealth = H and math.floor(H.MaxHealth) or 0;
			Race = P:GetAttribute(`Race`) or (C0 and C0:GetAttribute(`Race`)) or `?`;
			Height = P:GetAttribute(`HeightText`); Sub = P:GetAttribute(`SubRace`); Tier = P:GetAttribute(`RaceTier`);
			Muted = Muted[P.UserId] ~= nil; God = God[P] == true; Frozen = Frozen[P] == true;
			Ping = math.floor((P:GetNetworkPing() or 0) * 1000); Level = Shared.Level(P);
			Note = hasNote(P.UserId); InMenu = P:GetAttribute(`InMainMenu`) == true;
			-- (console 2) the four new flags and the Bell Tower lines
			Transformed = C0 ~= nil and C0:GetAttribute(`Transformation`) ~= nil;
			Bells = P:GetAttribute(`NHBells`); BellState = P:GetAttribute(`NHBellState`); Summons = P:GetAttribute(`NHSummons`);
			InCutscene = P:GetAttribute(`NHTutorial`) == true or (Cn ~= nil and Cn.IsWatching(P) == true);
			New = Q ~= nil and (function() local Ok, S = pcall(Q.CineState, P) return Ok and typeof(S) == `table` and S.Prologue ~= `Seen` end)() or false;
		})
	end
	return list
end

local function serverInfo()
	local live = workspace:FindFirstChild(`Live`)
	local enemies, wolves = 0, 0
	if live then
		for _, m in live:GetChildren() do if m:GetAttribute(`NHDelinquent`) or m.Name:match(`^NPC_`) then enemies += 1 end end
		local w = live:FindFirstChild(`NHWolves`) if w then wolves = #w:GetChildren() end
	end
	local BS = svc(`Features.Beasts`) -- (beasts)
	local beasts = BS and BS.Count() or 0
	local SC = svc(`School.SchoolClock`)
	local clock = SC and SC.GetState and select(2, pcall(SC.GetState)) or nil
	return {
		Players = #Players:GetPlayers(); MaxPlayers = Players.MaxPlayers; Uptime = os.time() - StartedAt;
		Fps = math.floor(workspace:GetRealPhysicsFPS()); Memory = math.floor(Stats:GetTotalMemoryUsageMb());
		Enemies = enemies; Wolves = wolves; Beasts = beasts; JobId = game.JobId ~= `` and game.JobId or `Studio`;
		Clock = type(clock) == `table` and (`{clock.DayName or ``} {clock.ClockText or ``}`) or nil;
	}
end

local function snapshot(Admin: Player)
	local lvl = Shared.Level(Admin)
	local gear = {}
	pcall(function() for _, it in require(ReplicatedStorage.Config.Gear).Items do table.insert(gear, { Id = it.Id; Name = it.Name; Rarity = it.Rarity }) end end)
	return {
		Level = lvl; Players = playerList(); Log = Log; Gear = gear; Lists = Shared.Lists(); Locked = Locked; Server = serverInfo();
		Registry = Shared.Registry(lvl); Sections = StaffConsole.SECTIONS;
	}
end

-- returns ok, message, and the target's name and UserId for the log
local function dispatch(P: Player, lvl: number, Command: any, TargetUserId: any, Args: any): (any, any, string?, number?)
	local def = typeof(Command) == `string` and C[Command] or nil
	local m = def and Meta[Command]
	if not m then return false, `Unknown command` end
	if m.Level > lvl then return false, `Needs {StaffConsole.LEVEL_NAMES[m.Level]}` end
	local okA, clean = StaffConsole.CheckArgs(m.Args, Args, Shared.Lists())
	if not okA then return false, clean end
	Args = clean
	-- (2026-11-17, Roblox text rules) text staff type that other players see (kick / ban / warn / shutdown reasons,
	-- announcements, staff notes, granted titles, the action log) goes through Roblox's filter first, as the
	-- sender's broadcast text. If the filter can't answer, the command doesn't run: unfiltered text is never sent.
	for _, K in { `Reason`, `Text`, if Command == `GrantTitle` then `Title` else nil } do
		local Raw = Args[K]
		if typeof(Raw) == `string` and Raw:match(`%S`) then
			local OkF, Out = pcall(function()
				return TextService:FilterStringAsync(Raw:sub(1, 300), P.UserId, Enum.TextFilterContext.PublicChat):GetNonChatStringForBroadcastAsync()
			end)
			if not OkF or typeof(Out) ~= `string` then return false, `The text filter is busy: try again in a moment` end
			Args[K] = Out
		end
	end
	local T, TargetId
	if m.Target == `user` then
		TargetId = tonumber(TargetUserId)
		if not TargetId then return false, `Pick a student first` end
		T = Players:GetPlayerByUserId(TargetId)
		if not StaffConsole.CanTarget(lvl, Shared.LevelOf(TargetId), TargetId == P.UserId) then
			return false, `Can't use that on a higher rank`, StaffRecords.NameOf(TargetId), TargetId
		end
	elseif m.Target ~= `none` then
		T = Players:GetPlayerByUserId(tonumber(TargetUserId) or 0)
		if not T and m.Target == `required` then return false, `Pick a player first` end
		if T and not StaffConsole.CanTarget(lvl, Shared.Level(T), T == P) then return false, `Can't use that on a higher rank`, T.Name, T.UserId end
		TargetId = T and T.UserId
	elseif Command == `Unban` then
		TargetId = tonumber(Args.UserId)
	end
	local TName = if T then T.Name elseif TargetId then StaffRecords.NameOf(TargetId) else nil
	local ok, a, b = pcall(def.Run, P, T, Args, TargetId)
	if not ok then warn(`[Admin] {Command} failed: {a}`) return false, `Failed: {tostring(a):sub(1, 120)}`, TName, TargetId end
	log(P, Command, T and T.Name, typeof(Args.Reason) == `string` and Args.Reason or (Args.Amount and tostring(Args.Amount)) or nil)
	return a, b, TName, TargetId
end

function Shared.Dispatch(P: Player, Command: any, TargetUserId: any, Args: any)
	local lvl = Shared.Level(P)
	if lvl < 1 then return false, `Not staff` end
	if os.clock() - (LastRun[P] or 0) < 0.15 then return false, `Slow down` end
	LastRun[P] = os.clock()
	local a, b, TName, TargetId = dispatch(P, lvl, Command, TargetUserId, Args)
	-- (1b) the saved log: every call past the two checks above, run or refused (Features.StaffRecords buffers it)
	local m = typeof(Command) == `string` and Meta[Command] or nil
	StaffRecords.LogAdd({
		At = os.time(); Staff = P.Name; StaffId = P.UserId; Action = if typeof(Command) == `string` then Command else `?`;
		Target = TName; TargetId = TargetId; Detail = tostring(b or ``); Side = m and m.Side; Ok = a == true;
	})
	return a, b
end

function Shared.OnStart()
	for Id in C do if not Meta[Id] then warn(`[Admin] {Id} has no Admin.Meta entry: the console can't show it`) end end
	for Id, D in Meta do
		if not C[Id] then warn(`[Admin] Admin.Meta {Id} has no command`) end
		local Ok, Why = StaffConsole.Validate(Id, D)
		if not Ok then warn(`[Admin] Admin.Meta {Why}`) end
	end
	Folder = Instance.new(`Folder`)
	Folder.Name = `NHAdmin`
	-- (1.71) NHStaff = this player's staff level (0 none, 1 moderator, 2 admin, 3 owner): the admin clothing kit reads it (UI.Appearance, >= 1)
	local function markStaff(P: Player)
		local function set()
			task.spawn(function()
				local ok, lvl = pcall(Shared.Level, P)
				if P.Parent then P:SetAttribute(`NHStaff`, ok and lvl or 0) end
			end)
		end
		set()
		if RunService:IsStudio() then
			P:GetAttributeChangedSignal(`NHTestLevel`):Connect(set)
			P:GetAttributeChangedSignal(`NHTestNotAdmin`):Connect(set)
		end
	end
	Players.PlayerAdded:Connect(markStaff)
	for _, P in Players:GetPlayers() do markStaff(P) end
	local Info = Instance.new(`RemoteFunction`); Info.Name = `Info`; Info.Parent = Folder
	local Run = Instance.new(`RemoteFunction`); Run.Name = `Run`; Run.Parent = Folder
	ClientEvent = Instance.new(`RemoteEvent`); ClientEvent.Name = `Client`; ClientEvent.Parent = Folder
	local InspectRF = Instance.new(`RemoteFunction`); InspectRF.Name = `Inspect`; InspectRF.Parent = Folder
	local StatusRF = Instance.new(`RemoteFunction`); StatusRF.Name = `Status`; StatusRF.Parent = Folder
	StatusRF.OnServerInvoke = function(P: Player)
		if Shared.Level(P) < 1 then return nil end
		return { Server = serverInfo(); Players = playerList(); Locked = Locked }
	end
	-- (1b) record, log and prefs remotes: level 1, checked here
	-- at most 8 reads a second per player: the console makes short bursts (a log row opens its history, the Unban card
	-- checks a record while the log loads), so a flat gap between calls would refuse real use
	local Reads = {} :: { [Player]: { number } }
	local function slow(P: Player): boolean
		local Now = os.clock()
		local L = Reads[P] or {}
		while L[1] and Now - L[1] > 1 do table.remove(L, 1) end
		Reads[P] = L
		if #L >= 8 then return true end
		table.insert(L, Now)
		return false
	end
	-- a copy of the record with ByName on every entry and every Lifted (the client shows names, not UserIds)
	local function withNames(Rec: any): any
		local Out = Records.Blank()
		for _, List in Records.LISTS do
			for _, E in Rec[List] do
				local Copy = table.clone(E)
				Copy.ByName = StaffRecords.NameOf(E.By)
				if typeof(E.Lifted) == `table` then Copy.Lifted = table.clone(E.Lifted) Copy.Lifted.ByName = StaffRecords.NameOf(E.Lifted.By) end
				table.insert(Out[List], Copy)
			end
		end
		return Out
	end
	local HistoryRF = Instance.new(`RemoteFunction`); HistoryRF.Name = `History`; HistoryRF.Parent = Folder
	HistoryRF.OnServerInvoke = function(P: Player, UserId: any)
		local lvl = Shared.Level(P)
		if lvl < 1 then return nil end
		if slow(P) then return { Ok = false; Error = `Slow down` } end
		local Id = tonumber(UserId)
		if not Id or Id ~= math.floor(Id) then return { Ok = false; Error = `Bad UserId` } end
		if not StaffConsole.CanTarget(lvl, Shared.LevelOf(Id), Id == P.UserId) then return { Ok = false; Error = `Can't view a higher rank's history` } end
		local Rec, Err = StaffRecords.Get(Id)
		if not Rec then return { Ok = false; Error = Err } end
		return { Ok = true; UserId = Id; Name = StaffRecords.NameOf(Id); Record = withNames(Rec) }
	end
	local LogRF = Instance.new(`RemoteFunction`); LogRF.Name = `LogDay`; LogRF.Parent = Folder
	LogRF.OnServerInvoke = function(P: Player, Offset: any, Filter: any)
		if Shared.Level(P) < 1 then return nil end
		if slow(P) then return { Ok = false; Error = `Slow down` } end
		local R, Err = StaffRecords.LogDay(Offset, Filter)
		if not R then return { Ok = false; Error = Err } end
		R.Ok = true
		return R
	end
	local PrefsRF = Instance.new(`RemoteFunction`); PrefsRF.Name = `Prefs`; PrefsRF.Parent = Folder
	PrefsRF.OnServerInvoke = function(P: Player)
		if Shared.Level(P) < 1 then return nil end
		local R, Err = StaffRecords.PrefsGet(P.UserId)
		if not R then return { Ok = false; Error = Err } end
		R.Ok = true
		return R
	end
	local SavePrefsRF = Instance.new(`RemoteFunction`); SavePrefsRF.Name = `SavePrefs`; SavePrefsRF.Parent = Folder
	SavePrefsRF.OnServerInvoke = function(P: Player, Favs: any, Side: any)
		if Shared.Level(P) < 1 then return false end
		StaffRecords.PrefsSet(P.UserId, Favs, Side)
		return true
	end
	InspectRF.OnServerInvoke = Shared.InspectFor
	Folder.Parent = ReplicatedStorage

	Info.OnServerInvoke = function(P: Player)
		if Shared.Level(P) < 1 then return nil end
		return snapshot(P)
	end
	Run.OnServerInvoke = Shared.Dispatch
	Folder:SetAttribute(`Ready`, true)

	-- mute: one gate on every channel
	local function hook(ch: Instance)
		if ch:IsA(`TextChannel`) then
			ch.ShouldDeliverCallback = function(msg)
				local src = msg.TextSource
				return not (src and Muted[src.UserId] ~= nil)
			end
		end
	end
	task.defer(function()
		local chans = TextChatService:WaitForChild(`TextChannels`, 20)
		if chans then for _, ch in chans:GetChildren() do hook(ch) end chans.ChildAdded:Connect(hook) end
	end)

	-- god mode: topped up every frame, never downed
	RunService.Heartbeat:Connect(function()
		for P in God do
			local C0, H = char(P)
			if H and H.Health > 0 and H.Health < H.MaxHealth then H.Health = H.MaxHealth end
			if C0 and C0:GetAttribute(`Downed`) then local D = svc(`Features.Downed`) if D then pcall(D.Recover, C0) end end
		end
	end)
	-- (1b) timed mutes end on time while they're here
	task.spawn(function()
		while true do
			task.wait(1)
			local Now = os.time()
			for Id, Until in Muted do
				if Until ~= 0 and Until <= Now then
					Muted[Id] = nil
					local P = Players:GetPlayerByUserId(Id)
					if P then notify(P, `Chat restored`, `Your mute has ended`, `Good`) end
				end
			end
		end
	end)
	Players.PlayerRemoving:Connect(function(P) God[P] = nil Frozen[P] = nil RankCache[P] = nil LastRun[P] = nil Reads[P] = nil Muted[P.UserId] = nil end)
	-- (1b) an open mute on their saved record is applied again when they join (and the record stays cached for the
	-- NOTE / MUTED row flags). A failed read leaves them unmuted for this visit (spec delta 7).
	local function loadRecord(P: Player)
		local Rec, Err = StaffRecords.Get(P.UserId, true)
		if not Rec then warn(`[Admin] record read for {P.Name} failed ({Err}): an open mute isn't applied this visit`) return end
		local M = Records.OpenMute(Rec, os.time())
		if M and P.Parent then Muted[P.UserId] = M.Until end
	end
	for _, P in Players:GetPlayers() do task.spawn(loadRecord, P) end
	Players.PlayerAdded:Connect(function(P)
		task.spawn(loadRecord, P)
		-- server lock (QOL): staff only while it's on
		if Locked then task.defer(function() if Shared.Level(P) == 0 then P:Kick(`This server is locked by staff for now. Try another server.`) end end) end
		P.CharacterAdded:Connect(function(C0)
			if God[P] then C0:SetAttribute(`NoDowned`, true) C0:SetAttribute(`NHGod`, true) end
			Frozen[P] = nil -- (audit) a respawn isn't frozen, so the panel shouldn't say it is
		end)
	end)
end

return Shared
