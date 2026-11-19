--[[
	Reputation + relationships (shared).
	Reputation is general standing with the whole school; faction standing and personal
	relationships are separate (see Config.Factions and the NPC list below).
]]

return {
	Categories = {
		Popularity   = { Min = 0; Max = 100; Text = `How well-liked you are. Opens friendlier dialogue.` };
		Intimidation = { Min = 0; Max = 100; Text = `How much people fear you. Needed for the Crimson Court's Inner Circle.` };
		Trust        = { Min = 0; Max = 100; Text = `Whether people believe you. Leaders share more with trusted students.` };
		Academics    = { Min = 0; Max = 100; Text = `Your standing with teachers. Needed for the Vigil's Inner Circle.` };
	};

	-- Relationship value -100..100 -> state (checked top to bottom).
	RelationshipStates = {
		{ Name = `Hostile`;      Max = -50 };
		{ Name = `Rival`;        Max = -20 };
		{ Name = `Acquaintance`; Max = 19 };
		{ Name = `Friendly`;     Max = 49 };
		{ Name = `Trusted`;      Max = 100 };
	};

	-- Important NPCs (only these keep a saved relationship).
	Npcs = {
		Ezra = { Name = `Ezra Vale`; Role = `Vigil Captain`; Faction = `Vigil` };
		Vesper = { Name = `Vesper Crane`; Role = `Regent of the Crimson Court`; Faction = `CrimsonCourt` };
	};

	AttackPenalty = { Relationship = -20; Standing = -10 }; -- hitting an important NPC

	SavedCap = 64; -- (2.27) saved relationships per slot (the cast and the roster); see Social.Reputation's Trim
}
