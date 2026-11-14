--[[
	Assist (client binding): the study-group tag assist key, G (combat concept 21, 2.15.0). One key for both halves:
	in a fight it calls your group in; when a groupmate called you, it answers. The server decides which
	(ServerStorage.Packages.TagAssist), so this only sends the press.
]]
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

return function(Character: Model, InputState: string, Action: string, Data: any)
	if not Character or InputState ~= `Began` then return end
	if Character:GetAttribute(`HasSportBall`) or Character:GetAttribute(`InSport`) then return end
	local R = ReplicatedStorage:FindFirstChild(`NHAssist`)
	if R then R:FireServer(`Press`) end
end
