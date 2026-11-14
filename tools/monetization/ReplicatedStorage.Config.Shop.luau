--[[
	Spin Shop (Robux). Server: Services.Player.Purchases (the only MarketplaceService.ProcessReceipt).
	Every product is a Developer Product. Create them on the Creator Dashboard
	(your experience > Monetization > Developer Products), then paste each id into ProductId below.
	A product with ProductId = 0 shows as "Not on sale yet". Price is only a hint for the button (2026-11-13: the owner's cheap prices, docs/Monetization-Concepts.md);
	the real price is read from Roblox once the id is set.

	Spins go to the student (save slot) you are playing when you buy.
	Kinds: Spin = "Clan" | "Height" | "Race" | "Variant" | "Trait" (adds spins), Kind = "NameChange", or Kind = "Cape" (owned for good,
	worn from the Wardrobe; models in ReplicatedStorage.NHCapes).
]]

local Shop = {}

Shop.Groups = {
	{ Id = `Clan`;       Name = `Clan Spins`;    Text = `Roll a new family name. Epic or better is guaranteed after 40 spins in a row without one.` };
	{ Id = `Height`;     Name = `Height Spins`;  Text = `Roll a new height within your race's range. Epic or better is guaranteed after 30 spins in a row without one.` };
	{ Id = `Race`;       Name = `Race Spins`;    Text = `Roll a new race and variant.` };
	{ Id = `Variant`;    Name = `Variant Spins`; Text = `Keep your race, roll its variant.` };
	{ Id = `Trait`;      Name = `Trait Spins`;   Text = `Reroll one trait slot.` };
	{ Id = `NameChange`; Name = `Name Change`;   Text = `Change your first name after you have enrolled.` };
	{ Id = `Capes`;      Name = `Capes`;         Text = `Rigged capes that sway as you move. Owned for good by this student; wear one from the Wardrobe (Outfit).` };
}

Shop.Products = {
	{ Key = `Clan1`;      Group = `Clan`;       Spin = `Clan`;    Amount = 1;  Price = 5;  ProductId = 0 };
	{ Key = `Clan5`;      Group = `Clan`;       Spin = `Clan`;    Amount = 5;  Price = 19; ProductId = 0; Badge = `Popular` };
	{ Key = `Clan15`;     Group = `Clan`;       Spin = `Clan`;    Amount = 15; Price = 49; ProductId = 0; Badge = `Best value` };
	{ Key = `Height3`;    Group = `Height`;     Spin = `Height`;  Amount = 3;  Price = 9;  ProductId = 0 };
	{ Key = `Height10`;   Group = `Height`;     Spin = `Height`;  Amount = 10; Price = 25; ProductId = 0; Badge = `Best value` };
	{ Key = `Race3`;     Group = `Race`;       Spin = `Race`;    Amount = 3;  Price = 15; ProductId = 0 };
	{ Key = `Race10`;     Group = `Race`;       Spin = `Race`;    Amount = 10; Price = 39; ProductId = 0; Badge = `Best value` };
	{ Key = `Variant3`;   Group = `Variant`;    Spin = `Variant`; Amount = 3;  Price = 9;  ProductId = 0 };
	{ Key = `Trait5`;     Group = `Trait`;      Spin = `Trait`;   Amount = 5;  Price = 9;  ProductId = 0 };
	{ Key = `NameChange`; Group = `NameChange`; Kind = `NameChange`; Amount = 1; Price = 25; ProductId = 0 };
	{ Key = `CapeVamp`;   Group = `Capes`;      Kind = `Cape`; Cape = `Vamp Cape`;  Amount = 1; Price = 49; ProductId = 0 };
	{ Key = `CapeRogue`;  Group = `Capes`;      Kind = `Cape`; Cape = `Rogue Cape`; Amount = 1; Price = 49; ProductId = 0 };
	{ Key = `CapeFur`;    Group = `Capes`;      Kind = `Cape`; Cape = `Fur Cape`;   Amount = 1; Price = 69; ProductId = 0; Badge = `New` };
}

Shop.ByKey = {}
Shop.ById = {}
for _, P in Shop.Products do
	Shop.ByKey[P.Key] = P
	if P.ProductId and P.ProductId ~= 0 then Shop.ById[P.ProductId] = P end
end

return Shop
