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
}
