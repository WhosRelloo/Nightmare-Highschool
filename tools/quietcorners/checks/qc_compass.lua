local P = game.Players.LocalPlayer
local PG = P.PlayerGui
local QC = require(game.ReplicatedStorage.Functions.QuietCorners)
local Art = require(game.ReplicatedStorage.Config.QuietCornersArt)
local Fails = {}
local function Ok(C, W) if not C then table.insert(Fails, W) end end
local Root = PG.NHCompass:FindFirstChild("Compass", true)
Ok(Root and Root.Parent.Name == "QcFade", "compass adopted")
local Back = Root and Root:FindFirstChild("Back")
local Want = QC.Image(Art, "CompassStrip", P:GetAttribute("Race"))
if Want then Ok(Back and Back:IsA("ImageLabel") and Back.Image == Want, "strip art") else Ok(Back ~= nil, "fallback back") end
for _, L in Root:GetDescendants() do
	if L:IsA("TextLabel") and L.Visible and L.Text ~= "" then Ok(L.TextSize >= 20, "text " .. L.Text .. " " .. L.TextSize) end
end
local RaceWas = P:GetAttribute("Race")
P:SetAttribute("Race", "Vampire") task.wait(0.3)
local WantV = QC.Image(Art, "CompassStrip", "Vampire")
if WantV then Ok(Back.Image == WantV, "race re-skin") end
P:SetAttribute("Race", RaceWas)
return #Fails == 0 and "PASS qc_compass" or ("FAIL\n" .. table.concat(Fails, "\n"))
