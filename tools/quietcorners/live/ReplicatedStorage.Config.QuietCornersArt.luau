--[[ (2.38) Quiet Corners art ids (group 15981569). Staged by art/ui/hud/export_quietcorners_upload.py as
	Qc<Piece><Race>.png / Qc<Piece>.png; filled by tools/quietcorners/harness/ids.py. 0 = not uploaded:
	Functions.QuietCorners.Image falls back to the Human trim, then the controller draws today's kit art. ]]
return {
	Slip = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 };
	PromptCap = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 };
	PromptTag = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 };
	PromptPip = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 };
	CompassStrip = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 };
	CompassLubber = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 };
	SkipRing = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 };
	BookCorner = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 };
	PlateTrim = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 }; -- tier C: the Bell Tower plate, after R2
	PromptCapFill = 0;
	SkipRingFill = 0;
	CompassTicks = 0;      -- greyscale, tinted bone; 600 x 48 = 30 degrees
	BookTab = 0;
	BookTabOn = 0;
	BookTL = 0;            -- the book, in quadrants (1024 x 582 each)
	BookTR = 0;
	BookBL = 0;
	BookBR = 0;
	Slices = {
		PromptTag = Rect.new(80, 16, 560, 112);   -- 640 x 128
	};
	Boxes = {
		Slip = { 0.14, 0.06, 0.97, 0.78 };
		PromptTag = { 0.11, 0.08, 0.90, 0.92 };
		PromptCap = { 0.12, 0.15, 0.88, 0.85 };
		CompassStrip = { 24 / 560, 8.4 / 52, 536 / 560, 43.6 / 52 };
		BookLeft = { 110 / 2048, 96 / 1164, 1000 / 2048, 1068 / 1164 };
		BookRight = { 1170 / 2048, 96 / 1164, 1938 / 2048, 1068 / 1164 };
	};
}
