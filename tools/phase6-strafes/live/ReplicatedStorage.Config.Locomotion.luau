--[[ (phase6-strafes) Locomotion numbers. Spec: docs/superpowers/specs/2026-11-22-strafes-npc-gestures-design.md §1.
	Read by Controllers.Character.AnimationController (the directional walk, stride-matched cadence), Controllers.CineActor
	(the approach cadence) and Services.Features.CombatSpeed (the strafe speed cap). Maths: Functions.Locomotion.
	Strides: studs/s each clip covers at 1x on 2-stud R6 legs (forward kinematics, spec §1.2). ]]
return {
	Ids = {
		-- the square-chest bakes (ServerStorage.NHPublish.Gestures.NHG_StrafeLeft_Square / Right) once published;
		-- 0 = Studio plays the local KeyframeSequence, live servers the originals below
		StrafeLeftSquare = 0; StrafeRightSquare = 0;
		StrafeLeft = 126969213208550; StrafeRight = 84541589738848;
	};
	Studio = { StrafeLeftSquare = "NHG_StrafeLeft_Square"; StrafeRightSquare = "NHG_StrafeRight_Square" }; -- ServerStorage.NHGestures
	Stride = { Walk = 5.9; Sprint = 13.5; CrouchWalk = 3.5; FastSprint = 18.0; Strafe = 5.8 };
	ContactPhase = { Walk = 0; Strafe = 0 }; -- left-foot contact as a fraction of the cycle (filled from anim/out/manifest.json)
	Length = { Walk = 1.17; Strafe = 1.033 };
	CadenceMin = 0.3;
	CadenceMax = 2.4;      -- owner, 2026-11-22: the stride fix on walk, sprint and crouch, capped at 2.4x playback
	StrafeSpeed = 8.5;     -- owner: about 8.5 studs/s while strafing (CombatSpeed caps the walk band)
	WalkBandMax = 20;
	EnterHold = 0.12;
	Fade = 0.15;
	FirstPersonDist = 1;
	-- any of these truthy (Player or Character attribute, or the flags the controller adds) keeps the plain walk
	Blockers = { "NHInCine", "NHApproach", "NHCineSeam", "NHCineHold", "NHTutorial", "Transformation", "WolfForm", "NHSkating", "NHEmoting", "Busy" };
	RemoteRate = 10; -- NHStrafe messages per second per player
}
