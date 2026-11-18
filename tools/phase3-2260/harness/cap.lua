-- (2.26.0) Hold the Strikethrough at one moment of one path for screen_capture. PATH and T (seconds from the cut's
-- start along that path) are filled in; STOP = true releases the hold. The held camera survives the call (a
-- RenderStep binding keeps it), so screen_capture between calls sees the shot.
local PATH, T, STOP = "__PATH__", __T__, __STOP__
local RS = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Players = game:GetService("Players")
local function release()
	pcall(function() RunService:UnbindFromRenderStep("NHCap") end)
	if shared.NHCap then
		pcall(function() shared.NHCap.H:stop() end)
		pcall(function() if shared.NHCap.Cut.Folder then shared.NHCap.Cut.Folder:Destroy() end end)
		shared.NHCap = nil
	end
	workspace.CurrentCamera.CameraType = Enum.CameraType.Custom
end
release()
if STOP then return "released" end
local Director = require(Players.LocalPlayer.PlayerScripts.Controllers.Cine)
local Lib = require(RS.Cine)
local Def = require(RS.Cinematics.Strikethrough)
local Path = {}
for S in PATH:gmatch("[^>]+") do table.insert(Path, S) end
local Cut, Built, L = Director.BuildForTests("Strikethrough")
local Flat = Director.FlattenForTests(Built, Def.Graph, Path)
table.sort(Flat.events, function(a, b) return (a.t or 0) < (b.t or 0) end)
local function stepTo(t)
	for _, A in Cut.Actors do for K, V in A.Target do A.Cur[K] = V end pcall(L.StepActor, A, 1 / 60, t, workspace.CurrentCamera) end
end
for _, E in Flat.events do
	if (E.t or 0) > T then break end
	stepTo(E.t or 0) -- finish earlier walks first (the director steps every frame)
	if E.walk then
		local A, To = Cut.Actors[E.walk.who], Cut.Ctx.Mark(E.walk.to)
		if A and To then A.Walk = { From = A.Base; To = To.CFrame; T0 = E.t; Dur = E.walk.dur or 2 } end
	elseif E.pose or E.look or E.place or E.move or E.fx then pcall(L.Fire, Cut, E) end
end
for _, A in Cut.Actors do for K, V in A.Target do A.Cur[K] = V end pcall(L.StepActor, A, 1 / 60, T, workspace.CurrentCamera) end
local H = Lib.play({ name = "cap"; letterbox = 2.28; grade = Built.grade; shots = Flat.shots }, { start = T; overlay = false; autoStop = false })
task.wait(0.25)
pcall(function() H:setTimeScale(0) end)
local Cam = workspace.CurrentCamera
local CF, FOV = Cam.CFrame, Cam.FieldOfView
RunService:BindToRenderStep("NHCap", Enum.RenderPriority.Last.Value + 1, function()
	Cam.CameraType = Enum.CameraType.Scriptable
	Cam.CFrame, Cam.FieldOfView = CF, FOV
end)
shared.NHCap = { H = H; Cut = Cut }
local At, Name = 0, "?"
for _, S in Flat.shots do if T >= At and T < At + S.dur then Name = S.name end At += S.dur end
return string.format("holding %s at %.2f (shot %s)", PATH, T, Name)
