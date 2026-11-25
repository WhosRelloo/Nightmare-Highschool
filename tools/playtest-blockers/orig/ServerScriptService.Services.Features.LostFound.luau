--[[
	Lost & Found (server). Services.Features.LostFound   (1.42)

	Up to MAX lost things lie about the grounds at a time (near the cliques' gathering spots, NHCliqueSpot, never in a
	Forbidden region), each with a glint and a "Pick up" prompt. Take one and you carry it in your hand (one at a time;
	Player attributes NHLostItem = id, NHLostItemText = what it is; not saved: it's dropped if you leave or go down).
	Then either:
	  - return it to its owner: any student of that clique (workspace.NHSchedule, attribute Clique). Your client shows a
	    "Return" prompt on them (Controllers.World.LostFound -> NHLostFound.Return): +5 standing with the clique and a
	    thank-you line; or
	  - hand it in at a Lost & Found box (any Model tagged NHLostFoundBox: props batch 24 LostFoundBox): Yen (more for
	    things nobody can claim).
	At most DAILY hand-ins a day each (the 6 AM event day; PlayerData.Social.LostFound { Day, N }). A taken item comes back
	somewhere else RESPAWN seconds later. Props: ServerStorage.NHProps.<Prop> (a plain stand-in block until imported).
]]
local CollectionService = game:GetService(`CollectionService`)
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local ServerStorage = game:GetService(`ServerStorage`)

local Shared = {}
local Local = {}

local MAX = 3
local RESPAWN = { 150, 300 }   -- seconds before a taken item turns up again elsewhere
local DAILY = 5
local STANDING = 5
local YEN = { Owned = 15; Unowned = 20 }
local RANGE = 10                -- studs to a student or the box

Shared.Items = {
	{ Id = `Scarf`; Prop = `LostScarf`; Name = `varsity scarf`; Text = `a varsity scarf`; Clique = `Athletes`;
		Thanks = { `My scarf! Coach would've had me running laps. Thanks.`, `No way, you found it? You're alright.` } };
	{ Id = `Sketchbook`; Prop = `LostSketchbook`; Name = `ink-stained sketchbook`; Text = `an ink-stained sketchbook`; Clique = `Ink`;
		Thanks = { `My sketches! Did you look inside? ...Don't answer that. Thank you.`, `Oh thank goodness. Half a portfolio in there.` } };
	{ Id = `Wristband`; Prop = `LostWristband`; Name = `studded wristband`; Text = `a studded wristband`; Clique = `Delinquents`;
		Thanks = { `Huh. You brought it back. Didn't have you pegged as the honest type.`, `That's mine. ...Thanks. Don't tell anyone.` } };
	{ Id = `Pendant`; Prop = `LostPendant`; Name = `wolf-tooth pendant`; Text = `a wolf-tooth pendant`; Clique = `Pack`;
		Thanks = { `My pendant. The Pack owes you one.`, `Where'd you find that? ...Thanks. It means a lot.` } };
	{ Id = `Hymnal`; Prop = `LostHymnal`; Name = `ribboned hymnal`; Text = `a ribboned hymnal`; Clique = `Choir`;
		Thanks = { `Bless you. I'd have had to sing from memory at vespers.`, `My hymnal! Thank you, truly.` } };
	{ Id = `LunchTin`; Prop = `LostLunchTin`; Name = `lunch tin`; Text = `a dented lunch tin`; Clique = `Ordinary`;
		Thanks = { `My lunch! You're the best. Want half a sandwich?`, `Oh, thank you! I thought someone took it.` } };
	{ Id = `PocketWatch`; Prop = `LostPocketWatch`; Name = `brass pocket watch`; Text = `a brass pocket watch` };
	{ Id = `Phone`; Prop = `LostPhone`; Name = `cracked phone`; Text = `a cracked phone` };
}
local ById = {}
for _, It in Shared.Items do ById[It.Id] = It end

local Loose = {} :: { [Model]: string }     -- items lying about -> id
local Carry = {} :: { [Player]: { Id: string, Held: Instance?, Down: RBXScriptConnection? } }
local Remote: RemoteFunction? = nil

local function svc(Path: string)
	local Node = ServerScriptService.Services
	for Part in Path:gmatch(`[^%.]+`) do Node = Node:FindFirstChild(Part) if not Node then return nil end end
	local Ok, Mod = pcall(require, Node)
	return Ok and Mod or nil
end
local function folder()
	local F = workspace:FindFirstChild(`NHLostFound`)
	if not F then F = Instance.new(`Folder`) F.Name = `NHLostFound` F.Parent = workspace end
	return F
end

---| the model |---

-- the prop (or a plain stand-in), anchored, not colliding, pivot at its bottom centre
function Local.Model(It): Model
	local Lib = ServerStorage:FindFirstChild(`NHProps`)
	local T = Lib and Lib:FindFirstChild(It.Prop)
	local M
	if T and T:IsA(`Model`) then
		M = T:Clone()
	else
		M = Instance.new(`Model`)
		local P = Instance.new(`Part`)
		P.Size = Vector3.new(0.9, 0.25, 0.7)
		P.Color = Color3.fromRGB(150, 120, 90)
		P.Material = Enum.Material.Fabric
		P.Parent = M
		M.PrimaryPart = P
	end
	M.Name = `Lost_{It.Id}`
	for _, P in M:GetDescendants() do
		if P:IsA(`BasePart`) then P.Anchored, P.CanCollide, P.CanTouch, P.CanQuery, P.Massless = true, false, false, true, true end
	end
	M:SetAttribute(`NHLostItem`, It.Id)
	return M
end

---| where things turn up |---

function Local.Forbidden(Pos: Vector3): boolean
	local Ok, Regions = pcall(require, ReplicatedStorage.Config.Regions)
	local Folder = workspace:FindFirstChild(`Regions`)
	if not (Ok and Folder) then return false end
	for _, B in Folder:GetChildren() do
		local Def = Regions.Defs and Regions.Defs[B:GetAttribute(`RegionId`) or B.Name] -- (audit) RegionId attribute, like the client
		if B:IsA(`BasePart`) and Def and Def.Kind == `Forbidden` then
			local L = B.CFrame:PointToObjectSpace(Pos)
			local H = B.Size / 2
			if math.abs(L.X) <= H.X and math.abs(L.Y) <= H.Y and math.abs(L.Z) <= H.Z then return true end -- (audit) abs on Y
		end
	end
	return false
end

function Local.Spot(): CFrame?
	local Spots = CollectionService:GetTagged(`NHCliqueSpot`)
	if #Spots == 0 then return nil end
	local RP = RaycastParams.new()
	RP.FilterType = Enum.RaycastFilterType.Exclude
	local Ignore = { folder() }
	for _, P in Players:GetPlayers() do if P.Character then table.insert(Ignore, P.Character) end end
	local Live = workspace:FindFirstChild(`Live`)
	if Live then table.insert(Ignore, Live) end
	local Reg = workspace:FindFirstChild(`Regions`)
	if Reg then table.insert(Ignore, Reg) end
	RP.FilterDescendantsInstances = Ignore
	for _ = 1, 24 do
		local S = Spots[math.random(1, #Spots)]
		local Base = if S:IsA(`BasePart`) then S.Position else (S:IsA(`Model`) and S:GetPivot().Position or nil)
		if Base then
			local A = math.random() * math.pi * 2
			local R = 3 + math.random() * 7
			local From = Base + Vector3.new(math.cos(A) * R, 12, math.sin(A) * R)
			local Hit = workspace:Raycast(From, Vector3.new(0, -40, 0), RP)
			if Hit and Hit.Normal.Y > 0.8 and not Local.Forbidden(Hit.Position) then
				local Clear = true
				for M in Loose do if M.Parent and (M:GetPivot().Position - Hit.Position).Magnitude < 40 then Clear = false break end end
				if Clear then return CFrame.new(Hit.Position) * CFrame.Angles(0, math.random() * math.pi * 2, 0) end
			end
		end
	end
	return nil
end

function Local.Spawn()
	local Count = 0
	for M in Loose do if M.Parent then Count += 1 end end
	if Count >= MAX then return end
	local At = Local.Spot()
	if not At then return end
	local It = Shared.Items[math.random(1, #Shared.Items)]
	local M = Local.Model(It)
	M:PivotTo(At)
	-- a faint glint so it can be spotted on the floor
	local Root = M.PrimaryPart or M:FindFirstChildWhichIsA(`BasePart`, true)
	local A = Instance.new(`Attachment`)
	A.Name = `Glint`
	A.Position = Vector3.new(0, 0.4, 0)
	A.Parent = Root
	local E = Instance.new(`ParticleEmitter`)
	E.Texture = `rbxasset://textures/particles/sparkles_main.dds`
	E.Color = ColorSequence.new(Color3.fromRGB(255, 236, 196))
	E.LightEmission = 0.6
	E.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.4, 0.22), NumberSequenceKeypoint.new(1, 0) })
	E.Transparency = NumberSequence.new(0.25)
	E.Lifetime = NumberRange.new(0.8, 1.2)
	E.Rate = 1.6
	E.Speed = NumberRange.new(0.2, 0.5)
	E.SpreadAngle = Vector2.new(180, 180)
	E.Parent = A
	local Pr = Instance.new(`ProximityPrompt`)
	Pr.Name = `NHLostPickUp`
	Pr.ActionText = `Pick up`
	Pr.ObjectText = It.Name:sub(1, 1):upper() .. It.Name:sub(2)
	Pr.HoldDuration = 0.4
	Pr.MaxActivationDistance = 8
	Pr.RequiresLineOfSight = false
	Pr.Parent = Root
	Pr.Triggered:Connect(function(P) Local.PickUp(P, M) end)
	M.Parent = folder()
	Loose[M] = It.Id
	return M
end

---| carrying |---

function Local.Notify(P: Player, Title: string, Text: string?, Kind: string?)
	local N = svc(`Features.Notifications`)
	if N then pcall(N.Notify, P, { Title = Title; Text = Text; Kind = Kind or `Info`; Duration = 5 }) end
end

function Local.Hold(P: Player, It)
	local C = P.Character
	local Hand = C and (C:FindFirstChild(`RightHand`) or C:FindFirstChild(`Right Arm`))
	if not Hand then return nil end
	local M = Local.Model(It)
	M.Name = `NHHeldLost`
	for _, Pt in M:GetDescendants() do if Pt:IsA(`BasePart`) then Pt.Anchored = false Pt.CanQuery = false end end
	local Root = M.PrimaryPart or M:FindFirstChildWhichIsA(`BasePart`, true)
	-- weld every piece to the root, the root to the hand
	for _, Pt in M:GetDescendants() do
		if Pt:IsA(`BasePart`) and Pt ~= Root then
			local W = Instance.new(`WeldConstraint`) W.Part0 = Root W.Part1 = Pt W.Parent = Pt
		end
	end
	M:PivotTo(Hand.CFrame * CFrame.new(0, -(Hand.Size.Y / 2) - 0.05, -0.15) * CFrame.Angles(math.rad(-90), 0, 0))
	local W = Instance.new(`WeldConstraint`)
	W.Part0 = Hand W.Part1 = Root W.Parent = Root
	M.Parent = C
	return M
end

function Local.Drop(P: Player)
	local C = Carry[P]
	Carry[P] = nil
	if C and C.Down then C.Down:Disconnect() end -- (audit)
	if C and C.Held and C.Held.Parent then C.Held:Destroy() end
	if P.Parent then
		P:SetAttribute(`NHLostItem`, nil)
		P:SetAttribute(`NHLostItemText`, nil)
		P:SetAttribute(`NHLostItemClique`, nil)
	end
end

function Local.PickUp(P: Player, M: Model)
	if not (M.Parent and Loose[M]) then return end
	if P:GetAttribute(`InMainMenu`) == true then return end
	if Carry[P] then Local.Notify(P, `Your hands are full`, `Return what you're carrying first.`) return end
	local It = ById[Loose[M]]
	local Root = P.Character and P.Character:FindFirstChild(`HumanoidRootPart`)
	if not (It and Root) or (Root.Position - M:GetPivot().Position).Magnitude > RANGE then return end
	-- (audit) not while down; going down later drops it (below)
	local Hum = P.Character:FindFirstChildOfClass(`Humanoid`)
	if Hum and Hum:GetAttribute(`Downed`) then return end
	Loose[M] = nil
	M:Destroy()
	Carry[P] = { Id = It.Id; Held = Local.Hold(P, It) }
	-- (audit) going down (the Humanoid's Downed attribute) drops it, as the header says
	if Hum then
		local Rec = Carry[P]
		Rec.Down = Hum:GetAttributeChangedSignal(`Downed`):Connect(function()
			if Hum:GetAttribute(`Downed`) and Carry[P] == Rec then Local.Drop(P) end
		end)
	end
	P:SetAttribute(`NHLostItem`, It.Id)
	local Owner = It.Clique and require(ReplicatedStorage.Config.Cliques).Defs[It.Clique]
	P:SetAttribute(`NHLostItemText`, if Owner then `{It.Text} ({Owner.Name})` else It.Text)
	P:SetAttribute(`NHLostItemClique`, It.Clique)
	Local.Notify(P, `You found {It.Text}`, if Owner then `It belongs to {Owner.Name}. Return it to one of them, or hand it in at the Lost & Found.`
		else `Nobody's name is on it. Hand it in at the Lost & Found.`)
	task.delay(math.random(RESPAWN[1], RESPAWN[2]), function() pcall(Local.Spawn) end)
end

---| handing it back |---

function Local.Daily(P: Player)
	local Rep = svc(`Social.Reputation`)
	local Social = Rep and Rep.Get(P)
	if not Social then return nil end
	local Day = 0
	pcall(function() Day = require(ReplicatedStorage.Config.Cliques).EventDay(svc(`School.SchoolClock`).GetState()) or 0 end)
	local L = Social.LostFound
	if typeof(L) ~= `table` or L.Day ~= Day then L = { Day = Day; N = 0 } Social.LostFound = L end
	return L, Rep
end

-- give the carried item to Student (a member of its clique): standing, a thank-you
function Shared.Return(P: Player, Student: Instance?): (boolean, string?)
	local C = Carry[P]
	local It = C and ById[C.Id]
	if not (It and It.Clique) then return false, `You're not carrying anything with an owner.` end
	if not (typeof(Student) == `Instance` and Student:IsA(`Model`) and Student:GetAttribute(`Clique`) == It.Clique) then return false, `That's not theirs.` end
	local R = Student:FindFirstChild(`HumanoidRootPart`)
	local Me = P.Character and P.Character:FindFirstChild(`HumanoidRootPart`)
	if not (R and Me) or (R.Position - Me.Position).Magnitude > RANGE + 4 then return false, `Get closer.` end
	local L, Rep = Local.Daily(P)
	if not L then return false, `Your record isn't loaded yet.` end
	if L.N >= DAILY then return false, `You've handed in {DAILY} things today. Try again tomorrow.` end
	L.N += 1
	Rep.Sync(P)
	Local.Drop(P)
	local Cl = svc(`Social.Cliques`)
	if Cl and Cl.Add then pcall(Cl.Add, P, It.Clique, STANDING, `You returned their lost {It.Name}`) end
	if Cl and Cl.SayTo then pcall(Cl.SayTo, P, Student, It.Thanks[math.random(1, #It.Thanks)]) end
	Local.Notify(P, `Returned: {It.Text}`, `+{STANDING} standing with {require(ReplicatedStorage.Config.Cliques).Defs[It.Clique].Name}.`, `Good`)
	return true, nil
end

-- hand the carried item in at a Lost & Found box: Yen
function Shared.HandIn(P: Player, Box: Instance?): (boolean, string?)
	local C = Carry[P]
	local It = C and ById[C.Id]
	if not It then return false, `You're not carrying anything lost.` end
	local Me = P.Character and P.Character:FindFirstChild(`HumanoidRootPart`)
	if not (Me and Box and (Box:GetPivot().Position - Me.Position).Magnitude <= RANGE + 6) then return false, `Get closer to the box.` end
	local L, Rep = Local.Daily(P)
	if not L then return false, `Your record isn't loaded yet.` end
	if L.N >= DAILY then return false, `You've handed in {DAILY} things today. Try again tomorrow.` end
	L.N += 1
	Rep.Sync(P)
	Local.Drop(P)
	local Pay = if It.Clique then YEN.Owned else YEN.Unowned
	local Data = svc(`Player.Data`)
	if Data then Data.UpdateState(P, { type = `UpdateYen`; amount = Pay }) end
	Local.Notify(P, `Handed in: {It.Text}`, `The Lost & Found pays \u{A5}{Pay} for honesty.`, `Good`)
	return true, nil
end

function Local.Box(M: Instance)
	local At = if M:IsA(`Model`) then (M.PrimaryPart or M:FindFirstChildWhichIsA(`BasePart`, true)) else M
	if not (At and At:IsA(`BasePart`)) or At:FindFirstChild(`NHLostHandIn`) then return end
	local Pr = Instance.new(`ProximityPrompt`)
	Pr.Name = `NHLostHandIn`
	Pr.ActionText = `Hand in`
	Pr.ObjectText = `Lost & Found`
	Pr.HoldDuration = 0.3
	Pr.MaxActivationDistance = 9
	Pr.RequiresLineOfSight = false
	Pr.Parent = At
	Pr.Triggered:Connect(function(P)
		local Ok, Why = Shared.HandIn(P, M)
		if not Ok and Why then Local.Notify(P, Why) end
	end)
end

---| tests |---

function Shared.SpawnForTests(Id: string?, At: CFrame?)
	local It = Id and ById[Id]
	if It and At then
		local M = Local.Model(It)
		M:PivotTo(At)
		local Root = M.PrimaryPart or M:FindFirstChildWhichIsA(`BasePart`, true)
		local Pr = Instance.new(`ProximityPrompt`)
		Pr.Name = `NHLostPickUp` Pr.ActionText = `Pick up` Pr.ObjectText = It.Name Pr.HoldDuration = 0.4 Pr.MaxActivationDistance = 8 Pr.RequiresLineOfSight = false
		Pr.Parent = Root
		Pr.Triggered:Connect(function(P) Local.PickUp(P, M) end)
		M.Parent = folder()
		Loose[M] = It.Id
		return M
	end
	return Local.Spawn()
end
function Shared.PickUpForTests(P: Player, M: Model) Local.PickUp(P, M) return P:GetAttribute(`NHLostItem`) end
-- the items lying about now (Features.Fortune's hints): { Id, Pos, Text, Clique? }
function Shared.Loose()
	local L = {}
	for M, Id in Loose do
		local It = ById[Id]
		if M.Parent and It then table.insert(L, { Id = Id; Pos = M:GetPivot().Position; Text = It.Text; Clique = It.Clique }) end
	end
	return L
end

function Shared.State()
	local L = {}
	for M, Id in Loose do if M.Parent then table.insert(L, { Id = Id; At = tostring(M:GetPivot().Position) }) end end
	local C = {}
	for P, Cc in Carry do C[P.Name] = Cc.Id end
	return { Loose = L; Carrying = C }
end

---| start |---

function Shared.OnStart()
	local F = Instance.new(`Folder`)
	F.Name = `NHLostFound`
	local R = Instance.new(`RemoteFunction`)
	R.Name = `Return`
	R.Parent = F
	F.Parent = ReplicatedStorage
	Remote = R
	local Last = {} :: { [Player]: number }
	R.OnServerInvoke = function(P, Student)
		if Last[P] and os.clock() - Last[P] < 0.8 then return false, nil end
		Last[P] = os.clock()
		local Ok, Why = Shared.Return(P, Student)
		if not Ok and Why then Local.Notify(P, Why) end
		return Ok
	end
	-- carrying ends if you leave, respawn or go down
	Players.PlayerRemoving:Connect(function(P) Local.Drop(P) Last[P] = nil end)
	Players.PlayerAdded:Connect(function(P) P.CharacterAdded:Connect(function() if Carry[P] then Local.Drop(P) end end) end)
	for _, P in Players:GetPlayers() do P.CharacterAdded:Connect(function() if Carry[P] then Local.Drop(P) end end) end
	for _, M in CollectionService:GetTagged(`NHLostFoundBox`) do pcall(Local.Box, M) end
	CollectionService:GetInstanceAddedSignal(`NHLostFoundBox`):Connect(function(M) task.defer(function() pcall(Local.Box, M) end) end)
	task.delay(20, function()
		for _ = 1, MAX do pcall(Local.Spawn) end
		-- top up now and then (a spot may not have been found earlier)
		while true do
			task.wait(120)
			pcall(Local.Spawn)
		end
	end)
end

return Shared
