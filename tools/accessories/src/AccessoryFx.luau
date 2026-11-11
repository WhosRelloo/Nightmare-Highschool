--[[
	AccessoryFx (client): the 3D accessories' own motion and light, beside AccessorySway (UI.AccessoryWear wears them;
	the attributes come from the templates in ReplicatedStorage.NHAccessories).
	  NHOrbitAxis (Vector3, the mount's axes) + NHOrbitRpm: the piece turns about its mount's centre (orbiting sigils,
	    keys). The offline check clears every angle of the orbit, so it never passes through the body, hair or a hat.
	  NHBob (studs): a slow float up and down (halos).
	  NHIdle ("Familiar", "Ledger", ...): idle motion on named bones (NHIdleBones, JSON: { Bone = { axis = {x,y,z},
	    min = deg, max = deg } } in each bone's own axes), by role: Head looks about, LidL / LidR blink, Tail flicks,
	    WingL / WingR settle now and then, Page<n> turn over one after another. A group letter after the role
	    (HeadA, HeadB) keeps two creatures on one piece apart. Bones without an entry stay still.
	  NHPulse (seconds): the glow breathes slowly (the crown's stone, ember eyes).
	  NHFlare (true): the glow flares for a moment when the wearer's character gets NHAdminFlare (a time, set by the
	    server when an admin tool is used): the crimson sigil halo.
	  NHTrail (true): its ParticleEmitters run only while the wearer walks (the shadow trail). Off with Reduce Motion.
	  PointLights with NHFlicker: candle flicker.
	Reduce Motion (player attribute NHReducedMotion): orbits at a third, no bob, the familiar only blinks, no trails.
	Characters within MAX_DIST of the camera. The welds are changed on this client only (it's cosmetic).
]]
local HttpService = game:GetService(`HttpService`)
local Players = game:GetService(`Players`)
local RunService = game:GetService(`RunService`)

local Player = Players.LocalPlayer
local MAX_DIST = 120
local Shared = {}
local States = {} :: { [Instance]: any }

local function parseBones(P: Instance)
	local Raw = P:GetAttribute(`NHIdleBones`)
	if typeof(Raw) ~= `string` or Raw == `` then return {} end
	local Ok, T = pcall(HttpService.JSONDecode, HttpService, Raw)
	if not Ok or typeof(T) ~= `table` then return {} end
	local Out = {}
	for Name, Spec in T do
		local B = P:FindFirstChild(Name, true)
		local A = typeof(Spec) == `table` and Spec.axis
		if B and B:IsA(`Bone`) and typeof(A) == `table` then
			local Axis = Vector3.new(tonumber(A[1]) or 0, tonumber(A[2]) or 0, tonumber(A[3]) or 0)
			if Axis.Magnitude > 0 then
				Out[Name] = { Bone = B; Axis = Axis.Unit; Min = math.rad(tonumber(Spec.min) or 0); Max = math.rad(tonumber(Spec.max) or 0);
					Value = 0; Target = 0; Next = 0 }
			end
		end
	end
	return Out
end

local function newState(P: BasePart)
	local W = P:FindFirstChild(`NHAccWeld`)
	local S = { Weld = if W and W:IsA(`Weld`) then W else nil; Angle = math.random() * math.pi * 2; Phase = math.random() * 6 }
	S.Base = S.Weld and S.Weld.C0
	S.Axis = P:GetAttribute(`NHOrbitAxis`)
	S.Rpm = tonumber(P:GetAttribute(`NHOrbitRpm`)) or 0
	S.Bob = tonumber(P:GetAttribute(`NHBob`)) or 0
	S.Idle = P:GetAttribute(`NHIdle`)
	S.Bones = if S.Idle then parseBones(P) else {}
	S.Lights = {}
	for _, L in P:GetDescendants() do
		if L:IsA(`Light`) and L:GetAttribute(`NHFlicker`) then table.insert(S.Lights, { Light = L; Base = L.Brightness }) end
	end
	S.Emitters = {}
	if P:GetAttribute(`NHTrail`) then
		for _, E in P:GetDescendants() do if E:IsA(`ParticleEmitter`) then table.insert(S.Emitters, E) end end
	end
	local SA = P:FindFirstChildOfClass(`SurfaceAppearance`)
	S.Flare = P:GetAttribute(`NHFlare`) == true and SA or nil
	S.Pulse = tonumber(P:GetAttribute(`NHPulse`))   -- seconds per slow glow pulse
	S.PulseSA = S.Pulse and SA or nil
	S.FlareBase = SA and SA.EmissiveStrength or 0
	return S
end

-- the idle bones, by role and group: a bone's name is <Role><Group>, Role one of Head, LidL, LidR, Tail, WingL, WingR,
-- Page<n> (a ledger's pages), Group an optional letter (two crows on one mantle: HeadA, LidLA... and HeadB...). Each
-- group keeps its own timers, so two creatures never blink or look round together.
local ROLES = { `LidL`, `LidR`, `WingL`, `WingR`, `Head`, `Tail` }
local function roleOf(Name: string): (string?, string)
	local P = string.match(Name, `^Page(%d+)`)
	if P then return `Page`, string.sub(Name, #`Page` + #P + 1) end
	for _, R in ROLES do
		if string.sub(Name, 1, #R) == R then return R, string.sub(Name, #R + 1) end
	end
	return nil, ``
end

local function idle(S, Dt: number, T: number, Reduced: boolean)
	S.Groups = S.Groups or {}
	for Name, E in S.Bones do
		local Role, G = roleOf(Name)
		if not Role then continue end
		local Grp = S.Groups[G]
		if not Grp then
			Grp = { Blink = T + 1 + math.random() * 4; Ruffle = T + 6 + math.random() * 8; Phase = math.random() * 6;
				Page = T + 3 + math.random() * 3; PageN = 0 }
			S.Groups[G] = Grp
		end
		if Role == `LidL` or Role == `LidR` then -- blink, 0.14 s, every 2-6 s
			if T >= Grp.Blink then Grp.Blink = T + 2 + math.random() * 4 Grp.BlinkT = T end
			local K = if Grp.BlinkT and T - Grp.BlinkT < 0.14 then math.sin((T - Grp.BlinkT) / 0.14 * math.pi) else 0
			E.Value = E.Min + (E.Max - E.Min) * K
		elseif Reduced then
			continue
		elseif Role == `Head` then -- look about: a new heading every 1.5-4 s, eased in
			if T >= E.Next then E.Next = T + 1.5 + math.random() * 2.5 E.Target = E.Min + (E.Max - E.Min) * math.random() end
			E.Value += (E.Target - E.Value) * math.min(1, Dt * 5)
		elseif Role == `Tail` then
			E.Value = (E.Min + E.Max) / 2 + (E.Max - E.Min) / 2 * math.sin(T * 1.7 + Grp.Phase) * 0.8
		elseif Role == `WingL` or Role == `WingR` then -- settle the wings now and then (0.7 s)
			if T >= Grp.Ruffle then Grp.Ruffle = T + 9 + math.random() * 8 Grp.RuffleT = T end
			local K = if Grp.RuffleT and T - Grp.RuffleT < 0.7 then math.sin((T - Grp.RuffleT) / 0.7 * math.pi) else 0
			E.Value = E.Min + (E.Max - E.Min) * K
		elseif Role == `Page` then -- a ledger: every 3-6 s the next page turns over (1.1 s), then they all lie back
			E.Index = E.Index or tonumber(string.match(Name, `^Page(%d+)`)) or 1
			if T >= Grp.Page then
				Grp.Page = T + 3 + math.random() * 3
				Grp.PageN += 1
				Grp.PageT = T
				Grp.PageCount = 0
				for N in S.Bones do if string.match(N, `^Page%d+` .. G .. `$`) then Grp.PageCount += 1 end end
				if Grp.PageN > Grp.PageCount then Grp.PageN = 0 Grp.ResetT = T end -- all turned: they settle back together
			end
			local K
			if Grp.PageN == 0 and Grp.ResetT then
				K = 1 - math.clamp((T - Grp.ResetT) / 1.4, 0, 1)
			elseif E.Index == Grp.PageN and Grp.PageT then
				K = math.clamp((T - Grp.PageT) / 1.1, 0, 1)
			else
				K = if E.Index < Grp.PageN then 1 else 0
			end
			K = K * K * (3 - 2 * K)
			E.Value = E.Min + (E.Max - E.Min) * K
		end
	end
	for _, E in S.Bones do
		E.Bone.Transform = CFrame.fromAxisAngle(E.Axis, math.clamp(E.Value, math.min(E.Min, E.Max), math.max(E.Min, E.Max)))
	end
end

local function step(Dt: number)
	local Cam = workspace.CurrentCamera
	if not Cam then return end
	Dt = math.clamp(Dt, 1 / 240, 1 / 15)
	local T = os.clock()
	local Reduced = Player:GetAttribute(`NHReducedMotion`) == true
	local Seen = {}
	for _, Pl in Players:GetPlayers() do
		local Char = Pl.Character
		local Root = Char and Char:FindFirstChild(`HumanoidRootPart`) :: BasePart?
		if not Root or (Root.Position - Cam.CFrame.Position).Magnitude > MAX_DIST then continue end
		local FlareAt = tonumber(Char:GetAttribute(`NHAdminFlare`))
		local Moving = (Root.AssemblyLinearVelocity * Vector3.new(1, 0, 1)).Magnitude > 2
		for _, M in Char:GetChildren() do
			if not (M:IsA(`Model`) and M:GetAttribute(`NHAcc`) ~= nil) then continue end
			for _, P in M:GetChildren() do
				if not P:IsA(`BasePart`) then continue end
				local S = States[P]
				if not S then
					if not (P:GetAttribute(`NHOrbitAxis`) or P:GetAttribute(`NHBob`) or P:GetAttribute(`NHIdle`)
						or P:GetAttribute(`NHFlare`) or P:GetAttribute(`NHTrail`) or P:GetAttribute(`NHPulse`) or P:FindFirstChildWhichIsA(`Light`, true)) then
						continue
					end
					S = newState(P)
					States[P] = S
				end
				Seen[P] = true
				if S.Weld and S.Base and (typeof(S.Axis) == `Vector3` and S.Rpm ~= 0 or S.Bob ~= 0) then
					local Rot = CFrame.identity
					if typeof(S.Axis) == `Vector3` and S.Axis.Magnitude > 0 and S.Rpm ~= 0 then
						S.Angle += S.Rpm / 60 * math.pi * 2 * Dt * (if Reduced then 1 / 3 else 1)
						Rot = CFrame.fromAxisAngle(S.Axis.Unit, S.Angle)
					end
					local Lift = if Reduced then 0 else math.sin(T * 1.3 + S.Phase) * S.Bob
					S.Weld.C0 = CFrame.new(0, Lift, 0) * Rot * S.Base
				end
				if S.Idle then idle(S, Dt, T, Reduced) end
				for _, L in S.Lights do
					local N = math.noise(T * 6, S.Phase) * 0.6 + math.noise(T * 17, S.Phase + 3) * 0.4
					L.Light.Brightness = L.Base * (if Reduced then 0.95 + 0.05 * N else 0.82 + 0.18 * N)
				end
				for _, E in S.Emitters do E.Enabled = Moving and not Reduced end
				if S.PulseSA and not S.Flare then
					local K = 0.5 + 0.5 * math.sin(T * math.pi * 2 / math.max(S.Pulse, 0.5) + S.Phase)
					S.PulseSA.EmissiveStrength = S.FlareBase * (if Reduced then 0.85 + 0.15 * K else 0.55 + 0.75 * K)
				end
				if S.Flare then
					local Since = if FlareAt then workspace:GetServerTimeNow() - FlareAt else math.huge
					local K = if Since >= 0 and Since < 1.6 then (1 - Since / 1.6) else 0
					S.Flare.EmissiveStrength = S.FlareBase * (1 + 2.5 * K)
				end
			end
		end
	end
	for P in States do
		if not Seen[P] or not P.Parent then States[P] = nil end
	end
end

function Shared.OnStart()
	RunService.PreSimulation:Connect(function(Dt)
		local Ok, Err = pcall(step, Dt)
		if not Ok then warn(`[AccessoryFx] {Err}`) end
	end)
end

return Shared
