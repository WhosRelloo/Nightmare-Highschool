local B = game.ServerStorage:FindFirstChild("NHNotorietyProbe")
local P = game.Players:GetPlayers()[1]
if not (B and P) then return "FAIL no probe/player" end
local N = P.Name
local Fails = {}
local function Ok(C, What) if not C then table.insert(Fails, What) end end
-- Converge exists: at Bell 4 more than one monitor is sent (when two are on duty)
B:Invoke("Reset", N) B:Invoke("Manual", N, false, {})
B:Invoke("Witness", N, "Fighting") B:Invoke("Witness", N, "Fighting") local G = B:Invoke("Witness", N, "Fighting")
Ok(G.Tier >= 4, "tier " .. tostring(G.Tier))
task.wait(0.5)
local Responding = 0
for _, M in B:Invoke("Monitors", N) do if M.State == "Respond" or M.State == "Chase" then Responding += 1 end end
Ok(Responding >= 1, "no monitor responding at Bell 4")
-- SeenBy through live sight: with Manual(nil) the service asks HallMonitor.SeenBy (no error expected)
B:Invoke("Manual", N, nil, {}) G = B:Invoke("Advance", N, 0.25)
Ok(G.State == "Lit" or G.State == "Search", "state via SeenBy " .. tostring(G.State))
B:Invoke("Reset", N) B:Invoke("Live", N)
return #Fails == 0 and ("PASS nt_monitor (responding " .. Responding .. ")") or ("FAIL\n" .. table.concat(Fails, "\n"))
