--[[
	Sky motion (client). Controllers.World.SkyMotion   (2.36, sky-2360)   Config: ReplicatedStorage.Config.DayCycle.Motion
	Docs: docs/Sky-and-Lighting.md §5.

	Layers, by tier (the game's own Effects Quality, LocalPlayer NHFxQuality "High"/"Low"; High drops to Medium, and
	Medium to Low, while the average frame time stays over Motion.SlowFrameMs for Motion.SlowSeconds):
		Clouds      workspace.GlobalWind drives Terrain.Clouds' drift (World.DayCycle owns Cover, Density and Color).
		            A storm multiplies it (StormMultiplier); Low halves it.
		Wisp ring   curved Beams with NHWisp_A / NHWisp_B on a client-only anchor that follows the camera. The engine scrolls
		            them (TextureSpeed); Color is the key's CloudColor; they fade in with the night (FadeIn / FadeOut hours).
		            High 3 beams, Medium 1, Low none.
		Storm       while the sky is Storm (workspace NHSky): 2-3 quick grade-brightness flickers every MinGap..MaxGap
		            seconds, at most MaxHz, never white, on its own ColorCorrectionEffect "NHStormFlash".
		            Reduce Flashing (NHReducedFlash) gives one soft pulse instead.
		Sky turn    off (Motion.SkyTurn.Enabled) until Studio shows no Atmosphere seam at QL21 and QL1.
	It follows World.DayCycle: nothing moves while DayCycle is suspended (the main menu, a cutscene that takes the
	lighting); the wind goes back to the place's own, the wisps hide.

		SkyMotion.Tier(): "High" | "Medium" | "Low"     SkyMotion.Info(): table (for tests)
	Studio test: LocalPlayer NHSkyTierPreview = "High" | "Medium" | "Low" forces the tier.
]]

local Lighting = game:GetService(`Lighting`)
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)

local Player = Players.LocalPlayer
local Config = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`DayCycle`))
local Motion = Config.Motion
local DayCycle = require(script.Parent:WaitForChild(`DayCycle`))
local Fx = require(script.Parent.Parent:WaitForChild(`Fx`))

local Shared = {}
local State = {
	Tier = `High`, Slow = 0, Frames = 0, FrameSum = 0, Drop = 0,
	BaseWind = nil :: Vector3?, Anchor = nil :: BasePart?, Beams = {} :: { Beam }, Built = -1,
	NextStorm = 0, Flash = nil :: ColorCorrectionEffect?, Flickering = false, Weight = 0,
}

local function smooth(x: number): number x = math.clamp(x, 0, 1) return x * x * (3 - 2 * x) end

function Shared.Tier(): string
	-- Studio test: LocalPlayer NHSkyTierPreview forces a tier (Studio's own frame times would drop it)
	local Pv = Player:GetAttribute(`NHSkyTierPreview`)
	if (Pv == `High` or Pv == `Medium` or Pv == `Low`) and RunService:IsStudio() then return Pv end
	local Base = if Player:GetAttribute(`NHFxQuality`) == `Low` then 2 else 0
	local Steps = { `High`, `Medium`, `Low` }
	return Steps[math.min(Base + State.Drop, 2) + 1]
end

local function storm(): boolean
	local S = Player:GetAttribute(`NHSkyPreview`) or workspace:GetAttribute(`NHSky`)
	return S == `Storm`
end

-- 0 by day, 1 at night, by the wisps' own fade hours
local function wispWeight(Hour: number): number
	local W = Motion.Wisps
	local I0, I1, O0, O1 = W.FadeIn[1], W.FadeIn[2], W.FadeOut[1], W.FadeOut[2]
	if Hour >= I1 or Hour < O0 then return 1 end
	if Hour >= I0 then return smooth((Hour - I0) / (I1 - I0)) end
	if Hour < O1 then return 1 - smooth((Hour - O0) / (O1 - O0)) end
	return 0
end

---| Clouds |---

local function setWind(On: boolean)
	if On then
		State.BaseWind = State.BaseWind or workspace.GlobalWind
		local C = Motion.Clouds
		local Mul = (if storm() then C.StormMultiplier or 3 else 1) * (if Shared.Tier() == `Low` then C.LowMultiplier or 0.5 else 1)
		local Want = C.WindStuds * Mul
		if (workspace.GlobalWind - Want).Magnitude > 1e-3 then workspace.GlobalWind = Want end
	elseif State.BaseWind then
		workspace.GlobalWind = State.BaseWind
		State.BaseWind = nil
	end
end

---| Wisp ring |---

local function clearBeams()
	for _, B in State.Beams do
		if B.Attachment0 then B.Attachment0:Destroy() end
		if B.Attachment1 then B.Attachment1:Destroy() end
		B:Destroy()
	end
	table.clear(State.Beams)
	State.Built = -1
end

local function anchor(): BasePart
	if State.Anchor and State.Anchor.Parent then return State.Anchor end
	local P = Instance.new(`Part`)
	P.Name = `NHSkyMotionAnchor`
	P.Anchored, P.CanCollide, P.CanQuery, P.CanTouch, P.CastShadow = true, false, false, false, false
	P.Transparency = 1
	P.Size = Vector3.one
	P.Parent = workspace.CurrentCamera -- client-only, never replicated
	State.Anchor = P
	return P
end

local function asset(Id: any): string?
	if typeof(Id) == `number` and Id > 0 then return `rbxassetid://{Id}` end
	return nil
end

-- N beams, spread around the ring; each a long curved band high over the horizon
local function buildBeams(N: number)
	if State.Built == N then return end
	clearBeams()
	State.Built = N
	if N <= 0 then return end
	local W = Motion.Wisps
	local R = W.Radius or 1500
	local Tex = { asset(W.Textures and W.Textures.A), asset(W.Textures and W.Textures.B) }
	if not Tex[1] and not Tex[2] then return end
	local A = anchor()
	local Rng = Random.new(2360)
	for I = 1, N do
		local Yaw = (I - 1) / N * math.pi * 2 + Rng:NextNumber(-0.3, 0.3)
		local Span = Rng:NextNumber(0.7, 1.1)
		local H = R * Rng:NextNumber(0.18, 0.3)
		local A0 = Instance.new(`Attachment`)
		A0.Position = Vector3.new(math.cos(Yaw) * R, H, math.sin(Yaw) * R)
		A0.Parent = A
		local A1 = Instance.new(`Attachment`)
		A1.Position = Vector3.new(math.cos(Yaw + Span) * R, H * 1.15, math.sin(Yaw + Span) * R)
		A1.Parent = A
		local B = Instance.new(`Beam`)
		B.Name = `NHWisp{I}`
		B.Attachment0, B.Attachment1 = A0, A1
		B.Texture = Tex[(I - 1) % 2 + 1] or Tex[1] or Tex[2] :: string
		B.TextureMode = Enum.TextureMode.Wrap
		B.TextureLength = R * 0.4 -- (Studio check) at 0.9 R the thin streaks were too sparse to see
		B.TextureSpeed = Rng:NextNumber(W.TextureSpeed[1], W.TextureSpeed[2])
		B.Width0, B.Width1 = R * 0.16, R * 0.22
		B.CurveSize0, B.CurveSize1 = R * 0.35, -R * 0.2
		B.FaceCamera = true
		-- (Studio check) the wisp textures are mostly clear (mean alpha 6-16 of 255): unlit and with no emission they
		-- vanished against the night sky, so they glow (emission 1) a little over their colour
		B.LightInfluence, B.LightEmission = 0, 1
		B.Brightness = 2.5
		B.Segments = 24
		B.Transparency = NumberSequence.new(1)
		B.Parent = A
		table.insert(State.Beams, B)
	end
end

local function stepWisps(On: boolean, Hour: number)
	local N = if On then (Motion.Wisps.Beams[Shared.Tier()] or 0) else 0
	buildBeams(N)
	if #State.Beams == 0 then return end
	local Cam = workspace.CurrentCamera
	if Cam then State.Anchor.CFrame = CFrame.new(Cam.CFrame.Position) end
	local W = wispWeight(Hour)
	State.Weight = W
	local Look = DayCycle.LookAt(Hour)
	local Color = Look.CloudColor or Color3.new(1, 1, 1)
	-- soft at both ends, at most 70 % opaque in the middle
	local Peak = 1 - 0.7 * W
	local T = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.25, Peak),
		NumberSequenceKeypoint.new(0.75, Peak), NumberSequenceKeypoint.new(1, 1) })
	for _, B in State.Beams do
		B.Enabled = W > 0.01
		B.Color = ColorSequence.new(Color)
		B.Transparency = T
	end
end

---| Storm flashes |---

local function flash(): ColorCorrectionEffect
	if State.Flash and State.Flash.Parent then return State.Flash end
	local G = Instance.new(`ColorCorrectionEffect`)
	G.Name = `NHStormFlash`
	G.Brightness = 0
	G.Parent = Lighting
	State.Flash = G
	return G
end

local function strike()
	if State.Flickering then return end
	State.Flickering = true
	local S = Motion.Storm
	local Rng = Random.new()
	local Soft = Player:GetAttribute(`NHReducedFlash`) == true
	local Peak = S.GradeBrightness * Fx.FlashScale()
	local Count = if Soft then 1 else Rng:NextInteger(S.Flickers[1], S.Flickers[2])
	local Gap = 1 / math.max(S.MaxHz or 3, 0.5)
	task.spawn(function()
		local G = flash()
		for I = 1, Count do
			local Len = if Soft then 0.6 else Rng:NextNumber(S.FlickerSeconds[1], S.FlickerSeconds[2])
			local T0 = os.clock()
			while os.clock() - T0 < Len do
				local T = (os.clock() - T0) / Len
				G.Brightness = Peak * math.sin(math.pi * T)
				RunService.RenderStepped:Wait()
			end
			G.Brightness = 0
			if I < Count then task.wait(math.max(Gap - Len, 0.05)) end
		end
		State.Flickering = false
	end)
end

local function stepStorm(On: boolean)
	if not (On and storm()) then
		if State.Flash then State.Flash.Brightness = 0 end
		State.NextStorm = 0
		return
	end
	local Now = os.clock()
	local S = Motion.Storm
	if State.NextStorm == 0 then State.NextStorm = Now + Random.new():NextNumber(S.MinGap, S.MaxGap) end
	if Now >= State.NextStorm then
		strike()
		State.NextStorm = Now + Random.new():NextNumber(S.MinGap, S.MaxGap)
	end
end

---| Tier watch |---

local function watchFrames(Dt: number)
	State.Frames += 1
	State.FrameSum += Dt
	if State.FrameSum < 1 then return end
	local Avg = State.FrameSum / State.Frames * 1000
	State.Frames, State.FrameSum = 0, 0
	if Avg > (Motion.SlowFrameMs or 22) then State.Slow += 1 else State.Slow = 0 end
	if State.Slow >= (Motion.SlowSeconds or 5) and State.Drop < 2 then
		State.Drop += 1
		State.Slow = 0
	end
end

function Shared.Info()
	return { Tier = Shared.Tier(); Drop = State.Drop; Beams = #State.Beams; Weight = State.Weight; Wind = workspace.GlobalWind;
		Storm = storm(); Active = DayCycle.Active() }
end

function Shared.OnStart()
	if not (Motion and Motion.Enabled) then return end
	RunService.Heartbeat:Connect(watchFrames)
	-- (2.36) the sky turn ships only after the seam check; until then nothing rotates the Sky here
	task.spawn(function()
		while true do
			local On = DayCycle.Active()
			local Hour = DayCycle.Hour()
			pcall(setWind, On)
			pcall(stepWisps, On, Hour)
			pcall(stepStorm, On)
			task.wait(0.2)
		end
	end)
end

return Shared
