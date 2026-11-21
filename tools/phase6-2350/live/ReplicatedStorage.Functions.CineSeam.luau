--!strict
--[[
	CineSeam (shared, pure). ReplicatedStorage.Functions.CineSeam   (2.35.0, spec 2026-11-20 §2)
	The glide between the live gameplay camera and a seamless cut's first shot: how long, which path, and the lint that
	keeps shot 1 close to a gameplay angle. No side effects; the director turns Keys into a camera.keys shot.
]]
local Seam = {}

local MIN, MAX, DISSOLVE = 0.6, 1.0, 0.2
local LINT_TURN, LINT_TRAVEL = 90, 12

function Seam.Ease(U: number): number
	U = math.clamp(U, 0, 1)
	return U * U * U * (U * (6 * U - 15) + 10)
end

local function turn(A: CFrame, B: CFrame): number
	return math.deg(math.acos(math.clamp(A.LookVector:Dot(B.LookVector), -1, 1)))
end

function Seam.Length(FromCF: CFrame, ToCF: CFrame, Reduced: boolean?): number
	if Reduced then return DISSOLVE end
	local Travel = (ToCF.Position - FromCF.Position).Magnitude
	local Amount = math.clamp(math.max(Travel / LINT_TRAVEL, turn(FromCF, ToCF) / LINT_TURN), 0, 1)
	return MIN + (MAX - MIN) * Amount
end

function Seam.Keys(FromCF: CFrame, FromFov: number, ToCF: CFrame, ToFov: number, Length: number)
	-- a curved path: the middle key lifts a little and swings out to the side the camera turns from, so the glide
	-- reads as a camera operator's move, not a straight dolly
	local A, B = FromCF.Position, ToCF.Position
	local Mid = (A + B) / 2
	local Span = (B - A).Magnitude
	local Side = FromCF.RightVector * (if FromCF.LookVector:Cross(ToCF.LookVector).Y > 0 then -1 else 1)
	local Bend = math.clamp(Span * 0.18, 0.4, 2.5)
	local MidPos = Mid + Side * Bend + Vector3.new(0, Bend * 0.35, 0)
	-- the shot player interpolates FOV linearly in log focal length between keys, so the middle key sits at the geometric
	-- mean focal length (tan(fov/2) is inverse to it): both halves then share one slope and the FOV has no kink mid-glide
	local MidFov = math.deg(2 * math.atan(math.sqrt(math.tan(math.rad(FromFov) / 2) * math.tan(math.rad(ToFov) / 2))))
	local LookA = A + FromCF.LookVector * 10
	local LookB = B + ToCF.LookVector * 10
	return {
		{ t = 0; pos = A; look = LookA; fov = FromFov },
		{ t = Length / 2; pos = MidPos; look = LookA:Lerp(LookB, 0.5); fov = MidFov },
		{ t = Length; pos = B; look = LookB; fov = ToFov },
	}
end

function Seam.Lint(FromCF: CFrame, ToCF: CFrame): string?
	local Turn = turn(FromCF, ToCF)
	local Travel = (ToCF.Position - FromCF.Position).Magnitude
	if Turn > LINT_TURN or Travel > LINT_TRAVEL then
		return string.format("[fix] shot 1 turns %d deg / travels %.1f studs from the gameplay camera (max %d / %d)",
			math.floor(Turn + 0.5), Travel, LINT_TURN, LINT_TRAVEL)
	end
	return nil
end

-- the camera's roll about its own look: its right vector against a level horizon looking the same way
local function rollOf(CF: CFrame): number
	local Base = CFrame.lookAt(Vector3.zero, CF.LookVector)
	return math.atan2(CF.RightVector:Dot(Base.UpVector), CF.RightVector:Dot(Base.RightVector))
end

-- (task 12 fix round 1) the rotation between two cameras with a LEVEL horizon: a plain quaternion slerp between two level
-- orientations that differ in both yaw and pitch tilts the horizon in between (measured: up to -3.1 deg one way in the glide in,
-- -1.6 in the blend out; house style wants roll 0 on ground beats). The look direction slerps on its great circle; the roll is the
-- two ends' own rolls eased. Rotation only (position 0). Falls back to the quaternion slerp for looks within 0.5 deg of
-- parallel or opposed, or near straight up/down.
function Seam.Rot(A: CFrame, B: CFrame, E: number): CFrame
	local La, Lb = A.LookVector, B.LookVector
	local Dot = math.clamp(La:Dot(Lb), -1, 1)
	local Theta = math.acos(Dot)
	if Theta < math.rad(0.5) or Theta > math.pi - math.rad(0.5) or math.abs(La.Y) > 0.999 or math.abs(Lb.Y) > 0.999 then
		return A.Rotation:Lerp(B.Rotation, E)
	end
	local Look = (La * math.sin((1 - E) * Theta) + Lb * math.sin(E * Theta)) / math.sin(Theta)
	local Ra, Rb = rollOf(A), rollOf(B)
	return CFrame.lookAt(Vector3.zero, Look) * CFrame.Angles(0, 0, Ra + (Rb - Ra) * E)
end

function Seam.Blend(A: CFrame, B: CFrame, E: number): CFrame
	E = math.clamp(E, 0, 1)
	return CFrame.new(A.Position:Lerp(B.Position, E)) * Seam.Rot(A, B, E)
end

return Seam
