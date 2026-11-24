--[[ StaffConsole.Tools (client): the console's own-client tools, moved from the 1.18 desk (AdminPanel) unchanged:
	Fly (WASD / Space / Ctrl, Shift for speed), Noclip, ESP (names + health through walls), Ctrl+click teleport, Stop
	spectating, and the Inspect card (Features.Admin's Inspect remote). Level 2 (the Test side), except Stop
	spectating (level 1, the Student section). No OnStart: StaffConsole calls Init. ]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local Player = Players.LocalPlayer
local Tools = {}
local Run = nil :: any
local Inited = false
local On = { Fly = false; Noclip = false; Esp = false; ClickTp = false }
local Conns = {}
local CRIMSON = Color3.fromRGB(200, 40, 60) -- the desk's Theme.Colors.Crimson / Gold, inlined so this module needs no UI kit
local GOLD = Color3.fromRGB(235, 205, 120)

local function root()
	local C = Player and Player.Character
	return C and C:FindFirstChild(`HumanoidRootPart`), C and C:FindFirstChildWhichIsA(`Humanoid`)
end

local function setFly(on: boolean)
	On.Fly = on
	if Conns.Fly then Conns.Fly:Disconnect() Conns.Fly = nil end
	local R, H = root()
	if not (R and H) then return end
	local att = R:FindFirstChild(`NHFlyAtt`)
	if not on then
		for _, n in { `NHFlyAtt`, `NHFlyVel`, `NHFlyGyro` } do local x = R:FindFirstChild(n) if x then x:Destroy() end end
		H.PlatformStand = false
		return
	end
	att = Instance.new(`Attachment`); att.Name = `NHFlyAtt`; att.Parent = R
	local lv = Instance.new(`LinearVelocity`); lv.Name = `NHFlyVel`; lv.Attachment0 = att; lv.MaxForce = 1e6
	lv.RelativeTo = Enum.ActuatorRelativeTo.World; lv.VectorVelocity = Vector3.zero; lv.Parent = R
	local ao = Instance.new(`AlignOrientation`); ao.Name = `NHFlyGyro`; ao.Mode = Enum.OrientationAlignmentMode.OneAttachment
	ao.Attachment0 = att; ao.Responsiveness = 60; ao.MaxTorque = 1e6; ao.Parent = R
	H.PlatformStand = true
	Conns.Fly = RunService.RenderStepped:Connect(function()
		local cam = workspace.CurrentCamera
		if not (R.Parent and cam) then return end
		local d = Vector3.zero
		local cf = cam.CFrame
		if UserInputService:IsKeyDown(Enum.KeyCode.W) then d += cf.LookVector end
		if UserInputService:IsKeyDown(Enum.KeyCode.S) then d -= cf.LookVector end
		if UserInputService:IsKeyDown(Enum.KeyCode.D) then d += cf.RightVector end
		if UserInputService:IsKeyDown(Enum.KeyCode.A) then d -= cf.RightVector end
		if UserInputService:IsKeyDown(Enum.KeyCode.Space) then d += Vector3.yAxis end
		if UserInputService:IsKeyDown(Enum.KeyCode.LeftControl) then d -= Vector3.yAxis end
		local speed = UserInputService:IsKeyDown(Enum.KeyCode.LeftShift) and 140 or 60
		lv.VectorVelocity = if d.Magnitude > 0 then d.Unit * speed else Vector3.zero
		ao.CFrame = CFrame.lookAt(Vector3.zero, Vector3.new(cf.LookVector.X, 0, cf.LookVector.Z).Unit)
	end)
end

local function setNoclip(on: boolean)
	On.Noclip = on
	if Conns.Noclip then Conns.Noclip:Disconnect() Conns.Noclip = nil end
	if on then
		Conns.Noclip = RunService.Stepped:Connect(function()
			local C = Player.Character
			if not C then return end
			for _, p in C:GetDescendants() do if p:IsA(`BasePart`) and p.CanCollide then p.CanCollide = false end end
		end)
	end
end

local EspFolder
local function setEsp(on: boolean)
	On.Esp = on
	if Conns.Esp then Conns.Esp:Disconnect() Conns.Esp = nil end
	if EspFolder then EspFolder:Destroy() EspFolder = nil end
	if not on then return end
	EspFolder = Instance.new(`Folder`); EspFolder.Name = `NHAdminEsp`; EspFolder.Parent = workspace.CurrentCamera
	local function refresh()
		if not EspFolder then return end
		EspFolder:ClearAllChildren()
		for _, P in Players:GetPlayers() do
			local C = P.Character
			if P ~= Player and C and C:FindFirstChild(`Head`) then
				local h = Instance.new(`Highlight`); h.Adornee = C; h.FillTransparency = 0.8; h.FillColor = CRIMSON
				h.OutlineColor = GOLD; h.DepthMode = Enum.HighlightDepthMode.AlwaysOnTop; h.Parent = EspFolder
				local b = Instance.new(`BillboardGui`); b.Adornee = C.Head; b.Size = UDim2.fromOffset(200, 40); b.StudsOffset = Vector3.new(0, 2.6, 0)
				b.AlwaysOnTop = true; b.Parent = EspFolder
				local hum = C:FindFirstChildWhichIsA(`Humanoid`)
				local l = Instance.new(`TextLabel`)
				l.BackgroundTransparency = 1; l.Font = Enum.Font.Garamond; l.TextSize = 16; l.TextColor3 = GOLD; l.RichText = true
				l.Text = `{P.DisplayName}  ·  {hum and math.floor(hum.Health) or 0} HP`; l.Parent = b
				l.Size = UDim2.fromScale(1, 1); l.TextStrokeTransparency = 0.3
			end
		end
	end
	refresh()
	local t = 0
	Conns.Esp = RunService.Heartbeat:Connect(function(dt) t += dt if t > 1 then t = 0 refresh() end end)
end


local function card(Id, Section, Title, Help, Icon, Level, Target, Synonyms)
	return { Id = Id; Side = if Level >= 2 then "Test" else "Moderate"; Section = Section; Title = Title; Help = Help; Icon = Icon;
		Level = Level; Target = Target; Args = {}; Danger = false; Synonyms = Synonyms; Local = true }
end
Tools.Defs = {
	card("ToolFly", "Self", "Fly", "WASD, Space up, Ctrl down, Shift faster (again to land)", "Speed", 2, "none", { "fly" }),
	card("ToolNoclip", "Self", "Noclip", "Walk through walls (again to stop)", "Teleport", 2, "none", { "clip" }),
	card("ToolEsp", "Self", "ESP", "Names and health through walls", "Spectate", 2, "none", { "wallhack", "esp" }),
	card("ToolClickTp", "Self", "Ctrl+click teleport", "Hold Ctrl and click the world to go there", "Teleport", 2, "none", { "click tp" }),
	card("ToolUnspectate", "Student", "Stop spectating", "Your camera back on you", "Spectate", 1, "none", { "unspectate" }),
	card("ToolInspect", "Progress", "Inspect", "Their loaded slot, read only (in the side panel)", "SecProgress", 2, "required", { "inspector" }),
}

function Tools.State() return table.clone(On) end

function Tools.Do(Id: string, _Values: any, Selected: number?): (boolean, string)
	if Id == "ToolFly" then On.Fly = not On.Fly setFly(On.Fly) return true, if On.Fly then "Flying" else "Landed" end
	if Id == "ToolNoclip" then On.Noclip = not On.Noclip setNoclip(On.Noclip) return true, if On.Noclip then "Noclip on" else "Noclip off" end
	if Id == "ToolEsp" then On.Esp = not On.Esp setEsp(On.Esp) return true, if On.Esp then "ESP on" else "ESP off" end
	if Id == "ToolClickTp" then On.ClickTp = not On.ClickTp return true, if On.ClickTp then "Ctrl+click teleport on" else "Ctrl+click teleport off" end
	if Id == "ToolUnspectate" then
		local H = Player.Character and Player.Character:FindFirstChildWhichIsA("Humanoid")
		if H then workspace.CurrentCamera.CameraSubject = H end
		return true, "Camera back on you"
	end
	if Id == "ToolInspect" then return Selected ~= nil, if Selected then "Inspecting" else "Pick a student first" end
	return false, "Unknown tool"
end

function Tools.Inspect(UserId: number): any
	local F = ReplicatedStorage:FindFirstChild("NHAdmin")
	if not F then return nil end
	local Ok, R = pcall(F.Inspect.InvokeServer, F.Inspect, UserId)
	return if Ok then R else nil
end

function Tools.Init(RunFn: any)
	Run = RunFn
	if Inited or not Player then return end
	Inited = true
	UserInputService.InputBegan:Connect(function(input, gp)
		if On.ClickTp and input.UserInputType == Enum.UserInputType.MouseButton1 and not gp
			and UserInputService:IsKeyDown(Enum.KeyCode.LeftControl) then
			local m = Player:GetMouse()
			if m.Hit and Run then Run("TeleportTo", { Position = m.Hit.Position }) end
		end
	end)
	task.spawn(function()
		local F = ReplicatedStorage:WaitForChild(`NHAdmin`, 60)
		if not F then return end
		F:WaitForChild(`Client`).OnClientEvent:Connect(function(kind, target)
			if kind == `Spectate` and typeof(target) == `Instance` then
				local c = target.Character
				local h = c and c:FindFirstChildWhichIsA(`Humanoid`)
				if h then workspace.CurrentCamera.CameraSubject = h end
			end
		end)
	end)
	Player.CharacterAdded:Connect(function() if On.Fly then task.wait(1) setFly(true) end end)
end

return Tools
