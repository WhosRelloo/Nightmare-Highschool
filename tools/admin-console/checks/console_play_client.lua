local P = game.Players.LocalPlayer
local B = P.PlayerGui:WaitForChild("NHQuietProbe", 10)
if not B then return "FAIL no probe" end
local Fails = {}
local function Eq(Got, Want, What) if Got ~= Want then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end
Eq(B:Invoke("Console", "Open"), true, "opens")
task.wait(1)
local G = P.PlayerGui:FindFirstChild("NHStaffConsole")
Eq(G and G.Enabled, true, "gui on")
local I = B:Invoke("Console", "Info")
Eq(I.Level, 3, "studio level") Eq(I.Side, "Moderate", "start side") Eq(I.Section, "Student", "start section")
Eq(#I.Cards, 13, "student cards (12 + Stop spectating)")
Eq(B:Invoke("Console", "Side", "Test"), "Test", "test side")
for _, Sec in { "Character", "Progress", "School", "Story", "World", "Spawns", "Self" } do
	Eq(B:Invoke("Console", "Section", Sec), Sec, "section " .. Sec)
	task.wait(0.3)
	local Cards = B:Invoke("Console", "Info").Cards
	if #Cards == 0 then table.insert(Fails, Sec .. " has no cards") end
	for _, Id in Cards do
		if not G:FindFirstChild("Card_" .. Id, true) then table.insert(Fails, "no Card_" .. Id .. " drawn in " .. Sec) end
	end
end
local R = B:Invoke("Console", "Search", "tp")
Eq(R[1], "Goto", "tp finds Go to")
-- every text label at 20+ px
for _, L in G:GetDescendants() do
	if (L:IsA("TextLabel") or L:IsA("TextButton") or L:IsA("TextBox")) and L.Text ~= "" and L.TextSize < 20 then
		table.insert(Fails, "small text " .. L:GetFullName() .. " " .. L.TextSize)
	end
end
if #Fails > 0 then return "FAIL " .. #Fails .. "\n" .. table.concat(Fails, "\n") end
return "PASS console_play_client"
