-- make_motion (chat-factions-ui, Edit): creates ReplicatedStorage.UI.Motion as an empty ModuleScript, once, so
-- install_inplace.py (which only sets Source on existing scripts) can install it.
local UI = game.ReplicatedStorage:FindFirstChild("UI")
if not UI then return "FAIL no ReplicatedStorage.UI" end
local M = UI:FindFirstChild("Motion")
if M then return "PASS already there (" .. M.ClassName .. ")" end
M = Instance.new("ModuleScript")
M.Name = "Motion"
M.Source = "return {}\n"
M.Parent = UI
return "PASS made ReplicatedStorage.UI.Motion"
