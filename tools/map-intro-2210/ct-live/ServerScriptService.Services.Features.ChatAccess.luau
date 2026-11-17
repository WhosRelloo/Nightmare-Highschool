--[[
	ChatAccess (server, 2026-11-17): who may use text chat, for the NH chat window (Controllers.Gui.Chat).

	Roblox's own chat window hides itself for accounts that can't chat (privacy settings, parental controls, regional
	rules). Ours replaces it, so it has to do the same: on join this asks TextChatService:CanUserChatAsync (server
	only) and sets the Player attribute NHCanChat (true / false). Gui.Chat hides the window and the bar when it's
	false. If Roblox can't answer, it tries again a few times and leaves the attribute unset; the bar then shows, and
	Roblox still refuses to send or deliver chat for an account that isn't allowed.

	Chat itself is unchanged: every message goes through TextChannel:SendAsync, so Roblox filters it and applies
	each pair's privacy settings.
]]

local Players = game:GetService(`Players`)
local TextChatService = game:GetService(`TextChatService`)

local Shared = {}

local function check(Player: Player)
	for Try = 1, 4 do
		if not Player.Parent then return end
		local Ok, Can = pcall(TextChatService.CanUserChatAsync, TextChatService, Player.UserId)
		if Ok and typeof(Can) == `boolean` then
			Player:SetAttribute(`NHCanChat`, Can)
			return
		end
		task.wait(2 * Try)
	end
end

function Shared.CanChat(Player: Player): boolean?
	return Player:GetAttribute(`NHCanChat`)
end

function Shared.OnStart()
	for _, P in Players:GetPlayers() do task.spawn(check, P) end
	Players.PlayerAdded:Connect(function(P) task.spawn(check, P) end)
end

return Shared
