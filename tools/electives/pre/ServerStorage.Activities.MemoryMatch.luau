--[[
	History: "Match the Past" (server logic, memory game)
	Face-down cards; each pair is an event and its era. Flip two at a time to find pairs.
	The server holds the layout: a card's face is only revealed when that card is flipped.
	Grade: pairs found, minus a little for each mismatch beyond the number of pairs.
]]

local Pairs = {
	{ `Pyramids of Giza`, `Ancient Egypt` },
	{ `Knights and castles`, `Middle Ages` },
	{ `First Moon landing`, `1969` },
	{ `Gladiators in the Colosseum`, `Ancient Rome` },
	{ `First powered airplane flight`, `1903` },
	{ `Great Wall begins`, `Ancient China` },
	{ `Steam engines and factories`, `Industrial Revolution` },
	{ `Printing press in Europe`, `1400s` },
	{ `World Wide Web goes public`, `1990s` },
	{ `Olympic Games begin`, `Ancient Greece` },
}

local Memory = {}

function Memory.PairCount(Level: number): number
	return math.clamp(3 + Level, 4, 8)
end

function Memory.TimeLimit(Level: number): number
	return 40 + Memory.PairCount(Level) * 10
end

function Memory.Start(S, Level: number, StartAt: number)
	local Rng = Random.new()
	local Pool = table.clone(Pairs)
	local Count = Memory.PairCount(Level)

	local Cards = {}
	for PairId = 1, Count do
		local Pair = table.remove(Pool, Rng:NextInteger(1, #Pool))
		table.insert(Cards, { Text = Pair[1]; Pair = PairId; Kind = `Event`; Matched = false })
		table.insert(Cards, { Text = Pair[2]; Pair = PairId; Kind = `Era`; Matched = false })
	end
	for I = #Cards, 2, -1 do
		local J = Rng:NextInteger(1, I)
		Cards[I], Cards[J] = Cards[J], Cards[I]
	end

	S.Cards = Cards
	S.Pairs = Count
	S.Matched = 0
	S.Mistakes = 0
	S.First = nil
	S.StartAt = StartAt

	return { CardCount = #Cards; Columns = 4; Pairs = Count; TimeLimit = Memory.TimeLimit(Level) }
end

function Memory.Handle(S, Action: string, Data: any, Now: number)
	if Action ~= `Flip` or typeof(Data) ~= `table` then return nil, false end
	if Now < S.StartAt - 0.5 then return nil, false end

	local Index = Data.Index
	local Card = typeof(Index) == `number` and S.Cards[Index]
	if not Card or Card.Matched or Index == S.First then return nil, false end

	if not S.First then
		S.First = Index
		return { Index = Index; Text = Card.Text; Kind = Card.Kind; Stage = `First` }, false
	end

	local FirstIndex = S.First
	local First = S.Cards[FirstIndex]
	S.First = nil

	local Match = First.Pair == Card.Pair
	if Match then
		First.Matched = true
		Card.Matched = true
		S.Matched += 1
	else
		S.Mistakes += 1
	end

	return {
		Index = Index; Text = Card.Text; Kind = Card.Kind; Stage = `Second`;
		FirstIndex = FirstIndex; Match = Match; Matched = S.Matched; Mistakes = S.Mistakes;
	}, S.Matched >= S.Pairs
end

function Memory.Score(S): (number, number)
	local Found = S.Matched / S.Pairs
	local Penalty = math.max(0, S.Mistakes - S.Pairs) * 0.06
	return math.floor(Found * math.clamp(1 - Penalty, 0.3, 1) * 100 + 0.5), 100
end

return Memory
