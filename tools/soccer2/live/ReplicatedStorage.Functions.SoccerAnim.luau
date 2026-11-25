--!strict
--[[ (soccer-2.0) Pure soccer-clip maths: no services, no instances. A Clip is a Config.SoccerClips.Clips entry:
	{ Length: number, ContactAt: number?, Loop: boolean?, Path: { {number} }? }   (Path rows { t, x, z }, HRP space, studs)
	StartAt(Clip, Lead)                where a kick starts so the foot meets the ball Lead s later (0 with no contact)
	Hold(Clip, Lead, Margin, MaxHold)  HoldAt, Creep: a charge plays 1x to HoldAt, then Creep reaches StartAt at MaxHold
	Window(Clip)                       t0, t1: where the path's distance passes 10 % and 90 % of its peak
	Fit(Clip, DashTime, Cap)           Rate, Time, t0, t1: the clip's rate through its window (1..Cap) and the dash time
	Progress(Clip, t, t0, t1)          0..1 along the window's displacement by clip time t (clamped, never decreasing)
	KickSlot(Speed, RunSpeed)          "KickRun" at or above RunSpeed, else "Kick"
	DiveSlot(RightDot)                 "KeeperDiveRight" when the dive goes right (RightDot >= 0), else "KeeperDiveLeft"
	KickMargin                         0.20: the Kick charge's Hold margin (every other clip keeps 0.10), a creep of about 0.1x
	Spec: docs/superpowers/specs/2026-11-24-soccer-2-0-design.md §3-4. ]]
local A = {}

-- (soccer-2.0 final, the owner's ruling) the Kick (and KickRun) charge creeps from 0.20 before contact, so it moves
A.KickMargin = 0.20

export type Clip = { Length: number, ContactAt: number?, Loop: boolean?, Path: { { number } }? }

local function at(P: { { number } }, t: number): (number, number)
	if t <= P[1][1] then return P[1][2], P[1][3] end
	for I = 2, #P do
		local B = P[I]
		if t <= B[1] then
			local Q = P[I - 1]
			local u = (t - Q[1]) / math.max(B[1] - Q[1], 1e-6)
			return Q[2] + (B[2] - Q[2]) * u, Q[3] + (B[3] - Q[3]) * u
		end
	end
	local L = P[#P]
	return L[2], L[3]
end

local function linear(t: number, t0: number, t1: number): number
	return math.clamp((t - t0) / math.max(t1 - t0, 1e-3), 0, 1)
end

function A.StartAt(Clip: Clip, Lead: number): number
	local C = Clip.ContactAt
	if not C then return 0 end
	return math.max(0, C - Lead)
end

function A.Hold(Clip: Clip, Lead: number, Margin: number, MaxHold: number): (number, number)
	local Start = A.StartAt(Clip, Lead)
	local HoldAt = math.min(math.max(0, (Clip.ContactAt or 0) - Margin), Start)
	return HoldAt, (Start - HoldAt) / math.max(MaxHold, 1e-3)
end

function A.Window(Clip: Clip): (number, number)
	local P = Clip.Path
	if not P or #P < 2 then return 0, Clip.Length end
	local Peak = 0
	for _, S in P do Peak = math.max(Peak, math.sqrt(S[2] * S[2] + S[3] * S[3])) end
	if Peak < 1e-3 then return 0, Clip.Length end
	local t0: number?, t1: number? = nil, nil
	for _, S in P do
		local M = math.sqrt(S[2] * S[2] + S[3] * S[3])
		if t0 == nil and M >= 0.1 * Peak then t0 = S[1] end
		if t1 == nil and M >= 0.9 * Peak then t1 = S[1] end
	end
	return t0 or 0, t1 or Clip.Length
end

function A.Fit(Clip: Clip, DashTime: number, Cap: number): (number, number, number, number)
	local t0, t1 = A.Window(Clip)
	local W = math.max(t1 - t0, 1e-3)
	local Rate = math.clamp(W / math.max(DashTime, 1e-3), 1, Cap)
	return Rate, W / Rate, t0, t1
end

function A.Progress(Clip: Clip, t: number, t0: number, t1: number): number
	local P = Clip.Path
	if not P or #P < 2 then return linear(t, t0, t1) end
	local x0, z0 = at(P, t0)
	local x1, z1 = at(P, t1)
	local Dx, Dz = x1 - x0, z1 - z0
	local Len2 = Dx * Dx + Dz * Dz
	if Len2 < 1e-6 then return linear(t, t0, t1) end
	-- the furthest the path has got along the window's direction by t (30 fps steps), so it never goes back
	local Stop = math.clamp(t, t0, t1)
	local Best, T = 0, t0
	while true do
		local x, z = at(P, T)
		Best = math.max(Best, ((x - x0) * Dx + (z - z0) * Dz) / Len2)
		if T >= Stop then break end
		T = math.min(T + 1 / 30, Stop)
	end
	return math.clamp(Best, 0, 1)
end

function A.KickSlot(Speed: number, RunSpeed: number): string
	return if Speed >= RunSpeed then "KickRun" else "Kick"
end

function A.DiveSlot(RightDot: number): string
	return if RightDot >= 0 then "KeeperDiveRight" else "KeeperDiveLeft"
end

return A
