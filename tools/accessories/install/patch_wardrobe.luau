-- Accessories 1.79: the Wardrobe's Accessories tab and the staff-only Admin tab (NH Combat Test, Edit). Plain-text
-- replacements, each must match once; backup ServerStorage.NH_Backup.Accessories_pre first. Strings use [=[ ]=]
-- because the Wardrobe's own code contains "]]".
local SS = game:GetService("ServerStorage")
local M = game.StarterPlayer.StarterPlayerScripts.Controllers.Gui.Wardrobe
local S = M.Source
local report = {}
if string.find(S, "Local.AccessoriesTab", 1, true) then
	return "already patched"
end
local function once(a, b, label)
	local i = string.find(S, a, 1, true)
	assert(i, "not found: " .. label)
	assert(not string.find(S, a, i + 1, true), "found twice: " .. label)
	S = string.sub(S, 1, i - 1) .. b .. string.sub(S, i + #a)
	table.insert(report, "ok " .. label)
end

once([=[local TABS = { `Look`, `Face`, `Hair`, `Outfit` }]=],
	[=[local TABS = { `Look`, `Face`, `Hair`, `Outfit`, `Accessories`, `Admin` } -- Admin: staff only (Appearance.IsStaff; the server checks too)]=],
	"TABS")

once([=[	if Mode == `Outfit` then Tab = 4 elseif Mode == `Barber` then Tab = 3 end
	local TabBar = Ui.Panel:FindFirstChild(`Tabs`, true)
	if TabBar then TabBar.Visible = Mode == `Full` end]=],
[=[	-- the tabs each mode shows: the creator all of them; a wardrobe station the outfit, accessories and (staff) the Admin
	-- tab; the barber hair only
	local IsStaff = Appearance.IsStaff(Player)
	local Show = if Mode == `Barber` then { Hair = true }
		elseif Mode == `Outfit` then { Outfit = true; Accessories = true; Admin = IsStaff }
		else { Look = true; Face = true; Hair = true; Outfit = true; Accessories = true; Admin = IsStaff }
	if not Show[TABS[Tab]] then Tab = if Mode == `Barber` then 3 else 4 end
	local TabBar = Ui.Panel:FindFirstChild(`Tabs`, true)
	if TabBar then
		TabBar.Visible = Mode ~= `Barber`
		local Shown = 0
		for _, N in TABS do if Show[N] then Shown += 1 end end
		local List = TabBar:FindFirstChild(`Tabs`)
		for _, N in TABS do
			local B = List and List:FindFirstChild(N)
			if B and B:IsA(`GuiObject`) then
				B.Visible = Show[N] == true
				B.Size = UDim2.new(1 / math.max(1, Shown), 0, 1, 0)
			end
		end
		if Ui.Tabs and Ui.Tabs.Select then Ui.Tabs:Select(Tab, true) end
	end]=], "Render.tabs")

once([=[	local Build = ({ Local.LookTab, Local.FaceTab, Local.HairTab, Local.OutfitTab })[Tab]]=],
	[=[	local Build = ({ Local.LookTab, Local.FaceTab, Local.HairTab, Local.OutfitTab, Local.AccessoriesTab, Local.AdminTab })[Tab]]=],
	"Render.build")

-- the old stat-gear section is "Gear" now (the new tab is the cosmetic Accessories)
once([=[	Local.Section(`Accessories`)
	local GearCfg]=], [=[	Local.Section(`Gear`)
	local GearCfg]=], "Gear.rename")

-- a cape that clashes with worn accessories takes them off
once([=[			if Have then
				Local.Set(`Cape`, Index)
			else]=], [=[			if Have then
				local AccCfg = require(ReplicatedStorage.Config.Accessories)
				local Worn, Off = AccCfg.Parse(Data.Acc), {}
				for S, Id in AccCfg.Parse(Data.Acc) do
					if AccCfg.CapeClash(Cape.Id, AccCfg.ById[Id]) then Worn[S] = nil table.insert(Off, AccCfg.ById[Id].Name) end
				end
				Local.Set({ Cape = Index; Acc = AccCfg.Join(Worn) })
				if #Off > 0 then Local.Status(`Took off {table.concat(Off, ", ")}: it can't be worn with a cape.`, true) end
			else]=], "Cape.clash")

once([=[---| Render |---]=], [=[-- 3D accessories (Config.Accessories, UI.AccessoryWear): a row per slot, from what you own (all of it in Studio).
-- Picking one takes off whatever it can't be worn with (they'd pass through each other) and says so; pieces must
-- fit over your hair. Admin = true items live in the Admin tab (staff only). The server checks all of it again.
function Local.AccessoryRows(AdminKit: boolean)
	local AccCfg = require(ReplicatedStorage.Config.Accessories)
	local AccWear = require(UI:WaitForChild(`AccessoryWear`))
	local Owned = {}
	pcall(function()
		local P = Profiles and Profiles.GetProfile(false)
		for _, Id in (P and P.Identity and P.Identity.Accessories) or {} do Owned[Id] = true end
	end)
	local Worn = AccCfg.Parse(Data.Acc)
	local CapeDef = Appearance.Capes[Data.Cape or 1]
	local Gender = Appearance.BodyGender(Data.Body)
	local Any = false
	local function pick(It)
		if not AccWear.FitsHair(It, Data.HairId) then
			Local.Status(`{It.Name} doesn't fit over this hair. Try another hairstyle at the barber.`, false)
			return
		end
		local New = AccCfg.Resolve(Worn, It.Id)
		local Off = {}
		for S, Id in Worn do
			if New[S] ~= Id and S ~= It.Slot then table.insert(Off, AccCfg.ById[Id].Name) end
		end
		local Change = { Acc = AccCfg.Join(New) }
		if CapeDef and AccCfg.CapeClash(CapeDef.Id, It) then
			Change.Cape = 1
			table.insert(Off, CapeDef.Short or CapeDef.Name)
		end
		Local.Set(Change)
		if #Off > 0 then Local.Status(`Took off {table.concat(Off, ", ")}: they can't be worn together.`, true) end
	end
	for _, Slot in AccCfg.Slots do
		local List = {}
		for _, It in AccCfg.BySlot[Slot] do
			if (It.Admin == true) ~= AdminKit or not AccCfg.Ready(It) then continue end
			if It.Gender ~= `Unisex` and It.Gender ~= Gender and Worn[Slot] ~= It.Id then continue end
			if not AdminKit and not (Owned[It.Id] or RunService:IsStudio() or Worn[Slot] == It.Id) then continue end
			table.insert(List, It)
		end
		if #List == 0 then continue end
		Any = true
		Local.Section(AccCfg.SlotNames[Slot] or Slot)
		local Row = Local.Row()
		Local.Choice(Row, 0, `None`, Worn[Slot] == nil, function()
			local New = table.clone(Worn)
			New[Slot] = nil
			Local.Set(`Acc`, AccCfg.Join(New))
		end, 184)
		for N, It in List do
			if N % 3 == 0 then Row = Local.Row() end
			local Fits = AccWear.FitsHair(It, Data.HairId)
			Local.Choice(Row, N, if Fits then It.Name else `{It.Name}  (not with this hair)`, Worn[Slot] == It.Id, function() pick(It) end, 184)
		end
	end
	return Any
end

function Local.AccessoriesTab()
	Local.Section(`Accessories`)
	Local.Note(`3D pieces, one per slot. They're bought at the School Store and belong to this student. A few can't be worn together (they'd pass through each other): picking one takes the other off.`)
	if not Local.AccessoryRows(false) then
		Local.Note(`You don't own any accessories yet. Find them at the School Store.`)
	end
end

function Local.AdminTab()
	if not Appearance.IsStaff(Player) then
		Local.Note(`Staff only.`)
		return
	end
	Local.Section(`The Headmaster's Circle`)
	Local.Note(`Admin regalia: staff only, never sold. The server checks it on every change.`)
	if not Local.AccessoryRows(true) then
		Local.Note(`No regalia in the game yet.`)
	end
end

---| Render |---]=], "Tabs.code")

local fn, err = loadstring(S)
assert(fn, "compile: " .. tostring(err))
local bk = SS:FindFirstChild("NH_Backup") or Instance.new("Folder", SS)
bk.Name = "NH_Backup"
local f = bk:FindFirstChild("Accessories_pre") or Instance.new("Folder", bk)
f.Name = "Accessories_pre"
if not f:FindFirstChild("StarterPlayer__StarterPlayerScripts__Controllers__Gui__Wardrobe") then
	local c = M:Clone()
	c.Name = "StarterPlayer__StarterPlayerScripts__Controllers__Gui__Wardrobe"
	c.Parent = f
end
M.Source = S
table.insert(report, "len " .. #S)
return table.concat(report, "\n")
