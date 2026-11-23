--[[
	FormParts (client): while a character is transformed (character attribute Transformation, and not the full wolf),
	it wears its race form's wings and horns from ReplicatedStorage.Assets.Forms.
	Spec: docs/superpowers/specs/2026-11-22-race-transformations-design.md   Import notes: docs/Forms-Import.md

	- What to wear: Functions.Forms.Resolve(Player.Race, ParseLooks(Player.RaceLooks)), so every client resolves every
	  character on its own; nothing new on the server. Until Lineage carries the form slots, each race wears its first
	  direction's defaults.
	- Placement: the imported forms face +Z, so they turn 180 degrees. Wings: the model's RootPart (the build origin) goes
	  3 studs (times the height scale) below the Torso centre, welded to the Torso; the rig's own Motor6Ds carry the
	  membrane and frame. Horns: the FormAnchor attachment (the head centre) goes on the Head centre, every piece welded
	  to the Head. Scale = Torso height / 2 (and the Wing size Look).
	- Colour: each piece's SurfaceAppearance.Color from its FormTint attribute: WingPalette, WingFinish, HornFinish,
	  HornTip (None keeps the staged colour).
	- Only characters within RANGE studs of the camera get pieces (rebuilt when they come back).
	- While horns are worn, Hat accessories are hidden (restored when the form ends).
	- The Sovereign halo spins slowly (held still under Reduce Motion).
	- Wing motion (Task 3), by Functions.FormWings (the concepts' own skeleton, set on the bones each frame, no clips to
	  publish): Idle (a slow breathe, half folded) while standing or walking; Flap while sprinting (ground speed >= 20,
	  the CineBeat line: walk is 12-16, sprint 25 / 40.5) or in the air; a Fold kick on landing; a Flare when the form
	  starts. States cross-fade. Under Reduce Motion the wings hold the still idle pose (no flap, no flare).
	- Body pieces (batch 2): fur, bone, wraps, ice, chains, the capelet, fitted per body type. Assets.Forms.Bodies.<body>
	  holds one model per body (the 12 of UI.Appearance.Bodies; a character's body is read off its NHBodyMesh Torso
	  CharacterMesh, none = standard). Pieces are named <race letter><direction><piece> (V2Spines, W1Mantle, G2WrapL...),
	  each MeshPart carrying FormPart (the R6 part it welds to), FormOffset (its centre from that part's centre at height
	  1) and FormTint. Scaled per axis with the part (Size / its default 2x2x1 or 1x2x1). Head pieces (G1Jaw) are in Assets.Forms.NHFormHead. Fur takes the Werewolf Fur Look's colour.
	- The cape (NHCape) is hidden while the form is worn (wings sit where it hangs) and comes back after.
	- What hangs moves (Functions.FormDangles, rest shapes in Config.FormDangles, meshes in Assets.Forms.Dangles):
	  Wraith 2's chest and back chains and its wrist chain, Ghoul 2's linen tatters, as rigid links / strips on a small
	  rope simulation. Everything else stays welded.
	V1 has no body piece: its long ears are the Vampire Ears Look.
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)

local Cfg = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`Forms`))
local Forms = require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`Forms`))
local FormWings = require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`FormWings`))
local Lineage = require(ReplicatedStorage:WaitForChild(`Lineage`))
local FormDangles = require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`FormDangles`))
local DangleCfg = (function()
	local M = ReplicatedStorage:WaitForChild(`Config`):FindFirstChild(`FormDangles`)
	local Ok, C = pcall(function() return M and require(M) end)
	return if Ok then C else nil
end)()

local BodyByMesh: { [number]: string } = {} -- the Torso CharacterMesh id -> UI.Appearance body id
do
	local Ok, App = pcall(function() return require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Appearance`)) end)
	if Ok and App and App.Bodies then
		for _, B in App.Bodies do
			if B.TorsoMesh then BodyByMesh[B.TorsoMesh] = B.Id end
		end
	end
end

local RACE_LETTER = { Vampire = `V`; Werewolf = `W`; Ghoul = `G`; Wraith = `R` }
local FIXED_TINT = { Moss = Color3.fromRGB(74, 88, 52); Iron = Color3.fromRGB(58, 56, 60); Chain = Color3.fromRGB(150, 170, 192) }
local FUR_DEFAULT = Color3.fromRGB(110, 84, 62)

local Shared = {}

local RANGE = 150
local YAW = CFrame.Angles(0, math.pi, 0)
local WING_DROP = 3 -- studs from the Torso centre down to the build origin, at height scale 1
local HALO_SPEED = math.rad(18) -- per second
local SPRINTING = 20 -- ground speed (studs/s) at which the wings flap
local BLEND_RATE = 6 -- idle <-> flap cross-fade, per second
local LAND_FOLD = 0.4 -- seconds of the landing fold
local SLOW_RANGE = 60 -- beyond this the wings update every other frame

type Wing = { Rig: FormWings.Rig, Char: Model, Hum: Humanoid?, Root: BasePart?, Clock: number, Flap: number,
	Flare: number, Land: number, Air: boolean, Still: boolean, Odd: boolean }
type Worn = { Folder: Folder, Key: string, Halos: { Weld }, Hats: { [BasePart]: number }, Wings: { Wing },
	Dangles: FormDangles.Group? }
local Worn: { [Model]: Worn } = {}
local Watched: { [Model]: { RBXScriptConnection } } = {}
local Began: { [Model]: number } = {} -- when the form last started (seen here), so only a fresh start flares

local function justBegan(Char: Model): boolean
	local T = Began[Char]
	return T ~= nil and os.clock() - T < 1
end

local function assets(): Folder?
	local A = ReplicatedStorage:FindFirstChild(`Assets`)
	return A and A:FindFirstChild(`Forms`) :: Folder?
end

local function reduceMotion(): boolean -- the same read as Controllers.Gui.Fortune
	local Ok, S = pcall(function() return require(ReplicatedStorage.UI.Settings) end)
	local V = Ok and S and S.Get and S.Get(`ReduceMotion`)
	return V == true
end

local function bodyOf(Char: Model): string
	for _, C in Char:GetChildren() do
		if C:IsA(`CharacterMesh`) and C.Name == `NHBodyMesh` and C.BodyPart == Enum.BodyPart.Torso then
			return BodyByMesh[C.MeshId] or `standard`
		end
	end
	return `standard`
end

local function furOf(P: Player, Race: string): Color3?
	if Race ~= `Werewolf` then return nil end
	local Ok, Looks = pcall(function()
		local L = { Race = Race; Tier = P:GetAttribute(`RaceTier`) or 1; Looks = {} }
		for Pair in string.gmatch(P:GetAttribute(`RaceLooks`) or ``, `[^,]+`) do
			local Slot, Id = Pair:match(`^(%w+)=(%w+)$`)
			if Slot then L.Looks[Slot] = Id end
		end
		return Lineage.ResolveLooks(L)
	end)
	return (Ok and Looks and Looks.Fur and Looks.Fur.Color) or FUR_DEFAULT
end

local function wanted(Char: Model): any
	if not Char:GetAttribute(`Transformation`) or Char:GetAttribute(`WolfForm`) then return nil end
	local P = Players:GetPlayerFromCharacter(Char)
	local Race = P and P:GetAttribute(`Race`)
	if type(Race) ~= `string` then return nil end
	local F = Forms.Resolve(Race, Forms.ParseLooks(P:GetAttribute(`RaceLooks`)))
	if not F then return nil end
	F.Body = bodyOf(Char)
	F.Fur = furOf(P, Race)
	return F
end

local function keyOf(F): string
	local W, H = F.Wings, F.Horns
	return table.concat({
		F.Race, F.Direction, F.Body, F.Fur and F.Fur:ToHex() or `-`,
		W and (W.Style .. W.Palette .. W.Finish .. W.Size) or `-`,
		H and (H.Style .. H.Finish .. H.Tip) or `-`,
	}, `|`)
end

local function tint(Model: Model, F)
	for _, D in Model:GetDescendants() do
		if not D:IsA(`MeshPart`) then continue end
		local SA = D:FindFirstChildWhichIsA(`SurfaceAppearance`)
		local Kind = D:GetAttribute(`FormTint`)
		if not SA or not Kind then continue end
		local E
		if Kind == `WingPalette` and F.Wings then E = Cfg.Palettes[F.Wings.Palette]
		elseif Kind == `WingFinish` and F.Wings then E = Cfg.Finishes[F.Wings.Finish]
		elseif Kind == `HornFinish` and F.Horns then E = Cfg.Finishes[F.Horns.Finish]
		elseif Kind == `HornTip` and F.Horns then E = Cfg.Finishes[F.Horns.Tip]
		elseif Kind == `HornFinish` then E = Cfg.Finishes[Cfg.HornDefaults.Finish] -- body pieces with the horns off
		elseif Kind == `WingFinish` then E = nil
		elseif Kind == `Fur` then E = { Color = F.Fur or FUR_DEFAULT }
		elseif FIXED_TINT[Kind] then E = { Color = FIXED_TINT[Kind] } end
		if E then SA.Color = E.Color end
	end
end

local function loose(Model: Model)
	for _, D in Model:GetDescendants() do
		if D:IsA(`BasePart`) then
			D.Anchored = false
			D.CanCollide = false
			D.CanQuery = false
			D.CanTouch = false
			D.Massless = true
			D.CastShadow = true
		end
	end
end

local function weld(A: BasePart, B: BasePart): WeldConstraint
	local W = Instance.new(`WeldConstraint`)
	W.Part0 = A
	W.Part1 = B
	W.Parent = B
	return W
end

-- the cape folds away while the form is worn (Appearance may put a new one on mid-form: hidden on sight too)
local function hideCape(Char: Model, R: Worn)
	local Cape = Char:FindFirstChild(`NHCape`)
	if not Cape then return end
	for _, D in Cape:GetDescendants() do
		if D:IsA(`BasePart`) and D.Transparency < 1 and R.Hats[D] == nil then
			R.Hats[D] = D.Transparency
			D.Transparency = 1
		end
	end
end

local function remove(Char: Model)
	local R = Worn[Char]
	if not R then return end
	Worn[Char] = nil
	for Handle, T in R.Hats do
		if Handle.Parent then Handle.Transparency = T end
	end
	R.Folder:Destroy()
end

local function build(Char: Model, F)
	local Lib = assets()
	local Torso = Char:FindFirstChild(`Torso`) :: BasePart?
	local Head = Char:FindFirstChild(`Head`) :: BasePart?
	if not Lib or not Torso or not Head then return end
	local S = Torso.Size.Y / 2
	local Folder = Instance.new(`Folder`)
	Folder.Name = `NHFormParts`
	local R: Worn = { Folder = Folder, Key = keyOf(F), Halos = {}, Hats = {}, Wings = {} }
	local Hum = Char:FindFirstChildOfClass(`Humanoid`)
	local HRP = Char:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	local Phase = math.random() * 10 -- characters don't breathe in step

	if F.Wings then
		for _, Side in { `L`, `R` } do
			local Src = Lib:FindFirstChild(`NHWing_{F.Wings.Style}_{Side}`) :: Model?
			local Root = Src and Src:FindFirstChild(`RootPart`)
			if not Src or not Root then continue end
			local M = Src:Clone()
			loose(M)
			local K = S * (F.Wings.Scale or 1)
			if math.abs(K - 1) > 1e-3 then M:ScaleTo(K) end
			local Rt = M:FindFirstChild(`RootPart`) :: BasePart
			local Target = Torso.CFrame * CFrame.new(0, -WING_DROP * K, 0) * YAW
			M:PivotTo(Target * Rt.CFrame:Inverse() * M:GetPivot())
			tint(M, F)
			M.Parent = Folder
			weld(Torso, Rt)
			local Rig = FormWings.Rig(M)
			if Rig then
				table.insert(R.Wings, { Rig = Rig, Char = Char, Hum = Hum, Root = HRP, Clock = Phase, Flap = 0,
					Flare = if justBegan(Char) and not reduceMotion() then 0 else 1, Land = 1, Air = false,
					Still = false, Odd = false })
			end
		end
	end

	if F.Horns then
		local Src = Lib:FindFirstChild(`NHHorns_{F.Horns.Style}`) :: Model?
		if Src then
			local M = Src:Clone()
			loose(M)
			if math.abs(S - 1) > 1e-3 then M:ScaleTo(S) end
			local Anchor = M:FindFirstChild(`FormAnchor`, true) :: Attachment?
			if Anchor then
				local Target = Head.CFrame * YAW
				M:PivotTo(Target * Anchor.WorldCFrame:Inverse() * M:GetPivot())
			end
			tint(M, F)
			M.Parent = Folder
			for _, P in M:GetDescendants() do
				if not P:IsA(`BasePart`) then continue end
				if P.Name:match(`Halo$`) then
					local W = Instance.new(`Weld`)
					W.Part0 = Head
					W.Part1 = P
					W.C0 = Head.CFrame:Inverse() * P.CFrame
					W.Parent = P
					table.insert(R.Halos, W)
				else
					weld(Head, P)
				end
			end
			-- horns clear hats: hide Hat accessories while the form is worn
			for _, Acc in Char:GetChildren() do
				if Acc:IsA(`Accessory`) and Acc.AccessoryType == Enum.AccessoryType.Hat then
					local H = Acc:FindFirstChild(`Handle`) :: BasePart?
					if H and H.Transparency < 1 then
						R.Hats[H] = H.Transparency
						H.Transparency = 1
					end
				end
			end
		end
	end

	-- body pieces: this body's model, the race letter + direction's pieces, each on its own R6 part
	local Prefix = (RACE_LETTER[F.Race] or `?`) .. tostring(F.Direction)
	local Bodies = Lib:FindFirstChild(`Bodies`)
	local Sets = { Bodies and (Bodies:FindFirstChild(F.Body) or Bodies:FindFirstChild(`standard`)), Lib:FindFirstChild(`NHFormHead`) }
	local Pieces = Instance.new(`Model`)
	Pieces.Name = `NHFormBody`
	for _, Set in Sets do
		if not Set then continue end
		for _, Src in Set:GetChildren() do
			if not Src:IsA(`MeshPart`) or Src.Name:sub(1, #Prefix) ~= Prefix then continue end
			local Part = Char:FindFirstChild(Src:GetAttribute(`FormPart`) or ``) :: BasePart?
			local Off = Src:GetAttribute(`FormOffset`)
			if not Part or typeof(Off) ~= `Vector3` then continue end
			-- per axis: body scales stretch parts unevenly (an arm 0.91 wide and 1.59 tall), and a piece fitted to the
			-- surface must stretch with it or sink in
			local K = if Part.Name == `Head` then Vector3.one * S else Part.Size / FormDangles.Base(Part)
			local M = Src:Clone()
			M.Size = Src.Size * K
			M.CFrame = Part.CFrame * CFrame.new(Off * K) * YAW
			M.Anchored, M.CanCollide, M.CanQuery, M.CanTouch, M.Massless = false, false, false, false, true
			M.Parent = Pieces
			weld(Part, M)
		end
	end
	if #Pieces:GetChildren() > 0 then
		tint(Pieces, F)
		Pieces.Parent = Folder
	else
		Pieces:Destroy()
	end

	-- what hangs: chains and tatters on their ropes
	local DB = DangleCfg and DangleCfg.Bodies
	local DD = DB and (DB[F.Body] or DB.standard)
	local G = FormDangles.Build(Char, DD and DD[Prefix], DD and DD.LegOuter, Lib:FindFirstChild(`Dangles`), Folder)
	if G then
		tint(G.Model, F)
		R.Dangles = G
	end

	Folder.Parent = Char
	Worn[Char] = R
	hideCape(Char, R)
end

local function airborne(W: Wing): boolean
	local H = W.Hum
	if not H then return false end
	local S = H:GetState()
	return S == Enum.HumanoidStateType.Freefall or S == Enum.HumanoidStateType.Jumping
		or S == Enum.HumanoidStateType.Flying
end

-- one wing, one frame: locomotion picks idle or flap (cross-faded), then the landing fold and the start flare on top
local function animate(W: Wing, Dt: number, Still: boolean, CamPos: Vector3)
	if Still then
		if not W.Still then
			W.Still = true
			FormWings.Pose(W.Rig, FormWings.Idle(0))
		end
		return
	end
	W.Still = false
	local Root = W.Root
	if Root and (Root.Position - CamPos).Magnitude > SLOW_RANGE then
		W.Odd = not W.Odd
		if W.Odd then W.Clock += Dt return end
		Dt *= 2
	end
	W.Clock += Dt
	local V = if Root then Root.AssemblyLinearVelocity else Vector3.zero
	local Air = airborne(W) or math.abs(V.Y) > 14 -- the velocity covers other players, whose state may lag
	if W.Air and not Air then W.Land = 0 end
	W.Air = Air
	local Fast = Air or Vector3.new(V.X, 0, V.Z).Magnitude >= SPRINTING
	W.Flap = math.clamp(W.Flap + (if Fast then Dt else -Dt) * BLEND_RATE, 0, 1)
	local A = W.Flap * W.Flap * (3 - 2 * W.Flap)
	local f1, p1, l1 = FormWings.Idle(W.Clock)
	local f2, p2, l2 = FormWings.Flap(W.Clock)
	local fold, flap, lag = f1 + (f2 - f1) * A, p1 + (p2 - p1) * A, l1 + (l2 - l1) * A
	if W.Land < 1 then -- landing: the wings snap tighter and settle back
		W.Land = math.min(W.Land + Dt / LAND_FOLD, 1)
		local K = math.sin(math.pi * W.Land) * (1 - W.Land * 0.5)
		fold = math.min(fold + 0.3 * K, 1)
		flap -= 8 * K
		lag += 10 * K
	end
	if W.Flare < 1 then -- the form starting: folded wings throw open, then hand over to the locomotion pose
		W.Flare = math.min(W.Flare + Dt / FormWings.FLARE_TIME, 1)
		local ff, fp, fl = FormWings.Flare(W.Flare)
		local B = W.Flare * W.Flare
		fold, flap, lag = ff + (fold - ff) * B, fp + (flap - fp) * B, fl + (lag - fl) * B
	end
	FormWings.Pose(W.Rig, fold, flap, lag)
end

local function inRange(Char: Model): boolean
	local Cam = workspace.CurrentCamera
	local Root = Char:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	if not Cam or not Root then return false end
	return (Cam.CFrame.Position - Root.Position).Magnitude <= RANGE
end

local function refresh(Char: Model)
	if not Char.Parent then remove(Char) return end
	local F = inRange(Char) and wanted(Char) or nil
	local Cur = Worn[Char]
	if not F then
		if Cur then remove(Char) end
		return
	end
	if Cur and Cur.Key == keyOf(F) and Cur.Folder.Parent == Char then
		hideCape(Char, Cur)
		return
	end
	if Cur then remove(Char) end
	local Ok, Err = pcall(build, Char, F)
	if not Ok then warn(`[FormParts] {Char.Name}: {Err}`) end
end

local function watch(Char: Model, P: Player)
	if Watched[Char] then return end
	local function go() task.defer(refresh, Char) end
	Watched[Char] = {
		Char:GetAttributeChangedSignal(`Transformation`):Connect(function()
			if Char:GetAttribute(`Transformation`) then Began[Char] = os.clock() end
			go()
		end),
		Char:GetAttributeChangedSignal(`WolfForm`):Connect(go),
		P:GetAttributeChangedSignal(`Race`):Connect(go),
		P:GetAttributeChangedSignal(`RaceLooks`):Connect(go),
		Char.AncestryChanged:Connect(function()
			if Char.Parent then return end
			remove(Char)
			for _, C in Watched[Char] or {} do C:Disconnect() end
			Watched[Char] = nil
			Began[Char] = nil
		end),
	}
	go()
end

local function onPlayer(P: Player)
	P.CharacterAdded:Connect(function(Char) watch(Char, P) end)
	if P.Character then watch(P.Character, P) end
end

-- Bloodline's preview: dress any (anchored, posed) copy of a character in a race's form, whatever its Transformation.
-- Looks = { [slot] = option id }; Fur = the Fur Look's colour. The wings breathe with the idle (held under Reduce
-- Motion); the copy forgets its pieces once it leaves the DataModel.
function Shared.Preview(Model: Model, Race: string, Looks: { [string]: string }, Fur: Color3?): boolean
	local F = Forms.Resolve(Race, Looks)
	if not F then return false end
	F.Body = bodyOf(Model)
	F.Fur = if Race == `Werewolf` then (Fur or FUR_DEFAULT) else nil
	local Old = Model:FindFirstChild(`NHFormParts`)
	if Old then Old:Destroy() end
	local Ok, Err = pcall(build, Model, F)
	if not Ok then warn(`[FormParts] preview: {Err}`) return false end
	local R = Worn[Model]
	if R then
		for _, W in R.Wings do W.Flare = 1 end
	end
	local Conn
	Conn = Model.AncestryChanged:Connect(function()
		if Model:IsDescendantOf(game) then return end
		Worn[Model] = nil
		Conn:Disconnect()
	end)
	return true
end

function Shared.OnStart()
	Players.PlayerAdded:Connect(onPlayer)
	for _, P in Players:GetPlayers() do onPlayer(P) end
	-- range: characters walking in and out of RANGE
	task.spawn(function()
		while true do
			task.wait(0.5)
			for Char in Watched do refresh(Char) end
		end
	end)
	-- the Sovereign halo
	local Angle = 0
	RunService.RenderStepped:Connect(function(Dt)
		local Still = reduceMotion()
		local Cam = workspace.CurrentCamera
		local CamPos = if Cam then Cam.CFrame.Position else Vector3.zero
		if not Still then Angle = (Angle + HALO_SPEED * Dt) % (2 * math.pi) end
		for _, R in Worn do
			if not Still then
				for _, W in R.Halos do W.C1 = CFrame.Angles(0, 0, Angle) end
			end
			for _, W in R.Wings do
				local Ok, Err = pcall(animate, W, Dt, Still, CamPos)
				if not Ok then
					warn(`[FormParts] wings {W.Char.Name}: {Err}`)
					table.clear(R.Wings)
					break
				end
			end
			if R.Dangles then
				local Ok, Err = pcall(FormDangles.Step, R.Dangles, Dt, Still, CamPos, SLOW_RANGE)
				if not Ok then
					warn(`[FormParts] dangles: {Err}`)
					R.Dangles = nil
				end
			end
		end
	end)
end

return Shared
