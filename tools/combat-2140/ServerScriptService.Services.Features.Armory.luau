--[[
	Armory (server). Services.Features.Armory                                  (owner, 2026-11-12)
	"I want all students to start off with the Fist class then can buy a katana from the armory shop keeper."
	Config: ReplicatedStorage.Config.Armory (stock, prices, the save, the Fist migration). Client: Controllers.Gui.ArmoryUi.

	  Shopkeeper  an anchored NPC (the AI rig, dressed by UI.Appearance) stands on every part tagged NHArmoryKeeper,
	              facing the part's front. Its prompt (attribute NHArmoryShop) opens the armoury window.
	  Counters    anything tagged NHArmoryShop (the keeper, the counter) is where you can buy: within Config.Armory.Range.
	  Buying      a class you don't own, for Yen (PlayerData.Armory.Owned). You switch to it at a class locker
	              (Features.ClassLocker), which only offers the classes you own.
	Remotes: ReplicatedStorage.NHArmory (Ready attribute)
		Info (RF)          -> { Yen, Weapon, Shop, Items = { { Class, Name, Price, Text, Owned, Locked } } }
		Buy  (RF, class)   -> ok, message
		Gear (RF, action, id) (2.14.0, combat concept 16) -> ok, message. Actions: Buy, Wear, Remove.
	Hand gear (Config.Armory.Gear): bought for Yen, one worn at a time (PlayerData.Armory.Gear). The worn piece is the
	character attribute NHGear (its effects: ServerStorage.Packages.HandGear) and its mesh on both hands. A hall monitor
	who sees you fight in brass knuckles takes them (Shared.Confiscate, from Services.School.HallMonitor).
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local CollectionService = game:GetService(`CollectionService`)

local Data = require(ServerScriptService.Services.Player.Data)
local Armory = require(ReplicatedStorage.Config.Armory)
local HandGear = require(game:GetService(`ServerStorage`).Packages.HandGear) -- (2.14.0)

local Shared = {}
local Local = {}
local Keepers: Folder? = nil

function Local.Pos(I: Instance): Vector3?
	if I:IsA(`BasePart`) then return I.Position end
	if I:IsA(`Model`) then return I:GetPivot().Position end
	return nil
end

function Shared.Near(P: Player): boolean
	local Root = P.Character and P.Character:FindFirstChild(`HumanoidRootPart`)
	if not Root then return false end
	for _, I in CollectionService:GetTagged(`NHArmoryShop`) do
		local Pos = Local.Pos(I)
		if Pos and (Pos - Root.Position).Magnitude <= Armory.Range then return true end
	end
	return false
end

function Local.Info(P: Player)
	local Profile = Data.GetProfile(P)
	local Items = {}
	table.insert(Items, { Class = Armory.Default; Name = `Fists`; Price = 0; Text = `Every student's first class. Fast blunt combos, grabs and a launching kick.`; Owned = true })
	for _, S in Armory.Stock do
		table.insert(Items, { Class = S.Class; Name = S.Name; Price = S.Price; Text = S.Text; Owned = Armory.Owns(Profile, S.Class) })
	end
	for Class, Why in Armory.Locked do
		local Owned = Armory.Owns(Profile, Class)
		table.insert(Items, { Class = Class; Name = Class; Text = if Owned then `Yours.` else Why; Owned = Owned; Locked = not Owned })
	end
	-- (2.14.0) hand gear
	local Gear = {}
	local Worn = Armory.WornGear(Profile)
	for _, G in Armory.Gear do
		table.insert(Gear, { Id = G.Id; Name = G.Name; Price = G.Price; Text = G.Text; Icon = G.Icon; Contraband = G.Contraband;
			Owned = Armory.OwnsGear(Profile, G.Id); Worn = Worn == G.Id })
	end
	return { Yen = Profile and Profile.Yen or 0; Weapon = Profile and Profile.Weapon; Shop = Armory.Shop; Items = Items; Gear = Gear; Loaded = Profile ~= nil }
end

---| hand gear (2.14.0, combat concept 16) |---

-- the worn piece onto the character: the NHGear attribute (the effects) and the mesh on both hands
function Shared.SyncGear(P: Player)
	local C = P.Character
	if not C then return end
	local Worn = Armory.WornGear(Data.GetProfile(P))
	if C:GetAttribute(`NHGear`) == Worn and (Worn == nil or C:FindFirstChild(`NHGear_` .. Worn)) then return end
	C:SetAttribute(`NHGear`, Worn)
	pcall(HandGear.Dress, C, Worn)
end

function Shared.Gear(P: Player, Action: any, Id: any): (boolean, string)
	local G = typeof(Id) == `string` and Armory.GearById[Id]
	if not G then return false, `That isn't sold here.` end
	local Profile = Data.GetProfile(P)
	if not Profile then return false, `Your record isn't loaded yet.` end
	if Action == `Buy` then
		if Armory.OwnsGear(Profile, G.Id) then return false, `You already own the {G.Name}.` end
		if not Shared.Near(P) then return false, `Buy it at the armory.` end
		local Price = math.max(0, math.floor(tonumber(G.Price) or 0))
		if (tonumber(Profile.Yen) or 0) < Price then return false, `Not enough Yen. The {G.Name} cost \u{A5}{Price}.` end
		if Price > 0 then Data.UpdateState(P, { type = `UpdateYen`; amount = -Price }) end
		Armory.GrantGear(Profile, G.Id)
		Armory.WearGear(Profile, G.Id) -- straight on
		Shared.SyncGear(P)
		return true, `The {G.Name} are yours, and on your hands.`
	elseif Action == `Wear` then
		if not Armory.OwnsGear(Profile, G.Id) then return false, `You don't own the {G.Name}.` end
		Armory.WearGear(Profile, G.Id)
		Shared.SyncGear(P)
		return true, `{G.Name} on.`
	elseif Action == `Remove` then
		if Armory.WornGear(Profile) == G.Id then Armory.WearGear(Profile, nil) end
		Shared.SyncGear(P)
		return true, `{G.Name} off.`
	end
	return false, `Something went wrong.`
end

-- contraband taken by a hall monitor: gone from the save and off the hands. True when there was something to take.
function Shared.Confiscate(P: Player, Id: string): boolean
	local Profile = Data.GetProfile(P)
	if not (Profile and Armory.OwnsGear(Profile, Id)) then return false end
	Armory.TakeGear(Profile, Id)
	Shared.SyncGear(P)
	return true
end

function Shared.Buy(P: Player, Class: any): (boolean, string)
	local S = typeof(Class) == `string` and Armory.ByClass[Class]
	if not S then return false, `That isn't sold here.` end
	local Profile = Data.GetProfile(P)
	if not Profile then return false, `Your record isn't loaded yet.` end
	if Armory.Owns(Profile, S.Class) then return false, `You already own the {S.Name}.` end
	if not Shared.Near(P) then return false, `Buy it at the armory.` end
	local Price = math.max(0, math.floor(tonumber(S.Price) or 0))
	if (tonumber(Profile.Yen) or 0) < Price then return false, `Not enough Yen. The {S.Name} costs \u{A5}{Price}.` end
	if Price > 0 then Data.UpdateState(P, { type = `UpdateYen`; amount = -Price }) end
	Armory.Grant(Profile, S.Class)
	return true, `The {S.Name} is yours. Switch to it at a class locker.`
end

---| the shopkeeper |---

function Local.Keeper(Spot: Instance)
	if not (Spot:IsA(`BasePart`) and Spot:IsDescendantOf(workspace)) or Spot:GetAttribute(`NHKeeperUp`) then return end
	-- the AI rig (NH Combat Test); where it's only a stub (the Map), a plain R6 body
	local AIFolder = ServerScriptService.Services:FindFirstChild(`AI`) and ServerScriptService.Services.AI:FindFirstChild(`AI`)
	local Rig = AIFolder and AIFolder:FindFirstChild(`Rig`)
	if not (Rig and Rig:FindFirstChildWhichIsA(`Humanoid`) and Rig:FindFirstChild(`HumanoidRootPart`)) then
		local Ok, Made = pcall(function() return Players:CreateHumanoidModelFromDescription(Instance.new(`HumanoidDescription`), Enum.HumanoidRigType.R6) end)
		Rig = if Ok then Made else nil
	end
	if not Rig then warn(`[Armory] no rig for the shopkeeper`) return end
	Spot:SetAttribute(`NHKeeperUp`, true)
	Spot.Transparency = 1
	Spot.CanCollide = false
	Spot.CanQuery = false
	Spot.CanTouch = false
	local Model = Rig:Clone()
	Model.Name = Spot:GetAttribute(`KeeperName`) or `Armourer`
	Model:SetAttribute(`Role`, `Ambient`)
	Model:SetAttribute(`NHShopkeeper`, `Armory`)
	for _, D in Model:GetDescendants() do
		if D:IsA(`Script`) or D:IsA(`LocalScript`) then D:Destroy() end
	end
	local Hum = Model:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	local Root = Model:FindFirstChild(`HumanoidRootPart`) :: BasePart
	if not (Hum and Root) then return end
	Hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	Hum.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
	Hum.BreakJointsOnDeath = false
	Hum:SetStateEnabled(Enum.HumanoidStateType.Dead, false)
	-- feet on the spot's floor (the spot's bottom face), facing the spot's front
	local Floor = Spot.Position - Vector3.new(0, Spot.Size.Y / 2, 0)
	local Up = Root.Size.Y / 2 + Hum.HipHeight + (Model:FindFirstChild(`Left Leg`) and Model[`Left Leg`].Size.Y or 2)
	local Look = Spot.CFrame.LookVector * Vector3.new(1, 0, 1)
	if Look.Magnitude < 1e-3 then Look = Vector3.new(0, 0, -1) end
	local Want = CFrame.lookAt(Floor + Vector3.new(0, Up, 0), Floor + Vector3.new(0, Up, 0) + Look.Unit)
	Model:PivotTo(Want * Root.CFrame:Inverse() * Model:GetPivot())
	for _, D in Model:GetDescendants() do if D:IsA(`BasePart`) then D.Anchored = true end end
	Model.Parent = Keepers
	-- the armourer's look: a seeded skin and haircut, clothes picked by UI.Appearance
	pcall(function()
		local Appearance = require(ReplicatedStorage.UI.Appearance)
		local R = Random.new(Spot:GetAttribute(`KeeperSeed`) or 1846)
		local L = Appearance.Sanitize(nil)
		L.UseAvatar = false
		L.Body = 1
		L.Skin = R:NextInteger(1, #Appearance.Skins)
		L.HairColor = 1
		L.Uniform = Appearance.RandomPiece(Appearance.Uniforms, L)
		L.Bottoms = Appearance.RandomPiece(Appearance.BottomsList, L)
		local Cat = ReplicatedStorage:FindFirstChild(`NHHairCatalog`)
		if Cat then
			local Pool = {}
			for _, H in Cat:GetChildren() do if H:GetAttribute(`Group`) == `Male` then table.insert(Pool, H:GetAttribute(`AssetId`)) end end
			table.sort(Pool, function(A, B) return tostring(A) < tostring(B) end)
			if #Pool > 0 then L.HairId = Pool[R:NextInteger(1, #Pool)] end
		end
		Appearance.ApplyTo(Model, L)
	end)
	for _, D in Model:GetDescendants() do if D:IsA(`BasePart`) then D.Anchored = true end end
	local Pr = Instance.new(`ProximityPrompt`)
	Pr.Name = `NHArmoryPrompt`
	Pr.ActionText = `Browse`
	Pr.ObjectText = Model.Name
	Pr.HoldDuration = 0.2
	Pr.MaxActivationDistance = 10
	Pr.RequiresLineOfSight = false
	Pr:SetAttribute(`NHArmoryShop`, true)
	Pr.Parent = Root
	CollectionService:AddTag(Root, `NHArmoryShop`)
end

---| Studio-only test hook (runs in this module instance, so it sees the real profiles) |---
-- ServerStorage.NHArmoryTest:Invoke(cmd, playerName, ...)
--   State             -> { Weapon, Owned, Yen, V }
--   Yen, n            -> adds n Yen (n may be negative) through Data.UpdateState
function Local.TestHook()
	if not game:GetService(`RunService`):IsStudio() then return end
	local B = game:GetService(`ServerStorage`):FindFirstChild(`NHArmoryTest`) or Instance.new(`BindableFunction`)
	B.Name = `NHArmoryTest`
	B.OnInvoke = function(Cmd, Name, A)
		local P = if Name then Players:FindFirstChild(Name) else Players:GetPlayers()[1]
		local Profile = P and Data.GetProfile(P)
		if not Profile then return nil end
		if Cmd == `Yen` and typeof(A) == `number` then Data.UpdateState(P, { type = `UpdateYen`; amount = math.floor(A) }) end
		if Cmd == `Confiscate` and typeof(A) == `string` then Shared.Confiscate(P, A) end -- (2.14.0) what a hall monitor does
		-- (2.14.0) Gear, id: owns and wears it (nil id: takes the worn one off)
		if Cmd == `Gear` then
			if typeof(A) == `string` then Armory.GrantGear(Profile, A) end
			Armory.WearGear(Profile, if typeof(A) == `string` then A else nil)
			Shared.SyncGear(P)
		end
		local Owned = {}
		for K, V in (Profile.Armory and Profile.Armory.Owned) or {} do if V then table.insert(Owned, K) end end
		return { Weapon = Profile.Weapon; Owned = Owned; Yen = Profile.Yen; V = Profile.Armory and Profile.Armory.V; Gear = Armory.WornGear(Profile) }
	end
	B.Parent = game:GetService(`ServerStorage`)
end

---| start |---

function Shared.OnStart()
	local F = ReplicatedStorage:FindFirstChild(`NHArmory`) or Instance.new(`Folder`)
	F.Name = `NHArmory`
	local Info = F:FindFirstChild(`Info`) or Instance.new(`RemoteFunction`); Info.Name = `Info`; Info.Parent = F
	local Buy = F:FindFirstChild(`Buy`) or Instance.new(`RemoteFunction`); Buy.Name = `Buy`; Buy.Parent = F
	local GearRF = F:FindFirstChild(`Gear`) or Instance.new(`RemoteFunction`); GearRF.Name = `Gear`; GearRF.Parent = F -- (2.14.0)
	F.Parent = ReplicatedStorage

	Info.OnServerInvoke = function(P) return Local.Info(P) end
	local Busy = {}
	Buy.OnServerInvoke = function(P, Class)
		if Busy[P] then return false, `One moment...` end
		Busy[P] = true
		local Ok, A, B = pcall(Shared.Buy, P, Class)
		Busy[P] = nil
		if not Ok then warn(`[Armory] {A}`) return false, `Something went wrong.` end
		return A, B
	end
	GearRF.OnServerInvoke = function(P, Action, Id) -- (2.14.0) hand gear
		if Busy[P] then return false, `One moment...` end
		Busy[P] = true
		local Ok, A, B = pcall(Shared.Gear, P, Action, Id)
		Busy[P] = nil
		if not Ok then warn(`[Armory] {A}`) return false, `Something went wrong.` end
		return A, B
	end
	Players.PlayerRemoving:Connect(function(P) Busy[P] = nil end)
	-- (2.14.0) the worn hand gear back on every spawn (once the record has loaded)
	local function Watch(P: Player)
		P.CharacterAdded:Connect(function()
			task.spawn(function()
				for _ = 1, 60 do
					if Data.GetProfile(P) then break end
					task.wait(0.5)
				end
				task.wait(0.5)
				Shared.SyncGear(P)
			end)
		end)
		if P.Character then task.spawn(Shared.SyncGear, P) end
	end
	Players.PlayerAdded:Connect(Watch)
	for _, P in Players:GetPlayers() do Watch(P) end
	F:SetAttribute(`Ready`, true)
	Local.TestHook()

	Keepers = workspace:FindFirstChild(`NHShopkeepers`) or Instance.new(`Folder`)
	Keepers.Name = `NHShopkeepers`
	Keepers.Parent = workspace
	for _, S in CollectionService:GetTagged(`NHArmoryKeeper`) do task.spawn(Local.Keeper, S) end
	CollectionService:GetInstanceAddedSignal(`NHArmoryKeeper`):Connect(function(S) task.spawn(Local.Keeper, S) end)
end

return Shared
