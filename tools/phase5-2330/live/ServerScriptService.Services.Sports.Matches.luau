--[[
	Sports Matches (server): the sport-agnostic match core. One match per venue (Workspace.Sports.<Venue>,
	SportVenue = <sport>). The sport's rules live in Services.Sports.<Sport> (the plug-in):
		Plug.Setup(m)  Plug.Start(m)  Plug.Tick(m, dt)  Plug.OnAction(m, player, action, args)
		Plug.OnRemoved(m, player)  Plug.Stop(m)  Plug.Hud(m) -> table  Plug.Halftime(m)?  Plug.Drill*(...)
	Flow: Waiting (stand on a team pad) -> Countdown (10 s) -> Live -> Halftime -> Live -> (Overtime) -> Ended -> Waiting
	Removal: leaving the game, getting downed, dying, or 5 s outside SportBounds.
	Rewards (at the end, only for students who played >= MinPlaySeconds of live time):
		Progression SportMatch / SportWin / SportMvp, yen, popularity, and for members of that sport's club
		club EXP (Played / Won / Mvp) plus a win/loss record when the match is ranked (club hours + a member playing).
	Player attributes while playing: InSport = venue name, SportTeam = "A" | "B".
	Remotes (ReplicatedStorage.NHSports): Action (client intents, rate limited), Hud (state to players nearby),
	Summary (post-game card), Get / Updated (Clubs).
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local Config = require(ReplicatedStorage.Config.Sports)
local Data = require(ServerScriptService.Services.Player.Data)
local Clubs = require(script.Parent.Clubs)

local Shared = {}
local Local = {}
local Matches = {} :: { [string]: any }
local PlayerMatch = {} :: { [Player]: any }
local Remotes = nil

local MIN_PLAY_SECONDS = 60
local MATCH_REWARD_COOLDOWN = 180   -- one rewarded game per player every 3 minutes (real games run longer)
local PaidAt = {} :: { [number]: number }
local OUT_OF_BOUNDS_SECONDS = 5
local ENDED_SECONDS = 8
local ACTION_RATE = 20      -- per second, per player

local function try(Path: { string })
	local M = ServerScriptService
	for _, N in Path do M = M and M:FindFirstChild(N) end
	if not M then return nil end
	local Ok, Mod = pcall(require, M)
	return if Ok then Mod else nil
end

local function notify(Player: Player, Data_)
	local N = try({ `Services`, `Features`, `Notifications` })
	if N then pcall(N.Notify, Player, Data_) end
end

---| eligibility |---

function Local.Alive(Player: Player): boolean
	local Char = Player.Character
	local Hum = Char and Char:FindFirstChildOfClass(`Humanoid`)
	local Root = Char and Char:FindFirstChild(`HumanoidRootPart`)
	if not (Hum and Root and Hum.Health > 0) then return false end
	local Downed = try({ `Services`, `Features`, `Downed` })
	if Downed and Downed.IsDowned(Char) then return false end
	return true
end

function Local.Free(Player: Player): (boolean, string?)
	if not Local.Alive(Player) then return false end
	local Char = Player.Character
	if Char:GetAttribute(`Dueling`) then return false, `You're in a duel.` end
	if Char:GetAttribute(`NH_Evolving`) then return false end
	if Player:GetAttribute(`InDrill`) then return false, `Finish your drill first.` end
	if not Data.GetProfile(Player) then return false end
	return true
end

local function rootPos(Player: Player): Vector3?
	local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	return Root and Root.Position
end

function Local.Inside(Part: BasePart, Pos: Vector3, Margin: number?): boolean
	local L = Part.CFrame:PointToObjectSpace(Pos)
	local M = Margin or 0
	return math.abs(L.X) <= Part.Size.X / 2 + M and math.abs(L.Y) <= Part.Size.Y / 2 + M and math.abs(L.Z) <= Part.Size.Z / 2 + M
end

function Local.OnPad(Pad: BasePart, Player: Player): boolean
	local P = rootPos(Player)
	if not P then return false end
	local D = Vector3.new(P.X - Pad.Position.X, 0, P.Z - Pad.Position.Z).Magnitude
	return D <= Pad.Size.Y / 2 + 0.5 and math.abs(P.Y - Pad.Position.Y) < 5
end

---| match object |---

local Match = {}
Match.__index = Match

local function find(Venue: Model, Attr: string, Value: any?): BasePart?
	for _, D in Venue:GetDescendants() do
		if D:IsA(`BasePart`) and D:GetAttribute(Attr) ~= nil and (Value == nil or D:GetAttribute(Attr) == Value) then return D end
	end
	return nil
end

function Match.new(Venue: Model)
	local Sport = Venue:GetAttribute(`SportVenue`)
	local self = setmetatable({
		Venue = Venue; Name = Venue.Name; Sport = Sport; Tuning = Config[Sport] or {};
		Pads = { A = find(Venue, `SportPad`, `A`); B = find(Venue, `SportPad`, `B`) };
		KeeperPads = { A = find(Venue, `SportKeeperPad`, `A`); B = find(Venue, `SportKeeperPad`, `B`) };   -- soccer
		FromKeeperPad = {} :: { [Player]: boolean };
		Court = find(Venue, `SportCourt`); Bounds = find(Venue, `SportBounds`); BallSpawn = find(Venue, `SportBall`);
		Board = find(Venue, `SportScoreboard`);
		Plug = nil; Phase = `Waiting`; Clock = 0; Half = 1; Overtime = false;
		Score = { A = 0; B = 0 }; Teams = { A = {}; B = {} }; Team = {} :: { [Player]: string };
		Stats = {} :: { [Player]: any }; Played = {} :: { [Player]: number }; OutSince = {} :: { [Player]: number };
		Queue = { A = {}; B = {} }; LiveTime = 0; Ranked = false; Message = ``; MessageUntil = 0;
		Ball = nil;
	}, Match)
	local PlugModule = script.Parent:FindFirstChild(Sport)
	if PlugModule then
		local Ok, Plug = pcall(require, PlugModule)
		if Ok and type(Plug) == `table` and Plug.Setup then self.Plug = Plug else warn(`[Sports] {Sport} rules failed to load: {Plug}`) end
	end
	if self.Plug then
		local Ok, Err = pcall(self.Plug.Setup, self)
		if not Ok then warn(`[Sports] {Sport} Setup: {Err}`) self.Plug = nil end
	end
	return self
end

function Match:Tune(Key: string, Default: any): any
	local V = self.Tuning[Key]
	if V == nil then return Default end
	return V
end

function Match:Players(): { Player }
	local List = {}
	for P in self.Team do table.insert(List, P) end
	return List
end

function Match:Opponent(Team: string): string return if Team == `A` then `B` else `A` end

function Match:Say(Text: string, Seconds: number?)
	self.Message = Text
	self.MessageUntil = os.clock() + (Seconds or 3)
end

-- Plug-ins call this when a team scores
function Match:Scored(Team: string, Points: number, Scorer: Player?)
	if self.Phase ~= `Live` then return end
	self.Score[Team] += Points
	if Scorer and self.Stats[Scorer] then self.Stats[Scorer].Points += Points end
	local Win = self:Tune(`WinScore`, math.huge)
	local Mercy = self:Tune(`MercyLead`, math.huge)
	if self.Overtime or self.Score[Team] >= Win or self.Score[Team] - self.Score[self:Opponent(Team)] >= Mercy then
		self:End(Team, if self.Overtime then `Overtime winner` elseif self.Score[Team] >= Win then `First to {Win}` else `{Mercy}-{self:Tune(`ScoreWord`, `goal`)} lead`)
	end
end

function Match:Stat(Player: Player, Key: string, Amount: number?)
	local S = self.Stats[Player]
	if S then S[Key] = (S[Key] or 0) + (Amount or 1) end
end

---| teams |---

function Match:Add(Player: Player, Team: string)
	self.Team[Player] = Team
	table.insert(self.Teams[Team], Player)
	self.Stats[Player] = self.Stats[Player] or { Points = 0; Assists = 0; Steals = 0; Blocks = 0; Rebounds = 0; Touches = 0 }
	self.Played[Player] = self.Played[Player] or 0
	PlayerMatch[Player] = self
	Player:SetAttribute(`InSport`, self.Name)
	Player:SetAttribute(`SportTeam`, Team)
	if Player.Character then Player.Character:SetAttribute(`InSport`, self.Name) end
	Local.Armband(Player, Team)
	local Crouch = try({ `Services`, `Player`, `Crouch` })
	local Hum = Player.Character and Player.Character:FindFirstChildOfClass(`Humanoid`)
	if Crouch and Hum and Crouch.IsCrouched(Hum) then pcall(Crouch.Stand, Hum) end
end

function Match:Remove(Player: Player, Why: string?)
	local Team = self.Team[Player]
	if not Team then return end
	if self.Plug and self.Plug.OnRemoved then pcall(self.Plug.OnRemoved, self, Player) end
	self.Team[Player] = nil
	local List = self.Teams[Team]
	local I = table.find(List, Player)
	if I then table.remove(List, I) end
	self.OutSince[Player] = nil
	PlayerMatch[Player] = nil
	if Player.Parent then
		Player:SetAttribute(`InSport`, nil)
		Player:SetAttribute(`SportTeam`, nil)
		if Player.Character then Player.Character:SetAttribute(`InSport`, nil) end
		Local.Armband(Player, nil)
		if Remotes then Remotes.Hud:FireClient(Player, nil) end
		if Why then notify(Player, { Title = `Out of the game`; Text = Why; Kind = `Info`; Duration = 4 }) end
	end
	if (self.Phase == `Live` or self.Phase == `Halftime`) and #self.Teams.A + #self.Teams.B == 0 then
		self:End(nil, `Everyone left`)
	elseif (self.Phase == `Live` or self.Phase == `Halftime`) and not self.SoloTest then
		if #self.Teams.A == 0 or #self.Teams.B == 0 then
			local Winner = if #self.Teams.A > 0 then `A` elseif #self.Teams.B > 0 then `B` else nil
			self:End(Winner, `Forfeit`)
		end
	end
end

-- even out teams: sizes differ by at most 1, capped per side
function Match:Balance(A: { Player }, B: { Player }): ({ Player }, { Player })
	local Max = self:Tune(`MaxPerSide`, 5)
	while #A > #B + 1 do table.insert(B, table.remove(A)) end
	while #B > #A + 1 do table.insert(A, table.remove(B)) end
	while #A > Max do table.remove(A) end
	while #B > Max do table.remove(B) end
	return A, B
end

---| phases |---

function Match:Start()
	local A, B = self:Balance(table.clone(self.Queue.A), table.clone(self.Queue.B))
	local Min = if self.SoloTest then 0 else self:Tune(`MinPerSide`, 1)
	if #A < Min or #B < Min or #A + #B == 0 then self.Phase = `Waiting` return end
	self.Score = { A = 0; B = 0 }
	self.Stats, self.Played = {}, {}
	self.Half, self.Overtime, self.LiveTime = 1, false, 0
	for _, P in A do self:Add(P, `A`) end
	for _, P in B do self:Add(P, `B`) end
	self.Clock = self:Tune(`HalfSeconds`, 240)
	self.Ranked = Local.IsRanked(self)
	self.Phase = `Live`
	local Word = self:Tune(`StartWord`, `tip-off`)
	self:Say(if self.Ranked then `Ranked club game: {Word}!` else `Pickup game: {Word}!`, 3)
	if self.Plug and self.Plug.Start then
		local Ok, Err = pcall(self.Plug.Start, self)
		if not Ok then warn(`[Sports] Start: {Err}`) self:End(nil, `Something went wrong`) end
	end
end

function Match:End(Winner: string?, Why: string)
	if self.Phase == `Ended` or self.Phase == `Waiting` then return end
	self.Phase = `Ended`
	self.Clock = ENDED_SECONDS
	self.Winner = Winner
	if self.Plug and self.Plug.Stop then pcall(self.Plug.Stop, self) end
	local Summary = Local.Reward(self, Winner, Why)
	if Winner and self.Ranked then -- (2.33) a ranked club game won counts toward the Club Cup (Services.Player.Paths)
		for _, P in self.Teams[Winner] or {} do pcall(function() require(ServerScriptService.Services.Player.Paths).Count(P, `MatchWins`) end) end
	end
	pcall(function() -- (2.29) the incident bus (World.Incidents; rumours come from it)
		local Root = self.Venue and self.Venue:IsA(`Model`) and self.Venue:GetPivot().Position or nil
		local Team = Winner and Config.Teams[Winner] and Config.Teams[Winner].Name
		require(ServerScriptService.Services.World.Incidents).Emit({ Kind = `Match`; Where = Root; Sport = self.Sport;
			Winner = Team; Score = table.clone(self.Score); Severity = 1; Extra = Team and `{self.Sport}.` or nil;
			Who = if Team then { { Id = Team; Role = `Doer` } } else {} })
	end)
	for _, P in self:Players() do
		if Remotes then Remotes.Summary:FireClient(P, Summary) end
	end
	self:Say(if Winner then `{Config.Teams[Winner].Name} win!` else `It's a tie.`, ENDED_SECONDS)
end

function Match:Reset()
	self.SoloTest = nil
	self.BuzzerWait = 0
	for _, P in self:Players() do self:Remove(P) end
	self.Phase = `Waiting`
	self.Score = { A = 0; B = 0 }
	self.Clock = 0
	self.Queue = { A = {}; B = {} }
	if self.Plug and self.Plug.Reset then pcall(self.Plug.Reset, self) end
end

function Match:Step(dt: number)
	local Now = os.clock()
	if self.Phase == `Waiting` or self.Phase == `Countdown` then
		-- queue from the pads
		table.clear(self.FromKeeperPad)
		for _, T in { `A`, `B` } do
			local Q = {}
			local Pad = self.Pads[T]
			local KPad = self.KeeperPads[T]
			for _, P in Players:GetPlayers() do
				if not PlayerMatch[P] and Local.Free(P) then
					-- keeper pads queue for that team too, first in line so balancing never moves the keeper
					if KPad and Local.OnPad(KPad, P) then table.insert(Q, 1, P) self.FromKeeperPad[P] = true
					elseif Pad and Local.OnPad(Pad, P) then table.insert(Q, P) end
				end
			end
			self.Queue[T] = Q
		end
		local Min = self:Tune(`MinPerSide`, 1)
		local Ready = self.Plug ~= nil and #self.Queue.A >= Min and #self.Queue.B >= Min
		if self.Phase == `Waiting` and Ready then
			self.Phase = `Countdown`
			self.Clock = self:Tune(`Countdown`, 10)
		elseif self.Phase == `Countdown` then
			if not Ready then self.Phase = `Waiting` self.Clock = 0
			else
				self.Clock -= dt
				if self.Clock <= 0 then self:Start() end
			end
		end
		return
	end
	if self.Phase == `Ended` then
		self.Clock -= dt
		if self.Clock <= 0 then self:Reset() end
		return
	end
	-- Live / Halftime: removals
	for _, P in self:Players() do
		if not P.Parent then self:Remove(P) continue end
		if not Local.Alive(P) then self:Remove(P, `You went down, so you're out of the game.`) continue end
		local Pos = rootPos(P)
		if Pos and self.Bounds and not Local.Inside(self.Bounds, Pos, 0) then
			self.OutSince[P] = self.OutSince[P] or Now
			if Now - self.OutSince[P] >= OUT_OF_BOUNDS_SECONDS then self:Remove(P, `You left the court.`) end
		else
			self.OutSince[P] = nil
		end
	end
	if self.Phase ~= `Live` and self.Phase ~= `Halftime` then return end
	-- late arrivals fill open slots on their pad's team
	if self.Phase == `Live` then
		local Max = self:Tune(`MaxPerSide`, 5)
		for _, T in { `A`, `B` } do
			local Pad = self.Pads[T]
			if Pad and #self.Teams[T] < Max and #self.Teams[T] <= #self.Teams[self:Opponent(T)] then
				for _, P in Players:GetPlayers() do
					if not PlayerMatch[P] and Local.OnPad(Pad, P) and Local.Free(P) then
						self:Add(P, T)
						if self.Plug and self.Plug.Joined then pcall(self.Plug.Joined, self, P) end
						break
					end
				end
			end
		end
	end
	if self.Phase == `Halftime` then
		self.Clock -= dt
		if self.Clock <= 0 then
			self.Half = 2
			self.Phase = `Live`
			self.Clock = self:Tune(`HalfSeconds`, 240)
			self:Say(`Second half!`, 3)
			if self.Plug and self.Plug.Start then pcall(self.Plug.Start, self, true) end
		end
		return
	end
	-- Live
	self.LiveTime += dt
	for P in self.Team do self.Played[P] = (self.Played[P] or 0) + dt end
	if self.Plug and self.Plug.Tick then
		local Ok, Err = pcall(self.Plug.Tick, self, dt)
		if not Ok then warn(`[Sports] Tick: {Err}`) end
	end
	if self.Phase ~= `Live` then return end
	self.Clock -= dt
	if self.Clock <= 0 and self.Plug and self.Plug.Busy and self.Plug.Busy(self) and (self.BuzzerWait or 0) < 4 then
		self.BuzzerWait = (self.BuzzerWait or 0) + dt   -- buzzer-beater in the air: let it land (3 s at most)
		self.Clock = 0
		return
	end
	if self.Clock <= 0 then
		self.BuzzerWait = 0
		if self.Overtime then
			self:End(nil, `Overtime ran out`)
		elseif self.Half == 1 then
			self.Phase = `Halftime`
			self.Clock = self:Tune(`Halftime`, 10)
			self:Say(`Halftime`, 4)
			if self.Plug and self.Plug.Halftime then pcall(self.Plug.Halftime, self) end
		elseif self.Score.A ~= self.Score.B then
			self:End(if self.Score.A > self.Score.B then `A` else `B`, `Time`)
		else
			self.Overtime = true
			self.Clock = 120
			self:Say(`Overtime: next score wins`, 4)
			if self.Plug and self.Plug.Start then pcall(self.Plug.Start, self, true) end
		end
	end
end

---| ranked + rewards |---

function Local.IsRanked(m): boolean
	local Clock = try({ `Services`, `School`, `SchoolClock` })
	local State = Clock and Clock.GetState()
	local Hour = State and State.Hour
	if not Hour or Hour < Config.ClubHours.From or Hour >= Config.ClubHours.To then return false end
	for P in m.Team do
		local S = Clubs.Get(P)
		if S and S.Club and Config.Clubs[S.Club].Sport == m.Sport then return true end
	end
	return false
end

function Local.Reward(m, Winner: string?, Why: string)
	local Progression = try({ `Services`, `Player`, `Progression` })
	local Rep = try({ `Services`, `Social`, `Reputation` })
	-- MVP: most points, then most other plays
	local Mvp, Best = nil, -1
	for P, S in m.Stats do
		local V = if m.Plug and m.Plug.MvpScore then m.Plug.MvpScore(m, P, S) else S.Points * 10 + (S.Assists + S.Steals + S.Blocks + S.Rebounds)
		if m.Team[P] and V > Best then Mvp, Best = P, V end
	end
	if Best <= 0 then Mvp = nil end
	local Counted = m.LiveTime >= MIN_PLAY_SECONDS and Why ~= `Something went wrong`
	local Lines = {}
	for P, Team in m.Team do
		local Forfeit = Why == `Forfeit`
		local Won = Winner ~= nil and Team == Winner and not Forfeit
		local Got = { Exp = 0; Yen = 0; Club = 0 }
		-- played a minute AND actually took part (had the ball twice or scored): standing on a pad isn't playing
		local St = m.Stats[P] or {}
		local Active = (St.Touches or 0) >= 2 or (St.Points or 0) > 0
		local Fresh = os.clock() - (PaidAt[P.UserId] or -math.huge) >= MATCH_REWARD_COOLDOWN
		if Counted and Active and Fresh and (m.Played[P] or 0) >= MIN_PLAY_SECONDS then
			PaidAt[P.UserId] = os.clock()
			if Progression then
				Got.Exp += (Progression.Award(P, `SportMatch`, nil, `{m.Sport} game`) or 0)
				if Won then Got.Exp += (Progression.Award(P, `SportWin`, nil, `{m.Sport} win`) or 0) end
				if P == Mvp then Got.Exp += (Progression.Award(P, `SportMvp`, nil, `{m.Sport} MVP`) or 0) end
			end
			local R = Config.Rewards[if Won then `Won` else `Played`]
			Got.Yen = R.Yen
			Data.UpdateState(P, { type = `UpdateYen`; amount = R.Yen })
			if Rep then pcall(Rep.Add, P, `Popularity`, R.Popularity, `{m.Sport} game`) end
			local Quests = try({ `Services`, `Quests`, `Quests` })
			if Quests then pcall(Quests.Progress, P, `SportMatch`, m.Sport) end
			if m.Ranked then
				local E = Config.ClubExp
				local Club = E.Played + (if Won then E.Won else 0) + (if P == Mvp then E.Mvp else 0)
				local S = Clubs.Get(P)
				if S and S.Club and Config.Clubs[S.Club].Sport == m.Sport then
					Got.Club = Club
					Clubs.AddExp(P, m.Sport, Club, `Ranked game`)
					if Winner and not Forfeit then Clubs.Record(P, m.Sport, Won) end
				end
			end
		end
		Lines[P.Name] = { Team = Team; Stats = m.Stats[P]; Got = Got; Idle = not Active; Cooldown = not Fresh }
	end
	return {
		Sport = m.Sport; Winner = Winner; Why = Why; Score = table.clone(m.Score); Ranked = m.Ranked;
		Mvp = Mvp and Mvp.Name or nil; Counted = Counted; Players = Lines; TeamNames = { A = Config.Teams.A.Name; B = Config.Teams.B.Name };
	}
end

---| display |---

local function clockText(t: number): string
	t = math.max(0, math.ceil(t))
	return string.format(`%d:%02d`, t // 60, t % 60)
end

function Match:Hud(For: Player?)
	local Names = { A = {}; B = {} }
	for _, T in { `A`, `B` } do for _, P in self.Teams[T] do table.insert(Names[T], P.DisplayName) end end
	local H = {
		Venue = self.Name; Sport = self.Sport; Phase = self.Phase; Clock = self.Clock; Half = self.Half; Overtime = self.Overtime;
		Score = self.Score; Names = Names; Ranked = self.Ranked;
		Queue = { A = #self.Queue.A; B = #self.Queue.B }; Min = self:Tune(`MinPerSide`, 1);
		Message = if os.clock() < self.MessageUntil then self.Message else nil;
		You = For and self.Team[For] or nil;
	}
	if self.Plug and self.Plug.Hud then
		local Ok, Extra = pcall(self.Plug.Hud, self, For)
		if Ok and Extra then for K, V in Extra do H[K] = V end end
	end
	return H
end

function Match:Draw()
	local Board = self.Board and self.Board:FindFirstChild(`Board`)
	if Board then
		Board.HomeScore.Text = tostring(self.Score.A)
		Board.AwayScore.Text = tostring(self.Score.B)
		Board.Clock.Text = if self.Phase == `Live` or self.Phase == `Halftime` or self.Phase == `Countdown` then clockText(self.Clock) else `--:--`
		local Status = if not self.Plug then `Coming soon: {self.Sport} rules are still being written`
			elseif self.Phase == `Waiting` then `Stand on a pad to play ({#self.Queue.A} v {#self.Queue.B})`
			elseif self.Phase == `Countdown` then `Starting in {math.ceil(self.Clock)}`
			elseif self.Phase == `Halftime` then `Halftime`
			elseif self.Phase == `Ended` then (if self.Winner then `{Config.Teams[self.Winner].Name} win` else `Tie game`)
			elseif self.Overtime then `Overtime: next score wins`
			else (if self.Ranked then `Ranked club game` else `Pickup game`) .. (if self.Half == 2 then ` · 2nd half` else ` · 1st half`)
		Board.Status.Text = Status
		local Extra = self.Plug and self.Plug.BoardSub and self.Plug.BoardSub(self) or ``
		Board.Sub.Text = Extra
	end
	for T, Pad in self.Pads do
		local Label = Pad:FindFirstChild(`BillboardGui`) and Pad.BillboardGui:FindFirstChild(`Label`)
		if Label then
			local Name = Config.Teams[T].Name
			Label.Text = if not self.Plug then `{Name} · coming soon`
				elseif self.Phase == `Live` then `{Name} · join ({#self.Teams[T]}/{self:Tune(`MaxPerSide`, 5)})`
				else `{Name} · stand to play ({#self.Queue[T]})`
		end
	end
end

---| misc |---

function Local.Armband(Player: Player, Team: string?)
	local Char = Player.Character
	if not Char then return end
	local Old = Char:FindFirstChild(`SportArmband`)
	if Old then Old:Destroy() end
	if not Team then return end
	local Arm = Char:FindFirstChild(`Left Arm`) :: BasePart?
	if not Arm then return end
	local Band = Instance.new(`Part`)
	Band.Name = `SportArmband`
	Band.Size = Vector3.new(Arm.Size.X + 0.08, 0.35, Arm.Size.Z + 0.08)
	Band.Color = Config.Teams[Team].Color
	Band.Material = Enum.Material.Fabric
	Band.CanCollide, Band.CanQuery, Band.CanTouch, Band.Massless = false, false, false, true
	Band.CFrame = Arm.CFrame * CFrame.new(0, Arm.Size.Y / 2 - 0.45, 0)
	local W = Instance.new(`WeldConstraint`) W.Part0 = Arm W.Part1 = Band W.Parent = Band
	Band.Parent = Char
end

function Shared.MatchOf(Player: Player) return PlayerMatch[Player] end
function Shared.Get(Name: string) return Matches[Name] end
function Shared.All() return Matches end

-- tests / bridge: force-start a venue with the given teams (bypasses the pads, not the rules)
function Shared.ForceStart(Name: string, A: { Player }, B: { Player }, SoloTest: boolean?)
	local m = Matches[Name]
	if not m then return false, `no venue` end
	if m.Phase ~= `Waiting` and m.Phase ~= `Countdown` then return false, `busy` end
	m.SoloTest = SoloTest and game:GetService(`RunService`):IsStudio() or nil   -- Studio only: one player can test a match
	m.Queue = { A = A; B = B }
	m:Start()
	return m.Phase == `Live`
end

function Shared.OnStart()
	local Folder = ReplicatedStorage:FindFirstChild(`NHSports`) or Instance.new(`Folder`)
	Folder.Name = `NHSports`
	Folder.Parent = ReplicatedStorage
	local function remote(Name: string)
		local R = Folder:FindFirstChild(Name) or Instance.new(`RemoteEvent`)
		R.Name = Name R.Parent = Folder
		return R
	end
	Remotes = { Action = remote(`Action`); Hud = remote(`Hud`); Summary = remote(`Summary`); Fx = remote(`Fx`) }
	Shared.Remotes = Remotes

	local Root = workspace:WaitForChild(`Sports`, 30)
	if not Root then warn(`[Sports] no Workspace.Sports`) return end
	for _, Venue in Root:GetChildren() do
		if Venue:IsA(`Model`) and Venue:GetAttribute(`SportVenue`) then
			Matches[Venue.Name] = Match.new(Venue)
		end
	end

	-- client intents: rate limited, routed to the player's match (or the sport's drill)
	local Budget = {} :: { [Player]: { n: number, t: number } }
	Remotes.Action.OnServerEvent:Connect(function(Player: Player, Action: any, Args: any)
		if typeof(Action) ~= `string` or #Action > 24 then return end
		local B = Budget[Player]
		local Now = os.clock()
		if not B or Now - B.t >= 1 then B = { n = 0; t = Now } Budget[Player] = B end
		B.n += 1
		if B.n > ACTION_RATE then return end
		if typeof(Args) ~= `table` then Args = {} end
		local m = PlayerMatch[Player]
		if m then
			if m.Phase == `Live` and m.Plug and m.Plug.OnAction then
				local Ok, Err = pcall(m.Plug.OnAction, m, Player, Action, Args)
				if not Ok then warn(`[Sports] OnAction {Action}: {Err}`) end
			end
			return
		end
		-- not in a match: drills
		for _, Mod in script.Parent:GetChildren() do
			if Mod:IsA(`ModuleScript`) and Mod ~= script and Mod.Name ~= `Clubs` and Mod.Name ~= `Ball` then
				local Ok, Plug = pcall(require, Mod)
				if Ok and type(Plug) == `table` and Plug.DrillAction and Plug.DrillAction(Player, Action, Args) then return end
			end
		end
	end)
	local function watch(Player: Player)
		Player.CharacterAdded:Connect(function()
			local m = PlayerMatch[Player]
			if m then m:Remove(Player, `You left the game.`) end
		end)
	end
	for _, Player in Players:GetPlayers() do watch(Player) end
	Players.PlayerAdded:Connect(watch)
	Players.PlayerRemoving:Connect(function(Player)
		Budget[Player] = nil
		local m = PlayerMatch[Player]
		if m then m:Remove(Player) end
	end)
	local Downed = try({ `Services`, `Features`, `Downed` })
	if Downed and Downed.OnDowned then
		Downed.OnDowned:Connect(function(Target)
			local P = typeof(Target) == `Instance` and Players:GetPlayerFromCharacter(Target)
			local m = P and PlayerMatch[P]
			if m then m:Remove(P, `You went down, so you're out of the game.`) end
		end)
	end

	-- step at 10 Hz, HUD at 4 Hz to players in or near the venue
	local Acc, HudAcc = 0, 0
	RunService.Heartbeat:Connect(function(dt)
		Acc += dt
		HudAcc += dt
		if Acc < 0.1 then return end
		local Step = Acc
		Acc = 0
		for _, m in Matches do
			local Ok, Err = pcall(m.Step, m, Step)
			if not Ok then warn(`[Sports] {m.Name}: {Err}`) end
		end
		if HudAcc < 0.25 then return end
		HudAcc = 0
		for _, m in Matches do
			pcall(m.Draw, m)
			if m.Phase == `Waiting` and #m.Queue.A + #m.Queue.B == 0 then continue end
			for _, P in Players:GetPlayers() do
				local Pos = rootPos(P)
				local Mine = m.Team[P] ~= nil
				local Free = not PlayerMatch[P] and not P:GetAttribute(`InDrill`)
				local Near = Mine or (Free and Pos and m.Bounds and Local.Inside(m.Bounds, Pos, 25))
				if Near then
					local Ok, H = pcall(m.Hud, m, P)
					if Ok then Remotes.Hud:FireClient(P, H) end
				end
			end
		end
	end)
end

return Shared
