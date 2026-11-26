-- tools/electives/stage/anatomy_import.lua (Edit, after the owner imports the Anatomy FBX files; not run yet).
-- Import each art/props/fbx/Anat<Prop>.fbx with "Import as rig" OFF into Workspace (it arrives as a Model named
-- Anat<Prop> holding MeshParts Anat<Prop>_<Piece>). This script then, per prop in ReplicatedStorage.Anatomy.Layout:
--   * renames each MeshPart to its piece name and sets its Size and CFrame from the layout (bench space, studs), so
--     the ~100x import scale and any offset do not matter;
--   * anchors it, turns collisions off, dresses *Glow pieces as Neon and *Glass pieces as Glass;
--   * adds a SurfaceAppearance from TEXTURES (fill it in with the group image ids once the owner has uploaded
--     art/props/textures/Anat*_{color,normal,rough,metal}.png; PUBLISH_LIST.md lists them);
--   * moves the model to ReplicatedStorage.Anatomy.Models.<Prop>, where the bench renderer prefers it to its stand-ins.
-- Screenshot a prop in a viewport before trusting it (Pipeline-Lessons).
local TEXTURES = {
	-- ["AnatFrog_Body"] = { Color = 0, Normal = 0, Rough = 0, Metal = 0 },
}
local RS = game.ReplicatedStorage
local L = require(RS.Anatomy.Layout)
local Models = RS.Anatomy:FindFirstChild("Models") or Instance.new("Folder")
Models.Name = "Models"
Models.Parent = RS.Anatomy
local out = {}
for prop, P in L.Props do
	local M = workspace:FindFirstChild("Anat" .. prop)
	if not M then continue end
	local done, missing = 0, {}
	for piece, pc in P.Pieces do
		local part = M:FindFirstChild("Anat" .. prop .. "_" .. piece, true) or M:FindFirstChild(piece, true)
		if not (part and part:IsA("MeshPart")) then table.insert(missing, piece) continue end
		local tex = TEXTURES["Anat" .. prop .. "_" .. piece]
		part.Name = piece
		part.Size = pc.Size
		part.CFrame = CFrame.new(pc.Centre)
		part.Anchored = true
		part.CanCollide, part.CanTouch, part.CanQuery = false, false, true
		if pc.Glow then part.Material = Enum.Material.Neon part.Color = pc.Color end
		if pc.Glass then part.Material = Enum.Material.Glass part.Transparency = 0.6 part.Color = pc.Color end
		if tex then
			local SA = part:FindFirstChildOfClass("SurfaceAppearance") or Instance.new("SurfaceAppearance")
			SA.ColorMap = "rbxassetid://" .. tex.Color
			SA.NormalMap = "rbxassetid://" .. tex.Normal
			SA.RoughnessMap = "rbxassetid://" .. tex.Rough
			SA.MetalnessMap = "rbxassetid://" .. tex.Metal
			SA.Parent = part
		end
		done += 1
	end
	M.Name = prop
	local old = Models:FindFirstChild(prop)
	if old then old:Destroy() end
	M.Parent = Models
	table.insert(out, string.format("%s: %d pieces%s", prop, done, #missing > 0 and (" MISSING " .. table.concat(missing, ",")) or ""))
end
return #out > 0 and table.concat(out, "\n") or "no Anat* models in Workspace: import the FBX files first"
