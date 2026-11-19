--[[
	Phone (server). Services.Features.Phone   (the client is Controllers.Gui.Phone; Y opens it)
	  Wallet      send Yen to another student in the server. 1 to 5,000 at a time, 5 s apart, never more than you
	              have; both of you get a toast and a line in your history (PlayerData.Phone.History, last 15).
	              You can't send from the main menu, while downed, or to yourself.
	  Night FM    your recent audio IDs are saved (PlayerData.Phone.Recent, last 10). Playback is client-only:
	              only you hear it.
	  Gazette     "The Midnight Bell", the school paper, written from the live game: the moon and the night,
	              the top students in the building, the discipline report, today's specials at the stand, club
	              notices, and a rumour column. Names appear only if the reader knows the student (Strangers rule).
	  Contacts    every other student in the server: known ones by name, the rest as "a stranger".
	  Style       your phone's wallpaper: a preset or your own image / decal id (PlayerData.Phone.Wallpaper)
	  Texts       (1.33) messages from people at school: clique leaders' daily dares (Accept starts the quest), rumble
	              warnings. Saved per slot in PlayerData.Phone.Texts (newest first, Config.Cliques.Events.TextsKept);
	              PlayerData.Phone.DareDay is the event day the morning dares were last sent (Social.CliqueEvents).
	The handset  every character spawns with a "Phone" Tool in their backpack (it sits on the hotbar), built from the
	              owner's model ServerStorage.NHPhoneModel: welded to an invisible handle, the crest glowing on its
	              screen. Equipping it opens the phone UI (Controllers.Gui.Phone); Y takes it out / puts it away.
	Remotes ReplicatedStorage.NHPhone (Ready): Get (RF) -> state, Send (RF userId, amount), Gazette (RF),
	  Contacts (RF), SaveRecent (RF { id }), SaveWallpaper (RF { Preset, Image? }), Changed (RE) -> state,
	  Texts (RF markRead?) -> list, TextAction (RF index, "Accept" | "Decline") -> ok, message
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

local Data = require(ServerScriptService.Services.Player.Data)
local SchoolTime = require(game:GetService("ReplicatedStorage"):WaitForChild("Functions"):WaitForChild("SchoolTime")) -- (2.22.0) shared night windows
local Identity = require(ServerScriptService.Services.Player.Identity)
local Notifications = require(ServerScriptService.Services.Features.Notifications)

local MAX_SEND = 5000
local SEND_GAP = 5
local HISTORY = 15
local RECENT = 10

local Shared = {}
local Local = {}
local Remotes = nil
local LastSend = {} :: { [Player]: number }
local LastCall = {} :: { [Player]: number }

---| data |---

function Shared.Sanitize(Raw)
	local Out = { History = {}; Recent = {}; Wallpaper = { Preset = `CrimsonInk` }; Texts = {}; Liked = {}; Broadcast = 0 } -- (2.30) Liked, Broadcast
	if typeof(Raw) ~= `table` then return Out end
	-- (1.33) texts: { From, Body, At, Day, Dare?, State = New | Read | Accepted | Declined }
	local Kept = 30
	pcall(function() Kept = require(ReplicatedStorage.Config.Cliques).Events.TextsKept or 30 end)
	for _, T in (typeof(Raw.Texts) == `table` and Raw.Texts) or {} do
		if typeof(T) == `table` and typeof(T.Body) == `string` and #Out.Texts < Kept then
			local St = if T.State == `Read` or T.State == `Accepted` or T.State == `Declined` then T.State else `New`
			table.insert(Out.Texts, {
				From = tostring(T.From or ``):sub(1, 40); Body = T.Body:sub(1, 300); At = tostring(T.At or ``):sub(1, 30);
				Day = if typeof(T.Day) == `number` then math.floor(T.Day) else 0;
				Dare = if typeof(T.Dare) == `string` and #T.Dare <= 40 then T.Dare else nil; State = St;
				-- (homes) a dorm-room invite: the host's UserId (Accept = visit, Features.Homes)
				Invite = if typeof(T.Invite) == `number` and T.Invite == T.Invite then math.floor(T.Invite) else nil;
				-- (audit) a stable id: TextAction matches on it (the list index shifts when a new text arrives)
				Id = if typeof(T.Id) == `number` and T.Id == T.Id then math.floor(T.Id) else nil;
			})
		end
	end
	if typeof(Raw.DareDay) == `number` then Out.DareDay = math.floor(Raw.DareDay) end
	-- wallpaper (Style app): a preset id, and optionally your own image / decal id
	if typeof(Raw.Wallpaper) == `table` then
		local P = Raw.Wallpaper.Preset
		if typeof(P) == `string` and #P <= 24 and P:match(`^%w+$`) then Out.Wallpaper.Preset = P end
		local I = tonumber(Raw.Wallpaper.Image)
		if I and I > 0 and I % 1 == 0 and I < 1e15 then Out.Wallpaper.Image = I end
	end
	for _, H in (typeof(Raw.History) == `table` and Raw.History) or {} do
		if typeof(H) == `table` and typeof(H.Amount) == `number` and #Out.History < HISTORY then
			-- (audit) Seq rises by one per row, so the phone's wallet badge can tell new rows from seen ones
			table.insert(Out.History, { Dir = if H.Dir == `In` then `In` else `Out`; Amount = math.floor(H.Amount); Who = tostring(H.Who or ``):sub(1, 40); At = tostring(H.At or ``):sub(1, 30);
				Seq = if typeof(H.Seq) == `number` and H.Seq == H.Seq then math.floor(H.Seq) else nil })
		end
	end
	for _, Id in (typeof(Raw.Recent) == `table` and Raw.Recent) or {} do
		local N = tonumber(Id)
		if N and N > 0 and N % 1 == 0 and #Out.Recent < RECENT and not table.find(Out.Recent, N) then table.insert(Out.Recent, N) end
	end
	-- (2.30) Night FM: liked tracks (30 at most) and the station's last read item
	for _, Id in (typeof(Raw.Liked) == `table` and Raw.Liked) or {} do
		local N = tonumber(Id)
		if N and N > 0 and N % 1 == 0 and N < 1e15 and #Out.Liked < 30 and not table.find(Out.Liked, N) then table.insert(Out.Liked, N) end
	end
	if typeof(Raw.Broadcast) == `number` then Out.Broadcast = math.max(0, math.floor(Raw.Broadcast)) end
	if Raw.Tuned == true then Out.Tuned = true end -- (2.30) heard Night FM's introduction
	return Out
end

function Local.Get(P: Player)
	local Profile = Data.GetProfile(P)
	return Profile and Shared.Sanitize(Profile.Phone)
end

function Local.Save(P: Player, Ph)
	Data.UpdateState(P, { type = `SetPhone`; phone = Ph })
	if Remotes and P.Parent then Remotes.Changed:FireClient(P, Shared.State(P)) end
end

function Shared.State(P: Player)
	local Ph = Local.Get(P)
	local Profile = Data.GetProfile(P)
	-- (1.40) ReportUnread: a report card you haven't opened (Services.School.ReportCards)
	local RepUnread = false
	pcall(function() RepUnread = require(ServerScriptService.Services.School.ReportCards).Unread(P) end)
	return { History = Ph and Ph.History or {}; Recent = Ph and Ph.Recent or {}; Liked = Ph and Ph.Liked or {}; -- (2.30) Liked
		 Wallpaper = Ph and Ph.Wallpaper or nil; Yen = Profile and Profile.Yen or 0;
		Unread = Ph and Shared.Unread(P) or 0; ReportUnread = RepUnread }
end

-- how Viewer sees Target's name
function Local.NameFor(Viewer: Player, Target: Player): string
	local Knows = Viewer == Target
	if not Knows then pcall(function() Knows = require(ServerScriptService.Services.Social.Strangers).Knows(Viewer, Target) end) end
	if Knows then
		local Ok, Name = pcall(function() return Identity.FullName(Identity.Get(Target)) end)
		if Ok and typeof(Name) == `string` and Name ~= `` then return Name end
	end
	return `a stranger`
end

function Local.Who(Viewer: Player, Target: Player)
	return {
		UserId = Target.UserId; Name = Local.NameFor(Viewer, Target); Known = Local.NameFor(Viewer, Target) ~= `a stranger`;
		Race = Target:GetAttribute(`SubRace`) or Target:GetAttribute(`Race`) or `Human`; Family = Target:GetAttribute(`Race`) or `Human`;
		Level = Target:GetAttribute(`Level`) or 1;
	}
end

function Local.ClockText(): string
	local Ok, St = pcall(function() return require(ServerScriptService.Services.School.SchoolClock).GetState() end)
	return if Ok and St then `{St.DayName} {St.ClockText}` else ``
end

---| wallet |---

function Shared.Send(P: Player, UserId: any, Amount: any): (boolean, string)
	local T = typeof(UserId) == `number` and Players:GetPlayerByUserId(UserId)
	if not T or T == P then return false, `They aren't here.` end
	local N = if typeof(Amount) == `number` and Amount == Amount then math.floor(Amount) else 0
	if N < 1 then return false, `Enter an amount.` end
	if N > MAX_SEND then return false, `You can send up to \u{A5}{MAX_SEND} at a time.` end
	if P:GetAttribute(`InMainMenu`) == true or T:GetAttribute(`InMainMenu`) == true then return false, `Not from the main menu.` end
	local Char = P.Character
	if Char and (Char:GetAttribute(`DownedUntil`) or Char:GetAttribute(`Downed`)) then return false, `Not while you're down.` end
	local Now = os.clock()
	if LastSend[P] and Now - LastSend[P] < SEND_GAP then return false, `Wait a moment before sending again.` end
	local From, To = Data.GetProfile(P), Data.GetProfile(T)
	if not (From and To) then return false, `Their record isn't loaded yet.` end
	if (From.Yen or 0) < N then return false, `You don't have \u{A5}{N}.` end
	LastSend[P] = Now
	Data.UpdateState(P, { type = `UpdateYen`; amount = -N })
	Data.UpdateState(T, { type = `UpdateYen`; amount = N })
	local At = Local.ClockText()
	local A, B = Local.Get(P), Local.Get(T)
	-- (audit) each row gets the next Seq (the newest row is first) for the wallet badge
	local function seq(Ph) return ((Ph.History[1] and Ph.History[1].Seq) or 0) + 1 end
	if A then table.insert(A.History, 1, { Dir = `Out`; Amount = N; Who = Local.NameFor(P, T); At = At; Seq = seq(A) }) while #A.History > HISTORY do table.remove(A.History) end Local.Save(P, A) end
	if B then table.insert(B.History, 1, { Dir = `In`; Amount = N; Who = Local.NameFor(T, P); At = At; Seq = seq(B) }) while #B.History > HISTORY do table.remove(B.History) end Local.Save(T, B) end
	Notifications.Notify(T, { Title = `+\u{A5}{N} from {Local.NameFor(T, P)}`; Text = `Sent to your phone's wallet`; Kind = `Good`; Duration = 4 })
	return true, `Sent \u{A5}{N} to {Local.NameFor(P, T)}.`
end

---| the Midnight Bell |---

-- (2.30) another service by dotted path (Social.Rumours, World.Broadcast), nil if it isn't there
local function svc(Path: string)
	local Node = ServerScriptService.Services
	for Seg in Path:gmatch(`[^%.]+`) do Node = Node and Node:FindFirstChild(Seg) end
	if not Node then return nil end
	local Ok, M = pcall(require, Node)
	return if Ok then M else nil
end

local RUMOURS = {
	`Someone keeps hearing knocking from inside the Archive's locked cabinet. The librarian says it's the pipes.`,
	`Three students swear the Hollow left a mark on the Boiler Yard wall. By morning, it was gone.`,
	`The Ordinary don't talk about the night. Ask one why, and watch them change the subject.`,
	`A locker in the Staff Room was found warm at dawn. Nobody signed it out.`,
	`The vending machine gives a free drink if you thank it. It has never once worked.`,
	`Mr. Hale's coffee is the same temperature at midnight as it was at noon.`,
	`A wolf was seen at the edge of the west field, sitting very still, watching the lights of Room 105.`,
}
-- (1.39) the daily special is a real item now (Config.Items.TodaySpecial); the superlatives come from Social.Superlatives
function Local.SupLines(List): string
	local Out = {}
	for _, W in List do
		table.insert(Out, `{W.Title}: {W.First}{if W.Race then ` the {W.Race}` else ``}, {W.Value} {W.What}`)
	end
	return table.concat(Out, `\n`)
end

-- (2.34) the Today card's server lines (docs/expansion/14 §6.2): one live rumour, and your closest path tier with the
-- first thing it's missing. Each is nil when there's nothing real to say.
function Shared.Today(P: Player)
	local Out = {}
	pcall(function()
		local Ru = svc(`Social.Rumours`)
		local Live = Ru and Ru.Live() or {}
		if #Live > 0 then Out.Heard = Ru.Text(Live[#Live]) end
	end)
	pcall(function()
		local N = svc(`Player.Paths`)
		local Nx = N and N.Next(P)
		if Nx and Nx.Missing and #Nx.Missing > 0 then Out.Next = { Path = Nx.Path; Name = Nx.Name; Missing = Nx.Missing[1]; More = #Nx.Missing - 1 } end
	end)
	return Out
end

function Shared.Gazette(Viewer: Player)
	local Day, Hour, DayName, ClockText = 0, 12, ``, ``
	pcall(function()
		local St = require(ServerScriptService.Services.School.SchoolClock).GetState()
		Day, Hour, DayName, ClockText = St.Day, St.Hour, St.DayName, St.ClockText
	end)
	local Lineage = require(ReplicatedStorage.Lineage)
	local Full = false
	pcall(function() Full = Lineage.IsFullMoon(Day, if SchoolTime.IsNight(Hour) then Hour else 21) end)
	local Night = SchoolTime.IsNight(Hour)
	local Articles = {}
	-- the front page
	table.insert(Articles, if Full then {
		Kicker = `FRONT PAGE`; Title = `Full moon tonight`;
		Body = `The Vigil asks students to stay inside after dark. Night races report feeling stronger than usual. The Crimson Court has no comment.`;
	} else {
		Kicker = `FRONT PAGE`; Title = if Night then `The halls are quiet. Too quiet.` else `Another day at Nightmare High`;
		Body = if Night then `Night Study runs at the Archive table after dark. The hall monitors have gone home, but the Night Custodian keeps the Records Office: stay out of restricted areas.`
			else `Homeroom starts at 8:00 in Room 101. Be in your seat on time: tardiness goes on your record.`;
	})
	-- (1.34) the King / Queen of the School makes the front page
	for _, P in Players:GetPlayers() do
		if P:GetAttribute(`NHKing`) == true and P:GetAttribute(`InMainMenu`) ~= true then
			local W = Local.Who(Viewer, P)
			local Who = if P == Viewer then `You` elseif W.Known then W.Name else `A {W.Race}`
			table.insert(Articles, 1, { Kicker = `FRONT PAGE`; Title = `{Who} {if P == Viewer then `run` else `runs`} this school`;
				Body = `Every clique leader at Nightmare High has been beaten in a showdown. The Vigil, the Court, the Athletes, the Lot, the Pack, the Commons, the Choir and the Ink Club all answer to one student now.` })
			break
		end
	end
	-- top of the class
	local Ranked = {}
	for _, P in Players:GetPlayers() do
		if P:GetAttribute(`InMainMenu`) ~= true then table.insert(Ranked, P) end
	end
	table.sort(Ranked, function(A, B) return (A:GetAttribute(`Level`) or 1) > (B:GetAttribute(`Level`) or 1) end)
	local Lines = {}
	for I = 1, math.min(3, #Ranked) do
		local W = Local.Who(Viewer, Ranked[I])
		table.insert(Lines, `{I}. {if W.Known then W.Name else `A {W.Race}`}, level {W.Level}`)
	end
	table.insert(Articles, { Kicker = `TOP OF THE CLASS`; Title = `Who's ahead in the building`;
		Body = if #Lines > 0 then table.concat(Lines, `\n`) else `Nobody's on campus yet.` })
	-- the discipline report
	local Det, Prob = 0, 0
	for _, P in Players:GetPlayers() do
		local L = P:GetAttribute(`DisciplineLevel`)
		if L == `Detention` then Det += 1 elseif L == `Probation` or L == `Suspension` then Prob += 1 end
	end
	table.insert(Articles, { Kicker = `THE OFFICE`; Title = `Discipline report`;
		Body = `{Det} student{if Det == 1 then ` owes` else `s owe`} detention (Room 106, outside class), and {Prob} {if Prob == 1 then `is` else `are`} on probation or worse. Hall monitors remind everyone: wall art is vandalism.` })
	-- (1.41) tonight's sky
	pcall(function()
		local Ph = Lineage.MoonPhase(Day, Hour)
		local Until = Lineage.NightsUntilFull(Day, Hour)
		local SKY = {
			Full = { `Tonight: a full moon`, `The Vigil asks students to keep to the lit halls. Werewolves, mind your manners: your eyes give you away.` };
			Waning = { `Tonight: a waning moon`, `The moon is shrinking. The new moon comes tomorrow night, and with it the Wraiths' hour.` };
			New = { `Tonight: a new moon`, `No moon at all. The darkest night of the cycle. Wraiths, enjoy it; everyone else, carry a light.` };
			Waxing = { `Tonight: a waxing moon`, `The moon is growing. Full in {Until} night{if Until == 1 then `` else `s`}.` };
		}
		local T = SKY[Ph]
		-- a crimson or blue moon takes the front page
		local Ev = Lineage.MoonEvent and Lineage.MoonEvent(Day, Hour)
		if Ev == `Crimson` then
			table.insert(Articles, 1, { Kicker = `FRONT PAGE`; Title = `A crimson moon tonight`;
				Body = `The blood moon rises after dark. Vampires will be at their strongest until dawn, and Ghouls and Wraiths are restless too. The Vigil advises everyone else to stay in the lit halls.` })
		elseif Ev == `Blue` then
			table.insert(Articles, 1, { Kicker = `FRONT PAGE`; Title = `A blue moon tonight`;
				Body = `A rare blue moon rises after dark. The chapel calls it a blessing: Priests and the living stand stronger until dawn.` })
		elseif T then
			table.insert(Articles, { Kicker = `SKYWATCH`; Title = T[1]; Body = T[2] })
		end
	end)
	-- (1.39) the week's superlatives: last week's winners lead Monday's paper; the rest of the week, who's ahead
	local EventDay = if Hour >= 6 then Day else Day - 1
	local SupOk, Sup = pcall(require, ServerScriptService.Services.Social.Superlatives)
	local Board = SupOk and Sup and Sup.Board and Sup.Board()
	if Board then
		if #Board.Last > 0 then
			local Art = { Kicker = `SUPERLATIVES`; Title = `Last week's Most Likely To...`;
				Body = Local.SupLines(Board.Last) .. `\n\nEach winner wears the title until next Monday.` }
			if EventDay % 5 == 0 then table.insert(Articles, 2, Art) else table.insert(Articles, Art) end
		elseif #Board.Leaders > 0 then
			table.insert(Articles, { Kicker = `SUPERLATIVES`; Title = `This week, so far`;
				Body = Local.SupLines(Board.Leaders) .. `\n\nThe Midnight Bell names its winners on Monday morning.` })
		else
			table.insert(Articles, { Kicker = `SUPERLATIVES`; Title = `Who will it be this week?`;
				Body = `Every Monday the Midnight Bell names the school's Class Clown, Most Feared, Teacher's Pet and more, from what students really did that week. It takes at least {Board.Min or 3} to make the paper.` })
		end
	end
	-- the stand: today's special (1.39: a real item, one each a day, with a twist for some races)
	local Items = require(ReplicatedStorage.Config.Items)
	local Sp = Items.SpecialFor(EventDay)
	if Sp then
		local Notes = {}
		for _, Tw in Sp.Race or {} do if Tw.Note then table.insert(Notes, Tw.Note) end end
		table.sort(Notes)
		table.insert(Articles, { Kicker = `CONCESSIONS`; Title = `Today's special: {Sp.Name}`;
			Body = `{Sp.Text} \u{A5}{Sp.Price} at Mrs. Okada's stand by the west doors, one each today: {Items.Describe(Sp)}.`
				.. (if #Notes > 0 then `\n\n` .. table.concat(Notes, ` `) else ``) })
	end
	-- clubs
	table.insert(Articles, { Kicker = `CLUB NOTICES`; Title = `Pitch, court and field`;
		Body = `Soccer, basketball and football clubs meet after school; the Iron Wardens run routes on the lanes west of the field. Drills pay EXP once every few minutes, and personal bests go on the board. Study groups of up to four share their fight EXP.` })
	-- rumours (2.30: the school's live rumours, Social.Rumours; the fixed strings when the halls are quiet)
	local Ru = svc(`Social.Rumours`)
	local Live = (Ru and Ru.Live()) or {}
	local Heard = {}
	for K = #Live, math.max(1, #Live - 2), -1 do table.insert(Heard, `"{Ru.Text(Live[K])}"`) end
	table.insert(Articles, { Kicker = `WHISPERS`; Title = `Heard in the halls`;
		Body = if #Heard > 0 then table.concat(Heard, `\n\n`) .. `\n\n<i>Whether any of it is true is another matter.</i>`
			else RUMOURS[Day % #RUMOURS + 1] .. `\n\n` .. RUMOURS[(Day + 3) % #RUMOURS + 1] })
	-- (2.30) today's campus reports (World.Broadcast)
	local Bc = svc(`World.Broadcast`)
	local Reports = {}
	for _, It in (Bc and Bc.Items()) or {} do if It.Kind == `IncidentReport` then table.insert(Reports, It.Text) end end
	if #Reports > 0 then
		local Last = {}
		for K = #Reports, math.max(1, #Reports - 2), -1 do table.insert(Last, Reports[K]) end
		table.insert(Articles, { Kicker = `ON CAMPUS`; Title = `Today at school`; Body = table.concat(Last, `\n\n`) })
	end
	-- the clock's day count runs from 2024, so the paper numbers its issues within the school year
	return { Date = `{DayName}  \u{00B7}  {ClockText}`; Issue = Day % 200 + 1; Articles = Articles }
end

function Shared.Contacts(Viewer: Player)
	local Out = {}
	for _, P in Players:GetPlayers() do
		if P ~= Viewer and P:GetAttribute(`InMainMenu`) ~= true then table.insert(Out, Local.Who(Viewer, P)) end
	end
	table.sort(Out, function(A, B) if A.Known ~= B.Known then return A.Known end return A.Level > B.Level end)
	return Out
end

---| texts (1.33) |---

-- a text from someone at school (newest first). Text = { From, Body, Dare? }. Toast unless Quiet.
function Shared.AddText(P: Player, T, Quiet: boolean?): boolean
	local Ph = Local.Get(P)
	if not (Ph and typeof(T) == `table` and typeof(T.Body) == `string`) then return false end
	local Day = 0
	pcall(function()
		local St = require(ServerScriptService.Services.School.SchoolClock).GetState()
		Day = require(ReplicatedStorage.Config.Cliques).EventDay(St) or St.Day
	end)
	-- (audit) a stable id for TextAction: one more than the highest kept
	local NextId = 1
	for _, X in Ph.Texts do if X.Id and X.Id >= NextId then NextId = X.Id + 1 end end
	table.insert(Ph.Texts, 1, { From = T.From or `Unknown`; Body = T.Body; At = Local.ClockText(); Day = Day; Dare = T.Dare; Invite = T.Invite; State = `New`; Id = NextId })
	Ph = Shared.Sanitize(Ph)
	Local.Save(P, Ph)
	if not Quiet then
		pcall(Notifications.Notify, P, { Title = `{T.From or `Someone`} texted you`; Text = if #T.Body > 70 then T.Body:sub(1, 67) .. `...` else T.Body; Kind = `Info`; Duration = 5 })
	end
	return true
end

function Shared.SetDareDay(P: Player, Day: number)
	local Ph = Local.Get(P)
	if not Ph then return end
	Ph.DareDay = Day
	Local.Save(P, Ph)
end
function Shared.DareDay(P: Player): number?
	local Ph = Local.Get(P)
	return Ph and Ph.DareDay
end

-- (2.23.0) the school's event day, as texts store it in Day (a night belongs to the evening before it), or nil
function Local.EventDay(): number?
	local Day = nil
	pcall(function()
		local St = require(ServerScriptService.Services.School.SchoolClock).GetState()
		Day = require(ReplicatedStorage.Config.Cliques).EventDay(St) or St.Day
	end)
	return Day
end

-- (2.23.0) a dare text can be answered only if it is the newest copy of that dare and was sent today. Leaders resend
-- the same dare on later days, and Quests.CanStart only knows that the dare itself is current.
function Local.DareLive(Ph, T, Today: number?): boolean
	for _, X in Ph.Texts do -- newest first
		if X.Dare == T.Dare then
			if X ~= T then return false end
			break
		end
	end
	if Today and typeof(T.Day) == `number` and T.Day ~= 0 and T.Day ~= Today then return false end
	return true
end

-- (2.23.0) MarkRead with From marks only that sender's texts read (the Texts app opens one conversation at a time)
function Shared.Texts(P: Player, MarkRead: boolean?, From: string?)
	local Ph = Local.Get(P)
	if not Ph then return {} end
	local Quests = nil
	pcall(function() Quests = require(ServerScriptService.Services.Quests.Quests) end)
	local Out = {}
	local Changed = false
	local Today = Local.EventDay()
	for I, T in Ph.Texts do
		local Row = table.clone(T)
		Row.Index = I
		-- a dare can be accepted while it's still that leader's dare and you haven't done it
		if T.Dare and Quests and T.State ~= `Accepted` and T.State ~= `Declined` then
			local Ok = Quests.CanStart(P, T.Dare)
			Row.CanAccept = Ok == true and Local.DareLive(Ph, T, Today)
		end
		-- (homes) an invite can be taken while it's fresh and the host's room is open
		if T.Invite and T.State ~= `Accepted` and T.State ~= `Declined` then
			local Ok, Homes = pcall(require, ServerScriptService.Services.Features.Homes)
			Row.CanAccept = Ok and Homes.CanVisit(P, T.Invite) == true
		end
		if T.Dare and Quests then
			local QC = require(ReplicatedStorage.Config.Quests).Quests[T.Dare]
			Row.DareName = QC and QC.Name
		end
		table.insert(Out, Row)
		if MarkRead and T.State == `New` and (From == nil or T.From == From) then T.State = `Read` Changed = true end
	end
	if Changed then Local.Save(P, Ph) end
	return Out
end

function Shared.Unread(P: Player): number
	local Ph = Local.Get(P)
	local N = 0
	for _, T in Ph and Ph.Texts or {} do if T.State == `New` then N += 1 end end
	return N
end

function Shared.TextAction(P: Player, Index: any, Action: any, Id: any): (boolean, string)
	local Ph = Local.Get(P)
	local T = nil
	if Ph and typeof(Id) == `number` then
		-- (audit) match the text by its id: the index shifts when a new text arrives after the list was drawn
		for _, X in Ph.Texts do if X.Id == Id then T = X break end end
	else
		-- older saved texts have no id: fall back to the index
		T = Ph and typeof(Index) == `number` and Ph.Texts[Index]
	end
	if not (T and (T.Dare or T.Invite)) then return false, `Nothing to answer.` end
	-- (2.23.0) each text is answered once, and only a live dare (the newest copy, sent today) can be answered
	if T.State == `Accepted` or T.State == `Declined` then return false, `You already answered that.` end
	if T.Dare and not Local.DareLive(Ph, T, Local.EventDay()) then return false, `That dare's over.` end
	-- (homes) a dorm-room invite
	if T.Invite then
		if Action == `Decline` then
			T.State = `Declined`
			Local.Save(P, Ph)
			return true, `Maybe later.`
		elseif Action == `Accept` then
			local Homes = require(ServerScriptService.Services.Features.Homes)
			local Ok, Msg = Homes.Visit(P, T.Invite)
			if not Ok then return false, Msg end
			T.State = `Accepted`
			Local.Save(P, Ph)
			return true, Msg
		end
		return false, `Unknown action.`
	end
	if Action == `Decline` then
		T.State = `Declined`
		Local.Save(P, Ph)
		return true, `Not today.`
	elseif Action == `Accept` then
		local Quests = require(ServerScriptService.Services.Quests.Quests)
		local Ok, Why = Quests.CanStart(P, T.Dare)
		if not Ok then
			return false, if Why == `DoneToday` then `You already did that dare today.`
				elseif Why == `NotToday` then `That dare's over.`
				elseif Why == `Active` then `You're already on it.`
				else `You can't take that dare right now.`
		end
		if not Quests.Start(P, T.Dare) then return false, `You can't take that dare right now.` end
		T.State = `Accepted`
		Local.Save(P, Ph)
		return true, `Dare accepted.`
	end
	return false, `Unknown action.`
end

-- (2.30) Night FM: liked tracks and the station's last read item (saved per slot)
function Shared.SaveLiked(P: Player, List: any): boolean
	if typeof(List) ~= `table` then return false end
	local Ph = Local.Get(P)
	if not Ph then return false end
	local Clean = {}
	for _, V in List do
		local N = tonumber(V)
		if N and N > 0 and N % 1 == 0 and N < 1e15 and #Clean < 30 and not table.find(Clean, N) then table.insert(Clean, N) end
	end
	Ph.Liked = Clean
	Local.Save(P, Ph)
	return true
end
function Shared.BroadcastRead(P: Player): number
	local Ph = Local.Get(P)
	return Ph and Ph.Broadcast or 0
end
function Shared.Tuned(P: Player): boolean -- (2.30) has this student heard Night FM's first-time introduction?
	local Ph = Local.Get(P)
	return Ph ~= nil and Ph.Tuned == true
end
function Shared.SetTuned(P: Player, Value: boolean?)
	local Ph = Local.Get(P)
	if not Ph then return end
	Ph.Tuned = if Value == false then nil else true
	Local.Save(P, Ph)
end
function Shared.StationRead(P: Player, Id: any): boolean
	local Ph = Local.Get(P)
	local N = tonumber(Id)
	if not (Ph and N) then return false end
	Ph.Broadcast = math.max(Ph.Broadcast or 0, math.floor(N))
	Local.Save(P, Ph)
	return true
end

function Shared.SaveWallpaper(P: Player, Wp: any): boolean
	local Ph = Local.Get(P)
	if not Ph or typeof(Wp) ~= `table` then return false end
	Ph.Wallpaper = Shared.Sanitize({ Wallpaper = Wp }).Wallpaper
	Local.Save(P, Ph)
	return true
end

function Shared.SaveRecent(P: Player, List: any): boolean
	local Ph = Local.Get(P)
	if not Ph or typeof(List) ~= `table` then return false end
	local Clean = Shared.Sanitize({ Recent = List }).Recent
	Ph.Recent = Clean
	Local.Save(P, Ph)
	return true
end

---| the handset (a Tool every character spawns with) |---

-- Holding it: the game's animations don't raise the arm for tools, so while the phone is out the server turns the
-- right shoulder (Motor6D C0, replicates to everyone) to bring the hand up in front of the chest, and the grip
-- (solved in Play against the R6 RightGrip weld) stands the phone upright with its screen toward the face and its
-- back, lenses and all, facing out.
local POSE = CFrame.Angles(0, math.rad(45), math.rad(105))
local GRIP = CFrame.new(-0.248250008, -0.0295313597, 0, -0.0342340842, 0.942064762, -0.333679318, -0.821599126, 0.16357027, 0.546094596, 0.569036543, 0.292845726, 0.768400073)

function Local.Pose(Char: Model?, On: boolean)
	local Torso = Char and Char:FindFirstChild(`Torso`)
	local Shoulder = Torso and Torso:FindFirstChild(`Right Shoulder`) :: Motor6D?
	if not Shoulder then return end
	local Base = Shoulder:GetAttribute(`NHBaseC0`)
	if Base == nil then Base = Shoulder.C0 Shoulder:SetAttribute(`NHBaseC0`, Base) end
	Shoulder.C0 = if On then Base * POSE else Base
end

function Local.MakeTool(): Tool?
	local Tpl = game:GetService(`ServerStorage`):FindFirstChild(`NHPhoneModel`)
	if not Tpl then return nil end
	local Model = Tpl:Clone()
	local Screen = Model:FindFirstChild(`Screen`, true) :: BasePart?
	local CF, Size = Model:GetBoundingBox()
	local Basis = if Screen then Screen.CFrame.Rotation + CF.Position else CF
	local T = Instance.new(`Tool`)
	T.Name = `Phone`
	T.CanBeDropped = false
	T.RequiresHandle = true
	T.ToolTip = `Your phone (Y)`
	T:SetAttribute(`NHPhone`, true)
	T:SetAttribute(`Rarity`, `Rare`)
	local Handle = Instance.new(`Part`)
	Handle.Name = `Handle`
	Handle.Size = Vector3.new(0.3, 0.3, 0.3)
	Handle.Transparency = 1
	Handle.CanCollide, Handle.CanQuery, Handle.CanTouch, Handle.Massless = false, false, false, true
	Handle.CFrame = Basis
	Handle.Parent = T
	for _, D in Model:GetDescendants() do
		if D:IsA(`BasePart`) then
			D.Anchored = false
			D.CanCollide, D.CanQuery, D.CanTouch, D.Massless = false, false, false, true
			local W = Instance.new(`WeldConstraint`)
			W.Part0, W.Part1 = Handle, D
			W.Parent = D
		elseif D:IsA(`WeldConstraint`) or D:IsA(`Weld`) then
			D:Destroy()
		end
	end
	-- the screen: a dim glow with the crest on it
	if Screen then
		Screen.Color = Color3.fromRGB(26, 16, 30)
		Screen.Material = Enum.Material.Glass
		for _, Face in { Enum.NormalId.Top, Enum.NormalId.Bottom } do
			local G = Instance.new(`SurfaceGui`)
			G.Face = Face
			G.LightInfluence = 0
			G.Brightness = 1.6
			G.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
			G.PixelsPerStud = 200
			local Bg = Instance.new(`Frame`)
			Bg.Size = UDim2.fromScale(1, 1)
			Bg.BackgroundColor3 = Color3.fromRGB(40, 8, 16)
			Bg.BorderSizePixel = 0
			Bg.Parent = G
			local Gr = Instance.new(`UIGradient`)
			Gr.Rotation = 0
			Gr.Color = ColorSequence.new(Color3.fromRGB(12, 10, 16), Color3.fromRGB(80, 14, 24))
			Gr.Parent = Bg
			local Crest = Instance.new(`ImageLabel`)
			Crest.BackgroundTransparency = 1
			Crest.Image = `rbxassetid://140163448311226` -- Theme.Images.CrestFlat
			Crest.ScaleType = Enum.ScaleType.Fit
			Crest.AnchorPoint = Vector2.new(0.5, 0.5)
			Crest.Position = UDim2.fromScale(0.5, 0.5)
			Crest.Size = UDim2.fromScale(0.42, 0.7)
			Crest.ImageTransparency = 0.15
			Crest.Parent = Bg
			G.Parent = Screen
		end
	end
	Model.Parent = T
	T.Grip = GRIP
	return T
end

function Local.GiveTool(P: Player)
	local Pack = P:WaitForChild(`Backpack`, 10)
	if not Pack then return end
	for _, Holder in { Pack, P.Character } do
		for _, T in (Holder and Holder:GetChildren()) or {} do
			if T:IsA(`Tool`) and T:GetAttribute(`NHPhone`) then return end
		end
	end
	local T = Local.MakeTool()
	if T then
		T.Equipped:Connect(function() Local.Pose(T.Parent :: Model, true) end)
		T.Unequipped:Connect(function() Local.Pose(P.Character, false) end)
		T.Parent = Pack
	end
end

function Shared.OnStart()
	local F = Instance.new(`Folder`)
	F.Name = `NHPhone`
	local function rf(N) local R = Instance.new(`RemoteFunction`) R.Name = N R.Parent = F return R end
	local Get, Send, Gazette, Contacts, SaveRecent = rf(`Get`), rf(`Send`), rf(`Gazette`), rf(`Contacts`), rf(`SaveRecent`)
	local Changed = Instance.new(`RemoteEvent`) Changed.Name = `Changed` Changed.Parent = F
	Remotes = { Changed = Changed }
	local ReadCache
	local function limited(P: Player): boolean
		if ReadCache then ReadCache[P] = nil end -- (audit) a write makes the cached reads stale
		local Now = os.clock()
		if LastCall[P] and Now - LastCall[P] < 0.25 then return true end
		LastCall[P] = Now
		return false
	end
	-- (audit) the read-only remotes had no limit at all (Gazette walks every player and builds ~10 articles); a call
	-- repeated within the window gets the last answer for that remote
	ReadCache = {} :: { [Player]: { [string]: { At: number, Value: any } } }
	local function cached(P: Player, Key: string, Window: number, Fn: () -> any): any
		local Mine = ReadCache[P] or {}
		ReadCache[P] = Mine
		local C = Mine[Key]
		if C and os.clock() - C.At < Window then return C.Value end
		local V = Fn()
		Mine[Key] = { At = os.clock(); Value = V }
		return V
	end
	Players.PlayerRemoving:Connect(function(P) ReadCache[P] = nil end)
	Get.OnServerInvoke = function(P) return cached(P, `Get`, 0.3, function() return Shared.State(P) end) end
	Send.OnServerInvoke = function(P, Id, N) if limited(P) then return false, `One moment...` end return Shared.Send(P, Id, N) end
	Gazette.OnServerInvoke = function(P) return cached(P, `Gazette`, 3, function() return Shared.Gazette(P) end) end
	-- (1.40) the Report Card app
	rf(`Reports`).OnServerInvoke = function(P)
		return cached(P, `Reports`, 1, function()
			local Ok, R = pcall(function() return require(ServerScriptService.Services.School.ReportCards).List(P) end)
			return if Ok then R else nil
		end)
	end
	Contacts.OnServerInvoke = function(P) return cached(P, `Contacts`, 1, function() return Shared.Contacts(P) end) end
	SaveRecent.OnServerInvoke = function(P, L) if limited(P) then return false end return Shared.SaveRecent(P, L) end
	-- (2.30) Night FM: liked tracks, the Midnight Broadcast station (World.Broadcast) and what you've read of it
	rf(`Today`).OnServerInvoke = function(P) return cached(P, `Today`, 4, function() return Shared.Today(P) end) end -- (2.34)
	rf(`SaveLiked`).OnServerInvoke = function(P, L) if limited(P) then return false end return Shared.SaveLiked(P, L) end
	rf(`StationRead`).OnServerInvoke = function(P, Id) if limited(P) then return false end return Shared.StationRead(P, Id) end
	rf(`Station`).OnServerInvoke = function(P)
		return cached(P, `Station`, 2, function()
			local Ok, R = pcall(function() return require(ServerScriptService.Services.World.Broadcast).Station(P) end)
			return if Ok then R else { OnAir = false; Items = {}; LastRead = 0 }
		end)
	end
	-- (2.30) Night FM's voices: the next clip for you, picked when you tune in (World.Broadcast.Voice)
	local VoiceAt = {} :: { [Player]: number }
	Players.PlayerRemoving:Connect(function(P) VoiceAt[P] = nil end)
	rf(`Voice`).OnServerInvoke = function(P)
		if VoiceAt[P] and os.clock() - VoiceAt[P] < 1 then return nil end -- (its own limit: a tune-in lands beside StationRead)
		VoiceAt[P] = os.clock()
		local Ok, R = pcall(function() return require(ServerScriptService.Services.World.Broadcast).Voice(P) end)
		return if Ok then R else nil
	end
	local SaveWallpaper = rf(`SaveWallpaper`)
	SaveWallpaper.OnServerInvoke = function(P, Wp) if limited(P) then return false end return Shared.SaveWallpaper(P, Wp) end
	local Texts, TextAction = rf(`Texts`), rf(`TextAction`)
	Texts.OnServerInvoke = function(P, MarkRead, From)
		local Who = if typeof(From) == `string` then From:sub(1, 40) else nil
		return cached(P, if MarkRead == true then `TextsRead:{Who or ``}` else `Texts`, 0.3, function() return Shared.Texts(P, MarkRead == true, Who) end)
	end
	-- (audit) the client also sends the text's id (the index is only the fallback)
	TextAction.OnServerInvoke = function(P, I, A, Id) if limited(P) then return false, `One moment...` end return Shared.TextAction(P, I, A, Id) end
	F:SetAttribute(`Ready`, true)
	F.Parent = ReplicatedStorage
	Players.PlayerRemoving:Connect(function(P) LastSend[P] = nil LastCall[P] = nil end)
	local function onPlayer(P: Player)
		P.CharacterAdded:Connect(function() task.defer(function() task.wait(0.6) Local.GiveTool(P) end) end)
		if P.Character then task.defer(Local.GiveTool, P) end
	end
	Players.PlayerAdded:Connect(onPlayer)
	for _, P in Players:GetPlayers() do onPlayer(P) end
end

return Shared
