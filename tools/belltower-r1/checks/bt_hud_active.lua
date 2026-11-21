local P = game.Players.LocalPlayer
local PG = P:WaitForChild("PlayerGui")
local Fails = {}
local function Check(Ok, What) if not Ok then table.insert(Fails, What) end end
local function Shown(G)
	local X = G
	while X and X:IsA("GuiObject") do if not X.Visible then return false end X = X.Parent end
	return true
end
local State = ... or "active" -- "owed" | "warning" | "clear" | "active" | "suspended"
local Sets = {
	clear = { DisciplineLevel = "Clear", DisciplinePoints = 0, DetentionsOwed = 0, DetentionActive = false, Suspended = false },
	warning = { DisciplineLevel = "Warning", DisciplinePoints = 3, DetentionsOwed = 0, DetentionActive = false, Suspended = false },
	owed = { DisciplineLevel = "Detention", DisciplinePoints = 6, DetentionsOwed = 1, DetentionActive = false, Suspended = false },
	active = { DisciplineLevel = "Detention", DisciplinePoints = 6, DetentionsOwed = 1, DetentionActive = true, DetentionCollected = 2, DetentionTotal = 5, Suspended = false },
	suspended = { DisciplineLevel = "Suspension", DisciplinePoints = 19, DetentionsOwed = 0, DetentionActive = false, Suspended = true },
}
for K, V in Sets[State] do P:SetAttribute(K, V) end
task.wait(1.2) -- ClockHud ticks every 0.5 s

local Hud = PG:FindFirstChild("ClockHud")
local Panel = Hud and Hud:FindFirstChild("Panel")
Check(Panel ~= nil, "ClockHud.Panel missing")
if not Panel then return "FAIL\n" .. table.concat(Fails, "\n") end
local Frames = 0
for _, K in Hud:GetChildren() do if K:IsA("Frame") then Frames += 1 end end
Check(Frames == 1 and Hud:FindFirstChildWhichIsA("Frame") == Panel, "Panel must be ClockHud's only Frame child")
Check(Panel:FindFirstChild("Head") and Panel.Head:FindFirstChild("Plate"), "Head.Plate missing")
local Conduct = Panel:FindFirstChild("Conduct")
Check(Conduct ~= nil, "Conduct row missing")
if Conduct then
	local WantVisible = State ~= "clear"
	Check(Conduct.Visible == WantVisible, "Conduct.Visible " .. tostring(Conduct.Visible) .. " for " .. State)
	if State == "owed" then Check(Conduct.Slip.Visible and Conduct.Slip.Title.Text == "Detention owed", "owed slip") end
	if State == "active" then Check(Conduct.Slip.Line.Text == "Trash 2/5", "active slip line") end
	if State == "warning" then Check(Conduct.Level.Text == "Warning · 3 pts", "warning level text: " .. Conduct.Level.Text) end
	if State == "suspended" then Check(Conduct.Level.Text == "Suspended", "suspended text") end
end
-- the hand follows the clock
local Dial = Panel:FindFirstChild("Head") and Panel.Head:FindFirstChild("Dial")
if Dial then
	local ST = require(game.ReplicatedStorage.Functions.SchoolTime)
	local S = ST.GetState(game.ReplicatedStorage.SchoolClock:GetAttribute("Epoch"), workspace:GetServerTimeNow())
	local Want = ((S.MinuteOfDay / 60) / 24 * 360 + 180) % 360
	local D = math.abs(Dial.Hand.Rotation - Want)
	Check(math.min(D, 360 - D) < 1.5, "hand off by " .. D)
	Check(Dial.Moon.Visible, "moon not in the dial window")
end
-- the house text floor, and nothing cut off
for _, G in { Hud, PG:FindFirstChild("QuestTracker") } do
	for _, L in (G and G:GetDescendants() or {}) do
		if (L:IsA("TextLabel") or L:IsA("TextButton")) and L.Text ~= "" and Shown(L) and not L:FindFirstAncestorWhichIsA("BillboardGui") then
			Check(L.TextSize >= 20, L:GetFullName() .. " TextSize " .. L.TextSize)
			Check(L.TextFits, L:GetFullName() .. " text doesn't fit")
		end
	end
end
-- contracts
Check(Panel:GetAttribute("NHTimetableHooked") == true, "Timetable click hook missing")
local QT = PG:FindFirstChild("QuestTracker")
local T = QT and QT:FindFirstChild("Tracker")
Check(T ~= nil, "QuestTracker.Tracker missing")
if T and T.Visible and T.AnchorPoint.X > 0.5 then
	Check(T.AbsolutePosition.Y >= Panel.AbsolutePosition.Y + Panel.AbsoluteSize.Y - 1, "tracker overlaps the clock cluster")
end
return #Fails == 0 and ("PASS bt_hud " .. State) or ("FAIL " .. State .. "\n" .. table.concat(Fails, "\n"))
