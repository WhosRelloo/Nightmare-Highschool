--[[
	The everyday-carry kit (shared). ReplicatedStorage.Config.Kit           (owner approved 2026-11-11)
	Design: docs/superpowers/specs/2026-11-11-qol-items-design.md. Server: Services.Features.Kit. Hold poses and grips:
	Config.KitHolds (generated from the Blender layouts, art/characters/qol/nh_qol.py).

	Twelve items a student owns for good (save slot), kept in the Locker's Kit tab. Pin up to MaxPinned to the hotbar
	(as well as the snack pouch). The key ring is worn; the hand warmer works from the pocket.
	Saved: PlayerData.Inventory.Kit (Config.Items.Sanitize calls Kit.Sanitize), through ProfileService only.
	Counters: anything tagged NHKitShop with attribute Shop = Sundries | Cafe | Office | Archive (16 studs).
]]local SchoolTime = require(game:GetService("ReplicatedStorage"):WaitForChild("Functions"):WaitForChild("SchoolTime")) -- (2.22.0) shared night windows

local Kit = {}

Kit.MaxPinned = 3

-- the HUD art (art/ui/hud/make_kit_ui.py; upload art/group-upload/kit-ui/ under the group). 0 = not uploaded yet:
-- the HUD falls back to plain shapes.
Kit.Art = {   -- group 15981569, 2026-11-11 (0 = not uploaded yet: a plain stand-in shows)
	CompassBezel = 98317613982331;
	CompassFace = 111693582059740;
	CompassNeedle = 81723021779869;
	CompassGlass = 108715309060756;
	KitPlate = 97376576287306;
	CardHud = 95865520982030;
	MapSheet = 117161918638283;
	MapHatch = 104140364749385;
	MapStipple = 137896165860809;
	MapYou = 107375906715949;
	MapPin = 114023900270124;
	FrostEdge = 104559232486608;
	InkEdge = 88085803637209;
	IconOil = 133175001625121;
	IconCup = 104230024199136;
	IconBiscuit = 120182314185938;
	IconBandage = 130873790081458;
	IconPass = 106812511008438;
	IconFlame = 87284856990105;
	IconFrost = 96724116026183;
	IconHeart = 81278772842357;
	IconKeys = 92184032626014;
	IconBook = 115399362774511;
}
Kit.Range = 16          -- studs to a counter

Kit.Shops = {
	Sundries = { Name = `MORROW & VANE`; Sub = `Purveyors of Sundries`; Text = `Lamps, oil, umbrellas, bandages and charcoal.` };
	Cafe = { Name = `THE WICK & KETTLE`; Sub = `Tea, coffee & biscuits`; Text = `Flasks filled, tins topped up.` };
	Office = { Name = `The Office`; Sub = `Main Hall`; Text = `Hall passes and replacement keys.` };
	Archive = { Name = `The Archive`; Sub = `Borrowing desk`; Text = `One book at a time. Mind the due date.` };
}

-- the use clips (KeyframeSequences in ServerStorage.NHKitAnims for the owner to publish; 0 = not published: the
-- hold pose alone, and the eating clip for sips, biscuits and bandages)
Kit.Anims = {   -- published by the owner (group 15981569), 2026-11-11
	FirstAid = 93493041203096;
	LibraryBook = 98142735985899;
	Timetable = 90489094973001;
	Compass = 70921087123347;
	KeyRing = 102742890260292;
	Lantern = 81572359052986;
	CampusMap = 91767817740887;
	HallPass = 72004004507455;
	Thermos = 117810698724970;
	SnackTin = 114776952647954;
	Umbrella = 103212455784729;
	HandWarmer = 118247637261372;
}
-- these play when the item is taken out (equipped); the rest when it is used. The keys turn at your dorm door.
Kit.AnimOnEquip = { CampusMap = true; Compass = true; Umbrella = true }

-- Starter: given at enrolment (and on the next join for students who already have a record)
Kit.Items = {
	{ Id = `Lantern`; Name = `Hand Lantern`; Rarity = `Uncommon`; Price = 150; Shop = `Sundries`; Hotbar = true;
		Text = `Brass and glass, a fluted wick knob. Lights your way after dark.`;
		Use = `Click to light it or put it out. A full tank burns 15 minutes.` };
	{ Id = `CampusMap`; Name = `Campus Map`; Rarity = `Common`; Starter = true; Hotbar = true;
		Text = `The inked plan of the grounds, folded in three.`;
		Use = `Click to open it. Click a place to pin a waypoint for your compass.` };
	{ Id = `Compass`; Name = `Pocket Compass`; Rarity = `Uncommon`; Price = 120; Shop = `Sundries`; Hotbar = true;
		Text = `A hunter-case compass. The needle finds whatever you're looking for.`;
		Use = `Hold it: the needle points to your waypoint, your quest, your next class or home.` };
	{ Id = `Umbrella`; Name = `Umbrella`; Rarity = `Uncommon`; Price = 180; Shop = `Sundries`; Hotbar = true;
		Text = `Black waxed canvas, a crimson lining, a carved bone crook.`;
		Use = `Open while held: keeps the rain off and slows a fall. Closes in a fight.` };
	{ Id = `Timetable`; Name = `Timetable Card`; Rarity = `Common`; Starter = true; Hotbar = true;
		Text = `The bell times, brass-cornered.`;
		Use = `Hold it to see the lesson now and next. Click for the full timetable.` };
	{ Id = `KeyRing`; Name = `Dorm Keys`; Rarity = `Common`; Starter = true; Worn = true;
		Text = `Your room key and two others nobody remembers.`;
		Use = `Worn on the hip. Needed to enter your room. The Office cuts a new set if you lose them.` };
	{ Id = `HallPass`; Name = `Hall Pass`; Rarity = `Uncommon`; Price = 40; Shop = `Office`; Hotbar = true; Daily = 1;
		Text = `A brass paddle with three punch holes. Prefects respect brass.`;
		Use = `Show it during class: the hall monitor lets you be for 60 seconds. One punch a period.` };
	{ Id = `LibraryBook`; Name = `Library Book`; Rarity = `Rare`; Shop = `Archive`; Hotbar = true; Loan = true;
		Text = `Borrowed from the Archive. The card in the pocket has your name on it.`;
		Use = `Pinned: +3% class EXP, +10% on its subject's lessons. Due back in 3 school days.` };
	{ Id = `Thermos`; Name = `Thermos`; Rarity = `Uncommon`; Price = 100; Shop = `Cafe`; Hotbar = true;
		Text = `Black enamel and brass. Hot all night.`;
		Use = `A sip steadies your guard (30 posture). Tea warms you; coffee sharpens you.` };
	{ Id = `SnackTin`; Name = `Snack Tin`; Rarity = `Common`; Price = 80; Shop = `Cafe`; Hotbar = true;
		Text = `Midnight Biscuits, baked by candlelight.`;
		Use = `A biscuit: +15 health over 4 s. Out of a fight only.` };
	{ Id = `FirstAid`; Name = `First-Aid Pouch`; Rarity = `Uncommon`; Price = 90; Shop = `Sundries`; Hotbar = true;
		Text = `Linen bandages, iodine, a steady hand.`;
		Use = `Bandage up (2.5 s): +25 health over 5 s, clears Wounded for 2 minutes.` };
	{ Id = `HandWarmer`; Name = `Hand Warmer`; Rarity = `Uncommon`; Price = 110; Shop = `Sundries`; Hotbar = true; Pocket = true;
		Text = `Pierced brass with a crescent moon. The coals glow through.`;
		Use = `Light it: the night chill can't touch you. Works from your pocket. A stick burns all night.` };
}
Kit.ById = {}
for I, It in Kit.Items do It.Order = I Kit.ById[It.Id] = It end

-- refills and services bought at a counter (Needs = an item you must own)
Kit.Refills = {
	{ Id = `LampOil`; Name = `Lamp Oil`; Shop = `Sundries`; Price = 15; Needs = `Lantern`; Text = `Fills the lantern's tank.` };
	{ Id = `Charcoal`; Name = `Charcoal Stick`; Shop = `Sundries`; Price = 10; Needs = `HandWarmer`; Text = `Burns one night in the warmer.` };
	{ Id = `Bandages`; Name = `Bandages (3)`; Shop = `Sundries`; Price = 25; Needs = `FirstAid`; Text = `Fills the pouch.` };
	{ Id = `Tea`; Name = `Fill with Tea`; Shop = `Cafe`; Price = 20; Needs = `Thermos`; Text = `Four cups. Tea also chases off the chill.` };
	{ Id = `Coffee`; Name = `Fill with Coffee`; Shop = `Cafe`; Price = 20; Needs = `Thermos`; Text = `Four cups. +2% class EXP for 3 min a cup.` };
	{ Id = `Biscuits`; Name = `Biscuits (6)`; Shop = `Cafe`; Price = 30; Needs = `SnackTin`; Text = `Fills the tin.` };
	{ Id = `NewKeys`; Name = `New Set of Keys`; Shop = `Office`; Price = 50; Text = `Your old set stops working.` };
	{ Id = `LibraryCard`; Name = `Library Card`; Shop = `Archive`; Price = 0; Text = `Sign up to borrow. Free.` };
}
Kit.RefillById = {}
for _, R in Kit.Refills do Kit.RefillById[R.Id] = R end

-- the Archive's lending shelf (one book at a time; Subject nil = no subject bonus)
Kit.Books = {
	{ Id = `Arithmetic`; Name = `Practical Arithmetic`; Subject = `Mathematics` };
	{ Id = `Reagents`; Name = `Tinctures & Reagents`; Subject = `Chemistry` };
	{ Id = `NightVerse`; Name = `An Anthology of Night Verse`; Subject = `English` };
	{ Id = `OldTown`; Name = `Annals of the Old Town`; Subject = `History` };
	{ Id = `NightSchools`; Name = `A History of the Night Schools` };
}
Kit.BookById = {}
for _, B in Kit.Books do Kit.BookById[B.Id] = B end

-- the numbers (spec: "The 12 items")
Kit.Lantern = { Tank = 900; Range = 22; Brightness = 1.6; Color = Color3.fromRGB(255, 170, 90) }
Kit.Thermos = { Cups = 4; Posture = 30; Stamina = 35; Cooldown = 20; SipTime = 1.2; CoffeeBuff = `FlaskCoffee` }
Kit.Tin = { Biscuits = 6; Heal = 15; Duration = 4 }
Kit.Aid = { Bandages = 3; Channel = 2.5; Heal = 25; Duration = 5; Clears = 120; ChannelSpeed = 0.5 }
Kit.Pass = { Punches = 3; Seconds = 60; ChaseGrace = 3 }
Kit.Book = { ClassExp = 0.03; Subject = 0.10; LoanDays = 3; FinePerDay = 10; FineMax = 30 }
Kit.Umbrella = { FallCap = 28 }
Kit.Warmer = { Burn = 3000; MaxSticks = 9 }
Kit.Keys = { DropChance = 0.10; Reward = 10; Range = 8; Lifetime = 900 }

-- Night Chill: outdoors 21:00 to 06:00. A Region box counts as indoors unless listed here; no region, or no roof
-- overhead outside any indoor region, counts as outdoors.
Kit.Chill = { From = SchoolTime.Windows.Late.From; To = SchoolTime.Windows.Late.To; After = 60; Fade = 15; PostureRegen = 0.75;
	Immune = { Wraith = true; Vampire = true }; Slow = { Werewolf = 2 } }
Kit.OutdoorRegions = { Grounds = true; Pitch = true; Field = true; PracticeLanes = true; BackLot = true; WestEdge = true;
	BoilerYard = true; Ring = true }

-- Wounded: below Threshold of max health; walk speed x Speed out of combat
Kit.Wounded = { Threshold = 0.25; Speed = 0.9 }

-- Rain nights: chosen at StartHour each game day, Chance, lasting Hours game hours; soaked after Soak s outdoors
Kit.Rain = { StartHour = 20; Chance = 0.25; Hours = { 2, 4 }; Soak = 8 }

---| saved form |---
-- Kit = { Owned = { [id] = true }, Pinned = { id }, Oil = s, Warmer = { Sticks, Burn, Lit }, Flask = { Kind, Cups },
--   Biscuits, Bandages, Pass = { Punches, Day, Key }, Card = bool, Book = { Id, Due } | nil, Fine, Keys = { Lost, Set },
--   Starter = bool }
local function num(V, Lo, Hi, Def)
	if typeof(V) ~= `number` or V ~= V then return Def end
	return math.clamp(V, Lo, Hi)
end
local function int(V, Lo, Hi, Def)
	local N = num(V, Lo, Hi, Def)
	return if N == nil then nil else math.floor(N)
end

function Kit.Sanitize(Raw)
	local R = if typeof(Raw) == `table` then Raw else {}
	local Out = { Owned = {}; Pinned = {} }
	if typeof(R.Owned) == `table` then
		for Id, On in R.Owned do if Kit.ById[Id] and On == true then Out.Owned[Id] = true end end
	end
	if typeof(R.Pinned) == `table` then
		for _, Id in R.Pinned do
			local It = Kit.ById[Id]
			if It and It.Hotbar and Out.Owned[Id] and not table.find(Out.Pinned, Id) and #Out.Pinned < Kit.MaxPinned then table.insert(Out.Pinned, Id) end
		end
	end
	Out.Oil = num(R.Oil, 0, Kit.Lantern.Tank, 0)
	local W = if typeof(R.Warmer) == `table` then R.Warmer else {}
	Out.Warmer = { Sticks = int(W.Sticks, 0, Kit.Warmer.MaxSticks, 0); Burn = num(W.Burn, 0, Kit.Warmer.Burn, 0); Lit = W.Lit == true }
	local F = if typeof(R.Flask) == `table` then R.Flask else {}
	Out.Flask = { Kind = if F.Kind == `Coffee` then `Coffee` else `Tea`; Cups = int(F.Cups, 0, Kit.Thermos.Cups, 0) }
	Out.Biscuits = int(R.Biscuits, 0, Kit.Tin.Biscuits, 0)
	Out.Bandages = int(R.Bandages, 0, Kit.Aid.Bandages, 0)
	local P = if typeof(R.Pass) == `table` then R.Pass else {}
	Out.Pass = { Punches = int(P.Punches, 0, Kit.Pass.Punches, 0); Day = int(P.Day, -1, 1e7, -1);
		Key = if typeof(P.Key) == `string` and #P.Key <= 24 then P.Key else nil }
	Out.Card = R.Card == true
	if typeof(R.Book) == `table` and Kit.BookById[R.Book.Id] then
		Out.Book = { Id = R.Book.Id; Due = int(R.Book.Due, 0, 1e7, 0) }
	end
	if not Out.Book then Out.Owned.LibraryBook = nil end
	Out.Fine = int(R.Fine, 0, Kit.Book.FineMax, 0)
	local K = if typeof(R.Keys) == `table` then R.Keys else {}
	Out.Keys = { Lost = K.Lost == true; Set = int(K.Set, 0, 1e6, 0) }
	Out.Starter = R.Starter == true
	-- pins may name only what you still own
	for I = #Out.Pinned, 1, -1 do if not Out.Owned[Out.Pinned[I]] then table.remove(Out.Pinned, I) end end
	return Out
end

-- "Lit 12:40 left" style charge line for UI
function Kit.Charge(Id: string, K): string?
	if not K then return nil end
	local function mmss(S) S = math.max(0, math.floor(S)) return string.format(`%d:%02d`, S // 60, S % 60) end
	if Id == `Lantern` then return `Oil {mmss(K.Oil)}` end
	if Id == `HandWarmer` then return `{K.Warmer.Sticks} sticks · {if K.Warmer.Burn > 0 then mmss(K.Warmer.Burn) .. ` left` else `cold`}` end
	if Id == `Thermos` then return `{K.Flask.Cups}/{Kit.Thermos.Cups} cups of {string.lower(K.Flask.Kind)}` end
	if Id == `SnackTin` then return `{K.Biscuits}/{Kit.Tin.Biscuits} biscuits` end
	if Id == `FirstAid` then return `{K.Bandages}/{Kit.Aid.Bandages} bandages` end
	if Id == `HallPass` then return `{K.Pass.Punches}/{Kit.Pass.Punches} punches left` end
	if Id == `KeyRing` then return if K.Keys.Lost then `Lost` else `On your hip` end
	if Id == `LibraryBook` and K.Book then
		local B = Kit.BookById[K.Book.Id]
		return B and B.Name or nil
	end
	return nil
end

-- the count badge on the hotbar slot (nil = none)
function Kit.Count(Id: string, K): number?
	if not K then return nil end
	if Id == `Thermos` then return K.Flask.Cups end
	if Id == `SnackTin` then return K.Biscuits end
	if Id == `FirstAid` then return K.Bandages end
	if Id == `HallPass` then return K.Pass.Punches end
	return nil
end

return Kit
