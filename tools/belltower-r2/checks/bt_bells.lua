local P = game.Players.LocalPlayer
local PG = P:WaitForChild("PlayerGui")
local Fails = {}
local function Check(C, What) if not C then table.insert(Fails, What) end end
local function Shown(G) local X = G while X and X:IsA("GuiObject") do if not X.Visible then return false end X = X.Parent end return true end
local Panel = PG.ClockHud.Panel
local Frames = 0 for _, K in PG.ClockHud:GetChildren() do if K:IsA("Frame") then Frames += 1 end end
Check(Frames == 1, "Panel must stay ClockHud's only Frame child")
-- Bell 3, searching
P:SetAttribute("NHBells", 3) P:SetAttribute("NHBellState", "Search") P:SetAttribute("NHSearchWhere", "The Library")
task.wait(1.2)
local Row = Panel:FindFirstChild("Bells")
Check(Row and Row.Visible, "rail hidden at Bell 3")
if Row then
	local N = 0 for I = 1, 5 do local B = Row:FindFirstChild("Bell" .. I) if B and B.Visible then N += 1 end end
	Check(N == 3, "bells shown " .. N)
	Check(Row.Status.ContentText == "Named · searching · The Library", "status " .. Row.Status.ContentText)
	Check(Row.Status.TextSize >= 20 and Row.Status.TextFits, "status size/fit")
	Check(Row.AbsolutePosition.Y >= Panel.Head.AbsolutePosition.Y + Panel.Head.AbsoluteSize.Y - 1, "rail under the plate")
end
local T = PG.QuestTracker:FindFirstChild("Tracker")
if T and T.Visible then
	local Obj = T:FindFirstChild("Objective", true)
	Check(Obj and not Shown(Obj), "card not folded")
	Check(T.AnchorPoint.X < 0.5 or T.AbsolutePosition.Y >= Panel.AbsolutePosition.Y + Panel.AbsoluteSize.Y - 1, "tracker overlaps the cluster")
end
-- the floor
for _, L in Panel:GetDescendants() do
	if L:IsA("TextLabel") and L.Text ~= "" and Shown(L) then Check(L.TextSize >= 20, L:GetFullName() .. " size " .. L.TextSize) end
end
-- cleared
P:SetAttribute("NHBells", nil) P:SetAttribute("NHBellState", nil) P:SetAttribute("NHSearchWhere", nil)
task.wait(1.2)
Check(Row and not Row.Visible, "rail still shown at Bell 0")
if T and T.Visible then local Obj = T:FindFirstChild("Objective", true) Check(Obj and Shown(Obj), "card not unfolded") end
return #Fails == 0 and "PASS bt_bells" or ("FAIL\n" .. table.concat(Fails, "\n"))
