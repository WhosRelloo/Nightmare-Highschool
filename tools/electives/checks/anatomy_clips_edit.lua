-- anatomy_clips_edit (Task 9 step 3): the nine seated R6 clips exist, each has a Contact marker, the Clips map points at
-- real clips, and each registers with KeyframeSequenceProvider (how the bench plays them until they are published).
local F = game.ReplicatedStorage:FindFirstChild("AnatomyClips")
assert(F and F:FindFirstChild("Animations"), "FAIL no AnatomyClips.Animations")
local KSP = game:GetService("KeyframeSequenceProvider")
local fails, n = {}, 0
for _, name in { "BenchIdle", "Unwind", "Trace", "Pry", "Lift", "Recoil", "Loupe", "Write", "Done" } do
	local S = F.Animations:FindFirstChild("Anat" .. name)
	if not S then table.insert(fails, "missing " .. name) continue end
	local contact = false
	for _, K in S:GetKeyframes() do for _, M in K:GetMarkers() do if M.Name == "Contact" then contact = true end end end
	if not contact then table.insert(fails, name .. " has no Contact") end
	local ok, id = pcall(function() return KSP:RegisterKeyframeSequence(S) end)
	if not (ok and type(id) == "string" and #id > 0) then table.insert(fails, name .. " register " .. tostring(id)) end
	n += 1
end
local Map = require(F.Clips)
for step, clip in Map do if not F.Animations:FindFirstChild(clip) then table.insert(fails, "map " .. step .. " -> " .. clip) end end
for _, Sp in require(game.ReplicatedStorage.Config.Anatomy).Species do
	for _, St in Sp.Steps do if not Map[St.Id] then table.insert(fails, "no clip for step " .. St.Id) end end
end
if #fails > 0 then return "FAIL anatomy_clips_edit: " .. table.concat(fails, "; ") end
return "PASS anatomy_clips_edit (" .. n .. " clips)"
