--[[
	Hall monitors (server)

	States: Off (off duty, waits at spawn) | Patrol | Chase | Confront
	- On duty during Config.Discipline.HallMonitor.DutyKinds segments.
	- During Class periods, a student in sight (range + field of view + no wall in the way)
	  who isn't in their classroom is chased. Caught = Truancy violation. Escaping (out of
	  sight, too far, or chase timeout) is logged as an unrecognised incident: no punishment.
	  A student who goes into class during the chase is let go.
	- Fights: any combat hit by a student that a monitor can see (no FOV needed: fights are
	  noisy). Recognised (close enough) = Fighting violation right away; otherwise the monitor
	  investigates (chases) and a catch counts.
	- Never permanently stuck: no progress -> jump; waypoint timeout -> skip waypoint;
	  twice the timeout -> teleport to the waypoint.
	- Monitors can be downed/killed like any NPC. They stop working while downed and respawn
	  after RespawnSeconds if killed.
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local CollectionService = game:GetService(`CollectionService`)

---| Modules |---

local Config = require(ReplicatedStorage.Config.Discipline)
local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local SignalPlus = require(ReplicatedStorage.Packages.SignalPlus)

local SchoolClock = require(ServerScriptService.Services.School.SchoolClock)
local Discipline = require(ServerScriptService.Services.School.Discipline)
local Notifications = require(ServerScriptService.Services.Features.Notifications)
local Fx = require(ServerScriptService.Services.Features.Fx) -- VFX P0-9 "Spotted!" (client Controllers.World.Spotted)
local Downed = require(ServerScriptService.Services.Features.Downed)
local EntityLoader = require(ServerScriptService.Services.Managers.EntityLoader)

local Settings = Config.HallMonitor
local TICK = 0.2

local Monitors = {} :: { any }
local Caught = {} :: { [Player]: { [string]: string } } -- per player: violation type -> period key already punished
local LastFightReport = {} :: { [Player]: number }

local Local = {}
local Shared = {}

Shared.Escaped = SignalPlus() -- (Player, Reason)
Shared.Caught = SignalPlus()  -- (Player, Reason, Excused)
-- Optional: function(Player, Reason) -> (punish: boolean, line: string?). Set by Factions (Vigil Pass).
Shared.CatchFilter = nil :: ((Player, string) -> (boolean, string?))?

---| Helpers |---

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
function Local.Flat(V: Vector3): Vector3
	return Vector3.new(V.X, 0, V.Z)
end

function Local.GetSchool(): Folder?
	return workspace:FindFirstChild(`School`) :: Folder?
end

function Local.GetRoute(): { BasePart }
	local School = Local.GetSchool()
	local Folder = School and School:FindFirstChild(`PatrolRoute`)
	local Route = {}
	if Folder then
		for _, Part in Folder:GetChildren() do
			if Part:IsA(`BasePart`) then table.insert(Route, Part) end
		end
		table.sort(Route, function(A, B) return A.Name < B.Name end)
	end
	return Route
end

function Local.IsActive(M): boolean
	if not M.Model or not M.Model.Parent then return false end
	if not M.Humanoid or M.Humanoid.Health <= 0 then return false end
	return not StateManager.HasState(M.Model, { `Downed`, `Carried`, `Gripped`, `Stun`, `ParryStun`, `Paralyzed` })
end

function Local.Say(M, Text: string)
	local Bubble = M.Bubble
	if not Bubble then return end
	Bubble.Label.Text = Text
	Bubble.Enabled = true
	M.SayToken = (M.SayToken or 0) + 1
	local Token = M.SayToken
	task.delay(2.5, function()
		if M.SayToken == Token and Bubble.Parent then Bubble.Enabled = false end
	end)
end

-- Line of sight from the monitor's head to the character, ignoring all characters.
function Local.CanSee(M, Character: Model, UseFieldOfView: boolean): (boolean, number)
	local Head = M.Model:FindFirstChild(`Head`) :: BasePart?
	local Root = Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	if not Head or not Root then return false, math.huge end

	local Offset = Root.Position - Head.Position
	local Distance = Offset.Magnitude
	if Distance > Settings.SightRange then return false, Distance end

	if UseFieldOfView then
		local Look = Local.Flat(M.Root.CFrame.LookVector)
		local Dir = Local.Flat(Offset)
		if Look.Magnitude > 0 and Dir.Magnitude > 0 then
			local Angle = math.deg(math.acos(math.clamp(Look.Unit:Dot(Dir.Unit), -1, 1)))
			if Angle > Settings.FieldOfView / 2 then return false, Distance end
		end
	end

	local Params = RaycastParams.new()
	Params.FilterType = Enum.RaycastFilterType.Exclude
	-- (audit) skip every character / invisible folder (the list Substitutes uses), not just Live
	local Ignore = {}
	for _, F in { `Live`, `NHSchedule`, `NHAmbient`, `NHSubstitutes`, `Regions`, `NHFx` } do local X = workspace:FindFirstChild(F) if X then table.insert(Ignore, X) end end
	Params.FilterDescendantsInstances = Ignore
	local Hit = workspace:Raycast(Head.Position, Offset, Params)
	return Hit == nil, Distance
end

-- (2.8.1) a student on Probation or Suspension is known on sight from farther away (Config.Discipline.Record)
function Local.RecognizeRange(Player: Player): number
	local Level = Player:GetAttribute(`DisciplineLevel`)
	if Level == `Probation` or Level == `Suspension` then
		return math.max(Config.Witness.RecognizeRange, Config.Record.ProbationRecognizeRange)
	end
	return Config.Witness.RecognizeRange
end

-- (2.8.1) inside the school (any Config.Regions place of Kind School), where a suspended student may not be in class time
function Local.OnCampus(Player: Player): boolean
	local Ok, Regions = pcall(require, ServerScriptService.Services.Features.Regions)
	local Ok2, Defs = pcall(require, ReplicatedStorage.Config.Regions)
	if not (Ok and Ok2 and Regions and Defs and Defs.Defs) then return false end
	for Id, Def in Defs.Defs do
		if Def.Kind == `School` and Regions.Inside(Player, Id) then return true end
	end
	-- the school building itself: workspace.School's rooms (R101...) and halls (Hallway...), up to a storey high. In NH Combat
	-- Test the region boxes sit above the greybox school, so this is what finds you in its hallway
	local School = Local.GetSchool()
	local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	if School and Root then
		for _, M in School:GetChildren() do
			if M:IsA(`Model`) and (M.Name:match(`^R%d+$`) or M.Name:match(`^Hallway`)) then
				local CF, Size = M:GetBoundingBox()
				local L = CF:PointToObjectSpace(Root.Position)
				if math.abs(L.X) <= Size.X / 2 and math.abs(L.Z) <= Size.Z / 2 and L.Y >= -Size.Y / 2 - 2 and L.Y <= Size.Y / 2 + 14 then return true end
			end
		end
	end
	return false
end

-- (2.8.1) a suspended student on campus during class: Trespassing (once a period)
function Local.IsTrespassing(Player: Player, State): boolean
	if State.Segment.Kind ~= `Class` or Player:GetAttribute(`Suspended`) ~= true then return false end
	local Character = Player.Character
	local Humanoid = Character and Character:FindFirstChildWhichIsA(`Humanoid`)
	if not Humanoid or Humanoid.Health <= 0 or Humanoid:GetAttribute(`Downed`) then return false end
	if Caught[Player] and Caught[Player].Trespassing == Local.PeriodKey(State) then return false end
	return Local.OnCampus(Player)
end

function Local.PeriodKey(State): string
	return `D{State.Day}-S{State.SegmentIndex}`
end

-- Parts tagged "CombatAllowed" (CollectionService) mark places where fighting is fine
-- (e.g. a gym sparring ring). No violation there.
function Local.InCombatAllowedZone(Position: Vector3): boolean
	for _, Part in CollectionService:GetTagged(`CombatAllowed`) do
		if Part:IsA(`BasePart`) then
			local Local3 = Part.CFrame:PointToObjectSpace(Position)
			local Half = Part.Size / 2
			if math.abs(Local3.X) <= Half.X and math.abs(Local3.Y) <= Half.Y and math.abs(Local3.Z) <= Half.Z then
				return true
			end
		end
	end
	return false
end

-- Is this student breaking the truancy rule right now?
function Local.IsTruant(Player: Player, State): boolean
	if State.Segment.Kind ~= `Class` then return false end
	if Player:GetAttribute(`Suspended`) == true then return false end
	if Player:GetAttribute(`ClassRoom`) == nil then return false end -- attendance isn't tracking them
	if Player:GetAttribute(`ClassInRoom`) == true then return false end
	-- (kit 1.79) a hall pass shown this period (Services.Features.Kit): left alone, but no attendance
	if (Player:GetAttribute(`NHPassUntil`) or 0) > workspace:GetServerTimeNow() then return false end

	local Character = Player.Character
	local Humanoid = Character and Character:FindFirstChildWhichIsA(`Humanoid`)
	if not Humanoid or Humanoid.Health <= 0 or Humanoid:GetAttribute(`Downed`) then return false end

	local Already = Caught[Player] and Caught[Player].Truancy
	return Already ~= Local.PeriodKey(State)
end

---| Movement |---

function Local.MoveTowards(M, Position: Vector3): number
	local Now = os.clock()
	M.Humanoid:MoveTo(Position)

	local Distance = Local.Flat(M.Root.Position - Position).Magnitude
	if Distance < (M.BestDistance or math.huge) - 0.5 then
		M.BestDistance = Distance
		M.LastProgress = Now
	elseif Now - (M.LastProgress or Now) > 2 then
		M.Humanoid.Jump = true
	end
	return Distance
end

function Local.ResetProgress(M)
	M.BestDistance = math.huge
	M.LastProgress = os.clock()
end

function Local.NearestWaypoint(M, Route): number
	local Best, BestDistance = 1, math.huge
	for Index, Part in Route do
		local Distance = (Part.Position - M.Root.Position).Magnitude
		if Distance < BestDistance then Best, BestDistance = Index, Distance end
	end
	return Best
end

---| States |---

function Local.SetState(M, State: string)
	-- (audit) pulled out of Respond another way (a chase, off duty): still run the callback, as the 30 s give-up does,
	-- so the scuffle isn't left waiting for a monitor that never comes
	if M.State == `Respond` and State ~= `Respond` and M.RespondDone then
		local Done = M.RespondDone
		M.RespondDone = nil
		task.defer(Done)
	end
	M.State = State
	M.Model:SetAttribute(`MonitorState`, State)
	if State ~= `Chase` then M.Model:SetAttribute(`MonitorTarget`, nil) end -- the chased student's alert clears on every exit
	Local.ResetProgress(M)
end

function Local.StartChase(M, Player: Player, Reason: string)
	M.Target = Player
	M.Reason = Reason
	M.ChaseStart = os.clock()
	M.LastSeen = os.clock()
	M.ChaseOrigin = M.Root.Position
	M.Humanoid.WalkSpeed = Settings.ChaseSpeed
	Local.SetState(M, `Chase`)
	M.Model:SetAttribute(`MonitorTarget`, Player.UserId)
	M.Model:SetAttribute(`MonitorChaseAt`, os.clock()) -- (kit 1.79) the pass works only in the first seconds
	M.Model:SetAttribute(`MonitorReason`, Reason) -- (inventory audit 1.90) the hall pass only covers Truancy
	Fx.Fire(Player, `Spotted`, { Monitor = M.Model; Reason = Reason })
	Local.Say(M, if Reason == `Fighting` then `Hey! Stop right there!`
		elseif Reason == `Vandalism` then `Hey! Put that paint down!`
		elseif Reason == `Trespassing` then `You're suspended! Off school grounds!`
		else `You! Why aren't you in class?`)
end

function Local.EndChase(M)
	M.Target = nil
	M.Reason = nil
	M.Humanoid.WalkSpeed = Settings.WalkSpeed
	local Route = Local.GetRoute()
	if #Route > 0 then M.Index = Local.NearestWaypoint(M, Route) end
	Local.SetState(M, `Patrol`)
end

function Local.Catch(M, Player: Player, State)
	local Reason = M.Reason or `Truancy`
	Caught[Player] = Caught[Player] or {}
	Caught[Player][Reason] = Local.PeriodKey(State)

	local Punish, Line = true, nil
	if Shared.CatchFilter then
		local Ok, P, L = pcall(Shared.CatchFilter, Player, Reason)
		if Ok and P == false then Punish, Line = false, L end
	end

	if Punish then
		Local.Say(M, if Reason == `Fighting` then `No fighting on school grounds!`
			elseif Reason == `Vandalism` then `Painting on the walls? You're done.`
			elseif Reason == `Trespassing` then `Suspended means off campus. This goes on your record.`
			else `Get to class! This is going on your record.`)
		Discipline.ReportIncident({
			Type = Reason;
			Suspect = Player;
			Witness = `Hall Monitor`;
			Position = M.Root.Position;
			Recognized = true;
		})
	else
		Local.Say(M, Line or `...Just this once.`)
	end
	Fx.Fire(Player, `SpottedEnd`, { Monitor = M.Model; Result = if Punish then `Caught` else `LetOff` })
	Shared.Caught:Fire(Player, Reason, not Punish)

	M.Target = nil
	M.ConfrontUntil = os.clock() + 2
	Local.SetState(M, `Confront`)
end

function Local.UpdateMonitor(M, State)
	if not Local.IsActive(M) then
		if M.State == `Chase` then M.Target = nil M.Model:SetAttribute(`MonitorTarget`, nil) end
		return
	end

	local OnDuty = Settings.DutyKinds[State.Segment.Kind] == true
	local Route = Local.GetRoute()

	if not OnDuty then
		if M.State ~= `Off` then
			M.Target = nil
			M.Humanoid.WalkSpeed = Settings.WalkSpeed
			Local.SetState(M, `Off`)
		end
		if M.Spawn and Local.MoveTowards(M, M.Spawn.Position) > 3 and os.clock() - M.LastProgress > Settings.WaypointTimeout * 2 then
			M.Model:PivotTo(M.Spawn.CFrame)
			Local.ResetProgress(M)
		end
		return
	end

	if M.State == `Off` then
		M.Index = if #Route > 0 then Local.NearestWaypoint(M, Route) else 1
		Local.SetState(M, `Patrol`)
	end

	if M.State == `Confront` then
		if os.clock() >= (M.ConfrontUntil or 0) then
			Local.EndChase(M)
		end
		return
	end

	-- (1.27) on the way to break up a clique scuffle (Social.CliqueFights)
	if M.State == `Respond` then
		local Distance = Local.MoveTowards(M, M.RespondAt)
		if Distance <= 14 or os.clock() > (M.RespondUntil or 0) then
			local Done = M.RespondDone
			M.RespondDone = nil
			if Distance <= 14 then Local.Say(M, `Break it up! All of you, move along!`) end
			if Done then task.spawn(Done) end
			Local.EndChase(M)
		end
		return
	end

	if M.State == `Chase` then
		local Player = M.Target
		local Character = Player and Player.Parent and Player.Character
		local Root = Character and Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
		local Humanoid = Character and Character:FindFirstChildWhichIsA(`Humanoid`)

		if not Root or not Humanoid or Humanoid.Health <= 0 or Humanoid:GetAttribute(`Downed`) then
			Local.EndChase(M)
			return
		end

		-- (2.8.1) a suspended trespasser who leaves the school: job done
		if M.Reason == `Trespassing` and not Local.IsTrespassing(Player, State) then
			Local.Say(M, `And stay out.`)
			Local.EndChase(M)
			return
		end

		-- Went to class: job done.
		if M.Reason == `Truancy` and not Local.IsTruant(Player, State) then
			Local.Say(M, if (Player:GetAttribute(`NHPassUntil`) or 0) > workspace:GetServerTimeNow() then `Carry on.` else `That's more like it.`)
			Local.EndChase(M)
			return
		end

		local Visible = Local.CanSee(M, Character, false)
		if Visible then M.LastSeen = os.clock() end

		local Distance = Local.MoveTowards(M, Root.Position)
		if Distance <= Settings.CatchRange then
			Local.Catch(M, Player, State)
			return
		end

		-- Crimson Court "Shadowstep" perk: monitors lose track twice as fast.
		local LoseSight = Settings.LoseSightSeconds * (if Player:GetAttribute(`Perk_Shadowstep`) then 0.5 else 1)
		local Escaped = os.clock() - M.ChaseStart > Settings.GiveUpSeconds
			or os.clock() - M.LastSeen > LoseSight
			or (M.Root.Position - M.ChaseOrigin).Magnitude > Settings.MaxChaseDistance

		if Escaped then
			Discipline.ReportIncident({
				Type = M.Reason;
				Suspect = Player;
				Witness = `Hall Monitor`;
				Position = Root.Position;
				Recognized = false; -- got away: can't be pinned on them later
			})
			Notifications.Notify(Player, { Title = `You slipped away from the hall monitor`; Kind = `Info`; Duration = 4 })
			Fx.Fire(Player, `SpottedEnd`, { Monitor = M.Model; Result = `Escaped` })
			Local.Say(M, `...Where did they go?`)
			local Reason = M.Reason
			Local.EndChase(M)
			Shared.Escaped:Fire(Player, Reason)
		end
		return
	end

	-- Patrol: look for truants first.
	if State.Segment.Kind == `Class` then
		local Best, BestDistance, BestWhy = nil, math.huge, nil
		for _, Player in Players:GetPlayers() do
			if not Player.Character then continue end
			local Why = if Local.IsTruant(Player, State) then `Truancy` elseif Local.IsTrespassing(Player, State) then `Trespassing` else nil -- (2.8.1)
			if not Why then continue end
			local Visible, Distance = Local.CanSee(M, Player.Character, true)
			if Visible and Distance < BestDistance then
				Best, BestDistance, BestWhy = Player, Distance, Why
			end
		end
		if Best then
			Local.StartChase(M, Best, BestWhy or `Truancy`)
			return
		end
	end

	if #Route == 0 then return end
	M.Index = M.Index or 1
	local Waypoint = Route[M.Index]
	local Distance = Local.MoveTowards(M, Waypoint.Position)
	local Stalled = os.clock() - M.LastProgress

	if Distance < 4 or Stalled > Settings.WaypointTimeout then
		if Distance >= 4 and Stalled > Settings.WaypointTimeout * 2 then
			M.Model:PivotTo(Waypoint.CFrame) -- last resort: never stay stuck
		end
		if Distance < 4 or Stalled > Settings.WaypointTimeout * 2 then
			M.Index = (M.Index % #Route) + 1
		end
		Local.ResetProgress(M)
	end
end

---| Fights |---

function Local.OnDamage(Target: Model, Damage: number, Attacker: Model?)
	if not Attacker then return end
	local Player = Players:GetPlayerFromCharacter(Attacker)
	if not Player then return end

	local Now = os.clock()
	if LastFightReport[Player] and Now - LastFightReport[Player] < Config.Witness.FightCooldown then return end

	local Root = Attacker:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	if not Root or Local.InCombatAllowedZone(Root.Position) then return end

	local State = SchoolClock.GetState()
	for _, M in Monitors do
		if not Local.IsActive(M) or not Settings.DutyKinds[State.Segment.Kind] then continue end

		local Visible, Distance = Local.CanSee(M, Attacker, false)
		if not Visible then continue end

		LastFightReport[Player] = Now
		if Distance <= Local.RecognizeRange(Player) then -- (2.8.1) farther on Probation / Suspension
			Local.Say(M, `I saw that! No fighting!`)
			Discipline.ReportIncident({
				Type = `Fighting`; Suspect = Player; Witness = `Hall Monitor`;
				Position = Root.Position; Recognized = true;
			})
			-- (2.14.0, combat concept 16) brass knuckles are contraband: a monitor who sees you fight with them takes them
			if Attacker:GetAttribute(`NHGear`) == `BrassKnuckles` then
				local Took = false
				pcall(function() Took = require(game:GetService(`ServerScriptService`).Services.Features.Armory).Confiscate(Player, `BrassKnuckles`) end)
				if Took then
					task.delay(1.6, function() Local.Say(M, `And I'll take those knuckles.`) end)
					Discipline.ReportIncident({
						Type = `Contraband`; Suspect = Player; Witness = `Hall Monitor`;
						Position = Root.Position; Recognized = true;
					})
				end
			end
		elseif M.State ~= `Chase` and M.State ~= `Respond` then -- (2.7.3) already on its way to a fight: it keeps going
			Local.StartChase(M, Player, `Fighting`) -- too far to recognise: investigate
		end
		return
	end
end

---| Spawning |---

function Local.Spawn(Slot: number)
	local School = Local.GetSchool()
	local Spawn = School and School:FindFirstChild(`MonitorSpawn`) :: BasePart?
	local AIFolder = ServerScriptService.Services.AI.AI
	if not Spawn then
		warn(`[HallMonitor] workspace.School.MonitorSpawn missing`)
		return
	end

	local Model = AIFolder.Rig:Clone()
	Model.Name = `Hall Monitor`
	Model:SetAttribute(`Role`, `HallMonitor`)

	local Animate = AIFolder.Animate:Clone()
	Animate.Parent = Model
	Animate.Enabled = true

	Model:PivotTo(Spawn.CFrame + Vector3.new((Slot - 1) * 3, 0, 0))
	Model.Parent = workspace.Live
	EntityLoader.OnCharacterAdded(Model)
	do -- a full look (face art, outfit, hair): Services.Features.NpcLooks
		local Looks = require(game:GetService(`ServerScriptService`).Services.Features.NpcLooks)
		task.spawn(Looks.Apply, Model, Looks.Specs.HallMonitor)
	end

	local Humanoid = Model:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	local Root = Model:FindFirstChild(`HumanoidRootPart`) :: BasePart
	Humanoid.WalkSpeed = Settings.WalkSpeed
	Humanoid.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	pcall(function() Root:SetNetworkOwner(nil) end)

	-- Name tag + speech bubble
	local Tag = Instance.new(`BillboardGui`)
	Tag.Name = `NameTag`
	Tag.Size = UDim2.new(0, 140, 0, 22)
	Tag.StudsOffset = Vector3.new(0, 2.6, 0)
	Tag.MaxDistance = 80
	local TagLabel = Instance.new(`TextLabel`)
	TagLabel.Size = UDim2.fromScale(1, 1)
	TagLabel.BackgroundTransparency = 1
	TagLabel.Font = Enum.Font.GothamBold
	TagLabel.TextSize = 14
	TagLabel.TextColor3 = Color3.fromRGB(255, 214, 102)
	TagLabel.TextStrokeTransparency = 0.4
	TagLabel.Text = `Hall Monitor`
	TagLabel.Parent = Tag
	Tag.Parent = Model:FindFirstChild(`Head`)

	local Bubble = Instance.new(`BillboardGui`)
	Bubble.Name = `Speech`
	Bubble.Size = UDim2.new(0, 220, 0, 40)
	Bubble.StudsOffset = Vector3.new(0, 4.5, 0)
	Bubble.MaxDistance = 80
	Bubble.Enabled = false
	local BubbleLabel = Instance.new(`TextLabel`)
	BubbleLabel.Name = `Label`
	BubbleLabel.Size = UDim2.fromScale(1, 1)
	BubbleLabel.BackgroundColor3 = Color3.new(1, 1, 1)
	BubbleLabel.Font = Enum.Font.GothamBold
	BubbleLabel.TextSize = 14
	BubbleLabel.TextWrapped = true
	BubbleLabel.TextColor3 = Color3.fromRGB(20, 20, 20)
	BubbleLabel.Parent = Bubble
	local Corner = Instance.new(`UICorner`)
	Corner.CornerRadius = UDim.new(0, 8)
	Corner.Parent = BubbleLabel
	Bubble.Parent = Model:FindFirstChild(`Head`)

	local M = {
		Slot = Slot; Model = Model; Humanoid = Humanoid; Root = Root; Spawn = Spawn; Bubble = Bubble;
		State = `Off`; Index = 1; Target = nil; Reason = nil;
	}
	Local.ResetProgress(M)
	Model:SetAttribute(`MonitorState`, `Off`)
	Monitors[Slot] = M

	Humanoid.Died:Connect(function()
		task.delay(Settings.RespawnSeconds, function()
			if Monitors[Slot] == M then
				if Model.Parent then Model:Destroy() end
				Local.Spawn(Slot)
			end
		end)
	end)
end

---| API |---

-- Did an on-duty monitor see this player do something (e.g. mark a wall)?
-- Returns "Recognized" (close enough: punished now), "Spotted" (seen from afar: the monitor
-- comes to investigate; a catch counts) or nil (unseen).
function Shared.CheckWitness(Player: Player, Reason: string, RecognizeRange: number?): string?
	local Character = Player.Character
	if not Character then return nil end
	local State = SchoolClock.GetState()
	if not Settings.DutyKinds[State.Segment.Kind] then return nil end

	local Range = math.max(RecognizeRange or Config.Witness.RecognizeRange, Local.RecognizeRange(Player)) -- (2.8.1)
	local Result = nil
	for _, M in Monitors do
		if not Local.IsActive(M) then continue end
		local Visible, Distance = Local.CanSee(M, Character, true)
		if not Visible then continue end

		if Distance <= Range then
			Local.Say(M, `Hey! I saw that!`)
			Discipline.ReportIncident({
				Type = Reason; Suspect = Player; Witness = `Hall Monitor`;
				Position = M.Root.Position; Recognized = true;
			})
			return `Recognized`
		end
		if M.State ~= `Chase` and M.State ~= `Respond` then -- (2.7.3) see OnDamage
			Local.StartChase(M, Player, Reason)
		end
		Result = `Spotted`
	end
	return Result
end

-- (1.27) send the nearest free monitor on duty to Position; OnArrive runs when it gets there. True if one is coming.
function Shared.Respond(Position: Vector3, OnArrive: (() -> ())?): boolean
	local State = SchoolClock.GetState()
	if not (State and State.Segment and Settings.DutyKinds[State.Segment.Kind]) then return false end
	local Best, BestDistance = nil, math.huge
	for _, M in Monitors do
		if Local.IsActive(M) and M.State == `Patrol` then
			local D = (M.Root.Position - Position).Magnitude
			if D < BestDistance then Best, BestDistance = M, D end
		end
	end
	if not Best or BestDistance > 260 then return false end
	Best.RespondAt = Position
	Best.RespondDone = OnArrive
	Best.RespondUntil = os.clock() + 30
	Best.Humanoid.WalkSpeed = Settings.ChaseSpeed
	Local.SetState(Best, `Respond`)
	Local.Say(Best, `What's going on over there?`)
	return true
end

function Shared.GetMonitors(): { any }
	local Result = {}
	for _, M in Monitors do
		table.insert(Result, {
			Name = M.Model.Name; State = M.State; Target = M.Target and M.Target.Name;
			Reason = M.Reason; Position = M.Root.Position; Active = Local.IsActive(M);
		})
	end
	return Result
end

function Shared.OnStart()
	for Slot = 1, Settings.Count do
		task.spawn(Local.Spawn, Slot)
	end

	Downed.OnDamage:Connect(function(Target, Damage, Attacker)
		local Ok, Err = pcall(Local.OnDamage, Target, Damage, Attacker)
		if not Ok then warn(`[HallMonitor] {Err}`) end
	end)

	Players.PlayerRemoving:Connect(function(Player)
		Caught[Player] = nil
		LastFightReport[Player] = nil
		for _, M in Monitors do
			if M.Target == Player then Local.EndChase(M) end
		end
	end)

	task.spawn(function()
		while true do
			task.wait(TICK)
			local State = SchoolClock.GetState()
			for _, M in Monitors do
				local Ok, Err = pcall(Local.UpdateMonitor, M, State)
				if not Ok then warn(`[HallMonitor] {Err}`) end
			end
		end
	end)
end

return Shared
