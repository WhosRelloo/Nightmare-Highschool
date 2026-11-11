-- Accessories 1.79 (play-test fix): a piece the hair rules out comes off, wherever it came from. Before, a hair change
-- at the barber kept a worn piece that the new hair passes through (the slot fell back to what was saved). The wear
-- code never drew it, but the saved look still listed it. NH Combat Test, Edit. Backup NH_Backup.Accessories_pre2.
local SS = game:GetService("ServerStorage")
local M = game.ReplicatedStorage.UI.Appearance
local S = M.Source
if string.find(S, "the hair rules a piece out wherever it came from", 1, true) then
	return "already patched"
end
local a = [[				look.Acc = AccCfg.Join(keep)
				-- a cape and accessories that pass through each other]]
local i = string.find(S, a, 1, true)
assert(i and not string.find(S, a, i + 1, true), "anchor")
local b = [[				-- (1.79) the hair rules a piece out wherever it came from (a hair change at the barber, an older save):
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
				-- a cape and accessories that pass through each other]]
S = string.sub(S, 1, i - 1) .. b .. string.sub(S, i + #a)
local bk = SS:FindFirstChild("NH_Backup") or Instance.new("Folder", SS)
bk.Name = "NH_Backup"
local f = bk:FindFirstChild("Accessories_pre2") or Instance.new("Folder", bk)
f.Name = "Accessories_pre2"
if not f:FindFirstChild("ReplicatedStorage__UI__Appearance") then
	local c = M:Clone()
	c.Name = "ReplicatedStorage__UI__Appearance"
	c.Parent = f
end
M.Source = S
return "ok len " .. #S
