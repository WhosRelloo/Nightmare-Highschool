--[[ (2.38) Dialogue art ids (group 15981569). Crests uploaded 2026-11-22 (art/ui/hud/out/dialogue/ids.json).
	Staged as Dl<Piece>[<Race>].png; filled by tools/quietcorners/harness/ids.py. ]]
return {
	Crest = { Athletes = 125526182544004; Choir = 115415145538112; Court = 131064465186809; Delinquents = 89893229015938; Ink = 119107806148335; Ordinary = 103447597440204; Pack = 129141861458358; Unaffiliated = 133870303290329; Vigil = 114860166389267 };
	CrestFlip = { Athletes = 76316749978761; Choir = 107120128277090; Court = 87270020294102; Delinquents = 122740491517693; Ink = 101114883166304; Ordinary = 119699734867052; Pack = 105408956760891; Unaffiliated = 92428028361207; Vigil = 74478677001800 };
	CallingCard = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 };
	ReplyTab = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 };
	ReplyTabOn = { Human = 0; Priest = 0; Vampire = 0; Werewolf = 0; Ghoul = 0; Wraith = 0 };
	Ribbon = 0;            -- 1024 x 140 (downscaled from 2048 x 280), a 9-slice
	Nib = 0;
	ToneKind = 0;
	ToneSly = 0;
	ToneThreat = 0;
	ToneAsk = 0;
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
