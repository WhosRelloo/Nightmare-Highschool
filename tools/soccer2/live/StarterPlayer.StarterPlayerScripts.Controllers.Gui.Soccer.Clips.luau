--[[
	Soccer clips (client, soccer-2.0): which animation a Config.Sports.SoccerAnims slot plays, its timing data
	(Config.SoccerClips, written by tools/soccer2/bake/bake_soccer_clips.lua), and the dash that follows a clip's travel.
		Id(Slot) -> (id?, fier)   a published Id; in Studio the baked NHSoccerClips copy (registered); else Was; else nil.
		                          fier = the FIER clip plays (its timing data applies)
		Clip(Slot) -> data?       the slot's Config.SoccerClips.Clips entry
		Drive(Track, Clip, DashTime, Cap) -> (Rate, Time, t0, t1)   the clip through its travel window at the fitted rate
		DashPath(Root, Track, Clip, Dir, Dist, Rate, t0, t1, Time, Slot?)  the mover's dash: Dist studs along Dir on the clip's curve
		                          (a clip that never loads: warns once and runs the plain 1.1 dash, Dist / Time over Time)
		Cancel()                  stops a running DashPath (a new dash takes over)
		Seek(Track, At, Speed)    TimePosition = At now, or once a loading clip has a Length (At + the time since, x Speed)
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
local Seeks = setmetatable({}, { __mode = `k` }) :: { [AnimationTrack]: number }   -- (polish) a track's newest Seek
local TestId = nil :: { [string]: string }?   -- (polish) Studio checks: a slot's id swapped for a bogus one

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
	if TestId and TestId[Slot] then return TestId[Slot], true end   -- (polish) Studio checks
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

-- (soccer-2.0 final) a published clip that hasn't loaded has Length 0, and a TimePosition set then is lost: wait for the
-- Length (up to 1 s) and jump to where the clip would be by now
function M.Seek(Track: AnimationTrack, At: number, Speed: number?)
	-- (polish) a per-track token: a newer Seek (a replay inside the first, loading second) retires an older waiting one
	local Mine = (Seeks[Track] or 0) + 1
	Seeks[Track] = Mine
	if Track.Length > 0 then Track.TimePosition = At return end
	if At <= 0 then return end
	local T0 = os.clock()
	task.spawn(function()
		while Track.Length <= 0 and os.clock() - T0 < 1 and Seeks[Track] == Mine do RunService.Heartbeat:Wait() end
		if Seeks[Track] ~= Mine then return end
		if Track.Length > 0 and Track.IsPlaying then
			Track.TimePosition = math.min(At + (os.clock() - T0) * (Speed or 1), Track.Length)
		end
	end)
end

function M.Drive(Track: AnimationTrack, Clip: any, DashTime: number, Cap: number): (number, number, number, number)
	local Rate, Time, t0, t1 = Anim.Fit(Clip, DashTime, Cap)
	M.Seek(Track, t0, Rate)
	Track:AdjustSpeed(Rate)
	task.spawn(function()
		local L0 = os.clock()
		while Track.Length <= 0 and Track.IsPlaying and os.clock() - L0 < 1 do RunService.Heartbeat:Wait() end
		local T0 = os.clock()
		while Track.IsPlaying and Track.TimePosition < t1 and os.clock() - T0 < Time + 1 do RunService.Heartbeat:Wait() end
		if Track.IsPlaying and math.abs(Track.Speed - Rate) < 1e-3 then Track:AdjustSpeed(1) end
	end)
	return Rate, Time, t0, t1
end

function M.Cancel() Token += 1 end

-- (polish) Studio checks: swap a slot's id (nil puts it back); a bogus id is a clip that never loads
function M.TestId(Slot: string, Id: string?)
	if not RunService:IsStudio() then return end
	TestId = TestId or {}
	TestId[Slot] = Id
	if next(TestId) == nil then TestId = nil end
end

function M.DashPath(Root: BasePart, Track: AnimationTrack, Clip: any, Dir: Vector3?, Dist: number, Rate: number, t0: number, t1: number, Time: number, Slot: string?)
	Token += 1
	local Mine = Token
	local D = if typeof(Dir) == `Vector3` then Vector3.new(Dir.X, 0, Dir.Z) else Vector3.zero
	if D.Magnitude < 0.1 then D = Vector3.new(Root.CFrame.LookVector.X, 0, Root.CFrame.LookVector.Z) end
	D = D.Unit
	if Clip == nil then return end
	local Att = Instance.new(`Attachment`) Att.Parent = Root
	local LV = Instance.new(`LinearVelocity`)
	LV.Attachment0 = Att LV.RelativeTo = Enum.ActuatorRelativeTo.World LV.VelocityConstraintMode = Enum.VelocityConstraintMode.Plane
	LV.PrimaryTangentAxis = Vector3.new(1, 0, 0) LV.SecondaryTangentAxis = Vector3.new(0, 0, 1)
	LV.PlaneVelocity = Vector2.zero
	LV.MaxForce = 60000
	LV.Parent = Root
	local L0 = os.clock()
	local T0 = L0
	local Plain = nil :: number?   -- (polish) the clip never loaded: when the plain 1.1 dash began
	local Conn: RBXScriptConnection? = nil
	local function finish()
		if Conn then Conn:Disconnect() end LV:Destroy() Att:Destroy()
	end
	Conn = RunService.Heartbeat:Connect(function(dt: number)
		local Ok, Err = pcall(function()
			if Mine ~= Token or not Root.Parent or not (Plain or Track.IsPlaying) then finish() return end
			-- (soccer-2.0 final) a clip still loading: hold still (up to 1 s), and the dash's time starts once it has loaded
			if Plain then
				-- (polish) the 1.1 dash (Gui.Soccer Local.Dash): Dist studs at Dist / Time over Time, flat along Dir
				if os.clock() - Plain >= Time then finish() return end
				LV.PlaneVelocity = Vector2.new(D.X, D.Z) * (Dist / Time)
				return
			end
			if Track.Length <= 0 then
				if os.clock() - L0 > 1 then
					Plain = os.clock()
					local Key = `never:{Slot or Track.Name}`
					if not Warned[Key] then Warned[Key] = true warn(`[Soccer clips] {Slot or Track.Name} never loaded; plain dash`) end
					LV.PlaneVelocity = Vector2.new(D.X, D.Z) * (Dist / Time)
					return
				end
				T0 = os.clock()
				LV.PlaneVelocity = Vector2.zero
				return
			end
			local t = Track.TimePosition
			if t >= t1 or os.clock() - T0 > Time + 0.5 then finish() return end
			local t2 = math.min(t + dt * Rate, t1)
			local V = if t2 - t > 1e-4 then Dist * (Anim.Progress(Clip, t2, t0, t1) - Anim.Progress(Clip, t, t0, t1)) / (t2 - t) * Rate else 0
			LV.PlaneVelocity = Vector2.new(D.X, D.Z) * V
		end)
		if not Ok then
			warn("[Soccer clips] DashPath: " .. tostring(Err))
			finish()
		end
	end)
end

return M
