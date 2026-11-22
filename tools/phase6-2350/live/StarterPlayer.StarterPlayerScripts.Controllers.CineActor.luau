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
	if Ctl then Ctl:Disable() end
end

local function flat(V: Vector3): Vector3 return Vector3.new(V.X, 0, V.Z) end
local function yawOf(V: Vector3): number return math.atan2(-V.X, -V.Z) end -- 0 = facing -Z, positive = left
local function wrap(Deg: number): number return (Deg + 540) % 360 - 180 end

-- Approach (task 14, owner request 2026-11-21). The character gets to a mark ON FOOT, with the game's own locomotion: the
-- Humanoid is driven (Move toward the waypoint every frame) at the gait's WalkSpeed and Controllers.Character.AnimationController plays Walk / Sprint /
-- CrouchWalk from its speed, so nothing here animates and nothing is placed. It arrives already facing the mark: a lead-in
-- waypoint LeadIn studs behind the mark along its facing is walked to first (skipped if the character is already within ~30 degrees
-- of the mark's facing and in line with it), then the last steps run straight at the mark and AutoRotate has the body facing along
-- them. The few degrees left at the stop turn over 0.45 s or more (45 degrees a second at most on average) while the next piece fades in (a turn inside the blend, never a spin).
-- Opts: Gait "Walk" | "Run" | "Crouch" | "Sneak" (Crouch and Sneak are the game's crouch: speed 7; the crouch is asked of the server if
-- it isn't up), LeadIn (3.0), Arrive (0.35 studs), BlendLead (0.2 s), OnNear(secondsLeft) (fires once, BlendLead before arrival, so the
-- caller can start the next piece's fade-in), Timeout (seconds; default from the distance).
-- Returns true on arrival. Otherwise false and a reason: "blocked" (no progress for 3 s), "timeout", "fell", "released" (Release ran) or
-- "nochar". The caller then dips to black and places the character (Shared.Fallback).
function Shared.Approach(Mark: CFrame, Opts: { Gait: string?, LeadIn: number?, Arrive: number?, BlendLead: number?, OnNear: ((number) -> ())?, Timeout: number? }?): (boolean, string?)
	local Opt = Opts or {}
	local Char, Hum, Root = parts()
	if not (Char and Hum and Root) then return false, `nochar` end
	local My = ChainGen
	if Easing then EaseOver = true end                          -- Begin's ease would slow a walking player to a stop first: end it now
	while Easing and ChainGen == My do RunService.Heartbeat:Wait() end -- (it writes the speed each frame)
	if ChainGen ~= My then return false, `released` end
	local Gait = Opt.Gait or `Walk`
	local Crouching = Gait == `Crouch` or Gait == `Sneak`
	local LeadIn = Opt.LeadIn or 3.0
	local Arrive = Opt.Arrive or 0.35
	local BlendLead = Opt.BlendLead or 0.2
	local Remote = ReplicatedStorage:FindFirstChild(`NHCine`)
	if Crouching and Hum:GetAttribute(`Crouch`) ~= true and Remote then
		Remote:FireServer({ Kind = `BeatCrouch`; On = true })
		local T0 = os.clock()
		while Hum:GetAttribute(`Crouch`) ~= true and os.clock() - T0 < 1 do RunService.Heartbeat:Wait() end
	end
	local Was = Hum.WalkSpeed
	local Speed = if Gait == `Run` then RUN elseif Crouching then CROUCH
		else (if Was > 4 and Was < 20 then Was else WALK)           -- the walk speed the player has (hunger bands change it), the game's 12 otherwise
	Hum.WalkSpeed = Speed
	local Face = flat(Mark.LookVector)
	Face = if Face.Magnitude > 1e-3 then Face.Unit else Vector3.new(0, 0, -1)
	local Goal = Vector3.new(Mark.Position.X, Root.Position.Y, Mark.Position.Z)
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
	local Reason: string? = nil
	local Arrived = false
	-- steering: the Humanoid is moved straight at the leg's point every frame (Hum:Move, world space). MoveTo was tried first and stops
	-- about a stud short of its point (it counts as arrived there) and gives up after 8 s, which left the walk stalled short of a
	-- lead-in; Move toward the point is exact, and AutoRotate turns the body along it
	-- the corner at the lead-in is rounded by pursuit: within CORNER studs of the lead-in the walk is on the final leg, steering at the point
	-- LOOK studs further along the lead-in -> mark line than where it has got to (a lead-in is a place to line up, not a corner to turn
	-- on: the camera framing you swings with your heading, so a sharp turn there swung it). The aim is always ahead of the root along the
	-- line, so it can't settle short of the mark
	local CORNER, LOOK = 1.5, 1.2
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
		-- A big turn slows the pace (TurnPace) so the turning circle stays small: at full pace a limited turn would orbit a mark close by
		local Now = os.clock()
		local Dt = math.min(Now - TurnAt, 0.1)
		TurnAt = Now
		local Want = math.deg(yawOf(Move.Unit))
		local Err = wrap(Want - Yaw)
		local Rate = math.clamp(Err * 8, -360, 360)
		local Step = 1800 * Dt
		TurnPace = math.clamp(1.15 - math.abs(Err) / 90, 0.2, 1)
		Spin += math.clamp(Rate - Spin, -Step, Step)
		Yaw = wrap(Yaw + Spin * Dt)
		local Dir = Vector3.new(-math.sin(math.rad(Yaw)), 0, -math.cos(math.rad(Yaw)))
		Hum:Move(Dir, false)
	end
	steer()
	while true do
		RunService.Heartbeat:Wait()
		if ChainGen ~= My then Reason = `released` break end
		if not (Hum.Parent and Root.Parent) or Hum.Health <= 0 then Reason = `fell` break end
		if Root.Position.Y < Y0 - 8 then Reason = `fell` break end
		local Left = remaining()
		-- the pace: the gait's speed, eased up over 0.25 s from the start and down over the last stud to 35 % of it, so the camera that is
		-- framing you (the glide in tracks the root) never sees the root start or stop in one frame. Someone else writing the speed (the
		-- server's crouch, a sprint) is put back: this is the pace of the walk
		local Up = math.clamp((os.clock() - T0) / 0.25, 0, 1)
		local Pace = Speed * math.max(0.15, Up * Up * (3 - 2 * Up)) * (if Leg == #Legs then math.clamp(Left / 1.0, 0.35, 1) else 1) * TurnPace
		if math.abs(Hum.WalkSpeed - Pace) > 1e-3 then Hum.WalkSpeed = Pace end
		if Leg < #Legs then
			if (flat(Legs[Leg]) - flat(Root.Position)).Magnitude < CORNER then Leg += 1 Left = remaining() end
		else
			-- arrived: within the stop radius, or the mark passed (a hitching frame stepped over it)
			local Rel = flat(Root.Position) - flat(Goal)
			if Left <= Arrive or (Rel:Dot(Face) > 0 and Left < 1.2) then Arrived = true break end
		end
		if not Near and Leg == #Legs and (Left - Arrive) / (Pace * 1.0) <= BlendLead then
			Near = true
			local Fn = Opt.OnNear
			if Fn then task.spawn(Fn, math.max(0, (Left - Arrive) / Pace)) end
		end
		steer()
		if Left < Best - 0.25 then Best = Left Moved0 = os.clock() end
		if os.clock() - Moved0 > 3 then Reason = `blocked` break end
		if os.clock() - T0 > Budget then Reason = `timeout` break end
	end
	Hum:Move(Vector3.zero)                                      -- the Humanoid stops
	Hum.WalkSpeed = Was                                         -- (nothing else owns the speed during an approach)
	if not Arrived then return false, Reason end
	-- the heading left at the stop (AutoRotate got it within a few degrees) turns over the blend window, inside the next piece's fade-in
	local Err = wrap(math.deg(yawOf(Face) - yawOf(Root.CFrame.LookVector)))
	if math.abs(Err) > 1.5 then
		task.spawn(function()
			local From = Root.CFrame
			local T1 = os.clock()
			local Dur = math.max(0.45, math.abs(Err) / 45)                 -- never faster than about 45 degrees a second on average (peak 1.5x): a turn, not a spin
			while os.clock() - T1 < Dur and ChainGen == My and Root.Parent do
				local A = (os.clock() - T1) / Dur
				Root.CFrame = From * CFrame.Angles(0, math.rad(Err) * A * A * (3 - 2 * A), 0)
				RunService.Heartbeat:Wait()
			end
		end)
	end
	return true, nil
end

-- The fallback when Approach can't arrive (blocked, timed out, fell): a short dip to black and the character is placed on the mark
-- (position and heading, root height kept), with a warning. Black first, then the move, so nothing is seen to jump. The token rules
-- are CineUI.Dip's own (a newer veil claim wins; if black isn't reached, a second short dip of its own hides the move).
function Shared.Fallback(Mark: CFrame, Why: string?)
	warn(`[CineActor] Approach fell back to a dip and a placement ({Why or `unknown`})`)
	local _, _, Root = parts()
	if not Root then return end
	local function place()
		if not Root.Parent then return end
		Root.CFrame = CFrame.new(Mark.X, Root.Position.Y, Mark.Z) * (Mark - Mark.Position)
		Root.AssemblyLinearVelocity = Vector3.zero
	end
	local Ok, CineUI = pcall(function() return require(Player.PlayerScripts.Controllers.Gui.CineUI) end)
	if not Ok then place() return end
	pcall(CineUI.Dip, 0.3, function(Black: boolean?)
		if Black == false then pcall(CineUI.Dip, 0.2, place) else place() end
	end)
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
function Shared.Chain(Chain: string, Resolve: (string) -> string?, Cues: any?, OnSwitch: ((string) -> ())?, Opts: { FadeIn: number?, Entry: (number | () -> number)? }?): { [string]: AnimationTrack }
	local _, _, _, Animator = parts()
	assert(Animator, `no Animator`)
	local TA = require(ReplicatedStorage.Config.TutorialAnim)
	local FadeIn = math.max(0.05, (Opts and Opts.FadeIn) or 0.4)
	Shared.Preload(Chain, Resolve)
	-- the first piece eases in over FadeIn (smootherstep weight 0 -> 1, written each frame) so the arms don't snap from the
	-- game's idle to the chain's pose; this is a blend. Later switches are identical frames and stay instant.
	local First = true
	local function switched(Piece: string)
		if First then
			First = false
			local Id = Resolve(Piece)
			for _, T in Animator:GetPlayingAnimationTracks() do
				if T.Animation and T.Animation.AnimationId == Id then
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
