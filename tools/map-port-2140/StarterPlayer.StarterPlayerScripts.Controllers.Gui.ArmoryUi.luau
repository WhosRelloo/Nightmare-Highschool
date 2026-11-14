--[[
	ArmoryUi (client). Controllers.Gui.ArmoryUi                                     (owner, 2026-11-12)
	The armoury window, opened by the armourer's prompt (attribute NHArmoryShop; Services.Features.Armory).
	  Fists     every student's first class, free.
	  Katana    sold for Yen (Config.Armory.Stock). Buying puts it in your weapons; switch to it at a class locker
	            (Gui.ClassLocker), which only offers the classes you own.
	  Claws     shown, locked for now.
	Closes when you walk away (Config.Armory.Range). Built from the UI kit (Panel, ItemSlot, Button, Plate, Text), like
	the kit counters (Gui.KitUi).
]]
local Players = game:GetService(`Players`)
local ProximityPromptService = game:GetService(`ProximityPromptService`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)

local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))
local ArmoryCfg = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`Armory`))

local Player = Players.LocalPlayer
local Theme = Kit.Theme
local C = Theme.Colors
local Fonts = Theme.Fonts
local YEN = `\u{A5}`
local RARITY = { Fist = `Common`; Katana = `Rare`; Claws = `Epic` }

local Shared = {}
local Local = {}
local Ui = nil
local OpenAt: BasePart? = nil
local Inflight = false
local Tab = `Classes` -- (2.14.0) or `Gear`: the hand gear tab
local GEAR_RARITY = { HandWraps = `Common`; WeightedGloves = `Rare`; BrassKnuckles = `Epic` }

function Local.Ask(Name: string, ...)
	local F = ReplicatedStorage:FindFirstChild(`NHArmory`)
	local R = F and F:GetAttribute(`Ready`) and F:FindFirstChild(Name)
	if not R or Inflight then return nil end
	Inflight = true
	local Ok, A, B = pcall(R.InvokeServer, R, ...)
	Inflight = false
	if not Ok then return nil end
	return A, B
end

function Local.Label(Parent: Instance, Text: string, Size: number, Props)
	local T = Kit.Text({ Text = Text; TextSize = Size; TextColor3 = C.Text; TextWrapped = true; RichText = true;
		TextXAlignment = Enum.TextXAlignment.Left; TextYAlignment = Enum.TextYAlignment.Top; Parent = Parent })
	for K, V in Props or {} do T[K] = V end
	return T
end

-- the weapon in 3D in its slot: the katana's back model, the claws' kit; fists have none
function Local.ModelFor(Class: string): Instance?
	local Src = nil
	if Class == `Claws` then
		local W = ReplicatedStorage:FindFirstChild(`Assets`) and ReplicatedStorage.Assets:FindFirstChild(`Weapons`)
		local F = W and W:FindFirstChild(`Claws`)
		Src = F and F:FindFirstChild(`Kit`)
	else
		local Ok, W = pcall(function() return require(ReplicatedStorage.Config.Weapons)[Class] end)
		Src = Ok and W and W.Model and (W.Model.Back or W.Model.Handle) or nil
	end
	if not (Src and Src:IsA(`Instance`)) then return nil end
	local M = Src:Clone()
	for _, D in M:GetDescendants() do
		if D:IsA(`JointInstance`) or D:IsA(`Constraint`) or D:IsA(`BaseScript`) or D:IsA(`ParticleEmitter`) or D:IsA(`Trail`) or D:IsA(`Beam`) then
			D:Destroy()
		elseif D:IsA(`BasePart`) then
			D.Anchored = true
		end
	end
	return M
end

function Local.View(Slot: GuiObject, Class: string)
	local M = Local.ModelFor(Class)
	if not M then return end
	local V = Instance.new(`ViewportFrame`)
	V.Name = `NHView`
	V.BackgroundTransparency = 1
	V.AnchorPoint = Vector2.new(0.5, 0.5)
	V.Position = UDim2.fromScale(0.5, 0.47)
	V.Size = UDim2.fromScale(0.8, 0.8)
	V.ZIndex = 6
	V.Ambient = Color3.fromRGB(210, 200, 190)
	V.LightColor = Color3.fromRGB(255, 240, 220)
	V.LightDirection = Vector3.new(-0.4, -1, -0.8)
	local Cam = Instance.new(`Camera`)
	Cam.FieldOfView = 30
	M.Parent = V
	-- frame the visible parts only (the katana's Back is an invisible 2x2x1 root with the meshes welded under it)
	local Min, Max = Vector3.one * math.huge, -Vector3.one * math.huge
	local Parts = M:GetDescendants()
	table.insert(Parts, M)
	for _, P in Parts do
		if P:IsA(`BasePart`) and P.Transparency < 1 then
			for _, Sx in { -0.5, 0.5 } do for _, Sy in { -0.5, 0.5 } do for _, Sz in { -0.5, 0.5 } do
				local W = P.CFrame:PointToWorldSpace(P.Size * Vector3.new(Sx, Sy, Sz))
				Min, Max = Min:Min(W), Max:Max(W)
			end end end
		end
	end
	if Min.X == math.huge then return end
	local Center, Size = (Min + Max) / 2, Max - Min
	local R = math.max(Size.X, Size.Y, Size.Z)
	Cam.CFrame = CFrame.lookAt(Center + Vector3.new(-0.7, 0.45, -1.0).Unit * R * 1.9, Center)
	Cam.Parent = V
	V.CurrentCamera = Cam
	V.Parent = Slot
end

function Local.Build()
	local G = Instance.new(`ScreenGui`)
	G.Name = `NHArmory`
	G.ResetOnSpawn = false
	G.DisplayOrder = 12
	G.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	G.Enabled = false
	G.Parent = Player:WaitForChild(`PlayerGui`)
	Kit.AutoScale(G)
	local _, Api = Kit.Panel({ title = ArmoryCfg.Shop.Name; Name = `Panel`; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5);
		Size = UDim2.fromOffset(760, 410); Parent = G })
	local Body = Api.Content
	local Sub = Local.Label(Body, ``, 17, { Name = `Sub`; TextColor3 = C.TextDim; Size = UDim2.new(1, -200, 0, 24); Position = UDim2.fromOffset(8, 0) })
	local _, YenApi = Kit.Plate({ text = `{YEN} 0`; Size = UDim2.fromOffset(150, 34); AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -8, 0, -4); Parent = Body })
	local Grid = Instance.new(`Frame`)
	Grid.Name = `Grid`
	Grid.BackgroundTransparency = 1
	Grid.Position = UDim2.fromOffset(0, 40)
	Grid.Size = UDim2.new(1, 0, 1, -100)
	local L = Instance.new(`UIGridLayout`)
	L.CellSize = UDim2.fromOffset(220, 240)
	L.CellPadding = UDim2.fromOffset(16, 10)
	L.HorizontalAlignment = Enum.HorizontalAlignment.Center
	L.SortOrder = Enum.SortOrder.LayoutOrder
	L.Parent = Grid
	Grid.Parent = Body
	local Status = Local.Label(Body, ``, 17, { Name = `Status`; TextColor3 = C.Gold; TextXAlignment = Enum.TextXAlignment.Center;
		Size = UDim2.new(1, -220, 0, 24); Position = UDim2.new(0, 10, 1, -44) })
	Kit.Button({ text = `Close`; style = `ghost`; Size = UDim2.fromOffset(160, 40); AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -8, 1, -52); Parent = Body;
		onClick = function() Shared.Close() end })
	-- (2.14.0, combat concept 16) two tabs: the classes, and hand gear for fists
	local Tabs = {}
	for I, Name in { `Classes`, `Gear` } do
		local _, B = Kit.Button({ text = if Name == `Gear` then `Hand gear` else `Classes`; style = `ghost`; textSize = 15;
			Size = UDim2.fromOffset(120, 32); Position = UDim2.fromOffset(8 + (I - 1) * 128, 28); Parent = Body;
			onClick = function() Tab = Name Shared.Open(OpenAt) end })
		Tabs[Name] = B
	end
	Grid.Position = UDim2.fromOffset(0, 68)
	Grid.Size = UDim2.new(1, 0, 1, -128)
	Ui = { Gui = G; Panel = Api; Grid = Grid; Yen = YenApi; Status = Status; Sub = Sub; Tabs = Tabs }
end

function Local.Cell(Order: number, It, Current: boolean)
	local Cell = Instance.new(`Frame`)
	Cell.Name = It.Class
	Cell.BackgroundTransparency = 1
	Cell.LayoutOrder = Order
	Cell.Parent = Ui.Grid
	local Slot = Kit.ItemSlot({ item = { name = if Local.ModelFor(It.Class) then `` else It.Name; rarity = RARITY[It.Class] or `Common` }; size = 88;
		AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, 0, 0, 2); Parent = Cell })
	Local.View(Slot, It.Class)
	Local.Label(Cell, It.Name, 18, { Font = Fonts.Title; TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(0, 96); Size = UDim2.new(1, 0, 0, 22) })
	Local.Label(Cell, It.Text or ``, 14, { TextColor3 = C.TextDim; TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(4, 120); Size = UDim2.new(1, -8, 0, 54) })
	local B
	if It.Locked then
		B = { text = `Locked`; style = `ghost`; enabled = false }
	elseif It.Owned then
		B = { text = if Current then `Your class` else `Owned`; style = `ghost`; enabled = false }
	else
		B = { text = `Buy {YEN}{It.Price}`; style = `gold`; onClick = function() Local.Buy(It.Class) end }
	end
	Kit.Button({ text = B.text; style = B.style; enabled = B.enabled ~= false; textSize = 15; Size = UDim2.fromOffset(212, 38);
		Position = UDim2.fromOffset(4, 182); Parent = Cell; onClick = B.onClick })
end

-- (2.14.0) a hand gear cell: its icon (a group upload; the name until it's set), what it does, buy / wear / take off
function Local.GearCell(Order: number, It)
	local Cell = Instance.new(`Frame`)
	Cell.Name = It.Id
	Cell.BackgroundTransparency = 1
	Cell.LayoutOrder = Order
	Cell.Parent = Ui.Grid
	local HasIcon = typeof(It.Icon) == `string` and It.Icon ~= ``
	local Slot = Kit.ItemSlot({ item = { name = if HasIcon then `` else It.Name; rarity = GEAR_RARITY[It.Id] or `Common` }; size = 88;
		AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, 0, 0, 2); Parent = Cell })
	if HasIcon then
		local I = Instance.new(`ImageLabel`)
		I.Name = `NHIcon`
		I.BackgroundTransparency = 1
		I.Image = It.Icon
		I.AnchorPoint = Vector2.new(0.5, 0.5)
		I.Position = UDim2.fromScale(0.5, 0.5)
		I.Size = UDim2.fromScale(0.82, 0.82)
		I.ZIndex = 6
		I.Parent = Slot
	end
	Local.Label(Cell, It.Name, 18, { Font = Fonts.Title; TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(0, 96); Size = UDim2.new(1, 0, 0, 22) })
	Local.Label(Cell, It.Text or ``, 14, { TextColor3 = if It.Contraband then C.Gold else C.TextDim; TextXAlignment = Enum.TextXAlignment.Center;
		Position = UDim2.fromOffset(4, 120); Size = UDim2.new(1, -8, 0, 58) })
	local B
	if It.Worn then
		B = { text = `Take off`; style = `ghost`; onClick = function() Local.Gear(`Remove`, It.Id) end }
	elseif It.Owned then
		B = { text = `Wear`; style = `gold`; onClick = function() Local.Gear(`Wear`, It.Id) end }
	else
		B = { text = `Buy {YEN}{It.Price}`; style = `gold`; onClick = function() Local.Gear(`Buy`, It.Id) end }
	end
	Kit.Button({ text = B.text; style = B.style; textSize = 15; Size = UDim2.fromOffset(212, 38);
		Position = UDim2.fromOffset(4, 182); Parent = Cell; onClick = B.onClick })
end

function Local.Gear(Action: string, Id: string)
	local Ok, Msg = Local.Ask(`Gear`, Action, Id)
	if Ok then pcall(Kit.PlaySound, `Confirm`) end
	Shared.Open(OpenAt, Msg or (if Ok == nil then `One moment...` else nil))
end

function Local.Fill(Info)
	for _, Ch in Ui.Grid:GetChildren() do if Ch:IsA(`Frame`) then Ch:Destroy() end end
	Ui.Yen.Label.Text = `{YEN} {Info.Yen or 0}`
	local Shop = Info.Shop or ArmoryCfg.Shop
	if Ui.Panel.SetTitle then Ui.Panel:SetTitle(Shop.Name) end
	Ui.Sub.Text = `<i>{Shop.Sub}. {Shop.Text}</i>`
	if Tab == `Gear` and Info.Gear then
		for I, It in Info.Gear do Local.GearCell(I, It) end
	else
		for I, It in Info.Items or {} do Local.Cell(I, It, Info.Weapon == It.Class) end
	end
	-- the active tab reads as pressed
	for Name, B in Ui.Tabs or {} do
		pcall(function() B.Label.TextColor3 = if Name == Tab then C.Gold else C.TextDim end)
	end
end

function Local.Buy(Class: string)
	local Ok, Msg = Local.Ask(`Buy`, Class)
	if Ok then pcall(Kit.PlaySound, `Confirm`) end
	Shared.Open(OpenAt, Msg or (if Ok == nil then `One moment...` else nil))
end

function Shared.Open(At: Instance?, Msg: string?)
	local Info = Local.Ask(`Info`)
	if typeof(Info) ~= `table` then return end
	if not Ui then Local.Build() end
	OpenAt = if At and At:IsA(`BasePart`) then At else OpenAt
	Local.Fill(Info)
	Ui.Status.Text = Msg or (if Info.Loaded then `` else `Your record isn't loaded yet.`)
	if not Ui.Gui.Enabled then pcall(Kit.PlaySound, `Tick`) end
	Ui.Gui.Enabled = true
end

function Shared.Close()
	OpenAt = nil
	if Ui then Ui.Gui.Enabled = false end
end

function Shared.IsOpen(): boolean
	return Ui ~= nil and Ui.Gui.Enabled
end

function Shared.OnStart()
	ProximityPromptService.PromptTriggered:Connect(function(Prompt)
		-- any other prompt (the class locker beside the counter) closes the armoury, so its window isn't covered
		if Prompt:GetAttribute(`NHArmoryShop`) then Shared.Open(Prompt.Parent) else Shared.Close() end
	end)
	local Acc = 0
	RunService.Heartbeat:Connect(function(Dt)
		Acc += Dt
		if Acc < 0.4 then return end
		Acc = 0
		if not Shared.IsOpen() then return end
		local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`)
		if not (Root and OpenAt) or (Root.Position - OpenAt.Position).Magnitude > ArmoryCfg.Range + 2 or Player:GetAttribute(`InMainMenu`) == true then
			Shared.Close()
		end
	end)
end

return Shared
