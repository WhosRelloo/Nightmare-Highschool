--[[ (2.33) Earned trophies (server). Services.Player.Trophies (docs/expansion/14-Progression-and-Identity.md §5).
	Each is an item (Config.Items.Trophies, Kind Trophy) granted once into the Locker (Features.Inventory) when its rule
	holds on the same facts the Standing Paths use (Paths.CheckNow calls CheckFacts after every check):
	  ClubCup            a ranked club game won (Progress.Tally.MatchWins, counted by Sports.Matches)
	  HonourRollPlaque   a report card averaging A or better
	  RingBelt           the Ring's champion beaten
	  TheRegister        Chapter One finished (After Hours)
	  PathMedal<Path>    a Standing Path at its top tier (one each)
	Granting: an NHFx "Trophy" banner and a Notable Entry. Shown on the dorm room's trophy wall (Features.Homes) and in the
	Permanent Record's Trophy Case (Record.FileFor).
	API: CheckFacts(P, F) -> { Id }, Owned(P) -> { [Id] = true }, Granted (signal: Player, Id), SelfTestForTests(P) ]]
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local Items = require(ReplicatedStorage.Config.Items)
local PathsCfg = require(ReplicatedStorage.Config.Paths)
local SignalPlus = require(ReplicatedStorage.Packages.SignalPlus)

local Shared = {}
Shared.Granted = SignalPlus() -- (Player, Id)

local function svc(Path: string)
	local Node = ServerScriptService.Services
	for Seg in Path:gmatch(`[^%.]+`) do Node = Node and Node:FindFirstChild(Seg) end
	if not Node then return nil end
	local Ok, M = pcall(require, Node)
	return if Ok then M else nil
end

-- the rules: Id -> Test(F, Paths saved)
Shared.Rules = {
	ClubCup = function(F) return (F.Tally.MatchWins or 0) >= 1 end;
	HonourRollPlaque = function(F) return F.BestCard >= 5 end;
	RingBelt = function(F) return (F.Tally.Champion or 0) >= 1 end;
	TheRegister = function(F) return F.AfterHours == true end;
}
for _, Path in PathsCfg.Order do
	local Top = #PathsCfg.Paths[Path].Tiers
	Shared.Rules[`PathMedal{Path}`] = function(_, Saved) return (Saved[Path] or 1) >= Top end
end

function Shared.Owned(P: Player): { [string]: boolean }
	local Out = {}
	local Inv = svc(`Features.Inventory`)
	local I = Inv and Inv.Get(P)
	for Id, N in (I and I.Items) or {} do
		local It = Items.ById[Id]
		if It and It.Kind == `Trophy` and (tonumber(N) or 0) > 0 then Out[Id] = true end
	end
	return Out
end

function Shared.CheckFacts(P: Player, F): { string }
	local New = {}
	local Prog = svc(`Player.Progression`)
	local Pr = Prog and Prog.Get(P)
	local Inv = svc(`Features.Inventory`)
	if not (Pr and F and Inv) then return New end
	local Owned = Shared.Owned(P)
	local Seen = Pr.RecordSeen or {}
	for Id, Test in Shared.Rules do
		-- once: owned now, or granted before (its Notable Entry key is remembered even if the item were ever gone)
		if not Owned[Id] and not Seen[`Trophy:{Id}`] then
			local Ok, Yes = pcall(Test, F, Pr.Paths)
			if Ok and Yes and Inv.Grant(P, Id, 1) > 0 then table.insert(New, Id) end
		end
	end
	local Fx = svc(`Features.Fx`)
	local Rec = svc(`Player.Record`)
	for I, Id in New do
		local It = Items.ById[Id]
		if Fx and I <= 2 then pcall(Fx.Fire, P, `Trophy`, { Id = Id; Name = It.Name; Text = It.Text }) end
		if Rec then pcall(Rec.Add, P, `Trophy:{Id}`, `Awarded {It.Name}.`) end
		Shared.Granted:Fire(P, Id)
	end
	if #New > 0 then
		local Homes = svc(`Features.Homes`)
		if Homes and Homes.RefreshTrophies then pcall(Homes.RefreshTrophies, P) end
	end
	return New
end

---| tests |---

function Shared.SelfTestForTests(P: Player)
	local Paths = svc(`Player.Paths`)
	local Prog = svc(`Player.Progression`)
	local Inv = svc(`Features.Inventory`)
	local R = { Rules = 0 }
	for _ in Shared.Rules do R.Rules += 1 end -- 9
	local Zero, Max = Paths.ZeroFactsForTests(), Paths.MaxFactsForTests()
	Max.Tally.MatchWins = 1
	local Top = {}
	for _, Path in PathsCfg.Order do Top[Path] = #PathsCfg.Paths[Path].Tiers end
	R.ZeroNone, R.MaxAll = true, true
	for Id, Test in Shared.Rules do
		if Test(Zero, {}) then R.ZeroNone = false R.FailZero = Id end
		if not Test(Max, Top) then R.MaxAll = false R.FailMax = Id end
	end
	-- live: grant the Register on made-up facts, once; then take it back and forget the entry
	local Pr = Prog.Get(P)
	local RecBefore, SeenBefore = table.clone(Pr.Record), table.clone(Pr.RecordSeen)
	local HadIt = Shared.Owned(P).TheRegister == true
	local F = Paths.ZeroFactsForTests()
	F.AfterHours = true
	if not HadIt then
		local First = Shared.CheckFacts(P, F)
		local Second = Shared.CheckFacts(P, F)
		R.First, R.Second = #First, #Second -- 1, 0
		R.Owned = Shared.Owned(P).TheRegister == true
		pcall(Inv.Take, P, `TheRegister`, 1)
	else
		R.AlreadyOwned = true
	end
	local Pr2 = Prog.Get(P)
	Pr2.Record, Pr2.RecordSeen = RecBefore, SeenBefore
	svc(`Player.Data`).UpdateState(P, { type = `SetProgress`; progress = Pr2 })
	R.TakenBack = Shared.Owned(P).TheRegister ~= true or HadIt
	return R
end

return Shared
