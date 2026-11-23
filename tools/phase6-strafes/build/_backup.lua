-- phase6-strafes T1: back up every script this plan changes, before the first install (Edit). Idempotent per name.
if game.PlaceId ~= 98950102230473 then return "REFUSED: not NH Combat Test" end
local PATHS = {
	"StarterPlayer.StarterPlayerScripts.Controllers.Character.AnimationController",
	"StarterPlayer.StarterPlayerScripts.Controllers.CineActor",
	"ServerScriptService.Services.Features.CombatSpeed",
	"ServerScriptService.Services.AI.StudentBrain",
	"ServerScriptService.Services.AI.StudentBrain.Nudges",
	"ServerScriptService.Services.Features.Schedules",
	"ServerScriptService.Services.World.Scenes",
	"ReplicatedStorage.Config.Scenes",
	"ServerScriptService.Services.Social.Npcs",
	"ReplicatedStorage.Config.Npcs",
	"ServerScriptService.Services.School.HallMonitor",
	"ServerScriptService.Services.Social.CliqueFights",
	"ServerScriptService.Services.Features.PlayerSeats",
	"ReplicatedStorage.Config.Regions",
}
local SS = game:GetService("ServerStorage")
local Root = SS:FindFirstChild("NH_Backup") or Instance.new("Folder")
Root.Name = "NH_Backup"
Root.Parent = SS
local F = Root:FindFirstChild("Phase6Strafes_pre_20261122") or Instance.new("Folder")
F.Name = "Phase6Strafes_pre_20261122"
F.Parent = Root
local N, Out = 0, {}
for _, Path in PATHS do
	local Node = game
	for Part in string.gmatch(Path, "[^%.]+") do Node = Node and Node:FindFirstChild(Part) end
	if not Node then table.insert(Out, "missing " .. Path) continue end
	local Name = Path:gsub("%.", "_")
	if not F:FindFirstChild(Name) then
		local M = Instance.new("ModuleScript")
		M.Name = Name
		M.Source = Node.Source
		M:SetAttribute("From", Path)
		M:SetAttribute("Class", Node.ClassName)
		M.Parent = F
	end
	N += 1
end
return string.format("backed up %d / %d into %s %s", N, #PATHS, F:GetFullName(), table.concat(Out, " "))
