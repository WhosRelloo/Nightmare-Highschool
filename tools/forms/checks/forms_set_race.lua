-- forms check (server, game VM via harness/server.py): set the Player's Race ATTRIBUTES only (no transform, the profile
-- untouched), so the client's Bloodline Looks and preview show that race. Edit RACE / LOOKS per run.
local RACE, LOOKS = "Vampire", "FormDirection=2"
local P = game.Players:GetPlayers()[1]
P:SetAttribute("Race", RACE)
P:SetAttribute("RaceTier", 3)
P:SetAttribute("RaceLooks", LOOKS)
return "Race=" .. tostring(P:GetAttribute("Race")) .. " Looks=" .. tostring(P:GetAttribute("RaceLooks"))
