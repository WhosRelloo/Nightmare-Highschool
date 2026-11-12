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
]]

local CollectionService = game:GetService(`CollectionService`)
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local ServerStorage = game:GetService(`ServerStorage`)

local Nav = require(ServerScriptService.Services.AI.Nav)
local Senses = require(ServerScriptService.Services.AI.Senses)
local Lines = require(script:WaitForChild(`Lines`))
-- (line matrix) clique x attitude x moment; a broken or missing Talk falls back to today's pools, never the whole brain
local OkT, Talk = pcall(require, script:WaitForChild(`Talk`, 5))
if not OkT or typeof(Talk) ~= `table` then
	Talk = { Pick = function() return nil end; Attitude = function() return `Neutral` end; Outfit = function() return nil end }
end
local CliqueConfig = require(ReplicatedStorage.Config.Cliques)
local Appearance = require(ReplicatedStorage.UI.Appearance)
local Cliques = require(ServerScriptService.Services.Social.Cliques) -- (line matrix) the dress code, Cliques.Dressed

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
		Night = T < 6 or T >= 19.5 or workspace:GetAttribute(`NHMoonNight`) == true;
	}
end

local function bubble(S, Text: string)
	S.SaidAt = os.clock()
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
		bubble(S, Text)
		return true
	end
	return Fallback ~= nil and say(S, Fallback, Cooldown)
end

-- a shove (Nudges) gets its own line once the student turns to look at who did it
NudgeMod.OnShove = function(S, Rec)
	sayMatrix(S, `Shoved`, Rec and Rec.Player, nil, 0, Lines.MakeWay)
end

-- what a student remembers about each player: how often they've met, when they last said hi, when they saw them fight
local function memo(S, Pl: Player?)
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

local function greet(S, Rec): boolean
	local Pl = Rec and Rec.Player
	local M = memo(S, Pl)
	if os.clock() - (M.Greeted or -1e9) < 60 then return false end
	local Moment, Opts, Pool = greeting(S, Rec)
	local Said = if Moment then sayMatrix(S, Moment, Pl, Opts, 6, Pool) else say(S, Pool, 6)
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

function React.Gawk(S, Snap)
	local T = Snap.Threat
	mood(S, `Watching`, 4)
	if not S.Seated then
		S.Model:SetAttribute(`NHActivity`, `Watching a fight`)
		S.Agent:Stop()
		pose(S, nil)
		S.Agent:Face(T.Pos)
	end
	lookAt(S, T.Pos + Vector3.new(0, 2, 0), 1.2)
	if os.clock() > (S.WatchUntil or 0) then -- just started watching
		if T.From and T.From.Player then memo(S, T.From.Player).Fought = os.clock() end
		if T.Heard and math.random() < 0.5 then
			say(S, Lines.Heard.Fight, 10)
		else
			sayMatrix(S, `FightSeen`, T.From and T.From.Player, nil, 10, Lines.ByNature(S, Lines.Gawk, `Brave`))
		end
	elseif math.random() < 0.08 then
		sayMatrix(S, `FightSeen`, T.From and T.From.Player, nil, 9, Lines.ByNature(S, Lines.Gawk, `Brave`))
	end
	S.WatchUntil = os.clock() + 6
	S.WatchAt = T.Pos
	S.Shaken = true
	task.wait(0.4)
end

function React.MakeWay(S, Snap)
	local Rec = Snap.Approaching
	if not (Rec and Rec.Pos) then return end
	mood(S, `Wary`, 3)
	lookAt(S, headOf(Rec), 1.5)
	if math.random() < 0.6 then
		if (Rec.Speed or 0) > 18 then say(S, Lines.Sprint, 10) else sayMatrix(S, `Bump`, Rec.Player, nil, 10, Lines.MakeWay) end
	end
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
				say(S, Lines.Shy, 20)
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
	local Lines2 = Lines.PickChat(A, ctx())
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

local function shoulder(S): Motor6D?
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
	task.spawn(loop, S, M)
end

function Brain.Detach(S)
	if S.Agent then pcall(function() S.Agent:Stop() end) end
	if S.Senses and S.Senses.Destroy then pcall(function() S.Senses:Destroy() end) end
	S.Agent, S.Senses = nil, nil
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
