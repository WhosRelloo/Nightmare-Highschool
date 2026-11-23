-- Bell Tower R2 (Task 1 S4): clones of the eight scripts R2 edits, before any install. Edit VM.
local Folder = game.ServerStorage:FindFirstChild("NH_Backup") or Instance.new("Folder", game.ServerStorage)
Folder.Name = "NH_Backup"
local B = Folder:FindFirstChild("BellTower_R2_pre_20261121") or Instance.new("Folder", Folder)
B.Name = "BellTower_R2_pre_20261121"
local Out = {}
for _, Path in { "ServerScriptService.Services.School.Discipline", "ServerScriptService.Services.School.HallMonitor",
	"ReplicatedStorage.Config.Discipline", "ReplicatedStorage.PlayerData", "ReplicatedStorage.Functions.BellTower",
	"ReplicatedStorage.Config.BellTowerArt", "StarterPlayer.StarterPlayerScripts.Controllers.Gui.ClockHud",
	"StarterPlayer.StarterPlayerScripts.Controllers.Gui.QuestTracker" } do
	local I = game
	for Part in string.gmatch(Path, "[^%.]+") do I = I and I:FindFirstChild(Part) end
	local Name = Path:gsub("%.", "_")
	if I and not B:FindFirstChild(Name) then local C = I:Clone() C.Name = Name C.Parent = B end
	table.insert(Out, Name .. (I and "" or " MISSING"))
end
return #B:GetChildren() .. " clones: " .. table.concat(Out, ", ")
