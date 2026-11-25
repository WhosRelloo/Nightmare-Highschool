-- motion_play (chat-factions-ui, Client, Play): UI.Motion's animated paths reach their end states, an interrupted fade
-- is replaced, a panel reopened mid-close stays open, and the shared loop flickers a candle and lets it go on destroy.
local Motion = require(game.ReplicatedStorage.UI.Motion)
local P = game.Players.LocalPlayer
local Fails = {}
local function Ok(Cond, What) if not Cond then table.insert(Fails, What) end end
Motion.ForceReduced = false
local Base = Motion.ActiveCount() -- the live chat's and panel's candles may already be in the loop
local G = Instance.new("ScreenGui")
G.Name = "MotionCheck"
G.Parent = P.PlayerGui

local L = Instance.new("TextLabel")
L.TextTransparency = 0.1
L.Position = UDim2.fromOffset(15, 0)
L.Parent = G
Motion.SmokeIn(L)
Ok(L.TextTransparency == 1, "SmokeIn doesn't start hidden")
task.wait(0.6)
Ok(math.abs(L.TextTransparency - 0.1) < 0.01 and L.Position == UDim2.fromOffset(15, 0), "SmokeIn end " .. L.TextTransparency)

local F = Instance.new("Frame")
F.BackgroundTransparency = 0
F.Parent = G
local Items = { { F, { BackgroundTransparency = 0 }, { BackgroundTransparency = 1 } } }
Motion.Wake(Items, false)
task.wait(0.15)
Motion.Wake(Items, true) -- replaces the fade-out half way
task.wait(0.45)
Ok(F.BackgroundTransparency < 0.01, "Wake: the interrupted fade didn't end awake " .. F.BackgroundTransparency)

local Flame = Instance.new("ImageLabel")
Flame.Size = UDim2.fromOffset(12, 14)
Flame.Parent = G
Motion.Candle(Flame, nil)
local S = Instance.new("UIStroke")
S.Parent = F
Motion.Glint(S, "Color", Color3.new(1, 0, 0), Color3.new(0, 0, 1), nil)
Ok(Motion.ActiveCount() == Base + 2, ("loop entries %d, want %d"):format(Motion.ActiveCount(), Base + 2))
local Seen = {}
for _ = 1, 12 do
	task.wait(0.05)
	Seen[math.floor(Flame.Size.X.Offset * 100)] = true
end
local N = 0
for _ in Seen do N += 1 end
Ok(N >= 3, "the candle doesn't flicker (" .. N .. " sizes)")

local Bar = Instance.new("Frame")
local Fill = Instance.new("Frame")
Fill.Name = "Fill"
Fill.Size = UDim2.new(0.4, -4, 1, -4)
Fill.Parent = Bar
Bar.Parent = G
Motion.Fill(Bar, 0)
Ok(Fill.Size.X.Scale == 0, "Fill doesn't start empty")
task.wait(1.3)
Ok(Fill.Size == UDim2.new(0.4, -4, 1, -4), "Fill end " .. tostring(Fill.Size))

local Pips = {}
for I = 1, 5 do
	local Q = Instance.new("Frame")
	Q.Parent = G
	Pips[I] = Q
end
Motion.Pips(Pips, 3, Color3.new(1, 1, 0), Color3.new(0, 0, 0), 0)
Ok(Pips[1].BackgroundColor3 == Color3.new(0, 0, 0), "Pips don't start off")
task.wait(0.9)
Ok(Pips[3].BackgroundColor3 == Color3.new(1, 1, 0) and Pips[4].BackgroundColor3 == Color3.new(0, 0, 0), "Pips end")

local Panel = Instance.new("Frame")
Panel.Visible = false
Panel.Parent = G
local T = Instance.new("TextLabel")
T.Parent = Panel
Motion.Open(Panel)
task.wait(0.5)
Ok(Panel.Visible and T.TextTransparency == 0 and Panel.NHOpenScale.Scale == 1, "Open end")
Motion.Close(Panel)
task.wait(0.1)
Motion.Open(Panel) -- reopened mid-close
task.wait(0.5)
Ok(Panel.Visible and T.TextTransparency == 0, "reopened mid-close but hidden or faded")
Motion.Close(Panel)
task.wait(0.5)
Ok(not Panel.Visible, "Close end")

G:Destroy()
task.wait(0.2)
Ok(Motion.ActiveCount() == Base, ("loop entries after destroy %d, want %d"):format(Motion.ActiveCount(), Base))
Motion.ForceReduced = nil
return if #Fails == 0 then "PASS motion_play" else "FAIL " .. table.concat(Fails, "; ")
