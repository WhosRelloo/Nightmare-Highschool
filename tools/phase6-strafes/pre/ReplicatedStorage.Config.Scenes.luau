--[[ (2.29) Scenes (World.Scenes; docs/expansion/13-Living-School.md §4.2). Six small scenes with rostered students,
	staged only where a player can see them (60 studs), at most one per region every 10 minutes, never in a cut or in
	class. Spot kinds: Hall (a hallway spot), Lockers (in front of the hallway lockers), Notice (the main hall's notice
	board), Region:<Id> (the middle of a region box), RecordsDoor. Region: the place's Config.Regions id (the region boxes don't line up with this place's rooms). A prompt step waits up to Seconds for a player to press
	it; Pressed / Missed choose the outcome. ]]
return {
	Argument = { Region = `MainHall`; When = { `Passing`, `Break`, `Lunch`, `AfterSchool` }; Spot = `Hall`; Cast = { Count = 2; Rival = true };
		Steps = {
			{ `go`, 1, Vector3.new(-1.5, 0, 0) }, { `go`, 2, Vector3.new(1.5, 0, 0) }, { `face`, 1, 2 }, { `face`, 2, 1 },
			{ `say`, 1, "You've got some nerve, {B}." }, { `wait`, 2 }, { `say`, 2, `Say that again. I dare you.` }, { `wait`, 2 },
			{ `prompt`, 1, `Step in`, 8 },
		};
		Pressed = { Lines = { { 1, `...Fine. Not worth it.` }, { 2, `This isn't over.` } }; Helper = true; Size = 1 };
		Missed = { Lines = { { 2, `Yeah? Come on then!` } }; Size = 3 };
	};
	Locker = { Region = `MainHall`; When = { `Passing`, `Break`, `Lunch`, `AfterSchool` }; Spot = `Lockers`; Cast = { Count = 2 };
		Steps = {
			{ `go`, 1, Vector3.new(0, 0, 3) }, { `go`, 2, Vector3.new(0, 0, 1.2) }, { `face`, 1, 2 },
			{ `say`, 1, "In you go, {B}." }, { `fx`, 2, `Shove` }, { `say`, 2, `Hey! Let me out!` },
			{ `prompt`, 2, `Help out`, 10 },
		};
		Pressed = { Lines = { { 2, `Thanks. I owe you.` } }; Helper = true; Size = 1 };
		Missed = { Lines = { { 1, `Enjoy the dark.` } }; Size = 3 };
	};
	Notice = { Region = `MainHall`; When = { `BeforeSchool` }; Spot = `Notice`; Cast = { Count = 2 };
		Steps = {
			{ `go`, 1, Vector3.new(-1.5, 0, 4) }, { `go`, 2, Vector3.new(1.5, 0, 4) }, { `face`, 1, `spot` }, { `face`, 2, `spot` },
			{ `say`, 1, `Who wrote that?` }, { `say`, 2, `"ANSWER THE BELL." In red. Creepy.` }, { `prompt`, 0, `Read it`, 12 },
		};
		Pressed = { Note = `ANSWER THE BELL, scrawled across the timetable in red.`; Size = 1; Extra = `It says "ANSWER THE BELL".` };
		Missed = { Size = 1; Extra = `Nobody saw who did it.` };
	};
	EastWing = { Region = `EastWing`; When = { `Evening` }; -- (2.29) at dusk: every student has gone home by Night, so a Night scene could never be cast
		 Spot = `Region:EastWing`; Cast = { Count = 1 };
		Steps = {
			{ `go`, 1, Vector3.new(0, 0, 0) }, { `say`, 1, `Did you hear that? Footsteps...` }, { `wait`, 3 },
			{ `prompt`, 1, `Go and look`, 10 },
		};
		Pressed = { Lines = { { 1, `Nothing. ...Right?` } }; Size = 1 };
		Missed = { Lines = { { 1, `I'm getting out of here.` } }; Size = 2 };
	};
	Figure = { Region = `MainHall`; When = { `Evening` }; -- (2.29) at dusk: every student has gone home by Night, so a Night scene could never be cast
		 Spot = `Hall`; Cast = { Count = 1 };
		Steps = {
			{ `go`, 1, Vector3.new(0, 0, 0) }, { `figure`, 26, 4 }, { `say`, 1, `There's someone at the end of the hall...` },
			{ `prompt`, 1, `Look up`, 6 },
		};
		Pressed = { Lines = { { 1, `She's gone. You saw her too, right?` } }; Size = 2 };
		Missed = { Lines = { { 1, `I need to sleep more.` } }; Size = 1 };
	};
	Dare = { Region = `MainHall`; When = { `AfterSchool`, `Evening` }; Spot = `RecordsDoor`; Cast = { Count = 2 };
		Steps = {
			{ `go`, 1, Vector3.new(-1.5, 0, 3) }, { `go`, 2, Vector3.new(0, 0, 1.5) }, { `face`, 1, 2 },
			{ `say`, 1, "Go on, {B}. Touch the door. I dare you." }, { `say`, 2, `Fine. It's just a door.` },
			{ `prompt`, 2, `Stop them`, 8 },
		};
		Pressed = { Lines = { { 2, `...Yeah. Maybe not.` } }; Helper = true; Size = 1 };
		Missed = { Lines = { { 2, `It's... cold. Why is it cold?` } }; Size = 2 };
	};
	RegionCooldown = 600;
	SeeRange = 60;
	TickSeconds = 5;
	TryChance = 0.15; -- per tick, when a scene fits the place and time
}
