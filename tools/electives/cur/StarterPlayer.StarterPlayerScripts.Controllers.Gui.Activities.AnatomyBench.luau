--[[
	Anatomy: The Bench (renderer for Activities type AnatomyBench; Bench mode, full screen).
	A ViewportFrame + WorldModel holds the bench (ReplicatedStorage.Anatomy.Layout: desk, tray, wax, tool roll, candle),
	the specimen (Frog / Raven / Wyvern) and the five tools. Real meshes come from ReplicatedStorage.Anatomy.Models once
	the owner has imported them (tools/electives/stage/anatomy_import.lua); until then each piece is a stand-in built
	from its layout box (bowl body, dome plate, ellipsoid organs), so the lesson plays the same either way.
	The student's arms (an R6 clone of the player, scaled to the bench) reach in from below and play the seated clips in
	ReplicatedStorage.AnatomyClips (published ids in Clips.Ids; KeyframeSequenceProvider only for a clip with no id).

	Input: click a tool on the roll (or its tag, or keys 1-5) to pick it up: it follows the pointer, tip first. Click a
	target to use it: the Key and the Driver turn while held (a hold ring fills every 0.25 s); the Scalpel traces the seam
	(press on the plate, draw round, release); the Tweezers lift an organ, which then rides on their tips until you click
	its outline on the Specimen card. Right-click, Q or B puts the tool down: on the roll, or on the desk where you point.
	The server judges everything (ServerStorage.Activities.AnatomyBench); this only shows it.
	API: Bench.new(Content, Payload, Api) -> :Update(Reply), :PadBack(), :Destroy()
	Studio test hooks (RunService:IsStudio() only): _TestKey(n), _TestUse(Target, Organ?), _TestTrace(points?),
	_TestPlace(Slot), _TestPut(Spot), _TestState(); the live object is _G.NHAnatomyBench while a lesson runs.
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local TweenService = game:GetService(`TweenService`)
local UserInputService = game:GetService(`UserInputService`)
local GuiService = game:GetService(`GuiService`)

local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))
local Layout = require(ReplicatedStorage:WaitForChild(`Anatomy`):WaitForChild(`Layout`))
local Config = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`Anatomy`))
local Electives = require(ReplicatedStorage.Config:WaitForChild(`Electives`))

local C = Kit.Theme.Colors
local Fonts = Kit.Theme.Fonts
local IRON = Color3.fromRGB(22, 18, 20)
local IRON_HI = Color3.fromRGB(46, 38, 36)
local GOLD = C.Gold or Color3.fromRGB(214, 170, 84)
local CRIMSON = C.Crimson or Color3.fromRGB(170, 36, 44)
local INK = C.Text or Color3.fromRGB(236, 226, 206)
local DIM = C.TextDim or Color3.fromRGB(170, 160, 146)

local TURN_EVERY = 0.25        -- seconds of holding per Key/Driver turn
local TRACE_HZ = 30
-- framed so the frog's head sits ~11% from the top and the roll's near edge ~86% down, clear of the tool-button bar
local CAMERA_CF = CFrame.lookAt(Vector3.new(0, 9, 9.75), Vector3.new(0, 0, 1.3))
local HOVER = Vector3.new(0, 0.9, 1.8) -- where a tool in hand waits while the pointer is over the panels
local CAMERA_FOV = 38
local STAGE = Vector3.new(0, 2600, 0) -- where the bench is staged in the world (client-only parts, high over the map)
local WIDE_FOCUS_ARMS = Vector3.new(0, 0, 1.3)
local ARM_SCALE = 3.25         -- the R6 clone scaled so an arm is ~0.65 m at the layout's 10 studs per metre
local SEAT_CF = CFrame.new(0, 2.65, 10.2)
local OPEN_DEG = 95

local TOOL_NAMES = { Key = `Key`; Driver = `Driver`; Loupe = `Loupe`; Scalpel = `Scalpel`; Tweezers = `Tweezers` }
local STEP_TEXT = {
	Unwind = { `Unwind the side key`, `Hold the Key on the side key until it stops (%d/%d)` };
	Unscrew = { `Unscrew the wing plates`, `Hold the Driver on each wing-plate screw (%d/%d)` };
	Inspect = { `Find the hidden seam`, `Look along the plate's edge with the Loupe` };
	Trace = { `Trace the seam`, `With the Scalpel, press on the seam and draw all the way round` };
	Pry = { `Pry the plate open`, `Set the Driver under the plate's lip` };
	Lift = { `Lift out each part`, `Tweezers on a part, then its outline on the Specimen card` };
}
local SLOT_TEXT = { Heart = `Heart`; Lungs = `Lungs`; Gut = `Gut`; Voice = `Voice-box`; Wing = `Wing spring`; Fire = `Fire-gland`;
	HeartA = `Fore heart`; HeartB = `Aft heart` }
local TWIST_TEXT = { Inspection = `Inspection: slips cost double`; Loose = `Loose specimen: the card is blank`;
	Crate = `Crate specimen`; Bet = `Lazzaro's bet` }

local Bench = {}
Bench.__index = Bench

----------------------------------------------------------------------------------------------------- preload
-- The bench clones its props from ReplicatedStorage.Anatomy.Models. Unloaded meshes show up seconds late and
-- unloaded SurfaceAppearances show white, so the assets are fetched ahead: Bench.Preload() warms every model (it runs
-- once, when this module is first required), and Bench.new covers the specimen until its own props are in.
local ContentProvider = game:GetService(`ContentProvider`)
local PRELOAD_WAIT = 10 -- the longest a lesson waits on its props before showing them anyway
local Warmed = false
local function assetsOf(Root: Instance): { Instance }
	local List = {}
	for _, D in Root:GetDescendants() do
		if D:IsA(`MeshPart`) or D:IsA(`SurfaceAppearance`) or D:IsA(`Decal`) or D:IsA(`Texture`) then table.insert(List, D) end
	end
	return List
end
function Bench.Preload()
	if Warmed then return end
	Warmed = true
	task.spawn(function()
		local Models = ReplicatedStorage:WaitForChild(`Anatomy`):WaitForChild(`Models`, 30)
		if Models then pcall(ContentProvider.PreloadAsync, ContentProvider, assetsOf(Models)) end
	end)
end
Bench.Preload()

----------------------------------------------------------------------------------------------------- small helpers
local function new(Class: string, Props: { [string]: any }?, Parent: Instance?)
	local I = Instance.new(Class)
	for K, V in Props or {} do (I :: any)[K] = V end
	if Parent then I.Parent = Parent end
	return I
end

local function panel(Parent: Instance, Props)
	local F = new(`Frame`, { BackgroundColor3 = IRON; BackgroundTransparency = 0.08; BorderSizePixel = 0 }, Parent)
	for K, V in Props do (F :: any)[K] = V end
	new(`UICorner`, { CornerRadius = UDim.new(0, 8) }, F)
	new(`UIStroke`, { Color = GOLD; Thickness = 1.5; Transparency = 0.35; ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, F)
	new(`UIGradient`, { Rotation = 90; Color = ColorSequence.new(IRON_HI, IRON) }, F)
	return F
end

local function text(Parent: Instance, Str: string, Props)
	local T = new(`TextLabel`, { BackgroundTransparency = 1; Text = Str; TextColor3 = INK; Font = Enum.Font.Gotham; TextScaled = true;
		RichText = true; TextXAlignment = Enum.TextXAlignment.Left; TextWrapped = true }, Parent)
	for K, V in Props or {} do (T :: any)[K] = V end
	return T
end

-- a flat line on the bench from A to B (layout space): a thin strip lifted a hair off the surface, overlapping the next
local function stroke(A: Vector3, B: Vector3, Width: number, Color: Color3, Material: Enum.Material, Lift: number, Parent: Instance): BasePart
	local L = math.max((B - A).Magnitude, 0.001)
	local Mid = (A + B) / 2 + Vector3.new(0, Lift, 0)
	local CF = if L > 0.002 then CFrame.lookAt(Mid, Mid + (B - A)) * CFrame.Angles(0, math.pi / 2, 0) else CFrame.new(Mid)
	return new(`Part`, { Name = `Stroke`; Anchored = true; CanCollide = false; CanQuery = false; CanTouch = false; CastShadow = false;
		Material = Material; Color = Color; Size = Vector3.new(L + Width * 0.5, 0.012, Width);
		CFrame = CFrame.new(STAGE) * CF }, Parent)
end

local function ease(t: number): number -- smooth in/out
	t = math.clamp(t, 0, 1)
	return t * t * (3 - 2 * t)
end

----------------------------------------------------------------------------------------------------- props
-- Proxy shapes per piece name (stand-ins until the meshes are imported).
local SHAPE = {
	Body = `Bowl`; Plate = `Ellipsoid`; Head = `Ellipsoid`; Legs = `Splay`; Limbs = `Pair`; Tail = `Ellipsoid`;
	Mechanism = `Deck`; CradleGlow = `Disc`; HeartPump = `Ellipsoid`; HeartA = `Ellipsoid`; HeartB = `Ellipsoid`;
	Lungs = `PairBlock`; GearGut = `Disc`; FlagCog = `Disc`; VoiceBox = `Block`; WingSpring = `RodX`; FireGland = `Disc`;
	FireGlandGlass = `Ellipsoid`; FireGlandGlow = `Ellipsoid`; SideKey = `Rod`;
	Desk = `Desk`; Tray = `Block`; Wax = `Block`; Roll = `Block`; Candle = `DiscTall`; FlameGlow = `Ellipsoid`;
	Main = `Rod`; LensGlass = `Ellipsoid`;
}

local function basePart(pc, Size: Vector3, CF: CFrame)
	local P = new(`Part`, { Anchored = true; CanCollide = false; CanTouch = false; CanQuery = true; CastShadow = false;
		Size = Size; CFrame = CF; Color = pc.Color; TopSurface = Enum.SurfaceType.Smooth; BottomSurface = Enum.SurfaceType.Smooth })
	local ok, M = pcall(function() return (Enum.Material :: any)[pc.Material] end)
	P.Material = if ok and M then M else Enum.Material.SmoothPlastic
	if pc.Glass then P.Transparency = 0.55 end
	return P
end

local function ellipsoid(pc, Size, CF)
	local P = basePart(pc, Size, CF)
	new(`SpecialMesh`, { MeshType = Enum.MeshType.Sphere }, P)
	return P
end

local function cylinder(pc, Len: number, Dia: number, CF: CFrame) -- Roblox cylinders run along X
	local P = basePart(pc, Vector3.new(Len, Dia, Dia), CF)
	P.Shape = Enum.PartType.Cylinder
	return P
end

local function proxyParts(Piece: string, pc): { BasePart }
	local S, Cn = pc.Size, pc.Centre
	local Shape = SHAPE[Piece] or (if string.match(Piece, `^WingPlate`) then `Block` elseif string.match(Piece, `^Chalk`) then `Outline` else `Block`)
	local out = {}
	if Shape == `Bowl` then -- an open brass bowl: a ring of wall staves and a floor, so the inside reads hollow
		local Bottom = Cn.Y - S.Y / 2
		table.insert(out, ellipsoid(pc, Vector3.new(S.X * 0.96, S.Y * 0.55, S.Z * 0.96), CFrame.new(Cn.X, Bottom + S.Y * 0.2, Cn.Z)))
		local Lacquer = { Color = Color3.fromRGB(64, 12, 12); Material = `SmoothPlastic` }
		table.insert(out, ellipsoid(Lacquer, Vector3.new(S.X * 0.9, S.Y * 0.4, S.Z * 0.9), CFrame.new(Cn.X, Bottom + S.Y * 0.26, Cn.Z)))
		local N = 28
		for i = 1, N do
			local a = (i - 0.5) / N * math.pi * 2
			local x, z = math.cos(a) * S.X * 0.47, math.sin(a) * S.Z * 0.47
			local nx, nz = math.cos(a) * S.Z, math.sin(a) * S.X -- ellipse normal (unnormalised)
			local look = CFrame.lookAt(Vector3.new(Cn.X + x, Bottom + S.Y * 0.45, Cn.Z + z), Vector3.new(Cn.X + x + nx, Bottom + S.Y * 0.45, Cn.Z + z + nz))
			local circ = math.pi * (S.X + S.Z) / 2 / N
			table.insert(out, basePart(pc, Vector3.new(circ * 1.12, S.Y * 0.62, 0.07), look))
		end
	elseif Shape == `Ellipsoid` then
		table.insert(out, ellipsoid(pc, S, CFrame.new(Cn)))
	elseif Shape == `Splay` then
		table.insert(out, ellipsoid(pc, Vector3.new(S.X, S.Y * 0.5, S.Z * 0.85), CFrame.new(Cn.X, Cn.Y - S.Y * 0.2, Cn.Z)))
	elseif Shape == `Pair` or Shape == `PairBlock` then
		local w = math.min(S.X * 0.22, 0.35)
		for _, sx in { -1, 1 } do
			local CF = CFrame.new(Cn.X + sx * (S.X / 2 - w / 2), Cn.Y, Cn.Z)
			table.insert(out, if Shape == `Pair` then ellipsoid(pc, Vector3.new(w, S.Y, S.Z), CF) else basePart(pc, Vector3.new(w * 1.6, S.Y, S.Z), CF))
		end
	elseif Shape == `Deck` then
		table.insert(out, cylinder(pc, 0.05, math.min(S.X, S.Z) * 0.95, CFrame.new(Cn.X, Cn.Y - S.Y / 2 + 0.03, Cn.Z) * CFrame.Angles(0, 0, math.pi / 2)))
		local d = new(`SpecialMesh`, { MeshType = Enum.MeshType.Cylinder; Scale = Vector3.new(1, 1, S.Z / math.max(S.X, 0.01)) }, out[1])
		d.Name = `Stretch`
	elseif Shape == `Disc` or Shape == `DiscTall` then
		table.insert(out, cylinder(pc, S.Y, math.max(S.X, S.Z), CFrame.new(Cn) * CFrame.Angles(0, 0, math.pi / 2)))
	elseif Shape == `Rod` then
		local Long = math.max(S.X, S.Y, S.Z)
		local Thick = math.max(math.min(S.X, S.Z), 0.12)
		local CF = if S.X >= S.Z then CFrame.new(Cn) else CFrame.new(Cn) * CFrame.Angles(0, math.pi / 2, 0)
		table.insert(out, basePart(pc, Vector3.new(Long, math.max(S.Y, 0.08), Thick), CF))
	elseif Shape == `RodX` then
		table.insert(out, cylinder(pc, S.X, math.min(S.Y, S.Z), CFrame.new(Cn)))
	elseif Shape == `Desk` then
		table.insert(out, basePart(pc, Vector3.new(S.X, 0.4, S.Z), CFrame.new(Cn.X, Cn.Y - 0.2, Cn.Z)))
	elseif Shape == `Outline` then
		local T = 0.035
		for _, e in { { 0, -1 }, { 0, 1 }, { -1, 0 }, { 1, 0 } } do
			local sz = if e[1] == 0 then Vector3.new(S.X, 0.02, T) else Vector3.new(T, 0.02, S.Z)
			table.insert(out, basePart(pc, sz, CFrame.new(Cn.X + e[1] * (S.X / 2 - T / 2), Cn.Y, Cn.Z + e[2] * (S.Z / 2 - T / 2))))
		end
	else
		table.insert(out, basePart(pc, S, CFrame.new(Cn)))
	end
	for _, P in out do P.Name = Piece end
	return out
end

-- Builds one prop: { Model, Pieces = { [piece] = { Bone, Parts = { {Part, Rest} } } }, Bones = { [bone] = { Head, Axis, Pieces } } }
local function buildProp(Name: string, Parent: Instance)
	local L = Layout.Props[Name]
	assert(L, `no layout for {Name}`)
	local Models = ReplicatedStorage.Anatomy:FindFirstChild(`Models`)
	local Real = Models and Models:FindFirstChild(Name)
	local Model = if Real then Real:Clone() else new(`Model`, { Name = Name })
	local Prop = { Name = Name; Model = Model; Pieces = {}; Bones = {}; Layout = L; Real = Real ~= nil }
	for Bone, B in L.Bones do Prop.Bones[Bone] = { Head = B.Head; Axis = B.Axis; Pieces = {}; CF = CFrame.identity } end
	for Piece, pc in L.Pieces do
		local Parts = {}
		if Real then
			local P = Model:FindFirstChild(Piece, true)
			if P and P:IsA(`BasePart`) then table.insert(Parts, P) end
		end
		if #Parts == 0 then Parts = proxyParts(Piece, pc) end
		local Entry = { Bone = pc.Bone; Parts = {} }
		for _, P in Parts do
			P.Anchored = true
			P.CanCollide = false
			P:SetAttribute(`Prop`, Name)
			P:SetAttribute(`Piece`, Piece)
			P:SetAttribute(`Bone`, pc.Bone)
			if not P.Parent or P.Parent == nil then P.Parent = Model end
			table.insert(Entry.Parts, { Part = P; Rest = P.CFrame; Transparency = P.Transparency })
			P.CFrame = P.CFrame + STAGE
		end
		Prop.Pieces[Piece] = Entry
		if Prop.Bones[pc.Bone] then table.insert(Prop.Bones[pc.Bone].Pieces, Piece) end
	end
	Model.Parent = Parent
	return Prop
end

local function setBone(Prop, Bone: string, CF: CFrame)
	local B = Prop.Bones[Bone]
	if not B then return end
	B.CF = CF
	for _, Piece in B.Pieces do
		for _, E in Prop.Pieces[Piece].Parts do E.Part.CFrame = (CF * E.Rest) + STAGE end
	end
end

local function fadeBone(Prop, Bone: string, To: number, Time: number)
	local B = Prop.Bones[Bone]
	if not B then return end
	for _, Piece in B.Pieces do
		for _, E in Prop.Pieces[Piece].Parts do
			TweenService:Create(E.Part, TweenInfo.new(Time), { Transparency = if To >= 1 then 1 else E.Transparency }):Play()
		end
	end
end

local function pieceVisible(Prop, Piece: string, On: boolean)
	local E = Prop.Pieces[Piece]
	if not E then return end
	for _, X in E.Parts do X.Part.Transparency = if On then X.Transparency else 1 end
end

----------------------------------------------------------------------------------------------------- construction
function Bench.new(Content: Frame, Payload, Api)
	local self = setmetatable({}, Bench)
	self.Api = Api
	self.Content = Content
	self.Payload = Payload
	self.Species = Payload.Species
	self.Def = nil
	for _, Sp in Config.Species do if Sp.Id == Payload.Species then self.Def = Sp end end
	self.Steps = Payload.Steps or {}
	self.StepIndex = 1
	self.Progress = 0
	self.Hand = nil
	self.Holding = nil
	self.Placed = {}
	self.Revealed = {}
	self.Recoiling = false
	self.Conns = {}
	self.Tracks = {}
	self.Pointer = nil
	self.Busy = false
	for _, O in Payload.Organs or {} do if O.Slot then self.Revealed[O.Id] = O.Slot end end

	self:BuildStage()
	self:BuildChrome()
	self:ApplySkin()
	self:BuildArms()
	self:BindInput()
	self:RefreshSteps()
	self:RefreshTools()
	self:RefreshCard()
	self:CoverUntilLoaded()
	if RunService:IsStudio() then _G.NHAnatomyBench = self end
	return self
end

-- A dark cloth over the bench (under the panels) until this lesson's props have their meshes and maps, so the
-- specimen never pops in late or white. Gives up after PRELOAD_WAIT and shows what there is. (Game scripts can't
-- read a SurfaceAppearance's map ids, so it doesn't ask what is cached: PreloadAsync returns at once when all of it
-- is, and the cloth then goes without a fade.)
function Bench:CoverUntilLoaded()
	local List = {}
	for _, Prop in { self.Set, self.Specimen } do for _, X in assetsOf(Prop.Model) do table.insert(List, X) end end
	for _, T in self.Tools do for _, X in assetsOf(T.Model) do table.insert(List, X) end end
	self.Loaded = false
	local Cover = new(`Frame`, { Name = `Cover`; Size = UDim2.fromScale(1, 1); BackgroundColor3 = Color3.fromRGB(12, 10, 12); BorderSizePixel = 0; ZIndex = 3 }, self.Content)
	local Label = text(Cover, `Laying out the specimen...`, { AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.42);
		Size = UDim2.fromScale(0.4, 0.05); TextXAlignment = Enum.TextXAlignment.Center; TextColor3 = DIM })
	self.Cover = Cover
	local Started = os.clock()
	local Done = false
	task.spawn(function()
		pcall(ContentProvider.PreloadAsync, ContentProvider, List)
		Done = true
	end)
	task.spawn(function()
		while not Done and os.clock() - Started < PRELOAD_WAIT and not self.Destroyed do task.wait(0.1) end
		self.Loaded = true
		self.LoadTime = os.clock() - Started
		if self.Destroyed or not Cover.Parent then return end
		if self.LoadTime < 0.2 then Cover:Destroy() return end -- all cached: no fade
		local Info = TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
		TweenService:Create(Cover, Info, { BackgroundTransparency = 1 }):Play()
		TweenService:Create(Label, Info, { TextTransparency = 1 }):Play()
		task.delay(0.4, function() Cover:Destroy() end)
	end)
end

-- (2026-11-26) The bench is staged in the real world, not a ViewportFrame: a ViewportFrame has no environment, so its
-- brass read flat. The props are drawn at STAGE (high over the map, client-only parts) inside a dark room with their
-- own candle, key and rim lights, and the bench drives the real camera while the lesson is open. All the bench's
-- maths stays in layout space: parts sit at STAGE + their layout pose, rays and screen points are moved by STAGE.
function Bench:BuildStage()
	local Stage = new(`Model`, { Name = `NHAnatomyStage` })
	self.Stage = Stage
	local function wall(Size: Vector3, Pos: Vector3)
		new(`Part`, { Anchored = true; CanCollide = false; CanQuery = false; CastShadow = false; Size = Size; CFrame = CFrame.new(STAGE + Pos);
			Color = Color3.fromRGB(14, 11, 10); Material = Enum.Material.SmoothPlastic }, Stage)
	end
	-- a closed dark room: no sun, no sky, whatever the school clock says
	wall(Vector3.new(64, 2, 54), Vector3.new(0, -4, 0)) wall(Vector3.new(64, 2, 54), Vector3.new(0, 24, 0))
	wall(Vector3.new(2, 30, 54), Vector3.new(-32, 10, 0)) wall(Vector3.new(2, 30, 54), Vector3.new(32, 10, 0))
	wall(Vector3.new(64, 30, 2), Vector3.new(0, 10, -27)) wall(Vector3.new(64, 30, 2), Vector3.new(0, 10, 27))
	local function lamp(CF: CFrame, Class: string, Props)
		local A = new(`Part`, { Name = `Lamp`; Anchored = true; CanCollide = false; CanQuery = false; Transparency = 1; Size = Vector3.one * 0.2; CFrame = CF + STAGE }, Stage)
		return new(Class, Props, A)
	end
	-- the candle's pool, a warm key over the student's left shoulder, a cool rim from behind the specimen
	self.CandleLight = lamp(CFrame.new(-6.2, 2.1, -3.6), `PointLight`, { Color = Color3.fromRGB(255, 160, 80); Brightness = 2.4; Range = 22; Shadows = true })
	lamp(CFrame.lookAt(Vector3.new(-6, 14, 9), Vector3.zero), `SpotLight`, { Color = Color3.fromRGB(255, 220, 180); Brightness = 0.8; Range = 32; Angle = 45; Shadows = true; Face = Enum.NormalId.Front })
	lamp(CFrame.lookAt(Vector3.new(5, 8, -9), Vector3.new(0, 0.5, 0)), `SpotLight`, { Color = Color3.fromRGB(150, 175, 255); Brightness = 0.9; Range = 25; Angle = 45; Face = Enum.NormalId.Front })
	local WM = Stage
	self.World = Stage
	self.Camera = workspace.CurrentCamera
	self.CamBase = CAMERA_CF
	-- the real camera is the bench's while the lesson is open (put back in Destroy)
	local Cam = workspace.CurrentCamera
	self.CamWas = { Type = Cam.CameraType; FOV = Cam.FieldOfView; Subject = Cam.CameraSubject }
	Cam.CameraType = Enum.CameraType.Scriptable
	-- the rest of the HUD steps aside (the lesson's own screen stays); put back in Destroy
	self.HiddenGuis = {}
	local Mine = self.Content:FindFirstAncestorWhichIsA(`ScreenGui`)
	for _, G in Players.LocalPlayer.PlayerGui:GetChildren() do
		if G:IsA(`ScreenGui`) and G.Enabled and G ~= Mine then G.Enabled = false table.insert(self.HiddenGuis, G) end
	end
	-- a vignette over the view
	local Vig = new(`Frame`, { Name = `Vignette`; Size = UDim2.fromScale(1, 1); BackgroundTransparency = 0; BackgroundColor3 = Color3.new(0, 0, 0); ZIndex = 2 }, self.Content)
	new(`UIGradient`, { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(0.18, 1), NumberSequenceKeypoint.new(0.82, 1), NumberSequenceKeypoint.new(1, 0.35) }) }, Vig)
	Vig.Active = false
	self.Vignette = Vig

	self.Set = buildProp(`BenchSet`, WM)
	self.Specimen = buildProp(self.Species, WM)
	self.Tools = {}
	for i, Id in Config.Tools do
		local T = buildProp(`Tool` .. Id, WM)
		T.Id = Id
		T.Index = i
		T.Spot = `Roll`
		T.CF = CFrame.identity
		local A = T.Layout.Attach
		T.Tip, T.Grip = A.Tip.Pos, A.Grip.Pos
		local lo = math.huge
		for _, E in T.Pieces do for _, X in E.Parts do lo = math.min(lo, X.Rest.Position.Y - X.Part.Size.Y / 2) end end
		T.Bottom = lo
		self.Tools[Id] = T
	end
	for i = 1, 5 do pieceVisible(self.Set, `Chalk{i}Glow`, false) end

	-- the seam: 24 dots on the plate, shown while tracing; the plate's centre and radius for plate space
	local Seam, Sum = {}, Vector3.zero
	for i = 1, 24 do local P = self.Specimen.Layout.Attach[string.format(`Seam%02d`, i)].Pos Seam[i] = P Sum += P end
	self.SeamCentre = Sum / 24
	self.SeamR = (Seam[1] - self.SeamCentre).Magnitude
	self.SeamDots = {}
	for i, P in Seam do
		local Q = Seam[i % #Seam + 1]
		local A, B = P:Lerp(Q, 0.18), P:Lerp(Q, 0.82)
		table.insert(self.SeamDots, stroke(A, B, 0.13, Color3.fromRGB(26, 14, 10), Enum.Material.SmoothPlastic, 0.02, WM))
		table.insert(self.SeamDots, stroke(A, B, 0.05, Color3.fromRGB(255, 240, 205), Enum.Material.Neon, 0.035, WM))
	end
	for _, D in self.SeamDots do D.Transparency = 1 end
	self.Trail = new(`Folder`, { Name = `Trail` }, WM)
	Stage.Parent = workspace
end

function Bench:BuildArms()
	-- the student's arms reaching in from below the view: an R6 clone of the player, scaled, seated behind the camera
	local Char = Players.LocalPlayer.Character
	if not Char or not Char:FindFirstChildOfClass(`Humanoid`) or Char:FindFirstChildOfClass(`Humanoid`).RigType ~= Enum.HumanoidRigType.R6 then return end
	local Was = Char.Archivable
	Char.Archivable = true
	local ok, Rig = pcall(function() return Char:Clone() end)
	Char.Archivable = Was
	if not ok or not Rig then return end
	for _, X in Rig:GetDescendants() do
		if X:IsA(`Script`) or X:IsA(`LocalScript`) or X:IsA(`ForceField`) or X:IsA(`Tool`) or X:IsA(`Sound`) or X:IsA(`ParticleEmitter`)
			or X:IsA(`Accoutrement`) or X:IsA(`Decal`) then X:Destroy() end
	end
	-- the head sits at the camera at this scale: hide it (hair, hats and the face are gone above), keep torso and arms
	local RigHead = Rig:FindFirstChild(`Head`)
	if RigHead and RigHead:IsA(`BasePart`) then RigHead.Transparency = 1 end
	local Hum = Rig:FindFirstChildOfClass(`Humanoid`)
	local Root = Rig:FindFirstChild(`HumanoidRootPart`)
	if not Hum or not Root then Rig:Destroy() return end
	Hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	for _, P in Rig:GetDescendants() do if P:IsA(`BasePart`) then P.CanCollide = false P.CanQuery = false P.Anchored = false end end
	Root.Anchored = true
	Rig.Parent = self.World
	pcall(function() Rig:ScaleTo(ARM_SCALE) end)
	Rig:PivotTo(SEAT_CF + STAGE)
	local Animator = Hum:FindFirstChildOfClass(`Animator`) or new(`Animator`, {}, Hum)
	self.Rig, self.Animator = Rig, Animator
	local Folder = ReplicatedStorage:FindFirstChild(`AnatomyClips`)
	self.ClipMap = Folder and Folder:FindFirstChild(`Clips`) and require(Folder.Clips) or {}
	-- published clips first (Clips.Ids: clip name -> group asset id); KSP registration only covers a clip with no id
	-- (it works in Studio only)
	for Name, AssetId in (type(self.ClipMap.Ids) == `table` and self.ClipMap.Ids) or {} do
		local A = new(`Animation`, { AnimationId = `rbxassetid://{AssetId}`; Name = Name })
		local okT, Track = pcall(function() return Animator:LoadAnimation(A) end)
		if okT and Track then self.Tracks[Name] = Track end
	end
	if Folder and Folder:FindFirstChild(`Animations`) then
		local KSP = game:GetService(`KeyframeSequenceProvider`)
		for _, Seq in Folder.Animations:GetChildren() do
			if Seq:IsA(`KeyframeSequence`) and not self.Tracks[Seq.Name] then
				local okId, Id = pcall(function() return KSP:RegisterKeyframeSequence(Seq) end)
				if okId then
					local A = new(`Animation`, { AnimationId = Id; Name = Seq.Name })
					local okT, Track = pcall(function() return Animator:LoadAnimation(A) end)
					if okT then self.Tracks[Seq.Name] = Track end
				end
			end
		end
	end
	local Idle = self.Tracks.AnatBenchIdle
	if Idle then Idle.Looped = true Idle.Priority = Enum.AnimationPriority.Idle Idle:Play(0.2) end
	-- after the Animator has posed the arms each frame, bend the shoulders toward what the student is doing
	table.insert(self.Conns, RunService.PreSimulation:Connect(function(Dt) self:AimArms(Dt) end))
end

-- The arms follow the work. The clips pose them; on top of that each shoulder turns its arm toward a target, blended
-- by a weight that eases in and out:
--   right arm: the tool in hand (0.4), or the pointer over the bench when the hand is empty (0.2); kept partial so the
--              near arm stays at the frame's edge and never covers the tool roll or the card
--   left arm:  the specimen, steadying it while tracing, turning a key/driver or lifting a part; resting otherwise
-- The R6 stays rigid: only the shoulder Motor6D's Transform turns, so the limb stays on its socket.
local AIM_RATE = 10 -- how fast a target and a weight ease (per second)
function Bench:AimArms(Dt: number)
	if self.Destroyed or not self.Rig then return end
	local Torso = self.Rig:FindFirstChild(`Torso`)
	if not Torso then return end
	Dt = math.min(Dt, 1 / 20)
	local k = 1 - math.exp(-AIM_RATE * Dt)
	self.Aim = self.Aim or {}
	local Busy = self.Tracing or self.Holding_ or self.Holding
	local Specimen = (self.SeamCentre or WIDE_FOCUS_ARMS) + Vector3.new(0, 0.1, 0)
	-- right: the tool's grip, else the pointer
	local RGoal, RW
	if self.Hand and self.Tools[self.Hand] then
		RGoal, RW = self.Tools[self.Hand].CF.Position, 0.4
	elseif not self:OverChrome() and self:Hit() then
		RGoal, RW = self:Hit().Position, 0.2
	else
		RGoal, RW = Specimen + Vector3.new(2.5, 0, 2.5), 0
	end
	-- left: brace the specimen beside the work while busy, a light rest toward the tray when a tool is up
	local LGoal, LW
	if Busy then
		LGoal, LW = Specimen + Vector3.new(-1.1, 0, 0.6), 0.5
	elseif self.Hand then
		LGoal, LW = Specimen + Vector3.new(-2.6, -0.2, 2.2), 0.2
	else
		LGoal, LW = Specimen + Vector3.new(-2.6, 0, 2.5), 0
	end
	for Side, Goal in { Right = RGoal; Left = LGoal } do
		local W = if Side == `Right` then RW else LW
		local A = self.Aim[Side]
		if not A then A = { P = Goal; W = 0 } self.Aim[Side] = A end
		A.P = A.P:Lerp(Goal, k)
		A.W += (W - A.W) * k
		local M = Torso:FindFirstChild(Side .. ` Shoulder`)
		if M and M:IsA(`Motor6D`) and A.W > 0.001 then
			local J = Torso.CFrame * M.C0
			local To = J:VectorToObjectSpace((A.P + STAGE) - J.Position)
			if To.Magnitude > 1e-3 then
				-- the arm hangs down the joint's -Y; turn that onto the target, keeping the clip's own twist on top
				local Aim = CFrame.fromRotationBetweenVectors(Vector3.new(0, -1, 0), To.Unit)
				M.Transform = M.Transform:Lerp(Aim, A.W)
			end
		end
	end
end

function Bench:Clip(Key: string, Reverse: boolean?)
	local Name = self.ClipMap and self.ClipMap[Key]
	local T = Name and self.Tracks[Name]
	if not T then return end
	T.Priority = Enum.AnimationPriority.Action
	T:Play(0.08)
	if Reverse then T.TimePosition = math.max(T.Length - 0.01, 0) T:AdjustSpeed(-1) else T:AdjustSpeed(1) end
end

----------------------------------------------------------------------------------------------------- chrome
function Bench:BuildChrome()
	local UI = new(`Frame`, { Name = `Chrome`; BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1); ZIndex = 5 }, self.Content)
	self.UI = UI
	local P = self.Payload
	local E = Electives.Get and Electives.Get(`Anatomy`) or {}

	-- the plate: species, Latin, room/level/teacher, the timer
	local Plate = panel(UI, { Name = `Plate`; Position = UDim2.fromScale(0.015, 0.02); Size = UDim2.fromScale(0.34, 0.13) })
	text(Plate, string.upper(P.Name or self.Species), { Font = Fonts.Title or Enum.Font.Fantasy; TextColor3 = GOLD; Position = UDim2.fromScale(0.04, 0.08); Size = UDim2.fromScale(0.66, 0.38) })
	text(Plate, `<i>{P.Latin or ``}</i>`, { TextColor3 = DIM; Position = UDim2.fromScale(0.04, 0.48); Size = UDim2.fromScale(0.66, 0.2) })
	text(Plate, `Room {E.Room or `R103`}  \u{00B7}  Lv {P.Level or 1}  \u{00B7}  {E.Teacher or ``}`, { TextColor3 = DIM; Position = UDim2.fromScale(0.04, 0.72); Size = UDim2.fromScale(0.7, 0.2) })
	local Timer = text(Plate, `--:--`, { Font = Fonts.Title or Enum.Font.Fantasy; TextColor3 = GOLD; TextXAlignment = Enum.TextXAlignment.Right;
		Position = UDim2.fromScale(0.7, 0.12); Size = UDim2.fromScale(0.27, 0.6) })
	if self.Api.SetTimerLabel then self.Api.SetTimerLabel(Timer) end
	if P.Twist and TWIST_TEXT[P.Twist] then
		local Tag = panel(UI, { Name = `Twist`; Position = UDim2.fromScale(0.015, 0.16); Size = UDim2.fromScale(0.2, 0.04); BackgroundColor3 = Color3.fromRGB(60, 14, 18) })
		text(Tag, TWIST_TEXT[P.Twist], { TextColor3 = INK; Position = UDim2.fromScale(0.05, 0.12); Size = UDim2.fromScale(0.9, 0.76) })
	end

	-- the hint line
	self.Hint = text(UI, ``, { TextXAlignment = Enum.TextXAlignment.Center; TextColor3 = INK; Position = UDim2.fromScale(0.36, 0.03); Size = UDim2.fromScale(0.4, 0.04);
		TextStrokeTransparency = 0.4 })

	-- the procedure card
	local Proc = panel(UI, { Name = `Procedure`; Position = UDim2.fromScale(0.015, 0.22); Size = UDim2.fromScale(0.22, 0.06 + 0.055 * #self.Steps) })
	text(Proc, `PROCEDURE`, { Font = Fonts.Title or Enum.Font.Fantasy; TextColor3 = GOLD; Position = UDim2.new(0.06, 0, 0, 6); Size = UDim2.new(0.9, 0, 0.055 / (0.06 + 0.055 * #self.Steps), 0) })
	self.StepLines = {}
	local h = 1 / (#self.Steps + 1.1)
	for i, St in self.Steps do
		local L = text(Proc, ``, { Name = `Step{i}`; Position = UDim2.fromScale(0.06, h * (i + 0.05)); Size = UDim2.fromScale(0.9, h * 0.8) })
		self.StepLines[i] = L
	end

	-- the Specimen card: one outline per slot (hidden until revealed)
	local Card = panel(UI, { Name = `SpecimenCard`; Position = UDim2.fromScale(0.765, 0.17); Size = UDim2.fromScale(0.22, 0.5) })
	self.Card = Card
	text(Card, `SPECIMEN CARD`, { Font = Fonts.Title or Enum.Font.Fantasy; TextColor3 = GOLD; Position = UDim2.fromScale(0.06, 0.02); Size = UDim2.fromScale(0.9, 0.07) })
	text(Card, P.Name or ``, { TextColor3 = DIM; Position = UDim2.fromScale(0.06, 0.09); Size = UDim2.fromScale(0.9, 0.05) })
	self.CardNote = text(Card, ``, { TextColor3 = DIM; TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromScale(0.06, 0.42); Size = UDim2.fromScale(0.88, 0.14); Visible = false })
	self.InspectBtn = new(`TextButton`, { Name = `InspectCard`; Text = `Inspect the card (Loupe)`; Font = Enum.Font.GothamBold; TextScaled = true;
		TextColor3 = IRON; BackgroundColor3 = GOLD; Position = UDim2.fromScale(0.15, 0.6); Size = UDim2.fromScale(0.7, 0.08); Visible = false; AutoButtonColor = true }, Card)
	new(`UICorner`, { CornerRadius = UDim.new(0, 6) }, self.InspectBtn)
	self.InspectBtn.Activated:Connect(function() self:UseCard() end)
	self.SlotButtons = {}
	local Slots = {}
	for _, O in P.Organs or {} do if O.Id ~= `FlagCog` then table.insert(Slots, O) end end
	self.SlotOrder = Slots
	for i, O in Slots do
		local B = new(`TextButton`, { Name = `Slot{i}`; Text = ``; BackgroundColor3 = Color3.fromRGB(30, 24, 22); BackgroundTransparency = 0.2; AutoButtonColor = true;
			Position = UDim2.fromScale(0.08, 0.17 + (i - 1) * 0.8 / math.max(#Slots, 1)); Size = UDim2.fromScale(0.84, 0.8 / math.max(#Slots, 1) - 0.03) }, Card)
		new(`UICorner`, { CornerRadius = UDim.new(0, 6) }, B)
		local Stroke = new(`UIStroke`, { Color = GOLD; Thickness = 1.5; Transparency = 0.2; ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, B)
		local L = text(B, ``, { TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromScale(0.05, 0.2); Size = UDim2.fromScale(0.9, 0.6) })
		self.SlotButtons[i] = { Button = B; Label = L; Stroke = Stroke; Organ = O.Id }
		B.Activated:Connect(function() self:PlaceOn(i) end)
	end

	-- the tool tags along the bottom and the IN HAND box
	self.Tags = {}
	for i, Id in Config.Tools do
		local Tag = new(`TextButton`, { Name = `Tag{Id}`; Text = ``; AutoButtonColor = true; BackgroundColor3 = IRON; BackgroundTransparency = 0.1;
			Position = UDim2.fromScale(0.25 + (i - 1) * 0.1, 0.9); Size = UDim2.fromScale(0.09, 0.07) }, UI)
		new(`UICorner`, { CornerRadius = UDim.new(0, 8) }, Tag)
		local Stroke = new(`UIStroke`, { Color = GOLD; Thickness = 1.5; Transparency = 0.4; ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, Tag)
		text(Tag, `<b>{i}</b>  {TOOL_NAMES[Id] or Id}`, { TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromScale(0.06, 0.22); Size = UDim2.fromScale(0.88, 0.56) })
		Tag.Activated:Connect(function() self:Key(i) end)
		self.Tags[Id] = { Button = Tag; Stroke = Stroke }
	end
	local Hand = panel(UI, { Name = `InHand`; Position = UDim2.fromScale(0.79, 0.86); Size = UDim2.fromScale(0.195, 0.11) })
	text(Hand, `IN HAND`, { TextColor3 = GOLD; Font = Fonts.Title or Enum.Font.Fantasy; Position = UDim2.fromScale(0.06, 0.08); Size = UDim2.fromScale(0.9, 0.3) })
	self.HandText = text(Hand, `Nothing`, { Position = UDim2.fromScale(0.06, 0.42); Size = UDim2.fromScale(0.9, 0.45) })

	-- the hold ring that fills while the Key or the Driver turns
	local Ring = new(`Frame`, { Name = `HoldRing`; AnchorPoint = Vector2.new(0.5, 0.5); Size = UDim2.fromOffset(46, 46); BackgroundTransparency = 1; Visible = false; ZIndex = 8 }, UI)
	new(`UICorner`, { CornerRadius = UDim.new(1, 0) }, Ring)
	local RS_ = new(`UIStroke`, { Color = GOLD; Thickness = 4; Transparency = 0 }, Ring)
	self.RingGrad = new(`UIGradient`, { Transparency = NumberSequence.new(0) }, RS_)
	self.Ring = Ring
end

-- The PBR chrome images (Config.UI ids) over the plain panels: each panel with an id swaps its iron fill for the
-- image, and the paper cards take dark ink. Panels whose id is 0 stay as built.
local IRON_PAL = { Done = DIM; Now = GOLD; Next = INK; ToolHex = `#9a8f80`; Title = GOLD; Sub = DIM;
	Slot = Color3.fromRGB(30, 24, 22); SlotDone = Color3.fromRGB(92, 70, 28); SlotText = INK; SlotDoneText = INK; SlotStroke = GOLD }
local PAPER_INK = Color3.fromRGB(46, 34, 28)
local PAPER_RED = Color3.fromRGB(140, 28, 34)
local PAPER_PAL = { Done = Color3.fromRGB(128, 112, 96); Now = PAPER_RED; Next = PAPER_INK; ToolHex = `#7d6a58`; Title = PAPER_RED; Sub = Color3.fromRGB(96, 80, 66);
	Slot = Color3.fromRGB(235, 228, 214); SlotDone = Color3.fromRGB(214, 176, 92); SlotText = PAPER_INK; SlotDoneText = PAPER_INK; SlotStroke = Color3.fromRGB(120, 96, 70) }

-- Slice borders scale with the panel's height (Scale is right at RefH px tall), so the drawn rules and edges sit at
-- the same fraction of the panel at every screen size and the text laid out in fractions stays clear of them.
local function skinFrame(F: GuiObject, Id: number, Slice: Rect?, Scale: number?, RefH: number?)
	F.BackgroundTransparency = 1
	for _, X in F:GetChildren() do if X:IsA(`UIStroke`) or X:IsA(`UIGradient`) then X:Destroy() end end
	local I = new(`ImageLabel`, { Name = `Skin`; BackgroundTransparency = 1; Image = `rbxassetid://{Id}`; Size = UDim2.fromScale(1, 1); ZIndex = 0 }, F)
	if Slice then
		I.ScaleType = Enum.ScaleType.Slice I.SliceCenter = Slice
		local function fit() I.SliceScale = math.max((Scale or 1) * F.AbsoluteSize.Y / (RefH or F.AbsoluteSize.Y), 0.05) end
		fit()
		if RefH then F:GetPropertyChangedSignal(`AbsoluteSize`):Connect(fit) end
	end
	return I
end

-- One text size for a row of labels: the largest that fits every label, so the tags match and none clips. Set as an
-- explicit TextSize (in the GUI's own units: AbsoluteSize is divided by any UIScale above) and re-checked every half
-- second from Step, so a resize, an intro scale-in or anything else touching the labels is corrected at once.
-- Not TextScaled: in Play something flips TextScaled straight back to false on these labels and leaves TextSize 8
-- (seen 2026-11-26, two flips per set, every set); an explicit size is the only thing that holds. UI.FitCheck copies
-- the GUI, so its 844x390 pass carries this screen's size and may flag Scalpel/Tweezers; a real resize re-fits within 0.5 s.
local TextService = game:GetService(`TextService`)
local function scaleAbove(G: Instance): number
	local S, X = 1, G
	while X do
		local U = X:FindFirstChildOfClass(`UIScale`)
		if U then S *= U.Scale end
		X = X.Parent
		if X and X:IsA(`LayerCollector`) then break end
	end
	return S
end
local function uniformText(Labels: { TextLabel }): boolean
	local Best = math.huge
	for _, L in Labels do
		local k = scaleAbove(L)
		local W, H = L.AbsoluteSize.X / k, L.AbsoluteSize.Y / k
		if W < 4 or H < 4 then return false end
		local Size = math.floor(H)
		while Size > 8 and TextService:GetTextSize(L.ContentText, Size, L.Font, Vector2.new(10000, 10000)).X > W do Size -= 1 end
		Best = math.min(Best, Size)
	end
	for _, L in Labels do
		if L.TextScaled then L.TextScaled = false end
		if L.TextWrapped then L.TextWrapped = false end
		if L.TextSize ~= Best then L.TextSize = Best end
	end
	return true
end

function Bench:ApplySkin()
	local Ids = Config.UI or {}
	local function has(K) return typeof(Ids[K]) == `number` and Ids[K] > 0 end
	self.StepPal = if has(`Procedure`) then PAPER_PAL else IRON_PAL
	self.CardPal = IRON_PAL
	local UI = self.UI
	if has(`Plate`) then
		local Plate = UI:FindFirstChild(`Plate`)
		skinFrame(Plate, Ids.Plate)
		-- clear the loupe roundel on the left
		-- rows: name, Latin, room line, all inside the frame's inner edge (it eats ~15% top and bottom)
		local Rows = { { 0.08, 0.13, 0.32 }; { 0.48, 0.46, 0.17 }; { 0.72, 0.64, 0.16 } }
		for _, X in Plate:GetChildren() do
			if X:IsA(`TextLabel`) and X.Position.X.Scale < 0.5 then
				local R
				for _, Row in Rows do if math.abs(X.Position.Y.Scale - Row[1]) < 0.01 then R = Row end end
				X.Position = UDim2.fromScale(0.2, if R then R[2] else X.Position.Y.Scale)
				X.Size = UDim2.fromScale(0.5, if R then R[3] else X.Size.Y.Scale)
			elseif X:IsA(`TextLabel`) then
				X.Position = UDim2.fromScale(0.71, 0.2) X.Size = UDim2.fromScale(0.25, 0.56) -- the timer
			end
		end
	end
	if has(`Procedure`) then
		local Proc = UI:FindFirstChild(`Procedure`)
		local n = #self.Steps
		Proc.Size = UDim2.fromScale(Proc.Size.X.Scale, 0.1 + 0.055 * n)
		local H = 0.1 + 0.055 * n
		-- the card's red rule sits ~60 px down at slice scale 0.5 on a 190 px card: keep that ratio at every size
		skinFrame(Proc, Ids.Procedure, Rect.new(30, 120, 370, 540), 0.5, 190 * H / 0.28)
		-- the rule is ~6.7% of the screen's height below the card's top, so as a fraction of the card: 0.067 / H
		local Top, Bottom = 0.067 / H + 0.04, 0.93
		for _, X in Proc:GetChildren() do
			if X:IsA(`TextLabel`) and X.Text == `PROCEDURE` then
				X.TextColor3 = PAPER_RED
				X.Position = UDim2.fromScale(0.09, 0.06) X.Size = UDim2.fromScale(0.82, math.min(0.16, Top - 0.1))
			end
		end
		local Pitch = (Bottom - Top) / n
		for i, L in self.StepLines do
			L.Position = UDim2.fromScale(0.09, Top + (i - 1) * Pitch + Pitch * 0.1)
			L.Size = UDim2.fromScale(0.82, Pitch * 0.8)
		end
	end
	if has(`Specimen`) then
		local Card = self.Card
		skinFrame(Card, Ids.Specimen, Rect.new(40, 110, 360, 540), 0.6, 341)
		for _, X in Card:GetChildren() do
			if X:IsA(`TextLabel`) and X.Text == `SPECIMEN CARD` then
				X.TextColor3 = PAPER_RED X.Position = UDim2.fromScale(0.1, 0.06) X.Size = UDim2.fromScale(0.8, 0.06)
			elseif X:IsA(`TextLabel`) and X ~= self.CardNote then
				X.TextColor3 = PAPER_PAL.Sub X.Position = UDim2.fromScale(0.1, 0.125) X.Size = UDim2.fromScale(0.8, 0.04)
			end
		end
		local n = math.max(#self.SlotButtons, 1)
		for i, S in self.SlotButtons do
			S.Button.Position = UDim2.fromScale(0.09, 0.22 + (i - 1) * 0.72 / n)
			S.Button.Size = UDim2.fromScale(0.82, 0.72 / n - 0.03)
		end
		self.CardPal = PAPER_PAL
		for _, S in self.SlotButtons do S.Button.BackgroundTransparency = 0.35 S.Stroke.Color = PAPER_PAL.SlotStroke end
	end
	if has(`Tag`) then
		for _, T in self.Tags do
			T.Skin = skinFrame(T.Button, Ids.Tag)
			T.Stroke = new(`UIStroke`, { Color = GOLD; Thickness = 1.5; Transparency = 1; ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, T.Button)
			for _, X in T.Button:GetChildren() do if X:IsA(`TextLabel`) then X.TextColor3 = PAPER_INK X.Position = UDim2.fromScale(0.25, 0.2) X.Size = UDim2.fromScale(0.71, 0.6) end end
		end
		local Labels = {}
		for _, T in self.Tags do for _, X in T.Button:GetChildren() do if X:IsA(`TextLabel`) then table.insert(Labels, X) end end end
		self.TagLabels = Labels
		uniformText(Labels)
	end
	if has(`Hold`) then
		new(`ImageLabel`, { Name = `Socket`; BackgroundTransparency = 1; Image = `rbxassetid://{Ids.Hold}`; AnchorPoint = Vector2.new(0.5, 0.5);
			Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromScale(1.5, 1.5); ZIndex = 7 }, self.Ring)
	end
	self:RefreshSteps()
	self:RefreshCard()
end

function Bench:SetHint(Str: string, Bad: boolean?)
	self.Hint.Text = Str
	self.Hint.TextColor3 = if Bad then Color3.fromRGB(255, 120, 110) else INK
end

function Bench:RefreshSteps()
	for i, St in self.Steps do
		local T = STEP_TEXT[St.Id] or { St.Id, `` }
		local Pal = self.StepPal or IRON_PAL
		local Label = `{i}. {T[1]}  <font color="{Pal.ToolHex}">({St.Tool})</font>`
		local L = self.StepLines[i]
		if i < self.StepIndex then
			L.Text = `<s>{i}. {T[1]}</s>`
			L.TextColor3 = Pal.Done
		elseif i == self.StepIndex then
			L.Text = `<b>{Label}</b>`
			L.TextColor3 = Pal.Now
		else
			L.Text = Label
			L.TextColor3 = Pal.Next
		end
	end
	local St = self.Steps[self.StepIndex]
	if St then
		local T = STEP_TEXT[St.Id] or { St.Id, `` }
		self:SetHint(if St.Count then string.format(T[2], self.Progress, St.Count) else T[2])
		for _, D in self.SeamDots do D.Transparency = if St.Id == `Trace` then 0.15 else 1 end
	end
end

function Bench:RefreshTools()
	for i, Id in Config.Tools do
		local T = self.Tools[Id]
		local InHand = self.Hand == Id
		local OnRoll = T.Spot == `Roll` and not InHand
		local Tag = self.Tags[Id]
		Tag.Stroke.Transparency = if InHand then 0 else 0.45
		Tag.Stroke.Thickness = if InHand then 3 else 1.5
		if Tag.Skin then
			Tag.Skin.ImageTransparency = if OnRoll or InHand then 0 else 0.45
			Tag.Skin.ImageColor3 = if InHand then Color3.fromRGB(255, 236, 190) else Color3.new(1, 1, 1)
		else
			Tag.Button.BackgroundTransparency = if OnRoll or InHand then 0.1 else 0.55
		end
		pieceVisible(self.Set, `Chalk{i}Glow`, not OnRoll)
	end
	local Holding = ``
	if self.Holding then
		for _, O in self.Payload.Organs or {} do if O.Id == self.Holding then Holding = ` \u{00B7} {O.Name}` end end
	end
	self.HandText.Text = if self.Hand then `{TOOL_NAMES[self.Hand] or self.Hand}{Holding}` else `Nothing`
end

function Bench:RefreshCard()
	local AnyHidden = false
	for i, S in self.SlotButtons do
		local Slot = self.Revealed[S.Organ]
		local Done = self.Placed[S.Organ]
		S.Button.Visible = Slot ~= nil
		if not Slot then AnyHidden = true end
		S.Label.Text = if Done then `<b>{SLOT_TEXT[Slot] or Slot}</b>  \u{2713}` else (SLOT_TEXT[Slot or ``] or Slot or ``)
		local Pal = self.CardPal or IRON_PAL
		S.Button.BackgroundColor3 = if Done then Pal.SlotDone else Pal.Slot
		S.Label.TextColor3 = if Done then Pal.SlotDoneText else Pal.SlotText
		S.Stroke.Transparency = if Done then 0 else 0.2
	end
	self.CardNote.Visible = AnyHidden
	self.CardNote.Text = `The outlines are missing. Look the card over with the Loupe.`
	self.InspectBtn.Visible = AnyHidden
end

----------------------------------------------------------------------------------------------------- pointer and input
-- the pointer in GUI space (AbsolutePosition's): GUI positions are measured from below the top bar even in an
-- IgnoreGuiInset ScreenGui (the bench's ViewportFrame sits at y -58), like InputObject.Position. GetMouseLocation
-- counts the bar, so take it off. (2026-11-26: a real mouse saw the tool in hand drawn 58 px below the pointer.)
function Bench:Pointer(): Vector2
	return UserInputService:GetMouseLocation() - GuiService:GetGuiInset()
end

-- the pointer's ray in layout space (the real camera's ray, moved back from STAGE)
function Bench:PointerRay(Screen: Vector2?)
	local Pos = Screen or self:Pointer()
	local R = workspace.CurrentCamera:ScreenPointToRay(Pos.X, Pos.Y)
	return R.Origin - STAGE, R.Direction.Unit
end

-- a layout-space point to GUI space (PointerRay's inverse)
function Bench:ToScreen(W: Vector3): Vector2?
	local p = workspace.CurrentCamera:WorldToScreenPoint(W + STAGE)
	if p.Z <= 0 then return nil end
	return Vector2.new(p.X, p.Y)
end

-- the unplaced organ drawn nearest a press, within PICK_RADIUS px: organs are small, and the cradle round them is
-- hollow (2026-11-26: real clicks on the frog's heart landed on the Mechanism's hull)
local PICK_RADIUS = 40
function Bench:NearestOrgan(Screen: Vector2): string?
	local Best, BestD = nil, PICK_RADIUS
	for _, O in self.Payload.Organs or {} do
		-- measured to the organ's drawn pieces (their centre), not its bone's pivot, which can sit off the part
		local B = not self.Placed[O.Id] and self.Specimen.Bones[self:BoneOf(O.Id)]
		local Sum, N = Vector3.zero, 0
		for _, Piece in (B and B.Pieces) or {} do
			for _, E in (self.Specimen.Pieces[Piece] or { Parts = {} }).Parts do Sum += E.Part.Position N += 1 end
		end
		local At = N > 0 and self:ToScreen(Sum / N - STAGE) or nil
		if At and (At - Screen).Magnitude < BestD then Best, BestD = O.Id, (At - Screen).Magnitude end
	end
	return Best
end

-- true while the pointer is outside the bench's screen or over one of the chrome panels drawn on top of it
function Bench:OverChrome(): boolean
	local Pos = self:Pointer()
	local C = self.Content
	local Rel = Pos - C.AbsolutePosition
	if Rel.X < 0 or Rel.Y < 0 or Rel.X > C.AbsoluteSize.X or Rel.Y > C.AbsoluteSize.Y then return true end
	for _, F in self.UI:GetDescendants() do
		if F:IsA(`GuiObject`) and F.Visible and F.Name ~= `Vignette` and F.BackgroundTransparency < 0.95 then
			local A, S = F.AbsolutePosition, F.AbsoluteSize
			if Pos.X >= A.X and Pos.Y >= A.Y and Pos.X <= A.X + S.X and Pos.Y <= A.Y + S.Y then return true end
		end
	end
	return false
end

-- a ray in layout space against the stage; the result's Position is in layout space too
local function stageCast(O: Vector3, D: Vector3, Params: RaycastParams)
	local R = workspace:Raycast(O + STAGE, D, Params)
	if not R then return nil end
	return { Instance = R.Instance; Position = R.Position - STAGE; Normal = R.Normal }
end

function Bench:Hit(Screen: Vector2?)
	local O, D = self:PointerRay(Screen)
	if not O then return nil end
	local Params = RaycastParams.new()
	Params.FilterType = Enum.RaycastFilterType.Exclude
	local Ex = { self.Trail }
	if self.Hand then table.insert(Ex, self.Tools[self.Hand].Model) end
	if self.Rig then table.insert(Ex, self.Rig) end
	if self.Holding then
		for _, Piece in (self.Specimen.Bones[self:BoneOf(self.Holding)] or { Pieces = {} }).Pieces do
			for _, E in self.Specimen.Pieces[Piece].Parts do table.insert(Ex, E.Part) end
		end
	end
	Params.FilterDescendantsInstances = Ex
	local R = stageCast(O, D * 60, Params)
	-- with the plate open, the shell and the cradle are hollow but their collision hulls aren't: a ray that lands on the
	-- specimen's body goes on through it to an organ behind, if there is one (2026-11-26: a real click on the frog's
	-- heart hit the Mechanism's hull over most of it)
	if R and self.PlateOpen then
		local First, Tries = R, 0
		while R and Tries < 6 do
			local W = self:Classify(R.Instance)
			if not W or W.Kind ~= `Body` then break end
			table.insert(Ex, R.Instance)
			Params.FilterDescendantsInstances = Ex
			R = stageCast(O, D * 60, Params)
			Tries += 1
		end
		local W = R and self:Classify(R.Instance)
		if not (W and W.Kind == `Organ`) then R = First end
	end
	return R, O, D
end

function Bench:BoneOf(OrganId: string): string
	return OrganId -- organ bones are named after the organ (FireGlandGlass/Glow ride on FireGland)
end

-- what a hit part means: Tool (on the roll/desk), SideKey, Plate, WingPlate, Organ, Desk, Roll
function Bench:Classify(Part: BasePart?)
	if not Part then return nil end
	local Prop, Bone, Piece = Part:GetAttribute(`Prop`), Part:GetAttribute(`Bone`), Part:GetAttribute(`Piece`)
	if typeof(Prop) == `string` and string.sub(Prop, 1, 4) == `Tool` then return { Kind = `Tool`; Tool = string.sub(Prop, 5) } end
	if Prop == `BenchSet` then
		if Piece == `Roll` or string.match(tostring(Piece), `^Chalk`) then return { Kind = `Roll` } end
		if Piece == `Desk` then return { Kind = `Desk` } end
		return { Kind = `Set` }
	end
	if Prop == self.Species then
		if Bone == `SideKey` then return { Kind = `SideKey` } end
		if Bone == `PlateHinge` then return { Kind = `Plate` } end
		if typeof(Bone) == `string` and string.match(Bone, `^WingPlate`) then return { Kind = `WingPlate`; Bone = Bone } end
		for _, O in self.Payload.Organs or {} do
			if O.Id == Bone then return { Kind = `Organ`; Organ = Bone } end
		end
		return { Kind = `Body` }
	end
	return nil
end

function Bench:BindInput()
	local function Conn(Sig, Fn) table.insert(self.Conns, Sig:Connect(Fn)) end
	Conn(UserInputService.InputBegan, function(Input, Processed)
		if self.Destroyed then return end
		local T = Input.UserInputType
		if T == Enum.UserInputType.MouseButton1 or T == Enum.UserInputType.Touch then
			if Processed then return end
			self:PressAt(Vector2.new(Input.Position.X, Input.Position.Y))
		elseif T == Enum.UserInputType.MouseButton2 then
			self:PutHere()
		elseif T == Enum.UserInputType.Keyboard then
			local K = Input.KeyCode
			local N = ({ [Enum.KeyCode.One] = 1; [Enum.KeyCode.Two] = 2; [Enum.KeyCode.Three] = 3; [Enum.KeyCode.Four] = 4; [Enum.KeyCode.Five] = 5 })[K]
			if N and not Processed then self:Key(N) end
			if K == Enum.KeyCode.Q and not Processed then self:PutHere() end
		elseif T == Enum.UserInputType.Gamepad1 then
			if Input.KeyCode == Enum.KeyCode.ButtonR1 then self:Key(((self.Hand and table.find(Config.Tools, self.Hand) or 0) % 5) + 1) end
		end
	end)
	Conn(UserInputService.InputEnded, function(Input)
		local T = Input.UserInputType
		if T == Enum.UserInputType.MouseButton1 or T == Enum.UserInputType.Touch then self:Release() end
	end)
	-- after the game's own camera each frame, so the bench's shot wins
	local Bind = `NHAnatomyBench`
	pcall(function() RunService:UnbindFromRenderStep(Bind) end)
	RunService:BindToRenderStep(Bind, Enum.RenderPriority.Camera.Value + 1, function(Dt) self:Step(Dt) end)
	self.Bound = Bind
end

function Bench:Key(N: number)
	local Id = Config.Tools[N]
	if not Id or self.Recoiling then return end
	if self.Hand == Id then self:Put(`Roll`) return end
	if self.Holding then self:SetHint(`Set the part down on the card first`, true) return end
	self.Api.Send(`Pick`, { Tool = Id })
	self.PendingPick = Id
end

function Bench:PressAt(Screen: Vector2)
	if self.Recoiling then return end
	local R = self:Hit(Screen)
	local What = R and self:Classify(R.Instance)
	self.PressScreen = Screen
	if self.Hand == `Tweezers` and self.PlateOpen and not self.Holding and not (What and (What.Kind == `Organ` or What.Kind == `Tool`)) then
		local Near = self:NearestOrgan(Screen)
		if Near then What = { Kind = `Organ`; Organ = Near } end
	end
	if not self.Hand then
		if What and What.Kind == `Tool` then self:Key(table.find(Config.Tools, What.Tool) or 0) end
		return
	end
	if not What then return end
	if What.Kind == `Tool` and What.Tool ~= self.Hand then self:Key(table.find(Config.Tools, What.Tool) or 0) return end
	local St = self.Steps[self.StepIndex]
	if self.Hand == `Scalpel` and (What.Kind == `Plate` or What.Kind == `Body`) and St and St.Id == `Trace` then
		self:BeginTrace()
		return
	end
	if What.Kind == `SideKey` or What.Kind == `WingPlate` then
		self.Holding_ = { Target = if What.Kind == `SideKey` then `SideKey` else `WingPlate`; Since = os.clock(); Screen = Screen }
		return
	end
	if What.Kind == `Plate` then
		local Target = `Plate`
		if St and St.Id == `Inspect` and self.Hand == `Loupe` then Target = `HiddenSeam` end
		self.Api.Send(`Use`, { Target = Target })
		self.LastUse = Target
		return
	end
	if What.Kind == `Organ` then
		self.Api.Send(`Use`, { Target = `Organ`; Organ = What.Organ })
		self.LastUse = `Organ`
		return
	end
end

function Bench:Release()
	self.Holding_ = nil
	self.Ring.Visible = false
	if self.Tracing then self:EndTrace() end
end

function Bench:PutHere()
	if not self.Hand then return end
	local R = self:Hit()
	local What = R and self:Classify(R.Instance)
	-- a desk spot hidden behind a panel would lose the tool: over a panel it goes back to the roll
	if What and What.Kind == `Desk` and not self:OverChrome() then
		self.PutPoint = R.Position
		self:Put(`Desk`)
	else
		self:Put(`Roll`)
	end
end

function Bench:Put(Spot: string)
	if not self.Hand or self.Holding then
		if self.Holding then self:SetHint(`Set the part down on the card first`, true) end
		return
	end
	self.PendingPut = Spot
	self.Api.Send(`Put`, { Spot = Spot })
end

function Bench:PadBack()
	if self.Hand then self:Put(`Roll`) return true end
	return false
end

function Bench:UseCard()
	if self.Hand ~= `Loupe` then self:SetHint(`Pick up the Loupe (3) to look the card over`, true) return end
	self.Api.Send(`Use`, { Target = `Card` })
end

function Bench:PlaceOn(i: number)
	local S = self.SlotButtons[i]
	if not S or not self.Holding then return end
	local Slot = self.Revealed[S.Organ]
	if not Slot then return end
	self.PendingPlace = i
	self.Api.Send(`Place`, { Organ = self.Holding; Slot = Slot })
end

----------------------------------------------------------------------------------------------------- the trace
function Bench:PlatePoint(Screen: Vector2?)
	local O, D = self:PointerRay(Screen)
	if not O or math.abs(D.Y) < 1e-4 then return nil end
	local t = (self.SeamCentre.Y - O.Y) / D.Y
	if t <= 0 then return nil end
	return O + D * t
end

function Bench:BeginTrace()
	self.Tracing = { Points = {}; Last = 0 }
	self.Trail:ClearAllChildren()
	self:Clip(`Trace`)
end

function Bench:SampleTrace(P: Vector3)
	local Tr = self.Tracing
	if not Tr or #Tr.Points >= 380 then return end
	local x = (P.X - self.SeamCentre.X) / self.SeamR
	local y = -(P.Z - self.SeamCentre.Z) / self.SeamR
	table.insert(Tr.Points, { math.floor(x * 1000) / 1000, math.floor(y * 1000) / 1000 })
	-- join to the last sample unless the pointer jumped (left the plate and came back): then start a fresh run
	local From = if Tr.LastP and (P - Tr.LastP).Magnitude < self.SeamR * 0.35 then Tr.LastP else P
	Tr.LastP = P
	stroke(From, P, 0.13, Color3.fromRGB(30, 6, 4), Enum.Material.SmoothPlastic, 0.045, self.Trail).Name = `CutEdge`
	stroke(From, P, 0.07, Color3.fromRGB(255, 70, 40), Enum.Material.Neon, 0.06, self.Trail).Name = `Cut`
end

function Bench:EndTrace()
	local Tr = self.Tracing
	self.Tracing = nil
	if not Tr then return end
	if #Tr.Points < 8 then self:SetHint(`Draw all the way round the seam`, true) self.Trail:ClearAllChildren() return end
	self.LastUse = `Seam`
	self.Api.Send(`Use`, { Target = `Seam`; Points = Tr.Points })
end

----------------------------------------------------------------------------------------------------- per frame
function Bench:ToolHandCF(T, Target: Vector3, Lift: number)
	-- the tool tilted ~35 degrees, tip first, its tip at Target (raised by Lift)
	local R = CFrame.Angles(math.rad(-35), 0, 0)
	return CFrame.new(Target + Vector3.new(0, Lift, 0)) * R * CFrame.new(-T.Tip)
end

function Bench:Step(Dt: number)
	if self.Destroyed then return end
	local Now = os.clock()
	if self.TagLabels and Now >= (self.NextTagFit or 0) then
		self.NextTagFit = Now + 0.5
		uniformText(self.TagLabels)
	end
	-- the tool in hand follows the pointer
	if self.Hand then
		local T = self.Tools[self.Hand]
		local R = self:Hit()
		local P = if R and not self:OverChrome() then R.Position else nil
		if self.TestPoint then P = self.TestPoint end
		-- off the bench (over a panel, or outside the view) the tool waits where it was, or above the specimen
		if P then self.LastPoint = P else P = self.LastPoint or HOVER R = nil end
		if P then
			local Over = R and self:Classify(R.Instance)
			local Lift = if self.Holding_ or self.Tracing then 0.02 else (if Over and (Over.Kind == `Desk` or Over.Kind == `Roll` or Over.Kind == `Set`) then 0.45 else 0.18)
			local Goal = self:ToolHandCF(T, P, Lift)
			T.CF = T.CF:Lerp(Goal, math.min(1, Dt * 18))
			setBone(T, `Root`, T.CF)
		end
		if self.Tracing then
			self.Tracing.Last += Dt
			if self.Tracing.Last >= 1 / TRACE_HZ then
				self.Tracing.Last = 0
				local PP = self:PlatePoint()
				if PP then self:SampleTrace(PP) end
			end
		end
		-- the held organ rides on the tweezers' tips
		if self.Holding then
			local B = self.Specimen.Bones[self:BoneOf(self.Holding)]
			if B then
				local Tip = T.CF * T.Tip
				local Goal = CFrame.new(Tip - Vector3.new(0, 0.25, 0) - B.Head)
				for Bone, X in self.Specimen.Bones do
					if Bone == self.Holding or (Bone == `FireGland` and self.Holding == `FireGland`) then setBone(self.Specimen, Bone, X.CF:Lerp(Goal, math.min(1, Dt * 20))) end
				end
			end
		end
	end
	-- Key/Driver: a hold ring fills; each fill sends one turn
	local H = self.Holding_
	if H then
		local Pos = self:Pointer()
		self.Ring.Visible = true
		self.Ring.Position = UDim2.fromOffset(Pos.X - self.UI.AbsolutePosition.X, Pos.Y - self.UI.AbsolutePosition.Y)
		local k = math.clamp((Now - H.Since) / TURN_EVERY, 0, 1)
		self.RingGrad.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(math.max(k - 0.001, 0), 0),
			NumberSequenceKeypoint.new(math.min(k + 0.001, 1), 1), NumberSequenceKeypoint.new(1, 1) })
		if k >= 1 then
			H.Since = Now
			self.LastUse = H.Target
			self.Api.Send(`Use`, { Target = H.Target })
		end
	end
	-- tools not in hand: on their slot, or where they were put on the desk
	for Id, T in self.Tools do
		if Id ~= self.Hand then
			local Goal = T.RestCF or CFrame.identity
			if (T.CF.Position - Goal.Position).Magnitude > 0.002 or T.CF ~= Goal then
				T.CF = T.CF:Lerp(Goal, math.min(1, Dt * 12))
				setBone(T, `Root`, T.CF)
			end
		end
	end
	self:StepCamera(Dt, Now)
end

----------------------------------------------------------------------------------------------------- the camera
-- The view is a shot: a focus point, a distance along the wide shot's line of sight, a lens (FOV) and a yaw round the
-- focus. Each frame the camera springs toward the shot the bench is in (critically damped: quick to start, slow to
-- land). Close shots come only while the step's own tool is in hand, so the roll is back in view whenever a tool is
-- being chosen. Kicks (a quick lens punch) and shakes land on the moments: the plate giving, a lift, a place, a slip.
-- The pointer ray and ToScreen read the live camera, so clicks stay true while it moves.
local WIDE_FOCUS = Vector3.new(0, 0, 1.3)
local WIDE_OFFSET = CAMERA_CF.Position - WIDE_FOCUS
local WIDE_DIST = WIDE_OFFSET.Magnitude
local WIDE_DIR = WIDE_OFFSET.Unit

function Bench:ShotFor(): (Vector3, number, number, number, number)
	-- returns Focus, Dist, FOV, Yaw (degrees), spring rate
	local Sp = self.Specimen
	if self.Finished then
		-- the reveal: back off and swing round the finished specimen
		local t = os.clock() - self.Finished
		return WIDE_FOCUS:Lerp(self.SeamCentre, 0.5), WIDE_DIST * 0.9, 34, math.clamp(t * 4, 0, 14), 2.2
	end
	if not self.Loaded then return WIDE_FOCUS + Vector3.new(0, 0.6, 0), WIDE_DIST * 1.3, 46, -6, 3 end
	local St = self.Steps[self.StepIndex]
	local Id, Hand = St and St.Id, self.Hand
	local Near = function(P: Vector3, k: number) return WIDE_FOCUS:Lerp(P, k) end
	if Id == `Unwind` and Hand == `Key` and Sp.Bones.SideKey then
		return Near(Sp.Bones.SideKey.Head, 0.6), WIDE_DIST * 0.82, 30, -7, 4.5
	elseif Id == `Unscrew` and Hand == `Driver` then
		local B = Sp.Bones[`WingPlate{math.min((self.Progress or 0) + 1, 4)}`]
		local P = if B then B.Head else self.SeamCentre
		return Near(P, 0.6), WIDE_DIST * 0.82, 30, if P.X >= 0 then 6 else -6, 4
	elseif Id == `Inspect` and Hand == `Loupe` then
		return Near(self.SeamCentre, 0.85), WIDE_DIST * 0.72, 22, 3, 3.2 -- the loupe's look: slow, tight
	elseif Id == `Trace` and Hand == `Scalpel` then
		return Near(self.SeamCentre, 0.8), WIDE_DIST * 0.8, 28, 0, 4
	elseif Id == `Pry` and Hand == `Driver` then
		return Near(self.SeamCentre, 0.75), WIDE_DIST * 0.8, 29, 4, 4
	elseif Id == `Lift` and Hand == `Tweezers` and self.PlateOpen then
		if self.Holding then
			-- a part in the tweezers: ease back and lean toward the specimen card
			return Near(self.SeamCentre, 0.55) + Vector3.new(0.5, 0, 0), WIDE_DIST * 0.88, 32, 5, 3.5
		end
		return Near(self.SeamCentre, 0.85), WIDE_DIST * 0.74, 25, -3, 4
	end
	return WIDE_FOCUS, WIDE_DIST, CAMERA_FOV, 0, 3
end

function Bench:Kick(Fov: number, Shake: number?)
	-- a lens punch (degrees narrower, springs back) and an optional shake (studs)
	local C = self.Cam
	if not C then return end
	C.FovV -= Fov * 14
	if Shake then self.ShakeUntil = os.clock() + 0.18 self.ShakeAmp = Shake end
end

function Bench:StepCamera(Dt: number, Now: number)
	local Focus, Dist, Fov, Yaw, Rate = self:ShotFor()
	local C = self.Cam
	if not C then
		-- the first frame: start wide and high so the bench opens on a slow push-in
		C = { Focus = Focus; FocusV = Vector3.zero; Dist = Dist; DistV = 0; Fov = Fov; FovV = 0; Yaw = Yaw; YawV = 0 }
		self.Cam = C
	end
	Dt = math.min(Dt, 1 / 30)
	local w = Rate
	local function spring(x, v, goal)
		local a = (goal - x) * w * w - v * 2 * w
		v += a * Dt
		return x + v * Dt, v
	end
	C.Focus, C.FocusV = spring(C.Focus, C.FocusV, Focus)
	C.Dist, C.DistV = spring(C.Dist, C.DistV, Dist)
	C.Fov, C.FovV = spring(C.Fov, C.FovV, Fov)
	C.Yaw, C.YawV = spring(C.Yaw, C.YawV, Yaw)
	-- alive: a slow breath of drift, stilled while drawing or holding a turn so the hand stays steady
	local Still = self.Tracing or self.Holding_
	self.Drift = (self.Drift or 0) + (if Still then -Dt else Dt) * 2
	self.Drift = math.clamp(self.Drift, 0, 1)
	local d = self.Drift
	local Sway = Vector3.new(math.sin(Now * 0.37) * 0.05, math.sin(Now * 0.53) * 0.03, 0) * d
	local Dir = CFrame.Angles(0, math.rad(C.Yaw + math.sin(Now * 0.23) * 0.5 * d), 0):VectorToWorldSpace(WIDE_DIR)
	local CF = CFrame.lookAt(C.Focus + Dir * C.Dist, C.Focus) * CFrame.new(Sway)
	if self.ShakeUntil and Now < self.ShakeUntil then
		local a = (self.ShakeUntil - Now) / 0.18 * (self.ShakeAmp or 0.08)
		CF *= CFrame.new((math.random() - 0.5) * a, (math.random() - 0.5) * a, 0) * CFrame.Angles(0, 0, (math.random() - 0.5) * a * 0.15)
	end
	local Cam = workspace.CurrentCamera
	Cam.CameraType = Enum.CameraType.Scriptable
	Cam.CFrame = CF + STAGE
	Cam.FieldOfView = math.clamp(C.Fov, 12, 60)
	self.CamBase = CF
end

----------------------------------------------------------------------------------------------------- server replies
function Bench:OpenPlate()
	local Sp = self.Specimen
	local B = Sp.Bones.PlateHinge
	if not B or self.PlateOpen then return end
	self.PlateOpen = true
	self:Kick(5, 0.12) -- the plate gives
	local Axis = B.Axis or Vector3.new(0, 0, 1)
	local V = new(`NumberValue`, { Value = 0 })
	V.Changed:Connect(function(a)
		setBone(Sp, `PlateHinge`, CFrame.new(B.Head) * CFrame.fromAxisAngle(Axis, math.rad(a)) * CFrame.new(-B.Head))
	end)
	TweenService:Create(V, TweenInfo.new(0.9, Enum.EasingStyle.Back, Enum.EasingDirection.Out, 0, false, 0.05), { Value = OPEN_DEG }):Play()
	task.delay(1.2, function() V:Destroy() end)
	for _, D in self.SeamDots do D.Transparency = 1 end
	self.Trail:ClearAllChildren()
end

function Bench:TurnKey()
	local Sp = self.Specimen
	local B = Sp.Bones.SideKey
	if not B then return end
	self.KeyAngle = (self.KeyAngle or 0) + 45
	self:Kick(0.6)
	local Axis = B.Axis or Vector3.new(1, 0, 0)
	local From = (self.KeyAngle - 45)
	local V = new(`NumberValue`, { Value = From })
	V.Changed:Connect(function(a) setBone(Sp, `SideKey`, CFrame.new(B.Head) * CFrame.fromAxisAngle(Axis, math.rad(a)) * CFrame.new(-B.Head)) end)
	TweenService:Create(V, TweenInfo.new(0.16, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Value = self.KeyAngle }):Play()
	task.delay(0.3, function() V:Destroy() end)
end

function Bench:PopWingPlate(k: number)
	local Sp = self.Specimen
	local Bone = `WingPlate{k}`
	local B = Sp.Bones[Bone]
	if not B then return end
	local Out = Vector3.new(if B.Head.X >= 0 then 1 else -1, 0.6, 0) * 0.6
	self:Kick(1.5, 0.05)
	local V = new(`NumberValue`, { Value = 0 })
	V.Changed:Connect(function(t) setBone(Sp, Bone, CFrame.new(Out * t) * CFrame.new(B.Head) * CFrame.Angles(0, 0, t * 0.8) * CFrame.new(-B.Head)) end)
	TweenService:Create(V, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Value = 1 }):Play()
	task.delay(0.35, function() fadeBone(Sp, Bone, 1, 0.3) end)
	task.delay(0.8, function() V:Destroy() end)
end

function Bench:DropHeld()
	if not self.Holding then return end
	local Id = self.Holding
	self.Holding = nil
	local B = self.Specimen.Bones[Id]
	if B then
		local From = B.CF
		local V = new(`NumberValue`, { Value = 0 })
		V.Changed:Connect(function(t) setBone(self.Specimen, Id, From:Lerp(CFrame.identity, ease(t))) end)
		TweenService:Create(V, TweenInfo.new(0.35), { Value = 1 }):Play()
		task.delay(0.5, function() V:Destroy() end)
	end
end

function Bench:Update(Reply)
	if self.Destroyed or typeof(Reply) ~= `table` then return end
	local Api = self.Api
	-- the hand
	if Reply.Hand ~= nil or (Reply.Ok and self.PendingPut and Reply.Spot) then
		local Old = self.Hand
		if Reply.Spot then -- put down
			local T = Old and self.Tools[Old]
			if T then
				if Reply.Spot == `Desk` and self.PutPoint then
					local Centre = T.Layout.Bones.Root.Head
					local P = self.PutPoint
					T.RestCF = CFrame.new(Vector3.new(P.X - Centre.X, 0.01 - T.Bottom, P.Z - Centre.Z)) * CFrame.new(0, 0, 0)
					T.Spot = `Desk`
				else
					T.RestCF = CFrame.identity
					T.Spot = `Roll`
				end
			end
			self.Hand = nil
			self:Clip(`Put`, true)
		elseif Reply.Hand then
			if Old and Old ~= Reply.Hand then self.Tools[Old].RestCF = CFrame.identity self.Tools[Old].Spot = `Roll` end
			self.Hand = Reply.Hand
			if Old ~= Reply.Hand then self:Clip(`Pick`) pcall(Kit.PlaySound, `Tick`, 0.4, 1.4) end
		end
		self.PendingPut, self.PutPoint, self.PendingPick = nil, nil, nil
	end
	if Reply.Slip then
		self:DropHeld()
		self.Recoiling = true
		self.Holding_ = nil
		self.Ring.Visible = false
		self:Clip(`Recoil`)
		self:Kick(-1, 0.1)
		if Api.Sound then Api.Sound(`Wrong`) end
		local Why = ({ Flag = `That cog is loose: it isn't part of the specimen`; FirstOrgan = `The fire-gland comes out first`;
			WrongSlot = `Not that outline`; NotYet = `Not yet: follow the procedure` })[Reply.Why] or `Slipped!`
		self:SetHint(Why, true)
		local L = self.StepLines[self.StepIndex]
		if L then
			L.TextColor3 = Color3.fromRGB(255, 90, 80)
			task.delay(0.5, function() if not self.Destroyed then self:RefreshSteps() end end)
		end
		task.delay(Config.RecoilSeconds or 0.8, function() self.Recoiling = false end)
	elseif Reply.Ok == false then
		if Api.Sound then Api.Sound(`Wrong`) end
		local Why = ({ WrongTool = `Wrong tool for this step`; WrongTarget = `Not there`; Incomplete = `The cut must go all the way round` })[Reply.Why] or `Not quite`
		self:SetHint(Why, true)
		if Reply.Why == `Incomplete` then self.Trail:ClearAllChildren() end
	end
	if Reply.Reveal then
		for Id, Slot in Reply.Reveal do self.Revealed[Id] = Slot end
		self:Clip(`Inspect`)
		self:RefreshCard()
		for _, S in self.SlotButtons do if S.Button.Visible then S.Button.BackgroundTransparency = 1 TweenService:Create(S.Button, TweenInfo.new(0.5), { BackgroundTransparency = 0.2 }):Play() end end
	end
	if Reply.Holding then
		self.Holding = Reply.Holding
		self:Clip(`Lift`)
		self:Kick(2)
		if Api.Sound then Api.Sound(`Good`) end
	end
	if Reply.Placed then
		local Id = Reply.Placed
		self.Placed[Id] = true
		self.Holding = nil
		fadeBone(self.Specimen, Id, 1, 0.35)
		if Id == `FireGland` then fadeBone(self.Specimen, `FireGland`, 1, 0.35) end
		self:Clip(`Place`)
		self:Kick(-1.5)
		if Api.Sound then Api.Sound(`Correct`, self:PlacedCount()) end
		local S = self.SlotButtons[self.PendingPlace or 0]
		if S and Api.Burst then Api.Burst(S.Button, true) end
		self:RefreshCard()
		if Reply.Done then self:Clip(`Done`) self:SetHint(`Specimen complete`) self.Finished = os.clock() end
	end
	-- progress and steps
	if Reply.Progress then
		self.Progress = Reply.Progress
		if self.LastUse == `SideKey` then self:TurnKey() pcall(Kit.PlaySound, `Tick`, 0.35, 1.2) end
		if self.LastUse == `WingPlate` then self:PopWingPlate(Reply.Progress) end
		self:Clip(`Unwind`)
	end
	if Reply.Step and Reply.Step ~= self.StepIndex then
		local Done = self.Steps[self.StepIndex]
		self.StepIndex = Reply.Step
		self.Progress = 0
		self.Holding_ = nil
		self.Ring.Visible = false
		if Done then
			if Done.Id == `Pry` then self:OpenPlate() self:Clip(`Pry`) end
			if Done.Id == `Trace` then self:Clip(`Trace`) for _, P in self.Trail:GetChildren() do if P.Name == `Cut` then P.Color = Color3.fromRGB(150, 26, 20) P.Material = Enum.Material.SmoothPlastic end end end
			if Done.Id == `Inspect` then self:Clip(`Inspect`) end
			if Api.Sound then Api.Sound(`Good`) end
		end
		Api.SetScore(`Step {math.min(self.StepIndex, #self.Steps)}/{#self.Steps}`)
	end
	self:RefreshSteps()
	self:RefreshTools()
end

function Bench:PlacedCount(): number
	local n = 0
	for _ in self.Placed do n += 1 end
	return n
end

function Bench:Destroy()
	self.Destroyed = true
	for _, C_ in self.Conns do C_:Disconnect() end
	for _, T in self.Tracks do pcall(function() T:Stop(0) end) end
	if _G.NHAnatomyBench == self then _G.NHAnatomyBench = nil end
	if self.Bound then pcall(function() RunService:UnbindFromRenderStep(self.Bound) end) end
	if self.Stage then self.Stage:Destroy() end
	if self.Vignette then self.Vignette:Destroy() end
	-- the camera and the HUD go back as they were
	local Cam = workspace.CurrentCamera
	local W = self.CamWas
	if W then
		Cam.CameraType = if W.Type == Enum.CameraType.Scriptable then Enum.CameraType.Custom else W.Type
		Cam.FieldOfView = W.FOV
		local Hum = Players.LocalPlayer.Character and Players.LocalPlayer.Character:FindFirstChildOfClass(`Humanoid`)
		Cam.CameraSubject = Hum or W.Subject
	end
	for _, G in self.HiddenGuis or {} do if G.Parent then G.Enabled = true end end
	if self.UI then self.UI:Destroy() end
	if self.Cover then self.Cover:Destroy() end
end

----------------------------------------------------------------------------------------------------- Studio test hooks
if RunService:IsStudio() then
	function Bench:_TestKey(n: number) self.TestPoint = HOVER self:Key(n) end
	function Bench:_TestUse(Target: string, Organ: string?)
		self.LastUse = Target
		-- the tool in hand goes to what it is used on (hook runs have no real pointer)
		local Sp = self.Specimen
		if Target == `SideKey` and Sp.Bones.SideKey then self.TestPoint = Sp.Bones.SideKey.Head
		elseif Target == `Plate` then self.TestPoint = self.SeamCentre
		elseif Target == `Organ` and Organ and Sp.Bones[self:BoneOf(Organ)] then self.TestPoint = Sp.Bones[self:BoneOf(Organ)].Head + Vector3.new(0, 0.35, 0)
		end
		self.Api.Send(`Use`, { Target = Target; Organ = Organ })
	end
	function Bench:_TestTrace(Points, Delay: number?)
		if not Points then
			Points = {}
			local Rx, Ry = 1, 1.3
			if self.Def and self.Def.Seam then Rx, Ry = self.Def.Seam.Rx, self.Def.Seam.Ry end
			for i = 0, 47 do local a = i / 48 * math.pi * 2 table.insert(Points, { math.cos(a) * Rx, math.sin(a) * Ry }) end
		end
		self:BeginTrace()
		for _, P in Points do
			self:SampleTrace(self.SeamCentre + Vector3.new(P[1] * self.SeamR, 0, -P[2] * self.SeamR))
			if self.Hand then
				local T = self.Tools[self.Hand]
				T.CF = self:ToolHandCF(T, self.SeamCentre + Vector3.new(P[1] * self.SeamR, 0, -P[2] * self.SeamR), 0.02)
				setBone(T, `Root`, T.CF)
			end
			if Delay then task.wait(Delay) end
		end
		local Tr = self.Tracing
		self.Tracing = nil
		self.LastUse = `Seam`
		self.Api.Send(`Use`, { Target = `Seam`; Points = Points })
		return Tr and #Tr.Points or 0
	end
	function Bench:_TestPlace(Slot: string)
		for i, S in self.SlotButtons do if self.Revealed[S.Organ] == Slot then self:PlaceOn(i) return true end end
		return false
	end
	function Bench:_TestPut(Spot: string, Point: Vector3?)
		self.PutPoint = Point
		self:Put(Spot)
	end
	function Bench:_TestState()
		local Playing = {}
		if self.Animator then for _, T in self.Animator:GetPlayingAnimationTracks() do table.insert(Playing, T.Animation and T.Name or `?`) end end
		return { Step = self.StepIndex; Hand = self.Hand; Holding = self.Holding; Placed = self:PlacedCount(); Revealed = self.Revealed;
			Rig = self.Rig ~= nil; Tracks = (function() local n = 0 for _ in self.Tracks do n += 1 end return n end)(); Playing = Playing;
			Real = self.Specimen.Real; PlateOpen = self.PlateOpen == true; Tools = (function() local t = {} for Id, T in self.Tools do t[Id] = T.Spot end return t end)() }
	end
end

----------------------------------------------------------------------------------------------------- the intro docket
-- The lesson intro for bench lessons, in place of the chalkboard and the gold 3-2-1 orb: a specimen docket hangs on a
-- red string over a dark, candle-warm room (species, Latin, level, teacher, time, twist, the task in hand, a wax seal
-- for the mode) and a candle burns down past three marks for the count. The Activities controller calls
-- Bench.Docket(Screen, Message) when the lesson opens, :Count(n) each second, and :Leave() when the bench takes over.
-- Every text sits in fractions of the docket, clear of its frame art; one size cap per role keeps the rows even.
local DOCKET_INK = Color3.fromRGB(46, 34, 28)
local DOCKET_RED = Color3.fromRGB(140, 28, 34)
local DOCKET_DIM = Color3.fromRGB(110, 92, 76)
local DOCKET_LINE = Color3.fromRGB(170, 150, 124)
local WAX = Color3.fromRGB(236, 226, 200)

local function docketText(Parent: Instance, Str: string, Props): TextLabel
	-- an explicit size, fitted by fitDocket (TextScaled does not hold on these labels in Play: see uniformText)
	local T = new(`TextLabel`, { BackgroundTransparency = 1; Text = Str; TextColor3 = DOCKET_INK; Font = Enum.Font.Merriweather; TextScaled = false; TextSize = 14;
		RichText = true; TextWrapped = false; TextXAlignment = Enum.TextXAlignment.Center; TextYAlignment = Enum.TextYAlignment.Center; ZIndex = 3 }, Parent)
	for K, V in Props or {} do (T :: any)[K] = V end
	return T
end

-- the largest size that fits a label's box (wrapped labels: every line inside the height), in the GUI's own units.
-- The label's own UIScale (the numeral pop) is left out so the pop still reads; rich-text tags get a 6% width margin.
local function fitSize(L: TextLabel, Max: number?): number?
	local k = scaleAbove(L.Parent :: Instance)
	local W, H = L.AbsoluteSize.X / k, L.AbsoluteSize.Y / k
	if W < 4 or H < 4 then return nil end
	local Size = math.min(math.floor(H), Max or 200)
	while Size > 8 do
		local B = TextService:GetTextSize(L.ContentText, Size, L.Font, Vector2.new(if L.TextWrapped then W else 10000, 10000))
		if B.X * 1.06 <= W and B.Y <= H then break end
		Size -= 1
	end
	return Size
end
-- Groups share one size (the smallest fit); a lone label is its own group. Max caps a group.
local function fitDocket(Groups: { { Labels: { TextLabel }, Max: number? } })
	for _, G in Groups do
		local Best
		for _, L in G.Labels do
			if L.Parent then
				local S = fitSize(L, G.Max)
				if S then Best = math.min(Best or S, S) end
			end
		end
		if Best then
			for _, L in G.Labels do
				if L.TextScaled then L.TextScaled = false end
				if L.TextSize ~= Best then L.TextSize = Best end
			end
		end
	end
end

local function rule(Parent: Instance, Y: number, Thick: number, Color: Color3, X0: number?, X1: number?)
	return new(`Frame`, { BackgroundColor3 = Color; BorderSizePixel = 0; ZIndex = 3; Position = UDim2.fromScale(X0 or 0.11, Y);
		Size = UDim2.new((X1 or 0.89) - (X0 or 0.11), 0, 0, Thick) }, Parent)
end

function Bench.Docket(Screen, Message)
	local Gui: ScreenGui = Screen.Gui
	local P = Message.Payload or {}
	local E = Electives.Get and Electives.Get(`Anatomy`) or {}
	local Ids = Config.UI or {}
	local Calm = Kit.ReducedMotion and Kit.ReducedMotion()
	local D = {}

	-- the room: near-black with a warm pool where the candle stands
	local Room = new(`Frame`, { Name = `DocketRoom`; Size = UDim2.fromScale(1, 1); BackgroundColor3 = Color3.new(1, 1, 1); BorderSizePixel = 0; ZIndex = 1 }, Gui)
	Room:SetAttribute(`NHNotPanel`, true)
	new(`UIGradient`, { Rotation = 0; Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromRGB(10, 7, 6)), ColorSequenceKeypoint.new(0.6, Color3.fromRGB(12, 8, 7)),
		ColorSequenceKeypoint.new(0.76, Color3.fromRGB(52, 31, 15)), ColorSequenceKeypoint.new(0.92, Color3.fromRGB(14, 9, 7)), ColorSequenceKeypoint.new(1, Color3.fromRGB(8, 6, 5)) }) }, Room)
	local Fit = {}
	local function one(L: TextLabel, Max: number?) L.TextScaled = false L.TextWrapped = L.TextWrapped and L.Name == `Task` table.insert(Fit, { Labels = { L }; Max = Max }) return L end
	one(text(Room, `NIGHTMARE HIGHSCHOOL  \u{00B7}  ELECTIVE  \u{00B7}  {string.upper(E.Name or `Anatomy`)}`, { Font = Enum.Font.Merriweather; TextColor3 = Color3.fromRGB(222, 204, 170);
		Position = UDim2.fromScale(0.025, 0.03); Size = UDim2.fromScale(0.5, 0.034); ZIndex = 2 }))
	-- FitCheck reads the room's white base colour, not the near-black gradient over it; on the real ground this cream is ~13:1
	Room:FindFirstChildOfClass(`TextLabel`):SetAttribute(`NHContrastOk`, true)

	-- the docket: a CanvasGroup so it swings and fades as one piece
	local Group = new(`CanvasGroup`, { Name = `Docket`; BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.42, 0.53);
		Size = UDim2.fromScale(0.8, 0.86); ZIndex = 4; Rotation = -3 }, Gui)
	new(`UIAspectRatioConstraint`, { AspectRatio = 0.8; DominantAxis = Enum.DominantAxis.Height }, Group)
	local Card = new(`Frame`, { Name = `Card`; BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1); ZIndex = 2 }, Group)
	if typeof(Ids.Specimen) == `number` and Ids.Specimen > 0 then
		new(`ImageLabel`, { Name = `Skin`; BackgroundTransparency = 1; Image = `rbxassetid://{Ids.Specimen}`; Size = UDim2.fromScale(1, 1); ZIndex = 2 }, Card)
	else
		Card.BackgroundTransparency = 0 Card.BackgroundColor3 = Color3.fromRGB(240, 232, 214)
		new(`UIStroke`, { Color = GOLD; Thickness = 3 }, Card)
	end
	-- the eyelet the string runs through
	local Eye = new(`Frame`, { Name = `Eyelet`; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.075); Size = UDim2.fromScale(0.05, 0.04);
		BackgroundColor3 = Color3.fromRGB(30, 22, 18); ZIndex = 3 }, Card)
	new(`UICorner`, { CornerRadius = UDim.new(1, 0) }, Eye)
	new(`UIStroke`, { Color = Color3.fromRGB(150, 118, 62); Thickness = 3 }, Eye)

	-- the card art carries its own double red rule at ~18% down: header and subline sit above it, the name below
	one(docketText(Card, `SPECIMEN  DOCKET`, { Font = Fonts.Title or Enum.Font.Fantasy; TextColor3 = DOCKET_RED; Position = UDim2.fromScale(0.15, 0.098); Size = UDim2.fromScale(0.7, 0.04) }))
	one(docketText(Card, `{E.Name or `Anatomy`}  \u{00B7}  Room {E.Room or `R103`}  \u{00B7}  Level {P.Level or Message.Level or 1}`,
		{ TextColor3 = DOCKET_DIM; Position = UDim2.fromScale(0.15, 0.137); Size = UDim2.fromScale(0.7, 0.032) }))
	one(docketText(Card, string.upper(P.Name or `Specimen`), { Font = Fonts.Title or Enum.Font.Fantasy; Position = UDim2.fromScale(0.1, 0.235); Size = UDim2.fromScale(0.8, 0.07) }))
	one(docketText(Card, `<i>{P.Latin or ``}</i>`, { TextColor3 = DOCKET_DIM; Position = UDim2.fromScale(0.15, 0.315); Size = UDim2.fromScale(0.7, 0.04) }))

	-- the fields: a small-caps key and a value on a ruled line
	local Mode = if Message.Study then `Night Study` elseif Message.Practice then `Practice` else `Graded`
	local Limit = tonumber(Message.TimeLimit or P.TimeLimit) or 60
	local Fields = {
		{ `LEVEL`; `{P.Level or Message.Level or 1}  \u{2014}  {Mode}` };
		{ `TEACHER`; if Message.Substitute then `{Message.Substitute.Name} (substitute)` else (E.Teacher or ``) };
		{ `TIME`; string.format(`%d:%02d`, Limit // 60, Limit % 60) };
		{ `TWIST`; TWIST_TEXT[P.Twist] or `None tonight` };
	}
	local KeyLabels, ValueLabels = {}, {}
	for i, Fd in Fields do
		local Y = 0.385 + (i - 1) * 0.072
		table.insert(KeyLabels, docketText(Card, `<b>{Fd[1]}</b>`, { TextColor3 = DOCKET_DIM; TextXAlignment = Enum.TextXAlignment.Left; Position = UDim2.fromScale(0.14, Y + 0.006); Size = UDim2.fromScale(0.23, 0.034) }))
		table.insert(ValueLabels, docketText(Card, Fd[2], { TextXAlignment = Enum.TextXAlignment.Left; Position = UDim2.fromScale(0.38, Y); Size = UDim2.fromScale(0.48, 0.04) }))
		rule(Card, Y + 0.047, 1, DOCKET_LINE, 0.38, 0.86)
	end
	table.insert(Fit, { Labels = KeyLabels }) table.insert(Fit, { Labels = ValueLabels })
	rule(Card, 0.69, 1, DOCKET_RED)
	-- the task, in hand: wrapped inside the lower panel, left of the seal
	local Task = docketText(Card, `<i>{Message.Tagline or ``}</i>`, { Name = `Task`; TextWrapped = true; TextXAlignment = Enum.TextXAlignment.Left; TextYAlignment = Enum.TextYAlignment.Top;
		Position = UDim2.fromScale(0.14, 0.715); Size = UDim2.fromScale(0.5, 0.2) })
	one(Task, 28)
	-- the wax seal: the mode, stamped
	local SealHolder = new(`Frame`, { Name = `Seal`; BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.77, 0.8);
		Size = UDim2.fromScale(0.26, 0.26); ZIndex = 4 }, Card)
	new(`UIAspectRatioConstraint`, {}, SealHolder)
	if typeof(Ids.Seal) == `number` and Ids.Seal > 0 then
		new(`ImageLabel`, { BackgroundTransparency = 1; Image = `rbxassetid://{Ids.Seal}`; Size = UDim2.fromScale(1, 1); ZIndex = 4 }, SealHolder)
	else
		SealHolder.BackgroundColor3 = Color3.fromRGB(120, 24, 30) SealHolder.BackgroundTransparency = 0
		new(`UICorner`, { CornerRadius = UDim.new(1, 0) }, SealHolder)
	end
	one(docketText(SealHolder, string.upper(Mode), { TextColor3 = Color3.fromRGB(250, 226, 200); Font = Fonts.Title or Enum.Font.Fantasy;
		AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromScale(0.68, 0.2); ZIndex = 5 }))

	-- the string, from the top of the screen to the eyelet (outside the group, so it isn't clipped)
	local String = new(`Frame`, { Name = `DocketString`; BackgroundColor3 = Color3.fromRGB(150, 30, 30); BorderSizePixel = 0; AnchorPoint = Vector2.new(0.5, 0);
		Position = UDim2.fromScale(0.42, 0); Size = UDim2.new(0, 3, 0.15, 0); ZIndex = 3 }, Gui)

	-- the candle: a cream stick in a brass dish, three burn marks with their numerals, a flame with a warm glow
	local Stand = new(`Frame`, { Name = `CountCandle`; BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.76, 0.52);
		Size = UDim2.fromScale(0.3, 0.62); ZIndex = 4 }, Gui)
	new(`UIAspectRatioConstraint`, { AspectRatio = 0.5; DominantAxis = Enum.DominantAxis.Height }, Stand)
	-- the glow: nested faint discs, so the light falls off instead of reading as one flat circle
	local Glow = new(`Frame`, { Name = `Glow`; BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.42, 0.2); Size = UDim2.fromScale(1.3, 0.65); ZIndex = 3 }, Stand)
	for k = 1, 6 do
		local f = 1 - (k - 1) * 0.15
		local Ring = new(`Frame`, { AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromScale(f, f);
			BackgroundColor3 = Color3.fromRGB(255, 170, 70); BackgroundTransparency = 0.955; ZIndex = 3 }, Glow)
		new(`UICorner`, { CornerRadius = UDim.new(1, 0) }, Ring)
	end
	local Dish = new(`Frame`, { Name = `Dish`; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.42, 0.9); Size = UDim2.fromScale(0.8, 0.09);
		BackgroundColor3 = Color3.fromRGB(150, 118, 62); ZIndex = 4 }, Stand)
	new(`UICorner`, { CornerRadius = UDim.new(1, 0) }, Dish)
	new(`UIStroke`, { Color = Color3.fromRGB(70, 52, 30); Thickness = 4 }, Dish)
	local TOP, BASE = 0.3, 0.88 -- the stick's top (full height) and its foot, as fractions of the stand
	local Stick = new(`Frame`, { Name = `Stick`; AnchorPoint = Vector2.new(0.5, 1); Position = UDim2.fromScale(0.42, BASE); Size = UDim2.fromScale(0.3, BASE - TOP);
		BackgroundColor3 = Color3.new(1, 1, 1); ZIndex = 5 }, Stand)
	new(`UICorner`, { CornerRadius = UDim.new(0.12, 0) }, Stick)
	new(`UIGradient`, { Color = ColorSequence.new(Color3.fromRGB(255, 250, 236), WAX:Lerp(Color3.fromRGB(180, 160, 120), 0.4)) }, Stick)
	local Wick = new(`Frame`, { Name = `Wick`; AnchorPoint = Vector2.new(0.5, 1); Position = UDim2.fromScale(0.42, TOP); Size = UDim2.fromScale(0.025, 0.04);
		BackgroundColor3 = Color3.fromRGB(30, 20, 14); BorderSizePixel = 0; ZIndex = 6 }, Stand)
	local Flame = new(`Frame`, { Name = `Flame`; AnchorPoint = Vector2.new(0.5, 1); Position = UDim2.fromScale(0.42, TOP - 0.03); Size = UDim2.fromScale(0.14, 0.12);
		BackgroundColor3 = Color3.fromRGB(255, 190, 80); ZIndex = 7 }, Stand)
	new(`UICorner`, { CornerRadius = UDim.new(1, 0) }, Flame)
	local Core = new(`Frame`, { Name = `Core`; AnchorPoint = Vector2.new(0.5, 1); Position = UDim2.fromScale(0.5, 0.95); Size = UDim2.fromScale(0.5, 0.55);
		BackgroundColor3 = Color3.fromRGB(255, 244, 200); ZIndex = 8 }, Flame)
	new(`UICorner`, { CornerRadius = UDim.new(1, 0) }, Core)
	local Marks, Numerals = {}, {}
	for i = 1, 3 do
		local Y = TOP + (BASE - TOP) * (i - 0.35) / 3.2
		new(`Frame`, { Name = `Mark{i}`; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.42, Y); Size = UDim2.fromScale(0.3, 0.006);
			BackgroundColor3 = Color3.fromRGB(150, 120, 90); BorderSizePixel = 0; ZIndex = 6 }, Stand)
		Marks[4 - i] = { Y = Y; Label = text(Stand, tostring(4 - i), { Font = Fonts.Title or Enum.Font.Fantasy; TextColor3 = Color3.fromRGB(150, 132, 110);
			TextXAlignment = Enum.TextXAlignment.Left; AnchorPoint = Vector2.new(0, 0.5); Position = UDim2.fromScale(0.63, Y); Size = UDim2.fromScale(0.3, 0.07); ZIndex = 6 }) }
		Marks[4 - i].Label.TextScaled = false
		table.insert(Numerals, Marks[4 - i].Label)
	end
	table.insert(Fit, { Labels = Numerals })
	one(text(Stand, `THE COUNT BURNS DOWN`, { Font = Enum.Font.Merriweather; TextColor3 = Color3.fromRGB(190, 166, 130); TextXAlignment = Enum.TextXAlignment.Center;
		AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.fromScale(0.42, 0.955); Size = UDim2.fromScale(1.1, 0.045); ZIndex = 4 }))

	-- the flame flickers while the docket is up
	local Alive = true
	fitDocket(Fit)
	local NextFit = 0
	task.spawn(function()
		while Alive and Flame.Parent do
			if os.clock() >= NextFit then NextFit = os.clock() + 0.25 fitDocket(Fit) end
			local s = 1 + math.sin(os.clock() * 13) * 0.06 + math.sin(os.clock() * 7.3) * 0.05
			Flame.Size = UDim2.fromScale(0.14 * (2 - s), 0.12 * s)
			local g = 1 + math.sin(os.clock() * 5.1) * 0.03
			Glow.Size = UDim2.fromScale(1.3 * g, 0.65 * g)
			task.wait()
		end
	end)

	-- arrival: the docket drops on its string and swings to rest
	if not Calm then
		Group.Position = UDim2.fromScale(0.42, -0.5) Group.Rotation = -12 Group.GroupTransparency = 0.2
		String.Size = UDim2.new(0, 3, 0, 0)
		TweenService:Create(Group, TweenInfo.new(0.7, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Position = UDim2.fromScale(0.42, 0.53); GroupTransparency = 0 }):Play()
		TweenService:Create(Group, TweenInfo.new(1.4, Enum.EasingStyle.Elastic, Enum.EasingDirection.Out), { Rotation = -3 }):Play()
		TweenService:Create(String, TweenInfo.new(0.7, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Size = UDim2.new(0, 3, 0.15, 0) }):Play()
		Stand.Position = UDim2.fromScale(0.82, 0.52)
		TweenService:Create(Stand, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Position = UDim2.fromScale(0.76, 0.52) }):Play()
	end

	-- the count: the stick burns down to the mark, the mark's numeral lights, the spent ones go dim
	function D:Count(n: number)
		local M = Marks[n]
		if not M then return end
		for k, X in Marks do
			X.Label.TextColor3 = if k == n then Color3.fromRGB(250, 210, 150) elseif k > n then Color3.fromRGB(96, 84, 70) else Color3.fromRGB(150, 132, 110)
		end
		local Top = if n == 3 then TOP else Marks[n + 1].Y
		local Info = TweenInfo.new(if Calm then 0 else 0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
		TweenService:Create(Stick, Info, { Size = UDim2.fromScale(0.3, BASE - Top) }):Play()
		TweenService:Create(Wick, Info, { Position = UDim2.fromScale(0.42, Top) }):Play()
		TweenService:Create(Flame, Info, { Position = UDim2.fromScale(0.42, Top - 0.03) }):Play()
		TweenService:Create(Glow, Info, { Position = UDim2.fromScale(0.42, Top - 0.1) }):Play()
		if not Calm then
			local Sc = M.Label:FindFirstChildOfClass(`UIScale`) or new(`UIScale`, {}, M.Label)
			Sc.Scale = 1.35
			TweenService:Create(Sc, TweenInfo.new(0.3, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 }):Play()
		end
	end

	-- departure: the docket lifts away on its string, the candle and the room fade; the bench's own cover takes over
	function D:Leave()
		Alive = false
		local T = if Calm then 0 else 0.45
		local Info = TweenInfo.new(T, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
		TweenService:Create(Group, Info, { Position = UDim2.fromScale(0.42, -0.6); Rotation = -8; GroupTransparency = 1 }):Play()
		TweenService:Create(String, Info, { Size = UDim2.new(0, 3, 0, 0) }):Play()
		for _, X in Stand:GetDescendants() do
			if X:IsA(`GuiObject`) then
				local Goal: { [string]: any } = { BackgroundTransparency = 1 }
				if X:IsA(`TextLabel`) then Goal.TextTransparency = 1 end
				TweenService:Create(X, Info, Goal):Play()
			end
		end
		task.delay(T + 0.05, function()
			for _, X in { Group, String, Stand } do if X.Parent then X:Destroy() end end
			for _, X in Room:GetChildren() do if X:IsA(`TextLabel`) then X:Destroy() end end
			TweenService:Create(Room, TweenInfo.new(if Calm then 0 else 0.35), { BackgroundTransparency = 1 }):Play()
			task.delay(0.4, function() if Room.Parent then Room:Destroy() end end)
		end)
	end
	function D:Destroy()
		Alive = false
		for _, X in { Group, String, Stand, Room } do if X.Parent then X:Destroy() end end
	end
	D.Gui = Gui
	return D
end

-- the Leave lesson button as a brass tag (bench lessons): the Anatomy tag art behind ink text, clear of its hole
function Bench.SkinQuit(Quit: TextButton)
	local Ids = Config.UI or {}
	if not (typeof(Ids.Tag) == `number` and Ids.Tag > 0) then return end
	Quit.BackgroundTransparency = 1
	for _, X in Quit:GetChildren() do if X:IsA(`ImageLabel`) or X:IsA(`UIGradient`) or X:IsA(`UIStroke`) then X:Destroy() end end
	-- the tag art's hole sits 16-19% across: the text starts at 26%
	local Pad = Quit:FindFirstChildOfClass(`UIPadding`) or new(`UIPadding`, {}, Quit)
	Pad.PaddingLeft = UDim.new(0.26, 0) Pad.PaddingRight = UDim.new(0.06, 0)
	-- children are laid out inside the padded box, so the art's size and offset undo the padding and it fills the button
	local L, R, T, B = Pad.PaddingLeft.Scale, Pad.PaddingRight.Scale, Pad.PaddingTop.Scale, Pad.PaddingBottom.Scale
	new(`ImageLabel`, { Name = `TagSkin`; BackgroundTransparency = 1; Image = `rbxassetid://{Ids.Tag}`; ZIndex = math.max(Quit.ZIndex - 1, 1);
		Size = UDim2.fromScale(1 / (1 - L - R), 1 / (1 - T - B)); Position = UDim2.fromScale(-L / (1 - L - R), -T / (1 - T - B)) }, Quit)
	Quit.TextXAlignment = Enum.TextXAlignment.Left
	Quit.TextColor3 = DOCKET_INK
	Quit.Font = Enum.Font.Merriweather
	-- an explicit size inside the padded box (TextScaled does not hold in Play), refitted on resize
	local function fit()
		local k = scaleAbove(Quit.Parent :: Instance)
		local Pd = Quit:FindFirstChildOfClass(`UIPadding`)
		local AX, AY = Quit.AbsoluteSize.X / k, Quit.AbsoluteSize.Y / k
		local W = AX * (1 - (if Pd then Pd.PaddingLeft.Scale + Pd.PaddingRight.Scale else 0)) - (if Pd then Pd.PaddingLeft.Offset + Pd.PaddingRight.Offset else 0)
		local H = AY * (1 - (if Pd then Pd.PaddingTop.Scale + Pd.PaddingBottom.Scale else 0)) - (if Pd then Pd.PaddingTop.Offset + Pd.PaddingBottom.Offset else 0)
		if W < 4 or H < 4 then return end
		local Size = math.floor(H)
		while Size > 8 and TextService:GetTextSize(Quit.ContentText, Size, Quit.Font, Vector2.new(10000, 10000)).X * 1.04 > W do Size -= 1 end
		Quit.TextScaled = false
		Quit.TextWrapped = false
		Quit.TextSize = Size
	end
	fit()
	Quit:GetPropertyChangedSignal(`AbsoluteSize`):Connect(fit)
	Quit:GetPropertyChangedSignal(`Text`):Connect(fit)
end

return Bench
