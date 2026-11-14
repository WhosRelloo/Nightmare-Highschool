--[[
	WildWolves (server): wolves roam the grounds at night (the owner's rigged Wolf, ServerStorage.NHWolf).
	  * Spawn on parts tagged NHWolfSpawn (workspace.Map.NHHangouts: the west edge and south-west corner, away from
	  the school, 2026-11-02), else in the BoilerYard, after dark, up to MAX at once; gone by morning.
	  * Wander -> howl when they spot a student (calls the pack) -> a FIXED, telegraphed pattern:
	    Bite -> Bite -> hop back -> Leap (1.4 s punish window after it lands). Every attack glows red first;
	    only one wolf attacks you at a time while the rest circle.
	  * They take normal combat damage. Stun -> stun clip; posture break (Paralyzed) -> guard-broken clip.
	  * Death clip, then the killer gets EXP (Combat) and Yen; the body fades and a new wolf comes later.
	Damage to students goes through Downed.ApplyDamage (so a wolf can down you, never execute you).
]]
local Players = game:GetService(`Players`)
local ServerStorage = game:GetService(`ServerStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local CollectionService = game:GetService(`CollectionService`)
local Lighting = game:GetService(`Lighting`)

local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)

local MAX = 3
local HEALTH = 70
local SIGHT = 55
local BITE_RANGE = 5.5
local LEAP_MIN, LEAP_MAX = 9, 16
local BITE_DAMAGE, LEAP_DAMAGE = 5, 8
local REWARD_EXP, REWARD_YEN = 40, 15
local RESPAWN = 45

local Shared = {}
local Live = {} :: { [Model]: any }
local Pending = 0 -- (audit) wolves that died and are waiting out RESPAWN; Fill counts them, so the 10 s loop can't replace them early
local Folder: Folder? = nil

local function isNight(): boolean
	local T = Lighting.ClockTime
	return T >= 19.5 or T < 5.5
end

local function spawnPoints(): { Vector3 }
	local Out = {}
	for _, P in CollectionService:GetTagged(`NHWolfSpawn`) do
		if P:IsA(`BasePart`) then table.insert(Out, P.Position) end
	end
	if #Out == 0 then
		local Yard = workspace:FindFirstChild(`School`) and workspace.School:FindFirstChild(`BoilerYard`)
		if Yard then
			local CF, Size = Yard:GetBoundingBox()
			for _, Off in { Vector3.new(-0.3, 0, -0.3), Vector3.new(0.3, 0, 0.25), Vector3.new(0, 0, 0.35), Vector3.new(-0.25, 0, 0.3) } do
				table.insert(Out, (CF * CFrame.new(Size.X * Off.X, 0, Size.Z * Off.Z)).Position)
			end
		end
	end
	return Out
end

local function ground(At: Vector3): Vector3?
	local P = RaycastParams.new()
	P.FilterType = Enum.RaycastFilterType.Exclude
	P.FilterDescendantsInstances = { workspace:FindFirstChild(`Live`), Folder }
	local Hit = workspace:Raycast(At + Vector3.new(0, 30, 0), Vector3.new(0, -80, 0), P)
	return Hit and Hit.Normal.Y > 0.6 and Hit.Position or nil
end

local function nearestStudent(From: Vector3, Range: number): Model?
	local Best, BestD = nil, Range
	for _, P in Players:GetPlayers() do
		local C = P.Character
		local R = C and C:FindFirstChild(`HumanoidRootPart`)
		local H = C and C:FindFirstChildWhichIsA(`Humanoid`)
		if R and H and H.Health > 0 and not P:GetAttribute(`InMainMenu`) and not H:GetAttribute(`Downed`) then -- (audit) Downed is on the Humanoid
			local D = (R.Position - From).Magnitude
			if D < BestD then Best, BestD = C, D end
		end
	end
	return Best
end

local function play(W, Name: string, Fade: number?, Looped: boolean?)
	local T = W.Tracks[Name]
	if not T then return nil end
	if W.Loop and W.Loop ~= T and (Looped or Name == `Death`) then W.Loop:Stop(0.15) end
	if Looped then
		if W.Loop == T and T.IsPlaying then return T end
		W.Loop = T
	end
	T:Play(Fade or 0.1)
	return T
end

local function hurt(W, Target: Model, Amount: number)
	pcall(function()
		require(ServerScriptService.Services.Features.Downed).ApplyDamage(Target, Amount, W.Model)
	end)
end

local function spawnWolf(At: Vector3)
	local Src = ServerStorage:FindFirstChild(`NHWolf`)
	if not Src then return end
	local Floor = ground(At)
	if not Floor then return end
	local M = Src.Wolf:Clone()
	M.Name = `Wild Wolf`
	local Hum = M:FindFirstChildWhichIsA(`Humanoid`)
	Hum.MaxHealth, Hum.Health = HEALTH, HEALTH
	Hum.WalkSpeed = 8
	Hum.BreakJointsOnDeath = false
	Hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	M:PivotTo(CFrame.new(Floor + Vector3.new(0, 3, 0)) * CFrame.Angles(0, math.random() * math.pi * 2, 0))
	M:SetAttribute(`NHWolf`, true)
	M:SetAttribute(`NoDowned`, true) -- wolves die, they don't get downed and gripped
	M.Parent = Folder
	local Animator = Hum:FindFirstChildOfClass(`Animator`) or Instance.new(`Animator`, Hum)
	local W = { Model = M; Hum = Hum; Root = M:FindFirstChild(`HumanoidRootPart`); Tracks = {}; Home = Floor; NextBite = 0; NextLeap = 0; Howled = false; Busy = false; LastHit = nil }
	for _, A in Src.Animations:GetChildren() do
		local Ok, T = pcall(function() return Animator:LoadAnimation(A) end)
		if Ok then
			T.Looped = A.Name == `Idle` or A.Name == `Walk` or A.Name == `Run`
			T.Priority = if T.Looped then Enum.AnimationPriority.Movement else Enum.AnimationPriority.Action
			W.Tracks[A.Name] = T
		end
	end
	pcall(function() W.Root:SetNetworkOwner(nil) end)
	play(W, `Idle`, 0, true)
	Live[M] = W
	-- who hit it last gets the kill
	Hum:GetAttributeChangedSignal(`LastAttacker`):Connect(function() W.LastHit = Hum:GetAttribute(`LastAttacker`) end)
	Hum.HealthChanged:Connect(function(H)
		if H < (W.LastHealth or HEALTH) then
			W.Hurt = os.clock()
			if not W.Target then
				W.Target = nearestStudent(W.Root.Position, SIGHT * 1.5) -- hit it and it comes for you
			end
		end
		W.LastHealth = H
	end)
	Hum.Died:Connect(function()
		Live[M] = nil
		play(W, `Death`, 0.1)
		local Killer = nil
		pcall(function() Killer = require(ServerScriptService.Services.Features.Downed).GetKiller(M) end)
		local P = Killer and Players:GetPlayerFromCharacter(Killer)
		P = P or (W.Target and Players:GetPlayerFromCharacter(W.Target))
		if P then
			pcall(function() require(ServerScriptService.Services.Player.Progression).Award(P, REWARD_EXP, `Combat`, `Wolf`) end)
			pcall(function() require(ServerScriptService.Services.Player.Data).UpdateState(P, { type = `UpdateYen`; amount = REWARD_YEN }) end)
		end
		task.delay(4, function()
			for _, D in M:GetDescendants() do
				if D:IsA(`BasePart`) then game:GetService(`TweenService`):Create(D, TweenInfo.new(1.5), { Transparency = 1 }):Play() end
			end
			task.delay(1.6, function() M:Destroy() end)
		end)
		Pending += 1
		task.delay(RESPAWN, function() Pending = math.max(0, Pending - 1) if isNight() then Shared.Fill() end end)
	end)
end

function Shared.Fill()
	if not isNight() then return end
	local N = Pending
	for _ in Live do N += 1 end
	local Points = spawnPoints()
	if #Points == 0 then return end
	while N < MAX do
		spawnWolf(Points[math.random(#Points)] + Vector3.new(math.random(-6, 6), 0, math.random(-6, 6)))
		N += 1
	end
end

-- fixed, telegraphed fight pattern (replaces the random bite/leap logic in WildWolves)
-- Cycle per wolf: Bite -> Bite -> Retreat -> Leap (with a 1.4 s punish window after landing).
-- Every attack is announced: the wolf stops, crouches and its eyes + outline glow red for TELL seconds.
-- Only one wolf attacks a given student at a time (the attack token); the rest circle at a distance.
local PATTERN = { `Bite`, `Bite`, `Retreat`, `Leap` }
local TELL_BITE, TELL_LEAP = 0.5, 0.85
local RECOVER = 1.4
local CIRCLE_NEAR, CIRCLE_FAR = 10, 14
local AttackToken = {} :: { [Model]: any }
-- the turn expires if its holder stops making progress (stunned, stuck, posture-broken): no deadlocks
local TURN_STALE = 3
local function claim(T: Model, W) AttackToken[T] = { W = W; t = os.clock() } end
local function release(T: Model, W) local h = AttackToken[T] if h and h.W == W then AttackToken[T] = nil end end
local function holderOf(T: Model)
	local h = AttackToken[T]
	if not h then return nil end
	if not h.W.Model.Parent or os.clock() - h.t > TURN_STALE then AttackToken[T] = nil return nil end
	return h.W
end

local function tell(W, On: boolean, Strong: boolean?)
	local M = W.Model
	local H = M:FindFirstChild(`NHTell`)
	if not H then
		H = Instance.new(`Highlight`)
		H.Name = `NHTell`
		H.FillColor = Color3.fromRGB(255, 40, 40)
		H.OutlineColor = Color3.fromRGB(255, 70, 50)
		H.DepthMode = Enum.HighlightDepthMode.Occluded
		H.Parent = M
		local head = M:FindFirstChild(`Head`) or W.Root
		local L = Instance.new(`PointLight`)
		L.Name = `NHTellLight`
		L.Color = Color3.fromRGB(255, 50, 40)
		L.Range = 9
		L.Parent = head
	end
	H.Enabled = On
	H.FillTransparency = if Strong then 0.55 else 0.8
	local L = M:FindFirstChild(`NHTellLight`, true)
	if L then L.Brightness = On and (Strong and 4 or 2.5) or 0 end
end

local function stunned(W): boolean
	return StateManager.HasState(W.Model, { `Stun`, `ParryStun`, `Paralyzed` })
end

local function face(W, TR: BasePart)
	W.Root.CFrame = CFrame.lookAt(W.Root.Position, Vector3.new(TR.Position.X, W.Root.Position.Y, TR.Position.Z))
end

local function mouth(W): Vector3
	local h = W.Model:FindFirstChild(`Head`)
	return if h and h:IsA(`BasePart`) then h.Position else W.Root.Position + W.Root.CFrame.LookVector * 2
end

local function inFront(W, TR: BasePart, Range: number): boolean
	local d = (TR.Position - mouth(W)) * Vector3.new(1, 0, 1)
	if d.Magnitude > Range then return false end
	return d.Magnitude < 1 or W.Root.CFrame.LookVector:Dot(d.Unit) > 0.35
end

local function endStep(W, Target: Model, Rest: number)
	release(Target, W)
	W.Step = (W.Step % #PATTERN) + 1
	W.CircleUntil = os.clock() + Rest
	W.Busy = false
end

-- the wolf commits to the wind-up; getting hit during it interrupts the attack
local function windUp(W, Dur: number, Strong: boolean?): boolean
	W.Hum:MoveTo(W.Root.Position)
	play(W, `Idle`, 0.1, true)
	tell(W, true, Strong)
	local hurtAt = W.Hurt or 0
	local t0 = os.clock()
	while os.clock() - t0 < Dur do
		task.wait(0.05)
		if not W.Model.Parent or stunned(W) or (W.Hurt or 0) > hurtAt then tell(W, false) return false end
	end
	tell(W, false)
	return true
end

local function bite(W, Target: Model)
	W.Busy = true
	claim(Target, W)
	local TR = Target:FindFirstChild(`HumanoidRootPart`)
	if not TR then return endStep(W, Target, 0.6) end
	face(W, TR)
	if not windUp(W, TELL_BITE) then return endStep(W, Target, 1.0) end
	local T = play(W, if W.Step == 1 then `Bite1` else `Bite2`, 0.05)
	-- a short scripted step-in closes the last gap (the Humanoid ignores raw velocity)
	if W.Model.Parent then
		local gap = ((TR.Position - mouth(W)) * Vector3.new(1, 0, 1)).Magnitude
		local stepIn = math.clamp(gap - 2.2, 0, 4)
		if stepIn > 0.2 then
			local from = W.Root.CFrame
			local to = from + from.LookVector * stepIn
			W.Root.Anchored = true
			for k = 1, 4 do W.Root.CFrame = from:Lerp(to, k / 4) task.wait() end
			if W.Model.Parent then W.Root.Anchored = false end
		end
	end
	task.wait(0.28)
	-- only lands if the student is still close and in front: back off or sidestep during the tell to dodge
	if W.Model.Parent and not stunned(W) and inFront(W, TR, BITE_RANGE) then hurt(W, Target, BITE_DAMAGE) end
	task.wait(math.max(0.25, (T and T.Length or 0.8) - 0.28))
	endStep(W, Target, 0.55)
end

local function retreat(W, Target: Model)
	W.Busy = true
	play(W, `JumpBack`, 0.05)
	W.Root.AssemblyLinearVelocity = -W.Root.CFrame.LookVector * 34 + Vector3.new(0, 18, 0)
	task.wait(0.6)
	endStep(W, Target, 1.4)
end

local function leap(W, Target: Model)
	W.Busy = true
	claim(Target, W)
	local TR = Target:FindFirstChild(`HumanoidRootPart`)
	if not TR then return endStep(W, Target, 0.6) end
	face(W, TR)
	if not windUp(W, TELL_LEAP, true) then return endStep(W, Target, 1.0) end
	-- the direction locks here: a sidestep after the tell makes it miss
	local Dir = (TR.Position - W.Root.Position) * Vector3.new(1, 0, 1)
	play(W, `JumpBite`, 0.05)
	task.wait(0.1)
	-- a scripted arc to where the student stood when the tell ended (the Humanoid eats raw velocity)
	local hit = false
	if W.Model.Parent and Dir.Magnitude > 0.1 then
		local from = W.Root.Position
		local land = math.max(0, Dir.Magnitude - 2.5)
		local to = from + Dir.Unit * land
		local ok, floor = pcall(function()
			local p = RaycastParams.new()
			p.FilterType = Enum.RaycastFilterType.Exclude
			p.FilterDescendantsInstances = { workspace:FindFirstChild(`Live`) }
			return workspace:Raycast(to + Vector3.new(0, 6, 0), Vector3.new(0, -14, 0), p)
		end)
		if ok and floor then to = Vector3.new(to.X, floor.Position.Y + (from.Y - (ground(from) or from).Y), to.Z) else to = Vector3.new(to.X, from.Y, to.Z) end
		W.Hum.PlatformStand = true
		W.Root.Anchored = true
		local dur = 0.42
		local t0 = os.clock()
		while W.Model.Parent do
			local t = math.min(1, (os.clock() - t0) / dur)
			local p = from:Lerp(to, t) + Vector3.new(0, math.sin(t * math.pi) * 3.2, 0)
			W.Root.CFrame = CFrame.lookAt(p, p + Dir.Unit)
			if not hit and (TR.Position - mouth(W)).Magnitude <= 4 then hit = true hurt(W, Target, LEAP_DAMAGE) end
			if t >= 1 then break end
			task.wait()
		end
		if W.Model.Parent then W.Root.Anchored = false W.Hum.PlatformStand = false end
	end
	-- the punish window: it lands, pants, and stands still
	task.wait(0.15)
	if W.Model.Parent then
		W.Recovering = true
		W.Hum:MoveTo(W.Root.Position)
		play(W, `Idle`, 0.15, true)
		task.wait(RECOVER)
		W.Recovering = false
	end
	endStep(W, Target, 2.6)
end

local function circle(W, TR: BasePart, Radius: number)
	W.Orbit = (W.Orbit or math.random() * math.pi * 2) + 0.35 * (W.OrbitDir or 1)
	if math.random() < 0.02 then W.OrbitDir = -(W.OrbitDir or 1) end
	local pos = TR.Position + Vector3.new(math.cos(W.Orbit), 0, math.sin(W.Orbit)) * Radius
	W.Hum.WalkSpeed = 13
	W.Hum:MoveTo(pos)
	play(W, `Walk`, 0.2, true)
end

local function think(W)
	local M, Hum, Root = W.Model, W.Hum, W.Root
	if not (M.Parent and Root and Hum.Health > 0) or W.Busy then return end
	if StateManager.HasState(M, { `Paralyzed`, `Stun`, `ParryStun` }) and W.Target then release(W.Target, W) end
	if StateManager.HasState(M, `Paralyzed`) then
		if not W.Staggered then W.Staggered = true play(W, `GuardBroken`, 0.05) end
		Hum:MoveTo(Root.Position)
		return
	end
	if StateManager.HasState(M, { `Stun`, `ParryStun` }) then
		if not W.Staggered then W.Staggered = true play(W, if math.random() < 0.5 then `Stun1` else `Stun2`, 0.05) end
		Hum:MoveTo(Root.Position)
		return
	end
	W.Staggered = false
	W.Step = W.Step or 1
	local T = W.Target
	local TR = T and T.Parent and T:FindFirstChild(`HumanoidRootPart`)
	local TH = T and T:FindFirstChildWhichIsA(`Humanoid`)
	if not (TR and TH and TH.Health > 0) or TH:GetAttribute(`Downed`) or (TR.Position - Root.Position).Magnitude > SIGHT * 1.6 then
		if T then release(T, W) end
		W.Target, T, TR = nil, nil, nil
		local Seen = nearestStudent(Root.Position, SIGHT)
		if Seen then
			W.Target, T = Seen, Seen
			TR = Seen:FindFirstChild(`HumanoidRootPart`)
			W.Step = 1
			W.CircleUntil = os.clock() + 1.5      -- it sizes you up before the first bite
			if not W.Howled then
				W.Howled = true
				W.Busy = true
				Hum:MoveTo(Root.Position)
				play(W, `Howl`, 0.1)
				for Other, OW in Live do
					if Other ~= M and (OW.Root.Position - Root.Position).Magnitude < 90 and not OW.Target then
						OW.Target = Seen OW.Howled = true OW.Step = 1 OW.CircleUntil = os.clock() + 2.5
					end
				end
				task.delay(1.6, function() W.Busy = false end)
				return
			end
		end
	end
	if not TR then
		Hum.WalkSpeed = 7
		if not W.WanderTo or (Root.Position - W.WanderTo).Magnitude < 3 or os.clock() > (W.WanderUntil or 0) then
			W.WanderTo = W.Home + Vector3.new(math.random(-18, 18), 0, math.random(-18, 18))
			W.WanderUntil = os.clock() + 6
			if math.random() < 0.35 then W.WanderTo = Root.Position end
		end
		Hum:MoveTo(W.WanderTo)
		play(W, if (Root.Position - W.WanderTo).Magnitude > 2 then `Walk` else `Idle`, 0.2, true)
		return
	end
	-- one attacker at a time: everyone else circles wide and waits their turn
	local holder = holderOf(T)
	if holder and holder ~= W then circle(W, TR, CIRCLE_FAR) return end
	if os.clock() < (W.CircleUntil or 0) then circle(W, TR, CIRCLE_NEAR) return end
	local Dist = (TR.Position - Root.Position).Magnitude
	claim(T, W) -- claim (and keep refreshing) the turn while closing in
	local step = PATTERN[W.Step]
	if step == `Bite` then
		local JawDist = ((TR.Position - mouth(W)) * Vector3.new(1, 0, 1)).Magnitude
		W.ApproachSince = W.ApproachSince or os.clock()
		if JawDist <= BITE_RANGE or (os.clock() - W.ApproachSince > 2.5 and Dist <= 10) then W.ApproachSince = nil task.spawn(bite, W, T) return end
		if os.clock() - W.ApproachSince > 5 then W.ApproachSince = nil endStep(W, T, 1.2) return end -- give the turn away
		Hum.WalkSpeed = 20
		Hum:MoveTo(TR.Position - (TR.Position - Root.Position).Unit * 3)
		play(W, `Run`, 0.15, true)
	elseif step == `Retreat` then
		task.spawn(retreat, W, T)
	elseif step == `Leap` then
		if Dist >= LEAP_MIN and Dist <= LEAP_MAX then task.spawn(leap, W, T) return end
		Hum.WalkSpeed = 16
		local away = (Root.Position - TR.Position) * Vector3.new(1, 0, 1)
		local want = TR.Position + (if away.Magnitude > 0.1 then away.Unit else Vector3.xAxis) * ((LEAP_MIN + LEAP_MAX) / 2)
		Hum:MoveTo(want)
		play(W, `Run`, 0.15, true)
	end
end

function Shared.OnStart()
	Folder = Instance.new(`Folder`)
	Folder.Name = `NHWolves`
	Folder.Parent = workspace:FindFirstChild(`Live`) or workspace -- in Live so combat hitboxes and lock-on see them
	task.spawn(function()
		while true do
			task.wait(0.15)
			for _, W in Live do task.spawn(think, W) end
		end
	end)
	task.spawn(function()
		while true do
			if isNight() then
				Shared.Fill()
			else
				for M in Live do Live[M] = nil M:Destroy() end -- they melt away by morning
			end
			task.wait(10)
		end
	end)
end

return Shared
