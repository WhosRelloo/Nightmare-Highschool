	-- batch 5: magic (Kit A 21-24)
	{ Id = `halo-rune`; Name = `Floating Rune Halo`; Slot = `Halo`; Model = `RuneHalo`; Piece = `RuneHalo`; Price = 850; Kit = A };
	{ Id = `sigils-orbiting`; Name = `Orbiting Sigils`; Slot = `Halo`; Model = `OrbitSigils`; Piece = `OrbitSigils`; Price = 900; Kit = A };
	{ Id = `familiar-crow`; Name = `Crow Familiar`; Slot = `Familiar`; Model = `CrowFamiliar`; Piece = `Crow`; Price = 800; Kit = A };
	{ Id = `pendant-crystal`; Name = `Caged Crystal Pendant`; Slot = `Neck`; Model = `CrystalPendant`; Piece = `CrystalPendant`; Price = 450; Kit = A };
	{ Id = `belt-potion`; Name = `Potion Belt`; Slot = `Belt`; Model = `PotionBelt`; Piece = `PotionBelt`; Price = 550; Kit = A };
-- conflicts
	{ `familiar-crow`, `Sash` };       -- the crow perches on the left shoulder top, where both sashes cross it
	{ `familiar-crow`, `Back` };       -- and where the satchel's and the messenger bag's straps cross it
	{ `familiar-crow`, `cape:*` };     -- every cape lies over both shoulder tops
	{ `belt-potion`, `bag-messenger` };   -- the messenger bag sits on the lower back across the belt line
	{ `belt-potion`, `tie-school` };      -- the tie's blade hangs past the belt line (fitted to the chest, it stands off the waist)
	{ `pendant-crystal`, `cape:*` };      -- the chain lies round the neck on the shoulder tops, under every cape's collar
	{ `halo-rune`, `Hat` };              -- hats are scaled and lifted per hair; the tall ones reach up through the halo
	{ `sigils-orbiting`, `hat-hunter` };   -- measured: under the hunter hat's hair fits (5 hairs) its brim meets the orbit
	{ `sigils-orbiting`, `hat-witch` };    -- and the witch hat's brim (4 hairs)
