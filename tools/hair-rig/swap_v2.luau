-- Hair rigs v2 (the locks carry their strands, for the accessories' hair tuck): swap each catalog hair's Handle for
-- the owner's import of art/group-upload-hair-v2/<RigSource>.fbx. NH Combat Test, Edit; run once the 35 imports are in
-- the workspace (File > Import 3D, one model per hair, any folder). Re-runnable: a hair already on v2 is skipped.
--
-- For every ReplicatedStorage.NHHairCatalog.Hair_<id> (Accessory, attribute RigSource):
--   * the imported model named <RigSource> (or a MeshPart named Hair_<RigSource>) with bones is found;
--   * its size must equal the old Handle's (the same mesh, only the weights changed; bones too: checked by name and
--     position), else it is skipped and reported;
--   * the old accessory is backed up to ServerStorage.NH_Backup.Hair_v1, the new MeshPart becomes the Handle with
--     the old Handle's TextureID, colour, material, attachments (HairAttachment) and values, and NHHairRig = 2.
local RS = game:GetService("ReplicatedStorage")
local SS = game:GetService("ServerStorage")
local Cat = RS:FindFirstChild("NHHairCatalog")
assert(Cat, "no NHHairCatalog")
local bk = SS:FindFirstChild("NH_Backup") or Instance.new("Folder", SS)
bk.Name = "NH_Backup"
local keep = bk:FindFirstChild("Hair_v1") or Instance.new("Folder", bk)
keep.Name = "Hair_v1"
local report = {}
-- hairs whose catalog rig differs from the source rig the tucks were solved for (same mesh, different lock bones):
-- the swap takes the source rig, as long as every bone the two share sits where it did
-- (Hair_9000000002 Males_Super_Messy_Long_Hair: catalog 16 bones with Lock5_3; source 17 with Lock3_3 and Lock4_3)
local NEW_BONES_OK = { Males_Super_Messy_Long_Hair = true }

local function findImport(src)
	for _, d in ipairs(workspace:GetDescendants()) do
		if d:IsA("MeshPart") and d:FindFirstChildWhichIsA("Bone", true)
			and (d.Name == "Hair_" .. src or (d.Parent and d.Parent:IsA("Model") and d.Parent.Name == src)) then
			return d
		end
	end
	return nil
end

local function restOf(b)
	local cf = b.CFrame
	local p = b.Parent
	while p and p:IsA("Bone") do
		cf = p.CFrame * cf
		p = p.Parent
	end
	return cf
end

for _, A in ipairs(Cat:GetChildren()) do
	local src = A:GetAttribute("RigSource")
	local old = A:FindFirstChild("Handle")
	if not (src and old and old:IsA("MeshPart")) then continue end
	if old:GetAttribute("NHHairRig") == 2 then
		table.insert(report, A.Name .. " " .. src .. ": already v2")
		continue
	end
	local new = findImport(src)
	if not new then
		table.insert(report, A.Name .. " " .. src .. ": no import found")
		continue
	end
	-- Import 3D may read the FBX in centimetres (100x): scale the mesh and every bone position back (a uniform scale
	-- keeps the rig exact: each bone's offset from its parent shrinks, its turn is unchanged)
	local ratio = new.Size.Magnitude / old.Size.Magnitude
	if math.abs(ratio - 100) < 0.5 then
		new.Size = new.Size / 100
		for _, b in ipairs(new:GetDescendants()) do
			if b:IsA("Bone") then b.CFrame = CFrame.new(b.CFrame.Position / 100) * b.CFrame.Rotation end
		end
	end
	if (new.Size - old.Size).Magnitude > 0.02 then
		table.insert(report, string.format("%s %s: size %s, old %s: skipped", A.Name, src, tostring(new.Size), tostring(old.Size)))
		continue
	end
	-- the same bones, where the old ones were
	local worst, missing = 0, 0
	for _, b in ipairs(old:GetDescendants()) do
		if b:IsA("Bone") then
			local nb = new:FindFirstChild(b.Name, true)
			if not (nb and nb:IsA("Bone")) then
				if not NEW_BONES_OK[src] then missing += 1 end
			else
				worst = math.max(worst, (restOf(nb).Position - restOf(b).Position).Magnitude)
			end
		end
	end
	if missing > 0 or worst > 0.01 then
		table.insert(report, string.format("%s %s: bones differ (%d missing, %.3f off): skipped", A.Name, src, missing, worst))
		continue
	end
	if not keep:FindFirstChild(A.Name) then
		A:Clone().Parent = keep
	end
	new.Anchored = old.Anchored
	new.CanCollide, new.CanTouch, new.CanQuery, new.Massless = old.CanCollide, old.CanTouch, old.CanQuery, old.Massless
	new.TextureID = old.TextureID
	new.Color, new.Material, new.Transparency = old.Color, old.Material, old.Transparency
	new.CastShadow = old.CastShadow
	pcall(function() new.DoubleSided = old.DoubleSided end)   -- not settable from every context
	for k, v in pairs(old:GetAttributes()) do new:SetAttribute(k, v) end
	for _, c in ipairs(old:GetChildren()) do
		if not c:IsA("Bone") and not c:IsA("Weld") and not c:IsA("WeldConstraint") then c.Parent = new end
	end
	new.CFrame = old.CFrame
	new:SetAttribute("NHHairRig", 2)
	local model = new.Parent
	old:Destroy()
	new.Name = "Handle"
	new.Parent = A
	if model and model:IsA("Model") and model ~= A and #model:GetChildren() == 0 then model:Destroy() end
	table.insert(report, A.Name .. " " .. src .. ": v2")
end
table.sort(report)
return table.concat(report, "\n")
