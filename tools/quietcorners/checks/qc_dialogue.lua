local P = game.Players.LocalPlayer
local PG = P.PlayerGui
local Probe = PG:FindFirstChild("NHQuietProbe")
if not Probe then return "FAIL no NHQuietProbe" end
local QC = require(game.ReplicatedStorage.Functions.QuietCorners)
local DA = require(game.ReplicatedStorage.Config.DialogueArt)
local Seal = require(game.ReplicatedStorage.UI.Theme).Images.Seal
local Fails = {}
local function Ok(C, W) if not C then table.insert(Fails, W) end end
local RMWas = P:GetAttribute("NHReducedMotion")
P:SetAttribute("NHReducedMotion", false)
Probe:Invoke("Dialogue", { Type = "Node"; Id = 9001; Speaker = "Odette Marsh"; Role = "second year"; Clique = "Ink"; Relationship = "Friendly";
	Text = "You came back. Nobody comes back after their first night in Room 106."; Choices = { "What happened in Room 106?", "Maybe you could show me around?", "Pay her ¥10 to keep quiet", "Stay out of my way." };
	Tones = { "Ask", "Kind", "Sly", "Threat" } })
task.wait(2.5)
local I = Probe:Invoke("DialogueInfo")
Ok(I.Crest == QC.Crest(DA, "Ink", true), "Ink crest flipbook") Ok(I.CrestRect == 256, "ImageRectSize 256")
Ok(I.Name == "ODETTE MARSH", "name caps: " .. tostring(I.Name)) Ok(I.Sub:find("The Ink Club", 1, true) ~= nil, "sub: " .. tostring(I.Sub))
Ok(#I.Replies == 4 and I.Replies[3].Tone == "Sly", "replies and tones") Ok(I.Seal == false, "the Seal is drawn somewhere")
Ok(P:GetAttribute("InDialogue") == true, "InDialogue")
for _, L in PG.Dialogue:GetDescendants() do
	if (L:IsA("TextLabel") or L:IsA("TextButton")) and L.Visible and L.Text ~= "" then Ok(L.TextSize >= 20 and L.TextFits, L:GetFullName() .. " " .. L.TextSize) end
end
-- no clique: the Unaffiliated crest; Reduce Motion: frame 0 only
P:SetAttribute("NHReducedMotion", true)
Probe:Invoke("Dialogue", { Type = "Node"; Id = 9002; Speaker = "Wendell Price"; Role = "Custodian"; Text = "Mind the wet floor. And don't go past the boiler room after the last bell, whatever you hear. I mean it, every word of it, all of it, truly."; Choices = { "What's past the boiler room?" } })
local Moved = false
for _ = 1, 20 do task.wait(0.1) I = Probe:Invoke("DialogueInfo") if I.CrestOffset ~= "0, 0" then Moved = true end end
Ok(I.Crest == QC.Crest(DA, nil, true), "Unaffiliated crest") Ok(not Moved, "Reduce Motion: the crest left frame 0")
Ok(I.RibbonH >= 150, "ribbon height") Ok(PG.Dialogue:FindFirstChild("Line", true).TextFits, "long line fits (the ribbon grew)")
Probe:Invoke("DialogueClose")
P:SetAttribute("NHReducedMotion", RMWas)
return #Fails == 0 and "PASS qc_dialogue" or ("FAIL\n" .. table.concat(Fails, "\n"))
