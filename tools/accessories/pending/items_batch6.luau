	-- Kit A 25-28: civilian (batch 6)
	{ Id = `watch-pocket`; Name = `Brass Pocket Watch`; Slot = `Watch`; Model = `PocketWatch`; Price = 480; Kit = A };
	{ Id = `umbrella-crook`; Name = `Crook Umbrella`; Slot = `Hand`; Model = `Umbrellas`; Piece = `CrookUmbrella`; Price = 320; Kit = A };
	{ Id = `parasol-lace`; Name = `Lace Parasol`; Slot = `Hand`; Model = `Umbrellas`; Piece = `LaceParasol`; Price = 420; Kit = A };
	{ Id = `lantern-candle`; Name = `Candle Lantern`; Slot = `Hand`; Model = `CandleLantern`; Price = 560; Kit = A };
	{ Id = `scarf-knit-crimson`; Name = `Crimson Striped Scarf`; Slot = `Neck`; Model = `Scarves`; Piece = `ScarfStripe`; Price = 260; Kit = A };
	{ Id = `scarf-knit-violet`; Name = `Grey-Violet Scarf`; Slot = `Neck`; Model = `Scarves`; Piece = `ScarfViolet`; Price = 260; Kit = A };
-- conflicts
	{ `cape:*`, `scarf-knit-crimson` };   -- every cape's collar and shoulders lie where the scarf's roll goes round the neck
	{ `cape:*`, `scarf-knit-violet` };
	{ `scarf-knit-crimson`, `Collar` };   -- (measured against batches 3-5) the torc and the opera clasp sit round the throat in the roll
	{ `scarf-knit-violet`, `Collar` };
	{ `scarf-knit-crimson`, `bandolier-hunter` };   -- the bandolier's thick strap crosses the chest under both tails
	{ `scarf-knit-violet`, `bandolier-hunter` };
	{ `scarf-knit-crimson`, `belt-potion` };   -- the long tail hangs past the belt line
	{ `scarf-knit-violet`, `belt-potion` };
	{ `scarf-knit-crimson`, `hood-tattered` };   -- the hood's cowl rests on the shoulders where the roll goes
	{ `scarf-knit-violet`, `hood-tattered` };
	{ `scarf-knit-crimson`, `familiar-crow` };   -- the crow perches on the left shoulder top, on the roll
	{ `scarf-knit-violet`, `familiar-crow` };
	{ `watch-pocket`, `belt-potion` };   -- the watch hangs at the waist front across the belt line
