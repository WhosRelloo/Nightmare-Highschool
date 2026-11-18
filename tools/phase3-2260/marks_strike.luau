--!nonstrict
-- (2.26.0) The Strikethrough's set marks: Room 102 at night. Floor-level marks (feet), the 2.24.0 style: transparent,
-- non-colliding, non-querying, anchored 0.6-stud parts made with CFrame.lookAt. Re-run safe. Run in Edit.
local V = Vector3.new
local Sets = workspace:FindFirstChild("NHCineSets")
local Old = Sets:FindFirstChild("Strike")
if Old then Old:Destroy() end
local S = Instance.new("Folder")
S.Name = "Strike"
local function mark(name, pos, look, size, attrs)
	local p = Instance.new("Part")
	p.Name = name
	p.Size = size or V(0.6, 0.2, 0.6)
	p.CFrame = CFrame.lookAt(pos, look)
	p.Transparency, p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch = 1, true, false, false, false
	for k, v in pairs(attrs or {}) do p:SetAttribute(k, v) end
	p.Parent = S
end
mark("You", V(98, 1.1, 63.4), V(98, 1.1, 64.4)) -- you at Mira's desk, the chair side
mark("Rise", V(98, 1.1, 68.8), V(98, 1.1, 67.8)) -- it stands up out of the desk, on the board side
mark("RiseLow", V(98, -1.9, 68.8), V(98, -1.9, 67.8)) -- under the floor: it starts here and rises to Rise
mark("LungeTo", V(98, 1.1, 64.6), V(98, 1.1, 63.6)) -- where its lunge lands, an arm's length from You (Mira's chair is pushed aside first)
mark("DodgeTo", V(101.4, 1.1, 63.0), V(101.4, 1.1, 64.0)) -- the dodge goes to your left (+X)
mark("ThrownTo", V(95.6, 1.1, 60.4), V(95.6, 1.1, 61.4)) -- thrown back into the back-row desks
mark("TugYou", V(98, 1.1, 63.8), V(98, 1.1, 64.8)) -- behind Mira's chair (the chair mesh spans z 64.15 to 65.65)
mark("TugIt", V(98, 1.1, 68.8), V(98, 1.1, 67.8)) -- across the desk (z 65.5 to 67.5), clear of the carved top (to 68.5)
local F = Sets.Hall.File:Clone()
F.Parent = S
mark("Desk", V(98, 2.37, 66.5), V(98, 2.37, 67.5), V(3, 2.54, 1.96)) -- Mira's desk: the shove's target
mark("Wide", V(88, 7.5, 60.6), V(98, 4, 67)) -- the establishing camera
mark("Bell", V(146.1, 11.4, 57.7), V(146.1, 11.4, 56.7), nil, { BellPart = "Workspace.School.NHProps.SchoolBell_R104.SchoolBell_Bell" })
S.Parent = Sets
-- check: visible props inside each actor mark's body volume (2 x 4.2 x 0.8 above the floor; prop meshes are not queryable)
local out = { #S:GetChildren() .. " marks" }
for _, n in ipairs({ "You", "Rise", "LungeTo", "DodgeTo", "ThrownTo", "TugYou", "TugIt" }) do
	local m = S[n]
	local c = m.Position + V(0, 2.4, 0)
	local list = {}
	for _, d in ipairs(workspace:GetDescendants()) do
		if d:IsA("BasePart") and d.Transparency < 1 and d.Size.Magnitude < 30 and not d:IsDescendantOf(Sets) then
			local rel = d.CFrame:PointToObjectSpace(c)
			local h = d.Size / 2 + V(0.8, 2.1, 0.4)
			if math.abs(rel.X) < h.X and math.abs(rel.Y) < h.Y and math.abs(rel.Z) < h.Z then table.insert(list, (d:GetFullName():gsub("Workspace.School.", ""))) end
		end
	end
	table.insert(out, n .. ": " .. (#list > 0 and table.concat(list, ", ") or "clear"))
end
local bell = workspace:FindFirstChild("School") and workspace.School:FindFirstChild("NHProps")
bell = bell and bell:FindFirstChild("SchoolBell_R104")
table.insert(out, "bell part: " .. tostring(bell and bell:FindFirstChild("SchoolBell_Bell") ~= nil))
return table.concat(out, "\n")
