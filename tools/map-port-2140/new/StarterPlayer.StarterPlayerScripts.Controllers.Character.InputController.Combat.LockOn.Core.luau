--[[
	LockOn.Core (client): soft lock-on (combat concept 5, 2.11.0).
	  Mouse and keyboard: middle mouse (Keybinds LockOn) locks on to the nearest opponent in front, and again lets go.
	    While locked you face them between swings (AutoRotate off, the root turned toward them each frame), and a small
	    gold marker sits over their head. It lets go by itself when they drop, go down, get 40+ studs away, or you put
	    your fists away.
	  Gamepad and touch (no free button): aim assist instead. Each swing (Combat.M1 / Combat.M2) turns you to the
	    nearest opponent in front within 9 studs. Mouse players keep their own aim.
	It only turns the character (the client owns its physics); the server's hitboxes follow the real facing.
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local TweenService = game:GetService(`TweenService`)
local UserInputService = game:GetService(`UserInputService`)

local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)

local Core = {}
local Player = Players.LocalPlayer

local RANGE = 30 -- pick a target this close
local KEEP = 40 -- let go past this
local ASSIST = 9 -- aim assist reach
local ASSIST_CONE = 0.34 -- about 70 degrees either side
local BUSY = { `Dodge`, `Sliding`, `Ragdoll`, `Downed`, `Carried`, `Gripped`, `Gripping`, `Paralyzed` }

local Target: Model? = nil
local Conn: RBXScriptConnection? = nil
local Marker: BillboardGui? = nil
local Hum: Humanoid? = nil

local function Usable(M: Model?): boolean
	local H = M and M.Parent and M:FindFirstChildWhichIsA(`Humanoid`)
	if not (H and H.Health > 0 and M:FindFirstChild(`HumanoidRootPart`)) then return false end
	if H:GetAttribute(`Downed`) or M:GetAttribute(`CarriedBy`) or M:GetAttribute(`GrippedBy`) then return false end
	return true
end

local function Flat(V: Vector3): Vector3 return Vector3.new(V.X, 0, V.Z) end

-- the nearest usable model in front (Cone = the minimum dot with your facing; nil = any direction), weighted to the front
function Core.Nearest(Char: Model, Range: number, Cone: number?): Model?
	local Root = Char:FindFirstChild(`HumanoidRootPart`)
	local Live = workspace:FindFirstChild(`Live`)
	if not (Root and Live) then return nil end
	local Look = Flat(Root.CFrame.LookVector)
	if Look.Magnitude < 0.01 then return nil end
	Look = Look.Unit
	local Best, BestScore = nil, math.huge
	for _, M in Live:GetChildren() do
		if M ~= Char and M:IsA(`Model`) and Usable(M) then
			local D = Flat(M.HumanoidRootPart.Position - Root.Position)
			local Dist = D.Magnitude
			if Dist > 0.5 and Dist <= Range then
				local Dot = D.Unit:Dot(Look)
				if not Cone or Dot >= Cone then
					local Score = Dist * (1.6 - Dot)
					if Score < BestScore then Best, BestScore = M, Score end
				end
			end
		end
	end
	return Best
end

local function Face(Char: Model, M: Model?)
	local Root = Char:FindFirstChild(`HumanoidRootPart`)
	local T = M and M:FindFirstChild(`HumanoidRootPart`)
	if not (Root and T) then return end
	local At = Vector3.new(T.Position.X, Root.Position.Y, T.Position.Z)
	if (At - Root.Position).Magnitude < 0.5 then return end
	Root.CFrame = CFrame.lookAt(Root.Position, At)
end

local function MakeMarker(M: Model)
	local Head = M:FindFirstChild(`Head`) or M:FindFirstChild(`HumanoidRootPart`)
	if not Head then return end
	local Kit = require(ReplicatedStorage.UI.Components)
	local B = Instance.new(`BillboardGui`)
	B.Name = `NHLockOn` B.Size = UDim2.fromOffset(18, 18) B.AlwaysOnTop = true B.LightInfluence = 0
	B.StudsOffsetWorldSpace = Vector3.new(0, 2.4, 0) B.Adornee = Head B.MaxDistance = KEEP + 10
	local D = Instance.new(`Frame`)
	D.Name = `Diamond` D.AnchorPoint = Vector2.new(0.5, 0.5) D.Position = UDim2.fromScale(0.5, 0.5)
	D.Size = UDim2.fromOffset(9, 9) D.Rotation = 45 D.BorderSizePixel = 0
	D.BackgroundColor3 = Kit.Theme.Colors.Gold D.BackgroundTransparency = 0.15
	local S = Instance.new(`UIStroke`) S.Color = Color3.fromRGB(14, 10, 12) S.Thickness = 1.5 S.Parent = D
	D.Parent = B
	B.Parent = Player:WaitForChild(`PlayerGui`)
	-- a slow breath, unless Reduce Motion
	if Player:GetAttribute(`NHReducedMotion`) ~= true then
		TweenService:Create(D, TweenInfo.new(0.9, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true), { BackgroundTransparency = 0.5 }):Play()
	end
	Marker = B
end

function Core.Release()
	if Conn then Conn:Disconnect() Conn = nil end
	if Marker then Marker:Destroy() Marker = nil end
	if Hum and Hum.Parent then Hum.AutoRotate = true end
	Hum = nil
	Target = nil
end

function Core.Lock(Char: Model, M: Model)
	Core.Release()
	local H = Char:FindFirstChildWhichIsA(`Humanoid`)
	if not H then return end
	Target, Hum = M, H
	H.AutoRotate = false
	MakeMarker(M)
	Conn = RunService.RenderStepped:Connect(function()
		local Root = Char:FindFirstChild(`HumanoidRootPart`)
		local T = Target and Target:FindFirstChild(`HumanoidRootPart`)
		if not (Char.Parent and H.Health > 0 and Root and T and Usable(Target)) or H:GetAttribute(`Equip`) ~= true
			or Player:GetAttribute(`InMainMenu`) == true or (T.Position - Root.Position).Magnitude > KEEP then
			Core.Release()
			return
		end
		if not StateManager.HasState(Char, BUSY) then Face(Char, Target) end
	end)
end

function Core.Toggle(Char: Model)
	if Target then Core.Release() return end
	local H = Char:FindFirstChildWhichIsA(`Humanoid`)
	if not (H and H:GetAttribute(`Equip`)) then return end
	local M = Core.Nearest(Char, RANGE, -0.2) or Core.Nearest(Char, RANGE, nil)
	if M then Core.Lock(Char, M) end
end

function Core.Locked(): Model? return Target end

-- each swing: face the locked target, or (gamepad / touch) the nearest one in front
function Core.Assist(Char: Model)
	if Target then Face(Char, Target) return end
	if UserInputService.PreferredInput == Enum.PreferredInput.KeyboardAndMouse then return end
	if StateManager.HasState(Char, BUSY) then return end
	local M = Core.Nearest(Char, ASSIST, ASSIST_CONE)
	if M then Face(Char, M) end
end

Player.CharacterAdded:Connect(function() Core.Release() end)

return Core
