local P = game.Players:GetPlayers()[1]
local App = require(game.ReplicatedStorage.UI.Appearance)
local Prof = require(game.ServerScriptService.Services.Player.Data).GetProfile(P)
local L = App.Decode and App.Decode(Prof.Appearance) or App.Sanitize(Prof.Appearance)
L.UseAvatar = false
L.Uniform = App.IndexOf(App.Uniforms, "path-rolled-sleeves")
L.Acc = ""
local ok, e = pcall(App.ApplyTo, P.Character, L) if not ok then return "ERR " .. tostring(e) end
task.wait(0.3)
for _, d in P.Character:GetDescendants() do if d:IsA("BasePart") and d.Parent and d.Parent.Name == "NHCape" then d.Transparency = 1 end end
local s = P.Character:FindFirstChildOfClass("Shirt") return tostring(L.Uniform) .. " " .. (s and s.ShirtTemplate or "noshirt")
