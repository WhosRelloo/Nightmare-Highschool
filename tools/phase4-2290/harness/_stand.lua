local WHERE = "stand"
local Stand = workspace:FindFirstChild("NHConcession")
local S = Stand and Stand:GetPivot().Position
local At
if WHERE == "stand" then
	At = S + Vector3.new(0, 3, 10)
else
	local best, bd
	for _, b in workspace.Regions:GetChildren() do
		if b:IsA("BasePart") then local d = (b.Position - S).Magnitude if not bd or d > bd then best, bd = b, d end end
	end
	At = best.Position + Vector3.new(0, 3, 0)
	WHERE = best.Name .. string.format(" %.0f studs from the stand", bd)
end
P.Character:PivotTo(CFrame.new(At))
return "at " .. WHERE
