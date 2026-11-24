--[[
	StaffRecords (server): the console's saved records, the saved staff log and saved favourites
	(spec docs/superpowers/specs/2026-11-23-admin-console-1b-design.md §2-§4). The rules are in Functions.StaffRecords.
	Stores (Studio adds the prefix "[Test] "):
	  NHStaffRecords_v1  u_<UserId>                    a player's record
	  NHStaffLog_v1      day_<n>_<Job> / day_<n>        this server's Moderate entries for day n / the servers that wrote it
	                     test_day_<n>_<Job> / test_day_<n>   the same for Test actions (removed after 7 days)
	  NHStaffPrefs_v1    u_<UserId>                    { Favs, Side }
	Records are written straight away (3 tries). A failed write waits in Pending: it shows in the console's copy, goes
	with the next write for that player and is retried every 30 s. The log is buffered and saved every 30 s and on
	close (a crash can lose up to 30 s of it). Prefs are saved 5 s after the last change and on leave.
	Features.Admin calls it. checks/records_store.lua tests it in Edit against fake stores (SetStoresForTest).
]]
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local DataStoreService = game:GetService("DataStoreService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Rules = require(ReplicatedStorage:WaitForChild("Functions"):WaitForChild("StaffRecords"))

local Shared = {}
Shared.PREFIX = if RunService:IsStudio() then "[Test] " else ""
Shared.BACKOFF = { 1, 2 }
Shared.CACHE_S = 60
Shared.PREFS_DELAY = 5
Shared.Clock = function(): number return os.time() end

local Stores = {} :: { [string]: any }
local Override = nil :: ((string) -> any)?
local Cache = {} :: { [number]: { Rec: any, At: number, Partial: boolean? } }
local Pending = {} :: { [number]: { (any) -> () } }
local Busy = {} :: { [number]: boolean }
local Buffer = {} :: { any }
local InFlight = {} :: { [string]: { any } } -- log key -> entries a running FlushLog is still writing
local FlushBusy = false
local Indexed = {} :: { [string]: boolean }
local Swept = {} :: { [number]: boolean }
local DayCache = {} :: { [number]: { Lists: { { any } }, At: number } }
local Prefs = {} :: { [number]: { Favs: { string }, Side: string?, At: number } }
local Names = {} :: { [number]: string }

function Shared.SetStoresForTest(Get: (string) -> any)
	Override = Get
	Stores = {}
end

local function store(Name: string): any
	if Override then return Override(Name) end
	Stores[Name] = Stores[Name] or DataStoreService:GetDataStore(Shared.PREFIX .. Name)
	return Stores[Name]
end

-- 3 tries, waiting BACKOFF[1] then BACKOFF[2] between them
local function tries(Fn: () -> any): (boolean, any)
	for I = 1, 3 do
		local Ok, A = pcall(Fn)
		if Ok then return true, A end
		if I < 3 then task.wait(Shared.BACKOFF[I] or 0) end
	end
	return false, nil
end

local function key(UserId: number): string return `u_{UserId}` end

function Shared.JobKey(): string
	-- Studio (Edit and Play) has a JobId of its own, but the spec keeps Studio on one key: day_<n>_studio
	return if RunService:IsStudio() or game.JobId == "" then "studio" else game.JobId
end

function Shared.Status(Saved: boolean): string
	return if Saved then "Saved" else "Saved later (DataStore busy)"
end

---------------------------------------------------------------- records
function Shared.Cached(UserId: number): any
	local C = Cache[UserId]
	return C and C.Rec
end

function Shared.Get(UserId: number, Fresh: boolean?): (any, string?)
	local C = Cache[UserId]
	if C and not C.Partial and not Fresh and os.clock() - C.At < Shared.CACHE_S then return C.Rec end
	local S = store("NHStaffRecords_v1")
	local Ok, V = tries(function() return S:GetAsync(key(UserId)) end)
	if not Ok then return nil, "History unavailable" end
	local Rec = Rules.Normalize(V)
	for _, M in Pending[UserId] or {} do M(Rec) end -- writes still waiting show already
	Cache[UserId] = { Rec = Rec; At = os.clock() }
	return Rec
end

-- Mutate changes a record in place and must be pure: UpdateAsync may call it more than once. One write per player at
-- a time, so a waiting write is never applied twice.
function Shared.Write(UserId: number, Mutate: (any) -> ()): (any, boolean)
	while Busy[UserId] do task.wait() end
	Busy[UserId] = true
	local Queue = Pending[UserId] or {}
	table.insert(Queue, Mutate)
	Pending[UserId] = Queue
	local S = store("NHStaffRecords_v1")
	local Ok, V = tries(function()
		return S:UpdateAsync(key(UserId), function(Old)
			local Rec = Rules.Normalize(Old)
			for _, M in Queue do M(Rec) end
			return Rec
		end)
	end)
	local Out
	if Ok then
		Pending[UserId] = nil
		Cache[UserId] = { Rec = Rules.Normalize(V); At = os.clock() }
		Out = Cache[UserId].Rec
	else
		local C = Cache[UserId]
		if C then
			Mutate(C.Rec)
		else
			local Rec = Rules.Blank()
			for _, M in Queue do M(Rec) end
			Cache[UserId] = { Rec = Rec; At = os.clock(); Partial = true } -- Get reads the store again before trusting it
		end
		Out = Cache[UserId].Rec
	end
	Busy[UserId] = nil
	return Out, Ok
end

function Shared.RetryPending()
	local Ids = {}
	for Id in Pending do table.insert(Ids, Id) end
	for _, Id in Ids do
		if Pending[Id] then Shared.Write(Id, function() end) end
	end
end

function Shared.RemoveEntry(UserId: number, List: string, At: number, By: number): (any, boolean?, string?)
	local Rec, Err = Shared.Get(UserId, true)
	if not Rec then return nil, nil, Err end
	local I = Rules.Find(Rec, List, At, By)
	if not I then return nil, nil, "No such entry" end
	local Entry = Rec[List][I]
	local _, Saved = Shared.Write(UserId, function(R) Rules.Remove(R, List, At, By) end)
	return Entry, Saved
end

---------------------------------------------------------------- the saved log
function Shared.LogAdd(F: any)
	table.insert(Buffer, Rules.LogEntry(F))
	if #Buffer > Rules.LOG_CAP then Buffer = Rules.CapLog(Buffer) end
end

-- the first Test write on a day removes day n-7's Test keys and their index (best effort)
local function sweepTest(Day: number)
	if Swept[Day] then return end
	Swept[Day] = true
	local S = store("NHStaffLog_v1")
	local Old = Rules.TestCutoff(Day)
	local Ok, Jobs = pcall(function() return S:GetAsync(Rules.IndexKey(Old, true)) end)
	if not Ok then warn(`[StaffRecords] Test log clean-up of day {Old} failed: {Jobs}`) return end
	for _, Job in (if typeof(Jobs) == "table" then Jobs else {}) do
		local Ok2, Err = pcall(function() S:RemoveAsync(Rules.LogKey(Old, Job, true)) end)
		if not Ok2 then warn(`[StaffRecords] Test log clean-up of {Job} on day {Old} failed: {Err}`) end
	end
	local Ok3, Err3 = pcall(function() S:RemoveAsync(Rules.IndexKey(Old, true)) end)
	if not Ok3 then warn(`[StaffRecords] Test log index clean-up of day {Old} failed: {Err3}`) end
end

-- one flush at a time: a second call waits for the running one, then saves what's left, so "FlushLog() then read"
-- always finds every entry logged before the call. Entries being written stay readable (InFlight) until their key saves.
-- The index first (a reader treats a listed key that doesn't exist yet as empty), then the entries.
local function flushBatch(Batch: { any }, Failed: { any }): boolean
	local Job = Shared.JobKey()
	local Groups, Order = {}, {}
	for _, E in Batch do
		local Day, Test = Rules.Day(E.At), E.Side == "Test"
		local K = Rules.LogKey(Day, Job, Test)
		if not Groups[K] then Groups[K] = { Day = Day; Test = Test; Entries = {} } table.insert(Order, K) end
		table.insert(Groups[K].Entries, E)
	end
	for _, K in Order do InFlight[K] = Groups[K].Entries end
	local S = store("NHStaffLog_v1")
	local AllOk = true
	for _, K in Order do
		local G = Groups[K]
		if G.Test then sweepTest(G.Day) end
		local IK = Rules.IndexKey(G.Day, G.Test)
		local Ok = Indexed[IK] == true
		if not Ok then
			Ok = (tries(function()
				return S:UpdateAsync(IK, function(Old)
					local L = if typeof(Old) == "table" then Old else {}
					if not table.find(L, Job) then table.insert(L, Job) end
					return L
				end)
			end))
			if Ok then Indexed[IK] = true end
		end
		if Ok then
			Ok = (tries(function()
				return S:UpdateAsync(K, function(Old)
					local L = if typeof(Old) == "table" then Old else {}
					for _, E in G.Entries do table.insert(L, E) end
					return Rules.CapLog(L)
				end)
			end))
		end
		if Ok then
			DayCache[G.Day] = nil
		else
			AllOk = false
			for _, E in G.Entries do table.insert(Failed, E) end
		end
		InFlight[K] = nil
	end
	return AllOk
end

function Shared.FlushLog(): boolean
	while FlushBusy do task.wait() end
	if #Buffer == 0 then return true end
	FlushBusy = true
	local Batch, Failed = Buffer, {}
	Buffer = {}
	local Ran, AllOk = pcall(flushBatch, Batch, Failed)
	if not Ran then
		warn(`[StaffRecords] log save failed: {AllOk}`)
		Failed, AllOk = Batch, false -- a key saved before the error may get these again: a repeat beats a loss
	end
	table.clear(InFlight)
	-- the failed ones go back in front of anything logged meanwhile
	local Since = Buffer
	Buffer = Failed
	for _, E in Since do table.insert(Buffer, E) end
	if #Buffer > Rules.LOG_CAP then Buffer = Rules.CapLog(Buffer) end
	FlushBusy = false
	return AllOk
end

local function readDay(Day: number): ({ { any } }?, string?)
	local C = DayCache[Day]
	if C and os.clock() - C.At < Shared.CACHE_S then return C.Lists end
	local S = store("NHStaffLog_v1")
	local Lists = {}
	for _, Test in { false, true } do
		local Ok, Jobs = tries(function() return S:GetAsync(Rules.IndexKey(Day, Test)) end)
		if not Ok then return nil, "Log unavailable" end
		for _, Job in (if typeof(Jobs) == "table" then Jobs else {}) do
			local Ok2, L = tries(function() return S:GetAsync(Rules.LogKey(Day, Job, Test)) end)
			if not Ok2 then return nil, "Log unavailable" end
			if typeof(L) == "table" then table.insert(Lists, L) end
		end
	end
	DayCache[Day] = { Lists = Lists; At = os.clock() }
	return Lists
end

-- Offset 0 = today .. 6; Filter = { Query?, Chip? ("All"|"Moderate"|"Test"|"Refused"), Page? }. This server's unsaved
-- entries for that day are included, so an action shows before the next save.
function Shared.LogDay(Offset: any, Filter: any): (any, string?)
	local Off = tonumber(Offset)
	if not Off or Off ~= math.floor(Off) or Off < 0 or Off > 6 then return nil, "Pick a day this week" end
	local Day = Rules.Day(Shared.Clock()) - Off
	local Saved, Err = readDay(Day)
	if not Saved then return nil, Err end
	local Mine = {}
	for _, L in InFlight do for _, E in L do if Rules.Day(E.At) == Day then table.insert(Mine, E) end end end
	for _, E in Buffer do if Rules.Day(E.At) == Day then table.insert(Mine, E) end end
	local Lists = table.clone(Saved)
	table.insert(Lists, Mine)
	local All = Rules.MergeDay(Lists)
	local F = if typeof(Filter) == "table" then Filter else {}
	local Query = if typeof(F.Query) == "string" then string.sub(F.Query, 1, 60) else ""
	local Chip = if F.Chip == "Moderate" or F.Chip == "Test" or F.Chip == "Refused" then F.Chip else "All"
	local Hits = {}
	for _, E in All do if Rules.LogMatch(E, Query, Chip) then table.insert(Hits, E) end end
	local Rows, Page, Pages = Rules.Page(Hits, F.Page, 50)
	return { Day = Day; Rows = Rows; Total = #Hits; Page = Page; Pages = Pages }
end

---------------------------------------------------------------- saved favourites and last side
function Shared.PrefsGet(UserId: number): (any, string?)
	local Mine = Prefs[UserId]
	if Mine then return { Favs = table.clone(Mine.Favs); Side = Mine.Side } end
	local S = store("NHStaffPrefs_v1")
	local Ok, V = tries(function() return S:GetAsync(key(UserId)) end)
	if not Ok then return nil, "Favourites unavailable" end
	local T = if typeof(V) == "table" then V else {}
	return { Favs = Rules.CleanFavs(T.Favs, nil); Side = Rules.CleanSide(T.Side) }
end

function Shared.PrefsSet(UserId: number, Favs: any, Side: any)
	Prefs[UserId] = { Favs = Rules.CleanFavs(Favs, nil); Side = Rules.CleanSide(Side); At = os.clock() }
end

-- no args: the ones untouched for PREFS_DELAY s (the 1 s loop); UserId: that one now; All: every one now (on close)
function Shared.PrefsFlush(UserId: number?, All: boolean?)
	local S = store("NHStaffPrefs_v1")
	local Ids = {}
	for Id in Prefs do table.insert(Ids, Id) end
	for _, Id in Ids do
		local P = Prefs[Id]
		if not P then continue end
		if UserId ~= nil and Id ~= UserId then continue end
		if UserId == nil and not All and os.clock() - P.At < Shared.PREFS_DELAY then continue end
		local Ok = tries(function() return S:SetAsync(key(Id), { Favs = P.Favs; Side = P.Side }) end)
		if Ok and Prefs[Id] == P then Prefs[Id] = nil end
	end
end

---------------------------------------------------------------- names
function Shared.NameOf(UserId: number): string
	local P = Players:GetPlayerByUserId(UserId)
	if P then return P.Name end
	if Names[UserId] then return Names[UserId] end
	local Ok, N = pcall(Players.GetNameFromUserIdAsync, Players, UserId)
	if Ok and typeof(N) == "string" then Names[UserId] = N return N end
	return tostring(UserId)
end

function Shared.OnStart()
	task.spawn(function()
		while true do
			task.wait(30)
			pcall(Shared.FlushLog)
			pcall(Shared.RetryPending)
		end
	end)
	task.spawn(function()
		while true do
			task.wait(1)
			pcall(Shared.PrefsFlush)
		end
	end)
	Players.PlayerRemoving:Connect(function(P) task.spawn(Shared.PrefsFlush, P.UserId) end)
	game:BindToClose(function()
		local Left = 3
		for _, Fn in { Shared.FlushLog, function() Shared.PrefsFlush(nil, true) end, Shared.RetryPending } do
			task.spawn(function() pcall(Fn) Left -= 1 end)
		end
		local T0 = os.clock()
		while Left > 0 and os.clock() - T0 < 25 do task.wait(0.1) end
	end)
end

return Shared
