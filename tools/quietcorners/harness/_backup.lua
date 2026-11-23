-- Quiet Corners (Task S1 Step 4): clones of the 14 scripts Quiet Corners edits, before any install. Edit VM.
local Folder = game.ServerStorage:FindFirstChild("NH_Backup") or Instance.new("Folder", game.ServerStorage)
Folder.Name = "NH_Backup"
local B = Folder:FindFirstChild("QuietCorners_pre_20261123") or Instance.new("Folder", Folder)
B.Name = "QuietCorners_pre_20261123"
local G = "StarterPlayer.StarterPlayerScripts.Controllers.Gui."
local Out = {}
for _, Path in { G .. "Notifications", G .. "PromptUi", G .. "Compass", G .. "Dialogue", G .. "QuestJournal", G .. "KitHud", G .. "TopBar",
	G .. "SettingsMenu", G .. "CineUI", "ReplicatedStorage.UI.Settings", "ReplicatedStorage.Config.Cases",
	"ServerScriptService.Services.Social.Dialogue", "ServerScriptService.Services.Quests.Investigation", "ServerScriptService.Services.Quests.Quests" } do
	local I = game
	for Part in string.gmatch(Path, "[^%.]+") do I = I and I:FindFirstChild(Part) end
	local Name = Path:gsub("%.", "_")
	if I and not B:FindFirstChild(Name) then local C = I:Clone() C.Name = Name C.Parent = B end
	table.insert(Out, Name .. (I and "" or " MISSING"))
end
return #B:GetChildren() .. " clones: " .. table.concat(Out, ", ")
