--[[ (2.32) Honours (server). Services.Player.Honours (docs/expansion/14-Progression-and-Identity.md §4.3).
	Config.Honours' conditions are read from the same facts the Standing Paths use (Paths.Facts); Paths.CheckNow
	calls CheckFacts after every check. Earned = PlayerData.Progress.Honours[Id] = the school day; each is granted once:
	a Moments banner (NHFx "Honour") and a Notable Entry (Services.Player.Record).
	API: CheckFacts(P, F) -> { Id }, Earned(P) -> { [Id] = day }, Granted (signal: Player, Id), SelfTestForTests(P) ]]
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local Config = require(ReplicatedStorage.Config.Honours)
local SignalPlus = require(ReplicatedStorage.Packages.SignalPlus)

local Shared = {}
local Local = {}
Shared.Granted = SignalPlus() -- (Player, Id)

local function svc(Path: string)
	local Node = ServerScriptService.Services
	for Seg in Path:gmatch(`[^%.]+`) do Node = Node and Node:FindFirstChild(Seg) end
	if not Node then return nil end
	local Ok, M = pcall(require, Node)
	return if Ok then M else nil
end

function Shared.Earned(P: Player): { [string]: number }
	local Prog = svc(`Player.Progression`)
	local Pr = Prog and Prog.Get(P)
	return (Pr and Pr.Honours) or {}
end

-- grant every honour whose condition holds and isn't earned yet; returns the new ids
function Shared.CheckFacts(P: Player, F): { string }
	local New = {}
	local Prog = svc(`Player.Progression`)
	local Pr = Prog and Prog.Get(P)
	if not (Pr and F) then return New end
	for _, H in Config.List do
		if not Pr.Honours[H.Id] then
			local Ok, Yes = pcall(H.Test, F)
			if Ok and Yes then
				Pr.Honours[H.Id] = F.Today or 0
				table.insert(New, H.Id)
			end
		end
	end
	if #New == 0 then return New end
	svc(`Player.Data`).UpdateState(P, { type = `SetProgress`; progress = Pr })
	local Fx = svc(`Features.Fx`)
	local Rec = svc(`Player.Record`)
	for I, Id in New do
		local H = Config.ById[Id]
		if Fx and I <= 3 then pcall(Fx.Fire, P, `Honour`, { Id = Id; Name = H.Name; Text = H.Text; Group = H.Group; Secret = H.Hidden == true }) end
		if Rec then pcall(Rec.Add, P, `Honour:{Id}`, `Awarded the honour "{H.Name}".`) end
		Shared.Granted:Fire(P, Id)
	end
	return New
end

---| tests |---

function Shared.SelfTestForTests(P: Player)
	local Paths = svc(`Player.Paths`)
	local Prog = svc(`Player.Progression`)
	local R = {}
	-- every honour's condition passes on full facts and fails on empty ones
	local Zero, Max = Paths.ZeroFactsForTests(), Paths.MaxFactsForTests()
	Max.Passed, Max.APlus, Max.Streak, Max.DetentionsServed, Max.DaysClean, Max.InClub, Max.Trusted, Max.Tuned, Max.StrikeGrade = 4, true, 30, 1, 30, true, 1, true, `S`
	R.ZeroNone, R.MaxAll, R.Count = true, true, #Config.List
	for _, H in Config.List do
		local Ok0, Y0 = pcall(H.Test, Zero)
		local Ok1, Y1 = pcall(H.Test, Max)
		if not Ok0 or Y0 then R.ZeroNone = false R.FailZero = H.Id end
		if not (Ok1 and Y1) then R.MaxAll = false R.FailMax = H.Id end
	end
	-- live: grant on made-up facts, once; then put the slot back
	local Pr = Prog.Get(P)
	local Before, RecBefore, SeenBefore = table.clone(Pr.Honours), table.clone(Pr.Record), table.clone(Pr.RecordSeen)
	Pr.Honours = {} svc(`Player.Data`).UpdateState(P, { type = `SetProgress`; progress = Pr })
	local F = Paths.ZeroFactsForTests()
	F.Passed, F.Takedowns, F.Today = 1, 1, 77
	local First = Shared.CheckFacts(P, F)
	local Second = Shared.CheckFacts(P, F)
	R.First, R.Second = #First, #Second -- 2 (FirstPass, FirstTakedown), 0
	R.Day = Shared.Earned(P).FirstPass -- 77
	R.Entry = (Prog.Get(P).Record[1] or {}).Text
	local Pr2 = Prog.Get(P)
	Pr2.Honours, Pr2.Record, Pr2.RecordSeen = Before, RecBefore, SeenBefore
	svc(`Player.Data`).UpdateState(P, { type = `SetProgress`; progress = Pr2 })
	return R
end

return Shared
