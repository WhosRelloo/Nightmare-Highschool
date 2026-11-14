
---| Services |---

local Players = game:GetService(`Players`)
local ServerScriptService = game:GetService(`ServerScriptService`)

local ServerStorage = game:GetService(`ServerStorage`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

---| Modules |---

local DataService = require(ServerScriptService.Services.Player.Data)
local PlayerDataConfig = require(ReplicatedStorage.PlayerData)

local LinearVelocity = require(ReplicatedStorage.Functions.LinearVelocity)
local GameConfig = require(ServerScriptService.Services.Studio.Game)

local WeaponsConfig = require(ReplicatedStorage.Config.Weapons)
local AirCombat = require(ServerStorage.Packages.AirCombat)
local Trove = require(ReplicatedStorage.Packages.Trove)

---| Entity |---

local EntityData = { } :: { [Model]: PlayerDataConfig.PlayerData & { Connection: RBXScriptConnection } }
local CharacterTroves = {} :: { [Model]: typeof(Trove.new()) }

local Local = {}
Local.DescriptionCache = {} :: { [number]: HumanoidDescription } -- fallback NPC look (EntityLoader.OnCharacterAdded)
local Shared = {}

function Shared.OnStart()

	-- every player, including anyone who joined before this service started, gets CharacterAdded
	-- (Known bug #10: early joiners only had their first character set up, never their respawns)
	local function Hook(Player: Player)
		Player.CharacterAdded:Connect(Shared.OnCharacterAdded)
	end
	Players.PlayerAdded:Connect(Hook)

	for _, Player in Players:GetPlayers() do
		Hook(Player)
		if not Player.Character then continue end
		Shared.OnCharacterAdded(Player.Character)

	end

end

--| Apperance & Info |--

function Shared.OnCharacterAdded(Character: GameConfig.R6)
	local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	local RootPart = Humanoid.RootPart :: BasePart

	Character.PrimaryPart = RootPart
	Character.Parent = workspace.Live

	local Player = Players:GetPlayerFromCharacter(Character)
	local IsNPC = not Player
	local CollisionGroup = IsNPC and `NPC` or `Entity`

	for _, BasePart: BasePart in Character:GetDescendants() do
		if BasePart:IsA("BasePart") then 
			BasePart.CollisionGroup = CollisionGroup

			if BasePart.Name == `Handle` then
				BasePart.Massless = true

			end

		end
	end

	if Character:FindFirstChild('Health') and Character:FindFirstChild('Health'):IsA(`Script`) then
		Character.Health:Destroy()

	end

	Humanoid:SetAttribute(`Equip`, false)
	LinearVelocity.Register(Character)

	Player = Player or { UserId = 3585755651 }

	-- one web call per user id (every NPC used to make its own, unprotected, with the same fallback id)
	local PlayerDescription = Local.DescriptionCache[Player.UserId]
	if not PlayerDescription then
		local Ok, Desc = pcall(function() return Players:GetHumanoidDescriptionFromUserId(Player.UserId) end)
		PlayerDescription = if Ok and Desc then Desc else Instance.new(`HumanoidDescription`)
		if Ok and Desc and not Players:GetPlayerByUserId(Player.UserId) then Local.DescriptionCache[Player.UserId] = Desc end
	end
	local HumanoidDescription = Character.Humanoid.HumanoidDescription

	for _, Description in GameConfig.WhiteListDescription do
		if not PlayerDescription[Description] then
			continue
		end

		HumanoidDescription[Description] = PlayerDescription[Description]
	end

	Local.EnsureFodlers(Character, GameConfig.FolderStructer);
	-- (audit) the web call above yields; a character replaced meanwhile (menu stage -> school) made this throw
	-- "DataModel was not available"
	if not Character:IsDescendantOf(workspace) then return end
	Humanoid:ApplyDescriptionReset(HumanoidDescription)
	-- (height) the body is rebuilt: Services.Player.Height may scale it now (scaling earlier would be undone)
	Character:SetAttribute(`NHDescribed`, true)

	local Data = Shared.GetProfile(Character)
	if not Data then return end 

	Shared.SetWeapon(Character, Data)


	if Character.Name == `Attacking` or Character.Name == `Aerial Critical` or Character.Name == `Aerial M1 Dummy` or Character.Name == `Running Attack Dummy` or Character.Name == `Katana Critical Dummy` then
		Humanoid:SetAttribute(`Equip`, true)

		local Config = WeaponsConfig[Data.Weapon]
		if Config and Config.Model and Config.Model.Handle then
			local Accessory = Character:FindFirstChild(`Accessory`)
			if Accessory then
				local Weapons = Accessory:FindFirstChild(`Weapons`)
				if Weapons then
					for _, Weapon: BasePart in Weapons:GetChildren() do
						Weapon:Destroy()
					end

					local WeaponModel = Config.Model.Handle:Clone()
					WeaponModel.Parent = Weapons

					local GripLocation = Character:FindFirstChild(Config.Model.Grip) :: BasePart
					if GripLocation then
						(WeaponModel :: Model & { Handle: Motor6D } ).Handle.Part1 = GripLocation
					end
				end
			end
		end
	end
	Humanoid.BreakJointsOnDeath = false

	local characterTrove = Trove.new()
	CharacterTroves[Character] = characterTrove

	characterTrove:Connect(Humanoid.Died, function()
		AirCombat.StopCharacter(Character)
	end)

	characterTrove:Connect(Character.AncestryChanged, function(_, Parent)
		if not Parent then
			AirCombat.StopCharacter(Character)
			if CharacterTroves[Character] then
				CharacterTroves[Character]:Destroy()
				CharacterTroves[Character] = nil
			end
		end
	end)
end

function Shared.GetProfile(Character: Model): DataService.PlayerData
	local Data: DataService.PlayerData
	local Player = Players:GetPlayerFromCharacter(Character)

	if Player then
		local StartTime = os.clock()
		local attempts = 0
		local maxAttempts = 200

		while Data == nil and os.clock() - StartTime < 20 and attempts < maxAttempts do
			Data = DataService.GetProfile(Player)
			if Data then break end
			attempts += 1
			task.wait(.1)
		end

		if not Data then
			warn(`[EntityLoader] Failed to get profile for {Player.Name} after {attempts} attempts`)
		end

	else
		if EntityData[Character] then
			return EntityData[Character]
		end

		local clonedData = table.clone(PlayerDataConfig.DEFAULT_PLAYER_DATA)
		clonedData.Weapon = `Katana` -- (armory) students now start on Fist; NPCs and dummies keep their old Katana default

		if Character.Name == "Blocking" then
			clonedData.Weapon = `Katana`

		end
		if Character.Name == `ParryTrade` then
			clonedData.Weapon = `Katana`
		end

		if Character.Name == `Attacking` or Character.Name == `KatanaCritical` or Character.Name == `Aerial M1 Dummy` or Character.Name == `Running Attack Dummy` or Character.Name == `Katana Critical Dummy` then
			clonedData.Weapon = `Katana`
		end

		local connection = Character.AncestryChanged:Connect(function(Child: Instance, Parent: Instance)
			if Parent then
				return
			end

			if EntityData[Character] and EntityData[Character].Connection then
				EntityData[Character].Connection:Disconnect()
				EntityData[Character].Connection = nil
			end
			EntityData[Character] = nil
		end)

		clonedData.Connection = connection
		EntityData[Character] = clonedData
		Data = clonedData
	end

	return Data
end

-- (height) weapons are built for today's body: a student scaled to their height is put back to the base size while
-- the weapon is attached, then scaled back (Services.Player.Height), so a weapon swapped mid-game fits too
function Shared.SetWeapon(Character: Model, Data: DataService.PlayerData)
	local Base = require(ReplicatedStorage.Config.Heights).Base
	local Heights = require(ReplicatedStorage.Config.Heights)
	local Ok, Now = pcall(function() return Character:GetScale() end)
	-- (1.70.0) a height also stretches the torso, legs and arms: the weapon is attached to the even base body too
	local St, Sl, Sa = Heights.StretchOf(Character)
	local Stretched = math.abs(St - 1) > 1e-4 or math.abs(Sl - 1) > 1e-4 or math.abs(Sa - 1) > 1e-4
	if not Ok or (math.abs(Now - Base) < 1e-3 and not Stretched) then return Local.SetWeaponRaw(Character, Data) end
	local Height = require(ServerScriptService.Services.Player.Height)
	if Stretched then Heights.SetStretch(Character, 1, 1, 1) end
	Height.ScaleKeep(Character, Base)
	local Done, Err = pcall(Local.SetWeaponRaw, Character, Data)
	if Character.Parent then
		Height.ScaleKeep(Character, Now)
		if Stretched then Heights.SetStretch(Character, St, Sl, Sa) end
	end
	if not Done then warn(`[EntityLoader] SetWeapon: {Err}`) end
end

function Local.SetWeaponRaw(Character: Model, Data: DataService.PlayerData)
	local Weapon = Data.Weapon
	local Config = WeaponsConfig[Weapon]

	if not Config then
		return
	end

	local Accessory = Character:FindFirstChild(`Accessory`)
	if not Accessory then
		Accessory = Instance.new(`Folder`)
		Accessory.Name = `Accessory`
		Accessory.Parent = Character
	end

	local Weapons = Accessory:FindFirstChild(`Weapons`)
	if not Weapons then
		Weapons = Instance.new(`Folder`)
		Weapons.Name = `Weapons`
		Weapons.Parent = Accessory
	end

	for _, Weapon: BasePart in Weapons:GetChildren() do
		Weapon:Destroy()
	end

	-- Claws: the claws stay on the forearms (no sheath), so a Claws student starts equipped
	if Weapon == `Claws` then
		local ClawKit = require(ReplicatedStorage.Functions.ClawKit)
		ClawKit.Attach(Character)
		local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		Humanoid:SetAttribute(`Equip`, true)
		Character:SetAttribute(`Weapon`, Weapon)
		local Player = Players:GetPlayerFromCharacter(Character)
		if Player then
			-- tell the client once its controllers are up (equip stance + claws movement pack)
			task.delay(2, function()
				if Character.Parent and Humanoid:GetAttribute(`Equip`) then
					pcall(function() require(ReplicatedStorage.Remotes.Packets).Replicate:FireClient(Player, `Misc`, `Equip`, { State = true }) end)
				end
			end)
		end
		return
	end

	local WeaponModel = Config.Model
	if not WeaponModel or not WeaponModel.Back then return end 

	WeaponModel = WeaponModel.Back:Clone()
	WeaponModel.Parent = Weapons

	local Torso = Character:FindFirstChild(`Torso`) :: BasePart

	(WeaponModel :: Model & { Torso: Motor6D } ).Torso.Part1 =  Torso

	local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	Humanoid:SetAttribute(`Equip`, false)
end

function Local.EnsureFodlers(Parent: Instance, Structer: { [string]: any })

	for Name, Sub in pairs(Structer) do
		if typeof(Name) == `number` then
			Name, Sub = Sub, {}

		end

		local Folder = Parent:FindFirstChild(Name) :: Folder
		if not Folder or not Folder:IsA(`Folder`) then
			Folder = Instance.new(`Folder`, Parent)
			Folder.Name = Name


		end

		if typeof(Sub) == `table` then
			Local.EnsureFodlers(Folder, Sub)

		end

	end

end

return Shared
