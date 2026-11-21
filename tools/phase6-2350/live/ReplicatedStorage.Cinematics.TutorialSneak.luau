--[[
	TutorialSneak (doc 15 §5 beat 2). Seamless walk-and-talk: you crouch across the back garden past Biscuit's kennel
	(Follow rig, Biscuit kept in frame) with the game's own Crouch / CrouchWalk. Stand up near him (within 8 studs) and he
	gives one bored "wuff" and wakes, the bedroom light flicks on and you have to crouch and wait (the soft fail: the Hide
	beat, until he sighs and the light goes off). Reach the fence (the gate) and a short seamless cut plays the FenceOver
	chain, then control comes straight back on the far side. Set Garden (tools/phase6-2350/stage/hometown.lua).

	Biscuit is the player's own copy (Controllers.Hometown.Cast; Wickfield is private), and the rig only lays out right while
	a clip plays, so a BASE LOOP is always playing on him: BiscuitSleep from the moment the copy exists (Hometown casts him
	and starts the loop as soon as NHTutorial is set, long before this cut; Build only starts it if it isn't already
	playing), with Wuff / WakeStare / Sigh played over it (Action priority). A clip that ends fades out to the sleep
	loop; WakeStare is held on its last frame until the Sigh. Every track the cut loads is stopped and destroyed when the cut
	ends (Ctx.OnEnd), except the sleep loop itself, which keeps him laid out for as long as he's in the garden. Outside Wickfield (Cast nil: a lint run) nothing of the shared WFBiscuit is touched.

	The fence (ruling C1): FenceOver2 is a vault whose own root motion is 1.56 studs sideways (-X of the root) and 0.43
	forward, ending turned 100 degrees (measured in Play against the clip's data: the EndOffset is not a mis-measure, the clip is
	simply a vault in place). So the cut squares you up to FenceZone (position AND heading: turned 40 degrees left of the fence
	so the clip's first frame, which faces 40 degrees right of its root, faces the fence), and at the top of the climb, under a
	short dip, moves your root to the far-side mark FenceLand (less the clip's own EndOffset, so the re-seat at the end of the clip
	lands exactly on it, facing away from the house).

	The crouch is the game's own (CineBeat: move.crouch -> BeatCrouch). Beat to beat and beat to fence it is handed on
	(ends.keepCrouch), so the player isn't stood up and crouched again between them; the FenceOver chain starts on the
	game's own crouch walk, and the stand-up happens as its climb starts (FenceOver2), under the chain's pose.
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local TweenService = game:GetService(`TweenService`)
local Config = require(ReplicatedStorage.Config.Cine)
local Def = { Set = `Garden`; Seamless = true }
-- (fix round 1, C1) FenceOver2's first frame faces 40 degrees to the right of its root (measured in Play: torso heading -40 as the
-- piece starts), so the root squares up turned 40 degrees left of the fence's heading and the body faces the fence
local APPROACH_YAW = 40
local FENCE_DUR = 6.1        -- the square-up, the chain and the re-seat end 5.47 s in (measured, checks/sneakcheck.lua timeline), plus a beat; was 7.0 with 1.5 s dead
local DIP_AT = 0.75          -- seconds into FenceOver2: the dip reaches black at its top (about 0.9 s)

function Def.Build(Ctx)
	local Player = Players.LocalPlayer
	local Ctl = Player.PlayerScripts:FindFirstChild(`Controllers`)
	local Home = Ctl and require(Ctl.Hometown) or nil
	local Actor = Ctl and require(Ctl.CineActor) or nil
	local Remote = ReplicatedStorage:FindFirstChild(`NHCine`)
	local Own = Home and Home.Cast(`WFBiscuit`) or nil -- the player's own Biscuit (nil outside Wickfield: never the shared one)
	local Light = Ctx.Prop(`BedroomLight`, { Size = Vector3.new(2.1, 1.3, 0.1); CFrame = Ctx.CF(`LightWindow`);
		Color = Color3.fromRGB(255, 210, 140); Material = Enum.Material.Neon; Transparency = 1 })
	local Built = { start = `Garden`; Fails = 0; Armed = false }
	Built.grade = Config.Looks.Night

	---| Biscuit's clips: Sleep is the base loop, the rest play over it |---
	local Controller = Own and Own:FindFirstChildWhichIsA(`AnimationController`, true)
	local Animator: Animator? = Own and Own:FindFirstChildWhichIsA(`Animator`, true) or nil
	if Own and not Animator and Controller then
		Animator = Instance.new(`Animator`)
		Animator.Parent = Controller
	end
	local Tracks: { AnimationTrack } = {}
	local Anims: { Animation } = {}
	local function load(Name: string): AnimationTrack?
		local Id = Ctx.Clip(Name)
		if not (Animator and Id and Ctx.Alive()) then return nil end
		local A = Instance.new(`Animation`)
		A.AnimationId = Id
		local T = Animator:LoadAnimation(A)
		table.insert(Anims, A)
		table.insert(Tracks, T)
		return T
	end
	local function loaded(T: AnimationTrack)
		local T0 = os.clock()
		while T.Length == 0 and os.clock() - T0 < 3 do task.wait() end
		return T.Length > 0
	end
	local Over: AnimationTrack? = nil -- the clip over the sleep loop right now
	local function over(Name: string, Hold: boolean?)
		local T = load(Name)
		if not T then return end
		T.Priority = Enum.AnimationPriority.Action
		T.Looped = false
		T:Play(0.2)
		local Prev = Over
		Over = T
		if Prev then Prev:Stop(0.2) end
		task.spawn(function()
			if not loaded(T) then return end
			if Hold then
				-- hold the last frame: a clip that ends would fade to the sleep loop
				local Conn: RBXScriptConnection
				Conn = RunService.PreAnimation:Connect(function(Dt: number)
					if Over ~= T or not T.IsPlaying then Conn:Disconnect() return end
					if T.TimePosition + 1.25 * Dt >= T.Length then
						Conn:Disconnect()
						T:AdjustSpeed(0)
						T.TimePosition = math.max(0, T.Length - 1 / 60)
					end
				end)
			else
				-- near its end it fades out and the sleep loop shows through
				while Ctx.Alive() and Over == T and T.IsPlaying and T.TimePosition < T.Length - 0.25 do task.wait() end
				if Over == T then Over = nil T:Stop(0.25) end
			end
		end)
	end
	-- the base loop outlives the cut: Biscuit stays in the garden after it, and with no clip his rig falls to its bare pose. It
	-- dies with the cast copy (Hometown destroys the cast when NHTutorial clears). A replay finds it still playing and reuses it
	local Sleep: AnimationTrack? = nil
	if Own and Animator then
		local SleepId = Ctx.Clip(`BiscuitSleep`)
		for _, T in Animator:GetPlayingAnimationTracks() do
			if T.Animation and T.Animation.AnimationId == SleepId then Sleep = T end
		end
		if not Sleep then
			Sleep = load(`BiscuitSleep`)
			if Sleep then
				table.remove(Tracks, table.find(Tracks, Sleep) :: number) -- not cleaned up with the cut
				table.remove(Anims, #Anims)
				Sleep.Priority = Enum.AnimationPriority.Movement
				Sleep.Looped = true
				Sleep:Play(0)
				loaded(Sleep) -- the first frame the cut shows already has him asleep, not in his bare rig pose
			end
		end
	end
	Ctx.OnEnd(function()
		-- (fix round 1, I2) the crouch the Garden beat handed on to the Fence cut ends with the cut, however it ends (a skip, the
		-- timeout, a leave) before FenceOver2 stands it; the server ignores this if nothing is crouched by a beat
		if Remote then Remote:FireServer({ Kind = `BeatCrouch`; On = false }) end
		for _, T in Tracks do pcall(function() T:Stop(0) T:Destroy() end) end
		for _, A in Anims do pcall(function() A:Destroy() end) end
		table.clear(Tracks)
		table.clear(Anims)
		Over = nil
	end)

	-- (fix round 2) a Skip or a timeout before the dip would leave you on the house side of a fence you can't cross (and a resumed
	-- run, after a rejoin, can skip): the end state is the far side. Placed at full black inside the skip's own dip, and only if
	-- no newer cut has started (the director checks). A Leave (Aborted) doesn't move you: Hometown's cleanup owns that
	Ctx.OnBlack(function(How: string, Black: boolean?)
		if How ~= `Skipped` and How ~= `Timeout` then return end
		local Land = Ctx.Mark(`FenceLand`)
		local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
		if not (Land and Root) then return end
		local function place()
			Root.CFrame = CFrame.new(Land.Position.X, Root.Position.Y, Land.Position.Z) * (Land.CFrame - Land.Position)
			Root.AssemblyLinearVelocity = Vector3.zero
		end
		-- (final fix round) the screen isn't black (a newer lift won): never a visible jump, hide it under a short dip of its own
		if Black == false then pcall(require(Player.PlayerScripts.Controllers.Gui.CineUI).Dip, 0.3, place) else place() end
	end)

	local function lamp(On: boolean)
		TweenService:Create(Light, TweenInfo.new(if On then 0.25 else 0.6), { Transparency = if On then 0 else 1 }):Play()
	end
	local function standing(): boolean
		local Hum = Player.Character and Player.Character:FindFirstChildOfClass(`Humanoid`)
		return Hum ~= nil and Hum:GetAttribute(`Crouch`) ~= true
	end

	Built.cues = {
		-- a beat's first moments are for the server's crouch to land; a stand-up only counts once the beat is armed
		Disarm = function() Built.Armed = false end;
		Arm = function() Built.Armed = true end;
		-- asked every quarter second while you're within 8 studs: only standing up (deliberately) wakes him
		BiscuitWakes = function()
			if not (Own and Built.Armed and not Built.Fail and standing()) then return end
			Built.Fails += 1
			Built.Fail = true
			pcall(require(Player.PlayerScripts.Controllers.Gui.CineUI).Subtitle, `Biscuit`, `Wuff.`, 1.5)
			over(`BiscuitWuff`)
			lamp(true)
		end;
		BiscuitStares = function() over(`BiscuitWakeStare`, true) end;
		BiscuitSighs = function()
			over(`BiscuitSigh`)
			lamp(false)
		end;
	}
	Built.segments = {
		Garden = { beat = {
			rig = `Follow`; frame = { also = `Biscuit`; lens = 35; low = true };
			move = { speed = 1; sprint = false; crouch = true }; -- (fix round 2) the game's own crouch speed (7): a scale under it makes CrouchWalk foot-slide
			lines = { { on = `start`; who = `You`; text = function()
				return if Built.Fails > 0 then `Still asleep. Probably.` else `Okay. Quiet. Very quiet.`
			end } };
			cues = {
				{ on = `start`; run = `Disarm` };
				{ on = `t:1.5`; run = `Arm` };
				{ on = `near:Biscuit:8`; run = `BiscuitWakes`; every = 0.25 };
			};
			ends = {
				{ on = `fail`; next = `Hide`; keepCrouch = true };
				{ on = `enter:FenceZone`; next = `Fence`; keepCrouch = true };
			};
		} };
		Hide = { beat = {
			rig = `Frame`; frame = { also = `LightWindow`; lens = 40 };
			move = { speed = 0; crouch = true };
			lines = { { on = `start`; who = `You`; text = `Don't. Move.` } };
			cues = {
				{ on = `t:1.7`; run = `BiscuitStares` };
				{ on = `t:6.0`; run = `BiscuitSighs` };
			};
			ends = { on = `t:7.2`; next = `Garden`; keepCrouch = true };
		} };
		Fence = { shots = {
			-- a fixed camera on the fence (the chain's re-seat moves your root and turns it in one frame, so a shot framed on you
			-- would jump with it): three-quarter from behind on the right, looking at the fence, wide enough to take the far side
			-- (where you land). No depth of field: the Garden beat has none, so one that switches on with these shots would pop
			-- (the director carries a beat's grade and bloom into the shots, not a DOF). The shot is the square-up, the chain
			-- (about 5.5 s) and the re-seat, plus a beat (fix round 1, M4)
			{ name = `Over the fence`; dur = FENCE_DUR; subject = Ctx.Mark(`FenceZone`); noise = `tense`; dof = false;
			  -- (task 12 fix round 1, motion ruling) a moving hold, not a locked camera: a slow push in (about 1.7 studs over the shot) with
			  -- the aim drifting a little toward where you land; level horizon (keys carry no roll). Fixed in the world, so the chain's
			  -- re-seat still can't move it
			  camera = { lens = 36; ease = `inout`; path = `linear`; keys = {
				{ t = 0; pos = Ctx.CF(`FenceZone`):PointToWorldSpace(Vector3.new(5.5, 2.6, 6.0)); look = Ctx.CF(`FenceZone`):PointToWorldSpace(Vector3.new(0, 2.4, -2.4)) };
				{ t = FENCE_DUR; pos = Ctx.CF(`FenceZone`):PointToWorldSpace(Vector3.new(4.5, 2.5, 4.7)); look = Ctx.CF(`FenceZone`):PointToWorldSpace(Vector3.new(-0.2, 2.4, -3.0)) };
			  } } };
		}; events = { { t = 0; call = function()
			if not Actor then return end
			local Char = Player.Character
			local Root = Char and Char:FindFirstChild(`HumanoidRootPart`) :: BasePart?
			if not (Char and Root) then return end
			-- square up to the fence over 0.35 s: position AND heading (you're already in the zone, up to 2 studs off it; CineActor
			-- WalkTo would wait out its 3 s for a point the Humanoid's MoveTo stops about a stud short of)
			local Zone = Ctx.CF(`FenceZone`)
			local From = Root.CFrame
			local To = CFrame.new(Zone.X, From.Y, Zone.Z) * (Zone - Zone.Position) * CFrame.Angles(0, math.rad(APPROACH_YAW), 0)
			local T0 = os.clock()
			while Ctx.Alive() and os.clock() - T0 < 0.35 do
				local A = (os.clock() - T0) / 0.35
				Root.CFrame = From:Lerp(To, A * A * (3 - 2 * A))
				RunService.Heartbeat:Wait()
			end
			if not Ctx.Alive() then return end
			Root.CFrame = To
			Root.AssemblyLinearVelocity = Vector3.zero
			local TA = require(ReplicatedStorage.Config.TutorialAnim)
			local Offset = TA.Chains.FenceOver[2].EndOffset
			-- the re-seat's own root move (CineActor.Reseat writes this); the far side is placed so it lands on FenceLand
			local S = Char:GetScale()
			local Seat = CFrame.new(Offset.X * S, 0, Offset.Z * S) * CFrame.Angles(0, math.rad(Offset.Yaw), 0)
			local LandMark = Ctx.Mark(`FenceLand`)
			if not LandMark then warn(`[Cine] TutorialSneak: no FenceLand mark in the Garden set: the climb lands where the clip's own motion does`) end
			Actor.Chain(`FenceOver`, Ctx.Clip, nil, function(Piece: string)
				if Piece ~= `FenceOver2` then return end
				-- the climb starts: the game's crouch ends under the chain's own pose
				if Remote then Remote:FireServer({ Kind = `BeatCrouch`; On = false }) end
				-- and at the top of it (about 0.9 s in) the root moves to the far side under a 0.3 s dip to black
				if LandMark then
					task.delay(DIP_AT, function()
						if not Ctx.Alive() then return end
						local CineUI = require(Player.PlayerScripts.Controllers.Gui.CineUI)
						local function place()
							if not Ctx.Alive() or not Root.Parent then return end
							local Land = LandMark.CFrame
							Root.CFrame = CFrame.new(Land.X, Root.Position.Y, Land.Z) * (Land - Land.Position) * Seat:Inverse()
							Root.AssemblyLinearVelocity = Vector3.zero
						end
						-- (final fix round) only at real black; if a newer lift won, the move waits for a fresh short dip of its own
						pcall(CineUI.Dip, 0.3, function(Black: boolean?)
							if Black == false then pcall(CineUI.Dip, 0.2, place) else place() end
						end)
					end)
				end
			end)
			if Ctx.Alive() then Actor.Reseat(`FenceOver2`, Offset, Ctx.Clip) end
		end } } };
	}
	return Built
end

return Def
