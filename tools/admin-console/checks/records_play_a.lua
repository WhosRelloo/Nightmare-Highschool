-- records_play_a.lua: Server, Play, slot 2, [Test] stores only. Run with run_live.py (the game's own VM).
-- 1b spec §6, the first half: Warn, Note, Mute (each length) and Ban written through the real Dispatch and read back
-- from the store; the unban rule at levels 1 and 3; Remove history entry refused at 2, passes at 3 and is logged; the
-- log saved and read back. It leaves an open 1-day mute ("1b restart") and a marker key (its start time and the owner's
-- prefs before the round) for records_play_b.lua and records_cleanup.lua.
local Players = game:GetService("Players")
local DataStoreService = game:GetService("DataStoreService")
local RunService = game:GetService("RunService")
local SSS = game.ServerScriptService.Services
local Admin = require(SSS.Features.Admin)
local SR = require(SSS.Features.StaffRecords)
local P = Players:GetPlayers()[1]
if not P then return "FAIL no player" end
if not RunService:IsStudio() or SR.PREFIX ~= "[Test] " then return "FAIL not on the [Test] stores" end
local Me, T0 = P.UserId, os.time()
local Fails, Ran = {}, 0
local function go(Cmd, Args, Target)
	task.wait(0.2) -- Dispatch's 0.15 s rate limit
	if script:GetAttribute("Stop") then error("stopped by run_live.py (timeout)", 0) end
	return Admin.Dispatch(P, Cmd, Target, Args or {})
end
local function want(Ok, Cmd, Args, Target, Expect)
	local A, B = go(Cmd, Args, Target)
	Ran += 1
	if (A == true) ~= Ok then table.insert(Fails, `{Cmd}: got {tostring(A)} {tostring(B)}`) return end
	if Expect and not string.find(tostring(B), Expect, 1, true) then table.insert(Fails, `{Cmd}: "{tostring(B)}", want "{Expect}"`) end
end
local function level(N) P:SetAttribute("NHTestLevel", N) task.wait(0.3) end
local function body()
	local PS = DataStoreService:GetDataStore("[Test] NHStaffPrefs_v1")
	PS:SetAsync("check1b_" .. Me, { T0 = T0; Prefs = PS:GetAsync("u_" .. Me) })
	Admin.TestSkipBanApi = true
	want(true, "Warn", { Reason = "1b test warn" }, Me, "Saved")
	want(true, "Note", { Text = "1b test note" }, Me, "Saved")
	want(false, "Note", { Text = "" }, Me, "Note is needed")
	for _, Min in { 10, 60, 1440, 0 } do
		want(true, "Mute", { Minutes = Min; Reason = "1b test" }, Me, "Saved")
		local U = Admin.MutedUntil(Me)
		if U == nil or (Min == 0 and U ~= 0) or (Min > 0 and math.abs(U - (os.time() + Min * 60)) > 3) then
			table.insert(Fails, `Mute {Min}: MutedUntil is {tostring(U)}`)
		end
		want(true, "Unmute", {}, Me, "Saved")
		if Admin.MutedUntil(Me) ~= nil then table.insert(Fails, `Unmute after {Min}: still muted`) end
	end
	level(3) want(true, "Ban", { Days = 0; Reason = "1b test" }, Me, "Ban API skipped")
	level(1) want(false, "Unban", { UserId = Me }, nil, "Permanent bans can only be lifted by the owner")
	level(3) want(true, "Unban", { UserId = Me }, nil, "Unbanned")
	level(1) want(true, "Ban", { Days = 7; Reason = "1b test" }, Me, "Ban API skipped")
	want(true, "Unban", { UserId = Me }, nil, "Unbanned")
	level(nil)

	-- read back from the store, not the cache
	local Rec, Err = SR.Get(Me, true)
	if not Rec then table.insert(Fails, "read back: " .. tostring(Err)) return end
	local function mine(List, Pred)
		local N = 0
		for _, E in Rec[List] do if E.By == Me and E.At >= T0 and Pred(E) then N += 1 end end
		return N
	end
	if mine("Warnings", function(E) return E.Reason == "1b test warn" end) ~= 1 then table.insert(Fails, "the warning didn't read back") end
	if mine("Notes", function(E) return E.Text == "1b test note" end) ~= 1 then table.insert(Fails, "the note didn't read back") end
	for _, Min in { 10, 60, 1440 } do
		if mine("Mutes", function(E) return E.Until - E.At == Min * 60 and E.Lifted ~= nil end) ~= 1 then
			table.insert(Fails, `the {Min} min mute didn't read back lifted`)
		end
	end
	if mine("Mutes", function(E) return E.Until == 0 and E.Lifted ~= nil end) ~= 1 then table.insert(Fails, "the until-unmuted mute didn't read back lifted") end
	if mine("Bans", function(E) return E.Days == 0 and E.Lifted ~= nil end) ~= 1 then table.insert(Fails, "the permanent ban didn't read back lifted") end
	if mine("Bans", function(E) return E.Days == 7 and E.Lifted ~= nil end) ~= 1 then table.insert(Fails, "the 7-day ban didn't read back lifted") end

	-- Remove history entry: refused at 2, passes at 3, logged
	local W
	for _, E in Rec.Warnings do if E.Reason == "1b test warn" and E.By == Me and E.At >= T0 then W = E end end
	if W then
		level(2) want(false, "RemoveRecordEntry", { List = "Warnings"; At = W.At; By = W.By }, Me, "Needs the owner")
		level(nil) want(true, "RemoveRecordEntry", { List = "Warnings"; At = W.At; By = W.By }, Me, "Removed")
		local Rec2 = SR.Get(Me, true)
		for _, E in Rec2 and Rec2.Warnings or {} do
			if E.At == W.At and E.By == W.By and E.Reason == W.Reason then table.insert(Fails, "the warning is still there after RemoveRecordEntry") end
		end
	end

	-- the log: saved, then today read back from the store
	if not SR.FlushLog() then table.insert(Fails, "FlushLog failed") end
	local Day = SR.LogDay(0, { Query = "RemoveRecordEntry" })
	local Removed, Refused = false, false
	for _, E in Day and Day.Rows or {} do
		if E.At >= T0 and E.StaffId == Me then
			if E.Ok and string.find(E.Detail, "1b test warn", 1, true) then Removed = true end
			if not E.Ok and string.find(E.Detail, "Needs the owner", 1, true) then Refused = true end
		end
	end
	if not Removed then table.insert(Fails, "the removal isn't in today's log with the entry's text") end
	if not Refused then table.insert(Fails, "the refused removal isn't in today's log") end
	local Ref = SR.LogDay(0, { Chip = "Refused"; Query = "Unban" })
	if not (Ref and Ref.Total >= 1) then table.insert(Fails, "the refused Unban isn't under the Refused chip") end

	-- for the restart: an open mute
	want(true, "Mute", { Minutes = 1440; Reason = "1b restart" }, Me, "Saved")
end
local OkRun, Err = xpcall(body, debug.traceback)
if not OkRun then table.insert(Fails, "run stopped: " .. tostring(Err):sub(1, 300)) end
P:SetAttribute("NHTestLevel", nil)
Admin.TestSkipBanApi = false
if #Fails > 0 then return "FAIL " .. #Fails .. " of " .. Ran .. "\n" .. table.concat(Fails, "\n") end
return `PASS records_play_a ({Ran} calls; T0 {T0})`
