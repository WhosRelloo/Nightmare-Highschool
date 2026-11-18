-- (2.28) staff NpcPost parts (docs/superpowers/plans/2026-11-18-staff-school-day.md Task 1). Re-runnable: replaces the folder.
local Quests = workspace.School.Quests
local Old = Quests:FindFirstChild(`Staff`) if Old then Old:Destroy() end
local F = Instance.new(`Folder`) F.Name = `Staff` F.Parent = Quests
local function Post(Key: string, Pos: Vector3, Look: Vector3)
	local P = Instance.new(`Part`)
	P.Name = Key P.Anchored = true P.CanCollide = false P.CanQuery = false P.CanTouch = false P.Transparency = 1
	P.Size = Vector3.new(2, 1, 2)
	P.CFrame = CFrame.lookAt(Pos, Vector3.new(Look.X, Pos.Y, Look.Z))
	P:SetAttribute(`NpcPost`, Key)
	P.Parent = F
end
local Chairs = workspace.School.NHProps
local Out = {}
for Key, Room in { Sallow = `R102`, [`Hale@R103`] = `R103`, Pryce = `R104`, Whitlock = `R105` } do
	local Desk = workspace.School[Room].TeacherDesk
	-- the chairs' centre in this room decides which side of the desk faces the class
	local CF, Size = workspace.School[Room]:GetBoundingBox()
	local Sum, N = Vector3.zero, 0
	for _, C in Chairs:GetChildren() do
		if C.Name == `StudentChair` and C:IsA(`Model`) then
			local L = CF:PointToObjectSpace(C:GetPivot().Position)
			if math.abs(L.X) < Size.X / 2 and math.abs(L.Z) < Size.Z / 2 then Sum += C:GetPivot().Position N += 1 end
		end
	end
	local Class = if N > 0 then Sum / N else CF.Position
	local Away = ((Desk.Position - Class) * Vector3.new(1, 0, 1)).Unit
	local At = Desk.Position + Away * 2.5 + Vector3.new(0, 2, 0)
	Post(Key, At, Class)
	table.insert(Out, string.format("%s %s (%.1f, %.1f, %.1f) chairs %d", Key, Room, At.X, At.Y, At.Z, N))
end
local SR = workspace:FindFirstChild(`Area_StaffRoom`, true)
for I, Key in { `Hale@Staff`, `Sallow@Staff`, `Pryce@Staff`, `Whitlock@Staff` } do
	local X = (I - 2.5) * 4
	local At = SR.Position + Vector3.new(X, -SR.Size.Y / 2 + 3, 4)
	Post(Key, At, SR.Position)
	table.insert(Out, string.format("%s (%.1f, %.1f, %.1f)", Key, At.X, At.Y, At.Z))
end
local Exit = workspace:FindFirstChild(`Area_RecordsExit`, true)
local At = Exit.Position + Vector3.new(5, 0, 2)
Post(`Ashgrave`, At, Exit.Position + Vector3.new(5, 0, 12))
table.insert(Out, string.format("Ashgrave (%.1f, %.1f, %.1f)", At.X, At.Y, At.Z))
return #F:GetChildren() .. " posts\n" .. table.concat(Out, "\n")
