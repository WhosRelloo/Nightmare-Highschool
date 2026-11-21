local Folder = game.ServerStorage:FindFirstChild("NH_Backup") or Instance.new("Folder", game.ServerStorage)
Folder.Name = "NH_Backup"
local B = Folder:FindFirstChild("BellTower_pre_20261120") or Instance.new("Folder", Folder)
B.Name = "BellTower_pre_20261120"
local Out = {}
for _, Path in { "StarterPlayer.StarterPlayerScripts.Controllers.Gui.ClockHud", "StarterPlayer.StarterPlayerScripts.Controllers.Gui.QuestTracker" } do
	local I = game
	for Part in string.gmatch(Path, "[^%.]+") do I = I:FindFirstChild(Part) end
	local Name = Path:gsub("%.", "_")
	if not B:FindFirstChild(Name) then local C = I:Clone() C.Name = Name C.Parent = B end
	table.insert(Out, Name)
end
return table.concat(Out, ", ")
