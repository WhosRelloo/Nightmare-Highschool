--[[
	AmbientNpcs (server). Services.Features.AmbientNpcs  (owner's animations, 2026-11-01)
	Background students who make the school feel lived in. Anchored scenery: no AI, no prompts, no combat.
	  Gymnasium   push-ups (rest / reps), sit-ups (rest / reps), pull-ups on an iron bar (rest / reps)
	  Hallway     a student sprawled on the floor (side lay), a barber cutting hair, a student eating lunch
	  R106        a kid in detention (prisoner idle)
	  Infirmary   (phase6-infirmary) a patient lying on bed 1 (LayingIdle) while the Nurse is on duty and the bed is free
	Each wears a random school uniform through the Appearance module. Placed by floor raycasts from each area's
	bounding box, so they follow the greybox; tag a part "NHAmbientSpot" (attribute Kind) later to place them by hand.
	Also: feeding after a grip finisher (Ghoul: eating the body, Vampire: drinking).
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

local Seats = require(ServerScriptService.Services.Features.Seats) -- where hips go on the school's seat props

local Shared = {}
local Local = {}

local ANIM = {
	PushIdle = 111737875654076; PushAction = 112288220550648;
	SitIdle = 132757288791974;
	PullIdle = 134151351487837; PullAction = 115584556914404;
	SideLay = 79446383649016; Barber = 80222068692077; Eat = 126575676069500; Prisoner = 132416886468242;
	EatBody = 79651374323565; Drink = 134503729182597;
	-- 2026-11-01 batch 2 (owner)
	Sitting = 103637860968444; SitThinking = 117282044534528; SitChill = 124142826216078;
	Barbell = 136973050103731; Lean = 129824051499811;
}

local Folder: Folder? = nil

function Local.Floor(At: Vector3): Vector3?
	local P = RaycastParams.new()
	P.FilterType = Enum.RaycastFilterType.Exclude
	local Ex = {}
	for _, N in { `Live`, `NHFx` } do local F = workspace:FindFirstChild(N) if F then table.insert(Ex, F) end end
	if Folder then table.insert(Ex, Folder) end
	P.FilterDescendantsInstances = Ex
	P.RespectCanCollide = true
	-- skip invisible colliders (trash-bin boxes, trigger volumes): keep casting below them
	local From, Left = At + Vector3.new(0, 6, 0), 40
	for _ = 1, 6 do
		local Hit = workspace:Raycast(From, Vector3.new(0, -Left, 0), P)
		if not Hit then return nil end
		if Hit.Instance.Transparency < 0.9 then return if Hit.Normal.Y > 0.6 then Hit.Position else nil end
		Left -= (From.Y - Hit.Position.Y) + 0.05
		From = Hit.Position - Vector3.new(0, 0.05, 0)
		if Left <= 0 then return nil end
	end
	return nil
end

function Local.Track(Hum: Humanoid, Id: number, Looped: boolean): AnimationTrack?
	local Animator = Hum:FindFirstChildOfClass(`Animator`) or Instance.new(`Animator`, Hum)
	local A = Instance.new(`Animation`)
	A.AnimationId = `rbxassetid://{Id}`
	local Ok, T = pcall(function() return Animator:LoadAnimation(A) end)
	if not Ok then return nil end
	T.Looped = Looped
	T.Priority = Enum.AnimationPriority.Action
	return T
end

function Local.Spawn(Name: string, At: Vector3, LookAt: Vector3): (Model?, Humanoid?)
	local AIFolder = ServerScriptService.Services.AI.AI
	local Rig = AIFolder:FindFirstChild(`Rig`)
	if not Rig then return nil, nil end
	local Model = Rig:Clone()
	Model.Name = Name
	Model:SetAttribute(`Role`, `Ambient`)
	local Hum = Model:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	local Root = Model:FindFirstChild(`HumanoidRootPart`) :: BasePart
	Hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	Hum.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
	local Up = Root.Size.Y / 2 + Hum.HipHeight + (Model:FindFirstChild(`Left Leg`) and Model[`Left Leg`].Size.Y or 2)
	local Want = CFrame.lookAt(At + Vector3.new(0, Up, 0), Vector3.new(LookAt.X, At.Y + Up, LookAt.Z))
	Model:PivotTo(Want * Root.CFrame:Inverse() * Model:GetPivot())
	Root.Anchored = true
	Model.Parent = Folder
	-- a random school look
	pcall(function()
		local Appearance = require(ReplicatedStorage.UI.Appearance)
		local Look = Appearance.Sanitize(nil)
		Look.UseAvatar = false
		Look.Uniform = math.random(1, #Appearance.Uniforms)
		Look.Bottoms = math.random(1, math.min(6, #Appearance.BottomsList))
		Look.Skin = math.random(1, #Appearance.Skins)
		Look.Hair = math.random(1, #Appearance.HairStyles)
		Look.HairColor = math.random(1, #Appearance.HairColors)
		Look.Body = math.random(1, 2)
		-- (1.71) clothes by the NPC's gender (UI.Appearance), never the admin kit
		Look.Uniform = Appearance.RandomPiece(Appearance.Uniforms, Look)
		Look.Bottoms = Appearance.RandomPiece(Appearance.BottomsList, Look)
		-- (2.3.0) height and body type by their clique (Config.Cliques.Npcs, else Ordinary) and personality, the same every
		-- spawn (Config.NpcBuilds); no posture: they're doing reps, sitting or napping
		local NpcBuilds = require(ReplicatedStorage.Config.NpcBuilds)
		local Clique = require(ReplicatedStorage.Config.Cliques).Npcs[Name]
		local Female = Appearance.IsFemale(Look)
		local Build = NpcBuilds.Roll(`Ambient|{Name}|{math.floor(At.X + 0.5)},{math.floor(At.Z + 0.5)}`, Clique, Female)
		Look.Body = NpcBuilds.BodyFor(Appearance, Female, Build) or Look.Body
		Model:SetAttribute(`NHHeightWant`, Build.Height)
		Model:SetAttribute(`NHBuild`, NpcBuilds.Describe(Build))
		local Cat = ReplicatedStorage:FindFirstChild(`NHHairCatalog`)
		if Cat then
			local Pool = {}
			for _, H in Cat:GetChildren() do
				if H:GetAttribute(`Group`) == (if Appearance.IsFemale(Look) then `Female` else `Male`) then table.insert(Pool, H:GetAttribute(`AssetId`)) end
			end
			if #Pool > 0 then Look.HairId = Pool[math.random(1, #Pool)] end
		end
		Appearance.ApplyTo(Model, Look)
	end)
	Local.Settle(Model, At)
	return Model, Hum
end

-- feet exactly on the floor (rest pose) and nudged out of walls toward open space
function Local.Settle(Model: Model, At: Vector3)
	local Low = math.huge
	for _, N in { `Left Leg`, `Right Leg` } do
		local L = Model:FindFirstChild(N)
		if L then Low = math.min(Low, L.Position.Y - L.Size.Y / 2) end
	end
	if Low < math.huge then Model:PivotTo(Model:GetPivot() - Vector3.new(0, Low - At.Y, 0)) end
	local Torso = Model:FindFirstChild(`Torso`)
	if not Torso then return end
	local O = OverlapParams.new()
	O.FilterType = Enum.RaycastFilterType.Exclude
	local Ex = { Model }
	for _, N in { `Live`, `NHFx` } do local F = workspace:FindFirstChild(N) if F then table.insert(Ex, F) end end
	if Folder then table.insert(Ex, Folder) end
	O.FilterDescendantsInstances = Ex
	O.RespectCanCollide = true
	local function blocked(): boolean
		for _, N in { `Torso`, `Left Arm`, `Right Arm`, `Head`, `Left Leg`, `Right Leg` } do
			local P = Model:FindFirstChild(N)
			if P and #workspace:GetPartBoundsInBox(P.CFrame + Vector3.new(0, 0.15, 0), P.Size * 0.8, O) > 0 then return true end
		end
		return false
	end
	if not blocked() then return end
	local Base = Model:GetPivot()
	for R = 1, 6 do
		for K = 0, 7 do
			local A = K * math.pi / 4
			Model:PivotTo(Base + Vector3.new(math.cos(A), 0, math.sin(A)) * R)
			if not blocked() then return end
		end
	end
	Model:PivotTo(Base)
end

-- once the pose is playing: rest the body on whatever is under it (floor, seat) and pull it out of walls.
-- Poses move limbs a long way from the rest pose (lying, sitting, kneeling), so this runs on the posed body.
local HANGING = { [`Pull-up kid`] = true }
function Local.PostSettle(Model: Model)
	if not (Model and Model.Parent) or HANGING[Model.Name] or Model:GetAttribute(`NHSeated`) then return end
	local RP = RaycastParams.new()
	RP.FilterType = Enum.RaycastFilterType.Exclude
	local Ex = { Model }
	for _, N in { `Live`, `NHFx` } do local F = workspace:FindFirstChild(N) if F then table.insert(Ex, F) end end
	if Folder then table.insert(Ex, Folder) end
	RP.FilterDescendantsInstances = Ex
	RP.RespectCanCollide = true
	local function surfaceUnder(P: BasePart): number?
		local From = P.Position + Vector3.new(0, P.Size.Magnitude / 2 + 3, 0)
		for _ = 1, 4 do
			local Hit = workspace:Raycast(From, Vector3.new(0, -30, 0), RP)
			if not Hit then return nil end
			if Hit.Instance.Transparency < 0.9 and Hit.Normal.Y > 0.5 then return Hit.Position.Y end
			From = Hit.Position - Vector3.new(0, 0.05, 0)
		end
		return nil
	end
	-- the limb nearest its surface decides: raise if anything is sunk, lower if everything floats
	local Best = math.huge
	for _, N in { `Torso`, `Left Leg`, `Right Leg`, `Left Arm`, `Right Arm`, `Head` } do
		local P = Model:FindFirstChild(N)
		if P and P:IsA(`BasePart`) then
			local Bottom = P.Position.Y - P.Size.Y / 2
			-- a rotated limb (lying, sitting): use its real lowest point
			local cf, sz = P.CFrame, P.Size / 2
			local Low = math.huge
			for _, X in { -1, 1 } do for _, Y in { -1, 1 } do for _, Z in { -1, 1 } do
				Low = math.min(Low, (cf * Vector3.new(X * sz.X, Y * sz.Y, Z * sz.Z)).Y)
			end end end
			Bottom = Low
			local Surf = surfaceUnder(P)
			if Surf then Best = math.min(Best, Bottom - Surf) end
		end
	end
	if Best < math.huge and math.abs(Best) > 0.04 then Model:PivotTo(Model:GetPivot() - Vector3.new(0, Best, 0)) end
	-- out of walls (posed arms / bodies): nudge sideways a little at a time
	local O = OverlapParams.new()
	O.FilterType = Enum.RaycastFilterType.Exclude
	O.FilterDescendantsInstances = Ex
	O.RespectCanCollide = true
	local function blocked(): boolean
		for _, N in { `Torso`, `Left Arm`, `Right Arm`, `Head`, `Left Leg`, `Right Leg` } do
			local P = Model:FindFirstChild(N)
			if P then
				-- lift the test box slightly so resting on the floor / seat doesn't count
				for _, Q in workspace:GetPartBoundsInBox(P.CFrame + Vector3.new(0, 0.15, 0), P.Size * 0.75, O) do
					if Q.Transparency < 0.9 then return true end
				end
			end
		end
		return false
	end
	if not blocked() then return end
	local Base = Model:GetPivot()
	for R = 1, 8 do
		for K = 0, 7 do
			local A = K * math.pi / 4
			Model:PivotTo(Base + Vector3.new(math.cos(A), 0, math.sin(A)) * (R * 0.5))
			if not blocked() then return end
		end
	end
	Model:PivotTo(Base)
end

-- seated students: once the pose plays, put the hips over the seat and rest them on its surface
function Local.SeatSettle(Model: Model, Prop: Model, SeatAt: Vector3, Back: Vector3)
	-- (1.46.1) the shared seat logic: hips and thighs on the seat, then out of the wall / backrest behind them
	if not (Prop and Prop.Parent) then return end
	Seats.Settle(Model, SeatAt, Back, 0.35, Prop)
end

-- loop Idle, now and then play Action a few times (reps), forever
function Local.Reps(Hum: Humanoid, IdleId: number, ActionId: number?)
	local Idle = Local.Track(Hum, IdleId, true)
	local Action = ActionId and Local.Track(Hum, ActionId, false)
	if Idle then Idle:Play(0.3) end
	task.spawn(function()
		-- wait for the pose to actually load and play (first Play downloads the animation), then settle on it
		local t0 = os.clock()
		while Idle and (Idle.Length == 0 or not Idle.IsPlaying) and os.clock() - t0 < 15 do task.wait(0.2) end
		task.wait(0.7)
		pcall(Local.PostSettle, Hum.Parent)
		task.wait(4)
		pcall(Local.PostSettle, Hum.Parent)
	end)
	if not Action then return end
	task.spawn(function()
		while Hum.Parent do
			task.wait(math.random(40, 90) / 10)
			if not Hum.Parent then break end
			for _ = 1, math.random(3, 6) do
				Action:Play(0.15)
				Action.Stopped:Wait()
			end
		end
	end)
end

function Local.Area(Model: Instance?): (CFrame?, Vector3?)
	if not Model then return nil, nil end
	local Ok, CF, Size = pcall(function() return Model:GetBoundingBox() end)
	if Ok then return CF, Size end
	return nil, nil
end

function Local.Bar(At: Vector3, Facing: Vector3)
	local Iron = Color3.fromRGB(40, 38, 42)
	local Right = Facing:Cross(Vector3.yAxis).Unit
	local function part(Size, CF)
		local P = Instance.new(`Part`)
		P.Anchored, P.CanCollide, P.CastShadow = true, true, true
		P.Material = Enum.Material.Metal
		P.Color = Iron
		P.Size = Size
		P.CFrame = CF
		P.Parent = Folder
	end
	for _, S in { -1, 1 } do part(Vector3.new(0.3, 8, 0.3), CFrame.new(At + Right * 1.8 * S + Vector3.new(0, 4, 0))) end
	part(Vector3.new(4, 0.22, 0.22), CFrame.lookAt(At + Vector3.new(0, 7.8, 0), At + Vector3.new(0, 7.8, 0) + Right) * CFrame.Angles(0, math.rad(90), 0))
end

function Shared.Build()
	if Folder then Folder:Destroy() end
	Folder = Instance.new(`Folder`)
	Folder.Name = `NHAmbient`
	Folder.Parent = workspace
	local Sports = workspace:FindFirstChild(`Sports`)
	local School = workspace:FindFirstChild(`School`)

	-- Gymnasium: an exercise corner at one end of the court
	local GCF, GSize = Local.Area(Sports and Sports:FindFirstChild(`Gymnasium`))
	if GCF then
		local End = GCF * CFrame.new(-GSize.X / 2 + 14, 0, 0)
		local Mid = GCF.Position
		local Spots = {
			{ `Push-up kid`, Vector3.new(0, 0, -10), function(H) Local.Reps(H, ANIM.PushIdle, ANIM.PushAction) end },
			{ `Sit-up kid`, Vector3.new(0, 0, -4), function(H) Local.Reps(H, ANIM.SitIdle, nil) end },
			{ `Pull-up kid`, Vector3.new(0, 0, 4), function(H) Local.Reps(H, ANIM.PullIdle, ANIM.PullAction) end },
		}
		for _, S in Spots do
			local Floor = Local.Floor((End * CFrame.new(S[2])).Position)
			if Floor then
				if S[1] == `Pull-up kid` then Local.Bar(Floor, (Mid - Floor) * Vector3.new(1, 0, 1)) end
				local _, H = Local.Spawn(S[1], Floor, Mid)
				if H then S[3](H) end
			end
		end
	end

	-- Hallway: a sprawled student, a barber, someone eating
	local HCF, HSize = Local.Area(School and School:FindFirstChild(`Hallway`))
	if HCF then
		local Places = {
			{ `Napping student`, -HSize.X / 2 + 18, ANIM.SideLay },
			{ `Lunch kid`, HSize.X / 2 - 34, ANIM.Eat },
		}
		for _, S in Places do
			local Floor = Local.Floor((HCF * CFrame.new(S[2], 0, HSize.Z / 2 - 2.5)).Position)
			if Floor then
				local M, H = Local.Spawn(S[1], Floor, HCF.Position)
				if H then Local.Reps(H, S[3], nil) end
			end
		end

		-- The barber works out of the nook between the Records Office and the Boiler Yard, facing the hallway,
		-- so he isn't standing in front of anyone in the corridor (owner, 2026-11-02). Falls back to the hallway.
		local Records = School:FindFirstChild(`Quests`) and School.Quests:FindFirstChild(`RecordsOffice`)
		local Yard = School:FindFirstChild(`BoilerYard`)
		local Spot
		if Records and Yard then
			local RCF0, RSize0 = Records:GetBoundingBox()
			local YCF0, YSize0 = Yard:GetBoundingBox()
			local X = ((RCF0.Position.X + RSize0.X / 2) + (YCF0.Position.X - YSize0.X / 2)) / 2
			Spot = Local.Floor(Vector3.new(X, HCF.Position.Y + 2, HCF.Position.Z - HSize.Z / 2 - 16))
		end
		Spot = Spot or Local.Floor((HCF * CFrame.new(HSize.X / 2 - 22, 0, HSize.Z / 2 - 2.5)).Position)
		if Spot then
			local M, H = Local.Spawn(`Barber`, Spot, Vector3.new(Spot.X, Spot.Y, HCF.Position.Z))
			if M then game:GetService(`CollectionService`):AddTag(M:FindFirstChild(`HumanoidRootPart`) or M, `NHBarber`) end -- hair at the barber
			if H then Local.Reps(H, ANIM.Barber, nil) end
		end
	end

	-- Detention (R106): a kid serving time
	local RCF, RSize = Local.Area(School and School:FindFirstChild(`R106`))
	if RCF then
		local Floor = Local.Floor((RCF * CFrame.new(RSize.X / 2 - 4, 0, RSize.Z / 2 - 4)).Position)
		if Floor then
			local _, H = Local.Spawn(`Detention kid`, Floor, RCF.Position)
			if H then Local.Reps(H, ANIM.Prisoner, nil) end
		end
	end
	-- Seated and leaning students (batch 2). Seats are props without Seat parts: sit them on the geometry.
	local function sitOn(Name: string, Prop: Model?, Id: number, Lift: number, Side: number?)
		if not Prop then return end
		local CF = Prop:GetPivot()
		local Seat = CF * CFrame.new(Side or 0, 0, 0)
		local M, H = Local.Spawn(Name, Seat.Position, (Seat * CFrame.new(0, 0, -5)).Position)
		if not (M and H) then return end
		-- the seat surface (Services.Features.Seats: the props don't take raycasts)
		local SeatY = Seats.Top(Prop, Side).Y
		local Root = M:FindFirstChild(`HumanoidRootPart`) :: BasePart
		local Want = CFrame.lookAt(Vector3.new(Seat.Position.X, SeatY + Lift, Seat.Position.Z), (Seat * CFrame.new(0, 0, -5)).Position * Vector3.new(1, 0, 1) + Vector3.new(0, SeatY + Lift, 0))
		-- move the model so its ROOT lands there (the model pivot isn't the root)
		M:PivotTo(Want * Root.CFrame:Inverse() * M:GetPivot())
		M:SetAttribute(`NHSeated`, true)
		Local.Reps(H, Id, nil)
		local Back = -((Seat * CFrame.new(0, 0, -5)).Position - Seat.Position) * Vector3.new(1, 0, 1)
		Back = if Back.Magnitude > 0 then Back.Unit else Vector3.zero
		task.spawn(function()
			local Animator = H:FindFirstChildOfClass(`Animator`)
			local t0 = os.clock()
			repeat
				task.wait(0.3)
				local Playing = Animator and Animator:GetPlayingAnimationTracks() or {}
				local ok = false
				for _, T in Playing do if T.Length > 0 then ok = true end end
			until ok or os.clock() - t0 > 15
			task.wait(0.7)
			pcall(Local.SeatSettle, M, Prop, Vector3.new(Seat.Position.X, SeatY, Seat.Position.Z), Back)
			task.wait(4)
			pcall(Local.SeatSettle, M, Prop, Vector3.new(Seat.Position.X, SeatY, Seat.Position.Z), Back)
		end)
	end
	local Props = School and School:FindFirstChild(`NHProps`)
	local Sofa, Arm1, Arm2, Chair
	local Teachers = {}
	for _, P in (Props and Props:GetChildren()) or {} do
		if P.Name == `Sofa` and not Sofa then Sofa = P
		elseif P.Name == `Armchair` then if not Arm1 then Arm1 = P elseif not Arm2 then Arm2 = P end
		elseif P.Name == `StudentChair` and not Chair then Chair = P
		elseif P.Name == `TeacherChair` then table.insert(Teachers, P) end
	end
	-- (1.46.1) an R6 student (about 3.6 studs across with the arms) is wider than the 2.7-stud armchairs, so a sitter's
	-- arms always went through the armrests: the Thinker sits in the staff room's armless teacher chair nearest the
	-- armchair instead, and the slacker in the middle of the sofa, clear of both armrests
	local Thinking
	for _, T in Teachers do
		if Arm1 and (not Thinking or (T:GetPivot().Position - Arm1:GetPivot().Position).Magnitude < (Thinking:GetPivot().Position - Arm1:GetPivot().Position).Magnitude) then Thinking = T end
	end
	sitOn(`Staff-room slacker`, Sofa, ANIM.SitChill, 1.05, 0)
	sitOn(`Thinker`, Thinking or Arm1, ANIM.SitThinking, 1.05)
	sitOn(`Early bird`, Chair, ANIM.Sitting, 1.05)
	-- a student leaning on the hallway wall
	if HCF then
		local At = (HCF * CFrame.new(-HSize.X / 2 + 34, 0, -HSize.Z / 2 + 3))
		local Floor = Local.Floor(At.Position)
		if Floor then
			local M, H = Local.Spawn(`Leaning kid`, Floor, (At * CFrame.new(0, 0, 5)).Position)
			if H then Local.Reps(H, ANIM.Lean, nil) end
		end
	end
	-- a gym regular curling the barbell from the owner's Sean White model
	local GCF2, GSize2 = Local.Area(Sports and Sports:FindFirstChild(`Gymnasium`))
	local BarbellSrc = workspace:FindFirstChild(`Sean White`) and workspace[`Sean White`]:FindFirstChild(`BarbellModel`)
	if GCF2 and BarbellSrc then
		local Floor = Local.Floor((GCF2 * CFrame.new(-GSize2.X / 2 + 14, 0, 10)).Position) -- beside the push-up / pull-up corner
		if Floor then
			local M, H = Local.Spawn(`Gym regular`, Floor, GCF2.Position)
			if M and H then
				local Bar = BarbellSrc:Clone()
				for _, D in Bar:GetDescendants() do
					if D:IsA(`BasePart`) then D.Anchored = false D.CanCollide = false D.Massless = true end
					if D:IsA(`Motor6D`) then D.Part0 = M:FindFirstChild(`Right Arm`) end
				end
				Bar.Parent = M
				Local.Reps(H, ANIM.Barbell, nil)
			end
		end
	end
end

---| (phase6-infirmary) the Infirmary's ambient patient |---
-- Lies on bed 1 (School.Infirmary.Props.DormBed_Infirmary1) with the LayingIdle gesture while the Nurse is at her post
-- (Features.Infirmary.Nurse: the school day) and no student has the bed (Schedules sets NHInfirmaryTaken). The bed
-- carries NHAmbientPatient while they lie there, so Schedules sends sick students to bed 2 and the standing spots first.
-- They come and go only with no player within PATIENT_NEAR studs of the bed, so nobody sees them pop.
local PATIENT_NEAR = 30
local PATIENT_SHIFT, PATIENT_SINK = 0.9, 0.12 -- torso toward the pillow; how far the body sinks into the bedding
local Patient: Model? = nil

-- lay a posed model on a bed: turn it (about the vertical) so its head points to the bed's head (-LookVector), centre
-- the torso on the mattress, and rest the body's lowest point on the bedding top (Seats.Top: the bed's SeatHeight)
function Local.LieOn(Model: Model, Bed: Model)
	local Root = Model:FindFirstChild(`HumanoidRootPart`) :: BasePart
	local Torso = Model:FindFirstChild(`Torso`) :: BasePart
	local Head = Model:FindFirstChild(`Head`) :: BasePart
	if not (Root and Torso and Head) then return end
	local BedCF = Bed:GetPivot()
	local HeadDir = -BedCF.LookVector * Vector3.new(1, 0, 1)
	local Body = (Head.Position - Torso.Position) * Vector3.new(1, 0, 1)
	if Body.Magnitude < 0.2 or HeadDir.Magnitude < 0.1 then return end
	local Yaw = math.atan2(Body.Unit.X, Body.Unit.Z) - math.atan2(HeadDir.Unit.X, HeadDir.Unit.Z)
	local Turn = CFrame.new(Torso.Position) * CFrame.Angles(0, -Yaw, 0) * CFrame.new(-Torso.Position)
	Model:PivotTo(Turn * Model:GetPivot())
	-- the lowest point of the body now (limbs, torso, head: not accessories), and where the torso should be
	local Low = math.huge
	for _, N in { `Torso`, `Head`, `Left Arm`, `Right Arm`, `Left Leg`, `Right Leg` } do
		local P = Model:FindFirstChild(N)
		if P and P:IsA(`BasePart`) then
			local CF, Sz = P.CFrame, P.Size / 2
			for _, X in { -1, 1 } do for _, Y in { -1, 1 } do for _, Z in { -1, 1 } do
				Low = math.min(Low, (CF * Vector3.new(X * Sz.X, Y * Sz.Y, Z * Sz.Z)).Y)
			end end end
		end
	end
	local Top = Seats.Top(Bed)
	local Want = Vector3.new(BedCF.Position.X, 0, BedCF.Position.Z) + HeadDir.Unit * PATIENT_SHIFT
	local Move = Vector3.new(Want.X - Torso.Position.X, (Top.Y - PATIENT_SINK) - Low, Want.Z - Torso.Position.Z)
	Model:PivotTo(CFrame.new(Move) * Model:GetPivot())
end

function Local.PatientWanted(Bed: Model): boolean
	if Bed:GetAttribute(`NHInfirmaryTaken`) then return false end
	local Ok, Nurse = pcall(function() return require(ServerScriptService.Services.Features.Infirmary).Nurse() end)
	return Ok and Nurse ~= nil
end

function Local.PatientShow(Bed: Model)
	local GCfg = require(ReplicatedStorage.Config.Gestures)
	local Clip = GCfg.Clips.LayingIdle
	local BedCF = Bed:GetPivot()
	local At = BedCF.Position
	local M, H = Local.Spawn(`Infirmary patient`, Vector3.new(At.X, Seats.Top(Bed).Y, At.Z), At - BedCF.LookVector * 5)
	if not (M and H and Clip and Clip.Id ~= 0) then if M then M:Destroy() end return end
	M:SetAttribute(`NHActivity`, `Resting in the infirmary`)
	for _, P in M:GetDescendants() do if P:IsA(`BasePart`) then P.CanCollide = false end end
	Patient = M
	Bed:SetAttribute(`NHAmbientPatient`, true)
	local T = Local.Track(H, Clip.Id, true)
	if not T then return end
	T:Play(0)
	task.spawn(function() -- once the pose is on, lay them on the bed (twice: the clip settles over its first second)
		local t0 = os.clock()
		repeat task.wait(0.2) until T.Length > 0 or os.clock() - t0 > 15 or Patient ~= M
		for _ = 1, 2 do
			task.wait(0.8)
			if Patient ~= M or not M.Parent then return end
			pcall(Local.LieOn, M, Bed)
		end
		M:SetAttribute(`NHLaid`, true)
	end)
end

function Local.PatientHide(Bed: Model)
	if Patient then Patient:Destroy() Patient = nil end
	Bed:SetAttribute(`NHAmbientPatient`, nil)
end

function Local.PlayerNear(P: Vector3, R: number): boolean
	for _, Pl in Players:GetPlayers() do
		local Root = Pl.Character and Pl.Character:FindFirstChild(`HumanoidRootPart`)
		if Root and (Root.Position - P).Magnitude <= R then return true end
	end
	return false
end

function Local.PatientLoop()
	while true do
		local Room = workspace:FindFirstChild(`School`) and workspace.School:FindFirstChild(`Infirmary`)
		local Bed = Room and Room:FindFirstChild(`Props`) and Room.Props:FindFirstChild(`DormBed_Infirmary1`)
		if Bed then
			local Want = Local.PatientWanted(Bed)
			local Has = Patient ~= nil and Patient.Parent ~= nil
			if Want ~= Has and not Local.PlayerNear(Bed:GetPivot().Position, PATIENT_NEAR) then
				if Want then pcall(Local.PatientShow, Bed) else Local.PatientHide(Bed) end
			end
		end
		task.wait(4)
	end
end

-- tests: show / hide the patient now (ignores the near-player rule); "get" returns the model
function Shared.PatientForTests(Cmd: string): any
	local Bed = workspace.School.Infirmary.Props.DormBed_Infirmary1
	if Cmd == `show` then Local.PatientHide(Bed) Local.PatientShow(Bed) return Patient ~= nil
	elseif Cmd == `hide` then Local.PatientHide(Bed) return true end
	return Patient
end

-- (phase6-infirmary) ServerStorage.NHInfirmaryProbe (Studio only): the patient, and Schedules' infirmary test hooks
function Local.Probe()
	local B = game:GetService(`ServerStorage`):FindFirstChild(`NHInfirmaryProbe`) or Instance.new(`BindableFunction`)
	B.Name = `NHInfirmaryProbe`
	B.OnInvoke = function(Cmd: string, A: any, Bv: any)
		local Ok, R = pcall(function()
			if Cmd == `Patient` then
				local Bed = workspace.School.Infirmary.Props.DormBed_Infirmary1
				if A == `show` or A == `hide` then Shared.PatientForTests(A) task.wait(if A == `show` then 3.5 else 0) end
				local M = Patient
				local Info = { Shown = M ~= nil and M.Parent ~= nil; Flag = Bed:GetAttribute(`NHAmbientPatient`); Wanted = Local.PatientWanted(Bed) }
				if M and M.Parent then
					Info.Laid = M:GetAttribute(`NHLaid`)
					for _, N in { `Head`, `Torso`, `Left Leg`, `Right Leg` } do
						local P = M:FindFirstChild(N)
						if P then Info[N] = { P.Position.X, P.Position.Y, P.Position.Z } end
					end
					Info.Top = Seats.Top(Bed).Y
					Info.Bed = { Bed:GetPivot().Position.X, Bed:GetPivot().Position.Z }
				end
				return Info
			end
			return require(ServerScriptService.Services.Features.Schedules).InfirmaryForTests(Cmd, A, Bv)
		end)
		return if Ok then R else { Err = tostring(R) }
	end
	B.Parent = game:GetService(`ServerStorage`)
end

function Shared.OnStart()
	task.delay(3, function()
		local Ok, Err = pcall(Shared.Build)
		if not Ok then warn(`[AmbientNpcs] {Err}`) end
		task.spawn(Local.PatientLoop) -- (phase6-infirmary)
		if game:GetService(`RunService`):IsStudio() then Local.Probe() end -- (phase6-infirmary) Studio checks only
	end)
	-- feeding moved to the N-key race actions (ActionManager.Misc.RaceAction / Features.RaceAction)
end

return Shared
