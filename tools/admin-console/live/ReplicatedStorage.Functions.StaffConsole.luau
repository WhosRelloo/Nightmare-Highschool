--[[
	StaffConsole (shared, pure): the Headmaster's Console rules (spec docs/superpowers/specs/2026-11-23-admin-console-design.md).
	Levels (§6), argument checks (§7), the palette search (§5), registry validation. No services, no state: the server
	(Features.Admin) and the client (Controllers.Gui.StaffConsole) both use it, and checks/console_pure.lua tests it.
]]
local Shared = {}

Shared.DANGER_HOLD = 0.8
Shared.SECTIONS = {
	Moderate = { "Student", "Server" },
	Test = { "Character", "Progress", "School", "Story", "World", "Spawns", "Self" },
}
Shared.SIDE_LEVEL = { Moderate = 1, Test = 2 }
Shared.LEVEL_NAMES = { "a moderator", "an admin", "the owner" }

local KINDS = { number = true, text = true, choice = true, toggle = true, position = true }
local TARGETS = { none = true, required = true, optional = true }

-- 0 none, 1 moderator, 2 admin, 3 owner. In Studio: 3, or the server-set test level (0-3), or 0 for NHTestNotAdmin.
function Shared.LevelFrom(F: any): number
	if F.Studio then
		local T = tonumber(F.TestLevel)
		if T and T == math.floor(T) and T >= 0 and T <= 3 then return T end
		if F.NotAdmin then return 0 end
		return 3
	end
	local Rank = tonumber(F.Rank) or 0
	if F.Owner or Rank >= 255 then return 3 end
	if F.Admin or F.Tester then return 2 end
	if Rank >= 254 then return 1 end
	return 0
end

local function inList(List: any, V: any): boolean
	for _, It in List or {} do
		if It == V or (typeof(It) == "table" and It.Id == V) then return true end
	end
	return false
end

-- Only declared args come back; missing optional args stay nil (the command's own default applies).
function Shared.CheckArgs(Schema: any, Args: any, Lists: any): (boolean, any)
	Args = if typeof(Args) == "table" then Args else {}
	local Out = {}
	for _, A in Schema or {} do
		local Label = A.Label or A.Name
		local V = Args[A.Name]
		if V == nil or V == "" then
			if A.Required then return false, `{Label} is needed` end
			continue
		end
		if A.Kind == "number" then
			local N = tonumber(V)
			if not N or N ~= N then return false, `{Label} must be a number` end
			if N < A.Min or N > A.Max then return false, `{Label} must be {A.Min} to {A.Max}` end
			Out[A.Name] = N
		elseif A.Kind == "text" then
			if typeof(V) ~= "string" then return false, `{Label} must be text` end
			Out[A.Name] = string.sub(V, 1, A.Max or 200)
		elseif A.Kind == "choice" then
			local Ok = (A.Choices ~= nil and table.find(A.Choices, V) ~= nil) or (A.From ~= nil and inList(Lists and Lists[A.From], V))
			if not Ok then return false, `Unknown {Label}: {tostring(V)}` end
			Out[A.Name] = V
		elseif A.Kind == "toggle" then
			if typeof(V) ~= "boolean" then return false, `{Label} must be on or off` end
			Out[A.Name] = V
		elseif A.Kind == "position" then
			if typeof(V) ~= "Vector3" then return false, `{Label} must be a position` end
			for _, C in { V.X, V.Y, V.Z } do
				if C ~= C or math.abs(C) == math.huge or math.abs(C) > 1e6 then return false, `{Label} must be a position` end
			end
			Out[A.Name] = V
		end
	end
	return true, Out
end

-- Title prefix 3, title contains 2, synonym exact 3 / prefix 2, help contains 1; ties by Title.
function Shared.Search(Defs: any, Query: string?): any
	local Q = string.match(string.lower(Query or ""), "^%s*(.-)%s*$") or ""
	if Q == "" then return {} end
	local Hits = {}
	for _, D in Defs do
		local T = string.lower(D.Title)
		local Score = 0
		if string.sub(T, 1, #Q) == Q then Score = 3 elseif string.find(T, Q, 1, true) then Score = 2 end
		for _, W in D.Synonyms or {} do
			local L = string.lower(W)
			if L == Q then Score = math.max(Score, 3) elseif string.sub(L, 1, #Q) == Q then Score = math.max(Score, 2) end
		end
		if Score == 0 and string.find(string.lower(D.Help or ""), Q, 1, true) then Score = 1 end
		if Score > 0 then table.insert(Hits, { Def = D; Score = Score }) end
	end
	table.sort(Hits, function(A, B)
		if A.Score ~= B.Score then return A.Score > B.Score end
		return A.Def.Title < B.Def.Title
	end)
	local Out = {}
	for _, H in Hits do table.insert(Out, H.Def) end
	return Out
end

function Shared.Validate(Id: string, D: any): (boolean, string?)
	local function bad(Why: string) return false, `{Id}: {Why}` end
	if typeof(D) ~= "table" then return bad("not a table") end
	if not Shared.SECTIONS[D.Side] then return bad("Side") end
	if not table.find(Shared.SECTIONS[D.Side], D.Section) then return bad("Section") end
	if typeof(D.Title) ~= "string" or D.Title == "" then return bad("Title") end
	if typeof(D.Help) ~= "string" or D.Help == "" then return bad("Help") end
	if typeof(D.Icon) ~= "string" or D.Icon == "" then return bad("Icon") end
	if not (D.Level == 1 or D.Level == 2 or D.Level == 3) then return bad("Level") end
	if D.Level < Shared.SIDE_LEVEL[D.Side] then return bad("Level below its side") end
	if not TARGETS[D.Target] then return bad("Target") end
	if typeof(D.Args) ~= "table" then return bad("Args") end
	for _, A in D.Args do
		if typeof(A) ~= "table" or typeof(A.Name) ~= "string" or not KINDS[A.Kind] then return bad("an arg") end
		if A.Kind == "number" and not (typeof(A.Min) == "number" and typeof(A.Max) == "number") then return bad(`{A.Name} needs Min and Max`) end
		if A.Kind == "choice" and not (A.Choices or A.From) then return bad(`{A.Name} needs Choices or From`) end
	end
	if typeof(D.Danger) ~= "boolean" then return bad("Danger") end
	if typeof(D.Synonyms) ~= "table" then return bad("Synonyms") end
	return true
end

function Shared.Public(Id: string, D: any): any
	return {
		Id = Id; Side = D.Side; Section = D.Section; Title = D.Title; Help = D.Help; Icon = D.Icon; Level = D.Level;
		Target = D.Target; Args = D.Args; Danger = D.Danger; Synonyms = D.Synonyms; Local = D.Local;
	}
end

return Shared
