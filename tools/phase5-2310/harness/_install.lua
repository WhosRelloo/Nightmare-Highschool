local Report = {}
local Items = {}
table.insert(Items, { Path = {"ServerScriptService", "Services", "Player", "Paths"}; Source = [==[
--[[ (2.31) Standing Paths (server). Services.Player.Paths (docs/expansion/14-Progression-and-Identity.md §3).
	Tiers are computed from data the game already keeps (Config.Paths); only the highest tier reached is saved
	(PlayerData.Progress.Paths, kept by Progression.Sanitize), so a tier never drops. Five counters the old signals
	didn't keep live in Progress.Tally.
	Checks: on join, a 60 s sweep, and a few signals (Check, debounced 2 s per player).
	Player attributes: Path_<Path> = tier, PathTop = the path at tier 3+ with the highest tier (Config order breaks ties).
	API: Evaluate(F), Facts(P), Tier(P, Path), Next(P), Check(P), CheckNow(P), Count(P, Key, N?), Granted (signal),
	     SelfTestForTests(P), FactsOverride (tests) ]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local Config = require(ReplicatedStorage.Config.Paths)
local SignalPlus = require(ReplicatedStorage.Packages.SignalPlus)

local Shared = {}
local Local = {}
Shared.Granted = SignalPlus() -- (Player, Path, Tier, Name)
Shared.FactsOverride = {} :: { [Player]: any }
local Pending = {} :: { [Player]: boolean }
local GRADE = { [`A+`] = 6; A = 5; B = 4; C = 3; D = 2; F = 1 }

local function svc(Path: string)
	local Node = ServerScriptService.Services
	for Seg in Path:gmatch(`[^%.]+`) do Node = Node and Node:FindFirstChild(Seg) end
	if not Node then return nil end
	local Ok, M = pcall(require, Node)
	return if Ok then M else nil
end

---| the facts |---

function Shared.Facts(P: Player)
	if Shared.FactsOverride[P] then return Shared.FactsOverride[P] end
	local Data = svc(`Player.Data`)
	local Prof = Data and Data.GetProfile(P)
	local Prog = svc(`Player.Progression`)
	local Pr = Prog and Prog.Get(P)
	if not (Prof and Pr) then return nil end
	local F = { Subjects = {}; Rep = {}; CliqueTiers = {}; Tally = {} }
	for _, K in Config.Tally do F.Tally[K] = Pr.Tally[K] or 0 end
	for Subject, C in Prof.Classes or {} do
		if typeof(C) == `table` then F.Subjects[Subject] = tonumber(C.Level) or 1 end
	end
	F.BestStreak = (typeof(Prof.Attendance) == `table` and tonumber(Prof.Attendance.BestStreak)) or 0
	F.BestCard = 0
	pcall(function()
		local St = svc(`School.ReportCards`).State(P)
		for _, Card in (St and St.Cards) or {} do F.BestCard = math.max(F.BestCard, GRADE[Card.Average or ``] or 0) end
	end)
	local Rep = svc(`Social.Reputation`)
	for Cat in require(ReplicatedStorage.Config.Reputation).Categories do
		F.Rep[Cat] = (Rep and Rep.Value(P, Cat)) or 0
	end
	F.Met = 0
	pcall(function()
		local Roster = svc(`Social.Roster`)
		for Id, R in Rep.Get(P).Relationships do
			if typeof(R) == `table` and R.Met == true and Roster.IsRostered(Id) then F.Met += 1 end
		end
	end)
	pcall(function()
		local Cl = svc(`Social.Cliques`)
		for Id, V in Cl.Get(P) or {} do
			if typeof(V) == `number` then F.CliqueTiers[Id] = Cl.Tier(V) end
		end
	end)
	F.FactionRank = 1
	pcall(function()
		local Fa = svc(`Social.Factions`)
		for Id in require(ReplicatedStorage.Config.Factions).Factions do
			local E = Fa.Get(P, Id)
			if E then F.FactionRank = math.max(F.FactionRank, Fa.RankIndex(E.Rank)) end
		end
	end)
	F.Takedowns = (tonumber(Prof.Kills) or 0) + (tonumber(Prof.NPCKills) or 0)
	F.Showdowns = 0
	pcall(function() F.Showdowns = svc(`Social.CliqueShowdowns`).Summary(P).Beaten or 0 end)
	F.ClubRank = `Rookie`
	pcall(function()
		local S = svc(`Sports.Clubs`).Get(P)
		if S and S.Club then F.ClubRank = require(ReplicatedStorage.Config.Sports).RankFor(S.ClubExp) end
	end)
	local Q = svc(`Quests.Quests`)
	F.Orientation = Q ~= nil and Q.IsDone(P, `Orientation`)
	F.AfterHours = Q ~= nil and Q.IsDone(P, `AfterHours`)
	F.FileKept = F.AfterHours and Q.Decided(P, `FileKept`) ~= `Lose`
	F.LineageTier = 1
	pcall(function() F.LineageTier = require(ReplicatedStorage.Lineage).Sanitize(Prof.Lineage).Tier or 1 end)
	return F
end

---| the evaluator (pure) |---

function Local.Passes(Tier, F): (boolean, { string })
	local Missing = {}
	for _, N in Tier.Need do
		local Ok, R = pcall(N.Test, F)
		if not (Ok and R) then table.insert(Missing, N.Text) end
	end
	return #Missing == 0, Missing
end

-- the highest tier of each path whose conditions hold for these facts
function Shared.Evaluate(F): { [string]: number }
	local Out = {}
	for _, Path in Config.Order do
		local Best = 1
		for I, Tier in Config.Paths[Path].Tiers do
			if I > 1 and (Local.Passes(Tier, F)) then Best = I end
		end
		Out[Path] = Best
	end
	return Out
end

---| saving |---

function Local.Saved(P: Player): ({ [string]: number }?, any?)
	local Prog = svc(`Player.Progression`)
	local Pr = Prog and Prog.Get(P)
	if not Pr then return nil, nil end
	return Pr.Paths, Pr
end
function Local.Save(P: Player, Pr)
	svc(`Player.Data`).UpdateState(P, { type = `SetProgress`; progress = Pr })
end

function Shared.Tier(P: Player, Path: string): (number, string)
	local Saved = Local.Saved(P)
	local T = (Saved and Saved[Path]) or 1
	local Def = Config.Paths[Path]
	return T, Def and Def.Tiers[T] and Def.Tiers[T].Name or ``
end

-- the closest next tier: the one with the fewest missing conditions
function Shared.Next(P: Player)
	local F = Shared.Facts(P)
	if not F then return nil end
	local Best = nil
	for _, Path in Config.Order do
		local T = Shared.Tier(P, Path)
		local Tier = Config.Paths[Path].Tiers[T + 1]
		if Tier then
			local _, Missing = Local.Passes(Tier, F)
			if not Best or #Missing < #Best.Missing then Best = { Path = Path; Tier = T + 1; Name = Tier.Name; Missing = Missing } end
		end
	end
	return Best
end

function Local.Mirror(P: Player, Saved)
	local Top, TopTier = nil, 2
	for _, Path in Config.Order do
		local T = Saved[Path] or 1
		P:SetAttribute(`Path_{Path}`, if T > 1 then T else nil)
		if T > TopTier then Top, TopTier = Path, T end
	end
	P:SetAttribute(`PathTop`, Top)
end

-- grants every tier between the saved one and what the facts hold now; never lowers one
function Shared.CheckNow(P: Player): { { Path: string, Tier: number } }
	local Made = {}
	local F = Shared.Facts(P)
	local Saved, Pr = Local.Saved(P)
	if not (F and Saved and Pr) then return Made end
	local Now = Shared.Evaluate(F)
	for _, Path in Config.Order do
		local Old = Saved[Path] or 1
		for T = Old + 1, Now[Path] do
			Saved[Path] = T
			table.insert(Made, { Path = Path; Tier = T })
		end
	end
	if #Made > 0 then
		Pr.Paths = Saved
		Local.Save(P, Pr)
		for I, G in Made do
			local Tier = Config.Paths[G.Path].Tiers[G.Tier]
			local Last = I == #Made or Made[I + 1].Path ~= G.Path -- the newest tier of this path in this check
			Local.Reward(P, G.Path, G.Tier, Tier, Last)
			Shared.Granted:Fire(P, G.Path, G.Tier, Tier.Name)
		end
	end
	Local.Mirror(P, Saved)
	return Made
end

-- what a tier gives: its title, a Moments banner (the newest tier of each path only), and from tier 4 a mention on
-- the PA by day or the Midnight Broadcast by night (Services.World.Broadcast; the PA speaks at most once a segment)
function Local.Reward(P: Player, Path: string, T: number, Tier, Last: boolean)
	local Rep = svc(`Social.Reputation`)
	if Tier.Title and Rep then pcall(Rep.AwardTitle, P, Tier.Title) end
	if not Last then return end
	local Fx = svc(`Features.Fx`)
	if Fx then pcall(Fx.Fire, P, `PathTier`, { Path = Path; Tier = T; Name = Tier.Name; Of = #Config.Paths[Path].Tiers }) end
	if T >= 4 then
		local First = P.DisplayName
		pcall(function() local Id = svc(`Player.Identity`) First = Id.Get(P).First or First end)
		local Article = if Tier.Name:match(`^[AEIOU]`) then `an` else `a`
		local Text = Config.Mention:gsub("{Name}", First):gsub("{Article}", Article):gsub("{Tier}", Tier.Name)
		local Bc = svc(`World.Broadcast`)
		if Bc then
			local OnAir = false
			pcall(function() OnAir = Bc.Station(P).OnAir end)
			if OnAir or not Bc.PA(Text) then Bc.Post(`Notable`, Text, `Paths`) end
		end
	end
	Shared.LastReward = { Player = P; Path = Path; Tier = T }
end

function Shared.Check(P: Player)
	if Pending[P] then return end
	Pending[P] = true
	task.delay(2, function()
		Pending[P] = nil
		if P.Parent then pcall(Shared.CheckNow, P) end
	end)
end

---| counters (Progress.Tally) |---

function Shared.Count(P: Player, Key: string, N: number?)
	if not table.find(Config.Tally, Key) then return end
	local Prog = svc(`Player.Progression`)
	local Pr = Prog and Prog.Get(P)
	if not Pr then return end
	Pr.Tally[Key] = (Pr.Tally[Key] or 0) + (N or 1)
	Local.Save(P, Pr)
	Shared.Check(P)
end

---| start |---

function Shared.OnStart()
	local Data = svc(`Player.Data`)
	if Data and Data.ProfileLoaded then
		Data.ProfileLoaded:Connect(function(P) task.delay(5, function() if P.Parent then pcall(Shared.CheckNow, P) end end) end)
	end
	Players.PlayerRemoving:Connect(function(P) Pending[P] = nil Shared.FactsOverride[P] = nil end)
	-- the counters the old signals didn't keep (Progress.Tally); they count from 2.31 on
	local function on(Path: string, Signal: string, Key: string)
		local M = svc(Path)
		local S = M and M[Signal]
		if S and S.Connect then
			S:Connect(function(P) if typeof(P) == `Instance` and P:IsA(`Player`) then Shared.Count(P, Key) end end)
		else
			warn(`[Paths] missing {Path}.{Signal}`)
		end
	end
	on(`Quests.Duels`, `Won`, `DuelWins`)
	on(`Quests.Duels`, `ChampionDefeated`, `Champion`)
	on(`School.HallMonitor`, `Escaped`, `Escapes`)
	-- and the signals that can change a tier, so it shows without waiting for the sweep
	for _, S in { { `Social.Reputation`, `Changed` }, { `Social.Reputation`, `RelationshipChanged` }, { `Social.Factions`, `RankChanged` } } do
		local M = svc(S[1])
		if M and M[S[2]] then M[S[2]]:Connect(function(P) if typeof(P) == `Instance` and P:IsA(`Player`) then Shared.Check(P) end end) end
	end
	task.spawn(function()
		while true do
			task.wait(60)
			for _, P in Players:GetPlayers() do pcall(Shared.CheckNow, P) end
		end
	end)
end

---| tests |---

function Local.ZeroFacts()
	local F = { Subjects = {}; Rep = { Popularity = 0; Intimidation = 0; Trust = 0; Academics = 0 }; CliqueTiers = {}; Tally = {};
		BestStreak = 0; BestCard = 0; Met = 0; FactionRank = 1; Takedowns = 0; Showdowns = 0; ClubRank = `Rookie`;
		Orientation = false; AfterHours = false; FileKept = false; LineageTier = 1 }
	for _, K in Config.Tally do F.Tally[K] = 0 end
	return F
end
function Local.MaxFacts()
	local F = Local.ZeroFacts()
	for _, S in { `History`, `Mathematics`, `Chemistry`, `English` } do F.Subjects[S] = 5 end
	F.BestStreak, F.BestCard, F.Met, F.FactionRank, F.Takedowns, F.Showdowns = 30, 6, 24, 5, 200, 2
	F.Rep = { Popularity = 100; Intimidation = 100; Trust = 100; Academics = 100 }
	F.CliqueTiers = { Vigil = `Respected`; Court = `Friendly` }
	F.ClubRank, F.Orientation, F.AfterHours, F.FileKept, F.LineageTier = `Captain`, true, true, true, 3
	F.Tally = { DuelWins = 5; Champion = 1; Beasts = 12; Escapes = 1; Superlatives = 1 }
	return F
end

function Shared.SelfTestForTests(P: Player)
	local R = {}
	-- the evaluator on made-up facts
	local Z, M = Shared.Evaluate(Local.ZeroFacts()), Shared.Evaluate(Local.MaxFacts())
	R.ZeroAllOne, R.MaxAllTop = true, true
	for _, Path in Config.Order do
		if Z[Path] ~= 1 then R.ZeroAllOne = false end
		if M[Path] ~= #Config.Paths[Path].Tiers then R.MaxAllTop = false end
	end
	local Honor = Local.ZeroFacts()
	Honor.Subjects = { History = 4; Mathematics = 4; Chemistry = 4; English = 2 }
	Honor.BestStreak, Honor.BestCard = 10, 4
	R.HonorStudent = Shared.Evaluate(Honor).Academic -- 3
	local Uneasy = Local.ZeroFacts() Uneasy.Tally.Beasts = 1
	R.UneasyByBeast = Shared.Evaluate(Uneasy).Supernatural -- 2
	R.FactsLive = Shared.Facts(P) ~= nil
	-- grants on the live player: from 1 to Honor Student, once; then lower facts never drop it
	local Saved, Pr = Local.Saved(P)
	if not (Saved and Pr) then R.NoProfile = true return R end
	local Before = table.clone(Saved)
	local Rep = svc(`Social.Reputation`)
	local Social = Rep.Get(P)
	local TitlesBefore, TitleBefore = table.clone(Social.Titles), Social.Title
	Pr.Paths = {} Local.Save(P, Pr)
	local Grants = 0
	local Con = Shared.Granted:Connect(function(Pl) if Pl == P then Grants += 1 end end)
	Shared.FactsOverride[P] = Honor
	local First = Shared.CheckNow(P)
	local Second = Shared.CheckNow(P)
	Shared.FactsOverride[P] = Local.ZeroFacts()
	Shared.CheckNow(P)
	task.wait(0.1) -- (SignalPlus delivers on a later frame)
	R.AfterDrop = Shared.Tier(P, `Academic`) -- still 3
	R.FirstGrants, R.SecondGrants, R.GrantSignals = #First, #Second, Grants -- 2, 0, 2 (Academic 2 and 3)
	R.TitleGiven = table.find(Rep.Get(P).Titles, `Honor Student`) ~= nil
	R.Attr = P:GetAttribute(`Path_Academic`) -- 3
	Con:Disconnect()
	Shared.FactsOverride[P] = nil
	-- put everything back
	local _, Pr2 = Local.Saved(P)
	Pr2.Paths = Before Local.Save(P, Pr2)
	Social.Titles = TitlesBefore Social.Title = TitleBefore Rep.Sync(P)
	Local.Mirror(P, Before)
	return R
end

function Shared.RewardTestForTests(P: Player)
	local Saved, Pr = Local.Saved(P)
	local Before = table.clone(Saved)
	local Rep = svc(`Social.Reputation`)
	local Social = Rep.Get(P)
	local TitlesBefore, TitleBefore = table.clone(Social.Titles), Social.Title
	local Bc = svc(`World.Broadcast`)
	local Items0 = #Bc.Items()
	Bc.PATestReset()
	Pr.Paths = {} Local.Save(P, Pr)
	local F = Local.MaxFacts()
	F.Rep.Intimidation, F.Takedowns, F.Showdowns, F.Tally.Beasts = 0, 0, 0, 0 -- only Combat stays at 1
	Shared.FactsOverride[P] = F
	Shared.LastReward = nil
	local Made = Shared.CheckNow(P)
	local R = { Made = #Made; Last = Shared.LastReward and `{Shared.LastReward.Path}:{Shared.LastReward.Tier}` or `none`;
		Mentions = #Bc.Items() - Items0; Top = P:GetAttribute(`PathTop`); Academic = P:GetAttribute(`Path_Academic`) }
	Shared.FactsOverride[P] = nil
	local _, Pr2 = Local.Saved(P)
	Pr2.Paths = Before Local.Save(P, Pr2)
	Social.Titles = TitlesBefore Social.Title = TitleBefore Rep.Sync(P)
	Local.Mirror(P, Before)
	return R
end

return Shared
]==] })
table.insert(Items, { Path = {"StarterPlayer", "StarterPlayerScripts", "Controllers", "Gui", "Moments"}; Source = [==[
--[[
	Moments (client). Controllers.Gui.Moments  -- VFX Batch 2 "core feedback" (vault: Docs/VFX-Design-Bible.md)

	One queue, at most one Moment banner on screen at a time (style guide: "Moment" tier). Each beat replaces
	its old toast, so nothing shows twice.

		P0-8  School Bell & Period Card   ReplicatedStorage.SchoolClock "Period" changes (never on join)
		P1-4  Quest Beat banner           NHFx "QuestBeat" { Type = Start|Stage|Complete|Fail, Title, Text, Category, Story }
		P1-5  Clue Discovered             NHFx "Clue" { Name, Case, Pos? }  ink sparkles + a "+CLUE" slip into the Journal
		P1-6  Level-up "Bell Toll"        NHFx "LevelUp" { UserId, Level, Points }  (sent to players within 80 studs)
		P1-8  Purchase granted            NHFx "Purchase" { Title, Text }
		P1-9  "Roll call" respawn         client-only: any player's CharacterAdded after a death (never the menu spawn)

	Everything follows the settings through Controllers.Fx (shake, reduced flashing / motion, effects quality),
	and pauses while the player is in the main menu or mid tier-up (character attribute NH_Evolving).

	Dialogue: quests are accepted by choosing a reply, so a quest banner usually fires while the dialogue box
	(PlayerGui.Dialogue.Box, bottom of the screen) is open. Banners wait up to DIALOGUE_HOLD seconds for the
	conversation to end; if it is still open, or opens while a banner is up, the banner lifts to sit just
	above the box so it never covers the replies.
]]

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local SoundService = game:GetService(`SoundService`)
local TweenService = game:GetService(`TweenService`)
local Lighting = game:GetService(`Lighting`)
local TextService = game:GetService(`TextService`)
local RunService = game:GetService(`RunService`)
local GuiService = game:GetService(`GuiService`)

local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))
local Fx = require(script.Parent.Parent:WaitForChild(`Fx`))
local Classes = require(ReplicatedStorage.Config.Classes)
local SchoolTime = require(ReplicatedStorage.Functions.SchoolTime)

local Player = Players.LocalPlayer
local Theme = Kit.Theme
local C = Theme.Colors
local Fonts = Theme.Fonts

local GOLD = C.Gold
local IRON = C.Chalk
local FAIL = C.Danger
local INK_BLUE = Color3.fromRGB(92, 128, 210)
local VIOLET = Color3.fromRGB(120, 92, 190)

-- Roblox-licensed Pro Sound Effects (Creator Store), routed to the Effects volume.
local SOUNDS = {
	Bell = { Id = `rbxassetid://9113584435`, Volume = 0.32, Length = 2.4 },      -- Brass Hand Bell 7
	Stamp = { Id = `rbxassetid://9119907907`, Volume = 0.45, Length = 0.5 },     -- palm on wood (kit Stamp)
	Chime = { Id = `rbxassetid://9114058995`, Volume = 0.25, Length = 0.8 },     -- desk bell (kit Confirm)
	Tick = { Id = `rbxassetid://9120300134`, Volume = 0.3, Length = 0.4 },       -- typewriter key (kit Tick)
}

-- Which period changes ring the bell (the start and end of the school day's blocks).
local RING_KINDS = { Class = true; Passing = true; Break = true; Lunch = true; AfterSchool = true }
local CARD_KINDS = { Class = true; Passing = true; Break = true; Lunch = true; AfterSchool = true; BeforeSchool = true }

local Local = {}
local Shared = {}

---| sound |---

function Local.Sound(Name: string, VolumeScale: number?)
	local Def = SOUNDS[Name]
	if not Def then return end
	local S = Instance.new(`Sound`)
	S.Name = `NHMoment{Name}`
	S.SoundId = Def.Id
	S.Volume = Def.Volume * (VolumeScale or 1)
	local Master = SoundService:FindFirstChild(`NH_Master`)
	local Group = Master and Master:FindFirstChild(`NH_Effects`)
	if Group and Group:IsA(`SoundGroup`) then S.SoundGroup = Group end
	S.Parent = SoundService
	S:Play()
	task.delay(Def.Length, function()
		if not S.Parent then return end
		TweenService:Create(S, TweenInfo.new(0.35), { Volume = 0 }):Play()
		task.delay(0.4, function() S:Destroy() end)
	end)
end

---| screen |---

local Gui: ScreenGui? = nil
local function gui(): ScreenGui
	if Gui and Gui.Parent then return Gui end
	local G = Instance.new(`ScreenGui`)
	G.Name = `NHMoments`
	G.ResetOnSpawn = false
	G.DisplayOrder = 11 -- above toasts (10), below menus
	G.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	Kit.AutoScale(G)
	G.Parent = Player:WaitForChild(`PlayerGui`)
	Gui = G
	return G
end

local function uiScale(): number
	local U = gui():FindFirstChild(`NHAutoScale`)
	return if U and U:IsA(`UIScale`) and U.Scale > 0 then U.Scale else 1
end

---| queue: one Moment at a time |---

local Queue = {} :: { () -> () }
local Pumping = false
local MAX_QUEUE = 6
local DIALOGUE_HOLD = 6 -- seconds a banner waits for an open conversation to end

function Local.Blocked(): boolean
	if Player:GetAttribute(`InMainMenu`) == true then return true end
	local Char = Player.Character
	return Char ~= nil and Char:GetAttribute(`NH_Evolving`) == true
end

function Local.Enqueue(Fn: () -> ())
	if #Queue >= MAX_QUEUE then table.remove(Queue, 1) end
	table.insert(Queue, Fn)
	if Pumping then return end
	Pumping = true
	task.spawn(function()
		while #Queue > 0 do
			local Waited = 0
			while Local.Blocked() and Waited < 30 do
				Waited += task.wait(0.25)
			end
			local Held = 0
			while Player:GetAttribute(`InDialogue`) == true and Held < DIALOGUE_HOLD do
				Held += task.wait(0.25)
			end
			local Next = table.remove(Queue, 1)
			local Ok, Err = pcall(Next)
			if not Ok then warn(`[Moments] {Err}`) end
		end
		Pumping = false
	end)
end

---| the banner |---

local WIDTH = 580
local BANNER_POS = UDim2.new(0.5, 0, 0.745, 0)
local DIALOGUE_GAP = 10 -- px between a lifted banner and the top of the dialogue box

-- top edge in screen pixels (a ScreenGui that keeps the top inset measures from below it)
function Local.ScreenTop(G: GuiObject): number
	local Sg = G:FindFirstAncestorWhichIsA(`ScreenGui`)
	local Inset = if Sg and Sg.IgnoreGuiInset then 0 else GuiService:GetGuiInset().Y
	return G.AbsolutePosition.Y + Inset
end

-- the dialogue box while a conversation is on screen
function Local.DialogueBox(): GuiObject?
	if Player:GetAttribute(`InDialogue`) ~= true then return nil end
	local D = Player.PlayerGui:FindFirstChild(`Dialogue`)
	local Box = D and D:FindFirstChild(`Box`)
	if not (Box and Box:IsA(`GuiObject`) and Box.Visible) then return nil end
	if D:IsA(`ScreenGui`) and not D.Enabled then return nil end
	return Box
end

-- keep a banner clear of the dialogue box: lift it just above the box, and back down once the box is gone.
-- Run every frame while the banner is up, so it also follows a box that opens, grows or closes mid-banner.
function Local.Fit(Root: GuiObject)
	local Box = Local.DialogueBox()
	local Offset = Root.Position.Y.Offset
	local Want = 0
	if Box then
		local Bottom = Local.ScreenTop(Root) + Root.AbsoluteSize.Y -- AbsolutePosition is always the top-left corner
		local Over = Bottom - (Local.ScreenTop(Box) - DIALOGUE_GAP)
		Want = math.min(0, Offset - Over / uiScale())
	end
	if math.abs(Want - Offset) > 0.5 then
		Root.Position = UDim2.new(BANNER_POS.X.Scale, BANNER_POS.X.Offset, BANNER_POS.Y.Scale, Want)
	end
end

-- wrapped height of a text block in design px (falls back to an estimate)
function Local.Measure(Text: string, FontArg: any, Size: number, Width: number): number -- (audit) a param named Font hid the Font datatype
	local Ok, H = pcall(function()
		local Params = Instance.new(`GetTextBoundsParams`)
		Params.Text = Text
		Params.Size = Size
		Params.Width = Width
		Params.Font = if typeof(FontArg) == `EnumItem` then Font.fromEnum(FontArg) else FontArg
		return TextService:GetTextBoundsAsync(Params).Y
	end)
	if Ok and typeof(H) == `number` and H > 0 then return math.ceil(H) end
	return math.ceil(#Text / 52) * math.ceil(Size * 1.3)
end

--[[ Opts: Caption, Title, Text, Color, Icon (a Theme.Images key: IconBanner*, Bell, IconNib), Glyph (short text on the icon), Hold, Sound
	Yields until the banner has gone. ]]
function Local.Banner(Opts)
	local Color = Opts.Color or GOLD
	local HasText = Opts.Text ~= nil and Opts.Text ~= ``
	local X = 98
	local BodyTop = if Opts.Caption then 60 else 50
	local BodySize = Theme.Sizes.TextSmall + 2
	-- story text is never cut off: the banner grows to fit the wrapped body
	local BodyH = if HasText then Local.Measure(Opts.Text, Fonts.Body, BodySize, WIDTH - X - 22) else 0
	local Height = math.max(76, if HasText then BodyTop + BodyH + 16 else (if Opts.Caption then 70 else 62))
	local Long = BodyH > BodySize * 2

	local Root = Instance.new(`Frame`)
	Root.Name = `MomentBanner`
	Root.AnchorPoint = Vector2.new(0.5, 1)
	Root.Position = BANNER_POS -- low centre, above the health bar and clear of the toast stack
	Root.Size = UDim2.fromOffset(WIDTH, Height)
	Root.BackgroundTransparency = 1
	Kit.Decorate(Root, { ornamentScale = 0.5, bgTransparency = 0.06, frameColor = Color:Lerp(C.Iron, 0.35) })

	local IconKey = Opts.Icon or `IconNoteMilestone`
	local Seal = Kit.Image(IconKey, {
		Name = `Seal`; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(0, 52, 0.5, 0);
		Size = UDim2.fromOffset(60, 60); ImageColor3 = if Theme.Baked and Theme.Baked[IconKey] then Color3.new(1, 1, 1) else Color; ZIndex = 8; Parent = Root;
	})
	if Opts.Glyph then
		Kit.Text({
			Name = `Glyph`; Text = Opts.Glyph; Font = Fonts.Title; TextSize = if #Opts.Glyph > 2 then 17 else 24;
			TextColor3 = C.Ink; TextStrokeTransparency = 1; TextXAlignment = Enum.TextXAlignment.Center;
			Size = UDim2.fromScale(1, 1); ZIndex = 9; Parent = Seal;
		})
	end

	if Opts.Caption then
		Kit.Text({
			Name = `Caption`; Text = string.upper(Opts.Caption); Font = Fonts.Title; TextSize = Theme.Sizes.TextTiny;
			TextColor3 = Color:Lerp(C.Text, 0.25); TextXAlignment = Enum.TextXAlignment.Left;
			Position = UDim2.fromOffset(X, 12); Size = UDim2.new(1, -X - 22, 0, 16); ZIndex = 8; Parent = Root;
		})
	end
	local Title = Kit.Text({
		Name = `Title`; Text = Opts.Title or ``; Font = Fonts.Title; TextSize = 25;
		TextColor3 = Color:Lerp(C.Text, 0.55); TextXAlignment = Enum.TextXAlignment.Left;
		TextTruncate = Enum.TextTruncate.AtEnd;
		Position = UDim2.fromOffset(X, if Opts.Caption then 28 else 18); Size = UDim2.new(1, -X - 22, 0, 30);
		ZIndex = 8; Parent = Root;
	})
	Kit.Emboss(Title, Color:Lerp(C.Ink, 0.4), 1.4)
	if HasText then
		Kit.Text({
			Name = `Body`; Text = Opts.Text; Font = Fonts.Body; TextSize = BodySize;
			TextColor3 = C.Text; TextXAlignment = Enum.TextXAlignment.Left; TextYAlignment = Enum.TextYAlignment.Top;
			TextWrapped = true;
			Position = UDim2.fromOffset(X, BodyTop); Size = UDim2.new(1, -X - 22, 0, BodyH + 4);
			ZIndex = 8; Parent = Root;
		})
	end

	-- single gold sheen across the title
	local Sheen = Instance.new(`UIGradient`)
	Sheen.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0); NumberSequenceKeypoint.new(0.45, 0); NumberSequenceKeypoint.new(0.5, 0.6);
		NumberSequenceKeypoint.new(0.55, 0); NumberSequenceKeypoint.new(1, 0);
	})
	Sheen.Offset = Vector2.new(-1, 0)

	Root.Parent = gui()
	Local.Fit(Root)
	local FitConn = RunService.RenderStepped:Connect(function() Local.Fit(Root) end)
	Kit.FadeIn(Root, 0.25)
	if not Fx.Reduced() then
		local Slide = Instance.new(`UIScale`)
		Slide.Scale = 0.92
		Slide.Parent = Root
		TweenService:Create(Slide, TweenInfo.new(0.3, Enum.EasingStyle.Back), { Scale = 1 }):Play()
		task.delay(0.08, function()
			if Seal.Parent then Fx.Pop(Seal, 1.6, 0.18) end
		end)
		Sheen.Parent = Title
		TweenService:Create(Sheen, TweenInfo.new(0.9, Enum.EasingStyle.Sine), { Offset = Vector2.new(1, 0) }):Play()
	end
	if Opts.Sound then Local.Sound(Opts.Sound) end
	task.delay(0.1, function() Local.Sound(`Stamp`, 0.6) end)

	local Hold = Opts.Hold or (if Long then 4.5 else 2.6)
	task.wait(0.25 + Hold)
	local Out = Kit.FadeOut(Root, 0.4)
	if Out then Out.Completed:Wait() else task.wait(0.4) end
	FitConn:Disconnect()
	Root:Destroy()
end

---| P0-8 School Bell & Period Card |---

function Local.ClockRim()
	local Hud = Player.PlayerGui:FindFirstChild(`ClockHud`)
	local Panel = Hud and Hud:FindFirstChild(`Panel`)
	if not Panel then return end
	local Rim = Kit.Slice(`FrameThin`, GOLD, { Name = `BellRim`; SliceScale = 0.45; ZIndex = 9; ImageTransparency = 0; Parent = Panel })
	Rim.Size = UDim2.fromScale(1, 1)
	local Tw = TweenService:Create(Rim, TweenInfo.new(1.1, Enum.EasingStyle.Sine), { ImageTransparency = 1 })
	Tw.Completed:Connect(function() Rim:Destroy() end)
	Tw:Play()
end

function Local.PulseWaypoint()
	local W = Player.PlayerGui:FindFirstChild(`ClassWaypoint`)
	if not (W and W:IsA(`BillboardGui`) and W.Enabled) then return end
	local Base = W.Size
	task.spawn(function()
		for _ = 1, 2 do
			if not W.Parent then return end
			local Up = TweenService:Create(W, TweenInfo.new(0.18, Enum.EasingStyle.Quad), { Size = UDim2.new(Base.X.Scale, Base.X.Offset * 1.25, Base.Y.Scale, Base.Y.Offset * 1.25) })
			Up:Play()
			Up.Completed:Wait()
			local Down = TweenService:Create(W, TweenInfo.new(0.3, Enum.EasingStyle.Sine), { Size = Base })
			Down:Play()
			Down.Completed:Wait()
		end
	end)
end

function Local.Bell(Clock: Instance)
	local Epoch = Clock:GetAttribute(`Epoch`)
	if not Epoch then return end
	local State = SchoolTime.GetState(Epoch, workspace:GetServerTimeNow())
	local Seg = State.Segment
	if not CARD_KINDS[Seg.Kind] then return end
	local Ring = RING_KINDS[Seg.Kind] == true

	local Caption, Title, Text
	local Until = SchoolTime.FormatClock(Seg.End)
	if Seg.Kind == `Class` then
		local Class = Classes.Periods[Seg.Name]
		Caption = `The bell rings`
		Title = Seg.Name
		if Class then
			local Room = Classes.Rooms and Classes.Rooms[Class.Room] or Class.Room
			Text = `{Class.Subject} · {Room} · until {Until}`
		else
			Text = `Until {Until}`
		end
	elseif Seg.Kind == `BeforeSchool` then
		Caption, Title, Text = `The gates open`, `Before School`, `Homeroom at {SchoolTime.FormatClock(Seg.End)}`
	elseif Seg.Kind == `AfterSchool` then
		Caption, Title, Text = `The bell rings`, `Classes are over`, `After school until {Until}`
	else
		Caption, Title, Text = `The bell rings`, Seg.Name, `Until {Until}`
	end

	-- the bell itself rings at once, even if a banner is still showing
	if Ring then
		Local.Sound(`Bell`)
		Local.ClockRim()
		if Seg.Kind == `Class` then task.delay(0.7, Local.PulseWaypoint) end
	end
	Local.Enqueue(function()
		Local.Banner({ Caption = Caption; Title = Title; Text = Text; Icon = `Bell`; Color = GOLD; Hold = 2.5 })
	end)
end

function Local.StartBell()
	local Clock = ReplicatedStorage:WaitForChild(`SchoolClock`)
	local Last = Clock:GetAttribute(`Period`) -- the value at join is a baseline, never a ring
	Clock:GetAttributeChangedSignal(`Period`):Connect(function()
		local Now = Clock:GetAttribute(`Period`)
		if Now == Last then return end
		local First = Last == nil
		Last = Now
		if First or Local.Blocked() then return end
		Local.Bell(Clock)
	end)
end

---| P1-4 Quest beats |---

function Local.RaceColor(): Color3
	local Ok, Col = pcall(function()
		local Lineage = require(ReplicatedStorage.Lineage)
		local Race = Player:GetAttribute(`Race`)
		local R = Race and Lineage.Races and Lineage.Races[Race]
		return R and R.Color
	end)
	return if Ok and typeof(Col) == `Color3` then Col else C.Crimson
end

function Local.QuestBeat(D)
	if typeof(D) ~= `table` then return end
	local Color = if D.Category == `Main` then GOLD elseif D.Category == `Rite` then Local.RaceColor() else IRON
	if D.Type == `Start` then
		Local.Enqueue(function()
			Local.Banner({ Caption = if D.Category == `Main` then `New main quest` else `New quest`; Title = D.Title; Text = D.Text; Color = Color; Icon = `IconBannerQuestNew`; Sound = `Chime` })
		end)
	elseif D.Type == `Stage` then
		Local.Enqueue(function()
			Local.Banner({ Caption = `New objective`; Title = D.Title; Text = D.Text; Color = Color; Icon = `IconBannerQuestStep`; Hold = 2.2 })
		end)
	elseif D.Type == `Complete` then
		Local.Enqueue(function()
			Local.Banner({ Caption = `Quest complete`; Title = D.Title; Text = D.Text; Color = Color; Icon = `IconBannerQuestDone`; Sound = `Chime` })
			if typeof(D.Story) == `string` and D.Story ~= `` then
				Local.Banner({ Caption = `Epilogue`; Title = D.Title; Text = D.Story; Color = C.Chalk; Icon = `IconNib`; Hold = math.clamp(#D.Story * 0.055, 4, 9) })
			end
		end)
	elseif D.Type == `Fail` then
		Local.Enqueue(function()
			Local.Banner({ Caption = `Quest failed`; Title = D.Title; Text = D.Text; Color = FAIL; Icon = `IconBannerQuestFailed`; Hold = 3.2 })
		end)
	end
end

---| (2.31) Standing Path tier |---

function Local.PathTier(D)
	if typeof(D) ~= `table` or typeof(D.Name) ~= `string` then return end
	Local.Enqueue(function()
		Local.Banner({ Caption = `Standing: {D.Path or ``}`; Title = string.upper(D.Name); Text = `The {D.Path} path, tier {D.Tier} of {D.Of}.`;
			Color = GOLD; Icon = `IconBannerQuestDone`; Sound = `Chime`; Hold = 3.2 })
	end)
end

---| P1-5 Clue Discovered |---

function Local.ClueWorld(Pos: Vector3)
	Fx.Burst(Pos, {
		Texture = Fx.Tex.Shards; Flipbook = `Grid2x2`; Count = 16;
		Color = ColorSequence.new(GOLD, INK_BLUE); Size = 0.35;
		Speed = NumberRange.new(1, 3); Spread = 70; Accel = Vector3.new(0, 2.5, 0);
		Lifetime = NumberRange.new(0.7, 1.3); LightEmission = 0.8;
	})
	Fx.Light(Pos, GOLD, 1.6, 10, 1)
	-- flash the found object, then fade (never a hard pop)
	local Params = OverlapParams.new()
	local Best, BestD = nil, math.huge
	for _, P in workspace:GetPartBoundsInRadius(Pos, 2, Params) do
		if P:GetAttribute(`QuestObject`) then
			local Dd = (P.Position - Pos).Magnitude
			if Dd < BestD then Best, BestD = P, Dd end
		end
	end
	if Best then
		local H = Instance.new(`Highlight`)
		H.Name = `NHClueFlash`
		H.FillColor = GOLD
		H.OutlineColor = GOLD
		H.FillTransparency = 0.55
		H.OutlineTransparency = 0
		H.DepthMode = Enum.HighlightDepthMode.Occluded
		H.Adornee = Best
		H.Parent = Best
		local Tw = TweenService:Create(H, TweenInfo.new(1.3, Enum.EasingStyle.Sine), { FillTransparency = 1; OutlineTransparency = 1 })
		Tw.Completed:Connect(function() H:Destroy() end)
		Tw:Play()
	end
end

function Local.TextWidth(Text: string, Size: number): number
	local Ok, W = pcall(function()
		local F = Fonts.Title
		return TextService:GetTextSize(Text, Size, if typeof(F) == `EnumItem` then F else Enum.Font.Garamond, Vector2.new(2000, 100)).X
	end)
	return if Ok and typeof(W) == `number` then W else #Text * Size * 0.55
end

function Local.ClueSlip(D)
	local Root = gui()
	local Label = `+ CLUE  ·  {D.Name or `Clue`}`
	local Slip = Kit.Plate({ text = Label; color = GOLD; textSize = 19; frameColor = GOLD:Lerp(C.Iron, 0.4) })
	Slip.Name = `ClueSlip`
	Slip.AnchorPoint = Vector2.new(0.5, 0.5)
	Slip.Position = UDim2.new(0.5, 0, 0.6, 0)
	Slip.Size = UDim2.fromOffset(math.clamp(Local.TextWidth(Label, 19) + 60, 220, 560), 44)
	Slip.ZIndex = 20
	Slip.Parent = Root
	local Sub = Kit.Text({
		Name = `Case`; Text = `Added to your case file{if D.Case then ` (` .. D.Case .. `)` else ``}`; Font = Fonts.Body;
		TextSize = Theme.Sizes.TextSmall; TextColor3 = C.Text; TextXAlignment = Enum.TextXAlignment.Center;
		AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, 0, 1, 6); Size = UDim2.fromOffset(420, 20); ZIndex = 20; Parent = Slip;
	})
	Kit.FadeIn(Slip, 0.2)
	Fx.Pop(Slip, 1.4, 0.22)
	Local.Sound(`Tick`)
	task.delay(0.12, function() Local.Sound(`Stamp`, 0.5) end)
	task.wait(1.4)
	Sub:Destroy()

	-- fly to the Journal button (left edge), shrinking
	local Journal = Player.PlayerGui:FindFirstChild(`QuestJournal`)
	local Toggle = Journal and Journal:FindFirstChild(`Toggle`)
	local Scale = uiScale()
	local Target
	if Toggle and Toggle:IsA(`GuiObject`) and Toggle.Visible then
		-- both screens use the same inset, so absolute px / our design scale = our offset
		local Abs = Toggle.AbsolutePosition + Toggle.AbsoluteSize / 2
		Target = UDim2.fromOffset(Abs.X / Scale, Abs.Y / Scale)
	else
		Target = UDim2.new(0, 90, 0.5, 78)
	end
	local Time = if Fx.Reduced() then 0.25 else 0.55
	local Fly = TweenService:Create(Slip, TweenInfo.new(Time, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Position = Target })
	local U = Instance.new(`UIScale`)
	U.Parent = Slip
	TweenService:Create(U, TweenInfo.new(Time, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Scale = 0.35 }):Play()
	Fly:Play()
	Fly.Completed:Wait()
	if Toggle and Toggle:IsA(`GuiObject`) then Fx.Pop(Toggle, 1.2, 0.25) end
	local Out = Kit.FadeOut(Slip, 0.15)
	if Out then Out.Completed:Wait() end
	Slip:Destroy()
end

function Local.Clue(D)
	if typeof(D) ~= `table` then return end
	if typeof(D.Pos) == `Vector3` then Local.ClueWorld(D.Pos) end
	Local.Enqueue(function() Local.ClueSlip(D) end)
end

---| P1-6 Level-up "Bell Toll" |---

function Local.LevelUp(D)
	if typeof(D) ~= `table` then return end
	local Who = Players:GetPlayerByUserId(D.UserId or 0)
	local Char = Who and Who.Character
	local Root = Char and Char:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	local Mine = Who == Player
	if Root and (Mine or Fx.Near(Root.Position, 80)) then
		local Feet = Root.Position - Vector3.new(0, 2.8, 0)
		Fx.Burst(Feet, {
			Texture = Fx.Tex.Ember; Count = 40; Color = ColorSequence.new(Color3.fromRGB(255, 226, 150), GOLD);
			Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5), NumberSequenceKeypoint.new(1, 0) });
			Speed = NumberRange.new(6, 11); Spread = 14; Accel = Vector3.new(0, 3, 0); Drag = 1.2;
			Lifetime = NumberRange.new(0.8, 1.4); LightEmission = 1;
		})
		Fx.Ring(Feet + Vector3.new(0, 0.1, 0), GOLD, 9, nil, 0.6)
		Fx.Light(Root.Position, GOLD, 2, 12, 1.2)
	end
	if not Mine then return end
	Local.Sound(`Bell`, 0.8)
	Fx.Shake(0.6, 0.35)
	Local.Enqueue(function()
		Local.Banner({
			Caption = `Level up`; Title = `Level {D.Level or `?`}`; Color = GOLD; Icon = `IconBannerLevelUp`; Glyph = tostring(D.Level or ``);
			Text = if D.Points and D.Points > 0 then `+{D.Points} stat points. Open your record (M) to spend them.` else nil;
		})
	end)
end

---| P1-8 Purchase granted |---

function Local.Purchase(D)
	if typeof(D) ~= `table` then return end
	Local.Enqueue(function()
		Local.Banner({ Caption = `Purchase complete`; Title = D.Title or `Thank you!`; Text = D.Text; Color = GOLD; Icon = `IconBannerPurchase`; Sound = `Chime` })
	end)
end

---| P1-17 tier-up: the "Evolved" banner, after the cutscene |---

-- The server fires this as the cutscene starts; the queue holds it while NH_Evolving is set, so it lands after.
function Local.Evolved(D)
	if typeof(D) ~= `table` then return end
	task.wait(0.5) -- let the NH_Evolving flag arrive first
	local Roman = { `I`, `II`, `III` }
	local Ok, Col = pcall(function()
		return require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`RaceFX`)).Color(D.Race)
	end)
	Local.Enqueue(function()
		Local.Banner({
			Caption = `Evolved`; Title = D.Name or `Evolved`; Color = if Ok and typeof(Col) == `Color3` then Col else C.Crimson;
			Text = `Tier {Roman[D.Tier or 0] or tostring(D.Tier)} {D.Race or ``}`; Icon = `IconBannerEvolved`; Sound = `Chime`;
		})
	end)
end

---| P1-9 "Roll call" respawn |---

function Local.OwnRespawn()
	local Veil = Instance.new(`Frame`)
	Veil.Name = `RollCallVeil`
	Veil.BorderSizePixel = 0
	Veil.BackgroundColor3 = C.Ink
	Veil.BackgroundTransparency = 0
	Veil.Size = UDim2.new(1, 0, 1, 80)
	Veil.Position = UDim2.fromOffset(0, -60)
	Veil.ZIndex = 30
	Veil.Parent = gui()
	local Tw = TweenService:Create(Veil, TweenInfo.new(0.5, Enum.EasingStyle.Sine), { BackgroundTransparency = 1 })
	Tw.Completed:Connect(function() Veil:Destroy() end)
	Tw:Play()
	-- colour comes back over 0.8 s
	local CC = Instance.new(`ColorCorrectionEffect`)
	CC.Name = `NHRollCall`
	CC.Saturation = -0.85
	CC.Parent = Lighting
	local Back = TweenService:Create(CC, TweenInfo.new(0.8, Enum.EasingStyle.Sine), { Saturation = 0 })
	Back.Completed:Connect(function() CC:Destroy() end)
	task.delay(0.3, function() Back:Play() end)
end

function Local.OtherRespawn(Char: Model)
	local Root = Char:WaitForChild(`HumanoidRootPart`, 5) :: BasePart?
	if not Root then return end
	task.wait(0.1)
	if not Fx.Near(Root.Position, 80) then return end
	local Feet = Root.Position - Vector3.new(0, 2.8, 0)
	Fx.Burst(Feet + Vector3.new(0, 1, 0), {
		Texture = Fx.Tex.Smoke; Flipbook = `Grid4x4`; Count = 10; Color = VIOLET;
		Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1.2), NumberSequenceKeypoint.new(1, 2.4) });
		Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.45), NumberSequenceKeypoint.new(1, 1) });
		Speed = NumberRange.new(1, 2.5); Spread = 180; Lifetime = NumberRange.new(0.8, 1.2); LightEmission = 0.2; Drag = 2;
	})
	Fx.Ring(Feet + Vector3.new(0, 0.1, 0), C.Chalk, 6, nil, 0.5)
end

function Local.WatchRespawns(P: Player)
	local WasInSchool = false
	local function onCharacter(Char: Model)
		local InSchool = P:GetAttribute(`InMainMenu`) ~= true
		local Play = WasInSchool and InSchool
		WasInSchool = InSchool
		if not Play then return end
		if P == Player then
			Local.OwnRespawn()
		else
			task.spawn(Local.OtherRespawn, Char)
		end
	end
	if P.Character then WasInSchool = P:GetAttribute(`InMainMenu`) ~= true end
	P.CharacterAdded:Connect(onCharacter)
end

---| start |---

function Shared.OnStart()
	Fx.On(`QuestBeat`, Local.QuestBeat)
	Fx.On(`PathTier`, Local.PathTier) -- (2.31) Standing Paths
	Fx.On(`Clue`, Local.Clue)
	Fx.On(`LevelUp`, Local.LevelUp)
	Fx.On(`Purchase`, Local.Purchase)
	Fx.On(`Evolved`, Local.Evolved)
	task.spawn(Local.StartBell)
	for _, P in Players:GetPlayers() do Local.WatchRespawns(P) end
	Players.PlayerAdded:Connect(Local.WatchRespawns)
end

-- other client systems can queue a Moment banner (VFX P2-1 full moon, ...): Opts = { Title, Text?, Caption?, Color?, Icon?, Glyph?, Sound?, Hold? }
function Shared.Banner(Opts) Local.Enqueue(function() Local.Banner(Opts) end) end

-- testing hooks (Studio command bar / test scripts)
Shared.Test = {
	Banner = function(Opts) Local.Enqueue(function() Local.Banner(Opts) end) end;
	Bell = function() Local.Bell(ReplicatedStorage:WaitForChild(`SchoolClock`)) end;
	QuestBeat = Local.QuestBeat; Clue = Local.Clue; LevelUp = Local.LevelUp; Purchase = Local.Purchase;
	Respawn = Local.OwnRespawn;
}

return Shared
]==] })
table.insert(Items, { Path = {"ReplicatedStorage", "Config", "Broadcast"}; Source = [==[
--[[ (2.30) Broadcast wording (World.Broadcast). The PA speaks only of real state (doc 13 §5.2), at most once per school
	segment (emergencies aside). The station (Night FM "Midnight Broadcast") is on air 21:00 to 03:00. ]]
return {
	PA = {
		BeforeSchool = { "Good morning, students. Homeroom begins at eight. Do not be late; the register is kept." };
		Substitute = { "A substitute will cover {Subject} today. Mind your manners." };
		Lunch = { "The lunch period has begun. Mrs. Okada's stand is open by the west doors." };
		AfterSchool = { "Classes are dismissed. Clubs meet now. The building closes at ten." };
		Curfew = { "Curfew is now in force. All students to the dorms. The halls are patrolled." };
		Rumble = { "Students are to clear {Place} at once. Staff are on their way." };
	};
	Transmissions = {
		"...and the roll is read. Holt. Mira Holt. ...No answer. No answer. No answer.",
		"A voice on the static, very calm: 'Answer the bell, and you will be kept.'",
		"Somewhere under the music, a register being read. One name too many.",
		"Static, and a girl humming the school hymn a beat behind the choir.",
	};
	Kickers = { Announcement = `ANNOUNCEMENT`; IncidentReport = `CAMPUS REPORT`; CallerLine = `CALLER LINE`; Transmission = `TRANSMISSION`; Notable = `SHOUT-OUT` }; -- (2.31) Notable: a Standing Path tier 4+
	MaxItems = 40;
	StationFrom = 21; StationTo = 3; -- hours (wraps past midnight)
	CurfewHour = 22;
	Chime = `rbxassetid://9114058995`; -- the desk bell (the kit's Confirm and Moments' Chime)
	-- (2.30) Night FM's voices (the owner's clips, art/sfx/NightFM): the station's host, the hall monitors' bulletins, the
	-- PSA and the lore. World.Broadcast.Voice picks one when you tune in (the Station tab), then the next after VoiceGap
	-- seconds of music while you stay tuned. Id 0 = not uploaded: that clip is skipped. From/To are hours, a [From, To)
	-- window that may wrap past midnight.
	Voice = {
		FirstTune = { Id = 111499524031786; Len = 28; Who = `Night FM`; Title = `You're listening to Night FM` }; -- the first time you ever tune in after dark
		WelcomeBack = { Id = 134125591548166; Len = 16; Who = `Night FM`; Title = `And we're back` }; -- your first tune-in of a later night
		PSA = { Id = 97206902894473; Len = 23; Who = `Public service`; Title = `Stay inside, stay out of trouble`; From = 20; To = 23 };
		Hello = { Id = 77658749464340; Len = 10; Who = `Night FM`; Title = `A special hello`; From = 21; To = 3 };
		Quiet = { Id = 75710916882636; Len = 15; Who = `Night FM`; Title = `A suspiciously quiet day`; From = 15; To = 3; QuietOnly = true }; -- only with no campus report today
		Lore1 = { Id = 100641239050743; Len = 33; Who = `Night FM`; Title = `About Mira Holt`; From = 23; To = 3 };
		Lore2 = { Id = 107164773510555; Len = 20; Who = `Night FM`; Title = `The photograph from 1887`; From = 23; To = 3 };
		SignOff = { Id = 138187748818510; Len = 18; Who = `Night FM`; Title = `Signing off`; From = 2.5; To = 3 }; -- the last half hour
		HallMonitor1 = { Id = 91112498069449; Len = 19; Who = `Hall monitor`; Title = `The dress code remains in effect`; From = 6; To = 12 };
		Afternoon = { Id = 105987665107075; Len = 16; Who = `Night FM`; Title = `The afternoon is rolling along`; From = 12; To = 18 };
		HallMonitor2 = { Id = 115752323853903; Len = 19; Who = `Hall monitor`; Title = `After hours, the halls are patrolled`; From = 15; To = 21 };
	};
	VoiceGap = 45;
}
]==] })
table.insert(Items, { Path = {"StarterPlayer", "StarterPlayerScripts", "Controllers", "Gui", "PhoneRadio"}; Source = [==[
--[[ (2.30) PhoneRadio (client). Controllers.Gui.PhoneRadio: Night FM, remade as a music app in the school's dress
	(the owner's reference, 2026-11-18: a Spotify-like home, library and now-playing, with a floating tab bar).
	Tabs: Home (greeting, chips, the Midnight Broadcast banner, recent tracks), Library (saved + recent, add by ID),
	Station (Midnight Broadcast, 21:00-03:00: caller lines, campus reports, transmissions; World.Broadcast), and the
	Now Playing sheet (cover, title, creator, like, waveform scrubber, loop / prev / play / next / volume).
	Art: "The Midnight Wireless" (owner: "wayy higher quality ... UNIQUE designs ... PBR textures, easy to read"), baked by
	art/ui/hud/make_nightfm_ui.py and staged in art/group-upload-nightfm (group 15981569): lacquer, gilt bezels, amethyst
	enamel, 12 painted covers, 16 bold icons. Until an id in ART is set, that piece falls back to the kit look (never the Seal).
	Voices (the owner's clips, Config.Broadcast.Voice): tuning in to the Station tab plays the host, the hall monitors, the
	PSA or the lore (World.Broadcast.Voice picks), with the music ducked under it, and the next one after a gap while you stay.
	Driven by Controllers.Gui.Phone: Open(Ctx), Tick(). ]]
local Players = game:GetService(`Players`)
local MarketplaceService = game:GetService(`MarketplaceService`)
local UserInputService = game:GetService(`UserInputService`)

local Shared = {}
local Ctx = nil
local Ui = nil
local Tab = `Home`
local Chip = `All`
local Info = {} :: { [number]: { Title: string, Creator: string } }

local PURPLE = Color3.fromRGB(150, 95, 230)
local PURPLE_DEEP = Color3.fromRGB(46, 22, 78)
local COVERS = { `IconAppRadio`, `IconCandle`, `Crest`, `IconBannerFullMoon`, `IconBannerBlueMoon`, `IconBannerCrimsonMoon`, `IconNib`, `Bell`, `IconCardBack` } -- (owner: no Seal icon)
local GRADS = {
	{ Color3.fromRGB(120, 60, 200), Color3.fromRGB(150, 30, 60) }, { Color3.fromRGB(70, 40, 150), Color3.fromRGB(20, 10, 40) },
	{ Color3.fromRGB(170, 70, 140), Color3.fromRGB(60, 20, 90) }, { Color3.fromRGB(90, 30, 40), Color3.fromRGB(150, 95, 230) },
}

-- (2.30) Night FM's PBR art (art/group-upload-nightfm, group 15981569). 0 = not imported: the kit look stands in.
local ART = {
	FmBackdrop = 127584299102551; FmCard = 113509808470918; FmChip = 99474149194088; FmChipOn = 135428344116127; FmKnob = 121754044071543; FmKnobOn = 87400242169148; FmTabBar = 139401041948754; FmOnAir = 119760735963337; FmBanner = 120062098656401; FmCoverFrame = 102140831342487;
	FmCover01 = 115207179383792; FmCover02 = 129339770425808; FmCover03 = 78521782695502; FmCover04 = 85842377440992; FmCover05 = 120254835544079; FmCover06 = 125971269956977; FmCover07 = 100458599549919; FmCover08 = 84310157061916; FmCover09 = 120827498837397; FmCover10 = 96216876489409; FmCover11 = 116184429450292; FmCover12 = 81335875522563;
	FmIconPlay = 107934318677097; FmIconPause = 103299744726376; FmIconPrev = 71254529174801; FmIconNext = 76973076777397; FmIconLoop = 119391678462515; FmIconQueue = 136134569814000; FmIconHeart = 115051670439309; FmIconHeartFull = 118215613287012; FmIconSearch = 102419618933770; FmIconBell = 119998418603355; FmIconHome = 138834344537959; FmIconLibrary = 109630327095017; FmIconStation = 96986282526360; FmIconBack = 127715630347481; FmIconPlus = 104299352902905; FmIconVolume = 92169605654444;
}
local function art(Name: string): string?
	local Id = ART[Name]
	if type(Id) == `string` then return Id end -- (a local preview: rbxasset://)
	return if Id and Id > 0 then `rbxassetid://` .. Id else nil
end
local ICON_GOLD = Color3.fromRGB(240, 206, 130)
-- a 9-slice plate from the art (Rect in pixels of the source, Scale shrinks the corners to fit the phone)
local SLICES = { FmCard = { Rect.new(44, 44, 148, 148), 0.3 }; FmChip = { Rect.new(30, 30, 162, 34), 0.47 }; FmChipOn = { Rect.new(30, 30, 162, 34), 0.47 };
	FmTabBar = { Rect.new(60, 60, 452, 68), 0.45 }; FmOnAir = { Rect.new(34, 34, 222, 38), 0.36 } }
local function sliced(Img, Name: string): boolean
	local A = art(Name)
	if not A then return false end
	Img.Image = A
	Img.ScaleType = Enum.ScaleType.Slice
	Img.SliceCenter = SLICES[Name][1]
	Img.SliceScale = SLICES[Name][2]
	Img.BackgroundTransparency = 1
	return true
end

local function new(Class: string, Props, Parent: Instance?)
	local I = Instance.new(Class)
	for K, V in Props do I[K] = V end
	if Parent then I.Parent = Parent end
	return I
end
local function corner(I, R) new(`UICorner`, { CornerRadius = if R then UDim.new(0, R) else UDim.new(1, 0) }, I) end
local function T() return Ctx.Theme end
local function label(Parent, Text, Size, Props)
	local L = new(`TextLabel`, { BackgroundTransparency = 1; Text = Text; TextSize = Size; Font = T().Fonts.Body; TextColor3 = T().Colors.Text;
		TextXAlignment = Enum.TextXAlignment.Left; RichText = true; TextTruncate = Enum.TextTruncate.AtEnd }, Parent)
	for K, V in Props or {} do L[K] = V end
	return L
end
local function hash(N: number): number return (N * 2654435761) % 4294967296 end

-- (2.30) the station's voice: one clip at a time, the music ducked under it
local Voice = { Sound = nil :: Sound?; Now = nil :: any; Busy = false; NextAt = 0; Ducked = nil :: number? }
local function duck(On: boolean)
	local M = Ctx and Ctx.Music and Ctx.Music.Sound
	if On then
		if M and not Voice.Ducked then Voice.Ducked = M.Volume M.Volume = M.Volume * 0.3 end
	else
		if M and Voice.Ducked then M.Volume = Voice.Ducked end
		Voice.Ducked = nil
	end
end
function Shared.StopVoice()
	if Voice.Sound then Voice.Sound:Destroy() Voice.Sound = nil end
	Voice.Now = nil
	duck(false)
	Voice.NextAt = os.clock() + 20
end
-- tuning in: ask the station for the next voice (nothing while one plays, or before the gap is up)
function Shared.TuneIn(Force: boolean?)
	if Voice.Busy or (Voice.Sound and Voice.Now) then return end
	if not Force and os.clock() < Voice.NextAt then return end
	Voice.Busy = true
	task.spawn(function()
		local V = Ctx and Ctx.Call(`Voice`)
		Voice.Busy = false
		if not (V and V.Id) then Voice.NextAt = os.clock() + 60 return end
		local S = new(`Sound`, { Name = `NightFMVoice`; SoundId = if typeof(V.Id) == `string` then V.Id else `rbxassetid://{V.Id}`; Volume = 0.9 }, game:GetService(`SoundService`))
		Voice.Sound, Voice.Now = S, V
		duck(true)
		S.Ended:Connect(function()
			if Voice.Sound ~= S then return end
			S:Destroy()
			Voice.Sound, Voice.Now = nil, nil
			duck(false)
			Voice.NextAt = os.clock() + (V.Gap or 45)
			Shared.Refresh()
			task.delay((V.Gap or 45) + 0.5, function() -- still tuned in? the next voice
				if Ui and Ui.Root and Ui.Root.Parent and Tab == `Station` then Shared.TuneIn() end
			end)
		end)
		S:Play()
		pcall(Ctx.Kit.PlaySound, `Tick`, 0.4, 0.7) -- the dial clicking over
		Shared.Refresh()
	end)
end

local function titleOf(Id: number): (string, string)
	local I = Info[Id]
	if I then return I.Title, I.Creator end
	Info[Id] = { Title = `Track {Id}`; Creator = `Night FM` }
	task.spawn(function()
		local Ok, P = pcall(MarketplaceService.GetProductInfo, MarketplaceService, Id, Enum.InfoType.Asset)
		if Ok and P then
			Info[Id] = { Title = P.Name or `Track {Id}`; Creator = (P.Creator and P.Creator.Name) or `Unknown` }
			Shared.Refresh()
		end
	end)
	return Info[Id].Title, Info[Id].Creator
end

-- a cover: one of the kit's emblems on a gradient, picked by the track id (the same track, the same cover)
local function cover(Parent, Id: number, Size: number)
	local H = hash(Id)
	local Plate = art(string.format(`FmCover%02d`, H % 12 + 1))
	if Plate then
		local F = new(`ImageLabel`, { BackgroundTransparency = 1; Image = Plate; ScaleType = Enum.ScaleType.Crop; Size = UDim2.fromOffset(Size, Size) }, Parent)
		corner(F, math.floor(Size / 6))
		return F
	end
	local G = GRADS[H % #GRADS + 1]
	local F = new(`Frame`, { BackgroundColor3 = Color3.new(1, 1, 1); BorderSizePixel = 0; Size = UDim2.fromOffset(Size, Size) }, Parent)
	corner(F, math.floor(Size / 6))
	new(`UIGradient`, { Rotation = 35 + H % 90; Color = ColorSequence.new(G[1], G[2]) }, F)
	new(`ImageLabel`, { BackgroundTransparency = 1; Image = T().Images.Glow; ImageTransparency = 0.55; Size = UDim2.fromScale(1, 1) }, F)
	new(`ImageLabel`, { BackgroundTransparency = 1; Image = T().Images[COVERS[(H // 7) % #COVERS + 1]]; ScaleType = Enum.ScaleType.Fit;
		AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromScale(0.62, 0.62) }, F)
	return F
end

-- a round button on the kit's orb ring, with a glyph
local function roundBtn(Parent, Icon: string, Glyph: string, Size: number, Filled: boolean?, Fn)
	local Knob, Img = art(if Filled then `FmKnobOn` else `FmKnob`), art(`FmIcon` .. Icon)
	if Knob and Img then
		local B = new(`ImageButton`, { Image = Knob; BackgroundTransparency = 1; AutoButtonColor = true; Size = UDim2.fromOffset(Size, Size) }, Parent)
		new(`ImageLabel`, { Name = `Icon`; BackgroundTransparency = 1; Image = Img; ImageColor3 = if Filled then Color3.new(1, 1, 1) else ICON_GOLD;
			AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromScale(0.6, 0.6) }, B)
		B.Activated:Connect(function() pcall(Ctx.Kit.PlaySound, `Tick`, 0.5, 1.3) Fn() end)
		return B
	end
	local B = new(`TextButton`, { Text = Glyph; Font = T().Fonts.Title; TextSize = math.floor(Size * 0.42); TextColor3 = if Filled then Color3.new(1, 1, 1) else T().Colors.Gold;
		BackgroundColor3 = if Filled then PURPLE else T().Colors.Ink; BackgroundTransparency = if Filled then 0 else 0.25; AutoButtonColor = true; Size = UDim2.fromOffset(Size, Size) }, Parent)
	corner(B)
	new(`UIStroke`, { Color = if Filled then Color3.fromRGB(210, 180, 255) else T().Colors.GoldDeep; Thickness = 1; Transparency = 0.35 }, B)
	-- (a UIGradient here would tint the glyph as well, so filled buttons are a solid fill)
	B.Activated:Connect(function() pcall(Ctx.Kit.PlaySound, `Tick`, 0.5, 1.3) Fn() end)
	return B
end
-- swap a round button's icon (art) or glyph (stand-in), and optionally its colour
local function setIcon(B, Icon: string, Glyph: string, Color: Color3?)
	local I = B:FindFirstChild(`Icon`)
	if I then
		I.Image = art(`FmIcon` .. Icon) or I.Image
		if Color then I.ImageColor3 = Color end
	else
		B.Text = Glyph
		if Color then B.TextColor3 = Color end
	end
end

local function chip(Parent, Text: string, Active: boolean, Fn)
	local Img = Instance.new(`ImageButton`)
	if sliced(Img, if Active then `FmChipOn` else `FmChip`) then
		Img.AutomaticSize = Enum.AutomaticSize.X
		Img.Size = UDim2.fromOffset(0, 30)
		Img.Parent = Parent
		new(`UIPadding`, { PaddingLeft = UDim.new(0, 15); PaddingRight = UDim.new(0, 15) }, Img)
		new(`TextLabel`, { BackgroundTransparency = 1; Text = Text; Font = T().Fonts.Title; TextSize = 14; AutomaticSize = Enum.AutomaticSize.X; Size = UDim2.fromScale(0, 1);
			TextColor3 = if Active then Color3.new(1, 1, 1) else Color3.fromRGB(225, 210, 190) }, Img)
		Img.Activated:Connect(Fn)
		return Img
	end
	Img:Destroy()
	local B = new(`TextButton`, { Text = Text; Font = T().Fonts.Body; TextSize = 13; TextColor3 = if Active then Color3.new(1, 1, 1) else T().Colors.TextDim;
		BackgroundColor3 = if Active then PURPLE else T().Colors.Ink; BackgroundTransparency = if Active then 0 else 0.3; AutomaticSize = Enum.AutomaticSize.X; Size = UDim2.fromOffset(0, 28) }, Parent)
	corner(B)
	new(`UIPadding`, { PaddingLeft = UDim.new(0, 14); PaddingRight = UDim.new(0, 14) }, B)
	new(`UIStroke`, { Color = if Active then Color3.fromRGB(210, 180, 255) else T().Colors.IronDim; Transparency = 0.4 }, B)
	B.Activated:Connect(Fn)
	return B
end

-- a track row: cover, title, creator, a round play button (the reference's list)
local function row(Parent, Id: number, Order: number)
	local Carded = art(`FmCard`) ~= nil
	local R = new(`TextButton`, { Text = ``; BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, if Carded then 62 else 52); LayoutOrder = Order }, Parent)
	if Carded then sliced(new(`ImageLabel`, { Size = UDim2.fromScale(1, 1) }, R), `FmCard`) end
	local X0, Y0 = if Carded then 9 else 0, if Carded then 9 else 4
	local C = cover(R, Id, 44) C.Position = UDim2.fromOffset(X0, Y0)
	local Title, By = titleOf(Id)
	label(R, Title, 15, { Font = T().Fonts.Title; TextColor3 = Color3.fromRGB(245, 236, 222); Position = UDim2.fromOffset(X0 + 54, Y0 + 4); Size = UDim2.new(1, -(X0 + 112), 0, 18) })
	label(R, By, 13, { TextColor3 = Color3.fromRGB(196, 184, 206); Position = UDim2.fromOffset(X0 + 54, Y0 + 24); Size = UDim2.new(1, -(X0 + 112), 0, 16) })
	local Playing = Ctx.Music.Id == Id and Ctx.Music.Sound and Ctx.Music.Sound.IsPlaying
	local B = roundBtn(R, if Playing then `Pause` else `Play`, if Playing then `\u{23F8}` else `\u{25B6}`, 34, false, function()
		if Ctx.Music.Id == Id and Ctx.Music.Sound then
			if Ctx.Music.Sound.IsPlaying then Ctx.Music.Sound:Pause() else Ctx.Music.Sound:Resume() end
		else Ctx.Play(Id) end
		Shared.Render()
	end)
	B.Position = if Carded then UDim2.new(1, -46, 0, 13) else UDim2.new(1, -38, 0, 9)
	R.Activated:Connect(function() if Ctx.Music.Id ~= Id then Ctx.Play(Id) end Shared.NowPlaying() end)
	return R
end

local function body(Parent)
	local S = new(`ScrollingFrame`, { BackgroundTransparency = 1; BorderSizePixel = 0; Position = UDim2.fromOffset(0, 0); Size = UDim2.new(1, 0, 1, -74);
		CanvasSize = UDim2.new(); AutomaticCanvasSize = Enum.AutomaticSize.Y; ScrollBarThickness = 2; ScrollBarImageColor3 = T().Colors.IronDim }, Parent)
	new(`UIListLayout`, { SortOrder = Enum.SortOrder.LayoutOrder; Padding = UDim.new(0, 8) }, S)
	new(`UIPadding`, { PaddingLeft = UDim.new(0, 16); PaddingRight = UDim.new(0, 16); PaddingTop = UDim.new(0, 12); PaddingBottom = UDim.new(0, 12) }, S)
	return S
end

local function heading(Parent, Text, Order, Right, RightFn)
	local F = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 24); LayoutOrder = Order }, Parent)
	label(F, Text, 17, { Font = T().Fonts.Title; TextColor3 = T().Colors.Gold; Size = UDim2.new(1, -80, 1, 0) })
	if Right then
		local B = new(`TextButton`, { Text = Right .. ` \u{203A}`; Font = T().Fonts.Title; TextSize = 13; TextColor3 = Color3.fromRGB(205, 190, 215); BackgroundTransparency = 1;
			AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, 0, 0, 0); Size = UDim2.fromOffset(80, 24); TextXAlignment = Enum.TextXAlignment.Right }, F)
		B.Activated:Connect(RightFn)
	end
end

function Shared.Home(Parent)
	local S = body(Parent)
	-- greeting with avatar, search and bell (the reference's header)
	local Head = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 86); LayoutOrder = 1 }, S)
	local Av = new(`ImageLabel`, { BackgroundColor3 = T().Colors.Ink; Size = UDim2.fromOffset(40, 40) }, Head)
	corner(Av) new(`UIStroke`, { Color = T().Colors.Gold; Transparency = 0.3 }, Av)
	task.spawn(function()
		local Ok, Url = pcall(Players.GetUserThumbnailAsync, Players, Players.LocalPlayer.UserId, Enum.ThumbnailType.HeadShot, Enum.ThumbnailSize.Size100x100)
		if Ok then Av.Image = Url end
	end)
	local B1 = roundBtn(Head, `Search`, `\u{1F50D}`, 36, false, function() Tab = `Library` Shared.Render() end) B1.Position = UDim2.new(1, -82, 0, 2)
	local B2 = roundBtn(Head, `Bell`, `\u{1F514}`, 36, false, function() Tab = `Station` Shared.Render() end) B2.Position = UDim2.new(1, -38, 0, 2)
	local Hour = game:GetService(`Lighting`).ClockTime -- the school's clock (SchoolClock syncs Lighting), not the real one
	local Hi = if Hour < 12 then `Good morning` elseif Hour < 18 then `Good afternoon` else `Good evening`
	label(Head, `{Hi}, {Players.LocalPlayer.DisplayName}`, 22, { Font = T().Fonts.Title; Position = UDim2.fromOffset(0, 50); Size = UDim2.new(1, 0, 0, 30) })
	-- chips
	local Chips = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 30); LayoutOrder = 2 }, S)
	new(`UIListLayout`, { FillDirection = Enum.FillDirection.Horizontal; Padding = UDim.new(0, 6) }, Chips)
	for _, Name in { `All`, `Recent`, `Saved`, `Station` } do
		chip(Chips, Name, Chip == Name, function()
			if Name == `Station` then Tab = `Station` else Chip = Name end
			Shared.Render()
		end)
	end
	-- the banner: tonight on Night FM (the reference's "For you" card)
	heading(S, `Tonight`, 3)
	local St = Ctx.Station or { OnAir = false }
	local Banner = new(`Frame`, { BackgroundColor3 = Color3.new(1, 1, 1); BorderSizePixel = 0; Size = UDim2.new(1, 0, 0, 132); LayoutOrder = 4 }, S)
	corner(Banner, 16)
	new(`UIGradient`, { Rotation = 20; Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromRGB(110, 50, 190)), ColorSequenceKeypoint.new(1, Color3.fromRGB(140, 30, 60)) }) }, Banner)
	new(`ImageLabel`, { BackgroundTransparency = 1; Image = T().Images.PanelBg; ImageTransparency = 0.85; ScaleType = Enum.ScaleType.Crop; Size = UDim2.fromScale(1, 1) }, Banner)
	local BArt = art(`FmBanner`)
	if BArt then -- the painted bell tower and wireless mast under the moon (the left is left clear for the words)
		new(`ImageLabel`, { BackgroundTransparency = 1; Image = BArt; ScaleType = Enum.ScaleType.Crop; Size = UDim2.fromScale(1, 1) }, Banner)
		new(`UIStroke`, { Color = ICON_GOLD; Transparency = 0.45; Thickness = 1.5 }, Banner)
	else
		new(`ImageLabel`, { BackgroundTransparency = 1; Image = T().Images.IconAppRadio; ScaleType = Enum.ScaleType.Fit; AnchorPoint = Vector2.new(1, 0.5); Position = UDim2.new(1, -10, 0.5, 0); Size = UDim2.fromOffset(104, 104) }, Banner)
	end
	label(Banner, `Midnight Broadcast`, 19, { Font = T().Fonts.Title; TextColor3 = Color3.new(1, 0.97, 0.92); Position = UDim2.fromOffset(14, 12); Size = UDim2.new(0.62, 0, 0, 24) })
	label(Banner, if St.OnAir then `On air now: callers, campus reports, and things on the static.` else `Off air until 9 PM. The school talks after dark.`, 13,
		{ TextWrapped = true; TextTruncate = Enum.TextTruncate.None; TextColor3 = Color3.fromRGB(240, 232, 248); TextYAlignment = Enum.TextYAlignment.Top; Position = UDim2.fromOffset(14, 40); Size = UDim2.new(0.5, 0, 0, 50) })
	local Go = new(`TextButton`, { Text = if St.OnAir then `Tune in` else `See tonight`; Font = T().Fonts.Title; TextSize = 13; TextColor3 = Color3.new(1, 1, 1);
		BackgroundColor3 = Color3.new(1, 1, 1); BackgroundTransparency = 0.82; Position = UDim2.fromOffset(14, 92); Size = UDim2.fromOffset(110, 28) }, Banner)
	corner(Go)
	local GoArt = new(`ImageLabel`, { Size = UDim2.fromScale(1, 1) }, Go)
	if sliced(GoArt, `FmChipOn`) then Go.BackgroundTransparency = 1 GoArt.ZIndex = 0 Go.TextTransparency = 1
		new(`TextLabel`, { BackgroundTransparency = 1; Text = Go.Text; Font = T().Fonts.Title; TextSize = 14; TextColor3 = Color3.new(1, 1, 1); ZIndex = 2; Size = UDim2.fromScale(1, 1) }, Go)
	else GoArt:Destroy() new(`UIStroke`, { Color = Color3.new(1, 1, 1); Transparency = 0.5 }, Go) end
	Go.Activated:Connect(function() Tab = `Station` Shared.Render() end)
	-- the list
	local Ids = if Chip == `Saved` then (Ctx.State.Liked or {}) else (Ctx.State.Recent or {})
	heading(S, if Chip == `Saved` then `Saved` else `Recently played`, 5, `Show all`, function() Tab = `Library` Shared.Render() end)
	if #Ids == 0 then label(S, `<i>Nothing here yet. Add a track by its audio ID in your library.</i>`, 13, { TextWrapped = true; TextTruncate = Enum.TextTruncate.None; TextColor3 = T().Colors.TextDim; Size = UDim2.new(1, 0, 0, 34); LayoutOrder = 6 }) end
	for K, Id in Ids do if K <= 6 then row(S, Id, 10 + K) end end
end

function Shared.Library(Parent)
	local S = body(Parent)
	label(S, `Your library`, 22, { Font = T().Fonts.Title; Size = UDim2.new(1, 0, 0, 30); LayoutOrder = 1 })
	local Chips = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 30); LayoutOrder = 2 }, S)
	new(`UIListLayout`, { FillDirection = Enum.FillDirection.Horizontal; Padding = UDim.new(0, 6) }, Chips)
	for _, Name in { `All`, `Saved`, `Recent` } do chip(Chips, Name, Chip == Name, function() Chip = Name Shared.Render() end) end
	local Input, Api = Ctx.Kit.SearchBar({ placeholder = `Add a track: audio ID, then Enter`; Size = UDim2.new(1, 0, 0, 38); LayoutOrder = 3; Parent = S;
		onSubmit = function(Text) local N = tonumber((Text or ``):match(`%d+`)) if N then Ctx.Play(N) Shared.NowPlaying() end end })
	local Seen, Ids = {}, {}
	local function add(List) for _, Id in List or {} do if not Seen[Id] then Seen[Id] = true table.insert(Ids, Id) end end end
	if Chip ~= `Recent` then add(Ctx.State.Liked) end
	if Chip ~= `Saved` then add(Ctx.State.Recent) end
	if #Ids == 0 then label(S, `<i>Nothing yet.</i>`, 15, { TextColor3 = Color3.fromRGB(205, 192, 218); Size = UDim2.new(1, 0, 0, 20); LayoutOrder = 4 }) end
	for K, Id in Ids do row(S, Id, 10 + K) end
end

function Shared.Station(Parent)
	local S = body(Parent)
	local St = Ctx.Station or { OnAir = false; Items = {}; LastRead = 0 }
	label(S, `Midnight Broadcast`, 22, { Font = T().Fonts.Title; Size = UDim2.new(1, 0, 0, 30); LayoutOrder = 1 })
	local Badge = new(`TextLabel`, { Text = if St.OnAir then `\u{25CF}  ON AIR` else `OFF AIR  \u{00B7}  9 PM to 3 AM`; Font = T().Fonts.Title; TextSize = 12;
		TextColor3 = Color3.new(1, 1, 1); BackgroundColor3 = if St.OnAir then T().Colors.Crimson else T().Colors.Iron; AutomaticSize = Enum.AutomaticSize.X;
		Size = UDim2.fromOffset(0, 24); LayoutOrder = 2 }, S)
	corner(Badge) new(`UIPadding`, { PaddingLeft = UDim.new(0, 12); PaddingRight = UDim.new(0, 12) }, Badge)
	if St.OnAir and art(`FmOnAir`) then -- the crimson enamel lamp
		local Lamp = new(`ImageLabel`, { ZIndex = 0; Size = UDim2.new(1, 24, 1, 4); Position = UDim2.fromOffset(-12, -2) }, Badge)
		sliced(Lamp, `FmOnAir`)
		Badge.BackgroundTransparency = 1
		Badge.TextTransparency = 1 -- (it still sizes the badge) the words ride above the lamp
		new(`TextLabel`, { BackgroundTransparency = 1; Text = Badge.Text; Font = Badge.Font; TextSize = 13; TextColor3 = Color3.new(1, 1, 1); ZIndex = 2; Size = UDim2.fromScale(1, 1) }, Badge)
	end
	if Voice.Now then -- who's on the air right now (the voice playing), with a stop
		local V = Voice.Now
		local Card = new(if art(`FmCard`) then `ImageLabel` else `Frame`, { BackgroundColor3 = PURPLE_DEEP; BackgroundTransparency = 0.15; Size = UDim2.new(1, 0, 0, 66); LayoutOrder = 3 }, S)
		corner(Card, 12)
		if art(`FmCard`) then sliced(Card, `FmCard`) Card.ImageColor3 = Color3.fromRGB(215, 185, 255) else new(`UIStroke`, { Color = PURPLE; Transparency = 0.3 }, Card) end
		local Pad = if art(`FmCard`) then 12 else 10
		label(Card, `<font color="#{Color3.fromRGB(255, 120, 130):ToHex()}">\u{25CF}</font>  ON THE AIR  \u{00B7}  {string.upper(V.Who or `Night FM`)}`, 11,
			{ Font = T().Fonts.Title; TextColor3 = Color3.fromRGB(215, 190, 255); Position = UDim2.fromOffset(Pad, 10); Size = UDim2.new(1, -(Pad + 56), 0, 14) })
		label(Card, V.Title or ``, 16, { Font = T().Fonts.Title; TextColor3 = Color3.fromRGB(248, 240, 228); Position = UDim2.fromOffset(Pad, 28); Size = UDim2.new(1, -(Pad + 56), 0, 22) })
		local Stop = roundBtn(Card, `Pause`, `\u{23F9}`, 38, false, function() Shared.StopVoice() Shared.Refresh() end)
		Stop.AnchorPoint = Vector2.new(1, 0.5) Stop.Position = UDim2.new(1, -(Pad - 2), 0.5, 0)
	elseif St.OnAir or Voice.NextAt > 0 then -- (nothing playing) a dial to tune in again
		local Go = new(`TextButton`, { Text = `\u{1F4FB}  Tune in`; Font = T().Fonts.Title; TextSize = 14; TextColor3 = Color3.new(1, 1, 1); BackgroundColor3 = PURPLE;
			AutoButtonColor = true; Size = UDim2.fromOffset(120, 32); LayoutOrder = 3 }, S)
		corner(Go)
		local GoArt = new(`ImageLabel`, { Size = UDim2.fromScale(1, 1) }, Go)
		if sliced(GoArt, `FmChipOn`) then Go.BackgroundTransparency = 1 GoArt.ZIndex = 0 Go.TextTransparency = 1
			new(`TextLabel`, { BackgroundTransparency = 1; Text = `Tune in`; Font = T().Fonts.Title; TextSize = 14; TextColor3 = Color3.new(1, 1, 1); ZIndex = 2; Size = UDim2.fromScale(1, 1) }, Go)
		else GoArt:Destroy() end
		Go.Activated:Connect(function() Shared.TuneIn(true) end)
	end
	local Kick = { Announcement = `ANNOUNCEMENT`; IncidentReport = `CAMPUS REPORT`; CallerLine = `CALLER LINE`; Transmission = `TRANSMISSION`; Notable = `SHOUT-OUT` }
	local Items = St.Items or {}
	if #Items == 0 then label(S, `<i>Quiet tonight. Nothing on the line yet.</i>`, 15, { TextColor3 = Color3.fromRGB(205, 192, 218); Size = UDim2.new(1, 0, 0, 20); LayoutOrder = 4 }) end
	local Newest = 0
	for K = #Items, 1, -1 do
		local It = Items[K]
		Newest = math.max(Newest, It.Id)
		local Card = new(if art(`FmCard`) then `ImageLabel` else `Frame`, { BackgroundColor3 = T().Colors.Ink; BackgroundTransparency = 0.3; AutomaticSize = Enum.AutomaticSize.Y; Size = UDim2.new(1, 0, 0, 0); LayoutOrder = 100 - K + 10 }, S)
		corner(Card, 12)
		if art(`FmCard`) then
			sliced(Card, `FmCard`) -- the card is the lacquer plate itself (a child plate would join the list layout)
			if It.Kind == `Transmission` then Card.ImageColor3 = Color3.fromRGB(255, 170, 170) end
		else
			new(`UIStroke`, { Color = if It.Kind == `Transmission` then T().Colors.Crimson else T().Colors.IronDim; Transparency = 0.4 }, Card)
		end
		new(`UIPadding`, { PaddingLeft = UDim.new(0, 12); PaddingRight = UDim.new(0, 12); PaddingTop = UDim.new(0, 8); PaddingBottom = UDim.new(0, 10) }, Card)
		new(`UIListLayout`, { SortOrder = Enum.SortOrder.LayoutOrder; Padding = UDim.new(0, 4) }, Card)
		label(Card, (if It.Id > (St.LastRead or 0) then `<font color="#{T().Colors.Gold:ToHex()}">\u{25CF} NEW</font>  ` else ``) .. (Kick[It.Kind] or It.Kind), 11,
			{ Font = T().Fonts.Title; TextColor3 = Color3.fromRGB(200, 170, 255); Size = UDim2.new(1, 0, 0, 14); LayoutOrder = 1 })
		label(Card, It.Text, 14, { TextWrapped = true; TextTruncate = Enum.TextTruncate.None; AutomaticSize = Enum.AutomaticSize.Y; Size = UDim2.new(1, 0, 0, 18); LayoutOrder = 2;
			Font = if It.Kind == `Transmission` then T().Fonts.Title else T().Fonts.Body })
	end
	if Newest > (St.LastRead or 0) then task.spawn(Ctx.Call, `StationRead`, Newest) end
end

-- the now playing sheet (the reference's third screen)
function Shared.NowPlaying()
	if not Ui then return end
	if Ui.Sheet then Ui.Sheet:Destroy() end
	local Id = Ctx.Music.Id
	if not Id then return end
	local Sheet = new(`Frame`, { Name = `NowPlaying`; BackgroundColor3 = Color3.new(1, 1, 1); Size = UDim2.fromScale(1, 1); ZIndex = 20 }, Ui.Root)
	new(`UIGradient`, { Rotation = 90; Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromRGB(80, 40, 140)), ColorSequenceKeypoint.new(0.6, Color3.fromRGB(40, 20, 70)), ColorSequenceKeypoint.new(1, Color3.fromRGB(20, 12, 30)) }) }, Sheet)
	Ui.Sheet = Sheet
	if art(`FmBackdrop`) then -- the lacquer wall under a violet wash
		new(`ImageLabel`, { BackgroundTransparency = 1; Image = art(`FmBackdrop`); ImageTransparency = 0.25; ScaleType = Enum.ScaleType.Crop; Size = UDim2.fromScale(1, 1) }, Sheet)
	end
	local Back = roundBtn(Sheet, `Back`, `\u{2039}`, 36, false, function() Sheet:Destroy() Ui.Sheet = nil end) Back.Position = UDim2.fromOffset(14, 10)
	label(Sheet, `Now Playing`, 15, { Font = T().Fonts.Title; TextColor3 = Color3.fromRGB(230, 214, 240); TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(60, 10); Size = UDim2.new(1, -120, 0, 36) })
	-- the neighbours peek in from the sides, as in the reference
	local Recent = Ctx.State.Recent or {}
	local At = table.find(Recent, Id) or 1
	local Prev, Next = Recent[At + 1], Recent[At - 1]
	if Prev then local P = cover(Sheet, Prev, 170) P.Position = UDim2.new(0, -130, 0, 82) if P:IsA(`ImageLabel`) then P.ImageTransparency = 0.45 else P.BackgroundTransparency = 0.4 end end
	if Next then local N = cover(Sheet, Next, 170) N.Position = UDim2.new(1, -40, 0, 82) if N:IsA(`ImageLabel`) then N.ImageTransparency = 0.45 else N.BackgroundTransparency = 0.4 end end
	local Big = cover(Sheet, Id, 220) Big.AnchorPoint = Vector2.new(0.5, 0) Big.Position = UDim2.new(0.5, 0, 0, 62)
	local Fr = art(`FmCoverFrame`)
	if Fr then
		new(`ImageLabel`, { BackgroundTransparency = 1; Image = Fr; Size = UDim2.new(1, 12, 1, 12); Position = UDim2.fromOffset(-6, -6); ZIndex = 2 }, Big)
	else
		new(`UIStroke`, { Color = Color3.fromRGB(210, 180, 255); Transparency = 0.5; Thickness = 1 }, Big)
	end
	local Title, By = titleOf(Id)
	label(Sheet, By, 14, { TextColor3 = Color3.fromRGB(214, 200, 228); Position = UDim2.fromOffset(22, 296); Size = UDim2.new(1, -90, 0, 18) })
	local TitleL = label(Sheet, Title, 22, { Font = T().Fonts.Title; Position = UDim2.fromOffset(22, 316); Size = UDim2.new(1, -90, 0, 28) })
	local Liked = table.find(Ctx.State.Liked or {}, Id) ~= nil
	local Heart Heart = roundBtn(Sheet, if Liked then `HeartFull` else `Heart`, if Liked then `\u{2665}` else `\u{2661}`, 40, false, function()
		local L = table.clone(Ctx.State.Liked or {})
		local K = table.find(L, Id)
		if K then table.remove(L, K) else table.insert(L, 1, Id) end
		Ctx.State.Liked = L
		setIcon(Heart, if K then `Heart` else `HeartFull`, if K then `\u{2661}` else `\u{2665}`, if K then (if Heart:FindFirstChild(`Icon`) then ICON_GOLD else T().Colors.Gold) else Color3.fromRGB(235, 70, 90))
		task.spawn(Ctx.Call, `SaveLiked`, L)
	end)
	Heart.Position = UDim2.new(1, -62, 0, 302)
	if Liked then setIcon(Heart, `HeartFull`, `\u{2665}`, Color3.fromRGB(235, 70, 90)) end
	-- the waveform: bars from the track id, the played part lit; click or drag to seek
	local Wave = new(`TextButton`, { Text = ``; BackgroundTransparency = 1; Position = UDim2.fromOffset(22, 360); Size = UDim2.new(1, -44, 0, 44) }, Sheet)
	local Bars = {}
	local N = 46
	for K = 1, N do
		local Hh = 0.25 + ((hash(Id + K * 31) % 1000) / 1000) * 0.75
		local B = new(`Frame`, { BorderSizePixel = 0; BackgroundColor3 = Color3.fromRGB(120, 105, 140); AnchorPoint = Vector2.new(0, 0.5);
			Position = UDim2.new((K - 1) / N, 1, 0.5, 0); Size = UDim2.new(1 / N, -2, Hh, 0) }, Wave)
		corner(B, 2)
		Bars[K] = B
	end
	local Cur = label(Sheet, `0:00`, 13, { TextColor3 = Color3.fromRGB(214, 200, 228); Position = UDim2.fromOffset(22, 406); Size = UDim2.fromOffset(60, 14) })
	local Len = label(Sheet, `0:00`, 13, { TextColor3 = Color3.fromRGB(214, 200, 228); TextXAlignment = Enum.TextXAlignment.Right; Position = UDim2.new(1, -82, 0, 406); Size = UDim2.fromOffset(60, 14) })
	local function seek(X: number)
		local S = Ctx.Music.Sound
		if not (S and S.TimeLength > 0) then return end
		local A = math.clamp((X - Wave.AbsolutePosition.X) / Wave.AbsoluteSize.X, 0, 1)
		S.TimePosition = A * S.TimeLength
	end
	Wave.InputBegan:Connect(function(Inp)
		if Inp.UserInputType == Enum.UserInputType.MouseButton1 or Inp.UserInputType == Enum.UserInputType.Touch then seek(Inp.Position.X) end
	end)
	-- controls
	local Row = new(`Frame`, { BackgroundTransparency = 1; Position = UDim2.fromOffset(18, 436); Size = UDim2.new(1, -36, 0, 70) }, Sheet)
	local function place(B, X) B.AnchorPoint = Vector2.new(0.5, 0.5) B.Position = UDim2.new(X, 0, 0.5, 0) end
	local Loop = roundBtn(Row, `Loop`, `\u{1F501}`, 38, false, function() if Ctx.Music.Sound then Ctx.Music.Sound.Looped = not Ctx.Music.Sound.Looped end end) place(Loop, 0.08)
	place(roundBtn(Row, `Prev`, `\u{23EE}`, 44, false, function() if Prev then Ctx.Play(Prev) Shared.NowPlaying() elseif Ctx.Music.Sound then Ctx.Music.Sound.TimePosition = 0 end end), 0.29)
	local Pl Pl = roundBtn(Row, `Pause`, `\u{23F8}`, 64, true, function()
		local S = Ctx.Music.Sound
		if not S then return end
		if S.IsPlaying then S:Pause() else S:Resume() end
	end) place(Pl, 0.5)
	place(roundBtn(Row, `Next`, `\u{23ED}`, 44, false, function() if Next then Ctx.Play(Next) Shared.NowPlaying() end end), 0.71)
	place(roundBtn(Row, `Queue`, `\u{266A}`, 38, false, function() Sheet:Destroy() Ui.Sheet = nil Tab = `Library` Shared.Render() end), 0.92)
	Ctx.Kit.Slider({ label = `Volume`; min = 0; max = 100; step = 5; value = if Ctx.Music.Sound then math.floor(Ctx.Music.Sound.Volume * 100) else 50;
		Size = UDim2.new(1, -44, 0, 34); Position = UDim2.fromOffset(22, 520); Parent = Sheet;
		onChanged = function(V) if Ctx.Music.Sound then Ctx.Music.Sound.Volume = V / 100 end end })
	Ui.NP = { Bars = Bars; Cur = Cur; Len = Len; Play = Pl; Loop = Loop; Title = TitleL; Id = Id }
end

-- the floating tab bar (the reference's pill): Home, Library, Station
function Shared.TabBar(Parent)
	local Bar = new(`Frame`, { BackgroundColor3 = T().Colors.Ink; BackgroundTransparency = 0.1; AnchorPoint = Vector2.new(0.5, 1); Position = UDim2.new(0.5, 0, 1, -12); Size = UDim2.fromOffset(186, 56); ZIndex = 10 }, Parent)
	corner(Bar)
	local BarArt = art(`FmTabBar`)
	if BarArt then
		Bar.BackgroundTransparency = 1
		local Plate = new(`ImageLabel`, { ZIndex = 9; Size = UDim2.fromScale(1, 1) }, Bar)
		sliced(Plate, `FmTabBar`)
		Plate.Parent = Bar.Parent
		Plate.AnchorPoint, Plate.Position, Plate.Size = Bar.AnchorPoint, Bar.Position, Bar.Size
	else
		new(`UIStroke`, { Color = T().Colors.GoldDeep; Transparency = 0.45 }, Bar)
	end
	new(`UIListLayout`, { FillDirection = Enum.FillDirection.Horizontal; HorizontalAlignment = Enum.HorizontalAlignment.Center; VerticalAlignment = Enum.VerticalAlignment.Center; Padding = UDim.new(0, 10) }, Bar)
	for _, Def in { { `Home`, `\u{2302}` }, { `Library`, `\u{266A}` }, { `Station`, `\u{1F4FB}` } } do
		local B = roundBtn(Bar, Def[1], Def[2], 46, Tab == Def[1], function() Tab = Def[1] Shared.Render() end)
		B.ZIndex = 11
	end
	if Ctx.Music.Id then -- a mini player above the bar
		local Mini = new(`TextButton`, { Text = ``; BackgroundColor3 = PURPLE_DEEP; AnchorPoint = Vector2.new(0.5, 1); Position = UDim2.new(0.5, 0, 1, -74); Size = UDim2.new(1, -24, 0, 46); ZIndex = 10 }, Parent)
		corner(Mini, 12)
		if art(`FmCard`) then
			local Plate = new(`ImageLabel`, { ZIndex = 10; Size = UDim2.fromScale(1, 1) }, Mini)
			sliced(Plate, `FmCard`)
			Plate.ImageColor3 = Color3.fromRGB(215, 185, 255)
			Mini.BackgroundTransparency = 1
		else
			new(`UIStroke`, { Color = PURPLE; Transparency = 0.5 }, Mini)
		end
		local C = cover(Mini, Ctx.Music.Id, 34) C.Position = UDim2.fromOffset(6, 6) C.ZIndex = 11
		local Title = titleOf(Ctx.Music.Id)
		label(Mini, Title, 14, { Font = T().Fonts.Title; ZIndex = 11; Position = UDim2.fromOffset(48, 0); Size = UDim2.new(1, -100, 1, 0) })
		Mini.Activated:Connect(Shared.NowPlaying)
	end
end

-- a redraw soon after names arrive (one for several), unless the now playing sheet is up (it updates itself)
local RefreshQueued = false
local StationAt = 0 -- (2.30) when the Station tab last fetched
function Shared.Refresh()
	if RefreshQueued then return end
	RefreshQueued = true
	task.delay(0.3, function()
		RefreshQueued = false
		if Ui and Ui.Root and Ui.Root.Parent and not (Ui.Sheet and Ui.Sheet.Parent) then Shared.Render() end
	end)
end

function Shared.Render()
	if not (Ui and Ui.Root and Ui.Root.Parent) then return end
	for _, Ch in Ui.Root:GetChildren() do if Ch ~= Ui.Bg and Ch.Name ~= `NowPlaying` then Ch:Destroy() end end
	local Page = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1) }, Ui.Root)
	if Tab == `Station` then
		if os.clock() - StationAt > 5 then -- (fetch, then redraw once: the redraw doesn't fetch again within 5 s)
			StationAt = os.clock()
			task.spawn(function() Ctx.Station = Ctx.Call(`Station`) or Ctx.Station if Tab == `Station` and Page.Parent then Page:Destroy() Shared.Render() end end)
		end
		Shared.TuneIn() -- (the voices; it waits out the gap and never talks over itself)
	end
	if Tab == `Home` then Shared.Home(Page) elseif Tab == `Library` then Shared.Library(Page) else Shared.Station(Page) end
	Shared.TabBar(Page)
end

function Shared.Open(C)
	Ctx = C
	local App = C.App
	for _, Ch in App:GetChildren() do if Ch.Name ~= `Grain` then Ch:Destroy() end end
	App.Visible = true
	local Root = new(`Frame`, { Name = `NightFM`; BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1); ClipsDescendants = true }, App)
	local Bg = new(`Frame`, { Name = `Bg`; BackgroundColor3 = Color3.new(1, 1, 1); Size = UDim2.fromScale(1, 1) }, Root)
	new(`UIGradient`, { Rotation = 90; Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromRGB(58, 28, 96)), ColorSequenceKeypoint.new(0.45, Color3.fromRGB(26, 16, 36)), ColorSequenceKeypoint.new(1, Color3.fromRGB(14, 10, 18)) }) }, Bg)
	new(`ImageLabel`, { BackgroundTransparency = 1; Image = art(`FmBackdrop`) or C.Theme.Images.PanelBg; ImageTransparency = if art(`FmBackdrop`) then 0 else 0.9; ScaleType = Enum.ScaleType.Crop; Size = UDim2.fromScale(1, 1) }, Bg)
	-- a back-to-home control in the corner (the phone's Home)
	Ui = { Root = Root; Bg = Bg }
	task.spawn(function() Ctx.Station = Ctx.Call(`Station`) if Ui and Tab == `Home` then Shared.Render() end end)
	Shared.Render()
	-- the phone's back: a thin gold chevron over the page, top-left of the status area
	local Back = new(`TextButton`, { Text = `\u{2039}`; Font = C.Theme.Fonts.Title; TextSize = 26; TextColor3 = C.Theme.Colors.Gold; BackgroundTransparency = 1; Position = UDim2.fromOffset(4, -2); Size = UDim2.fromOffset(26, 30); ZIndex = 30 }, Root)
	Back.Activated:Connect(function() C.Home() end)
end

-- tests: point the art at local files (Studio's content folder) to preview it before the ids are in
function Shared.UseArt(Map) for K, V in Map do ART[K] = V end end

function Shared.Tick()
	if not (Ui and Ui.Root and Ui.Root.Parent) then return end
	local NP = Ui.NP
	local S = Ctx.Music.Sound
	if NP and Ui.Sheet and Ui.Sheet.Parent and S then
		local A = if S.TimeLength > 0 then S.TimePosition / S.TimeLength else 0
		local Lit = math.floor(A * #NP.Bars + 0.5)
		for K, B in NP.Bars do B.BackgroundColor3 = if K <= Lit then Color3.fromRGB(205, 165, 255) else Color3.fromRGB(110, 96, 130) end
		local function mmss(X) X = math.floor(X) return string.format(`%d:%02d`, X // 60, X % 60) end
		NP.Cur.Text = mmss(S.TimePosition) NP.Len.Text = mmss(S.TimeLength)
		setIcon(NP.Play, if S.IsPlaying then `Pause` else `Play`, if S.IsPlaying then `\u{23F8}` else `\u{25B6}`)
		setIcon(NP.Loop, `Loop`, `\u{1F501}`, if S.Looped then Color3.fromRGB(205, 165, 255) else (if NP.Loop:FindFirstChild(`Icon`) then ICON_GOLD else Ctx.Theme.Colors.Gold))
		NP.Title.Text = (titleOf(NP.Id))
	end
end

return Shared
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