--[[
	Cliques (Config). The social map of Nightmare High (owner, 2026-11-03: "heavily inspired by Bully: cliques and groups,
	with our theme on them"). Phase 1: who's in which clique, how they dress and talk, where they hang out, and your
	standing with each (saved per slot in PlayerData.Social.Cliques). Phase 2 (1.27): reactions by standing, turf
	confrontations, rival scuffles and the hall monitor (Services.Social.CliqueFights). Phase 3: turf, leader quests
	and rank rewards. Phase 4 (1.33): events: pranks (Services.Social.CliquePranks), rumble days (CliqueFights), the
	bulletin and daily dares (Services.Social.CliqueEvents; Cliques.Events below).

	The two joinable factions (Config.Factions: the Vigil, the Crimson Court) are cliques too; joining and faction ranks
	stay with Services.Social.Factions. Clique standing is how its members see you, from -100 to 100.

	Used by Services.Social.Cliques (standing, membership), Services.Features.Schedules (students' cliques and
	hangouts), Controllers.World.Chatter (their lines) and the phone's Cliques app.
]]

local Cliques = {}

local function rgb(r, g, b) return Color3.fromRGB(r, g, b) end

Cliques.Order = { `Vigil`, `Court`, `Athletes`, `Delinquents`, `Pack`, `Ordinary`, `Choir`, `Ink` }

Cliques.Defs = {
	Vigil = {
		Name = `The Vigil`; Archetype = `Scholars`; Color = rgb(235, 205, 120); Faction = `Vigil`;
		Tagline = `They dig through the school's records by lamplight.`;
		Hangout = `Archive`; HangoutName = `The Archive`; Leader = `Ezra Vale`; Rival = `Court`;
		Look = { Tops = { `vigil-vest`, `charcoal-cardigan` }; Bottoms = { `charcoal-slacks`, `khaki-trousers` }; FemaleBottoms = { `pleated-tartan-skirt` } };
		Lines = { `The records don't match. They never match.`, `Lamps lit? Good.`, `Have you read the founding charter?`, `Quiet. Someone's listening.`, `There's a page missing from 1893.` };
	};
	Court = {
		Name = `The Crimson Court`; Archetype = `Night elite`; Color = rgb(200, 40, 60); Faction = `CrimsonCourt`;
		Tagline = `The night's aristocrats. Crimson, silver and a long memory.`;
		Hangout = `CrimsonParlor`; HangoutName = `The Crimson Parlor`; Leader = `Vesper Crane`; Rival = `Vigil`;
		Look = { Tops = { `crimson-court-vest`, `black-blazer` }; Bottoms = { `charcoal-slacks` }; FemaleBottoms = { `pleated-tartan-skirt` };
			Civ = { Tops = { `victorian-waistcoat`, `hussar-coat` }; Bottoms = { `pinstripes-riding-boots` }; FemaleBottoms = { `pleated-tartan-skirt`, `black-skirt-fishnets` } } };
		Lines = { `Did you see what she was wearing? Tragic.`, `The night belongs to us.`, `Mind your manners near the Parlor.`, `Daddy owns half this town.`, `Crimson suits you. Almost.` };
	};
	Athletes = {
		Name = `The Athletes`; Archetype = `Jocks`; Color = rgb(90, 150, 220);
		Tagline = `Iron Wardens, Night Ravens and Grave Rovers. Win or bleed trying.`;
		Hangout = `Gymnasium`; HangoutName = `The Gymnasium`; Leader = `Captain Rhys Thorne`; Rival = `Ink`;
		Look = { Tops = { `varsity-jacket`, `gym-pe-shirt` }; Bottoms = { `striped-joggers`, `khaki-shorts` } };
		Lines = { `Did you see that catch last night?`, `Coach wants twenty more laps.`, `Ravens rule, Rovers drool.`, `Out of the way, I'm warming up.`, `Hydrate or die-drate.` };
	};
	Delinquents = {
		Name = `The Delinquents`; Archetype = `Greasers`; Color = rgb(150, 110, 70);
		Tagline = `Leather, smokes and the Back Lot. Rules are for other people.`;
		Hangout = `BackLot`; HangoutName = `The Back Lot`; Leader = `Bruno Vance`; Rival = `Ordinary`;
		Look = { Tops = { `delinquent-polo` }; Bottoms = { `uniform-trousers` };
			Civ = { Tops = { `leather-jacket`, `the-hollow-band-tee` }; Bottoms = { `black-jeans-boots`, `ripped-jeans` }; FemaleBottoms = { `black-skirt-fishnets` } } };
		Lines = { `What are you looking at?`, `Got a light?`, `The hall monitor can kiss my boots.`, `This lot's ours. Keep walking.`, `Nice shoes. Shame if something happened to them.` };
	};
	Pack = {
		Name = `The Pack`; Archetype = `Bullies`; Color = rgb(130, 150, 90);
		Tagline = `Wolf-blooded bruisers who shove first-years around for fun.`;
		Hangout = `Den`; HangoutName = `The Den`; Leader = `Dex Moreno`; Rival = `Choir`;
		Look = { Tops = { `forest-vest`, `forest-polo` }; Bottoms = { `khaki-trousers` };
			Civ = { Tops = { `open-flannel`, `blood-moon-hoodie` }; Bottoms = { `cargo-boots`, `dark-indigo-jeans` }; FemaleBottoms = { `black-skirt-fishnets` } } };
		Lines = { `Hey, first-year. Lunch money.`, `Smell that? Fear.`, `The moon's gonna be fat soon.`, `Move, or get moved.`, `Somebody's crying. Wasn't us. Probably.` };
	};
	Ordinary = {
		Name = `The Ordinary`; Archetype = `Regulars`; Color = rgb(200, 190, 170);
		Tagline = `Humans who just want to graduate alive. Safety in numbers.`;
		Hangout = `Commons`; HangoutName = `The Commons`; Leader = `Pip Larkin`; Rival = `Delinquents`;
		Look = { Tops = { `navy-vest`, `navy-polo`, `ivory-polo`, `red-vest` }; Bottoms = { `uniform-trousers`, `khaki-trousers` }; FemaleBottoms = { `pleated-tartan-skirt` } };
		Lines = { `Just keep your head down and graduate.`, `Did anyone else hear screaming last night?`, `I'm going home before dark.`, `Is it true about the full moon?`, `Strength in numbers, right?` };
	};
	Choir = {
		Name = `The Chapel Choir`; Archetype = `Faithful`; Color = rgb(230, 225, 210);
		Tagline = `Priest-blooded kids with candles, hymns and very sharp crosses.`;
		Hangout = `Chapel`; HangoutName = `The Chapel`; Leader = `Lucien Grey`; Rival = `Pack`;
		Look = { Tops = { `ivory-polo`, `black-blazer` }; Bottoms = { `charcoal-slacks` }; FemaleBottoms = { `pleated-tartan-skirt` } };
		Lines = { `Bless you. You need it.`, `Practice is at dusk. Don't be late.`, `The candles flickered again.`, `Something unholy walks these halls.`, `Hum it with me.` };
	};
	Ink = {
		Name = `The Ink Club`; Archetype = `Artists`; Color = rgb(150, 80, 190);
		Tagline = `Artists and pranksters from the paint-stained back rows.`;
		Hangout = `InkStudio`; HangoutName = `The Ink Studio`; Leader = `Wren Ashby`; Rival = `Athletes`;
		Look = { Tops = { `black-shirt`, `charcoal-vest` }; Bottoms = { `uniform-trousers`, `charcoal-slacks` }; FemaleBottoms = { `pleated-tartan-skirt` } };
		Lines = { `Art is just a prank that took longer.`, `Who moved my brushes?`, `I'm painting the gym doors tonight.`, `That wall needs a mural. A rude one.`, `Ink stains are a lifestyle.` };
	};
}

-- standing: how a clique's members see you
Cliques.Min, Cliques.Max = -100, 100
Cliques.Tiers = { -- highest Min first
	{ Name = `Respected`; Min = 60 };
	{ Name = `Friendly`; Min = 20 };
	{ Name = `Neutral`; Min = -10 };
	{ Name = `Wary`; Min = -40 };
	{ Name = `Hostile`; Min = -math.huge };
}
Cliques.Standing = {
	DownedMember = -8;      -- you put one of theirs on the floor
	RivalShare = 0.25;      -- the rival clique likes it a little (that share of the loss, as a gain)
}

function Cliques.Tier(Value: number): string
	for _, T in Cliques.Tiers do if Value >= T.Min then return T.Name end end
	return `Hostile`
end

-- the background students' cliques, by their schedule index (Services.Features.Schedules: 14 students)
Cliques.Students = { `Ordinary`, `Vigil`, `Court`, `Athletes`, `Ink`, `Ordinary`, `Choir`, `Pack`, `Delinquents`, `Vigil`, `Court`, `Athletes`, `Ink`, `Ordinary` }

-- named NPCs (Live / NHAmbient) and what they belong to
Cliques.Npcs = {
	[`Ezra Vale`] = `Vigil`; [`Vesper Crane`] = `Court`; [`Bruno Vance`] = `Delinquents`; [`Dex Moreno`] = `Pack`; [`Pip Larkin`] = `Ordinary`;
	[`Delinquent`] = `Delinquents`; [`Delinquent Brute`] = `Delinquents`;
	[`Push-up kid`] = `Athletes`; [`Sit-up kid`] = `Athletes`; [`Pull-up kid`] = `Athletes`; [`Gym regular`] = `Athletes`;
	[`Thinker`] = `Vigil`; [`Early bird`] = `Vigil`; [`Staff-room slacker`] = `Court`; [`Leaning kid`] = `Pack`;
	[`Detention kid`] = `Delinquents`; [`Napping student`] = `Ordinary`; [`Lunch kid`] = `Ordinary`;
}

-- the three new leaders (stand at their hangouts; quests come in Phase 3)
Cliques.NewLeaders = {
	{ Name = `Captain Rhys Thorne`; Clique = `Athletes`; Title = `Athletes captain`;
		Spec = { Body = 1; Skin = 3; Uniform = `varsity-jacket`; Bottoms = `striped-joggers`; Eyes = 2; Brows = `flatthick`; Mouth = `grin`; HairId = 1852838120 } };
	{ Name = `Lucien Grey`; Clique = `Choir`; Title = `Chapel Choir cantor`;
		Spec = { Body = 1; Skin = 1; Uniform = `black-blazer`; Bottoms = `charcoal-slacks`; Eyes = 4; Brows = `straight`; Mouth = `flat`; HairId = 2680376026 } };
	{ Name = `Wren Ashby`; Clique = `Ink`; Title = `Ink Club ringleader`;
		Spec = { Body = 2; Skin = 2; Uniform = `charcoal-vest`; Bottoms = `pleated-tartan-skirt`; Eyes = 5; Brows = `arched`; Mouth = `smirk`; HairId = 3612414364 } };
}

function Cliques.Sanitize(Raw)
	local Out = {}
	if type(Raw) ~= `table` then Raw = {} end
	for Id in Cliques.Defs do
		local V = tonumber(Raw[Id]) or 0
		Out[Id] = math.clamp(math.floor(V + 0.5), Cliques.Min, Cliques.Max)
	end
	return Out
end

---| Phase 2 (1.27): how each clique fights and what it says to you |---
-- Tier: the difficulty its fighters use (Config.NPC.Tiers); LeaderTier for its leader when leaders fight (Phase 3).
-- Fighter: the name over a fighter's head. Reactions: lines said to you by your standing tier (Neutral says the
-- clique's usual Lines). Taunt / Jeer / Leave: a turf confrontation (start, you're down, you got away).
-- Rally / Scatter: a scuffle (squaring off, a hall monitor breaks it up).
local PHASE2 = {
	Vigil = {
		Tier = `Normal`; LeaderTier = `Hard`; Fighter = `Vigil Warden`;
		Reactions = {
			Respected = { `Keeper. The lamps burn for you.`, `Good to see you. The archive is yours.`, `If you find anything, we listen.` };
			Friendly = { `Evening. Found anything odd?`, `Keep your eyes open, friend.`, `You're welcome in the stacks.` };
			Wary = { `We're watching what you do.`, `Careful where you put your hands.`, `Hm. You again.` };
			Hostile = { `Out of our archive.`, `You've made your choice. So have we.`, `We have records on you now.` };
		};
		Taunt = { `You were warned. Now you learn.`, `This is our archive.` };
		Jeer = { `Write that down.`, `Lesson over.` };
		Leave = { `And stay out of the stacks.` };
		Rally = { `For the Vigil!`, `Not in our halls!` };
		Scatter = { `Later. Remember their faces.` };
	};
	Court = {
		Tier = `Hard`; LeaderTier = `Nightmare`; Fighter = `Court Retainer`;
		Reactions = {
			Respected = { `The Court remembers its friends.`, `Do sit. You're one of us tonight.`, `Darling. Always a pleasure.` };
			Friendly = { `Charming as ever.`, `You may stay. For now.`, `Lovely evening for it, isn't it?` };
			Wary = { `Who invited you?`, `Mind the carpet.`, `How... common.` };
			Hostile = { `You have some nerve showing your face here.`, `The Court has a long memory.`, `Leave. Before we make you.` };
		};
		Taunt = { `Uninvited guests get shown out.`, `You'll regret this little visit.` };
		Jeer = { `On your knees suits you.`, `How tragic.` };
		Leave = { `Run along, peasant.` };
		Rally = { `For the Court!`, `Teach them manners!` };
		Scatter = { `We'll finish this somewhere quieter.` };
	};
	Athletes = {
		Tier = `Normal`; LeaderTier = `Hard`; Fighter = `Varsity Bruiser`;
		Reactions = {
			Respected = { `Captain's favourite! Want in on drills?`, `Yo, MVP!`, `Saved you a spot on the bench.` };
			Friendly = { `Nice hustle out there.`, `You lift?`, `Good game, good game.` };
			Wary = { `You're in the way.`, `Off the court, nerd.`, `Do you even play?` };
			Hostile = { `You're benched. Permanently.`, `Wrong gym, loser.`, `Somebody take this one out.` };
		};
		Taunt = { `Time for some extra practice.`, `You picked the wrong gym.` };
		Jeer = { `And that's the game!`, `Hit the showers.` };
		Leave = { `That's right, run laps.` };
		Rally = { `Team, on me!`, `Let's go, let's go!` };
		Scatter = { `Coach's coming, split!` };
	};
	Delinquents = {
		Tier = `Normal`; LeaderTier = `Hard`; Fighter = `Back Lot Tough`;
		Reactions = {
			Respected = { `Hey, it's our guy.`, `You need anything, you ask Bruno.`, `Nobody touches you on this lot.` };
			Friendly = { `You're alright.`, `Want a smoke? No? Suit yourself.`, `Cool shoes.` };
			Wary = { `What're you looking at?`, `Keep walking.`, `You lost?` };
			Hostile = { `You got a death wish?`, `Wrong lot, pal.`, `Boys, we got company.` };
		};
		Taunt = { `You don't belong here.`, `Let's rough this one up.` };
		Jeer = { `Stay down.`, `Shoulda kept walking.` };
		Leave = { `Yeah, you better run.` };
		Rally = { `Get 'em!`, `This lot's ours!` };
		Scatter = { `Cheese it, the monitor!` };
	};
	Pack = {
		Tier = `Hard`; LeaderTier = `Nightmare`; Fighter = `Pack Bruiser`;
		Reactions = {
			Respected = { `You run with us now.`, `Pack's got your back.`, `Smell that? Friend.` };
			Friendly = { `You're not prey. Today.`, `Hey. Want some?`, `Good night for it.` };
			Wary = { `I can smell you from here.`, `Back off.`, `You're twitchy. I like that.` };
			Hostile = { `Fresh meat walked into the Den.`, `Lunch money. All of it.`, `Bad night to be you.` };
		};
		Taunt = { `You smell like fear.`, `Fresh meat.` };
		Jeer = { `Whimper all you want.`, `Too easy.` };
		Leave = { `Run, little rabbit. Run.` };
		Rally = { `Pack up!`, `Get the choirboys!` };
		Scatter = { `Scatter! Into the trees!` };
	};
	Ordinary = {
		Tier = `Easy`; LeaderTier = `Normal`; Fighter = `Commons Regular`;
		Reactions = {
			Respected = { `Thanks for looking out for us.`, `You're a legend around here.`, `Sit with us at lunch?` };
			Friendly = { `Hey! You're the nice one.`, `Safe out there?`, `Strength in numbers, right?` };
			Wary = { `Please don't start anything.`, `Uh. Hi.`, `We don't want trouble.` };
			Hostile = { `Leave us alone.`, `You're just like the rest of them.`, `Go pick on someone else.` };
		};
		Taunt = { `We've had enough of you!`, `Strength in numbers!` };
		Jeer = { `Not so tough now!`, `We did it!` };
		Leave = { `And don't come back!` };
		Rally = { `Everyone, now!`, `We're not scared of you!` };
		Scatter = { `Oh no, the monitor!` };
	};
	Choir = {
		Tier = `Easy`; LeaderTier = `Normal`; Fighter = `Choir Acolyte`;
		Reactions = {
			Respected = { `Bless you, friend. Truly.`, `The candles burn brighter when you're near.`, `Sing with us tonight.` };
			Friendly = { `Peace be with you.`, `Come to practice sometime.`, `You have a kind soul.` };
			Wary = { `We'll pray for you.`, `Keep your distance.`, `Something about you is off.` };
			Hostile = { `Begone from this holy place.`, `You are not welcome here, sinner.`, `The cross remembers.` };
		};
		Taunt = { `Begone, foul thing!`, `The Chapel is protected.` };
		Jeer = { `Repent.`, `Mercy is for the faithful.` };
		Leave = { `Go, and sin no more.` };
		Rally = { `For the Chapel!`, `Drive them out!` };
		Scatter = { `Back inside, quickly!` };
	};
	Ink = {
		Tier = `Easy`; LeaderTier = `Normal`; Fighter = `Ink Club Prankster`;
		Reactions = {
			Respected = { `Our muse returns!`, `We named a mural after you.`, `You want to see the secret wall?` };
			Friendly = { `Nice colours today.`, `Pose for me sometime?`, `You've got an artist's eye.` };
			Wary = { `Don't touch the canvases.`, `Ugh. Philistine.`, `Mind the wet paint.` };
			Hostile = { `Get out of our studio.`, `You'd ruin a mural just by looking at it.`, `We'll paint you as a clown.` };
		};
		Taunt = { `Time to redecorate your face.`, `Out of our studio!` };
		Jeer = { `A masterpiece.`, `Now that's art.` };
		Leave = { `Go on, scram, critic.` };
		Rally = { `Paint them red!`, `For the Ink Club!` };
		Scatter = { `Hide the brushes!` };
	};
}
for Id, Extra in PHASE2 do
	for K, V in Extra do Cliques.Defs[Id][K] = V end
end

-- rival pairs that scuffle (each clique's Rival, counted once)
Cliques.RivalPairs = { { `Vigil`, `Court` }, { `Athletes`, `Ink` }, { `Delinquents`, `Ordinary` }, { `Pack`, `Choir` } }

Cliques.Fights = {
	TurfLinger = 8;           -- seconds in a Hostile clique's hangout before its members confront you
	ConfrontCooldown = 120;   -- seconds before the same clique confronts you again
	ConfrontCrew = { 2, 3 };  -- 2 members, 3 when the standing is at -70 or lower
	LetGoDistance = 30;       -- studs past their hangout's edge where they stop chasing you
	ConfrontTime = 90;        -- seconds a confrontation can last
	ScuffleEvery = 240;       -- seconds between scuffles (Break, After School, Evening)
	ScuffleKinds = { Break = true; AfterSchool = true; Evening = true; Lunch = true };
	ScuffleSeeRange = 120;    -- a player must be this close to the venue for a scuffle to start
	ScuffleSize = { 2, 3 };   -- per side
	ScuffleTime = 60;         -- seconds before both sides give up
	HelpDown = 6;             -- standing with a side for each of its rivals you put down in a scuffle
	HelpWin = 10;             -- more standing with that side if it wins with your help
	FacingRange = 10;         -- studs: students who respect or hate you turn to face you
	-- Phase 3 (1.28)
	TurfWins = 2;             -- scuffles a rival must win at a hangout in one in-game day to take it until 6 AM
	TurfBonus = 15;           -- standing with the winners for helping take (or take back) a hangout
	BackupCooldown = 90;      -- seconds between backups for the same student
}

---| Phase 3 (1.28): leader quests and rewards |---
-- Quests: the leader's two jobs (Config.Quests ids). Quest 1 opens at Neutral, quest 2 at Friendly.
-- Titles: Friendly earns the first; Respected plus quest 2 done unlocks the clique's reward (Social.Cliques): the
-- second title, its SignatureLook in the Wardrobe's Clique Looks (one click wears it; nothing else is ever locked), backup in
-- fights near its hangout (Social.CliqueFights), and its Perk if it has one.
local PHASE3 = {
	Vigil = { Quests = { `CliqueVigil1`, `CliqueVigil2` }; Titles = { `Lamplighter`, `Keeper of the Vigil` };
		SignatureLook = { Top = `vigil-vest`; Bottoms = `charcoal-slacks`; FemaleTop = `vigil-vest-f`; FemaleBottoms = `vigil-tartan` } };
	Court = { Quests = { `CliqueCourt1`, `CliqueCourt2` }; Titles = { `Guest of the Court`, `Blood of the Court` };
		SignatureLook = { Top = `crimson-court-vest`; Bottoms = `charcoal-slacks`; FemaleTop = `crimson-court-blazer`; FemaleBottoms = `court-pleats` } };
	Athletes = { Quests = { `CliqueAthletes1`, `CliqueAthletes2` }; Titles = { `Walk-on`, `Varsity` };
		SignatureLook = { Top = `varsity-jacket`; Bottoms = `striped-joggers`; FemaleTop = `varsity-jacket`; FemaleBottoms = `cheer-skirt` } };
	Delinquents = { Quests = { `CliqueDelinquents1`, `CliqueDelinquents2` }; Titles = { `Back Lot Regular`, `Back Lot Royalty` };
		SignatureLook = { Top = `leather-jacket`; Bottoms = `black-jeans-boots`; FemaleTop = `delinquent-long-blazer`; FemaleBottoms = `delinquent-long-skirt` };
		Perk = { Shop = `Boards`; Off = 0.25; Text = `25% off skateboards: Back Lot connections` } };
	Pack = { Quests = { `CliquePack1`, `CliquePack2` }; Titles = { `Friend of the Pack`, `Pack Blood` };
		SignatureLook = { Top = `open-flannel`; Bottoms = `cargo-boots`; FemaleTop = `moon-sweater`; FemaleBottoms = `corset-flares` } };
	Ordinary = { Quests = { `CliqueOrdinary1`, `CliqueOrdinary2` }; Titles = { `Good Neighbour`, `Pillar of the Commons` };
		SignatureLook = { Top = `navy-vest`; Bottoms = `uniform-trousers`; FemaleTop = `navy-vest-f`; FemaleBottoms = `navy-pleats` };
		Perk = { Shop = `Concession`; Off = 0.25; Text = `25% off at the concession stand: they run the lunch line` } };
	Choir = { Quests = { `CliqueChoir1`, `CliqueChoir2` }; Titles = { `Faithful`, `Voice of the Choir` };
		SignatureLook = { Top = `black-blazer`; Bottoms = `charcoal-slacks`; FemaleTop = `choir-capelet`; FemaleBottoms = `chapel-midi` } };
	Ink = { Quests = { `CliqueInk1`, `CliqueInk2` }; Titles = { `Muse`, `Ink Club Legend` };
		SignatureLook = { Top = `black-shirt`; Bottoms = `charcoal-slacks`; FemaleTop = `ink-club-blouse`; FemaleBottoms = `black-pleats-sheer` } };
}
for Id, Extra in PHASE3 do
	for K, V in Extra do Cliques.Defs[Id][K] = V end
end
Cliques.QuestOpen = { -10, 20 } -- standing needed for quest 1 (Neutral) and quest 2 (Friendly)

---| Phase 4 (1.33): events |---
-- Slogan: what their tags say. Pranked: what members say about a mess at their hangout. Shh: a prankster at work.
-- RumbleCall: the text that announces a rumble (from this clique's leader).
local PHASE4 = {
	Vigil = { Slogan = { `THE VIGIL REMEMBERS`, `LIGHTS ON`, `WE KEEP THE RECORDS` };
		Pranked = { `Who touched the archive?`, `Someone defaced the stacks.`, `This will be recorded.` };
		Shh = { `Quiet... quiet...`, `In and out.` } };
	Court = { Slogan = { `FANGS OUT`, `THE NIGHT IS OURS`, `CRIMSON` };
		Pranked = { `In OUR parlor? How vulgar.`, `Someone will pay for this.`, `Disgusting. Find who did it.` };
		Shh = { `Elegance, darling. Quickly.`, `Not a sound.` } };
	Athletes = { Slogan = { `VARSITY`, `GO TEAM`, `UNDEFEATED` };
		Pranked = { `Who wrecked the court?!`, `Foul! That's a foul!`, `Somebody's getting benched.` };
		Shh = { `Quick play, quick play.`, `Hut, hut... quietly.` } };
	Delinquents = { Slogan = { `BACK LOT RULES`, `NO COPS`, `GREASE` };
		Pranked = { `Who messed with the Lot?`, `Somebody's asking for it.`, `Ain't funny.` };
		Shh = { `Keep it down, keep it down.`, `Lookout's on.` } };
	Pack = { Slogan = { `PACK RUNS THIS`, `BITE ME`, `ALPHA` };
		Pranked = { `Who's been in the Den?`, `Smells like a dead man walking.`, `We'll find them.` };
		Shh = { `Heh. Watch this.`, `Nobody's gonna know.` } };
	Ordinary = { Slogan = { `REGULAR & PROUD`, `HI MOM`, `THE COMMONS` };
		Pranked = { `Aw, come on, we just cleaned!`, `Who would DO this?`, `That's not nice.` };
		Shh = { `Is this okay? This is okay.`, `Sorry, sorry...` } };
	Choir = { Slogan = { `REPENT`, `AMEN`, `SING OUT` };
		Pranked = { `In the chapel? Have they no shame?`, `Lord, give me patience.`, `This is a holy place!` };
		Shh = { `Forgive me...`, `Quick, before vespers.` } };
	Ink = { Slogan = { `ART IS A WEAPON`, `INK CLUB`, `BEIGE IS DEAD` };
		Pranked = { `They ruined the light in here!`, `Philistines.`, `Who did THIS? It's not even good.` };
		Shh = { `A masterpiece takes time...`, `Shh, I'm working.` } };
}
for Id, Extra in PHASE4 do
	for K, V in Extra do Cliques.Defs[Id][K] = V end
end

---| Phase 5 (1.34): leader showdowns (Services.Social.CliqueShowdowns) |---
-- Challenge: the leader's text to a student they're Hostile with. Call: at half health, to the ring. Beaten: when you win.
-- Gloat: when they win. Crown: their text when you become King (or Queen) of the School.
local PHASE5 = {
	Vigil = { Challenge = `The Archive. After school. Come alone. The Vigil settles its accounts in person.`; Call = { `Wardens! To me!` }; Beaten = `...Noted. Recorded. You've earned the Vigil's respect.`; Gloat = { `Write that down. You lost.` }; Crown = `Every record in the school has your name on it now. Long live the King.` };
	Court = { Challenge = `The Parlor. After school. Come alone, if you have the stomach for it.`; Call = { `Retainers. Deal with this.` }; Beaten = `You... actually won. How tiresome. The Court bows to you.`; Gloat = { `Did you really think you could touch me?` }; Crown = `The whole school kneels to you now. Even the Court. Don't let it go to your head... too much.` };
	Athletes = { Challenge = `Gym. After school. Just you and me, no subs.`; Call = { `Team! Get in here!` }; Beaten = `Good game. Seriously. You've got the whole team's respect.`; Gloat = { `That's game. Hit the showers.` }; Crown = `MVP of the whole school. Every team wants you. Even mine.` };
	Delinquents = { Challenge = `Back Lot, after school. Come alone. Let's settle this.`; Call = { `Get in here!` }; Beaten = `Okay, okay. You're the real deal. The Lot's got your back.`; Gloat = { `Stay down, kid.` }; Crown = `The whole school's yours now, King. Even the Lot.` };
	Pack = { Challenge = `The Den. After school. Come alone. Or don't come at all.`; Call = { `Pack! Get 'em!` }; Beaten = `Heh. Okay. You're Pack now, whether you like it or not.`; Gloat = { `Alpha's still alpha.` }; Crown = `Everybody bows to you now. Even the Pack. Don't make me regret it.` };
	Ordinary = { Challenge = `Um. The Commons, after school? Come alone, please? This is very scary for me.`; Call = { `Guys? GUYS! Help!` }; Beaten = `I lost! But that was amazing! Everybody, they're one of us now!`; Gloat = { `I... I won? I WON!` }; Crown = `You did it! You're the King of the School! I'm telling everyone!` };
	Choir = { Challenge = `The Chapel. After school. Come alone and repent.`; Call = { `Brothers, sisters! Stand with me!` }; Beaten = `Truly, you were sent to test us. The Choir honours you.`; Gloat = { `Go in peace. And humility.` }; Crown = `The whole school sings your name now. Even the Choir.` };
	Ink = { Challenge = `Ink Studio. After school. Come alone. I want this to be art.`; Call = { `Club! Paint them red!` }; Beaten = `Ugh. That was beautiful. You're one of us now.`; Gloat = { `That's what I call performance art.` }; Crown = `The whole school is your canvas now, your majesty.` };
}
for Id, Extra in PHASE5 do
	for K, V in Extra do Cliques.Defs[Id][K] = V end
end

Cliques.Showdown = {
	RingSize = 5;              -- members who stand round the fight
	RingRadius = 14;           -- studs from the hangout's middle
	Backup = 2;                -- ring members who join the leader at half health
	ForfeitDistance = 30;      -- studs past the hangout's edge: you ran, it's a forfeit
	FoeLoss = -5;              -- more standing lost when a Hostile leader beats you
	FoeKinds = { AfterSchool = true; Evening = true }; -- when a challenge can be answered
	LeaderHealth = { Easy = 110; Normal = 130; Hard = 160; Nightmare = 190 };
	ShoutEvery = 6;            -- seconds between the ring's shouts
	KingOff = 0.10;            -- King of the School: 10% off at every shop
	KingTitle = { `King of the School`, `Queen of the School` };
}

---| Phase 6 (1.35): joining a clique (Services.Social.CliqueMembership) |---
-- Joined / Betrayed: the leader's lines when you join or walk out. Greet: members greeting you ({Name} = your first name).
local PHASE6 = {
	Athletes = { Joined = `Welcome to the team. You wear our colours now. Don't make me regret it.`; Betrayed = `Quitter. You're off the team, and you're not welcome in my gym. We'll settle this.`; Greet = { "Yo, {Name}! Good to see you.", "{Name}! Team's here.", "Looking strong, {Name}." } };
	Delinquents = { Joined = `Welcome to the Lot, kid. You're one of us now.`; Betrayed = `You walked out on the Lot? Nobody walks out on the Lot. You'll hear from me.`; Greet = { "{Name}! What's up.", "Hey {Name}, you good?", "{Name}'s here. Nobody start nothing." } };
	Pack = { Joined = `You're Pack now. We look after our own.`; Betrayed = `You think you can just leave the Pack? Come to the Den. We'll talk about it.`; Greet = { "{Name}. Pack.", "Heh, {Name}'s here.", "Look who it is. {Name}." } };
	Ordinary = { Joined = `You're one of us! Welcome to the Commons! We have snacks!`; Betrayed = `You... left? After everything? I thought we were friends. That's not okay.`; Greet = { "Hi {Name}!", "Oh, hey {Name}!", "{Name}! Want a snack?" } };
	Choir = { Joined = `Welcome, brother. Sister. The Choir sings for you now.`; Betrayed = `You have turned your back on the Choir. Come to the Chapel and answer for it.`; Greet = { "Blessings, {Name}.", "Peace be with you, {Name}.", "Good to see you, {Name}." } };
	Ink = { Joined = `You're in the Ink Club now. Try to be interesting.`; Betrayed = `You're leaving the Club? How derivative. We'll see you at the Studio. Come ready.`; Greet = { "{Name}! Darling.", "Oh, it's {Name}. Inspiring.", "{Name}, you look... avant-garde." } };
}
for Id, Extra in PHASE6 do
	for K, V in Extra do Cliques.Defs[Id][K] = V end
end

-- One crowd at a time. The Vigil and the Court are joined through Social.Factions; the other six through Social.CliqueMembership
-- (Respected and their leader's showdown won). Leaving one of the six is a betrayal.
Cliques.Membership = {
	Joinable = { `Athletes`, `Delinquents`, `Pack`, `Ordinary`, `Choir`, `Ink` };
	JoinAt = 60;               -- Respected
	Ranks = { { Name = `Hanger-on`; Min = 60 }, { Name = `Member`; Min = 75 }, { Name = `Lieutenant`; Min = 90 } };
	Crew = { Member = 1; Lieutenant = 2 }; -- members who walk with you outside class
	CrewRespawn = 60;          -- seconds before a downed crew member is replaced
	BetrayTo = -50;            -- standing after you walk out (Hostile)
	LieutenantBonus = 1.5;     -- member jobs pay this much more
	GreetEvery = 60;           -- seconds between greetings from the same student
}

Cliques.Events = {
	-- pranks (Services.Social.CliquePranks)
	PrankEvery = 360;          -- seconds between NPC pranks (Break, Lunch, After School, Evening)
	PrankKinds = { Break = true; Lunch = true; AfterSchool = true; Evening = true };
	PrankSeeRange = 120;       -- a player must be this close to the target hangout for an NPC prank to start
	PrankTime = 6;             -- seconds an NPC prankster works (half that with a player keeping watch)
	PrankSpots = 2;            -- prank spots per hangout, when the map doesn't place its own (NHPrankSpot)
	PrankStop = 6;             -- standing with the victims for each prankster you put down mid-prank
	PrankHelp = 6;             -- keeping watch: + with the pranksters, - with the victims
	PrankClean = 3;            -- cleaning a mess: + with the victims (once per mess)
	PrankMine = -15;           -- your own prank: with the victims
	PrankMineRival = 8;        -- your own prank: with the victims' rival
	PrankHold = 4;             -- seconds to hold E for your own prank
	CleanHold = 3;             -- seconds to hold E to clean a mess
	PrankSeen = 20;            -- studs: a victim member this close who can see you comes for you
	-- rumble days (Services.Social.CliqueFights)
	RumbleEveryDays = 3;       -- in-game days between rumbles (each announced the day before)
	RumbleVenue = `Ordinary`;  -- whose hangout holds the rumble: the Ordinary's, the Commons (its gathering spots)
	RumbleWaves = 3;           -- waves per side
	RumbleSize = 3;            -- fighters per wave
	RumbleTime = 240;          -- seconds at most
	RumbleMonitor = 60;        -- seconds before the hall monitor comes ("Break it up!": they keep going)
	RumbleStaff = 120;         -- seconds before a coach comes and ends it
	RumbleStartRange = 160;    -- a player this close to the venue after school starts it (else 10 in-game minutes in)
	RumbleWin = 15;            -- standing with your side if it wins with your help (HelpDown still counts each down)
	-- dares (Services.Social.CliqueEvents, Config.Quests Dare = true)
	DaresPerDay = { 1, 3 };    -- leaders who text you a dare each morning (Neutral or better with you)
	TextsKept = 30;            -- texts kept on the phone (PlayerData.Phone.Texts)
}

-- the in-game day an event belongs to: days run 6 AM to 6 AM (turf, dares, prank kits, messes)
function Cliques.EventDay(State): number?
	if not (State and State.Day) then return nil end
	local Hour = State.Hour or ((State.MinuteOfDay or 720) / 60)
	return if Hour >= 6 then State.Day else State.Day - 1
end

-- the discount a student's unlocked clique rewards give at a shop (Concession / Boards): a price multiplier
function Cliques.PriceFactor(Player: Player, Shop: string): number
	local Off = 0
	for Id, D in Cliques.Defs do
		if D.Perk and D.Perk.Shop == Shop and Player:GetAttribute(`CliqueReward_{Id}`) == true then Off = math.max(Off, D.Perk.Off) end
	end
	-- (1.34) King / Queen of the School: off at every shop
	if Player:GetAttribute(`NHKing`) == true then Off = math.max(Off, Cliques.Showdown.KingOff or 0.1) end
	return 1 - Off
end

---| (line matrix) what you wear: NHWear, the clique looks, taste |---

-- what a character wears, from its NHWear attribute ("top|bottoms|acc,acc"; set by UI.Appearance.ApplyTo)
function Cliques.ParseWear(W: any): { Top: string, Bottoms: string, Acc: { string } }?
	if typeof(W) ~= `string` then return nil end
	local Top, Bottoms, Acc = string.match(W, `^([^|]*)|([^|]*)|(.*)$`)
	if not Top then return nil end
	local List = {}
	for Id in string.gmatch(Acc, `[^,]+`) do table.insert(List, Id) end
	return { Top = Top; Bottoms = Bottoms; Acc = List }
end

local function listed(L: { string }?, Id: string?): boolean
	return L ~= nil and Id ~= nil and Id ~= `` and table.find(L, Id) ~= nil
end

-- wearing one of a clique's tops (school or civvies, boys' or girls')
function Cliques.WearsTop(Id: string, Top: string?): boolean
	local L = Cliques.Defs[Id] and Cliques.Defs[Id].Look
	if not L then return false end
	return listed(L.Tops, Top) or listed(L.FemaleMatchTops, Top) or (L.Civ ~= nil and listed(L.Civ.Tops, Top))
end

function Cliques.WearsBottoms(Id: string, Bottoms: string?): boolean
	local L = Cliques.Defs[Id] and Cliques.Defs[Id].Look
	if not L then return false end
	return listed(L.Bottoms, Bottoms) or listed(L.FemaleBottoms, Bottoms) or listed(L.FemaleMatchBottoms, Bottoms)
		or (L.Civ ~= nil and (listed(L.Civ.Bottoms, Bottoms) or listed(L.Civ.FemaleBottoms, Bottoms)))
end

-- the girls' versions of each clique's school top that count towards its look (a NEW key, like FemaleMatchBottoms:
-- the NPC dressers read Look.FemaleTops and must not change)
local FemaleMatchTops = {
	Vigil = { `vigil-vest-f` }; Court = { `crimson-court-blazer` }; Athletes = { `cheer-uniform`, `track-jacket` };
	Delinquents = { `delinquent-long-blazer` }; Pack = { `forest-vest-f` }; Ordinary = { `navy-vest-f`, `crest-blazer` };
	Choir = { `choir-capelet`, `chapel-corset` }; Ink = { `ink-club-blouse` };
}
for Id, Tops in FemaleMatchTops do
	local Look = Cliques.Defs[Id] and Cliques.Defs[Id].Look
	if Look then Look.FemaleMatchTops = Tops end
end

-- girls' bottoms that count towards a clique's look (a NEW key: the NPC dressers read FemaleBottoms and must not change)
local FemaleMatchBottoms = {
	Athletes = { `cheer-skirt` }; Delinquents = { `delinquent-long-skirt` }; Pack = { `forest-tartan` };
}
for Id, Bottoms in FemaleMatchBottoms do
	local Look = Cliques.Defs[Id] and Cliques.Defs[Id].Look
	if Look then Look.FemaleMatchBottoms = Bottoms end
end

-- what each clique likes and mocks on you (Config.Accessories ids; a clique never likes what its rival likes)
local Taste = {
	Vigil = {
		Likes = { { Id = `watch-pocket` }, { Id = `lantern-candle` }, { Id = `tube-scroll` }, { Id = `coat-scholar` }, { Id = `coat-lamplighter` }, { Id = `book-strap` }, { Id = `pin-vigil` } };
		Mocks = { { Id = `hat-fascinator` }, { Id = `mask-gilt` }, { Id = `jacket-smoking` }, { Id = `parasol-lace` }, { Id = `pin-court` } };
	};
	Court = {
		Likes = { { Id = `hat-top` }, { Id = `mask-gilt` }, { Id = `clasp-opera` }, { Id = `jacket-smoking` }, { Id = `ring-bat-signet` }, { Id = `parasol-lace` }, { Id = `hat-fascinator` }, { Id = `pin-court` } };
		Mocks = { { Id = `coat-lamplighter` }, { Id = `bag-messenger` }, { Id = `tube-scroll` }, { Id = `cloak-oilskin` }, { Id = `pin-vigil` } };
	};
	Athletes = {
		Likes = { { Id = `jacket-varsity` }, { Id = `pin-athletes` }, { Id = `scarf-knit-crimson` }, { Id = `bag-messenger` } };
		Mocks = { { Id = `grimoire-chained` }, { Id = `case-violin` }, { Id = `collar-ruff` }, { Id = `parasol-lace` }, { Id = `pin-ink` } };
	};
	Delinquents = {
		Likes = { { Id = `coat-delinquent` }, { Id = `pin-delinquents` }, { Id = `mask-grille` }, { Id = `pauldrons-blackened` }, { Id = `gorget-steel` } };
		Mocks = { { Id = `sash-prefect` }, { Id = `tie-bow` }, { Id = `umbrella-crook` }, { Id = `book-strap` }, { Id = `pin-ordinary` } };
	};
	Pack = {
		Likes = { { Id = `necklace-wolf-fang` }, { Id = `fur-torn` }, { Id = `mask-wolf` }, { Id = `torc-moonstone` }, { Id = `jacket-hunting` }, { Id = `pin-pack` } };
		Mocks = { { Id = `collar-choir` }, { Id = `mask-wax` }, { Id = `pendant-crystal` }, { Id = `pin-choir` } };
	};
	Ordinary = {
		Likes = { { Id = `umbrella-crook` }, { Id = `cloak-oilskin` }, { Id = `tie-school` }, { Id = `coat-cardigan` }, { Id = `coat-cadet` }, { Id = `pin-ordinary` } };
		Mocks = { { Id = `mask-bone` }, { Id = `pendant-scythe` }, { Id = `crossbow-hunter` }, { Id = `pin-delinquents` } };
	};
	Choir = {
		Likes = { { Id = `collar-choir` }, { Id = `collar-ruff` }, { Id = `mask-wax` }, { Id = `pendant-crystal` }, { Id = `halo-rune` }, { Id = `pin-choir` } };
		Mocks = { { Id = `mask-wolf` }, { Id = `necklace-wolf-fang` }, { Id = `hat-witch` }, { Id = `grimoire-chained` }, { Id = `pin-pack` } };
	};
	Ink = {
		Likes = { { Id = `mask-fox` }, { Id = `mask-moth` }, { Id = `mask-domino` }, { Id = `backpack-batwing` }, { Id = `scarf-knit-violet` }, { Id = `bag-satchel` }, { Id = `pin-ink` } };
		Mocks = { { Id = `jacket-varsity` }, { Id = `sash-prefect` }, { Id = `sash-head` }, { Id = `tie-school` }, { Id = `pin-athletes` } };
	};
}
for Id, T in Taste do
	if Cliques.Defs[Id] then Cliques.Defs[Id].Taste = T end
end

return Cliques
