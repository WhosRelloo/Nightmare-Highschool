-- Accessories 1.79 (play-test fixes) for Gui.Wardrobe, NH Combat Test, Edit. Backup NH_Backup.Accessories_pre2.
--  * a hair change (barber, creator) takes off the accessories that hair passes through, and says so
--  * "Took off ..." messages stay up (Local.Notice) instead of being replaced by "Saved to your profile" 1.2 s later
local SS = game:GetService("ServerStorage")
local M = game.StarterPlayer.StarterPlayerScripts.Controllers.Gui.Wardrobe
local S = M.Source
if string.find(S, "function Local.DropForHair", 1, true) then
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
local function all(a, b, label)
	local n = 0
	while true do
		local i = string.find(S, a, 1, true)
		if not i then break end
		S = string.sub(S, 1, i - 1) .. b .. string.sub(S, i + #a)
		n += 1
	end
	assert(n > 0, "not found: " .. label)
	table.insert(report, "ok " .. label .. " x" .. n)
end

once([=[function Local.Set(Key: string | { [string]: any }, Value: any?)
	if not Local.Ready() then return end
	if type(Key) == `table` then
		for K, V in Key do Data[K] = V end
	else
		Data[Key] = Value
	end
	Appearance.Send(Data)
	Local.Render()
	Local.Saving()
end]=], [=[function Local.Set(Key: string | { [string]: any }, Value: any?)
	if not Local.Ready() then return end
	if type(Key) == `table` then
		for K, V in Key do Data[K] = V end
	else
		Data[Key] = Value
	end
	local HairOff = Local.DropForHair()
	Appearance.Send(Data)
	Local.Render()
	Local.Saving()
	if HairOff then Local.Notice(HairOff) end
end

-- A message that stays up (the "Saved" that follows a change would otherwise replace it).
function Local.Notice(Text: string, _Ok: boolean?)
	StatusToken += 1
	Local.Status(Text, true)
end

-- (1.79) the accessories the current hair passes through come off (a hair change at the barber or in the creator);
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
end]=], "Set.hair")

all([=[Local.Status(`Took off ]=], [=[Local.Notice(`Took off ]=], "notices")

local fn, err = loadstring(S)
assert(fn, "compile: " .. tostring(err))
local bk = SS:FindFirstChild("NH_Backup") or Instance.new("Folder", SS)
bk.Name = "NH_Backup"
local f = bk:FindFirstChild("Accessories_pre2") or Instance.new("Folder", bk)
f.Name = "Accessories_pre2"
if not f:FindFirstChild("StarterPlayer__StarterPlayerScripts__Controllers__Gui__Wardrobe") then
	local c = M:Clone()
	c.Name = "StarterPlayer__StarterPlayerScripts__Controllers__Gui__Wardrobe"
	c.Parent = f
end
M.Source = S
table.insert(report, "len " .. #S)
return table.concat(report, "\n")
