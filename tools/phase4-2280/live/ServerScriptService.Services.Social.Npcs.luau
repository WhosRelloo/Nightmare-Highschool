--[[
	Talkable NPCs (Config.Npcs: faction leaders, quest givers). Each stands at the part whose
	attribute NpcPost is its id, has a "Talk" prompt that opens server dialogue
	(Services.Social.Dialogue), walks back to its post when pushed away, and respawns after dying.

	Hitting a leader costs relationship and faction standing (Config.Reputation.AttackPenalty),
	at most once per player per leader every PENALTY_COOLDOWN seconds.

	(2.28) Staff with Posts (Config.Npcs) move between them by school segment: Homeroom, the other Class periods, and
	Other (before school, passing, break, lunch, after school), Off (the rest); no key = off campus. A change fades them out at the old
	post and in at the new one, on the next tick. Npcs.PostKey(NpcId, Kind, Name) -> key? (pure).
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local Interaction = require(ReplicatedStorage.Config.Interaction)
local RepConfig = require(ReplicatedStorage.Config.Reputation)
local FactionConfig = require(ReplicatedStorage.Config.Factions)
local Cast = require(ReplicatedStorage.Config.Npcs)

local Places = require(ServerScriptService.Services.Quests.Places)

local EntityLoader = require(ServerScriptService.Services.Managers.EntityLoader)
local Downed = require(ServerScriptService.Services.Features.Downed)
local Reputation = require(ServerScriptService.Services.Social.Reputation)
local Factions = require(ServerScriptService.Services.Social.Factions)
local Dialogue = require(ServerScriptService.Services.Social.Dialogue)
local Notifications = require(ServerScriptService.Services.Features.Notifications)

local BUSY = { `Downed`, `Carried`, `Gripped`, `Gripping`, `InActivity`, `Stun`, `ParryStun`, `Paralyzed` }
local RESPAWN_SECONDS = 30
local PENALTY_COOLDOWN = 8
local HOME_RADIUS = 3

local Active = {} :: { [string]: any }
local Returning = {} :: { [string]: boolean } -- (2.24.0) OffWhen staff on their way back to the post
local LastPenalty = {} :: { [Player]: { [string]: number } }

local Local = {}
local Shared = {}

-- (2.28) the post key for a school segment: Config.Npcs Posts (Homeroom / Class / Other), else the NPC's own id.
-- nil = not on campus in that segment.
local OTHER = { BeforeSchool = true; Passing = true; Break = true; Lunch = true; AfterSchool = true }
function Shared.PostKey(NpcId: string, Kind: string?, Name: string?): string?
	local Npc = Cast[NpcId]
	if not Npc then return nil end
	if not Npc.Posts then return NpcId end
	if Kind == `Class` and Name == `Homeroom` then return Npc.Posts.Homeroom end
	if Kind == `Class` then return Npc.Posts.Class end
	if OTHER[Kind or ``] then return Npc.Posts.Other end
	return Npc.Posts.Off -- (2.28) evening, night and morning: most staff have none
end
function Local.KeyNow(NpcId: string): string?
	local Ok, Seg = pcall(function() return require(ServerScriptService.Services.School.SchoolClock).GetState().Segment end)
	return Shared.PostKey(NpcId, Ok and Seg and Seg.Kind or nil, Ok and Seg and Seg.Name or nil)
end

function Local.Post(NpcId: string): BasePart?
	local Key = Local.KeyNow(NpcId) -- (2.28)
	return if Key then Places.Find(`NpcPost`, Key) else nil
end

function Local.Tag(Model: Model, Npc, Color: Color3)
	local Tag = Instance.new(`BillboardGui`)
	Tag.Name = `NameTag`
	Tag.Size = UDim2.new(0, 200, 0, 40)
	Tag.StudsOffset = Vector3.new(0, 2.8, 0)
	Tag.MaxDistance = 70

	local Name = Instance.new(`TextLabel`)
	Name.Size = UDim2.new(1, 0, 0.6, 0)
	Name.BackgroundTransparency = 1
	Name.Font = Enum.Font.GothamBold
	Name.TextSize = 16
	Name.TextColor3 = Color
	Name.TextStrokeTransparency = 0.3
	Name.Text = Npc.Name
	Name.Parent = Tag

	local Role = Instance.new(`TextLabel`)
	Role.Position = UDim2.fromScale(0, 0.6)
	Role.Size = UDim2.new(1, 0, 0.4, 0)
	Role.BackgroundTransparency = 1
	Role.Font = Enum.Font.Gotham
	Role.TextSize = 12
	Role.TextColor3 = Color3.fromRGB(220, 220, 220)
	Role.TextStrokeTransparency = 0.4
	Role.Text = Npc.Role
	Role.Parent = Tag

	Tag.Parent = Model:FindFirstChild(`Head`)
end

-- Faction look: tint the clothes-free rig and add a small glow so leaders stand out.
-- the owner's catalog hair on a scripted character (ReplicatedStorage.NHHairCatalog via Appearance.LoadHair)
local function giveHair(Model: Model, Id: number)
	local ok, Appearance = pcall(require, game:GetService(`ReplicatedStorage`).UI.Appearance)
	if not ok then return end
	local Hum = Model:FindFirstChildWhichIsA(`Humanoid`)
	if not Hum then return end
	local okL, Src = pcall(Appearance.LoadHair, Id)
	if not (okL and typeof(Src) == `Instance`) then return end
	local Acc = Src:Clone()
	for _, J in Acc:GetDescendants() do if J:IsA(`JointInstance`) or J:IsA(`WeldConstraint`) then J:Destroy() end end
	local H = Acc:FindFirstChild(`Handle`)
	if H and H:IsA(`BasePart`) then H.Anchored = false H.CanCollide = false H.Massless = true end
	Hum:AddAccessory(Acc)
end
local NPC_HAIR = { -- one fixed hair per character
	Pip = 3576061351; Ezra = 2680376026; Varga = 1852838120; Mallory = 1903448711;
	Dex = 3379112107; Vesper = 3612414364; Bruno = 1848734696; Dunmore = 3609301673;
}

function Local.Dress(Model: Model, Color: Color3)
	local Skin = Color3.fromRGB(234, 196, 160)
	-- Drop the generic rig clothing so the faction colours show.
	for _, Item in Model:GetChildren() do
		if Item:IsA(`Shirt`) or Item:IsA(`Pants`) or Item:IsA(`ShirtGraphic`) or Item:IsA(`BodyColors`) then Item:Destroy() end
	end
	for _, Part in Model:GetDescendants() do
		if Part:IsA(`BasePart`) then
			if Part.Name == `Torso` or Part.Name == `UpperTorso` or Part.Name == `LowerTorso` then
				Part.Color = Color:Lerp(Color3.new(0, 0, 0), 0.35)
			elseif Part.Name:find(`Leg`) then
				Part.Color = Color3.fromRGB(30, 30, 36)
			elseif Part.Name ~= `HumanoidRootPart` then
				Part.Color = Skin
			end
		end
	end
	local Root = Model:FindFirstChild(`HumanoidRootPart`)
	if Root then
		local Light = Instance.new(`PointLight`)
		Light.Color = Color
		Light.Range = 10
		Light.Brightness = 0.8
		Light.Parent = Root
	end
end

function Local.OnTalk(Player: Player, NpcId: string)
	local N = Active[NpcId]
	if not N or not N.Model.Parent then return end
	local Character = Player.Character
	local Humanoid = Character and Character:FindFirstChildWhichIsA(`Humanoid`)
	if not Humanoid or Humanoid.Health <= 0 or Humanoid:GetAttribute(`Downed`) then return end
	if StateManager.HasState(Character, BUSY) then return end
	if N.Humanoid.Health <= 0 or N.Humanoid:GetAttribute(`Downed`) then return end

	-- Face the player
	local Root = Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	if Root then
		local From = N.Root.Position
		local To = Vector3.new(Root.Position.X, From.Y, Root.Position.Z)
		if (To - From).Magnitude > 0.1 and not N.Model:GetAttribute(`NHSeated`) then N.Root.CFrame = CFrame.lookAt(From, To) end -- (1.45) a seated NPC (Sable) stays in the chair
	end

	Dialogue.Start(Player, NpcId, N.Model)
end

-- (2.24.0) staff with another job after hours (Config.Npcs OffWhen = a Config.Stealth zone): the post stays empty while
-- that zone is watched, because the watcher is the same person; they come back to the post when it isn't
function Local.Away(Npc, NpcId: string?): boolean
	if Npc.Posts and NpcId then return Local.KeyNow(NpcId) == nil end -- (2.28) staff off campus in this segment
	if not Npc.OffWhen then return false end
	local Ok, Away = pcall(function()
		local Zone = require(ReplicatedStorage.Config.Stealth).Zones[Npc.OffWhen]
		local Kind = require(ServerScriptService.Services.School.SchoolClock).GetState().Segment.Kind
		return Zone ~= nil and Zone.Active[Kind] == true
	end)
	return Ok and Away == true
end

function Local.Depart(NpcId: string)
	local N = Active[NpcId]
	if not N then return end
	Active[NpcId] = nil
	for _, P in Players:GetPlayers() do
		if Dialogue.IsTalking(P) then pcall(function() if (P.Character and P.Character:FindFirstChild(`HumanoidRootPart`)) and (P.Character.HumanoidRootPart.Position - N.Root.Position).Magnitude < 20 then Dialogue.Close(P) end end) end
	end
	if N.Model.Parent then
		N.Model:SetAttribute(`Departing`, true) -- fades out on clients (VFX P2-12)
		task.delay(0.8, function() if N.Model.Parent then N.Model:Destroy() end end)
	end
end

function Local.Spawn(NpcId: string)
	local Npc = Cast[NpcId]
	if Npc and Local.Away(Npc, NpcId) then return end -- (2.24.0) Local.Tick brings them back when the zone closes
	local Post = Local.Post(NpcId)
	if not Npc or not Post then
		if Npc and Npc.Posts and not Local.KeyNow(NpcId) then return end -- (2.28) off campus now: not an error
		warn(`[Npcs] no part with NpcPost = {NpcId}`)
		return
	end
	local Faction = Npc.Faction and FactionConfig.Factions[Npc.Faction]
	local Color = Faction and Faction.Color or Npc.Color or Color3.new(1, 1, 1)

	local AIFolder = ServerScriptService.Services.AI.AI
	local Model = AIFolder.Rig:Clone()
	Model.Name = Npc.Name
	Model:SetAttribute(`NpcId`, NpcId)
	Model:SetAttribute(`Role`, `Leader`)
	if Npc.Clique then Model:SetAttribute(`Clique`, Npc.Clique) end -- (1.28) clique leaders

	-- (audit) drop the rig's own (inert LocalScript) Animate first, as Schedules does: with two named Animate,
	-- Fortune.Pose toggled the inert one
	local OldAnimate = Model:FindFirstChild(`Animate`)
	if OldAnimate then OldAnimate:Destroy() end
	local Animate = AIFolder.Animate:Clone()
	Animate.Parent = Model
	Animate.Enabled = true

	Model:PivotTo(Post.CFrame)
	Model:SetAttribute(`Presence`, true) -- fades in on clients (Controllers.World.Presence, VFX P2-12)
	Model.Parent = workspace.Live
	EntityLoader.OnCharacterAdded(Model)

	local Humanoid = Model:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	local Root = Model:FindFirstChild(`HumanoidRootPart`) :: BasePart
	Humanoid.WalkSpeed = 6 -- a stroll that fits the walk clip (5.3 studs/s at 1x; AI.AI.Animate plays it at speed / 5.3)
	Humanoid.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	pcall(function() Root:SetNetworkOwner(nil) end)

	Local.Dress(Model, Color)
	-- a full Nightmare High look (face art, outfit, skin, hair): Services.Features.NpcLooks
	local Looks = require(ServerScriptService.Services.Features.NpcLooks)
	if Looks.Specs[NpcId] then
		Model:SetAttribute(`NHLooksKey`, NpcId) -- (2.24.0) the cinematics dress their clones from this
		task.spawn(Looks.Apply, Model, Looks.Specs[NpcId])
	elseif NPC_HAIR[NpcId] then
		task.spawn(giveHair, Model, NPC_HAIR[NpcId])
	end
	Local.Tag(Model, Npc, Color)

	local Prompt = Instance.new(`ProximityPrompt`)
	Prompt.Name = `TalkPrompt`
	Prompt.ActionText = `Talk`
	Prompt.ObjectText = Npc.Name
	Prompt.KeyboardKeyCode = Interaction.PromptKey
	Prompt.GamepadKeyCode = Interaction.GamepadKey
	Prompt.HoldDuration = 0
	Prompt.MaxActivationDistance = 10
	Prompt.RequiresLineOfSight = false
	Prompt.Parent = Root
	Prompt.Triggered:Connect(function(Player)
		local Ok, Err = pcall(Local.OnTalk, Player, NpcId)
		if not Ok then warn(`[Npcs] {Err}`) end
	end)

	local N = { Id = NpcId; Key = Local.KeyNow(NpcId); Model = Model; Humanoid = Humanoid; Root = Root; Post = Post; Prompt = Prompt } -- (2.28) Key
	Active[NpcId] = N

	Humanoid:GetAttributeChangedSignal(`Downed`):Connect(function()
		Prompt.Enabled = not Humanoid:GetAttribute(`Downed`)
	end)
	Humanoid.Died:Connect(function()
		Prompt.Enabled = false
		task.delay(RESPAWN_SECONDS, function()
			if Active[NpcId] ~= N then return end
			-- the body fades out (VFX P2-12), then they come back
			if Model.Parent then
				Model:SetAttribute(`Departing`, true)
				task.wait(0.8)
				if Model.Parent then Model:Destroy() end
			end
			if Active[NpcId] ~= N then return end
			Local.Spawn(NpcId)
		end)
	end)
end

-- Walk back to the post when moved (pushed, carried and dropped, recovered from downed).
function Local.Tick()
	-- (2.24.0) staff who go off to another job after hours (OffWhen)
	-- (2.28) and staff with Posts, who move between them as the school day changes
	for NpcId, Npc in Cast do
		if not (Npc.OffWhen or Npc.Posts) then continue end
		local Away = Local.Away(Npc, NpcId)
		local N = Active[NpcId]
		if Away and N then Local.Depart(NpcId)
		elseif N and Npc.Posts and N.Key ~= Local.KeyNow(NpcId) then
			Local.Depart(NpcId) -- (2.28) a new segment: fade out here, back at the new post next tick
		elseif not Away and not N and not Returning[NpcId] and Local.Post(NpcId) then
			Returning[NpcId] = true
			task.spawn(function() pcall(Local.Spawn, NpcId) Returning[NpcId] = nil end)
		end
	end
	for _, N in Active do
		if not N.Model.Parent or N.Humanoid.Health <= 0 or N.Humanoid:GetAttribute(`Downed`) then continue end
		if N.Model:GetAttribute(`CarriedBy`) or N.Model:GetAttribute(`GrippedBy`) then continue end
		local Offset = (N.Root.Position - N.Post.Position) * Vector3.new(1, 0, 1)
		if Offset.Magnitude > HOME_RADIUS then
			if Offset.Magnitude > 60 then
				N.Model:PivotTo(N.Post.CFrame) -- fell off the map or got dragged far
			else
				N.Humanoid:MoveTo(N.Post.Position)
			end
		end
	end
end

function Local.OnDamage(Target: Model, Damage: number, Attacker: Model?)
	local NpcId = Target:GetAttribute(`NpcId`)
	if not NpcId or not Attacker then return end
	local Player = Players:GetPlayerFromCharacter(Attacker)
	local Npc = RepConfig.Npcs[NpcId]
	if not Player or not Npc then return end

	LastPenalty[Player] = LastPenalty[Player] or {}
	local Now = os.clock()
	if LastPenalty[Player][NpcId] and Now - LastPenalty[Player][NpcId] < PENALTY_COOLDOWN then return end
	LastPenalty[Player][NpcId] = Now

	local Penalty = RepConfig.AttackPenalty
	Reputation.ChangeRelationship(Player, NpcId, Penalty.Relationship, `You attacked {Npc.Name}.`)
	if Npc.Faction then
		Factions.AddStanding(Player, Npc.Faction, Penalty.Standing, `Attacked {Npc.Name}`)
	end
	if Dialogue.IsTalking(Player) then Dialogue.Close(Player) end
	Notifications.Notify(Player, { Title = `{Npc.Name} won't forget that`; Kind = `Bad`; Duration = 4 })
end

---| API |---

function Shared.Get(NpcId: string): Model?
	local N = Active[NpcId]
	return N and N.Model
end

function Shared.TalkForTests(Player: Player, NpcId: string)
	Local.OnTalk(Player, NpcId)
	return Dialogue.IsTalking(Player)
end

function Shared.OnStart()
	for NpcId in Cast do
		-- (2.24.0) marked as on their way until the first spawn finishes: Local.Tick's OffWhen check runs a second
		-- later, and a spawn still loading the look then made a second Night Custodian at the same post
		Returning[NpcId] = true
		task.spawn(function()
			local Ok, Err = pcall(Local.Spawn, NpcId)
			Returning[NpcId] = nil
			if not Ok then warn(`[Npcs] {NpcId}: {Err}`) end
		end)
	end

	Downed.OnDamage:Connect(function(...)
		local Ok, Err = pcall(Local.OnDamage, ...)
		if not Ok then warn(`[Npcs] {Err}`) end
	end)
	Players.PlayerRemoving:Connect(function(Player) LastPenalty[Player] = nil end)

	task.spawn(function()
		while true do
			task.wait(1)
			Local.Tick()
		end
	end)
end

return Shared
