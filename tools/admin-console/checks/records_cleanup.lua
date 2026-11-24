-- records_cleanup.lua: Server, Play, [Test] stores only. Run with run_live.py after records_play_a (and, in the
-- restart round, after records_play_b). As the owner, through RemoveRecordEntry: unmute, then remove every record entry
-- By the owner since records_play_a's start (the marker's T0). Then put the owner's prefs back as they were before the
-- round and delete the marker.
local Players = game:GetService("Players")
local DataStoreService = game:GetService("DataStoreService")
local RunService = game:GetService("RunService")
local SSS = game.ServerScriptService.Services
local Admin = require(SSS.Features.Admin)
local SR = require(SSS.Features.StaffRecords)
local P = Players:GetPlayers()[1]
if not P then return "FAIL no player" end
if not RunService:IsStudio() or SR.PREFIX ~= "[Test] " then return "FAIL not on the [Test] stores" end
local Me = P.UserId
local PS = DataStoreService:GetDataStore("[Test] NHStaffPrefs_v1")
local Marker = PS:GetAsync("check1b_" .. Me)
if typeof(Marker) ~= "table" or typeof(Marker.T0) ~= "number" then return "FAIL no marker from records_play_a" end
local T0 = Marker.T0
local Fails, Removed = {}, 0
P:SetAttribute("NHTestLevel", nil)
task.wait(0.3)
local function go(Cmd, Args, Target)
	task.wait(0.2)
	return Admin.Dispatch(P, Cmd, Target, Args or {})
end
local A, B = go("Unmute", {}, Me)
if A ~= true then table.insert(Fails, "Unmute: " .. tostring(B)) end
local Rec = SR.Get(Me, true)
if not Rec then return "FAIL record read failed: run again" end
for _, List in { "Notes", "Warnings", "Bans", "Mutes" } do
	for _, E in table.clone(Rec[List]) do
		if E.By == Me and E.At >= T0 then
			local A2, B2 = go("RemoveRecordEntry", { List = List; At = E.At; By = E.By }, Me)
			if A2 == true then Removed += 1 else table.insert(Fails, `remove {List} {E.At}: {tostring(B2)}`) end
		end
	end
end
local After = SR.Get(Me, true)
for _, List in { "Notes", "Warnings", "Bans", "Mutes" } do
	for _, E in After and After[List] or {} do
		if E.By == Me and E.At >= T0 then table.insert(Fails, `left behind: {List} at {E.At}`) end
	end
end
-- prefs as before the round: a waiting save goes first, so it can't land after the put-back
SR.PrefsFlush(Me)
if typeof(Marker.Prefs) == "table" then PS:SetAsync("u_" .. Me, Marker.Prefs) else PS:RemoveAsync("u_" .. Me) end
PS:RemoveAsync("check1b_" .. Me)
if #Fails > 0 then return "FAIL " .. #Fails .. "\n" .. table.concat(Fails, "\n") end
return `PASS records_cleanup (removed {Removed})`
