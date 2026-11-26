-- anatomy_models_edit (Task 8 step 5): every Anatomy prop the bench needs is described by ReplicatedStorage.Anatomy.Layout
-- (and, once the owner has imported the FBX files, present in ReplicatedStorage.Anatomy.Models with the same pieces).
-- Clipping is proven in Blender (export_bench.py runs clipcheck on the rest pose and refuses to export on any hit).
local RS = game.ReplicatedStorage
local L = require(RS.Anatomy.Layout)
local A = require(RS.Config.Anatomy)
local fails = {}
local function need(c, msg) if not c then table.insert(fails, msg) end end
for _, Sp in A.Species do
	local P = L.Props[Sp.Id]
	need(P, "no layout for " .. Sp.Id)
	if P then
		for _, O in Sp.Organs do need(P.Pieces[O.Id] and P.Bones[O.Id], Sp.Id .. " organ " .. O.Id) end
		need(P.Pieces.Plate and P.Bones.PlateHinge and P.Bones.PlateHinge.Axis, Sp.Id .. " Plate/PlateHinge")
		need(P.Pieces.SideKey and P.Bones.SideKey and P.Bones.SideKey.Axis, Sp.Id .. " SideKey")
		need(P.Pieces.Body, Sp.Id .. " Body")
		for i = 1, 24 do need(P.Attach[string.format("Seam%02d", i)], Sp.Id .. " Seam" .. i) end
		for _, St in Sp.Steps do
			if St.Target == "WingPlate" then for i = 1, St.Count do need(P.Pieces["WingPlate" .. i] and P.Attach["WingPlate" .. i], Sp.Id .. " WingPlate" .. i) end end
			if St.Target == "HiddenSeam" then need(P.Attach.HiddenSeam, Sp.Id .. " HiddenSeam") end
		end
		for name, pc in P.Pieces do need(pc.Tris <= 20000, Sp.Id .. " " .. name .. " over 20k tris") need(P.Bones[pc.Bone], Sp.Id .. " " .. name .. " bone") end
	end
end
for i, T in A.Tools do
	local P = L.Props["Tool" .. T]
	need(P and P.Attach.Grip and P.Attach.Tip and P.Pieces.Main, "tool " .. tostring(T))
	local S = L.Props.BenchSet.Attach["Slot" .. i]
	need(S and S.Tool == T, "BenchSet Slot" .. i .. " for " .. tostring(T))
end
for i = 1, 5 do need(L.Props.BenchSet.Pieces["Chalk" .. i .. "Glow"], "Chalk" .. i) end
local Models = RS.Anatomy:FindFirstChild("Models")
local imported = 0
if Models then
	for prop, P in L.Props do
		local M = Models:FindFirstChild(prop)
		if M then
			imported += 1
			for name in P.Pieces do need(M:FindFirstChild(name, true), "model " .. prop .. " missing " .. name) end
		end
	end
end
if #fails > 0 then return "FAIL anatomy_models_edit: " .. table.concat(fails, "; ") end
return string.format("PASS anatomy_models_edit (layout: %d props; imported models: %d)", (function() local n = 0 for _ in L.Props do n += 1 end return n end)(), imported)
