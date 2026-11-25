-- Client, Play: Preview just for me and the row flags. Run with run_live.py <file> 120 Client.
local Players = game:GetService("Players")
local Me = Players.LocalPlayer
local G = Me.PlayerScripts:WaitForChild("Controllers"):WaitForChild("Gui")
local Tools = require(G.StaffConsole.Tools)
local Model = require(G.StaffConsole.Model)
local Fails = {}
local function Eq(Got, Want, What) if Got ~= Want then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end
local Keys = { "NHSeasonPreview", "NHMoonPhasePreview", "NHMoonPreview", "NHSkyPreview" }
local Old = {} for _, K in Keys do Old[K] = Me:GetAttribute(K) end
local SeasonW = workspace:GetAttribute("NHSeason")
local ok, err = pcall(function()
	local Ok1 = Tools.Do("ToolPreview", { Season = "Winter"; Moon = "Crimson"; Sky = "Storm" })
	Eq(Ok1, true, "preview ok")
	Eq(Me:GetAttribute("NHSeasonPreview"), "Winter", "season preview set")
	Eq(Me:GetAttribute("NHMoonPhasePreview"), "Crimson", "moon preview set")
	Eq(Me:GetAttribute("NHSkyPreview"), "Storm", "sky preview set")
	Eq(workspace:GetAttribute("NHSeason"), SeasonW, "the server season is untouched")
	local World = Me.PlayerScripts.Controllers:FindFirstChild("World")
	local DC = World and World:FindFirstChild("DayCycle")
	if DC then
		local D = require(DC)
		if typeof(D) == "table" and D.Season then Eq(D.Season(), "Winter", "DayCycle sees the preview") end
		if typeof(D) == "table" and D.Moon then Eq(D.Moon(), "Crimson", "DayCycle moon preview") end
	end
	task.wait(2)
	Tools.Do("ToolPreview", { Season = "Off"; Moon = "Full"; Sky = "Off" })
	Eq(Me:GetAttribute("NHMoonPreview"), true, "Full sets NHMoonPreview")
	Tools.Do("ToolPreview", { Season = "Off"; Moon = "Off"; Sky = "Off" })
	for _, K in Keys do Eq(Me:GetAttribute(K), nil, K .. " cleared") end
	Eq(table.concat(Model.Flags({ Transformed = true; Bells = 4; New = true; InCutscene = true }), ","), "TRANSFORMED,WANTED,NEW,IN CUTSCENE", "flags")
	Eq(#Model.Flags({ Bells = 2; New = false }), 0, "no flags for bell 2")
end)
for _, K in Keys do Me:SetAttribute(K, Old[K]) end
if not ok then return "FAIL error: " .. tostring(err) end
if #Fails > 0 then return "FAIL " .. #Fails .. "\n" .. table.concat(Fails, "\n") end
return "PASS console2_play_client"
