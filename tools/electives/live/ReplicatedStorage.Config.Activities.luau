--[[
	Class activities (shared).

	Each subject from Config.Classes gets a short, arcade-style minigame graded by the
	teacher. Passing raises your class level (harder next time) and pays Yen, once per
	class period. Replaying an already-passed period is practice (no rewards).
]]

return {
	IntroSeconds = 3;        -- title card + 3-2-1 before the game starts
	PassPercent = 70;        -- C or better passes
	MaxLevel = 5;

	Grades = {
		{ Letter = `A+`; Min = 97 };
		{ Letter = `A`;  Min = 90 };
		{ Letter = `B`;  Min = 80 };
		{ Letter = `C`;  Min = 70 };
		{ Letter = `D`;  Min = 60 };
		{ Letter = `F`;  Min = 0 };
	};

	RewardYen = { [`A+`] = 20; A = 15; B = 10; C = 6 };

	Subjects = {
		Mathematics = { Type = `MathQuiz`;     Title = `Pop Quiz`;        Tagline = `Answer fast. Keys 1-4 or tap. The bell won't wait.` };
		Chemistry   = { Type = `LabRhythm`;    Title = `Lab Mix`;         Tagline = `Drop ingredients on the line: D F J K or tap. Too many slips and... BOOM.` };
		English     = { Type = `WordScramble`; Title = `Word Scramble`;   Tagline = `Type or tap the letters. Enter to check.` };
		History     = { Type = `MemoryMatch`;  Title = `Match the Past`;  Tagline = `Flip two cards. Match each event to its era.` };
		-- (Electives) term electives: Tue/Thu periods 3-4 (Config.Classes.For). Bench = full-screen game (Controllers.Gui.Activities)
		Anatomy     = { Type = `AnatomyBench`; Title = `The Bench`;       Tagline = `Pick a tool from the roll: 1-5 or tap. Right-click or B puts it down.`; Bench = true };
	};

	-- Original teacher one-liners shown on the grade sheet.
	TeacherLines = {
		Pass = {
			`Well, well. Somebody did the reading.`;
			`Don't let it go to your head.`;
			`Acceptable. Barely. But acceptable.`;
			`I'll pretend I'm not impressed.`;
		};
		Fail = {
			`I've seen better work from the vending machine.`;
			`See me after class. Actually, don't.`;
			`Were you even awake?`;
			`Try again before I start a file on you.`;
		};
		Practice = {
			`Extra credit doesn't exist, but sure, keep practicing.`;
		};
	};
}
