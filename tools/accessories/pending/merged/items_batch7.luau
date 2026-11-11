	-- Kit A 7 and Kit B 2: the coats (batch 7; one coat builder: shell, sleeves, rigged coattails worn together)
	{ Id = `coat-delinquent`; Name = `Delinquent's Long Coat`; Slot = `Coat`; Model = `LongCoat`; Pieces = { `LongCoatShell`, `LongCoatTailL`, `LongCoatTailR`, `LongCoatSleeveL`, `LongCoatSleeveR` }; Price = 1100; Kit = A };
	{ Id = `regalia-greatcoat`; Name = `Headmaster's Greatcoat`; Slot = `Coat`; Model = `Greatcoat`; Pieces = { `GreatcoatShell`, `GreatcoatTailL`, `GreatcoatTailR`, `GreatcoatSleeveL`, `GreatcoatSleeveR` }; Admin = true; Tint = `Crimson`; Kit = B };
-- conflicts
	{ `cape:*`, `Coat` };            -- every cape hangs over the shoulders and the back, over the coat's collar and shoulders
	{ `Coat`, `Sash` };              -- the sashes and the bandolier cross the shoulder top and the back under the coat
	{ `Coat`, `Back` };              -- the bag straps and the crossbow's sling cross the shoulder and the back; the satchel hangs on the right tail
	{ `Coat`, `Shoulders` };         -- the pauldrons sit on the sleeves' shoulder caps; the furs and mantles on the collar
	{ `Coat`, `Arms` };              -- the bracers and gauntlets wrap the forearm inside the sleeve
	{ `Coat`, `Lapel` };             -- the clique pins sit on the left breast, under the coat's front panel
	{ `Coat`, `Hip` };               -- the grimoire and the hook lantern hang beside the right hip, where the right tail hangs
	{ `Coat`, `Belt` };              -- the potion belt goes round the waist under the shell
	{ `Coat`, `Watch` };             -- the pocket watch hangs at the right front, under the front panel
	{ `Coat`, `familiar-crow` };     -- the crow perches on the left shoulder, on the collar
	{ `Coat`, `pendant-crystal` };   -- the chain lies round the neck on the shoulder tops, under the collar
	{ `Coat`, `scarf-knit-crimson` };   -- the scarf's roll lies round the neck on the collar, its tails over the lapels
	{ `Coat`, `scarf-knit-violet` };
	{ `Coat`, `torc-moonstone` };       -- (coat helper, measured) the shell's collar sits where the torc does
	{ `Coat`, `necklace-wolf-fang` };   -- the shell covers the cord
	{ `Coat`, `pendant-scythe` };       -- and the chain
	{ `Coat`, `hood-tattered` };        -- the hood's cowl lies on the shoulders under the collar
