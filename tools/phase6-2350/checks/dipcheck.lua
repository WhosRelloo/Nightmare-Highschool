-- dipcheck (2.35.0, task 12): CineUI.Dip's veil token. A dip must lift its veil only if nothing claimed it since: a second dip
-- (a Skip inside the fence dip or the hold's timeout dip) or a Veil call (a Prologue Play's Veil(1, 0)) arriving inside the
-- first dip's first half owns the screen; the first dip's lift must not run (the screen would clear before the second black).
-- Client VM, ONE call. Reads the veil of the module copy's own NHCineUI gui.
-- Case A: dip(0.6) at 0, dip(1.6) at 0.1 (black at 0.3 and 0.9): between 0.33 and 0.85 the veil must stay black.
-- Case B: dip(0.6) at 0, Veil(1, 0) at 0.1 (the Play's own black), no lift at all until we clear it: stays black to 0.8.
-- Case C: one dip alone still lifts (clear again by 0.8).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local PG = Players.LocalPlayer:WaitForChild("PlayerGui")
local UI = require(Players.LocalPlayer.PlayerScripts.Controllers.Gui.CineUI)
-- the module copy's own gui (the client VM keeps the require cache across calls, so it may exist already): black it with a
-- Veil call and find the NHCineUI whose veil went black
UI.Veil(0, 0)
for _, G in PG:GetChildren() do if G.Name == "NHCineUI" and G:FindFirstChild("Veil") then G.Veil.BackgroundTransparency = 0.5 end end
UI.Veil(1, 0)
local Veil
for _, G in PG:GetChildren() do if G.Name == "NHCineUI" and G:FindFirstChild("Veil") and G.Veil.BackgroundTransparency == 0 then Veil = G.Veil end end
assert(Veil, "the module copy's veil was not found")
UI.Veil(0, 0)
local Rep, Pass = {}, true
local function check(Ok, Text) table.insert(Rep, (Ok and "ok   " or "FAIL ") .. Text) if not Ok then Pass = false end end
local function sample(Seconds)
	local Rows, T0 = {}, os.clock()
	while os.clock() - T0 < Seconds do
		table.insert(Rows, { t = os.clock() - T0, v = Veil.BackgroundTransparency })
		RunService.Heartbeat:Wait()
	end
	return Rows
end
local function maxIn(Rows, A, B)
	local M, N = 0, 0
	for _, R in Rows do if R.t >= A and R.t <= B then M = math.max(M, R.v) N += 1 end end
	return M, N
end
-- A
task.spawn(UI.Dip, 0.6)
task.delay(0.1, UI.Dip, 1.6)
local A = sample(2.2)
local M, N = maxIn(A, 0.33, 0.85)
local Rise = 0
for I = 2, #A do if A[I].t >= 0.33 and A[I].t <= 0.88 then Rise = math.max(Rise, A[I].v - A[I - 1].v) end end
check(Rise <= 0.02, string.format("two dips: no sample rises from the one before between 0.33 and 0.88 s (largest rise %.3f)", Rise))
check(N > 0 and M <= 0.02, string.format("two dips: veil max transparency %.3f over %d samples in 0.33-0.85 s (want <= 0.02: black until the second dip's black)", M, N))
local Tr = {} for _, R in A do if R.t < 1.3 then table.insert(Tr, string.format("%.2f:%.2f", R.t, R.v)) end end
table.insert(Rep, "trace A " .. table.concat(Tr, " "))
local M2, N2 = maxIn(A, 2.0, 2.2)
check(M2 >= 0.99, string.format("two dips: the screen is clear again by 2.0 s (%.2f)", M2))
-- B
UI.Veil(0, 0)
task.wait(0.2)
task.spawn(UI.Dip, 0.6)
task.delay(0.1, UI.Veil, 1, 0)
local B = sample(0.9)
local M3, N3 = maxIn(B, 0.35, 0.8)
check(N3 > 0 and M3 <= 0.02, string.format("a Veil(1, 0) inside a dip: stays black 0.35-0.8 s (max transparency %.3f over %d)", M3, N3))
-- C
UI.Veil(0, 0)
task.wait(0.2)
task.spawn(UI.Dip, 0.6)
local C = sample(1.0)
local M4 = maxIn(C, 0.8, 1.0)
check(M4 >= 0.99, string.format("a single dip lifts (transparency %.2f at 0.8-1.0 s)", M4))
UI.Veil(0, 0)
return (Pass and "DIP OK\n" or "DIP FAIL\n") .. table.concat(Rep, "\n")
