--[[
	Cast list: every talkable NPC (leaders, quest givers). Services.Social.Npcs spawns each one at
	the BasePart whose attribute NpcPost equals its id, anywhere in workspace, so the real map only
	needs a part with that attribute. Dialogue trees: ServerStorage.Dialogue.<Dialogue>.

	Important NPCs (saved relationship) are the ones also listed in Config.Reputation.Npcs.
]]

return {
	Ezra = { Name = `Ezra Vale`; Role = `Vigil Captain`; Faction = `Vigil`; Dialogue = `Ezra` };
	Vesper = { Name = `Vesper Crane`; Role = `Regent of the Crimson Court`; Faction = `CrimsonCourt`; Dialogue = `Vesper` };

	Dex = { Name = `Dex Moreno`; Role = `Campus Courier`; Color = Color3.fromRGB(90, 170, 230); Dialogue = `Dex` };
	Pip = { Name = `Pip Larkin`; Role = `First-year`; Color = Color3.fromRGB(150, 210, 140); Dialogue = `Pip` };
	Bruno = { Name = `Bruno Vance`; Role = `Keeper of the Ring`; Color = Color3.fromRGB(230, 140, 60); Dialogue = `Bruno` };

	-- clique leaders (Cliques Phase 3, 1.28): quest givers at their hangouts (posts placed by Studio/clique_quest_props.luau)
	Rhys = { Name = `Captain Rhys Thorne`; Role = `Athletes Captain`; Color = Color3.fromRGB(90, 150, 220); Clique = `Athletes`; Dialogue = `Rhys` };
	Lucien = { Name = `Lucien Grey`; Role = `Chapel Choir Cantor`; Color = Color3.fromRGB(230, 225, 210); Clique = `Choir`; Dialogue = `Lucien` };
	Wren = { Name = `Wren Ashby`; Role = `Ink Club Ringleader`; Color = Color3.fromRGB(150, 80, 190); Clique = `Ink`; Dialogue = `Wren` };
	-- (1.45) the Ink Club's seer: reads fortunes at the Ink Studio (Features.Fortune; no Clique here, so Sable is not a joinable leader)
	Sable = { Name = `Sable Vey`; Role = `Ink Club Seer`; Color = Color3.fromRGB(176, 120, 210); Dialogue = `Sable` };

	-- sports coaches (Services.Sports.Clubs; posts at the gym, pitch and field)
	Varga = { Name = `Coach Varga`; Role = `Night Ravens Coach`; Color = Color3.fromRGB(120, 70, 160); Dialogue = `Varga` };
	Mallory = { Name = `Coach Mallory`; Role = `Grave Rovers Coach`; Color = Color3.fromRGB(70, 140, 90); Dialogue = `Mallory` };
	Dunmore = { Name = `Coach Dunmore`; Role = `Iron Wardens Coach`; Color = Color3.fromRGB(170, 60, 50); Dialogue = `Dunmore` };

	-- (2.24.0) staff, Phase 1. Mr. Hale keeps his homeroom desk in Room 102 (in the Map: the first ground-floor classroom
	-- west of the entrance hall). The Night Custodian sweeps the main hallway by day; OffWhen = a Config.Stealth zone: while
	-- it's watched (after hours) his post stays empty, because he's the Records Office watcher then (Quests.Stealth).
	Hale = { Name = `Mr. Hale`; Role = `Chemistry, Room 103`; Color = Color3.fromRGB(196, 160, 112); Dialogue = `Hale`;
		-- (2.28) his Room 102 desk (2.24's post) all day and after hours, so Orientation can always find him; Chemistry in
		-- Room 103 during the class periods
		Posts = { Homeroom = `Hale`; Class = `Hale@R103`; Other = `Hale`; Off = `Hale` } };
	Custodian = { Name = `Night Custodian`; Role = `Custodian`; Color = Color3.fromRGB(110, 124, 150); Dialogue = `Custodian`; OffWhen = `RecordsOffice` };

	-- (2.28) the subject teachers and the Headmaster (docs/expansion/13-Living-School.md §3.1). Posts by segment:
	-- Homeroom (the register), Class (the other periods), Other (before school, passing, break, lunch, after school).
	-- Off = evening, night and morning. No key for a segment = not on campus then. Sallow has no Homeroom post: Hale takes the register in her room.
	Sallow = { Name = `Ms. Sallow`; Role = `Mathematics, Room 102`; Color = Color3.fromRGB(150, 150, 170); Dialogue = `Sallow`;
		Posts = { Class = `Sallow`; Other = `Sallow@Staff` } };
	Pryce = { Name = `Mr. Pryce`; Role = `English, Room 104`; Color = Color3.fromRGB(170, 120, 90); Dialogue = `Pryce`;
		Posts = { Class = `Pryce`; Other = `Pryce@Staff` } };
	Whitlock = { Name = `Dr. Whitlock`; Role = `History, Room 105`; Color = Color3.fromRGB(120, 100, 80); Dialogue = `Whitlock`;
		Posts = { Class = `Whitlock`; Other = `Whitlock@Staff` } };
	Ashgrave = { Name = `Headmaster Ashgrave`; Role = `Headmaster`; Color = Color3.fromRGB(60, 50, 70); Dialogue = `Ashgrave`;
		Posts = { Homeroom = `Ashgrave`; Class = `Ashgrave` } }; -- office hours by the Records Office door, class time only
}
