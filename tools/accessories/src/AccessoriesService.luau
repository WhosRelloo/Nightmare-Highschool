--[[
	Accessories (server): the 3D accessory kits' shop side (Config.Accessories; wearing is UI.Appearance + UI.AccessoryWear).
	  * Kit A pieces with a Price are sold for Yen at the School Store (CollectionService tag NHSchoolStore, within 14
	    studs). A Clique piece is sold only to that clique's members (Social.CliqueMembership.Joined).
	  * Bought pieces are saved for good in Identity.Accessories (ProfileService through Data.UpdateState SetIdentity;
	    Yen through UpdateYen).
	  * Kit B (Admin = true, the Headmaster's Circle) is never sold or owned: staff wear it free (Appearance's look check).
	Remotes ReplicatedStorage.NHAccRemotes (attribute Ready): Info (RF) -> { Owned, Yen, Clique }, Buy (RF id) -> ok, msg.
	Cosmetic only: no stats, and nothing here reads or writes Race.
]]
local CollectionService = game:GetService(`CollectionService`)
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

local Data = require(ServerScriptService.Services.Player.Data)
local Identity = require(ServerScriptService.Services.Player.Identity)
local AccCfg = require(ReplicatedStorage.Config.Accessories)

local Shared = {}
local Local = {}
local REACH = 14

function Local.Clique(P: Player): string?
	local Ok, M = pcall(require, ServerScriptService.Services.Social.CliqueMembership)
	if not Ok or not M or not M.Joined then return nil end
	local Ok2, Id = pcall(M.Joined, P)
	return if Ok2 and typeof(Id) == `string` then Id else nil
end

function Local.NearStore(P: Player): boolean
	local Root = P.Character and P.Character:FindFirstChild(`HumanoidRootPart`)
	if not Root then return false end
	for _, S in CollectionService:GetTagged(`NHSchoolStore`) do
		local Pos = if S:IsA(`BasePart`) then S.Position elseif S:IsA(`Model`) then S:GetPivot().Position else nil
		if Pos and (Pos - Root.Position).Magnitude <= REACH then return true end
	end
	return false
end

function Shared.Owns(P: Player, Id: string): boolean
	local I = Identity.Get(P)
	return I ~= nil and table.find(I.Accessories or {}, Id) ~= nil
end

-- give a piece (rewards, quests); returns true if it was new
function Shared.Grant(P: Player, Id: string): boolean
	local It = AccCfg.ById[Id]
	local I = Identity.Get(P)
	if not (It and I) or It.Admin then return false end
	I.Accessories = I.Accessories or {}
	if table.find(I.Accessories, Id) then return false end
	table.insert(I.Accessories, Id)
	Data.UpdateState(P, { type = `SetIdentity`; identity = I })
	return true
end

function Shared.OnStart()
	local F = ReplicatedStorage:FindFirstChild(`NHAccRemotes`) or Instance.new(`Folder`)
	F.Name = `NHAccRemotes`
	local function rf(N)
		local R = F:FindFirstChild(N) or Instance.new(`RemoteFunction`)
		R.Name = N
		R.Parent = F
		return R
	end
	local Info, Buy = rf(`Info`), rf(`Buy`)
	F.Parent = ReplicatedStorage
	local Busy = {}
	Info.OnServerInvoke = function(P)
		local I = Identity.Get(P)
		local Profile = Data.GetProfile(P)
		return { Owned = (I and I.Accessories) or {}; Yen = Profile and Profile.Yen or 0; Clique = Local.Clique(P) }
	end
	Buy.OnServerInvoke = function(P, Id)
		if Busy[P] then return false, `One moment...` end
		local It = typeof(Id) == `string` and AccCfg.ById[Id]
		if not (It and It.Price) or It.Admin or not AccCfg.Ready(It) then return false, `Not sold here.` end
		if not Local.NearStore(P) then return false, `You're too far from the store.` end
		if It.Clique and Local.Clique(P) ~= It.Clique then return false, `Only members of that clique can buy it.` end
		if Shared.Owns(P, Id) then return false, `You already own it.` end
		local Profile = Data.GetProfile(P)
		if not Profile or (Profile.Yen or 0) < It.Price then return false, `Not enough Yen.` end
		Busy[P] = true
		local Ok, Err = pcall(function()
			Data.UpdateState(P, { type = `UpdateYen`; amount = -It.Price })
			Shared.Grant(P, Id)
		end)
		Busy[P] = nil
		if not Ok then warn(`[Accessories] buy failed: {Err}`) return false, `Something went wrong.` end
		return true, `Bought the {It.Name}. Wear it from a locker-room wardrobe.`
	end
	F:SetAttribute(`Ready`, true)
	Players.PlayerRemoving:Connect(function(P) Busy[P] = nil end)
	-- (1.79) a Held-slot piece (the Book Strap, hanging from the right hand) is hidden while a weapon or tool is in that
	-- hand: the drawn katana's grip and blade pass through it (measured against the katana by acc_check.py)
	local function watch(Ch: Model)
		local Hum = Ch:WaitForChild(`Humanoid`, 10)
		if not Hum then return end
		local function apply()
			local Hide = Hum:GetAttribute(`Equip`) == true or Ch:FindFirstChildOfClass(`Tool`) ~= nil
			for _, M in Ch:GetChildren() do
				if M:IsA(`Model`) and M.Name == `NHAcc_Hand` then
					for _, P in M:GetDescendants() do
						if P:IsA(`BasePart`) then P.Transparency = if Hide then 1 else 0 end
					end
				end
			end
		end
		Hum:GetAttributeChangedSignal(`Equip`):Connect(apply)
		Ch.ChildAdded:Connect(function(C) if C:IsA(`Tool`) or C.Name == `NHAcc_Hand` then task.defer(apply) end end)
		Ch.ChildRemoved:Connect(function(C) if C:IsA(`Tool`) then task.defer(apply) end end)
		apply()
	end
	local function onPlayer(P: Player)
		P.CharacterAdded:Connect(watch)
		if P.Character then task.spawn(watch, P.Character) end
	end
	Players.PlayerAdded:Connect(onPlayer)
	for _, P in Players:GetPlayers() do onPlayer(P) end
end

return Shared
