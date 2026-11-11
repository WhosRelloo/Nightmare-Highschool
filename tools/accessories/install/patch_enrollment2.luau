-- Accessories 1.79 (play-test fix) for Gui.Enrollment: the School Store's header line follows the tab (it said
-- "Uniform tops · ¥250 each" over the accessories). NH Combat Test, Edit. Backup NH_Backup.Accessories_pre2.
local SS = game:GetService("ServerStorage")
local M = game.StarterPlayer.StarterPlayerScripts.Controllers.Gui.Enrollment
local S = M.Source
if string.find(S, "function Local.StoreHeader", 1, true) then
	return "already patched"
end
local report = {}
local function once(a, b, label)
	local i = string.find(S, a, 1, true)
	assert(i, "not found: " .. label)
	assert(not string.find(S, a, i + 1, true), "found twice: " .. label)
	S = string.sub(S, 1, i - 1) .. b .. string.sub(S, i + #a)
	table.insert(report, "ok " .. label)
end
once([=[	local Info = Local.Label(`Uniform tops · ¥{Cat.Price} each · wear them from a locker-room wardrobe`, 16, 1, Head)]=],
	[=[	local Info = Local.Label(Local.StoreHeader(Cat), 16, 1, Head)]=], "header")
once([=[onChanged = function(Index) Local.StoreTab = Index; if Grid then Local.FillStore(Grid, Cat) end end;]=],
	[=[onChanged = function(Index) Local.StoreTab = Index; Info.Text = Local.StoreHeader(Cat); if Grid then Local.FillStore(Grid, Cat) end end;]=],
	"header.tab")
once([=[function Shared.OpenStore()]=], [=[-- the store's header line for the open tab
function Local.StoreHeader(Cat): string
	if Local.StoreTab == 7 then
		return `3D accessories · one per slot · wear them from a locker-room wardrobe (Accessories)`
	end
	return `Uniform tops · ¥{Cat.Price} each · wear them from a locker-room wardrobe`
end

function Shared.OpenStore()]=], "StoreHeader")
local fn, err = loadstring(S)
assert(fn, "compile: " .. tostring(err))
local bk = SS:FindFirstChild("NH_Backup") or Instance.new("Folder", SS)
bk.Name = "NH_Backup"
local f = bk:FindFirstChild("Accessories_pre2") or Instance.new("Folder", bk)
f.Name = "Accessories_pre2"
if not f:FindFirstChild("StarterPlayer__StarterPlayerScripts__Controllers__Gui__Enrollment") then
	local c = M:Clone()
	c.Name = "StarterPlayer__StarterPlayerScripts__Controllers__Gui__Enrollment"
	c.Parent = f
end
M.Source = S
table.insert(report, "len " .. #S)
return table.concat(report, "\n")
