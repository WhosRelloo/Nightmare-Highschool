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
	              head), dz = lift; other pieces are 1,0 or x. "x" = no measured fit for that hair: the piece is
	              still worn, at the "*" fit, and the hair isn't tucked round it (it may pass through). "*" = any other hair.
	  NHHairScale "Radial" on the face masks (1.99.0): a hair fit k scales the mask out round the head's vertical axis
	              (across and front-to-back, not up or down), the way acc_hairfit.py measures masks, so the eye holes
	              stay on the painted eyes whatever hair is worn. Scaled about the headband (NHSeat), a mask at k 1.11
	              (the "*" fit) slid 0.06 studs down the face.
	Worn as Model "NHAcc_<Slot>" (attribute NHAcc = item id) under the character. Admin items are skipped on a player
	who isn't staff (previews and dummies with no player still show them).
	Hair tuck: an item's pieces may carry NHHairTuck, "<RigSource>=Bone:x,y,z|Bone:x,y,z;...": for each rigged hair
	the piece would otherwise pass through, the turn of each lock bone (a rotation vector, radians, in the hair Handle's
	own frame, about the bone's head in its rest frame) that lays the hair over, under or round the piece, solved and
	checked offline (art/characters/accessories/acc_hairtuck.py). Wear merges the tucks of everything worn (per bone, the
	larger turn) into the character's NHHairTuck ("Bone:x,y,z|..."), poses the hair's bones with it (previews), and
	Controllers.Character.HairSway eases it in under the hair's sway. The turns were solved for the v2 hair rigs (the locks
	carry their strands; tools/hair-rig/nh_hair_autorig.py), marked NHHairRig = 2 on the hair's Handle: on an older rig
	nothing is turned, and a piece that needs a turn for that hair is still worn, untucked (1.88).
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

-- a head piece's fit for a hair: k, dz (nil = no measured fit for it: Wear.DefaultFit)
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

-- a head piece's fit for a hair it has no fit for: the "*" fit (1, 0 without one)
function Wear.DefaultFit(P: Instance): (number, number)
	local K, Z = Wear.HairFit(P, `*`)
	return K or 1, Z or 0
end

-- does this hair get the item's full look (every piece has a measured fit for it, and any tuck it needs can be
-- taken)? A hair that doesn't still wears it, untucked (1.88)
function Wear.FitsHair(It, HairId: number?): boolean
	local Key = Wear.HairKey(HairId)
	local V2 = nil -- is the catalog hair a v2 rig (only looked up when a piece needs a tuck for it)?
	for _, P in Wear.Pieces(It) do
		if Wear.HairFit(P, Key) == nil then return false end
		if Wear.ParseTuck(P:GetAttribute(`NHHairTuck`), Key) then
			if V2 == nil then
				local Cat = ReplicatedStorage:FindFirstChild(`NHHairCatalog`)
				local H = Cat and HairId and Cat:FindFirstChild(`Hair_{HairId}`)
				V2 = Wear.Tuckable(H and H:FindFirstChild(`Handle`))
			end
			if not V2 then return false end
		end
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
	Character:SetAttribute(`NHHairTuck`, nil)
	local Handle = Wear.HairHandle(Character)
	if Handle then
		for _, B in Handle:GetDescendants() do
			if B:IsA(`Bone`) then B.Transform = CFrame.identity end
		end
	end
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

-- the hair tuck: one hair's entry ("Bone:x,y,z|...", or "<RigSource>=..." entries separated by ";") -> { bone = turn }
function Wear.ParseTuck(S: any, Key: string?): { [string]: Vector3 }?
	if typeof(S) ~= `string` or S == `` then return nil end
	local Body = S
	if Key then
		Body = nil
		for Entry in S:gmatch(`[^;]+`) do
			local K, B = Entry:match(`^([^=]+)=(.*)$`)
			if K == Key then Body = B break end
		end
		if not Body then return nil end
	end
	local Out = {}
	for Name, X, Y, Z in Body:gmatch(`([%w_]+):([%-%d%.e]+),([%-%d%.e]+),([%-%d%.e]+)`) do
		Out[Name] = Vector3.new(tonumber(X) or 0, tonumber(Y) or 0, tonumber(Z) or 0)
	end
	return Out
end

function Wear.JoinTuck(T: { [string]: Vector3 }): string
	local Parts = {}
	for N, V in T do table.insert(Parts, string.format(`%s:%.4f,%.4f,%.4f`, N, V.X, V.Y, V.Z)) end
	table.sort(Parts)
	return table.concat(Parts, `|`)
end

-- a hair bone's rest frame in its Handle's space, and a tuck turn (Handle frame) as the bone's own Transform
function Wear.RestInHandle(B: Bone): CFrame
	local CF = B.CFrame
	local P = B.Parent
	while P and P:IsA(`Bone`) do
		CF = P.CFrame * CF
		P = P.Parent
	end
	return CF
end

function Wear.TuckCFrame(B: Bone, V: Vector3): CFrame
	local A = V.Magnitude
	if A < 1e-5 then return CFrame.identity end
	return CFrame.fromAxisAngle(Wear.RestInHandle(B).Rotation:VectorToObjectSpace(V / A), A)
end

-- the character's rigged hair Handle (the catalog hair accessory), if any
function Wear.HairHandle(Character: Model): BasePart?
	for _, C in Character:GetChildren() do
		if C:IsA(`Accessory`) or C.Name == `NHHair` then
			local H = C:FindFirstChild(`Handle`)
			if H and H:IsA(`BasePart`) and H:FindFirstChildWhichIsA(`Bone`) then return H end
		end
	end
	return nil
end

-- can this hair take a tuck (a v2 rig)?
function Wear.Tuckable(Handle: Instance?): boolean
	return Handle ~= nil and Handle:GetAttribute(`NHHairRig`) == 2
end

-- the look's hair: the catalog's (UI.Appearance.ApplyTo wears the accessories before it puts the new hair on, so
-- the catalog says which rig it will be), else the hair the character has on
function Wear.TuckableHair(Character: Model, HairId: number?): boolean
	if HairId and HairId > 0 then
		local Cat = ReplicatedStorage:FindFirstChild(`NHHairCatalog`)
		local H = Cat and Cat:FindFirstChild(`Hair_{HairId}`)
		return Wear.Tuckable(H and H:FindFirstChild(`Handle`))
	end
	return Wear.Tuckable(Wear.HairHandle(Character))
end

local function poseHair(Character: Model, Merged: { [string]: Vector3 })
	local Handle = Wear.HairHandle(Character)
	if not Handle then return end
	for _, B in Handle:GetDescendants() do
		if B:IsA(`Bone`) then B.Transform = if Merged[B.Name] then Wear.TuckCFrame(B, Merged[B.Name]) else CFrame.identity end
	end
end

local function applyTuck(Character: Model, HairKey: string, TuckOK: boolean)
	local Merged = {}
	for _, H in Character:GetChildren() do
		if not (H:IsA(`Model`) and H:GetAttribute(`NHAcc`) ~= nil) then continue end
		for _, P in H:GetChildren() do
			local T = Wear.ParseTuck(P:GetAttribute(`NHHairTuck`), HairKey)
			for N, V in T or {} do
				if not Merged[N] or V.Magnitude > Merged[N].Magnitude then Merged[N] = V end
			end
		end
	end
	if not TuckOK then Merged = {} end
	local S = if next(Merged) then Wear.JoinTuck(Merged) else nil
	Character:SetAttribute(`NHHairTuck`, S)
	-- pose the bones too (a preview or a dummy has no HairSway; a player's HairSway takes over every frame), now and
	-- once the look is on (ApplyTo puts the new hair on after the accessories)
	poseHair(Character, Merged)
	task.defer(function()
		if Character.Parent and Character:GetAttribute(`NHHairTuck`) == S then poseHair(Character, Merged) end
	end)
end

local function wearPiece(Character: Model, Holder: Model, Tpl: BasePart, BodyId: string?, HairKey: string, TuckOK: boolean)
	local MountKey = Tpl:GetAttribute(`NHMount`) or `Torso`
	local Mount = Character:FindFirstChild(PART[MountKey] or `Torso`)
	if not (Mount and Mount:IsA(`BasePart`)) then return end
	local K = Mount.Size.Y / (NOMINAL_Y[MountKey] or 2)
	local D = if MountKey == `Head` then 1 else depthFor(Tpl, BodyId)
	local Fit = Tpl:GetAttribute(`NHFit`)
	if typeof(Fit) ~= `CFrame` then Fit = CFrame.new() end
	local HK, HZ = Wear.HairFit(Tpl, HairKey)
	-- no measured fit for this hair: worn anyway at the default fit, the hair untucked (owner, 1.88: "It just wont
	-- have the new look for it"). A tuck an older rig can't take is left off the same way (applyTuck)
	if not HK then HK, HZ = Wear.DefaultFit(Tpl) end
	if MountKey ~= `Head` then HK, HZ = 1, 0 end
	local Seat = tonumber(Tpl:GetAttribute(`NHSeat`)) or 0.43
	local Pos = Vector3.new(Fit.X, Fit.Y, Fit.Z)
	local Radial = MountKey == `Head` and Tpl:GetAttribute(`NHHairScale`) == `Radial` -- a mask (see NHHairScale)
	if Radial and (HK ~= 1 or HZ ~= 0) then -- the hair fit: out round the head's axis, the eye holes kept level
		Pos = Vector3.new(Pos.X * HK, Pos.Y + HZ, Pos.Z * HK)
	elseif MountKey == `Head` and (HK ~= 1 or HZ ~= 0) then -- the hair fit: scale about the headband centre, then lift
		local Piv = Vector3.new(0, Seat, 0)
		Pos = Piv + (Pos - Piv) * HK + Vector3.new(0, HZ, 0)
	end
	local Off = CFrame.new(Pos.X * K, Pos.Y * K, Pos.Z * K * D) * Fit.Rotation
	local P = Tpl:Clone()
	local KY = K -- a radial fit leaves the height alone
	K *= HK
	if not Radial then KY = K end
	P.Size = Vector3.new(P.Size.X * K, P.Size.Y * KY, P.Size.Z * K * D)
	-- bones: scale each one's position in the PIECE's frame (a child bone's CFrame is relative to its parent, which may
	-- be turned), then rebuild the local CFrames so the chain keeps its directions
	local Scale = function(V: Vector3) return Vector3.new(V.X * K, V.Y * KY, V.Z * K * D) end
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
	local TuckOK = Wear.TuckableHair(Character, HairId)
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
			local ok, err = pcall(wearPiece, Character, Holder, Tpl, BodyId, HairKey, TuckOK)
			if not ok then warn(`[AccessoryWear] {Id}: {err}`) end
		end
		if #Holder:GetChildren() == 0 then -- no piece could be placed (no mount part): wear nothing for the slot
			Holder:Destroy()
			continue
		end
		Holder.Parent = Character
	end
	applyTuck(Character, HairKey, TuckOK)
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
