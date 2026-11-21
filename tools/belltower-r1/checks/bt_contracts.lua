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
-- (2.36.1) Settings ShowClock hides the whole cluster: run the real UI.Settings handler (Apply, no save),
-- and the Lead Card goes back to its default desktop Y (200 design px) while the clock is off
local Settings = require(game.ReplicatedStorage.UI.Settings)
local Was = Settings.Current.ShowClock
local T = PG:FindFirstChild("QuestTracker") and PG.QuestTracker:FindFirstChild("Tracker")
Settings.Current.ShowClock = false Settings.Apply("ShowClock") task.wait(0.5)
table.insert(Out, "hidden " .. tostring(PG.ClockHud.Enabled == false))
if T and T.AnchorPoint.X > 0.5 then table.insert(Out, "card at default Y " .. tostring(T.Position.Y.Offset == 200) .. " (" .. T.Position.Y.Offset .. ")") end
Settings.Current.ShowClock = if Was == nil then true else Was Settings.Apply("ShowClock") task.wait(0.5)
table.insert(Out, "shown again " .. tostring(PG.ClockHud.Enabled == true))
if T and T.AnchorPoint.X > 0.5 then table.insert(Out, "card under cluster " .. tostring(T.Position.Y.Offset ~= 200)) end
return table.concat(Out, "\n")
