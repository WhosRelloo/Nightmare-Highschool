	{ Id = `bandolier-hunter`; Name = `Hunter's Bandolier`; Slot = `Sash`; Model = `Bandolier`; Price = 650; Kit = A };
	{ Id = `pauldrons-blackened`; Name = `Blackened Steel Pauldrons`; Slot = `Shoulders`; Model = `Pauldrons`; Price = 850; Kit = A };
	{ Id = `gorget-steel`; Name = `Riveted Steel Gorget`; Slot = `Collar`; Model = `Gorget`; Price = 550; Kit = A };
	{ Id = `bracers-hunter`; Name = `Hunter's Bracers`; Slot = `Arms`; Model = `Bracers`; Price = 450; Kit = A };
	{ Id = `gauntlets-hunter`; Name = `Hunter's Gauntlets`; Slot = `Arms`; Model = `Gauntlets`; Price = 600; Kit = A };
	{ Id = `crossbow-hunter`; Name = `Hunter's Crossbow`; Slot = `Back`; Model = `Crossbow`; Price = 900; Kit = A };
-- conflicts
	{ `gorget-steel`, `Neck` };   -- the gorget's top lame covers the throat and the knot
	{ `gorget-steel`, `Sash` };   -- its crescent lames cover the chest top where every sash and the bandolier cross
	{ `cape:*`, `Shoulders` };    -- every cape hangs over both shoulders, where the pauldrons sit
	{ `gauntlets-hunter`, `Ring` };   -- the back-of-hand plate and knuckle lames cover the hand where a ring is worn
