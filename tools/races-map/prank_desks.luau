-- (1.66) prank desks: a prank that lands also tags one classroom desk with the pranksters' desk (ServerStorage.NHProps)
local S = game.ServerScriptService.Services.Social.CliquePranks
local src = S.Source
assert(not src:find("Local.TagDesk", 1, true), "already patched")
local function rep(old, new)
	local a, b = src:find(old, 1, true)
	assert(a, "missing: " .. old:sub(1, 60))
	assert(not src:find(old, b + 1, true), "twice: " .. old:sub(1, 60))
	src = src:sub(1, a - 1) .. new .. src:sub(b + 1)
end

rep([[	API: UseKit(Player), NpcPrank(By, Victim), PlayerPrank(Player, Victim, SkipKit?), CleanAll(), State().]],
[[	Prank desks   (1.66) A prank that lands also swaps one classroom desk (workspace.School.NHProps StudentDesk) for the
	              pranksters' desk, ServerStorage.NHProps.StudentDeskPrank<Clique>; your own prank uses your clique (the one
	              you stand 60+ with) or a carved / graffiti desk. The real desk only turns see-through (it keeps its collision
	              and anything built on it), and the tag is a non-colliding copy on top. Hold E to scrub it; the janitor
	              clears them all at 6 AM with the messes. At most DESK_MAX at once. No templates imported: no desk tags.
	API: UseKit(Player), NpcPrank(By, Victim), PlayerPrank(Player, Victim, SkipKit?), CleanAll(), State(), TagDesk(By?, Player?).]])

rep([[local KINDS = { `Tag`, `Stink`, `Trash` }]], [[local KINDS = { `Tag`, `Stink`, `Trash` }
local DESK_MAX = 6 -- (1.66) prank desks at once
local OWN_DESKS = { `StudentDeskCarved`, `StudentDeskGraffiti` }]])

rep([[-- victims' students near a mess complain about it]], [[---| prank desks (1.66) |---

function Local.DeskTemplate(By: string?, P: Player?): Model?
	local Lib = game:GetService(`ServerStorage`):FindFirstChild(`NHProps`)
	if not Lib then return nil end
	local Id = By
	if not Id and P then
		-- your own prank: the clique you stand highest with, from Hanger-on (60) up
		local Cl = Cliques()
		local Ok, Vals = pcall(function() return Cl and Cl.Get(P) end)
		local Best, BV = nil, 59
		for K, V in (Ok and Vals) or {} do
			if type(V) == `number` and V > BV and Config.Defs[K] then Best, BV = K, V end
		end
		Id = Best
	end
	local T = Id and Lib:FindFirstChild(`StudentDeskPrank{Id}`)
	if not T then T = Lib:FindFirstChild(OWN_DESKS[Rng:NextInteger(1, #OWN_DESKS)]) end
	return if T and T:IsA(`Model`) then T else nil
end

function Local.Desks(): { Model }
	local Out = {}
	local Props = workspace:FindFirstChild(`School`) and workspace.School:FindFirstChild(`NHProps`)
	for _, D in (Props and Props:GetChildren()) or {} do
		if D.Name == `StudentDesk` and D:IsA(`Model`) then table.insert(Out, D) end
	end
	return Out
end

function Local.Untag(Desk: Model)
	local Tag = Desk:FindFirstChild(`NHDeskTag`)
	if Tag then Tag:Destroy() end
	for _, X in Desk:GetDescendants() do
		local T = X:GetAttribute(`NHDeskT`)
		if T ~= nil and X:IsA(`BasePart`) then X.Transparency = T X:SetAttribute(`NHDeskT`, nil) end
	end
	Desk:SetAttribute(`NHDeskTag`, nil)
	Desk:SetAttribute(`NHDeskBy`, nil)
end

function Shared.TagDesk(By: string?, P: Player?): Model?
	local T = Local.DeskTemplate(By, P)
	if not T then return nil end
	local Free, Tagged = {}, 0
	for _, D in Local.Desks() do
		if D:GetAttribute(`NHDeskTag`) then Tagged += 1 else table.insert(Free, D) end
	end
	if Tagged >= DESK_MAX or #Free == 0 then return nil end
	local Desk = Free[Rng:NextInteger(1, #Free)]
	for _, X in Desk:GetDescendants() do
		if X:IsA(`BasePart`) then X:SetAttribute(`NHDeskT`, X.Transparency) X.Transparency = 1 end
	end
	local C = T:Clone()
	C.Name = `NHDeskTag`
	C:SetAttribute(`NHBuildKit`, nil)
	C:PivotTo(Desk:GetPivot())
	local Main = nil
	for _, X in C:GetDescendants() do
		if X:IsA(`BasePart`) then
			X.Anchored, X.CanCollide, X.CanQuery, X.CanTouch = true, false, false, false
			Main = Main or X
		end
	end
	C.Parent = Desk
	Desk:SetAttribute(`NHDeskTag`, T.Name)
	Desk:SetAttribute(`NHDeskBy`, By or (P and `you`) or nil)
	if Main then
		local Name = if By and Config.Defs[By] then `{Config.Defs[By].Name} desk` else `Carved desk`
		local Scrub = Local.Prompt(Main, `Scrub desk`, Name, E.CleanHold or 3, `NHScrub`)
		Scrub.Triggered:Connect(function(Player)
			if not C.Parent then return end
			Local.Untag(Desk)
			local N = svc(`Features.Notifications`)
			if N then pcall(N.Notify, Player, { Title = `Desk scrubbed`; Text = `Good as new. Nearly.`; Kind = `Good`; Duration = 3 }) end
		end)
	end
	return Desk
end

function Local.UntagAll()
	for _, D in Local.Desks() do if D:GetAttribute(`NHDeskTag`) then Local.Untag(D) end end
end

-- victims' students near a mess complain about it]])

rep([[function Shared.CleanAll()
	for _, M in Local.Folder(`Messes`):GetChildren() do if M:IsA(`Model`) then Local.RemoveMess(M) end end
end]], [[function Shared.CleanAll()
	for _, M in Local.Folder(`Messes`):GetChildren() do if M:IsA(`Model`) then Local.RemoveMess(M) end end
	pcall(Local.UntagAll) -- (1.66) the prank desks too
end]])

rep([[				Local.MakeMess(Spot, Victim, By, nil)
]], [[				Local.MakeMess(Spot, Victim, By, nil)
				pcall(Shared.TagDesk, By, nil) -- (1.66)
]])

rep([[	Local.MakeMess(Spot, Victim, nil, P)
	local Cl = Cliques()]], [[	Local.MakeMess(Spot, Victim, nil, P)
	pcall(Shared.TagDesk, nil, P) -- (1.66) your clique's desk, or a carved one
	local Cl = Cliques()]])

rep([[	for _ in Spots do Out.Spots += 1 end]], [[	for _ in Spots do Out.Spots += 1 end
	Out.Desks = {}
	for _, D in Local.Desks() do if D:GetAttribute(`NHDeskTag`) then table.insert(Out.Desks, D:GetAttribute(`NHDeskTag`)) end end]])

local f, e = loadstring(src)
assert(f, e)
S.Source = src
return "CliquePranks ok " .. #src
