--[[
	Wing motion for the race forms. ReplicatedStorage.Functions.FormWings   Used by Controllers.Character.FormParts.

	The wings are driven on the client by Bone.Transform instead of published KeyframeSequences: the motion is the
	approved concepts' own skeleton (art/characters/transformations/hqwing.py Wing.skeleton(fold, flap, lag)), so the
	game shows exactly what the concept loops showed, with no clips to publish, and states blend in parameter space.

	Skeleton(sx, digits, fold, flap, lag): the joints R, E, W and the digits' K/T, in the model's own space.
	        fold 0 = spread (the bind pose), 1 = folded; flap = degrees about the body's long axis; lag = the digits'
	        trailing (follow-through), degrees.
	Rig(model): reads one imported wing (RootPart > Root > Hum > Fore > D<n>a > D<n>b) at rest. Call before any
	        Transform is set.
	Pose(rig, fold, flap, lag): sets every bone's Transform so each bone points where the skeleton says.
	Idle(t) / Flap(t) / Flare(u): the clips as parameter curves -> fold, flap, lag.
	        Idle: a slow breathe, 3 s loop, wings half folded like a cloak.
	        Flap: the concepts' stroke, 1.33 s loop, the digits trailing.
	        Flare: 0.6 s, folded to spread with an overshoot (on transform). The landing fold is a kick FormParts adds.
]]

local FormWings = {}

FormWings.IDLE_PERIOD = 3
FormWings.FLAP_PERIOD = 1.33
FormWings.FLARE_TIME = 0.6

local rad, sin, cos = math.rad, math.sin, math.cos

local function lerp(a: number, b: number, t: number): number
	return a + (b - a) * t
end

-- the build's axes (Blender: x right, y FORWARD is -y.. the rig faces +Y; z up) -> the imported model's space
-- (checked on the imported bones: the right wing's root (0.42, -0.5, 3.72) sits at (-0.42, 3.72, -0.5))
local function toModel(p: Vector3): Vector3
	return Vector3.new(-p.X, p.Z, p.Y)
end

local EL = { [4] = { 52, 18, -18, -52 }; [3] = { 44, -6, -48 } }
local LN = { [4] = { 1.75, 2.1, 1.85, 1.45 }; [3] = { 2.15, 2.35, 1.75 } }
local BK = { [4] = { 0.12, 0.18, 0.24, 0.3 }; [3] = { 0.14, 0.22, 0.3 } }

function FormWings.Skeleton(sx: number, digits: number, fold: number, flap: number, lag: number)
	local out, up, back = Vector3.new(sx, 0, 0), Vector3.new(0, 0, 1), Vector3.new(0, -1, 0)
	local function d(elev: number, bk: number): Vector3
		local a = rad(elev)
		return (out * cos(a) + up * sin(a) + back * bk).Unit
	end
	local R = Vector3.zero
	local E = R + d(lerp(42, 72, fold), lerp(0.35, 0.75, fold)) * 0.85
	local W = E + d(lerp(14, -105, fold), lerp(0.25, 0.45, fold)) * 1.3
	local el, ln, bk = EL[digits], LN[digits], BK[digits]
	local rot = CFrame.fromAxisAngle(Vector3.new(0, 1, 0), rad(flap) * sx)
	local function F(p: Vector3): Vector3
		return R + rot * (p - R)
	end
	local J = { Hum = { toModel(F(R)), toModel(F(E)) }; Fore = { toModel(F(E)), toModel(F(W)) } }
	for k = 1, digits do
		local e = lerp(el[k], -98 - 4 * (k - 1), fold)
		local lagk = lag * (0.5 + 0.5 * (k - 1) / math.max(digits - 1, 1))
		local dir1 = d(e + lagk * 0.6, lerp(bk[k], 0.5, fold))
		local dir2 = d(e - 9 - (k - 1) * 3 + lagk, lerp(bk[k] + 0.08, 0.55, fold))
		local K = W + dir1 * ln[k] * 0.48
		local T = K + dir2 * ln[k] * 0.52
		J[`D{k}a`] = { toModel(F(W)), toModel(F(K)) }
		J[`D{k}b`] = { toModel(F(K)), toModel(F(T)) }
	end
	return J
end

local function arc(a: Vector3, b: Vector3): CFrame
	a, b = a.Unit, b.Unit
	local c = a:Cross(b)
	local s = c.Magnitude
	local d = math.clamp(a:Dot(b), -1, 1)
	if s < 1e-6 then return CFrame.identity end
	return CFrame.fromAxisAngle(c / s, math.atan2(s, d))
end

export type Rig = { Root: BasePart, Bones: { { Bone: Bone, Name: string, ParentName: string?, Local: CFrame, RestRot: CFrame } },
	Rest: { [string]: CFrame }, Sx: number, Digits: number, Bind: any }

local ORDER = { "Hum", "Fore", "D1a", "D1b", "D2a", "D2b", "D3a", "D3b", "D4a", "D4b" }

function FormWings.Rig(Model: Model): Rig?
	local RootPart = Model:FindFirstChild(`RootPart`) :: BasePart?
	if not RootPart then return nil end
	local ByName: { [string]: Bone } = {}
	for _, B in RootPart:GetDescendants() do
		if B:IsA(`Bone`) then ByName[B.Name] = B end
	end
	local RootBone, Hum = ByName.Root, ByName.Hum
	if not RootBone or not Hum then return nil end
	local Digits = if ByName.D4a then 4 else 3
	local RootPos = RootPart.CFrame:PointToObjectSpace(RootBone.WorldPosition)
	local Rest: { [string]: CFrame } = { Root = RootPart.CFrame:ToObjectSpace(RootBone.WorldCFrame) }
	local Bones = {}
	for _, N in ORDER do
		local B = ByName[N]
		if not B then continue end
		local M = RootPart.CFrame:ToObjectSpace(B.WorldCFrame)
		Rest[N] = M
		table.insert(Bones, { Bone = B; Name = N; ParentName = (B.Parent :: Instance).Name; Local = B.CFrame; RestRot = M.Rotation })
	end
	-- which side: the right wing reaches toward -X in the model's space
	local Fore = Rest.Fore
	local Sx = if Fore and Fore.Position.X < RootPos.X then 1 else -1
	return { Root = RootPart; Bones = Bones; Rest = Rest; Sx = Sx; Digits = Digits; Bind = FormWings.Skeleton(Sx, Digits, 0, 0, 0) }
end

function FormWings.Pose(Rig: Rig, fold: number, flap: number, lag: number)
	local J = FormWings.Skeleton(Rig.Sx, Rig.Digits, fold, flap, lag)
	local Posed: { [string]: CFrame } = { Root = Rig.Rest.Root }
	for _, B in Rig.Bones do
		local Pj, P0 = J[B.Name], Rig.Bind[B.Name]
		local Parent = Posed[B.ParentName] or Rig.Rest[B.ParentName] or Rig.Rest.Root
		local Base = Parent * B.Local
		local T = CFrame.identity
		if Pj and P0 then
			local O = arc(P0[2] - P0[1], Pj[2] - Pj[1]) * B.RestRot
			T = Base.Rotation:Inverse() * O
		end
		B.Bone.Transform = T
		Posed[B.Name] = Base * T
	end
end

-- the clips as curves: (fold, flap, lag)
function FormWings.Idle(t: number): (number, number, number)
	local p = 2 * math.pi * t / FormWings.IDLE_PERIOD
	return 0.62 + 0.06 * sin(p), 3 * sin(p + 0.5), 5 * sin(p - 0.8)
end

function FormWings.Flap(t: number): (number, number, number)
	local p = 2 * math.pi * t / FormWings.FLAP_PERIOD
	local down = if sin(p) > 0 then 1 else 0.3
	return 0.12 + 0.18 * (0.5 - 0.5 * cos(p)) * down, 34 * sin(p) + 6, -16 * sin(p - 0.9)
end

function FormWings.Flare(u: number): (number, number, number)
	-- 0 -> 1 over FLARE_TIME: folded (0.9) snaps open past spread, then settles toward the idle
	u = math.clamp(u, 0, 1)
	local open = 1 - (1 - u) ^ 3
	local over = sin(math.pi * u) * (1 - u)
	return lerp(0.9, 0.62, u) - 0.75 * over - 0.1 * open * (1 - u), -18 * over, 22 * over
end

return FormWings
