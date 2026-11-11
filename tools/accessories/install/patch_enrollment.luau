-- Accessories 1.79: the School Store's Accessories tab (cosmetic 3D kit, Config.Accessories); the old stat-gear tab is
-- renamed Gear. NH Combat Test, Edit. Backup ServerStorage.NH_Backup.Accessories_pre.
local SS = game:GetService("ServerStorage")
local M = game.StarterPlayer.StarterPlayerScripts.Controllers.Gui.Enrollment
local S = M.Source
local report = {}
if string.find(S, "Local.FillAcc", 1, true) then
	return "already patched"
end
local function once(a, b, label)
	local i = string.find(S, a, 1, true)
	assert(i, "not found: " .. label)
	assert(not string.find(S, a, i + 1, true), "found twice: " .. label)
	S = string.sub(S, 1, i - 1) .. b .. string.sub(S, i + #a)
	table.insert(report, "ok " .. label)
end
once([[local STORE_TABS = { `Official`, `Vests`, `Polos & Blouses`, `Jackets & PE`, `Owned`, `Accessories` }]],
	[[local STORE_TABS = { `Official`, `Vests`, `Polos & Blouses`, `Jackets & PE`, `Owned`, `Gear`, `Accessories` } -- Gear: stats (Config.Gear); Accessories: the cosmetic 3D kit (Config.Accessories)]],
	"tabs")
once([[	if Local.StoreTab == 6 then Local.FillGear(Grid) return end]],
	[[	if Local.StoreTab == 6 then Local.FillGear(Grid) return end
	if Local.StoreTab == 7 then Local.FillAcc(Grid) return end]], "fill")
once([[function Local.FillStore(Grid: Instance, Cat)]], [[-- the cosmetic 3D accessories (Config.Accessories): try one on the preview, buy it for Yen. Clique pieces are for
-- that clique's members; the admin regalia is never sold. Services.Features.Accessories checks everything again.
function Local.AccRemote(Name: string)
	local F = ReplicatedStorage:FindFirstChild(`NHAccRemotes`)
	return F and F:GetAttribute(`Ready`) and F:FindFirstChild(Name)
end

function Local.TryAcc(Id: string)
	local Mo = Ui and Ui.PreviewApi and Ui.PreviewApi:GetModel()
	if not Mo then return end
	local Ok, Wear = pcall(require, ReplicatedStorage.UI.AccessoryWear)
	if not Ok then return end
	local App = require(ReplicatedStorage.UI.Appearance)
	local Look = App.Current or {}
	pcall(Wear.Wear, Mo, Id, (App.Bodies[Look.Body or 1] or App.Bodies[1]).Id, Look.HairId)
end

function Local.FillAcc(Grid: Instance)
	local AccCfg = require(ReplicatedStorage.Config.Accessories)
	local Info = nil
	local R = Local.AccRemote(`Info`)
	if R then local Ok, I = pcall(R.InvokeServer, R) Info = Ok and I or nil end
	local Owned = {}
	for _, Id in (Info and Info.Owned) or {} do Owned[Id] = true end
	local N = 0
	for _, It in AccCfg.Items do
		if It.Admin or not It.Price or not AccCfg.Ready(It) then continue end
		N += 1
		local C = Instance.new(`Frame`)
		C.BackgroundTransparency = 1
		C.Size = UDim2.fromOffset(150, 178)
		C.LayoutOrder = N
		local L = Instance.new(`UIListLayout`)
		L.HorizontalAlignment = Enum.HorizontalAlignment.Center
		L.Padding = UDim.new(0, 3)
		L.SortOrder = Enum.SortOrder.LayoutOrder
		L.Parent = C
		local function try() Local.TryAcc(It.Id) end
		local Slot = Kit.ItemSlot({ item = { name = It.Name; rarity = if It.Clique then `Epic` else `Rare` }; size = 96; LayoutOrder = 1; Parent = C; onClick = try })
		Slot.MouseEnter:Connect(try)
		local Sub = Local.Label(AccCfg.SlotNames[It.Slot] or It.Slot, 12, 2, C)
		Sub.Size = UDim2.new(1, 0, 0, 20)
		if Owned[It.Id] then
			local T = Local.Label(`Owned`, 15, 3, C)
			T.Size = UDim2.new(1, 0, 0, 22)
			T.TextColor3 = Color3.fromRGB(150, 205, 140)
		elseif It.Clique and (Info and Info.Clique) ~= It.Clique then
			local T = Local.Label(`Members only`, 14, 3, C)
			T.Size = UDim2.new(1, 0, 0, 22)
		else
			Kit.Button({ text = `¥{It.Price}`; style = `gold`; Size = UDim2.fromOffset(120, 34); LayoutOrder = 3; Parent = C;
				onClick = function()
					try()
					local B = Local.AccRemote(`Buy`)
					if not B then return end
					local Ok, A, Msg = pcall(B.InvokeServer, B, It.Id)
					Local.Status((Ok and Msg) or ``)
					if Ok and A then task.delay(0.5, Shared.OpenStore) end
				end })
		end
		C.Parent = Grid
	end
	if N == 0 then
		local E = Local.Label(`New accessories are on their way.`, 17, 1, Grid)
		E.Size = UDim2.new(1, 0, 0, 40)
	end
end

function Local.FillStore(Grid: Instance, Cat)]], "FillAcc")
local bk = SS:FindFirstChild("NH_Backup") or Instance.new("Folder", SS)
bk.Name = "NH_Backup"
local f = bk:FindFirstChild("Accessories_pre") or Instance.new("Folder", bk)
f.Name = "Accessories_pre"
if not f:FindFirstChild("StarterPlayer__StarterPlayerScripts__Controllers__Gui__Enrollment") then
	local c = M:Clone()
	c.Name = "StarterPlayer__StarterPlayerScripts__Controllers__Gui__Enrollment"
	c.Parent = f
end
M.Source = S
table.insert(report, "len " .. #S)
return table.concat(report, "\n")
