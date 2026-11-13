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
