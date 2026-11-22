--!strict
--[[
	CineActor (client). StarterPlayer.StarterPlayerScripts.Controllers.CineActor   (2.35.0, spec 2026-11-20 §2)
	The player's own character as a seamless cut's actor: input eases out, it walks to marks ON FOOT (Approach: the game's own Walk / Run / CrouchWalk, never a slide, lerp or teleport on screen), it plays
	TutorialAnim chains over its normal Animate, and at the end its root is re-seated under the body on the same frame
	the _End pose takes over, so nothing moves; then the game's idle/walk blends back in.
	Only a chain that ends on a one-shot is re-seated (build.py ends that piece at rest, so the re-seat is a still pose to an
	identical still pose). A chain that ends on a LOOP (Drainpipe, BiscuitStirs, Getaway, HomeAgain, ParentsWaiting,
	Breakfast, MomSlidesEnvelope) hands back through Release WITHOUT a re-seat (controller ruling): those loops are in
	place (GameCrouch is the game's own crouch), so there is nothing to re-seat and the loop fades into the game's anims.
	Release also stops a chain that is still running (the Skip path).
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local ContentProvider = game:GetService(`ContentProvider`)

local Player = Players.LocalPlayer
local Shared = {}
local Held = false
local EndTrack: AnimationTrack? = nil                       -- the held _End pose (after a re-seat), until Release
local EndAnim: Animation? = nil
local Pending: AnimationTrack? = nil                        -- a Reseat's _End track before its step lands
local PendingAnim: Animation? = nil
local ChainTracks: { [string]: AnimationTrack }? = nil      -- the last Chain's tracks (its last piece held at its end)
local Gen = 0                                               -- cancellation token: Release and every Reseat bump it
local ChainGen = 0                                          -- a running Chain's token: only Release bumps it
local SpeedWas: number? = nil
local EaseOver = false                                      -- an Approach asks Begin to end its ease at once (the walk carries on, it doesn't stop and start)
local Easing = false                                        -- Begin's 0.3 s input ease is running (Approach waits it out)
local Approaching = false                                   -- an Approach is driving the character (fix round 1)
local ApproachDepth = 0                                     -- (fix round 2) how many are running (Approaching = depth > 0)
local STRIDE = { Walk = 10, CrouchWalk = 7, Sprint = 24, FastSprint = 30 } -- (fix round 2) studs/s at speed 1: AnimationController's own scales
local WALK, RUN, CROUCH = 12, 25, 7                         -- the game's own speeds: Sprint's Release, Sprint's Activate, Services.Player.Crouch

local function controls()
	local Ok, C = pcall(function() return require(Player.PlayerScripts:WaitForChild(`PlayerModule`)):GetControls() end)
	return if Ok then C else nil
end
local function parts()
	local C = Player.Character
	local Hum = C and C:FindFirstChildOfClass(`Humanoid`)
	local Root = C and C:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	local Animator = Hum and Hum:FindFirstChildOfClass(`Animator`)
	return C, Hum, Root, Animator
end

function Shared.Begin()
	if Held then return end
	Held = true
	-- (task 7) a Release during the ease-out (Skip, or a cut that ends at once) wins: only Release bumps ChainGen, so
	-- if it moved, the ease stops and the controls are NOT disabled (it used to leave them off with Held = false)
	local My = ChainGen
	local _, Hum = parts()
	if Hum then
		SpeedWas = Hum.WalkSpeed
		local T0, S0 = os.clock(), Hum.WalkSpeed
		Easing = true
		-- (task 8 fix round 1) a speed someone else writes during the ease (the server standing a beat's crouch back up:
		-- 7 -> 14.4 replicating in) becomes the speed handed back; restoring the stale one left you at crouch speed
		local Wrote: number? = nil
		while os.clock() - T0 < 0.3 and ChainGen == My and not EaseOver do  -- input eases out (spec §2.1): 0.3 s (an Approach that starts now takes it over)
			if Wrote and math.abs(Hum.WalkSpeed - Wrote) > 1e-3 then SpeedWas = Hum.WalkSpeed end
			Wrote = S0 * (1 - (os.clock() - T0) / 0.3)
			Hum.WalkSpeed = Wrote :: number
			RunService.Heartbeat:Wait()
		end
		if Wrote and math.abs(Hum.WalkSpeed - Wrote) > 1e-3 then SpeedWas = Hum.WalkSpeed end
		Hum.WalkSpeed = SpeedWas :: number
		Easing = false
		EaseOver = false
	end
	if ChainGen ~= My then return end
	local Ctl = controls()
	-- (fix round 1, I2) disabling the controls writes a zero move: with an Approach already walking you, that was a one-step stop at the
	-- beat -> approach seam. The walk's move is put straight back (the Approach steers it again on its next frame)
	local Mv = Hum and Hum.MoveDirection
	if Ctl then Ctl:Disable() end
	if Approaching and Hum and Mv and Mv.Magnitude > 0.1 then Hum:Move(Mv, false) end
end

local function flat(V: Vector3): Vector3 return Vector3.new(V.X, 0, V.Z) end
local function yawOf(V: Vector3): number return math.atan2(-V.X, -V.Z) end -- 0 = facing -Z, positive = left
local function wrap(Deg: number): number return (Deg + 540) % 360 - 180 end

-- Approach (task 14, owner request 2026-11-21). The character gets to a mark ON FOOT, with the game's own locomotion: the
-- Humanoid is driven (Move toward the waypoint every frame) at the gait's WalkSpeed and Controllers.Character.AnimationController plays Walk / Sprint /
-- CrouchWalk from its speed, so nothing here animates and nothing is placed. It arrives already facing the mark: a lead-in
-- waypoint LeadIn studs behind the mark along its facing is walked to first (skipped if the character is already within ~30 degrees
-- of the mark's facing and in line with it), then the last steps run straight at the mark and AutoRotate has the body facing along
-- them. The few degrees left at the stop (TurnMax at most) turn over 0.45 s or more (45 degrees a second at most on average) while the next piece
-- fades in: a turn inside the blend, never a spin. (fix round 1) The turn is about where the root IS (it never pins it to the arrival
-- point), and a Reseat or a Release cancels it. A heading more than TurnMax off as the stop nears is not turned on the spot: the walk keeps
-- steering (once round the lead-in again) instead.
-- Opts: Gait "Walk" | "Run" | "Crouch" | "Sneak" (Crouch and Sneak are the game's crouch: speed 7; the crouch is asked of the server if
-- it isn't up), LeadIn (3.0), Arrive (0.35 studs), BlendLead (0.2 s), OnNear(secondsLeft) (fires once, BlendLead before arrival, so the
-- caller can start the next piece's fade-in), Timeout (seconds; default from the distance),
-- (fix round 1) EaseOut (true: the pace eases down over the last stud), StopWhen() (asked every frame on the last leg: true = stop here,
-- the caller's next piece has taken over), OnLeft(studs) (every frame on the last leg: the distance left), TurnMax (20 degrees),
-- NearSkip (0.5 studs) and NearTurn (TurnMax; fix round 2): already this close to the mark and this nearly facing it, there is no walk at all and the
-- heading turns in the blend.
-- Returns true on arrival. Otherwise false and a reason: "blocked" (no progress for 3 s), "timeout", "fell" (dropped 8 studs), "died"
-- (Health 0 or the character gone), "released" (Release ran) or "nochar". On blocked / timeout / fell the caller dips to black and places
-- the character (Shared.Fallback); on died / released / nochar it does neither (nothing to place, and no chain on a dead character).
local LastRise: number? = nil                                -- the root's height over the ground at the last Approach's start (Fallback places at it)
-- (fix round 2, m-1) the floor under a point: solid parts only (RespectCanCollide), cast from just above it (2 studs, so a roof or a
-- branch overhead isn't taken for the floor), and a hit above the point itself is refused (Above: a mark part sitting on the floor may
-- have its centre a little under the floor's top)
local function groundBelow(At: Vector3, Char: Model?, Above: number?): number?
	local Params = RaycastParams.new()
	Params.FilterType = Enum.RaycastFilterType.Exclude
	Params.FilterDescendantsInstances = if Char then { Char } else {}
	Params.RespectCanCollide = true
	local Hit = workspace:Raycast(At + Vector3.new(0, 2, 0), Vector3.new(0, -40, 0), Params)
	if not Hit or Hit.Position.Y > At.Y + (Above or 0.05) then return nil end
	return Hit.Position.Y
end
local function approach(Mark: CFrame, Opts: { Gait: string?, LeadIn: number?, Arrive: number?, BlendLead: number?, OnNear: ((number) -> ())?, Timeout: number?,
	EaseOut: boolean?, StopWhen: (() -> boolean)?, OnLeft: ((number) -> ())?, TurnMax: number?, NearSkip: number?, NearTurn: number? }?, State: { Restore: (() -> ())? }?): (boolean, string?)
	local Opt = Opts or {}
	local Char, Hum, Root = parts()
	if not (Char and Hum and Root) then return false, `nochar` end
	if Hum.Health <= 0 then return false, `died` end
	local My = ChainGen
	-- (fix round 1, I2) the walk you have as the approach takes over: it carries on through the frame Begin's ease takes to end (nothing
	-- else moves you then: the controls are going off) and the pace ramps up from it
	local V0 = flat(Root.AssemblyLinearVelocity)
	if Easing then EaseOver = true end                          -- Begin's ease would slow a walking player to a stop first: end it now
	while Easing and ChainGen == My do                          -- (it writes the speed each frame)
		if V0.Magnitude > 0.5 then Hum:Move(V0.Unit, false) end
		RunService.Heartbeat:Wait()
	end
	if ChainGen ~= My then return false, `released` end
	local Gait = Opt.Gait or `Walk`
	local Crouching = Gait == `Crouch` or Gait == `Sneak`
	local LeadIn = Opt.LeadIn or 3.0
	local Arrive = Opt.Arrive or 0.35
	local BlendLead = Opt.BlendLead or 0.2
	local EaseOut = Opt.EaseOut ~= false
	local TurnMax = Opt.TurnMax or 20
	local Remote = ReplicatedStorage:FindFirstChild(`NHCine`)
	if Crouching and Hum:GetAttribute(`Crouch`) ~= true and Remote then
		Remote:FireServer({ Kind = `BeatCrouch`; On = true })
		local T0 = os.clock()
		while Hum:GetAttribute(`Crouch`) ~= true and os.clock() - T0 < 1 do RunService.Heartbeat:Wait() end
	end
	local Was = Hum.WalkSpeed
	local RotWas = Hum.AutoRotate
	-- (fix round 2) the legs keep step with the ground: Controllers.Character.AnimationController sets the live Walk / CrouchWalk /
	-- Sprint speed only on Humanoid.Running events, which lag a pace that changes every frame (the ramp, the turn slow-down, the ease-out:
	-- measured Walk at 0.95 against 0.39 wanted). While the approach drives you, the live locomotion track's speed is the root's flat
	-- speed over that clip's own stride (the game's scales: Walk 10, CrouchWalk 7, Sprint 24, FastSprint 30), written before each
	-- animation step
	local Animator = Hum:FindFirstChildOfClass(`Animator`)
	local CadConn = Animator and RunService.PreAnimation:Connect(function()
		if not Root.Parent then return end
		local Flat = flat(Root.AssemblyLinearVelocity).Magnitude
		for _, T in (Animator :: Animator):GetPlayingAnimationTracks() do
			local Per = T.Animation and STRIDE[T.Animation.Name]
			if Per and T.Priority == Enum.AnimationPriority.Core then T:AdjustSpeed(math.clamp(Flat / Per, 0.05, 2.5)) end
		end
	end) or nil
	local function cadOff() if CadConn then CadConn:Disconnect() CadConn = nil end end
	-- (fix round 2, m-3) what the wrapper puts back if this errors part way
	if State then State.Restore = function() cadOff() Hum:Move(Vector3.zero) Hum.WalkSpeed = Was Hum.AutoRotate = RotWas end end
	Hum.AutoRotate = true                                        -- (fix round 1, M4) the body turns with the walk, whatever the cut had set
	local Speed = if Gait == `Run` then RUN elseif Crouching then CROUCH
		else (if Was > 4 and Was < 20 then Was else WALK)           -- the walk speed the player has (hunger bands change it), the game's 12 otherwise
	local Face = flat(Mark.LookVector)
	Face = if Face.Magnitude > 1e-3 then Face.Unit else Vector3.new(0, 0, -1)
	local Goal = Vector3.new(Mark.Position.X, Root.Position.Y, Mark.Position.Z)
	do local G = groundBelow(Root.Position, Char) LastRise = if G then math.clamp(Root.Position.Y - G, 1, 6) else nil end
	local function headErr(): number return wrap(math.deg(yawOf(Face) - yawOf(Root.CFrame.LookVector))) end
	-- the settle: the heading left at the stop turns over the blend window, inside the next piece's fade-in, about where the root is now
	local function settle(Cap: number)
		local Turn = math.clamp(headErr(), -Cap, Cap)
		if math.abs(Turn) <= 1.5 then return end
		local MyGen, MyChain = Gen, ChainGen
		task.spawn(function()
			local Rot0 = Root.CFrame.Rotation
			local T1 = os.clock()
			local Dur = math.max(0.45, math.abs(Turn) / 45)                 -- never faster than about 45 degrees a second on average (peak 1.5x): a turn, not a spin
			while ChainGen == MyChain and Gen == MyGen and Root.Parent and Hum.Health > 0 do
				local A = math.min(1, (os.clock() - T1) / Dur)
				Root.CFrame = CFrame.new(Root.Position) * Rot0 * CFrame.Angles(0, math.rad(Turn) * A * A * (3 - 2 * A), 0)
				if A >= 1 then break end
				RunService.Heartbeat:Wait()
			end
		end)
	end
	-- (fix round 1, I4) already on the mark and nearly facing it: no walk (a lead-in from here is an out-and-back); the heading turns in the blend
	-- (fix round 2, m-4) only within TurnMax of its heading, and the turn is capped there like every other settle
	if (flat(Root.Position) - flat(Goal)).Magnitude <= (Opt.NearSkip or 0.5) and math.abs(headErr()) <= (Opt.NearTurn or TurnMax) then
		cadOff()
		Hum:Move(Vector3.zero)                                  -- (fix round 2, I-1) a walk handed on (the ease wait, Begin's re-issue) stops here
		Hum.AutoRotate = RotWas
		Hum.WalkSpeed = Was
		local Fn = Opt.OnNear
		if Fn then task.spawn(Fn, 0) end
		settle(math.min(Opt.NearTurn or TurnMax, TurnMax))
		return true, nil
	end
	local Lead = Goal - Face * LeadIn
	-- in line: facing within 30 degrees of the mark's heading and on the line running back from it (within 0.6 studs of it, behind the mark)
	local Off = flat(Root.Position - Goal)
	local Side = Face:Cross(Vector3.yAxis)
	local InLine = math.abs(wrap(math.deg(yawOf(Root.CFrame.LookVector) - yawOf(Face)))) < 30
		and Off:Dot(Face) < 0 and math.abs(Off:Dot(Side)) < 0.6
	local Legs = if InLine then { Goal } else { Lead, Goal }
	local Leg = 1
	local function remaining(): number
		local D = (flat(Legs[Leg]) - flat(Root.Position)).Magnitude
		for I = Leg + 1, #Legs do D += (flat(Legs[I]) - flat(Legs[I - 1])).Magnitude end
		return D
	end
	local Total = remaining()
	local Budget = Opt.Timeout or (3 + 2 * Total / Speed)
	local T0, Moved0 = os.clock(), os.clock()
	local Best = Total
	local Y0 = Root.Position.Y
	local Near = false
	local Replanned = false
	local Reason: string? = nil
	local Arrived = false
	-- (fix round 1, I2) the pace ramps up from the speed you already have (a walk that is handed on carries on; only a standing start eases in)
	local Up0 = math.clamp(math.max(V0.Magnitude, flat(Root.AssemblyLinearVelocity).Magnitude) / Speed, 0, 1)
	-- steering: the Humanoid is moved straight at the leg's point every frame (Hum:Move, world space). MoveTo was tried first and stops
	-- about a stud short of its point (it counts as arrived there) and gives up after 8 s, which left the walk stalled short of a
	-- lead-in; Move toward the point is exact, and AutoRotate turns the body along it
	-- the corner at the lead-in is rounded by pursuit: within CORNER studs of the lead-in the walk is on the final leg, steering at the point
	-- LOOK studs further along the lead-in -> mark line than where it has got to (a lead-in is a place to line up, not a corner to turn
	-- on: the camera framing you swings with your heading, so a sharp turn there swung it). The aim is always ahead of the root along the
	-- line, so it can't settle short of the mark
	local CORNER, LOOK = 1.5, 1.2
	local REPLAN = 45
	local Yaw, Spin, TurnAt, TurnPace = math.deg(yawOf(Root.CFrame.LookVector)), 0, os.clock(), 1
	local function steer()
		local P = flat(Root.Position)
		local Aim = flat(Legs[Leg])
		if Leg == #Legs and #Legs == 2 then
			local From, To = flat(Legs[1]), flat(Legs[2])
			local Line = To - From
			local Len = Line.Magnitude
			if Len > 1e-3 then
				local Dir = Line / Len
				local Along = math.clamp((P - From):Dot(Dir), 0, Len)
				Aim = From + Dir * math.min(Len, Along + LOOK)
			end
		end
		local Move = Aim - P
		if Move.Magnitude < 1e-3 then Hum:Move(Vector3.zero, false) return end
		-- the heading you walk is turned toward the aim with a limited rate (360 degrees a second) that builds up (1800 degrees a second
		-- squared): the camera framing you is relative to your heading, and a heading that snaps swings it. The body follows the move direction.
		-- A big turn slows the pace (TurnPace) so the turning circle stays small: at full pace a limited turn would orbit a mark close by.
		-- (fix round 1) only when the aim is that close: with room to turn (over 3 turning radii away) the pace keeps at least 90 %, so a walk
		-- handed on from a beat doesn't brake at the seam
		local Now = os.clock()
		local Dt = math.min(Now - TurnAt, 0.1)
		TurnAt = Now
		local Want = math.deg(yawOf(Move.Unit))
		local Err = wrap(Want - Yaw)
		local Rate = math.clamp(Err * 8, -360, 360)
		local Step = 1800 * Dt
		local TurnWant = math.clamp(1.15 - math.abs(Err) / 90, 0.2, 1)
		if Move.Magnitude > 3 * Speed / math.rad(360) then TurnWant = math.max(TurnWant, 0.9) end
		-- (fix round 2) on the way to the lead-in the corner is rounded by pursuit (CORNER), not stopped at: no need to brake below 75 % there
		if Leg < #Legs then TurnWant = math.max(TurnWant, 0.75) end
		-- (fix round 2) eased, at most 3 a second: a slow-down that snapped took the walk from 11 to under 5 studs/s in two frames, which no
		-- body does and which the leg cycle couldn't keep step with
		TurnPace += math.clamp(TurnWant - TurnPace, -3 * Dt, 3 * Dt)
		Spin += math.clamp(Rate - Spin, -Step, Step)
		Yaw = wrap(Yaw + Spin * Dt)
		local Dir = Vector3.new(-math.sin(math.rad(Yaw)), 0, -math.cos(math.rad(Yaw)))
		Hum:Move(Dir, false)
	end
	steer()
	while true do
		RunService.Heartbeat:Wait()
		if ChainGen ~= My then Reason = `released` break end
		if not (Hum.Parent and Root.Parent) or Hum.Health <= 0 then Reason = `died` break end
		if Root.Position.Y < Y0 - 8 then Reason = `fell` break end
		local Left = remaining()
		-- the pace: the gait's speed, eased up over 0.25 s from the speed you had (I2) and (EaseOut) down over the last stud to 35 % of it, so
		-- the camera that is framing you (the glide in tracks the root) never sees the root start or stop in one frame. Someone else writing the
		-- speed (the server's crouch, a sprint) is put back: this is the pace of the walk
		local Up = math.clamp((os.clock() - T0) / 0.25, 0, 1)
		local Ramp = Up0 + (1 - Up0) * Up * Up * (3 - 2 * Up)
		local Pace = Speed * math.max(0.15, Ramp) * (if Leg == #Legs and EaseOut then math.clamp(Left / 1.0, 0.35, 1) else 1) * TurnPace
		if math.abs(Hum.WalkSpeed - Pace) > 1e-3 then Hum.WalkSpeed = Pace end
		if Leg < #Legs then
			if (flat(Legs[Leg]) - flat(Root.Position)).Magnitude < CORNER then Leg += 1 Left = remaining() end
		else
			local Fn = Opt.OnLeft
			if Fn then Fn(Left) end
			local Stop = Opt.StopWhen
			if Stop and Stop() then Arrived = true break end
			-- arrived: within the stop radius, or the mark passed (a hitching frame stepped over it)
			local Rel = flat(Root.Position) - flat(Goal)
			if Left <= Arrive or (Rel:Dot(Face) > 0 and Left < 1.2) then Arrived = true break end
		end
		-- the time left at the pace profile still to come (fix round 1: the EaseOut slow-down over the last stud is counted, so OnNear's piece
		-- starts BlendLead before the stop, not up to 0.7 s before it with the legs still walking under a still pose)
		local function secondsLeft(): number
			local K = math.max(Pace, 0.05) / (if Leg == #Legs and EaseOut then math.clamp(Left / 1.0, 0.35, 1) else 1) -- the pace before the slow-down
			if not EaseOut then return math.max(0, Left - Arrive) / K end
			local T = math.max(0, Left - math.max(1, Arrive)) / K                 -- the stretch before the last stud
			local A, B = Arrive, math.min(Left, 1)
			if B > A then
				local C = math.max(A, 0.35)
				if C > A then T += (math.min(B, 0.35) - A) / (0.35 * K) end    -- under 0.35 studs: at 35 %
				if B > C then T += math.log(B / C) / K end                        -- from 0.35 to 1 stud: pace in proportion to the distance
			end
			return T
		end
		if not Near and Leg == #Legs and secondsLeft() <= BlendLead then
			-- (fix round 1, M1) a walk still heading far off the mark's heading as the stop nears (over REPLAN degrees: the body, turning
			-- with it, can't get within TurnMax by the stop) would end in a turn on the spot: keep steering instead, once more round the
			-- lead-in (the next piece hasn't started). The walk's own direction is judged, not the body's (the body lags it while it turns)
			local MoveErr = wrap(math.deg(yawOf(Face)) - Yaw)
			if math.abs(MoveErr) > REPLAN and not Replanned then
				Replanned = true
				warn(`[CineActor] Approach: walking {math.floor(math.abs(MoveErr))} degrees off the mark's heading as the stop nears: round the lead-in again`)
				Legs = { Goal - Face * LeadIn, Goal }
				Leg = 1
				Best = remaining()
				Moved0 = os.clock()
				Budget += 3 + 2 * Best / Speed
			else
				Near = true
				local Fn = Opt.OnNear
				if Fn then task.spawn(Fn, secondsLeft()) end
			end
		end
		steer()
		if Left < Best - 0.25 then Best = Left Moved0 = os.clock() end
		if os.clock() - Moved0 > 3 then Reason = `blocked` break end
		if os.clock() - T0 > Budget then Reason = `timeout` break end
	end
	cadOff()
	Hum:Move(Vector3.zero)                                      -- the Humanoid stops
	Hum.WalkSpeed = Was                                         -- (nothing else owns the speed during an approach)
	Hum.AutoRotate = RotWas
	if not Arrived then return false, Reason end
	-- whatever is left (AutoRotate got it within a few degrees) turns in the blend; never more than TurnMax on the spot
	if math.abs(headErr()) > TurnMax then
		warn(`[CineActor] Approach: arrived {math.floor(math.abs(headErr()))} degrees off the mark's heading: turning {TurnMax} in the blend, the rest stays`)
	end
	settle(TurnMax)
	return true, nil
end

-- the player attribute NHApproach is true while an approach drives the character (a player's held input keeps walking up to it: the
-- checks' scripted walker hands over on it the same way)
-- (fix round 2, m-2) a depth count: an approach that starts while another is still unwinding doesn't have its flag cleared under it
function Shared.Approach(Mark: CFrame, Opts: any?): (boolean, string?)
	ApproachDepth += 1
	Approaching = true
	Player:SetAttribute(`NHApproach`, true)
	local State = {}
	local Ok, Res, Why = pcall(approach, Mark, Opts, State)
	ApproachDepth -= 1
	Approaching = ApproachDepth > 0
	if not Approaching then Player:SetAttribute(`NHApproach`, nil) end
	if not Ok then
		warn(`[CineActor] Approach errored: {Res}`)
		if State.Restore then pcall(State.Restore) end           -- (fix round 2, m-3) speed, AutoRotate and the move put back
		return false, `error`
	end
	return Res, Why
end

-- The fallback when Approach can't arrive (blocked, timed out, fell): a short dip to black and the character is placed on the mark
-- (position and heading), with a warning. Black first, then the move, so nothing is seen to jump. The token rules are CineUI.Dip's
-- own (a newer veil claim wins; if black isn't reached, a second short dip of its own hides the move).
-- (fix round 1, I3) nothing is placed for "died", "released" or "nochar" (returns false: the caller doesn't start its chain either). The
-- height is the ground under the mark plus the root's height over the ground when the walk began (a fall kept the fallen height).
-- (M2) Alive (optional, the cut's Ctx.Alive) is asked again inside the dip, the nested one too: a cut that ended meanwhile places nothing.
function Shared.Fallback(Mark: CFrame, Why: string?, Alive: (() -> boolean)?): boolean
	if Why == `died` or Why == `released` or Why == `nochar` then return false end
	warn(`[CineActor] Approach fell back to a dip and a placement ({Why or `unknown`})`)
	local Char, Hum, Root = parts()
	if not (Char and Hum and Root) or Hum.Health <= 0 then return false end
	local function live(): boolean
		return Root.Parent ~= nil and Hum.Health > 0 and (Alive == nil or Alive())
	end
	local function place()
		if not live() then return end
		local G = groundBelow(Mark.Position, Char, 1)
		local Y = if G then G + (LastRise or (Root.Size.Y / 2 + (if Hum.RigType == Enum.HumanoidRigType.R6 then 2 else Hum.HipHeight))) else Mark.Position.Y
		if not G and Why ~= `fell` then Y = Root.Position.Y end           -- no ground found under the mark: a walk that was blocked keeps its height
		Root.CFrame = CFrame.new(Mark.X, Y, Mark.Z) * (Mark - Mark.Position)
		Root.AssemblyLinearVelocity = Vector3.zero
	end
	local Ok, CineUI = pcall(function() return require(Player.PlayerScripts.Controllers.Gui.CineUI) end)
	if not Ok then place() return live() end
	pcall(CineUI.Dip, 0.3, function(Black: boolean?)
		if not live() then return end
		if Black == false then pcall(CineUI.Dip, 0.2, place) else place() end
	end)
	return live()
end

-- the old name: a walk to a mark on foot, with no distance limit and no turn on the spot
function Shared.WalkTo(Mark: CFrame, _MaxStuds: number?): boolean
	return (Shared.Approach(Mark, { Gait = `Walk` }))
end

-- Preload (task 14): the chain's every piece and _End pose, fetched before they are needed (the published clips load over the
-- network: a cold first piece has Length 0 and shows only the live locomotion/idle until it arrives, and with the first piece
-- fading in from the approach that would read as a dead idle). A cut calls it at its start, long before the approach ends; Chain
-- waits for it (bounded at 3 s). Safe to call twice: the second call waits on the first.
local Warm: { [string]: boolean } = {}
local Warming: { [string]: boolean } = {}
function Shared.Preload(Chain: string, Resolve: (string) -> string?)
	if Warm[Chain] then return end
	if Warming[Chain] then
		local T0 = os.clock()
		while not Warm[Chain] and os.clock() - T0 < 3 do task.wait() end
		return
	end
	Warming[Chain] = true
	local TA = require(ReplicatedStorage.Config.TutorialAnim)
	-- loaded through the Animator, which is what fetches a published clip (ContentProvider:PreloadAsync sat on them for 3 s+): a track's
	-- Length goes above 0 once its clip is in, and the later LoadAnimation of the same id finds it cached
	local _, _, _, Animator = parts()
	local Loaded: { AnimationTrack } = {}
	local Anims: { Animation } = {}
	if Animator then
		for _, P in TA.Chains[Chain] or {} do
			for _, Name in { P.Piece, P.Piece .. `_End` } do
				local Id = Resolve(Name)
				if Id and Id ~= `` then
					local A = Instance.new(`Animation`)
					A.AnimationId = Id
					table.insert(Anims, A)
					table.insert(Loaded, Animator:LoadAnimation(A))
				end
			end
		end
	end
	local T1 = os.clock()
	local function pending(): boolean
		for _, T in Loaded do if T.Length == 0 then return true end end
		return false
	end
	while pending() and os.clock() - T1 < 3 do task.wait() end    -- bounded: a clip that never arrives must not hold the cut
	if pending() then warn(`[CineActor] Preload {Chain}: not every clip had loaded after 3 s`) end
	for _, T in Loaded do T:Destroy() end
	for _, A in Anims do A:Destroy() end
	Warm[Chain] = true
	Warming[Chain] = nil
end

-- Plays the chain and yields until it ends: its last piece is then held on its final (settled) frame until Reseat or
-- Release. Returns the tracks. Opts.FadeIn (seconds, default 0.4) is the FIRST piece's fade-in from whatever is showing (the live
-- locomotion pose after an Approach: 0.2 to 0.3 s); the later pieces switch instantly, exactly as before. Opts.Entry (a number, or a function
-- asked right before the first piece plays) is the phase a first LOOP piece enters at, so a cut can land the loop's exit on a beat.
-- (fix round 1, I1) Opts.Pace (a function) is the first piece's playback speed, asked every frame until the second piece starts: a first
-- piece that is a walk cycle (FenceOver1_GameCrouchWalk) is driven at the live walk's own speed, so its legs move exactly as far as the
-- root does and stop when it stops (a walk cycle played at speed 1 after the root stopped was a walk on the spot).
function Shared.Chain(Chain: string, Resolve: (string) -> string?, Cues: any?, OnSwitch: ((string) -> ())?, Opts: { FadeIn: number?, Entry: (number | () -> number?)?, Pace: (() -> number)? }?): { [string]: AnimationTrack }
	local _, _, _, Animator = parts()
	assert(Animator, `no Animator`)
	local TA = require(ReplicatedStorage.Config.TutorialAnim)
	local FadeIn = math.max(0.05, (Opts and Opts.FadeIn) or 0.4)
	Shared.Preload(Chain, Resolve)
	-- the first piece eases in over FadeIn (smootherstep weight 0 -> 1, written each frame) so the arms don't snap from the
	-- game's idle to the chain's pose; this is a blend. Later switches are identical frames and stay instant.
	local First = true
	local Second = false
	local Pace = Opts and Opts.Pace
	local function switched(Piece: string)
		if not First then Second = true end
		if First then
			First = false
			local Id = Resolve(Piece)
			for _, T in Animator:GetPlayingAnimationTracks() do
				if T.Animation and T.Animation.AnimationId == Id then
					if Pace then
						local PaceFn = Pace
						T:AdjustSpeed(PaceFn())
						local PConn: RBXScriptConnection
						PConn = RunService.PreAnimation:Connect(function()
							if Second or not T.IsPlaying then PConn:Disconnect() return end
							T:AdjustSpeed(PaceFn())
						end)
					end
					T:AdjustWeight(0.001, 0)
					local T0 = os.clock()
					local Conn: RBXScriptConnection
					Conn = RunService.PreAnimation:Connect(function()
						local A = math.min(1, (os.clock() - T0) / FadeIn)
						T:AdjustWeight(math.max(0.001, A * A * A * (A * (A * 6 - 15) + 10)), 0)
						if A >= 1 then Conn:Disconnect() end
					end)
					break
				end
			end
		end
		if OnSwitch then OnSwitch(Piece) end
	end
	local My = ChainGen
	local Entry = Opts and Opts.Entry
	if typeof(Entry) == `function` then Entry = Entry() end
	local Tracks = TA.Play(Animator, Chain, Resolve, Cues, switched, function() return ChainGen ~= My end, Entry :: number?)
	if ChainGen ~= My then return Tracks end                -- released while it ran: Play stopped its tracks (Stop(0))
	-- (final fix round) a second Chain must not leave the first one's held tracks playing, unreachable, once their table is overwritten
	local Fresh = {}
	for _, T in Tracks do Fresh[T] = true end
	for _, Old in ChainTracks or {} do
		if not Fresh[Old] and Old.IsPlaying then Old:Stop(0) end
	end
	ChainTracks = Tracks
	return Tracks
end

-- the _End track (and its Animation) held after a re-seat, or still waiting for its step; and the last chain's tracks
local function drop(Track: AnimationTrack?, Anim: Animation?, Fade: number)
	if Track then
		Track:Stop(Fade)
		task.delay(Fade + 0.1, function() Track:Destroy() end)
	end
	if Anim then task.delay(Fade + 0.1, function() Anim:Destroy() end) end
end

-- The re-seat. The chain's last piece has played to its end and is held still (build.py settles it; TutorialAnim.Play
-- freezes it); its _End clip is that same final pose with the ground offset and heading taken out, as two identical
-- keyframes. So this switches a still pose to an identical still pose: the _End track is played (Action4, speed 0, so it
-- can't advance and fall to idle even through a frame hitch) on a Heartbeat; a played track's pose is first drawn by the
-- NEXT step's animation, and that step's PreSimulation (after the animation, before render) writes the root, so the pose
-- and the root change in one engine step. The chain's tracks (outranked by Action4) are stopped after it.
-- Returns true once the root has moved. Returns false, and changes nothing, if `<Piece>_End` doesn't resolve or the
-- character is missing; false too if a Release (or another Reseat) cancelled it before it landed.
function Shared.Reseat(Piece: string, Offset: { X: number, Z: number, Yaw: number }, Resolve: (string) -> string?): boolean
	local Char, _, Root, Animator = parts()
	if not (Char and Root and Animator) then return false end
	local Id = Resolve(Piece .. `_End`)
	if not Id or Id == `` then return false end
	Gen += 1
	local My = Gen
	if Pending then drop(Pending, PendingAnim, 0) Pending, PendingAnim = nil, nil end -- an earlier Reseat still in flight
	local A = Instance.new(`Animation`)
	A.AnimationId = Id
	local T = Animator:LoadAnimation(A)
	T.Priority = Enum.AnimationPriority.Action4
	T.Looped = true                                         -- belt and braces: two identical keyframes, speed 0
	Pending, PendingAnim = T, A
	-- (final fix round) a clip still loading has Length 0: give it up to 3 s (the re-seat holds the chain's last pose meanwhile)
	local Wait0 = os.clock()
	while T.Length == 0 and Gen == My and os.clock() - Wait0 < 3 do task.wait() end
	local Thread = coroutine.running()
	local Moved = false
	local function cancel()
		if Pending == T then Pending, PendingAnim = nil, nil end
		drop(T, A, 0)
		task.spawn(Thread)
	end
	RunService.Heartbeat:Once(function()
		if Gen ~= My then cancel() return end
		if EndTrack then drop(EndTrack, EndAnim, 0) EndTrack, EndAnim = nil, nil end -- a second Reseat replaces the first's hold (same priority: never two at once)
		T:Play(0, 1, 0)
		RunService.PreSimulation:Once(function()
			if Gen ~= My or not T.IsPlaying or not Root.Parent then cancel() return end
			-- (final fix round) a track that never loaded (an unpublished clip: PreviewId resolves only in Studio) has Length 0 and draws no
			-- pose: moving the root by EndOffset would pop the character with nothing to hide it, so the re-seat doesn't happen
			if T.Length == 0 then
				warn(`[CineActor] Reseat {Piece}: its _End track has Length 0 (clip not loaded or not published): root left where it is`)
				cancel()
				return
			end
			-- EndOffset is in the clip's units; the Animator scales a Pose's translation by the character's scale (Model:ScaleTo,
			-- e.g. 1.0296 for this avatar), so the ground offset is scaled the same way (unscaled it left a 0.03 x 1.4 = 4 cm step)
			local S = (Char :: Model):GetScale()
			Root.CFrame = Root.CFrame * CFrame.new(Offset.X * S, 0, Offset.Z * S) * CFrame.Angles(0, math.rad(Offset.Yaw), 0)
			Moved = true
			Pending, PendingAnim = nil, nil
			EndTrack, EndAnim = T, A
			for _, Other in ChainTracks or {} do
				if Other.IsPlaying then Other:Stop(0) end
			end
			ChainTracks = nil
			task.spawn(Thread)
		end)
	end)
	coroutine.yield()
	return Moved
end

-- Release wins over a Reseat in flight (the Skip path): it bumps the token, so the pending Reseat's next step stops and
-- destroys its _End track without moving the root; nothing is left held. The held _End (or, without a re-seat, the
-- chain's held last piece) fades out over 0.25 s and the game's idle/walk blends back in (spec §2.2).
function Shared.Release()
	Gen += 1
	ChainGen += 1                                           -- a Chain still running stops its tracks at its next step
	if Pending then drop(Pending, PendingAnim, 0) Pending, PendingAnim = nil, nil end
	if EndTrack then drop(EndTrack, EndAnim, 0.25) EndTrack, EndAnim = nil, nil end
	for _, Other in ChainTracks or {} do
		if Other.IsPlaying then Other:Stop(0.25) end
	end
	ChainTracks = nil
	local Ctl = controls()
	if Ctl then Ctl:Enable() end
	Held = false
end

function Shared.OnStart() end

return Shared
