--[[
	Space (server). Services.AI.StudentBrain.Space  (phase6-strafes)
	The room checks a student needs before being moved by code: nothing solid (and a floor) along a slide, and how far
	ahead is free at waist, chest and head height. Moved verbatim from StudentBrain.Nudges (1.86.3, contact feel) so
	Nudges and StudentBrain.Gestures (the shove carry) share them.
	  Space.Clear(S, Dir, Dist) -> boolean   a slide of Dist studs along Dir keeps clear of walls and on a floor
	  Space.Room(S, Dir, Max) -> number      studs free along Dir (up to Max), rays plus a body-wide box sweep
	S: a student / NPC record with Model, Root and Up (or Agent.Up).
]]
local Players = game:GetService(`Players`)
local ServerScriptService = game:GetService(`ServerScriptService`)

local Nav = require(ServerScriptService.Services.AI.Nav)

local Space = {}

local function flat(V: Vector3): Vector3
	return Vector3.new(V.X, 0, V.Z)
end

local Params = RaycastParams.new()
Params.FilterType = Enum.RaycastFilterType.Exclude
Params.RespectCanCollide = true
local function filter(S)
	local Ex = { S.Model }
	for _, N in { `Live`, `NHFx`, `NHStudents`, `NHSchedule`, `NHAmbient` } do
		local F = workspace:FindFirstChild(N)
		if F then table.insert(Ex, F) end
	end
	for _, P in Players:GetPlayers() do if P.Character then table.insert(Ex, P.Character) end end
	Params.FilterDescendantsInstances = Ex
end

function Space.Clear(S, Dir: Vector3, Dist: number): boolean
	filter(S)
	local From = S.Root.Position
	if workspace:Raycast(From, Dir * (Dist + 1), Params) then return false end
	local Feet = From - Vector3.new(0, S.Up or (S.Agent and S.Agent.Up) or 3, 0)
	local Floor = Nav.Floor(Feet + Dir * Dist, 1.5)
	return Floor ~= nil and math.abs(Floor.Y - Feet.Y) < 1.2
end

function Space.Room(S, Dir: Vector3, Max: number): number
	filter(S)
	local Free = Max
	for _, H in { 0, 1, 1.5 } do
		local From = S.Root.Position + Vector3.new(0, H, 0)
		local Hit = workspace:Raycast(From, Dir * Max, Params)
		if Hit then Free = math.min(Free, flat(Hit.Position - From).Magnitude) end
	end
	-- with the arms out front the body is about 4 studs wide: sweep a box that size too (posts and railings slip
	-- between single rays)
	local At = S.Root.Position + Vector3.new(0, 0.75, 0)
	local Hit = workspace:Blockcast(CFrame.lookAt(At, At + Dir), Vector3.new(4, 3.5, 0.5), Dir * Max, Params)
	if Hit then Free = math.min(Free, Hit.Distance) end
	return Free
end

-- (phase6-strafes) the floor is clear for an in-place pacing clip: Radius studs free in four directions
function Space.Pace(S, Radius: number): boolean
	if not (S.Root and S.Root.Parent) then return false end
	local L = flat(S.Root.CFrame.LookVector).Unit
	local R = flat(S.Root.CFrame.RightVector).Unit
	for _, D in { L, -L, R, -R } do
		if Space.Room(S, D, Radius) < Radius then return false end
	end
	return true
end

return Space
