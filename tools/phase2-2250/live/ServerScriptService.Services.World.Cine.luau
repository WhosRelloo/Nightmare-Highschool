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

local function Quests() return require(ServerScriptService.Services.Quests.Quests) end -- lazy: Quests requires us too

local RATE = 12 -- messages a second per player

local Local = {}
local Shared = {}

Shared.Began = SignalPlus()    -- (Player, CutId)
Shared.Finished = SignalPlus() -- (Player, CutId, How)

local Remote: RemoteEvent = nil
local Sessions = {} :: { [string]: any }
local ByPlayer = {} :: { [Player]: string } -- the session each player is watching
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
		local Arrive = not SeenBefore and not Opts.Skippable and Local.SetMark(Cut.Set, Cut.Arrive)
		-- set marks sit on the floor; a character's pivot is its root, 3 studs up
		if Arrive and Player.Character then pcall(function() Player.Character:PivotTo(Arrive.CFrame * CFrame.new(0, 3, 0)) end) end
		local Release = Local.Hold(Player)
		if not Release then continue end
		Local.Mark(Player, CutId, `Started`) -- saved before it plays: a disconnect mid-cut replays on rejoin
		S.Viewers[Player] = { SeenBefore = SeenBefore; StartedBefore = StartedBefore; Release = Release }
		ByPlayer[Player] = S.Id
		table.insert(Ids, Player.UserId)
	end
	if #Ids == 0 then return nil end
	S.Group = #Ids > 1
	Sessions[S.Id] = S
	local StartAt = workspace:GetServerTimeNow() + (if S.Group then Config.GroupLead else 0)
	for Player, V in S.Viewers do
		-- personal: skippable once seen (or started: the rejoin replay); group: by vote only (doc 04 §2)
		local Skippable = S.Skippable or (not S.Group and (V.SeenBefore or V.StartedBefore))
		Local.Send(Player, { Kind = `Play`; Session = S.Id; Id = CutId; StartAt = StartAt; Skippable = Skippable;
			Group = S.Group; Viewers = Ids; Need = Local.Need(S); Votes = Local.Votes(S); Name = Local.NameOf(Player) })
		-- the client may take a moment to get ready (the menu finishing); the real timer starts when it says Began
		Local.ArmTimeout(S, Player, Config.StartGrace + Cut.Length + Config.TimeoutPad)
		Shared.Began:Fire(Player, CutId)
	end
	if S.Group then Local.BroadcastVotes(S) end
	return S.Id
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

	local S = typeof(Message.Session) == `string` and Sessions[Message.Session]
	local V = S and S.Viewers[Player]
	if not V or V.Ended then return end
	local Cut = Config.Cuts[S.CutId]
	if Message.Kind == `Began` then
		if not V.BeganAt then
			V.BeganAt = Now
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

function Shared.SessionsForTests()
	local Out = {}
	for Id, S in Sessions do
		local V = {}
		for P, X in S.Viewers do V[tostring(P)] = { Ended = X.Ended == true; Voted = X.Voted == true; Seen = X.SeenBefore == true } end
		Out[Id] = { Cut = S.CutId; Group = S.Group; Viewers = V }
	end
	return Out
end

return Shared
