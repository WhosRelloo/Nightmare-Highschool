--!strict
--[[
	FormDangles: the race-form pieces that hang, as rigid links or strips on a small rope simulation (client only, drawn
	by Controllers.Character.FormParts). Only the pieces that hang move; every other form piece stays welded.
	Rest shapes come from Config.FormDangles (generated from art/characters/transformations/form_bodies.py --dangles:
	part-local nodes at height 1, Roblox axes), meshes from ReplicatedStorage.Assets.Forms.Dangles (Link, TatterSeg,
	TatterTip; staged by tools/forms/stage/dress_dangles.luau).

	Kinds:
	  Swag    a chain lying across the chest or back, pinned over both shoulders (Wraith 2). It holds its drape with a
	          spring and is set swinging by the body: the run's air pulls it back, steps bob it, stops and landings throw
	          it. It never sinks into the body (each node may only move out along its rest normal).
	  Hang    a chain hanging from a wrist (Wraith 2): a real pendulum under gravity; it trails when you run and swings
	          with the arm. It stays below the arm and outside the leg.
	  Tatter  a grave-linen strip hanging from an arm wrap (Ghoul 2): as Hang, lighter, catching more air, with a flutter
	          at speed. It stays off its arm and outside the leg.
	Fixed 90 Hz substeps (any frame rate), position-based distance constraints, the parts' motion interpolated across
	the substeps. A jump of more than TELEPORT studs between frames snaps every rope back to rest.
	Reduce Motion: swags hold their rest drape; hanging things still hang under gravity, with no bob or flutter.
]]

local FormDangles = {}

local STEP = 1 / 90
local MAX_STEPS = 6 -- (a 15 fps frame)
local ITER = 4
local TELEPORT = 6
local SPEED_FULL = 22
local LINK_TURN = true -- alternate links stand at right angles

-- Swag: Spring / Damp hold the drape (natural frequency ~17 rad/s, well off the ~9 rad/s step bob), MaxOff caps a node's
-- travel from rest (studs at height 1). Hang / Tatter: Cone caps every segment's swing from straight down (degrees),
-- so a fast turn never whips a chain over the wrist or flips a strip up.
type Profile = { Gravity: number, Drag: number, Spring: number, Damp: number, Bob: number, Flutter: number,
	MaxOff: number, Cone: number }
local PROFILE: { [string]: Profile } = {
	Swag = { Gravity = 0, Drag = 1.2, Spring = 300, Damp = 18, Bob = 14, Flutter = 0, MaxOff = 0.3, Cone = 0 },
	Hang = { Gravity = 140, Drag = 3, Spring = 0, Damp = 0, Bob = 0, Flutter = 0, MaxOff = 0, Cone = 70 },
	Tatter = { Gravity = 100, Drag = 3.5, Spring = 0, Damp = 0, Bob = 0, Flutter = 20, MaxOff = 0, Cone = 65 },
}

export type Rope = {
	Kind: string, Prof: Profile, Part: BasePart, Side: number,
	Rest: { Vector3 }, Nrm: { Vector3 }?, Across: Vector3?, Len: { number }, Pin: { [number]: boolean },
	X: { Vector3 }, V: { Vector3 }, RW: { Vector3 }, R0: number, Parts: { BasePart }, Phase: number,
}
export type Group = {
	Model: Model, Torso: BasePart, Root: BasePart?, Ropes: { Rope }, Prev: { [BasePart]: CFrame },
	Acc: number, Clock: number, LegOuter: { number }, Odd: boolean, Fresh: boolean,
}

-- an R6 part's default size: body pieces and rest nodes scale per axis by Part.Size / this
function FormDangles.Base(Part: BasePart): Vector3
	return if Part.Name == `Torso` then Vector3.new(2, 2, 1) else Vector3.new(1, 2, 1)
end

local function scaled(List: { Vector3 }, K: Vector3): { Vector3 }
	local Out = table.create(#List)
	for I, V in List do Out[I] = V * K end
	return Out
end

local function clonePart(Src: BasePart, Size: Vector3, Parent: Instance): BasePart
	local M = Src:Clone()
	M.Size = Size
	M.Anchored, M.CanCollide, M.CanQuery, M.CanTouch, M.Massless = true, false, false, false, true
	M.Parent = Parent
	return M
end

-- the ropes of one direction on one character: Data = Config.FormDangles.Bodies[body][prefix] (nil: nothing hangs)
function FormDangles.Build(Char: Model, Data: { any }?, LegOuter: { number }?, Lib: Instance?, Parent: Instance): Group?
	if not Data or #Data == 0 or not Lib then return nil end
	local Torso = Char:FindFirstChild(`Torso`) :: BasePart?
	local Link = Lib:FindFirstChild(`Link`) :: BasePart?
	local Seg, Tip = Lib:FindFirstChild(`TatterSeg`) :: BasePart?, Lib:FindFirstChild(`TatterTip`) :: BasePart?
	if not Torso then return nil end
	local Model = Instance.new(`Model`)
	Model.Name = `NHFormDangles`
	local G: Group = { Model = Model, Torso = Torso, Root = Char:FindFirstChild(`HumanoidRootPart`) :: BasePart?,
		Ropes = {}, Prev = {}, Acc = 0, Clock = math.random() * 10, LegOuter = LegOuter or { 1, 1 }, Odd = false, Fresh = true }
	for _, D in Data do
		local Part = Char:FindFirstChild(D.Part) :: BasePart?
		local Prof = PROFILE[D.Kind]
		if not Part or not Prof then continue end
		local K = Part.Size.Y / 2
		local Rest = scaled(D.Pts, Part.Size / FormDangles.Base(Part))
		local N = #Rest
		local Len = table.create(N - 1)
		for I = 1, N - 1 do Len[I] = (Rest[I + 1] - Rest[I]).Magnitude end
		local Pin = { [1] = true }
		if D.Kind == `Swag` then Pin[N] = true end
		local CF = Part.CFrame
		local X, V, RW = table.create(N), table.create(N), table.create(N)
		for I = 1, N do
			X[I] = CF:PointToWorldSpace(Rest[I]); V[I] = Vector3.zero; RW[I] = X[I]
		end
		local Parts = {}
		if D.Kind == `Tatter` then
			if not (Seg and Tip) then continue end
			for I = 1, N - 1 do
				local Src = if I == N - 1 then Tip else Seg
				local W = D.W * K
				table.insert(Parts, clonePart(Src, Vector3.new(W, Len[I] * 1.12, Src.Size.Z * W / Src.Size.X), Model))
			end
		else
			if not Link then continue end
			for _ = 1, N - 1 do table.insert(Parts, clonePart(Link, Link.Size * K, Model)) end
		end
		local Sx = Part.CFrame:PointToObjectSpace(Torso.Position).X -- the torso lies this way from the part
		table.insert(G.Ropes, { Kind = D.Kind, Prof = Prof, Part = Part,
			Side = if Part == Torso then 0 elseif Sx < 0 then 1 else -1,
			Rest = Rest, Nrm = D.Nrm, Across = D.Across, Len = Len, Pin = Pin, X = X, V = V, RW = RW,
			R0 = Vector2.new(Rest[1].X, Rest[1].Z).Magnitude, Parts = Parts, Phase = math.random() * 6.28 })
	end
	if #G.Ropes == 0 then Model:Destroy() return nil end
	Model.Parent = Parent
	FormDangles.Draw(G)
	return G
end

local function keepOut(G: Group, R: Rope, I: number, P: Vector3, CF: CFrame, TCF: CFrame, Top: Vector3): Vector3
	local K = R.Part.Size.Y / 2
	if R.Kind == `Swag` then
		local Nrm = R.Nrm :: { Vector3 }
		local Off = CF:PointToObjectSpace(P) - R.Rest[I]
		local D = Off:Dot(Nrm[I])
		if D < 0 then Off -= Nrm[I] * D end
		local Max = R.Prof.MaxOff * K
		if Off.Magnitude > Max then Off = Off.Unit * Max end
		return CF:PointToWorldSpace(R.Rest[I] + Off)
	end
	local L = CF:PointToObjectSpace(P)
	if R.Kind == `Hang` then
		if L.Y > -K then L = Vector3.new(L.X, -K, L.Z) end -- never up into the arm
	elseif L.Y > -K then -- a tatter: off its own arm
		local Rad = Vector2.new(L.X, L.Z)
		local M = Rad.Magnitude
		if M < R.R0 and M > 1e-4 then
			Rad = Rad * (R.R0 / M)
			L = Vector3.new(Rad.X, L.Y, Rad.Y)
		end
	end
	P = CF:PointToWorldSpace(L)
	-- outside the leg (torso space): below the hips, nothing crosses inside the leg's outer reach
	local TS = G.Torso.Size
	local T = TCF:PointToObjectSpace(P)
	if R.Side ~= 0 and T.Y < -0.45 * TS.Y then
		local Lim = ((G.LegOuter[if R.Side > 0 then 1 else 2] or 1) + 0.05) * TS.X / 2
		if T.X * R.Side < Lim then
			P = TCF:PointToWorldSpace(Vector3.new(Lim * R.Side, T.Y, T.Z))
		end
	end
	-- last, the swing cone: this segment, from the node above it (after the pushes, so none of them tips a strip up)
	local Dv = P - Top
	local Len = Dv.Magnitude
	if Len > 1e-4 then
		local Cone = math.rad(R.Prof.Cone)
		if -Dv.Y / Len < math.cos(Cone) then
			local Hz = Vector3.new(Dv.X, 0, Dv.Z)
			if Hz.Magnitude > 1e-4 then
				P = Top + (Hz.Unit * math.sin(Cone) - Vector3.yAxis * math.cos(Cone)) * Len
			end
		end
	end
	return P
end

local function reset(G: Group)
	for _, R in G.Ropes do
		local CF = R.Part.CFrame
		for I = 1, #R.Rest do
			R.X[I] = CF:PointToWorldSpace(R.Rest[I]); R.V[I] = Vector3.zero; R.RW[I] = R.X[I]
		end
	end
end

local function substep(G: Group, A: number, H: number, Still: boolean, Speed: number, Cur: { [BasePart]: CFrame })
	local TCF = G.Prev[G.Torso]:Lerp(Cur[G.Torso], A)
	local Up = Vector3.yAxis
	for _, R in G.Ropes do
		local Pr = R.Prof
		local CF = G.Prev[R.Part]:Lerp(Cur[R.Part], A)
		local X, V, RW, Pin = R.X, R.V, R.RW, R.Pin
		local N = #X
		local Xp = table.create(N)
		local Bob = if Still then 0 else Pr.Bob * Speed * math.sin(G.Clock * 9 + R.Phase)
		local Fl = if Still or Pr.Flutter == 0 then 0 else Pr.Flutter * Speed
		local Across = if R.Across then CF:VectorToWorldSpace(R.Across) else Vector3.zero
		for I = 1, N do
			local W = CF:PointToWorldSpace(R.Rest[I])
			if Pin[I] then
				Xp[I] = W
			else
				local Vi = V[I]
				local Acc = Vector3.new(0, -Pr.Gravity, 0) - Vi * Pr.Drag
				if Pr.Spring > 0 then
					local RV = (W - RW[I]) / H
					Acc += (W - X[I]) * Pr.Spring - (Vi - RV) * Pr.Damp + Up * Bob
				end
				if Fl ~= 0 then Acc += Across * (Fl * math.sin(G.Clock * 13 + I * 1.7 + R.Phase)) end
				Vi += Acc * H
				V[I] = Vi
				Xp[I] = X[I] + Vi * H
			end
			RW[I] = W
		end
		for _ = 1, ITER do
			for I = 1, N - 1 do
				local WA, WB = if Pin[I] then 0 else 1, if Pin[I + 1] then 0 else 1
				local S = WA + WB
				if S == 0 then continue end
				local D = Xp[I + 1] - Xp[I]
				local L = D.Magnitude
				if L < 1e-6 then continue end
				local Corr = D * ((L - R.Len[I]) / (L * S))
				Xp[I] += Corr * WA
				Xp[I + 1] -= Corr * WB
			end
			for I = 1, N do
				if not Pin[I] then Xp[I] = keepOut(G, R, I, Xp[I], CF, TCF, Xp[I - 1]) end
			end
		end
		for I = 1, N do
			if not Pin[I] then V[I] = (Xp[I] - X[I]) / H end
			X[I] = Xp[I]
		end
	end
end

-- one frame. SlowRange: beyond it the ropes update every other frame (as the wings)
function FormDangles.Step(G: Group, Dt: number, Still: boolean, CamPos: Vector3, SlowRange: number)
	local Root = G.Root
	if Root and (Root.Position - CamPos).Magnitude > SlowRange then
		G.Odd = not G.Odd
		if G.Odd then G.Acc += Dt return end
	end
	local Cur: { [BasePart]: CFrame } = { [G.Torso] = G.Torso.CFrame }
	for _, R in G.Ropes do Cur[R.Part] = R.Part.CFrame end
	local Jump = G.Fresh
	for P, CF in Cur do
		local Old = G.Prev[P]
		if not Old or (Old.Position - CF.Position).Magnitude > TELEPORT then Jump = true end
	end
	G.Fresh = false
	if Jump then
		for P, CF in Cur do G.Prev[P] = CF end
		reset(G)
		G.Acc = 0
		FormDangles.Draw(G)
		return
	end
	G.Acc = math.min(G.Acc + Dt, STEP * MAX_STEPS)
	local Steps = math.floor(G.Acc / STEP)
	if Steps > 0 then
		G.Acc -= Steps * STEP
		local Vel = if Root then Root.AssemblyLinearVelocity else Vector3.zero
		local Speed = math.clamp(Vector3.new(Vel.X, 0, Vel.Z).Magnitude / SPEED_FULL, 0, 1)
		local OnlySwags = Still -- Reduce Motion: swags hold the rest drape
		for S = 1, Steps do
			G.Clock += STEP
			substep(G, S / Steps, STEP, Still, Speed, Cur)
		end
		if OnlySwags then
			for _, R in G.Ropes do
				if R.Kind ~= `Swag` then continue end
				local CF = Cur[R.Part]
				for I = 1, #R.Rest do R.X[I] = CF:PointToWorldSpace(R.Rest[I]); R.V[I] = Vector3.zero end
			end
		end
	end
	for P, CF in Cur do G.Prev[P] = CF end
	FormDangles.Draw(G)
end

-- lay the links and strips along the nodes
function FormDangles.Draw(G: Group)
	local Parts, CFs = {}, {}
	for _, R in G.Ropes do
		local X = R.X
		local CF = R.Part.CFrame
		local LastAlong = -CF.UpVector
		for I = 1, #X - 1 do
			local A, B = X[I], X[I + 1]
			local Mid = (A + B) * 0.5
			local Along = B - A
			Along = if Along.Magnitude > 1e-4 then Along.Unit else LastAlong
			LastAlong = Along
			local Out
			if R.Kind == `Tatter` then
				local Dn = Along
				local Ac = CF:VectorToWorldSpace(R.Across :: Vector3)
				Ac -= Dn * Ac:Dot(Dn)
				if Ac.Magnitude < 1e-3 then Ac = CF.RightVector end
				Out = CFrame.fromMatrix(Mid, Ac.Unit, -Dn) -- the card: X across, +Y up the strip
			else
				local Nrm = R.Nrm
				local Ref = if Nrm then CF:VectorToWorldSpace((Nrm[I] + Nrm[I + 1]).Unit) else CF.RightVector
				local Y
				if LINK_TURN and I % 2 == 0 then
					Y = Ref - Along * Ref:Dot(Along) -- standing: the ring plane holds the normal
				else
					Y = Ref:Cross(Along) -- lying flat on the body
				end
				if Y.Magnitude < 1e-3 then Y = Along:Cross(Vector3.xAxis) end
				if Y.Magnitude < 1e-3 then Y = Along:Cross(Vector3.zAxis) end
				Out = CFrame.fromMatrix(Mid, Along, Y.Unit)
			end
			table.insert(Parts, R.Parts[I])
			table.insert(CFs, Out)
		end
	end
	workspace:BulkMoveTo(Parts, CFs, Enum.BulkMoveMode.FireCFrameChanged)
end

return FormDangles
