	-- Kit A 8: tricorn, top hat and bowler, each with a crimson band
	{ Id = `hat-tricorn`; Name = `Crimson-Banded Tricorn`; Slot = `Hat`; Model = `Hats`; Piece = `Tricorn`; Price = 450; Kit = A };
	{ Id = `hat-top`; Name = `Crimson-Banded Top Hat`; Slot = `Hat`; Model = `Hats`; Piece = `TopHat`; Price = 500; Kit = A };
	{ Id = `hat-bowler`; Name = `Crimson-Banded Bowler`; Slot = `Hat`; Model = `Hats`; Piece = `Bowler`; Price = 400; Kit = A };
	-- 9: veiled mourning hat and fascinator (feminine, by the clothing kits' gender rule)
	{ Id = `hat-mourning`; Name = `Veiled Mourning Toque`; Slot = `Hat`; Model = `MourningHats`; Pieces = { `MourningToque`, `MourningVeil` }; Price = 550; Gender = `Female`; Kit = A };
	{ Id = `hat-fascinator`; Name = `Crimson Fascinator`; Slot = `Hat`; Model = `MourningHats`; Pieces = { `Fascinator`, `FascVeil` }; Price = 480; Gender = `Female`; Kit = A };
	-- 10, 11: the crooked witch hat, the hunter's wide-brim
	{ Id = `hat-witch`; Name = `Crooked Witch Hat`; Slot = `Hat`; Model = `WitchHat`; Price = 520; Kit = A };
	{ Id = `hat-hunter`; Name = `Hunter's Wide-Brim`; Slot = `Hat`; Model = `HunterHat`; Price = 600; Kit = A };
	-- 12: masquerade half-masks
	{ Id = `mask-lace`; Name = `Black Lace Half-Mask`; Slot = `Face`; Model = `Masks`; Pieces = { `LaceMask`, `LaceMaskTrim` }; Price = 380; Kit = A };
	{ Id = `mask-bone`; Name = `Carved Bone Half-Mask`; Slot = `Face`; Model = `Masks`; Piece = `BoneMask`; Price = 420; Kit = A };
	{ Id = `mask-gilt`; Name = `Gilt Half-Mask`; Slot = `Face`; Model = `Masks`; Piece = `GiltMask`; Price = 650; Kit = A };
-- conflicts
	{ `cape:CapeMidnight`, `Hat` };   -- the Midnight Lord's high collar meets the brims at their hair fits (tricorn, top hat, hunter, witch, veils; acc_hatcapes.py)
	{ `hat-mourning`, `cape:*` };     -- the mourning veil drapes to the shoulders, onto every cape's collar
	{ `familiar-crow`, `hat-mourning` };   -- the veil drapes to the shoulders, where the crow perches (cross-batch check)
