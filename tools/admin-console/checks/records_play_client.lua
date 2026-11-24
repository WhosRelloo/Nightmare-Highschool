-- records_play_client.lua: Client, Play (through the NHQuietProbe probe). Run after records_play_a in the same round, or
-- after the restart (Restart = true reads back the saved side and favourite from the real-input step). The Log section
-- (day, search, chips, paging, a row opens its target's history) and the history timeline with its remove buttons.
local Restart = false -- Task 6 sets it to true for the round after the restart
local P = game.Players.LocalPlayer
local B = P.PlayerGui:WaitForChild("NHQuietProbe", 10)
if not B then return "FAIL no probe" end
local Fails = {}
local function Eq(Got, Want, What) if Got ~= Want then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end
Eq(B:Invoke("Console", "Open"), true, "opens")
task.wait(2)
local G = P.PlayerGui:FindFirstChild("NHStaffConsole")
if Restart then
	-- before anything changes the side: what the real-input round saved
	local I = B:Invoke("Console", "Info")
	Eq(I.Side, "Test", "opens on the saved side")
	local Pr = B:Invoke("Console", "Prefs")
	Eq(Pr.Ok, true, "prefs read")
	Eq(table.find(Pr.Favs, "Warn") ~= nil, true, "the saved favourite came back")
end
-- the Log section
local L = B:Invoke("Console", "Log", { Day = 0; Query = ""; Chip = "All"; Page = 1 })
Eq(L.Ok, true, "today's log reads")
if L.Ok then
	if L.Total < 1 then table.insert(Fails, "today's log is empty after records_play_a") end
	if #L.Rows > 50 then table.insert(Fails, "more than 50 rows on a page") end
	if L.Total > 50 then
		local L2 = B:Invoke("Console", "Log", { Page = 2 })
		Eq(L2.Page, 2, "page 2") if L2.Rows[1] and L.Rows[1] and L2.Rows[1].Text == L.Rows[1].Text then table.insert(Fails, "page 2 shows page 1") end
		B:Invoke("Console", "Log", { Page = 1 })
	end
end
local Rf = B:Invoke("Console", "Log", { Chip = "Refused"; Query = ""; Page = 1 })
for _, R in Rf.Rows or {} do if R.Ok then table.insert(Fails, "a run row under Refused: " .. R.Text) end end
local Rm = B:Invoke("Console", "Log", { Chip = "All"; Query = "RemoveRecordEntry"; Page = 1 })
if not (Rm.Ok and Rm.Total >= 1) then table.insert(Fails, "search finds no RemoveRecordEntry row") end
local Yd = B:Invoke("Console", "Log", { Day = 1; Query = ""; Page = 1 })
Eq(Yd.Ok, true, "yesterday reads (empty is fine, unavailable is not)")
B:Invoke("Console", "Log", { Day = 0; Query = "RemoveRecordEntry"; Page = 1 })
-- a row opens its target's history
Eq(B:Invoke("Console", "OpenRow", 1), P.UserId, "the row picked its target")
local H = B:Invoke("Console", "History", P.UserId)
Eq(H.Ok, true, "history reads")
if H.Ok then
	if not string.find(H.Summary or "", "note", 1, true) then table.insert(Fails, "summary has no note: " .. tostring(H.Summary)) end
	if not string.find(H.Summary or "", "muted until", 1, true) then table.insert(Fails, "summary has no open mute: " .. tostring(H.Summary)) end
	if H.Count < 1 then table.insert(Fails, "no timeline entries") end
end
task.wait(0.5)
local E1 = G and G:FindFirstChild("Entry_1", true)
if not E1 then table.insert(Fails, "no timeline entry drawn") elseif not E1:FindFirstChild("Remove") then table.insert(Fails, "no remove button at level 3") end
-- text at 20 px or more
for _, X in G:GetDescendants() do
	if (X:IsA("TextLabel") or X:IsA("TextButton") or X:IsA("TextBox")) and X.Text ~= "" and X.TextSize < 20 then
		table.insert(Fails, "small text " .. X:GetFullName() .. " " .. X.TextSize)
	end
end
if #Fails > 0 then return "FAIL " .. #Fails .. "\n" .. table.concat(Fails, "\n") end
return "PASS records_play_client" .. (if Restart then " (after restart)" else "")
