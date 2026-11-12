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
local CliqueTalk = require(ReplicatedStorage.Config:WaitForChild(`CliqueTalk`))
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

return Talk
