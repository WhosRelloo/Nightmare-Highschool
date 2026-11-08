local function patch(inst, anchor, insert, mode)
  local s = inst.Source
  local a, b = s:find(anchor, 1, true)
  assert(a, inst.Name .. ": anchor missing: " .. anchor:sub(1, 60))
  assert(not s:find(anchor, b + 1, true), inst.Name .. ": anchor twice: " .. anchor:sub(1, 60))
  if mode == "before" then s = s:sub(1, a - 1) .. insert .. s:sub(a)
  elseif mode == "after" then s = s:sub(1, b) .. insert .. s:sub(b + 1)
  else s = s:sub(1, a - 1) .. insert .. s:sub(b + 1) end
  inst.Source = s
end
local RS, SSS = game.ReplicatedStorage, game.ServerScriptService
local Lin = RS.Lineage
local Adm = SSS.Services.Features.Admin
local Pan = game.StarterPlayer.StarterPlayerScripts.Controllers.Gui.AdminPanel
assert(not Lin.Source:find("AdminSetRace", 1, true), "already patched")

-- Lineage: staff set a race (any variant) or a tier, through the normal save path (the admin panel calls these)
patch(Lin, "\nend\n\n--------------------------------------------------------------------------\n-- client", [[

	-- (admin, 1.65) the Headmaster's Desk sets a student's race (any variant) or forces a tier. A new race keeps the
	-- tier (staff set that separately) but clears hunger and race looks, like a race spin; Earned stops the old
	-- kill-count migration from lifting the tier again.
	function Lineage.AdminSetRace(p, subId)
		local l = current(p)
		if not l then return false, "Their record is still loading" end
		local s = SubById[subId]
		if not s then return false, "Unknown race" end
		if l.Race ~= s.Race.Id then
			l.Hunger = 0
			l.Looks = {}
		end
		l.Race = s.Race.Id
		l.SubRace = subId
		l.Earned = true
		save(p, l)
		return true, l
	end
	function Lineage.AdminSetTier(p, tier)
		local l = current(p)
		if not (l and l.Race) then return false, "Their record is still loading" end
		tier = tonumber(tier)
		if not tier or tier ~= math.floor(tier) or tier < 1 or tier > #Lineage.TierKills then return false, "Pick Tier I, II or III" end
		l.Tier = tier
		l.Earned = true
		save(p, l)
		return true, l
	end]], "before")

-- Admin: the two commands, and the tier in the student list
patch(Adm, "C.Speed = { Target = true; Run = function(A, T, a)", [[-- (race, 1.65) set a student's race and variant, or force their tier (ReplicatedStorage.Lineage). The full game saves
-- it; the Map place keeps it for the session.
C.SetRace = { Target = true; Run = function(A, T, a)
	local L = require(ReplicatedStorage.Lineage)
	if not L.AdminSetRace then return false, `No race system here` end
	local ok, r = L.AdminSetRace(T, str(a.Sub, 24))
	if not ok then return false, tostring(r) end
	local S = L.SubById[r.SubRace]
	return true, `{T.Name} is now {S and S.Sub.Name or r.Race} ({r.Race}), Tier {({ `I`, `II`, `III` })[r.Tier] or r.Tier}`
end }
C.SetTier = { Target = true; Run = function(A, T, a)
	local L = require(ReplicatedStorage.Lineage)
	if not L.AdminSetTier then return false, `No race system here` end
	local ok, r = L.AdminSetTier(T, a.Tier)
	if not ok then return false, tostring(r) end
	return true, `{T.Name} is now Tier {({ `I`, `II`, `III` })[r.Tier]}, {L.TierName(r.Race, r.Tier)}`
end }
]], "before")
patch(Adm, "Height = P:GetAttribute(`HeightText`);", " Sub = P:GetAttribute(`SubRace`); Tier = P:GetAttribute(`RaceTier`);", "after")

-- AdminPanel: Race and Tier on the Student tab, My race and My tier on the Self tab, the tier in the list
patch(Pan, "{tostring(P.Race)}{if P.Height", "{tostring(P.Sub or P.Race)}{if P.Tier then ` ` .. (({ `I`, `II`, `III` })[P.Tier] or ``) else ``}{if P.Height", "replace")
local RACE_UI = [[
		-- (race, 1.65) every race and variant, and tiers I to III (the server checks and saves through Lineage)
		local function raceButtons(Target: number?)
			local okL, L = pcall(require, ReplicatedStorage:WaitForChild(`Lineage`))
			if not okL then return end
			local gr = grid(Body, nxt())
			for _, R in L.Races do
				for _, S in R.Subs do
					button(gr, S.Name, function() run(`SetRace`, true, { Sub = S.Id }, Target) end, if S.Id == R.Id then `gold` else nil)
				end
			end
		end
		local function tierButtons(Target: number?)
			local gt = grid(Body, nxt())
			for T, Name in { `Tier I`, `Tier II`, `Tier III` } do
				button(gt, Name, function() run(`SetTier`, true, { Tier = T }, Target) end, if T == 3 then `gold` else nil)
			end
		end
]]
patch(Pan, "\t\theader(Body, `Rewards`, nxt())", RACE_UI .. [[
		header(Body, `Race (gold: the base race, then its variants)`, nxt())
		raceButtons(nil)
		header(Body, `Tier`, nxt())
		tierButtons(nil)
]], "before")
patch(Pan, "\telseif tab == `Server` then", RACE_UI .. [[
		header(Body, `My race`, nxt())
		raceButtons(Player.UserId)
		header(Body, `My tier`, nxt())
		tierButtons(Player.UserId)
]], "before")
local out = {}
for _, m in { Lin, Adm, Pan } do local f, e = loadstring(m.Source) table.insert(out, m.Name .. " " .. (f and "ok" or ("ERR " .. tostring(e)))) end
return table.concat(out, " | ")
