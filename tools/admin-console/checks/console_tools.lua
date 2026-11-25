local G = game.StarterPlayer.StarterPlayerScripts.Controllers.Gui
local Root = G:FindFirstChild("StaffConsole")
local Mod = Root and Root:FindFirstChild("Tools")
if not Mod then return "FAIL StaffConsole.Tools missing" end
local T = require(Mod:Clone())
local SC = require(game.ReplicatedStorage.Functions.StaffConsole)
local Art = require(game.ReplicatedStorage.Config.ConsoleArt)
local Fails = {}
if #T.Defs ~= 7 then table.insert(Fails, "defs " .. #T.Defs) end
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
-- (phase 2) Preview just for me
local PV
for _, D in T.Defs do if D.Id == "ToolPreview" then PV = D end end
if not PV then table.insert(Fails, "ToolPreview card missing")
else
	if PV.Section ~= "World" then table.insert(Fails, "preview section " .. tostring(PV.Section)) end
	if PV.Level ~= 2 then table.insert(Fails, "preview level " .. tostring(PV.Level)) end
	if #PV.Args ~= 3 then table.insert(Fails, "preview args " .. #PV.Args) end
end
local A1 = T.PreviewAttrs({ Season = "Winter"; Moon = "Full"; Sky = "Storm" })
if A1.NHSeasonPreview ~= "Winter" then table.insert(Fails, "season") end
if A1.NHMoonPhasePreview ~= "Full" then table.insert(Fails, "moon") end
if A1.NHMoonPreview ~= true then table.insert(Fails, "full moon size") end
if A1.NHSkyPreview ~= "Storm" then table.insert(Fails, "sky") end
local A2 = T.PreviewAttrs({ Season = "Off"; Moon = "Crimson"; Sky = "Off" })
if A2.NHSeasonPreview ~= nil then table.insert(Fails, "season off") end
if A2.NHMoonPhasePreview ~= "Crimson" then table.insert(Fails, "crimson") end
if A2.NHMoonPreview ~= nil then table.insert(Fails, "not full") end
if A2.NHSkyPreview ~= nil then table.insert(Fails, "sky off") end
local A3 = T.PreviewAttrs({ Season = "Autumn" })
if A3.NHSeasonPreview ~= "Autumn" then table.insert(Fails, "Autumn previews as Autumn") end
if A3.NHMoonPhasePreview ~= nil then table.insert(Fails, "missing moon is off") end
if #Fails > 0 then return "FAIL tools: " .. table.concat(Fails, "; ") end
return "PASS tools"
