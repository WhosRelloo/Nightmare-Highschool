--[[
	Investigation (server). Cases in Config.Cases (public text) + ServerStorage.QuestSecrets (links,
	answer). Saved in PlayerData.Quests.Cases[CaseId] = { Clues = {Id = true}, Insights = {{Id, Text}},
	Solved, SolvedText }.

	Flow: find clues (quest objects with a Clue, or granted by quests) -> link two clues on the
	evidence board (server checks the pair) -> answer the case's deduction question.

	Quests wires this up with Init({ Get, Sync, IsOpen, Changed }) so there is no require cycle.

	(2.38) Link takes the question id (the Evidence Wall): a right pair under the wrong question is a miss.
]]

---| Services |---

local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerStorage = game:GetService(`ServerStorage`)

local Cases = require(ReplicatedStorage.Config.Cases)
local Secrets = require(ServerStorage.QuestSecrets)
local Fx = require(game:GetService(`ServerScriptService`).Services.Features.Fx) -- clue Moments (client Controllers.Gui.Moments)

local DEDUCE_COOLDOWN = 8
local LINK_COOLDOWN = 0.75

local Hooks = nil
local LastLink = {} :: { [Player]: number }
local LastDeduce = {} :: { [Player]: number }

local Shared = {}

function Shared.Init(H)
	Hooks = H
end

function Shared.Get(Player: Player, CaseId: string): any?
	if not Hooks or not Cases[CaseId] then return nil end
	local Q = Hooks.Get(Player)
	if not Q then return nil end
	local C = Q.Cases[CaseId]
	if typeof(C) ~= `table` then
		C = {}
		Q.Cases[CaseId] = C
	end
	C.Clues = if typeof(C.Clues) == `table` then C.Clues else {}
	C.Insights = if typeof(C.Insights) == `table` then C.Insights else {}
	C.Solved = C.Solved == true
	return C
end

function Shared.Count(Player: Player, CaseId: string, Kind: string): number
	local C = Shared.Get(Player, CaseId)
	if not C then return 0 end
	if Kind == `Clues` then
		local N = 0
		for _ in C.Clues do N += 1 end
		return N
	elseif Kind == `Link` then
		return #C.Insights
	elseif Kind == `Deduce` then
		return if C.Solved then 1 else 0
	end
	return 0
end

function Shared.HasClue(Player: Player, CaseId: string, ClueId: string): boolean
	local C = Shared.Get(Player, CaseId)
	return C ~= nil and C.Clues[ClueId] == true
end

-- Granted by a quest (no "case open" check).
-- Pos: where it was found (for the ink sparkles); nil when a quest grants it.
function Shared.Grant(Player: Player, CaseId: string, ClueId: string, Pos: Vector3?): boolean
	local C = Shared.Get(Player, CaseId)
	local Def = Cases[CaseId]
	if not C or not Def.Clues[ClueId] or C.Clues[ClueId] then return false end
	C.Clues[ClueId] = true
	Hooks.Sync(Player)
	Fx.Fire(Player, `Clue`, { Name = Def.Clues[ClueId].Name; Case = Def.Name; Pos = Pos }) -- VFX P1-5 (replaces the toast)
	Hooks.Changed(Player, CaseId, `Clues`)
	return true
end

-- (console 2) the staff console's Reset a case: clues, links (Insights), the deduction and its text for one case
function Shared.ResetCase(Player: Player, CaseId: string): boolean
	local C = Shared.Get(Player, CaseId)
	if not C then return false end
	C.Clues, C.Insights, C.Solved = {}, {}, false
	C.SolvedText = nil
	Hooks.Sync(Player)
	Hooks.Changed(Player, CaseId, `Clues`)
	return true
end

-- Found in the world. Only counts once the case is open (a quest has pointed you at it).
function Shared.Find(Player: Player, CaseId: string, ClueId: string, Pos: Vector3?): boolean
	if not Hooks.IsOpen(Player, CaseId) then return false end
	return Shared.Grant(Player, CaseId, ClueId, Pos)
end

function Shared.Link(Player: Player, CaseId: string, A: string, B: string, Question: string?): (boolean, string)
	local C = Shared.Get(Player, CaseId)
	local Secret = Secrets[CaseId]
	if not C or not Secret or typeof(A) ~= `string` or typeof(B) ~= `string` or A == B then return false, `Pick two different clues.` end
	if Question ~= nil and (typeof(Question) ~= `string` or #Question > 32) then return false, `` end
	if not C.Clues[A] or not C.Clues[B] then return false, `You haven't found both of those.` end

	local Now = os.clock()
	if LastLink[Player] and Now - LastLink[Player] < LINK_COOLDOWN then return false, `` end
	LastLink[Player] = Now

	for _, Link in Secret.Links do
		if (Question == nil or Link.Id == Question) and ((Link.A == A and Link.B == B) or (Link.A == B and Link.B == A)) then
			for _, Known in C.Insights do
				if Known.Id == Link.Id then return false, `You've already connected those.` end
			end
			table.insert(C.Insights, { Id = Link.Id; Text = Link.Text; A = A; B = B })
			Hooks.Sync(Player)
			Hooks.Notify(Player, { Title = `New insight`; Text = Link.Text; Kind = `Good`; Duration = 8; Open = `Evidence`; Case = CaseId })
			Hooks.Changed(Player, CaseId, `Link`)
			Fx.Fire(Player, `LinkHit`, { Case = CaseId; A = A; B = B }) -- VFX P2-13: the string draws itself on the board
			return true, Link.Text
		end
	end
	Hooks.Notify(Player, { Title = `No connection`; Text = `Those two don't seem to fit together.`; Kind = `Info`; Duration = 3 })
	Fx.Fire(Player, `LinkMiss`, { Case = CaseId; A = A; B = B }) -- VFX P2-13: the two cards shake
	return false, `Those two don't seem to fit together.`
end

function Shared.Deduce(Player: Player, CaseId: string, Option: number): (boolean, string)
	local C = Shared.Get(Player, CaseId)
	local Secret = Secrets[CaseId]
	if not C or not Secret or typeof(Option) ~= `number` then return false, `` end
	if C.Solved then return false, `Already solved.` end
	if #C.Insights < (Secret.Needs or 0) then
		return false, `You need to connect more of your clues first.`
	end

	local Now = os.clock()
	if LastDeduce[Player] and Now - LastDeduce[Player] < DEDUCE_COOLDOWN then
		return false, `Take a moment before you guess again.`
	end
	LastDeduce[Player] = Now

	if Option ~= Secret.Answer then
		Hooks.Notify(Player, { Title = `That doesn't fit`; Text = Secret.Wrong; Kind = `Warning`; Duration = 5; Open = `Evidence`; Case = CaseId })
		return false, Secret.Wrong
	end
	C.Solved = true
	C.SolvedText = Secret.Solved
	Hooks.Sync(Player)
	Hooks.Notify(Player, { Title = `Case breakthrough`; Text = Secret.Solved; Kind = `Good`; Duration = 8; Open = `Evidence`; Case = CaseId })
	Hooks.Changed(Player, CaseId, `Deduce`)
	Fx.Fire(Player, `Solved`, { Case = CaseId; Name = Cases[CaseId] and Cases[CaseId].Name }) -- VFX P2-13: the SOLVED stamp
	return true, Secret.Solved
end

function Shared.Forget(Player: Player)
	LastLink[Player] = nil
	LastDeduce[Player] = nil
end

return Shared
