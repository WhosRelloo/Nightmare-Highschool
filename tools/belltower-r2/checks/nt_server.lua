local B = game.ServerStorage:FindFirstChild("NHNotorietyProbe")
if not B then return "FAIL no NHNotorietyProbe" end
local P = game.Players:GetPlayers()[1]
if not P then return "FAIL no player" end
local N = P.Name
local F = require(game.ReplicatedStorage.Functions.Notoriety) -- pure: a VM copy is fine
local Fails, Notes = {}, {}
local function Ok(C, What) if not C then table.insert(Fails, What) end end
local function Call(...) local R = B:Invoke(...) if type(R) == "table" and R.Error then table.insert(Fails, "probe error: " .. tostring(R.Error)) end return R end

-- 1. a witnessed truancy: Heat = Gain, Lit, not booked
Call("Reset", N) Call("Manual", N, false, {})
local G = Call("Witness", N, "Truancy")
local Want = F.Gain("Truancy", { Night = G.Night, Probation = G.Probation })
Ok(math.abs(G.Heat - Want) < 0.01, "1 heat " .. G.Heat .. " want " .. Want)
Ok(G.Tier == F.Tier(Want), "1 tier " .. G.Tier) Ok(G.Misdeed == "Truancy" and G.Booked == false, "1 misdeed/booked")
Ok(P:GetAttribute("NHBells") == G.Tier, "1 NHBells attribute")
-- 2. unseen for 12 s: it cools to 0, and nobody knew the face, so no summons
G = Call("Advance", N, 12)
Ok(G.Heat == 0 and G.Tier == 0, "2 cooled " .. G.Heat) Ok(G.Summons == 0, "2 no summons") Ok(P:GetAttribute("NHBells") == nil, "2 attribute cleared")
-- 3. a recognised fight: booked (+4) at once, identified, Heat 25+
Call("Reset", N) Call("Manual", N, false, {})
local P0 = Call("Get", N).Points
G = Call("Report", N, "Fighting", true, false)
Ok(G.Points - P0 == 4, "3 points +" .. (G.Points - P0)) Ok(G.Identified == true, "3 identified") Ok(G.Tier >= 2, "3 tier " .. G.Tier)
G = Call("Advance", N, 0.25) Ok(G.State == "Search", "3 search state " .. tostring(G.State))
Ok(P:GetAttribute("NHBellState") == "Search", "3 NHBellState attribute")
G = Call("Advance", N, 40) Ok(G.Heat == 0 and G.Summons == 0, "3 booked fight: no summons")
-- 4. caught at Bell 3: +1 bonus on top of Truancy's 2
Call("Reset", N) Call("Manual", N, false, {})
Call("Witness", N, "Fighting") G = Call("Witness", N, "Fighting")
Ok(G.Tier >= 3, "4 tier " .. G.Tier)
P0 = G.Points
G = Call("Report", N, "Truancy", true, true)
Ok(G.Points - P0 == 2 + F.Bonus(3) or G.Points - P0 == 2 + F.Bonus(4), "4 caught points +" .. (G.Points - P0))
Ok(G.Heat == 0 and G.Tier == 0, "4 cleared on catch")
-- 5. an identified escape becomes a summons; serving books it without the bonus
Call("Reset", N) Call("Manual", N, true, {})
Call("Witness", N, "Vandalism") G = Call("Advance", N, 2.25)
Ok(G.Identified == true, "5 identified after 2 s lit")
Call("Manual", N, false, {}) G = Call("Advance", N, 60)
Ok(G.Summons == 1, "5 summons " .. G.Summons) Ok(P:GetAttribute("NHSummons") == 1, "5 NHSummons attribute")
P0 = G.Points G = Call("Serve", N)
Ok(G.Points - P0 == 3 and G.Summons == 0, "5 served +" .. (G.Points - P0))
-- 6. an ignored summons: Skipped Detention (+4)
Call("Reset", N) Call("Manual", N, true, {}) Call("Witness", N, "Vandalism") Call("Advance", N, 2.25)
Call("Manual", N, false, {}) G = Call("Advance", N, 60)
P0 = G.Points G = Call("AgeSummons", N, 2)
Ok(G.Summons == 0 and G.Points - P0 == 4, "6 expired +" .. (G.Points - P0))
-- 7. the alibi cools three times faster
Call("Reset", N) Call("Manual", N, false, { Alibi = true }) Call("Witness", N, "Fighting")
G = Call("Advance", N, 4)
local W = F.Gain("Fighting", { Night = G.Night, Probation = G.Probation })
Ok(math.abs(G.Heat - math.max(0, W - 1.5 * 3 * 4)) < 0.6, "7 alibi heat " .. G.Heat)
-- 8. escalation at Bell 3 asks a monitor to respond (observed: depends on a monitor within 260 studs)
Call("Reset", N) Call("Manual", N, false, {}) Call("Witness", N, "Fighting") G = Call("Witness", N, "Fighting")
table.insert(Notes, "8 RespondOk=" .. tostring(G.RespondOk) .. " monitors=" .. #Call("Monitors", N))
-- leave it clean
Call("Reset", N) Call("Live", N)
return (#Fails == 0 and "PASS nt_server" or ("FAIL\n" .. table.concat(Fails, "\n"))) .. "\n" .. table.concat(Notes, "\n")
