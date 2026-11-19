local Report = {}
local Items = {}
table.insert(Items, { Path = {"ServerScriptService", "Services", "Features", "Homes"}; Source = [==[
--[[
	Homes (server). Services.Features.Homes          (design: docs/superpowers/specs/2026-11-06-homes-interiors-design.md)
	Config: ReplicatedStorage.Config.Homes. Saved: PlayerData.Housing (action SetHousing) = { Owned, Current, CutOff, DStreak }.

	  * Private copies. A student's home is built from ServerStorage.NHHomes.<Template> into a slot of a grid far below the
	    map (workspace.NHHomes), the first time they go in. Hallway doors (anything tagged NHHomeDoor) get an "Enter your
	    room" prompt; inside, the template's Exit part has "Leave" and, for the owner, "Send guests out". The room is
	    destroyed when its owner leaves the server (guests are sent back first).
	  * A template: a Model with a Spawn part (where you arrive, facing its front), an Exit part, TrophySpot1..4 parts
	    (where the owner's beast trophies stand), lights (any Light whose part, or the light itself, has NHHomeLight), and
	    props with the attribute NHHomeState = a comma list of states ("Spotless,Tidy"); props without it always show.
	  * The look follows the latest report card (Config.Homes.States): a new card changes it at once (ReportCards calls
	    Shared.AfterCard), with a toast if you're inside.
	  * Visitors: Classmates' "Invite to my room" (NHHomes.Invite) texts the friend; Accept on that text (Phone.TextAction)
	    brings them in (Shared.Visit).
	  * Mom & Dad (ReportCards calls Shared.Adjust before paying a card, Shared.AfterCard after the Office's text): an A adds
	    a bonus, an F or a second D in a row cuts the allowance off, a C or better brings it back.
	API: Get(p), StateOf(p), Enter(p, ownerUserId?), Leave(p), Visit(p, hostUserId), CanVisit(p, hostUserId), Invite(host, guest),
	     Adjust(p, card), AfterCard(p, card), RoomOf(p)
]]

local CollectionService = game:GetService(`CollectionService`)
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local ServerStorage = game:GetService(`ServerStorage`)

local Config = require(ReplicatedStorage.Config.Homes)

local Local = {}
local Shared = {}

local Rooms = {} :: { [number]: { Model: Model, Slot: number, Owner: number, State: string? } } -- by owner UserId
local SlotsUsed = {} :: { [number]: number }   -- slot -> owner UserId
local Inside = {} :: { [Player]: number }      -- whose room each player is in
local ReturnTo = {} :: { [Player]: CFrame }    -- where to put them when they leave
local Invites = {} :: { [string]: number }     -- "host:guest" -> os.time() sent
local LastUse = {} :: { [Player]: number }
local Folder: Folder? = nil
local Rng = Random.new()

local function svc(Path: string)
	local Node = ServerScriptService.Services
	for Part in Path:gmatch(`[^%.]+`) do Node = Node:FindFirstChild(Part) if not Node then return nil end end
	local Ok, Mod = pcall(require, Node)
	return Ok and Mod or nil
end

local function notify(P: Player, Title: string, Text: string?, Kind: string?)
	local N = svc(`Features.Notifications`)
	if N then pcall(N.Notify, P, { Title = Title; Text = Text; Kind = Kind or `Info`; Duration = 5 }) end
end

---| saved data |---

function Shared.Get(P: Player)
	local Data = svc(`Player.Data`)
	local Profile = Data and Data.GetProfile(P)
	return Profile and Config.Sanitize(Profile.Housing) or nil
end

function Local.Save(P: Player, H)
	local Data = svc(`Player.Data`)
	if Data then Data.UpdateState(P, { type = `SetHousing`; housing = H }) end
end

-- the latest report card's average letter (nil before the first card)
function Local.LastGrade(P: Player): string?
	local RC = svc(`School.ReportCards`)
	local S = RC and RC.State and RC.State(P)
	local Card = S and S.Cards and S.Cards[1]
	return Card and Card.Average or nil
end

function Shared.StateOf(P: Player)
	return Config.StateFor(Local.LastGrade(P))
end

---| building a room |---

function Local.SlotCFrame(Slot: number): CFrame
	local G = Config.Grid
	local Col, Row = Slot % G.Columns, Slot // G.Columns
	return CFrame.new(G.Origin + Vector3.new(Col * G.Spacing, 0, Row * G.Spacing))
end

function Local.FreeSlot(): number
	local S = 0
	while SlotsUsed[S] do S += 1 end
	return S
end

-- show the pieces for State, hide the rest (and remember how they looked)
function Local.ApplyState(Model: Model, StateId: string)
	local S = Config.StateById[StateId] or Config.StateById[Config.DefaultState]
	for _, D in Model:GetDescendants() do
		local List = D:GetAttribute(`NHHomeState`)
		if typeof(List) == `string` then
			local Show = false
			for Id in List:gmatch(`[^,%s]+`) do if Id == S.Id then Show = true end end
			local Parts = if D:IsA(`BasePart`) then { D } else D:GetDescendants()
			for _, X in Parts do
				if X:IsA(`BasePart`) then
					if X:GetAttribute(`NHHomeT`) == nil then X:SetAttribute(`NHHomeT`, X.Transparency) X:SetAttribute(`NHHomeC`, X.CanCollide) end
					X.Transparency = if Show then X:GetAttribute(`NHHomeT`) else 1
					X.CanCollide = Show and X:GetAttribute(`NHHomeC`) or false
					X.CanQuery = Show
				elseif X:IsA(`Decal`) or X:IsA(`Texture`) then
					if X:GetAttribute(`NHHomeT`) == nil then X:SetAttribute(`NHHomeT`, X.Transparency) end
					X.Transparency = if Show then X:GetAttribute(`NHHomeT`) else 1
				elseif X:IsA(`Light`) or X:IsA(`ParticleEmitter`) or X:IsA(`SurfaceGui`) or X:IsA(`ProximityPrompt`) then
					X.Enabled = Show
				end
			end
		end
	end
	-- the lights: brighter when it's spotless, dim (and flickering) when it's a wreck
	for _, L in Model:GetDescendants() do
		if L:IsA(`Light`) and (L:GetAttribute(`NHHomeLight`) or (L.Parent and L.Parent:GetAttribute(`NHHomeLight`))) then
			if L:GetAttribute(`NHHomeB`) == nil then L:SetAttribute(`NHHomeB`, L.Brightness) end
			L.Brightness = L:GetAttribute(`NHHomeB`) * S.Light
			L:SetAttribute(`NHFlicker`, S.Flicker or nil)
		end
	end
	Model:SetAttribute(`NHHomeState`, S.Id)
end

-- the owner's beast trophies on the trophy shelf (up to four), as small stand-ins of their locker models
function Local.Trophies(Model: Model, P: Player?)
	for _, D in Model:GetDescendants() do if D.Name == `NHTrophyShown` then D:Destroy() end end
	if not P then return end
	local Inv = svc(`Features.Inventory`)
	local Items = require(ReplicatedStorage.Config.Items)
	local I = Inv and Inv.Get(P)
	local Owned, Earned = {}, {}
	for Id, N in (I and I.Items) or {} do
		local It = Items.ById[Id]
		if It and It.Kind == `Trophy` and N > 0 then table.insert(if It.Model then Earned else Owned, It) end -- (2.33) earned ones go on the wall
	end
	table.sort(Owned, function(A, B) return (A.Order or 0) < (B.Order or 0) end)
	for K = 1, 4 do
		local Spot = Model:FindFirstChild(`TrophySpot{K}`, true)
		local It = Owned[K]
		if Spot and Spot:IsA(`BasePart`) and It and It.Prop then
			local T = Instance.new(`Part`)
			T.Name = `NHTrophyShown`
			T.Anchored, T.CanCollide, T.CanQuery, T.CanTouch = true, false, true, false
			T.Color = It.Prop.Color or Color3.new(0.8, 0.8, 0.75)
			local Shape = It.Prop.Shape
			if Shape == `Fang` then
				T.Shape = Enum.PartType.Wedge
				T.Size = Vector3.new(0.26, 0.9, 0.42)
			elseif Shape == `Locket` then
				T.Shape = Enum.PartType.Cylinder
				T.Material = Enum.Material.Metal
				T.Size = Vector3.new(0.14, 0.7, 0.7)
			else -- Bone and anything else: a long rod
				T.Shape = Enum.PartType.Cylinder
				T.Material = Enum.Material.Marble
				T.Size = Vector3.new(1.0, 0.18, 0.18)
			end
			T.CFrame = Spot.CFrame * CFrame.new(0, Spot.Size.Y / 2 + T.Size.Y / 2, 0)
			T:SetAttribute(`NHTrophy`, It.Id)
			-- the spots live on the trophy shelf, which only shows in some states: a trophy made while it's hidden starts
			-- hidden, and remembers its look so ApplyState can bring it back with the shelf
			T:SetAttribute(`NHHomeT`, 0)
			T:SetAttribute(`NHHomeC`, false)
			local Holder = Spot.Parent
			local List = Holder and Holder:GetAttribute(`NHHomeState`)
			local Now = Model:GetAttribute(`NHHomeState`)
			if typeof(List) == `string` and typeof(Now) == `string` and not (`,` .. List:gsub(`%s`, ``) .. `,`):find(`,` .. Now .. `,`, 1, true) then
				T.Transparency = 1
				T.CanQuery = false
			end
			T.Parent = Spot.Parent
		end
	end
	-- (2.33) the trophy wall: earned trophies (Config.Items.Trophies with a Model) on WallSpot1..12, as their 3D models
	-- (ReplicatedStorage.NHTrophies) scaled to fit the slot, or a simple stand-in until the models are in
	table.sort(Earned, function(A, B) return (A.Order or 0) < (B.Order or 0) end)
	local Lib = ReplicatedStorage:FindFirstChild(`NHTrophies`)
	for K = 1, 12 do
		local Spot = Model:FindFirstChild(`WallSpot{K}`, true)
		local It = Earned[K]
		if Spot and Spot:IsA(`BasePart`) and It then
			local Tpl = Lib and Lib:FindFirstChild(It.Model)
			local T
			if Tpl then
				T = Tpl:Clone()
				local _, Size = T:GetBoundingBox()
				local Fit = math.min(1.25 / math.max(Size.X, Size.Z), 1.45 / Size.Y, 1) -- (shelves 2.4 apart)
				if Fit < 0.999 then T:ScaleTo(T:GetScale() * Fit) end
				local _, Size2 = T:GetBoundingBox()
				T:PivotTo(Spot.CFrame * CFrame.new(0, Spot.Size.Y / 2, 0) * CFrame.Angles(0, math.pi, 0)) -- (pivot at the base; the models' fronts face -Z, the shelves face +Z)
				for _, D in T:GetDescendants() do if D:IsA(`BasePart`) then D.Anchored = true D.CanCollide = false D.CanTouch = false end end
			else
				T = Instance.new(`Part`)
				T.Anchored, T.CanCollide, T.CanTouch = true, false, false
				T.Material = Enum.Material.Metal
				T.Color = (It.Prop and It.Prop.Color) or Color3.fromRGB(214, 170, 90)
				T.Size = Vector3.new(0.7, 1.1, 0.7)
				T.CFrame = Spot.CFrame * CFrame.new(0, Spot.Size.Y / 2 + 0.55, 0)
			end
			T.Name = `NHTrophyShown`
			T:SetAttribute(`NHTrophy`, It.Id)
			T.Parent = Spot.Parent
		end
	end
end

function Local.Build(Owner: Player): any
	local H = Shared.Get(Owner)
	if not H then return nil end
	local Def = Config.Defs[H.Current] or Config.Defs[Config.Starter]
	local Lib = ServerStorage:FindFirstChild(`NHHomes`)
	local Tpl = Lib and Lib:FindFirstChild(Def.Template)
	if not (Tpl and Folder) then return nil end
	local Slot = Local.FreeSlot()
	local M = Tpl:Clone()
	M.Name = `Home_{Owner.UserId}`
	M:SetAttribute(`NHHomeOwner`, Owner.UserId)
	M:PivotTo(Local.SlotCFrame(Slot))
	for _, D in M:GetDescendants() do if D:IsA(`BasePart`) then D.Anchored = true end end
	M.Parent = Folder
	SlotsUsed[Slot] = Owner.UserId
	local R = { Model = M; Slot = Slot; Owner = Owner.UserId }
	Rooms[Owner.UserId] = R
	Local.Prompts(M, Owner.UserId)
	local S = Shared.StateOf(Owner)
	Local.ApplyState(M, S.Id)
	R.State = S.Id
	Local.Trophies(M, Owner)
	return R
end

-- (2.33) a trophy just won goes up at once (Services.Player.Trophies)
function Shared.RefreshTrophies(P: Player)
	local R = Rooms[P.UserId]
	if R and R.Model then pcall(Local.Trophies, R.Model, P) end
end

function Shared.RoomOf(P: Player)
	return Rooms[P.UserId] or Local.Build(P)
end

-- the Exit part's prompts: Leave (anyone), Send guests out (the owner)
function Local.Prompts(M: Model, OwnerId: number)
	local Exit = M:FindFirstChild(`Exit`, true)
	if not (Exit and Exit:IsA(`BasePart`)) then return end
	local Leave = Instance.new(`ProximityPrompt`)
	Leave.Name = `NHHomeLeave`
	Leave.ActionText = `Leave`
	Leave.ObjectText = `Door`
	Leave.HoldDuration = 0.2
	Leave.MaxActivationDistance = 8
	Leave.RequiresLineOfSight = false
	Leave.Parent = Exit
	Leave.Triggered:Connect(function(P) Shared.Leave(P) end)
	local Out = Instance.new(`ProximityPrompt`)
	Out.Name = `NHHomeGuestsOut`
	Out.ActionText = `Send guests out`
	Out.ObjectText = `Your room`
	Out.KeyboardKeyCode = Enum.KeyCode.F
	Out.GamepadKeyCode = Enum.KeyCode.ButtonY
	Out.HoldDuration = 0.6
	Out.MaxActivationDistance = 8
	Out.RequiresLineOfSight = false
	Out.UIOffset = Vector2.new(0, 72)
	Out.Parent = Exit
	Out.Triggered:Connect(function(P)
		if P.UserId ~= OwnerId then notify(P, `It's not your room`, `Only the owner can send guests out.`) return end
		local N = 0
		for G, Where in Inside do
			if Where == OwnerId and G ~= P then Shared.Leave(G) notify(G, `You were sent home`, `They wanted some time alone.`) N += 1 end
		end
		notify(P, if N > 0 then `Guests sent out` else `No guests`, nil, `Good`)
	end)
end

---| going in and out |---

function Local.Move(P: Player, To: CFrame)
	local Fx = svc(`Features.Fx`)
	if Fx and Fx.VeilMove then
		pcall(Fx.VeilMove, P, To)
	else
		local C = P.Character
		if C then C:PivotTo(To) end
	end
end

function Local.Busy(P: Player): boolean
	local C = P.Character
	local H = C and C:FindFirstChildWhichIsA(`Humanoid`)
	if not (H and H.Health > 0) then return true end
	if H:GetAttribute(`Downed`) or C:GetAttribute(`Carrying`) or C:GetAttribute(`CarriedBy`) then return true end
	if P:GetAttribute(`CombatTagUntil`) and P:GetAttribute(`CombatTagUntil`) > os.time() then return true end
	return false
end

-- into a room: your own (OwnerId nil) or a host's
function Shared.Enter(P: Player, OwnerId: number?): (boolean, string?)
	if LastUse[P] and os.clock() - LastUse[P] < 1.5 then return false, `One moment` end
	LastUse[P] = os.clock()
	if Local.Busy(P) then return false, `Not right now` end
	OwnerId = OwnerId or P.UserId
	local Owner = Players:GetPlayerByUserId(OwnerId)
	if not Owner then return false, `They've left` end
	local R = if Owner == P then Shared.RoomOf(P) else Rooms[OwnerId]
	if not R then return false, if Owner == P then `Your room isn't ready` else `Their room isn't open` end
	pcall(Local.Trophies, R.Model, Owner) -- trophies won since the room was built
	local Spawn = R.Model:FindFirstChild(`Spawn`, true)
	local To = if Spawn and Spawn:IsA(`BasePart`) then Spawn.CFrame + Vector3.new(0, 3, 0) else R.Model:GetPivot() + Vector3.new(0, 4, 0)
	-- remember the way back (only from outside, so a guest moving between rooms still returns to the hallway)
	if not Inside[P] then
		local C = P.Character
		local Root = C and C:FindFirstChild(`HumanoidRootPart`)
		if Root then ReturnTo[P] = Root.CFrame end
	end
	Inside[P] = OwnerId
	P:SetAttribute(`NHInHome`, OwnerId)
	Local.Move(P, To)
	if Owner == P then
		local S = Config.StateById[R.State or Config.DefaultState]
		notify(P, `Your dorm room`, if S then `It's {string.lower(S.Name)}, like your last report card.` else nil)
	else
		notify(Owner, `You have a guest`, nil, `Good`)
	end
	return true
end

function Shared.Leave(P: Player)
	if not Inside[P] then return end
	Inside[P] = nil
	P:SetAttribute(`NHInHome`, nil)
	local To = ReturnTo[P]
	ReturnTo[P] = nil
	if not To then
		local Door = CollectionService:GetTagged(`NHHomeDoor`)[1]
		local Pivot = Door and (if Door:IsA(`Model`) then Door:GetPivot() elseif Door:IsA(`BasePart`) then Door.CFrame else nil)
		To = if Pivot then Pivot * CFrame.new(0, 3, -4) else nil
	end
	if To then Local.Move(P, To) end
end

---| visitors |---

function Shared.CanVisit(Guest: Player, HostId: number): boolean
	local T = Invites[`{HostId}:{Guest.UserId}`]
	return T ~= nil and os.time() - T <= Config.InviteMinutes * 60 and Rooms[HostId] ~= nil and Players:GetPlayerByUserId(HostId) ~= nil
end

function Shared.Visit(Guest: Player, HostId: number): (boolean, string)
	if not Shared.CanVisit(Guest, HostId) then return false, `That invite's over.` end
	local Ok, Why = Shared.Enter(Guest, HostId)
	if not Ok then return false, Why or `You can't go right now.` end
	Invites[`{HostId}:{Guest.UserId}`] = nil
	return true, `On your way.`
end

function Shared.Invite(Host: Player, GuestId: any): (boolean, string)
	local Guest = typeof(GuestId) == `number` and Players:GetPlayerByUserId(GuestId)
	if not Guest or Guest == Host then return false, `They're not here.` end
	if not Shared.Get(Host) then return false, `Your record is still loading.` end
	Shared.RoomOf(Host) -- open it so they can come in
	Invites[`{Host.UserId}:{Guest.UserId}`] = os.time()
	local Name = `A classmate`
	pcall(function()
		local Strangers = svc(`Social.Strangers`)
		if Strangers and Strangers.Knows(Guest, Host) then
			local Identity = svc(`Player.Identity`)
			local Full = Identity and Identity.FullName(Identity.Get(Host))
			if Full and Full ~= `` then Name = Full end
		end
	end)
	local Phone = svc(`Features.Phone`)
	local Ok = Phone and Phone.AddText and Phone.AddText(Guest, {
		From = Name; Body = `Come over to my dorm room! Tap Visit (the invite lasts {Config.InviteMinutes} minutes).`; Invite = Host.UserId;
	})
	return Ok == true, if Ok then `Invite sent.` else `Couldn't send it.`
end

---| Mom & Dad and the report card |---

local function pick(List: { string }): string return List[Rng:NextInteger(1, #List)] end

-- before the card's allowance is paid: the A bonus, or nothing while cut off. Returns the allowance to pay
function Shared.Adjust(P: Player, Card)
	local H = Shared.Get(P)
	if not (H and Card) then return Card and Card.Allowance or 0 end
	local V = Config.GradeValue(Card.Average)
	local Par = Config.Parents
	local Restore = Config.GradeValue(Par.RestoreAt)
	local Mood
	if V == nil then
		Mood = if H.CutOff then `StillCut` else nil -- no graded lessons: no news from home
		if H.CutOff then Card.Allowance = 0 end
	elseif H.CutOff then
		if V >= Restore then
			H.CutOff = false
			H.DStreak = 0
			Mood = `Restored`
			if V >= 4 then Card.Allowance += Par.Bonus end
		else
			Mood = `StillCut`
			Card.Allowance = 0
			if V == 1 then H.DStreak += 1 end
		end
	elseif V == 0 then
		H.CutOff = true
		Mood = `CutOff`
		Card.Allowance = 0
	elseif V == 1 then
		H.DStreak += 1
		if H.DStreak >= Par.CutOffAfterDs then
			H.CutOff = true
			Mood = `CutOff`
			Card.Allowance = 0
		else
			Mood = `Warn`
		end
	else
		H.DStreak = 0
		Mood = if V >= 4 then `Top` elseif V == 3 then `Good` else `Fair`
		if V >= 4 then Card.Allowance += Par.Bonus end
	end
	Card.Parents = Mood
	Card.CutOff = H.CutOff or nil
	Local.Save(P, H)
	return Card.Allowance
end

-- after the Office's text: Mom & Dad's text, and the room changes to match the new card
function Shared.AfterCard(P: Player, Card)
	local Mood = Card and Card.Parents
	local Lines = Mood and Config.Parents.Lines[Mood]
	if Lines then
		local Phone = svc(`Features.Phone`)
		if Phone and Phone.AddText then pcall(Phone.AddText, P, { From = Config.Parents.From; Body = pick(Lines) }) end
	end
	local R = Rooms[P.UserId]
	local S = Config.StateFor(Card and Card.Average)
	if R and R.State ~= S.Id then
		Local.ApplyState(R.Model, S.Id)
		R.State = S.Id
		if Inside[P] == P.UserId then notify(P, `Your room looks different`, `Your report card is in.`) end
	end
end

function Shared.CutOff(P: Player): boolean
	local H = Shared.Get(P)
	return H ~= nil and H.CutOff
end

---| tests |---

function Shared.SetStateForTests(P: Player, StateId: string)
	local R = Shared.RoomOf(P)
	if not R then return false end
	Local.ApplyState(R.Model, StateId)
	R.State = StateId
	return true
end

-- the trophies now on the owner's shelf (their item ids, spot order)
function Shared.TrophiesForTests(P: Player)
	local R = Shared.RoomOf(P)
	if not R then return nil end
	Local.Trophies(R.Model, P)
	local Out = {}
	for K = 1, 4 do
		local Spot = R.Model:FindFirstChild(`TrophySpot{K}`, true)
		for _, D in (Spot and Spot.Parent or R.Model):GetChildren() do
			if D.Name == `NHTrophyShown` and Spot and (D.Position - Spot.Position).Magnitude < 1.5 then table.insert(Out, D:GetAttribute(`NHTrophy`)) end
		end
	end
	return Out
end

---| start |---

function Shared.OnStart()
	Folder = Instance.new(`Folder`)
	Folder.Name = `NHHomes`
	Folder.Parent = workspace
	local Remotes = Instance.new(`Folder`)
	Remotes.Name = `NHHomes`
	local InviteRF = Instance.new(`RemoteFunction`)
	InviteRF.Name = `Invite`
	InviteRF.Parent = Remotes
	Remotes.Parent = ReplicatedStorage
	InviteRF.OnServerInvoke = function(P, GuestId)
		if LastUse[P] and os.clock() - LastUse[P] < 1 then return false, `One moment` end
		LastUse[P] = os.clock()
		return Shared.Invite(P, GuestId)
	end

	-- hallway doors: "Enter your room"
	local function Door(D: Instance)
		if D:FindFirstChild(`NHHomePromptPart`) then return end
		-- the prompt sits on its own small part just in front of the door, at chest height (a door's own mesh can be
		-- deep inside the wall, and a door model may carry other door systems' bits)
		local CF, Size
		if D:IsA(`Model`) then CF, Size = D:GetBoundingBox() elseif D:IsA(`BasePart`) then CF, Size = D.CFrame, D.Size else return end
		local Front = D:GetAttribute(`NHHomeFront`) or -1 -- which way the door faces along its own Z (-1 = its -Z side)
		local Part = Instance.new(`Part`)
		Part.Name = `NHHomePromptPart`
		Part.Anchored, Part.CanCollide, Part.CanQuery, Part.CanTouch, Part.Transparency = true, false, false, false, 1
		Part.Size = Vector3.new(1, 1, 1)
		local Bottom = CF.Position.Y - Size.Y / 2
		Part.CFrame = CFrame.new(CF.Position.X, Bottom + 3.2, CF.Position.Z) + (CF.LookVector * Front) * (Size.Z / 2 + 1.2)
		Part.Parent = D
		local Pr = Instance.new(`ProximityPrompt`)
		Pr.Name = `NHHomeEnter`
		Pr.ActionText = `Enter your room`
		Pr.ObjectText = `Dorm`
		Pr.HoldDuration = 0.3
		Pr.MaxActivationDistance = 8
		Pr.RequiresLineOfSight = false
		Pr.Parent = Part
		Pr.Triggered:Connect(function(P)
			if P:GetAttribute(`InMainMenu`) then return end
			-- (kit 1.79) your own room needs your dorm keys (Services.Features.Kit); guests come in by invite
			local KitOk, HasKeys = pcall(function() return require(ServerScriptService.Services.Features.Kit).HasKeys(P) end)
			if KitOk and HasKeys == false then
				D:SetAttribute(`Rattle`, (D:GetAttribute(`Rattle`) or 0) + 1)
				notify(P, `The door won't open`, `Your keys are lost. The Office can cut a new set (\u{A5}50).`)
				return
			end
			if KitOk then pcall(function() require(ServerScriptService.Services.Features.Kit).KeyTurn(P) end) end
			local Ok, Why = Shared.Enter(P)
			if not Ok and Why then notify(P, Why) end
		end)
	end
	for _, D in CollectionService:GetTagged(`NHHomeDoor`) do Door(D) end
	CollectionService:GetInstanceAddedSignal(`NHHomeDoor`):Connect(Door)

	-- a room goes when its owner does (guests first); a player leaving drops their visit
	Players.PlayerRemoving:Connect(function(P)
		Inside[P], ReturnTo[P], LastUse[P] = nil, nil, nil
		local R = Rooms[P.UserId]
		if R then
			for G, Where in Inside do if Where == P.UserId then Shared.Leave(G) end end
			Rooms[P.UserId] = nil
			SlotsUsed[R.Slot] = nil
			R.Model:Destroy()
		end
		for K in Invites do if K:match(`^{P.UserId}:`) or K:match(`:{P.UserId}$`) then Invites[K] = nil end end
	end)
	-- a new save slot (back to the menu, another student): that student's room is a different one
	local function Watch(P: Player)
		P:GetAttributeChangedSignal(`Slot`):Connect(function()
			if Inside[P] then Inside[P], ReturnTo[P] = nil, nil P:SetAttribute(`NHInHome`, nil) end
			local R = Rooms[P.UserId]
			if R then
				for G, Where in Inside do if Where == P.UserId then Shared.Leave(G) end end
				Rooms[P.UserId] = nil
				SlotsUsed[R.Slot] = nil
				R.Model:Destroy()
			end
		end)
		-- dying or respawning inside a room puts you back outside
		P.CharacterAdded:Connect(function()
			if Inside[P] then Inside[P] = nil P:SetAttribute(`NHInHome`, nil) ReturnTo[P] = nil end
		end)
	end
	for _, P in Players:GetPlayers() do Watch(P) end
	Players.PlayerAdded:Connect(Watch)

	-- the flickering bulbs in a wreck of a room
	task.spawn(function()
		while true do
			task.wait(0.12)
			for _, R in Rooms do
				if R.State == `Wreck` and R.Model.Parent then
					for _, L in R.Model:GetDescendants() do
						if L:IsA(`Light`) and L:GetAttribute(`NHFlicker`) then
							local B = (L:GetAttribute(`NHHomeB`) or 1) * Config.StateById.Wreck.Light
							L.Brightness = if Rng:NextNumber() < 0.12 then B * 0.15 else B * (0.8 + Rng:NextNumber() * 0.4)
						end
					end
				end
			end
		end
	end)
end

return Shared
]==] })

for _, It in Items do
	local Fn, Err = loadstring(It.Source)
	if not Fn then return "PARSE FAIL " .. table.concat(It.Path, ".") .. ": " .. tostring(Err) end
end
for _, It in Items do
	local Node = game:GetService(It.Path[1])
	for I = 2, #It.Path - 1 do
		local Next = Node:FindFirstChild(It.Path[I])
		if not Next then Next = Instance.new("Folder") Next.Name = It.Path[I] Next.Parent = Node end
		Node = Next
	end
	local Name = It.Path[#It.Path]
	local Old = Node:FindFirstChild(Name)
	local New = Instance.new("ModuleScript")
	New.Name = Name
	New.Source = It.Source
	New.Parent = Node
	if Old then for _, K in Old:GetChildren() do K.Parent = New end Old:Destroy() end
	table.insert(Report, New:GetFullName() .. " " .. #New.Source)
end
return table.concat(Report, "\n")