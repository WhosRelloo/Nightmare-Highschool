-- tools/electives/anim/clips_map.lua (Edit): ReplicatedStorage.AnatomyClips.Clips, step/action -> seated R6 clip name.
local Folder = game.ReplicatedStorage:WaitForChild("AnatomyClips")
local Map = Folder:FindFirstChild("Clips") or Instance.new("ModuleScript")
Map.Name = "Clips"
Map.Source = [==[-- ReplicatedStorage.AnatomyClips.Clips (tools/electives/anim/clips_map.lua): step/action -> seated R6 clip in
-- AnatomyClips.Animations. Every clip has a Contact marker where its action lands. Put-down plays Lift in reverse.
return {
	Idle = "AnatBenchIdle";
	Unwind = "AnatUnwind"; Unscrew = "AnatUnwind";
	Trace = "AnatTrace";
	Pry = "AnatPry";
	Lift = "AnatLift"; Pick = "AnatLift"; Put = "AnatLift";
	Inspect = "AnatLoupe";
	Recoil = "AnatRecoil";
	Place = "AnatWrite"; Write = "AnatWrite";
	Done = "AnatDone";
}
]==]
Map.Parent = Folder
return "Clips map ok"
