local P = game.Players.LocalPlayer
local B = P.PlayerGui:WaitForChild("NHQuietProbe", 10)
if not B then return "FAIL no probe" end
-- (fix round 3) own start state: a running cutscene is waited out, and the stored staff prefs (Side, Favs) are
-- set to Moderate / none for the run, then put back (server-side PrefsGet / PrefsSet through the console's own remotes)
local RS = game:GetService("ReplicatedStorage")
local F = RS:FindFirstChild("NHAdmin")
local T0 = os.clock()
while workspace:GetAttribute("NHCinePlaying") and os.clock() - T0 < 100 do task.wait(0.5) end
if workspace:GetAttribute("NHCinePlaying") then return "FAIL a cutscene (NHCinePlaying) was still playing after 100 s" end
while not (F and F:GetAttribute("Ready") and F:FindFirstChild("Prefs") and F:FindFirstChild("SavePrefs")) and os.clock() - T0 < 30 do
	task.wait(0.5) F = RS:FindFirstChild("NHAdmin")
end
if not (F and F:FindFirstChild("Prefs") and F:FindFirstChild("SavePrefs")) then return "FAIL no NHAdmin Prefs remotes" end
local Orig = F.Prefs:InvokeServer()
if typeof(Orig) ~= "table" or not Orig.Ok then return "FAIL could not read the stored prefs: " .. tostring(Orig and Orig.Error) end
local OrigFavs, OrigSide = table.clone(Orig.Favs or {}), Orig.Side
F.SavePrefs:InvokeServer({}, "Moderate")
local function Body()
local Fails = {}
local function Eq(Got, Want, What) if Got ~= Want then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end
-- (2026-11-24) the card layout: every option sits inside its card and clear of Run, Run sits inside the card, and no
-- two cards overlap (cards with many options grow taller instead of scrolling them sideways)
local function inside(A: GuiObject, B: GuiObject): boolean
	local a, b = A.AbsolutePosition, B.AbsolutePosition
	return a.X >= b.X - 0.5 and a.Y >= b.Y - 0.5 and a.X + A.AbsoluteSize.X <= b.X + B.AbsoluteSize.X + 0.5
		and a.Y + A.AbsoluteSize.Y <= b.Y + B.AbsoluteSize.Y + 0.5
end
local function overlap(A: GuiObject, B: GuiObject): boolean
	local a, b = A.AbsolutePosition, B.AbsolutePosition
	return a.X < b.X + B.AbsoluteSize.X - 1 and b.X < a.X + A.AbsoluteSize.X - 1
		and a.Y < b.Y + B.AbsoluteSize.Y - 1 and b.Y < a.Y + A.AbsoluteSize.Y - 1
end
local Tall = {}
local function layout(G: Instance, Where: string)
	local All = {}
	for _, C in G:GetDescendants() do
		if C:IsA("GuiObject") and string.sub(C.Name, 1, 5) == "Card_" and C:FindFirstChild("Options") then
			table.insert(All, C)
			if C.Size.Y.Offset > 168 then Tall[string.sub(C.Name, 6)] = C.Size.Y.Offset end
			local Run = C:FindFirstChild("Run") :: GuiObject?
			if Run and not inside(Run, C) then table.insert(Fails, Where .. ": Run spills out of " .. C.Name) end
			for _, O in C.Options:GetChildren() do
				if O:IsA("GuiObject") then
					if not inside(O, C) then table.insert(Fails, Where .. ": " .. O.Name .. " spills out of " .. C.Name) end
					if Run and overlap(O, Run) then table.insert(Fails, Where .. ": " .. O.Name .. " under Run on " .. C.Name) end
				end
			end
		end
	end
	for I = 1, #All do for J = I + 1, #All do
		if overlap(All[I], All[J]) then table.insert(Fails, Where .. ": " .. All[I].Name .. " overlaps " .. All[J].Name) end
	end end
end
Eq(B:Invoke("Console", "Open"), true, "opens")
task.wait(1)
local G = P.PlayerGui:FindFirstChild("NHStaffConsole")
Eq(G and G.Enabled, true, "gui on")
if B:Invoke("Console", "Info").Side ~= "Moderate" then B:Invoke("Console", "Side", "Moderate") task.wait(0.3) end
local I = B:Invoke("Console", "Info")
Eq(I.Level, 3, "studio level") Eq(I.Side, "Moderate", "start side") Eq(I.Section, "Student", "start section")
Eq(#I.Cards, 14, "student cards (13 + Stop spectating)")
layout(G, "Student")
Eq(B:Invoke("Console", "Section", "Server"), "Server", "section Server")
task.wait(0.3)
layout(G, "Server")
Eq(B:Invoke("Console", "Side", "Test"), "Test", "test side")
for _, Sec in { "Character", "Progress", "School", "Story", "World", "Spawns", "Self" } do
	Eq(B:Invoke("Console", "Section", Sec), Sec, "section " .. Sec)
	task.wait(0.3)
	local Cards = B:Invoke("Console", "Info").Cards
	if #Cards == 0 then table.insert(Fails, Sec .. " has no cards") end
	for _, Id in Cards do
		if not G:FindFirstChild("Card_" .. Id, true) then table.insert(Fails, "no Card_" .. Id .. " drawn in " .. Sec) end
	end
	layout(G, Sec)
end
-- the three cards that used to scroll their options grow instead
for _, Id in { "Ban", "Mute", "RemoveRecordEntry" } do
	if not Tall[Id] then table.insert(Fails, Id .. " card is not the tall layout") end
end
local R = B:Invoke("Console", "Search", "tp")
Eq(R[1], "Goto", "tp finds Go to")
-- (1b) the Log section draws (rows may be empty on a fresh day; the chrome is always there)
local L = B:Invoke("Console", "Log", { Day = 0; Query = ""; Chip = "All"; Page = 1 })
Eq(L.Ok, true, "log reads today")
task.wait(0.5)
for _, N in { "LogDays", "Day_0", "Day_6", "LogSearch", "Chip_All", "Chip_Refused", "LogRows", "LogPrev", "LogNext", "LogPage" } do
	if not G:FindFirstChild(N, true) then table.insert(Fails, "Log section: no " .. N) end
end
-- every text label at 20+ px
for _, L in G:GetDescendants() do
	if (L:IsA("TextLabel") or L:IsA("TextButton") or L:IsA("TextBox")) and L.Text ~= "" and L.TextSize < 20 then
		table.insert(Fails, "small text " .. L:GetFullName() .. " " .. L.TextSize)
	end
end
if #Fails > 0 then return "FAIL " .. #Fails .. "\n" .. table.concat(Fails, "\n") end
return "PASS console_play_client"
end
local Ok, Res = pcall(Body)
-- put the prefs back (the console's own client state goes to the stored side first, then the stored record is written last)
pcall(function()
	if OrigSide then B:Invoke("Console", "Side", OrigSide) end
	F.SavePrefs:InvokeServer(OrigFavs, OrigSide)
end)
if not Ok then return "FAIL error: " .. tostring(Res) end
return Res
