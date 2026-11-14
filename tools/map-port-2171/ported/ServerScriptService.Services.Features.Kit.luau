--[[
	The everyday-carry kit (server). Services.Features.Kit                  (owner approved 2026-11-11)
	Config: ReplicatedStorage.Config.Kit (items, numbers), Config.KitHolds (hold poses, grips, piece layout).
	Saved: PlayerData.Inventory.Kit (through Services.Features.Inventory.SetKit, ProfileService only).

	  * Owned for good. Pinned items (up to Kit.MaxPinned) are Tools in the Backpack (attribute NHKit), so they sit on the
	    hotbar beside the snacks. Equipping one poses the arm at once (the shoulder Motor6D C0, like the phone); the
	    client (World.KitFx) holds the joint still. The dorm keys are worn on the left leg; the hand warmer works from
	    the pocket while lit.
	  * Everything that changes the game happens here: lantern light and oil, the pass window, sips, biscuits,
	    bandages, loans and fines, the Night Chill, Wounded, rain nights, lost keys. Clients only draw.
	  * Counters: anything tagged NHKitShop (attribute Shop = Sundries | Cafe | Office | Archive), within Kit.Range.
	    NH Combat Test gets stand-in counters (Local.StandInCounters) when none are tagged.
	Attributes it writes (server only, so clients can't fake them):
	  Player    NHPassUntil (server time), NHKitKeys (owner UserId of the keys you carry)
	  Character NHChilled, NHSoaked, NHWounded, NHKitSlow (walk-speed factor while bandaging), NHUmbrellaOpen,
	            NHBandagedUntil, NHWarm (hand warmer lit)
	  workspace NHRain, NHRainEnd (game minute)
	Remotes ReplicatedStorage.NHKit (attribute Ready): Get (RF) -> state, Act (RF action, ...) -> ok, msg, Changed (RE)
	API: Get(p), HasKeys(p), Effects(p), LessonBonus(p, subject), IsIndoors(p), Grant(p, id)
]]
local CollectionService = game:GetService(`CollectionService`)
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local ServerStorage = game:GetService(`ServerStorage`)

local Data = require(ServerScriptService.Services.Player.Data)
local Notifications = require(ServerScriptService.Services.Features.Notifications)
local Kit = require(ReplicatedStorage.Config.Kit)
local Holds = require(ReplicatedStorage.Config.KitHolds)
local RegionsCfg = require(ReplicatedStorage.Config.Regions)

local Shared = {}
local Local = {}
local Remotes = nil

local LastCall = {} :: { [Player]: number }
local Busy = {} :: { [Player]: string? }
local Cool = {} :: { [Player]: { [string]: number } }
local Lit = {} :: { [Player]: boolean }                 -- the lantern is lit (only while it's in hand)
local Chill = {} :: { [Player]: { Out: number, In: number, Wet: number } }
local Dirty = {} :: { [Player]: number }                -- oil / charcoal burnt since the last save
local Dropped = {} :: { [number]: { Model: Model, Set: number, At: number } }   -- owner UserId -> keys on the ground
local Carrying = {} :: { [Player]: { Owner: number, Set: number } }

local EAT_ANIM = 126575676069500 -- the owner's "eating lunch" clip (Features.Inventory)
local GRIP_C0 = CFrame.new(0, -1, 0) * CFrame.Angles(math.rad(-90), 0, 0)   -- R6 RightGrip weld C0

---| small helpers |---

local function Inventory() return require(ServerScriptService.Services.Features.Inventory) end
local function now(): number return workspace:GetServerTimeNow() end
local function notify(P: Player, Title: string, Text: string?, Kind: string?)
	Notifications.Notify(P, { Title = Title; Text = Text; Kind = Kind or `Info`; Duration = 3.5 })
end
local function clock()
	local Ok, S = pcall(function() return require(ServerScriptService.Services.School.SchoolClock).GetState() end)
	return if Ok then S else nil
end
-- the 6 AM event day (like Inventory.Daily and the cliques' dares)
function Local.Day(): number
	local S = clock()
	if not S then return 0 end
	return if S.Hour >= 6 then S.Day else S.Day - 1
end
local function tagged(P: Player): boolean return (P:GetAttribute(`CombatTagUntil`) or 0) > now() end
local function hum(P: Player): Humanoid?
	local C = P.Character
	return C and C:FindFirstChildOfClass(`Humanoid`)
end
local function down(P: Player): boolean
	local C = P.Character
	local H = hum(P)
	return not H or H.Health <= 0 or C:GetAttribute(`DownedUntil`) ~= nil or C:GetAttribute(`Downed`) == true or H:GetAttribute(`Downed`) == true
end
local function price(P: Player, Shop: string, Base: number): number
	local F = 1
	pcall(function() F = require(ReplicatedStorage.Config.Cliques).PriceFactor(P, `Kit{Shop}`) or 1 end)
	return math.ceil(Base * F)
end

---| data |---

function Shared.Get(P: Player)
	local Inv = Inventory().Get(P)
	return Inv and Inv.Kit
end

function Local.Save(P: Player, K)
	Inventory().SetKit(P, K)
	Dirty[P] = nil
	Local.SyncTools(P, K)
	Local.Push(P)
end

function Shared.State(P: Player)
	local K = Shared.Get(P)
	if not K then return nil end
	local Profile = Data.GetProfile(P)
	local S = clock()
	return { Kit = K; Yen = Profile and Profile.Yen or 0; Day = Local.Day(); Lit = Lit[P] == true;
		Period = S and `D{S.Day}-S{S.SegmentIndex}` or nil; Carrying = Carrying[P] and Carrying[P].Owner or nil }
end

function Local.Push(P: Player)
	if Remotes and P.Parent then
		local S = Shared.State(P)
		if S then Remotes.Changed:FireClient(P, S) end
	end
end

-- give an item outright (starter kit, admin, quests); sets its first charges and pins it if there's room
function Shared.Grant(P: Player, Id: string, K): boolean
	local Own = K or Shared.Get(P)
	local It = Kit.ById[Id]
	if not (Own and It) then return false end
	Own.Owned[Id] = true
	if Id == `Lantern` then Own.Oil = Kit.Lantern.Tank
	elseif Id == `Thermos` then Own.Flask = { Kind = `Tea`; Cups = Kit.Thermos.Cups }
	elseif Id == `SnackTin` then Own.Biscuits = Kit.Tin.Biscuits
	elseif Id == `FirstAid` then Own.Bandages = Kit.Aid.Bandages
	elseif Id == `HandWarmer` then Own.Warmer.Sticks = math.max(Own.Warmer.Sticks, 1)
	elseif Id == `HallPass` then Own.Pass = { Punches = Kit.Pass.Punches; Day = Local.Day(); Key = nil }
	elseif Id == `KeyRing` then Own.Keys.Lost = false end
	if It.Hotbar and not table.find(Own.Pinned, Id) and #Own.Pinned < Kit.MaxPinned then table.insert(Own.Pinned, Id) end
	if not K then Local.Save(P, Own) end
	return true
end

function Local.Starter(P: Player)
	local K = Shared.Get(P)
	if not K or K.Starter then return end
	for _, It in Kit.Items do if It.Starter and not K.Owned[It.Id] then Shared.Grant(P, It.Id, K) end end
	K.Starter = true
	Local.Save(P, K)
	notify(P, `Your everyday kit`, `A campus map, your timetable card and your dorm keys. They're in your Locker (\`).`, `Good`)
end

---| the models |---

-- ReplicatedStorage.NHKit.Models.<Id>: BaseParts laid out in item space (origin = the grip point; for the keys,
-- character space). Until the owner imports the meshes, a stand-in is built from the layout's piece boxes.
local STANDIN = {
	Lantern = Color3.fromRGB(150, 110, 56); CampusMap = Color3.fromRGB(214, 198, 160); Compass = Color3.fromRGB(196, 150, 70);
	Umbrella = Color3.fromRGB(24, 22, 26); Timetable = Color3.fromRGB(226, 214, 186); KeyRing = Color3.fromRGB(150, 120, 70);
	HallPass = Color3.fromRGB(150, 26, 36); LibraryBook = Color3.fromRGB(34, 44, 66); Thermos = Color3.fromRGB(26, 24, 28);
	SnackTin = Color3.fromRGB(120, 18, 30); FirstAid = Color3.fromRGB(20, 18, 20); HandWarmer = Color3.fromRGB(170, 130, 60);
}
function Local.StandIn(Id: string): Model
	local M = Instance.new(`Model`)
	M.Name = Id
	local H = Holds[Id]
	for Name, Pc in (H and H.Pieces) or {} do
		local P = Instance.new(`Part`)
		P.Name = Name
		P.Size = Vector3.new(math.max(Pc.Size[1], 0.05), math.max(Pc.Size[2], 0.05), math.max(Pc.Size[3], 0.05))
		P.CFrame = CFrame.new(Pc.Centre[1], Pc.Centre[2], Pc.Centre[3])
		P.Material = if Pc.Kind == `Glow` then Enum.Material.Neon elseif Pc.Kind == `Glass` then Enum.Material.Glass else Enum.Material.SmoothPlastic
		P.Color = if Pc.Kind == `Glow` and Pc.Glow then Color3.new(Pc.Glow[1], Pc.Glow[2], Pc.Glow[3]) else STANDIN[Id] or Color3.new(0.5, 0.5, 0.5)
		P.Transparency = if Pc.Kind == `Glass` then 0.6 else 0
		P.Parent = M
	end
	M:SetAttribute(`NHStandIn`, true)
	return M
end

function Shared.Model(Id: string): Model
	local Lib = ReplicatedStorage:FindFirstChild(`NHKit`)
	local Store = Lib and Lib:FindFirstChild(`Models`)
	local T = Store and Store:FindFirstChild(Id)
	return if T then T:Clone() else Local.StandIn(Id)
end

local function prep(P: BasePart)
	P.Anchored = false
	P.CanCollide, P.CanQuery, P.CanTouch, P.Massless = false, false, false, true
	P.CastShadow = true
end

---| hotbar tools |---

function Local.Glow(T: Instance): BasePart?
	for _, D in T:GetDescendants() do
		if D:IsA(`BasePart`) and (D.Name:find(`_Glow`) or D:GetAttribute(`NHGlow`)) then return D end
	end
	return nil
end

-- the wearer's body type (UI.Appearance.Bodies id) and even scale (Heights: ScaleTo), for the fit
function Local.BodyOf(P: Player): (string, number)
	local Body = `standard`
	pcall(function()
		local Look = Data.GetProfile(P).Appearance
		local Bodies = require(ReplicatedStorage.UI.Appearance).Bodies
		local B = Look and Bodies[Look.Body]
		if B and B.Id then Body = B.Id end
	end)
	local Char = P.Character
	local W = 1
	pcall(function() W = Char:GetScale() end)
	return Body, W
end

-- (re)build a tool's model and grip for its holder: the body's fit (Config.KitHolds Fit, in the arm's frame) and the
-- character's scale (the item scales about the hand point, like the accessories do)
function Local.Dress(P: Player, T: Tool, Id: string)
	local Body, W = Local.BodyOf(P)
	local Key = `{Body}@{math.floor(W * 100 + 0.5)}`
	if T:GetAttribute(`NHFitKey`) == Key and T:FindFirstChild(Id) then return end
	local Old = T:FindFirstChild(Id)
	if Old then Old:Destroy() end
	local Handle = T:FindFirstChild(`Handle`) :: BasePart
	local H = Holds[Id] or {}
	local Model = Shared.Model(Id)
	Model.Name = Id
	for _, D in Model:GetDescendants() do
		if D:IsA(`BasePart`) then
			prep(D)
			if math.abs(W - 1) > 0.005 then
				D.Size *= W
				D.CFrame = D.CFrame.Rotation + D.CFrame.Position * W
			end
			D.CFrame = Handle.CFrame * D.CFrame
			if Id == `Lantern` or D.Material == Enum.Material.Glass then D.CastShadow = false end   -- don't shade the flame's light
			if D.Name == `Compass_Needle` then   -- a Weld, so the holder's client can turn the needle to its target
				local Wd = Instance.new(`Weld`)
				Wd.Name = `NHNeedleWeld`
				Wd.Part0, Wd.Part1 = Handle, D
				Wd.C0 = Handle.CFrame:ToObjectSpace(D.CFrame)
				Wd.Parent = D
			else
				local Wc = Instance.new(`WeldConstraint`)
				Wc.Part0, Wc.Part1 = Handle, D
				Wc.Parent = D
			end
		end
	end
	Model.Parent = T
	-- the lantern's light (off until it's lit; a refit keeps it lit or dark as it was)
	if Id == `Lantern` then
		local Glow = Local.Glow(T)
		if Glow then
			local L = Instance.new(`PointLight`)
			L.Name = `LanternLight`
			L.Range, L.Brightness, L.Color, L.Shadows = Kit.Lantern.Range, Kit.Lantern.Brightness, Kit.Lantern.Color, true
			L.Parent = Glow
			Glow:SetAttribute(`NHLitColor`, Glow.Color)
			local On = T:GetAttribute(`Lit`) == true
			L.Enabled = On
			if not On then Glow.Color = Color3.fromRGB(60, 44, 30) Glow.Material = Enum.Material.SmoothPlastic end
		end
	end
	if H.Grip then
		local G = H.Grip
		local InArm = CFrame.new(G[1], G[2], G[3], G[4], G[5], G[6], G[7], G[8], G[9], G[10], G[11], G[12])
		local F = H.Fit and H.Fit[Body]
		if F then InArm = CFrame.new(F[1], F[2], F[3]) * InArm end
		-- scale about the hand point (the arm's bottom centre, (0, -1, 0) on the nominal arm)
		local FromHand = CFrame.new(0, 1, 0) * InArm
		FromHand = FromHand.Rotation + FromHand.Position * W
		T.Grip = (CFrame.new(0, -1, 0) * FromHand):Inverse() * GRIP_C0
	end
	T:SetAttribute(`NHFitKey`, Key)
end

function Local.MakeTool(P: Player, Id: string): Tool
	local It = Kit.ById[Id]
	local H = Holds[Id] or {}
	local T = Instance.new(`Tool`)
	T.Name = It.Name
	T.CanBeDropped = false
	T.RequiresHandle = true
	T.ToolTip = It.Use
	T:SetAttribute(`NHKit`, Id)
	T:SetAttribute(`Rarity`, It.Rarity)
	local Handle = Instance.new(`Part`)
	Handle.Name = `Handle`
	Handle.Size = Vector3.new(0.2, 0.2, 0.2)
	Handle.Transparency = 1
	Handle.CFrame = CFrame.new()
	prep(Handle)
	Handle.Parent = T
	Local.Dress(P, T, Id)
	T.Activated:Connect(function()
		local Ok, Msg = Shared.Use(P, Id)
		if Msg then notify(P, Msg) end -- (inventory audit 1.90) the book's "due back" line is a success message
	end)
	T.Equipped:Connect(function() Local.OnEquip(P, T, Id, true) end)
	T.Unequipped:Connect(function() Local.OnEquip(P, T, Id, false) end)
	return T
end

function Local.Pose(Char: Model?, Id: string, On: boolean)
	local Torso = Char and Char:FindFirstChild(`Torso`)
	local H = Holds[Id]
	if not (Torso and H) then return end
	for _, Side in { `Right`, `Left` } do
		local A = if Side == `Right` then H.R else H.L
		local M = Torso:FindFirstChild(`{Side} Shoulder`) :: Motor6D?
		if not (A and M) then continue end
		local Base = M:GetAttribute(`NHBaseC0`)
		if Base == nil then Base = M.C0 M:SetAttribute(`NHBaseC0`, Base) end
		if On then
			local Pitch, Yaw = math.rad(A[1]), math.rad(A[2])
			M.C0 = if Side == `Right` then Base * CFrame.Angles(0, Yaw, 0) * CFrame.Angles(0, 0, Pitch)
				else Base * CFrame.Angles(0, -Yaw, 0) * CFrame.Angles(0, 0, -Pitch)
		else
			M.C0 = Base
		end
	end
end

function Local.OnEquip(P: Player, T: Tool, Id: string, On: boolean)
	local Char = P.Character
	if On and Id == `Umbrella` and tagged(P) then
		task.defer(function() local H = hum(P) if H then H:UnequipTools() end end)
		notify(P, `Not in a fight`, `The umbrella stays shut while you're combat-tagged.`)
		return
	end
	if On then pcall(Local.Dress, P, T, Id) end
	Local.Pose(Char, Id, On)
	if On and Kit.AnimOnEquip[Id] then task.defer(pcall, Local.PlayUse, P, Id) end
	if Char then
		Char:SetAttribute(`NHKitHolding`, if On then Id else nil)
		if Id == `Umbrella` then Char:SetAttribute(`NHUmbrellaOpen`, if On then true else nil) end
	end
	if not On and Id == `Lantern` and Lit[P] then Local.SetLit(P, T, false) end
end

function Local.SetLit(P: Player, T: Tool?, On: boolean)
	Lit[P] = On or nil
	T = T or Local.ToolOf(P, `Lantern`)
	local Glow = T and Local.Glow(T)
	if Glow then
		local L = Glow:FindFirstChild(`LanternLight`) :: PointLight?
		if L then L.Enabled = On end
		Glow.Color = if On then (Glow:GetAttribute(`NHLitColor`) or Color3.fromRGB(255, 158, 66)) else Color3.fromRGB(60, 44, 30)
		Glow.Material = if On then Enum.Material.Neon else Enum.Material.SmoothPlastic
	end
	if T then T:SetAttribute(`Lit`, On or nil) end
	if not On and Dirty[P] then local K = Shared.Get(P) if K then Local.Flush(P, K) end end
end

function Local.ToolOf(P: Player, Id: string): Tool?
	for _, Holder in { P:FindFirstChildOfClass(`Backpack`), P.Character } do
		for _, T in (Holder and Holder:GetChildren()) or {} do
			if T:IsA(`Tool`) and T:GetAttribute(`NHKit`) == Id then return T end
		end
	end
	return nil
end

function Local.SyncTools(P: Player, K)
	K = K or Shared.Get(P)
	local Pack = P:FindFirstChildOfClass(`Backpack`)
	if not (K and Pack) then return end
	local Want = {}
	for _, Id in K.Pinned do if K.Owned[Id] and Kit.ById[Id] and Kit.ById[Id].Hotbar then Want[Id] = true end end
	local Have = {}
	for _, Holder in { Pack, P.Character } do
		for _, T in (Holder and Holder:GetChildren()) or {} do
			local Id = T:IsA(`Tool`) and T:GetAttribute(`NHKit`)
			if Id then
				if Want[Id] and not Have[Id] then Have[Id] = T else T:Destroy() end
			end
		end
	end
	for _, Id in K.Pinned do
		if Want[Id] and not Have[Id] then Have[Id] = Local.MakeTool(P, Id) Have[Id].Parent = Pack end
	end
	for Id, T in Have do
		T:SetAttribute(`Count`, Kit.Count(Id, K))
		T:SetAttribute(`NHCharge`, Kit.Charge(Id, K))
	end
	Local.Wear(P, K)
end

-- the dorm keys on the left leg (gone while they're lost)
function Local.Wear(P: Player, K)
	local Char = P.Character
	local Leg = Char and Char:FindFirstChild(`Left Leg`) :: BasePart?
	if not Leg then return end
	local Old = Char:FindFirstChild(`NHKitKeys`)
	local Want = K.Owned.KeyRing and not K.Keys.Lost
	if not Want then if Old then Old:Destroy() end return end
	local Body = Local.BodyOf(P)
	local Key = `{Body}@{math.floor(Leg.Size.X * 100 + 0.5)}x{math.floor(Leg.Size.Y * 100 + 0.5)}`
	if Old and Old:GetAttribute(`NHFitKey`) == Key then return end
	if Old then Old:Destroy() end
	local M = Shared.Model(`KeyRing`)
	M.Name = `NHKitKeys`
	M:SetAttribute(`NHFitKey`, Key)
	local F = Holds.KeyRing and Holds.KeyRing.Fit and Holds.KeyRing.Fit[Body]
	local Off = if F then Vector3.new(F[1], F[2], F[3]) else Vector3.zero
	-- the leg's centre is (-0.5, -2, 0) in character space; scale the hang to this leg (height, stretch, thickness)
	local Sc = Vector3.new(Leg.Size.X / 1, Leg.Size.Y / 2, Leg.Size.Z / 1)
	for _, D in M:GetDescendants() do
		if D:IsA(`BasePart`) then
			local L = D.CFrame.Position + Vector3.new(0.5, 2, 0) + Off
			D.Size *= math.min(Sc.X, Sc.Z)
			D.CFrame = Leg.CFrame * (D.CFrame.Rotation + L * Sc)
			prep(D)
			local W = Instance.new(`WeldConstraint`)
			W.Part0, W.Part1 = Leg, D
			W.Parent = D
		end
	end
	M.Parent = Char
end

---| using |---

function Local.Anim(P: Player, Seconds: number, Id: string?)
	local Own = Id and Kit.Anims and Kit.Anims[Id]
	if typeof(Own) == `number` and Own > 0 then return end   -- the item's own clip plays instead (Local.PlayUse)
	local H = hum(P)
	local Animator = H and H:FindFirstChildOfClass(`Animator`)
	if not Animator then return end
	local A = Instance.new(`Animation`)
	A.AnimationId = `rbxassetid://{EAT_ANIM}`
	local Ok, Tr = pcall(function() return Animator:LoadAnimation(A) end)
	if not Ok then return end
	Tr.Priority = Enum.AnimationPriority.Action
	Tr:Play(0.15)
	task.delay(Seconds, function() Tr:Stop(0.25) end)
end

function Local.Cool(P: Player, Key: string, Seconds: number?): number
	Cool[P] = Cool[P] or {}
	local Left = (Cool[P][Key] or 0) - now()
	if Seconds and Left <= 0 then Cool[P][Key] = now() + Seconds end
	return Left
end

-- the item's own use clip, once the owner has published it (Config.Kit.Anims); the client lets the posed shoulder
-- move while NHKitAnim is set
function Local.PlayUse(P: Player, Id: string)
	local AnimId = Kit.Anims and Kit.Anims[Id]
	local H = hum(P)
	local Animator = H and H:FindFirstChildOfClass(`Animator`)
	if not (typeof(AnimId) == `number` and AnimId > 0 and Animator) then return end
	local A = Instance.new(`Animation`)
	A.AnimationId = `rbxassetid://{AnimId}`
	local Ok, Tr = pcall(function() return Animator:LoadAnimation(A) end)
	if not Ok then return end
	Tr.Priority = Enum.AnimationPriority.Action2
	local Char = P.Character
	Char:SetAttribute(`NHKitAnim`, true)
	Tr:Play(0.12)
	Tr.Stopped:Once(function() if Char.Parent then Char:SetAttribute(`NHKitAnim`, nil) end end)
end

function Shared.Use(P: Player, Id: any): (boolean, string?)
	local Ok, Msg = Local.UseInner(P, Id)
	if Ok and typeof(Id) == `string` and not Kit.AnimOnEquip[Id] then pcall(Local.PlayUse, P, Id) end
	return Ok, Msg
end

-- the key turning in your dorm door (Features.Homes calls this as you go in)
function Shared.KeyTurn(P: Player) pcall(Local.PlayUse, P, `KeyRing`) end

function Local.UseInner(P: Player, Id: any): (boolean, string?)
	local It = typeof(Id) == `string` and Kit.ById[Id]
	if not It then return false, `Unknown item.` end
	local K = Shared.Get(P)
	if not K or not K.Owned[Id] then return false, `You don't have that.` end
	if P:GetAttribute(`InMainMenu`) == true then return false, nil end
	if down(P) then return false, `Not while you're down.` end
	if Busy[P] then return false, nil end
	if Id == `Lantern` then
		local T = Local.ToolOf(P, `Lantern`)
		if not (T and T.Parent == P.Character) then return false, `Hold the lantern to light it.` end
		if Lit[P] then Local.SetLit(P, T, false) return true end
		if K.Oil <= 0 then return false, `Out of oil. MORROW & VANE sells lamp oil.` end
		Local.SetLit(P, T, true)
		return true
	elseif Id == `HallPass` then
		return Local.ShowPass(P, K)
	elseif Id == `Thermos` then
		return Local.Sip(P, K)
	elseif Id == `SnackTin` then
		return Local.Biscuit(P, K)
	elseif Id == `FirstAid` then
		return Local.Bandage(P, K)
	elseif Id == `HandWarmer` then
		local W = K.Warmer
		if W.Lit then W.Lit = false Local.Save(P, K) notify(P, `Hand warmer`, `You let it go cold.`) return true end
		if W.Burn <= 0 then
			if W.Sticks <= 0 then return false, `No charcoal. MORROW & VANE sells sticks for the warmer.` end
			W.Sticks -= 1
			W.Burn = Kit.Warmer.Burn
		end
		W.Lit = true
		Local.Save(P, K)
		notify(P, `Hand warmer lit`, `The coals glow. The night chill can't touch you while it burns.`, `Good`)
		return true
	elseif Id == `LibraryBook` then
		local B = K.Book and Kit.BookById[K.Book.Id]
		if not B then return false, nil end
		local Left = K.Book.Due - Local.Day()
		return true, if Left < 0 then `{B.Name} is overdue. Return it to the Archive.` else `{B.Name}: due back in {Left} school day{if Left == 1 then `` else `s`}.`
	end
	return true   -- the map, compass and card are drawn on the client
end

-- the hall pass: one punch a class period; the monitor lets you be for Kit.Pass.Seconds
function Local.ShowPass(P: Player, K): (boolean, string?)
	local S = clock()
	if not S or S.Segment.Kind ~= `Class` then return false, `No need for a pass outside class.` end
	-- (2.8.1) the Office voids passes for students on Probation or Suspension (Config.Discipline.Record.NoPassLevels)
	local Level = P:GetAttribute(`DisciplineLevel`)
	local Rec = require(game:GetService(`ReplicatedStorage`).Config.Discipline).Record
	if Rec and Rec.NoPassLevels[Level] then return false, `The Office voided your pass while you're on {Level}.` end
	if K.Pass.Punches <= 0 then return false, `Your pass is fully punched. The Office sells a new one.` end
	local Key = `D{S.Day}-S{S.SegmentIndex}`
	if K.Pass.Key == Key then return false, `You've already used your pass this period.` end
	-- being chased: the pass works only if you show it quickly
	-- (the monitor model carries MonitorTarget / MonitorChaseAt, set by School.HallMonitor)
	for _, Model in workspace:GetDescendants() do
		if Model:IsA(`Model`) and Model:GetAttribute(`MonitorTarget`) == P.UserId then
			-- (inventory audit 1.90) a pass covers being out of class, not a fight or paint (School.HallMonitor)
			if (Model:GetAttribute(`MonitorReason`) or `Truancy`) ~= `Truancy` then return false, `A pass won't get you out of this.` end
			local At = Model:GetAttribute(`MonitorChaseAt`)
			if At and os.clock() - At > Kit.Pass.ChaseGrace then return false, `Too late for that. You're caught out.` end
		end
	end
	K.Pass.Punches -= 1
	K.Pass.Key = Key
	P:SetAttribute(`NHPassUntil`, now() + Kit.Pass.Seconds)
	Local.Save(P, K)
	notify(P, `Hall pass shown`, `The hall monitor will let you be for {Kit.Pass.Seconds} seconds. It still isn't attendance.`, `Good`)
	return true
end

function Local.Sip(P: Player, K): (boolean, string?)
	if K.Flask.Cups <= 0 then return false, `The flask is empty. THE WICK & KETTLE refills it.` end
	local Left = Local.Cool(P, `Sip`)
	if Left > 0 then return false, `Let it cool ({math.ceil(Left)} s).` end
	Local.Cool(P, `Sip`, Kit.Thermos.Cooldown + Kit.Thermos.SipTime)
	Busy[P] = `Sip`
	Local.Anim(P, Kit.Thermos.SipTime, `Thermos`)
	local Kind = K.Flask.Kind
	task.delay(Kit.Thermos.SipTime, function()
		Busy[P] = nil
		local H = hum(P)
		if not (P.Parent and H and not down(P)) then return end
		local K2 = Shared.Get(P)
		if not K2 or K2.Flask.Cups <= 0 then return end
		K2.Flask.Cups -= 1
		local Amount = Kit.Thermos.Posture * (if tagged(P) then 0.5 else 1)
		local Post = H:GetAttribute(`Posture`) or 0
		if Post > 0 then H:SetAttribute(`Posture`, math.max(0, Post - Amount)) end
		-- a sports match reads and clears this on its next stamina tick (Sports.Basketball / Soccer / Football)
		P:SetAttribute(`NHStaminaBoost`, Kit.Thermos.Stamina)
		task.delay(2, function() if P.Parent then P:SetAttribute(`NHStaminaBoost`, nil) end end)
		if Kind == `Tea` then
			local C = Chill[P]
			if C then C.Out, C.Wet = 0, 0 end
			if P.Character then P.Character:SetAttribute(`NHChilled`, nil) P.Character:SetAttribute(`NHSoaked`, nil) end
		else
			-- (inventory audit 1.90) the coffee never replaces a snack buff you paid for
			local Cur, Until = P:GetAttribute(`NHSnackBuff`), P:GetAttribute(`NHSnackBuffUntil`) or 0
			if Cur == nil or Cur == Kit.Thermos.CoffeeBuff or Until <= now() then
				pcall(function() Inventory().GiveBuff(P, Kit.Thermos.CoffeeBuff) end)
			end
		end
		Local.Save(P, K2)
	end)
	return true
end

function Local.Biscuit(P: Player, K): (boolean, string?)
	if K.Biscuits <= 0 then return false, `The tin is empty. THE WICK & KETTLE refills it.` end
	if tagged(P) then return false, `Not in a fight.` end
	local Ok, Msg = Inventory().KitEat(P, Kit.Tin.Heal, Kit.Tin.Duration, function()
		local K2 = Shared.Get(P)
		if K2 and K2.Biscuits > 0 then K2.Biscuits -= 1 Local.Save(P, K2) return true end
		return false
	end, (Kit.Anims and Kit.Anims.SnackTin or 0) ~= 0) -- (inventory audit 1.90) the tin's own clip, not the eating one too
	return Ok, Msg
end

function Local.Bandage(P: Player, K): (boolean, string?)
	if K.Bandages <= 0 then return false, `No bandages left. MORROW & VANE sells them.` end
	local H = hum(P)
	if not H then return false, nil end
	if H.Health >= H.MaxHealth and not (P.Character and P.Character:GetAttribute(`NHWounded`)) then return false, `You're not hurt.` end
	Busy[P] = `Bandage`
	local Char = P.Character
	Char:SetAttribute(`NHKitSlow`, Kit.Aid.ChannelSpeed)
	Local.Anim(P, Kit.Aid.Channel, `FirstAid`)
	task.spawn(function()
		local Start, Hp = os.clock(), H.Health
		local Cancelled = false
		while os.clock() - Start < Kit.Aid.Channel do
			task.wait(0.1)
			if not (H.Parent and P.Parent) or down(P) or H.Health < Hp - 0.01 then Cancelled = true break end
			Hp = math.max(Hp, H.Health)
		end
		Busy[P] = nil
		if Char.Parent then Char:SetAttribute(`NHKitSlow`, nil) end
		if Cancelled then
			if P.Parent then notify(P, `Interrupted`, `You took a hit. The bandage is still in the pouch.`) end
			return
		end
		local K2 = Shared.Get(P)
		if not K2 or K2.Bandages <= 0 then return end
		K2.Bandages -= 1
		Local.Save(P, K2)
		Char:SetAttribute(`NHBandagedUntil`, now() + Kit.Aid.Clears)
		Char:SetAttribute(`NHWounded`, nil)
		local Steps = math.floor(Kit.Aid.Duration / 0.5)
		for _ = 1, Steps do
			if not (H.Parent and H.Health > 0) or down(P) then return end
			H.Health = math.min(H.MaxHealth, H.Health + Kit.Aid.Heal / Steps)
			task.wait(0.5)
		end
	end)
	return true
end

---| counters: buying, refills, loans |---

function Local.NearShop(P: Player, Shop: string): Instance?
	local Root = P.Character and P.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	if not Root then return nil end
	for _, S in CollectionService:GetTagged(`NHKitShop`) do
		if S:GetAttribute(`Shop`) ~= Shop or not S:IsDescendantOf(workspace) then continue end
		local Pos = if S:IsA(`BasePart`) then S.Position elseif S:IsA(`Model`) then S:GetPivot().Position else nil
		if Pos and (Pos - Root.Position).Magnitude <= Kit.Range then return S end
	end
	return nil
end

function Local.Pay(P: Player, Amount: number): boolean
	if Amount <= 0 then return true end
	local Profile = Data.GetProfile(P)
	if not Profile or (Profile.Yen or 0) < Amount then return false end
	Data.UpdateState(P, { type = `UpdateYen`; amount = -Amount })
	return true
end

function Shared.Buy(P: Player, Id: any): (boolean, string?)
	local It = typeof(Id) == `string` and Kit.ById[Id]
	if not (It and It.Shop and It.Price) then return false, `Not sold here.` end
	if not Local.NearShop(P, It.Shop) then return false, `You're too far from the counter.` end
	local K = Shared.Get(P)
	if not K then return false, `Your record isn't loaded yet.` end
	if Id == `HallPass` then
		if K.Pass.Day == Local.Day() and K.Owned.HallPass then return false, `One pass a day. Come back tomorrow.` end
		if K.Owned.HallPass and K.Pass.Punches > 0 then return false, `Your pass still has punches left.` end
	elseif K.Owned[Id] then
		return false, `You already have one.`
	end
	local Cost = price(P, It.Shop, It.Price)
	if not Local.Pay(P, Cost) then return false, `Not enough Yen.` end
	K = Shared.Get(P)
	Shared.Grant(P, Id, K)
	Local.Save(P, K)
	return true, `Bought: {It.Name}.` .. (if It.Hotbar and table.find(K.Pinned, Id) then ` It's on your hotbar.` elseif It.Hotbar then ` Pin it from your Locker.` else ``)
end

function Shared.Refill(P: Player, Id: any): (boolean, string?)
	local R = typeof(Id) == `string` and Kit.RefillById[Id]
	if not R then return false, `Not sold here.` end
	if not Local.NearShop(P, R.Shop) then return false, `You're too far from the counter.` end
	local K = Shared.Get(P)
	if not K then return false, `Your record isn't loaded yet.` end
	if R.Needs and not K.Owned[R.Needs] then return false, `You need the {Kit.ById[R.Needs].Name} for that.` end
	if Id == `LampOil` and K.Oil >= Kit.Lantern.Tank - 1 then return false, `The tank is already full.` end
	if Id == `Charcoal` and K.Warmer.Sticks >= Kit.Warmer.MaxSticks then return false, `You can't carry more sticks.` end
	if Id == `Bandages` and K.Bandages >= Kit.Aid.Bandages then return false, `The pouch is already full.` end
	if Id == `Biscuits` and K.Biscuits >= Kit.Tin.Biscuits then return false, `The tin is already full.` end
	if (Id == `Tea` or Id == `Coffee`) and K.Flask.Cups >= Kit.Thermos.Cups and K.Flask.Kind == Id then return false, `The flask is already full.` end
	if Id == `NewKeys` and not K.Keys.Lost and K.Owned.KeyRing then return false, `You have your keys.` end
	if Id == `LibraryCard` and K.Card then return false, `You already have a library card.` end
	if not Local.Pay(P, price(P, R.Shop, R.Price)) then return false, `Not enough Yen.` end
	K = Shared.Get(P)
	if Id == `LampOil` then K.Oil = Kit.Lantern.Tank
	elseif Id == `Charcoal` then K.Warmer.Sticks += 1
	elseif Id == `Bandages` then K.Bandages = Kit.Aid.Bandages
	elseif Id == `Biscuits` then K.Biscuits = Kit.Tin.Biscuits
	elseif Id == `Tea` or Id == `Coffee` then K.Flask = { Kind = Id; Cups = Kit.Thermos.Cups }
	elseif Id == `NewKeys` then
		K.Keys = { Lost = false; Set = K.Keys.Set + 1 }
		K.Owned.KeyRing = true
		local D = Dropped[P.UserId]
		if D then if D.Model.Parent then D.Model:Destroy() end Dropped[P.UserId] = nil end
	elseif Id == `LibraryCard` then K.Card = true end
	Local.Save(P, K)
	return true, if Id == `NewKeys` then `A new set of keys. The old ones won't turn.` else `Done: {R.Name}.`
end

function Shared.Borrow(P: Player, BookId: any): (boolean, string?)
	local B = typeof(BookId) == `string` and Kit.BookById[BookId]
	if not B then return false, `That isn't on the shelf.` end
	if not Local.NearShop(P, `Archive`) then return false, `Borrow at the Archive desk.` end
	local K = Shared.Get(P)
	if not K then return false, nil end
	if not K.Card then return false, `You need a library card first (free at the desk).` end
	if K.Book then return false, `One book at a time. Return the one you have.` end
	if K.Fine > 0 then return false, `You owe a fine of \u{A5}{K.Fine}. Pay it first.` end
	K.Book = { Id = B.Id; Due = Local.Day() + Kit.Book.LoanDays }
	K.Owned.LibraryBook = true
	if not table.find(K.Pinned, `LibraryBook`) and #K.Pinned < Kit.MaxPinned then table.insert(K.Pinned, `LibraryBook`) end
	Local.Save(P, K)
	local Pinned = table.find(K.Pinned, `LibraryBook`) ~= nil
	return true, `Borrowed {B.Name}. Due back in {Kit.Book.LoanDays} school days.` ..
		(if Pinned then `` else ` Pin it to your hotbar from the Locker to study with it.`)
end

function Shared.Return(P: Player): (boolean, string?)
	if not Local.NearShop(P, `Archive`) then return false, `Return books at the Archive desk.` end
	local K = Shared.Get(P)
	if not (K and K.Book) then return false, `You haven't borrowed anything.` end
	local Late = math.max(0, Local.Day() - K.Book.Due)
	local Fine = math.min(Kit.Book.FineMax, Late * Kit.Book.FinePerDay)
	local Msg = `Returned. Thank you.`
	local Paid = Fine > 0 and Local.Pay(P, Fine)
	if Fine > 0 then
		Msg = if Paid then `Returned {Late} day{if Late == 1 then `` else `s`} late. Fine paid: \u{A5}{Fine}.`
			else `Returned late. You owe \u{A5}{Fine}; no new loans until it's paid.`
	end
	K = Shared.Get(P)
	if Fine > 0 and not Paid then K.Fine = Fine end
	K.Book = nil
	K.Owned.LibraryBook = nil
	local At = table.find(K.Pinned, `LibraryBook`)
	if At then table.remove(K.Pinned, At) end
	Local.Save(P, K)
	return true, Msg
end

function Shared.PayFine(P: Player): (boolean, string?)
	if not Local.NearShop(P, `Archive`) then return false, `Pay at the Archive desk.` end
	local K = Shared.Get(P)
	if not K or K.Fine <= 0 then return false, `You don't owe anything.` end
	if not Local.Pay(P, K.Fine) then return false, `Not enough Yen.` end
	K = Shared.Get(P)
	local Paid = K.Fine
	K.Fine = 0
	Local.Save(P, K)
	return true, `Fine paid: \u{A5}{Paid}.`
end

function Shared.Pin(P: Player, Id: any, On: any): (boolean, string?)
	local It = typeof(Id) == `string` and Kit.ById[Id]
	local K = Shared.Get(P)
	if not (It and K and K.Owned[Id]) then return false, `You don't have that.` end
	if not It.Hotbar then return false, `That doesn't go on the hotbar.` end
	local At = table.find(K.Pinned, Id)
	if On and not At then
		if #K.Pinned >= Kit.MaxPinned then return false, `Your hotbar holds {Kit.MaxPinned} kit items. Unpin one first.` end
		table.insert(K.Pinned, Id)
	elseif not On and At then
		table.remove(K.Pinned, At)
		if Id == `Lantern` and Lit[P] then Local.SetLit(P, nil, false) end
	end
	Local.Save(P, K)
	return true
end

---| what the kit adds to your sheet (Progression.Effects) |---

function Local.BookActive(K): boolean
	return K and K.Book ~= nil and table.find(K.Pinned, `LibraryBook`) ~= nil and Local.Day() <= K.Book.Due
end

function Shared.Effects(P: Player)
	local K = Shared.Get(P)
	if Local.BookActive(K) then return { ClassExp = Kit.Book.ClassExp } end
	return {}
end

function Shared.LessonBonus(P: Player, Subject: string?): number
	local K = Shared.Get(P)
	if not (Subject and Local.BookActive(K)) then return 0 end
	local B = Kit.BookById[K.Book.Id]
	return if B and B.Subject == Subject then Kit.Book.Subject else 0
end

function Shared.HasKeys(P: Player): boolean
	local K = Shared.Get(P)
	return K ~= nil and K.Owned.KeyRing == true and not K.Keys.Lost
end

---| indoors, the chill, rain, wounds |---

local RayParams = RaycastParams.new()
RayParams.FilterType = Enum.RaycastFilterType.Exclude
RayParams.IgnoreWater = true
RayParams.RespectCanCollide = true -- (inventory audit 1.90) an invisible trigger overhead isn't a roof

function Shared.RegionAt(Pos: Vector3): string?
	local Folder = workspace:FindFirstChild(`Regions`)
	if not Folder then return nil end
	local Best, BestPri, BestVol = nil, -math.huge, math.huge
	for _, B in Folder:GetDescendants() do
		if not B:IsA(`BasePart`) then continue end
		local L = B.CFrame:PointToObjectSpace(Pos)
		local H = B.Size / 2
		if math.abs(L.X) <= H.X and math.abs(L.Y) <= H.Y and math.abs(L.Z) <= H.Z then
			local Id = B:GetAttribute(`RegionId`) or B.Name
			local Def = RegionsCfg.Defs and RegionsCfg.Defs[Id]
			local Pri = Def and Def.Priority or 0
			local Vol = B.Size.X * B.Size.Y * B.Size.Z
			if Pri > BestPri or (Pri == BestPri and Vol < BestVol) then Best, BestPri, BestVol = Id, Pri, Vol end
		end
	end
	return Best
end

function Shared.IsIndoors(P: Player): boolean
	if P:GetAttribute(`NHInHome`) ~= nil then return true end
	local Char = P.Character
	local Head = Char and Char:FindFirstChild(`Head`) :: BasePart?
	if not Head then return true end
	local Region = Shared.RegionAt(Head.Position)
	if Region and not Kit.OutdoorRegions[Region] then return true end
	-- outdoors by region, or no region: a solid roof overhead still counts as indoors (porches, arcades, buildings
	-- the region boxes don't cover)
	RayParams.FilterDescendantsInstances = { workspace:FindFirstChild(`Live`) or Char, workspace:FindFirstChild(`Regions`) }
	local Hit = workspace:Raycast(Head.Position + Vector3.new(0, 1, 0), Vector3.new(0, 60, 0), RayParams)
	return Hit ~= nil and Hit.Instance.Transparency < 0.9 and Hit.Instance.CanCollide
end

function Local.Night(S): boolean
	return S ~= nil and (S.Hour >= Kit.Chill.From or S.Hour < Kit.Chill.To)
end

-- once a second: lantern oil, warmer charcoal, chill, soaking, wounds
function Local.Tick(Dt: number)
	local S = clock()
	local Night = Local.Night(S)
	local Raining = workspace:GetAttribute(`NHRain`) == true
	for _, P in Players:GetPlayers() do
		local Char = P.Character
		local H = hum(P)
		if not (Char and H) or P:GetAttribute(`InMainMenu`) == true then continue end
		local K = Shared.Get(P)
		if not K then continue end
		-- fuel
		local Burnt = false
		if Lit[P] then
			K.Oil = math.max(0, K.Oil - Dt)
			Burnt = true
			if K.Oil <= 0 then Local.SetLit(P, nil, false) notify(P, `The lantern sputters out`, `Out of oil. MORROW & VANE sells lamp oil.`) end
		end
		local Warm = false
		if K.Warmer.Lit and K.Owned.HandWarmer then
			K.Warmer.Burn = math.max(0, K.Warmer.Burn - Dt)
			Burnt = true
			Warm = K.Warmer.Burn > 0
			if not Warm then K.Warmer.Lit = false notify(P, `Your hand warmer has gone cold`, if K.Warmer.Sticks > 0 then `Light it again to burn another stick.` else `MORROW & VANE sells charcoal.`) end
		end
		Char:SetAttribute(`NHWarm`, Warm or nil)
		if Burnt then
			Inventory().SetKit(P, K, true)   -- quiet: no tool rebuild, no push every second
			Dirty[P] = (Dirty[P] or 0) + Dt
			if Dirty[P] >= 30 or not Lit[P] and not K.Warmer.Lit then Local.Flush(P, K) end
		end
		-- the chill
		local C = Chill[P] or { Out = 0; In = 0; Wet = 0 }
		Chill[P] = C
		local Race = P:GetAttribute(`Race`)
		local Indoors = Shared.IsIndoors(P)
		local Shelter = Indoors or Char:GetAttribute(`NHUmbrellaOpen`) == true
		if Raining and not Shelter then C.Wet += Dt else C.Wet = math.max(0, C.Wet - Dt * 0.5) end
		local Soaked = C.Wet >= Kit.Rain.Soak
		Char:SetAttribute(`NHSoaked`, Soaked or nil)
		local Chilled = Char:GetAttribute(`NHChilled`) == true
		if Kit.Chill.Immune[Race] or Warm then
			C.Out, Chilled = 0, false
		elseif Night and not Indoors then
			C.In = 0
			C.Out += Dt / (Kit.Chill.Slow[Race] or 1)
			if C.Out >= Kit.Chill.After or Soaked then Chilled = true end
		elseif Chilled then
			C.In += Dt
			if C.In >= Kit.Chill.Fade then Chilled, C.Out, C.In = false, 0, 0 end
		else
			C.Out = math.max(0, C.Out - Dt)
		end
		Char:SetAttribute(`NHChilled`, Chilled or nil)
		-- wounds (cleared for a while by a bandage)
		local Wounded = H.Health > 0 and H.Health < H.MaxHealth * Kit.Wounded.Threshold and not down(P)
			and (Char:GetAttribute(`NHBandagedUntil`) or 0) < now()
		Char:SetAttribute(`NHWounded`, Wounded or nil)
		-- the umbrella snaps shut in a fight
		if Char:GetAttribute(`NHUmbrellaOpen`) and tagged(P) then
			H:UnequipTools()
			notify(P, `Your umbrella snaps shut`, `Not in a fight.`)
		end
	end
end

function Local.Flush(P: Player, K)
	Dirty[P] = nil
	Inventory().SetKit(P, K)
	Local.SyncTools(P, K)
	Local.Push(P)
end

-- rain nights: decided at Kit.Rain.StartHour once a game day
local RainRolledDay = nil
function Local.RainTick()
	local S = clock()
	if not S then return end
	local Minute = S.Day * 1440 + (S.MinuteOfDay or S.Hour * 60)
	local End = workspace:GetAttribute(`NHRainEnd`)
	if workspace:GetAttribute(`NHRain`) and End and Minute >= End then
		workspace:SetAttribute(`NHRain`, nil)
		workspace:SetAttribute(`NHRainEnd`, nil)
	end
	if S.Hour == Kit.Rain.StartHour and RainRolledDay ~= S.Day then
		RainRolledDay = S.Day
		if math.random() < Kit.Rain.Chance then Shared.StartRain(math.random(Kit.Rain.Hours[1], Kit.Rain.Hours[2]) * 60) end
	end
end

function Shared.StartRain(Minutes: number)
	local S = clock()
	if not S then return end
	local Minute = S.Day * 1440 + (S.MinuteOfDay or S.Hour * 60)
	workspace:SetAttribute(`NHRainEnd`, Minute + Minutes)
	workspace:SetAttribute(`NHRain`, true)
end

---| lost keys |---

function Local.DropKeys(P: Player)
	local K = Shared.Get(P)
	local Root = P.Character and P.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	if not (K and Root) or not Shared.HasKeys(P) then return end
	K.Keys.Lost = true
	Local.Save(P, K)
	notify(P, `Your keys fell out`, `Someone may hand them in. The Office cuts a new set for \u{A5}50.`, `Bad`)
	local Old = Dropped[P.UserId]
	if Old and Old.Model.Parent then Old.Model:Destroy() end
	RayParams.FilterDescendantsInstances = { workspace:FindFirstChild(`Live`) or P.Character }
	local Hit = workspace:Raycast(Root.Position, Vector3.new(0, -12, 0), RayParams)
	local Floor = if Hit then Hit.Position else Root.Position - Vector3.new(0, 3, 0)
	local M = Shared.Model(`KeyRing`)
	M.Name = `NHDroppedKeys`
	-- lay the ring flat on the floor (its parts are in character space around the left thigh)
	local Pivot = CFrame.new(Floor + Vector3.new(0, 0.05, 0)) * CFrame.Angles(math.rad(-90), math.rad(math.random(0, 359)), 0)
	local Centre = M:GetBoundingBox()
	for _, D in M:GetDescendants() do
		if D:IsA(`BasePart`) then
			D.CFrame = Pivot * Centre:Inverse() * D.CFrame
			D.Anchored, D.CanCollide, D.CanTouch = true, false, false
		end
	end
	local Anchor = M:FindFirstChildWhichIsA(`BasePart`)
	if Anchor then
		local Pr = Instance.new(`ProximityPrompt`)
		Pr.Name = `NHKeysPrompt`
		Pr.ActionText = `Pick up`
		Pr.ObjectText = `Dorm keys`
		Pr.HoldDuration = 0.3
		Pr.MaxActivationDistance = 8
		Pr.RequiresLineOfSight = false
		Pr.Parent = Anchor
		local Sp = Instance.new(`Sparkles`)
		Sp.SparkleColor = Color3.fromRGB(235, 205, 120)
		Sp.Parent = Anchor
		local OwnerId, Set = P.UserId, K.Keys.Set
		Pr.Triggered:Connect(function(F) Local.PickUpKeys(F, OwnerId, Set) end)
	end
	M:SetAttribute(`NHKeysOwner`, P.UserId)
	M.Parent = workspace
	Dropped[P.UserId] = { Model = M; Set = K.Keys.Set; At = os.clock() }
end

function Local.PickUpKeys(F: Player, OwnerId: number, Set: number)
	local D = Dropped[OwnerId]
	if not D or D.Set ~= Set then return end
	if down(F) then return end
	local Owner = Players:GetPlayerByUserId(OwnerId)
	if D.Model.Parent then D.Model:Destroy() end
	Dropped[OwnerId] = nil
	if F == Owner then
		local K = Shared.Get(F)
		if K and K.Keys.Set == Set then K.Keys.Lost = false Local.Save(F, K) notify(F, `Your keys`, `Back on your hip.`, `Good`) end
		return
	end
	if Carrying[F] then notify(F, `Your hands are full`, `Return the keys you're carrying first.`) return end
	Carrying[F] = { Owner = OwnerId; Set = Set }
	F:SetAttribute(`NHKitKeys`, OwnerId)
	notify(F, `You found someone's dorm keys`, if Owner then `They belong to {Owner.DisplayName}. Return them, or hand them in at the Office or a Lost & Found box (\u{A5}{Kit.Keys.Reward}).` else `Hand them in at the Office or a Lost & Found box.`)
	Local.Push(F)
end

function Local.GiveBack(F: Player): (boolean, string?)
	local C = Carrying[F]
	if not C then return false, `You aren't carrying anyone's keys.` end
	Carrying[F] = nil
	F:SetAttribute(`NHKitKeys`, nil)
	local Owner = Players:GetPlayerByUserId(C.Owner)
	if not Owner then Local.Push(F) return true, `Their owner has gone home. The Office will keep them.` end -- (inventory audit 1.90)
	local K = Shared.Get(Owner)
	if K and K.Keys.Lost and K.Keys.Set == C.Set then
		K.Keys.Lost = false
		Local.Save(Owner, K)
		notify(Owner, `Your keys are back`, `{F.DisplayName} returned them.`, `Good`)
		Data.UpdateState(F, { type = `UpdateYen`; amount = Kit.Keys.Reward })
		Local.Push(F)
		return true, `Returned. The Office pays you \u{A5}{Kit.Keys.Reward}.`
	end
	Local.Push(F)
	return true, `They had a new set cut already. No reward.`
end

function Shared.ReturnKeys(F: Player, To: any): (boolean, string?)
	local C = Carrying[F]
	if not C then return false, `You aren't carrying anyone's keys.` end
	local Owner = Players:GetPlayerByUserId(C.Owner)
	local A = F.Character and F.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	local B = Owner and Owner.Character and Owner.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	if not (Owner and A and B) or To ~= Owner.UserId then return false, `Find their owner.` end
	if (A.Position - B.Position).Magnitude > Kit.Keys.Range then return false, `Get closer.` end
	return Local.GiveBack(F)
end

function Shared.HandInKeys(F: Player): (boolean, string?)
	if not Carrying[F] then return false, `You aren't carrying anyone's keys.` end
	local Near = Local.NearShop(F, `Office`)
	if not Near then
		local Root = F.Character and F.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
		for _, Box in CollectionService:GetTagged(`NHLostFoundBox`) do
			local Pos = if Box:IsA(`BasePart`) then Box.Position elseif Box:IsA(`Model`) then Box:GetPivot().Position else nil
			if Root and Pos and (Pos - Root.Position).Magnitude <= 10 then Near = Box break end
		end
	end
	if not Near then return false, `Hand them in at the Office or a Lost & Found box.` end
	return Local.GiveBack(F)
end

---| stand-in counters for NH Combat Test |---

local STAND_IN = {
	{ Shop = `Sundries`; Offset = Vector3.new(0, 0, 0) };
	{ Shop = `Cafe`; Offset = Vector3.new(12, 0, 0) };
	{ Shop = `Office`; Offset = Vector3.new(24, 0, 0) };
	{ Shop = `Archive`; Offset = Vector3.new(36, 0, 0) };
}
function Local.StandInCounters(): boolean
	if #CollectionService:GetTagged(`NHKitShop`) > 0 then return true end
	if game.PlaceId ~= 98950102230473 then return true end   -- only NH Combat Test: the Map place tags its real counters
	local Spot = workspace:FindFirstChild(`NHKitCounters`, true)
	local Base = if Spot and Spot:IsA(`BasePart`) then Spot.CFrame else nil
	if not Base then
		local Stand = CollectionService:GetTagged(`NHConcession`)[1]
		local At = Stand and (if Stand:IsA(`Model`) then Stand:GetPivot() elseif Stand:IsA(`BasePart`) then Stand.CFrame else nil)
		if not At then return false end
		-- a row 26 studs along from the snack stand, standing on the floor there
		local Flat = CFrame.new(At.Position) * CFrame.fromEulerAnglesYXZ(0, select(2, At:ToEulerAnglesYXZ()), 0)
		local Spot = (Flat * CFrame.new(-18, 0, -26)).Position
		RayParams.FilterDescendantsInstances = { workspace:FindFirstChild(`Live`) or workspace.Terrain }
		local Hit = workspace:Raycast(Spot + Vector3.new(0, 20, 0), Vector3.new(0, -80, 0), RayParams)
		Base = Flat.Rotation + (if Hit then Hit.Position else Spot - Vector3.new(0, 4, 0))
	end
	local Folder = Instance.new(`Folder`)
	Folder.Name = `NHKitCountersStandIn`
	Folder:SetAttribute(`NHStandIn`, true)
	for _, S in STAND_IN do
		local Def = Kit.Shops[S.Shop]
		local M = Instance.new(`Model`)
		M.Name = `Counter{S.Shop}`
		local Top = Instance.new(`Part`)
		Top.Name = `Counter`
		Top.Anchored = true
		Top.Size = Vector3.new(8, 3.4, 2.6)
		Top.CFrame = Base * CFrame.new(S.Offset) * CFrame.new(0, 1.7, 0)
		Top.Color = Color3.fromRGB(56, 20, 26)
		Top.Material = Enum.Material.Marble
		Top.Parent = M
		local Sign = Instance.new(`Part`)
		Sign.Name = `Sign`
		Sign.Anchored = true
		Sign.CanCollide = false
		Sign.Size = Vector3.new(7, 1.4, 0.2)
		Sign.CFrame = Top.CFrame * CFrame.new(0, 3.6, 0.6)
		Sign.Color = Color3.fromRGB(24, 20, 24)
		Sign.Parent = M
		local G = Instance.new(`SurfaceGui`)
		G.Face = Enum.NormalId.Front
		G.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
		G.PixelsPerStud = 60
		local L = Instance.new(`TextLabel`)
		L.BackgroundTransparency = 1
		L.Size = UDim2.fromScale(1, 1)
		L.Font = Enum.Font.Fantasy
		L.TextScaled = true
		L.TextColor3 = Color3.fromRGB(226, 190, 120)
		L.Text = Def.Name
		L.Parent = G
		G.Parent = Sign
		local Pr = Instance.new(`ProximityPrompt`)
		Pr.Name = `NHKitShopPrompt`
		Pr.ActionText = if S.Shop == `Archive` then `Borrowing desk` else `Browse`
		Pr.ObjectText = Def.Name
		Pr.HoldDuration = 0.2
		Pr.MaxActivationDistance = 9
		Pr.RequiresLineOfSight = false
		Pr:SetAttribute(`NHKitShop`, S.Shop)
		Pr.Parent = Top
		M:SetAttribute(`Shop`, S.Shop)
		M.PrimaryPart = Top
		CollectionService:AddTag(M, `NHKitShop`)
		M.Parent = Folder
	end
	Folder.Parent = workspace
	return true
end

-- every tagged counter gets the browse prompt (the Map place's real counters too)
function Local.Prompt(S: Instance)
	local Part = if S:IsA(`BasePart`) then S elseif S:IsA(`Model`) then (S.PrimaryPart or S:FindFirstChildWhichIsA(`BasePart`, true)) else nil
	if not Part or Part:FindFirstChild(`NHKitShopPrompt`) then return end
	local Shop = S:GetAttribute(`Shop`)
	local Def = Kit.Shops[Shop]
	if not Def then return end
	local Pr = Instance.new(`ProximityPrompt`)
	Pr.Name = `NHKitShopPrompt`
	Pr.ActionText = if Shop == `Archive` then `Borrowing desk` else `Browse`
	Pr.ObjectText = Def.Name
	Pr.HoldDuration = 0.2
	Pr.MaxActivationDistance = 9
	Pr.RequiresLineOfSight = false
	Pr:SetAttribute(`NHKitShop`, Shop)
	Pr.Parent = Part
end

---| Studio-only test hook (runs in this module instance) |---

function Local.TestHook()
	if not RunService:IsStudio() then return end
	local B = ServerStorage:FindFirstChild(`NHKitTest`) or Instance.new(`BindableFunction`)
	B.Name = `NHKitTest`
	B.OnInvoke = function(Cmd, Name, ...)
		local P = if Name then Players:FindFirstChild(Name) else Players:GetPlayers()[1]
		if Cmd == `State` then return P and Shared.State(P) end
		if Cmd == `Grant` then return P and Shared.Grant(P, ...) end
		if Cmd == `Use` then return P and table.pack(Shared.Use(P, ...)) end
		if Cmd == `Act` then return P and table.pack(Local.Act(P, ...)) end
		if Cmd == `Rain` then if ... then Shared.StartRain(...) else workspace:SetAttribute(`NHRain`, nil) end return workspace:GetAttribute(`NHRain`) end
		if Cmd == `DropKeys` then Local.DropKeys(P) return Shared.HasKeys(P) end
		if Cmd == `PickUp` then local F, O = ... local D = Dropped[O] if D then Local.PickUpKeys(Players:FindFirstChild(F) or P, O, D.Set) end return Carrying[Players:FindFirstChild(F) or P] ~= nil end
		if Cmd == `Indoors` then return P and Shared.IsIndoors(P), P and P.Character and Shared.RegionAt(P.Character.Head.Position) end
		if Cmd == `SetKit` then local K = Shared.Get(P) for Key, V in (... or {}) do K[Key] = V end Local.Save(P, K) return Shared.Get(P) end
		if Cmd == `Effects` then return P and Shared.Effects(P), P and Shared.LessonBonus(P, ...) end
		if Cmd == `Reset` then Inventory().SetKit(P, Kit.Sanitize({})) Local.Starter(P) return Shared.Get(P) end
		return `unknown`
	end
	B.Parent = ServerStorage
end

---| remotes |---

function Local.Act(P: Player, Action: any, A: any, B: any): (boolean, string?)
	if Action == `Buy` then return Shared.Buy(P, A)
	elseif Action == `Refill` then return Shared.Refill(P, A)
	elseif Action == `Pin` then return Shared.Pin(P, A, B == true)
	elseif Action == `Use` then -- (inventory audit 1.90) only pocket items are used from the Locker; the rest from the hand
		local It = typeof(A) == `string` and Kit.ById[A]
		if not (It and It.Pocket) then return false, nil end
		return Shared.Use(P, A)
	elseif Action == `Borrow` then return Shared.Borrow(P, A)
	elseif Action == `Return` then return Shared.Return(P)
	elseif Action == `PayFine` then return Shared.PayFine(P)
	elseif Action == `ReturnKeys` or Action == `HandInKeys` then
		local Ok, Msg = if Action == `ReturnKeys` then Shared.ReturnKeys(P, A) else Shared.HandInKeys(P)
		if Msg then notify(P, Msg) end
		return Ok, Msg
	end
	return false, nil
end

function Shared.OnStart()
	local F = Instance.new(`Folder`)
	F.Name = `NHKit`
	local Get = Instance.new(`RemoteFunction`) Get.Name = `Get` Get.Parent = F
	local Act = Instance.new(`RemoteFunction`) Act.Name = `Act` Act.Parent = F
	local Changed = Instance.new(`RemoteEvent`) Changed.Name = `Changed` Changed.Parent = F
	local Old = ReplicatedStorage:FindFirstChild(`NHKit`)
	if Old then
		-- keep the models folder (it holds the imported meshes)
		local Models = Old:FindFirstChild(`Models`)
		if Models then Models.Parent = F end
		Old:Destroy()
	end
	Remotes = { Changed = Changed }
	Get.OnServerInvoke = function(P) return Shared.State(P) end
	Act.OnServerInvoke = function(P, Action, A, B)
		local T = os.clock()
		if LastCall[P] and T - LastCall[P] < 0.15 then return false, `One moment...` end
		LastCall[P] = T
		local Ok, R1, R2 = pcall(Local.Act, P, Action, A, B)
		if not Ok then warn(`[Kit] {R1}`) return false, nil end
		return R1, R2
	end
	F:SetAttribute(`Ready`, true)
	F.Parent = ReplicatedStorage

	local function onPlayer(P: Player)
		P.CharacterAdded:Connect(function(Char)
			Lit[P] = nil
			Busy[P] = nil
			Chill[P] = nil
			task.defer(function()
				P:WaitForChild(`Backpack`, 10)
				Char:WaitForChild(`Left Leg`, 10)
				task.wait(0.6)
				local K = Shared.Get(P)
				if K then Local.SyncTools(P, K) end
			end)
		end)
	end
	Players.PlayerAdded:Connect(onPlayer)
	for _, P in Players:GetPlayers() do onPlayer(P) end
	Data.ProfileLoaded:Connect(function(P)
		task.defer(function()
			Local.Starter(P)
			local K = Shared.Get(P)
			if K then Local.SyncTools(P, K) end
			Local.Push(P)
		end)
	end)
	for _, P in Players:GetPlayers() do
		task.defer(function() if Data.GetProfile(P) then Local.Starter(P) local K = Shared.Get(P) if K then Local.SyncTools(P, K) end end end)
	end
	Players.PlayerRemoving:Connect(function(P)
		if Dirty[P] then pcall(function() local K = Shared.Get(P) if K then Inventory().SetKit(P, K, true) end end) end
		LastCall[P], Busy[P], Cool[P], Lit[P], Chill[P], Dirty[P], Carrying[P] = nil, nil, nil, nil, nil, nil, nil
		-- (inventory audit 1.90) the leaver's keys on the ground go with them
		local D = Dropped[P.UserId]
		if D then if D.Model.Parent then D.Model:Destroy() end Dropped[P.UserId] = nil end
	end)

	-- lost keys: being downed by another student (Features.Downed.OnDowned(Target, Attacker))
	pcall(function()
		local Downed = require(ServerScriptService.Services.Features.Downed)
		Downed.OnDowned:Connect(function(Target, Attacker)
			local P = Target and Players:GetPlayerFromCharacter(Target)
			local A = Attacker and Players:GetPlayerFromCharacter(Attacker)
			if P and A and P ~= A and math.random() < Kit.Keys.DropChance then pcall(Local.DropKeys, P) end
			-- a finder who goes down drops the keys they carry (lost for good: the owner gets a new set cut)
			if P and Carrying[P] then Carrying[P] = nil P:SetAttribute(`NHKitKeys`, nil) end
		end)
	end)

	for _, S in CollectionService:GetTagged(`NHKitShop`) do Local.Prompt(S) end
	CollectionService:GetInstanceAddedSignal(`NHKitShop`):Connect(Local.Prompt)
	task.spawn(function()   -- the snack stand is built from the greybox a little after start
		for _ = 1, 30 do
			task.wait(2)
			local Ok, Done = pcall(Local.StandInCounters)
			if Ok and Done then break end
		end
	end)
	Local.TestHook()

	task.spawn(function()
		local Last = os.clock()
		while true do
			task.wait(1)
			local T = os.clock()
			local Dt = math.min(3, T - Last)
			Last = T
			local Ok, Err = pcall(Local.Tick, Dt)
			if not Ok then warn(`[Kit] tick: {Err}`) end
			pcall(Local.RainTick)
			for Owner, D in Dropped do
				if os.clock() - D.At > Kit.Keys.Lifetime then if D.Model.Parent then D.Model:Destroy() end Dropped[Owner] = nil end
			end
		end
	end)
end

return Shared
