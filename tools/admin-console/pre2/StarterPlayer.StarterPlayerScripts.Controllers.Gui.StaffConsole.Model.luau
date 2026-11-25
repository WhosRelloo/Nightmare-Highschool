--[[ StaffConsole.Model (client, pure): the console's state rules. No Instances; checks/console_model.lua tests it.
	1b: offline picks (from the Log), saved prefs, the history timeline and summary, the Unban note, log labels. ]]
local Records = require(game:GetService("ReplicatedStorage"):WaitForChild("Functions"):WaitForChild("StaffRecords"))
local Model = {}
local RECENT_MAX, FEED_MAX = 5, 5

function Model.New()
	return { Side = "Moderate"; Section = "Student"; Selected = nil :: number?; Offline = false; Recent = {} :: { number };
		Favs = {} :: { string }; Feed = {} :: { any }; Filter = ""; Level = 0;
		Log = { Day = 0; Query = ""; Chip = "All"; Page = 1 }; PrefsTried = false; PrefsOk = false }
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

-- Offline: picked from the Log, not in this server (only their history works)
function Model.Pick(S: any, UserId: number, Offline: boolean?)
	S.Selected = UserId
	S.Offline = Offline == true
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
	-- (phase 2) from the player list: the Transformation attribute, NHBells, the Prologue not seen yet, a cut or Wickfield
	if P.Transformed == true then table.insert(Out, "TRANSFORMED") end
	if (tonumber(P.Bells) or 0) >= 3 then table.insert(Out, "WANTED") end
	if P.New == true then table.insert(Out, "NEW") end
	if P.InCutscene == true then table.insert(Out, "IN CUTSCENE") end
	return Out
end

function Model.Push(S: any, Ok: boolean, Text: string, Title: string?)
	table.insert(S.Feed, 1, { Ok = Ok; Text = Text; Title = Title or ""; At = os.clock() })
	while #S.Feed > FEED_MAX do table.remove(S.Feed) end
end

-- Can the card run? Same rules the server applies (StaffConsole.CheckArgs), so a ready card is never refused for its values.
-- Lists (optional) is the snapshot's Lists, for choice args that draw from a list.
-- A ready card also returns the cleaned values (CheckArgs' Out: declared args only, numbers as numbers, text cut to
-- Max), which the shell sends instead of the raw box values.
function Model.Ready(Def: any, Values: any, Selected: number?, Lists: any?, Offline: boolean?): (boolean, string?, any)
	if (Def.Target == "required" or Def.Target == "user") and not Selected then return false, "Pick a student on the left first", nil end
	if Def.Target == "required" and Offline then return false, "They're not in this server: only their history works", nil end
	local Shared = require(game:GetService("ReplicatedStorage").Functions.StaffConsole)
	local Ok, Out = Shared.CheckArgs(Def.Args or {}, Values or {}, Lists)
	if not Ok then return false, Out, nil end
	return true, nil, Out
end

-- saved favourites and side (spec 1b §4): ids no longer in the registry are dropped; a side the level can't open is ignored
function Model.LoadPrefs(S: any, P: any, Defs: any, Sections: any)
	if typeof(P) ~= "table" then return end
	local Known = {}
	for _, D in Defs do Known[D.Id] = true end
	S.Favs = Records.CleanFavs(P.Favs, Known)
	local Side = Records.CleanSide(P.Side)
	if Side and table.find(Model.Sides(S.Level), Side) then
		S.Side = Side
		S.Section = (Sections[Side] or {})[1]
	end
end

-- the history timeline: newest first; lifted, or ended on time, bans and mutes are greyed; the owner may remove
function Model.Timeline(Rec: any, Level: number, Now: number): any
	local Out = {}
	for _, T in Records.Timeline(Records.Normalize(Rec)) do
		local E = T.Entry
		local State = nil
		if T.List == "Bans" or T.List == "Mutes" then
			if E.Lifted then State = "lifted"
			elseif (T.List == "Bans" and not Records.BanOn(E, Now)) or (T.List == "Mutes" and not Records.MuteOn(E, Now)) then State = "ended" end
		end
		table.insert(Out, { Kind = T.Kind; List = T.List; At = E.At; By = E.By; Who = E.ByName or tostring(E.By);
			Text = Records.EntryText(T.List, E); State = State; Lifted = State ~= nil; CanRemove = Level >= 3 })
	end
	return Out
end

function Model.Summary(Rec: any, Now: number, Clock: ((number) -> string)?): string
	return Records.Summary(Records.Normalize(Rec), Now, Clock)
end

-- the line the Unban card shows: the ban it would lift (H = the History result for the typed UserId; nil = loading)
function Model.UnbanNote(H: any, Clock: ((number) -> string)?): string?
	if H == nil then return nil end
	if not H.Ok then return H.Error or "History unavailable" end
	local Ban = Records.OpenBan(Records.Normalize(H.Record))
	if not Ban then return "No ban on record: counts as permanent (owner only)" end
	local Fmt = Clock or function(T: number): string return os.date("%d %b", T) end
	local Length = if (tonumber(Ban.Days) or 0) == 0 then "permanent" else `{Ban.Days}-day`
	return `Lifts: {Length} ban by {Ban.ByName or tostring(Ban.By)}, {Fmt(Ban.At)}{if Records.UnbanLevel(Ban) == 3 then " (owner only)" else ""}`
end

-- log days are UTC days (the server's keys), so the labels are too
function Model.DayLabel(Offset: number, Now: number): string
	if Offset == 0 then return "Today" end
	if Offset == 1 then return "Yesterday" end
	return os.date("!%a %d", (Records.Day(Now) - Offset) * 86400)
end

function Model.LogHead(E: any, Clock: ((number) -> string)?): string
	local Fmt = Clock or function(T: number): string return os.date("%H:%M", T) end
	return `{Fmt(E.At)} · {E.Staff} · {E.Action}{if E.Target then " · " .. E.Target else ""}`
end

return Model
