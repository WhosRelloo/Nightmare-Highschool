--[[
	AccessorySway (client): the 3D accessory kits (UI.AccessoryWear, Config.Accessories) move with you.
	Every rigged piece (a MeshPart under a character's "NHAcc_<Slot>" model that carries Bones) bends its chains the
	way Controllers.Character.HairSway bends hair: toward one drag direction in world space (behind the motion, up
	when falling, outward on a turn, a breeze), about an axis at right angles to each chain, shared down the chain
	(the shares add up to 1) and capped per joint, through a nearly critically damped spring. Depth-1 bones (the
	hinges, rigged as Root > H<n> > C<n>_<k> like the capes) never move.
	The piece's NHSway attribute picks a profile:
	  Flutter   ties: small bends, never pulled into the chest
	  Loops     bow ties: tiny bends
	  Pendulum  hanging things (bags, books, the grimoire, lanterns, watches): swing back, bob with the step
	  BackHang  things hanging on the back: as Pendulum, never pulled into the back
	  Tails     scarf tails and coat skirts: hair-like
	NHSwayKeepOut (Vector3, the piece's own axes) points at the body: the pull never goes that way.
	NHSwayLock "X" bends only about the piece's X axis (fore and aft: the satchel and grimoire hang in the narrow space
	beside the leg), "Z" only about its Z axis (flat on the chest, side to side: the ties). With these, every swing stays
	clear of the body and of the other pieces (checked offline by art/characters/accessories/acc_check.py).
	All characters within MAX_DIST of the camera. Reduce Motion (NHReducedMotion): half the motion, no wind or bob.
]]
local Players = game:GetService(`Players`)
local RunService = game:GetService(`RunService`)

local Player = Players.LocalPlayer
local MAX_DIST = 100
local SPEED_FULL = 22
local FALL_FULL = 45
local TELEPORT = 6
local Shared = {}
local States = {} :: { [Instance]: any }

local PROFILES = {
	Flutter = { Bend = math.rad(8); Joint = math.rad(4); Body = `Front`; Lift = 0; Wind = 0.6; Bob = 0; K = 70; D = 13 };
	Loops = { Bend = math.rad(9); Joint = math.rad(6); Body = `Front`; Lift = 0.2; Wind = 0.4; Bob = 0; K = 80; D = 14 };
	Pendulum = { Bend = math.rad(34); Joint = math.rad(20); Body = nil; Lift = 0; Wind = 0.25; Bob = 0.18; K = 45; D = 9 };
	BackHang = { Bend = math.rad(24); Joint = math.rad(16); Body = `Back`; Lift = 0; Wind = 0.2; Bob = 0.15; K = 50; D = 10 };
	Tails = { Bend = math.rad(50); Joint = math.rad(15); Body = nil; Lift = 0; Wind = 1; Bob = 0.05; K = 60; D = 13 };
}

-- the bones AccessoryFx's idle drives on this piece (NHIdleBones' names): never swung, and not part of a chain
local function idleBones(Handle: Instance): { [string]: boolean }
	local Raw = Handle:GetAttribute(`NHIdleBones`)
	local Out = {}
	if typeof(Raw) == `string` then
		for Name in Raw:gmatch('"([%w_]+)"%s*:%s*{') do Out[Name] = true end
	end
	return Out
end

local function collectBones(Handle: Instance)
	local Out = {}
	local Idle = idleBones(Handle)
	local function walk(P: Instance, Depth: number, Root)
		local Deepest = Depth - 1
		for _, B in P:GetChildren() do
			if B:IsA(`Bone`) and not Idle[B.Name] then
				local E = { Bone = B; Depth = Depth; Next = nil :: Bone? }
				for _, C in B:GetChildren() do
					if C:IsA(`Bone`) and not Idle[C.Name] then E.Next = C break end
				end
				table.insert(Out, E)
				local R = Root or (if Depth == 2 then E else nil)
				E.Root = R
				Deepest = math.max(Deepest, walk(B, Depth + 1, R))
			end
		end
		if Root then Root.ChainDepth = math.max(Root.ChainDepth or 0, Deepest) end
		return Deepest
	end
	walk(Handle, 0, nil)
	-- shares over the swinging bones of each chain (depth >= 2): 1, 2, ... k parts of the bend, adding up to 1
	for _, E in Out do
		local N = (E.Root and E.Root.ChainDepth) or E.Depth
		local Count = N - 1
		local Sum = Count * (Count + 1) / 2
		E.Share = if E.Depth >= 2 and Sum > 0 then (E.Depth - 1) / Sum else 0
	end
	return Out
end

local function capped(V: Vector3, Max: number): Vector3
	local M = V.Magnitude
	return if M > Max then V * (Max / M) else V
end

local function piecesOf(Char: Model)
	local Out = {}
	for _, M in Char:GetChildren() do
		if M:IsA(`Model`) and M:GetAttribute(`NHAcc`) ~= nil then
			for _, P in M:GetChildren() do
				-- (a familiar's bones are driven by AccessoryFx's idle, not swung; a piece with both, the birdcage purse,
				-- swings on its chain while its idle bones stay with AccessoryFx: collectBones skips them)
				if P:IsA(`BasePart`) and P:FindFirstChildWhichIsA(`Bone`)
					and (not P:GetAttribute(`NHIdle`) or P:GetAttribute(`NHSway`) ~= nil) then table.insert(Out, P) end
			end
		end
	end
	return Out
end

local function step(Dt: number)
	local Cam = workspace.CurrentCamera
	if not Cam then return end
	Dt = math.clamp(Dt, 1 / 240, 1 / 20)
	local Reduced = Player:GetAttribute(`NHReducedMotion`) == true
	local T = os.clock()
	local Seen = {}
	local Wind = (if Reduced then 0 else (0.5 + 0.5 * math.sin(T * 0.37)) * (0.35 + 0.65 * math.max(0, math.sin(T * 1.9) * math.sin(T * 0.53))))
	local WindDir = Vector3.new(math.cos(T * 0.05), 0, math.sin(T * 0.05))
	for _, Pl in Players:GetPlayers() do
		local Char = Pl.Character
		local Root = Char and Char:FindFirstChild(`HumanoidRootPart`) :: BasePart?
		if not Root or (Root.Position - Cam.CFrame.Position).Magnitude > MAX_DIST then continue end
		for _, Piece in piecesOf(Char) do
			Seen[Piece] = true
			local S = States[Piece]
			if not S then
				S = { Bones = collectBones(Piece); Drag = Vector3.zero; DragV = Vector3.zero;
					Prof = PROFILES[Piece:GetAttribute(`NHSway`) or `Pendulum`] or PROFILES.Pendulum;
					LastYaw = select(2, Root.CFrame:ToOrientation()); LastPos = Root.Position; Phase = math.random() * 6 }
				States[Piece] = S
			end
			if #S.Bones == 0 then continue end
			local Pr = S.Prof
			local Moved = (Root.Position - S.LastPos).Magnitude
			S.LastPos = Root.Position
			local Vel = Root.AssemblyLinearVelocity
			local Yaw = select(2, Root.CFrame:ToOrientation())
			local DYaw = math.atan2(math.sin(Yaw - S.LastYaw), math.cos(Yaw - S.LastYaw)) / Dt
			S.LastYaw = Yaw
			if Moved > TELEPORT then Vel = Vector3.zero DYaw = 0 end
			local Flat = Vector3.new(Vel.X, 0, Vel.Z)
			local Speed = math.clamp(Flat.Magnitude / SPEED_FULL, 0, 1)
			local Look, Right = Root.CFrame.LookVector, Root.CFrame.RightVector
			local Target = capped(-Flat / SPEED_FULL, 1)
				+ Vector3.yAxis * math.clamp(-Vel.Y / FALL_FULL, 0, 1) * 0.45
				+ Right * math.clamp(DYaw * 0.05, -0.5, 0.5)
				+ WindDir * Wind * 0.15 * Pr.Wind
			if not Reduced and Pr.Bob > 0 then -- the step's bounce: a small fore-and-aft swing at walking pace
				Target += Look * math.sin(T * 9 + S.Phase) * Pr.Bob * Speed
			end
			local Lock = Piece:GetAttribute(`NHSwayLock`)
			-- X: bends only about the side axis (fore and aft; it hangs in a narrow space); Z: only about the depth axis
			-- (flat on the chest, side to side). The piece's own axes are the mount's.
			local LockAxis = if Lock == `X` then Piece.CFrame.RightVector elseif Lock == `Z` then Piece.CFrame.LookVector else nil
			local KO = Piece:GetAttribute(`NHSwayKeepOut`)
			if typeof(KO) == `Vector3` and KO.Magnitude > 0 then -- toward the body (the piece's own axes): never pulled that way
				local Away = Piece.CFrame:VectorToWorldSpace(KO.Unit)
				Target -= Away * math.max(0, Target:Dot(Away))
			end
			if Pr.Body == `Front` then
				-- the body is behind the piece: drop any pull into it, and lift it off a little at speed
				local Back = -Look
				Target -= Back * math.max(0, Target:Dot(Back))
				Target += Look * Pr.Lift * Speed
			elseif Pr.Body == `Back` then
				Target -= Look * math.max(0, Target:Dot(Look))
			end
			Target = capped(Target, 1.1)
			if Reduced then Target *= 0.5 end
			local A = (Target - S.Drag) * Pr.K - S.DragV * Pr.D
			S.DragV += A * Dt
			S.Drag = capped(S.Drag + S.DragV * Dt, 1.2)
			for _, E in S.Bones do
				if E.Share <= 0 then continue end
				local B = E.Bone
				local Rest = (B.WorldCFrame * B.Transform:Inverse()).Rotation
				local Up = B.Parent :: any
				local Dir = if E.Next then Rest:VectorToWorldSpace(E.Next.Position)
					else (if Up:IsA(`Bone`) then Up.WorldCFrame else Up.CFrame):VectorToWorldSpace(B.Position)
				if Dir.Magnitude < 1e-4 then continue end
				Dir = Dir.Unit
				local Pull = S.Drag + WindDir * Wind * 0.06 * Pr.Wind * math.sin(T * 7 - E.Depth * 1.1)
				local Axis = Dir:Cross(Pull)
				if LockAxis then Axis = LockAxis * Axis:Dot(LockAxis) end
				local Perp = Axis.Magnitude
				if Perp < 1e-4 then B.Transform = CFrame.identity continue end
				local Angle = math.min(math.min(Perp, 1) * Pr.Bend * E.Share, Pr.Joint)
				B.Transform = CFrame.fromAxisAngle(Rest:VectorToObjectSpace(Axis / Perp), Angle)
			end
		end
	end
	for P, S in States do
		if not Seen[P] or not P.Parent then
			for _, E in S.Bones do if E.Bone.Parent then E.Bone.Transform = CFrame.identity end end
			States[P] = nil
		end
	end
end

function Shared.OnStart()
	RunService.PreSimulation:Connect(function(Dt)
		local Ok, Err = pcall(step, Dt)
		if not Ok then warn(`[AccessorySway] {Err}`) end
	end)
end

return Shared
