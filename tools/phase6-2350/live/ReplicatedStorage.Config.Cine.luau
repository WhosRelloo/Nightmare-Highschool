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
	};
	TimeoutPad = 5;    -- doc 04 §6: Length + 5 s, then Done is forced
	StartGrace = 15;   -- how long a client may take to get ready (the main menu finishing) before the timer starts anyway
	GroupLead = 1.5;   -- a group cut starts this long after the server sends it, so every client starts together
	SkipGrace = 0.3;   -- doc 04 §4: control comes back with a short input grace
	GradeCard = 2.5;   -- (2.25.0) seconds an interactive cut's grade card holds
}
