--[[
	UI.AccessoryWear: puts the 3D accessory kits (Config.Accessories) on a character. Called by UI.Appearance.ApplyTo,
	which builds every look at the base, unstretched body (Config.Heights.Base) and then scales it back, so each
	piece is placed in studs for that body. Height v2's stretch (Heights.SetStretch) moves every Weld on the torso,
	arms and legs, so the pieces here are held by Welds (JointInstances), not WeldConstraints.

	Templates (ReplicatedStorage.NHAccessories.<Model>.<Piece>): a MeshPart (rigged pieces carry their Bones) with
	  NHMount     the R6 part it rides: Torso | Head | RightArm | LeftArm | RightLeg | LeftLeg
	  NHFit       CFrame of the piece on that part, built for the nominal R6 part (Torso 2 x 2 x 1, Head 2 x 1 x 1,
	              limbs 1 x 2 x 1); scaled here by the part's real height (the player's 0.9 body: x 0.9)
	  NHFitBody   "female=1.06;curvy=1.21;..." how much deeper the piece sits on each body type (UI.Appearance.Bodies
	              ids), measured against that body's mesh by the Blender builder: Size.Z, NHFit.Z and the bones' Z
	              are scaled about the part's centre plane, so chest and back pieces sit on busts, bellies and lean
	              bodies without sinking in or floating
	  NHSway      a profile for Controllers.Character.AccessorySway (Flutter | Pendulum | Tails | Loops | ...)
	  NHHairFit   "<RigSource>=k,dz;...;*=k,dz" per rigged hair (ReplicatedStorage.NHHairCatalog's RigSource),
	              measured by art/characters/accessories/acc_hairfit.py so no strand passes through it. Head pieces:
	              k = uniform scale about the headband centre (NHSeat, studs above the head centre on the nominal
	              head), dz = lift; other pieces are 1,0 or x. "x" = that hair can't wear it. "*" = any other hair.
	Worn as Model "NHAcc_<Slot>" (attribute NHAcc = item id) under the character. Admin items are skipped on a player
	who isn't staff (previews and dummies with no player still show them).
	Regalia colour (Kit B): while the character wears any Admin item, it carries NHRegaliaTint (Color3) and NHRegalia
	(the item id that decided it): the tint of the most visible regalia worn (REGALIA_ORDER), so the staff teleport's
	flock (Controllers.World.TpFlock) can take the same ember or crimson. Cleared when no regalia is worn.
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local Cfg = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`Accessories`))

local Wear = {}
local PART = { Torso = `Torso`; Head = `Head`; RightArm = `Right Arm`; LeftArm = `Left Arm`; RightLeg = `Right Leg`; LeftLeg = `Left Leg` }
local NOMINAL_Y = { Torso = 2; Head = 1; RightArm = 2; LeftArm = 2; RightLeg = 2; LeftLeg = 2 }
-- Kit B's two glows (the layouts' emissive tints): the crows' ember eyes and keys, the crimson sigil, crown and staff
local REGALIA_TINT = { Ember = Color3.new(1, 0.34, 0.07); Crimson = Color3.new(0.92, 0.06, 0.12) }
local REGALIA_ORDER = { `Halo`, `Shoulders`, `Hat`, `Coat`, `Hand`, `Collar`, `Trail`, `Familiar`, `Face`, `Ring` }

-- the wearer's hair key for NHHairFit: the catalog hair's RigSource, "Built" for the built hairstyles, "*" otherwise
function Wear.HairKey(HairId: number?): string
	if not HairId or HairId <= 0 then return `Built` end
	local Cat = ReplicatedStorage:FindFirstChild(`NHHairCatalog`)
	local H = Cat and Cat:FindFirstChild(`Hair_{HairId}`)
	local R = H and H:GetAttribute(`RigSource`)
	return if typeof(R) == `string` then R else `*`
end

-- a head piece's fit for a hair: k, dz (nil = this hair can't wear it)
function Wear.HairFit(P: Instance, Key: string): (number?, number?)
	local S = P:GetAttribute(`NHHairFit`)
	if typeof(S) ~= `string` then return 1, 0 end
	local Def = nil
	for K, V in S:gmatch(`([^=;]+)=([^;]+)`) do
		if K == Key or (K == `*` and Def == nil) then
			if V == `x` then
				if K == Key then return nil, nil end
			else
				local A, B = V:match(`([%d%.]+),([%d%.%-]+)`)
				if K == Key then return tonumber(A) or 1, tonumber(B) or 0 end
				Def = { tonumber(A) or 1, tonumber(B) or 0 }
			end
		end
	end
	if Def then return Def[1], Def[2] end
	return 1, 0
end

-- can this hair wear the item (every head piece has a fit for it)?
function Wear.FitsHair(It, HairId: number?): boolean
	local Key = Wear.HairKey(HairId)
	for _, P in Wear.Pieces(It) do
		if Wear.HairFit(P, Key) == nil then return false end
	end
	return true
end

local function depthFor(P: Instance, BodyId: string?): number
	local S = P:GetAttribute(`NHFitBody`)
	if typeof(S) ~= `string` or not BodyId or BodyId == `standard` then return 1 end
	for K, V in S:gmatch(`([%w_]+)=([%d%.]+)`) do
		if K == BodyId then return math.clamp(tonumber(V) or 1, 0.75, 1.5) end
	end
	return 1
end

function Wear.Clear(Character: Model)
	for _, C in Character:GetChildren() do
		if C:IsA(`Model`) and C:GetAttribute(`NHAcc`) ~= nil then C:Destroy() end
	end
	Character:SetAttribute(`NHRegalia`, nil)
	Character:SetAttribute(`NHRegaliaTint`, nil)
end

-- the pieces an item wears (one named piece, or every MeshPart of its model)
function Wear.Pieces(It)
	local Store = ReplicatedStorage:FindFirstChild(`NHAccessories`)
	local M = It and Store and Store:FindFirstChild(It.Model)
	if not M then return {} end
	local Names = It.Pieces or (It.Piece and { It.Piece })
	local Out = {}
	if Names then
		for _, N in Names do
			local P = M:FindFirstChild(N)
			if P and P:IsA(`BasePart`) then table.insert(Out, P) end
		end
	else
		for _, P in M:GetChildren() do
			if P:IsA(`BasePart`) then table.insert(Out, P) end
		end
	end
	return Out
end

local function wearPiece(Character: Model, Holder: Model, Tpl: BasePart, BodyId: string?, HairKey: string)
	local MountKey = Tpl:GetAttribute(`NHMount`) or `Torso`
	local Mount = Character:FindFirstChild(PART[MountKey] or `Torso`)
	if not (Mount and Mount:IsA(`BasePart`)) then return end
	local K = Mount.Size.Y / (NOMINAL_Y[MountKey] or 2)
	local D = if MountKey == `Head` then 1 else depthFor(Tpl, BodyId)
	local Fit = Tpl:GetAttribute(`NHFit`)
	if typeof(Fit) ~= `CFrame` then Fit = CFrame.new() end
	local HK, HZ = Wear.HairFit(Tpl, HairKey) -- every piece: nil = this hair passes through it (not worn)
	if not HK then return end
	if MountKey ~= `Head` then HK, HZ = 1, 0 end
	local Seat = tonumber(Tpl:GetAttribute(`NHSeat`)) or 0.43
	local Pos = Vector3.new(Fit.X, Fit.Y, Fit.Z)
	if MountKey == `Head` and (HK ~= 1 or HZ ~= 0) then -- the hair fit: scale about the headband centre, then lift
		local Piv = Vector3.new(0, Seat, 0)
		Pos = Piv + (Pos - Piv) * HK + Vector3.new(0, HZ, 0)
	end
	local Off = CFrame.new(Pos.X * K, Pos.Y * K, Pos.Z * K * D) * Fit.Rotation
	local P = Tpl:Clone()
	K *= HK
	P.Size = Vector3.new(P.Size.X * K, P.Size.Y * K, P.Size.Z * K * D)
	-- bones: scale each one's position in the PIECE's frame (a child bone's CFrame is relative to its parent, which may
	-- be turned), then rebuild the local CFrames so the chain keeps its directions
	local Scale = function(V: Vector3) return Vector3.new(V.X * K, V.Y * K, V.Z * K * D) end
	local function rescale(Parent: Instance, OldParentCF: CFrame, NewParentCF: CFrame)
		for _, B in Parent:GetChildren() do
			if B:IsA(`Bone`) then
				local Old = OldParentCF * B.CFrame
				local New = CFrame.new(Scale(Old.Position)) * Old.Rotation
				B.CFrame = NewParentCF:Inverse() * New
				rescale(B, Old, New)
			end
		end
	end
	rescale(P, CFrame.identity, CFrame.identity)
	for _, B in P:GetDescendants() do
		if B:IsA(`Attachment`) and not B:IsA(`Bone`) then
			B.Position = Scale(B.Position)
		elseif B:IsA(`PointLight`) or B:IsA(`SpotLight`) then
			B.Range *= K
		end
	end
	P.Anchored, P.CanCollide, P.CanQuery, P.CanTouch, P.Massless = false, false, false, false, true
	P.CFrame = Mount.CFrame * Off
	local W = Instance.new(`Weld`)
	W.Name = `NHAccWeld`
	W.Part0, W.Part1 = Mount, P
	W.C0 = Off
	W.Parent = P
	P.Parent = Holder
end

-- Acc = the look's worn list (Config.Accessories.Parse). BodyId = UI.Appearance.Bodies[look.Body].Id. HairId = the
-- look's catalog hair (0 = a built hairstyle)
function Wear.Wear(Character: Model, Acc: string?, BodyId: string?, HairId: number?)
	local HairKey = Wear.HairKey(HairId)
	Wear.Clear(Character)
	local Owner = Players:GetPlayerFromCharacter(Character)
	local Staff = Owner ~= nil and (tonumber(Owner:GetAttribute(`NHStaff`)) or 0) >= 1
	for Slot, Id in Cfg.Parse(Acc) do
		local It = Cfg.ById[Id]
		if not It or (It.Admin and Owner and not Staff) then continue end
		local Pieces = Wear.Pieces(It)
		if #Pieces == 0 then continue end
		local Holder = Instance.new(`Model`)
		Holder.Name = `NHAcc_{Slot}`
		Holder:SetAttribute(`NHAcc`, Id)
		for _, Tpl in Pieces do
			local ok, err = pcall(wearPiece, Character, Holder, Tpl, BodyId, HairKey)
			if not ok then warn(`[AccessoryWear] {Id}: {err}`) end
		end
		if #Holder:GetChildren() == 0 then -- nothing fitted (this hair passes through it): wear nothing for the slot
			Holder:Destroy()
			continue
		end
		Holder.Parent = Character
	end
	local TintId = nil
	for _, Slot in REGALIA_ORDER do
		local H = Character:FindFirstChild(`NHAcc_{Slot}`)
		local It = H and Cfg.ById[H:GetAttribute(`NHAcc`)]
		if It and It.Admin and REGALIA_TINT[It.Tint] then TintId = It.Id break end
	end
	Character:SetAttribute(`NHRegalia`, TintId)
	Character:SetAttribute(`NHRegaliaTint`, if TintId then REGALIA_TINT[Cfg.ById[TintId].Tint] else nil)
end

return Wear
