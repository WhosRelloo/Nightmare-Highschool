--[[ (phase6-strafes) Locomotion numbers. Spec: docs/superpowers/specs/2026-11-22-strafes-npc-gestures-design.md §1.
	Read by Controllers.Character.AnimationController (the directional walk, stride-matched cadence), Controllers.CineActor
	(the approach cadence) and Services.Features.CombatSpeed (the strafe speed cap). Maths: Functions.Locomotion.
	Strides: studs/s each clip covers at 1x on 2-stud R6 legs (forward kinematics, spec §1.2). ]]
return {
	Ids = {
		-- the square-chest bakes (ServerStorage.NHPublish.Gestures.NHG_StrafeLeft_Square / Right) once published;
		-- 0 = Studio plays the local KeyframeSequence, live servers the originals below
		StrafeLeftSquare = 71722624627092; StrafeRightSquare = 96856365545562;
		StrafeLeft = 126969213208550; StrafeRight = 84541589738848;
	};
	Studio = { StrafeLeftSquare = "NHG_StrafeLeft_Square"; StrafeRightSquare = "NHG_StrafeRight_Square" }; -- ServerStorage.NHGestures
	-- Walk / Sprint / CrouchWalk / FastSprint: the spread method (twice the feet's widest split per cycle; matches the NPCs'
	-- measured 5.3 studs/s on 1.8-stud legs). Strafes: the planted foot's ground speed of the baked square-chest clips
	-- (anim/out/manifest.json "stance": the spread method overstates a sideways step).
	Stride = { Walk = 5.9; Sprint = 13.5; CrouchWalk = 3.5; FastSprint = 18.0; Strafe = 4.8; StrafeLeft = 4.76; StrafeRight = 4.84 };
	-- left-foot contact as a fraction of the cycle (Walk measured from 113454991107499; strafes from the bake manifest)
	ContactPhase = { Walk = 0.057; Strafe = 0.226; StrafeLeft = 0.258; StrafeRight = 0.194 };
	Length = { Walk = 1.167; Strafe = 1.033 };
	-- (locomotion-pace, owner 2026-11-23: "the running speed and animation is too fast") the one place the walk and sprint
	-- speeds live. Sprint writes Sprint, then FastSprint after FastAfter seconds; StateManager's resets, Crouch, Evolution
	-- and Cine hand back Walk; StarterPlayer.CharacterWalkSpeed matches Walk. Attacking: the walk while an attack plays.
	-- At these the clips play at about 1.7x (walk), 1.5x (sprint) and 1.5x (fast sprint) instead of 2 to 2.4x.
	-- (owner, 2026-11-23, second pass: "make the run slower") sprint 20 (was 22), fast sprint 27 (was 30). Sprint stays over
	-- 19 (the sports' stamina drain reads Speed > 19) and over 17 (Stealth's sprint check).
	Speeds = { Walk = 10; Sprint = 20; FastSprint = 27; FastAfter = 2; Attacking = 7 };
	-- which clip a ground speed plays (Functions.Locomotion.Gait), for players and every humanoid NPC alike: the walk up to
	-- WalkMax, the sprint clip up to SprintMax, the fast sprint above. WalkMax 12: over a player's walk (10) and an NPC's
	-- patrol, under the students' flight (13 to 15, StudentBrain) and the AI chase (15 to 18), so those run instead of
	-- walking at 2.4x. SprintMax 23: between the sprint (20) and the fast sprint (27).
	Gaits = { WalkMax = 12; SprintMax = 23 };
	CadenceMin = 0.3;
	CadenceMax = 2.4;      -- owner, 2026-11-22: the stride fix on walk, sprint and crouch, capped at 2.4x playback
	StrafeSpeed = 7;       -- owner: slower strafes (was 8.5, 2026-11-23); CombatSpeed caps the walk band at this
	WalkBandMax = 20;
	EnterHold = 0.12;
	Fade = 0.15;
	FirstPersonDist = 1;
	-- any of these truthy (Player or Character attribute, or the flags the controller adds) keeps the plain walk
	Blockers = { "NHInCine", "NHApproach", "NHCineSeam", "NHCineHold", "NHTutorial", "Transformation", "WolfForm", "NHSkating", "NHEmoting", "Busy" };
	RemoteRate = 10; -- NHStrafe messages per second per player
}
