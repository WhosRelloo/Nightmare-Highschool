--[[
	Strangers (server): you only know a student's name once you've learned it.

	A student is one save slot of one player: key "<UserId>:<Slot>". Who you know is saved per
	student in PlayerData.Known = { [studentKey] = true } (action "SetKnown").
	You know someone when:
		- they introduced themselves to you (they walked up and pressed E: "Introduce yourself"), or
		- you're both members of the same faction (members know each other), or
		- it's you.
	Names never go out on public attributes. Each player gets only the names they know, through
	ReplicatedStorage.NHStrangers.Names (RemoteEvent, server -> client):
		{ Known = { [userId] = { Name, First, Clan, Rarity, Faction } }, KnowsMe = { [userId] = true } }
	It's re-sent whenever it changes (joins, introductions, name / clan changes, faction changes).

	Remotes: ReplicatedStorage.NHStrangers
		Introduce (RF)  (target: Player) -> ok, reason   rate-limited, max 14 studs, both in school
		Names (RE)      server -> client
	Server API: Strangers.Knows(viewer, target), Strangers.Introduce(from, to), Strangers.Refresh()
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local HttpService = game:GetService(`HttpService`)

---| Modules |---

local Data = require(ServerScriptService.Services.Player.Data)
local Identity = require(ServerScriptService.Services.Player.Identity)
local Clans = require(ReplicatedStorage.Config.Clans)
local FactionConfig = require(ReplicatedStorage.Config.Factions)
local Notifications = require(ServerScriptService.Services.Features.Notifications)

local MAX_DISTANCE = 14
local MAX_KNOWN = 1000
local COOLDOWN = 2

local Last = {} :: { [Player]: number }
local Sent = {} :: { [Player]: string }
local Dirty = true

local Local = {}
local Shared = {}

---| Helpers |---

function Shared.Key(Player: Player): string?
	local Slot = Data.GetSlot(Player)
	return if Slot then `{Player.UserId}:{Slot}` else nil
end

function Local.Known(Player: Player): { [string]: boolean }
	local Profile = Data.GetProfile(Player)
	local K = Profile and Profile.Known
	return if typeof(K) == `table` then K else {}
end

function Local.Faction(Player: Player): string?
	for Id in FactionConfig.Factions do
		if Player:GetAttribute(`Faction_{Id}`) then return Id end
	end
	return nil
end

function Shared.Knows(Viewer: Player, Target: Player): boolean
	if Viewer == Target then return true end
	local Key = Shared.Key(Target)
	if not Key then return false end
	if Local.Known(Viewer)[Key] then return true end
	local F = Local.Faction(Viewer)
	return F ~= nil and F == Local.Faction(Target)
end

function Local.Card(Target: Player)
	local I = Identity.Get(Target)
	if not I or I.First == `` then return nil end
	local Def = I.Clan and Clans.ById[I.Clan]
	return { Name = Identity.FullName(I); First = I.First; Clan = Def and Def.Name; Rarity = Def and Def.Rarity; Faction = Local.Faction(Target) }
end

---| Introductions |---

function Shared.Introduce(From: Player, To: Player): (boolean, string?)
	if typeof(To) ~= `Instance` or not To:IsA(`Player`) or To.Parent ~= Players or To == From then return false, `Nobody there` end
	if From:GetAttribute(`InMainMenu`) ~= false or To:GetAttribute(`InMainMenu`) ~= false then return false, `Not in school` end
	if not Identity.HasName(From) then return false, `Sign the register first` end
	local A = From.Character and From.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	local B = To.Character and To.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	if not A or not B or (A.Position - B.Position).Magnitude > MAX_DISTANCE then return false, `Too far away` end
	local Key = Shared.Key(From)
	local Profile = Data.GetProfile(To)
	if not Key or not Profile then return false, `They're still arriving` end
	if Shared.Knows(To, From) then return false, `They already know you` end
	local Known = table.clone(Local.Known(To))
	local Count = 0
	for _ in Known do Count += 1 end
	if Count >= MAX_KNOWN then
		for K in Known do Known[K] = nil break end -- forget someone old to make room
	end
	Known[Key] = true
	Data.UpdateState(To, { type = `SetKnown`; known = Known })
	local Name = Identity.FullName(Identity.Get(From))
	pcall(Notifications.Notify, To, { Title = `A stranger introduced themselves`; Text = `{Name}. You'll remember the name.`; Kind = `Info` })
	pcall(Notifications.Notify, From, { Title = `You introduced yourself`; Text = `They know your name now.`; Kind = `Good` })
	Dirty = true
	Shared.Refresh()
	local OkP, Progression = pcall(require, ServerScriptService.Services.Player.Progression)
	if OkP and Progression.OnIntroduced then task.spawn(Progression.OnIntroduced, From) end
	return true
end

---| Sending names |---

function Shared.Refresh()
	Dirty = true
end

function Local.Send()
	Dirty = false
	local All = Players:GetPlayers()
	local Cards = {}
	for _, P in All do Cards[P] = Local.Card(P) end
	local Remote = ReplicatedStorage:FindFirstChild(`NHStrangers`) and ReplicatedStorage.NHStrangers:FindFirstChild(`Names`)
	if not Remote then return end
	for _, Viewer in All do
		if Data.GetProfile(Viewer) then
			local Payload = { Known = {}; KnowsMe = {} }
			for _, Target in All do
				if Cards[Target] and Shared.Knows(Viewer, Target) then
					Payload.Known[tostring(Target.UserId)] = Cards[Target]
				end
				if Target ~= Viewer and Data.GetProfile(Target) and Shared.Knows(Target, Viewer) then
					Payload.KnowsMe[tostring(Target.UserId)] = true
				end
			end
			local Encoded = HttpService:JSONEncode(Payload)
			if Sent[Viewer] ~= Encoded then
				Sent[Viewer] = Encoded
				Remote:FireClient(Viewer, Payload)
			end
		end
	end
end

---| Lifecycle |---

function Shared.OnStart()
	local Folder = Instance.new(`Folder`)
	Folder.Name = `NHStrangers`
	local Introduce = Instance.new(`RemoteFunction`) Introduce.Name = `Introduce` Introduce.Parent = Folder
	local Names = Instance.new(`RemoteEvent`) Names.Name = `Names` Names.Parent = Folder
	Folder.Parent = ReplicatedStorage

	Introduce.OnServerInvoke = function(Player, Target)
		local Now = os.clock()
		if Last[Player] and Now - Last[Player] < COOLDOWN then return false, `Slow down` end
		Last[Player] = Now
		return Shared.Introduce(Player, Target)
	end

	local function Watch(Player: Player)
		Player.AttributeChanged:Connect(function(Name)
			if Name:sub(1, 8) == `Faction_` or Name == `Slot` or Name == `Signed` or Name == `InMainMenu` then Dirty = true end
		end)
		-- other players never see the Roblox name; nameplates are drawn per viewer
		Player.CharacterAdded:Connect(function(Character)
			local Humanoid = Character:WaitForChild(`Humanoid`, 10) :: Humanoid?
			if Humanoid then
				Humanoid.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
				Humanoid.DisplayName = `Student`
			end
		end)
	end
	for _, P in Players:GetPlayers() do Watch(P) end
	Players.PlayerAdded:Connect(function(P) Watch(P) Dirty = true end)
	Players.PlayerRemoving:Connect(function(P)
		Last[P] = nil
		Sent[P] = nil
		Dirty = true
	end)
	Data.ProfileLoaded:Connect(function() Dirty = true end)

	-- names and clans change through Identity; checking once a second keeps everyone in step cheaply
	task.spawn(function()
		local Tick = 0
		while true do
			task.wait(0.25)
			Tick += 1
			if Dirty or Tick % 4 == 0 then pcall(Local.Send) end
		end
	end)
end

---| Testing |---

function Shared.IntroduceForTests(From: Player, To: Player) return Shared.Introduce(From, To) end
function Shared.SentForTests(Player: Player) return Sent[Player] end

return Shared
