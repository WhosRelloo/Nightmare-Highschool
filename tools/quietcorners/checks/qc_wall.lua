local P = game.Players.LocalPlayer
local Probe = P.PlayerGui:FindFirstChild("NHQuietProbe")
if not Probe then return "FAIL no NHQuietProbe" end
local Fails = {}
local function Ok(C, W) if not C then table.insert(Fails, W) end end
Probe:Invoke("Wall", "EmptyDesk") task.wait(1)
local I = Probe:Invoke("WallInfo")
Ok(I.Ask == "Where is Mira Holt's original record kept?", "plate ask") Ok(I.Progress == "Clues 4 of 4 · Answered 1 of 2", "progress: " .. tostring(I.Progress))
Ok(#I.Cards == 4, "cards " .. #I.Cards) Ok(#I.Sheets == 3 and I.Sheets[1].State == "Answered", "sheets")
Ok(P:GetAttribute("NHMenuOpen") == true and P:GetAttribute("NHHudState") == "Menu", "menu state")
for _, L in P.PlayerGui.NHEvidenceWall:GetDescendants() do
	if L:IsA("TextLabel") and L.Visible and L.Text ~= "" then Ok(L.TextSize >= 20 and L.TextFits, L:GetFullName() .. " " .. L.TextSize) end
end
-- pin the Originals pair through the real wall
Probe:Invoke("WallPin", "Originals", 1, "AttendanceSheet") Probe:Invoke("WallPin", "Originals", 2, "ArchiveCard")
task.wait(2.5) I = Probe:Invoke("WallInfo")
Ok(I.Sheets[2].State == "Answered", "Originals answered via the wall: " .. tostring(I.Sheets[2].State))
Ok(I.Answers == 4, "answer cards shown when ready: " .. tostring(I.Answers))
Probe:Invoke("WallClose") task.wait(0.4)
Ok(P:GetAttribute("NHMenuOpen") ~= true, "menu closed")
return #Fails == 0 and "PASS qc_wall" or ("FAIL\n" .. table.concat(Fails, "\n"))
