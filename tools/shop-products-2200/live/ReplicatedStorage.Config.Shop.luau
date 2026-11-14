--[[
	Spin Shop (Robux). Server: Services.Player.Purchases (the only MarketplaceService.ProcessReceipt).
	Every product is a Developer Product. Create them on the Creator Dashboard
	(your experience > Monetization > Developer Products), then paste each id into ProductId below.
	A product with ProductId = 0 shows as "Not on sale yet". Price is only a hint for the button: the real price is read
	from Roblox once the id is set (managed pricing can change it by region, and Roblox Plus members see 20% off).
	(2026-11-14) The owner created the 14 spin products on NH Combat Test's experience (universe 10773746169); Price holds
	their dashboard base prices. Developer products belong to one experience: the live game needs its own copies.

	Spins go to the student (save slot) you are playing when you buy.
	Kinds: Spin = "Clan" | "Height" | "Race" | "Variant" | "Trait" (adds spins), Kind = "NameChange", Kind = "Cape" (owned for good,
	worn from the Wardrobe; models in ReplicatedStorage.NHCapes), or Kind = "Bundle" (Grants = a list of { Spin; Amount }).
	Icon = a key of Shop.Icons: the product's icon image (art/group-upload-shop, docs/Monetization-Concepts.md).
]]

local Shop = {}

Shop.Groups = {
	{ Id = `Clan`;       Name = `Clan Spins`;    Text = `Roll a new family name. Epic or better is guaranteed after 40 spins in a row without one.` };
	{ Id = `Height`;     Name = `Height Spins`;  Text = `Roll a new height within your race's range. Epic or better is guaranteed after 30 spins in a row without one.` };
	{ Id = `Race`;       Name = `Race Spins`;    Text = `Roll a new race and variant.` };
	{ Id = `Variant`;    Name = `Variant Spins`; Text = `Keep your race, roll its variant.` };
	{ Id = `Trait`;      Name = `Trait Spins`;   Text = `Reroll one trait slot.` };
	{ Id = `Bundles`;    Name = `Bundles`;       Text = `Bloodline: 3 race, 3 variant and 5 trait spins. Identity: 5 clan and 3 height spins. Each spin has its own kind's odds.` };
	{ Id = `NameChange`; Name = `Name Change`;   Text = `Change your first name after you have enrolled.` };
	{ Id = `Capes`;      Name = `Capes`;         Text = `Rigged capes that sway as you move. Owned for good by this student; wear one from the Wardrobe (Outfit).` };
}

Shop.Products = {
	{ Key = `Clan1`;      Group = `Clan`;       Spin = `Clan`;    Amount = 1;  Price = 10; ProductId = 3731113386; Icon = `ClanSpins1` };
	{ Key = `Clan5`;      Group = `Clan`;       Spin = `Clan`;    Amount = 5;  Price = 39; ProductId = 3731113943; Icon = `ClanSpins5`; Badge = `Popular` };
	{ Key = `Clan15`;     Group = `Clan`;       Spin = `Clan`;    Amount = 15; Price = 89; ProductId = 3731113998; Icon = `ClanSpins15`; Badge = `Best value` };
	{ Key = `Height3`;    Group = `Height`;     Spin = `Height`;  Amount = 3;  Price = 19; ProductId = 3731114273; Icon = `HeightSpins3` };
	{ Key = `Height10`;   Group = `Height`;     Spin = `Height`;  Amount = 10; Price = 49; ProductId = 3731114370; Icon = `HeightSpins10`; Badge = `Best value` };
	{ Key = `Race3`;      Group = `Race`;       Spin = `Race`;    Amount = 3;  Price = 25; ProductId = 3731114428; Icon = `RaceSpins3` };
	{ Key = `Race10`;     Group = `Race`;       Spin = `Race`;    Amount = 10; Price = 69; ProductId = 3731114490; Icon = `RaceSpins10`; Badge = `Best value` };
	{ Key = `Variant3`;   Group = `Variant`;    Spin = `Variant`; Amount = 3;  Price = 19; ProductId = 3731114557; Icon = `VariantSpins3` };
	{ Key = `Variant10`;  Group = `Variant`;    Spin = `Variant`; Amount = 10; Price = 49; ProductId = 3731114611; Icon = `VariantSpins10`; Badge = `Best value` };
	{ Key = `Trait5`;     Group = `Trait`;      Spin = `Trait`;   Amount = 5;  Price = 29; ProductId = 3731114678; Icon = `TraitSpins5` };
	{ Key = `Trait15`;    Group = `Trait`;      Spin = `Trait`;   Amount = 15; Price = 69; ProductId = 3731114736; Icon = `TraitSpins15`; Badge = `Best value` };
	{ Key = `BloodlineBundle`; Group = `Bundles`; Kind = `Bundle`; Label = `Bloodline`; Amount = 1; Price = 79; ProductId = 3731117742; Icon = `BloodlineBundle`;
		Grants = { { Spin = `Race`; Amount = 3 }; { Spin = `Variant`; Amount = 3 }; { Spin = `Trait`; Amount = 5 } } };
	{ Key = `IdentityBundle`;  Group = `Bundles`; Kind = `Bundle`; Label = `Identity`;  Amount = 1; Price = 59; ProductId = 3731117907; Icon = `IdentityBundle`;
		Grants = { { Spin = `Clan`; Amount = 5 }; { Spin = `Height`; Amount = 3 } } };
	{ Key = `NameChange`; Group = `NameChange`; Kind = `NameChange`; Amount = 1; Price = 15; ProductId = 3731119590; Icon = `NameChange` };
	{ Key = `CapeVamp`;   Group = `Capes`;      Kind = `Cape`; Cape = `Vamp Cape`;  Amount = 1; Price = 49; ProductId = 0; Icon = `CapeVamp` };
	{ Key = `CapeRogue`;  Group = `Capes`;      Kind = `Cape`; Cape = `Rogue Cape`; Amount = 1; Price = 49; ProductId = 0; Icon = `CapeRogue` };
	{ Key = `CapeFur`;    Group = `Capes`;      Kind = `Cape`; Cape = `Fur Cape`;   Amount = 1; Price = 69; ProductId = 0; Icon = `CapeFur`; Badge = `New` };
}

Shop.Icons = { -- (2026-11-13) image ids of the shop icons (art/group-upload-shop/NHShop<Name>.png); 0 = not uploaded yet
	ClanSpins1 = 81997389624394;
	ClanSpins5 = 112833070370582;
	ClanSpins15 = 83524850768587;
	HeightSpins3 = 107203858871293;
	HeightSpins10 = 128999897064375;
	RaceSpins3 = 138177087914276;
	RaceSpins10 = 133721535617654;
	VariantSpins3 = 100277619338525;
	VariantSpins10 = 80887610145448;
	TraitSpins5 = 105620614161477;
	TraitSpins15 = 105370084312499;
	BloodlineBundle = 85562458363237;
	IdentityBundle = 129740475010091;
	NameChange = 136880589370002;
	CapeVamp = 99243484013451;
	CapeRogue = 94617129303894;
	CapeFur = 79155264888400;
	CloakRavenfeather = 82341804116508;
	CloakMoonlit = 127463890730141;
	CloakAshen = 108307744691376;
	OutfitMidnightPrefect = 92295091595921;
	OutfitCrimsonGala = 82733659165733;
	OutfitGraveyardFormal = 87602506357322;
	EyeGlowTint = 127773769827829;
	DeckHellfire = 106573346339629;
	DeckMoonwake = 72455282372755;
	DeckBoneRail = 92635186663680;
	LunchboxCoffin = 99495207499824;
	LunchboxBatTin = 90398482929423;
	LunchboxCrimsonBento = 121675171117041;
	LanternCrimsonGlass = 101527759702075;
	UmbrellaBatWing = 135777850866728;
	ThermosRaven = 138610314496985;
	PhoneWallpapers = 85088899996593;
	PhoneCase = 129109819586690;
	PhoneRingtones = 81230938975821;
	DecorGothicStudy = 95324863095608;
	DecorMoonlitLoft = 117142920511540;
	DecorCrimsonCourt = 94871785001958;
	GearTint = 131086890927352;
	MomentLanternRelease = 82834305252245;
	MomentCrimsonFireworks = 92598015496554;
	MomentShoutout = 97246518195180;
	PassExtraStudents = 125536192896921;
	PassTailor = 138343778374809;
	PassCollectorsDorm = 109263291575654;
	PassGothicEmotes = 117199176910711;
	PassGramophone = 135666657549207;
	PassPrefectsSeal = 93437096118641;
	NightSociety = 135469725267771;
}

Shop.ByKey = {}
Shop.ById = {}
for _, P in Shop.Products do
	Shop.ByKey[P.Key] = P
	if P.ProductId and P.ProductId ~= 0 then Shop.ById[P.ProductId] = P end
end

return Shop
