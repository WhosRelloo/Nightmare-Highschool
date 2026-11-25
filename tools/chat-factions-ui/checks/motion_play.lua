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
	Seen[Flame.Size.X.Offset .. "/" .. math.round(Flame.ImageColor3.R * 100)] = true
end
local N = 0
for _ in Seen do N += 1 end
Ok(N >= 3, "the candle doesn't flicker (" .. N .. " distinct size/colour pairs)")
Flame.ImageTransparency = 0.7
task.wait(0.2)
Ok(math.abs(Flame.ImageTransparency - 0.7) < 0.001, "the candle loop still writes ImageTransparency (" .. Flame.ImageTransparency .. ")")

-- Reduce Motion turned on after registration (the saved setting lands after OnStart): the flame rests at how it was
-- built and the glint at A, for as long as it is on; turned off, the flicker carries on.
Motion.ForceReduced = true
task.wait(0.05)
local Still = true
for _ = 1, 10 do
	if Flame.Size ~= UDim2.fromOffset(12, 14) or Flame.ImageColor3 ~= Color3.new(1, 1, 1) or S.Color ~= Color3.new(1, 0, 0) then
		Still = false
	end
	task.wait(0.05)
end
Ok(Still, ("Reduce Motion on after registration: flame %s %s, glint %s"):format(tostring(Flame.Size), tostring(Flame.ImageColor3), tostring(S.Color)))
Ok(Motion.ActiveCount() == Base + 2, "Reduce Motion dropped loop entries")
Motion.ForceReduced = false
local Moved = {}
for _ = 1, 10 do
	task.wait(0.05)
	Moved[Flame.Size.X.Offset .. "/" .. math.round(Flame.ImageColor3.R * 100)] = true
end
local NM = 0
for _ in Moved do NM += 1 end
Ok(NM >= 3, "the candle didn't resume after Reduce Motion was turned off (" .. NM .. ")")

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
Ok((Pips[3].BackgroundColor3.R + Pips[3].BackgroundColor3.G + (1 - Pips[3].BackgroundColor3.B)) > 2.99 and Pips[4].BackgroundColor3 == Color3.new(0, 0, 0), "Pips end")

local Panel = Instance.new("Frame")
Panel.Visible = false
Panel.Parent = G
local T = Instance.new("TextLabel")
T.Parent = Panel
Motion.Open(Panel)
task.wait(0.5)
Ok(Panel.Visible and math.abs(T.TextTransparency) < 0.001 and math.abs(Panel.NHOpenScale.Scale - 1) < 0.001, "Open end")
Motion.Close(Panel)
task.wait(0.1)
Motion.Open(Panel) -- reopened mid-close
task.wait(0.5)
Ok(Panel.Visible and math.abs(T.TextTransparency) < 0.001, "reopened mid-close but hidden or faded")
Motion.Close(Panel)
task.wait(0.5)
Ok(not Panel.Visible, "Close end")

-- Open then Rise in the same frame (the Toggle path): the sections must come back to how they were built.
local P2 = Instance.new("Frame")
P2.Visible = false
P2.Parent = G
local Secs, Labs = {}, {}
for I = 1, 2 do
	local Sec = Instance.new("Frame")
	Sec.BackgroundTransparency = 1
	Sec.Position = UDim2.fromOffset(0, (I - 1) * 30)
	Sec.Parent = P2
	local Lab = Instance.new("TextLabel")
	Lab.TextTransparency = 0.1
	Lab.Parent = Sec
	Secs[I], Labs[I] = Sec, Lab
end
Motion.Open(P2)
Motion.Rise(Secs, 0.15)
task.wait(0.15)
-- the stagger survives Open's own fade: the second section (due at 0.2 s) is still hidden
Ok(Labs[2].TextTransparency > 0.5, ("Rise stagger lost: the second section is at %.2f 0.15 s after Open"):format(Labs[2].TextTransparency))
task.wait(1.05)
Ok(math.abs(Labs[1].TextTransparency - 0.1) < 0.01 and math.abs(Labs[2].TextTransparency - 0.1) < 0.01, ("Open + Rise left labels at %.2f / %.2f"):format(Labs[1].TextTransparency, Labs[2].TextTransparency))

-- Open + Rise + a delayed SmokeIn, Close 0.1 s later: nothing fades back in once the panel has gone.
local P6 = Instance.new("Frame")
P6.Visible = false
P6.Parent = G
local Secs6, Labs6 = {}, {}
for I = 1, 2 do
	local Sec = Instance.new("Frame")
	Sec.BackgroundTransparency = 1
	Sec.Parent = P6
	local Lab = Instance.new("TextLabel")
	Lab.TextTransparency = 0.1
	Lab.Parent = Sec
	Secs6[I], Labs6[I] = Sec, Lab
end
local Smoke6 = Instance.new("TextLabel")
Smoke6.TextTransparency = 0.1
Smoke6.Parent = P6
Motion.Open(P6)
Motion.Rise(Secs6, 0.15)
Motion.SmokeIn(Smoke6, 0.3)
task.wait(0.1)
Motion.Close(P6)
task.wait(0.7)
Ok(not P6.Visible, "Open/Close: the panel is still showing")
Ok(Labs6[1].TextTransparency > 0.99 and Labs6[2].TextTransparency > 0.99 and Smoke6.TextTransparency > 0.99,
	("a fade-in came back after Close (rise %.2f / %.2f, smoke %.2f)"):format(Labs6[1].TextTransparency, Labs6[2].TextTransparency, Smoke6.TextTransparency))

-- Close is the true reverse: half way it is scaled down and dropped; once hidden it is back at its open place.
local P7 = Instance.new("Frame")
P7.Visible = false
P7.Position = UDim2.fromOffset(100, 100)
P7.Parent = G
Motion.Open(P7)
task.wait(0.5)
Motion.Close(P7)
task.wait(0.1)
Ok(P7.NHOpenScale.Scale < 0.999 and P7.Position.Y.Offset > 100, ("Close half way: scale %.4f, y %d"):format(P7.NHOpenScale.Scale, P7.Position.Y.Offset))
task.wait(0.3)
Ok(not P7.Visible and P7.Position == UDim2.fromOffset(100, 100), "Close end " .. tostring(P7.Position))

-- Open, Close 0.1 s later, Open again: the panel is back at how it was built, not dimmed.
local P3 = Instance.new("Frame")
P3.Visible = false
P3.Parent = G
local L3 = Instance.new("TextLabel")
L3.TextTransparency = 0.1
L3.Parent = P3
Motion.Open(P3)
task.wait(0.1)
Motion.Close(P3)
task.wait(0.1)
Motion.Open(P3)
task.wait(0.6)
Ok(P3.Visible and math.abs(L3.TextTransparency - 0.1) < 0.01, ("Open/Close/Open left the label at %.2f"):format(L3.TextTransparency))

-- Fill called twice 0.3 s apart still ends at its built size.
local Bar2 = Instance.new("Frame")
local Fill2 = Instance.new("Frame")
Fill2.Name = "Fill"
Fill2.Size = UDim2.new(0.4, -4, 1, -4)
Fill2.Parent = Bar2
Bar2.Parent = G
Motion.Fill(Bar2, 0)
task.wait(0.3)
Motion.Fill(Bar2, 0)
task.wait(1.4)
Ok(math.abs(Fill2.Size.X.Scale - 0.4) < 0.001 and Fill2.Size.X.Offset == -4, "Fill twice ended at " .. tostring(Fill2.Size))

-- SmokeIn called twice 0.1 s apart still ends at the built transparency and position.
local L4 = Instance.new("TextLabel")
L4.TextTransparency = 0.1
L4.Position = UDim2.fromOffset(15, 0)
L4.Parent = G
Motion.SmokeIn(L4)
task.wait(0.1)
Motion.SmokeIn(L4)
task.wait(0.6)
Ok(math.abs(L4.TextTransparency - 0.1) < 0.01 and L4.Position == UDim2.fromOffset(15, 0), ("SmokeIn twice ended at %.2f"):format(L4.TextTransparency))

-- The fade-in of Open is visible: two Heartbeats after Open the label is still mostly transparent, then it returns.
local P5 = Instance.new("Frame")
P5.Visible = false
P5.Parent = G
local L5 = Instance.new("TextLabel")
L5.TextTransparency = 0.1
L5.Parent = P5
Motion.Open(P5)
game:GetService("RunService").Heartbeat:Wait()
game:GetService("RunService").Heartbeat:Wait()
Ok(L5.TextTransparency > 0.5, ("Open's fade-in isn't visible (label at %.2f after two Heartbeats)"):format(L5.TextTransparency))
task.wait(0.5)
Ok(math.abs(L5.TextTransparency - 0.1) < 0.01, ("Open's fade-in didn't end at built (%.2f)"):format(L5.TextTransparency))

G:Destroy()
task.wait(0.2)
Ok(Motion.ActiveCount() == Base, ("loop entries after destroy %d, want %d"):format(Motion.ActiveCount(), Base))
Motion.ForceReduced = nil
return if #Fails == 0 then "PASS motion_play" else "FAIL " .. table.concat(Fails, "; ")
