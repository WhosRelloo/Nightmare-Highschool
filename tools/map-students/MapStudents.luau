--[[
	MapStudents (server). Services.Features.MapStudents  (NH core add-on for the Map place, 2026-11-10)

	Owner: "Start putting a few school NPC's in the Map place, but COMPLETELY upgrade their pathfinding & awareness".
	A few background students who live by the school clock on the builder's map. They walk with Services.AI.Nav
	(doors, steps, smoothing, avoidance, re-planning) and notice the world through Services.AI.Senses.

	Where they go: parts tagged NHNpcSpot (attribute Kind), in workspace["School NPC Spots"] for now:
	  Gate     where they come in and leave (just outside the front gate)
	  Yard     outside: the front yard and the courtyard (breaks, lunch, before and after school)
	  Inside   the ground-floor halls (passing time, class time: the classrooms aren't fitted yet)
	A spot's LookVector is the way a student faces there. Spots with the same Group attribute are close enough to
	stand and talk together. The folder's attribute Students sets how many there are (default 6).

	The day (Config.SchoolSchedule segments via School.SchoolClock):
	  Night, Morning     off campus
	  Before School      come in through the gate, hang out in the yard
	  Passing            drift between the halls and the yard
	  Class              head inside and wait in the halls
	  Break, Lunch       the yard, in twos and threes, facing each other
	  After School       the yard; from 14:00 a third head home; Evening: everyone home by 19:00

	What they react to (most urgent first; walking stops for the first four):
	  Danger      a fight, a transformed monster or a downed body close by: back away fast, then watch from a
	              distance. Braver students stand their ground closer. ("Whoa!", "Not again...")
	  Gawk        a fight they can see or hear further off: stop and turn to watch until it's been quiet 6 s
	  Make way    a student coming straight at them: step aside, look at them
	  Space       someone standing right on top of them: step back ("Uh... hi?")
	  Stared at   someone facing them, close, for a while: look back; the friendly ones say hello, the shy ones move off
	  Followed    someone keeping behind them as they walk: glance back, walk faster
	  Glance      whoever they're most aware of (the head turns, Controllers.World.NpcLook); otherwise they look
	              around, at the people they're talking to, or at a door that opened
	Model attributes for clients and tests: Role = "Ambient", NHActivity, NHMood, NHLookAt (Vector3) + NHLookUntil,
	NHSay + NHSayAt (a speech bubble), NHPersonality.
]]

local CollectionService = game:GetService(`CollectionService`)
local PhysicsService = game:GetService(`PhysicsService`)
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local ServerStorage = game:GetService(`ServerStorage`)

local Nav = require(ServerScriptService.Services.AI.Nav)
local Senses = require(ServerScriptService.Services.AI.Senses)

local Shared = {}
local Local = {}

local SPOT_TAG = `NHNpcSpot`
local DEFAULT_COUNT = 6
local WALK_PACE = 5.3 -- studs/s the Default walk clip covers at 1x
local RUN_PACE = 16
local ANIM = { Walk = 180426354; Idle = 180435571; Sprint = 0; Lean = 129824051499811 }
do
	local Pack = ReplicatedStorage:FindFirstChild(`Assets`)
	Pack = Pack and Pack:FindFirstChild(`Animations`)
	Pack = Pack and Pack:FindFirstChild(`Default`)
	Pack = Pack and Pack:FindFirstChild(`Movement`)
	for _, N in { `Walk`, `Idle`, `Sprint` } do
		local A = Pack and Pack:FindFirstChild(N)
		local Id = A and A:IsA(`Animation`) and tonumber(A.AnimationId:match(`%d+`))
		if Id then ANIM[N] = Id end
	end
end

local Lines = require(script:WaitForChild(`Lines`)) -- every voice line (Features.MapStudents.Lines)

local Folder: Folder? = nil
local mutterPool, chat -- (defined below)
local Students = {} :: { any }
local SpotTaken = {} :: { [BasePart]: any }
local Plan = { Kind = `Off`; Hour = 0 }

---| helpers |---

-- what the lines can talk about right now
local function ctx(): { [string]: any }
	local T = game:GetService(`Lighting`).ClockTime
	return {
		Kind = Plan.Kind; Day = Plan.DayName or `today`; Period = Plan.SegName or `class`;
		Moon = workspace:GetAttribute(`NHMoonPhase`) or ``;
		Night = T < 6 or T >= 19.5 or workspace:GetAttribute(`NHMoonNight`) == true;
	}
end

-- say a line from a pool (not one they said lately). Force skips the "don't talk over yourself" wait (chats).
local function say(S, Pool: { string }?, Cooldown: number?, Force: boolean?): boolean
	local Now = os.clock()
	if not Force and Now - (S.SaidAt or -1e9) < (Cooldown or 8) then return false end
	local Text = Pool and Lines.Pick(S, Pool, ctx())
	if not (Text and S.Model) then return false end
	S.SaidAt = Now
	S.Model:SetAttribute(`NHSay`, Text)
	S.Model:SetAttribute(`NHSayFor`, math.clamp(1.8 + #Text * 0.06, 2.4, 6))
	S.Model:SetAttribute(`NHSayAt`, workspace:GetServerTimeNow())
	return true
end
local function sayText(S, Text: string)
	if not S.Model then return end
	Text = Lines.Fill(Text, ctx())
	S.SaidAt = os.clock()
	S.Model:SetAttribute(`NHSay`, Text)
	S.Model:SetAttribute(`NHSayFor`, math.clamp(1.8 + #Text * 0.06, 2.4, 6))
	S.Model:SetAttribute(`NHSayAt`, workspace:GetServerTimeNow())
end

-- what a student remembers about each player: how often they've met, when they last said hi, when they saw them fight
local function memo(S, Pl: Player?)
	if not Pl then return {} end
	S.Memory = S.Memory or {}
	local M = S.Memory[Pl.UserId]
	if not M then M = { Met = 0; Greeted = -1e9; Fought = -1e9 } S.Memory[Pl.UserId] = M end
	return M
end

-- the right hello for this player, now
local function greeting(S, Rec): { string }
	local C = ctx()
	local M = memo(S, Rec and Rec.Player)
	local G = Lines.Greet
	if os.clock() - (M.Fought or -1e9) < 300 then return G.Wary end
	local Race = Rec and Rec.Player and Rec.Player:GetAttribute(`Race`)
	if Race and G.Race[Race] and math.random() < 0.3 then return G.Race[Race] end
	if (M.Met or 0) >= 4 and math.random() < 0.6 then return G.Often end
	if (M.Met or 0) >= 1 and math.random() < 0.7 then return G.Again end
	if C.Night then
		if C.Moon == `Full` and math.random() < 0.6 then return G.FullMoon end
		if C.Moon == `New` and math.random() < 0.4 then return G.NewMoon end
		return G.Night
	end
	local H = game:GetService(`Lighting`).ClockTime
	return if H < 11 then G.Morning elseif H >= 16.5 then G.Evening else G.Day
end

local function greet(S, Rec): boolean
	local M = memo(S, Rec and Rec.Player)
	if os.clock() - (M.Greeted or -1e9) < 60 then return false end
	if say(S, greeting(S, Rec), 6) then
		M.Greeted = os.clock()
		M.Met = (M.Met or 0) + 1
		return true
	end
	return false
end

local function lookAt(S, P: Vector3?, Seconds: number?)
	if not S.Model then return end
	if P then
		S.Model:SetAttribute(`NHLookAt`, P)
		S.Model:SetAttribute(`NHLookUntil`, workspace:GetServerTimeNow() + (Seconds or 0.6))
	else
		S.Model:SetAttribute(`NHLookUntil`, nil)
	end
end

local Studio = game:GetService(`RunService`):IsStudio()
local function step(S, Text: string)
	if Studio and S.Model then S.Model:SetAttribute(`NHStep`, Text) end
end

-- a reaction's mood (Scared, Uneasy, Watching) holds a few seconds before everyday glances can change it back
local function mood(S, M: string, Hold: number?)
	local Now = os.clock()
	if not Hold and Now < (S.MoodHold or 0) then return end
	if Hold then S.MoodHold = Now + Hold end
	if S.Model and S.Model:GetAttribute(`NHMood`) ~= M then S.Model:SetAttribute(`NHMood`, M) end
end

local function headOf(Rec): Vector3?
	local C = Rec and Rec.Player and Rec.Player.Character
	local H = C and C:FindFirstChild(`Head`)
	return H and H:IsA(`BasePart`) and H.Position or (Rec and Rec.Pos)
end

local function spots(Kind: string): { BasePart }
	local Out = {}
	for _, P in CollectionService:GetTagged(SPOT_TAG) do
		if P:IsA(`BasePart`) and P:IsDescendantOf(workspace) and P:GetAttribute(`Kind`) == Kind then table.insert(Out, P) end
	end
	return Out
end

-- a free spot of that kind, preferring a talking group someone is already at (for twos and threes)
local function playerOn(P: BasePart): boolean
	for _, Pl in Players:GetPlayers() do
		local R = Pl.Character and Pl.Character:FindFirstChild(`HumanoidRootPart`)
		if R and R:IsA(`BasePart`) and (Vector3.new(R.Position.X, 0, R.Position.Z) - Vector3.new(P.Position.X, 0, P.Position.Z)).Magnitude < 3.5
			and math.abs(R.Position.Y - P.Position.Y) < 6 then return true end
	end
	return false
end

local function freeSpot(S, Kind: string, Social: boolean?): BasePart?
	local Free, Grouped = {}, {}
	local Busy = {}
	for Spot, Who in SpotTaken do if Who ~= S and Who.Model then Busy[Spot:GetAttribute(`Group`) or ``] = true end end
	for _, P in spots(Kind) do
		local Who = SpotTaken[P]
		if (not Who or Who == S or not Who.Model) and not (S.Agent and Nav.Unreachable(P.Position, S.Agent)) and P ~= S.LastSpot and not playerOn(P) then
			table.insert(Free, P)
			if Social and P:GetAttribute(`Group`) and Busy[P:GetAttribute(`Group`)] then table.insert(Grouped, P) end
		end
	end
	local Pool = if #Grouped > 0 and math.random() < 0.75 then Grouped else Free
	-- everything else is taken or failed lately: the spot we just left is better than standing in the hall
	if #Pool == 0 and S.LastSpot and (not SpotTaken[S.LastSpot] or SpotTaken[S.LastSpot] == S) and S.LastSpot:GetAttribute(`Kind`) == Kind
		and not (S.Agent and Nav.Unreachable(S.LastSpot.Position, S.Agent)) then return S.LastSpot end
	if #Pool == 0 then return nil end
	return Pool[math.random(1, #Pool)]
end

local function claim(S, Spot: BasePart?)
	for P, Who in SpotTaken do if Who == S then SpotTaken[P] = nil end end
	if Spot then SpotTaken[Spot] = S end
	S.Spot = Spot
end

---| bodies |---

local function setupGroups()
	pcall(function() PhysicsService:RegisterCollisionGroup(`NHWalkers`) end)
	for _, G in { `Entity`, `NPC`, `NHWalkers`, `SportBall` } do
		pcall(function() PhysicsService:CollisionGroupSetCollidable(`NHWalkers`, G, false) end)
	end
end

local function rollLook(): any
	local Appearance = require(ReplicatedStorage.UI.Appearance)
	local Look = Appearance.Sanitize(nil)
	Look.UseAvatar = false
	Look.Body = math.random(1, 2)
	Look.Skin = math.random(1, #Appearance.Skins)
	Look.HairColor = math.random(1, #Appearance.HairColors)
	local Female = Appearance.IsFemale and Appearance.IsFemale(Look)
	-- school clothes only (never the admin kit): uniforms whose id says nothing about staff
	local function pick(List, Field)
		local Pool = {}
		for I, It in List or {} do
			local Id = string.lower(tostring(typeof(It) == `table` and (It.Id or It.Name) or It))
			if not Id:find(`admin`) and not Id:find(`staff`) then table.insert(Pool, I) end
		end
		if #Pool > 0 then Look[Field] = Pool[math.random(1, #Pool)] end
	end
	pick(Appearance.Uniforms, `Uniform`)
	pick(Appearance.BottomsList, `Bottoms`)
	Look.EyeSet = if Female then 2 else 1
	if Appearance.Eyes then Look.Eyes = math.random(1, #Appearance.Eyes) end
	local Cat = ReplicatedStorage:FindFirstChild(`NHHairCatalog`)
	if Cat then
		local Pool = {}
		for _, H in Cat:GetChildren() do
			if H:GetAttribute(`Group`) == (if Female then `Female` else `Male`) then table.insert(Pool, H:GetAttribute(`AssetId`)) end
		end
		if #Pool > 0 then Look.HairId = Pool[math.random(1, #Pool)] end
	end
	Look.Created = true
	return Look
end

local function track(S, Name: string, Looped: boolean): AnimationTrack?
	if S.Tracks[Name] then return S.Tracks[Name] end
	if (ANIM[Name] or 0) == 0 then return nil end
	local Animator = S.Hum:FindFirstChildOfClass(`Animator`) or Instance.new(`Animator`, S.Hum)
	local A = Instance.new(`Animation`)
	A.AnimationId = `rbxassetid://{ANIM[Name]}`
	local Ok, T = pcall(function() return Animator:LoadAnimation(A) end)
	if not Ok then return nil end
	T.Looped = Looped
	T.Priority = if Name == `Walk` or Name == `Idle` or Name == `Sprint` then Enum.AnimationPriority.Movement else Enum.AnimationPriority.Action
	S.Tracks[Name] = T
	return T
end

local function pose(S, Name: string?)
	for K, T in S.Tracks do
		if K ~= `Walk` and K ~= `Idle` and K ~= `Sprint` and K ~= Name and T.IsPlaying then T:Stop(0.3) end
	end
	if Name then
		local T = track(S, Name, true)
		if T and not T.IsPlaying then T:Play(0.3) end
	end
end

local function spawn(S, At: CFrame)
	local Rig = ServerStorage:FindFirstChild(`NHCore`) and ServerStorage.NHCore:FindFirstChild(`NpcRig`)
	if not (Rig and Folder) then return false end
	local M = Rig:Clone()
	M.Name = `Student`
	M:SetAttribute(`Role`, `Ambient`)
	M:SetAttribute(`NHStudent`, S.Index)
	M:SetAttribute(`NHPersonality`, string.format(`brave %.1f, social %.1f`, S.Bravery, S.Social))
	M:SetAttribute(`NHVoice`, S.Voice or 1) -- each student's voice pitch (Controllers.World.NpcLook's blips)
	local Animate = M:FindFirstChild(`Animate`)
	if Animate then Animate:Destroy() end
	local Hum = M:FindFirstChildOfClass(`Humanoid`) :: Humanoid
	local Root = M:FindFirstChild(`HumanoidRootPart`) :: BasePart
	Hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	Hum.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
	Hum.BreakJointsOnDeath = false
	Hum.UseJumpPower = true
	Hum.JumpPower = 50 -- the Map's gravity is 210: about 6 studs, enough for the entrance steps
	Hum.AutoRotate = true
	for _, St in { Enum.HumanoidStateType.Dead, Enum.HumanoidStateType.FallingDown, Enum.HumanoidStateType.Ragdoll, Enum.HumanoidStateType.Climbing, Enum.HumanoidStateType.Swimming } do
		Hum:SetStateEnabled(St, false)
	end
	local Up = Root.Size.Y / 2 + Hum.HipHeight + (M:FindFirstChild(`Left Leg`) and M[`Left Leg`].Size.Y or 2)
	M:PivotTo(At * CFrame.new(0, Up, 0) * Root.CFrame:Inverse() * M:GetPivot())
	M.Parent = Folder
	pcall(function() require(ReplicatedStorage.UI.Appearance).ApplyTo(M, table.clone(S.Look)) end)
	for _, D in M:GetDescendants() do
		if D:IsA(`BasePart`) then D.CollisionGroup = `NHWalkers` D.CanQuery = false D.CanTouch = false end
	end
	pcall(function() Root:SetNetworkOwner(nil) end)
	S.Model, S.Hum, S.Root, S.Tracks = M, Hum, Root, {}
	-- the shoulders' rest pose, for the phone hold and the stretch (clients read NHBaseC0)
	local Torso = M:FindFirstChild(`Torso`)
	for _, J in { `Right Shoulder`, `Left Shoulder` } do
		local Joint = Torso and Torso:FindFirstChild(J)
		if Joint and Joint:IsA(`Motor6D`) then Joint:SetAttribute(`NHBaseC0`, Joint.C0) end
	end
	S.Agent = Nav.Agent(M, { Speed = S.Speed; Name = `Student{S.Index}` })
	S.Agent.Up = Up
	S.Senses = Senses.Perceiver(M, { Bravery = S.Bravery; ViewRange = 60 + S.Social * 20 })
	local Walk, Idle, Run = track(S, `Walk`, true), track(S, `Idle`, true), track(S, `Sprint`, true)
	if Idle then Idle:Play() end
	Hum.Running:Connect(function(Speed)
		if Speed > 10 and Run then
			if Walk and Walk.IsPlaying then Walk:Stop(0.15) end
			if not Run.IsPlaying then Run:Play(0.15) end
			Run:AdjustSpeed(Speed / RUN_PACE)
		elseif Speed > 0.5 and Walk then
			if Run and Run.IsPlaying then Run:Stop(0.15) end
			if not Walk.IsPlaying then Walk:Play(0.2) end
			Walk:AdjustSpeed(Speed / WALK_PACE) -- feet match the ground speed
		else
			if Walk and Walk.IsPlaying then Walk:Stop(0.2) end
			if Run and Run.IsPlaying then Run:Stop(0.2) end
		end
	end)
	return true
end

local function despawn(S)
	claim(S, nil)
	if S.Model then S.Model:Destroy() end
	S.Model, S.Hum, S.Root, S.Tracks, S.Agent, S.Senses = nil, nil, nil, nil, nil, nil
end

---| reactions |---

-- the most urgent thing to react to right now, or nil. What triggered it is kept for 0.8 s (S.Pending), so a
-- reaction isn't lost when the moment has passed by the time the brain gets to it (someone who rushed at a
-- student and stopped should still make them step aside)
local function urgentNow(S, Snap): string?
	if not Snap then return nil end
	local T = Snap.Threat
	if T and S.Root then
		local Dist = (T.Pos - S.Root.Position).Magnitude
		local Close = 10 + (1 - S.Bravery) * 12 -- brave ones let it get closer
		if Dist < Close and T.Level > 0.15 then return `Danger` end
		if T.Kind == `Fight` and Dist < 55 then return `Gawk` end
	end
	if Snap.Approaching and not S.Busy then return `MakeWay` end
	if Snap.Crowding then return `Space` end
	return nil
end

local function urgent(S, Snap): (string?, any)
	local U = urgentNow(S, Snap)
	if U then
		S.Pending = { U = U; Snap = Snap; At = os.clock() }
		return U, Snap
	end
	local P = S.Pending
	if P and os.clock() - P.At < 0.8 then return P.U, P.Snap end
	return nil, Snap
end

local function shouldStop(S): () -> boolean
	return function()
		local Snap = S.Senses and S.Senses.Last
		local U = urgent(S, Snap)
		return U == `Danger` or U == `Gawk` or U == `MakeWay` or U == `Space` or S.Plan ~= Plan
	end
end

-- somewhere 20-30 studs away from a point, on the floor, that we can get to in a straight-ish line
local function awayFrom(S, From: Vector3): Vector3?
	local My = S.Root.Position
	local Base = Vector3.new(My.X - From.X, 0, My.Z - From.Z)
	if Base.Magnitude < 0.1 then Base = S.Root.CFrame.LookVector * -1 end
	Base = Base.Unit
	for _, A in { 0, 35, -35, 70, -70, 110, -110 } do
		local Dir = CFrame.Angles(0, math.rad(A), 0):VectorToWorldSpace(Base)
		for _, R in { 26, 18, 12 } do
			local F = Nav.Floor(My + Dir * R, 6)
			if F and (F - From).Magnitude > (My - From).Magnitude then return F end
		end
	end
	return nil
end

local React = {}

function React.Danger(S, Snap)
	local T = Snap.Threat
	mood(S, `Scared`, 6)
	S.Model:SetAttribute(`NHActivity`, `Backing away ({T.Kind})`)
	local C = ctx()
	if T.From and T.From.Player and T.Kind == `Fight` then memo(S, T.From.Player).Fought = os.clock() end
	local Pool = if T.Kind == `Monster` then (if C.Moon == `Full` and math.random() < 0.4 then Lines.MonsterFullMoon else Lines.ByNature(S, Lines.Monster, `Brave`))
		elseif T.Kind == `Body` then Lines.Body
		elseif C.Night and math.random() < 0.35 then Lines.FleeNight
		else Lines.ByNature(S, Lines.Flee, `Brave`)
	say(S, Pool, 8)
	S.Shaken = true -- they'll say something once it's over
	lookAt(S, T.Pos + Vector3.new(0, 2, 0), 2)
	local To = awayFrom(S, T.Pos)
	if To then
		S.Agent:GoTo(To, { Speed = 13 + S.Bravery * 2; Arrive = 2.5 })
	else
		S.Agent:Shuffle(S.Root.Position - T.Pos, 1.2, 11)
	end
	S.WatchUntil = os.clock() + 8
	S.WatchAt = T.Pos
end

function React.Gawk(S, Snap)
	local T = Snap.Threat
	mood(S, `Watching`, 4)
	S.Model:SetAttribute(`NHActivity`, `Watching a fight`)
	S.Agent:Stop()
	pose(S, nil)
	S.Agent:Face(T.Pos)
	lookAt(S, T.Pos + Vector3.new(0, 2, 0), 1.2)
	if os.clock() > (S.WatchUntil or 0) then -- just started watching
		if T.From and T.From.Player then memo(S, T.From.Player).Fought = os.clock() end
		say(S, if T.Heard and math.random() < 0.5 then Lines.Heard.Fight else Lines.ByNature(S, Lines.Gawk, `Brave`), 10)
	elseif math.random() < 0.08 then
		say(S, Lines.ByNature(S, Lines.Gawk, `Brave`), 9) -- now and then, a comment while watching
	end
	S.WatchUntil = os.clock() + 6
	S.WatchAt = T.Pos
	S.Shaken = true
	task.wait(0.4)
end

function React.MakeWay(S, Snap)
	local Rec = Snap.Approaching
	if not (Rec and Rec.Pos) then return end
	mood(S, `Wary`, 3)
	local Rel = Rec.Pos - S.Root.Position
	local Side = Vector3.new(-Rel.Z, 0, Rel.X)
	-- step to whichever side they aren't heading for
	local V = Rec.Root and Rec.Root.AssemblyLinearVelocity or Vector3.zero
	if Side:Dot(V) > 0 then Side = -Side end
	lookAt(S, headOf(Rec), 1.5)
	if math.random() < 0.6 then say(S, if (Rec.Speed or 0) > 18 then Lines.Sprint else Lines.MakeWay, 10) end
	S.Agent:Shuffle(Side, 0.55, 7)
	S.Agent:Face(Rec.Pos)
	task.wait(0.3)
end

function React.Space(S, Snap)
	local Rec = Snap.Crowding
	if not (Rec and Rec.Pos) then return end
	mood(S, `Uneasy`, 5)
	lookAt(S, headOf(Rec), 2.5)
	say(S, Lines.ByNature(S, Lines.Space, `Social`), 10)
	S.Agent:Shuffle(S.Root.Position - Rec.Pos, 0.7, 4)
	S.Agent:Face(Rec.Pos)
	Rec.Near = 0
	S.Restless = true -- find somewhere else to stand
	task.wait(0.4)
end

-- the gentle ones (never stop walking): staring back, glancing, feeling followed
local function glance(S, Snap)
	local Now = os.clock()
	if Snap and Snap.Staring then
		local Rec = Snap.Staring
		lookAt(S, headOf(Rec), 0.6)
		if not S.Agent.Moving then
			if S.Social >= 0.5 then
				mood(S, `Friendly`)
				if not greet(S, Rec) and Rec.Stare > 7 and not Rec.SaidStared then
					Rec.SaidStared = say(S, Lines.Stared, 8) -- you're still staring
				end
			elseif Rec.Stare > 6 and not S.Busy then
				mood(S, `Shy`)
				say(S, Lines.Shy, 20)
				S.Restless = true -- move on to another spot
			end
		end
		return
	end
	if Snap and Snap.Following then
		mood(S, `Uneasy`)
		if Now - (S.GlancedBack or 0) > 2.5 then
			S.GlancedBack = Now
			lookAt(S, headOf(Snap.Following), 0.9)
			local M = memo(S, Snap.Following.Player)
			M.Followed = (M.Followed or 0) + 1
			say(S, if M.Followed > 2 then Lines.FollowedAgain else Lines.Followed, 12)
		end
		S.Hurry = Now + 6
		return
	end
	if S.WatchUntil and Now < S.WatchUntil and S.WatchAt then
		lookAt(S, S.WatchAt + Vector3.new(0, 2, 0), 0.6)
		return
	end
	-- it's over: a word to steady themselves
	if S.Shaken and not (S.WatchUntil and Now < S.WatchUntil) and not (Snap and Snap.Threat) then
		S.Shaken = false
		say(S, Lines.Relief, 4)
	end
	if Snap and Snap.Focus and Snap.Focus.Aware > 0.45 and (Snap.Focus.Dist or 99) < 30 then
		lookAt(S, headOf(Snap.Focus), 0.6)
		-- a friendly hello to someone passing close by
		local F = Snap.Focus
		if F.Visible and (F.Dist or 99) < 7 and S.Social > 0.55 and not S.Agent.Moving and math.random() < 0.05 then greet(S, F) end
		if F.Fighting and F.Player then memo(S, F.Player).Fought = Now end
		return
	end
	if Snap and Snap.Heard and Snap.Heard.Kind == `Door` and Now - Snap.Heard.At < 1.5 then
		lookAt(S, Snap.Heard.Pos, 1.2)
		if Snap.Heard ~= S.LastHeard then
			S.LastHeard = Snap.Heard
			local C = ctx()
			if math.random() < (if C.Night then 0.35 else 0.1) then say(S, if C.Night then Lines.Heard.DoorNight else Lines.Heard.Door, 15) end
		end
		return
	end
	-- the people we're talking to, or a look around now and then
	if S.Partner and S.Partner.Root and not S.Agent.Moving then
		lookAt(S, S.Partner.Root.Position + Vector3.new(0, 1.5, 0), 0.6)
		return
	end
	if Now > (S.NextLookAround or 0) and S.Root then
		S.NextLookAround = Now + math.random(25, 70) / 10
		local Ang = math.rad(math.random(-70, 70))
		local Dir = CFrame.Angles(0, Ang, 0):VectorToWorldSpace(S.Root.CFrame.LookVector)
		lookAt(S, S.Root.Position + Dir * 12 + Vector3.new(0, math.random(-2, 3), 0), 1.4)
	end
	if S.Model and S.Model:GetAttribute(`NHMood`) ~= `Calm` and not (S.WatchUntil and Now < S.WatchUntil) then mood(S, `Calm`) end
end

---| the day |---

local function activityFor(S): (string, string)
	local K = Plan.Kind
	if K == `Night` or K == `Morning` or K == `Off` then return `Leave`, `Going home` end
	if K == `Evening` then
		if Plan.Hour >= 19 or S.Index % 2 == 0 then return `Leave`, `Going home` end
		return `Yard`, `Hanging out`
	end
	if K == `AfterSchool` then
		if Plan.Hour >= 14 and S.Index % 3 == 0 then return `Leave`, `Going home` end
		return `Yard`, `After school`
	end
	if K == `Class` then return `Inside`, `Waiting for class` end
	if K == `Passing` then return (if math.random() < 0.6 then `Inside` else `Yard`), `Passing time` end
	if K == `Break` or K == `Lunch` then return `Yard`, (if K == `Lunch` then `Lunch` else `Break`) end
	return `Yard`, `Before school`
end

local function playerNear(P: Vector3, R: number): boolean
	for _, Pl in Players:GetPlayers() do
		local Root = Pl.Character and Pl.Character:FindFirstChild(`HumanoidRootPart`)
		if Root and Root:IsA(`BasePart`) and (Root.Position - P).Magnitude < R then return true end
	end
	return false
end

-- something to mutter: the day, the moon, the time, or what part of the day it is
mutterPool = function(): { string }
	local C = ctx()
	local M = Lines.Mutter
	if C.Night then
		if C.Moon == `Full` and math.random() < 0.5 then return M.FullMoon end
		return M.Night
	end
	if math.random() < 0.2 then
		if C.Day == `Monday` then return M.Monday end
		if C.Day == `Friday` then return M.Friday end
		if C.Day == `Saturday` or C.Day == `Sunday` then return M.Weekend end
	end
	return M[C.Kind] or M.Break
end

-- a little conversation between two students standing together: they take turns, look at whoever's talking,
-- and break off if anything needs reacting to
chat = function(A, B)
	local Lines2 = Lines.PickChat(A, ctx())
	if not Lines2 then return end
	A.Chatting, B.Chatting = true, true
	for _, L in Lines2 do
		if typeof(L) ~= `string` then continue end
		local Who, Text = L:match(`^(%a):%s*(.+)$`)
		local Speaker, Listener = if Who == `B` then B else A, if Who == `B` then A else B
		if not (Speaker.Model and Listener.Model and Speaker.Root and Listener.Root) then break end
		if urgent(A, A.Senses and A.Senses.Last) or urgent(B, B.Senses and B.Senses.Last) then break end
		if A.Agent.Moving or B.Agent.Moving then break end
		sayText(Speaker, Text or L)
		lookAt(Listener, Speaker.Root.Position + Vector3.new(0, 1.5, 0), 3)
		lookAt(Speaker, Listener.Root.Position + Vector3.new(0, 1.5, 0), 3)
		task.wait(math.clamp(1.6 + #(Text or L) * 0.055, 2.2, 4.6))
	end
	A.Chatting, B.Chatting = false, false
end

---| fidgets |---
-- Small things students do while they wait, so nobody stands frozen: check their phone, stretch (a yawn in the
-- morning or at night), glance up at the clock tower, look over their shoulder, shift their weight.

-- the handset, built the way Features.Phone builds a player's (same model, grip and arm pose)
local PHONE_POSE = CFrame.Angles(0, math.rad(45), math.rad(105))
local PHONE_GRIP = CFrame.new(-0.248250008, -0.0295313597, 0, -0.0342340842, 0.942064762, -0.333679318, -0.821599126, 0.16357027, 0.546094596, 0.569036543, 0.292845726, 0.768400073)

local function makePhone(): Tool?
	local Tpl = ServerStorage:FindFirstChild(`NHPhoneModel`)
	if not Tpl then return nil end
	local Model = Tpl:Clone()
	local Screen = Model:FindFirstChild(`Screen`, true)
	local CF = Model:GetBoundingBox()
	local Basis = if Screen and Screen:IsA(`BasePart`) then Screen.CFrame.Rotation + CF.Position else CF
	local T = Instance.new(`Tool`)
	T.Name = `Phone`
	T.CanBeDropped = false
	T.RequiresHandle = true
	T.Grip = PHONE_GRIP
	T:SetAttribute(`NHPhone`, true) -- Controllers.Character.PhoneHold keeps the arm steady
	T:SetAttribute(`NHNpcPhone`, true)
	local Handle = Instance.new(`Part`)
	Handle.Name = `Handle`
	Handle.Size = Vector3.new(0.3, 0.3, 0.3)
	Handle.Transparency = 1
	Handle.CanCollide, Handle.CanQuery, Handle.CanTouch, Handle.Massless = false, false, false, true
	Handle.CFrame = Basis
	Handle.Parent = T
	for _, D in Model:GetDescendants() do
		if D:IsA(`BasePart`) then
			D.Anchored = false
			D.CanCollide, D.CanQuery, D.CanTouch, D.Massless = false, false, false, true
			local W = Instance.new(`WeldConstraint`)
			W.Part0, W.Part1 = Handle, D
			W.Parent = D
		elseif D:IsA(`WeldConstraint`) or D:IsA(`Weld`) then
			D:Destroy()
		end
	end
	if Screen and Screen:IsA(`BasePart`) then
		Screen.Material = Enum.Material.Neon -- the screen glows a little
		Screen.Color = Color3.fromRGB(60, 24, 40)
	end
	Model.Parent = T
	return T
end

local function shoulder(S): Motor6D?
	local Torso = S.Model and S.Model:FindFirstChild(`Torso`)
	local J = Torso and Torso:FindFirstChild(`Right Shoulder`)
	return if J and J:IsA(`Motor6D`) then J else nil
end

local function busyNow(S): boolean
	return S.Chatting or not S.Model or (S.Agent and S.Agent.Moving) or urgent(S, S.Senses and S.Senses.Last) ~= nil
end

local function fidgetPhone(S)
	local T = makePhone()
	local J = shoulder(S)
	if not (T and J and S.Hum) then if T then T:Destroy() end return end
	T.Parent = S.Model
	pcall(function() S.Hum:EquipTool(T) end)
	J.C0 = (J:GetAttribute(`NHBaseC0`) or J.C0) * PHONE_POSE
	local Was = S.Model:GetAttribute(`NHActivity`)
	S.Model:SetAttribute(`NHActivity`, `{Was or ``} (on the phone)`)
	if math.random() < 0.45 then say(S, Lines.Phone, 8) end
	local Until = os.clock() + math.random(40, 90) / 10
	while os.clock() < Until and not busyNow(S) and T.Parent do
		-- eyes on the screen
		local Arm = S.Model:FindFirstChild(`Right Arm`)
		if Arm then lookAt(S, Arm.Position + Vector3.new(0, -0.4, 0), 0.6) end
		task.wait(0.25)
	end
	if T.Parent then T:Destroy() end
	if J.Parent then J.C0 = J:GetAttribute(`NHBaseC0`) or J.C0 end
	if S.Model then S.Model:SetAttribute(`NHActivity`, Was) end
end

local function fidget(S)
	if busyNow(S) or not S.Root then return end
	local C = ctx()
	local Sleepy = C.Kind == `BeforeSchool` or C.Night
	local Pool = {
		{ `Phone`, if S.Partner then 0.12 else 0.32 };
		{ `Stretch`, if Sleepy then 0.28 else 0.12 };
		{ `LookUp`, 0.14 };
		{ `LookBehind`, if C.Night then 0.3 else 0.12 };
		{ `Shift`, 0.25 };
	}
	local Total = 0
	for _, P in Pool do Total += P[2] end
	local R = math.random() * Total
	local Kind = Pool[#Pool][1]
	for _, P in Pool do R -= P[2] if R <= 0 then Kind = P[1] break end end
	step(S, `fidget: {Kind}`)
	if Kind == `Phone` then
		fidgetPhone(S)
	elseif Kind == `Stretch` then
		S.Model:SetAttribute(`NHFidget`, `Stretch`)
		S.Model:SetAttribute(`NHFidgetAt`, workspace:GetServerTimeNow())
		if Sleepy and math.random() < 0.5 then say(S, Lines.Yawn, 6) end
		lookAt(S, S.Root.Position + S.Root.CFrame.LookVector * 6 + Vector3.new(0, 9, 0), 1.4)
		task.wait(1.6)
	elseif Kind == `LookUp` then
		-- the clock tower, the sky, a window
		lookAt(S, S.Root.Position + S.Root.CFrame.LookVector * 25 + S.Root.CFrame.RightVector * math.random(-12, 12) + Vector3.new(0, 30, 0), 2.2)
		task.wait(2.2)
	elseif Kind == `LookBehind` then
		local Side = if math.random() < 0.5 then 1 else -1
		lookAt(S, S.Root.Position - S.Root.CFrame.LookVector * 4 + S.Root.CFrame.RightVector * 10 * Side + Vector3.new(0, 1.5, 0), 1.3)
		if C.Night and math.random() < 0.25 then say(S, Lines.Mutter.Night, 10) end
		task.wait(1.4)
	else -- shift their weight: turn a little, ease into it
		local From = S.Root.CFrame
		local To = From * CFrame.Angles(0, math.rad(math.random(15, 35) * (if math.random() < 0.5 then 1 else -1)), 0)
		for I = 1, 8 do
			if not S.Root.Parent or busyNow(S) then break end
			S.Root.CFrame = From:Lerp(To, I / 8)
			task.wait(0.05)
		end
	end
end

-- one leg of the student's day: get somewhere and spend a while there (returns early to react)
local function doTask(S)
	local Kind, Label = activityFor(S)
	S.Plan = Plan
	if Kind == `Leave` then
		if not S.Model then task.wait(1) return end
		local Gate = spots(`Gate`)[1]
		S.Model:SetAttribute(`NHActivity`, Label)
		claim(S, nil)
		local Ok = Gate and S.Agent:GoTo(Gate.Position, { Speed = S.Speed; Arrive = 3; ShouldStop = shouldStop(S) })
		if Ok or not Gate then despawn(S) end
		return
	end
	if not S.Model then
		local Gate = spots(`Gate`)[1] or spots(`Yard`)[1]
		if not Gate then task.wait(2) return end
		if not spawn(S, Gate.CFrame * CFrame.new((math.random() - 0.5) * 6, 0, (math.random() - 0.5) * 4)) then task.wait(2) return end
	end
	local Keep = not S.Restless and S.Spot and S.Spot:GetAttribute(`Kind`) == Kind and SpotTaken[S.Spot] == S and not playerOn(S.Spot)
	local Spot = if Keep then S.Spot else freeSpot(S, Kind, Kind == `Yard`)
	S.Restless = false
	step(S, if Spot then `going to {Spot.Name}` else `no free {Kind} spot`)
	if not Spot then task.wait(1.5) return end
	claim(S, Spot)
	S.Model:SetAttribute(`NHActivity`, `{Label}: walking`)
	pose(S, nil)
	S.Partner = nil
	local Speed = S.Speed * (if S.Hurry and os.clock() < S.Hurry then 1.35 else 1)
	local Ok, Why = S.Agent:GoTo(Spot.Position, { Speed = Speed; ShouldStop = shouldStop(S) })
	step(S, if Ok then `at {Spot.Name}` else `{Spot.Name}: {Why}`)
	if not Ok then
		if Why == `unreachable` then S.LastSpot = Spot claim(S, nil) task.wait(0.5 + math.random()) end
		return
	end
	S.LastSpot = Spot
	S.Model:SetAttribute(`NHActivity`, Label)
	-- face the way the spot says, or a friend at the same group
	local Group = Spot:GetAttribute(`Group`)
	for P, Who in SpotTaken do
		if Who ~= S and Who.Model and Group and P:GetAttribute(`Group`) == Group then S.Partner = Who break end
	end
	if S.Partner and S.Partner.Root then S.Agent:Face(S.Partner.Root.Position)
	else S.Agent:Face(Spot.Position + Spot.CFrame.LookVector * 5) end
	if not S.Partner and math.random() < 0.3 then pose(S, `Lean`) end
	local Until = os.clock() + math.random(150, 360) / 10
	local NextFriend = 0
	S.NextChat = math.max(S.NextChat or 0, os.clock() + math.random(30, 90) / 10)
	while os.clock() < Until and S.Plan == Plan and S.Model and not S.Restless do
		local Snap = S.Senses and S.Senses.Last
		if urgent(S, Snap) then break end
		-- fidget now and then (with someone near enough to see it)
		if os.clock() >= (S.NextFidget or 0) and S.Root then
			S.NextFidget = os.clock() + math.random(60, 140) / 10
			if not S.Chatting and playerNear(S.Root.Position, 60) then fidget(S) end
		end
		-- talk: two together have a little conversation (the lower number starts it); alone, mutter now and then.
		-- Only with a player near enough to hear it.
		if os.clock() >= S.NextChat and S.Root then
			S.NextChat = os.clock() + math.random(120, 280) / 10
			if playerNear(S.Root.Position, 60) then -- (as far as the speech bubbles show)
				local P = S.Partner
				if P and P.Model and P.Root and P.Index > S.Index and not P.Agent.Moving and not P.Chatting then
					chat(S, P)
				elseif not P and math.random() < 0.55 then
					say(S, mutterPool(), 10)
				end
			end
		end
		-- a friend turned up at the same group: turn to them
		if Group and os.clock() >= NextFriend then
			NextFriend = os.clock() + 1
			if not (S.Partner and S.Partner.Model) then
				S.Partner = nil
				for P, Who in SpotTaken do
					if Who ~= S and Who.Model and Who.Root and P:GetAttribute(`Group`) == Group and not Who.Agent.Moving then S.Partner = Who break end
				end
			end
			local F = S.Partner and S.Partner.Root
			if F and S.Root then
				local To = Vector3.new(F.Position.X - S.Root.Position.X, 0, F.Position.Z - S.Root.Position.Z)
				if To.Magnitude > 0.5 and S.Root.CFrame.LookVector:Dot(To.Unit) < 0.85 then
					pose(S, nil)
					S.Agent:Face(F.Position)
				end
			end
		end
		task.wait(0.25)
	end
	pose(S, nil)
end

---| the brain |---

local function brain(S)
	while true do
		if S.Model and S.Senses then
			local Snap = S.Senses:Due() and S.Senses:Tick() or S.Senses.Last
			glance(S, Snap)
			local U, USnap = urgent(S, Snap)
			if U and React[U] then
				S.Pending = nil
				step(S, `reacting: {U}`)
				local Ok, Err = pcall(React[U], S, USnap)
				if not Ok then warn(`[MapStudents] {U}: {Err}`) task.wait(0.5) end
				continue
			end
			if S.WatchUntil and os.clock() < S.WatchUntil then step(S, `watching`) task.wait(0.25) continue end
		end
		local Ok, Err = pcall(doTask, S)
		if not Ok then warn(`[MapStudents] {Err}`) task.wait(1) end
		task.wait()
	end
end

-- the senses keep ticking while a student walks or waits (the brain is inside GoTo then)
local function senseLoop()
	while true do
		for _, S in Students do
			if S.Model and S.Senses and S.Senses:Due() then
				local Snap = S.Senses:Tick()
				pcall(glance, S, Snap)
			end
		end
		task.wait(0.1)
	end
end

---| start |---

function Shared.Debug()
	local Out = {}
	for _, S in Students do
		table.insert(Out, {
			Index = S.Index; Spawned = S.Model ~= nil;
			Activity = S.Model and S.Model:GetAttribute(`NHActivity`); Mood = S.Model and S.Model:GetAttribute(`NHMood`);
			Pos = S.Root and S.Root.Position; Spot = S.Spot and S.Spot.Name;
		})
	end
	return Out
end

function Shared.OnStart()
	Nav.Init()
	Senses.Init()
	setupGroups()
	local SpotFolder = workspace:FindFirstChild(`School NPC Spots`)
	if SpotFolder then
		for _, P in SpotFolder:GetDescendants() do if P:IsA(`BasePart`) then P.Transparency = 1 end end
	end
	if #CollectionService:GetTagged(SPOT_TAG) == 0 then return end -- nowhere to be yet
	Folder = Instance.new(`Folder`)
	Folder.Name = `NHStudents`
	Folder.Parent = workspace
	local Count = (SpotFolder and tonumber(SpotFolder:GetAttribute(`Students`))) or DEFAULT_COUNT
	for I = 1, Count do
		local Ok, Look = pcall(rollLook)
		Students[I] = {
			Index = I; Look = if Ok then Look else {};
			Bravery = math.random(10, 85) / 100; Social = math.random(15, 95) / 100;
			Speed = 5.4 + math.random() * 1.6;
			-- one voice each: higher on the female body, lower on the male (the blips' pitch)
			Voice = if (Ok and Look and require(ReplicatedStorage.UI.Appearance).IsFemale(Look)) then 1.15 + math.random() * 0.3 else 0.8 + math.random() * 0.3;
		}
	end
	task.spawn(function()
		task.wait(4)
		local Clock = require(ServerScriptService.Services.School.SchoolClock)
		local function refresh()
			local Ok, State = pcall(Clock.GetState)
			if not (Ok and State and State.Segment) then return end
			local Hour = State.Hour or math.floor((State.MinuteOfDay or 0) / 60)
			local Kind = State.Segment.Kind
			local Key = `{Kind}:{State.Segment.Name}:{Hour >= 14}:{Hour >= 19}`
			if Key ~= Plan.Key then Plan = { Kind = Kind; Hour = Hour; Key = Key; DayName = State.DayName; SegName = State.Segment.Name } end
			Plan.Hour = Hour
		end
		refresh()
		for I, S in Students do
			task.delay(I * 1.5, brain, S) -- they don't all walk in at once
		end
		task.spawn(senseLoop)
		while true do
			task.wait(1)
			if workspace:GetAttribute(`NHStudentsPlan`) then
				-- tests: force a part of the day (Kind) without moving the school clock
				local K = workspace:GetAttribute(`NHStudentsPlan`)
				if Plan.Key ~= `test:` .. K then Plan = { Kind = K; Hour = 10; Key = `test:` .. K; DayName = `Wednesday`; SegName = K } end
			else
				refresh()
			end
		end
	end)
end

return Shared
