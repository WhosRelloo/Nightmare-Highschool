local G = game.StarterPlayer.StarterPlayerScripts.Controllers.Gui
local Root = G:FindFirstChild("StaffConsole")
local Mod = Root and Root:FindFirstChild("Tools")
if not Mod then return "FAIL StaffConsole.Tools missing" end
local T = require(Mod:Clone())
local SC = require(game.ReplicatedStorage.Functions.StaffConsole)
local Art = require(game.ReplicatedStorage.Config.ConsoleArt)
local Fails = {}
if #T.Defs ~= 6 then table.insert(Fails, "defs " .. #T.Defs) end
if typeof(T.Do) ~= "function" or typeof(T.Init) ~= "function" or typeof(T.State) ~= "function" then table.insert(Fails, "api") end
for _, D in T.Defs do
	local Ok, Why = SC.Validate(D.Id, D)
	if not Ok then table.insert(Fails, tostring(Why)) end
	if D.Local ~= true then table.insert(Fails, D.Id .. " not Local") end
	if not Art.Icons[D.Icon] then table.insert(Fails, D.Id .. " icon " .. D.Icon) end
end
local S = T.State()
if S.Fly or S.Noclip or S.Esp or S.ClickTp then table.insert(Fails, "state not all off") end
local Ok, Msg = T.Do("ToolClickTp", {}, nil)
if not (Ok and Msg == "Ctrl+click teleport on" and T.State().ClickTp) then table.insert(Fails, "ClickTp toggle") end
Ok, Msg = T.Do("ToolClickTp", {}, nil)
if T.State().ClickTp then table.insert(Fails, "ClickTp off") end
Ok = T.Do("ToolInspect", {}, nil) if Ok then table.insert(Fails, "inspect needs target") end
Ok = T.Do("ToolInspect", {}, 5) if not Ok then table.insert(Fails, "inspect with target") end
Ok = T.Do("Nope", {}, nil) if Ok then table.insert(Fails, "unknown") end
if #Fails > 0 then return "FAIL tools: " .. table.concat(Fails, "; ") end
return "PASS tools"
