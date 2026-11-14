DEL = "ServerScriptService.Services.Features.Delinquents"
WOLF = "ServerScriptService.Services.Features.WildWolves"
ADM = "ServerScriptService.Services.Features.Admin"
PAN = "StarterPlayer.StarterPlayerScripts.Controllers.Gui.AdminPanel"

EDITS = [
    # --- Delinquents: spawn a role or a crew at a spot (the admin desk, in front of you) ---
    (DEL, """function Shared.OnStart()
	Folder = workspace:FindFirstChild(`Live`) or workspace""", """-- (2.19.0) the admin desk spawns them in front of you: the Map has no hangout spots, and testing wants them close
function Shared.SpawnAt(Role: string, Pos: Vector3): boolean
	if not ROLES[Role] then return false end
	if not Folder then Folder = workspace:FindFirstChild(`Live`) or workspace end
	local Before = count()
	pcall(spawnOne, Role, Pos)
	return count() > Before
end

-- a crew at a spot: 2 grunts, often a Brute, sometimes a Gang Leader. Returns how many came.
function Shared.CrewAt(Pos: Vector3): number
	local Crew = { `Grunt`, `Grunt` }
	if Rng:NextNumber() < 0.5 then table.insert(Crew, `Brute`) end
	if Rng:NextNumber() < 0.25 then table.insert(Crew, `Leader`) end
	local N = 0
	for _, Role in Crew do if Shared.SpawnAt(Role, Pos) then N += 1 end end
	return N
end

function Shared.OnStart()
	Folder = workspace:FindFirstChild(`Live`) or workspace"""),
    # --- Wild wolves: a pack right here, any time of day ---
    (WOLF, """local Pending = 0""", """local AdminNext = false -- (2.19.0) wolves spawned while this is set are the admin desk's (kept by day)
local Pending = 0"""),
    (WOLF, """	M:SetAttribute(`NoDowned`, true) -- wolves die, they don't get downed and gripped""",
     """	M:SetAttribute(`NoDowned`, true) -- wolves die, they don't get downed and gripped
	if AdminNext then M:SetAttribute(`NHAdminSpawn`, true) end -- (2.19.0)"""),
    (WOLF, """-- fixed, telegraphed fight pattern (replaces""", """-- (2.19.0) the admin desk: a pack right here, any time of day. They stay through the morning until killed or
-- cleared (the Map has no wolf spots and no night requirement for a test). Returns how many came.
function Shared.SpawnPack(At: Vector3, Count: number?): number
	local Before = 0
	for _ in Live do Before += 1 end
	AdminNext = true
	for _ = 1, math.clamp(Count or 3, 1, 6) do
		pcall(spawnWolf, At + Vector3.new(math.random(-6, 6), 0, math.random(-6, 6)))
	end
	AdminNext = false
	local After = 0
	for _ in Live do After += 1 end
	return After - Before
end

-- fixed, telegraphed fight pattern (replaces"""),
    (WOLF, """				for M in Live do Live[M] = nil M:Destroy() end -- they melt away by morning""",
     """				for M in Live do -- they melt away by morning (not an admin's test pack, 2.19.0)
					if not M:GetAttribute(`NHAdminSpawn`) then Live[M] = nil M:Destroy() end
				end"""),
    # --- Admin (server): delinquents and wolves in front of you ---
    (ADM, """C.SpawnDelinquents = { Run = function(A)
	local D = svc(`Features.Delinquents`)
	if not D then return false, `Delinquents missing` end
	D.Fill()
	return true, `A delinquent crew is on its way (out of sight)`
end }
C.SpawnWolves = { Run = function(A)
	local W = svc(`Features.WildWolves`)
	if not W then return false, `Wolves missing` end
	W.Fill()
	return true, `Wolves called (night only)`
end }""", """-- (2.19.0) enemies come in front of you, on the floor there: the Map has no hangout or wolf spots, and a test
-- wants them close. They stay until killed or cleared ("Clear all enemies").
local function aheadFloor(R: BasePart, Dist: number): Vector3?
	local P = RaycastParams.new()
	P.FilterType = Enum.RaycastFilterType.Exclude
	P.FilterDescendantsInstances = { workspace:FindFirstChild(`Live`) or R.Parent }
	local From = (R.CFrame * CFrame.new(0, 0, -Dist)).Position
	local Hit = workspace:Raycast(From + Vector3.new(0, 8, 0), Vector3.new(0, -40, 0), P)
	return Hit and Hit.Position or nil
end
local ROLE_NAMES = { Grunt = `delinquent`; Brute = `delinquent brute`; Leader = `gang leader` }
C.SpawnDelinquents = { Run = function(A)
	local D = svc(`Features.Delinquents`)
	local _, _, R = char(A)
	if not (D and R) then return false, `Delinquents missing` end
	local At = D.CrewAt and aheadFloor(R, 16)
	if not At then D.Fill() return true, `A delinquent crew is on its way (out of sight)` end
	local n = D.CrewAt(At)
	return n > 0, `{n} delinquents ahead of you`
end }
C.SpawnDelinquent = { Run = function(A, _, a)
	local D = svc(`Features.Delinquents`)
	local _, _, R = char(A)
	if not (D and R and D.SpawnAt) then return false, `Delinquents missing` end
	local Role = typeof(a) == `table` and ROLE_NAMES[a.Role] and a.Role or `Grunt`
	local At = aheadFloor(R, 12)
	if not At then return false, `No floor ahead of you` end
	if not D.SpawnAt(Role, At) then return false, `Couldn't spawn a {ROLE_NAMES[Role]}` end
	return true, `A {ROLE_NAMES[Role]} is ahead of you`
end }
C.SpawnWolves = { Run = function(A)
	local W = svc(`Features.WildWolves`)
	local _, _, R = char(A)
	if not (W and R) then return false, `Wolves missing` end
	if not W.SpawnPack then W.Fill() return true, `Wolves called (night only)` end
	local At = aheadFloor(R, 18)
	if not At then return false, `No floor ahead of you` end
	local n = W.SpawnPack(At, 3)
	if n == 0 then return false, `No wolves came: the wolf model (ServerStorage.NHWolf) isn't in this place` end
	return true, `{n} wolves ahead of you (they stay until killed or cleared)`
end }"""),
    (ADM, """	if not M then return false, `No beast called {name}` end""",
     """	if not M then -- (2.19.0) say why: the beast rigs live in ServerStorage.NHBeasts
		if not game:GetService(`ServerStorage`):FindFirstChild(`NHBeasts`) then return false, `The beast rigs (ServerStorage.NHBeasts) aren't in this place` end
		return false, `No beast called {name}`
	end"""),
    # --- Admin panel: one of each delinquent, and the pack works by day ---
    (PAN, """		button(g, `Delinquent crew`, function() run(`SpawnDelinquents`) end, `gold`, 230)
		button(g, `Wolf pack (night)`, function() run(`SpawnWolves`) end, `gold`, 230)""",
     """		button(g, `Delinquent crew`, function() run(`SpawnDelinquents`) end, `gold`, 230)
		-- (2.19.0) one of each, in front of you; the wolf pack comes any time of day
		button(g, `Delinquent`, function() run(`SpawnDelinquent`, false, { Role = `Grunt` }) end, `gold`, 230)
		button(g, `Delinquent Brute`, function() run(`SpawnDelinquent`, false, { Role = `Brute` }) end, `gold`, 230)
		button(g, `Gang Leader`, function() run(`SpawnDelinquent`, false, { Role = `Leader` }) end, `gold`, 230)
		button(g, `Wolf pack`, function() run(`SpawnWolves`) end, `gold`, 230)"""),
]
