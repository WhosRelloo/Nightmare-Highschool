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

return BellTower
