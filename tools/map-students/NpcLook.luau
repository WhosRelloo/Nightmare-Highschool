--[[
	NpcLook (client). Controllers.World.NpcLook  (NH core add-on for the Map place, 2026-11-10)

	The client half of the school NPCs' awareness (Services.Features.MapStudents):
	  * Head turning: each student's model carries NHLookAt (Vector3) and NHLookUntil (server time). While it's set,
	    the head turns toward the point over a few frames (clamped like a neck: 75 degrees either side, 35 up or down),
	    and eases back to straight ahead when it lapses. Only students within 140 studs are animated. This runs on
	    each client, so it's smooth at any frame rate and costs the server nothing.
	  * Speech bubbles: NHSay + NHSayAt show a small engraved bubble over the head for NHSayFor seconds (longer lines
	    stay up longer), and the head nods a little while they talk.
	Reduce Motion (NHReducedMotion) keeps the head turns but makes them quicker and shorter.
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

local State = {} :: { [Model]: { Neck: Motor6D, C0: CFrame, Yaw: number, Pitch: number } }

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
	M:GetAttributeChangedSignal(`NHSayAt`):Connect(function() bubble(M) end)
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
