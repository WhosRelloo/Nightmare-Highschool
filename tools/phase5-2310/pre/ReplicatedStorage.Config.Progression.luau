--[[
	Progression: EXP, levels, stat points and what perks and traits actually do.
	Server: Services.Player.Progression. Saved in PlayerData.Progress (action SetProgress).

	The concept doc says: a Verdant Moon-style stat system, kill-count race tiers, and 1.2x EXP for
	school missions during school hours (SchoolClock.GetExpMultiplier). The stats, curve and numbers
	below are a PROPOSAL; tune freely.
]]

local Progression = {}

Progression.MaxLevel = 50
Progression.PointsPerLevel = 3
Progression.MaxStat = 60

-- EXP to go from level L to L + 1
function Progression.ToNext(Level: number): number
	return math.floor(100 + 45 * (Level - 1) ^ 1.35)
end

-- Stats you spend points on. Each point gives the listed effects (see Effects below).
Progression.Stats = {
	{ Id = `Might`; Name = `Might`; Text = `Hit harder.`; Per = { DamageDealt = 0.015 } };
	{ Id = `Grit`; Name = `Grit`; Text = `More health; your guard holds longer.`; Per = { MaxHealth = 2; PostureGain = -0.004 } };
	{ Id = `Wits`; Name = `Wits`; Text = `Learn faster and sneak better.`; Per = { ClassExp = 0.01; QuestExp = 0.008; Stealth = -0.006 } };
}
Progression.StatById = {}
for _, S in Progression.Stats do Progression.StatById[S.Id] = S end

-- EXP awards. Each has a category, so perks/traits can boost one kind of EXP.
Progression.Exp = {
	AttendPresent = { Amount = 40; Category = `Class` };
	AttendTardy = { Amount = 20; Category = `Class` };
	Lesson = { Amount = 30; Category = `Class` };          -- + LessonGradeBonus by grade
	QuestMain = { Amount = 150; Category = `Quest` };       -- a quest's Rewards.Exp overrides these
	QuestSide = { Amount = 80; Category = `Quest` };
	DuelWon = { Amount = 40; Category = `Combat` };
	ChampionDefeated = { Amount = 120; Category = `Combat` };
	ExecuteNPC = { Amount = 20; Category = `Combat` };
	ExecutePlayer = { Amount = 40; Category = `Combat` };
	FactionRank = { Amount = 60; Category = `Social` };
	FactionJoined = { Amount = 50; Category = `Social` };
	Introduced = { Amount = 5; Category = `Social` };       -- first time you introduce yourself to someone
	EscapedMonitor = { Amount = 15; Category = `Stealth` };
	SportDrill = { Amount = 20; Category = `Sport` };      -- finishing a sports drill
	RegionFound = { Amount = 15; Category = `Quest` };     -- the first time you find a place (Config.Regions)
	SportMatch = { Amount = 40; Category = `Sport` };      -- playing a full match
	SportWin = { Amount = 40; Category = `Sport` };        -- winning one (on top of SportMatch)
	SportMvp = { Amount = 25; Category = `Sport` };
}
Progression.LessonGradeBonus = { ["A+"] = 30; A = 24; B = 16; C = 8; D = 2; F = 0 }

-- (training 1.81) small bonuses per level of each trained area (Services.Features.Training.Effects; levels 0-20).
-- At 20: Arms +8% damage (a Might point is 1.5%), Torso +20 health and -6% posture gain, Legs +6% sprint speed.
Progression.Training = {
	Arms = { DamageDealt = 0.004 };
	Torso = { MaxHealth = 1; PostureGain = -0.003 };
	Legs = { SprintSpeed = 0.003 };
}

--[[ Effects: one shared list of every modifier a stat, clan perk or trait can give.
	Active ones are applied by Services.Player.Progression; "planned" ones are stored and shown but
	wait for the system they need.
		DamageDealt   +x  your hits deal (1 + x) damage                      active (Downed.ApplyDamage)
		DamageTaken   -x  you take (1 + x) damage                            active
		MaxHealth     +n  max health                                         active
		PostureGain   -x  your guard fills (1 + x) as fast                   active (DamageLogic)
		Stealth       -x  watchers spot you (1 + x) as fast                  active (Quests.Stealth)
		ClassExp / QuestExp / CombatExp / SocialExp / StealthExp / SportExp  +x EXP of that kind   active
		SchoolExp     +x  EXP during school hours                            active
		NightExp      +x  EXP at night                                       active
		NightPower    +x  damage dealt at night                              active
		LowHealthRegen +x regenerate when below 30% health (base 1 HP/s)     active
		DailyRevive   1   once per in-game day, get back up instead of staying downed   active
		AllExp        +x  every kind of EXP                                  active (races)
		DamageVsUndead / DamageVsMonster   +x damage vs that race family     active (Lineage.DamageScale)
		DamageTakenFromUndead  -x  damage taken from undead attackers        active (Lineage.DamageScale)
		DamageByDay   -x  damage dealt by day                                active
		HealOnKill / HealOnExecute  +x  heal x of max health per kill / execution   active
		FullMoonPower +x  extra damage on a full-moon night                  active
		NewMoonPower  +x  extra damage on a new-moon night (1.41)             active
		NewMoonStealth -x harder to spot on a new-moon night (1.41)           active
		WalkSpeed, ParryWindow, Prices, Popularity, Awareness, ClueSense, YenLessons, ...  planned
]]
Progression.Active = {
	DamageDealt = true; DamageTaken = true; MaxHealth = true; PostureGain = true; Stealth = true;
	ClassExp = true; QuestExp = true; CombatExp = true; SocialExp = true; StealthExp = true;
	SchoolExp = true; NightExp = true; NightPower = true; LowHealthRegen = true; DailyRevive = true;
	AllExp = true; DamageVsUndead = true; DamageVsMonster = true; DamageTakenFromUndead = true; DamageByDay = true;
	HealOnKill = true; HealOnExecute = true; FullMoonPower = true; SportExp = true;
	NewMoonPower = true; NewMoonStealth = true;
	SprintSpeed = true; -- (training 1.81) Legs: sprint speed (Features.CombatSpeed, NH_SprintMult)
}

-- What each clan's perk does (Config.Clans keeps the names and texts).
Progression.ClanEffects = {
	Harlow = { QuestExp = 0.05 };           Pike = { DamageDealt = 0.02 };
	Mercer = { Prices = -0.05 };             Fenwick = { SchoolExp = 0.06 };
	Abbott = { SocialExp = 0.1 };            Tully = { SocialExp = 0.08; MaxHealth = 4 };
	Marsh = { Stealth = -0.05 };             Danby = { MaxHealth = 8 };
	Whitlock = { SocialExp = 0.12 };         Garrow = { NightExp = 0.08 };
	Kestrel = { WalkSpeed = 0.03; Stealth = -0.04 };  Ambrose = { ClassExp = 0.08 };
	Lowell = { ClassExp = 0.06; QuestExp = 0.03 };    Sallow = { NightExp = 0.1 };
	Ashgrove = { ClassExp = 0.12 };          Blackwood = { ClueSense = 0.15; QuestExp = 0.05 };
	Calloway = { QuestExp = 0.1 };           Thorne = { CombatExp = 0.1; DamageDealt = 0.03 };
	Wren = { ClueSense = 0.2; StealthExp = 0.1 };
	Ravenscar = { Stealth = -0.1 };          Greymoor = { SchoolExp = 0.12 };
	Duskmere = { NightPower = 0.06 };        Holloway = { LowHealthRegen = 0.3; MaxHealth = 6 };
	Vauclair = { QuestExp = 0.1; SocialExp = 0.1 };   Mortlake = { DamageTaken = -0.05; MaxHealth = 10 };
	["Saint-Alder"] = { DamageDealt = 0.05; ClassExp = 0.05 };
	Hollowmere = { NightPower = 0.08; Stealth = -0.08 };  Nocturne = { DamageDealt = 0.04; Stealth = -0.06 };
}

-- Plain-English text for a set of effects, e.g. "+5% quest EXP, +4 max health". Planned ones are marked.
local LABELS = {
	DamageDealt = `damage`; DamageTaken = `damage taken`; MaxHealth = `max health`; PostureGain = `guard strain`;
	Stealth = `chance to be spotted`; ClassExp = `class EXP`; QuestExp = `quest EXP`; CombatExp = `combat EXP`;
	SocialExp = `social EXP`; StealthExp = `stealth EXP`; SportExp = `sport EXP`; SchoolExp = `EXP in school hours`; NightExp = `EXP at night`;
	NightPower = `damage at night`; LowHealthRegen = `healing when badly hurt`; DailyRevive = `daily second chance`;
	WalkSpeed = `walk speed`; Prices = `shop prices`; ClueSense = `clue sense`; Popularity = `popularity`;
	Awareness = `awareness`; ParryWindow = `parry window`;
	AllExp = `all EXP`; DamageVsUndead = `damage vs the undead`; DamageVsMonster = `damage vs monsters`;
	DamageTakenFromUndead = `damage taken from the undead`; DamageByDay = `damage by day`;
	HealOnKill = `max health healed per kill`; HealOnExecute = `max health healed per execution`;
	FullMoonPower = `extra damage on a full-moon night`;
	NewMoonPower = `extra damage on a new-moon night`; NewMoonStealth = `chance to be spotted on a new-moon night`;
}
function Progression.Describe(Effects): string
	local Parts = {}
	local Keys = {}
	for K, V in Effects or {} do
		if math.abs(V) > 1e-6 then table.insert(Keys, K) end -- skip zeros (stats with no points)
	end
	table.sort(Keys)
	for _, K in Keys do
		local V = Effects[K]
		local Label = LABELS[K] or K
		local Text
		if K == `MaxHealth` then Text = `{if V >= 0 then `+` else `−`}{math.abs(math.floor(V + 0.5))} {Label}`
		elseif K == `LowHealthRegen` then Text = `heal {string.format("%g", math.floor((1 + V * 5) * 10 + 0.5) / 10)} HP/s when badly hurt`
		elseif K == `DailyRevive` then Text = `a {Label}`
		else
			local Pct = math.abs(V) * 100
			local Num = if Pct < 9.95 and math.abs(Pct - math.floor(Pct + 0.5)) > 0.05 then string.format(`%.1f`, Pct) else tostring(math.floor(Pct + 0.5))
			Text = `{if V >= 0 then `+` else `−`}{Num}% {Label}`
		end
		if not Progression.Active[K] then Text ..= ` (planned)` end
		table.insert(Parts, Text)
	end
	return table.concat(Parts, `, `)
end

return Progression
