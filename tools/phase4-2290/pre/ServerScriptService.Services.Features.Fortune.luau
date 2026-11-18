--[[
	The Ink Club fortune teller (server). Services.Features.Fortune   (1.45)

	Sable Vey (Config.Npcs Sable, ServerStorage.Dialogue.Sable) sits at a tarot table in the Ink Studio (props batch 26
	SeerTable and SeerChair; the post is the part with NpcPost = Sable, where the sitter's root goes). Once a day (the
	6 AM event day) a student can pay PRICE Yen for a reading: Sable draws one card and gives one vague but true hint about
	what's going on right now. Topics with nothing going on are skipped. At Friendly or better with the Ink Club the hint
	is plain instead of a riddle.

	  The Tower    a rumble today or tomorrow (Social.CliqueFights Rumble), or yesterday's most heated feud
	  The Fool     a dare the student has open (Social.CliqueEvents Today)
	  The Moon     the next full, new, crimson or blue moon (Lineage)
	  The Seeker   where a lost thing is lying (Features.LostFound Loose), by its region (workspace.Regions)
	  The Feast    the daily special and what it does for the student's race (Config.Items)
	  The Crown    who leads one of this week's superlatives (Social.Superlatives Board)
	  The Scholar  the student's report card so far this week (School.ReportCards State), or (1.47) a substitute
	               coming later this week (School.Substitutes Upcoming)

	Saved: PlayerData.Social.Fortune { Day, Card, Text }. The client shows the card (Controllers.World.Fortune, remote
	ReplicatedStorage.NHFortune.Show(Reading)). Sable sits for real: the root is anchored at the post in a seated pose (POSE),
	attribute NHSeated, and is let go while downed or carried.

	API: Read(P) -> (ok, Reading | why), Today(P) -> the reading already given today or nil, Hints(P) -> every hint
	available now (tests), ReadForTests(P, Card?), ResetForTests(P).
]]
local CollectionService = game:GetService(`CollectionService`)
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

local Shared = {}
local Local = {}

local PRICE = 5
local FRIENDLY = 20               -- Ink Club standing for plain hints (Config.Cliques tier Friendly)
-- the seated reading pose on the R6 rig: legs forward on the cushion, hands lowered to the table's edge (radians about
-- each Torso joint's Z axis, on top of its own C0; the Animate script is paused while seated)
local POSE = { [`Right Hip`] = math.pi / 2; [`Left Hip`] = -math.pi / 2; [`Right Shoulder`] = 0.6; [`Left Shoulder`] = -0.6 }
local Rng = Random.new()

-- the cards: title, numeral, and the image (UI.Theme FortuneCards[Card] once uploaded)
Shared.Cards = {
	Tower = { Title = `The Tower`; Numeral = `XVI` };
	Fool = { Title = `The Fool`; Numeral = `0` };
	Moon = { Title = `The Moon`; Numeral = `XVIII` };
	Seeker = { Title = `The Seeker`; Numeral = `IX` };
	Feast = { Title = `The Feast`; Numeral = `III` };
	Crown = { Title = `The Crown`; Numeral = `IV` };
	Scholar = { Title = `The Scholar`; Numeral = `V` };
}

-- how Sable names the cliques in a riddle
local KENNING = {
	Athletes = `those who run in circles`; Ink = `the ink-stained`; Choir = `the voices in the chapel`;
	Pack = `the wolf-toothed`; Delinquents = `the leather and the smoke`; Ordinary = `the ones nobody notices`;
	Vigil = `the watchers in the stacks`; Court = `the crimson court`;
}

local function svc(Path: string)
	local Node = ServerScriptService.Services
	for Part in Path:gmatch(`[^%.]+`) do Node = Node:FindFirstChild(Part) if not Node then return nil end end
	local Ok, Mod = pcall(require, Node)
	return Ok and Mod or nil
end

local function cfg(Name: string)
	local Ok, M = pcall(require, ReplicatedStorage.Config[Name])
	return Ok and M or nil
end

function Local.Clock()
	local C = svc(`School.SchoolClock`)
	local Ok, S = pcall(function() return C.GetState() end)
	return Ok and S or nil
end

function Local.Day(): number
	local D = 0
	pcall(function() D = cfg(`Cliques`).EventDay(Local.Clock()) or 0 end)
	return D
end

function Local.CliqueName(Id: string): string
	local C = cfg(`Cliques`)
	local Def = C and C.Defs and C.Defs[Id]
	return Def and Def.Name or Id
end

function Local.Standing(P: Player): number
	local Rep = svc(`Social.Reputation`)
	local Social = Rep and Rep.Get(P)
	local C = Social and Social.Cliques
	return typeof(C) == `table` and tonumber(C.Ink) or 0
end

-- the region a point is in (the highest Priority, then the smallest box), skipping the open grounds
function Local.RegionAt(Pos: Vector3): string?
	local Defs = (cfg(`Regions`) or {}).Defs or {}
	local Folder = workspace:FindFirstChild(`Regions`)
	local Best, BestPri, BestVol
	for _, B in (Folder and Folder:GetDescendants()) or {} do
		if not B:IsA(`BasePart`) then continue end
		local Id = B:GetAttribute(`RegionId`) or B.Name
		local Def = Defs[Id]
		if not Def or Def.Kind == `Grounds` then continue end
		local L = B.CFrame:PointToObjectSpace(Pos)
		local H = B.Size / 2
		if math.abs(L.X) <= H.X and math.abs(L.Y) <= H.Y and math.abs(L.Z) <= H.Z then -- (audit) abs on Y: points below a box counted as inside
			local Pri, Vol = Def.Priority or 0, B.Size.X * B.Size.Y * B.Size.Z
			if not Best or Pri > BestPri or (Pri == BestPri and Vol < BestVol) then Best, BestPri, BestVol = Def, Pri, Vol end
		end
	end
	return Best and (Best.Title or Best.Name) or nil
end

---| the hints: each returns { Card, Vague, Plain } or nil |---

local Hint = {}

function Hint.Tower(P: Player)
	local F = svc(`Social.CliqueFights`)
	if not F then return nil end
	local R = F.Rumble()
	if R and R.Live then
		return { Card = `Tower`;
			Vague = `The tower is already falling. Go to where the fountain sings, if you want to see it.`;
			Plain = `The rumble's on right now: {Local.CliqueName(R.Live.A)} against {Local.CliqueName(R.Live.B)}, at the Commons.` }
	end
	local Plan = R and R.Plan
	if Plan then
		local When = if Plan.Today then `before tonight's last bell` else `when the sun next sets on school`
		local PWhen = if Plan.Today then `today after school` else `tomorrow after school`
		return { Card = `Tower`;
			Vague = `{KENNING[Plan.A] or Plan.A} and {KENNING[Plan.B] or Plan.B} will meet where the fountain sings, {When}. Fists, not words.`;
			Plain = `{Local.CliqueName(Plan.A)} and {Local.CliqueName(Plan.B)} rumble at the Commons {PWhen}.` }
	end
	local Feud = F.Feuds and (F.Feuds()[1] or F.Feuds(Local.Day() - 1)[1])
	if Feud and Feud.Count and Feud.Count > 0 then
		return { Card = `Tower`;
			Vague = `Bad blood runs between {KENNING[Feud.A] or Feud.A} and {KENNING[Feud.B] or Feud.B}. The tower leans. It will fall soon.`;
			Plain = `{Local.CliqueName(Feud.A)} and {Local.CliqueName(Feud.B)} keep fighting. They're the likeliest pair for the next rumble.` }
	end
	return nil
end

function Hint.Fool(P: Player)
	local Ev = svc(`Social.CliqueEvents`)
	local Ok, T = pcall(function() return Ev.Today(P) end)
	if not (Ok and T) then return nil end
	for _, D in T.Dares or {} do
		if D.State ~= `Done` then
			return { Card = `Fool`;
				Vague = `Someone has dared you, little fool, and the dare is still waiting. {D.From or `Its maker`} is counting the hours.`;
				Plain = `Your dare "{D.Name}" from {D.From or `a leader`} isn't done yet. It's gone at dawn.` }
		end
	end
	return nil
end

function Hint.Moon(P: Player)
	local S = Local.Clock()
	local L = require(ReplicatedStorage.Lineage)
	if not (S and S.Day and L.MoonEvent) then return nil end
	local Hour = S.Hour or 12
	-- the nights ahead (by day the coming night counts as tonight)
	local function ahead(Test)
		for K = 0, 24 do
			if Test(S.Day + K, if K == 0 then Hour else 22) then return K end
		end
		return nil
	end
	local Special = ahead(function(D, H) return L.MoonEvent(D, H) ~= nil end)
	local Kind = Special and L.MoonEvent(S.Day + Special, if Special == 0 then Hour else 22)
	local function nights(K) return if K == 0 then `tonight` elseif K == 1 then `tomorrow night` else `in {K} nights` end
	if Kind and Special <= 8 then
		if Kind == `Crimson` then
			return { Card = `Moon`;
				Vague = `I see the moon bleeding {nights(Special)}. The children of the night will be hungrier than ever.`;
				Plain = `A crimson moon rises {nights(Special)}: Vampires hit harder, Ghouls and Wraiths a little.` }
		end
		return { Card = `Moon`;
			Vague = `A cold blue light is coming, {nights(Special)}. The faithful and the plain will stand taller under it.`;
			Plain = `A blue moon rises {nights(Special)}: Priests and Humans hit harder.` }
	end
	local New = ahead(function(D, H) return L.IsNewMoon(D, H) end)
	local Full = L.NightsUntilFull(S.Day, Hour)
	if New and (not Full or New < Full) then
		return { Card = `Moon`;
			Vague = `The moon closes its eye {nights(New)}. What walks unseen will walk easier.`;
			Plain = `The new moon is {nights(New)}: darker nights, and Wraiths get stronger and harder to spot.` }
	end
	if Full then
		return { Card = `Moon`;
			Vague = `The moon swells. {if Full == 0 then `Tonight` elseif Full == 1 then `Tomorrow` else `In {Full} nights`} it opens wide, and the wolves will answer.`;
			Plain = `The full moon is {nights(Full)}. Werewolves are at their strongest.` }
	end
	return nil
end

function Hint.Seeker(P: Player)
	local LF = svc(`Features.LostFound`)
	local List = LF and LF.Loose and LF.Loose()
	if not (List and #List > 0) then return nil end
	local It = List[Rng:NextInteger(1, #List)]
	local Where = Local.RegionAt(It.Pos)
	local Owner = if It.Clique then KENNING[It.Clique] else nil
	return { Card = `Seeker`;
		Vague = `Something {if Owner then `of {Owner}` else `nobody will claim`} lies forgotten {if Where then `in {Where}` else `out under the open sky`}. It glints, if you look.`;
		Plain = `There's {It.Text} lying {if Where then `in {Where}` else `out on the grounds`}{if It.Clique then `. It belongs to {Local.CliqueName(It.Clique)}` else ``}.` }
end

function Hint.Feast(P: Player)
	local Items = cfg(`Items`)
	local It = Items and Items.TodaySpecial and Items.TodaySpecial()
	if not It then return nil end
	local Race = P:GetAttribute(`Race`)
	local Note = Items.RaceNote(It, Race)
	return { Card = `Feast`;
		Vague = `I see a table set for one, and on it {It.Name}. {if Note then `It knows what you are. Mind it.` else `Eat, and be stronger for it.`}`;
		Plain = `Today's special is {It.Name}{if Note then `. For you: {Note}` else ``}.` }
end

function Hint.Crown(P: Player)
	local Sup = svc(`Social.Superlatives`)
	local Ok, B = pcall(function() return Sup.Board() end)
	local L = Ok and B and B.Leaders
	if not (L and #L > 0) then return nil end
	local Row = L[Rng:NextInteger(1, #L)]
	if not (Row.First and Row.Title) then return nil end
	local Initial = Row.First:sub(1, 1):upper()
	return { Card = `Crown`;
		Vague = `A crown of iron hangs over a {Row.Race and Row.Race:lower() or `student`} whose name begins with {Initial}. They'd be "{Row.Title}". The week isn't over.`;
		Plain = `{Row.First} leads this week for "{Row.Title}".` }
end

local LETTERS = { [0] = `F`, `D`, `C`, `B`, `A`, `A+` }
function Hint.Scholar(P: Player)
	local RC = svc(`School.ReportCards`)
	local Ok, S = pcall(function() return RC.State(P) end)
	local W = Ok and S and S.Week
	if typeof(W) ~= `table` or typeof(W.Subjects) ~= `table` then return nil end
	local Sum, N = 0, 0
	for _, Row in W.Subjects do if typeof(Row) == `table` then Sum += Row.Sum or 0 N += Row.N or 0 end end
	if N == 0 then
		return { Card = `Scholar`;
			Vague = `The owl looks at your report and finds it blank. Ink must touch paper before it can be judged.`;
			Plain = `You haven't been graded in a lesson this week yet. Go to class.` }
	end
	local Avg = Sum / N
	local Letter = LETTERS[math.clamp(math.floor(Avg + 0.5), 0, 5)]
	local Good = Avg >= 3
	return { Card = `Scholar`;
		Vague = if Good then `The owl is pleased. Your ink runs clean this week, keep it so until Monday.`
			else `The owl frowns at your report. The ink is blotted. There's still time before Monday.`;
		Plain = `So far this week you're on a {Letter} average over {N} graded lesson{if N == 1 then `` else `s`}.` }
end

-- (1.47) a substitute later this week (School.Substitutes): who stays a surprise, the plain line says where and when
local WEEKDAYS = { [0] = `Monday`, `Tuesday`, `Wednesday`, `Thursday`, `Friday` }
function Hint.Stranger(P: Player)
	local Subs = svc(`School.Substitutes`)
	local E = Subs and Subs.Upcoming and Subs.Upcoming()
	if not E then return nil end
	return { Card = `Scholar`;
		Vague = `The owl sees a stranger standing at a teacher's desk before the week is out. They will not play by the usual rules.`;
		Plain = `A substitute covers {E.Subject} on {WEEKDAYS[E.Weekday] or `a school day`}. Expect different rules.` }
end

local ORDER = { `Tower`, `Fool`, `Moon`, `Seeker`, `Feast`, `Crown`, `Scholar`, `Stranger` }

function Shared.Hints(P: Player)
	local Out = {}
	for _, Id in ORDER do
		local Ok, H = pcall(Hint[Id], P)
		if Ok and H then
			H.Vague = H.Vague:sub(1, 1):upper() .. H.Vague:sub(2)
			H.Plain = H.Plain:sub(1, 1):upper() .. H.Plain:sub(2)
			Out[Id] = H
		elseif not Ok then
			warn(`[Fortune] {Id}: {H}`)
		end
	end
	return Out
end

---| a reading |---

function Local.Social(P: Player)
	local Rep = svc(`Social.Reputation`)
	return Rep and Rep.Get(P), Rep
end

function Shared.Today(P: Player)
	local Social = Local.Social(P)
	local F = Social and Social.Fortune
	if typeof(F) == `table` and F.Day == Local.Day() and F.Card then return F end
	return nil
end

function Local.Pick(P: Player, Want: string?)
	local All = Shared.Hints(P)
	if Want and All[Want] then return All[Want] end
	local Ids = {}
	for Id in All do table.insert(Ids, Id) end
	if #Ids == 0 then return nil end
	return All[Ids[Rng:NextInteger(1, #Ids)]]
end

function Local.Reading(P: Player, H)
	local Card = Shared.Cards[H.Card]
	local Plain = Local.Standing(P) >= FRIENDLY
	return { Card = H.Card; Title = Card.Title; Numeral = Card.Numeral; Text = if Plain then H.Plain else H.Vague; Plain = Plain }
end

function Shared.Read(P: Player, Want: string?)
	local Social, Rep = Local.Social(P)
	local Data = svc(`Player.Data`)
	local Profile = Data and Data.GetProfile(P)
	if not (Social and Profile) then return false, `NoSlot` end
	local Day = Local.Day()
	if Shared.Today(P) then return false, `Done` end
	if (tonumber(Profile.Yen) or 0) < PRICE then return false, `Broke` end
	local H = Local.Pick(P, Want)
	if not H then return false, `Nothing` end
	local Reading = Local.Reading(P, H)
	Data.UpdateState(P, { type = `UpdateYen`; amount = -PRICE })
	Social.Fortune = { Day = Day; Card = Reading.Card; Text = Reading.Text }
	Rep.Sync(P)
	local Show = ReplicatedStorage:FindFirstChild(`NHFortune`) and ReplicatedStorage.NHFortune:FindFirstChild(`Show`)
	if Show then Show:FireClient(P, Reading) end
	return true, Reading
end

-- show today's card again
function Shared.Again(P: Player)
	local F = Shared.Today(P)
	local Card = F and Shared.Cards[F.Card]
	local Show = ReplicatedStorage:FindFirstChild(`NHFortune`) and ReplicatedStorage.NHFortune:FindFirstChild(`Show`)
	if not (Card and Show) then return false end
	Show:FireClient(P, { Card = F.Card; Title = Card.Title; Numeral = Card.Numeral; Text = F.Text; Again = true })
	return true
end

---| Sable sits |---

function Local.Seat()
	local Live = workspace:FindFirstChild(`Live`)
	local Model
	for _, M in (Live and Live:GetChildren()) or {} do if M:GetAttribute(`NpcId`) == `Sable` then Model = M break end end
	if not Model then return end
	local Hum = Model:FindFirstChildWhichIsA(`Humanoid`)
	local Root = Model:FindFirstChild(`HumanoidRootPart`)
	if not (Hum and Root) then return end
	if Model:GetAttribute(`Clique`) ~= `Ink` then Model:SetAttribute(`Clique`, `Ink`) end
	local Places = svc(`Quests.Places`)
	local Post = Places and Places.Find(`NpcPost`, `Sable`)
	local Free = Hum.Health > 0 and not Hum:GetAttribute(`Downed`) and not Model:GetAttribute(`CarriedBy`) and not Model:GetAttribute(`GrippedBy`)
	if Free and Post then
		if not Model:GetAttribute(`NHSeated`) or not Local.SeatCF then
			Root.Anchored = true
			Root.CFrame = Post.CFrame
			Local.Pose(Model, true)
			-- (1.46.1) rest the hips and thighs on the cushion and keep clear of the chair back (Features.Seats)
			local Chair = Post.Parent and Post.Parent:FindFirstChild(`SeerChair`)
			local Seats = svc(`Features.Seats`)
			if Chair and Seats then pcall(Seats.Settle, Model, Seats.Top(Chair), Seats.Back(Chair), 0.15, Chair) end
			Local.SeatCF = Root.CFrame
			Model:SetAttribute(`NHSeated`, true)
		elseif (Root.Position - Local.SeatCF.Position).Magnitude > 0.2 then
			Root.CFrame = Local.SeatCF
		end
	elseif Model:GetAttribute(`NHSeated`) then
		Model:SetAttribute(`NHSeated`, false)
		Local.SeatCF = nil
		Root.Anchored = false
		Local.Pose(Model, false)
	end
end

-- sit (On) or stand: the joints' C0s, the Animate script, and any playing tracks
function Local.Pose(Model: Model, On: boolean)
	local Torso = Model:FindFirstChild(`Torso`)
	local Hum = Model:FindFirstChildWhichIsA(`Humanoid`)
	local Animate = Model:FindFirstChild(`Animate`)
	if Animate and Animate:IsA(`BaseScript`) then Animate.Enabled = not On end
	if On and Hum then
		local Animator = Hum:FindFirstChildWhichIsA(`Animator`)
		for _, T in (Animator and Animator:GetPlayingAnimationTracks()) or {} do T:Stop(0.1) end
	end
	for Name, Angle in POSE do
		local J = Torso and Torso:FindFirstChild(Name)
		if not (J and J:IsA(`Motor6D`)) then continue end
		local Orig = J:GetAttribute(`NHStandC0`)
		if not Orig then Orig = J.C0 J:SetAttribute(`NHStandC0`, Orig) end
		-- (1.46.1) the legs swing forward from the hip; lift them half their thickness so the thighs lie on the
		-- cushion level with the hips instead of sinking into it
		local Leg = J.Part1
		local Lift = if Name:find(`Hip`) and Leg then CFrame.new(0, Leg.Size.Z / 2, 0) else CFrame.identity
		J.C0 = if On then Lift * Orig * CFrame.Angles(0, 0, Angle) else Orig
	end
end

---| tests |---

function Shared.ReadForTests(P: Player, Card: string?)
	return Shared.Read(P, Card)
end

-- set (or read) a clique standing directly, for the Friendly test
function Shared.StandingForTests(P: Player, Id: string, Value: number?)
	local Social, Rep = Local.Social(P)
	if not (Social and typeof(Social.Cliques) == `table`) then return nil end
	if Value then Social.Cliques[Id] = Value Rep.Sync(P) end
	return Social.Cliques[Id]
end

function Shared.ResetForTests(P: Player)
	local Social, Rep = Local.Social(P)
	if Social then Social.Fortune = nil Rep.Sync(P) end
	return true
end

---| start |---

function Shared.OnStart()
	local F = Instance.new(`Folder`)
	F.Name = `NHFortune`
	local Show = Instance.new(`RemoteEvent`)
	Show.Name = `Show`
	Show.Parent = F
	F.Parent = ReplicatedStorage
	task.spawn(function()
		while true do
			pcall(Local.Seat)
			task.wait(1)
		end
	end)
end

return Shared
