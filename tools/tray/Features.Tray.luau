--[[
	Lunch trays (server). Services.Features.Tray                            (props batch 54, 2026-11-12)
	Config: ReplicatedStorage.Config.Tray. Client: Controllers.World.TrayFx (keeps the posed shoulders still).

	Players: equipping a lunch-tray meal (a Tool whose NHItem is in Tray.Items) holds it in both hands: both shoulders'
	C0 are posed, the hand grip is dropped and the tray is welded to the torso (Tray.Hold.Offset). Unequipping lets go.
	  Using it        Services.Features.Inventory calls Shared.OnUse: EatStand (or EatSit while seated) loops for the
	                  meal's Duration; for a Grimace item (no tray) the Grimace clip plays before the bite.
	  Sitting         Humanoid.Seated: SitDown, then the tray goes on the table top in front (a raycast) or the lap;
	                  standing: StandUp and the tray comes back to the hands.
	  Standing still  after Tray.IdleAfter seconds, QueueIdle loops until the character moves, sits or eats.
	  Spill           a hit of Tray.Spill.Damage health or more, FallingDown / Ragdoll / Physics, or Downed: Spill plays,
	                  a copy of the tray tumbles away (6 s), one meal is taken (Inventory.Take), and the hold ends.
	  Return          parts tagged NHTrayReturn get a "Return tray" prompt: Return plays, a copy of the tray is set on
	                  the rack, and the tray is put away (unequipped, not lost). A rack with Attachments Slot1, Slot2, ...
	                  (a tray's bottom centre, its long side along the attachment's X) fills them in turn, the oldest
	                  making way when all are full, and keeps each copy Tray.Rack.Keep seconds (the batch 55 trolley); a
	                  slot with a SlotNInto beside it is a conveyor: the copy rolls there in Tray.Rack.Roll seconds and is
	                  gone (the batch 55 hatch). A rack without slots gets the copy on its top for 30 s.
	NPCs (for a lunch period): Shared.Hold(Char, TrayModelOrPart, Id), Shared.Release(Char), Shared.Eat(Char, Seconds),
	Shared.Spill(Char), Shared.Return(Char, RackPart?). An NPC's tray is just dropped on Spill (no inventory).
	Holders carry the CollectionService tag NHTrayHolder and the attribute NHTray (the item id); NHTrayAnim is set while
	a clip that moves the arms plays, so TrayFx lets go of the shoulders.
]]
local CollectionService = game:GetService(`CollectionService`)
local Debris = game:GetService(`Debris`)
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local ServerStorage = game:GetService(`ServerStorage`)
local TweenService = game:GetService(`TweenService`)

local Tray = require(ReplicatedStorage.Config.Tray)

local Shared = {}
local Local = {}

local State = {}          -- [Char] = { Id, Part, Weld, Player, Tracks = {}, Seated, Still, Eating, Spilled }
local AnimIds = {}        -- name -> content id ("" when there is none)
local ARM_CLIPS = { EatStand = true; EatSit = true; Spill = true; SitDown = true; StandUp = true; Return = true }

---| clips |---

-- the published id, or (in Studio) the KeyframeSequence registered from ServerStorage.NHTrayAnims
function Local.AnimId(Name: string): string
	if AnimIds[Name] then return AnimIds[Name] end
	local Id = Tray.Anims[Name]
	local Out = ``
	if typeof(Id) == `number` and Id > 0 then
		Out = `rbxassetid://{Id}`
	elseif RunService:IsStudio() then
		local Folder = ServerStorage:FindFirstChild(`NHTrayAnims`)
		local K = Folder and Folder:FindFirstChild(Name)
		if K then
			local Ok, Url = pcall(function() return game:GetService(`KeyframeSequenceProvider`):RegisterKeyframeSequence(K) end)
			if Ok then Out = Url end
		end
	end
	AnimIds[Name] = Out
	return Out
end

function Local.Track(Char: Model, Name: string): AnimationTrack?
	local S = State[Char]
	if S and S.Tracks[Name] then return S.Tracks[Name] end
	local Hum = Char:FindFirstChildOfClass(`Humanoid`)
	local Animator = Hum and Hum:FindFirstChildOfClass(`Animator`)
	local Id = Local.AnimId(Name)
	if not (Animator and Id ~= ``) then return nil end
	local A = Instance.new(`Animation`)
	A.AnimationId = Id
	local Ok, T = pcall(function() return Animator:LoadAnimation(A) end)
	if not Ok then return nil end
	if S then S.Tracks[Name] = T end
	return T
end

-- play a clip; the arm clips set NHTrayAnim while they run so TrayFx lets the shoulders move
function Local.Play(Char: Model, Name: string, Looped: boolean?, Fade: number?): AnimationTrack?
	local T = Local.Track(Char, Name)
	if not T then return nil end
	T.Looped = Looped == true
	if ARM_CLIPS[Name] then
		Char:SetAttribute(`NHTrayAnim`, Name)
		T.Stopped:Once(function()
			if Char.Parent and Char:GetAttribute(`NHTrayAnim`) == Name then Char:SetAttribute(`NHTrayAnim`, nil) end
		end)
	end
	T:Play(Fade or 0.2)
	-- seated, the chair's Sitting pose (Controllers.World.PlayerSeat) plays at Action4 and would hide the arms: play over it
	-- at the same priority and outweigh it 8 to 1 (it still holds the legs, which these clips don't key)
	local Hum = Char:FindFirstChildOfClass(`Humanoid`)
	if Hum and Hum.Sit then
		T.Priority = Enum.AnimationPriority.Action4
		T:AdjustWeight(8, Fade or 0.2)
	end
	return T
end

function Local.Stop(Char: Model, Name: string, Fade: number?)
	local S = State[Char]
	local T = S and S.Tracks[Name]
	if T and T.IsPlaying then T:Stop(Fade or 0.25) end
end

---| the hold |---

function Local.Pose(Char: Model, On: boolean)
	local Torso = Char:FindFirstChild(`Torso`)
	if not Torso then return end
	for _, Side in { `Right`, `Left` } do
		local M = Torso:FindFirstChild(`{Side} Shoulder`) :: Motor6D?
		local A = if Side == `Right` then Tray.Hold.R else Tray.Hold.L
		if not (M and A) then continue end
		local Base = M:GetAttribute(`NHBaseC0`)
		if Base == nil then Base = M.C0 M:SetAttribute(`NHBaseC0`, Base) end
		if On then
			local Pitch, Yaw = math.rad(A[1]), math.rad(A[2])
			M.C0 = if Side == `Right` then Base * CFrame.Angles(0, Yaw, 0) * CFrame.Angles(0, 0, Pitch)
				else Base * CFrame.Angles(0, -Yaw, 0) * CFrame.Angles(0, 0, -Pitch)
		else
			M.C0 = Base
		end
	end
end

-- weld the tray to the torso: At is the tray's bottom centre for a standard torso (Vector3, scaled with this torso and
-- lifted by half the tray's height so any tray sits on its base), or an exact CFrame of the tray's centre (a table top)
function Local.Place(Char: Model, At: Vector3 | CFrame)
	local S = State[Char]
	local Torso = Char:FindFirstChild(`Torso`) :: BasePart?
	if not (S and Torso and S.Part and S.Part.Parent) then return end
	if not (S.Weld and S.Weld.Parent) then
		local W = Instance.new(`Weld`)
		W.Name = `NHTrayWeld`
		W.Part0 = Torso
		W.Part1 = S.Part
		W.Parent = S.Part
		S.Weld = W
	end
	if typeof(At) == `Vector3` then
		local K = Torso.Size.Y / 2
		S.Weld.C0 = CFrame.new(At.X * K, At.Y * K + S.Part.Size.Y / 2, At.Z * K)
	else
		S.Weld.C0 = At
	end
	S.Weld.C1 = CFrame.identity
end

-- the tool's own hand grip pins the tray to the right hand; drop it (Roblox makes a new one on each equip)
function Local.DropGrip(Char: Model)
	local Arm = Char:FindFirstChild(`Right Arm`)
	local G = Arm and Arm:FindFirstChild(`RightGrip`)
	if G then G:Destroy() end
end

function Shared.Hold(Char: Model, Part: BasePart, Id: string, P: Player?)
	if State[Char] then Shared.Release(Char) end
	local Hum = Char:FindFirstChildOfClass(`Humanoid`)
	if not (Hum and Char:FindFirstChild(`Torso`)) then return end
	State[Char] = { Id = Id; Part = Part; Player = P; Tracks = {}; Still = 0 }
	Local.DropGrip(Char)
	Local.Pose(Char, true)
	Local.Place(Char, Tray.Hold.Offset)
	Char:SetAttribute(`NHTray`, Id)
	CollectionService:AddTag(Char, `NHTrayHolder`)
	if Hum.Sit and Hum.SeatPart then Local.Seated(Char, true, Hum.SeatPart, true) end
end

function Shared.Release(Char: Model)
	local S = State[Char]
	if not S then return end
	State[Char] = nil
	-- the spill and the return finish on their own (they end with the arms at rest)
	for Name, T in S.Tracks do if T.IsPlaying and Name ~= `Spill` and Name ~= `Return` then T:Stop(0.2) end end
	if S.Weld then S.Weld:Destroy() end
	if Char.Parent then
		Local.Pose(Char, false)
		Char:SetAttribute(`NHTray`, nil)
		Char:SetAttribute(`NHTrayAnim`, nil)
		CollectionService:RemoveTag(Char, `NHTrayHolder`)
	end
end

function Shared.Holding(Char: Model): string?
	local S = State[Char]
	return S and S.Id or nil
end

---| eating |---

function Shared.Eat(Char: Model, Seconds: number)
	local S = State[Char]
	if not S then return false end
	Local.Stop(Char, `QueueIdle`)
	local Name = if S.Seated then `EatSit` else `EatStand`
	local T = Local.Play(Char, Name, true, 0.2)
	if not T then return false end
	S.Eating = true
	task.delay(Seconds, function()
		if State[Char] == S then S.Eating = false S.Still = 0 end
		if T.IsPlaying then T:Stop(0.3) end
	end)
	return true
end

-- from Services.Features.Inventory's Use: true when a tray clip plays in place of the usual eating clip
function Shared.OnUse(P: Player, Hum: Humanoid, It): boolean
	local Char = Hum.Parent
	if not Char then return false end
	if Tray.Grimace[It.Id] then Local.Play(Char, `Grimace`, false, 0.1) end
	if Tray.Items[It.Id] and State[Char] and State[Char].Id == It.Id then
		return Shared.Eat(Char, math.max(3, It.Duration or 6))
	end
	return false
end

---| sitting |---

-- the table top in front of the seated torso, as an Offset in torso space (nil when there is none)
function Local.TableOffset(Char: Model): CFrame?
	local Torso = Char:FindFirstChild(`Torso`) :: BasePart?
	local S = State[Char]
	if not (Torso and S and S.Part) then return nil end
	local Params = RaycastParams.new()
	Params.FilterType = Enum.RaycastFilterType.Exclude
	Params.FilterDescendantsInstances = { Char, S.Part }
	local Look = Torso.CFrame.LookVector * Vector3.new(1, 0, 1)
	if Look.Magnitude < 0.1 then return nil end
	Look = Look.Unit
	for _, Ahead in { 1.4, 1.8, 2.2, Tray.TableReach } do
		local From = Torso.Position + Look * Ahead + Vector3.new(0, 0.6, 0)
		local Hit = workspace:Raycast(From, Vector3.new(0, -2.6, 0), Params)
		-- only furniture: a part of a character (a student at the next desk) or anything loose doesn't count
		local Body = Hit and Hit.Instance:FindFirstAncestorWhichIsA(`Model`)
		if Hit and (not Hit.Instance.Anchored or (Body and Body:FindFirstChildOfClass(`Humanoid`))) then Hit = nil end
		if Hit and Hit.Normal.Y > 0.9 and Hit.Position.Y > Torso.Position.Y - 1.6 and Hit.Position.Y < Torso.Position.Y + 0.3 then
			local H = S.Part.Size.Y / 2 + 0.05   -- a hair above the top: the chair settles the body a little after this
			local World = CFrame.lookAt(Hit.Position + Vector3.new(0, H, 0), Hit.Position + Vector3.new(0, H, 0) + Look)
			return Torso.CFrame:ToObjectSpace(World)
		end
	end
	return nil
end

function Local.Seated(Char: Model, On: boolean, Seat: Instance?, Quiet: boolean?)
	local S = State[Char]
	if not S then return end
	Local.Stop(Char, `QueueIdle`)
	if On then
		S.Seated = true
		if not Quiet then Local.Play(Char, `SitDown`, false, 0.15) end
		task.delay(if Quiet then 0 else 0.45, function()
			if State[Char] ~= S or not S.Seated then return end
			Local.Place(Char, Local.TableOffset(Char) or Tray.Lap)
		end)
	else
		S.Seated = false
		Local.Play(Char, `StandUp`, false, 0.15)
		task.delay(0.3, function()
			if State[Char] == S and not S.Seated then Local.Place(Char, Tray.Hold.Offset) end
		end)
	end
end

---| spilling |---

-- a copy of the tray that tumbles away out of the hands and fades
function Local.Tumble(Char: Model, Part: BasePart)
	local Root = Char:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	local C = Part:Clone()
	for _, D in { C, table.unpack(C:GetDescendants()) } do
		if D:IsA(`BasePart`) then D.Anchored = false D.CanCollide = true D.CanQuery = false D.CanTouch = false D.Massless = false end
		if D:IsA(`Weld`) or D:IsA(`Motor6D`) then D:Destroy() end
	end
	C.Name = `SpilledTray`
	C.CFrame = Part.CFrame
	C.Parent = workspace
	local Fwd = Root and Root.CFrame.LookVector or Vector3.new(0, 0, -1)
	C.AssemblyLinearVelocity = Fwd * 9 + Vector3.new(0, 11, 0)
	C.AssemblyAngularVelocity = Vector3.new(math.random(-8, 8), math.random(-3, 3), math.random(-8, 8))
	Debris:AddItem(C, 6)
end

function Shared.Spill(Char: Model)
	local S = State[Char]
	if not S or S.Spilled then return end
	S.Spilled = true
	Local.Stop(Char, `QueueIdle`, 0.05)
	Local.Stop(Char, `EatStand`, 0.05)
	Local.Stop(Char, `EatSit`, 0.05)
	local T = Local.Play(Char, `Spill`, false, 0.05)
	-- the real tray hides while a copy tumbles away, and shows again before it goes back in the backpack
	local Hidden = {}
	task.delay(0.18, function()
		if S.Part and S.Part.Parent then
			Local.Tumble(Char, S.Part)
			for _, D in { S.Part, table.unpack(S.Part:GetDescendants()) } do
				if D:IsA(`BasePart`) then Hidden[D] = D.Transparency D.Transparency = 1 end
			end
		end
	end)
	task.delay(if T then math.max(0.6, T.Length) else 0.8, function()
		for D, Was in Hidden do if D.Parent then D.Transparency = Was end end
		local P = S.Player
		if P then
			local Hum = Char:FindFirstChildOfClass(`Humanoid`)
			if Hum then Hum:UnequipTools() end
			pcall(function() require(ServerScriptService.Services.Features.Inventory).Take(P, S.Id, 1) end)
			pcall(function()
				require(ServerScriptService.Services.Features.Notifications).Notify(P, { Title = `You spilled your lunch!`;
					Text = `The tray went flying. Watch where you're going next time.`; Kind = `Info`; Duration = 3 })
			end)
		end
		if State[Char] == S then Shared.Release(Char) end
		if not P and S.Part and S.Part.Parent then S.Part:Destroy() end   -- an NPC's tray is simply gone
	end)
end

---| returning |---

local Racked = {}         -- [slot Attachment] = the tray copy resting in it

-- the slot a returned tray goes in: the first empty one, else the one filled longest ago (its copy makes way); nil when
-- the rack has no slots
function Local.Slot(Rack: BasePart): Attachment?
	local Oldest, OldestAt = nil, math.huge
	for I = 1, 64 do
		local A = Rack:FindFirstChild(`Slot{I}`)
		if not (A and A:IsA(`Attachment`)) then break end
		local C = Racked[A]
		if not (C and C.Parent) then return A end
		local At = C:GetAttribute(`At`) or 0
		if At < OldestAt then Oldest, OldestAt = A, At end
	end
	if Oldest then
		Racked[Oldest]:Destroy()
		Racked[Oldest] = nil
	end
	return Oldest
end

-- set a copy of the tray on the rack: in a slot (rolled away on a conveyor), else on top
function Local.Rest(Rack: BasePart, C: BasePart)
	C.Name = `ReturnedTray`
	local Slot = Local.Slot(Rack)
	if not Slot then
		C.CFrame = Rack.CFrame * CFrame.new(0, Rack.Size.Y / 2 + C.Size.Y / 2, 0)
		C.Parent = workspace
		Debris:AddItem(C, 30)
		return
	end
	local Up = CFrame.new(0, C.Size.Y / 2, 0)
	C.CFrame = Slot.WorldCFrame * Up
	C:SetAttribute(`At`, os.clock())
	C.Parent = workspace
	Racked[Slot] = C     -- (a rolling copy keeps its slot until it's gone, so a second tray takes the next one)
	local Into = Rack:FindFirstChild(Slot.Name .. `Into`)
	if Into and Into:IsA(`Attachment`) then
		local Tw = TweenService:Create(C, TweenInfo.new(Tray.Rack.Roll, Enum.EasingStyle.Linear), { CFrame = Into.WorldCFrame * Up })
		Tw:Play()
		Tw.Completed:Once(function() if C.Parent then C:Destroy() end end)
		Debris:AddItem(C, Tray.Rack.Roll + 1)
	else
		Debris:AddItem(C, Tray.Rack.Keep)
	end
end

function Shared.Return(Char: Model, Rack: BasePart?)
	local S = State[Char]
	if not S then return end
	Local.Stop(Char, `QueueIdle`, 0.05)
	local T = Local.Play(Char, `Return`, false, 0.12)
	-- at 0.55 s the tray is let go on the rack (a copy rests there, the real one hides); the carry ends with the clip,
	-- whose last key is the arms back at the sides
	local Hidden = {}
	task.delay(0.55, function()
		if State[Char] ~= S then return end
		if Rack and S.Part then
			local C = S.Part:Clone()
			for _, D in { C, table.unpack(C:GetDescendants()) } do
				if D:IsA(`BasePart`) then D.Anchored = true D.CanCollide = false D.CanQuery = false end
				if D:IsA(`Weld`) or D:IsA(`Motor6D`) or D:IsA(`WeldConstraint`) then D:Destroy() end
			end
			Local.Rest(Rack, C)
		end
		if S.Part then
			for _, D in { S.Part, table.unpack(S.Part:GetDescendants()) } do
				if D:IsA(`BasePart`) then Hidden[D] = D.Transparency D.Transparency = 1 end
			end
		end
	end)
	task.delay(if T then math.max(0.7, T.Length) else 1.0, function()
		for D, Was in Hidden do if D.Parent then D.Transparency = Was end end
		if State[Char] ~= S then return end
		if S.Player then
			local Hum = Char:FindFirstChildOfClass(`Humanoid`)
			if Hum then Hum:UnequipTools() end
		else
			Shared.Release(Char)
			if S.Part then S.Part:Destroy() end
		end
	end)
end

function Local.Rack(Part: Instance)
	if not Part:IsA(`BasePart`) or Part:FindFirstChild(`NHTrayReturnPrompt`) then return end
	local Pr = Instance.new(`ProximityPrompt`)
	Pr.Name = `NHTrayReturnPrompt`
	Pr.ActionText = `Return tray`
	Pr.ObjectText = `Tray rack`
	Pr.HoldDuration = 0.3
	Pr.MaxActivationDistance = 7
	Pr.RequiresLineOfSight = false
	Pr.Parent = Part
	Pr.Triggered:Connect(function(P)
		local Char = P.Character
		if Char and State[Char] then Shared.Return(Char, Part) end
	end)
end

---| players |---

function Local.Watch(P: Player, Char: Model)
	local Hum = Char:WaitForChild(`Humanoid`, 10) :: Humanoid?
	if not Hum then return end
	local function check(T: Instance)
		if not T:IsA(`Tool`) then return end
		local Id = T:GetAttribute(`NHItem`)
		local H = T:FindFirstChild(`Handle`) :: BasePart?
		if Id and Tray.Items[Id] and H then
			task.defer(function()
				if T.Parent == Char then Shared.Hold(Char, H, Id, P) end
			end)
		end
	end
	Char.ChildAdded:Connect(check)
	Char.ChildRemoved:Connect(function(T)
		local S = State[Char]
		if S and T:IsA(`Tool`) and T:FindFirstChild(`Handle`) == S.Part then Shared.Release(Char) end
	end)
	for _, T in Char:GetChildren() do check(T) end
	-- a new RightGrip appears on each equip; keep the tray off the hand
	local Arm = Char:WaitForChild(`Right Arm`, 10)
	if Arm then
		Arm.ChildAdded:Connect(function(C)
			if C.Name == `RightGrip` and State[Char] then task.defer(function() if State[Char] then C:Destroy() end end) end
		end)
	end
	Hum.Seated:Connect(function(Active, Seat) Local.Seated(Char, Active, Seat) end)
	local Last = Hum.Health
	Hum.HealthChanged:Connect(function(H)
		if State[Char] and Last - H >= Tray.Spill.Damage then Shared.Spill(Char) end
		Last = H
	end)
	Hum.StateChanged:Connect(function(_, New)
		if State[Char] and (New == Enum.HumanoidStateType.FallingDown or New == Enum.HumanoidStateType.Ragdoll
			or New == Enum.HumanoidStateType.Physics) then Shared.Spill(Char) end
	end)
	Char:GetAttributeChangedSignal(`Downed`):Connect(function()
		if State[Char] and Char:GetAttribute(`Downed`) then Shared.Spill(Char) end
	end)
	Char.AncestryChanged:Connect(function(_, Parent) if not Parent then State[Char] = nil end end)
end

-- standing still with a tray: the queue idle
function Local.Step(Dt: number)
	for Char, S in State do
		if not Char.Parent then State[Char] = nil continue end
		local Hum = Char:FindFirstChildOfClass(`Humanoid`)
		if not Hum then continue end
		local Moving = Hum.MoveDirection.Magnitude > 0.1 or Hum.FloorMaterial == Enum.Material.Air
		if Moving or S.Seated or S.Eating or S.Spilled then
			S.Still = 0
			Local.Stop(Char, `QueueIdle`, 0.2)
		else
			S.Still += Dt
			if S.Still >= Tray.IdleAfter then
				local T = S.Tracks.QueueIdle
				if not (T and T.IsPlaying) then Local.Play(Char, `QueueIdle`, true, 0.4) end
			end
		end
	end
end

function Shared.OnStart()
	local function onPlayer(P: Player)
		P.CharacterAdded:Connect(function(C) Local.Watch(P, C) end)
		if P.Character then task.spawn(Local.Watch, P, P.Character) end
	end
	Players.PlayerAdded:Connect(onPlayer)
	for _, P in Players:GetPlayers() do onPlayer(P) end
	CollectionService:GetInstanceAddedSignal(`NHTrayReturn`):Connect(Local.Rack)
	for _, R in CollectionService:GetTagged(`NHTrayReturn`) do Local.Rack(R) end
	local Acc = 0
	RunService.Heartbeat:Connect(function(Dt)
		Acc += Dt
		if Acc < 0.1 then return end
		local Ok, Err = pcall(Local.Step, Acc)
		Acc = 0
		if not Ok then warn(`[Tray] {Err}`) end
	end)
end

return Shared
