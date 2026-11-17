--[[
	Cliques (server). Services.Social.Cliques   (Phase 1, 2026-11-03; Config.Cliques)
	The social map of Nightmare High: eight cliques, each with its members, hangout, leader and rival.

	  Standing   how each clique's members see you, -100 to 100 (Hostile / Wary / Neutral / Friendly / Respected),
	             saved per slot in PlayerData.Social.Cliques. A gain with one clique costs a little with its rival, and
	             a loss with one is a small gain with its rival. Phase 1 sources: putting a member on the floor.
	  Members    NPCs carry the attribute Clique: the scheduled students (Services.Features.Schedules), the named cast,
	             delinquents and ambient students (by name, Config.Cliques.Npcs), and three new leaders who stand at
	             their hangouts (the Athletes' captain, the Chapel Choir's cantor, the Ink Club's ringleader).
	  Remotes    ReplicatedStorage.NHCliques (Ready): Get (RF) -> the phone's Cliques app list; Changed (RE) when your
	             standing moves.
	API: Get(Player) -> { [id] = value }, Add(Player, Id, Amount, Reason?), Tier(value), State(Player).
	1.27: SyncTiers(Player) (attributes CliqueTier_<Id>), Say(Model, Text) (remote NHCliques.Say), Line(Id, Key).
]]

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local CollectionService = game:GetService(`CollectionService`)

local Config = require(ReplicatedStorage.Config.Cliques)

local Shared = {}
local Local = {}
local TIER_LINE = {
	Respected = `They respect you now.`; Friendly = `They're friendly toward you now.`; Neutral = `They've stopped caring either way.`;
	Wary = `They're wary of you now.`; Hostile = `They're out for you now.`;
}
local Remotes = nil

local function svc(path: string)
	local node = ServerScriptService.Services
	for part in path:gmatch(`[^%.]+`) do node = node:FindFirstChild(part) if not node then return nil end end
	local ok, mod = pcall(require, node)
	return ok and mod or nil
end

---| standing |---

function Shared.Get(P: Player)
	local Rep = svc(`Social.Reputation`)
	local Social = Rep and Rep.Get(P)
	if not Social then return nil end
	Social.Cliques = Config.Sanitize(Social.Cliques)
	return Social.Cliques
end

function Shared.Tier(Value: number): string
	return Config.Tier(Value)
end

-- (line matrix) the dress code: a clique deals with you in person if you wear one of its tops, you're Friendly or
-- better with it, or you're a member. Dares by phone and members' jobs never ask.
function Shared.Dressed(P: Player, Id: string): boolean
	if not Config.Defs[Id] then return true end
	local C = Shared.Get(P)
	local Tier = C and Config.Tier(C[Id] or 0)
	if Tier == `Friendly` or Tier == `Respected` then return true end
	local M = svc(`Social.CliqueMembership`)
	if M and M.IsMember and M.IsMember(P, Id) then return true end
	local W = P.Character and Config.ParseWear(P.Character:GetAttribute(`NHWear`))
	return W ~= nil and Config.WearsTop(Id, W.Top)
end

function Shared.Add(P: Player, Id: string, Amount: number, Reason: string?, FromRival: boolean?)
	local C = Shared.Get(P)
	local Def = Config.Defs[Id]
	if not (C and Def) or Amount == 0 then return end
	local Old = C[Id]
	C[Id] = math.clamp(math.floor(Old + Amount + 0.5), Config.Min, Config.Max)
	local Delta = C[Id] - Old
	if not FromRival and Def.Rival and Config.Defs[Def.Rival] then
		Shared.Add(P, Def.Rival, -Delta * Config.Standing.RivalShare, nil, true) -- a share of what actually changed
	end
	if not FromRival and Delta ~= 0 then
		local N = svc(`Features.Notifications`)
		local OldTier, NewTier = Config.Tier(Old), Config.Tier(C[Id])
		if N then
			pcall(N.Notify, P, {
				Title = `{if Delta > 0 then `+` else ``}{Delta} {Def.Name}`;
				Text = if OldTier ~= NewTier then `{Reason or ``}{if Reason then `  ·  ` else ``}{TIER_LINE[NewTier] or ``}` else Reason;
				Kind = if Delta > 0 then `Info` else `Warning`; Duration = 4;
			})
		end
	end
	if Remotes and P.Parent then Remotes.Changed:FireClient(P, Shared.State(P)) end
	Shared.SyncTiers(P)
end

-- (1.27) your tier with each clique as player attributes (CliqueTier_<Id>), so clients can react without asking
function Shared.SyncTiers(P: Player)
	local C = Shared.Get(P)
	for _, Id in Config.Order do
		local T = C and Config.Tier(C[Id] or 0) or nil
		if P:GetAttribute(`CliqueTier_{Id}`) ~= T then P:SetAttribute(`CliqueTier_{Id}`, T) end
	end
	if C then pcall(Shared.CheckRewards, P, C) end
end

-- (1.28, Phase 3) Friendly earns a clique's first title; Respected with its leader's second quest done unlocks its
-- reward: the second title, its Look in the Wardrobe (its top is added to the tops you own, so the look saves),
-- backup in fights (Social.CliqueFights) and its shop Perk. CliqueReward_<Id> on the player says it's unlocked
-- (it follows your standing: drop below Respected and the backup and discount pause; titles stay).
function Shared.CheckRewards(P: Player, C)
	local Profile = svc(`Player.Data`) and svc(`Player.Data`).GetProfile(P)
	local Done = Profile and Profile.Quests and Profile.Quests.Done
	local Rep = svc(`Social.Reputation`)
	for _, Id in Config.Order do
		local D = Config.Defs[Id]
		local T = Config.Tier(C[Id] or 0)
		if D.Titles and Rep and (T == `Friendly` or T == `Respected`) then pcall(Rep.AwardTitle, P, D.Titles[1]) end
		local Unlocked = T == `Respected` and Done ~= nil and D.Quests ~= nil and Done[D.Quests[2]] ~= nil
		local Had = P:GetAttribute(`CliqueReward_{Id}`) == true
		if Unlocked ~= Had then P:SetAttribute(`CliqueReward_{Id}`, if Unlocked then true else nil) end
		if Unlocked and not Had then
			local New = Rep and D.Titles and select(2, pcall(Rep.AwardTitle, P, D.Titles[2]))
			Local.GrantTop(P, D)
			if New then
				local N = svc(`Features.Notifications`)
				local Perk = D.Perk and `  ·  {D.Perk.Text}` or ``
				if N then pcall(N.Notify, P, {
					Title = `{D.Name} respect you`;
					Text = `Title "{D.Titles[2]}"  ·  Clique Look in the Wardrobe  ·  they'll back you up near {D.HangoutName}{Perk}`;
					Kind = `Good`; Duration = 8;
				}) end
			end
		end
	end
end

-- the clique's top goes into the tops you own (school tops must be owned to wear them: UI.Appearance)
function Local.GrantTop(P: Player, D)
	local Top = D.SignatureLook and D.SignatureLook.Top
	local Identity = svc(`Player.Identity`)
	local Data = svc(`Player.Data`)
	if not (Top and Identity and Data) then return end
	local Ok, App = pcall(require, ReplicatedStorage.UI.Appearance)
	local Idx = Ok and App.IndexOf(App.Uniforms, Top)
	local I = Identity.Get(P)
	if not (Idx and I and I.Uniforms) then return end
	if App.IsSchoolTop(Idx) and not table.find(I.Uniforms, Top) then
		table.insert(I.Uniforms, Top)
		pcall(Data.UpdateState, P, { type = `SetIdentity`; identity = I })
	end
	-- (1.71) the girls' version of the look (Config.Cliques SignatureLook.FemaleTop)
	local FTop = D.SignatureLook.FemaleTop
	local FIdx = FTop and App.IndexOf(App.Uniforms, FTop)
	if FIdx and App.IsSchoolTop(FIdx) and not App.OwnsTop(I.Uniforms, FTop) then
		table.insert(I.Uniforms, FTop)
		pcall(Data.UpdateState, P, { type = `SetIdentity`; identity = I })
	end
end

-- (1.27) a speech bubble over a clique NPC for everyone nearby (Controllers.World.Chatter shows it)
-- (1.35) a line only one student sees (members greeting you by name)
function Shared.SayTo(P: Player, Model: Model?, Text: string?)
	if Remotes and Remotes.Say and Model and Text and P.Parent then Remotes.Say:FireClient(P, Model, Text) end
end

-- (1.35) send the phone's list again (membership changed)
function Shared.Push(P: Player)
	if Remotes and P.Parent then Remotes.Changed:FireClient(P, Shared.State(P)) end
end

function Shared.Say(Model: Model?, Text: string?)
	if not (Remotes and Remotes.Say and Model and Text) then return end
	local Head = Model:FindFirstChild(`Head`)
	if not Head then return end
	for _, P in Players:GetPlayers() do
		local R = P.Character and P.Character:FindFirstChild(`HumanoidRootPart`)
		if R and (R.Position - Head.Position).Magnitude <= 90 then Remotes.Say:FireClient(P, Model, Text) end
	end
end

-- a random line from a clique's list (Config.Cliques: Taunt, Jeer, Leave, Rally, Scatter)
function Shared.Line(Id: string, Key: string): string?
	local D = Config.Defs[Id]
	local L = D and D[Key]
	return L and #L > 0 and L[math.random(1, #L)] or nil
end

-- the phone's Cliques app
function Shared.State(P: Player)
	local C = Shared.Get(P) or Config.Sanitize(nil)
	local Factions = svc(`Social.Factions`)
	local Membership = svc(`Social.CliqueMembership`) -- (1.35)
	local Joined = Membership and Membership.Joined(P)
	local Out = {}
	for _, Id in Config.Order do
		local D = Config.Defs[Id]
		local Faction = nil
		if D.Faction and Factions then
			pcall(function()
				local F = Factions.Get(P, D.Faction)
				Faction = { Rank = Factions.RankFor(P, D.Faction); Member = F and F.Member == true; Standing = F and F.Standing or 0 }
			end)
		end
		table.insert(Out, {
			Id = Id; Name = D.Name; Archetype = D.Archetype; Tagline = D.Tagline; Color = D.Color;
			Hangout = D.HangoutName; Leader = D.Leader; Rival = D.Rival and Config.Defs[D.Rival] and Config.Defs[D.Rival].Name or ``;
			Standing = C[Id] or 0; Tier = Config.Tier(C[Id] or 0); Faction = Faction;
			Member = if Joined == Id then { Rank = Membership.Rank(P) } else nil;
		})
	end
	return Out
end

---| members |---

function Local.Tag(M: Model)
	if M:GetAttribute(`Clique`) or Players:GetPlayerFromCharacter(M) then return end
	local Id = Config.Npcs[M.Name]
	if Id then M:SetAttribute(`Clique`, Id) end
end

-- the leader's spot: behind the middle of their clique's gathering spots, facing in
function Local.LeaderCFrame(Clique: string): CFrame?
	local Sum, N = Vector3.zero, 0
	for _, P in CollectionService:GetTagged(`NHCliqueSpot`) do
		if P:GetAttribute(`NHCliqueSpot`) == Clique then Sum += P.Position N += 1 end
	end
	if N == 0 then return nil end
	local Mid = Sum / N
	return CFrame.lookAt(Mid + Vector3.new(0, 2.6, 0), Mid + Vector3.new(0, 2.6, -1)) -- stand in the middle of the group
end

-- stand a leader's feet on the floor under them (the rig is scaled, so measure rather than guess)
function Local.Ground(M: Model)
	local Root = M:FindFirstChild(`HumanoidRootPart`)
	if not (Root and M.Parent) then return end
	local Low = math.huge
	for _, P in M:GetChildren() do
		if P:IsA(`BasePart`) and P ~= Root then Low = math.min(Low, P.Position.Y - P.Size.Y / 2) end
	end
	if Low == math.huge then return end
	local RP = RaycastParams.new()
	RP.FilterType = Enum.RaycastFilterType.Exclude
	local Ex = { M }
	for _, N in { `Live`, `NHFx`, `NHAmbient`, `NHSchedule` } do local F = workspace:FindFirstChild(N) if F then table.insert(Ex, F) end end
	RP.FilterDescendantsInstances = Ex
	RP.RespectCanCollide = true
	local Hit = workspace:Raycast(Root.Position + Vector3.new(0, 2, 0), Vector3.new(0, -30, 0), RP)
	if Hit then M:PivotTo(M:GetPivot() + Vector3.new(0, Hit.Position.Y - Low, 0)) end
end

-- the same name tag as the cast (Services.Social.Npcs)
function Local.NameTag(M: Model, Name: string, Title: string, Color: Color3)
	local Head = M:FindFirstChild(`Head`)
	if not Head then return end
	local B = Instance.new(`BillboardGui`)
	B.Name = `NameTag`
	B.Size = UDim2.new(0, 200, 0, 40)
	B.StudsOffset = Vector3.new(0, 2.8, 0)
	B.MaxDistance = 70
	local N = Instance.new(`TextLabel`)
	N.Size = UDim2.new(1, 0, 0.6, 0)
	N.BackgroundTransparency = 1
	N.Font = Enum.Font.GothamBold
	N.TextSize = 16
	N.TextColor3 = Color
	N.TextStrokeTransparency = 0.3
	N.Text = Name
	N.Parent = B
	local T = Instance.new(`TextLabel`)
	T.Position = UDim2.fromScale(0, 0.6)
	T.Size = UDim2.new(1, 0, 0.4, 0)
	T.BackgroundTransparency = 1
	T.Font = Enum.Font.Gotham
	T.TextSize = 12
	T.TextColor3 = Color3.fromRGB(220, 220, 220)
	T.TextStrokeTransparency = 0.4
	T.Text = Title
	T.Parent = B
	B.Parent = Head
end

function Local.SpawnLeaders()
	local AI = ServerScriptService.Services.AI.AI
	local Live = workspace:FindFirstChild(`Live`) or workspace
	local Looks = svc(`Features.NpcLooks`)
	for _, L in Config.NewLeaders do
		local CF = Local.LeaderCFrame(L.Clique)
		if CF and not Live:FindFirstChild(L.Name) then
			local M = AI.Rig:Clone()
			M.Name = L.Name
			M:SetAttribute(`Clique`, L.Clique)
			M:SetAttribute(`Role`, `CliqueLeader`)
			local Anim = AI:FindFirstChild(`Animate`)
			if Anim then local A = Anim:Clone() A.Parent = M A.Enabled = true end
			M:PivotTo(CF)
			M.Parent = Live
			local Hum = M:FindFirstChildOfClass(`Humanoid`)
			if Hum then Hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None Hum.WalkSpeed = 6 end
			local Root = M:FindFirstChild(`HumanoidRootPart`)
			if Root then Root.Anchored = true end
			pcall(function() require(ServerScriptService.Services.Managers.EntityLoader).OnCharacterAdded(M) end)
			if Looks then pcall(Looks.Apply, M, L.Spec) end
			Local.NameTag(M, L.Name, L.Title, Config.Defs[L.Clique].Color)
			task.delay(1, Local.Ground, M) -- once the look (and its scale) is on
		end
	end
end

function Shared.OnStart()
	local F = Instance.new(`Folder`)
	F.Name = `NHCliques`
	local Get = Instance.new(`RemoteFunction`) Get.Name = `Get` Get.Parent = F
	local Changed = Instance.new(`RemoteEvent`) Changed.Name = `Changed` Changed.Parent = F
	local Say = Instance.new(`RemoteEvent`) Say.Name = `Say` Say.Parent = F
	Remotes = { Changed = Changed; Say = Say }
	-- keep everyone's clique tiers on their player (a slot loading, the menu, standing changing elsewhere)
	task.spawn(function()
		while true do
			task.wait(3)
			for _, P in Players:GetPlayers() do pcall(Shared.SyncTiers, P) end
		end
	end)
	local Last = {} :: { [Player]: number }
	Get.OnServerInvoke = function(P)
		if Last[P] and os.clock() - Last[P] < 0.25 then return nil end
		Last[P] = os.clock()
		return Shared.State(P)
	end
	Players.PlayerRemoving:Connect(function(P) Last[P] = nil end)
	F:SetAttribute(`Ready`, true)
	F.Parent = ReplicatedStorage

	-- name the members as they appear
	for _, Name in { `Live`, `NHAmbient` } do
		task.spawn(function()
			local Folder = workspace:WaitForChild(Name, 30)
			if not Folder then return end
			for _, M in Folder:GetChildren() do if M:IsA(`Model`) then Local.Tag(M) end end
			Folder.ChildAdded:Connect(function(M) if M:IsA(`Model`) then task.defer(Local.Tag, M) end end)
		end)
	end
	-- (1.28) the three new leaders are talkable cast now (Config.Npcs Rhys / Lucien / Wren, Social.Npcs); Local.SpawnLeaders is retired
	-- (1.28) Bruno's quest crate, behind the concession stand (the stand is built at runtime by Features.Concession)
	task.spawn(function()
		for _ = 1, 60 do
			local Stand = CollectionService:GetTagged(`NHConcession`)[1]
			if Stand then
				local CF = if Stand:IsA(`Model`) then Stand:GetPivot() elseif Stand:IsA(`BasePart`) then Stand.CFrame else nil
				if CF and not workspace:FindFirstChild(`NHSnackCrate`, true) then
					local At = CF.Position - CF.LookVector * 6
					local RP = RaycastParams.new()
					RP.FilterType = Enum.RaycastFilterType.Exclude
					RP.FilterDescendantsInstances = { workspace:FindFirstChild(`Live`) or workspace.Terrain }
					local Hit = workspace:Raycast(At + Vector3.new(0, 8, 0), Vector3.new(0, -30, 0), RP)
					local Crate = Instance.new(`Part`)
					Crate.Name = `NHSnackCrate`
					Crate.Anchored = true
					Crate.Size = Vector3.new(2.4, 1.6, 1.8)
					Crate.CFrame = CFrame.new((if Hit then Hit.Position else At) + Vector3.new(0, 0.8, 0)) * CFrame.Angles(0, math.rad(12), 0)
					Crate.Color = Color3.fromRGB(120, 86, 54)
					Crate.Material = Enum.Material.WoodPlanks
					Crate:SetAttribute(`QuestObject`, `SnackCrate`)
					Crate.Parent = workspace:FindFirstChild(`NHCliqueAreas`) or workspace
				end
				return
			end
			task.wait(1)
		end
	end)

	-- Phase 1 standing: putting a clique member on the floor
	local Downed = svc(`Features.Downed`)
	if Downed and Downed.OnDowned then
		Downed.OnDowned:Connect(function(Target, Attacker)
			local P = Attacker and Players:GetPlayerFromCharacter(Attacker)
			local Id = Target and Target:GetAttribute(`Clique`)
			if P and Id and Config.Defs[Id] then
				Shared.Add(P, Id, Config.Standing.DownedMember, `You put one of theirs on the floor`)
			end
		end)
	end
end

return Shared
