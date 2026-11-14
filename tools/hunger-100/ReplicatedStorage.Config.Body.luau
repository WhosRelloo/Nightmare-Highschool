--[[
	Config.Body (Hunger 1.0, phases 1 and 2 of docs/Hunger-and-Body-Concept.md). Shared by the server and the client.

	Hunger is a need from 0 to 100 that falls while you play and rises when you eat your race's food. It is NOT the
	Races 1.2 "hunger" (PlayerData.Lineage.Hunger, the Bloodline meter that only rises and opens the rites); feeding
	still fills that one through Evolution.Feed as before.

	Saved in PlayerData.Body = { Hunger, LastTick, Reserve, Race, V } (action SetBody), written only by Services.Features.Body.
	Mirrored as the player attributes Hunger (0-100, one decimal) and HungerBand.
	The body drift (Reserve, builds) is phase 3; Reserve is kept at 0 until then.
]]
local Body = {}

Body.V = 1
Body.Max = 100
Body.Start = 70            -- a new student (and a save from before hunger) starts Full
Body.TurnedTo = 60         -- a new race (the bite, a race spin) starts Fed, never starving
Body.OfflineFloor = 35     -- away from the game, hunger never falls below Peckish
Body.OfflineRate = 0.25    -- and falls at a quarter of the rate on the way down
Body.Decay = 0.55 / 60     -- per second of play, before the race's factor: about 33 an hour
Body.ComaSeconds = 120     -- reaching Stuffed: two minutes of food coma

-- bands, highest first: Min is inclusive
Body.Bands = {
	{ Id = `Stuffed`; Min = 90 };
	{ Id = `Full`; Min = 70 };
	{ Id = `Fed`; Min = 40 };
	{ Id = `Peckish`; Min = 20 };
	{ Id = `Hungry`; Min = 5 };
	{ Id = `Starving`; Min = 0 };
}
Body.BandIndex = {}
for I, B in Body.Bands do Body.BandIndex[B.Id] = I end

-- what each band does (Progression effect keys; Services.Player.Progression adds them as the source "Hunger")
Body.BandEffects = {
	Stuffed = {};
	Full = {};
	Fed = {};
	Peckish = {};
	Hungry = { DamageDealt = -0.04; Stealth = 0.05 };            -- a growling stomach: 5% easier to spot
	Starving = { DamageDealt = -0.08; Stealth = 0.05; ClassExp = -0.10 };
}
Body.ComaEffects = { SprintSpeed = -0.06 }

-- the band's name in each race's own words (the vessel's enamel plate)
Body.Words = {
	Human = { Stuffed = `Stuffed`; Full = `Full`; Fed = `Fed`; Peckish = `Peckish`; Hungry = `Hungry`; Starving = `Starving` };
	Priest = { Stuffed = `Sated`; Full = `Blessed`; Fed = `Fed`; Peckish = `Fasting`; Hungry = `Hungry`; Starving = `Faint` };
	Vampire = { Stuffed = `Gorged`; Full = `Sated`; Fed = `Fed`; Peckish = `Thirsting`; Hungry = `Parched`; Starving = `Starving` };
	Werewolf = { Stuffed = `Gorged`; Full = `Full`; Fed = `Fed`; Peckish = `Prowling`; Hungry = `Ravenous`; Starving = `Starving` };
	Ghoul = { Stuffed = `Gorged`; Full = `Full`; Fed = `Fed`; Peckish = `Gnawing`; Hungry = `Hollow`; Starving = `Frenzied` };
	Wraith = { Stuffed = `Warm`; Full = `Kindled`; Fed = `Steady`; Peckish = `Thin`; Hungry = `Fading`; Starving = `Hollow` };
}

-- the race colour (text, glow, splash); the vessel art carries the rest
Body.Colours = {
	Human = Color3.fromRGB(255, 176, 92);
	Priest = Color3.fromRGB(255, 226, 150);
	Vampire = Color3.fromRGB(255, 76, 150); -- ruby-magenta: a gem, never blood
	Werewolf = Color3.fromRGB(226, 232, 255);
	Ghoul = Color3.fromRGB(150, 255, 110);
	Wraith = Color3.fromRGB(150, 200, 255);
}

-- how the HUD fills the vessel: Rise (from the bottom), Wipe (left to right, the moon), Fade (the wisp brightens)
Body.FillMode = { Human = `Rise`; Priest = `Rise`; Vampire = `Rise`; Werewolf = `Wipe`; Ghoul = `Rise`; Wraith = `Fade` }

--[[ the races. Food = share of a food's hunger a plain meal gives; Decay = factor on Body.Decay.
	Feeds = racial grips (Downed.OnExecuted Kind) and what they give. Extra = items with their own value for this race.
	Phase 4 adds the Priest's fast, the Vampire's Sanguine Tonic, the Ghoul's Charnel Tins, Wraith warmth by lights,
	Fade, and the frenzies. ]]
Body.Races = {
	Human = { Food = 1; Decay = 1 };
	Priest = { Food = 1; Decay = 1; Extra = { HolyLemonade = 14 } };
	Vampire = { Food = 0.25; Decay = 1; DayDecay = 1.25; NightDecay = 0.75; CrimsonDecay = 0; Feeds = { BloodDrain = 45 } };
	Werewolf = { Food = 1; Decay = 1; Meaty = 1.5; Sweet = 0.5; FullMoonDecay = 2; Feeds = { Maul = 35; EatBody = 35 } };
	Ghoul = { Food = 0; Decay = 0.6; Extra = { MeatLoaf = 25 }; Feeds = { EatBody = 55 } };
	-- Wraiths don't eat. Until phase 4's warmth, they draw on a crowd: 3+ others within 12 studs
	Wraith = { Food = 0; Decay = 1; NewMoonDecay = 0.5; Feeds = { SoulSiphon = 40 };
		Crowd = { Radius = 12; Count = 3; PerMinute = 2 } };
}

-- sub-races: Decay multiplies the race's own; FullMoon / Meaty replace the race's; Radius replaces the crowd radius
Body.Subs = {
	Superhuman = { Decay = 1.2 };
	Ghast = { Decay = 0.5 / 0.6 };
	CryptLord = { Decay = 0.4 / 0.6 };
	Bloodmoon = { FullMoonDecay = 2.2; Meaty = 1.7 };
	Alpha = { FullMoonDecay = 2.4; Meaty = 1.9 };
	Revenant = { Radius = 14 };
	HollowKing = { Radius = 18 };
}

-- food families (Config.Items ids)
Body.Meaty = { Nikuman = true; YakitoriSkewers = true; KaraageSet = true; MeatLoaf = true; RavensRoast = true;
	ShepherdsPie = true; KatsuCurry = true; TakoyakiBoat = true; MackerelSet = true }
Body.Sweet = { BatGummies = true; CandyApple = true; GhostMints = true; KonpeitoStars = true; LicoriceWhips = true;
	ChocolateBar = true; Dango = true; Taiyaki = true; PuddingCup = true; TombstoneCookie = true; CreamPuff = true;
	MoonCake = true; MelonBread = true; StrawberryMilk = true; HotCocoa = true; ChocolateMilk = true }

-- a food's plain hunger, from its size (an item's own Hunger field wins)
function Body.ItemHunger(It): number
	if typeof(It) ~= `table` then return 0 end
	if typeof(It.Hunger) == `number` then return It.Hunger end
	if It.Kind == `Buff` then return 4 end
	if It.Kind ~= `Heal` then return 0 end
	if It.Lunch then return 40 end
	local H = It.Heal or 0
	if H <= 15 then return 8 end
	if H <= 40 then return 14 end
	if H <= 80 then return 24 end
	return 40
end

-- a snack-tin bite (Inventory.KitEat) is plain food of that heal
function Body.HealHunger(Heal: number): number
	return Body.ItemHunger({ Kind = `Heal`; Heal = Heal })
end

local function race(RaceId: string?)
	return Body.Races[RaceId or ``] or Body.Races.Human
end

local function sub(SubId: string?)
	return Body.Subs[SubId or ``] or {}
end

-- what eating this item gives this race (0 = it doesn't sate them)
function Body.Gain(RaceId: string?, SubId: string?, It): number
	local R = race(RaceId)
	if typeof(It) ~= `table` then return 0 end
	if R.Extra and R.Extra[It.Id] then return R.Extra[It.Id] end
	local Base = Body.ItemHunger(It)
	local K = R.Food
	if R.Meaty and Body.Meaty[It.Id] then K = sub(SubId).Meaty or R.Meaty end
	if R.Sweet and Body.Sweet[It.Id] then K = R.Sweet end
	return Base * K
end

-- what a racial grip gives (Kind from Downed.OnExecuted)
function Body.FeedGain(RaceId: string?, Kind: string?): number
	local R = race(RaceId)
	return R.Feeds and R.Feeds[Kind or ``] or 0
end

-- Ctx = { Night, FullMoon, NewMoon, Crimson } -> hunger lost per second of play
function Body.DecayRate(RaceId: string?, SubId: string?, Ctx): number
	local R, S = race(RaceId), sub(SubId)
	Ctx = Ctx or {}
	local K = R.Decay * (S.Decay or 1)
	if R.DayDecay then
		if Ctx.Night then
			K *= if Ctx.Crimson and R.CrimsonDecay then R.CrimsonDecay else R.NightDecay
		else
			K *= R.DayDecay
		end
	end
	if R.FullMoonDecay and Ctx.FullMoon then K *= S.FullMoonDecay or R.FullMoonDecay end
	if R.NewMoonDecay and Ctx.NewMoon then K *= R.NewMoonDecay end
	return Body.Decay * K
end

-- the offline rate ignores the time of day and the moon (the race's base factor only)
function Body.OfflineDecay(RaceId: string?, SubId: string?): number
	local R, S = race(RaceId), sub(SubId)
	return Body.Decay * R.Decay * (S.Decay or 1) * Body.OfflineRate
end

function Body.Crowd(RaceId: string?, SubId: string?)
	local R = race(RaceId)
	if not R.Crowd then return nil end
	local S = sub(SubId)
	return { Radius = S.Radius or R.Crowd.Radius; Count = R.Crowd.Count; PerMinute = R.Crowd.PerMinute }
end

-- does plain food do anything for this race? (the snack wheel greys food out when not)
function Body.EatsFood(RaceId: string?): boolean
	return race(RaceId).Food > 0
end

function Body.Band(Hunger: number): string
	for _, B in Body.Bands do
		if Hunger >= B.Min then return B.Id end
	end
	return `Starving`
end

function Body.Word(RaceId: string?, Band: string): string
	local W = Body.Words[RaceId or ``] or Body.Words.Human
	return W[Band] or Band
end

function Body.Sanitize(Raw: any)
	local Out = { Hunger = Body.Start; LastTick = 0; Reserve = 0; V = Body.V }
	if typeof(Raw) ~= `table` then return Out end
	local H = Raw.Hunger
	if typeof(H) == `number` and H == H then Out.Hunger = math.clamp(H, 0, Body.Max) end
	local T = Raw.LastTick
	if typeof(T) == `number` and T == T and T > 0 then Out.LastTick = math.floor(T) end
	local R = Raw.Reserve
	if typeof(R) == `number` and R == R then Out.Reserve = math.clamp(R, -100, 100) end
	if typeof(Raw.Race) == `string` and #Raw.Race <= 24 then Out.Race = Raw.Race end
	return Out
end

--[[ the art (group 15981569). 0 = not uploaded yet: the HUD draws its stand-in vessel. Per race:
	Back (the vessel spent), Fill (the contents brimming, cut to the contents), Glow (the contents' halo),
	Shared: Frost (the cold creeping in: Hungry and Starving), Plate (the band plate, 9-slice), Splash, Mote.
	Upload names: Hunger<Race>Back / Fill / Glow, HungerFrost, HungerPlate, HungerSplash, HungerMote. ]]
Body.Art = { -- (Hunger 1.0) the owner's import of art/group-upload-hunger, read by name from the group
	Human = { Back = 84764828890865; Fill = 92501604024020; Glow = 131245003988873 };
	Priest = { Back = 94070707547013; Fill = 130948692528601; Glow = 125824448438035 };
	Vampire = { Back = 101890322150335; Fill = 102798096485969; Glow = 101568386950431 };
	Werewolf = { Back = 122077151490816; Fill = 98116974505580; Glow = 139388068287737 };
	Ghoul = { Back = 98067528481264; Fill = 131095693419592; Glow = 80220184230970 };
	Wraith = { Back = 121840574269645; Fill = 138836639263225; Glow = 135538733937729 };
	Plate = 84440332534399; Splash = 98543895840857; Mote = 131916021444619; Frost = 95255146828905; -- Frost is shared; a race's own Frost wins
}
-- the art's measurements (art/ui/hud/out/hunger/layout.json, written by finish_hunger_vessels.py): every race shares
-- one 264 x 552 frame; ArtFill is where the contents sit in it (fractions), the HUD's level runs between Top and Bottom
Body.ArtAspect = 0.4783
Body.ArtFill = { Left = 0.2159; Right = 0.7841; Top = 0.4579; Bottom = 0.8525 }
Body.PlateSize = { 485, 120 }
Body.PlateSlice = { 36, 30, 449, 90 }

return Body
