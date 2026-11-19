--[[
	Report cards (server). Services.School.ReportCards   (1.40)

	Each save slot keeps a tally of its school week (the same week as Social.Superlatives: five event days, Monday 6 AM
	to Monday 6 AM) in PlayerData.Social.Reports.Week:
	  Subjects  [subject] = { Sum, N (graded lessons, F=0 .. A+=5), Seen (classes attended) }   (School.Attendance)
	  Status    Present / Tardy / LeftEarly / Absent counts (Excused isn't counted)
	  Violations, Detentions                                                                  (School.Discipline)
	When the week ends (Monday 6 AM, or at the next login if you were away) the week becomes a report card in
	Social.Reports.Cards (newest first, the last 4): each subject's average letter, attendance, conduct, a comment from
	Mr. Hale, your homeroom teacher (by how you did, with a race joke now and then), and an allowance paid once:
	A / A+ 60, B 40, C 20, D / F 0; +20 for perfect attendance (5+ classes, none missed, late or left); halved after a
	detention. (Homes, 1.64) Mom & Dad add 20 to an A card, and an F or a second D in a row cuts it off until a C or better. A text from the Office says it's in. A week with no classes and no marks sends no card.
	The phone's Report Card app (Gui.Phone) reads Shared.List(P) through NHPhone.Reports.

	API: Class(P, Subject, Status, Grade?), Violation(P), Detention(P), List(P), Unread(P).
	Tests: DeliverForTests(P) (sends this week's tally now), State(P).
]]
local Players = game:GetService(`Players`)
local ServerScriptService = game:GetService(`ServerScriptService`)

local Shared = {}
local Local = {}

local LETTERS = { [0] = `F`, `D`, `C`, `B`, `A`, `A+` }
local VALUE = { F = 0; D = 1; C = 2; B = 3; A = 4; [`A+`] = 5 }
local KEEP = 4
local ALLOWANCE = { [`A+`] = 60; A = 60; B = 40; C = 20; D = 0; F = 0 }
local PERFECT_BONUS = 20
local TEACHER = `Mr. Hale, Homeroom`

local COMMENTS = {
	Top = {
		`A pleasure to teach. Whatever you're doing after dark, keep it up.`,
		`Top marks. The staff room has started to talk about you. Mostly kindly.`,
		`Exemplary work. I've moved you to the front row, away from the windows.`,
	};
	Good = {
		`Solid work this week. A little more focus and you'll be at the top.`,
		`Shows real promise. Please stop doodling sigils in the margins.`,
		`Good effort. Your homework arrived on time, which in this building is rare.`,
	};
	Fair = {
		`Average. Not bad, not good. Like the cafeteria.`,
		`Capable of more. I've seen you outrun a hall monitor; apply that to algebra.`,
		`Passing, just. The library is open until dark. Please use it.`,
	};
	Poor = {
		`We need to talk. My office, Monday, before the bell.`,
		`Your grades are in freefall. So, apparently, is your attendance.`,
		`I am told you were "busy". Busy is not a subject.`,
	};
	None = {
		`I barely saw you in class this week. I'd like to see more of you.`,
	};
}
local RACE = {
	Vampire = `Shows promise. Stop biting classmates.`;
	Wraith = `Please stop walking through the walls during tests.`;
	Werewolf = `Lovely work, but the scratch marks on the desk are coming out of your allowance.`;
	Ghoul = `Bright mind. Lunch is for food, not for "tasting" the biology specimens.`;
	Priest = `Diligent as ever. The chapel can spare you for one more period of maths.`;
	Human = `Hard-working and, refreshingly, alive. Keep it that way.`;
}
local CONDUCT = {
	Detention = ` I've also seen your name on the detention list. Again.`;
	Warnings = ` Watch your conduct: the Office has started a file.`;
}

local function svc(Path: string)
	local Node = ServerScriptService.Services
	for Part in Path:gmatch(`[^%.]+`) do Node = Node:FindFirstChild(Part) if not Node then return nil end end
	local Ok, Mod = pcall(require, Node)
	return Ok and Mod or nil
end

function Local.Week(): number?
	local Sup = svc(`Social.Superlatives`)
	return Sup and Sup.Week and Sup.Week() or nil
end

-- Social.Reports, with this week's tally (a finished week is turned into a card first)
function Local.Data(P: Player)
	local Rep = svc(`Social.Reputation`)
	local Social = Rep and Rep.Get(P)
	if not Social then return nil end
	local R = Social.Reports
	if typeof(R) ~= `table` then R = {} Social.Reports = R end
	R.Cards = if typeof(R.Cards) == `table` then R.Cards else {}
	return R, Rep
end

function Local.Fresh(W: number)
	return { Week = W; Subjects = {}; Status = {}; Violations = 0; Detentions = 0 }
end

function Local.Tally(P: Player)
	local R, Rep = Local.Data(P)
	local W = Local.Week()
	if not (R and W) then return nil end
	if typeof(R.Week) ~= `table` or typeof(R.Week.Week) ~= `number` then
		R.Week = Local.Fresh(W)
	elseif R.Week.Week < W then
		Local.Deliver(P, R, W)
	end
	return R.Week, R, Rep
end

---| counting |---

function Shared.Class(P: Player, Subject: string?, Status: string?, Grade: string?)
	if Status == `Excused` or typeof(Status) ~= `string` then return end
	local T, _, Rep = Local.Tally(P)
	if not T then return end
	T.Status[Status] = (T.Status[Status] or 0) + 1
	local S = typeof(Subject) == `string` and Subject ~= `` and Subject or `Homeroom`
	local Row = T.Subjects[S]
	if typeof(Row) ~= `table` then Row = { Sum = 0; N = 0; Seen = 0 } T.Subjects[S] = Row end
	if Status ~= `Absent` then Row.Seen += 1 end
	local V = Grade and VALUE[Grade]
	if V and Status ~= `Absent` then Row.Sum += V Row.N += 1 end
	Rep.Sync(P)
end

function Shared.Violation(P: Player)
	local T, _, Rep = Local.Tally(P)
	if not T then return end
	T.Violations += 1
	Rep.Sync(P)
end

function Shared.Detention(P: Player)
	local T, _, Rep = Local.Tally(P)
	if not T then return end
	T.Detentions += 1
	Rep.Sync(P)
end

---| the card |---

function Local.Letter(V: number): string
	return LETTERS[math.clamp(math.floor(V + 0.5), 0, 5)]
end

function Local.Comment(P: Player, Avg: string?, T, Seed: number): string
	local Tier = if not Avg then `None` elseif VALUE[Avg] >= 4 then `Top` elseif VALUE[Avg] >= 3 then `Good` elseif VALUE[Avg] >= 2 then `Fair` else `Poor`
	local Race = P:GetAttribute(`Race`)
	local Pick
	-- a race joke about one week in three (never on a poor week, where it would sting)
	if RACE[Race] and Tier ~= `Poor` and Tier ~= `None` and Seed % 3 == 0 then
		Pick = RACE[Race]
	else
		local Pool = COMMENTS[Tier]
		Pick = Pool[Seed % #Pool + 1]
	end
	if T.Detentions > 0 then Pick ..= CONDUCT.Detention elseif T.Violations >= 2 then Pick ..= CONDUCT.Warnings end
	return Pick
end

function Local.Build(P: Player, T)
	local Subjects, Sum, N = {}, 0, 0
	for Name, Row in T.Subjects do
		local G = if Row.N > 0 then Local.Letter(Row.Sum / Row.N) elseif Row.Seen > 0 then `Attended` else `Absent`
		table.insert(Subjects, { Name = Name; Grade = G; Lessons = Row.N; Seen = Row.Seen })
		Sum += Row.Sum
		N += Row.N
	end
	table.sort(Subjects, function(A, B) return A.Name < B.Name end)
	local St = T.Status
	local Attended = (St.Present or 0) + (St.Tardy or 0) + (St.LeftEarly or 0)
	local Total = Attended + (St.Absent or 0)
	if Total == 0 and T.Violations == 0 and T.Detentions == 0 then return nil end
	local Avg = if N > 0 then Local.Letter(Sum / N) else nil
	local Perfect = Total >= 5 and (St.Absent or 0) == 0 and (St.Tardy or 0) == 0 and (St.LeftEarly or 0) == 0
	local Allowance = (Avg and ALLOWANCE[Avg] or 0) + (if Perfect then PERFECT_BONUS else 0)
	if T.Detentions > 0 then Allowance = math.floor(Allowance / 2) end
	local Streak = 0
	pcall(function() local Prof = svc(`Player.Data`).GetProfile(P) Streak = Prof.Attendance and Prof.Attendance.Streak or 0 end)
	local Conduct = if T.Detentions > 0 then `Detention` elseif T.Violations > 0 then `{T.Violations} warning{if T.Violations == 1 then `` else `s`}` else `Clear`
	return {
		Week = T.Week; Subjects = Subjects; Average = Avg;
		Attendance = { Attended = Attended; Total = Total; Tardy = St.Tardy or 0; Absent = St.Absent or 0; LeftEarly = St.LeftEarly or 0; Perfect = Perfect; Streak = Streak };
		Conduct = Conduct; Violations = T.Violations; Detentions = T.Detentions;
		Comment = Local.Comment(P, Avg, T, T.Week + P.UserId); Teacher = TEACHER;
		Allowance = Allowance; Read = false;
	}
end

-- turn the finished week into a card, pay the allowance once, text the student, start week W
function Local.Deliver(P: Player, R, W: number)
	local T = R.Week
	R.Week = Local.Fresh(W)
	local Card = typeof(T) == `table` and Local.Build(P, T) or nil
	if not Card then return nil end
	table.insert(R.Cards, 1, Card)
	while #R.Cards > KEEP do table.remove(R.Cards) end
	-- (homes) Mom & Dad: an A adds a bonus, an F or a second D in a row cuts the allowance off (Features.Homes)
	local Homes = svc(`Features.Homes`)
	if Homes and Homes.Adjust then pcall(Homes.Adjust, P, Card) end
	local Data = svc(`Player.Data`)
	if Data and Card.Allowance > 0 then Data.UpdateState(P, { type = `UpdateYen`; amount = Card.Allowance }) end
	local Phone = svc(`Features.Phone`)
	local Body = `Your report card is in: {if Card.Average then `a {Card.Average} average` else `no graded lessons`}, {Card.Attendance.Attended} of {Card.Attendance.Total} classes`
		.. (if Card.Allowance > 0 then `. Allowance: \u{A5}{Card.Allowance}.` else `.`) .. ` Open Report Card on your phone.`
	if Phone and Phone.AddText then pcall(Phone.AddText, P, { From = `The Office`; Body = Body }, true) end
	-- (homes) then Mom & Dad's text, and the room changes to match the card
	if Homes and Homes.AfterCard then pcall(Homes.AfterCard, P, Card) end
	local N = svc(`Features.Notifications`)
	if N then pcall(N.Notify, P, { Title = `Your report card is in`; Text = if Card.Average then `{Card.Average} average` .. (if Card.Allowance > 0 then `, \u{A5}{Card.Allowance} allowance` else ``) else `Open Report Card on your phone`; Kind = `Milestone`; Duration = 7 }) end
	local Rep = svc(`Social.Reputation`)
	if Rep then Rep.Sync(P) end
	return Card
end

---| the phone |---

-- the cards (newest first) and this week so far; marks the newest card read
function Shared.List(P: Player)
	local T, R, Rep = Local.Tally(P)
	if not R then return nil end
	local Cards = R.Cards
	local WasUnread = Cards[1] and Cards[1].Read == false
	if WasUnread then Cards[1].Read = true Rep.Sync(P) end
	local Sum, N = 0, 0
	for _, Row in (T and T.Subjects) or {} do Sum += Row.Sum N += Row.N end
	local St = (T and T.Status) or {}
	local Att = (St.Present or 0) + (St.Tardy or 0) + (St.LeftEarly or 0)
	local Identity = svc(`Player.Identity`)
	local Name = ``
	pcall(function() Name = Identity.FullName(Identity.Get(P)) end)
	return { Cards = Cards; Week = Local.Week(); New = WasUnread; Student = Name; Race = P:GetAttribute(`Race`);
		SoFar = { Average = if N > 0 then Local.Letter(Sum / N) else nil; Attended = Att; Total = Att + (St.Absent or 0); Lessons = N } }
end

function Shared.Unread(P: Player): boolean
	local R = Local.Data(P)
	return R ~= nil and R.Cards[1] ~= nil and R.Cards[1].Read == false
end

---| tests |---

function Shared.DeliverForTests(P: Player)
	local R = Local.Data(P)
	local W = Local.Week()
	if not (R and W) then return nil end
	if typeof(R.Week) ~= `table` then return nil end
	return Local.Deliver(P, R, W)
end
function Shared.State(P: Player)
	local R = Local.Data(P)
	return R and { Week = R.Week; Cards = R.Cards } or nil
end

---| start |---

function Shared.OnStart()
	local Data = svc(`Player.Data`)
	if Data and Data.ProfileLoaded then
		Data.ProfileLoaded:Connect(function(P) task.delay(3, function() if P.Parent then pcall(Local.Tally, P) end end) end)
	end
	-- the Monday hand-out: every 15 s, anyone whose tally belongs to a finished week gets their card
	task.spawn(function()
		while true do
			task.wait(15)
			for _, P in Players:GetPlayers() do pcall(Local.Tally, P) end
		end
	end)
end

return Shared
