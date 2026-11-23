--!strict
--[[ (phase6-strafes) Pure locomotion maths: no services, no instances. Callers pass Config.Locomotion.
	Weights(A)        the directional blend for the move angle A (radians, 0 = forward, +pi/2 = right)
	StrafeMode(F)     whether the directional blend runs (walk gait, a facing mode, nothing blocking)
	Blocked(Flags)    any Config.Blockers name truthy in Flags
	Rate(...)         stride-matched cadence, clamped to [CadenceMin, CadenceMax]
	Phase(...)        a secondary track's TimePosition so both clips' left-foot contacts line up
	Spec: docs/superpowers/specs/2026-11-22-strafes-npc-gestures-design.md §1. ]]
local L = {}

function L.Weights(A: number): { Walk: number, Back: number, Left: number, Right: number }
	local C, S = math.cos(A), math.sin(A)
	local W = { Walk = math.max(0, C), Back = math.max(0, -C), Left = math.max(0, -S), Right = math.max(0, S) }
	local Sum = W.Walk + W.Back + W.Left + W.Right
	if Sum < 1e-6 then return { Walk = 1, Back = 0, Left = 0, Right = 0 } end
	W.Walk /= Sum
	W.Back /= Sum
	W.Left /= Sum
	W.Right /= Sum
	return W
end

function L.StrafeMode(F: { [string]: any }): boolean
	if F.Gait ~= "Walk" or F.Blocked then return false end
	return F.Locked == true or F.MouseLocked == true or F.FirstPerson == true
end

function L.Blocked(Flags: { [string]: any }, Cfg: any): boolean
	for _, N in Cfg.Blockers do
		local V = Flags[N]
		if V ~= nil and V ~= false then return true end
	end
	return false
end

function L.Rate(Ground: number, Stride: number, LegLen: number, Cfg: any): number
	local Per = Stride * math.max(LegLen, 0.1) / 2
	return math.clamp(Ground / Per, Cfg.CadenceMin, Cfg.CadenceMax)
end

function L.Phase(DomTime: number, DomLen: number, SecLen: number, DomContact: number, SecContact: number): number
	local P = (DomTime / DomLen - DomContact + SecContact) % 1
	return P * SecLen
end

return L
