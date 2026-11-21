-- tools/phase6-2350/stage/hometown.lua (Edit mode). Arranges the imported Wickfield props and writes the cut sets.
local ORIGIN = CFrame.new(4000, 0, 4000) -- Wickfield's corner, away from the school (doc 15 §2)
local H = workspace:FindFirstChild("Hometown") or Instance.new("Folder")
H.Name = "Hometown"
H.Parent = workspace
-- (task 10) the Blender import came in at 100x (the bus is 2100 studs long): each model is fitted to its real size in studs,
-- measured from its longest bounding-box side, so a later re-import at the right scale is left alone (scale 1)
local function take(name, into, cf, longest)
	local M = workspace:FindFirstChild(name, true)
	if not M then return name .. " MISSING" end
	local Folder = H:FindFirstChild(into) or Instance.new("Folder")
	Folder.Name = into
	Folder.Parent = H
	M.Parent = Folder
	local _, Size = M:GetBoundingBox()
	M:ScaleTo(M:GetScale() * longest / math.max(Size.X, Size.Y, Size.Z))
	M:PivotTo(ORIGIN * cf)
	-- (task 10) nothing may fall in Play: a rigged model (a RootPart, its mesh parts on Motor6Ds) is held by its root alone (its
	-- joints still animate); a plain model has every part anchored
	-- (task 10) StreamingEnabled: a model is only complete on a client near it, and Hometown.Cast clones the whole thing (the
	-- bus 60 studs away, the dog), so Wickfield's models are Persistent (sent whole to every client)
	if M:IsA("Model") then M.ModelStreamingMode = Enum.ModelStreamingMode.Persistent end
	local Root = M:FindFirstChild("RootPart")
	-- a rig part with no joint path to the root would fall in Play: those are anchored too, and named in the report
	local Joined = {}
	if Root then
		Root.Anchored = false
		for _, P in Root:GetConnectedParts(true) do Joined[P] = true end
		Joined[Root] = true
	end
	local Loose = {}
	for _, D in M:GetDescendants() do
		if D:IsA("BasePart") then
			D.Anchored = (Root == nil) or D == Root or not Joined[D]
			if Root and D ~= Root and not Joined[D] then table.insert(Loose, D.Name) end
		end
	end
	return name .. " ok" .. (#Loose > 0 and (" (anchored, no joint to the root: " .. table.concat(Loose, ", ") .. ")") or "")
end
local Report = {
	-- the stop faces -Y in Blender = -Z in Roblox; the road runs along X in front of it
	take("WFBusStop", "BusStop", CFrame.new(0, 0, 0), 20),
	take("WFBlackBus", "BlackBus", CFrame.new(30, 0.3, -5.6) * CFrame.Angles(0, math.rad(90), 0), 21),
	take("WFWickHouse", "Garden", CFrame.new(0, 0, 120), 20.7),
	take("WFKennel", "Garden", CFrame.new(14, 0, 96), 7.4),
	take("WFBiscuit", "Garden", CFrame.new(14, 0, 93), 6.4),
	take("WFPicketFence", "Garden", CFrame.new(0, 0, 80), 8.7),
	take("WFPicketGate", "Garden", CFrame.new(12, 0, 80), 6.0),
}
local Sets = workspace:FindFirstChild("NHCineSets") or Instance.new("Folder")
Sets.Name = "NHCineSets"
Sets.Parent = workspace
local function set(name, marks)
	local S = Sets:FindFirstChild(name)
	if S then S:Destroy() end
	S = Instance.new("Folder")
	S.Name = name
	S.Parent = Sets
	for mark, cf in marks do
		local P = Instance.new("Part")
		P.Name = mark
		P.Size = Vector3.one
		P.Anchored, P.CanCollide, P.CanQuery, P.CanTouch = true, false, false, false
		P.Transparency = 1
		P.CFrame = ORIGIN * cf
		P.Parent = S
	end
end
set("BusStop", {
	Stand = CFrame.new(1.5, 0.75, -1.6),                                    -- by the kerb, facing the road (-Z)
	-- (task 10) the bus faces -X (its doors, on its +Z side, face the stop; the driver sits on the far side) and the road
	-- runs along X in front of the stop: it comes in from +X. Its doors (pivot + (-5.0, 0, +2.53)) land on Stand's X.
	BusStart = CFrame.new(64.5, 0.3, -5.6) * CFrame.Angles(0, math.rad(90), 0),
	BusStop = CFrame.new(6.5, 0.3, -5.6) * CFrame.Angles(0, math.rad(90), 0),  -- the doors line up with Stand
	BusAway = CFrame.new(-85.5, 0.3, -5.6) * CFrame.Angles(0, math.rad(90), 0),
	Door = CFrame.new(1.5, 2.4, -3.1),                                       -- the doorway, mid-height (the doors' own Z)
	Board = CFrame.new(1.5, 2.9, -6.2),
	Driver = CFrame.new(1.7, 5.3, -7.0),                                     -- the driver's head, seen through the doorway
	-- cameras: the arrival from the left end of the stop looking along the road at the bus coming in; the doors from the
	-- pavement at the right; the driver from above the player's head through the doorway; the leaving from beyond the
	-- bus's tail so it recedes (the pull-away runs the bus along -X, never past a camera)
	CamWide = CFrame.new(-16, 2.4, -2),     CamLookWide = CFrame.new(4, 3.5, -5.6),
	CamDoor = CFrame.new(6, 2.3, -0.5),
	CamDriver = CFrame.new(1.6, 6.6, 0.2),
	CamAway = CFrame.new(22, 2.6, -0.5),    CamLookAway = CFrame.new(-30, 4, -5.6),
})
-- (task 11) the garden's lawn: the imported props have no ground of their own, and the player walks from the house to the
-- fence and over it (the far side too). Placeholder grass until the real map has a back garden.
do
	local Folder = H:FindFirstChild("Garden") or Instance.new("Folder")
	Folder.Name = "Garden"
	Folder.Parent = H
	local Lawn = Folder:FindFirstChild("WFGardenLawn") or Instance.new("Part")
	Lawn.Name = "WFGardenLawn"
	Lawn.Anchored = true
	Lawn.Size = Vector3.new(90, 1, 90)
	Lawn.CFrame = ORIGIN * CFrame.new(0, -0.5, 95)
	Lawn.Material = Enum.Material.Grass
	Lawn.Color = Color3.fromRGB(58, 84, 52)
	Lawn.TopSurface, Lawn.BottomSurface = Enum.SurfaceType.Smooth, Enum.SurfaceType.Smooth
	Lawn.Parent = Folder
end
-- FenceZone: where you stop at the gate to climb (z 82: the gate's collision face is at z 80.3 and your root needs about 1 stud
-- more, so a mark nearer than that can't be walked to)
-- LightWindow: the bedroom window (the house's BedSash, 3994.3 / 7.1 / 4113.2 in the world), a hair in front of it
set("Garden", {
	Start = CFrame.new(-6, 0, 104), Biscuit = CFrame.new(14, 0, 93), FenceZone = CFrame.new(12, 0, 82),
	LightWindow = CFrame.new(-5.66, 7.11, 113.0), Hide = CFrame.new(4, 0, 92),
})
return table.concat(Report, "\n")
