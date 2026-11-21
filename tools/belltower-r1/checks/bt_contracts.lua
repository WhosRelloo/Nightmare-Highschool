local P = game.Players.LocalPlayer
local PG = P.PlayerGui
local Out = {}
local Panel = PG.ClockHud.Panel
-- Timetable's click hook is on the cluster (the real click is Step 3b)
table.insert(Out, "timetable hooked " .. tostring(Panel:GetAttribute("NHTimetableHooked") == true))
-- where to click: the dial's centre, in screen px (for Step 3b)
local Dial = Panel.Head:FindFirstChild("Dial") or Panel.Head.Plate
local Inset = game:GetService("GuiService"):GetGuiInset()
table.insert(Out, ("click at %d,%d"):format(Dial.AbsolutePosition.X + Dial.AbsoluteSize.X / 2, Dial.AbsolutePosition.Y + Dial.AbsoluteSize.Y / 2 + Inset.Y))
-- Moments' bell rim still finds the panel
table.insert(Out, "panel for Moments " .. tostring(PG.ClockHud:FindFirstChild("Panel") ~= nil))
-- SchoolFx's "In class" line exists when ClassInRoom
P:SetAttribute("ClassInRoom", true) task.wait(1)
local Found = false
for _, D in PG.ClockHud:GetDescendants() do if D:IsA("TextLabel") and D.Visible and D.Text:find("In class", 1, true) then Found = true end end
table.insert(Out, "in-class line " .. tostring(Found) .. " (needs a class period; false outside class is expected)")
P:SetAttribute("ClassInRoom", nil)
-- Settings ShowClock hides the whole cluster
PG.ClockHud.Enabled = false task.wait(0.3) table.insert(Out, "hidden " .. tostring(not PG.ClockHud.Enabled)) PG.ClockHud.Enabled = true
return table.concat(Out, "\n")
