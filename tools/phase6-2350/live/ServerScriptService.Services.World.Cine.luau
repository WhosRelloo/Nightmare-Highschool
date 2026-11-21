--[[
	Cine (server, Phase 1 / 2.24.0). Services.World.Cine: who sees which cut, and the story beats around it.
	Spec: docs/expansion/04-Cinematic-Framework.md. The client side is Controllers.Cine (it plays the shot list).

	Cine.Play(Players, CutId, Opts?) -> session id?
		Plays a cut (Config.Cine.Cuts) for one player (a personal cut) or a party (a group cut). Opts:
		  Skippable = true      everyone may skip at once (a replay from the journal)
		  OnFinish(Player, How) called once per viewer: How = "Done" | "Skipped" | "Timeout" | "Left" | "Died"
		Before it plays, each viewer's cut is saved as "Started" (Quests block: Cine[Id]), so a disconnect mid-cut
		is replayed once on rejoin with Skip offered (Quests' Cinematic objective does that). When it ends it's saved
		as "Seen". The beat's progress never depends on the cut finishing: the timeout (Length + 5 s from the moment
		the client began) forces Done.
	While a cut plays, each viewer's real character stays where it is: anchored, still, untouchable (NH_Evolving,
	as in a tier-up, plus Protected) and in the InActivity state (no combat, no emotes, no vaults).

	Skipping:
		A personal cut can be skipped once it has been seen (or started before: the rejoin replay).
		A group cut skips by vote: a strict majority of the viewers still watching. Anyone who has already seen it
		votes skip automatically.
	Remote: ReplicatedStorage.NHCine (RemoteEvent), one table per message:
		server -> client  { Kind = "Play", Session, Id, StartAt, Skippable, Group, Viewers, Need }
		                  { Kind = "Votes", Session, Votes, Need }    { Kind = "End", Session, How }
		client -> server  { Kind = "Began", Session }  { Kind = "Done", Session }  { Kind = "Skip", Session }
		                  { Kind = "Vote", Session }    { Kind = "Replay", Id }
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local HttpService = game:GetService(`HttpService`)

---| Modules |---

local SignalPlus = require(ReplicatedStorage.Packages.SignalPlus)
local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local Config = require(ReplicatedStorage.Config.Cine)
local Judge = require(ReplicatedStorage.Functions.CineJudge)

local function Quests() return require(ServerScriptService.Services.Quests.Quests) end -- lazy: Quests requires us too

local RATE = 40 -- messages a second per player (2.25.0: Seg / Where / Input add a few; still blocks floods)

local Local = {}
local Shared = {}

Shared.Began = SignalPlus()    -- (Player, CutId)
Shared.Finished = SignalPlus() -- (Player, CutId, How)

local Remote: RemoteEvent = nil
local Sessions = {} :: { [string]: any }
local ByPlayer = {} :: { [Player]: string } -- the session each player is watching
local BeatCrouched = {} :: { [Player]: boolean } -- (fix round 1) crouched by a walk-and-talk beat (BeatCrouch)
local Rate = {} :: { [Player]: { At: number, N: number } }

---| Saved state (Quests block: Cine = { [CutId] = "Started" | "Seen" }) |---

function Local.State(Player: Player): { [string]: string }?
	local Ok, Q = pcall(function() return Quests().CineState(Player) end)
	return if Ok then Q else nil
end

function Shared.Seen(Player: Player, Id: string): boolean
	local S = Local.State(Player)
	return S ~= nil and S[Id] == `Seen`
end

function Shared.Started(Player: Player, Id: string): boolean
	local S = Local.State(Player)
	return S ~= nil and (S[Id] == `Started` or S[Id] == `Seen`)
end

function Local.Mark(Player: Player, Id: string, Value: string)
	local S = Local.State(Player)
	if not S then return end
	if Value == `Started` and S[Id] == `Seen` then return end -- a replay never un-sees it
	S[Id] = Value
	pcall(function() Quests().SyncForCine(Player) end)
end

---| The real character during a cut |---

-- (2.35.0) a seamless cut: the player's own client drives their character (it walks to marks, plays the chain), so
-- nothing anchors and speed isn't zeroed here; they're protected and marked in a cut, and the client locks input
function Local.HoldSeamless(Player: Player): (() -> ())?
	local Character = Player.Character
	if not (Character and Character:FindFirstChildOfClass(`Humanoid`)) then return nil end
	local WasProtected = Character:GetAttribute(`Protected`)
	Character:SetAttribute(`Protected`, true)
	Character:SetAttribute(`NHInCine`, true)
	return function()
		if not Character.Parent then return end
		Character:SetAttribute(`NHInCine`, nil)
		Character:SetAttribute(`Protected`, WasProtected)
	end
end

function Local.Hold(Player: Player): (() -> ())?
	local Character = Player.Character
	local Humanoid = Character and Character:FindFirstChildOfClass(`Humanoid`)
	local Root = Character and Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	if not (Humanoid and Root) then return nil end
	local Speed, Jump, JumpH = Humanoid.WalkSpeed, Humanoid.JumpPower, Humanoid.JumpHeight
	local Mult = Humanoid:GetAttribute(`NH_SpeedMult`) -- (as Evolution.Freeze) save the base speed, not a slowed one
	if typeof(Mult) == `number` and Mult > 0 then Speed = Speed / Mult end
	local WasProtected = Character:GetAttribute(`Protected`)
	Humanoid.WalkSpeed = 0
	Humanoid.JumpPower = 0
	Humanoid.JumpHeight = 0
	Root.Anchored = true
	Character:SetAttribute(`NH_Evolving`, true) -- untouchable (Features.Downed), no vault / emote, Moments wait
	Character:SetAttribute(`Protected`, true)   -- AI and grabs leave you alone
	Character:SetAttribute(`NHInCine`, true)
	local State = StateManager.CreateState(Character, `InActivity`)
	return function()
		pcall(function() State:Destroy() end)
		if not Character.Parent then return end
		Character:SetAttribute(`NHInCine`, nil)
		Character:SetAttribute(`NH_Evolving`, nil)
		Character:SetAttribute(`Protected`, WasProtected)
		if Root.Parent then Root.Anchored = false end
		if Humanoid.Parent then
			if Humanoid.WalkSpeed == 0 then Humanoid.WalkSpeed = if Speed > 0 then Speed else 14.4 end
			Humanoid.JumpPower = Jump
			Humanoid.JumpHeight = JumpH
		end
	end
end

---| Sessions |---

function Local.Send(Player: Player, Message)
	if Player.Parent then Remote:FireClient(Player, Message) end
end

function Local.Watching(S): { Player }
	local List = {}
	for Player, V in S.Viewers do
		if not V.Ended then table.insert(List, Player) end
	end
	return List
end

-- a strict majority of the viewers still watching (doc 04 §5); anyone who has seen it counts as a skip vote
function Local.Need(S): number
	return math.floor(#Local.Watching(S) / 2) + 1
end

function Local.Votes(S): number
	local N = 0
	for _, V in S.Viewers do
		if not V.Ended and (V.Voted or V.SeenBefore) then N += 1 end
	end
	return N
end

function Local.BroadcastVotes(S)
	if not S.Group then return end
	local Votes, Need = Local.Votes(S), Local.Need(S)
	for _, Player in Local.Watching(S) do
		Local.Send(Player, { Kind = `Votes`; Session = S.Id; Votes = Votes; Need = Need })
	end
	if #Local.Watching(S) > 0 and Votes >= Need then
		for _, Player in Local.Watching(S) do Local.End(S, Player, `Skipped`) end
	end
end

-- one viewer is finished with the cut (every path out comes through here, once per viewer)
function Local.End(S, Player: Player, How: string)
	local V = S.Viewers[Player]
	if not V or V.Ended then return end
	V.Ended = true
	if ByPlayer[Player] == S.Id then ByPlayer[Player] = nil end
	if V.Release then
		local Release = V.Release
		V.Release = nil
		-- (doc 04 §4) control comes back with a short grace after the camera has landed
		task.delay(if How == `Left` then 0 else Config.SkipGrace, function() pcall(Release) end)
	end
	if How ~= `Left` and How ~= `Died` then Local.Mark(Player, S.CutId, `Seen`) end
	if How ~= `Done` and How ~= `Left` then Local.Send(Player, { Kind = `End`; Session = S.Id; How = How }) end
	if S.OnFinish then task.spawn(S.OnFinish, Player, How) end
	Shared.Finished:Fire(Player, S.CutId, How)
	if #Local.Watching(S) == 0 then
		Sessions[S.Id] = nil
		workspace:SetAttribute(`NHCinePlaying`, if next(Sessions) ~= nil then true else nil) -- (2.29) World.Scenes waits for cuts
	elseif S.Group then
		Local.BroadcastVotes(S) -- the majority is of those still watching
	end
end

function Local.ArmTimeout(S, Player: Player, Seconds: number)
	local V = S.Viewers[Player]
	if not V then return end
	local Token = {}
	V.Timer = Token
	task.delay(Seconds, function()
		if V.Timer == Token and not V.Ended then Local.End(S, Player, `Timeout`) end
	end)
end

-- the register name the cut reads out (Services.Player.Identity: "First Clan"), or the display name
function Local.NameOf(Player: Player): string
	local Ok, Name = pcall(function()
		local Identity = require(ServerScriptService.Services.Player.Identity)
		return Identity.FullName(Identity.Get(Player))
	end)
	return if Ok and typeof(Name) == `string` and Name ~= `` then Name else Player.DisplayName
end

-- a set mark in this place (workspace.NHCineSets.<Set>.<Mark>)
function Local.SetMark(Set: string?, Name: string?): BasePart?
	local Sets = workspace:FindFirstChild(`NHCineSets`)
	local S = Sets and Set and Sets:FindFirstChild(Set)
	local M = S and Name and S:FindFirstChild(Name)
	return if M and M:IsA(`BasePart`) then M else nil
end

---| interactive cuts (2.25.0): the graph lives in the cut module (ReplicatedStorage.Cinematics.<Id>.Graph) |---

function Local.FlagsFor(Player: Player, Cut): { [string]: string }
	local Out = {}
	for _, F in Cut.Flags or {} do
		local Ok, V = pcall(function() return Quests().Decided(Player, F) end)
		if Ok and typeof(V) == `string` then Out[F] = V end
	end
	return Out
end

function Local.GraphOf(CutId: string)
	local Ok, Def = pcall(function() return require(ReplicatedStorage.Cinematics[CutId]) end)
	return if Ok and typeof(Def) == `table` and typeof(Def.Graph) == `table` then Def.Graph else nil
end

function Local.Flag(Player: Player, Flag: string, Outcome: string)
	pcall(function() Quests().Decide(Player, Flag, Outcome) end)
end

function Local.Score(V, Seg: string, P, Outcome: string, Points: number)
	V.Judged[Seg] = { Outcome = Outcome }
	V.Points += Points
	V.Max += Judge.MAX[P.kind] or 0
	if Outcome == `Perfect` then V.Perfects += 1 end
end

function Local.CleanInput(M, P)
	local Window = Judge.Window(P, { Reduced = M.Reduced == true })
	local Times = {}
	if typeof(M.Times) == `table` then
		for I, T in M.Times do
			if I > 64 then break end
			if typeof(T) == `number` and T == T and T >= -0.5 and T <= Window + 0.5 then table.insert(Times, T) end
		end
	end
	return { Times = Times; Pick = if typeof(M.Pick) == `string` then M.Pick else nil; PickAt = tonumber(M.PickAt);
		Release = tonumber(M.Release); Touch = M.Touch == true; Reduced = M.Reduced == true }
end

-- a group's prompt is decided when everyone still watching has answered, or at its deadline (missing = a miss)
function Local.Decide(S, Seg: string)
	S.Decided = S.Decided or {}
	if S.Decided[Seg] then return end
	local P = S.Graph.segments[Seg].prompt
	local Outs = {}
	for Player, V in S.Viewers do
		if not V.Ended then
			if not V.Judged[Seg] then
				local O, Pts = Judge.Evaluate(P, {})
				Local.Score(V, Seg, P, O, Pts)
			end
			table.insert(Outs, V.Judged[Seg].Outcome)
		end
	end
	if #Outs == 0 then return end
	S.Decided[Seg] = true
	local Team = Judge.Team(P, Outs)
	local Next = Judge.Branch(P, Team)
	local StartAt = workspace:GetServerTimeNow() + 0.25
	S.Seg, S.SegStartAt = Next, StartAt
	for Player, V in S.Viewers do
		if not V.Ended then
			if P.flag then Local.Flag(Player, P.flag, Team) end
			Local.Send(Player, { Kind = `Branch`; Session = S.Id; Seg = Seg; Next = Next; StartAt = StartAt;
				Outcome = V.Judged[Seg].Outcome; Team = Team })
		end
	end
	Local.ArmPrompt(S)
end

function Local.TryDecide(S, Seg: string)
	for _, V in S.Viewers do
		if not V.Ended and not V.Judged[Seg] then return end
	end
	Local.Decide(S, Seg)
end

-- group: from the current segment, follow next links to the next prompt and set its deadline on the shared clock
function Local.ArmPrompt(S)
	if not (S.Graph and S.Group) then return end
	local N, At = S.Seg, S.SegStartAt
	local Seen = {}
	while N and not Seen[N] do
		Seen[N] = true
		local Node = S.Graph.segments[N]
		if not Node then return end
		if Node.prompt then
			local P, Seg = Node.prompt, N
			local Deadline = At + P.at + Judge.Window(P, { Reduced = true }) + Judge.GRACE
			task.delay(math.max(0, Deadline - workspace:GetServerTimeNow()), function()
				if Sessions[S.Id] then Local.Decide(S, Seg) end
			end)
			return
		end
		At += Node.len
		N = Node.next
	end
end

function Local.OnInput(S, Player: Player, V, M)
	if not S.Graph or typeof(M.Seg) ~= `string` then return end
	local Node = S.Graph.segments[M.Seg]
	local P = Node and Node.prompt
	if not P or V.Judged[M.Seg] then return end
	if not Judge.Follows(S.Graph, S.Seg, M.Seg) then return end
	local Outcome, Points = Judge.Evaluate(P, Local.CleanInput(M, P))
	Local.Score(V, M.Seg, P, Outcome, Points)
	if S.Group then
		Local.TryDecide(S, M.Seg)
	else
		V.Judged[M.Seg].Next = Judge.Branch(P, Outcome)
		if P.flag then Local.Flag(Player, P.flag, Outcome) end
	end
end

-- solo: the client says where it is now (it branches on its own); only real moves along the graph are accepted
function Local.OnSeg(S, Player: Player, V, M)
	if typeof(M.Name) ~= `string` then return end
	local Seamless = Config.Cuts[S.CutId] ~= nil and Config.Cuts[S.CutId].Seamless == true
	-- (fix round 1) a beat has no timeout because the player drives it (spec §4.3): entering one invalidates the pending
	-- timer (ArmTimeout's token); the next segment that isn't a beat arms a fresh Length + TimeoutPad. Leaving Wickfield
	-- stays the safety net.
	if Seamless and not S.Group and V and not V.Ended then
		if M.Beat == true then
			V.Timer = {}
			V.InBeat = true
		elseif V.InBeat then
			V.InBeat = nil
			Local.ArmTimeout(S, Player, Config.Cuts[S.CutId].Length + Config.TimeoutPad)
		end
	end
	if S.Graph == nil then
		-- (2.35.0) a seamless cut without a prompt graph (shots only, or shots and beats): nothing to judge, but every
		-- segment the client reaches is a resume checkpoint (the server can't build the cut, so the name is only bounded)
		if Seamless and not S.Group and #M.Name <= 40 and M.Name:match(`^[%w_]+$`) then
			pcall(function() require(script.Parent.Tutorial).Checkpoint(Player, S.CutId, M.Name) end)
		end
		return
	end
	if S.Group or not S.Graph.segments[M.Name] then return end
	local Cur = S.Seg
	local Ok = Judge.Follows(S.Graph, Cur, M.Name)
	if not Ok then
		-- through a prompt: only after it was judged (the server's own verdict says which way)
		local J = V.Judged[Cur]
		if J then
			for _, T in Judge.Successors(S.Graph, Cur) do
				if Judge.Follows(S.Graph, T, M.Name) then Ok = true end
			end
			if Ok and J.Next and not Judge.Follows(S.Graph, J.Next, M.Name) then
				warn(`[Cine] {Player.Name}: solo branch {Cur} -> {M.Name}, but the server judged {J.Next}`)
			end
		end
	end
	if not Ok then return end
	S.Seg = M.Name
	S.SegStartAt = tonumber(M.At) or workspace:GetServerTimeNow()
	if Seamless then
		pcall(function() require(script.Parent.Tutorial).Checkpoint(Player, S.CutId, M.Name) end)
	end
end

-- the grade, once, when the client reaches the end of the cut; saved as the best, and the first viewing pays a bonus
function Local.SendGrade(S, Player: Player, V)
	if V.Graded then return end
	V.Graded = true
	local Cut = Config.Cuts[S.CutId]
	local Grade = Judge.Grade(V.Points, V.Max)
	if Grade then
		pcall(function()
			local G = Quests().CineGrades(Player)
			if not G then return end
			local Old = G[S.CutId]
			if not Old or (Judge.GRADE_RANK[Grade] or 0) > (Judge.GRADE_RANK[Old.Best] or 0) then
				G[S.CutId] = { Best = Grade; Points = V.Points; Max = V.Max }
				Quests().SyncForCine(Player)
			end
		end)
		local First = not V.SeenBefore and not S.Skippable
		local Bonus = First and Cut.Rewards and Cut.Rewards[Grade]
		if typeof(Bonus) == `number` and Bonus > 0 then
			pcall(function()
				require(ServerScriptService.Services.Player.Data).UpdateState(Player, { type = `UpdateYen`; amount = Bonus })
			end)
		end
	end
	Local.Send(Player, { Kind = `Grade`; Session = S.Id; Grade = Grade; Points = V.Points; Max = V.Max; Perfects = V.Perfects;
		Show = Cut.ShowGrade ~= false })
end

function Shared.Play(List: { Player }, CutId: string, Opts: any?): string?
	local Cut = Config.Cuts[CutId]
	if not Cut then warn(`[Cine] unknown cut {CutId}`) return nil end
	Opts = Opts or {}
	local S = { Id = HttpService:GenerateGUID(false); CutId = CutId; Viewers = {}; OnFinish = Opts.OnFinish;
		Group = #List > 1; Skippable = Opts.Skippable == true }
	local Ids = {}
	for _, Player in List do
		if not Player.Parent or ByPlayer[Player] or Player:GetAttribute(`InMainMenu`) == true then continue end
		local SeenBefore = Shared.Seen(Player, CutId)
		local StartedBefore = Shared.Started(Player, CutId)
		-- (Cuts[Id].Arrive) a story cut that ends where you are now: the first time, you're placed on that mark (the
		-- prologue seats you in Room 102); a replay leaves you where you stand
		local Arrive = not Cut.Seamless and not SeenBefore and not Opts.Skippable and Local.SetMark(Cut.Set, Cut.Arrive)
		-- set marks sit on the floor; a character's pivot is its root, 3 studs up
		if Arrive and Player.Character then pcall(function() Player.Character:PivotTo(Arrive.CFrame * CFrame.new(0, 3, 0)) end) end
		local Release = if Cut.Seamless then Local.HoldSeamless(Player) else Local.Hold(Player)
		if not Release then continue end
		Local.Mark(Player, CutId, `Started`) -- saved before it plays: a disconnect mid-cut replays on rejoin
		if Cut.Seamless then pcall(function() require(script.Parent.Tutorial).Checkpoint(Player, CutId, `Start`) end) end
		S.Viewers[Player] = { SeenBefore = SeenBefore; StartedBefore = StartedBefore; Release = Release;
			Points = 0; Max = 0; Perfects = 0; Judged = {} }
		ByPlayer[Player] = S.Id
		table.insert(Ids, Player.UserId)
	end
	if #Ids == 0 then return nil end
	S.Group = #Ids > 1
	Sessions[S.Id] = S
	workspace:SetAttribute(`NHCinePlaying`, true) -- (2.29) World.Scenes waits for cuts
	S.Graph = Local.GraphOf(CutId)
	if S.Graph then S.Seg = S.Graph.start end
	local StartAt = workspace:GetServerTimeNow() + (if S.Group then Config.GroupLead else 0)
	S.SegStartAt = StartAt
	for Player, V in S.Viewers do
		-- personal: skippable once seen (or started: the rejoin replay); group: by vote only (doc 04 §2)
		local Skippable = S.Skippable or (not S.Group and (V.SeenBefore or V.StartedBefore))
		Local.Send(Player, { Kind = `Play`; Session = S.Id; Id = CutId; StartAt = StartAt; Skippable = Skippable;
			Group = S.Group; Viewers = Ids; Need = Local.Need(S); Votes = Local.Votes(S); Name = Local.NameOf(Player);
			Seamless = Cut.Seamless == true; Interactive = S.Graph ~= nil; Solo = not S.Group; Flags = Local.FlagsFor(Player, Cut) })
		-- the client may take a moment to get ready (the menu finishing); the real timer starts when it says Began
		Local.ArmTimeout(S, Player, Config.StartGrace + Cut.Length + Config.TimeoutPad)
		Shared.Began:Fire(Player, CutId)
	end
	Local.ArmPrompt(S)
	if S.Group then Local.BroadcastVotes(S) end
	return S.Id
end

-- (fix round 1) stands a player a beat crouched (the beat's end, Tutorial.Leave, leaving the game); a crouch of their
-- own is left alone
function Shared.EndBeatCrouch(Player: Player)
	if not BeatCrouched[Player] then return end
	BeatCrouched[Player] = nil
	local C = Player.Character
	local H = C and C:FindFirstChildWhichIsA(`Humanoid`)
	if H then pcall(require(ServerScriptService.Services.Player.Crouch).Stand, H) end
end

-- (task 9) ends the player's running session (Tutorial.Leave: the safety net for an open-ended beat). The client sees
-- the normal non-blended end for How ("Skipped" is the skip-style dip).
function Shared.EndFor(Player: Player, How: string?)
	local Id = ByPlayer[Player]
	local S = Id and Sessions[Id]
	if S then Local.End(S, Player, How or `Skipped`) end
end

function Shared.IsWatching(Player: Player, CutId: string?): boolean
	local Id = ByPlayer[Player]
	local S = Id and Sessions[Id]
	return S ~= nil and (CutId == nil or S.CutId == CutId)
end

---| Client messages |---

function Local.OnMessage(Player: Player, Message)
	if typeof(Message) ~= `table` or typeof(Message.Kind) ~= `string` then return end
	local Now = os.clock()
	local R = Rate[Player]
	if not R or Now - R.At > 1 then R = { At = Now; N = 0 } Rate[Player] = R end
	R.N += 1
	if R.N > RATE then return end

	if Message.Kind == `Replay` then
		local Id = Message.Id
		local Cut = typeof(Id) == `string` and Config.Cuts[Id]
		if Cut and Cut.Replay and Shared.Seen(Player, Id) and not ByPlayer[Player] then
			Shared.Play({ Player }, Id, { Skippable = true })
		end
		return
	end

	-- (2.35.0) a walk-and-talk beat holds crouch (spec §3 move.crouch): the server's Crouch service owns the state
	-- (fix round 1) Crouch takes the Character (Crouch) and the Humanoid (Stand). Crouching needs NHTutorial; standing a
	-- beat's crouch back up doesn't (Tutorial.Leave calls Shared.EndBeatCrouch too)
	if Message.Kind == `BeatCrouch` then
		if Message.On == true then
			local C = Player.Character
			if Player:GetAttribute(`NHTutorial`) == true and C then
				local Ok, Did = pcall(require(ServerScriptService.Services.Player.Crouch).Crouch, C)
				if Ok and Did then BeatCrouched[Player] = true end
			end
		else
			Shared.EndBeatCrouch(Player)
		end
		return
	end

	local S = typeof(Message.Session) == `string` and Sessions[Message.Session]
	local V = S and S.Viewers[Player]
	if not V or V.Ended then return end
	local Cut = Config.Cuts[S.CutId]
	if Message.Kind == `Began` then
		if not V.BeganAt then
			V.BeganAt = Now
			if V.InBeat then return end -- (fix round 1) a cut that opens on a beat: no timer until its first non-beat segment
			local Late = math.max(0, workspace:GetServerTimeNow() - (tonumber(Message.At) or workspace:GetServerTimeNow()))
			Local.ArmTimeout(S, Player, math.max(1, Cut.Length - (if S.Group then Late else 0)) + Config.TimeoutPad)
		end
	elseif Message.Kind == `Done` then
		Local.End(S, Player, `Done`)
	elseif Message.Kind == `Skip` then
		local Can = S.Skippable or (not S.Group and (V.SeenBefore or V.StartedBefore))
		if Can then Local.End(S, Player, `Skipped`) end
	elseif Message.Kind == `Vote` then
		if S.Group and not V.Voted then
			V.Voted = true
			Local.BroadcastVotes(S)
		end
	elseif Message.Kind == `Input` then
		Local.OnInput(S, Player, V, Message)
	elseif Message.Kind == `Seg` then
		Local.OnSeg(S, Player, V, Message)
	elseif Message.Kind == `Where` then
		if S.Graph then Local.Send(Player, { Kind = `Segment`; Session = S.Id; Name = S.Seg; StartAt = S.SegStartAt }) end
	elseif Message.Kind == `Grade` then
		if S.Graph then Local.SendGrade(S, Player, V) end
	end
end

---| Start |---

function Shared.OnStart()
	Remote = ReplicatedStorage:FindFirstChild(`NHCine`) :: RemoteEvent
	if not Remote then
		Remote = Instance.new(`RemoteEvent`)
		Remote.Name = `NHCine`
		Remote.Parent = ReplicatedStorage
	end
	Remote.OnServerEvent:Connect(function(Player, Message)
		local Ok, Err = pcall(Local.OnMessage, Player, Message)
		if not Ok then warn(`[Cine] {Err}`) end
	end)
	local function watch(Player: Player)
		Player.CharacterAdded:Connect(function()
			local Id = ByPlayer[Player]
			local S = Id and Sessions[Id]
			if S then Local.End(S, Player, `Died`) end -- a respawn ends the cut (the client's lease is gone too)
		end)
	end
	Players.PlayerAdded:Connect(watch)
	for _, Player in Players:GetPlayers() do watch(Player) end
	Players.PlayerRemoving:Connect(function(Player)
		local Id = ByPlayer[Player]
		local S = Id and Sessions[Id]
		if S then Local.End(S, Player, `Left`) end
		Rate[Player] = nil
		BeatCrouched[Player] = nil
	end)
end

---| Testing (TestBridge) |---

-- The group vote, on the real session code, with stand-ins for the other viewers (the MCP can only start a one-player
-- Play). Nothing is saved: the stand-ins aren't players, and the real player's own state is put back.
function Shared.VoteSelfTestForTests(Player: Player)
	local Out = {}
	local function fake(Name: string) return setmetatable({ Name = Name; Parent = game; UserId = -1 }, { __tostring = function() return Name end }) end
	local A, B, C = Player, fake(`StandInB`), fake(`StandInC`)
	local SentTo = {}
	local SavedState = table.clone(Local.State(Player) or {})
	local RealSend = Local.Send
	Local.Send = function(P, M) if P == Player then RealSend(P, M) end table.insert(SentTo, `{tostring(P)}:{M.Kind}`) end
	local Ok, Err = pcall(function()
		-- two viewers, nobody has seen it: one vote is not a majority, two are
		local S = { Id = `test2`; CutId = `Prologue`; Group = true; Viewers = {
			[A] = { SeenBefore = false }; [B] = { SeenBefore = false } } }
		Sessions[S.Id] = S
		Out.TwoNeed = Local.Need(S)
		S.Viewers[A].Voted = true
		Local.BroadcastVotes(S)
		Out.TwoAfterOneVote = { Votes = Local.Votes(S); Ended = S.Viewers[A].Ended == true }
		S.Viewers[B].Voted = true
		Local.BroadcastVotes(S)
		Out.TwoAfterTwoVotes = { EndedA = S.Viewers[A].Ended == true; EndedB = S.Viewers[B].Ended == true; Gone = Sessions[S.Id] == nil }
		-- three viewers, one has seen it (auto vote): one more vote skips; a leaver lowers the majority
		local S3 = { Id = `test3`; CutId = `Prologue`; Group = true; Viewers = {
			[A] = { SeenBefore = false }; [B] = { SeenBefore = true }; [C] = { SeenBefore = false } } }
		Sessions[S3.Id] = S3
		Out.ThreeNeed = Local.Need(S3)
		Out.ThreeAutoVotes = Local.Votes(S3)
		Local.End(S3, C, `Left`)
		Out.AfterLeaveNeed = Local.Need(S3)
		Out.AfterLeaveEnded = S3.Viewers[A].Ended == true -- B's auto vote is now 1 of 2 still watching: not yet a majority
		S3.Viewers[A].Voted = true
		Local.BroadcastVotes(S3)
		Out.AfterVoteEnded = S3.Viewers[A].Ended == true
	end)
	Local.Send = RealSend
	Sessions.test2, Sessions.test3 = nil, nil
	ByPlayer[Player] = nil
	-- the stand-in sessions marked the real player "Seen": put their cut state back as it was
	local Now = Local.State(Player)
	if Now then
		table.clear(Now)
		for K, V in SavedState do Now[K] = V end
		pcall(function() Quests().SyncForCine(Player) end)
	end
	if not Ok then Out.Error = tostring(Err) end
	Out.Messages = SentTo
	return Out
end

function Shared.EndForTests(Player: Player)
	local Id = ByPlayer[Player]
	local S = Id and Sessions[Id]
	if S then Local.End(S, Player, `Skipped`) end
end

function Shared.SessionsForTests()
	local Out = {}
	for Id, S in Sessions do
		local V = {}
		for P, X in S.Viewers do V[tostring(P)] = { Ended = X.Ended == true; Voted = X.Voted == true; Seen = X.SeenBefore == true } end
		Out[Id] = { Cut = S.CutId; Group = S.Group; Viewers = V }
	end
	return Out
end

-- (2.25.0) the group decide, the solo path check, Where and the grade on the real code, with stand-in viewers (the MCP
-- starts one-player Plays). Nothing is saved: messages to stand-ins are recorded, the real player's grades and
-- decisions are put back.
function Shared.QteSelfTestForTests(Player: Player)
	local Out = {}
	local function fake(Name: string) return setmetatable({ Name = Name; Parent = game; UserId = -1 }, { __tostring = function() return Name end }) end
	local A, B, C = Player, fake(`StandInB`), fake(`StandInC`)
	local Graph = { start = `A`; segments = {
		A = { len = 3; prompt = { kind = `Press`; at = 1; beat = 0.6; slow = 0.3; on = { Perfect = `B`; Good = `B`; Miss = `C` } } };
		B = { len = 2; next = `D` }; C = { len = 2; next = `D` };
		D = { len = 3; prompt = { kind = `Mash`; at = 0.5; dur = 1.6; rate = 7; slow = 0.5; on = { Win = `E`; Lose = `E` } } };
		E = { len = 1 } } }
	local Sent = {}
	local RealSend = Local.Send
	Local.Send = function(P, M) table.insert(Sent, { To = tostring(P); M = M }) end
	local SavedGrades = table.clone((Quests().CineGrades(Player)) or {})
	local function viewer() return { SeenBefore = false; Points = 0; Max = 0; Perfects = 0; Judged = {} } end
	local function msg(Kind, To) for I = #Sent, 1, -1 do if Sent[I].M.Kind == Kind and (To == nil or Sent[I].To == To) then return Sent[I].M end end return nil end
	local Ok, Err = pcall(function()
		-- 1. two viewers: a Perfect and a Miss tie -> the better outcome (Perfect) -> B; each keeps their own points
		local S = { Id = `qte1`; CutId = `Prologue`; Group = true; Graph = Graph; Seg = `A`; SegStartAt = 0; Viewers = { [A] = viewer(); [B] = viewer() } }
		Sessions[S.Id] = S
		Local.OnInput(S, A, S.Viewers[A], { Seg = `A`; Times = { 0.6 } })
		Out.WaitsForEveryone = msg(`Branch`) == nil
		Local.OnInput(S, B, S.Viewers[B], { Seg = `A`; Times = {} })
		local Br = msg(`Branch`, tostring(A))
		Out.TieBranch = Br and Br.Next
		Out.PointsA, Out.PointsB = S.Viewers[A].Points, S.Viewers[B].Points
		Out.SegAfter = S.Seg
		-- 2. Where tells a lost client the current segment
		Sent = {}
		Local.OnMessage(A, { Kind = `Where`; Session = `qte1` })
		local W = msg(`Segment`)
		Out.Where = W and W.Name
		-- 3. three viewers, two miss: majority -> C; a missing answer at the deadline counts as a miss
		Sent = {}
		local S3 = { Id = `qte3`; CutId = `Prologue`; Group = true; Graph = Graph; Seg = `A`; SegStartAt = 0;
			Viewers = { [A] = viewer(); [B] = viewer(); [C] = viewer() } }
		Sessions[S3.Id] = S3
		Local.OnInput(S3, A, S3.Viewers[A], { Seg = `A`; Times = { 0.8 } })
		Local.OnInput(S3, B, S3.Viewers[B], { Seg = `A`; Times = { 0.1 } })
		Local.Decide(S3, `A`) -- C never answered: the deadline
		local B3 = msg(`Branch`, tostring(A))
		Out.MajorityBranch = B3 and B3.Next
		-- 4. solo: input then a path report the server agrees with; a skip past an unjudged prompt is refused
		Sent = {}
		local S4 = { Id = `qte4`; CutId = `Prologue`; Group = false; Graph = Graph; Seg = `A`; SegStartAt = 0; Viewers = { [A] = viewer() } }
		Sessions[S4.Id] = S4
		Local.OnSeg(S4, A, S4.Viewers[A], { Name = `D`; At = 1 })
		Out.SoloSkipRefused = S4.Seg == `A`
		Local.OnInput(S4, A, S4.Viewers[A], { Seg = `A`; Times = { 0.62 } })
		Local.OnSeg(S4, A, S4.Viewers[A], { Name = `B`; At = 2 })
		Out.SoloMovedToB = S4.Seg == `B`
		Local.OnSeg(S4, A, S4.Viewers[A], { Name = `D`; At = 4 })
		Out.SoloNextChain = S4.Seg == `D`
		local Taps = {}
		for I = 1, 12 do Taps[I] = I * 0.13 end
		Local.OnInput(S4, A, S4.Viewers[A], { Seg = `D`; Times = Taps })
		Out.MashOutcome = S4.Viewers[A].Judged.D.Outcome
		-- 5. the grade: Perfect (3/3) + Mash Win (2/2) = 5/5 -> S
		Sent = {}
		Local.SendGrade(S4, A, S4.Viewers[A])
		local G = msg(`Grade`)
		Out.Grade = G and G.Grade
		Out.GradeSaved = ((Quests().CineGrades(Player)) or {}).Prologue ~= nil
	end)
	Local.Send = RealSend
	for _, Id in { `qte1`, `qte3`, `qte4` } do Sessions[Id] = nil end
	local G = Quests().CineGrades(Player)
	if G then table.clear(G) for K, V in SavedGrades do G[K] = V end pcall(function() Quests().SyncForCine(Player) end) end
	if not Ok then Out.Error = tostring(Err) end
	return Out
end

return Shared
