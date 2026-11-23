--[[
	Race transformation forms (pure rules). ReplicatedStorage.Functions.Forms   Data: ReplicatedStorage.Config.Forms

	Forms.Options(race): { [slot]: { {Id, Name, Tier} } }   the Look slots a race gets (ReplicatedStorage.Lineage merges
	        them into Lineage.Looks, so SetLook validates and ResolveLooks falls back by tier as for every race Look).
	        Style slots start with "Auto" (the direction's own choice); a direction's own option is Tier I, two more are
	        Tier II, the rest Tier III. HornStyle also offers "None".
	Forms.Resolve(race, looks): the concrete pieces for one character, or nil for a race without a form.
	        looks = { [slot] = optionId } (from the RaceLooks attribute or Lineage.ResolveLooks); unknown ids fall back.
	        -> { Race, Direction, Name, Parts = { region... }, Mantle?,
	             Wings = { Style, Palette, Finish, Size, Scale }?, Horns = { Style, Finish, Tip, Halo }? }
	Forms.ParseLooks(attr): "A=x,B=y" -> { A = "x", B = "y" }
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Cfg = require(ReplicatedStorage:WaitForChild("Config"):WaitForChild("Forms"))

local Forms = {}

Forms.SlotNames = {
	FormDirection = "Form"; WingStyle = "Wings"; WingPalette = "Wing colour"; WingFinish = "Wing bone";
	WingSize = "Wing size"; HornStyle = "Horns"; HornFinish = "Horn finish"; HornTip = "Horn tip";
}

local function tiered(order: { string }, defaults: { [string]: boolean }, auto: boolean, extra: { any }?)
	local out = {}
	if auto then table.insert(out, { Id = "Auto"; Name = "Form default"; Tier = 1 }) end
	for _, E in extra or {} do table.insert(out, E) end
	local twos = 0
	for _, Id in order do
		local Tier = 3
		if defaults[Id] then Tier = 1 elseif twos < 2 then Tier = 2 twos += 1 end
		table.insert(out, { Id = Id; Tier = Tier })
	end
	return out
end

local function named(list, lookup)
	for _, O in list do
		if not O.Name then
			local E = lookup and lookup[O.Id]
			O.Name = (E and E.Name) or O.Id
		end
	end
	return list
end

-- the Look slots for a race (nil = the race has no form)
function Forms.Options(Race: string): { [string]: any }?
	local R = Cfg.Races[Race]
	if not R then return nil end
	local Slots = {}
	Slots.FormDirection = {}
	for _, D in R.Directions do table.insert(Slots.FormDirection, { Id = D.Id; Name = D.Name; Tier = 1 }) end
	if R.WingStyles then
		local Def, Pal, Fin = {}, {}, {}
		for _, D in R.Directions do
			if D.Wings then Def[D.Wings.Style] = true Pal[D.Wings.Palette] = true Fin[D.Wings.Finish] = true end
		end
		Slots.WingStyle = named(tiered(R.WingStyles, Def, true), Cfg.WingStyles)
		Slots.WingPalette = named(tiered(Cfg.PaletteOrder, Pal, true), Cfg.Palettes)
		Slots.WingFinish = named(tiered(Cfg.FinishOrder, Fin, true), Cfg.Finishes)
		local Sizes = {}
		for I, Id in Cfg.SizeOrder do table.insert(Sizes, { Id = Id; Name = Id; Tier = if I == 1 then 1 else 2 }) end
		Slots.WingSize = Sizes
	end
	if R.HornStyles then
		local Def, Fin, Tip = {}, {}, {}
		for _, D in R.Directions do
			if D.Horns then Def[D.Horns.Style] = true Fin[D.Horns.Finish] = true Tip[D.Horns.Tip] = true end
		end
		Slots.HornStyle = named(tiered(R.HornStyles, Def, true, { { Id = "None"; Name = "None"; Tier = 1 } }), Cfg.HornStyles)
		Slots.HornFinish = named(tiered(Cfg.FinishOrder, Fin, true), Cfg.Finishes)
		Slots.HornTip = named(tiered(Cfg.FinishOrder, Tip, true), Cfg.Finishes)
	end
	return Slots
end

-- the slot order shown in the Bloodline Looks
Forms.SlotOrder = { "FormDirection", "WingStyle", "WingPalette", "WingFinish", "WingSize", "HornStyle", "HornFinish", "HornTip" }

local function allowed(list: { string }?, id: any): boolean
	return type(id) == "string" and list ~= nil and table.find(list, id) ~= nil
end

local function pick(id: any, lookup, fallback)
	if type(id) == "string" and id ~= "Auto" and lookup[id] then return id end
	return fallback
end

function Forms.Resolve(Race: string, Looks: { [string]: any }?)
	local R = Cfg.Races[Race]
	if not R then return nil end
	Looks = Looks or {}
	local Dir = R.Directions[1]
	for _, D in R.Directions do if D.Id == Looks.FormDirection then Dir = D end end
	local Out = { Race = Race; Direction = Dir.Id; Name = Dir.Name; Parts = table.clone(Dir.Parts or {}); Mantle = Dir.Mantle }
	-- wings: the direction's own, or a style the race allows
	local WStyle = Dir.Wings and Dir.Wings.Style
	if allowed(R.WingStyles, Looks.WingStyle) then WStyle = Looks.WingStyle end
	if WStyle then
		local Base = Dir.Wings or (R.Directions[1].Wings) or { Palette = "Wine"; Finish = "Obsidian" }
		local Size = pick(Looks.WingSize, Cfg.WingSizes, "Regular")
		Out.Wings = {
			Style = WStyle;
			Palette = pick(Looks.WingPalette, Cfg.Palettes, Base.Palette);
			Finish = pick(Looks.WingFinish, Cfg.Finishes, Base.Finish);
			Size = Size;
			Scale = Cfg.WingSizes[Size];
		}
	end
	-- horns: the direction's own, another the race allows, or None
	if R.HornStyles then
		local HStyle = Dir.Horns and Dir.Horns.Style
		if Looks.HornStyle == "None" then HStyle = nil
		elseif allowed(R.HornStyles, Looks.HornStyle) then HStyle = Looks.HornStyle end
		if HStyle then
			local Base = Dir.Horns or Cfg.HornDefaults
			Out.Horns = {
				Style = HStyle;
				Finish = pick(Looks.HornFinish, Cfg.Finishes, Base.Finish);
				Tip = pick(Looks.HornTip, Cfg.Finishes, Base.Tip);
				Halo = Cfg.HornStyles[HStyle].Halo == true;
			}
		end
	end
	return Out
end

function Forms.ParseLooks(Attr: any): { [string]: string }
	local Out = {}
	if type(Attr) ~= "string" then return Out end
	for Pair in string.gmatch(Attr, "[^,]+") do
		local K, V = string.match(Pair, "^(%w+)=([%w]+)$")
		if K then Out[K] = V end
	end
	return Out
end

return Forms
