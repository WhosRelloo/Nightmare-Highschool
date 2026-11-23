--[[
	Cine config (shared, data only). The cut definitions (shots, actors, lines) live in ReplicatedStorage.Cinematics.<Id>;
	this file is what the server needs to run a cut: its length (for the timeout), whether it's a story cut, its name.

	Cuts[Id] = {
		Name     shown on the skip button and in the journal's "Watch again"
		Length   seconds (the server forces Done at Length + TimeoutPad after the client says it began)
		Set      the set it's staged on: workspace.NHCineSets.<Set> holds its marks (one set per place, so a cut ports
		         to the Map by placing the same marks in the real rooms)
		Replay   true: once seen, the journal can play it again (always skippable then)
		Arrive   a mark in the set: the first time (not a replay), the viewer's real character is placed there as the cut
		         starts, so the cut can end behind their shoulder where they now stand

		Interactive  true: the cut's module has a Def.Graph (segments and prompts); Length is its longest path
		             (CineJudge.LongestPath) plus the grade card
		ShowGrade    false: no grade card at the end (a story beat with one prompt); the grade is still kept
		Rewards      { S = yen, A = yen, B = yen }: a bonus by grade, on the first viewing only
		Hidden       true: never listed in the Journal (test cuts)
	}
]]
return {
	Cuts = {
		-- (2.25.0) interactive: the longest path is 33.7 s (CineJudge.LongestPath); no grade card for one story prompt
		Prologue = { Name = `Roll Call`; Length = 35; Set = `RollCall`; Replay = true; Arrive = `Arrive`; Interactive = true; ShowGrade = false };
		-- (2.26.0) COLLECTED reads the fight's FileKept decision (the torn page)
		Collected = { Name = `Collected`; Length = 13; Set = `Hall`; Replay = true; Flags = { `FileKept` } };
		-- (2.26.0) Chapter One's finale: the longest path is 52.0 s (CineJudge.LongestPath, slow-mo prompts included) + the grade card + 1
		Strikethrough = { Name = `The Strikethrough`; Length = 56; Set = `Strike`; Replay = true; Interactive = true; Rewards = { S = 15; A = 10; B = 5 } };
		-- (2.25.0) a test cut for the interactive director (TestBridge / harness only; never in a quest)
		__QteTest = { Name = `QTE test`; Length = 30; Set = `Hall`; Replay = true; Interactive = true; Hidden = true };
		-- (2.35.0) seamless (spec 2026-11-20): the real character acts, the camera glides in and out, nothing anchors
		-- (task 14 follow-up) A cut with walk-and-talk beats MUST list its beat segments in Beats = { <Segment> = true }: the server holds the timeout
		-- only while a listed beat runs, so an unlisted beat is timed out mid-beat (Length + TimeoutPad) and the cut ends under the player.
		__SeamlessTest = { Name = `Seamless test`; Length = 18; Set = `BusStop`; Seamless = true; Replay = true; Hidden = true; Beats = { Walk = true } };
		-- (task 8 fix round 1) beatcheck: Length 6 is shorter than the cut on purpose (a beat holds the timeout)
		__BeatHoldTest = { Name = `Beat hold test`; Length = 6; Set = `BusStop`; Seamless = true; Replay = true; Hidden = true; Beats = { Hold = true } };
		-- (task 11 fix round 1, ruling I4) Replay = false for the two tutorial walk-and-talk cuts until seamless replay staging is
		-- designed (T12/T13): a journal replay outside Wickfield has no cast and no player-private set, and a beat's suspended timeout
		-- never ends it. Their first viewing is unchanged (a first viewing is the only way to play them)
		-- (task 12 fix round 1, ruling I2) Resume: where Tutorial.Resume puts a player who enters or respawns in Wickfield with a checkpoint
		-- "<Cut>:<Segment>": Marks maps each segment the cut reports to a mark of its Set; End is the mark a Seen/finished cut resumes at.
		-- No name guessing: an unmapped segment (or a missing mark) warns and leaves the player where the game put them.
		TutorialBus = { Name = `The Bus`; Length = 34; Set = `BusStop`; Seamless = true; Replay = false;
			Resume = { Marks = { Start = `Stand`; Main = `Stand` }; End = `Stand` } };
		TutorialSneak = { Name = `Sneaking Out`; Length = 90; Set = `Garden`; Seamless = true; Replay = false; Beats = { Garden = true; Hide = true };
			Resume = { Marks = { Start = `Start`; Garden = `Start`; Hide = `Start`; Fence = `FenceZone` }; End = `FenceLand` } };
	};
	-- (2.35.0) per-scene grades for seamless cuts, eased over 1 s (spec §4.1)
	Looks = {
		Night = { contrast = 0.1; saturation = -0.12; tint = { 214, 228, 240 }; bloom = { intensity = 0.55; size = 40; threshold = 0.92 } };
		Morning = { contrast = 0.06; saturation = 0.04; tint = { 255, 238, 214 }; bloom = { intensity = 0.4; size = 32; threshold = 0.95 } };
		BusStop = { contrast = 0.14; saturation = -0.28; tint = { 206, 220, 232 }; bloom = { intensity = 0.7; size = 48; threshold = 0.9 } };
	};
	GradeEase = 1.0;
	TimeoutPad = 5;    -- doc 04 §6: Length + 5 s, then Done is forced
	StartGrace = 15;   -- how long a client may take to get ready (the main menu finishing) before the timer starts anyway
	GroupLead = 1.5;   -- a group cut starts this long after the server sends it, so every client starts together
	SkipGrace = 0.3;   -- doc 04 §4: control comes back with a short input grace
	GradeCard = 2.5;   -- (2.25.0) seconds an interactive cut's grade card holds
}
