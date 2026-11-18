--[[ (2.29) Rumour wording (Social.Rumours). Templates by incident kind (Scene incidents by scene id); Size ladders go
	from mild to wild. Names: a player by their first name, a rostered student by first name, anything else as given. ]]
return {
	Templates = {
		Downed = { "{Doer} {Size} {Target} in {Where}.", "Heard {Target} got {SizePast} by {Doer} near {Where}." };
		Scuffle = { "The {Doer} came out on top in a scuffle in {Where}." };
		Caught = { "A monitor caught {Target} in {Where}. {Extra}" };
		Prank = { "Somebody marked a wall in {Where}. People are saying it was {Doer}." };
		Match = { "{Doer} won the match. {Extra}" };
		Beast = { "Something like a {Doer} was seen out by {Where}." };
		Moon = { "They say tonight's moon is {Extra}. Stay in." };
		Argument = { "{Doer} and {Target} had a {Size} in {Where}." };
		Locker = { "{Doer} {Size} {Target} into a locker in {Where}." };
		Notice = { "Someone defaced the notice board in {Where}. {Extra}" };
		EastWing = { "Somebody heard {Size} in the east wing last night." };
		Figure = { "{Doer} swears there was {Size} at the end of the main hall." };
		Dare = { "{Doer} dared {Target} to try the Records Office door." };
	};
	Sizes = {
		Downed = { `knocked down`, `flattened`, `wiped the floor with` };
		DownedPast = { `knocked down`, `flattened`, `destroyed` };
		Argument = { `row`, `screaming match`, `full-on fight` };
		Locker = { `pushed`, `shoved`, `slammed` };
		EastWing = { `footsteps`, `crying`, `someone calling a name` };
		Figure = { `a shadow`, `a girl in old clothes`, `a girl with no face` };
	};
	-- region names as players see them (Config.Regions ids -> words)
	Places = { MainHall = `the main hall`; Commons = `the Commons`; EastWing = `the east wing`; Cafeteria = `the cafeteria`;
		Library = `the library`; Chapel = `the chapel`; Dorms = `the dorms`; Grounds = `the grounds` };
	MaxLive = 30;
	HopSeconds = 300;
	LifeSeconds = 7200; -- one in-game day: Config.SchoolSchedule RealSecondsPerGameHour 300 x 24 (measured 2026-11-18)
	MutateChance = 0.2;
}
