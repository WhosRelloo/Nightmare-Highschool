--[[
	Superlatives (server). Services.Social.Superlatives   (1.39, the Midnight Bell's weekly awards)

	A school week is five event days (Monday 6 AM to the next Monday 6 AM; Week = floor(EventDay / 5)), about ten
	real hours. Each student (each save slot) counts six things that week, saved in PlayerData.Social.Weekly
	{ Week, Counts }:
	  Pranks      pranks pulled (Quests.Progress `Prank`)              -> Class Clown
	  Riots       scuffles and rumbles won, with a down (`Scuffle`)     -> Most Likely to Start a Riot
	  Takedowns   takedowns (Features.KillTracker)                       -> Most Feared
	  Detentions  detentions earned (School.Discipline)                  -> Most Likely to Be Expelled
	  Classes     classes attended with a B or better (School.Attendance) -> Teacher's Pet
	  Power       dares and member jobs done, showdowns won              -> Most Likely to Run the School
	The game runs on many servers, so each server writes its students' counts every minute to an OrderedDataStore
	per award per week ("NHSup_<Id>", scope = the week; key "<UserId>_<Slot>"), and their first name and race to
	"NHSupNames". The top student of each award with at least MIN wins. In Studio the stores are prefixed "[Test] ".

	The week after, each winner wears the award's title (Social.Reputation AwardTitle) for that week only:
	PlayerData.Social.TempTitles = { [title] = last week it's worn }; it's taken off when that week ends. A title the
	student already owned for good is left alone. The Midnight Bell (Features.Phone Gazette) prints last week's
	winners on Monday's front page and this week's leaders the rest of the week; the notice board shows both.

	API: Count(P, Id, N?), Week(), Board() -> { Week, Last = { {Id, Title, What, First, Race, Value} }, Leaders = {...} },
	Defs. Tests: FlushForTests(), FetchForTests(Week), AwardForTests(P) (this week's leaders as if last week's), State(P).
]]
local DataStoreService = game:GetService(`DataStoreService`)
local Players = game:GetService(`Players`)
local RunService = game:GetService(`RunService`)
local ServerScriptService = game:GetService(`ServerScriptService`)

local Shared = {}
local Local = {}

Shared.Defs = {
	{ Id = `Pranks`; Title = `Class Clown`; What = `pranks pulled` };
	{ Id = `Riots`; Title = `Most Likely to Start a Riot`; What = `scuffles and rumbles won` };
	{ Id = `Takedowns`; Title = `Most Feared`; What = `takedowns` };
	{ Id = `Detentions`; Title = `Most Likely to Be Expelled`; What = `detentions earned` };
	{ Id = `Classes`; Title = `Teacher's Pet`; What = `classes with a B or better` };
	{ Id = `Power`; Title = `Most Likely to Run the School`; What = `dares, jobs and showdowns` };
}
local ById = {}
for _, D in Shared.Defs do ById[D.Id] = D end
local MIN = 3                 -- the least that wins an award
local FLUSH_EVERY = 60        -- seconds between store writes
local LEADERS_EVERY = 300     -- seconds between reads of this week's leaders
local PREFIX = if RunService:IsStudio() then `[Test] ` else ``

local Dirty = {} :: { [Player]: { [string]: boolean } }
local Named = {} :: { [Player]: number } -- the week this student's name was last written
local Results = {} :: { [number]: { At: number, Winners: { [string]: any } } }
local Granted = {} :: { [Player]: number } -- the week we last checked this student for a title
local Settling = false -- (audit) the week just rolled over and last week's winners aren't read yet

local function svc(Path: string)
	local Node = ServerScriptService.Services
	for Part in Path:gmatch(`[^%.]+`) do Node = Node:FindFirstChild(Part) if not Node then return nil end end
	local Ok, Mod = pcall(require, Node)
	return Ok and Mod or nil
end

---| the week |---

function Shared.Week(): number?
	local Clock = svc(`School.SchoolClock`)
	local Ok, S = pcall(function() return Clock.GetState() end)
	if not (Ok and S and S.Day) then return nil end
	local Hour = S.Hour or ((S.MinuteOfDay or 720) / 60)
	local EventDay = if Hour >= 6 then S.Day else S.Day - 1
	return math.floor(EventDay / 5)
end

function Local.Key(P: Player): string?
	local Data = svc(`Player.Data`)
	local Slot = Data and Data.GetSlot(P)
	return Slot and `{P.UserId}_{Slot}` or nil
end

-- this student's weekly record (reset when the week changes); nil without a loaded slot
function Local.Weekly(P: Player)
	local Rep = svc(`Social.Reputation`)
	local Social = Rep and Rep.Get(P)
	local W = Shared.Week()
	if not (Social and W) then return nil end
	local R = Social.Weekly
	if typeof(R) ~= `table` or R.Week ~= W or typeof(R.Counts) ~= `table` then
		-- (audit) the week changed with counts not yet written: write them to the old week's store first (they were lost)
		local D = Dirty[P]
		if D and typeof(R) == `table` and typeof(R.Week) == `number` and typeof(R.Counts) == `table` then
			Dirty[P] = nil
			task.spawn(Local.FlushOld, P, R, D)
		end
		R = { Week = W; Counts = {} }
		Social.Weekly = R
	end
	return R, Social
end

---| counting |---

function Shared.Count(P: Player, Id: string, N: number?)
	if not ById[Id] or typeof(P) ~= `Instance` or not P:IsA(`Player`) then return end
	local R = Local.Weekly(P)
	if not R then return end
	R.Counts[Id] = (R.Counts[Id] or 0) + (N or 1)
	Dirty[P] = Dirty[P] or {}
	Dirty[P][Id] = true
	local Rep = svc(`Social.Reputation`)
	if Rep and Rep.Sync then Rep.Sync(P) end
end

function Local.Store(Id: string, Week: number)
	return DataStoreService:GetOrderedDataStore(`{PREFIX}NHSup_{Id}`, tostring(Week))
end
function Local.Names()
	return DataStoreService:GetDataStore(`{PREFIX}NHSupNames`)
end

function Local.Flush(P: Player)
	if not Dirty[P] then return end
	-- (audit) read the record first: if the week just changed, Weekly hands the old week's counts to FlushOld
	local R = Local.Weekly(P)
	local D = Dirty[P]
	if not D then return end
	Dirty[P] = nil
	local Key = Local.Key(P)
	if not (R and Key) then return end
	for Id in D do
		local V = R.Counts[Id] or 0
		local Ok, Err = pcall(function() Local.Store(Id, R.Week):SetAsync(Key, V) end)
		if not Ok then warn(`[Superlatives] write {Id}: {Err}`) Dirty[P] = Dirty[P] or {} Dirty[P][Id] = true end
	end
	if Named[P] ~= R.Week then
		local Identity = svc(`Player.Identity`)
		local I = Identity and Identity.Get(P)
		local First = I and typeof(I.First) == `string` and I.First ~= `` and I.First or P.DisplayName
		local Ok = pcall(function() Local.Names():SetAsync(Key, { First = First; Race = P:GetAttribute(`Race`) or `Human` }) end)
		if Ok then Named[P] = R.Week end
	end
end

-- (audit) write a finished week's unsaved counts to that week's store
function Local.FlushOld(P: Player, R, D)
	local Key = Local.Key(P)
	if not Key then return end
	for Id in D do
		local Ok, Err = pcall(function() Local.Store(Id, R.Week):SetAsync(Key, R.Counts[Id] or 0) end)
		if not Ok then warn(`[Superlatives] write {Id} (week {R.Week}): {Err}`) end
	end
end

---| results |---

-- read each award's top student for a week (yields; cached)
function Local.Fetch(Week: number)
	local Winners = {}
	local Failed = false
	for _, D in Shared.Defs do
		local Ok, Page = pcall(function() return Local.Store(D.Id, Week):GetSortedAsync(false, 1):GetCurrentPage() end)
		if not Ok then Failed = true warn(`[Superlatives] read {D.Id}: {Page}`) end
		local Top = Ok and Page and Page[1]
		if Top and Top.value >= MIN then
			local Ok2, Info = pcall(function() return Local.Names():GetAsync(Top.key) end)
			Info = if Ok2 and typeof(Info) == `table` then Info else {}
			Winners[D.Id] = { Key = Top.key; Value = Top.value; First = Info.First or `A student`; Race = Info.Race }
		end
	end
	Results[Week] = { At = os.clock(); Winners = Winners; Failed = Failed }
	return Results[Week]
end

function Local.List(Week: number?)
	local R = Week and Results[Week]
	if not R then return {} end
	local Out = {}
	for _, D in Shared.Defs do
		local Wn = R.Winners[D.Id]
		if Wn then table.insert(Out, { Id = D.Id; Title = D.Title; What = D.What; First = Wn.First; Race = Wn.Race; Value = Wn.Value; Key = Wn.Key }) end
	end
	return Out
end

-- what the paper and the board show (cached only, never yields)
function Shared.Board()
	local W = Shared.Week()
	return { Week = W; Last = Local.List(W and W - 1); Leaders = Local.List(W); Min = MIN }
end

---| week-long titles |---

function Local.Expire(P: Player)
	local Rep = svc(`Social.Reputation`)
	local Social = Rep and Rep.Get(P)
	local W = Shared.Week()
	if not (Social and W) or typeof(Social.TempTitles) ~= `table` then return end
	local Changed = false
	for Title, Until in Social.TempTitles do
		if typeof(Until) ~= `number` or Until < W then
			local I = table.find(Social.Titles, Title)
			if I then table.remove(Social.Titles, I) end
			if Social.Title == Title then Social.Title = `` end
			Social.TempTitles[Title] = nil
			Changed = true
		end
	end
	if Changed then Rep.Sync(P) end
end

-- give P the titles they won in Winners, worn through week Until
function Local.Grant(P: Player, Winners: { [string]: any }, Until: number)
	local Rep = svc(`Social.Reputation`)
	local Social = Rep and Rep.Get(P)
	local Key = Local.Key(P)
	if not (Social and Key) then return end
	Social.TempTitles = if typeof(Social.TempTitles) == `table` then Social.TempTitles else {}
	for Id, Wn in Winners do
		local D = ById[Id]
		if D and Wn.Key == Key then
			local Owned = table.find(Social.Titles, D.Title) ~= nil
			if Owned and not Social.TempTitles[D.Title] then continue end -- already theirs for good
			if Social.TempTitles[D.Title] ~= Until then -- (2.31) a superlative won (counted once per award and week)
				pcall(function() require(game:GetService(`ServerScriptService`).Services.Player.Paths).Count(P, `Superlatives`) end)
			end
			Social.TempTitles[D.Title] = Until
			if not Owned then Rep.AwardTitle(P, D.Title) end
			local N = svc(`Features.Notifications`)
			if N then pcall(N.Notify, P, { Title = `The Midnight Bell: {D.Title}`; Text = `{Wn.Value} {D.What} last week. The title is yours until next Monday.`; Kind = `Milestone`; Duration = 8 }) end
		end
	end
	Rep.Sync(P)
end

function Local.Check(P: Player)
	local W = Shared.Week()
	if not W or Settling then return end -- (audit) not until last week's winners are read (the loop checks everyone then)
	Local.Expire(P)
	local Last = Results[W - 1]
	if Last and Granted[P] ~= W then
		Granted[P] = W
		Local.Grant(P, Last.Winners, W)
	end
end

---| tests |---

function Shared.FlushForTests()
	for P in table.clone(Dirty) do Local.Flush(P) end
	return true
end
function Shared.FetchForTests(Week: number?)
	local W = Week or Shared.Week()
	if not W then return {} end
	Local.Fetch(W)
	return Local.List(W)
end
function Shared.AwardForTests(P: Player)
	local W = Shared.Week()
	local R = W and Local.Fetch(W)
	if not R then return false end
	Local.Grant(P, R.Winners, W)
	return true
end
function Shared.State(P: Player)
	local R, Social = Local.Weekly(P)
	return { Weekly = R; TempTitles = Social and Social.TempTitles; Titles = Social and Social.Titles; Title = Social and Social.Title; Key = Local.Key(P); Board = Shared.Board() }
end

---| start |---

function Shared.OnStart()
	local Data = svc(`Player.Data`)
	if Data and Data.ProfileLoaded then
		Data.ProfileLoaded:Connect(function(P) task.delay(2, function() if P.Parent then pcall(Local.Check, P) end end) end)
	end
	Players.PlayerRemoving:Connect(function(P)
		pcall(Local.Flush, P)
		Dirty[P] = nil Named[P] = nil Granted[P] = nil
	end)
	game:BindToClose(function()
		for P in table.clone(Dirty) do pcall(Local.Flush, P) end
	end)
	-- writes every minute; last week's winners once a week (retried until read); this week's leaders every 5 min
	task.spawn(function()
		local LastFlush, LastLeaders, LastWeek = 0, -math.huge, nil
		local RolledAt = nil -- (audit) when this server saw the week change
		while true do
			task.wait(15)
			local Now = os.clock()
			if Now - LastFlush >= FLUSH_EVERY then
				LastFlush = Now
				for P in table.clone(Dirty) do pcall(Local.Flush, P) end
			end
			local W = Shared.Week()
			if W then
				local Prev = Results[W - 1]
				-- (audit) the week just rolled over: give the other servers' last writes of the old week (every minute) a few
				-- minutes to land before reading its winners, which are then kept for the whole week
				if LastWeek and W ~= LastWeek and not RolledAt then RolledAt = Now Settling = true end
				local Waiting = RolledAt ~= nil and Now - RolledAt < 150
				if not Waiting and (not Prev or W ~= LastWeek or (Prev.Failed and Now - Prev.At >= LEADERS_EVERY)) then
					RolledAt = nil
					Settling = false
					LastWeek = W
					pcall(Local.Fetch, W - 1)
					for _, P in Players:GetPlayers() do pcall(Local.Check, P) end
				end
				if Now - LastLeaders >= LEADERS_EVERY then
					LastLeaders = Now
					pcall(Local.Fetch, W)
				end
			end
		end
	end)
end

return Shared
