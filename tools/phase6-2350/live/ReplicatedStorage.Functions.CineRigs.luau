--!strict
--[[
	CineRigs (shared, pure). ReplicatedStorage.Functions.CineRigs   (2.35.0, spec 2026-11-20 §3)
	Walk-and-talk camera goals around a player who keeps moving: Follow (low shoulder, drifts to keep a second subject in
	frame), Lead (ahead at hip height, looking back), Side (a dolly beside you), Frame (eases toward a point of interest).
	The runner damps toward these goals and adds the player's nudge.
]]
local Rigs = {}
local function fov(mm: number): number return math.deg(2 * math.atan(10.125 / mm)) end

function Rigs.Target(Rig: string, Player: CFrame, Also: Vector3?, Travel: Vector3, Opts): (CFrame, number)
	local Flat = Vector3.new(Travel.X, 0, Travel.Z)
	local Fwd = if Flat.Magnitude > 1e-3 then Flat.Unit else Player.LookVector
	local Right = Fwd:Cross(Vector3.yAxis).Unit
	local Head = Player.Position + Vector3.new(0, 1.5, 0)
	local Low = Opts.low == true
	local Lens = Opts.lens or 35
	local Pos, Look
	if Rig == `Lead` then
		Pos = Player.Position + Fwd * (Opts.dist or 9) + Vector3.new(0, Opts.height or 0.6, 0)
		Look = Head - Vector3.new(0, 0.4, 0)
	elseif Rig == `Side` then
		Pos = Player.Position + Right * (Opts.dist or 9) + Fwd * 1.5 + Vector3.new(0, Opts.height or 1.6, 0)
		Look = Head + Fwd * 1.5
	elseif Rig == `Frame` and Also then
		Pos = Player.Position - Fwd * (Opts.dist or 8) + Right * 2.2 + Vector3.new(0, Opts.height or 2.4, 0)
		Look = Head:Lerp(Also, 0.55)
	else -- Follow
		Pos = Player.Position - Fwd * (Opts.dist or 8) + Right * 2.0 + Vector3.new(0, Opts.height or (if Low then 1.2 else 2.6), 0)
		Look = if Also then Head:Lerp(Also, 0.3) else Head + Fwd * 4
	end
	return CFrame.lookAt(Pos, Look), fov(Lens)
end

function Rigs.Nudge(State, InputDelta: Vector2, Dt: number): Vector2
	-- mouse/stick pushes up to 25 degrees; it springs back with a 0.15 s half-life (about 0.6 s to settle)
	State.yaw = math.clamp(State.yaw - InputDelta.X * 0.25, -25, 25)
	State.pitch = math.clamp(State.pitch - InputDelta.Y * 0.25, -25, 25)
	if InputDelta.Magnitude < 1e-3 then
		local K = 0.5 ^ (Dt / 0.15)
		State.yaw *= K
		State.pitch *= K
	end
	return Vector2.new(State.yaw, State.pitch)
end

function Rigs.Damp(Current: CFrame, Goal: CFrame, Dt: number, Halflife: number): CFrame
	return Current:Lerp(Goal, 1 - 0.5 ^ (Dt / math.max(Halflife, 1e-3)))
end

return Rigs
