-- tools/phase6-2350/stage/hometown.lua (Edit mode). Arranges the imported Wickfield props and writes the cut sets.
local ORIGIN = CFrame.new(4000, 0, 4000) -- Wickfield's corner, away from the school (doc 15 §2)
local H = workspace:FindFirstChild("Hometown") or Instance.new("Folder")
H.Name = "Hometown"
H.Parent = workspace
local function take(name, into, cf)
	local M = workspace:FindFirstChild(name, true)
	if not M then return name .. " MISSING" end
	local Folder = H:FindFirstChild(into) or Instance.new("Folder")
	Folder.Name = into
	Folder.Parent = H
	M.Parent = Folder
	M:PivotTo(ORIGIN * cf)
	return name .. " ok"
end
local Report = {
	-- the stop faces -Y in Blender = -Z in Roblox; the road runs along X in front of it
	take("WFBusStop", "BusStop", CFrame.new(0, 0, 0)),
	take("WFBlackBus", "BlackBus", CFrame.new(-30, 0, -5.6) * CFrame.Angles(0, math.rad(-90), 0)),
	take("WFWickHouse", "Garden", CFrame.new(0, 0, 120)),
	take("WFKennel", "Garden", CFrame.new(14, 0, 96)),
	take("WFBiscuit", "Garden", CFrame.new(14, 0, 93)),
	take("WFPicketFence", "Garden", CFrame.new(0, 0, 80)),
	take("WFPicketGate", "Garden", CFrame.new(12, 0, 80)),
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
	BusStart = CFrame.new(-60, 0, -5.6) * CFrame.Angles(0, math.rad(-90), 0),
	BusStop = CFrame.new(-2, 0, -5.6) * CFrame.Angles(0, math.rad(-90), 0),  -- the doors line up with Stand
	BusAway = CFrame.new(90, 0, -5.6) * CFrame.Angles(0, math.rad(-90), 0),
	Door = CFrame.new(1.5, 0.75, -3.4),
	Board = CFrame.new(1.5, 2.9, -6.2),
	CamWide = CFrame.new(-14, 2.2, 6),  CamLookWide = CFrame.new(-6, 4, -5),
	CamDoor = CFrame.new(6, 3.4, -1.0), CamDriver = CFrame.new(0, 8.5, -16),
})
set("Garden", {
	Start = CFrame.new(-6, 0, 104), Biscuit = CFrame.new(14, 0, 93), FenceZone = CFrame.new(12, 0, 81),
	LightWindow = CFrame.new(0, 14, 108), Hide = CFrame.new(4, 0, 92),
})
return table.concat(Report, "\n")
