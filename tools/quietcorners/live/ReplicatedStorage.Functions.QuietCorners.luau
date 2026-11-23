--!strict
--[[ (2.38) Quiet Corners: the pure rules (spec docs/superpowers/specs/2026-11-21-quiet-corners-ui-design.md).
	No services, no instances (Vector2 only). Read by Controllers.Gui.{HudState, Notifications, PromptUi, Compass, Dialogue,
	EvidenceWall, QuestJournal}. Tested by tools/quietcorners/checks/qc_pure.lua in the Edit VM. ]]
local QC = {}

QC.MIN_TEXT = 20
QC.RACES = { "Human", "Priest", "Vampire", "Werewolf", "Ghoul", "Wraith" }
QC.CLIQUES = { "Vigil", "Court", "Athletes", "Delinquents", "Pack", "Ordinary", "Choir", "Ink" }
QC.FACTION_CLIQUE = { Vigil = "Vigil", CrimsonCourt = "Court" } :: { [string]: string }
QC.TONES = { Kind = true, Sly = true, Threat = true, Ask = true } :: { [string]: boolean }
QC.GHOST = 0.65      -- Ghost: 35% visible
QC.FOCUS = 0.65      -- combat: the top-left and the compass at 35%
QC.CALM_AFTER = 6
QC.COMBAT_FOR = 4
QC.WAKE_FOR = 4
QC.FLIP = { Frame = 256, Cols = 4, Frames = 16, Fps = 15 }

local function valid(List: { string }, V: any): boolean return typeof(V) == "string" and table.find(List, V) ~= nil end
local function asset(Id: any): string? return if typeof(Id) == "number" and Id > 0 then "rbxassetid://" .. Id else nil end

function QC.Race(R: any): string return if valid(QC.RACES, R) then R else "Human" end

-- Art[Piece] is an id (a shared piece) or { [Race] = id }; a missing race falls back to Human; nil = the kit fallback
function QC.Image(Art: any, Piece: string, Race: any?): string?
	local V = Art and Art[Piece]
	if typeof(V) == "table" then return asset(V[QC.Race(Race)]) or asset(V.Human) end
	return asset(V)
end

function QC.CliqueOf(Npc: any): string?
	if typeof(Npc) ~= "table" then return nil end
	if valid(QC.CLIQUES, Npc.Clique) then return Npc.Clique end
	return QC.FACTION_CLIQUE[Npc.Faction or ""]
end

-- the speaker's crest: never empty and never the school Seal; no clique (staff, townsfolk, new students) = Unaffiliated
function QC.Crest(Art: any, Clique: any, Flip: boolean?): string?
	local Set = Art and Art[if Flip then "CrestFlip" else "Crest"]
	if typeof(Set) ~= "table" then return nil end
	return asset(Set[if valid(QC.CLIQUES, Clique) then Clique else "Unaffiliated"]) or asset(Set.Unaffiliated)
end

function QC.FlipOffset(I: number): Vector2
	local N = math.clamp(math.floor(I), 0, QC.FLIP.Frames - 1)
	return Vector2.new((N % QC.FLIP.Cols) * QC.FLIP.Frame, (N // QC.FLIP.Cols) * QC.FLIP.Frame)
end

function QC.Mode(M: any): string return if M == "Always" or M == "Vanish" then M else "Ghost" end

function QC.State(I: any): string
	if I.Cut then return "Cut" end
	if I.Menu then return "Menu" end
	if I.Dialogue then return "Dialogue" end
	if I.Lesson then return "Lesson" end
	if (I.CombatUntil or 0) > I.Now then return "Combat" end
	if I.Now - (I.LastActive or -math.huge) >= QC.CALM_AFTER then return "Calm" end
	return "Active"
end

-- a cluster ("TopLeft", "Compass", "Vitals"): its GroupTransparency. Awake = it changed, was hovered, or Tab/View peeked.
function QC.HudTarget(State: string, Mode: string, Cluster: string, Awake: boolean?): number
	if State == "Cut" or State == "Dialogue" or State == "Menu" then return 1 end
	if State == "Lesson" then return if Cluster == "TopLeft" then 0 else 1 end
	if State == "Combat" then return if Cluster == "Vitals" or Awake then 0 else QC.FOCUS end
	if State == "Calm" and not Awake then
		if Mode == "Always" then return 0 end
		if Mode == "Vanish" then return 1 end
		return QC.GHOST
	end
	return 0
end

function QC.SlipsQueued(State: string): boolean return State ~= "Active" and State ~= "Calm" end
function QC.Danger(Kind: any): boolean return Kind == "Bad" end
function QC.MaxSlips(Phone: boolean): number return if Phone then 2 else 3 end
function QC.Waiting(N: number): string return if N > 0 then N .. " waiting" else "" end

function QC.SlipOpen(Data: any): string?
	if typeof(Data) ~= "table" then return nil end
	if Data.Open == "Texts" or Data.Open == "Evidence" or Data.Open == "Journal" then return Data.Open end
	if Data.Open ~= nil then return nil end
	local T = tostring(Data.Title or "")
	if T:find("^Text from") then return "Texts" end
	if T == "New insight" or T == "Case breakthrough" or T:find("^Clue") then return "Evidence" end
	if T:find("^Quest") or T:find("^Objective") then return "Journal" end
	return nil
end

-- shorten at a word with "…" until Fits says yes (Fits measures with TextService on the client)
function QC.Ellipsize(Text: string, Fits: (string) -> boolean): string
	if Fits(Text) then return Text end
	local Words = string.split(Text, " ")
	while #Words > 1 do
		table.remove(Words)
		local T = table.concat(Words, " ") .. "…"
		if Fits(T) then return T end
	end
	return "…"
end

function QC.Nearest(Dists: { [any]: number }): any?
	local Best, D = nil, math.huge
	for K, V in Dists do if V < D then Best, D = K, V end end
	return Best
end
function QC.KeySize(Key: string): number return if (utf8.len(Key) or #Key) == 1 then 22 else 20 end
-- PromptTag's text box is 0.11 .. 0.90 of its width (measured from the art); the tag is a 9-slice, 320 to 520 wide
function QC.TagWidth(TextW: number): number return math.clamp(math.ceil((TextW + 8) / 0.79), 320, 520) end
function QC.Phone(Vp: Vector2): boolean return math.min(Vp.X, Vp.Y) < 600 end

function QC.Tone(T: any): string? return if typeof(T) == "string" and QC.TONES[T] then T else nil end

-- the card's second line: drop the relation first, then the clique, until it fits
function QC.CardSub(Clique: string?, Role: string?, Relation: string?, Fits: (string) -> boolean): string
	local function join(...) local P = {} for I = 1, select("#", ...) do local S = select(I, ...) if S and S ~= "" then table.insert(P, S) end end return table.concat(P, " · ") end
	for _, T in { join(Clique, Role, Relation), join(Clique, Role), join(Role, Relation), join(Role), join(Clique) } do
		if T ~= "" and Fits(T) then return T end
	end
	return join(Role) ~= "" and join(Role) or join(Clique)
end

-- the Evidence Wall's model for one case. Saved = Quests.Cases[CaseId] ({ Clues, Insights, Solved, SolvedText }); Pins = client-only
function QC.Wall(Case: any, Saved: any, Pins: any)
	Saved = Saved or {}
	Pins = Pins or {}
	local Found = Saved.Clues or {}
	local Insight = {}
	for _, I in Saved.Insights or {} do if I.Id then Insight[I.Id] = I end end
	local Clues, NFound, NTotal = {}, 0, 0
	for Id, C in Case.Clues or {} do
		local Has = Found[Id] ~= nil and Found[Id] ~= false
		if C.Hidden and not Has then continue end
		NTotal += 1
		if Has then NFound += 1 end
		local Kind = if C.Kind == "Photo" and not C.Photo then "Object"
			elseif C.Kind == "Note" or C.Kind == "Record" or C.Kind == "Object" or C.Kind == "Photo" then C.Kind else "Note"
		table.insert(Clues, { Id = Id; Name = C.Name; Where = C.Where; Text = C.Text; Kind = Kind; Photo = C.Photo; Found = Has; Order = C.Order or 99 })
	end
	table.sort(Clues, function(A, B)
		if A.Found ~= B.Found then return A.Found end
		if A.Order ~= B.Order then return A.Order < B.Order end
		return A.Id < B.Id
	end)
	local Questions, NAns, NNeed = {}, 0, 0
	for _, Q in Case.Questions or {} do
		local I = Insight[Q.Id]
		local Row = Pins[Q.Id] or {}
		local N = (if Row[1] then 1 else 0) + (if Row[2] then 1 else 0)
		if not Q.Bonus then
			NNeed += 1
			if I then NAns += 1 end
		end
		table.insert(Questions, { Id = Q.Id; Ask = Q.Ask; Hint = Q.Hint; Bonus = Q.Bonus == true;
			State = if I then "Answered" elseif N == 2 then "Full" elseif N == 1 then "Half" else "Empty";
			Insight = I and I.Text; A = (I and I.A) or Row[1]; B = (I and I.B) or Row[2] })
	end
	return { Clues = Clues; Questions = Questions; Found = NFound; Total = NTotal; Answered = NAns; Needed = NNeed;
		Ready = NNeed > 0 and NAns >= NNeed; Solved = Saved.Solved == true; SolvedText = Saved.SolvedText;
		Progress = ("Clues %d of %d · Answered %d of %d"):format(NFound, NTotal, NAns, NNeed) }
end

-- pin a clue in a question's slot (1 or 2); returns the new pins and, once both slots hold different clues, the pair to send
function QC.Pin(Pins: any, Q: string, Slot: number, Clue: string)
	local P = table.clone(Pins or {})
	local Row = table.clone(P[Q] or {})
	if Row[3 - Slot] == Clue then Row[3 - Slot] = nil end
	Row[Slot] = Clue
	P[Q] = Row
	if Row[1] and Row[2] then return P, { Question = Q; A = Row[1]; B = Row[2] } end
	return P, nil
end
function QC.Unpin(Pins: any, Q: string) local P = table.clone(Pins or {}) P[Q] = nil return P end
function QC.Miss(M: any, Q: string) local C = table.clone(M or {}) C[Q] = (C[Q] or 0) + 1 return C end
function QC.ShowHint(M: any, Q: string): boolean return ((M or {})[Q] or 0) >= 2 end

return QC
