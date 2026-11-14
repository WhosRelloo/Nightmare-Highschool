--[[
	The everyday kit (client world effects). Controllers.World.KitFx          (owner approved 2026-11-11)
	Server: Services.Features.Kit (it decides everything; this only draws and steadies).

	  Holds      a character holding a kit Tool keeps its posed shoulder(s) still: after the animations run, the
	             Transform of the shoulder the server posed (Config.KitHolds R / L) is cleared, like PhoneHold.
	  Umbrella   while your NHUmbrellaOpen is set, your fall speed is capped at Config.Kit.Umbrella.FallCap.
	  Chill      NHChilled: frost creeps in at the screen edges; chilled characters breathe out little puffs.
	  Wounded    NHWounded: ink-dark screen edges and a slow heartbeat (no red, no blood).
	  Rain       workspace NHRain: rain around your camera (not indoors), the rain loop, a little darker.
	  Lantern    a lit lantern's light flickers softly.
	  Keys       worn dorm keys jingle quietly when their owner walks or runs.
]]
local Lighting = game:GetService(`Lighting`)
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local TweenService = game:GetService(`TweenService`)

local KitCfg = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`Kit`))
local Holds = require(ReplicatedStorage.Config:WaitForChild(`KitHolds`))

local Player = Players.LocalPlayer
local Shared = {}
local Local = {}

local SOUND = {
	Jingle = `rbxassetid://9113849492`;   -- Pro Sound Effects: coins or keys jingle
	Rain = `rbxassetid://5911952995`;     -- rain, seamless loop
	Heart = `rbxassetid://6202853067`;    -- heartbeat (loop)
}
local MAX_DIST = 150

---| holds |---

function Local.Holds()
	local Cam = workspace.CurrentCamera
	local Eye = Cam and Cam.CFrame.Position or Vector3.zero
	for _, P in Players:GetPlayers() do
		local Char = P.Character
		local Root = Char and Char:FindFirstChild(`HumanoidRootPart`) :: BasePart?
		if not Root or (Root.Position - Eye).Magnitude > MAX_DIST then continue end
		for _, T in Char:GetChildren() do
			local Id = T:IsA(`Tool`) and T:GetAttribute(`NHKit`)
			local H = Id and Holds[Id]
			if H and Char:GetAttribute(`NHKitAnim`) then break end   -- a use clip is playing: let it move the arm
			if H then
				local Torso = Char:FindFirstChild(`Torso`)
				if Torso then
					if H.R then local M = Torso:FindFirstChild(`Right Shoulder`) if M and M:IsA(`Motor6D`) then M.Transform = CFrame.identity end end
					if H.L then local M = Torso:FindFirstChild(`Left Shoulder`) if M and M:IsA(`Motor6D`) then M.Transform = CFrame.identity end end
				end
				break
			end
		end
	end
end

---| screen edges (frost, ink) |---

local Edges = nil
function Local.BuildEdges()
	local G = Instance.new(`ScreenGui`)
	G.Name = `NHKitEdges`
	G.IgnoreGuiInset = true
	G.ResetOnSpawn = false
	G.DisplayOrder = 2
	G.Parent = Player:WaitForChild(`PlayerGui`)
	local function ring(Name: string, Color: Color3)
		local F = Instance.new(`Frame`)
		F.Name = Name
		F.BackgroundTransparency = 1
		F.Size = UDim2.fromScale(1, 1)
		F.Parent = G
		local Sides = {}
		for _, S in { { UDim2.fromScale(1, 0.22), UDim2.fromScale(0, 0), 90 }, { UDim2.fromScale(1, 0.22), UDim2.fromScale(0, 0.78), -90 },
			{ UDim2.fromScale(0.16, 1), UDim2.fromScale(0, 0), 0 }, { UDim2.fromScale(0.16, 1), UDim2.fromScale(0.84, 0), 180 } } do
			local E = Instance.new(`Frame`)
			E.BorderSizePixel = 0
			E.BackgroundColor3 = Color
			E.Size, E.Position = S[1], S[2]
			E.BackgroundTransparency = 0
			local Gr = Instance.new(`UIGradient`)
			Gr.Rotation = S[3]
			Gr.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.15), NumberSequenceKeypoint.new(0.55, 0.8), NumberSequenceKeypoint.new(1, 1) })
			Gr.Parent = E
			E.Parent = F
			table.insert(Sides, E)
		end
		return { Root = F; Sides = Sides; Level = 0 }
	end
	-- the painted edges (art/ui/hud/make_kit_ui.py: FrostEdge, InkEdge) when they're uploaded, else soft gradients
	local function art(Name: string, Fallback: Color3)
		local Id = KitCfg.Art and KitCfg.Art[Name]
		if not (typeof(Id) == `number` and Id > 0) then return ring(Name, Fallback) end
		local I = Instance.new(`ImageLabel`)
		I.Name = Name
		I.BackgroundTransparency = 1
		I.Image = `rbxassetid://{Id}`
		I.ScaleType = Enum.ScaleType.Stretch
		I.Size = UDim2.fromScale(1, 1)
		I.ImageTransparency = 1
		I.Parent = G
		return { Root = I; Sides = {}; Level = 0; Image = I }
	end
	Edges = { Gui = G; Frost = art(`FrostEdge`, Color3.fromRGB(196, 222, 244)); Ink = art(`InkEdge`, Color3.fromRGB(8, 6, 12)) }
	Edges.Frost.Root.Visible, Edges.Ink.Root.Visible = false, false
end

function Local.EdgeTo(E, Want: number, Dt: number, Rate: number)
	E.Level += math.clamp(Want - E.Level, -Rate * Dt, Rate * Dt)
	E.Root.Visible = E.Level > 0.01
	for _, S in E.Sides do S.BackgroundTransparency = 1 - E.Level end
	if E.Image then E.Image.ImageTransparency = 1 - math.min(0.8, E.Level * (if E.Image.Name == `FrostEdge` then 1.1 else 1.5)) end
end

---| sounds |---

local Sounds = {}
function Local.Sound(Key: string, Looped: boolean, Volume: number): Sound
	local S = Sounds[Key]
	if S and S.Parent then return S end
	S = Instance.new(`Sound`)
	S.Name = `NHKit{Key}`
	S.SoundId = SOUND[Key]
	S.Looped = Looped
	S.Volume = Volume
	S.Parent = workspace.CurrentCamera or workspace
	Sounds[Key] = S
	return S
end

---| rain |---

local Rain = nil
function Local.BuildRain()
	local P = Instance.new(`Part`)
	P.Name = `NHKitRain`
	P.Anchored, P.CanCollide, P.CanQuery, P.CanTouch = true, false, false, false
	P.Transparency = 1
	P.Size = Vector3.new(90, 1, 90)
	local E = Instance.new(`ParticleEmitter`)
	E.Name = `Drops`
	E.Texture = `rbxasset://textures/particles/sparkles_main.dds`
	E.Color = ColorSequence.new(Color3.fromRGB(190, 200, 220))
	E.LightEmission = 0.35
	E.LightInfluence = 0.6
	E.Transparency = NumberSequence.new(0.35)
	E.Size = NumberSequence.new(0.13)
	E.Squash = NumberSequence.new(-3.2)
	E.Orientation = Enum.ParticleOrientation.VelocityParallel
	E.EmissionDirection = Enum.NormalId.Bottom
	E.Speed = NumberRange.new(70, 85)
	E.Lifetime = NumberRange.new(0.8, 1.0)
	E.Rate = 0
	E.SpreadAngle = Vector2.new(4, 4)
	E.Parent = P
	local CC = Instance.new(`ColorCorrectionEffect`)
	CC.Name = `NHKitRainGrade`
	CC.Brightness, CC.Saturation, CC.Contrast = 0, 0, 0
	CC.Parent = Lighting
	Rain = { Part = P; Drops = E; Grade = CC; Level = 0 }
end

local RayParams = RaycastParams.new()
RayParams.FilterType = Enum.RaycastFilterType.Exclude

function Local.Roofed(Pos: Vector3): boolean
	RayParams.FilterDescendantsInstances = { workspace:FindFirstChild(`Live`) or Player.Character, Rain and Rain.Part }
	local Hit = workspace:Raycast(Pos, Vector3.new(0, 80, 0), RayParams)
	return Hit ~= nil and Hit.Instance.Transparency < 0.9 and Hit.Instance.CanCollide
end

function Local.StepRain(Dt: number)
	if not Rain then Local.BuildRain() end
	local On = workspace:GetAttribute(`NHRain`) == true and Player:GetAttribute(`InMainMenu`) ~= true
	local Cam = workspace.CurrentCamera
	local Pos = Cam and Cam.CFrame.Position or Vector3.zero
	local Inside = On and (Local.Roofed(Pos) or Player:GetAttribute(`NHInHome`) ~= nil)
	local Want = if On and not Inside then 1 elseif On then 0.25 else 0
	Rain.Level += math.clamp(Want - Rain.Level, -Dt * 0.6, Dt * 0.6)
	Rain.Part.CFrame = CFrame.new(Pos + Vector3.new(0, 40, 0))
	Rain.Part.Parent = if Rain.Level > 0.01 then workspace else nil
	Rain.Drops.Rate = if On and not Inside then 900 * Rain.Level else 0
	Rain.Grade.Brightness = -0.06 * math.min(1, Rain.Level * 2)
	Rain.Grade.Saturation = -0.12 * math.min(1, Rain.Level * 2)
	local S = Local.Sound(`Rain`, true, 0)
	S.Volume = 0.55 * Rain.Level
	if Rain.Level > 0.01 and not S.IsPlaying then S:Play() elseif Rain.Level <= 0.01 and S.IsPlaying then S:Stop() end
end

---| breath puffs, lantern flicker, key jingles |---

local Puffs = setmetatable({}, { __mode = `k` })
local Jingle = setmetatable({}, { __mode = `k` })

function Local.Puff(Char: Model, On: boolean)
	local Head = Char:FindFirstChild(`Head`) :: BasePart?
	if not Head then return end
	local E = Puffs[Char]
	if On and not E then
		local A = Instance.new(`Attachment`)
		A.Name = `NHKitBreath`
		A.Position = Vector3.new(0, -0.15, -0.65)
		A.Parent = Head
		E = Instance.new(`ParticleEmitter`)
		E.Texture = `rbxasset://textures/particles/smoke_main.dds`
		E.Color = ColorSequence.new(Color3.fromRGB(230, 236, 244))
		E.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.7), NumberSequenceKeypoint.new(1, 1) })
		E.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.12), NumberSequenceKeypoint.new(1, 0.55) })
		E.Lifetime = NumberRange.new(0.9, 1.3)
		E.Speed = NumberRange.new(0.8, 1.4)
		E.EmissionDirection = Enum.NormalId.Front
		E.Drag = 2
		E.Rate = 0
		E.LightInfluence = 1
		E.Parent = A
		Puffs[Char] = E
	elseif not On and E then
		if E.Parent then E.Parent:Destroy() end
		Puffs[Char] = nil
	end
end

function Local.StepWorld(Dt: number)
	local Cam = workspace.CurrentCamera
	local Eye = Cam and Cam.CFrame.Position or Vector3.zero
	local T = os.clock()
	for _, P in Players:GetPlayers() do
		local Char = P.Character
		local Root = Char and Char:FindFirstChild(`HumanoidRootPart`) :: BasePart?
		if not Root or (Root.Position - Eye).Magnitude > MAX_DIST then continue end
		-- breath
		local Chilled = Char:GetAttribute(`NHChilled`) == true
		Local.Puff(Char, Chilled)
		local E = Puffs[Char]
		if E and math.floor(T / 2.6) ~= (E:GetAttribute(`Last`) or -1) then
			E:SetAttribute(`Last`, math.floor(T / 2.6))
			E:Emit(3)
		end
		-- lantern flicker
		for _, Tool in Char:GetChildren() do
			if Tool:IsA(`Tool`) and Tool:GetAttribute(`NHKit`) == `Lantern` then
				local L = Tool:FindFirstChild(`LanternLight`, true)
				if L and L:IsA(`PointLight`) and L.Enabled then
					L.Brightness = KitCfg.Lantern.Brightness * (0.94 + 0.06 * math.sin(T * 11.3 + 1.7) * math.sin(T * 3.1))
				end
			end
		end
		-- key jingle while walking or running
		local Keys = Char:FindFirstChild(`NHKitKeys`)
		if Keys then
			local Speed = Vector3.new(Root.AssemblyLinearVelocity.X, 0, Root.AssemblyLinearVelocity.Z).Magnitude
			local Part = Keys:FindFirstChildWhichIsA(`BasePart`)
			local J = Jingle[Char]
			if Part and not (J and J.Parent) then
				J = Instance.new(`Sound`)
				J.Name = `NHKitJingle`
				J.SoundId = SOUND.Jingle
				J.Volume = 0.22
				J.RollOffMaxDistance = 40
				J.RollOffMinDistance = 4
				J.Parent = Part
				Jingle[Char] = J
			end
			if J and Speed > 6 then
				local Gap = if Speed > 20 then 0.32 else 0.55
				if T - (J:GetAttribute(`At`) or 0) > Gap then
					J:SetAttribute(`At`, T)
					J.TimePosition = math.random() * 1.2
					J.PlaybackSpeed = 0.95 + math.random() * 0.15
					J:Play()
					task.delay(0.28, function() if J.Parent then J:Stop() end end)
				end
			end
		end
	end
	-- your own screen: frost and ink, the heartbeat
	if not Edges then Local.BuildEdges() end
	local Mine = Player.Character
	local Menu = Player:GetAttribute(`InMainMenu`) == true
	Local.EdgeTo(Edges.Frost, if Mine and Mine:GetAttribute(`NHChilled`) and not Menu then 0.55 else 0, Dt, 0.25)
	local Wounded = Mine and Mine:GetAttribute(`NHWounded`) and not Menu
	Local.EdgeTo(Edges.Ink, if Wounded then 0.6 + 0.12 * math.sin(T * 5.2) else 0, Dt, 1.2)
	local H = Local.Sound(`Heart`, true, 0)
	H.Volume = if Wounded then 0.5 else 0
	if Wounded and not H.IsPlaying then H:Play() elseif not Wounded and H.IsPlaying then H:Stop() end
end

---| the umbrella's slow fall (your own character: you own its physics) |---

function Local.StepFall()
	local Char = Player.Character
	if not (Char and Char:GetAttribute(`NHUmbrellaOpen`) == true) then return end
	local Root = Char:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	if not Root then return end
	local V = Root.AssemblyLinearVelocity
	local Cap = KitCfg.Umbrella.FallCap
	if V.Y < -Cap then Root.AssemblyLinearVelocity = Vector3.new(V.X, -Cap, V.Z) end
end

function Shared.OnStart()
	RunService.PreSimulation:Connect(function()
		local Ok, Err = pcall(Local.Holds)
		if not Ok then warn(`[KitFx] holds: {Err}`) end
		pcall(Local.StepFall)
	end)
	RunService.PostSimulation:Connect(function() pcall(Local.StepFall) end)
	local Acc = 0
	RunService.Heartbeat:Connect(function(Dt)
		Acc += Dt
		if Acc < 1 / 20 then return end
		local Step = Acc
		Acc = 0
		local Ok, Err = pcall(Local.StepWorld, Step)
		if not Ok then warn(`[KitFx] {Err}`) end
		pcall(Local.StepRain, Step)
	end)
end

return Shared
