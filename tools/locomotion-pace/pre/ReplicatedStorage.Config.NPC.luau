--[[
	NPC (Config). Combat AI defaults (Services.AI.AI) and the difficulty tiers (1.23, owner 2026-11-04: "make them have
	different difficulty levels with parrying, etc.").

	Tiers: Easy / Normal / Hard / Nightmare. An NPC's config picks one with Tier (Default: Normal); the tier's fields win
	over the config's own for everything combat. Who uses which:
	  Easy        delinquent grunt               Normal      delinquent brute, a plain AI.Spawn
	  Hard        gang leader                     Nightmare   the Ring Champion (duels), the Cmdr ParryDemon
	Admins can spawn a sparring partner of any tier (admin panel, Spawns).

	How the tier fields are used (Services.AI.AI.NPCBehaviors):
	  React             seconds between your swing starting and the NPC dodging it or raising a guard
	  Parry / Dodge     chance, rolled ONCE per swing you throw, to parry it or sidestep it. A parry is timed to
	                    the swing's hit (its animation's Hit marker), off by up to Timing seconds either way; the
	                    parry window is 0.25 s, so a Timing of 0.16 (Easy) misses about one parry in five
	  Block             chance to raise a held guard instead, once the NPC has taken BlockAfterHits hits in a row
	  Heavy             extra chance to parry or dodge a heavy (M2, uppercut, slam)
	  Evasive           chance, once per stun, to break out with an evasive
	  Feint / ReadBlock chance to feint one of its own swings; multiplied by ReadBlock while you hold block
	  Punish            after one of its parries lands, it attacks straight away
	  Uppercut / M2     chance to open with an uppercut / a heavy instead of a light
	  AttackCooldown    seconds between its attacks; MaxStringLength / MaxPressureTime / RecoveryWindow cap stunlocks
	  ChaseSpeed / SprintSpeed, Jump / Slide (chance per second while closing in)
	  Pips              how many crimson pips show under its name (1 to 4)
	Nobody parries or blocks while stunned, so a combo that lands keeps landing.
]]

export type NPCConfig = {
	AggroRange: number;
	AttackRange: number;
	ChaseRange: number;

	--| Pathfinding |--

	AgentRadius: number;
	AgentHeight: number;
	AgentCanJump: boolean;
	WaypointSpacing: number;

	--| Behavior |--

	Weapon: string;
	AttackCooldown: number;
	IdleWaitTime: number;
	PatrolSpeed: number;
	ChaseSpeed: number;
	Tier: string?;              -- Easy / Normal / Hard / Nightmare (Config.NPC.Tiers)

	--| Fairness |--

	MaxStringLength: number?;   -- attacks an NPC may land on a stunned target in a row
	MaxPressureTime: number?;   -- seconds of non-stop target stun before the NPC backs off
	RecoveryWindow: number?;    -- seconds the target must be un-stunned before the next string

	--| Death |--

	CorpseTime: number?;        -- seconds before a dead NPC's body is removed
	RespawnTime: number?;       -- seconds before a dead NPC respawns at its home spot (nil = never)
}

local Tiers = {
	Easy = {
		React = { 0.34, 0.46 }; Timing = 0.16; Parry = 0.10; Dodge = 0.05; Block = 0.15; BlockAfterHits = 3; Heavy = 0.05;
		Evasive = 0.15; Feint = 0; ReadBlock = 1; Punish = false; Uppercut = 0.08; M2 = 0.25;
		AttackCooldown = 1.2; MaxStringLength = 2; MaxPressureTime = 0.6; RecoveryWindow = 1.6;
		ChaseSpeed = 15; SprintSpeed = 19; Jump = 0.04; Slide = 0.04; Pips = 1;
	};
	Normal = {
		React = { 0.26, 0.34 }; Timing = 0.11; Parry = 0.25; Dodge = 0.12; Block = 0.30; BlockAfterHits = 2; Heavy = 0.10;
		Evasive = 0.30; Feint = 0.08; ReadBlock = 1.5; Punish = false; Uppercut = 0.15; M2 = 0.35;
		AttackCooldown = 0.9; MaxStringLength = 3; MaxPressureTime = 0.8; RecoveryWindow = 1.3;
		ChaseSpeed = 16; SprintSpeed = 21; Jump = 0.08; Slide = 0.10; Pips = 2;
	};
	Hard = {
		React = { 0.17, 0.23 }; Timing = 0.07; Parry = 0.45; Dodge = 0.20; Block = 0.45; BlockAfterHits = 2; Heavy = 0.15;
		Evasive = 0.50; Feint = 0.20; ReadBlock = 2; Punish = true; Uppercut = 0.22; M2 = 0.45;
		AttackCooldown = 0.6; MaxStringLength = 3; MaxPressureTime = 0.9; RecoveryWindow = 1.1;
		ChaseSpeed = 17; SprintSpeed = 23; Jump = 0.12; Slide = 0.16; Pips = 3;
	};
	Nightmare = {
		React = { 0.11, 0.17 }; Timing = 0.04; Parry = 0.65; Dodge = 0.30; Block = 0.55; BlockAfterHits = 1; Heavy = 0.15;
		Evasive = 0.70; Feint = 0.30; ReadBlock = 2.4; Punish = true; Uppercut = 0.28; M2 = 0.50;
		AttackCooldown = 0.45; MaxStringLength = 4; MaxPressureTime = 1.0; RecoveryWindow = 1.0;
		ChaseSpeed = 18; SprintSpeed = 24; Jump = 0.16; Slide = 0.20; Pips = 4;
	};
}

local Order = { `Easy`, `Normal`, `Hard`, `Nightmare` }

-- the config an NPC actually runs on: its own settings with its tier's combat fields on top
local function Resolve(Config: any): any
	local Out = table.clone(Config or {})
	local Name = Out.Tier
	if not Tiers[Name] then
		-- older configs only had Skill (0..1)
		local S = Out.Skill
		Name = if S == nil then `Normal` elseif S >= 0.9 then `Nightmare` elseif S >= 0.4 then `Hard` elseif S >= 0.15 then `Normal` else `Easy`
	end
	for K, V in Tiers[Name] do Out[K] = V end
	Out.Tier = Name
	return Out
end

return {
	Default = {
		AggroRange = 50;
		AttackRange = 10;
		ChaseRange = 100;

		AgentRadius = 2;
		AgentHeight = 5;
		AgentCanJump = true;
		WaypointSpacing = 4;

		Weapon = `Fist`; -- (2.15.0, owner) enemy NPCs fight with their fists by default
		ContrabandChance = 0.25; -- (2.15.0) a fist NPC carries brass knuckles this often (NHContraband attribute: true forces, false never)
		AttackCooldown = 0.4;
		IdleWaitTime = 0.5;
		PatrolSpeed = 12;
		ChaseSpeed = 18;
		Tier = `Normal`;

		-- Tuned 2026-10-29 vs an idle player: ~52% stunned (was 80%), longest chain ~2.3s,
		-- a 1s+ free window about every 3s, ~3.6 damage/s. (The tier's values now override these.)
		MaxStringLength = 3;
		MaxPressureTime = 0.8;
		RecoveryWindow = 1.2;

		CorpseTime = 4;
		RespawnTime = nil;
	} :: NPCConfig;

	Tiers = Tiers;
	TierOrder = Order;
	Resolve = Resolve;
}
