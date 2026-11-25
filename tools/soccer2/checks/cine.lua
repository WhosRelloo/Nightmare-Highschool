-- cine (soccer-2.0, Server, Play): the slot-2 cine state, recorded before and after every round's checks.
local P = game.Players:GetPlayers()[1]
return string.format("PASS CineState=%s Seen=%s Origin=%s", tostring(P:GetAttribute("CineState")), tostring(P:GetAttribute("Seen")), tostring(P:GetAttribute("Origin")))
