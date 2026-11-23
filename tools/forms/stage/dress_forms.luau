--!nocheck
-- Race transformations, batch 1 staging (run in Studio Edit; never saves).
-- Dresses the 21 imported form models (Workspace.NHWing_* / NHHorns_*) with SurfaceAppearances from the group images
-- (art/group-upload-forms/textures.json), tints them with the race defaults from Config.Forms, tags them, and moves
-- them to ReplicatedStorage.Assets.Forms.
-- Imported forms face +Z (the FBX axes turn the +Y-facing build round), so the welds need a 180-degree yaw: the
-- model attribute FormYaw = 180 says so.
local RS = game:GetService("ReplicatedStorage")
local ID = {
	Membrane = { 135205925838029, 131588905823219, 98075805815547 },
	Feather = { 77686053566433, 84059578753499, 129806633381577 },
	Cloth = { 138112712699916, 70844911033119, 77793688753953 },
	Mist = { 106250679469907, 129771447645641, 90005488644542 },
	Ice = { 99796689341880, 104415262518492, 84690912729597 },
	Bone = { 124233546569226, 94823965627909, 103382690601514 },
	Horn = { 130451982169321, 83784713526082, 131027277593486 },
}
local SEE_THROUGH = { Mist = true, Ice = true }
local MEMBRANE = { Nocturne = "Membrane", Wyrm = "Membrane", Tattered = "Membrane", Fallen = "Feather",
	Ossuary = "Cloth", Wraithveil = "Mist", Rime = "Ice" }
local rgb = Color3.fromRGB
local PAL = { Wine = rgb(122, 20, 34), Midnight = rgb(52, 60, 112), Ashen = rgb(196, 190, 184), Ember = rgb(176, 70, 30),
	Raven = rgb(34, 36, 48), Dove = rgb(232, 230, 236) }
local FIN = { Obsidian = rgb(30, 28, 34), Bone = rgb(214, 204, 180), Gilded = rgb(196, 156, 74), Ivory = rgb(236, 230, 214),
	Bloodstone = rgb(110, 16, 26) }
-- the spec's default palette / finish per wing style (§3); Ossuary's grave-cloth stays linen (not palette-tinted)
local WING_DEFAULT = { Nocturne = { "Wine", "Obsidian" }, Wyrm = { "Wine", "Bloodstone" }, Tattered = { "Ashen", "Bone" },
	Fallen = { "Raven", "Obsidian" }, Ossuary = { "Linen", "Bone" }, Wraithveil = { "Midnight", "Ivory" },
	Rime = { "Midnight", "Ivory" } }
local LINEN = rgb(176, 170, 152)
-- attach points (Roblox axes, studs): wings from the Torso centre, horns at the Head centre
local WING_ATTACH = Vector3.new(0, 0.72, 0.5)

local function dress(part, set, tint)
	local old = part:FindFirstChildWhichIsA("SurfaceAppearance")
	if old then old:Destroy() end
	local sa = Instance.new("SurfaceAppearance")
	local ids = ID[set]
	sa.ColorMap = "rbxassetid://" .. ids[1]
	sa.NormalMap = "rbxassetid://" .. ids[2]
	sa.RoughnessMap = "rbxassetid://" .. ids[3]
	sa.AlphaMode = SEE_THROUGH[set] and Enum.AlphaMode.Transparency or Enum.AlphaMode.Overlay
	sa.Color = tint
	sa.Name = "Form" .. set
	sa.Parent = part
	part:SetAttribute("FormMaps", set)
end

local assets = RS:WaitForChild("Assets")
local forms = assets:FindFirstChild("Forms") or Instance.new("Folder")
forms.Name = "Forms"
forms.Parent = assets
local report = {}
for _, m in ipairs(workspace:GetChildren()) do
	if not m:IsA("Model") then continue end
	local style, side = m.Name:match("^NHWing_(%a+)_([LR])$")
	local hstyle = m.Name:match("^NHHorns_(%a+)$")
	if style then
		local d = WING_DEFAULT[style]
		for _, p in ipairs(m:GetDescendants()) do
			if p:IsA("MeshPart") then
				if p.Name:match("Membrane$") then
					dress(p, MEMBRANE[style], d[1] == "Linen" and LINEN or PAL[d[1]])
					p:SetAttribute("FormTint", style == "Ossuary" and "None" or "WingPalette")
				elseif p.Name:match("Frame$") then
					dress(p, "Bone", FIN[d[2]])
					p:SetAttribute("FormTint", "WingFinish")
				end
				p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.Massless = true
			end
		end
		m:SetAttribute("FormKind", "Wing"); m:SetAttribute("FormStyle", style); m:SetAttribute("FormSide", side)
		m:SetAttribute("FormYaw", 180); m:SetAttribute("AttachFromTorso", WING_ATTACH)
	elseif hstyle then
		for _, p in ipairs(m:GetDescendants()) do
			if p:IsA("MeshPart") then
				local isTip = p.Name:match("Tip$") ~= nil
				dress(p, "Horn", isTip and FIN.Gilded or FIN.Obsidian)
				p:SetAttribute("FormTint", isTip and "HornTip" or "HornFinish")
				p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.Massless = true
			end
		end
		m:SetAttribute("FormKind", "Horns"); m:SetAttribute("FormStyle", hstyle)
		m:SetAttribute("FormYaw", 180); m:SetAttribute("AttachFromHead", Vector3.zero)
	else
		continue
	end
	m.Parent = forms
	table.insert(report, m.Name)
end
-- anchors for Controllers.Character.FormParts: wings place by RootPart (the build origin, 3 studs below the Torso
-- centre); horns by a FormAnchor attachment at the head centre. Build-axes centres from forms_fit.json; the imported
-- models face +Z, so the model-frame offset is (-x, y, -z).
local HC = { Ram = { "RamHorns", 0.001, 0.5938, 0.3011 }, Demon = { "DemonHorns", 0, 0.8624, 0.6458 },
	Wendigo = { "WendigoHorns", 0, 1.2233, 0.1207 }, Thorn = { "ThornHorns", 0, 0.8015, 0.2038 },
	Broken = { "BrokenHorns", 0.04, 0.8608, 0.6444 }, Sovereign = { "SovereignHorns", -0.001, 1.2124, 0.1155 },
	Bull = { "BullHorns", 0, 0.5172, -0.4377 } }
for style, c in pairs(HC) do
	local m = forms:FindFirstChild("NHHorns_" .. style)
	if not m then continue end
	local main = m[c[1]]
	local old = main:FindFirstChild("FormAnchor")
	if old then old:Destroy() end
	local a = Instance.new("Attachment")
	a.Name = "FormAnchor"
	a.Parent = main
	a.WorldCFrame = CFrame.new(main.Position - Vector3.new(-c[2], c[3], -c[4]))
	m.PrimaryPart = main
end
for _, m in ipairs(forms:GetChildren()) do
	if m.Name:match("^NHWing") then m.PrimaryPart = m:FindFirstChild("RootPart") end
end
table.sort(report)
return #report .. " moved to " .. forms:GetFullName() .. ": " .. table.concat(report, ", ")
