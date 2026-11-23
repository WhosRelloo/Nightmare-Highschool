-- Sky 2360: clones of the scripts the sky wiring edits, before any install. Edit VM.
local Folder = game.ServerStorage:FindFirstChild("NH_Backup") or Instance.new("Folder", game.ServerStorage)
Folder.Name = "NH_Backup"
local B = Folder:FindFirstChild("Sky2360_pre_20261123") or Instance.new("Folder", Folder)
B.Name = "Sky2360_pre_20261123"
local G = "StarterPlayer.StarterPlayerScripts.Controllers."
local Out = {}
for _, Path in { "ReplicatedStorage.Config.DayCycle", G .. "Cine", "ReplicatedStorage.Config.Cine",
	"StarterPlayer.StarterPlayerScripts.Controllers.World.DayCycle", "StarterPlayer.StarterPlayerScripts.Controllers.World.FullMoon",
	"StarterPlayer.StarterPlayerScripts.Controllers.World.MoonPhases" } do
	local I = game
	for Part in string.gmatch(Path, "[^%.]+") do I = I and I:FindFirstChild(Part) end
	local Name = Path:gsub("%.", "_")
	if I and not B:FindFirstChild(Name) then local C = I:Clone() C.Name = Name C.Parent = B end
	table.insert(Out, Name .. (I and "" or " MISSING"))
end
return #B:GetChildren() .. " clones: " .. table.concat(Out, ", ")
