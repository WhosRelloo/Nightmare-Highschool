--!strict
--[[
	CineActor (client). StarterPlayer.StarterPlayerScripts.Controllers.CineActor   (2.35.0, spec 2026-11-20 §2)
	The player's own character as a seamless cut's actor: input eases out, it walks to marks (never a teleport), it plays
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
	local _, Hum = parts()
	if Hum then
		SpeedWas = Hum.WalkSpeed
		local T0, S0 = os.clock(), Hum.WalkSpeed
		while os.clock() - T0 < 0.3 do                       -- input eases out (spec §2.1): 0.3 s
			Hum.WalkSpeed = S0 * (1 - (os.clock() - T0) / 0.3)
			RunService.Heartbeat:Wait()
		end
		Hum.WalkSpeed = SpeedWas :: number
	end
	local Ctl = controls()
	if Ctl then Ctl:Disable() end
end

function Shared.WalkTo(Mark: CFrame, MaxStuds: number?): boolean
	local _, Hum, Root = parts()
	if not (Hum and Root) then return false end
	local Goal = Mark.Position + Vector3.new(0, Root.Position.Y - Mark.Position.Y, 0)
	local Dist = (Goal - Root.Position) * Vector3.new(1, 0, 1)
	if Dist.Magnitude > (MaxStuds or 4) then return false end
	if Dist.Magnitude > 0.25 then
		Hum:MoveTo(Goal)
		local T0 = os.clock()
		while ((Goal - Root.Position) * Vector3.new(1, 0, 1)).Magnitude > 0.35 and os.clock() - T0 < 3 do RunService.Heartbeat:Wait() end
		Hum:Move(Vector3.zero)
	end
	-- turn to the mark's heading over 0.35 s
	local From = Root.CFrame
	local To = CFrame.new(Root.Position) * (Mark - Mark.Position)
	local T0 = os.clock()
	while os.clock() - T0 < 0.35 do
		local A = (os.clock() - T0) / 0.35
		Root.CFrame = From:Lerp(To, A * A * (3 - 2 * A))
		RunService.Heartbeat:Wait()
	end
	Root.CFrame = To
	return true
end

-- Plays the chain and yields until it ends: its last piece is then held on its final (settled) frame until Reseat or
-- Release. Returns the tracks.
function Shared.Chain(Chain: string, Resolve: (string) -> string?, Cues: any?, OnSwitch: ((string) -> ())?): { [string]: AnimationTrack }
	local _, _, _, Animator = parts()
	assert(Animator, `no Animator`)
	local TA = require(ReplicatedStorage.Config.TutorialAnim)
	-- the first piece eases in over 0.4 s (smootherstep weight 0 -> 1, written each frame) so the arms don't snap from the
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
						local A = math.min(1, (os.clock() - T0) / 0.4)
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
	local Tracks = TA.Play(Animator, Chain, Resolve, Cues, switched, function() return ChainGen ~= My end)
	if ChainGen ~= My then return Tracks end                -- released while it ran: Play stopped its tracks (Stop(0))
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
