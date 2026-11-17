--[[
	Turning (server): the bite (Races Phase 3).

	A Monster (Vampire, Werewolf, Ghoul, Wraith) at Tier II or higher who is gripping a downed Mortal player
	(Human or Priest) can press T to offer the turn. The grip stops (nobody is finished) and the victim chooses:
	  Accept  -> they become the biter's base race at Tier I (spins and traits kept, looks reset)
	  Refuse / 15 s pass -> nothing changes; they stay downed and the biter may grip them again.
	Limits: one successful turn per biter per in-game day; never in duels or protected fights; a Werewolf only
	bites at night. The biter's own hunger gains +5 on a successful turn.

	Remotes: ReplicatedStorage.NHTurn.Offer (biter -> server)
	         ReplicatedStorage.NHTurn.Ask (server -> victim: biter race)   .Answer (victim -> server: bool)
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local Lineage = require(ReplicatedStorage:WaitForChild(`Lineage`))
local SchoolTime = require(game:GetService("ReplicatedStorage"):WaitForChild("Functions"):WaitForChild("SchoolTime")) -- (2.22.0) shared night windows

local ANSWER_TIME = 15

local Local = {}
local Shared = {}
local Offers = {} :: { [Player]: { Biter: Player, Race: string, Expires: number } }  -- keyed by victim
local LastOffer = {} :: { [Player]: number }

local function try(Path: { string })
	local M = ServerScriptService
	for _, N in Path do M = M and M:FindFirstChild(N) end
	if not M then return nil end
	local Ok, Mod = pcall(require, M)
	return if Ok then Mod else nil
end

function Local.Notify(Player: Player, Data)
	local N = try({ `Services`, `Features`, `Notifications` })
	if N then pcall(N.Notify, Player, Data) end
end

function Local.Clock()
	local Clock = try({ `Services`, `School`, `SchoolClock` })
	local Ok, State = pcall(function() return Clock.GetState() end)
	if not (Ok and State) then return 0, false end
	return State.Day, SchoolTime.IsNight(State.Hour)
end

-- the downed player this character is gripping (nil if none / not a player)
function Local.GripTarget(Character: Model): Player?
	for _, P in Players:GetPlayers() do
		local C = P.Character
		if C and C ~= Character and C:GetAttribute(`GrippedBy`) == Character.Name then return P end
	end
	return nil
end

-- why this biter can't turn their grip target right now (nil = they can)
function Shared.Why(Biter: Player): (string?, Player?)
	local C = Biter.Character
	if not C then return `No character` end
	local Race, Tier = Biter:GetAttribute(`Race`), Biter:GetAttribute(`RaceTier`) or 1
	if not Lineage.IsMonster(Race) then return `Only monsters can turn` end
	if Tier < 2 then return `Your bloodline is too young (Tier II needed)` end
	local Victim = Local.GripTarget(C)
	if not Victim then return `Grip a downed student first` end
	if Lineage.IsMonster(Victim:GetAttribute(`Race`)) then return `They're already one of you` end
	if C:GetAttribute(`Dueling`) or (Victim.Character and (Victim.Character:GetAttribute(`Dueling`) or Victim.Character:GetAttribute(`Protected`))) then return `Not in a duel` end
	local Day, Night = Local.Clock()
	if Race == `Werewolf` and not Night then return `A werewolf's bite only takes at night` end
	local L = Lineage.Current and Lineage.Current(Biter)
	if L and L.TurnDay == Day then return `You've already turned someone today` end
	if Offers[Victim] then return `They're already deciding` end
	return nil, Victim
end

function Shared.Offer(Biter: Player)
	local Now = os.clock()
	if LastOffer[Biter] and Now - LastOffer[Biter] < 1 then return end
	LastOffer[Biter] = Now
	local Why, Victim = Shared.Why(Biter)
	if Why then
		Local.Notify(Biter, { Title = `Can't turn them`; Text = Why; Kind = `Warning`; Duration = 4 })
		return
	end
	local Downed = try({ `Services`, `Features`, `Downed` })
	if Downed then pcall(Downed.CancelGrip, Biter.Character) end -- the bite replaces the finish
	local Race = Biter:GetAttribute(`Race`)
	Offers[Victim] = { Biter = Biter; Race = Race; Expires = Now + ANSWER_TIME }
	ReplicatedStorage.NHTurn.Ask:FireClient(Victim, Race, ANSWER_TIME)
	Local.Notify(Biter, { Title = `The bite`; Text = `They're deciding...`; Kind = `Info`; Duration = 4 })
	task.delay(ANSWER_TIME + 0.5, function()
		local O = Offers[Victim]
		if O and O.Biter == Biter then
			Offers[Victim] = nil
			Local.Notify(Biter, { Title = `The bite didn't take`; Text = `They fought it off.`; Kind = `Info`; Duration = 4 })
		end
	end)
end

function Shared.Answer(Victim: Player, Accept: boolean)
	local O = Offers[Victim]
	if not O or os.clock() > O.Expires then return end
	Offers[Victim] = nil
	if Accept ~= true then
		Local.Notify(O.Biter, { Title = `The bite didn't take`; Text = `They fought it off.`; Kind = `Info`; Duration = 4 })
		Local.Notify(Victim, { Title = `You fought it off`; Text = `Your blood is still your own.`; Kind = `Info`; Duration = 4 })
		return
	end
	-- re-check the biter's limits at the moment of acceptance
	local Day = Local.Clock()
	local L = Lineage.Current and Lineage.Current(O.Biter)
	if not O.Biter.Parent or not L or L.TurnDay == Day or Lineage.IsMonster(Victim:GetAttribute(`Race`)) then return end
	local Ok = Lineage.Turn(Victim, O.Race)
	if not Ok then return end
	Lineage.SetTurnDay(O.Biter, Day)
	local Evolution = try({ `Services`, `Player`, `Evolution` })
	if Evolution then pcall(Evolution.Feed, O.Biter, 5, `Turn`) end
	-- VFX P1-13 "The Blood Takes": the victim's heartbeat and grade, a lite burst for everyone within 140 studs (client Gui.Evolution)
	local Fx = try({ `Services`, `Features`, `Fx` })
	local VRoot = Victim.Character and Victim.Character:FindFirstChild(`HumanoidRootPart`)
	if Fx then
		local FxData = { UserId = Victim.UserId; Race = O.Race }
		if VRoot then Fx.FireNear(VRoot.Position, 140, `Turned`, FxData) else Fx.Fire(Victim, `Turned`, FxData) end
	end
	Local.Notify(Victim, { Title = `Turned`; Text = `You are a {O.Race} now. Open the Bloodline tab to see what that means.`; Kind = `Good`; Duration = 8 })
	Local.Notify(O.Biter, { Title = `Turned`; Text = `Your bite took. Another {O.Race} walks the halls.`; Kind = `Good`; Duration = 6 })
end

function Shared.OnStart()
	local Folder = ReplicatedStorage:FindFirstChild(`NHTurn`) or Instance.new(`Folder`)
	Folder.Name = `NHTurn`
	for _, N in { `Offer`, `Ask`, `Answer` } do
		local R = Folder:FindFirstChild(N) or Instance.new(`RemoteEvent`)
		R.Name = N; R.Parent = Folder
	end
	Folder.Parent = ReplicatedStorage
	Folder.Offer.OnServerEvent:Connect(function(Player) pcall(Shared.Offer, Player) end)
	Folder.Answer.OnServerEvent:Connect(function(Player, Accept) pcall(Shared.Answer, Player, Accept == true) end)
	Players.PlayerRemoving:Connect(function(P) Offers[P] = nil; LastOffer[P] = nil end)
end

return Shared
