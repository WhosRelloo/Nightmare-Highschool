--!strict
--[[
	CineActor (client). StarterPlayer.StarterPlayerScripts.Controllers.CineActor   (2.35.0, spec 2026-11-20 §2)
	The player's own character as a seamless cut's actor: input eases out, it walks to marks (never a teleport), it plays
	TutorialAnim chains over its normal Animate, and at the end its root is re-seated under the body on the same frame
	the _End pose takes over, so nothing moves; then the game's idle/walk blends back in.
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)

local Player = Players.LocalPlayer
local Shared = {}
local Held = false
local EndTrack: AnimationTrack? = nil
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

function Shared.Chain(Chain: string, Resolve: (string) -> string?, Cues: any?, OnSwitch: ((string) -> ())?)
	local _, _, _, Animator = parts()
	assert(Animator, `no Animator`)
	local TA = require(ReplicatedStorage.Config.TutorialAnim)
	-- the first piece eases in over 0.25 s (weight 0 -> 1) so the arms don't snap from the game's idle to the chain's pose;
	-- later switches are identical frames, so they stay instant (a fade there would show the rig's default pose)
	local First = true
	local function switched(Piece: string)
		if First then
			First = false
			local Id = Resolve(Piece)
			for _, T in Animator:GetPlayingAnimationTracks() do
				if T.Animation and T.Animation.AnimationId == Id then
					T:AdjustWeight(0.001, 0)
					task.spawn(function()
						local T0 = os.clock()
						while os.clock() - T0 < 0.25 do
							RunService.Heartbeat:Wait()
							T:AdjustWeight(math.max(0.001, (os.clock() - T0) / 0.25), 0)
						end
						T:AdjustWeight(1, 0)
					end)
					break
				end
			end
		end
		if OnSwitch then OnSwitch(Piece) end
	end
	return TA.Play(Animator, Chain, Resolve, Cues, switched)
end

function Shared.Reseat(Piece: string, Offset: { X: number, Z: number, Yaw: number }, Resolve: (string) -> string?)
	local _, _, Root, Animator = parts()
	if not (Root and Animator) then return end
	local A = Instance.new(`Animation`)
	A.AnimationId = Resolve(Piece .. `_End`) or ``
	local T = Animator:LoadAnimation(A)
	T.Priority = Enum.AnimationPriority.Action4
	-- the _End pose (offset taken out) takes over and the root moves under the body in the SAME rendered frame. A track's
	-- pose lands one engine step after :Play(), while a CFrame write lands at once; writing both in one step shows the
	-- root move for a frame (measured: 1.3 st jump, twice). So play, wait one Stepped, then move the root.
	T:Play(0)
	RunService.Stepped:Wait()
	Root.CFrame = Root.CFrame * CFrame.new(Offset.X, 0, Offset.Z) * CFrame.Angles(0, math.rad(Offset.Yaw), 0)
	for _, Other in Animator:GetPlayingAnimationTracks() do
		if Other ~= T and Other.Priority == Enum.AnimationPriority.Action then Other:Stop(0) end
	end
	EndTrack = T
end

function Shared.Release()
	if EndTrack then EndTrack:Stop(0.25) EndTrack = nil end -- the game's idle/walk blends back in (spec §2.2)
	local Ctl = controls()
	if Ctl then Ctl:Enable() end
	Held = false
end

function Shared.OnStart() end

return Shared
