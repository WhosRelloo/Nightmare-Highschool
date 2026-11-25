-- carry_grip (playtest-blockers, Server, Play, run_live.py): the carried body lies on the carrier's shoulder, and a
-- gripped body stays held at the grip offset even when it tries to move away.
-- A scale-1 test NPC is downed by the bridge (no attacker, so no discipline), carried, then gripped to the end.
local B = game.ServerStorage.NHTestBridge
local D = require(game.ServerScriptService.Services.Features.Downed)
local Cfg = require(game.ReplicatedStorage.Config.Downed)
local P = game.Players:GetPlayers()[1]
local C = P.Character
local R = C.HumanoidRootPart
local Home = R.CFrame
local Bad = {}
for _, M in workspace.Live:GetChildren() do if M.Name:match(`^NPC_`) then M:Destroy() end end
local function npc()
	local _, Names = B:Invoke(`SpawnAI`, 1, R.Position + Vector3.new(-6, 0, 0))
	local N = workspace.Live:FindFirstChild(Names and Names[1] or ``)
	if not N then return nil end
	pcall(function() N:ScaleTo(1) end)
	task.wait(0.3)
	B:Invoke(`Damage`, N.Name, 1e6, nil)
	task.wait(0.4)
	local T = N.HumanoidRootPart
	C:PivotTo(CFrame.lookAt(T.Position + Vector3.new(0, 0, 3), T.Position))
	task.wait(0.3)
	return N
end
-- carry
local N = npc()
if not N then return `FAIL no test NPC` end
local _, Carried = B:Invoke(`ToggleCarry`, P.Name)
task.wait(1.2)
local T = C.Torso
local Torso = T.CFrame:PointToObjectSpace(N.Torso.Position)
local Head = T.CFrame:PointToObjectSpace(N.Head.Position)
local LegY = (T.CFrame:PointToObjectSpace(N[`Left Leg`].Position).Y + T.CFrame:PointToObjectSpace(N[`Right Leg`].Position).Y) / 2
if not Carried then table.insert(Bad, `carry refused`) end
-- on the right shoulder: torso 1-2.2 up (the carrier's shoulders are at +1), right of centre, not above the head
if not (Torso.Y > 1 and Torso.Y < 2.2) then table.insert(Bad, string.format(`carried torso %.2f up (want 1-2.2)`, Torso.Y)) end
if not (Torso.X > 0.4 and Torso.X < 2) then table.insert(Bad, string.format(`carried torso %.2f right (want 0.4-2)`, Torso.X)) end
if LegY > 1 then table.insert(Bad, string.format(`legs %.2f up (want hanging below the shoulder)`, LegY)) end
local CarryLine = string.format(`torso (%.2f, %.2f, %.2f) head (%.2f, %.2f, %.2f) legs y %.2f`, Torso.X, Torso.Y, Torso.Z, Head.X, Head.Y, Head.Z, LegY)
-- grip from the carry (B while carrying puts it down and grips it): the victim is held while it tries to walk off
local _, Gripped = B:Invoke(`Grip`, P.Name)
if not Gripped then table.insert(Bad, `grip refused`) end
local Off = Cfg.GripVictimOffset
N.Humanoid:MoveTo(N.HumanoidRootPart.Position + R.CFrame.LookVector * 12)
local Worst = 0
local Weld = R:FindFirstChild(`GripWeld`) ~= nil
local T0 = os.clock()
while D.IsDowned(N) and N.Parent and N.Humanoid.Health > 0 and os.clock() - T0 < 6 do
	local Rel = R.CFrame:ToObjectSpace(N.HumanoidRootPart.CFrame)
	Worst = math.max(Worst, (Rel.Position - Off.Position).Magnitude)
	task.wait(0.1)
end
task.wait(0.3)
local Dead = not N.Parent or N.Humanoid.Health <= 0
if not Weld then table.insert(Bad, `no GripWeld`) end
if Worst > 0.3 then table.insert(Bad, string.format(`victim drifted %.2f studs from the grip offset`, Worst)) end
if not Dead then table.insert(Bad, `the grip didn't finish the victim`) end
if N.Parent then N:Destroy() end
C:PivotTo(Home)
if #Bad > 0 then return `FAIL ` .. table.concat(Bad, `; `) .. ` | carry ` .. CarryLine end
return string.format(`PASS carry on the shoulder: %s; grip held (worst drift %.2f studs), weld %s, victim finished`, CarryLine, Worst, tostring(Weld))
