local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local Director = require(Players.LocalPlayer.PlayerScripts.Controllers.Cine)
local Judge = require(RS.Functions.CineJudge)
local Lib = require(RS.Cine)
local Def = require(RS.Cinematics["__CUT__"])
local Graph = Def.Graph
local Paths = {}
local function walk(N, Path)
	table.insert(Path, N)
	local S = Judge.Successors(Graph, N)
	if #S == 0 then table.insert(Paths, table.clone(Path)) else for _, Next in S do walk(Next, Path) end end
	table.remove(Path)
end
if not Graph then return "no graph" end
local Errs = Judge.Validate(Graph)
if #Errs > 0 then return "INVALID: " .. table.concat(Errs, " | ") end
walk(Graph.start, {})
local Out, Fixes = {}, 0
for _, Path in Paths do
	local Cut, Built, L = Director.BuildForTests("__CUT__")
	local Flat = Director.FlattenForTests(Built, Graph, Path)
	local events = Flat.events
	table.sort(events, function(a, b) return (a.t or 0) < (b.t or 0) end)
	local line = (Cut.Actors.Hale and Cut.Actors.Self) and { Cut.Actors.Hale.Model, Cut.Actors.Self.Model } or (Cut.Actors.You and Cut.Actors.It) and { Cut.Actors.You.Model, Cut.Actors.It.Model } or nil
	local At, Fired = 0, 1
	for _, shot in Flat.shots do
		local Mid = At + shot.dur / 2
		while Fired <= #events and (events[Fired].t or 0) <= Mid do
			local E = events[Fired]
			Fired += 1
			if E.walk then
				local A, To = Cut.Actors[E.walk.who], Cut.Ctx.Mark(E.walk.to)
				if A and To then if E.walk.pose then L.SetPose(A, E.walk.pose, 100) end A.Walk = { From = A.Base; To = To.CFrame; T0 = E.t; Dur = E.walk.dur or 2 } end
			elseif E.pose or E.look or E.place then pcall(L.Fire, Cut, E) end
		end
		for _, A in Cut.Actors do for K, V in A.Target do A.Cur[K] = V end pcall(L.StepActor, A, 1 / 60, Mid, workspace.CurrentCamera) end
		local ok, report = pcall(Lib.analyze, { name = shot.name; letterbox = 2.28; line = line; shots = { shot } })
		for l in tostring(report):gmatch("[^\n]+") do
			if l:find("^%[fix%]") then Fixes += 1 table.insert(Out, table.concat(Path, ">") .. " " .. l) end
		end
		At += shot.dur
	end
	if Cut.Folder then Cut.Folder:Destroy() end
end
return string.format("%d paths, %d fixes, longest %.1f s\n", #Paths, Fixes, Judge.LongestPath(Graph)) .. table.concat(Out, "\n")
