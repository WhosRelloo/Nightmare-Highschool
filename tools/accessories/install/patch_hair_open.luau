-- 1.88.0 (owner: "Let players wear clothing their hair doesnt tuck, etc. for. It just wont have the new look for it.")
-- NH Combat Test, Edit. Backups in ServerStorage.NH_Backup.HairOpen_pre. Re-runnable (each script once).
--  * UI.AccessoryWear: a hair with no measured fit ("x") or a tuck its rig can't take still wears the piece, at the
--    piece's default fit ("*"), with the hair left as it is (no tuck)
--  * UI.Appearance: the server no longer refuses or takes off a piece for the hair
--  * Gui.Wardrobe: picking such a piece wears it (a note says the hair won't tuck); a hair change takes nothing off
if game.PlaceId ~= 98950102230473 then return "WRONG PLACE" end
local SS = game:GetService("ServerStorage")
local RS = game:GetService("ReplicatedStorage")
local bk = SS:FindFirstChild("NH_Backup") or Instance.new("Folder", SS)
bk.Name = "NH_Backup"
local into = bk:FindFirstChild("HairOpen_pre") or Instance.new("Folder", bk)
into.Name = "HairOpen_pre"
local report = {}

local function patch(M, label, done, edits)
	local S = M.Source
	if string.find(S, done, 1, true) then
		table.insert(report, label .. ": already patched")
		return
	end
	if not into:FindFirstChild(label) then
		local c = M:Clone()
		c.Name = label
		c.Parent = into
	end
	for _, e in edits do
		local a, b = e[1], e[2]
		local i = string.find(S, a, 1, true)
		assert(i, label .. ": not found: " .. e[3])
		assert(not string.find(S, a, i + 1, true), label .. ": found twice: " .. e[3])
		S = string.sub(S, 1, i - 1) .. b .. string.sub(S, i + #a)
	end
	M.Source = S
	table.insert(report, label .. ": " .. #edits .. " edits")
end

-- UI.AccessoryWear ------------------------------------------------------------------------------------------------
patch(RS.UI.AccessoryWear, "AccessoryWear", "function Wear.DefaultFit", {
	{ [=[dz = lift; other pieces are 1,0 or x. "x" = that hair can't wear it. "*" = any other hair.]=],
	  [=[dz = lift; other pieces are 1,0 or x. "x" = no measured fit for that hair: the piece is
	              still worn, at the "*" fit, and the hair isn't tucked round it (it may pass through). "*" = any other hair.]=], "doc x" },
	{ [=[-- can this hair wear the item (every head piece has a fit for it)?]=],
	  [=[-- a head piece's fit for a hair it has no fit for: the "*" fit (1, 0 without one)
function Wear.DefaultFit(P: Instance): (number, number)
	local K, Z = Wear.HairFit(P, `*`)
	return K or 1, Z or 0
end

-- does this hair get the item's full look (every piece has a measured fit for it, and any tuck it needs can be
-- taken)? A hair that doesn't still wears it, untucked (1.88)]=], "FitsHair doc" },
	{ [=[	local HK, HZ = Wear.HairFit(Tpl, HairKey) -- every piece: nil = this hair passes through it (not worn)
	if not HK then return end
	-- the fit may rely on a hair tuck, which only a v2 rig can take
	if not TuckOK and Wear.ParseTuck(Tpl:GetAttribute(`NHHairTuck`), HairKey) then return end]=],
	  [=[	local HK, HZ = Wear.HairFit(Tpl, HairKey)
	-- no measured fit for this hair: worn anyway at the default fit, the hair untucked (owner, 1.88: "It just wont
	-- have the new look for it"). A tuck an older rig can't take is left off the same way (applyTuck)
	if not HK then HK, HZ = Wear.DefaultFit(Tpl) end]=], "wearPiece" },
	{ [=[		if #Holder:GetChildren() == 0 then -- nothing fitted (this hair passes through it): wear nothing for the slot]=],
	  [=[		if #Holder:GetChildren() == 0 then -- no piece could be placed (no mount part): wear nothing for the slot]=], "holder" },
	{ [=[nothing is turned, and a piece that needs a turn for that hair isn't worn (as if the hair passed through it).]=],
	  [=[nothing is turned, and a piece that needs a turn for that hair is still worn, untucked (1.88).]=], "doc rig" },
	{ [=[-- a head piece's fit for a hair: k, dz (nil = this hair can't wear it)]=],
	  [=[-- a head piece's fit for a hair: k, dz (nil = no measured fit for it: Wear.DefaultFit)]=], "doc HairFit" },
})

-- UI.Appearance (the server's look check) --------------------------------------------------------------------------
patch(RS.UI.Appearance, "Appearance", "(1.88) the hair no longer rules a piece out", {
	{ [=[					if ok then -- the hair worn with it must have a fit (acc_hairfit.py), so no strand passes through
						local wm = script.Parent:FindFirstChild("AccessoryWear")
						local okW, AccWear = pcall(require, wm)
						if wm and okW and not AccWear.FitsHair(it, look.HairId) then
							ok = false
						end
					end
]=], "", "want check" },
	{ [=[				-- (1.79) the hair rules a piece out wherever it came from (a hair change at the barber, an older save):
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
]=], [=[				-- (1.88) the hair no longer rules a piece out: a hair with no measured fit wears it untucked
				-- (UI.AccessoryWear), so a hair change takes nothing off
]=], "keep check" },
})

-- Gui.Wardrobe -------------------------------------------------------------------------------------------------------
patch(game.StarterPlayer.StarterPlayerScripts.Controllers.Gui.Wardrobe, "Wardrobe", "hair won't tuck round it", {
	{ [=[	local HairOff = Local.DropForHair()
	Appearance.Send(Data)
	Local.Render()
	Local.Saving()
	if HairOff then Local.Notice(HairOff) end]=],
	  [=[	Appearance.Send(Data)
	Local.Render()
	Local.Saving()]=], "Set" },
	{ [=[-- (1.79) the accessories the current hair passes through come off (a hair change at the barber or in the creator);
-- returns what to tell the student, or nil. The server does the same (UI.Appearance).
function Local.DropForHair(): string?
	if type(Data.Acc) ~= `string` or Data.Acc == `` then return nil end
	local AccCfg = require(ReplicatedStorage.Config.Accessories)
	local AccWear = require(UI:WaitForChild(`AccessoryWear`))
	local Worn, Off = AccCfg.Parse(Data.Acc), {}
	for Slot, Id in AccCfg.Parse(Data.Acc) do
		local It = AccCfg.ById[Id]
		if It and not AccWear.FitsHair(It, Data.HairId) then
			Worn[Slot] = nil
			table.insert(Off, It.Name)
		end
	end
	if #Off == 0 then return nil end
	Data.Acc = AccCfg.Join(Worn)
	return `Took off {table.concat(Off, ", ")}: this hair would pass through it.`
end

]=], "", "DropForHair" },
	{ [=[-- fit over your hair. Admin = true items live in the Admin tab (staff only). The server checks all of it again.]=],
	  [=[-- go over any hair (1.88: a hair without a measured fit wears it untucked; the row says so). Admin = true items live
-- in the Admin tab (staff only). The server checks all of it again.]=], "rows doc" },
	{ [=[		if not AccWear.FitsHair(It, Data.HairId) then
			Local.Status(`{It.Name} doesn't fit over this hair. Try another hairstyle at the barber.`, false)
			return
		end
		local New = AccCfg.Resolve(Worn, It.Id)]=],
	  [=[		local Untucked = not AccWear.FitsHair(It, Data.HairId)
		local New = AccCfg.Resolve(Worn, It.Id)]=], "pick" },
	{ [=[		if #Off > 0 then Local.Notice(`Took off {table.concat(Off, ", ")}: they can't be worn together.`, true) end
	end]=],
	  [=[		if #Off > 0 then
			Local.Notice(`Took off {table.concat(Off, ", ")}: they can't be worn together.`, true)
		elseif Untucked then
			Local.Notice(`{It.Name}: this hair won't tuck round it, so they may overlap.`, true)
		end
	end]=], "pick note" },
	{ [=[if Fits then It.Name else `{It.Name}  (not with this hair)`]=],
	  [=[if Fits then It.Name else `{It.Name}  (hair won't tuck)`]=], "row label" },
})

return table.concat(report, "\n")
