--[[
	Regions (Config). The places of Nightmare High and the town around it, and how their name cards behave.
	Read by Services.Features.Regions (discovery, rewards) and Controllers.World.Regions (the card under the compass).

	Each region is an invisible box in workspace.Regions (a Persistent model, so it never streams out) with the
	attribute RegionId = a key below. Where boxes overlap the highest Priority wins (then the smaller box).
	Kind:
	  School     the building           gold line
	  Restricted fine by day, out of bounds after dark (Night text shown at night, crimson)
	  Forbidden  staff only, always     crimson line
	  Sports     the clubs' grounds     gold line
	  Turf       a faction's hangout    crimson line
	  Grounds    the open grounds       no card on its own, never counted
]]

local Regions = {}

Regions.Defs = {
	MainHall = { Name = `The Main Hall`; Kind = `School`; Priority = 2;
		Text = `Portraits line the corridor. Some of them blink.`; Night = `Lights out. The hall monitors walk here now.` };
	EastWing = { Name = `The East Wing`; Kind = `School`; Priority = 2;
		Text = `Past Detention the corridor runs colder.`; Night = `Nobody comes this way after dark. Nobody admits it.` };
	R101 = { Name = `Room 101 · Homeroom`; Title = `Homeroom`; Kicker = `Room 101`; Kind = `School`; Priority = 5; Text = `Every day begins here, with the bell.` };
	R102 = { Name = `Room 102 · Mathematics`; Title = `Mathematics`; Kicker = `Room 102`; Kind = `School`; Priority = 5; Text = `Chalk dust and quiet arithmetic.` };
	R103 = { Name = `Room 103 · Chemistry`; Title = `Chemistry`; Kicker = `Room 103`; Kind = `School`; Priority = 5; Text = `Something on the back shelf is still bubbling.` };
	R104 = { Name = `Room 104 · English`; Title = `English`; Kicker = `Room 104`; Kind = `School`; Priority = 5; Text = `The margins are full of other students' secrets.` };
	R105 = { Name = `Room 105 · History`; Title = `History`; Kicker = `Room 105`; Kind = `School`; Priority = 5; Text = `The past is taught here. Some of it was there.` };
	R106 = { Name = `Room 106 · Detention`; Title = `Detention`; Kicker = `Room 106`; Kind = `School`; Priority = 5; Text = `Sit. Write your lines. Don't look at the window.` };
	Archive = { Name = `The Archive`; Kind = `Restricted`; Priority = 5;
		Text = `The oldest books keep the quietest secrets.`; Night = `Forbidden after dark. The books don't like company.` };
	BoilerYard = { Name = `The Boiler Yard`; Kind = `Restricted`; Priority = 5;
		Text = `Mind the pipes. Something down here breathes.`; Night = `Out of bounds. The boiler is louder at night.` };
	StaffRoom = { Name = `The Staff Room`; Kind = `Forbidden`; Priority = 5; Text = `Coffee, gossip and confiscated things.` };
	RecordsOffice = { Name = `The Records Office`; Kind = `Forbidden`; Priority = 5; Text = `Every name, every mark, every secret, filed.` };
	Ring = { Name = `The Ring`; Kicker = `Settled here`; Kind = `School`; Priority = 5; Text = `Where scores are settled. Bring a second.` };
	Gymnasium = { Name = `The Gymnasium`; Kind = `Sports`; Priority = 4; Text = `Night Ravens' court. Mind the rafters.` };
	Pitch = { Name = `The West Pitch`; Kind = `Sports`; Priority = 4; Text = `Grave Rovers' ground. The fog rolls in by the second half.` };
	Field = { Name = `The North Field`; Kind = `Sports`; Priority = 4; Text = `Iron Wardens. Hold the line.` };
	PracticeLanes = { Name = `The Practice Lanes`; Kind = `Sports`; Priority = 4; Text = `Run it again. The machine never tires.` };
	BackLot = { Name = `The Back Lot`; Kicker = `Delinquent turf`; Kind = `Turf`; Priority = 3; Text = `Keep your head down. They watch the gate.` };
	WestEdge = { Name = `The West Edge`; Kicker = `Wolf territory`; Kind = `Turf`; Priority = 3; Text = `Wolves run the tree line after dark.` };
	-- the cliques' hangouts (1.20, stand-ins until the builder's map)
	Commons = { Name = `The Commons`; Kicker = `The Ordinary`; Kind = `School`; Priority = 3; Text = `Benches, gossip and the fountain nobody drinks from.` };
	Chapel = { Name = `The Chapel`; Kicker = `The Chapel Choir`; Kind = `School`; Priority = 5;
		Text = `Hymns at dusk. The candles never quite go out.`; Night = `Someone is still singing in there.` };
	InkStudio = { Name = `The Ink Studio`; Kicker = `The Ink Club`; Kind = `School`; Priority = 5; Text = `Paint on every surface. Mind your shoes.` };
	CrimsonParlor = { Name = `The Crimson Parlor`; Kicker = `Crimson Court turf`; Kind = `Turf`; Priority = 5; Text = `Invitation only. You weren't invited.` };
	Den = { Name = `The Den`; Kicker = `Pack turf`; Kind = `Turf`; Priority = 4; Text = `Smoke, embers and a lot of teeth.` };
	-- (2.16.0) places for the Map's region boxes; not counted for discovery until they have boxes in every place
	Library = { Name = `The Library`; Kind = `School`; Priority = 5; Text = `Quiet. The books are listening.`; Discover = false };
	Cafeteria = { Name = `The Cafeteria`; Kind = `School`; Priority = 4; Text = `Trays, gossip and whatever today's special is.`; Discover = false };
	Dorms = { Name = `The Dorms`; Kind = `School`; Priority = 4; Text = `Lights out at curfew. Mostly.`; Discover = false };
	Graveyard = { Name = `The Graveyard`; Kind = `Restricted`; Priority = 4; Text = `Old stones and older names.`;
		Night = `Out of bounds after dark. The ground isn't always still.`; Discover = false };
	Grounds = { Name = `School Grounds`; Kind = `Grounds`; Priority = 1; Text = `Nightmare Highschool`; Discover = false };
}

-- the card's small line above the name, by kind (a place's own Kicker wins; Title, if set, is the card's big name)
Regions.Kickers = {
	School = `Nightmare High`; Restricted = `Restricted`; Forbidden = `Staff only`; Sports = `Club grounds`; Turf = `Faction turf`;
}
Regions.NightKicker = `Out of bounds after dark`   -- Restricted places at night

Regions.Dwell = 0.5          -- seconds inside a new region before its card shows
Regions.Repeat = 6           -- every visit gets its card (found or not); this only stops a doorway shuffle repeating it
Regions.Hold = 3.2           -- the card stays this long (a discovery stays DiscoverHold)
Regions.DiscoverHold = 4.4
Regions.AfterArrival = 7     -- no cards for this long after you leave the main menu (the arrival card names the place)
Regions.Margin = 6           -- the server allows this many studs of slack when it checks you're in the region
Regions.Exp = `RegionFound`  -- Config.Progression.Exp key for each new place
Regions.Title = `Explorer`   -- earned for finding every place
Regions.NightFrom, Regions.NightTo = 18.5, 6.5   -- school-clock hours (as Config.Ambience)

-- the places that count for discovery, in a stable order
function Regions.Countable(): { string }
	local L = {}
	for Id, D in Regions.Defs do
		if D.Discover ~= false then table.insert(L, Id) end
	end
	table.sort(L)
	return L
end

function Regions.Sanitize(Raw)
	local Out = { Found = {} }
	if type(Raw) ~= `table` or type(Raw.Found) ~= `table` then return Out end
	for Id, V in Raw.Found do
		if type(Id) == `string` and Regions.Defs[Id] and Regions.Defs[Id].Discover ~= false and V then Out.Found[Id] = true end
	end
	return Out
end

return Regions
