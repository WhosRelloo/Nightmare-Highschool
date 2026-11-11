-- Accessories 1.79: wire the 3D accessory kits into UI.Appearance (NH Combat Test, Edit). Plain-text replacements,
-- each must match exactly once; a backup goes to ServerStorage.NH_Backup.Accessories_pre first.
local RS = game:GetService("ReplicatedStorage")
local SS = game:GetService("ServerStorage")
local M = RS.UI.Appearance
local S = M.Source
local report = {}

local function once(a, b, label)
	local i = string.find(S, a, 1, true)
	assert(i, "not found: " .. label)
	assert(not string.find(S, a, i + 1, true), "found twice: " .. label)
	S = string.sub(S, 1, i - 1) .. b .. string.sub(S, i + #a)
	table.insert(report, "ok " .. label)
end

if string.find(S, "NHAccessories (1.79)", 1, true) then
	return "already patched"
end

once([[UseAvatar = false, Created = false, Body = 1, Cape = 1, Marks = 1, RaceEyes = false,
}]], [[UseAvatar = false, Created = false, Body = 1, Cape = 1, Marks = 1, RaceEyes = false,
	Acc = "", -- NHAccessories (1.79): the worn 3D accessories (Config.Accessories ids, one per slot, comma list)
}]], "Defaults.Acc")

once([[	out.SkinHex, out.HairHex, out.EyeHex = hexOf(data.SkinHex), hexOf(data.HairHex), hexOf(data.EyeHex)]],
[[	do -- 3D accessories: a comma list of known ids, one per slot, in slot order (equal looks compare equal)
		local cfgF = ReplicatedStorage:FindFirstChild("Config")
		local mod = cfgF and cfgF:FindFirstChild("Accessories")
		local okA, AccCfg = pcall(require, mod)
		if mod and okA and type(data.Acc) == "string" then
			out.Acc = AccCfg.Join(AccCfg.Parse(data.Acc))
		end
	end
	out.SkinHex, out.HairHex, out.EyeHex = hexOf(data.SkinHex), hexOf(data.HairHex), hexOf(data.EyeHex)]], "Sanitize.Acc")

once([[	Appearance.WearCape(character, data.Cape)
	local folder = Instance.new("Folder")]], [[	Appearance.WearCape(character, data.Cape)
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
	local folder = Instance.new("Folder")]], "ApplyTo.Wear")

once([[Appearance.OutfitFields = { Uniform = true, Bottoms = true, Cape = true }]],
	[[Appearance.OutfitFields = { Uniform = true, Bottoms = true, Cape = true, Acc = true }]], "OutfitFields.Acc")

once([[		do -- clothes by gender (1.71): only your gender's pieces or Unisex ones; the admin kit is staff-only.]],
[[		do -- 3D accessories (1.79, Config.Accessories): owned (Identity.Accessories; free in Studio, like capes) and
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
					if ok then -- head pieces: the hair worn with it must have a fit (acc_hairfit.py), so no strand passes through
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
		do -- clothes by gender (1.71): only your gender's pieces or Unisex ones; the admin kit is staff-only.]], "Set.AccCheck")

-- backup, then write
local bk = SS:FindFirstChild("NH_Backup") or Instance.new("Folder", SS)
bk.Name = "NH_Backup"
local f = bk:FindFirstChild("Accessories_pre") or Instance.new("Folder", bk)
f.Name = "Accessories_pre"
if not f:FindFirstChild("ReplicatedStorage__UI__Appearance") then
	local c = M:Clone()
	c.Name = "ReplicatedStorage__UI__Appearance"
	c.Parent = f
end
M.Source = S
table.insert(report, "len " .. #S)
return table.concat(report, "\n")
