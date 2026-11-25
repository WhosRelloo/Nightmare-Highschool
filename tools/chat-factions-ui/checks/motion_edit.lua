-- motion_edit (chat-factions-ui, Edit): UI.Motion has every helper, and with reduced motion every helper leaves the end
-- state at once (no tween, no loop). The animated paths are checked in Play (motion_play.lua).
local M = game.ReplicatedStorage.UI:FindFirstChild("Motion")
if not M then return "FAIL no UI.Motion" end
local C = M:Clone()
C.Parent = M.Parent -- it requires script.Parent.Components
local Okr, Motion = pcall(require, C)
C:Destroy()
if not Okr then return "FAIL require: " .. tostring(Motion) end
if type(Motion) ~= "table" then return "FAIL UI.Motion returns " .. typeof(Motion) end
local Fails = {}
local function Ok(Cond, What) if not Cond then table.insert(Fails, What) end end
for _, Name in { "Reduced", "Play", "SmokeIn", "Wake", "Candle", "Glint", "Stop", "ActiveCount", "Rise", "Fill", "Pips", "Open", "Close" } do
	Ok(type(Motion[Name]) == "function", "missing " .. Name)
end
if #Fails > 0 then return "FAIL " .. table.concat(Fails, "; ") end
Motion.ForceReduced = true
Ok(Motion.Reduced() == true, "ForceReduced ignored")
local G = Instance.new("ScreenGui")
local L = Instance.new("TextLabel")
L.TextTransparency = 0.1
L.Position = UDim2.fromOffset(15, 0)
L.Parent = G
Motion.SmokeIn(L)
Ok(math.abs(L.TextTransparency - 0.1) < 0.001 and L.Position == UDim2.fromOffset(15, 0), "SmokeIn (reduced) changed the label")
local F = Instance.new("Frame")
F.BackgroundTransparency = 0.5
F.Parent = G
local Items = { { F, { BackgroundTransparency = 0 }, { BackgroundTransparency = 1 } } }
Motion.Wake(Items, false)
Ok(F.BackgroundTransparency == 1, "Wake quiet (reduced) " .. F.BackgroundTransparency)
Motion.Wake(Items, true)
Ok(F.BackgroundTransparency == 0, "Wake awake (reduced) " .. F.BackgroundTransparency)
local Base = Motion.ActiveCount()
local Flame = Instance.new("ImageLabel")
Flame.Parent = G
Motion.Candle(Flame, nil)
local S = Instance.new("UIStroke")
S.Parent = F
Motion.Glint(S, "Color", Color3.new(1, 0, 0), Color3.new(0, 0, 1), nil)
Ok(S.Color == Color3.new(1, 0, 0), "Glint (reduced) didn't set A")
Ok(Motion.ActiveCount() == Base, "Candle or Glint joined the loop under reduced motion")
local Bar = Instance.new("Frame")
local Fill = Instance.new("Frame")
Fill.Name = "Fill"
Fill.Size = UDim2.new(0.4, -4, 1, -4)
Fill.Parent = Bar
Bar.Parent = G
Motion.Fill(Bar, 0)
Ok(Fill.Size == UDim2.new(0.4, -4, 1, -4), "Fill (reduced) changed the size")
local Pips = {}
for I = 1, 5 do
	local P = Instance.new("Frame")
	P.Parent = G
	Pips[I] = P
end
Motion.Pips(Pips, 3, Color3.new(1, 1, 0), Color3.new(0, 0, 0), 0)
Ok(Pips[3].BackgroundColor3 == Color3.new(1, 1, 0) and Pips[4].BackgroundColor3 == Color3.new(0, 0, 0), "Pips (reduced)")
local Panel = Instance.new("Frame")
Panel.Visible = false
Panel.Parent = G
Motion.Open(Panel)
Ok(Panel.Visible, "Open (reduced) left it hidden")
Motion.Close(Panel)
Ok(not Panel.Visible, "Close (reduced) left it shown")
Motion.ForceReduced = nil
G:Destroy()
return if #Fails == 0 then "PASS motion_edit" else "FAIL " .. table.concat(Fails, "; ")
