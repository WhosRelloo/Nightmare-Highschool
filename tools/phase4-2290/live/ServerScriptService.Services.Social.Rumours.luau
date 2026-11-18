--[[ (2.29) Rumours (server). Services.Social.Rumours (docs/expansion/13-Living-School.md §4.3).
	Incidents become rumours. Rostered students who witnessed it know it; it spreads through pair chats (StudentBrain) and,
	off-screen, to a student near a knower, at most one hop per rumour every HopSeconds. Each hop may change one detail
	(MutateChance): the place (a neighbouring region), the size, or an NPC subject (to an NPC who was there).
	THE SAFETY RULE: a rumour about a real player carries only true facts. No player is ever added to a rumour or moved
	to another role, no player is ever swapped out of their own deed, and a rumour holding a player never mutates its
	place or size. RumourSafetyTest checks it over 10,000 hops.
	API: Make(I), Hop(R, Rng), Text(R), Live(), ForChat(SpeakerId, ListenerId), Heard(ListenerId, R), HeardByPlayer(P, R) ]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local Config = require(ReplicatedStorage.Config.Rumours)

local Shared = {}
local Local = {}
local Live = {} :: { any }
local NextId = 0
local Rng = Random.new()

local function svc(Path: string)
	local Node = ServerScriptService.Services
	for Seg in Path:gmatch(`[^%.]+`) do Node = Node and Node:FindFirstChild(Seg) end
	local Ok, M = pcall(require, Node)
	return if Ok then M else nil
end
local function isPlayer(X) return typeof(X) == `Instance` and X:IsA(`Player`) end

function Local.TemplateKey(I): string? return if I.Kind == `Scene` then I.Scene else I.Kind end

function Shared.Make(I)
	local Key = Local.TemplateKey(I)
	if not (Key and Config.Templates[Key]) then return nil end
	NextId += 1
	local Subject = {}
	for _, W in I.Who or {} do table.insert(Subject, { Id = W.Id; Role = W.Role }) end
	local R = { Id = NextId; Kind = I.Kind; Key = Key; Subject = Subject; Where = I.Region; Size = math.max(1, I.Size or 1); T = I.T or os.time(); -- (2.29) Size: a scene's outcome sets it
		Truth = I.Truth ~= false; Hops = 0; Notable = (I.Severity or 1) >= 3; Knowers = {}; LastHop = os.clock();
		Witnesses = table.clone(I.Witnesses or {}); Extra = I.Extra or I.Reason or I.Event; Template = 1 }
	R.Base = { Where = R.Where; Size = R.Size }
	for _, Id in R.Witnesses do R.Knowers[Id] = true end
	return R
end

function Local.HasPlayer(R): boolean
	for _, S in R.Subject do if isPlayer(S.Id) then return true end end
	return false
end

-- a neighbouring region: the nearest other region box to this one
function Local.Neighbour(Where: string?): string?
	local Folder = workspace:FindFirstChild(`Regions`)
	local From = Folder and Where and Folder:FindFirstChild(Where)
	if not From then return Where end
	local Best, BestD = nil, math.huge
	for _, B in Folder:GetChildren() do
		if B:IsA(`BasePart`) and B ~= From then
			local D = (B.Position - From.Position).Magnitude
			if D < BestD then Best, BestD = B.Name, D end
		end
	end
	return Best or Where
end

function Shared.Hop(R, Rng2: Random)
	local H = table.clone(R)
	H.Subject = {}
	for _, S in R.Subject do table.insert(H.Subject, { Id = S.Id; Role = S.Role }) end
	H.Hops = R.Hops + 1
	H.Knowers = R.Knowers -- the same set: one rumour, mangled as it travels
	if Rng2:NextNumber() >= Config.MutateChance then return H end
	local Safe = not Local.HasPlayer(R) -- THE SAFETY RULE: a rumour with a player in it never mutates
	if not Safe then return H end
	local Choice = Rng2:NextInteger(1, 3)
	local Ladder = Config.Sizes[R.Key]
	if Choice == 1 then
		H.Where = Local.Neighbour(R.Where)
	elseif Choice == 2 and Ladder then
		H.Size = math.clamp(R.Size + 1, 1, #Ladder)
	else
		-- the person: an NPC subject becomes another NPC who was there (never a player: witnesses are rostered ids)
		local Pool = {}
		for _, Id in R.Witnesses do
			local Taken = false
			for _, S in H.Subject do if S.Id == Id then Taken = true end end
			if not Taken then table.insert(Pool, Id) end
		end
		if #Pool > 0 and #H.Subject > 0 then
			local K = Rng2:NextInteger(1, #H.Subject)
			H.Subject[K] = { Id = Pool[Rng2:NextInteger(1, #Pool)]; Role = H.Subject[K].Role }
		end
	end
	return H
end

function Local.Name(Id): string
	if isPlayer(Id) then
		local Ok, N = pcall(function() return require(ServerScriptService.Services.AI.StudentBrain.Talk).FirstName(Id) end)
		return if Ok and N then N else Id.DisplayName
	end
	local Roster = svc(`Social.Roster`)
	local E = Roster and typeof(Id) == `string` and Roster.Get(Id)
	if E then return E.First end
	local Cast = require(ReplicatedStorage.Config.Npcs)
	if Cast[Id] then return Cast[Id].Name end
	return tostring(Id)
end

function Shared.Text(R): string
	local T = Config.Templates[R.Key][R.Template] or Config.Templates[R.Key][1]
	local Ladder = Config.Sizes[R.Key]
	local Past = Config.Sizes[R.Key .. `Past`]
	local Fill = { Where = Config.Places[R.Where or ``] or (if R.Where then R.Where else `school`);
		Size = Ladder and Ladder[R.Size] or ``; SizePast = Past and Past[R.Size] or ``; Extra = if R.Extra then tostring(R.Extra) else `` }
	for _, S in R.Subject do Fill[S.Role] = Fill[S.Role] or Local.Name(S.Id) end
	local Out = T:gsub("{(%w+)}", function(K) return Fill[K] or `someone` end) -- (a plain string: {..} in backticks would interpolate)
	return (Out:gsub(`%s+$`, ``))
end

function Shared.Live() return Live end

function Local.Add(R)
	if not R then return end
	table.insert(Live, R)
	while #Live > Config.MaxLive do table.remove(Live, 1) end
end

-- a rumour the speaker knows and the listener doesn't (nil if none)
function Shared.ForChat(SpeakerId: string?, ListenerId: string?)
	if not (SpeakerId and ListenerId) then return nil end
	for _, R in Live do
		if R.Knowers[SpeakerId] and not R.Knowers[ListenerId] then return R end
	end
	return nil
end

-- the listener now knows it; the rumour itself hops (and may change) at most once per HopSeconds
function Shared.Heard(ListenerId: string, R)
	R.Knowers[ListenerId] = true
	if os.clock() - R.LastHop >= Config.HopSeconds then
		local H = Shared.Hop(R, Rng)
		for K, V in H do R[K] = V end
		R.LastHop = os.clock()
	end
end

-- a player overheard it: a rostered student named in it whom the player can't meet any other way (fell out first) is
-- now known by name (doc 13 §2.5)
function Shared.HeardByPlayer(P: Player, R)
	local Rep, Roster = svc(`Social.Reputation`), svc(`Social.Roster`)
	if not (Rep and Roster) then return end
	for _, S in R.Subject do
		if typeof(S.Id) == `string` and Roster.IsRostered(S.Id) then
			local E = Rep.Entry(P, S.Id)
			if not E.Met and E.Value < -19 then Rep.Learn(P, S.Id) end
		end
	end
end

-- off-screen spread: every 10 s, a rumour whose hop is due passes from a knower to a student near them
function Local.Spread()
	local Roster = svc(`Social.Roster`)
	if not Roster then return end
	local Now = os.time()
	for K = #Live, 1, -1 do
		local R = Live[K]
		if Now - R.T > Config.LifeSeconds then table.remove(Live, K) continue end
		if os.clock() - R.LastHop < Config.HopSeconds then continue end
		local Knowers = {}
		for Id in R.Knowers do table.insert(Knowers, Id) end
		if #Knowers == 0 then continue end
		local From = Knowers[Rng:NextInteger(1, #Knowers)]
		local W = Roster.WhereNow(From)
		local Near = W.At and Roster.Near(W.At, 30) or {}
		for _, Id in Near do
			if not R.Knowers[Id] then Shared.Heard(Id, R) break end
		end
	end
end

function Shared.OnStart()
	task.defer(function()
		local Inc = svc(`World.Incidents`)
		if Inc then Inc.On(`*`, function(I) Local.Add(Shared.Make(I)) end) end
	end)
	task.spawn(function()
		while true do
			task.wait(10)
			local Ok, Err = pcall(Local.Spread)
			if not Ok then warn(`[Rumours] {Err}`) end
		end
	end)
end

function Shared.ClearForTests() table.clear(Live) end
function Shared.AgeForTests(R, Seconds: number) R.LastHop -= Seconds end

return Shared
