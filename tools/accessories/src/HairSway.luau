--[[
	HairSway (client): hair that moves.
	  * Rigged hair (an accessory Handle with Bones, e.g. the owner's re-rigged hairs): every bone chain swings like
	    a strand. Moving drags the strands back, turning makes them lag outward, falling lifts them, and a soft wind
	    with gusts ruffles them. Bones on the scalp (depth 1) never move.
	  * (1.71.0, owner: "I don't want the weird stretch thing") The strands only bend, never twist or over-bend:
	      - each bone bends its strand TOWARD one drag direction (world space), about an axis at right angles to
	        the strand, so a ponytail lying along the head is never spun around its own length (the old fixed
	        head-axis pitch/roll twisted those, and skinned strands smear when twisted);
	      - the bend is shared down each chain (the shares add up to 1), so the tip's total bend is capped at
	        MAX_BEND at full speed (it used to be the target x the sum of (depth - 1) x 0.16, 2.4x on a 6-deep
	        chain), and no joint bends more than MAX_JOINT;
	      - dashes and teleports can't spike it: the frame time is clamped, a jump of more than TELEPORT studs in
	        one frame is ignored, speeds are capped, and the spring is nearly critically damped (no overshoot).
	  * (accessories, hair tuck) While the character wears accessories the hair would pass through, its NHHairTuck
	    attribute (UI.AccessoryWear) holds each lock bone's turn that lays the hair over, under or round them. The turn
	    eases in and out (TUCK_EASE). A tucked lock rests on the piece and holds still (TUCK_SWAY 0: the tucks lay the
	    hair just clear of it, and any swing would carry it back in); the other locks sway as before.
	All characters within MAX_DIST of the camera. Reduce Motion: half the motion, no wind.
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)

local Wear = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`AccessoryWear`))

local Player = Players.LocalPlayer
local MAX_DIST = 90
local MAX_BEND = math.rad(50)   -- a strand's total bend at the tip, at full drag
local MAX_JOINT = math.rad(15)  -- any one joint
local SPEED_FULL = 22           -- studs/s of travel for full drag
local FALL_FULL = 45            -- studs/s of falling for full lift
local TELEPORT = 6              -- studs in one frame: a dash / teleport, not motion
local K, D = 60, 13             -- spring (damping ratio about 0.84)
local TUCK_EASE = 8             -- 1/s: a tuck settles in about a quarter of a second
local TUCK_SWAY = 0             -- a tucked lock's share of the sway (it rests on the piece)
local Shared = {}
local States = {} :: { [Instance]: any }

local function isHair(Acc: Instance): boolean
	if not Acc:IsA(`Accessory`) then return Acc.Name == `NHHair` end
	if Acc.AccessoryType == Enum.AccessoryType.Hair then return true end
	local H = Acc:FindFirstChild(`Handle`)
	return H ~= nil and H:FindFirstChild(`HairAttachment`) ~= nil
end

-- every bone with its depth, the bone that continues its strand, and its share of the strand's bend
local function collectBones(Handle: Instance)
	local Out = {}
	local function walk(P: Instance, Depth: number, Root, Lock)
		local Deepest = Depth - 1
		for _, B in P:GetChildren() do
			if B:IsA(`Bone`) then
				local E = { Bone = B; Depth = Depth; Next = nil :: Bone? }
				for _, C in B:GetChildren() do
					if C:IsA(`Bone`) then E.Next = C break end
				end
				table.insert(Out, E)
				local R = Root or E
				E.Root = R
				E.Lock = Lock or (if Depth == 2 then E else nil) -- the lock (strand chain) it belongs to
				Deepest = math.max(Deepest, walk(B, Depth + 1, R, E.Lock))
			end
		end
		if Root then Root.ChainDepth = math.max(Root.ChainDepth or 0, Deepest) end
		return Deepest
	end
	walk(Handle, 1, nil)
	for _, E in Out do
		local N = (E.Root and E.Root.ChainDepth) or E.Depth
		local Sum = (N - 1) * N / 2 -- 1 + 2 + ... + (N - 1)
		E.Share = if E.Depth > 1 and Sum > 0 then (E.Depth - 1) / Sum else 0
		E.Tuck = Vector3.zero   -- the turn now (eased toward the target)
	end
	return Out
end

local function hairOf(Char: Model)
	local Out = {}
	for _, C in Char:GetChildren() do
		if isHair(C) then
			for _, H in C:GetDescendants() do
				if H:IsA(`BasePart`) and (H.Name == `Handle` or H:FindFirstChildWhichIsA(`Bone`)) then table.insert(Out, H) end
			end
		end
	end
	return Out
end

local function capped(V: Vector3, Max: number): Vector3
	local M = V.Magnitude
	return if M > Max then V * (Max / M) else V
end

local function step(Dt: number)
	local Cam = workspace.CurrentCamera
	if not Cam then return end
	Dt = math.clamp(Dt, 1 / 240, 1 / 20)
	local Reduced = Player:GetAttribute(`NHReducedMotion`) == true
	local T = os.clock()
	local Seen = {}
	-- one shared breeze: a slow swell with occasional gusts, from one direction
	local Wind = (if Reduced then 0 else (0.5 + 0.5 * math.sin(T * 0.37)) * (0.35 + 0.65 * math.max(0, math.sin(T * 1.9) * math.sin(T * 0.53))))
	local WindDir = Vector3.new(math.cos(T * 0.05), 0, math.sin(T * 0.05))
	local Ease = 1 - math.exp(-TUCK_EASE * Dt)
	for _, P in Players:GetPlayers() do
		local Char = P.Character
		local Head = Char and Char:FindFirstChild(`Head`) :: BasePart?
		local Root = Char and Char:FindFirstChild(`HumanoidRootPart`) :: BasePart?
		if not (Head and Root) or (Root.Position - Cam.CFrame.Position).Magnitude > MAX_DIST then continue end
		for _, Handle in hairOf(Char) do
			Seen[Handle] = true
			local S = States[Handle]
			if not S then
				S = { Bones = collectBones(Handle); Drag = Vector3.zero; DragV = Vector3.zero;
					LastYaw = select(2, Head.CFrame:ToOrientation()); LastPos = Root.Position }
				States[Handle] = S
			end
			if #S.Bones == 0 then continue end
			-- the hair tuck for what the character wears now (read again only when it changes)
			local TuckSrc = Char:GetAttribute(`NHHairTuck`)
			if TuckSrc ~= S.TuckSrc then
				S.TuckSrc = TuckSrc
				local Target = Wear.ParseTuck(TuckSrc) or {}
				for _, E in S.Bones do E.TuckTarget = Target[E.Bone.Name] or Vector3.zero end
				for _, E in S.Bones do -- a lock is tucked if any bone of it is
					if E.Lock then E.Lock.Tucked = false end
				end
				for _, E in S.Bones do
					if E.Lock and E.TuckTarget.Magnitude > 1e-4 then E.Lock.Tucked = true end
				end
			end
			-- a dash or teleport (a big jump in one frame): don't read it as motion
			local Moved = (Root.Position - S.LastPos).Magnitude
			S.LastPos = Root.Position
			local Vel = Root.AssemblyLinearVelocity
			local Yaw = select(2, Head.CFrame:ToOrientation())
			local DYaw = math.atan2(math.sin(Yaw - S.LastYaw), math.cos(Yaw - S.LastYaw)) / Dt
			S.LastYaw = Yaw
			if Moved > TELEPORT then Vel = Vector3.zero DYaw = 0 end
			local Flat = Vector3.new(Vel.X, 0, Vel.Z)
			-- where the strands are pulled to (world): behind the motion, outward on a turn, up when falling, the wind
			local Target = capped(-Flat / SPEED_FULL, 1)
				+ Vector3.yAxis * math.clamp(-Vel.Y / FALL_FULL, 0, 1) * 0.45
				+ Head.CFrame.RightVector * math.clamp(DYaw * 0.05, -0.5, 0.5)
				+ WindDir * Wind * 0.15
				- Head.CFrame.LookVector * math.sin(T * 1.3) * 0.02
			Target = capped(Target, 1.1)
			if Reduced then Target *= 0.5 end
			local A = (Target - S.Drag) * K - S.DragV * D
			S.DragV += A * Dt
			S.Drag = capped(S.Drag + S.DragV * Dt, 1.2)
			for _, E in S.Bones do
				local B = E.Bone
				local Goal = E.TuckTarget or Vector3.zero
				E.Tuck = if (Goal - E.Tuck).Magnitude < 1e-4 then Goal else E.Tuck + (Goal - E.Tuck) * Ease
				local Tuck = if E.Tuck.Magnitude > 1e-5 then Wear.TuckCFrame(B, E.Tuck) else CFrame.identity
				if E.Share <= 0 then
					if E.Tuck.Magnitude > 1e-5 then B.Transform = Tuck end
					continue
				end
				-- this bone's frame without its own sway (its parent's frame and rest offset), and the strand's
				-- direction from it in that rest frame, so last frame's bend never feeds back into this one
				local Rest = (B.WorldCFrame * B.Transform:Inverse()).Rotation
				local Up = B.Parent :: any
				local Dir = if E.Next then Rest:VectorToWorldSpace(E.Next.Position)
					else (if Up:IsA(`Bone`) then Up.WorldCFrame else Up.CFrame):VectorToWorldSpace(B.Position)
				if Dir.Magnitude < 1e-4 then B.Transform = Tuck continue end
				Dir = Dir.Unit
				-- flutter along the strand, a little more toward the tips
				local Pull = S.Drag + WindDir * Wind * 0.06 * math.sin(T * 7 - E.Depth * 1.1)
				local Axis = Dir:Cross(Pull) -- at right angles to the strand: bends it, never twists it
				local Perp = Axis.Magnitude
				if Perp < 1e-4 then B.Transform = Tuck continue end
				local Angle = math.min(math.min(Perp, 1) * MAX_BEND * E.Share, MAX_JOINT)
				if E.Lock and E.Lock.Tucked then Angle *= TUCK_SWAY end
				-- the sway turns the strand about its rest frame, on top of the tuck
				B.Transform = CFrame.fromAxisAngle(Rest:VectorToObjectSpace(Axis / Perp), Angle) * Tuck
			end
		end
	end
	for H, S in States do
		if not Seen[H] or not H.Parent then
			for _, E in S.Bones do if E.Bone.Parent then E.Bone.Transform = CFrame.identity end end
			States[H] = nil
		end
	end
end

function Shared.OnStart()
	RunService.PreSimulation:Connect(function(Dt)
		local Ok, Err = pcall(step, Dt)
		if not Ok then warn(`[HairSway] {Err}`) end
	end)
end

return Shared
