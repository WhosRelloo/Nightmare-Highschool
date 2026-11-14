--[[
	SnackWheel (client). Controllers.Gui.SnackWheel  (inventory QOL, 2026-11-12)

	Owner: "What about holding G?" Hold G (a tap still introduces you: the wheel never opens while an "Introduce
	yourself" prompt is showing) or hold D-pad Right on a gamepad (a tap still steps the hotbar) for a ring of every
	snack you carry, up to 12: favourites first, then your pins. Move the mouse (or the right stick) toward one and let
	go to eat or drink it. Let go in the middle for Best food: the cheapest food you carry that covers the health you're
	missing (Services.Features.Inventory.UseBest). Right click or B cancels.
	Not while you're dead or down, in the main menu, a dialogue, a lesson, a sports match or a drill, or typing.

	The look (owner: "a completely original look, cool, on theme, and animated, with cool markers for each item"): the
	Bell Wheel, baked PBR art from art/ui/hud/make_snack_wheel.py (group 15981569, ART below). A candle halo flickers
	round it, light turns through the rose window, the rune band turns and its runes and the moons breathe. Opening
	springs the wheel up and fans the sockets out from the hub one by one; the clock hand swings to what you aim at, and
	that socket lifts, turns gilt, and a rune ring spins behind it. Letting go drops the snack into the hub and folds the
	wheel shut. Embers drift off it the whole time. Each socket shows the snack in 3D, a ring in its rarity colour, how
	many you carry, and its cooldown draining from the top.
	One render loop sets every visual from the state (open time, the pick, each socket's lift), so nothing is tweened.
]]
local Players = game:GetService(`Players`)
local ProximityPromptService = game:GetService(`ProximityPromptService`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local UserInputService = game:GetService(`UserInputService`)
local Typing = require(game:GetService(`ReplicatedStorage`):WaitForChild(`Packages`):WaitForChild(`Bind`):WaitForChild(`Typing`)) -- (2.1.0) one "is the player typing?" for every key

local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))
local Items = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`Items`))

local Player = Players.LocalPlayer
local Theme = Kit.Theme
local C = Theme.Colors
local Fonts = Theme.Fonts

-- the baked art (group 15981569, uploaded 2026-11-12); 0 = not uploaded yet (a plain stand-in shows)
local ART = {
	WheelRim = 105890871550180; WheelRimGlow = 78046134931925; WheelBand = 73622975432065; WheelBandGlow = 81115412153701;
	WheelDisc = 127664307321099; WheelRays = 102187976579961; WheelHalo = 139808609322673; WheelHub = 100837689049169;
	WheelHand = 137529731077087; WheelMarker = 90789825301811; WheelMarkerLit = 93146562121593; WheelMarkerRim = 99537513739789;
	WheelShade = 132150444488871; WheelSigil = 81282077430601; WheelGlow = 76519726911323; WheelEmber = 135727121185332;
	KitPlate = 97376576287306; -- the kit's ink plate (Config.Kit.Art), for the caption
}

local HOLD = 0.3                -- seconds of holding before the wheel opens
local D = 520                   -- the wheel's design size (px)
local R = D * 0.335             -- socket centres from the middle
local CENTRE = 52               -- px: a cursor inside this picks Best food
local MAX = 12
local EMBERS = 10
local GOLD = Color3.fromRGB(240, 200, 120)
local FLAME = Color3.fromRGB(255, 150, 70)
local KEYS = { [Enum.KeyCode.G] = true; [Enum.KeyCode.DPadRight] = true }

local Shared = {}
local Local = {}
local Ui = nil
local Open = nil -- { Key, Cursor: Vector2, Pick: number (0 = Best food), State, At, Closing, Commit }
local Holding = nil
local Token = 0
local Introduce = {} :: { [ProximityPrompt]: boolean }

---| helpers |---

function Local.Call(Name: string, ...)
	local F = ReplicatedStorage:FindFirstChild(`NHInventory`)
	local Rm = F and F:GetAttribute(`Ready`) and F:FindFirstChild(Name)
	if not Rm then return nil end
	local Ok, A, B = pcall(Rm.InvokeServer, Rm, ...)
	if not Ok then return nil end
	return A, B
end

function Local.Has(Name: string): boolean
	return (ART[Name] or 0) > 0
end

-- an ImageLabel of a baked piece, centred; Fallback (no art yet): a plain round Frame of that colour, or nothing
function Local.Img(Parent: Instance, Name: string, Size: number, Z: number, Fallback: Color3?): GuiObject
	local G
	if Local.Has(Name) then
		G = Instance.new(`ImageLabel`)
		G.Image = `rbxassetid://{ART[Name]}`
		G.BackgroundTransparency = 1
	else
		G = Instance.new(`Frame`)
		G.BackgroundColor3 = Fallback or Color3.new(0, 0, 0)
		G.BackgroundTransparency = if Fallback then 0.2 else 1
		Instance.new(`UICorner`, G).CornerRadius = UDim.new(1, 0)
	end
	G.Name = Name
	G.BorderSizePixel = 0
	G.AnchorPoint = Vector2.new(0.5, 0.5)
	G.Position = UDim2.fromScale(0.5, 0.5)
	G.Size = UDim2.fromOffset(Size, Size)
	G.ZIndex = Z
	G.Parent = Parent
	return G
end

-- set an image's (or stand-in's) transparency
function Local.Alpha(G: GuiObject, T: number)
	if G:IsA(`ImageLabel`) then G.ImageTransparency = T
	elseif G.BackgroundTransparency < 1 or G:GetAttribute(`Solid`) then G:SetAttribute(`Solid`, true) G.BackgroundTransparency = 0.2 + 0.8 * T end
end

function Local.Label(Parent: Instance, Text: string, Size: number, Props)
	local L = Kit.Text({ Text = Text; TextSize = Size; TextColor3 = C.Text; RichText = true; TextWrapped = true;
		TextXAlignment = Enum.TextXAlignment.Center; Parent = Parent })
	for K, V in Props or {} do L[K] = V end
	return L
end

-- the snack's modelled prop (ReplicatedStorage.NHSnacks.<Id>), or a coloured stand-in, in a little 3D view
function Local.View(Parent: GuiObject, It, Z: number): ViewportFrame
	local Lib = ReplicatedStorage:FindFirstChild(`NHSnacks`)
	local Tpl = Lib and Lib:FindFirstChild(It.Id)
	local M
	if Tpl and Tpl:FindFirstChild(`Handle`) then
		M = Tpl:Clone()
		M:PivotTo(CFrame.Angles(0, math.rad(-25), 0))
	else
		M = Instance.new(`Part`)
		M.Color = It.Prop.Color
		M.Material = Enum.Material.SmoothPlastic
		M.Shape = if It.Prop.Shape == `Food` then Enum.PartType.Ball else Enum.PartType.Block
		M.Size = Vector3.new(0.6, 0.6, 0.6)
	end
	for _, Dd in M:GetDescendants() do if Dd:IsA(`BasePart`) then Dd.Anchored = true end end
	if M:IsA(`BasePart`) then M.Anchored = true end
	local V = Instance.new(`ViewportFrame`)
	V.Name = `View`
	V.BackgroundTransparency = 1
	V.AnchorPoint = Vector2.new(0.5, 0.5)
	V.Position = UDim2.fromScale(0.5, 0.5)
	V.Size = UDim2.fromScale(0.64, 0.64)
	V.ZIndex = Z
	V.Ambient = Color3.fromRGB(160, 145, 130)
	V.LightColor = Color3.fromRGB(255, 226, 190)
	V.LightDirection = Vector3.new(-1, -1.4, -0.8)
	M.Parent = V
	local CF, Size
	if M:IsA(`Model`) then CF, Size = M:GetBoundingBox() else CF, Size = M.CFrame, M.Size end
	local Rr = math.max(Size.X, Size.Y, Size.Z)
	local Cam = Instance.new(`Camera`)
	Cam.FieldOfView = 30
	Cam.CFrame = CFrame.lookAt(CF.Position + Vector3.new(0.55, 0.35, -1).Unit * Rr * 2.25, CF.Position)
	Cam.Parent = V
	V.CurrentCamera = Cam
	V.Parent = Parent
	return V
end

-- can the wheel open now?
function Local.Blocked(): boolean
	if Typing.Active() then return true end
	if next(Introduce) ~= nil then return true end
	for _, A in { `InMainMenu`, `InDialogue`, `InSport`, `InDrill` } do if Player:GetAttribute(A) then return true end end
	local Char = Player.Character
	local Hum = Char and Char:FindFirstChildOfClass(`Humanoid`)
	if not Hum or Hum.Health <= 0 then return true end
	for _, A in { `Downed`, `DownedUntil`, `InSport`, `InDrill` } do if Char:GetAttribute(A) then return true end end
	local Gui = Player:FindFirstChild(`PlayerGui`)
	return Gui ~= nil and Gui:FindFirstChild(`Lesson`) ~= nil
end

local function ease(T: number): number -- back out (a little overshoot)
	T = math.clamp(T, 0, 1)
	local S = 1.70158
	return 1 + (S + 1) * (T - 1) ^ 3 + S * (T - 1) ^ 2
end
local function angleTo(A: number, B: number): number -- shortest signed step from A to B (degrees)
	return (B - A + 540) % 360 - 180
end

---| the wheel |---

function Local.Build()
	local G = Instance.new(`ScreenGui`)
	G.Name = `NHSnackWheel`
	G.ResetOnSpawn = false
	G.DisplayOrder = 14
	G.IgnoreGuiInset = true
	G.ZIndexBehavior = Enum.ZIndexBehavior.Global
	G.Enabled = false
	G.Parent = Player:WaitForChild(`PlayerGui`)
	pcall(Kit.AutoScale, G, { fitWidth = D * 1.2; fitHeight = D + 110 })
	local Root = Instance.new(`Frame`)
	Root.Name = `Root`
	Root.BackgroundTransparency = 1
	Root.AnchorPoint = Vector2.new(0.5, 0.5)
	Root.Position = UDim2.new(0.5, 0, 0.5, -24)
	Root.Size = UDim2.fromOffset(D, D)
	Root.Parent = G
	local Pop = Instance.new(`UIScale`)
	Pop.Name = `Pop`
	Pop.Parent = Root
	local W = {
		Gui = G; Root = Root; Pop = Pop; Cells = {}; Embers = {};
		Halo = Local.Img(Root, `WheelHalo`, D * 1.3, 2);
		Disc = Local.Img(Root, `WheelDisc`, D, 3, Color3.fromRGB(40, 10, 16));
		Rays = Local.Img(Root, `WheelRays`, D, 4);
		Band = Local.Img(Root, `WheelBand`, D, 5);
		BandGlow = Local.Img(Root, `WheelBandGlow`, D, 6);
		Rim = Local.Img(Root, `WheelRim`, D, 7);
		RimGlow = Local.Img(Root, `WheelRimGlow`, D, 8);
		HubGlow = Local.Img(Root, `WheelGlow`, D * 0.5, 30);
		Hand = Local.Img(Root, `WheelHand`, D, 31);
		Hub = Local.Img(Root, `WheelHub`, D * 0.28, 32, Color3.fromRGB(70, 52, 30));
	}
	for _, Name in { `Halo`, `Rays`, `BandGlow`, `RimGlow`, `HubGlow` } do
		local Im = W[Name]
		if Im:IsA(`ImageLabel`) then Im.ImageColor3 = if Name == `Rays` then Color3.fromRGB(255, 190, 120) elseif Name == `HubGlow` then GOLD else FLAME end
	end
	if not Local.Has(`WheelHub`) then
		Local.Label(W.Hub, `Best food`, 15, { Font = Fonts.Title; TextColor3 = C.Gold; Size = UDim2.fromScale(1, 1); ZIndex = 33 })
	end
	for I = 1, EMBERS do
		local E = Local.Img(Root, `WheelEmber`, 18, 9)
		if E:IsA(`ImageLabel`) then E.ImageColor3 = FLAME end
		W.Embers[I] = { Img = E; Born = -1e9; Life = 1; A = 0; Speed = 0; Size = 18 }
	end
	-- the caption on the kit's ink plate, under the wheel
	local Plate = Instance.new(if Local.Has(`KitPlate`) then `ImageLabel` else `Frame`)
	Plate.Name = `Caption`
	Plate.AnchorPoint = Vector2.new(0.5, 0)
	Plate.Position = UDim2.new(0.5, 0, 0.5, D / 2 + 2)
	Plate.Size = UDim2.fromOffset(560, 74)
	Plate.ZIndex = 40
	if Plate:IsA(`ImageLabel`) then
		Plate.Image = `rbxassetid://{ART.KitPlate}`
		Plate.BackgroundTransparency = 1
		Plate.ScaleType = Enum.ScaleType.Slice
		Plate.SliceCenter = Rect.new(84, 44, 684, 116)
		Plate.SliceScale = 0.46
	else
		Plate.BackgroundColor3 = Color3.fromRGB(20, 16, 18)
		Plate.BackgroundTransparency = 0.15
	end
	Plate.Parent = G
	local Title = Local.Label(Plate, ``, 19, { Name = `Title`; Font = Fonts.Title; TextColor3 = C.Gold; ZIndex = 41;
		Position = UDim2.new(0, 40, 0, 10); Size = UDim2.new(1, -80, 0, 26); TextStrokeTransparency = 0.6 })
	local Line = Local.Label(Plate, ``, 15, { Name = `Line`; TextColor3 = Color3.fromRGB(150, 205, 140); ZIndex = 41;
		Position = UDim2.new(0, 40, 0, 36); Size = UDim2.new(1, -80, 0, 24); TextStrokeTransparency = 0.7 })
	local Toast = Local.Label(G, ``, 19, { Name = `Toast`; Font = Fonts.Title; AnchorPoint = Vector2.new(0.5, 0.5);
		Position = UDim2.new(0.5, 0, 0.62, 0); Size = UDim2.fromOffset(600, 30); TextColor3 = C.Gold; TextStrokeTransparency = 0.3; Visible = false; ZIndex = 50 })
	W.Caption, W.Title, W.Line, W.Toast = Plate, Title, Line, Toast
	Ui = W
end

function Local.Entries(S): { any }
	local Out = {}
	for Id, N in S.Items or {} do
		local It = Items.ById[Id]
		if It and N > 0 and It.Kind ~= `Trophy` then table.insert(Out, { It = It; N = N }) end
	end
	local Fav, Pin = {}, {}
	for _, Id in S.Fav or {} do Fav[Id] = true end
	for I, Id in S.Pinned or {} do Pin[Id] = I end
	table.sort(Out, function(A, B)
		local FA, FB = Fav[A.It.Id] == true, Fav[B.It.Id] == true
		if FA ~= FB then return FA end
		local PA, PB = Pin[A.It.Id] or 99, Pin[B.It.Id] or 99
		if PA ~= PB then return PA < PB end
		return (A.It.Order or 0) < (B.It.Order or 0)
	end)
	while #Out > MAX do table.remove(Out) end
	return Out
end

-- one socket: its frame turns to face out; the snack, the rarity ring, the count and the cooldown stay upright
function Local.Socket(I: number, E, N: number)
	local A = -90 + (I - 1) * 360 / math.max(N, 1)
	local Spacing = 2 * math.pi * R / math.max(N, 1)
	local S = math.min(124, Spacing * 0.9)
	local F = Instance.new(`Frame`)
	F.Name = `Snack{I}`
	F.BackgroundTransparency = 1
	F.AnchorPoint = Vector2.new(0.5, 0.5)
	F.Size = UDim2.fromOffset(S, S)
	F.ZIndex = 12
	F.Parent = Ui.Root
	local Glow = Local.Img(F, `WheelGlow`, S * 2, 10)
	local Sigil = Local.Img(F, `WheelSigil`, S * 1.45, 11)
	for _, Im in { Glow, Sigil } do if Im:IsA(`ImageLabel`) then Im.ImageColor3 = if Im == Glow then FLAME else GOLD end end
	local Frame = Local.Img(F, `WheelMarker`, S, 13, Color3.fromRGB(110, 80, 40))
	local Lit = Local.Img(F, `WheelMarkerLit`, S, 14)
	Frame.Rotation, Lit.Rotation = A + 90, A + 90
	local Rc = Theme.Rarity and Theme.Rarity[E.It.Rarity] or C.Text
	local Rim = Local.Img(F, `WheelMarkerRim`, S, 15)
	if Rim:IsA(`ImageLabel`) then Rim.ImageColor3 = Rc end
	local View = Local.View(F, E.It, 16)
	-- the cooldown: the well's dark disc, clipped from the top as it drains
	local Clip = Instance.new(`Frame`)
	Clip.Name = `Cool`
	Clip.BackgroundTransparency = 1
	Clip.ClipsDescendants = true
	Clip.AnchorPoint = Vector2.new(0.5, 1)
	Clip.Position = UDim2.new(0.5, 0, 0.5, S / 2)
	Clip.Size = UDim2.fromOffset(S, 0)
	Clip.ZIndex = 17
	Clip.Parent = F
	local Shade = Local.Img(Clip, `WheelShade`, S, 17, Color3.new(0, 0, 0))
	Shade.AnchorPoint = Vector2.new(0.5, 1)
	Shade.Position = UDim2.new(0.5, 0, 1, 0)
	if Shade:IsA(`ImageLabel`) then Shade.ImageTransparency = 0.35 end
	local CoolText = Local.Label(F, ``, 16, { Name = `CoolText`; Font = Enum.Font.GothamBold; ZIndex = 18; Size = UDim2.fromScale(1, 1);
		TextStrokeTransparency = 0.3 })
	-- how many you carry, on a little dark pill at the bottom of the well
	local Count = Local.Label(F, `{E.N}`, 14, { Name = `Count`; Font = Fonts.Title; TextColor3 = C.Gold; ZIndex = 19;
		AnchorPoint = Vector2.new(0.5, 1); Position = UDim2.new(0.5, 0, 0.82, 0); Size = UDim2.fromOffset(34, 18);
		BackgroundTransparency = 0.25; BackgroundColor3 = Color3.fromRGB(14, 10, 12) })
	Instance.new(`UICorner`, Count).CornerRadius = UDim.new(1, 0)
	return { Root = F; It = E.It; N = E.N; Angle = A; Size = S; Glow = Glow; Sigil = Sigil; Frame = Frame; Lit = Lit; Rim = Rim;
		View = View; Clip = Clip; Shade = Shade; CoolText = CoolText; Count = Count; Lift = 0 }
end

function Local.Show(Key: Enum.KeyCode)
	if not Ui then Local.Build() end
	local S = Local.Call(`Get`)
	if typeof(S) ~= `table` then return end
	for _, Cell in Ui.Cells do Cell.Root:Destroy() end
	Ui.Cells = {}
	local List = Local.Entries(S)
	for I, E in List do table.insert(Ui.Cells, Local.Socket(I, E, #List)) end
	Token += 1
	Open = { Key = Key; Cursor = Vector2.zero; Pick = 0; State = S; At = os.clock(); HandAngle = nil }
	Ui.Toast.Visible = false
	Ui.Root.Visible = true
	Ui.Caption.Visible = true
	Ui.Gui.Enabled = true
	pcall(Kit.PlaySound, `Tick`)
end

function Local.Hide()
	if not Open then return end
	Open.Closing = Open.Closing or os.clock()
end

-- what the cursor points at: 0 (the middle: Best food) or a snack
function Local.Pick(): number
	if not (Open and Ui) then return 0 end
	if Open.Cursor.Magnitude < CENTRE or #Ui.Cells == 0 then return 0 end
	local Best, Dist = 0, math.huge
	local Want = math.deg(math.atan2(Open.Cursor.Y, Open.Cursor.X))
	for I, Cell in Ui.Cells do
		local Dd = math.abs(angleTo(Cell.Angle, Want))
		if Dd < Dist then Best, Dist = I, Dd end
	end
	return Best
end

-- every frame while it's on screen: all the motion comes from here
function Local.Render(Dt: number)
	if not (Open and Ui) then return end
	local Now = os.clock()
	local T = Now - Open.At
	local Close = if Open.Closing then math.clamp((Now - Open.Closing) / 0.2, 0, 1) else 0
	if Close >= 1 then
		Open = nil
		Ui.Root.Visible = false
		Ui.Caption.Visible = false
		if not Ui.Toast.Visible then Ui.Gui.Enabled = false end
		return
	end
	if not Open.Closing then Open.Pick = Local.Pick() end
	local A = math.clamp(T / 0.16, 0, 1) * (1 - Close)          -- overall fade
	Ui.Pop.Scale = (0.72 + 0.28 * ease(T / 0.3)) * (1 - 0.15 * Close)
	-- the ambient life: halo flicker, turning light and band, breathing runes and moons
	local Flick = 0.5 + 0.25 * math.sin(Now * 7.3) * math.sin(Now * 3.1 + 1.7) + 0.1 * math.sin(Now * 17)
	Local.Alpha(Ui.Halo, 1 - A * (0.35 + 0.25 * Flick))
	Local.Alpha(Ui.Disc, 1 - A)
	Local.Alpha(Ui.Rays, 1 - A * (0.35 + 0.1 * math.sin(Now * 1.3)))
	Ui.Rays.Rotation = (Now * 4) % 360
	Ui.Band.Rotation = (-Now * 6) % 360
	Ui.BandGlow.Rotation = Ui.Band.Rotation
	Local.Alpha(Ui.Band, 1 - A)
	Local.Alpha(Ui.BandGlow, 1 - A * (0.3 + 0.35 * (0.5 + 0.5 * math.sin(Now * 2.2))))
	Local.Alpha(Ui.Rim, 1 - A)
	Local.Alpha(Ui.RimGlow, 1 - A * (0.25 + 0.3 * (0.5 + 0.5 * math.sin(Now * 1.6 + 1))))
	Local.Alpha(Ui.Hub, 1 - A)
	local OnHub = Open.Pick == 0 and #Ui.Cells > 0
	Local.Alpha(Ui.HubGlow, 1 - A * (if OnHub then 0.55 + 0.15 * math.sin(Now * 5) else 0.12))
	Ui.Hub.Size = UDim2.fromOffset(D * 0.28 * (if OnHub then 1.06 else 1), D * 0.28 * (if OnHub then 1.06 else 1))
	-- the clock hand swings to the pick (a damped follow), and steps back when you aim at the hub
	local Pick = Ui.Cells[Open.Pick]
	local Target = if Pick then Pick.Angle + 90 else (Open.HandAngle or 0)
	Open.HandAngle = Open.HandAngle or Target
	Open.HandAngle += angleTo(Open.HandAngle, Target) * (1 - math.exp(-Dt * 16))
	Ui.Hand.Rotation = Open.HandAngle
	local Tip = R - (if Pick then Pick.Size else 100) * 0.46
	local Hs = Tip * 1024 / 488
	Ui.Hand.Size = UDim2.fromOffset(Hs, Hs)
	Open.HandShow = (Open.HandShow or 0) + ((if Pick then 1 else 0) - (Open.HandShow or 0)) * (1 - math.exp(-Dt * 12))
	Local.Alpha(Ui.Hand, 1 - A * Open.HandShow)
	-- the sockets: fan out one by one, the picked one lifts and lights
	local Server = workspace:GetServerTimeNow()
	local S = Open.State
	for I, Cell in Ui.Cells do
		local Out = ease((T - 0.05 - (I - 1) * 0.035) / 0.28)
		local Commit = Open.Commit == I
		local Fly = if Commit and Open.Closing then math.clamp((Now - Open.Closing) / 0.2, 0, 1) else 0
		local Rad = R * Out * (1 - Fly)
		local Ar = math.rad(Cell.Angle)
		Cell.Root.Position = UDim2.new(0.5, math.cos(Ar) * Rad, 0.5, math.sin(Ar) * Rad)
		Cell.Lift += ((if I == Open.Pick then 1 else 0) - Cell.Lift) * (1 - math.exp(-Dt * 14))
		local L = Cell.Lift
		local Sz = Cell.Size * (1 + 0.14 * L) * (1 - 0.5 * Fly)
		Cell.Root.Size = UDim2.fromOffset(Sz, Sz)
		local Ca = A * math.clamp(Out, 0, 1)
		for _, Im in { Cell.Frame, Cell.Rim } do
			Im.Size = UDim2.fromOffset(Sz, Sz)
			Local.Alpha(Im, 1 - Ca)
		end
		Cell.Lit.Size = UDim2.fromOffset(Sz, Sz)
		Local.Alpha(Cell.Lit, 1 - Ca * L)
		Cell.Glow.Size = UDim2.fromOffset(Sz * 2.1, Sz * 2.1)
		Local.Alpha(Cell.Glow, 1 - Ca * L * (0.55 + 0.2 * math.sin(Now * 6)))
		Cell.Sigil.Size = UDim2.fromOffset(Sz * 1.5, Sz * 1.5)
		Cell.Sigil.Rotation = (Now * 40 + I * 30) % 360
		Local.Alpha(Cell.Sigil, 1 - Ca * L * 0.9)
		Cell.View.ImageTransparency = 1 - Ca
		Cell.Count.TextTransparency = 1 - Ca
		Cell.Count.BackgroundTransparency = 1 - Ca * 0.75
		-- the cooldown
		local Ready = if Cell.It.Kind == `Heal` then S.HealReady elseif Cell.It.Kind == `Buff` then S.BuffReady else nil
		local Left = (Ready or 0) - Server
		local Full = (Items.Cooldown[Cell.It.Kind] or 1) + Items.UseTime
		local Fr = if Left > 0 then math.clamp(Left / Full, 0, 1) else 0
		Cell.Clip.Size = UDim2.fromOffset(Sz, Sz * Fr)
		Cell.Clip.Position = UDim2.new(0.5, 0, 0.5, Sz / 2)
		Cell.Shade.Size = UDim2.fromOffset(Sz * 0.86, Sz * 0.86)
		Cell.Shade.Position = UDim2.new(0.5, 0, 1, -Sz * 0.07)
		Cell.CoolText.Text = if Left > 0 then tostring(math.ceil(Left)) else ``
		Cell.CoolText.TextTransparency = 1 - Ca
	end
	-- embers drift off the rim
	for _, E in Ui.Embers do
		local Age = Now - E.Born
		if Age > E.Life then
			E.Born = Now - math.random() * 0.2
			E.Life = 1.2 + math.random() * 1.4
			E.A = math.random() * 2 * math.pi
			E.Speed = 30 + math.random() * 50
			E.Size = 10 + math.random() * 14
			Age = 0
		end
		local P = Age / E.Life
		local Rr = D * 0.47 + E.Speed * Age
		E.Img.Position = UDim2.new(0.5, math.cos(E.A) * Rr, 0.5, math.sin(E.A) * Rr - 40 * Age)
		E.Img.Size = UDim2.fromOffset(E.Size * (1 - 0.5 * P), E.Size * (1 - 0.5 * P))
		Local.Alpha(E.Img, 1 - A * math.sin(P * math.pi) * 0.9)
	end
	-- the caption
	if Pick then
		Ui.Title.Text = `{Pick.It.Name}  \u{00B7}  you carry {Pick.N}`
		Ui.Line.Text = Items.Describe(Pick.It)
	elseif #Ui.Cells == 0 then
		Ui.Title.Text = `No snacks on you`
		Ui.Line.Text = `The concession stand by the west doors sells them.`
	else
		local Hum = Player.Character and Player.Character:FindFirstChildOfClass(`Humanoid`)
		Ui.Title.Text = `Best food` .. (if Hum then `  \u{00B7}  {math.floor(Hum.Health / math.max(Hum.MaxHealth, 1) * 100 + 0.5)}% health` else ``)
		Ui.Line.Text = `The cheapest food you carry that covers what you're missing.`
	end
	Ui.Title.TextTransparency, Ui.Line.TextTransparency = 1 - A, 1 - A
	Local.Alpha(Ui.Caption, 1 - A)
end

function Local.Toast(Text: string?)
	if not (Ui and Text and Text ~= ``) then return end
	Ui.Toast.Text = Text
	Ui.Toast.Visible = true
	Ui.Toast.TextTransparency = 0
	Ui.Gui.Enabled = true
	local My = Token
	task.spawn(function()
		task.wait(1.4)
		for I = 1, 10 do
			if My ~= Token or not Ui then return end
			Ui.Toast.TextTransparency = I / 10
			task.wait(0.04)
		end
		if My == Token and Ui then
			Ui.Toast.Visible = false
			if not Open then Ui.Gui.Enabled = false end
		end
	end)
end

-- letting go: use the picked snack (or Best food); the snack drops into the hub as the wheel folds
function Local.Commit()
	if not (Open and Ui) or Open.Closing then return end
	local Cell = Ui.Cells[Open.Pick]
	local Empty = #Ui.Cells == 0
	Open.Commit = Open.Pick
	Local.Hide()
	if Empty then return end
	Token += 1
	local Ok, Msg
	if Cell then
		Ok, Msg = Local.Call(`Use`, Cell.It.Id)
		if Ok and not Msg then Msg = Cell.It.Name end
	else
		Ok, Msg = Local.Call(`UseBest`)
	end
	Local.Toast(Msg or (if Ok then nil else `Can't right now.`))
end

---| input |---

function Shared.OnStart()
	-- the art is big: fetch it early so the first open shows the whole wheel
	task.spawn(function()
		local List = {}
		for _, Id in ART do
			if Id > 0 then local Dl = Instance.new(`Decal`) Dl.Texture = `rbxassetid://{Id}` table.insert(List, Dl) end
		end
		pcall(function() game:GetService(`ContentProvider`):PreloadAsync(List) end)
	end)
	ProximityPromptService.PromptShown:Connect(function(P) if P.Name == `NHIntroduce` then Introduce[P] = true end end)
	ProximityPromptService.PromptHidden:Connect(function(P) Introduce[P] = nil end)
	UserInputService.InputBegan:Connect(function(Input, Processed)
		if Open and not Open.Closing then
			if Input.UserInputType == Enum.UserInputType.MouseButton2 or Input.KeyCode == Enum.KeyCode.ButtonB then Local.Hide() end
			return
		end
		if not KEYS[Input.KeyCode] then return end
		if Input.KeyCode == Enum.KeyCode.G and Processed then return end -- a prompt (or a text box) took the press
		Token += 1
		local My = Token
		Holding = { Key = Input.KeyCode; Token = My }
		task.delay(HOLD, function()
			if not (Holding and Holding.Token == My) or (Open and not Open.Closing) or Local.Blocked() then return end
			Local.Show(Holding.Key)
		end)
	end)
	UserInputService.InputEnded:Connect(function(Input)
		if Holding and Input.KeyCode == Holding.Key then Holding = nil end
		if Open and not Open.Closing and Input.KeyCode == Open.Key then Local.Commit() end
	end)
	UserInputService.InputChanged:Connect(function(Input)
		if not Open or Open.Closing then return end
		if Input.UserInputType == Enum.UserInputType.MouseMovement then
			local V = Open.Cursor + Vector2.new(Input.Delta.X, Input.Delta.Y)
			Open.Cursor = if V.Magnitude > R then V.Unit * R else V
		elseif Input.KeyCode == Enum.KeyCode.Thumbstick2 then
			local P = Vector2.new(Input.Position.X, -Input.Position.Y)
			Open.Cursor = if P.Magnitude > 0.35 then P.Unit * R else Vector2.zero
		end
	end)
	RunService.RenderStepped:Connect(function(Dt)
		if not Open then return end
		if not Open.Closing and Local.Blocked() and next(Introduce) == nil then Local.Hide() end -- died, went down, a menu opened
		Local.Render(Dt)
	end)
end

-- Studio tests (runs inside this copy of the module): script.NHSnackWheelTest:Invoke(cmd, n)
-- Open | Pick n (0 = Best food) | Commit | Cancel | State
function Local.TestHook()
	if not RunService:IsStudio() then return end
	local B = Instance.new(`BindableFunction`)
	B.Name = `NHSnackWheelTest`
	B.OnInvoke = function(Cmd, N)
		if Cmd == `Open` then Local.Show(Enum.KeyCode.G) end
		if Cmd == `Pick` and Open and Ui then
			local Cell = Ui.Cells[N or 0]
			Open.Cursor = if Cell then Vector2.new(math.cos(math.rad(Cell.Angle)), math.sin(math.rad(Cell.Angle))) * R else Vector2.zero
		end
		if Cmd == `Commit` then Local.Commit() end
		if Cmd == `Cancel` then Local.Hide() end
		if not (Open and Ui) then return { Open = false; Toast = Ui and Ui.Toast.Visible and Ui.Toast.Text or nil } end
		local Names = {}
		for _, Cell in Ui.Cells do table.insert(Names, `{Cell.It.Id}x{Cell.N}`) end
		return { Open = true; Closing = Open.Closing ~= nil; Pick = Open.Pick; Cells = Names; Title = Ui.Title.Text }
	end
	B.Parent = script
end

Local.TestHook()

return Shared
