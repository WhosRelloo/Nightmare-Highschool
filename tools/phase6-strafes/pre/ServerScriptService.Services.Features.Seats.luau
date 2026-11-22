--[[
	Seats (server). Services.Features.Seats
	Where an NPC's hips go on a seat prop, for the background students (Services.Features.Schedules) and the
	ambient sitters (Services.Features.AmbientNpcs).

	The school's seat props are single meshes with CanQuery off (so nothing can raycast onto them), so the seat
	surface comes from the models themselves: the height of the top of each prop's seat above its base, in studs,
	from art/props/nh_props.py and nh_props_batch3.py (1 Blender unit = 1 stud, base on the ground). A prop can
	override it with the attribute SeatHeight. Anything else falls back to a raycast (for greybox seats that do take
	queries), then to 1.2 studs above the pivot.

	Front = the prop's LookVector (its -Y in Blender), which is how every seat prop is exported.
]]

local Seats = {}

Seats.Heights = {
	StudentChair = 1.545;  -- oak seat, 0.09 thick, centred at 1.5
	TeacherChair = 1.72;   -- leather cushion, 0.14 thick, centred at 1.65
	Armchair = 1.575;      -- leather seat, 0.35 thick, centred at 1.4
	Sofa = 1.525;          -- leather cushions, 0.35 thick, centred at 1.35
	HallBench = 1.465;     -- oak slats, 0.09 thick, at 1.42
}

-- bench and sofa places, sideways from the centre (studs)
Seats.Places = {
	HallBench = { -1.2, 1.2 };
	Sofa = { -1.3, 1.3 };
}

-- the prop's kind from its name ("HallBench_53.5" -> "HallBench")
function Seats.Kind(Prop: Instance): string
	return (Prop.Name:match(`^(%a+)`)) or Prop.Name
end

function Seats.Height(Prop: Instance): number?
	local H = Prop:GetAttribute(`SeatHeight`)
	if typeof(H) == `number` then return H end
	return Seats.Heights[Seats.Kind(Prop)]
end

-- the world point on top of the seat, Side studs sideways from the centre (+ = the prop's right)
function Seats.Top(Prop: Model, Side: number?): Vector3
	local CF = Prop:GetPivot()
	local BoxCF, Size = Prop:GetBoundingBox()
	local Base = BoxCF.Position.Y - Size.Y / 2
	local At = (CF * CFrame.new(Side or 0, 0, 0)).Position
	local H = Seats.Height(Prop)
	if H then return Vector3.new(At.X, Base + H, At.Z) end
	local RP = RaycastParams.new()
	RP.FilterType = Enum.RaycastFilterType.Include
	RP.FilterDescendantsInstances = { Prop }
	local Hit = workspace:Raycast(Vector3.new(At.X, Base + Size.Y + 2, At.Z), Vector3.new(0, -(Size.Y + 6), 0), RP)
	return Vector3.new(At.X, if Hit then Hit.Position.Y else CF.Position.Y + 1.2, At.Z)
end

-- the direction toward the backrest (flat)
function Seats.Back(Prop: Model): Vector3
	local L = Prop:GetPivot().LookVector * Vector3.new(1, 0, 1)
	return if L.Magnitude > 0 then -L.Unit else Vector3.zero
end

local function lowestTorso(Torso: BasePart): Vector3
	local cf, sz = Torso.CFrame, Torso.Size / 2
	local best
	for _, X in { -1, 1 } do for _, Y in { -1, 1 } do for _, Z in { -1, 1 } do
		local p = cf * Vector3.new(X * sz.X, Y * sz.Y, Z * sz.Z)
		if not best or p.Y < best.Y then best = p end
	end end end
	return best
end

-- the lowest point of a leg's hip end (its top face in the rest pose): where the thigh meets the seat in a sitting pose
local function thighLow(Leg: BasePart): number
	local cf, sz = Leg.CFrame, Leg.Size / 2
	local low = math.huge
	for _, X in { -1, 1 } do for _, Z in { -1, 1 } do
		low = math.min(low, (cf * Vector3.new(X * sz.X, sz.Y, Z * sz.Z)).Y)
	end end
	return low
end

-- (1.46.1) true when a body part pushes into something that isn't the seat it sits on or a floor under it
local BODY = { `Torso`, `Head`, `Left Arm`, `Right Arm` }
local function lowY(P: BasePart): number
	local cf, sz = P.CFrame, P.Size / 2
	local low = math.huge
	for _, X in { -1, 1 } do for _, Y in { -1, 1 } do for _, Z in { -1, 1 } do
		low = math.min(low, (cf * Vector3.new(X * sz.X, Y * sz.Y, Z * sz.Z)).Y)
	end end end
	return low
end
local function clipping(Model: Model, Params: OverlapParams): number
	local N = 0
	for _, Name in BODY do
		local P = Model:FindFirstChild(Name)
		if not (P and P:IsA(`BasePart`)) or P.Transparency >= 1 then continue end
		local Bottom = lowY(P)
		for _, Q in workspace:GetPartBoundsInBox(P.CFrame + Vector3.new(0, 0.1, 0), P.Size * 0.85, Params) do
			if Q.Transparency >= 0.9 then continue end
			if Q.Size.Y < 1.2 and Q.Position.Y + Q.Size.Y / 2 <= Bottom + 0.3 then continue end -- a floor or rug under the seat
			N += 1
			break
		end
	end
	return N
end

-- the props near a point (the school's prop folders), for counting them in a test
local PROP_FOLDERS = { { `School`, `NHProps` }, { `NHPropsMap` }, { `NHCliqueAreas` } }
local function nearbyParts(At: Vector3, Radius: number, Skip: { Instance }): { BasePart }
	local Out = {}
	for _, Path in PROP_FOLDERS do
		local F = workspace
		for _, N in Path do F = F and F:FindFirstChild(N) end
		for _, M in (F and F:GetChildren()) or {} do
			local Pos
			if M:IsA(`Model`) then Pos = M:GetPivot().Position elseif M:IsA(`BasePart`) then Pos = M.Position end
			if not Pos then continue end
			-- single props: only the ones close by (a prop is never much bigger than a room); areas: all of them
			if Path[#Path] ~= `NHCliqueAreas` and (Pos - At).Magnitude > Radius + 10 then continue end
			local Skipped = false
			for _, E in Skip do if M == E or M:IsDescendantOf(E) then Skipped = true break end end
			if Skipped then continue end
			local Parts = if M:IsA(`BasePart`) then { M } else M:GetDescendants()
			for _, Q in Parts do
				if Q:IsA(`BasePart`) and (Q.Position - At).Magnitude < Radius + Q.Size.Magnitude / 2 then table.insert(Out, Q) end
			end
		end
	end
	return Out
end

-- (1.46.1) slide the sitter forward (away from the backrest) until nothing behind them is pushed into: walls,
-- picture frames, the next prop. The seat itself is left out (its mesh hull would always "hit").
-- Props switch CanQuery off, so the nearby ones are counted for the test and put back afterwards.
function Seats.Unclip(Model: Model, Back: Vector3, Prop: Instance?, MaxForward: number?)
	local Torso = Model:FindFirstChild(`Torso`) :: BasePart?
	if not Torso or Back.Magnitude == 0 then return 0 end
	local Ex = { Model }
	if Prop then table.insert(Ex, Prop) end
	for _, N in { `Live`, `NHSchedule`, `NHAmbient`, `NHFx` } do local F = workspace:FindFirstChild(N) if F then table.insert(Ex, F) end end
	local Restore = {}
	for _, Q in nearbyParts(Torso.Position, 8, Ex) do
		if not Q.CanQuery and Q.Transparency < 0.9 then Q.CanQuery = true table.insert(Restore, Q) end
	end
	local Params = OverlapParams.new()
	Params.FilterType = Enum.RaycastFilterType.Exclude
	Params.FilterDescendantsInstances = Ex
	local Moved = 0
	local Base = Model:GetPivot()
	local Worst = clipping(Model, Params)
	if Worst > 0 then
		-- forward a little at a time; keep the first clear place, else the one with the fewest parts still touching
		local Best, BestAt = Worst, 0
		local At = 0
		while At < (MaxForward or 1.2) - 1e-6 do
			At += 0.1
			Model:PivotTo(Base - Back * At)
			local N = clipping(Model, Params)
			if N < Best then Best, BestAt = N, At end
			if N == 0 then break end
		end
		Moved = BestAt
		Model:PivotTo(Base - Back * BestAt)
	end
	for _, Q in Restore do Q.CanQuery = false end
	return Moved
end

-- once the sitting pose is playing: hips a little behind the seat's centre (toward the backrest), resting on Top.
-- (1.46.1) The thighs rest on it too: R6 sitting poses swing the legs forward from the hip, so the thigh hangs half
-- its thickness below the torso and used to sink into the cushion; whichever is lower (hips or thighs) goes on Top.
-- Then, with Prop given, the sitter is slid forward out of anything behind them (Seats.Unclip).
function Seats.Settle(Model: Model, Top: Vector3, Back: Vector3, Inset: number?, Prop: Instance?)
	local Torso = Model:FindFirstChild(`Torso`) :: BasePart?
	if not Torso then return end
	local Want = Top + Back * (Inset or 0.35)
	Model:PivotTo(Model:GetPivot() + Vector3.new(Want.X - Torso.Position.X, 0, Want.Z - Torso.Position.Z))
	local Low = lowestTorso(Torso).Y
	for _, N in { `Left Leg`, `Right Leg` } do
		local L = Model:FindFirstChild(N)
		if L and L:IsA(`BasePart`) then Low = math.min(Low, thighLow(L)) end
	end
	Model:PivotTo(Model:GetPivot() + Vector3.new(0, Top.Y - Low, 0))
	if Prop then pcall(Seats.Unclip, Model, Back, Prop) end
end

-- wait until the sitting pose is fully on (PoseId's track at full weight; any loaded track if no id is given), then
-- settle; again a moment later, in case it was still blending in
function Seats.SettleWhenPosed(Model: Model, Hum: Humanoid, Top: Vector3, Back: Vector3, StillWanted: () -> boolean, Inset: number?, PoseId: number?, Prop: Instance?)
	task.spawn(function()
		local Animator = Hum:FindFirstChildOfClass(`Animator`)
		local t0 = os.clock()
		repeat
			task.wait(0.2)
			local ok = false
			for _, T in (Animator and Animator:GetPlayingAnimationTracks()) or {} do
				if PoseId then
					if T.Animation and T.Animation.AnimationId:find(tostring(PoseId), 1, true) and T.WeightCurrent > 0.9 then ok = true end
				elseif T.Length > 0 then
					ok = true
				end
			end
		until ok or os.clock() - t0 > 15 or not Model.Parent or not StillWanted()
		for _, Delay in { 0.15, 1.5, 4 } do
			task.wait(Delay)
			if not (Model.Parent and StillWanted()) then return end
			pcall(Seats.Settle, Model, Top, Back, Inset, Prop)
		end
	end)
end

return Seats
