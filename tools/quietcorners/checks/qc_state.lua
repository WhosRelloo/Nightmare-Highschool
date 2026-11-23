local P = game.Players.LocalPlayer
local PG = P:WaitForChild("PlayerGui")
local Probe = PG:FindFirstChild("NHQuietProbe")
if not Probe then return "FAIL no NHQuietProbe" end
local Fails, Notes = {}, {}
local function Ok(C, W) if not C then table.insert(Fails, W) end end
local function Near(A, B) return typeof(A) == "number" and math.abs(A - B) < 0.01 end
local function G() return Probe:Invoke("Get") end
local ModeWas = P:GetAttribute("NHHudMode")
local S = G()
for _, N in { "TopLeft", "Compass", "Vitals" } do Ok(S.Groups[N] ~= nil, "cluster not adopted: " .. N) end
Ok(PG.ClockHud:FindFirstChild("QcFade") == nil and PG.QuestTracker:FindFirstChild("QcFade") == nil, "the Bell Tower must not be adopted (ruling 2)")
Ok(PG.KitHud:FindFirstChild("Downed") and PG.KitHud.Downed.Parent == PG.KitHud, "DOWNED must stay outside the fade")
-- Ghost / Vanish / Always in calm
P:SetAttribute("NHHudMode", "Ghost") Probe:Invoke("Force", nil) Probe:Invoke("Idle") task.wait(0.8) S = G()
Ok(S.State == "Calm", "calm: " .. tostring(S.State)) Ok(P:GetAttribute("NHHudState") == "Calm", "NHHudState attribute")
for _, N in { "TopLeft", "Compass", "Vitals" } do Ok(Near(S.Targets[N], 0.65), "ghost " .. N .. " " .. tostring(S.Targets[N])) end
P:SetAttribute("NHHudMode", "Vanish") task.wait(0.4) S = G() Ok(S.Targets.Compass == 1, "vanish compass")
local Thread = PG.KitHud:FindFirstChild("QcThread", true) Ok(Thread and Thread.Visible, "Vanish health thread")
P:SetAttribute("NHHudMode", "Always") task.wait(0.4) S = G() Ok(S.Targets.Compass == 0, "always compass")
-- combat focus, and its end 4 s after the last hit
P:SetAttribute("NHHudMode", "Ghost") Probe:Invoke("Poke", "Hit") task.wait(0.4) S = G()
Ok(S.State == "Combat", "combat: " .. tostring(S.State)) Ok(S.Targets.Vitals == 0 and Near(S.Targets.TopLeft, 0.65) and Near(S.Targets.Compass, 0.65), "combat targets")
task.wait(4.6) S = G() Ok(S.State ~= "Combat", "combat still on 4.6 s after the hit")
-- dialogue and menu hide all three
P:SetAttribute("InDialogue", true) task.wait(0.4) S = G() Ok(S.State == "Dialogue" and S.Targets.Compass == 1 and S.Targets.TopLeft == 1, "dialogue")
P:SetAttribute("InDialogue", nil)
P:SetAttribute("NHMenuOpen", true) task.wait(0.4) S = G() Ok(S.State == "Menu" and S.Targets.Vitals == 1, "menu") P:SetAttribute("NHMenuOpen", nil)
-- a cut: the real NHCineUI if built, else forced; leaving it lands on Calm, not Active
local Cine = PG:FindFirstChild("NHCineUI")
if Cine and not Cine.Enabled then Cine.Enabled = true task.wait(0.4) S = G() Ok(S.State == "Cut", "cut via NHCineUI") Cine.Enabled = false
else Probe:Invoke("Force", "Cut") task.wait(0.2) Probe:Invoke("Force", nil) table.insert(Notes, "cut forced (NHCineUI not built yet)") end
task.wait(0.4) S = G() Ok(S.State == "Calm", "after a cut: " .. tostring(S.State) .. " (spec: calm, not full)")
-- waking one cluster
Probe:Invoke("Wake", "Compass") task.wait(0.8) S = G()
Ok(S.Targets.Compass == 0 and Near(S.Targets.TopLeft, 0.65), "wake only the compass")
local Fade = PG.NHCompass:FindFirstChild("QcFade") Ok(Fade and Fade:IsA("CanvasGroup") and Fade.GroupTransparency < 0.05, "the compass group follows")
-- Settings: HudMode is a real setting
local Settings = require(game.ReplicatedStorage.UI.Settings)
Ok(Settings.Choices and Settings.Choices.HudMode and #Settings.Choices.HudMode == 3, "Settings.Choices.HudMode")
P:SetAttribute("NHHudMode", ModeWas)
return (#Fails == 0 and "PASS qc_state" or ("FAIL\n" .. table.concat(Fails, "\n"))) .. "\n" .. table.concat(Notes, "\n")
