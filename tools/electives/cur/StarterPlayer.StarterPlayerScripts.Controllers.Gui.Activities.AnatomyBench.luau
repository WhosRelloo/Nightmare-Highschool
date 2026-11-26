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
		for _, E in Prop.Pieces[Piece].Parts do E.Part.CFrame = CF * E.Rest end
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

	self:BuildViewport()
	self:BuildChrome()
	self:BuildArms()
	self:BindInput()
	self:RefreshSteps()
	self:RefreshTools()
	self:RefreshCard()
	if RunService:IsStudio() then _G.NHAnatomyBench = self end
	return self
end

function Bench:BuildViewport()
	local VF = new(`ViewportFrame`, { Name = `Bench`; Size = UDim2.fromScale(1, 1); BackgroundColor3 = Color3.fromRGB(12, 10, 12);
		-- a ViewportFrame has no sky or environment for the PBR maps: a near-neutral key from over the student's left
		-- shoulder and a strong ambient keep brass reading as brass instead of flat orange
		BorderSizePixel = 0; Ambient = Color3.fromRGB(112, 104, 96); LightColor = Color3.fromRGB(255, 240, 220);
		LightDirection = Vector3.new(0.35, -0.85, -0.4); ZIndex = 1 }, self.Content)
	local WM = new(`WorldModel`, {}, VF)
	local Cam = new(`Camera`, { FieldOfView = CAMERA_FOV; CFrame = CAMERA_CF }, VF)
	VF.CurrentCamera = Cam
	self.VF, self.World, self.Camera = VF, WM, Cam
	self.CamBase = CAMERA_CF
	-- a vignette over the viewport, warm at the candle's corner
	local Vig = new(`Frame`, { Name = `Vignette`; Size = UDim2.fromScale(1, 1); BackgroundTransparency = 0; BackgroundColor3 = Color3.new(0, 0, 0); ZIndex = 2 }, self.Content)
	new(`UIGradient`, { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(0.18, 1), NumberSequenceKeypoint.new(0.82, 1), NumberSequenceKeypoint.new(1, 0.35) }) }, Vig)
	Vig.Active = false

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
		for _, E in T.Pieces do for _, X in E.Parts do lo = math.min(lo, X.Part.Position.Y - X.Part.Size.Y / 2) end end
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
		local D = new(`Part`, { Name = `SeamDot`; Anchored = true; CanCollide = false; CanQuery = false; Shape = Enum.PartType.Ball;
			Size = Vector3.one * 0.06; Material = Enum.Material.Neon; Color = GOLD; Transparency = 1; CFrame = CFrame.new(P + Vector3.new(0, 0.03, 0)) }, WM)
		self.SeamDots[i] = D
	end
	self.Trail = new(`Folder`, { Name = `Trail` }, WM)
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
	Rig:PivotTo(SEAT_CF)
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

function Bench:SetHint(Str: string, Bad: boolean?)
	self.Hint.Text = Str
	self.Hint.TextColor3 = if Bad then Color3.fromRGB(255, 120, 110) else INK
end

function Bench:RefreshSteps()
	for i, St in self.Steps do
		local T = STEP_TEXT[St.Id] or { St.Id, `` }
		local Label = `{i}. {T[1]}  <font color="#9a8f80">({St.Tool})</font>`
		local L = self.StepLines[i]
		if i < self.StepIndex then
			L.Text = `<s>{i}. {T[1]}</s>`
			L.TextColor3 = DIM
		elseif i == self.StepIndex then
			L.Text = Label
			L.TextColor3 = GOLD
		else
			L.Text = Label
			L.TextColor3 = INK
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
		Tag.Button.BackgroundTransparency = if OnRoll or InHand then 0.1 else 0.55
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
		S.Button.BackgroundColor3 = if Done then Color3.fromRGB(92, 70, 28) else Color3.fromRGB(30, 24, 22)
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

function Bench:PointerRay(Screen: Vector2?)
	local VF = self.VF
	local Pos = Screen or self:Pointer()
	local Rel = Pos - VF.AbsolutePosition
	local Size = VF.AbsoluteSize
	if Size.X <= 0 or Size.Y <= 0 then return nil end
	local u, v = Rel.X / Size.X, Rel.Y / Size.Y
	local tanY = math.tan(math.rad(self.Camera.FieldOfView) / 2)
	local Aspect = Size.X / Size.Y
	local Dir = self.Camera.CFrame:VectorToWorldSpace(Vector3.new((2 * u - 1) * tanY * Aspect, (1 - 2 * v) * tanY, -1)).Unit
	return self.Camera.CFrame.Position, Dir, u, v
end

-- a world point to GUI space (PointerRay's inverse)
function Bench:ToScreen(W: Vector3): Vector2?
	local VF, Cam = self.VF, self.Camera
	local Size = VF.AbsoluteSize
	local p = Cam.CFrame:PointToObjectSpace(W)
	if p.Z >= 0 or Size.Y <= 0 then return nil end
	local tanY = math.tan(math.rad(Cam.FieldOfView) / 2)
	local x, y = p.X / -p.Z / (tanY * Size.X / Size.Y), p.Y / -p.Z / tanY
	return VF.AbsolutePosition + Vector2.new((x + 1) / 2 * Size.X, (1 - y) / 2 * Size.Y)
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
		local At = N > 0 and self:ToScreen(Sum / N) or nil
		if At and (At - Screen).Magnitude < BestD then Best, BestD = O.Id, (At - Screen).Magnitude end
	end
	return Best
end

-- true while the pointer is outside the viewport or over one of the chrome panels drawn on top of it
function Bench:OverChrome(): boolean
	local Pos = self:Pointer()
	local VF = self.VF
	local Rel = Pos - VF.AbsolutePosition
	if Rel.X < 0 or Rel.Y < 0 or Rel.X > VF.AbsoluteSize.X or Rel.Y > VF.AbsoluteSize.Y then return true end
	for _, F in self.UI:GetDescendants() do
		if F:IsA(`GuiObject`) and F.Visible and F ~= VF and not F:IsDescendantOf(VF) and F.Name ~= `Vignette`
			and F.BackgroundTransparency < 0.95 then
			local A, S = F.AbsolutePosition, F.AbsoluteSize
			if Pos.X >= A.X and Pos.Y >= A.Y and Pos.X <= A.X + S.X and Pos.Y <= A.Y + S.Y then return true end
		end
	end
	return false
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
	local R = self.World:Raycast(O, D * 60, Params)
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
			R = self.World:Raycast(O, D * 60, Params)
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
	Conn(RunService.RenderStepped, function(Dt) self:Step(Dt) end)
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
	new(`Part`, { Name = `Cut`; Anchored = true; CanCollide = false; CanQuery = false; Shape = Enum.PartType.Ball; Material = Enum.Material.Neon;
		Color = Color3.fromRGB(255, 92, 60); Size = Vector3.one * 0.05; CFrame = CFrame.new(P + Vector3.new(0, 0.04, 0)) }, self.Trail)
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
	-- a slip shakes the view
	if self.ShakeUntil and Now < self.ShakeUntil then
		local a = (self.ShakeUntil - Now) / 0.15
		self.Camera.CFrame = self.CamBase * CFrame.new((math.random() - 0.5) * 0.08 * a, (math.random() - 0.5) * 0.08 * a, 0)
	elseif self.ShakeUntil then
		self.ShakeUntil = nil
		self.Camera.CFrame = self.CamBase
	end
end

----------------------------------------------------------------------------------------------------- server replies
function Bench:OpenPlate()
	local Sp = self.Specimen
	local B = Sp.Bones.PlateHinge
	if not B or self.PlateOpen then return end
	self.PlateOpen = true
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
		self.ShakeUntil = os.clock() + 0.15
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
		if Api.Sound then Api.Sound(`Good`) end
	end
	if Reply.Placed then
		local Id = Reply.Placed
		self.Placed[Id] = true
		self.Holding = nil
		fadeBone(self.Specimen, Id, 1, 0.35)
		if Id == `FireGland` then fadeBone(self.Specimen, `FireGland`, 1, 0.35) end
		self:Clip(`Place`)
		if Api.Sound then Api.Sound(`Correct`, self:PlacedCount()) end
		local S = self.SlotButtons[self.PendingPlace or 0]
		if S and Api.Burst then Api.Burst(S.Button, true) end
		self:RefreshCard()
		if Reply.Done then self:Clip(`Done`) self:SetHint(`Specimen complete`) end
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
			if Done.Id == `Trace` then self:Clip(`Trace`) for _, P in self.Trail:GetChildren() do P.Color = Color3.fromRGB(70, 20, 16) end end
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
	if self.VF then self.VF:Destroy() end
	if self.UI then self.UI:Destroy() end
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

return Bench
