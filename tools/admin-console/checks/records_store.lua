-- Edit: Features.StaffRecords against fake DataStores (no real store is touched). Values are copied in and out, as
-- real stores serialize them; Fail = N makes the next N calls on that store error.
local Mod = game.ServerScriptService.Services.Features:FindFirstChild("StaffRecords")
if not Mod then return "FAIL Features.StaffRecords missing" end
local SR = require(Mod:Clone())
local Rules = require(game.ReplicatedStorage.Functions.StaffRecords)
local Fails = {}
local function Eq(Got, Want, What) if Got ~= Want then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end
local function deep(V) if typeof(V) ~= "table" then return V end local O = {} for K, X in V do O[K] = deep(X) end return O end
local Fakes = {}
local function fake(Name)
	if Fakes[Name] then return Fakes[Name] end
	local S = { Data = {}; Fail = 0 }
	local function gate() if S.Fail > 0 then S.Fail -= 1 error("DataStore busy (fake)") end end
	function S:GetAsync(K) gate() return deep(S.Data[K]) end
	function S:SetAsync(K, V) gate() S.Data[K] = deep(V) end
	function S:RemoveAsync(K) gate() local V = S.Data[K] S.Data[K] = nil return V end
	function S:UpdateAsync(K, Fn) gate() if S.Slow then task.wait(S.Slow) end local V = Fn(deep(S.Data[K])) if V ~= nil then S.Data[K] = deep(V) end return deep(S.Data[K]) end
	Fakes[Name] = S
	return S
end
SR.SetStoresForTest(fake)
SR.BACKOFF = { 0, 0 }
SR.CACHE_S = 0
SR.PREFS_DELAY = 0
local Day = 20000
SR.Clock = function() return Day * 86400 + 3600 end
local Rec, Log, Prefs = fake("NHStaffRecords_v1"), fake("NHStaffLog_v1"), fake("NHStaffPrefs_v1")

-- 1. a write lands and reads back
local R1, S1 = SR.Write(1, function(R) Rules.Push(R, "Warnings", { By = 9; At = 100; Reason = "a" }) end)
Eq(S1, true, "write saved") Eq(R1 and #R1.Warnings, 1, "write returns the record")
Eq(Rec.Data.u_1 and #Rec.Data.u_1.Warnings, 1, "the store has it")
local G1 = SR.Get(1, true)
Eq(G1 and #G1.Warnings, 1, "read back")
Eq(SR.Status(true), "Saved", "status saved") Eq(SR.Status(false), "Saved later (DataStore busy)", "status later")

-- 2. two failed tries, then the third lands
Rec.Fail = 2
local _, S2 = SR.Write(1, function(R) Rules.Push(R, "Notes", { By = 9; At = 101; Text = "n" }) end)
Eq(S2, true, "saved on the third try")

-- 3. three failures: pending, shown already, retried once
Rec.Fail = 3
local R3, S3 = SR.Write(1, function(R) Rules.Push(R, "Warnings", { By = 9; At = 102; Reason = "b" }) end)
Eq(S3, false, "a busy write is not saved") Eq(R3 and #R3.Warnings, 2, "but shows in the console's copy")
Eq(#Rec.Data.u_1.Warnings, 1, "the store is unchanged")
local G3 = SR.Get(1, true)
Eq(G3 and #G3.Warnings, 2, "a fresh read still shows the waiting write")
SR.RetryPending()
Eq(#Rec.Data.u_1.Warnings, 2, "the retry saved it")
SR.RetryPending()
Eq(#Rec.Data.u_1.Warnings, 2, "and only once")

-- 3b. a waiting write goes with the next write for that player
Rec.Fail = 3
SR.Write(1, function(R) Rules.Push(R, "Warnings", { By = 9; At = 103; Reason = "c" }) end)
SR.Write(1, function(R) Rules.Push(R, "Warnings", { By = 9; At = 104; Reason = "d" }) end)
Eq(#Rec.Data.u_1.Warnings, 4, "the next write carried the waiting one")

-- 4. a failed read is an error, never an empty history
Rec.Fail = 3
local G4, E4 = SR.Get(1, true)
Eq(G4, nil, "a failed read gives no record") Eq(E4, "History unavailable", "failed read message")

-- 5. the cap of 50 through writes
for I = 1, 51 do SR.Write(2, function(R) Rules.Push(R, "Warnings", { By = 9; At = I; Reason = "w" }) end) end
Eq(#Rec.Data.u_2.Warnings, 50, "cap 50 in the store") Eq(Rec.Data.u_2.Warnings[1].At, 2, "the oldest dropped")

-- 6. removing one entry
local Gone, S6 = SR.RemoveEntry(1, "Warnings", 102, 9)
Eq(Gone and Gone.Reason, "b", "removed the matching entry") Eq(S6, true, "the removal saved")
Eq(#Rec.Data.u_1.Warnings, 3, "three left")
local Miss, _, E6 = SR.RemoveEntry(1, "Warnings", 999, 9)
Eq(Miss, nil, "no such entry") Eq(E6, "No such entry", "missing entry message")

-- 7. the log: buffered, flushed into this server's keys with an index, read back newest first, filtered
local T = Day * 86400 + 100
SR.LogAdd({ At = T; Staff = "mod"; StaffId = 9; Action = "Warn"; Target = "kid"; TargetId = 1; Detail = "Warned kid"; Side = "Moderate"; Ok = true })
SR.LogAdd({ At = T + 1; Staff = "mod"; StaffId = 9; Action = "Ban"; Target = "kid"; TargetId = 1; Detail = "Permanent bans are owner-only"; Side = "Moderate"; Ok = false })
SR.LogAdd({ At = T + 2; Staff = "mod"; StaffId = 9; Action = "Heal"; Detail = "Healed"; Side = "Test"; Ok = true })
local D0 = SR.LogDay(0, {})
Eq(D0 and D0.Total, 3, "unsaved entries show already")
Eq(SR.FlushLog(), true, "flush ok")
Eq(#(Log.Data[`day_{Day}_studio`] or {}), 2, "the Moderate key has 2")
Eq(#(Log.Data[`test_day_{Day}_studio`] or {}), 1, "the Test key has 1")
Eq(table.find(Log.Data[`day_{Day}`] or {}, "studio") ~= nil, true, "the index has this server")
Eq(table.find(Log.Data[`test_day_{Day}`] or {}, "studio") ~= nil, true, "the Test index has this server")
local D1 = SR.LogDay(0, {})
Eq(D1 and D1.Total, 3, "read back 3") Eq(D1 and D1.Rows[1].Action, "Heal", "newest first")
Eq(SR.LogDay(0, { Chip = "Refused" }).Total, 1, "refused chip") Eq(SR.LogDay(0, { Chip = "Test" }).Total, 1, "test chip")
Eq(SR.LogDay(0, { Query = "KID" }).Total, 2, "search by target name")
Eq(SR.LogDay(1, {}).Total, 0, "an empty day is empty, not an error")
Eq(SR.LogDay(7, {}), nil, "only this week")

-- 8. the cap of 2000 per key
local Old = {}
for I = 1, 1999 do Old[I] = { At = T - 5000 + I; Staff = "x"; Action = "Old"; Detail = ""; Side = "Moderate"; Ok = true } end
Log.Data[`day_{Day}_studio`] = Old
for I = 1, 5 do SR.LogAdd({ At = T + 10 + I; Staff = "mod"; Action = "New"; Side = "Moderate"; Ok = true }) end
SR.FlushLog()
local K = Log.Data[`day_{Day}_studio`]
Eq(#K, 2000, "the key is capped at 2000") Eq(K[1] and K[1].At, T - 5000 + 5, "the oldest dropped") Eq(K[2000] and K[2000].Action, "New", "the newest kept")

-- 9. a failed flush keeps its entries for the next one
Log.Fail = 3
SR.LogAdd({ At = T + 50; Staff = "mod"; Action = "Kept"; Side = "Moderate"; Ok = true })
Eq(SR.FlushLog(), false, "a busy flush says so")
Eq(SR.LogDay(0, { Query = "Kept" }).Total, 1, "the kept entry still shows")
Eq(SR.FlushLog(), true, "the next flush is ok")
local Found = false
for _, E in Log.Data[`day_{Day}_studio`] do if E.Action == "Kept" then Found = true end end
Eq(Found, true, "the kept entry was saved")

-- 10. a failed day read is an error, never an empty day
Log.Fail = 3
local D10, E10 = SR.LogDay(0, {})
Eq(D10, nil, "a failed day read gives nothing") Eq(E10, "Log unavailable", "failed day message")
Log.Fail = 0

-- 11. the first Test write on day n removes day n-7's Test keys and index; Moderate keys stay
local N1 = Day + 1
SR.Clock = function() return N1 * 86400 + 60 end
Log.Data[`test_day_{N1 - 7}`] = { "jobA" }
Log.Data[`test_day_{N1 - 7}_jobA`] = { { At = (N1 - 7) * 86400; Action = "OldTest"; Side = "Test"; Ok = true } }
Log.Data[`day_{N1 - 7}_jobA`] = { { At = (N1 - 7) * 86400; Action = "OldModerate"; Side = "Moderate"; Ok = true } }
SR.LogAdd({ At = N1 * 86400 + 10; Staff = "mod"; Action = "Heal"; Side = "Test"; Ok = true })
SR.FlushLog()
Eq(Log.Data[`test_day_{N1 - 7}_jobA`], nil, "the old Test key removed")
Eq(Log.Data[`test_day_{N1 - 7}`], nil, "the old Test index removed")
Eq(Log.Data[`day_{N1 - 7}_jobA`] ~= nil, true, "Moderate keys are kept")

-- 12. prefs: kept in memory, saved after the delay (0 here), cleaned on the way in and out
SR.PrefsSet(9, { "Warn", 5, "Warn" }, "Test")
local P1 = SR.PrefsGet(9)
Eq(P1 and #P1.Favs, 1, "prefs cleaned on set") Eq(P1 and P1.Side, "Test", "side kept")
SR.PrefsFlush()
Eq(Prefs.Data.u_9 and Prefs.Data.u_9.Side, "Test", "prefs saved")
Prefs.Data.u_9 = { Favs = { "Goto", {}, "Goto" }; Side = "Bad" }
local P2 = SR.PrefsGet(9)
Eq(P2 and #P2.Favs, 1, "stored prefs cleaned on read") Eq(P2 and P2.Side, nil, "a bad side dropped")
Prefs.Fail = 3
local P3, E3p = SR.PrefsGet(10)
Eq(P3, nil, "a failed prefs read") Eq(E3p, "Favourites unavailable", "prefs message")

-- 13. a flush already running (the 30 s loop) doesn't hide entries: they stay readable while it writes, and a second
-- FlushLog waits for it, so "flush, then read" finds everything logged before the call
SR.Clock = function() return Day * 86400 + 3600 end
Log.Slow = 0.3
SR.LogAdd({ At = T + 60; Staff = "mod"; Action = "Racing"; Side = "Moderate"; Ok = false })
task.spawn(SR.FlushLog)
task.wait(0.05)
Eq(SR.LogDay(0, { Query = "Racing" }).Total, 1, "an entry being written still shows")
SR.LogAdd({ At = T + 61; Staff = "mod"; Action = "Racing"; Side = "Moderate"; Ok = false })
Eq(SR.FlushLog(), true, "the second flush waits, then saves")
Log.Slow = nil
local Racing = 0
for _, E in Log.Data[`day_{Day}_studio`] do if E.Action == "Racing" then Racing += 1 end end
Eq(Racing, 2, "both racing entries saved, once each")
Eq(SR.LogDay(0, { Query = "Racing"; Chip = "Refused" }).Total, 2, "and read back once each")

if #Fails > 0 then return "FAIL " .. #Fails .. "\n" .. table.concat(Fails, "\n") end
return "PASS records_store"
