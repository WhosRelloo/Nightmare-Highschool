--[[
	Config.Accessories: the 3D accessory kits (cosmetic only: no stats, never Race).
	  Kit A "Player accessories" (28 designs): bought for Yen at the School Store (Accessories tab), worn at a wardrobe.
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

local A, B = `A`, `B`
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
