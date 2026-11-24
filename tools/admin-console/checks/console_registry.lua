local Admin = game.ServerScriptService.Services.Features:FindFirstChild("Admin")
if not Admin then return "FAIL Features.Admin missing" end
local MetaMod = Admin:FindFirstChild("Meta")
if not MetaMod then return "FAIL Admin.Meta missing" end
local S = require(game.ReplicatedStorage.Functions.StaffConsole:Clone())
local Meta = require(MetaMod:Clone())
local Fails = {}
-- the command ids in Admin's source: every top-level `C.<Id> = {`
local Ids = {}
for Id in string.gmatch("\n" .. Admin.Source, "\nC%.(%w+) = {") do Ids[Id] = true end
local N = 0
for Id in Ids do
	N += 1
	if not Meta[Id] then table.insert(Fails, "no Meta for " .. Id) end
end
for Id, D in Meta do
	if not Ids[Id] then table.insert(Fails, "Meta for a missing command " .. Id) end
	local Ok, Why = S.Validate(Id, D)
	if not Ok then table.insert(Fails, Why) end
end
if N ~= 67 then table.insert(Fails, "commands in Admin: " .. N .. ", want 67") end
-- danger list (spec §5 + §2b)
local DANGER = { Kick = true, Ban = true, Kill = true, Shutdown = true, ClearEnemies = true, FreezeAll = true,
	ServerLock = true, BringAll = true, QuestReset = true, RegionsReset = true, RemoveRecordEntry = true }
for Id, D in Meta do
	if (DANGER[Id] == true) ~= (D.Danger == true) then table.insert(Fails, Id .. " danger is " .. tostring(D.Danger)) end
end
-- owner-only by level: Shutdown and Remove history entry (the rest are checked inside Run)
local OWNER = { Shutdown = true, RemoveRecordEntry = true }
for Id, D in Meta do
	if (D.Level == 3) ~= (OWNER[Id] == true) then table.insert(Fails, Id .. " level " .. D.Level) end
end
-- only Remove history entry takes an offline UserId
for Id, D in Meta do
	if (D.Target == "user") ~= (Id == "RemoveRecordEntry") then table.insert(Fails, Id .. " target " .. D.Target) end
end
-- every icon exists in the art config (when it is installed)
local Art = game.ReplicatedStorage.Config:FindFirstChild("ConsoleArt")
if Art then
	local A = require(Art:Clone())
	for Id, D in Meta do if not A.Icons[D.Icon] then table.insert(Fails, Id .. " icon " .. D.Icon .. " has no id") end end
end
-- every section has at least one card
for Side, List in S.SECTIONS do
	for _, Sec in List do
		if S.CARDLESS and S.CARDLESS[Sec] then continue end
		local Any = false
		for _, D in Meta do if D.Side == Side and D.Section == Sec then Any = true end end
		if not Any then table.insert(Fails, Side .. "/" .. Sec .. " has no server card") end
	end
end
if #Fails > 0 then return "FAIL " .. #Fails .. "\n" .. table.concat(Fails, "\n") end
return "PASS console_registry (" .. N .. " commands)"
