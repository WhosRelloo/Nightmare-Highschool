--[[ (2.26.0) Cutscene clips by name. The owner's rule: use the game's own animations; if the game has none, use the
	group's. A value is either
	  * `Assets:<path>`: an Animation under ReplicatedStorage.Assets.Animations (the game's own clip), or
	  * `rbxassetid://<id>`: a published animation (the group's).
	An empty string plays the KeyframeSequence of the same name under ReplicatedStorage.NHCineClips (Studio only).
	Hit times (for the cut's events): Uptilt Hit 0.50; Fist RunningM1 Hit 0.33; Parried 1 recoils at 0.03;
	Posture Break at 0.10; Fist Clinch Hit 0.37; Fist M2 strikes at 0.43. ]]
return {
	StrikeRise = `Assets:Default.Uptilt`; -- it rises from the floor into an upward strike
	StrikeLunge = `Assets:Weapons.Fist.RunningM1`; -- the lunge is a running M1
	StrikeRecoil = `Assets:Default.Parried.1`; -- it overshoots, or is thrown off the file
	StrikeGrab = `Assets:Weapons.Fist.Moves.Clinch`; -- it grabs your arm
	StrikeStagger = `Assets:Default.Posture Break`; -- the shove breaks its posture
	StrikeTug = `rbxassetid://98518994869117`; -- group upload (loop)
	StrikeShatter = `rbxassetid://104606462612953`; -- group upload
	YouTugPull = `rbxassetid://116365221175140`; -- group upload (loop)
	YouFinisher = `Assets:Weapons.Fist.M2`; -- the charged heavy
	-- (2.35.0) the black bus (WFBlackBus: a rigid rig, plain meshes on Motor6Ds built by stage/bus_rig.lua), group uploads of
	-- ServerStorage.NHPublish.WFBlackBus (an empty string would play the Studio preview NHCineClips.Bus<Clip>). EngineIdle is the
	-- base loop; EngineIdle and WipersSweep loop. (The earlier ids target the deleted skinned bone rig: dead.)
	BusBrakeStop = `rbxassetid://86119358976248`;
	BusDoorsOpen = `rbxassetid://104054269135104`;
	BusDoorsClose = `rbxassetid://123569026172264`;
	BusDriverTurn = `rbxassetid://83327824886537`;
	BusEngineIdle = `rbxassetid://128354189531944`; -- loop (the base loop)
	BusPullAway = `rbxassetid://104172158912194`;
	BusWipersSweep = `rbxassetid://121067625954733`; -- loop
	-- (2.35.0) Biscuit (WFBiscuit, an AnimationController rig) and the garden gate, group uploads; BiscuitSleep and BiscuitTrot loop
	BiscuitSleep = `rbxassetid://95274201499517`; -- loop (the base loop)
	BiscuitTrot = `rbxassetid://101982272082907`; -- loop
	BiscuitWuff = `rbxassetid://116754381892948`;
	BiscuitWakeStare = `rbxassetid://104742093696031`;
	BiscuitSigh = `rbxassetid://131075439249040`;
	GateOpen = `rbxassetid://127810787589543`;
	GateSwingShut = `rbxassetid://100841390179835`;
	WickHouseSashOpen = `rbxassetid://73964857478179`; -- the rigid house (stage/rigid_rig.py), group upload
	-- (2.35.0) the tutorial's player clips (tools/tutorial-anim; ReplicatedStorage.NHCineClips.Tutorial), group uploads.
	-- Each chain piece and its _End re-seat pose. Names match the KeyframeSequences, so Ctx.Clip finds the id first.
	BiscuitStirs1_GameCrouchWalk = `rbxassetid://104742186430395`;
	BiscuitStirs1_GameCrouchWalk_End = `rbxassetid://114383628130359`;
	BiscuitStirs2 = `rbxassetid://72201043089605`;
	BiscuitStirs2_End = `rbxassetid://78542119706131`;
	BiscuitStirs3_GameCrouchWalk = `rbxassetid://135515545347434`;
	BiscuitStirs3_GameCrouchWalk_End = `rbxassetid://89972499333873`;
	Breakfast1_TableIdle = `rbxassetid://109868055862712`;
	Breakfast1_TableIdle_End = `rbxassetid://89266944406636`;
	Breakfast2 = `rbxassetid://125804185254516`;
	Breakfast2_End = `rbxassetid://123687859070157`;
	Breakfast3_TableIdle = `rbxassetid://76732098083526`;
	Breakfast3_TableIdle_End = `rbxassetid://122644695848385`;
	ColdOpen1 = `rbxassetid://85220841811898`;
	ColdOpen1_End = `rbxassetid://110698245477688`;
	Drainpipe1 = `rbxassetid://110710650729631`;
	Drainpipe1_End = `rbxassetid://93122474703582`;
	Drainpipe2_GameCrouch = `rbxassetid://133008119690769`;
	Drainpipe2_GameCrouch_End = `rbxassetid://125165455805666`;
	Excuses1_LieLookAround = `rbxassetid://106088660527993`;
	Excuses1_LieLookAround_End = `rbxassetid://91153672053638`;
	Excuses2 = `rbxassetid://91937184634014`;
	Excuses2_End = `rbxassetid://116007760291064`;
	FenceOver1_GameCrouchWalk = `rbxassetid://99637459557585`;
	FenceOver1_GameCrouchWalk_End = `rbxassetid://88159268691857`;
	FenceOver2 = `rbxassetid://137091473855957`;
	FenceOver2_End = `rbxassetid://88782954561713`;
	Getaway1_RunLookBack = `rbxassetid://76183749092409`;
	Getaway1_RunLookBack_End = `rbxassetid://140296024775548`;
	Getaway2 = `rbxassetid://83528567061215`;
	Getaway2_End = `rbxassetid://82218996342661`;
	Getaway3_LookAroundNervous = `rbxassetid://114245637626947`;
	Getaway3_LookAroundNervous_End = `rbxassetid://118457549329415`;
	HomeAgain1 = `rbxassetid://133562792056287`;
	HomeAgain1_End = `rbxassetid://83229111709432`;
	HomeAgain2_GameCrouchWalk = `rbxassetid://92794012057392`;
	HomeAgain2_GameCrouchWalk_End = `rbxassetid://115930374981365`;
	HomeAgain3 = `rbxassetid://104927466573203`;
	HomeAgain3_End = `rbxassetid://84542905733735`;
	HomeAgain4_SleepLoop = `rbxassetid://118208386984390`;
	HomeAgain4_SleepLoop_End = `rbxassetid://138379519558720`;
	HomeAgain5 = `rbxassetid://103078274443199`;
	HomeAgain5_End = `rbxassetid://123390355212066`;
	HomeAgain6_LieLookAround = `rbxassetid://137745883423938`;
	HomeAgain6_LieLookAround_End = `rbxassetid://81056343837106`;
	MomSlidesEnvelope1_ParentSit = `rbxassetid://130534592559705`;
	MomSlidesEnvelope1_ParentSit_End = `rbxassetid://82425911911282`;
	MomSlidesEnvelope2 = `rbxassetid://125667198097288`;
	MomSlidesEnvelope2_End = `rbxassetid://118108327265600`;
	MomSlidesEnvelope3_ParentSit = `rbxassetid://114110274723832`;
	MomSlidesEnvelope3_ParentSit_End = `rbxassetid://87471474399798`;
	ParentsWaiting1_ParentSit = `rbxassetid://83439854710005`;
	ParentsWaiting1_ParentSit_End = `rbxassetid://121812582146453`;
	ParentsWaiting2 = `rbxassetid://119616713171281`;
	ParentsWaiting2_End = `rbxassetid://131188960801441`;
	ParentsWaiting3_ParentSit = `rbxassetid://113919388559583`;
	ParentsWaiting3_ParentSit_End = `rbxassetid://102173104635294`;
	ParentsWaiting4 = `rbxassetid://89585758495566`;
	ParentsWaiting4_End = `rbxassetid://112130452838461`;
	ParentsWaiting5_ParentSit = `rbxassetid://86176788260761`;
	ParentsWaiting5_ParentSit_End = `rbxassetid://129441511459031`;
	TheBus1_WaitBored = `rbxassetid://74294967099318`;
	TheBus1_WaitBored_End = `rbxassetid://110562085631915`;
	TheBus2 = `rbxassetid://97522793120813`;
	TheBus2_End = `rbxassetid://100385944229977`;
	ThePlan1 = `rbxassetid://124666060221514`;
	ThePlan1_End = `rbxassetid://114978263088837`;
}
