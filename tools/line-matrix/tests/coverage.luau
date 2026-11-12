-- Line matrix coverage (NH Combat Test, Edit mode, run with execute_luau). Set ONLY to one module's name
-- ("Generic", "Vigil", ...) to check just that one; nil checks Generic and all 8 cliques.
local ONLY = nil
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Config = ReplicatedStorage:WaitForChild("Config")
assert(Config:FindFirstChild("CliqueTalk"), "Config.CliqueTalk is not installed")
local CT = require(Config.CliqueTalk:Clone()) -- a clone, so never a cached copy
local Cliques = require(Config.Cliques)
local MOMENTS = { "Greet", "Bump", "Crowded", "Shoved", "FightSeen", "Flee", "Transformed", "Night", "FullMoon", "Race", "Hurt", "Outfit", "DressCode" }
local SUBS = { Race = { "Human", "Priest", "Vampire", "Werewolf", "Ghoul", "Wraith" }, Outfit = { "FullLook", "RivalLook", "Likes", "Mocks" } }
local ATTS = { "Hostile", "Wary", "Neutral", "Friendly", "Respected" }
local KEYS = { Name = true, Piece = true, Clique = true, Rival = true, Day = true, Period = true, Moon = true }
local BANNED = { "blood", "bloody", "bleed", "bleeding", "gore", "guts", "corpse", "stab", "kill", "murder" }
local Fails, Cells, Count = {}, 0, 0

local function fail(Text) table.insert(Fails, Text) end

local function checkPool(Where, Pool)
	if typeof(Pool) ~= "table" then fail(`{Where}: not a list`) return end
	if #Pool < 3 or #Pool > 5 then fail(`{Where}: {#Pool} lines (want 3 to 5)`) end
	for _, L in Pool do
		Count += 1
		if typeof(L) ~= "string" then fail(`{Where}: not a string`) continue end
		if #L > 60 then fail(`{Where}: {#L} chars: {L}`) end
		for K in L:gmatch("{(%w*)}") do
			if not KEYS[K] then fail(`{Where}: unknown placeholder {K}: {L}`) end
		end
		local Low = L:lower()
		for _, W in BANNED do
			if Low:find("%f[%a]" .. W .. "%f[%A]") then fail(`{Where}: banned word "{W}": {L}`) end
		end
	end
end

local function checkNode(Where, Node, NoAny)
	if typeof(Node) ~= "table" then fail(`{Where}: missing`) return end
	for K, Pool in Node do
		if K ~= "Any" and not table.find(ATTS, K) then fail(`{Where}: unknown key {K}`) end
		checkPool(`{Where}.{K}`, Pool)
	end
	if NoAny and Node.Any then fail(`{Where}: uses Any (Greet must give every attitude its own lines)`) end
	for _, A in ATTS do
		Cells += 1
		local P = Node[A] or Node.Any
		if typeof(P) ~= "table" or #P == 0 then fail(`{Where}: nothing for {A} (would fall through to Generic)`) end
	end
end

local Names = { "Generic" }
for _, Id in Cliques.Order do table.insert(Names, Id) end
for _, Name in Names do
	if ONLY and Name ~= ONLY then continue end
	local Mod = CT[Name]
	if typeof(Mod) ~= "table" then fail(`{Name}: module missing`) continue end
	for K in Mod do
		if not table.find(MOMENTS, K) then fail(`{Name}: unknown moment {K}`) end
	end
	for _, Moment in MOMENTS do
		if SUBS[Moment] then
			for _, Sub in SUBS[Moment] do
				checkNode(`{Name}.{Moment}.{Sub}`, Mod[Moment] and Mod[Moment][Sub], false)
			end
		else
			checkNode(`{Name}.{Moment}`, Mod[Moment], Moment == "Greet" and Name ~= "Generic")
		end
	end
end
return if #Fails == 0 then `PASS: {Cells} cells, {Count} lines`
	else `FAIL ({#Fails}):\n` .. table.concat(Fails, "\n", 1, math.min(#Fails, 60))
