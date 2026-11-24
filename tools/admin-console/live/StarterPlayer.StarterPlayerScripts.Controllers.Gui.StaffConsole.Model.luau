--[[ StaffConsole.Model (client, pure): the console's state rules. No Instances; checks/console_model.lua tests it. ]]
local Model = {}
local RECENT_MAX, FEED_MAX = 5, 5

function Model.New()
	return { Side = "Moderate"; Section = "Student"; Selected = nil :: number?; Recent = {} :: { number };
		Favs = {} :: { string }; Feed = {} :: { any }; Filter = ""; Level = 0 }
end

function Model.Sides(Level: number): { string }
	if Level >= 2 then return { "Moderate", "Test" } end
	if Level >= 1 then return { "Moderate" } end
	return {}
end

function Model.SetLevel(S: any, Level: number, Sections: any)
	S.Level = Level
	local Sides = Model.Sides(Level)
	if not table.find(Sides, S.Side) then S.Side = Sides[1] or "Moderate" S.Section = (Sections[S.Side] or {})[1] end
	if not table.find(Sections[S.Side] or {}, S.Section) then S.Section = (Sections[S.Side] or {})[1] end
end

function Model.Section(S: any, Index: number, Sections: any): boolean
	local Name = (Sections[S.Side] or {})[Index]
	if not Name then return false end
	S.Section = Name
	return true
end

function Model.Cards(Defs: any, Side: string, Section: string): any
	local Out = {}
	for _, D in Defs do if D.Side == Side and D.Section == Section then table.insert(Out, D) end end
	table.sort(Out, function(a, b) return a.Title < b.Title end)
	return Out
end

function Model.ToggleFav(S: any, Id: string): boolean
	local I = table.find(S.Favs, Id)
	if I then table.remove(S.Favs, I) return false end
	table.insert(S.Favs, Id)
	return true
end

function Model.Favourites(Defs: any, S: any): any
	local ById = {}
	for _, D in Defs do ById[D.Id] = D end
	local Out = {}
	for _, Id in S.Favs do if ById[Id] then table.insert(Out, ById[Id]) end end
	return Out
end

function Model.Pick(S: any, UserId: number)
	S.Selected = UserId
	local I = table.find(S.Recent, UserId)
	if I then table.remove(S.Recent, I) end
	table.insert(S.Recent, 1, UserId)
	while #S.Recent > RECENT_MAX do table.remove(S.Recent) end
end

function Model.Rows(Players: any, Filter: string, Recent: { number }): any
	local Q = string.lower(Filter or "")
	local Out = {}
	for _, P in Players or {} do
		if Q == "" or string.find(string.lower(P.Name), Q, 1, true) or string.find(string.lower(P.Display or ""), Q, 1, true) then
			table.insert(Out, P)
		end
	end
	table.sort(Out, function(a, b)
		local ra, rb = table.find(Recent, a.UserId) or math.huge, table.find(Recent, b.UserId) or math.huge
		if ra ~= rb then return ra < rb end
		return string.lower(a.Name) < string.lower(b.Name)
	end)
	return Out
end

function Model.Flags(P: any): { string }
	local Out = {}
	if P.Note then table.insert(Out, "NOTE") end
	if P.Muted then table.insert(Out, "MUTED") end
	if P.Frozen then table.insert(Out, "FROZEN") end
	if P.InMenu then table.insert(Out, "IN MENU") end
	if P.God then table.insert(Out, "GOD") end
	return Out
end

function Model.Push(S: any, Ok: boolean, Text: string, Title: string?)
	table.insert(S.Feed, 1, { Ok = Ok; Text = Text; Title = Title or ""; At = os.clock() })
	while #S.Feed > FEED_MAX do table.remove(S.Feed) end
end

-- Can the card run? Same rules the server applies (StaffConsole.CheckArgs), so a ready card is never refused for its values.
-- Lists (optional) is the snapshot's Lists, for choice args that draw from a list.
function Model.Ready(Def: any, Values: any, Selected: number?, Lists: any?): (boolean, string?)
	if Def.Target == "required" and not Selected then return false, "Pick a student on the left first" end
	local Shared = require(game:GetService("ReplicatedStorage").Functions.StaffConsole)
	local Ok, Why = Shared.CheckArgs(Def.Args or {}, Values or {}, Lists)
	if not Ok then return false, Why end
	return true, nil
end

return Model
