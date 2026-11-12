--[[
	Talk (server). Services.AI.StudentBrain.Talk  (the line matrix; spec docs/superpowers/specs/2026-11-12-line-matrix-outfits-design.md)

	What a student says depends on their clique (Config.CliqueTalk has one module per clique, plus Generic), how they
	feel about you, and the moment. How they feel: your standing tier with their clique (CliqueTier_<Id>), at least
	Friendly if you're a member, one step down if they saw you fight in the last 5 minutes, one step up (never past
	Friendly) if you've met 4 times or more.

	API
	  Talk.Attitude(S, Player?) -> "Hostile" | "Wary" | "Neutral" | "Friendly" | "Respected"
	  Talk.Pool(Clique?, Moment, Attitude, Sub?) -> lines?      the clique's own (attitude, then Any), then Generic's
	  Talk.Pick(S, Moment, Player?, Opts?) -> line?            Opts: Sub (race / verdict), Attitude, Piece, Ctx
	  Talk.Line(Clique, Moment, Player?, Opts?) -> line?        a stand-in student: a leader in dialogue, a notification
	  Talk.Wear(Player) -> { Top, Bottoms, Acc }?               from the character's NHWear (set by UI.Appearance)
	  Talk.Outfit(S, Player) -> (Verdict?, PieceName?)          FullLook | RivalLook | Likes | Mocks (Task 4)
	  Talk.Use(Data?, CliqueCfg?)                               tests: swap the line data / clique config
	Lines with a {Key} that can't be filled (no name, no piece) are skipped, never shown half-filled.
]]

local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

local Lines = require(script.Parent:WaitForChild(`Lines`))
local CliqueConfig = require(ReplicatedStorage.Config.Cliques)
-- a missing or broken line module leaves the matrix empty (every Pick falls back to today's pools)
local OkC, CliqueTalk = pcall(require, ReplicatedStorage.Config:FindFirstChild(`CliqueTalk`))
if not OkC or typeof(CliqueTalk) ~= `table` then CliqueTalk = {} end
local Accessories = require(ReplicatedStorage.Config.Accessories)

local Talk = {}
Talk.Attitudes = { `Hostile`, `Wary`, `Neutral`, `Friendly`, `Respected` }
local Rank = {}
for I, A in Talk.Attitudes do Rank[A] = I end

function Talk.Use(Data: { [string]: any }?, CliqueCfg: { [string]: any }?)
	if Data then CliqueTalk = Data end
	if CliqueCfg then CliqueConfig = CliqueCfg end
end

-- membership (Social.CliqueMembership)
function Talk.IsMember(Player: Player, Clique: string): boolean
	local Social = ServerScriptService:FindFirstChild(`Services`) and ServerScriptService.Services:FindFirstChild(`Social`)
	local Node = Social and Social:FindFirstChild(`CliqueMembership`)
	if not Node then return false end
	local Ok, Is = pcall(function() return require(Node).IsMember(Player, Clique) end)
	return Ok and Is == true
end

-- the name students use: the student's first name (Player.Identity), else the display name (as CliqueMembership does)
function Talk.FirstName(Player: Player): string
	local Name = Player.DisplayName
	pcall(function()
		local Identity = require(ServerScriptService.Services.Player.Identity)
		local Full = Identity.FullName(Identity.Get(Player))
		if typeof(Full) == `string` and Full ~= `` then Name = Full end
	end)
	return string.match(Name, `^(%S+)`) or Name
end

function Talk.Attitude(S, Player: Player?): string
	if not Player then return `Neutral` end
	local Tier = S.Clique and Player:GetAttribute(`CliqueTier_{S.Clique}`)
	local R = Rank[Tier or `Neutral`] or Rank.Neutral
	if S.Clique and Talk.IsMember(Player, S.Clique) then R = math.max(R, Rank.Friendly) end
	local M = S.Memory and S.Memory[Player.UserId]
	if M then
		if os.clock() - (M.Fought or -1e9) < 300 then
			R -= 1
		elseif (M.Met or 0) >= 4 and R < Rank.Friendly then
			R += 1
		end
	end
	return Talk.Attitudes[math.clamp(R, 1, #Talk.Attitudes)]
end

local function cell(Mod: any, Moment: string, Sub: string?, Attitude: string): { string }?
	local Node = typeof(Mod) == `table` and Mod[Moment] or nil
	if Node and Sub then Node = Node[Sub] end
	if typeof(Node) ~= `table` then return nil end
	local P = Node[Attitude]
	if typeof(P) == `table` and #P > 0 then return P end
	P = Node.Any
	if typeof(P) == `table` and #P > 0 then return P end
	return nil
end

function Talk.Pool(Clique: string?, Moment: string, Attitude: string, Sub: string?): { string }?
	return cell(Clique and CliqueTalk[Clique], Moment, Sub, Attitude) or cell(CliqueTalk.Generic, Moment, Sub, Attitude)
end

-- the lines whose every {Key} has a value
local function fillable(Pool: { string }, Ctx: { [string]: any }): { string }
	local Out = {}
	for _, L in Pool do
		local Ok = true
		for K in L:gmatch("{(%w+)}") do
			if Ctx[K] == nil then Ok = false break end
		end
		if Ok then table.insert(Out, L) end
	end
	return Out
end

function Talk.Pick(S, Moment: string, Player: Player?, Opts: { [string]: any }?): string?
	local O = Opts or {}
	local Attitude = O.Attitude or Talk.Attitude(S, Player)
	local Pool = Talk.Pool(S.Clique, Moment, Attitude, O.Sub)
	if not Pool then return nil end
	local Ctx = table.clone(O.Ctx or {})
	if Player then Ctx.Name = Talk.FirstName(Player) end
	Ctx.Piece = O.Piece
	local Def = S.Clique and CliqueConfig.Defs[S.Clique]
	if Def then
		Ctx.Clique = Def.Name
		local Rival = Def.Rival and CliqueConfig.Defs[Def.Rival]
		Ctx.Rival = Rival and Rival.Name
	end
	local Ready = fillable(Pool, Ctx)
	if #Ready == 0 then return nil end
	return Lines.Pick(S, Ready, Ctx)
end

local Stand = {} :: { [string]: { [string]: any } }
function Talk.Line(Clique: string, Moment: string, Player: Player?, Opts: { [string]: any }?): string?
	Stand[Clique] = Stand[Clique] or { Clique = Clique }
	return Talk.Pick(Stand[Clique], Moment, Player, Opts)
end

---| outfits |---

function Talk.Wear(Player: Player?): { Top: string, Bottoms: string, Acc: { string } }?
	local C = Player and Player.Character
	return C and CliqueConfig.ParseWear(C:GetAttribute(`NHWear`)) or nil
end

-- the name of the worn piece a taste rule matches, in lower case
local function matched(Rule: { [string]: string }, W): string?
	if Rule.Top then return if W.Top == Rule.Top then (string.gsub(W.Top, `-`, ` `)) else nil end
	for _, Id in W.Acc do
		local It = Accessories.ById[Id]
		if It and (Rule.Id == Id or (Rule.Kit ~= nil and It.Kit == Rule.Kit) or (Rule.Slot ~= nil and It.Slot == Rule.Slot)) then
			return string.lower(It.Name)
		end
	end
	return nil
end

-- another clique besides the rival also wears this top (black-blazer: Court and Choir), so it's no rival's colours
local function shared(Rival: string, Top: string?): boolean
	for Other in CliqueConfig.Defs do
		if Other ~= Rival and CliqueConfig.WearsTop(Other, Top) then return true end
	end
	return false
end

-- what this student thinks of your outfit (first match wins): their clique's full look, a top only their rival wears,
-- a piece they like, a piece they mock. A student without a clique only remarks on a random accessory you wear.
function Talk.Outfit(S, Player: Player?): (string?, string?)
	local W = Talk.Wear(Player)
	if not W then return nil end
	local Id = S.Clique
	local Def = Id and CliqueConfig.Defs[Id]
	if not Def then
		if #W.Acc == 0 then return nil end
		local It = Accessories.ById[W.Acc[math.random(1, #W.Acc)]]
		if not It then return nil end
		return `Likes`, string.lower(It.Name)
	end
	if CliqueConfig.WearsTop(Id, W.Top) and CliqueConfig.WearsBottoms(Id, W.Bottoms) then return `FullLook` end
	if Def.Rival and CliqueConfig.WearsTop(Def.Rival, W.Top) and not shared(Def.Rival, W.Top) then return `RivalLook` end
	local T = Def.Taste or {}
	for _, R in T.Likes or {} do
		local N = matched(R, W)
		if N then return `Likes`, N end
	end
	for _, R in T.Mocks or {} do
		local N = matched(R, W)
		if N then return `Mocks`, N end
	end
	return nil
end

return Talk
