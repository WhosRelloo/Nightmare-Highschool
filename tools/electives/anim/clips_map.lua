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
	-- published to the group (15981569) on 2026-11-25; read from itemconfiguration creations/get-assets
	Ids = {
		AnatBenchIdle = 117481599858207; AnatUnwind = 102587190817512; AnatTrace = 86075891799612;
		AnatPry = 133822918395116; AnatLift = 111362329532180; AnatRecoil = 123607750141449;
		AnatLoupe = 102743841450402; AnatWrite = 70531388019356; AnatDone = 134109698207019;
	};
}
]==]
Map.Parent = Folder
return "Clips map ok"
