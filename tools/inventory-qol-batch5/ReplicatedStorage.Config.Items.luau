--[[
	Consumables (shared). ReplicatedStorage.Config.Items
	Snacks and drinks from the concession stand (Services.Features.Concession), kept in your Locker
	(Services.Features.Inventory, saved in PlayerData.Inventory) and eaten from the hotbar (pin up to 4).

	Kind  Heal  restores Heal health over Duration seconds (half while you're combat-tagged).
	          Food shares one "full" cooldown (Config.Cooldown.Heal).
	      Buff  a snack buff for Duration seconds. Only one buff at a time: a new one replaces the old.
	      Prank (1.33) a prank kit: hold E on a prank spot at another clique's hangout (Services.Social.CliquePranks).
	          DailyLimit: the stand sells at most that many a day (6 AM to 6 AM; Inventory.Daily).
	          Buff effects use the same keys as Config.Progression (they add to your sheet while active).
	Balance: buffs stay under one Common gear piece's budget for their length (Config.Gear), so snacks help
	without beating levelling or gear.

	(1.39) The daily special: items with Special = 1..5 are sold only on that school day (Monday = 1; the 6 AM event
	day, like the dares), one each a day (DailyLimit 1). Race = { [race] = { Mult = n } or { Effects = {...} }, Note }
	twists the buff for one race (Items.EffectsFor). Items.TodaySpecial() works on the server and the client
	(ReplicatedStorage.SchoolClock's Epoch); the Gazette, the stand's menu board and the Midnight Bell notice board show it.

	(batch 54) The concession kit adds 26 snacks to Items.List and the lunch meals in Items.Lunch (Lunch = true,
	sold only while ReplicatedStorage's NHLunchOpen is set; Items.LunchOpen()). Hand props: ReplicatedStorage.NHSnacks.<Id>.

	(beasts, 2026-11-05) Trophies (Kind Trophy, Items.Trophies): a rare drop from a beast you kill (Config.Beasts Reward.Trophy,
	Services.Features.Beasts). Kept in your Locker: never sold, never pinned to the hotbar, never used. Not in Items.List,
	so the concession stand never shows them; Items.ById has them, so they save.
]]
local Items = {}
local function boardsCfg() return require(script.Parent:WaitForChild(`Boards`)) end

Items.MaxStack = 20
Items.MaxPinned = 4
Items.Cooldown = { Heal = 12; Buff = 3; Prank = 1 }
Items.UseTime = 1.1 -- seconds you're eating / drinking before it takes effect

-- Prop: the little thing in your hand (a generated part): Shape Food | Can | Bottle | Box
Items.List = {
	{ Id = `Onigiri`; Name = `Onigiri`; Rarity = `Common`; Price = 25; Kind = `Heal`; Heal = 15; Duration = 3;
		Text = `A rice ball with a salty plum inside.`; Prop = { Shape = `Food`; Color = Color3.fromRGB(240, 238, 228) } };
	{ Id = `MelonBread`; Name = `Melon Bread`; Rarity = `Common`; Price = 40; Kind = `Heal`; Heal = 30; Duration = 6;
		Text = `Crisp sugar crust, still warm.`; Prop = { Shape = `Food`; Color = Color3.fromRGB(226, 196, 120) } };
	{ Id = `YakisobaBun`; Name = `Yakisoba Bun`; Rarity = `Uncommon`; Price = 80; Kind = `Heal`; Heal = 50; Duration = 8;
		Text = `Fried noodles in a bun. Gone before the bell.`; Prop = { Shape = `Food`; Color = Color3.fromRGB(170, 104, 60) } };
	{ Id = `Bento`; Name = `Night Bento`; Rarity = `Rare`; Price = 200; Kind = `Heal`; Heal = 80; Duration = 10;
		Text = `The good box, kept back for the night crowd.`; Prop = { Shape = `Box`; Color = Color3.fromRGB(120, 28, 36) } };
	{ Id = `Ramune`; Name = `Ramune`; Rarity = `Common`; Price = 35; Kind = `Buff`; Duration = 180;
		Effects = { PostureGain = -0.006 }; Text = `Fizzy and cold. Steadies your guard.`; Prop = { Shape = `Bottle`; Color = Color3.fromRGB(120, 190, 230) } };
	{ Id = `BarleyTea`; Name = `Barley Tea`; Rarity = `Common`; Price = 45; Kind = `Buff`; Duration = 180;
		Effects = { Stealth = -0.008 }; Text = `Calm nerves, quiet feet.`; Prop = { Shape = `Can`; Color = Color3.fromRGB(150, 110, 60) } };
	{ Id = `CannedCoffee`; Name = `Canned Coffee`; Rarity = `Uncommon`; Price = 60; Kind = `Buff`; Duration = 300;
		Effects = { ClassExp = 0.03; QuestExp = 0.02 }; Text = `Black, bitter, keeps you sharp in class.`; Prop = { Shape = `Can`; Color = Color3.fromRGB(40, 32, 30) } };
	{ Id = `RedLantern`; Name = `Red Lantern`; Rarity = `Rare`; Price = 150; Kind = `Buff`; Duration = 180;
		Effects = { DamageDealt = 0.01; MaxHealth = 2 }; Text = `An energy drink the teachers pretend not to see.`; Prop = { Shape = `Can`; Color = Color3.fromRGB(190, 30, 40) } };
	{ Id = `PrankKit`; Name = `Prank Kit`; Rarity = `Uncommon`; Price = 15; Kind = `Prank`; DailyLimit = 3;
		Text = `Spray paint, a stink bomb, a roll of tape. Don't ask where it came from.`; Prop = { Shape = `Box`; Color = Color3.fromRGB(70, 150, 80) } };
	-- (batch 54) the concession kit's new snacks (2026-11-12): hot food, snacks, candy, sweets, drinks
	{ Id = `TakoyakiBoat`; Name = `Takoyaki Boat`; Rarity = `Common`; Price = 55; Kind = `Heal`; Heal = 35; Duration = 6;
		Text = `Six octopus balls, sauce, mayo and dancing bonito flakes.`; Prop = { Shape = `Box`; Color = Color3.fromRGB(150, 96, 50) } };
	{ Id = `Nikuman`; Name = `Nikuman`; Rarity = `Common`; Price = 35; Kind = `Heal`; Heal = 22; Duration = 4;
		Text = `A steamed pork bun, too hot to hold.`; Prop = { Shape = `Food`; Color = Color3.fromRGB(236, 232, 220) } };
	{ Id = `CurryBread`; Name = `Curry Bread`; Rarity = `Common`; Price = 50; Kind = `Heal`; Heal = 32; Duration = 5;
		Text = `Fried, crunchy, and full of curry.`; Prop = { Shape = `Food`; Color = Color3.fromRGB(180, 116, 40) } };
	{ Id = `CupRamen`; Name = `Cup Ramen`; Rarity = `Uncommon`; Price = 90; Kind = `Heal`; Heal = 55; Duration = 9;
		Text = `Midnight Ramen. Three minutes, if you can wait that long.`; Prop = { Shape = `Can`; Color = Color3.fromRGB(236, 228, 210) } };
	{ Id = `RoastSweetPotato`; Name = `Roast Sweet Potato`; Rarity = `Common`; Price = 45; Kind = `Heal`; Heal = 28; Duration = 5;
		Text = `Yaki-imo in a paper bag. Warms your hands on the way back.`; Prop = { Shape = `Food`; Color = Color3.fromRGB(110, 30, 40) } };
	{ Id = `YakitoriSkewers`; Name = `Yakitori Skewers`; Rarity = `Common`; Price = 30; Kind = `Heal`; Heal = 18; Duration = 3;
		Text = `Two skewers of glazed chicken and spring onion.`; Prop = { Shape = `Food`; Color = Color3.fromRGB(120, 60, 24) } };
	{ Id = `PumpkinSoup`; Name = `Pumpkin Soup`; Rarity = `Uncommon`; Price = 120; Kind = `Heal`; Heal = 65; Duration = 10;
		Text = `Thick, sweet and orange as a lantern.`; Prop = { Shape = `Can`; Color = Color3.fromRGB(210, 104, 20) } };
	{ Id = `Senbei`; Name = `Senbei`; Rarity = `Common`; Price = 15; Kind = `Heal`; Heal = 8; Duration = 2;
		Text = `A soy-glazed rice cracker. Loud in the library.`; Prop = { Shape = `Food`; Color = Color3.fromRGB(128, 72, 26) } };
	{ Id = `GraveCrisps`; Name = `Grave Crisps`; Rarity = `Common`; Price = 20; Kind = `Heal`; Heal = 10; Duration = 2;
		Text = `Sea salt and vinegar, dug up fresh.`; Prop = { Shape = `Box`; Color = Color3.fromRGB(22, 20, 26) } };
	{ Id = `Popcorn`; Name = `Popcorn`; Rarity = `Common`; Price = 25; Kind = `Heal`; Heal = 14; Duration = 3;
		Text = `A striped carton, heaped over the top.`; Prop = { Shape = `Box`; Color = Color3.fromRGB(170, 24, 36) } };
	{ Id = `BatGummies`; Name = `Bat Gummies`; Rarity = `Common`; Price = 20; Kind = `Buff`; Duration = 120;
		Effects = { Stealth = -0.004 }; Text = `Blackcurrant, cherry and lime. Chew quietly.`; Prop = { Shape = `Box`; Color = Color3.fromRGB(70, 34, 104) } };
	{ Id = `CandyApple`; Name = `Candy Apple`; Rarity = `Common`; Price = 30; Kind = `Buff`; Duration = 120;
		Effects = { PostureGain = -0.004 }; Text = `A crimson glaze you can see your face in.`; Prop = { Shape = `Food`; Color = Color3.fromRGB(150, 10, 20) } };
	{ Id = `GhostMints`; Name = `Ghost Mints`; Rarity = `Common`; Price = 25; Kind = `Buff`; Duration = 120;
		Effects = { QuestExp = 0.01 }; Text = `Cold as the grave. Clears the head.`; Prop = { Shape = `Box`; Color = Color3.fromRGB(40, 70, 84) } };
	{ Id = `KonpeitoStars`; Name = `Konpeito Stars`; Rarity = `Common`; Price = 25; Kind = `Buff`; Duration = 120;
		Effects = { ClassExp = 0.01 }; Text = `Sugar stars, a handful. Good luck before a test.`; Prop = { Shape = `Box`; Color = Color3.fromRGB(232, 218, 190) } };
	{ Id = `LicoriceWhips`; Name = `Licorice Whips`; Rarity = `Common`; Price = 20; Kind = `Buff`; Duration = 120;
		Effects = { CombatExp = 0.01 }; Text = `Black licorice. Nobody's favourite, everybody's habit.`; Prop = { Shape = `Box`; Color = Color3.fromRGB(16, 14, 16) } };
	{ Id = `ChocolateBar`; Name = `Moonlight Chocolate`; Rarity = `Common`; Price = 40; Kind = `Buff`; Duration = 180;
		Effects = { MaxHealth = 1 }; Text = `Dark chocolate in gold foil.`; Prop = { Shape = `Box`; Color = Color3.fromRGB(20, 26, 60) } };
	{ Id = `Dango`; Name = `Dango`; Rarity = `Common`; Price = 30; Kind = `Heal`; Heal = 18; Duration = 3;
		Text = `Pink, white and green, on a stick.`; Prop = { Shape = `Food`; Color = Color3.fromRGB(226, 150, 160) } };
	{ Id = `Taiyaki`; Name = `Taiyaki`; Rarity = `Common`; Price = 40; Kind = `Heal`; Heal = 26; Duration = 5;
		Text = `A fish-shaped cake with sweet bean inside. Head first or tail first?`; Prop = { Shape = `Food`; Color = Color3.fromRGB(170, 100, 36) } };
	{ Id = `PuddingCup`; Name = `Custard Pudding`; Rarity = `Common`; Price = 45; Kind = `Heal`; Heal = 28; Duration = 5;
		Text = `With burnt caramel. Don't forget the spoon.`; Prop = { Shape = `Can`; Color = Color3.fromRGB(232, 178, 60) } };
	{ Id = `TombstoneCookie`; Name = `Tombstone Cookie`; Rarity = `Common`; Price = 20; Kind = `Heal`; Heal = 12; Duration = 2;
		Text = `Shortbread. R.I.P. HOMEWORK.`; Prop = { Shape = `Box`; Color = Color3.fromRGB(150, 150, 156) } };
	{ Id = `CreamPuff`; Name = `Cream Puff`; Rarity = `Common`; Price = 35; Kind = `Heal`; Heal = 20; Duration = 4;
		Text = `Choux pastry, too much cream, a dusting of sugar.`; Prop = { Shape = `Food`; Color = Color3.fromRGB(190, 130, 60) } };
	{ Id = `StrawberryMilk`; Name = `Strawberry Milk`; Rarity = `Common`; Price = 30; Kind = `Buff`; Duration = 180;
		Effects = { MaxHealth = 1 }; Text = `Nightmare High Dairy. Not for the cafeteria cat.`; Prop = { Shape = `Box`; Color = Color3.fromRGB(226, 150, 170) } };
	{ Id = `HotCocoa`; Name = `Hot Cocoa`; Rarity = `Common`; Price = 40; Kind = `Buff`; Duration = 180;
		Effects = { DamageTaken = -0.005 }; Text = `Thick, sweet, in a lidded cup.`; Prop = { Shape = `Can`; Color = Color3.fromRGB(140, 24, 32) } };
	{ Id = `MelonSoda`; Name = `Melon Soda`; Rarity = `Common`; Price = 35; Kind = `Buff`; Duration = 180;
		Effects = { QuestExp = 0.015 }; Text = `Bright green and far too sweet.`; Prop = { Shape = `Can`; Color = Color3.fromRGB(60, 160, 50) } };
	{ Id = `BlackCatCola`; Name = `Black Cat Cola`; Rarity = `Uncommon`; Price = 45; Kind = `Buff`; Duration = 180;
		Effects = { DamageDealt = 0.005 }; Text = `Crossed your path. In a glass bottle, the proper way.`; Prop = { Shape = `Bottle`; Color = Color3.fromRGB(28, 22, 26) } };
	{ Id = `GreenTea`; Name = `Green Tea`; Rarity = `Common`; Price = 40; Kind = `Buff`; Duration = 180;
		Effects = { ClassExp = 0.02 }; Text = `Willow Leaf, unsweetened. Sharpens you up for class.`; Prop = { Shape = `Bottle`; Color = Color3.fromRGB(110, 140, 60) } };
	-- (1.39) the daily specials, Monday to Friday
	{ Id = `GarlicBread`; Name = `Garlic Bread`; Rarity = `Uncommon`; Price = 30; Kind = `Buff`; Duration = 300; Special = 1; DailyLimit = 1;
		Effects = { DamageTaken = -0.02 }; Text = `Monday's special. Buttery, crisp, and absolutely loaded with garlic.`;
		Race = { Human = { Mult = 2; Note = `Humans love it: double toughness.` };
			Vampire = { Effects = { DamageDealt = -0.02 }; Note = `Vampires: -2% damage instead. You regret it.` } };
		Prop = { Shape = `Food`; Color = Color3.fromRGB(214, 170, 96) } };
	{ Id = `MeatLoaf`; Name = `Mystery Meat Loaf`; Rarity = `Uncommon`; Price = 30; Kind = `Buff`; Duration = 300; Special = 2; DailyLimit = 1;
		Effects = { CombatExp = 0.02 }; Text = `Tuesday's special. Nobody knows what's in it. Nobody asks twice.`;
		Race = { Ghoul = { Mult = 2; Note = `Ghouls know exactly what's in it: double.` } };
		Prop = { Shape = `Box`; Color = Color3.fromRGB(122, 74, 52) } };
	{ Id = `MoonCake`; Name = `Moon Cake`; Rarity = `Uncommon`; Price = 30; Kind = `Buff`; Duration = 300; Special = 3; DailyLimit = 1;
		Effects = { PostureGain = -0.01 }; Text = `Wednesday's special. Round, golden, stamped with the school crest.`;
		Race = { Werewolf = { Mult = 2; Note = `Werewolves can't resist anything shaped like the moon: double.` } };
		Prop = { Shape = `Food`; Color = Color3.fromRGB(206, 150, 70) } };
	{ Id = `HolyLemonade`; Name = `Holy Water Lemonade`; Rarity = `Uncommon`; Price = 30; Kind = `Buff`; Duration = 300; Special = 4; DailyLimit = 1;
		Effects = { MaxHealth = 2 }; Text = `Thursday's special. The chapel's recipe. It fizzes more than lemonade should.`;
		Race = { Priest = { Mult = 2; Note = `Priests: blessed twice over. Double.` };
			Vampire = { Effects = { Stealth = 0.01 }; Note = `Vampires: it fizzes. -1% stealth.` };
			Wraith = { Effects = { Stealth = 0.01 }; Note = `Wraiths: it fizzes. -1% stealth.` } };
		Prop = { Shape = `Bottle`; Color = Color3.fromRGB(236, 226, 150) } };
	{ Id = `EctoJelly`; Name = `Ectoplasm Jelly`; Rarity = `Uncommon`; Price = 30; Kind = `Buff`; Duration = 300; Special = 5; DailyLimit = 1;
		Effects = { ClassExp = 0.02 }; Text = `Friday's special. Pale green, faintly glowing, and it wobbles on its own.`;
		Race = { Wraith = { Mult = 2; Note = `Wraiths: a taste of home. Double.` };
			Human = { Effects = {}; Note = `Humans: it wobbles. You can't. No effect.` } };
		Prop = { Shape = `Box`; Color = Color3.fromRGB(150, 220, 160) } };
}

-- (beasts) trophies: Prop Shape Fang (a wedge) | Locket (a disc) | Bone (a long rod) | Food etc.
Items.Trophies = {
	{ Id = `EmberTooth`; Name = `Ember Tooth`; Rarity = `Rare`; Kind = `Trophy`; Beast = `Hellhound`;
		Text = `A hellhound's fang, still warm. It glows faintly in the dark.`; Prop = { Shape = `Fang`; Color = Color3.fromRGB(232, 128, 64) } };
	{ Id = `GraveLocket`; Name = `Grave-Dirt Locket`; Rarity = `Rare`; Kind = `Trophy`; Beast = `Grave Ghoul`;
		Text = `A tarnished locket, packed with grave dirt. Someone's portrait is still inside.`; Prop = { Shape = `Locket`; Color = Color3.fromRGB(150, 140, 120) } };
	{ Id = `StalkerBone`; Name = `Stalker's Finger-Bone`; Rarity = `Rare`; Kind = `Trophy`; Beast = `Night Stalker`;
		Text = `Far too long to be human. It's cold, and it never warms in your hand.`; Prop = { Shape = `Bone`; Color = Color3.fromRGB(214, 208, 190) } };
	{ Id = `SpiderFang`; Name = `Bone Spider's Fang`; Rarity = `Rare`; Kind = `Trophy`; Beast = `Bone Spider`;
		Text = `A hooked fang of polished bone, a thread of old silk still wound around its root.`; Prop = { Shape = `Fang`; Color = Color3.fromRGB(226, 220, 204) } };
	{ Id = `BatClaw`; Name = `Crypt Bat's Wing-Claw`; Rarity = `Rare`; Kind = `Trophy`; Beast = `Crypt Bat`;
		Text = `The hooked thumb-claw from a crypt bat's wing, black and needle sharp. It smells of old stone.`; Prop = { Shape = `Fang`; Color = Color3.fromRGB(58, 46, 52) } };
}

Items.ById = {}
for I, It in Items.List do
	It.Order = I
	Items.ById[It.Id] = It
end
-- (kit 1.79) buffs the everyday kit gives (Services.Features.Kit): never sold or carried, only in ById so the buff resolves
Items.KitBuffs = {
	{ Id = `FlaskCoffee`; Name = `Flask Coffee`; Rarity = `Common`; Kind = `Buff`; Duration = 180; Hidden = true;
		Effects = { ClassExp = 0.02 }; Text = `From your thermos. Strong.`; Prop = { Shape = `Can`; Color = Color3.fromRGB(40, 32, 30) } };
}
for I, It in Items.KitBuffs do It.Order = 2000 + I Items.ById[It.Id] = It end
for I, It in Items.Trophies do
	It.Order = 1000 + I
	Items.ById[It.Id] = It
end

-- (batch 54) the lunch meals: kept off the stand until a lunch period opens (ReplicatedStorage attribute NHLunchOpen).
-- In Items.ById (they save and can be granted), not in Items.List (the stand's grid).
Items.Lunch = {
	{ Id = `KatsuCurry`; Name = `Katsu Curry`; Rarity = `Uncommon`; Price = 180; Kind = `Heal`; Heal = 100; Duration = 12; Lunch = true;
		Text = `Monday's curry, a crisp pork cutlet laid across the rice.`; Prop = { Shape = `Box`; Color = Color3.fromRGB(120, 60, 20) } };
	{ Id = `ShoyuRamen`; Name = `Shoyu Ramen`; Rarity = `Uncommon`; Price = 170; Kind = `Heal`; Heal = 95; Duration = 12; Lunch = true;
		Text = `Chashu, a soft egg, naruto and nori, in a lacquer bowl.`; Prop = { Shape = `Box`; Color = Color3.fromRGB(90, 50, 20) } };
	{ Id = `KaraageSet`; Name = `Karaage Set`; Rarity = `Uncommon`; Price = 190; Kind = `Heal`; Heal = 105; Duration = 12; Lunch = true;
		Text = `Fried chicken, cabbage, rice and miso soup.`; Prop = { Shape = `Box`; Color = Color3.fromRGB(150, 90, 30) } };
	{ Id = `MackerelSet`; Name = `Grilled Mackerel Set`; Rarity = `Uncommon`; Price = 160; Kind = `Heal`; Heal = 90; Duration = 12; Lunch = true;
		Text = `Salted mackerel, grated daikon, rice, miso and pickles.`; Prop = { Shape = `Box`; Color = Color3.fromRGB(110, 120, 130) } };
	{ Id = `Omurice`; Name = `Omurice`; Rarity = `Uncommon`; Price = 170; Kind = `Heal`; Heal = 95; Duration = 12; Lunch = true;
		Text = `A golden omelette over fried rice, with demi-glace.`; Prop = { Shape = `Box`; Color = Color3.fromRGB(240, 190, 60) } };
	{ Id = `WitchingStew`; Name = `Witching Hour Stew`; Rarity = `Rare`; Price = 200; Kind = `Heal`; Heal = 115; Duration = 14; Lunch = true;
		Text = `Beef stew in a hollowed loaf. Eat the bowl.`; Prop = { Shape = `Box`; Color = Color3.fromRGB(120, 70, 30) } };
	{ Id = `ShepherdsPie`; Name = `Graveyard Shepherd's Pie`; Rarity = `Rare`; Price = 200; Kind = `Heal`; Heal = 115; Duration = 14; Lunch = true;
		Text = `Mince under piped mash, with shortbread headstones.`; Prop = { Shape = `Box`; Color = Color3.fromRGB(150, 22, 34) } };
	{ Id = `PumpkinGratin`; Name = `Pumpkin Gratin`; Rarity = `Rare`; Price = 180; Kind = `Heal`; Heal = 105; Duration = 12; Lunch = true;
		Text = `Baked in its own little pumpkin, cheese bubbling on top.`; Prop = { Shape = `Box`; Color = Color3.fromRGB(210, 90, 20) } };
	{ Id = `RavensRoast`; Name = `Raven's Roast`; Rarity = `Rare`; Price = 220; Kind = `Heal`; Heal = 125; Duration = 14; Lunch = true;
		Text = `A roast chicken leg, potatoes, glazed carrots and gravy.`; Prop = { Shape = `Box`; Color = Color3.fromRGB(140, 72, 24) } };
	{ Id = `FruitCup`; Name = `Fruit Cup`; Rarity = `Common`; Price = 40; Kind = `Heal`; Heal = 22; Duration = 4; Lunch = true;
		Text = `Peach, pineapple and grapes in syrup, a cherry on top.`; Prop = { Shape = `Can`; Color = Color3.fromRGB(240, 170, 70) } };
	{ Id = `SideSalad`; Name = `Side Salad`; Rarity = `Common`; Price = 35; Kind = `Heal`; Heal = 18; Duration = 3; Lunch = true;
		Text = `Lettuce, tomato and cucumber. Your mother would be proud.`; Prop = { Shape = `Food`; Color = Color3.fromRGB(110, 170, 60) } };
	{ Id = `RiceBowl`; Name = `Rice Bowl`; Rarity = `Common`; Price = 30; Kind = `Heal`; Heal = 20; Duration = 3; Lunch = true;
		Text = `Rice, sesame and one sour plum.`; Prop = { Shape = `Food`; Color = Color3.fromRGB(240, 238, 228) } };
	{ Id = `MisoSoup`; Name = `Miso Soup`; Rarity = `Common`; Price = 30; Kind = `Heal`; Heal = 15; Duration = 3; Lunch = true;
		Text = `Tofu and wakame, in the stand's paper cup.`; Prop = { Shape = `Can`; Color = Color3.fromRGB(180, 130, 70) } };
	{ Id = `ChocolateMilk`; Name = `Chocolate Milk`; Rarity = `Common`; Price = 35; Kind = `Buff`; Duration = 180; Lunch = true;
		Effects = { MaxHealth = 1 }; Text = `Nightmare High Dairy, the chocolate one.`; Prop = { Shape = `Box`; Color = Color3.fromRGB(110, 60, 30) } };
}
for I, It in Items.Lunch do It.Order = 3000 + I Items.ById[It.Id] = It end

-- (inventory QOL batch 5) the taste book: every food and drink you can eat (prank kits, trophies and the kit's
-- hidden buffs don't count). Each milestone gives a title and +1 max health for good (Inventory.TasteEffects).
function Items.Tasteable(): { any }
	local Out = {}
	for _, It in Items.List do if It.Kind == `Heal` or It.Kind == `Buff` then table.insert(Out, It) end end
	for _, It in Items.Lunch or {} do if It.Kind == `Heal` or It.Kind == `Buff` then table.insert(Out, It) end end
	return Out
end
Items.TasteMilestones = { { At = 10; Title = `Snacker` }; { At = 25; Title = `Refectory Regular` }; { At = `All`; Title = `Iron Stomach` } }

-- (inventory QOL batch 5) the foods each clique loves: feeding one to a member is worth standing (Inventory.Feed)
Items.CliqueFood = {
	Athletes = { `YakisobaBun`, `TakoyakiBoat`, `Bento`, `CurryBread`, `KaraageSet` };
	Choir = { `MoonCake`, `GreenTea`, `Dango`, `HolyLemonade`, `FruitCup` };
	Pack = { `Nikuman`, `YakitoriSkewers`, `MeatLoaf`, `KaraageSet`, `RavensRoast` };
	Vigil = { `CannedCoffee`, `BarleyTea`, `Senbei`, `KonpeitoStars`, `MisoSoup` };
	Court = { `CreamPuff`, `PuddingCup`, `StrawberryMilk`, `RedLantern`, `Omurice` };
	Delinquents = { `BlackCatCola`, `GraveCrisps`, `CupRamen`, `LicoriceWhips`, `ShoyuRamen` };
	Ordinary = { `Onigiri`, `MelonBread`, `MisoSoup`, `Popcorn`, `RiceBowl` };
	Ink = { `Taiyaki`, `BatGummies`, `MelonSoda`, `GhostMints`, `ChocolateBar` };
}

-- (batch 54) a lunch period opens the lunch meals (ReplicatedStorage attribute NHLunchOpen = true)
-- (inventory QOL 1.92) the lunch period comes from the school timetable (the Lunch segment, 11:25 to 12:00 on school
-- days); ReplicatedStorage's NHLunchOpen = true still forces it open. LunchInfo returns whether it's open and the real
-- seconds until it opens (shut) or closes (open), or nil when there's no lunch in the next few days.
local LunchCache = { At = -1e9 }
function Items.LunchInfo(): (boolean, number?)
	local RS = game:GetService(`ReplicatedStorage`)
	local Forced = RS:GetAttribute(`NHLunchOpen`) == true
	local Clock = RS:FindFirstChild(`SchoolClock`)
	local Epoch = Clock and Clock:GetAttribute(`Epoch`)
	if not Epoch then return Forced, nil end
	local Now = workspace:GetServerTimeNow()
	if Now - LunchCache.At < 1 and LunchCache.Epoch == Epoch then
		local Left = LunchCache.Secs and (LunchCache.Secs - (Now - LunchCache.At)) or nil
		return Forced or LunchCache.Open, Left
	end
	local ST = require(RS.Functions.SchoolTime)
	local S = ST.GetState(Epoch, Now)
	-- game minutes per real second, measured over the next ten real minutes
	local Ahead = ST.GetState(Epoch, Now + 600)
	local Rate = ((Ahead.Day - S.Day) * 1440 + Ahead.MinuteOfDay - S.MinuteOfDay) / 600
	local Open, Secs = false, nil
	if Rate > 0 then
		if S.Segment and S.Segment.Kind == `Lunch` then
			Open, Secs = true, (S.Segment.End - S.MinuteOfDay) / Rate
		else
			for D = 0, 3 do
				local Found = false
				for M = (if D == 0 then math.floor(S.MinuteOfDay) + 1 else 0), 1439, 5 do
					local At = ST.GetState(ST.EpochFor(Now, S.Day + D, M), Now)
					if At.Segment and At.Segment.Kind == `Lunch` then
						Secs = (D * 1440 + At.Segment.Start - S.MinuteOfDay) / Rate
						Found = true
						break
					end
				end
				if Found then break end
			end
		end
	end
	LunchCache = { At = Now; Epoch = Epoch; Open = Open; Secs = Secs }
	return Forced or Open, Secs
end

function Items.LunchOpen(): boolean
	return (Items.LunchInfo())
end

-- (inventory QOL 1.92) the stand's tabs. Category says which tab an item sits under; anything not listed goes by kind
-- (food under Hot food, buffs under Drinks), and the lunch meals under Lunch.
Items.StandTabs = { `All`, `Hot food`, `Snacks`, `Sweets`, `Drinks`, `Lunch` }
Items.Category = {
	Onigiri = `Hot food`; YakisobaBun = `Hot food`; Bento = `Hot food`; TakoyakiBoat = `Hot food`;
	Nikuman = `Hot food`; CurryBread = `Hot food`; CupRamen = `Hot food`; RoastSweetPotato = `Hot food`;
	YakitoriSkewers = `Hot food`; PumpkinSoup = `Hot food`; GarlicBread = `Hot food`; MeatLoaf = `Hot food`;
	MelonBread = `Snacks`; Senbei = `Snacks`; GraveCrisps = `Snacks`; Popcorn = `Snacks`; PrankKit = `Snacks`;
	BatGummies = `Sweets`; CandyApple = `Sweets`; GhostMints = `Sweets`; KonpeitoStars = `Sweets`; LicoriceWhips = `Sweets`;
	ChocolateBar = `Sweets`; Dango = `Sweets`; Taiyaki = `Sweets`; PuddingCup = `Sweets`; TombstoneCookie = `Sweets`;
	CreamPuff = `Sweets`; MoonCake = `Sweets`; EctoJelly = `Sweets`;
	Ramune = `Drinks`; BarleyTea = `Drinks`; CannedCoffee = `Drinks`; RedLantern = `Drinks`; StrawberryMilk = `Drinks`;
	HotCocoa = `Drinks`; MelonSoda = `Drinks`; BlackCatCola = `Drinks`; GreenTea = `Drinks`; HolyLemonade = `Drinks`;
}
function Items.CategoryOf(It): string
	if It.Lunch then return `Lunch` end
	return Items.Category[It.Id] or (if It.Kind == `Heal` then `Hot food` elseif It.Kind == `Prank` then `Snacks` else `Drinks`)
end

-- (1.39) the daily special --------------------------------------------------------------------------
Items.Specials = {}
for _, It in Items.List do if It.Special then Items.Specials[It.Special] = It end end

-- the special for an event day (school days run Monday..Friday, the clock's DayNames)
function Items.SpecialFor(EventDay: number)
	return Items.Specials[EventDay % 5 + 1]
end

-- today's event day (6 AM rollover, like Config.Cliques.EventDay), from the SchoolClock's Epoch
function Items.EventDay(): number?
	local Clock = game:GetService(`ReplicatedStorage`):FindFirstChild(`SchoolClock`)
	local Epoch = Clock and Clock:GetAttribute(`Epoch`)
	if not Epoch then return nil end
	local ST = require(game:GetService(`ReplicatedStorage`).Functions.SchoolTime)
	local S = ST.GetState(Epoch, workspace:GetServerTimeNow())
	return if S.Hour >= 6 then S.Day else S.Day - 1
end

function Items.TodaySpecial()
	local D = Items.EventDay()
	return D and Items.SpecialFor(D) or nil
end

-- regular items are always on sale; a special only on its day
function Items.OnSale(It): boolean
	if It.Lunch then return Items.LunchOpen() end -- (batch 54)
	if not It.Special then return true end
	local T = Items.TodaySpecial()
	return T ~= nil and T.Id == It.Id
end

-- the buff an item gives this race (a special's twist), and the twist's note (nil if none)
function Items.EffectsFor(It, Race: string?): { [string]: number }
	local Tw = It.Race and Race and It.Race[Race]
	local Out = {}
	if Tw and Tw.Effects then
		for K, V in Tw.Effects do Out[K] = V end
	else
		local M = (Tw and Tw.Mult) or 1
		for K, V in It.Effects or {} do Out[K] = V * M end
	end
	return Out
end
function Items.RaceNote(It, Race: string?): string?
	local Tw = It.Race and Race and It.Race[Race]
	return Tw and Tw.Note or nil
end

-- "+30 health over 6 s" / "+0.6% guard for 3 min" style line for UI
local LABELS = { DamageDealt = `damage`; DamageTaken = `toughness`; MaxHealth = `max health`; PostureGain = `guard`;
	Stealth = `stealth`; ClassExp = `class EXP`; QuestExp = `quest EXP`; CombatExp = `combat EXP`; AllExp = `all EXP` }
function Items.Describe(It): string
	if It.Kind == `Trophy` then return `A trophy from the {It.Beast or `hunt`}. Kept in your Locker.` end
	if It.Kind == `Heal` then return `+{It.Heal} health over {It.Duration} s` end
	if It.Kind == `Prank` then return `Prank another clique's hangout (hold E on a prank spot). {It.DailyLimit or 3} a day.` end
	local Parts = {}
	for K, V in It.Effects or {} do
		if K == `MaxHealth` then table.insert(Parts, `+{V} {LABELS[K]}`)
		else table.insert(Parts, `+{math.floor(math.abs(V) * 1000 + 0.5) / 10}% {LABELS[K] or K}`) end
	end
	table.sort(Parts)
	local Mins = It.Duration / 60
	return `{table.concat(Parts, `, `)} for {if Mins >= 1 then `{math.floor(Mins + 0.5)} min` else `{It.Duration} s`}`
end

-- saved form: { Items = { [id] = count }, Pinned = { id }, Boards = { Owned = { id }, Equipped = id } (Config.Boards),
--   Daily = { Day = n, [id] = bought that day } (1.33: items with a DailyLimit) }
function Items.Sanitize(Raw)
	local Out = { Items = {}; Pinned = {}; Boards = boardsCfg().Sanitize(if typeof(Raw) == `table` then Raw.Boards else nil) }
	-- (kit 1.79) the everyday kit rides in the same record (Config.Kit.Sanitize)
	Out.Kit = require(script.Parent:WaitForChild(`Kit`)).Sanitize(if typeof(Raw) == `table` then Raw.Kit else nil)
	if typeof(Raw) ~= `table` then return Out end
	if typeof(Raw.Items) == `table` then
		for Id, N in Raw.Items do
			if Items.ById[Id] and not Items.ById[Id].Hidden and typeof(N) == `number` and N == N and N >= 1 then Out.Items[Id] = math.clamp(math.floor(N), 1, Items.MaxStack) end
		end
	end
	if typeof(Raw.Pinned) == `table` then
		for _, Id in Raw.Pinned do
			if Items.ById[Id] and Items.ById[Id].Kind ~= `Trophy` and not table.find(Out.Pinned, Id) and #Out.Pinned < Items.MaxPinned then table.insert(Out.Pinned, Id) end
		end
	end
	-- (inventory QOL 1.93) favourites: up to 12 item ids (Inventory.Fav checks they're real)
	if typeof(Raw.Fav) == `table` then
		Out.Fav = {}
		for _, Id in Raw.Fav do
			if typeof(Id) == `string` and #Id <= 48 and not table.find(Out.Fav, Id) and #Out.Fav < 12 then table.insert(Out.Fav, Id) end
		end
	end
	-- (inventory QOL batch 5) the taste book ({ [id] = true }) and today's fed cliques ({ Day = n, [clique] = true })
	if typeof(Raw.Tasted) == `table` then
		Out.Tasted = {}
		for Id, V in Raw.Tasted do if V == true and Items.ById[Id] and not Items.ById[Id].Hidden then Out.Tasted[Id] = true end end
	end
	if typeof(Raw.Fed) == `table` and typeof(Raw.Fed.Day) == `number` then
		Out.Fed = { Day = math.floor(Raw.Fed.Day) }
		for K, V in Raw.Fed do if K ~= `Day` and typeof(K) == `string` and #K <= 24 and V == true then Out.Fed[K] = true end end
	end
	if typeof(Raw.Daily) == `table` and typeof(Raw.Daily.Day) == `number` then
		Out.Daily = { Day = math.floor(Raw.Daily.Day) }
		for Id, N in Raw.Daily do
			if Id ~= `Day` and Items.ById[Id] and typeof(N) == `number` and N >= 0 then Out.Daily[Id] = math.clamp(math.floor(N), 0, 99) end
		end
	end
	return Out
end

return Items
