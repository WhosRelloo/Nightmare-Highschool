-- healcheck (phase6-strafes T5 round C, Server, Play): Infirmary.Treat and the pluggable Care, through NHGestureProbe.
local B = game.ServerStorage:FindFirstChild("NHGestureProbe")
if not B then return "FAIL no NHGestureProbe" end
local H = game:GetService("HttpService")
local P = game.Players:GetPlayers()[1]
local Fails = {}
local function Ok(C, W) if not C then table.insert(Fails, W) end end
local N = B:Invoke("NurseAt")
if not N.Pos then return "FAIL the Nurse isn't spawned (Config.Npcs Nurse, the NursePost in School.Infirmary)" end
Ok(N.Prompt, "no TreatPrompt on the Nurse")
P.Character.HumanoidRootPart.CFrame = CFrame.lookAt(N.Pos + Vector3.new(0, 0, 3), N.Pos)
P:SetAttribute("CombatTagUntil", nil)
B:Invoke("ResetCooldown") B:Invoke("SetHealth", nil, 40)
task.wait(0.3)
local R = B:Invoke("Treat")
Ok(R.Ok and math.abs(R.Health - R.Max) < 0.01 and not R.Wounded, "treat: " .. H:JSONEncode(R))
Ok((P.Character:GetAttribute("NHBandagedUntil") or 0) > workspace:GetServerTimeNow(), "NHBandagedUntil not set")
B:Invoke("SetHealth", nil, 40)
R = B:Invoke("Treat")
Ok(not R.Ok and R.Why == "Come back in a few minutes.", "cooldown: " .. tostring(R.Why))
B:Invoke("ResetCooldown")
P:SetAttribute("CombatTagUntil", workspace:GetServerTimeNow() + 10)
R = B:Invoke("Treat")
Ok(not R.Ok and R.Why == "Not while you're fighting.", "fight: " .. tostring(R.Why))
P:SetAttribute("CombatTagUntil", nil)
-- interrupt: a hit 1 s in
B:Invoke("ResetCooldown") B:Invoke("SetHealth", nil, 50)
task.delay(1, function() P.Character.Humanoid.Health = 45 end)
R = B:Invoke("Treat")
Ok(not R.Ok and R.Why == "hit" and R.Health < R.Max, "interrupt: " .. H:JSONEncode(R))
-- the swap: a stub Care decides (the injury system's seam)
B:Invoke("StubCare") B:Invoke("SetHealth", nil, 40)
R = B:Invoke("Treat")
Ok(R.Ok and math.abs(R.Health - 77) < 0.01, "stub care: " .. tostring(R.Health))
B:Invoke("RestoreCare") B:Invoke("ResetCooldown")
P.Character.Humanoid.Health = P.Character.Humanoid.MaxHealth
return #Fails == 0 and "PASS healcheck" or ("FAIL healcheck\n" .. table.concat(Fails, "\n"))
