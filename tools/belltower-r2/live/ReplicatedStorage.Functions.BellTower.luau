--!strict
--[[ (2.36) The Bell Tower HUD's view logic (spec: docs/superpowers/specs/2026-11-20-notoriety-timetable-discipline-ui-design.md §4).
	Pure: no services, no instances. ClockHud and QuestTracker draw what these return. ]]
local BellTower = {}

BellTower.MIN_TEXT = 20 -- the owner's floor for game text, in design px

-- Conduct seal tints (ImageColor3 over the greyscale Seal)
local Tints: { [string]: Color3 } = { -- (2.36.1) typed for strict mode
	Warning = Color3.fromRGB(255, 168, 72);
	Detention = Color3.fromRGB(219, 31, 41);
	Probation = Color3.fromRGB(107, 15, 26);
	Suspension = Color3.fromRGB(51, 43, 48);
}
BellTower.Tints = Tints

function BellTower.Image(Art: { [string]: any }, Key: string): string?
	local Id = Art[Key]
	if typeof(Id) == "number" and Id > 0 then return "rbxassetid://" .. tostring(Id) end
	return nil
end

-- The dial's hand: midnight at the bottom, noon at the top (the rim art is baked the same way).
function BellTower.HandAngle(Hour: number): number
	return ((Hour / 24) * 360 + 180) % 360
end

-- What the conduct row shows, from the Discipline attributes (Services.School.Discipline / Detention).
function BellTower.Conduct(A: { [string]: any }, IsClass: boolean)
	local Level = A.DisciplineLevel
	if A.Suspended == true then Level = "Suspension" end
	local Points = tonumber(A.DisciplinePoints) or 0
	local Owed = math.max(0, math.floor(tonumber(A.DetentionsOwed) or 0))
	local Out = { Visible = false, Seal = nil :: string?, Broken = false, Text = "", Slips = {} :: { { Title: string, Line: string } }, Waypoint = false }
	if typeof(Level) == "string" and Level ~= "Clear" and BellTower.Tints[Level] then
		Out.Seal = Level
		Out.Broken = Level == "Suspension"
		Out.Text = if Level == "Suspension" then "Suspended" else `{Level} · {Points} pts`
	end
	if A.DetentionActive == true then
		local Done = tonumber(A.DetentionCollected) or 0
		local Total = tonumber(A.DetentionTotal) or 0
		table.insert(Out.Slips, { Title = "Detention", Line = if Done >= Total then "Use the bin to finish" else `Trash {Done}/{Total}` })
	elseif (tonumber(A.NHSummons) or 0) > 0 then -- (2.37) Notoriety: report to Room 106
		local S = math.floor(tonumber(A.NHSummons) or 0)
		table.insert(Out.Slips, { Title = if S > 1 then `Summons ×{S}` else "Summons", Line = "Room 106, outside class" })
		Out.Waypoint = not IsClass
	elseif Owed > 0 then
		table.insert(Out.Slips, { Title = if Owed > 1 then `Detention owed ×{Owed}` else "Detention owed", Line = "Room 106, outside class" })
		Out.Waypoint = not IsClass
	end
	Out.Visible = Out.Seal ~= nil or #Out.Slips > 0
	return Out
end

-- Fang pips for a counted objective (2 to 6); nil means "show the count as text".
function BellTower.Pips(Have: number, Need: number): { boolean }?
	local N = math.floor(tonumber(Need) or 1)
	if N < 2 or N > 6 then return nil end
	local H = math.clamp(math.floor(tonumber(Have) or 0), 0, N)
	local P = {}
	for I = 1, N do P[I] = I <= H end
	return P
end

-- (2.37) the Bell Rail (R2): tier names, fallback tints, and what the rail shows
BellTower.TierNames = { "Murmur", "Noticed", "Named", "Hunted", "The Tolling" }
BellTower.BellTint = {
	Hollow = Color3.fromRGB(70, 64, 74);
	Tarnished = Color3.fromRGB(110, 150, 128);
	Lit = Color3.fromRGB(235, 205, 120);
	Search = Color3.fromRGB(235, 205, 120);
}

function BellTower.BellStatus(Bells: any, State: any, Where: any)
	local N = math.clamp(math.floor(tonumber(Bells) or 0), 0, 5)
	local S = if State == "Lit" or State == "Search" or State == "Tarnished" or State == "Hollow" then State else "Hollow"
	local Out = { Visible = N > 0; Count = N; State = S; ArtKey = "BellHollow"; Tint = BellTower.BellTint[S];
		Glow = false; Dim = false; Swing = false; Line = "" }
	if N == 0 then return Out end
	Out.ArtKey = if S == "Lit" or S == "Search" then "BellLit" elseif S == "Tarnished" then "BellTarnished" else "BellHollow"
	Out.Glow = S == "Lit"
	Out.Dim = S == "Search"
	Out.Swing = S == "Search"
	local Place = if typeof(Where) == "string" and Where ~= "" then Where else "nearby"
	local Detail = if S == "Lit" then "they can see you"
		elseif S == "Search" then "searching · " .. Place
		elseif S == "Tarnished" then "they know who you are"
		else "something was seen"
	Out.Line = '<font color="#C8283C">' .. BellTower.TierNames[N] .. '</font> · ' .. Detail
	return Out
end

return BellTower
