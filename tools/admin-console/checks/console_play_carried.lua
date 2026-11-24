-- Client, Play (run with run_live.py ... Client: a LocalScript in the game's own client VM, so it reaches the running
-- StaffConsole controller). Task 7 review items, logic side: the phone sinks take taps in the rail's and the
-- context's gaps (hit-tested with PlayerGui:GetGuiObjectsAtPosition, the phone layout from Kit's Studio preview
-- attributes), the small-text rule skips only empty-text sinks, and a departed pick is cleared on the next status tick.
local RS = game:GetService("ReplicatedStorage")
local GuiService = game:GetService("GuiService")
local P = game.Players.LocalPlayer
local PG = P.PlayerGui
local B = PG:WaitForChild("NHQuietProbe", 10)
local Shell = require(P.PlayerScripts.Controllers.Gui.StaffConsole)
local Kit = require(RS.UI.Components)
local Fails, Notes = {}, {}
local function fail(T) table.insert(Fails, T) end
B:Invoke("Console", "Open")
B:Invoke("Console", "Side", "Moderate")
B:Invoke("Console", "Section", "Student")
local G = PG.NHStaffConsole
-- the topmost input-taking object at a point (GetGuiObjectsAtPosition lists the topmost first)
local function topActive(X, Y)
	for _, O in PG:GetGuiObjectsAtPosition(X, Y) do
		if O:IsDescendantOf(G) and O:IsA("GuiObject") and O.Active and O.Visible then return O end
	end
	return nil
end
local function centre(O) return O.AbsolutePosition.X + O.AbsoluteSize.X / 2, O.AbsolutePosition.Y + O.AbsoluteSize.Y / 2 end
local function inside(O, X, Y) local A, S = O.AbsolutePosition, O.AbsoluteSize return X >= A.X and Y >= A.Y and X <= A.X + S.X and Y <= A.Y + S.Y end

-- phone layout
local OldPrev, OldTouch = RS:GetAttribute("NHPhonePreview"), RS:GetAttribute("NHTouchTest")
RS:SetAttribute("NHPhonePreview", Vector2.new(844, 390))
RS:SetAttribute("NHTouchTest", true)
task.wait(0.5)
local ok = pcall(function()
	if not Kit.Phone() then fail("phone preview not a phone") return end
	Shell.Handlers.Redraw()
	task.wait(0.3)
	-- control: a card's Run, with no overlay open, is the topmost thing at its centre
	local Run0 = G.Board.Dyn.Cards:FindFirstChild("Run", true)
	local X0, Y0 = centre(Run0)
	if topActive(X0, Y0) ~= Run0 then fail("control: a card's Run isn't topmost at its own centre (" .. tostring(topActive(X0, Y0)) .. ")") end
	for _, Which in { { "PhoneRail", "RailSink", { "Rows", "StudentSearch" } }, { "PhoneContext", "ContextSink", { "Context" } } } do
		Shell.Handlers[Which[1]]()
		task.wait(0.3)
		-- the 1 s status tick rebuilds the layer, and a layer built this frame has no layout yet (the hit test would see
		-- only the scrim): sample right after a frame in which the layer stayed the same
		local Dyn
		repeat Dyn = G.Board.Dyn task.wait() until G.Board.Dyn == Dyn
		local Sink = Dyn:FindFirstChild(Which[2])
		if not Sink then fail(Which[2] .. " missing") continue end
		if not (Sink:IsA("TextButton") and Sink.Text == "" and Sink.Active and Sink.BackgroundTransparency == 1) then fail(Which[2] .. " isn't a blank active button") end
		-- every card Run under the overlay: whatever is topmost there must be the overlay's (the sink, or a part of it)
		local Under, Leaks = 0, 0
		for _, R in Dyn.Cards:GetDescendants() do
			if R.Name == "Run" and R:IsA("GuiButton") then
				for _, Pt in { { centre(R) }, { R.AbsolutePosition.X + 4, R.AbsolutePosition.Y + 4 }, { R.AbsolutePosition.X + R.AbsoluteSize.X - 4, R.AbsolutePosition.Y + R.AbsoluteSize.Y - 4 } } do
					if inside(Sink, Pt[1], Pt[2]) then
						Under += 1
						local Top = topActive(Pt[1], Pt[2])
						if Top and Top:IsDescendantOf(Dyn.Cards) then Leaks += 1 fail(`{Which[2]}: a tap at {math.floor(Pt[1])},{math.floor(Pt[2])} reaches {Top:GetFullName()}`) end
					end
				end
			end
		end
		-- and a 12 x 12 grid over the whole overlay: the topmost input-taker is always the overlay's own (sink, its
		-- controls, or the board's Close / Students / Details buttons, which sit above it by design)
		local Own = { [Sink] = true }
		local Grid, Out = 0, 0
		for I = 1, 12 do for J = 1, 12 do
			local X = Sink.AbsolutePosition.X + Sink.AbsoluteSize.X * (I - 0.5) / 12
			local Y = Sink.AbsolutePosition.Y + Sink.AbsoluteSize.Y * (J - 0.5) / 12
			local Top = topActive(X, Y)
			Grid += 1
			local Mine = Top == nil or Own[Top] or Top.Name == "Close" or Top.Name == "Students" or Top.Name == "Details"
			if not Mine then
				for _, N in Which[3] do local O = Dyn:FindFirstChild(N) if O and Top:IsDescendantOf(O) or Top == O then Mine = true end end
			end
			if not Mine then
				Out += 1
				if Out <= 2 then
					local L = {}
					for _, O in PG:GetGuiObjectsAtPosition(X, Y) do table.insert(L, O.Name .. (if O.Active then "*" else "")) end
					fail(`{Which[2]}: a tap at {math.floor(X)},{math.floor(Y)} reaches {Top:GetFullName()} (at the point: {table.concat(L, " ")}; sink parent {tostring(Sink.Parent)})`)
				end
			end
		end end
		if Which[2] == "RailSink" and Under == 0 then fail("RailSink: no card Run lies under it (nothing tested)") end
		table.insert(Notes, `{Which[2]}: {Under} card-button points under it, {Leaks} reach a card; {Grid} grid points, {Out} reach past the overlay`)
		-- the small-text rule on the phone layout: non-empty text is 20+; what it skips is empty-text sinks only
		local Skipped = {}
		for _, L in G:GetDescendants() do
			if L:IsA("TextLabel") or L:IsA("TextButton") or L:IsA("TextBox") then
				if L.TextSize < 20 then
					if L.Text ~= "" then fail("small text " .. L:GetFullName() .. " " .. L.TextSize)
					elseif L:IsA("TextBox") then fail("empty TextBox under 20 px: " .. L:GetFullName())
					else Skipped[L.Name] = (Skipped[L.Name] or 0) + 1 end
				end
			end
		end
		local S = {}
		for N, C in Skipped do table.insert(S, N .. " x" .. C) end
		table.sort(S)
		table.insert(Notes, `{Which[1]} open, empty-text buttons under 20 px (skipped): {table.concat(S, ", ")}`)
		Shell.Handlers[Which[1]]() -- close it again
		task.wait(0.3)
	end
end)
RS:SetAttribute("NHPhonePreview", OldPrev)
RS:SetAttribute("NHTouchTest", OldTouch)
task.wait(0.3)
Shell.Handlers.Redraw()
if not ok then fail("phone part errored") end

-- a departed pick: a UserId not in the server's list is dropped on the next status tick (1 s)
B:Invoke("Console", "Pick", 1)
local Picked = B:Invoke("Console", "Info").Selected
task.wait(2.5)
local After = B:Invoke("Console", "Info").Selected
if Picked ~= 1 then fail("pick: got " .. tostring(Picked)) end
if After ~= nil then fail("departed pick kept: " .. tostring(After)) end
table.insert(Notes, `departed pick: picked {tostring(Picked)}, after a status tick {tostring(After)}`)

GuiService.SelectedObject = nil
local Tail = "\n" .. table.concat(Notes, "\n")
if #Fails > 0 then return "FAIL " .. #Fails .. "\n" .. table.concat(Fails, "\n") .. Tail end
return "PASS console_play_carried" .. Tail
