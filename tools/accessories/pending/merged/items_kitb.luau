	-- Kit B "The Headmaster's Circle" (batch 8): the admin regalia, staff only, never sold (the greatcoat, Kit B 2, is in the coat batch)
	{ Id = `regalia-crow-mantle`; Name = `Murder of Crows Mantle`; Slot = `Shoulders`; Model = `CrowMantle`; Pieces = { `CrowMantle`, `MantleCrows` }; Admin = true; Tint = `Ember`; Kit = B };
	{ Id = `regalia-thorn-crown`; Name = `Crown of Thorned Brass`; Slot = `Hat`; Model = `ThornCrown`; Piece = `ThornCrown`; Admin = true; Tint = `Crimson`; Kit = B };
	{ Id = `regalia-raven-pauldron`; Name = `Raven-Skull Pauldron`; Slot = `Shoulders`; Model = `RavenPauldron`; Piece = `RavenPauldron`; Admin = true; Tint = `Ember`; Kit = B };
	{ Id = `regalia-iron-keys`; Name = `Three Iron Keys`; Slot = `Halo`; Model = `IronKeys`; Piece = `IronKeys`; Admin = true; Tint = `Ember`; Kit = B };
	{ Id = `regalia-shadow-trail`; Name = `Shadow Trail`; Slot = `Trail`; Model = `ShadowTrail`; Piece = `ShadowTrail`; Admin = true; Tint = `Ember`; Kit = B };
	{ Id = `regalia-chained-ledger`; Name = `Floating Chained Ledger`; Slot = `Familiar`; Model = `ChainedLedger`; Pieces = { `Ledger`, `LedgerChain` }; Admin = true; Tint = `Crimson`; Kit = B };
	{ Id = `regalia-sigil-halo`; Name = `Crimson Sigil Halo`; Slot = `Halo`; Model = `SigilHalo`; Piece = `SigilHalo`; Admin = true; Tint = `Crimson`; Kit = B };
	{ Id = `regalia-seal-of-office`; Name = `Seal of Office`; Slot = `Collar`; Model = `SealOfOffice`; Piece = `SealOfOffice`; Admin = true; Tint = `Crimson`; Kit = B };
	{ Id = `regalia-signet`; Name = `Headmaster's Signet`; Slot = `Ring`; Model = `HeadSignet`; Piece = `HeadSignet`; Admin = true; Tint = `Crimson`; Kit = B };
	{ Id = `regalia-staff`; Name = `Staff of Office`; Slot = `Hand`; Model = `OfficeStaff`; Piece = `OfficeStaff`; Admin = true; Tint = `Crimson`; Kit = B };
	{ Id = `regalia-observer-mask`; Name = `Observer Half-Mask`; Slot = `Face`; Model = `ObserverMask`; Piece = `ObserverMask`; Admin = true; Tint = `Crimson`; Kit = B };
-- conflicts
	{ `regalia-crow-mantle`, `Neck` };      -- the mantle closes over the throat (its iron clasp) and lies round the neck where the ties, scarves and pendant chains go
	{ `regalia-crow-mantle`, `Collar` };    -- the collars, torc and chain of office lie round the neck under its feathers
	{ `regalia-crow-mantle`, `Sash` };      -- the sashes and the bandolier cross the left shoulder under the feathers and the crow
	{ `regalia-crow-mantle`, `Back` };      -- the bag and crossbow straps cross the shoulders under it
	{ `regalia-crow-mantle`, `familiar-crow` };   -- the familiar perches on the left shoulder, where crow A is
	{ `regalia-crow-mantle`, `hat-mourning` };    -- the veil drapes onto the shoulders over the crows
	{ `regalia-crow-mantle`, `hood-tattered` };   -- the hood's cowl rests on the shoulders where the mantle and the crows are
	{ `regalia-seal-of-office`, `Sash` };   -- the chain crosses the chest top where every sash and the bandolier cross
	{ `regalia-seal-of-office`, `Back` };   -- and where the bag and crossbow straps cross
	{ `regalia-seal-of-office`, `tie-school` };          -- the medallion and the chain's U hang over the tie
	{ `regalia-seal-of-office`, `pendant-crystal` };     -- the pendant chains lie round the neck on the same line
	{ `regalia-seal-of-office`, `necklace-wolf-fang` };
	{ `regalia-seal-of-office`, `pendant-scythe` };
	{ `regalia-seal-of-office`, `fur-torn` };            -- the mantles cover the shoulders where the chain lies
	{ `regalia-seal-of-office`, `shawl-grave-moss` };
	{ `regalia-sigil-halo`, `hat-top` };      -- measured: the brims (scaled and lifted for the hair) reach back through the ring as it spins
	{ `regalia-sigil-halo`, `hat-hunter` };
	{ `regalia-sigil-halo`, `hat-witch` };
	{ `regalia-sigil-halo`, `hat-tricorn` };
	{ `regalia-sigil-halo`, `hat-bowler` };
	{ `regalia-sigil-halo`, `hat-mourning` };
	{ `regalia-sigil-halo`, `hood-tattered` };   -- the hood's back rises into the ring
	{ `regalia-sigil-halo`, `cape:CapeMidnight` };   -- the Midnight Lord's high collar stands behind the head, in the ring
	{ `regalia-chained-ledger`, `Arms` };     -- the iron cuff is on the right wrist, where the bracers and gauntlets go
	{ `regalia-chained-ledger`, `cape:CapeWardenMantle` };   -- the capes hang over the right arm, where the ledger floats and its chain runs
	{ `regalia-chained-ledger`, `cape:CapeReaperShroud` };
	{ `regalia-chained-ledger`, `cape:CapeCaptain` };
	{ `regalia-chained-ledger`, `cape:CapeMidnight` };
	{ `regalia-staff`, `pauldrons-blackened` };   -- the staff stands in front of the right arm, through the right pauldron's lames
	{ `regalia-staff`, `cape:CapeWardenMantle` };   -- the Warden's mantle drapes over the front of the right arm, where the staff stands
	{ `regalia-raven-pauldron`, `hat-mourning` };   -- measured: as the left arm swings, the skull meets the veil at two hairs' fits
	{ `regalia-seal-of-office`, `familiar-crow` };   -- the familiar perches on the left shoulder top, on the chain
	{ `regalia-crow-mantle`, `Coat` };      -- (measured against the coat batch's first build) the coats' collars and shoulders lie under the mantle and the crows
	{ `regalia-seal-of-office`, `Coat` };   -- the coats' collars stand round the neck where the chain lies
	{ `regalia-chained-ledger`, `Coat` };   -- the right sleeve covers the wrist under the cuff
	{ `regalia-raven-pauldron`, `Coat` };   -- the left sleeve's shoulder lies under the pauldron's lames
	{ `regalia-staff`, `Coat` };            -- the right sleeve and the coat's right tail meet the staff in front of the arm
