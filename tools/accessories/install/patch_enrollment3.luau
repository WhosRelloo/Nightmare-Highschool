-- Accessories 1.79 for Gui.Enrollment: each store card shows the accessory itself (a 3D view of its template in the
-- slot) with its name and slot under it, instead of a name on a blank tile. NH Combat Test, Edit.
local M = game.StarterPlayer.StarterPlayerScripts.Controllers.Gui.Enrollment
local S = M.Source
if string.find(S, "function Local.AccPreview", 1, true) then
	return "already patched"
end
local a0 = string.find(S, "function Local.FillAcc(Grid: Instance)", 1, true)
local a1 = string.find(S, "function Local.FillStore(Grid: Instance, Cat)", 1, true)
assert(a0 and a1 and a1 > a0, "FillAcc bounds")
local body = string.sub(S, a0, a1 - 1)
local report = {}
local function once(a, b, label)
	local i = string.find(body, a, 1, true)
	assert(i, "not found: " .. label)
	assert(not string.find(body, a, i + 1, true), "found twice: " .. label)
	body = string.sub(body, 1, i - 1) .. b .. string.sub(body, i + #a)
	table.insert(report, "ok " .. label)
end
once([=[		local Sub = Local.Label(AccCfg.SlotNames[It.Slot] or It.Slot, 12, 2, C)
		Sub.Size = UDim2.new(1, 0, 0, 20)]=], [=[		if Local.AccPreview(Slot, It) then
			local Nm = Local.Label(It.Name, 13, 2, C)
			Nm.Size = UDim2.new(1, 0, 0, 16)
			Nm.TextTruncate = Enum.TextTruncate.AtEnd
			Nm.LayoutOrder = 2
		end
		local Sub = Local.Label(AccCfg.SlotNames[It.Slot] or It.Slot, 11, 3, C)
		Sub.Size = UDim2.new(1, 0, 0, 14)
		Sub.LayoutOrder = 3]=], "card.labels")
once([=[local T = Local.Label(`Owned`, 15, 3, C)]=], [=[local T = Local.Label(`Owned`, 15, 4, C)
			T.LayoutOrder = 4]=], "card.owned")
once([=[local T = Local.Label(`Members only`, 14, 3, C)]=], [=[local T = Local.Label(`Members only`, 14, 4, C)
			T.LayoutOrder = 4]=], "card.members")
once([=[Size = UDim2.fromOffset(120, 34); LayoutOrder = 3; Parent = C;]=], [=[Size = UDim2.fromOffset(120, 34); LayoutOrder = 4; Parent = C;]=], "card.buy")
body = [=[-- a 3D view of an accessory's pieces (ReplicatedStorage.NHAccessories, at their fit on the nominal R6 body) in a store
-- slot, framed on the item from the front-right; hides the slot's own name text. Returns true when shown.
local ACC_MOUNT_AT = { Torso = Vector3.zero; Head = Vector3.new(0, 1.5, 0); RightArm = Vector3.new(1.5, 0, 0);
	LeftArm = Vector3.new(-1.5, 0, 0); RightLeg = Vector3.new(0.5, -2, 0); LeftLeg = Vector3.new(-0.5, -2, 0) }
function Local.AccPreview(Slot: GuiObject, It): boolean
	local Ok, AccWear = pcall(require, ReplicatedStorage.UI.AccessoryWear)
	if not Ok then return false end
	local Pieces = AccWear.Pieces(It)
	if #Pieces == 0 then return false end
	local VP = Instance.new(`ViewportFrame`)
	VP.Name = `AccPreview`
	VP.BackgroundTransparency = 1
	VP.AnchorPoint = Vector2.new(0.5, 0.5)
	VP.Position = UDim2.fromScale(0.5, 0.5)
	VP.Size = UDim2.new(1, -10, 1, -10)
	VP.ZIndex = 3
	VP.Ambient = Color3.fromRGB(150, 140, 160)
	VP.LightColor = Color3.fromRGB(255, 244, 228)
	VP.LightDirection = Vector3.new(-0.5, -0.7, -0.6)
	local World = Instance.new(`WorldModel`)
	World.Parent = VP
	for _, Tpl in Pieces do
		local P = Tpl:Clone()
		local Fit = Tpl:GetAttribute(`NHFit`)
		P.CFrame = CFrame.new(ACC_MOUNT_AT[Tpl:GetAttribute(`NHMount`) or `Torso`] or Vector3.zero) * (if typeof(Fit) == `CFrame` then Fit else CFrame.new())
		P.Anchored = true
		P.Parent = World
	end
	local Box, Size = World:GetBoundingBox()
	local R = math.max(Size.Magnitude / 2, 0.2)
	local Cam = Instance.new(`Camera`)
	Cam.FieldOfView = 30
	Cam.CFrame = CFrame.lookAt(Box.Position + Vector3.new(0.45, 0.22, -1).Unit * (R / math.sin(math.rad(15)) * 0.92), Box.Position)
	Cam.Parent = VP
	VP.CurrentCamera = Cam
	VP.Parent = Slot
	local Name = Slot:FindFirstChild(`ItemName`, true)
	if Name then Name.Visible = false end
	return true
end

]=] .. body
S = string.sub(S, 1, a0 - 1) .. body .. string.sub(S, a1)
local fn, err = loadstring(S)
assert(fn, "compile: " .. tostring(err))
M.Source = S
table.insert(report, "len " .. #S)
return table.concat(report, "\n")
