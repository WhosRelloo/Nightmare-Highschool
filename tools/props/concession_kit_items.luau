--!nocheck
-- Props batch 54 (the concession consumables kit): patches ReplicatedStorage.Config.Items in place. Safe to run again (it
-- looks for its "(batch 54)" marker first).
--   * Items.List gets the 26 new snacks the owner approved on 2026-11-12 (hot food, snacks, candy, sweets, drinks), placed
--     before the daily specials so the stand's grid keeps its order. Heal and buff values follow the file's balance note
--     (buffs under a Common gear piece's budget).
--   * Items.Lunch: the lunch meals (Japanese sets, the house meals, the extras). Registered in Items.ById (so they save and
--     can be granted) but not in Items.List, so the stand doesn't show them, and Items.OnSale says no until a lunch period
--     sets ReplicatedStorage's NHLunchOpen attribute (Items.LunchOpen()).
--   * Every item's hand prop is ReplicatedStorage.NHSnacks.<Id>.Handle when that model exists (Services.Features.Inventory
--     and Controllers.Gui.Locker); Prop.Shape / Prop.Color stay as the fallback.
local M = game:GetService("ReplicatedStorage").Config.Items
local src = M.Source
if src:find("(batch 54)", 1, true) then return "already patched" end

local NEW = [==[
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
]==]

local LUNCH = [==[

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

-- (batch 54) a lunch period opens the lunch meals (ReplicatedStorage attribute NHLunchOpen = true)
function Items.LunchOpen(): boolean
	return game:GetService(`ReplicatedStorage`):GetAttribute(`NHLunchOpen`) == true
end
]==]

local A1 = "\t-- (1.39) the daily specials, Monday to Friday\n"
local A2 = "-- (1.39) the daily special ------"
local A3 = "function Items.OnSale(It): boolean\n\tif not It.Special then return true end"
assert(src:find(A1, 1, true), "anchor 1 (daily specials) not found")
assert(src:find(A2, 1, true), "anchor 2 (daily special section) not found")
assert(src:find(A3, 1, true), "anchor 3 (OnSale) not found")
local function put(s, anchor, text, before)
	local i, j = s:find(anchor, 1, true)
	if before then return s:sub(1, i - 1) .. text .. s:sub(i) end
	return s:sub(1, j) .. text .. s:sub(j + 1)
end
src = put(src, A1, NEW, true)
src = put(src, A2, LUNCH:sub(2) .. "\n", true)
src = put(src, A3, "", false)
src = src:gsub("function Items%.OnSale%(It%): boolean\n\tif not It%.Special then return true end",
	"function Items.OnSale(It): boolean\n\tif It.Lunch then return Items.LunchOpen() end -- (batch 54)\n\tif not It.Special then return true end", 1)
src = src:gsub("(\t%(beasts, 2026%-11%-05%) Trophies)", "\t(batch 54) The concession kit adds 26 snacks to Items.List and the lunch meals in Items.Lunch (Lunch = true,\n\tsold only while ReplicatedStorage's NHLunchOpen is set; Items.LunchOpen()). Hand props: ReplicatedStorage.NHSnacks.<Id>.\n\n%1", 1)
-- compile check before writing it back
local ok, err = loadstring(src)
assert(ok, "patched source doesn't compile: " .. tostring(err))
M.Source = src
return "patched, " .. #src .. " bytes"
