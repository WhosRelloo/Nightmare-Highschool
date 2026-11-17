--[[
	Dialogue (client). Bottom-of-screen box: speaker name in their faction colour, role and
	your relationship, a typewriter line, and numbered choices (keys 1-9, click or tap).
	Clicking the text finishes the line; walking away (or the Goodbye reply) leaves. The server decides everything;
	this only shows what it sends and returns the chosen index.
	Talk cinematic (1.35.1): when a conversation opens with an NPC (Data.Model), the camera eases into an over-the-shoulder
	shot of them (a slightly narrower field of view, thin letterbox bars, a soft depth of field, a slow drift), and eases
	back when it ends. Reduce Motion: a cut, no drift. Skipped in the cinematic view, the main menu, first person, and
	when the NPC is far away.
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local UserInputService = game:GetService(`UserInputService`)
local TweenService = game:GetService(`TweenService`)
local StarterGui = game:GetService(`StarterGui`)

---| Modules |---

local Packets = require(ReplicatedStorage.Remotes.Packets)
local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`)) -- NH UI kit
local KitColors = Kit.Theme.Colors

local Player = Players.LocalPlayer
local CHARS_PER_SECOND = 55

local NUMBER_KEYS = {
	[Enum.KeyCode.One] = 1, [Enum.KeyCode.Two] = 2, [Enum.KeyCode.Three] = 3,
	[Enum.KeyCode.Four] = 4, [Enum.KeyCode.Five] = 5, [Enum.KeyCode.Six] = 6,
	[Enum.KeyCode.Seven] = 7, [Enum.KeyCode.Eight] = 8, [Enum.KeyCode.Nine] = 9,
}

local RELATION_COLORS = {
	Hostile = Color3.fromRGB(230, 80, 80);
	Rival = Color3.fromRGB(240, 150, 90);
	Acquaintance = Color3.fromRGB(200, 200, 200);
	Friendly = Color3.fromRGB(130, 210, 140);
	Trusted = Color3.fromRGB(120, 190, 255);
}

local Local = {}
local Shared = {}

local Ui = nil
local Current = nil -- { Id, Choices, Typing, FullText }
local BackpackWas = nil

---| talk cinematic (1.35.1) |---

local RunService = game:GetService(`RunService`)
local Lighting = game:GetService(`Lighting`)
local Shot = nil :: any -- { Model, Home (camera CFrame), Fov, Conn, Bars, Dof, T0 }

function Local.Head(M: Model?): BasePart?
	return M and (M:FindFirstChild(`Head`) or M:FindFirstChild(`HumanoidRootPart`)) :: BasePart?
end

function Local.ShotBars(On: boolean)
	local PG = Player:FindFirstChild(`PlayerGui`)
	if not PG then return end
	local G = PG:FindFirstChild(`NHTalkBars`)
	if not G then
		G = Instance.new(`ScreenGui`)
		G.Name = `NHTalkBars`
		G.IgnoreGuiInset = true
		G.ResetOnSpawn = false
		G.DisplayOrder = 3 -- under the dialogue box and the HUD
		G:SetAttribute(`ShowInCinematic`, true)
		for _, Top in { true, false } do
			local B = Instance.new(`Frame`)
			B.Name = if Top then `Top` else `Bottom`
			B.BorderSizePixel = 0
			B.BackgroundColor3 = Color3.new(0, 0, 0)
			B.AnchorPoint = Vector2.new(0, if Top then 0 else 1)
			B.Position = UDim2.fromScale(0, if Top then 0 else 1)
			B.Size = UDim2.fromScale(1, 0)
			B.Parent = G
		end
		G.Parent = PG
	end
	G.Enabled = true
	for _, B in G:GetChildren() do
		if B:IsA(`Frame`) then
			TweenService:Create(B, TweenInfo.new(0.45, Enum.EasingStyle.Quint, Enum.EasingDirection.Out), { Size = UDim2.fromScale(1, if On then 0.055 else 0) }):Play()
		end
	end
end

-- where the camera sits: over your shoulder, looking at the NPC's face
function Local.ShotFrame(M: Model): CFrame?
	local Char = Player.Character
	local Me, Them = Local.Head(Char), Local.Head(M)
	if not (Me and Them) then return nil end
	local Flat = (Them.Position - Me.Position) * Vector3.new(1, 0, 1)
	if Flat.Magnitude < 0.5 then return nil end
	local Fwd = Flat.Unit
	local Right = Fwd:Cross(Vector3.yAxis)
	local At = Me.Position - Fwd * 5.5 + Right * 4.3 + Vector3.new(0, 1, 0)
	local Look = Them.Position + Vector3.new(0, 0.2, 0) + Right * 0.4
	return CFrame.lookAt(At, Look)
end

function Local.ShotIn(M: any)
	if Shot or typeof(M) ~= `Instance` or not M:IsA(`Model`) or not M.Parent then return end
	if Player:GetAttribute(`InMainMenu`) == true then return end
	local Cine = script.Parent:FindFirstChild(`Cinematic`)
	local Ok, C = pcall(function() return Cine and require(Cine) end)
	if Ok and C and C.IsOn and C.IsOn() then return end
	local Cam = workspace.CurrentCamera
	local Char = Player.Character
	local Me, Them = Local.Head(Char), Local.Head(M)
	if not (Cam and Me and Them) or (Me.Position - Them.Position).Magnitude > 20 then return end
	if (Cam.CFrame.Position - Me.Position).Magnitude < 1 then return end -- first person: leave it alone
	local Frame = Local.ShotFrame(M)
	if not Frame then return end
	local Calm = Kit.ReducedMotion()
	Shot = { Model = M; Home = Cam.CFrame; Fov = Cam.FieldOfView; Type = Cam.CameraType; T0 = os.clock() }
	Cam.CameraType = Enum.CameraType.Scriptable
	local Fov = math.max(40, Shot.Fov - 12)
	if Calm then
		Cam.CFrame = Frame
		Cam.FieldOfView = Fov
	else
		TweenService:Create(Cam, TweenInfo.new(0.7, Enum.EasingStyle.Quint, Enum.EasingDirection.Out), { CFrame = Frame; FieldOfView = Fov }):Play()
	end
	Local.ShotBars(true)
	-- a soft depth of field on the NPC
	local Dof = Instance.new(`DepthOfFieldEffect`)
	Dof.Name = `NHTalkDof`
	Dof.FocusDistance = (Frame.Position - Them.Position).Magnitude
	Dof.InFocusRadius = 5
	Dof.NearIntensity = 0
	Dof.FarIntensity = 0
	Dof.Parent = Lighting
	TweenService:Create(Dof, TweenInfo.new(0.6), { FarIntensity = 0.35 }):Play()
	Shot.Dof = Dof
	-- hold the frame (they may shift a little), with a slow drift
	Shot.Conn = RunService.RenderStepped:Connect(function()
		if not Shot then return end
		if not (M.Parent and Player.Character) then Local.ShotOut() return end
		local F = Local.ShotFrame(M)
		if not F then return end
		if os.clock() - Shot.T0 < 0.75 and not Calm then return end -- the ease-in tween is still running
		local Drift = if Calm then CFrame.identity else CFrame.new(math.sin((os.clock() - Shot.T0) * 0.25) * 0.25, 0, -math.min(os.clock() - Shot.T0, 20) * 0.02)
		Cam.CFrame = Cam.CFrame:Lerp(F * Drift, 0.08)
	end)
end

function Local.ShotOut()
	local S = Shot
	if not S then return end
	Shot = nil
	if S.Conn then S.Conn:Disconnect() end
	Local.ShotBars(false)
	if S.Dof then
		TweenService:Create(S.Dof, TweenInfo.new(0.3), { FarIntensity = 0 }):Play()
		task.delay(0.35, function() S.Dof:Destroy() end)
	end
	local Cam = workspace.CurrentCamera
	if not Cam then return end
	local function Done()
		if Shot then return end -- a new conversation took the camera again
		Cam.FieldOfView = S.Fov
		Cam.CameraType = if S.Type == Enum.CameraType.Scriptable then Enum.CameraType.Custom else S.Type
	end
	if Kit.ReducedMotion() then Done() return end
	local Tw = TweenService:Create(Cam, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.InOut), { CFrame = S.Home; FieldOfView = S.Fov })
	Tw.Completed:Connect(Done)
	Tw:Play()
end

function Local.Build()
	local Gui = Instance.new(`ScreenGui`)
	Gui.Name = `Dialogue`
	Gui.ResetOnSpawn = false
	Gui.DisplayOrder = 8
	Gui.Enabled = false
	Kit.AutoScale(Gui, { min = 0.8, max = 1.1; phoneScale = 0.66 }) -- shrink a little on short screens so it never covers the view

	-- Box: auto-height ornate kit frame. The art lives in Box.NHDecor; content in Box.Inner.
	local Box = Instance.new(`Frame`)
	Box.Name = `Box`
	Box.AnchorPoint = Vector2.new(0.5, 1)
	-- Compact and low so it doesn't cover the middle of the screen (the bottom HUD hides while talking).
	Box.Position = UDim2.new(0.5, 0, 1, -14)
	Box.Size = UDim2.new(0.42, 0, 0, 0)
	Box.AutomaticSize = Enum.AutomaticSize.Y
	Box.BackgroundTransparency = 1
	Box.Parent = Gui
	local Max = Instance.new(`UISizeConstraint`)
	Max.MinSize = Vector2.new(340, 0)
	Max.MaxSize = Vector2.new(580, 320)
	Max.Parent = Box
	local _, Decor = Kit.Decorate(Box, { ornamentScale = 0.7 })

	local Inner = Instance.new(`Frame`)
	Inner.Name = `Inner`
	Inner.BackgroundTransparency = 1
	Inner.Size = UDim2.new(1, 0, 0, 0)
	Inner.AutomaticSize = Enum.AutomaticSize.Y
	Inner.ZIndex = 2
	Inner.Parent = Box
	local Pad = Instance.new(`UIPadding`)
	Pad.PaddingTop = UDim.new(0, 16)
	Pad.PaddingBottom = UDim.new(0, 14)
	Pad.PaddingLeft = UDim.new(0, 24)
	Pad.PaddingRight = UDim.new(0, 24)
	Pad.Parent = Inner
	local Layout = Instance.new(`UIListLayout`)
	Layout.SortOrder = Enum.SortOrder.LayoutOrder
	Layout.Padding = UDim.new(0, 4)
	Layout.Parent = Inner

	local Header = Instance.new(`Frame`)
	Header.Name = `Header`
	Header.LayoutOrder = 1
	Header.Size = UDim2.new(1, 0, 0, 24)
	Header.BackgroundTransparency = 1
	Header.Parent = Inner

	local Name = Kit.Text({ Name = `Speaker`, Font = Kit.Theme.Fonts.Title, TextSize = 19, AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.new(0, 0, 1, 0), Parent = Header })
	Kit.Emboss(Name, Color3.fromRGB(150, 135, 120), 1.4)

	local Role = Kit.Text({
		Name = `Role`, AnchorPoint = Vector2.new(1, 0), Position = UDim2.fromScale(1, 0), Size = UDim2.new(0.6, 0, 1, 0),
		TextSize = 17, TextXAlignment = Enum.TextXAlignment.Right, TextColor3 = KitColors.TextDim, Parent = Header,
	})

	local Rule = Instance.new(`Frame`)
	Rule.Name = `Rule`
	Rule.LayoutOrder = 2
	Rule.Size = UDim2.new(0.5, 0, 0, 1)
	Rule.BorderSizePixel = 0
	Rule.BackgroundColor3 = KitColors.IronDim
	Rule.Parent = Inner
	local RuleFade = Instance.new(`UIGradient`)
	RuleFade.Transparency = NumberSequence.new(0, 1)
	RuleFade.Parent = Rule

	local Line = Instance.new(`TextButton`)
	Line.Name = `Line`
	Line.LayoutOrder = 3
	Line.AutoButtonColor = false
	Line.BackgroundTransparency = 1
	Line.Size = UDim2.new(1, 0, 0, 0)
	Line.AutomaticSize = Enum.AutomaticSize.Y
	Line.Font = Kit.Theme.Fonts.Body
	Line.TextSize = 18
	Line.TextWrapped = true
	Line.TextXAlignment = Enum.TextXAlignment.Left
	Line.TextYAlignment = Enum.TextYAlignment.Top
	Line.TextColor3 = KitColors.Text
	Line.TextStrokeTransparency = 0.75
	Line.Parent = Inner

	local Choices = Instance.new(`Frame`)
	Choices.Name = `Choices`
	Choices.LayoutOrder = 4
	Choices.BackgroundTransparency = 1
	Choices.Size = UDim2.new(1, 0, 0, 0)
	Choices.AutomaticSize = Enum.AutomaticSize.Y
	Choices.Parent = Inner
	local ChoiceLayout = Instance.new(`UIListLayout`)
	ChoiceLayout.SortOrder = Enum.SortOrder.LayoutOrder
	ChoiceLayout.Padding = UDim.new(0, 4)
	ChoiceLayout.Parent = Choices

	local Hint = Kit.Text({
		Name = `Hint`, LayoutOrder = 5, Size = UDim2.new(1, 0, 0, 18), Font = Kit.Theme.Fonts.Title, TextSize = 15,
		TextXAlignment = Enum.TextXAlignment.Right, TextColor3 = KitColors.TextFaint, Parent = Inner,
		Text = ``,
	})
	-- for the keyboard, a gamepad or a touch screen (Kit.InputKind), and again when that changes
	local function HintText()
		local Kind = if Kit.InputKind then Kit.InputKind() else (if UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled then `Touch` else `Keyboard`)
		Hint.Text = if Kind == `Touch` then `Tap a reply`
			elseif Kind == `Gamepad` then Kit.PadText("D-pad to choose  ·  {A} to reply  ·  {B} to leave")
			else `1-9 reply  ·  click text to skip  ·  walk away to leave`
	end
	HintText()
	if Kit.InputKindChanged then Kit.InputKindChanged:Connect(HintText) end

	Gui.Parent = Player:WaitForChild(`PlayerGui`)
	Line.Activated:Connect(function() Local.Skip() end)
	return { Gui = Gui; Box = Box; Decor = Decor; Name = Name; Role = Role; Line = Line; Choices = Choices }
end

function Local.SetBackpack(Open: boolean)
	if Open then
		if BackpackWas == nil then
			local Ok, Was = pcall(function() return StarterGui:GetCoreGuiEnabled(Enum.CoreGuiType.Backpack) end)
			BackpackWas = if Ok then Was else true
		end
		pcall(function() StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.Backpack, false) end)
	elseif BackpackWas ~= nil then
		local Was = BackpackWas
		BackpackWas = nil
		pcall(function() StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.Backpack, Was) end)
	end
end

function Local.ShowChoices(Labels: { string })
	for _, Child in Ui.Choices:GetChildren() do
		if Child:IsA(`TextButton`) then Child:Destroy() end
	end
	for Index, Text in Labels do
		Kit.ChoiceRow({
			Name = `Choice{Index}`; index = Index; text = tostring(Text); LayoutOrder = Index; height = 40;
			onClick = function() Local.Choose(Index) end;
			Parent = Ui.Choices;
		})
	end
	Ui.Choices.Visible = true
end

function Local.Skip()
	if Current and Current.Typing then
		Current.Typing = false
	end
end

function Local.Choose(Index: number)
	if not Current or Current.Waiting then return end
	if Current.Typing then
		Local.Skip()
		return
	end
	if not Current.Choices[Index] then return end
	Current.Waiting = true
	Packets.DialogueAction:Fire({ Id = Current.Id; Choice = Index })
end

function Local.Leave()
	if not Current then return end
	Packets.DialogueAction:Fire({ Id = Current.Id; Close = true })
	Local.Hide()
end

local ShowToken = 0
local Hiding = false
local BOX_HOME = UDim2.new(0.5, 0, 1, -14)
local BOX_LOW = UDim2.new(0.5, 0, 1, 26)

function Local.Hide()
	Current = nil
	if Ui and Ui.Gui.Enabled then
		-- slide back down and fade, then switch off (unless a new line opened meanwhile)
		Hiding = true
		ShowToken += 1
		local My = ShowToken
		local Box = Ui.Gui:FindFirstChild(`Box`)
		if Box then
			if not Kit.ReducedMotion() then
				TweenService:Create(Box, TweenInfo.new(0.2, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Position = BOX_LOW }):Play()
			end
			Kit.FadeOut(Box, 0.2)
		end
		task.delay(0.22, function()
			if My == ShowToken and Ui and not Current then
				Hiding = false
				Ui.Gui.Enabled = false
				if Box then Box.Position = BOX_HOME end
			end
		end)
	end
	Local.SetBackpack(false)
	Player:SetAttribute(`InDialogue`, nil)
	Local.ShotOut()
end

function Local.ShowNode(Data)
	Ui = Ui or Local.Build()
	local Color = typeof(Data.Color) == `Color3` and Data.Color or Color3.new(1, 1, 1)

	Ui.Name.Text = tostring(Data.Speaker or ``)
	Ui.Name.TextColor3 = Color
	Ui.Decor:SetFrameColor(Color:Lerp(KitColors.Iron, 0.55))
	local Relation = tostring(Data.Relationship or ``)
	local RelColor = RELATION_COLORS[Relation]
	Ui.Role.Text = if RelColor
		then `{Data.Role or ``}  ·  <font color="#{RelColor:ToHex()}">{Relation}</font>`
		else tostring(Data.Role or ``)

	local Choices = if typeof(Data.Choices) == `table` then Data.Choices else {}
	local Text = tostring(Data.Text or ``)
	local Node = { Id = Data.Id; Choices = Choices; Typing = true }
	Current = Node

	Ui.Choices.Visible = false
	Ui.Line.Text = Text
	Ui.Line.MaxVisibleGraphemes = 0
	local Box = Ui.Gui:FindFirstChild(`Box`)
	-- speaker rim: a soft glow along the top edge in the speaker's colour, brighter when the speaker changes
	if Box then
		local Rim = Box:FindFirstChild(`SpeakerRim`)
		if not Rim then
			Rim = Instance.new(`ImageLabel`)
			Rim.Name = `SpeakerRim`
			Rim.BackgroundTransparency = 1
			local Glow = Kit.Theme.Images and Kit.Theme.Images.Glow
			Rim.Image = if typeof(Glow) == `number` then `rbxassetid://{Glow}` else tostring(Glow or ``)
			Rim.ScaleType = Enum.ScaleType.Stretch
			Rim.AnchorPoint = Vector2.new(0.5, 0.5)
			Rim.Position = UDim2.new(0.5, 0, 0, 0)
			Rim.Size = UDim2.new(0.9, 0, 0, 30)
			Rim.ImageTransparency = 1
			Rim.ZIndex = 1
			Rim.Parent = Box
		end
		local NewSpeaker = Rim:GetAttribute(`Speaker`) ~= tostring(Data.Speaker or ``)
		Rim:SetAttribute(`Speaker`, tostring(Data.Speaker or ``))
		Rim.ImageColor3 = Color
		if NewSpeaker then
			Rim.ImageTransparency = 0.25
			TweenService:Create(Rim, TweenInfo.new(0.8, Enum.EasingStyle.Sine), { ImageTransparency = 0.62 }):Play()
		end
	end
	local Opening = not Ui.Gui.Enabled or Hiding -- a line arriving mid-hide re-opens the box
	Hiding = false
	ShowToken += 1
	Ui.Gui.Enabled = true
	if Opening and Box then
		-- slide up into place and fade in (Reduce Motion: fade only)
		Box.Position = if Kit.ReducedMotion() then BOX_HOME else BOX_LOW
		Kit.FadeIn(Box, 0.22)
		TweenService:Create(Box, TweenInfo.new(0.28, Enum.EasingStyle.Quint, Enum.EasingDirection.Out), { Position = BOX_HOME }):Play()
	end
	Local.SetBackpack(true)
	Player:SetAttribute(`InDialogue`, true)
	if Opening or not Shot then Local.ShotIn(Data.Model) end

	task.spawn(function()
		local Total = utf8.len(Text) or #Text
		local Started = os.clock()
		while Current == Node and Node.Typing do
			local Shown = math.floor((os.clock() - Started) * CHARS_PER_SECOND)
			if Shown >= Total then break end
			Ui.Line.MaxVisibleGraphemes = Shown
			task.wait()
		end
		if Current ~= Node then return end
		Node.Typing = false
		Ui.Line.MaxVisibleGraphemes = -1
		Local.ShowChoices(Choices)
	end)
end

function Shared.IsOpen(): boolean
	return Current ~= nil
end

function Shared.OnStart()
	Packets.DialogueEvent.OnClientEvent:Connect(function(Data)
		if typeof(Data) ~= `table` then return end
		if Data.Type == `Node` then
			Local.ShowNode(Data)
		elseif Data.Type == `Close` then
			if Current and (Data.Id == nil or Data.Id == Current.Id) then Local.Hide() end
		end
	end)

	UserInputService.InputBegan:Connect(function(Input, Processed)
		if not Current or Processed then return end
		local Index = NUMBER_KEYS[Input.KeyCode]
		if Index then
			Local.Choose(Index)
		elseif Input.KeyCode == Enum.KeyCode.Escape or Input.KeyCode == Enum.KeyCode.ButtonB then
			Local.Leave()
		end
	end)

	Player.CharacterAdded:Connect(function() if Current then Local.Hide() end end)
end

return Shared
