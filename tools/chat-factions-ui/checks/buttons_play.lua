-- buttons_play (chat-factions-ui, Client, Play): the left-edge Factions and Journal buttons are gone (hidden, the
-- instances kept), and they stay hidden after each panel opens and closes.
local P = game.Players.LocalPlayer
local Gui = P.PlayerGui
local Fails = {}
local function Ok(Cond, What) if not Cond then table.insert(Fails, What) end end
local Factions = require(P.PlayerScripts.Controllers.Gui.FactionsPanel)
local Journal = require(P.PlayerScripts.Controllers.Gui.QuestJournal)
local function hidden(Name: string): boolean
	local G = Gui:FindFirstChild(Name)
	local T = G and G:FindFirstChild("Toggle")
	return T ~= nil and T:IsA("GuiObject") and not T.Visible
end
Ok(Gui:FindFirstChild("FactionsPanel") ~= nil, "no FactionsPanel gui")
Ok(Gui:FindFirstChild("QuestJournal") ~= nil, "no QuestJournal gui")
Ok(hidden("FactionsPanel"), "the Factions button shows")
Ok(hidden("QuestJournal"), "the Journal button shows")
Factions.Toggle(true)
task.wait(0.5)
Factions.Toggle(false)
task.wait(0.5)
Ok(hidden("FactionsPanel"), "the Factions button shows after open and close")
Journal.Toggle(true)
task.wait(0.5)
Journal.Toggle(false)
task.wait(0.5)
Ok(hidden("QuestJournal"), "the Journal button shows after open and close")
return if #Fails == 0 then "PASS buttons_play" else "FAIL " .. table.concat(Fails, "; ")
