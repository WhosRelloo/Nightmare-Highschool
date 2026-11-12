--!nonstrict
--[[
	NH Appearance - the student the player makes (Wardrobe, K). COSMETIC ONLY.

	Data (all optional, Sanitize fills defaults):
	  LookStyle  Scholar | Chapel (gold cross pin) | Nightborn (pale skin, crimson eyes)
	  Skin, HairColor, EyeColor   preset index;  SkinHex / HairHex / EyeHex "RRGGBB" override it ("" = preset)
	  Hair       built hairstyle index (last = None);  HairId = catalog hair accessory id (0 = none)
	  TintHair   true = recolour the catalog hair with the hair colour
	  Eyes       1 = keep the Roblox face, 2+ = NH painted eye shape (UI.EyeArt);  EyeSet 1 = Male, 2 = Female
	  Brows      1 = none, 2+ = brow style (fitted to the eye shape);  BrowHex "" = match the hair colour
	  Mouth      1 = none, 2+ = mouth style;  Lips = fuller tinted lips
	  (brows and mouth are separate decals and only show with painted eyes)
	  Uniform (top), Bottoms (1 = uniform trousers), UseAvatar, Created
	  UseAvatar = true (default): your Roblox outfit stays; eyes, look marks and catalog hair still apply.
	  UseAvatar = false: your outfit is stashed (not deleted) and you wear the official Nightmare High
	                     uniform (group Shirt + Pants), with skin BodyColors and your hair.
	  This is NOT race: race is rolled by ReplicatedStorage.Lineage. Nothing here writes Race.

	Transformations: when gameplay sets the character attribute Transformation to Vampire / Wolf /
	Ghoul / Wraith, the painted eyes switch to that form's art (and back when it is cleared).
	TransformationStage = 2 gives Vampire and Ghoul their second form: jet-black sclera.
	This module only reads that attribute.

	Server  Appearance.StartServer()   (ServerScriptService.NHAppearance runs it)
	  Saved in ProfileService data (PlayerData.Appearance) via Data.UpdateState({ type = "SetAppearance" }).
	  ReplicatedStorage.NHAppearance.Set (RemoteEvent) and .CheckHair (RemoteFunction id -> ok, name|reason).
	Client  Appearance.Fetch() -> data, isNew      Appearance.Send(data)     Appearance.CheckHair(id)
]]

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local rgb = Color3.fromRGB
local EyeArt = require(script.Parent:WaitForChild("EyeArt"))

local Appearance = {}
Appearance.RemotesName = "NHAppearance"
Appearance.EyeArt = EyeArt

-- Cosmetic look styles (not race).
Appearance.Looks = {
	{ Id = "Scholar", Label = "Scholar", Icon = "IconNib", Text = "Plain and tidy. Nothing to see here." },
	{ Id = "Chapel", Label = "Chapel", Icon = "IconCross", Text = "A gold cross pinned to the blazer." },
	{ Id = "Nightborn", Label = "Nightborn", Icon = "IconDrop", Text = "Pale skin and crimson eyes." },
}
Appearance.Skins = {
	rgb(236, 206, 178), rgb(216, 180, 146), rgb(180, 132, 98),
	rgb(132, 92, 62), rgb(94, 64, 46), rgb(246, 228, 216),
}
Appearance.HairColors = {
	{ Id = "black", Name = "Black", Color = rgb(24, 20, 24) },
	{ Id = "raven", Name = "Raven", Color = rgb(36, 40, 64) },
	{ Id = "chestnut", Name = "Chestnut", Color = rgb(98, 60, 36) },
	{ Id = "ash-blonde", Name = "Ash Blonde", Color = rgb(196, 176, 130) },
	{ Id = "silver", Name = "Silver", Color = rgb(192, 192, 202) },
	{ Id = "blood-red", Name = "Blood Red", Color = rgb(132, 24, 36) },
}
Appearance.HairStyles = { "Neat Crop", "Fringe", "Long", "Bun", "None" }
-- Official uniform clothing (Nightmare Highschool group). Shirt/Pants are the texture ids that
-- InsertService:LoadAsset(Catalog) returns; Catalog is the shop item id.
Appearance.Pants = { Name = "Uniform Pants", Template = "rbxassetid://11092315741", Catalog = 11092315756 }
Appearance.Uniforms = {
	{ Id = "red-vest", Name = "Red Vest", Shirt = "rbxassetid://11092306245", Catalog = 11092306255 },
	{ Id = "red-shirt", Name = "Red Shirt", Shirt = "rbxassetid://11092301473", Catalog = 11092301482 },
	{ Id = "black-vest", Name = "Black Vest", Shirt = "rbxassetid://11092309131", Catalog = 11092309137 },
	{ Id = "black-shirt", Name = "Black Shirt", Shirt = "rbxassetid://11092303922", Catalog = 11092303926 },
	-- variants made from the uniform templates (clothing session; image ids)
	{ Id = "navy-vest", Name = "Navy Vest", Shirt = "rbxassetid://126033480692745" },
	{ Id = "forest-vest", Name = "Forest Vest", Shirt = "rbxassetid://134507908775962" },
	{ Id = "charcoal-vest", Name = "Charcoal Vest", Shirt = "rbxassetid://90592600352473" },
	{ Id = "vigil-vest", Name = "Vigil Vest", Shirt = "rbxassetid://136662504832591" },
	{ Id = "crimson-court-vest", Name = "Crimson Court Vest", Shirt = "rbxassetid://96445202871241" },
	{ Id = "navy-polo", Name = "Navy Polo", Shirt = "rbxassetid://107114650770030" },
	{ Id = "forest-polo", Name = "Forest Polo", Shirt = "rbxassetid://134361944222018" },
	{ Id = "ivory-polo", Name = "Ivory Polo", Shirt = "rbxassetid://105124419047920" },
	{ Id = "crimson-polo", Name = "Crimson Polo", Shirt = "rbxassetid://88220726097116" },
	{ Id = "delinquent-polo", Name = "Delinquent Polo", Shirt = "rbxassetid://108805155717873" },
	{ Id = "black-blazer", Name = "Black Blazer", Shirt = "rbxassetid://114503423083394" },
	{ Id = "charcoal-cardigan", Name = "Charcoal Cardigan", Shirt = "rbxassetid://74775509137658" },
	{ Id = "varsity-jacket", Name = "Varsity Jacket", Shirt = "rbxassetid://130358206613936" },
	{ Id = "gym-pe-shirt", Name = "Gym / PE Shirt", Shirt = "rbxassetid://81495425196079" },
	-- civilian (clothing session)
	{ Id = "blood-moon-hoodie", Name = "Blood Moon Hoodie", Shirt = "rbxassetid://117967871612083" },
	{ Id = "leather-jacket", Name = "Leather Jacket", Shirt = "rbxassetid://131118808030664" },
	{ Id = "open-flannel", Name = "Open Flannel", Shirt = "rbxassetid://135280609408620" },
	{ Id = "victorian-waistcoat", Name = "Victorian Waistcoat", Shirt = "rbxassetid://92860287023765" },
	{ Id = "hussar-coat", Name = "Hussar Coat", Shirt = "rbxassetid://131384159019053" },
	{ Id = "the-hollow-band-tee", Name = "\"The Hollow\" Band Tee", Shirt = "rbxassetid://81586058028887" },
	-- female outfits (2026-11-03, Clothing/tools/female.py; drawn for the Female body). School wear first, then civilian.
	{ Id = "sailor-uniform", Name = "Sailor Uniform", Shirt = "rbxassetid://82560658973588", Female = true },
	{ Id = "chapel-corset", Name = "Chapel Blouse & Corset", Shirt = "rbxassetid://113065665742505", Female = true },
	{ Id = "bolero-pinafore", Name = "Crimson Bolero & Pinafore", Shirt = "rbxassetid://116103505706898", Female = true },
	{ Id = "cheer-uniform", Name = "NH Cheer Uniform", Shirt = "rbxassetid://74342213311812", Female = true },
	{ Id = "lolita-dress", Name = "Gothic Lolita Dress", Shirt = "rbxassetid://135700738872216", Female = true },
	{ Id = "cable-knit", Name = "Oversized Cable Knit", Shirt = "rbxassetid://118771757807189", Female = true },
	{ Id = "gala-gown", Name = "Midnight Gala Gown", Shirt = "rbxassetid://95458576559201", Female = true },
	-- (1.71) gender kits (art/clothing/tools/kit_school_f.py, kit_civilian.py, kit_admin2.py; group 15981569 images).
	-- Schoolgirl kit (school tops: owned through enrolment, the School Store or a clique reward), civilian per gender,
	-- and the admin kit (Admin = true: staff only, Appearance.ClothingAllows).
	{ Id = "crest-blazer", Name = "Crest Blazer & Ribbon", Shirt = "rbxassetid://105376183533118", Gender = "Female" },
	{ Id = "navy-vest-f", Name = "Navy Sweater Vest", Shirt = "rbxassetid://109010216363354", Gender = "Female" },
	{ Id = "cropped-cardigan", Name = "Cropped Cardigan & Bow", Shirt = "rbxassetid://86481957958704", Gender = "Female" },
	{ Id = "vigil-vest-f", Name = "Vigil Sweater Vest", Shirt = "rbxassetid://108749195786444", Gender = "Female" },
	{ Id = "crimson-court-blazer", Name = "Crimson Court Blazer", Shirt = "rbxassetid://81449676375446", Gender = "Female" },
	{ Id = "choir-capelet", Name = "Choir Blouse & Capelet", Shirt = "rbxassetid://92038344609400", Gender = "Female" },
	{ Id = "ink-club-blouse", Name = "Ink Club Blouse", Shirt = "rbxassetid://130146407301064", Gender = "Female" },
	{ Id = "mourning-pinafore", Name = "Mourning Pinafore", Shirt = "rbxassetid://125153508249005", Gender = "Female" },
	{ Id = "summer-blouse", Name = "Summer Blouse", Shirt = "rbxassetid://71468061666418", Gender = "Female" },
	{ Id = "forest-vest-f", Name = "Forest Sweater Vest", Shirt = "rbxassetid://73003580509095", Gender = "Female" },
	{ Id = "delinquent-long-blazer", Name = "Delinquent Long Blazer", Shirt = "rbxassetid://95446318684651", Gender = "Female" },
	{ Id = "crimson-jumper", Name = "Crimson V-Neck Jumper", Shirt = "rbxassetid://82267514052524", Gender = "Female" },
	{ Id = "velvet-corset", Name = "Wine Velvet Corset", Shirt = "rbxassetid://93087343963914", Gender = "Female" },
	{ Id = "moto-cami", Name = "Cropped Moto Jacket & Lace Cami", Shirt = "rbxassetid://89558072025525", Gender = "Female" },
	{ Id = "moon-sweater", Name = "Off-Shoulder Moon Sweater", Shirt = "rbxassetid://81324792857416", Gender = "Female" },
	{ Id = "lace-blouse", Name = "Victorian Lace Blouse", Shirt = "rbxassetid://118907107993430", Gender = "Female" },
	{ Id = "cropped-hoodie", Name = "Cropped Crimson Hoodie", Shirt = "rbxassetid://88659118807328", Gender = "Female" },
	{ Id = "duster-slip", Name = "Long Duster & Slip Top", Shirt = "rbxassetid://82474737277515", Gender = "Female" },
	{ Id = "wool-overcoat", Name = "Wool Overcoat + Turtleneck", Shirt = "rbxassetid://106739966385590", Gender = "Male" },
	{ Id = "satin-bomber", Name = "Crimson Satin Bomber", Shirt = "rbxassetid://74398198814828", Gender = "Male" },
	{ Id = "denim-hoodie", Name = "Denim Jacket + Hoodie", Shirt = "rbxassetid://109051191198254", Gender = "Male" },
	{ Id = "henley-suspenders", Name = "Henley + Brass Suspenders", Shirt = "rbxassetid://117483426682275", Gender = "Male" },
	{ Id = "shawl-cardigan", Name = "Shawl Cardigan + Tie", Shirt = "rbxassetid://115359201454289", Gender = "Male" },
	{ Id = "track-jacket", Name = "Track Jacket", Shirt = "rbxassetid://71972073669268", Gender = "Male" },
	{ Id = "adm-night-warden", Name = "Night Warden Greatcoat", Shirt = "rbxassetid://89056529988336", Gender = "Unisex", Admin = true },
	{ Id = "adm-crimson-haori", Name = "Crimson Haori", Shirt = "rbxassetid://105148376808676", Gender = "Unisex", Admin = true },
	{ Id = "adm-exorcist-coat", Name = "Exorcist's Coat", Shirt = "rbxassetid://136667186002126", Gender = "Unisex", Admin = true },
	{ Id = "adm-reaper-cloak", Name = "Reaper's Hooded Cloak", Shirt = "rbxassetid://113659324463163", Gender = "Unisex", Admin = true },
	{ Id = "adm-council-captain", Name = "Council Captain's Coat", Shirt = "rbxassetid://96446121590415", Gender = "Unisex", Admin = true },
	{ Id = "adm-shadow-ops", Name = "Shadow Ops Jacket", Shirt = "rbxassetid://135675322522231", Gender = "Unisex", Admin = true },
	{ Id = "adm-midnight-tailcoat", Name = "Midnight Lord Tailcoat", Shirt = "rbxassetid://110052705054383", Gender = "Unisex", Admin = true },
	{ Id = "adm-duelist", Name = "Duelist's Jacket & Cape", Shirt = "rbxassetid://134379224025273", Gender = "Unisex", Admin = true },
}
-- Civilian clothes: what every new student owns. School tops must be owned (the enrollment pick at the
-- Enrollment desk, or the School Store); school bottoms unlock on enrolling. (Services.School.Enrollment)
Appearance.CivilianTops = {
	["blood-moon-hoodie"] = true, ["leather-jacket"] = true, ["open-flannel"] = true,
	["victorian-waistcoat"] = true, ["hussar-coat"] = true, ["the-hollow-band-tee"] = true,
	["lolita-dress"] = true, ["cable-knit"] = true, ["gala-gown"] = true,
	-- (1.71) civilian kit and admin kit (the admin kit is never sold; staff wear it free)
	["velvet-corset"] = true, ["moto-cami"] = true, ["moon-sweater"] = true, ["lace-blouse"] = true, ["cropped-hoodie"] = true, ["duster-slip"] = true, ["wool-overcoat"] = true, ["satin-bomber"] = true, ["denim-hoodie"] = true, ["henley-suspenders"] = true, ["shawl-cardigan"] = true, ["track-jacket"] = true, ["adm-night-warden"] = true, ["adm-crimson-haori"] = true, ["adm-exorcist-coat"] = true, ["adm-reaper-cloak"] = true, ["adm-council-captain"] = true, ["adm-shadow-ops"] = true, ["adm-midnight-tailcoat"] = true, ["adm-duelist"] = true,
}
Appearance.CivilianBottoms = {
	["dark-indigo-jeans"] = true, ["black-jeans"] = true, ["ripped-jeans"] = true, ["cargo-boots"] = true,
	["black-jeans-boots"] = true, ["striped-joggers"] = true, ["pinstripes-riding-boots"] = true, ["black-skirt-fishnets"] = true,
	["lolita-skirt"] = true, ["plaid-mini"] = true, ["gala-skirt"] = true,
	-- (1.71) civilian kit and admin kit
	["corset-flares"] = true, ["velvet-midi"] = true, ["leather-mini"] = true, ["wide-leg-trousers"] = true, ["skater-thighhighs"] = true, ["lace-maxi"] = true, ["trousers-chelsea"] = true, ["dark-jeans-hightops"] = true, ["track-pants"] = true, ["chinos-loafers"] = true, ["ripped-black-boots"] = true, ["cargo-shorts"] = true, ["adm-night-warden-tails"] = true, ["adm-hakama"] = true, ["adm-exorcist-trousers"] = true, ["adm-reaper-hem"] = true, ["adm-captain-riding"] = true, ["adm-shadow-cargo"] = true, ["adm-midnight-tails"] = true, ["adm-duelist-breeches"] = true,
}
-- the three uniforms offered on enrolling, per gender (Body 2 = female); race recolours apply automatically
Appearance.StarterUniforms = {
	Male = { Tops = { "black-blazer", "navy-vest", "charcoal-cardigan" }, Bottoms = "uniform-trousers" },
	Female = { Tops = { "crest-blazer", "navy-vest-f", "cropped-cardigan" }, Bottoms = "charcoal-pleats" }, -- (1.71) the schoolgirl kit
}
Appearance.UniformPrice = 250 -- Yen per school top at the School Store
function Appearance.IndexOf(list, id)
	for i, e in ipairs(list) do
		if e.Id == id then
			return i
		end
	end
	return nil
end
function Appearance.IsSchoolTop(index)
	local u = Appearance.Uniforms[index]
	return u ~= nil and not Appearance.CivilianTops[u.Id]
end
function Appearance.IsSchoolBottom(index)
	local b = Appearance.BottomsList[index]
	return b ~= nil and not Appearance.CivilianBottoms[b.Id]
end

-- Gender and staff clothing (1.71, owner: "the clothing needs to be separate by gender"). Every top and bottom has a
-- Gender: "Male", "Female" or "Unisex" (shown to both). A piece's own Gender field wins; else Female = true or
-- FemaleClothing makes it Female, UnisexClothing makes it Unisex, and the rest is Male. Admin = true pieces (the admin
-- kit) are for staff only: player attribute NHStaff >= 1, set by Features.Admin. The Wardrobe, the School Store and the
-- server's look check all use Appearance.ClothingAllows. A saved look keeps what it wears until it's changed.
Appearance.UnisexClothing = {
	["gym-pe-shirt"] = true, ["varsity-jacket"] = true, ["blood-moon-hoodie"] = true, ["the-hollow-band-tee"] = true,
	["striped-joggers"] = true, ["dark-indigo-jeans"] = true, ["black-jeans"] = true, ["ripped-jeans"] = true,
}
Appearance.FemaleClothing = { ["pleated-tartan-skirt"] = true, ["black-skirt-fishnets"] = true }
-- each piece and its other-gender version: switching gender swaps to it, and owning one school top counts for both
Appearance.Counterparts = {}
for _, pair in ipairs({
	{ "black-blazer", "crest-blazer" }, { "navy-vest", "navy-vest-f" }, { "charcoal-cardigan", "cropped-cardigan" },
	{ "vigil-vest", "vigil-vest-f" }, { "crimson-court-vest", "crimson-court-blazer" }, { "forest-vest", "forest-vest-f" },
	{ "delinquent-polo", "delinquent-long-blazer" }, { "black-shirt", "ink-club-blouse" }, { "crimson-polo", "crimson-jumper" },
	{ "ivory-polo", "summer-blouse" },
	{ "uniform-trousers", "charcoal-pleats" }, { "charcoal-slacks", "black-pleats-sheer" }, { "khaki-trousers", "navy-pleats" },
	{ "leather-jacket", "moto-cami" }, { "victorian-waistcoat", "lace-blouse" }, { "hussar-coat", "velvet-corset" },
	{ "open-flannel", "duster-slip" }, { "satin-bomber", "cropped-hoodie" }, { "denim-hoodie", "moon-sweater" },
	{ "cargo-boots", "leather-mini" }, { "black-jeans-boots", "corset-flares" }, { "pinstripes-riding-boots", "wide-leg-trousers" },
	{ "trousers-chelsea", "velvet-midi" }, { "chinos-loafers", "lace-maxi" },
}) do
	Appearance.Counterparts[pair[1]] = pair[2]
	Appearance.Counterparts[pair[2]] = pair[1]
end
-- what a gender gets when nothing it wears suits it any more (tops default to the unisex Blood Moon Hoodie)
Appearance.GenderDefaults = { Male = { Bottoms = "cargo-boots" }, Female = { Bottoms = "corset-flares" } }
function Appearance.GenderOf(entry)
	if not entry then
		return "Unisex"
	end
	if entry.Gender then
		return entry.Gender
	end
	if entry.Female or Appearance.FemaleClothing[entry.Id] then
		return "Female"
	end
	return Appearance.UnisexClothing[entry.Id] and "Unisex" or "Male"
end
function Appearance.IsStaff(player)
	return typeof(player) == "Instance" and (tonumber(player:GetAttribute("NHStaff")) or 0) >= 1
end
-- may this look (its body's gender) wear this piece? staff = may wear the admin kit
function Appearance.ClothingAllows(entry, look, staff)
	if not entry then
		return false
	end
	if entry.Admin and not staff then
		return false
	end
	local g = Appearance.GenderOf(entry)
	return g == "Unisex" or g == Appearance.BodyGender(type(look) == "table" and look.Body or look)
end
-- school-top ownership: owning a piece counts for its other-gender version too (Identity.Uniforms holds ids)
function Appearance.OwnsTop(owned, id)
	if type(owned) ~= "table" or not id then
		return false
	end
	local cp = Appearance.Counterparts[id]
	return table.find(owned, id) ~= nil or (cp ~= nil and table.find(owned, cp) ~= nil)
end
-- after a gender change: each worn piece the new gender can't wear becomes its counterpart, else that gender's default
function Appearance.DressForGender(look, staff)
	for _, spec in ipairs({ { "Uniform", Appearance.Uniforms }, { "Bottoms", Appearance.BottomsList } }) do
		local key, list = spec[1], spec[2]
		local cur = list[look[key]]
		if cur and not Appearance.ClothingAllows(cur, look, staff) then
			local cp = Appearance.Counterparts[cur.Id]
			local ci = cp and Appearance.IndexOf(list, cp)
			if ci and Appearance.ClothingAllows(list[ci], look, staff) then
				look[key] = ci
			else
				local d = Appearance.GenderDefaults[Appearance.BodyGender(look.Body)]
				look[key] = (d and d[key] and Appearance.IndexOf(list, d[key])) or Appearance.Defaults[key]
			end
		end
	end
	return look
end
-- a random piece an NPC of this look's gender could wear (never the admin kit)
function Appearance.RandomPiece(list, look)
	local pool = {}
	for i, e in ipairs(list) do
		if not e.Admin and Appearance.ClothingAllows(e, look, false) then
			table.insert(pool, i)
		end
	end
	return #pool > 0 and pool[math.random(1, #pool)] or 1
end

-- Race versions of the school uniform (clothing session; image ids). Worn in uniform mode only, keyed by
-- the player's Race: Shirts[i] replaces Uniforms[i]; Pants replaces the official trousers (Bottoms 1).
-- Other tops / bottoms, avatar mode and transformation outfits are unchanged.
Appearance.RaceUniforms = {
	Ghoul = {
		Shirts = {
			[1] = "rbxassetid://75282115673322", -- Red Vest
			[2] = "rbxassetid://71851326048367", -- Red Shirt
			[3] = "rbxassetid://70473044441154", -- Black Vest
			[4] = "rbxassetid://117242546409771", -- Black Shirt
		},
		Pants = "rbxassetid://115495222925569",
	},
}

-- Bottoms (data key Bottoms). 1 = the official uniform trousers.
Appearance.BottomsList = {
	{ Id = "uniform-trousers", Name = "Uniform Trousers", Template = Appearance.Pants.Template },
	{ Id = "dark-indigo-jeans", Name = "Dark Indigo Jeans", Template = "rbxassetid://96000307451923" },
	{ Id = "black-jeans", Name = "Black Jeans", Template = "rbxassetid://128318648376057" },
	{ Id = "ripped-jeans", Name = "Ripped Jeans", Template = "rbxassetid://134667912165119" },
	{ Id = "charcoal-slacks", Name = "Charcoal Slacks", Template = "rbxassetid://79890092859210" },
	{ Id = "khaki-trousers", Name = "Khaki Trousers", Template = "rbxassetid://92165415452345" },
	{ Id = "khaki-shorts", Name = "Khaki Shorts", Template = "rbxassetid://121776222862081" },
	{ Id = "pleated-tartan-skirt", Name = "Pleated Tartan Skirt", Template = "rbxassetid://85690129195432" },
	-- civilian (clothing session)
	{ Id = "cargo-boots", Name = "Cargo + Boots", Template = "rbxassetid://100719470659873" },
	{ Id = "black-jeans-boots", Name = "Black Jeans + Boots", Template = "rbxassetid://111155560587590" },
	{ Id = "striped-joggers", Name = "Striped Joggers", Template = "rbxassetid://139412137380678" },
	{ Id = "pinstripes-riding-boots", Name = "Pinstripes + Riding Boots", Template = "rbxassetid://121154909777878" },
	{ Id = "black-skirt-fishnets", Name = "Black Skirt + Fishnets", Template = "rbxassetid://102014097640002" },
	-- female outfits (2026-11-03): each pairs with the matching top above
	{ Id = "sailor-skirt", Name = "Sailor Skirt", Template = "rbxassetid://98354523964224", Female = true },
	{ Id = "chapel-skirt", Name = "Chapel Skirt + Tights", Template = "rbxassetid://129354749586720", Female = true },
	{ Id = "pinafore-skirt", Name = "Pinafore Skirt", Template = "rbxassetid://132305935792023", Female = true },
	{ Id = "cheer-skirt", Name = "Cheer Skirt", Template = "rbxassetid://87915264137976", Female = true },
	{ Id = "lolita-skirt", Name = "Lolita Skirt + Stockings", Template = "rbxassetid://138883555295233", Female = true },
	{ Id = "plaid-mini", Name = "Plaid Mini + Boots", Template = "rbxassetid://120585760495378", Female = true },
	{ Id = "gala-skirt", Name = "Gala Gown Skirt", Template = "rbxassetid://76676349618674", Female = true },
	-- (1.71) gender kits: schoolgirl skirts (school bottoms), civilian per gender, admin kit (staff only)
	{ Id = "charcoal-pleats", Name = "Charcoal Pleats + Knee Socks", Template = "rbxassetid://136595680779871", Gender = "Female" },
	{ Id = "vigil-tartan", Name = "Vigil Tartan + Tights", Template = "rbxassetid://84047896244219", Gender = "Female" },
	{ Id = "court-pleats", Name = "Crimson Court Pleats", Template = "rbxassetid://84119009662768", Gender = "Female" },
	{ Id = "navy-pleats", Name = "Navy Pleats + Ivory Socks", Template = "rbxassetid://129239234992657", Gender = "Female" },
	{ Id = "forest-tartan", Name = "Forest Tartan Skirt", Template = "rbxassetid://102514205734979", Gender = "Female" },
	{ Id = "black-pleats-sheer", Name = "Black Pleats + Sheer Tights", Template = "rbxassetid://127991026166918", Gender = "Female" },
	{ Id = "pinafore-stockings", Name = "Pinafore Skirt + Stockings", Template = "rbxassetid://104520896399978", Gender = "Female" },
	{ Id = "delinquent-long-skirt", Name = "Long Delinquent Skirt + Boots", Template = "rbxassetid://87839260098528", Gender = "Female" },
	{ Id = "crimson-tartan-tights", Name = "Crimson Tartan + Tights", Template = "rbxassetid://112945599527000", Gender = "Female" },
	{ Id = "chapel-midi", Name = "Chapel Midi Skirt + Tights", Template = "rbxassetid://138828254289244", Gender = "Female" },
	{ Id = "corset-flares", Name = "Corset-Belt Flares + Platforms", Template = "rbxassetid://139341866928255", Gender = "Female" },
	{ Id = "velvet-midi", Name = "Velvet Midi Skirt + Boots", Template = "rbxassetid://82409096922756", Gender = "Female" },
	{ Id = "leather-mini", Name = "Leather Mini + Ripped Tights", Template = "rbxassetid://100960345453121", Gender = "Female" },
	{ Id = "wide-leg-trousers", Name = "Wide-Leg Trousers", Template = "rbxassetid://126689427325893", Gender = "Female" },
	{ Id = "skater-thighhighs", Name = "Tartan Skater + Thigh-Highs", Template = "rbxassetid://110698266380980", Gender = "Female" },
	{ Id = "lace-maxi", Name = "Lace-Hem Maxi Skirt", Template = "rbxassetid://131837355491642", Gender = "Female" },
	{ Id = "trousers-chelsea", Name = "Wool Trousers + Chelsea Boots", Template = "rbxassetid://100320593351698", Gender = "Male" },
	{ Id = "dark-jeans-hightops", Name = "Dark Jeans + High-Tops", Template = "rbxassetid://124413043338399", Gender = "Male" },
	{ Id = "track-pants", Name = "Track Pants + Sneakers", Template = "rbxassetid://89194891614405", Gender = "Male" },
	{ Id = "chinos-loafers", Name = "Chinos + Loafers", Template = "rbxassetid://80222373485230", Gender = "Male" },
	{ Id = "ripped-black-boots", Name = "Ripped Black Jeans + Boots", Template = "rbxassetid://76269817376489", Gender = "Male" },
	{ Id = "cargo-shorts", Name = "Cargo Shorts + Socks", Template = "rbxassetid://129085384688877", Gender = "Male" },
	{ Id = "adm-night-warden-tails", Name = "Night Warden Coat Tails + Jackboots", Template = "rbxassetid://103839093067497", Gender = "Unisex", Admin = true },
	{ Id = "adm-hakama", Name = "Hakama + Tabi Boots", Template = "rbxassetid://124563755573649", Gender = "Unisex", Admin = true },
	{ Id = "adm-exorcist-trousers", Name = "Exorcist Trousers + Buckle Boots", Template = "rbxassetid://82910616585092", Gender = "Unisex", Admin = true },
	{ Id = "adm-reaper-hem", Name = "Tattered Cloak Hem + Wraps", Template = "rbxassetid://87142530546870", Gender = "Unisex", Admin = true },
	{ Id = "adm-captain-riding", Name = "Captain's Coat Tails + Riding Boots", Template = "rbxassetid://118424182345884", Gender = "Unisex", Admin = true },
	{ Id = "adm-shadow-cargo", Name = "Shadow Ops Cargo + Boots", Template = "rbxassetid://112823749606573", Gender = "Unisex", Admin = true },
	{ Id = "adm-midnight-tails", Name = "Tailcoat Tails + Riding Boots", Template = "rbxassetid://100394738477575", Gender = "Unisex", Admin = true },
	{ Id = "adm-duelist-breeches", Name = "Duelist Breeches + Thigh Boots", Template = "rbxassetid://91315441485958", Gender = "Unisex", Admin = true },
}
-- Eyes: 1 = Roblox face, then the painted shapes from UI.EyeArt.
Appearance.Eyes = { { Name = "Roblox face" } }
for _, s in ipairs(EyeArt.Shapes) do
	table.insert(Appearance.Eyes, { Name = s.Name, Shape = s.Id })
end
Appearance.EyeSets = { "Male", "Female" }
Appearance.Brows = { { Name = "None" } }
for _, b in ipairs(EyeArt.BrowStyles) do
	table.insert(Appearance.Brows, { Name = b.Name, Style = b.Id })
end
Appearance.Mouths = { { Name = "None" } }
for _, mo in ipairs(EyeArt.MouthStyles) do
	table.insert(Appearance.Mouths, { Name = mo.Name, Style = mo.Id })
end
-- Race mouths (2026-11-04): only offered to, and only drawn on, that race (Race = a Lineage race id)
for _, mo in ipairs(EyeArt.RaceMouths or {}) do
	table.insert(Appearance.Mouths, { Name = mo.Name, Style = mo.Id, Race = mo.Race })
end
-- Face marks (2026-11-04): 1 = none, then EyeArt.Marks. A mark with a Race only shows on that race.
Appearance.Marks = { { Name = "None" } }
for _, mk in ipairs(EyeArt.Marks or {}) do
	table.insert(Appearance.Marks, { Name = mk.Name, Style = mk.Id, Race = mk.Race })
end
-- Bloodline eyes (look field RaceEyes): your race's eyes without transforming. Priests get a gold iris.
Appearance.PriestIris = rgb(236, 196, 90)
function Appearance.RaceAllows(entry, race)
	return entry ~= nil and (entry.Race == nil or entry.Race == race)
end
Appearance.EyeColors = {
	{ Id = "umber", Name = "Umber", Color = rgb(150, 98, 62) },
	{ Id = "hazel", Name = "Hazel", Color = rgb(150, 128, 70) },
	{ Id = "moss", Name = "Moss", Color = rgb(96, 136, 88) },
	{ Id = "ice", Name = "Ice", Color = rgb(124, 172, 214) },
	{ Id = "ash", Name = "Ash", Color = rgb(150, 156, 166) },
	{ Id = "violet", Name = "Violet", Color = rgb(128, 96, 166) },
	{ Id = "amber", Name = "Amber", Color = rgb(214, 156, 52) },
}
Appearance.NightbornIris = rgb(214, 34, 50)
-- Transformation forms (character attribute Transformation, set by gameplay) -> eye art + iris tint
Appearance.Forms = {
	-- Stage2: the second transformation (character attribute TransformationStage = 2): jet-black sclera
	-- Veins: vein layer colour, mixed 50/50 with the character's real skin colour so veins look natural on any skin
	-- Outfit: worn while transformed (clothing session). Priest has an outfit only (eyes unchanged).
	-- UniformOutfit: the school top as it transforms, used when you transform wearing a school top; it has no
	--   Pants, so your own uniform bottoms (trousers or skirt) stay on. FemaleOutfit: the full form on the
	--   Female body when you aren't in uniform. Appearance.FormOutfit picks between the three.
	Vampire = { Key = "vampire", Tint = rgb(220, 34, 52), Stage2 = "vampire2", Veins = rgb(158, 10, 31),
		Outfit = { Shirt = "rbxassetid://84954175291601", Pants = "rbxassetid://91761624304127" },
		UniformOutfit = { Shirt = "rbxassetid://99568494756631" },
		FemaleOutfit = { Shirt = "rbxassetid://82036496118569", Pants = "rbxassetid://72055367907700" } },
	Wolf = { Key = "wolf", Tint = rgb(236, 158, 40),
		Outfit = { Shirt = "rbxassetid://77909860828071", Pants = "rbxassetid://129868849941474" },
		UniformOutfit = { Shirt = "rbxassetid://81458513797704" } },
	Ghoul = { Key = "ghoul", Tint = rgb(214, 220, 204), Stage2 = "ghoul2", Veins = rgb(77, 13, 82),
		Outfit = { Shirt = "rbxassetid://122227122884831", Pants = "rbxassetid://80804276005159" },
		UniformOutfit = { Shirt = "rbxassetid://121170882178993" } },
	Wraith = { Key = "wraith", Tint = rgb(158, 220, 255),
		Outfit = { Shirt = "rbxassetid://92404956711982", Pants = "rbxassetid://121029292372649" },
		UniformOutfit = { Shirt = "rbxassetid://81276347693530" },
		FemaleOutfit = { Shirt = "rbxassetid://94381120030964", Pants = "rbxassetid://129307806934839" } },
	Priest = { Outfit = { Shirt = "rbxassetid://130811233234323", Pants = "rbxassetid://73003093663735" } },
}
-- Which transformation outfit to wear: the transformed school top over your own bottoms when you're in
-- uniform (a school top, not your Roblox outfit), else the Female full form on the Female body, else the
-- form's full outfit. Returns { Shirt, Pants? } or nil; a nil Pants means "keep your own bottoms".
function Appearance.FormOutfit(form, data)
	if not form then
		return nil
	end
	if data and not data.UseAvatar and form.UniformOutfit and Appearance.IsSchoolTop(data.Uniform) then
		return form.UniformOutfit
	end
	local body = data and Appearance.Bodies[data.Body]
	if body and body.Gender == "Female" and form.FemaleOutfit then
		return form.FemaleOutfit
	end
	return form.Outfit
end
-- race names map onto the same forms (Races/Bloodlines design): Transformation = "Werewolf" works like "Wolf"
Appearance.Forms.Werewolf = Appearance.Forms.Wolf
-- The form a character is in, so every race wears its own transformation outfit (and eyes / mouth):
--   Transformation = a form name ("Vampire", "Wolf"/"Werewolf", "Ghoul", "Wraith", "Priest") -> that form
--   Transformation = a race or sub-race id ("Bloodmoon", "RoyalVamp"...) -> that race's form
--   Transformation = true / "Race" / anything else -> the player's rolled race (Player attribute Race)
-- Humans have no transformation form. Returns the Forms entry, or nil when not transformed.
function Appearance.FormOf(character)
	if not character then
		return nil
	end
	local t = character:GetAttribute("Transformation")
	if t == nil or t == false or t == "" then
		return nil
	end
	if type(t) == "string" and Appearance.Forms[t] then
		return Appearance.Forms[t]
	end
	local okL, Lineage = pcall(require, ReplicatedStorage:FindFirstChild("Lineage"))
	if type(t) == "string" and okL and type(Lineage) == "table" and Lineage.SubById and Lineage.SubById[t] then
		return Appearance.Forms[Lineage.SubById[t].Race.Id]
	end
	local player = Players:GetPlayerFromCharacter(character)
	local race = (player and player:GetAttribute("Race")) or character:GetAttribute("Race")
	return race and Appearance.Forms[race] or nil
end
-- Transformation variants (2026-11-04): every everyday piece has its own transformed version per form
-- (UI.FormVariants, keyed by the template id the piece is worn with). nil = no variant for that piece / form.
local FormVariantsOk, FormVariants = pcall(function()
	return require(script.Parent:FindFirstChild("FormVariants"))
end)
local FORM_NAME = {}
for name, f in pairs(Appearance.Forms) do
	if name ~= "Werewolf" then
		FORM_NAME[f] = name
	end
end
function Appearance.FormVariant(form, template)
	if not (FormVariantsOk and type(FormVariants) == "table" and form and type(template) == "string") then
		return nil
	end
	local id = string.match(template, "%d+")
	local v = id and FormVariants[id]
	return v and v[FORM_NAME[form] or ""] or nil
end
-- Body shape (2026-11-01): Standard or Female. Saved as an id.
-- Female (2026-11-10): five R6 CharacterMeshes (art/characters/female, group meshes). The torso keeps the old hourglass,
--   smoothed, with softer shoulders, a soft bust and hips; arms and legs taper on the outer side. Every mesh stays inside its
--   R6 part box, and the UVs index Roblox's R6 clothing atlas, so Shirts / Pants / skin colour work as on a standard body.
--   v2 (2026-11-10, owner): the legs meet like standard R6 (near-square inner edges) and a fuller bust.
--   (Before: TorsoMesh 48112070, Roblox's 2011 Girl torso, on standard limbs.)
Appearance.Bodies = {
	{ Id = "standard", Name = "Standard", Gender = "Male", Build = "Average", Step = 0 },
	{ Id = "female", Name = "Female", Gender = "Female", Build = "Average", Step = 0, TorsoMesh = 107771235632658,
		Meshes = { Torso = 107771235632658, RightArm = 107796907683955, LeftArm = 80112520115136,
			RightLeg = 111053847385892, LeftLeg = 87713593848889 } },
	-- body types (2026-11-10, art/characters/bodies/nh_body_types.py): earned only through training or the admin desk
	-- (Appearance.SetBuild). Variants of the standard body (male) and the Female body v2 (female).
	{ Id = "lean", Name = "Lean", Gender = "Male", Build = "Skinny", Step = 1, TorsoMesh = 80599151440718,
		Meshes = { Torso = 80599151440718, RightArm = 81698806804529, LeftArm = 115700541325418, RightLeg = 102705588776863, LeftLeg = 133298074138660 } },
	{ Id = "athletic", Name = "Athletic", Gender = "Male", Build = "Conditioned", Step = 1, TorsoMesh = 131786090664045,
		Meshes = { Torso = 131786090664045, RightArm = 132414762109621, LeftArm = 131417759794420, RightLeg = 120173701032082, LeftLeg = 112936256263410 } },
	{ Id = "muscular", Name = "Muscular", Gender = "Male", Build = "Conditioned", Step = 2, TorsoMesh = 77979027494394,
		Meshes = { Torso = 77979027494394, RightArm = 105787224767323, LeftArm = 132341858324942, RightLeg = 123508178938073, LeftLeg = 129971107420398 } },
	{ Id = "stocky", Name = "Stocky", Gender = "Male", Build = "Heavy", Step = 1, TorsoMesh = 97395586937787,
		Meshes = { Torso = 97395586937787, RightArm = 116817128513775, LeftArm = 99902053204043, RightLeg = 127221281464817, LeftLeg = 110235894677793 } },
	{ Id = "heavy", Name = "Heavy", Gender = "Male", Build = "Heavy", Step = 2, TorsoMesh = 113481648066946,
		Meshes = { Torso = 113481648066946, RightArm = 94026483479391, LeftArm = 117091958168532, RightLeg = 111602082267684, LeftLeg = 76843775024418 } },
	{ Id = "petite", Name = "Petite", Gender = "Female", Build = "Skinny", Step = 1, TorsoMesh = 98160542260548,
		Meshes = { Torso = 98160542260548, RightArm = 137735929863681, LeftArm = 140464173247332, RightLeg = 93849031916640, LeftLeg = 81128309715298 } },
	{ Id = "toned", Name = "Toned", Gender = "Female", Build = "Conditioned", Step = 1, TorsoMesh = 109650324114415,
		Meshes = { Torso = 109650324114415, RightArm = 108348625488717, LeftArm = 101966670697769, RightLeg = 91312785820514, LeftLeg = 119700145873929 } },
	{ Id = "curvy", Name = "Curvy", Gender = "Female", Build = "Heavy", Step = 1, TorsoMesh = 90093573152527,
		Meshes = { Torso = 90093573152527, RightArm = 97161066706362, LeftArm = 81650822243600, RightLeg = 79830470075363, LeftLeg = 116410414866469 } },
	{ Id = "strong", Name = "Strong", Gender = "Female", Build = "Conditioned", Step = 2, TorsoMesh = 97081723455688,
		Meshes = { Torso = 97081723455688, RightArm = 81789560903270, LeftArm = 121910719117018, RightLeg = 135474747479085, LeftLeg = 86478900952963 } },
	{ Id = "plus", Name = "Plus", Gender = "Female", Build = "Heavy", Step = 2, TorsoMesh = 77671978644176,
		Meshes = { Torso = 77671978644176, RightArm = 131507995802644, LeftArm = 132653815234283, RightLeg = 120966302767125, LeftLeg = 138612636058559 } },
}
-- Body gender (2026-11-10 body types): every body carries Gender. Use these instead of `Body == 2`, so the female
-- body types (Petite, Toned, Curvy, Strong, Plus) count as female everywhere. `body` is an index or an id.
function Appearance.BodyGender(body)
	local b = type(body) == "number" and Appearance.Bodies[body] or nil
	if not b and type(body) == "string" then
		for _, x in ipairs(Appearance.Bodies) do
			if x.Id == body then b = x end
		end
	end
	return (b and b.Gender) or "Male"
end
function Appearance.IsFemale(look)
	return type(look) == "table" and Appearance.BodyGender(look.Body) == "Female"
end
-- Builds (2026-11-10, owner: body types come "Only through training (or the admin menu)"): every body has a Build
-- ("Average", "Skinny", "Conditioned" or "Heavy") and a Step (0 for Average, then 1, 2). The creator only picks the
-- gender; Appearance.SetBuild (server) is how training and the admin desk change the build.
Appearance.Builds = { "Average", "Skinny", "Conditioned", "Heavy" }
function Appearance.BodyBuild(body)
	local b = type(body) == "number" and Appearance.Bodies[body] or nil
	if not b and type(body) == "string" then
		for _, x in ipairs(Appearance.Bodies) do
			if x.Id == body then b = x end
		end
	end
	return (b and b.Build) or "Average", (b and b.Step) or 0
end
-- the body index for a gender, build and step: the highest step that exists up to `step`, else that gender's base body
function Appearance.BodyFor(gender, build, step)
	gender = gender == "Female" and "Female" or "Male"
	local best, bestStep, base = nil, -1, nil
	for i, b in ipairs(Appearance.Bodies) do
		if (b.Gender or "Male") == gender then
			if (b.Build or "Average") == "Average" and not base then base = i end
			if b.Build == build and (b.Step or 0) <= (step or 0) and (b.Step or 0) > bestStep then
				best, bestStep = i, b.Step or 0
			end
		end
	end
	return best or base
end
-- (training 1.81) per-area bodies. Training changes one area at a time (Appearance.SetArea, server): the torso, both
-- arms or both legs can each come from a different build path and step. A look's Areas is "torso|arms|legs" (body
-- ids); "" means Body for all three, so every save from before training keeps its body. Each area is shown in the
-- look's gender (a gender switch in the creator keeps each area's build and step).
Appearance.AreaNames = { "Torso", "Arms", "Legs" }
Appearance.AreaParts = { Torso = { "Torso" }, Arms = { "RightArm", "LeftArm" }, Legs = { "RightLeg", "LeftLeg" } }
local function bodyIndexById(id)
	for i, b in ipairs(Appearance.Bodies) do
		if b.Id == id then
			return i
		end
	end
	return nil
end
function Appearance.ParseAreas(s)
	if type(s) ~= "string" or s == "" then
		return nil
	end
	local ids = string.split(s, "|")
	if #ids ~= 3 then
		return nil
	end
	local out = {}
	for i, name in ipairs(Appearance.AreaNames) do
		local idx = bodyIndexById(ids[i])
		if not idx then
			return nil
		end
		out[name] = idx
	end
	return out
end
function Appearance.EncodeAreas(areas)
	local ids = {}
	for i, name in ipairs(Appearance.AreaNames) do
		local b = Appearance.Bodies[areas[name]] or Appearance.Bodies[1]
		ids[i] = b.Id
	end
	return table.concat(ids, "|")
end
-- { Torso = index, Arms = index, Legs = index } for a sanitized look, each in the look's gender
function Appearance.AreaBodies(look)
	look = type(look) == "table" and look or {}
	local body = type(look.Body) == "number" and look.Body or 1
	local gender = Appearance.BodyGender(body)
	local parsed = Appearance.ParseAreas(look.Areas)
	local out = {}
	for _, name in ipairs(Appearance.AreaNames) do
		local idx = parsed and parsed[name] or body
		if Appearance.BodyGender(idx) ~= gender then
			local build, step = Appearance.BodyBuild(idx)
			idx = Appearance.BodyFor(gender, build, step) or body
		end
		out[name] = idx
	end
	return out
end
-- Capes (2026-11-01): bought in the Spin Shop (Config.Shop Kind = "Cape"), owned in Identity.Capes, worn here.
-- Models: ReplicatedStorage.NHCapes.<Model> (rigged; Controllers.Character.CapeSway moves the bones).
Appearance.Capes = {
	{ Id = "none", Name = "None" },
	{ Id = "CapeVamp", Name = "Vamp Cape", Model = "Vamp Cape" },
	{ Id = "CapeRogue", Name = "Rogue Cape", Model = "Rogue Cape" },
	{ Id = "CapeFur", Name = "Fur Cape", Model = "Fur Cape" },
	-- the admin kit's 3D capes (staff-only: Wardrobe + server look check + WearCape; never sold). docs/Admin-Capes.md
	{ Id = "CapeWardenMantle", Name = "Night Warden's Mantle", Model = "Night Warden's Mantle", Admin = true },
	{ Id = "CapeReaperShroud", Name = "Reaper's Tattered Shroud", Model = "Reaper's Tattered Shroud", Admin = true },
	{ Id = "CapeDuelist", Name = "Duelist's Shoulder Cape", Model = "Duelist's Shoulder Cape", Admin = true },
	{ Id = "CapeCaptain", Name = "Council Captain's Greatcape", Model = "Council Captain's Greatcape", Short = "Captain's Greatcape", Admin = true },
	{ Id = "CapeMidnight", Name = "Midnight Lord's High-Collar Cape", Model = "Midnight Lord's High-Collar Cape", Short = "Midnight Lord's Cape", Admin = true },
}
Appearance.Defaults = {
	LookStyle = "Scholar", Skin = 2, SkinHex = "", Hair = 2, HairColor = 1, HairHex = "", HairId = 0, TintHair = false,
	Uniform = 19, Eyes = 2, EyeSet = 1, EyeColor = 1, EyeHex = "", Brows = 2, BrowHex = "", Mouth = 2, Lips = false, Bottoms = 9,
	UseAvatar = false, Created = false, Body = 1, Cape = 1, Marks = 1, RaceEyes = false,
	Acc = "", -- NHAccessories (1.79): the worn 3D accessories (Config.Accessories ids, one per slot, comma list)
	Areas = "", -- (training 1.81) per-area bodies "torso|arms|legs" (body ids); "" = Body for all three. Server-only (SetArea).
}

local LookIds = {}
for _, l in ipairs(Appearance.Looks) do
	LookIds[l.Id] = true
end

local function hexOf(v)
	if type(v) ~= "string" then
		return ""
	end
	local h = string.match(v, "^%s*#?(%x%x%x%x%x%x)%s*$")
	return h and string.upper(h) or ""
end
Appearance.Hex = hexOf

--------------------------------------------------------------------------
-- Saved looks use stable ids, not list positions (so reordering / inserting options never changes
-- anyone's look). In memory (Sanitize output, the Wardrobe) the fields are list indices, marked _Idx.
-- On the wire and in the profile they are ids:  Eyes = "doe", Uniform = "red-vest", Skin = "#D8B492"...
-- Id per list: Skin = "#"..hex of the colour, Hair / EyeSet = the name, Eyes / Brows / Mouth = the
-- EyeArt id ("face" / "none" for slot 1), HairColor / Uniform / Bottoms / EyeColor = the entry's Id.
-- New options: give them a NEW unique Id; never reuse or change an existing one.
--------------------------------------------------------------------------
-- FROZEN: the list order before ids (2026-10-30). A bare number in a save is read through this table,
-- never through the live lists, so old saves stay right forever. NEVER EDIT OR REORDER THIS TABLE.
local LEGACY_ORDER = {
	Skin = { "#ECCEB2", "#D8B492", "#B48462", "#845C3E", "#5E402E", "#F6E4D8" },
	Hair = { "Neat Crop", "Fringe", "Long", "Bun", "None" },
	HairColor = { "black", "raven", "chestnut", "ash-blonde", "silver", "blood-red" },
	Uniform = { "red-vest", "red-shirt", "black-vest", "black-shirt", "navy-vest", "forest-vest", "charcoal-vest", "vigil-vest", "crimson-court-vest", "navy-polo", "forest-polo", "ivory-polo", "crimson-polo", "delinquent-polo", "black-blazer", "charcoal-cardigan", "varsity-jacket", "gym-pe-shirt", "blood-moon-hoodie", "leather-jacket", "open-flannel", "victorian-waistcoat", "hussar-coat", "the-hollow-band-tee" },
	Bottoms = { "uniform-trousers", "dark-indigo-jeans", "black-jeans", "ripped-jeans", "charcoal-slacks", "khaki-trousers", "khaki-shorts", "pleated-tartan-skirt", "cargo-boots", "black-jeans-boots", "striped-joggers", "pinstripes-riding-boots", "black-skirt-fishnets" },
	Eyes = { "face", "sharp", "hooded", "fierce", "doe", "sleepless", "cat", "gentle", "calm" },
	EyeSet = { "Male", "Female" },
	EyeColor = { "umber", "hazel", "moss", "ice", "ash", "violet", "amber" },
	Brows = { "none", "straight", "arched", "angled", "soft", "thick", "thin", "furrowed", "raised", "bold", "heavy", "bushy", "sleek", "flatthick", "higharch", "sharparch", "worried", "angry", "feathered", "wisp", "tapered", "rounded" },
	Mouth = { "none", "neutral", "smile", "flat", "smirk", "hint", "grin", "small", "ooh", "open", "talk", "laugh", "shout", "pout", "frown", "scowl", "sulk", "grimace", "cat", "fang", "shark" },
}

local LIST_KEYS = { "Skin", "Hair", "HairColor", "Uniform", "Bottoms", "Eyes", "EyeSet", "EyeColor", "Brows", "Mouth", "Marks" }
local function listOf(key)
	return ({
		Skin = Appearance.Skins, Hair = Appearance.HairStyles, HairColor = Appearance.HairColors,
		Uniform = Appearance.Uniforms, Bottoms = Appearance.BottomsList, Eyes = Appearance.Eyes,
		EyeSet = Appearance.EyeSets, EyeColor = Appearance.EyeColors, Brows = Appearance.Brows, Mouth = Appearance.Mouths,
		Marks = Appearance.Marks,
	})[key]
end
local function entryId(key, e)
	if key == "Skin" then
		return "#" .. e:ToHex():upper()
	elseif key == "Hair" or key == "EyeSet" then
		return e
	elseif key == "Eyes" then
		return e.Shape or "face"
	elseif key == "Brows" or key == "Mouth" or key == "Marks" then
		return e.Style or "none"
	end
	return e.Id
end
local IndexById = {} -- [key][id] = current index
for _, key in ipairs(LIST_KEYS) do
	IndexById[key] = {}
	for i, e in ipairs(listOf(key)) do
		IndexById[key][entryId(key, e)] = i
	end
end
function Appearance.IdOf(key, index)
	local e = listOf(key)[index]
	return e ~= nil and entryId(key, e) or nil
end
-- a saved / sent value -> current list index (nil = unknown, keep the default)
local function resolveIndex(key, v, isIndex)
	if type(v) == "string" then
		return IndexById[key][v]
	elseif type(v) == "number" and v == math.floor(v) then
		if isIndex then -- already a current index (an in-memory look)
			return (v >= 1 and v <= #listOf(key)) and v or nil
		end
		local id = LEGACY_ORDER[key] and LEGACY_ORDER[key][v] -- an old save: a position in the frozen order (new keys have none)
		return id and IndexById[key][id] or nil
	end
	return nil
end
-- in-memory look (indices) -> stored / sent form (ids). Drops the _Idx marker.
function Appearance.Encode(look)
	local out = table.clone(Appearance.Sanitize(look))
	out._Idx = nil
	for _, key in ipairs(LIST_KEYS) do
		out[key] = Appearance.IdOf(key, out[key])
	end
	out.Body = (Appearance.Bodies[out.Body] or Appearance.Bodies[1]).Id
	out.Cape = (Appearance.Capes[out.Cape] or Appearance.Capes[1]).Id
	out.V = 2
	return out
end
-- does a stored look still use old list positions? (one-time migration)
function Appearance.IsLegacy(stored)
	if type(stored) ~= "table" or stored._Idx then
		return false
	end
	for _, key in ipairs(LIST_KEYS) do
		if type(stored[key]) == "number" then
			return true
		end
	end
	return false
end

function Appearance.Sanitize(data)
	local out = table.clone(Appearance.Defaults)
	if type(data) ~= "table" then
		out._Idx = true
		return out
	end
	if LookIds[data.LookStyle] then
		out.LookStyle = data.LookStyle
	end
	local isIndex = data._Idx == true
	local function index(key, _list)
		local i = resolveIndex(key, data[key], isIndex)
		if i then
			out[key] = i
		end
	end
	index("Skin", Appearance.Skins)
	index("Hair", Appearance.HairStyles)
	index("HairColor", Appearance.HairColors)
	index("Uniform", Appearance.Uniforms)
	index("Bottoms", Appearance.BottomsList)
	index("Eyes", Appearance.Eyes)
	index("EyeSet", Appearance.EyeSets)
	index("EyeColor", Appearance.EyeColors)
	index("Brows", Appearance.Brows)
	index("Mouth", Appearance.Mouths)
	index("Marks", Appearance.Marks)
	for i, c in ipairs(Appearance.Capes) do
		if data.Cape == c.Id or (isIndex and data.Cape == i) then
			out.Cape = i
		end
	end
	for i, b in ipairs(Appearance.Bodies) do
		if data.Body == b.Id or (isIndex and data.Body == i) then
			out.Body = i
		end
	end
	do -- 3D accessories: a comma list of known ids, one per slot, in slot order (equal looks compare equal)
		local cfgF = ReplicatedStorage:FindFirstChild("Config")
		local mod = cfgF and cfgF:FindFirstChild("Accessories")
		local okA, AccCfg = pcall(require, mod)
		if mod and okA and type(data.Acc) == "string" then
			out.Acc = AccCfg.Join(AccCfg.Parse(data.Acc))
		end
	end
	out.SkinHex, out.HairHex, out.EyeHex = hexOf(data.SkinHex), hexOf(data.HairHex), hexOf(data.EyeHex)
	out.BrowHex = hexOf(data.BrowHex)
	local id = tonumber(data.HairId)
	if id and id == math.floor(id) and id > 0 and id < 1e15 then
		out.HairId = id
	end
	if type(data.Areas) == "string" and Appearance.ParseAreas(data.Areas) then
		out.Areas = data.Areas -- (training 1.81) per-area bodies
	end
	for _, k in ipairs({ "UseAvatar", "Created", "TintHair", "Lips", "RaceEyes" }) do
		if type(data[k]) == "boolean" then
			out[k] = data[k]
		end
	end
	out._Idx = true -- list fields are current indices (Appearance.Encode gives the saved form)
	return out
end

-- Resolved colours for a sanitized look
function Appearance.SkinColor(d)
	return d.SkinHex ~= "" and Color3.fromHex(d.SkinHex) or Appearance.Skins[d.Skin]
end
function Appearance.HairColor(d)
	return d.HairHex ~= "" and Color3.fromHex(d.HairHex) or Appearance.HairColors[d.HairColor].Color
end
function Appearance.BrowColor(d)
	if d.BrowHex ~= "" then
		return Color3.fromHex(d.BrowHex)
	end
	return Appearance.HairColor(d):Lerp(Color3.new(0, 0, 0), 0.18) -- brows read a little darker than hair
end
function Appearance.EyeColor(d)
	return d.EyeHex ~= "" and Color3.fromHex(d.EyeHex) or Appearance.EyeColors[d.EyeColor].Color
end

--------------------------------------------------------------------------
-- building the look (server)
--------------------------------------------------------------------------
local LOOK = "NHLook"

-- Hair is fitted for the player's head (the game's characters are 0.9 scale: StarterCharacter's head is 1.8 x 0.9 x
-- 0.9). The NPC rig's head is full size (2 x 1 x 1), so hair fitted for a player sat too small on every NPC: the
-- head showed through it and fringes sat on the face (owner report, 2026-11-03). Both kinds of hair now scale by
-- the head they go on (players: x1, unchanged).
local FIT_HEAD = 0.9
local function headScale(head)
	local k = head and head:IsA("BasePart") and head.Size.Y / FIT_HEAD or 1
	return if math.abs(k - 1) < 0.01 then 1 else k
end
Appearance.HeadScale = headScale

local function part(parent, name, size, color, cf, attachTo, shape, material)
	local p = Instance.new("Part")
	p.Name = name
	p.Size = size
	p.Color = color
	p.Material = material or Enum.Material.SmoothPlastic
	p.Shape = shape or Enum.PartType.Block
	p.TopSurface, p.BottomSurface = Enum.SurfaceType.Smooth, Enum.SurfaceType.Smooth
	p.CanCollide, p.CanQuery, p.CanTouch, p.Massless = false, false, false, true
	p.CastShadow = false
	p.CFrame = attachTo.CFrame * cf
	local w = Instance.new("WeldConstraint")
	w.Part0, w.Part1 = attachTo, p
	w.Parent = p
	p.Parent = parent
	return p
end

local function hair(folder, head, style, color)
	local k = headScale(head) -- sized for a player's head; scaled to this one
	local V = function(x, y, z) return Vector3.new(x, y, z) * k end
	local C = function(x, y, z) return CFrame.new(x * k, y * k, z * k) end
	part(folder, "HairTop", V(1.18, 0.3, 1.18), color, C(0, 0.48, 0.03), head)
	if style == 1 then -- Neat Crop
		part(folder, "HairSideL", V(0.12, 0.34, 0.96), color, C(-0.58, 0.28, 0.08), head)
		part(folder, "HairSideR", V(0.12, 0.34, 0.96), color, C(0.58, 0.28, 0.08), head)
		part(folder, "HairBack", V(1.18, 0.42, 0.14), color, C(0, 0.24, 0.57), head)
	elseif style == 2 then -- Fringe
		part(folder, "HairFringe", V(1.18, 0.2, 0.14), color, C(0, 0.3, -0.56), head)
		part(folder, "HairSideL", V(0.12, 0.46, 0.96), color, C(-0.58, 0.22, 0.08), head)
		part(folder, "HairSideR", V(0.12, 0.46, 0.96), color, C(0.58, 0.22, 0.08), head)
		part(folder, "HairBack", V(1.18, 0.56, 0.14), color, C(0, 0.18, 0.57), head)
	elseif style == 3 then -- Long
		part(folder, "HairFringe", V(1.18, 0.16, 0.14), color, C(0, 0.33, -0.56), head)
		part(folder, "HairSideL", V(0.12, 0.95, 0.96), color, C(-0.58, -0.02, 0.08), head)
		part(folder, "HairSideR", V(0.12, 0.95, 0.96), color, C(0.58, -0.02, 0.08), head)
		part(folder, "HairBack", V(1.18, 1.25, 0.16), color, C(0, -0.18, 0.58), head)
	else -- Bun
		part(folder, "HairSideL", V(0.12, 0.3, 0.96), color, C(-0.58, 0.3, 0.08), head)
		part(folder, "HairSideR", V(0.12, 0.3, 0.96), color, C(0.58, 0.3, 0.08), head)
		part(folder, "HairBack", V(1.18, 0.4, 0.14), color, C(0, 0.25, 0.57), head)
		part(folder, "HairBun", V(0.5, 0.5, 0.5), color, C(0, 0.52, 0.66), head, Enum.PartType.Ball)
	end
end

-- Stash / restore the Roblox avatar outfit (kept in ServerStorage while the uniform is worn).
local Stashes = setmetatable({}, { __mode = "k" }) -- [character] = { folder, colors }
local HairStashes = setmetatable({}, { __mode = "k" }) -- [character] = folder (avatar hair hidden by a catalog hair id)
local AVATAR_CLASSES = { "Accessory", "Shirt", "Pants", "ShirtGraphic" }
local BODY_PROPS = { "HeadColor3", "TorsoColor3", "LeftArmColor3", "RightArmColor3", "LeftLegColor3", "RightLegColor3" }
local NH_HAIR = "NHHair"

local function stashRoot(name)
	local storage = game:GetService("ServerStorage")
	local root = storage:FindFirstChild(name) or Instance.new("Folder")
	root.Name = name
	root.Parent = storage
	return root
end

local function bodyColors(character)
	local bc = character:FindFirstChildOfClass("BodyColors")
	if not bc then
		bc = Instance.new("BodyColors")
		local function c(n)
			local p = character:FindFirstChild(n)
			return p and p:IsA("BasePart") and p.Color or rgb(163, 162, 165)
		end
		bc.HeadColor3, bc.TorsoColor3 = c("Head"), c("Torso")
		bc.LeftArmColor3, bc.RightArmColor3 = c("Left Arm"), c("Right Arm")
		bc.LeftLegColor3, bc.RightLegColor3 = c("Left Leg"), c("Right Leg")
		bc.Parent = character
	end
	return bc
end

local function stash(character, clothesOnly)
	if Stashes[character] then
		return
	end
	local folder = Instance.new("Folder")
	folder.Name = character.Name
	folder.Parent = stashRoot("NHAppearanceStash")
	local bc = bodyColors(character)
	local colors = {}
	for _, n in ipairs(BODY_PROPS) do
		colors[n] = bc[n]
	end
	for _, d in ipairs(character:GetChildren()) do
		for _, cls in ipairs(AVATAR_CLASSES) do
			if d:IsA(cls) and d.Name ~= NH_HAIR and not (clothesOnly and cls == "Accessory") then
				d.Parent = folder
			end
		end
	end
	Stashes[character] = { folder = folder, colors = colors, clothesOnly = clothesOnly == true }
	character.Destroying:Connect(function()
		folder:Destroy()
	end)
end

local UNIFORM_SHIRT, UNIFORM_PANTS = "NHUniformShirt", "NHUniformPants"
local function clearUniform(character)
	for _, n in ipairs({ UNIFORM_SHIRT, UNIFORM_PANTS }) do
		local c = character:FindFirstChild(n)
		if c then
			c:Destroy()
		end
	end
end

local function restore(character)
	clearUniform(character)
	local s = Stashes[character]
	if not s then
		return
	end
	Stashes[character] = nil
	for _, d in ipairs(s.folder:GetChildren()) do
		d.Parent = character
	end
	s.folder:Destroy()
	local bc = bodyColors(character)
	for n, v in pairs(s.colors) do
		bc[n] = v
	end
end

-- Catalog hair (any Roblox hair accessory id). Loaded once per id through a HumanoidDescription.
local HairCache = {} -- [id] = Accessory template | false (known not a hair)
local HairNames = {}
local HairCount = 0
local HairFailedAt = {} -- [id] = os.clock() of a temporary failure (lookup / load), retried after HAIR_RETRY
local HAIR_RETRY, HAIR_CACHE_MAX = 30, 300
-- (audit) a server-wide budget for uncached catalog lookups (the 1.5 s per-player gap still let a full server make
-- ~20 web calls a second), and failures are pruned once past their retry window (the table only ever grew)
local HAIR_BUDGET, HAIR_WINDOW = 40, 60
local HairLookups, HairWindowAt, HairPruneAt = 0, 0, 0
local function hairFailed(id)
	local now = os.clock()
	HairFailedAt[id] = now
	if now >= HairPruneAt then
		HairPruneAt = now + HAIR_RETRY
		for k, t in pairs(HairFailedAt) do
			if now - t >= HAIR_RETRY then
				HairFailedAt[k] = nil
			end
		end
	end
end
local function cacheHair(id, v, name)
	if HairCount >= HAIR_CACHE_MAX then -- bounded: start over rather than grow forever
		table.clear(HairCache)
		table.clear(HairNames)
		HairCount = 0
	end
	HairCount += 1
	HairCache[id], HairNames[id] = v, name
end
function Appearance.IsHairCached(id)
	return HairCache[id] ~= nil
end
function Appearance.IsKnownNotHair(id) -- true only when the id is definitely not a hair accessory
	return HairCache[id] == false
end
function Appearance.LoadHair(id)
	if HairCache[id] ~= nil then
		return HairCache[id], HairNames[id]
	end
	-- the owner's hairs (ReplicatedStorage.NHHairCatalog, AssetId attribute): straight from the place
	local Cat = ReplicatedStorage:FindFirstChild("NHHairCatalog")
	local Local = Cat and Cat:FindFirstChild("Hair_" .. tostring(id))
	if Local and Local:IsA("Accessory") then
		local acc = Local:Clone()
		acc.Name = NH_HAIR
		-- the catalog hairs are cut for a full-size head: bring them in a little (owner, 2026-11-01)
		local HAIR_FIT = 0.88
		local h = acc:FindFirstChild("Handle")
		if h then
			if h:IsA("MeshPart") then
				h.Size = h.Size * HAIR_FIT
			else
				local sm = h:FindFirstChildOfClass("SpecialMesh")
				if sm then sm.Scale = sm.Scale * HAIR_FIT end
				h.Size = h.Size * HAIR_FIT
			end
			for _, at in ipairs(h:GetChildren()) do
				if at:IsA("Attachment") and not at:IsA("Bone") then at.Position = at.Position * HAIR_FIT end
			end
			-- rigged hairs: bones don't follow Size, so bring their offsets in too (keeps the skin on the mesh)
			for _, bn in ipairs(h:GetDescendants()) do
				if bn:IsA("Bone") then bn.Position = bn.Position * HAIR_FIT end
			end
		end
		for _, jn in ipairs(acc:GetDescendants()) do
			if jn:IsA("JointInstance") or jn:IsA("WeldConstraint") then
				jn:Destroy()
			end
		end
		cacheHair(id, acc, Local:GetAttribute("DisplayName") or Local.Name)
		return HairCache[id], HairNames[id]
	end
	if HairFailedAt[id] and os.clock() - HairFailedAt[id] < HAIR_RETRY then
		return false, "Couldn't load that hair right now (try again soon)"
	end
	local now = os.clock()
	if now - HairWindowAt >= HAIR_WINDOW then
		HairWindowAt, HairLookups = now, 0
	end
	if HairLookups >= HAIR_BUDGET then
		return false, "The catalog is busy right now (try again in a minute)" -- (audit) budget spent: not cached as a failure
	end
	HairLookups += 1
	local MPS = game:GetService("MarketplaceService")
	local ok, info = pcall(MPS.GetProductInfo, MPS, id, Enum.InfoType.Asset)
	if not ok or type(info) ~= "table" then
		hairFailed(id)
		return false, "Couldn't look up that id (try again)"
	end
	if HairCache[id] ~= nil then -- another caller finished while we waited
		return HairCache[id], HairNames[id]
	end
	if info.AssetTypeId ~= Enum.AssetType.HairAccessory.Value then
		cacheHair(id, false, "That id isn't a hair accessory")
		return false, HairNames[id]
	end
	local desc = Instance.new("HumanoidDescription")
	desc.HairAccessory = tostring(id)
	local ok2, model = pcall(Players.CreateHumanoidModelFromDescription, Players, desc, Enum.HumanoidRigType.R6)
	local acc = ok2 and model and model:FindFirstChildOfClass("Accessory")
	if acc then
		acc = acc:Clone()
		acc.Name = NH_HAIR
		-- drop the weld to the throwaway model: cloned it points at nothing, and on the client
		-- AddAccessory keeps it instead of making its own, so the hair fell out of the world
		for _, j in ipairs(acc:GetDescendants()) do
			if j:IsA("JointInstance") or j:IsA("WeldConstraint") then
				j:Destroy()
			end
		end
		cacheHair(id, acc, info.Name)
		HairFailedAt[id] = nil
	else
		if model then
			model:Destroy()
		end
		hairFailed(id) -- (audit) pruned like the lookup failures
		return false, "That hair couldn't be loaded"
	end
	if model then
		model:Destroy()
	end
	return acc, info.Name
end

local function hideAvatarHair(character)
	local hidden = HairStashes[character]
	for _, d in ipairs(character:GetChildren()) do
		if d:IsA("Accessory") and d.Name ~= NH_HAIR and d.AccessoryType == Enum.AccessoryType.Hair then
			if not hidden then
				hidden = Instance.new("Folder")
				hidden.Name = character.Name
				hidden.Parent = stashRoot("NHHairStash")
				HairStashes[character] = hidden
				character.Destroying:Connect(function()
					hidden:Destroy()
				end)
			end
			d.Parent = hidden
		end
	end
end

local function showAvatarHair(character)
	local hidden = HairStashes[character]
	if not hidden then
		return
	end
	HairStashes[character] = nil
	for _, d in ipairs(hidden:GetChildren()) do
		d.Parent = character
	end
	hidden:Destroy()
end

-- drop a character's stashed avatar clothes / hair (ServerStorage) when it's gone
local function forgetCharacter(character)
	local st = Stashes[character]
	if st then
		Stashes[character] = nil
		st.folder:Destroy()
	end
	local hidden = HairStashes[character]
	if hidden then
		HairStashes[character] = nil
		hidden:Destroy()
	end
end
Appearance.ForgetCharacter = forgetCharacter

local function wearCatalogHair(character, data)
	local acc = Appearance.LoadHair(data.HairId)
	if not acc then
		return false
	end
	local hum = character:FindFirstChildOfClass("Humanoid")
	if not hum then
		return false
	end
	local a = acc:Clone()
	-- fitted for a player's head: scale it to this head (players: x1)
	local k = headScale(character:FindFirstChild("Head"))
	local ah = a:FindFirstChild("Handle")
	if k ~= 1 and ah and ah:IsA("BasePart") then
		local sm = ah:FindFirstChildOfClass("SpecialMesh")
		if sm then sm.Scale = sm.Scale * k end
		ah.Size = ah.Size * k
		for _, at in ipairs(ah:GetDescendants()) do
			if at:IsA("Attachment") then at.Position = at.Position * k end -- (Bones too: rigged hairs keep their skin on the mesh)
		end
	end
	if data.TintHair then
		local c = Appearance.HairColor(data)
		local handle = a:FindFirstChild("Handle")
		local mesh = handle and handle:FindFirstChildOfClass("SpecialMesh")
		if mesh then
			mesh.VertexColor = Vector3.new(c.R, c.G, c.B) * 1.6
		elseif handle and handle:IsA("MeshPart") then
			handle.TextureID = ""
			handle.Color = c
		end
	end
	local wantSize = ah and ah.Size
	hum:AddAccessory(a)
	-- AddAccessory sometimes rescales a new accessory by the model's scale (it did on the ScaleTo(0.9) NPC rig, not on
	-- the player's character), which shrank every NPC's hair a second time so it sat small and high (owner,
	-- 2026-11-03). Put it back to the size we meant and weld it again from the attachments (below).
	if wantSize and ah and ah.Parent and math.abs(ah.Size.X - wantSize.X) > 0.005 then
		local f = wantSize.X / ah.Size.X
		local sm = ah:FindFirstChildOfClass("SpecialMesh")
		if sm then sm.Scale = sm.Scale * f end
		ah.Size = wantSize
		for _, at in ipairs(ah:GetDescendants()) do
			if at:IsA("Attachment") then at.Position = at.Position * f end
		end
		local w = ah:FindFirstChild("AccessoryWeld")
		if w then w:Destroy() end
	end
	-- On the client (menu plinths, previews) AddAccessory doesn't weld: do it ourselves from the
	-- matching attachments, or the hair falls out of the world.
	local handle = a:FindFirstChild("Handle")
	if handle and handle:IsA("BasePart") and not handle:FindFirstChild("AccessoryWeld") then
		for _, hAtt in ipairs(handle:GetChildren()) do
			if hAtt:IsA("Attachment") then
				local cAtt
				for _, p in ipairs(character:GetChildren()) do
					local c = p:IsA("BasePart") and p:FindFirstChild(hAtt.Name)
					if c and c:IsA("Attachment") then
						cAtt = c
						break
					end
				end
				if cAtt then
					handle.CFrame = cAtt.WorldCFrame * hAtt.CFrame:Inverse()
					local w = Instance.new("Weld")
					w.Name = "AccessoryWeld"
					w.Part0, w.Part1 = handle, cAtt.Parent
					w.C0, w.C1 = hAtt.CFrame, cAtt.CFrame
					w.Parent = handle
					break
				end
			end
		end
	end
	return true
end

-- Painted eyes: hide the avatar's own face decals (remembered, restored for "Roblox face").
local EYES_IRIS, EYES_MAIN, FACE_BROWS, FACE_MOUTH, EYES_VEINS = "NHEyesIris", "NHEyesMain", "NHBrows", "NHMouth", "NHEyesVeins"
local FACE_MARKS, FACE_FORM = "NHMarks", "NHFormFace" -- under the eyes: race marks, the transformed face
function Appearance.EyeLayers(data, character)
	local form = character and Appearance.FormOf(character)
	local style = Appearance.Eyes[data.Eyes]
	local shape = style and style.Shape
	if not shape and form and form.Key then
		shape = EyeArt.Shapes[1].Id -- transformations still show on a "Roblox face" student
	end
	if not shape then
		return nil
	end
	local key = form and form.Key or "base"
	if form and form.Stage2 and character:GetAttribute("TransformationStage") == 2 then
		key = form.Stage2
	end
	local raceTint = nil
	if not form and data.RaceEyes and character then -- bloodline eyes: your race's eyes, untransformed
		local race = Appearance.RaceOf(character)
		local rf = race and Appearance.Forms[race]
		if rf and rf.Key then
			key, raceTint = rf.Key, rf.Tint
		elseif race == "Priest" then
			raceTint = Appearance.PriestIris
		end
	end
	local art = EyeArt.Get(shape, data.EyeSet == 2 and "f" or "m", key)
	if not art then
		return nil
	end
	local tint = (form and form.Tint) or raceTint or (data.LookStyle == "Nightborn" and Appearance.NightbornIris) or Appearance.EyeColor(data)
	return art, tint, shape, form and form.Key
end

-- The painted face. On a classic head (a cylinder) it is drawn as SurfaceGuis on FACE_STRIPS thin
-- invisible strips that wrap the head front, each showing its slice of the 1024px art (ImageRect), so it
-- sits on the face like a decal but renders at full resolution at every graphics level (Decals get
-- down-sampled on lower quality settings). Other heads (MeshPart / dynamic heads) fall back to Decals.
-- CharacterPreview turns the strips back into Decals for its ViewportFrame.
local FACE_PLATE, FACE_GUI = "NHFacePlate", "NHFace"
local FACE_COVER = 0.84   -- face art width, as a fraction of the visible head width
local FACE_STRIPS = 12    -- strips around the curve (each spans ~8 degrees: no visible facets)
local FACE_LIFT = 0.006   -- studs off the skin (just enough to never z-fight)

local function classicHead(head)
	local mesh = head:FindFirstChildOfClass("SpecialMesh")
	if mesh and mesh.MeshType == Enum.MeshType.Head then
		-- The classic head mesh's visible radius is 0.48 of its scaled width (not 0.5), so the art is sized
		-- to that visible width and the strips sit on the real skin. Measured on 0.9-scale R6 heads.
		local d = math.min(head.Size.Y, head.Size.Z)
		local R = d * mesh.Scale.X * 0.48
		return d * mesh.Scale.Y * 0.96, R -- visible width basis, cylinder radius
	end
	return nil
end

local function faceShell(head)
	local base, R = classicHead(head)
	if not base then
		return nil
	end
	local W = base * FACE_COVER
	local shell = head:FindFirstChild(FACE_PLATE)
	if shell and shell:IsA("Folder") and math.abs((shell:GetAttribute("W") or 0) - W) < 1e-4
		and math.abs((shell:GetAttribute("R") or 0) - R) < 1e-4 then
		return shell
	end
	if shell then
		shell:Destroy()
	end
	shell = Instance.new("Folder")
	shell.Name = FACE_PLATE
	shell:SetAttribute("W", W)
	shell:SetAttribute("R", R)
	local r = R + FACE_LIFT
	local span = W / R
	local step = span / FACE_STRIPS
	local chord = 2 * r * math.sin(step / 2)
	local inset = r * math.cos(step / 2) -- each flat strip is a chord: its edges touch radius r, never poke past it
	for i = 0, FACE_STRIPS - 1 do
		local theta = ((i + 0.5) / FACE_STRIPS - 0.5) * span -- image left (u = 0) sits on the head's +X side
		local p = Instance.new("Part")
		p.Name = "Strip" .. (i + 1)
		p.Transparency = 1
		p.CanCollide, p.CanQuery, p.CanTouch, p.Massless = false, false, false, true
		p.CastShadow = false
		p.Size = Vector3.new(chord, W, 0.01)
		p.CFrame = head.CFrame * CFrame.Angles(0, theta, 0) * CFrame.new(0, 0, -inset)
		local w = Instance.new("WeldConstraint")
		w.Part0, w.Part1 = head, p
		w.Parent = p
		local sg = Instance.new("SurfaceGui")
		sg.Name = FACE_GUI
		sg.Face = Enum.NormalId.Front
		sg.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
		sg.PixelsPerStud = 1024 / W
		sg.LightInfluence = 1
		sg.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
		sg:SetAttribute("Slice", i)
		sg.Parent = p
		p.Parent = shell
	end
	shell.Parent = head
	return shell
end

local function applyEyes(head, data, character)
	-- clear the old face (decal faces from earlier builds, and the strip images)
	for _, n in ipairs({ EYES_IRIS, EYES_MAIN, FACE_BROWS, FACE_MOUTH, EYES_VEINS, FACE_MARKS, FACE_FORM }) do
		local d = head:FindFirstChild(n)
		if d then
			d:Destroy()
		end
	end
	local art, tint, shape, formName = Appearance.EyeLayers(data, character)
	for _, d in ipairs(head:GetChildren()) do
		if d:IsA("Decal") and d.Face == Enum.NormalId.Front then
			if art then
				if d:GetAttribute("NHFaceT") == nil then
					d:SetAttribute("NHFaceT", d.Transparency)
				end
				d.Transparency = 1
			elseif d:GetAttribute("NHFaceT") ~= nil then
				d.Transparency = d:GetAttribute("NHFaceT")
				d:SetAttribute("NHFaceT", nil)
			end
		end
	end
	if not art then
		local plate = head:FindFirstChild(FACE_PLATE)
		if plate then
			plate:Destroy()
		end
		return false
	end
	-- the face layers, bottom to top: { name, texture, z, colour }
	local layers = {}
	local form = character and Appearance.FormOf(character)
	local race = character and Appearance.RaceOf(character)
	local mark = Appearance.Marks[data.Marks or 1]
	local markTex = mark and mark.Style and Appearance.RaceAllows(mark, race) and EyeArt.Mark and EyeArt.Mark(mark.Style)
	if markTex then
		table.insert(layers, { FACE_MARKS, markTex, 1 })
	end
	if form and form.Key and EyeArt.FormFace then -- the menacing transformed face: sockets, glow, tears, creases
		local fkey = (form.Stage2 and character:GetAttribute("TransformationStage") == 2) and form.Stage2 or form.Key
		local formTex = EyeArt.FormFace(fkey)
		if formTex then
			table.insert(layers, { FACE_FORM, formTex, 1 })
		end
	end
	if art.Veins and form and form.Veins then
		table.insert(layers, { EYES_VEINS, art.Veins, 1, head.Color:Lerp(form.Veins, 0.5) }) -- veins take on the skin tone
	end
	table.insert(layers, { EYES_IRIS, art.Iris, 2, tint })
	table.insert(layers, { EYES_MAIN, art.Main, 3 })
	local brow = Appearance.Brows[data.Brows]
	local browTex = brow and brow.Style and EyeArt.Brow(brow.Style, shape)
	if browTex then
		table.insert(layers, { FACE_BROWS, browTex, 4, Appearance.BrowColor(data) })
	end
	local mouthTex = formName and EyeArt.FormMouth(formName)
	if not mouthTex then
		local mo = Appearance.Mouths[data.Mouth]
		if mo and not Appearance.RaceAllows(mo, race) then
			mo = Appearance.Mouths[2] -- a race mouth on someone not of that race: plain mouth
		end
		mouthTex = mo and mo.Style and EyeArt.Mouth(mo.Style, data.Lips)
	end
	if mouthTex then
		table.insert(layers, { FACE_MOUTH, mouthTex, 4 })
	end

	local shell = faceShell(head)
	if shell then
		local slice = 1024 / FACE_STRIPS
		for _, sg in ipairs(shell:GetDescendants()) do
			if sg:IsA("SurfaceGui") then
				sg:ClearAllChildren()
				local i = sg:GetAttribute("Slice") or 0
				for _, L in ipairs(layers) do
					local im = Instance.new("ImageLabel")
					im.Name = L[1]
					im.BackgroundTransparency = 1
					im.Size = UDim2.fromScale(1, 1)
					im.Image = L[2]
					im.ImageRectOffset = Vector2.new(i * slice, 0)
					im.ImageRectSize = Vector2.new(slice, 1024)
					im.ImageColor3 = L[4] or Color3.new(1, 1, 1)
					im.ZIndex = L[3]
					im.Parent = sg
				end
			end
		end
	else
		local plate = head:FindFirstChild(FACE_PLATE)
		if plate then
			plate:Destroy()
		end
		for _, L in ipairs(layers) do -- non-classic head: plain decals
			local d = Instance.new("Decal")
			d.Name = L[1]
			d.Face = Enum.NormalId.Front
			d.Texture = L[2]
			d.ZIndex = L[3]
			d.Color3 = L[4] or Color3.new(1, 1, 1)
			d.Parent = head
		end
	end
	return true
end
Appearance.ApplyEyes = applyEyes

-- Late avatar loading: when a character is spawned by the main menu / save slots, Roblox can finish
-- adding the avatar's clothes, accessories, BodyColors or face AFTER the look was applied. Keep the
-- look in charge: tuck late avatar clothing into the stash, keep our skin colours, hide a late face.
local Guards = setmetatable({}, { __mode = "k" }) -- [character] = { useAvatar, hairId, skin, painted }
-- Race skin palettes (Lineage.Palette(raceId) -> {Color3} or nil). Vampire and Ghoul skins always land
-- on one of their race's tones, in both outfit modes. The saved choice is kept as-is, so a race change
-- (e.g. Vampire -> Human) frees the skin again; the clamp is applied here, on the server, every time.
function Appearance.RaceOf(character)
	if not character then
		return nil
	end
	local player = Players:GetPlayerFromCharacter(character)
	return (player and player:GetAttribute("Race")) or character:GetAttribute("Race")
end

function Appearance.RacePalette(race)
	if not race then
		return nil
	end
	local ok, Lineage = pcall(require, ReplicatedStorage:FindFirstChild("Lineage"))
	if ok and type(Lineage) == "table" and Lineage.Palette then
		local ok2, pal = pcall(Lineage.Palette, race)
		if ok2 and type(pal) == "table" and #pal > 0 then
			return pal
		end
	end
	return nil
end

function Appearance.NearestColor(palette, c)
	local best, bestD = palette[1], math.huge
	for _, p in ipairs(palette) do
		local d = (p.R - c.R) ^ 2 + (p.G - c.G) ^ 2 + (p.B - c.B) ^ 2
		if d < bestD then
			best, bestD = p, d
		end
	end
	return best
end

-- "Use my Roblox outfit" + a palette race: move the avatar's own body colours onto the palette,
-- remembering the originals on the BodyColors (attributes NHOrig_*) so they come back without one.
local function clampAvatarSkin(character, palette)
	local bc = character:FindFirstChildOfClass("BodyColors")
	if not bc then
		if not palette then
			return
		end
		bc = bodyColors(character)
	end
	for _, n in ipairs(BODY_PROPS) do
		local orig = bc:GetAttribute("NHOrig_" .. n)
		if palette then
			if orig == nil then
				orig = bc[n]
				bc:SetAttribute("NHOrig_" .. n, orig)
			end
			bc[n] = Appearance.NearestColor(palette, orig)
		elseif orig ~= nil then
			bc[n] = orig
			bc:SetAttribute("NHOrig_" .. n, nil)
		end
	end
end

local FACE_LAYER_NAMES = { [EYES_IRIS] = true, [EYES_MAIN] = true, [EYES_VEINS] = true, [FACE_BROWS] = true, [FACE_MOUTH] = true,
	[FACE_MARKS] = true, [FACE_FORM] = true }
local ApplyTokens = setmetatable({}, { __mode = "k" }) -- [character] = latest ApplyTo call

local function guardLate(character, g)
	Guards[character] = g
	if character:GetAttribute("NHLookGuard") then
		return
	end
	character:SetAttribute("NHLookGuard", true)
	local function handle(d)
		local look = Guards[character]
		if not look or d.Parent ~= character then
			return
		end
		if d.Name == UNIFORM_SHIRT or d.Name == UNIFORM_PANTS or d.Name == NH_HAIR then
			return
		end
		if d:IsA("BodyColors") and look.avatarSkinPalette then
			for _, n in ipairs(BODY_PROPS) do
				d:SetAttribute("NHOrig_" .. n, d[n])
				d[n] = Appearance.NearestColor(look.avatarSkinPalette, d[n])
			end
		end
		if not look.useAvatar then
			local st = Stashes[character]
			if st then
				for _, cls in ipairs(AVATAR_CLASSES) do
					if d:IsA(cls) and not (look.clothesOnly and cls == "Accessory") then
						d.Parent = st.folder
						return
					end
				end
			end
			if d:IsA("BodyColors") and look.keepSkin then
				for _, n in ipairs(BODY_PROPS) do
					st = Stashes[character]
					if st then
						st.colors[n] = d[n] -- remember the avatar's own colours for when you switch back
					end
					d[n] = look.skin
				end
			end
		elseif look.hairId > 0 and d:IsA("Accessory") and d.AccessoryType == Enum.AccessoryType.Hair then
			hideAvatarHair(character)
		end
	end
	character.ChildAdded:Connect(function(d)
		task.defer(handle, d)
	end)
	-- Roblox's avatar loader can also just EDIT the existing BodyColors after the look is applied:
	-- keep the uniform skin, or the race palette in "use my Roblox outfit" mode.
	local watched = setmetatable({}, { __mode = "k" })
	local function watchColors(bc)
		if watched[bc] then
			return
		end
		watched[bc] = true
		bc.Changed:Connect(function(prop)
			local look = Guards[character]
			if not look or not table.find(BODY_PROPS, prop) or bc.Parent ~= character then
				return
			end
			local v = bc[prop]
			if look.avatarSkinPalette then
				local near = Appearance.NearestColor(look.avatarSkinPalette, v)
				if near ~= v then
					bc:SetAttribute("NHOrig_" .. prop, v)
					bc[prop] = near
				end
			elseif look.keepSkin and not look.useAvatar and v ~= look.skin then
				local st = Stashes[character]
				if st then
					st.colors[prop] = v -- the avatar's own colour, for when you switch back
				end
				bc[prop] = look.skin
			end
		end)
	end
	for _, d in ipairs(character:GetChildren()) do
		if d:IsA("BodyColors") then
			watchColors(d)
		end
	end
	character.ChildAdded:Connect(function(d)
		if d:IsA("BodyColors") then
			watchColors(d)
		end
	end)
	-- Roblox's avatar loader removes existing Shirt/Pants when it applies the avatar's own. If it
	-- takes the uniform off while the uniform look is active, put it straight back (no naked gap).
	character.ChildRemoved:Connect(function(d)
		if d.Name ~= UNIFORM_SHIRT and d.Name ~= UNIFORM_PANTS then
			return
		end
		task.defer(function()
			local look = Guards[character]
			if not look or look.useAvatar or not character.Parent then
				return
			end
			if not character:FindFirstChild(UNIFORM_SHIRT) and look.shirt then
				local sh = Instance.new("Shirt")
				sh.Name = UNIFORM_SHIRT
				sh.ShirtTemplate = look.shirt
				sh.Parent = character
			end
			if not character:FindFirstChild(UNIFORM_PANTS) and look.pants then
				local pa = Instance.new("Pants")
				pa.Name = UNIFORM_PANTS
				pa.PantsTemplate = look.pants
				pa.Parent = character
			end
		end)
	end)
	local head = character:FindFirstChild("Head")
	if head then
		head.ChildAdded:Connect(function(d)
			task.defer(function()
				local look = Guards[character]
				if look and look.painted and d:IsA("Decal") and d.Face == Enum.NormalId.Front and d.Parent == head
					and not FACE_LAYER_NAMES[d.Name] then
					if d:GetAttribute("NHFaceT") == nil then
						d:SetAttribute("NHFaceT", d.Transparency)
					end
					d.Transparency = 1
				end
			end)
		end)
	end
end

-- Put a cape on (index into Appearance.Capes; 1 = none). Scaled to the body, its neck bone on the top of the back.
function Appearance.WearCape(character, index)
	local old = character:FindFirstChild("NHCape")
	if old then
		old:Destroy()
	end
	local def = Appearance.Capes[index or 1]
	if def and def.Admin then -- staff-only (a look saved before staff was taken away doesn't show it); previews have no player
		local owner = game:GetService("Players"):GetPlayerFromCharacter(character)
		if owner and not Appearance.IsStaff(owner) then
			return
		end
	end
	local torso = character:FindFirstChild("Torso")
	local store = ReplicatedStorage:FindFirstChild("NHCapes")
	local tpl = def and def.Model and store and store:FindFirstChild(def.Model)
	if not (tpl and torso) then
		return
	end
	local cape = tpl:Clone()
	cape.Name = "NHCape"
	cape:SetAttribute("CapeId", def.Id)
	local body = cape.PrimaryPart
	local k = torso.Size.Y / 2
	for _, d in ipairs(cape:GetDescendants()) do
		if d:IsA("BasePart") then
			d.Size = d.Size * k
			d.Anchored, d.CanCollide, d.CanQuery, d.CanTouch, d.Massless = false, false, false, false, true
		elseif d:IsA("Bone") then
			d.Position = d.Position * k
		elseif d:IsA("Motor6D") then
			d.C0 = d.C0 - d.C0.Position + d.C0.Position * k
			d.C1 = d.C1 - d.C1.Position + d.C1.Position * k
		end
	end
	local root = nil
	for _, b in ipairs(body:GetChildren()) do
		if b:IsA("Bone") then
			root = b
			break
		end
	end
	-- owner-fitted (template attribute NH_TorsoFit: the cape body's CFrame on a 2x2x1 R6 torso), scaled to this torso
	local fit = tpl:GetAttribute("NH_TorsoFit")
	if typeof(fit) == "CFrame" then
		body.CFrame = torso.CFrame * (fit - fit.Position + fit.Position * k)
	else
		local anchorAt = torso.CFrame * CFrame.new(0, torso.Size.Y / 2 - 0.1, torso.Size.Z / 4)
		body.CFrame = anchorAt * CFrame.new(-(root and root.Position or Vector3.zero))
	end
	local weld = Instance.new("WeldConstraint")
	weld.Part0, weld.Part1 = torso, body
	weld.Parent = body
	cape.Parent = character
end

--------------------------------------------------------------------------
-- NPC dress code (owner, 2026-11-03): NPCs in school wear only school clothes; people outside the school wear
-- civilian clothes. Players are never touched. Where an NPC stands when its look goes on decides it: the school is
-- its building and grounds (every region but the factions' turf); the turf (Config.Regions kind Turf: the Back Lot,
-- the West Edge) is outside. Scheduled students are always in school clothes, and the model attribute
-- NHDress = "School" | "Civilian" forces either. Anything that breaks the code is swapped for an everyday item that's
-- allowed and suits the body (picked the same way every time for the same NPC); PE kit, cheer and formalwear stay
-- only when an NPC's own look asks for them.
--------------------------------------------------------------------------
Appearance.SchoolTops = {
	["red-vest"] = true, ["red-shirt"] = true, ["black-vest"] = true, ["black-shirt"] = true, ["navy-vest"] = true,
	["forest-vest"] = true, ["charcoal-vest"] = true, ["vigil-vest"] = true, ["crimson-court-vest"] = true,
	["navy-polo"] = true, ["forest-polo"] = true, ["ivory-polo"] = true, ["crimson-polo"] = true, ["delinquent-polo"] = true,
	["black-blazer"] = true, ["charcoal-cardigan"] = true, ["varsity-jacket"] = true, ["gym-pe-shirt"] = true,
	["sailor-uniform"] = true, ["bolero-pinafore"] = true, ["cheer-uniform"] = true,
}
Appearance.SchoolBottoms = {
	["uniform-trousers"] = true, ["charcoal-slacks"] = true, ["khaki-trousers"] = true, ["khaki-shorts"] = true,
	["pleated-tartan-skirt"] = true, ["striped-joggers"] = true, ["sailor-skirt"] = true, ["chapel-skirt"] = true,
	["pinafore-skirt"] = true, ["cheer-skirt"] = true,
}
local OUTSIDE_KINDS = { Turf = true }
-- what a swap picks from (everyday wear; the rest is allowed but never chosen for an NPC)
local SWAP = {
	School = {
		Tops = { "red-vest", "black-vest", "navy-vest", "forest-vest", "charcoal-vest", "red-shirt", "black-shirt", "navy-polo", "forest-polo", "ivory-polo" },
		FemaleTops = { "sailor-uniform", "bolero-pinafore" },
		Bottoms = { "uniform-trousers", "charcoal-slacks", "khaki-trousers" },
		FemaleBottoms = { "pleated-tartan-skirt", "sailor-skirt", "pinafore-skirt", "chapel-skirt" },
	},
	Civilian = {
		Tops = { "leather-jacket", "open-flannel", "blood-moon-hoodie", "the-hollow-band-tee" },
		FemaleTops = { "cable-knit" },
		Bottoms = { "dark-indigo-jeans", "black-jeans", "ripped-jeans", "cargo-boots", "black-jeans-boots" },
		FemaleBottoms = { "plaid-mini", "black-skirt-fishnets" },
	},
}

-- "School" or "Civilian" for an NPC, from where it stands
function Appearance.DressFor(character)
	local forced = character:GetAttribute("NHDress")
	if forced == "School" or forced == "Civilian" then
		return forced
	end
	if character:GetAttribute("NHScheduled") then
		return "School"
	end
	local ok, pos = pcall(function() return character:GetPivot().Position end)
	local folder = workspace:FindFirstChild("Regions")
	local okC, cfg = pcall(require, ReplicatedStorage:WaitForChild("Config"):WaitForChild("Regions"))
	if not (ok and folder and okC) then
		return "School"
	end
	local best, bestP = nil, -math.huge
	for _, b in ipairs(folder:GetChildren()) do
		local def = b:IsA("BasePart") and cfg.Defs[b:GetAttribute("RegionId") or ""]
		if def then
			local l = b.CFrame:PointToObjectSpace(pos)
			local h = b.Size / 2
			if math.abs(l.X) <= h.X and math.abs(l.Y) <= h.Y + 4 and math.abs(l.Z) <= h.Z and (def.Priority or 0) > bestP then
				best, bestP = def, def.Priority or 0
			end
		end
	end
	return if best and OUTSIDE_KINDS[best.Kind] then "Civilian" else "School"
end

local function dressPick(list, ids, femaleIds, female, seed)
	local pool = {}
	for _, id in ipairs(ids) do table.insert(pool, id) end
	if female then for _, id in ipairs(femaleIds) do table.insert(pool, id) end end
	if #pool == 0 then
		return nil
	end
	return Appearance.IndexOf(list, pool[(seed % #pool) + 1])
end

local NPC_FOLDERS = { Live = true, NHSchedule = true, NHAmbient = true, NHConcession = true }
function Appearance.IsNpc(character)
	if Players:GetPlayerFromCharacter(character) or not character:IsDescendantOf(workspace) then
		return false
	end
	local menu = workspace:FindFirstChild("MenuScene")
	if menu and character:IsDescendantOf(menu) then
		return false
	end
	return character.Parent ~= nil and NPC_FOLDERS[character.Parent.Name] == true
end

function Appearance.DressCode(character, data)
	local kind = Appearance.DressFor(character)
	local want = kind == "School"
	local set = SWAP[kind]
	local female = Appearance.IsFemale(data)
	local seed = 0
	for i = 1, #character.Name do
		seed = (seed * 31 + string.byte(character.Name, i)) % 1000003
	end
	local top = Appearance.Uniforms[data.Uniform]
	if top and (Appearance.SchoolTops[top.Id] == true) ~= want then
		data.Uniform = dressPick(Appearance.Uniforms, set.Tops, set.FemaleTops, female, seed) or data.Uniform
	end
	local bottom = Appearance.BottomsList[data.Bottoms]
	if bottom and (Appearance.SchoolBottoms[bottom.Id] == true) ~= want then
		data.Bottoms = dressPick(Appearance.BottomsList, set.Bottoms, set.FemaleBottoms, female, seed + 7) or data.Bottoms
	end
	return data
end

function Appearance.ApplyTo(character, data)
	data = Appearance.Sanitize(data)
	if Appearance.IsNpc(character) then
		data = Appearance.DressCode(character, data) -- NPCs only (never players, previews or the menu's posed students)
	end
	local head = character:FindFirstChild("Head")
	local torso = character:FindFirstChild("Torso") or character:FindFirstChild("UpperTorso")
	if not (head and torso) then
		return false
	end
	local token = (ApplyTokens[character] or 0) + 1
	ApplyTokens[character] = token
	local hairAcc = data.HairId > 0 and Appearance.LoadHair(data.HairId) or nil -- may yield
	if ApplyTokens[character] ~= token or not character.Parent then
		return false -- a newer apply started while we waited; it wins
	end
	-- nothing below yields, so two applies can never interleave
	for _, c in ipairs(character:GetChildren()) do
		if c.Name == LOOK or c.Name == NH_HAIR then
			c:Destroy()
		end
	end
	showAvatarHair(character)
	-- body shape: the Female body's meshes replace any CharacterMesh on those parts (avatar packages included);
	-- Standard removes ours (avatar meshes return on respawn)
	local body = Appearance.Bodies[data.Body] or Appearance.Bodies[1]
	local bodyMeshes = body.Meshes or (body.TorsoMesh and { Torso = body.TorsoMesh }) or nil
	if data.Areas ~= "" then -- (training 1.81) each area's meshes from its own body
		local areas = Appearance.AreaBodies(data)
		local mixed = {}
		for area, parts in pairs(Appearance.AreaParts) do
			local ab = Appearance.Bodies[areas[area]] or body
			local m = ab.Meshes or (ab.TorsoMesh and { Torso = ab.TorsoMesh }) or {}
			for _, partName in ipairs(parts) do
				mixed[partName] = m[partName]
			end
		end
		bodyMeshes = next(mixed) and mixed or nil
	end
	for _, c in ipairs(character:GetChildren()) do
		if c:IsA("CharacterMesh") and (c.Name == "NHBodyMesh" or (bodyMeshes and bodyMeshes[c.BodyPart.Name])) then
			c:Destroy()
		end
	end
	if bodyMeshes and torso.Name == "Torso" then
		for partName, meshId in pairs(bodyMeshes) do
			local cm = Instance.new("CharacterMesh")
			cm.Name = "NHBodyMesh"
			cm.BodyPart = Enum.BodyPart[partName]
			cm.MeshId = meshId
			cm.Parent = character
		end
	end
	Appearance.WearCape(character, data.Cape)
	do -- 3D accessories (UI.AccessoryWear): each piece on its R6 part, fitted to this body type
		local wm = script.Parent:FindFirstChild("AccessoryWear")
		local okW, AccWear = pcall(require, wm)
		if wm and okW then
			local okR, err = pcall(AccWear.Wear, character, data.Acc, (Appearance.Bodies[data.Body] or Appearance.Bodies[1]).Id, data.HairId)
			if not okR then
				warn("[Appearance] accessories: " .. tostring(err))
			end
		end
	end
	local folder = Instance.new("Folder")
	folder.Name = LOOK

	local palette = Appearance.RacePalette(Appearance.RaceOf(character))
	local skin = Appearance.SkinColor(data)
	if palette then
		skin = Appearance.NearestColor(palette, skin) -- Vampire / Ghoul: always one of the race's tones
	elseif data.LookStyle == "Nightborn" then
		skin = skin:Lerp(rgb(222, 224, 232), 0.45)
	end
	local catalogHair = hairAcc and true or false -- a failed lookup keeps your other hair (no bald spawn)

	local formNow = Appearance.FormOf(character)
	local formOutfit = formNow and Appearance.FormOutfit(formNow, data)
	local raceKit = Appearance.RaceUniforms[Appearance.RaceOf(character) or ""]
	local baseShirt = (raceKit and raceKit.Shirts[data.Uniform]) or Appearance.Uniforms[data.Uniform].Shirt
	local basePants = (raceKit and data.Bottoms == 1 and raceKit.Pants) or Appearance.BottomsList[data.Bottoms].Template
	-- transformed in your own top and bottoms (UI.FormVariants) when both have a variant; else the form outfit
	if formNow and not data.UseAvatar then
		local vShirt, vPants = Appearance.FormVariant(formNow, baseShirt), Appearance.FormVariant(formNow, basePants)
		if vShirt and vPants then
			formOutfit = { Shirt = vShirt, Pants = vPants }
		end
	end
	local shirtTex = formOutfit and formOutfit.Shirt or baseShirt
	local pantsTex = formOutfit and formOutfit.Pants or basePants
	if data.UseAvatar and not formOutfit then
		restore(character)
		clampAvatarSkin(character, palette)
		if catalogHair then
			hideAvatarHair(character)
		end
	else
		local clothesOnly = data.UseAvatar -- transformed in your own outfit: swap clothes, keep accessories
		local st = Stashes[character]
		if st and st.clothesOnly ~= clothesOnly then
			restore(character)
		end
		clearUniform(character)
		stash(character, clothesOnly)
		if not data.UseAvatar then
			local bc = bodyColors(character)
			for _, n in ipairs(BODY_PROPS) do
				bc[n] = skin -- the clothing textures cover the body; skin shows at the hands and neck
			end
		else
			clampAvatarSkin(character, palette)
			if catalogHair then
				hideAvatarHair(character)
			end
		end
		local shirt = Instance.new("Shirt")
		shirt.Name = UNIFORM_SHIRT
		shirt.ShirtTemplate = shirtTex
		shirt.Parent = character
		local pants = Instance.new("Pants")
		pants.Name = UNIFORM_PANTS
		pants.PantsTemplate = pantsTex
		pants.Parent = character
		if not data.UseAvatar and not catalogHair and data.Hair < #Appearance.HairStyles then
			hair(folder, head, data.Hair, Appearance.HairColor(data))
		end
	end
	if catalogHair then
		wearCatalogHair(character, data)
	end

	-- look-style marks (shown in both modes)
	local V, C = Vector3.new, CFrame.new
	if data.LookStyle == "Chapel" then
		part(folder, "CrossV", V(0.08, 0.34, 0.05), rgb(235, 205, 120), C(0.46, 0.4, -0.48), torso, nil, Enum.Material.Metal)
		part(folder, "CrossH", V(0.24, 0.08, 0.05), rgb(235, 205, 120), C(0.46, 0.46, -0.48), torso, nil, Enum.Material.Metal)
	end
	local painted = applyEyes(head, data, character)
	if data.LookStyle == "Nightborn" and not painted then -- painted eyes get crimson irises instead
		part(folder, "EyeGlintL", V(0.14, 0.07, 0.02), rgb(220, 30, 50), C(-0.19, 0.08, -0.56), head, nil, Enum.Material.Neon)
		part(folder, "EyeGlintR", V(0.14, 0.07, 0.02), rgb(220, 30, 50), C(0.19, 0.08, -0.56), head, nil, Enum.Material.Neon)
	end
	folder.Parent = character
	character:SetAttribute("LookStyle", data.LookStyle) -- cosmetic; never race
	local dressed = (not data.UseAvatar) or formOutfit ~= nil
	guardLate(character, {
		useAvatar = not dressed, hairId = catalogHair and data.HairId or 0, skin = skin, painted = painted,
		keepSkin = not data.UseAvatar, clothesOnly = data.UseAvatar and formOutfit ~= nil,
		avatarSkinPalette = data.UseAvatar and palette or nil,
		shirt = dressed and shirtTex or nil, pants = dressed and pantsTex or nil,
	})
	return true
end

--------------------------------------------------------------------------
-- server: validate, save through ProfileService (Services.Player.Data), apply on spawn
--------------------------------------------------------------------------
local function sameLook(a, b)
	for k, v in pairs(a) do
		if b[k] ~= v then
			return false
		end
	end
	for k in pairs(b) do
		if a[k] == nil then
			return false
		end
	end
	return true
end

-- Is this player standing at a wardrobe station (any instance tagged NHWardrobe, within reach)?
-- AtTag(p, "NHBarber") is the same check for the barber.
Appearance.WardrobeReach = 14
function Appearance.AtWardrobe(p)
	if workspace:GetAttribute("NHAnywhereWardrobe") then return true end -- (Map preview) the Map has no stations: anywhere counts
	return Appearance.AtTag(p, "NHWardrobe")
end
-- which look fields each place may change outside the creator: outfit at a wardrobe, hair at the barber
Appearance.OutfitFields = { Uniform = true, Bottoms = true, Cape = true, Acc = true }
Appearance.HairFields = { Hair = true, HairColor = true, HairHex = true, HairId = true, TintHair = true }
function Appearance.AtTag(p, tag)
	local ch = p.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart")
	if not root then
		return false
	end
	for _, w in ipairs(game:GetService("CollectionService"):GetTagged(tag)) do
		local pos = if w:IsA("BasePart") then w.Position elseif w:IsA("Model") then w:GetPivot().Position else nil
		if pos and (pos - root.Position).Magnitude <= Appearance.WardrobeReach then
			return true
		end
	end
	return false
end

-- 2026-11-01 (owner): no "Use my Roblox outfit" and no Roblox face. Every look is the Nightmare High one.
do
	local rawSanitize = Appearance.Sanitize
	Appearance.Sanitize = function(data)
		local look = rawSanitize(data)
		look.UseAvatar = false
		local e = Appearance.Eyes[look.Eyes]
		if not e or e.Shape == nil then
			look.Eyes = 2
		end
		return look
	end
end

-- (height, 1.62) a look is built at today's size. Hair, marks and capes are placed in studs for the base body, so a
-- student scaled to their height (Services.Player.Height) is put back to Config.Heights.Base while the look is built,
-- then scaled back. Catalog hair is loaded first, so nothing yields while the body is at the base size.
-- NPC students (class schedules, ambient students) get a height too, fixed by their name (the Human range), so the
-- school doesn't look cloned. Their feet stay where they were placed.
local NPC_HEIGHT = { NHSchedule = true, NHAmbient = true }
do
	local rawApply = Appearance.ApplyTo
	Appearance.ApplyTo = function(character, data)
		local okH, Heights = pcall(require, ReplicatedStorage:WaitForChild("Config"):WaitForChild("Heights"))
		local base = okH and Heights.Base or 0.9
		local ok, now = pcall(function() return character:GetScale() end)
		local hum = character:FindFirstChildWhichIsA("Humanoid")
		local function scaleKeep(s)
			local ws, jp, jh = hum and hum.WalkSpeed, hum and hum.JumpPower, hum and hum.JumpHeight
			character:ScaleTo(s)
			if hum then hum.WalkSpeed, hum.JumpPower, hum.JumpHeight = ws, jp, jh end
		end
		local result
		-- (1.70.0) a height also stretches the torso, legs and arms: take that off while the look is built, too
		local st, sl, sa = 1, 1, 1
		if okH and Heights.StretchOf then st, sl, sa = Heights.StretchOf(character) end
		local stretched = math.abs(st - 1) > 1e-4 or math.abs(sl - 1) > 1e-4 or math.abs(sa - 1) > 1e-4
		if not ok or (math.abs(now - base) < 1e-3 and not stretched) then
			result = rawApply(character, data)
		else
			local look = Appearance.Sanitize(data)
			if look.HairId and look.HairId > 0 then
				pcall(Appearance.LoadHair, look.HairId) -- cached: the apply below won't wait for it
			end
			if stretched then Heights.SetStretch(character, 1, 1, 1) end
			scaleKeep(base)
			local okA, r = pcall(rawApply, character, data)
			if character.Parent then
				scaleKeep(now)
				if stretched then Heights.SetStretch(character, st, sl, sa) end
			end
			if not okA then
				error(r, 0)
			end
			result = r
		end
		if okH and RunService:IsServer() and character.Parent and NPC_HEIGHT[character.Parent.Name]
			and character:GetAttribute("NHHeight") == nil then
			-- seeded by the name and the look (class students are all called "Student", their looks differ)
			local key = character.Name
			local look = Appearance.Sanitize(data)
			local keys = {}
			for k in pairs(look) do
				table.insert(keys, tostring(k))
			end
			table.sort(keys)
			for _, k in ipairs(keys) do
				key ..= "|" .. k .. "=" .. tostring(look[k])
			end
			local seed = 7
			for i = 1, #key do
				seed = (seed * 131 + string.byte(key, i)) % 1000003
			end
			local scale = Heights.Scale(nil, (seed % 9973) / 9973)
			local function feetY()
				local cf, size = character:GetBoundingBox()
				return cf.Position.Y - size.Y / 2
			end
			pcall(function()
				local before = feetY()
				-- (1.70.0) even for thickness and the head, then the torso, legs and arms are stretched
				local w, kt, kl, ka = Heights.Proportions(scale)
				scaleKeep((Heights.Normal or 1) * w) -- Average is a standard R6 body
				Heights.SetStretch(character, kt, kl, ka)
				character:PivotTo(character:GetPivot() + Vector3.new(0, before - feetY(), 0))
				character:SetAttribute("NHHeight", scale)
			end)
		end
		return result
	end
end

function Appearance.StartServer()
	assert(RunService:IsServer(), "Appearance.StartServer must run on the server")
	if Appearance._started then
		return
	end
	Appearance._started = true
	local Data = require(game:GetService("ServerScriptService"):WaitForChild("Services"):WaitForChild("Player"):WaitForChild("Data"))
	local folder = ReplicatedStorage:FindFirstChild(Appearance.RemotesName) or Instance.new("Folder")
	folder.Name = Appearance.RemotesName
	local setRE = folder:FindFirstChild("Set") or Instance.new("RemoteEvent")
	setRE.Name = "Set"
	setRE.Parent = folder
	local checkRF = folder:FindFirstChild("CheckHair") or Instance.new("RemoteFunction")
	checkRF.Name = "CheckHair"
	checkRF.Parent = folder
	folder.Parent = ReplicatedStorage

	local function profileLook(p)
		local profile = Data.GetProfile(p)
		return profile and Appearance.Sanitize(profile.Appearance)
	end
	local function onCharacter(p, ch)
		-- wait for the Roblox avatar (LoadCharacterAppearance) and the profile
		local t0 = os.clock()
		while not p:HasAppearanceLoaded() and os.clock() - t0 < 6 and ch.Parent do
			task.wait(0.1)
		end
		while not Data.GetProfile(p) and os.clock() - t0 < 15 and p.Parent do
			task.wait(0.2)
		end
		local look = profileLook(p)
		if look and p.Character == ch then
			pcall(Appearance.ApplyTo, ch, look)
		end
		-- transformations swap the eyes live
		local function reEyes()
			local l = profileLook(p)
			if l and p.Character == ch then
				pcall(Appearance.ApplyTo, ch, l) -- outfit + eyes + mouth for the form
			end
		end
		ch:GetAttributeChangedSignal("Transformation"):Connect(reEyes)
		ch:GetAttributeChangedSignal("TransformationStage"):Connect(reEyes)
	end
	local function hook(p)
		p:GetAttributeChangedSignal("Race"):Connect(function()
			local look = profileLook(p)
			if look and p.Character then
				pcall(Appearance.ApplyTo, p.Character, look)
			end
		end)
		p.CharacterAppearanceLoaded:Connect(function(ch)
			task.defer(function()
				local look = profileLook(p)
				if look and p.Character == ch then
					pcall(Appearance.ApplyTo, ch, look)
				end
			end)
		end)
		p.CharacterAdded:Connect(function(ch)
			task.spawn(onCharacter, p, ch)
		end)
		p.CharacterRemoving:Connect(forgetCharacter)
		if p.Character then
			task.spawn(onCharacter, p, p.Character)
		end
	end
	Players.PlayerAdded:Connect(hook)
	for _, p in ipairs(Players:GetPlayers()) do
		hook(p)
	end
	-- save slots: a profile can load (or change) after the character exists
	-- one-time migration: a save that still uses list positions is rewritten with ids
	local function migrate(p)
		local profile = Data.GetProfile(p)
		local stored = profile and profile.Appearance
		if Appearance.IsLegacy(stored) then
			pcall(Data.UpdateState, p, { type = "SetAppearance", appearance = Appearance.Encode(stored) })
		end
	end
	for _, p in ipairs(Players:GetPlayers()) do
		task.spawn(migrate, p)
	end
	Data.ProfileLoaded:Connect(function(p)
		migrate(p)
		local look = profileLook(p)
		if look and p.Character then
			pcall(Appearance.ApplyTo, p.Character, look)
		end
	end)

	local last, lastCheck, lastLookup = {}, {}, {}
	setRE.OnServerEvent:Connect(function(p, data)
		local now = os.clock()
		if last[p] and now - last[p] < 0.2 then
			return -- rate limit
		end
		last[p] = now
		if not Data.GetProfile(p) then
			return
		end
		local look = Appearance.Sanitize(data)
		look.Created = true
		local saved = profileLook(p)
		-- the wardrobe is a place: changes only from a locker-room wardrobe (CollectionService tag NHWardrobe),
		-- the main-menu creator, or a student's very first look
		-- (Map preview) no main menu here, so the K wardrobe may change everything (gender, skin, eyes...) live
		if saved and saved.Created and p:GetAttribute("InMainMenu") ~= true and not workspace:GetAttribute("NHAnywhereWardrobe") then
			local atWardrobe, atBarber = Appearance.AtWardrobe(p), Appearance.AtTag(p, "NHBarber")
			for k, v in pairs(look) do
				if saved[k] ~= nil and v ~= saved[k] and k ~= "Created" then
					local ok = (Appearance.OutfitFields[k] and atWardrobe) or (Appearance.HairFields[k] and atBarber)
					if not ok then
						look[k] = saved[k] -- skin, eyes, body... are set in the creator; outfit and hair need the right place
					end
				end
			end
		end
		do -- body types (2026-11-10): a trained build comes only from training or the admin desk (Appearance.SetBuild).
			-- A client may only change gender (in the creator); the saved build and step carry over.
			local build, step = Appearance.BodyBuild(saved and saved.Body or 1)
			look.Body = Appearance.BodyFor(Appearance.BodyGender(look.Body), build, step) or (saved and saved.Body) or 1
			look.Areas = saved and saved.Areas or "" -- (training 1.81) per-area bodies come only from Appearance.SetArea
		end
		if look.HairId > 0 and look.HairId ~= (saved and saved.HairId) and not Appearance.IsHairCached(look.HairId) then
			-- a new, uncached id costs web calls: at most one per player every 1.5 s
			if lastLookup[p] and now - lastLookup[p] < 1.5 then
				look.HairId = saved and saved.HairId or 0
			else
				lastLookup[p] = now
				Appearance.LoadHair(look.HairId)
			end
		end
		if look.HairId > 0 and Appearance.IsKnownNotHair(look.HairId) then
			look.HairId = 0 -- never save an id that isn't a hair (a lookup hiccup keeps it)
		end
		if look.Cape and look.Cape > 1 then
			local prof = Data.GetProfile(p)
			local owned = prof and type(prof.Identity) == "table" and type(prof.Identity.Capes) == "table" and prof.Identity.Capes or {}
			local cape = Appearance.Capes[look.Cape]
			if cape and cape.Admin then -- the admin capes (3D, staff-only): staff only, in Studio too; never bought
				if not Appearance.IsStaff(p) then
					look.Cape = 1
				end
			elseif not (cape and (table.find(owned, cape.Id) or RunService:IsStudio())) then -- free in Studio, like the shop
				look.Cape = saved and saved.Cape or 1 -- not bought: keep what they had
			end
		end
		do -- 3D accessories (1.79, Config.Accessories): owned (Identity.Accessories; free in Studio, like capes) and
			-- your gender's (or Unisex); Admin items (the Headmaster's Circle) are staff only, in Studio too; an item
			-- whose template isn't in the game yet is refused. A slot that fails keeps what was saved there.
			local okA, AccCfg = pcall(require, ReplicatedStorage.Config.Accessories)
			if okA then
				local prof = Data.GetProfile(p)
				local ident = prof and type(prof.Identity) == "table" and prof.Identity or {}
				local owned = type(ident.Accessories) == "table" and ident.Accessories or {}
				local staff = Appearance.IsStaff(p)
				local want, had = AccCfg.Parse(look.Acc), AccCfg.Parse(saved and saved.Acc)
				local keep = {}
				for slot, id in pairs(want) do
					local it = AccCfg.ById[id]
					local ok
					if it.Admin then
						ok = staff
					else
						ok = (table.find(owned, id) ~= nil or RunService:IsStudio())
							and (it.Gender == "Unisex" or it.Gender == Appearance.BodyGender(look.Body))
					end
					if ok then -- the hair worn with it must have a fit (acc_hairfit.py), so no strand passes through
						local wm = script.Parent:FindFirstChild("AccessoryWear")
						local okW, AccWear = pcall(require, wm)
						if wm and okW and not AccWear.FitsHair(it, look.HairId) then
							ok = false
						end
					end
					if ok and AccCfg.Ready(it) then
						keep[slot] = id
					elseif had[slot] and not (it.Admin and not staff) then
						keep[slot] = had[slot]
					end
				end
				-- (1.79) the hair rules a piece out wherever it came from (a hair change at the barber, an older save):
				-- it comes off, so no strand passes through it
				do
					local wm = script.Parent:FindFirstChild("AccessoryWear")
					local okW, AccWear = pcall(require, wm)
					if wm and okW then
						for slot, id in pairs(keep) do
							local it = AccCfg.ById[id]
							if it and not AccWear.FitsHair(it, look.HairId) then
								keep[slot] = nil
							end
						end
					end
				end
				look.Acc = AccCfg.Join(keep)
				-- a cape and accessories that pass through each other (Config.Accessories.Conflicts): the one just
				-- changed wins (a new cape takes the clashing pieces off; a new piece takes the cape off)
				local capeDef = Appearance.Capes[look.Cape]
				if capeDef and capeDef.Id ~= "none" then
					local worn = AccCfg.Parse(look.Acc)
					local capeNew = not saved or saved.Cape ~= look.Cape
					for slot, id in pairs(worn) do
						if AccCfg.CapeClash(capeDef.Id, AccCfg.ById[id]) then
							if capeNew then
								worn[slot] = nil
							else
								look.Cape = 1
								break
							end
						end
					end
					look.Acc = AccCfg.Join(worn)
				end
			end
		end
		do -- clothes by gender (1.71): only your gender's pieces or Unisex ones; the admin kit is staff-only.
			-- Switching gender swaps each piece for its counterpart; an unchanged saved piece is kept.
			local staff = Appearance.IsStaff(p)
			local switched = saved ~= nil and Appearance.BodyGender(saved.Body) ~= Appearance.BodyGender(look.Body)
			if switched then
				Appearance.DressForGender(look, staff)
			end
			local d = Appearance.GenderDefaults[Appearance.BodyGender(look.Body)] or {}
			if not (saved and not switched and saved.Uniform == look.Uniform)
				and not Appearance.ClothingAllows(Appearance.Uniforms[look.Uniform], look, staff) then
				look.Uniform = (saved and not switched and saved.Uniform) or Appearance.Defaults.Uniform
			end
			if not (saved and not switched and saved.Bottoms == look.Bottoms)
				and not Appearance.ClothingAllows(Appearance.BottomsList[look.Bottoms], look, staff) then
				look.Bottoms = (saved and not switched and saved.Bottoms) or (d.Bottoms and Appearance.IndexOf(Appearance.BottomsList, d.Bottoms)) or Appearance.Defaults.Bottoms
			end
		end
		do -- clothes: school tops must be owned, school bottoms need enrolment (Services.School.Enrollment)
			local prof = Data.GetProfile(p)
			local ident = prof and type(prof.Identity) == "table" and prof.Identity or {}
			local owned = type(ident.Uniforms) == "table" and ident.Uniforms or {}
			local enrolled = ident.Enrolled ~= false -- nil = an older student (counts as enrolled)
			local u = Appearance.Uniforms[look.Uniform]
			if Appearance.IsSchoolTop(look.Uniform) and not (u and Appearance.OwnsTop(owned, u.Id)) and not (saved and saved.Uniform == look.Uniform) then
				look.Uniform = saved and saved.Uniform or Appearance.Defaults.Uniform
			end
			if Appearance.IsSchoolBottom(look.Bottoms) and not enrolled and not (saved and saved.Bottoms == look.Bottoms) then
				look.Bottoms = saved and saved.Bottoms or Appearance.Defaults.Bottoms
			end
		end
		if saved and saved.Created and sameLook(saved, look) then
			return -- nothing changed: no save, no rebuild
		end
		Data.UpdateState(p, { type = "SetAppearance", appearance = Appearance.Encode(look) })
		if p.Character then
			pcall(Appearance.ApplyTo, p.Character, look)
		end
	end)
	-- training / admin desk (2026-11-10): set a student's build ("Average", "Skinny", "Conditioned", "Heavy") and step.
	-- Keeps their gender; saved through Data like every look change, then re-applied. Returns ok, body name / reason.
	function Appearance.SetBuild(p, build, step)
		local saved = profileLook(p)
		if not saved then
			return false, "No loaded slot"
		end
		if not table.find(Appearance.Builds, build) then
			return false, "Unknown build"
		end
		local idx = Appearance.BodyFor(Appearance.BodyGender(saved.Body), build, tonumber(step) or 0)
		if not idx then
			return false, "No body for that build"
		end
		local look = table.clone(saved)
		look.Body = idx
		look.Areas = "" -- (training 1.81) the whole body, every area
		Data.UpdateState(p, { type = "SetAppearance", appearance = Appearance.Encode(look) })
		if p.Character then
			pcall(Appearance.ApplyTo, p.Character, look)
		end
		return true, Appearance.Bodies[idx].Name
	end
	-- (training 1.81) training changes ONE area: "Torso", "Arms" or "Legs" to a path ("Average", "Conditioned",
	-- "Heavy", "Lean") and step, keeping the other two areas and the gender. Never lowers an area that is already
	-- at that path and a higher step. The look's Body follows the torso (accessories fit to it). Returns ok,
	-- body name / reason, changed.
	local PATH_BUILD = { Average = "Average", Conditioned = "Conditioned", Heavy = "Heavy", Lean = "Skinny", Skinny = "Skinny" }
	function Appearance.SetArea(p, area, path, step)
		local saved = profileLook(p)
		if not saved then
			return false, "No loaded slot", false
		end
		if not Appearance.AreaParts[area] then
			return false, "Unknown area", false
		end
		local build = PATH_BUILD[path]
		if not build then
			return false, "Unknown path", false
		end
		local gender = Appearance.BodyGender(saved.Body)
		local idx = Appearance.BodyFor(gender, build, tonumber(step) or 0)
		if not idx then
			return false, "No body for that path", false
		end
		local areas = Appearance.AreaBodies(saved)
		local curBuild, curStep = Appearance.BodyBuild(areas[area])
		local _, newStep = Appearance.BodyBuild(idx)
		if areas[area] == idx or (curBuild == build and curStep >= newStep) then
			return true, Appearance.Bodies[areas[area]].Name, false
		end
		areas[area] = idx
		local look = table.clone(saved)
		look.Areas = Appearance.EncodeAreas(areas)
		look.Body = areas.Torso
		Data.UpdateState(p, { type = "SetAppearance", appearance = Appearance.Encode(look) })
		if p.Character then
			pcall(Appearance.ApplyTo, p.Character, look)
		end
		return true, Appearance.Bodies[idx].Name, true
	end
	checkRF.OnServerInvoke = function(p, id)
		local now = os.clock()
		if lastCheck[p] and now - lastCheck[p] < 1 then
			return false, "One moment..."
		end
		lastCheck[p] = now
		id = tonumber(id)
		if not id or id ~= math.floor(id) or id <= 0 or id >= 1e15 then
			return false, "Enter a number"
		end
		local acc, name = Appearance.LoadHair(id)
		return acc and true or false, name
	end
	Players.PlayerRemoving:Connect(function(p)
		last[p], lastCheck[p], lastLookup[p] = nil, nil, nil
		if p.Character then
			forgetCharacter(p.Character)
		end
	end)
end

--------------------------------------------------------------------------
-- client
--------------------------------------------------------------------------
Appearance.Current = table.clone(Appearance.Defaults)

local function remotes()
	return ReplicatedStorage:WaitForChild(Appearance.RemotesName, 10)
end

function Appearance.Fetch()
	local ps = Players.LocalPlayer:WaitForChild("PlayerScripts")
	local m = ps:WaitForChild("Controllers"):WaitForChild("StateController", 15)
	local ok, sc = pcall(require, m)
	local profile = ok and sc and sc.GetProfile(true)
	Appearance.Current = Appearance.Sanitize(profile and profile.Appearance)
	return Appearance.Current, not Appearance.Current.Created
end

local sendToken = 0
function Appearance.Send(data)
	local look = Appearance.Sanitize(data)
	Appearance.Current = table.clone(look)
	sendToken += 1
	local my = sendToken
	task.delay(0.25, function() -- coalesce quick clicks and colour drags
		if my ~= sendToken then
			return
		end
		local f = remotes()
		if f then
			f:WaitForChild("Set"):FireServer(Appearance.Encode(look)) -- ids, as it was when you clicked
		end
	end)
end

-- Cancel a pending Send (e.g. the profile changed under the Wardrobe before it went out)
function Appearance.CancelSend()
	sendToken += 1
end

function Appearance.CheckHair(id)
	local f = remotes()
	if not f then
		return false, "Wardrobe is offline"
	end
	local ok, a, b = pcall(function()
		return f:WaitForChild("CheckHair"):InvokeServer(id)
	end)
	if not ok then
		return false, "Check failed"
	end
	return a, b
end

return Appearance
