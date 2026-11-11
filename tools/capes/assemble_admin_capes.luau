--[[
	Admin capes (NH Combat Test, Edit mode): turn the owner's imported FBX models into ReplicatedStorage.NHCapes templates.

	Run in the command bar / execute_luau after the owner has imported art/group-upload-capes/NHCape_<Set>.fbx
	(File > Import 3D, group creator) and bulk-imported the 20 maps. Fill IDS with the group asset ids read by name.

	For each set it:
	  * finds the imported model (workspace descendant named NHCape_<Set>, or a Model holding a MeshPart "CapeBody")
	  * renames it to the cape's display name, makes CapeBody the PrimaryPart, non-colliding, massless
	  * gives CapeBody a SurfaceAppearance (Color/Normal/Roughness/Metalness, AlphaMode Overlay)
	  * sets NH_TorsoFit from the builder's layout (the CapeBody's CFrame on a 2 x 2 x 1 torso; the importer re-centres
	    the mesh on its bounding box, so this is that box's centre in torso space)
	  * checks the bone tree CapeSway expects (Root > H<n> > C<n>_<k>)
	  * moves it to ReplicatedStorage.NHCapes (an older copy there is kept in ServerStorage.NH_Backup.AdminCapes_pre)
]]
-- group 15981569 image ids, read by name (NHCape_<Set>_<kind>) on 2026-11-10
local IDS = {
	WardenMantle = { color = 116672460086178, normal = 133407446101457, roughness = 100541077512381, metalness = 122698314959326 },
	ReaperShroud = { color = 102870607206081, normal = 103076532309349, roughness = 113957250202381, metalness = 103288338312897 },
	DuelistCape = { color = 82829571371610, normal = 90163964254307, roughness = 83012266523685, metalness = 122167191814576 },
	CaptainGreatcape = { color = 81424694842197, normal = 105599732977835, roughness = 84176605512600, metalness = 108222512683315 },
	MidnightCollar = { color = 134877268273695, normal = 87099915353183, roughness = 110805795304970, metalness = 102327465896233 },
}
local SETS = {
	WardenMantle = { Name = "Night Warden's Mantle", Fit = Vector3.new(0.019, 0.533, 0.069) },
	ReaperShroud = { Name = "Reaper's Tattered Shroud", Fit = Vector3.new(-0.016, -0.674, 0.283) },
	DuelistCape = { Name = "Duelist's Shoulder Cape", Fit = Vector3.new(-0.836, 0.110, 0.178) },
	CaptainGreatcape = { Name = "Council Captain's Greatcape", Fit = Vector3.new(-0.003, -0.614, 0.337) },
	MidnightCollar = { Name = "Midnight Lord's High-Collar Cape", Fit = Vector3.new(0.015, 0.031, 0.104) },
}

local RS = game:GetService("ReplicatedStorage")
local SS = game:GetService("ServerStorage")
local store = RS:FindFirstChild("NHCapes")
local report = {}

local function findImport(set)
	for _, d in ipairs(workspace:GetDescendants()) do
		if d:IsA("Model") and (d.Name == "NHCape_" .. set) then
			return d
		end
	end
	return nil
end

for set, def in pairs(SETS) do
	local ids = IDS[set]
	local m = findImport(set)
	if not (m and ids) then
		table.insert(report, set .. ": skipped (" .. (m and "no ids" or "no import") .. ")")
		continue
	end
	local body = m:FindFirstChild("CapeBody", true)
	if not (body and body:IsA("MeshPart")) then
		table.insert(report, set .. ": no CapeBody MeshPart")
		continue
	end
	for _, n in ipairs({ "AnimationController", "InitialPoses" }) do -- the importer's rig helpers; capes don't use them
		local c = m:FindFirstChild(n)
		if c then c:Destroy() end
	end
	local old = store:FindFirstChild(def.Name)
	if old then
		local bk = SS:FindFirstChild("NH_Backup") or Instance.new("Folder", SS)
		bk.Name = "NH_Backup"
		local f = bk:FindFirstChild("AdminCapes_pre") or Instance.new("Folder", bk)
		f.Name = "AdminCapes_pre"
		old.Parent = f
	end
	m.Name = def.Name
	m.PrimaryPart = body
	for _, p in ipairs(m:GetDescendants()) do
		if p:IsA("BasePart") then
			p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch, p.Massless = true, false, false, false, true
			p.CastShadow = true
		end
	end
	body.TextureID = ""
	for _, s in ipairs(body:GetChildren()) do
		if s:IsA("SurfaceAppearance") then
			s:Destroy()
		end
	end
	local sa = Instance.new("SurfaceAppearance")
	sa.ColorMap = "rbxassetid://" .. ids.color
	sa.NormalMap = "rbxassetid://" .. ids.normal
	sa.RoughnessMap = "rbxassetid://" .. ids.roughness
	sa.MetalnessMap = "rbxassetid://" .. ids.metalness
	sa.AlphaMode = Enum.AlphaMode.Overlay
	sa.Parent = body
	m:SetAttribute("NH_TorsoFit", CFrame.new(def.Fit))
	m:SetAttribute("NHAdminCape", true)
	local bones, chain = 0, 0
	for _, b in ipairs(m:GetDescendants()) do
		if b:IsA("Bone") then
			bones += 1
			if b.Name:match("^C%d+_%d+$") then
				chain += 1
			end
		end
	end
	m.Parent = store
	table.insert(report, string.format("%s: ok, %d bones (%d chain), size %s", set, bones, chain, tostring(body.Size)))
end
return table.concat(report, "\n")
