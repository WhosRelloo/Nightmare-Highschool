-- chat_play (chat-factions-ui, Client, Play): the rebuilt chat. A sent note arrives as a line and joins the history,
-- the frame sinks to text only when quiet and wakes on Focus, the draft holds, SetShown and NHCanChat hide it.
local P = game.Players.LocalPlayer
local Chat = require(P.PlayerScripts.Controllers.Gui.Chat)
local T = Chat.ForTests
if not T then return "FAIL no Chat.ForTests" end
local U = T.Ui()
if not U then return "FAIL the chat isn't built" end
if not U.Vignette or not U.Flame then return "FAIL no vignette or candle" end
local S = T.State
local Fails = {}
local function Ok(Cond, What) if not Cond then table.insert(Fails, What) end end
local function lineWith(Text: string): TextLabel?
	for _, R in U.Log:GetChildren() do
		local L = R:FindFirstChild("Text")
		if L and string.find(L.Text, Text, 1, true) then return L end
	end
	return nil
end

-- 1. a sent note arrives and joins the history
local Tag = "chat check " .. math.random(1000, 9999)
S.LastSent = 0
T.Send(Tag)
local Got = nil
for _ = 1, 60 do
	Got = lineWith(Tag)
	if Got then break end
	task.wait(0.1)
end
Ok(Got ~= nil, "the sent note never arrived")
Ok(S.History[#S.History] == Tag, "history: " .. tostring(S.History[#S.History]))

-- 2. quiet: the frame sinks, the lines stay
if U.Box:IsFocused() then U.Box:ReleaseFocus(false) end
S.Hover = false
S.LastActive = os.clock() - 60
task.wait(1.3)
Ok(S.Faded == true, "never went quiet")
Ok(U.Header.GroupTransparency > 0.99, "header shows when quiet: " .. U.Header.GroupTransparency)
Ok(U.Background == nil or U.Background.ImageTransparency > 0.99, "panel shows when quiet")
Ok(U.Border == nil or not U.Border:IsA("ImageLabel") or U.Border.ImageTransparency > 0.99, "iron edge shows when quiet")
Ok(U.Bar.GroupTransparency > (if S.Touch then 0.55 else 0.99), "bar when quiet: " .. U.Bar.GroupTransparency)
Ok(Got == nil or Got.TextTransparency < 0.05, "the line is hidden when quiet")
Ok(U.Vignette.ImageTransparency < 0.5, "no vignette when quiet: " .. U.Vignette.ImageTransparency)
do -- the vignette sits behind the lines, not the window
	local Content = math.min(U.LogLayout.AbsoluteContentSize.Y, U.Log.AbsoluteSize.Y)
	Ok(U.Vignette.AbsoluteSize.Y <= U.Log.AbsoluteSize.Y + 30, "vignette taller than the log: " .. U.Vignette.AbsoluteSize.Y)
	local Mid = U.Vignette.AbsolutePosition.Y + U.Vignette.AbsoluteSize.Y / 2
	Ok(Mid >= U.Log.AbsolutePosition.Y - 2 and Mid <= U.Log.AbsolutePosition.Y + Content + 2, "vignette centre off the lines: " .. Mid)
end

-- 3. Focus (what / does) wakes it and focuses the bar; leaving keeps the draft
Chat.Focus()
task.wait(0.5)
Ok(U.Box:IsFocused(), "Focus didn't focus the bar")
Ok(S.Faded == false and U.Header.GroupTransparency < 0.01, "Focus didn't wake it: " .. U.Header.GroupTransparency)
Ok(U.Vignette.ImageTransparency > 0.99, "vignette shows when awake")
U.Box.Text = "a draft"
U.Box:ReleaseFocus(false)
task.wait(0.1)
Ok(U.Box.Text == "a draft", "the draft was lost: " .. U.Box.Text)
U.Box.Text = ""

-- 4. SetShown and NHCanChat
Chat.SetShown(false)
Ok(U.Window.Visible == false, "SetShown(false) left it showing")
Chat.SetShown(true)
Ok(U.Window.Visible == true, "SetShown(true) left it hidden")
local Was = P:GetAttribute("NHCanChat")
P:SetAttribute("NHCanChat", false)
task.wait(0.1)
Ok(U.Window.Visible == false, "NHCanChat=false still shows it")
P:SetAttribute("NHCanChat", Was)
task.wait(0.1)
Ok(U.Window.Visible == true, "NHCanChat put back but still hidden")
return if #Fails == 0 then "PASS chat_play" else "FAIL " .. table.concat(Fails, "; ")
