local Report = {}
local Items = {}
table.insert(Items, { Path = {"ReplicatedStorage", "Config", "CliqueTalk", "Generic"}; Source = [==[
-- CliqueTalk.Generic: students without a clique, and the fallback for any clique cell left empty (the line matrix)
return {
	Greet = {
		Hostile = { `Get lost.`, `Not you.`, `Keep walking.`, `We're not friends.` };
		Wary = { `...Hey.`, `Oh. It's you.`, `What do you want?`, `Hm. Hi, I guess.` };
		Neutral = { `Hey.`, `Hi.`, `Sup.`, `How's it going?` };
		Friendly = { "Hey, {Name}!", `Oh good, it's you.`, "{Name}! What's up?", `Hey you. Good day?` };
		Respected = { "{Name}! Looking sharp.", `There's the legend.`, "Always good to see you, {Name}.", `Make way, everyone.` };
	};
	Bump = { Any = { `Watch it!`, `Whoa, sorry.`, `Excuse you.`, `Easy!` } };
	Crowded = { Any = { `Personal space?`, `Little room, please.`, `You're kind of close.`, `Can I help you?` } };
	Shoved = { Any = { `Hey! What was that?`, `Rude much?`, `Okay, ow.`, `Did you just shove me?` } };
	FightSeen = { Any = { `Ooh, here we go.`, `Somebody stop them!`, `I'm not watching. Okay, I'm watching.`, `Someone's getting detention.` } };
	Flee = { Any = { `Whoa, not near me!`, `Take it outside!`, `Nope. I'm out.`, `Someone get a teacher!` } };
	Transformed = { Any = { `What IS that?`, `Stay back...`, `Okay, that's new.`, `Please don't eat me.` } };
	Night = { Any = { `What are you doing out this late?`, `Stay in the light.`, `Late night, huh?`, `Careful out here.` } };
	FullMoon = { Any = { `Full moon tonight. Be careful.`, `You feel that? Full moon.`, `Don't go near the oaks tonight.` } };
	Race = {
		Human = { Any = { `Just a normal kid, huh? Lucky.`, `Human, huh? Welcome to the weird school.`, `Human? Stick close to the lamps.` } };
		Priest = { Any = { `Bless you. Or whatever you say.`, `Oh good, someone holy.`, `Keep that cross handy.` } };
		Vampire = { Any = { `Is it colder near you?`, `Nice fangs. Real?`, `Up all night again? You okay?` } };
		Werewolf = { Any = { `Nice ears.`, `Is that a tail?`, `You smell like the woods.` } };
		Ghoul = { Any = { `You look... tired.`, `Did you sleep at all?`, `You seem really calm today.` } };
		Wraith = { Any = { `I didn't hear you come up.`, `You walk really quietly.`, `Were you always here?` } };
	};
	Hurt = { Any = { `You okay? You look rough.`, `Go see the nurse.`, `Who did that to you?`, `Sit down before you fall down.` } };
	Outfit = {
		FullLook = { Any = { "{Clique} look, head to toe. Huh.", "{Clique} would claim you in that.", "{Clique} colours? Bold." } };
		RivalLook = { Any = { "{Rival} colours? Here?", "{Rival} look? Brave.", "{Rival} look. People notice." } };
		Likes = { Any = { "Nice {Piece}.", "Where'd you get the {Piece}?", "Okay, the {Piece} is cool." } };
		Mocks = { Any = { "Is that a {Piece}? Really?", "Bold choice, the {Piece}.", "Hm. The {Piece}. Interesting." } };
	};
	DressCode = { Any = { `Members' corner. Dress the part.`, `Come back in our colours.`, `Not dressed like that, you're not.` } };
	Fed = {
		Loved = { Any = { "Oh, {Snack}? You're the best.", "{Snack}! How did you know?", "You're sharing {Snack}? Legend.", `My favourite. Thank you!` } };
		Liked = { Any = { "{Snack}? Sure, thanks.", `Oh. Thanks!`, `That's nice of you.`, `Free food? I won't say no.` } };
		Refuse = { Hostile = { `I'm not taking anything from you.`, `Keep it.`, `Is it poisoned? No thanks.` }; Wary = { `Uh, no thanks.`, `I'm good. Really.`, `Why are you giving me food?` } };
	};
	-- (2.31) a Standing Path at tier 3+ (the player's PathTop): StudentBrain greets with it now and then
	Path = {
		Academic = { Any = { `That's the honor student.`, `Top of the class, that one.`, `Heard you aced another test.` } };
		Social = { Any = { `Everyone knows you, huh?`, "Oh, it's {Name}. Of course it is.", `You know everyone here.` } };
		Combat = { Any = { `Don't start with that one.`, `I heard about you. Respect.`, `Easy. I'm not looking for trouble.` } };
		Athletic = { Any = { "Good game last week, {Name}.", `There's the varsity star.`, `Saving a seat at the next match.` } };
		Supernatural = { Any = { `You've seen things. I can tell.`, `You were out the night it rang.`, `People say you know about Mira.` } };
	};
}
]==] })
table.insert(Items, { Path = {"ServerScriptService", "Services", "AI", "StudentBrain"}; Source = [==[
--[[
	StudentBrain (server). Services.AI.StudentBrain  (1.86.2, from the Map place's Features.MapStudents 1.78.0-1.78.6)

	The awareness and the little life of a background student, for any module that owns their routine (in NH Combat
	Test that is Features.Schedules: classes, chairs, cliques, lunch, clubs). The host keeps deciding WHERE a student
	goes; the brain decides how they walk there (Services.AI.Nav), what they notice (Services.AI.Senses), how they
	react, what they say (voices and bubbles: Controllers.World.NpcLook, lines in StudentBrain.Lines), the fidgets, and
	leaning only against a real wall.

	Reactions (most urgent first; Danger cancels the routine, the host re-plans after):
	  Danger      a fight, a transformed monster or a downed body close by: back away fast, then watch
	  Gawk        a fight seen or heard further off: stop and watch until it's been quiet 6 s
	  MakeWay     a student coming straight at them: step aside            (the bump hook, see Brain.OnBump)
	  Space       someone standing right on top of them: step back          (the bump hook, see Brain.OnBump)
	  Stared at, Followed, Glance: head turns and a word, never interrupting the walk
	A seated student (S.Seated) only turns their head for anything but Danger.

	API (S is the host's student table; the brain adds Agent, Senses and its own fields to it)
	  Brain.Init(Host)               Host = { Pose(S, name?), Unseat(S), Replan(S), Students() -> {S}, Plan() -> {Kind, DayName, SegName} }
	  Brain.Attach(S)                after the host spawned S.Model / S.Hum / S.Root (and S.Up): agent, senses, voice, the loop
	  Brain.Detach(S)                before the host destroys the model
	  Brain.GoTo(S, Goal, Valid, Opts?) -> ok     walk with Nav; pauses for reactions and carries on; Valid() false = stop
	  Brain.Idle(S, Seconds, Valid)  wait there for a while: fidgets, a chat with a student beside them, a mutter
	  Brain.LeanOnWall(S, Walk?)     lean only with a wall right behind (Walk: may step up to 9 studs to one) -> ok
	  Brain.Urgent(S) -> string?     the reaction due now, if any
	  Brain.OnBump                   nil, or function(S, Rec, Kind) -> handled  (see the hook in React.MakeWay / Space)
	  Brain.Contact(Pl, Model, Speed, Dir) -> reacted   a bump Pl's client felt (contact feel: Features.ContactFeel
	                                 checked it): the student reacts now, even if Senses never flagged an approach
]]

local CollectionService = game:GetService(`CollectionService`)
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local ServerStorage = game:GetService(`ServerStorage`)

local Nav = require(ServerScriptService.Services.AI.Nav)
local SchoolTime = require(game:GetService("ReplicatedStorage"):WaitForChild("Functions"):WaitForChild("SchoolTime")) -- (2.22.0) shared night windows
local Senses = require(ServerScriptService.Services.AI.Senses)
local Lines = require(script:WaitForChild(`Lines`))
local Items = require(game:GetService(`ReplicatedStorage`).Config.Items) -- (inventory QOL batch 5) the clique foods
-- (line matrix) clique x attitude x moment; a broken or missing Talk falls back to today's pools, never the whole brain
local OkT, Talk = pcall(require, script:WaitForChild(`Talk`, 5))
if not OkT or typeof(Talk) ~= `table` then
	Talk = { Pick = function() return nil end; Attitude = function() return `Neutral` end; Outfit = function() return nil end }
end
local CliqueConfig = require(ReplicatedStorage.Config.Cliques)
local Appearance = require(ReplicatedStorage.UI.Appearance)
local Cliques = require(ServerScriptService.Services.Social.Cliques) -- (line matrix) the dress code, Cliques.Dressed
local function Rep() return require(ServerScriptService.Services.Social.Reputation) end -- (2.27) lazy: no cycle at load

local Brain = {}
local Host = nil
local Started = false
local Studio = RunService:IsStudio()
local React = {}

-- NUDGE HOOK (for Nudge_Left / Nudge_Right / Shove_Forward): set Brain.OnBump to a function(S, Rec, Kind) that
-- plays the reaction and moves the student, and return true to skip the default step aside. Kind is "MakeWay"
-- (someone walking straight at them) or "Space" (someone standing on top of them). Rec is the Senses record of
-- the player (Rec.Player, Rec.Root, Rec.Pos, Rec.Speed, Rec.Dist).
local NudgeMod = require(script:WaitForChild(`Nudges`))
Brain.OnBump = NudgeMod.Handle :: ((any, any, string) -> boolean)? -- (1.86.3) the nudges

---| helpers |---

local function plan(): { [string]: any }
	return (Host and Host.Plan and Host.Plan()) or { Kind = `Off` }
end

-- what the lines can talk about right now
local function ctx(): { [string]: any }
	local T = game:GetService(`Lighting`).ClockTime
	local P = plan()
	return {
		Kind = P.Kind; Day = P.DayName or `today`; Period = P.SegName or `class`;
		Moon = workspace:GetAttribute(`NHMoonPhase`) or ``;
		Night = SchoolTime.InWindow(T, `Dark`) or workspace:GetAttribute(`NHMoonNight`) == true;
	}
end

local function bubble(S, Text: string, Mood: string?)
	S.SaidAt = os.clock()
	-- (2.0.0) the line's attitude (Hostile, Wary, Respected...): the clients' talking face takes its expression from it
	-- (Controllers.Character.FaceTalk); nil = from the student's mood or the words
	S.Model:SetAttribute(`NHSayMood`, Mood)
	S.Model:SetAttribute(`NHSay`, Text)
	S.Model:SetAttribute(`NHSayFor`, math.clamp(1.8 + #Text * 0.06, 2.4, 6))
	S.Model:SetAttribute(`NHSayAt`, workspace:GetServerTimeNow())
end

-- say a line from a pool (not one they said lately). Force skips the "don't talk over yourself" wait (chats).
local function say(S, Pool: { string }?, Cooldown: number?, Force: boolean?): boolean
	if not Force and os.clock() - (S.SaidAt or -1e9) < (Cooldown or 8) then return false end
	local Text = Pool and Lines.Pick(S, Pool, ctx())
	if not (Text and S.Model) then return false end
	bubble(S, Text)
	return true
end
local function sayText(S, Text: string)
	if not S.Model then return end
	bubble(S, Lines.Fill(Text, ctx()))
end

-- say a line from the line matrix (StudentBrain.Talk: this student's clique, how they feel about Pl, the moment), or
-- one from Fallback (today's pool) when the matrix has nothing. Opts: Sub (race / outfit verdict), Attitude, Piece.
local function sayMatrix(S, Moment: string, Pl: Player?, Opts: { [string]: any }?, Cooldown: number?, Fallback: { string }?): boolean
	if os.clock() - (S.SaidAt or -1e9) < (Cooldown or 8) or not S.Model then return false end
	local O = table.clone(Opts or {})
	O.Ctx = O.Ctx or ctx()
	local Ok, Text = pcall(Talk.Pick, S, Moment, Pl, O)
	if Ok and Text then
		bubble(S, Text, O.Attitude)
		return true
	end
	return Fallback ~= nil and say(S, Fallback, Cooldown)
end

-- a shove (Nudges) gets its own line once the student turns to look at who did it
local memo, remembers -- (2.27) declared below; OnShove and glance use them
NudgeMod.OnShove = function(S, Rec)
	local Pl = Rec and Rec.Player
	if S.RosterId and Pl then -- (2.27) a shove is remembered: -12 and Fought, at most once per 30 s
		local M = memo(S, Pl)
		if os.clock() - (M.ShoveSaved or -1e9) >= 30 then
			M.ShoveSaved = os.clock()
			pcall(function() Rep().ChangeRelationship(Pl, S.RosterId, -12, nil, `Fought`) end)
		end
	end
	sayMatrix(S, `Shoved`, Pl, nil, 0, Lines.MakeWay)
end

-- (contact feel) the bump line lands at the moment of contact, not on the approach: a sprinter's hit always gets the
-- Sprint line, a brush the Bump line 60% of the time (as MakeWay did). Space already said its Crowded line, and a
-- shove says Shoved once the student has turned round.
NudgeMod.OnContact = function(S, Rec, Kind, Speed, Shove)
	if Kind == `Space` or Shove then return end
	if (Speed or 0) > 18 then
		say(S, Lines.Sprint, 10)
	elseif math.random() < 0.6 then
		sayMatrix(S, `Bump`, Rec and Rec.Player, nil, 10, Lines.MakeWay)
	end
end

-- what a student remembers about each player: how often they've met, when they last said hi, when they saw them fight
function memo(S, Pl: Player?)
	if not Pl then return {} end
	S.Memory = S.Memory or {}
	local M = S.Memory[Pl.UserId]
	if not M then M = { Met = 0; Greeted = -1e9; Fought = -1e9 } S.Memory[Pl.UserId] = M end
	return M
end

-- the time-of-day hello (today's pools), the matrix's fallback
local function daily(C): { string }
	local G = Lines.Greet
	if C.Night then
		if C.Moon == `Full` and math.random() < 0.6 then return G.FullMoon end
		if C.Moon == `New` and math.random() < 0.4 then return G.NewMoon end
		return G.Night
	end
	local H = game:GetService(`Lighting`).ClockTime
	return if H < 11 then G.Morning elseif H >= 16.5 then G.Evening else G.Day
end

-- the right hello for this player, now: a line-matrix moment (nil = today's pool only), its options, and today's pool
-- as the fallback. Order (the line matrix spec): saw you fight, your outfit, you're hurt, you're transformed, your race,
-- their clique, met before, night, time of day.
local function greeting(S, Rec): (string?, { [string]: any }?, { string })
	local C = ctx()
	local Pl = Rec and Rec.Player
	local M = memo(S, Pl)
	local G = Lines.Greet
	if S.RosterId and Pl and os.clock() - (M.Fought or -1e9) >= 300 then -- (2.27) the saved memory, after a fresh fight
		local Ok, E = pcall(function() return Rep().Entry(Pl, S.RosterId) end)
		if Ok and E then
			local T = S.Temper or `Warm`
			if not E.Met and E.Value >= -19 then return `Intro`, nil, Lines.Intro[T] or Lines.Intro.Warm end
			if (E.Flags.Fought or 0) >= 1 and E.Value < 0 then return nil, nil, G.Grudge[T] or G.Grudge.Warm end
			if (E.Flags.Helped or 0) >= 2 and E.Value >= 10 then return nil, nil, G.Grateful[T] or G.Grateful.Warm end
		end
	end
	if os.clock() - (M.Fought or -1e9) < 300 then
		local OkA, A = pcall(Talk.Attitude, S, Pl)
		return `Greet`, { Attitude = if OkA and A == `Hostile` then `Hostile` else `Wary` }, G.Wary
	end
	local Ch = Pl and Pl.Character
	if Pl and os.clock() - (M.Outfit or -1e9) > 600 then
		local Ok, Verdict, Piece = pcall(Talk.Outfit, S, Pl)
		if Ok and Verdict and math.random() < (if S.Clique then 0.35 else 0.15) then
			M.Outfit = os.clock()
			return `Outfit`, { Sub = Verdict; Piece = Piece }, daily(C)
		end
	end
	local Hum = Ch and Ch:FindFirstChildWhichIsA(`Humanoid`)
	if Hum and Hum.MaxHealth > 0 and Hum.Health / Hum.MaxHealth < 0.35 and math.random() < 0.5 then
		return `Hurt`, nil, daily(C)
	end
	local OkF, Form = false, nil
	if Ch then OkF, Form = pcall(Appearance.FormOf, Ch) end
	if OkF and Form then return `Transformed`, nil, Lines.ByNature(S, Lines.Monster, `Brave`) end
	local Top = Pl and Pl:GetAttribute(`PathTop`) -- (2.31) a Standing Path at tier 3+: "That's the honor student."
	if Top and math.random() < 0.25 then return `Path`, { Sub = Top }, daily(C) end
	local Race = Pl and Pl:GetAttribute(`Race`)
	if Race and math.random() < 0.3 then return `Race`, { Sub = Race }, G.Race[Race] or daily(C) end
	local Def = S.Clique and CliqueConfig.Defs[S.Clique]
	if Def then
		-- strong feelings always show (a Hostile student never chirps "Hi."); the rest greet by their clique 60% of the time
		local OkA, A = pcall(Talk.Attitude, S, Pl)
		if not OkA or typeof(A) ~= `string` then A = `Neutral` end
		local Strong = A == `Hostile` or A == `Wary` or A == `Respected`
		if Strong or math.random() < 0.6 then
			local O = if Strong then { Attitude = A } else nil
			if C.Night and math.random() < 0.4 then -- (line matrix) the night still shows at the extremes
				if C.Moon == `Full` then return `FullMoon`, O, G.FullMoon end
				return `Night`, O, G.Night
			end
			local Tier = Pl and Pl:GetAttribute(`CliqueTier_{S.Clique}`)
			return `Greet`, O, (Def.Reactions and Tier and Def.Reactions[Tier]) or daily(C)
		end
	end
	if (M.Met or 0) >= 4 and math.random() < 0.6 then return nil, nil, G.Often end
	if (M.Met or 0) >= 1 and math.random() < 0.7 then return nil, nil, G.Again end
	if C.Night then
		if C.Moon == `Full` and math.random() < 0.6 then return `FullMoon`, nil, G.FullMoon end
		if C.Moon == `New` and math.random() < 0.4 then return nil, nil, G.NewMoon end
		return `Night`, nil, G.Night
	end
	return nil, nil, daily(C)
end

-- (2.27) does this rostered student have something saved to say to Pl (an introduction, a grudge, thanks)?
-- the same rules as greeting()'s saved-memory branch
function remembers(S, Pl: Player?): boolean
	if not (S.RosterId and Pl) then return false end
	local Ok, E = pcall(function() return Rep().Entry(Pl, S.RosterId) end)
	if not (Ok and E) then return false end
	return (not E.Met and E.Value >= -19)
		or ((E.Flags.Fought or 0) >= 1 and E.Value < 0)
		or ((E.Flags.Helped or 0) >= 2 and E.Value >= 10)
end

local function greet(S, Rec): boolean
	local Pl = Rec and Rec.Player
	local M = memo(S, Pl)
	if os.clock() - (M.Greeted or -1e9) < 60 then return false end
	local Moment, Opts, Pool = greeting(S, Rec)
	local Said
	if Moment == `Intro` then -- (2.27) they tell you their name, and now you've met
		if os.clock() - (S.SaidAt or -1e9) < 6 then return false end
		local Line = Pool[math.random(1, #Pool)]
		sayText(S, (string.gsub(Line, "{First}", S.First or `me`))) -- (2.29) a plain pattern string, not an interpolation
		Said = true
		pcall(function() Rep().Meet(Pl, S.RosterId) end)
	else
		Said = if Moment then sayMatrix(S, Moment, Pl, Opts, 6, Pool) else say(S, Pool, 6)
	end
	if Said then
		M.Greeted = os.clock()
		M.Met = (M.Met or 0) + 1
		return true
	end
	return false
end

local function lookAt(S, P: Vector3?, Seconds: number?)
	if not S.Model then return end
	if P then
		S.Model:SetAttribute(`NHLookAt`, P)
		S.Model:SetAttribute(`NHLookUntil`, workspace:GetServerTimeNow() + (Seconds or 0.6))
	else
		S.Model:SetAttribute(`NHLookUntil`, nil)
	end
end

local function step(S, Text: string)
	if Studio and S.Model then S.Model:SetAttribute(`NHStep`, Text) end
end

local function mood(S, M: string, Hold: number?)
	local Now = os.clock()
	if not Hold and Now < (S.MoodHold or 0) then return end
	if Hold then S.MoodHold = Now + Hold end
	if S.Model and S.Model:GetAttribute(`NHMood`) ~= M then S.Model:SetAttribute(`NHMood`, M) end
end

local function headOf(Rec): Vector3?
	local C = Rec and Rec.Player and Rec.Player.Character
	local H = C and C:FindFirstChild(`Head`)
	return H and H:IsA(`BasePart`) and H.Position or (Rec and Rec.Pos)
end

local function playerNear(P: Vector3, R: number): boolean
	for _, Pl in Players:GetPlayers() do
		local Root = Pl.Character and Pl.Character:FindFirstChild(`HumanoidRootPart`)
		if Root and Root:IsA(`BasePart`) and (Root.Position - P).Magnitude < R then return true end
	end
	return false
end

local function pose(S, Name: string?)
	if Host and Host.Pose then Host.Pose(S, Name) end
end

---| reactions |---

-- the most urgent thing to react to right now. What triggered it is kept 0.8 s (S.Pending), so a reaction isn't
-- lost when the moment has passed by the time the brain gets to it
local function urgentNow(S, Snap): string?
	if not Snap then return nil end
	local T = Snap.Threat
	if T and S.Root then
		local Dist = (T.Pos - S.Root.Position).Magnitude
		local Close = 10 + (1 - S.Bravery) * 12 -- brave ones let it get closer
		if Dist < Close and T.Level > 0.15 then return `Danger` end
		if T.Kind == `Fight` and Dist < 55 then return `Gawk` end
	end
	if S.Seated then return nil end -- a seated student only reacts to danger and fights
	if Snap.Approaching and not S.Busy then return `MakeWay` end
	if Snap.Crowding then return `Space` end
	return nil
end

local function urgent(S, Snap): (string?, any)
	local U = urgentNow(S, Snap)
	if U then
		S.Pending = { U = U; Snap = Snap; At = os.clock() }
		return U, Snap
	end
	local P = S.Pending
	if P and os.clock() - P.At < 0.8 then return P.U, P.Snap end
	return nil, Snap
end

function Brain.Urgent(S): string?
	return (urgent(S, S.Senses and S.Senses.Last))
end

local function watching(S): boolean
	return S.WatchUntil ~= nil and os.clock() < S.WatchUntil and not S.Seated
end

-- somewhere 12-26 studs away from a point, on the floor, further from it
local function awayFrom(S, From: Vector3): Vector3?
	local My = S.Root.Position
	local Base = Vector3.new(My.X - From.X, 0, My.Z - From.Z)
	if Base.Magnitude < 0.1 then Base = S.Root.CFrame.LookVector * -1 end
	Base = Base.Unit
	for _, A in { 0, 35, -35, 70, -70, 110, -110 } do
		local Dir = CFrame.Angles(0, math.rad(A), 0):VectorToWorldSpace(Base)
		for _, R in { 26, 18, 12 } do
			local F = Nav.Floor(My + Dir * R, 6)
			if F and (F - From).Magnitude > (My - From).Magnitude then return F end
		end
	end
	return nil
end

function React.Danger(S, Snap)
	local T = Snap.Threat
	if S.Seated and Host and Host.Unseat then Host.Unseat(S) end
	mood(S, `Scared`, 6)
	S.Model:SetAttribute(`NHActivity`, `Backing away ({T.Kind})`)
	local C = ctx()
	if T.From and T.From.Player and T.Kind == `Fight` then memo(S, T.From.Player).Fought = os.clock() end
	local Pool = if T.Kind == `Monster` then (if C.Moon == `Full` and math.random() < 0.4 then Lines.MonsterFullMoon else Lines.ByNature(S, Lines.Monster, `Brave`))
		elseif T.Kind == `Body` then Lines.Body
		elseif C.Night and math.random() < 0.35 then Lines.FleeNight
		else Lines.ByNature(S, Lines.Flee, `Brave`)
	local Who = T.From and T.From.Player
	local Moment = if T.Kind == `Monster` then `Transformed` elseif T.Kind == `Fight` then `Flee` else nil
	if not (Moment and Who and sayMatrix(S, Moment, Who, nil, 8, nil)) then say(S, Pool, 8) end
	S.Shaken = true
	lookAt(S, T.Pos + Vector3.new(0, 2, 0), 2)
	local To = awayFrom(S, T.Pos)
	if To then
		S.Agent:GoTo(To, { Speed = 13 + S.Bravery * 2; Arrive = 2.5 })
	else
		S.Agent:Shuffle(S.Root.Position - T.Pos, 1.2, 11)
	end
	S.WatchUntil = os.clock() + 8
	S.WatchAt = T.Pos
	S.Replan = true -- the routine starts again from here once it's over
end

---| (2.15.0, combat concept 19) crowds at fights |---
-- Gawkers form a ring round a fight at a safe distance (each one just outside their own Danger distance), face it,
-- and act the part: the brave chant and shout bets, the timid beg them to stop or say they're glad it isn't them,
-- the rest call the state of the fight, and about a third hold a phone up to record it. A ring of three or more
-- draws the nearest hall monitor (School.HallMonitor.Respond, once every 25 s per ring; the Map has no monitors).
local Rings = {} :: { any }
local GOLDEN = math.rad(137.5)
local RECORD_POSE = CFrame.Angles(0, math.rad(35), math.rad(140)) -- the right arm up in front, phone to the fight

local function ringFor(Center: Vector3)
	local Now = os.clock()
	for I = #Rings, 1, -1 do if Now - Rings[I].Last > 10 then table.remove(Rings, I) end end
	for _, R in Rings do
		if (R.Center - Center).Magnitude < 16 then
			R.Center = R.Center:Lerp(Center, 0.3)
			R.Last = Now
			return R
		end
	end
	local R = { Center = Center; Members = {}; Count = 0; Last = Now; Alerted = 0; Base = math.random() * math.pi * 2 }
	table.insert(Rings, R)
	return R
end

-- this student's spot in the ring: spread round it (golden angle), just outside the distance that would scare them off
local function ringSpot(S, R): Vector3?
	local Slot = R.Members[S]
	if not Slot then R.Count += 1 Slot = R.Count R.Members[S] = Slot end
	local Close = 10 + (1 - (S.Bravery or 0.5)) * 12 -- the Danger distance (urgentNow)
	local Radius = Close + 2.5 + (Slot % 2) * 1.5
	local A = R.Base + Slot * GOLDEN
	local P = R.Center + Vector3.new(math.cos(A), 0, math.sin(A)) * Radius
	return Nav.Floor(P, 6)
end

local function crowdCount(R): number
	local N = 0
	for S in R.Members do if S.Model and S.Model.Parent and watching(S) then N += 1 end end
	return N
end

local function crowdLine(S)
	local P, B = Lines.Crowd, S.Bravery or 0.5
	local Pool = if B > 0.65 then (if math.random() < 0.5 then P.Chant else P.Bet)
		elseif B < 0.35 then (if math.random() < 0.5 then P.Beg else P.Glad)
		elseif S.CrowdPhone then P.Phone
		else P.State
	say(S, Pool, 9)
end

-- a phone held up at the fight while they watch (the fidget's phone, arm raised); it goes away when the watching ends
local function holdPhone(S)
	if S.CrowdPhone or S.Seated or not (Brain._MakePhone and Brain._Shoulder) then return end
	local T, J = Brain._MakePhone(), Brain._Shoulder(S)
	if not (T and J and S.Hum) then if T then T:Destroy() end return end
	S.CrowdPhone = T
	T.Parent = S.Model
	pcall(function() S.Hum:EquipTool(T) end)
	J.C0 = (J:GetAttribute(`NHBaseC0`) or J.C0) * RECORD_POSE
	task.spawn(function()
		while S.Model and S.Model.Parent and T.Parent and watching(S) do task.wait(0.3) end
		if T.Parent then T:Destroy() end
		if J.Parent then J.C0 = J:GetAttribute(`NHBaseC0`) or J.C0 end
		S.CrowdPhone = nil
	end)
end

function React.Gawk(S, Snap)
	local T = Snap.Threat
	mood(S, `Watching`, 4)
	local Started = os.clock() > (S.WatchUntil or 0)
	local R = ringFor(T.Pos)
	if not S.Seated then
		S.Model:SetAttribute(`NHActivity`, `Watching a fight`)
		pose(S, nil)
		local Spot = ringSpot(S, R)
		if Spot and S.Root and (S.Root.Position - Spot).Magnitude > 3 then
			S.Agent:GoTo(Spot, { Speed = 9 + (S.Bravery or 0.5) * 3; Arrive = 1.5 })
		else
			S.Agent:Stop()
		end
		S.Agent:Face(R.Center)
		if Started and math.random() < 0.35 then holdPhone(S) end
	end
	lookAt(S, R.Center + Vector3.new(0, 2, 0), 1.2)
	if Started then -- just started watching
		if T.From and T.From.Player then memo(S, T.From.Player).Fought = os.clock() end
		if T.Heard and math.random() < 0.5 then
			say(S, Lines.Heard.Fight, 10)
		else
			sayMatrix(S, `FightSeen`, T.From and T.From.Player, nil, 10, Lines.ByNature(S, Lines.Gawk, `Brave`))
		end
	elseif math.random() < 0.12 then
		crowdLine(S)
	end
	S.WatchUntil = os.clock() + 6
	S.WatchAt = T.Pos
	S.Shaken = true
	if os.clock() - R.Alerted > 25 and crowdCount(R) >= 3 then
		R.Alerted = os.clock()
		task.spawn(function()
			local School = ServerScriptService.Services:FindFirstChild(`School`)
			local M = School and School:FindFirstChild(`HallMonitor`)
			if not M then return end
			local Ok, HM = pcall(require, M)
			if Ok and typeof(HM) == `table` and HM.Respond then pcall(HM.Respond, R.Center) end
		end)
	end
	task.wait(0.4)
end

function React.MakeWay(S, Snap)
	local Rec = Snap.Approaching
	if not (Rec and Rec.Pos) then return end
	mood(S, `Wary`, 3)
	lookAt(S, headOf(Rec), 1.5)
	-- (contact feel) no line here any more: it comes at the moment of contact (NudgeMod.OnContact)
	-- the bump hook (nudges): a handler that plays its own reaction and moves the student replaces the step aside
	if Brain.OnBump then
		local Ok, Handled = pcall(Brain.OnBump, S, Rec, `MakeWay`)
		if Ok and Handled then return end
	end
	-- step to whichever side they aren't heading for
	local Rel = Rec.Pos - S.Root.Position
	local Side = Vector3.new(-Rel.Z, 0, Rel.X)
	local V = Rec.Root and Rec.Root.AssemblyLinearVelocity or Vector3.zero
	if Side:Dot(V) > 0 then Side = -Side end
	S.Agent:Shuffle(Side, 0.55, 7)
	S.Agent:Face(Rec.Pos)
	task.wait(0.3)
end

function React.Space(S, Snap)
	local Rec = Snap.Crowding
	if not (Rec and Rec.Pos) then return end
	mood(S, `Uneasy`, 5)
	lookAt(S, headOf(Rec), 2.5)
	sayMatrix(S, `Crowded`, Rec.Player, nil, 10, Lines.ByNature(S, Lines.Space, `Social`))
	if Brain.OnBump then
		local Ok, Handled = pcall(Brain.OnBump, S, Rec, `Space`)
		if Ok and Handled then Rec.Near = 0 return end
	end
	S.Agent:Shuffle(S.Root.Position - Rec.Pos, 0.7, 4)
	S.Agent:Face(Rec.Pos)
	Rec.Near = 0
	task.wait(0.4)
end

-- the gentle ones (never stop walking): staring back, glancing, feeling followed
local function glance(S, Snap)
	local Now = os.clock()
	local Moving = S.Agent and S.Agent.Moving
	if Snap and Snap.Staring then
		local Rec = Snap.Staring
		lookAt(S, headOf(Rec), 0.6)
		if not Moving then
			if S.Social >= 0.5 then
				mood(S, `Friendly`)
				if not greet(S, Rec) and Rec.Stare > 7 and not Rec.SaidStared then
					Rec.SaidStared = say(S, Lines.Stared, 8)
				end
			elseif Rec.Stare > 6 and not S.Busy then
				mood(S, `Shy`)
				-- (2.27) a shy rostered student still speaks up when there's something saved to say: their name the first
				-- time, a grudge, or thanks (the greeting picks which); otherwise they stay shy
				if not (remembers(S, Rec.Player) and greet(S, Rec)) then say(S, Lines.Shy, 20) end
			end
		end
		return
	end
	if Snap and Snap.Following then
		mood(S, `Uneasy`)
		if Now - (S.GlancedBack or 0) > 2.5 then
			S.GlancedBack = Now
			lookAt(S, headOf(Snap.Following), 0.9)
			local M = memo(S, Snap.Following.Player)
			M.Followed = (M.Followed or 0) + 1
			say(S, if M.Followed > 2 then Lines.FollowedAgain else Lines.Followed, 12)
		end
		S.Hurry = Now + 6
		return
	end
	if S.WatchUntil and Now < S.WatchUntil and S.WatchAt then
		lookAt(S, S.WatchAt + Vector3.new(0, 2, 0), 0.6)
		return
	end
	if S.Shaken and not (S.WatchUntil and Now < S.WatchUntil) and not (Snap and Snap.Threat) then
		S.Shaken = false
		say(S, Lines.Relief, 4)
	end
	if Snap and Snap.Focus and Snap.Focus.Aware > 0.45 and (Snap.Focus.Dist or 99) < 30 then
		lookAt(S, headOf(Snap.Focus), 0.6)
		local F = Snap.Focus
		if F.Visible and (F.Dist or 99) < 7 and S.Social > 0.55 and not Moving and math.random() < 0.05 then greet(S, F) end
		if F.Fighting and F.Player then memo(S, F.Player).Fought = Now end
		return
	end
	if Snap and Snap.Heard and Snap.Heard.Kind == `Door` and Now - Snap.Heard.At < 1.5 then
		lookAt(S, Snap.Heard.Pos, 1.2)
		if Snap.Heard ~= S.LastHeard then
			S.LastHeard = Snap.Heard
			local C = ctx()
			if math.random() < (if C.Night then 0.35 else 0.1) then say(S, if C.Night then Lines.Heard.DoorNight else Lines.Heard.Door, 15) end
		end
		return
	end
	if S.Partner and S.Partner.Root and not Moving then
		lookAt(S, S.Partner.Root.Position + Vector3.new(0, 1.5, 0), 0.6)
		return
	end
	if Now > (S.NextLookAround or 0) and S.Root then
		S.NextLookAround = Now + math.random(25, 70) / 10
		local Ang = math.rad(math.random(-70, 70))
		local Dir = CFrame.Angles(0, Ang, 0):VectorToWorldSpace(S.Root.CFrame.LookVector)
		lookAt(S, S.Root.Position + Dir * 12 + Vector3.new(0, math.random(-2, 3), 0), 1.4)
	end
	if S.Model and S.Model:GetAttribute(`NHMood`) ~= `Calm` and not (S.WatchUntil and Now < S.WatchUntil) then mood(S, `Calm`) end
end

---| walking |---

-- walk with Nav. A reaction stops the walk; it carries on afterwards. Valid() false (the routine changed) stops it.
function Brain.GoTo(S, Goal: Vector3, Valid: () -> boolean, Opts: { [string]: any }?): boolean
	local Tries = 0
	while Valid() and S.Agent and S.Root do
		-- let a reaction (or watching a fight) finish first
		local Since = os.clock()
		while Valid() and (S.Reacting or watching(S) or Brain.Urgent(S)) and os.clock() - Since < 20 do task.wait(0.1) end
		if not (Valid() and S.Agent and S.Root) then return false end
		local Speed = (S.Speed or 6) * (if S.Hurry and os.clock() < S.Hurry then 1.35 else 1)
		local Ok, Why = S.Agent:GoTo(Goal, {
			Speed = (Opts and Opts.Speed) or Speed; Arrive = Opts and Opts.Arrive;
			ShouldStop = function() return not Valid() or S.Reacting or watching(S) or Brain.Urgent(S) ~= nil end;
		})
		if Ok then return Valid() end
		if Why ~= `cancelled` then step(S, `walk failed: {Why}`) return false end
		Tries += 1
		if Tries > 12 then return false end
		task.wait(0.1)
	end
	return false
end

---| talk |---

-- something to mutter: the day, the moon, the time, the part of the day, or (in a clique) the clique's own talk
local function mutterPool(S): { string }
	local C = ctx()
	local Def = S.Clique and CliqueConfig.Defs[S.Clique]
	if Def and Def.Lines and #Def.Lines > 0 and math.random() < 0.4 then return Def.Lines end
	local M = Lines.Mutter
	if C.Night then
		if C.Moon == `Full` and math.random() < 0.5 then return M.FullMoon end
		return M.Night
	end
	if math.random() < 0.2 then
		if C.Day == `Monday` then return M.Monday end
		if C.Day == `Friday` then return M.Friday end
		if C.Day == `Saturday` or C.Day == `Sunday` then return M.Weekend end
	end
	return M[C.Kind] or M.Break
end

-- two students standing together take turns, look at whoever's talking, and break off for anything urgent
local function chat(A, B)
	-- (2.29) a rumour A knows and B doesn't comes first (Social.Rumours); anyone within 12 studs overhears it
	local Lines2
	local OkR, Ru = pcall(function() return require(ServerScriptService.Services.Social.Rumours) end)
	local Rumour = OkR and Ru and A.RosterId and B.RosterId and Ru.ForChat(A.RosterId, B.RosterId)
	if not Rumour and OkR and Ru and A.RosterId and B.RosterId then
		Rumour = Ru.ForChat(B.RosterId, A.RosterId)
		if Rumour then A, B = B, A end -- whoever knows it tells it (the pair's first speaker is just the lower index)
	end
	if Rumour then
		Lines2 = { `A: Did you hear? {Ru.Text(Rumour)}`, `B: ` .. (Lines.Pick(B, Lines.RumourReply or { `No way.` }, ctx()) or `No way.`) }
		Ru.Heard(B.RosterId, Rumour)
		for _, P in Players:GetPlayers() do
			local R = P.Character and P.Character:FindFirstChild(`HumanoidRootPart`)
			if R and A.Root and (R.Position - A.Root.Position).Magnitude <= 12 then pcall(Ru.HeardByPlayer, P, Rumour) end
		end
	else
		Lines2 = Lines.PickChat(A, ctx())
	end
	if not Lines2 then return end
	A.Chatting, B.Chatting = true, true
	A.Partner, B.Partner = B, A
	if not A.Seated and A.Agent and B.Root then A.Agent:Face(B.Root.Position) end
	if not B.Seated and B.Agent and A.Root then B.Agent:Face(A.Root.Position) end
	for _, L in Lines2 do
		if typeof(L) ~= `string` then continue end
		local Who, Text = L:match(`^(%a):%s*(.+)$`)
		local Speaker, Listener = if Who == `B` then B else A, if Who == `B` then A else B
		if not (Speaker.Model and Listener.Model and Speaker.Root and Listener.Root) then break end
		if Brain.Urgent(A) or Brain.Urgent(B) or A.Reacting or B.Reacting then break end
		if (A.Agent and A.Agent.Moving) or (B.Agent and B.Agent.Moving) then break end
		sayText(Speaker, Text or L)
		lookAt(Listener, Speaker.Root.Position + Vector3.new(0, 1.5, 0), 3)
		lookAt(Speaker, Listener.Root.Position + Vector3.new(0, 1.5, 0), 3)
		task.wait(math.clamp(1.6 + #(Text or L) * 0.055, 2.2, 4.6))
	end
	A.Chatting, B.Chatting = false, false
	A.Partner, B.Partner = nil, nil
end

---| fidgets |---

local PHONE_POSE = CFrame.Angles(0, math.rad(45), math.rad(105))
local PHONE_GRIP = CFrame.new(-0.248250008, -0.0295313597, 0, -0.0342340842, 0.942064762, -0.333679318, -0.821599126, 0.16357027, 0.546094596, 0.569036543, 0.292845726, 0.768400073)

local function makePhone(): Tool?
	local Tpl = ServerStorage:FindFirstChild(`NHPhoneModel`)
	if not Tpl then return nil end
	local Model = Tpl:Clone()
	local Screen = Model:FindFirstChild(`Screen`, true)
	local CF = Model:GetBoundingBox()
	local Basis = if Screen and Screen:IsA(`BasePart`) then Screen.CFrame.Rotation + CF.Position else CF
	local T = Instance.new(`Tool`)
	T.Name = `Phone`
	T.CanBeDropped = false
	T.RequiresHandle = true
	T.Grip = PHONE_GRIP
	T:SetAttribute(`NHPhone`, true)
	T:SetAttribute(`NHNpcPhone`, true)
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
	if Screen and Screen:IsA(`BasePart`) then
		Screen.Material = Enum.Material.Neon
		Screen.Color = Color3.fromRGB(60, 24, 40)
	end
	Model.Parent = T
	return T
end

local shoulder
-- (2.15.0) the crowd's phone (React.Gawk, defined above, reaches these through Brain)
Brain._MakePhone = function() return makePhone() end
Brain._Shoulder = function(S) return shoulder(S) end

function shoulder(S): Motor6D?
	local Torso = S.Model and S.Model:FindFirstChild(`Torso`)
	local J = Torso and Torso:FindFirstChild(`Right Shoulder`)
	return if J and J:IsA(`Motor6D`) then J else nil
end

local function busyNow(S): boolean
	return S.Chatting or S.Reacting or not S.Model or (S.Agent and S.Agent.Moving) or Brain.Urgent(S) ~= nil
end

local function fidgetPhone(S, Valid)
	local T = makePhone()
	local J = shoulder(S)
	if not (T and J and S.Hum) then if T then T:Destroy() end return end
	T.Parent = S.Model
	pcall(function() S.Hum:EquipTool(T) end)
	J.C0 = (J:GetAttribute(`NHBaseC0`) or J.C0) * PHONE_POSE
	if math.random() < 0.45 then say(S, Lines.Phone, 8) end
	local Until = os.clock() + math.random(40, 90) / 10
	while os.clock() < Until and not busyNow(S) and T.Parent and Valid() do
		local Arm = S.Model:FindFirstChild(`Right Arm`)
		if Arm then lookAt(S, Arm.Position + Vector3.new(0, -0.4, 0), 0.6) end
		task.wait(0.25)
	end
	if T.Parent then T:Destroy() end
	if J.Parent then J.C0 = J:GetAttribute(`NHBaseC0`) or J.C0 end
end

local function fidget(S, Valid)
	if busyNow(S) or not S.Root then return end
	local C = ctx()
	local Sleepy = C.Kind == `BeforeSchool` or C.Night
	local Pool = if S.Seated then { { `LookUp`, 0.3 }, { `LookBehind`, 0.3 }, { `Phone`, if C.Kind == `Class` then 0 else 0.3 } }
		else {
			{ `Phone`, if S.Partner then 0.12 else 0.32 };
			{ `Stretch`, if Sleepy then 0.28 else 0.12 };
			{ `LookUp`, 0.14 };
			{ `LookBehind`, if C.Night then 0.3 else 0.12 };
			{ `Shift`, if S.Leaning then 0 else 0.25 };
		}
	local Total = 0
	for _, P in Pool do Total += P[2] end
	local R = math.random() * Total
	local Kind = Pool[#Pool][1]
	for _, P in Pool do R -= P[2] if R <= 0 then Kind = P[1] break end end
	step(S, `fidget: {Kind}`)
	if Kind == `Phone` then
		fidgetPhone(S, Valid)
	elseif Kind == `Stretch` then
		S.Model:SetAttribute(`NHFidget`, `Stretch`)
		S.Model:SetAttribute(`NHFidgetAt`, workspace:GetServerTimeNow())
		if Sleepy and math.random() < 0.5 then say(S, Lines.Yawn, 6) end
		lookAt(S, S.Root.Position + S.Root.CFrame.LookVector * 6 + Vector3.new(0, 9, 0), 1.4)
		task.wait(1.6)
	elseif Kind == `LookUp` then
		lookAt(S, S.Root.Position + S.Root.CFrame.LookVector * 25 + S.Root.CFrame.RightVector * math.random(-12, 12) + Vector3.new(0, 30, 0), 2.2)
		task.wait(2.2)
	elseif Kind == `LookBehind` then
		local Side = if math.random() < 0.5 then 1 else -1
		lookAt(S, S.Root.Position - S.Root.CFrame.LookVector * 4 + S.Root.CFrame.RightVector * 10 * Side + Vector3.new(0, 1.5, 0), 1.3)
		if C.Night and math.random() < 0.25 then say(S, Lines.Mutter.Night, 10) end
		task.wait(1.4)
	else -- shift their weight: turn a little, ease into it
		local From = S.Root.CFrame
		local To = From * CFrame.Angles(0, math.rad(math.random(15, 35) * (if math.random() < 0.5 then 1 else -1)), 0)
		for I = 1, 8 do
			if not S.Root.Parent or busyNow(S) then break end
			S.Root.CFrame = From:Lerp(To, I / 8)
			task.wait(0.05)
		end
	end
end

---| leaning |---
-- Owner (1.78.6): "they should only have this pose when they are leaning on a wall". A student only leans with a
-- solid, upright wall right behind them (never a door: it could open behind them); they turn their back to it and
-- step back to about a stud off it. No wall near: no lean.
local LeanP = RaycastParams.new()
LeanP.FilterType = Enum.RaycastFilterType.Exclude
LeanP.RespectCanCollide = true

local function isDoor(I: Instance): boolean
	local M = I:FindFirstAncestorOfClass(`Model`)
	while M do
		if CollectionService:HasTag(M, `NHDoor`) then return true end
		M = M:FindFirstAncestorOfClass(`Model`)
	end
	return false
end

local function wallNear(S, Reach: number): (Vector3?, Vector3?)
	local R = S.Root
	if not R then return nil, nil end
	local Ex = {}
	for _, N in { `NHSchedule`, `NHStudents`, `NHAmbient`, `Live`, `School NPC Spots`, `NHFx`, `NHNavDebug` } do local F = workspace:FindFirstChild(N) if F then table.insert(Ex, F) end end
	for _, Pl in Players:GetPlayers() do if Pl.Character then table.insert(Ex, Pl.Character) end end
	LeanP.FilterDescendantsInstances = Ex
	local Best, BestD = nil, math.huge
	local Look = R.CFrame.LookVector
	for I = 0, 11 do
		local Dir = CFrame.Angles(0, math.rad(I * 30), 0):VectorToWorldSpace(Vector3.new(Look.X, 0, Look.Z).Unit)
		local Hits = 0
		local First = nil
		for _, H in { -0.4, 1.0 } do -- waist and shoulder height
			local Hit = workspace:Raycast(R.Position + Vector3.new(0, H, 0), Dir * Reach, LeanP)
			if Hit and Hit.Instance.Transparency < 0.5 and math.abs(Hit.Normal.Y) < 0.25 and not isDoor(Hit.Instance) then
				Hits += 1
				First = First or Hit
			end
		end
		if Hits == 2 and First then
			local D = (Vector3.new(First.Position.X, 0, First.Position.Z) - Vector3.new(R.Position.X, 0, R.Position.Z)).Magnitude
			if D < BestD then Best, BestD = First, D end
		end
	end
	if not Best then return nil, nil end
	return Best.Position, Vector3.new(Best.Normal.X, 0, Best.Normal.Z).Unit
end

function Brain.LeanOnWall(S, Walk: boolean?, Valid: (() -> boolean)?): boolean
	if not (S.Root and S.Agent) or S.Seated then return false end
	Valid = Valid or function() return true end
	local At, Normal = wallNear(S, 4)
	if not At then
		if not Walk then return false end
		At, Normal = wallNear(S, 9)
		if not (At and Normal) then return false end
		if not Brain.GoTo(S, At + Normal * 1.6, Valid, { Speed = (S.Speed or 6) * 0.8; Arrive = 0.8 }) then return false end
		At, Normal = wallNear(S, 4)
		if not (At and Normal) then return false end
	end
	S.Agent:Face(S.Root.Position + Normal * 5)
	local R = S.Root
	local Gap = Vector3.new(R.Position.X - At.X, 0, R.Position.Z - At.Z):Dot(Normal)
	local Back = Gap - 1.15
	if Back > 0.15 then
		S.Agent:Shuffle(-Normal, Back / 2.5, 2.5)
		S.Agent:Face(S.Root.Position + Normal * 5)
	end
	local Behind = workspace:Raycast(S.Root.Position, -Normal * 2.2, LeanP)
	if not (Behind and math.abs(Behind.Normal.Y) < 0.25 and not isDoor(Behind.Instance)) then return false end
	pose(S, `Lean`)
	S.Leaning = true
	step(S, `leaning on a wall`)
	return true
end

---| idling |---

-- the nearest other student standing still within reach, free to talk
local function neighbour(S, Reach: number)
	local Best, BestD = nil, Reach
	for _, O in (Host and Host.Students and Host.Students()) or {} do
		if O ~= S and O.Model and O.Root and O.Idling and not O.Chatting and not O.Reacting and not (O.Agent and O.Agent.Moving)
			and (O.Seated ~= nil) == (S.Seated ~= nil) then
			local D = (O.Root.Position - S.Root.Position).Magnitude
			if D < BestD then Best, BestD = O, D end
		end
	end
	return Best
end

-- stay here a while: fidget now and then, talk with a student beside you, mutter (only with a player near enough
-- to see and hear it). Returns when the time is up or Valid() is false.
function Brain.Idle(S, Seconds: number, Valid: () -> boolean)
	local Until = os.clock() + Seconds
	S.Idling = true
	S.NextChat = math.max(S.NextChat or 0, os.clock() + math.random(30, 90) / 10)
	S.NextFidget = math.max(S.NextFidget or 0, os.clock() + math.random(20, 60) / 10)
	local InClass = plan().Kind == `Class`
	while os.clock() < Until and Valid() and S.Model and S.Root do
		if S.Reacting or busyNow(S) then task.wait(0.25) continue end
		local Near = playerNear(S.Root.Position, 60)
		if os.clock() >= S.NextFidget then
			S.NextFidget = os.clock() + math.random(60, 140) / 10
			if Near and not S.Chatting then fidget(S, Valid) end
		end
		if os.clock() >= S.NextChat then
			S.NextChat = os.clock() + math.random(120, 280) / 10 * (if InClass then 3 else 1)
			if Near then
				local O = neighbour(S, 7)
				if O and O.Index > S.Index and not InClass then
					chat(S, O)
				elseif math.random() < (if InClass then 0.15 else 0.55) then
					say(S, mutterPool(S), 10)
				end
			end
		end
		task.wait(0.25)
	end
	S.Idling = false
	if S.Leaning then S.Leaning = false end
end

---| the loop |---

local function loop(S, Model)
	while S.Model == Model and Model.Parent do
		if S.Senses then
			local Snap = S.Senses:Due() and S.Senses:Tick() or S.Senses.Last
			pcall(glance, S, Snap)
			local U, USnap = urgent(S, Snap)
			if U and React[U] and not S.Reacting then
				S.Pending = nil
				S.Reacting = true
				if S.Leaning then pose(S, nil) S.Leaning = false end
				step(S, `reacting: {U}`)
				local Ok, Err = pcall(React[U], S, USnap)
				if not Ok then warn(`[StudentBrain] {U}: {Err}`) end
				S.Reacting = false
				if S.Replan and not watching(S) then
					S.Replan = false
					if Host and Host.Replan then pcall(Host.Replan, S) end
				end
			elseif S.Replan and not watching(S) and not U then
				S.Replan = false
				if Host and Host.Replan then pcall(Host.Replan, S) end
			end
		end
		task.wait(0.1)
	end
end

function Brain.Attach(S)
	if not (S.Model and S.Hum and S.Root) then return end
	local M = S.Model
	M:SetAttribute(`NHVoice`, S.Voice or 1) -- Controllers.World.NpcLook: the pitch within the voice set
	M:SetAttribute(`NHVoiceSet`, S.VoiceSet or `Boy`)
	M:SetAttribute(`NHPersonality`, string.format(`brave %.1f, social %.1f`, S.Bravery or 0.5, S.Social or 0.5))
	M:SetAttribute(`NHBrain`, true) -- Controllers.World.Chatter leaves these to the brain's own lines
	local Torso = M:FindFirstChild(`Torso`)
	for _, J in { `Right Shoulder`, `Left Shoulder` } do
		local Joint = Torso and Torso:FindFirstChild(J)
		if Joint and Joint:IsA(`Motor6D`) then Joint:SetAttribute(`NHBaseC0`, Joint.C0) end
	end
	S.Agent = Nav.Agent(M, { Speed = S.Speed or 6; Name = `Student{S.Index}` })
	S.Agent.Up = S.Up or 3
	S.Senses = Senses.Perceiver(M, { Bravery = S.Bravery or 0.5; ViewRange = 60 + (S.Social or 0.5) * 20 })
	S.Reacting, S.Chatting, S.Idling, S.Leaning, S.Replan, S.Pending = false, false, false, false, false, nil
	S.NudgeWaiting, S.NudgeHit = nil, nil -- (contact feel) a record reused after a despawn starts clean
	task.spawn(loop, S, M)
end

-- (contact feel) a bump the player's client felt and Features.ContactFeel checked (Model is a live student, the player
-- is next to it, Speed is no more than the server saw them move). The impact goes into the nudges' ram memory; then
-- the student reacts now, unless they're seated, fleeing or busy with another reaction. If a MakeWay is already
-- waiting for this brush, the report ends the wait and that handler reacts.
-- (inventory QOL batch 5) a player offers this student a snack (Features.Inventory.Feed). They turn to the player and
-- answer in their clique's voice (the "Fed" moment): Loved (their clique loves it), Liked, or Refuse (Hostile, or Wary
-- with no loved food). Returns the verdict and the student's clique, or nil if Model isn't a student.
function Brain.Fed(Pl: Player, Model: Model, It): (string?, string?)
	local S = nil
	for _, X in (Host and Host.Students and Host.Students()) or {} do
		if X.Model == Model then S = X break end
	end
	if not (S and S.Model and S.Root) then return nil end
	local Foods = S.Clique and Items.CliqueFood[S.Clique]
	local Loved = Foods ~= nil and table.find(Foods, It.Id) ~= nil
	local OkA, Attitude = pcall(Talk.Attitude, S, Pl)
	Attitude = if OkA then Attitude else `Neutral`
	local Verdict = if Attitude == `Hostile` or (Attitude == `Wary` and not Loved) then `Refuse` elseif Loved then `Loved` else `Liked`
	local Root = Pl.Character and Pl.Character:FindFirstChild(`HumanoidRootPart`)
	if Root then lookAt(S, Root.Position + Vector3.new(0, 1.5, 0), 3) end
	local C = ctx()
	C.Snack = It.Name
	sayMatrix(S, `Fed`, Pl, { Sub = Verdict; Ctx = C; Attitude = if Verdict == `Refuse` then Attitude else nil }, 0)
	if S.RosterId and Verdict ~= `Refuse` then -- (2.27) a snack they took is remembered, at most once per 10 minutes
		local M = memo(S, Pl)
		if os.clock() - (M.FedSaved or -1e9) >= 600 then
			M.FedSaved = os.clock()
			pcall(function() Rep().ChangeRelationship(Pl, S.RosterId, if Verdict == `Loved` then 8 else 5, nil, `Helped`) end)
		end
	end
	return Verdict, S.Clique
end

-- (2.29) tests: one pair chat between two students (the rumour path runs if either knows one)
function Brain.ChatForTests(A, B) chat(A, B) end

-- (2.27) tests: the greeting this student would pick for Pl now (the moment, nil for a plain pool, and the pool)
function Brain.GreetingForTests(S, Pl: Player)
	local Moment, _, Pool = greeting(S, { Player = Pl })
	return Moment, Pool
end

function Brain.Contact(Pl: Player, Model: Model, Speed: number, Dir: Vector3): boolean
	local S = nil
	for _, X in (Host and Host.Students and Host.Students()) or {} do
		if X.Model == Model then S = X break end
	end
	if not (S and S.Root and S.Model) then return false end
	NudgeMod.Remember(Pl, Speed, Dir)
	local Root = Pl.Character and Pl.Character:FindFirstChild(`HumanoidRootPart`)
	if not (Root and Root:IsA(`BasePart`)) then return false end
	local Rec = { Player = Pl; Root = Root; Pos = Root.Position; Speed = Speed;
		Dist = (Root.Position - S.Root.Position).Magnitude }
	if S.Seated then return false end
	if S.NudgeWaiting then S.NudgeHit = Rec return true end
	if S.Reacting or not NudgeMod.Ready(S, Rec) then return false end
	-- the loop's own set-up for a reaction (the walk, Brain.GoTo, and the loop's reactions wait while Reacting)
	S.Pending = nil
	S.Reacting = true
	if S.Leaning then pose(S, nil) S.Leaning = false end
	step(S, `reacting: Contact`)
	task.spawn(function()
		mood(S, `Wary`, 3)
		local Ok, Err = pcall(NudgeMod.Handle, S, Rec, `Contact`)
		if not Ok then warn(`[StudentBrain] Contact: {Err}`) end
		S.Reacting = false
	end)
	return true
end

function Brain.Detach(S)
	if S.Agent then pcall(function() S.Agent:Stop() end) end
	if S.Senses and S.Senses.Destroy then pcall(function() S.Senses:Destroy() end) end
	S.Agent, S.Senses = nil, nil
	S.NudgeWaiting, S.NudgeHit = nil, nil
end

---| dress codes (line matrix) |---

-- walk into a clique's hangout out of its colours and the nearest of its students (30 studs) says so: once a visit,
-- at most every 120 s for each player. A hangout box is a floating marker in some places (Combat Test's sit 11 to 16
-- studs up while the floor is near 1), so it counts by its X/Z footprint, from 20 studs under its bottom face to 6
-- over its top face, not by its height.
local Visits = {} :: { [Player]: { In: string?, Told: number } }

local function hangoutOf(Root: BasePart): string?
	local Folder = workspace:FindFirstChild(`Regions`)
	if not Folder then return nil end
	for Id, Def in CliqueConfig.Defs do
		local Box = Def.Hangout and Folder:FindFirstChild(Def.Hangout)
		if Box and Box:IsA(`BasePart`) then
			local L = Box.CFrame:PointToObjectSpace(Root.Position)
			local H = Box.Size / 2
			if math.abs(L.X) <= H.X and math.abs(L.Z) <= H.Z and L.Y >= -H.Y - 20 and L.Y <= H.Y + 6 then return Id end
		end
	end
	return nil
end

local function dressCheck(P: Player)
	local Root = P.Character and P.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	local V = Visits[P] or { Told = -1e9 }
	Visits[P] = V
	local Id = Root and hangoutOf(Root)
	if Id == V.In then return end
	V.In = Id
	if not (Id and Root) or os.clock() - V.Told < 120 then return end
	local Ok, Dressed = pcall(Cliques.Dressed, P, Id)
	if not Ok or Dressed then return end
	local Best, BestD = nil, 30
	for _, S in (Host and Host.Students and Host.Students()) or {} do
		if S.Clique == Id and S.Root and S.Model and not S.Reacting then
			local D = (S.Root.Position - Root.Position).Magnitude
			if D < BestD then Best, BestD = S, D end
		end
	end
	if Best and sayMatrix(Best, `DressCode`, P, nil, 0, nil) then
		V.Told = os.clock()
		lookAt(Best, Root.Position + Vector3.new(0, 1.5, 0), 2)
	end
end

local function dressWatch()
	local Warned = false
	while true do
		task.wait(1)
		for _, P in Players:GetPlayers() do
			local Ok, Err = pcall(dressCheck, P) -- one bad player or student never stops the watch for the server
			if not Ok and not Warned then
				Warned = true
				warn("[StudentBrain] dressWatch: " .. tostring(Err))
			end
		end
		for P in Visits do
			if not P.Parent then Visits[P] = nil end
		end
	end
end

function Brain.Init(H)
	Host = H
	if Started then return end
	Started = true
	Nav.Init()
	Senses.Init()
	task.spawn(dressWatch) -- (line matrix) hangout dress codes
end

return Brain
]==] })
table.insert(Items, { Path = {"ServerScriptService", "Services", "Social", "Dialogue"}; Source = [==[
--[[
	Dialogue (server authoritative, reusable)

	Trees live in ServerStorage.Dialogue.<NpcId> and are plain data:
		{
			Start = function(ctx) -> node id,
			Nodes = {
				[Id] = {
					Text = "..." or function(ctx) -> string,
					Choices = { { Text = "..." or fn, If = fn(ctx)?, Do = fn(ctx) -> next id?, Next = id? } },
					-- or Choices = function(ctx) -> list (for shared menus)
				},
			},
		}
	The client only ever receives the current line and the choices that passed their If check.
	Every choice is re-validated here (session, index, distance to the NPC) before its Do runs,
	so outcomes (joining, relationship, reputation) can't be forged.

	ctx helpers: Player, NpcId, Npc, FactionId, Met(), Meet(), Value(), State(), Rel(n, reason),
	Rep(category), AddRep(category, n), Standing(), Rank(), Member(), RivalMember(), CanJoin(),
	Join(), Leave(), Once(key) (true once per in-game day), Mission(), MissionDef, Faction.
	Quests: Offers(), QuestDef(id), StartQuest(id), QuestStatus(id), JustCompleted (quests this
	conversation finished, e.g. a delivery), Has(item), StartChampion(), Decide(id, choice) / Decided(id) (2.24.0).
]]

---| Services |---

local Players = game:GetService(`Players`)
local HttpService = game:GetService(`HttpService`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerStorage = game:GetService(`ServerStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local Packets = require(ReplicatedStorage.Remotes.Packets)
local RepConfig = require(ReplicatedStorage.Config.Reputation)
local FactionConfig = require(ReplicatedStorage.Config.Factions)
local Cast = require(ReplicatedStorage.Config.Npcs)
local QuestConfig = require(ReplicatedStorage.Config.Quests)

local Reputation = require(ServerScriptService.Services.Social.Reputation)
local Factions = require(ServerScriptService.Services.Social.Factions)
local SchoolClock = require(ServerScriptService.Services.School.SchoolClock)
local Quests = require(ServerScriptService.Services.Quests.Quests)
local Duels = require(ServerScriptService.Services.Quests.Duels)

local MAX_DISTANCE = 16
local Sessions = {} :: { [Player]: any }

local Local = {}
local Shared = {}

function Local.Tree(NpcId: string)
	local Name = Cast[NpcId] and Cast[NpcId].Dialogue or NpcId
	local Module = ServerStorage:FindFirstChild(`Dialogue`) and ServerStorage.Dialogue:FindFirstChild(Name)
	return Module and require(Module)
end

function Local.Context(Player: Player, NpcId: string, JustCompleted: { string }?)
	local Npc = Cast[NpcId] or RepConfig.Npcs[NpcId]
	local FactionId = Npc and Npc.Faction
	local Faction = FactionId and FactionConfig.Factions[FactionId]
	local ctx = { Player = Player; NpcId = NpcId; Npc = Npc; FactionId = FactionId; Faction = Faction; MissionDef = Faction and Faction.Mission }

	function ctx.Met() local _, _, Met = Reputation.Relationship(Player, NpcId) return Met end
	function ctx.Meet() Reputation.Meet(Player, NpcId) end
	function ctx.Value() return (Reputation.Relationship(Player, NpcId)) end
	function ctx.State() local _, State = Reputation.Relationship(Player, NpcId) return State end
	function ctx.Rel(Amount: number, Reason: string?) Reputation.ChangeRelationship(Player, NpcId, Amount, Reason) end
	function ctx.Rep(Category: string) return Reputation.Value(Player, Category) end
	function ctx.PathTier(Path: string) -- (2.31) Standing Paths (Services.Player.Paths)
		local Ok, T = pcall(function() return require(ServerScriptService.Services.Player.Paths).Tier(Player, Path) end)
		return if Ok and typeof(T) == `number` then T else 1
	end
	function ctx.AddRep(Category: string, Amount: number) Reputation.Add(Player, Category, Amount) end
	function ctx.Standing() local F = Factions.Get(Player, FactionId) return F and F.Standing or 0 end
	function ctx.Rank() local F = Factions.Get(Player, FactionId) return F and F.Rank or `Outsider` end
	function ctx.Member() local F = Factions.Get(Player, FactionId) return F ~= nil and F.Member end
	function ctx.RivalMember()
		for _, RivalId in Faction and Faction.Rivals or {} do
			local R = Factions.Get(Player, RivalId)
			if R and R.Member then return true end
		end
		return false
	end
	function ctx.CanJoin() return Factions.CanJoin(Player, FactionId) end
	function ctx.Join() return Factions.Join(Player, FactionId) end
	function ctx.Leave() return Factions.Leave(Player, FactionId) end
	function ctx.Mission() return Factions.GetMissionProgress(Player, FactionId) end
	function ctx.MissionStatus() return Factions.MissionStatus(Player, FactionId) end
	function ctx.Once(Key: string): boolean
		local Social = Reputation.Get(Player)
		if not Social then return false end
		Social.DialogueDaily = if typeof(Social.DialogueDaily) == `table` then Social.DialogueDaily else {}
		local Day = SchoolClock.GetState().Day
		local Id = `{NpcId}:{Key}`
		return Social.DialogueDaily[Id] ~= Day
	end
	ctx.JustCompleted = JustCompleted or (Sessions[Player] and Sessions[Player].JustCompleted) or {}
	function ctx.Offers() return Quests.Offers(Player, NpcId, true) end
	function ctx.DressLine(Clique: string): string? -- (line matrix) a clique giver turns you away for your clothes
		local Ok, Line = pcall(function()
			return require(game:GetService(`ServerScriptService`).Services.AI.StudentBrain.Talk).Line(Clique, `DressCode`, Player)
		end)
		return if Ok then Line else nil
	end
	function ctx.QuestDef(Id: string) return QuestConfig.Quests[Id] end
	function ctx.StartQuest(Id: string) return Quests.Start(Player, Id) end
	function ctx.QuestStatus(Id: string) return Quests.Status(Player, Id) end
	function ctx.QuestActive(Id: string) return Quests.IsActive(Player, Id) end
	function ctx.Objective(Id: string) return Quests.CurrentObjective(Player, Id) end
	function ctx.Has(Item: string) return Quests.HasItem(Player, Item) end
	-- (2.24.0) Decision objectives: an answer chosen here is saved (Quests.Decisions[Id]) and completes the stage
	function ctx.Decide(Id: string, Choice: string) return Quests.Decide(Player, Id, Choice) end
	function ctx.Decided(Id: string) return Quests.Decided(Player, Id) end
	function ctx.StartChampion() return Duels.StartChampion(Player) end
	-- (1.35) clique membership (Social.CliqueMembership): this NPC's clique, if they lead one of the joinable six
	ctx.CliqueId = (Npc and Npc.Clique) or (function() for _, D in QuestConfig.Quests do if D.Dare and D.Giver == NpcId then return D.Clique end end return nil end)()
	local function Membership() local Ok, M = pcall(require, game:GetService(`ServerScriptService`).Services.Social.CliqueMembership) return Ok and M or nil end
	function ctx.CliqueMember() local M = Membership() return M ~= nil and ctx.CliqueId ~= nil and M.IsMember(Player, ctx.CliqueId) end
	function ctx.CliqueCanJoin() local M = Membership() if not (M and ctx.CliqueId) then return false, `NotJoinable` end return M.CanJoin(Player, ctx.CliqueId) end
	function ctx.CliqueJoin() local M = Membership() return M ~= nil and ctx.CliqueId ~= nil and (M.Join(Player, ctx.CliqueId)) == true end
	function ctx.CliqueLeave() local M = Membership() return M ~= nil and (M.Leave(Player)) == true end
	function ctx.CliqueLine(Key: string) local C = require(ReplicatedStorage.Config.Cliques).Defs[ctx.CliqueId or ``] return C and C[Key] end
	function ctx.Joinable() local C = require(ReplicatedStorage.Config.Cliques) return ctx.CliqueId ~= nil and table.find(C.Membership.Joinable, ctx.CliqueId) ~= nil end
	function ctx.QuestData(Id: string) return Quests.DataFor(Player, Id) end
	ctx.Vars = Sessions[Player] and Sessions[Player].Vars or {} -- per-conversation scratch (e.g. which quest)
	function ctx.UseOnce(Key: string)
		local Social = Reputation.Get(Player)
		if not Social then return end
		Social.DialogueDaily = if typeof(Social.DialogueDaily) == `table` then Social.DialogueDaily else {}
		Social.DialogueDaily[`{NpcId}:{Key}`] = SchoolClock.GetState().Day
	end
	return ctx
end

function Local.Resolve(Value: any, ctx): any
	if typeof(Value) == `function` then return Value(ctx) end
	return Value
end

function Local.Close(Player: Player, Silent: boolean?)
	local S = Sessions[Player]
	if not S then return end
	Sessions[Player] = nil
	if not Silent and Player.Parent then
		Packets.DialogueEvent:FireClient(Player, { Type = `Close`; Id = S.Id })
	end
end

function Local.Show(Player: Player, S, NodeId: string?)
	local Node = NodeId and S.Tree.Nodes[NodeId]
	if not Node then
		Local.Close(Player)
		return
	end

	local ctx = Local.Context(Player, S.NpcId)
	-- (audit) a node whose Text / Choices / If errored left the client stuck on Waiting: close the talk instead
	local Ok, Text, Offered, Labels = pcall(function()
		local T = Local.Resolve(Node.Text, ctx)
		local AllChoices = Local.Resolve(Node.Choices, ctx) or {}
		local O, L = {}, {}
		for _, Choice in AllChoices do
			if not Choice.If or Choice.If(ctx) then
				table.insert(O, Choice)
				table.insert(L, Local.Resolve(Choice.Text, ctx))
			end
		end
		return T, O, L
	end)
	if not Ok then
		warn(`[Dialogue] {S.NpcId}.{NodeId}: {Text}`)
		Local.Close(Player)
		return
	end
	if #Offered == 0 then
		table.insert(Offered, { Text = `Goodbye.` })
		table.insert(Labels, `Goodbye.`)
	end

	S.NodeId = NodeId
	S.Offered = Offered

	local Npc = S.Npc
	local Faction = Npc.Faction and FactionConfig.Factions[Npc.Faction]
	local State = nil
	if RepConfig.Npcs[S.NpcId] then
		State = select(2, Reputation.Relationship(Player, S.NpcId))
	end
	Packets.DialogueEvent:FireClient(Player, {
		Type = `Node`;
		Id = S.Id;
		Speaker = Npc.Name;
		Role = Npc.Role;
		Relationship = State;
		Color = Faction and Faction.Color or Npc.Color or Color3.fromRGB(240, 240, 240);
		Text = Text;
		Choices = Labels;
		Model = S.Model; -- (1.35.1) who's talking: the client frames them (Gui.Dialogue talk cinematic)
	})
end

function Local.InRange(Player: Player, S): boolean
	local Character = Player.Character
	local Root = Character and Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	local NpcRoot = S.Model and S.Model.Parent and S.Model:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	if not Root or not NpcRoot then return false end
	local NpcHumanoid = S.Model:FindFirstChildWhichIsA(`Humanoid`)
	if not NpcHumanoid or NpcHumanoid.Health <= 0 or NpcHumanoid:GetAttribute(`Downed`) then return false end
	return (Root.Position - NpcRoot.Position).Magnitude <= MAX_DISTANCE
end

---| API |---

function Shared.Start(Player: Player, NpcId: string, Model: Model): boolean
	local Tree = Local.Tree(NpcId)
	local Npc = Cast[NpcId] or RepConfig.Npcs[NpcId]
	if not Tree or not Npc then return false end

	Local.Close(Player)
	local S = { Id = HttpService:GenerateGUID(false); NpcId = NpcId; Npc = Npc; Tree = Tree; Model = Model; Vars = {} }
	if not Local.InRange(Player, S) then return false end
	Sessions[Player] = S

	-- Quests first: talking can finish objectives (meet someone, deliver something).
	local Ok, Completed = pcall(Quests.OnTalk, Player, NpcId)
	if not Ok then
		warn(`[Dialogue] quests: {Completed}`)
		Completed = {}
	end
	S.JustCompleted = Completed

	local ctx = Local.Context(Player, NpcId, Completed)
	Local.Show(Player, S, Tree.Start(ctx))
	return true
end

function Shared.IsTalking(Player: Player): boolean
	return Sessions[Player] ~= nil
end

function Shared.Close(Player: Player)
	Local.Close(Player)
end

-- Testing (TestBridge): current node + offered choice labels, and choosing by index.
function Shared.PeekForTests(Player: Player)
	local S = Sessions[Player]
	if not S then return nil end
	local Labels = {}
	local ctx = Local.Context(Player, S.NpcId)
	for _, Choice in S.Offered do table.insert(Labels, Local.Resolve(Choice.Text, ctx)) end
	return { Node = S.NodeId; Choices = Labels; Id = S.Id }
end

function Local.OnAction(Player: Player, Message)
	local S = Sessions[Player]
	if not S or typeof(Message) ~= `table` or Message.Id ~= S.Id then return end

	if Message.Close then
		Local.Close(Player, true)
		return
	end

	local Index = Message.Choice
	local Choice = typeof(Index) == `number` and S.Offered and S.Offered[Index]
	if not Choice then return end
	if not Local.InRange(Player, S) then
		Local.Close(Player)
		return
	end

	local ctx = Local.Context(Player, S.NpcId)
	-- Re-check the condition: state may have changed since the menu was shown.
	if Choice.If and not Choice.If(ctx) then
		Local.Show(Player, S, S.NodeId)
		return
	end

	local NextId = Choice.Next
	if Choice.Do then
		local Ok, Result = pcall(Choice.Do, ctx)
		if not Ok then
			warn(`[Dialogue] {S.NpcId}.{S.NodeId}: {Result}`)
		elseif typeof(Result) == `string` then
			NextId = Result
		end
	end

	if Sessions[Player] ~= S then return end -- closed meanwhile
	if NextId then
		Local.Show(Player, S, NextId)
	else
		Local.Close(Player)
	end
end

function Shared.ChooseForTests(Player: Player, Index: number)
	local S = Sessions[Player]
	if not S then return false end
	Local.OnAction(Player, { Id = S.Id; Choice = Index })
	return true
end

function Shared.OnStart()
	Packets.DialogueAction.OnServerEvent:Connect(function(Player, Message)
		local Ok, Err = pcall(Local.OnAction, Player, Message)
		if not Ok then warn(`[Dialogue] {Err}`) end
	end)
	Players.PlayerRemoving:Connect(function(Player) Sessions[Player] = nil end)

	task.spawn(function()
		while true do
			task.wait(1)
			for Player, S in Sessions do
				if not Player.Parent or not Local.InRange(Player, S) then
					Local.Close(Player)
				end
			end
		end
	end)
end

return Shared
]==] })
table.insert(Items, { Path = {"ServerStorage", "Dialogue", "GiverTemplate"}; Source = [==[
--[[
	Shared tree for ordinary students who give quests (no saved relationship).
	L = {
		Greeting = string | fn(ctx),
		PathGreeting = { Path, Tier, Text }?,   -- (2.31) said first once the student has that Standing Path tier
		Talk = { { Ask, Answer } },            -- small talk
		Extra = { choice, ... }?,              -- NPC-specific replies (may use If / Do)
		Nodes = { [id] = node }?,              -- nodes those replies lead to
		Bye = string,
	}
]]

local QuestChoices = require(script.Parent.QuestChoices)

return function(L)
	local Nodes = {}
	local QuestMenu = QuestChoices(Nodes, `Hub`)
	local Bye = { Text = L.Bye or `See you.` }

	for Id, Node in L.Nodes or {} do Nodes[Id] = Node end

	local TalkChoices = {}
	for Index, Pair in L.Talk or {} do
		Nodes[`Talk{Index}`] = { Text = Pair.Answer; Choices = { { Text = `Huh.`; Next = `Hub` }, Bye } }
		table.insert(TalkChoices, { Text = Pair.Ask; Next = `Talk{Index}` })
	end

	-- (1.35) clique leaders (the joinable six): "I want to join you." / "I'm out." (Social.CliqueMembership)
	local Refuse = {
		NotRespected = `Earn it first. Come back when my people respect you.`;
		NotBeaten = `Respect's one thing. You haven't beaten me yet. Ask me for a showdown.`;
		OtherClique = `You already run with another crowd. Leave them first.`;
		AlreadyMember = `You're already one of us.`;
	}
	for Code, Line in Refuse do Nodes[`CJ_{Code}`] = { Text = Line; Choices = { { Text = `Fair enough.`; Next = `Hub` }, Bye } } end
	Nodes.CJ_Unknown = { Text = `...Not now.`; Choices = { { Text = `Okay.`; Next = `Hub` }, Bye } }
	Nodes.CJ_Joined = { Text = function(ctx) return ctx.CliqueLine(`Joined`) or `Welcome.` end; Choices = { { Text = `Thanks.`; Next = `Hub` }, Bye } }
	Nodes.CJ_Confirm = {
		Text = `You want out? You know what that means. Walk away now and we're done. For good.`;
		Choices = {
			{ Text = `I'm sure. I'm out.`; Do = function(ctx) return if ctx.CliqueLeave() then `CJ_Left` else `Hub` end };
			{ Text = `Forget I said anything.`; Next = `Hub` };
		};
	}
	Nodes.CJ_Left = { Text = function(ctx) return ctx.CliqueLine(`Betrayed`) or `Get out.` end; Choices = { Bye } }
	local MemberChoices = {
		{
			Text = `I want to join you.`;
			If = function(ctx) return ctx.Joinable and ctx.Joinable() and not ctx.CliqueMember() end;
			Do = function(ctx)
				local Ok, Code = ctx.CliqueCanJoin()
				if Ok then return if ctx.CliqueJoin() then `CJ_Joined` else `Hub` end
				return if Nodes[`CJ_{Code}`] then `CJ_{Code}` else `CJ_Unknown`
			end;
		};
		{ Text = `I'm out.`; If = function(ctx) return ctx.Joinable and ctx.Joinable() and ctx.CliqueMember() end; Next = `CJ_Confirm` };
	}

	Nodes.Hub = {
		Text = function(ctx) -- (2.31) a Standing Path line first, once the student has earned it
			local PG = L.PathGreeting
			if PG and ctx.PathTier and ctx.PathTier(PG.Path) >= PG.Tier then return PG.Text end
			if typeof(L.Greeting) == `function` then return L.Greeting(ctx) end
			return L.Greeting
		end;
		Choices = function(ctx)
			local List = {}
			for _, Choice in QuestMenu.Choices(ctx) do table.insert(List, Choice) end
			for _, Choice in MemberChoices do table.insert(List, Choice) end
			for _, Choice in L.Extra or {} do table.insert(List, Choice) end
			for _, Choice in TalkChoices do table.insert(List, Choice) end
			table.insert(List, Bye)
			return List
		end;
	}

	return {
		Start = function(ctx)
			return QuestMenu.Start(ctx) or `Hub`
		end;
		Nodes = Nodes;
	}
end
]==] })
table.insert(Items, { Path = {"ServerStorage", "Dialogue", "LeaderTemplate"}; Source = [==[
--[[
	Shared dialogue tree for faction leaders. Each leader module passes its own lines (L) and
	gets back a full tree (see Services.Social.Dialogue for the format).

	L = {
		Intro, About, Lore, Hostile, Apology, Insulted, LeaveConfirm, Left, Joined,
		Hub = { Rival, Acquaintance, Friendly, Trusted, Hostile }, HubMember = fn(ctx), PathHub = { Path, Tier, Text }? ((2.31) a Standing Path line first),
		Join = { RivalMember, NotNoticed, Initiation = fn(ctx), Cooldown, AlreadyMember },
		Mission = fn(ctx, Count), MissionDone,
		Ask = { About, Join, Work, Lore, Sorry, Insult, Leave, Bye } -- player lines
	}
]]

local QuestChoices = require(script.Parent.QuestChoices)

return function(L)
	local Ask = L.Ask
	local Nodes = {}
	local QuestMenu = QuestChoices(Nodes, `Hub`)

	local function Back(Text: string?)
		return { Text = Text or `Back.`; Next = `Hub` }
	end
	local Bye = { Text = Ask.Bye }

	local function Friendly(ctx)
		local State = ctx.State()
		return State == `Friendly` or State == `Trusted` or ctx.Member()
	end

	Nodes.Intro = {
		Text = L.Intro;
		Choices = {
			{ Text = Ask.About; Next = `About` };
			{ Text = `Just looking around.`; Next = `Hub` };
		};
	}

	Nodes.Hub = {
		Text = function(ctx)
			if L.PathHub and ctx.PathTier and ctx.PathTier(L.PathHub.Path) >= L.PathHub.Tier then return L.PathHub.Text end -- (2.31)
			if ctx.Member() then return L.HubMember(ctx) end
			return L.Hub[ctx.State()] or L.Hub.Acquaintance
		end;
		Choices = function(ctx)
			local List = table.clone(Nodes.Hub.Base)
			local Bye = table.remove(List) -- keep Goodbye last
			for _, Choice in QuestMenu.Choices(ctx) do table.insert(List, Choice) end
			table.insert(List, Bye)
			return List
		end;
		Base = {
			{ Text = Ask.About; Next = `About` };
			{
				Text = Ask.Join;
				If = function(ctx) return not ctx.Member() end;
				Do = function(ctx)
					local Ok, Code = ctx.CanJoin()
					if Ok then return if ctx.Join() then `Joined` else `Hub` end
					return `Join_{Code}`
				end;
			};
			{ Text = Ask.Work; If = function(ctx) return ctx.Member() end; Next = `Mission` };
			{ Text = Ask.Lore; If = Friendly; Next = `Lore` };
			{
				Text = Ask.Sorry;
				If = function(ctx) return ctx.Value() < 0 and ctx.Once(`Apology`) end;
				Do = function(ctx)
					ctx.UseOnce(`Apology`)
					ctx.Rel(8, `They accepted your apology.`)
					return `Apology`
				end;
			};
			{
				Text = Ask.Insult;
				If = function(ctx) return not ctx.Member() end;
				Do = function(ctx)
					ctx.Rel(-10, `You insulted them.`)
					return `Insulted`
				end;
			};
			{ Text = Ask.Leave; If = function(ctx) return ctx.Member() end; Next = `LeaveConfirm` };
			Bye;
		};
	}

	Nodes.About = { Text = L.About; Choices = { Back(`I see.`), Bye } }
	Nodes.Lore = { Text = L.Lore; Choices = { Back(`...Right.`), Bye } }
	Nodes.Apology = { Text = L.Apology; Choices = { Back(), Bye } }
	Nodes.Insulted = { Text = L.Insulted; Choices = { Bye } }
	Nodes.Joined = { Text = L.Joined; Choices = { Back(`Thank you.`), Bye } }

	for Code, Line in L.Join do
		Nodes[`Join_{Code}`] = { Text = Line; Choices = { Back(`Fine.`), Bye } }
	end
	Nodes.Join_Unknown = { Text = `...Not now.`; Choices = { Back(), Bye } }
	-- (1.35) one crowd at a time (Social.CliqueMembership)
	Nodes.Join_CliqueMember = Nodes.Join_CliqueMember or { Text = `You already run with another crowd. Come back when you've left them.`; Choices = { Back(`Fine.`), Bye } }

	Nodes.Mission = {
		Text = function(ctx)
			local Done, Count = ctx.MissionStatus()
			if Done then return L.MissionDone end
			return L.Mission(ctx, Count)
		end;
		Choices = { Back(`On it.`), Bye };
	}

	Nodes.LeaveConfirm = {
		Text = L.LeaveConfirm;
		Choices = {
			{ Text = `Yes. I'm out.`; Do = function(ctx) return if ctx.Leave() then `Left` else `Hub` end };
			Back(`No, forget it.`);
		};
	}
	Nodes.Left = { Text = L.Left; Choices = { Bye } }

	Nodes.Hostile = {
		Text = L.Hostile;
		Choices = {
			{
				Text = Ask.Sorry;
				If = function(ctx) return ctx.Once(`Apology`) end;
				Do = function(ctx)
					ctx.UseOnce(`Apology`)
					ctx.Rel(8, `They accepted your apology.`)
					return if ctx.State() == `Hostile` then `Hostile` else `Apology`
				end;
			};
			Bye;
		};
	}

	return {
		Start = function(ctx)
			local First = not ctx.Met()
			ctx.Meet()
			if First then return `Intro` end
			local Thanks = QuestMenu.Start(ctx)
			if Thanks then return Thanks end
			if ctx.State() == `Hostile` then return `Hostile` end
			return `Hub`
		end;
		Nodes = Nodes;
	}
end
]==] })
table.insert(Items, { Path = {"ServerStorage", "Dialogue", "Sallow"}; Source = [==[
-- Ms. Sallow (2.28). Mathematics, Room 102. Exact, dry; keeps a ruler she never uses.
local Template = require(script.Parent.GiverTemplate)

return Template({
	PathGreeting = { Path = `Academic`; Tier = 3; Text = `The honor student. Sit where I can see your working.` }; -- (2.31) Standing Paths
	Greeting = `You're early, or you're late. Which?`;
	Bye = `Mind the margins.`;
	Talk = {
		{ Ask = `What are we doing in class?`; Answer = `Proofs. Everything in this school wants proving.` };
		{ Ask = `Why do you carry a ruler?`; Answer = `Lines should be straight. Very little here is.` };
		{ Ask = `Did you teach Mira Holt?`; Answer = `The register says I didn't. The register is usually right.` };
	};
})
]==] })
table.insert(Items, { Path = {"ServerStorage", "Dialogue", "Pryce"}; Source = [==[
-- Mr. Pryce (2.28). English, Room 104. Theatrical; reads the register as if it were a play; kind to the quiet ones.
local Template = require(script.Parent.GiverTemplate)

return Template({
	PathGreeting = { Path = `Social`; Tier = 3; Text = `Ah, the star of the corridor! Enter to applause.` }; -- (2.31) Standing Paths
	Greeting = `Ah! Enter, stage left.`;
	Bye = `Exit, pursued by homework.`;
	Talk = {
		{ Ask = `What are we reading?`; Answer = `Ghost stories. This term they're the only honest kind.` };
		{ Ask = `Why do you read the register like that?`; Answer = `Every name deserves to be said properly. Some only get the once.` };
		{ Ask = `Any advice?`; Answer = `Speak up in class. The quiet ones get forgotten here.` };
	};
})
]==] })
table.insert(Items, { Path = {"ServerStorage", "Dialogue", "Whitlock"}; Source = [==[
-- Dr. Whitlock (2.28). History, Room 105. The school's own historian: knows the False Explanation by heart, believes it.
local Template = require(script.Parent.GiverTemplate)

return Template({
	PathGreeting = { Path = `Supernatural`; Tier = 3; Text = `You've been reading the old records. Careful which ones.` }; -- (2.31) Standing Paths
	Greeting = `History is happening, you know. Sit down for it.`;
	Bye = `Mind the dates.`;
	Talk = {
		{ Ask = `How old is the school?`; Answer = `Founded 1887. A fire at the north gate that same year. Tragic. Well documented.` };
		{ Ask = `What happened to the students in the fire?`; Answer = `Transferred. It's all in the records. Every one of them.` };
		{ Ask = `Who's in the old painting?`; Answer = `The Class of 1887. All present and accounted for.` };
	};
})
]==] })
table.insert(Items, { Path = {"ServerStorage", "Dialogue", "Ezra"}; Source = [==[
-- Ezra Vale, Vigil Captain. Found in the Library Archive.
local Template = require(script.Parent.LeaderTemplate)

return Template({
	PathHub = { Path = `Academic`; Tier = 3; Text = `Honor Student now. The Vigil notices names like yours.` }; -- (2.31) Standing Paths
	Intro = `Shh. The Archive is closed after hours, which is exactly why we're here. Ezra Vale. I keep the Vigil.`;
	About = `The Vigil keeps the lamps lit. We read what this school files away, and we keep watch when the halls go dark. Pass your classes and come to Night Study, and people here will learn your name. Skipping class won't help you.`;
	Lore = `The bell in the east wing rings at hours nobody scheduled. We write every one down. One day the pattern will mean something.`;
	Hostile = `We have nothing to say to each other. The door is behind you.`;
	Apology = `...Fine. Everyone gets one bad night.`;
	Insulted = `Then go burn your candle with the Court. Mind the door on your way out.`;
	Joined = `Then take a candle. Keep it lit, and keep your eyes open. Welcome to the Vigil.`;
	LeaveConfirm = `Leaving? Your candle goes out with you, and so does half of what you've earned here. You're sure?`;
	Left = `Then I hope you never need us.`;

	Hub = {
		Hostile = `You've got nerve showing your face in here.`;
		Rival = `Keep your voice down and your hands where I can see them.`;
		Acquaintance = `Need something? Keep it quiet.`;
		Friendly = `Good to see you. The candles are holding tonight.`;
		Trusted = `There you are. I saved you a seat by the lamp.`;
	};
	HubMember = function(ctx)
		return `{ctx.Rank()}. Anything to report from the halls?`
	end;

	Join = {
		RivalMember = `You wear the Court's colours and you want a seat at this table? Cut ties with Vesper first.`;
		NotNoticed = `Nobody here knows your name yet. Pass a few classes, sit in on Night Study, then ask me again.`;
		Initiation = function(ctx)
			return `Show me you can do the work. {ctx.Faction.Initiation.Text} Then we'll talk.`
		end;
		Cooldown = `You walked out on us. Give it a day before you knock again.`;
		AlreadyMember = `You're already one of us.`;
	};

	Mission = function(ctx, Count)
		local M = ctx.MissionDef
		return `{M.Name}. {M.Text} You've managed {Count} of 3 today.`
	end;
	MissionDone = `You already earned your Lamplighter title. The lamps burn brighter for it.`;

	Ask = {
		About = `What is the Vigil?`;
		Join = `I want in.`;
		Work = `Any work for me?`;
		Lore = `Seen anything strange lately?`;
		Sorry = `About last time... I'm sorry.`;
		Insult = `Your candle club is a joke.`;
		Leave = `I'm done with the Vigil.`;
		Bye = `See you around.`;
	};
})
]==] })
table.insert(Items, { Path = {"ServerStorage", "Dialogue", "Vesper"}; Source = [==[
-- Vesper Crane, Regent of the Crimson Court. Found in the Boiler Yard.
local Template = require(script.Parent.LeaderTemplate)

return Template({
	PathHub = { Path = `Combat`; Tier = 3; Text = `Enforcer. The Court has been hearing your name.` }; -- (2.31) Standing Paths
	Intro = `Well. A new face in the Boiler Yard. Vesper Crane. The Court sees everything that happens after dark... and most of what happens before it.`;
	About = `The Crimson Court runs this place when the lights go out. We mark our walls and we make the hall monitors look slow. Paint a sigil without being seen, give a monitor the slip, put someone on the floor. That's how you rise.`;
	Lore = `The basement doors lock from the inside. Every night. Nobody on staff has a key. Funny, isn't it?`;
	Hostile = `Nothing to discuss. Walk away while you still can.`;
	Apology = `Cute. I'll let it slide. Once.`;
	Insulted = `Careful. People who talk like that find a sigil on their locker.`;
	Joined = `Then you're ours. Wear the crimson, and never apologise for it.`;
	LeaveConfirm = `Walking out on the Court? Half of what you've earned stays here with me. Sure?`;
	Left = `Run along, then. The night remembers.`;

	Hub = {
		Hostile = `You've got a death wish, wandering down here.`;
		Rival = `Smells like candle wax. What do you want?`;
		Acquaintance = `Make it quick. The boilers get loud.`;
		Friendly = `Ah, you again. Pull up a crate.`;
		Trusted = `My favourite troublemaker. Sit.`;
	};
	HubMember = function(ctx)
		return `{ctx.Rank()}. Bring me good news.`
	end;

	Join = {
		RivalMember = `Still got Vigil wax on your sleeves? Blow out their candle first.`;
		NotNoticed = `Nobody's whispering your name yet. Give them a reason to.`;
		Initiation = function(ctx)
			return `Prove it. {ctx.Faction.Initiation.Text} The marked walls are all over campus.`
		end;
		Cooldown = `You left. Come crawling back tomorrow, maybe.`;
		AlreadyMember = `You're already wearing our colours.`;
	};

	Mission = function(ctx, Count)
		local M = ctx.MissionDef
		return `{M.Name}. {M.Text} This period: {Count} of 3.`
	end;
	MissionDone = `Night Prowler. I keep hearing your name in the halls. Good.`;

	Ask = {
		About = `What is the Crimson Court?`;
		Join = `I want in.`;
		Work = `Got a job for me?`;
		Lore = `Heard any rumours?`;
		Sorry = `About last time... my bad.`;
		Insult = `You're just kids playing vampire.`;
		Leave = `I'm leaving the Court.`;
		Bye = `Later.`;
	};
})
]==] })
table.insert(Items, { Path = {"ServerScriptService", "Services", "Studio", "TestBridge"}; Source = [==[
--[[
	TestBridge (Studio only)

	Lives under Services.Studio, so ModuleLoader only starts it inside Studio.
	Creates ServerStorage.NHTestBridge (BindableFunction) so test tooling can run
	checks inside the game's own module instances (same require cache as the game).

	Usage (server): ServerStorage.NHTestBridge:Invoke("Command", ...)
]]

---| Services |---

local Players = game:GetService(`Players`)
local RunService = game:GetService(`RunService`)
local ServerStorage = game:GetService(`ServerStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local Shared = {}
local Commands = {}

local function GetAI()
	return require(ServerScriptService.Services.AI.AI)
end

-- Prefers characters that EntityLoader has initialized (they get an Accessory folder).
local function FindCharacter(Name: string): Model?
	local Fallback = nil
	for _, Model in workspace.Live:GetChildren() do
		if Model.Name == Name and Model:FindFirstChildWhichIsA(`Humanoid`) then
			if Model:FindFirstChild(`Accessory`) then
				return Model
			end
			Fallback = Fallback or Model
		end
	end
	return Fallback
end

local function Describe(Model: Model)
	local Humanoid = Model:FindFirstChildWhichIsA(`Humanoid`)
	local Root = Model:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	return {
		Name = Model.Name;
		Health = Humanoid and Humanoid.Health;
		Equip = Humanoid and Humanoid:GetAttribute(`Equip`);
		Posture = Humanoid and Humanoid:GetAttribute(`Posture`);
		WalkSpeed = Humanoid and Humanoid.WalkSpeed;
		Position = Root and Root.Position;
	}
end

-- Spawn AI NPCs through the real AI service.
function Commands.SpawnAI(Count: number?, Position: Vector3?, ConfigOverrides: { [string]: any }?)
	local AI = GetAI()
	local Config = table.clone(require(ReplicatedStorage.Config.NPC).Default)
	for Key, Value in ConfigOverrides or {} do
		Config[Key] = Value
	end

	local Names = {}
	for Index = 1, Count or 1 do
		local Npc = AI.Spawn(workspace.Live, script, nil, Config)
		if Npc and Npc.Character then
			if Position then
				Npc.Character:PivotTo(CFrame.new(Position + Vector3.new(Index * 4, 0, 0)))
			end
			table.insert(Names, Npc.Character.Name)
		end
	end
	return Names
end

-- Snapshot of every active AI NPC.
-- 1.23 enemy tests: make an NPC fight a given character (threat), and read its counters
function Commands.AIThreat(NpcName: string, AttackerName: string, Amount: number?)
	local Npc, Attacker = FindCharacter(NpcName), FindCharacter(AttackerName)
	if not (Npc and Attacker) then return false end
	GetAI().AddThreat(Npc, Attacker, Amount or 500)
	return true
end

function Commands.AIStats(NpcName: string)
	local Npc = FindCharacter(NpcName)
	if not Npc then return nil end
	local Out = { Tier = Npc:GetAttribute(`Difficulty`) }
	for K, V in Npc:GetAttributes() do
		local Key = K:match(`^NHStat_(.+)`)
		if Key then Out[Key] = V end
	end
	local H = Npc:FindFirstChildWhichIsA(`Humanoid`)
	Out.Health = H and math.floor(H.Health)
	return Out
end

-- 1.27 cliques Phase 2: start a scuffle or a confrontation by hand, and read what's going on
function Commands.Scuffle(Defender: string, Attacker: string)
	return require(ServerScriptService.Services.Social.CliqueFights).StartScuffle(Defender, Attacker)
end
function Commands.Confront(PlayerName: string, Clique: string)
	return require(ServerScriptService.Services.Social.CliqueFights).Confront(Players:FindFirstChild(PlayerName), Clique, -80)
end
function Commands.TurfWin(Owner: string, Rival: string, Winner: string) -- 1.28: count a scuffle result toward turf
	return require(ServerScriptService.Services.Social.CliqueFights).RecordWin(Owner, Rival, Winner, nil)
end
function Commands.FightState()
	return require(ServerScriptService.Services.Social.CliqueFights).State()
end
-- 1.33 cliques Phase 4: pranks, rumbles, dares, the bulletin
local function Pranks() return require(ServerScriptService.Services.Social.CliquePranks) end
local function Events() return require(ServerScriptService.Services.Social.CliqueEvents) end
function Commands.Prank(By: string, Victim: string) return Pranks().NpcPrank(By, Victim) end
function Commands.PrankMine(PlayerName: string, Victim: string, UseKit: boolean?) -- UseKit: spend a real kit (else skip it)
	return Pranks().PlayerPrank(Players:FindFirstChild(PlayerName), Victim, not UseKit)
end
function Commands.Messes() return Pranks().State() end
function Commands.PrankHit(PlayerName: string, Down: boolean?) return Pranks().TestHit(Players:FindFirstChild(PlayerName), Down) end
function Commands.CleanAll() Pranks().CleanAll() return true end
function Commands.Rumble(A: string, B: string, Now: boolean?) -- Now: start it now; else plan it for tomorrow (texts everyone)
	local F = require(ServerScriptService.Services.Social.CliqueFights)
	if Now then return F.StartRumble(A, B) end
	return F.PlanRumble(A, B)
end
function Commands.RumbleState() return require(ServerScriptService.Services.Social.CliqueFights).Rumble() end
function Commands.Dares(PlayerName: string) return Events().SendDares(Players:FindFirstChild(PlayerName), true) end
function Commands.Today(PlayerName: string) return Events().Today(Players:FindFirstChild(PlayerName)) end
function Commands.DareFor(Leader: string) return require(ServerScriptService.Services.Quests.Quests).DareFor(Leader) end
-- 1.34 cliques Phase 5: showdowns
local function Showdowns() return require(ServerScriptService.Services.Social.CliqueShowdowns) end
function Commands.Showdown(PlayerName: string, Clique: string, Path: string?) return Showdowns().StartFight(Players:FindFirstChild(PlayerName), Clique, Path) end
function Commands.ShowdownState() return Showdowns().State() end
function Commands.ShowdownHurt(Clique: string, Amount: number) return Showdowns().HurtForTests(Clique, Amount) end
function Commands.ShowdownWin(PlayerName: string, Clique: string) return Showdowns().WinForTests(Players:FindFirstChild(PlayerName), Clique) end
function Commands.CanShowdown(PlayerName: string, Clique: string) return Showdowns().CanChallenge(Players:FindFirstChild(PlayerName), Clique) end
-- 1.35 cliques Phase 6: membership. MemberTest treats a no-slot player as a member at a rank (nothing saved); nil clique ends it.
local function Membership() return require(ServerScriptService.Services.Social.CliqueMembership) end
function Commands.MemberTest(PlayerName: string, Clique: string?, Rank: string?) return Membership().TestMember(Players:FindFirstChild(PlayerName), Clique, Rank) end
function Commands.MemberState(PlayerName: string)
	local P = Players:FindFirstChild(PlayerName)
	local M = Membership()
	local Crew = 0
	for _, C in (workspace:FindFirstChild(`Live`) and workspace.Live:GetChildren() or {}) do if C:GetAttribute(`NHCrewOf`) == P.UserId then Crew += 1 end end
	return { Current = M.Current(P); Rank = M.Rank(P); Crew = Crew; NHClique = P:GetAttribute(`NHClique`); Summary = M.Summary(P) }
end
-- (1.38.3) CliqueCanJoin: a second Commands.CanJoin (the factions one, further down) used to replace this one
function Commands.CliqueCanJoin(PlayerName: string, Clique: string) return { Membership().CanJoin(Players:FindFirstChild(PlayerName), Clique) } end
function Commands.GuardDuty(PlayerName: string, Clique: string) return require(ServerScriptService.Services.Social.CliquePranks).GuardDuty(Players:FindFirstChild(PlayerName), Clique) end

-- 1.39 bundle 1: the daily special, the superlatives, the notice board
local function Sup() return require(ServerScriptService.Services.Social.Superlatives) end
function Commands.SupCount(PlayerName: string, Id: string, N: number?) Sup().Count(Players:FindFirstChild(PlayerName), Id, N) return Sup().State(Players:FindFirstChild(PlayerName)) end
function Commands.SupFlush() return Sup().FlushForTests() end
function Commands.SupFetch(Week: number?) return Sup().FetchForTests(Week) end
function Commands.SupAward(PlayerName: string) return Sup().AwardForTests(Players:FindFirstChild(PlayerName)) end
function Commands.SupState(PlayerName: string) return Sup().State(Players:FindFirstChild(PlayerName)) end
function Commands.BoardRefresh() return require(ServerScriptService.Services.Features.NoticeBoard).RefreshForTests() end
-- 1.40 report cards
local function Reports() return require(ServerScriptService.Services.School.ReportCards) end
function Commands.ReportClass(PlayerName: string, Subject: string, Status: string, Grade: string?) Reports().Class(Players:FindFirstChild(PlayerName), Subject, Status, Grade) return Reports().State(Players:FindFirstChild(PlayerName)) end
function Commands.ReportViolation(PlayerName: string) Reports().Violation(Players:FindFirstChild(PlayerName)) return true end
function Commands.ReportState(PlayerName: string) return Reports().State(Players:FindFirstChild(PlayerName)) end
function Commands.ReportList(PlayerName: string) return Reports().List(Players:FindFirstChild(PlayerName)) end
function Commands.ReportDeliver(PlayerName: string) return Reports().DeliverForTests(Players:FindFirstChild(PlayerName)) end -- hand out this week's card now
-- 1.42 Lost & Found
local function Lost() return require(ServerScriptService.Services.Features.LostFound) end
function Commands.LostSpawn(Id: string?, At: Vector3?) local M = Lost().SpawnForTests(Id, At and CFrame.new(At)) return M and M:GetFullName() end
function Commands.LostState() return Lost().State() end
-- 1.45 the fortune teller
local function Fortune() return require(ServerScriptService.Services.Features.Fortune) end
function Commands.FortuneRead(PlayerName: string, Card: string?) return Fortune().ReadForTests(Players:FindFirstChild(PlayerName), Card) end
function Commands.FortuneReset(PlayerName: string) return Fortune().ResetForTests(Players:FindFirstChild(PlayerName)) end
function Commands.FortuneHints(PlayerName: string) return Fortune().Hints(Players:FindFirstChild(PlayerName)) end
function Commands.FortuneToday(PlayerName: string) return Fortune().Today(Players:FindFirstChild(PlayerName)) end
function Commands.FortuneStanding(PlayerName: string, Id: string, Value: number?) return Fortune().StandingForTests(Players:FindFirstChild(PlayerName), Id, Value) end
function Commands.TodaySpecial() local It = require(ReplicatedStorage.Config.Items).TodaySpecial() return It and It.Id end
function Commands.AIStatus()
	local Result = {}
	for _, Npc in GetAI().GetActive() do
		if not Npc.Character then continue end
		local Info = Describe(Npc.Character)
		Info.State = Npc.State
		Info.Target = Npc.Target and Npc.Target.Name
		Info.Action = Npc.ActionManager and Npc.ActionManager.Action
		table.insert(Result, Info)
	end
	return Result
end

function Commands.DestroyAI()
	GetAI().DestroyAll()
	return true
end

-- Current action + states for any character in Live.
function Commands.Inspect(Name: string)
	local Model = FindCharacter(Name)
	if not Model then return nil end

	local ActionManager = require(ServerScriptService.Services.Player.ActionManager)
	local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
	local TagService = require(ReplicatedStorage.Packages.Core.TagService)

	local States = {}
	for _, State in StateManager.getEntityCache(Model).States do
		table.insert(States, State.Name)
	end

	local Info = Describe(Model)
	Info.Action = ActionManager.new(Model).Action
	Info.States = States
	Info.Tags = TagService:ReturnTags(Model)
	return Info
end

-- Make a character perform an action through the real ActionManager (server side).
function Commands.DoAction(Name: string, Action: string, ...)
	local Model = FindCharacter(Name)
	if not Model then return false end

	local ActionManager = require(ServerScriptService.Services.Player.ActionManager)
	if Action == `M1` then
		ActionManager.M1(Model)
		return true
	end
	return ActionManager.new(Model):Activate(Action, ...) == true
end

---| Downed / Carry / Grip |---

local function GetDowned()
	return require(ServerScriptService.Services.Features.Downed)
end

-- Deal damage through the real combat damage entry point (can down the target).
function Commands.Damage(Name: string, Amount: number, AttackerName: string?)
	local Target = FindCharacter(Name)
	if not Target then return nil end
	return GetDowned().ApplyDamage(Target, Amount, AttackerName and FindCharacter(AttackerName) or nil)
end

function Commands.ToggleCarry(ActorName: string)
	local Actor = FindCharacter(ActorName)
	return Actor and GetDowned().ToggleCarry(Actor)
end

function Commands.Grip(ActorName: string)
	local Actor = FindCharacter(ActorName)
	return Actor and GetDowned().StartGrip(Actor)
end

function Commands.Recover(Name: string)
	local Target = FindCharacter(Name)
	if Target then GetDowned().Recover(Target) end
	return Target ~= nil
end

local EventLog = {}
local Recording = false

function Commands.RecordEvents()
	table.clear(EventLog)
	if Recording then return true end
	Recording = true

	local function Log(Text: string)
		table.insert(EventLog, string.format("%.2f %s", os.clock(), Text))
	end
	local function NameOf(Model: Model?) return Model and Model.Name or "nil" end

	local Downed = GetDowned()
	Downed.OnDowned:Connect(function(Target, Attacker) Log(`Downed {NameOf(Target)} by {NameOf(Attacker)}`) end)
	Downed.OnRecovered:Connect(function(Target) Log(`Recovered {NameOf(Target)}`) end)
	Downed.OnExecuted:Connect(function(Gripper, Target) Log(`Executed {NameOf(Target)} by {NameOf(Gripper)}`) end)
	Downed.OnDefeated:Connect(function(Target, Killer) Log(`Defeated {NameOf(Target)} killer={NameOf(Killer)}`) end)
	GetAI().NPCDefeated:Connect(function(Npc, Killer) Log(`NPCDefeated {NameOf(Npc)} killer={NameOf(Killer)}`) end)
	return true
end

function Commands.Events()
	return table.clone(EventLog)
end

---| Player data |---

-- Read-only copy of a player's saved profile data.
function Commands.Profile(PlayerName: string)
	local Player = Players:FindFirstChild(PlayerName)
	if not Player then return nil end
	local Data = require(ServerScriptService.Services.Player.Data).GetProfile(Player)
	return Data and table.clone(Data)
end

---| School clock |---

---| Combat log (2.13.0, combat concept 14) |---

function Commands.CombatLog(Count: number?)
	return require(ServerStorage.Packages.CombatLog).Get(Count)
end

function Commands.CombatLogClear()
	require(ServerStorage.Packages.CombatLog).Clear()
	return true
end

function Commands.SetTime(TimeText: string, Day: number?)
	require(ServerScriptService.Services.School.SchoolClock).SetTime(TimeText, Day)
	return true
end

function Commands.ClockState()
	local Clock = require(ServerScriptService.Services.School.SchoolClock)
	local State = Clock.GetState()
	return {
		Day = State.DayName;
		Time = State.ClockText;
		Period = State.Segment.Name;
		Kind = State.Segment.Kind;
		MinutesLeft = State.MinutesLeft;
		SchoolHours = State.IsSchoolHours;
		ExpMultiplier = Clock.GetExpMultiplier();
		LightingClockTime = game:GetService(`Lighting`).ClockTime;
	}
end

function Commands.SetClockSpeed(RealSecondsPerGameHour: number)
	require(ServerScriptService.Services.School.SchoolClock).SetSpeed(RealSecondsPerGameHour)
	return true
end

function Commands.Notify(PlayerName: string, Title: string, Text: string?, Kind: string?)
	local Player = Players:FindFirstChild(PlayerName)
	if not Player then return false end
	require(ServerScriptService.Services.Features.Notifications).Notify(Player, { Title = Title; Text = Text; Kind = Kind })
	return true
end

---| Attendance |---

function Commands.Attendance(PlayerName: string)
	local Player = Players:FindFirstChild(PlayerName)
	local Profile = Player and require(ServerScriptService.Services.Player.Data).GetProfile(Player)
	return Profile and Profile.Attendance
end

function Commands.ResetAttendanceSession(PlayerName: string)
	local Player = Players:FindFirstChild(PlayerName)
	if not Player then return false end
	require(ServerScriptService.Services.School.Attendance).ResetSessionForTests(Player)
	return true
end

-- test cleanup: overwrite fields of the loaded slot's attendance record (Recent, Totals, ...)
function Commands.SetAttendance(PlayerName: string, Fields: { [string]: any })
	local Player = Players:FindFirstChild(PlayerName)
	local Profile = Player and require(ServerScriptService.Services.Player.Data).GetProfile(Player)
	if not (Profile and typeof(Profile.Attendance) == `table`) then return false end
	for Key, Value in Fields do Profile.Attendance[Key] = Value end
	return true
end

---| Discipline |---

function Commands.Discipline(PlayerName: string)
	local Player = Players:FindFirstChild(PlayerName)
	return Player and require(ServerScriptService.Services.School.Discipline).GetData(Player)
end

function Commands.AddViolation(PlayerName: string, Type: string)
	local Player = Players:FindFirstChild(PlayerName)
	return Player and require(ServerScriptService.Services.School.Discipline).AddViolation(Player, Type, { Witness = `Test` }) ~= nil
end

function Commands.SetDiscipline(PlayerName: string, Fields: { [string]: any })
	local Player = Players:FindFirstChild(PlayerName)
	local Data = Player and require(ServerScriptService.Services.School.Discipline).GetData(Player)
	if not Data then return false end
	for Key, Value in Fields do Data[Key] = Value end
	return true
end

function Commands.Incidents()
	local Out = {}
	for _, I in require(ServerScriptService.Services.School.Discipline).GetIncidents() do
		table.insert(Out, `{I.Time} {I.Type} suspect={I.Suspect and I.Suspect.Name} witness={I.Witness} recognized={I.Recognized}`)
	end
	return Out
end

function Commands.Monitors()
	return require(ServerScriptService.Services.School.HallMonitor).GetMonitors()
end

---| Class activities |---

-- AutoPlay (optional, 0..1): for Lab Mix, also start the auto-player at that accuracy (see AutoLab).
function Commands.StartLesson(PlayerName: string, RoomId: string, AutoPlay: number?)
	local Player = Players:FindFirstChild(PlayerName)
	local Started = Player and require(ServerScriptService.Services.School.Activities).StartForTests(Player, RoomId)
	if Started and AutoPlay then Commands.AutoLab(PlayerName, AutoPlay) end
	return Started
end

-- 1.47 substitute days
local function Subs() return require(ServerScriptService.Services.School.Substitutes) end
function Commands.SubForce(Subject: string, SubId: string, Twist: string?, Extra: string?, Variant: number?) return Subs().ForceForTests(Subject, SubId, Twist, Extra, Variant) end
function Commands.SubClear() return Subs().ClearForTests() end
function Commands.SubState() return Subs().State() end
function Commands.SubPickUp(PlayerName: string) return Subs().PickUpForTests(Players:FindFirstChild(PlayerName)) end
function Commands.SubHandIn(PlayerName: string) return Subs().HandInForTests(Players:FindFirstChild(PlayerName)) end
-- play Candle Vigil / Seance Sequence through the real action path (tool round trips are too slow to react)
function Commands.AutoVigil(PlayerName: string, Accuracy: number?)
	local Player = Players:FindFirstChild(PlayerName)
	local Activities = require(ServerScriptService.Services.School.Activities)
	local S = Player and Activities.GetSessionForTests(Player)
	if not S or not S.Candles then return false end
	task.spawn(function()
		local Seen = {}
		while Activities.GetSessionForTests(Player) == S do
			for I, C in S.Candles do
				if C.State == `Gutter` and not Seen[C] then
					Seen[C] = C.Until
					if math.random() <= (Accuracy or 0.9) then task.delay(0.4, function() if Activities.GetSessionForTests(Player) == S then Activities.ActionForTests(Player, `Tend`, { Index = I }) end end) end
				elseif C.State ~= `Gutter` then Seen[C] = nil end
			end
			task.wait(0.1)
		end
	end)
	return true
end
function Commands.AutoSeance(PlayerName: string, Accuracy: number?)
	local Player = Players:FindFirstChild(PlayerName)
	local Activities = require(ServerScriptService.Services.School.Activities)
	local S = Player and Activities.GetSessionForTests(Player)
	if not S or not S.Seq then return false end
	task.spawn(function()
		while Activities.GetSessionForTests(Player) == S do
			if os.clock() >= S.ShowUntil + 0.1 then
				local Want = S.Seq[S.Pos]
				local Press = if math.random() <= (Accuracy or 0.95) then Want else (Want % 6) + 1
				Activities.ActionForTests(Player, `Press`, { Index = Press })
			end
			task.wait(0.3)
		end
	end)
	return true
end

-- Testing only: play Lab Mix for a player. Tool round trips are far too slow to hit a rhythm chart, and
-- with no presses six missed notes blow the beaker ~7 s into the song (the real rule). Each note is hit
-- on its beat with probability Accuracy (default 0.85) through the real action path; the rest are missed.
function Commands.AutoLab(PlayerName: string, Accuracy: number?)
	local Player = Players:FindFirstChild(PlayerName)
	local Activities = require(ServerScriptService.Services.School.Activities)
	local S = Player and Activities.GetSessionForTests(Player)
	if not S or not S.Notes or not S.StartAt then return false end
	local Ping = 0
	pcall(function() Ping = math.clamp(Player:GetNetworkPing(), 0, 0.35) end)
	local Planned = 0
	for _, Note in S.Notes do
		if math.random() <= (Accuracy or 0.85) then
			Planned += 1
			task.delay(math.max(0, S.StartAt + Note.Time + Ping + 0.075 - os.clock()), function()
				if Activities.GetSessionForTests(Player) == S then
					Activities.ActionForTests(Player, `Hit`, { Lane = Note.Lane })
				end
			end)
		end
	end
	return { Notes = #S.Notes; Planned = Planned }
end

-- Peek at the server-side session (answers etc.) to drive a test player.
function Commands.Lesson(PlayerName: string)
	local Player = Players:FindFirstChild(PlayerName)
	local S = Player and require(ServerScriptService.Services.School.Activities).GetSessionForTests(Player)
	if not S then return nil end

	local Out = { Id = S.Id; Type = S.Def.Type; Level = S.Level; Practice = S.Practice; Index = S.Index; Answer = S.Answer; Word = S.Word; Correct = S.Correct }
	if S.Cards then
		Out.Pairs = {}
		for Index, Card in S.Cards do Out.Pairs[Index] = Card.Pair end
		Out.Matched = S.Matched
	end
	if S.Notes then
		Out.Notes = {}
		for _, Note in S.Notes do table.insert(Out.Notes, { Lane = Note.Lane; Time = Note.Time }) end
		Out.StartAt = S.StartAt
		Out.Now = os.clock()
		Out.Hits = S.Hits
	end
	return Out
end

-- Testing only: slow a lesson's per-item timer (tool round trips are slower than a human).
function Commands.SlowLesson(PlayerName: string, Seconds: number)
	local Player = Players:FindFirstChild(PlayerName)
	local S = Player and require(ServerScriptService.Services.School.Activities).GetSessionForTests(Player)
	if not S then return false end
	S.TimePer = Seconds
	S.EndsAt = os.clock() + Seconds * 12
	if S.Deadline then S.Deadline = os.clock() + Seconds end
	return true
end

function Commands.Classes(PlayerName: string)
	local Player = Players:FindFirstChild(PlayerName)
	local Profile = Player and require(ServerScriptService.Services.Player.Data).GetProfile(Player)
	return Profile and Profile.Classes
end

local PeriodLog = {}
function Commands.RecordPeriods()
	table.clear(PeriodLog)
	if not Commands._PeriodHooked then
		Commands._PeriodHooked = true
		require(ServerScriptService.Services.School.SchoolClock).PeriodChanged:Connect(function(State, Old)
			table.insert(PeriodLog, `{Old and Old.Name or "-"} -> {State.Segment.Name} at {State.ClockText}`)
		end)
	end
	return true
end

function Commands.Periods()
	return table.clone(PeriodLog)
end

---| Social (factions, reputation, dialogue) |---

local function Social() return require(ServerScriptService.Services.Social.Reputation) end
local function FactionsService() return require(ServerScriptService.Services.Social.Factions) end

local function DeepCopy(Value)
	if typeof(Value) ~= `table` then return Value end
	local Copy = {}
	for K, V in Value do Copy[K] = DeepCopy(V) end
	return Copy
end

-- Full social block + perk attributes.
function Commands.Social(PlayerName: string)
	local Player = Players:FindFirstChild(PlayerName)
	if not Player then return nil end
	local Attributes = {}
	for Name, Value in Player:GetAttributes() do
		if Name:find(`^Perk_`) or Name:find(`^Faction_`) or Name == `LessonYenBonus` or Name == `Title` then
			Attributes[Name] = Value
		end
	end
	return { Social = DeepCopy(Social().Get(Player)); Attributes = Attributes }
end

-- Wipe social data back to new-player defaults.
function Commands.ResetSocial(PlayerName: string)
	local Player = Players:FindFirstChild(PlayerName)
	local Profile = Player and require(ServerScriptService.Services.Player.Data).GetProfile(Player)
	if not Profile then return false end
	Profile.Social = nil
	Social().Get(Player)
	for Id in require(ReplicatedStorage.Config.Factions).Factions do
		FactionsService().AddStanding(Player, Id, -1000, nil, true)
	end
	Social().Sync(Player)
	return true
end

function Commands.AddStanding(PlayerName: string, Id: string, Amount: number)
	local Player = Players:FindFirstChild(PlayerName)
	FactionsService().AddStanding(Player, Id, Amount, `Test`)
	local F = FactionsService().Get(Player, Id)
	return F and { Standing = F.Standing; Rank = F.Rank; Member = F.Member }
end

function Commands.SetFlag(PlayerName: string, Id: string, Flag: string)
	FactionsService().SetFlag(Players:FindFirstChild(PlayerName), Id, Flag)
	return true
end

function Commands.AddRep(PlayerName: string, Category: string, Amount: number)
	local Player = Players:FindFirstChild(PlayerName)
	Social().Add(Player, Category, Amount, `Test`)
	return Social().Value(Player, Category)
end

function Commands.Relationship(PlayerName: string, NpcId: string, Change: number?)
	local Player = Players:FindFirstChild(PlayerName)
	if Change then Social().ChangeRelationship(Player, NpcId, Change, `Test`) end
	return { Social().Relationship(Player, NpcId) }
end

-- (2.27) the 64-entry cap's drop order, on stand-in tables (nothing saved)
function Commands.RelationshipCapTest(PlayerName: string)
	local Rep = Social()
	local Rels = {}
	-- 60 Acquaintance students, 3 Friendly, Ezra (important), 1 Hostile: 65 entries, cap 64
	for I = 1, 60 do Rels[`Ac{I}`] = { Value = 0; Met = true; Last = 1000 + I; Flags = {} } end
	for I = 1, 3 do Rels[`Fr{I}`] = { Value = 30; Met = true; Last = 10 + I; Flags = {} } end
	Rels.Ezra = { Value = 0; Met = true; Last = 1; Flags = {} }
	Rels.Ho1 = { Value = -80; Met = true; Last = 2; Flags = {} }
	local Dropped = Rep.TrimForTests(Rels, 64, 5000)
	local Count = 0 for _ in Rels do Count += 1 end
	-- no Acquaintance left: the next drop is the oldest entry that isn't Trusted, Hostile or important
	local Rels2 = {}
	for I = 1, 63 do Rels2[`Fr{I}`] = { Value = 30; Met = true; Last = 100 + I; Flags = {} } end
	Rels2.Tr = { Value = 90; Met = true; Last = 1; Flags = {} }
	Rels2.Ho = { Value = -90; Met = true; Last = 2; Flags = {} }
	local Dropped2 = Rep.TrimForTests(Rels2, 64, 5000)
	return { Dropped = Dropped; Count = Count; EzraKept = Rels.Ezra ~= nil; HostileKept = Rels.Ho1 ~= nil;
		Dropped2 = Dropped2; TrustedKept = Rels2.Tr ~= nil; HostileKept2 = Rels2.Ho ~= nil }
end

function Commands.CanJoin(PlayerName: string, Id: string)
	return { FactionsService().CanJoin(Players:FindFirstChild(PlayerName), Id) }
end

function Commands.MissionStatus(PlayerName: string, Id: string)
	return { FactionsService().MissionStatus(Players:FindFirstChild(PlayerName), Id) }
end

-- Talk to a leader (skips the prompt, keeps the server range checks).
function Commands.Talk(PlayerName: string, NpcId: string)
	local Player = Players:FindFirstChild(PlayerName)
	local Npcs = require(ServerScriptService.Services.Social.Npcs)
	return Npcs.TalkForTests(Player, NpcId)
end

function Commands.Dialogue(PlayerName: string)
	return require(ServerScriptService.Services.Social.Dialogue).PeekForTests(Players:FindFirstChild(PlayerName))
end

function Commands.Choose(PlayerName: string, Index: number)
	local Dialogue = require(ServerScriptService.Services.Social.Dialogue)
	local Player = Players:FindFirstChild(PlayerName)
	Dialogue.ChooseForTests(Player, Index)
	return Dialogue.PeekForTests(Player)
end

-- Choose by the text of the reply (first label containing Text).
function Commands.Say(PlayerName: string, Text: string)
	local Dialogue = require(ServerScriptService.Services.Social.Dialogue)
	local Player = Players:FindFirstChild(PlayerName)
	local Peek = Dialogue.PeekForTests(Player)
	if not Peek then return nil end
	for Index, Label in Peek.Choices do
		if Label:find(Text, 1, true) then
			Dialogue.ChooseForTests(Player, Index)
			return Dialogue.PeekForTests(Player) or { Closed = true }
		end
	end
	return { NotOffered = Text; Choices = Peek.Choices }
end

function Commands.LeaderModel(NpcId: string)
	local Model = require(ServerScriptService.Services.Social.Npcs).Get(NpcId)
	return Model and Describe(Model)
end

function Commands.MarkWall(PlayerName: string, WallId: string)
	return require(ServerScriptService.Services.Social.Pranks).MarkForTests(Players:FindFirstChild(PlayerName), WallId)
end

function Commands.ResetWalls(PlayerName: string)
	require(ServerScriptService.Services.Social.Pranks).ResetForTests(Players:FindFirstChild(PlayerName))
	return true
end

function Commands.NightStudy(PlayerName: string, Subject: string?, IgnoreCooldown: boolean?)
	return require(ServerScriptService.Services.Social.Hangouts).StudyForTests(Players:FindFirstChild(PlayerName), Subject, IgnoreCooldown)
end

---| Quests |---

local function QuestsService() return require(ServerScriptService.Services.Quests.Quests) end
local function Places() return require(ServerScriptService.Services.Quests.Places) end

function Commands.QuestState(PlayerName: string)
	return DeepCopy(QuestsService().StateForTests(Players:FindFirstChild(PlayerName)))
end

-- (2.22.0) New Kid's Enrol step and the saved-stage migration (quests restored afterwards)
function Commands.EnrolSelfTest(PlayerName: string)
	return DeepCopy(QuestsService().EnrolSelfTestForTests(Players:FindFirstChild(PlayerName)))
end

function Commands.ResetQuests(PlayerName: string, AutoStart: boolean?)
	local Player = Players:FindFirstChild(PlayerName)
	QuestsService().ResetForTests(Player)
	if AutoStart then QuestsService().AutoStartForTests(Player) end
	return true
end

-- (2.28) every staff post exists, and every staff member has a look and a talk tree
function Commands.StaffTest(PlayerName: string)
	local Cast = require(game:GetService(`ReplicatedStorage`).Config.Npcs)
	local Looks = require(game:GetService(`ServerScriptService`).Services.Features.NpcLooks)
	local Places = require(game:GetService(`ServerScriptService`).Services.Quests.Places)
	local Out = { Missing = {} }
	for _, Id in { `Sallow`, `Hale`, `Pryce`, `Whitlock`, `Ashgrave` } do
		local Npc = Cast[Id]
		if not Npc then table.insert(Out.Missing, `cast {Id}`) continue end
		if not Npc.Posts then table.insert(Out.Missing, `posts {Id}`) continue end
		for Slot, Key in Npc.Posts do
			if not Places.Find(`NpcPost`, Key) then table.insert(Out.Missing, `post {Id}.{Slot}={Key}`) end
		end
		if not Looks.Specs[Id] then table.insert(Out.Missing, `look {Id}`) end
		if not game:GetService(`ServerStorage`).Dialogue:FindFirstChild(Npc.Dialogue or ``) then table.insert(Out.Missing, `talk {Id}`) end
	end
	return Out
end

-- (2.28) the set rotation, homeroom rooms and skipping (pure)
function Commands.TimetableTest(PlayerName: string)
	local Roster = require(game:GetService(`ServerScriptService`).Services.Social.Roster)
	local Out = { PerRoom = {}, Homeroom = {}, Skips = 0, SkipStable = true }
	for _, Seg in { `Period 1`, `Period 2`, `Period 3`, `Period 4` } do
		local Count = {}
		for _, E in Roster.All() do
			local P = Roster.Plan(Seg, E.Id, 7)
			if P.Room then Count[P.Room] = (Count[P.Room] or 0) + 1 end
		end
		Out.PerRoom[Seg] = Count
	end
	for _, E in Roster.All() do
		local R = Roster.Plan(`Homeroom`, E.Id, 7).Room
		Out.Homeroom[R or `-`] = (Out.Homeroom[R or `-`] or 0) + 1
		for Day = 1, 40 do
			local A = Roster.Plan(`Period 3`, E.Id, Day)
			if A.Skip then Out.Skips += 1 end
			if A.Skip ~= Roster.Plan(`Period 3`, E.Id, Day).Skip then Out.SkipStable = false end
			if A.Skip and E.Clique ~= `Delinquents` then Out.SkipStable = false end
		end
	end
	Out.Seg1SetA = Roster.Plan(`Period 1`, `OdetteMarsh`, 7).Room -- set A, Period 1: R102
	Out.Seg2SetA = Roster.Plan(`Period 2`, `OdetteMarsh`, 7).Room -- set A, Period 2: R103
	return Out
end

-- (2.28) a fight in a class with its teacher at the desk is booked by that teacher; slot 2 is restored by the caller
function Commands.WitnessTest(PlayerName: string, RoomId: string)
	local Player = Players:FindFirstChild(PlayerName)
	return DeepCopy(require(game:GetService(`ServerScriptService`).Services.School.Teachers).WitnessForTests(Player, RoomId))
end

-- (2.28) bodies only near players: how many students have a body, and how many are asleep at a spot
function Commands.SleepTest(PlayerName: string)
	return DeepCopy(require(game:GetService(`ServerScriptService`).Services.Features.Schedules).SleepForTests())
end

-- (2.30) the broadcast: items roll at 40, a PA is limited to one per segment (emergencies aside), the station is on air at night
function Commands.BroadcastTest(PlayerName: string)
	local B = require(game:GetService(`ServerScriptService`).Services.World.Broadcast)
	local Player = Players:FindFirstChild(PlayerName)
	B.PATestReset()
	for I = 1, 45 do B.Post(`IncidentReport`, `Report {I}`) end
	local All = B.Items()
	local First = B.PA(`Test one.`)
	local Second = B.PA(`Test two.`)
	local Emergency = B.PA(`Emergency.`, true)
	B.PATestReset()
	local St = B.Station(Player)
	return { Count = #All; Newest = All[#All].Text; Oldest = All[1].Text; FirstPA = First; SecondPA = Second; EmergencyPA = Emergency;
		StationHasItems = #St.Items > 0; OnAirIsBool = typeof(St.OnAir) == `boolean` }
end

-- (2.30) the curfew rule at a given hour, with the player where the caller put them
function Commands.CurfewTest(PlayerName: string)
	local HM = require(game:GetService(`ServerScriptService`).Services.School.HallMonitor)
	local P = Players:FindFirstChild(PlayerName)
	local A, Why23 = HM.IsAfterHoursForTests(P, 23)
	local B, Why15 = HM.IsAfterHoursForTests(P, 15)
	local C, Why5 = HM.IsAfterHoursForTests(P, 5)
	return { At23 = A; Why23 = Why23; At15 = B; Why15 = Why15; At5 = C; Why5 = Why5 }
end

-- (2.29) the incident bus: Emit fills time, region and witnesses; On hears it; the relationship consumer applies flags
function Commands.IncidentTest(PlayerName: string)
	local SSS = game:GetService(`ServerScriptService`).Services
	local Player = Players:FindFirstChild(PlayerName)
	local Inc, Rep = require(SSS.World.Incidents), require(SSS.Social.Reputation)
	local Rels = Rep.Get(Player).Relationships
	local Saved = Rels.MaeGorse and table.clone(Rels.MaeGorse)
	local Heard = {}
	local C = Inc.On(`TestKind`, function(I) table.insert(Heard, I.Kind) end)
	local Hall = workspace.Regions:FindFirstChild(`MainHall`)
	local I = Inc.Emit({ Kind = `TestKind`; Where = Hall and Hall.Position; Who = { { Id = Player; Role = `Doer` } } })
	task.wait(0.3) -- SignalPlus delivers on the next frame
	C:Disconnect()
	local Before = Rep.Entry(Player, `MaeGorse`)
	Inc.Emit({ Kind = `Downed`; Who = { { Id = Player; Role = `Doer` }, { Id = `MaeGorse`; Role = `Target` } } })
	task.wait(0.3)
	local After = Rep.Entry(Player, `MaeGorse`)
	Rels.MaeGorse = Saved
	Rep.Sync(Player)
	return { Heard = #Heard; Region = I.Region; HasTime = typeof(I.T) == `number`; Truth = I.Truth;
		Witnesses = typeof(I.Witnesses) == `table`; FoughtAdded = (After.Flags.Fought or 0) - (Before.Flags.Fought or 0);
		ValueDelta = After.Value - Before.Value; Recent = #Inc.Recent(5) }
end

-- (2.29) rumours from incidents, their text, and one spread
function Commands.RumourTest(PlayerName: string)
	local SSS = game:GetService(`ServerScriptService`).Services
	local Player = Players:FindFirstChild(PlayerName)
	local Ru = require(SSS.Social.Rumours)
	local I = { Kind = `Downed`; Region = `Commons`; Who = { { Id = Player; Role = `Doer` }, { Id = `MaeGorse`; Role = `Target` } }; Witnesses = { `KitHarrow` }; Truth = true; Severity = 2; T = os.time() }
	local R = Ru.Make(I)
	local Text = R and Ru.Text(R)
	local H = R and Ru.Hop(R, Random.new(7))
	return { Made = R ~= nil; HasTime = R ~= nil and typeof(R.T) == `number`; Text = Text; KnowerKit = R and R.Knowers.KitHarrow == true; HopCount = H and H.Hops;
		PlayerStill = H and H.Subject[1].Id == Player; NoTemplate = Ru.Make({ Kind = `Nothing`; Who = {} }) == nil }
end

-- (2.29) the safety rule over many random hops: a player is never added, swapped or moved off their own deed
function Commands.RumourSafetyTest(PlayerName: string)
	local SSS = game:GetService(`ServerScriptService`).Services
	local Player = Players:FindFirstChild(PlayerName)
	local Ru = require(SSS.Social.Rumours)
	local Rng = Random.new(2029)
	local Bad, Mutated = 0, 0
	local Cases = {
		{ Kind = `Downed`; Region = `Commons`; Who = { { Id = Player; Role = `Doer` }, { Id = `MaeGorse`; Role = `Target` } }; Witnesses = { `KitHarrow`, `JaxCalloway` } };
		{ Kind = `Downed`; Region = `MainHall`; Who = { { Id = `RonanFell`; Role = `Doer` }, { Id = Player; Role = `Target` } }; Witnesses = { `KitHarrow` } };
		{ Kind = `Scene`; Scene = `Locker`; Region = `MainHall`; Who = { { Id = `JaxCalloway`; Role = `Doer` }, { Id = `AgnesLowe`; Role = `Target` } }; Witnesses = { `NicoRuiz`, `ClaraWebb` } };
		{ Kind = `Caught`; Reason = `Truancy`; Region = `EastWing`; Who = { { Id = Player; Role = `Target` } }; Witnesses = {} };
	}
	for _, I in Cases do
		I.Truth, I.T, I.Severity = true, os.time(), 2
		for _ = 1, 2500 do
			local R = Ru.Make(I)
			for _ = 1, Rng:NextInteger(1, 6) do
				local Before = R
				R = Ru.Hop(R, Rng)
				if Ru.Text(R) ~= Ru.Text(Before) then Mutated += 1 end
			end
			-- every player in the rumour is in the incident, in the same role; every player in the incident is still there
			for _, S in R.Subject do
				if typeof(S.Id) == `Instance` then
					local Ok = false
					for _, W in I.Who do if W.Id == S.Id and W.Role == S.Role then Ok = true end end
					if not Ok then Bad += 1 end
				end
			end
			for _, W in I.Who do
				if typeof(W.Id) == `Instance` then
					local Still = false
					for _, S in R.Subject do if S.Id == W.Id and S.Role == W.Role then Still = true end end
					if not Still then Bad += 1 end
				end
			end
			-- no rumour about a player may change its place or its size: a mutation there would make it untrue
			local HasPlayer = false
			for _, S in R.Subject do if typeof(S.Id) == `Instance` then HasPlayer = true end end
			if HasPlayer and (R.Where ~= R.Base.Where or R.Size ~= R.Base.Size) then Bad += 1 end
		end
	end
	return { Hops = 10000; Bad = Bad; Mutated = Mutated }
end

-- (2.29) run one scene now at its spot (the player is moved there by the caller); returns how it went
function Commands.SceneTest(PlayerName: string, Id: string)
	local Scenes = require(game:GetService(`ServerScriptService`).Services.World.Scenes)
	local Ok, Why = Scenes.RunForTests(Id)
	return { Ok = Ok; Why = Why; Last = Scenes.LastForTests() }
end

-- (2.28) which post each staff member uses in each segment (pure)
function Commands.StaffPlanTest(PlayerName: string)
	local Npcs = require(game:GetService(`ServerScriptService`).Services.Social.Npcs)
	local Out = {}
	for _, Seg in { { `BeforeSchool`, `Before School` }, { `Class`, `Homeroom` }, { `Class`, `Period 2` }, { `Lunch`, `Lunch` }, { `Night`, `Night` } } do
		local Row = {}
		for _, Id in { `Hale`, `Sallow`, `Ashgrave`, `Ezra` } do Row[Id] = Npcs.PostKey(Id, Seg[1], Seg[2]) or `-` end
		Out[Seg[2]] = Row
	end
	return Out
end

function Commands.StartQuest(PlayerName: string, Id: string)
	return QuestsService().Start(Players:FindFirstChild(PlayerName), Id)
end

function Commands.CanStartQuest(PlayerName: string, Id: string)
	return { QuestsService().CanStart(Players:FindFirstChild(PlayerName), Id) }
end

function Commands.QuestProgress(PlayerName: string, Type: string, Key: any, Extra: any?)
	QuestsService().Progress(Players:FindFirstChild(PlayerName), Type, Key, Extra)
	return true
end

function Commands.SetQuestDeadline(PlayerName: string, Id: string, Seconds: number)
	QuestsService().SetDeadlineForTests(Players:FindFirstChild(PlayerName), Id, Seconds)
	return true
end

---| (2.24.0) Phase 1: cuts, Decision / Kill objectives |---

local function CineService() return require(game:GetService(`ServerScriptService`).Services.World.Cine) end

-- (2.27) the roster's data and seeding (nothing saved)
function Commands.RosterTest(PlayerName: string)
	return DeepCopy(require(game:GetService(`ServerScriptService`).Services.Social.Roster).SelfTestForTests())
end

-- (2.27) greetings from the saved memory, on a stand-in student; slot 2's entry for her is put back after
function Commands.MemoryTest(PlayerName: string)
	local SSS = game:GetService(`ServerScriptService`).Services
	local Player = Players:FindFirstChild(PlayerName)
	local Rep, Brain = require(SSS.Social.Reputation), require(SSS.AI.StudentBrain)
	local Lines = require(SSS.AI.StudentBrain.Lines)
	local Id = `OdetteMarsh`
	local Rels = Rep.Get(Player).Relationships
	local Saved = Rels[Id] and table.clone(Rels[Id])
	Rels[Id] = nil
	local S = { Index = 999; RosterId = Id; First = `Odette`; Temper = `Warm`; Clique = `Choir`; Memory = {} }
	local Out = {}
	local Ok, Err = pcall(function()
		Out.Fresh = (Brain.GreetingForTests(S, Player)) -- expect Intro
		Rep.Meet(Player, Id)
		Out.AfterMeet = (Brain.GreetingForTests(S, Player)) ~= `Intro`
		Rep.ChangeRelationship(Player, Id, 12, nil, `Helped`)
		Rep.ChangeRelationship(Player, Id, 12, nil, `Helped`)
		local _, PoolG = Brain.GreetingForTests(S, Player)
		Out.Grateful = PoolG == Lines.Greet.Grateful.Warm
		Rep.ChangeRelationship(Player, Id, -40, nil, `Fought`)
		local _, PoolF = Brain.GreetingForTests(S, Player)
		Out.Grudge = PoolF == Lines.Greet.Grudge.Warm
		Rels[Id] = nil
		Rep.ChangeRelationship(Player, Id, -25, nil, `Fought`) -- a fight before any introduction
		Out.NoIntroAfterFight = (Brain.GreetingForTests(S, Player)) ~= `Intro`
		Out.Attitude = require(SSS.AI.StudentBrain.Talk).Attitude(S, Player) -- Rival: at most Wary
	end)
	if not Ok then Out.Error = tostring(Err) end
	Rels[Id] = Saved
	Rep.Sync(Player)
	return Out
end

-- (2.27) the roster's bodies: ids on the live students, and a look that is the same when built twice
function Commands.Rostered(PlayerName: string)
	local Sched = require(game:GetService(`ServerScriptService`).Services.Features.Schedules)
	local Ids, Seen = {}, {}
	for _, R in Sched.Debug() do if R.RosterId and not Seen[R.RosterId] then Seen[R.RosterId] = true table.insert(Ids, R.RosterId) end end
	local A, B = Sched.LookForTests(`MaeGorse`), Sched.LookForTests(`MaeGorse`)
	return { Students = #Sched.Debug(); Ids = #Ids;
		SameLook = A.Uniform == B.Uniform and A.Skin == B.Skin and A.HairId == B.HairId and A.Bottoms == B.Bottoms and A.Body == B.Body }
end

-- Decision, Kill, a seen Cinematic stage and Requires.Fresh on the real Quests code (a throwaway quest; put back after)
function Commands.Phase1SelfTest(PlayerName: string)
	return DeepCopy(QuestsService().Phase1SelfTestForTests(Players:FindFirstChild(PlayerName)))
end

-- the group skip vote on the real session code, with stand-ins for the other viewers (nothing is saved)
function Commands.CineVoteTest(PlayerName: string)
	return DeepCopy(CineService().VoteSelfTestForTests(Players:FindFirstChild(PlayerName)))
end

-- play a cut for a player now (Opts.Skippable = a replay); returns the session id
-- (2.26.0) After Hours v1 saves: a save on Collected (stage 3) moves past the two new stages; earlier stages stay
function Commands.AfterHoursMigrateTest()
	local Q = QuestsService()
	local Def = require(game:GetService(`ReplicatedStorage`).Config.Quests).Quests.AfterHours
	local Out = {}
	for _, Stage in { 1, 2, 3 } do
		local State = { Stage = Stage; V = 1 }
		Q.MigrateForTests(Def, State)
		Out[`From{Stage}`] = State.Stage
	end
	return Out
end

-- (2.26.0) a story decision as the cut would save it (Quests.Decide), e.g. FileKept = Lose
function Commands.Decide(PlayerName: string, Id: string, Choice: string)
	return QuestsService().Decide(Players:FindFirstChild(PlayerName), Id, Choice)
end

function Commands.PlayCut(PlayerName: string, CutId: string, Skippable: boolean?)
	return CineService().Play({ Players:FindFirstChild(PlayerName) }, CutId, { Skippable = Skippable == true })
end

-- this player's saved cut state ({ [CutId] = "Started" | "Seen" }) and the live sessions
function Commands.CineState(PlayerName: string)
	local Player = Players:FindFirstChild(PlayerName)
	return DeepCopy({ Saved = QuestsService().CineState(Player); Sessions = CineService().SessionsForTests() })
end

-- clear (or set) one cut's saved state: CineMark(name, "Prologue", nil) makes it unseen again
function Commands.CineMark(PlayerName: string, CutId: string, Value: string?)
	local Player = Players:FindFirstChild(PlayerName)
	local S = QuestsService().CineState(Player)
	if not S then return false end
	S[CutId] = Value
	QuestsService().SyncForCine(Player)
	return true
end

---| (2.25.0) interactive cuts: the judge and the graph |---

local function CineJudge() return require(game:GetService(`ReplicatedStorage`).Functions.CineJudge) end

-- every scoring rule on fixed inputs; returns { Passed, Failed = { "name: got X, want Y" } }
function Commands.CineJudgeTest()
	local J = CineJudge()
	local Press = { kind = `Press`; at = 1; beat = 0.6; slow = 0.3; on = { Perfect = `A`; Good = `A`; Miss = `B` } }
	local Mash = { kind = `Mash`; at = 0; dur = 2; rate = 7; touchRate = 5; on = { Win = `A`; Lose = `B` } }
	local Dir = { kind = `Direction`; at = 0; dur = 0.9; options = { `Left`, `Right` }; answer = `Left`; on = { Right = `A`; Wrong = `B` } }
	local Hold = { kind = `Hold`; at = 0; zoneAt = 1.2; zone = 0.15; on = { Hit = `A`; Miss = `B` } }
	local Choice = { kind = `Choice`; at = 0; dur = 5; options = { { id = `Ask`; text = `Who?` }, { id = `Nod`; text = `...` } }; default = `Nod`;
		on = { Ask = `A`; Nod = `B` } }
	local function taps(N, Dur) local T = {} for I = 1, N do T[I] = (I - 0.5) * Dur / N end return T end
	local Cases = {
		{ `press exact`, Press, { Times = { 0.6 } }, `Perfect`, 3 },
		{ `press +0.12 edge`, Press, { Times = { 0.72 } }, `Perfect`, 3 },
		{ `press +0.2`, Press, { Times = { 0.8 } }, `Good`, 2 },
		{ `press -0.25 edge`, Press, { Times = { 0.35 } }, `Good`, 2 },
		{ `press -0.3`, Press, { Times = { 0.3 } }, `Miss`, 0 },
		{ `press none`, Press, { Times = {} }, `Miss`, 0 },
		{ `press earliest counts`, Press, { Times = { 0.9, 0.6 } }, `Perfect`, 3 }, -- times are sorted: 0.6 is judged
		{ `press reduced widens`, Press, { Times = { 0.9 }; Reduced = true }, `Good`, 2 },
		{ `mash 14 of 14`, Mash, { Times = taps(14, 2) }, `Win`, 2 },
		{ `mash 13`, Mash, { Times = taps(13, 2) }, `Lose`, 0 },
		{ `mash touch 10`, Mash, { Times = taps(10, 2); Touch = true }, `Win`, 2 },
		{ `mash late taps ignored`, Mash, { Times = { 2.5, 2.6, 2.7 } }, `Lose`, 0 },
		{ `dir right`, Dir, { Pick = `Left`; PickAt = 0.5 }, `Right`, 1 },
		{ `dir wrong`, Dir, { Pick = `Right`; PickAt = 0.5 }, `Wrong`, 0 },
		{ `dir late`, Dir, { Pick = `Left`; PickAt = 1.2 }, `Wrong`, 0 },
		{ `dir none`, Dir, {}, `Wrong`, 0 },
		{ `hold hit`, Hold, { Times = { 0.1 }; Release = 1.3 }, `Hit`, 2 },
		{ `hold early`, Hold, { Times = { 0.1 }; Release = 0.9 }, `Miss`, 0 },
		{ `hold never down`, Hold, { Release = 1.2 }, `Miss`, 0 },
		{ `choice picked`, Choice, { Pick = `Ask`; PickAt = 2 }, `Ask`, 1 },
		{ `choice timeout`, Choice, {}, `Nod`, 0 },
		{ `choice bogus id`, Choice, { Pick = `Hack`; PickAt = 1 }, `Nod`, 0 },
	}
	local Out = { Passed = 0; Failed = {} }
	for _, C in Cases do
		local Ok, O, Pts = pcall(J.Evaluate, C[2], C[3])
		if Ok and O == C[4] and Pts == C[5] then Out.Passed += 1
		else table.insert(Out.Failed, `{C[1]}: got {tostring(O)}/{tostring(Pts)}, want {C[4]}/{C[5]}`) end
	end
	-- branch, team, grade
	local function check(Name, Got, Want) if Got == Want then Out.Passed += 1 else table.insert(Out.Failed, `{Name}: got {tostring(Got)}, want {tostring(Want)}`) end end
	check(`branch perfect`, J.Branch(Press, `Perfect`), `A`)
	check(`branch miss`, J.Branch(Press, `Miss`), `B`)
	check(`branch else`, J.Branch({ on = { Else = `Z` } }, `Whatever`), `Z`)
	check(`team majority`, J.Team(Press, { `Miss`, `Miss`, `Good` }), `Miss`)
	check(`team tie -> better`, J.Team(Press, { `Perfect`, `Miss` }), `Perfect`)
	check(`team empty -> miss`, J.Team(Press, {}), `Miss`)
	check(`team choice tie -> earlier option`, J.Team(Choice, { `Nod`, `Ask` }), `Ask`)
	check(`grade S`, J.Grade(9, 10), `S`)
	check(`grade A`, J.Grade(3, 4), `A`)
	check(`grade B`, J.Grade(11, 20), `B`)
	check(`grade C`, J.Grade(7, 20), `C`)
	check(`grade D`, J.Grade(1, 10), `D`)
	check(`grade none`, J.Grade(0, 0), nil)
	check(`max press`, J.MAX.Press, 3)
	return Out
end

-- graph validation on a good graph and on broken ones; returns { Passed, Failed }
function Commands.CineGraphTest()
	local J = CineJudge()
	local Out = { Passed = 0; Failed = {} }
	local function expect(Name, Graph, WantErrs: boolean, Needle: string?)
		local Errs = J.Validate(Graph)
		local Text = table.concat(Errs, " | ")
		local Ok = (#Errs > 0) == WantErrs and (Needle == nil or Text:find(Needle, 1, true) ~= nil)
		if Ok then Out.Passed += 1 else table.insert(Out.Failed, `{Name}: errors [{Text}]`) end
	end
	local function good()
		return { start = `A`; segments = {
			A = { len = 3; prompt = { kind = `Press`; at = 1; beat = 0.6; slow = 0.3; on = { Perfect = `B`; Good = `B`; Miss = `C` } } };
			B = { len = 2; next = `D` }; C = { len = 2; next = `D` };
			D = { len = 3; prompt = { kind = `Mash`; at = 0.5; dur = 1.6; rate = 7; slow = 0.5; on = { Win = `E`; Lose = `E` } } };
			E = { len = 1 } } }
	end
	expect(`good graph`, good(), false)
	local G1 = good() G1.start = `Nope`
	expect(`bad start`, G1, true, `start`)
	local G2 = good() G2.segments.B.next = `Ghost`
	expect(`unknown next`, G2, true, `Ghost`)
	local G3 = good() G3.segments.E.next = `A`
	expect(`loop`, G3, true, `loop`)
	local G4 = good() G4.segments.A.prompt.on.Miss = nil
	expect(`missing branch`, G4, true, `no branch for Miss`)
	local G5 = good() G5.segments.A.len = 1.2
	expect(`tail too short`, G5, true, `tail`)
	local G6 = good() G6.segments.A.next = `B`
	expect(`prompt with next`, G6, true, `no next`)
	-- the longest path: A (1 + 2/0.3) + C 2 + D (0.5 + 2.5/0.5) + E 1 = 7.67 + 2 + 5.5 + 1
	local L = J.LongestPath(good())
	if math.abs(L - (1 + 2 / 0.3 + 2 + 0.5 + 2.5 / 0.5 + 1)) < 0.01 then Out.Passed += 1 else table.insert(Out.Failed, `longest path {L}`) end
	if J.Follows(good(), `B`, `D`) and not J.Follows(good(), `A`, `D`) then Out.Passed += 1 else table.insert(Out.Failed, `follows`) end
	return Out
end

function Commands.CineGrades(PlayerName: string)
	return DeepCopy(QuestsService().CineGrades(Players:FindFirstChild(PlayerName)))
end

-- the group decide, the solo path check, Where and the grade on the real session code, with stand-in viewers
function Commands.CineQteTest(PlayerName: string)
	return DeepCopy(CineService().QteSelfTestForTests(Players:FindFirstChild(PlayerName)))
end

-- Move the player next to a map part found by attribute (QuestObject / QuestArea / NpcPost ...).
function Commands.GoTo(PlayerName: string, Attribute: string, Value: any, Offset: Vector3?)
	local Player = Players:FindFirstChild(PlayerName)
	local Part = Places().Find(Attribute, Value)
	if not Player or not Player.Character or not Part then return false end
	Player.Character:PivotTo(CFrame.new(Part.Position + (Offset or Vector3.new(0, 3, 3))))
	return true
end

-- Use a quest object (server range checks still apply).
function Commands.UseObject(PlayerName: string, ObjectId: string)
	local Player = Players:FindFirstChild(PlayerName)
	QuestsService().OnInteract(Player, ObjectId)
	return true
end

function Commands.Link(PlayerName: string, Case: string, A: string, B: string)
	return { require(ServerScriptService.Services.Quests.Investigation).Link(Players:FindFirstChild(PlayerName), Case, A, B) }
end

function Commands.Deduce(PlayerName: string, Case: string, Option: number)
	return { require(ServerScriptService.Services.Quests.Investigation).Deduce(Players:FindFirstChild(PlayerName), Case, Option) }
end

function Commands.Stealth(PlayerName: string, Zone: string?)
	local Stealth = require(ServerScriptService.Services.Quests.Stealth)
	local Player = Players:FindFirstChild(PlayerName)
	local W = Zone and Stealth.WatcherForTests(Zone)
	return {
		Meter = Player and Stealth.MeterForTests(Player);
		Hidden = Player and Stealth.IsHidden(Player);
		Watcher = W and Describe(W);
		WatcherPos = W and W:GetPivot().Position and tostring(W:GetPivot().Position);
	}
end

function Commands.MoveWatcher(Zone: string, Position: Vector3, LookAt: Vector3?)
	local W = require(ServerScriptService.Services.Quests.Stealth).WatcherForTests(Zone)
	if not W then return false end
	W:PivotTo(if LookAt then CFrame.lookAt(Position, LookAt) else CFrame.new(Position))
	return true
end

function Commands.Hide(PlayerName: string, Leave: boolean?)
	local Stealth = require(ServerScriptService.Services.Quests.Stealth)
	local Player = Players:FindFirstChild(PlayerName)
	if Leave then Stealth.Unhide(Player) return true end
	local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`)
	local Best, BestD = nil, math.huge
	for _, Spot in Places().FindAll(`HidingSpot`) do
		local D = (Spot.Position - Root.Position).Magnitude
		if D < BestD then Best, BestD = Spot, D end
	end
	return Best and Stealth.Hide(Player, Best) or false
end

function Commands.DuelTest(PlayerName: string, OpponentName: string)
	local Player = Players:FindFirstChild(PlayerName)
	local Opponent = FindCharacter(OpponentName)
	return Opponent ~= nil and require(ServerScriptService.Services.Quests.Duels).DuelForTests(Player, Opponent)
end

function Commands.DuelState()
	return require(ServerScriptService.Services.Quests.Duels).StateForTests()
end

---| Main menu / slots |---

function Commands.Slots(PlayerName: string)
	return require(ServerScriptService.Services.Player.Slots).List(Players:FindFirstChild(PlayerName))
end

function Commands.ChooseSlot(PlayerName: string, Slot: number)
	return { require(ServerScriptService.Services.Player.Slots).ChooseForTests(Players:FindFirstChild(PlayerName), Slot) }
end

function Commands.Identity(PlayerName: string)
	return require(ServerScriptService.Services.Player.Identity).Get(Players:FindFirstChild(PlayerName))
end

function Commands.SetName(PlayerName: string, Name: string)
	return { require(ServerScriptService.Services.Player.Identity).SetName(Players:FindFirstChild(PlayerName), Name) }
end

function Commands.SpinClan(PlayerName: string)
	return { require(ServerScriptService.Services.Player.Identity).SpinClan(Players:FindFirstChild(PlayerName)) }
end

-- (homes) the student's room, saved housing and who's where; force a look; or run a made-up report card through
-- Homes.Adjust / AfterCard (the allowance math and Mom & Dad's text), paying it like ReportCards does
function Commands.HomeInfo(PlayerName: string)
	local P = Players:FindFirstChild(PlayerName)
	local Homes = require(ServerScriptService.Services.Features.Homes)
	local R = P and Homes.RoomOf(P)
	local Shown = {}
	if R then
		for _, D in R.Model:GetDescendants() do
			if D:GetAttribute(`NHHomeState`) and D ~= R.Model then
				local Vis = D:IsA(`BasePart`) and D.Transparency < 1
				if not D:IsA(`BasePart`) then for _, X in D:GetDescendants() do if X:IsA(`BasePart`) and X.Transparency < 1 and X.Name ~= `NHTrophyShown` and not X.Name:find(`TrophySpot`) then Vis = true break end end end
				if Vis then table.insert(Shown, D.Name) end
			end
		end
		table.sort(Shown)
	end
	return { Housing = P and Homes.Get(P); State = R and R.State; Slot = R and R.Slot; Pivot = R and R.Model:GetPivot().Position; Shown = Shown; InHome = P and P:GetAttribute(`NHInHome`) }
end
function Commands.HomeEnter(PlayerName: string, OwnerName: string?)
	local P = Players:FindFirstChild(PlayerName)
	local O = OwnerName and Players:FindFirstChild(OwnerName)
	return { require(ServerScriptService.Services.Features.Homes).Enter(P, O and O.UserId or nil) }
end
function Commands.HomeLeave(PlayerName: string)
	require(ServerScriptService.Services.Features.Homes).Leave(Players:FindFirstChild(PlayerName))
	return true
end
function Commands.HomeState(PlayerName: string, StateId: string)
	return require(ServerScriptService.Services.Features.Homes).SetStateForTests(Players:FindFirstChild(PlayerName), StateId)
end
function Commands.HomeCard(PlayerName: string, Average: string?, Allowance: number?)
	local P = Players:FindFirstChild(PlayerName)
	local Homes = require(ServerScriptService.Services.Features.Homes)
	local Card = { Average = Average; Allowance = Allowance or 0 }
	Homes.Adjust(P, Card)
	if Card.Allowance > 0 then require(ServerScriptService.Services.Player.Data).UpdateState(P, { type = `UpdateYen`; amount = Card.Allowance }) end
	Homes.AfterCard(P, Card)
	return { Allowance = Card.Allowance; Parents = Card.Parents; CutOff = Card.CutOff; Housing = Homes.Get(P) }
end

-- (homes) give a beast trophy and redraw the owner's trophy shelf; returns the trophies on it
function Commands.HomeTrophy(PlayerName: string, ItemId: string)
	local P = Players:FindFirstChild(PlayerName)
	require(ServerScriptService.Services.Features.Inventory).Grant(P, ItemId, 1)
	return require(ServerScriptService.Services.Features.Homes).TrophiesForTests(P)
end
-- (homes) a host invites a guest; returns the result and whether the guest may visit now
function Commands.HomeInvite(HostName: string, GuestName: string)
	local H, G = Players:FindFirstChild(HostName), Players:FindFirstChild(GuestName)
	local Homes = require(ServerScriptService.Services.Features.Homes)
	local Ok, Why = Homes.Invite(H, G and G.UserId)
	return { Ok = Ok; Why = Why; CanVisit = G and H and Homes.CanVisit(G, H.UserId) }
end
-- (height) spin the height; or mark it not yet revealed, so the creator plays the first-roll reveal again
function Commands.SpinHeight(PlayerName: string)
	return { require(ServerScriptService.Services.Player.Identity).SpinHeight(Players:FindFirstChild(PlayerName)) }
end
function Commands.HeightUnseen(PlayerName: string)
	local P = Players:FindFirstChild(PlayerName)
	local Identity = require(ServerScriptService.Services.Player.Identity)
	local I = P and Identity.Get(P)
	if not I then return false end
	I.Height.Seen = false
	require(ServerScriptService.Services.Player.Data).UpdateState(P, { type = `SetIdentity`; identity = I })
	Identity.Notify(P) -- the client's copy too
	return true, I.Height
end

-- Runs the real receipt handler with a made-up receipt (Config.Shop key, receipt id).
function Commands.GrantProduct(PlayerName: string, Key: string, PurchaseId: string)
	return require(ServerScriptService.Services.Player.Purchases).ProcessForTests(Players:FindFirstChild(PlayerName), Key, PurchaseId)
end

-- Stranger system: From introduces themselves to To; Strangers lists what a player's client was sent.
function Commands.Introduce(From: string, To: string)
	return { require(ServerScriptService.Services.Social.Strangers).IntroduceForTests(Players:FindFirstChild(From), Players:FindFirstChild(To)) }
end

function Commands.Strangers(PlayerName: string)
	return require(ServerScriptService.Services.Social.Strangers).SentForTests(Players:FindFirstChild(PlayerName))
end

-- Progression: give EXP, read the record sheet, spend points.
function Commands.GiveExp(PlayerName: string, Amount: number, Category: string?)
	return require(ServerScriptService.Services.Player.Progression).AwardForTests(Players:FindFirstChild(PlayerName), Amount, Category)
end

function Commands.Progress(PlayerName: string)
	return require(ServerScriptService.Services.Player.Progression).Sheet(Players:FindFirstChild(PlayerName))
end

function Commands.SpendStat(PlayerName: string, StatId: string, Count: number?)
	return { require(ServerScriptService.Services.Player.Progression).Spend(Players:FindFirstChild(PlayerName), StatId, Count or 1) }
end

-- Races: force a lineage, then measure a hit through Downed.ApplyDamage (race family bonuses included)
function Commands.SetRace(PlayerName: string, Race: string, Sub: string?, Tier: number?)
	return { require(ReplicatedStorage.Lineage).SetForTests(Players:FindFirstChild(PlayerName), Race, Sub, Tier) }
end

-- Evolution: hunger, forcing a tier-up (plays the cutscene), opening the rite
-- Sports: clubs, venues, drills (Services.Sports.*)
local function Sports(Name) return require(ServerScriptService.Services.Sports[Name]) end
function Commands.JoinClub(PlayerName: string, ClubId: string?)
	local P = Players:FindFirstChild(PlayerName)
	if ClubId == nil or ClubId == `` then return { Sports(`Clubs`).Leave(P) } end
	return { Sports(`Clubs`).Join(P, ClubId) }
end
-- test cleanup: put a slot's places found back exactly (a list of region ids)
function Commands.RegionSet(PlayerName: string, Ids: { string })
	local P = Players:FindFirstChild(PlayerName)
	if not P then return false end
	local Found = {}
	for _, Id in Ids or {} do Found[Id] = true end
	require(ServerScriptService.Services.Player.Data).UpdateState(P, { type = `SetRegions`; regions = { Found = Found } })
	return require(ServerScriptService.Services.Features.Regions).State(P)
end
-- test cleanup: overwrite fields of a slot's progress (Level, Exp, Points)
function Commands.SetProgressFields(PlayerName: string, Fields: { [string]: any })
	local P = Players:FindFirstChild(PlayerName)
	local Prog = require(ServerScriptService.Services.Player.Progression)
	local Pr = P and Prog.Get(P)
	if not Pr then return false end
	for K, V in Fields do Pr[K] = V end
	require(ServerScriptService.Services.Player.Data).UpdateState(P, { type = `SetProgress`; progress = Pr })
	P:SetAttribute(`Level`, Pr.Level)
	return Prog.Sheet(P)
end
function Commands.RegionState(PlayerName: string) return require(ServerScriptService.Services.Features.Regions).State(Players:FindFirstChild(PlayerName)) end
function Commands.RegionReset(PlayerName: string) return require(ServerScriptService.Services.Features.Regions).Reset(Players:FindFirstChild(PlayerName)) end
-- 1.20 cliques: schedule test plans and clique standing
function Commands.SchedulePlan(Kind: string, Name: string?, Hour: number?) return require(ServerScriptService.Services.Features.Schedules).PlanForTests(Kind, Name, Hour) end
function Commands.ScheduleDebug() return require(ServerScriptService.Services.Features.Schedules).Debug() end
function Commands.Cliques(PlayerName: string) return require(ServerScriptService.Services.Social.Cliques).State(Players:FindFirstChild(PlayerName)) end
function Commands.CliqueAdd(PlayerName: string, Id: string, Amount: number, Reason: string?) return require(ServerScriptService.Services.Social.Cliques).Add(Players:FindFirstChild(PlayerName), Id, Amount, Reason) end
function Commands.ClubSheet(PlayerName: string) return Sports(`Clubs`).Sheet(Players:FindFirstChild(PlayerName)) end
function Commands.SportForce(Venue: string, A: string, B: string, Solo: boolean?)
	local PA, PB = {}, {}
	for N in string.gmatch(A or ``, `[^,]+`) do table.insert(PA, Players:FindFirstChild(N)) end
	for N in string.gmatch(B or ``, `[^,]+`) do table.insert(PB, Players:FindFirstChild(N)) end
	return { Sports(`Matches`).ForceStart(Venue, PA, PB, Solo) }
end
function Commands.SportState(Venue: string)
	local m = Sports(`Matches`).Get(Venue)
	if not m then return nil end
	local B = m.B
	return { Phase = m.Phase; Clock = m.Clock; Score = m.Score; A = #m.Teams.A; B = #m.Teams.B; QueueA = #m.Queue.A; QueueB = #m.Queue.B;
		Holder = B and B.Ball and B.Ball.Holder and B.Ball.Holder.Name; BallState = B and B.Ball and B.Ball.State; ShotClock = B and B.ShotClock;
		HalfCourt = B and B.HalfCourt; Possession = B and B.Possession; Ranked = m.Ranked; Plug = m.Plug ~= nil }
end
-- run a sport action as if the client sent it (goes through the same rules)
function Commands.SportAction(PlayerName: string, Action: string, Args: any)
	local P = Players:FindFirstChild(PlayerName)
	local m = Sports(`Matches`).MatchOf(P)
	if m and m.Plug then return { pcall(m.Plug.OnAction, m, P, Action, Args or {}) } end
	for _, Name in { `Basketball`, `Soccer`, `Football` } do local M = game.ServerScriptService.Services.Sports:FindFirstChild(Name) if M then local R = require(M).DrillAction(P, Action, Args or {}) if R then return { R } end end end return { false }
end
function Commands.AwardExp(PlayerName: string, Key: string)
	return require(ServerScriptService.Services.Player.Progression).Award(Players:FindFirstChild(PlayerName), Key, nil, `Test`)
end
function Commands.FootballState(Venue: string)
	local m = Sports(`Matches`).Get(Venue or `Field`)
	if not m then return nil end
	local S = m.S
	local H = S and S.Ball and S.Ball.Holder
	return { Phase = m.Phase; Clock = m.Clock; Score = m.Score; A = #m.Teams.A; B = #m.Teams.B; Plug = m.Plug ~= nil;
		Mode = S and S.Mode; Offence = S and S.Offence; Down = S and S.Down; LOS = S and S.LOS; ToGoX = S and S.ToGoX; Kind = S and S.Kind;
		QB = S and S.QB and S.QB.Name; Kicker = S and S.Kicker and S.Kicker.Name; Holder = H and H.Name; BallState = S and S.Ball and S.Ball.State;
		Air = S and S.Air and S.Air.Kind; Loose = S and S.Air and S.Air.Loose; Call = S and S.Call; Message = m.Message;
		BallPos = S and S.Ball and S.Ball.Part.Position; Dummies = S and S.Dummies and #S.Dummies or 0; Stats = m.Stats }
end
-- Studio only: put the ball on a down and a spot (yards to the goal) for the side with it, then huddle
function Commands.FootballSpot(Down: number, ToGoal: number, Venue: string?)
	local m = Sports(`Matches`).Get(Venue or `Field`)
	if not (m and m.Plug and m.Plug._Local and m.S and m.Phase == `Live`) then return false end
	local L, S = m.Plug._Local, m.S
	S.LOS = L.SpotX(m, S.Offence, 60 - ToGoal)
	S.Down = Down
	local Goal = S.GoalX[S.Offence]
	S.ToGoX = S.LOS + S.Dir[S.Offence] * 10 * S.Yard
	if (S.ToGoX - Goal) * S.Dir[S.Offence] > 0 then S.ToGoX = Goal end
	S.Kind = nil
	L.Huddle(m, `Test spot`)
	return true
end
-- Studio only: a test defender that chases the ball carrier (Team = "A" or "B")
function Commands.FootballDummy(Team: string, Venue: string?)
	local m = Sports(`Matches`).Get(Venue or `Field`)
	if not (m and m.Plug and m.Plug.AddDummy) then return false end
	return m.Plug.AddDummy(m, Team or `B`) ~= nil
end
function Commands.SportEnd(Venue: string)
	local m = Sports(`Matches`).Get(Venue)
	if m and m.Phase ~= `Waiting` then m:End(nil, `Test`) end
	return m and m.Phase
end
function Commands.SportClock(Venue: string, Seconds: number)
	local m = Sports(`Matches`).Get(Venue)
	if m then m.Clock = Seconds end
	return m and m.Clock
end

function Commands.GiveHunger(PlayerName: string, Amount: number)
	return require(ServerScriptService.Services.Player.Evolution).Feed(Players:FindFirstChild(PlayerName), Amount, `Test`)
end

function Commands.Evolve(PlayerName: string, Tier: number)
	return require(ServerScriptService.Services.Player.Evolution).Evolve(Players:FindFirstChild(PlayerName), Tier)
end

function Commands.RaceDamage(AttackerName: string, TargetName: string, Damage: number)
	local Downed = require(ServerScriptService.Services.Features.Downed)
	local A, T = FindCharacter(AttackerName), FindCharacter(TargetName)
	local H = T and T:FindFirstChildOfClass(`Humanoid`)
	if not (A and H) then return `missing` end
	local Before = H.Health
	Downed.ApplyDamage(T, Damage, A)
	return Before - H.Health
end

-- (training 1.81) the game's own Training instance: Training(name, "State") | ("Get") | ("Grant", area, xp) |
-- ("Submit", presses) (a forged result through the real check) | ("Begin")
function Commands.Training(PlayerName: string, Action: string, ...)
	local T = require(ServerScriptService.Services.Features.Training)
	local P = Players:FindFirstChild(PlayerName)
	if Action == `State` then return T.State(P) end
	if Action == `Get` then return T.Get(P) end
	if Action == `Grant` then return T.TestGrant(P, ...) end
	if Action == `Begin` then return T.Begin(P) end
	if Action == `Set` then return T.TestSet(P, ...) end -- (1.86) area, level, xp, resetBody
	if Action == `Submit` then return T.Submit(P, ...) end
	if Action == `Moment` then -- replay a step-up moment (the banner, flex and burst) without changing anything
		local Area = ...
		local Root = P.Character and P.Character:FindFirstChild(`HumanoidRootPart`)
		require(ServerScriptService.Services.Features.Fx).FireNear(Root.Position, 80, `TrainStep`, { UserId = P.UserId; Area = Area or `Arms`; Body = `Toned`; Step = 1; Test = true })
		return true
	end
	if Action == `Look` then
		local Profile = require(ServerScriptService.Services.Player.Data).GetProfile(P)
		return Profile and Profile.Appearance
	end
	return `unknown`
end

-- (batch 54) put snacks in a test student's Locker through the real Inventory service (Grant pins them too), or take them back
function Commands.GrantItem(PlayerName: string, Id: string, N: number?)
	return require(ServerScriptService.Services.Features.Inventory).Grant(Players:FindFirstChild(PlayerName), Id, N)
end

-- (hunger 1.0) the game's own Body instance: Body(name, "State") | ("Set", n) | ("Tick", seconds) | ("Eat", itemId) |
-- ("Fed", kind) | ("Effects") | ("Saved") (the save as it is in the profile)
function Commands.Body(PlayerName: string, Action: string, ...)
	local B = require(ServerScriptService.Services.Features.Body)
	local P = Players:FindFirstChild(PlayerName)
	if Action == `State` then return B.State(P) end
	if Action == `Set` then return B.TestSet(P, ...) end
	if Action == `Tick` then return B.TestTick(P, ...) end
	if Action == `Eat` then return B.Ate(P, require(ReplicatedStorage.Config.Items).ById[(...)]) end
	if Action == `Fed` then return B.Fed(P, ...) end
	if Action == `Effects` then return B.Effects(P) end
	if Action == `Saved` then
		local Profile = require(ServerScriptService.Services.Player.Data).GetProfile(P)
		return Profile and Profile.Body
	end
	return `unknown`
end

function Commands.EnterSchool(PlayerName: string)
	return require(ServerScriptService.Services.Player.Slots).EnterForTests(Players:FindFirstChild(PlayerName))
end

function Shared.OnStart()
	if not RunService:IsStudio() then
		return
	end

	local Existing = ServerStorage:FindFirstChild(`NHTestBridge`)
	if Existing then Existing:Destroy() end

	local Bridge = Instance.new(`BindableFunction`)
	Bridge.Name = `NHTestBridge`
	Bridge.OnInvoke = function(CommandName: string, ...)
		local Command = Commands[CommandName]
		if not Command then
			return false, `Unknown command {CommandName}`
		end
		return pcall(Command, ...)
	end
	Bridge.Parent = ServerStorage
end

-- (2.31) Standing Paths: the evaluator on made-up facts, then grants on the live player (put back after)
function Commands.PathsTest(PlayerName: string)
	return DeepCopy(require(ServerScriptService.Services.Player.Paths).SelfTestForTests(Players:FindFirstChild(PlayerName)))
end

-- (2.31) the five counters, each from its real signal; put back after
function Commands.TallyTest(PlayerName: string)
	local SSS = ServerScriptService.Services
	local P = Players:FindFirstChild(PlayerName)
	local Prog = require(SSS.Player.Progression)
	local Before = table.clone(Prog.Get(P).Tally)
	require(SSS.Quests.Duels).Won:Fire(P)
	require(SSS.Quests.Duels).ChampionDefeated:Fire(P)
	require(SSS.School.HallMonitor).Escaped:Fire(P, `Curfew`)
	require(SSS.Features.Beasts).Reward(P, { Name = `Test beast`; Reward = {} })
	task.wait(0.5)
	local After = Prog.Get(P).Tally
	local Out = {}
	for _, K in { `DuelWins`, `Champion`, `Escapes`, `Beasts` } do Out[K] = (After[K] or 0) - (Before[K] or 0) end
	local Pr = Prog.Get(P) Pr.Tally = Before
	require(SSS.Player.Data).UpdateState(P, { type = `SetProgress`; progress = Pr })
	return Out
end

-- (2.31) reaching a tier: the banner event, and a broadcast mention from tier 4 (put back after)
function Commands.PathRewardTest(PlayerName: string)
	local SSS = ServerScriptService.Services
	local P = Players:FindFirstChild(PlayerName)
	local Paths = require(SSS.Player.Paths)
	return DeepCopy(Paths.RewardTestForTests(P))
end

-- (2.31) NPCs and paths: the student pool, and each tree's line with a fake ctx at tier 3 and at tier 1
function Commands.RecognitionTest()
	local Talk = require(ServerScriptService.Services.AI.StudentBrain.Talk)
	local Out = { Pools = {} }
	for _, Path in { `Academic`, `Social`, `Combat`, `Athletic`, `Supernatural` } do
		local Pool = Talk.Pool(nil, `Path`, `Neutral`, Path)
		Out.Pools[Path] = Pool and #Pool or 0
	end
	local Trees = game:GetService(`ServerStorage`).Dialogue
	local function fake(Tier: number)
		return { PathTier = function() return Tier end; Member = function() return false end; State = function() return `Acquaintance` end;
			Decided = function() return nil end; Objective = function() return nil end }
	end
	Out.Lines = {}
	for _, Name in { `Sallow`, `Pryce`, `Whitlock`, `Ezra`, `Vesper` } do
		local Tree = require(Trees[Name]) -- the templates return { Start, Nodes }
		local Hub = Tree.Nodes and Tree.Nodes.Hub
		local T = Hub and Hub.Text
		local At3 = if typeof(T) == `function` then T(fake(3)) else T
		local At1 = if typeof(T) == `function` then T(fake(1)) else T
		Out.Lines[Name] = { Differs = At3 ~= At1; At3 = At3 }
	end
	return Out
end

return Shared
]==] })

for _, It in Items do
	local Fn, Err = loadstring(It.Source)
	if not Fn then return "PARSE FAIL " .. table.concat(It.Path, ".") .. ": " .. tostring(Err) end
end
for _, It in Items do
	local Node = game:GetService(It.Path[1])
	for I = 2, #It.Path - 1 do
		local Next = Node:FindFirstChild(It.Path[I])
		if not Next then Next = Instance.new("Folder") Next.Name = It.Path[I] Next.Parent = Node end
		Node = Next
	end
	local Name = It.Path[#It.Path]
	local Old = Node:FindFirstChild(Name)
	local New = Instance.new("ModuleScript")
	New.Name = Name
	New.Source = It.Source
	New.Parent = Node
	if Old then for _, K in Old:GetChildren() do K.Parent = New end Old:Destroy() end
	table.insert(Report, New:GetFullName() .. " " .. #New.Source)
end
return table.concat(Report, "\n")