-- lf_after (playtest-blockers, Server, Play, run_live.py): after a real E press on the box's prompt, the item is
-- handed in (hands empty, Yen paid). Then the slot's day count and Yen go back to what lf_setup recorded.
local Rep = require(game.ServerScriptService.Services.Social.Reputation)
local Data = require(game.ServerScriptService.Services.Player.Data)
local P = game.Players:GetPlayers()[1]
local Prof = Data.GetProfile(P)
local Yen0 = P:GetAttribute(`NHLFTestYen`)
local Paid = Prof.Yen - (Yen0 or Prof.Yen)
local Item = P:GetAttribute(`NHLostItem`)
local Held = P.Character and P.Character:FindFirstChild(`NHHeldLost`) ~= nil
-- put the slot back
local Social = Rep.Get(P)
local N0, D0 = P:GetAttribute(`NHLFTestN`), P:GetAttribute(`NHLFTestDay`)
if Social then
	if N0 == -1 then Social.LostFound = nil else Social.LostFound = { Day = D0; N = N0 } end
	Rep.Sync(P)
end
if Yen0 then Data.UpdateState(P, { type = `UpdateYen`; amount = Yen0 - Prof.Yen }) end
for _, K in { `NHLFTestN`, `NHLFTestDay`, `NHLFTestYen` } do P:SetAttribute(K, nil) end
if Item ~= nil or Held then return `FAIL still carrying {tostring(Item)} (in hand {tostring(Held)})` end
if Paid ~= 20 then return `FAIL paid {Paid} Yen (want 20 for an unclaimed item)` end
return `PASS handed in at the box by its prompt: hands empty, paid {Paid} Yen (Yen and day count put back)`
