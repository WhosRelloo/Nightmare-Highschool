-- (2.33) Builds ServerStorage.NHHomes.Dorm.TrophyWall: three copies of the room's TrophyShelf mesh (scaled 0.9) on the
-- right wall (inner face x = 10, centred z = -5.5, rows at y 4.0 / 6.4 / 8.8, facing -X) with WallSpot1..12 (4 a shelf,
-- 0.47 x 0.9 above each shelf's centre, at -2.025 / -0.675 / 0.675 / 2.025 along it). Run in Edit (execute_luau).
local Room = game.ServerStorage.NHHomes.Dorm
local old = Room:FindFirstChild("TrophyWall") if old then old:Destroy() end
local Src = Room.TrophyShelf.TrophyShelf
local piv = Room:GetPivot()
local W = Instance.new("Model") W.Name = "TrophyWall"
local K = 0
for row, y in ipairs({ 4.0, 6.4, 8.8 }) do
	local S = Src:Clone()
	S.Name = "WallShelf" .. row
	S.Size = S.Size * 0.9
	S.CFrame = piv * CFrame.new(10 - S.Size.Z / 2, y, -5.5) * CFrame.Angles(0, -math.pi / 2, 0)
	S.Anchored = true
	S.Parent = W
	for _, off in { -2.025, -0.675, 0.675, 2.025 } do
		K += 1
		local P = Instance.new("Part")
		P.Name = "WallSpot" .. K
		P.Size = Vector3.new(0.8, 0.05, 0.6)
		P.Transparency = 1 P.CanCollide = false P.CanQuery = false P.CanTouch = false P.Anchored = true
		P.CFrame = S.CFrame * CFrame.new(off, 0.47 * 0.9, -0.07)
		P.Parent = W
	end
end
W.Parent = Room
return K
