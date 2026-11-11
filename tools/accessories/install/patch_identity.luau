-- Accessories 1.79: Identity.Sanitize keeps the owned 3D accessories (Identity.Accessories), so no SetIdentity save
-- drops them. Backup: ServerStorage.NH_Backup.Accessories_pre.
local SSS = game:GetService("ServerScriptService")
local SS = game:GetService("ServerStorage")
local M = SSS.Services.Player.Identity
local S = M.Source
if string.find(S, "Out.Accessories", 1, true) then
	return "already patched"
end
local a = [[	-- 3D gear (Config.Gear): owned ids and what's worn per slot (Services.Features.Gear)]]
local i = string.find(S, a, 1, true)
assert(i and not string.find(S, a, i + 1, true), "anchor")
local add = [[	-- 3D accessory kits (Config.Accessories, 1.79): owned ids (bought at the School Store; the admin regalia is never owned)
	Out.Accessories = {}
	do
		local AccCfg = require(game:GetService(`ReplicatedStorage`).Config.Accessories)
		if typeof(Raw.Accessories) == `table` then
			for _, Id in Raw.Accessories do
				local It = typeof(Id) == `string` and AccCfg.ById[Id]
				if It and not It.Admin and not table.find(Out.Accessories, Id) then table.insert(Out.Accessories, Id) end
			end
		end
	end
]]
S = string.sub(S, 1, i - 1) .. add .. string.sub(S, i)
local bk = SS:FindFirstChild("NH_Backup") or Instance.new("Folder", SS)
bk.Name = "NH_Backup"
local f = bk:FindFirstChild("Accessories_pre") or Instance.new("Folder", bk)
f.Name = "Accessories_pre"
if not f:FindFirstChild("ServerScriptService__Services__Player__Identity") then
	local c = M:Clone()
	c.Name = "ServerScriptService__Services__Player__Identity"
	c.Parent = f
end
M.Source = S
return "ok len " .. #S
