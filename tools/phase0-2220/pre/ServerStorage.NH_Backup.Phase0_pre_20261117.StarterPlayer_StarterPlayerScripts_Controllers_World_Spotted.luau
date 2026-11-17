--[[
	Spotted (client). Controllers.World.Spotted  -- VFX P0-9 "Spotted!" (vault: Docs/VFX-Design-Bible.md)

	Only the chased student sees any of this:
		NHFx "Spotted"    { Monitor = Model, Reason }   orange outline on the monitor, a "!" over its head,
		                                                 a whistle and a pulse of the existing Darken vignette
		NHFx "SpottedEnd" { Monitor = Model, Result }   Caught: 0.3 s desaturate and a red "!" stamp
		                                                 Escaped: the "!" turns into a "?" and everything fades
	The server also sets Monitor:SetAttribute("MonitorTarget", UserId) for the whole chase; when it stops naming
	this player the alert clears, whatever the reason (went to class, downed, monitor off duty, left).

	Stealth zones (VFX P1-10 / P1-11), driven by the player's StealthZone / Detection attributes:
		Watcher awareness   a "?" over the zone's watcher from 0.25 detection, a crimson "!" from 0.75 (with a
		                    pulse of the vignette, which follows the Vignette setting)
		Flashlight          watchers carry a torch (SpotLight) after dark, for everyone
		NHFx "ThrownOut"    { Watcher, Zone }  fade to black with a THROWN OUT stamp while the server walks you out
]]

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local SoundService = game:GetService(`SoundService`)
local TweenService = game:GetService(`TweenService`)
local Lighting = game:GetService(`Lighting`)

local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))
local Fx = require(script.Parent.Parent:WaitForChild(`Fx`))

local Player = Players.LocalPlayer
local StealthConfig = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`Stealth`))
local Theme = Kit.Theme
local C = Theme.Colors

local ORANGE = Color3.fromRGB(255, 150, 45)
local WHISTLE = { Id = `rbxassetid://9117261163`, Volume = 0.4, Length = 0.9 } -- Pealess Whistle, Fox 40 (Pro Sound Effects)
local MAX_CHASE = 75 -- safety: never leave an alert up longer than this

local Local = {}
local Shared = {}

local Active = {} :: { [Model]: { Highlight: Highlight, Board: BillboardGui, Mark: TextLabel, Conn: RBXScriptConnection?, Token: number } }
local Tokens = 0

function Local.Sound(Def)
	local S = Instance.new(`Sound`)
	S.SoundId = Def.Id
	S.Volume = Def.Volume
	local Master = SoundService:FindFirstChild(`NH_Master`)
	local Group = Master and Master:FindFirstChild(`NH_Effects`)
	if Group and Group:IsA(`SoundGroup`) then S.SoundGroup = Group end
	S.Parent = SoundService
	S:Play()
	task.delay(Def.Length, function() S:Destroy() end)
end

-- reuse the combat-owned Darken vignette (never modified; called like its other users)
function Local.Vignette()
	local Char = Player.Character
	if not Char then return end
	pcall(function()
		local Darken = require(Player.PlayerScripts.Controllers.StateController.ScreenFX.Darken)
		Darken(Char, { User = Char; T = if Fx.FlashScale() < 1 then 0.6 else 0.35; tim = 0.18; Reset = true })
	end)
end

function Local.Clear(Model: Model, FadeTime: number?)
	local A = Active[Model]
	if not A then return end
	Active[Model] = nil
	if A.Conn then A.Conn:Disconnect() end
	local T = FadeTime or 0.5
	TweenService:Create(A.Highlight, TweenInfo.new(T, Enum.EasingStyle.Sine), { OutlineTransparency = 1 }):Play()
	TweenService:Create(A.Mark, TweenInfo.new(T, Enum.EasingStyle.Sine), { TextTransparency = 1; TextStrokeTransparency = 1 }):Play()
	task.delay(T + 0.05, function()
		A.Highlight:Destroy()
		A.Board:Destroy()
	end)
end

function Local.Start(D)
	if typeof(D) ~= `table` or typeof(D.Monitor) ~= `Instance` or not D.Monitor:IsA(`Model`) then return end
	local Model = D.Monitor :: Model
	if Active[Model] then Local.Clear(Model, 0) end
	local Head = Model:FindFirstChild(`Head`) or Model.PrimaryPart
	if not Head then return end

	local H = Instance.new(`Highlight`)
	H.Name = `NHSpotted`
	H.FillTransparency = 1
	H.OutlineColor = ORANGE
	H.OutlineTransparency = 1
	H.DepthMode = Enum.HighlightDepthMode.AlwaysOnTop
	H.Adornee = Model
	H.Parent = Model
	TweenService:Create(H, TweenInfo.new(0.15), { OutlineTransparency = 0 }):Play()

	local Board = Instance.new(`BillboardGui`)
	Board.Name = `NHSpottedMark`
	Board.AlwaysOnTop = true
	Board.LightInfluence = 0
	Board.Size = UDim2.fromOffset(64, 64)
	Board.StudsOffset = Vector3.new(0, 2.6, 0)
	Board.Adornee = Head
	Board.ResetOnSpawn = false
	local Mark = Kit.Text({
		Name = `Mark`; Text = `!`; Font = Theme.Fonts.Title; TextSize = 58; TextColor3 = ORANGE;
		TextStrokeColor3 = C.Ink; TextStrokeTransparency = 0.1; TextXAlignment = Enum.TextXAlignment.Center;
		Size = UDim2.fromScale(1, 1); Parent = Board;
	})
	Board.Parent = Player:WaitForChild(`PlayerGui`)
	Fx.Pop(Mark, 1.6, 0.2)

	Tokens += 1
	local Token = Tokens
	local Entry = { Highlight = H; Board = Board; Mark = Mark; Token = Token; Conn = nil }
	Active[Model] = Entry
	-- clears on every exit: the server stops naming us, the model goes, or the safety timeout
	Entry.Conn = Model:GetAttributeChangedSignal(`MonitorTarget`):Connect(function()
		if Model:GetAttribute(`MonitorTarget`) ~= Player.UserId then
			task.delay(0.15, function() -- let a SpottedEnd (caught / escaped) land first
				if Active[Model] == Entry then Local.Clear(Model) end
			end)
		end
	end)
	Model.AncestryChanged:Once(function()
		if Active[Model] == Entry then Local.Clear(Model, 0) end
	end)
	task.delay(MAX_CHASE, function()
		if Active[Model] == Entry then Local.Clear(Model) end
	end)

	Local.Sound(WHISTLE)
	Local.Vignette()
end

function Local.Stamp(Word: string?, Sub: string?)
	local Gui = Player.PlayerGui:FindFirstChild(`NHSpottedStamp`)
	if not Gui then
		Gui = Instance.new(`ScreenGui`)
		Gui.Name = `NHSpottedStamp`
		Gui.ResetOnSpawn = false
		Gui.DisplayOrder = 12
		Kit.AutoScale(Gui)
		Gui.Parent = Player.PlayerGui
	end
	local Root = Instance.new(`Frame`)
	Root.BackgroundTransparency = 1
	Root.AnchorPoint = Vector2.new(0.5, 0.5)
	Root.Position = UDim2.fromScale(0.5, 0.42)
	Root.Size = UDim2.fromOffset(300, 190)
	Root.Parent = Gui
	local Bang = Kit.Text({
		Name = `Bang`; Text = `!`; Font = Theme.Fonts.Title; TextSize = 96; TextColor3 = C.Danger;
		TextStrokeColor3 = C.Ink; TextStrokeTransparency = 0; TextXAlignment = Enum.TextXAlignment.Center;
		Size = UDim2.new(1, 0, 0, 100); Parent = Root;
	})
	Kit.Text({
		Name = `Word`; Text = Word or `CAUGHT`; Font = Theme.Fonts.Title; TextSize = 30; TextColor3 = C.Danger:Lerp(C.Text, 0.2);
		TextStrokeColor3 = C.Ink; TextStrokeTransparency = 0.1; TextXAlignment = Enum.TextXAlignment.Center;
		Position = UDim2.fromOffset(0, 100); Size = UDim2.new(1, 0, 0, 36); Parent = Root;
	})
	if Sub then
		Kit.Text({
			Name = `Sub`; Text = Sub; Font = Theme.Fonts.Body; TextSize = Theme.Sizes.TextBody; TextColor3 = C.Text;
			TextStrokeColor3 = C.Ink; TextStrokeTransparency = 0.3; TextXAlignment = Enum.TextXAlignment.Center; TextWrapped = true;
			AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, 0, 0, 138); Size = UDim2.fromOffset(520, 44); Parent = Root;
		})
	end
	Kit.FadeIn(Root, 0.12)
	Fx.Pop(Bang, 1.6, 0.2)
	pcall(Kit.PlaySound, `Stamp`)
	task.delay(if Sub then 1.9 else 1.3, function()
		local Out = Kit.FadeOut(Root, 0.4)
		if Out then Out.Completed:Wait() end
		Root:Destroy()
	end)
end

function Local.Desaturate()
	local CC = Instance.new(`ColorCorrectionEffect`)
	CC.Name = `NHCaught`
	CC.Saturation = 0
	CC.Parent = Lighting
	local Down = TweenService:Create(CC, TweenInfo.new(0.15, Enum.EasingStyle.Quad), { Saturation = -0.8 })
	Down:Play()
	task.delay(0.3, function()
		local Up = TweenService:Create(CC, TweenInfo.new(0.5, Enum.EasingStyle.Sine), { Saturation = 0 })
		Up.Completed:Connect(function() CC:Destroy() end)
		Up:Play()
	end)
end

function Local.End(D)
	if typeof(D) ~= `table` then return end
	local Model = D.Monitor
	local A = typeof(Model) == `Instance` and Active[Model]
	if D.Result == `Caught` then
		Local.Desaturate()
		Local.Stamp()
		if A then Local.Clear(Model, 0.3) end
	elseif D.Result == `Escaped` then
		if A then
			A.Mark.Text = `?`
			A.Mark.TextColor3 = C.Chalk
			Fx.Pop(A.Mark, 1.3, 0.2)
			TweenService:Create(A.Highlight, TweenInfo.new(0.6, Enum.EasingStyle.Sine), { OutlineTransparency = 1 }):Play()
			if A.Conn then A.Conn:Disconnect() A.Conn = nil end
			local Entry = A
			task.delay(1.2, function()
				if Active[Model] == Entry then Local.Clear(Model, 0.5) end
			end)
		end
	elseif A then
		Local.Clear(Model) -- let off with a warning
	end
end

---| stealth zones: watcher awareness, flashlight, thrown out |---

local AWARE_Q, AWARE_BANG = 0.25, 0.75
local Aware = { Model = nil :: Model?, Board = nil :: BillboardGui?, Mark = nil :: TextLabel?, Level = 0 }

function Local.ZoneWatcher(ZoneName: string): Model?
	local Live = workspace:FindFirstChild(`Live`)
	if not Live then return nil end
	for Id, Zone in StealthConfig.Zones do
		if Zone.Name == ZoneName then
			for _, M in Live:GetChildren() do
				if M:IsA(`Model`) and M:GetAttribute(`WatcherZone`) == Id then return M end
			end
		end
	end
	return nil
end

function Local.AwareClear()
	if Aware.Board then
		local B, M = Aware.Board, Aware.Mark
		Aware.Board, Aware.Mark = nil, nil
		if M then TweenService:Create(M, TweenInfo.new(0.35), { TextTransparency = 1; TextStrokeTransparency = 1 }):Play() end
		task.delay(0.4, function() B:Destroy() end)
	end
	Aware.Model, Aware.Level = nil, 0
end

function Local.AwareStep()
	local Zone = Player:GetAttribute(`StealthZone`)
	local D = Player:GetAttribute(`Detection`) or 0
	local Char = Player.Character
	if not Zone or (Char and Char:GetAttribute(`Hidden`)) then
		if Aware.Board then Local.AwareClear() end
		return
	end
	local Level = if D >= AWARE_BANG then 2 elseif D >= AWARE_Q then 1 else 0
	local Model = Local.ZoneWatcher(Zone)
	if Level == 0 or not Model then
		if Aware.Board then Local.AwareClear() end
		return
	end
	if Aware.Model ~= Model or not (Aware.Board and Aware.Board.Parent) then
		Local.AwareClear()
		local Head = Model:FindFirstChild(`Head`)
		if not Head then return end
		local Board = Instance.new(`BillboardGui`)
		Board.Name = `NHWatcherAware`
		Board.AlwaysOnTop = true
		Board.LightInfluence = 0
		Board.Size = UDim2.fromOffset(56, 56)
		Board.StudsOffset = Vector3.new(0, 3.2, 0)
		Board.MaxDistance = 90
		Board.Adornee = Head
		Board.ResetOnSpawn = false
		local Mark = Kit.Text({
			Name = `Mark`; Text = `?`; Font = Theme.Fonts.Title; TextSize = 50; TextColor3 = C.Chalk;
			TextStrokeColor3 = C.Ink; TextStrokeTransparency = 0.1; TextXAlignment = Enum.TextXAlignment.Center;
			Size = UDim2.fromScale(1, 1); Parent = Board;
		})
		Board.Parent = Player:WaitForChild(`PlayerGui`)
		Aware.Model, Aware.Board, Aware.Mark, Aware.Level = Model, Board, Mark, 0
	end
	if Level ~= Aware.Level and Aware.Mark then
		local Rising = Level > Aware.Level
		Aware.Level = Level
		Aware.Mark.Text = if Level == 2 then `!` else `?`
		Aware.Mark.TextColor3 = if Level == 2 then C.Crimson:Lerp(C.Danger, 0.4) else C.Chalk
		if Rising then
			Fx.Pop(Aware.Mark, if Level == 2 then 1.7 else 1.35, 0.2)
			if Level == 2 then Local.Vignette() end
		end
	end
	-- the "?" firms up as the meter rises, so you can read how close you are
	if Aware.Mark and Level == 1 then
		Aware.Mark.TextTransparency = math.clamp(0.55 - (D - AWARE_Q) * 1.1, 0, 0.55)
	elseif Aware.Mark then
		Aware.Mark.TextTransparency = 0
	end
end

-- torches for watchers after dark (everyone sees them; one light per watcher)
function Local.Torch(Model: Model)
	local Head = Model:WaitForChild(`Head`, 5)
	if not Head or Head:FindFirstChild(`NHTorch`) then return end
	local A = Instance.new(`Attachment`)
	A.Name = `NHTorch`
	A.Position = Vector3.new(0.35, -0.2, -0.6)
	A.Orientation = Vector3.new(-18, 0, 0)
	A.Parent = Head
	local L = Instance.new(`SpotLight`)
	L.Face = Enum.NormalId.Front
	L.Angle = 48
	L.Range = 26
	L.Brightness = 0
	L.Color = Color3.fromRGB(255, 226, 170)
	L.Shadows = true
	L.Parent = A
	task.spawn(function()
		while A.Parent and Model.Parent do
			local T = Lighting.ClockTime
			local Dark = T >= 19.5 or T < 6.5
			local Want = if Dark then 1.8 + math.noise(os.clock() * 1.7, 0.3) * 0.25 else 0
			L.Brightness += (Want - L.Brightness) * 0.25
			L.Enabled = L.Brightness > 0.02
			task.wait(0.1)
		end
	end)
end

function Local.WatchTorches()
	local Live = workspace:WaitForChild(`Live`, 30)
	if not Live then return end
	local function check(M: Instance)
		if M:IsA(`Model`) then
			task.defer(function()
				if M:GetAttribute(`Role`) == `Watcher` then Local.Torch(M) end
			end)
		end
	end
	for _, M in Live:GetChildren() do check(M) end
	Live.ChildAdded:Connect(check)
end

function Local.ThrownOut(D)
	if typeof(D) ~= `table` then return end
	Local.AwareClear()
	if typeof(D.Delay) == `number` and D.Delay > 0 then task.wait(math.min(D.Delay, 3)) end -- the catch animation plays first
	task.spawn(function()
		Fx.Veil(0.3, 0.55, 0.5, C.Ink)
	end)
	Local.Stamp(`THROWN OUT`, `{D.Watcher or `The watcher`} threw you out of the {D.Zone or `room`}.`)
	Local.AwareClear()
end

function Shared.OnStart()
	Fx.On(`Spotted`, Local.Start)
	Fx.On(`SpottedEnd`, Local.End)
	Fx.On(`ThrownOut`, Local.ThrownOut)
	task.spawn(Local.WatchTorches)
	task.spawn(function()
		while true do
			local Ok, Err = pcall(Local.AwareStep)
			if not Ok then
				warn(`[Spotted] aware: {Err}`)
				task.wait(2)
			end
			task.wait(0.1)
		end
	end)
	Player.CharacterAdded:Connect(function()
		for Model in Active do Local.Clear(Model, 0) end
	end)
end

Shared.Test = { Start = Local.Start; End = Local.End; ThrownOut = Local.ThrownOut; Stamp = Local.Stamp; Aware = Aware }

return Shared
