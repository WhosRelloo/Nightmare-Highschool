--[[
	Enrollment (server): new students arrive in civilian clothes, enrol at the Enrollment desk (outside the
	Records Office) by picking one of three starter uniforms (per gender, Appearance.StarterUniforms), and buy
	more school tops at the School Store (the vending machine). Until enrolled they can't start a class.

	Data: PlayerData.Identity.Enrolled (bool) and .Uniforms (owned school-top ids), via Identity.Sanitize.
	Migration: a student who already had a look (Appearance.Created) counts as enrolled and owns what they wear.
	Player attribute Enrolled mirrors it. Places: CollectionService tags NHEnrollDesk / NHSchoolStore.

	Remotes: ReplicatedStorage.NHEnroll (Ready attribute once handlers are set)
		Info (RF)          -> { Enrolled, Gender, Options = { { Index, Name } } }
		Pick (RF, n)       -> ok, message       (at the desk, not yet enrolled; n = 1..3)
		Catalog (RF)       -> { Yen, Price, Items = { { Index, Id, Name, Owned } } }
		Buy (RF, index)    -> ok, message       (at the store, enrolled)
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local CollectionService = game:GetService(`CollectionService`)

local Data = require(ServerScriptService.Services.Player.Data)
local Identity = require(ServerScriptService.Services.Player.Identity)
local Appearance = require(ReplicatedStorage.UI.Appearance)

local REACH = 14
local Shared = {}
local Local = {}

function Local.Near(P: Player, Tag: string): boolean
	local Root = P.Character and P.Character:FindFirstChild(`HumanoidRootPart`)
	if not Root then return false end
	for _, I in CollectionService:GetTagged(Tag) do
		local Pos = if I:IsA(`BasePart`) then I.Position elseif I:IsA(`Model`) then I:GetPivot().Position else nil
		if Pos and (Pos - Root.Position).Magnitude <= REACH then return true end
	end
	return false
end

function Local.Look(P: Player)
	local Profile = Data.GetProfile(P)
	return Profile and Appearance.Sanitize(Profile.Appearance)
end

function Local.Gender(P: Player): string
	local L = Local.Look(P)
	return if Appearance.IsFemale(L) then `Female` else `Male`
end

function Local.Save(P: Player, I)
	Data.UpdateState(P, { type = `SetIdentity`; identity = I })
	P:SetAttribute(`Enrolled`, I.Enrolled ~= false)
end

-- older students (a look already made) count as enrolled and own the top they wear
function Local.Migrate(P: Player)
	local I = Identity.Get(P)
	if not I then return end
	if I.Enrolled == nil then
		local L = Local.Look(P)
		if L and L.Created then
			I.Enrolled = true
			local U = Appearance.Uniforms[L.Uniform]
			if U and Appearance.IsSchoolTop(L.Uniform) and not table.find(I.Uniforms, U.Id) then table.insert(I.Uniforms, U.Id) end
		else
			I.Enrolled = false
		end
		Local.Save(P, I)
	else
		P:SetAttribute(`Enrolled`, I.Enrolled)
	end
end

function Local.SetLook(P: Player, Changes)
	local L = Local.Look(P)
	if not L then return end
	for K, V in Changes do L[K] = V end
	L.Created = true
	Data.UpdateState(P, { type = `SetAppearance`; appearance = Appearance.Encode(L) })
	if P.Character then pcall(Appearance.ApplyTo, P.Character, L) end
end

function Local.Notify(P: Player, Title: string, Text: string?)
	pcall(function()
		require(ServerScriptService.Services.Features.Notifications).Notify(P, { Title = Title; Text = Text; Kind = `Info`; Duration = 4 })
	end)
end

function Local.Prompt(Inst: Instance, Action: string, Object: string, Attr: string)
	local Host = if Inst:IsA(`Model`) then (Inst.PrimaryPart or Inst:FindFirstChildWhichIsA(`BasePart`, true)) else Inst
	if not (Host and Host:IsA(`BasePart`)) or Host:FindFirstChild(`NH` .. Attr .. `Prompt`) then return end
	local Pr = Instance.new(`ProximityPrompt`)
	Pr.Name = `NH` .. Attr .. `Prompt`
	Pr.ActionText = Action
	Pr.ObjectText = Object
	Pr.HoldDuration = 0
	Pr.MaxActivationDistance = 8
	Pr.RequiresLineOfSight = false
	Pr:SetAttribute(Attr, true)
	Pr.Parent = Host
end

function Shared.OnStart()
	local F = ReplicatedStorage:FindFirstChild(`NHEnroll`) or Instance.new(`Folder`)
	F.Name = `NHEnroll`
	local function rf(Name)
		local R = F:FindFirstChild(Name) or Instance.new(`RemoteFunction`)
		R.Name = Name
		R.Parent = F
		return R
	end
	local Info, Pick, Catalog, Buy = rf(`Info`), rf(`Pick`), rf(`Catalog`), rf(`Buy`)
	F.Parent = ReplicatedStorage

	local Busy = {}
	Info.OnServerInvoke = function(P)
		local I = Identity.Get(P)
		local G = Local.Gender(P)
		local Opts = {}
		for N, Id in Appearance.StarterUniforms[G].Tops do
			local Idx = Appearance.IndexOf(Appearance.Uniforms, Id)
			if Idx then table.insert(Opts, { Index = N; Name = Appearance.Uniforms[Idx].Name; Uniform = Idx }) end
		end
		return { Enrolled = I and I.Enrolled ~= false; Gender = G; Options = Opts }
	end
	Pick.OnServerInvoke = function(P, N)
		if Busy[P] then return false, `One moment...` end
		Busy[P] = true
		local Ok, Res, Msg = pcall(function()
			local I = Identity.Get(P)
			if not I then return false, `Your record isn't loaded yet.` end
			if I.Enrolled == true then return false, `You're already enrolled.` end
			if not Local.Near(P, `NHEnrollDesk`) then return false, `Come to the Enrollment desk.` end
			local G = Local.Gender(P)
			local Set = Appearance.StarterUniforms[G]
			local Id = typeof(N) == `number` and Set.Tops[N]
			local Top = Id and Appearance.IndexOf(Appearance.Uniforms, Id)
			if not Top then return false, `Pick one of the three.` end
			I.Enrolled = true
			if not table.find(I.Uniforms, Id) then table.insert(I.Uniforms, Id) end
			Local.Save(P, I)
			Local.SetLook(P, { Uniform = Top; Bottoms = Appearance.IndexOf(Appearance.BottomsList, Set.Bottoms) or 1; UseAvatar = false })
			Local.Notify(P, `Welcome to Nightmare High`, `You're enrolled. More uniforms at the School Store.`)
			return true, `Enrolled`
		end)
		Busy[P] = nil
		if not Ok then warn(`[Enrollment] {Res}`) return false, `Something went wrong.` end
		return Res, Msg
	end
	Catalog.OnServerInvoke = function(P)
		local I = Identity.Get(P)
		local Profile = Data.GetProfile(P)
		local Items = {}
		local L = Local.Look(P) -- (1.71) only this student's gender's tops (Unisex too); never the admin kit
		for Idx, U in Appearance.Uniforms do
			if Appearance.IsSchoolTop(Idx) and not U.Admin and not U.Earned and Appearance.ClothingAllows(U, L, false) then -- (2.34) Earned: path rewards
				table.insert(Items, { Index = Idx; Id = U.Id; Name = U.Name; Owned = I ~= nil and Appearance.OwnsTop(I.Uniforms, U.Id) })
			end
		end
		return { Yen = Profile and Profile.Yen or 0; Price = Appearance.UniformPrice; Enrolled = I and I.Enrolled ~= false; Items = Items }
	end
	Buy.OnServerInvoke = function(P, Idx)
		if Busy[P] then return false, `One moment...` end
		Busy[P] = true
		local Ok, A, B = pcall(function()
			local I = Identity.Get(P)
			local Profile = Data.GetProfile(P)
			if not (I and Profile) then return false, `Your record isn't loaded yet.` end
			if I.Enrolled == false then return false, `Enrol at the Enrollment desk first.` end
			if not Local.Near(P, `NHSchoolStore`) then return false, `You're too far from the store.` end
			local U = typeof(Idx) == `number` and Appearance.Uniforms[Idx]
			if not (U and Appearance.IsSchoolTop(Idx)) or U.Admin or U.Earned or not Appearance.ClothingAllows(U, Local.Look(P), false) then return false, `Not for sale.` end
			if Appearance.OwnsTop(I.Uniforms, U.Id) then return false, `You already own it.` end
			local Price = Appearance.UniformPrice
			if (Profile.Yen or 0) < Price then return false, `Not enough Yen.` end
			Data.UpdateState(P, { type = `UpdateYen`; amount = -Price })
			table.insert(I.Uniforms, U.Id)
			Local.Save(P, I)
			return true, `Bought {U.Name}. Wear it from a locker-room wardrobe.`
		end)
		Busy[P] = nil
		if not Ok then warn(`[Enrollment] {A}`) return false, `Something went wrong.` end
		return A, B
	end
	F:SetAttribute(`Ready`, true)

	for _, I in CollectionService:GetTagged(`NHEnrollDesk`) do Local.Prompt(I, `Enroll`, `Enrollment`, `NHEnrollDesk`) end
	CollectionService:GetInstanceAddedSignal(`NHEnrollDesk`):Connect(function(I) Local.Prompt(I, `Enroll`, `Enrollment`, `NHEnrollDesk`) end)
	for _, I in CollectionService:GetTagged(`NHSchoolStore`) do Local.Prompt(I, `Browse`, `School Store`, `NHSchoolStore`) end
	CollectionService:GetInstanceAddedSignal(`NHSchoolStore`):Connect(function(I) Local.Prompt(I, `Browse`, `School Store`, `NHSchoolStore`) end)

	local function onPlayer(P: Player)
		task.spawn(function()
			for _ = 1, 60 do if Data.GetProfile(P) then break end task.wait(0.5) end
			Local.Migrate(P)
		end)
	end
	Players.PlayerAdded:Connect(onPlayer)
	for _, P in Players:GetPlayers() do onPlayer(P) end
	if Data.ProfileLoaded then Data.ProfileLoaded:Connect(function(P) task.defer(Local.Migrate, P) end) end
end

function Shared.IsEnrolled(P: Player): boolean
	return P:GetAttribute(`Enrolled`) ~= false
end

return Shared
