--[[
	CineJudge (shared, 2.25.0). ReplicatedStorage.Functions.CineJudge. Pure functions, no state: the client uses them to
	branch a solo cut the instant you press, the server to score every viewer and pick a group's branch. Spec:
	docs/expansion/12-Interactive-Cutscenes.md.

	A prompt P (in a cut's Def.Graph segment): kind = "Press" | "Mash" | "Direction" | "Hold" | "Choice"; at (segment
	seconds when it opens); slow (world speed while open); on = { [Outcome] = Segment; Else = Segment? }; flag?
	  Press      beat (s after open), perfect = 0.12, good = 0.25        -> Perfect | Good | Miss
	  Mash       dur = 2, rate = 7 (taps/s), touchRate = 5               -> Win | Lose
	  Direction  dur = 0.9, options = {"Left","Right",...}, answer       -> Right | Wrong
	  Hold       zoneAt (s after open), zone = 0.15                      -> Hit | Miss
	  Choice     dur = 5, options = {{ id, text }}, default              -> the chosen id (or default)
	Input: { Times = {s after open}, Pick?, PickAt?, Release?, Touch?, Reduced? } (Reduce Motion widens Press, Direction,
	Hold by 1.3).
]]

local Judge = {}

Judge.POINTS = { Perfect = 3; Good = 2; Win = 2; Hit = 2; Right = 1 }
Judge.MAX = { Press = 3; Mash = 2; Direction = 1; Hold = 2; Choice = 1 }
Judge.RANK = { Perfect = 6; Good = 5; Win = 5; Hit = 5; Right = 4; Miss = 1; Lose = 1; Wrong = 1 }
Judge.MISS = { Press = `Miss`; Mash = `Lose`; Direction = `Wrong`; Hold = `Miss` }
Judge.GRADE_RANK = { S = 5; A = 4; B = 3; C = 2; D = 1 }
Judge.WIDEN = 1.3
Judge.GRACE = 0.35

local function widen(Opts): number
	return if Opts and Opts.Reduced then Judge.WIDEN else 1
end

function Judge.Window(P, Opts): number
	local W = widen(Opts)
	if P.kind == `Press` then return (P.beat or 0.6) + (P.good or 0.25) * W + 0.1
	elseif P.kind == `Mash` then return P.dur or 2
	elseif P.kind == `Direction` then return (P.dur or 0.9) * W
	elseif P.kind == `Hold` then return (P.zoneAt or 1) + (P.zone or 0.15) * W + 0.3
	elseif P.kind == `Choice` then return P.dur or 5 end
	return 0
end

function Judge.Evaluate(P, Input): (string, number)
	Input = Input or {}
	local W = widen(Input)
	local Window = Judge.Window(P, Input)
	local Times = table.clone(Input.Times or {})
	table.sort(Times)
	local Kind = P.kind
	local Outcome
	if Kind == `Press` then
		local First = nil
		for _, T in Times do if T >= -0.05 and T <= Window then First = T break end end
		if not First then Outcome = `Miss` else
			local D = math.abs(First - (P.beat or 0.6))
			Outcome = if D <= (P.perfect or 0.12) * W + 1e-6 then `Perfect` elseif D <= (P.good or 0.25) * W + 1e-6 then `Good` else `Miss`
		end
	elseif Kind == `Mash` then
		local Dur = P.dur or 2
		local N = 0
		for _, T in Times do if T >= 0 and T <= Dur then N += 1 end end
		local Rate = if Input.Touch then (P.touchRate or 5) else (P.rate or 7)
		Outcome = if N >= Rate * Dur - 1e-6 then `Win` else `Lose`
	elseif Kind == `Direction` then
		local InTime = Input.Pick ~= nil and (Input.PickAt or 0) <= Window
		local Valid = InTime and table.find(P.options or {}, Input.Pick) ~= nil
		Outcome = if Valid and Input.Pick == P.answer then `Right` else `Wrong`
	elseif Kind == `Hold` then
		local Down, Up = Times[1], Input.Release
		if Down == nil or Up == nil or Up < Down then Outcome = `Miss`
		else Outcome = if math.abs(Up - (P.zoneAt or 1)) <= (P.zone or 0.15) * W + 1e-6 then `Hit` else `Miss` end
	elseif Kind == `Choice` then
		if Input.Pick ~= nil and (Input.PickAt or 0) <= Window then
			for _, O in P.options or {} do
				if O.id == Input.Pick then return Input.Pick, 1 end
			end
		end
		return P.default, 0
	else
		return `Miss`, 0
	end
	return Outcome, Judge.POINTS[Outcome] or 0
end

function Judge.Branch(P, Outcome: string): string?
	local On = P.on or {}
	return On[Outcome] or On.Else
end

function Judge.Outcomes(P): { string }
	local K = P.kind
	if K == `Press` then return { `Perfect`, `Good`, `Miss` }
	elseif K == `Mash` then return { `Win`, `Lose` }
	elseif K == `Direction` then return { `Right`, `Wrong` }
	elseif K == `Hold` then return { `Hit`, `Miss` }
	elseif K == `Choice` then
		local L = {}
		for _, O in P.options or {} do table.insert(L, O.id) end
		return L
	end
	return {}
end

-- a Choice tie goes to the earlier option; other ties to the better outcome
local function rank(P, Outcome: string): number
	if P.kind == `Choice` then
		for I, O in P.options or {} do if O.id == Outcome then return 100 - I end end
		return 0
	end
	return Judge.RANK[Outcome] or 0
end

function Judge.Team(P, Outcomes: { string }): string
	if #Outcomes == 0 then return if P.kind == `Choice` then P.default else Judge.MISS[P.kind] or `Miss` end
	local Count = {}
	for _, O in Outcomes do Count[O] = (Count[O] or 0) + 1 end
	local Best, BestN, BestRank = nil, -1, -1
	for O, N in Count do
		local R = rank(P, O)
		if N > BestN or (N == BestN and R > BestRank) then Best, BestN, BestRank = O, N, R end
	end
	return Best
end

function Judge.Grade(Points: number, Max: number): string?
	if Max <= 0 then return nil end
	local S = Points / Max
	return if S >= 0.9 then `S` elseif S >= 0.75 then `A` elseif S >= 0.55 then `B` elseif S >= 0.35 then `C` else `D`
end

---| the graph |---

function Judge.Successors(Graph, Name: string): { string }
	local Node = Graph.segments[Name]
	if not Node then return {} end
	if Node.prompt then
		local L, Seen = {}, {}
		for _, O in Judge.Outcomes(Node.prompt) do
			local T = Judge.Branch(Node.prompt, O)
			if T and not Seen[T] then Seen[T] = true table.insert(L, T) end
		end
		return L
	end
	return if Node.next then { Node.next } else {}
end

-- To is From, or reached from it through next links only (no prompt in between)
function Judge.Follows(Graph, From: string?, To: string): boolean
	local Seen = {}
	local N = From
	while N and not Seen[N] do
		if N == To then return true end
		Seen[N] = true
		local Node = Graph.segments[N]
		N = Node and not Node.prompt and Node.next or nil
	end
	return false
end

-- real seconds of a segment: at normal speed until its prompt opens, the tail at the prompt's slow speed
local function realLen(Node): number
	local P = Node.prompt
	if not P then return Node.len end
	return P.at + (Node.len - P.at) / (P.slow or 1)
end

function Judge.LongestPath(Graph): number
	local Memo = {}
	local function cost(N, Depth)
		if Depth > 64 then return 0 end
		if Memo[N] then return Memo[N] end
		local Node = Graph.segments[N]
		if not Node then return 0 end
		local Best = 0
		for _, S in Judge.Successors(Graph, N) do Best = math.max(Best, cost(S, Depth + 1)) end
		Memo[N] = realLen(Node) + Best
		return Memo[N]
	end
	return cost(Graph.start, 0)
end

function Judge.Validate(Graph): { string }
	local Errs = {}
	local Segs = Graph and Graph.segments
	if typeof(Segs) ~= `table` then return { `no segments` } end
	if not Segs[Graph.start or ``] then table.insert(Errs, `start "{tostring(Graph.start)}" is not a segment`) end
	for Name, Node in Segs do
		if typeof(Node.len) ~= `number` or Node.len <= 0 then table.insert(Errs, `{Name}: len must be > 0`) end
		local P = Node.prompt
		if P then
			if Node.next then table.insert(Errs, `{Name}: a segment with a prompt branches, so it has no next`) end
			if not Judge.MAX[P.kind] then
				table.insert(Errs, `{Name}: unknown prompt kind {tostring(P.kind)}`)
			else
				if typeof(P.at) ~= `number` or P.at < 0 or P.at >= (Node.len or 0) then table.insert(Errs, `{Name}: prompt.at must be inside the segment`) end
				local Tail = ((Node.len or 0) - (P.at or 0)) / (P.slow or 1)
				local Need = Judge.Window(P, { Reduced = true }) + 0.6
				if Tail < Need then table.insert(Errs, string.format(`%s: the prompt's tail lasts %.2f s real time; it needs %.2f (window + hold)`, Name, Tail, Need)) end
				if P.kind == `Choice` then
					local Has = false
					for _, O in P.options or {} do if O.id == P.default then Has = true end end
					if not Has then table.insert(Errs, `{Name}: Choice default must be one of its options`) end
				end
				if P.kind == `Direction` and not table.find(P.options or {}, P.answer) then table.insert(Errs, `{Name}: Direction answer must be one of its options`) end
				for _, O in Judge.Outcomes(P) do
					local T = Judge.Branch(P, O)
					if not T then table.insert(Errs, `{Name}: no branch for {O}`)
					elseif not Segs[T] then table.insert(Errs, `{Name}: branch {O} -> unknown segment {T}`) end
				end
			end
		elseif Node.next and not Segs[Node.next] then
			table.insert(Errs, `{Name}: next -> unknown segment {Node.next}`)
		end
	end
	local State = {}
	local function walk(N, Depth)
		if Depth > 64 then table.insert(Errs, `path deeper than 64 segments`) return end
		if State[N] == 1 then table.insert(Errs, `loop through {N}`) return end
		if State[N] == 2 then return end
		State[N] = 1
		for _, S in Judge.Successors(Graph, N) do if Segs[S] then walk(S, Depth + 1) end end
		State[N] = 2
	end
	if Segs[Graph.start or ``] then walk(Graph.start, 0) end
	return Errs
end

return Judge
