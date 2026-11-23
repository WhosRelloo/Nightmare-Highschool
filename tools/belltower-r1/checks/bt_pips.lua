-- (2.36.1) Pip overflow: at Need 5 and 6 the fang pips plus the count must stop before the J key.
-- The check runner gets its own copy of every module (no profile, no tracker state), so it can't drive the live
-- tracker. Instead it clones the live card's Pips row in place (same width, same layout) and fills it the way
-- Local.SetPips does: the pip size rule is read from QuestTracker's source so the check follows the code.
local P = game.Players.LocalPlayer
local PG = P.PlayerGui
local Fails, Out = {}, {}
local function Check(Ok, What) if not Ok then table.insert(Fails, What) end end
local Src = P.PlayerScripts.Controllers.Gui.QuestTracker.Source
local Big, Small = Src:match("local Px = if Need > 4 then (%d+) else (%d+)")
Small, Big = tonumber(Big), tonumber(Small) -- (first capture is the Need > 4 size)
Check(Small ~= nil and Big ~= nil, "QuestTracker has no 'local Px = if Need > 4 then A else B' pip rule")
if not (Small and Big) then return "FAIL bt_pips\n" .. table.concat(Fails, "\n") end
local Tracker = PG.QuestTracker.Tracker
local WasVisible = Tracker.Visible
Tracker.Visible = true
local Foot = Tracker:FindFirstChild("Foot", true)
local Live, Key, Footer = Foot.Pips, Foot.Key, Foot.Footer
local Font = Footer.Font
for _, Need in { 3, 4, 5, 6 } do
	local Row = Live:Clone()
	for _, K in Row:GetChildren() do if K:IsA("GuiObject") then K:Destroy() end end
	Row.Name = "PipsProbe"
	local Px = if Need > 4 then Small else Big
	for I = 1, Need do
		local Img = Instance.new("ImageLabel")
		Img.LayoutOrder = I Img.BackgroundTransparency = 1 Img.Size = UDim2.fromOffset(Px, Px) Img.Parent = Row
	end
	local Count = Instance.new("TextLabel")
	Count.LayoutOrder = 99 Count.BackgroundTransparency = 1 Count.AutomaticSize = Enum.AutomaticSize.X
	Count.Size = UDim2.fromOffset(0, 30) Count.Font = Font Count.TextSize = 20 Count.Text = `  {Need}/{Need}`
	Count.Parent = Row
	Row.Parent = Foot
	task.wait(0.2)
	local Right = Count.AbsolutePosition.X + Count.AbsoluteSize.X
	local Stop = if Key.Visible then Key.AbsolutePosition.X else Footer.AbsolutePosition.X + Footer.AbsoluteSize.X - Footer.TextBounds.X
	table.insert(Out, ("need %d: %d px pips, row ends %.0f, frame ends %.0f, key at %.0f"):format(Need, Px, Right, Row.AbsolutePosition.X + Row.AbsoluteSize.X, Stop))
	Check(Right <= Stop, "need " .. Need .. ": the pips and count reach the J key")
	Check(Right <= Row.AbsolutePosition.X + Row.AbsoluteSize.X + 0.5, "need " .. Need .. ": the row overflows the Pips frame")
	Row:Destroy()
end
Tracker.Visible = WasVisible
return (#Fails == 0 and "PASS bt_pips" or ("FAIL bt_pips\n" .. table.concat(Fails, "\n"))) .. "\n" .. table.concat(Out, "\n")
