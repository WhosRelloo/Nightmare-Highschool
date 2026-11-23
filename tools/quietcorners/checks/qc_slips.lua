local P = game.Players.LocalPlayer
local PG = P.PlayerGui
local Probe = PG:FindFirstChild("NHQuietProbe")
if not Probe then return "FAIL no NHQuietProbe" end
local Fails = {}
local function Ok(C, W) if not C then table.insert(Fails, W) end end
Probe:Invoke("Force", "Active")
for I = 1, 4 do Probe:Invoke("Slip", { Title = "Slip " .. I; Text = "A detail line that is long enough to need shortening at a word boundary, surely"; Kind = "Info"; Duration = 30 }) end
task.wait(0.6)
local S = Probe:Invoke("Slips")
Ok(#S.Shown == 3, "max 3 shown, got " .. #S.Shown) Ok(S.Shown[1] == "Slip 4", "newest on top: " .. tostring(S.Shown[1]))
local Vp = workspace.CurrentCamera.ViewportSize
Ok(S.X < Vp.X * 0.25 and S.Y < Vp.Y * 0.3, "top-left")
for _, L in PG.Notifications:GetDescendants() do
	if L:IsA("TextLabel") and L.Text ~= "" and L.Visible then Ok(L.TextSize >= 20 and L.TextFits, L.Name .. " size/fit " .. L.TextSize) end
	if L:IsA("ImageLabel") or L:IsA("ImageButton") then Ok(L.Image ~= require(game.ReplicatedStorage.UI.Theme).Images.Seal, "the Seal is drawn") end
end
-- combat queues; danger breaks through; the queue flushes after
Probe:Invoke("Force", "Combat")
Probe:Invoke("Slip", { Title = "Queued A"; Text = "x"; Duration = 30 }) Probe:Invoke("Slip", { Title = "Queued B"; Text = "x"; Duration = 30 })
Probe:Invoke("Slip", { Title = "Danger"; Text = "x"; Kind = "Bad"; Duration = 30 })
task.wait(0.5) S = Probe:Invoke("Slips")
Ok(table.find(S.Shown, "Danger") ~= nil, "danger shown in combat") Ok(table.find(S.Shown, "Queued A") == nil, "event queued in combat")
Ok(S.Stub == "2 waiting", "stub: " .. tostring(S.Stub))
Probe:Invoke("Force", nil) Probe:Invoke("Force", "Active") task.wait(1.2) S = Probe:Invoke("Slips")
Ok(table.find(S.Shown, "Queued B") ~= nil, "queued slips show after combat")
Probe:Invoke("Force", nil)
return #Fails == 0 and "PASS qc_slips" or ("FAIL\n" .. table.concat(Fails, "\n"))
