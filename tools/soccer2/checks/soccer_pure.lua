-- soccer_pure (soccer-2.0 Task 1): Functions.SoccerAnim, inlined by harness/pure.py. Pure: writes no instances.
-- usage: python -X utf8 -I tools/soccer2/harness/pure.py tools/soccer2/checks/soccer_pure.lua
local function load(name)
	local Src = __SRC and __SRC[name]
	if not Src then error("FAIL source not inlined: " .. name) end
	local Fn, Err = loadstring(Src)
	if not Fn then error("FAIL parse " .. name .. ": " .. tostring(Err)) end
	return Fn()
end
local A = load("ReplicatedStorage.Functions.SoccerAnim.luau")
local Fails = {}
local function Near(G, W, What, Tol) if math.abs(G - W) > (Tol or 1e-3) then table.insert(Fails, What .. ": got " .. G .. " want " .. W) end end
local function Eq(G, W, What) if G ~= W then table.insert(Fails, What .. ": got " .. tostring(G) .. " want " .. tostring(W)) end end
-- kicks
Near(A.StartAt({ Length = 0.57, ContactAt = 0.23 }, 0.05), 0.18, "start kick")
Near(A.StartAt({ Length = 1 }, 0.05), 0, "start with no contact")
Near(A.StartAt({ Length = 1, ContactAt = 0.02 }, 0.05), 0, "start clamps at 0")
local H, C = A.Hold({ Length = 0.57, ContactAt = 0.23 }, 0.05, 0.10, 1.6)
Near(H, 0.13, "hold at") Near(C, 0.05 / 1.6, "creep rate")
Near(H + C * 1.6, 0.18, "the creep reaches the kick point at MaxHold")
local H2, C2 = A.Hold({ Length = 1, ContactAt = 0.04 }, 0.05, 0.10, 1.6)
Near(H2, 0, "hold clamps at 0") Near(C2, 0, "no creep room, no creep")
-- a straight dash path: still for 1 s, 10 studs left over 1..2 s, still to 3 s
local P = {}
for I = 0, 90 do local t = I / 30 local x = if t <= 1 then 0 elseif t >= 2 then -10 else -10 * (t - 1) table.insert(P, { t, x, 0 }) end
local Dash = { Length = 3, Path = P }
local t0, t1 = A.Window(Dash)
Near(t0, 1.1, "window t0", 0.04) Near(t1, 1.9, "window t1", 0.04)
local R, T = A.Fit(Dash, 0.5, 2) Near(R, 1.6, "fit rate", 0.1) Near(T, 0.5, "fit time", 0.02)
R, T = A.Fit(Dash, 0.2, 2) Near(R, 2, "rate capped at 2") Near(T, 0.4, "capped dash time", 0.03)
R = A.Fit(Dash, 5, 2) Near(R, 1, "never slower than 1x")
Near(A.Progress(Dash, t0, t0, t1), 0, "progress 0 at t0")
Near(A.Progress(Dash, t1, t0, t1), 1, "progress 1 at t1")
Near(A.Progress(Dash, (t0 + t1) / 2, t0, t1), 0.5, "progress halfway", 0.05)
Near(A.Progress(Dash, 0, t0, t1), 0, "progress before the window")
Near(A.Progress(Dash, 3, t0, t1), 1, "progress after the window")
-- a dive that overshoots and comes back: progress never goes down
local Q = {}
for I = 0, 60 do local t = I / 30 local x = if t <= 1 then -8 * t else -8 + 2 * (t - 1) table.insert(Q, { t, x, 0 }) end
local Back = { Length = 2, Path = Q }
local q0, q1 = A.Window(Back)
local Last = -1
for I = 0, 20 do
	local p = A.Progress(Back, q0 + (q1 - q0) * I / 20, q0, q1)
	if p < Last - 1e-6 then table.insert(Fails, "progress went down at step " .. I) end
	Last = p
end
Near(A.Progress({ Length = 1 }, 0.5, 0, 1), 0.5, "no path: linear")
-- slots
Eq(A.KickSlot(7, 6), "KickRun", "running shot") Eq(A.KickSlot(6, 6), "KickRun", "running shot at the edge") Eq(A.KickSlot(2, 6), "Kick", "standing shot")
Eq(A.DiveSlot(0.7), "KeeperDiveRight", "dive right") Eq(A.DiveSlot(0), "KeeperDiveRight", "dive edge") Eq(A.DiveSlot(-0.3), "KeeperDiveLeft", "dive left")
if #Fails > 0 then return "FAIL soccer_pure\n" .. table.concat(Fails, "\n") end
return "PASS soccer_pure"
