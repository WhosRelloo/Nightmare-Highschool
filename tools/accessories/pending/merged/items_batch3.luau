	-- Kit A 13-16: race-flavoured pieces (batch 3; cosmetic only, anyone may wear them, Race is never set from them)
	{ Id = `clasp-opera`; Name = `Opera-Cape Clasp`; Slot = `Collar`; Model = `OperaClasp`; Price = 520; Race = `Vampire`; Kit = A };
	{ Id = `ring-bat-signet`; Name = `Bat Signet Ring`; Slot = `Ring`; Model = `BatSignet`; Price = 380; Race = `Vampire`; Kit = A };
	{ Id = `torc-moonstone`; Name = `Moonstone Torc`; Slot = `Collar`; Model = `MoonTorc`; Price = 480; Race = `Werewolf`; Kit = A };
	{ Id = `necklace-wolf-fang`; Name = `Wolf-Fang Necklace`; Slot = `Neck`; Model = `FangNecklace`; Price = 260; Race = `Werewolf`; Kit = A };
	{ Id = `fur-torn`; Name = `Torn Shoulder Fur`; Slot = `Shoulders`; Model = `TornFur`; Price = 650; Race = `Werewolf`; Kit = A };
	{ Id = `lantern-ghoul`; Name = `Ghoul's Hook Lantern`; Slot = `Hip`; Model = `GhoulLantern`; Price = 720; Race = `Ghoul`; Kit = A };
	{ Id = `shawl-grave-moss`; Name = `Grave-Moss Shawl`; Slot = `Shoulders`; Model = `MossShawl`; Price = 560; Race = `Ghoul`; Kit = A };
	{ Id = `hood-tattered`; Name = `Tattered Specter Hood`; Slot = `Hat`; Model = `TatteredHood`; Price = 850; Race = `Specter`; Kit = A };
	{ Id = `pendant-scythe`; Name = `Scythe Pendant`; Slot = `Neck`; Model = `ScythePendant`; Price = 300; Race = `Specter`; Kit = A };
-- conflicts
	{ `clasp-opera`, `tie-school` };      -- the clasp's chains cross the throat where a tie's knot stands (deep chests push the knot through them)
	{ `clasp-opera`, `tie-bow` };         -- the bow's loops fill the space between the two clasps
	{ `necklace-wolf-fang`, `Sash` };     -- the fangs and beads hang on the chest where a sash crosses
	{ `pendant-scythe`, `Sash` };         -- so does the scythe
	{ `cape:*`, `necklace-wolf-fang` };   -- every cape's collar lies on the torso top round the neck, where the cords run
	{ `cape:*`, `pendant-scythe` };
	{ `fur-torn`, `Back` };               -- the mantles cover the shoulders and the upper back, where bag straps cross
	{ `fur-torn`, `Sash` };
	{ `cape:*`, `fur-torn` };
	{ `shawl-grave-moss`, `Back` };
	{ `shawl-grave-moss`, `Sash` };
	{ `cape:*`, `shawl-grave-moss` };
	{ `hood-tattered`, `fur-torn` };      -- the hood's cowl rests on the shoulders, inside the fur's pile
	{ `cape:CapeWardenMantle`, `hood-tattered` };   -- four of the capes rise round the neck into the cowl
	{ `cape:CapeReaperShroud`, `hood-tattered` };
	{ `cape:CapeCaptain`, `hood-tattered` };
	{ `cape:CapeMidnight`, `hood-tattered` };
