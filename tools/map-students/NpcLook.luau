--[[
	NpcLook (client). Controllers.World.NpcLook  (NH core add-on for the Map place, 2026-11-10)

	The client half of the school NPCs' awareness (Services.Features.MapStudents):
	  * Head turning: each student's model carries NHLookAt (Vector3) and NHLookUntil (server time). While it's set,
	    the head turns toward the point over a few frames (clamped like a neck: 75 degrees either side, 35 up or down),
	    and eases back to straight ahead when it lapses. Only students within 140 studs are animated. This runs on
	    each client, so it's smooth at any frame rate and costs the server nothing.
	  * Speech bubbles: NHSay + NHSayAt show a small engraved bubble over the head for NHSayFor seconds (longer lines
	    stay up longer), and the head nods a little while they talk.
	  * Voice blips (1.78.2): every line is heard as a short burble of pitched ticks, one voice per student
	    (NHVoice, set by the server), as many syllables as the text, rising at a question, louder at "!", pausing at
	    commas and "...". 3D from the head, on the game's effects volume (SoundService.NH_Master.NH_Effects).
	  * Fidgets (1.78.2): NHFidget = "Stretch" (+ NHFidgetAt) raises both arms for a moment. The phone fidget is a real
	    Tool on the server; Controllers.Character.PhoneHold keeps that arm steady.
	Reduce Motion (NHReducedMotion) keeps the head turns but makes them quicker and shorter, and skips the stretch.
]]

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)

local Shared = {}

local RANGE = 140
local MAX_YAW, MAX_PITCH = math.rad(75), math.rad(35)
local BUBBLE_TIME = 3.5

local Theme = nil
pcall(function() Theme = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Theme`)) end)

local State = {} :: { [Model]: any }

local BLIP = `rbxasset://sounds/volume_slider.ogg` -- ships with every Roblox client
local BLIP_RANGE = 55

-- the syllables of a line: { gap before it, pitch factor, loudness factor }
local function syllables(Text: string): { { number } }
	local Out = {}
	local Question = Text:find(`%?`) ~= nil
	local Shout = Text:find(`!`) ~= nil
	for Word, Sep in Text:gmatch(`([%w']+)([^%w']*)`) do
		local N = math.clamp(math.floor(#Word / 3 + 0.5), 1, 4)
		for _ = 1, N do table.insert(Out, { 0.075 + math.random() * 0.02, 0.92 + math.random() * 0.2, if Shout then 1.4 else 1 }) end
		if Sep:find(`%.%.`) or Sep:find(`,`) or Sep:find(`%-`) then table.insert(Out, { 0.22 }) -- a pause
		elseif Sep:find(`[%.!?]`) then table.insert(Out, { 0.16 }) end
		if #Out >= 22 then break end
	end
	if #Out == 0 then -- "..." alone: a hesitant hum
		table.insert(Out, { 0.1, 0.8, 0.6 })
		table.insert(Out, { 0.25, 0.75, 0.5 })
	end
	if Question then -- the last two syllables rise
		local K = 0
		for I = #Out, 1, -1 do
			if Out[I][2] then
				Out[I][2] *= 1.18 - K * 0.08
				K += 1
				if K >= 2 then break end
			end
		end
	end
	return Out
end

local function voice(M: Model, Text: string)
	local Head = M:FindFirstChild(`Head`)
	local Cam = workspace.CurrentCamera
	if not (Head and Head:IsA(`BasePart`) and Cam) then return end
	if (Head.Position - Cam.CFrame.Position).Magnitude > BLIP_RANGE + 20 then return end
	local Pitch = tonumber(M:GetAttribute(`NHVoice`)) or 1
	local Group = nil
	local Master = game:GetService(`SoundService`):FindFirstChild(`NH_Master`)
	Group = Master and Master:FindFirstChild(`NH_Effects`)
	local St = State[M]
	if not St then return end
	St.VoiceToken = (St.VoiceToken or 0) + 1
	local My = St.VoiceToken
	-- a few reusable sounds on the head, taken in turn
	St.Voices = St.Voices or {}
	for I = #St.Voices + 1, 3 do
		local Snd = Instance.new(`Sound`)
		Snd.Name = `NHVoice`
		Snd.SoundId = BLIP
		Snd.RollOffMode = Enum.RollOffMode.InverseTapered
		Snd.RollOffMinDistance = 6
		Snd.RollOffMaxDistance = BLIP_RANGE
		if Group and Group:IsA(`SoundGroup`) then Snd.SoundGroup = Group end
		Snd.Parent = Head
		St.Voices[I] = Snd
	end
	task.spawn(function()
		local K = 0
		for _, Syl in syllables(Text) do
			if St.VoiceToken ~= My or not Head.Parent then return end
			task.wait(Syl[1])
			if Syl[2] then
				K = K % #St.Voices + 1
				local Snd = St.Voices[K]
				Snd.PlaybackSpeed = Pitch * Syl[2]
				Snd.Volume = 0.32 * (Syl[3] or 1)
				Snd.TimePosition = 0
				Snd:Play()
				-- just the attack of the tick: a crisp syllable, not its 0.85 s tail
				local Cut = Snd
				task.delay(0.1, function() if Cut.IsPlaying then Cut:Stop() end end)
			end
		end
	end)
end

-- a quick stretch: both arms up and back down over about 1.6 s (on this client only)
local function stretch(M: Model)
	if Players.LocalPlayer:GetAttribute(`NHReducedMotion`) == true then return end
	local Torso = M:FindFirstChild(`Torso`)
	local R = Torso and Torso:FindFirstChild(`Right Shoulder`)
	local L = Torso and Torso:FindFirstChild(`Left Shoulder`)
	if not (R and L and R:IsA(`Motor6D`) and L:IsA(`Motor6D`)) then return end
	local R0 = R:GetAttribute(`NHBaseC0`) or R.C0
	local L0 = L:GetAttribute(`NHBaseC0`) or L.C0
	task.spawn(function()
		local T0 = os.clock()
		while os.clock() - T0 < 1.6 and M.Parent do
			local A = math.sin(math.clamp((os.clock() - T0) / 1.6, 0, 1) * math.pi) -- 0 -> 1 -> 0
			local Up = math.rad(165) * A
			R.C0 = R0 * CFrame.Angles(0, 0, Up)
			L.C0 = L0 * CFrame.Angles(0, 0, -Up)
			RunService.RenderStepped:Wait()
		end
		R.C0, L.C0 = R0, L0
	end)
end

local function neckOf(M: Model): Motor6D?
	local Torso = M:FindFirstChild(`Torso`)
	local N = Torso and Torso:FindFirstChild(`Neck`)
	return if N and N:IsA(`Motor6D`) then N else nil
end

local function bubble(M: Model)
	local Head = M:FindFirstChild(`Head`)
	local Text = M:GetAttribute(`NHSay`)
	if not (Head and Head:IsA(`BasePart`) and typeof(Text) == `string` and Text ~= ``) then return end
	local Old = Head:FindFirstChild(`NHSayBubble`)
	if Old then Old:Destroy() end
	-- in a conversation the other one's bubble gives way, so two lines never sit on top of each other
	for Other in State do
		local OH = Other ~= M and Other:FindFirstChild(`Head`)
		if OH and OH:IsA(`BasePart`) and (OH.Position - Head.Position).Magnitude < 7 then
			local B = OH:FindFirstChild(`NHSayBubble`)
			if B then B:Destroy() end
		end
	end
	local G = Instance.new(`BillboardGui`)
	G.Name = `NHSayBubble`
	G.Adornee = Head
	G.Size = UDim2.fromOffset(220, 46)
	G.StudsOffset = Vector3.new(0, 2.6, 0)
	G.MaxDistance = 60
	G.AlwaysOnTop = false
	G.LightInfluence = 0
	local F = Instance.new(`Frame`)
	F.AnchorPoint = Vector2.new(0.5, 1)
	F.Position = UDim2.fromScale(0.5, 1)
	F.Size = UDim2.fromOffset(0, 30)
	F.AutomaticSize = Enum.AutomaticSize.X
	F.BackgroundColor3 = if Theme then Theme.Colors.Well else Color3.fromRGB(22, 18, 24)
	F.BackgroundTransparency = 0.12
	F.Parent = G
	local C = Instance.new(`UICorner`) C.CornerRadius = UDim.new(0, 6) C.Parent = F
	local S = Instance.new(`UIStroke`) S.Color = if Theme then Theme.Colors.GoldDeep else Color3.fromRGB(150, 110, 50) S.Thickness = 1.5 S.Parent = F
	local P = Instance.new(`UIPadding`) P.PaddingLeft = UDim.new(0, 10) P.PaddingRight = UDim.new(0, 10) P.Parent = F
	local L = Instance.new(`TextLabel`)
	L.BackgroundTransparency = 1
	L.Size = UDim2.new(0, 0, 1, 0)
	L.AutomaticSize = Enum.AutomaticSize.X
	L.Text = Text
	L.TextSize = 17
	local Body = Theme and Theme.Fonts and Theme.Fonts.Body
	if typeof(Body) == `Font` then L.FontFace = Body elseif typeof(Body) == `EnumItem` then L.Font = Body else L.Font = Enum.Font.Garamond end
	L.TextColor3 = if Theme then Theme.Colors.Text else Color3.fromRGB(235, 225, 210)
	L.Parent = F
	G.Parent = Head
	-- fade out after the line's time (NHSayFor: longer lines stay up longer)
	local For = tonumber(M:GetAttribute(`NHSayFor`)) or BUBBLE_TIME
	local St = State[M]
	if St then St.TalkUntil = os.clock() + math.min(For, 2.5) end
	task.delay(For, function()
		if not G.Parent then return end
		for I = 1, 10 do
			F.BackgroundTransparency = 0.12 + I * 0.088
			L.TextTransparency = I / 10
			S.Transparency = I / 10
			task.wait(0.03)
		end
		G:Destroy()
	end)
end

local function track(M: Model)
	if State[M] then return end
	local Neck = neckOf(M)
	if not Neck then return end
	State[M] = { Neck = Neck; C0 = Neck.C0; Yaw = 0; Pitch = 0 }
	M:GetAttributeChangedSignal(`NHSayAt`):Connect(function()
		bubble(M)
		local Text = M:GetAttribute(`NHSay`)
		if typeof(Text) == `string` then voice(M, Text) end
	end)
	M:GetAttributeChangedSignal(`NHFidgetAt`):Connect(function()
		if M:GetAttribute(`NHFidget`) == `Stretch` then stretch(M) end
	end)
	M.Destroying:Connect(function() State[M] = nil end)
end

local function step(Dt: number)
	local Cam = workspace.CurrentCamera
	local CamPos = Cam and Cam.CFrame.Position or Vector3.zero
	local Now = workspace:GetServerTimeNow()
	local Quick = Players.LocalPlayer:GetAttribute(`NHReducedMotion`) == true
	for M, S in State do
		if not M.Parent then State[M] = nil continue end
		local Torso = M:FindFirstChild(`Torso`)
		local Head = M:FindFirstChild(`Head`)
		if not (Torso and Head and Torso:IsA(`BasePart`) and Head:IsA(`BasePart`)) then continue end
		if (Torso.Position - CamPos).Magnitude > RANGE then continue end
		local WantYaw, WantPitch = 0, 0
		local At = M:GetAttribute(`NHLookAt`)
		local Until = tonumber(M:GetAttribute(`NHLookUntil`)) or 0
		if typeof(At) == `Vector3` and Until > Now then
			local From = Torso.Position + Torso.CFrame.UpVector * 1.5
			local D = Torso.CFrame:VectorToObjectSpace(At - From)
			if D.Magnitude > 0.5 then
				D = D.Unit
				WantYaw = math.clamp(math.atan2(-D.X, -D.Z), -MAX_YAW, MAX_YAW)
				WantPitch = math.clamp(math.asin(math.clamp(D.Y, -1, 1)), -MAX_PITCH, MAX_PITCH)
			end
		end
		local Rate = if Quick then 18 else 7
		local A = 1 - math.exp(-Rate * Dt)
		S.Yaw += (WantYaw - S.Yaw) * A
		S.Pitch += (WantPitch - S.Pitch) * A
		-- R6 neck: its C0 is turned so the joint's Z is up and X is sideways
		-- a little nod while they talk, so you can tell who's speaking
		local Nod = if (S.TalkUntil or 0) > os.clock() and not Quick then math.sin(os.clock() * 9) * 0.045 else 0
		S.Neck.C0 = S.C0 * CFrame.Angles(-(S.Pitch + Nod), 0, S.Yaw)
	end
end

function Shared.OnStart()
	task.spawn(function()
		local Folder = workspace:WaitForChild(`NHStudents`, 120)
		if not Folder then return end
		for _, M in Folder:GetChildren() do if M:IsA(`Model`) then task.spawn(track, M) end end
		Folder.ChildAdded:Connect(function(M)
			if not M:IsA(`Model`) then return end
			M:WaitForChild(`Torso`, 5)
			track(M)
		end)
	end)
	RunService.RenderStepped:Connect(step)
end

-- tests read this
function Shared.Debug(M: Model)
	local S = State[M]
	return S and { Yaw = S.Yaw; Pitch = S.Pitch }
end

return Shared
