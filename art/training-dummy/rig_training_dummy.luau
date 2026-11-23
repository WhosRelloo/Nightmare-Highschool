--[[
	NH Training Dummy: build a complete R6 rig from the imported MeshParts (Studio command bar, EDIT mode).

	Before running: import NHDummy_TrainingDummy.fbx (or fbx/NH_TrainingDummy.fbx) and leave the imported model in
	Workspace. The script finds it under either name and gives each MeshPart its SurfaceAppearance from TEXTURES
	(the group image ids uploaded 2026-11-13).

	MODE = "build": makes a new R6 model "NH Training Dummy" next to the imported kit, with a Humanoid (RigType R6)
	        and Animator, a HumanoidRootPart, the six stock R6 Motor6Ds (RootJoint, Neck, Left/Right Shoulder,
	        Left/Right Hip, with the stock C0/C1, so every R6 animation plays unchanged) and the stock R6 attachments
	        (grip, shoulder, foot, hat, face, waist and so on).
	MODE = "swap": replaces the parts of every R6 rig in SWAP_FOLDER with the dummy MeshParts. It keeps those rigs'
	        own Motor6Ds, attachments, scripts and attributes, which suits the combat dummies in
	        ServerScriptService.Services.Studio.Dummy.Npcs.

	Only use this in NH Combat Test (or a copy). Never use it in the production place.
]]

local MODE = "build" -- "build" | "swap"
local KIT = workspace:FindFirstChild("NHDummy_TrainingDummy") or workspace:FindFirstChild("NH_TrainingDummy")
local SWAP_FOLDER = game:GetService("ServerScriptService").Services.Studio.Dummy.Npcs
local ANCHOR = false -- anchor the HumanoidRootPart of the built dummy (a static target)

assert(KIT, "import the FBX first (model NHDummy_TrainingDummy or NH_TrainingDummy in Workspace)")
local NAMES = { "Head", "Torso", "Left Arm", "Right Arm", "Left Leg", "Right Leg" }
for _, n in NAMES do
	assert(KIT:FindFirstChild(n), "kit is missing " .. n)
end

-- texture sets (group 15981569 image ids): { color, normal, roughness, metalness }
local TEXTURES = {
	Head = { 90720393713973, 72363495474083, 126110504698334, 140283783889253 },
	Torso = { 109506468309208, 118756881567200, 116033294607755, 84948339306528 },
	Limbs = { 104824909650697, 133613699384500, 96622949065240, 120915706016519 },
}
for _, n in NAMES do
	local set = TEXTURES[n] or TEXTURES.Limbs
	local part = KIT[n]
	local sa = part:FindFirstChildOfClass("SurfaceAppearance") or Instance.new("SurfaceAppearance")
	sa.Name = "NHDummy_" .. ((n == "Head" or n == "Torso") and n or "Limbs")
	sa.ColorMap = "rbxassetid://" .. set[1]
	sa.NormalMap = "rbxassetid://" .. set[2]
	sa.RoughnessMap = "rbxassetid://" .. set[3]
	sa.MetalnessMap = "rbxassetid://" .. set[4]
	sa.AlphaMode = Enum.AlphaMode.Overlay
	sa.Parent = part
end

-- stock R6 joints: { name, parent part, Part0, Part1, C0, C1 }
local JOINTS = {
	{ "RootJoint", "HumanoidRootPart", "HumanoidRootPart", "Torso",
		CFrame.new(0, 0, 0, -1, 0, 0, 0, 0, 1, 0, 1, -0), CFrame.new(0, 0, 0, -1, 0, 0, 0, 0, 1, 0, 1, -0) },
	{ "Neck", "Torso", "Torso", "Head",
		CFrame.new(0, 1, 0, -1, 0, 0, 0, 0, 1, 0, 1, -0), CFrame.new(0, -0.5, 0, -1, 0, 0, 0, 0, 1, 0, 1, -0) },
	{ "Right Shoulder", "Torso", "Torso", "Right Arm",
		CFrame.new(1, 0.5, 0, 0, 0, 1, 0, 1, -0, -1, 0, 0), CFrame.new(-0.5, 0.5, 0, 0, 0, 1, 0, 1, -0, -1, 0, 0) },
	{ "Left Shoulder", "Torso", "Torso", "Left Arm",
		CFrame.new(-1, 0.5, 0, 0, 0, -1, 0, 1, 0, 1, 0, 0), CFrame.new(0.5, 0.5, 0, 0, 0, -1, 0, 1, 0, 1, 0, 0) },
	{ "Right Hip", "Torso", "Torso", "Right Leg",
		CFrame.new(1, -1, 0, 0, 0, 1, 0, 1, -0, -1, 0, 0), CFrame.new(0.5, 1, 0, 0, 0, 1, 0, 1, -0, -1, 0, 0) },
	{ "Left Hip", "Torso", "Torso", "Left Leg",
		CFrame.new(-1, -1, 0, 0, 0, -1, 0, 1, 0, 1, 0, 0), CFrame.new(-0.5, 1, 0, 0, 0, -1, 0, 1, 0, 1, 0, 0) },
}

-- stock R6 attachments: { part, name, position, orientation (degrees) }
local ATTACHMENTS = {
	{ "HumanoidRootPart", "RootAttachment", Vector3.zero },
	{ "Head", "FaceCenterAttachment", Vector3.zero },
	{ "Head", "FaceFrontAttachment", Vector3.new(0, 0, -0.6) },
	{ "Head", "HairAttachment", Vector3.new(0, 0.6, 0) },
	{ "Head", "HatAttachment", Vector3.new(0, 0.6, 0) },
	{ "Torso", "NeckAttachment", Vector3.new(0, 1, 0) },
	{ "Torso", "BodyFrontAttachment", Vector3.new(0, 0, -0.5) },
	{ "Torso", "BodyBackAttachment", Vector3.new(0, 0, 0.5) },
	{ "Torso", "LeftCollarAttachment", Vector3.new(-1, 1, 0) },
	{ "Torso", "RightCollarAttachment", Vector3.new(1, 1, 0) },
	{ "Torso", "WaistFrontAttachment", Vector3.new(0, -1, -0.5) },
	{ "Torso", "WaistCenterAttachment", Vector3.new(0, -1, 0) },
	{ "Torso", "WaistBackAttachment", Vector3.new(0, -1, 0.5) },
	{ "Left Arm", "LeftShoulderAttachment", Vector3.new(0, 1, 0) },
	{ "Left Arm", "LeftGripAttachment", Vector3.new(0, -1, 0), Vector3.new(-90, 0, 0) },
	{ "Right Arm", "RightShoulderAttachment", Vector3.new(0, 1, 0) },
	{ "Right Arm", "RightGripAttachment", Vector3.new(0, -1, 0), Vector3.new(-90, 0, 0) },
	{ "Left Leg", "LeftFootAttachment", Vector3.new(0, -1, 0) },
	{ "Right Leg", "RightFootAttachment", Vector3.new(0, -1, 0) },
}

local function dressPart(src, name)
	local mp = src:Clone()
	mp.Name = name
	mp.Anchored = false
	mp.CanCollide = (name == "Torso" or name == "Head")
	if mp:IsA("MeshPart") then
		mp.CollisionFidelity = Enum.CollisionFidelity.Box
		mp.DoubleSided = false
	end
	return mp
end

local function build()
	local model = Instance.new("Model")
	model.Name = "NH Training Dummy"
	local parts = {}

	local hrp = Instance.new("Part")
	hrp.Name = "HumanoidRootPart"
	hrp.Size = Vector3.new(2, 2, 1)
	hrp.Transparency = 1
	hrp.CanCollide = false
	hrp.Anchored = ANCHOR
	hrp.CFrame = CFrame.new(KIT.Torso.Position + Vector3.new(8, 0, 0)) -- beside the kit, facing -Z
	hrp.Parent = model
	parts.HumanoidRootPart = hrp
	for _, n in NAMES do
		parts[n] = dressPart(KIT[n], n)
		parts[n].Parent = model
	end

	-- joints, placing each Part1 from its Part0: Part1 = Part0 * C0 * C1:Inverse()
	for _, j in JOINTS do
		local name, holder, p0, p1, c0, c1 = table.unpack(j)
		local m = Instance.new("Motor6D")
		m.Name = name
		m.Part0, m.Part1 = parts[p0], parts[p1]
		m.C0, m.C1 = c0, c1
		m.MaxVelocity = 0.1
		parts[p1].CFrame = parts[p0].CFrame * c0 * c1:Inverse()
		m.Parent = parts[holder]
	end

	for _, a in ATTACHMENTS do
		local at = Instance.new("Attachment")
		at.Name = a[2]
		at.Position = a[3]
		if a[4] then at.Orientation = a[4] end
		at.Parent = parts[a[1]]
	end

	local hum = Instance.new("Humanoid")
	hum.RigType = Enum.HumanoidRigType.R6
	hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	Instance.new("Animator").Parent = hum
	hum.Parent = model
	model.PrimaryPart = hrp
	model.Parent = workspace
	print("[NH dummy] built", model:GetFullName())
	return model
end

local function swap()
	for _, rig in SWAP_FOLDER:GetChildren() do
		if not rig:FindFirstChildOfClass("Humanoid") or not rig:FindFirstChild("Torso") then continue end
		-- the combat dummies are scaled R6 rigs (0.9, ParryTrade 0.8): scale the meshes with the rig's own joints
		local s = rig.Torso.Size.Y / 2
		for _, n in NAMES do
			local old = rig:FindFirstChild(n)
			if not old then warn(rig.Name, "missing", n) continue end
			local mp = dressPart(KIT[n], n)
			mp.Size = KIT[n].Size * s
			mp.CFrame = old.CFrame
			mp.Anchored, mp.CanCollide, mp.CanQuery, mp.CanTouch, mp.Massless =
				old.Anchored, old.CanCollide, old.CanQuery, old.CanTouch, old.Massless
			mp.CollisionGroup = old.CollisionGroup
			for _, ch in old:GetChildren() do -- keep joints, attachments, welds, scripts; drop the head mesh and face
				if not (ch:IsA("DataModelMesh") or ch:IsA("Decal")) then ch.Parent = mp end
			end
			for k, v in old:GetAttributes() do mp:SetAttribute(k, v) end
			mp.Parent = rig
			for _, d in rig:GetDescendants() do
				if d:IsA("JointInstance") or d:IsA("WeldConstraint") then
					if d.Part0 == old then d.Part0 = mp end
					if d.Part1 == old then d.Part1 = mp end
				end
			end
			old:Destroy()
		end
		for _, c in rig:GetChildren() do -- clothing / body colours / R6 char meshes would fight the SurfaceAppearance
			if c:IsA("Clothing") or c:IsA("ShirtGraphic") or c:IsA("CharacterMesh") or c:IsA("BodyColors") then c:Destroy() end
		end
		print("[NH dummy] swapped", rig:GetFullName())
	end
end

if MODE == "swap" then swap() else build() end
