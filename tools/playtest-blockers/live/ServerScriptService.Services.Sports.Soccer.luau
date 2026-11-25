--[[
	Soccer rules (server): the Matches plug-in for SportVenue = "Soccer" (the Pitch), plus Target Practice and Wall Passes.
	The server owns the ball and every outcome. Shot power comes from the hold measured on the server (KickStart -> KickRelease).
	The client only sends an aim direction, which is normalised and clamped here.

	Client actions (NHSports.Action):
		KickStart / KickRelease {Aim, Curve = -1|0|1}   click hold/release: shot (or a keeper's throw in their box);
		                                                 without the ball, a release opens a short volley/header window
		Pass {Aim}   R with the ball (to the teammate you aim at, else into space) · Call   R without it
		Dribble {Dir}   Q with the ball: a burst; a tackle that lands in it breaks the tackler's ankles
		Feint   right click with the ball: counters a tackle
		Tackle {Dir}   E without the ball: a lunge with a steal window; a miss stuns you
		Dive {Dir}   Q as the keeper in your box: a dive that catches with a long reach
		Bloodrush   T: spend your meter for a race-tinted burst (speed, power, stamina)
	Rules: the ball stays in play (ball-only walls), first to 10 or a 5-goal lead, two halves, golden-goal overtime.
	After a goal there's a short celebration, then the team that conceded kicks off from the centre.
	Fx (NHSports.Fx, prefixed S_): S_Charge, S_Kick, S_Pass, S_Dribble, S_Feint, S_Tackle, S_Stolen, S_Ankles, S_Stun,
	S_Dive, S_Throw, S_Pickup, S_Goal, S_Bloodrush, S_Call, S_Target.
]]

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local PhysicsService = game:GetService(`PhysicsService`)

local Config = require(ReplicatedStorage.Config.Sports)
local Ball = require(script.Parent.Ball)
local function clubs() return require(script.Parent.Clubs) end   -- lazy: Clubs pulls in the save system
local T = Config.Soccer

local Rules = {}
local Local = {}

local function try(Path: { string })
	local M = ServerScriptService
	for _, N in Path do M = M and M:FindFirstChild(N) end
	if not M then return nil end
	local Ok, Mod = pcall(require, M)
	return if Ok then Mod else nil
end
local function root(P: Player): BasePart? return P.Character and P.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart? end
local function flat(V: Vector3): Vector3 return Vector3.new(V.X, 0, V.Z) end
local function fx(Kind: string, Data: any)
	local F = ReplicatedStorage:FindFirstChild(`NHSports`) and ReplicatedStorage.NHSports:FindFirstChild(`Fx`)
	if F then F:FireAllClients(Kind, Data) end
end
-- did the ball's path from A to B pass through the box? (a fast ball crosses a sensor between 10 Hz checks)
local function finite(V: Vector3): boolean return V == V and V.Magnitude < math.huge end

-- a flat unit vector, or the fallback when there's no horizontal part (never NaN)
local function flatUnit(V: Vector3, Fallback: Vector3?): Vector3
	local F = Vector3.new(V.X, 0, V.Z)
	if F == F and F.Magnitude > 1e-3 and F.Magnitude < math.huge then return F.Unit end
	return Fallback or Vector3.new(0, 0, -1)
end

local function sweptBox(Part: BasePart, A: Vector3, B: Vector3, Margin: number?): boolean
	if not (finite(A) and finite(B)) then return false end   -- NaN would slip through every slab test
	local M = Margin or 0
	local H = Part.Size / 2 + Vector3.one * M
	local La, Lb = Part.CFrame:PointToObjectSpace(A), Part.CFrame:PointToObjectSpace(B)
	local D = Lb - La
	local T0, T1 = 0, 1
	for _, Ax in { `X`, `Y`, `Z` } do
		local a, d, h = La[Ax], D[Ax], H[Ax]
		if math.abs(d) < 1e-6 then
			if math.abs(a) > h then return false end
		else
			local u, v = (-h - a) / d, (h - a) / d
			if u > v then u, v = v, u end
			T0, T1 = math.max(T0, u), math.min(T1, v)
			if T0 > T1 then return false end
		end
	end
	return true
end

function Local.FxTo(P: Player, Kind: string, Data: any)
	local F = ReplicatedStorage:FindFirstChild(`NHSports`) and ReplicatedStorage.NHSports:FindFirstChild(`Fx`)
	if F then F:FireClient(P, Kind, Data) end
end

local function inBox(Part: BasePart, Pos: Vector3, Margin: number?): boolean
	if not finite(Pos) then return false end
	local L = Part.CFrame:PointToObjectSpace(Pos)
	local M = Margin or 0
	return math.abs(L.X) <= Part.Size.X / 2 + M and math.abs(L.Y) <= Part.Size.Y / 2 + M and math.abs(L.Z) <= Part.Size.Z / 2 + M
end

-- a client vector: finite, non-zero, unit length (nil if junk)
function Rules.CleanDir(V: any): Vector3?
	if typeof(V) ~= `Vector3` or V ~= V then return nil end
	local M = V.Magnitude
	if M ~= M or M < 1e-3 or M == math.huge then return nil end
	return V / M
end

-- pure: shot power from the server-measured hold
function Rules.Power(Held: number): number
	return math.clamp(Held / T.Kick.ChargeTime, T.Kick.MinPower, 1)
end

-- pure: the launch velocity for an aim (unit) and power
function Rules.ShotVelocity(Aim: Vector3, Power: number, Bonus: number?): Vector3
	local K = T.Kick
	local Y = math.clamp(Aim.Y, K.AimYMin, K.AimYMax)
	local Flat = flat(Aim)
	Flat = if Flat.Magnitude > 1e-3 then Flat.Unit * math.sqrt(1 - Y * Y) else Vector3.new(0, 0, -1)
	local Dir = Flat + Vector3.new(0, Y, 0)
	local V = Dir * K.Speed * Power * (1 + (Bonus or 0))
	local Up = math.min(V.Y + K.Lift * (0.9 - math.abs(Y)) * Power, K.MaxUp)
	return Vector3.new(V.X, Up, V.Z)
end

---| setup |---

function Rules.Setup(m)
	local V = m.Venue
	local S = { Goals = {}; Zones = {} }
	for _, D in V:GetDescendants() do
		if D:IsA(`BasePart`) then
			if D:GetAttribute(`SportGoal`) then S.Goals[D:GetAttribute(`SportGoal`)] = D end
			if D:GetAttribute(`SportKeeperZone`) then S.Zones[D:GetAttribute(`SportKeeperZone`)] = D end
		end
	end
	assert(S.Goals.A and S.Goals.B, `pitch needs both goal mouths`)
	m.S = S
	-- ball-only walls need the two collision groups (built in Edit; registered again here to be safe)
	pcall(function()
		for _, G in { `SportBall`, `SportBallWall` } do
			if not PhysicsService:IsCollisionGroupRegistered(G) then PhysicsService:RegisterCollisionGroup(G) end
		end
	end)
	Local.BallOnlyWalls()
end

-- (playtest-blockers) The pitch's invisible ball walls and ceiling (group SportBallWall) stop the ball and nothing else.
-- Only Default was switched off before, but characters run in the Entity group (Services.Server; NPC, Ragdoll,
-- NHWalkers and TutorialPlayers too), and a new group collides with everything, so nobody could walk onto the pitch
-- or the practice field. Every group but SportBall is switched off, at start and again every 10 s (groups that are
-- registered later start out colliding).
local Sweeping = false
function Local.BallOnlyWalls()
	if not Sweeping then
		Sweeping = true
		task.spawn(function()
			while true do
				task.wait(10)
				Local.BallOnlyWalls()
			end
		end)
	end
	pcall(function()
		for _, G in { `SportBall`, `SportBallWall` } do
			if not PhysicsService:IsCollisionGroupRegistered(G) then PhysicsService:RegisterCollisionGroup(G) end
		end
		for _, G in PhysicsService:GetRegisteredCollisionGroups() do
			if G.name ~= `SportBallWall` and PhysicsService:CollisionGroupsAreCollidable(`SportBallWall`, G.name) ~= (G.name == `SportBall`) then
				PhysicsService:CollisionGroupSetCollidable(`SportBallWall`, G.name, G.name == `SportBall`)
			end
		end
	end)
end

function Local.Fresh(m)
	local S = m.S
	S.Stamina, S.Charge, S.KickAt, S.PassAt, S.TackleAt, S.DribbleAt, S.FeintAt, S.DiveAt = {}, {}, {}, {}, {}, {}, {}, {}
	S.Window, S.Tackling, S.Dribbling, S.Feinting, S.Diving, S.Dodge = {}, {}, {}, {}, {}, {}
	S.Meter, S.Rush, S.Keeper = {}, {}, {}
	S.LastPos, S.Suspect, S.JumpTo = {}, {}, {}
	S.LastKicker, S.LastPass, S.HeldSince = nil, nil, nil
	S.PauseUntil = 0
end

function Local.Defends(Team: string): string return Team end            -- zone attribute = the defending team
function Local.TheirGoal(m, Team: string): BasePart return m.S.Goals[Team] end   -- SportGoal = the team that scores there

function Local.InZone(m, P: Player): boolean
	local Team = m.Team[P]
	local Z = Team and m.S.Zones[Team]
	local R = root(P)
	return Z ~= nil and R ~= nil and inBox(Z, R.Position, 0)
end

function Local.IsKeeper(m, P: Player): boolean return m.S.Keeper[m.Team[P] or ``] == P end

function Local.SetKeys(P: Player, On: boolean)
	local C = P.Character
	if C then C:SetAttribute(`SportKeys`, if On then true else nil) end
end

---| ball |---

function Local.NewBall(m)
	local S = m.S
	if S.Ball then S.Ball:Destroy() end
	local B = Ball.new({ Sport = `Soccer`; Spawn = m.BallSpawn.CFrame; Parent = m.Venue; PickupRange = T.PickupRange })
	B.Friction = 0.9
	B.FloorY = m.Court.Position.Y - 0.5
	B.StaleAfter = 20
	B.CanTouch = function(P)
		if not m.Team[P] or os.clock() < S.PauseUntil or (S.Suspect[P] or 0) > os.clock() then return false end
		local C = P.Character
		return C ~= nil and (C:GetAttribute(`SportStun`) or 0) < workspace:GetServerTimeNow()
	end
	B.ReachFor = function(P)
		local Base = T.PickupRange
		if Local.IsKeeper(m, P) and Local.InZone(m, P) then Base = T.Keeper.Reach end
		if S.Diving[P] and os.clock() < S.Diving[P] then Base = T.Keeper.Reach + 2 end
		if S.Tackling[P] and os.clock() < S.Tackling[P] then Base = math.max(Base, T.Tackle.Reach * Local.ReachBonus(P)) end
		return Base
	end
	B.OnTouch = function(_, P) Local.Touch(m, P) end
	B.OnStale = function() if m.Phase == `Live` and os.clock() >= S.PauseUntil then Local.Kickoff(m, nil, `Dead ball`) end end
	S.Ball = B
end

function Local.ReachBonus(P: Player): number
	return 1 + (if P:GetAttribute(`Race`) == `Wraith` then Config.Perk(`Wraith`, `Reach`) else 0)
end

function Local.Give(m, P: Player, How: string)
	local S = m.S
	if not S.Ball:Possess(P) then return end
	S.Dodge[P] = os.clock() + T.DodgeOnPickup
	S.HeldSince = os.clock()
	S.Charge[P] = nil
	S.Tackling[P] = nil
	if S.LastPass and m.Team[S.LastPass.From] ~= m.Team[P] then S.LastPass = nil end
	if How ~= `Kickoff` then m:Stat(P, `Touches`) end
	fx(`S_Pickup`, { Player = P })
end

-- a loose ball reached someone: a stored kick (volley / header) strikes it, otherwise they trap it
function Local.Touch(m, P: Player)
	local S = m.S
	local B = S.Ball
	if B.State == `Held` or os.clock() < S.PauseUntil then return end
	local W = S.Window[P]
	local Speed = B.Part.AssemblyLinearVelocity.Magnitude
	local R = root(P)
	if W and os.clock() < W.Until and R then
		S.Window[P] = nil
		local High = B.Part.Position.Y > R.Position.Y + 1.2
		local Power = if High then T.Kick.HeaderPower else T.Kick.VolleyPower
		Local.Strike(m, P, W.Aim, Power, nil, B.Part.CFrame, if High then `Header` else `Volley`)
		return
	end
	-- a pass or a loose ball: trap it (ignore a teammate's ball still in its first instant off the foot)
	Local.Give(m, P, if Speed > 30 then `Trap` else `Pickup`)
end

function Local.Strike(m, P: Player, Aim: Vector3, Power: number, Curve: number?, From: CFrame?, Kind: string)
	local S = m.S
	local R = root(P)
	if not R then return end
	local Bonus = if S.Rush[P] and os.clock() < S.Rush[P] then T.Bloodrush.Power else 0
	if P:GetAttribute(`Race`) == `Vampire` and Local.Night() then Bonus += Config.Perk(`Vampire`, `NightAccuracy`) * 0.5 end
	local V = Rules.ShotVelocity(Aim, Power, Bonus)
	local CurveVec = nil
	if Curve and Curve ~= 0 then
		local Side = flat(Aim):Cross(Vector3.yAxis)
		if Side.Magnitude > 1e-3 then CurveVec = Side.Unit * Curve * T.Kick.Curve * Power end   -- D (+1) bends right, A (-1) left
	end
	local Start = From or (R.CFrame * CFrame.new(0, -2.05, -1.6))
	S.Ball:Kick(V, { From = Start; NoTouch = { P }; Curve = CurveVec; CurveTime = T.Kick.CurveTime; CurveBack = T.Kick.CurveBack })
	S.LastKicker = { Player = P; Team = m.Team[P]; At = os.clock() }
	S.KickAt[P] = os.clock()
	S.HeldSince = nil
	m:Stat(P, `Touches`)
	-- on target: heading into the goal mouth this team attacks
	local Goal = Local.TheirGoal(m, m.Team[P])
	if Goal and flat(Goal.Position - R.Position).Unit:Dot(flat(V).Unit) > 0.93 then Local.AddMeter(m, P, T.Bloodrush.OnTarget) end
	fx(`S_Kick`, { Player = P; Kind = Kind; Power = Power; Curve = Curve or 0 })
end

---| match plug-in |---

function Rules.Start(m, Restart: boolean?)
	local S = m.S
	if not Restart then
		Local.Fresh(m)
		Local.NewBall(m)
		-- keepers: from 3v3, a player who queued on their keeper pad
		for _, Team in { `A`, `B` } do
			if #m.Teams[Team] >= T.KeeperFrom then
				for _, P in m.Teams[Team] do
					if m.FromKeeperPad and m.FromKeeperPad[P] then S.Keeper[Team] = P P:SetAttribute(`SportKeeper`, true) break end
				end
			end
		end
		for P in m.Team do Local.SetKeys(P, true) S.Meter[P] = 0 end
	end
	S.Ball.Paused = false
	S.GoalId = nil         -- overtime / second half: any pending goal kickoff is void
	S.PauseUntil = 0
	local First = if m.Half == 2 and not m.Overtime then `B` else `A`
	Local.Kickoff(m, First)
end

function Rules.Joined(m, P: Player)
	local S = m.S
	Local.SetKeys(P, true)
	S.Meter[P] = 0
	S.Stamina[P] = Local.MaxStamina(P)
	Local.Place(m, P)
end

function Rules.OnRemoved(m, P: Player)
	local S = m.S
	if not S then return end
	if S.Ball and S.Ball.Holder == P then S.Ball:Drop(Vector3.new(0, 6, 0)) end
	for _, K in { `Stamina`, `Charge`, `Window`, `Tackling`, `Dribbling`, `Feinting`, `Diving`, `Meter`, `Rush` } do S[K][P] = nil end
	for Team, K in S.Keeper do if K == P then S.Keeper[Team] = nil end end
	P:SetAttribute(`SportKeeper`, nil)
	P:SetAttribute(`SportMeter`, nil)
	Local.SetKeys(P, false)
	local C = P.Character
	if C then C:SetAttribute(`SportStun`, nil) C:SetAttribute(`SportRush`, nil) end
	local Hum = C and C:FindFirstChildOfClass(`Humanoid`)
	if Hum then Hum:SetAttribute(`SportTired`, nil) end
	Local.Aura(P, nil)
end

function Rules.Halftime(m)
	local S = m.S
	S.Ball:Release()
	S.Ball:Reset()
	S.Ball.Paused = true
	S.Charge, S.Window = {}, {}
	S.Tackling, S.Dribbling, S.Feinting, S.Diving, S.Dodge = {}, {}, {}, {}, {}
	S.GoalId = nil         -- a goal's pending kickoff is replaced by the second-half kickoff
	S.PauseUntil = 0
end

function Rules.Stop(m)
	local S = m.S
	if not S then return end
	for P in m.Team do Rules.OnRemoved(m, P) end
	if S.Ball then S.Ball:Destroy() S.Ball = nil end
end

function Rules.Reset(m) Rules.Stop(m) end

-- a goal celebration in progress: the clock waits at zero for it (buzzer goals count)
function Rules.Busy(m): boolean
	return m.S ~= nil and os.clock() < (m.S.PauseUntil or 0)
end

-- put a player in their own half for a kickoff (A defends the east goal, B the west)
function Local.Place(m, P: Player, Index: number?, Count: number?)
	local Team = m.Team[P]
	if not Team or not P.Character then return end
	local C = m.Court
	local Own = m.S.Zones[Team]
	local Toward = if Own then flat(Own.Position - C.Position).Unit else Vector3.new(if Team == `A` then 1 else -1, 0, 0)
	local Across = Vector3.new(-Toward.Z, 0, Toward.X)
	local I, N = Index or 1, Count or 1
	local Spot = Vector3.new(C.Position.X, C.Position.Y + 2.5, C.Position.Z) + Toward * 14 + Across * ((I - (N + 1) / 2) * 9)
	if Local.IsKeeper(m, P) and Own then Spot = Vector3.new(Own.Position.X, C.Position.Y + 2.5, Own.Position.Z) + Toward * 6 end
	P.Character:PivotTo(CFrame.lookAt(Spot, Vector3.new(C.Position.X, Spot.Y, C.Position.Z)))
	if m.S.LastPos then m.S.LastPos[P] = nil end
end

-- everyone back to their half, ball to the kicking team's taker at the centre spot
function Local.Kickoff(m, Team: string?, Say: string?)
	local S = m.S
	S.Charge, S.Window = {}, {}
	S.Tackling, S.Dribbling, S.Feinting, S.Diving, S.Dodge = {}, {}, {}, {}, {}
	S.LastKicker, S.LastPass = nil, nil
	for _, T_ in { `A`, `B` } do
		for I, P in m.Teams[T_] do Local.Place(m, P, I, #m.Teams[T_]) end
	end
	local Side = Team or (if math.random() < 0.5 then `A` else `B`)
	local List = m.Teams[Side]
	if #List == 0 then List = m.Teams[m:Opponent(Side)] end
	S.Ball.Part.Anchored = false
	S.Ball:Reset(m.BallSpawn.CFrame)
	S.LastBallPos = nil
	local Taker
	for _, P in List do if not Local.IsKeeper(m, P) then Taker = P break end end
	Taker = Taker or List[1]
	if Taker and Taker.Character then
		local C = m.Court.Position
		local Own = S.Zones[m.Team[Taker]]
		local Back = if Own then flat(Own.Position - C).Unit else Vector3.new(1, 0, 0)
		local Spot = Vector3.new(C.X, C.Y + 2.5, C.Z) + Back * 2
		Taker.Character:PivotTo(CFrame.lookAt(Spot, Vector3.new(C.X, Spot.Y, C.Z) - Back))
		S.LastPos[Taker] = nil
		Local.Give(m, Taker, `Kickoff`)
	end
	if Say then m:Say(Say, 2.5) end
end

function Rules.Tick(m, dt: number)
	local S = m.S
	local B = S.Ball
	if not B then return end
	local Now = os.clock()
	if Now < S.PauseUntil then return end
	-- teleport guard: characters are client-owned, so an impossible jump between ticks freezes that player's actions
	for P in m.Team do
		local R = root(P)
		if R then
			local L = S.LastPos[P]
			if L and (R.Position - L.Pos).Magnitude / math.max(Now - L.At, 0.05) > T.MaxSpeed then
				S.Suspect[P] = Now + 1.5
				if S.Ball.Holder == P then S.Ball:Drop(Vector3.zero) end
			end
			S.LastPos[P] = { Pos = R.Position; At = Now }
		end
	end
	-- stamina and Bloodrush
	for P in m.Team do
		local Max = Local.MaxStamina(P)
		local St = S.Stamina[P] or Max
		local R = root(P)
		local Speed = R and flat(R.AssemblyLinearVelocity).Magnitude or 0
		local Rush = S.Rush[P] and Now < S.Rush[P]
		if Speed > 19 then St -= Config.Stamina.Sprint * dt * (if Rush then T.Bloodrush.Drain else 1)
		else St += Config.Stamina.RegenPerSecond * dt * (1 + (if P:GetAttribute(`Race`) == `Human` then Config.Perk(`Human`, `StaminaRegen`) else 0)) * (if B.Holder == P then 0.65 else 1) end
		local Boost = P:GetAttribute(`NHStaminaBoost`) -- (kit 1.79) a sip from the thermos
		if typeof(Boost) == `number` then St += Boost P:SetAttribute(`NHStaminaBoost`, nil) end
		S.Stamina[P] = math.clamp(St, 0, Max)
		local Hum = P.Character and P.Character:FindFirstChildOfClass(`Humanoid`)
		if Hum then Hum:SetAttribute(`SportTired`, S.Stamina[P] < 8) end
		if S.Rush[P] and Now >= S.Rush[P] then
			S.Rush[P] = nil
			Local.Aura(P, nil)
			if P.Character then P.Character:SetAttribute(`SportRush`, nil) end
		end
		P:SetAttribute(`SportMeter`, math.floor(S.Meter[P] or 0))
	end
	-- tackles in their window
	for P, Until in S.Tackling do
		if Now >= Until then
			S.Tackling[P] = nil
			-- a whiff (no carrier reached, no loose ball won) leaves you stranded
			if B.Holder ~= P then Local.Stun(P, T.Tackle.MissStun, `Missed`) end
		else
			Local.TryTackle(m, P)
		end
	end
	-- keeper: holding too long in the box throws it on its own
	local H = B.Holder
	if H and Local.IsKeeper(m, H) and Local.InZone(m, H) and S.HeldSince and Now - S.HeldSince > T.Keeper.HoldMax then
		local R = root(H)
		if R then Local.Strike(m, H, (R.CFrame.LookVector + Vector3.new(0, 0.35, 0)).Unit, 0.8, nil, nil, `Throw`) end
	end
	-- goals: a loose ball inside a goal mouth
	local Pos = B.Part.Position
	local Last = S.LastBallPos or Pos
	S.LastBallPos = Pos
	if B.State ~= `Held` then
		for Team, Mouth in S.Goals do
			if sweptBox(Mouth, Last, Pos, 0) then Local.Goal(m, Team) return end
		end
		-- escaped the pitch somehow: back to a kickoff
		if m.Bounds and not inBox(m.Bounds, B.Part.Position, 2) then Local.Kickoff(m, nil, `Ball reset`) end
	end
end

function Local.Goal(m, Team: string)
	local S = m.S
	local K = S.LastKicker
	local Scorer = K and K.Player or nil
	local Own = K ~= nil and K.Team ~= Team
	if Own and Scorer then m:Stat(Scorer, `OwnGoals`) end
	local Credit = if Own then nil else Scorer
	local P = S.LastPass
	if Credit and P and P.From ~= Credit and m.Team[P.From] == Team and os.clock() - P.At < 12 then m:Stat(P.From, `Assists`) end
	if Credit then Local.AddMeter(m, Credit, T.Bloodrush.Goal) end
	S.LastBallPos = nil
	S.Ball:Reset(m.BallSpawn.CFrame + Vector3.new(0, -20, 0))   -- out of sight under the pitch for the celebration
	S.Ball.Part.Anchored = true                                  -- (anchored, or it would fall out of the world)
	S.Ball.Paused = true
	S.PauseUntil = os.clock() + T.GoalPause
	fx(`S_Goal`, { Team = Team; Scorer = Credit; Own = Own })
	m:Say(if Own then `Own goal!` else `GOAL! {Config.Teams[Team].Name}`, T.GoalPause)
	local Id = {}
	S.GoalId = Id
	m:Scored(Team, 1, Credit)
	if m.Phase ~= `Live` then return end
	task.delay(T.GoalPause, function()
		if m.Phase ~= `Live` or not S.Ball or S.GoalId ~= Id then return end
		S.GoalId = nil
		S.Ball.Paused = false
		Local.Kickoff(m, m:Opponent(Team))
	end)
end

---| actions |---

function Rules.OnAction(m, P: Player, Action: string, Args)
	local S = m.S
	if not S or not S.Ball or S.Ball.Paused or os.clock() < S.PauseUntil then return end
	local C = P.Character
	if not C or (C:GetAttribute(`SportStun`) or 0) > workspace:GetServerTimeNow() then return end
	if (S.Suspect[P] or 0) > os.clock() then return end
	-- no shots from inside a goal mouth or outside the pitch
	local Rt = root(P)
	if not Rt then return end
	for _, Mouth in S.Goals do if inBox(Mouth, Rt.Position, 1) then return end end
	if m.Bounds and not inBox(m.Bounds, Rt.Position, 0) then return end
	local Holding = S.Ball.Holder == P
	local Now = os.clock()
	if Action == `KickStart` then
		if Holding and not S.Charge[P] and Now - (S.KickAt[P] or 0) >= T.Kick.Cooldown then S.Charge[P] = Now fx(`S_Charge`, { Player = P }) end
	elseif Action == `KickRelease` then
		local Aim = Rules.CleanDir(Args.Aim)
		if Holding and S.Charge[P] then
			local Held = math.min(Now - S.Charge[P], T.Kick.MaxHold)
			S.Charge[P] = nil
			local R = root(P)
			if not (Aim and R) then return end
			if Held < 0.1 then Aim = (flatUnit(R.CFrame.LookVector, flatUnit(Aim)) + Vector3.new(0, math.clamp(Aim.Y, 0, 0.5), 0)).Unit end   -- a tap kicks where you face
			if Local.IsKeeper(m, P) and Local.InZone(m, P) then
				local Power = math.clamp(Held / T.Keeper.ThrowCharge, 0.5, 1.1)
				Local.Strike(m, P, Aim, Power * 0.8, nil, nil, `Throw`)
				return
			end
			local Power = Rules.Power(Held)
			local Curve = if Held >= T.Kick.ChargeTime and (Args.Curve == 1 or Args.Curve == -1) then Args.Curve else 0
			Local.Strike(m, P, Aim, Power, Curve, nil, `Shot`)
		elseif not Holding and Aim then
			-- no ball: a stored kick for a volley or header on whatever arrives next (a keeper in their box catches instead)
			if Local.IsKeeper(m, P) and Local.InZone(m, P) then return end
			if Now - (S.KickAt[P] or 0) < T.Kick.Cooldown then return end
			S.KickAt[P] = Now
			S.Window[P] = { Until = Now + T.Kick.KickWindow; Aim = Aim }
			fx(`S_Kick`, { Player = P; Kind = `Swing`; Power = 0 })
		end
	elseif Action == `Pass` then
		if Holding and Now - (S.PassAt[P] or 0) >= T.Pass.Cooldown then Local.Pass(m, P, Rules.CleanDir(Args.Aim)) end
	elseif Action == `Call` then
		if not Holding and Now - (S.PassAt[P] or 0) >= 2 then S.PassAt[P] = Now fx(`S_Call`, { Player = P }) end
	elseif Action == `Dribble` then
		if Holding and Now - (S.DribbleAt[P] or 0) >= T.Dribble.Cooldown and Local.Spend(m, P, T.Dribble.Stamina) then
			S.DribbleAt[P] = Now
			S.Dribbling[P] = Now + T.Dribble.Time
			S.Charge[P] = nil
			fx(`S_Dribble`, { Player = P; Dir = Rules.CleanDir(Args.Dir) })
		end
	elseif Action == `Feint` then
		if Holding and Now - (S.FeintAt[P] or 0) >= T.Feint.Cooldown and Local.Spend(m, P, T.Feint.Stamina) then
			S.FeintAt[P] = Now
			S.Feinting[P] = Now + T.Feint.Window
			S.Charge[P] = nil
			fx(`S_Feint`, { Player = P })
		end
	elseif Action == `Tackle` then
		local Cd = T.Tackle.Cooldown * (if S.Rush[P] and Now < S.Rush[P] then 0.75 else 1)
		if not Holding and Now - (S.TackleAt[P] or 0) >= Cd and Local.Spend(m, P, T.Tackle.Stamina) then
			S.TackleAt[P] = Now
			S.Tackling[P] = Now + T.Tackle.Window
			fx(`S_Tackle`, { Player = P; Dir = Rules.CleanDir(Args.Dir) })
		end
	elseif Action == `Dive` then
		if not Holding and Local.IsKeeper(m, P) and Local.InZone(m, P) and Now - (S.DiveAt[P] or 0) >= T.Keeper.DiveCooldown then
			S.DiveAt[P] = Now
			S.Diving[P] = Now + 1.2
			fx(`S_Dive`, { Player = P; Dir = Rules.CleanDir(Args.Dir) })
		end
	elseif Action == `Bloodrush` then
		Local.Rush(m, P)
	end
end

function Local.Pass(m, P: Player, Aim: Vector3?)
	local S = m.S
	local R = root(P)
	local Team = m.Team[P]
	if not (R and Team) then return end
	Aim = if Aim and flat(Aim).Magnitude > 1e-3 then flat(Aim).Unit else flatUnit(R.CFrame.LookVector)
	local Target, Best = nil, 0.6
	for Q, QT in m.Team do
		local QR = root(Q)
		if Q ~= P and QT == Team and QR then
			local Off = flat(QR.Position - R.Position)
			if Off.Magnitude > 3 and Off.Magnitude <= T.Pass.Range then
				local Dot = Off.Unit:Dot(Aim)
				if Dot > Best then Target, Best = Q, Dot end
			end
		end
	end
	local V
	if Target then
		local QR = root(Target) :: BasePart
		local Dist = flat(QR.Position - R.Position).Magnitude
		local Speed = math.clamp(45 + Dist * 0.9, 45, 110)
		local Lead = flat(QR.AssemblyLinearVelocity) * math.min(Dist / Speed, 0.8)
		local Acc = 1 + (if P:GetAttribute(`Race`) == `Priest` then Config.Perk(`Priest`, `PassAccuracy`) else 0)
		local To = QR.Position + Lead + Vector3.new((math.random() - 0.5) * 2 / Acc, 0, (math.random() - 0.5) * 2 / Acc)
		V = flat(To - R.Position).Unit * Speed + Vector3.new(0, 3 + Dist * 0.04, 0)
	else
		V = Aim * 60 + Vector3.new(0, 4, 0)   -- into space
	end
	S.PassAt[P] = os.clock()
	S.LastPass = { From = P; At = os.clock() }
	S.Ball:Kick(V, { From = R.CFrame * CFrame.new(0, -2.05, -1.6); NoTouch = { P } })
	S.LastKicker = { Player = P; Team = Team; At = os.clock() }
	S.HeldSince = nil
	m:Stat(P, `Touches`)
	fx(`S_Pass`, { Player = P; To = Target })
end

-- a tackler in their window: reach the ball carrier (or a loose ball, through the normal touch)
function Local.TryTackle(m, P: Player)
	local S = m.S
	local H = S.Ball.Holder
	if not H or H == P or m.Team[H] == m.Team[P] then return end
	local R, HR = root(P), root(H)
	if not (R and HR) or flat(HR.Position - R.Position).Magnitude > T.Tackle.Reach * Local.ReachBonus(P) then return end
	local Now = os.clock()
	S.Tackling[P] = nil
	if S.Dodge[H] and Now < S.Dodge[H] then return end
	if S.Feinting[H] and Now < S.Feinting[H] then
		-- feint counters the tackle: the tackler is stunned, the carrier slips away
		Local.Stun(P, T.Tackle.MissStun, `Feinted`)
		S.Dodge[H] = Now + 0.6
		Local.AddMeter(m, H, T.Bloodrush.Ankles)
		fx(`S_Ankles`, { Player = P; By = H; Kind = `Feint` })
		m:Say(`Feinted!`, 1.5)
		return
	end
	if S.Dribbling[H] and Now < S.Dribbling[H] then
		-- tackled into a dribble: ankles broken
		Local.Stun(P, T.Dribble.AnkleRagdoll, `Ankles`)
		S.DribbleAt[H] = Now - T.Dribble.Cooldown + 1.6
		Local.AddMeter(m, H, T.Bloodrush.Ankles)
		m:Stat(H, `AnkleBreaks`)
		fx(`S_Ankles`, { Player = P; By = H; Kind = `Dribble` })
		m:Say(`Ankles!`, 1.5)
		return
	end
	if H:GetAttribute(`Race`) == `Ghoul` and math.random() < Config.Perk(`Ghoul`, `StripResist`) then
		Local.Stun(P, T.Tackle.MissStun * 0.5, `Bounced`)
		return
	end
	-- clean tackle: the ball changes hands, the carrier goes down for a moment
	Local.Give(m, P, `Steal`)
	m:Stat(P, `Steals`)
	Local.AddMeter(m, P, T.Bloodrush.Steal)
	Local.Stun(H, T.Tackle.HitStun, `Tackled`)
	fx(`S_Stolen`, { Player = P; From = H; Push = flat(HR.Position - R.Position) })
end

-- stun: the character attribute the client honours (no movement, no actions); server checks it on every action
function Local.Stun(P: Player, Seconds: number, Why: string)
	local C = P.Character
	if not C then return end
	C:SetAttribute(`SportStun`, workspace:GetServerTimeNow() + Seconds)
	fx(`S_Stun`, { Player = P; Seconds = Seconds; Why = Why })
end

---| stamina, meter, Bloodrush |---

function Local.MaxStamina(P: Player): number
	local Prog = try({ `Services`, `Player`, `Progression` })
	local St = Prog and Prog.Get(P)
	local Grit = St and St.Stats and St.Stats.Grit or 0
	return Config.Stamina.Max * (1 + Grit * Config.StatScale.Grit)
end

function Local.Spend(m, P: Player, Cost: number): boolean
	local S = m.S
	local St = S.Stamina[P] or Local.MaxStamina(P)
	if St < Cost then Local.FxTo(P, `S_Text`, { Player = P; Text = `Out of gas` }) return false end
	S.Stamina[P] = St - Cost
	return true
end

function Local.AddMeter(m, P: Player, Amount: number)
	local S = m.S
	if S.Rush[P] then return end
	S.Meter[P] = math.min(100, (S.Meter[P] or 0) + Amount)
end

function Local.Rush(m, P: Player)
	local S = m.S
	local Meter = S.Meter[P] or 0
	if Meter < T.Bloodrush.Min or S.Rush[P] then return end
	local Seconds = T.Bloodrush.Seconds * Meter / 100
	S.Meter[P] = 0
	S.Rush[P] = os.clock() + Seconds
	if P.Character then P.Character:SetAttribute(`SportRush`, workspace:GetServerTimeNow() + Seconds) end
	-- VFX P2-6: clients draw the aura from the SportRush attribute (Controllers.Gui.Soccer); no server emitter
	fx(`S_Bloodrush`, { Player = P; Seconds = Seconds })
	m:Say(`{P.DisplayName}: Bloodrush!`, 2)
end

function Local.Aura(P: Player, Color: Color3?)
	local R = root(P)
	if not R then return end
	local Old = R:FindFirstChild(`SportAura`)
	if Old then Old:Destroy() end
	if not Color then return end
	local A = Instance.new(`Attachment`)
	A.Name = `SportAura`
	local E = Instance.new(`ParticleEmitter`)
	E.Texture = `rbxasset://textures/particles/sparkles_main.dds`
	E.Color = ColorSequence.new(Color)
	E.LightEmission = 0.7
	E.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.6), NumberSequenceKeypoint.new(1, 0) })
	E.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.3), NumberSequenceKeypoint.new(1, 1) })
	E.Lifetime = NumberRange.new(0.5, 0.9) E.Rate = 28 E.Speed = NumberRange.new(1, 3) E.SpreadAngle = Vector2.new(180, 180)
	E.Acceleration = Vector3.new(0, 4, 0)
	E.Parent = A
	A.Parent = R
end

function Local.Night(): boolean
	local Clock = try({ `Services`, `School`, `SchoolClock` })
	local S = Clock and Clock.GetState()
	return S ~= nil and S.Segment ~= nil and S.Segment.Kind == `Night` -- (audit) Segment is a table
end

function Rules.Hud(m, For: Player?)
	local S = m.S
	if not S then return nil end
	local H = S.Ball and S.Ball.Holder
	return {
		Possession = H and m.Team[H] or nil;
		HasBall = For ~= nil and H == For;
		Stamina = For and S.Stamina[For] or nil; StaminaMax = For and m.Team[For] and Local.MaxStamina(For) or nil;
		Meter = For and S.Meter[For] or nil; MeterMin = T.Bloodrush.Min;
		Rush = For ~= nil and S.Rush[For] ~= nil and os.clock() < S.Rush[For];
		Keeper = For ~= nil and Local.IsKeeper(m, For); InZone = For ~= nil and m.Team[For] ~= nil and Local.InZone(m, For);
		Charge = { Time = T.Kick.ChargeTime; Max = T.Kick.MaxHold };
	}
end

---| drills: Target Practice, Wall Passes |---

Local.Drills = {} :: { [Player]: any }
local Stations = {} :: { [string]: Player }
local PaidAt = {} :: { [string]: number }
local REWARD_COOLDOWN = 180

local function pitch(): Model? return workspace:FindFirstChild(`Sports`) and workspace.Sports:FindFirstChild(`Pitch`) end
local function part(Attr: string, Value: any): BasePart?
	local Pt = pitch()
	if not Pt then return nil end
	for _, D in Pt:GetDescendants() do
		if D:IsA(`BasePart`) and D:GetAttribute(Attr) == Value then return D end
	end
	return nil
end

function Local.Teleported(D, R: BasePart): boolean
	local Now = os.clock()
	local L = D.Seen
	D.Seen = { Pos = R.Position; At = Now }
	return L ~= nil and (R.Position - L.Pos).Magnitude / math.max(Now - L.At, 0.05) > T.MaxSpeed
end

function Local.EndDrill(P: Player, Why: string?)
	local D = Local.Drills[P]
	if not D then return end
	Local.Drills[P] = nil
	if Stations[D.Drill] == P then Stations[D.Drill] = nil end
	if D.Ball then D.Ball:Destroy() end
	if D.Cleanup then pcall(D.Cleanup) end
	if P.Parent then
		P:SetAttribute(`InDrill`, nil)
		Local.SetKeys(P, false)
		local R = ReplicatedStorage.NHSports:FindFirstChild(`Hud`)
		if R then R:FireClient(P, nil) end
		if Why then
			local N = try({ `Services`, `Features`, `Notifications` })
			if N then pcall(N.Notify, P, { Title = `Drill over`; Text = Why; Kind = `Info`; Duration = 4 }) end
		end
	end
end

function Local.FinishDrill(P: Player, Drill: string, Score: number, Passed: boolean, Text: string)
	local Def = Config.Drills[Drill]
	local Best = Passed and clubs().DrillBest(P, Drill, Score, false) or false
	local Key = `{P.UserId}:{Drill}`
	local Paid = Passed and os.clock() - (PaidAt[Key] or -math.huge) >= REWARD_COOLDOWN
	if Paid then PaidAt[Key] = os.clock() end
	local Exp = 0
	if Paid then
		local Prog = try({ `Services`, `Player`, `Progression` })
		if Prog then Exp = Prog.Award(P, `SportDrill`, nil, Def.Name) or 0 end
		local E = Config.ClubExp
		clubs().AddExp(P, Def.Sport, E.Drill + (if Best then E.DrillBest else 0), Def.Name)
	end
	if Passed then
		local Quests = try({ `Services`, `Quests`, `Quests` })
		if Quests and Quests.Progress then pcall(Quests.Progress, P, `Drill`, Drill) end
	end
	local S = ReplicatedStorage.NHSports:FindFirstChild(`Summary`)
	if S then S:FireClient(P, { Drill = Drill; Name = Def.Name; Score = Score; Best = Best; Passed = Passed; Paid = Paid; Text = Text; Exp = Exp }) end
	Local.EndDrill(P)
end

function Local.DrillBall(P: Player, D, Spawn: BasePart, Bounds: BasePart)
	local B = Ball.new({ Sport = `Soccer`; Spawn = Spawn.CFrame; Parent = Spawn.Parent; PickupRange = T.PickupRange })
	B.Friction = 0.9
	B.FloorY = Spawn.Position.Y - 1.5
	B.CanTouch = function(Q) return Q == P end
	B.OnTouch = function(b, Q) if Q == P then b:Possess(P) D.Message = nil end end
	B.StaleAfter = 6
	B.OnStale = function(b) b:Reset() end
	return B
end

function Local.StartTargets(P: Player)
	local Spawn, Bounds = part(`SportDrillBall`, `TargetPractice`), part(`SportDrillBounds`, `TargetPractice`)
	local Start = part(`SportDrillStart`, true)
	if not (Spawn and Bounds) then return nil end
	local Targets, Sensors = {}, {}
	for I = 1, 4 do Targets[I] = part(`SportTarget`, I) Sensors[I] = part(`SportTargetSensor`, I) end
	local Line = Spawn.Position.X - 3   -- shots count from behind (east of) this line
	local D = { Drill = `TargetPractice`; Score = 0; Goal = Config.Drills.TargetPractice.Goal; Started = os.clock(); Seconds = Config.Drills.TargetPractice.Seconds }
	D.Clock = function() return math.max(0, D.Seconds - (os.clock() - D.Started)) end
	D.Ball = Local.DrillBall(P, D, Spawn, Bounds)
	D.Ball:Possess(P)
	local function light(I)
		D.Lit = I
		for J, Tg in Targets do if Tg then Tg.Transparency = if J == I then 0 else 0.7 end end
		D.Spot = I
	end
	light(math.random(4))
	D.Cleanup = function() for _, Tg in Targets do if Tg then Tg.Transparency = 0.35 end end end
	D.OnKick = function(R: BasePart)
		D.ShotFrom = R.Position.X
		D.Checking = true
		D.KickedAt = os.clock()
	end
	D.Tick = function()
		if D.Clock() <= 0 then Local.FinishDrill(P, `TargetPractice`, D.Score, D.Score >= D.Goal, `{D.Score} targets in time.`) return end
		local R = root(P)
		if R and Local.Teleported(D, R) then Local.EndDrill(P, `That was too fast to count. Run it again.`) return end
		if not R or not inBox(Bounds, R.Position, 3) then Local.EndDrill(P, `You left the practice area.`) return end
		local B = D.Ball
		local Pos = B.Part.Position
		local Last = D.LastPos or Pos
		D.LastPos = Pos
		if D.Checking and B.State ~= `Held` then
			local S = Sensors[D.Lit]
			if S and sweptBox(S, Last, Pos, 0.4) then
				D.Checking = false
				if D.ShotFrom and D.ShotFrom >= Line then
					D.Score += 1
					fx(`S_Target`, { Player = P; Index = D.Lit })
					local Next = D.Lit
					while Next == D.Lit do Next = math.random(4) end
					light(Next)
				else
					D.Message = `Shoot from behind the line`
				end
			end
		end
		if D.KickedAt and os.clock() - D.KickedAt > 2.5 then
			D.Checking = false
			D.KickedAt = nil
			-- feed the ball back
			if B.State ~= `Held` then B:Possess(P) end
		end
	end
	return D
end

function Local.StartWall(P: Player)
	local Spawn, Bounds = part(`SportDrillBall`, `WallPasses`), part(`SportDrillBounds`, `WallPasses`)
	local Sensor = part(`SportReboundSensor`, true)
	if not (Spawn and Bounds and Sensor) then return nil end
	local Line = Sensor.Position.X - 9    -- pass from behind (west of) this line
	local D = { Drill = `WallPasses`; Score = 0; Goal = Config.Drills.WallPasses.Goal; Started = os.clock(); Seconds = Config.Drills.WallPasses.Seconds }
	D.Clock = function() return math.max(0, D.Seconds - (os.clock() - D.Started)) end
	D.Ball = Local.DrillBall(P, D, Spawn, Bounds)
	D.Ball:Possess(P)
	D.OnKick = function(R: BasePart)
		D.From = R.Position.X
		D.HitWall = false
		D.KickedAt = os.clock()
	end
	local Base = D.Ball.OnTouch
	D.Ball.OnTouch = function(b, Q)
		if Q ~= P then return end
		-- a clean pass: from behind the line, off the wall, controlled within 3 s
		if D.HitWall and D.KickedAt and os.clock() - D.KickedAt <= 3 and (D.From or math.huge) <= Line then
			D.Score += 1
			fx(`S_Target`, { Player = P; Index = 0 })
		end
		D.HitWall, D.KickedAt = false, nil
		Base(b, Q)
	end
	D.Tick = function()
		if D.Clock() <= 0 then Local.FinishDrill(P, `WallPasses`, D.Score, D.Score >= D.Goal, `{D.Score} clean passes.`) return end
		local R = root(P)
		if R and Local.Teleported(D, R) then Local.EndDrill(P, `That was too fast to count. Run it again.`) return end
		if not R or not inBox(Bounds, R.Position, 3) then Local.EndDrill(P, `You left the practice area.`) return end
		local Pos = D.Ball.Part.Position
		local Last = D.LastPos or Pos
		D.LastPos = Pos
		if D.KickedAt and not D.HitWall and sweptBox(Sensor, Last, Pos, 0.5) then D.HitWall = true end
		if D.KickedAt and os.clock() - D.KickedAt > 4 then D.KickedAt = nil end
	end
	return D
end

function Local.DrillHud(P: Player)
	local D = Local.Drills[P]
	local R = ReplicatedStorage.NHSports:FindFirstChild(`Hud`)
	if not (D and R) then return end
	R:FireClient(P, { Sport = `Soccer`; Drill = D.Drill; Name = Config.Drills[D.Drill].Name; Clock = D.Clock(); Score = D.Score; Goal = D.Goal;
		HasBall = D.Ball and D.Ball.Holder == P; Message = D.Message; Charge = { Time = T.Kick.ChargeTime; Max = T.Kick.MaxHold } })
end

-- called by Matches for players not in a match; true when handled
function Rules.DrillAction(P: Player, Action: string, Args): boolean
	local D = Local.Drills[P]
	if Action == `DrillStart` then
		local Drill = Args.Drill
		if Drill ~= `TargetPractice` and Drill ~= `WallPasses` then return false end
		if D or P:GetAttribute(`InSport`) or P:GetAttribute(`InDrill`) then return true end
		local Start
		local Pt = pitch()
		for _, X in (Pt and Pt:GetDescendants() or {}) do
			if X:IsA(`BasePart`) and X:GetAttribute(`SportDrillStart`) and X:GetAttribute(`SportDrill`) == Drill then Start = X end
		end
		local R = root(P)
		local C = P.Character
		local Hum = C and C:FindFirstChildOfClass(`Humanoid`)
		local Downed = try({ `Services`, `Features`, `Downed` })
		if not (Start and R and Hum and Hum.Health > 0) or flat(R.Position - Start.Position).Magnitude > 7 then return true end
		if C:GetAttribute(`Dueling`) or C:GetAttribute(`NH_Evolving`) or (Downed and Downed.IsDowned(C)) then return true end
		if Stations[Drill] and Stations[Drill].Parent and Local.Drills[Stations[Drill]] then
			local N = try({ `Services`, `Features`, `Notifications` })
			if N then pcall(N.Notify, P, { Title = `Station busy`; Text = `{Stations[Drill].DisplayName} is using it.`; Kind = `Info`; Duration = 3 }) end
			return true
		end
		local New = if Drill == `TargetPractice` then Local.StartTargets(P) else Local.StartWall(P)
		if New then
			Local.Drills[P] = New
			Stations[Drill] = P
			P:SetAttribute(`InDrill`, Drill)
			Local.SetKeys(P, true)
		end
		return true
	end
	if not D then return false end
	local Now = os.clock()
	if Action == `DrillQuit` then Local.EndDrill(P, `You stopped the drill.`)
	elseif Action == `KickStart` then
		if D.Ball.Holder == P then D.Charge = Now fx(`S_Charge`, { Player = P }) end
	elseif Action == `KickRelease` or Action == `Pass` then
		local R = root(P)
		local Aim = Rules.CleanDir(Args.Aim)
		if not (R and Aim and D.Ball.Holder == P) then D.Charge = nil return true end
		local V
		if Action == `Pass` then
			V = flatUnit(Aim, flatUnit(R.CFrame.LookVector)) * 70 + Vector3.new(0, 3, 0)
		else
			local Held = math.min(Now - (D.Charge or Now), T.Kick.MaxHold)
			local Power = Rules.Power(Held)
			V = Rules.ShotVelocity(Aim, Power)
		end
		D.Charge = nil
		D.Ball:Kick(V, { From = R.CFrame * CFrame.new(0, -2.05, -1.6); NoTouch = { P }; NoTouchFor = 0.3 })
		if D.OnKick then D.OnKick(R) end
		fx(`S_Kick`, { Player = P; Kind = if Action == `Pass` then `Pass` else `Shot`; Power = 1 })
	end
	return true
end

function Rules.OnStart()
	Local.BallOnlyWalls() -- (playtest-blockers) also from here, whichever runs first
	-- drill stations: a prompt on each start pad
	task.spawn(function()
		local Pt = workspace:WaitForChild(`Sports`, 30) and workspace.Sports:WaitForChild(`Pitch`, 30)
		if not Pt then return end
		Pt:WaitForChild(`Soccer`, 30)
		for _, X in Pt:GetDescendants() do
			if X:IsA(`BasePart`) and X:GetAttribute(`SportDrillStart`) then
				local Drill = X:GetAttribute(`SportDrill`)
				local Def = Config.Drills[Drill]
				if Def and not X:FindFirstChild(`DrillPrompt`) then
					local Pr = Instance.new(`ProximityPrompt`)
					Pr.Name = `DrillPrompt` Pr.ActionText = `Start {Def.Name}` Pr.ObjectText = `Grave Rovers drill`
					Pr.KeyboardKeyCode = Enum.KeyCode.E Pr.HoldDuration = 0.25 Pr.MaxActivationDistance = 6 Pr.RequiresLineOfSight = false
					Pr.Parent = X
					Pr.Triggered:Connect(function(P) Rules.DrillAction(P, `DrillStart`, { Drill = Drill }) end)
				end
			end
		end
	end)
	task.spawn(function()
		while true do
			task.wait(0.1)
			for P, D in Local.Drills do
				if not P.Parent then Local.EndDrill(P) continue end
				local C = P.Character
				local Hum = C and C:FindFirstChildOfClass(`Humanoid`)
				if not (Hum and Hum.Health > 0) or (C and C:GetAttribute(`InSport`)) then Local.EndDrill(P) continue end
				local Ok, Err = pcall(D.Tick)
				if not Ok then warn(`[Soccer drill] {Err}`) Local.EndDrill(P) continue end
				if Local.Drills[P] == D then Local.DrillHud(P) end
			end
		end
	end)
	Players.PlayerRemoving:Connect(function(P) Local.EndDrill(P) end)
end

Rules._Local = Local   -- tests
Rules.SweptBox = sweptBox
return Rules
