local G = game.Players.LocalPlayer.PlayerGui:FindFirstChild("NHPhone")
if not G then return "no phone gui" end
local T = G.Body.Screen.Home:FindFirstChild("Today")
if not T then return "no today" end
local o = { "body visible " .. tostring(G.Body.Visible), "day " .. T.Day.Text }
for _, r in T.Lines:GetChildren() do
  if r:IsA("TextButton") then table.insert(o, r.Name .. " " .. tostring(r.Visible) .. " | " .. r:FindFirstChild("Text").Text) end
end
table.insert(o, "quiet " .. tostring(T.Lines.Quiet.Visible))
table.insert(o, "grid y " .. tostring(G:FindFirstChild("Grid", true).AbsolutePosition.Y) .. " today bottom " .. tostring(T.AbsolutePosition.Y + T.AbsoluteSize.Y))
return table.concat(o, "\n")
