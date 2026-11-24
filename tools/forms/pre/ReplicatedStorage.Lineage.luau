--!nonstrict
--[[
	NH Lineage - race, race variant (sub-race) and traits, ROLLED ON THE SERVER. Players never choose.

	Concept doc: 3 base races (Human, Priest, Vampire); sub-races come from a spin system
	(Superhuman; Grand Priest, Pope; Nobleblood, Royal Vamp). The user's 2026-10-30 brief adds Werewolf,
	Ghoul and Wraith. Each race has a family, 3 tier titles, a passive (strengths by tier x sub-race Boost,
	flat drawbacks) and, for Vampire, Ghoul and (2.1.3) Wraith, a skin Palette. Spec: docs/superpowers/specs/2026-10-30-races-design.md Traits are not in the concept doc yet:
	the list below is a proposal and is data only (no gameplay effects until the stat system exists).

	Saved in ProfileService data: PlayerData.Lineage = { Race, SubRace, Traits = {ids}, Spins = { Race, Variant, Trait } }
	through Data.UpdateState({ type = "SetLineage" }). A new profile gets a free first roll on join.
	The server mirrors read-only Player attributes Race, SubRace, Traits (comma list) for other systems.

	Server  Lineage.StartServer()   (ServerScriptService.NHLineage runs it)
	  Remote ReplicatedStorage.NHLineage.Spin (RemoteFunction): (kind "Race"|"Variant"|"Trait", slot?) ->
	    ok, result | reason. Rate-limited; spins are not used up in Studio.
	Server  Lineage.GrantSpins(player, "Race"|"Variant"|"Trait"|"All", amount) -> saved  (for the spin shop)
	Client  Lineage.Get() -> lineage    Lineage.Spin(kind, slot?) -> ok, lineage|reason
	        Lineage.Describe(lineage) -> race, sub, traits (config rows)   Lineage.Odds(raceId?) -> rows
]]

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local rgb = Color3.fromRGB
local SchoolTime = require(game:GetService("ReplicatedStorage"):WaitForChild("Functions"):WaitForChild("SchoolTime")) -- (2.22.0) shared night windows

local Lineage = {}
Lineage.RemotesName = "NHLineage"
Lineage.TraitSlots = 2
Lineage.StartingSpins = { Race = 3, Variant = 3, Trait = 5 }
-- Concept doc: 3 race tiers by kill count. Thresholds are a PROPOSAL (total grip executions,
-- PlayerData.Kills + NPCKills). Tier is stored now so the class/tier systems need no migration.
Lineage.TierKills = { 0, 25, 100 }

-- Rarity tiers (shared look with the UI kit's rarity colours)
Lineage.Rarity = {
	Common = { Order = 1, Color = rgb(196, 190, 204) },
	Uncommon = { Order = 2, Color = rgb(108, 176, 118) },
	Rare = { Order = 3, Color = rgb(96, 150, 220) },
	Epic = { Order = 4, Color = rgb(170, 110, 220) },
	Legendary = { Order = 5, Color = rgb(235, 190, 90) },
}

-- Weights are relative. Families: Mortal (Human, Priest), Undead (Vampire, Ghoul, Wraith), Cursed (Werewolf).
-- Passive Strengths are { Tier I, Tier II, Tier III } and are multiplied by the sub-race's Boost; Drawbacks are flat.
-- Effect keys are Config.Progression's (applied by Services.Player.Progression). Numbers are a balance PROPOSAL.
Lineage.FullMoonEvery = 4
-- Evolution (Phase 3): each race fills its own hunger; enough hunger opens that tier's rite (a quest),
-- and finishing the rite raises the tier. Thresholds follow the concept doc's kill counts.
Lineage.HungerNeed = { [2] = 25, [3] = 100 }
Lineage.HungerName = { Human = "Resolve", Priest = "Faith", Vampire = "Blood", Werewolf = "the Hunt", Ghoul = "Feeding", Wraith = "Souls" }
function Lineage.RiteFor(raceId, tier) return "Rite" .. tostring(raceId) .. tostring(tier) end -- every 4th in-game night is a full moon
Lineage.Races = {
	{
		Id = "Human", Name = "Human", Weight = 40, Color = rgb(214, 196, 170), Family = "Mortal",
		Text = "Ordinary blood. Nothing holds you back, and nothing holds you up.",
		Tiers = { "Townsfolk", "Hunter", "Slayer" },
		Passive = { Name = "Stubborn Will", Text = "You learn from everything, and you don't break easily.",
			Strengths = { AllExp = { 0.08, 0.10, 0.12 }, PostureGain = { -0.04, -0.06, -0.08 }, DamageVsMonster = { 0, 0, 0.08 } },
			Drawbacks = {}, DrawbackText = "No power at night, and a monster's bite can turn you." },
		Subs = {
			{ Id = "Human", Name = "Human", Weight = 90, Rarity = "Common", Boost = 1 },
			{ Id = "Superhuman", Name = "Superhuman", Weight = 10, Rarity = "Rare", Boost = 1.15 },
		},
	},
	{
		Id = "Priest", Name = "Priest", Weight = 25, Color = rgb(235, 205, 120), Family = "Mortal",
		Text = "Born to the chapel. The light answers when you call.",
		Tiers = { "Acolyte", "Exorcist", "Saint" },
		Passive = { Name = "Consecrated", Text = "The dead flinch from you.",
			Strengths = { DamageVsUndead = { 0.06, 0.09, 0.12 }, DamageTakenFromUndead = { -0.06, -0.09, -0.12 }, ClassExp = { 0.05, 0.05, 0.05 } },
			Drawbacks = { NightPower = -0.05 }, DrawbackText = "Weaker after dark." },
		Subs = {
			{ Id = "Priest", Name = "Priest", Weight = 85, Rarity = "Uncommon", Boost = 1 },
			{ Id = "GrandPriest", Name = "Grand Priest", Weight = 12, Rarity = "Epic", Boost = 1.15 },
			{ Id = "Pope", Name = "Pope", Weight = 3, Rarity = "Legendary", Boost = 1.3 },
		},
	},
	{
		Id = "Vampire", Name = "Vampire", Weight = 15, Color = rgb(200, 40, 60), Family = "Undead",
		Text = "The night school was built for your kind.",
		Tiers = { "Fledgling", "Night Gentry", "Elder" },
		Passive = { Name = "Night Blood", Text = "Stronger in the dark; every kill feeds you.",
			Strengths = { NightPower = { 0.06, 0.09, 0.12 }, HealOnKill = { 0.04, 0.06, 0.08 } },
			Drawbacks = { DamageByDay = -0.05 }, DrawbackText = "Weaker by day." },
		Palette = { -- pale or dark tones only
			rgb(242, 234, 228), rgb(236, 228, 214), rgb(222, 212, 194), rgb(214, 208, 200), rgb(196, 198, 204),
			rgb(92, 62, 48), rgb(74, 52, 46), rgb(62, 44, 38), rgb(40, 34, 36),
		},
		Subs = {
			{ Id = "Vampire", Name = "Vampire", Weight = 85, Rarity = "Uncommon", Boost = 1 },
			{ Id = "Nobleblood", Name = "Nobleblood", Weight = 12, Rarity = "Epic", Boost = 1.15 },
			{ Id = "RoyalVamp", Name = "Royal Vamp", Weight = 3, Rarity = "Legendary", Boost = 1.3 },
		},
	},
	{
		Id = "Werewolf", Name = "Werewolf", Weight = 10, Color = rgb(150, 120, 90), Family = "Cursed",
		Text = "The moon remembers what you are, even when you forget.",
		Tiers = { "Cursed", "Moonbound", "Feral Lord" },
		Passive = { Name = "Moon-Blooded", Text = "Hard to put down, and hungrier at night.",
			Strengths = { MaxHealth = { 10, 15, 20 }, NightPower = { 0.05, 0.08, 0.10 }, FullMoonPower = { 0.025, 0.04, 0.05 } },
			Drawbacks = { Stealth = 0.10 }, DrawbackText = "Easier to spot while sneaking." },
		Subs = {
			{ Id = "Werewolf", Name = "Werewolf", Weight = 85, Rarity = "Uncommon", Boost = 1 },
			{ Id = "Bloodmoon", Name = "Bloodmoon", Weight = 12, Rarity = "Epic", Boost = 1.15 },
			{ Id = "Alpha", Name = "Alpha", Weight = 3, Rarity = "Legendary", Boost = 1.3 },
		},
	},
	{
		Id = "Ghoul", Name = "Ghoul", Weight = 6, Color = rgb(120, 140, 104), Family = "Undead",
		Text = "Something in the cellar woke up hungry. It was you.",
		Tiers = { "Starveling", "Grave-eater", "Charnel Lord" },
		Passive = { Name = "Grave Hunger", Text = "Rotten, tough, and mended by feeding.",
			Strengths = { DamageTaken = { -0.05, -0.08, -0.10 }, LowHealthRegen = { 0.01, 0.1, 0.2 }, HealOnExecute = { 0.06, 0.09, 0.12 } },
			Drawbacks = { ClassExp = -0.10 }, DrawbackText = "Learns less in class." },
		Palette = { -- ghoul tones only
			rgb(132, 138, 130), rgb(122, 140, 104), rgb(118, 100, 124), rgb(160, 158, 150), rgb(160, 152, 96), rgb(104, 118, 132),
		},
		Subs = {
			{ Id = "Ghoul", Name = "Ghoul", Weight = 85, Rarity = "Rare", Boost = 1 },
			{ Id = "Ghast", Name = "Ghast", Weight = 12, Rarity = "Epic", Boost = 1.15 },
			{ Id = "CryptLord", Name = "Crypt Lord", Weight = 3, Rarity = "Legendary", Boost = 1.3 },
		},
	},
	{
		Id = "Wraith", Name = "Wraith", Weight = 4, Color = rgb(150, 180, 210), Family = "Undead",
		Text = "Half of you never came back from the cold.",
		Tiers = { "Whisper", "Shroud", "Dirge" },
		Passive = { Name = "Unseen", Text = "Hard to see, hard to stagger, sharper after dark.",
			-- (1.41) the new moon is the Wraiths' night: +5% damage and +5% harder to spot (Progression.Apply)
			Strengths = { Stealth = { -0.10, -0.15, -0.20 }, PostureGain = { -0.06, -0.09, -0.12 }, NightExp = { 0.06, 0.09, 0.12 },
				NewMoonPower = { 0.05, 0.05, 0.05 }, NewMoonStealth = { -0.05, -0.05, -0.05 } },
			Drawbacks = { MaxHealth = -10 }, DrawbackText = "A frailer body." },
		Palette = { -- (2.1.3, owner) shadow tones only: black, charcoal, ash greys, a cold pale grey
			rgb(0, 0, 0), rgb(20, 20, 22), rgb(34, 34, 38), rgb(51, 51, 58), rgb(74, 74, 82), rgb(106, 106, 114),
			rgb(142, 142, 150), rgb(200, 200, 206),
		},
		Subs = {
			{ Id = "Wraith", Name = "Wraith", Weight = 85, Rarity = "Rare", Boost = 1 },
			{ Id = "Revenant", Name = "Revenant", Weight = 12, Rarity = "Epic", Boost = 1.15 },
			{ Id = "HollowKing", Name = "Hollow King", Weight = 3, Rarity = "Legendary", Boost = 1.3 },
		},
	},
}

-- Proposed traits (data only for now; Effects are for the future stat system to read).
Lineage.Traits = {
	{ Id = "NightOwl", Name = "Night Owl", Rarity = "Common", Weight = 10, Text = "More EXP after dark.", Effects = { NightExp = 0.1 } },
	{ Id = "EarlyRiser", Name = "Early Riser", Rarity = "Common", Weight = 10, Text = "More EXP during school hours.", Effects = { SchoolExp = 0.1 } },
	{ Id = "QuickFeet", Name = "Quick Feet", Rarity = "Common", Weight = 10, Text = "A little faster on your feet.", Effects = { WalkSpeed = 0.03 } },
	{ Id = "Bookworm", Name = "Bookworm", Rarity = "Common", Weight = 10, Text = "Classes teach you more.", Effects = { ClassExp = 0.08 } },
	{ Id = "ThickSkin", Name = "Thick Skin", Rarity = "Common", Weight = 10, Text = "Shrug off a little damage.", Effects = { DamageTaken = -0.03 } },
	{ Id = "SilverTongue", Name = "Silver Tongue", Rarity = "Uncommon", Weight = 5, Text = "People like you more, shops charge you less.", Effects = { Prices = -0.08, Popularity = 0.1 } },
	{ Id = "LightSleeper", Name = "Light Sleeper", Rarity = "Uncommon", Weight = 5, Text = "Hard to sneak up on.", Effects = { Awareness = 0.15 } },
	{ Id = "SecondWind", Name = "Second Wind", Rarity = "Uncommon", Weight = 5, Text = "Recover faster when you're low.", Effects = { LowHealthRegen = 0.2 } },
	{ Id = "SteadyHands", Name = "Steady Hands", Rarity = "Rare", Weight = 2, Text = "A wider window to parry.", Effects = { ParryWindow = 0.05 } },
	{ Id = "Unshakeable", Name = "Unshakeable", Rarity = "Rare", Weight = 2, Text = "Your posture breaks more slowly.", Effects = { PostureGain = -0.1 } },
	{ Id = "Bloodhound", Name = "Bloodhound", Rarity = "Rare", Weight = 2, Text = "You notice clues others miss.", Effects = { ClueSense = 0.2 } },
	{ Id = "Moonlit", Name = "Moonlit", Rarity = "Legendary", Weight = 0.5, Text = "Stronger under the moon.", Effects = { NightPower = 0.08 } },
	{ Id = "Fated", Name = "Fated", Rarity = "Legendary", Weight = 0.5, Text = "Once a day, fate refuses to let you fall.", Effects = { DailyRevive = 1 } },
}

local RaceById, SubById, TraitById = {}, {}, {}
for _, r in ipairs(Lineage.Races) do
	RaceById[r.Id] = r
	for _, s in ipairs(r.Subs) do
		SubById[s.Id] = { Sub = s, Race = r }
	end
end
for _, t in ipairs(Lineage.Traits) do
	TraitById[t.Id] = t
end
Lineage.RaceById, Lineage.SubById, Lineage.TraitById = RaceById, SubById, TraitById

function Lineage.Family(raceId)
	local r = RaceById[raceId]
	return r and r.Family
end
function Lineage.IsUndead(raceId) return Lineage.Family(raceId) == "Undead" end
function Lineage.IsMonster(raceId)
	local f = Lineage.Family(raceId)
	return f == "Undead" or f == "Cursed"
end
function Lineage.Palette(raceId)
	local r = RaceById[raceId]
	return r and r.Palette
end
function Lineage.TierName(raceId, tier)
	local r = RaceById[raceId]
	if not r then return "" end
	return r.Tiers[math.clamp(math.floor(tonumber(tier) or 1), 1, #r.Tiers)]
end
-- strengths (tier value x sub-race boost), drawbacks (flat), boost
function Lineage.Passives(raceId, subId, tier)
	local r = RaceById[raceId]
	if not (r and r.Passive) then return {}, {}, 1 end
	tier = math.clamp(math.floor(tonumber(tier) or 1), 1, 3)
	local s = SubById[subId]
	local boost = (s and s.Race == r and s.Sub.Boost) or 1
	local strengths, drawbacks = {}, {}
	for k, byTier in pairs(r.Passive.Strengths) do
		local v = byTier[tier] * boost
		if math.abs(v) > 1e-6 then strengths[k] = v end
	end
	for k, v in pairs(r.Passive.Drawbacks or {}) do drawbacks[k] = v end
	return strengths, drawbacks, boost
end
function Lineage.PassiveEffects(raceId, subId, tier)
	local a, b = Lineage.Passives(raceId, subId, tier)
	local out = table.clone(a)
	for k, v in pairs(b) do out[k] = (out[k] or 0) + v end
	return out
end
-- The night of in-game day D runs 20:00 on D to 06:00 on D+1. Every FullMoonEvery-th night is a full moon.
function Lineage.IsFullMoon(day, hour)
	if type(day) ~= "number" or type(hour) ~= "number" then return false end
	if not SchoolTime.InWindow(hour, "Night") then return false end
	local night = if hour < 6 then day - 1 else day
	return night % Lineage.FullMoonEvery == 0
end

-- (1.41) moon phases. The cycle runs with FullMoonEvery (4 nights): full, waning, new, waxing, full again, so the full
-- moon keeps its old nights. By day the phase is the coming night's moon.
Lineage.MoonPhases = { "Full", "Waning", "New", "Waxing" }
Lineage.MoonPhaseNames = { Full = "full moon", Waning = "waning moon", New = "new moon", Waxing = "waxing moon" }
-- sky textures and clock icons per phase (art/ui/hud/make_moon_phases.py; empty = the sky's own moon)
-- (the sky draws its moon mirrored left to right, so the waning sky texture is the right-lit image and the waxing one the
-- left-lit image; the clock icons are not mirrored)
Lineage.MoonTextures = { Full = "rbxassetid://87924126913194", Waning = "rbxassetid://94096373568392", New = "rbxassetid://87971574021791", Waxing = "rbxassetid://87606769858269",
	Crimson = "rbxassetid://84885605143974", Blue = "rbxassetid://115157018699839" }
Lineage.MoonIcons = { Full = "rbxassetid://104532707497388", Waning = "rbxassetid://76246084386531", New = "rbxassetid://120725029880837", Waxing = "rbxassetid://102285598476802",
	Crimson = "rbxassetid://106194505989461", Blue = "rbxassetid://105820547659109" }
function Lineage.NightOf(day, hour)
	return if hour < 6 then day - 1 else day
end
function Lineage.MoonPhase(day, hour)
	if type(day) ~= "number" or type(hour) ~= "number" then return "Full" end
	return Lineage.MoonPhases[Lineage.NightOf(day, hour) % 4 + 1]
end
function Lineage.IsNewMoon(day, hour)
	if type(day) ~= "number" or type(hour) ~= "number" then return false end
	return SchoolTime.InWindow(hour, "Night") and Lineage.MoonPhase(day, hour) == "New"
end
-- (1.41) the special full moons: every 4th full moon (every 16th night), crimson and blue by turns. Each strengthens some
-- races that night (extra damage, Progression.Apply); a crimson moon also lights Vampires' eyes (Features.MoonPhases).
Lineage.MoonEvents = {
	Crimson = { Name = "crimson moon"; Power = { Vampire = 0.08; Ghoul = 0.03; Wraith = 0.03 } };
	Blue = { Name = "blue moon"; Power = { Priest = 0.08; Human = 0.05 } };
}
Lineage.MoonEventEvery = 16
-- "Crimson" | "Blue" | nil for the night that (day, hour) belongs to (by day: the coming night)
function Lineage.MoonEvent(day, hour)
	if type(day) ~= "number" or type(hour) ~= "number" then return nil end
	local n = Lineage.NightOf(day, hour)
	if n % Lineage.MoonEventEvery ~= 0 then return nil end
	return if (n // Lineage.MoonEventEvery) % 2 == 0 then "Crimson" else "Blue"
end
-- the extra damage a race gets from tonight's special moon (0 by day or on an ordinary night)
function Lineage.MoonEventPower(race, day, hour)
	if not (type(hour) == "number" and SchoolTime.InWindow(hour, "Night")) then return 0 end
	local e = Lineage.MoonEvent(day, hour)
	local def = e and Lineage.MoonEvents[e]
	return def and race and def.Power[race] or 0
end

-- nights from tonight to the next full moon (0 = tonight)
function Lineage.NightsUntilFull(day, hour)
	local n = Lineage.NightOf(day, hour) % 4
	return if n == 0 then 0 else 4 - n
end

local function raceOf(model)
	if typeof(model) ~= "Instance" then return nil end
	local p = Players:GetPlayerFromCharacter(model)
	return (p and p:GetAttribute("Race")) or model:GetAttribute("Race")
end
-- Extra damage multiplier from race families (Downed.ApplyDamage applies it after the stat multipliers).
function Lineage.DamageScale(attacker, target)
	local scale = 1
	local tr, ar = raceOf(target), raceOf(attacker)
	if Lineage.IsUndead(tr) then scale *= 1 + (attacker:GetAttribute("NH_VsUndead") or 0) end
	if Lineage.IsMonster(tr) then scale *= 1 + (attacker:GetAttribute("NH_VsMonster") or 0) end
	if Lineage.IsUndead(ar) then scale *= 1 + (target:GetAttribute("NH_FromUndead") or 0) end
	return scale
end

local function total(list)
	local n = 0
	for _, x in ipairs(list) do
		n += x.Weight
	end
	return n
end

-- Odds as percentages: Lineage.Odds() -> races; Lineage.Odds(raceId) -> that race's variants; Lineage.Odds("Traits")
function Lineage.Odds(which: string?)
	local list = if which == "Traits" then Lineage.Traits elseif which then (RaceById[which] and RaceById[which].Subs) else Lineage.Races
	if not list then
		return {}
	end
	local t = total(list)
	local out = {}
	for _, x in ipairs(list) do
		table.insert(out, { Id = x.Id, Name = x.Name, Rarity = x.Rarity, Color = x.Color, Chance = x.Weight / t * 100 })
	end
	return out
end

local function pick(list, rng, exclude)
	local pool = {}
	for _, x in ipairs(list) do
		if not (exclude and exclude[x.Id]) then
			table.insert(pool, x)
		end
	end
	local roll = rng:NextNumber() * total(pool)
	for _, x in ipairs(pool) do
		roll -= x.Weight
		if roll <= 0 then
			return x
		end
	end
	return pool[#pool]
end

--------------------------------------------------------------------------
-- race looks (Phase 2): per-race slots, each option unlocks at a tier.
-- Meshes are in ServerStorage.NHRaceCosmetics (modelled in Blender, PBR SurfaceAppearance); attached by
-- Services.Player.RaceCosmetics. Chosen looks save in PlayerData.Lineage.Looks = { [slot] = optionId }.
--------------------------------------------------------------------------
Lineage.Looks = {
	Vampire = {
		Ears = {
			{ Id = "Pointed", Name = "Pointed", Tier = 1, Meshes = { "V_Ears_Pointed" } },
			{ Id = "Swept", Name = "Swept", Tier = 1, Meshes = { "V_Ears_Swept" } },
			{ Id = "LongSwept", Name = "Long Swept", Tier = 2, Meshes = { "V_Ears_LongSwept" } },
			{ Id = "Elder", Name = "Elder", Tier = 3, Meshes = { "V_Ears_Elder" } },
		},
	},
	Werewolf = {
		Ears = {
			{ Id = "Upright", Name = "Upright", Tier = 1, Meshes = { "W_Ears_Upright" } },
			{ Id = "Tufted", Name = "Tufted", Tier = 1, Meshes = { "W_Ears_Tufted" } },
			{ Id = "Torn", Name = "Torn", Tier = 2, Meshes = { "W_Ears_Torn" } },
			{ Id = "Moon", Name = "Moon-marked", Tier = 3, Meshes = { "W_Ears_Moon" } },
		},
		Tail = {
			{ Id = "Brush", Name = "Brush", Tier = 1, Meshes = { "W_Tail_Brush" } },
			{ Id = "Bushy", Name = "Bushy", Tier = 1, Meshes = { "W_Tail_Bushy" } },
			{ Id = "Bobbed", Name = "Bobbed", Tier = 1, Meshes = { "W_Tail_Bobbed" } },
			{ Id = "Shaggy", Name = "Shaggy", Tier = 2, Meshes = { "W_Tail_Shaggy" } },
			{ Id = "Moon", Name = "Moon-marked", Tier = 3, Meshes = { "W_Tail_Moon" } },
		},
		Fur = {
			{ Id = "Ash", Name = "Ash", Tier = 1, Color = rgb(128, 124, 126) },
			{ Id = "Charcoal", Name = "Charcoal", Tier = 1, Color = rgb(62, 60, 64) },
			{ Id = "Umber", Name = "Umber", Tier = 1, Color = rgb(116, 80, 52) },
			{ Id = "Russet", Name = "Russet", Tier = 1, Color = rgb(140, 78, 44) },
			{ Id = "Wheat", Name = "Wheat", Tier = 1, Color = rgb(186, 160, 120) },
			{ Id = "Snow", Name = "Snow", Tier = 1, Color = rgb(226, 224, 220) },
		},
	},
	Ghoul = {
		Extras = {
			{ Id = "None", Name = "None", Tier = 1, Meshes = {} },
			{ Id = "Stitches", Name = "Stitch straps", Tier = 2, Meshes = { "G_Stitch_Jaw", "G_Stitch_Shoulder" } },
			{ Id = "Shroud", Name = "Grave shroud", Tier = 3, Meshes = { "G_Shroud" } },
			{ Id = "Both", Name = "Straps + shroud", Tier = 3, Meshes = { "G_Stitch_Jaw", "G_Stitch_Shoulder", "G_Shroud" } },
		},
	},
	Wraith = {
		Wisps = {
			{ Id = "Pale", Name = "Pale", Tier = 1, Color = rgb(190, 222, 255) },
			{ Id = "Grave", Name = "Grave green", Tier = 2, Color = rgb(150, 226, 176) },
			{ Id = "Violet", Name = "Violet", Tier = 2, Color = rgb(196, 156, 255) },
		},
		Frost = {
			{ Id = "Off", Name = "None", Tier = 1 },
			{ Id = "On", Name = "Frost-tipped fingers", Tier = 3 },
		},
	},
}
Lineage.LookSlots = { Vampire = { "Ears" }, Werewolf = { "Ears", "Tail", "Fur" }, Ghoul = { "Extras" }, Wraith = { "Wisps", "Frost" } }
Lineage.SlotNames = { Ears = "Ears", Tail = "Tail", Fur = "Fur colour", Extras = "Grave wear", Wisps = "Cold wisps", Frost = "Frost" }

function Lineage.LookOption(raceId, slot, id)
	local r = Lineage.Looks[raceId]
	for _, o in ipairs(r and r[slot] or {}) do
		if o.Id == id then return o end
	end
	return nil
end
-- every slot for this lineage -> the option to wear (saved choice if still allowed at this tier, else the first Tier I option)
function Lineage.ResolveLooks(l)
	l = l or {}
	local out = {}
	for _, slot in ipairs(Lineage.LookSlots[l.Race] or {}) do
		local saved = l.Looks and Lineage.LookOption(l.Race, slot, l.Looks[slot])
		if saved and saved.Tier <= (l.Tier or 1) then
			out[slot] = saved
		else
			out[slot] = Lineage.Looks[l.Race][slot][1]
		end
	end
	return out
end

function Lineage.Sanitize(data)
	data = type(data) == "table" and data or {}
	local out = { Spins = table.clone(Lineage.StartingSpins), Traits = {}, Tier = 1, Looks = {}, Hunger = 0, Earned = false, Seen = {}, TurnDay = -1 }
	if type(data.Hunger) == "number" and data.Hunger == data.Hunger then out.Hunger = math.clamp(data.Hunger, 0, 99999) end
	if data.Earned == true then out.Earned = true end
	if type(data.TurnDay) == "number" then out.TurnDay = math.floor(data.TurnDay) end
	if type(data.Seen) == "table" then
		for _, k in ipairs(data.Seen) do
			if type(k) == "string" and #k <= 24 and #out.Seen < 24 then table.insert(out.Seen, k) end
		end
	end
	if type(data.Tier) == "number" and data.Tier == math.floor(data.Tier) and data.Tier >= 1 and data.Tier <= #Lineage.TierKills then
		out.Tier = data.Tier
	end
	if RaceById[data.Race] then
		out.Race = data.Race
		local s = SubById[data.SubRace]
		out.SubRace = (s and s.Race.Id == data.Race) and data.SubRace or data.Race
	end
	if type(data.Traits) == "table" then
		local seen = {}
		for _, id in ipairs(data.Traits) do
			if TraitById[id] and not seen[id] and #out.Traits < Lineage.TraitSlots then
				seen[id] = true
				table.insert(out.Traits, id)
			end
		end
	end
	if type(data.Looks) == "table" then
		for slot, id in pairs(data.Looks) do
			if type(slot) == "string" and type(id) == "string" and #slot <= 16 and #id <= 24 then out.Looks[slot] = id end
		end
	end
	if type(data.Spins) == "table" then
		for k in pairs(out.Spins) do
			local v = data.Spins[k]
			if type(v) == "number" and v == v then
				out.Spins[k] = math.clamp(math.floor(v), 0, 999)
			end
		end
	end
	return out
end

function Lineage.TierFor(kills: number): number
	local tier = 1
	for i, need in ipairs(Lineage.TierKills) do
		if (kills or 0) >= need then
			tier = i
		end
	end
	return tier
end

function Lineage.Describe(l)
	l = l or {}
	local race = RaceById[l.Race]
	local sub = SubById[l.SubRace]
	local traits = {}
	for _, id in ipairs(l.Traits or {}) do
		table.insert(traits, TraitById[id])
	end
	return race, sub and sub.Sub, traits
end

--------------------------------------------------------------------------
-- server
--------------------------------------------------------------------------
function Lineage.StartServer()
	assert(RunService:IsServer(), "Lineage.StartServer must run on the server")
	if Lineage._started then
		return
	end
	Lineage._started = true
	local Data = require(game:GetService("ServerScriptService"):WaitForChild("Services"):WaitForChild("Player"):WaitForChild("Data"))
	local rng = Random.new()
	local free = RunService:IsStudio() -- spins are not used up while testing in Studio

	local folder = ReplicatedStorage:FindFirstChild(Lineage.RemotesName) or Instance.new("Folder")
	folder.Name = Lineage.RemotesName
	local lookRF = folder:FindFirstChild("SetLook") or Instance.new("RemoteFunction")
	lookRF.Name = "SetLook"
	lookRF.Parent = folder
	local spinRF = folder:FindFirstChild("Spin") or Instance.new("RemoteFunction")
	spinRF.Name = "Spin"
	spinRF.Parent = folder
	folder.Parent = ReplicatedStorage

	local function mirror(p, l)
		p:SetAttribute("Race", l.Race)
		p:SetAttribute("SubRace", l.SubRace)
		p:SetAttribute("Traits", table.concat(l.Traits, ","))
		p:SetAttribute("RaceTier", l.Tier)
		p:SetAttribute("RaceHunger", math.floor(l.Hunger or 0))
		-- resolved looks ("Ears=Pointed,Tail=Brush") so Services.Player.RaceCosmetics re-dresses on any change
		local parts = {}
		for slot, o in pairs(Lineage.ResolveLooks(l)) do table.insert(parts, slot .. "=" .. o.Id) end
		table.sort(parts)
		p:SetAttribute("RaceLooks", table.concat(parts, ","))
	end
	local function save(p, l)
		Data.UpdateState(p, { type = "SetLineage", lineage = l })
		mirror(p, l)
	end
	local function rollRace(l)
		local r = pick(Lineage.Races, rng)
		l.Race = r.Id
		l.SubRace = pick(r.Subs, rng).Id
	end
	local function rollTrait(l, slot)
		local have = {}
		for i, id in ipairs(l.Traits) do
			if i ~= slot then
				have[id] = true
			end
		end
		l.Traits[slot] = pick(Lineage.Traits, rng, have).Id
	end
	local function current(p)
		local profile = Data.GetProfile(p)
		return profile and Lineage.Sanitize(profile.Lineage)
	end

	local seen = setmetatable({}, { __mode = "k" })
	local function onJoin(p)
		-- runs when a profile loads (after a save slot is picked) - once per loaded profile
		local profileData = Data.GetProfile(p)
		if not profileData or seen[profileData] then
			return
		end
		seen[profileData] = true
		local l = current(p)
		if not l then
			return
		end
		local changed = false
		local profile = Data.GetProfile(p)
		-- tiers are earned through rites now; an old save keeps the kill-count tier it already had (never lower)
		if not l.Earned then
			l.Tier = math.max(l.Tier, Lineage.TierFor((profile.Kills or 0) + (profile.NPCKills or 0)))
			l.Earned = true
			changed = true
		end
		if not l.Race then -- a new student: the first roll is free
			rollRace(l)
			changed = true
		end
		for slot = 1, Lineage.TraitSlots do
			if not l.Traits[slot] then
				rollTrait(l, slot)
				changed = true
			end
		end
		if changed then
			save(p, l)
		else
			mirror(p, l)
		end
	end
	Data.ProfileLoaded:Connect(function(p)
		task.spawn(onJoin, p)
	end)
	for _, p in ipairs(Players:GetPlayers()) do
		task.spawn(onJoin, p)
	end

	local last = {}
	spinRF.OnServerInvoke = function(p, kind, slot)
		local now = os.clock()
		if last[p] and now - last[p] < 1 then
			return false, "Too fast"
		end
		last[p] = now
		if kind ~= "Race" and kind ~= "Variant" and kind ~= "Trait" then
			return false, "Unknown spin"
		end
		local l = current(p)
		if not l or not l.Race then
			return false, "Your record is still loading"
		end
		if not free and (l.Spins[kind] or 0) <= 0 then
			return false, "No " .. string.lower(kind) .. " spins left"
		end
		if kind == "Race" then
			rollRace(l)
			-- a new race starts over like the bite: tiers are earned through that race's own rites
			l.Tier = 1
			l.Hunger = 0
			l.Looks = {}
			l.Earned = true -- never let the old kill-count migration lift it back
		elseif kind == "Variant" then
			l.SubRace = pick(RaceById[l.Race].Subs, rng).Id
		else
			slot = tonumber(slot)
			if not slot or slot < 1 or slot > Lineage.TraitSlots or slot ~= math.floor(slot) then
				return false, "Unknown trait slot"
			end
			rollTrait(l, slot)
		end
		if not free then
			l.Spins[kind] -= 1
		end
		save(p, l)
		return true, l
	end
	Players.PlayerRemoving:Connect(function(p)
		last[p] = nil
	end)

	-- For purchases / rewards (e.g. Services.Player.Purchases): add spins without touching the data directly.
	-- kind = "Race" | "Variant" | "Trait" | "All". Returns true when saved.
	function Lineage.GrantSpins(p, kind, amount)
		amount = math.floor(tonumber(amount) or 0)
		if amount <= 0 then
			return false
		end
		local l = current(p)
		if not l then
			return false
		end
		for k in pairs(l.Spins) do
			if kind == "All" or kind == k then
				l.Spins[k] = math.clamp(l.Spins[k] + amount, 0, 999)
			end
		end
		save(p, l)
		return true
	end

	---| evolution and turning (Services.Player.Evolution / Turning call these) |---
	Lineage.Current = current
	-- the rite for `tier` can start: right race, one tier below, hunger full
	function Lineage.RiteReady(p, raceId, tier)
		local l = current(p)
		return l ~= nil and l.Race == raceId and l.Tier == tier - 1 and (l.Hunger or 0) >= (Lineage.HungerNeed[tier] or math.huge)
	end
	function Lineage.AddHunger(p, amount)
		local l = current(p)
		if not (l and l.Race) or amount <= 0 then return nil end
		l.Hunger = math.min(99999, (l.Hunger or 0) + amount)
		save(p, l)
		return l
	end
	function Lineage.Evolve(p, tier)
		local l = current(p)
		if not (l and l.Race) or tier ~= l.Tier + 1 or tier > 3 then return false end
		l.Tier = tier
		save(p, l)
		return true, l
	end
	-- seen-once flags (tier-up cutscenes become skippable after the first time)
	function Lineage.MarkSeen(p, key)
		local l = current(p)
		if not l or table.find(l.Seen, key) then return end
		if #l.Seen >= 24 then table.remove(l.Seen, 1) end
		table.insert(l.Seen, key)
		save(p, l)
	end
	function Lineage.HasSeen(p, key)
		local l = current(p)
		return l ~= nil and table.find(l.Seen, key) ~= nil
	end
	-- the bite: a turned student becomes the biter's base race at Tier I (spins and traits kept)
	function Lineage.Turn(p, raceId)
		local l = current(p)
		if not (l and RaceById[raceId]) then return false end
		l.Race = raceId
		l.SubRace = raceId
		l.Tier = 1
		l.Hunger = 0
		l.Looks = {}
		save(p, l)
		return true, l
	end
	function Lineage.SetTurnDay(p, day)
		local l = current(p)
		if not l then return end
		l.TurnDay = day
		save(p, l)
	end

	-- Studio test bridge only: force a race/sub/tier through the normal save path
	-- choose a race look (server-validated: the option must exist for your race and be unlocked at your tier)
	local lastLook = {}
	function Lineage.SetLook(p, slot, id)
		local l = current(p)
		if not (l and l.Race) then return false, "Your record is still loading" end
		local o = Lineage.LookOption(l.Race, slot, id)
		if not o then return false, "Not a look for your race" end
		if o.Tier > (l.Tier or 1) then return false, "Unlocks at Tier " .. o.Tier end
		l.Looks[slot] = id
		save(p, l)
		return true, l
	end
	lookRF.OnServerInvoke = function(p, slot, id)
		local now = os.clock()
		if lastLook[p] and now - lastLook[p] < 0.25 then return false, "Too fast" end
		lastLook[p] = now
		if type(slot) ~= "string" or type(id) ~= "string" then return false, "Bad request" end
		return Lineage.SetLook(p, slot, id)
	end
	Players.PlayerRemoving:Connect(function(p) lastLook[p] = nil end)

	function Lineage.SetForTests(p, race, sub, tier)
		if not RunService:IsStudio() then return false end
		local l = current(p)
		if not (l and RaceById[race]) then return false end
		l.Race = race
		local s = SubById[sub]
		l.SubRace = (s and s.Race.Id == race) and sub or race
		l.Tier = math.clamp(math.floor(tonumber(tier) or 1), 1, 3)
		save(p, l)
		return true, l
	end
	-- (admin, 1.65) the Headmaster's Desk sets a student's race (any variant) or forces a tier. A new race keeps the
	-- tier (staff set that separately) but clears hunger and race looks, like a race spin; Earned stops the old
	-- kill-count migration from lifting the tier again.
	function Lineage.AdminSetRace(p, subId)
		local l = current(p)
		if not l then return false, "Their record is still loading" end
		local s = SubById[subId]
		if not s then return false, "Unknown race" end
		if l.Race ~= s.Race.Id then
			l.Hunger = 0
			l.Looks = {}
		end
		l.Race = s.Race.Id
		l.SubRace = subId
		l.Earned = true
		save(p, l)
		return true, l
	end
	function Lineage.AdminSetTier(p, tier)
		local l = current(p)
		if not (l and l.Race) then return false, "Their record is still loading" end
		tier = tonumber(tier)
		if not tier or tier ~= math.floor(tier) or tier < 1 or tier > #Lineage.TierKills then return false, "Pick Tier I, II or III" end
		l.Tier = tier
		l.Earned = true
		save(p, l)
		return true, l
	end
end

--------------------------------------------------------------------------
-- client
--------------------------------------------------------------------------
function Lineage.Get()
	local ps = Players.LocalPlayer:WaitForChild("PlayerScripts")
	local m = ps:WaitForChild("Controllers"):WaitForChild("StateController", 15)
	local ok, sc = pcall(require, m)
	local profile = ok and sc and sc.GetProfile(true)
	return Lineage.Sanitize(profile and profile.Lineage)
end

function Lineage.SetLookClient(slot: string, id: string)
	local f = ReplicatedStorage:WaitForChild(Lineage.RemotesName, 10)
	if not f then return false, "Offline" end
	local ok, a, b = pcall(function() return f:WaitForChild("SetLook"):InvokeServer(slot, id) end)
	if not ok then return false, "Failed" end
	return a, b
end

function Lineage.Spin(kind: string, slot: number?)
	local f = ReplicatedStorage:WaitForChild(Lineage.RemotesName, 10)
	if not f then
		return false, "Spins are offline"
	end
	local ok, a, b = pcall(function()
		return f:WaitForChild("Spin"):InvokeServer(kind, slot)
	end)
	if not ok then
		return false, "Spin failed"
	end
	return a, b
end

return Lineage

