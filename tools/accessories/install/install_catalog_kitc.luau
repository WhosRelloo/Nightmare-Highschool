if game.PlaceId ~= 98950102230473 then return "WRONG PLACE" end
local m = game.ReplicatedStorage.Config.Accessories
if #m.Source ~= 26970 then return "ABORT: Config.Accessories changed since it was read (" .. #m.Source .. " bytes)" end
local SS = game:GetService("ServerStorage")
local bk = SS:FindFirstChild("NH_Backup") or Instance.new("Folder", SS)
bk.Name = "NH_Backup"
local old = m:Clone()
old.Name = "Config_Accessories_pre_kitc"
old.Parent = bk
m.Source = [==[--[[
	Config.Accessories: the 3D accessory kits (cosmetic only: no stats, never Race).
	  Kit A "Player accessories" (28 designs): bought for Yen at the School Store (Accessories tab), worn at a wardrobe.
	  Kit C "The Night School Wardrobe" (approved 2026-11-11, built in batches): C1 coats and jackets (11; their skirts ride
	  the legs, Controllers.Character.BodyFollow), C2 masks (8). Sold at the School Store like Kit A.
	  Kit B "The Headmaster's Circle" (11 designs): Admin = true. Staff only (player attribute NHStaff >= 1, set by
	  Features.Admin), never sold, checked on the server (UI.Appearance's look check and WearAccessories).
	Worn: the look field Acc (UI.Appearance), a comma list of item ids, at most one per slot.
	Owned: Identity.Accessories (ids), saved through Data.UpdateState SetIdentity.
	Templates: ReplicatedStorage.NHAccessories.<Model>.<Piece> (a rigged or rigid MeshPart). An item whose template
	isn't there yet is hidden everywhere (Accessories.Ready). Art: art/characters/accessories (docs/Accessories.md).

	Item fields
	  Id        stable save id (never reuse or rename)
	  Name      shown name
	  Slot      one of Accessories.Slots
	  Model     template model; Pieces = its MeshParts worn together (default: Piece, or every part of the model)
	  Price     Yen at the School Store (nil = not sold: earned or staff)
	  Gender    "Male" | "Female" | "Unisex" (default Unisex): the Wardrobe and the server allow your gender only
	  Clique    a clique pin: sold only to members of that clique (Social.Cliques membership)
	  Admin     Kit B: staff only
	  Race      race-flavoured design (cosmetic only, anyone may wear it; the race is never set from it)
]]
local Accessories = {}

Accessories.Slots = { `Hat`, `Face`, `Collar`, `Neck`, `Lapel`, `Sash`, `Shoulders`, `Back`, `Hip`, `Arms`, `Hand`, `Ring`,
	`Halo`, `Familiar`, `Trail`, `Coat`, `Belt`, `Watch` }
Accessories.SlotNames = {
	Hat = `Hat`; Face = `Mask`; Collar = `Collar`; Neck = `Neck`; Lapel = `Lapel pin`; Sash = `Sash or strap`;
	Shoulders = `Shoulders`; Back = `Back`; Hip = `Hip`; Arms = `Arms`; Hand = `Held`; Ring = `Ring`;
	Halo = `Halo`; Familiar = `Familiar`; Trail = `Trail`; Coat = `Coat`; Belt = `Belt`; Watch = `Pocket watch`;
}

local A, B, C = `A`, `B`, `C`
Accessories.Items = {
	-- Kit A 1: clique crest pins (one per clique; members only)
	{ Id = `pin-vigil`; Name = `Vigil Crest Pin`; Slot = `Lapel`; Model = `CliquePins`; Piece = `PinVigil`; Price = 180; Clique = `Vigil`; Kit = A };
	{ Id = `pin-court`; Name = `Crimson Court Crest Pin`; Slot = `Lapel`; Model = `CliquePins`; Piece = `PinCourt`; Price = 180; Clique = `Court`; Kit = A };
	{ Id = `pin-athletes`; Name = `Athletes Crest Pin`; Slot = `Lapel`; Model = `CliquePins`; Piece = `PinAthletes`; Price = 180; Clique = `Athletes`; Kit = A };
	{ Id = `pin-delinquents`; Name = `Delinquents Crest Pin`; Slot = `Lapel`; Model = `CliquePins`; Piece = `PinDelinquents`; Price = 180; Clique = `Delinquents`; Kit = A };
	{ Id = `pin-pack`; Name = `Pack Crest Pin`; Slot = `Lapel`; Model = `CliquePins`; Piece = `PinPack`; Price = 180; Clique = `Pack`; Kit = A };
	{ Id = `pin-ordinary`; Name = `Ordinary Crest Pin`; Slot = `Lapel`; Model = `CliquePins`; Piece = `PinOrdinary`; Price = 180; Clique = `Ordinary`; Kit = A };
	{ Id = `pin-choir`; Name = `Chapel Choir Crest Pin`; Slot = `Lapel`; Model = `CliquePins`; Piece = `PinChoir`; Price = 180; Clique = `Choir`; Kit = A };
	{ Id = `pin-ink`; Name = `Ink Club Crest Pin`; Slot = `Lapel`; Model = `CliquePins`; Piece = `PinInk`; Price = 180; Clique = `Ink`; Kit = A };
	-- 2: sashes and medals
	{ Id = `sash-prefect`; Name = `Prefect's Sash`; Slot = `Sash`; Model = `Sashes`; Piece = `PrefectSash`; Price = 600; Kit = A };
	{ Id = `sash-head`; Name = `Head Student's Sash`; Slot = `Sash`; Model = `Sashes`; Piece = `HeadSash`; Price = 900; Kit = A };
	-- 3: ties
	{ Id = `tie-school`; Name = `School Tie`; Slot = `Neck`; Model = `SchoolTie`; Price = 120; Kit = A };
	{ Id = `tie-bow`; Name = `Velvet Bow Tie`; Slot = `Neck`; Model = `BowTie`; Price = 150; Kit = A };
	-- 4: bags
	{ Id = `bag-satchel`; Name = `Leather Satchel`; Slot = `Back`; Model = `Satchel`; Price = 450; Kit = A };
	{ Id = `bag-messenger`; Name = `Messenger Bag`; Slot = `Back`; Model = `MessengerBag`; Price = 400; Kit = A };
	-- 5: book strap, the Ink Club's chained grimoire
	{ Id = `book-strap`; Name = `Book Strap`; Slot = `Hand`; Model = `BookStrap`; Price = 220; Kit = A };
	{ Id = `grimoire-chained`; Name = `Chained Grimoire`; Slot = `Hip`; Model = `Grimoire`; Price = 700; Clique = `Ink`; Kit = A };
	-- 6: choir collar and ruff
	{ Id = `collar-choir`; Name = `Choir Collar`; Slot = `Collar`; Model = `ChoirCollar`; Price = 260; Kit = A };
	{ Id = `collar-ruff`; Name = `Falling Ruff`; Slot = `Collar`; Model = `Ruff`; Price = 320; Kit = A };
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
	{ Id = `bandolier-hunter`; Name = `Hunter's Bandolier`; Slot = `Sash`; Model = `Bandolier`; Price = 650; Kit = A };
	{ Id = `pauldrons-blackened`; Name = `Blackened Steel Pauldrons`; Slot = `Shoulders`; Model = `Pauldrons`; Price = 850; Kit = A };
	{ Id = `gorget-steel`; Name = `Riveted Steel Gorget`; Slot = `Collar`; Model = `Gorget`; Price = 550; Kit = A };
	{ Id = `bracers-hunter`; Name = `Hunter's Bracers`; Slot = `Arms`; Model = `Bracers`; Price = 450; Kit = A };
	{ Id = `gauntlets-hunter`; Name = `Hunter's Gauntlets`; Slot = `Arms`; Model = `Gauntlets`; Price = 600; Kit = A };
	{ Id = `crossbow-hunter`; Name = `Hunter's Crossbow`; Slot = `Back`; Model = `Crossbow`; Price = 900; Kit = A };
	-- batch 5: magic (Kit A 21-24)
	{ Id = `halo-rune`; Name = `Floating Rune Halo`; Slot = `Halo`; Model = `RuneHalo`; Piece = `RuneHalo`; Price = 850; Kit = A };
	{ Id = `sigils-orbiting`; Name = `Orbiting Sigils`; Slot = `Halo`; Model = `OrbitSigils`; Piece = `OrbitSigils`; Price = 900; Kit = A };
	{ Id = `familiar-crow`; Name = `Crow Familiar`; Slot = `Familiar`; Model = `CrowFamiliar`; Piece = `Crow`; Price = 800; Kit = A };
	{ Id = `pendant-crystal`; Name = `Caged Crystal Pendant`; Slot = `Neck`; Model = `CrystalPendant`; Piece = `CrystalPendant`; Price = 450; Kit = A };
	{ Id = `belt-potion`; Name = `Potion Belt`; Slot = `Belt`; Model = `PotionBelt`; Piece = `PotionBelt`; Price = 550; Kit = A };
	-- Kit A 25-28: civilian (batch 6)
	{ Id = `watch-pocket`; Name = `Brass Pocket Watch`; Slot = `Watch`; Model = `PocketWatch`; Price = 480; Kit = A };
	{ Id = `umbrella-crook`; Name = `Crook Umbrella`; Slot = `Hand`; Model = `Umbrellas`; Piece = `CrookUmbrella`; Price = 320; Kit = A };
	{ Id = `parasol-lace`; Name = `Lace Parasol`; Slot = `Hand`; Model = `Umbrellas`; Piece = `LaceParasol`; Price = 420; Kit = A };
	{ Id = `lantern-candle`; Name = `Candle Lantern`; Slot = `Hand`; Model = `CandleLantern`; Price = 560; Kit = A };
	{ Id = `scarf-knit-crimson`; Name = `Crimson Striped Scarf`; Slot = `Neck`; Model = `Scarves`; Piece = `ScarfStripe`; Price = 260; Kit = A };
	{ Id = `scarf-knit-violet`; Name = `Grey-Violet Scarf`; Slot = `Neck`; Model = `Scarves`; Piece = `ScarfViolet`; Price = 260; Kit = A };
	-- Kit A 7 and Kit B 2: the coats (batch 7; one coat builder: shell, sleeves, rigged coattails worn together)
	{ Id = `coat-delinquent`; Name = `Delinquent's Long Coat`; Slot = `Coat`; Model = `LongCoat`; Pieces = { `LongCoatShell`, `LongCoatTailL`, `LongCoatTailR`, `LongCoatSleeveL`, `LongCoatSleeveR` }; Price = 1100; Kit = A };
	{ Id = `regalia-greatcoat`; Name = `Headmaster's Greatcoat`; Slot = `Coat`; Model = `Greatcoat`; Pieces = { `GreatcoatShell`, `GreatcoatTailL`, `GreatcoatTailR`, `GreatcoatSleeveL`, `GreatcoatSleeveR` }; Admin = true; Tint = `Crimson`; Kit = B };
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
	-- Kit C1: coats and jackets (Coat slot). Skirts ride the legs (Controllers.Character.BodyFollow); the torso and
	-- arms are covered under each design (shirts, waistcoats, jumpers); the hip corners are their own pieces
	{ Id = `coat-scholar`; Name = `Scholar's Frock Coat`; Slot = `Coat`; Model = `ScholarCoat`; Pieces = { `ScholarCoatShell`, `ScholarCoatHipsUp`, `ScholarCoatHipsLo`, `ScholarCoatSkirt`, `ScholarCoatSleeveL`, `ScholarCoatSleeveR` }; Price = 1050; Kit = C };
	{ Id = `coat-inverness`; Name = `Inverness Cape-Coat`; Slot = `Coat`; Model = `InvernessCoat`; Pieces = { `InvernessCoatShell`, `InvernessCoatHipsUp`, `InvernessCoatHipsLo`, `InvernessCoatCape`, `InvernessCoatSkirt`, `InvernessCoatSleeveL`, `InvernessCoatSleeveR` }; Price = 1150; Kit = C };
	{ Id = `coat-cadet`; Name = `Academy Cadet Coat`; Slot = `Coat`; Model = `CadetCoat`; Pieces = { `CadetCoatShell`, `CadetCoatSkirt`, `CadetCoatSleeveL`, `CadetCoatSleeveR`, `CadetCoatHipsUp`, `CadetCoatHipsLo` }; Price = 1000; Kit = C };
	{ Id = `jacket-varsity`; Name = `Nightmare Varsity Jacket`; Slot = `Coat`; Model = `VarsityJacket`; Pieces = { `VarsityJacketShell`, `VarsityJacketInner`, `VarsityJacketSideLow`, `VarsityJacketSideMid`, `VarsityJacketSideTop`, `VarsityJacketSleeveL`, `VarsityJacketSleeveR` }; Price = 850; Kit = C };
	{ Id = `jacket-hunting`; Name = `Waxed Hunting Jacket`; Slot = `Coat`; Model = `HuntingJacket`; Pieces = { `HuntingJacketShell`, `HuntingJacketInner`, `HuntingJacketSideLow`, `HuntingJacketSideMid`, `HuntingJacketSideTop`, `HuntingJacketSkirt`, `HuntingJacketSleeveL`, `HuntingJacketSleeveR` }; Price = 800; Kit = C };
	{ Id = `cloak-oilskin`; Name = `Oilskin Rain Cloak`; Slot = `Coat`; Model = `RainCloak`; Pieces = { `RainCloakShell`, `RainCloakHipsUp`, `RainCloakHipsLo`, `RainCloakSkirt`, `RainCloakSleeveL`, `RainCloakSleeveR` }; Price = 900; Kit = C };
	{ Id = `jacket-smoking`; Name = `Velvet Smoking Jacket`; Slot = `Coat`; Model = `SmokingJacket`; Pieces = { `SmokingJacketShell`, `SmokingJacketInner`, `SmokingJacketSideLow`, `SmokingJacketSideMid`, `SmokingJacketSideTop`, `SmokingJacketSkirt`, `SmokingJacketSleeveL`, `SmokingJacketSleeveR` }; Price = 950; Kit = C };
	{ Id = `coat-lamplighter`; Name = `Lamplighter's Coat`; Slot = `Coat`; Model = `LamplighterCoat`; Pieces = { `LamplighterCoatShell`, `LamplighterCoatHipsUp`, `LamplighterCoatHipsLo`, `LamplighterCoatSkirt`, `LamplighterCoatSleeveL`, `LamplighterCoatSleeveR` }; Price = 950; Kit = C };
	{ Id = `jacket-spencer`; Name = `Crimson Spencer`; Slot = `Coat`; Model = `CrimsonSpencer`; Pieces = { `CrimsonSpencerShell`, `CrimsonSpencerInner`, `CrimsonSpencerGown`, `CrimsonSpencerSideLow`, `CrimsonSpencerSideMid`, `CrimsonSpencerSideTop`, `CrimsonSpencerSleeveL`, `CrimsonSpencerSleeveR` }; Price = 900; Gender = `Female`; Kit = C };
	{ Id = `coat-chesterfield`; Name = `Chesterfield Overcoat`; Slot = `Coat`; Model = `ChesterfieldCoat`; Pieces = { `ChesterfieldCoatShell`, `ChesterfieldCoatSkirt`, `ChesterfieldCoatSleeveL`, `ChesterfieldCoatSleeveR`, `ChesterfieldCoatHipsUp`, `ChesterfieldCoatHipsLo` }; Price = 1100; Gender = `Male`; Kit = C };
	{ Id = `coat-cardigan`; Name = `Cable-Knit Cardigan Coat`; Slot = `Coat`; Model = `CardiganCoat`; Pieces = { `CardiganCoatShell`, `CardiganCoatSkirt`, `CardiganCoatSleeveL`, `CardiganCoatSleeveR`, `CardiganCoatHipsUp`, `CardiganCoatHipsLo` }; Price = 750; Kit = C };
	-- Kit C2: the masks (Face slot; they sit on the face, no ties round the head)
	{ Id = `mask-kintsugi`; Name = `Kintsugi Porcelain Mask`; Slot = `Face`; Model = `KintsugiMask`; Price = 700; Kit = C };
	{ Id = `mask-watch`; Name = `Beaked Night-Watch Mask`; Slot = `Face`; Model = `WatchMask`; Price = 750; Kit = C };
	{ Id = `mask-fox`; Name = `Fox Half-Mask`; Slot = `Face`; Model = `FoxMask`; Price = 550; Kit = C };
	{ Id = `mask-wolf`; Name = `Wolf Half-Mask`; Slot = `Face`; Model = `WolfMask`; Price = 550; Kit = C };
	{ Id = `mask-grille`; Name = `Iron Grille Mask`; Slot = `Face`; Model = `GrilleMask`; Price = 500; Kit = C };
	{ Id = `mask-wax`; Name = `Wax Saint Mask`; Slot = `Face`; Model = `WaxMask`; Price = 600; Kit = C };
	{ Id = `mask-moth`; Name = `Moth Mask`; Slot = `Face`; Model = `MothMask`; Price = 600; Kit = C };
	{ Id = `mask-domino`; Name = `Black Silk Domino`; Slot = `Face`; Model = `DominoMask`; Price = 300; Kit = C };
}

-- Pairs that can't be worn together because they'd pass through each other (measured by
-- art/characters/accessories/acc_check.py: every other pair of slots is clash-free on all 12 bodies).
-- Each side is an item id or a slot name. Wearing one takes the other off (Accessories.Resolve).
Accessories.Conflicts = {
	{ `collar-choir`, `Neck` };   -- the collar's lobes cover the throat and the knot
	{ `collar-choir`, `Sash` };   -- its lobes lie on the chest top, where sashes and straps cross
	{ `collar-choir`, `Back` };
	{ `collar-ruff`, `Neck` };    -- the falling ruff covers the throat and the knot
	{ `Sash`, `Back` };           -- a sash and a bag strap cross over the chest and back
	{ `Sash`, `Lapel` };          -- both sashes cross the chest where a pin goes (a sash wears its own badge)
	{ `Sash`, `tie-bow` };        -- a bow tie's loops reach the sashes' inner edges (the flat school tie fits under)
	{ `bag-satchel`, `Hand` };    -- (1.79) the satchel hangs on the right hip, away from the sword: a held piece hangs there
	{ `bag-satchel`, `Hip` };     -- and so do the hip pieces (the left hip belongs to the sheathed katana)
	-- capes (UI.Appearance.Capes, the look's Cape): "cape:*" is every cape, "cape:<Id>" one of them
	{ `cape:*`, `Back` };         -- every cape hangs over the back and both shoulders
	{ `cape:*`, `Collar` };
	{ `cape:*`, `Sash` };
	{ `cape:CapeDuelist`, `Lapel` };   -- the Duelist's cape crosses the left chest
	{ `cape:CapeDuelist`, `tie-bow` };
	{ `cape:CapeWardenMantle`, `Neck` };   -- the Warden's mantle closes over the throat
	-- (items_batch2)
	{ `cape:CapeMidnight`, `Hat` };   -- the Midnight Lord's high collar meets the brims at their hair fits (tricorn, top hat, hunter, witch, veils; acc_hatcapes.py)
	{ `hat-mourning`, `cape:*` };     -- the mourning veil drapes to the shoulders, onto every cape's collar
	{ `familiar-crow`, `hat-mourning` };   -- the veil drapes to the shoulders, where the crow perches (cross-batch check)
	-- (items_batch3)
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
	-- (items_batch4)
	{ `gorget-steel`, `Neck` };   -- the gorget's top lame covers the throat and the knot
	{ `gorget-steel`, `Sash` };   -- its crescent lames cover the chest top where every sash and the bandolier cross
	{ `cape:*`, `Shoulders` };    -- every cape hangs over both shoulders, where the pauldrons sit
	{ `gauntlets-hunter`, `Ring` };   -- the back-of-hand plate and knuckle lames cover the hand where a ring is worn
	-- (items_batch5)
	{ `familiar-crow`, `Sash` };       -- the crow perches on the left shoulder top, where both sashes cross it
	{ `familiar-crow`, `Back` };       -- and where the satchel's and the messenger bag's straps cross it
	{ `familiar-crow`, `cape:*` };     -- every cape lies over both shoulder tops
	{ `belt-potion`, `bag-messenger` };   -- the messenger bag sits on the lower back across the belt line
	{ `belt-potion`, `tie-school` };      -- the tie's blade hangs past the belt line (fitted to the chest, it stands off the waist)
	{ `pendant-crystal`, `cape:*` };      -- the chain lies round the neck on the shoulder tops, under every cape's collar
	{ `halo-rune`, `Hat` };              -- hats are scaled and lifted per hair; the tall ones reach up through the halo
	{ `sigils-orbiting`, `hat-hunter` };   -- measured: under the hunter hat's hair fits (5 hairs) its brim meets the orbit
	{ `sigils-orbiting`, `hat-witch` };    -- and the witch hat's brim (4 hairs)
	{ `familiar-crow`, `fur-torn` };          -- (cross-batch check) the crow perches where the fur lies on the shoulder
	{ `familiar-crow`, `shawl-grave-moss` };  -- and the shawl
	{ `familiar-crow`, `hood-tattered` };     -- and the hood's cowl
	{ `pendant-crystal`, `torc-moonstone` };  -- the chain runs round the neck where the torc sits
	{ `pendant-crystal`, `clasp-opera` };     -- and through the opera clasp's chains
	-- (items_batch6)
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
	-- (items_batch7)
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
	-- (items_kitb)
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
	-- Kit C (art/characters/accessories acc_check, 2026-11-12)
	{ `coat-scholar`, `Neck` };    -- Kit C coats bring their own shirt and neckwear (a cravat, a tie, a jumper's neck)
	{ `coat-scholar`, `Collar` };
	{ `coat-inverness`, `Neck` };
	{ `coat-inverness`, `Collar` };
	{ `coat-cadet`, `Neck` };
	{ `coat-cadet`, `Collar` };
	{ `jacket-varsity`, `Neck` };
	{ `jacket-varsity`, `Collar` };
	{ `jacket-hunting`, `Neck` };
	{ `jacket-hunting`, `Collar` };
	{ `cloak-oilskin`, `Neck` };
	{ `cloak-oilskin`, `Collar` };
	{ `jacket-smoking`, `Neck` };
	{ `jacket-smoking`, `Collar` };
	{ `coat-lamplighter`, `Neck` };
	{ `coat-lamplighter`, `Collar` };
	{ `jacket-spencer`, `Neck` };
	{ `jacket-spencer`, `Collar` };
	{ `coat-chesterfield`, `Neck` };
	{ `coat-chesterfield`, `Collar` };
	{ `coat-cardigan`, `Neck` };
	{ `coat-cardigan`, `Collar` };
	{ `mask-grille`, `cape:CapeDuelist` };    -- the grille's lower edge meets the high collars
	{ `mask-grille`, `cape:CapeWardenMantle` };
	{ `mask-fox`, `cape:CapeWardenMantle` };
	{ `mask-kintsugi`, `cape:CapeWardenMantle` };
	{ `mask-wax`, `cape:CapeWardenMantle` };
	{ `mask-fox`, `hat-mourning` };    -- the veil falls over the face
	{ `mask-grille`, `hat-mourning` };
	{ `mask-moth`, `hat-mourning` };
	{ `mask-watch`, `hat-mourning` };
	{ `mask-wolf`, `hat-mourning` };
	{ `mask-domino`, `regalia-thorn-crown` };    -- the crown sits low on the brow at its hair fits
	{ `mask-fox`, `regalia-thorn-crown` };
	{ `mask-kintsugi`, `regalia-thorn-crown` };
	{ `mask-wolf`, `regalia-thorn-crown` };
	{ `mask-grille`, `Neck` };    -- the scarves, the pendants and the torc at the chin
	{ `mask-kintsugi`, `scarf-knit-crimson` };
	{ `mask-kintsugi`, `scarf-knit-violet` };
	{ `mask-wax`, `scarf-knit-crimson` };
	{ `mask-wax`, `scarf-knit-violet` };
	{ `mask-grille`, `torc-moonstone` };
	{ `mask-wax`, `torc-moonstone` };
	{ `mask-grille`, `hood-tattered` };
	{ `mask-wax`, `collar-choir` };
}

Accessories.ById = {}
Accessories.BySlot = {}
for _, S in Accessories.Slots do Accessories.BySlot[S] = {} end
for _, It in Accessories.Items do
	It.Gender = It.Gender or `Unisex`
	Accessories.ById[It.Id] = It
	table.insert(Accessories.BySlot[It.Slot], It)
end

-- is the item's template in the game yet? (art arrives batch by batch)
function Accessories.Ready(It): boolean
	local Store = game:GetService(`ReplicatedStorage`):FindFirstChild(`NHAccessories`)
	local M = It and Store and Store:FindFirstChild(It.Model)
	if not M then return false end
	if It.Piece then return M:FindFirstChild(It.Piece) ~= nil end
	for _, N in It.Pieces or {} do -- an item of several pieces (a hat and its veil): all of them
		if not M:FindFirstChild(N) then return false end
	end
	return true
end

-- a worn list (the look's Acc string) -> { [slot] = id }, unknown ids and slot clashes dropped (the last one wins)
function Accessories.Parse(S: any): { [string]: string }
	local Out = {}
	if typeof(S) ~= `string` then return Out end
	for Id in S:gmatch(`[^,]+`) do
		local It = Accessories.ById[Id]
		if It then Out[It.Slot] = Id end
	end
	return Out
end

local function matches(Side: string, It): boolean
	return It.Id == Side or It.Slot == Side
end
-- do these two items clash?
function Accessories.Clash(A, B): boolean
	for _, C in Accessories.Conflicts do
		if (matches(C[1], A) and matches(C[2], B)) or (matches(C[1], B) and matches(C[2], A)) then return true end
	end
	return false
end
-- does this item clash with a cape (UI.Appearance.Capes entry id; "none" never does)?
function Accessories.CapeClash(CapeId: string?, It): boolean
	if not CapeId or CapeId == `none` or not It then return false end
	for _, C in Accessories.Conflicts do
		for _, Pair in { { C[1], C[2] }, { C[2], C[1] } } do
			if (Pair[1] == `cape:*` or Pair[1] == `cape:` .. CapeId) and matches(Pair[2], It) then return true end
		end
	end
	return false
end
-- put on `Id` (into its slot), taking off whatever clashes with it; returns the new worn table
function Accessories.Resolve(Worn: { [string]: string }, Id: string): { [string]: string }
	local It = Accessories.ById[Id]
	local Out = table.clone(Worn)
	if not It then return Out end
	for S, Other in Worn do
		local O = Accessories.ById[Other]
		if O and S ~= It.Slot and Accessories.Clash(It, O) then Out[S] = nil end
	end
	Out[It.Slot] = Id
	return Out
end
-- drop clashing pairs from a worn table (later slots in Accessories.Slots give way to earlier ones)
function Accessories.Clean(Worn: { [string]: string }): { [string]: string }
	local Out = {}
	for _, S in Accessories.Slots do
		local Id = Worn[S]
		local It = Id and Accessories.ById[Id]
		if It then
			local Ok = true
			for _, Kept in Out do
				if Accessories.Clash(It, Accessories.ById[Kept]) then Ok = false break end
			end
			if Ok then Out[S] = Id end
		end
	end
	return Out
end

-- { [slot] = id } -> the look's Acc string, in slot order (so equal looks compare equal)
function Accessories.Join(Worn: { [string]: string }): string
	Worn = Accessories.Clean(Worn)
	local Parts = {}
	for _, S in Accessories.Slots do
		local Id = Worn[S]
		if Id and Accessories.ById[Id] and Accessories.ById[Id].Slot == S then table.insert(Parts, Id) end
	end
	return table.concat(Parts, `,`)
end

return Accessories
]==]
local _, n = m.Source:gsub("{ Id = `", "")
return "installed " .. #m.Source .. " bytes, " .. n .. " items (backup NH_Backup.Config_Accessories_pre_kitc)"
