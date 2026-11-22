-- lc_pure (phase6-strafes R2): Functions.Locomotion + Config.Locomotion, inlined from the repo by harness/pure.py.
-- Pure: writes no instances. usage: python -X utf8 -I harness/pure.py checks/lc_pure.lua
local function load(name)
	local Src = __SRC and __SRC[name]
	if not Src then error("FAIL source not inlined: " .. name) end
	local Fn, Err = loadstring(Src)
	if not Fn then error("FAIL parse " .. name .. ": " .. tostring(Err)) end
	return Fn()
end
local Cfg = load("ReplicatedStorage.Config.Locomotion.luau")
local L = load("ReplicatedStorage.Functions.Locomotion.luau")
local Fails = {}
local function Near(G, W, What, Tol) if math.abs(G - W) > (Tol or 1e-3) then table.insert(Fails, What .. ": got " .. G .. " want " .. W) end end
local function Eq(G, W, What) if G ~= W then table.insert(Fails, What .. ": got " .. tostring(G) .. " want " .. tostring(W)) end end
-- weights: forward, left, right, back, diagonals
local W = L.Weights(0) Near(W.Walk, 1, "fwd walk") Near(W.Left + W.Right + W.Back, 0, "fwd rest")
W = L.Weights(-math.pi / 2) Near(W.Left, 1, "left") W = L.Weights(math.pi / 2) Near(W.Right, 1, "right")
W = L.Weights(math.pi) Near(W.Back, 1, "back")
W = L.Weights(math.pi / 4) Near(W.Walk, 0.5, "fwd-right walk") Near(W.Right, 0.5, "fwd-right right")
W = L.Weights(-3 * math.pi / 4) Near(W.Back, 0.5, "back-left back") Near(W.Left, 0.5, "back-left left")
for _, A in { 0.3, 1.2, 2.9, -0.7, -2.2 } do local V = L.Weights(A) Near(V.Walk + V.Back + V.Left + V.Right, 1, "sum " .. A) end
-- strafe mode
Eq(L.StrafeMode({ Gait = "Walk", Locked = true }), true, "locked walk")
Eq(L.StrafeMode({ Gait = "Walk", MouseLocked = true }), true, "shift lock walk")
Eq(L.StrafeMode({ Gait = "Walk", FirstPerson = true }), true, "first person walk")
Eq(L.StrafeMode({ Gait = "Walk" }), false, "free camera walk")
Eq(L.StrafeMode({ Gait = "Sprint", Locked = true }), false, "sprint")
Eq(L.StrafeMode({ Gait = "CrouchWalk", Locked = true }), false, "crouch")
Eq(L.StrafeMode({ Gait = "Walk", Locked = true, Blocked = true }), false, "blocked")
-- blockers
Eq(L.Blocked({ NHApproach = true }, Cfg), true, "approach blocks")
Eq(L.Blocked({ NHCineSeam = "In" }, Cfg), true, "seam blocks")
Eq(L.Blocked({ NHInCine = true }, Cfg), true, "incine blocks")
Eq(L.Blocked({ NHCineHold = true }, Cfg), true, "hold blocks")
Eq(L.Blocked({ NHApproach = false }, Cfg), false, "false does not block")
Eq(L.Blocked({}, Cfg), false, "nothing blocks")
-- rate: stride-matched, clamped
Near(L.Rate(14.4, Cfg.Stride.Walk, 1.615, Cfg), math.min(Cfg.CadenceMax, 14.4 / (5.9 * 0.8075)), "walk rate", 1e-2)
Near(L.Rate(8.5, Cfg.Stride.Strafe, 1.615, Cfg), 8.5 / (5.8 * 0.8075), "strafe rate", 1e-2)
Near(L.Rate(0.1, Cfg.Stride.Walk, 2, Cfg), Cfg.CadenceMin, "rate floor")
Near(L.Rate(40, Cfg.Stride.Walk, 2, Cfg), Cfg.CadenceMax, "rate cap")
-- phase sync: contact phases line up
Near(L.Phase(0.585, 1.17, 1.03, 0, 0), 0.515, "phase half")
Near(L.Phase(0, 1.17, 1.03, 0.1, 0.3), (0.3 - 0.1) * 1.03, "phase offset")
-- config sanity
Eq(Cfg.StrafeSpeed, 8.5, "strafe speed") Eq(Cfg.WalkBandMax, 20, "walk band") Eq(Cfg.CadenceMax, 2.4, "cadence cap")
Eq(typeof(Cfg.Ids.StrafeLeft), "number", "strafe ids")
return #Fails == 0 and "PASS lc_pure" or ("FAIL\n" .. table.concat(Fails, "\n"))
