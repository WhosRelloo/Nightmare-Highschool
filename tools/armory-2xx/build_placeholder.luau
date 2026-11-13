--[[
	Armory placeholder booth (owner 2026-11-12: "Make a placeholder area (not too big)"). Run in Studio's Edit
	datamodel with BASE, SRC and TAG_CORE set at the top (see the two calls at the bottom).

	An open-front booth, 22 x 14 studs, 11 tall: slate floor, brick back and side walls, a roof with two warm
	lights. Inside: the batch-46 ArmoryCounter, KatanaStand, PlateArmourStand, ShieldWall and ArmorySign (cloned from
	the props showcase, same facing relative to their wall), the shopkeeper's spot (tag NHArmoryKeeper: the server
	stands the armourer there) and a class locker (tag NHClassLocker) to switch class.
	Everything is in one folder, "Armory Placeholder", so it can be moved or deleted in one go. In the Map the
	folder and its parts are tagged NHCore.
]]
local CS = game:GetService(`CollectionService`)

local function build(Base: CFrame, Src: Instance, TagCore: boolean): string
	local W, D, H = 22, 14, 11
	local Old = workspace:FindFirstChild(`Armory Placeholder`)
	if Old then Old:Destroy() end
	local F = Instance.new(`Folder`)
	F.Name = `Armory Placeholder`
	F:SetAttribute(`NHArmoryPlaceholder`, true)
	local FloorTop = 0.4

	local function part(Name: string, Size: Vector3, At: CFrame, Color: Color3, Mat: Enum.Material): Part
		local P = Instance.new(`Part`)
		P.Name = Name
		P.Anchored = true
		P.Size = Size
		P.CFrame = Base * At
		P.Color = Color
		P.Material = Mat
		P.TopSurface = Enum.SurfaceType.Smooth
		P.BottomSurface = Enum.SurfaceType.Smooth
		P.Parent = F
		return P
	end

	local Stone = Color3.fromRGB(40, 36, 38)
	local Brick = Color3.fromRGB(66, 46, 42)
	part(`Floor`, Vector3.new(W + 2, 0.4, D + 1), CFrame.new(0, 0.2, 0.5), Stone, Enum.Material.Slate)
	part(`BackWall`, Vector3.new(W + 2, H, 1), CFrame.new(0, FloorTop + H / 2, D / 2 + 0.5), Brick, Enum.Material.Brick)
	part(`SideWallL`, Vector3.new(1, H, D), CFrame.new(-(W / 2 + 0.5), FloorTop + H / 2, 0), Brick, Enum.Material.Brick)
	part(`SideWallR`, Vector3.new(1, H, D), CFrame.new(W / 2 + 0.5, FloorTop + H / 2, 0), Brick, Enum.Material.Brick)
	local Roof = part(`Roof`, Vector3.new(W + 3, 0.6, D + 2.5), CFrame.new(0, FloorTop + H + 0.3, 0.25), Color3.fromRGB(30, 28, 32), Enum.Material.Slate)
	for _, X in { -5, 5 } do
		local A = Instance.new(`Attachment`)
		A.Position = Vector3.new(X, -1.2, 0)
		A.Parent = Roof
		local L = Instance.new(`PointLight`)
		L.Color = Color3.fromRGB(255, 196, 140)
		L.Brightness = 1.4
		L.Range = 18
		L.Shadows = true
		L.Parent = A
	end

	-- the showcase's facing: from its wall toward the props
	local Wall = Src:FindFirstChild(`ArmoryWall`)
	local Counter = Src:FindFirstChild(`ArmoryCounter_Showcase`)
	assert(Wall and Counter, `need ArmoryWall and ArmoryCounter_Showcase in {Src:GetFullName()}`)
	local Axes = { { Wall.CFrame.RightVector, Wall.Size.X }, { Wall.CFrame.LookVector, Wall.Size.Z } }
	table.sort(Axes, function(A, B) return A[2] < B[2] end)
	local N = Axes[1][1]
	if N:Dot(Counter:GetPivot().Position - Wall.Position) < 0 then N = -N end
	local ShowFrame = CFrame.lookAt(Vector3.zero, N)
	local ShowFloor = Counter:GetPivot().Position.Y

	local Placed = {}
	-- Floor props: bounding-box centre at (X, Z) in booth space, bottom on the floor. Wall props: pivot on the back
	-- wall's face at the showcase's height above its floor.
	local function prop(Name: string, X: number, Z: number?, Wall: boolean?)
		local S = Src:FindFirstChild(Name .. `_Showcase`)
		if not S then table.insert(Placed, `missing {Name}`) return end
		local M = S:Clone()
		M.Name = Name
		local Rel = ShowFrame:ToObjectSpace(S:GetPivot()).Rotation
		local Rot = Base.Rotation * Rel
		if Wall then
			local Up = S:GetPivot().Position.Y - ShowFloor
			M:PivotTo(CFrame.new((Base * CFrame.new(X, FloorTop + Up, D / 2)).Position) * Rot)
		else
			M:PivotTo(CFrame.new((Base * CFrame.new(X, FloorTop, Z or 0)).Position) * Rot)
			local BB, Size = M:GetBoundingBox()
			local Want = (Base * CFrame.new(X, FloorTop + Size.Y / 2, Z or 0)).Position
			M:PivotTo(M:GetPivot() + (Want - BB.Position))
		end
		M.Parent = F
		table.insert(Placed, Name)
		return M
	end
	local C = prop(`ArmoryCounter`, 0, -0.5)
	if C then CS:AddTag(C, `NHArmoryShop`) end
	prop(`KatanaStand`, -6.5, D / 2 - 1.2)
	prop(`PlateArmourStand`, 7, D / 2 - 1.3)
	prop(`ShieldWall`, 0, nil, true)
	prop(`ArmorySign`, -W / 2 + 2.5, nil, true)

	-- where the armourer stands (Services.Features.Armory), behind the counter, facing out
	local Spot = part(`ArmourerSpot`, Vector3.new(2, 1, 1), CFrame.new(0, FloorTop + 0.5, 2.6), Color3.fromRGB(200, 60, 60), Enum.Material.SmoothPlastic)
	Spot.Transparency = 0.6
	Spot.CanCollide = false
	Spot:SetAttribute(`KeeperName`, `Armourer`)
	CS:AddTag(Spot, `NHArmoryKeeper`)

	-- a class locker (Features.ClassLocker) inside the right wall, facing into the booth
	local Lk = part(`ClassLocker`, Vector3.new(3, 7, 2.4), CFrame.new(W / 2 - 1.2, FloorTop + 3.5, -2.5) * CFrame.Angles(0, math.rad(90), 0),
		Color3.fromRGB(52, 62, 70), Enum.Material.DiamondPlate)
	local G = Instance.new(`SurfaceGui`)
	G.Face = Enum.NormalId.Front
	G.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	G.PixelsPerStud = 50
	local T = Instance.new(`TextLabel`)
	T.BackgroundTransparency = 1
	T.Size = UDim2.fromScale(1, 0.2)
	T.Position = UDim2.fromScale(0, 0.12)
	T.Font = Enum.Font.Fantasy
	T.TextScaled = true
	T.TextColor3 = Color3.fromRGB(226, 190, 120)
	T.Text = `CLASS LOCKER`
	T.Parent = G
	G.Parent = Lk
	CS:AddTag(Lk, `NHClassLocker`)

	if TagCore then
		CS:AddTag(F, `NHCore`)
		for _, Ch in F:GetChildren() do CS:AddTag(Ch, `NHCore`) end
	end
	F.Parent = workspace
	return table.concat(Placed, `, `)
end

-- Map (placeId 111107083446202): east of the Locker Room Placeholder, open side facing it (west)
-- return build(CFrame.lookAt(Vector3.new(-838, -7.96, -101), Vector3.new(-839, -7.96, -101)), workspace.Armory, true)
-- NH Combat Test (placeId 98950102230473): south of the school, open side facing south
-- return build(CFrame.lookAt(Vector3.new(72, 0.9, -8), Vector3.new(72, 0.9, -9)), workspace.NHPropsShowcase.Armory, false)
return build
