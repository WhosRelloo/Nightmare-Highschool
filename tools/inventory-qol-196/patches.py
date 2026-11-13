# Inventory QOL batch 4 (1.94.0): Best food (smart eat) on the server, and the buff cooldown in State for the wheel.
INV = "ServerScriptService.Services.Features.Inventory"
EDITS = [
(INV, """		HealReady = Cd.Heal or 0; -- server time""", """		HealReady = Cd.Heal or 0; -- server time
		BuffReady = Cd.Buff or 0; -- (inventory QOL 1.94) the one-sip wait, for the snack wheel"""),
(INV, """-- (inventory QOL 1.93) put back the last drop, within 5 s""", """-- (inventory QOL 1.94) Best food: the cheapest food you carry that covers the health you're missing (food heals half
-- while you're combat-tagged); if nothing covers it, the biggest heal you have. Uses it through Shared.Use.
function Shared.UseBest(P: Player): (boolean, string?)
	local Inv = Shared.Get(P)
	local Hum = P.Character and P.Character:FindFirstChildOfClass(`Humanoid`)
	if not (Inv and Hum) or Hum.Health <= 0 then return false, nil end
	local Missing = Hum.MaxHealth - Hum.Health
	if Missing < 1 then return false, `You're not hurt.` end
	local Tagged = (P:GetAttribute(`CombatTagUntil`) or 0) > workspace:GetServerTimeNow()
	local Best, Covers, Cost, Heal = nil, false, math.huge, 0
	for Id, N in Inv.Items do
		local It = Items.ById[Id]
		if It and It.Kind == `Heal` and N > 0 then
			local H = (It.Heal or 0) * (if Tagged then 0.5 else 1)
			local Price = It.Price or 0
			if H >= Missing then
				if not Covers or Price < Cost or (Price == Cost and H < Heal) then Best, Covers, Cost, Heal = It, true, Price, H end
			elseif not Covers and H > Heal then
				Best, Cost, Heal = It, Price, H
			end
		end
	end
	if not Best then return false, `No food on you. The stand by the west doors sells it.` end
	local Ok, Msg = Shared.Use(P, Best.Id)
	if Ok then return true, `{Best.Name}: +{math.floor(Heal)} health` end
	return false, Msg
end

-- (inventory QOL 1.93) put back the last drop, within 5 s"""),
(INV, """	local Undo, Fav = rf(`Undo`), rf(`Fav`) -- (inventory QOL 1.93)""", """	local Undo, Fav = rf(`Undo`), rf(`Fav`) -- (inventory QOL 1.93)
	local UseBest = rf(`UseBest`) -- (inventory QOL 1.94)"""),
(INV, """	Fav.OnServerInvoke = function(P, Id, On) if limited(P) then return false, `One moment...` end return Shared.Fav(P, Id, On == true) end""",
      """	Fav.OnServerInvoke = function(P, Id, On) if limited(P) then return false, `One moment...` end return Shared.Fav(P, Id, On == true) end
	UseBest.OnServerInvoke = function(P) if limited(P) then return false, `One moment...` end return Shared.UseBest(P) end"""),
]
