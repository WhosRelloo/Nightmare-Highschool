--[[
	Delinquents (server): crews of street delinquents hang around the grounds and pick fights, a PVE source of
	Combat EXP and Yen. They're the regular combat AI (Services.AI.AI) with a low Config.Skill, so they block,
	dodge and feint far less than the sparring demon and are beatable by a new student.
	  * Spots: parts tagged NHDelinquentSpawn (workspace.Map.NHHangouts: the empty south-east lot, away from classes
	    and the sports venues, 2026-11-02), else the Field, the Pitch and the Boiler Yard.
	  * A crew is 2 grunts, sometimes a Brute, rarely a Gang Leader. Up to MAX alive; crews refill out of sight.
	  * They only chase within AggroRange and give up past ChaseRange (they walk back to their spot).
	  * Defeat (they die, never downed): the killer gets EXP (Combat) + Yen by role.
]]
local Players = game:GetService(`Players`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local CollectionService = game:GetService(`CollectionService`)

local NPCConfig = require(ReplicatedStorage.Config.NPC)

local MAX = 6
local REFILL_EVERY = 20       -- seconds between refill checks
local MIN_PLAYER_DIST = 45    -- crews never pop in right next to a student

local function cfg(over)
	local C = table.clone(NPCConfig.Default)
	C.AggroRange = 26
	C.AttackRange = 10
	C.ChaseRange = 70
	C.Weapon = `Fist`
	C.AttackCooldown = 0.9
	C.IdleWaitTime = 2.5
	C.PatrolSpeed = 8
	C.ChaseSpeed = 16
	C.MaxStringLength = 2
	C.MaxPressureTime = 0.6
	C.RecoveryWindow = 1.6
	C.CorpseTime = 5
	C.RespawnTime = nil
	C.Tier = `Easy` -- Config.NPC.Tiers (1.23); the tier sets how they parry, block, dodge and attack
	for K, V in over or {} do C[K] = V end
	return C
end

local ROLES = {
	Grunt = { Name = `Delinquent`; Health = 100; Exp = 30; Yen = 10; Config = cfg() };
	Brute = { Name = `Delinquent Brute`; Health = 170; Exp = 45; Yen = 15; Config = cfg({ Tier = `Normal` }) };
	Leader = { Name = `Gang Leader`; Health = 220; Exp = 85; Yen = 30; Config = cfg({ Tier = `Hard`; AggroRange = 32 }) };
}

-- street looks: Appearance ids (resolved to indices at runtime so list reorders can't break them)
local TOPS = { `delinquent-polo`, `leather-jacket`, `open-flannel`, `varsity-jacket`, `the-hollow-band-tee`, `blood-moon-hoodie`, `delinquent-polo` }
local BOTTOMS = { `ripped-jeans`, `black-jeans`, `cargo-boots`, `striped-joggers`, `black-jeans-boots` }
local HAIR_HEX = { ``, ``, `E8D27A`, `C0392B`, `F2F2F2`, `D35400`, `` } -- some bleached / dyed
local BROWS = { `angry`, `furrowed`, `sharparch`, `flatthick`, `straight` }
local MOUTHS = { `smirk`, `scowl`, `grin`, `frown`, `flat` }

local Shared = {}
local Rng = Random.new()
local Alive = {} :: { [Model]: string }
local Folder: Folder? = nil

local function floorAt(At: Vector3): Vector3?
	local P = RaycastParams.new()
	P.FilterType = Enum.RaycastFilterType.Exclude
	P.FilterDescendantsInstances = { workspace:FindFirstChild(`Live`) }
	local Hit = workspace:Raycast(At + Vector3.new(0, 6, 0), Vector3.new(0, -60, 0), P)
	return Hit and Hit.Normal.Y > 0.6 and Hit.Position or nil
end

local function spots(): { Vector3 }
	local Out = {}
	for _, S in CollectionService:GetTagged(`NHDelinquentSpawn`) do
		if S:IsA(`BasePart`) then table.insert(Out, S.Position) end
	end
	if #Out > 0 then return Out end
	local School = workspace:FindFirstChild(`School`)
	local Sports = workspace:FindFirstChild(`Sports`)
	local function at(M: Instance?, fx: number, fz: number)
		if not M then return end
		local CF, Size
		if M:IsA(`BasePart`) then CF, Size = M.CFrame, M.Size else CF, Size = M:GetBoundingBox() end
		local F = floorAt((CF * CFrame.new(Size.X * fx, Size.Y / 2, Size.Z * fz)).Position)
		if F then table.insert(Out, F) end
	end
	local Field = Sports and Sports:FindFirstChild(`Field`)
	local Pitch = Sports and Sports:FindFirstChild(`Pitch`)
	local Yard = School and School:FindFirstChild(`BoilerYard`)
	at(Field, -0.3, -0.3) at(Field, 0.3, 0.3)
	at(Pitch, -0.3, 0.25) at(Pitch, 0.3, -0.25)
	at(Yard, -0.2, 0.2) at(Yard, 0.25, -0.2)
	return Out
end

local function nearestPlayer(Pos: Vector3): number
	local Best = math.huge
	for _, P in Players:GetPlayers() do
		local R = P.Character and P.Character:FindFirstChild(`HumanoidRootPart`)
		if R then Best = math.min(Best, (R.Position - Pos).Magnitude) end
	end
	return Best
end

local function dress(Char: Model)
	local App = require(ReplicatedStorage.UI.Appearance)
	local Look = App.Sanitize({})
	local Female = Rng:NextNumber() < 0.3
	Look.Body = Female and 2 or 1
	Look.Skin = Rng:NextInteger(1, math.max(1, #App.Skins))
	Look.Uniform = App.IndexOf(App.Uniforms, TOPS[Rng:NextInteger(1, #TOPS)]) or Look.Uniform
	local Bottom = Female and Rng:NextNumber() < 0.5 and `black-skirt-fishnets` or BOTTOMS[Rng:NextInteger(1, #BOTTOMS)]
	Look.Bottoms = App.IndexOf(App.BottomsList, Bottom) or Look.Bottoms
	Look.Eyes = Rng:NextInteger(2, math.max(2, #App.Eyes))
	Look.EyeSet = Female and 2 or 1
	for I, B in App.Brows do if B.Style == BROWS[Rng:NextInteger(1, #BROWS)] then Look.Brows = I break end end
	for I, M in App.Mouths do if M.Style == MOUTHS[Rng:NextInteger(1, #MOUTHS)] then Look.Mouth = I break end end
	-- a hair from the owner's catalog for the right group
	local Cat = ReplicatedStorage:FindFirstChild(`NHHairCatalog`)
	if Cat then
		local Pool = {}
		for _, H in Cat:GetChildren() do
			if H:GetAttribute(`Group`) == (Female and `Female` or `Male`) then table.insert(Pool, H:GetAttribute(`AssetId`)) end
		end
		if #Pool > 0 then Look.HairId = Pool[Rng:NextInteger(1, #Pool)] end
	end
	Look.HairColor = Rng:NextInteger(1, math.max(1, #App.HairColors))
	Look.HairHex = HAIR_HEX[Rng:NextInteger(1, #HAIR_HEX)]
	Look._Idx = true
	pcall(App.ApplyTo, Char, Look)
end

local function patrolAround(Pos: Vector3): { Vector3 }
	local Pts = {}
	for I = 1, 4 do
		local A = (I / 4) * math.pi * 2 + Rng:NextNumber(-0.4, 0.4)
		local F = floorAt(Pos + Vector3.new(math.cos(A), 0, math.sin(A)) * Rng:NextNumber(6, 14))
		if F then table.insert(Pts, F) end
	end
	return Pts
end

local function spawnOne(Role: string, Pos: Vector3)
	local R = ROLES[Role]
	local AI = require(ServerScriptService.Services.AI.AI)
	local npc = AI.Spawn(Folder, nil, patrolAround(Pos), R.Config)
	local Char = npc and npc.Character
	if not Char then return end
	Char.Name = R.Name
	Char:SetAttribute(`NHDelinquent`, Role)
	-- delinquents go down like students: carry (V), grip (B) or a race finisher (N) them before they get back up;
	-- a finish (or any kill) pays the killer through AI.NPCDefeated below
	Char:PivotTo(CFrame.new(Pos + Vector3.new(Rng:NextNumber(-3, 3), 3, Rng:NextNumber(-3, 3))) * CFrame.Angles(0, Rng:NextNumber(0, math.pi * 2), 0))
	npc.HomeCFrame = Char:GetPivot()
	local Hum = Char:FindFirstChildWhichIsA(`Humanoid`)
	if Hum then
		Hum.DisplayName = R.Name
		Hum.NameDisplayDistance = 45
		Hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.Viewer
		Hum.MaxHealth = R.Health
		Hum.Health = R.Health
	end
	if Role == `Brute` then
		for _, P in Char:GetChildren() do
			if P:IsA(`BasePart`) and P.Name ~= `HumanoidRootPart` then P.Color = P.Color end
		end
	end
	Alive[Char] = Role
	task.spawn(dress, Char)
	Char.AncestryChanged:Connect(function(_, Parent) if not Parent then Alive[Char] = nil end end)
end

local function count(): number
	local N = 0
	for C in Alive do if C.Parent then N += 1 else Alive[C] = nil end end
	return N
end

function Shared.Fill()
	local Room = MAX - count()
	if Room < 2 then return end
	local Pts = spots()
	-- prefer a spot no student is standing near
	local Choice
	for _ = 1, 8 do
		local P = Pts[Rng:NextInteger(1, #Pts)]
		if P and nearestPlayer(P) >= MIN_PLAYER_DIST then Choice = P break end
	end
	if not Choice then return end
	local Crew = { `Grunt`, `Grunt` }
	if Room >= 3 and Rng:NextNumber() < 0.35 then table.insert(Crew, `Brute`) end
	if Room >= #Crew + 1 and Rng:NextNumber() < 0.2 then table.insert(Crew, `Leader`) end
	for _, Role in Crew do pcall(spawnOne, Role, Choice) end
end

function Shared.OnStart()
	Folder = workspace:FindFirstChild(`Live`) or workspace
	local AI = require(ServerScriptService.Services.AI.AI)
	AI.NPCDefeated:Connect(function(Char: Model, Killer: Model?)
		local Role = Char:GetAttribute(`NHDelinquent`)
		if not Role then return end
		Alive[Char] = nil
		local R = ROLES[Role]
		local P = Killer and Players:GetPlayerFromCharacter(Killer)
		if P and R then
			pcall(function() require(ServerScriptService.Services.Player.Progression).Award(P, R.Exp, `Combat`, `Delinquent`) end)
			pcall(function() require(ServerScriptService.Services.Player.Data).UpdateState(P, { type = `UpdateYen`; amount = R.Yen }) end)
		end
	end)
	task.delay(6, function()
		while true do
			pcall(Shared.Fill)
			task.wait(REFILL_EVERY)
		end
	end)
end

return Shared
