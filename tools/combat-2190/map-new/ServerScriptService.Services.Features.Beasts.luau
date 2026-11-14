--[[
	Beasts (server). Services.Features.Beasts          (design: docs/superpowers/specs/2026-11-05-beasts-design.md)
	Every beast in ReplicatedStorage.Config.Beasts, run from its data. The wolves (Features.WildWolves) stay separate.

	  * At night (Config.Beasts.Night) each beast fills its lairs: parts tagged NHBeastLair whose Beast attribute is
	    its Spawn.Lair (else its Spawn.Fallback School part), up to Spawn.Max. It roams near its lair; they melt away by
	    morning. A dead beast comes back Spawn.Respawn seconds later.
	  * It spots a student within Sight, plays its Sighted clip once (a fair warning), then fights in its fixed Pattern
	    (Config moves: Melee, Breath, Leap, Hop). Special moves show the Kanji first (Indicators.BeastTell); normal
	    attacks have none. Every special leaves an opening afterwards, so the fight can be won.
	  * One beast attacks a given student at a time; the rest circle. It gives up past its Leash and walks home.
	  * Students' hits stun it (Stun1 / Stun2); a posture break (Paralyzed) plays GuardBroken.
	  * Its damage goes through Downed.ApplyDamage (it can down you, never execute you). It's NoDowned: it dies outright.
	  * Death: its Death clip, then the killer gets Reward.Exp (Combat), Reward.Yen and a rare trophy
	    (Reward.Trophy, Config.Items, into the Locker); the body fades.
	  * Ambushers (Config Ambush, the Grave Ghoul) wait buried; a student near the grave gets churning dirt and the Kanji,
	    then it bursts up (Emerge), hitting anyone right on top. With nobody about it walks home and digs back in.
	  * Ambush From = Above (the Bone Spider) hangs on a silk thread over its lair instead: the Kanji shows on the floor
	    under it, then it drops. Alone again, it climbs its thread back up.
	  * Spit (the Bone Spider's WebSpit): a glob of silk at where you stood when the Kanji ended; a hit slows you.
	  * The Crypt Bat flies by hovering (a tall HipHeight). Its Dive is a Leap that swoops down (a negative Arc) and carries
	    on past you (Through); its Screech stuns everyone in a cone in front of it.
	  * A clip with no AnimationId (not published yet) plays from its KeyframeSequence in
	    ServerStorage.NHBeasts.Clips.<Model> in Studio.
	Public: Shared.Fill(), Shared.SpawnAt(Name, CFrame) (admin / tests; any time of day), Shared.Clear(), Shared.Count(),
	Shared.Bury(W).
]]
local Players = game:GetService(`Players`)
local ServerStorage = game:GetService(`ServerStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local CollectionService = game:GetService(`CollectionService`)
local Lighting = game:GetService(`Lighting`)
local TweenService = game:GetService(`TweenService`)
local RunService = game:GetService(`RunService`)
local KeyframeSequenceProvider = game:GetService(`KeyframeSequenceProvider`)

local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local Config = require(ReplicatedStorage.Config.Beasts)

local CIRCLE_NEAR, CIRCLE_FAR = 11, 16

local Shared = {}
local Live = {} :: { [Model]: any }
local Pending = {} :: { [string]: number } -- dead beasts waiting out their respawn, by beast name
local Folder: Folder? = nil
local AttackToken = {} :: { [Model]: { W: any, t: number } }

---| helpers |---

local function isNight(): boolean return Config.IsNight(Lighting.ClockTime) end

local function packets()
	local Ok, P = pcall(require, ReplicatedStorage.Remotes.Packets)
	return Ok and P or nil
end

local function ground(At: Vector3): Vector3?
	local P = RaycastParams.new()
	P.FilterType = Enum.RaycastFilterType.Exclude
	P.FilterDescendantsInstances = { workspace:FindFirstChild(`Live`), Folder }
	local Hit = workspace:Raycast(At + Vector3.new(0, 30, 0), Vector3.new(0, -80, 0), P)
	return Hit and Hit.Normal.Y > 0.6 and Hit.Position or nil
end

local function lairs(Def): { Vector3 }
	local Out = {}
	for _, P in CollectionService:GetTagged(`NHBeastLair`) do
		if P:IsA(`BasePart`) and P:GetAttribute(`Beast`) == Def.Spawn.Lair then table.insert(Out, P.Position) end
	end
	if #Out == 0 and Def.Spawn.Fallback then
		local Spot = workspace:FindFirstChild(`School`) and workspace.School:FindFirstChild(Def.Spawn.Fallback)
		if Spot then
			local CF = if Spot:IsA(`Model`) then Spot:GetBoundingBox() elseif Spot:IsA(`BasePart`) then Spot.CFrame else nil
			if CF then table.insert(Out, CF.Position) end
		end
	end
	return Out
end

local function nearestStudent(From: Vector3, Range: number): Model?
	local Best, BestD = nil, Range
	for _, P in Players:GetPlayers() do
		local C = P.Character
		local R = C and C:FindFirstChild(`HumanoidRootPart`)
		local H = C and C:FindFirstChildWhichIsA(`Humanoid`)
		if R and H and H.Health > 0 and not P:GetAttribute(`InMainMenu`) and not H:GetAttribute(`Downed`) then
			local D = (R.Position - From).Magnitude
			if D < BestD then Best, BestD = C, D end
		end
	end
	return Best
end

local function play(W, Name: string, Fade: number?, Looped: boolean?)
	local T = W.Tracks[Name]
	if not T then return nil end
	if W.Hum.Health <= 0 and Name ~= `Death` then return nil end -- nothing plays over its death (a move in flight when it died)
	if W.Loop and W.Loop ~= T and (Looped or Name == `Death`) then W.Loop:Stop(0.15) end
	if Looped then
		if W.Loop == T and T.IsPlaying then return T end
		W.Loop = T
	end
	T:Play(Fade or 0.1)
	return T
end

local function hurt(W, Target: Model, Amount: number)
	if W.Hum.Health <= 0 then return end -- a dead beast's last swing doesn't land
	pcall(function() require(ServerScriptService.Services.Features.Downed).ApplyDamage(Target, Amount, W.Model) end)
end

-- a beast's pieces stop (or start again) colliding. An R15 beast's torso and head are their own physical pieces (joined by
-- AnimationConstraints): buried under the floor they'd be trapped below it and drag the body down, so they pass through
-- the ground while it's buried, rising or sinking. And a body moved by script through a student (a dive, a pin at death)
-- would fling them, so it isn't solid then either
local function solid(M: Model, On: boolean)
	for _, P in M:GetDescendants() do
		if P:IsA(`BasePart`) then
			if not On then
				if P:GetAttribute(`NHCollide`) == nil then P:SetAttribute(`NHCollide`, P.CanCollide) end
				P.CanCollide = false
			elseif P:GetAttribute(`NHCollide`) ~= nil then
				P.CanCollide = P:GetAttribute(`NHCollide`)
				P:SetAttribute(`NHCollide`, nil)
			end
		end
	end
end

-- a posture break (Paralyzed) always stops it. An ordinary stun doesn't during its StunGuard: for a moment after a stun
-- wears off it shrugs hits off, so mashing attacks can't stun-lock it (you win by dodging and punishing its openings)
local function guarded(W): boolean return os.clock() < (W.GuardUntil or 0) end
local function stunned(W): boolean
	if StateManager.HasState(W.Model, `Paralyzed`) then return true end
	return not guarded(W) and StateManager.HasState(W.Model, { `Stun`, `ParryStun` })
end

local function face(W, TR: BasePart)
	W.Root.CFrame = CFrame.lookAt(W.Root.Position, Vector3.new(TR.Position.X, W.Root.Position.Y, TR.Position.Z))
end

-- where a student is, in the beast's own frame: Ahead (studs in front of its root), Side (studs off its centre line), Up
local function rel(W, Pos: Vector3): (number, number, number)
	local r = W.Root.CFrame:PointToObjectSpace(Pos)
	return -r.Z, math.abs(r.X), r.Y
end

-- a hit lands on a student in front of the beast, out to its mouth plus Range, about as wide as its head. Measured from
-- the body, not the mouth: a big beast's mouth is studs ahead of its middle, and a student pressed against its chest is
-- "behind" the mouth but very much in reach. Ignore Height for an attack in the air (the pounce's arc).
local function inReach(W, Pos: Vector3, Range: number, IgnoreHeight: boolean?): boolean
	local Ahead, Side, Up = rel(W, Pos)
	return Ahead > -1 and Ahead <= W.Reach + Range and Side <= W.Width and (IgnoreHeight or math.abs(Up) < 7)
end

local function claim(T: Model, W) AttackToken[T] = { W = W; t = os.clock() } end
local function release(T: Model, W) local h = AttackToken[T] if h and h.W == W then AttackToken[T] = nil end end
local function holderOf(T: Model)
	local h = AttackToken[T]
	if not h then return nil end
	if not h.W.Model.Parent or os.clock() - h.t > Config.TurnStale then AttackToken[T] = nil return nil end
	return h.W
end

local function endStep(W, Target: Model, Rest: number)
	release(Target, W)
	W.Step = (W.Step % #W.Def.Pattern) + 1
	W.CircleUntil = os.clock() + Rest
	W.Busy = false
end

-- stand still for Dur seconds (the Kanji first on a special); a hit or a stun during it calls the move off
local function windUp(W, Dur: number, Special: boolean?): boolean
	W.Hum:MoveTo(W.Root.Position)
	play(W, `Idle`, 0.1, true)
	if Special then
		local P = packets()
		if P then pcall(function() P.Replicate:Fire(`Indicators`, `BeastTell`, { User = W.Model }) end) end
	end
	local hurtAt = W.Hurt or 0
	local t0 = os.clock()
	while os.clock() - t0 < Dur do
		task.wait(0.05)
		if not W.Model.Parent or W.Hum.Health <= 0 or stunned(W) or ((W.Hurt or 0) > hurtAt and not guarded(W)) then return false end
	end
	return true
end

---| moves |---

local Moves = {}

function Moves.Melee(W, Target: Model, M)
	local TR = Target:FindFirstChild(`HumanoidRootPart`)
	if not TR then return endStep(W, Target, 0.6) end
	face(W, TR)
	if not windUp(W, M.WindUp or 0.4, M.Special) then return endStep(W, Target, 1.0) end
	local T = play(W, M.Clip, 0.05)
	-- a short scripted step-in closes the last gap (the Humanoid ignores raw velocity): it brings the mouth to you
	if W.Model.Parent then
		local Ahead = rel(W, TR.Position)
		local stepIn = math.clamp(Ahead - W.Reach - 1, 0, 4)
		if stepIn > 0.2 then
			local from = W.Root.CFrame
			local to = from + from.LookVector * stepIn
			W.Root.Anchored = true
			for k = 1, 4 do W.Root.CFrame = from:Lerp(to, k / 4) task.wait() end
			if W.Model.Parent then W.Root.Anchored = false end
		end
	end
	task.wait(M.HitAt or 0.3)
	-- it only lands if you're still close and in front: back off or sidestep to dodge
	if W.Model.Parent and not stunned(W) and inReach(W, TR.Position, M.Range) then hurt(W, Target, M.Damage) end
	task.wait(math.max(0.25, (T and T.Length or 0.8) - (M.HitAt or 0.3)))
	endStep(W, Target, M.Rest or 0.7)
end

function Moves.Breath(W, Target: Model, M)
	local TR = Target:FindFirstChild(`HumanoidRootPart`)
	if not TR then return endStep(W, Target, 0.6) end
	face(W, TR)
	if not windUp(W, M.Tell or 0.9, true) then return endStep(W, Target, 1.0) end
	-- the aim locks here: step out of the cone to dodge it. The cone starts head-wide at the mouth and widens by Angle
	local Aim = W.Root.CFrame
	local Tan = math.tan(math.rad(M.Angle or 24))
	local T = play(W, M.Clip, 0.05)
	if T then T:AdjustSpeed(0.45) end
	local FX = ReplicatedStorage:FindFirstChild(`Beasts`) and ReplicatedStorage.Beasts:FindFirstChild(`HellhoundFX`)
	local Fx = FX and require(FX)
	if Fx then Fx.Breath(W.Model, true) end
	local t0 = os.clock()
	while os.clock() - t0 < (M.Duration or 1.4) and W.Model.Parent and not stunned(W) do
		for _, P in Players:GetPlayers() do
			local C = P.Character
			local R = C and C:FindFirstChild(`HumanoidRootPart`)
			if R then
				local r = Aim:PointToObjectSpace(R.Position)
				local Ahead, Side = -r.Z, math.abs(r.X)
				local Wide = W.Width + math.max(0, Ahead - W.Reach) * Tan
				if Ahead > -1 and Ahead <= W.Reach + (M.Range or 15) and Side <= Wide and math.abs(r.Y) < 7 then
					hurt(W, C, M.Damage or 3)
				end
			end
		end
		task.wait(M.Tick or 0.2)
	end
	if Fx and W.Model.Parent then Fx.Breath(W.Model, false) end
	if T then T:Stop(0.2) end
	-- the opening: it stands catching its breath
	if W.Model.Parent then W.Hum:MoveTo(W.Root.Position) play(W, `Idle`, 0.15, true) end
	endStep(W, Target, M.Rest or 1.8)
end

function Moves.Hop(W, Target: Model, M)
	play(W, M.Clip, 0.05)
	-- only spring back onto floor (never off an edge)
	if ground(W.Root.Position - W.Root.CFrame.LookVector * 9) then
		W.Root.AssemblyLinearVelocity = -W.Root.CFrame.LookVector * 34 + Vector3.new(0, 18, 0)
	end
	task.wait(0.6)
	endStep(W, Target, M.Rest or 1.0)
end

function Moves.Leap(W, Target: Model, M)
	local TR = Target:FindFirstChild(`HumanoidRootPart`)
	if not TR then return endStep(W, Target, 0.6) end
	face(W, TR)
	if not windUp(W, M.Tell or 0.95, true) then return endStep(W, Target, 1.0) end
	-- the direction locks here: a sidestep after the Kanji makes it miss
	local Dir = (TR.Position - W.Root.Position) * Vector3.new(1, 0, 1)
	play(W, M.Clip, 0.05)
	task.wait(0.1)
	local hit = false
	if W.Model.Parent and Dir.Magnitude > 0.1 then
		local from = W.Root.Position
		-- it lands with its jaws where you stood (Through: a flyer's dive carries on past you instead)
		local land = if M.Through then Dir.Magnitude + M.Through else math.max(0, Dir.Magnitude - W.Reach)
		local to = from + Dir.Unit * land
		local floor = ground(to)
		if not floor then to, floor = from, ground(from) end -- no floor there: it pounces on the spot rather than off an edge
		local fromFloor = ground(from) or from
		to = if floor then Vector3.new(to.X, floor.Y + (from.Y - fromFloor.Y), to.Z) else Vector3.new(to.X, from.Y, to.Z)
		W.Hum.PlatformStand = true
		W.Root.Anchored = true
		-- not solid in the air: a body moved through a student (the bat's dive goes right through you) would fling them
		solid(W.Model, false)
		local dur = M.Dur or 0.48
		local t0 = os.clock()
		while W.Model.Parent do
			local t = math.min(1, (os.clock() - t0) / dur)
			-- Arc: how high it bounds (a negative Arc swoops down: the bat's dive)
			local p = from:Lerp(to, t) + Vector3.new(0, math.sin(t * math.pi) * (M.Arc or 3.6), 0)
			W.Root.CFrame = CFrame.lookAt(p, p + Dir.Unit)
			if not hit and t > 0.35 and inReach(W, TR.Position, 1.5, true) then hit = true hurt(W, Target, M.Damage) end
			if t >= 1 then break end
			task.wait()
		end
		if W.Model.Parent then
			-- solid again only once nobody is inside it
			local Clear = true
			for _, Pl in Players:GetPlayers() do
				local R = Pl.Character and Pl.Character:FindFirstChild(`HumanoidRootPart`)
				if R and (R.Position - W.Root.Position).Magnitude < W.Root.Size.Magnitude / 2 + 2 then Clear = false end
			end
			if Clear then solid(W.Model, true) else task.delay(0.6, function() if W.Model.Parent and W.Hum.Health > 0 then solid(W.Model, true) end end) end
			W.Root.Anchored = false
			W.Hum.PlatformStand = false
		end
	end
	-- the opening: it lands, pants, and stands still
	task.wait(0.15)
	if W.Model.Parent then
		W.Recovering = true
		W.Hum:MoveTo(W.Root.Position)
		play(W, `Idle`, 0.15, true)
		task.wait(M.Recover or 1.8)
		W.Recovering = false
	end
	endStep(W, Target, M.Rest or 2.4)
end

-- Grab (the Grave Ghoul): after the Kanji it lunges with both claws (the direction locks at the end of the Kanji). Caught,
-- you're held stunned in front of it for Hold seconds, then slammed down for Damage. Another student hitting it breaks
-- the hold. A miss leaves it stumbling: a long opening (Miss).
function Moves.Grab(W, Target: Model, M)
	local TR = Target:FindFirstChild(`HumanoidRootPart`)
	if not TR then return endStep(W, Target, 0.6) end
	face(W, TR)
	if not windUp(W, M.Tell or 0.9, true) then return endStep(W, Target, 1.0) end
	play(W, M.Clip, 0.05)
	task.wait(M.LungeAt or 0.33)
	if W.Model.Parent then
		local from = W.Root.CFrame
		local Ahead = rel(W, TR.Position)
		local dist = math.clamp(Ahead - W.Reach - 0.5, 0, M.Lunge or 5)
		local to = from + from.LookVector * dist
		W.Root.Anchored = true
		for k = 1, 5 do W.Root.CFrame = from:Lerp(to, k / 5) task.wait() end
	end
	local caught = W.Model.Parent and not stunned(W) and inReach(W, TR.Position, M.Range)
	if not caught then
		if W.Model.Parent then W.Root.Anchored = false end
		task.wait(0.6)
		return endStep(W, Target, M.Miss or 2.2) -- the opening: it missed and stumbles
	end
	local Hold = M.Hold or 1.0
	local hurtAt = W.Hurt or 0
	local broke = false
	pcall(function() StateManager.CreateState(Target, `Stun`, Hold + 0.4) end)
	pcall(function()
		TR.Anchored = true
		local t0 = os.clock()
		while os.clock() - t0 < Hold and W.Model.Parent and TR.Parent do
			local front = (W.Root.CFrame * CFrame.new(0, 0.3, -(W.Reach + 1.3))).Position
			TR.CFrame = CFrame.lookAt(front, Vector3.new(W.Root.Position.X, front.Y, W.Root.Position.Z))
			if (W.Hurt or 0) > hurtAt then broke = true break end -- a friend's hit breaks the hold
			task.wait()
		end
	end)
	pcall(function() TR.Anchored = false end) -- always let go
	if W.Model.Parent then W.Root.Anchored = false end
	if not broke and W.Model.Parent then
		hurt(W, Target, M.Damage)
		pcall(function() TR.AssemblyLinearVelocity = W.Root.CFrame.LookVector * 28 + Vector3.new(0, 18, 0) end)
	end
	task.wait(0.3)
	endStep(W, Target, if broke then 1.6 else (M.Rest or 1.4))
end

-- the Crypt Bat's shriek, seen: the game's blunt block-hit shockwave, tinted pale violet, pulsing out of its mouth
local function shriekFx(At: CFrame)
	local E = ReplicatedStorage:FindFirstChild(`Assets`) and ReplicatedStorage.Assets:FindFirstChild(`Effects`)
	local Src = E and E:FindFirstChild(`BlockHit`) and E.BlockHit:FindFirstChild(`Blunt`) and E.BlockHit.Blunt:FindFirstChild(`Attachment`)
	if not Src then return end
	local P = Instance.new(`Part`)
	P.Name = `NHBatShriek`
	P.Anchored, P.CanCollide, P.CanQuery, P.CanTouch, P.Transparency = true, false, false, false, 1
	P.Size = Vector3.new(0.2, 0.2, 0.2)
	P.CFrame = At
	local A = Src:Clone()
	A.CFrame = CFrame.identity
	A.Parent = P
	for _, D in A:GetDescendants() do
		if D:IsA(`ParticleEmitter`) then
			D.Enabled = false
			D.Color = ColorSequence.new(Color3.fromRGB(214, 190, 240), Color3.fromRGB(120, 52, 92))
		end
	end
	P.Parent = workspace
	task.spawn(function()
		for _ = 1, 4 do
			for _, D in A:GetDescendants() do
				if D:IsA(`ParticleEmitter`) then D:Emit(D:GetAttribute(`EmitCount`) or 2) end
			end
			task.wait(0.12)
		end
		task.wait(2)
		P:Destroy()
	end)
end

-- Screech (the Crypt Bat): after the Kanji it rears up and shrieks. Anyone in front of it (within Angle of where it
-- faced when the Kanji ended, out to Range) takes Damage and is stunned for Stun seconds. Then it hangs there: the opening
function Moves.Screech(W, Target: Model, M)
	local TR = Target:FindFirstChild(`HumanoidRootPart`)
	if not TR then return endStep(W, Target, 0.6) end
	face(W, TR)
	if not windUp(W, M.Tell or 0.9, true) then return endStep(W, Target, 1.0) end
	local Aim = W.Root.CFrame
	local T = play(W, M.Clip, 0.05)
	task.wait(M.ScreechAt or 0.52)
	if W.Model.Parent and W.Hum.Health > 0 and not stunned(W) then
		local Body = W.Model:FindFirstChild(`Body`)
		local Mouth = (if Body and Body:IsA(`BasePart`) then Body.Position else W.Root.Position) + Aim.LookVector * 1.2
		shriekFx(CFrame.lookAt(Mouth, Mouth + Aim.LookVector))
		local CosA = math.cos(math.rad(M.Angle or 40))
		for _, P in Players:GetPlayers() do
			local C = P.Character
			local R = C and C:FindFirstChild(`HumanoidRootPart`)
			if R then
				local To = R.Position - Mouth
				local Flat = To * Vector3.new(1, 0, 1)
				local InCone = Flat.Magnitude < 1.5 or Aim.LookVector:Dot(Flat.Unit) >= CosA
				if To.Magnitude <= (M.Range or 14) and InCone and math.abs(To.Y) < 9 then
					hurt(W, C, M.Damage or 3)
					pcall(function() StateManager.CreateState(C, `Stun`, M.Stun or 1.0) end)
				end
			end
		end
	end
	task.wait(math.max(0.3, (T and T.Length or 1.35) - (M.ScreechAt or 0.52)))
	if W.Model.Parent then W.Hum:MoveTo(W.Root.Position) play(W, `Idle`, 0.15, true) end
	endStep(W, Target, M.Rest or 1.8)
end

-- the Bone Spider's silk (its thread, the spit, a splat)
local SILK = Color3.fromRGB(228, 224, 212)

-- a patch of silk left on the floor (or a wall) where a spit landed; it fades
local function splat(At: Vector3, Normal: Vector3)
	local P = Instance.new(`Part`)
	P.Name = `NHWebSplat`
	P.Shape = Enum.PartType.Cylinder
	P.Anchored, P.CanCollide, P.CanQuery, P.CanTouch = true, false, false, false
	P.Material = Enum.Material.SmoothPlastic
	P.Color = SILK
	P.Transparency = 0.3
	P.Size = Vector3.new(0.06, 2.6, 2.6)
	-- the disc's axis (X) along the surface normal
	P.CFrame = CFrame.lookAt(At + Normal * 0.04, At + Normal * 2) * CFrame.Angles(0, math.rad(90), 0)
	P.Parent = workspace
	TweenService:Create(P, TweenInfo.new(3, Enum.EasingStyle.Sine, Enum.EasingDirection.In, 0, false, 1.5), { Transparency = 1 }):Play()
	task.delay(4.6, function() P:Destroy() end)
end

-- silk clinging to a student while they're slowed
local function cling(C: Model, Dur: number)
	local R = C:FindFirstChild(`HumanoidRootPart`)
	if not R then return end
	local E = Instance.new(`ParticleEmitter`)
	E.Name = `NHWebCling`
	E.Texture = `rbxassetid://8527116276`
	E.Color = ColorSequence.new(SILK)
	E.LightInfluence = 0.7
	E.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5), NumberSequenceKeypoint.new(1, 1.3) })
	E.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.55), NumberSequenceKeypoint.new(1, 1) })
	E.Lifetime = NumberRange.new(0.5, 0.9)
	E.Rate = 18
	E.Speed = NumberRange.new(0.3, 1)
	E.SpreadAngle = Vector2.new(180, 180)
	E.Rotation = NumberRange.new(-180, 180)
	E.LockedToPart = true
	E.Parent = R
	task.delay(Dur, function() E.Enabled = false task.delay(1, function() E:Destroy() end) end)
end

-- the spit in flight: straight along Dir at Speed, out to Range. It hits the first student it passes within Radius of
-- (a little damage and the Slow state), or splats on whatever it hits
local function glob(W, From: Vector3, Dir: Vector3, M)
	local G = Instance.new(`Part`)
	G.Name = `NHWebGlob`
	G.Shape = Enum.PartType.Ball
	G.Anchored, G.CanCollide, G.CanQuery, G.CanTouch = true, false, false, false
	G.Material = Enum.Material.SmoothPlastic
	G.Color = SILK
	G.Size = Vector3.new(0.9, 0.9, 0.9)
	G.Position = From
	local A0, A1 = Instance.new(`Attachment`), Instance.new(`Attachment`)
	A0.Position, A1.Position = Vector3.new(0, 0.3, 0), Vector3.new(0, -0.3, 0)
	A0.Parent, A1.Parent = G, G
	local T = Instance.new(`Trail`)
	T.Attachment0, T.Attachment1 = A0, A1
	T.Color = ColorSequence.new(SILK)
	T.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(1, 1) })
	T.Lifetime = 0.22
	T.LightInfluence = 0.6
	T.FaceCamera = true
	T.Parent = G
	G.Parent = workspace
	local Rp = RaycastParams.new()
	Rp.FilterType = Enum.RaycastFilterType.Exclude
	Rp.FilterDescendantsInstances = { workspace:FindFirstChild(`Live`), Folder, G }
	local pos, gone = From, 0
	local Range, Speed, Radius = M.Range or 32, M.Speed or 60, M.Radius or 2.6
	while gone < Range do
		local step = math.min(Speed * task.wait(), Range - gone)
		local Ray = workspace:Raycast(pos, Dir * step, Rp)
		local nextPos = if Ray then Ray.Position else pos + Dir * step
		-- any student near this stretch of its path
		local seg = nextPos - pos
		for _, P in Players:GetPlayers() do
			local C = P.Character
			local R = C and C:FindFirstChild(`HumanoidRootPart`)
			if R and seg.Magnitude > 0 then
				local k = math.clamp((R.Position - pos):Dot(seg) / seg:Dot(seg), 0, 1)
				if (R.Position - (pos + seg * k)).Magnitude <= Radius then
					G:Destroy()
					hurt(W, C, M.Damage or 4)
					pcall(function() StateManager.CreateState(C, `Slow`, M.Slow or 2.5) end)
					cling(C, M.Slow or 2.5)
					return
				end
			end
		end
		pos = nextPos
		gone += step
		G.Position = pos
		if Ray then splat(Ray.Position, Ray.Normal) break end
	end
	G:Destroy()
end

-- WebSpit (the Bone Spider): after the Kanji it rears back and spits at where you stood when the Kanji ended (move to
-- dodge it), then stands a moment: the opening
function Moves.Spit(W, Target: Model, M)
	local TR = Target:FindFirstChild(`HumanoidRootPart`)
	if not TR then return endStep(W, Target, 0.6) end
	face(W, TR)
	if not windUp(W, M.Tell or 0.8, true) then return endStep(W, Target, 1.0) end
	local AimAt = TR.Position
	local T = play(W, M.Clip, 0.05)
	task.wait(M.SpitAt or 0.68)
	if W.Model.Parent and not stunned(W) then
		local Head = W.Model:FindFirstChild(`Thorax`)
		local From = (if Head and Head:IsA(`BasePart`) then Head.Position else W.Root.Position) + W.Root.CFrame.LookVector * 1.4
		local Dir = AimAt - From
		if Dir.Magnitude > 0.1 then task.spawn(glob, W, From, Dir.Unit, M) end
	end
	task.wait(math.max(0.3, (T and T.Length or 1.35) - (M.SpitAt or 0.68)))
	if W.Model.Parent then W.Hum:MoveTo(W.Root.Position) play(W, `Idle`, 0.15, true) end
	endStep(W, Target, M.Rest or 1.6)
end

---| ambush (the Grave Ghoul's Emerge) |---

-- dirt churning on the surface while it digs (the game's down-smoke texture, earth coloured)
local function dirt(At: Vector3, Dur: number)
	local P = Instance.new(`Part`)
	P.Name = `NHBeastDirt`
	P.Anchored, P.CanCollide, P.CanQuery, P.CanTouch, P.Transparency = true, false, false, false, 1
	P.Size = Vector3.new(4, 0.2, 4)
	P.Position = At + Vector3.new(0, 0.2, 0)
	local E = Instance.new(`ParticleEmitter`)
	E.Texture = `rbxassetid://8527116276`
	E.Color = ColorSequence.new(Color3.fromRGB(92, 74, 58), Color3.fromRGB(52, 42, 34))
	E.LightInfluence = 0.8
	E.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.8), NumberSequenceKeypoint.new(1, 2.6) })
	E.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.3), NumberSequenceKeypoint.new(1, 1) })
	E.Lifetime = NumberRange.new(0.6, 1.1)
	E.Rate = 26
	E.Speed = NumberRange.new(3, 7)
	E.SpreadAngle = Vector2.new(35, 35)
	E.Acceleration = Vector3.new(0, -14, 0)
	E.Rotation = NumberRange.new(-180, 180)
	E.EmissionDirection = Enum.NormalId.Top
	E.Parent = P
	P.Parent = workspace
	task.delay(Dur, function() E.Enabled = false task.delay(1.2, function() P:Destroy() end) end)
	return P
end

local function showFx(M: Model, On: boolean)
	for _, D in M:GetDescendants() do
		if (D:IsA(`ParticleEmitter`) or D:IsA(`Light`)) and D.Name:match(`^GhoulFX_`) then D.Enabled = On end
	end
end

-- an ambush's hit: anyone within Radius of where it comes up (or down) takes Damage once (Hit remembers who) and is thrown
-- clear at once, out to the edge, so nobody is left inside its body when it lands (an overlap would wedge it in the floor)
local function burst(W, Surface: Vector3, FloorY: number, Hit: { [Model]: boolean })
	local A = W.Def.Ambush
	for _, Pl in Players:GetPlayers() do
		local C = Pl.Character
		local R = C and C:FindFirstChild(`HumanoidRootPart`)
		if R and not Hit[C] and ((R.Position - Surface) * Vector3.new(1, 0, 1)).Magnitude <= (A.Radius or 6) and math.abs(R.Position.Y - FloorY) < 8 then
			Hit[C] = true
			hurt(W, C, A.Damage or 8)
			local Flat = (R.Position - Surface) * Vector3.new(1, 0, 1)
			local Dir = if Flat.Magnitude > 0.2 then Flat.Unit else W.Root.CFrame.LookVector
			pcall(function()
				R.CFrame = R.CFrame + Dir * math.max(0, (A.Radius or 6) + 1 - Flat.Magnitude)
				R.AssemblyLinearVelocity = Dir * 22 + Vector3.new(0, 24, 0)
			end)
		end
	end
end

-- up (or down) and in the fight: solid, on its feet, and after the student who woke it
local function landed(W, Target: Model)
	local A = W.Def.Ambush
	-- every piece with the root before it's solid again
	for _, P in W.Model:GetChildren() do
		if P:IsA(`BasePart`) and P ~= W.Root then pcall(function() P.AssemblyLinearVelocity = Vector3.zero end) end
	end
	task.wait(0.1)
	solid(W.Model, true)
	W.Root.Anchored = false
	pcall(function() W.Hum:ChangeState(Enum.HumanoidStateType.Running) end) -- on its feet the moment it's up
	W.Buried = false
	W.EmergedAt = os.clock()
	W.Target = Target
	W.Step = 1
	W.CircleUntil = os.clock() + (A.Rest or 0.8)
	task.wait(0.9)
	W.Busy = false
end

local hang -- (the Bone Spider's version of burying itself, below)

-- under the ground where it stands (Instant: at spawn, no digging), or digging itself back in
function Shared.Bury(W, Instant: boolean?)
	local A = W.Def.Ambush
	if not (A and W.Model.Parent) then return end
	if A.From == `Above` then return hang(W, Instant) end
	W.Busy = true
	local from = W.Root.CFrame
	-- deep enough that its whole body is under the floor it stands on (whatever that floor is)
	local BoxCF, BoxSize = W.Model:GetBoundingBox()
	local FloorY = (ground(from.Position) or (BoxCF.Position - Vector3.new(0, BoxSize.Y / 2, 0))).Y
	W.Depth = math.max(A.Depth or 6.5, BoxCF.Y + BoxSize.Y / 2 - FloorY + 0.8)
	W.SurfaceY = FloorY
	local to = from - Vector3.new(0, W.Depth, 0)
	W.Root.Anchored = true
	solid(W.Model, false)
	W.Hum:MoveTo(W.Root.Position)
	if not Instant then
		dirt(Vector3.new(from.X, (ground(from.Position) or from.Position).Y, from.Z), 1.2)
		local t0 = os.clock()
		while os.clock() - t0 < 1.0 and W.Model.Parent do
			W.Root.CFrame = from:Lerp(to, (os.clock() - t0) / 1.0)
			task.wait()
		end
	end
	if not W.Model.Parent then return end
	W.Root.CFrame = to
	showFx(W.Model, false)
	W.Buried = true
	W.Busy = false
end

-- a student came near: the ground churns, the Kanji shows, then it bursts up (hitting anyone right on top of it)
local function emerge(W, Target: Model)
	local A = W.Def.Ambush
	local TR = Target:FindFirstChild(`HumanoidRootPart`)
	local under = W.Root.CFrame
	local Depth = W.Depth or A.Depth or 6.5
	local surface = under.Position + Vector3.new(0, Depth, 0)
	local floorY = W.SurfaceY or (ground(surface) or surface).Y
	if TR then
		local d = (TR.Position - surface) * Vector3.new(1, 0, 1)
		if d.Magnitude > 0.1 then under = CFrame.lookAt(under.Position, under.Position + d.Unit) W.Root.CFrame = under end
	end
	dirt(Vector3.new(surface.X, floorY, surface.Z), (A.Tell or 1) + (A.Rise or 0.6))
	local P = packets()
	if P then pcall(function() P.Replicate:Fire(`Indicators`, `BeastTell`, { User = W.Model; At = Vector3.new(surface.X, floorY + 3.5, surface.Z) }) end) end
	task.wait(A.Tell or 1)
	if not W.Model.Parent then return end
	showFx(W.Model, true)
	play(W, A.Clip, 0.05)
	local top = under + Vector3.new(0, Depth, 0)
	local t0 = os.clock()
	local hit = {}
	while os.clock() - t0 < (A.Rise or 0.6) and W.Model.Parent do
		local t = (os.clock() - t0) / (A.Rise or 0.6)
		W.Root.CFrame = under:Lerp(top, 1 - (1 - t) ^ 2)
		if t > 0.4 then burst(W, surface, floorY, hit) end
		task.wait()
	end
	if not W.Model.Parent then return end
	W.Root.CFrame = top
	landed(W, Target)
end

---| hanging (the Bone Spider): it waits on a silk thread over its lair and drops on whoever walks under it |---

-- its thread: from its rear (pointing up while it hangs head down) to the ceiling over it, or up into the dark
local function thread(W, TopY: number)
	local old = W.Model:FindFirstChild(`SpiderThread`)
	if old then old:Destroy() end
	local A0 = W.Root:FindFirstChild(`SpiderSilk`) or Instance.new(`Attachment`)
	A0.Name = `SpiderSilk`
	A0.Position = Vector3.new(0, 0, W.Root.Size.Z / 2)
	A0.Parent = W.Root
	local P = Instance.new(`Part`)
	P.Name = `SpiderThread`
	P.Anchored, P.CanCollide, P.CanQuery, P.CanTouch, P.Transparency = true, false, false, false, 1
	P.Size = Vector3.new(0.2, 0.2, 0.2)
	P.Position = Vector3.new(W.Root.Position.X, TopY, W.Root.Position.Z)
	local A1 = Instance.new(`Attachment`)
	A1.Parent = P
	local B = Instance.new(`Beam`)
	B.Attachment0, B.Attachment1 = A0, A1
	B.Width0, B.Width1 = 0.07, 0.05
	B.Color = ColorSequence.new(SILK)
	B.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.15), NumberSequenceKeypoint.new(0.75, 0.35), NumberSequenceKeypoint.new(1, 1) })
	B.LightEmission = 0.25
	B.LightInfluence = 0.6
	B.FaceCamera = true
	B.Segments = 1
	B.Parent = P
	P.Parent = W.Model
end

-- how high it hangs: Height over the floor, or a little under a ceiling / branch that's lower; and where its thread ends
local function hangSpot(W): (Vector3, number, number)
	local A = W.Def.Ambush
	local Floor = ground(W.Root.Position) or (W.Root.Position - Vector3.new(0, W.Root.Size.Y / 2 + W.Hum.HipHeight, 0))
	local H = A.Height or 13
	local Rp = RaycastParams.new()
	Rp.FilterType = Enum.RaycastFilterType.Exclude
	Rp.FilterDescendantsInstances = { workspace:FindFirstChild(`Live`), Folder }
	local Up = workspace:Raycast(Floor + Vector3.new(0, 1, 0), Vector3.new(0, H + 6, 0), Rp)
	if Up then H = math.clamp(Up.Position.Y - Floor.Y - 4, 5, H) end
	return Floor, H, if Up then Up.Position.Y else Floor.Y + H + 14
end

-- up its thread (Instant: at spawn)
hang = function(W, Instant: boolean?)
	W.Busy = true
	local Floor, H, TopY = hangSpot(W)
	W.SurfaceY = Floor.Y
	local from = W.Root.CFrame
	local standY = Floor.Y + W.Root.Size.Y / 2 + W.Hum.HipHeight
	-- head down, hanging H studs over the floor
	local up = CFrame.new(Floor.X, standY + H, Floor.Z) * (from - from.Position) * CFrame.Angles(-math.pi / 2, 0, 0)
	W.Depth = -(up.Y - from.Y) -- (signed: the brain looks Depth below its root for the floor it guards)
	W.Root.Anchored = true
	solid(W.Model, false)
	W.Hum:MoveTo(W.Root.Position)
	thread(W, TopY)
	play(W, `Hang`, 0.3, true)
	if not Instant then
		local t0 = os.clock()
		while os.clock() - t0 < 1.6 and W.Model.Parent do
			local t = (os.clock() - t0) / 1.6
			W.Root.CFrame = from:Lerp(up, t * t * (3 - 2 * t))
			task.wait()
		end
	end
	if not W.Model.Parent then return end
	W.Root.CFrame = up
	W.Buried = true
	W.Busy = false
end

-- a student walked under it: its thread trembles and the Kanji shows on the floor below, then it drops, turning to land on
-- its feet facing them, and hits anyone right under it
local function drop(W, Target: Model)
	local A = W.Def.Ambush
	local TR = Target:FindFirstChild(`HumanoidRootPart`)
	local hung = W.Root.CFrame
	local floorY = W.SurfaceY or (ground(hung.Position) or hung.Position).Y
	local standY = floorY + W.Root.Size.Y / 2 + W.Hum.HipHeight
	local landAt = Vector3.new(hung.X, standY, hung.Z)
	local surface = Vector3.new(hung.X, floorY, hung.Z)
	local Dir = if TR then (TR.Position - landAt) * Vector3.new(1, 0, 1) else Vector3.zero
	local land = if Dir.Magnitude > 0.1 then CFrame.lookAt(landAt, landAt + Dir.Unit) else CFrame.new(landAt) * (hung - hung.Position) * CFrame.Angles(math.pi / 2, 0, 0)
	local P = packets()
	if P then pcall(function() P.Replicate:Fire(`Indicators`, `BeastTell`, { User = W.Model; At = surface + Vector3.new(0, 3.5, 0) }) end) end
	local t0 = os.clock()
	while os.clock() - t0 < (A.Tell or 0.8) and W.Model.Parent do
		W.Root.CFrame = hung * CFrame.new(math.sin(os.clock() * 45) * 0.07, 0, 0)
		task.wait()
	end
	if not W.Model.Parent then return end
	play(W, A.Clip, 0.05)
	local Rise = A.Rise or 0.45
	local hit = {}
	t0 = os.clock()
	while os.clock() - t0 < Rise and W.Model.Parent do
		local t = (os.clock() - t0) / Rise
		W.Root.CFrame = hung:Lerp(land, t * t) -- falling, faster and faster
		if t > 0.7 then burst(W, surface, floorY, hit) end
		task.wait()
	end
	if not W.Model.Parent then return end
	W.Root.CFrame = land
	burst(W, surface, floorY, hit)
	dirt(surface, 0.25) -- a puff of dust as it lands
	task.delay(0.35, function()
		local Th = W.Model:FindFirstChild(`SpiderThread`)
		if Th then Th:Destroy() end -- the thread snaps
	end)
	landed(W, Target)
end

---| freeze (the Night Stalker): it can't move while a student is looking at it |---

-- where each student is looking (ReplicatedStorage.NHBeastGaze, from Controllers.World.BeastGaze)
local Gaze = {} :: { [Player]: { Pos: Vector3, Look: Vector3, T: number } }

local function watched(W): boolean
	local F = W.Def.Freeze
	local Head = W.Model:FindFirstChild(`Head`)
	local At = if Head and Head:IsA(`BasePart`) then Head.Position else W.Root.Position
	local CosA = math.cos(math.rad(F.Angle or 35))
	for P, G in Gaze do
		local C = P.Character
		local R = C and C:FindFirstChild(`HumanoidRootPart`)
		local H = C and C:FindFirstChildWhichIsA(`Humanoid`)
		if R and H and H.Health > 0 and os.clock() - G.T < 0.6 and (R.Position - W.Root.Position).Magnitude <= (F.Range or 70) then
			-- the camera can't be far from its character (no freezing it from across the map with a spoofed camera)
			if (G.Pos - R.Position).Magnitude < 40 then
				local To = At - G.Pos
				if To.Magnitude > 0.1 and G.Look:Dot(To.Unit) >= CosA then
					local Rp = RaycastParams.new()
					Rp.FilterType = Enum.RaycastFilterType.Exclude
					Rp.FilterDescendantsInstances = { workspace:FindFirstChild(`Live`), Folder, C }
					local Hit = workspace:Raycast(G.Pos, To, Rp)
					if not Hit then return true end -- a clear line of sight
				end
			end
		end
	end
	return false
end

local function setFrozen(W, On: boolean)
	if W.Frozen == On then return end
	W.Frozen = On
	for _, T in W.Tracks do if T.IsPlaying then T:AdjustSpeed(if On then 0 else 1) end end
	if On then
		W.Hum.WalkSpeed = 0
		W.Hum:MoveTo(W.Root.Position)
	else
		W.Hum.WalkSpeed = W.Def.WalkSpeed
	end
end

---| spawning |---

local function count(Name: string): number
	local N = Pending[Name] or 0
	for _, W in Live do if W.Name == Name then N += 1 end end
	return N
end

function Shared.SpawnAt(Name: string, At: CFrame): Model?
	local Def = Config.Defs[Name]
	local Lib = ServerStorage:FindFirstChild(`NHBeasts`)
	local Src = Def and Lib and Lib:FindFirstChild(Def.Model)
	if not (Src and Folder) then return nil end
	-- outside Studio a beast needs its published clips: one still waiting on the owner's upload stays out of live servers
	if not RunService:IsStudio() then
		local Anims = Src:FindFirstChild(`Animations`)
		for _, A in (Anims and Anims:GetChildren()) or {} do
			if A:IsA(`Animation`) and A.AnimationId == `` then return nil end
		end
	end
	local Floor = ground(At.Position) or At.Position
	local M = Src:Clone()
	M.Name = Def.Name
	local Hum = M:FindFirstChildWhichIsA(`Humanoid`)
	local Root = M:FindFirstChild(`HumanoidRootPart`) :: BasePart
	if not (Hum and Root) then M:Destroy() return nil end
	Hum.MaxHealth, Hum.Health = Def.Health, Def.Health
	Hum.WalkSpeed = Def.WalkSpeed
	Hum.BreakJointsOnDeath = false
	Hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	-- a beast never tips over or ragdolls (an ambusher buried in the ground would collapse and could fall through the floor)
	for _, S in { Enum.HumanoidStateType.FallingDown, Enum.HumanoidStateType.Ragdoll } do Hum:SetStateEnabled(S, false) end
	Hum.RequiresNeck = false -- an R15 beast's neck may be an AnimationConstraint, not a Motor6D
	local Rot = At - At.Position
	-- place the root itself (a model's pivot isn't always its root part)
	local RootAt = CFrame.new(Floor + Vector3.new(0, Root.Size.Y / 2 + Hum.HipHeight, 0)) * Rot
	M:PivotTo(RootAt * (Root.CFrame:Inverse() * M:GetPivot()))
	M:SetAttribute(`NHBeast`, Name)
	M:SetAttribute(`NoDowned`, true) -- beasts die, they don't get downed and gripped
	if Def.Freeze then M:SetAttribute(`NHFreezeOnGaze`, true) end -- (clients near it report where they're looking)
	M.Parent = Folder
	local Animator = Hum:FindFirstChildOfClass(`Animator`) or Instance.new(`Animator`, Hum)
	local W = { Name = Name; Def = Def; Model = M; Hum = Hum; Root = Root; Tracks = {}; Home = Floor; Step = 1; Busy = false;
		Snout = M:FindFirstChild(`snout`, true) }
	-- how far its mouth is ahead of its middle, and how wide its head is (for every reach check)
	W.Reach = if W.Snout then math.max(1, -Root.CFrame:PointToObjectSpace(W.Snout.WorldPosition).Z) else Root.Size.Z / 2 + 1
	W.Width = Root.Size.X / 2 + 1
	local Anims = M:FindFirstChild(`Animations`)
	-- a clip the owner hasn't published yet (no AnimationId) plays from its KeyframeSequence in Studio
	-- (ServerStorage.NHBeasts.Clips.<Model>.<clip>), so a new beast can be tested before its clips are uploaded
	local ClipSet = Lib:FindFirstChild(`Clips`) and Lib.Clips:FindFirstChild(Def.Model)
	for _, A in (Anims and Anims:GetChildren()) or {} do
		if A:IsA(`Animation`) and A.AnimationId == `` and ClipSet and ClipSet:FindFirstChild(A.Name) and RunService:IsStudio() then
			pcall(function() A.AnimationId = KeyframeSequenceProvider:RegisterKeyframeSequence(ClipSet[A.Name]) end)
		end
		if A:IsA(`Animation`) and A.AnimationId ~= `` then
			local Ok, T = pcall(function() return Animator:LoadAnimation(A) end)
			if Ok then
				T.Looped = A.Name == `Idle` or A.Name == `Walk` or A.Name == `Run` or A.Name == `Hang`
				T.Priority = if T.Looped then Enum.AnimationPriority.Movement else Enum.AnimationPriority.Action
				W.Tracks[A.Name] = T
			end
		end
	end
	pcall(function() Root:SetNetworkOwner(nil) end)
	play(W, `Idle`, 0, true)
	Live[M] = W
	if Def.Ambush then Shared.Bury(W, true) end -- an ambusher starts underground
	Hum.HealthChanged:Connect(function(H)
		if H < (W.LastHealth or Def.Health) then
			W.Hurt = os.clock()
			if not W.Target then W.Target = nearestStudent(Root.Position, Def.Sight * 1.5) end -- hit it and it comes for you
		end
		W.LastHealth = H
	end)
	Hum.Died:Connect(function()
		Live[M] = nil
		if W.Target then release(W.Target, W) end
		local FXm = ReplicatedStorage:FindFirstChild(`Beasts`) and ReplicatedStorage.Beasts:FindFirstChild(`HellhoundFX`)
		if FXm then pcall(function() require(FXm).Breath(M, false) end) end
		for N, T in W.Tracks do if N ~= `Death` and T.IsPlaying then T:Stop(0.1) end end
		-- a dead Humanoid stops holding its HipHeight (a hovering bat would drop with its clip on top, into the floor):
		-- pin the root where it stands so the Death clip does all the falling
		if not W.Buried then
			pcall(function()
				solid(M, false) -- the body no longer blocks (and can't shove anyone as it's pinned)
				local Floor = ground(Root.Position)
				local Y = if Floor then Floor.Y + Root.Size.Y / 2 + Hum.HipHeight else Root.Position.Y
				Root.Anchored = true
				Root.CFrame = (Root.CFrame - Root.Position) + Vector3.new(Root.Position.X, Y, Root.Position.Z)
			end)
		end
		local DT = play(W, `Death`, 0.1)
		-- it stays down: the clip holds its last frame until the body fades (else it'd snap back up when the clip ends)
		if DT then
			task.spawn(function()
				local w = 0
				while DT.Length == 0 and w < 2 do w += task.wait() end
				task.wait(math.max(0, DT.Length - 0.08))
				if DT.IsPlaying then DT:AdjustSpeed(0) end
			end)
		end
		local Killer = nil
		pcall(function() Killer = require(ServerScriptService.Services.Features.Downed).GetKiller(M) end)
		local P = Killer and Players:GetPlayerFromCharacter(Killer)
		P = P or (W.Target and Players:GetPlayerFromCharacter(W.Target))
		if P then Shared.Reward(P, Def) end
		task.delay(4, function()
			for _, D in M:GetDescendants() do
				if D:IsA(`BasePart`) then TweenService:Create(D, TweenInfo.new(1.5), { Transparency = 1 }):Play()
				elseif D:IsA(`ParticleEmitter`) then D.Enabled = false
				elseif D:IsA(`Light`) then TweenService:Create(D, TweenInfo.new(1.5), { Brightness = 0 }):Play() end
			end
			task.delay(1.6, function() M:Destroy() end)
		end)
		Pending[Name] = (Pending[Name] or 0) + 1
		task.delay(Def.Spawn.Respawn, function()
			Pending[Name] = math.max(0, (Pending[Name] or 0) - 1)
			if isNight() then Shared.Fill() end
		end)
	end)
	return M
end

-- the killer's pay: Combat EXP, Yen, and a rare trophy into the Locker
function Shared.Reward(P: Player, Def)
	local R = Def.Reward or {}
	pcall(function() require(ServerScriptService.Services.Player.Progression).Award(P, R.Exp or 0, `Combat`, Def.Name) end)
	pcall(function() require(ServerScriptService.Services.Player.Data).UpdateState(P, { type = `UpdateYen`; amount = R.Yen or 0 }) end)
	local Tr = R.Trophy
	if Tr and math.random() < (Tr.Chance or 0) then
		pcall(function()
			local Items = require(ReplicatedStorage.Config.Items)
			local It = Items.ById[Tr.Id]
			if not It then return end
			if require(ServerScriptService.Services.Features.Inventory).Grant(P, Tr.Id, 1) > 0 then
				require(ServerScriptService.Services.Features.Notifications).Notify(P, {
					Title = `Trophy: {It.Name}`; Text = `From the {Def.Name}. It's in your Locker.`; Kind = `Good`; Duration = 5 })
			end
		end)
	end
end

function Shared.Fill()
	if not isNight() then return end
	for Name, Def in Config.Defs do
		local Spots = lairs(Def)
		if #Spots > 0 then
			local N = count(Name)
			while N < Def.Spawn.Max do
				local At = Spots[math.random(#Spots)] + Vector3.new(math.random(-6, 6), 0, math.random(-6, 6))
				Shared.SpawnAt(Name, CFrame.new(At) * CFrame.Angles(0, math.random() * math.pi * 2, 0))
				N += 1
			end
		end
	end
end

function Shared.Clear(): number
	local n = 0
	for M in Live do Live[M] = nil M:Destroy() n += 1 end
	return n
end

function Shared.Count(): number
	local n = 0
	for _ in Live do n += 1 end
	return n
end

---| the brain |---

local function circle(W, TR: BasePart, Radius: number)
	W.Orbit = (W.Orbit or math.random() * math.pi * 2) + 0.3 * (W.OrbitDir or 1)
	if math.random() < 0.02 then W.OrbitDir = -(W.OrbitDir or 1) end
	local pos = TR.Position + Vector3.new(math.cos(W.Orbit), 0, math.sin(W.Orbit)) * Radius
	W.Hum.WalkSpeed = W.Def.WalkSpeed + 4
	W.Hum:MoveTo(pos)
	play(W, `Walk`, 0.2, true)
end

local function think(W)
	local M, Hum, Root, Def = W.Model, W.Hum, W.Root, W.Def
	if not (M.Parent and Root and Hum.Health > 0) or W.Busy then return end
	-- fell off the world somehow: back to its lair
	if not W.Buried and Root.Position.Y < W.Home.Y - 40 then
		Root.AssemblyLinearVelocity = Vector3.zero
		local Upright = CFrame.new(W.Home + Vector3.new(0, Root.Size.Y / 2 + Hum.HipHeight, 0)) * (Root.CFrame - Root.Position)
		M:PivotTo(Upright * (Root.CFrame:Inverse() * M:GetPivot()))
		if W.Target then release(W.Target, W) W.Target = nil end
		return
	end
	-- an ambusher underground waits for a student to come near its grave
	if W.Buried then
		local surface = Root.Position + Vector3.new(0, W.Depth or Def.Ambush.Depth or 6.5, 0)
		local S = nearestStudent(surface, Def.Ambush.Range or 16)
		if S then W.Busy = true task.spawn(if Def.Ambush.From == `Above` then drop else emerge, W, S) end
		return
	end
	-- a Freeze beast stands stock still while anyone is looking at it (an attack already under way still lands)
	if Def.Freeze then
		if watched(W) then setFrozen(W, true) return end
		setFrozen(W, false)
	end
	if stunned(W) and W.Target then release(W.Target, W) end
	if StateManager.HasState(M, `Paralyzed`) then
		if not W.Staggered then W.Staggered = true play(W, `GuardBroken`, 0.05) end
		Hum:MoveTo(Root.Position)
		return
	end
	if stunned(W) then
		if not W.Staggered then W.Staggered = true play(W, if math.random() < 0.5 then `Stun1` else `Stun2`, 0.05) end
		Hum:MoveTo(Root.Position)
		return
	end
	-- coming out of a stun: the StunGuard starts
	if W.Staggered then W.GuardUntil = os.clock() + (Def.StunGuard or 0) end
	W.Staggered = false
	local T = W.Target
	local TR = T and T.Parent and T:FindFirstChild(`HumanoidRootPart`)
	local TH = T and T:FindFirstChildWhichIsA(`Humanoid`)
	-- lost them: dead, downed, gone, or led too far from home (you can get away)
	if not (TR and TH and TH.Health > 0) or TH:GetAttribute(`Downed`) or (TR.Position - W.Home).Magnitude > Def.Leash then
		if T then release(T, W) end
		W.Target, T, TR = nil, nil, nil
		local Seen = nearestStudent(Root.Position, Def.Sight)
		if Seen and (Seen.HumanoidRootPart.Position - W.Home).Magnitude <= Def.Leash then
			W.Target, T = Seen, Seen
			TR = Seen:FindFirstChild(`HumanoidRootPart`)
			W.Step = 1
			W.CircleUntil = os.clock() + 1.5 -- it sizes you up first
			if Def.Sighted and not W.Sighted and W.Tracks[Def.Sighted] then
				W.Sighted = true
				W.Busy = true
				Hum:MoveTo(Root.Position)
				face(W, TR)
				local Tr = play(W, Def.Sighted, 0.1)
				task.delay(math.min(2.2, Tr and Tr.Length or 1.6), function()
					if Tr and Tr.IsPlaying then Tr:Stop(0.25) end -- (the howl clip runs long; it doesn't carry into the first bite)
					W.Busy = false
				end)
				return
			end
		end
	end
	if not TR then
		-- an ambusher walks back to its grave and digs itself in again
		if Def.Ambush then
			Hum.WalkSpeed = Def.WalkSpeed
			local Flat = ((W.Home - Root.Position) * Vector3.new(1, 0, 1)).Magnitude
			if Flat < 3 and os.clock() - (W.EmergedAt or 0) > (Def.Ambush.Reburrow or 12) then
				task.spawn(Shared.Bury, W)
				return
			end
			Hum:MoveTo(W.Home)
			play(W, if Flat > 2 then `Walk` else `Idle`, 0.2, true)
			return
		end
		-- roam near home (and walk back if a chase dragged it away)
		Hum.WalkSpeed = Def.WalkSpeed
		local Far = (Root.Position - W.Home).Magnitude > Def.Roam * 1.5
		if Far or not W.WanderTo or (Root.Position - W.WanderTo).Magnitude < 3 or os.clock() > (W.WanderUntil or 0) then
			W.WanderTo = if Far then W.Home else W.Home + Vector3.new(math.random(-Def.Roam, Def.Roam), 0, math.random(-Def.Roam, Def.Roam))
			W.WanderUntil = os.clock() + 7
			if not Far and math.random() < 0.35 then W.WanderTo = Root.Position end
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
	claim(T, W)
	local Name = Def.Pattern[W.Step]
	local Mv = Def.Moves[Name]
	if not Mv then endStep(W, T, 0.5) return end
	local Go = Moves[Mv.Kind]
	if Mv.Kind == `Melee` or Mv.Kind == `Breath` or Mv.Kind == `Grab` or Mv.Kind == `Spit` or Mv.Kind == `Screech` then
		local Reach = if Mv.Kind == `Melee` then Mv.Range elseif Mv.Kind == `Grab` then Mv.Range + (Mv.Lunge or 0) * 0.7
			elseif Mv.Kind == `Spit` then Mv.Range * 0.45 else Mv.Range * 0.6
		-- the gap between its mouth and you (0 when you're already inside its reach)
		local Flat = ((TR.Position - Root.Position) * Vector3.new(1, 0, 1)).Magnitude
		local Gap = math.max(0, Flat - W.Reach)
		W.ApproachSince = W.ApproachSince or os.clock()
		if Gap <= Reach * 0.8 or (os.clock() - W.ApproachSince > 2.5 and Gap <= Reach + 6) then
			W.ApproachSince = nil
			W.Busy = true
			task.spawn(Go, W, T, Mv)
			return
		end
		if os.clock() - W.ApproachSince > 5 then W.ApproachSince = nil endStep(W, T, 1.2) return end -- give the turn away
		Hum.WalkSpeed = Def.RunSpeed
		Hum:MoveTo(TR.Position - (TR.Position - Root.Position).Unit * (W.Reach + 1)) -- it stops with its jaws at you, not on top of you
		play(W, `Run`, 0.15, true)
	elseif Mv.Kind == `Hop` then
		W.Busy = true
		task.spawn(Go, W, T, Mv)
	elseif Mv.Kind == `Leap` then
		if Dist >= Mv.Min and Dist <= Mv.Max then W.Busy = true task.spawn(Go, W, T, Mv) return end
		Hum.WalkSpeed = Def.RunSpeed - 4
		local away = (Root.Position - TR.Position) * Vector3.new(1, 0, 1)
		local want = TR.Position + (if away.Magnitude > 0.1 then away.Unit else Vector3.xAxis) * ((Mv.Min + Mv.Max) / 2)
		Hum:MoveTo(want)
		play(W, `Run`, 0.15, true)
	else
		endStep(W, T, 0.5)
	end
end

function Shared.OnStart()
	Folder = Instance.new(`Folder`)
	Folder.Name = `NHBeasts`
	Folder.Parent = workspace:FindFirstChild(`Live`) or workspace -- in Live so combat hitboxes and lock-on see them
	-- where students are looking, for Freeze beasts (rate-limited; only the latest counts)
	local GazeRemote = Instance.new(`RemoteEvent`)
	GazeRemote.Name = `NHBeastGaze`
	GazeRemote.Parent = ReplicatedStorage
	GazeRemote.OnServerEvent:Connect(function(P: Player, Pos: any, Look: any)
		if typeof(Pos) ~= `Vector3` or typeof(Look) ~= `Vector3` or Look.Magnitude < 0.5 or Look.Magnitude > 1.5 then return end
		if Pos.X ~= Pos.X or Look.X ~= Look.X then return end -- NaN
		local Last = Gaze[P]
		if Last and os.clock() - Last.T < 0.1 then return end
		Gaze[P] = { Pos = Pos; Look = Look.Unit; T = os.clock() }
	end)
	Players.PlayerRemoving:Connect(function(P) Gaze[P] = nil end)
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
				for M, W in Live do
					-- they melt away by morning (not one mid-fight, and not an admin's daytime test spawn)
					if not W.Target and not M:GetAttribute(`NHAdminSpawn`) then Live[M] = nil M:Destroy() end
				end
			end
			task.wait(10)
		end
	end)
end

return Shared
