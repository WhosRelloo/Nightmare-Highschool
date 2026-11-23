--[[
	Race cosmetics (server). Dresses each character in its race's chosen looks (ReplicatedStorage.Lineage.Looks):
	  Vampire ears, Werewolf ears + tail (tinted by fur colour), Ghoul straps / shroud, Wraith cold breath + wisps (+ frost).

	Meshes: ServerStorage.NHRaceCosmetics.<Name>.<Name> (MeshPart, Blender-made, PBR SurfaceAppearance already set).
	Each MeshPart carries attributes NH_Part ("Head" | "Torso"), NH_Offset (Vector3, from that part's centre) and
	NH_Tint ("skin" | "fur" | nil). Tails carry a 7-bone chain (Tail1..Tail7) animated on clients by
	Controllers.Character.TailSway.

	Everything lands in a folder "NHRaceLooks" inside the character and is rebuilt when Race, RaceTier or RaceLooks
	(Player attributes mirrored by Lineage) change, or on respawn.
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerStorage = game:GetService(`ServerStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local Lineage = require(ReplicatedStorage:WaitForChild(`Lineage`))

-- nh_* sprites (tools/vfx): soft 4x4 smoke flipbook and 2x2 crystal shards
local SMOKE = `rbxassetid://98289186261003`
local SPARKLE = `rbxassetid://109847030941320`

local Local = {}
local Shared = {}
local Pending = {}   -- [Player] = true while a rebuild is queued

function Local.Store(): Folder?
	return ServerStorage:FindFirstChild(`NHRaceCosmetics`)
end

function Local.Night(): boolean
	local Ok, Clock = pcall(require, ServerScriptService.Services.School.SchoolClock)
	if not Ok then return true end
	local Ok2, State = pcall(Clock.GetState)
	local H = Ok2 and State and State.Hour
	return typeof(H) == `number` and (H >= 20 or H < 6)
end

function Local.Clear(Character: Model)
	local Old = Character:FindFirstChild(`NHRaceLooks`)
	if Old then Old:Destroy() end
end

-- clone one mesh piece onto the character, positioned from its stored offset and welded to its part
function Local.Wear(Folder: Folder, Character: Model, MeshName: string, Tint: Color3?)
	local Store = Local.Store()
	local Model = Store and Store:FindFirstChild(MeshName)
	local Source = Model and Model:FindFirstChild(MeshName)
	if not (Source and Source:IsA(`MeshPart`)) then
		warn(`[RaceCosmetics] missing mesh {MeshName} in ServerStorage.NHRaceCosmetics`)
		return nil
	end
	local Part = Character:FindFirstChild(Source:GetAttribute(`NH_Part`) or `Head`)
	if not (Part and Part:IsA(`BasePart`)) then return nil end
	local Piece = Source:Clone()
	Piece.Name = MeshName
	Piece.Anchored = false; Piece.CanCollide = false; Piece.CanQuery = false; Piece.CanTouch = false; Piece.Massless = true
	-- the pieces are modelled on a standard R6 body (torso 2 studs tall); this game's bodies can be scaled (0.9 now),
	-- so scale the mesh, its offset and any bones to the real body. NH_Squeeze (optional) presses ear pairs into the head.
	local Torso = Character:FindFirstChild(`Torso`)
	local S = if Torso then Torso.Size.Y / 2 else 1
	local Squeeze = Source:GetAttribute(`NH_Squeeze`) or Vector3.one
	Piece.Size = Source.Size * S * Squeeze
	for _, B in Piece:GetDescendants() do
		if B:IsA(`Bone`) then B.Position = B.Position * S end
	end
	Piece.CFrame = Part.CFrame * CFrame.new((Source:GetAttribute(`NH_Offset`) or Vector3.zero) * S)
	local SA = Piece:FindFirstChildWhichIsA(`SurfaceAppearance`)
	if SA and Tint then SA.Color = Tint end
	local Weld = Instance.new(`WeldConstraint`)
	Weld.Part0 = Part; Weld.Part1 = Piece; Weld.Parent = Piece
	Piece.Parent = Folder
	return Piece
end

-- Wraith: a soft cold breath from the mouth every few seconds, thin rising wisps from the hands and shoulders
function Local.Emitter(Parent: Instance, Props)
	local E = Instance.new(`ParticleEmitter`)
	for K, V in Props do E[K] = V end
	E.Parent = Parent
	return E
end

function Local.Attach(Part: BasePart, Name: string, Offset: Vector3)
	local A = Instance.new(`Attachment`)
	A.Name = Name; A.Position = Offset; A.Parent = Part
	return A
end

function Local.Wraith(Folder: Folder, Character: Model, Wisp, Frost: boolean)
	local Head, Torso = Character:FindFirstChild(`Head`), Character:FindFirstChild(`Torso`)
	local RArm, LArm = Character:FindFirstChild(`Right Arm`), Character:FindFirstChild(`Left Arm`)
	if not (Head and Torso) then return end
	local Color = Wisp and Wisp.Color or Color3.fromRGB(190, 222, 255)
	local Night = Local.Night()
	local Fade = if Night then 0 else 0.15   -- a little softer by day, but always readable
	local Made = {}
	-- breath: just in front of the mouth, drifting forward and up
	local Mouth = Local.Attach(Head, `NH_WraithBreath`, Vector3.new(0, -0.18, -0.62))
	local Breath = Local.Emitter(Mouth, {
		Name = `ColdBreath`; Texture = SMOKE; Color = ColorSequence.new(Color:Lerp(Color3.new(1, 1, 1), 0.6));
		Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.12), NumberSequenceKeypoint.new(1, 0.55) });
		Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.4 + Fade * 0.5), NumberSequenceKeypoint.new(0.4, 0.62 + Fade * 0.4), NumberSequenceKeypoint.new(1, 1) });
		Lifetime = NumberRange.new(1.1, 1.6); Speed = NumberRange.new(1.0, 1.6); SpreadAngle = Vector2.new(12, 12);
		EmissionDirection = Enum.NormalId.Front; Acceleration = Vector3.new(0, 0.6, 0); Drag = 1.5;
		Rate = 14; Enabled = false; LightEmission = 0.2; Rotation = NumberRange.new(0, 360); RotSpeed = NumberRange.new(-30, 30);
	})
	table.insert(Made, Mouth)
	-- wisps: thin, cold, rising
	local Spots = {
		{ RArm, Vector3.new(0, -0.95, 0) }, { LArm, Vector3.new(0, -0.95, 0) },
		{ Torso, Vector3.new(0.85, 0.95, 0) }, { Torso, Vector3.new(-0.85, 0.95, 0) },
	}
	for I, S in Spots do
		if S[1] then
			local A = Local.Attach(S[1], `NH_Wisp{I}`, S[2])
			Local.Emitter(A, {
				Name = `ColdWisp`; Texture = SMOKE; Color = ColorSequence.new(Color);
				Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.18), NumberSequenceKeypoint.new(0.5, 0.55), NumberSequenceKeypoint.new(1, 0.25) });
				Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.25, 0.42 + Fade), NumberSequenceKeypoint.new(1, 1) });
				Lifetime = NumberRange.new(1.2, 2.0); Speed = NumberRange.new(0.2, 0.5); SpreadAngle = Vector2.new(25, 25);
				EmissionDirection = Enum.NormalId.Top; Acceleration = Vector3.new(0, 0.8, 0); Drag = 1;
				Rate = 6; LightEmission = 0.6; FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4; FlipbookMode = Enum.ParticleFlipbookMode.OneShot; Rotation = NumberRange.new(0, 360); RotSpeed = NumberRange.new(-40, 40);
			})
			table.insert(Made, A)
		end
	end
	if Frost then
		for _, Arm in { RArm, LArm } do
			if Arm then
				local A = Local.Attach(Arm, `NH_Frost`, Vector3.new(0, -1.0, 0))
				Local.Emitter(A, {
					Name = `Frost`; Texture = SPARKLE; Color = ColorSequence.new(Color3.fromRGB(205, 235, 255));
					Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.07), NumberSequenceKeypoint.new(1, 0) });
					Transparency = NumberSequence.new(0.25 + Fade); Lifetime = NumberRange.new(0.5, 0.9); Speed = NumberRange.new(0.05, 0.2);
					SpreadAngle = Vector2.new(180, 180); Rate = 6; LightEmission = 0.8;
				})
				table.insert(Made, A)
			end
		end
	end
	-- breath comes in short puffs every 4-6 s (Enabled replicates; Emit() from the server would not)
	task.spawn(function()
		while Breath.Parent and Folder.Parent do
			task.wait(4 + math.random() * 2)
			if not Breath.Parent then break end
			Breath.Enabled = true
			task.wait(0.35)
			if Breath.Parent then Breath.Enabled = false end
		end
	end)
	-- the attachments live on the body parts; remember them so a rebuild removes them
	local Tag = Instance.new(`ObjectValue`)
	Tag.Name = `NH_WraithParts`
	Tag.Parent = Folder
	for _, A in Made do
		local V = Instance.new(`ObjectValue`); V.Name = `Part`; V.Value = A; V.Parent = Tag
	end
end

function Local.ClearWraith(Character: Model)
	for _, D in Character:GetDescendants() do
		if D:IsA(`Attachment`) and (D.Name == `NH_WraithBreath` or D.Name:sub(1, 7) == `NH_Wisp` or D.Name == `NH_Frost`) then D:Destroy() end
	end
end

function Shared.Apply(Player: Player)
	local Character = Player.Character
	if not (Character and Character:FindFirstChild(`Head`)) then return end
	Local.Clear(Character)
	Local.ClearWraith(Character)
	local L = {
		Race = Player:GetAttribute(`Race`); Tier = Player:GetAttribute(`RaceTier`) or 1; Looks = {};
	}
	for Pair in string.gmatch(Player:GetAttribute(`RaceLooks`) or ``, `[^,]+`) do
		local Slot, Id = Pair:match(`^(%w+)=(%w+)$`)
		if Slot then L.Looks[Slot] = Id end
	end
	if not Lineage.LookSlots[L.Race] then return end
	local Looks = Lineage.ResolveLooks(L)
	local Folder = Instance.new(`Folder`)
	Folder.Name = `NHRaceLooks`
	Folder.Parent = Character
	local Head = Character:FindFirstChild(`Head`)
	local Fur = Looks.Fur and Looks.Fur.Color
	for _, Slot in Lineage.LookSlots[L.Race] do
		local O = Looks[Slot]
		for _, MeshName in (O and O.Meshes) or {} do
			local Store = Local.Store()
			local Src = Store and Store:FindFirstChild(MeshName) and Store[MeshName]:FindFirstChild(MeshName)
			local TintKind = Src and Src:GetAttribute(`NH_Tint`)
			local Tint = if TintKind == `skin` then Head.Color elseif TintKind == `fur` then Fur else nil
			Local.Wear(Folder, Character, MeshName, Tint)
		end
	end
	if L.Race == `Wraith` then
		Local.Wraith(Folder, Character, Looks.Wisps, Looks.Frost and Looks.Frost.Id == `On`)
	end
	-- vampire ears follow the skin colour (the Appearance service may recolour the head after this)
	if L.Race == `Vampire` then
		local Conn
		Conn = Head:GetPropertyChangedSignal(`Color`):Connect(function()
			if not Folder.Parent then Conn:Disconnect() return end
			for _, P in Folder:GetChildren() do
				local SA = P:IsA(`MeshPart`) and P:FindFirstChildWhichIsA(`SurfaceAppearance`)
				if SA then SA.Color = Head.Color end
			end
		end)
	end
end

-- collapse bursts of attribute changes into one rebuild
function Shared.Queue(Player: Player)
	if Pending[Player] then return end
	Pending[Player] = true
	task.delay(0.2, function()
		Pending[Player] = nil
		if Player.Parent then pcall(Shared.Apply, Player) end
	end)
end

function Shared.OnStart()
	local function Watch(Player: Player)
		Player.CharacterAdded:Connect(function(Character)
			Character:WaitForChild(`Head`, 10)
			task.wait(1.0)   -- after the Appearance service has dressed the body
			Shared.Queue(Player)
		end)
		Player.AttributeChanged:Connect(function(Name)
			if Name == `Race` or Name == `RaceTier` or Name == `RaceLooks` then Shared.Queue(Player) end
		end)
		if Player.Character then Shared.Queue(Player) end
	end
	for _, P in Players:GetPlayers() do Watch(P) end
	Players.PlayerAdded:Connect(Watch)
	Players.PlayerRemoving:Connect(function(P) Pending[P] = nil end)
	-- wraith visibility follows day / night: rebuild wraiths when it turns (cheap: a handful of emitters)
	local WasNight = Local.Night()
	task.spawn(function()
		while true do
			task.wait(10)
			local N = Local.Night()
			if N ~= WasNight then
				WasNight = N
				for _, P in Players:GetPlayers() do
					if P:GetAttribute(`Race`) == `Wraith` then Shared.Queue(P) end
				end
			end
		end
	end)
end

return Shared
