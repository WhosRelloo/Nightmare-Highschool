-- Talk.Outfit verdicts (NH Combat Test, Edit mode, run with execute_luau)
local SSS = game:GetService("ServerScriptService")
local RS = game:GetService("ReplicatedStorage")
local Brain = SSS.Services.AI.StudentBrain
local Tmp = Instance.new("Folder")
Tmp.Name = "NHOutfitTest"
Brain.Lines:Clone().Parent = Tmp
local TalkMod = Brain.Talk:Clone()
TalkMod.Parent = Tmp
Tmp.Parent = game:GetService("ServerStorage")
local Results, Bad = {}, 0
local Ok, Err = pcall(function()
	local Talk = require(TalkMod)
	local CC = require(RS.Config.Cliques:Clone())
	assert(CC.ParseWear and CC.WearsTop, "Config.Cliques has no ParseWear / WearsTop yet")
	Talk.Use(require(RS.Config.CliqueTalk:Clone()), CC)
	local function wearing(W)
		return { UserId = 7; DisplayName = "Testy"; GetAttribute = function() return nil end;
			Character = { GetAttribute = function(_, K) return if K == "NHWear" then W else nil end } }
	end
	local function case(Name, Clique, W, WantVerdict, WantPiece)
		local V, P = Talk.Outfit({ Clique = Clique }, wearing(W))
		local Good = V == WantVerdict and P == WantPiece
		if not Good then Bad += 1 end
		table.insert(Results, (if Good then "ok   " else "FAIL ") .. Name .. `: got {V}, {P}; want {WantVerdict}, {WantPiece}`)
	end
	case("Athletes full look", "Athletes", "varsity-jacket|striped-joggers|", "FullLook", nil)
	case("Athletes see an Ink top", "Athletes", "black-shirt|uniform-trousers|", "RivalLook", nil)
	case("Choir like the ruff", "Choir", "ivory-polo|khaki-trousers|collar-ruff", "Likes", "falling ruff")
	case("Athletes mock the grimoire", "Athletes", "navy-polo|uniform-trousers|grimoire-chained", "Mocks", "chained grimoire")
	case("Vigil: nothing to say", "Vigil", "navy-polo|uniform-trousers|", nil, nil)
	case("Vigil girl's full look", "Vigil", "vigil-vest-f|pleated-tartan-skirt|", "FullLook", nil)
	case("Athletes girl's full look", "Athletes", "cheer-uniform|cheer-skirt|", "FullLook", nil)
	case("no NHWear", "Vigil", nil, nil, nil)
	case("clique-less student, one piece", nil, "navy-polo|uniform-trousers|hat-top", "Likes", "crimson-banded top hat")
	local W = CC.ParseWear("a|b|x,y")
	local Parsed = W and W.Top == "a" and W.Bottoms == "b" and #W.Acc == 2
	if not Parsed then Bad += 1 end
	table.insert(Results, (if Parsed then "ok   " else "FAIL ") .. "ParseWear")
	for Id, Def in CC.Defs do
		local Rival = Def.Rival and CC.Defs[Def.Rival]
		for _, R in (Def.Taste and Def.Taste.Likes) or {} do
			for _, R2 in (Rival and Rival.Taste and Rival.Taste.Likes) or {} do
				if R.Id and R.Id == R2.Id then Bad += 1 table.insert(Results, `FAIL {Id} and its rival both like {R.Id}`) end
			end
		end
	end
	-- data checks
	local function fail(Msg) Bad += 1 table.insert(Results, "FAIL " .. Msg) end
	local Acc = require(RS.Config.Accessories:Clone()).ById -- a clone: the cached module can predate the Kit C batches
	local App = require(RS.UI.Appearance)
	local function has(List, Id) for _, E in List do if E.Id == Id then return true end end return false end
	local Checked = 0
	for Id, Def in CC.Defs do
		local Taste = Def.Taste
		if not Taste then fail(`{Id} has no Taste`) continue end
		local Liked = {}
		for _, R in Taste.Likes do
			if R.Id then Liked[R.Id] = true end
		end
		for _, Kind in { "Likes", "Mocks" } do
			for _, R in Taste[Kind] do
				Checked += 1
				if R.Id and not Acc[R.Id] then fail(`{Id} {Kind} unknown accessory {R.Id}`) end
			end
		end
		for _, R in Taste.Mocks do
			if R.Id and Liked[R.Id] then fail(`{Id} both likes and mocks {R.Id}`) end
		end
		for _, T in Def.Look.FemaleTops or {} do
			if not has(App.Uniforms, T) then fail(`{Id} FemaleTops {T} is not in Appearance.Uniforms`) end
		end
		for _, B in Def.Look.FemaleMatchBottoms or {} do
			if not has(App.BottomsList, B) then fail(`{Id} FemaleMatchBottoms {B} is not in Appearance.BottomsList`) end
		end
	end
	table.insert(Results, `ok   data checks ({Checked} taste rules)`)
end)
Tmp:Destroy()
if not Ok then return "ERROR: " .. tostring(Err) end
return (if Bad == 0 then "PASS\n" else `FAIL ({Bad})\n`) .. table.concat(Results, "\n")
