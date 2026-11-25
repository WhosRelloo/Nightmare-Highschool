-- spawn10 (locomotion-pace open row, Server, Play): a fresh spawn walks at 10 before any sprint, after a respawn too,
-- and the template Humanoids hold 10.
local Players = game:GetService("Players")
local P = Players:GetPlayers()[1]
if not P then return "FAIL no player" end
local Out = {}
local SP = game:GetService("StarterPlayer")
local SC = SP:FindFirstChild("StarterCharacter")
local TH = SC and SC:FindFirstChildOfClass("Humanoid")
table.insert(Out, "StarterPlayer.CharacterWalkSpeed " .. SP.CharacterWalkSpeed)
table.insert(Out, "StarterCharacter.Humanoid " .. tostring(TH and TH.WalkSpeed))
local Rig = game.ServerScriptService:FindFirstChild("Rig", true)
local RH = Rig and Rig:FindFirstChildOfClass("Humanoid")
table.insert(Out, "AI Rig.Humanoid " .. tostring(RH and RH.WalkSpeed))
P:LoadCharacter()
local C = P.Character or P.CharacterAdded:Wait()
local H = C:WaitForChild("Humanoid", 10)
task.wait(1)
local Fresh = H and H.WalkSpeed
table.insert(Out, "fresh spawn WalkSpeed " .. tostring(Fresh))
local Fails = {}
if not (TH and TH.WalkSpeed == 10) then table.insert(Fails, "template StarterCharacter") end
if RH and RH.WalkSpeed ~= 10 then table.insert(Fails, "template AI Rig") end
if Fresh ~= 10 then table.insert(Fails, "fresh spawn") end
return (#Fails == 0 and "PASS spawn10" or ("FAIL " .. table.concat(Fails, ", "))) .. " | " .. table.concat(Out, "; ")
