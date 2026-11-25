-- console_mute_remove.lua: Server, Play, slot 2, [Test] stores only. Run with run_live.py (the game's own VM).
-- Task 9: removing a mute entry that is still on lifts the live mute (or keeps it for another open mute); an ended
-- mute or a ban entry changes nothing. It goes through the real Dispatch as the owner. The player's staff record is
-- copied first and put back exactly at the end, and Muted is cleared.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local SSS = game.ServerScriptService.Services
local Admin = require(SSS.Features.Admin)
local SR = require(SSS.Features.StaffRecords)
local P = Players:GetPlayers()[1]
if not P then return "FAIL no player" end
if not RunService:IsStudio() or SR.PREFIX ~= "[Test] " then return "FAIL not on the [Test] stores" end
local Me = P.UserId
if Admin.MutedUntil(P.UserId) ~= nil then return "FAIL the player is muted already: unmute first" end
local Fails = {}
local LISTS = { "Notes", "Warnings", "Bans", "Mutes", "Reports" }
local Snap0 = SR.Get(Me, true)
if not Snap0 then return "FAIL record read failed: run again" end
local Snap = {}
for _, L in LISTS do Snap[L] = table.clone(Snap0[L] or {}) end
for _, L in LISTS do for I, E in Snap[L] do if typeof(E) == "table" then Snap[L][I] = table.clone(E) end end end
local function go(Cmd, Args)
	task.wait(0.2) -- Dispatch's 0.15 s rate limit
	if script:GetAttribute("Stop") then error("stopped by run_live.py (timeout)", 0) end
	return Admin.Dispatch(P, Cmd, Me, Args or {})
end
local function fail(S) table.insert(Fails, S) end
local function newestMute()
	local R = SR.Get(Me, true)
	return R.Mutes[#R.Mutes]
end
local function remove(List, E) return go("RemoveRecordEntry", { List = List; At = E.At; By = E.By }) end
local function body()
	Admin.TestSkipBanApi = true
	P:SetAttribute("NHTestLevel", 3) task.wait(0.3)
	go("Unmute")
	-- 1. one active mute, removed: Muted cleared, the message says lifted
	go("Mute", { Minutes = 60; Reason = "t9 one" })
	if Admin.MutedUntil(Me) == nil then fail("1: Mute did not set Muted") end
	local E1 = newestMute()
	local A, B = remove("Mutes", E1)
	if A ~= true or not string.find(tostring(B), "; mute lifted", 1, true) then fail(`1: got {tostring(A)} {tostring(B)}`) end
	if Admin.MutedUntil(Me) ~= nil then fail("1: Muted still set") end
	print("t9-1", A, B)
	-- 2. two active mutes, the newer removed: still muted, until the other's end; then the other removed: lifted
	task.wait(1.1) go("Mute", { Minutes = 10; Reason = "t9 a" }) local Ea = newestMute()
	task.wait(1.1) go("Mute", { Minutes = 60; Reason = "t9 b" }) local Eb = newestMute()
	A, B = remove("Mutes", Eb)
	if A ~= true or not string.find(tostring(B), "; still muted by another entry", 1, true) then fail(`2: got {tostring(A)} {tostring(B)}`) end
	if Admin.MutedUntil(Me) ~= Ea.Until then fail(`2: Muted is {tostring(Admin.MutedUntil(Me))}, want {Ea.Until}`) end
	print("t9-2", A, B)
	A, B = remove("Mutes", Ea)
	if A ~= true or not string.find(tostring(B), "; mute lifted", 1, true) or Admin.MutedUntil(Me) ~= nil then fail(`2b: got {tostring(A)} {tostring(B)} {tostring(Admin.MutedUntil(Me))}`) end
	-- 3. an ended mute removed while another is on: no change to Muted, no outcome in the message
	local Now = os.time()
	local Ended = { By = Me; At = Now - 7200; Until = Now - 3600; Reason = "t9 ended" }
	local Lifted = { By = Me; At = Now - 7300; Until = 0; Reason = "t9 lifted"; Lifted = { By = Me; At = Now - 7000 } }
	SR.Write(Me, function(R) table.insert(R.Mutes, Ended) table.insert(R.Mutes, Lifted) end)
	go("Mute", { Minutes = 10; Reason = "t9 open" }) local Open = newestMute()
	local Before = Admin.MutedUntil(Me)
	for _, E in { Ended, Lifted } do
		A, B = remove("Mutes", E)
		if A ~= true or string.find(tostring(B), "mute lifted", 1, true) or string.find(tostring(B), "still muted", 1, true) then fail(`3: got {tostring(A)} {tostring(B)}`) end
		if Admin.MutedUntil(Me) ~= Before or Before ~= Open.Until then fail(`3: Muted changed to {tostring(Admin.MutedUntil(Me))}`) end
	end
	print("t9-3", A, B)
	remove("Mutes", Open)
	if Admin.MutedUntil(Me) ~= nil then fail("3: cleanup left Muted set") end
	-- 4. a ban entry removed: not unbanned (no outcome text; Muted untouched)
	local Ban = { By = Me; At = Now - 100; Days = 0; Reason = "t9 ban" }
	SR.Write(Me, function(R) table.insert(R.Bans, Ban) end)
	go("Mute", { Minutes = 10; Reason = "t9 four" }) local Four = newestMute()
	local U = Admin.MutedUntil(Me)
	A, B = remove("Bans", Ban)
	if A ~= true or string.find(tostring(B), "unban", 1, true) or string.find(tostring(B), "lifted", 1, true) then fail(`4: got {tostring(A)} {tostring(B)}`) end
	if Admin.MutedUntil(Me) ~= U then fail("4: Muted changed") end
	print("t9-4", A, B)
	remove("Mutes", Four)
end
local ok, err = pcall(body)
if not ok then fail("error: " .. tostring(err)) end
-- put back: the record exactly as it was, no mute, level and ban-skip flag as before
pcall(function() go("Unmute") end)
SR.Write(Me, function(R)
	for _, L in LISTS do
		R[L] = {}
		for _, E in Snap[L] do table.insert(R[L], E) end
	end
end)
Admin.TestSkipBanApi = false
P:SetAttribute("NHTestLevel", nil)
local After = SR.Get(Me, true)
if not After then fail("put-back read failed") else
	for _, L in LISTS do
		if #After[L] ~= #Snap[L] then fail(`put-back {L}: {#After[L]} entries, was {#Snap[L]}`) end
	end
end
if #Fails > 0 then return "FAIL " .. #Fails .. "\n" .. table.concat(Fails, "\n") end
return "PASS console_mute_remove"
