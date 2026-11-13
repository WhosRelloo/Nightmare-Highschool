--!strict
--[[
	Typing guard (2.1.0): one answer, for every keybind in the game, to "is the player typing right now?"

	While the answer is yes, no game key may open a panel or do anything: the letters belong to the text box.
	- Any TextBox with focus counts: the NH chat bar (Controllers.Gui.Chat), the Wardrobe search, a name box...
	- Roblox's own chat bar counts too (ChatInputBarConfiguration.IsFocused). UserInputService:GetFocusedTextBox()
	  can't see that one, because it lives in CoreGui.

	Use:
		local Typing = require(ReplicatedStorage.Packages.Bind.Typing)
		if Typing.Active() then return end              -- in a key handler
		if Typing.Blocks(Input) then return end         -- keyboard / controller input only; clicks still go through

	Bind.Keybinds (every combat key: M1, Equip E, Block F, Dodge Q...) checks it before running anything.
]]

local TextChatService = game:GetService("TextChatService")
local UserInputService = game:GetService("UserInputService")

local Typing = {}

local Bar: ChatInputBarConfiguration? = nil

local function bar(): ChatInputBarConfiguration?
	if not Bar or not Bar.Parent then
		Bar = TextChatService:FindFirstChildOfClass("ChatInputBarConfiguration")
	end
	return Bar
end

-- true while any text box has the keyboard
function Typing.Active(): boolean
	if UserInputService:GetFocusedTextBox() then
		return true
	end
	local B = bar()
	if B then
		local Ok, Focused = pcall(function()
			return B.IsFocused
		end)
		if Ok and Focused then
			return true
		end
	end
	return false
end

-- true when this input is a key (keyboard or controller) and the player is typing.
-- Mouse and touch go through, so a click outside the box still works.
function Typing.Blocks(Input: InputObject): boolean
	local T = Input.UserInputType
	if T == Enum.UserInputType.Keyboard or string.sub(T.Name, 1, 7) == "Gamepad" then
		return Typing.Active()
	end
	return false
end

return Typing
