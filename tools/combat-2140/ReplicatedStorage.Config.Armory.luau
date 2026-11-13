--[[
	The armory (owner, 2026-11-12): "I want all students to start off with the Fist class then can buy a katana from the
	armory shop keeper."  Config.Armory, shared by Services.Features.Armory, Features.ClassLocker and Gui.ArmoryUi.

	  Every student owns Fist. Other classes are owned once bought (or granted by an admin's weapon command) and are
	  saved in PlayerData.Armory = { Owned = { [class] = true }, V = migration version }.
	  Migration V1 (owner: "Everyone to Fist"): no katana was ever sold, so every save made before the armory is moved
	  to Fist once, owning nothing else. A save whose class isn't owned is put back on Fist on every load.
	  The class locker only lets you pick a class you own.
	  Claws are locked for now (owner): no way to buy them; admins can still grant them.
]]
local Armory = {}

Armory.Default = `Fist`
Armory.Version = 1
Armory.Range = 16 -- studs from a counter or the shopkeeper to buy

-- what the armourer sells (in order), and the classes that are shown but locked
Armory.Stock = {
	{ Class = `Katana`; Name = `Katana`; Price = 1000; Text = `The school blade. Long reach, clean cuts.` };
}
Armory.Locked = {
	Claws = `Locked for now.`;
}
Armory.ByClass = {}
for _, S in Armory.Stock do Armory.ByClass[S.Class] = S end

Armory.Shop = { Name = `Iron Vigil Armoury`; Sub = `The armourer`; Text = `Everyone starts with their fists. Steel costs Yen.` }

-- (2.14.0, combat concept 16) hand gear for fists: bought here, one worn at a time (PlayerData.Armory.Gear =
-- { Owned = { [Id] = true }, Worn = Id }). Effects: ServerStorage.Packages.HandGear. Icon / Mesh / textures are group
-- 15981569 uploads (art/group-upload-fistgear); while empty the shop shows the name and nothing is drawn on the hands.
Armory.Gear = {
	{ Id = `HandWraps`; Name = `Hand Wraps`; Price = 250; Icon = ``;
		Text = `Taped knuckles. You take 10% less guard damage while blocking.` };
	{ Id = `WeightedGloves`; Name = `Weighted Gloves`; Price = 500; Icon = ``;
		Text = `Iron in the knuckles. +20% guard damage, but your swings are 5% slower.` };
	{ Id = `BrassKnuckles`; Name = `Brass Knuckles`; Price = 800; Icon = ``; Contraband = true;
		Text = `+15% fist damage, +10% guard damage. Contraband: a hall monitor who sees you fight takes them.` };
}
Armory.GearById = {}
for _, G in Armory.Gear do Armory.GearById[G.Id] = G end

local function GearSave(Data: any): { Owned: { [string]: boolean }, Worn: string? }?
	if typeof(Data) ~= `table` then return nil end
	if typeof(Data.Armory) ~= `table` then Data.Armory = {} end
	if typeof(Data.Armory.Gear) ~= `table` then Data.Armory.Gear = { Owned = {} } end
	if typeof(Data.Armory.Gear.Owned) ~= `table` then Data.Armory.Gear.Owned = {} end
	return Data.Armory.Gear
end

function Armory.OwnsGear(Data: any, Id: string?): boolean
	local G = typeof(Data) == `table` and typeof(Data.Armory) == `table` and Data.Armory.Gear
	return typeof(G) == `table` and typeof(G.Owned) == `table` and typeof(Id) == `string` and G.Owned[Id] == true
end

function Armory.WornGear(Data: any): string?
	local G = typeof(Data) == `table` and typeof(Data.Armory) == `table` and Data.Armory.Gear
	local W = typeof(G) == `table` and G.Worn
	return if typeof(W) == `string` and Armory.GearById[W] and Armory.OwnsGear(Data, W) then W else nil
end

function Armory.GrantGear(Data: any, Id: string)
	local G = GearSave(Data)
	if G and Armory.GearById[Id] then G.Owned[Id] = true end
end

function Armory.WearGear(Data: any, Id: string?)
	local G = GearSave(Data)
	if not G then return end
	G.Worn = if Id and Armory.OwnsGear(Data, Id) then Id else nil
end

-- confiscated (contraband): gone from the save, and off your hands
function Armory.TakeGear(Data: any, Id: string)
	local G = GearSave(Data)
	if not G then return end
	G.Owned[Id] = nil
	if G.Worn == Id then G.Worn = nil end
end

-- does this save own the class? Fist always.
function Armory.Owns(Data: any, Class: string?): boolean
	if Class == Armory.Default then return true end
	if typeof(Class) ~= `string` or typeof(Data) ~= `table` then return false end
	local A = Data.Armory
	return typeof(A) == `table` and typeof(A.Owned) == `table` and A.Owned[Class] == true
end

-- give a class (the shop, or an admin's weapon command)
function Armory.Grant(Data: any, Class: string)
	if typeof(Data) ~= `table` or typeof(Class) ~= `string` or Class == Armory.Default then return end
	if typeof(Data.Armory) ~= `table` then Data.Armory = {} end
	if typeof(Data.Armory.Owned) ~= `table` then Data.Armory.Owned = {} end
	Data.Armory.Owned[Class] = true
end

-- on every profile load (Services.Player.Data), before anything reads the class
function Armory.Migrate(Data: any): boolean
	if typeof(Data) ~= `table` then return false end
	local Changed = false
	if typeof(Data.Armory) ~= `table` then Data.Armory = {} end
	if typeof(Data.Armory.Owned) ~= `table` then Data.Armory.Owned = {} end
	if (tonumber(Data.Armory.V) or 0) < 1 then
		-- V1: everyone to Fist (the katana was a free default until now)
		Data.Weapon = Armory.Default
		Data.Armory.Owned = {}
		Data.Armory.V = 1
		Changed = true
	end
	if not Armory.Owns(Data, Data.Weapon) then
		Data.Weapon = Armory.Default
		Changed = true
	end
	return Changed
end

return Armory
