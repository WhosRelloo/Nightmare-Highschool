-- phase6-strafes T3: bleacher seat "props" (spec §7.1) in NH Combat Test, Edit mode. Idempotent.
-- One Model BleacherSeat_<n> per sitting place: an invisible Base tile on the step top, its pivot facing the court.
-- Features.Seats reads SeatHeight (above the model's base); Features.PlayerSeats gives each a Seat + "Sit" prompt;
-- Schedules' Watch job seats students on them. Numbers from build/bleachers_survey.json (S1, read-only).
if game.PlaceId ~= 98950102230473 then return "REFUSED: not NH Combat Test (" .. game.PlaceId .. ")" end
local CS = game:GetService("CollectionService")
local Sports = workspace:FindFirstChild("Sports")
if not Sports then return "FAIL no workspace.Sports" end

-- { Venue, centre X, step Z list (front to back), step top Y list, facing (+1 = +Z, -1 = -Z), seats per row, rows used }
local BANKS = {
	{ "Gymnasium", 66, { 120.5, 117.9 }, { 2.8, 4.3 }, 1, 8 },
	{ "Gymnasium", 124, { 120.5, 117.9 }, { 2.8, 4.3 }, 1, 8 },
	{ "Gymnasium", 95, { 180.9, 183.5 }, { 2.8, 4.3 }, -1, 8 },
	{ "Field", -94, { -197.3, -199.9 }, { 2.4, 3.9 }, 1, 8 },
}
local GAP = 2.2
local Out, N = {}, 0
for _, B in BANKS do
	local Venue = Sports:FindFirstChild(B[1])
	if not Venue then table.insert(Out, "no venue " .. B[1]) continue end
	local Folder = Venue:FindFirstChild("NHBleacherSeats")
	if not Folder then
		Folder = Instance.new("Folder")
		Folder.Name = "NHBleacherSeats"
		Folder.Parent = Venue
	end
	for Row = 1, #B[3] do
		for I = 1, B[6] do
			local X = B[2] + (I - (B[6] + 1) / 2) * GAP
			local Z, Y = B[3][Row], B[4][Row]
			local Key = string.format("%s_%d_%d_%d", B[1], B[2], Row, I)
			if Folder:FindFirstChild("BleacherSeat_" .. Key) then continue end
			local M = Instance.new("Model")
			M.Name = "BleacherSeat_" .. Key
			local P = Instance.new("Part")
			P.Name = "Base"
			P.Size = Vector3.new(1.6, 0.1, 1.6)
			P.Anchored, P.CanCollide, P.CanQuery, P.CanTouch = true, false, false, false
			P.Transparency = 1
			local Pos = Vector3.new(X, Y + 0.05, Z)
			P.CFrame = CFrame.lookAt(Pos, Pos + Vector3.new(0, 0, B[5]))
			P.Parent = M
			M.PrimaryPart = P
			M:SetAttribute("SeatHeight", 0.1)
			M:SetAttribute("Venue", B[1])
			M.Parent = Folder
			CS:AddTag(M, "NHBleacherSeat")
			N += 1
		end
	end
end
return string.format("bleacher seats added: %d %s", N, table.concat(Out, " "))
