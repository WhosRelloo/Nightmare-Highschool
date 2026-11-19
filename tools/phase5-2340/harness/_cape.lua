local P = game.Players:GetPlayers()[1]
local o = {}
for _, d in P.Character:GetChildren() do table.insert(o, d.ClassName .. ":" .. d.Name) end
local pin = P.Character:FindFirstChild("AcademicPin", true)
local T = P.Character.Torso
if pin then table.insert(o, "pin local " .. tostring(T.CFrame:PointToObjectSpace(pin.Position))) end
for _, d in P.Character:GetDescendants() do
  if (d:IsA("BasePart")) and d.Parent and (d.Parent.Name:lower():find("cape") or d.Name:lower():find("cape") or d.Name:lower():find("mantle")) then d.Transparency = 1 table.insert(o, "hid " .. d:GetFullName()) end
end
return table.concat(o, "\n")
