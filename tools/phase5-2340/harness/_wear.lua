local P = game.Players:GetPlayers()[1]
local App = require(game.ReplicatedStorage.UI.Appearance)
local Data = require(game.ServerScriptService.Services.Player.Data)
local Prof = Data.GetProfile(P)
local L = App.Decode and App.Decode(Prof.Appearance) or App.Sanitize(Prof.Appearance)
L.UseAvatar = false
L.Uniform = App.IndexOf(App.Uniforms, "path-worn-blazer")
L.Acc = "path-academic-pin,path-silver-sigil,path-knuckle-wraps"
local ok, err = pcall(App.ApplyTo, P.Character, L)
task.wait(2)
local o = { "apply " .. tostring(ok) .. " " .. tostring(err), "uniform idx " .. tostring(L.Uniform) }
local sh = P.Character:FindFirstChildOfClass("Shirt") table.insert(o, "shirt " .. (sh and sh.ShirtTemplate or "none"))
for _, d in P.Character:GetDescendants() do if d:IsA("MeshPart") and (d.Name:find("Wrap") or d.Name:find("Sigil") or d.Name:find("AcademicPin")) then table.insert(o, d.Name .. " " .. tostring(d.Parent and d.Parent.Name)) end end
P.Character:PivotTo(CFrame.new(120, 5, 50))
return table.concat(o, "\n")
