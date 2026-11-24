--[[
	Soccer clips (client, soccer-2.0): which animation a Config.Sports.SoccerAnims slot plays, its timing data
	(Config.SoccerClips, written by tools/soccer2/bake/bake_soccer_clips.lua), and the dash that follows a clip's travel.
		Id(Slot) -> (id?, fier)   a published Id; in Studio the baked NHSoccerClips copy (registered); else Was; else nil.
		                          fier = the FIER clip plays (its timing data applies)
		Clip(Slot) -> data?       the slot's Config.SoccerClips.Clips entry
		Drive(Track, Clip, DashTime, Cap) -> (Rate, Time, t0, t1)   the clip through its travel window at the fitted rate
		DashPath(Root, Track, Clip, Dir, Dist, Rate, t0, t1, Time)  the mover's dash: Dist studs along Dir on the clip's curve
		Cancel()                  stops a running DashPath (a new dash takes over)
	Spec: docs/superpowers/specs/2026-11-24-soccer-2-0-design.md §2, §4.
]]
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local KeyframeSequenceProvider = game:GetService(`KeyframeSequenceProvider`)

local Config = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`Sports`))
local Anim = require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`SoccerAnim`))

local M = {}
local Data = nil :: any
local Temp = {} :: { [string]: string }
local Warned = {} :: { [string]: boolean }
local Token = 0

function M.Data(): any?
	if Data == nil then
		local Mod = ReplicatedStorage:FindFirstChild(`Config`) and ReplicatedStorage.Config:FindFirstChild(`SoccerClips`)
		local Ok, D = false, nil
		if Mod then Ok, D = pcall(require, Mod) end
		Data = if Ok and type(D) == `table` and type(D.Clips) == `table` then D else false
	end
	return Data or nil
end

function M.Clip(Slot: string): any?
	local E = Config.SoccerAnims[Slot]
	local D = M.Data()
	return if type(E) == `table` and E.Clip and D then D.Clips[E.Clip] else nil
end

function M.Id(Slot: string): (string?, boolean)
	local E = Config.SoccerAnims[Slot]
	if type(E) == `number` then return `rbxassetid://{E}`, false end
	if type(E) ~= `table` then return nil, false end
	if E.Id then return `rbxassetid://{E.Id}`, E.Clip ~= nil end
	if E.Clip and RunService:IsStudio() then
		local Got = Temp[E.Clip]
		if not Got then
			local F = ReplicatedStorage:FindFirstChild(`NHSoccerClips`)
			local KS = F and F:FindFirstChild(E.Clip)
			if KS and KS:IsA(`KeyframeSequence`) then
				local Ok, T = pcall(function() return KeyframeSequenceProvider:RegisterKeyframeSequence(KS) end)
				if Ok and T then Got = T Temp[E.Clip] = T end
			end
		end
		if Got then return Got, true end
		if not Warned[E.Clip] then
			Warned[E.Clip] = true
			warn(`[Soccer clips] {E.Clip} isn't in ReplicatedStorage.NHSoccerClips (run tools/soccer2/bake/bake_soccer_clips.lua)`)
		end
	end
	if E.Was then return `rbxassetid://{E.Was}`, false end
	return nil, false
end

function M.Drive(Track: AnimationTrack, Clip: any, DashTime: number, Cap: number): (number, number, number, number)
	local Rate, Time, t0, t1 = Anim.Fit(Clip, DashTime, Cap)
	Track.TimePosition = t0
	Track:AdjustSpeed(Rate)
	task.spawn(function()
		local T0 = os.clock()
		while Track.IsPlaying and Track.TimePosition < t1 and os.clock() - T0 < Time + 1 do RunService.Heartbeat:Wait() end
		if Track.IsPlaying and math.abs(Track.Speed - Rate) < 1e-3 then Track:AdjustSpeed(1) end
	end)
	return Rate, Time, t0, t1
end

function M.Cancel() Token += 1 end

function M.DashPath(Root: BasePart, Track: AnimationTrack, Clip: any, Dir: Vector3?, Dist: number, Rate: number, t0: number, t1: number, Time: number)
	Token += 1
	local Mine = Token
	local D = if typeof(Dir) == `Vector3` then Vector3.new(Dir.X, 0, Dir.Z) else Vector3.zero
	if D.Magnitude < 0.1 then D = Vector3.new(Root.CFrame.LookVector.X, 0, Root.CFrame.LookVector.Z) end
	D = D.Unit
	local Att = Instance.new(`Attachment`) Att.Parent = Root
	local LV = Instance.new(`LinearVelocity`)
	LV.Attachment0 = Att LV.RelativeTo = Enum.ActuatorRelativeTo.World LV.VelocityConstraintMode = Enum.VelocityConstraintMode.Plane
	LV.PrimaryTangentAxis = Vector3.new(1, 0, 0) LV.SecondaryTangentAxis = Vector3.new(0, 0, 1)
	LV.PlaneVelocity = Vector2.zero
	LV.MaxForce = 60000
	LV.Parent = Root
	local T0 = os.clock()
	local Conn: RBXScriptConnection? = nil
	local function finish() if Conn then Conn:Disconnect() end LV:Destroy() Att:Destroy() end
	Conn = RunService.Heartbeat:Connect(function()
		local t = Track.TimePosition
		if Mine ~= Token or not Track.IsPlaying or t >= t1 or not Root.Parent or os.clock() - T0 > Time + 0.5 then finish() return end
		local t2 = math.min(t + 1 / 30, t1)
		local V = if t2 - t > 1e-4 then Dist * (Anim.Progress(Clip, t2, t0, t1) - Anim.Progress(Clip, t, t0, t1)) / (t2 - t) * Rate else 0
		LV.PlaneVelocity = Vector2.new(D.X, D.Z) * V
	end)
end

return M
