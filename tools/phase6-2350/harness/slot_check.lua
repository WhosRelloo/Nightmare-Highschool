-- slot_check.lua (Server VM): the player's save slot and menu state (round_start.sh refuses to snapshot anything but slot 2)
local P = game.Players:GetPlayers()[1]
return "Slot=" .. tostring(P and P:GetAttribute("Slot")) .. " InMainMenu=" .. tostring(P and P:GetAttribute("InMainMenu"))
