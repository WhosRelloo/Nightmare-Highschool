--[[
	RegionBoxes (shared). ReplicatedStorage.Functions.RegionBoxes   (ambience foundations, 2.16.0)
	Which Config.Regions place a point is in, from the invisible boxes in workspace.Regions (each with the attribute
	RegionId). Where boxes overlap the highest Priority wins, then the smaller box (the same rule as
	Controllers.World.Regions). The box list stays live: boxes added, moved or resized later are picked up.
	Used by the soundscape (a place's bed) and the room reverb, so they work on any place that has region boxes,
	the Map included, without the region cards.
	API: At(Position) -> RegionId?
]]
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local Config = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`Regions`))

local RegionBoxes = {}
local Boxes = {} :: { BasePart }
local Watching = nil :: Instance?

local function add(B: Instance)
	if B:IsA(`BasePart`) and Config.Defs[B:GetAttribute(`RegionId`) or ``] and not table.find(Boxes, B) then
		table.insert(Boxes, B)
	end
end

local function watch()
	local F = workspace:FindFirstChild(`Regions`)
	if not F or F == Watching then return end
	Watching = F
	table.clear(Boxes)
	F.ChildAdded:Connect(add)
	F.ChildRemoved:Connect(function(B)
		local I = table.find(Boxes, B :: any)
		if I then table.remove(Boxes, I) end
	end)
	for _, B in F:GetChildren() do add(B) end
end

function RegionBoxes.At(Pos: Vector3): string?
	if not Watching or not Watching.Parent then watch() end
	local Best, BestP, BestV = nil, -math.huge, math.huge
	for _, B in Boxes do
		local L = B.CFrame:PointToObjectSpace(Pos)
		local H = B.Size / 2
		if math.abs(L.X) <= H.X and math.abs(L.Y) <= H.Y and math.abs(L.Z) <= H.Z then
			local Id = B:GetAttribute(`RegionId`)
			local Def = Config.Defs[Id]
			local P = Def and Def.Priority or 0
			local V = B.Size.X * B.Size.Y * B.Size.Z
			if Def and (P > BestP or (P == BestP and V < BestV)) then
				Best, BestP, BestV = Id, P, V
			end
		end
	end
	return Best
end

return RegionBoxes
