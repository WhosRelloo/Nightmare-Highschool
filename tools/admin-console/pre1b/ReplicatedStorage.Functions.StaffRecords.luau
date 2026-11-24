--[[
	StaffRecords (shared, pure): the rules for the console's saved records, the saved staff log and saved favourites
	(spec docs/superpowers/specs/2026-11-23-admin-console-1b-design.md §2-§4). No services, no state. The server
	(Features.StaffRecords, Features.Admin) and the client (StaffConsole.Model) use it; checks/records_rules.lua tests it.
	Record lists are oldest first. By is a staff UserId; At and Until are os.time(); Until = 0 means until unmuted;
	Days = 0 means permanent; Lifted = { By, At }.
]]
local R = {}

R.CAP = 50
R.LOG_CAP = 2000
R.DETAIL_MAX = 120
R.FAVS_MAX = 40
R.LISTS = { "Notes", "Warnings", "Bans", "Mutes" }
R.KIND = { Notes = "Note", Warnings = "Warn", Bans = "Ban", Mutes = "Mute" }
R.MUTE_CHOICES = { 10, 60, 1440, 0 }
R.MUTE_LABELS = { "10 min", "1 h", "1 day", "Until unmuted" }
local SIDES = { Moderate = true, Test = true }

local function plural(N: number, Word: string): string
	return `{N} {Word}{if N == 1 then "" else "s"}`
end

function R.Blank(): any
	return { Notes = {}, Warnings = {}, Bans = {}, Mutes = {}, Reports = {} }
end

-- a stored value (or nil) as a record with every list; entries that aren't tables with a number At are dropped
function R.Normalize(V: any): any
	local Out = R.Blank()
	if typeof(V) ~= "table" then return Out end
	for _, Name in R.LISTS do
		local L = V[Name]
		if typeof(L) ~= "table" then continue end
		for _, E in L do
			if typeof(E) == "table" and typeof(E.At) == "number" then table.insert(Out[Name], E) end
		end
	end
	if typeof(V.Reports) == "table" then Out.Reports = V.Reports end
	return Out
end

-- the newest goes on the end; the oldest drop off past CAP
function R.Push(Rec: any, List: string, Entry: any): any
	local L = Rec[List]
	table.insert(L, Entry)
	while #L > R.CAP do table.remove(L, 1) end
	return Rec
end

function R.MuteUntil(Minutes: number, Now: number): number
	if Minutes == 0 then return 0 end
	return Now + Minutes * 60
end

function R.MuteOn(M: any, Now: number): boolean
	if typeof(M) ~= "table" or M.Lifted then return false end
	return M.Until == 0 or (typeof(M.Until) == "number" and M.Until > Now)
end

function R.OpenMute(Rec: any, Now: number): any
	for I = #Rec.Mutes, 1, -1 do
		if R.MuteOn(Rec.Mutes[I], Now) then return Rec.Mutes[I] end
	end
	return nil
end

function R.MuteLabel(M: any): string
	if M.Until == 0 then return R.MUTE_LABELS[4] end
	local Min = math.floor(((M.Until or 0) - (M.At or 0)) / 60 + 0.5)
	local I = table.find(R.MUTE_CHOICES, Min)
	return if I then R.MUTE_LABELS[I] else `{Min} min`
end

function R.BanOn(B: any, Now: number): boolean
	if typeof(B) ~= "table" or B.Lifted then return false end
	local D = tonumber(B.Days) or 0
	return D == 0 or (B.At or 0) + D * 86400 > Now
end

-- the latest ban nobody has lifted (it may have ended on time: lifting it is still allowed, and harmless)
function R.OpenBan(Rec: any): any
	for I = #Rec.Bans, 1, -1 do
		if not Rec.Bans[I].Lifted then return Rec.Bans[I] end
	end
	return nil
end

-- the staff level that may lift a ban: permanent 3, over 30 days 2, else 1; no ban on record (set before 1b) is permanent
function R.UnbanLevel(Ban: any): number
	if typeof(Ban) ~= "table" then return 3 end
	local D = tonumber(Ban.Days) or 0
	if D == 0 then return 3 end
	if D > 30 then return 2 end
	return 1
end

function R.Find(Rec: any, List: string, At: number, By: number): number?
	for I, E in Rec[List] or {} do
		if E.At == At and E.By == By then return I end
	end
	return nil
end

function R.Remove(Rec: any, List: string, At: number, By: number): any
	local I = R.Find(Rec, List, At, By)
	if not I then return nil end
	return table.remove(Rec[List], I)
end

function R.EntryText(List: string, E: any): string
	local Why = if typeof(E.Reason) == "string" and E.Reason ~= "" then ": " .. E.Reason else ""
	if List == "Notes" then return tostring(E.Text or "") end
	if List == "Warnings" then return if Why ~= "" then E.Reason else "Warned" end
	if List == "Bans" then return (if (tonumber(E.Days) or 0) == 0 then "Permanent ban" else `{E.Days}-day ban`) .. Why end
	if List == "Mutes" then return `Muted ({R.MuteLabel(E)})` .. Why end
	return ""
end

-- "3 warnings · 1 note · 1 ban (lifted) · muted until 14:20"; Clock formats Until (default: local HH:MM today,
-- else with the day, so a 1-day mute doesn't read as already over)
function R.Summary(Rec: any, Now: number, Clock: ((number) -> string)?): string
	local Fmt = Clock or function(T: number): string
		return os.date(if os.date("%Y%m%d", T) == os.date("%Y%m%d", Now) then "%H:%M" else "%a %d %b %H:%M", T)
	end
	local Parts = {}
	if #Rec.Warnings > 0 then table.insert(Parts, plural(#Rec.Warnings, "warning")) end
	if #Rec.Notes > 0 then table.insert(Parts, plural(#Rec.Notes, "note")) end
	if #Rec.Bans > 0 then
		local Any, AllLifted = false, true
		for _, Bn in Rec.Bans do
			if R.BanOn(Bn, Now) then Any = true end
			if not Bn.Lifted then AllLifted = false end
		end
		table.insert(Parts, plural(#Rec.Bans, "ban") .. (if Any then " (active)" elseif AllLifted then " (lifted)" else " (ended)"))
	end
	local M = R.OpenMute(Rec, Now)
	if M then table.insert(Parts, if M.Until == 0 then "muted until unmuted" else "muted until " .. Fmt(M.Until)) end
	return if #Parts > 0 then table.concat(Parts, " · ") else "No history"
end

-- every entry, newest first: { List, Kind, Entry, Seq }
function R.Timeline(Rec: any): any
	local Out = {}
	for _, List in R.LISTS do
		for I, E in Rec[List] do table.insert(Out, { List = List; Kind = R.KIND[List]; Entry = E; Seq = I }) end
	end
	table.sort(Out, function(A, B)
		if A.Entry.At ~= B.Entry.At then return A.Entry.At > B.Entry.At end
		if A.List ~= B.List then return A.List < B.List end
		return A.Seq > B.Seq
	end)
	return Out
end

---------------------------------------------------------------- the saved log
function R.Day(Now: number): number return Now // 86400 end
function R.LogKey(Day: number, Job: string, Test: boolean?): string return `{if Test then "test_" else ""}day_{Day}_{Job}` end
function R.IndexKey(Day: number, Test: boolean?): string return `{if Test then "test_" else ""}day_{Day}` end
function R.TestCutoff(Day: number): number return Day - 7 end

function R.LogEntry(F: any): any
	return {
		At = tonumber(F.At) or 0; Staff = string.sub(tostring(F.Staff or "?"), 1, 40); StaffId = tonumber(F.StaffId) or 0;
		Action = string.sub(tostring(F.Action or "?"), 1, 40);
		Target = if F.Target ~= nil then string.sub(tostring(F.Target), 1, 40) else nil; TargetId = tonumber(F.TargetId);
		Detail = string.sub(tostring(F.Detail or ""), 1, R.DETAIL_MAX);
		Side = if F.Side == "Test" then "Test" else "Moderate"; Ok = F.Ok == true;
	}
end

function R.CapLog(L: { any }): { any }
	local N = #L
	if N <= R.LOG_CAP then return L end
	return table.move(L, N - R.LOG_CAP + 1, N, 1, {})
end

-- Lists: each oldest first (a server's key, or this server's unsaved buffer last). Newest first out; a tie in the
-- same second keeps the later list's and later position's entry first
function R.MergeDay(Lists: { { any } }): { any }
	local All = {}
	for LI, L in Lists do
		for I, E in L do table.insert(All, { E = E; K = LI * 1e6 + I }) end
	end
	table.sort(All, function(A, B)
		if A.E.At ~= B.E.At then return A.E.At > B.E.At end
		return A.K > B.K
	end)
	local Out = table.create(#All)
	for I, X in All do Out[I] = X.E end
	return Out
end

-- Chip: "All" | "Moderate" | "Test" | "Refused"; Query: staff name, target name or UserId, or action
function R.LogMatch(E: any, Query: string?, Chip: string?): boolean
	if Chip == "Moderate" and E.Side ~= "Moderate" then return false end
	if Chip == "Test" and E.Side ~= "Test" then return false end
	if Chip == "Refused" and E.Ok then return false end
	local Q = string.lower(string.match(Query or "", "^%s*(.-)%s*$") or "")
	if Q == "" then return true end
	for _, Field in { E.Staff, E.Target, E.Action, if E.TargetId then tostring(E.TargetId) else nil } do
		if typeof(Field) == "string" and string.find(string.lower(Field), Q, 1, true) then return true end
	end
	return false
end

function R.Page(Rows: { any }, Page: any, Per: number): ({ any }, number, number)
	local Pages = math.max(1, math.ceil(#Rows / Per))
	local P = math.clamp(math.floor(tonumber(Page) or 1), 1, Pages)
	local Out = {}
	for I = (P - 1) * Per + 1, math.min(#Rows, P * Per) do table.insert(Out, Rows[I]) end
	return Out, P, Pages
end

---------------------------------------------------------------- saved favourites
-- strings only, no repeats, at most FAVS_MAX; with Known, only ids in it (the client drops ids no longer in the registry)
function R.CleanFavs(Favs: any, Known: any): { string }
	local Out, Seen = {}, {}
	if typeof(Favs) ~= "table" then return Out end
	for _, Id in Favs do
		if typeof(Id) == "string" and #Id <= 40 and not Seen[Id] and (Known == nil or Known[Id]) then
			Seen[Id] = true
			table.insert(Out, Id)
			if #Out >= R.FAVS_MAX then break end
		end
	end
	return Out
end

function R.CleanSide(Side: any): string?
	return if typeof(Side) == "string" and SIDES[Side] then Side else nil
end

return R
