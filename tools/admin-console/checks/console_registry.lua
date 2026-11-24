local Admin = game.ServerScriptService.Services.Features:FindFirstChild("Admin")
if not Admin then return "FAIL Features.Admin missing" end
local MetaMod = Admin:FindFirstChild("Meta")
if not MetaMod then return "FAIL Admin.Meta missing" end
local S = require(game.ReplicatedStorage.Functions.StaffConsole:Clone())
local Meta = require(MetaMod:Clone())
local Fails = {}
-- the command ids in Admin's source (every top-level `C.<Id> = {`) plus each group module's ids
local Ids = {}
for Id in string.gmatch("\n" .. Admin.Source, "\nC%.(%w+) = {") do Ids[Id] = true end
local Stub = setmetatable({}, { __index = function() return function() error("a group called H while building") end end })
Stub.Meta = function(Name, Kind, Extra) local T = Extra or {} T.Name = Name T.Kind = Kind return T end
local GroupMeta = {}
for _, G in { "World", "Story", "BellTower" } do
	local Mod = Admin:FindFirstChild(G)
	if not Mod then table.insert(Fails, "Admin." .. G .. " missing") continue end
	local OkB, Built = pcall(require(Mod:Clone()), Stub)
	if not OkB then table.insert(Fails, "Admin." .. G .. ": " .. tostring(Built)) continue end
	for Id, E in Built do
		if Ids[Id] or GroupMeta[Id] then table.insert(Fails, "id taken twice: " .. Id) end
		Ids[Id] = true
		GroupMeta[Id] = E.Meta
		if typeof(E.Run) ~= "function" then table.insert(Fails, Id .. " has no Run") end
	end
end
for Id, D in GroupMeta do Meta[Id] = D end
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
if N ~= 85 then table.insert(Fails, "commands: " .. N .. ", want 85") end
-- (phase 2) the 18 new server cards are all there
for _, Id in { "TimePreset", "SetSeason", "SetMoon", "SetSky", "PlayCutscene", "CutsceneSeen", "TutorialEnter",
	"TutorialJump", "TutorialLeave", "GiveClue", "ResetCase", "SetHeat", "SetBells", "GiveSummons", "ClearNotoriety",
	"HallMonitors", "WhosWanted", "FormDirection" } do
	if not Ids[Id] then table.insert(Fails, "missing phase 2 card " .. Id) end
end
-- danger list (spec §5 + §2b)
local DANGER = { Kick = true, Ban = true, Kill = true, Shutdown = true, ClearEnemies = true, FreezeAll = true,
	ServerLock = true, BringAll = true, QuestReset = true, RegionsReset = true, RemoveRecordEntry = true,
	ResetCase = true, ClearNotoriety = true, HallMonitors = true }
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
