--[[
	LockOn (client binding): middle mouse locks on to the nearest opponent, and again lets go (combat concept 5, 2.11.0).
	The work is in LockOn.Core; Combat.M1 / Combat.M2 call its aim assist on every swing.
]]
return function(Character: Model, InputState: string, Action: string, Data: any)
	if not Character then return end
	if Character:GetAttribute(`HasSportBall`) or Character:GetAttribute(`InSport`) then return end
	require(script.Core).Toggle(Character)
end
