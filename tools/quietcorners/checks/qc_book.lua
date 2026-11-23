local P = game.Players.LocalPlayer
local Probe = P.PlayerGui:FindFirstChild("NHQuietProbe")
if not Probe then return "FAIL no NHQuietProbe" end
local Fails = {}
local function Ok(C, W) if not C then table.insert(Fails, W) end end
Probe:Invoke("Book", true) task.wait(0.8)
local I = Probe:Invoke("BookInfo")
Ok(I.Open and I.Tab == "Journal", "open on Journal") Ok(I.Pages == "Two", "two pages on desktop")
Ok(P:GetAttribute("NHMenuOpen") == true, "menu state")
local Panel = P.PlayerGui.QuestJournal.Panel
local Ink = Color3.fromRGB(40, 22, 16)
for _, L in Panel:GetDescendants() do
	if L:IsA("TextLabel") and L.Visible and L.Text ~= "" then
		Ok(L.TextSize >= 20 and L.TextFits, L:GetFullName() .. " " .. L.TextSize)
	end
end
for _, T in { "Journal", "Evidence", "Record", "Settings" } do Ok(Panel:FindFirstChild("Tab_" .. T, true) ~= nil, "tab " .. T) end
Probe:Invoke("BookTab", "Evidence") task.wait(0.8)
Ok(P.PlayerGui:FindFirstChild("NHEvidenceWall") and P.PlayerGui.NHEvidenceWall.Enabled, "Evidence tab opens the wall")
Probe:Invoke("WallClose") Probe:Invoke("Book", false) task.wait(0.4)
Ok(P:GetAttribute("NHMenuOpen") ~= true, "closed")
return #Fails == 0 and "PASS qc_book" or ("FAIL\n" .. table.concat(Fails, "\n"))
