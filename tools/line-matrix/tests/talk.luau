-- Talk.Attitude / Pool / Pick / Line (NH Combat Test, Edit mode, run with execute_luau)
local SSS = game:GetService("ServerScriptService")
local RS = game:GetService("ReplicatedStorage")
local Brain = SSS.Services.AI.StudentBrain
assert(Brain:FindFirstChild("Talk"), "StudentBrain.Talk is not installed")
local Tmp = Instance.new("Folder")
Tmp.Name = "NHTalkTest"
Brain.Lines:Clone().Parent = Tmp
local TalkMod = Brain.Talk:Clone()
TalkMod.Parent = Tmp
Tmp.Parent = game:GetService("ServerStorage")
local Results, Bad = {}, 0
local function check(Name, Got, Want)
	local Ok = Got == Want
	if not Ok then Bad += 1 end
	table.insert(Results, (if Ok then "ok   " else "FAIL ") .. Name .. ": got " .. tostring(Got) .. ", want " .. tostring(Want))
end
local Ok, Err = pcall(function()
	local Talk = require(TalkMod)
	local Data = require(RS.Config.CliqueTalk:Clone())
	Data.Test = {
		Greet = { Friendly = { "F1 {Name}", "F2", "F3" } };
		Bump = { Any = { "Hi {Name}", "Hi {Piece}", "Plain" } };
	}
	Talk.Use(Data)
	Talk.IsMember = function() return false end
	Talk.FirstName = function(P) return P.DisplayName end
	local function player(Attrs)
		return { UserId = 7; DisplayName = "Testy"; Character = nil; GetAttribute = function(_, K) return Attrs[K] end }
	end
	local Friendly = player({ CliqueTier_Test = "Friendly" })
	local Neutral = player({ CliqueTier_Test = "Neutral" })
	local Hostile = player({ CliqueTier_Test = "Hostile" })
	local Wary = player({ CliqueTier_Test = "Wary" })
	check("tier only", Talk.Attitude({ Clique = "Test" }, Friendly), "Friendly")
	check("no tier", Talk.Attitude({ Clique = "Test" }, player({})), "Neutral")
	check("no player", Talk.Attitude({ Clique = "Test" }, nil), "Neutral")
	check("fought: a step down", Talk.Attitude({ Clique = "Test"; Memory = { [7] = { Fought = os.clock(); Met = 0 } } }, Friendly), "Neutral")
	check("fought, already Hostile", Talk.Attitude({ Clique = "Test"; Memory = { [7] = { Fought = os.clock(); Met = 0 } } }, Hostile), "Hostile")
	check("met often: a step up", Talk.Attitude({ Clique = "Test"; Memory = { [7] = { Fought = -1e9; Met = 5 } } }, Neutral), "Friendly")
	check("met often never makes Respected", Talk.Attitude({ Clique = "Test"; Memory = { [7] = { Fought = -1e9; Met = 9 } } }, Friendly), "Friendly")
	Talk.IsMember = function() return true end
	check("member is at least Friendly", Talk.Attitude({ Clique = "Test" }, Wary), "Friendly")
	Talk.IsMember = function() return false end
	check("own pool", Talk.Pool("Test", "Greet", "Friendly")[1], "F1 {Name}")
	check("falls back to Generic", Talk.Pool("Test", "Greet", "Hostile"), Data.Generic.Greet.Hostile)
	check("no clique uses Generic", Talk.Pool(nil, "Bump", "Neutral"), Data.Generic.Bump.Any)
	check("unknown moment", Talk.Pool("Test", "NoSuchMoment", "Neutral"), nil)
	local Line = Talk.Pick({ Clique = "Test" }, "Greet", Friendly)
	check("pick fills the name", Line == "F1 Testy" or Line == "F2" or Line == "F3", true)
	local SawPiece = false
	for _ = 1, 40 do
		local L = Talk.Pick({ Clique = "Test" }, "Bump", Friendly)
		if L == nil or L:find("{", 1, true) then SawPiece = true end
	end
	check("never an unfilled line", SawPiece, false)
	local WithPiece = 0
	for _ = 1, 40 do
		if Talk.Pick({ Clique = "Test" }, "Bump", Friendly, { Piece = "top hat" }) == "Hi top hat" then WithPiece += 1 end
	end
	check("a piece line once a piece is given", WithPiece > 0, true)
	check("attitude override", Talk.Pick({ Clique = "Test" }, "Greet", Friendly, { Attitude = "Hostile" }) ~= nil, true)
	check("stand-in line", Talk.Line("Test", "Greet", Friendly) ~= nil, true)
	check("stand-in, missing moment", Talk.Line("Test", "NoSuchMoment", Friendly), nil)
end)
Tmp:Destroy()
if not Ok then return "ERROR: " .. tostring(Err) end
return (if Bad == 0 then "PASS\n" else `FAIL ({Bad})\n`) .. table.concat(Results, "\n")
