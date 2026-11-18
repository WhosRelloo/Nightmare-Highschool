local S = Instance.new("Script")
S.Source = [[
local P = game.Players:GetPlayers()[1]
local H = game:GetService("HttpService")
local SSS = game.ServerScriptService.Services
local Prof = require(SSS.Player.Data).GetProfile(P)
local Disc = require(SSS.School.Discipline).GetData(P)
script:SetAttribute("Json", H:JSONEncode({ Quests = Prof.Quests; Yen = Prof.Yen; Discipline = Disc; Relationships = (Prof.Social and Prof.Social.Relationships) or {} }))
]]
S.Parent = game.ServerScriptService
task.wait(1)
local J = S:GetAttribute("Json")
S:Destroy()
return J
