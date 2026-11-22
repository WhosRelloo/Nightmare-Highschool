local Need = {
	"Workspace.Hometown.BusStop.WFBusStop", "Workspace.Hometown.BlackBus.WFBlackBus", "Workspace.Hometown.Garden.WFBiscuit",
	"Workspace.NHCineSets.BusStop.Stand", "Workspace.NHCineSets.BusStop.BusStop", "Workspace.NHCineSets.Garden.Biscuit",
}
local Bad = {}
for _, P in Need do
	local I = game
	for Part in P:gmatch("[^%.]+") do I = I and I:FindFirstChild(Part) end
	if not I then table.insert(Bad, "missing " .. P) end
end
local Bus = workspace.Hometown and workspace.Hometown:FindFirstChild("BlackBus")
Bus = Bus and Bus:FindFirstChild("WFBlackBus")
local Ctl = Bus and Bus:FindFirstChildWhichIsA("AnimationController", true)
if not (Ctl and Ctl:FindFirstChildOfClass("Animator")) then table.insert(Bad, "bus has no AnimationController/Animator") end
local Clips = require(game.ReplicatedStorage.Config.CineClips)
for _, K in { "BusBrakeStop", "BusDoorsOpen", "BusDriverTurn", "BusPullAway", "BusEngineIdle" } do
	if typeof(Clips[K]) ~= "string" or Clips[K] == "" then table.insert(Bad, "no clip id " .. K) end
end
return if #Bad == 0 then "ASSETS OK" else table.concat(Bad, "\n")
