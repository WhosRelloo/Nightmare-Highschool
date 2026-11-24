-- records_play_b.lua: Server, Play, after stopping Play and starting it again (1b spec §6 "Across a restart"). The
-- open mute from records_play_a was applied again on join; the record and today's log read back the same. It changes
-- nothing: records_cleanup.lua runs after it.
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
local Marker = DataStoreService:GetDataStore("[Test] NHStaffPrefs_v1"):GetAsync("check1b_" .. Me)
if typeof(Marker) ~= "table" then return "FAIL no marker from records_play_a" end
local T0 = Marker.T0
local Fails = {}
-- the open mute, applied on join (Admin reads the record in PlayerAdded)
local t = os.clock()
while Admin.MutedUntil(Me) == nil and os.clock() - t < 15 do task.wait(0.5) end
local U = Admin.MutedUntil(Me)
if not (U and U > os.time()) then table.insert(Fails, `the open mute wasn't applied on join: {tostring(U)}`) end
-- the record reads back
local Rec, Err = SR.Get(Me, true)
if not Rec then return "FAIL record read: " .. tostring(Err) end
local function has(List, Pred) for _, E in Rec[List] do if E.By == Me and E.At >= T0 and Pred(E) then return true end end return false end
if not has("Notes", function(E) return E.Text == "1b test note" end) then table.insert(Fails, "the note is gone after the restart") end
if not has("Mutes", function(E) return E.Reason == "1b restart" and E.Lifted == nil end) then table.insert(Fails, "the open mute is gone from the record") end
if not has("Bans", function(E) return E.Days == 0 and E.Lifted ~= nil end) then table.insert(Fails, "the lifted permanent ban is gone") end
if has("Warnings", function(E) return E.Reason == "1b test warn" end) then table.insert(Fails, "the removed warning came back") end
-- today's log from the store (saved by records_play_a's flush and the first session's BindToClose)
local Day = SR.LogDay(0, { Query = "RemoveRecordEntry" })
local Found = false
for _, E in Day and Day.Rows or {} do
	if E.At >= T0 and E.StaffId == Me and E.Ok and string.find(E.Detail, "1b test warn", 1, true) then Found = true end
end
if not Found then table.insert(Fails, "the removal row isn't in today's log after the restart") end
if #Fails > 0 then return "FAIL " .. #Fails .. "\n" .. table.concat(Fails, "\n") end
return "PASS records_play_b"
