--[[ (2.38) Quiet Corners art ids (group 15981569). Staged by art/ui/hud/export_quietcorners_upload.py as
	Qc<Piece><Race>.png / Qc<Piece>.png; filled by tools/quietcorners/harness/ids.py. 0 = not uploaded:
	Functions.QuietCorners.Image falls back to the Human trim, then the controller draws today's kit art. ]]
return {
	Slip = { Human = 89393253968500; Priest = 127506149327558; Vampire = 131216553991094; Werewolf = 70378847352415; Ghoul = 124114427810384; Wraith = 98090747364443 };
	PromptCap = { Human = 71604775752807; Priest = 105184036885199; Vampire = 76018939803972; Werewolf = 85465357353781; Ghoul = 86727839483543; Wraith = 131315068244353 };
	PromptTag = { Human = 112651460531721; Priest = 94525071319652; Vampire = 82975749057211; Werewolf = 85474079816319; Ghoul = 99441280100830; Wraith = 85876381186954 };
	PromptPip = { Human = 133728312972189; Priest = 123495682710127; Vampire = 101988134771008; Werewolf = 111264645370856; Ghoul = 88196108596876; Wraith = 74686616062003 };
	CompassStrip = { Human = 125180911934323; Priest = 94110303079072; Vampire = 116405466960701; Werewolf = 78864465693883; Ghoul = 137410714545776; Wraith = 118086650511952 };
	CompassLubber = { Human = 111536898546854; Priest = 119267157857261; Vampire = 79621804946220; Werewolf = 111657884214508; Ghoul = 105739804897094; Wraith = 92226856459360 };
	SkipRing = { Human = 138990745364791; Priest = 114622484155010; Vampire = 103327153882250; Werewolf = 139639885596121; Ghoul = 115581610554235; Wraith = 120486122549520 };
	BookCorner = { Human = 78787579356871; Priest = 135746357884483; Vampire = 108966011200368; Werewolf = 132713349021608; Ghoul = 90901588081510; Wraith = 93960230784212 };
	PlateTrim = { Human = 137230334910858; Priest = 113072097182200; Vampire = 132920524713697; Werewolf = 83054354740305; Ghoul = 119421929584288; Wraith = 82046892631058 }; -- tier C: the Bell Tower plate, after R2
	PromptCapFill = 76289339724658;
	SkipRingFill = 88016711278856;
	CompassTicks = 104707057644934;      -- greyscale, tinted bone; 600 x 48 = 30 degrees
	BookTab = 116709505235572;
	BookTabOn = 91470753259058;
	BookTL = 132659073667004;            -- the book, in quadrants (1024 x 582 each)
	BookTR = 131798143112089;
	BookBL = 124622920158632;
	BookBR = 86920093089341;
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
