local P = game.Players.LocalPlayer
local Root = P.Character and P.Character:FindFirstChild("HumanoidRootPart")
local Best, D = nil, math.huge
for _, Pr in workspace:GetDescendants() do
	if Pr:IsA("ProximityPrompt") and Pr.Enabled and (Pr.ActionText == "Talk" or Pr.ActionText:find("Talk")) then
		local Part = Pr.Parent:IsA("BasePart") and Pr.Parent or Pr.Parent:FindFirstChildWhichIsA("BasePart", true)
		if Part and (Part.Position - Root.Position).Magnitude < D then Best, D = Pr, (Part.Position - Root.Position).Magnitude end
	end
end
if not Best then return "SKIP no Talk prompt in workspace" end
local Home = Root.CFrame
local Part = Best.Parent:IsA("BasePart") and Best.Parent or Best.Parent:FindFirstChildWhichIsA("BasePart", true)
Root.CFrame = CFrame.new(Part.Position + Part.CFrame.LookVector * 4, Part.Position)
task.wait(1) Best:InputHoldBegin() task.wait(math.max(0.1, Best.HoldDuration) + 0.1) Best:InputHoldEnd()
task.wait(2)
local I = P.PlayerGui.NHQuietProbe:Invoke("DialogueInfo")
local Seal = require(game.ReplicatedStorage.UI.Theme).Images.Seal
local Out = ("speaker=%s crest=%s seal=%s replies=%d"):format(tostring(I.Name), tostring(I.Crest), tostring(I.Seal), I.Replies and #I.Replies or -1)
P.PlayerGui.NHQuietProbe:Invoke("DialogueClose")
Root.CFrame = Home
return ((I.Crest and I.Crest ~= "" and I.Crest ~= Seal and I.Seal == false) and "PASS qc_dialogue_real " or "FAIL qc_dialogue_real ") .. Out
