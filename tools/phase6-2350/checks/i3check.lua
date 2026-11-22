-- i3check (2.35.0, task 9 fix round 1, I3): a NON-seamless cut (Collected) hides every body on screen and ShowLive restores them;
-- it must not write a stale value over Controllers.Hometown's own hide / release. Client VM, Play, ~15 s.
-- Needs: Collected marked Seen (bridge.py CineMark $P '"Collected"' '"Seen"') so Skip works. A probe body (Humanoid, Part,
-- BillboardGui) stands in for another tutorial player; Hometown's HideCharacter (a second copy of the module, stateless)
-- plays the part of its heartbeat. Cases:
--   1 Hometown holds the probe when the cut starts, RELEASES it mid-cut     -> after the cut it is visible (LTM 0, gui on)
--   2 Hometown holds the probe through the whole cut                        -> after the cut it is still hidden
--   3 Nobody but the cut hides it                                           -> after the cut it is back to normal
local Players = game:GetService("Players")
local Player = Players.LocalPlayer
local H = require(Player.PlayerScripts.Controllers.Hometown)
local Remote = game.ReplicatedStorage:WaitForChild("NHCine")
local Out, Pass = {}, true
local function check(Ok, Text) Pass = Pass and Ok table.insert(Out, (Ok and "ok   " or "FAIL ") .. Text) end

local function probe()
	local M = Instance.new("Model"); M.Name = "__I3Probe"
	local Pt = Instance.new("Part"); Pt.Name = "Body"; Pt.Anchored = true; Pt.CanCollide = false; Pt.Position = Vector3.new(0, -500, 0); Pt.Parent = M
	local Bb = Instance.new("BillboardGui"); Bb.Parent = Pt
	Instance.new("Humanoid").Parent = M
	M.Parent = workspace
	return M, Pt, Bb
end
local function playCut()
	local Session
	local Conn = Remote.OnClientEvent:Connect(function(M) if typeof(M) == "table" and M.Kind == "Play" then Session = M.Session end end)
	Remote:FireServer({ Kind = "Replay"; Id = "Collected" })
	local T0 = os.clock()
	repeat task.wait(0.05) until Session or os.clock() - T0 > 5
	Conn:Disconnect()
	task.wait(1.5) -- HideLive has run
	return Session
end
local function endCut(Session) Remote:FireServer({ Kind = "Skip"; Session = Session }) task.wait(3) end

for Case = 1, 3 do
	local M, Pt, Bb = probe()
	if Case <= 2 then M:SetAttribute("NHHiddenLocal", true); H.HideCharacter(M, true) end
	local Session = playCut()
	check(Session ~= nil, Case .. " cut started")
	check(Pt.LocalTransparencyModifier == 1 and Bb.Enabled == false, Case .. " hidden during the cut")
	if Case == 1 then M:SetAttribute("NHHiddenLocal", false); H.HideCharacter(M, false) end
	endCut(Session)
	if Case == 1 then check(Pt.LocalTransparencyModifier == 0 and Bb.Enabled == true, "1 released mid-cut: visible after the cut (LTM " .. Pt.LocalTransparencyModifier .. ", gui " .. tostring(Bb.Enabled) .. ")")
	elseif Case == 2 then check(Pt.LocalTransparencyModifier == 1 and Bb.Enabled == false, "2 still held: still hidden after the cut")
	else check(Pt.LocalTransparencyModifier == 0 and Bb.Enabled == true, "3 only the cut hid it: back to normal") end
	H.HideCharacter(M, false)
	M:Destroy()
end
H.Stop()
return (Pass and "PASS" or "FAIL") .. "\n" .. table.concat(Out, "\n")
