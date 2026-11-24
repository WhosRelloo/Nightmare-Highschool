-- console_play_server.lua: run with Server (Play) for the full matrix, or Edit for the static half.
local RunService = game:GetService("RunService")
local Players = game:GetService("Players")
-- Edit: a clone, so a stale cached copy of the module is never handed back; Play: the running module (its state)
local Mod = game.ServerScriptService.Services.Features.Admin
local Admin = require(if RunService:IsRunning() then Mod else Mod:Clone())
local Fails = {}
local function Eq(Got, Want, What) if Got ~= Want then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end
Eq(typeof(Admin.Dispatch), "function", "Dispatch")
Eq(typeof(Admin.Registry), "function", "Registry")
if typeof(Admin.Registry) == "function" then
	Eq(#Admin.Registry(3), 66, "registry at level 3")
	-- level 1: Student 12 + Server 4 (Shutdown is level 3); level 2: those 16 + the Test side's 49
	Eq(#Admin.Registry(1), 16, "registry at level 1")
	Eq(#Admin.Registry(2), 65, "registry at level 2 (all but Shutdown)")
	Eq(#Admin.Registry(0), 0, "registry at level 0")
	for _, D in Admin.Registry(3) do if D.Run ~= nil then table.insert(Fails, D.Id .. " leaks Run") end end
end
-- Lists() requires Sports.Matches, which never returns in Edit (its Data dependencies yield), so it runs in Play only
if RunService:IsRunning() then
	local L = Admin.Lists()
	Eq(typeof(L.Races), "table", "Lists.Races") Eq(typeof(L.Gear), "table", "Lists.Gear")
	Eq(Admin.Lists(), L, "Lists cached for 10 s")
end
if #Fails > 0 then return "FAIL " .. #Fails .. "\n" .. table.concat(Fails, "\n") end
return "PASS console_play_server (static: " .. (if RunService:IsRunning() then "Play" else "Edit") .. ")"
