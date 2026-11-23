--[[ (2.38) Dialogue art ids (group 15981569). Crests uploaded 2026-11-22 (art/ui/hud/out/dialogue/ids.json).
	Staged as Dl<Piece>[<Race>].png; filled by tools/quietcorners/harness/ids.py. ]]
return {
	Crest = { Athletes = 125526182544004; Choir = 115415145538112; Court = 131064465186809; Delinquents = 89893229015938; Ink = 119107806148335; Ordinary = 103447597440204; Pack = 129141861458358; Unaffiliated = 133870303290329; Vigil = 114860166389267 };
	CrestFlip = { Athletes = 76316749978761; Choir = 107120128277090; Court = 87270020294102; Delinquents = 122740491517693; Ink = 101114883166304; Ordinary = 119699734867052; Pack = 105408956760891; Unaffiliated = 92428028361207; Vigil = 74478677001800 };
	CallingCard = { Human = 101540076125957; Priest = 112321751591845; Vampire = 136126226747516; Werewolf = 71140251588188; Ghoul = 90380013950594; Wraith = 78502425048982 };
	ReplyTab = { Human = 109044418319802; Priest = 125626708690687; Vampire = 127263151255715; Werewolf = 79052117944867; Ghoul = 138904778164695; Wraith = 105973416093398 };
	ReplyTabOn = { Human = 134143566470906; Priest = 84946260368636; Vampire = 102525043624722; Werewolf = 127764229719306; Ghoul = 71159695921975; Wraith = 87451833633717 };
	Ribbon = 110041304518907;            -- 1024 x 140 (downscaled from 2048 x 280), a 9-slice
	Nib = 120687772807087;
	ToneKind = 76574805123909;
	ToneSly = 92265011546288;
	ToneThreat = 128686646577476;
	ToneAsk = 80044694296250;
	Slices = {
		Ribbon = Rect.new(120, 35, 904, 105);
	};
	Boxes = {
		CallingCard = { 235 / 1040, 34 / 240, 988 / 1040, 206 / 240 };
		Ribbon = { 0.10, 0.20, 0.90, 0.80 };
		ReplySocket = { 26 / 1000, 20 / 128, 114 / 1000, 108 / 128 };
		ReplyText = { 132 / 1000, 24 / 128, 948 / 1000, 104 / 128 };
	};
}
