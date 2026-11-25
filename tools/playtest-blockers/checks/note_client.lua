-- note_client (playtest-blockers, Client, Play, run_live.py ... Client): at locker 113 with New Kid on the note, the
-- note's "Read note" prompt is the one E reaches: it's on, and every other E prompt within 3 studs is off for us.
local Loc = workspace.School.Quests.HallwayProps.Locker113
local Q = Loc:FindFirstChild(`QuestPrompt`)
if not (Q and Q.Enabled) then return `FAIL the note's prompt is off` end
local On, Off = {}, {}
for _, Pr in workspace:GetDescendants() do
	if Pr:IsA(`ProximityPrompt`) and Pr ~= Q and Pr.KeyboardKeyCode == Q.KeyboardKeyCode then
		local Par = Pr.Parent
		local Pos = if Par and Par:IsA(`BasePart`) then Par.Position elseif Par and Par:IsA(`Attachment`) then Par.WorldPosition else nil
		if Pos and (Pos - Loc.Position).Magnitude <= 3 then
			table.insert(if Pr.Enabled then On else Off, Par.Name .. `:` .. Pr.ActionText)
		end
	end
end
if #On > 0 then return `FAIL still on next to the note: {table.concat(On, `, `)}` end
return `PASS "Read note" on; muted next to it: {table.concat(Off, `, `)}`
